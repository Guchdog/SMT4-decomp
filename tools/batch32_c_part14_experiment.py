#!/usr/bin/env python3
"""Differential test runner for leaf_batch32_c Part 14 candidates against code.bin.

Tests:
  - 0x002bf558: func_002bf558 (368 B)
  - 0x002bf9f0: ui_func_002bf9f0 (664 B)
  - 0x002bfcb4: func_002bfcb4 (328 B)
  - 0x002c0c74: engine_func_002c0c74 (448 B)
  - 0x002c52f0: engine_func_002c52f0 (284 B)
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

BUILD_DIR = ROOT / "build" / "batch32_c_part14"

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
        compile_tu_armv6k(source, obj)
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
    uc.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc.mem_write(CODE_BASE, ORIG_DATA)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)
    uc.mem_map(0x10000000, 0x00100000, UC_PROT_READ | UC_PROT_WRITE)
    if RODATA_BYTES:
        uc.mem_write(RODATA_ADDR, RODATA_BYTES)
    return uc

CALL_126648 = 0x00126648
CALL_2B0188 = 0x002B0188
CALL_2AF8D0 = 0x002AF8D0
CALL_2C615C = 0x002C615C
CALL_2BDAC0 = 0x002BDAC0
CALL_2B1FC0 = 0x002B1FC0
CALL_2B1DFC = 0x002B1DFC
CALL_2B1C8C = 0x002B1C8C
CALL_2BC3C8 = 0x002BC3C8
CALL_1371EC = 0x001371EC
CALL_2C0C5C = 0x002C0C5C
CALL_2BAAA4 = 0x002BAAA4
CALL_2BA9D8 = 0x002BA9D8
CALL_2C0BCC = 0x002C0BCC
CALL_2BDD20 = 0x002BDD20
CALL_1375FC = 0x001375FC
CALL_125FD4 = 0x00125FD4
CALL_2C25F4 = 0x002C25F4
CALL_2BF148 = 0x002BF148
CALL_2BC9D8 = 0x002BC9D8
CALL_137314 = 0x00137314
CALL_2BF2B4 = 0x002BF2B4
CALL_137570 = 0x00137570

BASE_SYMS = {
    "func_00126648": CALL_126648,
    "ui_func_002b0188": CALL_2B0188,
    "ui_func_002af8d0": CALL_2AF8D0,
    "ui_func_002c615c": CALL_2C615C,
    "camp_func_002bdac0": CALL_2BDAC0,
    "ui_func_002b1fc0": CALL_2B1FC0,
    "ui_func_002b1dfc": CALL_2B1DFC,
    "ui_func_002b1c8c": CALL_2B1C8C,
    "battle_func_002bc3c8": CALL_2BC3C8,
    "battle_func_001371ec": CALL_1371EC,
    "ui_func_002c0c5c": CALL_2C0C5C,
    "func_002baaa4": CALL_2BAAA4,
    "camp_func_002ba9d8": CALL_2BA9D8,
    "engine_func_002c0bcc": CALL_2C0BCC,
    "battle_func_002bdd20": CALL_2BDD20,
    "engine_func_001375fc": CALL_1375FC,
    "AsdGxCommandList_func_00125fd4": CALL_125FD4,
    "engine_func_002c25f4": CALL_2C25F4,
    "battle_func_002bf148": CALL_2BF148,
    "engine_func_002bc9d8": CALL_2BC9D8,
    "engine_func_00137314": CALL_137314,
    "battle_func_002bf2b4": CALL_2BF2B4,
    "engine_func_00137570": CALL_137570,
}

BX_LR = struct.pack("<I", 0xE12FFF1E)

# -----------------------------------------------------------------------------
# Function 1: func_002bf558 (368 B)
# -----------------------------------------------------------------------------
def test_func_002bf558():
    addr = 0x002BF558
    size = 368
    fn_name = "func_002bf558"
    orig_code = load_original_bytes(addr, size)
    comp_body, relocs = compile_function(fn_name)
    comp_addr = 0x003D0000

    cases = [
        {"null_r5": True, "count": 0},
        {"null_r5": False, "count": 0},
        {"null_r5": False, "count": 2, "type": 0, "flag": 1},
        {"null_r5": False, "count": 2, "type": 0, "flag": 0},
        {"null_r5": False, "count": 3, "type": 1, "flag": 0},
    ]

    for tc in cases:
        def run_one(is_comp: bool):
            uc = create_emulator()
            target = comp_addr if is_comp else addr
            if is_comp:
                body = stage_body(comp_body, relocs, comp_addr, BASE_SYMS, fn_name)
                uc.mem_write(comp_addr, body)

            uc.mem_write(CALL_126648, BX_LR)
            uc.mem_write(CALL_2B0188, BX_LR)
            uc.mem_write(CALL_2AF8D0, BX_LR)

            calls_2af8d0 = []

            # Set up mock objects in memory
            r5_buf = 0x10020000
            entries_buf = 0x10020100
            sheet_buf = 0x10020400
            sheet_sub_ptr = 0x10020500
            sheet_sub = 0x10020600
            quad_buf = 0x10020800

            def hook_126648(mu, address, size, user_data):
                if tc["null_r5"]:
                    mu.reg_write(UC_ARM_REG_R0, 0)
                else:
                    mu.reg_write(UC_ARM_REG_R0, r5_buf)

            def hook_2b0188(mu, address, size, user_data):
                mu.reg_write(UC_ARM_REG_R0, sheet_buf)

            def hook_2af8d0(mu, address, size, user_data):
                r0 = mu.reg_read(UC_ARM_REG_R0)
                r1 = mu.reg_read(UC_ARM_REG_R1)
                r2 = mu.reg_read(UC_ARM_REG_R2)
                sp_data = struct.unpack("<12I", mu.mem_read(r2, 48))
                calls_2af8d0.append((r0, r1, sp_data))

            uc.hook_add(unicorn.UC_HOOK_CODE, hook_126648, begin=CALL_126648, end=CALL_126648)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2b0188, begin=CALL_2B0188, end=CALL_2B0188)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2af8d0, begin=CALL_2AF8D0, end=CALL_2AF8D0)

            # Initialize r5: [r5 + 4] = count, [r5 + 0xC] = entries_buf
            uc.mem_write(r5_buf + 4, struct.pack("<I", tc["count"]))
            uc.mem_write(r5_buf + 0x0C, struct.pack("<I", entries_buf))

            # Entries: each 20 bytes (e0, e1, e2, e3, e4)
            for i in range(tc["count"]):
                uc.mem_write(entries_buf + i * 20, struct.pack("<IIiii", 1 + i, 200 + i * 10, 10 + i, 20 + i, 30 + i))

            # Sheet: [sheet + 4] = sheet_sub_ptr; *sheet_sub_ptr = sheet_sub
            uc.mem_write(sheet_buf + 4, struct.pack("<I", sheet_sub_ptr))
            uc.mem_write(sheet_sub_ptr, struct.pack("<I", sheet_sub))

            # Sub-entries: each 20 bytes: [sub + 0xC] = quad_buf
            for rem in range(50):
                uc.mem_write(sheet_sub + rem * 20 + 0x0C, struct.pack("<I", quad_buf + rem * 32))
                # Quad at quad_buf: [quad] = x (h), [quad + 2] = y (h), [quad + 4] = type (h), [quad + 0xC] = flag (b)
                uc.mem_write(quad_buf + rem * 32, struct.pack("<hhhh", 50, 60, tc.get("type", 0), 0))
                uc.mem_write(quad_buf + rem * 32 + 0x0C, bytes([tc.get("flag", 0)]))

            # Registers & Stack: 6 args
            # r0, r1, r2, r3, sp[0] (arg4), sp[4] (arg5)
            uc.reg_write(UC_ARM_REG_R0, 0x100)
            uc.reg_write(UC_ARM_REG_R1, 0x200)
            uc.reg_write(UC_ARM_REG_R2, 0x300)
            uc.reg_write(UC_ARM_REG_R3, 40)
            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.mem_write(STACK_TOP, struct.pack("<ii", 50, 60))
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)
            uc.reg_write(UC_ARM_REG_R4, 0x11111111)
            uc.reg_write(UC_ARM_REG_R5, 0x22222222)
            uc.reg_write(UC_ARM_REG_R6, 0x33333333)
            uc.reg_write(UC_ARM_REG_R7, 0x44444444)
            uc.reg_write(UC_ARM_REG_R8, 0x55555555)
            uc.reg_write(UC_ARM_REG_SB, 0x66666666)
            uc.reg_write(UC_ARM_REG_SL, 0x77777777)
            uc.reg_write(UC_ARM_REG_FP, 0x88888888)

            uc.emu_start(target, 0xF0000000, timeout=2000000)

            ret = uc.reg_read(UC_ARM_REG_R0)
            regs = {
                "r4": uc.reg_read(UC_ARM_REG_R4),
                "r5": uc.reg_read(UC_ARM_REG_R5),
                "r6": uc.reg_read(UC_ARM_REG_R6),
                "r7": uc.reg_read(UC_ARM_REG_R7),
                "r8": uc.reg_read(UC_ARM_REG_R8),
                "sb": uc.reg_read(UC_ARM_REG_SB),
                "sl": uc.reg_read(UC_ARM_REG_SL),
                "fp": uc.reg_read(UC_ARM_REG_FP),
                "sp": uc.reg_read(UC_ARM_REG_SP),
            }
            return ret, calls_2af8d0, regs

        o_ret, o_calls, o_regs = run_one(False)
        c_ret, c_calls, c_regs = run_one(True)

        assert o_ret == c_ret, f"tc={tc}: ret mismatch: orig={o_ret} comp={c_ret}"
        assert o_calls == c_calls, f"tc={tc}: calls mismatch: orig={o_calls} comp={c_calls}"
        for r in ["r4", "r5", "r6", "r7", "r8", "sb", "sl", "fp", "sp"]:
            assert o_regs[r] == c_regs[r], f"tc={tc}: {r} mismatch"

    print("PASS: func_002bf558 (all 5 cases passed)")

# -----------------------------------------------------------------------------
# Function 2: ui_func_002bf9f0 (664 B)
# -----------------------------------------------------------------------------
def test_ui_func_002bf9f0():
    addr = 0x002BF9F0
    size = 664
    fn_name = "ui_func_002bf9f0"
    orig_code = load_original_bytes(addr, size)
    comp_body, relocs = compile_function(fn_name)
    comp_addr = 0x003D0000

    cases = [
        {"null_obj": True},
        {"f04": -1, "f08": -1},
        {"f04": 1, "f08": -1, "b86": 1},
        {"f04": 1, "f08": 1, "b86": 0, "interpolate": True, "dir": 0},
        {"f04": 1, "f08": 1, "b86": 0, "interpolate": True, "dir": 1},
        {"f04": 1, "f08": 1, "b86": 0, "interpolate": False, "loop": 1, "dir": 0},
        {"f04": 1, "f08": 1, "b86": 0, "interpolate": False, "loop": 0, "dir": 0, "next_cmd": -1},
        {"f04": 1, "f08": 1, "b86": 0, "interpolate": False, "loop": 0, "dir": 0, "next_cmd": -2},
        {"f04": 1, "f08": 1, "b86": 0, "interpolate": False, "loop": 0, "dir": 0, "next_cmd": 5},
    ]

    for tc in cases:
        def run_one(is_comp: bool):
            uc = create_emulator()
            target = comp_addr if is_comp else addr
            if is_comp:
                body = stage_body(comp_body, relocs, comp_addr, BASE_SYMS, fn_name)
                uc.mem_write(comp_addr, body)

            uc.mem_write(CALL_2C615C, BX_LR)
            uc.mem_write(CALL_2BDAC0, BX_LR)
            uc.mem_write(CALL_2B1FC0, BX_LR)
            uc.mem_write(CALL_2B1DFC, BX_LR)
            uc.mem_write(CALL_2B1C8C, BX_LR)

            calls_bdac0 = []

            # Implement real ui_func_002c615c: r0 / r1
            def hook_2c615c(mu, address, size, user_data):
                num = mu.reg_read(UC_ARM_REG_R0)
                den = mu.reg_read(UC_ARM_REG_R1)
                # signed division
                s_num = struct.unpack("<i", struct.pack("<I", num))[0]
                s_den = struct.unpack("<i", struct.pack("<I", den))[0]
                q = int(s_num / s_den) if s_den != 0 else 0
                mu.reg_write(UC_ARM_REG_R0, q & 0xFFFFFFFF)

            def hook_bdac0(mu, address, size, user_data):
                r0 = mu.reg_read(UC_ARM_REG_R0)
                r1 = mu.reg_read(UC_ARM_REG_R1)
                r2 = mu.reg_read(UC_ARM_REG_R2)
                calls_bdac0.append((r0, r1, r2))

            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2c615c, begin=CALL_2C615C, end=CALL_2C615C)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_bdac0, begin=CALL_2BDAC0, end=CALL_2BDAC0)

            obj = 0x10020000
            p4c = 0x10020200
            p78 = 0x10020400

            if not tc.get("null_obj", False):
                uc.mem_write(obj, b"\x00" * 0x100)
                uc.mem_write(obj + 4, struct.pack("<ii", tc.get("f04", 0), tc.get("f08", 0)))
                uc.mem_write(obj + 0x86, bytes([tc.get("b86", 0)]))
                uc.mem_write(obj + 0x4C, struct.pack("<I", p4c))
                r3_idx = 0
                r2_cur = 5 if tc.get("interpolate", False) else 10
                uc.mem_write(obj + 0x50, struct.pack("<hh", r3_idx, r2_cur))
                uc.mem_write(obj + 0x54, bytes([tc.get("dir", 0)]))
                uc.mem_write(obj + 0x84, bytes([1]))
                uc.mem_write(obj + 0x78, struct.pack("<I", p78))
                uc.mem_write(obj + 0x7C, struct.pack("<h", 0))

                # Step at p4c: [x0, y0, x1, y1, duration, loop_flag]
                uc.mem_write(p4c, struct.pack("<hhhhhB", 10, 20, 100, 200, 10, tc.get("loop", 0)))

                # Script sequence at p78: entries of 28 bytes
                next_cmd = tc.get("next_cmd", -1)
                uc.mem_write(p78, struct.pack("<ib", 1, 2))
                uc.mem_write(p78 + 28, struct.pack("<ib", next_cmd, 3))

                # Extra flag bytes
                uc.mem_write(obj + 0x87, bytes([1]))
                uc.mem_write(obj + 0x88, bytes([1]))
                uc.mem_write(obj + 0x89, bytes([1]))

            arg_obj = 0 if tc.get("null_obj", False) else obj
            uc.reg_write(UC_ARM_REG_R0, arg_obj)
            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)
            uc.reg_write(UC_ARM_REG_R4, 0x11111111)
            uc.reg_write(UC_ARM_REG_R5, 0x22222222)
            uc.reg_write(UC_ARM_REG_R6, 0x33333333)
            uc.reg_write(UC_ARM_REG_R7, 0x44444444)
            uc.reg_write(UC_ARM_REG_R8, 0x55555555)

            uc.emu_start(target, 0xF0000000, timeout=2000000)

            ret = uc.reg_read(UC_ARM_REG_R0)
            obj_state = uc.mem_read(obj, 0x90) if not tc.get("null_obj", False) else b""
            regs = {
                "r4": uc.reg_read(UC_ARM_REG_R4),
                "r5": uc.reg_read(UC_ARM_REG_R5),
                "r6": uc.reg_read(UC_ARM_REG_R6),
                "r7": uc.reg_read(UC_ARM_REG_R7),
                "r8": uc.reg_read(UC_ARM_REG_R8),
                "sp": uc.reg_read(UC_ARM_REG_SP),
            }
            return ret, obj_state, calls_bdac0, regs

        o_ret, o_state, o_calls, o_regs = run_one(False)
        c_ret, c_state, c_calls, c_regs = run_one(True)

        assert o_ret == c_ret, f"tc={tc}: ret mismatch: orig={o_ret} comp={c_ret}"
        assert o_state == c_state, f"tc={tc}: state mismatch"
        assert o_calls == c_calls, f"tc={tc}: calls mismatch"
        for r in ["r4", "r5", "r6", "r7", "r8", "sp"]:
            assert o_regs[r] == c_regs[r], f"tc={tc}: {r} mismatch"

    print("PASS: ui_func_002bf9f0 (all 9 cases passed)")

# -----------------------------------------------------------------------------
# Function 3: func_002bfcb4 (328 B)
# -----------------------------------------------------------------------------
def test_func_002bfcb4():
    addr = 0x002BFCB4
    size = 328
    fn_name = "func_002bfcb4"
    orig_code = load_original_bytes(addr, size)
    comp_body, relocs = compile_function(fn_name)
    comp_addr = 0x003D0000

    cases = [
        {"mode": 0, "val_c0": 0x500, "b_val": 0, "f1f8": 0x8058},
        {"mode": 1, "val_c0": 0x100, "b_val": 0, "f1f8": 0x8000},
        {"mode": 1, "val_c0": 0x100, "b_val": 1, "f1f8": 0x8058},
        {"mode": 2, "val_c0": 0x100, "b_val": 0, "f1f8": 0x8058},
        {"mode": 2, "val_c0": 0x100, "b_val": 1, "f1f8": 0x8000},
    ]

    for tc in cases:
        def run_one(is_comp: bool):
            uc = create_emulator()
            target = comp_addr if is_comp else addr
            if is_comp:
                body = stage_body(comp_body, relocs, comp_addr, BASE_SYMS, fn_name)
                uc.mem_write(comp_addr, body)

            uc.mem_write(CALL_2BC3C8, BX_LR)
            uc.mem_write(CALL_1371EC, BX_LR)

            calls_1371ec = []

            def hook_1371ec(mu, address, size, user_data):
                r0 = mu.reg_read(UC_ARM_REG_R0)
                r1 = mu.reg_read(UC_ARM_REG_R1)
                r2 = mu.reg_read(UC_ARM_REG_R2)
                r3 = mu.reg_read(UC_ARM_REG_R3)
                sp = mu.reg_read(UC_ARM_REG_SP)
                sp_args = struct.unpack("<III", mu.mem_read(sp, 12))
                calls_1371ec.append((r0, r1, r2, r3, sp_args))

            uc.hook_add(unicorn.UC_HOOK_CODE, hook_1371ec, begin=CALL_1371EC, end=CALL_1371EC)

            # Base at 0x004E39E0
            # [base + 0x88] desc for mode 0, 1: desc + 0x30 = r6, desc + 0x34 = sb, desc + 8 = f08
            uc.mem_write(0x004E39E0 + 0x88 + 8, struct.pack("<I", 0x1111))
            uc.mem_write(0x004E39E0 + 0x88 + 0x30, struct.pack("<II", 100, 200))
            # [base + 0x100] desc for mode 2
            uc.mem_write(0x004E39E0 + 0x100 + 8, struct.pack("<I", 0x2222))
            uc.mem_write(0x004E39E0 + 0x100 + 0x30, struct.pack("<II", 300, 400))

            # val_c0 at base + 0xC0 or base + 0x138
            uc.mem_write(0x004E39E0 + 0xC0, struct.pack("<I", tc["val_c0"]))
            uc.mem_write(0x004E39E0 + 0x138, struct.pack("<I", tc["val_c0"]))

            # b_val at 0x004E3BE0, 0x004E3BE1
            uc.mem_write(0x004E3BE0, bytes([tc["b_val"], tc["b_val"]]))

            # ctx struct
            ctx = 0x10020000
            uc.mem_write(ctx, b"\x00" * 0x200)
            uc.mem_write(ctx + 0x14, struct.pack("<i", 80))
            uc.mem_write(ctx + 0x24, struct.pack("<I", 0x5555))
            uc.mem_write(0x004E39E0 + 0x1F8, struct.pack("<I", tc["f1f8"]))

            uc.reg_write(UC_ARM_REG_R0, tc["mode"])
            uc.reg_write(UC_ARM_REG_R1, ctx)
            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)
            uc.reg_write(UC_ARM_REG_R4, 0x11111111)
            uc.reg_write(UC_ARM_REG_R5, 0x22222222)
            uc.reg_write(UC_ARM_REG_R6, 0x33333333)
            uc.reg_write(UC_ARM_REG_R7, 0x44444444)
            uc.reg_write(UC_ARM_REG_R8, 0x55555555)
            uc.reg_write(UC_ARM_REG_SB, 0x66666666)
            uc.reg_write(UC_ARM_REG_SL, 0x77777777)

            uc.emu_start(target, 0xF0000000, timeout=2000000)

            ret = uc.reg_read(UC_ARM_REG_R0)
            regs = {
                "r4": uc.reg_read(UC_ARM_REG_R4),
                "r5": uc.reg_read(UC_ARM_REG_R5),
                "r6": uc.reg_read(UC_ARM_REG_R6),
                "r7": uc.reg_read(UC_ARM_REG_R7),
                "r8": uc.reg_read(UC_ARM_REG_R8),
                "sb": uc.reg_read(UC_ARM_REG_SB),
                "sl": uc.reg_read(UC_ARM_REG_SL),
                "sp": uc.reg_read(UC_ARM_REG_SP),
            }
            return ret, calls_1371ec, regs

        o_ret, o_calls, o_regs = run_one(False)
        c_ret, c_calls, c_regs = run_one(True)

        assert o_ret == c_ret, f"tc={tc}: ret mismatch: orig={o_ret} comp={c_ret}"
        assert o_calls == c_calls, f"tc={tc}: calls mismatch: orig={o_calls} comp={c_calls}"
        for r in ["r4", "r5", "r6", "r7", "r8", "sb", "sl", "sp"]:
            assert o_regs[r] == c_regs[r], f"tc={tc}: {r} mismatch"

    print("PASS: func_002bfcb4 (all 6 cases passed)")

# -----------------------------------------------------------------------------
# Function 4: engine_func_002c0c74 (448 B)
# -----------------------------------------------------------------------------
def test_engine_func_002c0c74():
    addr = 0x002C0C74
    size = 448
    fn_name = "engine_func_002c0c74"
    orig_code = load_original_bytes(addr, size)
    comp_body, relocs = compile_function(fn_name)
    comp_addr = 0x003D0000

    cases = [
        {"r8": 0, "r1_low": 3, "val12": 0},
        {"r8": 1, "r1_low": 1, "val12": 0, "v": 10},
        {"r8": 0, "r1_low": 0, "val12": 500, "val2": 150, "thresh": 100, "v": 20},
        {"r8": 0, "r1_low": 0, "val12": 500, "val2": 50, "thresh": 100, "v": 20},
        {"r8": 0, "r1_low": 1, "val12": 1500, "rnd": 50, "flag2": 0},
        {"r8": 1, "r1_low": 0, "val12": 2000, "rnd": 5000, "flag2": 0},
        {"r8": 0, "r1_low": 1, "val12": 1500, "rnd": 50, "flag2": 1},
    ]

    for tc in cases:
        def run_one(is_comp: bool):
            uc = create_emulator()
            target = comp_addr if is_comp else addr
            if is_comp:
                body = stage_body(comp_body, relocs, comp_addr, BASE_SYMS, fn_name)
                uc.mem_write(comp_addr, body)

            uc.mem_write(CALL_2C0C5C, BX_LR)
            uc.mem_write(CALL_2BAAA4, BX_LR)
            uc.mem_write(CALL_2BA9D8, BX_LR)
            uc.mem_write(CALL_2C0BCC, BX_LR)

            r4_buf = 0x10020000
            r0_res = 0x10020100

            def hook_c0c5c(mu, address, size, user_data):
                mu.reg_write(UC_ARM_REG_R0, tc["r8"])

            def hook_baaa4(mu, address, size, user_data):
                mu.reg_write(UC_ARM_REG_R0, r4_buf)

            def hook_ba9d8(mu, address, size, user_data):
                mu.reg_write(UC_ARM_REG_R0, r0_res)

            def hook_c0bcc(mu, address, size, user_data):
                mu.reg_write(UC_ARM_REG_R0, tc.get("thresh", tc.get("rnd", 0)))

            uc.hook_add(unicorn.UC_HOOK_CODE, hook_c0c5c, begin=CALL_2C0C5C, end=CALL_2C0C5C)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_baaa4, begin=CALL_2BAAA4, end=CALL_2BAAA4)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_ba9d8, begin=CALL_2BA9D8, end=CALL_2BA9D8)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_c0bcc, begin=CALL_2C0BCC, end=CALL_2C0BCC)

            # Initialize r4
            uc.mem_write(r4_buf, struct.pack("<HBB", 100, tc.get("flag2", 0), tc["r1_low"] | 0x40))

            # Initialize r0_res: [0xE] = r6_val
            uc.mem_write(r0_res + 0x0E, struct.pack("<h", 200))
            r1_ptr = r0_res + tc["r8"] * 6
            r5_ptr = r1_ptr + 0x10
            uc.mem_write(r1_ptr + 0x12, struct.pack("<h", tc["val12"]))
            uc.mem_write(r5_ptr, struct.pack("<hhhh", tc.get("v", 300), tc.get("val2", 0), 5, 0))

            # Scan table for high val12 case:
            for k in range(5):
                uc.mem_write(r0_res + 0x12 + k * 6, struct.pack("<h", 1100 + k * 50))

            uc.reg_write(UC_ARM_REG_R0, 1)
            uc.reg_write(UC_ARM_REG_R1, 2)
            uc.reg_write(UC_ARM_REG_R2, 0)
            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)
            uc.reg_write(UC_ARM_REG_R4, 0x11111111)
            uc.reg_write(UC_ARM_REG_R5, 0x22222222)
            uc.reg_write(UC_ARM_REG_R6, 0x33333333)
            uc.reg_write(UC_ARM_REG_R7, 0x44444444)
            uc.reg_write(UC_ARM_REG_R8, 0x55555555)
            uc.reg_write(UC_ARM_REG_SB, 0x66666666)
            uc.reg_write(UC_ARM_REG_SL, 0x77777777)
            uc.reg_write(UC_ARM_REG_FP, 0x88888888)

            uc.emu_start(target, 0xF0000000, timeout=2000000)

            ret = uc.reg_read(UC_ARM_REG_R0)
            r4_state = uc.mem_read(r4_buf, 8)
            regs = {
                "r4": uc.reg_read(UC_ARM_REG_R4),
                "r5": uc.reg_read(UC_ARM_REG_R5),
                "r6": uc.reg_read(UC_ARM_REG_R6),
                "r7": uc.reg_read(UC_ARM_REG_R7),
                "r8": uc.reg_read(UC_ARM_REG_R8),
                "sb": uc.reg_read(UC_ARM_REG_SB),
                "sl": uc.reg_read(UC_ARM_REG_SL),
                "fp": uc.reg_read(UC_ARM_REG_FP),
                "sp": uc.reg_read(UC_ARM_REG_SP),
            }
            return ret, r4_state, regs

        o_ret, o_state, o_regs = run_one(False)
        c_ret, c_state, c_regs = run_one(True)

        assert o_ret == c_ret, f"tc={tc}: ret mismatch: orig={o_ret} comp={c_ret}"
        assert o_state == c_state, f"tc={tc}: state mismatch: orig={o_state.hex()} comp={c_state.hex()}"
        for r in ["r4", "r5", "r6", "r7", "r8", "sb", "sl", "fp", "sp"]:
            assert o_regs[r] == c_regs[r], f"tc={tc}: {r} mismatch"

    print("PASS: engine_func_002c0c74 (all 7 cases passed)")

# -----------------------------------------------------------------------------
# Function 5: engine_func_002c52f0 (284 B)
# -----------------------------------------------------------------------------
def test_engine_func_002c52f0():
    addr = 0x002C52F0
    size = 284
    fn_name = "engine_func_002c52f0"
    orig_code = load_original_bytes(addr, size)
    comp_body, relocs = compile_function(fn_name)
    comp_addr = 0x003D0000

    cases = [
        {"count": 1, "flag": 0},
        {"count": 1, "flag": 1, "f14": 0x1000},
        {"count": 1, "flag": 1, "f14": 0},
        {"count": 3, "flag": 0},
        {"count": 5, "flag": 1},
    ]

    for tc in cases:
        def run_one(is_comp: bool):
            uc = create_emulator()
            target = comp_addr if is_comp else addr
            if is_comp:
                body = stage_body(comp_body, relocs, comp_addr, BASE_SYMS, fn_name)
                uc.mem_write(comp_addr, body)

            uc.mem_write(CALL_2BDD20, BX_LR)
            uc.mem_write(CALL_1375FC, BX_LR)
            uc.mem_write(CALL_125FD4, BX_LR)
            uc.mem_write(CALL_2C25F4, BX_LR)
            uc.mem_write(CALL_2BF148, BX_LR)
            uc.mem_write(CALL_2BC9D8, BX_LR)
            uc.mem_write(CALL_137314, BX_LR)
            uc.mem_write(CALL_2BF2B4, BX_LR)
            uc.mem_write(CALL_137570, BX_LR)

            calls_314 = []

            def hook_2bc9d8(mu, address, size, user_data):
                r1 = mu.reg_read(UC_ARM_REG_R1)
                mu.mem_write(r1, struct.pack("<I", 0x7777))

            def hook_137314(mu, address, size, user_data):
                r0 = mu.reg_read(UC_ARM_REG_R0)
                r1 = mu.reg_read(UC_ARM_REG_R1)
                r2 = mu.reg_read(UC_ARM_REG_R2)
                calls_314.append((r0, r1, r2))

            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2bc9d8, begin=CALL_2BC9D8, end=CALL_2BC9D8)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_137314, begin=CALL_137314, end=CALL_137314)

            work = 0x10020000
            next_work = 0x10020400
            uc.mem_write(work, b"\x00" * 0x350)
            uc.mem_write(next_work, b"\x00" * 0x350)

            # Global count at 0x00465058 + 8
            uc.mem_write(0x00465058 + 8, struct.pack("<i", tc["count"]))

            # Work queue table at 0x004E39A0
            for k in range(8):
                uc.mem_write(0x004E39A0 + k * 4, struct.pack("<I", next_work))

            # Initialize work fields
            uc.mem_write(work + 0x304, struct.pack("<i", 1)) # idx
            uc.mem_write(work + 0x308, struct.pack("<I", 0x4444))
            uc.mem_write(work + 0x14, struct.pack("<I", tc.get("f14", 0)))
            uc.mem_write(work + 0x18, struct.pack("<I", 0x5555))

            # Initialize p_idx at work + 24 * 1 (offset 24)
            uc.mem_write(work + 24, struct.pack("<6I", 0, 10, 20, 30, 40, 50))
            # Next idx at next_work + 0x304
            uc.mem_write(next_work + 0x304, struct.pack("<i", 2))

            uc.reg_write(UC_ARM_REG_R0, work)
            uc.reg_write(UC_ARM_REG_R1, tc["flag"])
            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)
            uc.reg_write(UC_ARM_REG_R4, 0x11111111)
            uc.reg_write(UC_ARM_REG_R5, 0x22222222)

            uc.emu_start(target, 0xF0000000, timeout=2000000)

            work_state = uc.mem_read(work, 0x320)
            next_state = uc.mem_read(next_work, 0x320)
            count_state = uc.mem_read(0x00465058 + 8, 4)
            regs = {
                "r4": uc.reg_read(UC_ARM_REG_R4),
                "r5": uc.reg_read(UC_ARM_REG_R5),
                "sp": uc.reg_read(UC_ARM_REG_SP),
            }
            return work_state, next_state, count_state, calls_314, regs

        o_work, o_next, o_cnt, o_calls, o_regs = run_one(False)
        c_work, c_next, c_cnt, c_calls, c_regs = run_one(True)

        assert o_work == c_work, f"tc={tc}: work state mismatch"
        assert o_next == c_next, f"tc={tc}: next state mismatch"
        assert o_cnt == c_cnt, f"tc={tc}: count mismatch"
        assert o_calls == c_calls, f"tc={tc}: calls mismatch"
        for r in ["r4", "r5", "sp"]:
            assert o_regs[r] == c_regs[r], f"tc={tc}: {r} mismatch"

    print("PASS: engine_func_002c52f0 (all 5 cases passed)")

if __name__ == "__main__":
    test_func_002bf558()
    test_ui_func_002bf9f0()
    test_func_002bfcb4()
    test_engine_func_002c0c74()
    test_engine_func_002c52f0()
    print("\nALL 5 CANDIDATES IN PART 14 PASSED DIFFERENTIAL VERIFICATION!")
