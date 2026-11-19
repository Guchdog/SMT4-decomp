#!/usr/bin/env python3
"""Differential test for script_vm_func_003c7a94 (0x003C7A94) using Unicorn ARM."""

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

FUNC_ADDR = 0x003C7A94
FUNC_SIZE = 1048
FUNC_NAME = "script_vm_func_003c7a94"
TRAP_ADDR = 0x000F0000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000

G_33158 = 0x00433158
G_5D18 = 0x00435D18
SELF_ADDR = 0x004A0000
R5_ADDR = 0x004B0000
STACK_TOP = 0x08020000

CALLEES = {
    0x002C4B30: ("engine_func_002c4b30", 2),
    0x002BE7FC: ("ui_func_002be7fc", 4),
    0x0022A458: ("script_vm_func_0022a458", 2),
    0x00387C8C: ("script_vm_func_00387c8c", 4),
    0x00297704: ("script_vm_func_00297704", 3),
    0x002AC2F4: ("Tbb_GetSubTable", 2),
    0x002C0E9C: ("Tbb_GetPayloadData", 1),
    0x002C0E4C: ("Tbb_GetRowCount", 1),
    0x0022A324: ("script_vm_func_0022a324", 2),
    0x0022A2B0: ("script_vm_func_0022a2b0", 4),
    0x0022A210: ("script_vm_func_0022a210", 2),
    0x002971E4: ("script_vm_func_002971e4", 2),
    0x002B8B78: ("script_vm_func_002b8b78", 1),
    0x003C7988: ("battle_func_003c7988", 2),
    0x003DB004: ("engine_func_003db004", 1),
    0x003DC368: ("script_vm_func_003dc368", 1),
    0x003DC094: ("battle_func_003dc094", 1),
    0x003DCE60: ("script_vm_func_003dce60", 1),
}
STUB_BY_NAME = {name: STUB_BASE + idx * 4 for idx, (_, (name, _)) in enumerate(CALLEES.items())}
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
        top = (insn >> 24) & 0xFF
        if (insn & 0x0E000000) == 0x0A000000 or (top & 0xFE) == 0xFA:
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            h_bit = (insn >> 24) & 1 if (top & 0xFE) == 0xFA else 0
            pc = FUNC_ADDR + off
            target = (pc + 8 + imm24 * 4 + h_bit * 2) & ~3
            if target in CALLEES:
                stub = STUB_BY_NAME[CALLEES[target][0]]
                rel = (stub - (pc + 8)) // 4
                op = 0xEA000000 if top == 0xEA else 0xEB000000
                struct.pack_into("<I", buf, off, op | (rel & 0x00FFFFFF))
    return bytes(buf)


def read_cstr(uc: unicorn.Uc, addr: int) -> str:
    out = bytearray()
    while len(out) < 96:
        b = uc.mem_read(addr + len(out), 1)[0]
        if b == 0:
            break
        out.append(b)
    return out.decode("ascii", errors="replace")


class Runner:
    def __init__(self, code_bytes: bytes, rodata_blobs: list[tuple[int, bytes]] | None = None) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x000F0000, 0x00010000)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(0x08000000, 0x00100000)
        self.uc.mem_write(FUNC_ADDR, code_bytes)
        self.uc.mem_write(0x004009B4, b"battle/event/%s/ProTable_%s.tbb\x00")
        self.uc.mem_write(0x00400984, b"battle/event/%s/%s.bf\x00")
        if rodata_blobs:
            for addr, data in rodata_blobs:
                self.uc.mem_write(addr, data)
        for stub_addr in ADDR_BY_STUB:
            self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE1A00000))

    def run(
        self,
        *,
        state: int,
        sub_2c: int = 0,
        h8: int = 0,
        hc: int = 1,
        h10: int = 0,
        h20: int = 5,
        r5_44a0: int = 0,
        ret_a458: int = 1,
        load_ok: bool = True,
        ret_c368: int = 1,
        ret_ce60: int = 1,
    ) -> dict:
        self.uc.mem_write(G_33158, struct.pack("<I", 0x6000))
        self.uc.mem_write(G_5D18, struct.pack("<I", 0x7000))

        self_buf = bytearray(0x40)
        struct.pack_into("<I", self_buf, 0, state)
        struct.pack_into("<I", self_buf, 8, h8)
        struct.pack_into("<I", self_buf, 0xC, hc)
        struct.pack_into("<I", self_buf, 0x10, h10)
        struct.pack_into("<I", self_buf, 0x14, 0x8000)
        struct.pack_into("<i", self_buf, 0x20, h20)
        self_buf[0x2C] = sub_2c & 0xFF
        self.uc.mem_write(SELF_ADDR, bytes(self_buf))

        r5_buf = bytearray(0x4500)
        struct.pack_into("<I", r5_buf, 0xC4, 0x42)
        r5_buf[0x100 : 0x105] = b"ev01\x00"
        struct.pack_into("<I", r5_buf, 0x44A0, r5_44a0)
        self.uc.mem_write(R5_ADDR, bytes(r5_buf))

        trace: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr == TRAP_ADDR:
                uc.emu_stop()
                return
            if addr not in ADDR_BY_STUB:
                return
            target = ADDR_BY_STUB[addr]
            name, nargs = CALLEES[target]
            regs = (arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1, arm.UC_ARM_REG_R2, arm.UC_ARM_REG_R3)
            args = tuple(uc.reg_read(regs[i]) for i in range(nargs))

            if name == "engine_func_002c4b30":
                uc.mem_write(args[0], b"\x00" * args[1])
                trace.append((name, args[1]))
            elif name == "ui_func_002be7fc":
                fmt = read_cstr(uc, args[1])
                s1 = read_cstr(uc, args[2])
                s2 = read_cstr(uc, args[3])
                msg = fmt % (s1, s2)
                uc.mem_write(args[0], msg.encode("ascii") + b"\x00")
                trace.append((name, msg))
            elif name == "script_vm_func_0022a458":
                trace.append((name, args))
                uc.reg_write(arm.UC_ARM_REG_R0, ret_a458)
            elif name in ("script_vm_func_00387c8c", "script_vm_func_0022a2b0"):
                path = read_cstr(uc, args[3])
                trace.append((name, args[0], args[1], path))
                uc.mem_write(args[2], struct.pack("<I", 0x9001 if load_ok else 0))
            elif name == "script_vm_func_00297704":
                path = read_cstr(uc, args[0])
                trace.append((name, path, args[2]))
                uc.mem_write(args[1], struct.pack("<I", 0x9002 if load_ok else 0))
            elif name == "Tbb_GetSubTable":
                trace.append((name, args))
                uc.reg_write(arm.UC_ARM_REG_R0, 0x9100)
            elif name == "Tbb_GetPayloadData":
                trace.append((name, args))
                uc.reg_write(arm.UC_ARM_REG_R0, 0x9200)
            elif name == "Tbb_GetRowCount":
                trace.append((name, args))
                uc.reg_write(arm.UC_ARM_REG_R0, 12)
            elif name in ("script_vm_func_0022a324", "script_vm_func_0022a210", "battle_func_003c7988"):
                trace.append((name, args))
                uc.reg_write(arm.UC_ARM_REG_R0, 0x777)
            elif name == "script_vm_func_003dc368":
                trace.append((name, args))
                uc.reg_write(arm.UC_ARM_REG_R0, ret_c368)
            elif name == "script_vm_func_003dce60":
                trace.append((name, args))
                uc.reg_write(arm.UC_ARM_REG_R0, ret_ce60)
            else:
                trace.append((name, args))
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_R1, R5_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=100000)
        finally:
            self.uc.hook_del(hook)

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "self": bytes(self.uc.mem_read(SELF_ADDR, 0x30)),
            "trace": trace,
        }


def build_cases() -> list[tuple[str, dict]]:
    return [
        ("st0_zero", {"state": 0}),
        ("st1_tbb_ok", {"state": 1, "ret_a458": 1, "load_ok": True}),
        ("st1_tbb_fallback_fail", {"state": 1, "ret_a458": 0, "load_ok": False}),
        ("st2_nonnull", {"state": 2, "h8": 0x9001}),
        ("st3_direct", {"state": 3}),
        ("st4_hc_0", {"state": 4, "hc": 0}),
        ("st4_hc_1_ok", {"state": 4, "hc": 1, "load_ok": True}),
        ("st5_bf_fallback", {"state": 5, "ret_a458": 0, "load_ok": True}),
        ("st6_null", {"state": 6, "h10": 0}),
        ("st7_direct", {"state": 7}),
        ("st8_sub0_wait_c368", {"state": 8, "sub_2c": 0, "ret_c368": 0}),
        ("st8_sub1_wait_ce60", {"state": 8, "sub_2c": 1, "ret_c368": 1, "ret_ce60": 0}),
        ("st8_sub2_fire_dd", {"state": 8, "sub_2c": 2, "ret_ce60": 1, "r5_44a0": 0x100000}),
        ("st9_neg_id", {"state": 9, "h20": -1}),
        ("st10_direct", {"state": 10}),
        ("st11_default", {"state": 11}),
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
        ("wrong_tbb_fmt", '"battle/event/%s/ProTable_%s.tbb"', '"battle/event/%s/Pro_%s.tbb"'),
        ("wrong_row_state", "*reinterpret_cast<u32*>(self) = 3u;", "*reinterpret_cast<u32*>(self) = 4u;"),
        ("wrong_dd_mask", "(& 0x100000u) != 0u", "(& 0x200000u) != 0u"),
        ("wrong_sub2_next", "self[0x2Cu] = 3u;", "self[0x2Cu] = 2u;"),
        ("wrong_case10", "case 10u:\n            return battle_func_003c7988(self, r5);", "case 10u:\n            return 0u;"),
    ]
    for mut_name, old, new in mutations:
        if mut_name == "wrong_dd_mask":
            old = "((*reinterpret_cast<const u32*>(r5 + 0x44A0u) & 0x100000u) != 0u)"
            new = "((*reinterpret_cast<const u32*>(r5 + 0x44A0u) & 0x200000u) != 0u)"
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_src = cpp_text.replace(old, new, 1)
        cand_code, rodata_blobs, _ = compile_candidate(work_dir, mut_src)
        failures = run_suite(orig_code, cand_code, rodata_blobs)
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_003c7a94"
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
