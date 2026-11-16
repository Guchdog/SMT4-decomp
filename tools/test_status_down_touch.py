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

struct UiLayoutRect {
    s16 w;
    s16 h;
};

struct UiLayoutNode {
    u8  unk_00[8];
    s16 x;
    s16 y;
    const UiLayoutRect* rect;
};

extern "C" {
    void  UiTouch_UnregisterLastRegion();
    void  camp_func_002c4450(void* ptr, u32 size, s32 val) asm("camp_func_002c4450");
    s32   camp_func_0029f0f4(void* cursor) asm("camp_func_0029f0f4");
    s16   UiTouch_RegisterRegion(u32 group_id, u32 node_id);
    const UiLayoutNode* camp_func_002bf6d0(u32 group, u32 node_id) asm("camp_func_002bf6d0");
    s16   UiTouch_RegisterRectRegion(s32 x, s32 y, s32 w, s32 h);
    bool  Flag_CheckEventBit(u32 flag_id);
}

namespace smt4::ui {

void StatusDown_SetupTouchRegions() {
    auto* work = g_StatusDownWork;
    const s32 prev_count = static_cast<u8>(work->registered_touch_count);
    for (s32 i = 0; i < prev_count; ++i) {
        UiTouch_UnregisterLastRegion();
    }
    work->registered_touch_count = 0;
    camp_func_002c4450(work->slot_touch_handles, 0x29, -1);

    switch (work->state) {
    case 3: {
        for (s32 i = 0; i < camp_func_0029f0f4(&work->list_cursor_main); ++i) {
            work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, 0x414 + i);
            work->registered_touch_count++;
        }
        work->l_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50F);
        work->r_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50E);
        work->registered_touch_count += 2;
        break;
    }
    case 4: {
        for (s32 i = 0; i < camp_func_0029f0f4(&work->list_cursor_main); ++i) {
            work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, 0x414 + i);
            work->registered_touch_count++;
        }
        break;
    }
    case 6: {
        for (s32 i = 0; i < camp_func_0029f0f4(&work->list_cursor_main); ++i) {
            work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, 0x414 + i);
            work->registered_touch_count++;
        }
        const s32 last_slot = static_cast<u8>(work->registered_touch_count);
        work->slot_touch_handles[last_slot] = UiTouch_RegisterRegion(0x1A, 0x4F1);
        work->registered_touch_count++;
        break;
    }
    case 11: {
        for (s32 i = 0; i < camp_func_0029f0f4(&work->list_cursor_main) - 1; ++i) {
            work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, 0x414 + i);
            work->registered_touch_count++;
        }
        const auto* node_a = camp_func_002bf6d0(0x1A, 0x4F1);
        const auto* node_b = camp_func_002bf6d0(0x1A, 0x41F);
        const s16 handle = UiTouch_RegisterRectRegion(
            node_a->x, node_a->y, node_b->rect->w, node_a->rect->h);
        const s32 last_slot = static_cast<u8>(work->registered_touch_count);
        work->slot_touch_handles[last_slot] = handle;
        work->registered_touch_count++;
        break;
    }
    case 16: {
        for (s32 i = 0; i < 7; ++i) {
            if (Flag_CheckEventBit(0x410) || (i != 1 && i != 2)) {
                work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, 0x466 + i);
            } else {
                work->slot_touch_handles[i] = 0;
            }
            work->registered_touch_count++;
        }
        work->l_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50F);
        work->r_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50E);
        work->registered_touch_count += 2;
        break;
    }
    case 17: {
        for (s32 i = 0; i < 11; ++i) {
            work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, 0x44C + i);
            work->registered_touch_count++;
        }
        work->scroll_up_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E7);
        work->scroll_down_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E8);
        work->btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E9);
        work->registered_touch_count += 3;
        work->l_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50F);
        work->r_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50E);
        work->registered_touch_count += 2;
        break;
    }
    case 19: {
        const s32 total_items = *reinterpret_cast<const s16*>(reinterpret_cast<const u8*>(work) + 0x2232);
        for (s32 row = 0; row < 9; ++row) {
            for (s32 col = 0; col < 4; ++col) {
                const s32 idx = row * 4 + col;
                if (idx < total_items) {
                    work->slot_touch_handles[idx] = UiTouch_RegisterRegion(0x1A, 0x4AE + idx);
                    work->registered_touch_count++;
                }
            }
        }
        work->scroll_up_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E7);
        work->scroll_down_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E8);
        work->btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E9);
        work->registered_touch_count += 3;
        work->l_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50F);
        work->r_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50E);
        work->registered_touch_count += 2;
        break;
    }
    case 21: {
        work->scroll_up_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4EA);
        work->scroll_down_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4EB);
        work->btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4EC);
        work->registered_touch_count += 3;
        work->l_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50F);
        work->r_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50E);
        work->registered_touch_count += 2;
        break;
    }
    case 22:
    case 23:
    case 25:
    case 26: {
        for (s32 i = 0; i < camp_func_0029f0f4(&work->category_cursor) - 1; ++i) {
            work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, 0x414 + i);
            work->registered_touch_count++;
        }
        const s16 handle = UiTouch_RegisterRegion(0x1A, 0x54A);
        const s32 count = camp_func_0029f0f4(&work->category_cursor);
        work->slot_touch_handles[count - 1] = handle;
        work->registered_touch_count++;
        break;
    }
    default:
        break;
    }
}

}
"""

build_dir = Path("build/test_status_down_touch")
build_dir.mkdir(parents=True, exist_ok=True)
src_file = build_dir / "test.cpp"
obj_file = build_dir / "test.o"
src_file.write_text(test_cpp, encoding="utf-8")

res = compile_tu_armv6k(src_file, obj_file, repo_root=Path('.'))
assert res.returncode == 0, f"Compilation failed: {res.stderr}"
dec_funcs = extract_elf_functions_detailed(obj_file)
print("Compiled StatusDown_SetupTouchRegions test successfully.")

STUB_BASE = 0x02000000
RET_ADDR = 0x03000000
GLOBAL_PTR_ADDR = 0x0044E190
WORK_STRUCT_ADDR = 0x02100000
LAYOUT_NODE_A = 0x02180000
LAYOUT_NODE_B = 0x02180100
RECT_A = 0x02180200
RECT_B = 0x02180210
RODATA_ADDR = 0x02300000

STUB_MAP = {
    'UiTouch_UnregisterLastRegion': STUB_BASE + 0x00,
    'camp_func_002c4450': STUB_BASE + 0x10,
    'camp_func_0029f0f4': STUB_BASE + 0x20,
    'UiTouch_RegisterRegion': STUB_BASE + 0x30,
    'camp_func_002bf6d0': STUB_BASE + 0x40,
    'UiTouch_RegisterRectRegion': STUB_BASE + 0x50,
    'Flag_CheckEventBit': STUB_BASE + 0x60,
    '_ZN4smt42ui16g_StatusDownWorkE': GLOBAL_PTR_ADDR,
    '': RODATA_ADDR,
}

ORIG_ADDR_MAP = {
    0x002b9008: 'UiTouch_UnregisterLastRegion',
    0x002c4450: 'camp_func_002c4450',
    0x0029f0f4: 'camp_func_0029f0f4',
    0x002b88c4: 'UiTouch_RegisterRegion',
    0x002bf6d0: 'camp_func_002bf6d0',
    0x0029e2f4: 'UiTouch_RegisterRectRegion',
    0x002c0ba8: 'Flag_CheckEventBit',
}

ARITY = {
    'UiTouch_UnregisterLastRegion': 0,
    'camp_func_002c4450': 3,
    'camp_func_0029f0f4': 1,
    'UiTouch_RegisterRegion': 2,
    'camp_func_002bf6d0': 2,
    'UiTouch_RegisterRectRegion': 4,
    'Flag_CheckEventBit': 1,
}

def apply_relocs(code_bytes, relocs, target_addr):
    mutable = bytearray(code_bytes)
    for rel in relocs:
        offset = rel.offset
        name = rel.symbol_name
        rel_type = rel.relocation_type
        if name == '':
            orig = struct.unpack_from('<I', mutable, offset)[0]
            # Check if orig is pointing within the text section
            if orig < len(code_bytes):
                sym_val = target_addr
            else:
                sym_val = RODATA_ADDR
        elif name in STUB_MAP:
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

next_handle = 100

class CallTracker:
    def __init__(self):
        self.calls = []
        
    def hook_call(self, uc, address, size, user_data):
        global next_handle
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
            uc.reg_write(UC_ARM_REG_R0, 4) # 4 items in cursor
        elif user_data in ('UiTouch_RegisterRegion', 'UiTouch_RegisterRectRegion'):
            uc.reg_write(UC_ARM_REG_R0, next_handle)
            next_handle += 1
        elif user_data == 'Flag_CheckEventBit':
            uc.reg_write(UC_ARM_REG_R0, 1)
        elif user_data == 'camp_func_002bf6d0':
            node_id = uc.reg_read(UC_ARM_REG_R1)
            if node_id == 0x4F1:
                uc.reg_write(UC_ARM_REG_R0, LAYOUT_NODE_A)
            else:
                uc.reg_write(UC_ARM_REG_R0, LAYOUT_NODE_B)
        elif user_data == 'camp_func_002c4450':
            ptr = uc.reg_read(UC_ARM_REG_R0)
            sz = uc.reg_read(UC_ARM_REG_R1)
            val = uc.reg_read(UC_ARM_REG_R2) & 0xFF
            uc.mem_write(ptr, bytes([val] * sz))
            
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

func_name = '_ZN4smt42ui28StatusDown_SetupTouchRegionsEv'
dec_code = dec_funcs[func_name][0]
relocs = dec_funcs[func_name][1]
target_addr = 0x00380000
patched_code = apply_relocs(dec_code, relocs, target_addr)

TEST_STATES = [0, 3, 4, 6, 11, 16, 17, 19, 21, 22, 23, 25, 26, 99]

for test_state in TEST_STATES:
    orig_addr = 0x0026b0d0
    
    # Init work struct bytes
    init_work = bytearray(0x2400)
    init_work[0x480] = 3 # registered_touch_count = 3 (will test unregister loop!)
    struct.pack_into('<I', init_work, 0x400, test_state) # work->state
    struct.pack_into('<h', init_work, 0x2232, 10) # total_items = 10 for grid
    
    # Node A: x=10, y=20, rect=RECT_A
    node_a = bytearray(0x20)
    struct.pack_into('<hhI', node_a, 8, 10, 20, RECT_A)
    # Node B: x=30, y=40, rect=RECT_B
    node_b = bytearray(0x20)
    struct.pack_into('<hhI', node_b, 8, 30, 40, RECT_B)
    # Rect A: w=50, h=60
    rect_a = struct.pack('<hh', 50, 60)
    # Rect B: w=70, h=80
    rect_b = struct.pack('<hh', 70, 80)
    
    # 1. Orig
    next_handle = 100
    uc_orig = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc_orig.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc_orig.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc_orig.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc_orig.mem_map(0x00100000, 0x00500000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_orig.mem_map(0x0FFFF000, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(WORK_STRUCT_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(0x02180000, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(RET_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_orig.mem_write(RET_ADDR, b"\x1e\xff\x2f\xe1")
    uc_orig.mem_write(0x00100000, ORIG_DATA)
    uc_orig.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', WORK_STRUCT_ADDR))
    uc_orig.mem_write(WORK_STRUCT_ADDR, bytes(init_work))
    uc_orig.mem_write(LAYOUT_NODE_A, bytes(node_a))
    uc_orig.mem_write(LAYOUT_NODE_B, bytes(node_b))
    uc_orig.mem_write(RECT_A, rect_a)
    uc_orig.mem_write(RECT_B, rect_b)
    
    tracker_orig = CallTracker()
    for addr, name in ORIG_ADDR_MAP.items():
        if addr != orig_addr:
            uc_orig.mem_write(addr, b"\x1e\xff\x2f\xe1")
            uc_orig.hook_add(unicorn.UC_HOOK_CODE, tracker_orig.hook_call, user_data=name, begin=addr, end=addr)
        
    uc_orig.reg_write(UC_ARM_REG_SP, 0x0FFFF000 + 0x8000)
    uc_orig.reg_write(UC_ARM_REG_LR, RET_ADDR)
    uc_orig.emu_start(orig_addr, RET_ADDR, timeout=1000000)
    
    # 2. Dec
    next_handle = 100
    uc_dec = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc_dec.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc_dec.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc_dec.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc_dec.mem_map(0x00100000, 0x00500000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_map(0x0FFFF000, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(WORK_STRUCT_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(0x02180000, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(STUB_BASE, 0x10000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_map(RET_ADDR, 0x10000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_map(RODATA_ADDR, 0x10000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_write(RET_ADDR, b"\x1e\xff\x2f\xe1")
    uc_dec.mem_write(0x00100000, ORIG_DATA)
    uc_dec.mem_write(target_addr, patched_code)
    uc_dec.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', WORK_STRUCT_ADDR))
    uc_dec.mem_write(WORK_STRUCT_ADDR, bytes(init_work))
    uc_dec.mem_write(LAYOUT_NODE_A, bytes(node_a))
    uc_dec.mem_write(LAYOUT_NODE_B, bytes(node_b))
    uc_dec.mem_write(RECT_A, rect_a)
    uc_dec.mem_write(RECT_B, rect_b)
    
    tracker_dec = CallTracker()
    for name, addr in STUB_MAP.items():
        if name not in ('_ZN4smt42ui16g_StatusDownWorkE', ''):
            uc_dec.mem_write(addr, b"\x1e\xff\x2f\xe1")
            uc_dec.hook_add(unicorn.UC_HOOK_CODE, tracker_dec.hook_call, user_data=name, begin=addr, end=addr)
        
    uc_dec.reg_write(UC_ARM_REG_SP, 0x0FFFF000 + 0x8000)
    uc_dec.reg_write(UC_ARM_REG_LR, RET_ADDR)
    uc_dec.emu_start(target_addr, RET_ADDR, timeout=1000000)
    
    assert tracker_orig.calls == tracker_dec.calls, f"Calls mismatch for state {test_state}:\n  Orig: {tracker_orig.calls}\n  Dec:  {tracker_dec.calls}"
    
    mem_orig = uc_orig.mem_read(WORK_STRUCT_ADDR, 0x500)
    mem_dec = uc_dec.mem_read(WORK_STRUCT_ADDR, 0x500)
    assert mem_orig == mem_dec, f"Work struct memory mismatch for state {test_state}!"
    print(f"State {test_state:2d}: calls ({len(tracker_dec.calls)}) and memory match 100%!")

print("\nALL 14 TEST STATES OF STATUSDOWN_SETUPTOUCHREGIONS MATCH 100%!")
