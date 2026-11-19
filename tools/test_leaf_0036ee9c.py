#!/usr/bin/env python3
"""Differential test for engine_func_0036ee9c (0x0036ee9c) with Unicorn ARM."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_0036ee9c"

FUNC_ADDR = 0x0036EE9C
FUNC_SIZE = 640

T0_ADDR = 0x004091F8
BPP_ADDR = 0x00409268
DESC_ADDR = 0x20000000
ALLOC_ADDR = 0x20001000
VTBL_ADDR = 0x20001100
HEAP_BASE = 0x20002000
ALLOC_FN_ADDR = 0x00188000

STACK_BASE = 0x7F000000
STACK_SIZE = 0x10000
STACK_INIT = STACK_BASE + STACK_SIZE - 0x200
LR_SENTINEL = 0x90000000

CALLEE_SAVED = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}


def make_stub_bx_lr() -> bytes:
    return struct.pack("<I", 0xE12FFF1E)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_path = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_path)
    if res.returncode != 0:
        raise RuntimeError(f"compile failed:\n{res.stderr}")

    data = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    shdrs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = shdrs[e_shstrndx][4]

    def sh_name(idx: int) -> str:
        off = shstr_off + shdrs[idx][0]
        return data[off : data.index(b"\x00", off)].decode("ascii", errors="replace")

    tidx = next(i for i in range(e_shnum) if sh_name(i) == ".text")
    text_data = data[shdrs[tidx][4] : shdrs[tidx][4] + shdrs[tidx][5]]
    symtab = next(s for s in shdrs if s[1] == 2)
    strtab_off = shdrs[symtab[6]][4]

    fn_off = fn_size = None
    for i in range(symtab[5] // 16):
        st_name, st_value, st_size, st_info, _, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + i * 16)
        if st_shndx == tidx:
            name = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
            if name == "engine_func_0036ee9c":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("engine_func_0036ee9c not found in object")

    return bytes(text_data[fn_off : fn_off + fn_size])


def run_one(
    code_bytes: bytes,
    base_addr: int,
    t0_bytes: bytes,
    bpp_bytes: bytes,
    w: int,
    h: int,
    mips: int,
    f0c: int,
    f10: int,
    fmt: int,
    b18: int,
    b19: int,
) -> tuple[int, bytes, list[tuple], dict[str, int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(0x20000000, 0x00020000)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    cpacr = uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, cpacr | (0xF << 20))
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_write(base_addr, code_bytes)
    uc.mem_write(ALLOC_FN_ADDR, make_stub_bx_lr())
    uc.mem_write(T0_ADDR, t0_bytes)
    uc.mem_write(BPP_ADDR, bpp_bytes)

    desc = bytearray(0x20)
    struct.pack_into("<6I", desc, 0, w, h, mips, f0c, f10, fmt)
    desc[0x18] = b18
    desc[0x19] = b19
    uc.mem_write(DESC_ADDR, bytes(desc))

    uc.mem_write(ALLOC_ADDR, struct.pack("<I", VTBL_ADDR))
    uc.mem_write(VTBL_ADDR, struct.pack("<3I", 0, 0, ALLOC_FN_ADDR))
    uc.mem_write(HEAP_BASE, b"\xCD" * 0x4000)

    uc.reg_write(arm.UC_ARM_REG_R0, DESC_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, ALLOC_ADDR)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)
    uc.reg_write(arm.UC_ARM_REG_D8, 0x1122334455667788)
    uc.reg_write(arm.UC_ARM_REG_D9, 0x99AABBCCDDEEFF00)

    heap_ptr = [HEAP_BASE]
    calls: list[tuple] = []

    def hook_alloc(uc_inst, address, size, user_data):
        r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
        calls.append((r0, r1, r2))
        align = max(r2, 4)
        p = (heap_ptr[0] + align - 1) & ~(align - 1)
        heap_ptr[0] = p + ((r1 + 3) & ~3)
        uc_inst.reg_write(arm.UC_ARM_REG_R0, p)

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_alloc, begin=ALLOC_FN_ADDR, end=ALLOC_FN_ADDR)
    uc.emu_start(base_addr, LR_SENTINEL, count=100000)

    ret = uc.reg_read(arm.UC_ARM_REG_R0)
    used = heap_ptr[0] - HEAP_BASE
    heap_out = bytes(uc.mem_read(HEAP_BASE, used))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "d8": uc.reg_read(arm.UC_ARM_REG_D8),
        "d9": uc.reg_read(arm.UC_ARM_REG_D9),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return ret, heap_out, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    t0_bytes = orig_all[T0_ADDR - 0x00100000 : T0_ADDR - 0x00100000 + 0x70]
    bpp_bytes = orig_all[BPP_ADDR - 0x00100000 : BPP_ADDR - 0x00100000 + 0x40]
    cand_code = compile_candidate()

    cases = [
        ("fmt0_32x32_3mips_zero", 32, 32, 3, 0x11, 0x22, 0, 1, 1),
        ("fmt12_32x32_5mips_clamp16", 32, 32, 5, 0x33, 0x44, 0xC, 0, 1),
        ("fmt2_64x16_2mips_noalloc", 64, 16, 2, 0x55, 0x66, 2, 0, 0),
        ("fmt1_16x16_0mips_alloc0", 16, 16, 0, 0x77, 0x88, 1, 1, 1),
    ]

    for name, *args in cases:
        o_r, o_h, o_c, o_regs = run_one(orig_code, FUNC_ADDR, t0_bytes, bpp_bytes, *args)
        c_r, c_h, c_c, c_regs = run_one(cand_code, 0x00180000, t0_bytes, bpp_bytes, *args)
        if o_r != c_r or o_h != c_h:
            print(f"FAIL {name}: heap/ret mismatch orig=0x{o_r:08x} cand=0x{c_r:08x}")
            return 1
        if o_c != c_c:
            print(f"FAIL {name}: calls mismatch\n  orig={o_c}\n  cand={c_c}")
            return 1
        if o_regs != c_regs:
            print(f"FAIL {name}: callee-saved mismatch")
            return 1

    # 5 mutation controls
    def check_mutant(patch_fn, case_args):
        mc = bytearray(cand_code)
        if not patch_fn(mc):
            return False
        o_r, o_h, o_c, _ = run_one(orig_code, FUNC_ADDR, t0_bytes, bpp_bytes, *case_args)
        m_r, m_h, m_c, _ = run_one(bytes(mc), 0x00180000, t0_bytes, bpp_bytes, *case_args)
        return (m_r, m_h, m_c) != (o_r, o_h, o_c)

    def mut_const(old_val: int, new_val: int):
        def _fn(mc: bytearray) -> bool:
            for i in range(0, len(mc), 4):
                if struct.unpack_from("<I", mc, i)[0] == old_val:
                    struct.pack_into("<I", mc, i, new_val)
                    return True
            return False
        return _fn

    def mut_flip_cond(target_idx: int):
        def _fn(mc: bytearray) -> bool:
            seen = 0
            for i in range(0, len(mc), 4):
                w = struct.unpack_from("<I", mc, i)[0]
                if (w & 0x0E000000) == 0x0A000000 and (w >> 28) in (0x0, 0x1):
                    if seen == target_idx:
                        struct.pack_into("<I", mc, i, (w & 0x0FFFFFFF) | (((w >> 28) ^ 1) << 28))
                        return True
                    seen += 1
            return False
        return _fn

    mut_specs = [
        (mut_const(0x4D495854, 0x4D495855), cases[0][1:]),
        (mut_const(0x004091F8, 0x004091FC), cases[0][1:]),
        (mut_const(0xE3A0103C, 0xE3A01040), cases[0][1:]),
        (mut_const(0xE3A01020, 0xE3A01024), cases[0][1:]),
        (mut_const(0xE3A02080, 0xE3A02040), cases[0][1:]),
    ]
    mutants_ok = sum(1 for fn, cargs in mut_specs if check_mutant(fn, cargs))
    if mutants_ok != 5:
        print(f"FAIL: detected only {mutants_ok}/5 mutants")
        return 1

    print(
        f"PASS: engine_func_0036ee9c (0x{FUNC_ADDR:08x}) matched original across "
        f"{len(cases)} cases and detected {mutants_ok}/5 mutants "
        f"(candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
