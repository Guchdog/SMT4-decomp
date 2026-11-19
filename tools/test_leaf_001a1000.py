#!/usr/bin/env python3
"""Differential test for engine_func_001a1000 (0x001A1000) using Unicorn ARM."""

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

FUNC_ADDR = 0x001A1000
FUNC_SIZE = 984
FUNC_NAME = "engine_func_001a1000"
TRAP_ADDR = 0x000F0000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000

G_BASE_PTR = 0x0043E2A8
S1_ADDR = 0x00500000
S3_ADDR = 0x00580000
ITEM_POOL = 0x00590000
STACK_TOP = 0x08020000

CALLEES = {
    0x002C4B30: ("engine_func_002c4b30", 2),
    0x002C3B48: ("engine_func_002c3b48", 2),
    0x002B9364: ("camp_func_002b9364", 1),
    0x0033FA54: ("engine_func_0033fa54", 0),
    0x002C4B1C: ("func_002c4b1c", 0),
    0x003BC17C: ("camp_func_003bc17c", 0),
    0x003C2818: ("engine_func_003c2818", 0),
    0x002CF308: ("camp_func_002cf308", 0),
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
        if (insn & 0x0E000000) == 0x0A000000:
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = FUNC_ADDR + off
            target = (pc + 8 + imm24 * 4) & 0xFFFFFFFF
            if target in CALLEES:
                stub = STUB_BY_NAME[CALLEES[target][0]]
                rel = (stub - (pc + 8)) // 4
                struct.pack_into("<I", buf, off, (insn & 0xFF000000) | (rel & 0x00FFFFFF))
    return bytes(buf)


class Runner:
    def __init__(self, code_bytes: bytes, rodata_blobs: list[tuple[int, bytes]] | None = None) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x000F0000, 0x00010000)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(0x00500000, 0x00100000)
        self.uc.mem_map(0x08000000, 0x00100000)
        cpacr = self.uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, cpacr | (0xF << 20))
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_write(FUNC_ADDR, code_bytes)
        if rodata_blobs:
            for addr, data in rodata_blobs:
                self.uc.mem_write(addr, data)
        for stub_addr in ADDR_BY_STUB:
            self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE1A00000))

    def run(self, *, items: dict[int, tuple[int, int, int]]) -> dict:
        self.uc.mem_write(G_BASE_PTR + 4, struct.pack("<I", S1_ADDR))
        self.uc.mem_write(G_BASE_PTR + 12, struct.pack("<I", S3_ADDR))
        self.uc.mem_write(S1_ADDR, b"\xAA" * 0x26000)
        self.uc.mem_write(S3_ADDR, b"\x55" * 0x40)

        item_addrs: dict[int, int] = {}
        cursor = ITEM_POOL
        for idx, (item_id, flags, tag_b3) in items.items():
            buf = bytearray(0x50)
            struct.pack_into("<H", buf, 0, item_id)
            buf[3] = tag_b3 & 0xFF
            struct.pack_into("<H", buf, 6, flags)
            for off in (0x14, 0x16, 0x1A, 0x1C, 0x1E, 0x20, 0x22, 0x3C, 0x3E, 0x40, 0x42, 0x44, 0x46, 0x48, 0x4A):
                struct.pack_into("<H", buf, off, (idx * 17 + off) & 0xFFFF)
            self.uc.mem_write(cursor, bytes(buf))
            item_addrs[idx] = cursor
            cursor += 0x50

        trace: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr == TRAP_ADDR:
                uc.emu_stop()
                return
            if addr not in ADDR_BY_STUB:
                return
            target = ADDR_BY_STUB[addr]
            name, nargs = CALLEES[target]
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            args = (r0, r1)[:nargs]
            if name != "camp_func_002b9364" or r0 in item_addrs or r0 in (1, 0x500):
                trace.append((name, args))

            if name == "engine_func_002c4b30":
                uc.mem_write(r0, b"\x00" * r1)
            elif name == "engine_func_002c3b48":
                uc.mem_write(r0, b"\x5A" * r1)
            elif name == "camp_func_002b9364":
                uc.reg_write(arm.UC_ARM_REG_R0, item_addrs.get(r0, 0))
            elif name == "camp_func_002cf308":
                uc.reg_write(arm.UC_ARM_REG_R0, 0xCAFEBABE)
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=500000)
        finally:
            self.uc.hook_del(hook)

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "s3": bytes(self.uc.mem_read(S3_ADDR, 16)),
            "s1_mid": bytes(self.uc.mem_read(S1_ADDR + 0x917C, 0x20)),
            "s1_986c": bytes(self.uc.mem_read(S1_ADDR + 0x986C, 8)),
            "s1_a8c0": bytes(self.uc.mem_read(S1_ADDR + 0xA8C0, 0xE70)),
            "s1_slots": [
                bytes(self.uc.mem_read(S1_ADDR + 0xC22C + (idx - 1) * 0x34, 0x34))
                for idx in sorted(items)
            ],
            "s1_166": [
                self.uc.mem_read(S1_ADDR + 0x166 + i * 0x604, 1)[0]
                for i in range(0x18)
            ],
            "trace": trace,
        }


def build_cases() -> list[tuple[str, dict]]:
    return [
        ("empty_items", {"items": {}}),
        ("mixed_items", {"items": {1: (101, 0, 7), 3: (103, 1, 9), 50: (250, 3, 11), 0x500: (0x500, 1, 13)}}),
    ]


def run_suite(orig_code: bytes, cand_code: bytes, rodata_blobs: list[tuple[int, bytes]]) -> list[str]:
    failures: list[str] = []
    for name, kwargs in build_cases():
        orig = Runner(orig_code).run(**kwargs)
        cand = Runner(cand_code, rodata_blobs).run(**kwargs)
        if orig != cand:
            failures.append(f"{name}: mismatch")
    return failures


def run_negative_controls(orig_code: bytes, cpp_text: str, work_dir: Path) -> None:
    mutations = [
        ("wrong_slot_count", "i < 0x18u", "i < 0x17u"),
        ("wrong_item_count", "i < 0x500", "i < 0x4FF"),
        ("wrong_flag_mask", "if ((flags & 1u) != 0u)", "if ((flags & 2u) != 0u)"),
        ("wrong_e10", "*reinterpret_cast<u32*>(r4 + 0xD98u) = 0xE10u;", "*reinterpret_cast<u32*>(r4 + 0xD98u) = 0xE11u;"),
        ("wrong_tail_ret", "return camp_func_002cf308();", "camp_func_002cf308(); return 0u;"),
    ]
    for mut_name, old, new in mutations:
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_src = cpp_text.replace(old, new, 1)
        cand_code, rodata_blobs, _ = compile_candidate(work_dir, mut_src)
        failures = run_suite(orig_code, cand_code, rodata_blobs)
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_001a1000"
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
