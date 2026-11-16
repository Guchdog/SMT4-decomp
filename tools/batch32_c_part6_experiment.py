#!/usr/bin/env python3
"""Differential test for batch 32 C part 6:
- func_002bc304 (0x002BC304, 196 B)
- func_002c522c (0x002C522C, 196 B)
- engine_func_002e0328 (0x002E0328, 196 B)
- engine_func_002e130c (0x002E130C, 216 B)
- camp_func_002eea2c (0x002EEA2C, 256 B)
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
    UC_ARM_REG_D0,
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

# ---------------------------------------------------------------------------
# Test 1: func_002bc304 (0x002BC304)
# ---------------------------------------------------------------------------
def test_002bc304(out: Path):
    print("Testing func_002bc304 (0x002BC304)...")
    comp, relocs = compile_function("func_002bc304", out)
    orig_bytes = load_original_bytes(0x002BC304, 196)

    CALL_1371A0 = 0x001371A0
    BASE_4E39E0 = 0x004E39E0

    syms = {
        "func_001371a0": CALL_1371A0,
    }
    staged_compiled = stage_body(comp, relocs, 0x002BC304, syms, "func_002bc304")

    stub_ret = struct.pack("<I", 0xe12fff1e) # bx lr
    OBJ_ADDR = 0x10085000

    test_cases = [
        # (id, flag, r84, f200, f201)
        (0x400, 0, 0, 1, 0),
        (0x400, 1, 1, 0, 1),
        (0x401, 0, 0, 1, 0),
        (0x401, 0, 1, 1, 1),
        (0x401, 1, 0, 0, 1),
        (0x410, 0, 0, 1, 0),
        (0x410, 1, 0, 0, 0),
        (0x410, 1, 1, 1, 1),
    ]

    for id_val, flag_val, r84, f200, f201 in test_cases:
        captured_orig = []
        captured_comp = []

        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002BC304, code_bytes)
            uc.mem_write(CALL_1371A0, stub_ret)

            # Setup base struct 0x004E39E0
            uc.mem_write(BASE_4E39E0 + 0x84, struct.pack("<I", r84))
            uc.mem_write(BASE_4E39E0 + 0x1FC, struct.pack("<I", 0x12345678))
            uc.mem_write(BASE_4E39E0 + 0x200, struct.pack("<B", f200))
            uc.mem_write(BASE_4E39E0 + 0x201, struct.pack("<B", f201))

            for off in (0x88, 0xC4, 0x100):
                p = BASE_4E39E0 + off
                uc.mem_write(p + 0x00, struct.pack("<I", off + 1))
                uc.mem_write(p + 0x08, struct.pack("<I", off + 2))
                uc.mem_write(p + 0x30, struct.pack("<I", off + 3))
                uc.mem_write(p + 0x34, struct.pack("<I", off + 4))
                uc.mem_write(p + 0x38, struct.pack("<I", off + 5))

            # Setup input obj
            uc.mem_write(OBJ_ADDR, struct.pack("<I", id_val))
            uc.mem_write(OBJ_ADDR + 0x14, struct.pack("<I", 2))
            uc.mem_write(OBJ_ADDR + 0x18, struct.pack("<I", 0xAAAA0018))
            uc.mem_write(OBJ_ADDR + 0x1C, struct.pack("<I", 0xBBBB001C))
            uc.mem_write(OBJ_ADDR + 0x20 + 8, struct.pack("<I", 0xCCCC0028))

            dest_list = captured_comp if is_comp else captured_orig

            def hook_1371a0(uc, addr, size, user_data):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                cur_sp = uc.reg_read(UC_ARM_REG_SP)
                stack_args = [struct.unpack("<I", uc.mem_read(cur_sp + i*4, 4))[0] for i in range(7)]
                dest_list.append((r0, r1, r2, r3, tuple(stack_args)))

            uc.hook_add(1, hook_1371a0, None, CALL_1371A0, CALL_1371A0 + 4)

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)
            uc.reg_write(UC_ARM_REG_R0, OBJ_ADDR)
            uc.reg_write(UC_ARM_REG_R1, flag_val)

            uc.emu_start(0x002BC304, 0xF0000000, timeout=2000000)

        assert captured_orig == captured_comp, f"func_002bc304 mismatch for case {(id_val, flag_val, r84, f200, f201)}: orig={captured_orig} vs comp={captured_comp}"

    print("  func_002bc304: PASS (all cases match)")

# ---------------------------------------------------------------------------
# Test 2: func_002c522c (0x002C522C)
# ---------------------------------------------------------------------------
def test_002c522c(out: Path):
    print("Testing func_002c522c (0x002C522C)...")
    comp, relocs = compile_function("func_002c522c", out)
    orig_bytes = load_original_bytes(0x002C522C, 196)

    CALL_1371A0 = 0x001371A0
    CALL_2BC3C8 = 0x002BC3C8
    BASE_4E39E0 = 0x004E39E0

    syms = {
        "func_001371a0": CALL_1371A0,
        "battle_func_002bc3c8": CALL_2BC3C8,
    }
    staged_compiled = stage_body(comp, relocs, 0x002C522C, syms, "func_002c522c")

    stub_ret = struct.pack("<I", 0xe12fff1e) # bx lr

    test_cases = [
        # (id, f1f4, flag200, flag201)
        (0x400, 0, 1, 0),
        (0x400, 0, 0, 1),
        (0x400, 1, 1, 0), # early return
        (0x401, 0, 1, 1),
        (0x401, 0, 0, 0),
        (0x410, 0, 1, 0),
        (0x410, 0, 0, 1),
    ]

    for id_val, f1f4, f200, f201 in test_cases:
        captured_orig = []
        captured_comp = []

        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002C522C, code_bytes)
            uc.mem_write(CALL_2BC3C8, stub_ret)
            uc.mem_write(CALL_1371A0, stub_ret)

            # Setup base struct 0x004E39E0
            uc.mem_write(BASE_4E39E0 + 0x1F4, struct.pack("<I", f1f4))
            uc.mem_write(BASE_4E39E0 + 0x1FC, struct.pack("<I", 0x55AA55AA))
            uc.mem_write(BASE_4E39E0 + 0x200, struct.pack("<B", f200))
            uc.mem_write(BASE_4E39E0 + 0x201, struct.pack("<B", f201))

            for r5_off in (0x00, 0x2C, 0x58):
                p = BASE_4E39E0 + r5_off
                uc.mem_write(p + 0x14, struct.pack("<I", 1))
                uc.mem_write(p + 0x18, struct.pack("<I", r5_off + 10))
                uc.mem_write(p + 0x1C, struct.pack("<I", r5_off + 11))
                uc.mem_write(p + 0x20 + 4, struct.pack("<I", r5_off + 12))

            for r4_off in (0x88, 0xC4, 0x100):
                p = BASE_4E39E0 + r4_off
                uc.mem_write(p + 0x00, struct.pack("<I", r4_off + 1))
                uc.mem_write(p + 0x08, struct.pack("<I", r4_off + 2))
                uc.mem_write(p + 0x30, struct.pack("<I", r4_off + 3))
                uc.mem_write(p + 0x34, struct.pack("<I", r4_off + 4))
                uc.mem_write(p + 0x38, struct.pack("<I", r4_off + 5))

            dest_list = captured_comp if is_comp else captured_orig

            def hook_1371a0(uc, addr, size, user_data):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                cur_sp = uc.reg_read(UC_ARM_REG_SP)
                stack_args = [struct.unpack("<I", uc.mem_read(cur_sp + i*4, 4))[0] for i in range(7)]
                dest_list.append((r0, r1, r2, r3, tuple(stack_args)))

            uc.hook_add(1, hook_1371a0, None, CALL_1371A0, CALL_1371A0 + 4)

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)
            uc.reg_write(UC_ARM_REG_R0, id_val)

            uc.emu_start(0x002C522C, 0xF0000000, timeout=2000000)

        assert captured_orig == captured_comp, f"func_002c522c mismatch for case {(id_val, f1f4, f200, f201)}: orig={captured_orig} vs comp={captured_comp}"

    print("  func_002c522c: PASS (all cases match)")

# ---------------------------------------------------------------------------
# Test 3: engine_func_002e0328 (0x002E0328)
# ---------------------------------------------------------------------------
def test_002e0328(out: Path):
    print("Testing engine_func_002e0328 (0x002E0328)...")
    comp, relocs = compile_function("engine_func_002e0328", out)
    orig_bytes = load_original_bytes(0x002E0328, 196)

    CALL_2C2B1C = 0x002C2B1C
    CTX_ADDR = 0x10085000
    BASE_4BE698 = 0x004BE698

    syms = {
        "engine_func_002c2b1c": CALL_2C2B1C,
    }
    staged_compiled = stage_body(comp, relocs, 0x002E0328, syms, "engine_func_002e0328")

    stub_ret = struct.pack("<I", 0xe12fff1e) # bx lr

    test_cases = [
        # (filter, x, y)
        (0, 10.0, 10.0),    # in box 0
        (1, 10.0, 10.0),    # in box 0, filter matches
        (2, 10.0, 10.0),    # in box 0, filter mismatch -> fallback
        (0x63, 10.0, 10.0), # 0x63 matches any filter
        (0, 50.0, 50.0),    # in box 1
        (0, 100.0, 100.0),  # outside all boxes -> fallback
        (5, 50.0, 50.0),    # in box 1, filter matches
        (9, 50.0, 50.0),    # in box 1, filter mismatch
    ]

    for filter_val, x_val, y_val in test_cases:
        results = []
        ctx_after = []

        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002E0328, code_bytes)
            uc.mem_write(CALL_2C2B1C, stub_ret)

            def hook_2c2b1c(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, CTX_ADDR)
            uc.hook_add(1, hook_2c2b1c, None, CALL_2C2B1C, CALL_2C2B1C + 4)

            # CTX initial fallback idx at +0xd58 = 2
            uc.mem_write(CTX_ADDR + 0xD58, struct.pack("<h", 2))

            # count at base + 0x1200 = 3
            uc.mem_write(BASE_4BE698 + 0x1200, struct.pack("<i", 3))

            # Entry 0: x:[0, 20], y:[0, 20], filter: 1, val: 0x100
            uc.mem_write(BASE_4BE698 + 0*32 + 0x00, struct.pack("<f", 0.0))
            uc.mem_write(BASE_4BE698 + 0*32 + 0x08, struct.pack("<f", 0.0))
            uc.mem_write(BASE_4BE698 + 0*32 + 0x0C, struct.pack("<f", 20.0))
            uc.mem_write(BASE_4BE698 + 0*32 + 0x14, struct.pack("<f", 20.0))
            uc.mem_write(BASE_4BE698 + 0*32 + 0x18, struct.pack("<I", 0x100))
            uc.mem_write(BASE_4BE698 + 0*32 + 0x1C, struct.pack("<I", 1))

            # Entry 1: x:[40, 60], y:[40, 60], filter: 5, val: 0x200
            uc.mem_write(BASE_4BE698 + 1*32 + 0x00, struct.pack("<f", 40.0))
            uc.mem_write(BASE_4BE698 + 1*32 + 0x08, struct.pack("<f", 40.0))
            uc.mem_write(BASE_4BE698 + 1*32 + 0x0C, struct.pack("<f", 60.0))
            uc.mem_write(BASE_4BE698 + 1*32 + 0x14, struct.pack("<f", 60.0))
            uc.mem_write(BASE_4BE698 + 1*32 + 0x18, struct.pack("<I", 0x200))
            uc.mem_write(BASE_4BE698 + 1*32 + 0x1C, struct.pack("<I", 5))

            # Entry 2 (fallback entry): val: 0x999
            uc.mem_write(BASE_4BE698 + 2*32 + 0x18, struct.pack("<I", 0x999))

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)
            uc.reg_write(UC_ARM_REG_R0, filter_val)

            d0_bytes = struct.pack("<ff", x_val, y_val)
            uc.reg_write(UC_ARM_REG_D0, struct.unpack("<Q", d0_bytes)[0])

            uc.emu_start(0x002E0328, 0xF0000000, timeout=2000000)
            res = uc.reg_read(UC_ARM_REG_R0)
            results.append(res)
            saved_idx = struct.unpack("<h", uc.mem_read(CTX_ADDR + 0xD58, 2))[0]
            ctx_after.append(saved_idx)

        assert results[0] == results[1], f"Mismatch ret for case {(filter_val, x_val, y_val)}: {results[0]} != {results[1]}"
        assert ctx_after[0] == ctx_after[1], f"Mismatch ctx for case {(filter_val, x_val, y_val)}: {ctx_after[0]} != {ctx_after[1]}"

    print("  engine_func_002e0328: PASS (all cases match)")

# ---------------------------------------------------------------------------
# Test 4: engine_func_002e130c (0x002E130C)
# ---------------------------------------------------------------------------
def test_002e130c(out: Path):
    print("Testing engine_func_002e130c (0x002E130C)...")
    comp, relocs = compile_function("engine_func_002e130c", out)
    orig_bytes = load_original_bytes(0x002E130C, 216)

    CALL_254AC4 = 0x00254AC4
    CALL_2ADB14 = 0x002ADB14
    CALL_2ADA98 = 0x002ADA98
    CALL_2BB8E4 = 0x002BB8E4
    CALL_2C3714 = 0x002C3714

    syms = {
        "ui_func_00254ac4": CALL_254AC4,
        "engine_func_002adb14": CALL_2ADB14,
        "ui_func_002ada98": CALL_2ADA98,
        "engine_func_002bb8e4": CALL_2BB8E4,
        "func_002c3714": CALL_2C3714,
    }
    staged_compiled = stage_body(comp, relocs, 0x002E130C, syms, "engine_func_002e130c")

    stub_ret = struct.pack("<I", 0xe12fff1e) # bx lr
    OBJ_ADDR = 0x10085000

    test_cases = [
        # (ui_254ac4_ret, ada98_ret, bb8e4_ret)
        (0, 0, 0),         # ui_254ac4 fails -> returns 0xe0e046bc
        (1, 0, 0),         # all succeed -> returns 0
        (1, -1, 0),        # ada98 returns negative -> returns -1
        (1, 0, -5),        # bb8e4 returns negative -> returns -5
        (1, 0x80000001, 0),# negative bit set
    ]

    for c_254, c_ada, c_bb in test_cases:
        results = []
        c3714_calls = []
        obj_after = []

        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002E130C, code_bytes)

            for fn in (CALL_254AC4, CALL_2ADB14, CALL_2ADA98, CALL_2BB8E4, CALL_2C3714):
                uc.mem_write(fn, stub_ret)

            def hook_254(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, c_254)
            uc.hook_add(1, hook_254, None, CALL_254AC4, CALL_254AC4 + 4)

            def hook_ada(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, c_ada & 0xFFFFFFFF)
            uc.hook_add(1, hook_ada, None, CALL_2ADA98, CALL_2ADA98 + 4)

            def hook_bb(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, c_bb & 0xFFFFFFFF)
            uc.hook_add(1, hook_bb, None, CALL_2BB8E4, CALL_2BB8E4 + 4)

            cur_calls = []
            def hook_3714(uc, addr, size, ud):
                cur_calls.append(uc.reg_read(UC_ARM_REG_R0))
            uc.hook_add(1, hook_3714, None, CALL_2C3714, CALL_2C3714 + 4)

            # Fill obj with dummy non-zero
            uc.mem_write(OBJ_ADDR, b"\xAA" * 0x40)

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)
            uc.reg_write(UC_ARM_REG_R0, OBJ_ADDR)
            uc.reg_write(UC_ARM_REG_R1, 0x1111)
            uc.reg_write(UC_ARM_REG_R2, 0x2222)

            uc.emu_start(0x002E130C, 0xF0000000, timeout=2000000)
            res = uc.reg_read(UC_ARM_REG_R0)
            results.append(res)
            c3714_calls.append(cur_calls)
            obj_after.append(uc.mem_read(OBJ_ADDR, 0x20))

        assert results[0] == results[1], f"Mismatch ret for case {(c_254, c_ada, c_bb)}: {results[0]} != {results[1]}"
        assert c3714_calls[0] == c3714_calls[1], f"Mismatch c3714 for case {(c_254, c_ada, c_bb)}: {c3714_calls[0]} != {c3714_calls[1]}"
        assert obj_after[0] == obj_after[1], f"Mismatch obj for case {(c_254, c_ada, c_bb)}: {obj_after[0]} != {obj_after[1]}"

    print("  engine_func_002e130c: PASS (all cases match)")

# ---------------------------------------------------------------------------
# Test 5: camp_func_002eea2c (0x002EEA2C)
# ---------------------------------------------------------------------------
def test_002eea2c(out: Path):
    print("Testing camp_func_002eea2c (0x002EEA2C)...")
    comp, relocs = compile_function("camp_func_002eea2c", out)
    orig_bytes = load_original_bytes(0x002EEA2C, 256)

    CALL_GET_TABLE = 0x002C0EC4
    CALL_GET_DATA = 0x002C0E9C
    CALL_GET_ROWS = 0x002C0E4C

    TABLE_ADDR = 0x10085000

    syms = {
        "Tbb_GetGlobalSubTable": CALL_GET_TABLE,
        "Tbb_GetPayloadData": CALL_GET_DATA,
        "Tbb_GetRowCount": CALL_GET_ROWS,
    }
    staged_compiled = stage_body(comp, relocs, 0x002EEA2C, syms, "camp_func_002eea2c")

    stub_ret = struct.pack("<I", 0xe12fff1e) # bx lr

    test_cases = [
        # (type, target_id, row_count)
        (5, 10, 5),   # odd count, target at odd index
        (5, 1, 5),    # odd count, target at index 0
        (4, 20, 4),   # even count, target at index 1
        (3, 30, 4),   # even count, target at index 2
        (0x5C, 40, 6),# target at index 3
        (0x5D, 99, 4),# target not in table -> 0
        (1, 10, 0),   # 0 count -> 0
        (1, 10, -1),  # negative count -> 0
    ]

    for type_val, target_id, row_count in test_cases:
        results = []
        captured_subtypes = []

        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002EEA2C, code_bytes)

            for fn in (CALL_GET_TABLE, CALL_GET_DATA, CALL_GET_ROWS):
                uc.mem_write(fn, stub_ret)

            # Clear table
            uc.mem_write(TABLE_ADDR, b"\x00" * (6 * 92 + 0x100))

            # Populate table rows: stride 92, id at offset 8
            ids = [1, 20, 30, 40, 10, 50]
            for i in range(min(row_count, len(ids))):
                if i >= 0:
                    uc.mem_write(TABLE_ADDR + i * 92 + 8, struct.pack("<I", ids[i]))

            subtypes = []
            def hook_table(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                subtypes.append((r0, r1))
                uc.reg_write(UC_ARM_REG_R0, 0xCAFE0000)
            uc.hook_add(1, hook_table, None, CALL_GET_TABLE, CALL_GET_TABLE + 4)

            def hook_data(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, TABLE_ADDR)
            uc.hook_add(1, hook_data, None, CALL_GET_DATA, CALL_GET_DATA + 4)

            def hook_rows(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, row_count & 0xFFFFFFFF)
            uc.hook_add(1, hook_rows, None, CALL_GET_ROWS, CALL_GET_ROWS + 4)

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)
            uc.reg_write(UC_ARM_REG_R0, type_val)
            uc.reg_write(UC_ARM_REG_R1, target_id)

            uc.emu_start(0x002EEA2C, 0xF0000000, timeout=2000000)
            res = uc.reg_read(UC_ARM_REG_R0)
            results.append(res)
            captured_subtypes.append(subtypes)

        assert results[0] == results[1], f"Mismatch ret for case {(type_val, target_id, row_count)}: {results[0]} != {results[1]}"
        assert captured_subtypes[0] == captured_subtypes[1], f"Mismatch subtypes for case {(type_val, target_id, row_count)}: {captured_subtypes[0]} != {captured_subtypes[1]}"

    print("  camp_func_002eea2c: PASS (all cases match)")


def main():
    print("Running Batch 32 C Part 6 differential tests...")
    out_dir = ROOT / "build"
    out_dir.mkdir(exist_ok=True)

    test_002bc304(out_dir)
    test_002c522c(out_dir)
    test_002e0328(out_dir)
    test_002e130c(out_dir)
    test_002eea2c(out_dir)

    print("\nALL BATCH 32 C PART 6 TESTS PASSED!")

if __name__ == "__main__":
    main()
