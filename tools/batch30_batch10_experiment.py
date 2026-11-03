#!/usr/bin/env python3
"""Differential test for batch 30 part 10:
- camp_func_00211f8c (0x00211F8C, 152 B)
- script_vm_func_00215bd8 (0x00215BD8, 148 B)
- ui_func_002220a8 (0x002220A8, 148 B)
- engine_func_00224730 (0x00224730, 144 B)
- ui_func_002277fc (0x002277FC, 148 B)
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
    uc.mem_map(0x20000000, 0x80000)

    def hook_fault(uc, access, address, size, value, ud):
        print(f"FAULT access={access}, addr=0x{address:08X}")
        return False
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_fault)
    return uc

def test_00211f8c():
    print("--- Testing camp_func_00211f8c ---")
    addr = 0x00211F8C
    size = 152
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("camp_func_00211f8c", ROOT / "build")
    symbol_map = {
        "func_0026ace0": 0x0026ACE0,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    MGR_PTR = 0x20000000

    def run_one(c_bytes, total, elements):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # 0x0043E2A8 + 4 -> MGR_PTR
        uc.mem_write(0x0043E2AC, struct.pack("<I", MGR_PTR))

        # Setup MGR memory: array at MGR_PTR + 0x108
        mgr_data = bytearray(0x200)
        for i, val in enumerate(elements):
            struct.pack_into("<H", mgr_data, 0x108 + i * 2, val)
        uc.mem_write(MGR_PTR, bytes(mgr_data))

        # Stub func_0026ace0: return total
        stub = bytes([total & 0xFF, (total >> 8) & 0xFF, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1])
        uc.mem_write(0x0026ACE0, stub)

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
        }

    cases = [
        (0, []),
        (1, [0]),
        (1, [50]),
        (4, [0, 10, 0, 20]),
        (5, [1, 2, 0, 4, 0]),
        (6, [0, 0, 0, 0, 0, 0]),
        (6, [1, 1, 1, 1, 1, 1]),
    ]

    for total, elements in cases:
        o = run_one(orig, total, elements)
        c = run_one(staged, total, elements)
        assert o == c, f"00211f8c mismatch for total={total}, elements={elements}: {o} vs {c}"
    print("camp_func_00211f8c: PASS")

def test_00215bd8():
    print("--- Testing script_vm_func_00215bd8 ---")
    addr = 0x00215BD8
    size = 148
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_00215bd8", ROOT / "build")
    symbol_map = {
        "func_00299224": 0x00299224,
        "func_002509d8": 0x002509D8,
        "func_002900b0": 0x002900B0,
        "func_002bdac0": 0x002BDAC0,
        "func_002b6700": 0x002B6700,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    MGR = 0x20000000
    DEMON_REC = 0x20001000

    def run_one(c_bytes, demon_id, rec_byte7):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # 0x0043DD50 -> MGR
        uc.mem_write(0x0043DD50, struct.pack("<I", MGR))

        # Setup MGR memory
        mgr_data = bytearray(0xA00)
        struct.pack_into("<I", mgr_data, 4, 0x12345678)
        uc.mem_write(MGR, bytes(mgr_data))

        # Setup DEMON_REC
        rec_data = bytearray(0x20)
        rec_data[7] = rec_byte7
        uc.mem_write(DEMON_REC, bytes(rec_data))

        # Stubs:
        # func_00299224: return 0x42
        uc.mem_write(0x00299224, bytes([0x42, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1]))
        # func_002509d8, func_002900b0, func_002bdac0: bx lr
        bx_lr = b"\x1e\xff\x2f\xe1"
        uc.mem_write(0x002509D8, bx_lr)
        uc.mem_write(0x002900B0, bx_lr)
        uc.mem_write(0x002BDAC0, bx_lr)
        # func_002b6700: return DEMON_REC
        uc.mem_write(0x002B6700, struct.pack("<III", 0xe59f0000, 0xe12fff1e, DEMON_REC))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, demon_id)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)
        uc.reg_write(UC_ARM_REG_R7, 0x44444444)
        uc.reg_write(UC_ARM_REG_R8, 0x55555555)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "mgr_header": uc.mem_read(MGR, 0x20),
            "mgr_5c0": uc.mem_read(MGR + 0x5C0, 0x40),
            "mgr_97e": struct.unpack("<H", uc.mem_read(MGR + 0x97E, 2))[0],
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
            "r8": uc.reg_read(UC_ARM_REG_R8),
        }

    cases = [
        (100, 0x40), # flag 0x40 set -> field_5c8 = 2
        (250, 0x00), # flag 0x40 clear -> field_5c8 = 1
        (500, 0xBF), # bit 6 set among other bits -> field_5c8 = 2
    ]

    for did, r7 in cases:
        o = run_one(orig, did, r7)
        c = run_one(staged, did, r7)
        assert o == c, f"00215bd8 mismatch for {did}, {r7}: {o} vs {c}"
    print("script_vm_func_00215bd8: PASS")

def test_002220a8():
    print("--- Testing ui_func_002220a8 ---")
    addr = 0x002220A8
    size = 148
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_002220a8", ROOT / "build")
    symbol_map = {
        "func_00296f60": 0x00296F60,
        "func_002ebe10": 0x002EBE10,
        "func_002bf41c": 0x002BF41C,
        "func_002c4460": 0x002C4460,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    CTX = 0x20000000
    SUB_OBJ = 0x20001000

    def run_one(c_bytes, idx, val, b2bf41c_ret):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # 0x0043DFC0 -> CTX
        uc.mem_write(0x0043DFC0, struct.pack("<I", CTX))

        # Setup CTX memory: *CTX = SUB_OBJ
        ctx_data = bytearray(0x800)
        struct.pack_into("<I", ctx_data, 0, SUB_OBJ)
        uc.mem_write(CTX, bytes(ctx_data))

        # Stubs:
        # func_00296f60(r0): if r0==0 return idx else return val
        # cmp r0, #0; moveq r0, #idx; movne r0, #val; bx lr
        stub_296f60 = bytes([
            0x00, 0x00, 0x50, 0xe3, # cmp r0, #0
            idx, 0x00, 0xa0, 0x03,  # moveq r0, #idx
            val & 0xFF, (val >> 8) & 0xFF, 0xa0, 0x13, # movne r0, #val
            0x1e, 0xff, 0x2f, 0xe1, # bx lr
        ])
        uc.mem_write(0x00296F60, stub_296f60)

        # func_002ebe10: return 0x1234
        recorded_calls = []
        def hook_ebe10(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            s0_raw = uc.reg_read(UC_ARM_REG_S0)
            s1_raw = uc.reg_read(UC_ARM_REG_S1)
            s0 = struct.unpack("<f", struct.pack("<I", s0_raw))[0]
            s1 = struct.unpack("<f", struct.pack("<I", s1_raw))[0]
            recorded_calls.append(("ebe10", r0, r1, round(s0, 2), round(s1, 2)))
        uc.hook_add(UC_HOOK_CODE, hook_ebe10, begin=0x002EBE10, end=0x002EBE10)
        stub_ebe10 = struct.pack("<III", 0xe59f0000, 0xe12fff1e, 0x1234)
        uc.mem_write(0x002EBE10, stub_ebe10)

        # func_002bf41c: return b2bf41c_ret
        uc.mem_write(0x002BF41C, bytes([b2bf41c_ret, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1]))

        # func_002c4460(r0, r1): record call
        def hook_c4460(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            recorded_calls.append(("c4460", r0, r1))
        uc.hook_add(UC_HOOK_CODE, hook_c4460, begin=0x002C4460, end=0x002C4460)
        uc.mem_write(0x002C4460, b"\x1e\xff\x2f\xe1")

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "calls": recorded_calls,
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
        }

    cases = [
        (0, 10, 0),
        (1, 20, 1),
        (2, 5, 1),
    ]

    for idx, val, b_ret in cases:
        o = run_one(orig, idx, val, b_ret)
        c = run_one(staged, idx, val, b_ret)
        assert o == c, f"002220a8 mismatch for {idx}, {val}, {b_ret}: {o} vs {c}"
    print("ui_func_002220a8: PASS")

def test_00224730():
    print("--- Testing engine_func_00224730 ---")
    addr = 0x00224730
    size = 152
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_00224730", ROOT / "build")
    symbol_map = {
        "func_002c0ac8": 0x002C0AC8,
        "func_002a51dc": 0x002A51DC,
        "func_002a3d50": 0x002A3D50,
        "func_002a399c": 0x002A399C,
        "func_0021a36c": 0x0021A36C,
        "func_00281e20": 0x00281E20,
        "func_002f302c": 0x002F302C,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    NODE = 0x20000000
    SUB_RES = 0x20001000

    def run_one(c_bytes, state, has_field8, f2f302c_ret):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Setup Node memory
        node_data = bytearray(0x40)
        struct.pack_into("<I", node_data, 4, state)
        struct.pack_into("<I", node_data, 8, 0x12345678 if has_field8 else 0)
        struct.pack_into("<I", node_data, 0x0C, SUB_RES)
        uc.mem_write(NODE, bytes(node_data))

        # Stubs:
        # func_002c0ac8: return NODE
        uc.mem_write(0x002C0AC8, struct.pack("<III", 0xe59f0000, 0xe12fff1e, NODE))
        # func_002a51dc: return SUB_RES
        uc.mem_write(0x002A51DC, struct.pack("<III", 0xe59f0000, 0xe12fff1e, SUB_RES))
        bx_lr = b"\x1e\xff\x2f\xe1"
        uc.mem_write(0x002A3D50, bx_lr)
        uc.mem_write(0x002A399C, bx_lr)
        # func_0021a36c: return 0x7777
        uc.mem_write(0x0021A36C, struct.pack("<III", 0xe59f0000, 0xe12fff1e, 0x7777))
        uc.mem_write(0x00281E20, bx_lr)
        # func_002f302c: return f2f302c_ret
        uc.mem_write(0x002F302C, bytes([f2f302c_ret, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1]))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, 0xCAFEBABE)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": struct.unpack("<i", struct.pack("<I", uc.reg_read(UC_ARM_REG_R0)))[0],
            "node": uc.mem_read(NODE, 0x20),
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
        }

    cases = [
        (0, True, 0),   # state 0 with field8 -> transitions, returns 0
        (0, False, 0),  # state 0 without field8 -> returns 0
        (1, True, 0),   # state 1 with f2f302c=0 -> returns 0
        (1, True, 1),   # state 1 with f2f302c=1 -> returns -1
        (2, True, 0),   # state 2 -> returns 0
    ]

    for s, h8, f_ret in cases:
        o = run_one(orig, s, h8, f_ret)
        c = run_one(staged, s, h8, f_ret)
        assert o == c, f"00224730 mismatch for {s}, {h8}, {f_ret}: {o} vs {c}"
    print("engine_func_00224730: PASS")

def test_002277fc():
    print("--- Testing ui_func_002277fc ---")
    addr = 0x002277FC
    size = 148
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_002277fc", ROOT / "build")
    symbol_map = {
        "func_00293c98": 0x00293C98,
        "func_002934d4": 0x002934D4,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    ENTITY = 0x20000000
    COMP = 0x20002000

    def run_one(c_bytes, null_comp, f2934d4_ret, stats, fallback):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Entity memory: *(entity + 0x1CFC) = COMP
        entity_data = bytearray(0x1D00)
        struct.pack_into("<I", entity_data, 0x1CFC, 0 if null_comp else COMP)
        uc.mem_write(ENTITY, bytes(entity_data))

        # Comp memory: 0x68, 0x7E, 0x94, 0xAA, and fallback at 0x190
        if not null_comp:
            comp_data = bytearray(0x200)
            struct.pack_into("<h", comp_data, 0x68, stats[0])
            struct.pack_into("<h", comp_data, 0x7E, stats[1])
            struct.pack_into("<h", comp_data, 0x94, stats[2])
            struct.pack_into("<h", comp_data, 0xAA, stats[3])
            struct.pack_into("<h", comp_data, 0x190, fallback)
            uc.mem_write(COMP, bytes(comp_data))

        # Stubs:
        bx_lr = b"\x1e\xff\x2f\xe1"
        uc.mem_write(0x00293C98, bx_lr)
        uc.mem_write(0x002934D4, bytes([f2934d4_ret, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1]))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, ENTITY)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": struct.unpack("<i", struct.pack("<I", uc.reg_read(UC_ARM_REG_R0)))[0],
            "r4": uc.reg_read(UC_ARM_REG_R4),
        }

    cases = [
        (True, 0, [0, 0, 0, 0], 0),       # null comp -> -1
        (False, 1, [10, 20, 30, 40], 50), # 2934d4 != 0 -> -1
        (False, 0, [10, 20, 5, -1], 99),  # max 20 -> 20
        (False, 0, [50, 10, 20, 30], 99), # max 50 -> 50
        (False, 0, [5, 10, 80, 20], 99),  # max 80 -> 80
        (False, 0, [5, 10, 20, 150], 99), # max 150 -> 150
        (False, 0, [-5, -1, 0, -10], 77), # all <= 0 -> fallback 77
        (False, 0, [0, 0, 0, 0], -3),     # all <= 0 -> fallback -3
    ]

    for c_tuple in cases:
        o = run_one(orig, *c_tuple)
        c = run_one(staged, *c_tuple)
        assert o == c, f"002277fc mismatch for {c_tuple}: {o} vs {c}"
    print("ui_func_002277fc: PASS")

if __name__ == "__main__":
    test_00211f8c()
    test_00215bd8()
    test_002220a8()
    test_00224730()
    test_002277fc()
    print("\nALL 5 FUNCTIONS IN BATCH 10 PASSED DIFFERENTIAL VERIFICATION!")
