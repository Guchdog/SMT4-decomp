#!/usr/bin/env python3
"""Differential test for script_vm_func_003b9e20 (0x003B9E20) using Unicorn ARM."""

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

FUNC_ADDR = 0x003B9E20
FUNC_SIZE = 984
FUNC_NAME = "script_vm_func_003b9e20"
TRAP_ADDR = 0x000F0000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000

G_FLAG_44CFB8 = 0x0044CFB8
SELF_ADDR = 0x004A0000
ENTRIES_BASE = 0x004A2000
D88_ADDR = 0x004A4000
D90_ADDR = 0x004A4100
E5C_ADDR = 0x004A4200
STACK_TOP = 0x08020000

CALLEES = {
    0x0022B3CC: "engine_func_0022b3cc",
    0x002BE7FC: "ui_func_002be7fc",
    0x00291018: "script_vm_func_00291018",
    0x002971E4: "script_vm_func_002971e4",
    0x0019DFBC: "script_vm_func_0019dfbc",
    0x002C0BA8: "script_vm_func_002c0ba8",
    0x0022BA6C: "engine_func_0022ba6c",
    0x002BD9EC: "script_vm_func_002bd9ec",
    0x00297128: "shop_func_00297128",
    0x0022B430: "engine_func_0022b430",
    0x0022B158: "engine_func_0022b158",
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
        top = (insn >> 24) & 0xFF
        if (insn & 0x0F000000) == 0x0B000000 or (top & 0xFE) == 0xFA:
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            h_bit = (insn >> 24) & 1 if (top & 0xFE) == 0xFA else 0
            pc = FUNC_ADDR + off
            target = (pc + 8 + imm24 * 4 + h_bit * 2) & ~3
            if target in CALLEES:
                stub = STUB_BY_NAME[CALLEES[target]]
                rel = (stub - (pc + 8)) // 4
                struct.pack_into("<I", buf, off, 0xEB000000 | (rel & 0x00FFFFFF))
    return bytes(buf)


def read_cstr(uc: unicorn.Uc, addr: int) -> bytes:
    out = bytearray()
    while len(out) < 32:
        b = uc.mem_read(addr + len(out), 1)[0]
        if b == 0:
            break
        out.append(b)
    return bytes(out)


class Runner:
    def __init__(self, code_bytes: bytes, rodata_blobs: list[tuple[int, bytes]] | None = None) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x000F0000, 0x00010000)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(0x08000000, 0x00100000)
        self.uc.mem_write(FUNC_ADDR, code_bytes)
        self.uc.mem_write(0x00404EB0, b"%s\x00")
        if rodata_blobs:
            for addr, data in rodata_blobs:
                self.uc.mem_write(addr, data)
        for stub_addr in ADDR_BY_STUB:
            self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE1A00000))

    def run(
        self,
        *,
        entries: tuple[tuple[int, bytes, int, int], ...],
        mode: int,
        flags_20: int = 0x40,
        s3c_self: int = -7,
        ba8_map: dict[int, int] | None = None,
        flag_44cfb8_set: int = 0,
    ) -> dict:
        ba8_map = ba8_map or {}
        self.uc.mem_write(G_FLAG_44CFB8, struct.pack("<I", 0x99))

        self_buf = bytearray(0xF00)
        struct.pack_into("<I", self_buf, 0x20, flags_20)
        struct.pack_into("<h", self_buf, 0x3C, s3c_self)
        struct.pack_into("<i", self_buf, 0x9C + 0x52C, len(entries))
        struct.pack_into("<I", self_buf, 0xD64, mode)
        struct.pack_into("<I", self_buf, 0xD88, D88_ADDR)
        struct.pack_into("<I", self_buf, 0xD90, D90_ADDR)
        struct.pack_into("<I", self_buf, 0xE5C, E5C_ADDR)
        self.uc.mem_write(SELF_ADDR, bytes(self_buf))

        entry_addrs: list[int] = []
        for idx, (kind, name_b, s3c, s3e) in enumerate(entries):
            addr = ENTRIES_BASE + idx * 0x80
            buf = bytearray(0x80)
            buf[0x2C : 0x2C + len(name_b) + 1] = name_b + b"\x00"
            struct.pack_into("<HH", buf, 0x3C, s3c, s3e)
            struct.pack_into("<H", buf, 0x54, kind)
            self.uc.mem_write(addr, bytes(buf))
            entry_addrs.append(addr)

        trace: list[tuple] = []
        poll_count = 0

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            nonlocal poll_count
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

            if name == "engine_func_0022b3cc":
                trace.append((name, r0, r1))
                uc.reg_write(arm.UC_ARM_REG_R0, entry_addrs[r1])
            elif name == "ui_func_002be7fc":
                fmt = read_cstr(uc, r1)
                arg = read_cstr(uc, r2)
                uc.mem_write(r0, arg + b"\x00")
                trace.append((name, fmt, arg))
            elif name == "script_vm_func_00291018":
                s = read_cstr(uc, r1)
                trace.append((name, r0, s))
                uc.reg_write(arm.UC_ARM_REG_R0, 0x100 + len(s))
            elif name == "script_vm_func_002971e4":
                poll_count = 0
                trace.append((name, r0, r1))
            elif name == "script_vm_func_0019dfbc":
                poll_count += 1
                trace.append((name, r0, poll_count))
                if poll_count >= 2:
                    if flag_44cfb8_set:
                        uc.mem_write(G_FLAG_44CFB8, struct.pack("<I", flag_44cfb8_set))
                    uc.reg_write(arm.UC_ARM_REG_R0, 2)
                else:
                    uc.reg_write(arm.UC_ARM_REG_R0, 1)
            elif name == "script_vm_func_002c0ba8":
                trace.append((name, r0))
                uc.reg_write(arm.UC_ARM_REG_R0, ba8_map.get(r0, 1))
            elif name == "engine_func_0022ba6c":
                trace.append((name, r0, r1))
            elif name == "script_vm_func_002bd9ec":
                vals = struct.unpack("<HHH", uc.mem_read(r1, 6))
                trace.append((name, r0, vals))
            elif name == "shop_func_00297128":
                trace.append((name,))
            elif name in ("engine_func_0022b430", "engine_func_0022b158"):
                trace.append((name, r0, r1, r2))
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=100000)
        finally:
            self.uc.hook_del(hook)

        return {
            "f20": struct.unpack("<I", self.uc.mem_read(SELF_ADDR + 0x20, 4))[0],
            "f28": struct.unpack("<II", self.uc.mem_read(SELF_ADDR + 0x28, 8)),
            "b6ce": self.uc.mem_read(SELF_ADDR + 0x6CE, 1)[0],
            "trace": trace,
        }


def build_cases() -> list[tuple[str, dict]]:
    e_zero = (3, b"0", 0, 0)
    e_k3_pass = (3, b"k3", 10, 11)
    e_k4_fail = (4, b"k4", 0, 0)
    e_k2_skip = (2, b"k2", 12, 0)
    return [
        ("m0_ok_no40", {"entries": (e_zero, e_k3_pass), "mode": 0, "flags_20": 0, "ba8_map": {10: 0, 0x15: 1}}),
        ("m0_ok_with40", {"entries": (), "mode": 0, "flags_20": 0x40, "ba8_map": {0x15: 1}}),
        ("m0_r8_zero", {"entries": (e_k4_fail,), "mode": 0}),
        ("m0_15_zero", {"entries": (), "mode": 0, "ba8_map": {0x15: 0}}),
        ("m1_flag_44cfb8", {"entries": ((3, b"x", 0, 0),), "mode": 1, "flag_44cfb8_set": 1}),
        ("m2_k2_skip", {"entries": (e_k2_skip,), "mode": 2, "ba8_map": {12: 0}}),
        ("m5_r8_one", {"entries": (), "mode": 5}),
        ("m5_r8_zero", {"entries": (e_k4_fail,), "mode": 5}),
        ("m6_no_10000000", {"entries": (), "mode": 6, "flags_20": 0}),
        ("m7_with_10000000", {"entries": (), "mode": 7, "flags_20": 0x10000000}),
        ("m8_default", {"entries": (), "mode": 8}),
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
        ("wrong_zero_char", "if (entry[0x2Cu] == 0x30u)", "if (entry[0x2Cu] == 0x31u)"),
        ("wrong_kind_4", "else if (kind == 4u)", "else if (kind == 9u)"),
        ("wrong_15_id", "script_vm_func_002c0ba8(0x15u)", "script_vm_func_002c0ba8(0x16u)"),
        ("wrong_flag_10000000", "((f & 0x10000000u) != 0u) ? 4u : 3u", "((f & 0x20000000u) != 0u) ? 4u : 3u"),
        ("wrong_mode5_r8", "case 5u:\n            if (r8 == 0u)", "case 5u:\n            if (r8 != 0u)"),
    ]
    for mut_name, old, new in mutations:
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_src = cpp_text.replace(old, new, 1)
        cand_code, rodata_blobs, _ = compile_candidate(work_dir, mut_src)
        failures = run_suite(orig_code, cand_code, rodata_blobs)
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_003b9e20"
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
