#!/usr/bin/env python3
"""Differential test for batch 31 A part 7:
- func_003560bc (0x003560BC, 32 B)
- func_0035b084 (0x0035B084, 32 B)
- func_0035b0a4 (0x0035B0A4, 32 B)
- func_0038b618 (0x0038B618, 32 B)
- camp_func_0030ab70 (0x0030AB70, 36 B)
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

def test_func_003560bc():
    print("--- Testing func_003560bc ---")
    addr = 0x003560BC
    size = 32
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part7"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003560bc", tmp)

    sym_map = {}
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, self_ptr: int, method_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        method_target = 0x00290000
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == method_target:
                calls.append(("vtable_slot5", r0))
                uc.reg_write(UC_ARM_REG_R0, method_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=method_target, end=method_target)

        if self_ptr != 0:
            vtable_ptr = STACK_BASE + 0x2000
            # self points to vtable
            uc.mem_write(self_ptr, struct.pack("<I", vtable_ptr))
            # vtable[5] points to method_target (offset 0x14)
            uc.mem_write(vtable_ptr + 0x14, struct.pack("<I", method_target))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, self_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0),
        (STACK_BASE + 0x1000, 0x1234),
        (STACK_BASE + 0x1000, 0xCAFEBABE),
        (STACK_BASE + 0x1000, 0),
    ]

    for self_ptr, ret in cases:
        r1, c1 = run_one(orig_code, self_ptr, ret)
        r2, c2 = run_one(decomp_code, self_ptr, ret)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for self={hex(self_ptr)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for self={hex(self_ptr)}"

    print("func_003560bc: PASS")

def test_func_0035b084():
    print("--- Testing func_0035b084 ---")
    addr = 0x0035B084
    size = 32
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part7"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0035b084", tmp)

    sym_map = {
        "func_0035afc8": 0x0035AFC8,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, idx: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x0035AFC8:
                calls.append(("func_0035afc8", r0))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x0035AFC8, end=0x0035AFC8)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, idx)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x111),
        (1, 0x222),
        (2, 0x333),
        (3, 0x444),
        (4, 0x555),
        (5, 0x666),
        (10, 0x777),
        (0xFFFFFFFF, 0x888),
    ]

    for idx, hret in cases:
        r1, c1 = run_one(orig_code, idx, hret)
        r2, c2 = run_one(decomp_code, idx, hret)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for idx={idx}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for idx={idx}"

    print("func_0035b084: PASS")

def test_func_0035b0a4():
    print("--- Testing func_0035b0a4 ---")
    addr = 0x0035B0A4
    size = 32
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part7"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0035b0a4", tmp)

    sym_map = {
        "func_00128c48": 0x00128C48,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, idx: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00128C48:
                calls.append(("func_00128c48", r0))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00128C48, end=0x00128C48)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, idx)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x111),
        (1, 0x222),
        (2, 0x333),
        (3, 0x444),
        (4, 0x555),
        (5, 0x666),
        (10, 0x777),
        (0xFFFFFFFF, 0x888),
    ]

    for idx, hret in cases:
        r1, c1 = run_one(orig_code, idx, hret)
        r2, c2 = run_one(decomp_code, idx, hret)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for idx={idx}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for idx={idx}"

    print("func_0035b0a4: PASS")

def test_func_0038b618():
    print("--- Testing func_0038b618 ---")
    addr = 0x0038B618
    size = 32
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part7"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0038b618", tmp)

    sym_map = {
        "camp_func_0036136c": 0x0036136C,
        "func_003613d4": 0x003613D4,
        "func_003613e4": 0x003613E4,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, ret_3d4: int, ret_3e4: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x0036136C:
                calls.append(("camp_func_0036136c",))
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x003613D4:
                calls.append(("func_003613d4",))
                uc.reg_write(UC_ARM_REG_R0, ret_3d4)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x003613E4:
                calls.append(("func_003613e4",))
                uc.reg_write(UC_ARM_REG_R0, ret_3e4)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x0036136C, end=0x0036136C)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x003613D4, end=0x003613D4)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x003613E4, end=0x003613E4)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x1234),
        (0, 0),
        (1, 0x9999),
        (0x42, 0x8888),
        (0xDEADBEEF, 0x7777),
    ]

    for ret_3d4, ret_3e4 in cases:
        r1, c1 = run_one(orig_code, ret_3d4, ret_3e4)
        r2, c2 = run_one(decomp_code, ret_3d4, ret_3e4)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for 3d4={ret_3d4}, 3e4={ret_3e4}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for 3d4={ret_3d4}, 3e4={ret_3e4}"

    print("func_0038b618: PASS")

def test_camp_func_0030ab70():
    print("--- Testing camp_func_0030ab70 ---")
    addr = 0x0030AB70
    size = 36
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part7"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_0030ab70", tmp)

    sym_map = {
        "script_vm_func_00290694": 0x00290694,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, byte_val: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00290694:
                calls.append(("script_vm_func_00290694",))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00290694, end=0x00290694)

        obj_ptr = STACK_BASE + 0x1000
        # 0x0043DD50 holds pointer to obj
        uc.mem_write(0x0043DD50, struct.pack("<I", obj_ptr))
        # obj + 0x5C4 holds byte_val
        uc.mem_write(obj_ptr + 0x5C4, bytes([byte_val & 0xFF]))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x55),
        (0, 0xCAFE),
        (1, 0x55),
        (255, 0xCAFE),
        (0x42, 0x10),
    ]

    for byte_val, hret in cases:
        r1, c1 = run_one(orig_code, byte_val, hret)
        r2, c2 = run_one(decomp_code, byte_val, hret)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for byte={byte_val}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for byte={byte_val}"

    print("camp_func_0030ab70: PASS")

if __name__ == "__main__":
    test_func_003560bc()
    test_func_0035b084()
    test_func_0035b0a4()
    test_func_0038b618()
    test_camp_func_0030ab70()
    print("\nALL 5 FUNCTIONS IN BATCH 31 A PART 7 PASSED WITH 100% DIFFERENTIAL FIDELITY!")
