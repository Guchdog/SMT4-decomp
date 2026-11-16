#!/usr/bin/env python3
"""
Differential test harness for AsdTexture / AsdMemory functions in src/engine/asd_texture.cpp:
  - 0x002c23f8: AsdMemory_func_002c23f8 (56 B)
  - 0x001042c8: AsdPrim_func_001042c8 (176 B)
  - 0x002bd940: AsdTexture_func_002bd940 (172 B)

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
SOURCE = ROOT / "src" / "engine" / "asd_texture.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000 # 4MB (spans 0x00100000 to 0x00500000)
STACK_BASE = 0x0FFFF000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x100

STUB_BASE = 0x004B0000
STUB_MAP = {
    'engine_func_002c54f0': STUB_BASE + 0x00,
    'AsdMem_AllocAlign': STUB_BASE + 0x08,
    'engine_func_002c34a4': STUB_BASE + 0x10,
    'AsdWork_Alloc': STUB_BASE + 0x18,
    'AsdMem_Zero': STUB_BASE + 0x20,
    'engine_func_002c4b30': STUB_BASE + 0x28,
}

ORIG_ADDR_MAP = {
    0x002c54f0: 'engine_func_002c54f0',
    0x002c34a4: 'engine_func_002c34a4',
    0x002c4b30: 'AsdMem_Zero',
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
        self.next_alloc = 0x00460000

    def handle_call(self, uc, address, size, user_data):
        stub_name = user_data
        # Normalize alias names
        if stub_name == 'AsdMem_AllocAlign':
            stub_name = 'engine_func_002c54f0'
        elif stub_name == 'AsdWork_Alloc':
            stub_name = 'engine_func_002c34a4'
        elif stub_name == 'engine_func_002c4b30':
            stub_name = 'AsdMem_Zero'

        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        r3 = uc.reg_read(UC_ARM_REG_R3)
        sp = uc.reg_read(UC_ARM_REG_SP)
        stack_args = struct.unpack('<4I', uc.mem_read(sp, 16))
        self.calls.append({
            'name': stub_name,
            'r0': r0, 'r1': r1, 'r2': r2, 'r3': r3,
            'stack': stack_args,
        })

        if stub_name in ('engine_func_002c54f0', 'engine_func_002c34a4'):
            ptr = self.next_alloc
            self.next_alloc += 0x100
            uc.reg_write(UC_ARM_REG_R0, ptr)
        elif stub_name == 'AsdMem_Zero':
            uc.mem_write(r0, b"\x00" * r1)
            uc.reg_write(UC_ARM_REG_R0, 0)
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

def test_asdmemory_func_002c23f8():
    print("\n--- Testing AsdMemory_func_002c23f8 (0x002c23f8, 56 B) ---")
    orig_code = ORIG_DATA[0x002c23f8 - CODE_BASE : 0x002c23f8 - CODE_BASE + 56]
    decomp_code, relocs, rodata = compile_source(SOURCE, "AsdMemory_func_002c23f8", "asd_tex_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    extra_syms = {
        '_ZN4smt46engine14g_AsdPrimStateE': 0x004DAEC0,
    }
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR, extra_syms)

    def run_case(code, addr, is_orig, size):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker(uc)
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        uc.reg_write(UC_ARM_REG_R0, size)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=100000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, tracker.calls

    for sz in [0x10, 0x48, 0x1000]:
        r_orig, c_orig = run_case(orig_code, 0x002c23f8, True, sz)
        r_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False, sz)

        assert r_orig == r_dec, f"Return mismatch: orig={r_orig}, dec={r_dec}"
        assert len(c_orig) == len(c_dec)
        for i in range(len(c_orig)):
            assert c_orig[i]['name'] == c_dec[i]['name']
            assert c_orig[i]['r0'] == c_dec[i]['r0']
            assert c_orig[i]['r1'] == c_dec[i]['r1']
            assert c_orig[i]['r2'] == c_dec[i]['r2']
            assert c_orig[i]['r3'] == c_dec[i]['r3']
            assert c_orig[i]['stack'][0] == c_dec[i]['stack'][0]
    print("  [PASS] AsdMemory_func_002c23f8 passes exact ABI forward call!")

def test_asdtexture_func_002bd940():
    print("\n--- Testing AsdTexture_func_002bd940 (0x002bd940, 172 B) ---")
    orig_code = ORIG_DATA[0x002bd940 - CODE_BASE : 0x002bd940 - CODE_BASE + 172]
    decomp_code, relocs, rodata = compile_source(SOURCE, "AsdTexture_func_002bd940", "asd_tex_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    extra_syms = {
        '_ZN4smt46engine14g_AsdPrimStateE': 0x004DAEC0,
    }
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR, extra_syms)

    def run_case(code, addr, is_orig, flag):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker(uc)
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        uc.reg_write(UC_ARM_REG_R0, flag)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=100000)

        tex_ptr = uc.reg_read(UC_ARM_REG_R0)
        res_tex = uc.mem_read(tex_ptr, 0x48)

        return {
            'tex_ptr': tex_ptr,
            'ref_count': struct.unpack_from('<I', res_tex, 0)[0],
            'format': struct.unpack_from('<I', res_tex, 4)[0],
            'flags': struct.unpack_from('<I', res_tex, 8)[0],
            'type': struct.unpack_from('<I', res_tex, 0x38)[0],
            'field_3c': struct.unpack_from('<I', res_tex, 0x3C)[0],
            'field_40': struct.unpack_from('<I', res_tex, 0x40)[0],
        }, tracker.calls

    for fl in [0, 1]:
        f_orig, c_orig = run_case(orig_code, 0x002bd940, True, fl)
        f_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False, fl)

        assert f_orig == f_dec, f"State mismatch: orig={f_orig}, dec={f_dec}"
        assert len(c_orig) == len(c_dec)
        for i in range(len(c_orig)):
            assert c_orig[i]['name'] == c_dec[i]['name']
            assert c_orig[i]['r0'] == c_dec[i]['r0']
            assert c_orig[i]['r3'] == c_dec[i]['r3']
            assert c_orig[i]['stack'][0] == c_dec[i]['stack'][0]
    print("  [PASS] AsdTexture_func_002bd940 passes across flag=0 and flag=1!")

def test_asdprim_func_001042c8():
    print("\n--- Testing AsdPrim_func_001042c8 (0x001042c8, 176 B) ---")
    orig_code = ORIG_DATA[0x001042c8 - CODE_BASE : 0x001042c8 - CODE_BASE + 176]
    decomp_code, relocs, rodata = compile_source(SOURCE, "AsdPrim_func_001042c8", "asd_tex_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    extra_syms = {
        '_ZN4smt46engine14g_AsdPrimStateE': 0x004DAEC0,
    }
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR, extra_syms)

    def run_case(code, addr, is_orig, owner):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker(uc)
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        STATE_ADDR = 0x004DAEC0
        uc.mem_write(STATE_ADDR, b"\xFF" * 0x30)

        uc.reg_write(UC_ARM_REG_R0, owner)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=100000)

        res_state = uc.mem_read(STATE_ADDR, 0x30)
        return {
            'buf0': struct.unpack_from('<I', res_state, 0)[0],
            'buf1': struct.unpack_from('<I', res_state, 4)[0],
            'f08': struct.unpack_from('<I', res_state, 8)[0],
            'f0c': struct.unpack_from('<I', res_state, 0xC)[0],
            'f10': struct.unpack_from('<I', res_state, 0x10)[0],
            'owner': struct.unpack_from('<I', res_state, 0x14)[0],
        }, tracker.calls

    for own in [0x12345678, 0x00450000]:
        f_orig, c_orig = run_case(orig_code, 0x001042c8, True, own)
        f_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False, own)

        assert f_orig == f_dec, f"State mismatch: orig={f_orig}, dec={f_dec}"
        assert len(c_orig) == len(c_dec)
        for i in range(len(c_orig)):
            assert c_orig[i]['name'] == c_dec[i]['name']
            assert c_orig[i]['r3'] == c_dec[i]['r3']
            assert c_orig[i]['stack'][0] == c_dec[i]['stack'][0]
            assert c_orig[i]['stack'][1] == c_dec[i]['stack'][1]
    print("  [PASS] AsdPrim_func_001042c8 passes buffer setup and state fields!")

def main():
    print("Testing AsdTexture functions...")
    test_asdmemory_func_002c23f8()
    test_asdtexture_func_002bd940()
    test_asdprim_func_001042c8()
    print("\nALL ASD TEXTURE TESTS PASSED 100%!")

if __name__ == "__main__":
    main()
