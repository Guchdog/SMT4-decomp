#!/usr/bin/env python3
"""
Unicorn differential verification harness for 27 StatusDown state, field,
and cursor helper routines in src/ui/status_down.cpp (1,180 total bytes).
"""

import re
import struct
import sys
from pathlib import Path
import unicorn
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
    UC_ARM_REG_C1_C0_2, UC_ARM_REG_FPEXC,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / "extracted" / "exefs" / "code.bin"
ORIG_DATA = CODE_PATH.read_bytes()
SRC_PATH = ROOT / "src" / "ui" / "status_down.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00500000
STACK_BASE = 0x0FFFF000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x100

WORK_ADDR = 0x00470000
GLOBAL_PTR_ADDR = 0x0044E190

STUB_BASE = 0x004A0000
STUB_MAP = {
    'StatusDown_SetupTouchRegions': STUB_BASE + 0x00,
    '_ZN4smt42ui27StatusDown_SetupTouchRegionsEv': STUB_BASE + 0x00,
    'AsdMem_Copy': STUB_BASE + 0x10,
    'camp_func_0029f0f4': STUB_BASE + 0x20,
    'camp_func_0029f248': STUB_BASE + 0x30,
    '_ZN4smt42ui16g_StatusDownWorkE': GLOBAL_PTR_ADDR,
}

ORIG_ADDR_MAP = {
    0x0026b0d0: 'StatusDown_SetupTouchRegions',
    0x002c5ff4: 'AsdMem_Copy',
    0x0029f0f4: 'camp_func_0029f0f4',
    0x0029f248: 'camp_func_0029f248',
}

TARGET_FUNCS = [
    (0x00215a44, 28, 'StatusDown_SetActiveSoundId', 'void', [0x1234]),
    (0x00223b88, 40, 'StatusDown_IsState20', 'bool', []),
    (0x0026d8c0, 28, 'StatusDown_SetVisibility', 'void', [0x42]),
    (0x0028cd5c, 28, 'StatusDown_GetField2384', 'u32', []),
    (0x0028cd78, 36, 'StatusDown_IsInactiveOrState0', 'bool', []),
    (0x00293d2c, 36, 'StatusDown_IsNotTransitioning', 'bool', []),
    (0x00293e30, 28, 'StatusDown_GetStatusMode', 's8', []),
    (0x0029c70c, 32, 'StatusDown_IsNotState1', 'bool', []),
    (0x0029c72c, 32, 'StatusDown_IsNotState2', 'bool', []),
    (0x002d9618, 36, 'StatusDown_EnterState3_Alt', 'void', []),
    (0x002efe0c, 32, 'StatusDown_IsNotState4', 'bool', []),
    (0x002efe2c, 28, 'StatusDown_GetField2388', 's8', []),
    (0x002f6524, 44, 'StatusDown_IsState7', 'bool', []),
    (0x002f66e8, 36, 'StatusDown_EnterState3', 'void', []),
    (0x0030aa98, 40, 'StatusDown_EnterState6_Simple', 'void', []),
    (0x0030aac0, 32, 'StatusDown_IsState15', 'bool', []),
    (0x0030aae0, 32, 'StatusDown_IsState10', 'bool', []),
    (0x0030ab00, 52, 'StatusDown_EnterState14', 'void', [0]),
    (0x002efea4, 36, 'StatusDown_EnterState4', 'void', []),
    (0x0030ab34, 60, 'StatusDown_EnterState6', 'void', []),
    (0x00317f80, 36, 'StatusDown_RequestClose', 'void', []),
    (0x002efe48, 68, 'StatusDown_SetSubIdsB', 'void', [0x0FFFF800, 4]),
    (0x0026abe0, 84, 'StatusDown_SetSubIdsA', 'void', [0x0FFFF800, 4]),
    (0x0026b01c, 176, 'StatusDown_PopFirstSubIdA', 'void', []),
    (0x002efde0, 44, 'StatusDown_GetPartyMaxIndex', 's32', []),
    (0x002f65d4, 76, 'StatusDown_IsCursorAtLastPartySlot', 'bool', []),
    (0x0032303c, 40, 'StatusDown_GetSelectedPartyIndex', 's32', []),
]

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
        if 'camp_func_0029f0f4' in stub_name:
            uc.reg_write(UC_ARM_REG_R0, 8) # e.g. 8 items
        elif 'camp_func_0029f248' in stub_name:
            uc.reg_write(UC_ARM_REG_R0, 7) # selected index 7
        elif 'AsdMem_Copy' in stub_name:
            # Emulate memcpy(r0, r1, r2)
            src_bytes = uc.mem_read(r1, r2)
            uc.mem_write(r0, bytes(src_bytes))
            uc.reg_write(UC_ARM_REG_R0, r0)
        else:
            uc.reg_write(UC_ARM_REG_R0, 0)
        lr = uc.reg_read(UC_ARM_REG_LR)
        uc.reg_write(UC_ARM_REG_PC, lr)

def setup_orig_stubs(uc, tracker):
    for addr, name in ORIG_ADDR_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1") # bx lr
        uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data=name, begin=addr, end=addr)

def setup_stubs(uc, tracker):
    seen = set()
    for name, addr in STUB_MAP.items():
        if addr != GLOBAL_PTR_ADDR and addr not in seen:
            seen.add(addr)
            uc.mem_write(addr, b"\x1e\xff\x2f\xe1") # bx lr
            uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data=name, begin=addr, end=addr)
    setup_orig_stubs(uc, tracker)

def apply_relocations(code_bytes, relocs, target_addr, rodata_addr):
    mutable = bytearray(code_bytes)
    syms = dict(STUB_MAP)
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
            # Try demangled / stripped
            matched = False
            for k in syms:
                if k in name or name in k:
                    sym_val = syms[k]
                    matched = True
                    break
            if not matched:
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

def populate_mock_work(uc):
    # Set global pointer *0x0044E190 = WORK_ADDR
    uc.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', WORK_ADDR))
    # Zero out 0x2400 bytes of work
    uc.mem_write(WORK_ADDR, b'\x00' * 0x2400)
    # Set state = 20 (0x14), prev_state = 1
    uc.mem_write(WORK_ADDR + 0x400, struct.pack('<I', 0x14))
    uc.mem_write(WORK_ADDR + 0x404, struct.pack('<I', 1))
    uc.mem_write(WORK_ADDR + 0x40C, struct.pack('<I', 100)) # state timer
    uc.mem_write(WORK_ADDR + 0x481, struct.pack('b', -5))   # status_mode
    uc.mem_write(WORK_ADDR + 0x47E, struct.pack('<h', 0x1122)) # active_sound_id
    uc.mem_write(WORK_ADDR + 0x2384, struct.pack('<I', 0xDEADBEEF))
    uc.mem_write(WORK_ADDR + 0x2388, struct.pack('b', -12))
    uc.mem_write(WORK_ADDR + 0x2391, b'\x00')
    uc.mem_write(WORK_ADDR + 0x2392, b'\x05')
    # Sub IDs: a has [10, 20, 30, 0, 0, ...], b has [10, 50, 0, ...]
    sub_a = [10, 20, 30, 0, 0, 0, 0, 0]
    sub_b = [10, 50, 0, 0, 0, 0, 0, 0]
    uc.mem_write(WORK_ADDR + 0x4A2, struct.pack('<8H', *sub_a))
    uc.mem_write(WORK_ADDR + 0x4B2, struct.pack('<8H', *sub_b))
    # Test array at 0x0FFFF800
    test_ids = [101, 102, 103, 104, 0, 0, 0, 0]
    uc.mem_write(0x0FFFF800, struct.pack('<8H', *test_ids))

ARITY_MAP = {
    'StatusDown_SetupTouchRegions': 0,
    '_ZN4smt42ui27StatusDown_SetupTouchRegionsEv': 0,
    'AsdMem_Copy': 3,
    'camp_func_0029f0f4': 1,
    'camp_func_0029f248': 1,
}

def main():
    print(f"Loaded {len(TARGET_FUNCS)} target functions to verify...")

    print("Compiling src/ui/status_down.cpp...")
    build_dir = ROOT / "build" / "status_down_helpers_test"
    build_dir.mkdir(parents=True, exist_ok=True)
    obj = build_dir / "status_down.o"
    res = compile_tu_armv6k(SRC_PATH, obj, repo_root=ROOT)
    if res.returncode != 0:
        print("COMPILATION FAILED:")
        print(res.stderr)
        sys.exit(1)
    functions = extract_elf_functions_detailed(obj)

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A8000

    passed = 0
    total_bytes = 0

    for addr, sz, name, ret_type, args in TARGET_FUNCS:
        total_bytes += sz
        dec_code = None
        dec_relocs = None
        for mangled, (b, relocs) in functions.items():
            if f"{len(name)}{name}" in mangled or mangled.endswith(name) or name == mangled:
                dec_code = b
                dec_relocs = relocs
                break
        if dec_code is None:
            raise KeyError(f"Function {name} not found in compiled object")

        patched_code = apply_relocations(dec_code, dec_relocs, TARGET_DECOMP, RODATA_ADDR)

        # Test cases: normal work, and null work (for functions that guard against null)
        for test_case in ("normal", "null"):
            # Skip null case for functions that don't guard against null
            if test_case == "null" and name in (
                'StatusDown_IsNotTransitioning', 'StatusDown_IsNotState1',
                'StatusDown_IsNotState2', 'StatusDown_IsNotState4',
                'StatusDown_IsState15', 'StatusDown_IsState10',
                'StatusDown_EnterState3', 'StatusDown_EnterState3_Alt',
                'StatusDown_EnterState14', 'StatusDown_EnterState4',
                'StatusDown_EnterState6', 'StatusDown_EnterState6_Simple',
                'StatusDown_SetSubIdsA', 'StatusDown_SetSubIdsB',
                'StatusDown_PopFirstSubIdA'
            ):
                continue

            # Run original
            uc_orig = create_emulator()
            uc_orig.mem_write(CODE_BASE, ORIG_DATA)
            populate_mock_work(uc_orig)
            if test_case == "null":
                uc_orig.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', 0))
            tracker_orig = StubTracker(uc_orig)
            setup_orig_stubs(uc_orig, tracker_orig)
            writes_orig = []
            def hook_orig(uc, access, address, size, value, user_data):
                if not (0x0FFFF000 <= address < 0x10000000):
                    writes_orig.append((address, size, value))
            uc_orig.hook_add(unicorn.UC_HOOK_MEM_WRITE, hook_orig)
            uc_orig.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc_orig.reg_write(UC_ARM_REG_LR, 0x00000000)
            for i, arg in enumerate(args):
                uc_orig.reg_write(UC_ARM_REG_R0 + i, arg)
            uc_orig.emu_start(addr, 0x00000000, timeout=100000)
            ret_orig = uc_orig.reg_read(UC_ARM_REG_R0)

            # Run decompiled
            uc_dec = create_emulator()
            uc_dec.mem_write(CODE_BASE, ORIG_DATA)
            populate_mock_work(uc_dec)
            if test_case == "null":
                uc_dec.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', 0))
            uc_dec.mem_write(TARGET_DECOMP, patched_code)
            tracker_dec = StubTracker(uc_dec)
            setup_stubs(uc_dec, tracker_dec)
            writes_dec = []
            def hook_dec(uc, access, address, size, value, user_data):
                if not (0x0FFFF000 <= address < 0x10000000):
                    writes_dec.append((address, size, value))
            uc_dec.hook_add(unicorn.UC_HOOK_MEM_WRITE, hook_dec)
            uc_dec.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc_dec.reg_write(UC_ARM_REG_LR, 0x00000000)
            for i, arg in enumerate(args):
                uc_dec.reg_write(UC_ARM_REG_R0 + i, arg)
            uc_dec.emu_start(TARGET_DECOMP, 0x00000000, timeout=100000)
            ret_dec = uc_dec.reg_read(UC_ARM_REG_R0)

            # Mask return value based on type
            if ret_type == 'bool':
                ret_orig = 1 if ret_orig != 0 else 0
                ret_dec = 1 if ret_dec != 0 else 0
            elif ret_type == 's8':
                ret_orig = struct.unpack('b', struct.pack('B', ret_orig & 0xFF))[0]
                ret_dec = struct.unpack('b', struct.pack('B', ret_dec & 0xFF))[0]
            elif ret_type in ('u32', 's32'):
                pass

            if ret_type != 'void':
                assert ret_orig == ret_dec, f"Return mismatch for {name} ({test_case}): orig={ret_orig}, dec={ret_dec}"

            # Check calls match
            assert len(tracker_orig.calls) == len(tracker_dec.calls), f"Call count mismatch for {name}: orig={tracker_orig.calls}, dec={tracker_dec.calls}"
            for i in range(len(tracker_orig.calls)):
                c1 = tracker_orig.calls[i]
                c2 = tracker_dec.calls[i]
                assert c1['name'].split(':')[-1] in c2['name'] or c2['name'].split(':')[-1] in c1['name'], f"Call name mismatch for {name}: {c1} vs {c2}"
                arity = ARITY_MAP.get(c1['name'], 0)
                if arity >= 1:
                    assert c1['r0'] == c2['r0'], f"Call r0 mismatch for {name}: {c1} vs {c2}"
                if arity >= 2:
                    assert c1['r1'] == c2['r1'], f"Call r1 mismatch for {name}: {c1} vs {c2}"
                if arity >= 3:
                    assert c1['r2'] == c2['r2'], f"Call r2 mismatch for {name}: {c1} vs {c2}"

            # Check written memory
            all_written_addrs = set(a for a, s, v in writes_orig) | set(a for a, s, v in writes_dec)
            for written_addr in all_written_addrs:
                val_orig = uc_orig.mem_read(written_addr, 4)
                val_dec = uc_dec.mem_read(written_addr, 4)
                assert val_orig == val_dec, f"Memory mismatch at {hex(written_addr)} for {name} ({test_case}): orig={val_orig.hex()}, dec={val_dec.hex()}"

        passed += 1

    print(f"\nALL {passed} STATUS_DOWN FUNCTIONS ({total_bytes} BYTES) PASSED 100% UNICORN DIFFERENTIAL TEST!")

if __name__ == "__main__":
    main()
