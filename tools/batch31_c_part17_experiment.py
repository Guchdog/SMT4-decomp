#!/usr/bin/env python3
"""Differential test for batch 31 C part 17:
- engine_func_002c31e8 (0x002C31E8, 168 B)
- camp_func_002c6e04 (0x002C6E04, 172 B) [includes camp_func_002c6e7c]
- script_vm_func_002ca6f4 (0x002CA6F4, 180 B)
- func_002d29f4 (0x002D29F4, 160 B)
- script_vm_func_002d4dac (0x002D4DAC, 156 B)
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
SOURCE = ROOT / "src/engine/leaf_batch31_c.cpp"

with open(ORIG_BIN, "rb") as f:
    ORIG_DATA = f.read()

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

RODATA_ADDR = 0x10050000
RODATA_BYTES = b""

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
            # Check if inst is an offset into .rodata
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
# Function 1: engine_func_002c31e8 (0x002C31E8, 168 B)
# -----------------------------------------------------------------------------
def test_engine_func_002c31e8():
    addr = 0x002C31E8
    size = 168
    print(f"--- Testing engine_func_002c31e8 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part17"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_002c31e8", tmp)

    # 002c31e8 calls func_002aa7f4 (strcmp)
    # In original binary, 0x002AA7F4 is in code.bin.
    sym_map = {
        "func_002aa7f4": 0x002AA7F4,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "engine_func_002c31e8")

    # Construct test Patricia tree at TREE_ADDR = 0x10020000
    # Header:
    # 0x00: dummy
    # 0x04: dummy
    # 0x08: dummy
    # 0x0C: node 0 bit_index (u32)
    # 0x10: node 0 left_idx / root_idx (u16)
    # 0x12: node 0 right_idx (u16)
    # 0x14: node 0 str_offset (s32)
    # Nodes are 16 bytes each.
    TREE_BASE = 0x10020000
    KEY_ADDR = 0x10030000
    ROOT_PTR = 0x10040000

    # Let's create a 3-node tree:
    # Node 0 (root): bit_index = 10, left = 1, right = 2, str_offset = 0
    # Node 1 (left leaf): bit_index = 4 (descends from 10: 10 > 4), left = 1, right = 1
    # Node 2 (right leaf): bit_index = 2 (descends from 10: 10 > 2), left = 2, right = 2
    # String for node 1: "alpha\0"
    # String for node 2: "beta\0"
    # When bit at index 4 is tested...
    # Let's set up the tree carefully:
    tree_data = bytearray(0x200)
    # Node 0: offset 0xC
    # bit_index = 20
    struct.pack_into("<IHHi", tree_data, 0xC, 20, 1, 2, 0)
    # Node 1: offset 0x1C (16 bytes after 0xC)
    # bit_index = 10 (20 > 10, then loop: prev_bit = 20, bit_index = 10 -> tests bit 10 of key (byte 1, bit 2))
    # if bit == 0 -> left=1 (10 <= 10 -> terminates at node 1)
    # if bit == 1 -> right=2 (10 <= 2? 10 > 2 -> goes to node 2)
    # Node 1 str_offset: relative to (node1_addr + 8) = (TREE_BASE + 0x1C + 8) = TREE_BASE + 0x24
    # Let string be at TREE_BASE + 0x60 -> offset = 0x60 - 0x24 = 0x3C
    struct.pack_into("<IHHi", tree_data, 0x1C, 10, 1, 2, 0x3C)
    # Node 2: offset 0x2C
    # bit_index = 2 (prev 10 > 2, tests bit 2 of key (byte 0, bit 2), left=2, right=2 -> 2 <= 2 terminates)
    # str_offset: relative to (TREE_BASE + 0x2C + 8) = TREE_BASE + 0x34
    # String at TREE_BASE + 0x70 -> offset = 0x70 - 0x34 = 0x3C
    struct.pack_into("<IHHi", tree_data, 0x2C, 2, 2, 2, 0x3C)

    # Strings:
    tree_data[0x60:0x66] = b"alpha\x00"
    tree_data[0x70:0x75] = b"beta\x00"

    test_keys = [
        (b"alpha\x00", 6),
        (b"beta\x00", 5),
        (b"gamma\x00", 6),
        (b"a\x00", 2),
        (b"\x00", 1),
    ]

    def run_one(code, key_bytes, key_len):
        uc = create_emulator()
        uc.mem_write(TREE_BASE, bytes(tree_data))
        uc.mem_write(KEY_ADDR, key_bytes)
        uc.mem_write(ROOT_PTR, struct.pack("<I", TREE_BASE))

        target = addr
        uc.mem_write(target, code)
        ret_addr = 0x00100004
        uc.mem_write(ret_addr, b"\x00\x00\x00\x00")

        uc.reg_write(UC_ARM_REG_R0, ROOT_PTR)
        uc.reg_write(UC_ARM_REG_R1, KEY_ADDR)
        uc.reg_write(UC_ARM_REG_R2, key_len)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, ret_addr)
        uc.reg_write(UC_ARM_REG_PC, target)

        uc.emu_start(target, ret_addr, timeout=2000000)
        return uc.reg_read(UC_ARM_REG_R0)

    for k_bytes, k_len in test_keys:
        r_orig = run_one(orig_code, k_bytes, k_len)
        r_decomp = run_one(decomp_code, k_bytes, k_len)
        print(f"  key={k_bytes!r}: orig={hex(r_orig)} decomp={hex(r_decomp)}")
        assert r_orig == r_decomp, f"Mismatch for key {k_bytes}: {hex(r_orig)} != {hex(r_decomp)}"

    # Also test empty tree / null tree_ref
    def run_null():
        uc = create_emulator()
        uc.mem_write(ROOT_PTR, struct.pack("<I", 0))
        target = addr
        uc.mem_write(target, decomp_code)
        ret_addr = 0x00100004
        uc.reg_write(UC_ARM_REG_R0, ROOT_PTR)
        uc.reg_write(UC_ARM_REG_R1, KEY_ADDR)
        uc.reg_write(UC_ARM_REG_R2, 0)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, ret_addr)
        uc.reg_write(UC_ARM_REG_PC, target)
        uc.emu_start(target, ret_addr, timeout=2000000)
        assert uc.reg_read(UC_ARM_REG_R0) == 0

    run_null()
    print("engine_func_002c31e8: PASS")

# -----------------------------------------------------------------------------
# Function 2: camp_func_002c6e04 (0x002C6E04, 172 B)
# -----------------------------------------------------------------------------
def test_camp_func_002c6e04():
    addr = 0x002C6E04
    size = 172
    print(f"--- Testing camp_func_002c6e04 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part17"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_002c6e04", tmp)

    STUB_002B9364 = 0x002B9364

    sym_map = {
        "func_002b9364": STUB_002B9364,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "camp_func_002c6e04")

    # Mock table for func_002b9364(id):
    # Returns pointer to 4-byte record: {u16 id, u8 byte2, u8 byte3}
    TABLE_ADDR = 0x10020000
    mock_items = {
        10: struct.pack("<HBB", 10, 5, 20),
        20: struct.pack("<HBB", 20, 5, 20),
        30: struct.pack("<HBB", 30, 8, 20),
        40: struct.pack("<HBB", 40, 5, 50),
        50: struct.pack("<HBB", 50, 1, 10),
    }

    cases = [
        (10, 20), # same byte3 (20==20), same byte2 (5==5) -> 20 - 10 = 10
        (20, 10), # same byte3, same byte2 -> 10 - 20 = -10
        (10, 30), # same byte3 (20==20), diff byte2 (8 - 5 = 3)
        (30, 10), # same byte3, diff byte2 (5 - 8 = -3)
        (10, 40), # diff byte3 (50 - 20 = 30)
        (40, 10), # diff byte3 (20 - 50 = -30)
        (10, 50), # diff byte3 (10 - 20 = -10)
    ]

    PTR_A = 0x10030000
    PTR_B = 0x10030004

    def run_one(code, id_a, id_b):
        uc = create_emulator()
        # Setup mock items in memory
        for item_id, item_bytes in mock_items.items():
            uc.mem_write(TABLE_ADDR + item_id * 8, item_bytes)

        # Write stub at STUB_002B9364:
        # ldr r1, =TABLE_ADDR; add r0, r1, r0, lsl #3; bx lr
        stub = bytearray()
        stub += struct.pack("<I", 0xe59f1004) # ldr r1, [pc, #4]
        stub += struct.pack("<I", 0xe0810180) # add r0, r1, r0, lsl #3
        stub += struct.pack("<I", 0xe12fff1e) # bx lr
        stub += struct.pack("<I", TABLE_ADDR)
        uc.mem_write(STUB_002B9364, bytes(stub))

        # Write a and b
        uc.mem_write(PTR_A, struct.pack("<H", id_a))
        uc.mem_write(PTR_B, struct.pack("<H", id_b))

        target = addr
        uc.mem_write(target, code)
        ret_addr = 0x00100004
        uc.mem_write(ret_addr, b"\x00\x00\x00\x00")

        uc.reg_write(UC_ARM_REG_R0, PTR_A)
        uc.reg_write(UC_ARM_REG_R1, PTR_B)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, ret_addr)
        uc.reg_write(UC_ARM_REG_PC, target)

        uc.emu_start(target, ret_addr, timeout=2000000)
        ret = uc.reg_read(UC_ARM_REG_R0)
        if ret >= 0x80000000:
            ret -= 0x100000000
        return ret

    for id_a, id_b in cases:
        r_orig = run_one(orig_code, id_a, id_b)
        r_decomp = run_one(decomp_code, id_a, id_b)
        print(f"  compare({id_a}, {id_b}): orig={r_orig} decomp={r_decomp}")
        assert r_orig == r_decomp, f"Mismatch for ({id_a}, {id_b}): {r_orig} != {r_decomp}"

    # Also test camp_func_002c6e7c (the second entry point at offset 0x78 = 120 bytes)
    comp_7c, relocs_7c = compile_function("camp_func_002c6e7c", tmp)
    decomp_code_7c = stage_body(comp_7c, relocs_7c, addr + 0x78, {}, "camp_func_002c6e7c")

    def run_7c(code, id_a, id_b, entry_addr):
        uc = create_emulator()
        uc.mem_write(PTR_A, struct.pack("<H", id_a))
        uc.mem_write(PTR_B, struct.pack("<H", id_b))
        target = entry_addr
        uc.mem_write(target, code)
        ret_addr = 0x00100004
        uc.reg_write(UC_ARM_REG_R0, PTR_A)
        uc.reg_write(UC_ARM_REG_R1, PTR_B)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, ret_addr)
        uc.reg_write(UC_ARM_REG_PC, target)
        uc.emu_start(target, ret_addr, timeout=2000000)
        ret = uc.reg_read(UC_ARM_REG_R0)
        if ret >= 0x80000000:
            ret -= 0x100000000
        return ret

    cases_7c = [
        (10, 0),   # -1
        (0, 10),   # 1
        (0, 0),    # 0
        (50, 20),  # 30
        (20, 50),  # -30
        (10, 10),  # 0
    ]
    orig_code_7c = orig_code[0x78:]
    for id_a, id_b in cases_7c:
        r_orig = run_7c(orig_code_7c, id_a, id_b, addr + 0x78)
        r_decomp = run_7c(decomp_code_7c, id_a, id_b, addr + 0x78)
        print(f"  compare_7c({id_a}, {id_b}): orig={r_orig} decomp={r_decomp}")
        assert r_orig == r_decomp, f"Mismatch 7c for ({id_a}, {id_b}): {r_orig} != {r_decomp}"

    print("camp_func_002c6e04: PASS")

# -----------------------------------------------------------------------------
# Function 3: script_vm_func_002ca6f4 (0x002CA6F4, 180 B)
# -----------------------------------------------------------------------------
def test_script_vm_func_002ca6f4():
    addr = 0x002CA6F4
    size = 180
    print(f"--- Testing script_vm_func_002ca6f4 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part17"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_002ca6f4", tmp)

    # Use original addresses in code.bin for stubs so relocations stay in range:
    sym_map = {
        "func_002a497c": 0x002A497C,
        "func_003100c8": 0x003100C8,
        "func_00152af8": 0x00152AF8,
        "func_002a7aa0": 0x002A7AA0,
        "func_002a7604": 0x002A7604,
        "func_0029c56c": 0x0029C56C,
        "func_002637b4": 0x002637B4,
        "func_002a5058": 0x002A5058,
        "func_00275e58": 0x00275E58,
        "func_00291a5c": 0x00291A5C,
        "engine_func_002c4360": 0x002C4360,
    }

    decomp_code = stage_body(comp, relocs, addr, sym_map, "script_vm_func_002ca6f4")

    MGR_PTR_GLOBAL = 0x0044E300
    MGR_ADDR = 0x10020000

    def make_stub():
        # bx lr
        return b"\x1e\xff\x2f\xe1"

    cases = [
        # (field_85, field_8c, field_90, field_88)
        (0, 0x10050000, 0x10060000, 0x10070000),
        (1, 0x10050000, 0x10060000, 0x10070000),
        (0, 0, 0, 0),
        (2, 0x12345678, 0, 0x87654320),
    ]

    def run_one(code, field_85, field_8c, field_90, field_88):
        uc = create_emulator()

        # Write stubs
        for s_addr in sym_map.values():
            uc.mem_write(s_addr, make_stub())

        # Write manager object
        mgr_data = bytearray(0x100)
        mgr_data[0x85] = field_85
        struct.pack_into("<I", mgr_data, 0x8C, field_8c)
        struct.pack_into("<I", mgr_data, 0x90, field_90)
        struct.pack_into("<I", mgr_data, 0x88, field_88)
        uc.mem_write(MGR_ADDR, bytes(mgr_data))

        # Global ptr
        uc.mem_write(MGR_PTR_GLOBAL, struct.pack("<I", MGR_ADDR))

        target = addr
        uc.mem_write(target, code)
        ret_addr = 0x00100004
        uc.mem_write(ret_addr, b"\x00\x00\x00\x00")

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, ret_addr)
        uc.reg_write(UC_ARM_REG_PC, target)

        uc.emu_start(target, ret_addr, timeout=2000000)

        # Read back manager object and global ptr
        mgr_res = uc.mem_read(MGR_ADDR, 0x100)
        global_res = struct.unpack("<I", uc.mem_read(MGR_PTR_GLOBAL, 4))[0]
        return bytes(mgr_res), global_res

    for c in cases:
        orig_mgr, orig_g = run_one(orig_code, *c)
        decomp_mgr, decomp_g = run_one(decomp_code, *c)
        assert orig_mgr == decomp_mgr, f"Mgr state mismatch for {c}"
        assert orig_g == decomp_g, f"Global ptr mismatch for {c}: {hex(orig_g)} != {hex(decomp_g)}"
        # Verify specific expected mutations
        assert decomp_mgr[4] == 1, "mgr[4] was not set to 1"
        assert struct.unpack("<I", decomp_mgr[0x8C:0x90])[0] == 0, "mgr[0x8C] not cleared"
        assert struct.unpack("<I", decomp_mgr[0x90:0x94])[0] == 0, "mgr[0x90] not cleared"
        assert struct.unpack("<I", decomp_mgr[0x88:0x8C])[0] == 0, "mgr[0x88] not cleared"
        assert decomp_g == 0, "global ptr not cleared"

    print("script_vm_func_002ca6f4: PASS")

# -----------------------------------------------------------------------------
# Function 4: func_002d29f4 (0x002D29F4, 160 B)
# -----------------------------------------------------------------------------
def test_func_002d29f4():
    addr = 0x002D29F4
    size = 160
    print(f"--- Testing func_002d29f4 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part17"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_002d29f4", tmp)

    sym_map = {}
    decomp_code = stage_body(comp, relocs, addr, sym_map, "func_002d29f4")

    TABLE_BASE = 0x10020000
    TABLE_PTR_GLOBAL = 0x00447600

    def run_one(code, slot_configs):
        uc = create_emulator()
        # Allocate 32 * 0x180 = 0x3000 + 0x100 = 0x3100
        table_data = bytearray(0x3100)
        # Pre-populate slot_configs: list of (slot_idx, active, field_1a8, field_b1, val_b8)
        for idx, active, f1a8, fb1, vb8 in slot_configs:
            off = idx * 0x180
            table_data[off + 0x34] = active
            struct.pack_into("<I", table_data, off + 0x1A8, f1a8)
            table_data[off + 0xB1] = fb1
            struct.pack_into("<II", table_data, off + 0xB8, vb8, 0x11111111)

        # Set 0x3044 to non-zero
        struct.pack_into("<I", table_data, 0x3044, 0xABCDEF01)

        uc.mem_write(TABLE_BASE, bytes(table_data))
        uc.mem_write(TABLE_PTR_GLOBAL, struct.pack("<I", TABLE_BASE))

        target = addr
        uc.mem_write(target, code)
        ret_addr = 0x00100004
        uc.mem_write(ret_addr, b"\x00\x00\x00\x00")

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, ret_addr)
        uc.reg_write(UC_ARM_REG_PC, target)

        uc.emu_start(target, ret_addr, timeout=2000000)
        return bytes(uc.mem_read(TABLE_BASE, 0x3100))

    configs = [
        # (idx, active, f1a8, fb1, vb8)
        (0, 1, 5, 0, 0),   # active, valid f1a8, fb1==0, val==0 -> should become {0x14, 0}
        (1, 1, 5, 0, 2),   # val==2 -> should become {0x16, 0}
        (2, 1, 5, 0, 4),   # val==4 -> should become {0x14, 0}
        (3, 1, 5, 0, 5),   # val==5 -> should become {0x14, 0}
        (4, 1, 5, 0, 1),   # val==1 -> unchanged
        (5, 0, 5, 0, 0),   # inactive -> unchanged
        (6, 1, 0, 0, 0),   # f1a8==0 -> unchanged
        (7, 1, 11, 0, 0),  # f1a8==11 -> unchanged
        (8, 1, 5, 1, 0),   # fb1!=0 -> unchanged
        (31, 1, 10, 0, 2), # slot 31 boundary -> becomes {0x16, 0}
    ]

    r_orig = run_one(orig_code, configs)
    r_decomp = run_one(decomp_code, configs)
    assert r_orig == r_decomp, "Table buffer mismatch between orig and decomp"

    # Verify specific outcomes
    assert struct.unpack("<I", r_decomp[0x3044:0x3048])[0] == 0, "0x3044 not cleared"
    assert struct.unpack("<II", r_decomp[0xB8:0xC0]) == (0x14, 0), "Slot 0 not 0x14, 0"
    assert struct.unpack("<II", r_decomp[0x180 + 0xB8 : 0x180 + 0xC0]) == (0x16, 0), "Slot 1 not 0x16, 0"
    assert struct.unpack("<II", r_decomp[2 * 0x180 + 0xB8 : 2 * 0x180 + 0xC0]) == (0x14, 0), "Slot 2 not 0x14, 0"
    assert struct.unpack("<II", r_decomp[3 * 0x180 + 0xB8 : 3 * 0x180 + 0xC0]) == (0x14, 0), "Slot 3 not 0x14, 0"
    assert struct.unpack("<II", r_decomp[4 * 0x180 + 0xB8 : 4 * 0x180 + 0xC0]) == (1, 0x11111111), "Slot 4 modified unexpectedly"
    print("func_002d29f4: PASS")

# -----------------------------------------------------------------------------
# Function 5: script_vm_func_002d4dac (0x002D4DAC, 156 B)
# -----------------------------------------------------------------------------
def test_script_vm_func_002d4dac():
    addr = 0x002D4DAC
    size = 156
    print(f"--- Testing script_vm_func_002d4dac ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part17"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_002d4dac", tmp)

    STUB_27DA20 = 0x0027DA20
    STUB_27D9B8 = 0x0027D9B8

    sym_map = {
        "func_0027da20": STUB_27DA20,
        "func_0027d9b8": STUB_27D9B8,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "script_vm_func_002d4dac")

    TARGET_A_GLOBAL = 0x00447E88
    TARGET_B_GLOBAL = 0x004474F4
    TARGET_A = 0x10020000
    TARGET_B = 0x10030000
    SRC_OBJ = 0x10040000

    cases = [
        # (x, y, z, w) as s16
        (0, 0, 0, 0),
        (10, 20, 30, 40),
        (-100, 250, -32000, 15),
        (32767, -32768, 1, -1),
    ]

    def run_one(code, x, y, z, w):
        uc = create_emulator()

        # Write stubs:
        # STUB_27DA20: bx lr
        uc.mem_write(STUB_27DA20, b"\x1e\xff\x2f\xe1")
        # STUB_27D9B8: ldr r0, =SRC_OBJ; bx lr
        stub_b = bytearray()
        stub_b += struct.pack("<I", 0xe59f0000) # ldr r0, [pc]
        stub_b += struct.pack("<I", 0xe12fff1e) # bx lr
        stub_b += struct.pack("<I", SRC_OBJ)
        uc.mem_write(STUB_27D9B8, bytes(stub_b))

        # Write src object:
        # offset 4: x, offset 6: y, offset 8: z, offset 10: w
        src_data = bytearray(0x20)
        struct.pack_into("<hhhh", src_data, 4, x, y, z, w)
        uc.mem_write(SRC_OBJ, bytes(src_data))

        # Init targets
        uc.mem_write(TARGET_A, b"\x00" * 0x100)
        uc.mem_write(TARGET_B, b"\x00" * 0x100)
        uc.mem_write(TARGET_A_GLOBAL, struct.pack("<I", TARGET_A))
        uc.mem_write(TARGET_B_GLOBAL, struct.pack("<I", TARGET_B))

        target = addr
        uc.mem_write(target, code)
        ret_addr = 0x00100004
        uc.mem_write(ret_addr, b"\x00\x00\x00\x00")

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, ret_addr)
        uc.reg_write(UC_ARM_REG_PC, target)

        uc.emu_start(target, ret_addr, timeout=2000000)

        buf_a = uc.mem_read(TARGET_A, 0x60)
        buf_b = uc.mem_read(TARGET_B, 0x20)
        return bytes(buf_a), bytes(buf_b)

    for c in cases:
        orig_a, orig_b = run_one(orig_code, *c)
        decomp_a, decomp_b = run_one(decomp_code, *c)
        assert orig_a == decomp_a, f"Target A mismatch for {c}"
        assert orig_b == decomp_b, f"Target B mismatch for {c}"
        # Also check values directly
        fx, fy, fz, fw = float(c[0]), float(c[1]), float(c[2]), float(c[3])
        assert struct.unpack_from("<fff", decomp_a, 0x1C) == (fx, fy, fz)
        assert struct.unpack_from("<fff", decomp_a, 0x28) == (fx, fy, fz)
        assert struct.unpack_from("<fff", decomp_a, 0x34) == (fx, fy, fz)
        assert struct.unpack_from("<ff", decomp_a, 0x4C) == (fw, fw)
        assert struct.unpack_from("<f", decomp_b, 0x18)[0] == fw

    print("script_vm_func_002d4dac: PASS")

def main():
    test_engine_func_002c31e8()
    test_camp_func_002c6e04()
    test_script_vm_func_002ca6f4()
    test_func_002d29f4()
    test_script_vm_func_002d4dac()
    print("\n========================================")
    print("ALL 5 FUNCTIONS IN PART 17 PASSED 100%!")
    print("========================================")

if __name__ == "__main__":
    main()
