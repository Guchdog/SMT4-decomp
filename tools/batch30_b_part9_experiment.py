#!/usr/bin/env python3
"""Differential test for batch 30 B part 9:
- script_vm_func_0027054c (0x0027054C, 124 B)
- script_vm_func_00275c2c (0x00275C2C, 116 B)
- script_vm_func_002764d4 (0x002764D4, 124 B)
- script_vm_func_0027d9b8 (0x0027D9B8, 104 B)
- ui_func_002879c0 (0x002879C0, 124 B)
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
    UC_CPU_ARM_11MPCORE,
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_R4,
    UC_ARM_REG_R5,
    UC_ARM_REG_R6,
    UC_ARM_REG_R7,
    UC_ARM_REG_R8,
    UC_ARM_REG_SB,
    UC_ARM_REG_SL,
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
SOURCE = ROOT / "src/engine/leaf_batch30_b.cpp"

def load_original_bytes(addr: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(addr - CODE_BASE)
        return f.read(size)

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch30_b.o"
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

def setup_uc() -> Uc:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.ctl_set_cpu_model(UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(CODE_BASE, CODE_SIZE)
    with open(ORIG_BIN, "rb") as f:
        code_data = f.read(CODE_SIZE)
    uc.mem_write(CODE_BASE, code_data)

    uc.mem_map(0x00480000, 0x00100000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(0x20000000, 0x00100000)

    def hook_unmapped(uc, access, address, size, value, user_data):
        page = address & ~0xFFF
        try:
            uc.mem_map(page, 0x1000)
        except Exception:
            pass
        return True

    uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_unmapped)
    return uc


def test_0027054c():
    print("--- Testing script_vm_func_0027054c ---")
    addr = 0x0027054C
    size = 124
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_0027054c", ROOT / "build")

    STUB_FREE = 0x002C4360
    staged = stage_body(comp, relocs, addr, {
        "engine_func_002c4360": STUB_FREE,
    })

    BASE = 0x00446FE8
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, ptrs):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_FREE, stub_code)

        # Initialize base memory
        uc.mem_write(BASE, b"\xFF" * 0x40)
        for i, p in enumerate(ptrs):
            uc.mem_write(BASE + 0x18 + i * 4, struct.pack("<I", p))

        freed = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_FREE:
                r0 = uc.reg_read(UC_ARM_REG_R0)
                freed.append(r0)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        mem_after = uc.mem_read(BASE, 0x28)
        return freed, mem_after

    test_cases = [
        [0, 0, 0, 0],
        [0x20001000, 0x20002000, 0x20003000, 0x20004000],
        [0x20001000, 0, 0x20003000, 0],
        [0, 0, 0x20005000, 0x20006000],
    ]

    for ptrs in test_cases:
        f1, m1 = run_one(orig, ptrs)
        f2, m2 = run_one(staged, ptrs)
        assert f1 == f2, f"Freed mismatch: orig={f1}, comp={f2}"
        assert m1 == m2, f"Mem mismatch: orig={m1.hex()}, comp={m2.hex()}"
    print("script_vm_func_0027054c: PASS")


def test_00275c2c():
    print("--- Testing script_vm_func_00275c2c ---")
    addr = 0x00275C2C
    size = 116
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_00275c2c", ROOT / "build")

    STUB_REL = 0x002C0A6C
    staged = stage_body(comp, relocs, addr, {
        "ui_func_002c0a6c": STUB_REL,
    })

    PTR_MGR = 0x0043E278
    MGR = 0x20001000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, p_fdc, p_fe8, p_fe4):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_REL, stub_code)

        uc.mem_write(PTR_MGR, struct.pack("<I", MGR))
        uc.mem_write(MGR, b"\x00" * 0x1000)
        uc.mem_write(MGR + 0xE8C, struct.pack("<B", 1))
        uc.mem_write(MGR + 0xFDC, struct.pack("<I", p_fdc))
        uc.mem_write(MGR + 0xFE8, struct.pack("<I", p_fe8))
        uc.mem_write(MGR + 0xFE4, struct.pack("<I", p_fe4))

        released = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_REL:
                r0 = uc.reg_read(UC_ARM_REG_R0)
                released.append(r0)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        e8c = uc.mem_read(MGR + 0xE8C, 1)[0]
        fdc = struct.unpack_from("<I", uc.mem_read(MGR + 0xFDC, 4))[0]
        fe8 = struct.unpack_from("<I", uc.mem_read(MGR + 0xFE8, 4))[0]
        fe4 = struct.unpack_from("<I", uc.mem_read(MGR + 0xFE4, 4))[0]
        return released, e8c, fdc, fe8, fe4

    test_cases = [
        (0, 0, 0),
        (0x20002000, 0x20003000, 0x20004000),
        (0x20002000, 0, 0x20004000),
        (0, 0x20003000, 0),
    ]

    for p0, p1, p2 in test_cases:
        r1, e1, d1, e8_1, e4_1 = run_one(orig, p0, p1, p2)
        r2, e2, d2, e8_2, e4_2 = run_one(staged, p0, p1, p2)
        assert r1 == r2, f"Released mismatch: orig={r1}, comp={r2}"
        assert (e1, d1, e8_1, e4_1) == (e2, d2, e8_2, e4_2), "Memory state mismatch"
    print("script_vm_func_00275c2c: PASS")


def test_002764d4():
    print("--- Testing script_vm_func_002764d4 ---")
    addr = 0x002764D4
    size = 124
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_002764d4", ROOT / "build")

    STUB_SUB = 0x002C0EC4
    STUB_PAYLOAD = 0x002C0E9C
    STUB_COUNT = 0x002C0E4C

    staged = stage_body(comp, relocs, addr, {
        "Tbb_GetGlobalSubTable": STUB_SUB,
        "Tbb_GetPayloadData": STUB_PAYLOAD,
        "Tbb_GetRowCount": STUB_COUNT,
    })

    PTR_MGR = 0x00433158
    MGR = 0x20001000
    TABLE_HDR = 0x20003000
    PAYLOAD1 = 0x20004000
    PAYLOAD2 = 0x20006000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, index, count1, count2):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_SUB, stub_code)
        uc.mem_write(STUB_PAYLOAD, stub_code)
        uc.mem_write(STUB_COUNT, stub_code)

        uc.mem_write(PTR_MGR, struct.pack("<I", MGR))
        uc.mem_write(MGR, b"\x00" * 0x500)
        uc.mem_write(MGR + 0x40C, struct.pack("<I", count2))
        uc.mem_write(MGR + 0x410, struct.pack("<I", PAYLOAD2))

        def code_hook(uc, address, sz, user_data):
            if address == STUB_SUB:
                uc.reg_write(UC_ARM_REG_R0, TABLE_HDR)
            elif address == STUB_PAYLOAD:
                uc.reg_write(UC_ARM_REG_R0, PAYLOAD1)
            elif address == STUB_COUNT:
                uc.reg_write(UC_ARM_REG_R0, count1)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, index)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret

    test_cases = [
        # (index, count1, count2)
        (0, 5, 10),      # in table 1 -> PAYLOAD1 + 0*44
        (4, 5, 10),      # in table 1 -> PAYLOAD1 + 4*44
        (5, 5, 10),      # in table 2 -> PAYLOAD2 + 0*44
        (9, 5, 10),      # in table 2 -> PAYLOAD2 + 4*44
        (14, 5, 10),     # in table 2 -> PAYLOAD2 + 9*44
        (15, 5, 10),     # out of bounds -> 0
        (20, 5, 10),     # out of bounds -> 0
        (0, 0, 5),       # table 1 empty, in table 2
        (0, 0, 0),       # both empty -> 0
    ]

    for idx, c1, c2 in test_cases:
        r1 = run_one(orig, idx, c1, c2)
        r2 = run_one(staged, idx, c1, c2)
        assert r1 == r2, f"Ret mismatch: orig={hex(r1)}, comp={hex(r2)} for idx={idx}, c1={c1}, c2={c2}"
    print("script_vm_func_002764d4: PASS")


def test_0027d9b8():
    print("--- Testing script_vm_func_0027d9b8 ---")
    addr = 0x0027D9B8
    size = 104
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_0027d9b8", ROOT / "build")

    STUB_SUB = 0x002C0EC4
    STUB_PAYLOAD = 0x002C0E9C
    STUB_COUNT = 0x002C0E4C

    staged = stage_body(comp, relocs, addr, {
        "Tbb_GetGlobalSubTable": STUB_SUB,
        "Tbb_GetPayloadData": STUB_PAYLOAD,
        "Tbb_GetRowCount": STUB_COUNT,
    })

    PTR_MGR = 0x00433158
    MGR = 0x20001000
    TABLE_HDR = 0x20003000
    PAYLOAD1 = 0x20004000
    PAYLOAD2 = 0x20006000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, index, count1, count2):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_SUB, stub_code)
        uc.mem_write(STUB_PAYLOAD, stub_code)
        uc.mem_write(STUB_COUNT, stub_code)

        uc.mem_write(PTR_MGR, struct.pack("<I", MGR))
        uc.mem_write(MGR, b"\x00" * 0x500)
        uc.mem_write(MGR + 0x3EC, struct.pack("<I", count2))
        uc.mem_write(MGR + 0x3F0, struct.pack("<I", PAYLOAD2))

        def code_hook(uc, address, sz, user_data):
            if address == STUB_SUB:
                uc.reg_write(UC_ARM_REG_R0, TABLE_HDR)
            elif address == STUB_PAYLOAD:
                uc.reg_write(UC_ARM_REG_R0, PAYLOAD1)
            elif address == STUB_COUNT:
                uc.reg_write(UC_ARM_REG_R0, count1)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, index)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret

    test_cases = [
        # (index, count1, count2)
        (0, 5, 10),      # in table 1 -> PAYLOAD1 + 0*12
        (4, 5, 10),      # in table 1 -> PAYLOAD1 + 4*12
        (5, 5, 10),      # in table 2 -> PAYLOAD2 + 0*12
        (9, 5, 10),      # in table 2 -> PAYLOAD2 + 4*12
        (14, 5, 10),     # in table 2 -> PAYLOAD2 + 9*12
        (15, 5, 10),     # out of bounds -> 0
        (20, 5, 10),     # out of bounds -> 0
        (0, 0, 5),       # table 1 empty, in table 2
        (0, 0, 0),       # both empty -> 0
    ]

    for idx, c1, c2 in test_cases:
        r1 = run_one(orig, idx, c1, c2)
        r2 = run_one(staged, idx, c1, c2)
        assert r1 == r2, f"Ret mismatch: orig={hex(r1)}, comp={hex(r2)} for idx={idx}, c1={c1}, c2={c2}"
    print("script_vm_func_0027d9b8: PASS")


def test_002879c0():
    print("--- Testing ui_func_002879c0 ---")
    addr = 0x002879C0
    size = 124
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_002879c0", ROOT / "build")

    STUB_CHECK = 0x002A63F8
    staged = stage_body(comp, relocs, addr, {
        "ui_func_002a63f8": STUB_CHECK,
    })

    MODE_ADDR = 0x0044CF64
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, mode, check_result):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_CHECK, stub_code)

        uc.mem_write(MODE_ADDR, struct.pack("<I", mode))

        calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_CHECK:
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                calls.append((r0, r1))
                uc.reg_write(UC_ARM_REG_R0, check_result)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, calls

    test_cases = [
        # (mode, check_result)
        (0x65, 0),       # mode 0x65, check fails -> 0
        (0x65, 1),       # mode 0x65, check passes -> 1
        (0x66, 0),       # mode 0x66, check fails -> 0
        (0x66, 1),       # mode 0x66, check passes -> 1
        (0x67, 0),       # mode 0x67, check fails -> 0
        (0x67, 1),       # mode 0x67, check passes -> 1
        (0x64, 0),       # other mode -> no check, returns 1
        (0x68, 0),
        (0, 0),
    ]

    for mode, chk in test_cases:
        r1, c1 = run_one(orig, mode, chk)
        r2, c2 = run_one(staged, mode, chk)
        assert r1 == r2, f"Ret mismatch: orig={r1}, comp={r2} for mode={hex(mode)}"
        assert c1 == c2, f"Calls mismatch: orig={c1}, comp={c2} for mode={hex(mode)}"
    print("ui_func_002879c0: PASS")


def main():
    test_0027054c()
    test_00275c2c()
    test_002764d4()
    test_0027d9b8()
    test_002879c0()
    print("\nALL 5 FUNCTIONS IN BATCH 30 B PART 9 PASSED WITH 100% DIFFERENTIAL FIDELITY!")

if __name__ == "__main__":
    main()
