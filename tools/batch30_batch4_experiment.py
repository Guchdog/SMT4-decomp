#!/usr/bin/env python3
"""Differential test for batch 30 part 4:
- func_002b32e0 (0x002B32E0, 144 B)
- engine_func_002b0614 (0x002B0614, 140 B)
- engine_func_002a140c (0x002A140C, 148 B)
- ui_func_00295300 (0x00295300, 140 B)
- script_vm_func_00295f04 (0x00295F04, 140 B)
- script_vm_func_0028de84 (0x0028DE84, 136 B)
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
        f.seek(addr - 0x00100000)
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

def base_emulator(code_bytes: bytes, target_addr: int) -> Uc:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.ctl_set_cpu_model(UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_write(target_addr, code_bytes)
    return uc

def test_002b32e0():
    print("--- Testing func_002b32e0 ---")
    addr = 0x002B32E0
    size = 144
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_002b32e0", ROOT / "build")
    staged = stage_body(comp, relocs, addr, {})

    def run_one(c_bytes, val):
        uc = base_emulator(c_bytes, addr)
        # Setup table at 0x00465120
        # +0x1C..+0x28: starts (0x1000, 0x2000, 0x3000, 0x4000)
        # +0x2C..+0x38: sizes (0x50, 0x80, 0x100, 0x50)
        uc.mem_write(0x00465120 + 0x1C, struct.pack("<4I", 0x1000, 0x2000, 0x3000, 0x4000))
        uc.mem_write(0x00465120 + 0x2C, struct.pack("<4I", 0x50, 0x80, 0x100, 0x50))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, val)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
        }

    for v in [0x1020, 0x2040, 0x3080, 0x4010, 0x5000, 0x500]:
        o = run_one(orig, v)
        c = run_one(staged, v)
        assert o == c, f"002b32e0 (val={hex(v)}) failed: {o} vs {c}"
    print("func_002b32e0: PASS")

def test_002b0614():
    print("--- Testing engine_func_002b0614 ---")
    addr = 0x002B0614
    size = 140
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_002b0614", ROOT / "build")
    syms = {
        "engine_func_002c3290": 0x002C3290,
    }
    staged = stage_body(comp, relocs, addr, syms)

    def run_one(c_bytes, test_str):
        uc = base_emulator(c_bytes, addr)
        DATA_BASE = 0x20000000
        uc.mem_map(DATA_BASE, 0x1000)
        uc.mem_write(DATA_BASE, test_str.encode("ascii") + b"\x00")

        # Stub 0x2c3290: returns len(test_str)
        l = len(test_str)
        uc.mem_write(0x002C3290, struct.pack("<I", 0xe3a00000 | (l & 0xff)) + b"\x1e\xff\x2f\xe1")

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, DATA_BASE)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "r4": uc.reg_read(UC_ARM_REG_R4),
        }

    for s in ["abc:def", "ab:cd", ":abcdef", "abcdefgh", "", "1234567:"]:
        o = run_one(orig, s)
        c = run_one(staged, s)
        assert o == c, f"002b0614 (str='{s}') failed: {o} vs {c}"
    print("engine_func_002b0614: PASS")

def test_002a140c():
    print("--- Testing engine_func_002a140c ---")
    addr = 0x002A140C
    size = 148
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_002a140c", ROOT / "build")
    syms = {
        "engine_func_002a1578": 0x002A1578,
    }
    staged = stage_body(comp, relocs, addr, syms)

    def run_one(c_bytes, ret_val):
        uc = base_emulator(c_bytes, addr)
        # Stub 0x2a1578: return ret_val
        uc.mem_write(0x002A1578, (
            b"\x04\x00\x9f\xe5" # ldr r0, [pc, #4]
            b"\x1e\xff\x2f\xe1" # bx lr
            + struct.pack("<I", ret_val)
        ))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)

        uc.emu_start(addr, lr, timeout=3000000)
        return uc.reg_read(UC_ARM_REG_R0)

    test_vals = [
        0xC9413910, 0xC8A13909, 0xC941391A,
        0x13865, 0x13850, 0x13890, 0x10000
    ]
    for val in test_vals:
        o = run_one(orig, val)
        c = run_one(staged, val)
        assert o == c, f"002a140c (val={hex(val)}) failed: {o} vs {c}"
    print("engine_func_002a140c: PASS")

def test_00295300():
    print("--- Testing ui_func_00295300 ---")
    addr = 0x00295300
    size = 140
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_00295300", ROOT / "build")
    staged = stage_body(comp, relocs, addr, {})

    def run_one(c_bytes, has_chunk, valid_magic, already_parsed):
        uc = base_emulator(c_bytes, addr)
        DATA_BASE = 0x20000000
        uc.mem_map(DATA_BASE, 0x10000)

        OBJ = DATA_BASE + 0x100
        CHUNK = DATA_BASE + 0x200

        uc.mem_write(OBJ + 0x3C, struct.pack("<B", 1 if already_parsed else 0))

        if has_chunk:
            uc.mem_write(OBJ + 0x28, struct.pack("<I", CHUNK))
            magic = 0x57444B4E if valid_magic else 0x12345678
            uc.mem_write(CHUNK, struct.pack("<I", magic))
            uc.mem_write(CHUNK + 4, struct.pack("<H", 10))  # count4
            uc.mem_write(CHUNK + 6, struct.pack("<H", 5))   # count6
            uc.mem_write(CHUNK + 8, struct.pack("<I", 8))   # count8
            uc.mem_write(CHUNK + 0xC, struct.pack("<H", 4)) # countC
        else:
            uc.mem_write(OBJ + 0x28, struct.pack("<I", 0))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, OBJ)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "p10": struct.unpack("<I", uc.mem_read(OBJ + 0x10, 4))[0],
            "p14": struct.unpack("<I", uc.mem_read(OBJ + 0x14, 4))[0],
            "p18": struct.unpack("<I", uc.mem_read(OBJ + 0x18, 4))[0],
            "p1c": struct.unpack("<I", uc.mem_read(OBJ + 0x1C, 4))[0],
            "p20": struct.unpack("<I", uc.mem_read(OBJ + 0x20, 4))[0],
            "p24": struct.unpack("<I", uc.mem_read(OBJ + 0x24, 4))[0],
            "b3c": struct.unpack("<B", uc.mem_read(OBJ + 0x3C, 1))[0],
        }

    cases = [
        (False, False, False), # no chunk -> 0
        (True, True, True),    # already parsed -> 1
        (True, False, False),  # invalid magic -> 1, p10 = 0
        (True, True, False),   # valid chunk -> 1, all ptrs populated
    ]
    for case in cases:
        o = run_one(orig, *case)
        c = run_one(staged, *case)
        assert o == c, f"00295300 {case} failed: {o} vs {c}"
    print("ui_func_00295300: PASS")

def test_00295f04():
    print("--- Testing script_vm_func_00295f04 ---")
    addr = 0x00295F04
    size = 140
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_00295f04", ROOT / "build")
    syms = {
        "Tbb_GetGlobalSubTable": 0x002C0EC4,
        "Tbb_GetPayloadData": 0x002C0E9C,
        "camp_func_002b9364": 0x002B9364,
    }
    staged = stage_body(comp, relocs, addr, syms)

    def run_one(c_bytes, level, base_val, diff_factor):
        uc = base_emulator(c_bytes, addr)
        DATA_BASE = 0x20000000
        uc.mem_map(DATA_BASE, 0x10000)

        OBJ = DATA_BASE + 0x100
        INFO = DATA_BASE + 0x200
        TBL1 = DATA_BASE + 0x400
        TBL2 = DATA_BASE + 0x800

        uc.mem_write(INFO + 3, struct.pack("<B", 10)) # level in info is 10
        # TBL1 is u32 array for base costs
        for i in range(100):
            uc.mem_write(TBL1 + i * 4, struct.pack("<I", base_val + i))
        # TBL2 is u16 array for rate factors
        for i in range(15):
            uc.mem_write(TBL2 + i * 2, struct.pack("<H", diff_factor))

        # Stubs
        # 0x2c0ec4: return sub_id (r1)
        uc.mem_write(0x002C0EC4, b"\x01\x00\xa0\xe1\x1e\xff\x2f\xe1") # mov r0, r1; bx lr
        # 0x2c0e9c: if r0 == 1 return TBL1 else TBL2
        uc.mem_write(0x002C0E9C, (
            b"\x01\x00\x50\xe3" # cmp r0, #1
            b"\x04\x00\x9f\x05" # ldreq r0, [pc, #4] -> TBL1
            b"\x04\x00\x9f\x15" # ldrne r0, [pc, #4] -> TBL2
            b"\x1e\xff\x2f\xe1" # bx lr
            + struct.pack("<II", TBL1, TBL2)
        ))
        # 0x2b9364: return INFO (offset 8 from instruction is pc + 0)
        uc.mem_write(0x002B9364, (
            b"\x00\x00\x9f\xe5" # ldr r0, [pc, #0] -> INFO at offset 8
            b"\x1e\xff\x2f\xe1" # bx lr
            + struct.pack("<I", INFO)
        ))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, OBJ)
        uc.reg_write(UC_ARM_REG_R1, level)
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

    for lvl in [5, 10, 15, 25, 99]:
        o = run_one(orig, lvl, 250, 80)
        c = run_one(staged, lvl, 250, 80)
        assert o == c, f"00295f04 (lvl={lvl}) failed: {o} vs {c}"
    print("script_vm_func_00295f04: PASS")

def test_0028de84():
    print("--- Testing script_vm_func_0028de84 ---")
    addr = 0x0028DE84
    size = 136
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_0028de84", ROOT / "build")
    syms = {
        "camp_func_002b66ec": 0x002B66EC,
        "battle_func_002a89e4": 0x002A89E4,
        "engine_func_002b0788": 0x002B0788,
    }
    staged = stage_body(comp, relocs, addr, syms)

    def run_one(c_bytes, b23, id_val, target_idx, mask_val):
        uc = base_emulator(c_bytes, addr)
        DATA_BASE = 0x20000000
        uc.mem_map(DATA_BASE, 0x10000)

        OBJ = DATA_BASE + 0x100
        STRUCT_CAMP = DATA_BASE + 0x200
        STRUCT_BTL = DATA_BASE + 0x400

        uc.mem_write(OBJ + 0x23, struct.pack("<B", b23))
        uc.mem_write(OBJ + 0x34, struct.pack("<i", id_val))
        uc.mem_write(OBJ + 0x1C, struct.pack("<I", target_idx))

        uc.mem_write(STRUCT_CAMP + 0x72, struct.pack("<H", mask_val))
        uc.mem_write(STRUCT_BTL + 0x44, struct.pack("<H", mask_val))

        # Stubs (offset 8 is pc + 0)
        uc.mem_write(0x002B66EC, (
            b"\x00\x00\x9f\xe5" # ldr r0, [pc, #0]
            b"\x1e\xff\x2f\xe1" # bx lr
            + struct.pack("<I", STRUCT_CAMP)
        ))
        uc.mem_write(0x002A89E4, (
            b"\x00\x00\x9f\xe5" # ldr r0, [pc, #0]
            b"\x1e\xff\x2f\xe1" # bx lr
            + struct.pack("<I", STRUCT_BTL)
        ))
        # 0x2b0788: return bit + 100
        uc.mem_write(0x002B0788, (
            b"\x64\x00\x80\xe2" # add r0, r0, #100
            b"\x1e\xff\x2f\xe1" # bx lr
        ))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, OBJ)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)

        uc.emu_start(addr, lr, timeout=3000000)
        ret = uc.reg_read(UC_ARM_REG_R0)
        if ret >= 0x80000000: ret -= 0x100000000
        return {
            "ret": ret,
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
        }

    # Mask with bits 1, 3, 5 set (0b00101010 = 0x2A)
    cases = [
        (1, -5, 0, 0x2A), # b23 != 0 -> -1
        (0, -5, 0, 0x2A), # id < 0, target 0 -> bit 1 -> 101
        (0, -5, 1, 0x2A), # id < 0, target 1 -> bit 3 -> 103
        (0, 10, 2, 0x2A), # id >= 0, target 2 -> bit 5 -> 105
        (0, 10, 3, 0x2A), # target 3 (only 3 bits exist) -> -1
    ]
    for case in cases:
        o = run_one(orig, *case)
        c = run_one(staged, *case)
        assert o == c, f"0028de84 {case} failed: {o} vs {c}"
    print("script_vm_func_0028de84: PASS")

def main():
    test_002b32e0()
    test_002b0614()
    test_002a140c()
    test_00295300()
    test_00295f04()
    test_0028de84()
    print("\nALL 6 FUNCTIONS IN BATCH 4 PASSED DIFFERENTIAL VERIFICATION!")

if __name__ == "__main__":
    main()
