#!/usr/bin/env python3
"""Differential test for batch 30 B part 20:
- camp_func_002fc9d4 (0x002FC9D4, 112 B)
- engine_func_002febb4 (0x002FEBB4, 112 B)
- script_vm_func_002fec44 (0x002FEC44, 124 B)
- battle_func_002fff20 (0x002FFF20, 112 B)
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
    uc.mem_map(STACK_BASE, STACK_SIZE)
    try:
        val = uc.reg_read(UC_ARM_REG_C1_C0_2)
        uc.reg_write(UC_ARM_REG_C1_C0_2, val | (0xF << 20))
        uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    except Exception:
        pass
    return uc

def test_camp_func_002fc9d4():
    print("--- Testing camp_func_002fc9d4 ---")
    addr = 0x002FC9D4
    size = 112
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_part20"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_002fc9d4", tmp)

    sym_map = {
        "battle_func_0028ec78": 0x0028EC78,
        "camp_func_0028fde4": 0x0028FDE4,
        "ui_func_00250fc4": 0x00250FC4,
        "camp_func_002a0fac": 0x002A0FAC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    DATA_PAGE = 0x08000000
    BUF_PAGE = 0x08100000

    def run_one(code: bytes, active_ids: set[int]):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.mem_map(DATA_PAGE, 0x10000)
        uc.mem_map(BUF_PAGE, 0x10000)

        recorded_calls = []

        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x0028EC78:
                ret = 1 if r0 in active_ids else 0
                uc.reg_write(UC_ARM_REG_R0, ret)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x0028FDE4:
                uc.reg_write(UC_ARM_REG_R0, r0 + 0x1000)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x00250FC4:
                recorded_calls.append((r0, r1))
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002A0FAC:
                uc.reg_write(UC_ARM_REG_R0, BUF_PAGE)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x0028EC78, end=0x0028EC78)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x0028FDE4, end=0x0028FDE4)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00250FC4, end=0x00250FC4)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002A0FAC, end=0x002A0FAC)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        # Clear buffer
        uc.mem_write(BUF_PAGE, b"\x00" * 0x1000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        buf = bytes(uc.mem_read(BUF_PAGE, 0x200))
        return res, recorded_calls, buf

    cases = [
        set(),
        {0x79F},
        {0x79F + 0x63},
        {0x79F, 0x7A0, 0x7D0, 0x802},
        set(range(0x79F, 0x79F + 0x64)),
    ]

    for c in cases:
        r1, calls1, buf1 = run_one(orig_code, c)
        r2, calls2, buf2 = run_one(decomp_code, c)
        assert r1 == r2 == 1
        assert calls1 == calls2, f"calls mismatch: {calls1} vs {calls2}"
        assert buf1 == buf2, f"buffer mismatch"

    print("camp_func_002fc9d4: PASS")

def test_engine_func_002febb4():
    print("--- Testing engine_func_002febb4 ---")
    addr = 0x002FEBB4
    size = 112
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_part20"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_002febb4", tmp)

    sym_map = {
        "engine_func_00296f60": 0x00296F60,
        "shop_func_002ae650": 0x002AE650,
        "engine_func_003a63d0": 0x003A63D0,
        "shop_func_002466dc": 0x002466DC,
        "battle_func_0028df54": 0x0028DF54,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, p0_val: int, ae_val: int, stack_init: bytes):
        uc = create_emulator()
        uc.mem_write(addr, code)

        recorded_3a = []
        recorded_shop = []
        recorded_df = []

        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00296F60:
                uc.reg_write(UC_ARM_REG_R0, p0_val)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002AE650:
                uc.reg_write(UC_ARM_REG_R0, ae_val)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x003A63D0:
                recorded_3a.append((r0, r1, r2, r3))
                uc.reg_write(UC_ARM_REG_R0, (r0 ^ 0x1234) & 0xFFFF)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002466DC:
                data = bytes(uc.mem_read(r0, 4))
                id_val, flags_val = struct.unpack("<HH", data)
                recorded_shop.append((id_val, flags_val))
                uc.reg_write(UC_ARM_REG_R0, (id_val + 7) & 1)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x0028DF54:
                recorded_df.append(r0)
                uc.reg_write(UC_ARM_REG_PC, lr)

        for a in (0x00296F60, 0x002AE650, 0x003A63D0, 0x002466DC, 0x0028DF54):
            uc.hook_add(UC_HOOK_CODE, stub_hook, begin=a, end=a)

        sp = STACK_BASE + 0x8000
        uc.mem_write(sp - 0x100, stack_init * 16)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, recorded_3a, recorded_shop, recorded_df

    cases = [
        (100, 9, b"\xaa\xbb\xcc\xdd"),
        (200, 0, b"\x11\x22\x33\x44"),
        (0x5678, 9, b"\x00\x00\xff\xff"),
        (0xABCD, 5, b"\x55\xaa\x55\xaa"),
    ]

    for p0, ae, st in cases:
        r1, t1, s1, d1 = run_one(orig_code, p0, ae, st)
        r2, t2, s2, d2 = run_one(decomp_code, p0, ae, st)
        assert r1 == r2 == 1
        assert t1 == t2, f"3a mismatch: {t1} vs {t2}"
        assert s1 == s2, f"shop mismatch: {s1} vs {s2}"
        assert d1 == d2, f"df mismatch: {d1} vs {d2}"

    print("engine_func_002febb4: PASS")

def test_script_vm_func_002fec44():
    print("--- Testing script_vm_func_002fec44 ---")
    addr = 0x002FEC44
    size = 124
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_part20"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_002fec44", tmp)

    sym_map = {
        "script_vm_func_00299224": 0x00299224,
        "script_vm_func_002509d8": 0x002509D8,
        "script_vm_func_002900b0": 0x002900B0,
        "camp_func_002bdac0": 0x002BDAC0,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    PTR_PAGE = 0x00430000
    CTX_PAGE = 0x08200000

    def run_one(code: bytes, arg0: int):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.mem_map(CTX_PAGE, 0x10000)

        uc.mem_write(0x0043DD50, struct.pack("<I", CTX_PAGE))

        ctx_init = bytearray(0x2000)
        struct.pack_into("<I", ctx_init, 4, 0x55AA1234)
        uc.mem_write(CTX_PAGE, bytes(ctx_init))

        calls = []

        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00299224:
                calls.append(("99224", r0))
                uc.reg_write(UC_ARM_REG_R0, (r0 + 0x42) & 0xFF)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002509D8:
                calls.append(("509d8",))
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002900B0:
                calls.append(("900b0", r0, r1))
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002BDAC0:
                calls.append(("bdac0", r0 - CTX_PAGE, r1, r2))
                uc.reg_write(UC_ARM_REG_PC, lr)

        for a in (0x00299224, 0x002509D8, 0x002900B0, 0x002BDAC0):
            uc.hook_add(UC_HOOK_CODE, stub_hook, begin=a, end=a)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        ctx_out = bytes(uc.mem_read(CTX_PAGE, 0x1000))
        return calls, ctx_out

    for arg in (0, 1, 0x1234, 0xABCD, 0xFFFF):
        c1, out1 = run_one(orig_code, arg)
        c2, out2 = run_one(decomp_code, arg)
        assert c1 == c2, f"calls mismatch: {c1} vs {c2}"
        assert out1 == out2, f"ctx mismatch for arg {hex(arg)}"

    print("script_vm_func_002fec44: PASS")

def test_battle_func_002fff20():
    print("--- Testing battle_func_002fff20 ---")
    addr = 0x002FFF20
    size = 112
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_part20"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_002fff20", tmp)

    sym_map = {
        "ui_func_00293c98": 0x00293C98,
        "script_vm_func_00336cb8": 0x00336CB8,
        "script_vm_func_002b6e60": 0x002B6E60,
        "battle_func_002b6d94": 0x002B6D94,
        "battle_func_00294568": 0x00294568,
        "func_003ae840": 0x003AE840,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    UI_PAGE = 0x08300000
    P1_PAGE = 0x08400000
    P3_PAGE = 0x08500000
    G_PAGE = 0x00430000

    def run_one(code: bytes, val4: int, val6: int, val5a: int, initial_flags: int):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.mem_map(UI_PAGE, 0x10000)
        uc.mem_map(P1_PAGE, 0x10000)
        uc.mem_map(P3_PAGE, 0x10000)

        uc.mem_write(0x00439CA8, struct.pack("<I", 0x12345678))
        uc.mem_write(UI_PAGE + 0x44A0, struct.pack("<I", initial_flags))
        uc.mem_write(P1_PAGE + 0x604, struct.pack("<hH", val4, val6))
        uc.mem_write(P3_PAGE + 0x5A, struct.pack("<H", val5a))

        calls = []

        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00293C98:
                uc.reg_write(UC_ARM_REG_R0, UI_PAGE)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x00336CB8:
                calls.append(("336cb8",))
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002B6E60:
                uc.reg_write(UC_ARM_REG_R0, P1_PAGE)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002B6D94:
                calls.append(("b6d94", r0, r1))
                uc.reg_write(UC_ARM_REG_R0, P3_PAGE)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x00294568:
                calls.append(("94568", r0, r1))
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x003AE840:
                calls.append(("ae840", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        for a in (0x00293C98, 0x00336CB8, 0x002B6E60, 0x002B6D94, 0x00294568, 0x003AE840):
            uc.hook_add(UC_HOOK_CODE, stub_hook, begin=a, end=a)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        flags_out = struct.unpack("<I", uc.mem_read(UI_PAGE + 0x44A0, 4))[0]
        return res, calls, flags_out

    cases = [
        (10, 20, 5, 0),
        (-5, 0x1234, 0, 0x1000),
        (300, 400, 0x7FFF, 0x01000000),
        (-32768, 65535, 100, 0x02000000),
    ]

    for v4, v6, v5a, init_fl in cases:
        r1, c1, fl1 = run_one(orig_code, v4, v6, v5a, init_fl)
        r2, c2, fl2 = run_one(decomp_code, v4, v6, v5a, init_fl)
        assert r1 == r2 == 1
        assert c1 == c2, f"calls mismatch: {c1} vs {c2}"
        assert fl1 == fl2, f"flags mismatch: {hex(fl1)} vs {hex(fl2)}"

    print("battle_func_002fff20: PASS")

if __name__ == "__main__":
    test_camp_func_002fc9d4()
    test_engine_func_002febb4()
    test_script_vm_func_002fec44()
    test_battle_func_002fff20()
    print("\nALL 4 FUNCTIONS IN BATCH 30 B PART 20 PASSED WITH 100% DIFFERENTIAL FIDELITY!")
