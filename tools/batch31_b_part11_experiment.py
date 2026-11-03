#!/usr/bin/env python3
"""Differential test for batch 31 B part 11:
- func_00324b68 (0x00324B68, 64 B)
- func_00327b18 (0x00327B18, 64 B)
- func_00340918 (0x00340918, 64 B)
- func_00360354 (0x00360354, 64 B)
- engine_func_00360780 (0x00360780, 64 B)
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
SOURCE = ROOT / "src/engine/leaf_batch31_b.cpp"

with open(ORIG_BIN, "rb") as f:
    ORIG_DATA = f.read()

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch31_b.o"
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

def hook_unmapped(uc, access, address, size, value, user_data):
    aligned = address & ~0xFFF
    try:
        uc.mem_map(aligned, 0x1000)
    except Exception:
        pass
    return True

def create_emulator():
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_unmapped)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, ORIG_DATA)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    try:
        val = uc.reg_read(UC_ARM_REG_C1_C0_2)
        uc.reg_write(UC_ARM_REG_C1_C0_2, val | (0xF << 20))
        uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    except Exception:
        pass
    return uc

def test_func_00324b68():
    print("--- Testing func_00324b68 (0x00324b68) ---")
    addr = 0x00324B68
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part11"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_00324b68", tmp)

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)
        try:
            uc.mem_map(0x004D8000, 0x2000)
        except Exception:
            pass
        uc.mem_write(0x004D8B40 + 0x88, b"\xFF" * 4)
        uc.mem_write(0x004D8B40 + 0x740, b"\xFF" * 16)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        b88, b89, b8a = struct.unpack("<BBB", uc.mem_read(0x004D8B40 + 0x88, 3))
        v4 = struct.unpack("<ffff", uc.mem_read(0x004D8B40 + 0x740, 16))
        return (b88, b89, b8a), v4

    orig_b, orig_v = run_one(orig_code)
    decomp_b, decomp_v = run_one(comp)
    assert orig_b == (8, 0, 0) and orig_v == (0.0, 0.0, 0.0, 1.0)
    assert decomp_b == (8, 0, 0) and decomp_v == (0.0, 0.0, 0.0, 1.0)
    print("func_00324b68: PASS")

def test_func_00327b18():
    print("--- Testing func_00327b18 (0x00327b18) ---")
    addr = 0x00327B18
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part11"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_00327b18", tmp)

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)
        try:
            uc.mem_map(0x004D8000, 0x3000)
        except Exception:
            pass
        uc.mem_write(0x004D9270, b"\xFF" * 16)
        uc.mem_write(0x004D8B40 + 0x88, b"\xFF" * 4)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        r0 = uc.reg_read(UC_ARM_REG_R0)
        b88, b89, b8a = struct.unpack("<BBB", uc.mem_read(0x004D8B40 + 0x88, 3))
        v4 = struct.unpack("<ffff", uc.mem_read(0x004D9270, 16))
        return r0, (b88, b89, b8a), v4

    orig_r0, orig_b, orig_v = run_one(orig_code)
    decomp_r0, decomp_b, decomp_v = run_one(comp)
    assert orig_r0 == 0 and orig_b == (8, 0, 0) and orig_v == (0.0, 0.0, 0.0, 0.0)
    assert decomp_r0 == 0 and decomp_b == (8, 0, 0) and decomp_v == (0.0, 0.0, 0.0, 0.0)
    print("func_00327b18: PASS")

def test_func_00340918():
    print("--- Testing func_00340918 (0x00340918) ---")
    addr = 0x00340918
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part11"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_00340918", tmp)

    def run_one(code, a, b, c):
        uc = create_emulator()
        uc.mem_write(addr, code)
        obj = 0x10082000
        uc.mem_write(obj, b"\x00" * 0x30)
        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_R1, a)
        uc.reg_write(UC_ARM_REG_R2, b)
        uc.reg_write(UC_ARM_REG_R3, c)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        w0c, w10, w14 = struct.unpack("<iii", uc.mem_read(obj + 0xC, 12))
        f18, f1c = struct.unpack("<ff", uc.mem_read(obj + 0x18, 8))
        return (w0c, w10, w14), (f18, f1c)

    for a, b, c in [(10, 20, 30), (5, 0, 15), (100, 50, 25)]:
        o_w, o_f = run_one(orig_code, a, b, c)
        d_w, d_f = run_one(comp, a, b, c)
        assert o_w == (a, a + b, a + b + c)
        assert d_w == (a, a + b, a + b + c)
        assert abs(o_f[0] - (1.0 / a)) < 1e-5 and abs(o_f[1] - (1.0 / c)) < 1e-5
        assert abs(d_f[0] - (1.0 / a)) < 1e-5 and abs(d_f[1] - (1.0 / c)) < 1e-5
    print("func_00340918: PASS")

def test_func_00360354():
    print("--- Testing func_00360354 (0x00360354) ---")
    addr = 0x00360354
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part11"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_00360354", tmp)

    def run_one(code, id_val):
        uc = create_emulator()
        uc.mem_write(addr, code)
        obj = 0x10082000
        uc.mem_write(obj, b"\xFF" * 0x70)
        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_R1, id_val)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        w0 = struct.unpack("<I", uc.mem_read(obj, 4))[0]
        floats = struct.unpack("<12f", uc.mem_read(obj + 0x34, 48))
        return w0, floats

    for tid in [0, 42, 0x12345678]:
        o_w, o_fl = run_one(orig_code, tid)
        d_w, d_fl = run_one(comp, tid)
        assert o_w == tid and all(x == 0.0 for x in o_fl)
        assert d_w == tid and all(x == 0.0 for x in d_fl)
    print("func_00360354: PASS")

def test_engine_func_00360780():
    print("--- Testing engine_func_00360780 (0x00360780) ---")
    addr = 0x00360780
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part11"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_00360780", tmp)

    sym_map = {
        "func_00360bcc": 0x00360BCC,
        "engine_func_002bce48": 0x002BCE48,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, old_handle, bcc_res, bcc_handle):
        uc = create_emulator()
        uc.mem_write(addr, code)
        storage = 0x10082000
        uc.mem_write(storage, struct.pack("<I", old_handle))

        closed_handles = []
        bce_errors = []

        def stub_bcc(uc, address, size, user_data):
            out_ptr = uc.reg_read(UC_ARM_REG_R0)
            uc.mem_write(out_ptr, struct.pack("<I", bcc_handle))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_R0, bcc_res)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_bce(uc, address, size, user_data):
            bce_errors.append(uc.reg_read(UC_ARM_REG_R0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def svc_hook(uc, address, size, user_data):
            # Intercept svc 0x23
            inst = struct.unpack("<I", uc.mem_read(address, 4))[0]
            if (inst & 0xFF000000) == 0xEF000000 and (inst & 0xFFFFFF) == 0x23:
                h = uc.reg_read(UC_ARM_REG_R0)
                closed_handles.append(h)
                uc.reg_write(UC_ARM_REG_R0, 0) # svcCloseHandle returns 0
                uc.reg_write(UC_ARM_REG_PC, address + 4)

        uc.hook_add(UC_HOOK_CODE, stub_bcc, None, 0x00360BCC, 0x00360BCC)
        uc.hook_add(UC_HOOK_CODE, stub_bce, None, 0x002BCE48, 0x002BCE48)
        uc.hook_add(UC_HOOK_CODE, svc_hook)

        uc.reg_write(UC_ARM_REG_R0, storage)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        final_h = struct.unpack("<I", uc.mem_read(storage, 4))[0]
        return final_h, closed_handles, bce_errors

    # Case 1: valid old handle, bcc success (res=0, handle=0x111)
    o_h, o_closed, o_err = run_one(orig_code, 0x999, 0, 0x111)
    d_h, d_closed, d_err = run_one(decomp_code, 0x999, 0, 0x111)
    assert o_h == 0x111 and o_closed == [0x999] and o_err == []
    assert d_h == 0x111 and d_closed == [0x999] and d_err == []

    # Case 2: zero old handle, bcc success
    o_h, o_closed, o_err = run_one(orig_code, 0, 0, 0x222)
    d_h, d_closed, d_err = run_one(decomp_code, 0, 0, 0x222)
    assert o_h == 0x222 and o_closed == [] and o_err == []
    assert d_h == 0x222 and d_closed == [] and d_err == []

    # Case 3: bcc error (< 0)
    o_h, o_closed, o_err = run_one(orig_code, 0x777, -1, 0x333)
    d_h, d_closed, d_err = run_one(decomp_code, 0x777, -1, 0x333)
    assert o_h == 0x333 and o_closed == [0x777] and len(o_err) == 1
    assert d_h == 0x333 and d_closed == [0x777] and len(d_err) == 1
    print("engine_func_00360780: PASS")

def main():
    test_func_00324b68()
    test_func_00327b18()
    test_func_00340918()
    test_func_00360354()
    test_engine_func_00360780()
    print("ALL BATCH 31 B PART 11 TESTS PASSED!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
