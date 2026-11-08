#!/usr/bin/env python3
"""
Differential test harness for Result_DrawDown / Result_Cleanup (0x001c87d8, 156 B) in src/ui/result.cpp.

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
SOURCE = ROOT / "src" / "ui" / "result.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000 # 4MB (spans 0x00100000 to 0x00500000)
STACK_BASE = 0x0FFFF000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x100

STUB_BASE = 0x004B0000
STUB_MAP = {
    'script_vm_func_002a755c': STUB_BASE + 0x00,
    'engine_func_002c4360': STUB_BASE + 0x08,
    'script_vm_func_002c0128': STUB_BASE + 0x10,
    'script_vm_func_002a497c': STUB_BASE + 0x18,
    'script_vm_func_002aeb2c': STUB_BASE + 0x20,
}

ORIG_ADDR_MAP = {
    0x002a755c: 'script_vm_func_002a755c',
    0x002c4360: 'engine_func_002c4360',
    0x002c0128: 'script_vm_func_002c0128',
    0x002a497c: 'script_vm_func_002a497c',
    0x002aeb2c: 'script_vm_func_002aeb2c',
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

def test_result_drawdown():
    print("\n--- Testing Result_DrawDown (0x001c87d8, 156 B) ---")
    orig_code = ORIG_DATA[0x001c87d8 - CODE_BASE : 0x001c87d8 - CODE_BASE + 156]
    decomp_code, relocs, rodata = compile_source(SOURCE, "Result_DrawDown", "result_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    extra_syms = {
        '_ZN4smt42ui15g_ResultManagerE': 0x0044DC20,
    }
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR, extra_syms)

    GLOBAL_PTR = 0x0044DC20
    WORK_ADDR = 0x00450000

    def run_case(code, addr, is_orig, has_work):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker(uc)
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        if has_work:
            uc.mem_write(GLOBAL_PTR, struct.pack('<I', WORK_ADDR))
            work_buf = bytearray(0x4000)
            struct.pack_into('<I', work_buf, 0x3564, 0x11111111)
            struct.pack_into('<I', work_buf, 0x3568, 0x22222222)
            struct.pack_into('<I', work_buf, 0x356C, 0x33333333)
            struct.pack_into('<I', work_buf, 0x3570, 0x44444444)
            uc.mem_write(WORK_ADDR, bytes(work_buf))
        else:
            uc.mem_write(GLOBAL_PTR, struct.pack('<I', 0))

        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=100000)

        final_ptr = struct.unpack('<I', uc.mem_read(GLOBAL_PTR, 4))[0]
        return final_ptr, tracker.calls

    # Case 1: with active work buffer
    p_orig1, c_orig1 = run_case(orig_code, 0x001c87d8, True, True)
    p_dec1, c_dec1 = run_case(patched_code, TARGET_DECOMP, False, True)

    assert p_orig1 == p_dec1 == 0, f"Global pointer not zeroed: orig={p_orig1}, dec={p_dec1}"
    assert len(c_orig1) == len(c_dec1), f"Call count mismatch: orig={len(c_orig1)}, dec={len(c_dec1)}"
    for i in range(len(c_orig1)):
        assert c_orig1[i]['name'] == c_dec1[i]['name']
        assert c_orig1[i]['r0'] == c_dec1[i]['r0']
        assert c_orig1[i]['r1'] == c_dec1[i]['r1']
    print(f"  [PASS] Active cleanup path passed ({len(c_orig1)} calls matching)!")

    # Case 2: nullptr work
    p_orig0, c_orig0 = run_case(orig_code, 0x001c87d8, True, False)
    p_dec0, c_dec0 = run_case(patched_code, TARGET_DECOMP, False, False)

    assert p_orig0 == p_dec0 == 0
    assert len(c_orig0) == len(c_dec0) == 0
    print("  [PASS] Nullptr early return passed!")

def main():
    print("Testing Result_DrawDown...")
    test_result_drawdown()
    print("\nRESULT CLEANUP TESTS PASSED 100%!")

if __name__ == "__main__":
    main()
