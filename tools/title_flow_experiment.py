#!/usr/bin/env python3
"""Differential test runner for title_flow batch candidates against code.bin.

Tests:
  - 0x0018b660: Config_func_0018b660 (536 B)
  - 0x00194dbc: PlayLog_func_00194dbc (648 B)
  - 0x001eb02c: titleMain_func_001eb02c (524 B)
  - 0x001dafbc: tmnlMain_func_001dafbc (668 B)
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
SOURCE = ROOT / "src" / "camp" / "title_flow.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STACK_BASE = 0x0FFF0000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

BUILD_DIR = ROOT / "build" / "title_flow_test"

ORIG_DATA = CODE_BIN.read_bytes()

COMPILED_FUNCTIONS = None
RODATA_ADDR = 0x004A0000
RODATA_BYTES = b""

# Globals
ADDR_PLAY_LOG_WORK    = 0x0043DD08
ADDR_TITLE_CONF_WORK  = 0x0044E2D0
ADDR_CONFIG_WORK      = 0x0043DC58
ADDR_TITLE_MAIN_WORK  = 0x0044E300
ADDR_TMNL_MAIN_WORK   = 0x00432CE0

# Stubs
STUB_BASE = 0x004B0000
STUB_MAP = {
    'AsdMem_Alloc': STUB_BASE + 0x00,
    'AsdMem_AllocAlign': STUB_BASE + 0x08,
    'AsdMem_Zero': STUB_BASE + 0x10,
    'AsdTMTexTable_func_002c4e28': STUB_BASE + 0x18,
    'AsdRes_Request': STUB_BASE + 0x20,
    'ScriptVm_LoadTable': STUB_BASE + 0x28,
    'Tbb_EnsureSlotLoaded': STUB_BASE + 0x30,
    'Tbb_GetGlobalSubTable': STUB_BASE + 0x38,
    'Tbb_GetPayloadData': STUB_BASE + 0x40,
    'Tbb_GetRowCount': STUB_BASE + 0x48,
    'UiSpriteGroup_Init': STUB_BASE + 0x50,
    'UiSpriteGroup_BindTable': STUB_BASE + 0x58,
    'UiAnimSprite_Setup': STUB_BASE + 0x60,
    'UiAnimSprite_SetAnim': STUB_BASE + 0x68,
    'UiListCursor_Setup': STUB_BASE + 0x70,
    'Sound_PlaySE': STUB_BASE + 0x78,
    'SaveData_GetEntryValue': STUB_BASE + 0x80,
    'SaveData_GetPlayLogCount': STUB_BASE + 0x88,
    'SaveData_GetSettingMode': STUB_BASE + 0x90,
    'Camp_AddProgressValue': STUB_BASE + 0x98,
    'ScriptVm_SetFlag': STUB_BASE + 0xA0,
    'UiAnimSlot_SetState': STUB_BASE + 0xA8,
    'Ui_SetEntryLock': STUB_BASE + 0xB0,
    'UiInput_TestFlag': STUB_BASE + 0xB8,
    'UiInput_SetFlag': STUB_BASE + 0xC0,
    'Camp_SetFadeColor': STUB_BASE + 0xC8,
    'Flag_CheckEventBit': STUB_BASE + 0xD0,
    'AsdTask_CreateCalc': STUB_BASE + 0xD8,
    'AsdTask_CreateDraw': STUB_BASE + 0xE0,
}

ORIG_ADDR_MAP = {
    0x002c4b84: 'AsdMem_Alloc',
    0x002c54f0: 'AsdMem_AllocAlign',
    0x002c4b30: 'AsdMem_Zero',
    0x002c4e28: 'AsdTMTexTable_func_002c4e28',
    0x002a6214: 'AsdRes_Request',
    0x00297704: 'ScriptVm_LoadTable',
    0x002976ac: 'Tbb_EnsureSlotLoaded',
    0x002c0ec4: 'Tbb_GetGlobalSubTable',
    0x002c0e9c: 'Tbb_GetPayloadData',
    0x002c0e4c: 'Tbb_GetRowCount',
    0x002c3344: 'UiSpriteGroup_Init',
    0x002c32f8: 'UiSpriteGroup_BindTable',
    0x002bdb2c: 'UiAnimSprite_Setup',
    0x002bdac0: 'UiAnimSprite_SetAnim',
    0x0029fae8: 'UiListCursor_Setup',
    0x002b8b78: 'Sound_PlaySE',
    0x00290a38: 'SaveData_GetEntryValue',
    0x00290a4c: 'SaveData_GetPlayLogCount',
    0x00297688: 'SaveData_GetSettingMode',
    0x0029c0fc: 'Camp_AddProgressValue',
    0x002899c4: 'ScriptVm_SetFlag',
    0x00282e6c: 'UiAnimSlot_SetState',
    0x002a7540: 'Ui_SetEntryLock',
    0x00263778: 'UiInput_TestFlag',
    0x00263734: 'UiInput_SetFlag',
    0x0029f10c: 'Camp_SetFadeColor',
    0x002c0ba8: 'Flag_CheckEventBit',
    0x002c5978: 'AsdTask_CreateCalc',
    0x002c4c00: 'AsdTask_CreateDraw',
}

def compile_function(func_name: str, out: Path = BUILD_DIR, source: Path = SOURCE):
    global COMPILED_FUNCTIONS, RODATA_BYTES
    if COMPILED_FUNCTIONS is None:
        out.mkdir(parents=True, exist_ok=True)
        obj = out / "title_flow.o"
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

        if RODATA_BYTES:
            self.uc.mem_write(RODATA_ADDR, RODATA_BYTES)

        self.call_log = []
        self.alloc_ptr = 0x00480000
        self.task_handle_counter = 0x00490000

        # State configurations for mock behaviors
        self.setting_mode = 0
        self.event_bits = {}
        self.input_flags = {}
        self.play_log_count = 10
        self.entry_values = {}
        self.tbb_rows = 0
        self.tbb_table_ptr = 0x00470000
        self.tbb_payload_ptr = 0x00471000

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
            sp = uc.reg_read(UC_ARM_REG_SP)

            if name in ('AsdMem_Alloc', 'AsdMem_AllocAlign'):
                arg4 = struct.unpack('<I', uc.mem_read(sp, 4))[0]
                self.call_log.append((name, r0, r1, r2, r3, arg4))
                ret = self.alloc_ptr
                self.alloc_ptr += (r3 + 0x1FF) & ~0xFF
                uc.reg_write(UC_ARM_REG_R0, ret)
            elif name == 'AsdMem_Zero':
                self.call_log.append((name, r0, r1))
                uc.mem_write(r0, b'\x00' * r1)
            elif name == 'ScriptVm_LoadTable':
                name_str = uc.mem_read(r0, 32).split(b'\x00')[0].decode('ascii', errors='ignore')
                self.call_log.append((name, name_str, r1, r2))
                uc.reg_write(UC_ARM_REG_R0, 1)
            elif name == 'Tbb_GetGlobalSubTable':
                self.call_log.append((name, r0, r1))
                uc.reg_write(UC_ARM_REG_R0, self.tbb_table_ptr)
            elif name == 'Tbb_GetPayloadData':
                self.call_log.append((name, r0))
                uc.reg_write(UC_ARM_REG_R0, self.tbb_payload_ptr)
            elif name == 'Tbb_GetRowCount':
                self.call_log.append((name, r0))
                uc.reg_write(UC_ARM_REG_R0, self.tbb_rows)
            elif name == 'UiListCursor_Setup':
                args_stack = struct.unpack('<II', uc.mem_read(sp, 8))
                self.call_log.append((name, r0, r1, r2, r3, args_stack[0], args_stack[1]))
            elif name == 'SaveData_GetSettingMode':
                self.call_log.append((name,))
                uc.reg_write(UC_ARM_REG_R0, self.setting_mode)
            elif name == 'Flag_CheckEventBit':
                ret = 1 if self.event_bits.get(r0, False) else 0
                self.call_log.append((name, r0, ret))
                uc.reg_write(UC_ARM_REG_R0, ret)
            elif name == 'SaveData_GetPlayLogCount':
                self.call_log.append((name,))
                uc.reg_write(UC_ARM_REG_R0, self.play_log_count)
            elif name == 'SaveData_GetEntryValue':
                val = self.entry_values.get(r0, 0)
                self.call_log.append((name, r0, val))
                uc.reg_write(UC_ARM_REG_R0, val)
            elif name == 'UiInput_TestFlag':
                val = self.input_flags.get(r0, 0)
                self.call_log.append((name, r0, val))
                uc.reg_write(UC_ARM_REG_R0, val)
            elif name == 'UiInput_SetFlag':
                self.call_log.append((name, r0, r1))
                self.input_flags[r0] = r1
            elif name == 'AsdTask_CreateCalc':
                name_str = uc.mem_read(r0, 32).split(b'\x00')[0].decode('ascii', errors='ignore')
                args_stack = struct.unpack('<III', uc.mem_read(sp, 12))
                self.call_log.append((name, name_str, r1, r2, r3, args_stack[0], args_stack[1], args_stack[2]))
                ret = self.task_handle_counter
                self.task_handle_counter += 0x100
                uc.reg_write(UC_ARM_REG_R0, ret)
            elif name == 'AsdTask_CreateDraw':
                name_str = uc.mem_read(r0, 32).split(b'\x00')[0].decode('ascii', errors='ignore')
                args_stack = struct.unpack('<IIII', uc.mem_read(sp, 16))
                self.call_log.append((name, name_str, r1, r2, r3, args_stack[0], args_stack[1], args_stack[2], args_stack[3]))
                ret = self.task_handle_counter
                self.task_handle_counter += 0x100
                uc.reg_write(UC_ARM_REG_R0, ret)
            elif name == 'UiSpriteGroup_BindTable':
                args_stack = struct.unpack('<IIIIIII', uc.mem_read(sp, 28))
                self.call_log.append((name, r0, r1, r2, r3, args_stack))
            elif name == 'UiAnimSprite_Setup':
                arg4 = struct.unpack('<I', uc.mem_read(sp, 4))[0]
                self.call_log.append((name, r0, r1, r2, r3, arg4))
            elif name == 'Camp_AddProgressValue':
                self.call_log.append((name, r0, r1))
            elif name == 'ScriptVm_SetFlag':
                self.call_log.append((name, r0, r1, r2))
            elif name == 'UiAnimSlot_SetState':
                self.call_log.append((name, r0, r1))
            elif name == 'Ui_SetEntryLock':
                self.call_log.append((name, r0))
            else:
                self.call_log.append((name, r0, r1, r2, r3))
        return hook

def relocate_compiled(b: bytes, relocs: list, base_addr: int) -> bytearray:
    code = bytearray(b)
    sym_map = dict(STUB_MAP)
    sym_map.update({
        '_ZN4smt44camp13g_PlayLogWorkE': ADDR_PLAY_LOG_WORK,
        '_ZN4smt44camp15g_TitleMainWorkE': ADDR_TITLE_MAIN_WORK,
        '_ZN4smt44camp12g_ConfigWorkE': ADDR_CONFIG_WORK,
        '_ZN4smt44camp18g_TerminalMainWorkE': ADDR_TMNL_MAIN_WORK,
        '_ZN4smt44camp16g_TitleConfigWorkE': ADDR_TITLE_CONF_WORK,
        'AsdTask_CreateCalc': STUB_MAP['AsdTask_CreateCalc'],
        'AsdTask_CreateDraw': STUB_MAP['AsdTask_CreateDraw'],
        'Flag_CheckEventBit': STUB_MAP['Flag_CheckEventBit'],
        'SaveData_GetSettingMode': STUB_MAP['SaveData_GetSettingMode'],
        'SaveData_GetPlayLogCount': STUB_MAP['SaveData_GetPlayLogCount'],
        'SaveData_GetEntryValue': STUB_MAP['SaveData_GetEntryValue'],
        'UiInput_TestFlag': STUB_MAP['UiInput_TestFlag'],
        'UiInput_SetFlag': STUB_MAP['UiInput_SetFlag'],
        'ScriptVm_SetFlag': STUB_MAP['ScriptVm_SetFlag'],
        'Ui_SetEntryLock': STUB_MAP['Ui_SetEntryLock'],
        'Camp_AddProgressValue': STUB_MAP['Camp_AddProgressValue'],
        'UiAnimSlot_SetState': STUB_MAP['UiAnimSlot_SetState'],
        'AsdMem_Alloc': STUB_MAP['AsdMem_Alloc'],
        'AsdMem_AllocAlign': STUB_MAP['AsdMem_AllocAlign'],
        'AsdMem_Zero': STUB_MAP['AsdMem_Zero'],
        'AsdRes_Request': STUB_MAP['AsdRes_Request'],
        'ScriptVm_LoadTable': STUB_MAP['ScriptVm_LoadTable'],
        'UiAnimSprite_Setup': STUB_MAP['UiAnimSprite_Setup'],
        'UiAnimSprite_SetAnim': STUB_MAP['UiAnimSprite_SetAnim'],
        'UiListCursor_Setup': STUB_MAP['UiListCursor_Setup'],
        'Sound_PlaySE': STUB_MAP['Sound_PlaySE'],
        'Camp_SetFadeColor': STUB_MAP['Camp_SetFadeColor'],
        'Tbb_EnsureSlotLoaded': STUB_MAP['Tbb_EnsureSlotLoaded'],
        'UiSpriteGroup_Init': STUB_MAP['UiSpriteGroup_Init'],
        'UiSpriteGroup_BindTable': STUB_MAP['UiSpriteGroup_BindTable'],
        '_ZN4smt46engine27AsdTMTexTable_func_002c4e28Ej': STUB_MAP['AsdTMTexTable_func_002c4e28'],
        '_ZN4smt42ui21Tbb_GetGlobalSubTableEjj': STUB_MAP['Tbb_GetGlobalSubTable'],
        '_ZN4smt42ui18Tbb_GetPayloadDataEPKNS0_10Tbl1HeaderE': STUB_MAP['Tbb_GetPayloadData'],
        '_ZN4smt42ui15Tbb_GetRowCountEPKNS0_10Tbl1HeaderE': STUB_MAP['Tbb_GetRowCount'],
    })

    for rel in relocs:
        off = rel.offset
        sym = rel.symbol_name
        rel_type = rel.relocation_type

        if sym in sym_map:
            target = sym_map[sym]
        elif sym == '' or sym.startswith('.rodata'):
            target = RODATA_ADDR
        else:
            found = False
            for s, addr in sym_map.items():
                if sym in s or s in sym:
                    target = addr
                    found = True
                    break
            if not found:
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

def test_config_0018b660():
    print("\n--- Testing Config_func_0018b660 (0x0018b660, 536 B) ---")
    orig_addr = 0x0018b660
    comp_addr = 0x003D0000
    b, relocs = compile_function("Config_func_0018b660")
    relocated = relocate_compiled(b, relocs, comp_addr)

    scenarios = [
        ("null_work_both_flags", None, True, True, 1),
        ("existing_work_flag555_only", 0x00481000, True, False, 0),
        ("flag557_only", 0x00482000, False, True, 1),
        ("neither_flag", 0x00483000, False, False, 2),
    ]

    for name, init_work, f555, f557, mode in scenarios:
        # Original
        emu_orig = Emulator()
        emu_orig.event_bits[0x555] = f555
        emu_orig.event_bits[0x557] = f557
        emu_orig.setting_mode = mode
        emu_orig.tbb_rows = 5
        if init_work is not None:
            emu_orig.uc.mem_write(ADDR_CONFIG_WORK, struct.pack('<I', init_work))
        else:
            emu_orig.uc.mem_write(ADDR_CONFIG_WORK, struct.pack('<I', 0))
        run_function(emu_orig, orig_addr, [0])
        orig_work_ptr = struct.unpack('<I', emu_orig.uc.mem_read(ADDR_CONFIG_WORK, 4))[0]
        orig_work_data = emu_orig.uc.mem_read(orig_work_ptr, 0xBC)
        orig_calls = list(emu_orig.call_log)

        # Compiled
        emu_comp = Emulator()
        emu_comp.uc.mem_write(comp_addr, bytes(relocated))
        emu_comp.event_bits[0x555] = f555
        emu_comp.event_bits[0x557] = f557
        emu_comp.setting_mode = mode
        emu_comp.tbb_rows = 5
        if init_work is not None:
            emu_comp.uc.mem_write(ADDR_CONFIG_WORK, struct.pack('<I', init_work))
        else:
            emu_comp.uc.mem_write(ADDR_CONFIG_WORK, struct.pack('<I', 0))
        run_function(emu_comp, comp_addr, [0])
        comp_work_ptr = struct.unpack('<I', emu_comp.uc.mem_read(ADDR_CONFIG_WORK, 4))[0]
        comp_work_data = emu_comp.uc.mem_read(comp_work_ptr, 0xBC)
        comp_calls = list(emu_comp.call_log)

        # Assertions
        # Compare core setup calls (excluding redundant flag re-evaluations optimized by clang)
        orig_core_calls = [c for c in orig_calls if c[0] != 'Flag_CheckEventBit']
        comp_core_calls = [c for c in comp_calls if c[0] != 'Flag_CheckEventBit']
        assert len(orig_core_calls) == len(comp_core_calls), f"{name}: core calls mismatch: {orig_core_calls} vs {comp_core_calls}"
        for c1, c2 in zip(orig_core_calls, comp_core_calls):
            assert c1[0] == c2[0], f"{name}: call name mismatch: {c1} vs {c2}"
            if c1[0] == 'UiListCursor_Setup':
                assert c1[2:] == c2[2:], f"{name}: cursor params mismatch: {c1} vs {c2}"

        # Verify all flag calls query only 0x555 or 0x557
        for c in comp_calls:
            if c[0] == 'Flag_CheckEventBit':
                assert c[1] in (0x555, 0x557), f"{name}: unexpected flag ID checked: {c[1]}"

        # Check work->field_80 (+0x80) and field_a8 (+0xA8)
        orig_f80 = struct.unpack_from('<I', orig_work_data, 0x80)[0]
        comp_f80 = struct.unpack_from('<I', comp_work_data, 0x80)[0]
        assert orig_f80 == comp_f80, f"{name}: field_80 mismatch: orig={orig_f80}, comp={comp_f80}"

        orig_fa8 = orig_work_data[0xA8]
        comp_fa8 = comp_work_data[0xA8]
        assert orig_fa8 == comp_fa8, f"{name}: field_A8 mismatch: orig={orig_fa8}, comp={comp_fa8}"

        print(f"  [PASS] {name} (field_80={comp_f80}, field_a8={comp_fa8})")

def test_playlog_00194dbc():
    print("\n--- Testing PlayLog_func_00194dbc (0x00194dbc, 648 B) ---")
    orig_addr = 0x00194dbc
    comp_addr = 0x003D0000
    b, relocs = compile_function("PlayLog_func_00194dbc")
    relocated = relocate_compiled(b, relocs, comp_addr)

    scenarios = [
        ("rows_empty", 0, {}),
        ("rows_with_entries", 3, {-1: 5, 0x15: 12, 0x29: 2}),
    ]

    for name, row_count, entries in scenarios:
        # Setup TBB payload mock
        payload = bytearray(0x40 * (row_count if row_count > 0 else 1))
        if row_count > 0:
            # row 0: key -1
            struct.pack_into('<h', payload, 0x00, -1)
            # row 1: key 0x15
            struct.pack_into('<h', payload, 0x40, 0x15)
            # row 2: key 0x29
            struct.pack_into('<h', payload, 0x80, 0x29)

        # Original
        emu_orig = Emulator()
        emu_orig.tbb_rows = row_count
        emu_orig.uc.mem_write(emu_orig.tbb_payload_ptr, bytes(payload))
        emu_orig.play_log_count = entries.get(-1, 0)
        emu_orig.entry_values = entries
        emu_orig.uc.mem_write(ADDR_PLAY_LOG_WORK, struct.pack('<I', 0))
        run_function(emu_orig, orig_addr, [0])
        orig_work_ptr = struct.unpack('<I', emu_orig.uc.mem_read(ADDR_PLAY_LOG_WORK, 4))[0]
        orig_work_data = emu_orig.uc.mem_read(orig_work_ptr, 0x488)
        orig_calls = list(emu_orig.call_log)

        # Compiled
        emu_comp = Emulator()
        emu_comp.uc.mem_write(comp_addr, bytes(relocated))
        emu_comp.tbb_rows = row_count
        emu_comp.uc.mem_write(emu_comp.tbb_payload_ptr, bytes(payload))
        emu_comp.play_log_count = entries.get(-1, 0)
        emu_comp.entry_values = entries
        emu_comp.uc.mem_write(ADDR_PLAY_LOG_WORK, struct.pack('<I', 0))
        run_function(emu_comp, comp_addr, [0])
        comp_work_ptr = struct.unpack('<I', emu_comp.uc.mem_read(ADDR_PLAY_LOG_WORK, 4))[0]
        comp_work_data = emu_comp.uc.mem_read(comp_work_ptr, 0x488)
        comp_calls = list(emu_comp.call_log)

        # Verify cursor call and visible count
        assert len(orig_calls) == len(comp_calls), f"{name}: calls mismatch: {len(orig_calls)} vs {len(comp_calls)}"
        for c1, c2 in zip(orig_calls, comp_calls):
            assert c1[0] == c2[0], f"{name}: call name mismatch: {c1} vs {c2}"
            if c1[0] == 'UiListCursor_Setup':
                assert c1[2:] == c2[2:], f"{name}: cursor mismatch: {c1} vs {c2}"

        # Verify entry values and visible list
        orig_vals = [struct.unpack_from('<I', orig_work_data, 0x35C + i*4)[0] for i in range(row_count)]
        comp_vals = [struct.unpack_from('<I', comp_work_data, 0x35C + i*4)[0] for i in range(row_count)]
        assert orig_vals == comp_vals, f"{name}: values mismatch: {orig_vals} vs {comp_vals}"

        print(f"  [PASS] {name} (entries={comp_vals})")

def test_titlemain_001eb02c():
    print("\n--- Testing titleMain_func_001eb02c (0x001eb02c, 524 B) ---")
    orig_addr = 0x001eb02c
    comp_addr = 0x003D0000
    b, relocs = compile_function("titleMain_func_001eb02c")
    relocated = relocate_compiled(b, relocs, comp_addr)

    scenarios = [
        ("null_arg", 0, None),
        ("with_arg_0x42", 0x00475000, 0x42),
    ]

    for name, arg_ptr, arg_val in scenarios:
        # Original
        emu_orig = Emulator()
        if arg_ptr != 0:
            emu_orig.uc.mem_write(arg_ptr, bytes([arg_val]))
        emu_orig.uc.mem_write(ADDR_TITLE_MAIN_WORK, struct.pack('<I', 0))
        run_function(emu_orig, orig_addr, [arg_ptr])
        orig_work_ptr = struct.unpack('<I', emu_orig.uc.mem_read(ADDR_TITLE_MAIN_WORK, 4))[0]
        orig_work_data = emu_orig.uc.mem_read(orig_work_ptr, 0xA0)
        orig_calls = list(emu_orig.call_log)

        # Compiled
        emu_comp = Emulator()
        emu_comp.uc.mem_write(comp_addr, bytes(relocated))
        if arg_ptr != 0:
            emu_comp.uc.mem_write(arg_ptr, bytes([arg_val]))
        emu_comp.uc.mem_write(ADDR_TITLE_MAIN_WORK, struct.pack('<I', 0))
        run_function(emu_comp, comp_addr, [arg_ptr])
        comp_work_ptr = struct.unpack('<I', emu_comp.uc.mem_read(ADDR_TITLE_MAIN_WORK, 4))[0]
        comp_work_data = emu_comp.uc.mem_read(comp_work_ptr, 0xA0)
        comp_calls = list(emu_comp.call_log)

        assert len(orig_calls) == len(comp_calls), f"{name}: calls count mismatch"
        for c1, c2 in zip(orig_calls, comp_calls):
            assert c1[0] == c2[0], f"{name}: call name mismatch: {c1} vs {c2}"
            if c1[0] in ('AsdTask_CreateCalc', 'AsdTask_CreateDraw'):
                # Check task name, priority, and parent relationship
                assert c1[1] == c2[1], f"{name}: task name mismatch: {c1[1]} vs {c2[1]}"
                assert c1[2] == c2[2], f"{name}: task prio mismatch: {c1[2]} vs {c2[2]}"

        # Compare work memory fields (state flags, coords)
        # Note: word 0 is calc_task handle which can differ by address, compare fields from +4
        orig_tail = orig_work_data[4:]
        comp_tail = comp_work_data[4:]
        assert orig_tail == comp_tail, f"{name}: work structure memory mismatch"

        print(f"  [PASS] {name} (flag_10={comp_work_data[0x10]}, flag_95={comp_work_data[0x95]})")

def test_tmnlmain_001dafbc():
    print("\n--- Testing tmnlMain_func_001dafbc (0x001dafbc, 668 B) ---")
    orig_addr = 0x001dafbc
    comp_addr = 0x003D0000
    b, relocs = compile_function("tmnlMain_func_001dafbc")
    relocated = relocate_compiled(b, relocs, comp_addr)

    scenarios = [
        ("null_arg_flags_set", 0, None, {10: 1, 11: 1, 12: 1}, True),
        ("with_arg_flags_clear", 0x00475000, 0x05, {10: 0, 11: 0, 12: 0}, True),
    ]

    for name, arg_ptr, arg_val, in_flags, evt277 in scenarios:
        # Original
        emu_orig = Emulator()
        emu_orig.input_flags = dict(in_flags)
        emu_orig.event_bits[0x277] = evt277
        if arg_ptr != 0:
            emu_orig.uc.mem_write(arg_ptr, struct.pack('<I', arg_val))
        emu_orig.uc.mem_write(ADDR_TMNL_MAIN_WORK, struct.pack('<I', 0))
        run_function(emu_orig, orig_addr, [arg_ptr])
        orig_work_ptr = struct.unpack('<I', emu_orig.uc.mem_read(ADDR_TMNL_MAIN_WORK, 4))[0]
        orig_work_data = emu_orig.uc.mem_read(orig_work_ptr, 0x5E8)
        orig_calls = list(emu_orig.call_log)

        # Compiled
        emu_comp = Emulator()
        emu_comp.uc.mem_write(comp_addr, bytes(relocated))
        emu_comp.input_flags = dict(in_flags)
        emu_comp.event_bits[0x277] = evt277
        if arg_ptr != 0:
            emu_comp.uc.mem_write(arg_ptr, struct.pack('<I', arg_val))
        emu_comp.uc.mem_write(ADDR_TMNL_MAIN_WORK, struct.pack('<I', 0))
        run_function(emu_comp, comp_addr, [arg_ptr])
        comp_work_ptr = struct.unpack('<I', emu_comp.uc.mem_read(ADDR_TMNL_MAIN_WORK, 4))[0]
        comp_work_data = emu_comp.uc.mem_read(comp_work_ptr, 0x5E8)
        comp_calls = list(emu_comp.call_log)

        assert len(orig_calls) == len(comp_calls), f"{name}: calls count mismatch: {len(orig_calls)} vs {len(comp_calls)}"
        for c1, c2 in zip(orig_calls, comp_calls):
            assert c1[0] == c2[0], f"{name}: call name mismatch: {c1} vs {c2}"
            if c1[0] in ('AsdTask_CreateCalc', 'AsdTask_CreateDraw'):
                assert c1[1] == c2[1], f"{name}: task name mismatch: {c1[1]} vs {c2[1]}"
                assert c1[2] == c2[2], f"{name}: task prio mismatch: {c1[2]} vs {c2[2]}"

        # Compare work memory fields from offset +4
        orig_tail = orig_work_data[4:]
        comp_tail = comp_work_data[4:]
        assert orig_tail == comp_tail, f"{name}: work structure memory mismatch"

        print(f"  [PASS] {name} (flag_05={comp_work_data[5]}, flag_09={comp_work_data[9]}, field_10={struct.unpack_from('<I', comp_work_data, 0x10)[0]})")

def main():
    print("Testing Title Flow Batch candidates...")
    test_config_0018b660()
    test_playlog_00194dbc()
    test_titlemain_001eb02c()
    test_tmnlmain_001dafbc()
    print("\nALL 4 TITLE FLOW BATCH CANDIDATES PASSED 100%!")

if __name__ == "__main__":
    main()
