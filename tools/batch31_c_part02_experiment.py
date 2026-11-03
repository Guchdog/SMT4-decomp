#!/usr/bin/env python3
"""Differential test for batch 31 C part 2:
- func_00219570 (0x00219570, 144 B) and func_00219600 (0x00219600, 36 B)
- engine_func_0021a0a8 (0x0021A0A8, 172 B)
- script_vm_func_0021bd04 (0x0021BD04, 160 B)
- script_vm_func_0021de1c (0x0021DE1C, 164 B)
- script_vm_func_0021dec0 (0x0021DEC0, 156 B)
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
SOURCE = ROOT / "src/engine/leaf_batch31_c.cpp"

with open(ORIG_BIN, "rb") as f:
    ORIG_DATA = f.read()

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch31_c.o"
        compile_tu_armv6k(source, obj)
        COMPILED_FUNCTIONS = extract_elf_functions_detailed(obj)
    return COMPILED_FUNCTIONS[func_name]

def stage_body(body: bytes, relocs, target_addr: int, symbol_map: dict[str, int]) -> bytes:
    data = bytearray(body)
    for reloc in relocs:
        sym = reloc.symbol_name
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
    uc.mem_map(0x00480000, 0x00100000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, unmapped_hook)

    val = uc.reg_read(UC_ARM_REG_C1_C0_2)
    val |= (0xF << 20)
    uc.reg_write(UC_ARM_REG_C1_C0_2, val)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return uc

def test_func_00219570_and_600():
    addr_a = 0x00219570
    addr_b = 0x00219600
    print(f"--- Testing func_00219570 and func_00219600 ({hex(addr_a)}, {hex(addr_b)}) ---")
    orig_a = load_original_bytes(addr_a, 144)
    orig_b = load_original_bytes(addr_b, 36)

    tmp = ROOT / "build" / "test_31c_part02"
    tmp.mkdir(parents=True, exist_ok=True)
    comp_a, relocs_a = compile_function("func_00219570", tmp)
    comp_b, relocs_b = compile_function("func_00219600", tmp)

    FN_2AE818 = 0x002AE818
    FN_282C44 = 0x00282C44
    sym_map_a = {
        "camp_func_002ae818": FN_2AE818,
        "camp_func_00282c44": FN_282C44,
    }
    decomp_a = stage_body(comp_a, relocs_a, addr_a, sym_map_a)
    decomp_b = stage_body(comp_b, relocs_b, addr_b, {})

    # Test func_00219570
    # Case combinations: r6/r0 (2, 2), (2, 1), (1, 2), (1, 1)
    # diff at 0x26, diff at 0x24
    test_cases_a = [
        (2, 1, 10, 10, 20, 20),
        (1, 2, 10, 10, 20, 20),
        (2, 2, 15, 10, 20, 20),
        (2, 2, 10, 15, 20, 20),
        (2, 2, 10, 10, 50, 20),
        (2, 2, 10, 10, 20, 50),
        (1, 1, 10, 10, 10, 10),
    ]

    def run_9570(code, c_a, c_b, off26_a, off26_b, off24_a, off24_b):
        uc = create_emulator()
        uc.mem_write(addr_a, code)

        obj_a = 0x10082000
        obj_b = 0x10083000
        ptr_a = 0x10084000
        ptr_b = 0x10084004
        uc.mem_write(ptr_a, struct.pack("<I", obj_a))
        uc.mem_write(ptr_b, struct.pack("<I", obj_b))

        sub_a = 0x10085000
        sub_b = 0x10086000
        mem_a = bytearray(0x40)
        mem_b = bytearray(0x40)
        struct.pack_into("<H", mem_a, 0x26, off26_a)
        struct.pack_into("<H", mem_b, 0x26, off26_b)
        struct.pack_into("<H", mem_a, 0x24, off24_a)
        struct.pack_into("<H", mem_b, 0x24, off24_b)
        uc.mem_write(sub_a, bytes(mem_a))
        uc.mem_write(sub_b, bytes(mem_b))

        def f_ae818(uc, address, size, user_data):
            arg = uc.reg_read(UC_ARM_REG_R0)
            ret = sub_a if arg == obj_a else sub_b
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_82c44(uc, address, size, user_data):
            arg = uc.reg_read(UC_ARM_REG_R0)
            ret = c_a if arg == obj_a else c_b
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_ae818, None, FN_2AE818, FN_2AE818)
        uc.hook_add(UC_HOOK_CODE, f_82c44, None, FN_282C44, FN_282C44)

        uc.reg_write(UC_ARM_REG_R0, ptr_a)
        uc.reg_write(UC_ARM_REG_R1, ptr_b)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr_a, 0x003E0000, timeout=1000000)
        r0 = uc.reg_read(UC_ARM_REG_R0)
        if r0 >= 0x80000000:
            r0 -= 0x100000000
        return r0

    for tc in test_cases_a:
        res_orig = run_9570(orig_a, *tc)
        res_decomp = run_9570(decomp_a, *tc)
        assert res_orig == res_decomp, f"9570 mismatch on {tc}: orig {res_orig} vs decomp {res_decomp}"

    # Test func_00219600
    test_cases_b = [
        ((10, 20), (10, 30)),
        ((10, 30), (10, 20)),
        ((5, 20), (10, 20)),
        ((10, 20), (5, 20)),
        ((15, 25), (15, 25)),
    ]

    def run_9600(code, pair_a, pair_b):
        uc = create_emulator()
        uc.mem_write(addr_b, code)

        ptr_a = 0x10082000
        ptr_b = 0x10082010
        uc.mem_write(ptr_a, struct.pack("<HH", pair_a[0], pair_a[1]))
        uc.mem_write(ptr_b, struct.pack("<HH", pair_b[0], pair_b[1]))

        uc.reg_write(UC_ARM_REG_R0, ptr_a)
        uc.reg_write(UC_ARM_REG_R1, ptr_b)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr_b, 0x003E0000, timeout=1000000)
        r0 = uc.reg_read(UC_ARM_REG_R0)
        if r0 >= 0x80000000:
            r0 -= 0x100000000
        return r0

    for tc in test_cases_b:
        res_orig = run_9600(orig_b, *tc)
        res_decomp = run_9600(decomp_b, *tc)
        assert res_orig == res_decomp, f"9600 mismatch on {tc}: orig {res_orig} vs decomp {res_decomp}"

    print("func_00219570 and func_00219600: PASS")

def test_engine_func_0021a0a8():
    addr = 0x0021A0A8
    print(f"--- Testing engine_func_0021a0a8 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 172)
    tmp = ROOT / "build" / "test_31c_part02"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_0021a0a8", tmp)

    FN_2502E8 = 0x002502E8
    FN_256C3C = 0x00256C3C
    FN_250108 = 0x00250108
    FN_24FFBC = 0x0024FFBC
    FN_24FF28 = 0x0024FF28

    sym_map = {
        "engine_func_002502e8": FN_2502E8,
        "engine_func_00256c3c": FN_256C3C,
        "func_00250108": FN_250108,
        "func_0024ffbc": FN_24FFBC,
        "func_0024ff28": FN_24FF28,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, flag, scale, has_vec):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub(name, arg_count):
            def handler(uc, address, size, user_data):
                reg_list = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3]
                args = [uc.reg_read(reg_list[i]) for i in range(arg_count)]
                calls.append((name, *args))
                lr = uc.reg_read(UC_ARM_REG_LR)
                uc.reg_write(UC_ARM_REG_PC, lr)
            return handler

        uc.hook_add(UC_HOOK_CODE, stub("2502e8", 2), None, FN_2502E8, FN_2502E8)
        uc.hook_add(UC_HOOK_CODE, stub("256c3c", 1), None, FN_256C3C, FN_256C3C)
        uc.hook_add(UC_HOOK_CODE, stub("250108", 3), None, FN_250108, FN_250108)
        uc.hook_add(UC_HOOK_CODE, stub("24ffbc", 3), None, FN_24FFBC, FN_24FFBC)
        uc.hook_add(UC_HOOK_CODE, stub("24ff28", 3), None, FN_24FF28, FN_24FF28)

        dst = 0x10082000
        vec_ptr = 0x10083000 if has_vec else 0
        if has_vec:
            uc.mem_write(vec_ptr, struct.pack("<fff", 1.5, 2.5, 3.5))

        uc.reg_write(UC_ARM_REG_R0, dst)
        uc.reg_write(UC_ARM_REG_R1, vec_ptr)
        uc.reg_write(UC_ARM_REG_R2, flag)
        # pass scale in float / R3 and D0 (s0)
        scale_bits = struct.unpack("<I", struct.pack("<f", scale))[0]
        uc.reg_write(UC_ARM_REG_D0, scale_bits)
        uc.reg_write(UC_ARM_REG_R3, scale_bits)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        # normalize stack addresses in calls
        normalized = []
        for call in calls:
            name = call[0]
            args = list(call[1:])
            for idx in range(len(args)):
                if args[idx] == dst + 0x10:
                    args[idx] = "dst+0x10"
                elif isinstance(args[idx], int) and args[idx] > STACK_BASE:
                    args[idx] = "stack"
            normalized.append((name, *args))
        return normalized

    cases = [
        (0, 1.0, False),
        (1, 1.0, False),
        (0, 2.0, False),
        (5, 0.5, True),
        (0, 1.0, True),
    ]
    for c in cases:
        c_orig = run_one(orig_code, *c)
        c_decomp = run_one(decomp_code, *c)
        assert c_orig == c_decomp, f"0021a0a8 mismatch on {c}: orig {c_orig} vs decomp {c_decomp}"

    print("engine_func_0021a0a8: PASS")

def test_script_vm_func_0021bd04():
    addr = 0x0021BD04
    print(f"--- Testing script_vm_func_0021bd04 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 160)
    tmp = ROOT / "build" / "test_31c_part02"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_0021bd04", tmp)

    FN_24F734 = 0x0024F734
    FN_2C4B30 = 0x002C4B30
    FN_24F6FC = 0x0024F6FC
    sym_map = {
        "script_vm_func_0024f734": FN_24F734,
        "engine_func_002c4b30": FN_2C4B30,
        "script_vm_func_0024f6fc": FN_24F6FC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, has_first: bool, total_count: int, target0: int, target1: int, items_data: list[tuple[int, int]]):
        uc = create_emulator()
        uc.mem_write(addr, code)

        out_count_addr = 0x00447604
        out_buf_addr = 0x004A0BE4
        target0_addr = 0x0049F91C
        target1_addr = 0x0049F920

        uc.mem_write(target0_addr, struct.pack("<i", target0))
        uc.mem_write(target1_addr, struct.pack("<i", target1))
        uc.mem_write(out_count_addr, struct.pack("<I", 0xDEADBEEF))
        uc.mem_write(out_buf_addr, b"\xAA" * 0x400)

        item_pool = 0x10082000
        for idx, (b0, b1) in enumerate(items_data):
            uc.mem_write(item_pool + idx * 8, struct.pack("bb", b0, b1))

        def f_24f734(uc, address, size, user_data):
            idx = uc.reg_read(UC_ARM_REG_R0)
            if idx == 0 and not has_first:
                uc.reg_write(UC_ARM_REG_R0, 0)
            elif idx < len(items_data):
                uc.reg_write(UC_ARM_REG_R0, item_pool + idx * 8)
            else:
                uc.reg_write(UC_ARM_REG_R0, 0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_2c4b30(uc, address, size, user_data):
            # Memset / clear buffer
            buf = uc.reg_read(UC_ARM_REG_R0)
            sz = uc.reg_read(UC_ARM_REG_R1)
            uc.mem_write(buf, b"\x00" * sz)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_24f6fc(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, total_count)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_24f734, None, FN_24F734, FN_24F734)
        uc.hook_add(UC_HOOK_CODE, f_2c4b30, None, FN_2C4B30, FN_2C4B30)
        uc.hook_add(UC_HOOK_CODE, f_24f6fc, None, FN_24F6FC, FN_24F6FC)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_count = struct.unpack("<I", uc.mem_read(out_count_addr, 4))[0]
        out_buf = uc.mem_read(out_buf_addr, 32)
        return out_count, out_buf

    cases = [
        (False, 5, 1, 2, [(1, 2)]),
        (True, 0, 1, 2, [(1, 2)]),
        (True, 4, 1, 2, [(1, 2), (1, 3), (2, 2), (1, 2)]),
        (True, 3, -1, 5, [(-1, 5), (0, 5), (1, 5)]),
    ]
    for c in cases:
        cnt_o, buf_o = run_one(orig_code, *c)
        cnt_d, buf_d = run_one(decomp_code, *c)
        assert cnt_o == cnt_d, f"21bd04 count mismatch: orig {cnt_o} vs decomp {cnt_d}"
        assert buf_o == buf_d, f"21bd04 buf mismatch: orig {buf_o} vs decomp {buf_d}"

    print("script_vm_func_0021bd04: PASS")

def test_script_vm_func_0021de1c():
    global COMPILED_FUNCTIONS
    COMPILED_FUNCTIONS = None
    addr = 0x0021DE1C
    print(f"--- Testing script_vm_func_0021de1c ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 164)
    tmp = ROOT / "build" / "test_31c_part02"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_0021de1c", tmp)

    FN_287D54 = 0x00287D54
    sym_map = {
        "engine_func_00287d54": FN_287D54,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, entities):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.mem_write(FN_287D54, load_original_bytes(FN_287D54, 32))

        base_ptr = 0x00447A48
        target_holder = 0x00447E88
        entities_base = 0x10082000
        target_obj = 0x10085000

        uc.mem_write(base_ptr, struct.pack("<I", entities_base))
        uc.mem_write(target_holder, struct.pack("<I", target_obj))

        # Setup target position at target_obj + 0x1C
        uc.mem_write(target_obj + 0x1C, struct.pack("<fff", 10.0, 20.0, 30.0))

        # Setup 24 entities (buffer >= 24 * 40 + 0x40)
        mem = bytearray(24 * 40 + 0x40)
        for i, (active, type_id, dist_val) in entities.items():
            off = i * 40
            mem[off + 0x1C] = active
            struct.pack_into("<H", mem, off + 0x32, type_id)
            # target is at (10, 20, 30). Set entity at (10 + dist_val, 20, 30) so Euclidean dist == dist_val
            struct.pack_into("<fff", mem, off + 0x20, 10.0 + float(dist_val), 20.0, 30.0)
        uc.mem_write(entities_base, bytes(mem))

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        # Read back all entities
        return uc.mem_read(entities_base, 24 * 40 + 0x40)

    # Case 1: no active entities
    e1 = {}
    # Case 2: two entities matching type 15, entity 5 is closer (dist 50) than entity 2 (dist 100)
    e2 = {
        2: (1, 15, 100.0),
        5: (1, 15, 50.0),
        10: (1, 14, 10.0), # wrong type
        12: (0, 15, 5.0),  # inactive
    }
    for e in [e1, e2]:
        res_o = run_one(orig_code, e)
        res_d = run_one(decomp_code, e)
        assert res_o == res_d, f"21de1c mismatch"

    print("script_vm_func_0021de1c: PASS")

def test_script_vm_func_0021dec0():
    addr = 0x0021DEC0
    print(f"--- Testing script_vm_func_0021dec0 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 156)
    tmp = ROOT / "build" / "test_31c_part02"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_0021dec0", tmp)

    decomp_code = stage_body(comp, relocs, addr, {})

    def run_one(code, slots_setup):
        uc = create_emulator()
        uc.mem_write(addr, code)

        holder = 0x00447A78
        base = 0x10050000
        uc.mem_write(holder, struct.pack("<I", base))

        # Initial memory with base[0x17] = 0xFF
        mem = bytearray(128 * 404)
        mem[0x17] = 0xFF
        for i, (active, type_id, state_id) in slots_setup.items():
            off = i * 404
            mem[off + 0x1D0] = active
            struct.pack_into("<I", mem, off + 0x1E4, type_id)
            struct.pack_into("<I", mem, off + 0x1D4, state_id)
            struct.pack_into("<I", mem, off + 0x1D8, 0)
        uc.mem_map(base, 0x20000)
        uc.mem_write(base, bytes(mem))

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return uc.mem_read(base, 128 * 404)

    slots = {
        0: (1, 0x10, 8),    # active, normal type, state 8 -> becomes 6, 1
        1: (1, 0x1D, 8),    # active, skipped type 0x1D -> unchanged
        2: (0, 0x10, 10),   # inactive -> unchanged
        3: (1, 0x20, 12),   # active, state 12 -> becomes 6, 1
        4: (1, 0x25, 14),   # active, skipped type 0x25 -> unchanged
        5: (1, 0x05, 16),   # active, state 16 -> becomes 6, 1
        6: (1, 0x05, 7),    # active, state 7 -> unchanged
    }

    res_o = run_one(orig_code, slots)
    res_d = run_one(decomp_code, slots)
    assert res_o == res_d, "21dec0 memory mismatch"

    print("script_vm_func_0021dec0: PASS")

def main():
    test_func_00219570_and_600()
    test_engine_func_0021a0a8()
    test_script_vm_func_0021bd04()
    test_script_vm_func_0021de1c()
    test_script_vm_func_0021dec0()
    print("\nALL 5 FUNCTIONS IN LEAF_BATCH31_C PART 02 PASSED DIFFERENTIAL VERIFICATION!")

if __name__ == "__main__":
    main()
