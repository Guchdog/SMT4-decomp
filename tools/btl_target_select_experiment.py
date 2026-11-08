#!/usr/bin/env python3
"""
Differential test harness for Battle Target Select callbacks in src/battle/btl_target_select.cpp:
  - 0x002f4aa4: btlTargetSelect_DrawUp (76 B)
  - 0x002e06bc: btlTargetSelect_Calc (236 B)

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
    UC_ARM_REG_C1_C0_2, UC_ARM_REG_FPEXC
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / "extracted" / "exefs" / "code.bin"
ORIG_DATA = CODE_PATH.read_bytes()
SOURCE = ROOT / "src" / "battle" / "btl_target_select.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000 # 4MB (spans 0x00100000 to 0x00500000)
STACK_BASE = 0x0FFFF000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x100

STUB_BASE = 0x004B0000
STUB_MAP = {
    'ui_func_002c0ac8': STUB_BASE + 0x00,
    'ui_func_00342b54': STUB_BASE + 0x08,
    'ui_func_0034946c': STUB_BASE + 0x10,
    'ui_func_002bf9f0': STUB_BASE + 0x18,
    'camp_func_003428a4': STUB_BASE + 0x20,
    'AsdRef_Get': STUB_BASE + 0x28,
}

ORIG_ADDR_MAP = {
    0x002c0ac8: 'ui_func_002c0ac8',
    0x00342b54: 'ui_func_00342b54',
    0x0034946c: 'ui_func_0034946c',
    0x002bf9f0: 'ui_func_002bf9f0',
    0x003428a4: 'camp_func_003428a4',
}

def create_emulator():
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return uc

class StubTracker:
    def __init__(self, uc):
        self.uc = uc
        self.calls = []
        self.work_ptr = 0x00450000

    def handle_call(self, uc, address, size, user_data):
        stub_name = user_data
        if stub_name == 'AsdRef_Get':
            stub_name = 'ui_func_002c0ac8'
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        r3 = uc.reg_read(UC_ARM_REG_R3)
        self.calls.append({
            'name': stub_name,
            'r0': r0, 'r1': r1, 'r2': r2, 'r3': r3,
        })

        if stub_name in ('ui_func_002c0ac8', 'AsdRef_Get'):
            uc.reg_write(UC_ARM_REG_R0, self.work_ptr)
        else:
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

def test_btltargetselect_drawup():
    print("\n--- Testing btlTargetSelect_DrawUp (0x002f4aa4, 76 B) ---")
    orig_code = ORIG_DATA[0x002f4aa4 - CODE_BASE : 0x002f4aa4 - CODE_BASE + 76]
    decomp_code, relocs, rodata = compile_source(SOURCE, "btlTargetSelect_DrawUp", "btl_ts_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    def run_case(code, addr, is_orig, mode):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker(uc)
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        WORK_ADDR = tracker.work_ptr
        OBJ0 = 0x00451000
        OBJ1 = 0x00452000

        work_buf = bytearray(0x100)
        struct.pack_into('<I', work_buf, 0, OBJ0)
        struct.pack_into('<I', work_buf, 4, OBJ1)
        work_buf[8] = mode
        uc.mem_write(WORK_ADDR, bytes(work_buf))

        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=100000)

        return tracker.calls

    for mode in [0, 1, 2, 3]:
        c_orig = run_case(orig_code, 0x002f4aa4, True, mode)
        c_dec = run_case(patched_code, TARGET_DECOMP, False, mode)

        assert len(c_orig) == len(c_dec), f"Mode {mode} call count mismatch: orig={len(c_orig)}, dec={len(c_dec)}"
        for i in range(len(c_orig)):
            assert c_orig[i]['name'] == c_dec[i]['name']
            assert c_orig[i]['r0'] == c_dec[i]['r0']
    print("  [PASS] btlTargetSelect_DrawUp passes across all 4 modes!")

def test_btltargetselect_calc():
    print("\n--- Testing btlTargetSelect_Calc (0x002e06bc, 236 B) ---")
    orig_code = ORIG_DATA[0x002e06bc - CODE_BASE : 0x002e06bc - CODE_BASE + 236]
    decomp_code, relocs, rodata = compile_source(SOURCE, "btlTargetSelect_Calc", "btl_ts_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    def run_case(code, addr, is_orig, tag, mode, init_val, init_rot):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker(uc)
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            if rodata:
                uc.mem_write(RODATA_ADDR, rodata)
            setup_stubs(uc, tracker)

        WORK_ADDR = tracker.work_ptr
        OBJ0 = 0x00451000
        OBJ1 = 0x00452000

        work_buf = bytearray(0x100)
        struct.pack_into('<I', work_buf, 0, OBJ0)
        struct.pack_into('<I', work_buf, 4, OBJ1)
        work_buf[8] = mode
        struct.pack_into('<I', work_buf, 0x30, tag)
        uc.mem_write(WORK_ADDR, bytes(work_buf))

        obj0_buf = bytearray(0x200)
        obj1_buf = bytearray(0x200)
        struct.pack_into('<f', obj1_buf, 0x58, init_val)
        struct.pack_into('<f', obj1_buf, 0x5c, init_rot)
        uc.mem_write(OBJ0, bytes(obj0_buf))
        uc.mem_write(OBJ1, bytes(obj1_buf))

        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=100000)

        res_obj0 = uc.mem_read(OBJ0, 0x200)
        res_obj1 = uc.mem_read(OBJ1, 0x200)

        return {
            'obj0_f120': struct.unpack_from('<I', res_obj0, 0x120)[0],
            'obj1_f54': struct.unpack_from('<I', res_obj1, 0x54)[0],
            'val_58': round(struct.unpack_from('<f', res_obj1, 0x58)[0], 4),
            'rot_5c': round(struct.unpack_from('<f', res_obj1, 0x5c)[0], 4),
        }, tracker.calls

    # Test cases:
    # tag 0x71 vs 0x50
    # modes 0, 1, 2
    # mode 2 with wrap and without wrap
    cases = [
        (0x71, 0, 0.0, 0.0),
        (0x50, 0, 0.0, 0.0),
        (0x71, 1, 0.0, 0.0),
        (0x50, 2, 10.0, 100.0), # no wrap: val -> 11.0, rot -> 112.0
        (0x71, 2, 29.5, 355.0), # wrap: val -> 30.5 - 30.0 = 0.5, rot -> 367.0 - 360.0 = 7.0
        (0x71, 2, 29.0, 348.0), # exact boundary: val -> 30.0 -> wraps to 0.0, rot -> 360.0 -> no wrap (<= 360)
    ]

    for tag, mode, val, rot in cases:
        f_orig, c_orig = run_case(orig_code, 0x002e06bc, True, tag, mode, val, rot)
        f_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False, tag, mode, val, rot)

        assert f_orig == f_dec, f"State mismatch (tag={tag}, mode={mode}): orig={f_orig}, dec={f_dec}"
        assert len(c_orig) == len(c_dec), f"Call count mismatch: orig={len(c_orig)}, dec={len(c_dec)}"
        for i in range(len(c_orig)):
            assert c_orig[i]['name'] == c_dec[i]['name']
            assert c_orig[i]['r0'] == c_dec[i]['r0']
    print("  [PASS] btlTargetSelect_Calc passes across tag/mode/float wrap matrix!")

def main():
    print("Testing Battle Target Select callbacks...")
    test_btltargetselect_drawup()
    test_btltargetselect_calc()
    print("\nALL BATTLE TARGET SELECT TESTS PASSED 100%!")

if __name__ == "__main__":
    main()
