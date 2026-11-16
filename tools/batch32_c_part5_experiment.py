#!/usr/bin/env python3
"""Differential test for batch 32 C part 5:
- camp_func_002b9220 (0x002B9220, 252 B)
- engine_func_002bc744 (0x002BC744, 228 B)
- camp_func_002dc5cc (0x002DC5CC, 248 B)
- script_vm_func_002df7f8 (0x002DF7F8, 220 B)
- script_vm_func_002e16d0 (0x002E16D0, 216 B)
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
SOURCE = ROOT / "src/engine/leaf_batch32_c.cpp"

with open(ORIG_BIN, "rb") as f:
    ORIG_DATA = f.read()

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS, COMPILED_ST_VALUES, RODATA_BYTES
    if COMPILED_FUNCTIONS is None:
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

def test_002b9220(out: Path):
    print("Testing camp_func_002b9220 (0x002B9220)...")
    comp, relocs = compile_function("camp_func_002b9220", out)
    orig_bytes = load_original_bytes(0x002B9220, 252)

    STUB_1FC0 = 0x002B1FC0
    STUB_1DFC = 0x002B1DFC
    STUB_1C8C = 0x002B1C8C

    syms = {
        "ui_func_002b1fc0": STUB_1FC0,
        "ui_func_002b1dfc": STUB_1DFC,
        "ui_func_002b1c8c": STUB_1C8C,
    }
    staged_compiled = stage_body(comp, relocs, 0x002B9220, syms, "camp_func_002b9220")

    stub_nop = struct.pack("<II", 0xe1a00000, 0xe12fff1e)
    OBJ_ADDR = 0x10008000

    # Cases: (step, flag, cur_c, b86, b87, b88, b89)
    cases = [
        (0, 0, 0, 0, 0, 0, 0),
        (0, 1, 0, 0, 0, 0, 0),
        (5, 0, 0x100000, 0, 0, 0, 0),
        (20, 1, 0x50000, 0, 0, 0, 0),
        (1, 0, 0x2000, 1, 1, 1, 1),   # all 4 bytes active -> sets 0x8a to 1
        (1, 0, 0x2000, 1, 1, 0, 1),   # not all 4 bytes active -> sets 0x8a to 0
    ]

    for step, flag, cur_c, b86, b87, b88, b89 in cases:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002B9220, code_bytes)
            uc.mem_write(STUB_1FC0, stub_nop)
            uc.mem_write(STUB_1DFC, stub_nop)
            uc.mem_write(STUB_1C8C, stub_nop)

            obj_data = bytearray(0x100)
            struct.pack_into("<h", obj_data, 0x52, step)
            struct.pack_into("<i", obj_data, 0x0C, cur_c)
            obj_data[0x86] = b86
            obj_data[0x87] = b87
            obj_data[0x88] = b88
            obj_data[0x89] = b89
            uc.mem_write(OBJ_ADDR, bytes(obj_data))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, OBJ_ADDR)
            uc.reg_write(UC_ARM_REG_R1, flag)

            uc.emu_start(0x002B9220, 0x00100000, count=500)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            if r0 >= 0x80000000:
                r0 -= 0x100000000
            state = uc.mem_read(OBJ_ADDR, 0x100)
            results.append((r0, state))

        assert results[0] == results[1], f"Mismatch for case ({step}, {flag}, {hex(cur_c)}): {results[0][0]} != {results[1][0]}"
    print("  camp_func_002b9220: PASS (all cases match)")

def test_002bc744(out: Path):
    print("Testing engine_func_002bc744 (0x002BC744)...")
    comp, relocs = compile_function("engine_func_002bc744", out)
    orig_bytes = load_original_bytes(0x002BC744, 228)

    GLOBAL_FLOAT_LOC = 0x004E39E0 + 0x1F8
    OUT_BUF = 0x10009000

    staged_compiled = stage_body(comp, relocs, 0x002BC744, {}, "engine_func_002bc744")

    cases = [
        (0, 0),
        (1, 0),
        (0, 0x501),
        (1, 0x501),
        (0, 0x502),
        (1, 0x502),
        (2, 0x600),
    ]

    for p1, p2 in cases:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002BC744, code_bytes)

            uc.mem_write(GLOBAL_FLOAT_LOC, struct.pack("<f", 123.456))
            uc.mem_write(OUT_BUF, b'\x00' * 0x40)

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, OUT_BUF)
            uc.reg_write(UC_ARM_REG_R1, p1)
            uc.reg_write(UC_ARM_REG_R2, p2)

            uc.emu_start(0x002BC744, 0x00100000, count=200)
            data = uc.mem_read(OUT_BUF, 0x30)
            results.append(data)

        assert results[0] == results[1], f"Mismatch for case ({p1}, {hex(p2)})"
    print("  engine_func_002bc744: PASS (all cases match)")

def test_002dc5cc(out: Path):
    print("Testing camp_func_002dc5cc (0x002DC5CC)...")
    comp, relocs = compile_function("camp_func_002dc5cc", out)
    orig_bytes = load_original_bytes(0x002DC5CC, 248)

    STUB_9A44 = 0x00249A44
    STUB_E464 = 0x002AE464
    STUB_40B8 = 0x002840B8
    STUB_E3F0 = 0x002AE3F0
    STUB_89E4 = 0x002A89E4
    STUB_779C = 0x0025779C

    ENT_A = 0x10005000
    ENT_B = 0x10005100
    INFO_A = 0x10006000
    INFO_B = 0x10006100
    EXTRA_INFO = 0x10006200
    PARAM_A = 0x10007000
    PARAM_B = 0x10007004

    syms = {
        "camp_func_00249a44": STUB_9A44,
        "battle_func_002ae464": STUB_E464,
        "camp_func_002840b8": STUB_40B8,
        "battle_func_002ae3f0": STUB_E3F0,
        "camp_func_002a89e4": STUB_89E4,
        "battle_func_0025779c": STUB_779C,
    }
    staged_compiled = stage_body(comp, relocs, 0x002DC5CC, syms, "camp_func_002dc5cc")

    stub_9a44_code = struct.pack("<IIIII",
        0xe3500001,  # cmp r0, #1
        0x059f0004,  # ldreq r0, [pc, #4]
        0x159f0004,  # ldrne r0, [pc, #4]
        0xe12fff1e,  # bx lr
        ENT_A,
    ) + struct.pack("<I", ENT_B)

    stub_info_code = struct.pack("<IIIII",
        0xe3500001,  # cmp r0, #1
        0x059f0004,  # ldreq r0, [pc, #4]
        0x159f0004,  # ldrne r0, [pc, #4]
        0xe12fff1e,  # bx lr
        INFO_A,
    ) + struct.pack("<I", INFO_B)

    stub_89e4_code = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", EXTRA_INFO)

    # (is_dead_a, is_dead_b, val_a, val_b, ret_779c)
    cases = [
        (True, False, 10, 20, 0),     # A dead, B normal -> diff = -10
        (False, False, 50, 30, 0),    # diff = 20
        (False, False, 40, 40, 88),   # same val -> delegates to 25779c -> returns 88
    ]

    for is_dead_a, is_dead_b, v_a, v_b, ret_779c in cases:
        stub_e464_code = struct.pack("<IIII",
            0xe3500001,
            0x03a00000 | (1 if is_dead_a else 0),
            0x13a00000 | (1 if is_dead_b else 0),
            0xe12fff1e,
        )
        stub_779c_code = struct.pack("<II", 0xe3a00000 | (ret_779c & 0xFF), 0xe12fff1e)

        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002DC5CC, code_bytes)
            uc.mem_write(STUB_9A44, stub_9a44_code)
            uc.mem_write(STUB_E464, stub_e464_code)
            uc.mem_write(STUB_40B8, stub_info_code)
            uc.mem_write(STUB_E3F0, stub_info_code)
            uc.mem_write(STUB_89E4, stub_89e4_code)
            uc.mem_write(STUB_779C, stub_779c_code)

            ent_a_buf = bytearray(0x30)
            ent_b_buf = bytearray(0x30)
            struct.pack_into("<H", ent_a_buf, 0x26, 1)
            struct.pack_into("<H", ent_b_buf, 0x26, 2)
            uc.mem_write(ENT_A, bytes(ent_a_buf))
            uc.mem_write(ENT_B, bytes(ent_b_buf))

            info_a_buf = bytearray(0x30)
            info_b_buf = bytearray(0x30)
            struct.pack_into("<H", info_a_buf, 0x22 if is_dead_a else 0x24, v_a)
            struct.pack_into("<H", info_b_buf, 0x22 if is_dead_b else 0x24, v_b)
            uc.mem_write(INFO_A, bytes(info_a_buf))
            uc.mem_write(INFO_B, bytes(info_b_buf))

            extra_buf = bytearray(0x50)
            struct.pack_into("<H", extra_buf, 0x46, 123)
            uc.mem_write(EXTRA_INFO, bytes(extra_buf))

            uc.mem_write(PARAM_A, struct.pack("<H", 1))
            uc.mem_write(PARAM_B, struct.pack("<H", 2))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, PARAM_A)
            uc.reg_write(UC_ARM_REG_R1, PARAM_B)

            uc.emu_start(0x002DC5CC, 0x00100000, count=500)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            if r0 >= 0x80000000:
                r0 -= 0x100000000
            results.append(r0)

        assert results[0] == results[1], f"Mismatch for case ({is_dead_a}, {is_dead_b}, {v_a}, {v_b}): {results[0]} != {results[1]}"
    print("  camp_func_002dc5cc: PASS (all cases match)")

def test_002df7f8(out: Path):
    print("Testing script_vm_func_002df7f8 (0x002DF7F8)...")
    comp, relocs = compile_function("script_vm_func_002df7f8", out)
    orig_bytes = load_original_bytes(0x002DF7F8, 220)

    STUB_CTX = 0x002C2B1C
    STUB_27636C = 0x0027636C
    STUB_287B10 = 0x00287B10
    STUB_316FC4 = 0x00316FC4

    CONFIG_ADDR = 0x0049F91C
    CTX_ADDR = 0x10005000
    RES_ADDR = 0x10006000

    syms = {
        "engine_func_002c2b1c": STUB_CTX,
        "script_vm_func_0027636c": STUB_27636C,
        "script_vm_func_00287b10": STUB_287B10,
        "camp_func_00316fc4": STUB_316FC4,
    }
    staged_compiled = stage_body(comp, relocs, 0x002DF7F8, syms, "script_vm_func_002df7f8")

    stub_ctx_code = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", CTX_ADDR)
    stub_res_code = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", RES_ADDR)

    # Cases: (type, param, field_val, exp_clamped)
    cases = [
        (1, 0x10, 10, 10),      # type 1, <= 15
        (1, 0x10, 25, 15),      # type 1, > 15 -> clamped to 15
        (1, 0x10, 0, 0xFF),     # type 1, == 0 -> 0xFF (-1)
        (2, 0x20, 8, 8),        # type 2
        (3, 0x30, 5, 5),        # type 3
        (0, 0, 0, 0),           # type 0
    ]

    for type_idx, param, field_val, exp_c in cases:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002DF7F8, code_bytes)
            uc.mem_write(STUB_CTX, stub_ctx_code)
            uc.mem_write(STUB_27636C, stub_res_code)
            uc.mem_write(STUB_287B10, stub_res_code)
            uc.mem_write(STUB_316FC4, stub_res_code)

            cfg_data = bytearray(0xC0)
            struct.pack_into("<I", cfg_data, 0xA4, type_idx)
            struct.pack_into("<I", cfg_data, 0xA8, param)
            uc.mem_write(CONFIG_ADDR, bytes(cfg_data))

            res_data = bytearray(0x20)
            struct.pack_into("<H", res_data, 0x0C, 0x11)
            struct.pack_into("<H", res_data, 0x0E, 0x22)
            struct.pack_into("<H", res_data, 0x0A, field_val)
            struct.pack_into("<H", res_data, 0x08, field_val)
            struct.pack_into("<H", res_data, 0x10, 0x33)
            struct.pack_into("<H", res_data, 0x16, 0x44)
            uc.mem_write(RES_ADDR, bytes(res_data))

            ctx_data = bytearray(0x800)
            uc.mem_write(CTX_ADDR, bytes(ctx_data))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)

            uc.emu_start(0x002DF7F8, 0x00100000, count=500)
            out_ctx = uc.mem_read(CTX_ADDR, 0x800)
            results.append(out_ctx)

        assert results[0] == results[1], f"Mismatch for case ({type_idx}, {param}, {field_val})"
    print("  script_vm_func_002df7f8: PASS (all cases match)")

def test_002e16d0(out: Path):
    print("Testing script_vm_func_002e16d0 (0x002E16D0)...")
    comp, relocs = compile_function("script_vm_func_002e16d0", out)
    orig_bytes = load_original_bytes(0x002E16D0, 216)

    STUB_F9F4 = 0x0026F9F4
    STUB_72F8 = 0x002972F8
    STUB_FA70 = 0x0026FA70
    STUB_F474 = 0x0026F474
    STUB_D838 = 0x0028D838
    STUB_F460 = 0x0026F460
    STUB_F3F8 = 0x0026F3F8
    STUB_8B78 = 0x002B8B78
    STUB_ECC0 = 0x0024ECC0

    OBJ_ADDR = 0x10007000
    SUB_ADDR = 0x10008000
    RES_ADDR = 0x10009000

    syms = {
        "camp_func_0026f9f4": STUB_F9F4,
        "scrScriptProcess_func_002972f8": STUB_72F8,
        "camp_func_0026fa70": STUB_FA70,
        "camp_func_0026f474": STUB_F474,
        "camp_func_0028d838": STUB_D838,
        "script_vm_func_0026f460": STUB_F460,
        "script_vm_func_0026f3f8": STUB_F3F8,
        "script_vm_func_002b8b78": STUB_8B78,
        "script_vm_func_0024ecc0": STUB_ECC0,
    }
    staged_compiled = stage_body(comp, relocs, 0x002E16D0, syms, "script_vm_func_002e16d0")

    stub_72f8_code = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", RES_ADDR)
    stub_nop = struct.pack("<II", 0xe1a00000, 0xe12fff1e)

    # Cases: (b124, f9f4_ret, a4, a8, ac, b74, d838_ret, b129)
    cases = [
        (1, 1, 1, 1, 1, 1, 1, 0),     # active_flag != 0 -> 0
        (0, 0, 1, 1, 1, 1, 1, 0),     # f9f4 returns 0 -> 0
        (0, 1, 0, 1, 1, 1, 1, 0),     # a4 == 0 -> 0
        (0, 1, 1, 1, 1, 0, 1, 0),     # b74 != 1 -> 0
        (0, 1, 1, 1, 1, 1, 1, 0),     # full pass, d838=1, b129=0 -> 2
        (0, 1, 1, 1, 1, 1, 0, 1),     # full pass, d838=0, b129=1 -> 2
    ]

    for b124, f9f4_r, a4, a8, ac, b74, d838_r, b129 in cases:
        stub_f9f4_code = struct.pack("<II", 0xe3a00000 | (f9f4_r & 0xFF), 0xe12fff1e)
        stub_d838_code = struct.pack("<II", 0xe3a00000 | (d838_r & 0xFF), 0xe12fff1e)

        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002E16D0, code_bytes)
            uc.mem_write(STUB_F9F4, stub_f9f4_code)
            uc.mem_write(STUB_72F8, stub_72f8_code)
            uc.mem_write(STUB_FA70, stub_nop)
            uc.mem_write(STUB_F474, stub_nop)
            uc.mem_write(STUB_D838, stub_d838_code)
            uc.mem_write(STUB_F460, stub_nop)
            uc.mem_write(STUB_F3F8, stub_nop)
            uc.mem_write(STUB_8B78, stub_nop)
            uc.mem_write(STUB_ECC0, stub_nop)

            obj_data = bytearray(0x200)
            obj_data[0x124] = b124
            struct.pack_into("<I", obj_data, 4, SUB_ADDR)
            struct.pack_into("<I", obj_data, 0xA4, a4)
            struct.pack_into("<I", obj_data, 0xA8, a8)
            struct.pack_into("<I", obj_data, 0xAC, ac)
            obj_data[0x74] = b74
            obj_data[0x129] = b129
            uc.mem_write(OBJ_ADDR, bytes(obj_data))

            uc.mem_write(RES_ADDR, b'\x00' * 0x200)

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, OBJ_ADDR)

            uc.emu_start(0x002E16D0, 0x00100000, count=500)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            state = uc.mem_read(OBJ_ADDR, 0x200)
            res_state = uc.mem_read(RES_ADDR, 0x200)
            results.append((r0, state, res_state))

        assert results[0] == results[1], f"Mismatch for case ({b124}, {f9f4_r}, {a4}, {b74}): {results[0][0]} != {results[1][0]}"
    print("  script_vm_func_002e16d0: PASS (all cases match)")

def main():
    out = ROOT / "build"
    out.mkdir(exist_ok=True)
    print("Running Batch 32 C Part 5 differential tests...")
    test_002b9220(out)
    test_002bc744(out)
    test_002dc5cc(out)
    test_002df7f8(out)
    test_002e16d0(out)
    print("\nALL BATCH 32 C PART 5 TESTS PASSED!")

if __name__ == "__main__":
    main()
