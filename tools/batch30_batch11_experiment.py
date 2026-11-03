#!/usr/bin/env python3
"""Differential test for batch 30 part 11:
- engine_func_00227f50 (0x00227F50, 144 B)
- ui_func_002282a0 (0x002282A0, 152 B)
- script_vm_func_00229b2c (0x00229B2C, 148 B)
- battle_func_00229bd0 (0x00229BD0, 152 B)
- engine_func_002306ec (0x002306EC, 144 B)
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
    uc.mem_map(0x20000000, 0x80000)

    def hook_fault(uc, access, address, size, value, ud):
        print(f"FAULT access={access}, addr=0x{address:08X}")
        return False
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_fault)
    return uc

def test_00227f50():
    print("--- Testing engine_func_00227f50 ---")
    addr = 0x00227F50
    size = 144
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_00227f50", ROOT / "build")
    symbol_map = {
        "func_00293c98": 0x00293C98,
        "func_002934d4": 0x002934D4,
        "engine_func_002c3290": 0x002C3290,
        "engine_func_002b45f8": 0x002B45F8,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    ENTITY = 0x20000000
    BASE = 0x20001000

    def run_one(c_bytes, null_base, f2934d4_ret, match_i, ret_stat):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Entity memory
        entity_data = bytearray(0x1D00)
        struct.pack_into("<I", entity_data, 0x1CFC, 0 if null_base else BASE)
        uc.mem_write(ENTITY, bytes(entity_data))

        # Base memory: 4 entries of 22 bytes starting at 0x58
        if not null_base:
            base_data = bytearray(0x200)
            if match_i is not None and 0 <= match_i < 4:
                struct.pack_into("<h", base_data, 0x58 + match_i * 22 + 0x10, ret_stat)
            uc.mem_write(BASE, bytes(base_data))

        # Context at 0x00435D00 + 0x0C
        uc.mem_write(0x00435D0C, struct.pack("<I", 0x778899AA))

        # Stubs:
        bx_lr = b"\x1e\xff\x2f\xe1"
        uc.mem_write(0x00293C98, bx_lr)
        uc.mem_write(0x002934D4, bytes([f2934d4_ret, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1]))
        uc.mem_write(0x002C3290, bytes([0x55, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1]))

        # engine_func_002b45f8(entry, context, aux): return 0 if entry corresponds to match_i else 1
        def hook_b45f8(uc, address, size, user_data):
            entry = uc.reg_read(UC_ARM_REG_R0)
            cur_i = (entry - (BASE + 0x58)) // 22
            res = 0 if cur_i == match_i else 1
            uc.reg_write(UC_ARM_REG_R0, res)
        uc.hook_add(UC_HOOK_CODE, hook_b45f8, begin=0x002B45F8, end=0x002B45F8)
        uc.mem_write(0x002B45F8, bx_lr)

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, ENTITY)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)
        uc.reg_write(UC_ARM_REG_R7, 0x44444444)
        uc.reg_write(UC_ARM_REG_R8, 0x55555555)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": struct.unpack("<i", struct.pack("<I", uc.reg_read(UC_ARM_REG_R0)))[0],
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
            "r8": uc.reg_read(UC_ARM_REG_R8),
        }

    cases = [
        (True, 0, None, 0),    # null base -> -1
        (False, 1, 0, 100),    # 2934d4 != 0 -> -1
        (False, 0, 0, 123),    # match at 0 -> 123
        (False, 0, 2, 456),    # match at 2 -> 456
        (False, 0, 3, -10),    # match at 3 -> -10
        (False, 0, None, 0),   # no match -> -1
    ]

    for c_tuple in cases:
        o = run_one(orig, *c_tuple)
        c = run_one(staged, *c_tuple)
        assert o == c, f"00227f50 mismatch for {c_tuple}: {o} vs {c}"
    print("engine_func_00227f50: PASS")

def test_002282a0():
    print("--- Testing ui_func_002282a0 ---")
    addr = 0x002282A0
    size = 152
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_002282a0", ROOT / "build")
    symbol_map = {
        "func_00293c98": 0x00293C98,
        "func_002934d4": 0x002934D4,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    ENTITY = 0x20000000
    COMP = 0x20001000
    SUB_OBJ = 0x20002000

    def run_one(c_bytes, null_comp, val_190, f2934d4_1, sub_flag_bit1, flag_arg, f2934d4_2):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Entity
        entity_data = bytearray(0x1D00)
        struct.pack_into("<I", entity_data, 0x1CFC, 0 if null_comp else COMP)
        uc.mem_write(ENTITY, bytes(entity_data))

        # Comp
        if not null_comp:
            comp_data = bytearray(0x200)
            struct.pack_into("<h", comp_data, 0x190, val_190)
            uc.mem_write(COMP, bytes(comp_data))

        # Sub obj at 0x20002000: field at 0x44AC
        sub_data = bytearray(0x5000)
        struct.pack_into("<I", sub_data, 0x44AC, 2 if sub_flag_bit1 else 0)
        uc.mem_write(SUB_OBJ, bytes(sub_data))

        # Hook 293c98: returns SUB_OBJ
        uc.mem_write(0x00293C98, struct.pack("<III", 0xe59f0000, 0xe12fff1e, SUB_OBJ))

        # Hook 2934d4: returns f2934d4_1 on first call, f2934d4_2 on second call
        calls = [0]
        def hook_34d4(uc, address, size, user_data):
            c = calls[0]
            calls[0] += 1
            res = f2934d4_1 if c == 0 else f2934d4_2
            uc.reg_write(UC_ARM_REG_R0, res)
        uc.hook_add(UC_HOOK_CODE, hook_34d4, begin=0x002934D4, end=0x002934D4)
        uc.mem_write(0x002934D4, b"\x1e\xff\x2f\xe1")

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, ENTITY)
        uc.reg_write(UC_ARM_REG_R1, flag_arg)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": struct.unpack("<i", struct.pack("<I", uc.reg_read(UC_ARM_REG_R0)))[0],
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
        }

    cases = [
        (True, 10, 0, False, 0, 0),        # null comp -> -1
        (False, -5, 0, False, 0, 0),       # val < 0 -> -1
        (False, 10, 1, True, 0, 0),        # 2934d4 != 0 and bit 1 set -> 0
        (False, 25, 0, False, 0, 0),       # flag == 0 -> returns val 25
        (False, 30, 0, False, 1, 0),       # flag != 0, 2934d4 == 0 -> returns val 30
        (False, 30, 0, False, 1, 1),       # flag != 0, 2934d4 != 0 -> -1
    ]

    for c_tuple in cases:
        o = run_one(orig, *c_tuple)
        c = run_one(staged, *c_tuple)
        assert o == c, f"002282a0 mismatch for {c_tuple}: {o} vs {c}"
    print("ui_func_002282a0: PASS")

def test_00229b2c():
    print("--- Testing script_vm_func_00229b2c ---")
    addr = 0x00229B2C
    size = 148
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_00229b2c", ROOT / "build")
    symbol_map = {
        "script_vm_func_0027eb98": 0x0027EB98,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    MANAGER_HANDLE = 0x20000000
    MANAGER_OBJ = 0x20001000
    TABLE_BASE = 0x20010000
    TARGET_OBJ = 0x20002000

    def run_one(c_bytes, best_entry_idx, best_id, best_prio):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Manager handle -> MANAGER_OBJ
        uc.mem_write(MANAGER_HANDLE, struct.pack("<I", MANAGER_OBJ))

        # MANAGER_OBJ + 0x1FC0 -> TABLE_BASE
        mgr_data = bytearray(0x2000)
        struct.pack_into("<I", mgr_data, 0x1FC0, TABLE_BASE)
        uc.mem_write(MANAGER_OBJ, bytes(mgr_data))

        # Table base: 109 entries of 648 bytes
        tbl_data = bytearray(109 * 648)
        # Entry 0 has flags=0
        # Best entry: flags = 0x400 (bit 10 set)
        entry_off = best_entry_idx * 648
        struct.pack_into("<I", tbl_data, entry_off, 0x400)
        struct.pack_into("<h", tbl_data, entry_off + 0x1B4, best_prio)
        struct.pack_into("<h", tbl_data, entry_off + 0x6E, best_id)
        uc.mem_write(TABLE_BASE, bytes(tbl_data))

        # Clear target obj
        uc.mem_write(TARGET_OBJ, b"\x00" * 0x100)

        # Stub script_vm_func_0027eb98: return TARGET_OBJ
        uc.mem_write(0x0027EB98, struct.pack("<III", 0xe59f0000, 0xe12fff1e, TARGET_OBJ))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, MANAGER_HANDLE)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)
        uc.reg_write(UC_ARM_REG_R7, 0x44444444)
        uc.reg_write(UC_ARM_REG_R8, 0x55555555)

        uc.emu_start(addr, lr, timeout=5000000)
        return {
            "target": uc.mem_read(TARGET_OBJ, 0x60),
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
            "r8": uc.reg_read(UC_ARM_REG_R8),
        }

    cases = [
        (5, 4, 100),
        (0, 10, 50),
        (108, 1, 20),
    ]

    for idx, bid, prio in cases:
        o = run_one(orig, idx, bid, prio)
        c = run_one(staged, idx, bid, prio)
        assert o == c, f"00229b2c mismatch for {idx}, {bid}, {prio}: {o} vs {c}"
    print("script_vm_func_00229b2c: PASS")

def test_00229bd0():
    print("--- Testing battle_func_00229bd0 ---")
    addr = 0x00229BD0
    size = 152
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("battle_func_00229bd0", ROOT / "build")
    symbol_map = {
        "func_00226b2c": 0x00226B2C,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    MGR = 0x20000000
    ALLOC_NODE = 0x20001000
    LIST_HEAD = 0x20002000

    def run_one(c_bytes, arg0, arg1, arg2, arg3, arg4, match_in_list):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # 0x00434290 -> MGR
        uc.mem_write(0x00434290, struct.pack("<I", MGR))

        # MGR memory: MGR + 8 = LIST_HEAD
        mgr_data = bytearray(0x20)
        struct.pack_into("<I", mgr_data, 8, LIST_HEAD if arg4 != 0 else 0)
        uc.mem_write(MGR, bytes(mgr_data))

        # ALLOC_NODE
        alloc_data = bytearray(0x60)
        struct.pack_into("<h", alloc_data, 2, 5) # initial positive val at +2
        uc.mem_write(ALLOC_NODE, bytes(alloc_data))

        # LIST_HEAD
        list_data = bytearray(0x60)
        if match_in_list:
            list_data[4] = 0x0E
            struct.pack_into("<I", list_data, 0x28, 0)
            struct.pack_into("<I", list_data, 0x4C, arg3)
        else:
            list_data[4] = 0x01
        struct.pack_into("<I", list_data, 0x0C, 0) # next is null
        uc.mem_write(LIST_HEAD, bytes(list_data))

        # Stub func_00226b2c: return ALLOC_NODE
        uc.mem_write(0x00226B2C, struct.pack("<III", 0xe59f0000, 0xe12fff1e, ALLOC_NODE))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_R2, arg2)
        uc.reg_write(UC_ARM_REG_R3, arg3)
        # 5th arg on stack at sp:
        # Note: function preamble pushes 6 registers {r4..r8, lr} (24 bytes = 0x18).
        # So [sp, #0x18] was the caller's [sp, #0]!
        uc.mem_write(sp, struct.pack("<I", arg4))

        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)
        uc.reg_write(UC_ARM_REG_R7, 0x44444444)
        uc.reg_write(UC_ARM_REG_R8, 0x55555555)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "node": uc.mem_read(ALLOC_NODE, 0x54),
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
            "r8": uc.reg_read(UC_ARM_REG_R8),
        }

    cases = [
        (10, 20, 30, 40, 1, True),  # arg4=1 and matched in list -> sets field_2 = -1
        (10, 20, 30, 40, 1, False), # arg4=1 but not matched -> field_2 unchanged
        (10, 20, 30, 40, 0, True),  # arg4=0 -> does not check list
    ]

    for c_tuple in cases:
        o = run_one(orig, *c_tuple)
        c = run_one(staged, *c_tuple)
        assert o == c, f"00229bd0 mismatch for {c_tuple}: {o} vs {c}"
    print("battle_func_00229bd0: PASS")

def test_002306ec():
    print("--- Testing engine_func_002306ec ---")
    addr = 0x002306EC
    size = 144
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_002306ec", ROOT / "build")
    symbol_map = {
        "camp_func_002bdb2c": 0x002BDB2C,
        "func_002bdac0": 0x002BDAC0,
        "engine_func_002c4b30": 0x002C4B30,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    CTX_PTR = 0x20000000
    R4_OBJ = 0x20001000

    def run_one(c_bytes, input_val):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # 0x0043E188 + 8 -> R4_OBJ
        uc.mem_write(0x0043E190, struct.pack("<I", R4_OBJ))

        # R4_OBJ memory
        r4_data = bytearray(0x900)
        uc.mem_write(R4_OBJ, bytes(r4_data))

        # Stubs:
        calls = []
        def hook_bdb2c(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            sp = uc.reg_read(UC_ARM_REG_SP)
            arg4 = struct.unpack("<I", uc.mem_read(sp, 4))[0]
            s0_raw = uc.reg_read(UC_ARM_REG_S0)
            s0 = struct.unpack("<f", struct.pack("<I", s0_raw))[0]
            calls.append(("bdb2c", r0, r1, r2, r3, arg4, round(s0, 2)))
        uc.hook_add(UC_HOOK_CODE, hook_bdb2c, begin=0x002BDB2C, end=0x002BDB2C)
        uc.mem_write(0x002BDB2C, b"\x1e\xff\x2f\xe1")

        def hook_bdac0(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            calls.append(("bdac0", r0, r1, r2))
        uc.hook_add(UC_HOOK_CODE, hook_bdac0, begin=0x002BDAC0, end=0x002BDAC0)
        uc.mem_write(0x002BDAC0, b"\x1e\xff\x2f\xe1")

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, input_val)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "field_82": struct.unpack("<B", uc.mem_read(R4_OBJ + 0x82, 1))[0],
            "calls": calls,
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
        }

    cases = [0, 1, 5]
    for inp in cases:
        o = run_one(orig, inp)
        c = run_one(staged, inp)
        assert o == c, f"002306ec mismatch for {inp}: {o} vs {c}"
    print("engine_func_002306ec: PASS")

if __name__ == "__main__":
    test_00227f50()
    test_002282a0()
    test_00229b2c()
    test_00229bd0()
    test_002306ec()
    print("\nALL 5 FUNCTIONS IN BATCH 11 PASSED DIFFERENTIAL VERIFICATION!")
