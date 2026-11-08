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
    extern u8* g_AsdGpuState;
    s32   UiListCursor_GetSelectedRow(const UiListCursor* cursor);
    s32   UiListCursor_GetRowCount(const UiListCursor* cursor);
    s32   Camp_GetMainMenuId();
    void  UiSprite_SetGlobalAlpha(f32 alpha);
    void  UiSprite_DrawPanel(s32 prio, u32 group_id, u32 panel_id, s32 x, s32 y, s32 depth);
    void  UiSprite_DrawNode(s32 prio, u32 group_id, u32 node_id, s32 x, s32 y, s32 depth);
    const UiLayoutNode* LayoutNode(u32 group_id, u32 node_id);
    void  UiScissor_SetRect(s32 x, s32 y, s32 w, s32 h, s32 enable);
    s32   UiAnimSprite_GetPosY(const UiAnimSprite* sprite);
    s32   UiAnimSprite_GetPosX(const UiAnimSprite* sprite);
    void  UiFont_FormatString(char* dst, const char* fmt, ...);
    void  UiFont_DrawText(s32 prio, u32 color, const char* str, f32 x, f32 y, f32 scale, f32 a7, f32 a8);
    const char* camp_func_002bcff0(s32 demon_id);
    void  UiParty_DrawDemonBars(s16 demon_id, s32 x, s32 y, s32 prio, s32 scale_word, s32 a5);
    s32   Party_GetDemonLevel(s32 demon_id);
    void  UiFont_DrawFormatted(u32 screen, s32 x, s32 y, s32 mode, s32 width, s32 prio, const char* fmt, s32 val);
    s32   Party_GetDemonOrderNumber(s32 demon_id, s32 flag);
    const u8* Party_GetDemonWorkPtr(s32 demon_id);
    s32   Party_GetDemonActiveIndex(s32 demon_id);

    void  GpuModeSlotSet(u32 slot_offset, u32 value);
    __attribute__((pcs("aapcs"))) void StatusDown_DrawPartySlotRow(s32 x_offset, s32 y_offset, s32 demon_id,
                                                                  u32 node_id, f32 scale, s32 is_stock_row,
                                                                  s32 is_empty_mode, s32 highlight_mode);
}

void GpuModeSlotSet(u32 slot_offset, u32 value) {
    u8* slot = g_AsdGpuState + 0x1000 + slot_offset;
    const u32 index = *reinterpret_cast<u32*>(slot);
    u32* entry = reinterpret_cast<u32*>(slot + 8 + index * 4);
    const u32 old = *entry;
    *entry = value;
    if (*reinterpret_cast<u8*>(slot + 0x18) != 0 || old != value) {
        reinterpret_cast<void (*)()>(
            *reinterpret_cast<u32*>(slot + 0x1C))();
        *reinterpret_cast<u8*>(slot + 0x18) = 0;
    }
}

__attribute__((pcs("aapcs"))) void StatusDown_DrawPartySlotRow(s32 x_offset, s32 y_offset, s32 demon_id,
                                                              u32 node_id, f32 scale, s32 is_stock_row,
                                                              s32 is_empty_mode, s32 highlight_mode) {
    StatusDownWork* work = g_StatusDownWork;
    const UiLayoutNode* row_node = LayoutNode(0x1A, node_id);
    const s32 selected_row = UiListCursor_GetSelectedRow(&work->list_cursor_main);

    const f32 pulse_alpha = *reinterpret_cast<const f32*>(&work->panel_sprites[1].raw[0x20]);
    UiSprite_SetGlobalAlpha(pulse_alpha);
    UiSprite_DrawPanel(2, 0x1A, 8, x_offset + row_node->x, y_offset + row_node->y, 0xBF);

    UiSprite_SetGlobalAlpha(1.0f);
    UiSprite_DrawNode(2, 0x1A, 0x41F, x_offset + row_node->x, y_offset + row_node->y, 0xC4);

    u32 cursor_frame_node = 0x420;
    if (work->touch_drag_state[0] == 0 && work->touch_drag_state[1] == 0 &&
        work->touch_drag_state[2] == 0 && work->lr_state_left == 0 &&
        work->lr_state_right == 0 && work->touch_hold_state >= 0) {
        cursor_frame_node = 0x421;
    }
    UiSprite_DrawNode(2, 0x1A, cursor_frame_node, x_offset + row_node->x, y_offset + row_node->y, 0xC4);

    const UiLayoutNode* clip_node = LayoutNode(0x1A, 0x420);
    GpuModeSlotSet(0x30C, 3);
    UiScissor_SetRect(x_offset + row_node->x + clip_node->x,
                      y_offset + row_node->y + clip_node->y,
                      clip_node->rect->w, clip_node->rect->h, 1);

    const s32 anim_y = UiAnimSprite_GetPosY(&work->panel_sprites[3]);
    const s32 anim_x = UiAnimSprite_GetPosX(&work->panel_sprites[3]);
    UiSprite_DrawNode(2, 0x1A, 0x422,
                      x_offset + anim_x + row_node->x,
                      y_offset + anim_y + row_node->y, 0xC9);
    GpuModeSlotSet(0x30C, 0);

    u32 text_color = 0xFFFFFFFFu;
    if (highlight_mode == 1) {
        text_color = 0x72E027FFu;
    } else if (highlight_mode == 2) {
        text_color = 0xDC0F14FFu;
    }

    if (work->state == 11 || work->state == 14) {
        if (work->selected_result == selected_row) {
            text_color = 0x72E027FFu;
        } else {
            const s32 row_count = UiListCursor_GetRowCount(&work->list_cursor_main);
            if (selected_row == row_count - 1) {
                text_color = 0x72E027FFu;
            } else {
                text_color = 0x5A5A5AFFu;
            }
        }
    } else if (work->state != 6 && work->state != 9) {
        if (work->flag_548 != 0 && work->highlighted_slot_index == selected_row) {
            text_color = 0x72E027FFu;
        }
    }

    const UiLayoutNode* name_node = LayoutNode(0x1A, 0x42B);
    char name_buf[64];
    if (is_empty_mode != 0 && demon_id == 0) {
        UiFont_FormatString(name_buf, "\\x82\\x6d\\x82\\x85\\x82\\x97\\x81\\x40\\x82\\x92\\x82\\x85\\x82\\x87\\x82\\x89\\x82\\x93\\x82\\x94\\x82\\x92\\x82\\x81\\x82\\x94\\x82\\x89\\x82\\x8f\\x82\\x8e\\x81\\x40\\x82\\x90\\x82\\x8f\\x82\\x93\\x82\\x93\\x82\\x89\\x82\\x82\\x82\\x8c\\x82\\x85\\x81\\x49");
        text_color = 0x5A5A5AFFu;
    } else {
        if (is_stock_row != 0) {
            UiFont_FormatString(name_buf, "\\x81\\x48\\x81\\x48\\x81\\x48");
        } else {
            const char* dname = camp_func_002bcff0(demon_id);
            UiFont_FormatString(name_buf, "%s", dname);
        }
    }
    UiFont_DrawText(3, text_color, name_buf,
                    static_cast<f32>(x_offset + row_node->x + name_node->x),
                    static_cast<f32>(y_offset + row_node->y + name_node->y),
                    0.2f, 0.0f, 1.0f);

    if (is_empty_mode == 0 || demon_id != 0) {
        UiSprite_DrawNode(2, 0x1A, 0x425, x_offset + row_node->x, y_offset + row_node->y, 0xC4);
        const UiLayoutNode* bar_node = LayoutNode(0x1A, 0x42A);
        UiParty_DrawDemonBars(static_cast<s16>(demon_id),
                              x_offset + row_node->x + bar_node->x,
                              y_offset + row_node->y + bar_node->y,
                              0xC9, *reinterpret_cast<const s32*>(&scale), 0);
    }

    if (is_stock_row != 0) {
        return;
    }

    if (is_empty_mode != 0) {
        UiSprite_DrawNode(2, 0x1A, 0x522, x_offset + row_node->x, y_offset + row_node->y, 0xC4);
        const UiLayoutNode* lv_node = LayoutNode(0x1A, 0x52A);
        if (demon_id != 0) {
            const s32 lv = Party_GetDemonLevel(demon_id);
            UiFont_DrawFormatted(0, x_offset + row_node->x + lv_node->x,
                                 y_offset + row_node->y + lv_node->y,
                                 1, 8, 0xC9, "%d", lv);
        } else {
            char empty_lv[64];
            UiFont_FormatString(empty_lv, "---");
            UiFont_DrawFormatted(0, x_offset + row_node->x + lv_node->x,
                                 y_offset + row_node->y + lv_node->y,
                                 1, 8, 0xC9, empty_lv, 0);
        }
        return;
    }

    UiSprite_DrawNode(2, 0x1A, 0x423, x_offset + row_node->x, y_offset + row_node->y, 0xC4);
    s32 order_num = 0;
    if (work->active_sound_id < 0) {
        order_num = Party_GetDemonOrderNumber(demon_id, 1);
    } else if (Camp_GetMainMenuId() == 6) {
        const u8* dwork = Party_GetDemonWorkPtr(demon_id);
        if (dwork != nullptr) {
            order_num = dwork[0x22];
        }
    } else {
        order_num = Party_GetDemonActiveIndex(demon_id);
    }

    const UiLayoutNode* ord_node = LayoutNode(0x1A, 0x429);
    UiFont_DrawFormatted(0, x_offset + row_node->x + ord_node->x,
                         y_offset + row_node->y + ord_node->y,
                         1, 4, 0xC9, "%d", order_num);
}
"""

build_dir = Path("build/test_status_down_party_slot")
build_dir.mkdir(parents=True, exist_ok=True)
src_file = build_dir / "test.cpp"
obj_file = build_dir / "test.o"
src_file.write_text(test_cpp, encoding="utf-8")

res = compile_tu_armv6k(src_file, obj_file, repo_root=Path('.'))
assert res.returncode == 0, f"Compilation failed: {res.stderr}"
dec_funcs = extract_elf_functions_detailed(obj_file)
print("Compiled StatusDown_DrawPartySlotRow test successfully.")

STUB_BASE = 0x02000000
RET_ADDR = 0x03000000
GLOBAL_PTR_ADDR = 0x0044E190
GPU_PTR_ADDR = 0x0044EA00
WORK_STRUCT_ADDR = 0x02100000
GPU_STATE_ADDR = 0x02200000
RODATA_ADDR = 0x02300000
DEMON_WORK_ADDR = 0x02400000
NAME_STR_ADDR = 0x02410000

LAYOUT_NODES = {}
LAYOUT_BASE = 0x02500000
RECT_BASE = 0x02580000

for idx in list(range(0x410, 0x430)) + list(range(0x520, 0x530)):
    node_addr = LAYOUT_BASE + (idx - 0x400) * 0x20
    rect_addr = RECT_BASE + (idx - 0x400) * 0x10
    LAYOUT_NODES[idx] = (node_addr, rect_addr)

STUB_MAP = {
    'UiListCursor_GetSelectedRow': STUB_BASE + 0x00,
    'UiListCursor_GetRowCount': STUB_BASE + 0x10,
    'Camp_GetMainMenuId': STUB_BASE + 0x20,
    'UiSprite_SetGlobalAlpha': STUB_BASE + 0x30,
    'UiSprite_DrawPanel': STUB_BASE + 0x40,
    'UiSprite_DrawNode': STUB_BASE + 0x50,
    'LayoutNode': STUB_BASE + 0x60,
    'UiScissor_SetRect': STUB_BASE + 0x70,
    'UiAnimSprite_GetPosY': STUB_BASE + 0x80,
    'UiAnimSprite_GetPosX': STUB_BASE + 0x90,
    'UiFont_FormatString': STUB_BASE + 0xA0,
    'UiFont_DrawText': STUB_BASE + 0xB0,
    'camp_func_002bcff0': STUB_BASE + 0xC0,
    'UiParty_DrawDemonBars': STUB_BASE + 0xD0,
    'Party_GetDemonLevel': STUB_BASE + 0xE0,
    'UiFont_DrawFormatted': STUB_BASE + 0xF0,
    'Party_GetDemonOrderNumber': STUB_BASE + 0x100,
    'Party_GetDemonWorkPtr': STUB_BASE + 0x110,
    'Party_GetDemonActiveIndex': STUB_BASE + 0x120,
    '_ZN4smt42ui16g_StatusDownWorkE': GLOBAL_PTR_ADDR,
    'g_AsdGpuState': GPU_PTR_ADDR,
    '': RODATA_ADDR,
}

ORIG_ADDR_MAP = {
    0x0029f248: 'UiListCursor_GetSelectedRow',
    0x0029f0f4: 'UiListCursor_GetRowCount',
    0x0029af30: 'Camp_GetMainMenuId',
    0x002bf710: 'UiSprite_SetGlobalAlpha',
    0x002bf558: 'UiSprite_DrawPanel',
    0x002bf460: 'UiSprite_DrawNode',
    0x002bf6d0: 'LayoutNode',
    0x0029a418: 'UiScissor_SetRect',
    0x002bef70: 'UiAnimSprite_GetPosY',
    0x002bef7c: 'UiAnimSprite_GetPosX',
    0x002be7fc: 'UiFont_FormatString',
    0x002be77c: 'UiFont_DrawText',
    0x002bcff0: 'camp_func_002bcff0',
    0x002b6f74: 'UiParty_DrawDemonBars',
    0x0028d498: 'Party_GetDemonLevel',
    0x002be16c: 'UiFont_DrawFormatted',
    0x0029ac70: 'Party_GetDemonOrderNumber',
    0x002ae3f0: 'Party_GetDemonWorkPtr',
    0x0029abc0: 'Party_GetDemonActiveIndex',
}

ARITY = {
    'UiListCursor_GetSelectedRow': 1,
    'UiListCursor_GetRowCount': 1,
    'Camp_GetMainMenuId': 0,
    'UiSprite_SetGlobalAlpha': 0,
    'UiSprite_DrawPanel': 4,
    'UiSprite_DrawNode': 4,
    'LayoutNode': 2,
    'UiScissor_SetRect': 4,
    'UiAnimSprite_GetPosY': 1,
    'UiAnimSprite_GetPosX': 1,
    'UiFont_FormatString': 2,
    'UiFont_DrawText': 3,
    'camp_func_002bcff0': 1,
    'UiParty_DrawDemonBars': 4,
    'Party_GetDemonLevel': 1,
    'UiFont_DrawFormatted': 4,
    'Party_GetDemonOrderNumber': 2,
    'Party_GetDemonWorkPtr': 1,
    'Party_GetDemonActiveIndex': 1,
}

def apply_relocs(code_bytes, relocs, target_addr):
    mutable = bytearray(code_bytes)
    for rel in relocs:
        offset = rel.offset
        name = rel.symbol_name
        rel_type = rel.relocation_type
        if name == '':
            if offset < 0x300:
                sym_val = target_addr - 0x50 # subtract function offset in .text
            else:
                sym_val = RODATA_ADDR
        elif name in STUB_MAP:
            sym_val = STUB_MAP[name]
        else:
            raise ValueError(f"Unknown symbol '{name}'")
            
        if rel_type in (28, 29):
            orig = struct.unpack_from('<I', mutable, offset)[0]
            target = sym_val
            pc = target_addr + offset + 8
            new_disp = ((target - pc) >> 2) & 0x00FFFFFF
            inst = (orig & 0xFF000000) | new_disp
            struct.pack_into('<I', mutable, offset, inst)
        elif rel_type in (2, 38):
            orig = struct.unpack_from('<I', mutable, offset)[0]
            val = (sym_val + orig) & 0xFFFFFFFF
            struct.pack_into('<I', mutable, offset, val)
        else:
            raise ValueError(f"Unsupported reloc type {rel_type}")
    return bytes(mutable)

class CallTracker:
    def __init__(self, test_ctx):
        self.calls = []
        self.ctx = test_ctx
        
    def hook_call(self, uc, address, size, user_data):
        arity = ARITY.get(user_data, 4)
        raw_regs = [
            hex(uc.reg_read(UC_ARM_REG_R0)),
            hex(uc.reg_read(UC_ARM_REG_R1)),
            hex(uc.reg_read(UC_ARM_REG_R2)),
            hex(uc.reg_read(UC_ARM_REG_R3)),
        ]
        
        regs = []
        for r_idx, r in enumerate(raw_regs[:arity]):
            val = int(r, 16)
            if 0x04000000 <= val < 0x04100000:
                regs.append('<stack>')
            elif user_data == 'UiFont_FormatString' and r_idx == 1:
                regs.append('<fmt_str>')
            elif user_data == 'UiFont_DrawText' and r_idx == 2:
                regs.append('<draw_str>')
            else:
                regs.append(r)

        extra = []
        if user_data == 'UiFont_DrawText':
            s0 = uc.reg_read(UC_ARM_REG_D0) & 0xFFFFFFFF
            s1 = (uc.reg_read(UC_ARM_REG_D0) >> 32) & 0xFFFFFFFF
            s2 = uc.reg_read(UC_ARM_REG_D1) & 0xFFFFFFFF
            f0 = struct.unpack('<f', struct.pack('<I', s0))[0]
            f1 = struct.unpack('<f', struct.pack('<I', s1))[0]
            f2 = struct.unpack('<f', struct.pack('<I', s2))[0]
            str_bytes = uc.mem_read(int(raw_regs[2], 16), 16)
            s_val = str_bytes.split(b'\0')[0].decode('latin1', errors='replace')
            extra = [f"color={regs[1]}", f"x={f0:.1f}", f"y={f1:.1f}", f"scale={f2:.2f}", f"str='{s_val}'"]
        elif user_data in ('UiSprite_DrawPanel', 'UiSprite_DrawNode'):
            sp = uc.reg_read(UC_ARM_REG_SP)
            sp0 = struct.unpack('<I', uc.mem_read(sp, 4))[0]
            sp4 = struct.unpack('<I', uc.mem_read(sp + 4, 4))[0]
            extra = [f"sp0={hex(sp0)}", f"sp4={hex(sp4)}"]
        elif user_data == 'UiScissor_SetRect':
            sp = uc.reg_read(UC_ARM_REG_SP)
            sp0 = struct.unpack('<I', uc.mem_read(sp, 4))[0]
            extra = [f"sp0={hex(sp0)}"]
        elif user_data == 'UiSprite_SetGlobalAlpha':
            s0 = uc.reg_read(UC_ARM_REG_D0) & 0xFFFFFFFF
            f0 = struct.unpack('<f', struct.pack('<I', s0))[0]
            extra = [f"alpha={f0:.2f}"]
        elif user_data == 'UiParty_DrawDemonBars':
            sp = uc.reg_read(UC_ARM_REG_SP)
            sp0 = struct.unpack('<I', uc.mem_read(sp, 4))[0]
            extra = [f"scale_word={hex(sp0)}"]
        elif user_data == 'UiFont_DrawFormatted':
            sp = uc.reg_read(UC_ARM_REG_SP)
            sp0 = struct.unpack('<I', uc.mem_read(sp, 4))[0]
            sp4 = struct.unpack('<I', uc.mem_read(sp + 4, 4))[0]
            sp8 = struct.unpack('<I', uc.mem_read(sp + 8, 4))[0]
            fmt_str = uc.mem_read(sp8, 8).split(b'\0')[0].decode('ascii', errors='replace')
            extra = [f"width={sp0}", f"prio={hex(sp4)}", f"fmt='{fmt_str}'"]

        self.calls.append((user_data, tuple(regs), tuple(extra)))
        
        # Stubs behavior:
        if user_data == 'UiListCursor_GetSelectedRow':
            uc.reg_write(UC_ARM_REG_R0, self.ctx.get('selected_row', 0))
        elif user_data == 'UiListCursor_GetRowCount':
            uc.reg_write(UC_ARM_REG_R0, self.ctx.get('row_count', 4))
        elif user_data == 'Camp_GetMainMenuId':
            uc.reg_write(UC_ARM_REG_R0, self.ctx.get('main_menu_id', 1))
        elif user_data == 'LayoutNode':
            node_id = uc.reg_read(UC_ARM_REG_R1)
            node_addr, _ = LAYOUT_NODES.get(node_id, (0, 0))
            uc.reg_write(UC_ARM_REG_R0, node_addr)
        elif user_data == 'UiFont_FormatString':
            dst = uc.reg_read(UC_ARM_REG_R0)
            src = uc.reg_read(UC_ARM_REG_R1)
            s_bytes = uc.mem_read(src, 16)
            uc.mem_write(dst, bytes(s_bytes))
        elif user_data == 'camp_func_002bcff0':
            uc.reg_write(UC_ARM_REG_R0, NAME_STR_ADDR)
        elif user_data == 'UiAnimSprite_GetPosX':
            uc.reg_write(UC_ARM_REG_R0, 15)
        elif user_data == 'UiAnimSprite_GetPosY':
            uc.reg_write(UC_ARM_REG_R0, 25)
        elif user_data == 'Party_GetDemonLevel':
            uc.reg_write(UC_ARM_REG_R0, 45)
        elif user_data == 'Party_GetDemonOrderNumber':
            uc.reg_write(UC_ARM_REG_R0, 2)
        elif user_data == 'Party_GetDemonWorkPtr':
            uc.reg_write(UC_ARM_REG_R0, DEMON_WORK_ADDR)
        elif user_data == 'Party_GetDemonActiveIndex':
            uc.reg_write(UC_ARM_REG_R0, 3)

def run_test_case(test_ctx, orig_code, dec_code, rodata_data):
    results = {}
    for mode, code in [('orig', orig_code), ('dec', dec_code)]:
        uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
        uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
        uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

        uc.mem_map(0x00100000, 0x00300000, UC_PROT_READ | UC_PROT_EXEC)
        uc.mem_map(0x00400000, 0x00100000, UC_PROT_READ | UC_PROT_WRITE)
        uc.mem_map(STUB_BASE, 0x00100000, UC_PROT_READ | UC_PROT_EXEC)
        uc.mem_map(WORK_STRUCT_ADDR, 0x00100000, UC_PROT_READ | UC_PROT_WRITE)
        uc.mem_map(GPU_STATE_ADDR, 0x00100000, UC_PROT_READ | UC_PROT_WRITE)
        uc.mem_map(RODATA_ADDR, 0x00100000, UC_PROT_READ | UC_PROT_WRITE)
        uc.mem_map(DEMON_WORK_ADDR, 0x00100000, UC_PROT_READ | UC_PROT_WRITE)
        # NAME_STR_ADDR is within DEMON_WORK_ADDR (0x02400000..0x02500000)
        uc.mem_map(LAYOUT_BASE, 0x00100000, UC_PROT_READ | UC_PROT_WRITE)
        uc.mem_map(0x04000000, 0x00100000, UC_PROT_READ | UC_PROT_WRITE)
        uc.mem_map(RET_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_EXEC)

        uc.mem_write(RET_ADDR, b'\x00\x00\xa0\xe1')

        for idx, (node_addr, rect_addr) in LAYOUT_NODES.items():
            node_bytes = bytearray(0x20)
            struct.pack_into('<hhI', node_bytes, 8, (idx & 0xF) * 4, (idx & 0xF) * 2, rect_addr)
            uc.mem_write(node_addr, bytes(node_bytes))
            rect_bytes = struct.pack('<hh', 80, 16)
            uc.mem_write(rect_addr, rect_bytes)

        uc.mem_write(NAME_STR_ADDR, b"Pixie\0")
        # Demon work struct: byte at +0x22 = order_num
        dwork = bytearray(0x100)
        dwork[0x22] = 5
        uc.mem_write(DEMON_WORK_ADDR, bytes(dwork))

        uc.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', WORK_STRUCT_ADDR))
        uc.mem_write(GPU_PTR_ADDR, struct.pack('<I', GPU_STATE_ADDR))

        work_data = bytearray(0x4000)
        struct.pack_into('<I', work_data, 0x400, test_ctx.get('state', 3))
        struct.pack_into('<i', work_data, 0x414, test_ctx.get('touch_hold_state', 0))
        struct.pack_into('<III', work_data, 0x418, 0, 0, 0)
        struct.pack_into('<II', work_data, 0x424, 0, 0)
        struct.pack_into('<h', work_data, 0x47E, test_ctx.get('active_sound_id', -1))
        struct.pack_into('<I', work_data, 0x544, test_ctx.get('selected_result', 0))
        struct.pack_into('<B', work_data, 0x548, test_ctx.get('flag_548', 0))
        struct.pack_into('<i', work_data, 0x54C, test_ctx.get('highlighted_slot_index', -1))
        struct.pack_into('<f', work_data, 0xD4, 0.8) # pulse_alpha

        uc.mem_write(WORK_STRUCT_ADDR, bytes(work_data))

        gpu_data = bytearray(0x2000)
        struct.pack_into('<I', gpu_data, 0x130c, 0)
        struct.pack_into('<I', gpu_data, 0x130c + 8, 0)
        struct.pack_into('<B', gpu_data, 0x130c + 0x18, 0)
        struct.pack_into('<I', gpu_data, 0x130c + 0x1C, STUB_BASE + 0x500)
        uc.mem_write(GPU_STATE_ADDR, bytes(gpu_data))

        for sym, addr in STUB_MAP.items():
            if addr >= STUB_BASE:
                uc.mem_write(addr, b'\x1e\xff\x2f\xe1')
        uc.mem_write(STUB_BASE + 0x500, b'\x1e\xff\x2f\xe1')

        for orig_addr in ORIG_ADDR_MAP:
            if orig_addr == 0x002be7fc:
                uc.mem_write(orig_addr, b'\x70\x47\x00\x00')
            else:
                uc.mem_write(orig_addr, b'\x1e\xff\x2f\xe1')

        tracker = CallTracker(test_ctx)
        if mode == 'dec':
            for sym, addr in STUB_MAP.items():
                if addr >= STUB_BASE:
                    uc.hook_add(unicorn.UC_HOOK_CODE, tracker.hook_call, user_data=sym, begin=addr, end=addr)
        else:
            for orig_addr, sym in ORIG_ADDR_MAP.items():
                uc.hook_add(unicorn.UC_HOOK_CODE, tracker.hook_call, user_data=sym, begin=orig_addr, end=orig_addr)

        if rodata_data:
            uc.mem_write(RODATA_ADDR, rodata_data)

        entry_point = 0x0029a520
        uc.mem_write(entry_point, code)
        sp_base = 0x04000000 + 0x80000
        uc.reg_write(UC_ARM_REG_SP, sp_base)
        uc.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc.reg_write(UC_ARM_REG_R0, test_ctx.get('x_offset', 10))
        uc.reg_write(UC_ARM_REG_R1, test_ctx.get('y_offset', 20))
        uc.reg_write(UC_ARM_REG_R2, test_ctx.get('demon_id', 1))
        uc.reg_write(UC_ARM_REG_R3, test_ctx.get('node_id', 0x414))

        # Push stack arguments: scale (float), is_stock_row, is_empty_mode, highlight_mode
        stack_args = struct.pack('<fIII',
                                 test_ctx.get('scale', 1.0),
                                 test_ctx.get('is_stock_row', 0),
                                 test_ctx.get('is_empty_mode', 0),
                                 test_ctx.get('highlight_mode', 0))
        uc.mem_write(sp_base, stack_args)

        try:
            uc.emu_start(entry_point, RET_ADDR, timeout=5000000)
        except Exception as e:
            pc = uc.reg_read(UC_ARM_REG_PC)
            print(f"Exception in mode {mode} at PC={hex(pc)}: {e}")
            raise

        results[mode] = {
            'calls': tracker.calls,
            'work': uc.mem_read(WORK_STRUCT_ADDR, 0x4000),
            'gpu': uc.mem_read(GPU_STATE_ADDR, 0x2000),
        }

    orig_calls = results['orig']['calls']
    dec_calls = results['dec']['calls']
    assert len(orig_calls) == len(dec_calls), f"Call count mismatch: orig={len(orig_calls)} dec={len(dec_calls)}\nOrig:\n{orig_calls}\nDec:\n{dec_calls}"
    for i, (oc, dc) in enumerate(zip(orig_calls, dec_calls)):
        assert oc[0] == dc[0], f"Call {i} function mismatch: orig={oc[0]} dec={dc[0]}"
        assert oc[1] == dc[1], f"Call {i} ({oc[0]}) regs mismatch:\norig={oc[1]}\ndec={dc[1]}"
        assert oc[2] == dc[2], f"Call {i} ({oc[0]}) extra mismatch:\norig={oc[2]}\ndec={dc[2]}"

    assert results['orig']['gpu'] == results['dec']['gpu'], "GPU state mismatch"
    print(f"Test case passed ({len(orig_calls)} calls matched).")

def get_elf_section(path, target_name):
    data = Path(path).read_bytes()
    e_shoff, e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<IIHH", data, 32)[0], struct.unpack_from("<H", data, 46)[0], struct.unpack_from("<H", data, 48)[0], struct.unpack_from("<H", data, 50)[0]
    sections = [struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    for s in sections:
        end = shstrtab.find(b"\x00", s[0])
        name = shstrtab[s[0]:end].decode("ascii", errors="replace")
        if name == target_name or name.startswith(target_name):
            return data[s[4] : s[4] + s[5]]
    return b""

dec_code_bytes, dec_relocs = dec_funcs['StatusDown_DrawPartySlotRow']
rodata = get_elf_section(obj_file, ".rodata")
dec_code = apply_relocs(dec_code_bytes, dec_relocs, 0x0029a520)
orig_code = ORIG_DATA[0x0029a520 - 0x00100000 : 0x0029a520 - 0x00100000 + 1696]

test_cases = [
    {
        'desc': 'Normal active party slot, active_sound_id < 0',
        'demon_id': 10,
        'node_id': 0x414,
        'state': 3,
        'active_sound_id': -1,
        'is_stock_row': 0,
        'is_empty_mode': 0,
        'highlight_mode': 0,
    },
    {
        'desc': 'Empty slot in empty mode (NEW REGISTRATION POSSIBLE!)',
        'demon_id': 0,
        'node_id': 0x415,
        'state': 3,
        'is_stock_row': 0,
        'is_empty_mode': 1,
        'highlight_mode': 0,
    },
    {
        'desc': 'Populated slot in empty mode (shows level)',
        'demon_id': 15,
        'node_id': 0x416,
        'state': 3,
        'is_stock_row': 0,
        'is_empty_mode': 1,
        'highlight_mode': 0,
    },
    {
        'desc': 'Stock row (early return)',
        'demon_id': 20,
        'node_id': 0x417,
        'state': 3,
        'is_stock_row': 1,
        'is_empty_mode': 0,
        'highlight_mode': 0,
    },
    {
        'desc': 'State 11, selected_row == selected_result (green highlight)',
        'demon_id': 12,
        'node_id': 0x414,
        'state': 11,
        'selected_row': 2,
        'selected_result': 2,
        'row_count': 5,
        'is_stock_row': 0,
        'is_empty_mode': 0,
        'highlight_mode': 0,
    },
    {
        'desc': 'State 11, selected_row == row_count - 1 (green highlight)',
        'demon_id': 12,
        'node_id': 0x414,
        'state': 11,
        'selected_row': 4,
        'selected_result': 1,
        'row_count': 5,
        'is_stock_row': 0,
        'is_empty_mode': 0,
        'highlight_mode': 0,
    },
    {
        'desc': 'State 11, other row (gray highlight)',
        'demon_id': 12,
        'node_id': 0x414,
        'state': 11,
        'selected_row': 3,
        'selected_result': 1,
        'row_count': 5,
        'is_stock_row': 0,
        'is_empty_mode': 0,
        'highlight_mode': 0,
    },
    {
        'desc': 'State 3, flag_548, highlighted_slot_index match',
        'demon_id': 14,
        'node_id': 0x414,
        'state': 3,
        'selected_row': 1,
        'flag_548': 1,
        'highlighted_slot_index': 1,
        'is_stock_row': 0,
        'is_empty_mode': 0,
        'highlight_mode': 0,
    },
    {
        'desc': 'Active sound >= 0, main_menu_id = 6 (demon work ptr)',
        'demon_id': 18,
        'node_id': 0x414,
        'state': 3,
        'active_sound_id': 100,
        'main_menu_id': 6,
        'is_stock_row': 0,
        'is_empty_mode': 0,
        'highlight_mode': 0,
    },
    {
        'desc': 'Active sound >= 0, main_menu_id = 1 (active index)',
        'demon_id': 18,
        'node_id': 0x414,
        'state': 3,
        'active_sound_id': 100,
        'main_menu_id': 1,
        'is_stock_row': 0,
        'is_empty_mode': 0,
        'highlight_mode': 0,
    },
]

for tc in test_cases:
    print(f"Running test case: {tc['desc']}")
    run_test_case(tc, orig_code, dec_code, rodata)

print("\nALL StatusDown_DrawPartySlotRow TEST CASES PASSED SUCCESSFULLY!")
