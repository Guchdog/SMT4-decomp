#!/usr/bin/env python3
"""Differential test for batch 31 C part 5:
- engine_func_0023963c (0x0023963C, 188 B)
- engine_func_0023abd4 (0x0023ABD4, 180 B)
- func_0023bc5c (0x0023BC5C, 160 B)
- battle_func_0023c4c4 (0x0023C4C4, 192 B)
- camp_func_0023e590 (0x0023E590, 164 B)
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
    UC_ARM_REG_D0,
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
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, unmapped_hook)

    val = uc.reg_read(UC_ARM_REG_C1_C0_2)
    val |= (0xF << 20)
    uc.reg_write(UC_ARM_REG_C1_C0_2, val)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return uc

def test_engine_func_0023963c():
    addr = 0x0023963C
    print(f"--- Testing engine_func_0023963c ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 188)
    tmp = ROOT / "build" / "test_31c_part05"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_0023963c", tmp)

    FN_238E18 = 0x00238E18
    FN_3E0DBC = 0x003E0DBC
    sym_map = {
        "func_00238e18": FN_238E18,
        "func_003e0dbc": FN_3E0DBC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, mode: int, idx: int, count0: int, count: int, max_c: int, match_item_idx: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        self_addr = 0x10050000
        uc.mem_map(self_addr, 0x10000)
        mem = bytearray(0x800)

        struct.pack_into("<I", mem, 0x210, count0)
        struct.pack_into("<I", mem, 0x3C0, count)
        struct.pack_into("<I", mem, 0x560, max_c)

        # 0x21C array
        for i in range(count0):
            struct.pack_into("<I", mem, 0x21C + i * 4, 0x10061000 + i * 0x100)
        # 0x3CC array
        for i in range(count):
            struct.pack_into("<I", mem, 0x3CC + i * 4, 0x10071000 + i * 0x100)

        uc.mem_write(self_addr, bytes(mem))

        needle_str = 0x10085000
        uc.mem_write(needle_str, b"target\0")

        def f_38e18(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, needle_str)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_e0dbc(uc, address, size, user_data):
            arg1 = uc.reg_read(UC_ARM_REG_R1) # item + 0x20
            # if item index matches match_item_idx, return 1
            cur_item_idx = (arg1 - 0x10071000 - 0x20) // 0x100
            ret = 1 if cur_item_idx == match_item_idx else 0
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_38e18, None, FN_238E18, FN_238E18)
        uc.hook_add(UC_HOOK_CODE, f_e0dbc, None, FN_3E0DBC, FN_3E0DBC)

        uc.reg_write(UC_ARM_REG_R0, self_addr)
        uc.reg_write(UC_ARM_REG_R1, mode)
        uc.reg_write(UC_ARM_REG_R2, idx)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return uc.reg_read(UC_ARM_REG_R0)

    cases = [
        # mode=0: idx < count0
        (0, 1, 3, 5, 5, -1),
        # mode=0: idx >= count0
        (0, 5, 3, 5, 5, -1),
        # mode=1: idx >= count
        (1, 10, 3, 5, 5, -1),
        # mode=1: count != max_c -> returns 0x3CC + idx*4
        (1, 2, 3, 5, 10, -1),
        # mode=1: count == max_c -> search with match at item 2
        (1, 0, 3, 5, 5, 2),
        # mode=1: count == max_c -> search with no match
        (1, 0, 3, 5, 5, -1),
    ]

    for c in cases:
        r_o = run_one(orig_code, *c)
        r_d = run_one(decomp_code, *c)
        assert r_o == r_d, f"23963c mismatch on {c}: orig {hex(r_o)} vs decomp {hex(r_d)}"

    print("engine_func_0023963c: PASS")

def test_engine_func_0023abd4():
    addr = 0x0023ABD4
    print(f"--- Testing engine_func_0023abd4 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 180)
    tmp = ROOT / "build" / "test_31c_part05"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_0023abd4", tmp)

    decomp_code = stage_body(comp, relocs, addr, {})

    def run_one(code, flag_val: int, s32_pair: tuple[int, int], u16_pair: tuple[int, int], f_pair: tuple[float, float], scale: float):
        uc = create_emulator()
        uc.mem_write(addr, code)

        src_addr = 0x10082000
        out_addr = 0x10083000
        obj_f4 = 0x10084000
        obj_f2 = 0x10085000
        obj_f8 = 0x10086000
        obj_fc = 0x10087000

        # Setup pointers
        uc.mem_write(src_addr + 4, struct.pack("<I", obj_f4))
        uc.mem_write(obj_f4 + 0x10, struct.pack("<I", obj_f2))

        uc.mem_write(src_addr + 8, struct.pack("<I", obj_f8))
        uc.mem_write(obj_f8 + 0xC, struct.pack("<I", obj_fc))

        # Setup values
        uc.mem_write(src_addr + 0x1C, bytes([flag_val]))
        # s32 pair at obj_fc + 0x14
        uc.mem_write(obj_fc + 0x14, struct.pack("<ii", s32_pair[0], s32_pair[1]))
        # u16 pair at obj_f2 + 0x24
        uc.mem_write(obj_f2 + 0x24, struct.pack("<HH", u16_pair[0], u16_pair[1]))
        # float pair at src_addr + 0x10
        uc.mem_write(src_addr + 0x10, struct.pack("<ff", f_pair[0], f_pair[1]))

        uc.reg_write(UC_ARM_REG_R0, src_addr)
        uc.reg_write(UC_ARM_REG_R1, out_addr)
        scale_bits = struct.unpack("<I", struct.pack("<f", scale))[0]
        uc.reg_write(UC_ARM_REG_D0, scale_bits)
        uc.reg_write(UC_ARM_REG_R2, scale_bits)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_floats = struct.unpack("<fff", uc.mem_read(out_addr, 12))
        return out_floats

    cases = [
        (1, (100, 200), (50, 60), (1.0, 2.0), 1.5),
        (0, (100, 200), (50, 60), (-5.0, 10.0), 2.0),
        (0, (0, 0), (80, 20), (10.0, -2.0), 0.5),
    ]

    for c in cases:
        r_o = run_one(orig_code, *c)
        r_d = run_one(decomp_code, *c)
        for i in range(3):
            assert abs(r_o[i] - r_d[i]) < 1e-4, f"23abd4 mismatch on {c}: orig {r_o} vs decomp {r_d}"

    print("engine_func_0023abd4: PASS")

def test_func_0023bc5c():
    addr = 0x0023BC5C
    print(f"--- Testing func_0023bc5c ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 160)
    tmp = ROOT / "build" / "test_31c_part05"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0023bc5c", tmp)

    decomp_code = stage_body(comp, relocs, addr, {})

    def run_one(code, src_val0, src_val1, flag_byte, glob_val):
        uc = create_emulator()
        uc.mem_write(addr, code)

        glob_addr = 0x0044E670
        uc.mem_write(glob_addr, struct.pack("<I", glob_val))

        src_addr = 0x10082000
        dst_addr = 0x10083000

        uc.mem_write(src_addr, struct.pack("<IIB", src_val0, src_val1, flag_byte))

        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_R1, dst_addr)
        uc.reg_write(UC_ARM_REG_R2, src_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return uc.mem_read(dst_addr, 18 * 4)

    cases = [
        (0x10000, 0x20000, 1, 0x100),
        (0x50000, 0x60000, 0, 0x200),
    ]

    for c in cases:
        r_o = run_one(orig_code, *c)
        r_d = run_one(decomp_code, *c)
        assert r_o == r_d, f"23bc5c mismatch on {c}"

    print("func_0023bc5c: PASS")

def test_battle_func_0023c4c4():
    global COMPILED_FUNCTIONS
    COMPILED_FUNCTIONS = None
    addr = 0x0023C4C4
    print(f"--- Testing battle_func_0023c4c4 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 192)
    tmp = ROOT / "build" / "test_31c_part05"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_0023c4c4", tmp)

    FN_226B2C = 0x00226B2C
    sym_map = {
        "func_00226b2c": FN_226B2C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, arg0, arg1, arg2, arg3, arg4, arg5, arg6, arg7):
        uc = create_emulator()
        uc.mem_write(addr, code)

        holder = 0x00434290
        mgr_addr = 0x10082000
        uc.mem_write(holder, struct.pack("<I", mgr_addr))

        obj1 = 0x10083000
        obj2 = 0x10084000
        uc.mem_write(obj1, bytes(0x80))
        uc.mem_write(obj2, bytes(0x80))

        calls = []
        def f_26b2c(uc, address, size, user_data):
            a0 = uc.reg_read(UC_ARM_REG_R0)
            a1 = uc.reg_read(UC_ARM_REG_R1)
            a2 = uc.reg_read(UC_ARM_REG_R2)
            a3 = uc.reg_read(UC_ARM_REG_R3)
            calls.append((a0, a1, a2, a3))
            ret = obj1 if len(calls) == 1 else obj2
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_26b2c, None, FN_226B2C, FN_226B2C)

        sp_base = STACK_BASE + 0x8000
        sp_mem = bytearray(16)
        struct.pack_into("<I", sp_mem, 0, arg4)
        struct.pack_into("<f", sp_mem, 4, arg5)
        struct.pack_into("<f", sp_mem, 8, arg6)
        struct.pack_into("<I", sp_mem, 12, arg7)
        uc.mem_write(sp_base, bytes(sp_mem))

        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_R2, arg2)
        uc.reg_write(UC_ARM_REG_R3, arg3)
        uc.reg_write(UC_ARM_REG_SP, sp_base)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        r0 = uc.reg_read(UC_ARM_REG_R0)
        m1 = uc.mem_read(obj1, 0x60)
        m2 = uc.mem_read(obj2, 0x60)
        return r0, calls, m1, m2

    cases = [
        (10, 2, 0x1234, 0x5678, 5, 1.5, 2.5, 0),
        (20, 1, 0x9999, 0x8888, 3, 3.5, 4.5, 1),
    ]

    for c in cases:
        r_o = run_one(orig_code, *c)
        r_d = run_one(decomp_code, *c)
        assert r_o == r_d, f"23c4c4 mismatch on {c}"

    print("battle_func_0023c4c4: PASS")

def test_camp_func_0023e590():
    addr = 0x0023E590
    print(f"--- Testing camp_func_0023e590 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 164)
    tmp = ROOT / "build" / "test_31c_part05"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_0023e590", tmp)

    FN_2BF6D0 = 0x002BF6D0
    sym_map = {
        "func_002bf6d0": FN_2BF6D0,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, flag22: int, val38: int, val3c: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        self_addr = 0x10082000
        out1_addr = 0x10083000
        out2_addr = 0x10083004
        row_buf = 0x10084000

        self_mem = bytearray(0x50)
        self_mem[0x22] = flag22
        struct.pack_into("<i", self_mem, 0x38, val38)
        struct.pack_into("<I", self_mem, 0x3C, val3c)
        uc.mem_write(self_addr, bytes(self_mem))

        calls = []
        def f_bf6d0(uc, address, size, user_data):
            a0 = uc.reg_read(UC_ARM_REG_R0)
            a1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append((a0, a1))
            # return row buffer with s16 f8 = a1 + 10, fA = a1 + 20
            row_mem = bytearray(0x20)
            struct.pack_into("<hh", row_mem, 8, a1 + 10, a1 + 20)
            uc.mem_write(row_buf, bytes(row_mem))
            uc.reg_write(UC_ARM_REG_R0, row_buf)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_bf6d0, None, FN_2BF6D0, FN_2BF6D0)

        uc.reg_write(UC_ARM_REG_R0, self_addr)
        uc.reg_write(UC_ARM_REG_R1, out1_addr)
        uc.reg_write(UC_ARM_REG_R2, out2_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        o1 = struct.unpack("<i", uc.mem_read(out1_addr, 4))[0]
        o2 = struct.unpack("<i", uc.mem_read(out2_addr, 4))[0]
        return calls, o1, o2

    cases = [
        (1, 10, 0),
        (0, 20, 0),
        (0, 10, 1),
        (0, 2, 1),
        (0, 15, 1),
        (0, 16, 1),
    ]

    for c in cases:
        r_o = run_one(orig_code, *c)
        r_d = run_one(decomp_code, *c)
        assert r_o == r_d, f"23e590 mismatch on {c}: orig {r_o} vs decomp {r_d}"

    print("camp_func_0023e590: PASS")

def main():
    test_engine_func_0023963c()
    test_engine_func_0023abd4()
    test_func_0023bc5c()
    test_battle_func_0023c4c4()
    test_camp_func_0023e590()
    print("\nALL 5 FUNCTIONS IN LEAF_BATCH31_C PART 05 PASSED DIFFERENTIAL VERIFICATION!")

if __name__ == "__main__":
    main()
