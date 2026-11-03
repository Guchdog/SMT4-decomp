#!/usr/bin/env python3
"""Differential test for batch 30 B part 14:
- func_002a8cfc (0x002A8CFC, 108 B)
- func_002aa48c (0x002AA48C, 120 B)
- func_002ad714 (0x002AD714, 112 B)
- AsdList_func_002b2814 (0x002B2814, 120 B)
- func_002b4ddc (0x002B4DDC, 104 B)
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


def test_002a8cfc():
    print("--- Testing func_002a8cfc ---")
    addr = 0x002A8CFC
    size = 108
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_002a8cfc", ROOT / "build")

    STUB_E80 = 0x0014E804
    STUB_FFF = 0x002BFFF8
    STUB_71F = 0x002B71F8
    STUB_943 = 0x002B9438

    staged = stage_body(comp, relocs, addr, {
        "func_0014e804": STUB_E80,
        "func_002bfff8": STUB_FFF,
        "script_vm_func_002b71f8": STUB_71F,
        "engine_func_002b9438": STUB_943,
    })

    GLOBAL_SRC = 0x20050000
    DEST_BUF = 0x20060000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    sample_matrix = [float(i + 1) * 1.5 for i in range(16)]
    matrix_bytes = struct.pack("<16f", *sample_matrix)

    def run_one(c_bytes, pass_dest: bool):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_E80, stub_code)
        uc.mem_write(STUB_FFF, stub_code)
        uc.mem_write(STUB_71F, stub_code)
        uc.mem_write(STUB_943, stub_code)

        uc.mem_write(0x0044EA00, struct.pack("<I", GLOBAL_SRC))
        if pass_dest:
            uc.mem_write(DEST_BUF, b"\x00" * 64)

        calls_seq = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_E80:
                calls_seq.append(("E80",))
            elif address == STUB_FFF:
                buf = uc.reg_read(UC_ARM_REG_R0)
                src = uc.reg_read(UC_ARM_REG_R1)
                calls_seq.append(("FFF", src))
                # simulate populating matrix
                uc.mem_write(buf, matrix_bytes)
            elif address == STUB_71F:
                calls_seq.append(("71F",))
            elif address == STUB_943:
                src = uc.reg_read(UC_ARM_REG_R0)
                calls_seq.append(("943", src))
                uc.reg_write(UC_ARM_REG_R0, 0x12345678)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, DEST_BUF if pass_dest else 0)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        ret = uc.reg_read(UC_ARM_REG_R0)
        out_dest = bytes(uc.mem_read(DEST_BUF, 64)) if pass_dest else b""
        return ret, calls_seq, out_dest

    for pass_dst in [True, False]:
        r1, c1, d1 = run_one(orig, pass_dst)
        r2, c2, d2 = run_one(staged, pass_dst)
        assert r1 == r2, f"Ret mismatch: orig={hex(r1)}, comp={hex(r2)}"
        assert c1 == c2, f"Calls mismatch: orig={c1}, comp={c2}"
        assert d1 == d2, f"Dest matrix mismatch:\norig={d1.hex()}\ncomp={d2.hex()}"
    print("func_002a8cfc: PASS")


def test_002aa48c():
    print("--- Testing func_002aa48c ---")
    addr = 0x002AA48C
    size = 120
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_002aa48c", ROOT / "build")

    STUB_E76 = 0x0014E760
    STUB_UI = 0x001456D0
    staged = stage_body(comp, relocs, addr, {
        "func_0014e760": STUB_E76,
        "ui_func_001456d0": STUB_UI,
    })

    NODE_ADDR = 0x20010000
    TABLE_BASE = 0x000011E8
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, id_val, table_flag, slot_node_matches, pass_null_node, initial_cur_mode, target_mode):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_E76, stub_code)
        uc.mem_write(STUB_UI, stub_code)

        try:
            uc.mem_map(0, 0x10000)
        except Exception:
            pass

        uc.mem_write(TABLE_BASE + id_val, struct.pack("<B", table_flag))

        base = id_val + 0x1000
        page = base & ~0xFFF
        try:
            uc.mem_map(page, 0x2000)
        except Exception:
            pass

        existing_node = NODE_ADDR if slot_node_matches else 0x20020000
        passed_node = 0 if pass_null_node else NODE_ADDR
        uc.mem_write(base + 0x1E4, struct.pack("<I", existing_node))
        uc.mem_write(base + 0x1E8, struct.pack("<BB", 0xFF, initial_cur_mode))

        # Setup node fields
        node_buf = bytearray(0x40)
        struct.pack_into("<II", node_buf, 0x14, 0x11111111, 0x22222222)
        struct.pack_into("<II", node_buf, 0x30, 0x44444444, 0x33333333) # 0x34 is 0x33333333
        uc.mem_write(NODE_ADDR, bytes(node_buf))

        e76_calls = []
        ui_calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_E76:
                a = uc.reg_read(UC_ARM_REG_R0)
                b = uc.reg_read(UC_ARM_REG_R1)
                c = uc.reg_read(UC_ARM_REG_R2)
                d = uc.reg_read(UC_ARM_REG_R3)
                e76_calls.append((a, b, c, d))
            elif address == STUB_UI:
                ui_calls.append(uc.reg_read(UC_ARM_REG_R0))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, id_val)
        uc.reg_write(UC_ARM_REG_R1, passed_node)
        uc.reg_write(UC_ARM_REG_R2, target_mode)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        slot = struct.unpack("<I", uc.mem_read(base + 0x1E4, 4))[0]
        f1e8, f1e9 = struct.unpack("<BB", uc.mem_read(base + 0x1E8, 2))
        return slot, f1e8, f1e9, e76_calls, ui_calls

    test_cases = [
        # (id, flag, slot_match, pass_null, init_mode, target_mode)
        (0, 0, True, False, 1, 1),      # flag 0 & slot matches -> skips e76, target_mode == init -> skips ui
        (4, 0, False, False, 1, 2),     # flag 0 & slot mismatch -> updates slot, calls e76, sets mode 3, then mode 3 != 2 -> calls ui(2), sets 2
        (4, 1, True, False, 3, 3),      # flag != 0 -> updates slot, calls e76, mode 3 == 3 -> skips ui
        (8, 1, True, True, 0, 5),       # flag != 0, pass NULL -> updates slot = 0, skips e76, mode 0 != 5 -> calls ui(5)
    ]

    for tc in test_cases:
        s1, e1_8, e1_9, c1_76, u1 = run_one(orig, *tc)
        s2, e2_8, e2_9, c2_76, u2 = run_one(staged, *tc)
        assert s1 == s2, f"Slot mismatch: orig={hex(s1)}, comp={hex(s2)} for {tc}"
        assert (e1_8, e1_9) == (e2_8, e2_9), f"Flags mismatch: orig=({e1_8}, {e1_9}), comp=({e2_8}, {e2_9}) for {tc}"
        assert c1_76 == c2_76, f"E76 calls mismatch: orig={c1_76}, comp={c2_76} for {tc}"
        assert u1 == u2, f"UI calls mismatch: orig={u1}, comp={u2} for {tc}"
    print("func_002aa48c: PASS")


def test_002ad714():
    print("--- Testing func_002ad714 ---")
    addr = 0x002AD714
    size = 112
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_002ad714", ROOT / "build")

    STUB_DAYS = 0x002A8730
    staged = stage_body(comp, relocs, addr, {
        "script_vm_func_002a8730": STUB_DAYS,
    })

    OUT_ADDR = 0x20010000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, year, month, day, hour, minute, second, ms, mock_days):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_DAYS, stub_code)

        uc.mem_write(OUT_ADDR, b"\x00" * 8)

        def code_hook(uc, address, sz, user_data):
            if address == STUB_DAYS:
                uc.reg_write(UC_ARM_REG_R0, mock_days)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        # Push stack arguments: hour, minute, second, ms
        stack_args = struct.pack("<iiii", hour, minute, second, ms)
        uc.mem_write(sp, stack_args)

        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, OUT_ADDR)
        uc.reg_write(UC_ARM_REG_R1, year)
        uc.reg_write(UC_ARM_REG_R2, month)
        uc.reg_write(UC_ARM_REG_R3, day)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        out_ms = struct.unpack("<q", uc.mem_read(OUT_ADDR, 8))[0]
        return out_ms

    test_cases = [
        # (year, month, day, hour, minute, second, ms, mock_days)
        (2020, 1, 1, 0, 0, 0, 0, 7300),
        (2023, 6, 15, 12, 30, 45, 500, 8500),
        (2000, 1, 1, 23, 59, 59, 999, 0),
        (1990, 5, 20, 1, 2, 3, 4, -3650),
    ]

    for tc in test_cases:
        m1 = run_one(orig, *tc)
        m2 = run_one(staged, *tc)
        assert m1 == m2, f"Milliseconds mismatch: orig={m1}, comp={m2} for {tc}"
    print("func_002ad714: PASS")


def test_002b2814():
    print("--- Testing AsdList_func_002b2814 ---")
    addr = 0x002B2814
    size = 120
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("AsdList_func_002b2814", ROOT / "build")

    STUB_ALLOC = 0x002C54F0
    STUB_ADD = 0x0014E648
    staged = stage_body(comp, relocs, addr, {
        "engine_func_002c54f0": STUB_ALLOC,
        "engine_func_0014e648": STUB_ADD,
    })

    LIST_ADDR = 0x20010000
    ITEM_ADDR = 0x20020000
    NODE_ADDR = 0x20030000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, extra_val):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_ALLOC, stub_code)
        uc.mem_write(STUB_ADD, stub_code)

        uc.mem_write(NODE_ADDR, b"\xFF" * 0x20)

        add_calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_ALLOC:
                uc.reg_write(UC_ARM_REG_R0, NODE_ADDR)
            elif address == STUB_ADD:
                lst = uc.reg_read(UC_ARM_REG_R0)
                node = uc.reg_read(UC_ARM_REG_R1)
                idx = uc.reg_read(UC_ARM_REG_R2)
                add_calls.append((lst, node, idx))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, LIST_ADDR)
        uc.reg_write(UC_ARM_REG_R1, ITEM_ADDR)
        uc.reg_write(UC_ARM_REG_R2, extra_val)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        ret = uc.reg_read(UC_ARM_REG_R0)
        node_mem = bytes(uc.mem_read(NODE_ADDR, 0x1C))
        return ret, add_calls, node_mem

    test_cases = [0, 0x12345678, 0xFFFFFFFF]

    for ex in test_cases:
        r1, a1, m1 = run_one(orig, ex)
        r2, a2, m2 = run_one(staged, ex)
        assert r1 == r2, f"Ret mismatch: orig={hex(r1)}, comp={hex(r2)}"
        assert a1 == a2, f"Add calls mismatch: orig={a1}, comp={a2}"
        assert m1 == m2, f"Node memory mismatch for extra={hex(ex)}:\norig={m1.hex()}\ncomp={m2.hex()}"
    print("AsdList_func_002b2814: PASS")


def test_002b4ddc():
    print("--- Testing func_002b4ddc ---")
    addr = 0x002B4DDC
    size = 104
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_002b4ddc", ROOT / "build")

    STUB_ELEM_FREE = 0x002BD620
    STUB_MGR_GET = 0x002BB270
    STUB_UNREG = 0x0015C6BC

    staged = stage_body(comp, relocs, addr, {
        "func_002bd620": STUB_ELEM_FREE,
        "engine_func_002bb270": STUB_MGR_GET,
        "func_0015c6bc": STUB_UNREG,
    })

    OBJ_ADDR = 0x20010000
    MGR_ADDR = 0x20050000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, is_active: bool, elements: list[int]):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_ELEM_FREE, stub_code)
        uc.mem_write(STUB_MGR_GET, stub_code)
        uc.mem_write(STUB_UNREG, stub_code)

        obj_buf = bytearray(0x20)
        struct.pack_into("<I", obj_buf, 0x08, len(elements))
        struct.pack_into("<B", obj_buf, 0x14, 1 if is_active else 0)
        for i, elem in enumerate(elements):
            struct.pack_into("<I", obj_buf, i * 4, elem)
        uc.mem_write(OBJ_ADDR, bytes(obj_buf))

        freed_elems = []
        unreg_calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_ELEM_FREE:
                freed_elems.append(uc.reg_read(UC_ARM_REG_R0))
            elif address == STUB_MGR_GET:
                uc.reg_write(UC_ARM_REG_R0, MGR_ADDR)
            elif address == STUB_UNREG:
                mgr = uc.reg_read(UC_ARM_REG_R0)
                obj = uc.reg_read(UC_ARM_REG_R1)
                unreg_calls.append((mgr, obj))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, OBJ_ADDR)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        out_obj = bytes(uc.mem_read(OBJ_ADDR, 0x20))
        return freed_elems, unreg_calls, out_obj

    test_cases = [
        # (is_active, elements)
        (False, [0x1111, 0x2222]),                # inactive -> no-op
        (True, []),                               # active, 0 elements -> unregisters
        (True, [0x1111, 0x2222]),                 # active, 2 elements -> frees both, zeroes, unregisters
        (True, [0x1111, 0]),                      # active, 1 null element -> skips free on null
        (True, [0, 0]),                           # active, 2 null elements
    ]

    for is_act, elems in test_cases:
        f1, u1, o1 = run_one(orig, is_act, elems)
        f2, u2, o2 = run_one(staged, is_act, elems)
        assert f1 == f2, f"Freed mismatch: orig={f1}, comp={f2} for is_act={is_act}, elems={elems}"
        assert u1 == u2, f"Unreg mismatch: orig={u1}, comp={u2} for is_act={is_act}, elems={elems}"
        assert o1 == o2, f"Obj mem mismatch for is_act={is_act}, elems={elems}:\norig={o1.hex()}\ncomp={o2.hex()}"
    print("func_002b4ddc: PASS")


def main():
    test_002a8cfc()
    test_002aa48c()
    test_002ad714()
    test_002b2814()
    test_002b4ddc()
    print("\nALL 5 FUNCTIONS IN BATCH 30 B PART 14 PASSED WITH 100% DIFFERENTIAL FIDELITY!")

if __name__ == "__main__":
    main()
