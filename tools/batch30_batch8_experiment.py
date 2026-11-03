#!/usr/bin/env python3
"""Differential test for batch 30 part 8:
- func_00269e54 (0x00269E54, 140 B)
- func_00256524 (0x00256524, 140 B)
- script_vm_func_00252630 (0x00252630, 140 B)
- engine_func_0024de78 (0x0024DE78, 136 B)
- unite_func_0022df7c (0x0022DF7C, 140 B)
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
    uc.mem_map(0x20000000, 0x80000)

    def hook_fault(uc, access, address, size, value, ud):
        print(f"FAULT access={access}, addr=0x{address:08X}")
        return False
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_fault)
    return uc

def test_00269e54():
    print("--- Testing func_00269e54 ---")
    addr = 0x00269E54
    size = 140
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_00269e54", ROOT / "build")
    staged = stage_body(comp, relocs, addr, {})

    ENTITY = 0x20000000
    R2_OBJ = 0x20001000
    TABLE = 0x20010000

    def run_one(c_bytes, default_val, obj_status, match_index, result_val, null_global=False):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Entity
        entity_data = bytearray(0x40)
        struct.pack_into("<h", entity_data, 0x0E, default_val)
        uc.mem_write(ENTITY, bytes(entity_data))

        # Set 0x00435D90 -> R2_OBJ or NULL
        if null_global:
            uc.mem_write(0x00435D90, struct.pack("<I", 0))
        else:
            uc.mem_write(0x00435D90, struct.pack("<I", R2_OBJ))

            r2_data = bytearray(0x2000)
            struct.pack_into("<I", r2_data, 0x64, obj_status)
            struct.pack_into("<I", r2_data, 0x1FC0, TABLE)
            uc.mem_write(R2_OBJ, bytes(r2_data))

            # Table: 109 entries, stride 648 (0x288)
            table_data = bytearray(109 * 648)
            if match_index is not None and match_index < 109:
                entry_off = match_index * 648
                # flags: bit 0 and bit 3 set, bit 6 (0x40) clear -> 0x09
                struct.pack_into("<I", table_data, entry_off, 0x09)
                struct.pack_into("<I", table_data, entry_off + 0x27C, ENTITY)
                struct.pack_into("<h", table_data, entry_off + 0x1B6, result_val)
            uc.mem_write(TABLE, bytes(table_data))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, ENTITY)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": struct.unpack("<h", struct.pack("<H", uc.reg_read(UC_ARM_REG_R0) & 0xFFFF))[0],
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
        }

    cases = [
        (100, 0, 5, 555, False),
        (100, 0, 0, 999, False),
        (100, 0, 108, -123, False),
        (100, 0, None, 0, False),
        (100, 0x15, 5, 555, False),
        (100, 0, 5, 555, True), # null global
    ]

    for dval, status, midx, rval, ng in cases:
        o = run_one(orig, dval, status, midx, rval, ng)
        c = run_one(staged, dval, status, midx, rval, ng)
        assert o == c, f"00269e54 mismatch: {o} vs {c}"
    print("func_00269e54: PASS")

def test_00256524():
    print("--- Testing func_00256524 ---")
    addr = 0x00256524
    size = 140
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_00256524", ROOT / "build")
    staged = stage_body(comp, relocs, addr, {})

    CTX_BASE = 0x20000000

    def run_one(c_bytes, r0_val, r1_val):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Context pre-fill with pattern
        ctx_data = bytearray(b"\x55" * 0xD000)
        uc.mem_write(CTX_BASE, bytes(ctx_data))

        # Set 0x00447A78 -> CTX_BASE
        uc.mem_write(0x00447A78, struct.pack("<I", CTX_BASE))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, r0_val & 0xFFFFFFFF)
        uc.reg_write(UC_ARM_REG_R1, r1_val & 0xFFFFFFFF)

        uc.emu_start(addr, lr, timeout=3000000)
        # Read the 0x20 bytes around 0xCCC0
        return uc.mem_read(CTX_BASE + 0xCCC0, 0x20)

    cases = [
        (0, 0),
        (123, 0),
        (0, 5),
        (42, 12),
        (-7, -3),
        (300, 20),
    ]

    for r0_val, r1_val in cases:
        o = run_one(orig, r0_val, r1_val)
        c = run_one(staged, r0_val, r1_val)
        assert o == c, f"00256524 mismatch for {r0_val}, {r1_val}"
    print("func_00256524: PASS")

def test_00252630():
    print("--- Testing script_vm_func_00252630 ---")
    addr = 0x00252630
    size = 140
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_00252630", ROOT / "build")
    symbol_map = {
        "func_002aeb2c": 0x002AEB2C,
        "func_002a6410": 0x002A6410,
        "func_002c45b8": 0x002C45B8,
        "engine_func_002c4360": 0x002C4360,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    R5_OBJ = 0x20000000
    SUB_OBJ = 0x20001000
    SOUND_MGR = 0x20002000

    def run_one(c_bytes, voice_id, null_global=False):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Set up stubs (bx lr: 0xe12fff1e)
        for stub_addr in [0x002AEB2C, 0x002A6410, 0x002C45B8, 0x002C4360]:
            uc.mem_write(stub_addr, b"\x1e\xff\x2f\xe1")

        if null_global:
            uc.mem_write(0x00434210, struct.pack("<I", 0))
        else:
            uc.mem_write(0x00434210, struct.pack("<I", R5_OBJ))
            r5_data = bytearray(0x350)
            struct.pack_into("<i", r5_data, 0x2F8, voice_id)
            struct.pack_into("<B", r5_data, 0x2F4, 0x7F)
            struct.pack_into("<I", r5_data, 0x2E4, SUB_OBJ)
            struct.pack_into("<II", r5_data, 0x2E8, 0xAAAAAAAA, 0xBBBBBBBB)
            uc.mem_write(R5_OBJ, bytes(r5_data))

        uc.mem_write(0x00433158, struct.pack("<I", SOUND_MGR))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)
        uc.reg_write(UC_ARM_REG_R7, 0x44444444)
        uc.reg_write(UC_ARM_REG_R8, 0x55555555)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "global_slot": struct.unpack("<I", uc.mem_read(0x00434210, 4))[0],
            "r5_mem": uc.mem_read(R5_OBJ + 0x2E0, 0x20) if not null_global else b"",
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
            "r8": uc.reg_read(UC_ARM_REG_R8),
        }

    cases = [
        (5, False),
        (-1, False),
        (0, False),
        (10, True),
    ]

    for vid, ng in cases:
        o = run_one(orig, vid, ng)
        c = run_one(staged, vid, ng)
        assert o == c, f"00252630 mismatch for voice_id={vid}, ng={ng}: {o} vs {c}"
    print("script_vm_func_00252630: PASS")

def test_0024de78():
    print("--- Testing engine_func_0024de78 ---")
    addr = 0x0024DE78
    size = 136
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_0024de78", ROOT / "build")
    symbol_map = {
        "engine_func_002c4360": 0x002C4360,
        "engine_func_002c4b30": 0x002C4B30,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    ARRAY_BASE = 0x00478000
    COUNT_PTR = 0x00433278

    def run_one(c_bytes, count):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Stubs
        # engine_func_002c4360: bx lr (free)
        uc.mem_write(0x002C4360, b"\x1e\xff\x2f\xe1")
        # engine_func_002c4b30: authentic implementation in code.bin is used

        # Pre-fill array
        arr_data = bytearray(b"\xAA" * 0x5200)
        for i in range(max(0, min(count, 64))):
            entry_off = i * 328
            struct.pack_into("<I", arr_data, entry_off + 0x13C, 0x20001000 + i * 4)
            struct.pack_into("<I", arr_data, entry_off + 0x28, 0x11111111)
            struct.pack_into("<I", arr_data, entry_off + 0x24, 0x20002000 + i * 4)
            struct.pack_into("<I", arr_data, entry_off + 0x20, 0x22222222)
        uc.mem_write(ARRAY_BASE, bytes(arr_data))

        # Write count
        uc.mem_write(COUNT_PTR, struct.pack("<i", count))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)
        uc.reg_write(UC_ARM_REG_R7, 0x44444444)
        uc.reg_write(UC_ARM_REG_R8, 0x55555555)

        uc.emu_start(addr, lr, timeout=5000000)
        return {
            "count": struct.unpack("<i", uc.mem_read(COUNT_PTR, 4))[0],
            "arr_sample": uc.mem_read(ARRAY_BASE, 0x40),
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
            "r8": uc.reg_read(UC_ARM_REG_R8),
        }

    cases = [0, -1, 1, 3, 10]
    for cnt in cases:
        o = run_one(orig, cnt)
        c = run_one(staged, cnt)
        assert o == c, f"0024de78 mismatch for count={cnt}: {o} vs {c}"
    print("engine_func_0024de78: PASS")

def test_0022df7c():
    print("--- Testing unite_func_0022df7c ---")
    addr = 0x0022DF7C
    size = 140
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("unite_func_0022df7c", ROOT / "build")
    symbol_map = {
        "camp_func_002b9364": 0x002B9364,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    CONTAINER = 0x20000000
    DEMON_REC = 0x20001000

    def run_one(c_bytes, demon_id, race, initial_slots, null_rec=False):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Setup camp_func_002b9364 stub:
        # returns DEMON_REC if !null_rec else 0
        if null_rec:
            # mov r0, #0; bx lr
            stub = b"\x00\x00\xa0\xe3\x1e\xff\x2f\xe1"
        else:
            # ldr r0, [pc, #0]; bx lr; .word DEMON_REC
            stub = struct.pack("<III", 0xe59f0000, 0xe12fff1e, DEMON_REC)
            rec_data = bytearray(0x100)
            struct.pack_into("<H", rec_data, 0x90, race)
            uc.mem_write(DEMON_REC, bytes(rec_data))
        uc.mem_write(0x002B9364, stub)

        # Container
        cont_data = bytearray(0x40)
        for i in range(16):
            struct.pack_into("<h", cont_data, i * 2, initial_slots[i])
            cont_data[0x20 + i] = 0
        uc.mem_write(CONTAINER, bytes(cont_data))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, CONTAINER)
        uc.reg_write(UC_ARM_REG_R1, demon_id)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "container": uc.mem_read(CONTAINER, 0x30),
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
        }

    # 1. Null demon record
    slots1 = [-1] * 16
    o = run_one(orig, 100, 0x50, slots1, null_rec=True)
    c = run_one(staged, 100, 0x50, slots1, null_rec=True)
    assert o == c, "0022df7c null_rec mismatch"

    # 2. Race >= 0x160 (352)
    o = run_one(orig, 100, 0x160, slots1, null_rec=False)
    c = run_one(staged, 100, 0x160, slots1, null_rec=False)
    assert o == c, "0022df7c race high mismatch"

    # 3. Already in slot 0
    slots_match = [100] + [-1] * 15
    o = run_one(orig, 100, 0x50, slots_match, null_rec=False)
    c = run_one(staged, 100, 0x50, slots_match, null_rec=False)
    assert o == c, "0022df7c match slot 0 mismatch"

    # 4. Already in slot 7
    slots_match7 = [10, 20, 30, 40, 50, 60, 70, 100] + [-1] * 8
    o = run_one(orig, 100, 0x50, slots_match7, null_rec=False)
    c = run_one(staged, 100, 0x50, slots_match7, null_rec=False)
    assert o == c, "0022df7c match slot 7 mismatch"

    # 5. Empty slot 0
    slots_empty0 = [-1] * 16
    o = run_one(orig, 77, 0x20, slots_empty0, null_rec=False)
    c = run_one(staged, 77, 0x20, slots_empty0, null_rec=False)
    assert o == c, "0022df7c empty slot 0 mismatch"

    # 6. Empty slot 5
    slots_empty5 = [1, 2, 3, 4, 5, -1, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    o = run_one(orig, 77, 0x20, slots_empty5, null_rec=False)
    c = run_one(staged, 77, 0x20, slots_empty5, null_rec=False)
    assert o == c, "0022df7c empty slot 5 mismatch"

    # 7. All slots full, no match
    slots_full = list(range(1, 17))
    o = run_one(orig, 77, 0x20, slots_full, null_rec=False)
    c = run_one(staged, 77, 0x20, slots_full, null_rec=False)
    assert o == c, "0022df7c full slots mismatch"

    print("unite_func_0022df7c: PASS")

if __name__ == "__main__":
    test_00269e54()
    test_00256524()
    test_00252630()
    test_0024de78()
    test_0022df7c()
    print("\nALL 5 FUNCTIONS IN BATCH 8 PASSED DIFFERENTIAL VERIFICATION!")
