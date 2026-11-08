#!/usr/bin/env python3
"""Differential test for batch 32 C part 7:
- engine_func_002bf798 (0x002BF798, 196 B)
- engine_func_002c34a4 (0x002C34A4, 196 B)
- engine_func_002c54f0 (0x002C54F0, 244 B)
- ui_func_002e3d70 (0x002E3D70, 220 B)
- ui_func_002bf460 (0x002BF460, 248 B)
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

# ---------------------------------------------------------------------------
# Test 1 & 2: engine_func_002bf798 and engine_func_002c34a4
# ---------------------------------------------------------------------------
def run_allocator_test(func_name: str, target_addr: int, out: Path):
    print(f"Testing {func_name} (0x{target_addr:08X})...")
    comp, relocs = compile_function(func_name, out)
    orig_bytes = load_original_bytes(target_addr, 196)

    CALL_LOCK = 0x002C3AA8
    CALL_ALLOC = 0x002B2690
    CALL_REG = 0x002B25AC
    CALL_INIT = 0x002C3B48
    CALL_UNLOCK = 0x002C3A24

    syms = {
        "engine_func_002c3aa8": CALL_LOCK,
        "engine_func_002b2690": CALL_ALLOC,
        "engine_func_002b25ac": CALL_REG,
        "engine_func_002c3b48": CALL_INIT,
        "engine_func_002c3a24": CALL_UNLOCK,
    }
    staged_compiled = stage_body(comp, relocs, target_addr, syms, func_name)

    stub_ret = struct.pack("<I", 0xe12fff1e) # bx lr
    RAW_BASE = 0x10090000

    test_cases = [
        # (arg0, arg1, arg2, size, align, priority)
        (1, 2, 3, 0x100, 0x80, 0x3F800000),   # normal 128B align
        (1, 2, 3, 0x200, 0x40, 0x40000000),   # align < 0x80 -> clamped to 0x80
        (4, 5, 6, 0x50, 0x100, 0x0),          # 256B align
        (0, 0, 0, 0x1000, 0x200, 0x41200000), # 512B align
    ]

    for arg0, arg1, arg2, size, align, priority in test_cases:
        results = []
        raw_headers = []
        user_headers = []
        lock_calls = []
        unlock_calls = []
        init_calls = []

        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(target_addr, code_bytes)

            for fn in (CALL_LOCK, CALL_ALLOC, CALL_REG, CALL_INIT, CALL_UNLOCK):
                uc.mem_write(fn, stub_ret)

            # Allocator state 0x00465120
            uc.mem_write(0x00465120 + 4, struct.pack("<I", 0x11223344)) # mutex handle

            # Clear raw base buffer
            uc.mem_write(RAW_BASE, b"\x00" * 0x3000)

            l_calls = []
            def hook_lock(uc, addr, size, ud):
                l_calls.append(uc.reg_read(UC_ARM_REG_R0))
            uc.hook_add(1, hook_lock, None, CALL_LOCK, CALL_LOCK + 4)

            def hook_alloc(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, RAW_BASE)
            uc.hook_add(1, hook_alloc, None, CALL_ALLOC, CALL_ALLOC + 4)

            i_calls = []
            def hook_init(uc, addr, size_val, ud):
                i_calls.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)))
            uc.hook_add(1, hook_init, None, CALL_INIT, CALL_INIT + 4)

            u_calls = []
            def hook_unlock(uc, addr, size, ud):
                u_calls.append(uc.reg_read(UC_ARM_REG_R0))
            uc.hook_add(1, hook_unlock, None, CALL_UNLOCK, CALL_UNLOCK + 4)

            sp = STACK_BASE + STACK_SIZE - 0x1000
            # Push stack arguments: align at sp[0], priority at sp[4]
            uc.mem_write(sp, struct.pack("<II", align, priority))

            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)
            uc.reg_write(UC_ARM_REG_R0, arg0)
            uc.reg_write(UC_ARM_REG_R1, arg1)
            uc.reg_write(UC_ARM_REG_R2, arg2)
            uc.reg_write(UC_ARM_REG_R3, size)

            uc.emu_start(target_addr, 0xF0000000, timeout=2000000)
            ret_user = uc.reg_read(UC_ARM_REG_R0)
            results.append(ret_user)
            lock_calls.append(l_calls)
            unlock_calls.append(u_calls)
            init_calls.append(i_calls)

            # Check raw header at RAW_BASE (first 8 bytes)
            raw_headers.append(uc.mem_read(RAW_BASE, 8))
            # Check user back-pointer at ret_user - 4
            user_headers.append(uc.mem_read(ret_user - 4, 4))

        assert results[0] == results[1], f"{func_name} mismatch ret for case {(arg0, arg1, arg2, size, align, priority)}: {results[0]} != {results[1]}"
        assert raw_headers[0] == raw_headers[1], f"{func_name} mismatch raw_header for case: {raw_headers[0]} != {raw_headers[1]}"
        assert user_headers[0] == user_headers[1], f"{func_name} mismatch user_header for case: {user_headers[0]} != {user_headers[1]}"
        assert lock_calls[0] == lock_calls[1], f"{func_name} mismatch lock_calls"
        assert unlock_calls[0] == unlock_calls[1], f"{func_name} mismatch unlock_calls"
        assert init_calls[0] == init_calls[1], f"{func_name} mismatch init_calls"

    print(f"  {func_name}: PASS (all cases match)")

# ---------------------------------------------------------------------------
# Test 3: engine_func_002c54f0 (0x002C54F0)
# ---------------------------------------------------------------------------
def test_002c54f0(out: Path):
    print("Testing engine_func_002c54f0 (0x002C54F0)...")
    comp, relocs = compile_function("engine_func_002c54f0", out)
    orig_bytes = load_original_bytes(0x002C54F0, 244)

    CALL_LOCK = 0x002C3AA8
    CALL_ALLOC = 0x002B2690
    CALL_REG = 0x002B25AC
    CALL_INIT = 0x002C3B48
    CALL_UNLOCK = 0x002C3A24

    syms = {
        "engine_func_002c3aa8": CALL_LOCK,
        "engine_func_002b2690": CALL_ALLOC,
        "engine_func_002b25ac": CALL_REG,
        "engine_func_002c3b48": CALL_INIT,
        "engine_func_002c3a24": CALL_UNLOCK,
    }
    staged_compiled = stage_body(comp, relocs, 0x002C54F0, syms, "engine_func_002c54f0")

    stub_ret = struct.pack("<I", 0xe12fff1e) # bx lr
    RAW_BASE = 0x10090000

    test_cases = [
        # (arg0, arg1, arg2, size, priority)
        (0x20000, 1, 2, 0x100, 0x3F800000), # raw alloc branch 1
        (0x30000, 3, 4, 0x200, 0x40000000), # raw alloc branch 2
        (0x10000, 1, 2, 0x100, 0x3F800000), # aligned alloc branch
        (0, 0, 0, 0x500, 0),                 # aligned alloc branch 2
    ]

    for arg0, arg1, arg2, size, priority in test_cases:
        results = []
        raw_headers = []
        user_headers = []

        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002C54F0, code_bytes)

            for fn in (CALL_LOCK, CALL_ALLOC, CALL_REG, CALL_INIT, CALL_UNLOCK):
                uc.mem_write(fn, stub_ret)

            uc.mem_write(0x00465120 + 4, struct.pack("<I", 0x11223344))
            uc.mem_write(RAW_BASE, b"\x00" * 0x3000)

            def hook_alloc(uc, addr, size_val, ud):
                uc.reg_write(UC_ARM_REG_R0, RAW_BASE)
            uc.hook_add(1, hook_alloc, None, CALL_ALLOC, CALL_ALLOC + 4)

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.mem_write(sp, struct.pack("<I", priority))

            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)
            uc.reg_write(UC_ARM_REG_R0, arg0)
            uc.reg_write(UC_ARM_REG_R1, arg1)
            uc.reg_write(UC_ARM_REG_R2, arg2)
            uc.reg_write(UC_ARM_REG_R3, size)

            uc.emu_start(0x002C54F0, 0xF0000000, timeout=2000000)
            ret_user = uc.reg_read(UC_ARM_REG_R0)
            results.append(ret_user)

            if arg0 not in (0x20000, 0x30000):
                raw_headers.append(uc.mem_read(RAW_BASE, 8))
                user_headers.append(uc.mem_read(ret_user - 4, 4))
            else:
                raw_headers.append(b"")
                user_headers.append(b"")

        assert results[0] == results[1], f"engine_func_002c54f0 mismatch ret for case {(arg0, arg1, arg2, size, priority)}: {results[0]} != {results[1]}"
        assert raw_headers[0] == raw_headers[1], f"engine_func_002c54f0 mismatch raw_header"
        assert user_headers[0] == user_headers[1], f"engine_func_002c54f0 mismatch user_header"

    print("  engine_func_002c54f0: PASS (all cases match)")

# ---------------------------------------------------------------------------
# Test 4: ui_func_002e3d70 (0x002E3D70)
# ---------------------------------------------------------------------------
def test_002e3d70(out: Path):
    print("Testing ui_func_002e3d70 (0x002E3D70)...")
    comp, relocs = compile_function("ui_func_002e3d70", out)
    orig_bytes = load_original_bytes(0x002E3D70, 220)

    CALL_96F60 = 0x00296F60
    CALL_49BAC = 0x00249BAC
    CALL_49B54 = 0x00249B54
    CALL_93C98 = 0x00293C98
    CALL_49B0C = 0x00249B0C
    CALL_8DF54 = 0x0028DF54

    BASE_CTX = 0x10090000
    UNIT_TABLE = 0x100A0000

    syms = {
        "engine_func_00296f60": CALL_96F60,
        "ui_func_00249bac": CALL_49BAC,
        "func_00249b54": CALL_49B54,
        "ui_func_00293c98": CALL_93C98,
        "battle_func_00249b0c": CALL_49B0C,
        "battle_func_0028df54": CALL_8DF54,
    }
    staged_compiled = stage_body(comp, relocs, 0x002E3D70, syms, "ui_func_002e3d70")

    stub_ret = struct.pack("<I", 0xe12fff1e) # bx lr

    test_cases = [
        # (max_limit, start, count, extra_flag, extra_ret)
        (3, 0, 4, 0, 0), # units evaluated, active <= limit -> 1
        (1, 0, 4, 0, 0), # active > limit -> 0
        (2, 0, 2, 1, 1), # extra unit active
        (0, 0, 0, 0, 0), # empty range
    ]

    for max_lim, st_val, cnt_val, extra_flg, extra_ret in test_cases:
        results = []
        df54_calls = []

        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002E3D70, code_bytes)

            for fn in (CALL_96F60, CALL_49BAC, CALL_49B54, CALL_93C98, CALL_49B0C, CALL_8DF54):
                uc.mem_write(fn, stub_ret)

            def hook_96f60(uc, addr, size, ud):
                # Returns max_lim for 0
                r0 = uc.reg_read(UC_ARM_REG_R0)
                if r0 == 0:
                    uc.reg_write(UC_ARM_REG_R0, max_lim)
                else:
                    uc.reg_write(UC_ARM_REG_R0, 0)
            uc.hook_add(1, hook_96f60, None, CALL_96F60, CALL_96F60 + 4)

            def hook_49b54(uc, addr, size, ud):
                r1 = uc.reg_read(UC_ARM_REG_R1) # &start
                r2 = uc.reg_read(UC_ARM_REG_R2) # &count
                uc.mem_write(r1, struct.pack("<I", st_val))
                uc.mem_write(r2, struct.pack("<I", cnt_val))
            uc.hook_add(1, hook_49b54, None, CALL_49B54, CALL_49B54 + 4)

            def hook_93c98(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, BASE_CTX)
            uc.hook_add(1, hook_93c98, None, CALL_93C98, CALL_93C98 + 4)

            def hook_49b0c(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, extra_ret)
            uc.hook_add(1, hook_49b0c, None, CALL_49B0C, CALL_49B0C + 4)

            cur_df54 = []
            def hook_8df54(uc, addr, size, ud):
                cur_df54.append(uc.reg_read(UC_ARM_REG_R0))
            uc.hook_add(1, hook_8df54, None, CALL_8DF54, CALL_8DF54 + 4)

            # Setup BASE_CTX
            uc.mem_write(BASE_CTX + 0x1FC0, struct.pack("<I", UNIT_TABLE))
            uc.mem_write(BASE_CTX + 0x49C5, struct.pack("<B", extra_flg))

            # Populate UNIT_TABLE entries: stride 648
            # Unit 0: status = 1 (active)
            # Unit 1: status = 0x11 (has 0x10 -> inactive)
            # Unit 2: status = 1 (active)
            # Unit 3: status = 0x41 (has 0x40 -> inactive)
            statuses = [1, 0x11, 1, 0x41]
            for i, st in enumerate(statuses):
                uc.mem_write(UNIT_TABLE + i * 648, struct.pack("<I", st))

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)

            uc.emu_start(0x002E3D70, 0xF0000000, timeout=2000000)
            res = uc.reg_read(UC_ARM_REG_R0)
            results.append(res)
            df54_calls.append(cur_df54)

        assert results[0] == results[1], f"ui_func_002e3d70 mismatch ret: {results[0]} != {results[1]}"
        assert df54_calls[0] == df54_calls[1], f"ui_func_002e3d70 mismatch df54: {df54_calls[0]} != {df54_calls[1]}"

    print("  ui_func_002e3d70: PASS (all cases match)")

# ---------------------------------------------------------------------------
# Test 5: ui_func_002bf460 (0x002BF460)
# ---------------------------------------------------------------------------
def test_002bf460(out: Path):
    print("Testing ui_func_002bf460 (0x002BF460)...")
    comp, relocs = compile_function("ui_func_002bf460", out)
    orig_bytes = load_original_bytes(0x002BF460, 248)

    CALL_B0188 = 0x002B0188
    CALL_AF8D0 = 0x002AF8D0

    CTX_OBJ = 0x10090000
    GRID_TABLE = 0x100A0000
    NODE_ADDR = 0x100B0000

    syms = {
        "ui_func_002b0188": CALL_B0188,
        "ui_func_002af8d0": CALL_AF8D0,
    }
    staged_compiled = stage_body(comp, relocs, 0x002BF460, syms, "ui_func_002bf460")

    stub_ret = struct.pack("<I", 0xe12fff1e) # bx lr

    test_cases = [
        # (arg0, arg1, index, arg3, x_raw, y_raw, node_subtype, node_flag)
        (0x100, 0x200, 10, 0x300, 0x3F800000, 0x40000000, 0, 1), # subtype 0, flag & 1 -> arg0 | 0x8000
        (0x100, 0x200, 10, 0x300, 0x3F800000, 0x40000000, 0, 0), # subtype 0, flag 0
        (0x100, 0x200, 1010, 0x300, 0x40400000, 0x40800000, 1, 0), # subtype 1 -> dx, dy
        (0x100, 0x200, 500, 0x300, 0, 0, 2, 0), # subtype 2 -> no dx, dy
        (0x100, 0x200, 2000, 0x300, 0, 0, None, 0), # null node
    ]

    for arg0, arg1, index, arg3, x_raw, y_raw, sub_type, n_flag in test_cases:
        captured_descs = []

        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002BF460, code_bytes)
            uc.mem_write(CALL_B0188, stub_ret)
            uc.mem_write(CALL_AF8D0, stub_ret)

            def hook_b0188(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, CTX_OBJ)
            uc.hook_add(1, hook_b0188, None, CALL_B0188, CALL_B0188 + 4)

            # CTX_OBJ: [ctx + 4] -> pointer to table pointer
            TABLE_PTR_LOC = 0x10091000
            uc.mem_write(CTX_OBJ + 4, struct.pack("<I", TABLE_PTR_LOC))
            uc.mem_write(TABLE_PTR_LOC, struct.pack("<I", GRID_TABLE))

            # Entry in GRID_TABLE: (index % 1000) * 20
            slot_offset = (index % 1000) * 20
            if sub_type is not None:
                uc.mem_write(GRID_TABLE + slot_offset + 0xC, struct.pack("<I", NODE_ADDR))
                # NODE_ADDR: [0] dx = 15, [2] dy = 25, [4] subtype, [0xC] flag
                uc.mem_write(NODE_ADDR + 0, struct.pack("<h", 15))
                uc.mem_write(NODE_ADDR + 2, struct.pack("<h", 25))
                uc.mem_write(NODE_ADDR + 4, struct.pack("<h", sub_type))
                uc.mem_write(NODE_ADDR + 0xC, struct.pack("<B", n_flag))
            else:
                uc.mem_write(GRID_TABLE + slot_offset + 0xC, struct.pack("<I", 0))

            cur_desc = []
            def hook_af8d0(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0) # ctx
                r2 = uc.reg_read(UC_ARM_REG_R2) # desc on stack
                desc_bytes = uc.mem_read(r2, 0x30)
                cur_desc.append((r0, desc_bytes))
            uc.hook_add(1, hook_af8d0, None, CALL_AF8D0, CALL_AF8D0 + 4)

            sp = STACK_BASE + STACK_SIZE - 0x1000
            # Stack args: x_raw at sp[0], y_raw at sp[4]
            uc.mem_write(sp, struct.pack("<II", x_raw, y_raw))

            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)
            uc.reg_write(UC_ARM_REG_R0, arg0)
            uc.reg_write(UC_ARM_REG_R1, arg1)
            uc.reg_write(UC_ARM_REG_R2, index)
            uc.reg_write(UC_ARM_REG_R3, arg3)

            uc.emu_start(0x002BF460, 0xF0000000, timeout=2000000)
            captured_descs.append(cur_desc)

        assert captured_descs[0] == captured_descs[1], f"ui_func_002bf460 mismatch for case {(arg0, arg1, index, arg3, x_raw, y_raw, sub_type, n_flag)}: {captured_descs[0]} != {captured_descs[1]}"

    print("  ui_func_002bf460: PASS (all cases match)")


def main():
    print("Running Batch 32 C Part 7 differential tests...")
    out_dir = ROOT / "build"
    out_dir.mkdir(exist_ok=True)

    run_allocator_test("engine_func_002bf798", 0x002BF798, out_dir)
    run_allocator_test("engine_func_002c34a4", 0x002C34A4, out_dir)
    test_002c54f0(out_dir)
    test_002e3d70(out_dir)
    test_002bf460(out_dir)

    print("\nALL BATCH 32 C PART 7 TESTS PASSED!")

if __name__ == "__main__":
    main()
