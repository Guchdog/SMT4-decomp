#!/usr/bin/env python3
"""Differential test for batch 30 B part 13:
- camp_func_0029c084 (0x0029C084, 120 B)
- AsdMdlManager_func_002a135c (0x002A135C, 116 B)
- func_002a4588 (0x002A4588, 120 B)
- func_002a7fd8 (0x002A7FD8, 100 B)
- func_002a8674 (0x002A8674, 112 B)
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


def test_0029c084():
    print("--- Testing camp_func_0029c084 ---")
    addr = 0x0029C084
    size = 120
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("camp_func_0029c084", ROOT / "build")
    staged = stage_body(comp, relocs, addr, {})

    SRC_ADDR = 0x20001000
    CAMP_BASE = 0x20010000

    def run_one(c_bytes, ids, initial_bitmap):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # 0x0043E2AC contains pointer to camp state
        uc.mem_write(0x0043E2A8, struct.pack("<II", 0, CAMP_BASE))

        # Setup source buffer
        src_buf = bytearray(0x50)
        for i, val in enumerate(ids):
            struct.pack_into("<h", src_buf, 0x34 + i * 2, val)
        uc.mem_write(SRC_ADDR, bytes(src_buf))

        # Setup bitmap area in camp state (at CAMP_BASE + 0x24BC4)
        bitmap_addr = CAMP_BASE + 0x24BC4
        # Ensure pages are mapped
        for offset in range(0, 0x26000, 0x1000):
            try:
                uc.mem_map(CAMP_BASE + offset, 0x1000)
            except Exception:
                pass
        uc.mem_write(bitmap_addr, bytes(initial_bitmap))

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, SRC_ADDR)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=1000)

        out_bitmap = bytes(uc.mem_read(bitmap_addr, len(initial_bitmap)))
        return out_bitmap

    test_cases = [
        # (ids, initial_bitmap)
        ([1, 2, 7, 8, 9, 250, 499, 500], bytearray(70)),
        ([0, -1, 501, 1000, -50, 0, 0, 0], bytearray(70)),
        ([5, 0, 16, 501, 33, -1, 480, 2], bytearray([0xFF] * 70)),
        ([1, 1, 1, 1, 1, 1, 1, 1], bytearray(70)),
        ([8, 16, 24, 32, 40, 48, 56, 64], bytearray([0x55] * 70)),
    ]

    for ids, init_bm in test_cases:
        b1 = run_one(orig, ids, init_bm)
        b2 = run_one(staged, ids, init_bm)
        assert b1 == b2, f"Bitmap mismatch for ids={ids}"
    print("camp_func_0029c084: PASS")


def test_002a135c():
    print("--- Testing AsdMdlManager_func_002a135c ---")
    addr = 0x002A135C
    size = 116
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("AsdMdlManager_func_002a135c", ROOT / "build")

    STUB_ALLOC = 0x002C54F0
    STUB_MODEL = 0x001FE470
    staged = stage_body(comp, relocs, addr, {
        "engine_func_002c54f0": STUB_ALLOC,
        "AsdModel_func_001fe470": STUB_MODEL,
    })

    NODE_ADDR = 0x20010000
    SUB_PTR = 0x20020000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_ALLOC, stub_code)
        uc.mem_write(STUB_MODEL, stub_code)

        # Initialize node memory with non-zero garbage
        uc.mem_write(NODE_ADDR, b"\xAA" * 0x30)

        alloc_calls = []
        model_calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_ALLOC:
                a = uc.reg_read(UC_ARM_REG_R0)
                b = uc.reg_read(UC_ARM_REG_R1)
                c = uc.reg_read(UC_ARM_REG_R2)
                d = uc.reg_read(UC_ARM_REG_R3)
                sp = uc.reg_read(UC_ARM_REG_SP)
                e = struct.unpack("<I", uc.mem_read(sp, 4))[0]
                alloc_calls.append((a, b, c, d, e))
                uc.reg_write(UC_ARM_REG_R0, NODE_ADDR)
            elif address == STUB_MODEL:
                model_calls.append(True)
                uc.reg_write(UC_ARM_REG_R0, SUB_PTR)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        ret = uc.reg_read(UC_ARM_REG_R0)
        node_mem = bytes(uc.mem_read(NODE_ADDR, 0x1C))
        return ret, alloc_calls, model_calls, node_mem

    r1, a1, m1, mem1 = run_one(orig)
    r2, a2, m2, mem2 = run_one(staged)

    assert r1 == r2, f"Ret mismatch: orig={hex(r1)}, comp={hex(r2)}"
    assert a1 == a2, f"Alloc calls mismatch: orig={a1}, comp={a2}"
    assert m1 == m2, f"Model calls mismatch: orig={m1}, comp={m2}"
    assert mem1 == mem2, f"Node memory mismatch:\norig={mem1.hex()}\ncomp={mem2.hex()}"
    print("AsdMdlManager_func_002a135c: PASS")


def test_002a4588():
    print("--- Testing func_002a4588 ---")
    addr = 0x002A4588
    size = 120
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_002a4588", ROOT / "build")

    STUB_NOTIF = 0x002A8898
    staged = stage_body(comp, relocs, addr, {
        "engine_func_002a8898": STUB_NOTIF,
    })

    OBJ_ADDR = 0x20010000
    ARBITER_ADDR = 0x20050000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, cur_val, flag_val, max_cap, delta):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_NOTIF, stub_code)

        uc.mem_write(0x00471B58, struct.pack("<I", ARBITER_ADDR))

        uc.mem_write(OBJ_ADDR, struct.pack("<ihh", cur_val, flag_val, max_cap))

        notif_calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_NOTIF:
                arb = uc.reg_read(UC_ARM_REG_R0)
                obj = uc.reg_read(UC_ARM_REG_R1)
                op = uc.reg_read(UC_ARM_REG_R2)
                cnt = uc.reg_read(UC_ARM_REG_R3)
                sp = uc.reg_read(UC_ARM_REG_SP)
                t_lo, t_hi = struct.unpack("<II", uc.mem_read(sp, 8))
                notif_calls.append((arb, obj, op, cnt, t_lo, t_hi))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, OBJ_ADDR)
        uc.reg_write(UC_ARM_REG_R1, delta)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        ret = uc.reg_read(UC_ARM_REG_R0)
        new_cur = struct.unpack("<i", uc.mem_read(OBJ_ADDR, 4))[0]
        return ret, new_cur, notif_calls

    test_cases = [
        # (cur, flag, max, delta)
        (5, 0, 10, 2),    # cur + delta <= max (7), old > 0, flag <= 0 -> no notif
        (5, 0, 10, 8),    # cur + delta > max (clamped to 10), old > 0, flag <= 0 -> no notif
        (0, 0, 10, 3),    # old == 0 -> notify
        (-2, 0, 10, 5),   # old < 0 -> notify
        (5, 1, 10, 2),    # old > 0, flag > 0 -> notify
        (10, 2, 10, 0),   # cur == max, flag > 0 -> notify
        (8, -1, 10, -3),  # delta negative, flag <= 0 -> no notif
    ]

    for tc in test_cases:
        r1, c1, n1 = run_one(orig, *tc)
        r2, c2, n2 = run_one(staged, *tc)
        assert r1 == r2, f"Ret mismatch: orig={r1}, comp={r2} for {tc}"
        assert c1 == c2, f"Cur mismatch: orig={c1}, comp={c2} for {tc}"
        assert n1 == n2, f"Notif mismatch: orig={n1}, comp={n2} for {tc}"
    print("func_002a4588: PASS")


def test_002a7fd8():
    print("--- Testing func_002a7fd8 ---")
    addr = 0x002A7FD8
    size = 100
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_002a7fd8", ROOT / "build")
    staged = stage_body(comp, relocs, addr, {})

    def run_one(c_bytes, a: float, b: float):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", a))[0])
        uc.reg_write(UC_ARM_REG_S1, struct.unpack("<I", struct.pack("<f", b))[0])
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret

    test_cases = [
        (1.0, 1.0),
        (0.0, 0.0),
        (-5.5, -5.5),
        (1.0, 1.0 + 1e-7),
        (1.0, 1.0 + 2e-7),
        (100.0, 100.0 + 1e-5),
        (100.0, 101.0),
        (0.0, 1.0),
        (-10.0, 10.0),
        (1e-6, 1.1e-6),
    ]

    for a, b in test_cases:
        r1 = run_one(orig, a, b)
        r2 = run_one(staged, a, b)
        assert r1 == r2, f"Ret mismatch: orig={r1}, comp={r2} for a={a}, b={b}"
    print("func_002a7fd8: PASS")


def test_002a8674():
    print("--- Testing func_002a8674 ---")
    addr = 0x002A8674
    size = 112
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_002a8674", ROOT / "build")

    STUB_CHECK = 0x002BB5B4
    staged = stage_body(comp, relocs, addr, {
        "func_002bb5b4": STUB_CHECK,
    })

    TABLE_BASE = 0x0000131E
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    TARGET_NODE = 0x20010000

    def run_one(c_bytes, check_res, id_val, mode_val, float_val, initial_flags):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_CHECK, stub_code)

        def code_hook(uc, address, sz, user_data):
            if address == STUB_CHECK:
                uc.reg_write(UC_ARM_REG_R0, check_res)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        # Setup table at 0x0000131E
        # Map 0x00000000 page
        try:
            uc.mem_map(0, 0x10000)
        except Exception:
            pass

        offset_val = 0x40
        uc.mem_write(TABLE_BASE + id_val, struct.pack("<H", offset_val))

        entry_addr = id_val + (offset_val << 2) + 0x1000
        # Map page for entry if needed
        entry_page = entry_addr & ~0xFFF
        try:
            uc.mem_map(entry_page, 0x1000)
        except Exception:
            pass

        uc.mem_write(entry_addr + 0xA0, struct.pack("<I", TARGET_NODE))

        # Setup target node
        node_buf = bytearray(0x40)
        struct.pack_into("<I", node_buf, 0, initial_flags)
        uc.mem_write(TARGET_NODE, bytes(node_buf))

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, id_val)
        uc.reg_write(UC_ARM_REG_R1, mode_val)
        uc.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", float_val))[0])
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        out_node = bytes(uc.mem_read(TARGET_NODE, 0x40))
        return out_node

    test_cases = [
        # (check, id, mode, float_val, init_flags)
        (0, 0, 0, 1.5, 0),         # check fails -> no write
        (1, 0, 0, 2.5, 0),         # mode 0 -> sets 0x01000000, float at +8
        (1, 2, 1, 3.5, 0),         # mode 1 -> sets 0x02000000, float at +12
        (1, 4, 2, 4.5, 0x1234),    # mode 2 -> leaves flags, float at +16
        (1, 0, 0, -1.0, 0x02000000), # mode 0 -> orrs 0x01000000 with existing
    ]

    for tc in test_cases:
        m1 = run_one(orig, *tc)
        m2 = run_one(staged, *tc)
        assert m1 == m2, f"Node mismatch for {tc}:\norig={m1.hex()}\ncomp={m2.hex()}"
    print("func_002a8674: PASS")


def main():
    test_0029c084()
    test_002a135c()
    test_002a4588()
    test_002a7fd8()
    test_002a8674()
    print("\nALL 5 FUNCTIONS IN BATCH 30 B PART 13 PASSED WITH 100% DIFFERENTIAL FIDELITY!")

if __name__ == "__main__":
    main()
