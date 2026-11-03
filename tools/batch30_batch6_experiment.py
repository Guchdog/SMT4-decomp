#!/usr/bin/env python3
"""Differential test for batch 30 part 6:
- camp_func_00262edc (0x00262EDC, 144 B)
- script_vm_func_002649c0 (0x002649C0, 136 B)
- func_0026f370 (0x0026F370, 136 B)
- script_vm_func_00276c24 (0x00276C24, 136 B)
- camp_func_00289044 (0x00289044, 140 B)
"""

from __future__ import annotations

from pathlib import Path
import struct
import sys

from unicorn import (
    Uc,
    UC_ARCH_ARM,
    UC_MODE_ARM,
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
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
    UC_ARM_REG_S0,
    UC_ARM_REG_S1,
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
SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

def load_original_bytes(addr: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(addr - CODE_BASE)
        return f.read(size)

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch30_c.o"
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

    uc.mem_map(STACK_BASE, STACK_SIZE)
    # Extra data page
    uc.mem_map(0x20000000, 0x20000)
    # Map high global region 0x00490000 - 0x004A0000
    uc.mem_map(0x00490000, 0x20000)
    return uc

def test_00262edc():
    print("--- Testing camp_func_00262edc ---")
    addr = 0x00262EDC
    size = 144
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("camp_func_00262edc", ROOT / "build")
    symbol_map = {
        "camp_func_0026ace0": 0x0026ACE0,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    BASE_PTR = 0x20000000
    OBJ = BASE_PTR + 0x90
    ITEMS = OBJ + 0x78

    def run_one(c_bytes, count, items, target_id):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Set 0x0043E2A8 + 4 -> BASE_PTR
        uc.mem_write(0x0043E2A8 + 4, struct.pack("<I", BASE_PTR))

        # Write items
        for i, it in enumerate(items):
            uc.mem_write(ITEMS + i * 2, struct.pack("<H", it))

        # Stub 0x0026ACE0: return count
        # mov r0, count; bx lr
        stub = struct.pack("<I", 0xE3A00000 | (count & 0xFF)) + b"\x1e\xff\x2f\xe1"
        uc.mem_write(0x0026ACE0, stub)

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, target_id)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)

        def hook_fault(uc, access, address, size, value, ud):
            print(f"FAULT access={access}, addr=0x{address:08X}, pc=0x{uc.reg_read(UC_ARM_REG_R0):08X}")
            return False
        from unicorn import UC_HOOK_MEM_UNMAPPED
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_fault)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
        }

    test_cases = [
        (5, [10, 20, 30, 40, 50], 10), # match at 0 (odd)
        (5, [10, 20, 30, 40, 50], 30), # match at 2
        (5, [10, 20, 30, 40, 50], 50), # match at 4
        (5, [10, 20, 30, 40, 50], 99), # no match
        (6, [11, 22, 33, 44, 55, 66], 44), # match in unrolled pair
        (6, [11, 22, 33, 44, 55, 66], 55), # match second of pair
        (6, [11, 22, 33, 44, 55, 66], 99), # no match
        (0, [], 10), # count 0
    ]

    for count, items, target_id in test_cases:
        o = run_one(orig, count, items, target_id)
        c = run_one(staged, count, items, target_id)
        assert o == c, f"00262edc failed: {o} vs {c}"
    print("camp_func_00262edc: PASS")

def test_002649c0():
    print("--- Testing script_vm_func_002649c0 ---")
    addr = 0x002649C0
    size = 136
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_002649c0", ROOT / "build")
    staged = stage_body(comp, relocs, addr, {})

    TARGET = 0x0049F91C
    SRC1 = 0x20000000
    SRC2 = 0x20000100

    def run_one(c_bytes):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # 0x00447060 -> SRC1
        uc.mem_write(0x00447060, struct.pack("<I", SRC1))
        # 0x00447E88 -> SRC2
        uc.mem_write(0x00447E88, struct.pack("<I", SRC2))

        # Fill SRC1 and SRC2 with known pattern
        src1_data = bytearray(0x80)
        struct.pack_into("<I", src1_data, 0x40, 0x11112222)
        struct.pack_into("<I", src1_data, 0x48, 0x33334444)
        uc.mem_write(SRC1, bytes(src1_data))

        src2_data = bytearray(0x80)
        struct.pack_into("<3f", src2_data, 0x1C, 1.5, 2.5, 3.5)
        struct.pack_into("<I", src2_data, 0x4C, 0x55556666)
        uc.mem_write(SRC2, bytes(src2_data))

        # Fill TARGET with garbage and preset offset 8
        target_data = bytearray(b"\xAA" * 0x350)
        struct.pack_into("<I", target_data, 0x08, 0x77778888)
        uc.mem_write(TARGET, bytes(target_data))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)

        def hook_fault(uc, access, address, size, value, ud):
            print(f"FAULT access={access}, addr=0x{address:08X}, pc=0x{uc.reg_read(UC_ARM_REG_R0):08X}")
            return False
        from unicorn import UC_HOOK_MEM_UNMAPPED
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_fault)

        uc.emu_start(addr, lr, timeout=3000000)
        return uc.mem_read(TARGET + 0x2F0, 0x50)

    o = run_one(orig)
    c = run_one(staged)
    assert o == c, "002649c0 target memory mismatch"
    print("script_vm_func_002649c0: PASS")

def test_0026f370():
    print("--- Testing func_0026f370 ---")
    addr = 0x0026F370
    size = 136
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_0026f370", ROOT / "build")
    symbol_map = {
        "func_002c55e4": 0x002C55E4,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    OUT_VAL = 0x20000000

    def run_one(c_bytes, curr_step, total_steps, start_val, target_val, stub_ret):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Stub 0x002C55E4: returns stub_ret in s0
        # vldr s0, [pc, #0]; bx lr; .word stub_ret
        stub = (
            b"\x00\x0a\x9f\xed" # vldr s0, [pc, #0]
            b"\x1e\xff\x2f\xe1" # bx lr
            + struct.pack("<f", stub_ret)
        )
        uc.mem_write(0x002C55E4, stub)

        uc.mem_write(OUT_VAL, struct.pack("<f", -999.0))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, OUT_VAL)
        uc.reg_write(UC_ARM_REG_R1, curr_step)
        uc.reg_write(UC_ARM_REG_R2, total_steps)

        start_int = struct.unpack("<I", struct.pack("<f", start_val))[0]
        target_int = struct.unpack("<I", struct.pack("<f", target_val))[0]
        uc.reg_write(UC_ARM_REG_S0, start_int)
        uc.reg_write(UC_ARM_REG_S1, target_int)

        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)
        uc.reg_write(UC_ARM_REG_R7, 0x44444444)
        uc.reg_write(UC_ARM_REG_R8, 0x55555555)

        def hook_fault(uc, access, address, size, value, ud):
            print(f"FAULT access={access}, addr=0x{address:08X}, pc=0x{uc.reg_read(UC_ARM_REG_R0):08X}")
            return False
        from unicorn import UC_HOOK_MEM_UNMAPPED
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_fault)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "out_val": struct.unpack("<f", uc.mem_read(OUT_VAL, 4))[0],
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
            "r8": uc.reg_read(UC_ARM_REG_R8),
        }

    cases = [
        # curr_step, total_steps, start_val, target_val, stub_ret
        (2, 10, 0.0, 10.0, 2.0), # increasing, not yet at target
        (9, 10, 0.0, 10.0, 11.0), # increasing, overshoot target -> clamp & return 1
        (10, 10, 0.0, 10.0, 8.0), # reached end step -> return 1
        (3, 10, 10.0, 0.0, 7.0), # decreasing, not yet at target
        (8, 10, 10.0, 0.0, -1.0), # decreasing, undershoot target -> clamp & return 1
        (10, 10, 10.0, 0.0, 2.0), # reached end step decreasing -> return 1
    ]
    for cs, ts, sv, tv, sr in cases:
        o = run_one(orig, cs, ts, sv, tv, sr)
        c = run_one(staged, cs, ts, sv, tv, sr)
        assert o["ret"] == c["ret"], f"0026f370 ret mismatch: {o} vs {c}"
        assert abs(o["out_val"] - c["out_val"]) < 1e-4, f"0026f370 out_val mismatch: {o} vs {c}"
        assert o["r4"] == c["r4"], "r4 mismatch"
        assert o["r5"] == c["r5"], "r5 mismatch"
        assert o["r6"] == c["r6"], "r6 mismatch"
        assert o["r7"] == c["r7"], "r7 mismatch"
        assert o["r8"] == c["r8"], "r8 mismatch"
    print("func_0026f370: PASS")

def test_00276c24():
    print("--- Testing script_vm_func_00276c24 ---")
    addr = 0x00276C24
    size = 136
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_00276c24", ROOT / "build")
    symbol_map = {
        "script_vm_func_0024c538": 0x0024C538,
        "script_vm_func_0027d9b8": 0x0027D9B8,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    QUERY = 0x0049FD14
    ENTRIES = [0x20000000 + i * 16 for i in range(10)]

    def run_one(c_bytes, p0, p1, p2, entries_data):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Clear query buffer
        uc.mem_write(QUERY, struct.pack("<4I", 0, 0, 0, 0))

        # Write entry tables
        for i, ed in enumerate(entries_data):
            uc.mem_write(ENTRIES[i], struct.pack("<bbBB", ed[0], ed[1], ed[2] & 0xFF, ed[3] & 0xFF))

        # Stub 0x0024C538: return len(entries_data)
        count = len(entries_data)
        stub_cnt = struct.pack("<I", 0xE3A00000 | (count & 0xFF)) + b"\x1e\xff\x2f\xe1"
        uc.mem_write(0x0024C538, stub_cnt)

        # Stub 0x0027D9B8: return ENTRIES[r0]
        # ldr r1, =0x20000000; add r0, r1, r0, lsl #4; bx lr
        stub_lookup = (
            b"\x04\x10\x9f\xe5" # ldr r1, [pc, #4] -> literal at offset 12
            b"\x00\x02\x81\xe0" # add r0, r1, r0, lsl #4
            b"\x1e\xff\x2f\xe1" # bx lr
            + struct.pack("<I", 0x20000000)
        )
        uc.mem_write(0x0027D9B8, stub_lookup)

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, p0)
        uc.reg_write(UC_ARM_REG_R1, p1)
        uc.reg_write(UC_ARM_REG_R2, p2)

        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)
        uc.reg_write(UC_ARM_REG_R7, 0x44444444)
        uc.reg_write(UC_ARM_REG_R8, 0x55555555)

        def hook_fault(uc, access, address, size, value, ud):
            print(f"FAULT access={access}, addr=0x{address:08X}, pc=0x{uc.reg_read(UC_ARM_REG_R0):08X}")
            return False
        from unicorn import UC_HOOK_MEM_UNMAPPED
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_fault)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "query": uc.mem_read(QUERY, 16),
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
            "r8": uc.reg_read(UC_ARM_REG_R8),
        }

    sample_entries = [
        [1, 2, 3, 42],
        [5, 6, 7, 99],
        [10, 20, 30, 0xFF], # sentinel entry
        [-5, -10, 4, 15],
    ]

    cases = [
        (1, 2, 3), # matches entry 0 -> 42
        (5, 6, 7), # matches entry 1 -> 99
        (10, 20, 30), # matches sentinel 0xFF -> -1
        (99, 99, 99), # no match -> -1
        (1, 2, -1), # p2 == -1 -> early return -1
    ]

    for p0, p1, p2 in cases:
        o = run_one(orig, p0, p1, p2, sample_entries)
        c = run_one(staged, p0, p1, p2, sample_entries)
        assert o == c, f"00276c24 mismatch ({p0},{p1},{p2}): {o} vs {c}"
    print("script_vm_func_00276c24: PASS")

def test_00289044():
    print("--- Testing camp_func_00289044 ---")
    addr = 0x00289044
    size = 140
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("camp_func_00289044", ROOT / "build")
    symbol_map = {
        "script_vm_func_002b66ec": 0x002B66EC,
        "camp_func_002a8a08": 0x002A8A08,
        "camp_func_002a89e4": 0x002A89E4,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    P_SINGLE = 0x20000000
    BASE = 0x20001000
    ENTITY = 0x20002000

    def run_one(c_bytes, threshold, filter_id, single_val, slot_active, entity_id, entity_val):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Single structure at P_SINGLE
        uc.mem_write(P_SINGLE + 0x1C, struct.pack("<h", single_val))
        # Stub 0x002B66EC: return P_SINGLE
        uc.mem_write(0x002B66EC, (
            b"\x00\x00\x9f\xe5\x1e\xff\x2f\xe1" + struct.pack("<I", P_SINGLE)
        ))

        # Base structure
        base_data = bytearray(0x9200)
        # Put slot_active at 0x90F0
        struct.pack_into("<b", base_data, 0x90F0, slot_active)
        uc.mem_write(BASE, bytes(base_data))

        # Stub 0x002A8A08: return BASE
        uc.mem_write(0x002A8A08, (
            b"\x00\x00\x9f\xe5\x1e\xff\x2f\xe1" + struct.pack("<I", BASE)
        ))

        # Entity structure at ENTITY
        entity_data = bytearray(0x80)
        struct.pack_into("<h", entity_data, 0x0E, entity_val)
        struct.pack_into("<H", entity_data, 0x46, entity_id)
        uc.mem_write(ENTITY, bytes(entity_data))

        # Stub 0x002A89E4: return ENTITY if r0 >= 0 else 0
        uc.mem_write(0x002A89E4, (
            b"\x00\x00\x50\xe3" # cmp r0, #0
            b"\x00\x00\xa0\xb3" # movlt r0, #0
            b"\x00\x00\x9f\xa5" # ldrge r0, [pc, #0]
            b"\x1e\xff\x2f\xe1" # bx lr
            + struct.pack("<I", ENTITY)
        ))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, threshold)
        uc.reg_write(UC_ARM_REG_R1, filter_id)

        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)
        uc.reg_write(UC_ARM_REG_R7, 0x44444444)
        uc.reg_write(UC_ARM_REG_R8, 0x55555555)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
            "r8": uc.reg_read(UC_ARM_REG_R8),
        }

    cases = [
        # threshold, filter_id, single_val, slot_active, entity_id, entity_val
        (50, -1, 30, -1, 0, 0), # filter < 0, val < threshold -> 1
        (50, -1, 60, -1, 0, 0), # filter < 0, val >= threshold -> 0
        (100, 5, 0, 0, 5, 80), # filter >= 0, match id, val < threshold -> 1
        (100, 5, 0, 0, 5, 120), # filter >= 0, match id, val >= threshold -> 0
        (100, 5, 0, 0, 8, 80), # filter >= 0, different id -> 0
        (100, 5, 0, -1, 5, 80), # filter >= 0, slot inactive -> 0
    ]

    for th, fid, sv, sa, eid, ev in cases:
        o = run_one(orig, th, fid, sv, sa, eid, ev)
        c = run_one(staged, th, fid, sv, sa, eid, ev)
        assert o == c, f"00289044 mismatch: {o} vs {c}"
    print("camp_func_00289044: PASS")

def main():
    test_00262edc()
    test_002649c0()
    test_0026f370()
    test_00276c24()
    test_00289044()
    print("\nALL 5 FUNCTIONS IN BATCH 6 PASSED DIFFERENTIAL VERIFICATION!")

if __name__ == "__main__":
    main()
