#!/usr/bin/env python3
"""Differential test for batch 31 A part 16:
- camp_func_003a65e4 (0x003A65E4, 48 B)
- engine_func_003ca154 (0x003CA154, 48 B)
- func_003df0d8 (0x003DF0D8, 48 B)
- func_0031124c (0x0031124C, 52 B)
- func_003a07d0 (0x003A07D0, 52 B)
"""

from __future__ import annotations

from pathlib import Path
import struct
import sys

from unicorn import (
    Uc,
    UC_ARCH_ARM,
    UC_MODE_ARM,
    UC_HOOK_MEM_UNMAPPED,
    UC_HOOK_CODE,
)
from unicorn.arm_const import (
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
    UC_ARM_REG_S0,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

COMPILED_FUNCTIONS = None
SOURCE = ROOT / "src/engine/leaf_batch31_a.cpp"

def load_original_bytes(addr: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(addr - CODE_BASE)
        return f.read(size)

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch31_a.o"
        result = compile_tu_armv6k(source, obj, ROOT)
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        COMPILED_FUNCTIONS = extract_elf_functions_detailed(obj)
    if func_name not in COMPILED_FUNCTIONS:
        raise RuntimeError(f"{func_name} not in object")
    return COMPILED_FUNCTIONS[func_name]

def stage_body(body: bytes, relocs, target_addr: int, symbol_map: dict[str, int]) -> bytes:
    data = bytearray(body)
    for reloc in relocs:
        sym = reloc.symbol_name
        if sym not in symbol_map:
            raise RuntimeError(f"Unmapped relocation: {sym}")
        stub_addr = symbol_map[sym]
        rel_off = stub_addr - (target_addr + reloc.offset + 8)
        imm24 = (rel_off >> 2) & 0x00FFFFFF
        inst = struct.unpack_from("<I", data, reloc.offset)[0]
        inst = (inst & 0xFF000000) | imm24
        struct.pack_into("<I", data, reloc.offset, inst)
    return bytes(data)

def hook_unmapped(uc, access, address, size, value, user_data):
    aligned = address & ~0xFFF
    try:
        uc.mem_map(aligned, 0x1000)
    except Exception:
        pass
    return True

def create_emulator():
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_unmapped)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    try:
        val = uc.reg_read(UC_ARM_REG_C1_C0_2)
        uc.reg_write(UC_ARM_REG_C1_C0_2, val | (0xF << 20))
        uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    except Exception:
        pass
    return uc

def test_camp_func_003a65e4():
    print("--- Testing camp_func_003a65e4 ---")
    addr = 0x003A65E4
    size = 48
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part16"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_003a65e4", tmp)

    sym_map = {
        "camp_func_002976ac": 0x002976AC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, init_val: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        # Counter is at 0x0044E06C
        uc.mem_write(0x0044E06C, struct.pack("<i", init_val))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002976AC:
                calls.append(("camp_func_002976ac", r0))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002976AC, end=0x002976AC)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x003A0000)

        uc.emu_start(addr, 0x003A0000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        final_val = struct.unpack("<i", uc.mem_read(0x0044E06C, 4))[0]
        return res, final_val, calls

    cases = [
        (5, 0x99),
        (1, 0x99),
        (0, 0x55),
        (-1, 0x77),
    ]

    for init_val, hret in cases:
        r_orig, v_orig, c_orig = run_one(orig_code, init_val, hret)
        r_decomp, v_decomp, c_decomp = run_one(decomp_code, init_val, hret)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)} for init={init_val}"
        assert v_orig == v_decomp, f"val mismatch: {v_orig} vs {v_decomp} for init={init_val}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("camp_func_003a65e4: PASS")

def test_engine_func_003ca154():
    print("--- Testing engine_func_003ca154 ---")
    addr = 0x003CA154
    size = 48
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part16"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_003ca154", tmp)

    sym_map = {
        "engine_func_002c4360": 0x002C4360,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, non_null_slots: list[int]):
        uc = create_emulator()
        uc.mem_write(addr, code)

        self_ptr = STACK_BASE + 0x1000
        # Clear 0x38 slots
        for i in range(0x38):
            uc.mem_write(self_ptr + 0x38 + i * 4, b"\x00\x00\x00\x00")

        # Set specific slots
        for s in non_null_slots:
            target = 0x20000000 + s * 0x10
            uc.mem_write(self_ptr + 0x38 + s * 4, struct.pack("<I", target))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002C4360:
                calls.append(("engine_func_002c4360", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C4360, end=0x002C4360)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, self_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x003C0000)

        uc.emu_start(addr, 0x003C0000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        [],
        [0],
        [0x37],
        [2, 15, 30, 55],
    ]

    for slots in cases:
        r_orig, c_orig = run_one(orig_code, slots)
        r_decomp, c_decomp = run_one(decomp_code, slots)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("engine_func_003ca154: PASS")

def test_func_003df0d8():
    print("--- Testing func_003df0d8 ---")
    addr = 0x003DF0D8
    size = 48
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part16"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003df0d8", tmp)

    sym_map = {}
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    # Load rodata table at 0x003FF7C8 from original binary
    table_bytes = load_original_bytes(0x003FF7C8, 32)

    def run_one(code: bytes, sub_present: bool, idx: int):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.mem_write(0x003FF7C8, table_bytes)

        arg_ptr = STACK_BASE + 0x1000
        sub_ptr = STACK_BASE + 0x2000

        if sub_present:
            uc.mem_write(arg_ptr + 0x10, struct.pack("<I", sub_ptr))
            uc.mem_write(sub_ptr + 0x10, struct.pack("<H", idx))
        else:
            uc.mem_write(arg_ptr + 0x10, b"\x00\x00\x00\x00")

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x003D0000)

        uc.emu_start(addr, 0x003D0000, timeout=10000000)
        s0_raw = uc.reg_read(UC_ARM_REG_S0)
        s0_float = struct.unpack("<f", struct.pack("<I", s0_raw))[0]
        return s0_float

    cases = [
        (False, 0),
        (True, 0),
        (True, 1),
        (True, 2),
        (True, 3),
        (True, 4),
        (True, 5),
    ]

    for pres, idx in cases:
        f_orig = run_one(orig_code, pres, idx)
        f_decomp = run_one(decomp_code, pres, idx)
        assert abs(f_orig - f_decomp) < 1e-5, f"float mismatch: {f_orig} vs {f_decomp} for pres={pres}, idx={idx}"
    print("func_003df0d8: PASS")

def test_func_0031124c():
    print("--- Testing func_0031124c ---")
    addr = 0x0031124C
    size = 52
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part16"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0031124c", tmp)

    sym_map = {
        "script_vm_func_002935ec": 0x002935EC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, glob_present: bool, a0: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        if glob_present:
            uc.mem_write(0x0043DCF0, struct.pack("<I", 0x10082000))
        else:
            uc.mem_write(0x0043DCF0, b"\x00\x00\x00\x00")

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002935EC:
                calls.append(("script_vm_func_002935ec", r0, r1))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002935EC, end=0x002935EC)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, a0)
        uc.reg_write(UC_ARM_REG_LR, 0x00310000)

        uc.emu_start(addr, 0x00310000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (False, 0, 0x55),
        (False, 0x1234, 0x55),
        (True, 0, 0x777),
        (True, 1, 0x888),
        (True, 0xABC, 0x999),
    ]

    for glob_pres, a0, hret in cases:
        r_orig, c_orig = run_one(orig_code, glob_pres, a0, hret)
        r_decomp, c_decomp = run_one(decomp_code, glob_pres, a0, hret)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)} for glob={glob_pres}, a0={a0}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("func_0031124c: PASS")

def test_func_003a07d0():
    print("--- Testing func_003a07d0 and func_003a07e0 ---")
    addr = 0x003A07D0
    size = 52
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part16"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003a07d0", tmp)

    sym_map = {
        "func_002347f4": 0x002347F4,
        "engine_func_002b2520": 0x002B2520,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    # 1. Test func_003a07d0 entry point
    def run_one_d0(code: bytes, a0: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002347F4:
                calls.append(("func_002347f4", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002B2520:
                calls.append(("engine_func_002b2520", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002347F4, end=0x002347F4)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002B2520, end=0x002B2520)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, a0)
        uc.reg_write(UC_ARM_REG_LR, 0x003A0000)

        uc.emu_start(addr, 0x003A0000, timeout=10000000)
        return calls

    for test_ptr in [0x10081000, 0x10082000]:
        c_orig = run_one_d0(orig_code, test_ptr)
        c_decomp = run_one_d0(decomp_code, test_ptr)
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"

    # 2. Test func_003a07e0 entry point
    comp_e0, relocs_e0 = compile_function("func_003a07e0", tmp)
    decomp_code_e0 = stage_body(comp_e0, relocs_e0, 0x003A07E0, {})

    def run_one_e0(code: bytes, x1: int, y1: int, x2: int, y2: int):
        uc = create_emulator()
        uc.mem_write(0x003A07E0, code)

        p1 = STACK_BASE + 0x1000
        p2 = STACK_BASE + 0x2000
        uc.mem_write(p1, struct.pack("<HH", x1, y1))
        uc.mem_write(p2, struct.pack("<HH", x2, y2))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, p1)
        uc.reg_write(UC_ARM_REG_R1, p2)
        uc.reg_write(UC_ARM_REG_LR, 0x003A0000)

        uc.emu_start(0x003A07E0, 0x003A0000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        if res & 0x80000000:
            res -= 0x100000000
        return res

    e0_orig_slice = orig_code[16:52]
    e0_cases = [
        (10, 20, 10, 20),
        (5, 20, 10, 20),
        (15, 20, 10, 20),
        (10, 15, 10, 20),
        (10, 25, 10, 20),
        (0, 0xFFFF, 0xFFFF, 0),
    ]

    for x1, y1, x2, y2 in e0_cases:
        r_orig = run_one_e0(e0_orig_slice, x1, y1, x2, y2)
        r_decomp = run_one_e0(decomp_code_e0, x1, y1, x2, y2)
        assert r_orig == r_decomp, f"result mismatch: {r_orig} vs {r_decomp} for ({x1},{y1}) vs ({x2},{y2})"

    print("func_003a07d0: PASS")

if __name__ == "__main__":
    test_camp_func_003a65e4()
    test_engine_func_003ca154()
    test_func_003df0d8()
    test_func_0031124c()
    test_func_003a07d0()
    print("ALL PART 16 TESTS PASSED!")
