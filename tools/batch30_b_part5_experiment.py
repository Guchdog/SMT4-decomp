#!/usr/bin/env python3
"""Differential test for batch 30 B part 5:
- engine_func_00240e1c (0x00240E1C, 112 B)
- ui_func_0024807c (0x0024807C, 116 B)
- script_vm_func_00248358 (0x00248358, 96 B)
- camp_func_002483b8 (0x002483B8, 96 B)
- engine_func_0024a964 (0x0024A964, 112 B)
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


def test_00240e1c():
    print("--- Testing engine_func_00240e1c ---")
    addr = 0x00240E1C
    size = 112
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_00240e1c", ROOT / "build")
    symbol_map = {"engine_func_002c5ab8": 0x002C5AB8}
    staged = stage_body(comp, relocs, addr, symbol_map)

    STATE_ADDR = 0x0044CF60

    def run_one(c_bytes, init_state0, init_state1, cmd):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        uc.mem_write(STATE_ADDR, struct.pack("<II", init_state0, init_state1))

        calls = []
        def on_2c5ab8(uc, address, size, user_data):
            a0 = uc.reg_read(UC_ARM_REG_R0)
            a1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append((a0, a1))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h_mock = uc.hook_add(UC_HOOK_CODE, on_2c5ab8, None, 0x002C5AB8, 0x002C5AB8)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, cmd)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h_mock)

        state_out = struct.unpack("<II", uc.mem_read(STATE_ADDR, 8))
        reg_r4 = uc.reg_read(UC_ARM_REG_R4)
        return state_out, calls, reg_r4

    cases = [
        (0, 0, 0x65),
        (0, 0, 0x66),
        (0, 0, 0x67),
        (0, 0, 0x10),
        (1, 0x65, 0x66),
        (5, 0x123, 0x65),
    ]

    for s0, s1, cmd in cases:
        orig_state, orig_calls, orig_r4 = run_one(orig, s0, s1, cmd)
        comp_state, comp_calls, comp_r4 = run_one(staged, s0, s1, cmd)
        assert orig_state == comp_state, f"Mismatch state: orig={orig_state}, comp={comp_state}"
        assert orig_calls == comp_calls, f"Mismatch calls: orig={orig_calls}, comp={comp_calls}"
        assert orig_r4 == comp_r4, f"Mismatch r4: orig={orig_r4}, comp={comp_r4}"

    print("engine_func_00240e1c: PASS")


def test_0024807c():
    print("--- Testing ui_func_0024807c ---")
    addr = 0x0024807C
    size = 116
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_0024807c", ROOT / "build")
    symbol_map = {"func_002b3b34": 0x002B3B34}
    staged = stage_body(comp, relocs, addr, symbol_map)

    def run_one(c_bytes, min_v, max_v, dur, cur):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        def on_2b3b34(uc, address, size, user_data):
            angle = uc.reg_read(UC_ARM_REG_R0) & 0xFFFF
            # return float in s0 (e.g. angle / 16384.0f)
            factor = angle / 16384.0
            uc.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", factor))[0])
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h_mock = uc.hook_add(UC_HOOK_CODE, on_2b3b34, None, 0x002B3B34, 0x002B3B34)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", min_v))[0])
        uc.reg_write(UC_ARM_REG_S1, struct.unpack("<I", struct.pack("<f", max_v))[0])
        uc.reg_write(UC_ARM_REG_S2, struct.unpack("<I", struct.pack("<f", dur))[0])
        uc.reg_write(UC_ARM_REG_S3, struct.unpack("<I", struct.pack("<f", cur))[0])

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h_mock)

        s0_raw = uc.reg_read(UC_ARM_REG_S0)
        s0_float = struct.unpack("<f", struct.pack("<I", s0_raw))[0]
        reg_r4 = uc.reg_read(UC_ARM_REG_R4)
        return s0_float, reg_r4

    cases = [
        (10.0, 20.0, 0.0, 5.0),    # dur == 0 -> max_v (20.0)
        (10.0, 20.0, 100.0, 0.0),  # cur <= 0 -> min_v (10.0)
        (10.0, 20.0, 100.0, -5.0), # cur <= 0 -> min_v (10.0)
        (10.0, 20.0, 100.0, 100.0),# cur >= dur -> max_v (20.0)
        (10.0, 20.0, 100.0, 150.0),# cur >= dur -> max_v (20.0)
        (10.0, 20.0, 100.0, 50.0), # interpolates
        (20.0, 10.0, 100.0, 25.0), # reverse lerp
    ]

    for min_v, max_v, dur, cur in cases:
        orig_s0, orig_r4 = run_one(orig, min_v, max_v, dur, cur)
        comp_s0, comp_r4 = run_one(staged, min_v, max_v, dur, cur)
        assert abs(orig_s0 - comp_s0) < 1e-4, f"Mismatch s0: orig={orig_s0}, comp={comp_s0}"
        assert orig_r4 == comp_r4, f"Mismatch r4: orig={orig_r4}, comp={comp_r4}"

    print("ui_func_0024807c: PASS")


def test_00248358():
    print("--- Testing script_vm_func_00248358 ---")
    addr = 0x00248358
    size = 96
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_00248358", ROOT / "build")
    symbol_map = {
        "camp_func_002c0ec4": 0x002C0EC4,
        "camp_func_002c0e9c": 0x002C0E9C,
        "camp_func_002c0e4c": 0x002C0E4C,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    RES1 = 0x20001000
    BASE1 = 0x20002000
    MGR = 0x20003000
    BASE2 = 0x20004000

    def run_one(c_bytes, id_in, count1, count2):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # [0x00433158] = MGR
        uc.mem_write(0x00433158, struct.pack("<I", MGR))
        uc.mem_write(MGR + 0x3F4, struct.pack("<II", count2, BASE2))

        def on_2c0ec4(uc, address, size, user_data):
            assert uc.reg_read(UC_ARM_REG_R0) == 0x23
            assert uc.reg_read(UC_ARM_REG_R1) == 2
            uc.reg_write(UC_ARM_REG_R0, RES1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_2c0e9c(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, BASE1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_2c0e4c(uc, address, size, user_data):
            assert uc.reg_read(UC_ARM_REG_R0) == RES1
            uc.reg_write(UC_ARM_REG_R0, count1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h1 = uc.hook_add(UC_HOOK_CODE, on_2c0ec4, None, 0x002C0EC4, 0x002C0EC4)
        h2 = uc.hook_add(UC_HOOK_CODE, on_2c0e9c, None, 0x002C0E9C, 0x002C0E9C)
        h3 = uc.hook_add(UC_HOOK_CODE, on_2c0e4c, None, 0x002C0E4C, 0x002C0E4C)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, id_in)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h1)
        uc.hook_del(h2)
        uc.hook_del(h3)

        r0 = uc.reg_read(UC_ARM_REG_R0)
        regs = [uc.reg_read(getattr(sys.modules[__name__], f"UC_ARM_REG_R{i}")) for i in range(4, 7)]
        return r0, regs

    cases = [
        (0, 5, 10),   # seg 1: base1 + 0*32
        (4, 5, 10),   # seg 1: base1 + 4*32
        (5, 5, 10),   # seg 2: base2 + 0*32
        (14, 5, 10),  # seg 2: base2 + 9*32
        (15, 5, 10),  # out: 0
        (20, 5, 10),  # out: 0
    ]

    for id_in, c1, c2 in cases:
        orig_r0, orig_regs = run_one(orig, id_in, c1, c2)
        comp_r0, comp_regs = run_one(staged, id_in, c1, c2)
        assert orig_r0 == comp_r0, f"Mismatch r0: orig={hex(orig_r0)}, comp={hex(comp_r0)}"
        assert orig_regs == comp_regs, f"Mismatch regs: orig={orig_regs}, comp={comp_regs}"

    print("script_vm_func_00248358: PASS")


def test_002483b8():
    print("--- Testing camp_func_002483b8 ---")
    addr = 0x002483B8
    size = 96
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("camp_func_002483b8", ROOT / "build")
    symbol_map = {
        "camp_func_002c0ec4": 0x002C0EC4,
        "camp_func_002c0e9c": 0x002C0E9C,
        "camp_func_002c0e4c": 0x002C0E4C,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    RES1 = 0x20001000
    BASE1 = 0x20002000
    MGR = 0x20003000
    BASE2 = 0x20004000

    def run_one(c_bytes, id_in, count1, count2):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # [0x00433158] = MGR
        uc.mem_write(0x00433158, struct.pack("<I", MGR))
        uc.mem_write(MGR + 0x3E4, struct.pack("<II", count2, BASE2))

        def on_2c0ec4(uc, address, size, user_data):
            assert uc.reg_read(UC_ARM_REG_R0) == 0x23
            assert uc.reg_read(UC_ARM_REG_R1) == 0
            uc.reg_write(UC_ARM_REG_R0, RES1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_2c0e9c(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, BASE1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_2c0e4c(uc, address, size, user_data):
            assert uc.reg_read(UC_ARM_REG_R0) == RES1
            uc.reg_write(UC_ARM_REG_R0, count1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h1 = uc.hook_add(UC_HOOK_CODE, on_2c0ec4, None, 0x002C0EC4, 0x002C0EC4)
        h2 = uc.hook_add(UC_HOOK_CODE, on_2c0e9c, None, 0x002C0E9C, 0x002C0E9C)
        h3 = uc.hook_add(UC_HOOK_CODE, on_2c0e4c, None, 0x002C0E4C, 0x002C0E4C)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, id_in)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h1)
        uc.hook_del(h2)
        uc.hook_del(h3)

        r0 = uc.reg_read(UC_ARM_REG_R0)
        regs = [uc.reg_read(getattr(sys.modules[__name__], f"UC_ARM_REG_R{i}")) for i in range(4, 7)]
        return r0, regs

    cases = [
        (0, 5, 10),
        (4, 5, 10),
        (5, 5, 10),
        (14, 5, 10),
        (15, 5, 10),
        (20, 5, 10),
    ]

    for id_in, c1, c2 in cases:
        orig_r0, orig_regs = run_one(orig, id_in, c1, c2)
        comp_r0, comp_regs = run_one(staged, id_in, c1, c2)
        assert orig_r0 == comp_r0, f"Mismatch r0: orig={hex(orig_r0)}, comp={hex(comp_r0)}"
        assert orig_regs == comp_regs, f"Mismatch regs: orig={orig_regs}, comp={comp_regs}"

    print("camp_func_002483b8: PASS")


def test_0024a964():
    print("--- Testing engine_func_0024a964 ---")
    addr = 0x0024A964
    size = 112
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_0024a964", ROOT / "build")
    symbol_map = {"engine_func_002aa7f4": 0x002AA7F4}
    staged = stage_body(comp, relocs, addr, symbol_map)

    COUNT_ADDR = 0x00433278
    BASE_ADDR = 0x00478000
    TARGET_KEY = 0x20001000

    def run_one(c_bytes, max_count, match_index):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        uc.mem_write(COUNT_ADDR, struct.pack("<i", max_count))

        calls = []
        def on_aa7f4(uc, address, size, user_data):
            e1 = uc.reg_read(UC_ARM_REG_R0)
            key = uc.reg_read(UC_ARM_REG_R1)
            assert key == TARGET_KEY
            idx = (e1 - 1 - BASE_ADDR) // 328
            calls.append(idx)
            ret = 0 if idx == match_index else 1
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h_mock = uc.hook_add(UC_HOOK_CODE, on_aa7f4, None, 0x002AA7F4, 0x002AA7F4)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, TARGET_KEY)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h_mock)

        r0 = uc.reg_read(UC_ARM_REG_R0)
        regs = [uc.reg_read(getattr(sys.modules[__name__], f"UC_ARM_REG_R{i}")) for i in range(4, 9)]
        return r0, calls, regs

    cases = [
        (0, -1),   # max_count 0 -> 0xFF
        (-5, -1),  # max_count < 0 -> 0xFF
        (4, 0),    # match at index 0 -> 0
        (4, 2),    # match at index 2 -> 2
        (4, -1),   # no match -> 0xFF
    ]

    for mc, m_idx in cases:
        orig_r0, orig_calls, orig_regs = run_one(orig, mc, m_idx)
        comp_r0, comp_calls, comp_regs = run_one(staged, mc, m_idx)
        assert orig_r0 == comp_r0, f"Mismatch r0: orig={orig_r0}, comp={comp_r0}"
        assert orig_calls == comp_calls, f"Mismatch calls: orig={orig_calls}, comp={comp_calls}"
        assert orig_regs == comp_regs, f"Mismatch regs: orig={orig_regs}, comp={comp_regs}"

    print("engine_func_0024a964: PASS")


if __name__ == "__main__":
    test_00240e1c()
    test_0024807c()
    test_00248358()
    test_002483b8()
    test_0024a964()
    print("\nALL 5 FUNCTIONS PASSED 100% DIFFERENTIAL VERIFICATION!")
