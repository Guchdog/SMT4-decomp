#!/usr/bin/env python3
"""Differential test runner for window batch 3 candidates against code.bin.

Tests:
  - 0x0010a70c: ComWin_SetState (60 B)
  - 0x0010a940: ComWin_GetState (20 B)
  - 0x0010aed4: func_0010aed4 (16 B)
  - 0x0010aee4: ComWin_Reset (84 B)
  - 0x002638dc: PlaceWin_Dismiss (32 B)
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
SOURCE = ROOT / "src" / "ui" / "window.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STACK_BASE = 0x0FFF0000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

BUILD_DIR = ROOT / "build" / "window_batch3_test"

ORIG_DATA = CODE_BIN.read_bytes()

COMPILED_FUNCTIONS = None
RODATA_ADDR = 0x004A0000
RODATA_BYTES = b""

# Globals
ADDR_COMWIN_STATE = 0x004E3CD4
ADDR_COMWIN_RESET_GLOBAL = 0x004E2F68
ADDR_PLACEWIN_WORK = 0x0043E140

# Stubs
STUB_BASE = 0x004B0000
STUB_MAP = {
    'engine_func_002c54f0': STUB_BASE + 0x00,
    'func_00115b74': STUB_BASE + 0x08,
    'engine_func_002bdc08': STUB_BASE + 0x10,
    'engine_func_002bdbcc': STUB_BASE + 0x18,
    'camp_func_002bf030': STUB_BASE + 0x20,
    'UiAnimSprite_SetAnim': STUB_BASE + 0x28,
}

ORIG_ADDR_MAP = {
    0x002c54f0: 'engine_func_002c54f0',
    0x00115b74: 'func_00115b74',
    0x002bdc08: 'engine_func_002bdc08',
    0x002bdbcc: 'engine_func_002bdbcc',
    0x002bf030: 'camp_func_002bf030',
}

def compile_function(func_name: str, out: Path = BUILD_DIR, source: Path = SOURCE):
    global COMPILED_FUNCTIONS, RODATA_BYTES
    if COMPILED_FUNCTIONS is None:
        out.mkdir(parents=True, exist_ok=True)
        obj = out / "window.o"
        res = compile_tu_armv6k(source, obj, repo_root=ROOT)
        if res.returncode != 0:
            print("COMPILATION FAILED:")
            print(res.stderr)
            sys.exit(1)
        COMPILED_FUNCTIONS = extract_elf_functions_detailed(obj)
        data = obj.read_bytes()
        e_shoff = struct.unpack_from('<I', data, 32)[0]
        e_shentsize = struct.unpack_from('<H', data, 46)[0]
        e_shnum = struct.unpack_from('<H', data, 48)[0]
        sections = [struct.unpack_from('<IIIIIIIIII', data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
        shstr = sections[struct.unpack_from('<H', data, 50)[0]]
        shstrtab = data[shstr[4]:shstr[4]+shstr[5]]
        def get_sh_name(off):
            return shstrtab[off:].split(b'\x00')[0].decode('ascii')
        for s in sections:
            sh_name = get_sh_name(s[0])
            if sh_name.startswith(".rodata"):
                RODATA_BYTES = data[s[4]:s[4]+s[5]]
                break

    for mangled, (b, relocs) in COMPILED_FUNCTIONS.items():
        if func_name in mangled:
            return b, relocs
    raise KeyError(f"Function {func_name} not found in compiled object")

def create_emulator():
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)
    return uc

class StubTracker:
    def __init__(self):
        self.calls = []

    def handle_call(self, uc, address, size, user_data):
        stub_name = user_data
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        r3 = uc.reg_read(UC_ARM_REG_R3)
        sp = uc.reg_read(UC_ARM_REG_SP)
        stack_arg0 = struct.unpack('<I', uc.mem_read(sp, 4))[0]
        self.calls.append({
            'name': stub_name,
            'r0': r0, 'r1': r1, 'r2': r2, 'r3': r3,
            'stack0': stack_arg0,
        })
        # Default returns
        if stub_name == 'engine_func_002c54f0':
            uc.reg_write(UC_ARM_REG_R0, 0x12345678)
        elif stub_name == 'engine_func_002bdc08':
            uc.reg_write(UC_ARM_REG_R0, 0)
        elif stub_name == 'camp_func_002bf030':
            uc.reg_write(UC_ARM_REG_R0, 1)

        lr = uc.reg_read(UC_ARM_REG_LR)
        uc.reg_write(UC_ARM_REG_PC, lr)

def setup_stubs(uc, tracker):
    for name, addr in STUB_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1") # bx lr
        uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data=name, begin=addr, end=addr)

def setup_orig_stubs(uc, tracker):
    for addr, name in ORIG_ADDR_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1") # bx lr
        uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data=name, begin=addr, end=addr)

def apply_relocs(code_bytes, relocs, target_addr, rodata_addr):
    mutable = bytearray(code_bytes)
    for rel in relocs:
        offset = rel.offset
        name = rel.symbol_name
        rel_type = rel.relocation_type
        if name in STUB_MAP:
            sym_val = STUB_MAP[name]
        elif name.startswith(".rodata"):
            sym_val = rodata_addr
        elif name == "window.cpp":
            sym_val = target_addr
        else:
            raise ValueError(f"Unknown symbol {name}")

        if rel_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            orig = struct.unpack_from('<I', mutable, offset)[0]
            target = sym_val
            pc = target_addr + offset + 8
            new_disp = ((target - pc) >> 2) & 0x00FFFFFF
            inst = (orig & 0xFF000000) | new_disp
            struct.pack_into('<I', mutable, offset, inst)
        elif rel_type in (2, 38):  # R_ARM_ABS32 or R_ARM_TARGET1
            orig = struct.unpack_from('<I', mutable, offset)[0]
            val = (sym_val + orig) & 0xFFFFFFFF
            struct.pack_into('<I', mutable, offset, val)
        else:
            raise ValueError(f"Unsupported reloc type {rel_type}")
    return bytes(mutable)

def test_comwin_setstate():
    print("\n--- Testing ComWin_SetState (0x0010a70c, 60 B) ---")
    orig_code = ORIG_DATA[0x0010a70c - CODE_BASE : 0x0010a70c - CODE_BASE + 60]
    decomp_code, relocs = compile_function("ComWin_SetState")

    TARGET_DECOMP = 0x00380000
    patched_code = apply_relocs(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    def run_case(code, addr):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        # Fill state block with garbage
        garbage = b"\xaa\xbb\xcc\xdd" * 8
        uc.mem_write(ADDR_COMWIN_STATE, garbage)

        uc.emu_start(addr, 0x00000000, timeout=1000000)
        ret = uc.reg_read(UC_ARM_REG_R0)
        state_data = uc.mem_read(ADDR_COMWIN_STATE, 32)
        words = struct.unpack('<8I', state_data)
        return ret, words

    orig_ret, orig_words = run_case(orig_code, 0x0010a70c)
    decomp_ret, decomp_words = run_case(patched_code, TARGET_DECOMP)

    assert orig_ret == decomp_ret == 1, f"Ret mismatch: orig={orig_ret}, decomp={decomp_ret}"
    assert orig_words == decomp_words, f"State mismatch: orig={orig_words}, decomp={decomp_words}"
    assert orig_words == (0, 0, 0, 0, 0, 0, 15, 4), f"Unexpected words: {orig_words}"
    print(f"  [PASS] ComWin_SetState (ret={orig_ret}, words={orig_words})")

def test_comwin_getstate():
    print("\n--- Testing ComWin_GetState (0x0010a940, 20 B) ---")
    orig_code = ORIG_DATA[0x0010a940 - CODE_BASE : 0x0010a940 - CODE_BASE + 20]
    decomp_code, relocs = compile_function("ComWin_GetState")

    TARGET_DECOMP = 0x00380000
    patched_code = apply_relocs(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    def run_case(code, addr, args, is_orig):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker()
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)
        uc.reg_write(UC_ARM_REG_R0, args[0])
        uc.reg_write(UC_ARM_REG_R1, args[1])
        uc.reg_write(UC_ARM_REG_R2, args[2])
        uc.reg_write(UC_ARM_REG_R3, args[3])

        uc.emu_start(addr, 0x00000000, timeout=1000000)
        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, tracker.calls

    test_args = (0x11, 0x22, 0x33, 0x44)
    orig_ret, orig_calls = run_case(orig_code, 0x0010a940, test_args, True)
    decomp_ret, decomp_calls = run_case(patched_code, TARGET_DECOMP, test_args, False)

    assert orig_ret == decomp_ret == 0x12345678, f"Ret mismatch: orig={orig_ret}, decomp={decomp_ret}"
    assert len(orig_calls) == len(decomp_calls) == 1, f"Calls length mismatch"
    assert orig_calls[0]['name'] == decomp_calls[0]['name'] == 'engine_func_002c54f0'
    assert orig_calls[0]['r0'] == decomp_calls[0]['r0'] == 0x11
    assert orig_calls[0]['r1'] == decomp_calls[0]['r1'] == 0x22
    assert orig_calls[0]['r2'] == decomp_calls[0]['r2'] == 0x33
    assert orig_calls[0]['r3'] == decomp_calls[0]['r3'] == 0x44
    assert orig_calls[0]['stack0'] == decomp_calls[0]['stack0'] == 1
    print(f"  [PASS] ComWin_GetState (ret=0x{orig_ret:08x}, call={orig_calls[0]})")

def test_func_0010aed4():
    print("\n--- Testing func_0010aed4 (0x0010aed4, 16 B) ---")
    orig_code = ORIG_DATA[0x0010aed4 - CODE_BASE : 0x0010aed4 - CODE_BASE + 16]
    decomp_code, relocs = compile_function("func_0010aed4")

    TARGET_DECOMP = 0x00380000
    patched_code = apply_relocs(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    def run_case(code, addr, is_orig):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker()
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=1000000)
        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, tracker.calls

    orig_ret, orig_calls = run_case(orig_code, 0x0010aed4, True)
    decomp_ret, decomp_calls = run_case(patched_code, TARGET_DECOMP, False)

    assert orig_ret == decomp_ret == 0, f"Ret mismatch: orig={orig_ret}, decomp={decomp_ret}"
    assert len(orig_calls) == len(decomp_calls) == 1, f"Calls mismatch"
    assert orig_calls[0]['name'] == decomp_calls[0]['name'] == 'func_00115b74'
    print(f"  [PASS] func_0010aed4 (ret={orig_ret}, call={orig_calls[0]['name']})")

def test_comwin_reset():
    print("\n--- Testing ComWin_Reset (0x0010aee4, 84 B) ---")
    orig_code = ORIG_DATA[0x0010aee4 - CODE_BASE : 0x0010aee4 - CODE_BASE + 84]
    decomp_code, relocs = compile_function("ComWin_Reset")

    TARGET_DECOMP = 0x00380000
    patched_code = apply_relocs(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    def run_case(code, addr, is_orig, ctx_ptr):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker()
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        # Set global context pointer
        uc.mem_write(ADDR_COMWIN_RESET_GLOBAL + 0x204, struct.pack('<I', ctx_ptr))

        if ctx_ptr != 0:
            # Set up 8 entries at ctx_ptr
            # Entry 0: non-null voice (0xAAAA0000)
            # Entry 1: null
            # Entry 2: non-null voice (0xAAAA0002)
            # Entries 3..7: null
            table = bytearray(0x100)
            struct.pack_into('<I', table, 0x20 + 0 * 4, 0xAAAA0000)
            struct.pack_into('<I', table, 0x20 + 1 * 4, 0x00000000)
            struct.pack_into('<I', table, 0x20 + 2 * 4, 0xAAAA0002)
            uc.mem_write(ctx_ptr, bytes(table))

        uc.emu_start(addr, 0x00000000, timeout=1000000)
        return tracker.calls

    # Case 1: null context
    c_orig = run_case(orig_code, 0x0010aee4, True, 0)
    c_decomp = run_case(patched_code, TARGET_DECOMP, False, 0)
    assert len(c_orig) == len(c_decomp) == 0, f"Null context should make no calls"
    print("  [PASS] null_context (0 calls)")

    # Case 2: active context with entries
    CTX_ADDR = 0x00470000
    c_orig = run_case(orig_code, 0x0010aee4, True, CTX_ADDR)
    c_decomp = run_case(patched_code, TARGET_DECOMP, False, CTX_ADDR)

    assert len(c_orig) == len(c_decomp) == 4, f"Expected 4 calls (2 per non-null entry), got orig={len(c_orig)}, decomp={len(c_decomp)}"
    for i in range(len(c_orig)):
        assert c_orig[i]['name'] == c_decomp[i]['name']
        assert c_orig[i]['r0'] == c_decomp[i]['r0']
        assert c_orig[i]['r1'] == c_decomp[i]['r1']
    print(f"  [PASS] active_context (calls={len(c_orig)})")

def test_placewin_dismiss():
    print("\n--- Testing PlaceWin_Dismiss (0x002638dc, 32 B) ---")
    orig_code = ORIG_DATA[0x002638dc - CODE_BASE : 0x002638dc - CODE_BASE + 32]
    decomp_code, relocs = compile_function("PlaceWin_Dismiss")

    TARGET_DECOMP = 0x00380000
    patched_code = apply_relocs(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    def run_case(code, addr, is_orig):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker()
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        WORK_ADDR = 0x00471000
        uc.mem_write(ADDR_PLACEWIN_WORK, struct.pack('<I', WORK_ADDR))
        work_buf = bytearray(0x140)
        struct.pack_into('<I', work_buf, 8, 1) # initial state
        uc.mem_write(WORK_ADDR, bytes(work_buf))

        uc.emu_start(addr, 0x00000000, timeout=1000000)

        state = struct.unpack('<I', uc.mem_read(WORK_ADDR + 8, 4))[0]
        return state, tracker.calls

    s_orig, c_orig = run_case(orig_code, 0x002638dc, True)
    s_decomp, c_decomp = run_case(patched_code, TARGET_DECOMP, False)

    assert s_orig == s_decomp == 3, f"State mismatch: orig={s_orig}, decomp={s_decomp}"
    assert len(c_orig) == len(c_decomp) == 1, f"Calls mismatch"
    assert c_orig[0]['name'] == c_decomp[0]['name'] == 'camp_func_002bf030'
    assert c_orig[0]['r0'] == c_decomp[0]['r0'] == 0x00471000 + 0x34
    assert c_orig[0]['r1'] == c_decomp[0]['r1'] == 1
    print(f"  [PASS] PlaceWin_Dismiss (state={s_orig}, call={c_orig[0]})")

def main():
    print("Testing Window Batch 3 candidates...")
    test_comwin_setstate()
    test_comwin_getstate()
    test_func_0010aed4()
    test_comwin_reset()
    test_placewin_dismiss()
    print("\nALL 5 WINDOW BATCH 3 CANDIDATES PASSED 100%!")

if __name__ == "__main__":
    main()
