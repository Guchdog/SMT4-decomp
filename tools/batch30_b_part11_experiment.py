#!/usr/bin/env python3
"""Differential test for batch 30 B part 11:
- camp_func_0028ebd8 (0x0028EBD8, 108 B)
- script_vm_func_0029117c (0x0029117C, 112 B)
- script_vm_func_00291c3c (0x00291C3C, 112 B)
- script_vm_func_0029350c (0x0029350C, 112 B)
- script_vm_func_0029357c (0x0029357C, 112 B)
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


def test_0028ebd8():
    print("--- Testing camp_func_0028ebd8 ---")
    addr = 0x0028EBD8
    size = 108
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("camp_func_0028ebd8", ROOT / "build")

    STUB_CUSTOM = 0x002B931C
    STUB_SUB = 0x002C0EC4
    STUB_PAYLOAD = 0x002C0E9C
    STUB_COUNT = 0x002C0E4C

    staged = stage_body(comp, relocs, addr, {
        "script_vm_func_002b931c": STUB_CUSTOM,
        "Tbb_GetGlobalSubTable": STUB_SUB,
        "Tbb_GetPayloadData": STUB_PAYLOAD,
        "Tbb_GetRowCount": STUB_COUNT,
    })

    PTR_MGR = 0x00433158
    MGR = 0x20001000
    TABLE_HDR = 0x20002000
    PAYLOAD = 0x20003000
    CUSTOM_RET = 0x20006000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, id_arg, flag_arg, custom_p, row_count):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_CUSTOM, stub_code)
        uc.mem_write(STUB_SUB, stub_code)
        uc.mem_write(STUB_PAYLOAD, stub_code)
        uc.mem_write(STUB_COUNT, stub_code)

        uc.mem_write(PTR_MGR, struct.pack("<I", MGR))

        def code_hook(uc, address, sz, user_data):
            if address == STUB_CUSTOM:
                uc.reg_write(UC_ARM_REG_R0, custom_p)
            elif address == STUB_SUB:
                uc.reg_write(UC_ARM_REG_R0, TABLE_HDR)
            elif address == STUB_PAYLOAD:
                uc.reg_write(UC_ARM_REG_R0, PAYLOAD)
            elif address == STUB_COUNT:
                uc.reg_write(UC_ARM_REG_R0, row_count)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, id_arg)
        uc.reg_write(UC_ARM_REG_R1, flag_arg)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret

    test_cases = [
        # (id, flag, custom_p, row_count)
        (5, 0, CUSTOM_RET, 10),      # custom != null -> CUSTOM_RET + 2
        (5, 1, CUSTOM_RET, 10),      # custom != null -> CUSTOM_RET + 2
        (15, 0, 0, 10),              # row_count <= id -> PAYLOAD
        (2, 0, 0, 10),               # id < row_count, flag 0 -> PAYLOAD + 2*40
        (2, 1, 0, 10),               # id < row_count, flag 1 -> PAYLOAD + 2*40 + 0x10
        (0, 0, 0, 10),
        (0, 1, 0, 10),
    ]

    for id_a, fl_a, cust, cnt in test_cases:
        r1 = run_one(orig, id_a, fl_a, cust, cnt)
        r2 = run_one(staged, id_a, fl_a, cust, cnt)
        assert r1 == r2, f"Ret mismatch: orig={hex(r1)}, comp={hex(r2)} for id={id_a}, fl={fl_a}"
    print("camp_func_0028ebd8: PASS")


def test_0029117c():
    print("--- Testing script_vm_func_0029117c ---")
    addr = 0x0029117C
    size = 112
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_0029117c", ROOT / "build")

    STUB_GATE = 0x002C583C
    staged = stage_body(comp, relocs, addr, {
        "engine_func_002c583c": STUB_GATE,
    })

    MODE_PTR = 0x0044E09C
    SLOT0 = 0x004C53C4
    SLOT1 = 0x004C53E4
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, gate_ret, mode, val, init_flags):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_GATE, stub_code)

        uc.mem_write(MODE_PTR, struct.pack("<I", mode))
        target_slot = SLOT0 if mode == 0 else SLOT1
        uc.mem_write(target_slot, b"\x00" * 32)
        uc.mem_write(target_slot + 0x1C, struct.pack("<I", init_flags))

        def code_hook(uc, address, sz, user_data):
            if address == STUB_GATE:
                uc.reg_write(UC_ARM_REG_R0, gate_ret)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, val)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        out_val = struct.unpack_from("<I", uc.mem_read(target_slot + 8, 4))[0]
        out_flags = struct.unpack_from("<I", uc.mem_read(target_slot + 0x1C, 4))[0]
        return out_val, out_flags

    test_cases = [
        # (gate, mode, val, flags)
        (1, 0, 0x1234, 0x2),          # gate != 0 -> no change
        (0, 0, 0x1234, 0),            # flags & 2 == 0 -> no change
        (0, 0, 0x1234, 0x4),          # flags & 0x3C != 0 -> no change
        (0, 0, 0x5555, 0x2),          # flags & 2, & ~0x3C, & ~0x40 -> flags |= 0x10
        (0, 0, 0x5555, 0x42),         # flags & 2, & ~0x3C, & 0x40 -> flags |= 0x200
        (0, 1, 0x7777, 0x42),         # mode 1
    ]

    for gate, mode, val, fl in test_cases:
        v1, f1 = run_one(orig, gate, mode, val, fl)
        v2, f2 = run_one(staged, gate, mode, val, fl)
        assert (v1, f1) == (v2, f2), f"Mismatch for mode={mode}, flags={hex(fl)}: orig=({hex(v1)}, {hex(f1)}), comp=({hex(v2)}, {hex(f2)})"
    print("script_vm_func_0029117c: PASS")


def test_00291c3c():
    print("--- Testing script_vm_func_00291c3c ---")
    addr = 0x00291C3C
    size = 112
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_00291c3c", ROOT / "build")

    STUB_NOTIF = 0x002AEB2C
    staged = stage_body(comp, relocs, addr, {
        "script_vm_func_002aeb2c": STUB_NOTIF,
    })

    COUNT_ADDR = 0x0044CF60
    MODE_ADDR = 0x0044CF64
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, init_count, init_mode):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_NOTIF, stub_code)

        uc.mem_write(COUNT_ADDR, struct.pack("<I", init_count))
        uc.mem_write(MODE_ADDR, struct.pack("<I", init_mode))

        calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_NOTIF:
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                calls.append((r0, r1))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        out_count = struct.unpack_from("<I", uc.mem_read(COUNT_ADDR, 4))[0]
        out_mode = struct.unpack_from("<I", uc.mem_read(MODE_ADDR, 4))[0]
        return calls, out_count, out_mode

    test_cases = [
        # (count, mode)
        (2, 0x65),       # count -> 1, no call, mode unchanged
        (1, 0x65),       # count -> 0, call (0x1C, 6), mode -> 0
        (1, 0x66),       # count -> 0, call (0x1C, 7), mode -> 0
        (1, 0x67),       # count -> 0, call (0x1C, 8), mode -> 0
        (1, 0x10),       # count -> 0, other mode, mode -> 0
    ]

    for cnt, md in test_cases:
        c1, cnt1, md1 = run_one(orig, cnt, md)
        c2, cnt2, md2 = run_one(staged, cnt, md)
        assert c1 == c2, f"Calls mismatch for count={cnt}, mode={hex(md)}: orig={c1}, comp={c2}"
        assert (cnt1, md1) == (cnt2, md2), "State mismatch"
    print("script_vm_func_00291c3c: PASS")


def test_0029350c_and_57c():
    print("--- Testing script_vm_func_0029350c and script_vm_func_0029357c ---")
    PTR_MGR = 0x0043DCF0
    MGR = 0x20001000
    STUB_CAMP = 0x002BDAC0
    STUB_ELEM = 0x00293A30
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    for func_name, addr, sz, expected_type in [
        ("script_vm_func_0029350c", 0x0029350C, 112, 4),
        ("script_vm_func_0029357c", 0x0029357C, 112, 5),
    ]:
        orig = load_original_bytes(addr, sz)
        comp, relocs = compile_function(func_name, ROOT / "build")
        staged = stage_body(comp, relocs, addr, {
            "camp_func_002bdac0": STUB_CAMP,
            "script_vm_func_00293a30": STUB_ELEM,
        })

        def run_one(c_bytes, init_val):
            uc = setup_uc()
            uc.mem_write(addr, c_bytes)
            uc.mem_write(STUB_CAMP, stub_code)
            uc.mem_write(STUB_ELEM, stub_code)

            uc.mem_write(PTR_MGR, struct.pack("<I", MGR))
            uc.mem_write(MGR, b"\x00" * 0x800)
            uc.mem_write(MGR + 0x2C, struct.pack("<I", init_val))

            for i in range(4):
                uc.mem_write(MGR + 0x6C8 + i * 4, struct.pack("<I", 0x1000 + i))
            for i in range(24):
                uc.mem_write(MGR + 0x6D8 + i * 4, struct.pack("<I", 0x2000 + i))

            camp_calls = []
            elem_calls = []

            def code_hook(uc, address, sz, user_data):
                if address == STUB_CAMP:
                    r0 = uc.reg_read(UC_ARM_REG_R0)
                    r1 = uc.reg_read(UC_ARM_REG_R1)
                    r2 = uc.reg_read(UC_ARM_REG_R2)
                    camp_calls.append((r0, r1, r2))
                elif address == STUB_ELEM:
                    r0 = uc.reg_read(UC_ARM_REG_R0)
                    r1 = uc.reg_read(UC_ARM_REG_R1)
                    elem_calls.append((r0, r1))

            h = uc.hook_add(UC_HOOK_CODE, code_hook)

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0)
            uc.reg_write(UC_ARM_REG_PC, addr)

            uc.emu_start(addr, 0, count=500)

            out_val = struct.unpack_from("<I", uc.mem_read(MGR + 0x2C, 4))[0]
            return camp_calls, elem_calls, out_val

        for init_v in [0, 1]:
            c1, e1, v1 = run_one(orig, init_v)
            c2, e2, v2 = run_one(staged, init_v)
            assert c1 == c2, f"Camp call mismatch for {func_name}: orig={c1}, comp={c2}"
            assert e1 == e2, f"Elem call mismatch for {func_name}: orig={e1}, comp={e2}"
            assert v1 == v2, f"Val mismatch for {func_name}: orig={v1}, comp={v2}"
        print(f"{func_name}: PASS")


def main():
    test_0028ebd8()
    test_0029117c()
    test_00291c3c()
    test_0029350c_and_57c()
    print("\nALL 5 FUNCTIONS IN BATCH 30 B PART 11 PASSED WITH 100% DIFFERENTIAL FIDELITY!")

if __name__ == "__main__":
    main()
