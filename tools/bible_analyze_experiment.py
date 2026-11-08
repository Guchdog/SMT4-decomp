#!/usr/bin/env python3
"""Differential test runner for bibleAnalyze_Init (0x003a9200, 948 B) against code.bin.

100% file completion milestone for src/camp/bible.cpp.
"""

import struct
import sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.arm_const import *
import unicorn

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "camp" / "bible.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STACK_BASE = 0x0FFF0000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

BUILD_DIR = ROOT / "build" / "bible_analyze_test"

ORIG_DATA = CODE_BIN.read_bytes()

# Stubs
STUB_BASE = 0x004B0000
STUB_MAP = {
    'unite_func_0022e490': STUB_BASE + 0x00,
    'camp_func_0029e01c': STUB_BASE + 0x08,
    'engine_func_00240e1c': STUB_BASE + 0x10,
    'AsdMem_Alloc': STUB_BASE + 0x18,
    'engine_func_002c5978': STUB_BASE + 0x20,
    'camp_func_002c4c00': STUB_BASE + 0x28,
    'AsdMemory_func_002c23f8': STUB_BASE + 0x30,
    'unite_func_002333bc': STUB_BASE + 0x38,
    'unite_func_00233804': STUB_BASE + 0x40,
    'unite_func_0034232c': STUB_BASE + 0x48,
    'unite_func_003a8cc0': STUB_BASE + 0x50,
    'unite_func_003aad60': STUB_BASE + 0x58,
    'unite_func_0022df7c': STUB_BASE + 0x60,
    'unite_func_002338ac': STUB_BASE + 0x68,
    'unite_func_00233600': STUB_BASE + 0x70,
    'camp_func_002976ac': STUB_BASE + 0x78,
    'unite_func_00232800': STUB_BASE + 0x80,
    'vfunc_20': STUB_BASE + 0x88,
    'vfunc_08': STUB_BASE + 0x90,
}

ORIG_ADDR_MAP = {
    0x0022e490: 'unite_func_0022e490',
    0x0029e01c: 'camp_func_0029e01c',
    0x00240e1c: 'engine_func_00240e1c',
    0x002c4b84: 'AsdMem_Alloc',
    0x002c5978: 'engine_func_002c5978',
    0x002c4c00: 'camp_func_002c4c00',
    0x002c23f8: 'AsdMemory_func_002c23f8',
    0x002333bc: 'unite_func_002333bc',
    0x00233804: 'unite_func_00233804',
    0x0034232c: 'unite_func_0034232c',
    0x003a8cc0: 'unite_func_003a8cc0',
    0x003aad60: 'unite_func_003aad60',
    0x0022df7c: 'unite_func_0022df7c',
    0x002338ac: 'unite_func_002338ac',
    0x00233600: 'unite_func_00233600',
    0x002976ac: 'camp_func_002976ac',
    0x00232800: 'unite_func_00232800',
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
        self.next_alloc = 0x00470000

    def handle_call(self, uc, address, size, user_data):
        stub_name = user_data
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        r3 = uc.reg_read(UC_ARM_REG_R3)
        sp = uc.reg_read(UC_ARM_REG_SP)
        stack_args = struct.unpack('<4I', uc.mem_read(sp, 16))
        call_info = {
            'name': stub_name,
            'r0': r0, 'r1': r1, 'r2': r2, 'r3': r3,
            'stack': stack_args,
        }
        if stub_name in ('engine_func_002c5978', 'camp_func_002c4c00'):
            try:
                name_bytes = uc.mem_read(r0, 32).split(b'\x00')[0]
                call_info['task_name'] = name_bytes.decode('ascii', errors='ignore')
            except:
                call_info['task_name'] = ''

        self.calls.append(call_info)

        # Returns
        if stub_name in ('AsdMem_Alloc', 'engine_func_002c4b84'):
            ptr = self.next_alloc
            self.next_alloc += 0x100
            uc.reg_write(UC_ARM_REG_R0, ptr)
        elif stub_name == 'AsdMemory_func_002c23f8':
            ptr = self.next_alloc
            self.next_alloc += 0x100
            uc.reg_write(UC_ARM_REG_R0, ptr)
        elif stub_name in ('engine_func_002c5978', 'camp_func_002c4c00'):
            task_handle = 0x00480000 + len(self.calls) * 0x100
            uc.reg_write(UC_ARM_REG_R0, task_handle)
        elif stub_name == 'unite_func_0034232c':
            # return true for demon IDs 2, 5, 10
            uc.reg_write(UC_ARM_REG_R0, 1 if r0 in (2, 5, 10) else 0)
        elif stub_name == 'unite_func_002333bc':
            uc.reg_write(UC_ARM_REG_R0, r0)
        elif stub_name == 'unite_func_002338ac':
            # return 2 items
            uc.reg_write(UC_ARM_REG_R0, 2)
        else:
            uc.reg_write(UC_ARM_REG_R0, 0)

        lr = uc.reg_read(UC_ARM_REG_LR)
        uc.reg_write(UC_ARM_REG_PC, lr)

def setup_orig_stubs(uc, tracker):
    # Prepare all stub memory with 'bx lr'
    for name, addr in STUB_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1") # bx lr
    for addr, name in ORIG_ADDR_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1") # bx lr
        uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data=name, begin=addr, end=addr)
    # Hook virtual methods so orig also tracks them
    uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data='vfunc_20', begin=STUB_MAP['vfunc_20'], end=STUB_MAP['vfunc_20'])
    uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data='vfunc_08', begin=STUB_MAP['vfunc_08'], end=STUB_MAP['vfunc_08'])

def setup_stubs(uc, tracker):
    for name, addr in STUB_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1") # bx lr
        uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data=name, begin=addr, end=addr)
    # Also hook ORIG_ADDR_MAP in case decompiled code calls hardcoded function pointers
    for addr, name in ORIG_ADDR_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1") # bx lr
        uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data=name, begin=addr, end=addr)

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

def test_bibleanalyze_init():
    print("\n--- Testing bibleAnalyze_Init (0x003a9200, 948 B) ---")
    orig_code = ORIG_DATA[0x003a9200 - CODE_BASE : 0x003a9200 - CODE_BASE + 948]
    decomp_code, relocs, rodata = compile_source(SOURCE, "bibleAnalyze_Init", "bible_analyze_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    extra_syms = {
        'g_BibleAnalyzeManager': 0x0043d990,
    }
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR, extra_syms)

    ADDR_MGR = 0x0043d990
    WORK_ADDR = 0x00450000
    WORK_SIZE = 0xB000 # 44KB

    def run_case(code, addr, is_orig, view_mode):
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

        # Setup dummy vtable for work at 0x00460000
        VTABLE_ADDR = 0x00460000
        vtable_buf = bytearray(0x40)
        # func_20 at vtable + 0x20 points to stub that returns 0
        struct.pack_into('<I', vtable_buf, 0x20, STUB_MAP['vfunc_20'])
        uc.mem_write(VTABLE_ADDR, bytes(vtable_buf))

        # Setup dummy vtable for mode 0 sub-object at 0x00460100
        SUB_VTABLE_ADDR = 0x0042207C
        sub_vtable_buf = bytearray(0x40)
        struct.pack_into('<I', sub_vtable_buf, 0x08, STUB_MAP['vfunc_08'])
        uc.mem_write(SUB_VTABLE_ADDR, bytes(sub_vtable_buf))

        # Initialize work buffer
        work_buf = bytearray(WORK_SIZE)
        struct.pack_into('<I', work_buf, 0x00, VTABLE_ADDR)
        struct.pack_into('<B', work_buf, 0x5a4, view_mode)
        struct.pack_into('<I', work_buf, 0x28, 5) # r3 = 5 (demon count < 10)
        struct.pack_into('<I', work_buf, 0xa5b4, 5) # target demon ID = 5
        # Set up 2 items at work + 0x5a8
        # item 0 at +0x5a8: id at +4 = 0x1234
        # item 1 at +0x5a8 + 32: id at +4 = 0x5678
        struct.pack_into('<h', work_buf, 0x5a8 + 4, 0x1234)
        struct.pack_into('<h', work_buf, 0x5a8 + 32 + 4, 0x5678)

        uc.mem_write(WORK_ADDR, bytes(work_buf))
        uc.mem_write(ADDR_MGR, struct.pack('<I', 0))

        uc.reg_write(UC_ARM_REG_R0, WORK_ADDR)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=1000000)

        # Inspect resulting fields
        res_bytes = uc.mem_read(WORK_ADDR, WORK_SIZE)
        state_flag = res_bytes[0x94]
        val_a5b0 = struct.unpack_from('<H', res_bytes, 0xa5b0)[0]
        val_a6be = res_bytes[0xa6be]
        calc_task = struct.unpack_from('<I', res_bytes, 0x04)[0]
        draw_up = struct.unpack_from('<I', res_bytes, 0x08)[0]
        draw_down = struct.unpack_from('<I', res_bytes, 0x0C)[0]
        flag_14 = struct.unpack_from('<I', res_bytes, 0x14)[0]
        flag_18 = struct.unpack_from('<I', res_bytes, 0x18)[0]
        sub_obj = struct.unpack_from('<I', res_bytes, 0x590)[0]
        flag_56c = res_bytes[0x56c]

        return {
            'state_flag': state_flag,
            'val_a5b0': val_a5b0,
            'val_a6be': val_a6be,
            'has_calc_task': calc_task != 0,
            'has_draw_up': draw_up != 0,
            'has_draw_down': draw_down != 0,
            'flag_14': flag_14,
            'flag_18': flag_18,
            'sub_obj': sub_obj != 0,
            'flag_56c': flag_56c,
        }, tracker.calls

    # Test Mode 1
    f_orig1, c_orig1 = run_case(orig_code, 0x003a9200, True, 1)
    f_dec1, c_dec1 = run_case(patched_code, TARGET_DECOMP, False, 1)

    assert f_orig1 == f_dec1, f"Mode 1 fields mismatch: orig={f_orig1}, dec={f_dec1}"
    assert f_orig1['state_flag'] == 0
    assert f_orig1['val_a5b0'] == 0xFFFF
    assert f_orig1['val_a6be'] == 0xFF
    assert f_orig1['flag_14'] == 0
    assert f_orig1['flag_18'] == 0
    assert f_orig1['flag_56c'] == 1
    assert len(c_orig1) == len(c_dec1), f"Mode 1 calls mismatch: orig={len(c_orig1)}, dec={len(c_dec1)}"
    for i in range(len(c_orig1)):
        assert c_orig1[i]['name'] == c_dec1[i]['name'], f"Call {i} name mismatch: orig={c_orig1[i]['name']}, dec={c_dec1[i]['name']}"
    print(f"  [PASS] Mode 1 (calls={len(c_orig1)}, fields={f_orig1})")

    # Test Mode 0
    f_orig0, c_orig0 = run_case(orig_code, 0x003a9200, True, 0)
    f_dec0, c_dec0 = run_case(patched_code, TARGET_DECOMP, False, 0)

    assert f_orig0 == f_dec0, f"Mode 0 fields mismatch: orig={f_orig0}, dec={f_dec0}"
    assert len(c_orig0) == len(c_dec0), f"Mode 0 calls mismatch: orig={len(c_orig0)}, dec={len(c_dec0)}"
    for i in range(len(c_orig0)):
        assert c_orig0[i]['name'] == c_dec0[i]['name'], f"Call {i} name mismatch: orig={c_orig0[i]['name']}, dec={c_dec0[i]['name']}"
    print(f"  [PASS] Mode 0 (calls={len(c_orig0)}, fields={f_orig0})")

def main():
    print("Testing bibleAnalyze_Init...")
    test_bibleanalyze_init()
    print("\nALL BIBLE ANALYZE INIT TESTS PASSED 100%!")

if __name__ == "__main__":
    main()
