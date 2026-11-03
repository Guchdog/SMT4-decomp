#!/usr/bin/env python3
"""Differential test for batch 30 B part 1:
- engine_func_00201318 (0x00201318, 100 B)
- ui_func_00211824 (0x00211824, 124 B)
- script_vm_func_002147e8 (0x002147E8, 108 B)
- camp_func_00218ae4 (0x00218AE4, 112 B)
- battle_func_002196a4 (0x002196A4, 116 B)
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

def test_00201318():
    print("--- Testing engine_func_00201318 ---")
    addr = 0x00201318
    size = 100
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_00201318", ROOT / "build")
    symbol_map = {
        "func_00289640": 0x00289640,
        "func_00296f60": 0x00296F60,
        "eventCommand_func_0025955c": 0x0025955C,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    R0_OBJ = 0x20001000

    def run_one(c_bytes, ret_89640, r10_val, r14_val, ret_96f60):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # 0x0043E088 -> R0_OBJ
        uc.mem_write(0x0043E088, struct.pack("<I", R0_OBJ))
        uc.mem_write(R0_OBJ + 0x10, struct.pack("<II", r10_val, r14_val))

        calls = []
        uc.mem_write(0x00289640, b"\x1e\xff\x2f\xe1")
        def on_89640(u, a, s, ud):
            calls.append("89640")
            u.reg_write(UC_ARM_REG_R0, ret_89640)
        uc.hook_add(UC_HOOK_CODE, on_89640, None, 0x00289640, 0x00289640)

        uc.mem_write(0x00296F60, b"\x1e\xff\x2f\xe1")
        def on_96f60(u, a, s, ud):
            calls.append(("96f60", u.reg_read(UC_ARM_REG_R0)))
            u.reg_write(UC_ARM_REG_R0, ret_96f60)
        uc.hook_add(UC_HOOK_CODE, on_96f60, None, 0x00296F60, 0x00296F60)

        uc.mem_write(0x0025955C, b"\x1e\xff\x2f\xe1")
        def on_fade(u, a, s, ud):
            s0_b = u.reg_read(UC_ARM_REG_S0)
            f0 = struct.unpack("<f", struct.pack("<I", s0_b))[0]
            calls.append((
                "fade",
                u.reg_read(UC_ARM_REG_R0),
                u.reg_read(UC_ARM_REG_R1),
                u.reg_read(UC_ARM_REG_R2),
                round(f0, 2)
            ))
        uc.hook_add(UC_HOOK_CODE, on_fade, None, 0x0025955C, 0x0025955C)

        sp = STACK_BASE + STACK_SIZE - 0x100
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00100000)
        uc.reg_write(UC_ARM_REG_R4, 0xAAAAAAAA)

        uc.emu_start(addr, 0x00100000, timeout=200000)

        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "calls": calls,
            "r4": uc.reg_read(UC_ARM_REG_R4),
        }

    cases = [
        (1, 42, 42, 0),  # 89640 returns != 0, equal -> returns 1
        (1, 42, 99, 0),  # 89640 returns != 0, not equal -> returns 0
        (0, 0, 0, 0),    # 89640 returns 0, 96f60 returns 0 -> owner 0xFF
        (0, 0, 0, 1),    # 89640 returns 0, 96f60 returns 1 -> owner 0xFFFFFFFF
    ]

    for c_tuple in cases:
        o = run_one(orig, *c_tuple)
        c = run_one(staged, *c_tuple)
        assert o == c, f"00201318 mismatch for {c_tuple}: {o} vs {c}"
    print("engine_func_00201318: PASS")

def test_00211824():
    print("--- Testing ui_func_00211824 ---")
    addr = 0x00211824
    size = 124
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_00211824", ROOT / "build")
    symbol_map = {
        "func_00293c98": 0x00293C98,
        "func_00296f60": 0x00296F60,
        "func_00289640": 0x00289640,
        "func_00286928": 0x00286928,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    CTX_ADDR = 0x20001000
    OBJ_ADDR = 0x20002000

    def run_one(c_bytes, has_obj):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # 0x0043E188 + 4 -> OBJ_ADDR or 0
        obj_ptr = OBJ_ADDR if has_obj else 0
        uc.mem_write(0x0043E188 + 4, struct.pack("<I", obj_ptr))
        if has_obj:
            uc.mem_write(OBJ_ADDR + 0xA11, b"\x00")

        # CTX_ADDR + 0x2234 -> elem
        uc.mem_write(CTX_ADDR + 0x2234, struct.pack("<I", 0x55555555))

        calls = []
        uc.mem_write(0x00293C98, b"\x1e\xff\x2f\xe1")
        def on_ctx(u, a, s, ud):
            calls.append("293c98")
            u.reg_write(UC_ARM_REG_R0, CTX_ADDR)
        uc.hook_add(UC_HOOK_CODE, on_ctx, None, 0x00293C98, 0x00293C98)

        uc.mem_write(0x00296F60, b"\x1e\xff\x2f\xe1")
        def on_96f60(u, a, s, ud):
            calls.append(("96f60", u.reg_read(UC_ARM_REG_R0)))
            u.reg_write(UC_ARM_REG_R0, 0x66666666)
        uc.hook_add(UC_HOOK_CODE, on_96f60, None, 0x00296F60, 0x00296F60)

        uc.mem_write(0x00289640, b"\x1e\xff\x2f\xe1")
        def on_89640(u, a, s, ud):
            calls.append("89640")
            u.reg_write(UC_ARM_REG_R0, 0x22222222)
        uc.hook_add(UC_HOOK_CODE, on_89640, None, 0x00289640, 0x00289640)

        uc.mem_write(0x00286928, b"\x1e\xff\x2f\xe1")
        def on_86928(u, a, s, ud):
            sp = u.reg_read(UC_ARM_REG_SP)
            sp0, sp4 = struct.unpack("<II", u.mem_read(sp, 8))
            calls.append((
                "86928",
                u.reg_read(UC_ARM_REG_R0),
                u.reg_read(UC_ARM_REG_R1),
                u.reg_read(UC_ARM_REG_R2),
                u.reg_read(UC_ARM_REG_R3),
                sp0, sp4
            ))
        uc.hook_add(UC_HOOK_CODE, on_86928, None, 0x00286928, 0x00286928)

        sp = STACK_BASE + STACK_SIZE - 0x100
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00100000)
        uc.reg_write(UC_ARM_REG_R4, 0xAAAAAAAA)
        uc.reg_write(UC_ARM_REG_R5, 0xBBBBBBBB)
        uc.reg_write(UC_ARM_REG_R6, 0xCCCCCCCC)

        uc.emu_start(addr, 0x00100000, timeout=200000)

        val_a11 = uc.mem_read(OBJ_ADDR + 0xA11, 1)[0] if has_obj else 0
        return {
            "val_a11": val_a11,
            "calls": calls,
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
        }

    for has_o in (True, False):
        o = run_one(orig, has_o)
        c = run_one(staged, has_o)
        assert o == c, f"00211824 mismatch for has_obj={has_o}: {o} vs {c}"
    print("ui_func_00211824: PASS")

def test_002147e8():
    print("--- Testing script_vm_func_002147e8 ---")
    addr = 0x002147E8
    size = 108
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_002147e8", ROOT / "build")
    symbol_map = {
        "script_vm_func_002a7aa0": 0x002A7AA0,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    SB_ADDR = 0x20000000

    def run_one(c_bytes):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # 0x004BCE8C area
        uc.mem_write(SB_ADDR, b"\x00" * 0x1000)

        # Set some active slots:
        # ch 0: slot 2 = 0x1002, slot 10 = 0x1010, master = 0x10FF
        uc.mem_write(SB_ADDR + 0x284 + 2 * 4, struct.pack("<I", 0x1002))
        uc.mem_write(SB_ADDR + 0x284 + 10 * 4, struct.pack("<I", 0x1010))
        uc.mem_write(SB_ADDR + 0x26C + 0 * 4, struct.pack("<I", 0x10FF))

        # ch 3: slot 5 = 0x3005, master = 0x30FF
        uc.mem_write(SB_ADDR + 3 * 256 + 0x284 + 5 * 4, struct.pack("<I", 0x3005))
        uc.mem_write(SB_ADDR + 0x26C + 3 * 4, struct.pack("<I", 0x30FF))

        calls = []
        uc.mem_write(0x002A7AA0, b"\x1e\xff\x2f\xe1")
        def on_release(u, a, s, ud):
            calls.append(u.reg_read(UC_ARM_REG_R0))
        uc.hook_add(UC_HOOK_CODE, on_release, None, 0x002A7AA0, 0x002A7AA0)

        sp = STACK_BASE + STACK_SIZE - 0x100
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00100000)
        uc.reg_write(UC_ARM_REG_R4, 0xAAAAAAAA)
        uc.reg_write(UC_ARM_REG_R5, 0xBBBBBBBB)
        uc.reg_write(UC_ARM_REG_R6, 0xCCCCCCCC)
        uc.reg_write(UC_ARM_REG_R7, 0xDDDDDDDD)
        uc.reg_write(UC_ARM_REG_R8, 0xEEEEEEEE)
        uc.reg_write(UC_ARM_REG_SB, 0x12345678)
        uc.reg_write(UC_ARM_REG_SL, 0x87654321)

        uc.emu_start(addr, 0x00100000, timeout=200000)

        return {
            "calls": calls,
            "ch0_s2": struct.unpack("<I", uc.mem_read(SB_ADDR + 0x284 + 2 * 4, 4))[0],
            "ch0_s10": struct.unpack("<I", uc.mem_read(SB_ADDR + 0x284 + 10 * 4, 4))[0],
            "ch0_m": struct.unpack("<I", uc.mem_read(SB_ADDR + 0x26C + 0 * 4, 4))[0],
            "ch3_s5": struct.unpack("<I", uc.mem_read(SB_ADDR + 3 * 256 + 0x284 + 5 * 4, 4))[0],
            "ch3_m": struct.unpack("<I", uc.mem_read(SB_ADDR + 0x26C + 3 * 4, 4))[0],
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
            "r8": uc.reg_read(UC_ARM_REG_R8),
            "sb": uc.reg_read(UC_ARM_REG_SB),
            "sl": uc.reg_read(UC_ARM_REG_SL),
        }

    o = run_one(orig)
    c = run_one(staged)
    assert o == c, f"002147e8 mismatch: {o} vs {c}"
    print("script_vm_func_002147e8: PASS")

def test_00218ae4():
    print("--- Testing camp_func_00218ae4 ---")
    addr = 0x00218AE4
    size = 112
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("camp_func_00218ae4", ROOT / "build")
    symbol_map = {
        "camp_func_002bf030": 0x002BF030,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    BASE_ADDR = 0x20001000

    def run_one(c_bytes, count):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        uc.mem_write(BASE_ADDR, b"\x00" * 0x3000)
        uc.mem_write(BASE_ADDR + 0x218C, struct.pack("<h", count))

        calls = []
        uc.mem_write(0x002BF030, b"\x1e\xff\x2f\xe1")
        def on_bf030(u, a, s, ud):
            calls.append((u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
        uc.hook_add(UC_HOOK_CODE, on_bf030, None, 0x002BF030, 0x002BF030)

        sp = STACK_BASE + STACK_SIZE - 0x100
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00100000)
        uc.reg_write(UC_ARM_REG_R0, BASE_ADDR)
        uc.reg_write(UC_ARM_REG_R4, 0xAAAAAAAA)
        uc.reg_write(UC_ARM_REG_R5, 0xBBBBBBBB)
        uc.reg_write(UC_ARM_REG_R6, 0xCCCCCCCC)
        uc.reg_write(UC_ARM_REG_R7, 0xDDDDDDDD)
        uc.reg_write(UC_ARM_REG_R8, 0xEEEEEEEE)

        uc.emu_start(addr, 0x00100000, timeout=200000)

        f217c = struct.unpack("<I", uc.mem_read(BASE_ADDR + 0x217C, 4))[0]
        f2180 = struct.unpack("<I", uc.mem_read(BASE_ADDR + 0x2180, 4))[0]
        f218e = struct.unpack("<H", uc.mem_read(BASE_ADDR + 0x218E, 2))[0]

        return {
            "calls": calls,
            "f217c": f217c,
            "f2180": f2180,
            "f218e": f218e,
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
            "r8": uc.reg_read(UC_ARM_REG_R8),
        }

    cases = [0, -1, 1, 3]
    for cnt in cases:
        o = run_one(orig, cnt)
        c = run_one(staged, cnt)
        assert o == c, f"00218ae4 mismatch for count={cnt}: {o} vs {c}"
    print("camp_func_00218ae4: PASS")

def test_002196a4():
    print("--- Testing battle_func_002196a4 ---")
    addr = 0x002196A4
    size = 116
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("battle_func_002196a4", ROOT / "build")
    symbol_map = {
        "battle_func_002ae3f0": 0x002AE3F0,
        "battle_func_0029ac70": 0x0029AC70,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    A_ADDR = 0x20001000
    B_ADDR = 0x20001004

    def run_one(c_bytes, idA, idB, a_active, b_active, statA, statB):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        uc.mem_write(A_ADDR, struct.pack("<H", idA))
        uc.mem_write(B_ADDR, struct.pack("<H", idB))

        uc.mem_write(0x002AE3F0, b"\x1e\xff\x2f\xe1")
        def on_active(u, a, s, ud):
            id_val = u.reg_read(UC_ARM_REG_R0)
            ret = a_active if id_val == idA else b_active
            u.reg_write(UC_ARM_REG_R0, ret)
        uc.hook_add(UC_HOOK_CODE, on_active, None, 0x002AE3F0, 0x002AE3F0)

        uc.mem_write(0x0029AC70, b"\x1e\xff\x2f\xe1")
        def on_stat(u, a, s, ud):
            id_val = u.reg_read(UC_ARM_REG_R0)
            ret = statA if id_val == idA else statB
            u.reg_write(UC_ARM_REG_R0, ret)
        uc.hook_add(UC_HOOK_CODE, on_stat, None, 0x0029AC70, 0x0029AC70)

        sp = STACK_BASE + STACK_SIZE - 0x100
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00100000)
        uc.reg_write(UC_ARM_REG_R0, A_ADDR)
        uc.reg_write(UC_ARM_REG_R1, B_ADDR)
        uc.reg_write(UC_ARM_REG_R4, 0xAAAAAAAA)
        uc.reg_write(UC_ARM_REG_R5, 0xBBBBBBBB)
        uc.reg_write(UC_ARM_REG_R6, 0xCCCCCCCC)

        uc.emu_start(addr, 0x00100000, timeout=200000)

        return {
            "ret": struct.unpack("<i", struct.pack("<I", uc.reg_read(UC_ARM_REG_R0)))[0],
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
        }

    cases = [
        (0, 10, 1, 1, 50, 40),    # idA == 0 -> returns 0
        (10, 0, 1, 1, 50, 40),    # idB == 0 -> returns 0
        (10, 20, 0, 1, 50, 40),   # a inactive -> returns 0
        (10, 20, 1, 0, 50, 40),   # b inactive -> returns 0
        (10, 20, 1, 1, 50, 40),   # 50 - 40 = 10
        (10, 20, 1, 1, 30, 45),   # 30 - 45 = -15
    ]

    for c_tuple in cases:
        o = run_one(orig, *c_tuple)
        c = run_one(staged, *c_tuple)
        assert o == c, f"002196a4 mismatch for {c_tuple}: {o} vs {c}"
    print("battle_func_002196a4: PASS")

if __name__ == "__main__":
    test_00201318()
    test_00211824()
    test_002147e8()
    test_00218ae4()
    test_002196a4()
    print("\nALL 5 FUNCTIONS IN BATCH 30 B PART 1 PASSED DIFFERENTIAL VERIFICATION!")
