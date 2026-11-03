#!/usr/bin/env python3
"""Differential test for batch 31 C part 15:
- engine_func_002ac614 (0x002AC614, 188 B)
- func_002ad4fc (0x002AD4FC, 164 B)
- engine_func_002aea7c (0x002AEA7C, 176 B)
- engine_func_002aeb78 (0x002AEB78, 168 B)
- func_002b0908 (0x002B0908, 176 B)
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
COMPILED_ST_VALUES = {}
SOURCE = ROOT / "src/engine/leaf_batch31_c.cpp"

with open(ORIG_BIN, "rb") as f:
    ORIG_DATA = f.read()

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS, COMPILED_ST_VALUES
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch31_c.o"
        compile_tu_armv6k(source, obj)
        COMPILED_FUNCTIONS = extract_elf_functions_detailed(obj)
        data = obj.read_bytes()
        e_shoff = struct.unpack_from('<I', data, 32)[0]
        e_shentsize = struct.unpack_from('<H', data, 46)[0]
        e_shnum = struct.unpack_from('<H', data, 48)[0]
        sections = [struct.unpack_from('<IIIIIIIIII', data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
        symtab_sec = [s for s in sections if s[1] == 2][0]
        strtab_sec = sections[symtab_sec[6]]
        strtab_data = data[strtab_sec[4]:strtab_sec[4]+strtab_sec[5]]
        count = symtab_sec[5] // 16
        for i in range(count):
            st_name, st_value, st_size, st_info, st_other, st_shndx = struct.unpack_from('<IIIBBH', data, symtab_sec[4] + i * 16)
            name = strtab_data[st_name:].split(b'\x00')[0].decode('ascii', errors='ignore')
            if name:
                COMPILED_ST_VALUES[name] = st_value
    return COMPILED_FUNCTIONS[func_name]

def stage_body(body: bytes, relocs, target_addr: int, symbol_map: dict[str, int], func_name: str = "") -> bytes:
    data = bytearray(body)
    st_val = COMPILED_ST_VALUES.get(func_name, 0)
    for reloc in relocs:
        sym = reloc.symbol_name
        if sym == "":
            inst = struct.unpack_from("<I", data, reloc.offset)[0]
            off_in_fn = inst - st_val
            actual_addr = target_addr + off_in_fn
            struct.pack_into("<I", data, reloc.offset, actual_addr)
            continue
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
    uc.mem_write(CODE_BASE, ORIG_DATA)
    uc.mem_map(0x00480000, 0x00100000)
    uc.mem_map(0x10000000, 0x00100000)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, unmapped_hook)

    val = uc.reg_read(UC_ARM_REG_C1_C0_2)
    val |= (0xF << 20)
    uc.reg_write(UC_ARM_REG_C1_C0_2, val)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return uc

def test_engine_func_002ac614():
    addr = 0x002AC614
    size = 188
    print(f"--- Testing engine_func_002ac614 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part15"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_002ac614", tmp)

    FN_14D04C = 0x0014D04C
    FN_14D080 = 0x0014D080
    FN_14D040 = 0x0014D040
    FN_14D174 = 0x0014D174
    FN_14D0BC = 0x0014D0BC
    FN_2A7FC4 = 0x002A7FC4
    FN_14D0F8 = 0x0014D0F8
    FN_14D14C = 0x0014D14C
    FN_14D120 = 0x0014D120
    FN_14D1E8 = 0x0014D1E8

    sym_map = {
        "func_0014d04c": FN_14D04C,
        "func_0014d080": FN_14D080,
        "func_0014d040": FN_14D040,
        "func_0014d174": FN_14D174,
        "func_0014d0bc": FN_14D0BC,
        "func_002a7fc4": FN_2A7FC4,
        "func_0014d0f8": FN_14D0F8,
        "func_0014d14c": FN_14D14C,
        "func_0014d120": FN_14D120,
        "func_0014d1e8": FN_14D1E8,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "engine_func_002ac614")

    # Mock container, table, handle, item_info
    CONT_ADDR = 0x10020000
    TABLE_ADDR = 0x10021000
    HANDLE_ADDR = 0x10022000
    ITEM_INFO_ADDR = 0x10023000
    OUT_ADDR = 0x10024000
    BC_SRC_ADDR = 0x10025000

    def hook_stubs(uc: Uc, index_val: int):
        def s_14d04c(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, HANDLE_ADDR)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_14d080(uc, address, size, user_data):
            uc.mem_write(ITEM_INFO_ADDR, struct.pack("<I", index_val))
            uc.reg_write(UC_ARM_REG_R0, ITEM_INFO_ADDR)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_14d040(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, TABLE_ADDR)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_14d174(uc, address, size, user_data):
            # return float 3.5 in s0
            uc.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", 3.5))[0])
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_14d0bc(uc, address, size, user_data):
            uc.mem_write(BC_SRC_ADDR, b"\x11\x22\x33\x44\x55")
            uc.reg_write(UC_ARM_REG_R0, BC_SRC_ADDR)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_14d0f8(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, 0xAA)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_14d14c(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, 0xBB)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_14d120(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, 0xCC)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_14d1e8(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, 0xDD)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, s_14d04c, None, FN_14D04C, FN_14D04C)
        uc.hook_add(UC_HOOK_CODE, s_14d080, None, FN_14D080, FN_14D080)
        uc.hook_add(UC_HOOK_CODE, s_14d040, None, FN_14D040, FN_14D040)
        uc.hook_add(UC_HOOK_CODE, s_14d174, None, FN_14D174, FN_14D174)
        uc.hook_add(UC_HOOK_CODE, s_14d0bc, None, FN_14D0BC, FN_14D0BC)
        uc.hook_add(UC_HOOK_CODE, s_14d0f8, None, FN_14D0F8, FN_14D0F8)
        uc.hook_add(UC_HOOK_CODE, s_14d14c, None, FN_14D14C, FN_14D14C)
        uc.hook_add(UC_HOOK_CODE, s_14d120, None, FN_14D120, FN_14D120)
        uc.hook_add(UC_HOOK_CODE, s_14d1e8, None, FN_14D1E8, FN_14D1E8)

    cases = [
        0,  # index 0 (valid)
        1,  # index 1 (valid)
        4,  # index 4 (valid)
        5,  # index 5 (index == max_count -> failure)
        10, # index 10 (index > max_count -> failure)
    ]

    def run_one(code, idx):
        uc = create_emulator()
        uc.mem_write(addr, code)
        hook_stubs(uc, idx)

        # Container: field_4 points to internal data
        uc.mem_write(CONT_ADDR, b"\x00" * 0x20)
        uc.mem_write(CONT_ADDR + 4, struct.pack("<I", 0x10020100))

        # Table at TABLE_ADDR:
        # [0] = max_count = 5
        # entries: 5 pairs of (u32, u32)
        uc.mem_write(TABLE_ADDR, struct.pack("<I", 5))
        for i in range(5):
            uc.mem_write(TABLE_ADDR + 4 + i * 8, struct.pack("<II", 0x1000 + i, 0x2000 + i))

        uc.mem_write(OUT_ADDR, b"\x00" * 0x30)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE)
        uc.reg_write(UC_ARM_REG_LR, 0x003F0000)
        uc.reg_write(UC_ARM_REG_R0, CONT_ADDR)
        uc.reg_write(UC_ARM_REG_R1, OUT_ADDR)
        uc.reg_write(UC_ARM_REG_R2, 10)
        uc.reg_write(UC_ARM_REG_R3, 20)
        uc.emu_start(addr, 0x003F0000, timeout=1000000)
        return uc.reg_read(UC_ARM_REG_R0), uc.mem_read(OUT_ADDR, 0x20)

    for idx in cases:
        ret_orig, out_orig = run_one(orig_code, idx)
        ret_decomp, out_decomp = run_one(decomp_code, idx)
        assert ret_orig == ret_decomp, f"Return mismatch in 002ac614 for idx {idx}: {ret_orig} != {ret_decomp}"
        assert out_orig == out_decomp, f"Output struct mismatch in 002ac614 for idx {idx}"

    print("PASS: engine_func_002ac614")

def test_func_002ad4fc():
    addr = 0x002AD4FC
    size = 164
    print(f"--- Testing func_002ad4fc ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part15"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_002ad4fc", tmp)

    decomp_code = stage_body(comp, relocs, addr, {}, "func_002ad4fc")

    OUT_ADDR = 0x10020000

    cases = [
        # (left, right, top, bottom, near, far)
        (-10.0, 10.0, -10.0, 10.0, 1.0, 100.0),
        (-1.5, 2.5, -3.0, 4.0, 0.5, 50.0),
        (-0.5, 0.5, -0.5, 0.5, 0.1, 10.0),
        (-100.0, 100.0, -50.0, 50.0, 10.0, 1000.0),
    ]

    def to_u32(f):
        return struct.unpack("<I", struct.pack("<f", f))[0]

    def run_one(code, left, right, top, bottom, near, far):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.mem_write(OUT_ADDR, b"\x00" * 0x40)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE)
        uc.reg_write(UC_ARM_REG_LR, 0x003F0000)
        uc.reg_write(UC_ARM_REG_R0, OUT_ADDR)
        uc.reg_write(UC_ARM_REG_S0, to_u32(left))
        uc.reg_write(UC_ARM_REG_S1, to_u32(right))
        uc.reg_write(UC_ARM_REG_S2, to_u32(top))
        uc.reg_write(UC_ARM_REG_S3, to_u32(bottom))
        uc.reg_write(UC_ARM_REG_S4, to_u32(near))
        uc.reg_write(UC_ARM_REG_S5, to_u32(far))

        uc.emu_start(addr, 0x003F0000, timeout=1000000)
        return uc.mem_read(OUT_ADDR, 0x40)

    for c in cases:
        out_orig = run_one(orig_code, *c)
        out_decomp = run_one(decomp_code, *c)
        floats_orig = struct.unpack("<16f", out_orig)
        floats_decomp = struct.unpack("<16f", out_decomp)
        for i in range(16):
            diff = abs(floats_orig[i] - floats_decomp[i])
            assert diff < 1e-6, f"Matrix mismatch at index {i}: {floats_orig[i]} != {floats_decomp[i]} for case {c}"

    print("PASS: func_002ad4fc")

def test_engine_func_002aea7c():
    addr = 0x002AEA7C
    size = 176
    print(f"--- Testing engine_func_002aea7c ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part15"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_002aea7c", tmp)

    FN_2C4360 = 0x002C4360
    sym_map = {
        "func_002c4360": FN_2C4360,
        "engine_func_002c4360": FN_2C4360,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "engine_func_002aea7c")

    MGR_PTR = 0x0044EA28
    SLOTS_BASE = 0x10020000

    def run_one(code, slot_idx, setup_fn):
        uc = create_emulator()
        uc.mem_write(addr, code)

        freed_ptrs = []
        def stub_free(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            freed_ptrs.append(r0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_free, None, FN_2C4360, FN_2C4360)

        # Write global manager pointer
        uc.mem_write(MGR_PTR, struct.pack("<I", SLOTS_BASE))
        # Clear slots
        uc.mem_write(SLOTS_BASE, b"\x00" * (0x18 * 4))

        setup_fn(uc, SLOTS_BASE + slot_idx * 0x18)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE)
        uc.reg_write(UC_ARM_REG_LR, 0x003F0000)
        uc.reg_write(UC_ARM_REG_R0, slot_idx)

        uc.emu_start(addr, 0x003F0000, timeout=1000000)
        slot_mem = uc.mem_read(SLOTS_BASE + slot_idx * 0x18, 0x18)
        return freed_ptrs, slot_mem

    def setup_case1(uc: Uc, slot_addr: int):
        # Empty slot
        pass

    def setup_case2(uc: Uc, slot_addr: int):
        # Primary container at 0x10030000
        # Child container at 0x10031000 with 2 nodes:
        # node 0 at 0x10032000, payload at 0x10033000
        # node 1 at 0x10032020, payload at 0x10033020
        # sub_obj at 0x10034000
        PRIMARY = 0x10030000
        CHILD = 0x10031000
        NODE0 = 0x10032000
        NODE1 = 0x10032020
        SUB_OBJ = 0x10034000

        uc.mem_write(slot_addr, struct.pack("<II", PRIMARY, CHILD))

        # Primary: field_0 = 0x10035000, field_8 = 0x10035020
        uc.mem_write(PRIMARY, struct.pack("<III", 0x10035000, 0, 0x10035020))

        # Child: sub_obj, head = NODE0
        uc.mem_write(CHILD, struct.pack("<II", SUB_OBJ, NODE0))

        # NODE0: payload 0x10033000, next NODE1
        uc.mem_write(NODE0 + 0x0C, struct.pack("<II", 0x10033000, NODE1))

        # NODE1: payload 0x10033020, next 0
        uc.mem_write(NODE1 + 0x0C, struct.pack("<II", 0x10033020, 0))

    for idx, setup in [(0, setup_case1), (2, setup_case2)]:
        free_orig, slot_orig = run_one(orig_code, idx, setup)
        free_decomp, slot_decomp = run_one(decomp_code, idx, setup)
        assert free_orig == free_decomp, f"Freed pointers mismatch in 002aea7c for case {idx}: {free_orig} != {free_decomp}"
        assert slot_orig == slot_decomp, f"Slot memory mismatch in 002aea7c for case {idx}"

    print("PASS: engine_func_002aea7c")

def test_engine_func_002aeb78():
    addr = 0x002AEB78
    size = 168
    print(f"--- Testing engine_func_002aeb78 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part15"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_002aeb78", tmp)

    FN_2A728C = 0x002A728C
    FN_2C4B30 = 0x002C4B30
    FN_2A71C0 = 0x002A71C0
    FN_2B96F0 = 0x002B96F0
    FN_14EC5C = 0x0014EC5C
    FN_14CAE4 = 0x0014CAE4
    FN_2A7170 = 0x002A7170
    FN_2A7144 = 0x002A7144

    sym_map = {
        "func_002a728c": FN_2A728C,
        "engine_func_002c4b30": FN_2C4B30,
        "engine_func_002a71c0": FN_2A71C0,
        "func_002b96f0": FN_2B96F0,
        "func_0014ec5c": FN_14EC5C,
        "func_0014cae4": FN_14CAE4,
        "func_002a7170": FN_2A7170,
        "func_002a7144": FN_2A7144,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "engine_func_002aeb78")

    ITEM_ADDR = 0x10040000

    def hook_stubs(uc: Uc, handle_ret: int, res_ret: int, item_ret: int, call_log: list):
        def s_2a728c(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, handle_ret & 0xFFFFFFFF)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_2a71c0(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, res_ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_2b96f0(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, item_ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_14ec5c(uc, address, size, user_data):
            call_log.append("14ec5c")
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_14cae4(uc, address, size, user_data):
            call_log.append("14cae4")
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_2a7170(uc, address, size, user_data):
            call_log.append("2a7170")
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_2a7144(uc, address, size, user_data):
            call_log.append("2a7144")
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, s_2a728c, None, FN_2A728C, FN_2A728C)
        uc.hook_add(UC_HOOK_CODE, s_2a71c0, None, FN_2A71C0, FN_2A71C0)
        uc.hook_add(UC_HOOK_CODE, s_2b96f0, None, FN_2B96F0, FN_2B96F0)
        uc.hook_add(UC_HOOK_CODE, s_14ec5c, None, FN_14EC5C, FN_14EC5C)
        uc.hook_add(UC_HOOK_CODE, s_14cae4, None, FN_14CAE4, FN_14CAE4)
        uc.hook_add(UC_HOOK_CODE, s_2a7170, None, FN_2A7170, FN_2A7170)
        uc.hook_add(UC_HOOK_CODE, s_2a7144, None, FN_2A7144, FN_2A7144)

    cases = [
        (-1, 0, 0),        # handle -1
        (5, 0, 0),         # res 0
        (5, 1, 0),         # item 0
        (5, 1, ITEM_ADDR), # success
    ]

    def run_one(code, handle_ret, res_ret, item_ret):
        uc = create_emulator()
        uc.mem_write(addr, code)
        call_log = []
        hook_stubs(uc, handle_ret, res_ret, item_ret, call_log)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE)
        uc.reg_write(UC_ARM_REG_LR, 0x003F0000)
        uc.reg_write(UC_ARM_REG_R0, 0x10020000)
        uc.reg_write(UC_ARM_REG_R1, 0x10021000)
        uc.reg_write(UC_ARM_REG_R2, 100)
        uc.reg_write(UC_ARM_REG_R3, 200)

        uc.emu_start(addr, 0x003F0000, timeout=1000000)
        return uc.reg_read(UC_ARM_REG_R0), call_log

    for c in cases:
        ret_orig, log_orig = run_one(orig_code, *c)
        ret_decomp, log_decomp = run_one(decomp_code, *c)
        assert ret_orig == ret_decomp, f"Return mismatch in 002aeb78 for case {c}: {hex(ret_orig)} != {hex(ret_decomp)}"
        assert log_orig == log_decomp, f"Call log mismatch in 002aeb78 for case {c}"

    print("PASS: engine_func_002aeb78")

def test_func_002b0908():
    addr = 0x002B0908
    size = 176
    print(f"--- Testing func_002b0908 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part15"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_002b0908", tmp)

    FN_2B0188 = 0x002B0188
    FN_2AF8D0 = 0x002AF8D0

    sym_map = {
        "ui_func_002b0188": FN_2B0188,
        "ui_func_002af8d0": FN_2AF8D0,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "func_002b0908")

    OBJ_ADDR = 0x10020000
    P4_ADDR = 0x10021000
    R3_ADDR = 0x10022000

    def hook_stubs(uc: Uc, recorded_packets: list):
        def s_2b0188(uc, address, size, user_data):
            # Return OBJ_ADDR
            uc.reg_write(UC_ARM_REG_R0, OBJ_ADDR)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_2af8d0(uc, address, size, user_data):
            # Args: r0 = obj, r1 = entry, r2 = packet
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            pkt = uc.mem_read(r2, 0x40)
            recorded_packets.append((r0, r1, pkt))
            # Return success code 42
            uc.reg_write(UC_ARM_REG_R0, 42)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, s_2b0188, None, FN_2B0188, FN_2B0188)
        uc.hook_add(UC_HOOK_CODE, s_2af8d0, None, FN_2AF8D0, FN_2AF8D0)

    cases = [
        # (arg0, arg2, arg3, arg4, arg5, arg6, arg7)
        (0x12, 1250, 0x55, 1.5, 0, 0, 2.5),       # arg5==0 && arg6==0 -> return 0
        (0x34, 0,    0x77, 2.0, 10, 20, 3.0),     # arg2 = 0
        (0x56, 1000, 0x88, 3.0, 11, 22, 4.0),     # arg2 = 1000 (rem = 0)
        (0x78, 1234, 0x99, 4.0, 12, 23, 5.0),     # arg2 = 1234 (rem = 234)
        (0x9A, 5678, 0xAA, 5.0, 13, 24, 6.0),     # arg2 = 5678 (rem = 678)
    ]

    def to_u32(f):
        return struct.unpack("<I", struct.pack("<f", f))[0]

    def run_one(code, arg0, arg2, arg3, arg4, arg5, arg6, arg7):
        uc = create_emulator()
        uc.mem_write(addr, code)
        packets = []
        hook_stubs(uc, packets)

        # Setup obj -> p4 -> r3
        uc.mem_write(OBJ_ADDR + 4, struct.pack("<I", P4_ADDR))
        uc.mem_write(P4_ADDR, struct.pack("<I", R3_ADDR))
        # Clear entries memory at R3_ADDR
        uc.mem_write(R3_ADDR, b"\x00" * (20 * 1000))

        sp = STACK_BASE
        # On stack: arg4 (float), arg5 (u32), arg6 (u32), arg7 (float)
        stk_data = struct.pack("<fIIf", arg4, arg5, arg6, arg7)
        uc.mem_write(sp, stk_data)

        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x003F0000)
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, 0x10050000) # arg1 (context)
        uc.reg_write(UC_ARM_REG_R2, arg2)
        uc.reg_write(UC_ARM_REG_R3, arg3)

        uc.emu_start(addr, 0x003F0000, timeout=1000000)
        return uc.reg_read(UC_ARM_REG_R0), packets

    for c in cases:
        ret_orig, pkts_orig = run_one(orig_code, *c)
        ret_decomp, pkts_decomp = run_one(decomp_code, *c)
        assert ret_orig == ret_decomp, f"Return mismatch in 002b0908 for case {c}: {ret_orig} != {ret_decomp}"
        assert pkts_orig == pkts_decomp, f"Packet mismatch in 002b0908 for case {c}"

    print("PASS: func_002b0908")

if __name__ == "__main__":
    test_engine_func_002ac614()
    test_func_002ad4fc()
    test_engine_func_002aea7c()
    test_engine_func_002aeb78()
    test_func_002b0908()
    print("\n>>> ALL PART 15 TESTS PASSED! <<<")
