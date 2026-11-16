#!/usr/bin/env python3
"""Differential test runner for leaf_batch32_c Part 15 candidates against code.bin.

Tests:
  - 0x002bbb2c: engine_func_002bbb2c (348 B)
  - 0x002c15d8: engine_func_002c15d8 (360 B)
  - 0x002c2cf0: engine_func_002c2cf0 (1176 B)
  - 0x002cd2cc: camp_func_002cd2cc (708 B)
  - 0x002cf308: camp_func_002cf308 (444 B)
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

BUILD_DIR = ROOT / "build" / "batch32_c_part15"

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
    uc.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc.mem_write(CODE_BASE, ORIG_DATA)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)
    uc.mem_map(0x10000000, 0x00100000, UC_PROT_READ | UC_PROT_WRITE)
    if RODATA_BYTES:
        uc.mem_write(RODATA_ADDR, RODATA_BYTES)
    return uc

CALL_2C3AA8 = 0x002C3AA8
CALL_2C3A24 = 0x002C3A24
CALL_2C3290 = 0x002C3290
CALL_2B45F8 = 0x002B45F8
CALL_120660 = 0x00120660
CALL_120784 = 0x00120784
CALL_12070C = 0x0012070C
CALL_13F960 = 0x0013F960
CALL_2BD688 = 0x002BD688
CALL_2ACC98 = 0x002ACC98
CALL_1208B8 = 0x001208B8
CALL_2883BC = 0x002883BC
CALL_2B9364 = 0x002B9364
CALL_2C4B30 = 0x002C4B30
CALL_24BE90 = 0x0024BE90
CALL_29C950 = 0x0029C950
CALL_29CB94 = 0x0029CB94
CALL_2A0FAC = 0x002A0FAC

BASE_SYMS = {
    "engine_func_002c3aa8": CALL_2C3AA8,
    "engine_func_002c3a24": CALL_2C3A24,
    "engine_func_002c3290": CALL_2C3290,
    "engine_func_002b45f8": CALL_2B45F8,
    "engine_func_00120660": CALL_120660,
    "engine_func_00120784": CALL_120784,
    "engine_func_0012070c": CALL_12070C,
    "engine_func_0013f960": CALL_13F960,
    "engine_func_002bd688": CALL_2BD688,
    "engine_func_002acc98": CALL_2ACC98,
    "engine_func_001208b8": CALL_1208B8,
    "camp_func_002883bc": CALL_2883BC,
    "camp_func_002b9364": CALL_2B9364,
    "engine_func_002c4b30": CALL_2C4B30,
    "camp_func_0024be90": CALL_24BE90,
    "script_vm_func_0029c950": CALL_29C950,
    "script_vm_func_0029cb94": CALL_29CB94,
    "camp_func_002a0fac": CALL_2A0FAC,
}

# -------------------------------------------------------------------------
# Test 1: engine_func_002bbb2c (0x002bbb2c)
# -------------------------------------------------------------------------
def test_engine_func_002bbb2c():
    ADDR = 0x002bbb2c
    ORIG_SIZE = 432
    orig_code = load_original_bytes(ADDR, ORIG_SIZE)
    comp_body, relocs = compile_function("engine_func_002bbb2c")
    comp_code = stage_body(comp_body, relocs, ADDR, BASE_SYMS, "engine_func_002bbb2c")

    RET_ADDR = 0x004F0000
    BX_LR = struct.pack("<I", 0xE12FFF1E)

    cases = [
        # (name, head_nodes, alloc_size, align, limit)
        ("empty_heap_success", [], 0x1000, 0x10, 0x300000),
        ("empty_heap_overflow", [], 0x150000, 0x10, 0x300000),
        ("single_node_success", [(0x200000, 0x1000)], 0x2000, 0x10, 0x300000),
        ("single_node_overflow", [(0x200000, 0x0E0000)], 0x030000, 0x10, 0x300000),
        ("two_nodes_insert_after", [(0x200000, 0x1000), (0x210000, 0x2000)], 0x4000, 0x20, 0x300000),
        ("fit_before_head", [(0x210000, 0x1000)], 0x800, 0x10, 0x300000),
    ]

    for name, nodes_setup, alloc_size, align, limit in cases:
        def run_sim(code: bytes):
            uc = create_emulator()
            uc.mem_write(ADDR, code)
            uc.mem_write(RET_ADDR, BX_LR)
            uc.mem_write(CALL_2C3AA8, BX_LR)
            uc.mem_write(CALL_2C3A24, BX_LR)

            HEAP_ADDR = 0x10010000
            NEW_NODE = 0x10020000
            BASE_ADDR = 0x00200000

            uc.mem_write(NEW_NODE, b"\x00" * 32)

            if not nodes_setup:
                head_ptr = 0
            else:
                head_ptr = 0x10030000
                allocated_nodes = []
                for i, (n_addr, n_sz) in enumerate(nodes_setup):
                    ptr = 0x10030000 + i * 32
                    allocated_nodes.append((ptr, n_addr, n_sz))

                count = len(allocated_nodes)
                for i in range(count):
                    ptr, n_addr, n_sz = allocated_nodes[i]
                    next_ptr = allocated_nodes[(i + 1) % count][0]
                    prev_ptr = allocated_nodes[(i - 1 + count) % count][0]
                    buf = struct.pack("<IIII", next_ptr, prev_ptr, n_addr, n_sz)
                    uc.mem_write(ptr, buf)

            heap_buf = struct.pack("<IIII", BASE_ADDR, limit, head_ptr, 0)
            uc.mem_write(HEAP_ADDR, heap_buf)

            uc.reg_write(UC_ARM_REG_R0, HEAP_ADDR)
            uc.reg_write(UC_ARM_REG_R1, NEW_NODE)
            uc.reg_write(UC_ARM_REG_R2, alloc_size)
            uc.reg_write(UC_ARM_REG_R3, align)
            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, RET_ADDR)

            uc.emu_start(ADDR, RET_ADDR, timeout=2000000)

            ret_r0 = uc.reg_read(UC_ARM_REG_R0)
            final_heap = uc.mem_read(HEAP_ADDR, 16)
            final_node = uc.mem_read(NEW_NODE, 16)
            return ret_r0, final_heap, final_node

        orig_ret, orig_h, orig_n = run_sim(orig_code)
        comp_ret, comp_h, comp_n = run_sim(comp_code)

        assert orig_ret == comp_ret, f"{name}: ret mismatch (orig={orig_ret:#x}, comp={comp_ret:#x})"
        assert orig_h == comp_h, f"{name}: heap mismatch"
        assert orig_n == comp_n, f"{name}: node mismatch"

    print(f"PASS: engine_func_002bbb2c (all {len(cases)} cases passed)")

# -------------------------------------------------------------------------
# Test 2: engine_func_002c15d8 (0x002c15d8)
# -------------------------------------------------------------------------
def test_engine_func_002c15d8():
    ADDR = 0x002c15d8
    ORIG_SIZE = 360
    orig_code = load_original_bytes(ADDR, ORIG_SIZE)
    comp_body, relocs = compile_function("engine_func_002c15d8")
    comp_code = stage_body(comp_body, relocs, ADDR, BASE_SYMS, "engine_func_002c15d8")

    RET_ADDR = 0x004F0000
    BX_LR = struct.pack("<I", 0xE12FFF1E)

    cases = [
        # (name, mode, expected_type, b0, b1, sep, is_match)
        ("sep_dot_type4", 0, 4, 0x7A, 0x82, 0x2E, True),
        ("sep_null_type3", 1, 3, 0x72, 0x75, 0x00, True),
        ("sep_dot_type2", 0, 2, 0x20, 0x30, 0x2E, True),
        ("sep_null_type1", 0, 1, 0x05, 0x08, 0x00, True),
        ("b0_high_fails", 0, 4, 0x89, 0x90, 0x2E, True),
        ("type_mismatch_type3", 0, 2, 0x72, 0x75, 0x00, True),
        ("no_match_string", 0, 4, 0x7A, 0x82, 0x2E, False),
        ("invalid_sep", 0, 4, 0x7A, 0x82, 0x41, True),  # 'A' separator
    ]

    for name, mode, exp_type, b0, b1, sep, is_match in cases:
        def run_sim(code: bytes):
            uc = create_emulator()
            uc.mem_write(ADDR, code)
            uc.mem_write(RET_ADDR, BX_LR)

            # engine_func_002c3290: returns query length 4
            uc.mem_write(CALL_2C3290, struct.pack("<II", 0xE3A00004, 0xE12FFF1E)) # mov r0, #4; bx lr

            # engine_func_002b45f8: returns 0 if is_match else 1
            ret_val = 0 if is_match else 1
            uc.mem_write(CALL_2B45F8, struct.pack("<II", 0xE3A00000 | ret_val, 0xE12FFF1E))

            CTX_ADDR = 0x10010000
            PARAM_ADDR = 0x10020000
            QUERY_ADDR = 0x10030000
            NODE_ADDR = 0x10040000

            # CTX setup:
            # ctx[0] = 0 (offset 0), ctx[4] = 1 (offset 1)
            # ctx[0xC + 0*4] = NODE_ADDR
            # ctx[0xC + 1*4] = NODE_ADDR
            ctx_data = struct.pack("<IIIIII", 0, 1, 0, NODE_ADDR, NODE_ADDR, 0)
            uc.mem_write(CTX_ADDR, ctx_data)

            # NODE setup:
            # 0x30: desc_off = 0x40
            # 0x34: count = 1
            # 0x38: str_off = 0x60
            node_buf = bytearray(0x100)
            struct.pack_into("<III", node_buf, 0x30, 0x40, 1, 0x60)

            # Descriptor at 0x40:
            # +0: str_off = 0 (so string is at node + 0x60)
            # +4: flags = b0 | (b1 << 16)
            f4 = b0 | (b1 << 16)
            struct.pack_into("<II", node_buf, 0x40, 0, f4)

            # String at 0x60: "test" + sep + "\0"
            node_buf[0x60:0x66] = b"test" + bytes([sep]) + b"\x00"
            uc.mem_write(NODE_ADDR, bytes(node_buf))

            # PARAM setup:
            # [0] = mode, [1] = exp_type, [2] = 0, [3] = 0, [4..7] = 0
            param_buf = struct.pack("<BBBBII", mode, exp_type, 0, 0, 0, 0)
            uc.mem_write(PARAM_ADDR, param_buf)

            uc.reg_write(UC_ARM_REG_R0, CTX_ADDR)
            uc.reg_write(UC_ARM_REG_R1, PARAM_ADDR)
            uc.reg_write(UC_ARM_REG_R2, QUERY_ADDR)
            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, RET_ADDR)

            uc.emu_start(ADDR, RET_ADDR, timeout=2000000)

            ret_r0 = uc.reg_read(UC_ARM_REG_R0)
            final_param = uc.mem_read(PARAM_ADDR, 8)
            return ret_r0, final_param

        orig_ret, orig_p = run_sim(orig_code)
        comp_ret, comp_p = run_sim(comp_code)

        assert orig_ret == comp_ret, f"{name}: ret mismatch (orig={orig_ret}, comp={comp_ret})"
        assert orig_p == comp_p, f"{name}: param mismatch (orig={orig_p.hex()}, comp={comp_p.hex()})"

    print(f"PASS: engine_func_002c15d8 (all {len(cases)} cases passed)")

# -------------------------------------------------------------------------
# Test 3: engine_func_002c2cf0 (0x002c2cf0)
# -------------------------------------------------------------------------
def test_engine_func_002c2cf0():
    ADDR = 0x002c2cf0
    ORIG_SIZE = 1176
    orig_code = load_original_bytes(ADDR, ORIG_SIZE)
    comp_body, relocs = compile_function("engine_func_002c2cf0")
    comp_code = stage_body(comp_body, relocs, ADDR, BASE_SYMS, "engine_func_002c2cf0")

    RET_ADDR = 0x004F0000
    BX_LR = struct.pack("<I", 0xE12FFF1E)

    cases = [
        ("all_zeros", []),
        ("section1_only", [0]),
        ("sections_1_3_5", [0, 2, 4]),
        ("sections_6_to_10", [5, 6, 7, 8, 9]),
        ("all_sections", list(range(11))),
    ]

    callees = [
        (CALL_120660, 1 << 0),
        (CALL_120784, 1 << 1),
        (CALL_12070C, 1 << 2),
        (CALL_13F960, 1 << 3),
        (CALL_2BD688, 1 << 4),
        (CALL_2ACC98, 1 << 5),
        (CALL_1208B8, 1 << 10),
    ]

    section_offsets = [
        (0x2C, 0x30, CALL_120660),
        (0x4C, 0x50, CALL_120784),
        (0x54, 0x58, CALL_12070C),
        (0x3C, 0x40, CALL_13F960),
        (0x24, 0x28, CALL_2BD688),
        (0x64, 0x68, CALL_2ACC98),
        (0x6C, 0x70, CALL_2ACC98),
        (0x74, 0x78, CALL_2ACC98),
        (0x7C, 0x80, CALL_2ACC98),
        (0x84, 0x88, CALL_2ACC98),
        (0x1C, 0x20, CALL_1208B8),
    ]

    for name, active_sections in cases:
        def run_sim(code: bytes):
            uc = create_emulator()
            uc.mem_write(ADDR, code)
            uc.mem_write(RET_ADDR, BX_LR)

            # Install mock callbacks that return their bitmask
            for c_addr, val in callees:
                inst = struct.pack("<II", 0xE3A00000 | (val & 0xFF), 0xE12FFF1E)
                uc.mem_write(c_addr, inst)

            HOLDER_ADDR = 0x10010000
            OBJ_ADDR = 0x10020000
            uc.mem_write(HOLDER_ADDR, struct.pack("<I", OBJ_ADDR))

            obj_buf = bytearray(0x1000)
            data_cursor = 0x100
            for sec_idx in active_sections:
                cnt_off, off_field, _ = section_offsets[sec_idx]
                count = 1
                struct.pack_into("<i", obj_buf, cnt_off, count)
                # off1 is relative from (obj + off_field) to target array
                # target array is at OBJ_ADDR + data_cursor
                off1 = data_cursor - off_field
                struct.pack_into("<i", obj_buf, off_field, off1)

                # At obj_buf[data_cursor], each entry is 16 bytes:
                # entry + 0x28 has off2 relative from (entry + 0x28) to target
                # let target be at data_cursor + 0x40:
                off2 = 0x40 - 0x28
                struct.pack_into("<i", obj_buf, data_cursor + 0x28, off2)
                data_cursor += 0x60

            uc.mem_write(OBJ_ADDR, bytes(obj_buf))

            uc.reg_write(UC_ARM_REG_R0, HOLDER_ADDR)
            uc.reg_write(UC_ARM_REG_R1, 0x1234)
            uc.reg_write(UC_ARM_REG_R2, 0x5678)
            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, RET_ADDR)

            uc.emu_start(ADDR, RET_ADDR, timeout=2000000)

            ret_r0 = uc.reg_read(UC_ARM_REG_R0)
            return ret_r0

        orig_ret = run_sim(orig_code)
        comp_ret = run_sim(comp_code)

        assert orig_ret == comp_ret, f"{name}: ret mismatch (orig={orig_ret:#x}, comp={comp_ret:#x})"

    print(f"PASS: engine_func_002c2cf0 (all {len(cases)} cases passed)")

# -------------------------------------------------------------------------
# Test 4: camp_func_002cd2cc (0x002cd2cc)
# -------------------------------------------------------------------------
def test_camp_func_002cd2cc():
    ADDR = 0x002cd2cc
    ORIG_SIZE = 716
    orig_code = load_original_bytes(ADDR, ORIG_SIZE)
    comp_body, relocs = compile_function("camp_func_002cd2cc")
    comp_code = stage_body(comp_body, relocs, ADDR, BASE_SYMS, "camp_func_002cd2cc")

    RET_ADDR = 0x004F0000
    BX_LR = struct.pack("<I", 0xE12FFF1E)

    cases = [
        ("all_match", True, True, True, True, 3),
        ("first_call_fails", False, True, True, True, 3),
        ("id48_mismatch", True, False, True, True, 3),
        ("stat_mismatch", True, True, False, True, 3),
        ("missing_skill", True, True, True, False, 3),
        ("zero_skill_skipped", True, True, True, True, 0),
    ]

    for name, c1_succ, id48_match, stat_match, skill_match, skill_cnt in cases:
        def run_sim(code: bytes):
            uc = create_emulator()
            uc.mem_write(ADDR, code)
            uc.mem_write(RET_ADDR, BX_LR)

            # camp_func_002883bc: returns 1 if c1_succ else 0, and populates buffer
            def hook_2883bc(uc_inst, address, size, user_data):
                if not c1_succ:
                    uc_inst.reg_write(UC_ARM_REG_R0, 0)
                    return
                buf_ptr = uc_inst.reg_read(UC_ARM_REG_R1)
                mock_data = bytearray(0x40)
                struct.pack_into("<H", mock_data, 0, 0x12)       # sp[0]
                struct.pack_into("<H", mock_data, 2, 100)        # sp[2]
                struct.pack_into("<H", mock_data, 4, 110)        # sp[4]
                struct.pack_into("<H", mock_data, 6, 120)        # sp[6]
                struct.pack_into("<H", mock_data, 8, 130)        # sp[8]
                struct.pack_into("<H", mock_data, 0xA, 140)      # sp[0xA]
                struct.pack_into("<H", mock_data, 0x18, 50)      # sp[0x18]
                struct.pack_into("<H", mock_data, 0x1A, 60)      # sp[0x1A]
                struct.pack_into("<H", mock_data, 0x1C, 0x101)   # skill 0
                struct.pack_into("<H", mock_data, 0x1E, 0x102)   # skill 1
                struct.pack_into("<H", mock_data, 0x20, 0x103)   # skill 2
                struct.pack_into("<I", mock_data, 0x30, 0x9999)  # sp[0x30]
                mock_data[0x16] = 0x20                           # sp[0x16]
                uc_inst.mem_write(buf_ptr, bytes(mock_data))
                uc_inst.reg_write(UC_ARM_REG_R0, 1)

            DEMON_BASE = 0x10050000
            uc.mem_write(DEMON_BASE, b"\x00" * 0x80)
            struct.pack_into("<H", bytearray(0x80), 0x38, 0x55)
            uc.mem_write(DEMON_BASE + 0x38, struct.pack("<H", 0x55))

            # camp_func_002b9364: returns DEMON_BASE
            uc.mem_write(CALL_2B9364, struct.pack("<II", 0xE59F0000, 0xE12FFF1E) + struct.pack("<I", DEMON_BASE))

            # engine_func_002c4b30: zeroes memory (r0=ptr, r1=size)
            def hook_2c4b30(uc_inst, address, size, user_data):
                p = uc_inst.reg_read(UC_ARM_REG_R0)
                sz = uc_inst.reg_read(UC_ARM_REG_R1)
                uc_inst.mem_write(p, b"\x00" * sz)

            uc.mem_write(CALL_2C4B30, BX_LR)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2c4b30, begin=CALL_2C4B30, end=CALL_2C4B30)

            uc.mem_write(CALL_2883BC, BX_LR)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2883bc, begin=CALL_2883BC, end=CALL_2883BC)

            uc.mem_write(CALL_24BE90, BX_LR)
            uc.mem_write(CALL_29C950, BX_LR)

            # script_vm_func_0029cb94: returns skill_cnt
            uc.mem_write(CALL_29CB94, struct.pack("<II", 0xE3A00000 | skill_cnt, 0xE12FFF1E))

            # SRC_RECORD setup (r4):
            SRC_ADDR = 0x10010000
            src_buf = bytearray(0x600)
            struct.pack_into("<H", src_buf, 0x46, 0x55)      # id
            struct.pack_into("<B", src_buf, 0x48, 0x12 if id48_match else 0x99)
            struct.pack_into("<I", src_buf, 0x30, 0x9999)
            struct.pack_into("<h", src_buf, 0x00, 50 if stat_match else 99)
            struct.pack_into("<h", src_buf, 0x02, 60)
            struct.pack_into("<h", src_buf, 0x04, 100 - 10) # 90
            struct.pack_into("<h", src_buf, 0x06, 110 - 10)
            struct.pack_into("<h", src_buf, 0x08, 120 - 10)
            struct.pack_into("<h", src_buf, 0x0A, 130 - 10)
            struct.pack_into("<h", src_buf, 0x0C, 140 - 10)

            # r4 + 0x500 bonuses:
            struct.pack_into("<H", src_buf, 0x590, 10)
            struct.pack_into("<H", src_buf, 0x592, 10)
            struct.pack_into("<H", src_buf, 0x594, 10)
            struct.pack_into("<H", src_buf, 0x596, 10)
            struct.pack_into("<H", src_buf, 0x598, 10)

            # Skills in r4 at 0x34:
            if skill_cnt > 0:
                struct.pack_into("<H", src_buf, 0x34, 0x101)
                struct.pack_into("<H", src_buf, 0x36, 0x102)
                struct.pack_into("<H", src_buf, 0x38, 0x103 if skill_match else 0x999)
            else:
                struct.pack_into("<H", src_buf, 0x34, 0)

            uc.mem_write(SRC_ADDR, bytes(src_buf))

            uc.reg_write(UC_ARM_REG_R0, SRC_ADDR)
            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, RET_ADDR)

            uc.emu_start(ADDR, RET_ADDR, timeout=2000000)

            ret_r0 = uc.reg_read(UC_ARM_REG_R0)
            return ret_r0

        orig_ret = run_sim(orig_code)
        comp_ret = run_sim(comp_code)

        assert orig_ret == comp_ret, f"{name}: ret mismatch (orig={orig_ret}, comp={comp_ret})"

    print(f"PASS: camp_func_002cd2cc (all {len(cases)} cases passed)")

# -------------------------------------------------------------------------
# Test 5: camp_func_002cf308 (0x002cf308)
# -------------------------------------------------------------------------
def test_camp_func_002cf308():
    ADDR = 0x002cf308
    ORIG_SIZE = 444
    orig_code = load_original_bytes(ADDR, ORIG_SIZE)
    comp_body, relocs = compile_function("camp_func_002cf308")
    comp_code = stage_body(comp_body, relocs, ADDR, BASE_SYMS, "camp_func_002cf308")

    RET_ADDR = 0x004F0000
    BX_LR = struct.pack("<I", 0xE12FFF1E)

    cases = [
        ("all_zeros", bytes([0x00] * 32)),
        ("all_ones", bytes([0xFF] * 32)),
        ("alternating_bits", bytes([0x80 if i % 2 == 0 else 0x00 for i in range(32)])),
        ("random_mixed", bytes([(i * 37 + 13) & 0xFF for i in range(32)])),
    ]

    for name, init_data in cases:
        def run_sim(code: bytes):
            uc = create_emulator()
            uc.mem_write(ADDR, code)
            uc.mem_write(RET_ADDR, BX_LR)

            TBL_ADDR = 0x10010000
            uc.mem_write(TBL_ADDR, init_data)

            # camp_func_002a0fac returns TBL_ADDR
            uc.mem_write(CALL_2A0FAC, struct.pack("<II", 0xE59F0000, 0xE12FFF1E) + struct.pack("<I", TBL_ADDR))

            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, RET_ADDR)

            uc.emu_start(ADDR, RET_ADDR, timeout=2000000)

            final_data = uc.mem_read(TBL_ADDR, 27)
            return final_data

        orig_data = run_sim(orig_code)
        comp_data = run_sim(comp_code)

        assert orig_data == comp_data, f"{name}: table mismatch (orig={orig_data.hex()}, comp={comp_data.hex()})"

    print(f"PASS: camp_func_002cf308 (all {len(cases)} cases passed)")

if __name__ == "__main__":
    test_engine_func_002bbb2c()
    test_engine_func_002c15d8()
    test_engine_func_002c2cf0()
    test_camp_func_002cd2cc()
    test_camp_func_002cf308()
    print("\nALL 5 CANDIDATES IN PART 15 PASSED DIFFERENTIAL VERIFICATION!")
