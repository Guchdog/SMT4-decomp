#!/usr/bin/env python3
"""Differential test runner for leaf_batch32_c Part 16 candidates against code.bin.

Tests:
  - 0x002d0498: camp_func_002d0498 (452 B) & camp_func_002d0630 (44 B)
  - 0x002d18c8: ui_func_002d18c8 (468 B)
  - 0x002d3f60: script_vm_func_002d3f60 (444 B)
  - 0x002d85a4: script_vm_func_002d85a4 (424 B)
  - 0x002d88a0: script_vm_func_002d88a0 (760 B)
"""

import struct
import sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.arm_const import *
import unicorn

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "engine" / "leaf_batch32_c.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STACK_BASE = 0x0FFF0000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

BUILD_DIR = ROOT / "build" / "batch32_c_part16"

ORIG_DATA = CODE_BIN.read_bytes()

COMPILED_FUNCTIONS = None
COMPILED_ST_VALUES = {}
RODATA_ADDR = 0x10050000
RODATA_BYTES = b""

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path = BUILD_DIR, source: Path = SOURCE):
    global COMPILED_FUNCTIONS, COMPILED_ST_VALUES, RODATA_BYTES
    if COMPILED_FUNCTIONS is None:
        out.mkdir(parents=True, exist_ok=True)
        obj = out / "leaf_batch32_c.o"
        res = compile_tu_armv6k(source, obj, repo_root=ROOT)
        if res.returncode != 0:
            print("COMPILATION FAILED:")
            print(res.stderr)
            sys.exit(1)
        COMPILED_FUNCTIONS = extract_elf_functions_detailed(obj)
        data = obj.read_bytes()
        e_shoff = struct.unpack_from('<I', data, 32)[0]
        e_shentsize = struct.unpack_from('<H', data, 46)[0]
        e_shnum = struct.unpack_from('<H', data, 48)[0]
        sections = [struct.unpack_from('<IIIIIIIIII', data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
        shstr = sections[struct.unpack_from('<H', data, 50)[0]]
        shstrtab = data[shstr[4]:shstr[4]+shstr[5]]
        def get_sh_name(off):
            return shstrtab[off:].split(b'\x00')[0].decode('ascii')
        for s in sections:
            if get_sh_name(s[0]) == ".rodata":
                RODATA_BYTES = data[s[4]:s[4]+s[5]]
                break

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
            if 0 <= inst < len(RODATA_BYTES):
                actual_addr = RODATA_ADDR + inst
            else:
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

def create_emulator() -> Uc:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    try:
        uc.ctl_set_cpu_model(UC_CPU_ARM_11MPCORE)
    except Exception:
        pass
    try:
        uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    except Exception:
        pass
    try:
        uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    except Exception:
        pass
    uc.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc.mem_write(CODE_BASE, ORIG_DATA)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)
    uc.mem_map(0x10000000, 0x00100000, UC_PROT_READ | UC_PROT_WRITE)
    if RODATA_BYTES:
        uc.mem_write(RODATA_ADDR, RODATA_BYTES)
    return uc

CALL_2B9364 = 0x002B9364
CALL_293C98 = 0x00293C98
CALL_2C4B30 = 0x002C4B30
CALL_2B66EC = 0x002B66EC
CALL_2533CC = 0x002533CC
CALL_2D4E48 = 0x002D4E48
CALL_2533E4 = 0x002533E4
CALL_2D4E80 = 0x002D4E80
CALL_152AF8 = 0x00152AF8
CALL_2A7AA0 = 0x002A7AA0
CALL_25BE50 = 0x0025BE50
CALL_2A06C8 = 0x002A06C8
CALL_2B902C = 0x002B902C
CALL_2BFFBC = 0x002BFFBC
CALL_2C0BA8 = 0x002C0BA8
CALL_2899C4 = 0x002899C4
CALL_289640 = 0x00289640
CALL_249C70 = 0x00249C70
CALL_254514 = 0x00254514
CALL_2544FC = 0x002544FC
CALL_2B49D8 = 0x002B49D8
CALL_2A8A1C = 0x002A8A1C
CALL_2C0128 = 0x002C0128
CALL_25506C = 0x0025506C
CALL_2BD3EC = 0x002BD3EC
CALL_295904 = 0x00295904
CALL_2A8A08 = 0x002A8A08
CALL_2A89E4 = 0x002A89E4
CALL_2BD25C = 0x002BD25C

BASE_SYMS = {
    "camp_func_002b9364": CALL_2B9364,
    "ui_func_00293c98": CALL_293C98,
    "engine_func_002c4b30": CALL_2C4B30,
    "script_vm_func_002b66ec": CALL_2B66EC,
    "script_vm_func_002533cc": CALL_2533CC,
    "camp_func_002d4e48": CALL_2D4E48,
    "script_vm_func_002533e4": CALL_2533E4,
    "camp_func_002d4e80": CALL_2D4E80,
    "script_vm_func_00152af8": CALL_152AF8,
    "script_vm_func_002a7aa0": CALL_2A7AA0,
    "engine_func_0025be50": CALL_25BE50,
    "engine_func_002a06c8": CALL_2A06C8,
    "ui_func_002b902c": CALL_2B902C,
    "ui_func_002bffbc": CALL_2BFFBC,
    "script_vm_func_002c0ba8": CALL_2C0BA8,
    "script_vm_func_002899c4": CALL_2899C4,
    "engine_func_00289640": CALL_289640,
    "script_vm_func_00249c70": CALL_249C70,
    "ui_func_00254514": CALL_254514,
    "ui_func_002544fc": CALL_2544FC,
    "script_vm_func_002b49d8": CALL_2B49D8,
    "camp_func_002a8a1c": CALL_2A8A1C,
    "script_vm_func_002c0128": CALL_2C0128,
    "script_vm_func_0025506c": CALL_25506C,
    "script_vm_func_002bd3ec": CALL_2BD3EC,
    "script_vm_func_00295904": CALL_295904,
    "camp_func_002a8a08": CALL_2A8A08,
    "camp_func_002a89e4": CALL_2A89E4,
    "script_vm_func_002bd25c": CALL_2BD25C,
}

# -------------------------------------------------------------------------
# Test 1: camp_func_002d0498 & camp_func_002d0630 (0x002d0498)
# -------------------------------------------------------------------------
def test_camp_func_002d0498():
    ADDR = 0x002d0498
    ORIG_SIZE = 452
    orig_code = load_original_bytes(ADDR, ORIG_SIZE)
    comp_body, relocs = compile_function("camp_func_002d0498")
    comp_code = stage_body(comp_body, relocs, ADDR, BASE_SYMS, "camp_func_002d0498")

    RET_ADDR = 0x004F0000
    BX_LR = struct.pack("<I", 0xE12FFF1E)

    def pack_entry(id1, id2, id3, flag_a0, flag_a1):
        # id2: bits 0..14 of word 0
        # id3: bits 15..29 of word 0
        # flag_a0: bits 30..31 of word 0
        # flag_a1: bits 0..1 of word 1
        # id1: bits 2..16 of word 1
        w0 = (id2 & 0x7FFF) | ((id3 & 0x7FFF) << 15) | ((flag_a0 & 3) << 30)
        w1 = (flag_a1 & 3) | ((id1 & 0x7FFF) << 2)
        return struct.pack("<II", w0, w1)

    cases = [
        ("demon1_race_diff", pack_entry(10, 20, 30, 0, 0), pack_entry(11, 20, 30, 0, 0)),
        ("demon1_level_diff", pack_entry(10, 20, 30, 0, 0), pack_entry(12, 20, 30, 0, 0)),
        ("demon1_id_diff", pack_entry(10, 20, 30, 0, 0), pack_entry(13, 20, 30, 0, 0)),
        ("demon2_race_diff", pack_entry(10, 20, 30, 0, 0), pack_entry(10, 21, 30, 0, 0)),
        ("demon2_level_diff", pack_entry(10, 20, 30, 0, 0), pack_entry(10, 22, 30, 0, 0)),
        ("demon2_tie_breaker", pack_entry(10, 20, 30, 1, 0), pack_entry(10, 20, 30, 2, 0)),
        ("demon3_race_diff", pack_entry(10, 20, 30, 0, 0), pack_entry(10, 20, 31, 0, 0)),
        ("final_tie_breaker", pack_entry(10, 20, 30, 0, 1), pack_entry(10, 20, 30, 0, 2)),
        ("completely_equal", pack_entry(10, 20, 30, 1, 2), pack_entry(10, 20, 30, 1, 2)),
    ]

    for name, data_a, data_b in cases:
        def run_sim(code: bytes):
            uc = create_emulator()
            uc.mem_write(ADDR, code)
            uc.mem_write(RET_ADDR, BX_LR)

            DEMON_TABLE = 0x10050000
            # Setup demon database records:
            # id 10: race=5, level=30
            # id 11: race=6, level=30
            # id 12: race=5, level=40
            # id 13: race=5, level=30 (different id)
            # id 20: race=3, level=20
            # id 21: race=4, level=20
            # id 22: race=3, level=25
            # id 30: race=2, level=10
            # id 31: race=7, level=10
            demons = {
                10: (5, 30), 11: (6, 30), 12: (5, 40), 13: (5, 30),
                20: (3, 20), 21: (4, 20), 22: (3, 25),
                30: (2, 10), 31: (7, 10),
            }
            for d_id, (race, lvl) in demons.items():
                p = DEMON_TABLE + d_id * 16
                uc.mem_write(p, struct.pack("<BBBB", 0, 0, race, lvl))

            def hook_2b9364(uc_inst, address, size, user_data):
                d_id = uc_inst.reg_read(UC_ARM_REG_R0)
                ptr = DEMON_TABLE + (d_id * 16)
                uc_inst.reg_write(UC_ARM_REG_R0, ptr)

            uc.mem_write(CALL_2B9364, BX_LR)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2b9364, begin=CALL_2B9364, end=CALL_2B9364)

            A_ADDR = 0x10010000
            B_ADDR = 0x10010020
            uc.mem_write(A_ADDR, data_a)
            uc.mem_write(B_ADDR, data_b)

            uc.reg_write(UC_ARM_REG_R0, A_ADDR)
            uc.reg_write(UC_ARM_REG_R1, B_ADDR)
            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, RET_ADDR)

            uc.emu_start(ADDR, RET_ADDR, timeout=2000000)

            ret_r0 = uc.reg_read(UC_ARM_REG_R0)
            return struct.unpack("<i", struct.pack("<I", ret_r0))[0]

        orig_ret = run_sim(orig_code)
        comp_ret = run_sim(comp_code)

        assert orig_ret == comp_ret, f"{name}: ret mismatch (orig={orig_ret}, comp={comp_ret})"

    print(f"PASS: camp_func_002d0498 (all {len(cases)} cases passed)")

# -------------------------------------------------------------------------
# Test 2: ui_func_002d18c8 (0x002d18c8)
# -------------------------------------------------------------------------
def test_ui_func_002d18c8():
    ADDR = 0x002d18c8
    ORIG_SIZE = 468
    orig_code = load_original_bytes(ADDR, ORIG_SIZE)
    comp_body, relocs = compile_function("ui_func_002d18c8")
    comp_code = stage_body(comp_body, relocs, ADDR, BASE_SYMS, "ui_func_002d18c8")

    RET_ADDR = 0x004F0000
    BX_LR = struct.pack("<I", 0xE12FFF1E)

    cases = [
        ("flags_zero", 0x1000, 0, 10.0, 5.0, 1),
        ("self_f50_bit4", 0x20000, 0x10, 10.0, 5.0, 1),
        ("flag_20000_greater", 0x20000, 0, 10.0, 5.0, 1),
        ("flag_20000_lesser", 0x20000, 0, 2.0, 5.0, 1),
        ("flag_40000_lesser", 0x40000, 0, 2.0, 5.0, 1),
        ("flag_40000_greater", 0x40000, 0, 10.0, 5.0, 1),
        ("same_group_ignored", 0x20000, 0, 10.0, 5.0, 0), # group 0 matches self group 0
    ]

    for name, flags, self_f50, self_z, elem_z, elem_grp in cases:
        def run_sim(code: bytes):
            uc = create_emulator()
            uc.mem_write(ADDR, code)
            uc.mem_write(RET_ADDR, BX_LR)

            MGR_ADDR = 0x10020000
            LIST_ADDR = 0x10040000
            uc.mem_write(MGR_ADDR + 0x1E98, struct.pack("<I", LIST_ADDR))

            # ui_func_00293c98: returns MGR_ADDR
            uc.mem_write(CALL_293C98, struct.pack("<II", 0xE59F0000, 0xE12FFF1E) + struct.pack("<I", MGR_ADDR))

            # engine_func_002c4b30: zeroes memory
            def hook_2c4b30(uc_inst, address, size, user_data):
                p = uc_inst.reg_read(UC_ARM_REG_R0)
                sz = uc_inst.reg_read(UC_ARM_REG_R1)
                uc_inst.mem_write(p, b"\x00" * sz)

            uc.mem_write(CALL_2C4B30, BX_LR)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2c4b30, begin=CALL_2C4B30, end=CALL_2C4B30)

            # Setup widgets in list:
            # 50 records of 276 bytes starting at LIST_ADDR + 0x450
            widget_buf = bytearray(50 * 276 + 0x500)
            # Setup element 0:
            # +0x50: elem_f50 = 0x83
            # +0x62: elem_group = elem_grp
            # +0x0C: elem_z
            off0 = 0x450
            struct.pack_into("<I", widget_buf, off0 + 0x50, 0x83)
            struct.pack_into("<h", widget_buf, off0 + 0x62, elem_grp)
            struct.pack_into("<f", widget_buf, off0 + 0x0C, elem_z)
            uc.mem_write(LIST_ADDR, bytes(widget_buf))

            SELF_ADDR = 0x10010000
            self_buf = bytearray(0x80)
            struct.pack_into("<I", self_buf, 0x50, self_f50)
            struct.pack_into("<h", self_buf, 0x62, 0) # self group is 0
            struct.pack_into("<f", self_buf, 0x0C, self_z)
            uc.mem_write(SELF_ADDR, bytes(self_buf))

            uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
            uc.reg_write(UC_ARM_REG_R1, flags)
            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, RET_ADDR)

            uc.emu_start(ADDR, RET_ADDR, timeout=2000000)

            ret_r0 = uc.reg_read(UC_ARM_REG_R0)
            return ret_r0

        orig_ret = run_sim(orig_code)
        comp_ret = run_sim(comp_code)

        assert orig_ret == comp_ret, f"{name}: ret mismatch (orig={orig_ret}, comp={comp_ret})"

    print(f"PASS: ui_func_002d18c8 (all {len(cases)} cases passed)")

# -------------------------------------------------------------------------
# Test 3: script_vm_func_002d3f60 (0x002d3f60)
# -------------------------------------------------------------------------
def test_script_vm_func_002d3f60():
    ADDR = 0x002d3f60
    ORIG_SIZE = 576
    orig_code = load_original_bytes(ADDR, ORIG_SIZE)
    comp_body, relocs = compile_function("script_vm_func_002d3f60")
    comp_code = stage_body(comp_body, relocs, ADDR, BASE_SYMS, "script_vm_func_002d3f60")

    RET_ADDR = 0x004F0000
    BX_LR = struct.pack("<I", 0xE12FFF1E)

    cases = [
        ("state0_match_change", 0, 100, 200, 200, 5),
        ("state0_match_no_change", 0, 100, 200, 5, 5),
        ("state1_advance", 1, 0, 0, 0, 0),
        ("state2_clear_advance", 2, 0, 0, 0, 0),
        ("state3_alloc_reset", 3, 0, 0, 0, 2),
        ("state4_unhandled", 4, 0, 0, 0, 0),
    ]

    for name, init_state, param_f8, param_f0, old_218, new_val in cases:
        def run_sim(code: bytes):
            uc = create_emulator()
            uc.mem_write(ADDR, code)
            uc.mem_write(RET_ADDR, BX_LR)

            STATE_HOLDER_ADDR = 0x00447E88
            VM_CONFIG_ADDR = 0x0049F91C
            STATE_OBJ_ADDR = 0x10020000
            PARAM_ADDR = 0x10030000
            CHILD_OBJ_ADDR = 0x10040000

            uc.mem_write(STATE_HOLDER_ADDR, struct.pack("<I", STATE_OBJ_ADDR))

            # State object:
            # +0x164: child_ptr
            # +0x168: field_168
            # +0x16C: field_16C
            # +0x170: state
            state_buf = bytearray(0x200)
            struct.pack_into("<IIii", state_buf, 0x164, CHILD_OBJ_ADDR, 0, 0, init_state)
            uc.mem_write(STATE_OBJ_ADDR, bytes(state_buf))

            # VM config:
            # +0x218: val_218
            # +0x21C: val_21C
            # +0x3EC: 0xFFFFFFFF (-1)
            # +0x3F0: 0xFFFFFFFF (-1)
            vm_buf = bytearray(0x500)
            struct.pack_into("<ii", vm_buf, 0x218, old_218, 0)
            struct.pack_into("<ii", vm_buf, 0x3EC, -1, -1)
            # For state 3:
            struct.pack_into("<II", vm_buf, 0x298 + 2 * 8, CHILD_OBJ_ADDR, CHILD_OBJ_ADDR)
            uc.mem_write(VM_CONFIG_ADDR, bytes(vm_buf))

            # Child object at CHILD_OBJ_ADDR:
            # [0] = flags, [8] = inner_ptr
            # inner_ptr[0x2C] = inner2c_ptr
            # inner2c_ptr + 0x1F6 is cleared
            INNER_ADDR = 0x10050000
            INNER2C_ADDR = 0x10060000
            uc.mem_write(CHILD_OBJ_ADDR, struct.pack("<IIII", 0, 0, INNER_ADDR, 0))
            uc.mem_write(INNER_ADDR + 0x2C, struct.pack("<I", INNER2C_ADDR))
            uc.mem_write(INNER2C_ADDR, b"\xFF" * 0x300)

            # R4 param: [0] = param_f0, [8] = param_f8
            param_buf = bytearray(16)
            struct.pack_into("<H", param_buf, 0, param_f0)
            struct.pack_into("<H", param_buf, 8, param_f8)
            uc.mem_write(PARAM_ADDR, bytes(param_buf))

            # script_vm_func_002b66ec returns PARAM_ADDR
            uc.mem_write(CALL_2B66EC, struct.pack("<II", 0xE59F0000, 0xE12FFF1E) + struct.pack("<I", PARAM_ADDR))

            # script_vm_func_002533cc returns 1
            uc.mem_write(CALL_2533CC, struct.pack("<II", 0xE3A00001, 0xE12FFF1E))
            # camp_func_002d4e48(0) returns [param_f8, 77]
            E48_ADDR = 0x10070000
            uc.mem_write(E48_ADDR, struct.pack("<hh", param_f8, 77))
            uc.mem_write(CALL_2D4E48, struct.pack("<II", 0xE59F0000, 0xE12FFF1E) + struct.pack("<I", E48_ADDR))

            # script_vm_func_002533e4 returns 1
            uc.mem_write(CALL_2533E4, struct.pack("<II", 0xE3A00001, 0xE12FFF1E))
            # camp_func_002d4e80(0) returns [param_f0, new_val]
            E80_ADDR = 0x10080000
            uc.mem_write(E80_ADDR, struct.pack("<hh", param_f0, new_val))
            uc.mem_write(CALL_2D4E80, struct.pack("<II", 0xE59F0000, 0xE12FFF1E) + struct.pack("<I", E80_ADDR))

            uc.mem_write(CALL_152AF8, BX_LR)
            uc.mem_write(CALL_2A7AA0, BX_LR)
            # engine_func_0025be50 returns CHILD_OBJ_ADDR
            uc.mem_write(CALL_25BE50, struct.pack("<II", 0xE59F0000, 0xE12FFF1E) + struct.pack("<I", CHILD_OBJ_ADDR))
            uc.mem_write(CALL_2A06C8, BX_LR)

            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, RET_ADDR)

            uc.emu_start(ADDR, RET_ADDR, timeout=2000000)

            ret_r0 = uc.reg_read(UC_ARM_REG_R0)
            final_state = uc.mem_read(STATE_OBJ_ADDR + 0x164, 16)
            final_vm = uc.mem_read(VM_CONFIG_ADDR + 0x218, 8)
            return ret_r0, final_state, final_vm

        orig_ret, orig_st, orig_vm = run_sim(orig_code)
        comp_ret, comp_st, comp_vm = run_sim(comp_code)

        assert orig_ret == comp_ret, f"{name}: ret mismatch (orig={orig_ret}, comp={comp_ret})"
        assert orig_st == comp_st, f"{name}: state mismatch"
        assert orig_vm == comp_vm, f"{name}: vm mismatch"

    print(f"PASS: script_vm_func_002d3f60 (all {len(cases)} cases passed)")

# -------------------------------------------------------------------------
# Test 4: script_vm_func_002d85a4 (0x002d85a4)
# -------------------------------------------------------------------------
def test_script_vm_func_002d85a4():
    ADDR = 0x002d85a4
    ORIG_SIZE = 424
    orig_code = load_original_bytes(ADDR, ORIG_SIZE)
    comp_body, relocs = compile_function("script_vm_func_002d85a4")
    comp_code = stage_body(comp_body, relocs, ADDR, BASE_SYMS, "script_vm_func_002d85a4")

    RET_ADDR = 0x004F0000
    BX_LR = struct.pack("<I", 0xE12FFF1E)

    cases = [
        ("no_input", 0x100, [], 0, 0),
        ("right_pressed", 0x100, [3], 0, 0),
        ("down_pressed", 0x100, [6], 0, 0),
        ("up_wrap", 0, [5], 0, 0),
        ("action_btn0", 0x100, [], 1, 0),
        ("cancel_btn1", 0x100, [], 0, 1),
    ]

    for name, init_cur, pressed_btns, btn0, btn1 in cases:
        def run_sim(code: bytes):
            uc = create_emulator()
            uc.mem_write(ADDR, code)
            uc.mem_write(RET_ADDR, BX_LR)

            CURSOR_ADDR = 0x0043E360
            uc.mem_write(CURSOR_ADDR, struct.pack("<i", init_cur))

            # ui_func_002b902c(id): returns 1 if id in pressed_btns else 0
            def hook_2b902c(uc_inst, address, size, user_data):
                b_id = uc_inst.reg_read(UC_ARM_REG_R0)
                uc_inst.reg_write(UC_ARM_REG_R0, 1 if b_id in pressed_btns else 0)

            uc.mem_write(CALL_2B902C, BX_LR)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2b902c, begin=CALL_2B902C, end=CALL_2B902C)

            # ui_func_002bffbc(id): returns btn0 if id == 0 else btn1
            def hook_2bffbc(uc_inst, address, size, user_data):
                b_id = uc_inst.reg_read(UC_ARM_REG_R0)
                res = btn0 if b_id == 0 else btn1
                uc_inst.reg_write(UC_ARM_REG_R0, res)

            uc.mem_write(CALL_2BFFBC, BX_LR)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2bffbc, begin=CALL_2BFFBC, end=CALL_2BFFBC)

            uc.mem_write(CALL_2C0BA8, struct.pack("<II", 0xE3A00000, 0xE12FFF1E)) # returns 0
            uc.mem_write(CALL_2899C4, BX_LR)

            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, RET_ADDR)

            uc.emu_start(ADDR, RET_ADDR, timeout=2000000)

            ret_r0 = uc.reg_read(UC_ARM_REG_R0)
            final_cur = struct.unpack("<i", uc.mem_read(CURSOR_ADDR, 4))[0]
            return ret_r0, final_cur

        orig_ret, orig_c = run_sim(orig_code)
        comp_ret, comp_c = run_sim(comp_code)

        assert orig_ret == comp_ret, f"{name}: ret mismatch (orig={orig_ret}, comp={comp_ret})"
        assert orig_c == comp_c, f"{name}: cursor mismatch (orig={orig_c:#x}, comp={comp_c:#x})"

    print(f"PASS: script_vm_func_002d85a4 (all {len(cases)} cases passed)")

# -------------------------------------------------------------------------
# Test 5: script_vm_func_002d88a0 (0x002d88a0)
# -------------------------------------------------------------------------
def test_script_vm_func_002d88a0():
    ADDR = 0x002d88a0
    ORIG_SIZE = 760
    orig_code = load_original_bytes(ADDR, ORIG_SIZE)
    comp_body, relocs = compile_function("script_vm_func_002d88a0")
    comp_code = stage_body(comp_body, relocs, ADDR, BASE_SYMS, "script_vm_func_002d88a0")

    RET_ADDR = 0x004F0000
    BX_LR = struct.pack("<I", 0xE12FFF1E)

    cases = [
        ("mode0_camp1", 0, 1, 1, 0),
        ("mode0_camp0", 0, 0, 2, 0),
        ("mode1_format", 1, 0, 3, 0),
        ("mode2_loop_complete", 2, 0, 1, 2), # limit=2, starts at 0
        ("mode3_res1_reset", 3, 0, 1, 0),
        ("mode3_res0", 3, 0, 0, 0),
        ("mode4_invalid", 4, 0, 0, 0),
    ]

    for name, mode, camp_res, format_res, limit in cases:
        def run_sim(code: bytes):
            uc = create_emulator()
            uc.mem_write(ADDR, code)
            uc.mem_write(RET_ADDR, BX_LR)

            counters = {0: mode, 1: 0, 2: 0}

            # engine_func_00289640 returns 1 (already ready)
            uc.mem_write(CALL_289640, struct.pack("<II", 0xE3A00001, 0xE12FFF1E))
            uc.mem_write(CALL_249C70, BX_LR)

            def hook_2544fc(uc_inst, address, size, user_data):
                idx = uc_inst.reg_read(UC_ARM_REG_R0)
                uc_inst.reg_write(UC_ARM_REG_R0, counters.get(idx, 0))

            def hook_254514(uc_inst, address, size, user_data):
                idx = uc_inst.reg_read(UC_ARM_REG_R0)
                val = uc_inst.reg_read(UC_ARM_REG_R1)
                counters[idx] = val

            uc.mem_write(CALL_2544FC, BX_LR)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2544fc, begin=CALL_2544FC, end=CALL_2544FC)
            uc.mem_write(CALL_254514, BX_LR)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_254514, begin=CALL_254514, end=CALL_254514)

            TEXT_BUF = 0x10020000
            uc.mem_write(CALL_2B49D8, struct.pack("<II", 0xE59F0000, 0xE12FFF1E) + struct.pack("<I", TEXT_BUF))

            # camp_func_002a8a1c returns camp_res or limit
            lim_val = limit if mode == 2 else camp_res
            uc.mem_write(CALL_2A8A1C, struct.pack("<II", 0xE3A00000 | (lim_val & 0xFF), 0xE12FFF1E))
            uc.mem_write(CALL_2C0128, BX_LR)
            # script_vm_func_0025506c returns format_res
            uc.mem_write(CALL_25506C, struct.pack("<II", 0xE3A00000 | (format_res & 0xFF), 0xE12FFF1E))

            uc.mem_write(CALL_2BD3EC, struct.pack("<II", 0xE3A00042, 0xE12FFF1E)) # msg_id = 0x42
            uc.mem_write(CALL_295904, BX_LR)

            CAMP_BASE = 0x10030000
            # camp_base + 0x90F0 has demon indices
            uc.mem_write(CAMP_BASE + 0x90F0, b"\x00\x01\x02\x03\x04")
            uc.mem_write(CALL_2A8A08, struct.pack("<II", 0xE59F0000, 0xE12FFF1E) + struct.pack("<I", CAMP_BASE))

            DEMON_OBJ = 0x10040000
            uc.mem_write(DEMON_OBJ + 0x46, struct.pack("<H", 0x123))
            uc.mem_write(CALL_2A89E4, struct.pack("<II", 0xE59F0000, 0xE12FFF1E) + struct.pack("<I", DEMON_OBJ))
            uc.mem_write(CALL_2BD25C, struct.pack("<II", 0xE3A00099, 0xE12FFF1E))

            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, RET_ADDR)

            uc.emu_start(ADDR, RET_ADDR, timeout=2000000)

            ret_r0 = uc.reg_read(UC_ARM_REG_R0)
            return ret_r0, dict(counters)

        orig_ret, orig_cnt = run_sim(orig_code)
        comp_ret, comp_cnt = run_sim(comp_code)

        assert orig_ret == comp_ret, f"{name}: ret mismatch (orig={orig_ret}, comp={comp_ret})"
        assert orig_cnt == comp_cnt, f"{name}: counters mismatch (orig={orig_cnt}, comp={comp_cnt})"

    print(f"PASS: script_vm_func_002d88a0 (all {len(cases)} cases passed)")

if __name__ == "__main__":
    test_camp_func_002d0498()
    test_ui_func_002d18c8()
    test_script_vm_func_002d3f60()
    test_script_vm_func_002d85a4()
    test_script_vm_func_002d88a0()
    print("\nALL 5 CANDIDATES IN PART 16 PASSED DIFFERENTIAL VERIFICATION!")
