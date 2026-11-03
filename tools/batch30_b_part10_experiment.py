#!/usr/bin/env python3
"""Differential test for batch 30 B part 10:
- script_vm_func_00287ce0 (0x00287CE0, 116 B)
- ui_func_00288990 (0x00288990, 104 B)
- script_vm_func_00289fdc (0x00289FDC, 112 B)
- script_vm_func_0028a04c (0x0028A04C, 112 B)
- script_vm_func_0028c194 (0x0028C194, 112 B)
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


def test_00287ce0():
    print("--- Testing script_vm_func_00287ce0 ---")
    addr = 0x00287CE0
    size = 116
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_00287ce0", ROOT / "build")

    STUB_ATAN = 0x002820A4
    STUB_DELTA = 0x00287D74
    staged = stage_body(comp, relocs, addr, {
        "ui_func_002820a4": STUB_ATAN,
        "script_vm_func_00287d74": STUB_DELTA,
    })

    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, x1, y1, z1, heading, x2, y2, z2, atan_ret, delta_ret):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_ATAN, stub_code)
        uc.mem_write(STUB_DELTA, stub_code)

        calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_ATAN:
                # reads s0, s1
                s0_raw = uc.reg_read(UC_ARM_REG_S0)
                s1_raw = uc.reg_read(UC_ARM_REG_S1)
                s0_f = struct.unpack("<f", struct.pack("<I", s0_raw))[0]
                s1_f = struct.unpack("<f", struct.pack("<I", s1_raw))[0]
                calls.append(("ATAN", round(s0_f, 4), round(s1_f, 4)))
                uc.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", atan_ret))[0])
            elif address == STUB_DELTA:
                # reads s0, s1
                s0_raw = uc.reg_read(UC_ARM_REG_S0)
                s1_raw = uc.reg_read(UC_ARM_REG_S1)
                s0_f = struct.unpack("<f", struct.pack("<I", s0_raw))[0]
                s1_f = struct.unpack("<f", struct.pack("<I", s1_raw))[0]
                calls.append(("DELTA", round(s0_f, 4), round(s1_f, 4)))
                uc.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", delta_ret))[0])

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        # s0..s6
        uc.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", x1))[0])
        uc.reg_write(UC_ARM_REG_S1, struct.unpack("<I", struct.pack("<f", y1))[0])
        uc.reg_write(UC_ARM_REG_S2, struct.unpack("<I", struct.pack("<f", z1))[0])
        uc.reg_write(UC_ARM_REG_S3, struct.unpack("<I", struct.pack("<f", heading))[0])
        uc.reg_write(UC_ARM_REG_S4, struct.unpack("<I", struct.pack("<f", x2))[0])
        uc.reg_write(UC_ARM_REG_S5, struct.unpack("<I", struct.pack("<f", y2))[0])
        uc.reg_write(UC_ARM_REG_S6, struct.unpack("<I", struct.pack("<f", z2))[0])

        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        ret_raw = uc.reg_read(UC_ARM_REG_S0)
        ret_f = struct.unpack("<f", struct.pack("<I", ret_raw))[0]
        return ret_f, calls

    test_cases = [
        # (x1, y1, z1, heading, x2, y2, z2, atan_ret, delta_ret)
        (0.0, 0.0, 0.0, 90.0, 10.0, 0.0, 10.0, 1.0, 45.0),
        (0.0, 0.0, 0.0, 90.0, 10.0, 0.0, 10.0, -1.0, -30.0),    # negative deg -> +360, negative delta -> fabsf
        (5.0, 0.0, 5.0, 180.0, 10.0, 0.0, 10.0, 10.0, 120.0),   # deg > 360 -> -360
    ]

    for tc in test_cases:
        r1, c1 = run_one(orig, *tc)
        r2, c2 = run_one(staged, *tc)
        assert abs(r1 - r2) < 1e-4, f"Ret mismatch: orig={r1}, comp={r2}"
        assert c1 == c2, f"Calls mismatch: orig={c1}, comp={c2}"
    print("script_vm_func_00287ce0: PASS")


def test_00288990():
    print("--- Testing ui_func_00288990 ---")
    addr = 0x00288990
    size = 104
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_00288990", ROOT / "build")

    STUB_SUB = 0x002A7AA0
    STUB_FREE = 0x002C4360
    staged = stage_body(comp, relocs, addr, {
        "script_vm_func_002a7aa0": STUB_SUB,
        "engine_func_002c4360": STUB_FREE,
    })

    OBJ = 0x20001000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, p8, slot_ptrs):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_SUB, stub_code)
        uc.mem_write(STUB_FREE, stub_code)

        uc.mem_write(OBJ, b"\x00" * 0x200)
        uc.mem_write(OBJ + 8, struct.pack("<I", p8))
        for i, (p18, p1c) in enumerate(slot_ptrs):
            uc.mem_write(OBJ + i * 80 + 0x18, struct.pack("<I", p18))
            uc.mem_write(OBJ + i * 80 + 0x1C, struct.pack("<I", p1c))

        sub_calls = []
        free_calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_SUB:
                sub_calls.append(uc.reg_read(UC_ARM_REG_R0))
            elif address == STUB_FREE:
                free_calls.append(uc.reg_read(UC_ARM_REG_R0))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, OBJ)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=2000)

        # Read back pointers
        p8_after = struct.unpack_from("<I", uc.mem_read(OBJ + 8, 4))[0]
        slots_after = []
        for i in range(3):
            p18_a = struct.unpack_from("<I", uc.mem_read(OBJ + i * 80 + 0x18, 4))[0]
            p1c_a = struct.unpack_from("<I", uc.mem_read(OBJ + i * 80 + 0x1C, 4))[0]
            slots_after.append((p18_a, p1c_a))

        return sub_calls, free_calls, p8_after, slots_after

    test_cases = [
        (0x20002000, [(0x11, 0x12), (0x21, 0x22), (0x31, 0x32)]),
        (0, [(0, 0), (0, 0), (0, 0)]),
        (0x20003000, [(0x11, 0), (0, 0x22), (0x31, 0)]),
    ]

    for p8, s_ptrs in test_cases:
        sub1, fr1, p8_1, s1 = run_one(orig, p8, s_ptrs)
        sub2, fr2, p8_2, s2 = run_one(staged, p8, s_ptrs)
        assert sub1 == sub2, f"Sub mismatch: orig={sub1}, comp={sub2}"
        assert fr1 == fr2, f"Free mismatch: orig={fr1}, comp={fr2}"
        assert p8_1 == p8_2, f"p8 mismatch: orig={p8_1}, comp={p8_2}"
        assert s1 == s2, f"Slots mismatch: orig={s1}, comp={s2}"
    print("ui_func_00288990: PASS")


def test_00289fdc():
    print("--- Testing script_vm_func_00289fdc ---")
    addr = 0x00289FDC
    size = 112
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_00289fdc", ROOT / "build")

    STUB_CHECK = 0x002A71C0
    STUB_DISP = 0x002A4828
    staged = stage_body(comp, relocs, addr, {
        "engine_func_002a71c0": STUB_CHECK,
        "engine_func_002a4828": STUB_DISP,
    })

    PTR_MGR = 0x00433130
    MGR = 0x20001000
    RES_NODE = 0x20002000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, arg0, arg1, arg2, check_ret):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_CHECK, stub_code)
        uc.mem_write(STUB_DISP, stub_code)

        uc.mem_write(PTR_MGR, struct.pack("<I", MGR))

        check_args = []
        disp_args = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_CHECK:
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                check_args.append((r0, r1, r2))
                uc.reg_write(UC_ARM_REG_R0, check_ret)
            elif address == STUB_DISP:
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                sp = uc.reg_read(UC_ARM_REG_SP)
                p5, p6, p7 = struct.unpack_from("<III", uc.mem_read(sp, 12))
                disp_args.append((r0, r2, r3, p5, p6, p7))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_R2, arg2)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=2000)

        return check_args, disp_args

    test_cases = [
        (0x10, 0x20, 0x30, 0),         # check returns 0 -> no disp
        (0x10, 0x20, 0x30, RES_NODE),  # check returns RES_NODE -> disp called
    ]

    for a0, a1, a2, chk in test_cases:
        c1, d1 = run_one(orig, a0, a1, a2, chk)
        c2, d2 = run_one(staged, a0, a1, a2, chk)
        assert c1 == c2, f"Check args mismatch: orig={c1}, comp={c2}"
        assert d1 == d2, f"Disp args mismatch: orig={d1}, comp={d2}"
    print("script_vm_func_00289fdc: PASS")


def test_0028a04c():
    print("--- Testing script_vm_func_0028a04c ---")
    addr = 0x0028A04C
    size = 112
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_0028a04c", ROOT / "build")

    STUB_CHECK = 0x002A71C0
    STUB_DISP = 0x002A4828
    staged = stage_body(comp, relocs, addr, {
        "engine_func_002a71c0": STUB_CHECK,
        "engine_func_002a4828": STUB_DISP,
    })

    PTR_MGR = 0x00433130
    MGR = 0x20001000
    RES_NODE = 0x20002000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, arg0, arg1, arg2, check_ret):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_CHECK, stub_code)
        uc.mem_write(STUB_DISP, stub_code)

        uc.mem_write(PTR_MGR, struct.pack("<I", MGR))

        check_args = []
        disp_args = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_CHECK:
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                check_args.append((r0, r1, r2))
                uc.reg_write(UC_ARM_REG_R0, check_ret)
            elif address == STUB_DISP:
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                sp = uc.reg_read(UC_ARM_REG_SP)
                p5, p6, p7 = struct.unpack_from("<III", uc.mem_read(sp, 12))
                disp_args.append((r0, r2, r3, p5, p6, p7))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_R2, arg2)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=2000)

        return check_args, disp_args

    test_cases = [
        (0x10, 0x20, 0x30, 0),         # check returns 0 -> no disp
        (0x10, 0x20, 0x30, RES_NODE),  # check returns RES_NODE -> disp called
    ]

    for a0, a1, a2, chk in test_cases:
        c1, d1 = run_one(orig, a0, a1, a2, chk)
        c2, d2 = run_one(staged, a0, a1, a2, chk)
        assert c1 == c2, f"Check args mismatch: orig={c1}, comp={c2}"
        assert d1 == d2, f"Disp args mismatch: orig={d1}, comp={d2}"
    print("script_vm_func_0028a04c: PASS")


def test_0028c194():
    print("--- Testing script_vm_func_0028c194 ---")
    addr = 0x0028C194
    size = 112
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_0028c194", ROOT / "build")

    STUB_SUB = 0x002AEB2C
    STUB_DISP = 0x002A6410
    staged = stage_body(comp, relocs, addr, {
        "script_vm_func_002aeb2c": STUB_SUB,
        "engine_func_002a6410": STUB_DISP,
    })

    PTR_MGR1 = 0x00434210
    PTR_MGR2 = 0x00433158
    MGR1 = 0x20001000
    MGR2 = 0x20005000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, mgr1_ptr, init_id, init_f2f4):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_SUB, stub_code)
        uc.mem_write(STUB_DISP, stub_code)

        uc.mem_write(PTR_MGR1, struct.pack("<I", mgr1_ptr))
        uc.mem_write(PTR_MGR2, struct.pack("<I", MGR2))

        if mgr1_ptr != 0:
            uc.mem_write(MGR1, b"\x00" * 0x400)
            uc.mem_write(MGR1 + 0x2F8, struct.pack("<i", init_id))
            uc.mem_write(MGR1 + 0x2F4, struct.pack("<B", init_f2f4))

        sub_calls = []
        disp_calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_SUB:
                sub_calls.append(uc.reg_read(UC_ARM_REG_R0))
            elif address == STUB_DISP:
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                disp_calls.append((r0, r1, r2))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=2000)

        if mgr1_ptr != 0:
            out_id = struct.unpack_from("<i", uc.mem_read(MGR1 + 0x2F8, 4))[0]
            out_f2f4 = uc.mem_read(MGR1 + 0x2F4, 1)[0]
            out_f2e8 = struct.unpack_from("<ii", uc.mem_read(MGR1 + 0x2E8, 8))
        else:
            out_id, out_f2f4, out_f2e8 = None, None, None

        return sub_calls, disp_calls, out_id, out_f2f4, out_f2e8

    test_cases = [
        (0, 0, 0),
        (MGR1, -1, 1),
        (MGR1, 42, 1),
        (MGR1, 0, 1),
    ]

    for m1, id_init, f2f4 in test_cases:
        s1, d1, o_id1, o_f1, o_e1 = run_one(orig, m1, id_init, f2f4)
        s2, d2, o_id2, o_f2, o_e2 = run_one(staged, m1, id_init, f2f4)
        assert s1 == s2, f"Sub mismatch: orig={s1}, comp={s2}"
        assert d1 == d2, f"Disp mismatch: orig={d1}, comp={d2}"
        assert (o_id1, o_f1, o_e1) == (o_id2, o_f2, o_e2), "State mismatch"
    print("script_vm_func_0028c194: PASS")


def main():
    test_00287ce0()
    test_00288990()
    test_00289fdc()
    test_0028a04c()
    test_0028c194()
    print("\nALL 5 FUNCTIONS IN BATCH 30 B PART 10 PASSED WITH 100% DIFFERENTIAL FIDELITY!")

if __name__ == "__main__":
    main()
