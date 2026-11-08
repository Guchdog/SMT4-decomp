#!/usr/bin/env python3
"""Differential test runner for leaf_batch32_c Part 13 candidates against code.bin.

Tests:
  - 0x002cf768: ui_func_002cf768 (320 B)
  - 0x002d3e14: engine_func_002d3e14 (332 B)
  - 0x002cba48: camp_func_002cba48 (328 B)
  - 0x002bf2cc: engine_func_002bf2cc (336 B)
  - 0x002e198c: CecProcess_func_002e198c (252 B)
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

BUILD_DIR = ROOT / "build" / "batch32_c_part13"

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

CALL_2BF6D0 = 0x002BF6D0
CALL_2BF460 = 0x002BF460
CALL_316EAC = 0x00316EAC
CALL_152AF8 = 0x00152AF8
CALL_2A7AA0 = 0x002A7AA0
CALL_2E006C = 0x002E006C
CALL_1E3408 = 0x001E3408
CALL_2B780C = 0x002B780C
CALL_2C4B30 = 0x002C4B30
CALL_2C3B00 = 0x002C3B00
CALL_248C0C = 0x00248C0C
CALL_2C34A4 = 0x002C34A4
CALL_2BCF34 = 0x002BCF34
CALL_2BCE50 = 0x002BCE50
CALL_2C5468 = 0x002C5468

BASE_SYMS = {
    "camp_func_002bf6d0": CALL_2BF6D0,
    "ui_func_002bf460": CALL_2BF460,
    "engine_func_00316eac": CALL_316EAC,
    "script_vm_func_00152af8": CALL_152AF8,
    "script_vm_func_002a7aa0": CALL_2A7AA0,
    "engine_func_002e006c": CALL_2E006C,
    "engine_func_001e3408": CALL_1E3408,
    "script_vm_func_002b780c": CALL_2B780C,
    "engine_func_002c4b30": CALL_2C4B30,
    "ui_func_002c3b00": CALL_2C3B00,
    "engine_func_00248c0c": CALL_248C0C,
    "engine_func_002c34a4": CALL_2C34A4,
    "nn_sdk_func_002bcf34": CALL_2BCF34,
    "nn_sdk_func_002bce50": CALL_2BCE50,
    "engine_func_002c5468": CALL_2C5468,
}

BX_LR = struct.pack("<I", 0xE12FFF1E)

# -----------------------------------------------------------------------------
# Function 1: ui_func_002cf768 (320 B)
# -----------------------------------------------------------------------------
def test_ui_func_002cf768():
    addr = 0x002CF768
    size = 320
    fn_name = "ui_func_002cf768"
    orig_code = load_original_bytes(addr, size)
    comp_body, relocs = compile_function(fn_name)
    comp_addr = 0x003D0000

    test_args = [
        (0, 0),
        (10, 5),
        (20, 17),
        (0, 40),
        (5, -10),
        (12, -37),
        (100, 12345),
    ]

    for base_id, angle in test_args:
        def run_one(is_comp: bool):
            uc = create_emulator()
            target = comp_addr if is_comp else addr
            if is_comp:
                body = stage_body(comp_body, relocs, comp_addr, BASE_SYMS, fn_name)
                uc.mem_write(comp_addr, body)

            # Return stub
            uc.mem_write(CALL_2BF6D0, BX_LR)
            uc.mem_write(CALL_2BF460, BX_LR)

            calls_2bf6d0 = []
            calls_2bf460 = []

            # Mock node struct for 2bf6d0: [node + 8] = x, [node + 10] = y
            node_buf = 0x10020000
            # Populate node with x = 100 + id, y = 200 + id
            def hook_2bf6d0(mu, address, size, user_data):
                r0 = mu.reg_read(UC_ARM_REG_R0)
                r1 = mu.reg_read(UC_ARM_REG_R1)
                calls_2bf6d0.append((r0, r1))
                x = (100 + r1) & 0xFFFF
                y = (200 + r1) & 0xFFFF
                node_addr = node_buf + (r1 & 0xFF) * 16
                mu.mem_write(node_addr + 8, struct.pack("<hh", x, y))
                mu.reg_write(UC_ARM_REG_R0, node_addr)

            def hook_2bf460(mu, address, size, user_data):
                r0 = mu.reg_read(UC_ARM_REG_R0)
                r1 = mu.reg_read(UC_ARM_REG_R1)
                r2 = mu.reg_read(UC_ARM_REG_R2)
                r3 = mu.reg_read(UC_ARM_REG_R3)
                sp = mu.reg_read(UC_ARM_REG_SP)
                sp0, sp4 = struct.unpack("<II", mu.mem_read(sp, 8))
                calls_2bf460.append((r0, r1, r2, r3, sp0, sp4))

            h1 = uc.hook_add(unicorn.UC_HOOK_CODE, hook_2bf6d0, begin=CALL_2BF6D0, end=CALL_2BF6D0)
            h2 = uc.hook_add(unicorn.UC_HOOK_CODE, hook_2bf460, begin=CALL_2BF460, end=CALL_2BF460)

            uc.reg_write(UC_ARM_REG_R0, base_id & 0xFFFFFFFF)
            uc.reg_write(UC_ARM_REG_R1, angle & 0xFFFFFFFF)
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
            return calls_2bf6d0, calls_2bf460, regs

        orig_6d0, orig_460, orig_regs = run_one(False)
        comp_6d0, comp_460, comp_regs = run_one(True)

        assert orig_6d0 == comp_6d0, f"base_id={base_id}, angle={angle}: calls_2bf6d0 mismatch: orig={orig_6d0} comp={comp_6d0}"
        assert orig_460 == comp_460, f"base_id={base_id}, angle={angle}: calls_2bf460 mismatch: orig={orig_460} comp={comp_460}"
        for r in ["r4", "r5", "r6", "r7", "r8", "sb", "sl", "fp", "sp"]:
            assert orig_regs[r] == comp_regs[r], f"base_id={base_id}, angle={angle}: {r} mismatch: orig={hex(orig_regs[r])} comp={hex(comp_regs[r])}"

    print("PASS: ui_func_002cf768 (all 7 cases passed)")

# -----------------------------------------------------------------------------
# Function 2: engine_func_002d3e14 (332 B)
# -----------------------------------------------------------------------------
def test_engine_func_002d3e14():
    addr = 0x002D3E14
    size = 332
    fn_name = "engine_func_002d3e14"
    orig_code = load_original_bytes(addr, size)
    comp_body, relocs = compile_function(fn_name)
    comp_addr = 0x003D0000

    cases = [
        {"phase": 0, "counter": 0, "col_result": 0},
        {"phase": 0, "counter": 0, "col_result": 1},
        {"phase": 1, "counter": 0, "col_result": 0},
        {"phase": 1, "counter": 1, "col_result": 0},
        {"phase": 2, "counter": 0, "query_ret": 1},
        {"phase": 2, "counter": 0, "query_ret": 0},
        {"phase": 3, "counter": 0, "query_ret": 0},
    ]

    for tc in cases:
        def run_one(is_comp: bool):
            uc = create_emulator()
            target = comp_addr if is_comp else addr
            if is_comp:
                body = stage_body(comp_body, relocs, comp_addr, BASE_SYMS, fn_name)
                uc.mem_write(comp_addr, body)

            uc.mem_write(CALL_316EAC, BX_LR)
            uc.mem_write(CALL_152AF8, BX_LR)
            uc.mem_write(CALL_2A7AA0, BX_LR)
            uc.mem_write(CALL_2E006C, BX_LR)
            uc.mem_write(CALL_1E3408, BX_LR)

            calls_316 = []
            calls_152 = []
            calls_2a7 = []
            calls_2e0 = []
            calls_1e3 = []

            def hook_316(mu, address, size, user_data):
                r0 = mu.reg_read(UC_ARM_REG_R0)
                r1 = mu.reg_read(UC_ARM_REG_R1)
                calls_316.append((r0, r1))
                mu.reg_write(UC_ARM_REG_R0, tc["col_result"])

            def hook_152(mu, address, size, user_data):
                r0 = mu.reg_read(UC_ARM_REG_R0)
                calls_152.append(r0)

            def hook_2a7(mu, address, size, user_data):
                r0 = mu.reg_read(UC_ARM_REG_R0)
                calls_2a7.append(r0)

            def hook_2e0(mu, address, size, user_data):
                r0 = mu.reg_read(UC_ARM_REG_R0)
                calls_2e0.append(r0)

            def hook_1e3(mu, address, size, user_data):
                r0 = mu.reg_read(UC_ARM_REG_R0)
                r1 = mu.reg_read(UC_ARM_REG_R1)
                r2 = mu.reg_read(UC_ARM_REG_R2)
                calls_1e3.append((r0, r1, r2))
                mu.reg_write(UC_ARM_REG_R0, tc.get("query_ret", 0))

            uc.hook_add(unicorn.UC_HOOK_CODE, hook_316, begin=CALL_316EAC, end=CALL_316EAC)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_152, begin=CALL_152AF8, end=CALL_152AF8)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2a7, begin=CALL_2A7AA0, end=CALL_2A7AA0)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2e0, begin=CALL_2E006C, end=CALL_2E006C)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_1e3, begin=CALL_1E3408, end=CALL_1E3408)

            # Set up base buffer
            base_buf = 0x10010000
            uc.mem_write(0x00447E58, struct.pack("<I", base_buf))

            # Initialize 64 records
            uc.mem_write(base_buf, b"\x00" * 0x1000)
            for i in range(64):
                rec_addr = base_buf + i * 56 + 12
                b0 = 1 if (i % 2 == 0) else 0
                b3 = 1 if (i % 4 == 0) else 0
                uc.mem_write(rec_addr, bytes([b0]))
                uc.mem_write(rec_addr + 3, bytes([b3]))
                uc.mem_write(rec_addr + 0x28, struct.pack("<hh", 10 + i, 20 + i))
                uc.mem_write(rec_addr + 0x2C, struct.pack("<II", 0x20000000 + i * 4, 0x30000000 + i * 4))

            # Header at 0xE00
            header = bytearray(0x100)
            struct.pack_into("<hh", header, 0x3E, tc["phase"], tc["counter"])
            struct.pack_into("<hh", header, 0x42, 0x1234, 0x5678)
            uc.mem_write(base_buf + 0xE00, bytes(header))

            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)
            uc.reg_write(UC_ARM_REG_R4, 0x11111111)
            uc.reg_write(UC_ARM_REG_R5, 0x22222222)
            uc.reg_write(UC_ARM_REG_R6, 0x33333333)
            uc.reg_write(UC_ARM_REG_R7, 0x44444444)
            uc.reg_write(UC_ARM_REG_R8, 0x55555555)

            uc.emu_start(target, 0xF0000000, timeout=2000000)

            ret = uc.reg_read(UC_ARM_REG_R0)
            final_base_data = uc.mem_read(base_buf, 0xF00)
            regs = {
                "r4": uc.reg_read(UC_ARM_REG_R4),
                "r5": uc.reg_read(UC_ARM_REG_R5),
                "r6": uc.reg_read(UC_ARM_REG_R6),
                "r7": uc.reg_read(UC_ARM_REG_R7),
                "r8": uc.reg_read(UC_ARM_REG_R8),
                "sp": uc.reg_read(UC_ARM_REG_SP),
            }
            return ret, final_base_data, calls_316, calls_152, calls_2a7, calls_2e0, calls_1e3, regs

        orig_ret, orig_mem, o316, o152, o2a7, o2e0, o1e3, o_regs = run_one(False)
        comp_ret, comp_mem, c316, c152, c2a7, c2e0, c1e3, c_regs = run_one(True)

        assert orig_ret == comp_ret, f"tc={tc}: ret mismatch: orig={orig_ret} comp={comp_ret}"
        assert orig_mem == comp_mem, f"tc={tc}: memory mismatch"
        assert o316 == c316, f"tc={tc}: calls_316 mismatch"
        assert o152 == c152, f"tc={tc}: calls_152 mismatch"
        assert o2a7 == c2a7, f"tc={tc}: calls_2a7 mismatch"
        assert o2e0 == c2e0, f"tc={tc}: calls_2e0 mismatch"
        assert o1e3 == c1e3, f"tc={tc}: calls_1e3 mismatch"
        for r in ["r4", "r5", "r6", "r7", "r8", "sp"]:
            assert o_regs[r] == c_regs[r], f"tc={tc}: {r} mismatch"

    print("PASS: engine_func_002d3e14 (all 7 cases passed)")

# -----------------------------------------------------------------------------
# Function 3: camp_func_002cba48 (328 B)
# -----------------------------------------------------------------------------
def test_camp_func_002cba48():
    addr = 0x002CBA48
    size = 328
    fn_name = "camp_func_002cba48"
    orig_code = load_original_bytes(addr, size)
    comp_body, relocs = compile_function(fn_name)
    comp_addr = 0x003D0000

    cases = [
        {"slot_idx": 0, "found": True},
        {"slot_idx": 0, "found": False},
        {"slot_idx": 1, "found": True},
        {"slot_idx": 1, "found": False},
    ]

    for tc in cases:
        def run_one(is_comp: bool):
            uc = create_emulator()
            target = comp_addr if is_comp else addr
            if is_comp:
                body = stage_body(comp_body, relocs, comp_addr, BASE_SYMS, fn_name)
                uc.mem_write(comp_addr, body)

            # Implement real script_vm_func_002b780c logic in hook
            def hook_2b780c(mu, address, size, user_data):
                # r0 = it + 1, r1 = end, r2 = it, r3 = &target
                r0 = mu.reg_read(UC_ARM_REG_R0)
                r1 = mu.reg_read(UC_ARM_REG_R1)
                r2 = mu.reg_read(UC_ARM_REG_R2)
                r3 = mu.reg_read(UC_ARM_REG_R3)
                target_val = struct.unpack("<I", mu.mem_read(r3, 4))[0]

                cur_src = r0
                cur_dst = r2
                while cur_src < r1:
                    val = struct.unpack("<I", mu.mem_read(cur_src, 4))[0]
                    if val != target_val:
                        mu.mem_write(cur_dst, struct.pack("<I", val))
                        cur_dst += 4
                    cur_src += 4
                mu.reg_write(UC_ARM_REG_R0, cur_dst)

            uc.mem_write(CALL_2B780C, BX_LR)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2b780c, begin=CALL_2B780C, end=CALL_2B780C)

            # Layout memory:
            # 0x00464BB4, 0x00464BB8
            desc0 = 0x10030000
            desc1 = 0x10030100
            uc.mem_write(0x00464BB4, struct.pack("<II", desc0, desc1))
            # [desc + 4] = sub_info
            sub0 = 0x10030200
            sub1 = 0x10030300
            uc.mem_write(desc0 + 4, struct.pack("<I", sub0))
            uc.mem_write(desc1 + 4, struct.pack("<I", sub1))
            # r5 = sub + 0x40; [r5 + 0x6C] = node
            node0 = 0x10030400
            node1 = 0x10030500
            uc.mem_write(sub0 + 0x40 + 0x6C, struct.pack("<I", node0))
            uc.mem_write(sub1 + 0x40 + 0x6C, struct.pack("<I", node1))

            # Initial target pointers:
            target0_obj = 0x10030600
            target1_obj = 0x10030700
            uc.mem_write(0x00464B10, struct.pack("<I", target0_obj))
            uc.mem_write(0x00464B1C, struct.pack("<I", target1_obj))
            uc.mem_write(0x00464B20, struct.pack("<I", 0x11111111))
            uc.mem_write(0x00464B24, struct.pack("<I", 0x22222222))
            uc.mem_write(0x00464BBC, struct.pack("<II", 0, 0))

            # [target + 0x0C]
            uc.mem_write(target0_obj + 0x0C, struct.pack("<I", 0x99999999))
            uc.mem_write(target1_obj + 0x0C, struct.pack("<I", 0x88888888))

            # Vectors
            vec0 = 0x10030800
            vec1 = 0x10030900
            uc.mem_write(0x00464B9C, struct.pack("<II", vec0, vec1))
            self_obj = 0x10030A00

            arr0 = 0x10030C00
            arr1 = 0x10030D00
            if tc["found"]:
                items0 = [0x1000, target0_obj, 0x2000, 0x3000]
                items1 = [0x4000, target1_obj, 0x5000]
            else:
                items0 = [0x1000, 0x2000, 0x3000]
                items1 = [0x4000, 0x5000, 0x6000]

            for i, val in enumerate(items0):
                uc.mem_write(arr0 + i * 4, struct.pack("<I", val))
            for i, val in enumerate(items1):
                uc.mem_write(arr1 + i * 4, struct.pack("<I", val))

            uc.mem_write(vec0 + 0x18, struct.pack("<II", arr0, arr0 + len(items0) * 4))
            uc.mem_write(vec1 + 0x18, struct.pack("<II", arr1, arr1 + len(items1) * 4))

            uc.reg_write(UC_ARM_REG_R0, self_obj)
            uc.reg_write(UC_ARM_REG_R1, tc["slot_idx"])
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

            state = {
                "00464B10": uc.mem_read(0x00464B10, 32),
                "00464BBC": uc.mem_read(0x00464BBC, 16),
                "node0": uc.mem_read(node0, 16),
                "node1": uc.mem_read(node1, 16),
                "target0_c": uc.mem_read(target0_obj + 0x0C, 4),
                "target1_c": uc.mem_read(target1_obj + 0x0C, 4),
                "vec0": uc.mem_read(vec0 + 0x18, 8),
                "vec1": uc.mem_read(vec1 + 0x18, 8),
                "arr0": uc.mem_read(arr0, 24),
                "arr1": uc.mem_read(arr1, 24),
            }
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
            return state, regs

        orig_state, orig_regs = run_one(False)
        comp_state, comp_regs = run_one(True)

        for k in orig_state:
            assert orig_state[k] == comp_state[k], f"tc={tc}: state {k} mismatch"
        for r in ["r4", "r5", "r6", "r7", "r8", "sb", "sl", "fp", "sp"]:
            assert orig_regs[r] == comp_regs[r], f"tc={tc}: {r} mismatch"

    print("PASS: camp_func_002cba48 (all 5 cases passed)")

# -----------------------------------------------------------------------------
# Function 4: engine_func_002bf2cc (336 B)
# -----------------------------------------------------------------------------
def test_engine_func_002bf2cc():
    addr = 0x002BF2CC
    size = 336
    fn_name = "engine_func_002bf2cc"
    orig_code = load_original_bytes(addr, size)
    comp_body, relocs = compile_function(fn_name)
    comp_addr = 0x003D0000

    test_masks = [
        0,
        0x1 | 0x2 | 0x4 | 0x8 | 0x10 | 0x20 | 0x80 | 0x100 | 0x200 | 0x400 | 0x800 | 0x1000,
        0x40,
        0x1FFF,
        0x0040,
        0x5555,
        0xAAAA,
    ]

    for flags in test_masks:
        def run_one(is_comp: bool):
            uc = create_emulator()
            target = comp_addr if is_comp else addr
            if is_comp:
                body = stage_body(comp_body, relocs, comp_addr, BASE_SYMS, fn_name)
                uc.mem_write(comp_addr, body)

            uc.mem_write(CALL_2C4B30, BX_LR)
            calls_2c4 = []

            def hook_2c4(mu, address, size, user_data):
                r0 = mu.reg_read(UC_ARM_REG_R0)
                r1 = mu.reg_read(UC_ARM_REG_R1)
                calls_2c4.append((r0, r1))

            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2c4, begin=CALL_2C4B30, end=CALL_2C4B30)

            # Set up struct R4
            r4_buf = 0x10010000
            uc.mem_write(0x004655C0, struct.pack("<I", r4_buf))
            # R4: flags=0x01000000, field_04=0x100, mask=0x0010
            uc.mem_write(r4_buf, struct.pack("<III", 0x01000000, 0x100, 0x0010))

            uc.reg_write(UC_ARM_REG_R0, flags)
            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)
            uc.reg_write(UC_ARM_REG_R4, 0x11111111)
            uc.reg_write(UC_ARM_REG_R5, 0x22222222)
            uc.reg_write(UC_ARM_REG_R6, 0x33333333)

            uc.emu_start(target, 0xF0000000, timeout=2000000)

            r4_data = uc.mem_read(r4_buf, 16)
            regs = {
                "r4": uc.reg_read(UC_ARM_REG_R4),
                "r5": uc.reg_read(UC_ARM_REG_R5),
                "r6": uc.reg_read(UC_ARM_REG_R6),
                "sp": uc.reg_read(UC_ARM_REG_SP),
            }
            return r4_data, calls_2c4, regs

        orig_mem, orig_calls, orig_regs = run_one(False)
        comp_mem, comp_calls, comp_regs = run_one(True)

        assert orig_mem == comp_mem, f"flags={hex(flags)}: r4 memory mismatch: orig={orig_mem.hex()} comp={comp_mem.hex()}"
        assert orig_calls == comp_calls, f"flags={hex(flags)}: calls mismatch: orig={orig_calls} comp={comp_calls}"
        for r in ["r4", "r5", "r6", "sp"]:
            assert orig_regs[r] == comp_regs[r], f"flags={hex(flags)}: {r} mismatch"

    print("PASS: engine_func_002bf2cc (all 7 cases passed)")

# -----------------------------------------------------------------------------
# Function 5: CecProcess_func_002e198c (252 B)
# -----------------------------------------------------------------------------
def test_CecProcess_func_002e198c():
    addr = 0x002E198C
    size = 252
    fn_name = "CecProcess_func_002e198c"
    orig_code = load_original_bytes(addr, size)
    comp_body, relocs = compile_function(fn_name)
    comp_addr = 0x003D0000

    test_results = [
        0,              # Success
        0x00600000,     # Module 3
        0x80000001,     # Negative error
        0xC0600000,     # Negative with module 3 bits
        0xD8E00001,     # Negative error
    ]

    for bce_ret in test_results:
        def run_one(is_comp: bool):
            uc = create_emulator()
            target = comp_addr if is_comp else addr
            if is_comp:
                body = stage_body(comp_body, relocs, comp_addr, BASE_SYMS, fn_name)
                uc.mem_write(comp_addr, body)

            uc.mem_write(CALL_2C3B00, BX_LR)
            uc.mem_write(CALL_248C0C, BX_LR)
            uc.mem_write(CALL_2C34A4, BX_LR)
            uc.mem_write(CALL_2BCF34, BX_LR)
            uc.mem_write(CALL_2BCE50, BX_LR)
            uc.mem_write(CALL_2C5468, BX_LR)

            calls_3b00 = []
            calls_8c0c = []
            calls_34a4 = []
            calls_cf34 = []
            calls_ce50 = []
            calls_5468 = []

            def hook_3b00(mu, address, size, user_data):
                r0 = mu.reg_read(UC_ARM_REG_R0)
                calls_3b00.append(r0)

            def hook_8c0c(mu, address, size, user_data):
                calls_8c0c.append(True)
                mu.reg_write(UC_ARM_REG_R0, 0xAABBCCDD)

            def hook_34a4(mu, address, size, user_data):
                r0 = mu.reg_read(UC_ARM_REG_R0)
                r1 = mu.reg_read(UC_ARM_REG_R1)
                r2 = mu.reg_read(UC_ARM_REG_R2)
                r3 = mu.reg_read(UC_ARM_REG_R3)
                sp = mu.reg_read(UC_ARM_REG_SP)
                sp0, sp4 = struct.unpack("<II", mu.mem_read(sp, 8))
                calls_34a4.append((r0, r1, r2, r3, sp0, sp4))
                mu.reg_write(UC_ARM_REG_R0, 0x10040000)

            def hook_cf34(mu, address, size, user_data):
                r0 = mu.reg_read(UC_ARM_REG_R0)
                r1 = mu.reg_read(UC_ARM_REG_R1)
                r2 = mu.reg_read(UC_ARM_REG_R2)
                calls_cf34.append((r0, r1, r2))

            def hook_ce50(mu, address, size, user_data):
                r0 = mu.reg_read(UC_ARM_REG_R0)
                r1 = mu.reg_read(UC_ARM_REG_R1)
                r2 = mu.reg_read(UC_ARM_REG_R2)
                r3 = mu.reg_read(UC_ARM_REG_R3)
                sp = mu.reg_read(UC_ARM_REG_SP)
                sp_args = struct.unpack("<IIII", mu.mem_read(sp, 16))
                # Also read the 4 words pointed to by r1
                r1_words = struct.unpack("<IIII", mu.mem_read(r1, 16))
                # And the pointer pointed to by r3
                r3_val = struct.unpack("<I", mu.mem_read(r3, 4))[0]
                calls_ce50.append((r0, r1_words, r2, r3_val, sp_args))
                mu.reg_write(UC_ARM_REG_R0, bce_ret)

            def hook_5468(mu, address, size, user_data):
                calls_5468.append(True)

            uc.hook_add(unicorn.UC_HOOK_CODE, hook_3b00, begin=CALL_2C3B00, end=CALL_2C3B00)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_8c0c, begin=CALL_248C0C, end=CALL_248C0C)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_34a4, begin=CALL_2C34A4, end=CALL_2C34A4)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_cf34, begin=CALL_2BCF34, end=CALL_2BCF34)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_ce50, begin=CALL_2BCE50, end=CALL_2BCE50)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_5468, begin=CALL_2C5468, end=CALL_2C5468)

            self_obj = 0x10020000
            # Initialize fields in self
            uc.mem_write(self_obj + 0x43C, struct.pack("<II", 0x100, 0x200))

            uc.reg_write(UC_ARM_REG_R0, self_obj)
            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)
            uc.reg_write(UC_ARM_REG_R4, 0x11111111)
            uc.reg_write(UC_ARM_REG_R5, 0x22222222)

            uc.emu_start(target, 0xF0000000, timeout=2000000)

            self_fields = {
                "6c": struct.unpack("<I", uc.mem_read(self_obj + 0x6C, 4))[0],
                "70": struct.unpack("<I", uc.mem_read(self_obj + 0x70, 4))[0],
                "78": struct.unpack("<I", uc.mem_read(self_obj + 0x78, 4))[0],
                "7c": struct.unpack("<I", uc.mem_read(self_obj + 0x7C, 4))[0],
                "44c": struct.unpack("<I", uc.mem_read(self_obj + 0x44C, 4))[0],
            }
            regs = {
                "r4": uc.reg_read(UC_ARM_REG_R4),
                "r5": uc.reg_read(UC_ARM_REG_R5),
                "sp": uc.reg_read(UC_ARM_REG_SP),
            }
            return self_fields, calls_3b00, calls_8c0c, calls_34a4, calls_cf34, calls_ce50, calls_5468, regs

        o_fields, o3b, o8c, o34, ocf, oce, o54, o_regs = run_one(False)
        c_fields, c3b, c8c, c34, ccf, cce, c54, c_regs = run_one(True)

        assert o_fields == c_fields, f"bce_ret={hex(bce_ret)}: fields mismatch: orig={o_fields} comp={c_fields}"
        assert o3b == c3b, f"bce_ret={hex(bce_ret)}: calls_3b mismatch"
        assert o8c == c8c, f"bce_ret={hex(bce_ret)}: calls_8c mismatch"
        assert o34 == c34, f"bce_ret={hex(bce_ret)}: calls_34 mismatch"
        assert ocf == ccf, f"bce_ret={hex(bce_ret)}: calls_cf mismatch"
        assert oce == cce, f"bce_ret={hex(bce_ret)}: calls_ce mismatch: orig={oce} comp={cce}"
        assert o54 == c54, f"bce_ret={hex(bce_ret)}: calls_54 mismatch: orig={o54} comp={c54}"
        for r in ["r4", "r5", "sp"]:
            assert o_regs[r] == c_regs[r], f"bce_ret={hex(bce_ret)}: {r} mismatch"

    print("PASS: CecProcess_func_002e198c (all 5 cases passed)")

if __name__ == "__main__":
    test_ui_func_002cf768()
    test_engine_func_002d3e14()
    test_camp_func_002cba48()
    test_engine_func_002bf2cc()
    test_CecProcess_func_002e198c()
    print("\nALL 5 CANDIDATES IN PART 13 PASSED DIFFERENTIAL VERIFICATION!")
