#!/usr/bin/env python3
"""
Unicorn differential verification harness for AsdScene / AsdProcess functions in src/engine/asd_scene.cpp:
  - 0x002cb788 (204 B): AsdScene_func_002cb788
  - 0x00118488 (556 B): AsdProcess_func_00118488
"""

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
SRC_PATH = ROOT / "src" / "engine" / "asd_scene.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00500000
STACK_BASE = 0x0FFFF000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x100

STUB_BASE = 0x004A0000
STUB_MAP = {
    'AsdMem_AllocAlign': STUB_BASE + 0x00,
    'AsdRes_GetContext': STUB_BASE + 0x08,
    'AsdScene_CreateNodeObject': STUB_BASE + 0x10,
    'AsdRes_BuildKey': STUB_BASE + 0x18,
    'AsdMem_Alloc': STUB_BASE + 0x20,
    'AsdGxCommandList_Create': STUB_BASE + 0x28,
    'AsdProc_Attach': STUB_BASE + 0x30,
}

ORIG_ADDR_MAP = {
    0x002c54f0: 'AsdMem_AllocAlign',
    0x002c31bc: 'AsdRes_GetContext',
    0x0011d8e4: 'AsdScene_CreateNodeObject',
    0x002c2be8: 'AsdRes_BuildKey',
    0x002c4b84: 'AsdMem_Alloc',
    0x002c5d90: 'AsdGxCommandList_Create',
    0x002c4460: 'AsdProc_Attach',
}

def create_emulator():
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)
    # Enable VFP coprocessor CP10/CP11
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return uc

class StubTracker:
    def __init__(self, uc, mem_alloc_heap=0x00450000):
        self.uc = uc
        self.calls = []
        self.heap = mem_alloc_heap

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

        # Emulate allocator and object creator
        if stub_name in ('AsdMem_AllocAlign', 'AsdMem_Alloc'):
            ret = self.heap
            self.heap += 0x200
            uc.mem_write(ret, b"\x00" * 0x200)
            uc.reg_write(UC_ARM_REG_R0, ret)
        elif stub_name == 'AsdRes_GetContext':
            uc.reg_write(UC_ARM_REG_R0, 0x00470000)
        elif stub_name == 'AsdScene_CreateNodeObject':
            obj = self.heap
            self.heap += 0x100
            uc.mem_write(obj, b"\x00" * 0x100)
            data_ptr = self.heap
            self.heap += 0x200
            uc.mem_write(data_ptr, b"\x00" * 0x200)
            uc.mem_write(obj + 8, struct.pack('<I', data_ptr))
            uc.reg_write(UC_ARM_REG_R0, obj)
        elif stub_name == 'AsdRes_BuildKey':
            uc.reg_write(UC_ARM_REG_R0, 0x12345678)
        elif stub_name == 'AsdGxCommandList_Create':
            uc.reg_write(UC_ARM_REG_R0, 0x00480000)
        else:
            uc.reg_write(UC_ARM_REG_R0, 0)

        lr = uc.reg_read(UC_ARM_REG_LR)
        uc.reg_write(UC_ARM_REG_PC, lr)

def setup_orig_stubs(uc, tracker):
    for addr, name in ORIG_ADDR_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1")
        uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data=name, begin=addr, end=addr)

def setup_stubs(uc, tracker):
    for name, addr in STUB_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1")
        uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data=name, begin=addr, end=addr)
    setup_orig_stubs(uc, tracker)

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

def test_002cb788(functions):
    print("\n--- Testing AsdScene_func_002cb788 (0x002cb788, 204 B) ---")
    dec_code, relocs = functions['_ZN4smt46engine22AsdScene_func_002cb788Ev']
    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A8000
    patched = apply_relocations(dec_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    # Orig
    uc_orig = create_emulator()
    uc_orig.mem_write(CODE_BASE, ORIG_DATA)
    t_orig = StubTracker(uc_orig, 0x00450000)
    setup_orig_stubs(uc_orig, t_orig)
    uc_orig.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc_orig.reg_write(UC_ARM_REG_LR, 0x00000000)
    uc_orig.emu_start(0x002cb788, 0x00000000, timeout=100000)
    ret_orig = uc_orig.reg_read(UC_ARM_REG_R0)

    # Dec
    uc_dec = create_emulator()
    uc_dec.mem_write(CODE_BASE, ORIG_DATA)
    uc_dec.mem_write(TARGET_DECOMP, patched)
    t_dec = StubTracker(uc_dec, 0x00450000)
    setup_stubs(uc_dec, t_dec)
    uc_dec.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc_dec.reg_write(UC_ARM_REG_LR, 0x00000000)
    uc_dec.emu_start(TARGET_DECOMP, 0x00000000, timeout=100000)
    ret_dec = uc_dec.reg_read(UC_ARM_REG_R0)

    assert ret_orig == ret_dec, f"Return mismatch: orig={hex(ret_orig)}, dec={hex(ret_dec)}"
    assert len(t_orig.calls) == len(t_dec.calls)
    for i in range(len(t_orig.calls)):
        assert t_orig.calls[i]['name'] == t_dec.calls[i]['name']
    
    # Check node contents (12 bytes)
    node_orig = uc_orig.mem_read(ret_orig, 12)
    node_dec = uc_dec.mem_read(ret_dec, 12)
    assert node_orig == node_dec, f"Node mismatch: orig={node_orig.hex()}, dec={node_dec.hex()}"

    # Check data contents
    data_ptr = struct.unpack('<I', node_orig[8:12])[0]
    data_orig = uc_orig.mem_read(data_ptr + 0xB8, 20)
    data_dec = uc_dec.mem_read(data_ptr + 0xB8, 20)
    assert data_orig == data_dec, f"Data mismatch: orig={data_orig.hex()}, dec={data_dec.hex()}"

    print("  [PASS] AsdScene_func_002cb788 passed 100%!")

def test_00118488(functions):
    print("\n--- Testing AsdProcess_func_00118488 (0x00118488, 556 B) ---")
    dec_code, relocs = functions['_ZN4smt46engine24AsdProcess_func_00118488EPKcjttffffj']
    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A8000

    POOL_ADDR = 0x004E3CF4
    extra_syms = {
        '_ZN4smt46engine16g_AsdProcessPoolE': POOL_ADDR,
    }
    patched = apply_relocations(dec_code, relocs, TARGET_DECOMP, RODATA_ADDR, extra_syms)

    NAME_ADDR = 0x00475000
    test_cases = [
        ("TaskAlpha", 1, 0x10, 0x20, 1.0, 2.0, 3.0, 4.0, 0),
        ("TaskBeta", 2, 0x30, 0x40, 5.0, 6.0, 7.0, 8.0, 0x12345),
        ("VeryLongProcessNameExceeding24Chars", 0, 0x50, 0x60, 0.5, 1.5, 2.5, 3.5, 0),
    ]

    for name_str, bucket, f34, f36, f38, f3c, f40, f48, parent in test_cases:
        # Prepare pool state: bucket_count = 5, buckets buffer at 0x00476000
        BUCKETS_BUF = 0x00476000

        def run_case(code, addr, is_orig):
            uc = create_emulator()
            uc.mem_write(CODE_BASE, ORIG_DATA)
            tracker = StubTracker(uc, 0x00450000)
            if is_orig:
                setup_orig_stubs(uc, tracker)
            else:
                uc.mem_write(addr, code)
                setup_stubs(uc, tracker)

            # Pool struct:
            # +0x00: buckets (ptr)
            # +0x04: bucket_count (u32)
            # +0x0c: process_count (u32)
            # +0x14: next_id (u32)
            uc.mem_write(BUCKETS_BUF, b"\x00" * (8 * 5))
            pool_data = bytearray(0x20)
            struct.pack_into('<I', pool_data, 0x00, BUCKETS_BUF)
            struct.pack_into('<I', pool_data, 0x04, 5) # 5 buckets
            struct.pack_into('<I', pool_data, 0x0c, 0)
            struct.pack_into('<I', pool_data, 0x14, 0x100) # next_id = 0x100
            uc.mem_write(POOL_ADDR, bytes(pool_data))

            # Write name string
            uc.mem_write(NAME_ADDR, name_str.encode('ascii') + b"\x00")

            # Arguments: r0=name, r1=bucket, r2=f34, r3=f36
            uc.reg_write(UC_ARM_REG_R0, NAME_ADDR)
            uc.reg_write(UC_ARM_REG_R1, bucket)
            uc.reg_write(UC_ARM_REG_R2, f34)
            uc.reg_write(UC_ARM_REG_R3, f36)

            # Stack arguments: 4 floats + parent handle
            # [sp, #0]: f38
            # [sp, #4]: f3c
            # [sp, #8]: f40
            # [sp, #12]: f48
            # [sp, #16]: parent
            sp = STACK_TOP - 0x20
            stack_args = struct.pack('<ffffI', f38, f3c, f40, f48, parent)
            uc.mem_write(sp, stack_args)

            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00000000)

            uc.emu_start(addr, 0x00000000, timeout=100000)

            ret = uc.reg_read(UC_ARM_REG_R0)
            pool_after = uc.mem_read(POOL_ADDR, 0x20)
            buckets_after = uc.mem_read(BUCKETS_BUF, 8 * 5)
            return ret, pool_after, buckets_after, tracker.calls

        ret_orig, pool_orig, buckets_orig, calls_orig = run_case(ORIG_DATA[0x118488-CODE_BASE : 0x118488-CODE_BASE+556], 0x00118488, True)
        ret_dec, pool_dec, buckets_dec, calls_dec = run_case(patched, TARGET_DECOMP, False)

        assert ret_orig == ret_dec, f"Return handle mismatch for '{name_str}': orig={hex(ret_orig)}, dec={hex(ret_dec)}"
        assert pool_orig == pool_dec, f"Pool state mismatch for '{name_str}'"
        assert buckets_orig == buckets_dec, f"Buckets buffer mismatch for '{name_str}'"
        assert len(calls_orig) == len(calls_dec), f"Calls count mismatch: orig={calls_orig}, dec={calls_dec}"
        for i in range(len(calls_orig)):
            assert calls_orig[i]['name'] == calls_dec[i]['name']

    print("  [PASS] AsdProcess_func_00118488 passed 100% across all cases!")

def main():
    print("Compiling src/engine/asd_scene.cpp...")
    build_dir = ROOT / "build" / "asd_scene_test"
    build_dir.mkdir(parents=True, exist_ok=True)
    obj = build_dir / "asd_scene.o"
    res = compile_tu_armv6k(SRC_PATH, obj, repo_root=ROOT)
    if res.returncode != 0:
        print("COMPILATION FAILED:")
        print(res.stderr)
        sys.exit(1)
    functions = extract_elf_functions_detailed(obj)

    test_002cb788(functions)
    test_00118488(functions)

    print("\nALL ASD_SCENE FUNCTIONS (760 BYTES) PASSED 100%!")

if __name__ == "__main__":
    main()
