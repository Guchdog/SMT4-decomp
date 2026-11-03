#!/usr/bin/env python3
"""Differential test for batch 31 C part 18:
- camp_func_002d65fc (0x002D65FC, 160 B)
- effGeometry_func_002de208 (0x002DE208, 156 B)
- ui_func_002df484 (0x002DF484, 160 B)
- script_vm_func_002dfcf4 (0x002DFCF4, 160 B)
- ui_func_002e2750 (0x002E2750, 184 B)
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
COMPILED_ST_VALUES = {}
RODATA_ADDR = 0x10050000
RODATA_BYTES = b""
SOURCE = ROOT / "src/engine/leaf_batch31_c.cpp"

with open(ORIG_BIN, "rb") as f:
    ORIG_DATA = f.read()

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS, COMPILED_ST_VALUES, RODATA_BYTES
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch31_c.o"
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
    if RODATA_BYTES:
        uc.mem_write(RODATA_ADDR, RODATA_BYTES)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, unmapped_hook)

    val = uc.reg_read(UC_ARM_REG_C1_C0_2)
    val |= (0xF << 20)
    uc.reg_write(UC_ARM_REG_C1_C0_2, val)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return uc

# -----------------------------------------------------------------------------
# Function 1: camp_func_002d65fc (0x002D65FC, 160 B)
# -----------------------------------------------------------------------------
def test_camp_func_002d65fc():
    addr = 0x002D65FC
    size = 160
    print(f"--- Testing camp_func_002d65fc ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part18"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_002d65fc", tmp)

    STUB_00296154 = 0x00296154
    sym_map = {
        "script_vm_func_00296154": STUB_00296154,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "camp_func_002d65fc")

    OBJ_GLOBAL = 0x0043DA28
    OBJ_BASE = 0x10020000

    def run_one(code, flag):
        uc = create_emulator()

        # Write stub at STUB_00296154: bx lr
        uc.mem_write(STUB_00296154, b"\x1e\xff\x2f\xe1")

        # Set up object memory: size at least 0x500
        mem = bytearray(0x500)
        # Pre-fill with distinct bytes
        for i in range(len(mem)):
            mem[i] = (i * 7 + 3) & 0xFF
        uc.mem_write(OBJ_BASE, bytes(mem))
        uc.mem_write(OBJ_GLOBAL + 4, struct.pack("<I", OBJ_BASE))

        target = addr
        uc.mem_write(target, code)
        ret_addr = 0x00100004
        uc.mem_write(ret_addr, b"\x00\x00\x00\x00")

        uc.reg_write(UC_ARM_REG_R0, flag)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, ret_addr)
        uc.reg_write(UC_ARM_REG_PC, target)

        uc.emu_start(target, ret_addr, timeout=2000000)
        return bytes(uc.mem_read(OBJ_BASE, 0x500))

    for flag in [0, 1, 2, 0xFF]:
        r_orig = run_one(orig_code, flag)
        r_decomp = run_one(decomp_code, flag)
        assert r_orig == r_decomp, f"Mismatch for flag={flag}"
        assert r_decomp[0x4C8] == (flag & 0xFF)
        if flag != 0:
            assert r_decomp[0x3B8] == 0
            assert r_decomp[0x3B8 + 140] == 0
        else:
            assert struct.unpack("<H", r_decomp[0x3B6:0x3B8])[0] == 2
            assert r_decomp[0x3B8] == 1
            assert struct.unpack("<III", r_decomp[0x388:0x394]) == (0, 0, 0)
            assert struct.unpack("<H", r_decomp[0x3B6 + 140 : 0x3B8 + 140])[0] == 2
            assert r_decomp[0x3B8 + 140] == 1
            assert struct.unpack("<III", r_decomp[0x388 + 140 : 0x394 + 140]) == (0, 0, 0)

    print("camp_func_002d65fc: PASS")

# -----------------------------------------------------------------------------
# Function 2: effGeometry_func_002de208 (0x002DE208, 156 B)
# -----------------------------------------------------------------------------
def test_effGeometry_func_002de208():
    addr = 0x002DE208
    size = 156
    print(f"--- Testing effGeometry_func_002de208 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part18"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("effGeometry_func_002de208", tmp)

    STUB_002C34A4 = 0x002C34A4
    STUB_001F68B0 = 0x001F68B0

    sym_map = {
        "func_002c34a4": STUB_002C34A4,
        "effGeomEngine_func_001f68b0": STUB_001F68B0,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "effGeometry_func_002de208")

    NODE_ADDR = 0x10020000
    GEOM_ADDR = 0x10030000
    MATRIX_DATA = bytes([0x11, 0x22, 0x33, 0x44] * 4)

    def run_one(code, arg0, arg1):
        uc = create_emulator()

        # Stub 002C34A4: ldr r0, =NODE_ADDR; bx lr
        stub_node = bytearray()
        stub_node += struct.pack("<I", 0xe59f0000)
        stub_node += struct.pack("<I", 0xe12fff1e)
        stub_node += struct.pack("<I", NODE_ADDR)
        uc.mem_write(STUB_002C34A4, bytes(stub_node))

        # Stub 001F68B0: ldr r0, =GEOM_ADDR; bx lr
        stub_geom = bytearray()
        stub_geom += struct.pack("<I", 0xe59f0000)
        stub_geom += struct.pack("<I", 0xe12fff1e)
        stub_geom += struct.pack("<I", GEOM_ADDR)
        uc.mem_write(STUB_001F68B0, bytes(stub_geom))

        # Write matrix data at 0x00473808
        uc.mem_write(0x00473808, MATRIX_DATA)

        # Clear node and geom memory
        uc.mem_write(NODE_ADDR, b"\x00" * 0x80)
        uc.mem_write(GEOM_ADDR, b"\x00" * 0x80)

        target = addr
        uc.mem_write(target, code)
        ret_addr = 0x00100004
        uc.mem_write(ret_addr, b"\x00\x00\x00\x00")

        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, ret_addr)
        uc.reg_write(UC_ARM_REG_PC, target)

        uc.emu_start(target, ret_addr, timeout=2000000)
        ret_val = uc.reg_read(UC_ARM_REG_R0)
        node_mem = uc.mem_read(NODE_ADDR, 0x20)
        geom_mem = uc.mem_read(GEOM_ADDR, 0x80)
        return ret_val, bytes(node_mem), bytes(geom_mem)

    cases = [
        (0x1000, 0),
        (0x1000, 0x80000),
        (0x2000, 0x80005),
        (0x3000, 0x7FFFF),
    ]

    for a0, a1 in cases:
        r_orig, n_orig, g_orig = run_one(orig_code, a0, a1)
        r_decomp, n_decomp, g_decomp = run_one(decomp_code, a0, a1)
        assert r_orig == r_decomp == NODE_ADDR
        assert n_orig == n_decomp, f"Node mem mismatch for ({a0}, {a1})"
        assert g_orig == g_decomp, f"Geom mem mismatch for ({a0}, {a1})"
        assert struct.unpack("<H", n_decomp[0:2])[0] == 0x300
        assert struct.unpack("<H", n_decomp[2:4])[0] == 0
        assert struct.unpack("<I", n_decomp[0xC:0x10])[0] == GEOM_ADDR
        assert struct.unpack("<I", g_decomp[0x60:0x64])[0] == 0
        if a1 & 0x80000:
            assert g_decomp[0x40:0x50] == MATRIX_DATA

    print("effGeometry_func_002de208: PASS")

# -----------------------------------------------------------------------------
# Function 3: ui_func_002df484 (0x002DF484, 160 B)
# -----------------------------------------------------------------------------
def test_ui_func_002df484():
    addr = 0x002DF484
    size = 160
    print(f"--- Testing ui_func_002df484 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part18"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_002df484", tmp)

    STUB_2AE18C = 0x002AE18C
    STUB_29C56C = 0x0029C56C
    STUB_2637B4 = 0x002637B4
    STUB_276CAC = 0x00276CAC

    sym_map = {
        "func_002ae18c": STUB_2AE18C,
        "func_0029c56c": STUB_29C56C,
        "func_002637b4": STUB_2637B4,
        "func_00276cac": STUB_276CAC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "ui_func_002df484")

    VIEW_GLOBAL = 0x004474F0
    VIEW_ADDR = 0x10020000
    SUB_OBJ_ADDR = 0x10030000
    TEST_FLOATS = [1.5, 2.5, -3.5, 4.5, -5.5, 6.5]

    def run_one(code):
        uc = create_emulator()

        # Stub 002AE18C: writes 6 floats to [r0] (sp), then bx lr
        stub_data = bytearray()
        # We can write floats into a literal pool and ldmia into r0
        stub_floats = struct.pack("<ffffff", *TEST_FLOATS)
        # ldr r1, [pc, #8]; ldmia r1, {r1, r2, r3, ip}; stmia r0!, {r1, r2, r3, ip};
        # ldr r1, [pc, #4]; ldmia r1, {r1, r2}; stmia r0, {r1, r2}; bx lr
        # Or simpler: Unicorn mem_write directly hook or custom code:
        # ldr r1, =FLOAT_DATA; mov r2, #24; memcpy(r0, r1, 24); bx lr
        FLOAT_DATA_ADDR = 0x10040000
        uc.mem_write(FLOAT_DATA_ADDR, stub_floats)
        # ARM assembly for stub 002AE18C:
        # ldr r1, =FLOAT_DATA_ADDR
        # ldmia r1!, {r2, r3, ip, lr}
        # stmia r0!, {r2, r3, ip, lr}
        # ldmia r1, {r2, r3}
        # stmia r0, {r2, r3}
        # bx r14 (wait, we clobbered lr, so save or use other regs)
        # Instead of clobbering lr, just use r1, r2, r3:
        stub_asm = (
            b"\x0c\x10\x9f\xe5"  # ldr r1, [pc, #12]
            b"\x0f\x00\x91\xe8"  # ldm r1, {r0-r3} (wait, r0 is dest)
        )
        # Simplest: write a 16-byte copy using push/pop:
        # push {r4, lr}; ldr r1, [pc, #16]; ldm r1, {r2, r3, r4, ip}; stm r0, {r2, r3, r4, ip};
        # add r0, r0, #16; ldr r1, [pc, #8]; ldm r1, {r2, r3}; stm r0, {r2, r3}; pop {r4, pc}
        # Actually, let's assemble cleanly in python:
        stub_bytes = bytearray()
        stub_bytes += struct.pack("<I", 0xe92d4010) # push {r4, lr}
        stub_bytes += struct.pack("<I", 0xe59f1018) # ldr r1, [pc, #24]
        stub_bytes += struct.pack("<I", 0xe891101c) # ldm r1, {r2, r3, r4, ip}
        stub_bytes += struct.pack("<I", 0xe880101c) # stm r0, {r2, r3, r4, ip}
        stub_bytes += struct.pack("<I", 0xe2800010) # add r0, r0, #16
        stub_bytes += struct.pack("<I", 0xe59f100c) # ldr r1, [pc, #12]
        stub_bytes += struct.pack("<I", 0xe891000c) # ldm r1, {r2, r3}
        stub_bytes += struct.pack("<I", 0xe880000c) # stm r0, {r2, r3}
        stub_bytes += struct.pack("<I", 0xe8bd8010) # pop {r4, pc}
        stub_bytes += struct.pack("<I", FLOAT_DATA_ADDR)
        stub_bytes += struct.pack("<I", FLOAT_DATA_ADDR + 16)
        uc.mem_write(STUB_2AE18C, bytes(stub_bytes))

        # Other stubs: bx lr
        uc.mem_write(STUB_29C56C, b"\x1e\xff\x2f\xe1")
        uc.mem_write(STUB_2637B4, b"\x1e\xff\x2f\xe1")
        uc.mem_write(STUB_276CAC, b"\x1e\xff\x2f\xe1")

        # Set up view memory: 0x300 bytes
        view_mem = bytearray(0x300)
        struct.pack_into("<I", view_mem, 0x2B4, SUB_OBJ_ADDR)
        view_mem[0x2B0] = 5
        uc.mem_write(VIEW_ADDR, bytes(view_mem))
        uc.mem_write(VIEW_GLOBAL + 4, struct.pack("<I", VIEW_ADDR))

        target = addr
        uc.mem_write(target, code)
        ret_addr = 0x00100004
        uc.mem_write(ret_addr, b"\x00\x00\x00\x00")

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, ret_addr)
        uc.reg_write(UC_ARM_REG_PC, target)

        uc.emu_start(target, ret_addr, timeout=2000000)
        return bytes(uc.mem_read(VIEW_ADDR, 0x300))

    r_orig = run_one(orig_code)
    r_decomp = run_one(decomp_code)
    assert r_orig == r_decomp, "View object memory mismatch"

    # Check floats
    expected_floats = tuple(TEST_FLOATS)
    assert struct.unpack_from("<ffffff", r_decomp, 0x34) == expected_floats
    assert struct.unpack_from("<ffffff", r_decomp, 0x4C) == expected_floats
    assert struct.unpack_from("<I", r_decomp, 0x2B4)[0] == 0
    assert r_decomp[0x2B0] == 0

    print("ui_func_002df484: PASS")

# -----------------------------------------------------------------------------
# Function 4: script_vm_func_002dfcf4 (0x002DFCF4, 160 B)
# -----------------------------------------------------------------------------
def test_script_vm_func_002dfcf4():
    addr = 0x002DFCF4
    size = 160
    print(f"--- Testing script_vm_func_002dfcf4 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part18"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_002dfcf4", tmp)

    STUB_2C0BA8 = 0x002C0BA8
    STUB_287B64 = 0x00287B64

    sym_map = {
        "func_002c0ba8": STUB_2C0BA8,
        "func_00287b64": STUB_287B64,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "script_vm_func_002dfcf4")

    MGR_GLOBAL = 0x00447A48
    MGR_ADDR = 0x10020000
    LOG_ADDR = 0x10030000

    def run_one(code, slots_setup):
        uc = create_emulator()

        # Stub 2C0BA8: return 0 if r0 == 100, else return 1
        # cmp r0, #100; moveq r0, #0; movne r0, #1; bx lr
        stub_c0ba8 = (
            b"\x64\x00\x50\xe3"  # cmp r0, #100
            b"\x00\x00\xa0\x03"  # moveq r0, #0
            b"\x01\x00\xa0\x13"  # movne r0, #1
            b"\x1e\xff\x2f\xe1"  # bx lr
        )
        uc.mem_write(STUB_2C0BA8, stub_c0ba8)

        # Stub 287B64: logs r0 to LOG_ADDR table
        # ldr r1, =LOG_ADDR; ldr r2, [r1]; str r0, [r1, r2, lsl #2]; add r2, r2, #1; str r2, [r1]; bx lr
        # LOG_ADDR layout: [0]: count, [4..]: values
        stub_87b64 = bytearray()
        stub_87b64 += struct.pack("<I", 0xe59f1010) # ldr r1, [pc, #16]
        stub_87b64 += struct.pack("<I", 0xe5912000) # ldr r2, [r1]
        stub_87b64 += struct.pack("<I", 0xe2823001) # add r3, r2, #1
        stub_87b64 += struct.pack("<I", 0xe7810103) # str r0, [r1, r3, lsl #2]
        stub_87b64 += struct.pack("<I", 0xe5813000) # str r3, [r1]
        stub_87b64 += struct.pack("<I", 0xe12fff1e) # bx lr
        stub_87b64 += struct.pack("<I", LOG_ADDR)
        uc.mem_write(STUB_287B64, bytes(stub_87b64))
        uc.mem_write(LOG_ADDR, struct.pack("<I", 0))

        # Set up mgr memory: 24 * 40 + 0x100 = 0x500 bytes
        mgr_mem = bytearray(0x500)
        # Pre-populate slots_setup: list of (slot_idx, active, id0, id1, val_s16)
        for s_idx, act, id0, id1, val in slots_setup:
            p = s_idx * 40 + 0x1C
            mgr_mem[p] = act
            struct.pack_into("<h", mgr_mem, p + 0x20, id0)
            struct.pack_into("<h", mgr_mem, p + 0x22, id1)
            struct.pack_into("<i", mgr_mem, p + 0x1C, val)

        uc.mem_write(MGR_ADDR, bytes(mgr_mem))
        uc.mem_write(MGR_GLOBAL, struct.pack("<I", MGR_ADDR))

        target = addr
        uc.mem_write(target, code)
        ret_addr = 0x00100004
        uc.mem_write(ret_addr, b"\x00\x00\x00\x00")

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, ret_addr)
        uc.reg_write(UC_ARM_REG_PC, target)

        uc.emu_start(target, ret_addr, timeout=2000000)

        # Read back log
        count = struct.unpack("<I", uc.mem_read(LOG_ADDR, 4))[0]
        logged_vals = []
        if count > 0:
            logged_vals = list(struct.unpack(f"<{count}i", uc.mem_read(LOG_ADDR + 4, count * 4)))
        return bytes(uc.mem_read(MGR_ADDR, 0x500)), logged_vals

    slots = [
        # (slot_idx, active, id0, id1, val)
        (0, 1, 100, 0, 0x1111),    # id0=100 (returns 0) -> fires!
        (1, 1, 200, 0, 0x2222),    # id0=200 (returns 1), id1=0 -> skips!
        (2, 1, 200, 300, 0x3333),  # id0=200, id1=300 (returns 1) -> fires!
        (3, 1, 200, 100, 0x4444),  # id0=200, id1=100 (returns 0) -> skips!
        (4, 0, 100, 300, 0x5555),  # inactive -> skips!
        (23, 1, 0, 50, 0x7777),    # id0=0, id1=50 (returns 1) -> fires!
    ]

    r_orig, log_orig = run_one(orig_code, slots)
    r_decomp, log_decomp = run_one(decomp_code, slots)
    assert r_orig == r_decomp, "Mgr memory mismatch"
    assert log_orig == log_decomp, f"Log mismatch: {log_orig} != {log_decomp}"
    assert log_decomp == [0x1111, 0x3333, 0x7777]

    print("script_vm_func_002dfcf4: PASS")

# -----------------------------------------------------------------------------
# Function 5: ui_func_002e2750 (0x002E2750, 184 B)
# -----------------------------------------------------------------------------
def test_ui_func_002e2750():
    addr = 0x002E2750
    size = 184
    print(f"--- Testing ui_func_002e2750 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part18"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_002e2750", tmp)

    STUB_293CA8 = 0x00293CA8
    STUB_297004 = 0x00297004
    STUB_2C615C = 0x002C615C

    sym_map = {
        "ui_func_00293ca8": STUB_293CA8,
        "ui_func_00297004": STUB_297004,
        "ui_func_002c615c": STUB_2C615C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "ui_func_002e2750")

    TABLE_BASE = 0x10020000
    DATA_BASE = 0x10030000

    def run_one(code, count, mode, slot_initial):
        uc = create_emulator()

        # Stub 293CA8: returns float 50.0 in s0
        # vldr s0, [pc, #4]; bx lr; .float 50.0
        stub_3ca8 = (
            b"\x01\x0a\x9f\xed"  # vldr s0, [pc, #4]
            b"\x1e\xff\x2f\xe1"  # bx lr
            + struct.pack("<f", 50.0)
        )
        uc.mem_write(STUB_293CA8, stub_3ca8)

        # Stub 297004: returns pseudo-random int, say (arg1 * 3 + 7) & 0x7F
        # add r0, r1, r1, lsl #1; add r0, r0, #7; and r0, r0, #0x7F; bx lr
        stub_7004 = (
            b"\x01\x00\x81\xe0"  # add r0, r1, r1, lsl #1 (3 * r1)
            b"\x07\x00\x80\xe2"  # add r0, r0, #7
            b"\x7f\x00\x00\xe2"  # and r0, r0, #0x7F
            b"\x1e\xff\x2f\xe1"  # bx lr
        )
        uc.mem_write(STUB_297004, stub_7004)

        # Stub 2C615C: bx lr
        uc.mem_write(STUB_2C615C, b"\x1e\xff\x2f\xe1")

        # Set up table memory
        table_mem = bytearray(0x400)
        for s_idx, (idx_byte, val_u16) in enumerate(slot_initial):
            p = s_idx * 32
            table_mem[p + 6] = idx_byte & 0xFF
            struct.pack_into("<H", table_mem, p + 4, val_u16)
        uc.mem_write(TABLE_BASE, bytes(table_mem))

        target = addr
        uc.mem_write(target, code)
        ret_addr = 0x00100004
        uc.mem_write(ret_addr, b"\x00\x00\x00\x00")

        uc.reg_write(UC_ARM_REG_R0, TABLE_BASE)
        uc.reg_write(UC_ARM_REG_R1, count)
        uc.reg_write(UC_ARM_REG_R2, mode)
        uc.reg_write(UC_ARM_REG_R3, DATA_BASE)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, ret_addr)
        uc.reg_write(UC_ARM_REG_PC, target)

        uc.emu_start(target, ret_addr, timeout=2000000)
        return bytes(uc.mem_read(TABLE_BASE, 0x400))

    initial_slots = [
        (0, 10),    # idx=0, val=10
        (1, 60),    # idx=1, val=60 (already > max_val 50)
        (-1, 20),   # idx=-1 (skipped)
        (2, 50),    # idx=2, val=50 (equal max_val 50 -> clamped to 50)
    ]

    for mode in [0, 1, 2, 3]:
        r_orig = run_one(orig_code, 4, mode, initial_slots)
        r_decomp = run_one(decomp_code, 4, mode, initial_slots)
        assert r_orig == r_decomp, f"Mismatch for mode={mode}"

    # Also test count <= 0
    r_orig_neg = run_one(orig_code, 0, 1, initial_slots)
    r_decomp_neg = run_one(decomp_code, 0, 1, initial_slots)
    assert r_orig_neg == r_decomp_neg

    print("ui_func_002e2750: PASS")

def main():
    test_camp_func_002d65fc()
    test_effGeometry_func_002de208()
    test_ui_func_002df484()
    test_script_vm_func_002dfcf4()
    test_ui_func_002e2750()
    print("\n========================================")
    print("ALL 5 FUNCTIONS IN PART 18 PASSED 100%!")
    print("========================================")

if __name__ == "__main__":
    main()
