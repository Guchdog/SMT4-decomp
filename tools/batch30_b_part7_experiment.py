#!/usr/bin/env python3
"""Differential test for batch 30 B part 7:
- script_vm_func_00256364 (0x00256364, 112 B)
- battle_func_00256b04 (0x00256B04, 124 B)
- engine_func_00259760 (0x00259760, 108 B)
- script_vm_func_0025b640 (0x0025B640, 112 B)
- ui_func_00262b60 (0x00262B60, 108 B)
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
    UC_ARM_REG_S3,
    UC_ARM_REG_S4,
    UC_ARM_REG_S5,
    UC_ARM_REG_S6,
    UC_ARM_REG_S7,
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


def test_00256364():
    print("--- Testing script_vm_func_00256364 ---")
    addr = 0x00256364
    size = 112
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_00256364", ROOT / "build")

    STUB_CTX = 0x002B6E60
    STUB_DISP = 0x002899C4
    staged = stage_body(comp, relocs, addr, {
        "script_vm_func_002b6e60": STUB_CTX,
        "engine_func_002899c4": STUB_DISP,
    })

    CTX = 0x20002000
    DISP_LOG = 0x20004000

    # Hook STUB_CTX to return CTX
    # Hook STUB_DISP to log (r0, r1, r2)
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, flags, code):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_CTX, stub_code)
        uc.mem_write(STUB_DISP, stub_code)
        uc.mem_write(CTX, b"\x00" * 0x800)
        uc.mem_write(CTX + 0x608, struct.pack("<H", flags))
        uc.mem_write(CTX + 0x46, struct.pack("<H", code))
        uc.mem_write(DISP_LOG, struct.pack("<IIII", 0, 0, 0, 0))

        calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_CTX:
                uc.reg_write(UC_ARM_REG_R0, CTX)
            elif address == STUB_DISP:
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                calls.append((r0, r1, r2))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        out_code = struct.unpack_from("<H", uc.mem_read(CTX + 0x46, 2))[0]
        return calls, out_code

    test_cases = [
        (0, 0x2A3),       # flags bit 0 not set -> early exit
        (1, 0x2A3),       # flags bit 0 set, code 0x2A3 -> disp(0x262, 0, 1)
        (3, 0x2A5),       # flags bit 0 set, code 0x2A5 -> disp(0x263, 0, 1)
        (1, 0x100),       # other code -> no disp call, code cleared
        (0x101, 0),       # code 0
        (0xFFFF, 0x2A3),
    ]

    for flags, code in test_cases:
        c1, out1 = run_one(orig, flags, code)
        c2, out2 = run_one(staged, flags, code)
        assert c1 == c2, f"Calls mismatch for flags={hex(flags)}, code={hex(code)}: orig={c1}, comp={c2}"
        assert out1 == out2, f"Out code mismatch for flags={hex(flags)}, code={hex(code)}: orig={out1}, comp={out2}"
    print("script_vm_func_00256364: PASS")


def test_00256b04():
    print("--- Testing battle_func_00256b04 ---")
    addr = 0x00256B04
    size = 124
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("battle_func_00256b04", ROOT / "build")

    STUB_ALLOC = 0x00226B2C
    staged = stage_body(comp, relocs, addr, {
        "battle_func_00226b2c": STUB_ALLOC,
    })

    PTR_MGR = 0x00434290
    MGR = 0x20001000
    NODE = 0x20003000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, arg0, arg1, list_nodes, node_init):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_ALLOC, stub_code)

        uc.mem_write(PTR_MGR, struct.pack("<I", MGR))
        uc.mem_write(MGR, b"\x00" * 0x100)
        uc.mem_write(NODE, b"\x00" * 0x100)
        uc.mem_write(NODE, node_init)

        # Build linked list
        first_ptr = 0
        if list_nodes:
            curr_addr = 0x20004000
            first_ptr = curr_addr
            for i, (f0_id, f4_type, f2_val) in enumerate(list_nodes):
                next_addr = (curr_addr + 0x20) if (i < len(list_nodes) - 1) else 0
                node_data = bytearray(0x20)
                struct.pack_into("<h", node_data, 0, f0_id)
                struct.pack_into("<h", node_data, 2, f2_val)
                node_data[4] = f4_type
                struct.pack_into("<I", node_data, 0xC, next_addr)
                uc.mem_write(curr_addr, bytes(node_data))
                curr_addr = next_addr

        uc.mem_write(MGR + 8, struct.pack("<I", first_ptr))

        alloc_calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_ALLOC:
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                alloc_calls.append((r0, r1, r2, r3))
                uc.reg_write(UC_ARM_REG_R0, NODE)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        node_after = uc.mem_read(NODE, 8)
        return alloc_calls, node_after

    test_cases = [
        # (arg0, arg1, list_nodes [(id, type, f2)], node_init)
        (5, 10, [], struct.pack("<hhB", 5, 0, 0)),
        (5, 10, [(5, 0x34, 1)], struct.pack("<hhB", 5, 2, 0)),
        (5, 10, [(5, 0x10, 1)], struct.pack("<hhB", 5, 2, 0)), # type not 0x34
        (5, 10, [(6, 0x34, 1), (5, 0x34, 1)], struct.pack("<hhB", 5, 3, 0)),
        (5, 10, [(5, 0x34, 1)], struct.pack("<hhB", 5, -1, 0)), # already -1
        (1234, 99, [(1234, 0x34, 0)], struct.pack("<hhB", 1234, 10, 0)),
    ]

    for arg0, arg1, nodes, node_init in test_cases:
        c1, n1 = run_one(orig, arg0, arg1, nodes, node_init)
        c2, n2 = run_one(staged, arg0, arg1, nodes, node_init)
        assert c1 == c2, f"Alloc call mismatch: orig={c1}, comp={c2}"
        assert n1 == n2, f"Node result mismatch: orig={n1.hex()}, comp={n2.hex()}"
    print("battle_func_00256b04: PASS")


def test_00259760():
    print("--- Testing engine_func_00259760 ---")
    addr = 0x00259760
    size = 108
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_00259760", ROOT / "build")

    STUB_CHECK = 0x002BF41C
    staged = stage_body(comp, relocs, addr, {
        "engine_func_002bf41c": STUB_CHECK,
    })

    PTR_BASE = 0x0043DED0
    BASE = 0x20001000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, initial_slots, new_entry, valid_map):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_CHECK, stub_code)

        uc.mem_write(PTR_BASE, struct.pack("<I", BASE))
        uc.mem_write(BASE, b"\x00" * 0x200)

        for i, val in enumerate(initial_slots):
            uc.mem_write(BASE + 0x34 + i * 4, struct.pack("<I", val))

        def code_hook(uc, address, sz, user_data):
            if address == STUB_CHECK:
                r0 = uc.reg_read(UC_ARM_REG_R0)
                is_valid = valid_map.get(r0, 0)
                uc.reg_write(UC_ARM_REG_R0, is_valid)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, new_entry)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        slots_after = [struct.unpack_from("<I", uc.mem_read(BASE + 0x34 + i * 4, 4))[0] for i in range(10)]
        return slots_after

    test_cases = [
        # (initial_slots, new_entry, valid_map)
        ([0]*10, 0x12345678, {}),
        ([0x10, 0x20, 0, 0, 0, 0, 0, 0, 0, 0], 0x9999, {0x10: 1, 0x20: 1}),
        ([0x10, 0x20, 0, 0, 0, 0, 0, 0, 0, 0], 0x9999, {0x10: 0, 0x20: 1}), # slot 0 invalidated!
        ([0x10]*10, 0x9999, {0x10: 1}), # all full & valid -> no insert
        ([0x10]*10, 0x9999, {0x10: 0}), # all invalid -> slot 0 gets new_entry
        ([0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xA], 0x99, {0x5: 0}), # slot 4 invalidated
    ]

    for initial_slots, new_entry, valid_map in test_cases:
        s1 = run_one(orig, initial_slots, new_entry, valid_map)
        s2 = run_one(staged, initial_slots, new_entry, valid_map)
        assert s1 == s2, f"Slots mismatch: orig={s1}, comp={s2}"
    print("engine_func_00259760: PASS")


def test_0025b640():
    print("--- Testing script_vm_func_0025b640 ---")
    addr = 0x0025B640
    size = 112
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_0025b640", ROOT / "build")

    STUB_2D = 0x00287B4C
    STUB_3D = 0x00287D54
    staged = stage_body(comp, relocs, addr, {
        "script_vm_func_00287b4c": STUB_2D,
        "script_vm_func_00287d54": STUB_3D,
    })

    PTR_MODE = 0x0049F91C
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, mode, p1, p2, thresh, h_lim, ret_dist):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_2D, stub_code)
        uc.mem_write(STUB_3D, stub_code)

        uc.mem_write(PTR_MODE, struct.pack("<i", mode))

        calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_2D:
                calls.append("2D")
                uc.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", ret_dist))[0])
            elif address == STUB_3D:
                calls.append("3D")
                uc.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", ret_dist))[0])

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        # s0..s7
        uc.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", p1[0]))[0])
        uc.reg_write(UC_ARM_REG_S1, struct.unpack("<I", struct.pack("<f", p1[1]))[0])
        uc.reg_write(UC_ARM_REG_S2, struct.unpack("<I", struct.pack("<f", p1[2]))[0])
        uc.reg_write(UC_ARM_REG_S3, struct.unpack("<I", struct.pack("<f", p2[0]))[0])
        uc.reg_write(UC_ARM_REG_S4, struct.unpack("<I", struct.pack("<f", p2[1]))[0])
        uc.reg_write(UC_ARM_REG_S5, struct.unpack("<I", struct.pack("<f", p2[2]))[0])
        uc.reg_write(UC_ARM_REG_S6, struct.unpack("<I", struct.pack("<f", thresh))[0])
        uc.reg_write(UC_ARM_REG_S7, struct.unpack("<I", struct.pack("<f", h_lim))[0])

        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, calls

    test_cases = [
        # (mode, (x1, y1, z1), (x2, y2, z2), thresh, h_lim, ret_dist)
        (100, (0.0, 10.0, 0.0), (10.0, 10.0, 0.0), 15.0, 5.0, 10.0),  # mode >= 100, dist < thresh -> 1
        (105, (0.0, 10.0, 0.0), (10.0, 10.0, 0.0), 8.0, 5.0, 10.0),   # mode >= 100, dist >= thresh -> 0
        (50, (0.0, 10.0, 0.0), (10.0, 20.0, 0.0), 15.0, 5.0, 10.0),   # mode < 100, |dy|=10 >= h_lim(5) -> 0, no 3D call
        (50, (0.0, 10.0, 0.0), (10.0, 12.0, 0.0), 15.0, 5.0, 10.0),   # mode < 100, |dy|=2 < h_lim, dist(10) < thresh(15) -> 1
        (50, (0.0, 10.0, 0.0), (10.0, 8.0, 0.0), 15.0, 5.0, 16.0),    # mode < 100, |dy|=2 < h_lim, dist(16) >= thresh(15) -> 0
        (0, (1.0, 2.0, 3.0), (4.0, 5.0, 6.0), 10.0, 10.0, 5.0),
    ]

    for mode, p1, p2, thresh, h_lim, ret_dist in test_cases:
        r1, c1 = run_one(orig, mode, p1, p2, thresh, h_lim, ret_dist)
        r2, c2 = run_one(staged, mode, p1, p2, thresh, h_lim, ret_dist)
        assert r1 == r2, f"Ret mismatch: orig={r1}, comp={r2} for mode={mode}"
        assert c1 == c2, f"Call mismatch: orig={c1}, comp={c2} for mode={mode}"
    print("script_vm_func_0025b640: PASS")


def test_00262b60():
    print("--- Testing ui_func_00262b60 ---")
    addr = 0x00262B60
    size = 108
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_00262b60", ROOT / "build")

    STUB_ZERO = 0x002C3B48
    staged = stage_body(comp, relocs, addr, {
        "engine_func_002c3b48": STUB_ZERO,
    })

    DST = 0x20001000
    SRC = 0x20002000

    def run_one(c_bytes, src_bytes, max_len, dst_align_off=0, src_align_off=0):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Implementation for STUB_ZERO: zero out [r0, r0 + r1)
        # We can implement it via hook or ARM instructions:
        # stub:
        #   cmp r1, #0
        #   bxeq lr
        #   push {r0, r1, r2}
        # loop:
        #   strb r2, [r0], #1  (r2=0)
        #   subs r1, r1, #1
        #   bne loop
        #   pop {r0, r1, r2}
        #   bx lr
        def zero_hook(uc, address, sz, user_data):
            if address == STUB_ZERO:
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                if r1 > 0:
                    uc.mem_write(r0, b"\x00" * r1)

        stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr
        uc.mem_write(STUB_ZERO, stub_code)
        h = uc.hook_add(UC_HOOK_CODE, zero_hook)

        dst_addr = DST + dst_align_off
        src_addr = SRC + src_align_off

        # Fill DST with non-zero sentinel
        uc.mem_write(DST, b"\xAA" * 0x100)
        uc.mem_write(SRC, src_bytes)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, dst_addr)
        uc.reg_write(UC_ARM_REG_R1, src_addr)
        uc.reg_write(UC_ARM_REG_R2, max_len)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=1000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        dst_result = uc.mem_read(dst_addr, max_len)
        return ret == dst_addr, dst_result

    test_cases = [
        # (src_bytes, max_len, dst_off, src_off)
        (b"Hello\x00", 10, 0, 0),
        (b"Hello\x00", 5, 0, 0),         # max_len exact fit with null
        (b"Hello World\x00", 5, 0, 0),   # max_len truncates before null
        (b"Test\x00", 16, 0, 0),         # aligned 4-byte string
        (b"A\x00", 8, 1, 1),             # unaligned
        (b"12345678\x00", 20, 2, 3),     # unaligned with remaining padding
        (b"\x00", 10, 0, 0),             # empty string
        (b"LongerStringForTestingBuffer\x00", 32, 0, 0),
    ]

    for src_bytes, max_len, dst_off, src_off in test_cases:
        r1, d1 = run_one(orig, src_bytes, max_len, dst_off, src_off)
        r2, d2 = run_one(staged, src_bytes, max_len, dst_off, src_off)
        assert r1 and r2, "Return value must be dst pointer"
        assert d1 == d2, f"Dst mismatch for {src_bytes}, len={max_len}: orig={d1.hex()}, comp={d2.hex()}"
    print("ui_func_00262b60: PASS")


def main():
    test_00256364()
    test_00256b04()
    test_00259760()
    test_0025b640()
    test_00262b60()
    print("\nALL 5 FUNCTIONS IN BATCH 30 B PART 7 PASSED WITH 100% DIFFERENTIAL FIDELITY!")

if __name__ == "__main__":
    main()
