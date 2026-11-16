#!/usr/bin/env python3
"""Differential test runner for Cathedral of Shadows and UI task init candidates against code.bin.

Tests:
  - 0x0010299c: IfTouch_Init (260 B) in src/ui/tbb_loader.cpp
  - 0x00269cc8: bibleMain_Init (352 B) in src/camp/bible.cpp
  - 0x002e315c: UniteEffect_Init (344 B) in src/camp/unite.cpp
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
CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STACK_BASE = 0x0FFF0000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

ORIG_DATA = CODE_BIN.read_bytes()

# Stubs
STUB_BASE = 0x004B0000
STUB_MAP = {
    'engine_func_002c4b84': STUB_BASE + 0x00,
    'engine_func_002c4b30': STUB_BASE + 0x08,
    'engine_func_002c5978': STUB_BASE + 0x10,
    'engine_func_002c583c': STUB_BASE + 0x18,
    'camp_func_002c4c00': STUB_BASE + 0x20,
    'btlTalkBustUp_func_002959c4': STUB_BASE + 0x28,
    'script_vm_func_002c0128': STUB_BASE + 0x30,
    'camp_func_002976ac': STUB_BASE + 0x38,
}

ORIG_ADDR_MAP = {
    0x002c4b84: 'engine_func_002c4b84',
    0x002c4b30: 'engine_func_002c4b30',
    0x002c5978: 'engine_func_002c5978',
    0x002c583c: 'engine_func_002c583c',
    0x002c4c00: 'camp_func_002c4c00',
    0x002959c4: 'btlTalkBustUp_func_002959c4',
    0x002c0128: 'script_vm_func_002c0128',
    0x002976ac: 'camp_func_002976ac',
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
            # Read name string from r0
            try:
                name_bytes = uc.mem_read(r0, 32).split(b'\x00')[0]
                call_info['task_name'] = name_bytes.decode('ascii', errors='ignore')
            except:
                call_info['task_name'] = ''

        self.calls.append(call_info)

        # Handle returns
        if stub_name == 'engine_func_002c4b84':
            ptr = self.next_alloc
            self.next_alloc += (r3 + 0xFF) & ~0xFF
            uc.reg_write(UC_ARM_REG_R0, ptr)
        elif stub_name == 'engine_func_002c4b30':
            # zero memory
            uc.mem_write(r0, b'\x00' * r1)
            uc.reg_write(UC_ARM_REG_R0, 0)
        elif stub_name in ('engine_func_002c5978', 'camp_func_002c4c00'):
            task_handle = 0x00480000 + len(self.calls) * 0x100
            uc.reg_write(UC_ARM_REG_R0, task_handle)
        elif stub_name == 'engine_func_002c583c':
            uc.reg_write(UC_ARM_REG_R0, 0)
        else:
            uc.reg_write(UC_ARM_REG_R0, 0)

        lr = uc.reg_read(UC_ARM_REG_LR)
        uc.reg_write(UC_ARM_REG_PC, lr)

def setup_stubs(uc, tracker):
    for name, addr in STUB_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1") # bx lr
        uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data=name, begin=addr, end=addr)
    setup_orig_stubs(uc, tracker)

def setup_orig_stubs(uc, tracker):
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

def test_iftouch_init():
    print("\n--- Testing IfTouch_Init (0x0010299c, 260 B) ---")
    orig_code = ORIG_DATA[0x0010299c - CODE_BASE : 0x0010299c - CODE_BASE + 260]
    source_path = ROOT / "src" / "ui" / "tbb_loader.cpp"
    decomp_code, relocs, rodata = compile_source(source_path, "IfTouch_Init", "iftouch_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    extra_syms = {
        'IfTouch_CalcCallback_00107ccc': 0x00107ccc,
        'IfTouch_ExitCallback_0010a28c': 0x0010a28c,
        'g_IfTouchGlobal': 0x0043dcb0,
    }
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR, extra_syms)

    ADDR_GLOBAL = 0x0043dcb0

    def run_case(code, addr, is_orig, ref_count, work_ptr):
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

        # Setup g_IfTouchGlobal
        uc.mem_write(ADDR_GLOBAL, struct.pack('<b3xI', ref_count, work_ptr))

        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=1000000)

        final_ref, final_work = struct.unpack('<b3xI', uc.mem_read(ADDR_GLOBAL, 8))
        work_fields = None
        if final_work != 0:
            task_handle = struct.unpack('<I', uc.mem_read(final_work, 4))[0]
            touch_timer, touch_state, active_panel_id = struct.unpack('<3H', uc.mem_read(final_work + 0x64a, 6))
            work_fields = {
                'task_handle': task_handle,
                'touch_timer': touch_timer,
                'touch_state': touch_state,
                'active_panel_id': active_panel_id,
            }

        return final_ref, final_work, work_fields, tracker.calls

    # Case 1: uninitialized (ref_count = 0, work_ptr = 0)
    r_orig, w_orig, f_orig, c_orig = run_case(orig_code, 0x0010299c, True, 0, 0)
    r_dec, w_dec, f_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False, 0, 0)

    assert r_orig == r_dec == 1, f"ref mismatch: orig={r_orig}, dec={r_dec}"
    assert w_orig == w_dec != 0, f"work mismatch: orig={w_orig}, dec={w_dec}"
    assert f_orig == f_dec, f"fields mismatch: orig={f_orig}, dec={f_dec}"
    assert f_orig['touch_timer'] == 10
    assert f_orig['touch_state'] == 0
    assert f_orig['active_panel_id'] == 0xFFFF
    assert len(c_orig) == len(c_dec) == 3, f"Calls mismatch: orig={len(c_orig)}, dec={len(c_dec)}"
    assert c_orig[2]['task_name'] == c_dec[2]['task_name'] == "TOUCH CALC"
    assert c_orig[2]['r1'] == c_dec[2]['r1'] == 1
    assert c_orig[2]['stack'][0] == c_dec[2]['stack'][0] == 0x00107ccc
    assert c_orig[2]['stack'][1] == c_dec[2]['stack'][1] == 0x0010a28c
    print(f"  [PASS] uninitialized_alloc (ref={r_orig}, work=0x{w_orig:08x}, fields={f_orig})")

    # Case 2: already initialized (ref_count = 1, work_ptr = 0x00470000)
    r_orig2, w_orig2, f_orig2, c_orig2 = run_case(orig_code, 0x0010299c, True, 1, 0x00470000)
    r_dec2, w_dec2, f_dec2, c_dec2 = run_case(patched_code, TARGET_DECOMP, False, 1, 0x00470000)

    assert r_orig2 == r_dec2 == 2, f"ref mismatch: orig={r_orig2}, dec={r_dec2}"
    assert w_orig2 == w_dec2 == 0x00470000
    assert len(c_orig2) == len(c_dec2) == 0, f"Expected 0 calls when ref_count > 0, got {len(c_orig2)}"
    print(f"  [PASS] already_initialized (ref={r_orig2}, calls=0)")

def test_biblemain_init():
    print("\n--- Testing bibleMain_Init (0x00269cc8, 352 B) ---")
    orig_code = ORIG_DATA[0x00269cc8 - CODE_BASE : 0x00269cc8 - CODE_BASE + 352]
    source_path = ROOT / "src" / "camp" / "bible.cpp"
    decomp_code, relocs, rodata = compile_source(source_path, "bibleMain_Init", "bible_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    extra_syms = {
        'g_BibleMainManager': 0x0043da10,
        'AsdMem_Alloc': STUB_MAP['engine_func_002c4b84'],
    }
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR, extra_syms)

    ADDR_MGR = 0x0043da10

    def run_case(code, addr, is_orig):
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

        uc.mem_write(ADDR_MGR, struct.pack('<I', 0))

        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=1000000)

        work_ptr = struct.unpack('<I', uc.mem_read(ADDR_MGR, 4))[0]
        work_bytes = uc.mem_read(work_ptr, 0x20)
        proc_task, draw_up, draw_down = struct.unpack_from('<3I', work_bytes, 0)
        flag_0c, flag_0d = struct.unpack_from('<2B', work_bytes, 0x0C)
        state = struct.unpack_from('<I', work_bytes, 0x10)[0]
        flag_14 = struct.unpack_from('<B', work_bytes, 0x14)[0]

        return work_ptr, {
            'proc_task': proc_task,
            'draw_up': draw_up,
            'draw_down': draw_down,
            'flag_0c': flag_0c,
            'flag_0d': flag_0d,
            'state': state,
            'flag_14': flag_14,
        }, tracker.calls

    w_orig, f_orig, c_orig = run_case(orig_code, 0x00269cc8, True)
    w_dec, f_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False)

    assert w_orig == w_dec != 0, f"work ptr mismatch: orig={w_orig}, dec={w_dec}"
    assert f_orig == f_dec, f"fields mismatch: orig={f_orig}, dec={f_dec}"
    assert f_orig['flag_0c'] == 0
    assert f_orig['flag_0d'] == 0
    assert f_orig['state'] == 1
    assert f_orig['flag_14'] == 1
    assert len(c_orig) == len(c_dec) == 5, f"Calls mismatch: orig={len(c_orig)}, dec={len(c_dec)}"
    assert c_orig[0]['name'] == c_dec[0]['name'] == 'engine_func_002c583c'
    assert c_orig[1]['name'] == c_dec[1]['name'] == 'engine_func_002c4b84'
    assert c_orig[2]['name'] == c_dec[2]['name'] == 'engine_func_002c5978'
    assert c_orig[2]['task_name'] == c_dec[2]['task_name'] == "BibleMainProc"
    assert c_orig[2]['r1'] == c_dec[2]['r1'] == 2 # prio 2
    assert c_orig[3]['name'] == c_dec[3]['name'] == 'camp_func_002c4c00'
    assert c_orig[3]['task_name'] == c_dec[3]['task_name'] == "BibleDrawUp"
    assert c_orig[3]['r1'] == c_dec[3]['r1'] == 0x6F
    assert c_orig[4]['name'] == c_dec[4]['name'] == 'camp_func_002c4c00'
    assert c_orig[4]['task_name'] == c_dec[4]['task_name'] == "BibleDrawDown"
    assert c_orig[4]['r1'] == c_dec[4]['r1'] == 0xE6
    print(f"  [PASS] bibleMain_Init (work=0x{w_orig:08x}, fields={f_orig})")

def test_uniteeffect_init():
    print("\n--- Testing UniteEffect_Init (0x002e315c, 344 B) ---")
    orig_code = ORIG_DATA[0x002e315c - CODE_BASE : 0x002e315c - CODE_BASE + 344]
    source_path = ROOT / "src" / "camp" / "unite.cpp"
    decomp_code, relocs, rodata = compile_source(source_path, "UniteEffect_Init", "unite_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    extra_syms = {
        'AsdMem_Alloc': STUB_MAP['engine_func_002c4b84'],
        'AsdMem_Zero': STUB_MAP['engine_func_002c4b30'],
        'AsdTask_CreateCalc': STUB_MAP['engine_func_002c5978'],
        'AsdTask_CreateDraw': STUB_MAP['camp_func_002c4c00'],
    }
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR, extra_syms)

    ADDR_SLOT = 0x0043dd90

    def run_case(code, addr, is_orig, initial_ptr):
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

        uc.mem_write(ADDR_SLOT, struct.pack('<I', initial_ptr))

        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=1000000)

        work_ptr = struct.unpack('<I', uc.mem_read(ADDR_SLOT, 4))[0]
        calc_task = struct.unpack('<I', uc.mem_read(work_ptr, 4))[0]
        return work_ptr, calc_task, tracker.calls

    # Case 1: uninitialized
    w_orig, t_orig, c_orig = run_case(orig_code, 0x002e315c, True, 0)
    w_dec, t_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False, 0)

    assert w_orig == w_dec != 0, f"work ptr mismatch: orig={w_orig}, dec={w_dec}"
    assert t_orig == t_dec != 0, f"task ptr mismatch: orig={t_orig}, dec={t_dec}"
    assert len(c_orig) == len(c_dec) == 8, f"Calls mismatch: orig={len(c_orig)}, dec={len(c_dec)}"
    assert c_orig[2]['task_name'] == c_dec[2]['task_name'] == "TMD CALC"
    assert c_orig[2]['r1'] == c_dec[2]['r1'] == 2 # prio 2
    assert c_orig[3]['task_name'] == c_dec[3]['task_name'] == "TMD DDRAW"
    assert c_orig[3]['r1'] == c_dec[3]['r1'] == 0xE7 # prio 0xE7
    assert c_orig[4]['task_name'] == c_dec[4]['task_name'] == "TMD DDRAW"
    assert c_orig[4]['r1'] == c_dec[4]['r1'] == 0x6F # prio 0x6F
    assert c_orig[5]['name'] == c_dec[5]['name'] == 'btlTalkBustUp_func_002959c4'
    assert c_orig[6]['name'] == c_dec[6]['name'] == 'script_vm_func_002c0128'
    assert c_orig[7]['name'] == c_dec[7]['name'] == 'camp_func_002976ac'
    assert c_orig[7]['r0'] == c_dec[7]['r0'] == 0x25
    print(f"  [PASS] uninitialized_alloc (work=0x{w_orig:08x}, calc_task=0x{t_orig:08x}, 8 calls matched)")

def main():
    print("Testing Cathedral and UI Task Init candidates...")
    test_iftouch_init()
    test_biblemain_init()
    test_uniteeffect_init()
    print("\nALL 3 CATHEDRAL & UI TASK INIT CANDIDATES PASSED 100%!")

if __name__ == "__main__":
    main()
