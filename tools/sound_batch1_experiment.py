#!/usr/bin/env python3
"""Differential test runner for asd_sound Batch 1 candidates against code.bin.

Tests:
  - 0x0010368c: soundEffect_func_0010368c (184 B)
  - 0x00109524: soundEffect_func_00109524 (240 B)
  - 0x0010b974: AsdSoundSystem_func_0010b974 (176 B)
  - 0x001ea808: soundTest_func_001ea808 (264 B)
  - 0x002c1df4: AsdSoundSystem_func_002c1df4 (308 B)
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

BUILD_DIR = ROOT / "build" / "sound_batch1"

ORIG_DATA = CODE_BIN.read_bytes()

COMPILED_FUNCTIONS = None
RODATA_ADDR = 0x004A0000
RODATA_BYTES = b""

# Global addresses
ADDR_UNIT_A = 0x004C5484
ADDR_CFG_A  = 0x004C54E4
ADDR_UNIT_B = 0x004C54F4
ADDR_CFG_B  = 0x004C5604
ADDR_EFFECT_BUFS = 0x0044E0E0
ADDR_SOUND_SYS = 0x004E1F68
ADDR_SYS_HANDLE = 0x004E23E0
ADDR_SOUND_TEST_OBJ = 0x0044E110

# Stubs for external calls (placed in an unused area of CODE_BASE)
STUB_BASE = 0x004B0000
STUB_ALLOC_ALIGN = STUB_BASE + 0x00
STUB_ALLOC       = STUB_BASE + 0x10
STUB_GET_TABLE   = STUB_BASE + 0x20
STUB_CFG_A       = STUB_BASE + 0x30
STUB_SIZE_A      = STUB_BASE + 0x40
STUB_SET_BUF_A   = STUB_BASE + 0x50
STUB_CFG_B       = STUB_BASE + 0x60
STUB_SIZE_B      = STUB_BASE + 0x70
STUB_SET_BUF_B   = STUB_BASE + 0x80
STUB_DISPATCH    = STUB_BASE + 0x90
STUB_HAS_STATE   = STUB_BASE + 0xA0
STUB_STREAM_SIZE = STUB_BASE + 0xB0
STUB_LOAD_DATA   = STUB_BASE + 0xC0
STUB_SLOT_ATTACH = STUB_BASE + 0xD0
STUB_SLOT_HANDLE = STUB_BASE + 0xE0
STUB_TASK_CALC   = STUB_BASE + 0xF0
STUB_TASK_DRAW   = STUB_BASE + 0x100

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

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
        # Map code and data regions
        self.uc.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
        self.uc.mem_write(CODE_BASE, ORIG_DATA[:CODE_SIZE])

        # Map stack
        self.uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)

        # Map rodata if present
        if RODATA_BYTES:
            self.uc.mem_write(RODATA_ADDR, RODATA_BYTES)

        # Enable VFP
        try:
            self.uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
            self.uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
        except Exception:
            pass

        # Call log for mock stubs
        self.call_log = []
        self.table_entry_val = 0
        self.alloc_ptr = 0x00480000
        self.has_state_val = 0

        # Install stubs
        self._install_stubs()

    def _install_stubs(self):
        # Write "bx lr" (0xe12fff1e) to each stub address
        bx_lr = struct.pack('<I', 0xe12fff1e)
        stubs = [
            (STUB_ALLOC_ALIGN, self._hook_alloc_align),
            (STUB_ALLOC, self._hook_alloc),
            (STUB_GET_TABLE, self._hook_get_table),
            (STUB_CFG_A, self._hook_cfg_a),
            (STUB_SIZE_A, self._hook_size_a),
            (STUB_SET_BUF_A, self._hook_set_buf_a),
            (STUB_CFG_B, self._hook_cfg_b),
            (STUB_SIZE_B, self._hook_size_b),
            (STUB_SET_BUF_B, self._hook_set_buf_b),
            (STUB_DISPATCH, self._hook_dispatch),
            (STUB_HAS_STATE, self._hook_has_state),
            (STUB_STREAM_SIZE, self._hook_stream_size),
            (STUB_LOAD_DATA, self._hook_load_data),
            (STUB_SLOT_ATTACH, self._hook_slot_attach),
            (STUB_SLOT_HANDLE, self._hook_slot_handle),
            (STUB_TASK_CALC, self._hook_task_calc),
            (STUB_TASK_DRAW, self._hook_task_draw),
            (0x002c583c, self._hook_get_table),
            (0x00110c60, self._hook_cfg_a),
            (0x00110c44, self._hook_size_a),
            (0x00110c2c, self._hook_set_buf_a),
            (0x00121208, self._hook_cfg_b),
            (0x00121168, self._hook_size_b),
            (0x00121150, self._hook_set_buf_b),
            (0x00120ce4, self._hook_dispatch),
            (0x002c54f0, self._hook_alloc_align),
            (0x002c4b84, self._hook_alloc),
            (0x002bf85c, self._hook_has_state),
            (0x00132aa0, self._hook_stream_size),
            (0x00121694, self._hook_load_data),
            (0x00121a98, self._hook_slot_attach),
            (0x00121b50, self._hook_slot_handle),
            (0x002c5978, self._hook_task_calc),
            (0x002c4c00, self._hook_task_draw),
        ]
        for addr, cb in stubs:
            self.uc.mem_write(addr, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, cb, begin=addr, end=addr)

    def _hook_alloc_align(self, uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        r3 = uc.reg_read(UC_ARM_REG_R3)
        sp = uc.reg_read(UC_ARM_REG_SP)
        arg4 = struct.unpack('<I', uc.mem_read(sp, 4))[0]
        self.call_log.append(('AsdMem_AllocAlign', r0, r1, r2, r3, arg4))
        ret = self.alloc_ptr
        self.alloc_ptr += (r3 + 0xFF) & ~0xFF
        uc.reg_write(UC_ARM_REG_R0, ret)

    def _hook_alloc(self, uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        r3 = uc.reg_read(UC_ARM_REG_R3)
        sp = uc.reg_read(UC_ARM_REG_SP)
        arg4 = struct.unpack('<I', uc.mem_read(sp, 4))[0]
        self.call_log.append(('AsdMem_Alloc', r0, r1, r2, r3, arg4))
        ret = self.alloc_ptr
        self.alloc_ptr += (r3 + 0xFF) & ~0xFF
        uc.reg_write(UC_ARM_REG_R0, ret)

    def _hook_get_table(self, uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        self.call_log.append(('AsdSound_GetTableEntry', r0))
        uc.reg_write(UC_ARM_REG_R0, self.table_entry_val)

    def _hook_cfg_a(self, uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        self.call_log.append(('AsdSoundEffect_Configure', r0, r1))
        uc.reg_write(UC_ARM_REG_R0, 0)

    def _hook_size_a(self, uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        self.call_log.append(('AsdSoundEffect_GetBufferSize', r0))
        uc.reg_write(UC_ARM_REG_R0, 0x1000)

    def _hook_set_buf_a(self, uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        self.call_log.append(('AsdSoundEffect_SetBuffer', r0, r1, r2))
        uc.reg_write(UC_ARM_REG_R0, 0)

    def _hook_cfg_b(self, uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        self.call_log.append(('AsdSoundEffect2_Configure', r0, r1))
        uc.reg_write(UC_ARM_REG_R0, 0)

    def _hook_size_b(self, uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        self.call_log.append(('AsdSoundEffect2_GetBufferSize', r0))
        uc.reg_write(UC_ARM_REG_R0, 0x2000)

    def _hook_set_buf_b(self, uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        self.call_log.append(('AsdSoundEffect2_SetBuffer', r0, r1, r2))
        uc.reg_write(UC_ARM_REG_R0, 0)

    def _hook_dispatch(self, uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        self.call_log.append(('AsdSound_Dispatch', r0, r1))
        uc.reg_write(UC_ARM_REG_R0, 0)

    def _hook_has_state(self, uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        self.call_log.append(('AsdSound_HasState', r0))
        uc.reg_write(UC_ARM_REG_R0, self.has_state_val)

    def _hook_stream_size(self, uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        self.call_log.append(('AsdSound_GetStreamBlockSize', r0))
        uc.reg_write(UC_ARM_REG_R0, 0x4000)

    def _hook_load_data(self, uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        self.call_log.append(('AsdSound_LoadDataPersistent', r0, r1, r2))
        uc.reg_write(UC_ARM_REG_R0, 0)

    def _hook_slot_attach(self, uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        self.call_log.append(('AsdSoundSlot_Attach', r0, r1, r2))
        uc.reg_write(UC_ARM_REG_R0, 0)

    def _hook_slot_handle(self, uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        self.call_log.append(('AsdSoundSlot_GetHandle', r0))
        uc.reg_write(UC_ARM_REG_R0, 0x77)

    def _hook_task_calc(self, uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        r3 = uc.reg_read(UC_ARM_REG_R3)
        sp = uc.reg_read(UC_ARM_REG_SP)
        args_stack = struct.unpack('<III', uc.mem_read(sp, 12))
        name = uc.mem_read(r0, 16).split(b'\x00')[0].decode('ascii', errors='ignore')
        self.call_log.append(('AsdTask_CreateCalc', name, r1, r2, r3, args_stack))
        ret = 0x00481234
        uc.reg_write(UC_ARM_REG_R0, ret)

    def _hook_task_draw(self, uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        r3 = uc.reg_read(UC_ARM_REG_R3)
        sp = uc.reg_read(UC_ARM_REG_SP)
        args_stack = struct.unpack('<IIII', uc.mem_read(sp, 16))
        name = uc.mem_read(r0, 16).split(b'\x00')[0].decode('ascii', errors='ignore')
        self.call_log.append(('AsdTask_CreateDraw', name, r1, r2, r3, args_stack))
        ret = 0x00485678
        uc.reg_write(UC_ARM_REG_R0, ret)

def relocate_compiled(b: bytes, relocs: list, base_addr: int) -> bytearray:
    code = bytearray(b)
    # Symbol mapping for compiled relocations
    sym_map = {
        'AsdSound_GetTableEntry': STUB_GET_TABLE,
        'AsdSoundEffect_Configure': STUB_CFG_A,
        'AsdSoundEffect_GetBufferSize': STUB_SIZE_A,
        'AsdMem_AllocAlign': STUB_ALLOC_ALIGN,
        'AsdSoundEffect_SetBuffer': STUB_SET_BUF_A,
        'AsdSound_Dispatch': STUB_DISPATCH,
        '_ZN4smt46engine25soundEffect_func_00109524Ev': 0x00109524,
        '_ZN4smt46engine21g_AsdSoundEffectUnitAE': ADDR_UNIT_A,
        '_ZN4smt46engine23g_AsdSoundEffectConfigAE': ADDR_CFG_A,
        '_ZN4smt46engine23g_AsdSoundEffectBuffersE': ADDR_EFFECT_BUFS,
        'AsdSoundEffect2_Configure': STUB_CFG_B,
        'AsdSoundEffect2_GetBufferSize': STUB_SIZE_B,
        'AsdSoundEffect2_SetBuffer': STUB_SET_BUF_B,
        '_ZN4smt46engine21g_AsdSoundEffectUnitBE': ADDR_UNIT_B,
        '_ZN4smt46engine23g_AsdSoundEffectConfigBE': ADDR_CFG_B,
        'AsdSound_HasState': STUB_HAS_STATE,
        'AsdSound_GetStreamBlockSize': STUB_STREAM_SIZE,
        'AsdSound_LoadDataPersistent': STUB_LOAD_DATA,
        '_ZN4smt46engine16g_AsdSoundSystemE': ADDR_SOUND_SYS,
        '_ZN4smt46engine22g_AsdSoundSystemHandleE': ADDR_SYS_HANDLE,
        'AsdSoundSlot_Attach': STUB_SLOT_ATTACH,
        'AsdSoundSlot_GetHandle': STUB_SLOT_HANDLE,
        'AsdMem_Alloc': STUB_ALLOC,
        'AsdTask_CreateCalc': STUB_TASK_CALC,
        'AsdTask_CreateDraw': STUB_TASK_DRAW,
        '_ZN4smt46engine17g_SoundTestObjectE': ADDR_SOUND_TEST_OBJ,
    }

    for rel in relocs:
        off = rel.offset
        sym = rel.symbol_name
        rel_type = rel.relocation_type

        if sym in sym_map:
            target = sym_map[sym]
        elif sym == '':
            # rodata literal reference
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

def test_sound_batch1():
    print("Testing Sound Batch 1 candidates...")

    funcs = [
        ("soundEffect_func_0010368c", 0x0010368c, 184),
        ("soundEffect_func_00109524", 0x00109524, 240),
        ("AsdSoundSystem_func_0010b974", 0x0010b974, 176),
        ("soundTest_func_001ea808", 0x001ea808, 264),
        ("AsdSoundSystem_func_002c1df4", 0x002c1df4, 308),
    ]

    for name, orig_addr, orig_size in funcs:
        print(f"\n--- Testing {name} (0x{orig_addr:08x}, {orig_size} B) ---")
        compiled_bytes, relocs = compile_function(name)
        comp_addr = 0x00490000
        relocated_code = relocate_compiled(compiled_bytes, relocs, comp_addr)

        # Build test cases based on function
        if name == "soundEffect_func_0010368c":
            cases = [
                ("null_table_entry", 0),
                ("existing_table_entry", 0x12345678),
            ]
            for label, table_val in cases:
                # Run original
                emu_orig = Emulator()
                emu_orig.table_entry_val = table_val
                # Mock tail call target 0x00109524 with bx lr so it doesn't run full 0x00109524
                emu_orig.uc.mem_write(0x00109524, struct.pack('<I', 0xe12fff1e))
                # Set up SP and LR
                emu_orig.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
                ret_addr = 0x004FFF00
                emu_orig.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
                emu_orig.uc.reg_write(UC_ARM_REG_LR, ret_addr)

                # Clear config A and effect buffer
                emu_orig.uc.mem_write(ADDR_CFG_A, b'\x00' * 16)
                emu_orig.uc.mem_write(ADDR_EFFECT_BUFS, b'\x00' * 8)

                # Run
                emu_orig.uc.emu_start(orig_addr, ret_addr, timeout=5000000)
                orig_cfg = emu_orig.uc.mem_read(ADDR_CFG_A, 16)
                orig_buf = emu_orig.uc.mem_read(ADDR_EFFECT_BUFS, 8)
                orig_calls = list(emu_orig.call_log)

                # Run compiled
                emu_comp = Emulator()
                emu_comp.table_entry_val = table_val
                emu_comp.uc.mem_write(0x00109524, struct.pack('<I', 0xe12fff1e))
                emu_comp.uc.mem_write(comp_addr, bytes(relocated_code))
                emu_comp.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
                emu_comp.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
                emu_comp.uc.reg_write(UC_ARM_REG_LR, ret_addr)
                emu_comp.uc.mem_write(ADDR_CFG_A, b'\x00' * 16)
                emu_comp.uc.mem_write(ADDR_EFFECT_BUFS, b'\x00' * 8)

                emu_comp.uc.emu_start(comp_addr, ret_addr, timeout=5000000)
                comp_cfg = emu_comp.uc.mem_read(ADDR_CFG_A, 16)
                comp_buf = emu_comp.uc.mem_read(ADDR_EFFECT_BUFS, 8)
                comp_calls = list(emu_comp.call_log)

                assert orig_cfg == comp_cfg, f"{label}: config A mismatch"
                assert orig_buf == comp_buf, f"{label}: buffer mismatch"
                assert orig_calls == comp_calls, f"{label}: calls mismatch\norig: {orig_calls}\ncomp: {comp_calls}"
                print(f"  [PASS] {label}")

        elif name == "soundEffect_func_00109524":
            cases = [
                ("null_table_entry", 0),
                ("existing_table_entry", 0x12345678),
            ]
            for label, table_val in cases:
                emu_orig = Emulator()
                emu_orig.table_entry_val = table_val
                emu_orig.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
                ret_addr = 0x004FFF00
                emu_orig.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
                emu_orig.uc.reg_write(UC_ARM_REG_LR, ret_addr)
                emu_orig.uc.mem_write(ADDR_CFG_B, b'\x00' * 48)
                emu_orig.uc.mem_write(ADDR_EFFECT_BUFS, b'\x00' * 8)

                emu_orig.uc.emu_start(orig_addr, ret_addr, timeout=5000000)
                orig_cfg = emu_orig.uc.mem_read(ADDR_CFG_B, 48)
                orig_buf = emu_orig.uc.mem_read(ADDR_EFFECT_BUFS, 8)
                orig_calls = list(emu_orig.call_log)

                emu_comp = Emulator()
                emu_comp.table_entry_val = table_val
                emu_comp.uc.mem_write(comp_addr, bytes(relocated_code))
                emu_comp.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
                emu_comp.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
                emu_comp.uc.reg_write(UC_ARM_REG_LR, ret_addr)
                emu_comp.uc.mem_write(ADDR_CFG_B, b'\x00' * 48)
                emu_comp.uc.mem_write(ADDR_EFFECT_BUFS, b'\x00' * 8)

                emu_comp.uc.emu_start(comp_addr, ret_addr, timeout=5000000)
                comp_cfg = emu_comp.uc.mem_read(ADDR_CFG_B, 48)
                comp_buf = emu_comp.uc.mem_read(ADDR_EFFECT_BUFS, 8)
                comp_calls = list(emu_comp.call_log)

                assert orig_cfg == comp_cfg, f"{label}: config B mismatch"
                assert orig_buf == comp_buf, f"{label}: buffer mismatch"
                assert orig_calls == comp_calls, f"{label}: calls mismatch\norig: {orig_calls}\ncomp: {comp_calls}"
                print(f"  [PASS] {label}")

        elif name == "AsdSoundSystem_func_0010b974":
            cases = [
                ("inactive_state", 0),
                ("active_state", 1),
            ]
            for label, state_val in cases:
                emu_orig = Emulator()
                emu_orig.has_state_val = state_val
                emu_orig.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
                ret_addr = 0x004FFF00
                emu_orig.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
                emu_orig.uc.reg_write(UC_ARM_REG_LR, ret_addr)

                # Set up system.field_478 and g_AsdSoundSystemHandle
                emu_orig.uc.mem_write(ADDR_SOUND_SYS + 0x478, struct.pack('<I', 0x11223344))
                emu_orig.uc.mem_write(ADDR_SYS_HANDLE, struct.pack('<I', 0x55667788))

                emu_orig.uc.emu_start(orig_addr, ret_addr, timeout=5000000)
                orig_ret = emu_orig.uc.reg_read(UC_ARM_REG_R0)
                orig_field478 = emu_orig.uc.mem_read(ADDR_SOUND_SYS + 0x478, 4)
                orig_calls = list(emu_orig.call_log)

                emu_comp = Emulator()
                emu_comp.has_state_val = state_val
                emu_comp.uc.mem_write(comp_addr, bytes(relocated_code))
                emu_comp.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
                emu_comp.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
                emu_comp.uc.reg_write(UC_ARM_REG_LR, ret_addr)

                emu_comp.uc.mem_write(ADDR_SOUND_SYS + 0x478, struct.pack('<I', 0x11223344))
                emu_comp.uc.mem_write(ADDR_SYS_HANDLE, struct.pack('<I', 0x55667788))

                emu_comp.uc.emu_start(comp_addr, ret_addr, timeout=5000000)
                comp_ret = emu_comp.uc.reg_read(UC_ARM_REG_R0)
                comp_field478 = emu_comp.uc.mem_read(ADDR_SOUND_SYS + 0x478, 4)
                comp_calls = list(emu_comp.call_log)

                assert orig_ret == comp_ret, f"{label}: return value mismatch ({orig_ret:#x} vs {comp_ret:#x})"
                assert orig_field478 == comp_field478, f"{label}: field_478 mismatch"
                assert orig_calls == comp_calls, f"{label}: calls mismatch\norig: {orig_calls}\ncomp: {comp_calls}"
                print(f"  [PASS] {label} (ret={orig_ret:#x})")

        elif name == "soundTest_func_001ea808":
            emu_orig = Emulator()
            emu_orig.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            ret_addr = 0x004FFF00
            emu_orig.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
            emu_orig.uc.reg_write(UC_ARM_REG_LR, ret_addr)
            emu_orig.uc.mem_write(ADDR_SOUND_TEST_OBJ, struct.pack('<I', 0))

            emu_orig.uc.emu_start(orig_addr, ret_addr, timeout=5000000)
            orig_obj_ptr = struct.unpack('<I', emu_orig.uc.mem_read(ADDR_SOUND_TEST_OBJ, 4))[0]
            orig_obj_mem = emu_orig.uc.mem_read(orig_obj_ptr, 0x14)
            orig_calls = list(emu_orig.call_log)

            emu_comp = Emulator()
            emu_comp.uc.mem_write(comp_addr, bytes(relocated_code))
            emu_comp.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            emu_comp.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
            emu_comp.uc.reg_write(UC_ARM_REG_LR, ret_addr)
            emu_comp.uc.mem_write(ADDR_SOUND_TEST_OBJ, struct.pack('<I', 0))

            emu_comp.uc.emu_start(comp_addr, ret_addr, timeout=5000000)
            comp_obj_ptr = struct.unpack('<I', emu_comp.uc.mem_read(ADDR_SOUND_TEST_OBJ, 4))[0]
            comp_obj_mem = emu_comp.uc.mem_read(comp_obj_ptr, 0x14)
            comp_calls = list(emu_comp.call_log)

            assert orig_obj_mem == comp_obj_mem, f"soundTest object memory mismatch"
            assert orig_calls == comp_calls, f"calls mismatch\norig: {orig_calls}\ncomp: {comp_calls}"
            print(f"  [PASS] soundTest_func_001ea808 (obj_ptr={orig_obj_ptr:#x})")

        elif name == "AsdSoundSystem_func_002c1df4":
            cases = [
                ("out_of_bounds", 4, 0x800, [0, 0, 0, 0]),
                ("already_open", 1, 0x800, [0, 1, 0, 0]),
                ("open_slot_0_none_active", 0, 0x800, [0, 0, 0, 0]),
                ("open_slot_1_slot_2_active", 1, 0x800, [0, 0, 1, 0]),
            ]
            for label, idx, sz, flags in cases:
                emu_orig = Emulator()
                emu_orig.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
                ret_addr = 0x004FFF00
                emu_orig.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
                emu_orig.uc.reg_write(UC_ARM_REG_LR, ret_addr)

                emu_orig.uc.reg_write(UC_ARM_REG_R0, idx)
                emu_orig.uc.reg_write(UC_ARM_REG_R1, sz)

                # Clear streams and set initial field_10 flags
                emu_orig.uc.mem_write(ADDR_SOUND_SYS + 0x4bc, b'\x00' * (0x50 * 4))
                for i, f in enumerate(flags):
                    emu_orig.uc.mem_write(ADDR_SOUND_SYS + 0x4bc + i * 0x50 + 0x10, struct.pack('<I', f))
                emu_orig.uc.mem_write(ADDR_SOUND_SYS + 0x1204, struct.pack('<I', 0))

                emu_orig.uc.emu_start(orig_addr, ret_addr, timeout=5000000)
                orig_ret = emu_orig.uc.reg_read(UC_ARM_REG_R0)
                orig_streams = emu_orig.uc.mem_read(ADDR_SOUND_SYS + 0x4bc, 0x50 * 4)
                orig_active = struct.unpack('<I', emu_orig.uc.mem_read(ADDR_SOUND_SYS + 0x1204, 4))[0]
                orig_calls = list(emu_orig.call_log)

                emu_comp = Emulator()
                emu_comp.uc.mem_write(comp_addr, bytes(relocated_code))
                emu_comp.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
                emu_comp.uc.mem_write(ret_addr, struct.pack('<I', 0xe12fff1e))
                emu_comp.uc.reg_write(UC_ARM_REG_LR, ret_addr)

                emu_comp.uc.reg_write(UC_ARM_REG_R0, idx)
                emu_comp.uc.reg_write(UC_ARM_REG_R1, sz)

                emu_comp.uc.mem_write(ADDR_SOUND_SYS + 0x4bc, b'\x00' * (0x50 * 4))
                for i, f in enumerate(flags):
                    emu_comp.uc.mem_write(ADDR_SOUND_SYS + 0x4bc + i * 0x50 + 0x10, struct.pack('<I', f))
                emu_comp.uc.mem_write(ADDR_SOUND_SYS + 0x1204, struct.pack('<I', 0))

                emu_comp.uc.emu_start(comp_addr, ret_addr, timeout=5000000)
                comp_ret = emu_comp.uc.reg_read(UC_ARM_REG_R0)
                comp_streams = emu_comp.uc.mem_read(ADDR_SOUND_SYS + 0x4bc, 0x50 * 4)
                comp_active = struct.unpack('<I', emu_comp.uc.mem_read(ADDR_SOUND_SYS + 0x1204, 4))[0]
                comp_calls = list(emu_comp.call_log)

                assert orig_ret == comp_ret, f"{label}: return value mismatch ({orig_ret} vs {comp_ret})"
                assert orig_streams == comp_streams, f"{label}: streams memory mismatch"
                assert orig_active == comp_active, f"{label}: active stream mismatch ({orig_active:#x} vs {comp_active:#x})"
                assert orig_calls == comp_calls, f"{label}: calls mismatch\norig: {orig_calls}\ncomp: {comp_calls}"
                print(f"  [PASS] {label} (ret={orig_ret}, active={orig_active:#x})")

    print("\nALL 5 SOUND BATCH 1 CANDIDATES PASSED 100%!")

if __name__ == "__main__":
    test_sound_batch1()
