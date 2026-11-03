#!/usr/bin/env python3
"""Differential test for batch 30 B part 16:
- ui_func_002cd754 (0x002CD754, 116 B)
- engine_func_002cd880 (0x002CD880, 104 B)
- camp_func_002cde1c (0x002CDE1C, 96 B)
- engine_func_002d14d8 (0x002D14D8, 120 B)
- engine_func_002db9d0 (0x002DB9D0, 112 B)
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
    UC_ARM_REG_S0,
    UC_ARM_REG_S1,
    UC_ARM_REG_S2,
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


def test_002cd754():
    print("--- Testing ui_func_002cd754 ---")
    addr = 0x002CD754
    size = 116
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_002cd754", ROOT / "build")

    STUB_UI_BASE = 0x00293C98
    STUB_P0 = 0x00296F60
    STUB_P2 = 0x00289640
    STUB_CMD = 0x00286928

    staged = stage_body(comp, relocs, addr, {
        "ui_func_00293c98": STUB_UI_BASE,
        "engine_func_00296f60": STUB_P0,
        "engine_func_00289640": STUB_P2,
        "engine_func_00286928": STUB_CMD,
    })

    UI_BASE_ADDR = 0x20010000
    TARGET_OBJ = 0x20020000
    P0_ADDR = 0x20030000
    HOLDER_ADDR = 0x20040000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, has_holder: bool):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_UI_BASE, stub_code)
        uc.mem_write(STUB_P0, stub_code)
        uc.mem_write(STUB_P2, stub_code)
        uc.mem_write(STUB_CMD, stub_code)

        # Setup UI base struct
        uc.mem_write(UI_BASE_ADDR, b"\x00" * 0x3000)
        uc.mem_write(UI_BASE_ADDR + 0x2234, struct.pack("<I", TARGET_OBJ))

        # Setup 0x0043E188
        uc.mem_write(0x0043E188, struct.pack("<II", 0, HOLDER_ADDR if has_holder else 0))
        if has_holder:
            uc.mem_write(HOLDER_ADDR, b"\x00" * 0x1000)

        cmd_calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_UI_BASE:
                uc.reg_write(UC_ARM_REG_R0, UI_BASE_ADDR)
            elif address == STUB_P0:
                uc.reg_write(UC_ARM_REG_R0, P0_ADDR)
            elif address == STUB_P2:
                uc.reg_write(UC_ARM_REG_R0, 0x5555)
            elif address == STUB_CMD:
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                sp = uc.reg_read(UC_ARM_REG_SP)
                sp0, sp1 = struct.unpack("<II", uc.mem_read(sp, 8))
                cmd_calls.append((r0, r1, r2, r3, sp0, sp1))
                uc.reg_write(UC_ARM_REG_R0, 0x8888)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        ret = uc.reg_read(UC_ARM_REG_R0)
        holder_byte = struct.unpack("<B", uc.mem_read(HOLDER_ADDR + 0x0A11, 1))[0] if has_holder else 0
        return ret, holder_byte, cmd_calls

    for has_h in [True, False]:
        r1, b1, c1 = run_one(orig, has_h)
        r2, b2, c2 = run_one(staged, has_h)
        assert r1 == r2, f"Ret mismatch: orig={hex(r1)}, comp={hex(r2)}"
        assert b1 == b2, f"Holder byte mismatch: orig={hex(b1)}, comp={hex(b2)}"
        assert c1 == c2, f"Cmd calls mismatch: orig={c1}, comp={c2}"
    print("ui_func_002cd754: PASS")


def test_002cd880():
    print("--- Testing engine_func_002cd880 ---")
    addr = 0x002CD880
    size = 104
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_002cd880", ROOT / "build")

    STUB_P2 = 0x00289640
    STUB_P0 = 0x00296F60
    STUB_EVT = 0x0025955C

    staged = stage_body(comp, relocs, addr, {
        "engine_func_00289640": STUB_P2,
        "engine_func_00296f60": STUB_P0,
        "eventCommand_func_0025955c": STUB_EVT,
    })

    MGR_ADDR = 0x20010000
    P0_ADDR = 0x20020000
    P1_ADDR = 0x20030000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, p2_ret: int, mgr_a: int, mgr_b: int):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_P2, stub_code)
        uc.mem_write(STUB_P0, stub_code)
        uc.mem_write(STUB_EVT, stub_code)

        uc.mem_write(0x0043E088, struct.pack("<I", MGR_ADDR))
        uc.mem_write(MGR_ADDR, b"\x00" * 0x30)
        uc.mem_write(MGR_ADDR + 0x10, struct.pack("<II", mgr_a, mgr_b))

        evt_calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_P2:
                uc.reg_write(UC_ARM_REG_R0, p2_ret)
            elif address == STUB_P0:
                arg = uc.reg_read(UC_ARM_REG_R0)
                uc.reg_write(UC_ARM_REG_R0, P0_ADDR if arg == 0 else P1_ADDR)
            elif address == STUB_EVT:
                p0 = uc.reg_read(UC_ARM_REG_R0)
                p1 = uc.reg_read(UC_ARM_REG_R1)
                cmd = uc.reg_read(UC_ARM_REG_R2)
                s0 = struct.unpack("<f", struct.pack("<I", uc.reg_read(UC_ARM_REG_S0)))[0]
                evt_calls.append((p0, p1, cmd, s0))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, evt_calls

    test_cases = [
        # (p2_ret, mgr_a, mgr_b)
        (1, 10, 10),      # p2 != 0, a == b -> returns 1
        (1, 10, 20),      # p2 != 0, a != b -> returns 0
        (0, 10, 20),      # p2 == 0 -> calls eventCommand(P0, P1, 1, 1.0f), returns 0
    ]

    for tc in test_cases:
        r1, e1 = run_one(orig, *tc)
        r2, e2 = run_one(staged, *tc)
        assert r1 == r2, f"Ret mismatch: orig={r1}, comp={r2} for {tc}"
        assert e1 == e2, f"Evt calls mismatch: orig={e1}, comp={e2} for {tc}"
    print("engine_func_002cd880: PASS")


def test_002cde1c():
    print("--- Testing camp_func_002cde1c ---")
    addr = 0x002CDE1C
    size = 96
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("camp_func_002cde1c", ROOT / "build")

    STUB_TABLE = 0x002C0EC4
    STUB_PAYLOAD = 0x002C0E9C
    STUB_COUNT = 0x002C0E4C

    staged = stage_body(comp, relocs, addr, {
        "Tbb_GetGlobalSubTable": STUB_TABLE,
        "Tbb_GetPayloadData": STUB_PAYLOAD,
        "Tbb_GetRowCount": STUB_COUNT,
    })

    PAYLOAD_ADDR = 0x20010000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, key: int, rows: list[int]):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_TABLE, stub_code)
        uc.mem_write(STUB_PAYLOAD, stub_code)
        uc.mem_write(STUB_COUNT, stub_code)

        for i, rk in enumerate(rows):
            row_addr = PAYLOAD_ADDR + i * 0x20
            uc.mem_write(row_addr, b"\x00" * 0x20)
            uc.mem_write(row_addr, struct.pack("<b", rk))

        def code_hook(uc, address, sz, user_data):
            if address == STUB_TABLE:
                uc.reg_write(UC_ARM_REG_R0, 0x1234)
            elif address == STUB_PAYLOAD:
                uc.reg_write(UC_ARM_REG_R0, PAYLOAD_ADDR)
            elif address == STUB_COUNT:
                uc.reg_write(UC_ARM_REG_R0, len(rows))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, key)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret

    test_cases = [
        # (key, rows)
        (5, [5, 10, 15]),            # key at index 0 -> PAYLOAD_ADDR
        (10, [5, 10, 15]),           # key at index 1 -> PAYLOAD_ADDR + 0x20
        (15, [5, 10, 15]),           # key at index 2 -> PAYLOAD_ADDR + 0x40
        (20, [5, 10, 15]),           # key not found -> 0
        (-3, [1, -3, 5]),            # negative key found -> PAYLOAD_ADDR + 0x20
        (5, []),                     # empty rows -> 0
    ]

    for tc in test_cases:
        r1 = run_one(orig, *tc)
        r2 = run_one(staged, *tc)
        assert r1 == r2, f"Ret mismatch: orig={hex(r1)}, comp={hex(r2)} for {tc}"
    print("camp_func_002cde1c: PASS")


def test_002d14d8():
    print("--- Testing engine_func_002d14d8 ---")
    addr = 0x002D14D8
    size = 120
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_002d14d8", ROOT / "build")

    STUB_SUB = 0x0026959C
    STUB_ITEM = 0x00302494

    staged = stage_body(comp, relocs, addr, {
        "func_0026959c": STUB_SUB,
        "engine_func_00302494": STUB_ITEM,
    })

    OBJ_ADDR = 0x20010000
    SUB_ADDR = 0x20020000
    ITEMS_ADDR = 0x20030000
    SLOTS_ADDR = 0x20040000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, has_sub: bool, has_ptr: bool, obj_type: int, item_flags: list[int]):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_SUB, stub_code)
        uc.mem_write(STUB_ITEM, stub_code)

        uc.mem_write(OBJ_ADDR, b"\x00" * 0x100)
        uc.mem_write(OBJ_ADDR + 0x0C, struct.pack("<H", obj_type))
        uc.mem_write(OBJ_ADDR + 0x9C, struct.pack("<I", SUB_ADDR if has_sub else 0))
        uc.mem_write(OBJ_ADDR + 0xA0, struct.pack("<I", SLOTS_ADDR))

        if has_sub:
            uc.mem_write(SUB_ADDR, b"\x00" * 0x40)
            uc.mem_write(SUB_ADDR + 0x08, struct.pack("<I", len(item_flags)))
            uc.mem_write(SUB_ADDR + 0x10, struct.pack("<I", 0x20050000 if has_ptr else 0))
            uc.mem_write(SUB_ADDR + 0x18, struct.pack("<I", ITEMS_ADDR))

            for i, fl in enumerate(item_flags):
                uc.mem_write(ITEMS_ADDR + i * 0x28, b"\x00" * 0x28)
                uc.mem_write(ITEMS_ADDR + i * 0x28 + 0x10, struct.pack("<I", fl))

        item_calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_ITEM:
                o = uc.reg_read(UC_ARM_REG_R0)
                s = uc.reg_read(UC_ARM_REG_R1)
                item_calls.append((o, s))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, OBJ_ADDR)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        return item_calls

    test_cases = [
        # (has_sub, has_ptr, type, item_flags)
        (True, True, 3, [0, 1, 0]),         # items 0 and 2 have flag 0 -> called for slot 0 and slot 2
        (True, True, 3, [1, 1]),            # no flags 0 -> no calls
        (True, True, 2, [0, 0]),            # type != 3 -> returns early
        (True, False, 3, [0]),              # has_ptr is false -> returns early
        (False, False, 3, []),              # no sub -> returns early
    ]

    for tc in test_cases:
        c1 = run_one(orig, *tc)
        c2 = run_one(staged, *tc)
        assert c1 == c2, f"Item calls mismatch: orig={c1}, comp={c2} for {tc}"
    print("engine_func_002d14d8: PASS")


def test_002db9d0():
    print("--- Testing engine_func_002db9d0 ---")
    addr = 0x002DB9D0
    size = 112
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_002db9d0", ROOT / "build")

    STUB_P0 = 0x00296F60
    STUB_SUB = 0x00250FC4
    STUB_ADD = 0x00295CBC
    STUB_CHECK = 0x002CDB50
    STUB_SFX = 0x002B91C4
    STUB_CB = 0x002117E8

    staged = stage_body(comp, relocs, addr, {
        "engine_func_00296f60": STUB_P0,
        "ui_func_00250fc4": STUB_SUB,
        "script_vm_func_00295cbc": STUB_ADD,
        "func_002cdb50": STUB_CHECK,
        "script_vm_func_002b91c4": STUB_SFX,
        "func_002117e8": STUB_CB,
    })

    P0_ADDR = 0x20010000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, val: int, check_ret: int):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_P0, stub_code)
        uc.mem_write(STUB_SUB, stub_code)
        uc.mem_write(STUB_ADD, stub_code)
        uc.mem_write(STUB_CHECK, stub_code)
        uc.mem_write(STUB_SFX, stub_code)
        uc.mem_write(STUB_CB, stub_code)

        actions = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_P0:
                arg = uc.reg_read(UC_ARM_REG_R0)
                uc.reg_write(UC_ARM_REG_R0, P0_ADDR if arg == 0 else (val & 0xFFFFFFFF))
            elif address == STUB_SUB:
                p0 = uc.reg_read(UC_ARM_REG_R0)
                amt = uc.reg_read(UC_ARM_REG_R1)
                actions.append(("SUB", p0, amt))
            elif address == STUB_ADD:
                p0 = uc.reg_read(UC_ARM_REG_R0)
                amt = uc.reg_read(UC_ARM_REG_R1)
                actions.append(("ADD", p0, amt))
            elif address == STUB_CHECK:
                uc.reg_write(UC_ARM_REG_R0, check_ret)
            elif address == STUB_SFX:
                sfx = uc.reg_read(UC_ARM_REG_R0)
                actions.append(("SFX", sfx))
            elif address == STUB_CB:
                v = uc.reg_read(UC_ARM_REG_R0)
                actions.append(("CB", v))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, actions

    test_cases = [
        # (val, check_ret)
        (-50, 0),         # val < 0 -> calls SUB(P0, 50), check 0 -> no SFX/CB
        (-50, 1),         # val < 0 -> calls SUB(P0, 50), check 1 -> SFX(0x01000174), CB(-50)
        (100, 0),         # val >= 0 -> calls ADD(P0, 100), check 0 -> no SFX/CB
        (100, 1),         # val >= 0 -> calls ADD(P0, 100), check 1 -> SFX, CB(100)
        (0, 1),           # val == 0 -> calls ADD(P0, 0), check 1 -> SFX, CB(0)
    ]

    for tc in test_cases:
        r1, a1 = run_one(orig, *tc)
        r2, a2 = run_one(staged, *tc)
        assert r1 == r2, f"Ret mismatch: orig={r1}, comp={r2} for {tc}"
        assert a1 == a2, f"Actions mismatch: orig={a1}, comp={a2} for {tc}"
    print("engine_func_002db9d0: PASS")


def main():
    test_002cd754()
    test_002cd880()
    test_002cde1c()
    test_002d14d8()
    test_002db9d0()
    print("\nALL 5 FUNCTIONS IN BATCH 30 B PART 16 PASSED WITH 100% DIFFERENTIAL FIDELITY!")

if __name__ == "__main__":
    main()
