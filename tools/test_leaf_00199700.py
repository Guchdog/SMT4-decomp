#!/usr/bin/env python3
"""Differential test for camp_func_00199700 (0x00199700) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts camp_func_00199700,
resolves camp_func_002bf030, script_vm_func_002b90e0, and script_vm_func_00296154,
and exhaustively compares all 20 switch modes (0..19) plus out-of-range (20)
and mutant negative controls.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SRC_CPP = ROOT / "src/engine/leaf_batch45_a.cpp"
FUNC_ADDR = 0x00199700
FUNC_SIZE = 848
FUNC_NAME = "camp_func_00199700"

STUB_BASE = 0x00110000
RODATA_BASE = 0x00120000
MEM_BASE = 0x20000000
MEM_SIZE = 0x00010000
SELF_ADDR = 0x20000000
STACK_TOP = 0x2000F000
TRAP_ADDR = 0x001F0000

CALLEES = {
    0x00296154: ("script_vm_func_00296154", 3),
    0x002B90E0: ("script_vm_func_002b90e0", 2),
    0x002BF030: ("camp_func_002bf030", 2),
}

STUB_ADDRS = {addr: STUB_BASE + idx * 4 for idx, addr in enumerate(sorted(CALLEES))}
ADDR_BY_STUB = {v: k for k, v in STUB_ADDRS.items()}
NAME_TO_STUB = {CALLEES[k][0]: v for k, v in STUB_ADDRS.items()}


def encode_arm_branch(pc: int, target: int, link: bool) -> int:
    imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if link else 0xEA000000
    return opcode | imm24


def patch_orig_code(raw: bytes) -> bytearray:
    code = bytearray(raw)
    for off in range(0, len(code), 4):
        insn = struct.unpack_from("<I", code, off)[0]
        cond = (insn >> 28) & 0xF
        op = (insn >> 24) & 0xF
        if cond != 0xF and op in (0xA, 0xB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = FUNC_ADDR + off
            target = pc + 8 + (imm24 << 2)
            if target in STUB_ADDRS:
                struct.pack_into("<I", code, off, encode_arm_branch(pc, STUB_ADDRS[target], link=(op == 0xB)))
    return code


def patch_cand_elf(obj_path: Path) -> tuple[bytearray, bytes]:
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
                    target = NAME_TO_STUB[s_name]
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
                        raise RuntimeError(f"Unsupported R_ARM_ABS32 section {sec_name(s_shndx)}")
                else:
                    raise RuntimeError(f"Unsupported relocation type {r_type} for {s_name}")
    return code, bytes(rodata_blob)


def build_candidate(src_text: str | None = None) -> tuple[bytearray, bytes]:
    out_dir = ROOT / "build" / "test_leaf_00199700"
    out_dir.mkdir(parents=True, exist_ok=True)
    if src_text is None:
        src_path = SRC_CPP
        obj_path = out_dir / "baseline.o"
    else:
        src_path = out_dir / "mutant.cpp"
        obj_path = out_dir / "mutant.o"
        src_path.write_text(src_text, encoding="utf-8")

    res = compile_tu_armv6k(src_path, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compile failed:\n{res.stderr}")
    return patch_cand_elf(obj_path)


class Runner:
    def __init__(self, rodata: bytes = b"") -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(STUB_BASE, 0x1000)
        self.uc.mem_map(RODATA_BASE, 0x10000)
        self.uc.mem_map(FUNC_ADDR & ~0xFFF, 0x2000)
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))
        if rodata:
            self.uc.mem_write(RODATA_BASE, rodata)

        for addr in STUB_ADDRS.values():
            self.uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, mode: int, val_2f8: int = 3) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)
        self.uc.mem_write(SELF_ADDR + 0x2F0, struct.pack("<III", mode, 0, val_2f8))

        call_log: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr not in ADDR_BY_STUB:
                return
            orig_target = ADDR_BY_STUB[addr]
            cname, arity = CALLEES[orig_target]
            regs = [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(3)]
            call_log.append((cname, regs[0] - SELF_ADDR, *regs[1:arity]))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_BASE, end=STUB_BASE + 0x100)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)
        finally:
            self.uc.hook_del(hook)

        return {"call_log": call_log}


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = patch_orig_code(raw_bin[off : off + FUNC_SIZE])
    src_text = SRC_CPP.read_text(encoding="utf-8")
    cand_code, rodata = build_candidate()
    print(f"{FUNC_NAME}: orig {len(orig_code)} B, cand {len(cand_code)} B")

    modes = list(range(21))
    for m in modes:
        orig_res = Runner().run(orig_code, m)
        cand_res = Runner(rodata).run(cand_code, m)
        if orig_res != cand_res:
            print(f"FAIL [mode={m}]:")
            print("  orig:", orig_res)
            print("  cand:", cand_res)
            return 1
    print(f"PASS [all {len(modes)} modes: 0..20]")

    mutants = [
        ("case4_stride", "i * 0x8Cu + 0xACu", "i * 0x88u + 0xACu"),
        ("case5_id", "0x59D9u", "0x59DAu"),
        ("case9_mul", "* 1000u + 1u", "* 1000u"),
        ("case15_mul", "v2f8 * 1000u);", "v2f8 * 1000u + 1u);"),
        ("case18_id", "0x67071u", "0x67072u"),
    ]
    for name, old, new in mutants:
        assert old in src_text, f"Mutant target not found: {old}"
        m_code, m_rodata = build_candidate(src_text.replace(old, new, 1))
        detected = False
        for m in modes:
            orig_res = Runner().run(orig_code, m)
            try:
                bad_res = Runner(m_rodata).run(m_code, m)
            except unicorn.UcError:
                detected = True
                break
            if orig_res != bad_res:
                detected = True
                break
        if not detected:
            print(f"FAIL [mutant {name}]: not detected!")
            return 1
        print(f"PASS [mutant {name} detected]")

    print(f"ALL PASS: {len(modes)} cases + {len(mutants)} negative controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
