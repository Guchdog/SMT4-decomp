#!/usr/bin/env python3
"""Differential test runner for window batch 1 candidates against code.bin.

Tests:
  - 0x0010ae9c: ComWin_CheckFlag (44 B)
  - 0x0010aec8: ComWin_GetResult (12 B)
  - 0x0010af48: InfoWin_SetState (60 B)
  - 0x0010b320: InfoWin_Dismiss (32 B)
  - 0x002ced0c: SearchWin_Dismiss (28 B)
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

BUILD_DIR = ROOT / "build" / "window_batch1_test"

ORIG_DATA = CODE_BIN.read_bytes()

COMPILED_FUNCTIONS = None
RODATA_ADDR = 0x004A0000
RODATA_BYTES = b""

# Globals
ADDR_COMWIN_FLAG    = 0x00465058
ADDR_COMWIN_TABLE   = 0x00465064
ADDR_COMWIN_RESULT  = 0x00465024
ADDR_INFOWIN_CTX    = 0x004C3B20
ADDR_INFOWIN_FLAG   = 0x0044D020
ADDR_INFOWIN_DISM   = 0x00464A70
ADDR_SEARCHWIN_FLAG = 0x0043E310

# Stubs
STUB_BASE = 0x004B0000
STUB_MAP = {
    'battle_func_002bf148': STUB_BASE + 0x00,
    'engine_func_002c25f4': STUB_BASE + 0x08,
    'UiWindow_SetResult': STUB_BASE + 0x10,
    'func_0011b558': STUB_BASE + 0x18,
    'engine_func_0011b5e8': STUB_BASE + 0x20,
}

ORIG_ADDR_MAP = {
    0x002bf148: 'battle_func_002bf148',
    0x002c25f4: 'engine_func_002c25f4',
    0x002c4244: 'UiWindow_SetResult',
    0x0011b558: 'func_0011b558',
    0x0011b5e8: 'engine_func_0011b5e8',
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

class Emulator:
    def __init__(self):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.uc.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
        self.uc.mem_write(CODE_BASE, ORIG_DATA[:CODE_SIZE])
        self.uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)

        try:
            self.uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
            self.uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
        except Exception:
            pass

        self.call_log = []
        self._install_stubs()

    def _install_stubs(self):
        bx_lr = struct.pack('<I', 0xe12fff1e)

        for name, addr in STUB_MAP.items():
            self.uc.mem_write(addr, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._make_hook(name), begin=addr, end=addr)

        for addr, name in ORIG_ADDR_MAP.items():
            self.uc.mem_write(addr, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._make_hook(name), begin=addr, end=addr)

    def _make_hook(self, name):
        def hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)

            if name == 'battle_func_002bf148':
                self.call_log.append((name, r0))
                uc.reg_write(UC_ARM_REG_R0, r0 + 0x100)
            elif name == 'engine_func_002c25f4':
                self.call_log.append((name, r0))
            elif name == 'UiWindow_SetResult':
                self.call_log.append((name, r0))
            elif name == 'func_0011b558':
                self.call_log.append((name, r0))
            elif name == 'engine_func_0011b5e8':
                self.call_log.append((name, r0))
            else:
                self.call_log.append((name, r0, r1, r2, r3))
        return hook

def relocate_compiled(b: bytes, relocs: list, base_addr: int) -> bytearray:
    code = bytearray(b)
    sym_map = dict(STUB_MAP)

    for rel in relocs:
        off = rel.offset
        sym = rel.symbol_name
        rel_type = rel.relocation_type

        if sym in sym_map:
            target = sym_map[sym]
        else:
            raise RuntimeError(f"Unmapped relocation: {sym}")

        if rel_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            curr = struct.unpack_from('<I', code, off)[0]
            disp = (target - (base_addr + off + 8)) >> 2
            new_disp = disp & 0x00FFFFFF
            new_inst = (curr & 0xFF000000) | new_disp
            struct.pack_into('<I', code, off, new_inst)
        elif rel_type == 2:  # R_ARM_ABS32
            curr = struct.unpack_from('<I', code, off)[0]
            struct.pack_into('<I', code, off, target + curr)
        else:
            raise RuntimeError(f"Unsupported relocation type: {rel_type}")
    return code

def run_function(emu: Emulator, addr: int, args: list, stack_top: int = STACK_TOP):
    emu.uc.reg_write(UC_ARM_REG_SP, stack_top)
    emu.uc.reg_write(UC_ARM_REG_LR, 0x00000000)
    reg_list = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3]
    for i, val in enumerate(args[:4]):
        emu.uc.reg_write(reg_list[i], val)
    if len(args) > 4:
        for j, val in enumerate(args[4:]):
            emu.uc.mem_write(stack_top + j * 4, struct.pack('<I', val))

    end_addr = 0x00000000
    emu.uc.emu_start(addr, end_addr)
    return emu.uc.reg_read(UC_ARM_REG_R0)

def test_comwin_checkflag():
    print("\n--- Testing ComWin_CheckFlag (0x0010ae9c, 44 B) ---")
    orig_addr = 0x0010ae9c
    comp_addr = 0x003D0000
    b, relocs = compile_function("ComWin_CheckFlag")
    relocated = relocate_compiled(b, relocs, comp_addr)

    scenarios = [
        ("flag_0_selects_index_1", 0, [0x1111, 0x2222]),
        ("flag_1_selects_index_0", 1, [0x3333, 0x4444]),
    ]

    for name, flag_val, table_vals in scenarios:
        # Orig
        emu_orig = Emulator()
        emu_orig.uc.mem_write(ADDR_COMWIN_FLAG, struct.pack('<I', flag_val))
        emu_orig.uc.mem_write(ADDR_COMWIN_TABLE, struct.pack('<II', table_vals[0], table_vals[1]))
        run_function(emu_orig, orig_addr, [])
        orig_calls = list(emu_orig.call_log)

        # Comp
        emu_comp = Emulator()
        emu_comp.uc.mem_write(comp_addr, bytes(relocated))
        emu_comp.uc.mem_write(ADDR_COMWIN_FLAG, struct.pack('<I', flag_val))
        emu_comp.uc.mem_write(ADDR_COMWIN_TABLE, struct.pack('<II', table_vals[0], table_vals[1]))
        run_function(emu_comp, comp_addr, [])
        comp_calls = list(emu_comp.call_log)

        assert orig_calls == comp_calls, f"{name}: calls mismatch: orig={orig_calls}, comp={comp_calls}"
        print(f"  [PASS] {name} (calls={comp_calls})")

def test_comwin_getresult():
    print("\n--- Testing ComWin_GetResult (0x0010aec8, 12 B) ---")
    orig_addr = 0x0010aec8
    comp_addr = 0x003D0000
    b, relocs = compile_function("ComWin_GetResult")
    relocated = relocate_compiled(b, relocs, comp_addr)

    # Orig
    emu_orig = Emulator()
    run_function(emu_orig, orig_addr, [])
    orig_calls = list(emu_orig.call_log)

    # Comp
    emu_comp = Emulator()
    emu_comp.uc.mem_write(comp_addr, bytes(relocated))
    run_function(emu_comp, comp_addr, [])
    comp_calls = list(emu_comp.call_log)

    assert orig_calls == comp_calls, f"calls mismatch: orig={orig_calls}, comp={comp_calls}"
    assert orig_calls == [('UiWindow_SetResult', ADDR_COMWIN_RESULT)]
    print(f"  [PASS] ComWin_GetResult (arg={hex(ADDR_COMWIN_RESULT)})")

def test_infowin_setstate():
    print("\n--- Testing InfoWin_SetState (0x0010af48, 60 B) ---")
    orig_addr = 0x0010af48
    comp_addr = 0x003D0000
    b, relocs = compile_function("InfoWin_SetState")
    relocated = relocate_compiled(b, relocs, comp_addr)

    scenarios = [
        ("state_0", 0),
        ("state_3_sets_flag", 3),
        ("state_5", 5),
    ]

    for name, state in scenarios:
        # Orig
        emu_orig = Emulator()
        emu_orig.uc.mem_write(ADDR_INFOWIN_CTX + 0x1C0, struct.pack('<I', 0x00450000))
        emu_orig.uc.mem_write(ADDR_INFOWIN_FLAG, b'\x00')
        run_function(emu_orig, orig_addr, [state])
        orig_calls = list(emu_orig.call_log)
        orig_flag = emu_orig.uc.mem_read(ADDR_INFOWIN_FLAG, 1)[0]

        # Comp
        emu_comp = Emulator()
        emu_comp.uc.mem_write(comp_addr, bytes(relocated))
        emu_comp.uc.mem_write(ADDR_INFOWIN_CTX + 0x1C0, struct.pack('<I', 0x00450000))
        emu_comp.uc.mem_write(ADDR_INFOWIN_FLAG, b'\x00')
        run_function(emu_comp, comp_addr, [state])
        comp_calls = list(emu_comp.call_log)
        comp_flag = emu_comp.uc.mem_read(ADDR_INFOWIN_FLAG, 1)[0]

        assert orig_calls == comp_calls, f"{name}: calls mismatch: orig={orig_calls}, comp={comp_calls}"
        assert orig_flag == comp_flag, f"{name}: flag mismatch: orig={orig_flag}, comp={comp_flag}"
        print(f"  [PASS] {name} (flag={comp_flag})")

def test_infowin_dismiss():
    print("\n--- Testing InfoWin_Dismiss (0x0010b320, 32 B) ---")
    orig_addr = 0x0010b320
    comp_addr = 0x003D0000
    b, relocs = compile_function("InfoWin_Dismiss")
    relocated = relocate_compiled(b, relocs, comp_addr)

    scenarios = [
        ("val_under_limit_stored", 5, 10),
        ("val_equal_limit_rejected", 10, 10),
        ("val_over_limit_rejected", 15, 10),
    ]

    for name, val, limit in scenarios:
        # Orig
        emu_orig = Emulator()
        emu_orig.uc.mem_write(ADDR_INFOWIN_DISM + 4, struct.pack('<I', limit))
        emu_orig.uc.mem_write(ADDR_INFOWIN_DISM + 0xC, struct.pack('<I', 0xFFFFFFFF))
        ret_orig = run_function(emu_orig, orig_addr, [val])
        orig_stored = struct.unpack('<I', emu_orig.uc.mem_read(ADDR_INFOWIN_DISM + 0xC, 4))[0]

        # Comp
        emu_comp = Emulator()
        emu_comp.uc.mem_write(comp_addr, bytes(relocated))
        emu_comp.uc.mem_write(ADDR_INFOWIN_DISM + 4, struct.pack('<I', limit))
        emu_comp.uc.mem_write(ADDR_INFOWIN_DISM + 0xC, struct.pack('<I', 0xFFFFFFFF))
        ret_comp = run_function(emu_comp, comp_addr, [val])
        comp_stored = struct.unpack('<I', emu_comp.uc.mem_read(ADDR_INFOWIN_DISM + 0xC, 4))[0]

        assert ret_orig == ret_comp, f"{name}: ret mismatch: orig={ret_orig}, comp={ret_comp}"
        assert orig_stored == comp_stored, f"{name}: stored mismatch: orig={orig_stored}, comp={comp_stored}"
        print(f"  [PASS] {name} (ret={ret_comp}, stored={hex(comp_stored)})")

def test_searchwin_dismiss():
    print("\n--- Testing SearchWin_Dismiss (0x002ced0c, 28 B) ---")
    orig_addr = 0x002ced0c
    comp_addr = 0x003D0000
    b, relocs = compile_function("SearchWin_Dismiss")
    relocated = relocate_compiled(b, relocs, comp_addr)

    scenarios = [
        ("flag_zero_returns_1", 0),
        ("flag_one_returns_0", 1),
        ("flag_0xFF_returns_0", 0xFF),
    ]

    for name, flag_val in scenarios:
        # Orig
        emu_orig = Emulator()
        emu_orig.uc.mem_write(ADDR_SEARCHWIN_FLAG + 1, bytes([flag_val]))
        ret_orig = run_function(emu_orig, orig_addr, [])

        # Comp
        emu_comp = Emulator()
        emu_comp.uc.mem_write(comp_addr, bytes(relocated))
        emu_comp.uc.mem_write(ADDR_SEARCHWIN_FLAG + 1, bytes([flag_val]))
        ret_comp = run_function(emu_comp, comp_addr, [])

        assert ret_orig == ret_comp, f"{name}: ret mismatch: orig={ret_orig}, comp={ret_comp}"
        print(f"  [PASS] {name} (ret={ret_comp})")

def main():
    print("Testing Window Batch 1 candidates...")
    test_comwin_checkflag()
    test_comwin_getresult()
    test_infowin_setstate()
    test_infowin_dismiss()
    test_searchwin_dismiss()
    print("\nALL 5 WINDOW BATCH 1 CANDIDATES PASSED 100%!")

if __name__ == "__main__":
    main()
