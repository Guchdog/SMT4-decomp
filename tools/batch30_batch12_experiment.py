#!/usr/bin/env python3
"""Differential test for batch 30 part 12:
- ui_func_0024baf4 (0x0024BAF4, 140 B)
- engine_func_0024c3f8 (0x0024C3F8, 148 B)
- engine_func_0024fd10 (0x0024FD10, 148 B)
- script_vm_func_002642d0 (0x002642D0, 152 B)
- ui_func_0026b734 (0x0026B734, 152 B)
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

def test_0024baf4():
    print("--- Testing ui_func_0024baf4 ---")
    addr = 0x0024BAF4
    size = 140
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_0024baf4", ROOT / "build")
    symbol_map = {
        "func_00293c98": 0x00293C98,
        "ui_func_0024bb80": 0x0024BB80,
        "func_0028686c": 0x0028686C,
        "func_00296f60": 0x00296F60,
        "func_00289640": 0x00289640,
        "func_00286928": 0x00286928,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    CTX_ADDR = 0x20001000
    OBJ_ADDR = 0x20002000

    def run_one(c_bytes, r4_val):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # 0x0043E188 + 0x0C -> pointer to OBJ_ADDR
        uc.mem_write(0x0043E188 + 0x0C, struct.pack("<I", OBJ_ADDR))
        uc.mem_write(OBJ_ADDR + 0x24, b"\x00\x00\x00\x00")

        # CTX_ADDR + 0x2234 -> r4_val
        uc.mem_write(CTX_ADDR + 0x2234, struct.pack("<I", r4_val))

        calls = []

        def make_stub(target, handler):
            uc.mem_write(target, b"\x1e\xff\x2f\xe1") # bx lr
            def hook(uc_inst, address, size, user_data):
                handler(uc_inst)
            uc.hook_add(UC_HOOK_CODE, hook, None, target, target)

        def on_293c98(u):
            calls.append("293c98")
            u.reg_write(UC_ARM_REG_R0, CTX_ADDR)
        make_stub(0x00293C98, on_293c98)

        def on_24bb80(u):
            calls.append("24bb80")
            u.reg_write(UC_ARM_REG_R0, 0x12345678)
        make_stub(0x0024BB80, on_24bb80)

        def on_28686c(u):
            calls.append("28686c")
            u.reg_write(UC_ARM_REG_R0, 0x55555555)
        make_stub(0x0028686C, on_28686c)

        def on_296f60(u):
            arg0 = u.reg_write(UC_ARM_REG_R0, 0x77777777)
            calls.append(("296f60", u.reg_read(UC_ARM_REG_R0)))
            u.reg_write(UC_ARM_REG_R0, 0x77777777)
        make_stub(0x00296F60, on_296f60)

        def on_289640(u):
            calls.append("289640")
            u.reg_write(UC_ARM_REG_R0, 0x88888888)
        make_stub(0x00289640, on_289640)

        def on_286928(u):
            sp = u.reg_read(UC_ARM_REG_SP)
            sp0, sp4 = struct.unpack("<II", u.mem_read(sp, 8))
            calls.append((
                "286928",
                u.reg_read(UC_ARM_REG_R0),
                u.reg_read(UC_ARM_REG_R1),
                u.reg_read(UC_ARM_REG_R2),
                u.reg_read(UC_ARM_REG_R3),
                sp0, sp4
            ))
        make_stub(0x00286928, on_286928)

        sp = STACK_BASE + STACK_SIZE - 0x100
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00100000)
        uc.reg_write(UC_ARM_REG_R4, 0xAAAAAAAA)
        uc.reg_write(UC_ARM_REG_R5, 0xBBBBBBBB)

        uc.emu_start(addr, 0x00100000, timeout=200000)

        obj_24 = struct.unpack("<I", uc.mem_read(OBJ_ADDR + 0x24, 4))[0]
        return {
            "obj_24": obj_24,
            "calls": calls,
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
        }

    for r4_input in (0x11111111, 0):
        o = run_one(orig, r4_input)
        c = run_one(staged, r4_input)
        assert o == c, f"0024baf4 mismatch for r4={r4_input}: {o} vs {c}"
    print("ui_func_0024baf4: PASS")

def test_0024c3f8():
    print("--- Testing engine_func_0024c3f8 ---")
    addr = 0x0024C3F8
    size = 148
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_0024c3f8", ROOT / "build")
    symbol_map = {
        "func_002b0188": 0x002B0188,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    OBJ_ADDR = 0x20001000
    R3_ADDR = 0x20002000
    TABLE_ADDR = 0x20003000
    SUB_ADDR = 0x20005000
    OUT1_ADDR = 0x20006000
    OUT2_ADDR = 0x20006004

    def run_one(c_bytes, index, has_sub, sub_type, sub_flag, use_out1, use_out2):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # func_002b0188 returns OBJ_ADDR
        uc.mem_write(0x002B0188, b"\x1e\xff\x2f\xe1")
        def on_2b0188(u, address, size, user_data):
            u.reg_write(UC_ARM_REG_R0, OBJ_ADDR)
        uc.hook_add(UC_HOOK_CODE, on_2b0188, None, 0x002B0188, 0x002B0188)

        # OBJ_ADDR + 4 -> R3_ADDR
        uc.mem_write(OBJ_ADDR + 4, struct.pack("<I", R3_ADDR))
        # R3_ADDR -> TABLE_ADDR
        uc.mem_write(R3_ADDR, struct.pack("<I", TABLE_ADDR))

        # Fill table entry at rem = index % 1000
        rem = index % 1000
        entry = TABLE_ADDR + rem * 20
        # entry + 4: u16 val1, entry + 6: u16 val2, entry + 0xC: sub_ptr
        sub_ptr = SUB_ADDR if has_sub else 0
        uc.mem_write(entry, b"\x00" * 20)
        uc.mem_write(entry + 4, struct.pack("<HH", 0x8123, 0x8456)) # with bit 0x8000 set
        uc.mem_write(entry + 0x0C, struct.pack("<I", sub_ptr))

        if has_sub:
            # sub: s16 at 0, s16 at 2, u16 type at 4, u8 flag at 0xC
            uc.mem_write(SUB_ADDR, struct.pack("<hhH", -1234, -5678, sub_type))
            uc.mem_write(SUB_ADDR + 0x0C, bytes([sub_flag]))

        p_out1 = OUT1_ADDR if use_out1 else 0
        p_out2 = OUT2_ADDR if use_out2 else 0

        uc.mem_write(OUT1_ADDR, struct.pack("<I", 0xDEADBEEF))
        uc.mem_write(OUT2_ADDR, struct.pack("<I", 0xCAFEBABE))

        sp = STACK_BASE + STACK_SIZE - 0x100
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00100000)
        uc.reg_write(UC_ARM_REG_R0, 0x11111111)
        uc.reg_write(UC_ARM_REG_R1, index)
        uc.reg_write(UC_ARM_REG_R2, p_out1)
        uc.reg_write(UC_ARM_REG_R3, p_out2)
        uc.reg_write(UC_ARM_REG_R4, 0xAAAAAAAA)
        uc.reg_write(UC_ARM_REG_R5, 0xBBBBBBBB)
        uc.reg_write(UC_ARM_REG_R6, 0xCCCCCCCC)

        uc.emu_start(addr, 0x00100000, timeout=200000)

        o1 = struct.unpack("<i", uc.mem_read(OUT1_ADDR, 4))[0]
        o2 = struct.unpack("<i", uc.mem_read(OUT2_ADDR, 4))[0]
        return {
            "o1": o1,
            "o2": o2,
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
        }

    cases = [
        (0, False, 0, 0, True, True),
        (555, False, 0, 0, True, True),
        (1555, True, 1, 0, True, True),       # sub_type == 1 -> override
        (2555, True, 2, 1, True, True),       # sub_flag & 1 != 0 -> override
        (3555, True, 2, 0, True, True),       # sub_flag & 1 == 0 -> fallback to entry
        (4555, True, 1, 0, False, True),      # out1 is null
        (5555, True, 1, 0, True, False),      # out2 is null
    ]

    for c_tuple in cases:
        o = run_one(orig, *c_tuple)
        c = run_one(staged, *c_tuple)
        assert o == c, f"0024c3f8 mismatch for {c_tuple}: {o} vs {c}"
    print("engine_func_0024c3f8: PASS")

def test_0024fd10():
    print("--- Testing engine_func_0024fd10 ---")
    addr = 0x0024FD10
    size = 148
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_0024fd10", ROOT / "build")
    symbol_map = {
        "engine_func_002c34a4": 0x002C34A4,
        "engine_func_002c3b48": 0x002C3B48,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    NODE_ADDR = 0x20005000
    INPUT_ADDR = 0x20001000

    def run_one(c_bytes, r2, r1, b8):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Setup stubs
        calls = []
        uc.mem_write(0x002C34A4, b"\x1e\xff\x2f\xe1")
        def on_alloc(u, a, s, ud):
            sp = u.reg_read(UC_ARM_REG_SP)
            sp0, sp4 = struct.unpack("<II", u.mem_read(sp, 8))
            calls.append((
                "alloc",
                u.reg_read(UC_ARM_REG_R0),
                u.reg_read(UC_ARM_REG_R1),
                u.reg_read(UC_ARM_REG_R2),
                u.reg_read(UC_ARM_REG_R3),
                sp0, sp4
            ))
            u.reg_write(UC_ARM_REG_R0, NODE_ADDR)
        uc.hook_add(UC_HOOK_CODE, on_alloc, None, 0x002C34A4, 0x002C34A4)

        uc.mem_write(0x002C3B48, b"\x1e\xff\x2f\xe1")
        def on_zero(u, a, s, ud):
            calls.append((
                "zero",
                u.reg_read(UC_ARM_REG_R0),
                u.reg_read(UC_ARM_REG_R1)
            ))
            u.mem_write(NODE_ADDR, b"\x00" * 0x38)
        uc.hook_add(UC_HOOK_CODE, on_zero, None, 0x002C3B48, 0x002C3B48)

        # Write input struct
        uc.mem_write(INPUT_ADDR, b"\x00" * 0xC0)
        uc.mem_write(INPUT_ADDR + 0x20, struct.pack("<II", r2, r1))
        uc.mem_write(INPUT_ADDR + 0xB8, struct.pack("<I", b8))

        sp = STACK_BASE + STACK_SIZE - 0x100
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00100000)
        uc.reg_write(UC_ARM_REG_R0, INPUT_ADDR)
        uc.reg_write(UC_ARM_REG_R4, 0xAAAAAAAA)
        uc.reg_write(UC_ARM_REG_R5, 0xBBBBBBBB)
        uc.reg_write(UC_ARM_REG_R6, 0xCCCCCCCC)
        uc.reg_write(UC_ARM_REG_R7, 0xDDDDDDDD)

        uc.emu_start(addr, 0x00100000, timeout=200000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        node_bytes = bytes(uc.mem_read(NODE_ADDR, 0x38))
        return {
            "ret": ret,
            "calls": calls,
            "node": node_bytes,
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
        }

    cases = [
        (5, 10, 0),    # r2!=0, 5*10 = 50 < 100
        (20, 10, 0),   # r2!=0, 20*10 = 200 > 100 -> clamped to 100
        (0, 10, 8),    # r2==0, b8*10 = 80 < 100
        (0, 15, 10),   # r2==0, b8*15 = 150 > 100 -> clamped to 100
    ]

    for c_tuple in cases:
        o = run_one(orig, *c_tuple)
        c = run_one(staged, *c_tuple)
        assert o == c, f"0024fd10 mismatch for {c_tuple}: {o} vs {c}"
    print("engine_func_0024fd10: PASS")

def test_002642d0():
    print("--- Testing script_vm_func_002642d0 ---")
    addr = 0x002642D0
    size = 152
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_002642d0", ROOT / "build")
    symbol_map = {
        "script_vm_func_002b780c": 0x002B780C,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    TABLE_PTR_ADDR = 0x20001000
    TABLE_ADDR = 0x20002000
    ITEM_ADDR = 0x20003000
    CONTAINER_ADDR = 0x20004000
    LIST_MEM = 0x20005000

    def run_one(c_bytes, has_container, item_in_list):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Global counter at 0x004DAD80
        uc.mem_write(0x004DAD80, struct.pack("<i", 42))

        # Table setup
        uc.mem_write(TABLE_PTR_ADDR, struct.pack("<I", TABLE_ADDR))
        uc.mem_write(TABLE_ADDR + 4, struct.pack("<I", ITEM_ADDR)) # index 1

        # Item setup
        container_ptr = CONTAINER_ADDR if has_container else 0
        uc.mem_write(ITEM_ADDR, b"\x00" * 0x20)
        uc.mem_write(ITEM_ADDR + 0x0C, struct.pack("<I", container_ptr))

        # Container setup
        if has_container:
            # 3 items in list: [0x11111111, ITEM_ADDR, 0x22222222] or without item
            if item_in_list:
                items = [0x11111111, ITEM_ADDR, 0x22222222]
            else:
                items = [0x11111111, 0x33333333, 0x22222222]
            uc.mem_write(LIST_MEM, struct.pack("<3I", *items))
            begin_ptr = LIST_MEM
            end_ptr = LIST_MEM + 12
            uc.mem_write(CONTAINER_ADDR, b"\x00" * 0x30)
            uc.mem_write(CONTAINER_ADDR + 0x18, struct.pack("<I", begin_ptr))
            uc.mem_write(CONTAINER_ADDR + 0x1C, struct.pack("<I", end_ptr))

        # Mock script_vm_func_002b780c:
        # r0: first (it + 1)
        # r1: last (end)
        # r2: result (it)
        # r3: pointer to item (sp)
        # copies [first..last) omitting *r3, writes to r2, returns new end pointer in r0
        uc.mem_write(0x002B780C, b"\x1e\xff\x2f\xe1")
        def on_remove(u, a, s, ud):
            first = u.reg_read(UC_ARM_REG_R0)
            last = u.reg_read(UC_ARM_REG_R1)
            result = u.reg_read(UC_ARM_REG_R2)
            val_ptr = u.reg_read(UC_ARM_REG_R3)
            val = struct.unpack("<I", u.mem_read(val_ptr, 4))[0]

            curr = first
            dest = result
            while curr < last:
                w = struct.unpack("<I", u.mem_read(curr, 4))[0]
                if w != val:
                    u.mem_write(dest, struct.pack("<I", w))
                    dest += 4
                curr += 4
            u.reg_write(UC_ARM_REG_R0, dest)
        uc.hook_add(UC_HOOK_CODE, on_remove, None, 0x002B780C, 0x002B780C)

        sp = STACK_BASE + STACK_SIZE - 0x100
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00100000)
        uc.reg_write(UC_ARM_REG_R0, TABLE_PTR_ADDR)
        uc.reg_write(UC_ARM_REG_R1, 1) # index 1
        uc.reg_write(UC_ARM_REG_R4, 0xAAAAAAAA)
        uc.reg_write(UC_ARM_REG_R5, 0xBBBBBBBB)

        uc.emu_start(addr, 0x00100000, timeout=200000)

        counter = struct.unpack("<i", uc.mem_read(0x004DAD80, 4))[0]
        item_c = struct.unpack("<I", uc.mem_read(ITEM_ADDR + 0x0C, 4))[0]
        end_val = struct.unpack("<I", uc.mem_read(CONTAINER_ADDR + 0x1C, 4))[0] if has_container else 0

        return {
            "counter": counter,
            "item_c": item_c,
            "end_val": end_val,
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
        }

    cases = [
        (False, False), # container is null -> decrements counter
        (True, True),   # item found in list -> removes, clears item->container, decrements counter
        (True, False),  # item not found in list -> does not clear item->container, decrements counter
    ]

    for c_tuple in cases:
        o = run_one(orig, *c_tuple)
        c = run_one(staged, *c_tuple)
        assert o == c, f"002642d0 mismatch for {c_tuple}: {o} vs {c}"
    print("script_vm_func_002642d0: PASS")

def test_0026b734():
    print("--- Testing ui_func_0026b734 ---")
    addr = 0x0026B734
    size = 152
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_0026b734", ROOT / "build")
    symbol_map = {
        "engine_func_002c586c": 0x002C586C,
        "script_vm_func_0025461c": 0x0025461C,
        "script_vm_func_002545c4": 0x002545C4,
        "script_vm_func_0025456c": 0x0025456C,
        "script_vm_func_002a8730": 0x002A8730,
        "ui_func_003e0eac": 0x003E0EAC,
        "ui_func_003e0f14": 0x003E0F14,
        "ui_func_003e0f80": 0x003E0F80,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    PTR_ADDR = 0x20001000

    def run_one(c_bytes, y, m, d, days, hr, mn, sc):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # 0x0043E2A8 + 0x0C -> pointer to PTR_ADDR
        uc.mem_write(0x0043E2A8 + 0x0C, struct.pack("<I", PTR_ADDR))
        uc.mem_write(PTR_ADDR + 4, struct.pack("<I", 0))

        def make_stub(target, ret_val):
            uc.mem_write(target, b"\x1e\xff\x2f\xe1")
            def hook(u, a, s, ud):
                u.reg_write(UC_ARM_REG_R0, ret_val)
            uc.hook_add(UC_HOOK_CODE, hook, None, target, target)

        # engine_func_002c586c writes 8 bytes to *out
        uc.mem_write(0x002C586C, b"\x1e\xff\x2f\xe1")
        def on_tick(u, a, s, ud):
            out_ptr = u.reg_read(UC_ARM_REG_R0)
            u.mem_write(out_ptr, struct.pack("<II", 0x11223344, 0x55667788))
        uc.hook_add(UC_HOOK_CODE, on_tick, None, 0x002C586C, 0x002C586C)

        make_stub(0x0025461C, y)
        make_stub(0x002545C4, m)
        make_stub(0x0025456C, d)
        make_stub(0x002A8730, days)
        make_stub(0x003E0EAC, hr)
        make_stub(0x003E0F14, mn)
        make_stub(0x003E0F80, sc)

        sp = STACK_BASE + STACK_SIZE - 0x100
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00100000)
        uc.reg_write(UC_ARM_REG_R4, 0xAAAAAAAA)
        uc.reg_write(UC_ARM_REG_R5, 0xBBBBBBBB)

        uc.emu_start(addr, 0x00100000, timeout=200000)

        res = struct.unpack("<i", uc.mem_read(PTR_ADDR + 4, 4))[0]
        return {
            "res": res,
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
        }

    cases = [
        (2026, 11, 3, 100, 14, 30, 45),
        (2013, 5, 23, 0, 0, 0, 0),
        (2020, 1, 1, 500, 23, 59, 59),
    ]

    for c_tuple in cases:
        o = run_one(orig, *c_tuple)
        c = run_one(staged, *c_tuple)
        assert o == c, f"0026b734 mismatch for {c_tuple}: {o} vs {c}"
    print("ui_func_0026b734: PASS")

if __name__ == "__main__":
    test_0024baf4()
    test_0024c3f8()
    test_0024fd10()
    test_002642d0()
    test_0026b734()
    print("\nALL 5 FUNCTIONS IN BATCH 12 PASSED DIFFERENTIAL VERIFICATION!")
