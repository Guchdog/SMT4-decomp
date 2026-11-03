#!/usr/bin/env python3
"""Differential test for batch 30 part 7:
- func_00262664 (0x00262664, 140 B)
- script_vm_func_002706e4 (0x002706E4, 140 B)
- ui_func_002918c4 (0x002918C4, 140 B)
- camp_func_0029933c (0x0029933C, 152 B)
- func_002d782c (0x002D782C, 144 B)
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
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
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
    uc.mem_map(0x20000000, 0x40000)
    uc.mem_map(0x00490000, 0x20000)
    uc.mem_map(0x004E0000, 0x20000)
    return uc

def test_00262664():
    print("--- Testing func_00262664 ---")
    addr = 0x00262664
    size = 140
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_00262664", ROOT / "build")
    staged = stage_body(comp, relocs, addr, {})

    ENTITY = 0x20000000
    R2_OBJ = 0x20001000
    TABLE = 0x20010000

    def run_one(c_bytes, default_val, obj_status, match_index, result_val):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Entity
        entity_data = bytearray(0x40)
        struct.pack_into("<h", entity_data, 0x1C, default_val)
        uc.mem_write(ENTITY, bytes(entity_data))

        # Set 0x00435D90 -> R2_OBJ
        uc.mem_write(0x00435D90, struct.pack("<I", R2_OBJ))

        r2_data = bytearray(0x2000)
        struct.pack_into("<I", r2_data, 0x64, obj_status)
        struct.pack_into("<I", r2_data, 0x1FC0, TABLE)
        uc.mem_write(R2_OBJ, bytes(r2_data))

        # Table: 109 entries, stride 648 (0x288)
        table_data = bytearray(109 * 648)
        if match_index is not None and match_index < 109:
            entry_off = match_index * 648
            # flags: bit 0 and bit 1 set, bit 6 (0x40) clear -> 0x03
            struct.pack_into("<I", table_data, entry_off, 0x03)
            struct.pack_into("<I", table_data, entry_off + 0x278, ENTITY)
            struct.pack_into("<h", table_data, entry_off + 0x1B6, result_val)
        uc.mem_write(TABLE, bytes(table_data))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, ENTITY)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)

        def hook_fault(uc, access, address, size, value, ud):
            print(f"FAULT access={access}, addr=0x{address:08X}")
            return False
        from unicorn import UC_HOOK_MEM_UNMAPPED
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_fault)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": struct.unpack("<h", struct.pack("<H", uc.reg_read(UC_ARM_REG_R0) & 0xFFFF))[0],
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
        }

    cases = [
        (100, 0, 5, 555), # matched at index 5 -> 555
        (100, 0, 0, 999), # matched at index 0 -> 999
        (100, 0, None, 0), # no match -> returns default 100
        (100, 0x15, 5, 555), # status 0x15 early exit -> returns default 100
    ]

    for dval, status, midx, rval in cases:
        o = run_one(orig, dval, status, midx, rval)
        c = run_one(staged, dval, status, midx, rval)
        assert o == c, f"00262664 mismatch: {o} vs {c}"
    print("func_00262664: PASS")

def test_002706e4():
    print("--- Testing script_vm_func_002706e4 ---")
    addr = 0x002706E4
    size = 140
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_002706e4", ROOT / "build")
    symbol_map = {
        "script_vm_func_002711e0": 0x002711E0,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    TARGET = 0x0049F91C
    R0_SLOT = 0x20000000
    R4_OBJ = 0x20000100

    def run_one(c_bytes):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # 0x00447E28 -> R4_OBJ
        uc.mem_write(0x00447E28, struct.pack("<I", R4_OBJ))

        # Fill R4_OBJ
        r4_data = bytearray(0x80)
        struct.pack_into("<II", r4_data, 0x2C, 0x11223344, 0x55667788)
        uc.mem_write(R4_OBJ, bytes(r4_data))

        # Target pre-filled
        target_data = bytearray(b"\x55" * 0x350)
        struct.pack_into("<I", target_data, 0x08, 0xCAFEBABE)
        struct.pack_into("<I", target_data, 0x90, 0xFEEDFACE)
        struct.pack_into("<3f", target_data, 0x94, 1.25, 2.5, 3.75)
        struct.pack_into("<f", target_data, 0xA0, 4.5)
        uc.mem_write(TARGET, bytes(target_data))

        # Stub 0x002711E0: bx lr
        uc.mem_write(0x002711E0, b"\x1e\xff\x2f\xe1")

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)

        def hook_fault(uc, access, address, size, value, ud):
            print(f"FAULT access={access}, addr=0x{address:08X}")
            return False
        from unicorn import UC_HOOK_MEM_UNMAPPED
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_fault)

        uc.emu_start(addr, lr, timeout=3000000)
        return uc.mem_read(TARGET + 0x2F0, 0x50)

    o = run_one(orig)
    c = run_one(staged)
    assert o == c, "002706e4 target memory mismatch"
    print("script_vm_func_002706e4: PASS")

def test_002918c4():
    print("--- Testing ui_func_002918c4 ---")
    addr = 0x002918C4
    size = 140
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_002918c4", ROOT / "build")
    symbol_map = {
        "ui_func_00297004": 0x00297004,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    def run_one(c_bytes, mode, p1, p2, stub_ret_0, stub_ret_1):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Stub 0x00297004: if r1 == 1 return stub_ret_1 else return stub_ret_0
        # cmp r1, #1; ldreq r0, [pc, #4]; ldrne r0, [pc, #4]; bx lr
        stub = (
            b"\x01\x00\x51\xe3" # cmp r1, #1
            b"\x04\x00\x9f\x05" # ldreq r0, [pc, #4]
            b"\x04\x00\x9f\x15" # ldrne r0, [pc, #4]
            b"\x1e\xff\x2f\xe1" # bx lr
            + struct.pack("<ii", stub_ret_1, stub_ret_0)
        )
        uc.mem_write(0x00297004, stub)

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, mode)
        uc.reg_write(UC_ARM_REG_R1, p1)
        uc.reg_write(UC_ARM_REG_R2, p2)

        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)

        def hook_fault(uc, access, address, size, value, ud):
            print(f"FAULT access={access}, addr=0x{address:08X}")
            return False
        from unicorn import UC_HOOK_MEM_UNMAPPED
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_fault)

        uc.emu_start(addr, lr, timeout=3000000)
        s0_int = uc.reg_read(UC_ARM_REG_S0)
        s0_float = struct.unpack("<f", struct.pack("<I", s0_int))[0]
        return {
            "ret_float": s0_float,
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
        }

    cases = [
        # mode, p1, p2, stub_ret_0, stub_ret_1
        (0, 10, 50, 25, 0),
        (1, 10, 50, 25, 0),
        (2, 10, 50, 25, 1), # mode 2, check == 1 -> positive res
        (2, 10, 50, 25, 0), # mode 2, check == 0 -> negated res
        (3, 10, 50, 25, 0), # mode 3 -> 0.0f
    ]

    for m, p1, p2, sr0, sr1 in cases:
        o = run_one(orig, m, p1, p2, sr0, sr1)
        c = run_one(staged, m, p1, p2, sr0, sr1)
        assert abs(o["ret_float"] - c["ret_float"]) < 1e-4, f"002918c4 mismatch: {o} vs {c}"
        assert o["r4"] == c["r4"]
        assert o["r5"] == c["r5"]
        assert o["r6"] == c["r6"]
    print("ui_func_002918c4: PASS")

def test_0029933c():
    print("--- Testing camp_func_0029933c ---")
    addr = 0x0029933C
    size = 152
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("camp_func_0029933c", ROOT / "build")
    symbol_map = {
        "ui_func_002c0b94": 0x002C0B94,
        "camp_func_002bdb2c": 0x002BDB2C,
        "script_vm_func_002b90e0": 0x002B90E0,
        "camp_func_002bf030": 0x002BF030,
        "engine_func_002c4b30": 0x002C4B30,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    BASE_CTX = 0x20000000
    P_CTX = 0x20001000

    def run_one(c_bytes, val_val):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # 0x0043E188 + 8 -> BASE_CTX
        uc.mem_write(0x0043E188 + 8, struct.pack("<I", BASE_CTX))

        # Base structure
        base_data = bytearray(0x1000)
        uc.mem_write(BASE_CTX, bytes(base_data))

        # P_CTX + 0x1F454 = val_val
        uc.mem_map(0x20040000, 0x40000)
        P_BUFF = 0x20040000
        p_data = bytearray(0x20000)
        struct.pack_into("<I", p_data, 0x1F454, val_val)
        uc.mem_write(P_BUFF, bytes(p_data))

        # Stub 0x002C0B94: return P_BUFF
        uc.mem_write(0x002C0B94, (
            b"\x00\x00\x9f\xe5\x1e\xff\x2f\xe1" + struct.pack("<I", P_BUFF)
        ))

        # Stubs for downstream functions: bx lr
        uc.mem_write(0x002BDB2C, b"\x1e\xff\x2f\xe1")
        uc.mem_write(0x002B90E0, b"\x1e\xff\x2f\xe1")
        uc.mem_write(0x002BF030, b"\x1e\xff\x2f\xe1")

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)

        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)

        def hook_fault(uc, access, address, size, value, ud):
            print(f"FAULT access={access}, addr=0x{address:08X}")
            return False
        from unicorn import UC_HOOK_MEM_UNMAPPED
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_fault)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "base_9c": struct.unpack("<I", uc.mem_read(BASE_CTX + 0x9C, 4))[0],
            "base_a0": uc.mem_read(BASE_CTX + 0xA0, 2),
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
        }

    for val in [0, 0x12345678, 0xDEADBEEF]:
        o = run_one(orig, val)
        c = run_one(staged, val)
        assert o == c, f"0029933c mismatch ({val}): {o} vs {c}"
    print("camp_func_0029933c: PASS")

def test_002d782c():
    print("--- Testing func_002d782c ---")
    addr = 0x002D782C
    size = 144
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_002d782c", ROOT / "build")
    symbol_map = {
        "func_002d782c": addr,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    TABLE_PTR = 0x20000000
    NODE1 = 0x20001000
    NODE2 = 0x20001100
    NODE3 = 0x20001200
    CHILD1 = 0x20002000

    def run_one(c_bytes, set_or_clear, target_id, flags):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # 0x004E3CF4 -> TABLE_PTR
        uc.mem_write(0x004E3CF4, struct.pack("<I", TABLE_PTR))

        # Clear TABLE_PTR (256 buckets of 8 bytes = 2048 bytes)
        uc.mem_write(TABLE_PTR, b"\x00" * 2048)

        bucket = target_id >> 20
        tag = target_id & 0x000FFFFF

        # Place NODE1 at table[bucket]
        uc.mem_write(TABLE_PTR + bucket * 8, struct.pack("<I", NODE1))

        # Node 1: wrong tag (tag + 1), next = NODE2
        node1_data = bytearray(0x80)
        struct.pack_into("<I", node1_data, 0x24, tag + 1)
        struct.pack_into("<I", node1_data, 0x4C, NODE2)
        uc.mem_write(NODE1, bytes(node1_data))

        # Node 2: matching tag, flags = 0x11111111, next = NODE3, child = CHILD1
        node2_data = bytearray(0x80)
        struct.pack_into("<I", node2_data, 0x1C, 0x11111111)
        struct.pack_into("<I", node2_data, 0x24, tag)
        struct.pack_into("<I", node2_data, 0x4C, NODE3)
        struct.pack_into("<I", node2_data, 0x58, CHILD1)
        uc.mem_write(NODE2, bytes(node2_data))

        # Node 3: tag + 2, flags = 0x22222222, next = 0
        node3_data = bytearray(0x80)
        struct.pack_into("<I", node3_data, 0x1C, 0x22222222)
        struct.pack_into("<I", node3_data, 0x24, tag + 2)
        uc.mem_write(NODE3, bytes(node3_data))

        # Child 1: id of Node 3 = (bucket << 20) | (tag + 2), next = 0
        child1_data = bytearray(0x80)
        struct.pack_into("<I", child1_data, 0x28, (bucket << 20) | (tag + 2))
        uc.mem_write(CHILD1, bytes(child1_data))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, set_or_clear)
        uc.reg_write(UC_ARM_REG_R1, target_id)
        uc.reg_write(UC_ARM_REG_R2, flags)

        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "node2_flags": struct.unpack("<I", uc.mem_read(NODE2 + 0x1C, 4))[0],
            "node3_flags": struct.unpack("<I", uc.mem_read(NODE3 + 0x1C, 4))[0],
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
        }

    cases = [
        (1, 0x05123456, 0x00FF00FF), # set flags
        (0, 0x05123456, 0x00110000), # clear flags
        (1, 0x05123456, 0xF000000F), # mask bits 0xF000000F should be excluded
    ]

    for sc, tid, fl in cases:
        o = run_one(orig, sc, tid, fl)
        c = run_one(staged, sc, tid, fl)
        assert o == c, f"002d782c mismatch: {o} vs {c}"
    print("func_002d782c: PASS")

def main():
    test_00262664()
    test_002706e4()
    test_002918c4()
    test_0029933c()
    test_002d782c()
    print("\nALL 5 FUNCTIONS IN BATCH 7 PASSED DIFFERENTIAL VERIFICATION!")

if __name__ == "__main__":
    main()
