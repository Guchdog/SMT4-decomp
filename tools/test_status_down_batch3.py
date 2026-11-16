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
#include "ui/status.h"
#include <cstring>

using namespace smt4::ui;

extern "C" {
void Sound_PlaySE(s32 se_id);
void UiListCursor_Setup(void* cursor, s32 total_items, s32 visible_rows, s32 cols, s32 wrap_row, s32 repeat);
void AsdMem_Copy(void* dst, const void* src, u32 size);
s32 Camp_GetTransitionDir();
void UiAnimSprite_SetAnim(void* sprite, s32 anim_idx, s32 mode);
void UiTouch_UnregisterLastRegion();
void AsdMem_FillBytes(void* dst, u32 size, u32 value);
void Camp_SetFadeColor(u32 screen, u32 rgba);
s32 Status_GetMainMenuId();
}

namespace smt4::ui {

void StatusDown_SetPartyPrompt(const StatusDownPartyPrompt* prompt) {
    auto* work = g_StatusDownWork;
    if (work->active_sound_id >= 0 && work->active_mode == 1) {
        s32 menu_id = Status_GetMainMenuId();
        if (menu_id == 0xD || menu_id == 6) {
            Sound_PlaySE(0x2F);
        } else {
            Sound_PlaySE(0x1F);
        }
    }
    work->active_sound_id = -1;
    work->prompt_field0 = prompt->field0;
    work->prompt_field1 = prompt->field1;
    work->prompt_field2 = prompt->field2;
    work->prompt_field3 = prompt->field3;
    UiListCursor_Setup(&work->list_cursor_prompt, 7, 7, 1, 0, 1);
    work->needs_refresh = 1;
}

void StatusDown_SetPartySlots(const u16* party_slots, s32 count) {
    auto* work = g_StatusDownWork;
    for (s32 i = 0; i < 4; ++i) {
        reinterpret_cast<u32*>(work->new_party_flags)[i] = 0;
        reinterpret_cast<u32*>(work->party_ids)[i] = 0;
    }
    AsdMem_Copy(work->party_ids, party_slots, count * sizeof(u16));
    s32 total_items = 0;
    while (total_items < count && work->party_ids[total_items] != 0) {
        total_items++;
    }
    UiListCursor_Setup(&work->list_cursor_main, total_items, 8, 1, 0, 1);
    work->needs_refresh = 1;
    work->flag_548 = 0;
}

void StatusDown_SetDisplayMode(s32 mode) {
    auto* work = g_StatusDownWork;
    if (work->active_mode == mode) {
        return;
    }
    work->prev_active_mode = work->active_mode;
    work->active_mode = static_cast<u8>(mode);
    s32 dir = Camp_GetTransitionDir();
    if (dir < 0) {
        UiAnimSprite_SetAnim(&work->panel_sprites[0], 3, 0);
    } else if (Camp_GetTransitionDir() > 0) {
        UiAnimSprite_SetAnim(&work->panel_sprites[0], 2, 0);
    }
    const u8 tr_count = static_cast<u8>(work->registered_touch_count);
    for (s32 i = 0; i < tr_count; ++i) {
        UiTouch_UnregisterLastRegion();
    }
    work->registered_touch_count = 0;
    AsdMem_FillBytes(work->slot_touch_handles, 0x29, 0xFFFFFFFF);
    work = g_StatusDownWork;
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 2;
    work->prev_state = prev;
    if (mode == 0) {
        work->sub_state = 0;
    } else if (mode == 1) {
        work->sub_state = 3;
    } else if (mode == 2) {
        work->sub_state = 0x10;
    } else if (mode == 3) {
        work->sub_state = 0x11;
    } else if (mode == 4) {
        work->sub_state = 0x13;
    } else if (mode == 5) {
        work->sub_state = 0x15;
    }
    Camp_SetFadeColor(0, 0x323232FF);
}

}
"""

build_dir = Path("build/test_status_down_batch3")
build_dir.mkdir(parents=True, exist_ok=True)
src_file = build_dir / "test.cpp"
obj_file = build_dir / "test.o"
src_file.write_text(test_cpp, encoding="utf-8")

res = compile_tu_armv6k(src_file, obj_file, repo_root=Path('.'))
assert res.returncode == 0, f"Compilation failed: {res.stderr}"
dec_funcs = extract_elf_functions_detailed(obj_file)
print("Compiled 3 StatusDown functions successfully.")

STUB_BASE = 0x02000000
RET_ADDR = 0x03000000
GLOBAL_PTR_ADDR = 0x0044E190
WORK_STRUCT_ADDR = 0x02100000
PROMPT_STRUCT_ADDR = 0x02200000
SLOTS_ARRAY_ADDR = 0x02201000
RODATA_ADDR = 0x02300000

STUB_MAP = {
    '_ZN4smt42ui20Status_GetMainMenuIdEv': STUB_BASE + 0x00,
    'Sound_PlaySE': STUB_BASE + 0x10,
    'UiListCursor_Setup': STUB_BASE + 0x20,
    'AsdMem_Copy': STUB_BASE + 0x30,
    'Camp_GetTransitionDir': STUB_BASE + 0x40,
    'UiAnimSprite_SetAnim': STUB_BASE + 0x50,
    'UiTouch_UnregisterLastRegion': STUB_BASE + 0x60,
    'AsdMem_FillBytes': STUB_BASE + 0x70,
    'Camp_SetFadeColor': STUB_BASE + 0x80,
    '_ZN4smt42ui16g_StatusDownWorkE': GLOBAL_PTR_ADDR,
    '': RODATA_ADDR,
}

ORIG_ADDR_MAP = {
    0x0029af30: '_ZN4smt42ui20Status_GetMainMenuIdEv',
    0x002b8b78: 'Sound_PlaySE',
    0x0029fae8: 'UiListCursor_Setup',
    0x002c5ff4: 'AsdMem_Copy',
    0x0029e2b0: 'Camp_GetTransitionDir',
    0x002bdac0: 'UiAnimSprite_SetAnim',
    0x002b9008: 'UiTouch_UnregisterLastRegion',
    0x002c4450: 'AsdMem_FillBytes',
    0x0029f10c: 'Camp_SetFadeColor',
}

ARITY = {
    '_ZN4smt42ui20Status_GetMainMenuIdEv': 0,
    'Sound_PlaySE': 1,
    'UiListCursor_Setup': 6,
    'AsdMem_Copy': 3,
    'Camp_GetTransitionDir': 0,
    'UiAnimSprite_SetAnim': 3,
    'UiTouch_UnregisterLastRegion': 0,
    'AsdMem_FillBytes': 3,
    'Camp_SetFadeColor': 2,
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
        if user_data == 'Status_GetMainMenuId':
            uc.reg_write(UC_ARM_REG_R0, 6) # mock main menu id = 6
        elif user_data == 'Camp_GetTransitionDir':
            uc.reg_write(UC_ARM_REG_R0, 1) # mock transition dir = 1
        elif user_data == 'AsdMem_Copy':
            dst = uc.reg_read(UC_ARM_REG_R0)
            src = uc.reg_read(UC_ARM_REG_R1)
            sz = uc.reg_read(UC_ARM_REG_R2)
            data = uc.mem_read(src, sz)
            uc.mem_write(dst, bytes(data))
            
        lr = uc.reg_read(UC_ARM_REG_LR)
        if lr == 0:
            uc.emu_stop()
            return
        if lr & 1:
            uc.reg_write(UC_ARM_REG_CPSR, uc.reg_read(UC_ARM_REG_CPSR) | 0x20)
            uc.reg_write(UC_ARM_REG_PC, lr & ~1)
        else:
            uc.reg_write(UC_ARM_REG_CPSR, uc.reg_read(UC_ARM_REG_CPSR) & ~0x20)
            uc.reg_write(UC_ARM_REG_PC, lr)

TARGETS = [
    (0x00215990, '_ZN4smt42ui25StatusDown_SetPartyPromptEPKNS0_21StatusDownPartyPromptE', {'r0': PROMPT_STRUCT_ADDR}, 180),
    (0x00215a68, '_ZN4smt42ui24StatusDown_SetPartySlotsEPKti', {'r0': SLOTS_ARRAY_ADDR, 'r1': 5}, 248),
    (0x00292f44, '_ZN4smt42ui25StatusDown_SetDisplayModeEi', {'r0': 3}, 304),
]

for orig_addr, func_name, reg_inits, func_size in TARGETS:
    print(f"\nTesting {func_name} (0x{orig_addr:x})...")
    
    # 1. Orig
    uc_orig = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc_orig.mem_map(0x00100000, 0x00500000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_orig.mem_map(0x0FFFF000, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(WORK_STRUCT_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(PROMPT_STRUCT_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(RET_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_orig.mem_write(RET_ADDR, b"\x1e\xff\x2f\xe1")
    uc_orig.mem_write(0x00100000, ORIG_DATA)
    
    # Init work struct
    work_bytes = bytearray(0x4000)
    struct.pack_into('<I', work_bytes, 0x400, 5) # state = 5
    struct.pack_into('<I', work_bytes, 0x404, 2) # prev_state = 2
    work_bytes[0x3fc] = 1 # active_mode = 1
    struct.pack_into('<h', work_bytes, 0x47e, 10) # active_sound_id = 10
    work_bytes[0x480] = 2 # registered_touch_count = 2
    uc_orig.mem_write(WORK_STRUCT_ADDR, bytes(work_bytes))
    uc_orig.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', WORK_STRUCT_ADDR))
    
    # Init prompt struct
    prompt_bytes = struct.pack('<IIHI', 0x1111, 0x2222, 0x3333, 0x4444)
    uc_orig.mem_write(PROMPT_STRUCT_ADDR, prompt_bytes)
    
    # Init slots array: [101, 102, 103, 0, 105, 0, 0, 0]
    slots_bytes = struct.pack('<8H', 101, 102, 103, 0, 105, 0, 0, 0)
    uc_orig.mem_write(SLOTS_ARRAY_ADDR, slots_bytes)
    
    tracker_orig = CallTracker()
    for addr, name in ORIG_ADDR_MAP.items():
        if addr != orig_addr:
            uc_orig.mem_write(addr, b"\x1e\xff\x2f\xe1")
            uc_orig.hook_add(unicorn.UC_HOOK_CODE, tracker_orig.hook_call, user_data=name, begin=addr, end=addr)
        
    def hook_unmapped_orig(uc, access, address, size, value, user_data):
        pc = uc.reg_read(UC_ARM_REG_PC)
        lr = uc.reg_read(UC_ARM_REG_LR)
        print(f"[{func_name}] Orig unmapped at PC=0x{pc:x}, LR=0x{lr:x}, addr=0x{address:x}")
        return False
    uc_orig.hook_add(unicorn.UC_HOOK_MEM_READ_UNMAPPED | unicorn.UC_HOOK_MEM_WRITE_UNMAPPED | unicorn.UC_HOOK_MEM_FETCH_UNMAPPED, hook_unmapped_orig)
    
    uc_orig.reg_write(UC_ARM_REG_SP, 0x0FFFF000 + 0x8000)
    uc_orig.reg_write(UC_ARM_REG_LR, RET_ADDR)
    for r_name, r_val in reg_inits.items():
        reg_id = getattr(unicorn.arm_const, f"UC_ARM_REG_{r_name.upper()}")
        uc_orig.reg_write(reg_id, r_val)
    uc_orig.emu_start(orig_addr, RET_ADDR, timeout=100000)
    
    # 2. Dec
    dec_code = dec_funcs[func_name][0]
    relocs = dec_funcs[func_name][1]
    target_addr = 0x00380000
    patched_code = apply_relocs(dec_code, relocs, target_addr)
    
    uc_dec = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc_dec.mem_map(0x00100000, 0x00500000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_map(0x0FFFF000, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(WORK_STRUCT_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(PROMPT_STRUCT_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(STUB_BASE, 0x10000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_map(RET_ADDR, 0x10000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_map(RODATA_ADDR, 0x10000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_write(RODATA_ADDR, b'\x00\x03\x10\x11\x13\x15\x00\x00')
    uc_dec.mem_write(RET_ADDR, b"\x1e\xff\x2f\xe1")
    uc_dec.mem_write(0x00100000, ORIG_DATA)
    uc_dec.mem_write(target_addr, patched_code)
    
    uc_dec.mem_write(WORK_STRUCT_ADDR, bytes(work_bytes))
    uc_dec.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', WORK_STRUCT_ADDR))
    uc_dec.mem_write(PROMPT_STRUCT_ADDR, prompt_bytes)
    uc_dec.mem_write(SLOTS_ARRAY_ADDR, slots_bytes)
    
    tracker_dec = CallTracker()
    for name, addr in STUB_MAP.items():
        if name != '_ZN4smt42ui16g_StatusDownWorkE' and name != '':
            uc_dec.mem_write(addr, b"\x1e\xff\x2f\xe1")
            uc_dec.hook_add(unicorn.UC_HOOK_CODE, tracker_dec.hook_call, user_data=name, begin=addr, end=addr)
        
    uc_dec.reg_write(UC_ARM_REG_SP, 0x0FFFF000 + 0x8000)
    uc_dec.reg_write(UC_ARM_REG_LR, RET_ADDR)
    for r_name, r_val in reg_inits.items():
        reg_id = getattr(unicorn.arm_const, f"UC_ARM_REG_{r_name.upper()}")
        uc_dec.reg_write(reg_id, r_val)
    uc_dec.emu_start(target_addr, RET_ADDR, timeout=100000)
    
    assert tracker_orig.calls == tracker_dec.calls, f"Calls mismatch for {func_name}:\n  Orig: {tracker_orig.calls}\n  Dec:  {tracker_dec.calls}"
    print(f"  Calls match: {tracker_dec.calls}")
    
    mem_orig = uc_orig.mem_read(WORK_STRUCT_ADDR, 0x600)
    mem_dec = uc_dec.mem_read(WORK_STRUCT_ADDR, 0x600)
    assert mem_orig == mem_dec, f"Work struct memory mismatch for {func_name}!"
    print(f"  Work struct memory matches 100%!")

print("\nALL 3 STATUSDOWN FUNCTIONS MATCH 100%!")
