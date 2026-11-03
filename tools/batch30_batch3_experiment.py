#!/usr/bin/env python3
"""Differential test for batch 30 part 3:
- engine_func_002bc170 (0x002BC170, 144 B)
- engine_func_002c25f4 (0x002C25F4, 144 B)
- battle_func_002c854c (0x002C854C, 136 B)
- script_vm_func_002c8a78 (0x002C8A78, 148 B)
- script_vm_func_002d0400 (0x002D0400, 152 B)
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
    UC_ARM_REG_S2,
    UC_ARM_REG_S3,
    UC_ARM_REG_S4,
    UC_ARM_REG_S5,
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

def test_002bc170():
    print("--- Testing engine_func_002bc170 ---")
    addr = 0x002BC170
    size = 144
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_002bc170", ROOT / "build")
    staged = stage_body(comp, relocs, addr, {})

    def run_one(c_bytes, l, r, b, t, n, f):
        uc = base_emulator(c_bytes, addr)
        DATA_BASE = 0x20000000
        uc.mem_map(DATA_BASE, 0x1000)

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, DATA_BASE)
        uc.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", l))[0])
        uc.reg_write(UC_ARM_REG_S1, struct.unpack("<I", struct.pack("<f", r))[0])
        uc.reg_write(UC_ARM_REG_S2, struct.unpack("<I", struct.pack("<f", b))[0])
        uc.reg_write(UC_ARM_REG_S3, struct.unpack("<I", struct.pack("<f", t))[0])
        uc.reg_write(UC_ARM_REG_S4, struct.unpack("<I", struct.pack("<f", n))[0])
        uc.reg_write(UC_ARM_REG_S5, struct.unpack("<I", struct.pack("<f", f))[0])

        uc.emu_start(addr, lr, timeout=3000000)
        return struct.unpack("<16f", uc.mem_read(DATA_BASE, 64))

    cases = [
        (-200.0, 200.0, -120.0, 120.0, 1.0, 1000.0),
        (0.0, 400.0, 0.0, 240.0, 0.1, 50.0),
        (-10.0, 50.0, 20.0, 100.0, 5.0, 25.0),
    ]
    for case in cases:
        o = run_one(orig, *case)
        c = run_one(staged, *case)
        for i in range(16):
            assert abs(o[i] - c[i]) < 1e-5, f"002bc170 matrix element {i} mismatch: {o[i]} vs {c[i]}"
    print("engine_func_002bc170: PASS")

def test_002c25f4():
    print("--- Testing engine_func_002c25f4 ---")
    addr = 0x002C25F4
    size = 144
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_002c25f4", ROOT / "build")
    syms = {
        "engine_func_002c4b30": 0x002C4B30,
    }
    staged = stage_body(comp, relocs, addr, syms)

    def run_one(c_bytes, has_r4, f4, f18, f20):
        uc = base_emulator(c_bytes, addr)
        DATA_BASE = 0x20000000
        uc.mem_map(DATA_BASE, 0x10000)

        # Map 0x004C6000 (0x00465000 is inside CODE_BASE 0x00100000..0x00480000)
        uc.mem_map(0x004C6000, 0x1000)

        R4_PTR = DATA_BASE + 0x100
        if has_r4:
            uc.mem_write(0x004C6290 + 0x9C, struct.pack("<I", R4_PTR))
            uc.mem_write(R4_PTR + 4, struct.pack("<I", f4))
            uc.mem_write(R4_PTR + 8, struct.pack("<I", 0x100)) # size = 0x100
            uc.mem_write(R4_PTR + 0x18, struct.pack("<I", f18))
            uc.mem_write(R4_PTR + 0x20, struct.pack("<I", f20))
            for off in [0x0C, 0x10, 0x14, 0x24, 0x28, 0x30, 0x34]:
                uc.mem_write(R4_PTR + off, struct.pack("<I", 0xAAAAAAAA))
        else:
            uc.mem_write(0x004C6290 + 0x9C, struct.pack("<I", 0))

        # Stub 0x2c4b30: record r0, r1
        uc.mem_write(0x002C4B30, (
            b"\x08\x20\x9f\xe5" # ldr r2, [pc, #8] -> DATA_BASE at offset 16
            b"\x00\x00\x82\xe5" # str r0, [r2]
            b"\x04\x10\x82\xe5" # str r1, [r2, #4]
            b"\x1e\xff\x2f\xe1" # bx lr
            + struct.pack("<I", DATA_BASE)
        ))
        uc.mem_write(DATA_BASE, struct.pack("<II", 0xDEADBEEF, 0xDEADBEEF))
        uc.mem_write(0x004652A0, struct.pack("<II", 0, 0))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "cb": struct.unpack("<II", uc.mem_read(DATA_BASE, 8)),
            "g52a0": struct.unpack("<II", uc.mem_read(0x004652A0, 8)),
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "cleared": struct.unpack("<7I", uc.mem_read(R4_PTR + 0x0C, 28)) if has_r4 else None,
        }

    # Case 1: no r4
    assert run_one(orig, False, 0, 0, 0) == run_one(staged, False, 0, 0, 0)
    # Case 2: active
    o = run_one(orig, True, 0x2000, 0x3000, 5)
    c = run_one(staged, True, 0x2000, 0x3000, 5)
    assert o == c and o["cb"] == (0x3000, 140), f"002c25f4 failed: {o} vs {c}"
    print("engine_func_002c25f4: PASS")

def test_002c854c():
    print("--- Testing battle_func_002c854c ---")
    addr = 0x002C854C
    size = 136
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("battle_func_002c854c", ROOT / "build")
    syms = {
        "battle_func_002bf41c": 0x002BF41C,
    }
    staged = stage_body(comp, relocs, addr, syms)

    def run_one(c_bytes, bf_ret, p_null, flag80k, ui_flag4):
        uc = base_emulator(c_bytes, addr)
        DATA_BASE = 0x20000000
        uc.mem_map(DATA_BASE, 0x10000)

        OBJ = DATA_BASE + 0x100
        INNER = DATA_BASE + 0x200
        uc.mem_write(OBJ + 8, struct.pack("<I", INNER))

        # Stub 0x2bf41c
        uc.mem_write(0x002BF41C, struct.pack("<I", 0xe3a00000 | (bf_ret & 0xff)) + b"\x1e\xff\x2f\xe1")

        P_5D30 = DATA_BASE + 0x400
        P_4290 = DATA_BASE + 0x600
        P_5D18 = DATA_BASE + 0x800
        P_42C8 = DATA_BASE + 0xA00

        if p_null:
            uc.mem_write(0x00435D30, struct.pack("<I", 0))
        else:
            uc.mem_write(0x00435D30, struct.pack("<I", P_5D30))
            uc.mem_write(0x00434290, struct.pack("<I", P_4290))
            uc.mem_write(0x00435D18, struct.pack("<I", P_5D18))
            uc.mem_write(0x004342C8, struct.pack("<I", P_42C8))

            uc.mem_write(P_42C8 + 0x634, struct.pack("<I", 0x80000 if flag80k else 0))
            uc.mem_write(P_5D30 + 0x0C, struct.pack("<I", 4 if ui_flag4 else 0))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, OBJ)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "r4": uc.reg_read(UC_ARM_REG_R4),
        }

    cases = [
        (0, False, False, False), # bf=0 -> 1
        (1, True, False, False),  # null ptr -> 1
        (1, False, True, True),   # 80k flag -> 0
        (1, False, False, False), # ui_flag missing -> 0
        (1, False, False, True),  # all good -> 1
    ]
    for case in cases:
        o = run_one(orig, *case)
        c = run_one(staged, *case)
        assert o == c, f"002c854c {case} failed: {o} vs {c}"
    print("battle_func_002c854c: PASS")

def test_002c8a78():
    print("--- Testing script_vm_func_002c8a78 ---")
    addr = 0x002C8A78
    size = 148
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_002c8a78", ROOT / "build")
    syms = {
        "func_00152af8": 0x00152AF8,
    }
    staged = stage_body(comp, relocs, addr, syms)

    def run_one(c_bytes):
        uc = base_emulator(c_bytes, addr)
        DATA_BASE = 0x20000000
        uc.mem_map(DATA_BASE, 0x10000)

        BASE = DATA_BASE + 0x1000
        # 0x00447E10 is inside CODE_BASE (0x00100000..0x00480000)
        uc.mem_write(0x00447E10, struct.pack("<I", BASE))

        # Setup slots
        # Main group (9 slots, indices 8..0 at BASE + i*44 + 0x1114)
        for i in range(9):
            slot = BASE + i * 44 + 0x1114
            if i in (2, 5):
                uc.mem_write(slot, b"\x01") # active
                uc.mem_write(slot + 0x20, struct.pack("<I", 0x3000 + i))
                uc.mem_write(slot + 0x24, b"\x01")
            else:
                uc.mem_write(slot, b"\x00") # inactive
                uc.mem_write(slot + 0x20, struct.pack("<I", 0))
                uc.mem_write(slot + 0x24, b"\x00")

        # Second group (3 slots, indices 2..0 at BASE + i*44 + 0x12A0)
        for i in range(3):
            slot = BASE + i * 44 + 0x12A0
            if i == 1:
                uc.mem_write(slot, b"\x01")
                uc.mem_write(slot + 0x20, struct.pack("<I", 0x4000 + i))
                uc.mem_write(slot + 0x24, b"\x01")
            else:
                uc.mem_write(slot, b"\x00")
                uc.mem_write(slot + 0x20, struct.pack("<I", 0))
                uc.mem_write(slot + 0x24, b"\x00")

        # Stub 0x152af8: append ptr to DATA_BASE list
        # We can implement a small counter and array in DATA_BASE
        RECORD_ADDR = DATA_BASE + 0x100
        uc.mem_write(RECORD_ADDR, struct.pack("<I", 0)) # count = 0
        uc.mem_write(0x00152AF8, (
            b"\x10\x10\x9f\xe5" # ldr r1, [pc, #16] -> RECORD_ADDR
            b"\x00\x20\x91\xe5" # ldr r2, [r1] (count)
            b"\x01\x30\x82\xe2" # add r3, r2, #1
            b"\x00\x30\x81\xe5" # str r3, [r1] (count++)
            b"\x02\x01\x81\xe7" # str r0, [r1, r2, lsl #2]! (+4 offset adjustment: str r0, [r1, r3, lsl #2])
            b"\x1e\xff\x2f\xe1" # bx lr
            + struct.pack("<I", RECORD_ADDR)
        ))
        # Better stub:
        uc.mem_write(0x00152AF8, (
            b"\x10\x10\x9f\xe5" # ldr r1, [pc, #16]
            b"\x00\x20\x91\xe5" # ldr r2, [r1]
            b"\x01\x30\x82\xe2" # add r3, r2, #1
            b"\x00\x30\x81\xe5" # str r3, [r1]
            b"\x02\x01\x81\xe5" # str r0, [r1, #4] (simplified: just xor)
            b"\x1e\xff\x2f\xe1" # bx lr
            + struct.pack("<I", RECORD_ADDR)
        ))

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

        # Read back flags
        flags = []
        for i in range(9):
            flags.append(uc.mem_read(BASE + i * 44 + 0x1114 + 0x24, 1)[0])
        for i in range(3):
            flags.append(uc.mem_read(BASE + i * 44 + 0x12A0 + 0x24, 1)[0])

        return {
            "calls": struct.unpack("<I", uc.mem_read(RECORD_ADDR, 4))[0],
            "flags": flags,
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
            "r8": uc.reg_read(UC_ARM_REG_R8),
        }

    o = run_one(orig)
    c = run_one(staged)
    assert o == c and o["calls"] == 3, f"002c8a78 failed: {o} vs {c}"
    print("script_vm_func_002c8a78: PASS")

def test_002d0400():
    print("--- Testing script_vm_func_002d0400 ---")
    addr = 0x002D0400
    size = 152
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_002d0400", ROOT / "build")
    syms = {
        "camp_func_0029909c": 0x0029909C,
        "func_002b6700": 0x002B6700,
    }
    staged = stage_body(comp, relocs, addr, syms)

    def run_one(c_bytes, id_a, id_b, mask_a, mask_b, p_a, p_b):
        uc = base_emulator(c_bytes, addr)
        DATA_BASE = 0x20000000
        uc.mem_map(DATA_BASE, 0x10000)

        A_PTR = DATA_BASE + 0x10
        B_PTR = DATA_BASE + 0x14
        uc.mem_write(A_PTR, struct.pack("<H", id_a))
        uc.mem_write(B_PTR, struct.pack("<H", id_b))

        REC_A = DATA_BASE + 0x100
        REC_B = DATA_BASE + 0x200
        uc.mem_write(REC_A + 4, struct.pack("<H", p_a))
        uc.mem_write(REC_B + 4, struct.pack("<H", p_b))

        # Stubs
        # 0x29909c: if id == id_a return mask_a else mask_b
        uc.mem_write(0x0029909C, (
            b"\x0c\x10\x9f\xe5" # ldr r1, [pc, #12] -> id_a
            b"\x01\x00\x50\xe1" # cmp r0, r1
            b"\x08\x00\x9f\x05" # ldreq r0, [pc, #8] -> mask_a
            b"\x08\x00\x9f\x15" # ldrne r0, [pc, #8] -> mask_b
            b"\x1e\xff\x2f\xe1" # bx lr
            + struct.pack("<III", id_a, mask_a, mask_b)
        ))

        # 0x2b6700: if id == id_a return REC_A else REC_B
        uc.mem_write(0x002B6700, (
            b"\x0c\x10\x9f\xe5"
            b"\x01\x00\x50\xe1"
            b"\x08\x00\x9f\x05"
            b"\x08\x00\x9f\x15"
            b"\x1e\xff\x2f\xe1"
            + struct.pack("<III", id_a, REC_A, REC_B)
        ))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, A_PTR)
        uc.reg_write(UC_ARM_REG_R1, B_PTR)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)
        uc.reg_write(UC_ARM_REG_R7, 0x44444444)
        uc.reg_write(UC_ARM_REG_R8, 0x55555555)

        uc.emu_start(addr, lr, timeout=3000000)
        ret = uc.reg_read(UC_ARM_REG_R0)
        # Convert to signed 32-bit
        if ret >= 0x80000000:
            ret -= 0x100000000
        return {
            "ret": ret,
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
            "r8": uc.reg_read(UC_ARM_REG_R8),
        }

    cases = [
        (10, 20, 0b10, 0b01, 100, 200), # mask diff -> 1
        (10, 20, 0b01, 0b10, 100, 200), # mask diff -> -1
        (10, 20, 0b11, 0b11, 100, 250), # same mask -> pb - pa = 150
        (10, 20, 0b11, 0b11, 300, 100), # same mask -> pb - pa = -200
    ]
    for case in cases:
        o = run_one(orig, *case)
        c = run_one(staged, *case)
        assert o == c, f"002d0400 {case} failed: {o} vs {c}"
    print("script_vm_func_002d0400: PASS")

def main():
    test_002bc170()
    test_002c25f4()
    test_002c854c()
    test_002c8a78()
    test_002d0400()
    print("\nALL 5 FUNCTIONS IN BATCH 3 PASSED DIFFERENTIAL VERIFICATION!")

if __name__ == "__main__":
    main()
