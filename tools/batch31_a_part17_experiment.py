#!/usr/bin/env python3
"""Differential test for batch 31 A part 17:
- script_vm_func_00339a5c (0x00339A5C, 56 B)
- camp_func_0035a238 (0x0035A238, 56 B)
- func_00368cc0 (0x00368CC0, 56 B)
- func_0036c070 (0x0036C070, 56 B)
- func_00376b4c (0x00376B4C, 56 B)
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

def test_script_vm_func_00339a5c():
    print("--- Testing script_vm_func_00339a5c ---")
    addr = 0x00339A5C
    size = 56
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part17"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_00339a5c", tmp)

    sym_map = {
        "script_vm_func_00152af8": 0x00152AF8,
        "script_vm_func_002a7aa0": 0x002A7AA0,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, has_sub: bool, flag: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj_ptr = STACK_BASE + 0x1000
        sub_ptr = STACK_BASE + 0x6000
        p_ptr = STACK_BASE + 0x7000

        if has_sub:
            uc.mem_write(obj_ptr + 0x4398, struct.pack("<I", sub_ptr))
            uc.mem_write(sub_ptr + 8, struct.pack("<I", p_ptr))
            uc.mem_write(p_ptr + 0xC, struct.pack("<i", flag))
        else:
            uc.mem_write(obj_ptr + 0x4398, b"\x00\x00\x00\x00")

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00152AF8:
                calls.append(("script_vm_func_00152af8", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002A7AA0:
                calls.append(("script_vm_func_002a7aa0", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00152AF8, end=0x00152AF8)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002A7AA0, end=0x002A7AA0)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, obj_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00330000)

        uc.emu_start(addr, 0x00330000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        final_slot = struct.unpack("<I", uc.mem_read(obj_ptr + 0x4398, 4))[0]
        return res, final_slot, calls

    cases = [
        (False, 0),
        (True, -1),
        (True, -100),
        (True, 0),
        (True, 1),
        (True, 50),
    ]

    for has_sub, flag in cases:
        r_orig, s_orig, c_orig = run_one(orig_code, has_sub, flag)
        r_decomp, s_decomp, c_decomp = run_one(decomp_code, has_sub, flag)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)}"
        assert s_orig == s_decomp, f"slot mismatch: {hex(s_orig)} vs {hex(s_decomp)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("script_vm_func_00339a5c: PASS")

def test_camp_func_0035a238():
    print("--- Testing camp_func_0035a238 ---")
    addr = 0x0035A238
    size = 56
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part17"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_0035a238", tmp)

    sym_map = {
        "camp_func_00139ae0": 0x00139AE0,
        "nn_sdk_func_002bbd10": 0x002BBD10,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, helper_ret: int, buf_word: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00139AE0:
                calls.append(("camp_func_00139ae0", r1, r2))
                uc.mem_write(r0, struct.pack("<I", buf_word))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002BBD10:
                calls.append(("nn_sdk_func_002bbd10", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00139AE0, end=0x00139AE0)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002BBD10, end=0x002BBD10)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00350000)

        uc.emu_start(addr, 0x00350000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x00),
        (0, 0x20),
        (0, 0xFFFFFFFF),
        (0, 0xDF),
        (-1, 0x20),
        (-10, 0x00),
    ]

    for hret, bword in cases:
        r_orig, c_orig = run_one(orig_code, hret, bword)
        r_decomp, c_decomp = run_one(decomp_code, hret, bword)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)} for hret={hret}, bword={hex(bword)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("camp_func_0035a238: PASS")

def test_func_00368cc0():
    print("--- Testing func_00368cc0 ---")
    addr = 0x00368CC0
    size = 56
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part17"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00368cc0", tmp)

    sym_map = {}
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, vtable_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        self_ptr = STACK_BASE + 0x1000
        vtable_ptr = STACK_BASE + 0x2000
        fn_ptr = 0x002C9990

        uc.mem_write(self_ptr, struct.pack("<I", vtable_ptr))
        uc.mem_write(vtable_ptr + 8, struct.pack("<I", fn_ptr))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == fn_ptr:
                calls.append(("vtable_fn", r0, r1, r2))
                uc.reg_write(UC_ARM_REG_R0, vtable_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=fn_ptr, end=fn_ptr)

        if vtable_ret != 0:
            uc.mem_write(vtable_ret, b"\x00\x00\x00\x00\x00\x00\x00\x00")

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, self_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00360000)

        uc.emu_start(addr, 0x00360000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)

        out_data = b""
        if vtable_ret != 0:
            out_data = uc.mem_read(vtable_ret, 8)
        return res, out_data, calls

    cases = [
        0,
        STACK_BASE + 0x3000,
    ]

    for vret in cases:
        r_orig, d_orig, c_orig = run_one(orig_code, vret)
        r_decomp, d_decomp, c_decomp = run_one(decomp_code, vret)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)}"
        assert d_orig == d_decomp, f"data mismatch: {d_orig} vs {d_decomp}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("func_00368cc0: PASS")

def test_func_0036c070():
    print("--- Testing func_0036c070 ---")
    addr = 0x0036C070
    size = 56
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part17"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0036c070", tmp)

    sym_map = {}
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, vtable_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        self_ptr = STACK_BASE + 0x1000
        vtable_ptr = STACK_BASE + 0x2000
        fn_ptr = 0x002C9990

        uc.mem_write(self_ptr, struct.pack("<I", vtable_ptr))
        uc.mem_write(vtable_ptr + 8, struct.pack("<I", fn_ptr))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == fn_ptr:
                calls.append(("vtable_fn", r0, r1, r2))
                uc.reg_write(UC_ARM_REG_R0, vtable_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=fn_ptr, end=fn_ptr)

        if vtable_ret != 0:
            uc.mem_write(vtable_ret, b"\x00\x00\x00\x00\x00\x00\x00\x00")

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, self_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00360000)

        uc.emu_start(addr, 0x00360000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)

        out_data = b""
        if vtable_ret != 0:
            out_data = uc.mem_read(vtable_ret, 8)
        return res, out_data, calls

    cases = [
        0,
        STACK_BASE + 0x3000,
    ]

    for vret in cases:
        r_orig, d_orig, c_orig = run_one(orig_code, vret)
        r_decomp, d_decomp, c_decomp = run_one(decomp_code, vret)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)}"
        assert d_orig == d_decomp, f"data mismatch: {d_orig} vs {d_decomp}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("func_0036c070: PASS")

def test_func_00376b4c():
    print("--- Testing func_00376b4c and func_00376b78 ---")
    addr = 0x00376B4C
    size = 56
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part17"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00376b4c", tmp)

    sym_map = {
        "func_00379c14": 0x00379C14,
        "func_00379bcc": 0x00379BCC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one_4c(code: bytes, c14_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        self_ptr = STACK_BASE + 0x1000
        inner_ptr = STACK_BASE + 0x2000

        uc.mem_write(self_ptr, b"\x00\x00\x00\x00")
        uc.mem_write(inner_ptr + 0xC, b"\x00\x00\x00\x00")

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00379C14:
                calls.append(("func_00379c14", r0))
                uc.reg_write(UC_ARM_REG_R0, c14_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x00379BCC:
                calls.append(("func_00379bcc", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00379C14, end=0x00379C14)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00379BCC, end=0x00379BCC)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, self_ptr)
        uc.reg_write(UC_ARM_REG_R1, inner_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        stored_self = struct.unpack("<I", uc.mem_read(self_ptr, 4))[0]
        stored_inner_c = struct.unpack("<I", uc.mem_read(inner_ptr + 0xC, 4))[0]
        return res, stored_self, stored_inner_c, calls

    for c14_ret in [0, 1]:
        r_orig, s_orig, ic_orig, c_orig = run_one_4c(orig_code, c14_ret)
        r_decomp, s_decomp, ic_decomp, c_decomp = run_one_4c(decomp_code, c14_ret)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)}"
        assert s_orig == s_decomp, f"stored_self mismatch: {hex(s_orig)} vs {hex(s_decomp)}"
        assert ic_orig == ic_decomp, f"stored_inner_c mismatch: {hex(ic_orig)} vs {hex(ic_decomp)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"

    # Test func_00376b78 entry point
    comp_78, relocs_78 = compile_function("func_00376b78", tmp)
    decomp_code_78 = stage_body(comp_78, relocs_78, 0x00376B78, {})
    orig_code_78 = orig_code[44:56]

    def run_one_78(code: bytes):
        uc = create_emulator()
        uc.mem_write(0x00376B78, code)

        target_ptr = STACK_BASE + 0x1000
        uc.mem_write(target_ptr, b"\xFF\xFF\xFF\xFF")

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, target_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(0x00376B78, 0x00370000, timeout=10000000)
        val = struct.unpack("<I", uc.mem_read(target_ptr, 4))[0]
        return val

    assert run_one_78(orig_code_78) == 0
    assert run_one_78(decomp_code_78) == 0

    print("func_00376b4c: PASS")

if __name__ == "__main__":
    test_script_vm_func_00339a5c()
    test_camp_func_0035a238()
    test_func_00368cc0()
    test_func_0036c070()
    test_func_00376b4c()
    print("ALL PART 17 TESTS PASSED!")
