#!/usr/bin/env python3
"""Differential test for batch 31 B part 18:
- func_00353160 (0x00353160, 76 B)
- func_0035f454 (0x0035F454, 76 B)
- engine_func_00379a28 (0x00379A28, 76 B)
- func_003972c8 (0x003972C8, 76 B)
- func_003eb014 (0x003EB014, 76 B)
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
SOURCE = ROOT / "src/engine/leaf_batch31_b.cpp"

with open(ORIG_BIN, "rb") as f:
    ORIG_DATA = f.read()

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch31_b.o"
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
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, unmapped_hook)

    val = uc.reg_read(UC_ARM_REG_C1_C0_2)
    val |= (0xF << 20)
    uc.reg_write(UC_ARM_REG_C1_C0_2, val)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return uc

def test_func_00353160():
    addr = 0x00353160
    print(f"--- Testing func_00353160 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 76)
    tmp = ROOT / "build" / "test_31b_part18"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00353160", tmp)

    HELPER_ADDR = 0x003523D8
    sym_map = {"func_003523d8": HELPER_ADDR}
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    test_cases = [
        # (mock_ret, mock_temp_byte, a0, a1)
        (0xD8A083FA, 0, 10, 20),
        (0xD8A083FA, 1, 10, 20),
        (0xC0000005, 0, 5, 15),
        (0x80000001, 1, 1, 2),
        (0x00000000, 0, 100, 200),
        (0x00000000, 1, 100, 200),
        (0x00000000, 0xFF, 100, 200),
        (0x00000001, 0, 0, 0),
        (0x00000001, 2, 0, 0),
    ]

    def run_one(code, mock_ret, mock_temp, a0, a1):
        uc = create_emulator()
        uc.mem_write(addr, code)

        captured_args = []
        def helper_hook(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            arg2 = uc.reg_read(UC_ARM_REG_R2)
            arg3 = uc.reg_read(UC_ARM_REG_R3)
            captured_args.append((arg1, arg2, arg3))
            # write mock temp byte to ptr arg0
            uc.mem_write(arg0, bytes([mock_temp]))
            uc.reg_write(UC_ARM_REG_R0, mock_ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, helper_hook, None, HELPER_ADDR, HELPER_ADDR)

        uc.reg_write(UC_ARM_REG_R0, a0)
        uc.reg_write(UC_ARM_REG_R1, a1)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, captured_args

    for mock_ret, mock_temp, a0, a1 in test_cases:
        orig_ret, orig_args = run_one(orig_code, mock_ret, mock_temp, a0, a1)
        decomp_ret, decomp_args = run_one(decomp_code, mock_ret, mock_temp, a0, a1)
        assert orig_args == [(1, a0, a1)], f"Orig args mismatch: {orig_args}"
        assert decomp_args == [(1, a0, a1)], f"Decomp args mismatch: {decomp_args}"
        assert orig_ret == decomp_ret, f"Mismatch for case ({hex(mock_ret)}, {mock_temp}): orig {hex(orig_ret)} vs decomp {hex(decomp_ret)}"

    print("func_00353160: PASS")

def test_func_0035f454():
    addr = 0x0035F454
    print(f"--- Testing func_0035f454 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 76)
    tmp = ROOT / "build" / "test_31b_part18"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0035f454", tmp)
    assert not relocs
    decomp_code = comp

    test_strings = [
        ("", 0),
        ("", 5),
        ("hello", 5),
        ("hello", -1),
        ("foo@bar", 7),
        ("foo@bar", 3),     # '@' is at index 3, max_len 3 -> not visited (indices 0, 1, 2)
        ("foo@bar", 4),     # '@' is at index 3, max_len 4 -> found!
        ("test\uff20test", 9), # fullwidth '@'
        ("\x00@bar", 5),     # null before @
        ("@", 1),
        ("@@", 2),
    ]

    def run_one(code, text, max_len):
        uc = create_emulator()
        uc.mem_write(addr, code)

        str_buf = 0x10082000
        # encode UTF-16LE
        raw = text.encode("utf-16le") + b"\x00\x00"
        uc.mem_write(str_buf, raw)

        uc.reg_write(UC_ARM_REG_R0, 0x12345678)
        uc.reg_write(UC_ARM_REG_R1, str_buf)
        uc.reg_write(UC_ARM_REG_R2, max_len & 0xFFFFFFFF)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        return uc.reg_read(UC_ARM_REG_R0)

    for text, max_len in test_strings:
        orig_ret = run_one(orig_code, text, max_len)
        decomp_ret = run_one(decomp_code, text, max_len)
        assert orig_ret == decomp_ret, f"Mismatch for '{text}', len {max_len}: orig {orig_ret} vs decomp {decomp_ret}"

    print("func_0035f454: PASS")

def test_engine_func_00379a28():
    addr = 0x00379A28
    print(f"--- Testing engine_func_00379a28 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 76)
    tmp = ROOT / "build" / "test_31b_part18"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_00379a28", tmp)

    MEMCPY_ADDR = 0x002C5FF4
    sym_map = {"engine_func_002c5ff4": MEMCPY_ADDR}
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, vcall_returns_null: bool):
        uc = create_emulator()
        uc.mem_write(addr, code)

        dst = 0x10082000
        src = 0x10083000
        obj = 0x10084000
        vtable = 0x10085000
        vfn = 0x10086000
        res_obj = 0 if vcall_returns_null else 0x10087000

        uc.mem_write(dst, b"\xAA" * 0x40)
        uc.mem_write(src, struct.pack("<IIIII", 0x11111111, 0x22222222, obj, 0x33333333, 0x44444444))
        uc.mem_write(obj, struct.pack("<I", vtable))
        # vtable[2] is at vtable + 8
        uc.mem_write(vtable + 8, struct.pack("<I", vfn))

        vcall_calls = []
        def vcall_hook(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            vcall_calls.append((arg0, arg1))
            uc.reg_write(UC_ARM_REG_R0, res_obj)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, vcall_hook, None, vfn, vfn)

        memcpy_calls = []
        def memcpy_hook(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            arg2 = uc.reg_read(UC_ARM_REG_R2)
            memcpy_calls.append((arg0, arg1, arg2))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, memcpy_hook, None, MEMCPY_ADDR, MEMCPY_ADDR)

        uc.reg_write(UC_ARM_REG_R0, dst)
        uc.reg_write(UC_ARM_REG_R1, src)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        dst_data = uc.mem_read(dst, 0x40)
        return dst_data, vcall_calls, memcpy_calls

    for returns_null in [False, True]:
        o_dst, o_v, o_m = run_one(orig_code, returns_null)
        d_dst, d_v, d_m = run_one(decomp_code, returns_null)
        assert o_dst == d_dst, f"dst data mismatch (returns_null={returns_null})"
        assert o_v == d_v, f"vcall mismatch (returns_null={returns_null})"
        assert o_m == d_m, f"memcpy mismatch (returns_null={returns_null})"

    print("engine_func_00379a28: PASS")

def test_func_003972c8():
    addr = 0x003972C8
    print(f"--- Testing func_003972c8 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 76)
    tmp = ROOT / "build" / "test_31b_part18"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003972c8", tmp)

    sym_map = {"func_003972c8": addr}
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_traversal(code, test_mode: str):
        uc = create_emulator()
        uc.mem_write(addr, code)

        tree = 0x10082000
        vtable = 0x10083000
        destroy_fn = 0x10084000
        sentinel = tree + 8

        uc.mem_write(tree, struct.pack("<I", vtable))
        uc.mem_write(vtable, struct.pack("<I", destroy_fn))

        destroyed_nodes = []
        def destroy_hook(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            destroyed_nodes.append((arg0, arg1))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, destroy_hook, None, destroy_fn, destroy_fn)

        if test_mode == "empty":
            root = sentinel
        elif test_mode == "single":
            root = 0x10085000
            uc.mem_write(root, struct.pack("<II", sentinel, sentinel))
        elif test_mode == "tree":
            # root -> left, right
            # left -> sentinel, left_right
            # left_right -> sentinel, sentinel
            # right -> sentinel, sentinel
            root = 0x10085000
            n_left = 0x10085010
            n_right = 0x10085020
            n_left_right = 0x10085030

            uc.mem_write(root, struct.pack("<II", n_left, n_right))
            uc.mem_write(n_left, struct.pack("<II", sentinel, n_left_right))
            uc.mem_write(n_left_right, struct.pack("<II", sentinel, sentinel))
            uc.mem_write(n_right, struct.pack("<II", sentinel, sentinel))

        uc.reg_write(UC_ARM_REG_R0, tree)
        uc.reg_write(UC_ARM_REG_R1, root)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return destroyed_nodes

    for mode in ["empty", "single", "tree"]:
        o_nodes = run_traversal(orig_code, mode)
        d_nodes = run_traversal(decomp_code, mode)
        assert o_nodes == d_nodes, f"Mismatch in mode {mode}: orig {o_nodes} vs decomp {d_nodes}"

    print("func_003972c8: PASS")

def test_func_003eb014():
    addr = 0x003EB014
    print(f"--- Testing func_003eb014 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 76)
    tmp = ROOT / "build" / "test_31b_part18"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003eb014", tmp)

    FN_2BD630 = 0x002BD630
    FN_2B7770 = 0x002B7770
    sym_map = {
        "func_002bd630": FN_2BD630,
        "func_002b7770": FN_2B7770,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    # Base at 0x10082000, obj_44 at 0x10082044
    base = 0x10082000
    obj_44 = base + 0x44

    test_cases = [
        # (flag_0c, val_64, min_val, max_val, flag_0d)
        (0, 50, 10, 100, 1),      # flag_0c is 0 -> bail
        (1, 5, 10, 100, 1),       # val < min -> bail
        (1, 150, 10, 100, 1),     # val > max -> bail
        (1, 50, 10, 100, 0),      # flag_0d is 0 -> bail
        (1, 10, 10, 100, 1),      # boundary val == min -> pass!
        (1, 100, 10, 100, 1),     # boundary val == max -> pass!
        (1, 50, 10, 100, 1),      # inside range -> pass!
        (1, 50, 10, 100, 0x55),   # inside range with arbitrary flag_0d -> pass!
    ]

    def run_one(code, flag_0c, val_64, min_val, max_val, flag_0d):
        uc = create_emulator()
        uc.mem_write(addr, code)

        mem = bytearray(0x80)
        mem[0x0C] = flag_0c
        mem[0x0D] = flag_0d
        struct.pack_into("<I", mem, 0x64, val_64)
        uc.mem_write(base, bytes(mem))

        calls = []
        ctx_val = 0x10085000
        def f_2bd630(uc, address, size, user_data):
            calls.append("get_ctx")
            uc.reg_write(UC_ARM_REG_R0, ctx_val)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_2b7770(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("f_7770", arg0, arg1))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_2bd630, None, FN_2BD630, FN_2BD630)
        uc.hook_add(UC_HOOK_CODE, f_2b7770, None, FN_2B7770, FN_2B7770)

        uc.reg_write(UC_ARM_REG_R0, obj_44)
        uc.reg_write(UC_ARM_REG_R1, min_val)
        uc.reg_write(UC_ARM_REG_R2, max_val)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        final_flag_0d = uc.mem_read(base + 0x0D, 1)[0]
        return final_flag_0d, calls

    for flag_0c, val_64, min_val, max_val, flag_0d in test_cases:
        o_0d, o_calls = run_one(orig_code, flag_0c, val_64, min_val, max_val, flag_0d)
        d_0d, d_calls = run_one(decomp_code, flag_0c, val_64, min_val, max_val, flag_0d)
        assert o_0d == d_0d, f"flag_0d mismatch: orig {o_0d} vs decomp {d_0d}"
        assert o_calls == d_calls, f"calls mismatch: orig {o_calls} vs decomp {d_calls}"

    print("func_003eb014: PASS")

if __name__ == "__main__":
    test_func_00353160()
    test_func_0035f454()
    test_engine_func_00379a28()
    test_func_003972c8()
    test_func_003eb014()
    print("\nALL 5 FUNCTIONS IN PART 18 PASSED DIFFERENTIAL VERIFICATION!")
