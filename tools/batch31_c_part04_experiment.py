#!/usr/bin/env python3
"""Differential test for batch 31 C part 4:
- camp_func_0022e4e8 (0x0022E4E8, 164 B)
- engine_func_002303c8 (0x002303C8, 164 B)
- unite_func_00233804 (0x00233804, 168 B)
- func_00237738 (0x00237738, 172 B)
- func_00238b30 (0x00238B30, 184 B)
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

def test_camp_func_0022e4e8():
    addr = 0x0022E4E8
    print(f"--- Testing camp_func_0022e4e8 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 164)
    tmp = ROOT / "build" / "test_31c_part04"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_0022e4e8", tmp)

    FN_2B9364 = 0x002B9364
    FN_1F48F4 = 0x001F48F4
    FN_2992D8 = 0x002992D8
    sym_map = {
        "func_002b9364": FN_2B9364,
        "func_001f48f4": FN_1F48F4,
        "func_002992d8": FN_2992D8,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, initial_p_flags: int, extra_val: int, sub_ret: int, check_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        p_flags_addr = 0x10082000
        src_obj_addr = 0x10083000
        res_buf_addr = 0x10084000

        uc.mem_write(p_flags_addr, struct.pack("<H", initial_p_flags))

        src_mem = bytearray(0x80)
        struct.pack_into("<H", src_mem, 0x46, 0x42)
        uc.mem_write(src_obj_addr, bytes(src_mem))

        res_mem = bytearray(0x100)
        index = 2
        struct.pack_into("<H", res_mem, index * 2 + 0x6C, extra_val)
        uc.mem_write(res_buf_addr, bytes(res_mem))

        def f_b9364(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, res_buf_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_f48f4(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, sub_ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_992d8(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, check_ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_b9364, None, FN_2B9364, FN_2B9364)
        uc.hook_add(UC_HOOK_CODE, f_f48f4, None, FN_1F48F4, FN_1F48F4)
        uc.hook_add(UC_HOOK_CODE, f_992d8, None, FN_2992D8, FN_2992D8)

        uc.reg_write(UC_ARM_REG_R0, p_flags_addr)
        uc.reg_write(UC_ARM_REG_R1, src_obj_addr)
        uc.reg_write(UC_ARM_REG_R2, index)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        res_flags = struct.unpack("<H", uc.mem_read(p_flags_addr, 2))[0]
        return res_flags

    cases = [
        (0x0000, 0x0405, 3, 1),
        (0x1234, 0x0800, 5, 0),
        (0xFFFF, 0xFC00, 2, 1),
        (0x0000, 0x0000, 0, 0),
    ]

    for c in cases:
        r_o = run_one(orig_code, *c)
        r_d = run_one(decomp_code, *c)
        assert r_o == r_d, f"22e4e8 mismatch on {c}: orig {hex(r_o)} vs decomp {hex(r_d)}"

    print("camp_func_0022e4e8: PASS")

def test_engine_func_002303c8():
    addr = 0x002303C8
    print(f"--- Testing engine_func_002303c8 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 164)
    tmp = ROOT / "build" / "test_31c_part04"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_002303c8", tmp)

    FN_28C2A8 = 0x0028C2A8
    FN_29A3C4 = 0x0029A3C4
    FN_292F44 = 0x00292F44
    FN_2B66EC = 0x002B66EC
    FN_29C768 = 0x0029C768
    FN_29A384 = 0x0029A384
    FN_29A368 = 0x0029A368
    FN_2306EC = 0x002306EC
    FN_23077C = 0x0023077C
    FN_29A2D0 = 0x0029A2D0

    sym_map = {
        "func_0028c2a8": FN_28C2A8,
        "func_0029a3c4": FN_29A3C4,
        "func_00292f44": FN_292F44,
        "func_002b66ec": FN_2B66EC,
        "func_0029c768": FN_29C768,
        "func_0029a384": FN_29A384,
        "func_0029a368": FN_29A368,
        "func_002306ec": FN_2306EC,
        "func_0023077c": FN_23077C,
        "func_0029a2d0": FN_29A2D0,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, type_val: int, has_existing_ptr: bool):
        uc = create_emulator()
        uc.mem_write(addr, code)

        self_addr = 0x10050000
        uc.mem_map(self_addr, 0x20000)
        mem = bytearray(0x16000)
        struct.pack_into("<I", mem, 0x10, type_val)
        struct.pack_into("<I", mem, 0x15D48, 0x10070000 if has_existing_ptr else 0)
        uc.mem_write(self_addr, bytes(mem))

        calls = []
        def stub(name, n):
            def handler(uc, address, size, user_data):
                regs = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3]
                args = [uc.reg_read(regs[i]) for i in range(n)]
                calls.append((name, *args))
                if name == "b66ec":
                    uc.reg_write(UC_ARM_REG_R0, 0x10085000)
                elif name == "9a2d0":
                    uc.reg_write(UC_ARM_REG_R0, 0x10086000)
                lr = uc.reg_read(UC_ARM_REG_LR)
                uc.reg_write(UC_ARM_REG_PC, lr)
            return handler

        uc.hook_add(UC_HOOK_CODE, stub("8c2a8", 0), None, FN_28C2A8, FN_28C2A8)
        uc.hook_add(UC_HOOK_CODE, stub("9a3c4", 1), None, FN_29A3C4, FN_29A3C4)
        uc.hook_add(UC_HOOK_CODE, stub("92f44", 1), None, FN_292F44, FN_292F44)
        uc.hook_add(UC_HOOK_CODE, stub("b66ec", 0), None, FN_2B66EC, FN_2B66EC)
        uc.hook_add(UC_HOOK_CODE, stub("9c768", 1), None, FN_29C768, FN_29C768)
        uc.hook_add(UC_HOOK_CODE, stub("9a384", 1), None, FN_29A384, FN_29A384)
        uc.hook_add(UC_HOOK_CODE, stub("9a368", 1), None, FN_29A368, FN_29A368)
        uc.hook_add(UC_HOOK_CODE, stub("306ec", 1), None, FN_2306EC, FN_2306EC)
        uc.hook_add(UC_HOOK_CODE, stub("3077c", 1), None, FN_23077C, FN_23077C)
        uc.hook_add(UC_HOOK_CODE, stub("9a2d0", 2), None, FN_29A2D0, FN_29A2D0)

        uc.reg_write(UC_ARM_REG_R0, self_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        f15d24 = struct.unpack("<I", uc.mem_read(self_addr + 0x15D24, 4))[0]
        f15d28 = struct.unpack("<I", uc.mem_read(self_addr + 0x15D28, 4))[0]
        f15d48 = struct.unpack("<I", uc.mem_read(self_addr + 0x15D48, 4))[0]
        return calls, f15d24, f15d28, f15d48

    cases = [
        (1, False),
        (0, False),
        (1, True),
        (2, True),
    ]

    for c in cases:
        r_o = run_one(orig_code, *c)
        r_d = run_one(decomp_code, *c)
        assert r_o == r_d, f"2303c8 mismatch on {c}: orig {r_o} vs decomp {r_d}"

    print("engine_func_002303c8: PASS")

def test_unite_func_00233804():
    addr = 0x00233804
    print(f"--- Testing unite_func_00233804 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 168)
    tmp = ROOT / "build" / "test_31c_part04"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("unite_func_00233804", tmp)

    FN_2B9008 = 0x002B9008
    FN_2C4450 = 0x002C4450
    FN_2B88C4 = 0x002B88C4
    sym_map = {
        "func_002b9008": FN_2B9008,
        "func_002c4450": FN_2C4450,
        "func_002b88c4": FN_2B88C4,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, init_count: int, arg1: int, arg2: int, arg3: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        self_addr = 0x10082000
        mem = bytearray(0x100)
        struct.pack_into("<h", mem, 0x30, init_count)
        uc.mem_write(self_addr, bytes(mem))

        calls = []
        def f_b9008(uc, address, size, user_data):
            calls.append("b9008")
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_c4450(uc, address, size, user_data):
            buf = uc.reg_read(UC_ARM_REG_R0)
            sz = uc.reg_read(UC_ARM_REG_R1)
            val = uc.reg_read(UC_ARM_REG_R2) & 0xFF
            uc.mem_write(buf, bytes([val] * sz))
            calls.append(("c4450", sz, val))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_b88c4(uc, address, size, user_data):
            a0 = uc.reg_read(UC_ARM_REG_R0)
            a1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("b88c4", a0, a1))
            ret = (a1 + 0x100) & 0xFFFF
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_b9008, None, FN_2B9008, FN_2B9008)
        uc.hook_add(UC_HOOK_CODE, f_c4450, None, FN_2C4450, FN_2C4450)
        uc.hook_add(UC_HOOK_CODE, f_b88c4, None, FN_2B88C4, FN_2B88C4)

        uc.reg_write(UC_ARM_REG_R0, self_addr)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_R2, arg2)
        uc.reg_write(UC_ARM_REG_R3, arg3)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        mem_res = uc.mem_read(self_addr, 0x40)
        return calls, mem_res

    cases = [
        (3, 10, 20, 4),
        (0, 5, 10, 0),
        (-1, 5, 10, 2),
    ]

    for c in cases:
        r_o = run_one(orig_code, *c)
        r_d = run_one(decomp_code, *c)
        assert r_o == r_d, f"233804 mismatch on {c}"

    print("unite_func_00233804: PASS")

def test_func_00237738():
    addr = 0x00237738
    print(f"--- Testing func_00237738 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 172)
    tmp = ROOT / "build" / "test_31c_part04"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00237738", tmp)

    decomp_code = stage_body(comp, relocs, addr, {})

    def run_one(code, a1, a2, a3):
        uc = create_emulator()
        uc.mem_write(addr, code)

        self_addr = 0x10082000
        # fill with non-zero garbage
        uc.mem_write(self_addr, b"\xEE" * 0x70)

        uc.reg_write(UC_ARM_REG_R0, self_addr)
        uc.reg_write(UC_ARM_REG_R1, a1)
        uc.reg_write(UC_ARM_REG_R2, a2)
        uc.reg_write(UC_ARM_REG_R3, a3)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return uc.mem_read(self_addr, 0x68)

    cases = [
        (0x11111111, 0x22222222, 0x33333333),
        (0, 0, 0),
        (0xABCDEF01, 0x23456789, 0x3456789A),
    ]

    for c in cases:
        r_o = run_one(orig_code, *c)
        r_d = run_one(decomp_code, *c)
        assert r_o == r_d, f"237738 mismatch on {c}"

    print("func_00237738: PASS")

def test_func_00238b30():
    addr = 0x00238B30
    print(f"--- Testing func_00238b30 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 184)
    tmp = ROOT / "build" / "test_31c_part04"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00238b30", tmp)

    FN_238BE8 = 0x00238BE8
    sym_map = {
        "func_00238be8": FN_238BE8,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, arr_vals: list[int], nodes: list[int], lookup_map: dict[int, tuple[int, int, int]]):
        uc = create_emulator()
        uc.mem_write(addr, code)

        arr_base = 0x10082000
        arr_buf = bytearray(len(arr_vals) * 2)
        for i, v in enumerate(arr_vals):
            struct.pack_into("<H", arr_buf, i * 2, v)
        uc.mem_write(arr_base, bytes(arr_buf))

        p_arr_addr = 0x10083000
        uc.mem_write(p_arr_addr, struct.pack("<I", arr_base))

        node_base = 0x10084000
        for i, target_val in enumerate(nodes):
            n_addr = node_base + i * 0x20
            next_addr = (node_base + (i + 1) * 0x20) if i + 1 < len(nodes) else 0
            n_mem = bytearray(0x20)
            struct.pack_into("<I", n_mem, 4, next_addr)
            struct.pack_into("<H", n_mem, 0xA, target_val)
            uc.mem_write(n_addr, bytes(n_mem))

        p_node_addr = 0x10083004
        uc.mem_write(p_node_addr, struct.pack("<I", node_base))

        lookup_base = 0x10086000
        def f_38be8(uc, address, size, user_data):
            target = uc.reg_read(UC_ARM_REG_R0)
            if target in lookup_map:
                f2, f4, f6 = lookup_map[target]
                struct.pack_into("<HHHH", uc.mem_read(lookup_base, 8), 0, target, f2, f4, f6)
                # write entry
                l_mem = bytearray(8)
                struct.pack_into("<HHHH", l_mem, 0, target, f2, f4, f6)
                uc.mem_write(lookup_base, bytes(l_mem))
                uc.reg_write(UC_ARM_REG_R0, lookup_base)
            else:
                uc.reg_write(UC_ARM_REG_R0, 0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_38be8, None, FN_238BE8, FN_238BE8)

        start = 0
        count = len(arr_vals)
        uc.reg_write(UC_ARM_REG_R0, p_arr_addr)
        uc.reg_write(UC_ARM_REG_R1, p_node_addr)
        uc.reg_write(UC_ARM_REG_R2, start)
        uc.reg_write(UC_ARM_REG_R3, count)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        final_node_ptr = struct.unpack("<I", uc.mem_read(p_node_addr, 4))[0]
        return ret, final_node_ptr

    l_map = {
        10: (20, 30, 40),
        15: (0, 0, 0),
    }

    # Case 1: direct match [10, 20] against nodes [10, 20]
    c1 = ([10, 20], [10, 20], l_map)
    # Case 2: match via lookup f2 (arr[0]=20, node[0]=10 -> lookup has 20)
    c2 = ([20, 20], [10, 20], l_map)
    # Case 3: match via lookup f4 (arr[0]=30, node[0]=10)
    c3 = ([30, 20], [10, 20], l_map)
    # Case 4: match via lookup f6 (arr[0]=40, node[0]=10)
    c4 = ([40, 20], [10, 20], l_map)
    # Case 5: lookup returns null (node[0]=999 not in map)
    c5 = ([50, 20], [999, 20], l_map)
    # Case 6: lookup has f2=0 (node[0]=15)
    c6 = ([50, 20], [15, 20], l_map)

    for c in [c1, c2, c3, c4, c5, c6]:
        r_o = run_one(orig_code, *c)
        r_d = run_one(decomp_code, *c)
        assert r_o == r_d, f"238b30 mismatch on {c}: orig {r_o} vs decomp {r_d}"

    print("func_00238b30: PASS")

def main():
    test_camp_func_0022e4e8()
    test_engine_func_002303c8()
    test_unite_func_00233804()
    test_func_00237738()
    test_func_00238b30()
    print("\nALL 5 FUNCTIONS IN LEAF_BATCH31_C PART 04 PASSED DIFFERENTIAL VERIFICATION!")

if __name__ == "__main__":
    main()
