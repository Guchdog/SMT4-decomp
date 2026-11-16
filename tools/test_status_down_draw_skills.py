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
    s32   UiListCursor_GetScrollOffset(const UiListCursor* cursor);
    s32   UiListCursor_GetSelectedRow(const UiListCursor* cursor);
    s32   Camp_GetMainMenuId();
    const u16* Camp_GetSelectedActorPtr();
    bool  Camp_IsActorPlayer(u16 actor);
    void  UiSprite_DrawPanel(s32 prio, u32 group_id, u32 panel_id, s32 x, s32 y, s32 depth);
    // StatusDown_DrawLRPrompts is in include/ui/status_down.h
    const UiLayoutNode* LayoutNode(u32 group_id, u32 node_id);
    void  UiFont_FormatString(char* dst, const char* fmt, ...);
    void  UiFont_DrawText(s32 prio, u32 color, const char* str, f32 x, f32 y, f32 scale, f32 a7, f32 a8);
    const char* Skill_GetNameString(u16 skill_id);
    void  UiSkill_DrawItemIconAndCount(s32 item_id, s32 x, s32 y, s32 prio, s32 a4);
    void  UiSkill_DrawSkillCostAndInfo(u16 skill_id, s32 x, s32 y, s32 prio);
    void  UiSprite_SetGlobalAlpha(f32 alpha);
    void  UiSprite_DrawNode(s32 prio, u32 group_id, u32 node_id, s32 x, s32 y, s32 depth);
    void  UiScissor_SetRect(s32 x, s32 y, s32 w, s32 h, s32 enable);
    s32   UiAnimSprite_GetPosY(const UiAnimSprite* sprite);
    s32   UiAnimSprite_GetPosX(const UiAnimSprite* sprite);
    s32   UiListCursor_GetRowCount(const UiListCursor* cursor);
    void  UiScrollBar_Draw(UiListCursor* cursor, s32 x, s32 y, u32 group_id,
                           s32 up_h, s32 down_h, u32 a6, u32 a7,
                           u32 a8, u32 a9, u32 a10, s32 btn_h,
                           s32 up_h2, s32 down_h2, s32 prio, s32 a15);
    void  GpuModeSlotSet(u32 slot_offset, u32 value);

    void StatusDown_DrawSkillList(s32 x_offset, s32 y_offset);
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

void StatusDown_DrawSkillList(s32 x_offset, s32 y_offset) {
    StatusDownWork* work = g_StatusDownWork;
    UiListCursor* cursor = &work->skill_cursor;
    const s32 scroll_offset = UiListCursor_GetScrollOffset(cursor);
    const s32 selected_row = UiListCursor_GetSelectedRow(cursor);

    bool hide_names = false;
    const s32 menu_id = Camp_GetMainMenuId();
    if (menu_id == 0xD) {
        hide_names = true;
    } else if (menu_id == 6) {
        const u16* actor_ptr = Camp_GetSelectedActorPtr();
        if (!Camp_IsActorPlayer(*actor_ptr)) {
            hide_names = true;
        }
    }

    UiSprite_DrawPanel(2, 0x1A, 5, x_offset, y_offset, 0xB3);
    UiSprite_DrawPanel(2, 0x1A, 0xB, x_offset, y_offset, 0xB5);
    StatusDown_DrawLRPrompts(x_offset, y_offset);

    for (s32 row = 0; row < 11; ++row) {
        const StatusDownListEntry& entry = work->skill_entries[scroll_offset + row];
        if (entry.value == 0) {
            continue;
        }

        const UiLayoutNode* row_node = LayoutNode(0x1A, static_cast<u32>(0x44C + row));
        const UiLayoutNode* name_node = LayoutNode(0x1A, 0x44B);

        if (hide_names) {
            char buf[64];
            UiFont_FormatString(buf, "\\x81\\x48\\x81\\x48\\x81\\x48");
            UiFont_DrawText(2, 0xFF, buf,
                            static_cast<f32>(x_offset + row_node->x + name_node->x),
                            static_cast<f32>(y_offset + row_node->y + name_node->y),
                            0.28f, 0.0f, 1.0f);
        } else {
            const char* sk_name = Skill_GetNameString(entry.value);
            if (sk_name != nullptr) {
                UiFont_DrawText(2, 0xFF, sk_name,
                                static_cast<f32>(x_offset + row_node->x + name_node->x),
                                static_cast<f32>(y_offset + row_node->y + name_node->y),
                                0.28f, 0.0f, 1.0f);
            }
        }

        const UiLayoutNode* icon_node = LayoutNode(0x1A, 0x449);
        const s32 item_id_arg = hide_names ? 0 : static_cast<s16>(entry.id);
        UiSkill_DrawItemIconAndCount(item_id_arg,
                                     x_offset + row_node->x + icon_node->x,
                                     y_offset + row_node->y + icon_node->y,
                                     0xB5, 0);

        const UiLayoutNode* cost_node = LayoutNode(0x1A, 0x44A);
        UiSkill_DrawSkillCostAndInfo(entry.value,
                                     x_offset + row_node->x + cost_node->x,
                                     y_offset + row_node->y + cost_node->y,
                                     0xB5);
    }

    if (work->state == 17) {
        const StatusDownListEntry& sel_entry = work->skill_entries[scroll_offset + selected_row];
        if (sel_entry.value != 0) {
            const UiLayoutNode* sel_node = LayoutNode(0x1A, static_cast<u32>(0x42C + selected_row));
            const f32 pulse_alpha = *reinterpret_cast<const f32*>(&work->panel_sprites[1].raw[0x20]);
            UiSprite_SetGlobalAlpha(pulse_alpha);
            UiSprite_DrawPanel(2, 0x1A, 8, x_offset + sel_node->x, y_offset + sel_node->y, 0xBF);

            UiSprite_SetGlobalAlpha(1.0f);
            UiSprite_DrawNode(2, 0x1A, 0x41F, x_offset + sel_node->x, y_offset + sel_node->y, 0xC4);

            u32 cursor_frame_node = 0x420;
            if (work->touch_drag_state[0] == 0 && work->touch_drag_state[1] == 0 &&
                work->touch_drag_state[2] == 0 && work->lr_state_left == 0 &&
                work->lr_state_right == 0 && work->touch_hold_state >= 0) {
                cursor_frame_node = 0x421;
            }
            UiSprite_DrawNode(2, 0x1A, cursor_frame_node, x_offset + sel_node->x, y_offset + sel_node->y, 0xC4);
            UiSprite_DrawNode(2, 0x1A, 0x457, x_offset + sel_node->x, y_offset + sel_node->y, 0xC4);

            const UiLayoutNode* clip_node = LayoutNode(0x1A, 0x420);
            GpuModeSlotSet(0x30C, 3);
            UiScissor_SetRect(x_offset + sel_node->x + clip_node->x,
                              y_offset + sel_node->y + clip_node->y,
                              clip_node->rect->w, clip_node->rect->h, 1);

            const s32 anim_y = UiAnimSprite_GetPosY(&work->panel_sprites[3]);
            const s32 anim_x = UiAnimSprite_GetPosX(&work->panel_sprites[3]);
            UiSprite_DrawNode(2, 0x1A, 0x422,
                              x_offset + anim_x + sel_node->x,
                              y_offset + anim_y + sel_node->y, 0xC9);

            GpuModeSlotSet(0x30C, 0);

            const UiLayoutNode* icon_node = LayoutNode(0x1A, 0x458);
            const s32 item_id_arg = hide_names ? 0 : static_cast<s16>(sel_entry.id);
            UiSkill_DrawItemIconAndCount(item_id_arg,
                                         x_offset + sel_node->x + icon_node->x,
                                         y_offset + sel_node->y + icon_node->y,
                                         0xC9, 0);

            const UiLayoutNode* cost_node = LayoutNode(0x1A, 0x459);
            UiSkill_DrawSkillCostAndInfo(sel_entry.value,
                                         x_offset + sel_node->x + cost_node->x,
                                         y_offset + sel_node->y + cost_node->y,
                                         0xC9);
        }
    }

    if (UiListCursor_GetRowCount(cursor) <= 0) {
        UiSprite_DrawPanel(2, 0x1A, 0x1B, x_offset, y_offset, 0xDD);
    }

    UiScrollBar_Draw(cursor, x_offset, y_offset, 0x1A,
                     0x405, 0x406, 0x403, 0x400,
                     0x403, 0x403, 0x403, work->btn_touch_handle,
                     work->scroll_up_touch_handle, work->scroll_down_touch_handle,
                     0xC4, 0);
}
"""

build_dir = Path("build/test_status_down_draw_skills")
build_dir.mkdir(parents=True, exist_ok=True)
src_file = build_dir / "test.cpp"
obj_file = build_dir / "test.o"
src_file.write_text(test_cpp, encoding="utf-8")

res = compile_tu_armv6k(src_file, obj_file, repo_root=Path('.'))
assert res.returncode == 0, f"Compilation failed: {res.stderr}"
dec_funcs = extract_elf_functions_detailed(obj_file)
print("Compiled StatusDown_DrawSkillList test successfully.")

STUB_BASE = 0x02000000
RET_ADDR = 0x03000000
GLOBAL_PTR_ADDR = 0x0044E190
GPU_PTR_ADDR = 0x0044EA00
WORK_STRUCT_ADDR = 0x02100000
GPU_STATE_ADDR = 0x02200000
RODATA_ADDR = 0x02300000
ACTOR_PTR_ADDR = 0x02400000
NAME_STR_ADDR = 0x02410000

LAYOUT_NODES = {}
LAYOUT_BASE = 0x02500000
RECT_BASE = 0x02580000

# Prepare layout node pointers
for idx in range(0x400, 0x470):
    node_addr = LAYOUT_BASE + (idx - 0x400) * 0x20
    rect_addr = RECT_BASE + (idx - 0x400) * 0x10
    LAYOUT_NODES[idx] = (node_addr, rect_addr)

STUB_MAP = {
    'UiListCursor_GetScrollOffset': STUB_BASE + 0x00,
    'UiListCursor_GetSelectedRow': STUB_BASE + 0x10,
    'Camp_GetMainMenuId': STUB_BASE + 0x20,
    'Camp_GetSelectedActorPtr': STUB_BASE + 0x30,
    'Camp_IsActorPlayer': STUB_BASE + 0x40,
    'UiSprite_DrawPanel': STUB_BASE + 0x50,
    '_ZN4smt42ui24StatusDown_DrawLRPromptsEii': STUB_BASE + 0x60,
    'LayoutNode': STUB_BASE + 0x70,
    'UiFont_FormatString': STUB_BASE + 0x80,
    'UiFont_DrawText': STUB_BASE + 0x90,
    'Skill_GetNameString': STUB_BASE + 0xA0,
    'UiSkill_DrawItemIconAndCount': STUB_BASE + 0xB0,
    'UiSkill_DrawSkillCostAndInfo': STUB_BASE + 0xC0,
    'UiSprite_SetGlobalAlpha': STUB_BASE + 0xD0,
    'UiSprite_DrawNode': STUB_BASE + 0xE0,
    'UiScissor_SetRect': STUB_BASE + 0xF0,
    'UiAnimSprite_GetPosY': STUB_BASE + 0x100,
    'UiAnimSprite_GetPosX': STUB_BASE + 0x110,
    'UiListCursor_GetRowCount': STUB_BASE + 0x120,
    'UiScrollBar_Draw': STUB_BASE + 0x130,
    '_ZN4smt42ui16g_StatusDownWorkE': GLOBAL_PTR_ADDR,
    'g_AsdGpuState': GPU_PTR_ADDR,
    '': RODATA_ADDR,
}

ORIG_ADDR_MAP = {
    0x0029f260: 'UiListCursor_GetScrollOffset',
    0x0029f248: 'UiListCursor_GetSelectedRow',
    0x0029af30: 'Camp_GetMainMenuId',
    0x0029af4c: 'Camp_GetSelectedActorPtr',
    0x0029ec6c: 'Camp_IsActorPlayer',
    0x002bf558: 'UiSprite_DrawPanel',
    0x0029adf0: 'StatusDown_DrawLRPrompts',
    0x002bf6d0: 'LayoutNode',
    0x002be7fc: 'UiFont_FormatString',
    0x002be77c: 'UiFont_DrawText',
    0x0026ad50: 'Skill_GetNameString',
    0x002b6a98: 'UiSkill_DrawItemIconAndCount',
    0x002e1e60: 'UiSkill_DrawSkillCostAndInfo',
    0x002bf710: 'UiSprite_SetGlobalAlpha',
    0x002bf460: 'UiSprite_DrawNode',
    0x0029a418: 'UiScissor_SetRect',
    0x002bef70: 'UiAnimSprite_GetPosY',
    0x002bef7c: 'UiAnimSprite_GetPosX',
    0x0029f0f4: 'UiListCursor_GetRowCount',
    0x00290c38: 'UiScrollBar_Draw',
}

def apply_relocs(code_bytes, relocs, target_addr, rodata_data):
    mutable = bytearray(code_bytes)
    for rel in relocs:
        offset = rel.offset
        name = rel.symbol_name
        rel_type = rel.relocation_type
        if name == '':
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

ARITY = {
    'UiListCursor_GetScrollOffset': 1,
    'UiListCursor_GetSelectedRow': 1,
    'Camp_GetMainMenuId': 0,
    'Camp_GetSelectedActorPtr': 0,
    'Camp_IsActorPlayer': 1,
    'UiSprite_DrawPanel': 4,
    'StatusDown_DrawLRPrompts': 2,
    'LayoutNode': 2,
    'UiFont_FormatString': 2,
    'UiFont_DrawText': 3,
    'Skill_GetNameString': 1,
    'UiSkill_DrawItemIconAndCount': 4,
    'UiSkill_DrawSkillCostAndInfo': 4,
    'UiSprite_SetGlobalAlpha': 0,
    'UiSprite_DrawNode': 4,
    'UiScissor_SetRect': 4,
    'UiAnimSprite_GetPosY': 1,
    'UiAnimSprite_GetPosX': 1,
    'UiListCursor_GetRowCount': 1,
    'UiScrollBar_Draw': 4,
}

class CallTracker:
    def __init__(self, test_ctx):
        self.calls = []
        self.ctx = test_ctx
        
    def hook_call(self, uc, address, size, user_data):
        if user_data == '_ZN4smt42ui24StatusDown_DrawLRPromptsEii':
            user_data = 'StatusDown_DrawLRPrompts'
        arity = ARITY.get(user_data, 4)
        raw_regs = [
            hex(uc.reg_read(UC_ARM_REG_R0)),
            hex(uc.reg_read(UC_ARM_REG_R1)),
            hex(uc.reg_read(UC_ARM_REG_R2)),
            hex(uc.reg_read(UC_ARM_REG_R3)),
        ]
        
        # Normalize stack addresses and string pointers
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
        
        # Read float registers or stack if needed
        extra = []
        if user_data == 'UiFont_DrawText':
            s0 = uc.reg_read(UC_ARM_REG_D0) & 0xFFFFFFFF
            s1 = (uc.reg_read(UC_ARM_REG_D0) >> 32) & 0xFFFFFFFF
            s2 = uc.reg_read(UC_ARM_REG_D1) & 0xFFFFFFFF
            s3 = (uc.reg_read(UC_ARM_REG_D1) >> 32) & 0xFFFFFFFF
            s4 = uc.reg_read(UC_ARM_REG_D2) & 0xFFFFFFFF
            f0 = struct.unpack('<f', struct.pack('<I', s0))[0]
            f1 = struct.unpack('<f', struct.pack('<I', s1))[0]
            f2 = struct.unpack('<f', struct.pack('<I', s2))[0]
            # string at r2
            str_bytes = uc.mem_read(int(raw_regs[2], 16), 16)
            s_val = str_bytes.split(b'\0')[0].decode('latin1', errors='replace')
            extra = [f"x={f0:.1f}", f"y={f1:.1f}", f"scale={f2:.2f}", f"str='{s_val}'"]
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

        self.calls.append((user_data, tuple(regs), tuple(extra)))
        
        # Stubs behavior:
        if user_data == 'UiListCursor_GetScrollOffset':
            uc.reg_write(UC_ARM_REG_R0, self.ctx.get('scroll_offset', 0))
        elif user_data == 'UiListCursor_GetSelectedRow':
            uc.reg_write(UC_ARM_REG_R0, self.ctx.get('selected_row', 0))
        elif user_data == 'Camp_GetMainMenuId':
            uc.reg_write(UC_ARM_REG_R0, self.ctx.get('main_menu_id', 1))
        elif user_data == 'Camp_GetSelectedActorPtr':
            uc.reg_write(UC_ARM_REG_R0, ACTOR_PTR_ADDR)
        elif user_data == 'Camp_IsActorPlayer':
            uc.reg_write(UC_ARM_REG_R0, 1 if self.ctx.get('is_player', True) else 0)
        elif user_data == 'LayoutNode':
            node_id = uc.reg_read(UC_ARM_REG_R1)
            node_addr, _ = LAYOUT_NODES.get(node_id, (0, 0))
            uc.reg_write(UC_ARM_REG_R0, node_addr)
        elif user_data == 'UiFont_FormatString':
            dst = uc.reg_read(UC_ARM_REG_R0)
            src = uc.reg_read(UC_ARM_REG_R1)
            s_bytes = uc.mem_read(src, 16)
            uc.mem_write(dst, bytes(s_bytes))
        elif user_data == 'Skill_GetNameString':
            uc.reg_write(UC_ARM_REG_R0, NAME_STR_ADDR)
        elif user_data == 'UiAnimSprite_GetPosX':
            uc.reg_write(UC_ARM_REG_R0, 15)
        elif user_data == 'UiAnimSprite_GetPosY':
            uc.reg_write(UC_ARM_REG_R0, 25)
        elif user_data == 'UiListCursor_GetRowCount':
            uc.reg_write(UC_ARM_REG_R0, self.ctx.get('row_count', 10))

def run_test_case(test_ctx, orig_code, dec_code, rodata_data):
    results = {}
    for mode, code in [('orig', orig_code), ('dec', dec_code)]:
        uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        # Enable VFP
        uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
        uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
        uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

        # Map memory
        uc.mem_map(0x00100000, 0x00300000, UC_PROT_READ | UC_PROT_EXEC) # orig code space
        uc.mem_map(0x00400000, 0x00100000, UC_PROT_READ | UC_PROT_WRITE) # globals space
        uc.mem_map(STUB_BASE, 0x00100000, UC_PROT_READ | UC_PROT_EXEC)
        uc.mem_map(WORK_STRUCT_ADDR, 0x00100000, UC_PROT_READ | UC_PROT_WRITE) # work
        uc.mem_map(GPU_STATE_ADDR, 0x00100000, UC_PROT_READ | UC_PROT_WRITE) # gpu state
        uc.mem_map(RODATA_ADDR, 0x00100000, UC_PROT_READ | UC_PROT_WRITE) # rodata
        uc.mem_map(ACTOR_PTR_ADDR, 0x00100000, UC_PROT_READ | UC_PROT_WRITE) # actor / names
        uc.mem_map(LAYOUT_BASE, 0x00100000, UC_PROT_READ | UC_PROT_WRITE) # layout nodes
        uc.mem_map(0x04000000, 0x00100000, UC_PROT_READ | UC_PROT_WRITE) # stack
        uc.mem_map(RET_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_EXEC)

        # Write return hook
        uc.mem_write(RET_ADDR, b'\x00\x00\xa0\xe1') # nop

        # Setup layout nodes
        for idx in range(0x400, 0x470):
            node_addr, rect_addr = LAYOUT_NODES[idx]
            # UiLayoutNode: unk_00[8], s16 x, s16 y, rect*
            node_bytes = bytearray(0x20)
            struct.pack_into('<hhI', node_bytes, 8, (idx & 0xF) * 5, (idx & 0xF) * 3, rect_addr)
            uc.mem_write(node_addr, bytes(node_bytes))
            # UiLayoutRect: s16 w, s16 h
            rect_bytes = struct.pack('<hh', 100, 20)
            uc.mem_write(rect_addr, rect_bytes)

        # Setup name string and actor
        uc.mem_write(NAME_STR_ADDR, b"Agi\0")
        uc.mem_write(ACTOR_PTR_ADDR, struct.pack('<H', 1))

        # Setup globals
        uc.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', WORK_STRUCT_ADDR))
        uc.mem_write(GPU_PTR_ADDR, struct.pack('<I', GPU_STATE_ADDR))

        # Setup work struct
        work_data = bytearray(0x4000)
        # state at +0x400
        struct.pack_into('<I', work_data, 0x400, test_ctx.get('state', 17))
        # touch states
        struct.pack_into('<i', work_data, 0x414, test_ctx.get('touch_hold_state', 0))
        struct.pack_into('<III', work_data, 0x418, 0, 0, 0) # drag state
        struct.pack_into('<II', work_data, 0x424, 0, 0) # lr state
        # touch handles
        struct.pack_into('<h', work_data, 0x474, 50) # btn
        struct.pack_into('<h', work_data, 0x476, 51) # up
        struct.pack_into('<h', work_data, 0x478, 52) # down
        # pulse alpha in panel_sprites[1] (+0x28 + 0x8C = 0xB4) + 0x20 = 0xD4
        struct.pack_into('<f', work_data, 0xD4, 0.75)
        # skill_entries at work + 0x500 + scroll_offset*4
        # StatusDownListEntry is { s16 id; u16 value; }
        for i, (sk_id, sk_val) in enumerate(test_ctx.get('skills', [])):
            struct.pack_into('<HH', work_data, 0x5C8 + i * 4, sk_id, sk_val)

        uc.mem_write(WORK_STRUCT_ADDR, bytes(work_data))

        # Setup GPU state at 0x02200000:
        # slot at +0x130c
        gpu_data = bytearray(0x2000)
        # index = 0 at slot
        struct.pack_into('<I', gpu_data, 0x130c, 0)
        # old val at slot + 8 = 0
        struct.pack_into('<I', gpu_data, 0x130c + 8, 0)
        # slot + 0x18 = 0
        struct.pack_into('<B', gpu_data, 0x130c + 0x18, 0)
        # callback at slot + 0x1C
        struct.pack_into('<I', gpu_data, 0x130c + 0x1C, STUB_BASE + 0x500)
        uc.mem_write(GPU_STATE_ADDR, bytes(gpu_data))

        # Write stubs: bx lr for each
        for sym, addr in STUB_MAP.items():
            if addr >= STUB_BASE:
                uc.mem_write(addr, b'\x1e\xff\x2f\xe1') # bx lr
        uc.mem_write(STUB_BASE + 0x500, b'\x1e\xff\x2f\xe1')

        # Also write bx lr for orig addresses so bl returns immediately
        for orig_addr in ORIG_ADDR_MAP:
            if orig_addr == 0x002be7fc: # Thumb function!
                uc.mem_write(orig_addr, b'\x70\x47\x00\x00') # bx lr (thumb)
            else:
                uc.mem_write(orig_addr, b'\x1e\xff\x2f\xe1') # bx lr (arm)

        # Hook calls
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

        # Load code and run
        entry_point = 0x0032be34
        uc.mem_write(entry_point, code)
        uc.reg_write(UC_ARM_REG_SP, 0x04000000 + 0x80000)
        uc.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc.reg_write(UC_ARM_REG_R0, test_ctx.get('x_offset', 10))
        uc.reg_write(UC_ARM_REG_R1, test_ctx.get('y_offset', 20))

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

    # Compare calls
    orig_calls = results['orig']['calls']
    dec_calls = results['dec']['calls']
    assert len(orig_calls) == len(dec_calls), f"Call count mismatch: orig={len(orig_calls)} dec={len(dec_calls)}\nOrig:\n{orig_calls}\nDec:\n{dec_calls}"
    for i, (oc, dc) in enumerate(zip(orig_calls, dec_calls)):
        assert oc[0] == dc[0], f"Call {i} function mismatch: orig={oc[0]} dec={dc[0]}"
        assert oc[1] == dc[1], f"Call {i} ({oc[0]}) regs mismatch:\norig={oc[1]}\ndec={dc[1]}"
        assert oc[2] == dc[2], f"Call {i} ({oc[0]}) extra mismatch:\norig={oc[2]}\ndec={dc[2]}"

    # Compare GPU state
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

# Extract dec code
dec_code_bytes, dec_relocs = dec_funcs['StatusDown_DrawSkillList']
rodata = get_elf_section(obj_file, ".rodata")
dec_code = apply_relocs(dec_code_bytes, dec_relocs, 0x0032be34, rodata)
orig_code = ORIG_DATA[0x0032be34 - 0x00100000 : 0x0032be34 - 0x00100000 + 1672]

test_cases = [
    {
        'desc': 'State 17, player, 3 skills, touch hold >= 0',
        'state': 17,
        'main_menu_id': 1,
        'is_player': True,
        'scroll_offset': 0,
        'selected_row': 1,
        'row_count': 3,
        'touch_hold_state': 1,
        'skills': [(0x101, 12), (0x102, 15), (0x103, 0)],
    },
    {
        'desc': 'State 17, hide_names (menu 0xD), 5 skills, touch hold -1',
        'state': 17,
        'main_menu_id': 0xD,
        'is_player': True,
        'scroll_offset': 0,
        'selected_row': 0,
        'row_count': 5,
        'touch_hold_state': -1,
        'skills': [(0x101, 12), (0x102, 15), (0x103, 20), (0x104, 30), (0x105, 40)],
    },
    {
        'desc': 'State 17, demon in menu 6 (hide_names), 0 row_count (empty panel)',
        'state': 17,
        'main_menu_id': 6,
        'is_player': False,
        'scroll_offset': 0,
        'selected_row': 0,
        'row_count': 0,
        'touch_hold_state': 0,
        'skills': [],
    },
    {
        'desc': 'State 18 (no selection highlight), player, 8 skills',
        'state': 18,
        'main_menu_id': 1,
        'is_player': True,
        'scroll_offset': 2,
        'selected_row': 3,
        'row_count': 8,
        'touch_hold_state': 0,
        'skills': [(0x100 + i, 10 + i) for i in range(15)],
    },
]

for tc in test_cases:
    print(f"Running test case: {tc['desc']}")
    run_test_case(tc, orig_code, dec_code, rodata)

print("\nALL StatusDown_DrawSkillList TEST CASES PASSED SUCCESSFULLY!")
