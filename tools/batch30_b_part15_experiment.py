#!/usr/bin/env python3
"""Differential test for batch 30 B part 15:
- ui_func_002b8adc (0x002B8ADC, 104 B)
- func_002be4dc (0x002BE4DC, 108 B)
- nn_sdk_func_002c1570 (0x002C1570, 104 B)
- script_vm_func_002c8630 (0x002C8630, 104 B)
- script_vm_func_002c9b3c (0x002C9B3C, 104 B)
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


def test_002b8adc():
    print("--- Testing ui_func_002b8adc ---")
    addr = 0x002B8ADC
    size = 104
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_002b8adc", ROOT / "build")

    STUB_CHECK = 0x002B2530
    STUB_CLEAN = 0x002B01A0
    STUB_FREE = 0x002C4360

    staged = stage_body(comp, relocs, addr, {
        "ui_func_002b2530": STUB_CHECK,
        "script_vm_func_002b01a0": STUB_CLEAN,
        "engine_func_002c4360": STUB_FREE,
    })

    INST_ADDR = 0x20010000
    SUB_HANDLE = 0x20020000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, has_inst: bool, check_ret: int, flag_byte: int):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_CHECK, stub_code)
        uc.mem_write(STUB_CLEAN, stub_code)
        uc.mem_write(STUB_FREE, stub_code)

        if has_inst:
            uc.mem_write(0x00447060, struct.pack("<I", INST_ADDR))
            inst_buf = bytearray(0x100)
            struct.pack_into("<I", inst_buf, 0, SUB_HANDLE)
            struct.pack_into("<B", inst_buf, 8, flag_byte)
            uc.mem_write(INST_ADDR, bytes(inst_buf))
        else:
            uc.mem_write(0x00447060, struct.pack("<I", 0))

        clean_calls = []
        free_calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_CHECK:
                uc.reg_write(UC_ARM_REG_R0, check_ret)
            elif address == STUB_CLEAN:
                clean_calls.append(uc.reg_read(UC_ARM_REG_R0))
            elif address == STUB_FREE:
                free_calls.append(uc.reg_read(UC_ARM_REG_R0))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        ret = uc.reg_read(UC_ARM_REG_R0)
        holder_val = struct.unpack("<I", uc.mem_read(0x00447060, 4))[0]
        return ret, holder_val, clean_calls, free_calls

    test_cases = [
        # (has_inst, check_ret, flag_byte)
        (False, 0, 0),        # no instance -> returns 0
        (True, 1, 1),         # check_ret != 0 -> returns 1
        (True, 0, 0),         # check_ret == 0, flag == 0 -> returns 1
        (True, 0, 1),         # ready to close: clean callback, free instance, holder = 0, returns 0
    ]

    for tc in test_cases:
        r1, h1, c1, f1 = run_one(orig, *tc)
        r2, h2, c2, f2 = run_one(staged, *tc)
        assert r1 == r2, f"Ret mismatch: orig={r1}, comp={r2} for {tc}"
        assert h1 == h2, f"Holder mismatch: orig={hex(h1)}, comp={hex(h2)} for {tc}"
        assert c1 == c2, f"Clean calls mismatch: orig={c1}, comp={c2} for {tc}"
        assert f1 == f2, f"Free calls mismatch: orig={f1}, comp={f2} for {tc}"
    print("ui_func_002b8adc: PASS")


def test_002be4dc():
    print("--- Testing func_002be4dc ---")
    addr = 0x002BE4DC
    size = 108
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_002be4dc", ROOT / "build")

    STUB_UI = 0x002AE2C4
    staged = stage_body(comp, relocs, addr, {
        "ui_func_002ae2c4": STUB_UI,
    })

    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, hex_color: int):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_UI, stub_code)

        captured_rgba = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_UI:
                ptr = uc.reg_read(UC_ARM_REG_R0)
                rgba = struct.unpack("<4f", uc.mem_read(ptr, 16))
                captured_rgba.append(tuple(round(x, 4) for x in rgba))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, hex_color)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        return captured_rgba

    test_cases = [
        0xFF000000, # Red
        0x00FF0000, # Green
        0x0000FF00, # Blue
        0x80402000, # Mixed
        0x00000000, # Black
        0xFFFFFFFF, # White
    ]

    for clr in test_cases:
        c1 = run_one(orig, clr)
        c2 = run_one(staged, clr)
        assert c1 == c2, f"RGBA mismatch: orig={c1}, comp={c2} for color={hex(clr)}"
    print("func_002be4dc: PASS")


def test_002c1570():
    print("--- Testing nn_sdk_func_002c1570 ---")
    addr = 0x002C1570
    size = 104
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("nn_sdk_func_002c1570", ROOT / "build")

    STUB_LOCK = 0x002C3AA8
    STUB_UNLOCK = 0x002C3A24
    STUB_INIT = 0x0011CD48

    staged = stage_body(comp, relocs, addr, {
        "engine_func_002c3aa8": STUB_LOCK,
        "engine_func_002c3a24": STUB_UNLOCK,
        "camp_func_0011cd48": STUB_INIT,
    })

    MUTEX_ADDR = 0x004E9BA8
    COUNTER_ADDR = 0x00471B90
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, initial_counter: int, init_mock_ret: int):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_LOCK, stub_code)
        uc.mem_write(STUB_UNLOCK, stub_code)
        uc.mem_write(STUB_INIT, stub_code)

        uc.mem_write(COUNTER_ADDR, struct.pack("<i", initial_counter))

        events = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_LOCK:
                events.append(("LOCK", uc.reg_read(UC_ARM_REG_R0)))
            elif address == STUB_UNLOCK:
                events.append(("UNLOCK", uc.reg_read(UC_ARM_REG_R0)))
            elif address == STUB_INIT:
                cfg = uc.reg_read(UC_ARM_REG_R0)
                events.append(("INIT", cfg))
                uc.reg_write(UC_ARM_REG_R0, init_mock_ret)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        ret = uc.reg_read(UC_ARM_REG_R0)
        final_counter = struct.unpack("<i", uc.mem_read(COUNTER_ADDR, 4))[0]
        return ret, final_counter, events

    test_cases = [
        # (initial_counter, init_mock_ret)
        (1, 0),         # counter > 0 -> increments counter to 2, returns 0x082067F9
        (5, 0),         # counter > 0 -> increments counter to 6, returns 0x082067F9
        (0, 0x1234),    # counter <= 0 -> calls init(0x0040B6E4), counter unchanged, returns 0x1234
        (-1, 0xABCD),   # counter <= 0 -> calls init, returns 0xABCD
    ]

    for tc in test_cases:
        r1, c1, e1 = run_one(orig, *tc)
        r2, c2, e2 = run_one(staged, *tc)
        assert r1 == r2, f"Ret mismatch: orig={hex(r1)}, comp={hex(r2)} for {tc}"
        assert c1 == c2, f"Counter mismatch: orig={c1}, comp={c2} for {tc}"
        assert e1 == e2, f"Events mismatch: orig={e1}, comp={e2} for {tc}"
    print("nn_sdk_func_002c1570: PASS")


def test_002c8630():
    print("--- Testing script_vm_func_002c8630 ---")
    addr = 0x002C8630
    size = 104
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_002c8630", ROOT / "build")

    STUB_SYNC = 0x002C2B1C
    STUB_FLAG = 0x002C0BA8

    staged = stage_body(comp, relocs, addr, {
        "engine_func_002c2b1c": STUB_SYNC,
        "script_vm_func_002c0ba8": STUB_FLAG,
    })

    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, id_val: int, flag_144: int, flag_15a: int):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_SYNC, stub_code)
        uc.mem_write(STUB_FLAG, stub_code)

        flag_queries = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_FLAG:
                fid = uc.reg_read(UC_ARM_REG_R0)
                flag_queries.append(fid)
                if fid == 0x144:
                    uc.reg_write(UC_ARM_REG_R0, flag_144)
                elif fid == 0x15A:
                    uc.reg_write(UC_ARM_REG_R0, flag_15a)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, id_val)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, flag_queries

    test_cases = [
        # (id, f144, f15a)
        (25, 1, 1),       # range 25..30, f144=1 -> 1
        (25, 0, 1),       # range 25..30, f144=0 -> 0
        (30, 1, 1),       # boundary 30, f144=1 -> 1
        (0x66, 0, 1),     # 0x66, f144=0 -> 0
        (31, 1, 1),       # range 31..35, f15a=1 -> 1
        (31, 1, 0),       # range 31..35, f15a=0 -> 0
        (35, 1, 0),       # boundary 35, f15a=0 -> 0
        (0x67, 1, 0),     # 0x67, f15a=0 -> 0
        (10, 0, 0),       # outside both ranges -> returns 1 without querying
        (100, 0, 0),      # outside both ranges -> returns 1
    ]

    for tc in test_cases:
        r1, q1 = run_one(orig, *tc)
        r2, q2 = run_one(staged, *tc)
        assert r1 == r2, f"Ret mismatch: orig={r1}, comp={r2} for {tc}"
        assert q1 == q2, f"Queries mismatch: orig={q1}, comp={q2} for {tc}"
    print("script_vm_func_002c8630: PASS")


def test_002c9b3c():
    print("--- Testing script_vm_func_002c9b3c ---")
    addr = 0x002C9B3C
    size = 104
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_002c9b3c", ROOT / "build")

    STUB_TABLE = 0x002C0EC4
    STUB_PAYLOAD = 0x002C0E9C
    STUB_COUNT = 0x002C0E4C

    staged = stage_body(comp, relocs, addr, {
        "Tbb_GetGlobalSubTable": STUB_TABLE,
        "Tbb_GetPayloadData": STUB_PAYLOAD,
        "Tbb_GetRowCount": STUB_COUNT,
    })

    STATIC_BASE = 0x20010000
    DYN_MGR = 0x20020000
    DYN_BASE = 0x20030000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, id_val: int, static_count: int, dyn_count: int):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_TABLE, stub_code)
        uc.mem_write(STUB_PAYLOAD, stub_code)
        uc.mem_write(STUB_COUNT, stub_code)

        uc.mem_write(0x00433158, struct.pack("<I", DYN_MGR))
        uc.mem_write(DYN_MGR + 0x3FC, struct.pack("<II", dyn_count, DYN_BASE))

        def code_hook(uc, address, sz, user_data):
            if address == STUB_TABLE:
                uc.reg_write(UC_ARM_REG_R0, 0x1234) # table handle
            elif address == STUB_PAYLOAD:
                uc.reg_write(UC_ARM_REG_R0, STATIC_BASE)
            elif address == STUB_COUNT:
                uc.reg_write(UC_ARM_REG_R0, static_count)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, id_val)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret

    test_cases = [
        # (id, static_count, dyn_count)
        (0, 10, 5),      # static slot 0 -> STATIC_BASE + 0
        (5, 10, 5),      # static slot 5 -> STATIC_BASE + 100
        (9, 10, 5),      # static slot 9 -> STATIC_BASE + 180
        (10, 10, 5),     # dyn slot 0 (id 10) -> DYN_BASE + 0
        (12, 10, 5),     # dyn slot 2 (id 12) -> DYN_BASE + 40
        (14, 10, 5),     # dyn slot 4 (id 14) -> DYN_BASE + 80
        (15, 10, 5),     # out of bounds (id >= 15) -> 0
        (100, 10, 5),    # out of bounds -> 0
    ]

    for tc in test_cases:
        r1 = run_one(orig, *tc)
        r2 = run_one(staged, *tc)
        assert r1 == r2, f"Ret mismatch: orig={hex(r1)}, comp={hex(r2)} for {tc}"
    print("script_vm_func_002c9b3c: PASS")


def main():
    test_002b8adc()
    test_002be4dc()
    test_002c1570()
    test_002c8630()
    test_002c9b3c()
    print("\nALL 5 FUNCTIONS IN BATCH 30 B PART 15 PASSED WITH 100% DIFFERENTIAL FIDELITY!")

if __name__ == "__main__":
    main()
