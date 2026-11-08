#!/usr/bin/env python3
"""Differential test for batch 32 C part 4:
- camp_func_002ba9d8 (0x002BA9D8, 204 B)
- script_vm_func_002bd020 (0x002BD020, 224 B)
- func_002c01b8 (0x002C01B8, 212 B)
- battle_func_002cfbfc (0x002CFBFC, 100 B)
- battle_func_002e446c (0x002E446C, 200 B)
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

def test_002ba9d8(out: Path):
    print("Testing camp_func_002ba9d8 (0x002BA9D8)...")
    comp, relocs = compile_function("camp_func_002ba9d8", out)
    orig_bytes = load_original_bytes(0x002BA9D8, 204)

    GLOBAL_PTR_LOC = 0x00433158
    GLOBAL_PTR_VAL = 0x10001000
    HANDLE = 0x10002000
    PAYLOAD_ADDR = 0x10010000

    STUB_131548 = 0x00131548
    STUB_SUBTABLE = 0x002C0EC4
    STUB_PAYLOAD = 0x002C0E9C
    STUB_ROWCOUNT = 0x002C0E4C
    STUB_2C0BA8 = 0x002C0BA8

    syms = {
        "script_vm_func_00131548": STUB_131548,
        "Tbb_GetGlobalSubTable": STUB_SUBTABLE,
        "Tbb_GetPayloadData": STUB_PAYLOAD,
        "Tbb_GetRowCount": STUB_ROWCOUNT,
        "script_vm_func_002c0ba8": STUB_2C0BA8,
    }
    staged_compiled = stage_body(comp, relocs, 0x002BA9D8, syms, "camp_func_002ba9d8")

    # Cases: (ret_131548, count, val0, val1, cond1_ret, cond2_ret, rows)
    # rows: list of (b0, b1, cond1, cond2)
    cases = [
        (0x10009999, 0, 1, 2, 0, 0, []),  # fast path: 131548 returns non-zero
        (0, 0, 1, 2, 0, 0, []),           # count 0 -> returns payload
        (0, 3, 1, 2, 0, 0, [              # match at row 0 (cond1=0, cond2=0)
            (1, 2, 0, 0),
            (3, 4, 0, 0),
            (5, 6, 0, 0),
        ]),
        (0, 3, 3, 4, 1, 0, [              # match at row 1 (cond1=0x111 returns 1, cond2=0)
            (1, 2, 0, 0),
            (3, 4, 0x111, 0),
            (5, 6, 0, 0),
        ]),
        (0, 3, 3, 4, 0, 0, [              # row 1 cond1=0x111 returns 0 -> fails match -> returns payload
            (1, 2, 0, 0),
            (3, 4, 0x111, 0),
            (5, 6, 0, 0),
        ]),
        (0, 3, 3, 4, 1, 0, [              # match at row 1 (cond1=0, cond2=0x222 returns 0 -> match accepted!)
            (1, 2, 0, 0),
            (3, 4, 0, 0x222),
            (5, 6, 0, 0),
        ]),
        (0, 3, 3, 4, 1, 1, [              # row 1 cond1=0, cond2=0x222 returns 1 -> rejected!
            (1, 2, 0, 0),
            (3, 4, 0, 0x222),
            (5, 6, 0, 0),
        ]),
    ]

    for ret_131, count, v0, v1, c1_ret, c2_ret, rows in cases:
        stub_131_code = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", ret_131)
        stub_subtable_code = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", HANDLE)
        stub_payload_code = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", PAYLOAD_ADDR)
        stub_rowcount_code = struct.pack("<II", 0xe3a00000 | (count & 0xFF), 0xe12fff1e)

        # STUB_2C0BA8: check if r0 == 0x111 return c1_ret, if r0 == 0x222 return c2_ret
        stub_ba8_code = struct.pack("<IIIIIII",
            0xe3500c01,           # cmp r0, #0x100
            0x03a00000 | c1_ret,  # moveq r0, #c1_ret
            0x012fff1e,           # bxeq lr
            0xe3a00000 | c2_ret,  # mov r0, #c2_ret
            0xe12fff1e,           # bx lr
            0xe1a00000, 0xe1a00000
        )

        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002BA9D8, code_bytes)
            uc.mem_write(STUB_131548, stub_131_code)
            uc.mem_write(STUB_SUBTABLE, stub_subtable_code)
            uc.mem_write(STUB_PAYLOAD, stub_payload_code)
            uc.mem_write(STUB_ROWCOUNT, stub_rowcount_code)
            uc.mem_write(STUB_2C0BA8, stub_ba8_code)

            uc.mem_write(GLOBAL_PTR_LOC, struct.pack("<I", GLOBAL_PTR_VAL))

            payload_buf = bytearray(max(1, count) * 160)
            for i, (b0, b1, cond1, cond2) in enumerate(rows):
                off = i * 160
                payload_buf[off] = b0
                payload_buf[off + 1] = b1
                struct.pack_into("<H", payload_buf, off + 0x0A, cond1)
                struct.pack_into("<H", payload_buf, off + 0x0C, cond2)

            uc.mem_write(PAYLOAD_ADDR, bytes(payload_buf))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, v0)
            uc.reg_write(UC_ARM_REG_R1, v1)

            uc.emu_start(0x002BA9D8, 0x00100000, count=1000)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            results.append(r0)

        assert results[0] == results[1], f"Mismatch for case ({hex(ret_131)}, {count}, {v0}, {v1}): {hex(results[0])} != {hex(results[1])}"
    print("  camp_func_002ba9d8: PASS (all cases match)")

def test_002bd020(out: Path):
    print("Testing script_vm_func_002bd020 (0x002BD020)...")
    comp, relocs = compile_function("script_vm_func_002bd020", out)
    orig_bytes = load_original_bytes(0x002BD020, 224)

    GLOBAL_PTR_LOC = 0x00433158
    GLOBAL_PTR_VAL = 0x10001000
    HANDLE = 0x10002000
    PAYLOAD_ADDR = 0x10020000
    INFO_ADDR = 0x10005000

    STUB_CAMP_9364 = 0x002B9364
    STUB_VM_931C = 0x002B931C
    STUB_SUBTABLE = 0x002C0EC4
    STUB_PAYLOAD = 0x002C0E9C
    STUB_ROWCOUNT = 0x002C0E4C

    syms = {
        "camp_func_002b9364": STUB_CAMP_9364,
        "script_vm_func_002b931c": STUB_VM_931C,
        "Tbb_GetGlobalSubTable": STUB_SUBTABLE,
        "Tbb_GetPayloadData": STUB_PAYLOAD,
        "Tbb_GetRowCount": STUB_ROWCOUNT,
    }
    staged_compiled = stage_body(comp, relocs, 0x002BD020, syms, "script_vm_func_002bd020")

    # Cases: (has_info, slot, ret_931c, count, param1)
    cases = [
        (True, 3, 0x10008880, 5, 0),   # info != 0, 931c returns res -> returns res + 2
        (True, 2, 0, 5, 0),            # info != 0, 931c returns 0 -> returns payload + slot*40
        (True, 2, 0, 5, 1),            # info != 0, param1=1 -> returns payload + slot*40 + 0x10
        (True, 6, 0, 5, 0),            # info != 0, slot >= count -> returns payload
        (False, 0, 0x10007770, 3, 0),  # info == 0, 931c returns res -> returns res + 2
        (False, 0, 0, 3, 0),           # info == 0, count > 0, param1=0 -> returns payload
        (False, 0, 0, 3, 1),           # info == 0, count > 0, param1=1 -> returns payload + 0x10
        (False, 0, 0, 0, 1),           # info == 0, count == 0 -> returns payload
    ]

    for has_info, slot, ret_931c, count, p1 in cases:
        ret_9364 = INFO_ADDR if has_info else 0
        stub_9364_code = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", ret_9364)
        stub_931c_code = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", ret_931c)
        stub_subtable_code = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", HANDLE)
        stub_payload_code = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", PAYLOAD_ADDR)
        stub_rowcount_code = struct.pack("<II", 0xe3a00000 | (count & 0xFF), 0xe12fff1e)

        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002BD020, code_bytes)
            uc.mem_write(STUB_CAMP_9364, stub_9364_code)
            uc.mem_write(STUB_VM_931C, stub_931c_code)
            uc.mem_write(STUB_SUBTABLE, stub_subtable_code)
            uc.mem_write(STUB_PAYLOAD, stub_payload_code)
            uc.mem_write(STUB_ROWCOUNT, stub_rowcount_code)

            uc.mem_write(GLOBAL_PTR_LOC, struct.pack("<I", GLOBAL_PTR_VAL))

            if has_info:
                info_data = bytearray(16)
                info_data[2] = slot
                uc.mem_write(INFO_ADDR, bytes(info_data))

            uc.mem_write(PAYLOAD_ADDR, b'\x00' * (max(1, count, slot + 1) * 40 + 0x20))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, 0x1234)
            uc.reg_write(UC_ARM_REG_R1, p1)

            uc.emu_start(0x002BD020, 0x00100000, count=500)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            results.append(r0)

        assert results[0] == results[1], f"Mismatch for case ({has_info}, {slot}, {hex(ret_931c)}, {count}, {p1}): {hex(results[0])} != {hex(results[1])}"
    print("  script_vm_func_002bd020: PASS (all cases match)")

def test_002c01b8(out: Path):
    print("Testing func_002c01b8 (0x002C01B8)...")
    comp, relocs = compile_function("func_002c01b8", out)
    orig_bytes = load_original_bytes(0x002C01B8, 212)

    STRUCT_ADDR = 0x004E3CD4
    OUT0_ADDR = 0x10004000
    OUT1_ADDR = 0x10004004

    staged_compiled = stage_body(comp, relocs, 0x002C01B8, {}, "func_002c01b8")

    # (mode, f10, f11, f12, use_out0, use_out1)
    cases = [
        # mode 0: f10 == 1
        (0, 1, 0, 0, True, True),
        (0, 0, 0, 0, True, True),
        (0, 1, 0, 0, False, True),
        (0, 1, 0, 0, True, False),
        # mode 1: f10 == 1 && f11 == 0
        (1, 1, 0, 0, True, True),
        (1, 1, 1, 0, True, True),
        (1, 0, 0, 0, True, True),
        # mode 2: f10 == 1 && f12 == 1
        (2, 1, 0, 1, True, True),
        (2, 1, 0, 0, True, True),
        (2, 0, 0, 1, True, True),
        # mode 3: f10 == 0 && f11 == 1
        (3, 0, 1, 0, True, True),
        (3, 1, 1, 0, True, True),
        (3, 0, 0, 0, True, True),
        # invalid mode 4
        (4, 1, 0, 0, True, True),
    ]

    for mode, f10, f11, f12, use_o0, use_o1 in cases:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002C01B8, code_bytes)

            struct_data = bytearray(0x20)
            struct.pack_into("<H", struct_data, 0, 0x1234)
            struct.pack_into("<H", struct_data, 2, 0x5678)
            struct_data[0x10] = f10
            struct_data[0x11] = f11
            struct_data[0x12] = f12
            uc.mem_write(STRUCT_ADDR, bytes(struct_data))

            uc.mem_write(OUT0_ADDR, struct.pack("<I", 0))
            uc.mem_write(OUT1_ADDR, struct.pack("<I", 0))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, OUT0_ADDR if use_o0 else 0)
            uc.reg_write(UC_ARM_REG_R1, OUT1_ADDR if use_o1 else 0)
            uc.reg_write(UC_ARM_REG_R2, mode)

            uc.emu_start(0x002C01B8, 0x00100000, count=100)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            o0 = struct.unpack("<I", uc.mem_read(OUT0_ADDR, 4))[0]
            o1 = struct.unpack("<I", uc.mem_read(OUT1_ADDR, 4))[0]
            results.append((r0, o0, o1))

        assert results[0] == results[1], f"Mismatch for case ({mode}, {f10}, {f11}, {f12}, {use_o0}, {use_o1}): {results[0]} != {results[1]}"
    print("  func_002c01b8: PASS (all cases match)")

def test_002cfbfc(out: Path):
    print("Testing battle_func_002cfbfc (0x002CFBFC)...")
    comp, relocs = compile_function("battle_func_002cfbfc", out)
    orig_bytes = load_original_bytes(0x002CFBFC, 100)

    STUB_282A90 = 0x00282A90
    STUB_24BB80 = 0x0024BB80
    STUB_24BB18 = 0x0024BB18

    GLOBAL_PTR_LOC = 0x00439B58
    GLOBAL_OBJ_LOC = 0x10008000
    TARGET_OBJ = 0x10009000

    syms = {
        "battle_func_00282a90": STUB_282A90,
        "ui_func_0024bb80": STUB_24BB80,
        "ui_func_0024bb18": STUB_24BB18,
    }
    staged_compiled = stage_body(comp, relocs, 0x002CFBFC, syms, "battle_func_002cfbfc")

    # Test Entry 1: battle_func_002cfbfc (0x002CFBFC)
    stub_282a90_code = struct.pack("<II", 0xe3a00000, 0xe12fff1e)
    results = []
    for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
        uc = create_emulator()
        uc.mem_write(0x002CFBFC, code_bytes)
        uc.mem_write(STUB_282A90, stub_282a90_code)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00100000)

        uc.emu_start(0x002CFBFC, 0x00100000, count=100)
        r0 = uc.reg_read(UC_ARM_REG_R0)
        results.append(r0)
    assert results[0] == results[1] == 1, f"Entry 1 mismatch: {results[0]} != {results[1]}"

    # Test Entry 2: battle_func_002cfc38 (0x002CFC38)
    comp_c38, relocs_c38 = compile_function("battle_func_002cfc38", out)
    staged_c38 = stage_body(comp_c38, relocs_c38, 0x002CFC38, syms, "battle_func_002cfc38")

    stub_bb80_code = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", 0x1000ABCD)
    # stub_bb18: returns r0 + r1
    stub_bb18_code = struct.pack("<II", 0xe0800001, 0xe12fff1e)

    for ret_val in [10, 20]:
        results = []
        for is_comp, (entry, code_bytes) in enumerate([(0x002CFC38, orig_bytes[0x3C:0x3C+40]), (0x002CFC38, staged_c38)]):
            uc = create_emulator()
            uc.mem_write(0x002CFC38, code_bytes)
            uc.mem_write(STUB_24BB80, stub_bb80_code)
            uc.mem_write(STUB_24BB18, stub_bb18_code)

            # Setup global ptr
            uc.mem_write(GLOBAL_PTR_LOC, struct.pack("<I", GLOBAL_OBJ_LOC))
            # GLOBAL_OBJ_LOC[0x14] = TARGET_OBJ
            obj_data = bytearray(0x20)
            struct.pack_into("<I", obj_data, 0x14, TARGET_OBJ)
            uc.mem_write(GLOBAL_OBJ_LOC, bytes(obj_data))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)

            uc.emu_start(0x002CFC38, 0x00100000, count=100)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            results.append(r0)
        assert results[0] == results[1], f"Entry 2 mismatch: {results[0]} != {results[1]}"

    print("  battle_func_002cfbfc: PASS (all cases match)")

def test_002e446c(out: Path):
    print("Testing battle_func_002e446c (0x002E446C)...")
    comp, relocs = compile_function("battle_func_002e446c", out)
    orig_bytes = load_original_bytes(0x002E446C, 200)

    STUB_249A44 = 0x00249A44
    STUB_2AE464 = 0x002AE464
    STUB_24C740 = 0x0024C740
    STUB_2AE3F0 = 0x002AE3F0
    STUB_25779C = 0x0025779C

    ENT_A = 0x10005000
    ENT_B = 0x10005100
    INFO_A = 0x10006000
    INFO_B = 0x10006100
    PARAM_A = 0x10007000
    PARAM_B = 0x10007004

    syms = {
        "camp_func_00249a44": STUB_249A44,
        "battle_func_002ae464": STUB_2AE464,
        "func_0024c740": STUB_24C740,
        "battle_func_002ae3f0": STUB_2AE3F0,
        "battle_func_0025779c": STUB_25779C,
    }
    staged_compiled = stage_body(comp, relocs, 0x002E446C, syms, "battle_func_002e446c")

    # (is_dead_a, is_dead_b, prio_a, prio_b, sub_a, sub_b, ret_25779c)
    cases = [
        (True, False, 0, 50, 0, 0, 0),    # A dead (prio 99), B prio 50 -> diff = 49
        (False, False, 20, 80, 0, 0, 0),  # diff in prio = -60
        (False, False, 50, 50, 10, 30, 0),# same prio, sub_b - sub_a = 20
        (False, False, 50, 50, 40, 15, 0),# same prio, sub_b - sub_a = -25
        (False, False, 50, 50, 20, 20, 77),# same prio and sub -> dispatches 25779c
    ]

    stub_9a44_code = struct.pack("<IIIII",
        0xe3500001,  # cmp r0, #1
        0x059f0004,  # ldreq r0, [pc, #4]
        0x159f0004,  # ldrne r0, [pc, #4]
        0xe12fff1e,  # bx lr
        ENT_A,
    ) + struct.pack("<I", ENT_B)

    stub_e3f0_code = struct.pack("<IIIII",
        0xe3500001,  # cmp r0, #1
        0x059f0004,  # ldreq r0, [pc, #4]
        0x159f0004,  # ldrne r0, [pc, #4]
        0xe12fff1e,  # bx lr
        INFO_A,
    ) + struct.pack("<I", INFO_B)

    for is_dead_a, is_dead_b, p_a, p_b, s_a, s_b, ret_79c in cases:
        stub_e464_code = struct.pack("<IIII",
            0xe3500001,
            0x03a00000 | (1 if is_dead_a else 0),
            0x13a00000 | (1 if is_dead_b else 0),
            0xe12fff1e,
        )
        stub_c740_code = struct.pack("<IIII",
            0xe3500001,
            0x03a00000 | (p_a & 0xFF),
            0x13a00000 | (p_b & 0xFF),
            0xe12fff1e,
        )
        stub_779c_code = struct.pack("<II", 0xe3a00000 | (ret_79c & 0xFF), 0xe12fff1e)

        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002E446C, code_bytes)
            uc.mem_write(STUB_249A44, stub_9a44_code)
            uc.mem_write(STUB_2AE464, stub_e464_code)
            uc.mem_write(STUB_24C740, stub_c740_code)
            uc.mem_write(STUB_2AE3F0, stub_e3f0_code)
            uc.mem_write(STUB_25779C, stub_779c_code)

            # ENT_A[0x26] = 1, ENT_B[0x26] = 2
            ent_a_buf = bytearray(0x30)
            ent_b_buf = bytearray(0x30)
            struct.pack_into("<H", ent_a_buf, 0x26, 1)
            struct.pack_into("<H", ent_b_buf, 0x26, 2)
            uc.mem_write(ENT_A, bytes(ent_a_buf))
            uc.mem_write(ENT_B, bytes(ent_b_buf))

            # INFO_A[0x2C] = s_a, INFO_B[0x2C] = s_b
            info_a_buf = bytearray(0x30)
            info_b_buf = bytearray(0x30)
            struct.pack_into("<H", info_a_buf, 0x2C, s_a)
            struct.pack_into("<H", info_b_buf, 0x2C, s_b)
            uc.mem_write(INFO_A, bytes(info_a_buf))
            uc.mem_write(INFO_B, bytes(info_b_buf))

            uc.mem_write(PARAM_A, struct.pack("<H", 1))
            uc.mem_write(PARAM_B, struct.pack("<H", 2))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, PARAM_A)
            uc.reg_write(UC_ARM_REG_R1, PARAM_B)

            uc.emu_start(0x002E446C, 0x00100000, count=500)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            if r0 >= 0x80000000:
                r0 -= 0x100000000
            results.append(r0)

        assert results[0] == results[1], f"Mismatch for case ({is_dead_a}, {is_dead_b}, {p_a}, {p_b}, {s_a}, {s_b}): {results[0]} != {results[1]}"

    print("  battle_func_002e446c: PASS (all cases match)")

def main():
    out = ROOT / "build"
    out.mkdir(exist_ok=True)
    print("Running Batch 32 C Part 4 differential tests...")
    test_002ba9d8(out)
    test_002bd020(out)
    test_002c01b8(out)
    test_002cfbfc(out)
    test_002e446c(out)
    print("\nALL BATCH 32 C PART 4 TESTS PASSED!")

if __name__ == "__main__":
    main()
