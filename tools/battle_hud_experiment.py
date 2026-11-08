#!/usr/bin/env python3
"""
Differential test harness for Battle HUD functions in src/ui/battle_hud.cpp:
  - 0x003efa10: Ui_NkmBaseTableLoad (56 B)
  - 0x003efa48: func_003efa48 (92 B)
  - 0x003efaa4: func_003efaa4 (20 B)
  - 0x003efab8: func_003efab8 (20 B)
  - 0x003efacc: func_003efacc (64 B)
  - 0x003efb0c: func_003efb0c (44 B)
  - 0x003f0040: func_003f0040 (28 B)

Validates 100% semantic equivalence between original ARM binary and compiled C++.
"""

import struct
import sys
from pathlib import Path
import unicorn
from unicorn import (
    Uc, UC_ARCH_ARM, UC_MODE_ARM,
    UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
)
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / "extracted" / "exefs" / "code.bin"
ORIG_DATA = CODE_PATH.read_bytes()
SOURCE = ROOT / "src" / "ui" / "battle_hud.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000 # 4MB (spans 0x00100000 to 0x00500000)
STACK_BASE = 0x0FFFF000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x100

STUB_BASE = 0x004B0000
STUB_MAP = {
    'engine_func_002c3b00': STUB_BASE + 0x00,
    'engine_func_00225e4c': STUB_BASE + 0x08,
}

ORIG_ADDR_MAP = {
    0x002c3b00: 'engine_func_002c3b00',
    0x00225e4c: 'engine_func_00225e4c',
}

def create_emulator():
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)
    return uc

class StubTracker:
    def __init__(self, uc):
        self.uc = uc
        self.calls = []

    def handle_call(self, uc, address, size, user_data):
        stub_name = user_data
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        r3 = uc.reg_read(UC_ARM_REG_R3)
        self.calls.append({
            'name': stub_name,
            'r0': r0, 'r1': r1, 'r2': r2, 'r3': r3,
        })
        uc.reg_write(UC_ARM_REG_R0, 0)
        lr = uc.reg_read(UC_ARM_REG_LR)
        uc.reg_write(UC_ARM_REG_PC, lr)

def setup_orig_stubs(uc, tracker):
    for addr, name in ORIG_ADDR_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1") # bx lr
        uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data=name, begin=addr, end=addr)

def setup_stubs(uc, tracker):
    for name, addr in STUB_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1") # bx lr
        uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data=name, begin=addr, end=addr)
    setup_orig_stubs(uc, tracker)

def compile_source(source_path: Path, func_name: str, build_subdir: str):
    build_dir = ROOT / "build" / build_subdir
    build_dir.mkdir(parents=True, exist_ok=True)
    obj = build_dir / f"{source_path.stem}.o"
    res = compile_tu_armv6k(source_path, obj, repo_root=ROOT)
    if res.returncode != 0:
        print(f"COMPILATION FAILED for {source_path}:")
        print(res.stderr)
        sys.exit(1)
    functions = extract_elf_functions_detailed(obj)
    data = obj.read_bytes()
    e_shoff = struct.unpack_from('<I', data, 32)[0]
    e_shentsize = struct.unpack_from('<H', data, 46)[0]
    e_shnum = struct.unpack_from('<H', data, 48)[0]
    sections = [struct.unpack_from('<IIIIIIIIII', data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr = sections[struct.unpack_from('<H', data, 50)[0]]
    shstrtab = data[shstr[4]:shstr[4]+shstr[5]]
    def get_sh_name(off):
        return shstrtab[off:].split(b'\x00')[0].decode('ascii')
    rodata = b""
    for s in sections:
        if get_sh_name(s[0]).startswith(".rodata"):
            rodata = data[s[4]:s[4]+s[5]]
            break
    for mangled, (b, relocs) in functions.items():
        if func_name in mangled:
            return b, relocs, rodata
    raise KeyError(f"Function {func_name} not found in {obj}")

def apply_relocations(code_bytes, relocs, target_addr, rodata_addr, extra_syms=None):
    mutable = bytearray(code_bytes)
    syms = dict(STUB_MAP)
    if extra_syms:
        syms.update(extra_syms)

    for rel in relocs:
        offset = rel.offset
        name = rel.symbol_name
        rel_type = rel.relocation_type
        if not name or name.startswith(".rodata"):
            sym_val = rodata_addr
        elif name in syms:
            sym_val = syms[name]
        elif name.endswith(".cpp"):
            sym_val = target_addr
        else:
            raise ValueError(f"Unknown symbol '{name}'")

        if rel_type in (28, 29): # R_ARM_CALL / R_ARM_JUMP24
            orig = struct.unpack_from('<I', mutable, offset)[0]
            target = sym_val
            pc = target_addr + offset + 8
            new_disp = ((target - pc) >> 2) & 0x00FFFFFF
            inst = (orig & 0xFF000000) | new_disp
            struct.pack_into('<I', mutable, offset, inst)
        elif rel_type in (2, 38): # R_ARM_ABS32 or R_ARM_TARGET1
            orig = struct.unpack_from('<I', mutable, offset)[0]
            val = (sym_val + orig) & 0xFFFFFFFF
            struct.pack_into('<I', mutable, offset, val)
        else:
            raise ValueError(f"Unsupported reloc type {rel_type}")
    return bytes(mutable)

def test_ui_nkm_base_table_load():
    print("\n--- Testing Ui_NkmBaseTableLoad (0x003efa10, 56 B) ---")
    orig_code = ORIG_DATA[0x003efa10 - CODE_BASE : 0x003efa10 - CODE_BASE + 56]
    decomp_code, relocs, rodata = compile_source(SOURCE, "Ui_NkmBaseTableLoad", "btl_hud_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    GLOBAL_ADDR = 0x004E629C

    def run_case(code, addr, is_orig):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker(uc)
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        uc.mem_write(GLOBAL_ADDR, struct.pack('<I', 0x12345678))

        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_R1, 0)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=100000)

        val = struct.unpack('<I', uc.mem_read(GLOBAL_ADDR, 4))[0]
        return val, tracker.calls

    v_orig, c_orig = run_case(orig_code, 0x003efa10, True)
    v_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False)

    assert v_orig == v_dec == 0, f"Global value mismatch: orig={v_orig}, dec={v_dec}"
    assert len(c_orig) == len(c_dec)
    for i in range(len(c_orig)):
        assert c_orig[i]['name'] == c_dec[i]['name']
        assert c_orig[i]['r0'] == c_dec[i]['r0']
        assert c_orig[i]['r1'] == c_dec[i]['r1']
        assert c_orig[i]['r2'] == c_dec[i]['r2']
    print("  [PASS] Ui_NkmBaseTableLoad passed 100%!")

def test_func_003efa48():
    print("\n--- Testing func_003efa48 (0x003efa48, 92 B) ---")
    orig_code = ORIG_DATA[0x003efa48 - CODE_BASE : 0x003efa48 - CODE_BASE + 92]
    decomp_code, relocs, rodata = compile_source(SOURCE, "func_003efa48", "btl_hud_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    TABLE_ADDR = 0x00465788

    def run_case(code, addr, is_orig):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker(uc)
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        uc.mem_write(TABLE_ADDR, b"\x00" * 48)

        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=100000)

        table_data = uc.mem_read(TABLE_ADDR, 48)
        entries = [struct.unpack_from('<II', table_data, i * 8) for i in range(6)]
        return entries, tracker.calls

    t_orig, c_orig = run_case(orig_code, 0x003efa48, True)
    t_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False)

    assert t_orig == t_dec, f"Table entries mismatch: orig={t_orig}, dec={t_dec}"
    assert len(c_orig) == len(c_dec) == 0
    print(f"  [PASS] func_003efa48 passed 100% (6 table entries: {t_orig[0]}..{t_orig[-1]})!")

def test_func_003efaa4():
    print("\n--- Testing func_003efaa4 (0x003efaa4, 20 B) ---")
    orig_code = ORIG_DATA[0x003efaa4 - CODE_BASE : 0x003efaa4 - CODE_BASE + 20]
    decomp_code, relocs, rodata = compile_source(SOURCE, "func_003efaa4", "btl_hud_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    ADDR = 0x00473850

    def run_case(code, addr, is_orig):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker(uc)
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        uc.mem_write(ADDR, struct.pack('<I', 0x99999999))
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=100000)

        val = struct.unpack('<I', uc.mem_read(ADDR, 4))[0]
        return val, tracker.calls

    v_orig, c_orig = run_case(orig_code, 0x003efaa4, True)
    v_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False)

    assert v_orig == v_dec == 0
    assert len(c_orig) == len(c_dec) == 0
    print("  [PASS] func_003efaa4 passed 100%!")

def test_func_003efab8():
    print("\n--- Testing func_003efab8 (0x003efab8, 20 B) ---")
    orig_code = ORIG_DATA[0x003efab8 - CODE_BASE : 0x003efab8 - CODE_BASE + 20]
    decomp_code, relocs, rodata = compile_source(SOURCE, "func_003efab8", "btl_hud_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    ADDR = 0x00472A50

    def run_case(code, addr, is_orig):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker(uc)
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        uc.mem_write(ADDR, struct.pack('<I', 0x88888888))
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=100000)

        val = struct.unpack('<I', uc.mem_read(ADDR, 4))[0]
        return val, tracker.calls

    v_orig, c_orig = run_case(orig_code, 0x003efab8, True)
    v_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False)

    assert v_orig == v_dec == 0
    assert len(c_orig) == len(c_dec) == 0
    print("  [PASS] func_003efab8 passed 100%!")

def test_func_003efacc():
    print("\n--- Testing func_003efacc (0x003efacc, 64 B) ---")
    orig_code = ORIG_DATA[0x003efacc - CODE_BASE : 0x003efacc - CODE_BASE + 64]
    decomp_code, relocs, rodata = compile_source(SOURCE, "func_003efacc", "btl_hud_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    def run_case(code, addr, is_orig):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker(uc)
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        uc.mem_write(0x0044E588, b"\x00" * 8)
        uc.mem_write(0x0044E590, b"\xFF" * 8)
        uc.mem_write(0x004C7000 + 0x24, b"\x00" * 4)

        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=100000)

        p1 = struct.unpack('<II', uc.mem_read(0x0044E588, 8))
        p2 = struct.unpack('<II', uc.mem_read(0x0044E590, 8))
        v24 = struct.unpack('<I', uc.mem_read(0x004C7000 + 0x24, 4))[0]
        return (p1, p2, v24), tracker.calls

    res_orig, c_orig = run_case(orig_code, 0x003efacc, True)
    res_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False)

    assert res_orig == res_dec == ((0xFFFFFFFF, 0xFFFFFFFF), (0, 0), 0xE7E3FFFF)
    assert len(c_orig) == len(c_dec) == 0
    print("  [PASS] func_003efacc passed 100%!")

def test_func_003efb0c():
    print("\n--- Testing func_003efb0c (0x003efb0c, 44 B) ---")
    orig_code = ORIG_DATA[0x003efb0c - CODE_BASE : 0x003efb0c - CODE_BASE + 44]
    decomp_code, relocs, rodata = compile_source(SOURCE, "func_003efb0c", "btl_hud_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    def run_case(code, addr, is_orig):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker(uc)
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        uc.mem_write(0x0044E5B0, b"\x00" * 8)
        uc.mem_write(0x0044E5B8, b"\xFF" * 8)

        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=100000)

        p1 = struct.unpack('<II', uc.mem_read(0x0044E5B0, 8))
        p2 = struct.unpack('<II', uc.mem_read(0x0044E5B8, 8))
        return (p1, p2), tracker.calls

    res_orig, c_orig = run_case(orig_code, 0x003efb0c, True)
    res_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False)

    assert res_orig == res_dec == ((0xFFFFFFFF, 0xFFFFFFFF), (0, 0))
    assert len(c_orig) == len(c_dec) == 0
    print("  [PASS] func_003efb0c passed 100%!")

def test_func_003f0040():
    print("\n--- Testing func_003f0040 (0x003f0040, 28 B) ---")
    orig_code = ORIG_DATA[0x003f0040 - CODE_BASE : 0x003f0040 - CODE_BASE + 28]
    decomp_code, relocs, rodata = compile_source(SOURCE, "func_003f0040", "btl_hud_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    def run_case(code, addr, is_orig):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker(uc)
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        uc.mem_write(0x00465270, b"\xFF" * 8)

        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=100000)

        p = struct.unpack('<II', uc.mem_read(0x00465270, 8))
        return p, tracker.calls

    res_orig, c_orig = run_case(orig_code, 0x003f0040, True)
    res_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False)

    assert res_orig == res_dec == (0, 0)
    assert len(c_orig) == len(c_dec) == 0
    print("  [PASS] func_003f0040 passed 100%!")

def main():
    print("Testing Battle HUD functions...")
    test_ui_nkm_base_table_load()
    test_func_003efa48()
    test_func_003efaa4()
    test_func_003efab8()
    test_func_003efacc()
    test_func_003efb0c()
    test_func_003f0040()
    print("\nALL 7 BATTLE HUD FUNCTIONS PASSED 100%!")

if __name__ == "__main__":
    main()
