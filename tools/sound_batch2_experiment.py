#!/usr/bin/env python3
"""Differential test runner for asd_sound Batch 2 candidates against code.bin.

Tests:
  - 0x0010c078: AsdSoundSystem_func_0010c078 (380 B)
  - 0x0010c5d4: AsdSoundSystem_func_0010c5d4 (480 B)
  - 0x0010d40c: AsdSoundSystem_func_0010d40c (516 B)
  - 0x00109690: AsdSoundSystem_func_00109690 (1040 B)
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
SOURCE = ROOT / "src" / "engine" / "asd_sound.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STACK_BASE = 0x0FFF0000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

BUILD_DIR = ROOT / "build" / "sound_batch2"

ORIG_DATA = CODE_BIN.read_bytes()

COMPILED_FUNCTIONS = None
RODATA_ADDR = 0x004A0000
RODATA_BYTES = b""

# Globals
ADDR_SOUND_SYS   = 0x004E1F68
ADDR_SETTINGS    = 0x004E30EC
ADDR_FLAG        = 0x00476628
ADDR_MIX_LEVELS  = 0x004EFD2C
ADDR_LOCK        = 0x004E315C
ADDR_STREAM_SETT = 0x004E3138

# Stubs
STUB_BASE = 0x004B0000
STUB_MAP = {
    'AsdString_Strcpy': STUB_BASE + 0x00,
    'AsdMem_Compare': STUB_BASE + 0x08,
    'AsdSound_HasState': STUB_BASE + 0x10,
    'AsdSound_Shutdown': STUB_BASE + 0x18,
    'AsdSound_OpenArchive': STUB_BASE + 0x20,
    'AsdSound_GetBlockSize': STUB_BASE + 0x28,
    'AsdMem_AllocAlign': STUB_BASE + 0x30,
    'AsdSound_LoadData': STUB_BASE + 0x38,
    'AsdSound_GetDataSize': STUB_BASE + 0x40,
    'AsdSound_ParseContainer': STUB_BASE + 0x48,
    'AsdSound_GetContainerSize': STUB_BASE + 0x50,
    'AsdWork_Alloc2': STUB_BASE + 0x58,
    'AsdSound_GetSampleBytes': STUB_BASE + 0x60,
    'AsdSound_SetupContainer': STUB_BASE + 0x68,
    'AsdSoundVoice_GetBufferSize': STUB_BASE + 0x70,
    'AsdSoundVoice_AttachBuffer': STUB_BASE + 0x78,
    'AsdList_Append': STUB_BASE + 0x80,
    'AsdSound_UpdateListener': STUB_BASE + 0x88,
    'AsdSoundVoice_SetTarget': STUB_BASE + 0x90,
    'AsdSoundVoice_InitSlot': STUB_BASE + 0x98,
    'AsdFlag_TestAndSet': STUB_BASE + 0xA0,
    'engine_func_002c3aa8': STUB_BASE + 0xA8,
    'engine_func_002c3a24': STUB_BASE + 0xB0,
    'AsdMem_Alloc': STUB_BASE + 0xB8,
    'AsdData_GetBase': STUB_BASE + 0xC0,
    'AsdData_GetCount': STUB_BASE + 0xC8,
    'AsdData_GetEntry': STUB_BASE + 0xD0,
    'engine_func_002bd610': STUB_BASE + 0xD8,
    'AsdSoundVoice_Create': STUB_BASE + 0xE0,
    'AsdSoundVoice_SetParams': STUB_BASE + 0xE8,
    'AsdSoundVoice_SetVolume': STUB_BASE + 0xF0,
    'AsdSoundVoice_SetSpeed': STUB_BASE + 0xF8,
    'AsdSoundVoice_Clear': STUB_BASE + 0x100,
    'AsdSoundVoice_Attach': STUB_BASE + 0x108,
    'AsdSoundSlot_Attach': STUB_BASE + 0x110,
    'AsdSoundSlot_GetHandle': STUB_BASE + 0x118,
    'AsdSoundVoice_Stop': STUB_BASE + 0x120,
    'AsdSoundSlot_Stop': STUB_BASE + 0x128,
    'AsdSound_InitDsp': STUB_BASE + 0x130,
    'engine_func_002bce48': STUB_BASE + 0x138,
    'engine_func_0011be44': STUB_BASE + 0x140,
    'engine_func_0011cb3c': STUB_BASE + 0x148,
    'engine_func_002bce38': STUB_BASE + 0x150,
    'AsdSound_SetPhase': STUB_BASE + 0x158,
    'AsdSound_RequestMode': STUB_BASE + 0x160,
    'AsdSound_CreateEngine': STUB_BASE + 0x168,
    'AsdSound_InitEngine': STUB_BASE + 0x170,
}

ORIG_ADDR_MAP = {
    0x002bf86c: 'AsdString_Strcpy',
    0x002c1a48: 'AsdMem_Compare',
    0x002bf85c: 'AsdSound_HasState',
    0x001176e0: 'AsdSound_Shutdown',
    0x00121744: 'AsdSound_OpenArchive',
    0x00132a20: 'AsdSound_GetBlockSize',
    0x002c54f0: 'AsdMem_AllocAlign',
    0x001215ec: 'AsdSound_LoadData',
    0x00121f20: 'AsdSound_GetDataSize',
    0x00120f50: 'AsdSound_ParseContainer',
    0x00121f40: 'AsdSound_GetContainerSize',
    0x002bf798: 'AsdWork_Alloc2',
    0x00122094: 'AsdSound_GetSampleBytes',
    0x0012105c: 'AsdSound_SetupContainer',
    0x00120ef4: 'AsdSoundVoice_GetBufferSize',
    0x00120e68: 'AsdSoundVoice_AttachBuffer',
    0x002bf774: 'AsdList_Append',
    0x00119b48: 'AsdSound_UpdateListener',
    0x00120e14: 'AsdSoundVoice_SetTarget',
    0x00120dd4: 'AsdSoundVoice_InitSlot',
    0x002c00d4: 'AsdFlag_TestAndSet',
    0x002c3aa8: 'engine_func_002c3aa8',
    0x002c3a24: 'engine_func_002c3a24',
    0x002c4b84: 'AsdMem_Alloc',
    0x00128f34: 'AsdData_GetBase',
    0x00128f44: 'AsdData_GetCount',
    0x00128f58: 'AsdData_GetEntry',
    0x002bd610: 'engine_func_002bd610',
    0x002bd48c: 'AsdSoundVoice_Create',
    0x001537c4: 'AsdSoundVoice_SetParams',
    0x00147288: 'AsdSoundVoice_SetVolume',
    0x002bd46c: 'AsdSoundVoice_SetSpeed',
    0x002bd448: 'AsdSoundVoice_Clear',
    0x00128ff0: 'AsdSoundVoice_Attach',
    0x00121a98: 'AsdSoundSlot_Attach',
    0x00121b50: 'AsdSoundSlot_GetHandle',
    0x002bdc08: 'AsdSoundVoice_Stop',
    0x002bd3fc: 'AsdSoundSlot_Stop',
    0x0011bd78: 'AsdSound_InitDsp',
    0x002bce48: 'engine_func_002bce48',
    0x0011be44: 'engine_func_0011be44',
    0x0011cb3c: 'engine_func_0011cb3c',
    0x002bce38: 'engine_func_002bce38',
    0x0012a664: 'AsdSound_SetPhase',
    0x0011cc34: 'AsdSound_RequestMode',
    0x00120d44: 'AsdSound_CreateEngine',
    0x00120ac8: 'AsdSound_InitEngine',
}

def compile_function(func_name: str, out: Path = BUILD_DIR, source: Path = SOURCE):
    global COMPILED_FUNCTIONS, RODATA_BYTES
    if COMPILED_FUNCTIONS is None:
        out.mkdir(parents=True, exist_ok=True)
        obj = out / "asd_sound.o"
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
        self.has_state_val = 0
        self.test_and_set_val = 1
        self.dsp_val = 0

        self._install_stubs()

    def _install_stubs(self):
        bx_lr = struct.pack('<I', 0xe12fff1e)

        # Hook all stub targets
        for name, addr in STUB_MAP.items():
            self.uc.mem_write(addr, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._make_hook(name), begin=addr, end=addr)

        # Also hook original binary targets
        for addr, name in ORIG_ADDR_MAP.items():
            if addr in (0x002c00d4, 0x002c1a48):
                # Thumb function: write Thumb "bx lr" (0x4770)
                self.uc.mem_write(addr, struct.pack('<H', 0x4770))
            else:
                self.uc.mem_write(addr, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._make_hook(name), begin=addr, end=addr)

    def _make_hook(self, name):
        def hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            sp = uc.reg_read(UC_ARM_REG_SP)

            if name == 'AsdString_Strcpy':
                src_str = uc.mem_read(r1, 64).split(b'\x00')[0]
                uc.mem_write(r0, bytes(src_str + b'\x00'))
                self.call_log.append((name, src_str.decode('ascii', errors='ignore')))
            elif name == 'AsdMem_Compare':
                b0 = uc.mem_read(r0, r2)
                b1 = uc.mem_read(r1, r2)
                ret = 0 if b0 == b1 else 1
                self.call_log.append((name, bytes(b0), bytes(b1), r2))
                uc.reg_write(UC_ARM_REG_R0, ret)
            elif name == 'AsdSound_HasState':
                self.call_log.append((name, r0))
                uc.reg_write(UC_ARM_REG_R0, self.has_state_val)
            elif name in ('AsdSound_GetBlockSize', 'AsdSound_GetDataSize', 'AsdSound_GetContainerSize', 'AsdSound_GetSampleBytes'):
                self.call_log.append((name, r0, r1))
                uc.reg_write(UC_ARM_REG_R0, 0x1000)
            elif name == 'AsdSoundVoice_GetBufferSize':
                self.call_log.append((name, r0))
                uc.reg_write(UC_ARM_REG_R0, 0x500)
            elif name in ('AsdMem_AllocAlign', 'AsdWork_Alloc2', 'AsdMem_Alloc'):
                arg4 = struct.unpack('<I', uc.mem_read(sp, 4))[0]
                self.call_log.append((name, r0, r1, r2, r3, arg4))
                ret = self.alloc_ptr
                self.alloc_ptr += (r3 + 0xFF) & ~0xFF
                uc.reg_write(UC_ARM_REG_R0, ret)
            elif name == 'AsdFlag_TestAndSet':
                self.call_log.append((name, r0))
                uc.reg_write(UC_ARM_REG_R0, self.test_and_set_val)
            elif name == 'AsdData_GetBase':
                self.call_log.append((name, r0))
                uc.reg_write(UC_ARM_REG_R0, r0 + 0x10)
            elif name == 'AsdData_GetCount':
                self.call_log.append((name, r0))
                uc.reg_write(UC_ARM_REG_R0, 4)
            elif name == 'AsdData_GetEntry':
                self.call_log.append((name, r0, r1))
                uc.reg_write(UC_ARM_REG_R0, r0 + 0x20)
            elif name == 'AsdSoundVoice_Create':
                self.call_log.append((name, r0, r1, r2))
                uc.reg_write(UC_ARM_REG_R0, 0x00483330)
            elif name in ('AsdSound_InitDsp', 'engine_func_0011be44', 'engine_func_0011cb3c', 'AsdSound_Shutdown'):
                self.call_log.append((name,))
                uc.reg_write(UC_ARM_REG_R0, self.dsp_val)
            elif name == 'AsdSound_CreateEngine':
                self.call_log.append((name, r0))
                uc.reg_write(UC_ARM_REG_R0, 0x1800)
            elif name == 'AsdSound_OpenArchive':
                self.call_log.append((name, r0, r1))
                uc.reg_write(UC_ARM_REG_R0, 0)
            elif name == 'AsdSound_SetupContainer':
                s_args = struct.unpack('<III', uc.mem_read(sp, 12))
                self.call_log.append((name, r0, r1, r2, r3, s_args))
                uc.reg_write(UC_ARM_REG_R0, 0)
            elif name == 'AsdSoundVoice_InitSlot':
                self.call_log.append((name, r0, r1, r2))
            elif name == 'AsdSoundVoice_SetTarget':
                self.call_log.append((name, r0, r1))
            elif name == 'AsdSound_UpdateListener':
                self.call_log.append((name, 'stack_ptr' if (r0 & 0x0FFF0000) == 0x0FFF0000 else r0))
            elif name == 'AsdList_Append':
                self.call_log.append((name, r0, r1, r2))
                uc.reg_write(UC_ARM_REG_R0, 0)
            elif name in ('AsdSoundSlot_Stop', 'AsdSoundVoice_Stop'):
                self.call_log.append((name, r0, r1))
            else:
                self.call_log.append((name, r0, r1, r2, r3))
        return hook

def relocate_compiled(b: bytes, relocs: list, base_addr: int) -> bytearray:
    code = bytearray(b)
    sym_map = dict(STUB_MAP)
    sym_map.update({
        '_ZN4smt46engine16g_AsdSoundSystemE': ADDR_SOUND_SYS,
        '_ZN4smt46engine18g_AsdSoundSettingsE': ADDR_SETTINGS,
        '_ZN4smt46engine14g_AsdSoundFlagE': ADDR_FLAG,
        '_ZN4smt46engine19g_AsdSoundMixLevelsE': ADDR_MIX_LEVELS,
        '_ZN4smt46engine14g_AsdSoundLockE': ADDR_LOCK,
        '_ZN4smt46engine16g_AsdSoundStreamE': ADDR_STREAM_SETT,
    })

    for rel in relocs:
        off = rel.offset
        sym = rel.symbol_name
        rel_type = rel.relocation_type

        if sym in sym_map:
            target = sym_map[sym]
        elif sym == '':
            target = RODATA_ADDR
        else:
            raise RuntimeError(f"Unmapped relocation: {sym}")

        if rel_type in (28, 29): # R_ARM_CALL / R_ARM_JUMP24
            curr = struct.unpack_from('<I', code, off)[0]
            disp = (target - (base_addr + off + 8)) >> 2
            new_disp = disp & 0x00FFFFFF
            new_inst = (curr & 0xFF000000) | new_disp
            struct.pack_into('<I', code, off, new_inst)
        elif rel_type == 2: # R_ARM_ABS32
            curr = struct.unpack_from('<I', code, off)[0]
            struct.pack_into('<I', code, off, target + curr)
        else:
            raise RuntimeError(f"Unsupported relocation type: {rel_type}")

    return code

def test_sound_batch2():
    print("Testing Sound Batch 2 candidates...")

    funcs = [
        ("AsdSoundSystem_func_0010c078", 0x0010c078, 380),
        ("AsdSoundSystem_func_0010c5d4", 0x0010c5d4, 480),
        ("AsdSoundSystem_func_0010d40c", 0x0010d40c, 516),
        ("AsdSoundSystem_func_00109690", 0x00109690, 1040),
    ]

    for name, orig_addr, orig_size in funcs:
        print(f"\n--- Testing {name} (0x{orig_addr:08x}, {orig_size} B) ---")
        compiled_bytes, relocs = compile_function(name)
        comp_addr = 0x00490000
        relocated_code = relocate_compiled(compiled_bytes, relocs, comp_addr)

        if name == "AsdSoundSystem_func_0010c078":
            cases = [
                ("stream_obj_1", 0x00450000, 0x1000, 0x12),
                ("stream_obj_2", 0x00450000, 0x2400, 0),
            ]
            for label, data_ptr, size, extra in cases:
                emu_orig = Emulator()
                emu_orig.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
                ret_addr = 0x004FFF00
                emu_orig.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
                emu_orig.uc.reg_write(UC_ARM_REG_LR, ret_addr)

                emu_orig.uc.reg_write(UC_ARM_REG_R0, data_ptr)
                emu_orig.uc.reg_write(UC_ARM_REG_R1, size)
                emu_orig.uc.reg_write(UC_ARM_REG_R2, extra)

                emu_orig.uc.emu_start(orig_addr, ret_addr, timeout=5000000)
                orig_ret = emu_orig.uc.reg_read(UC_ARM_REG_R0)
                orig_mem = emu_orig.uc.mem_read(orig_ret, 0x98)
                orig_calls = list(emu_orig.call_log)

                emu_comp = Emulator()
                emu_comp.uc.mem_write(comp_addr, bytes(relocated_code))
                emu_comp.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
                emu_comp.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
                emu_comp.uc.reg_write(UC_ARM_REG_LR, ret_addr)

                emu_comp.uc.reg_write(UC_ARM_REG_R0, data_ptr)
                emu_comp.uc.reg_write(UC_ARM_REG_R1, size)
                emu_comp.uc.reg_write(UC_ARM_REG_R2, extra)

                emu_comp.uc.emu_start(comp_addr, ret_addr, timeout=5000000)
                comp_ret = emu_comp.uc.reg_read(UC_ARM_REG_R0)
                comp_mem = emu_comp.uc.mem_read(comp_ret, 0x98)
                comp_calls = list(emu_comp.call_log)

                assert orig_mem == comp_mem, f"{label}: object memory mismatch"
                assert orig_calls == comp_calls, f"{label}: calls mismatch\norig: {orig_calls}\ncomp: {comp_calls}"
                print(f"  [PASS] {label} (obj={orig_ret:#x})")

        elif name == "AsdSoundSystem_func_0010c5d4":
            cases = [
                ("out_of_bounds", 4, 0x400, [0, 0, 0, 0]),
                ("already_open", 1, 0x400, [0, 1, 0, 0]),
                ("open_slot_0_size_0", 0, 0, [0, 0, 0, 0]),
                ("open_slot_2_with_size", 2, 0x500, [0, 0, 0, 0]),
            ]
            for label, idx, size, flags in cases:
                emu_orig = Emulator()
                emu_orig.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
                ret_addr = 0x004FFF00
                emu_orig.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
                emu_orig.uc.reg_write(UC_ARM_REG_LR, ret_addr)

                emu_orig.uc.reg_write(UC_ARM_REG_R0, idx)
                emu_orig.uc.reg_write(UC_ARM_REG_R1, size)

                # Initialize sequences and stream settings
                emu_orig.uc.mem_write(ADDR_SOUND_SYS + 0x694, b'\x00' * (0x3C * 4))
                for i, f in enumerate(flags):
                    emu_orig.uc.mem_write(ADDR_SOUND_SYS + 0x694 + i * 0x3C + 0x3A, struct.pack('B', f))
                emu_orig.uc.mem_write(ADDR_SOUND_SYS + 0x1218, struct.pack('<I', 0))
                emu_orig.uc.mem_write(ADDR_STREAM_SETT, b'\x00' * 0x34)

                emu_orig.uc.emu_start(orig_addr, ret_addr, timeout=5000000)
                orig_ret = emu_orig.uc.reg_read(UC_ARM_REG_R0)
                orig_seq = emu_orig.uc.mem_read(ADDR_SOUND_SYS + 0x694, 0x3C * 4)
                orig_stream = emu_orig.uc.mem_read(ADDR_STREAM_SETT, 0x34)
                orig_active = struct.unpack('<I', emu_orig.uc.mem_read(ADDR_SOUND_SYS + 0x1218, 4))[0]
                orig_calls = list(emu_orig.call_log)

                emu_comp = Emulator()
                emu_comp.uc.mem_write(comp_addr, bytes(relocated_code))
                emu_comp.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
                emu_comp.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
                emu_comp.uc.reg_write(UC_ARM_REG_LR, ret_addr)

                emu_comp.uc.reg_write(UC_ARM_REG_R0, idx)
                emu_comp.uc.reg_write(UC_ARM_REG_R1, size)

                emu_comp.uc.mem_write(ADDR_SOUND_SYS + 0x694, b'\x00' * (0x3C * 4))
                for i, f in enumerate(flags):
                    emu_comp.uc.mem_write(ADDR_SOUND_SYS + 0x694 + i * 0x3C + 0x3A, struct.pack('B', f))
                emu_comp.uc.mem_write(ADDR_SOUND_SYS + 0x1218, struct.pack('<I', 0))
                emu_comp.uc.mem_write(ADDR_STREAM_SETT, b'\x00' * 0x34)

                emu_comp.uc.emu_start(comp_addr, ret_addr, timeout=5000000)
                comp_ret = emu_comp.uc.reg_read(UC_ARM_REG_R0)
                comp_seq = emu_comp.uc.mem_read(ADDR_SOUND_SYS + 0x694, 0x3C * 4)
                comp_stream = emu_comp.uc.mem_read(ADDR_STREAM_SETT, 0x34)
                comp_active = struct.unpack('<I', emu_comp.uc.mem_read(ADDR_SOUND_SYS + 0x1218, 4))[0]
                comp_calls = list(emu_comp.call_log)

                assert orig_ret == comp_ret, f"{label}: return value mismatch ({orig_ret} vs {comp_ret})"
                assert orig_seq == comp_seq, f"{label}: sequence memory mismatch"
                assert orig_stream == comp_stream, f"{label}: stream settings memory mismatch"
                assert orig_active == comp_active, f"{label}: active sequence mismatch ({orig_active:#x} vs {comp_active:#x})"
                assert orig_calls == comp_calls, f"{label}: calls mismatch\norig: {orig_calls}\ncomp: {comp_calls}"
                print(f"  [PASS] {label} (ret={orig_ret}, active={orig_active:#x})")

        elif name == "AsdSoundSystem_func_0010d40c":
            cases = [
                ("duration_0", 0),
                ("duration_pos", 100),
            ]
            for label, dur in cases:
                emu_orig = Emulator()
                emu_orig.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
                ret_addr = 0x004FFF00
                emu_orig.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
                emu_orig.uc.reg_write(UC_ARM_REG_LR, ret_addr)

                emu_orig.uc.reg_write(UC_ARM_REG_R0, dur)

                emu_orig.uc.mem_write(ADDR_SOUND_SYS, b'\x00' * 0x1220)
                emu_orig.uc.mem_write(ADDR_STREAM_SETT, b'\x00' * 0x34)

                emu_orig.uc.emu_start(orig_addr, ret_addr, timeout=5000000)
                orig_sys = emu_orig.uc.mem_read(ADDR_SOUND_SYS, 0x1220)
                orig_stream = emu_orig.uc.mem_read(ADDR_STREAM_SETT, 0x34)
                orig_calls = list(emu_orig.call_log)

                emu_comp = Emulator()
                emu_comp.uc.mem_write(comp_addr, bytes(relocated_code))
                emu_comp.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
                emu_comp.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
                emu_comp.uc.reg_write(UC_ARM_REG_LR, ret_addr)

                emu_comp.uc.reg_write(UC_ARM_REG_R0, dur)

                emu_comp.uc.mem_write(ADDR_SOUND_SYS, b'\x00' * 0x1220)
                emu_comp.uc.mem_write(ADDR_STREAM_SETT, b'\x00' * 0x34)

                emu_comp.uc.emu_start(comp_addr, ret_addr, timeout=5000000)
                comp_sys = emu_comp.uc.mem_read(ADDR_SOUND_SYS, 0x1220)
                comp_stream = emu_comp.uc.mem_read(ADDR_STREAM_SETT, 0x34)
                comp_calls = list(emu_comp.call_log)

                assert orig_sys == comp_sys, f"{label}: system memory mismatch"
                assert orig_stream == comp_stream, f"{label}: stream settings memory mismatch"
                assert orig_calls == comp_calls, f"{label}: calls mismatch\norig: {orig_calls}\ncomp: {comp_calls}"
                print(f"  [PASS] {label}")

        elif name == "AsdSoundSystem_func_00109690":
            cases = [
                ("rom_path_enable_1", b"rom:/sound/archive.bin\x00", 1, 0, 0, 1),
                ("raw_path_enable_0", b"data:/sound/archive.bin\x00", 0, 0x1000, 1, 0),
            ]
            archive_buf_addr = 0x00460000
            for label, archive_str, enable, size, has_state, settings_48 in cases:
                emu_orig = Emulator()
                emu_orig.has_state_val = has_state
                emu_orig.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
                ret_addr = 0x004FFF00
                emu_orig.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
                emu_orig.uc.reg_write(UC_ARM_REG_LR, ret_addr)

                emu_orig.uc.mem_write(archive_buf_addr, archive_str)
                emu_orig.uc.reg_write(UC_ARM_REG_R0, archive_buf_addr)
                emu_orig.uc.reg_write(UC_ARM_REG_R1, enable)
                emu_orig.uc.reg_write(UC_ARM_REG_R2, size)

                emu_orig.uc.mem_write(ADDR_SOUND_SYS, b'\x00' * 0x1220)
                emu_orig.uc.mem_write(ADDR_SETTINGS + 0x48, struct.pack('B', settings_48))
                emu_orig.uc.mem_write(ADDR_FLAG, struct.pack('<I', 0))

                emu_orig.uc.emu_start(orig_addr, ret_addr, timeout=5000000)
                orig_ret = emu_orig.uc.reg_read(UC_ARM_REG_R0)
                orig_sys = emu_orig.uc.mem_read(ADDR_SOUND_SYS, 0x1220)
                orig_calls = list(emu_orig.call_log)

                emu_comp = Emulator()
                emu_comp.has_state_val = has_state
                emu_comp.uc.mem_write(comp_addr, bytes(relocated_code))
                emu_comp.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
                emu_comp.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
                emu_comp.uc.reg_write(UC_ARM_REG_LR, ret_addr)

                emu_comp.uc.mem_write(archive_buf_addr, archive_str)
                emu_comp.uc.reg_write(UC_ARM_REG_R0, archive_buf_addr)
                emu_comp.uc.reg_write(UC_ARM_REG_R1, enable)
                emu_comp.uc.reg_write(UC_ARM_REG_R2, size)

                emu_comp.uc.mem_write(ADDR_SOUND_SYS, b'\x00' * 0x1220)
                emu_comp.uc.mem_write(ADDR_SETTINGS + 0x48, struct.pack('B', settings_48))
                emu_comp.uc.mem_write(ADDR_FLAG, struct.pack('<I', 0))

                emu_comp.uc.emu_start(comp_addr, ret_addr, timeout=5000000)
                comp_ret = emu_comp.uc.reg_read(UC_ARM_REG_R0)
                comp_sys = emu_comp.uc.mem_read(ADDR_SOUND_SYS, 0x1220)
                comp_calls = list(emu_comp.call_log)

                assert orig_ret == comp_ret, f"{label}: return value mismatch ({orig_ret} vs {comp_ret})"
                assert orig_sys == comp_sys, f"{label}: system memory mismatch"
                assert orig_calls == comp_calls, f"{label}: calls mismatch\norig: {orig_calls}\ncomp: {comp_calls}"
                print(f"  [PASS] {label} (ret={orig_ret})")

    print("\nALL 4 SOUND BATCH 2 CANDIDATES PASSED 100%!")

if __name__ == "__main__":
    test_sound_batch2()
