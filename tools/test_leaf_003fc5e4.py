#!/usr/bin/env python3
"""Differential test for func_003fc5e4 (0x003FC5E4) using Unicorn ARM."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
import unicorn.arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x003FC5E4
FUNC_SIZE = 960
FUNC_NAME = "func_003fc5e4"
TRAP_ADDR = 0x000F0000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000

SELF_PTR = 0x004A0000
OUT_DIR_PTR = 0x004A1000
OUT_INFO_PTR = 0x004A1100
OUT_NAME_PTR = 0x004A1200
PATH_PTR = 0x004A2000
SEG_STR_BASE = 0x004A3000
STACK_TOP = 0x08020000

CALLEES = {
    0x0035A408: "func_0035a408",
    0x0035A2E4: "func_0035a2e4",
    0x0035A350: "func_0035a350",
    0x00239DEC: "func_00239dec",
    0x003E0E7C: "func_003e0e7c",
    0x00239D2C: "func_00239d2c",
    0x0035A420: "func_0035a420",
    0x00225678: "func_00225678",
    0x003E0E28: "func_003e0e28",
    0x003E0DF8: "func_003e0df8",
}
STUB_BY_NAME = {name: STUB_BASE + idx * 4 for idx, name in enumerate(CALLEES.values())}
ADDR_BY_STUB = {STUB_BASE + idx * 4: addr for idx, addr in enumerate(CALLEES.keys())}


def patch_cand_elf(obj_path: Path) -> tuple[bytes, list[tuple[int, bytes]], int]:
    elf = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", elf, 0x20)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", elf, 0x2E)
    sections = [struct.unpack_from("<10I", elf, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = sections[e_shstrndx][4]

    def sec_name(idx: int) -> str:
        n_off = shstr_off + sections[idx][0]
        return elf[n_off : elf.find(b"\x00", n_off)].decode("ascii", errors="replace")

    symtab = next(sh for sh in sections if sh[1] == 2)
    strtab = sections[symtab[6]]
    str_off = strtab[4]

    def sym_info(sym_idx: int) -> tuple[str, int, int]:
        s_off = symtab[4] + sym_idx * 16
        st_name, st_value, _, _, _, st_shndx = struct.unpack_from("<IIIBBH", elf, s_off)
        end = elf.find(b"\x00", str_off + st_name)
        return elf[str_off + st_name : end].decode("ascii", errors="replace"), st_value, st_shndx

    func_val = func_size = func_shndx = None
    for idx in range(symtab[5] // 16):
        name, val, shndx = sym_info(idx)
        if name == FUNC_NAME:
            func_val = val
            func_size = struct.unpack_from("<I", elf, symtab[4] + idx * 16 + 8)[0]
            func_shndx = shndx
            break
    assert func_val is not None and func_size is not None and func_shndx is not None

    text_sh = sections[func_shndx]
    code = bytearray(elf[text_sh[4] + func_val : text_sh[4] + func_val + func_size])

    rodata_blob = bytearray()
    rodata_map: dict[int, int] = {}
    for idx, sh in enumerate(sections):
        if sec_name(idx).startswith(".rodata"):
            rodata_map[idx] = RODATA_BASE + len(rodata_blob)
            rodata_blob.extend(elf[sh[4] : sh[4] + sh[5]])
            while len(rodata_blob) % 4 != 0:
                rodata_blob.append(0)

    for sh in sections:
        if sh[1] == 9 and sh[7] == func_shndx:
            for pos in range(sh[4], sh[4] + sh[5], 8):
                r_off, r_info = struct.unpack_from("<II", elf, pos)
                if not (func_val <= r_off < func_val + func_size):
                    continue
                c_off = r_off - func_val
                r_type = r_info & 0xFF
                s_name, _, s_shndx = sym_info(r_info >> 8)
                if r_type in (28, 29):
                    insn = struct.unpack_from("<I", code, c_off)[0]
                    cond = (insn >> 28) & 0xF
                    op = (insn >> 24) & 0xF
                    link = op == 0xB
                    target = STUB_BY_NAME[s_name]
                    pc = FUNC_ADDR + c_off
                    imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
                    struct.pack_into("<I", code, c_off, (cond << 28) | ((0xB if link else 0xA) << 24) | imm24)
                elif r_type == 2:
                    addend = struct.unpack_from("<I", code, c_off)[0]
                    if s_shndx == func_shndx:
                        struct.pack_into("<I", code, c_off, (FUNC_ADDR - func_val) + addend)
                    elif s_shndx in rodata_map:
                        struct.pack_into("<I", code, c_off, rodata_map[s_shndx] + addend)
                    else:
                        raise RuntimeError(f"Unexpected R_ARM_ABS32 section {s_shndx} ({s_name})")
                else:
                    raise RuntimeError(f"Unsupported reloc {r_type} for {s_name}")
    rodata_blobs = [(RODATA_BASE, bytes(rodata_blob))] if rodata_blob else []
    return bytes(code), rodata_blobs, func_size


def compile_candidate(work_dir: Path, cpp_text: str | None = None) -> tuple[bytes, list[tuple[int, bytes]], int]:
    src = work_dir / "cand.cpp"
    if cpp_text is None:
        src.write_text(SRC_CPP.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        src.write_text(cpp_text, encoding="utf-8")
    obj = work_dir / "cand.o"
    res = compile_tu_armv6k(src, obj)
    if res.returncode != 0:
        raise RuntimeError(f"compile failed: {res.stderr}")
    return patch_cand_elf(obj)


def patch_orig_bl(orig_code: bytes) -> bytes:
    buf = bytearray(orig_code)
    for off in range(0, len(buf), 4):
        insn = struct.unpack_from("<I", buf, off)[0]
        if (insn & 0x0F000000) == 0x0B000000:
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = FUNC_ADDR + off
            target = (pc + 8 + imm24 * 4) & 0xFFFFFFFF
            if target in CALLEES:
                stub = STUB_BY_NAME[CALLEES[target]]
                rel = (stub - (pc + 8)) // 4
                struct.pack_into("<I", buf, off, (insn & 0xFF000000) | (rel & 0x00FFFFFF))
    return bytes(buf)


class Runner:
    def __init__(self, code_bytes: bytes, rodata_blobs: list[tuple[int, bytes]] | None = None) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x000F0000, 0x00010000)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(0x08000000, 0x00100000)
        self.uc.mem_write(FUNC_ADDR, code_bytes)
        if rodata_blobs:
            for addr, data in rodata_blobs:
                self.uc.mem_write(addr, data)
        for stub_addr in ADDR_BY_STUB:
            self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE1A00000))

    def run(
        self,
        *,
        segments: tuple[str, ...],
        leaf: str,
        resolve_leaf: int,
        rc_2e4: int = 0,
        rc_350_fail_at: int = -1,
        rc_dec_fail_at: int = -1,
        rc_d2c: int = 0,
        rc_420: int = 0,
        rc_e28: int = 0,
        rc_df8: int = 0,
        rc_e7c: int = 0,
        rc_678: tuple[int, ...] = (0, 0),
        parent_id: int = 10,
        next_ids: tuple[int, ...] = (100, 101, 102, 103),
        parent_lookup_id: int = 77,
    ) -> dict:
        self.uc.mem_write(OUT_DIR_PTR, b"\x00" * 12)
        self.uc.mem_write(OUT_INFO_PTR, b"\x00" * 12)
        self.uc.mem_write(OUT_NAME_PTR, b"\x00" * 12)
        self.uc.mem_write(PATH_PTR, b"p\x00\x00\x00")

        seg_ptrs: list[tuple[int, int]] = []
        cursor = SEG_STR_BASE
        for s in list(segments) + [leaf]:
            enc = s.encode("utf-16-le") + b"\x00\x00"
            self.uc.mem_write(cursor, enc)
            seg_ptrs.append((len(s), cursor))
            cursor += (len(enc) + 3) & ~3

        trace: list[tuple] = []
        seg_idx = 0
        dec_idx = 0
        g678_idx = 0

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            nonlocal seg_idx, dec_idx, g678_idx
            if addr == TRAP_ADDR:
                uc.emu_stop()
                return
            if addr not in ADDR_BY_STUB:
                return
            target = ADDR_BY_STUB[addr]
            name = CALLEES[target]
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc.reg_read(arm.UC_ARM_REG_R3)
            sp = uc.reg_read(arm.UC_ARM_REG_SP)

            if name == "func_0035a408":
                uc.mem_write(r0, b"\x00" * 0x10)
                trace.append((name,))
            elif name == "func_0035a2e4":
                trace.append((name, r1))
                uc.reg_write(arm.UC_ARM_REG_R0, rc_2e4 & 0xFFFFFFFF)
            elif name == "func_0035a350":
                trace.append((name, seg_idx))
                if seg_idx == rc_350_fail_at:
                    uc.reg_write(arm.UC_ARM_REG_R0, 0x80000001)
                else:
                    slen, sptr = seg_ptrs[seg_idx]
                    uc.mem_write(r1, struct.pack("<II", slen, sptr))
                    seg_idx += 1
                    uc.mem_write(r0 + 0xC, struct.pack("<b", 1 if seg_idx >= len(segments) else 0))
                    uc.reg_write(arm.UC_ARM_REG_R0, 0)
            elif name == "func_00239dec":
                state = struct.unpack("<III", uc.mem_read(r3, 12))
                trace.append((name, r0, state))
                if dec_idx == rc_dec_fail_at:
                    uc.reg_write(arm.UC_ARM_REG_R0, 0x80000002)
                else:
                    nid = next_ids[dec_idx]
                    dec_idx += 1
                    uc.mem_write(r1, struct.pack("<I", nid))
                    uc.mem_write(r2, struct.pack("<III", nid + 1, nid + 2, nid + 3))
                    uc.reg_write(arm.UC_ARM_REG_R0, 0)
            elif name == "func_00239d2c":
                s0, s1 = struct.unpack("<II", uc.mem_read(sp, 8))
                trace.append((name, r0, r3, s0, s1))
                uc.mem_write(r1, struct.pack("<I", parent_id))
                uc.mem_write(r2, struct.pack("<I", 0x55))
                uc.reg_write(arm.UC_ARM_REG_R0, rc_d2c & 0xFFFFFFFF)
            elif name == "func_0035a420":
                pair = struct.unpack("<II", uc.mem_read(r1, 8))
                trace.append((name, pair, r2))
                uc.mem_write(r0, struct.pack("<II", 3, seg_ptrs[0][1]))
                uc.reg_write(arm.UC_ARM_REG_R0, rc_420 & 0xFFFFFFFF)
            elif name == "func_003e0e28":
                trace.append((name,))
                uc.reg_write(arm.UC_ARM_REG_R0, rc_e28)
            elif name == "func_003e0df8":
                trace.append((name, r1))
                uc.mem_write(r1, struct.pack("<II", 4, seg_ptrs[-1][1]))
                uc.reg_write(arm.UC_ARM_REG_R0, rc_df8 & 0xFFFFFFFF)
            elif name == "func_003e0e7c":
                trace.append((name,))
                slen, sptr = seg_ptrs[-1]
                uc.mem_write(r1, struct.pack("<II", slen, sptr))
                uc.reg_write(arm.UC_ARM_REG_R0, rc_e7c & 0xFFFFFFFF)
            elif name == "func_00225678":
                s0, s1, s2, s3 = struct.unpack("<IIII", uc.mem_read(sp, 16))
                r3_val = struct.unpack("<I", uc.mem_read(r3, 4))[0]
                trace.append((name, r0, r2, r3_val if r2 == OUT_NAME_PTR else 0, s0, s1, s2, s3))
                rc_val = rc_678[g678_idx] if g678_idx < len(rc_678) else 0
                g678_idx += 1
                if rc_val >= 0:
                    uc.mem_write(r2, struct.pack("<III", parent_lookup_id, 5, seg_ptrs[0][1]))
                    if r2 == OUT_DIR_PTR:
                        uc.mem_write(r3, struct.pack("<III", 0xAA, 0xBB, 0xCC))
                uc.reg_write(arm.UC_ARM_REG_R0, rc_val & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_PTR)
            self.uc.reg_write(arm.UC_ARM_REG_R1, OUT_DIR_PTR)
            self.uc.reg_write(arm.UC_ARM_REG_R2, OUT_INFO_PTR)
            self.uc.reg_write(arm.UC_ARM_REG_R3, OUT_NAME_PTR)
            self.uc.mem_write(STACK_TOP, struct.pack("<II", resolve_leaf, PATH_PTR))
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=100000)
        finally:
            self.uc.hook_del(hook)

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "out_dir": struct.unpack("<III", self.uc.mem_read(OUT_DIR_PTR, 12)),
            "out_info": struct.unpack("<III", self.uc.mem_read(OUT_INFO_PTR, 12)),
            "out_name": struct.unpack("<III", self.uc.mem_read(OUT_NAME_PTR, 12)),
            "trace": trace,
        }


def build_cases() -> list[tuple[str, dict]]:
    return [
        ("err_2e4", {"segments": ("a",), "leaf": "b", "resolve_leaf": 1, "rc_2e4": -1}),
        ("err_350_init", {"segments": ("a",), "leaf": "b", "resolve_leaf": 1, "rc_350_fail_at": 0}),
        ("err_dec_init", {"segments": ("a",), "leaf": "b", "resolve_leaf": 1, "rc_dec_fail_at": 0}),
        ("dot_and_dotdot_ok", {"segments": ("a", ".", "b", ".."), "leaf": "file", "resolve_leaf": 1}),
        ("dotdot_at_root", {"segments": ("a", ".."), "leaf": "file", "resolve_leaf": 1, "next_ids": (0,)}),
        ("no_resolve_e28_nz", {"segments": ("a",), "leaf": "file", "resolve_leaf": 0, "rc_e28": 1}),
        ("no_resolve_ok", {"segments": ("a", "b"), "leaf": "file", "resolve_leaf": 0}),
        ("leaf_dot_root", {"segments": ("a",), "leaf": ".", "resolve_leaf": 1, "next_ids": (10,)}),
        ("leaf_dot_nz", {"segments": ("a", "b"), "leaf": ".", "resolve_leaf": 1}),
        ("leaf_dotdot_root", {"segments": ("a",), "leaf": "..", "resolve_leaf": 1, "next_ids": (0,)}),
        ("leaf_dotdot_to_root", {"segments": ("a", "b"), "leaf": "..", "resolve_leaf": 1, "parent_lookup_id": 0}),
        ("leaf_dotdot_to_dir", {"segments": ("a", "b"), "leaf": "..", "resolve_leaf": 1, "parent_lookup_id": 88}),
        ("leaf_empty", {"segments": ("a",), "leaf": "", "resolve_leaf": 1}),
    ]


def run_suite(orig_code: bytes, cand_code: bytes, rodata_blobs: list[tuple[int, bytes]]) -> list[str]:
    failures: list[str] = []
    for name, kwargs in build_cases():
        orig = Runner(orig_code).run(**kwargs)
        cand = Runner(cand_code, rodata_blobs).run(**kwargs)
        if orig != cand:
            failures.append(f"{name}: orig={orig} cand={cand}")
    return failures


def run_negative_controls(orig_code: bytes, cpp_text: str, work_dir: Path) -> None:
    mutations = [
        ("wrong_dotdot_err", "rc = static_cast<s32>(0xE0C04702u);", "rc = static_cast<s32>(0xE0C04703u);"),
        ("wrong_dot_skip", "if (cur_state[1] == 1u && comp[0] == u'.')", "if (cur_state[1] == 2u && comp[0] == u'.')"),
        ("wrong_resolve_branch", "if (resolve_leaf == 0u)", "if (resolve_leaf != 0u)"),
        ("wrong_leaf_empty", "out_name[0] = (leaf_comp[0] != 0u) ? cur_id : 0u;", "out_name[0] = cur_id;"),
        ("wrong_leaf_dotdot_zero", "if (out_name[0] == 0u) {\n            return 0;\n        }\n        rc = func_00225678(self, &dummy_out, out_dir", "if (out_name[0] != 0u) {\n            return 0;\n        }\n        rc = func_00225678(self, &dummy_out, out_dir"),
    ]
    for mut_name, old, new in mutations:
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_src = cpp_text.replace(old, new, 1)
        cand_code, rodata_blobs, _ = compile_candidate(work_dir, mut_src)
        try:
            failures = run_suite(orig_code, cand_code, rodata_blobs)
        except unicorn.UcError as exc:
            failures = [f"uc_error: {exc}"]
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_003fc5e4"
    work_dir.mkdir(parents=True, exist_ok=True)
    raw = CODE_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = patch_orig_bl(raw[off : off + FUNC_SIZE])
    cand_code, rodata_blobs, cand_size = compile_candidate(work_dir)
    failures = run_suite(orig_code, cand_code, rodata_blobs)
    if failures:
        for f in failures:
            print("FAIL:", f)
        return 1
    run_negative_controls(orig_code, SRC_CPP.read_text(encoding="utf-8"), work_dir)
    print(f"ALL PASS: {len(build_cases())} cases + 5 negative controls (cand_size={cand_size}B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
