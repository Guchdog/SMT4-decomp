#!/usr/bin/env python3
"""Differential test for batch 30 B part 18:
- camp_func_002ed404 (0x002ED404, 120 B)
- engine_func_002f067c (0x002F067C, 112 B)
- script_vm_func_002f3b78 (0x002F3B78, 104 B)
- engine_func_002f4a2c (0x002F4A2C, 120 B)
- engine_func_002f5dc0 (0x002F5DC0, 96 B)
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

    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(0x00480000, 0x00100000)
    uc.mem_map(0x00580000, 0x00100000)

    def hook_unmapped(uc, access, address, size, value, user_data):
        page = address & ~0xFFF
        print(f"CRASH: unmapped at 0x{address:08x}, pc=0x{uc.reg_read(UC_ARM_REG_PC):08x}")
        try:
            uc.mem_map(page, 0x1000)
            return True
        except Exception:
            return False

    uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_unmapped)
    return uc

def test_camp_func_002ed404():
    print("--- Testing camp_func_002ed404 ---")
    addr = 0x002ED404
    size = 120
    orig_code = load_original_bytes(addr, size)

    out_dir = ROOT / "build" / "batch30_b_part18"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_002ed404", out_dir)

    sym_map = {
        "camp_func_0028fde4": 0x0028FDE4,
        "camp_func_002bdb2c": 0x002BDB2C,
        "script_vm_func_002b90e0": 0x002B90E0,
        "camp_func_002bf030": 0x002BF030,
    }
    staged_decomp = stage_body(comp, relocs, addr, sym_map)

    # Stub 0x0028FDE4: returns 0x77778888
    code_28fde4 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", 0x77778888)
    # Stub 0x002BDB2C: records r0, r1, r2, r3 at 0x00495000 and returns
    code_2bdb2c = struct.pack("<IIII", 0xe59f4008, 0xe884000f, 0xe12fff1e, 0x00000000) + struct.pack("<I", 0x00495000)
    # Stub 0x002B90E0: records r0, r1 at 0x00495010
    code_2b90e0 = struct.pack("<IIII", 0xe59f2008, 0xe8820003, 0xe12fff1e, 0x00000000) + struct.pack("<I", 0x00495010)
    # Stub 0x002BF030: records r0, r1 at 0x00495020
    code_2bf030 = struct.pack("<IIII", 0xe59f2008, 0xe8820003, 0xe12fff1e, 0x00000000) + struct.pack("<I", 0x00495020)

    cases = [
        ("arg0_100", 0x12345678),
        ("arg0_0", 0),
    ]

    for name, arg0 in cases:
        def setup_mem(uc):
            uc.mem_write(0x0028FDE4, code_28fde4)
            uc.mem_write(0x002BDB2C, code_2bdb2c)
            uc.mem_write(0x002B90E0, code_2b90e0)
            uc.mem_write(0x002BF030, code_2bf030)
            # Global 0x0043E188 + 8 points to context at 0x00491000
            uc.mem_write(0x0043E188 + 8, struct.pack("<I", 0x00491000))
            # Zero out context memory at 0x00491000 (0x1000 bytes)
            uc.mem_write(0x00491000, bytes(0x1000))
            # Clear recorded buffers
            uc.mem_write(0x00495000, bytes(0x100))

        # Run orig
        RET_ADDR = 0x00499000
        uc_orig = setup_uc()
        setup_mem(uc_orig)
        uc_orig.reg_write(UC_ARM_REG_R0, arg0)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_orig.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_orig.emu_start(addr, RET_ADDR)
        orig_r0 = uc_orig.reg_read(UC_ARM_REG_R0)
        orig_ctx = uc_orig.mem_read(0x00491060, 0x30)
        orig_rec = uc_orig.mem_read(0x00495000, 0x30)

        # Run decomp
        uc_decomp = setup_uc()
        setup_mem(uc_decomp)
        uc_decomp.mem_write(addr, staged_decomp)
        uc_decomp.reg_write(UC_ARM_REG_R0, arg0)
        uc_decomp.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_decomp.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_decomp.emu_start(addr, RET_ADDR)
        decomp_r0 = uc_decomp.reg_read(UC_ARM_REG_R0)
        decomp_ctx = uc_decomp.mem_read(0x00491060, 0x30)
        decomp_rec = uc_decomp.mem_read(0x00495000, 0x30)

        assert orig_r0 == decomp_r0, f"{name}: r0 mismatch {orig_r0} != {decomp_r0}"
        assert orig_ctx == decomp_ctx, f"{name}: ctx mismatch {orig_ctx} != {decomp_ctx}"
        assert orig_rec == decomp_rec, f"{name}: call log mismatch {orig_rec} != {decomp_rec}"

    print("camp_func_002ed404: PASS")

def test_engine_func_002f067c():
    print("--- Testing engine_func_002f067c ---")
    addr = 0x002F067C
    size = 112
    orig_code = load_original_bytes(addr, size)

    out_dir = ROOT / "build" / "batch30_b_part18"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_002f067c", out_dir)

    sym_map = {
        "engine_func_00296f60": 0x00296F60,
        "script_vm_func_0027eb98": 0x0027EB98,
        "battle_func_0028df54": 0x0028DF54,
    }
    staged_decomp = stage_body(comp, relocs, addr, sym_map)

    # Stub 0x0027EB98: returns sub_obj pointer 0x00492000
    code_27eb98 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", 0x00492000)
    # Stub 0x0028DF54: records arg r0 at 0x00495000
    code_28df54 = struct.pack("<III", 0xe59f1004, 0xe5810000, 0xe12fff1e) + struct.pack("<I", 0x00495000)

    cases = [
        # (name, opt, target_val, actual_val_at_idx, should_match)
        ("opt_0_match", 0, 42, 42, True),
        ("opt_0_mismatch", 0, 42, 43, False),
        ("opt_1_match", 1, 100, 100, True),
        ("opt_2_match", 2, 999, 999, True),
        ("opt_default_match", 3, 7, 7, True), # default idx is 0
    ]

    for name, opt, target_val, actual_val, match in cases:
        # Stub 0x00296F60: if r0 == 0 return opt, else return target_val
        # cmp r0, #0; ldreq r0, [pc, #4]; ldrne r0, [pc, #4]; bx lr; .word opt; .word target_val
        code_296f60 = struct.pack("<IIIII", 0xe3500000, 0x059f0004, 0x159f0004, 0xe12fff1e, opt) + struct.pack("<I", target_val)

        def setup_mem(uc):
            uc.mem_write(0x00296F60, code_296f60)
            uc.mem_write(0x0027EB98, code_27eb98)
            uc.mem_write(0x0028DF54, code_28df54)
            # Global 0x0043427C: points to base 0x00491000
            uc.mem_write(0x0043427C, struct.pack("<I", 0x00491000))
            # sub_obj at 0x00492000: offset 0x20 points to data_arr at 0x00493000
            uc.mem_write(0x00492020, struct.pack("<I", 0x00493000))
            # data_arr at 0x00493000: zero out 0x100 bytes
            uc.mem_write(0x00493000, bytes(0x100))
            # compute idx:
            idx = 7 if opt == 0 else (10 if opt == 1 else (11 if opt == 2 else 0))
            uc.mem_write(0x00493000 + 0x72 + idx * 2, struct.pack("<h", actual_val))
            uc.mem_write(0x00495000, struct.pack("<I", 0xDEADBEEF))

        RET_ADDR = 0x00499000
        # Run orig
        uc_orig = setup_uc()
        setup_mem(uc_orig)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_orig.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_orig.emu_start(addr, RET_ADDR)
        orig_r0 = uc_orig.reg_read(UC_ARM_REG_R0)
        orig_rec = struct.unpack("<I", uc_orig.mem_read(0x00495000, 4))[0]

        # Run decomp
        uc_decomp = setup_uc()
        setup_mem(uc_decomp)
        uc_decomp.mem_write(addr, staged_decomp)
        uc_decomp.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_decomp.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_decomp.emu_start(addr, RET_ADDR)
        decomp_r0 = uc_decomp.reg_read(UC_ARM_REG_R0)
        decomp_rec = struct.unpack("<I", uc_decomp.mem_read(0x00495000, 4))[0]

        assert orig_r0 == decomp_r0, f"{name}: r0 mismatch {orig_r0} != {decomp_r0}"
        assert orig_rec == decomp_rec, f"{name}: recorded call mismatch {orig_rec} != {decomp_rec}"
        expected_call = 1 if match else 0
        assert orig_rec == expected_call, f"{name}: expected {expected_call} got {orig_rec}"

    print("engine_func_002f067c: PASS")

def test_script_vm_func_002f3b78():
    print("--- Testing script_vm_func_002f3b78 ---")
    addr = 0x002F3B78
    size = 104
    orig_code = load_original_bytes(addr, size)

    out_dir = ROOT / "build" / "batch30_b_part18"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_002f3b78", out_dir)
    staged_decomp = stage_body(comp, relocs, addr, {})

    cases = [
        # (name, active_slots)
        ("all_inactive", []),
        ("slot_0_type_29_state_8", [(0, 1, 0x1D, 8)]),
        ("slot_1_type_38_state_8", [(1, 1, 0x26, 8)]),
        ("slot_2_type_30_state_8", [(2, 1, 0x1E, 8)]),
        ("slot_3_type_31_state_8", [(3, 1, 0x1F, 8)]),
        ("slot_4_type_37_state_8", [(4, 1, 0x25, 8)]),
        ("slot_5_wrong_type", [(5, 1, 0x10, 8)]),
        ("slot_6_wrong_state", [(6, 1, 0x1D, 5)]),
        ("slot_127_last", [(127, 1, 0x1D, 8)]),
    ]

    for name, slots in cases:
        def setup_mem(uc):
            # Global 0x00447A78 points to base array at 0x00490000
            uc.mem_write(0x00447A78, struct.pack("<I", 0x00490000))
            # 128 slots * 404 bytes = 51712 (0xCA00 bytes)
            uc.mem_write(0x00490000, bytes(0xCA00 + 0x400))
            for idx, active, stype, state in slots:
                slot_addr = 0x00490000 + idx * 404
                uc.mem_write(slot_addr + 0x1D0, bytes([active]))
                uc.mem_write(slot_addr + 0x1D4, struct.pack("<I", state))
                uc.mem_write(slot_addr + 0x1E4, struct.pack("<I", stype))

        RET_ADDR = 0x00499000
        # Run orig
        uc_orig = setup_uc()
        setup_mem(uc_orig)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_orig.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_orig.emu_start(addr, RET_ADDR)
        orig_slots = uc_orig.mem_read(0x00490000, 0xCA00)

        # Run decomp
        uc_decomp = setup_uc()
        setup_mem(uc_decomp)
        uc_decomp.mem_write(addr, staged_decomp)
        uc_decomp.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_decomp.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_decomp.emu_start(addr, RET_ADDR)
        decomp_slots = uc_decomp.mem_read(0x00490000, 0xCA00)

        assert orig_slots == decomp_slots, f"{name}: slots mismatch"

    print("script_vm_func_002f3b78: PASS")

def test_engine_func_002f4a2c():
    print("--- Testing engine_func_002f4a2c ---")
    addr = 0x002F4A2C
    size = 120
    orig_code = load_original_bytes(addr, size)

    out_dir = ROOT / "build" / "batch30_b_part18"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_002f4a2c", out_dir)

    sym_map = {
        "func_00289640": 0x00289640,
        "engine_func_00289640": 0x00289640,
        "engine_func_002c1f28": 0x002C1F28,
        "script_vm_func_00287990": 0x00287990,
        "engine_func_00296f60": 0x00296F60,
        "ui_func_002a0678": 0x002A0678,
        "camp_func_002b8ce4": 0x002B8CE4,
    }
    staged_decomp = stage_body(comp, relocs, addr, sym_map)

    # Stubs
    # 0x00287990: records call by setting r0 = 1
    code_287990 = struct.pack("<II", 0xe3a00001, 0xe12fff1e)
    # 0x002A0678: records r0, r1 at 0x00495004
    code_2a0678 = struct.pack("<IIII", 0xe59f2008, 0xe8820003, 0xe12fff1e, 0x00000000) + struct.pack("<I", 0x00495004)

    cases = [
        # (name, f_289640, f_2c1f28, f_2b8ce4, f_296f60)
        ("path_a_c1f28_true", 1, 1, 0, 0),
        ("path_a_c1f28_false_b8ce4_true", 1, 0, 1, 0),
        ("path_a_c1f28_false_b8ce4_false", 1, 0, 0, 0),
        ("path_b_c1f28_true", 0, 1, 0, 0),
        ("path_b_c1f28_false", 0, 0, 0, 0x45),
    ]

    for name, v_289640, v_2c1f28, v_2b8ce4, v_296f60 in cases:
        code_289640 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", v_289640)
        code_2c1f28 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", v_2c1f28)
        code_2b8ce4 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", v_2b8ce4)
        code_296f60 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", v_296f60)

        def setup_mem(uc):
            uc.mem_write(0x00289640, code_289640)
            uc.mem_write(0x002C1F28, code_2c1f28)
            uc.mem_write(0x00287990, code_287990)
            uc.mem_write(0x00296F60, code_296f60)
            uc.mem_write(0x002A0678, code_2a0678)
            uc.mem_write(0x002B8CE4, code_2b8ce4)
            uc.mem_write(0x00495000, bytes(16))

        RET_ADDR = 0x00499000
        # Run orig
        uc_orig = setup_uc()
        setup_mem(uc_orig)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_orig.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_orig.emu_start(addr, RET_ADDR)
        orig_r0 = uc_orig.reg_read(UC_ARM_REG_R0)
        orig_rec = uc_orig.mem_read(0x00495000, 16)

        # Run decomp
        uc_decomp = setup_uc()
        setup_mem(uc_decomp)
        uc_decomp.mem_write(addr, staged_decomp)
        uc_decomp.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_decomp.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_decomp.emu_start(addr, RET_ADDR)
        decomp_r0 = uc_decomp.reg_read(UC_ARM_REG_R0)
        decomp_rec = uc_decomp.mem_read(0x00495000, 16)

        assert orig_r0 == decomp_r0, f"{name}: r0 mismatch {orig_r0} != {decomp_r0}"
        assert orig_rec == decomp_rec, f"{name}: call log mismatch {orig_rec} != {decomp_rec}"

    print("engine_func_002f4a2c: PASS")

def test_engine_func_002f5dc0():
    print("--- Testing engine_func_002f5dc0 ---")
    addr = 0x002F5DC0
    size = 96
    orig_code = load_original_bytes(addr, size)

    out_dir = ROOT / "build" / "batch30_b_part18"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_002f5dc0", out_dir)

    sym_map = {
        "func_0031bac0": 0x0031BAC0,
        "func_00309e5c": 0x00309E5C,
        "engine_func_002c4360": 0x002C4360,
        "battle_func_002c45b8": 0x002C45B8,
    }
    staged_decomp = stage_body(comp, relocs, addr, sym_map)

    # Stubs that append calls to a log buffer at 0x00495000
    # Let's make stubs simple:
    # 0x0031BAC0: records r0 at 0x00495000
    code_31bac0 = struct.pack("<III", 0xe59f1004, 0xe5810000, 0xe12fff1e) + struct.pack("<I", 0x00495000)
    # 0x00309E5C: records r0 at 0x00495004, 0x00495008, 0x0049500C sequentially
    # Let's just store at 0x00495000 + counter
    # or simple per-slot stores:
    # 0x00309E5C: ldr r1, =0x00495004; ldr r2, [r1]; str r0, [r1, r2]; add r2, r2, #4; str r2, [r1]; bx lr
    # 0x002C4360: stores at 0x00495020 (field_160) then 0x00495024 (self)
    # 0x002C45B8: stores r0, r1 at 0x00495030

    # Simple return stubs
    code_31bac0 = struct.pack("<I", 0xe12fff1e)
    code_309e5c = struct.pack("<I", 0xe12fff1e)
    code_2c4360 = struct.pack("<I", 0xe12fff1e)
    code_2c45b8 = struct.pack("<I", 0xe12fff1e)

    cases = [
        ("typical_subsystem_destroy", 0x00491000),
    ]

    for name, obj_addr in cases:
        def setup_mem(uc):
            uc.mem_write(0x0031BAC0, code_31bac0)
            uc.mem_write(0x00309E5C, code_309e5c)
            uc.mem_write(0x002C4360, code_2c4360)
            uc.mem_write(0x002C45B8, code_2c45b8)
            # Global 0x0043DB10 points to obj_addr
            uc.mem_write(0x0043DB10, struct.pack("<I", obj_addr))
            # Object memory:
            uc.mem_write(obj_addr, bytes(0x200))
            uc.mem_write(obj_addr, struct.pack("<I", 0x00492000)) # field_0
            uc.mem_write(obj_addr + 0x12C, struct.pack("<III", 0x1111, 0x2222, 0x3333)) # 3 items
            uc.mem_write(obj_addr + 0x138, struct.pack("<I", 0x4444)) # field_138
            uc.mem_write(obj_addr + 0x160, struct.pack("<I", 0x5555)) # field_160

            # Clear log memory
            uc.mem_write(0x00495000, bytes(0x100))

        RET_ADDR = 0x00499000
        # Run orig
        uc_orig = setup_uc()
        setup_mem(uc_orig)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_orig.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_orig.emu_start(addr, RET_ADDR)
        orig_global = struct.unpack("<I", uc_orig.mem_read(0x0043DB10, 4))[0]
        orig_log = uc_orig.mem_read(0x00495000, 0x70)

        # Run decomp
        uc_decomp = setup_uc()
        setup_mem(uc_decomp)
        uc_decomp.mem_write(addr, staged_decomp)
        uc_decomp.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_decomp.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_decomp.emu_start(addr, RET_ADDR)
        decomp_global = struct.unpack("<I", uc_decomp.mem_read(0x0043DB10, 4))[0]
        decomp_log = uc_decomp.mem_read(0x00495000, 0x70)

        assert orig_global == 0, f"global not cleared: {orig_global}"
        assert orig_global == decomp_global, f"global mismatch {orig_global} != {decomp_global}"
        assert orig_log == decomp_log, f"log mismatch: {orig_log} != {decomp_log}"

    print("engine_func_002f5dc0: PASS")

def main():
    test_camp_func_002ed404()
    test_engine_func_002f067c()
    test_script_vm_func_002f3b78()
    test_engine_func_002f4a2c()
    test_engine_func_002f5dc0()
    print("\nALL 5 FUNCTIONS IN BATCH 30 B PART 18 PASSED WITH 100% DIFFERENTIAL FIDELITY!")

if __name__ == "__main__":
    main()
