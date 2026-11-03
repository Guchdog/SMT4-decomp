#!/usr/bin/env python3
"""Differential test for batch 30 B part 8:
- script_vm_func_00266e10 (0x00266E10, 120 B)
- camp_func_00269f34 (0x00269F34, 124 B)
- script_vm_func_0026ca24 (0x0026CA24, 104 B)
- script_vm_func_0026f3f8 (0x0026F3F8, 104 B)
- script_vm_func_0026fc24 (0x0026FC24, 124 B)
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


def test_00266e10():
    print("--- Testing script_vm_func_00266e10 ---")
    addr = 0x00266E10
    size = 120
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_00266e10", ROOT / "build")
    staged = stage_body(comp, relocs, addr, {})

    ACTIVE_ADDR = 0x004E3134
    BITFIELD_ADDR = 0x004E312C
    ENTRIES_ADDR = 0x004E2F68

    def run_one(c_bytes, active, idx, entry_val, init_bitfield):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        uc.mem_write(ACTIVE_ADDR, struct.pack("<B", active))
        uc.mem_write(BITFIELD_ADDR, struct.pack("<I", init_bitfield))
        if idx < 16:
            uc.mem_write(ENTRIES_ADDR + idx * 4, struct.pack("<I", entry_val))

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, idx)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        ret = uc.reg_read(UC_ARM_REG_R0)
        out_bitfield = struct.unpack_from("<I", uc.mem_read(BITFIELD_ADDR, 4))[0]
        return ret, out_bitfield

    test_cases = [
        # (active, idx, entry_val, init_bitfield)
        (0, 5, 0x1234, 0xFFFF),          # inactive -> 0
        (1, 16, 0x1234, 0xFFFF),         # idx >= 16 -> 0
        (1, 20, 0x1234, 0xFFFF),
        (1, 0, 0, 0b1),                  # entry == 0 -> clears bit, returns 0
        (1, 0, 0x55, 0b1),               # entry != 0, bit set -> returns 1
        (1, 0, 0x55, 0b0),               # entry != 0, bit not set -> returns 0
        (1, 3, 0, 0xFF),                 # entry == 0 -> bit 3 cleared
        (1, 3, 0x100, 0xFF),             # entry != 0 -> bit 3 remains, returns 1
        (1, 15, 0x999, 1 << 15),         # top bit 15
        (1, 15, 0, 1 << 15),             # top bit 15 cleared
    ]

    for active, idx, entry_val, init_bf in test_cases:
        r1, bf1 = run_one(orig, active, idx, entry_val, init_bf)
        r2, bf2 = run_one(staged, active, idx, entry_val, init_bf)
        assert r1 == r2, f"Ret mismatch: orig={r1}, comp={r2} for idx={idx}"
        assert bf1 == bf2, f"Bitfield mismatch: orig={hex(bf1)}, comp={hex(bf2)} for idx={idx}"
    print("script_vm_func_00266e10: PASS")


def test_00269f34():
    print("--- Testing camp_func_00269f34 ---")
    addr = 0x00269F34
    size = 124
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("camp_func_00269f34", ROOT / "build")

    STUB_HELPER = 0x002B9008
    staged = stage_body(comp, relocs, addr, {
        "camp_func_002b9008": STUB_HELPER,
    })

    PTR_MGR = 0x0043DA90
    MGR = 0x20001000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_HELPER, stub_code)

        uc.mem_write(PTR_MGR, struct.pack("<I", MGR))
        uc.mem_write(MGR, b"\xAA" * 0x2000)

        call_count = [0]
        def helper_hook(uc, address, sz, user_data):
            if address == STUB_HELPER:
                call_count[0] += 1

        h = uc.hook_add(UC_HOOK_CODE, helper_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        mem_slice = uc.mem_read(MGR + 0xE00, 0x50)
        return call_count[0], mem_slice

    c1, m1 = run_one(orig)
    c2, m2 = run_one(staged)
    assert c1 == c2, f"Call count mismatch: orig={c1}, comp={c2}"
    assert m1 == m2, f"Memory mismatch: orig={m1.hex()}, comp={m2.hex()}"
    print("camp_func_00269f34: PASS")


def test_0026ca24():
    print("--- Testing script_vm_func_0026ca24 ---")
    addr = 0x0026CA24
    size = 104
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_0026ca24", ROOT / "build")

    STUB_MEMSET = 0x002C4B30
    STUB_MEMCPY = 0x002C5FF4
    staged = stage_body(comp, relocs, addr, {
        "engine_func_002c4b30": STUB_MEMSET,
        "engine_func_002c5ff4": STUB_MEMCPY,
    })

    PTR_BASE = 0x0043E0F8
    BASE = 0x20001000
    STR_ADDR = 0x20004000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, input_str_bytes):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_MEMSET, stub_code)
        uc.mem_write(STUB_MEMCPY, stub_code)

        uc.mem_write(PTR_BASE, struct.pack("<I", BASE))
        uc.mem_write(BASE, b"\xAA" * 0x300)

        str_ptr = 0
        if input_str_bytes is not None:
            str_ptr = STR_ADDR
            uc.mem_write(STR_ADDR, input_str_bytes)

        def code_hook(uc, address, sz, user_data):
            if address == STUB_MEMSET:
                dst = uc.reg_read(UC_ARM_REG_R0)
                length = uc.reg_read(UC_ARM_REG_R1)
                uc.mem_write(dst, b"\x00" * length)
            elif address == STUB_MEMCPY:
                dst = uc.reg_read(UC_ARM_REG_R0)
                src = uc.reg_read(UC_ARM_REG_R1)
                length = uc.reg_read(UC_ARM_REG_R2)
                data = uc.mem_read(src, length)
                uc.mem_write(dst, bytes(data))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, str_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        f10 = uc.mem_read(BASE + 0x10, 1)[0]
        buf = uc.mem_read(BASE + 0x154, 0x31)
        return f10, buf

    test_cases = [
        None,                       # nullptr
        b"\x00",                    # empty string
        b"Hello\x00",               # normal string
        b"A" * 48 + b"\x00",        # exact 48 chars + null (total 49)
        b"A" * 50,                  # 50 chars without null (overflows limit)
        b"TestString123\x00",
    ]

    for tc in test_cases:
        f1, b1 = run_one(orig, tc)
        f2, b2 = run_one(staged, tc)
        assert f1 == f2, f"Flag10 mismatch: orig={f1}, comp={f2} for {tc}"
        assert b1 == b2, f"Buffer mismatch: orig={b1.hex()}, comp={b2.hex()} for {tc}"
    print("script_vm_func_0026ca24: PASS")


def test_0026f3f8():
    print("--- Testing script_vm_func_0026f3f8 ---")
    addr = 0x0026F3F8
    size = 104
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_0026f3f8", ROOT / "build")

    STUB_DISP = 0x00296D8C
    staged = stage_body(comp, relocs, addr, {
        "script_vm_func_00296d8c": STUB_DISP,
    })

    PTR_MGR = 0x0043DA2C
    MGR = 0x20001000
    OBJ = 0x20005000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, arg0, arg1):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_DISP, stub_code)

        uc.mem_write(PTR_MGR, struct.pack("<I", MGR))
        uc.mem_write(MGR, b"\x00" * 0x600)
        uc.mem_write(MGR + 0x558, struct.pack("<I", OBJ))

        calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_DISP:
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                sp = uc.reg_read(UC_ARM_REG_SP)
                p5, p6, p7 = struct.unpack_from("<III", uc.mem_read(sp, 12))
                calls.append((r0, r1, r2, r3, p5, p6, p7))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        f4cb = uc.mem_read(MGR + 0x4CB, 1)[0]
        f55c = uc.mem_read(MGR + 0x55C, 1)[0]
        f558 = struct.unpack_from("<I", uc.mem_read(MGR + 0x558, 4))[0]
        return calls, f4cb, f55c, f558

    test_cases = [
        (0, 100),
        (1, 200),
        (55, 0),
        (0x12345678, 0x87654321),
    ]

    for arg0, arg1 in test_cases:
        c1, a1, b1, obj1 = run_one(orig, arg0, arg1)
        c2, a2, b2, obj2 = run_one(staged, arg0, arg1)
        assert c1 == c2, f"Call mismatch: orig={c1}, comp={c2}"
        assert a1 == a2, f"f4cb mismatch: orig={a1}, comp={a2}"
        assert b1 == b2, f"f55c mismatch: orig={b1}, comp={b2}"
        assert obj1 == obj2, f"obj mismatch: orig={obj1}, comp={obj2}"
    print("script_vm_func_0026f3f8: PASS")


def test_0026fc24():
    print("--- Testing script_vm_func_0026fc24 ---")
    addr = 0x0026FC24
    size = 124
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_0026fc24", ROOT / "build")

    STUB_GATE = 0x002C583C
    STUB_ACTION = 0x002105F4
    staged = stage_body(comp, relocs, addr, {
        "engine_func_002c583c": STUB_GATE,
        "script_vm_func_002105f4": STUB_ACTION,
    })

    TABLE = 0x004C53C4
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, gate_ret, slot0_data, slot1_data):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_GATE, stub_code)
        uc.mem_write(STUB_ACTION, stub_code)

        uc.mem_write(TABLE, slot0_data + slot1_data)

        actions = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_GATE:
                uc.reg_write(UC_ARM_REG_R0, gate_ret)
            elif address == STUB_ACTION:
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                actions.append((r0, r1))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        ret = uc.reg_read(UC_ARM_REG_R0)
        table_after = uc.mem_read(TABLE, 64)
        return ret, actions, table_after

    def make_slot(arg0, flags):
        buf = bytearray(32)
        struct.pack_into("<I", buf, 0, arg0)
        for offset in range(4, 28, 4):
            struct.pack_into("<I", buf, offset, 0x11111111 * (offset // 4))
        struct.pack_into("<I", buf, 0x1C, flags)
        return bytes(buf)

    test_cases = [
        # (gate_ret, slot0, slot1)
        (1, make_slot(10, 0x12), make_slot(20, 0x12)),       # gate != 0 -> early return 0
        (0, make_slot(10, 0), make_slot(20, 0)),            # no flags match -> 0
        (0, make_slot(10, 2), make_slot(20, 0x10)),         # each missing the other flag
        (0, make_slot(10, 0x12), make_slot(20, 0)),         # slot 0 matches (flags & 2 && flags & 0x10) -> 1
        (0, make_slot(10, 0), make_slot(20, 0x22)),         # slot 1 matches (flags & 2 && flags & 0x20) -> 1
        (0, make_slot(10, 0x32), make_slot(20, 0x32)),       # both match -> 1
    ]

    for gate_ret, s0, s1 in test_cases:
        r1, a1, t1 = run_one(orig, gate_ret, s0, s1)
        r2, a2, t2 = run_one(staged, gate_ret, s0, s1)
        assert r1 == r2, f"Ret mismatch: orig={r1}, comp={r2}"
        assert a1 == a2, f"Actions mismatch: orig={a1}, comp={a2}"
        assert t1 == t2, f"Table mismatch: orig={t1.hex()}, comp={t2.hex()}"
    print("script_vm_func_0026fc24: PASS")


def main():
    test_00266e10()
    test_00269f34()
    test_0026ca24()
    test_0026f3f8()
    test_0026fc24()
    print("\nALL 5 FUNCTIONS IN BATCH 30 B PART 8 PASSED WITH 100% DIFFERENTIAL FIDELITY!")

if __name__ == "__main__":
    main()
