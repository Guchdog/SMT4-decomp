#!/usr/bin/env python3
"""Differential test for batch 31 C part 8:
- camp_func_00258308 (0x00258308, 156 B)
- camp_func_0025a378 (0x0025A378, 188 B)
- func_0025c1dc (0x0025C1DC, 184 B)
- script_vm_func_002646d4 (0x002646D4, 160 B)
- script_vm_func_00264900 (0x00264900, 192 B)
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
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
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
SOURCE = ROOT / "src/engine/leaf_batch31_c.cpp"

with open(ORIG_BIN, "rb") as f:
    ORIG_DATA = f.read()

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch31_c.o"
        compile_tu_armv6k(source, obj)
        COMPILED_FUNCTIONS = extract_elf_functions_detailed(obj)
    return COMPILED_FUNCTIONS[func_name]

def stage_body(body: bytes, relocs, target_addr: int, symbol_map: dict[str, int]) -> bytes:
    data = bytearray(body)
    for reloc in relocs:
        sym = reloc.symbol_name
        if sym not in symbol_map:
            raise RuntimeError(f"Unmapped relocation: {sym}")
        stub_addr = symbol_map[sym]
        inst = struct.unpack_from("<I", data, reloc.offset)[0]
        if inst == 0:
            struct.pack_into("<I", data, reloc.offset, stub_addr)
            continue
        rel_off = stub_addr - (target_addr + reloc.offset + 8)
        if (inst & 0xFE000000) == 0xFA000000:
            h = (rel_off >> 1) & 1
            imm24 = (rel_off >> 2) & 0x00FFFFFF
            inst = 0xFA000000 | (h << 24) | imm24
        else:
            imm24 = (rel_off >> 2) & 0x00FFFFFF
            inst = (inst & 0xFF000000) | imm24
        struct.pack_into("<I", data, reloc.offset, inst)
    return bytes(data)

def unmapped_hook(uc, access, address, size, value, user_data):
    aligned = address & ~0xFFF
    uc.mem_map(aligned, 0x1000)
    return True

def create_emulator() -> Uc:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(0x00480000, 0x00100000)
    uc.mem_map(0x10000000, 0x00100000)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, unmapped_hook)

    val = uc.reg_read(UC_ARM_REG_C1_C0_2)
    val |= (0xF << 20)
    uc.reg_write(UC_ARM_REG_C1_C0_2, val)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return uc

def test_camp_func_00258308():
    addr = 0x00258308
    print(f"--- Testing camp_func_00258308 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 156)
    tmp = ROOT / "build" / "test_31c_part08"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_00258308", tmp)

    FN_2B0824 = 0x002B0824
    FN_29EE4C = 0x0029EE4C
    FN_29ED08 = 0x0029ED08
    FN_2BF460 = 0x002BF460

    sym_map = {
        "func_002b0824": FN_2B0824,
        "func_0029ee4c": FN_29EE4C,
        "func_0029ed08": FN_29ED08,
        "ui_func_002bf460": FN_2BF460,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, has_obj: bool, ret_ee4c_10: int, ret_ee4c_2: int, ret_ed08: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj_addr = 0x10052000 if has_obj else 0
        calls = []

        def stub_2b0824(uc, address, size, user_data):
            calls.append("2b0824")
            uc.reg_write(UC_ARM_REG_R0, obj_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_29ee4c(uc, address, size, user_data):
            r1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("29ee4c", r1))
            ret = ret_ee4c_10 if r1 == 10 else ret_ee4c_2
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_29ed08(uc, address, size, user_data):
            calls.append("29ed08")
            uc.reg_write(UC_ARM_REG_R0, ret_ed08)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_draw(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            sp = uc.reg_read(UC_ARM_REG_SP)
            stack_args = struct.unpack("<II", uc.mem_read(sp, 8))
            calls.append(("draw", r0, r1, r2, r3, stack_args[0], stack_args[1]))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_2b0824, None, FN_2B0824, FN_2B0824)
        uc.hook_add(UC_HOOK_CODE, stub_29ee4c, None, FN_29EE4C, FN_29EE4C)
        uc.hook_add(UC_HOOK_CODE, stub_29ed08, None, FN_29ED08, FN_29ED08)
        uc.hook_add(UC_HOOK_CODE, stub_draw, None, FN_2BF460, FN_2BF460)

        uc.reg_write(UC_ARM_REG_R0, 0x10051000)
        uc.reg_write(UC_ARM_REG_R1, 0x10)
        uc.reg_write(UC_ARM_REG_R2, 0x20)
        uc.reg_write(UC_ARM_REG_R3, 0x30)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return calls

    cases = [
        (False, 0, 0, 0),
        (False, 0, 0, 1),
        (True, 1, 0, 1),
        (True, 0, 1, 0),
        (True, 0, 0, 0),
    ]

    for has_obj, e10, e2, ed in cases:
        c_orig = run_one(orig_code, has_obj, e10, e2, ed)
        c_dec = run_one(decomp_code, has_obj, e10, e2, ed)
        assert c_orig == c_dec, f"258308 mismatch for case {(has_obj, e10, e2, ed)}: {c_orig} vs {c_dec}"

    print("camp_func_00258308 PASS")

def test_camp_func_0025a378():
    addr = 0x0025a378
    print(f"--- Testing camp_func_0025a378 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 188)
    tmp = ROOT / "build" / "test_31c_part08"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_0025a378", tmp)

    FN_2B66EC = 0x002B66EC
    FN_2A8A1C = 0x002A8A1C
    FN_2A8A08 = 0x002A8A08
    FN_2A89E4 = 0x002A89E4

    sym_map = {
        "func_002b66ec": FN_2B66EC,
        "func_002a8a1c": FN_2A8A1C,
        "func_002a8a08": FN_2A8A08,
        "func_002a89e4": FN_2A89E4,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, mode: int, bit_idx: int, f72: int, arr_vals: list[int], obj_f44_map: dict[int, int]):
        uc = create_emulator()
        uc.mem_write(addr, code)

        p_b66 = 0x10050000
        uc.mem_write(p_b66 + 0x72, struct.pack("<H", f72))

        base_a08 = 0x10051000
        # write arr at 0x90F0 and 0x9108
        uc.mem_write(base_a08 + 0x90F0, bytes([v & 0xFF for v in arr_vals]))
        uc.mem_write(base_a08 + 0x9108, bytes([v & 0xFF for v in arr_vals[:3]]))

        def stub_b66(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, p_b66)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_a1c(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, len(arr_vals))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_a08(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, base_a08)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_9e4(uc, address, size, user_data):
            idx = uc.reg_read(UC_ARM_REG_R0)
            f44 = obj_f44_map.get(idx, 0)
            obj_addr = 0x10060000 + (idx * 0x100)
            uc.mem_write(obj_addr + 0x44, struct.pack("<H", f44))
            uc.reg_write(UC_ARM_REG_R0, obj_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_b66, None, FN_2B66EC, FN_2B66EC)
        uc.hook_add(UC_HOOK_CODE, stub_a1c, None, FN_2A8A1C, FN_2A8A1C)
        uc.hook_add(UC_HOOK_CODE, stub_a08, None, FN_2A8A08, FN_2A8A08)
        uc.hook_add(UC_HOOK_CODE, stub_9e4, None, FN_2A89E4, FN_2A89E4)

        uc.reg_write(UC_ARM_REG_R0, mode)
        uc.reg_write(UC_ARM_REG_R1, bit_idx)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return uc.reg_read(UC_ARM_REG_R0)

    # Cases:
    # 1. mode = 0, f72 matches
    r_orig = run_one(orig_code, 0, 2, 0x04, [0, 1], {})
    r_dec = run_one(decomp_code, 0, 2, 0x04, [0, 1], {})
    assert r_orig == r_dec == 1

    # 2. mode = 1, f72 has bit, but mode 1 skips f72 and arr matches
    r_orig = run_one(orig_code, 1, 2, 0x04, [0, 1], {0: 0, 1: 0x04})
    r_dec = run_one(decomp_code, 1, 2, 0x04, [0, 1], {0: 0, 1: 0x04})
    assert r_orig == r_dec == 1

    # 3. mode = 2, f72 no bit, arr matches
    r_orig = run_one(orig_code, 2, 3, 0x00, [0, 1, 2], {0: 0, 1: 0x08, 2: 0})
    r_dec = run_one(decomp_code, 2, 3, 0x00, [0, 1, 2], {0: 0, 1: 0x08, 2: 0})
    assert r_orig == r_dec == 1

    # 4. mode = 0, no match
    r_orig = run_one(orig_code, 0, 1, 0x00, [0, 1], {0: 0, 1: 0})
    r_dec = run_one(decomp_code, 0, 1, 0x00, [0, 1], {0: 0, 1: 0})
    assert r_orig == r_dec == 0

    # 5. mode = 4 (invalid)
    r_orig = run_one(orig_code, 4, 1, 0xFF, [0], {0: 0xFF})
    r_dec = run_one(decomp_code, 4, 1, 0xFF, [0], {0: 0xFF})
    assert r_orig == r_dec == 0

    print("camp_func_0025a378 PASS")

def test_func_0025c1dc():
    addr = 0x0025c1dc
    print(f"--- Testing func_0025c1dc ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 184)
    tmp = ROOT / "build" / "test_31c_part08"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0025c1dc", tmp)

    FN_2C586C = 0x002C586C
    FN_25461C = 0x0025461C
    FN_2545C4 = 0x002545C4
    FN_25456C = 0x0025456C
    FN_2A8730 = 0x002A8730
    FN_3E0EAC = 0x003E0EAC
    FN_3E0F14 = 0x003E0F14
    FN_3E0F80 = 0x003E0F80

    sym_map = {
        "func_002c586c": FN_2C586C,
        "func_0025461c": FN_25461C,
        "func_002545c4": FN_2545C4,
        "func_0025456c": FN_25456C,
        "func_002a8730": FN_2A8730,
        "func_003e0eac": FN_3E0EAC,
        "func_003e0f14": FN_3E0F14,
        "func_003e0f80": FN_3E0F80,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, target: int, days: int, hours: int, minutes: int, seconds: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        glob_addr = 0x0043E2B4
        tgt_struct = 0x10050000
        uc.mem_write(glob_addr, struct.pack("<I", tgt_struct))
        uc.mem_write(tgt_struct + 4, struct.pack("<I", target))

        def stub_2c5(uc, address, size, user_data):
            sp = uc.reg_read(UC_ARM_REG_R0)
            uc.mem_write(sp, b"12345678")
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_const(val):
            def handler(uc, address, size, user_data):
                uc.reg_write(UC_ARM_REG_R0, val)
                lr = uc.reg_read(UC_ARM_REG_LR)
                uc.reg_write(UC_ARM_REG_PC, lr)
            return handler

        uc.hook_add(UC_HOOK_CODE, stub_2c5, None, FN_2C586C, FN_2C586C)
        uc.hook_add(UC_HOOK_CODE, stub_const(1), None, FN_25461C, FN_25461C)
        uc.hook_add(UC_HOOK_CODE, stub_const(2), None, FN_2545C4, FN_2545C4)
        uc.hook_add(UC_HOOK_CODE, stub_const(3), None, FN_25456C, FN_25456C)
        uc.hook_add(UC_HOOK_CODE, stub_const(days), None, FN_2A8730, FN_2A8730)
        uc.hook_add(UC_HOOK_CODE, stub_const(hours), None, FN_3E0EAC, FN_3E0EAC)
        uc.hook_add(UC_HOOK_CODE, stub_const(minutes), None, FN_3E0F14, FN_3E0F14)
        uc.hook_add(UC_HOOK_CODE, stub_const(seconds), None, FN_3E0F80, FN_3E0F80)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return uc.reg_read(UC_ARM_REG_R0)

    # Case 1: target == 0 -> -1
    r_orig = run_one(orig_code, 0, 1, 2, 3, 4)
    r_dec = run_one(decomp_code, 0, 1, 2, 3, 4)
    assert r_orig == r_dec == 0xFFFFFFFF, f"25c1dc target 0 mismatch: {hex(r_orig)} vs {hex(r_dec)}"

    # Case 2: total seconds = ((1 * 24 + 2) * 60 + 3) * 60 + 4 = ((26)*60+3)*60+4 = 1563*60+4 = 93784
    # target = 90000 -> diff = 3784
    r_orig = run_one(orig_code, 90000, 1, 2, 3, 4)
    r_dec = run_one(decomp_code, 90000, 1, 2, 3, 4)
    assert r_orig == r_dec == 3784, f"25c1dc target 90000 mismatch: {r_orig} vs {r_dec}"

    # Case 3: target > total_seconds (e.g. 100000) -> 0
    r_orig = run_one(orig_code, 100000, 1, 2, 3, 4)
    r_dec = run_one(decomp_code, 100000, 1, 2, 3, 4)
    assert r_orig == r_dec == 0, f"25c1dc target 100000 mismatch: {r_orig} vs {r_dec}"

    print("func_0025c1dc PASS")

def test_script_vm_func_002646d4():
    addr = 0x002646d4
    print(f"--- Testing script_vm_func_002646d4 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 160)
    tmp = ROOT / "build" / "test_31c_part08"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_002646d4", tmp)

    FN_2C0BA8 = 0x002C0BA8
    sym_map = {
        "func_002c0ba8": FN_2C0BA8,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, count: int, elem_configs: list[tuple[int, int, int, int]], ret_map_2c0: dict[int, int]):
        uc = create_emulator()
        uc.mem_write(addr, code)

        count_ptr = 0x00447A2C
        uc.mem_write(count_ptr, struct.pack("<I", count))

        base = 0x004A1264
        for i, (f164, f12c, id1, id2) in enumerate(elem_configs):
            elem = bytearray(0x178)
            elem[0x164] = f164
            struct.pack_into("<I", elem, 0x12C, f12c)
            struct.pack_into("<h", elem, 0x160, id1)
            struct.pack_into("<h", elem, 0x162, id2)
            uc.mem_write(base + i * 0x178, bytes(elem))

        def stub_2c0(uc, address, size, user_data):
            arg = struct.unpack("<h", struct.pack("<H", uc.reg_read(UC_ARM_REG_R0) & 0xFFFF))[0]
            uc.reg_write(UC_ARM_REG_R0, ret_map_2c0.get(arg, 0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_2c0, None, FN_2C0BA8, FN_2C0BA8)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_bytes = [uc.mem_read(base + i * 0x178 + 0x164, 1)[0] for i in range(count)]
        return out_bytes

    configs = [
        (1, 0x10, 10, 20),   # already 1 -> stays 1
        (0, 0, 10, 20),      # f12c == 0 -> stays 0
        (0, 0x10, 10, 20),   # id1=10 returns 0 -> sets 1
        (0, 0x10, 11, 20),   # id1=11 returns 1, id2=20 returns 1 -> sets 1
        (0, 0x10, 11, 21),   # id1=11 returns 1, id2=21 returns 0 -> stays 0
    ]
    ret_map = {10: 0, 11: 1, 20: 1, 21: 0}

    out_orig = run_one(orig_code, len(configs), configs, ret_map)
    out_dec = run_one(decomp_code, len(configs), configs, ret_map)
    assert out_orig == out_dec == [1, 0, 1, 1, 0], f"2646d4 mismatch: {out_orig} vs {out_dec}"

    print("script_vm_func_002646d4 PASS")

def test_script_vm_func_00264900():
    addr = 0x00264900
    print(f"--- Testing script_vm_func_00264900 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 192)
    tmp = ROOT / "build" / "test_31c_part08"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_00264900", tmp)

    FN_1E5D84 = 0x001E5D84
    FN_280F3C = 0x00280F3C
    sym_map = {
        "func_001e5d84": FN_1E5D84,
        "func_00280f3c": FN_280F3C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, arg0: int, item_entries: list[tuple[int, int]]):
        uc = create_emulator()
        uc.mem_write(addr, code)

        table_ptr = 0x00447A78
        table_base = 0x10010000
        uc.mem_write(table_ptr, struct.pack("<I", table_base))

        # 128 items * 404 bytes
        table_data = bytearray(0x10000)
        for idx, (f1d0, f214) in enumerate(item_entries):
            off = idx * 404
            table_data[off + 0x1D0] = f1d0
            struct.pack_into("<i", table_data, off + 0x214, f214)
        uc.mem_write(table_base, bytes(table_data))

        # Float object for middle section
        obj_ptr = 0x00447E88
        obj_base = 0x10050000
        uc.mem_write(obj_ptr, struct.pack("<I", obj_base))
        floats = [float(i) for i in range(30)]
        uc.mem_write(obj_base, struct.pack("<30f", *floats))

        calls = []
        def stub_1e5(uc, address, size, user_data):
            calls.append("1e5")
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_280(uc, address, size, user_data):
            # Read s0..s6
            s_regs = []
            for r in [UC_ARM_REG_S0, UC_ARM_REG_S1, UC_ARM_REG_S2, UC_ARM_REG_S3, UC_ARM_REG_S4, UC_ARM_REG_S5, UC_ARM_REG_S6]:
                raw = uc.reg_read(r)
                val = struct.unpack("<f", struct.pack("<I", raw))[0]
                s_regs.append(val)
            calls.append(("280", s_regs))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_1e5, None, FN_1E5D84, FN_1E5D84)
        uc.hook_add(UC_HOOK_CODE, stub_280, None, FN_280F3C, FN_280F3C)

        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_table = uc.mem_read(table_base, 0x10000)
        return out_table, calls

    # Test cases:
    # item 0: f1d0=1, f214=20 (>0) -> f1d8=1, f214=0x10
    # item 1: f1d0=1, f214=0 (<=0) -> f1d8=1, f214=0
    # item 2: f1d0=1, f214=-5 (<0) -> f1d8=1, f214=-5
    # item 3: f1d0=0, f214=20 -> f1d8=0, f214=20
    test_items = [(1, 20), (1, 0), (1, -5), (0, 20)] + [(0, 0)] * 124

    for arg0 in [0, 1]:
        t_orig, c_orig = run_one(orig_code, arg0, test_items)
        t_dec, c_dec = run_one(decomp_code, arg0, test_items)
        assert c_orig == c_dec, f"264900 calls mismatch for arg0={arg0}"
        assert t_orig == t_dec, f"264900 table memory mismatch for arg0={arg0}"

    print("script_vm_func_00264900 PASS")

if __name__ == "__main__":
    test_camp_func_00258308()
    test_camp_func_0025a378()
    test_func_0025c1dc()
    test_script_vm_func_002646d4()
    test_script_vm_func_00264900()
    print("\nALL 5 FUNCTIONS IN PART 08 PASSED PERFECTLY!")
