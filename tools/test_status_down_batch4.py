import sys
import struct
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unicorn
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = Path("extracted/exefs/code.bin")
ORIG_DATA = CODE_PATH.read_bytes()

test_cpp = """
#include "types.h"
#include "ui/status_down.h"

using namespace smt4::ui;

extern "C" {
void camp_func_002bdac0(void* obj, u32 idx, u32 val);
void camp_func_002b9008(s32 idx);
void camp_func_002c4450(void* obj, u32 a1, s32 a2);
void script_vm_func_002a7b50(void* ptr);
void battle_func_002c45b8(void* task, u32 val);
void engine_func_002c4360(void* obj);
s32 camp_func_0029f0f4(void* cursor);
void camp_func_0029fae8(void* cursor, s32 count, s32 r2, s32 r3, s32 sp0, s32 sp4);
void camp_func_0029edfc(void* cursor, s32 row);
}

namespace smt4::ui {
void StatusDown_OpenDefaultView() {
    auto* work = g_StatusDownWork;
    camp_func_002bdac0(&work->panel_sprites[0], 1, 0);
    work = g_StatusDownWork;
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 1;
    work->prev_state = prev;
    work->sub_state = 3;
}

void StatusDown_Close() {
    auto* work = g_StatusDownWork;
    if (work->state == 0) {
        return;
    }
    camp_func_002bdac0(&work->panel_sprites[0], 2, 0);
    work = g_StatusDownWork;
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 2;
    work->prev_state = prev;
    work->sub_state = 0;
    work->active_mode = 0;
    const u8 tr_count = static_cast<u8>(work->registered_touch_count);
    for (s32 i = 0; i < tr_count; ++i) {
        camp_func_002b9008(work->registered_touch_count);
    }
    work->registered_touch_count = 0;
    camp_func_002c4450(&work->slot_touch_handles[0], 0x29, -1);
}

void StatusDown_Destroy() {
    auto* work = g_StatusDownWork;
    const u8 tr_count = static_cast<u8>(work->registered_touch_count);
    for (s32 i = 0; i < tr_count; ++i) {
        camp_func_002b9008(work->registered_touch_count);
    }
    work->registered_touch_count = 0;
    camp_func_002c4450(&work->slot_touch_handles[0], 0x29, -1);
    script_vm_func_002a7b50(work->text_handle);
    battle_func_002c45b8(work->calc_task, 0);
    engine_func_002c4360(work);
    g_StatusDownWork = nullptr;
}

void StatusDown_SelectLastPartySlotAndEnterState11(u32 a0, u32 a1) {
    auto* work = g_StatusDownWork;
    work->selected_result = static_cast<s32>(a0);
    work->callback_arg1 = a1;
    s32 count = camp_func_0029f0f4(&work->list_cursor_main);
    camp_func_0029fae8(&work->list_cursor_main, count + 1, 9, 1, 0, 1);
    s32 new_count = camp_func_0029f0f4(&work->list_cursor_main);
    camp_func_0029edfc(&work->list_cursor_main, new_count - 1);
    work->needs_refresh = 1;
    work = g_StatusDownWork;
    const u8 tr_count = static_cast<u8>(work->registered_touch_count);
    for (s32 i = 0; i < tr_count; ++i) {
        camp_func_002b9008(work->registered_touch_count);
    }
    work->registered_touch_count = 0;
    camp_func_002c4450(&work->slot_touch_handles[0], 0x29, -1);
    work = g_StatusDownWork;
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 0x0B;
    work->prev_state = prev;
    StatusDown_SetupTouchRegions();
}

}
"""

build_dir = Path("build/test_status_down_batch4")
build_dir.mkdir(parents=True, exist_ok=True)
src_file = build_dir / "test.cpp"
obj_file = build_dir / "test.o"
src_file.write_text(test_cpp, encoding="utf-8")

res = compile_tu_armv6k(src_file, obj_file, repo_root=Path('.'))
assert res.returncode == 0, f"Compilation failed: {res.stderr}"
dec_funcs = extract_elf_functions_detailed(obj_file)
print("Compiled 4 StatusDown functions successfully.")

STUB_BASE = 0x02000000
GLOBAL_PTR_ADDR = 0x0044E190
WORK_STRUCT_ADDR = 0x02100000

STUB_MAP = {
    'camp_func_002bdac0': STUB_BASE + 0x00,
    'camp_func_002b9008': STUB_BASE + 0x10,
    'camp_func_002c4450': STUB_BASE + 0x20,
    'script_vm_func_002a7b50': STUB_BASE + 0x30,
    'battle_func_002c45b8': STUB_BASE + 0x40,
    'engine_func_002c4360': STUB_BASE + 0x50,
    'camp_func_0029f0f4': STUB_BASE + 0x60,
    'camp_func_0029fae8': STUB_BASE + 0x70,
    'camp_func_0029edfc': STUB_BASE + 0x80,
    '_ZN4smt42ui28StatusDown_SetupTouchRegionsEv': STUB_BASE + 0x90,
    '_ZN4smt42ui16g_StatusDownWorkE': GLOBAL_PTR_ADDR,
}

ORIG_ADDR_MAP = {
    0x002bdac0: 'camp_func_002bdac0',
    0x002b9008: 'camp_func_002b9008',
    0x002c4450: 'camp_func_002c4450',
    0x002a7b50: 'script_vm_func_002a7b50',
    0x002c45b8: 'battle_func_002c45b8',
    0x002c4360: 'engine_func_002c4360',
    0x0029f0f4: 'camp_func_0029f0f4',
    0x0029fae8: 'camp_func_0029fae8',
    0x0029edfc: 'camp_func_0029edfc',
    0x0026b0d0: '_ZN4smt42ui28StatusDown_SetupTouchRegionsEv',
}

ARITY = {
    'camp_func_002bdac0': 3,
    'camp_func_002b9008': 1,
    'camp_func_002c4450': 3,
    'script_vm_func_002a7b50': 1,
    'battle_func_002c45b8': 2,
    'engine_func_002c4360': 1,
    'camp_func_0029f0f4': 1,
    'camp_func_0029fae8': 6,
    'camp_func_0029edfc': 2,
    '_ZN4smt42ui28StatusDown_SetupTouchRegionsEv': 0,
}

def apply_relocs(code_bytes, relocs, target_addr):
    mutable = bytearray(code_bytes)
    for rel in relocs:
        offset = rel.offset
        name = rel.symbol_name
        rel_type = rel.relocation_type
        if name in STUB_MAP:
            sym_val = STUB_MAP[name]
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

class CallTracker:
    def __init__(self):
        self.calls = []
        
    def hook_call(self, uc, address, size, user_data):
        regs = [
            hex(uc.reg_read(UC_ARM_REG_R0)),
            hex(uc.reg_read(UC_ARM_REG_R1)),
            hex(uc.reg_read(UC_ARM_REG_R2)),
            hex(uc.reg_read(UC_ARM_REG_R3)),
        ]
        arity = ARITY.get(user_data, 4)
        self.calls.append((user_data, tuple(regs[:arity])))
        
        # Stubs return values:
        if user_data == 'camp_func_0029f0f4':
            uc.reg_write(UC_ARM_REG_R0, 3) # mock row count = 3
            
        lr = uc.reg_read(UC_ARM_REG_LR)
        if lr & 1:
            uc.reg_write(UC_ARM_REG_CPSR, uc.reg_read(UC_ARM_REG_CPSR) | 0x20)
            uc.reg_write(UC_ARM_REG_PC, lr & ~1)
        else:
            uc.reg_write(UC_ARM_REG_CPSR, uc.reg_read(UC_ARM_REG_CPSR) & ~0x20)
            uc.reg_write(UC_ARM_REG_PC, lr)

TARGETS = [
    (0x001ddab4, '_ZN4smt42ui26StatusDown_OpenDefaultViewEv', {}),
    (0x0029bfec, '_ZN4smt42ui16StatusDown_CloseEv', {}),
    (0x002f6550, '_ZN4smt42ui18StatusDown_DestroyEv', {}),
    (0x002f6620, '_ZN4smt42ui45StatusDown_SelectLastPartySlotAndEnterState11Ejj', {'r0': 0x1234, 'r1': 0x5678}),
]

for orig_addr, func_name, reg_inits in TARGETS:
    print(f"\nTesting {func_name} (0x{orig_addr:x})...")
    
    # 1. Orig
    uc_orig = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc_orig.mem_map(0x00100000, 0x00500000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_orig.mem_map(0x0FFFF000, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(WORK_STRUCT_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_write(0x00100000, ORIG_DATA)
    
    # Init work struct with touch_region_count = 2, state = 5, etc.
    work_bytes = bytearray(0x4000)
    struct.pack_into('<I', work_bytes, 0x400, 5) # state = 5
    struct.pack_into('<I', work_bytes, 0x404, 2) # prev_state = 2
    work_bytes[0x480] = 2 # registered_touch_count = 2
    struct.pack_into('<I', work_bytes, 0x22a0, 0x02105000) # text_handle
    struct.pack_into('<I', work_bytes, 0x0000, 0x02106000) # calc_task
    uc_orig.mem_write(WORK_STRUCT_ADDR, bytes(work_bytes))
    uc_orig.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', WORK_STRUCT_ADDR))
    
    tracker_orig = CallTracker()
    for addr, name in ORIG_ADDR_MAP.items():
        uc_orig.mem_write(addr, b"\x1e\xff\x2f\xe1")
        uc_orig.hook_add(unicorn.UC_HOOK_CODE, tracker_orig.hook_call, user_data=name, begin=addr, end=addr)
        
    writes_orig = {}
    def hook_mem_orig(uc, access, address, size, value, user_data):
        writes_orig[address] = (size, value)
    uc_orig.hook_add(unicorn.UC_HOOK_MEM_WRITE, hook_mem_orig)
    def hook_unmapped_orig(uc, access, address, size, value, user_data):
        pc = uc.reg_read(UC_ARM_REG_PC)
        lr = uc.reg_read(UC_ARM_REG_LR)
        print(f"[{func_name}] Orig unmapped at PC=0x{pc:x}, LR=0x{lr:x}, addr=0x{address:x}")
        return False
    uc_orig.hook_add(unicorn.UC_HOOK_MEM_READ_UNMAPPED | unicorn.UC_HOOK_MEM_WRITE_UNMAPPED, hook_unmapped_orig)
    
    uc_orig.reg_write(UC_ARM_REG_SP, 0x0FFFF000 + 0x8000)
    uc_orig.reg_write(UC_ARM_REG_LR, 0x0)
    for r_name, r_val in reg_inits.items():
        reg_id = getattr(unicorn.arm_const, f"UC_ARM_REG_{r_name.upper()}")
        uc_orig.reg_write(reg_id, r_val)
    uc_orig.emu_start(orig_addr, 0x0, timeout=100000)
    
    # 2. Dec
    dec_code = dec_funcs[func_name][0]
    relocs = dec_funcs[func_name][1]
    target_addr = 0x00380000
    patched_code = apply_relocs(dec_code, relocs, target_addr)
    
    uc_dec = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc_dec.mem_map(0x00100000, 0x00500000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_map(0x0FFFF000, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(WORK_STRUCT_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(STUB_BASE, 0x10000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_write(0x00100000, ORIG_DATA)
    uc_dec.mem_write(target_addr, patched_code)
    
    uc_dec.mem_write(WORK_STRUCT_ADDR, bytes(work_bytes))
    uc_dec.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', WORK_STRUCT_ADDR))
    
    tracker_dec = CallTracker()
    for name, addr in STUB_MAP.items():
        if name != '_ZN4smt42ui16g_StatusDownWorkE':
            uc_dec.mem_write(addr, b"\x1e\xff\x2f\xe1")
            uc_dec.hook_add(unicorn.UC_HOOK_CODE, tracker_dec.hook_call, user_data=name, begin=addr, end=addr)
        
    writes_dec = {}
    def hook_mem_dec(uc, access, address, size, value, user_data):
        writes_dec[address] = (size, value)
    uc_dec.hook_add(unicorn.UC_HOOK_MEM_WRITE, hook_mem_dec)
    
    uc_dec.reg_write(UC_ARM_REG_SP, 0x0FFFF000 + 0x8000)
    uc_dec.reg_write(UC_ARM_REG_LR, 0x0)
    for r_name, r_val in reg_inits.items():
        reg_id = getattr(unicorn.arm_const, f"UC_ARM_REG_{r_name.upper()}")
        uc_dec.reg_write(reg_id, r_val)
    uc_dec.emu_start(target_addr, 0x0, timeout=100000)
    
    assert tracker_orig.calls == tracker_dec.calls, f"Calls mismatch for {func_name}:\n  Orig: {tracker_orig.calls}\n  Dec:  {tracker_dec.calls}"
    print(f"  Calls match: {tracker_dec.calls}")
    
    # Check memory state at work struct
    mem_orig = uc_orig.mem_read(WORK_STRUCT_ADDR, 0x600)
    mem_dec = uc_dec.mem_read(WORK_STRUCT_ADDR, 0x600)
    assert mem_orig == mem_dec, f"Work struct memory mismatch for {func_name}!"
    print(f"  Work struct memory matches 100%!")

print("\nALL 4 STATUSDOWN FUNCTIONS MATCH 100%!")
