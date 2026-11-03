#!/usr/bin/env python3
"""Differential test for batch 30 B part 3:
- shop_func_00230db0 (0x00230DB0, 100 B)
- func_00232974 (0x00232974, 104 B)
- script_vm_func_00234304 (0x00234304, 100 B)
- script_vm_func_00234608 (0x00234608, 100 B)
- engine_func_00234738 (0x00234738, 116 B)
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


def test_00230db0():
    print("--- Testing shop_func_00230db0 ---")
    addr = 0x00230DB0
    size = 100
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("shop_func_00230db0", ROOT / "build")
    symbol_map = {
        "script_vm_func_0022ebbc": 0x0022EBBC,
        "ui_func_002c615c": 0x002C615C,
        "camp_func_002b9100": 0x002B9100,
        "camp_func_0028fde4": 0x0028FDE4,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    ITEM_PTR = 0x20004000
    OBJ_PTR = 0x20005000

    def run_one(c_bytes, count_in, c615c_ret, cap_ret, cur_ret):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        def on_22ebbc(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, ITEM_PTR)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_2c615c(uc, address, size, user_data):
            assert uc.reg_read(UC_ARM_REG_R0) == ITEM_PTR
            assert uc.reg_read(UC_ARM_REG_R1) == (count_in & 0xFFFFFFFF)
            uc.reg_write(UC_ARM_REG_R0, c615c_ret & 0xFFFFFFFF)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_2b9100(uc, address, size, user_data):
            assert uc.reg_read(UC_ARM_REG_R0) == OBJ_PTR
            uc.reg_write(UC_ARM_REG_R0, cap_ret & 0xFFFFFFFF)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_28fde4(uc, address, size, user_data):
            assert uc.reg_read(UC_ARM_REG_R0) == OBJ_PTR
            uc.reg_write(UC_ARM_REG_R0, cur_ret & 0xFFFFFFFF)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h1 = uc.hook_add(UC_HOOK_CODE, on_22ebbc, None, 0x0022EBBC, 0x0022EBBC)
        h2 = uc.hook_add(UC_HOOK_CODE, on_2c615c, None, 0x002C615C, 0x002C615C)
        h3 = uc.hook_add(UC_HOOK_CODE, on_2b9100, None, 0x002B9100, 0x002B9100)
        h4 = uc.hook_add(UC_HOOK_CODE, on_28fde4, None, 0x0028FDE4, 0x0028FDE4)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, OBJ_PTR)
        uc.reg_write(UC_ARM_REG_R1, count_in & 0xFFFFFFFF)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h1)
        uc.hook_del(h2)
        uc.hook_del(h3)
        uc.hook_del(h4)

        r0 = uc.reg_read(UC_ARM_REG_R0)
        if r0 >= 0x80000000:
            r0 -= 0x100000000
        regs = [uc.reg_read(getattr(sys.modules[__name__], f"UC_ARM_REG_R{i}")) for i in range(4, 7)]
        return r0, regs

    cases = [
        # (count_in, c615c_ret, cap_ret, cur_ret)
        (5, -5, 50, 40),   # clamped to 0 -> diff=10 -> returns 0
        (10, 15, 50, 40),  # clamped=15, diff=10 < 15 -> returns 10
        (10, 15, 50, 20),  # clamped=15, diff=30 > 15 -> returns 15
        (50, 150, 100, 10), # clamped to 99, diff=90 < 99 -> returns 90
        (50, 150, 200, 10), # clamped to 99, diff=190 > 99 -> returns 99
        (5, 5, 10, 20),    # clamped=5, diff=-10 < 5 -> returns -10
    ]

    for count_in, c_ret, cap, cur in cases:
        orig_r0, orig_regs = run_one(orig, count_in, c_ret, cap, cur)
        comp_r0, comp_regs = run_one(staged, count_in, c_ret, cap, cur)
        assert orig_r0 == comp_r0, f"Mismatch: r0 orig={orig_r0}, comp={comp_r0}"
        assert orig_regs == comp_regs, f"Register mismatch: orig={orig_regs}, comp={comp_regs}"

    print("shop_func_00230db0: PASS")


def test_00232974():
    print("--- Testing func_00232974 ---")
    addr = 0x00232974
    size = 104
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_00232974", ROOT / "build")
    staged = stage_body(comp, relocs, addr, {})

    SRC = 0x20001000
    DST = 0x20002000

    def run_one(c_bytes, test_bytes):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # clear buffers
        uc.mem_write(SRC, b"\x00" * 0x200)
        uc.mem_write(DST, b"\xcc" * 0x100)

        # write test pattern into src + 0xB0 .. src + 0xB0 + 18
        uc.mem_write(SRC + 0xB0, test_bytes)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, SRC)
        uc.reg_write(UC_ARM_REG_R1, DST)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)

        dst_out = uc.mem_read(DST, 20)
        regs = [uc.reg_read(getattr(sys.modules[__name__], f"UC_ARM_REG_R{i}")) for i in range(4, 7)]
        return dst_out, regs

    patterns = [
        bytes([i * 13 % 256 for i in range(18)]),
        bytes([0xFF, 0x80, 0x00, 0x01, 0x7F, 0xFF, 0x80, 0x00, 0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0, 0x11, 0x22]),
        bytes([0] * 18),
        bytes([0xFF] * 18),
    ]

    for pat in patterns:
        orig_out, orig_regs = run_one(orig, pat)
        comp_out, comp_regs = run_one(staged, pat)
        assert orig_out == comp_out, f"Memory mismatch: orig={orig_out.hex()}, comp={comp_out.hex()}"
        assert orig_regs == comp_regs, f"Register mismatch: orig={orig_regs}, comp={comp_regs}"

    print("func_00232974: PASS")


def test_00234304():
    print("--- Testing script_vm_func_00234304 ---")
    addr = 0x00234304
    size = 100
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_00234304", ROOT / "build")
    symbol_map = {"engine_func_002b45f8": 0x002B45F8}
    staged = stage_body(comp, relocs, addr, symbol_map)

    def run_one(c_bytes, count, match_index):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        CONTAINER = 0x20001000
        OBJ = 0x20002000
        ENTRIES = 0x20003000
        KEY_TARGET = 0x20004000

        uc.mem_write(CONTAINER, struct.pack("<I", OBJ))
        uc.mem_write(OBJ + 0x1C, struct.pack("<I", count))
        uc.mem_write(OBJ + 0x18, struct.pack("<I", ENTRIES))

        # Setup entries
        for i in range(count):
            entry_key = 0x20005000 + i * 0x100
            val = 0x1000 + i * 11
            uc.mem_write(ENTRIES + i * 8, struct.pack("<II", entry_key, val))

        def on_b45f8(uc, address, size, user_data):
            s1 = uc.reg_read(UC_ARM_REG_R0)
            s2 = uc.reg_read(UC_ARM_REG_R1)
            n = uc.reg_read(UC_ARM_REG_R2)
            assert s2 == KEY_TARGET
            assert n == 0x40
            idx = (s1 - 0x20005000) // 0x100
            ret = 0 if idx == match_index else 1
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h_mock = uc.hook_add(UC_HOOK_CODE, on_b45f8, None, 0x002B45F8, 0x002B45F8)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, CONTAINER)
        uc.reg_write(UC_ARM_REG_R1, KEY_TARGET)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h_mock)

        r0 = uc.reg_read(UC_ARM_REG_R0)
        regs = [uc.reg_read(getattr(sys.modules[__name__], f"UC_ARM_REG_R{i}")) for i in range(4, 9)]
        return r0, regs

    cases = [
        (0, -1),  # count 0 -> 0
        (1, 0),   # match at 0 -> val0
        (4, 2),   # match at 2 -> val2
        (4, -1),  # no match -> 0
    ]

    for count, m_idx in cases:
        orig_r0, orig_regs = run_one(orig, count, m_idx)
        comp_r0, comp_regs = run_one(staged, count, m_idx)
        assert orig_r0 == comp_r0, f"Mismatch: count={count}, m_idx={m_idx} -> orig={orig_r0}, comp={comp_r0}"
        assert orig_regs == comp_regs, f"Register mismatch: orig={orig_regs}, comp={comp_regs}"

    print("script_vm_func_00234304: PASS")


def test_00234608():
    print("--- Testing script_vm_func_00234608 ---")
    addr = 0x00234608
    size = 100
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_00234608", ROOT / "build")
    symbol_map = {"engine_func_002b45f8": 0x002B45F8}
    staged = stage_body(comp, relocs, addr, symbol_map)

    def run_one(c_bytes, count, match_index):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        CONTAINER = 0x20001000
        OBJ = 0x20002000
        ENTRIES = 0x20003000
        KEY_TARGET = 0x20004000

        uc.mem_write(CONTAINER, struct.pack("<I", OBJ))
        uc.mem_write(OBJ + 0x1C, struct.pack("<I", count))
        uc.mem_write(OBJ + 0x18, struct.pack("<I", ENTRIES))

        for i in range(count):
            entry_key = 0x20005000 + i * 0x100
            val = 0x2000 + i * 17
            uc.mem_write(ENTRIES + i * 8, struct.pack("<II", entry_key, val))

        def on_b45f8(uc, address, size, user_data):
            s1 = uc.reg_read(UC_ARM_REG_R0)
            s2 = uc.reg_read(UC_ARM_REG_R1)
            n = uc.reg_read(UC_ARM_REG_R2)
            assert s2 == KEY_TARGET
            assert n == 0x40
            idx = (s1 - 0x20005000) // 0x100
            ret = 0 if idx == match_index else 1
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h_mock = uc.hook_add(UC_HOOK_CODE, on_b45f8, None, 0x002B45F8, 0x002B45F8)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, CONTAINER)
        uc.reg_write(UC_ARM_REG_R1, KEY_TARGET)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h_mock)

        r0 = uc.reg_read(UC_ARM_REG_R0)
        regs = [uc.reg_read(getattr(sys.modules[__name__], f"UC_ARM_REG_R{i}")) for i in range(4, 9)]
        return r0, regs

    cases = [
        (0, -1),
        (1, 0),
        (5, 3),
        (5, -1),
    ]

    for count, m_idx in cases:
        orig_r0, orig_regs = run_one(orig, count, m_idx)
        comp_r0, comp_regs = run_one(staged, count, m_idx)
        assert orig_r0 == comp_r0, f"Mismatch: orig={orig_r0}, comp={comp_r0}"
        assert orig_regs == comp_regs, f"Register mismatch: orig={orig_regs}, comp={comp_regs}"

    print("script_vm_func_00234608: PASS")


def test_00234738():
    print("--- Testing engine_func_00234738 ---")
    addr = 0x00234738
    size = 116
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_00234738", ROOT / "build")
    symbol_map = {
        "func_0023a390": 0x0023A390,
        "engine_func_002bad80": 0x002BAD80,
        "ui_func_00353578": 0x00353578,
        "engine_func_0023a358": 0x0023A358,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    DST = 0x20001000
    ARG1 = 0x20002000

    def run_one(c_bytes, status, res_353578):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        uc.mem_write(DST, b"\x00" * 16)

        calls = []

        def on_23a390(uc, address, size, user_data):
            a1 = uc.reg_read(UC_ARM_REG_R0)
            assert a1 == ARG1
            calls.append(("23a390", a1))
            uc.reg_write(UC_ARM_REG_R0, status & 0xFFFFFFFF)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_2bad80(uc, address, size, user_data):
            dst = uc.reg_read(UC_ARM_REG_R0)
            code = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("2bad80", dst, code))
            # write mock payload to dst
            uc.mem_write(dst, struct.pack("<II", code ^ 0x12345678, code ^ 0x9ABCDEF0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_353578(uc, address, size, user_data):
            a0 = uc.reg_read(UC_ARM_REG_R0)
            a1 = uc.reg_read(UC_ARM_REG_R1)
            a2 = uc.reg_read(UC_ARM_REG_R2)
            calls.append(("353578", a0, a1, a2))
            uc.reg_write(UC_ARM_REG_R0, res_353578 & 0xFFFFFFFF)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_23a358(uc, address, size, user_data):
            a0 = uc.reg_read(UC_ARM_REG_R0)
            w0 = uc.reg_read(UC_ARM_REG_R1)
            w1 = uc.reg_read(UC_ARM_REG_R2)
            calls.append(("23a358", a0, w0, w1))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h1 = uc.hook_add(UC_HOOK_CODE, on_23a390, None, 0x0023A390, 0x0023A390)
        h2 = uc.hook_add(UC_HOOK_CODE, on_2bad80, None, 0x002BAD80, 0x002BAD80)
        h3 = uc.hook_add(UC_HOOK_CODE, on_353578, None, 0x00353578, 0x00353578)
        h4 = uc.hook_add(UC_HOOK_CODE, on_23a358, None, 0x0023A358, 0x0023A358)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, DST)
        uc.reg_write(UC_ARM_REG_R1, ARG1)
        uc.reg_write(UC_ARM_REG_R2, 0x100)
        uc.reg_write(UC_ARM_REG_R3, 0x200)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h1)
        uc.hook_del(h2)
        uc.hook_del(h3)
        uc.hook_del(h4)

        dst_mem = uc.mem_read(DST, 8)
        regs = [uc.reg_read(getattr(sys.modules[__name__], f"UC_ARM_REG_R{i}")) for i in range(4, 8)]
        return dst_mem, calls, regs

    cases = [
        (-1, 0x55), # status < 0
        (-100, 0),  # status < 0
        (0, 0x1234), # status >= 0
        (1, 0xABCD), # status >= 0
    ]

    for status, res in cases:
        orig_mem, orig_calls, orig_regs = run_one(orig, status, res)
        comp_mem, comp_calls, comp_regs = run_one(staged, status, res)
        assert orig_mem == comp_mem, f"Memory mismatch: orig={orig_mem.hex()}, comp={comp_mem.hex()}"
        # verify call sequence types match
        orig_seq = [c[0] for c in orig_calls]
        comp_seq = [c[0] for c in comp_calls]
        assert orig_seq == comp_seq, f"Call seq mismatch: orig={orig_seq}, comp={comp_seq}"
        assert orig_regs == comp_regs, f"Register mismatch: orig={orig_regs}, comp={comp_regs}"

    print("engine_func_00234738: PASS")


if __name__ == "__main__":
    test_00230db0()
    test_00232974()
    test_00234304()
    test_00234608()
    test_00234738()
    print("\nALL 5 FUNCTIONS PASSED 100% DIFFERENTIAL VERIFICATION!")
