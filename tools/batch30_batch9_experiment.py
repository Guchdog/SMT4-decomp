#!/usr/bin/env python3
"""Differential test for batch 30 part 9:
- engine_func_0020e9ac (0x0020E9AC, 152 B)
- engine_func_0020eac4 (0x0020EAC4, 148 B)
- ui_func_002100f8 (0x002100F8, 144 B)
- engine_func_002118a0 (0x002118A0, 148 B)
- battle_func_00211c50 (0x00211C50, 148 B)
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
    UC_ARM_REG_S0,
    UC_ARM_REG_S1,
    UC_ARM_REG_S2,
    UC_ARM_REG_S3,
    UC_ARM_REG_S4,
    UC_ARM_REG_S5,
    UC_ARM_REG_S16,
    UC_ARM_REG_S17,
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

def test_0020e9ac():
    print("--- Testing engine_func_0020e9ac ---")
    addr = 0x0020E9AC
    size = 152
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_0020e9ac", ROOT / "build")
    symbol_map = {
        "func_002b2530": 0x002B2530,
        "func_002a7b7c": 0x002A7B7C,
        "func_00263e60": 0x00263E60,
        "func_002b2520": 0x002B2520,
        "engine_func_002c4360": 0x002C4360,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    SLOT_PTR = 0x0044CFD4
    R4_OBJ = 0x20000000
    CHILD_OBJ = 0x20001000

    def run_one(c_bytes, b2530_ret, r4_byte4, has_child, null_slot=False):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Stubs
        # func_002b2530: mov r0, b2530_ret; bx lr
        stub_b2530 = bytes([b2530_ret, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1])
        uc.mem_write(0x002B2530, stub_b2530)
        # Others: bx lr
        bx_lr = b"\x1e\xff\x2f\xe1"
        uc.mem_write(0x002A7B7C, bx_lr)
        uc.mem_write(0x00263E60, bx_lr)
        uc.mem_write(0x002B2520, bx_lr)
        uc.mem_write(0x002C4360, bx_lr)

        if null_slot:
            uc.mem_write(SLOT_PTR, struct.pack("<I", 0))
        else:
            uc.mem_write(SLOT_PTR, struct.pack("<I", R4_OBJ))
            r4_data = bytearray(0x40)
            struct.pack_into("<I", r4_data, 0, 0x20002000)
            struct.pack_into("<B", r4_data, 4, r4_byte4)
            struct.pack_into("<I", r4_data, 8, CHILD_OBJ if has_child else 0)
            uc.mem_write(R4_OBJ, bytes(r4_data))
            if has_child:
                uc.mem_write(CHILD_OBJ, b"\x00" * 0x200)

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
            "slot": struct.unpack("<I", uc.mem_read(SLOT_PTR, 4))[0],
            "r4_mem": uc.mem_read(R4_OBJ, 0x10) if not null_slot else b"",
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
        }

    cases = [
        (0, 1, True, False),  # Normal with child -> 0
        (0, 1, False, False), # Normal without child -> 0
        (1, 1, True, False),  # b2530 != 0 -> 1
        (0, 0, True, False),  # r4[4] == 0 -> 1
        (0, 1, True, True),   # null slot -> 0
    ]

    for b_ret, b4, hc, ns in cases:
        o = run_one(orig, b_ret, b4, hc, ns)
        c = run_one(staged, b_ret, b4, hc, ns)
        assert o == c, f"0020e9ac mismatch: {o} vs {c}"
    print("engine_func_0020e9ac: PASS")

def test_0020eac4():
    print("--- Testing engine_func_0020eac4 ---")
    addr = 0x0020EAC4
    size = 148
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_0020eac4", ROOT / "build")
    symbol_map = {
        "func_00296f60": 0x00296F60,
        "func_00289640": 0x00289640,
        "func_002b8ce4": 0x002B8CE4,
        "func_002c1f28": 0x002C1F28,
        "func_002a0678": 0x002A0678,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    LOG_CALLS = 0x20000000

    def run_one(c_bytes, r296f60_1, r289640, r2b8ce4_0, r2b8ce4_1, r2c1f28, r296f60_0):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Clear log
        uc.mem_write(LOG_CALLS, b"\x00" * 0x40)

        # Stubs:
        # func_00296f60(r0): if r0==1 return r296f60_1 else return r296f60_0
        # cmp r0, #1; moveq r0, #r296f60_1; movne r0, #r296f60_0; bx lr
        stub_296f60 = bytes([
            0x01, 0x00, 0x50, 0xe3, # cmp r0, #1
            r296f60_1, 0x00, 0xa0, 0x03, # moveq r0, #r296f60_1
            r296f60_0, 0x00, 0xa0, 0x13, # movne r0, #r296f60_0
            0x1e, 0xff, 0x2f, 0xe1, # bx lr
        ])
        uc.mem_write(0x00296F60, stub_296f60)

        # func_00289640: return r289640
        uc.mem_write(0x00289640, bytes([r289640, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1]))

        # func_002b8ce4: return r2b8ce4_0
        uc.mem_write(0x002B8CE4, bytes([r2b8ce4_0, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1]))

        # func_002c1f28: return r2c1f28
        uc.mem_write(0x002C1F28, bytes([r2c1f28, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1]))

        # func_002a0678(r0, r1): log r0, r1
        call_log = []
        def hook_2a0678(uc, address, size, user_data):
            call_log.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)))
        from unicorn import UC_HOOK_CODE
        uc.hook_add(UC_HOOK_CODE, hook_2a0678, begin=0x002A0678, end=0x002A0678)
        uc.mem_write(0x002A0678, b"\x1e\xff\x2f\xe1")

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "log": call_log,
            "r4": uc.reg_read(UC_ARM_REG_R4),
        }

    cases = [
        # (r296f60_1, r289640, r2b8ce4_0, r2b8ce4_1, r2c1f28, r296f60_0)
        (7, 1, 0, 0, 0, 0), # 289640 != 0, 2b8ce4 returns 0 -> ret 0
        (7, 1, 1, 1, 0, 0), # 289640 != 0, 2b8ce4 returns 1 -> ret 1
        (7, 0, 0, 0, 1, 0), # 289640 == 0, 2c1f28 != 0 -> ret 1
        (7, 0, 0, 0, 0, 2), # 296f60(0) == 2 -> ret 1
        (7, 0, 0, 0, 0, 0), # 296f60(0) == 0 -> calls 2a0678(0, 7), 2a0678(1, 7), ret 0
        (9, 0, 0, 0, 0, 1), # 296f60(0) == 1 -> calls 2a0678(0, 9), 2a0678(1, 9), ret 0
    ]

    for c_tuple in cases:
        o = run_one(orig, *c_tuple)
        c = run_one(staged, *c_tuple)
        assert o == c, f"0020eac4 mismatch for {c_tuple}: {o} vs {c}"
    print("engine_func_0020eac4: PASS")

def test_002100f8():
    print("--- Testing ui_func_002100f8 ---")
    addr = 0x002100F8
    size = 144
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_002100f8", ROOT / "build")
    symbol_map = {
        "ui_func_00263254": 0x00263254,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    LOG_CALLS = 0x20000000

    def run_one(c_bytes, x, y, w, h, f4, f5, v0, v1, v2, v3):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Clear log
        uc.mem_write(LOG_CALLS, b"\x00" * 0x100)

        # ui_func_00263254: records (r0, r1, s0, s1, s2, s3, s4, s5)
        # We can implement a hook or a stub
        records = []
        def hook_263254(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            # Read VFP floats
            s0_raw = uc.reg_read(UC_ARM_REG_S0)
            s1_raw = uc.reg_read(UC_ARM_REG_S1)
            s2_raw = uc.reg_read(UC_ARM_REG_S2)
            s3_raw = uc.reg_read(UC_ARM_REG_S3)
            s4_raw = uc.reg_read(UC_ARM_REG_S4)
            s5_raw = uc.reg_read(UC_ARM_REG_S5)

            s0 = struct.unpack("<f", struct.pack("<I", s0_raw))[0]
            s1 = struct.unpack("<f", struct.pack("<I", s1_raw))[0]
            s2 = struct.unpack("<f", struct.pack("<I", s2_raw))[0]
            s3 = struct.unpack("<f", struct.pack("<I", s3_raw))[0]
            s4 = struct.unpack("<f", struct.pack("<I", s4_raw))[0]
            s5 = struct.unpack("<f", struct.pack("<I", s5_raw))[0]

            records.append((r0, r1, round(s0, 4), round(s1, 4), round(s2, 4), round(s3, 4), round(s4, 4), round(s5, 4)))

        from unicorn import UC_HOOK_CODE
        uc.hook_add(UC_HOOK_CODE, hook_263254, begin=0x00263254, end=0x00263254)
        # Stub at 0x00263254: bx lr
        uc.mem_write(0x00263254, b"\x1e\xff\x2f\xe1")

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, v0)
        uc.reg_write(UC_ARM_REG_R1, v1)
        uc.reg_write(UC_ARM_REG_R2, v2)
        uc.reg_write(UC_ARM_REG_R3, v3)

        # VFP float args
        uc.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", x))[0])
        uc.reg_write(UC_ARM_REG_S1, struct.unpack("<I", struct.pack("<f", y))[0])
        uc.reg_write(UC_ARM_REG_S2, struct.unpack("<I", struct.pack("<f", w))[0])
        uc.reg_write(UC_ARM_REG_S3, struct.unpack("<I", struct.pack("<f", h))[0])
        uc.reg_write(UC_ARM_REG_S4, struct.unpack("<I", struct.pack("<f", f4))[0])
        uc.reg_write(UC_ARM_REG_S5, struct.unpack("<I", struct.pack("<f", f5))[0])

        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)
        uc.reg_write(UC_ARM_REG_R7, 0x44444444)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "records": records,
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
        }

    cases = [
        (10.0, 20.0, 100.0, 50.0, 1.0, 2.0, 0x1000, 0x2000, 0x3000, 0x4000),
        (-5.0, 0.0, 30.0, 40.0, 0.5, -1.0, 0x5000, 0x6000, 0x7000, 0x8000),
    ]

    for c_args in cases:
        o = run_one(orig, *c_args)
        c = run_one(staged, *c_args)
        assert o == c, f"002100f8 mismatch: {o} vs {c}"
    print("ui_func_002100f8: PASS")

def test_002118a0():
    print("--- Testing engine_func_002118a0 ---")
    addr = 0x002118A0
    size = 148
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_002118a0", ROOT / "build")
    symbol_map = {
        "func_0028df3c": 0x0028DF3C,
        "func_00289640": 0x00289640,
        "func_00286880": 0x00286880,
        "func_0028686c": 0x0028686C,
        "func_00296f60": 0x00296F60,
        "func_00286928": 0x00286928,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    OBJ_PTR = 0x20000000
    CTX_0043E188 = 0x0043E188

    def run_one(c_bytes, r289640_val, r286880_val, null_obj=False):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Context 0x0043E188 + 8 -> OBJ_PTR or 0
        if null_obj:
            uc.mem_write(CTX_0043E188 + 8, struct.pack("<I", 0))
        else:
            uc.mem_write(CTX_0043E188 + 8, struct.pack("<I", OBJ_PTR))
            uc.mem_write(OBJ_PTR, b"\x00" * 0x40)

        # Stubs
        bx_lr = b"\x1e\xff\x2f\xe1"
        uc.mem_write(0x0028DF3C, bx_lr)
        # func_00289640: return r289640_val
        uc.mem_write(0x00289640, bytes([r289640_val, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1]))
        # func_00286880: return r286880_val
        uc.mem_write(0x00286880, bytes([r286880_val, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1]))
        # func_0028686c: return 0x77
        uc.mem_write(0x0028686C, bytes([0x77, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1]))
        # func_00296f60: return 0x88
        uc.mem_write(0x00296F60, bytes([0x88, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1]))

        # Hook func_00286928(r0, r1, r2, r3, sp[0], sp[4])
        call_log = []
        def hook_286928(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            sp = uc.reg_read(UC_ARM_REG_SP)
            arg4 = struct.unpack("<I", uc.mem_read(sp, 4))[0]
            arg5 = struct.unpack("<I", uc.mem_read(sp + 4, 4))[0]
            call_log.append((r0, r1, r2, r3, arg4, arg5))

        from unicorn import UC_HOOK_CODE
        uc.hook_add(UC_HOOK_CODE, hook_286928, begin=0x00286928, end=0x00286928)
        uc.mem_write(0x00286928, bx_lr)

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)
        uc.reg_write(UC_ARM_REG_R7, 0x44444444)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "calls": call_log,
            "obj_mem": uc.mem_read(OBJ_PTR, 0x34) if not null_obj else b"",
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
        }

    cases = [
        (0, 0x14, False), # 289640 == 0, mode 0x14 -> mode 5, sets obj[0x30]=1, obj[0x31]=1
        (1, 0x08, False), # 289640 != 0, mode 0x08 -> mode 8, does not set obj
        (1, 0x03, True),  # 289640 != 0 with null obj -> does not touch obj
    ]

    for c_tuple in cases:
        o = run_one(orig, *c_tuple)
        c = run_one(staged, *c_tuple)
        assert o == c, f"002118a0 mismatch for {c_tuple}: {o} vs {c}"
    print("engine_func_002118a0: PASS")

def test_00211c50():
    print("--- Testing battle_func_00211c50 ---")
    addr = 0x00211C50
    size = 148
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("battle_func_00211c50", ROOT / "build")
    symbol_map = {
        "func_0031bdbc": 0x0031BDBC,
        "func_002bf41c": 0x002BF41C,
        "func_002c0ac8": 0x002C0AC8,
        "func_002c45b8": 0x002C45B8,
        "func_00289640": 0x00289640,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    OBJ_PTR = 0x20000000
    R4_PTR = 0x20001000

    def run_one(c_bytes, r2bf41c_ret, field_0c, field_64, r289640_ret):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Stubs
        # func_0031bdbc: return OBJ_PTR
        uc.mem_write(0x0031BDBC, struct.pack("<III", 0xe59f0000, 0xe12fff1e, OBJ_PTR))
        # func_002bf41c: return r2bf41c_ret
        uc.mem_write(0x002BF41C, bytes([r2bf41c_ret, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1]))
        # func_002c0ac8: return R4_PTR
        uc.mem_write(0x002C0AC8, struct.pack("<III", 0xe59f0000, 0xe12fff1e, R4_PTR))
        # func_002c45b8: bx lr
        uc.mem_write(0x002C45B8, b"\x1e\xff\x2f\xe1")
        # func_00289640: return r289640_ret
        uc.mem_write(0x00289640, bytes([r289640_ret, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1]))

        # Prepare R4 memory
        r4_data = bytearray(0x80)
        struct.pack_into("<I", r4_data, 0x0C, field_0c)
        struct.pack_into("<B", r4_data, 0x64, field_64)
        struct.pack_into("<f", r4_data, 0x28, 0.0)
        struct.pack_into("<B", r4_data, 0x30, 0)
        uc.mem_write(R4_PTR, bytes(r4_data))

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
            "field_30": struct.unpack("<B", uc.mem_read(R4_PTR + 0x30, 1))[0],
            "field_28": round(struct.unpack("<f", uc.mem_read(R4_PTR + 0x28, 4))[0], 4),
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
        }

    cases = [
        (0, 0, 0, 0), # 2bf41c == 0 -> ret 1
        (1, 1, 0, 0), # field_0c == 1 -> ret 1
        (1, 0, 0, 0), # field_64 == 0 -> field_30=1, field_28=-0.25f, ret 1
        (1, 0, 1, 0), # field_64 != 0, 289640 == 0 -> field_30=1, field_28=-0.1f, ret 0
        (1, 0, 1, 1), # field_64 != 0, 289640 != 0 -> ret 0
    ]

    for c_tuple in cases:
        o = run_one(orig, *c_tuple)
        c = run_one(staged, *c_tuple)
        assert o == c, f"00211c50 mismatch for {c_tuple}: {o} vs {c}"
    print("battle_func_00211c50: PASS")

if __name__ == "__main__":
    test_0020e9ac()
    test_0020eac4()
    test_002100f8()
    test_002118a0()
    test_00211c50()
    print("\nALL 5 FUNCTIONS IN BATCH 9 PASSED DIFFERENTIAL VERIFICATION!")
