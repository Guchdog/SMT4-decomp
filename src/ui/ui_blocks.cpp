#include "ui/ui_blocks.h"
#include "engine/asd_symbols.h"
#include "engine/asd_text.h"
#include "engine/runtime_blocks.h"
#include <cstring>

namespace smt4::ui {

// ---------------------------------------------------------------------------
// Reproduced .data / .rodata
// ---------------------------------------------------------------------------

// 0x00409B60: five 16-byte palette rows.  The next rodata object (the
// `c:\SMT4\...` source path) starts at 0x00409BB0.
const DebugPalette g_DebugPalette[5] = {
    {{0x101010FFu, 0x808080FFu, 0x208020FFu, 0x000080FFu}},
    {{0x202020A8u, 0x80808080u, 0x80808060u, 0x101010C0u}},
    {{0x400000A8u, 0xC0000080u, 0x54000060u, 0x300000C0u}},
    {{0x004000A8u, 0x00C00080u, 0x00E30040u, 0x003000C0u}},
    {{0x000040A8u, 0x0000C080u, 0x00E34A60u, 0x000030C0u}},
};

// 0x0043DC2C: eight icon ids consumed by the state-3/4 icon rows.
const u8 g_BattleCommandIcons[8] = {1, 2, 0, 0, 1, 2, 0, 0};

// ---------------------------------------------------------------------------
// Shared ABI declarations.  Canonical spellings from engine/asd_symbols.h are
// reused for the GPU/viewport, layout and string helpers.
// ---------------------------------------------------------------------------

extern "C" {
    extern u8* g_AsdGpuState;                   // 0x0044EA00 (ui_runtime.cpp)

    void* AsdRef_Get(void* handle);             // 0x002C0AC8
    void  UiGpu_BeginPass(void* gpu_state);     // 0x002C3BA8
    void  Ui_DrawModel(void* gpu_state, void* model); // 0x002C1D3C
    void  UiGpu_EndPass1(void* gpu_state);      // 0x002C1B64
    void  UiGpu_EndPass2(void* gpu_state);      // 0x002C1ABC

    s32   UiInput_Trigger(u32 id);              // 0x002B902C
    s32   UiInput_Trigger2(u32 id);             // 0x002BFFBC
    s32   UiInput_Trigger3(u32 id);             // 0x002C17D4

    void  UiFont_FormatString(char* dst, const char* fmt, ...); // 0x002BE7FC

    void  UiSprite_DrawNode(u32 screen, u32 group, u32 node,
                            s32 x, s32 y, s32 prio);   // 0x002BF460
    void  UiSprite_DrawPanel(u32 screen, u32 group, u32 panel,
                             s32 x, s32 y, s32 prio);  // 0x002BF558
    void  UiSprite_SetGlobalAlpha(f32 alpha);          // 0x002BF710

    // 0x0027FBC8 (216 B): analog-stick axes; returns 0 when the stick is
    // centred.
    s32   script_vm_func_0027fbc8(f32* out_x, f32* out_y, s32 mode);
    // 0x002B7A10 (152 B): four-colour quad.  The four pointers select the
    // per-corner RGBA tables (ARGB float quadruplets).
    void  func_002b7a10(const void* c0, const void* c1, const void* c2,
                        const void* c3, f32 x, f32 y, f32 z, f32 w,
                        f32 alpha);
    // 0x002AEFC8 (152 B): text draw at (x,y) with font id.
    void  engine_func_002aefc8(s32 font, const char* text, f32 x, f32 y);

    // 0x001FF3C4 (1,104 B): list cursor update, returns 0..4.
    s32   camp_func_001ff3c4(void* list_state);
    // 0x00254FF0 (76 B): list-box item lookup.  The return type matches the
    // declaration in src/engine/asd_text.cpp.
    AsdListBoxItem* AsdListBox_FindItem(void* handle, u32 id);

    // 0x0026E910 (108 B): clamped scroll position.
    s32   ui_func_0026e910(s32 a, s32 b, s32 span, s32 offset, s32 reverse);
    // 0x0026E97C (72 B): clamped float interpolation.
    f32   ui_func_0026e97c(f32 a, f32 b, f32 span, f32 t);
    // 0x0024807C (116 B): stepped/quantised float interpolation.
    f32   ui_func_0024807c(f32 a, f32 b, f32 span, f32 t);

    // 0x00247DE4 (664 B): command icon row.
    void  ui_func_00247de4(BattleCommandWork* work, s32 row);
    // 0x002594F0 (32 B): text layout with default flags/selection; returns
    // the measured width.
    f32   script_vm_func_002594f0(void* text_handle);
    // 0x002B09B8 (3,032 B): text layout renderer; returns the laid-out width.
    f32   engine_func_002b09b8(void* text_handle, u32 flags, s32 selected,
                               f32 x, f32 y, f32 scale, f32 alpha);
    // 0x002B0908 (176 B): gradient/bar draw.  The four trailing words are the
    // four stack arguments consumed verbatim by the callee.
    void  func_002b0908(s32 screen, s32 group, s32 panel, s32 x,
                        u32 w0, u32 w1, u32 w2, u32 w3);
}

namespace {

// 0x41000000 / 0x43A00000 / 0x3F730000 / 0x3B808081 / 0x3C23D70A /
// 0x3ECCCCCD literal-pool values.
constexpr f32 kPanelSpan = 8.0f;
constexpr f32 kScreenWidth = 320.0f;
constexpr f32 kIconScale = 0.94921875f;
constexpr f32 kInv255 = 0.003921569f;
constexpr f32 kGaugeScale = 0.01f;
constexpr f32 kIconAlpha = 0.4f;
constexpr f32 kTwo = 2.0f;
constexpr f32 kFour = 4.0f;
constexpr f32 kHalf = 0.5f;
constexpr f32 kOne = 1.0f;

// 0x001FE590 packs an ARGB dword into the {A,R,G,B} float quadruplet consumed
// by 0x002B7A10: `lsr r1,r0,#0x18` -> [sp], `and/>>16` -> [sp+4],
// `and/>>8` -> [sp+8], `and #0xff` -> [sp+0xC] (0x001FE6F0..0x001FE75C).
void ArgbToFloat4(u32 argb, f32 out[4]) {
    out[0] = static_cast<f32>((argb >> 24) & 0xFFu) * kInv255;
    out[1] = static_cast<f32>((argb >> 16) & 0xFFu) * kInv255;
    out[2] = static_cast<f32>((argb >> 8) & 0xFFu) * kInv255;
    out[3] = static_cast<f32>(argb & 0xFFu) * kInv255;
}

// 0x001FEC40 / 0x001FEDD4 convert the float member to double for "%4.2f".
inline double AsDouble(f32 value) {
    return static_cast<double>(value);
}

// The repeat-speed ladder at 0x001FEF80..0x001FEFB8 (and repeats):
// repeat 1..5 -> 10, 100, 1000, 10000, 100000; otherwise 1.
s32 StepForRepeat(s32 repeat) {
    switch (repeat) {
    case 1: return 10;
    case 2: return 100;
    case 3: return 1000;
    case 4: return 10000;
    case 5: return 100000;
    default: return 1;
    }
}

// 0x001FEEE4..0x001FEF28 and 0x001FF250..0x001FF298: resolve the entry that
// belongs to the item whose id is (hud->scroll + hud->first_id).  The listing
// resolves the scene handle twice: once for the cursor pair and once for the
// list head.
DebugValueEntry* FindEntryAtCursor(void* scene) {
    DebugHudWork* cursor =
        static_cast<DebugHudWork*>(AsdRef_Get(scene));   // 0x001FEEDC
    const u32 wanted =
        static_cast<u32>(cursor->scroll + cursor->first_id);
    DebugHudWork* list_work =
        static_cast<DebugHudWork*>(AsdRef_Get(scene));   // 0x001FEEF0
    u32 entry_id = 0xFFFFFFFFu;                 // `mvn sl,#0` (0x001FEA40)
    for (DebugListNode* node = list_work->list; node != nullptr;
         node = node->next) {
        if (node->id == wanted) {
            entry_id = *reinterpret_cast<u32*>(node->entry);
            break;
        }
    }
    return reinterpret_cast<DebugValueEntry*>(
        AsdListBox_FindItem(scene, entry_id));
}

// ---------------------------------------------------------------------------
// UI render-state stack at GPU+0x124C and GPU+0x12AC.
//
// The count is at +0x00, the value slots begin at +0x08 (`r3 = r4 + count*4;
// [r3+8]`), the dirty byte at +0x18 and the flush callback at +0x1C.
// ---------------------------------------------------------------------------

struct UiRenderStack {
    s32 count;                          // +0x00: `ldr r1,[r4]` (0x002ED60C)
    u8  pad_004[0x14];
    u8  dirty;                          // +0x18: `ldrb r2,[r4,#0x18]`
                                        //   (0x002ED628)
    u8  pad_019[3];
    void (*flush)(u32 value);           // +0x1C: `ldr r1,[r4,#0x1c]`
                                        //   (0x002ED638)
};
static_assert(offsetof(UiRenderStack, count) == 0x00);
static_assert(offsetof(UiRenderStack, dirty) == 0x18);
static_assert(offsetof(UiRenderStack, flush) == 0x1C);

inline u32* StackSlot(UiRenderStack* stack, s32 index) {
    return reinterpret_cast<u32*>(reinterpret_cast<u8*>(stack) + 8) + index;
}

// 0x002ED60C..0x002ED640 and repeats.
void PushRenderState(UiRenderStack* stack, u32 value) {
    const s32 count = stack->count;
    const u32 previous = *StackSlot(stack, count);
    stack->count = count + 1;
    *StackSlot(stack, count + 1) = value;
    if (stack->dirty == 0 && previous == value) {
        return;
    }
    stack->flush(value);
    stack->dirty = 0;
}

// 0x002EE330..0x002EE370.
void PopRenderState(UiRenderStack* stack) {
    const s32 count = stack->count;
    const u32 previous = *StackSlot(stack, count);
    stack->count = count - 1;
    const u32 current = *StackSlot(stack, stack->count);
    if (stack->dirty == 0 && previous == current) {
        return;
    }
    stack->flush(current);
    stack->dirty = 0;
}

} // namespace

// ---------------------------------------------------------------------------
// 0x001FE590: debug value list.
//
// The routine is a small state machine (HUD+0x34) driving a scrollable editor:
//   state 0 -> 1 -> 2 (when enabled) -> 3 (running)
//   state 4 = idle, state 5 = shutdown (-1)
// While running it draws the panel (palette rows at 0x00409B60), walks the
// linked list of value nodes, and edits the selected entry through the four
// input triggers.  Every format string below is in the function's rodata:
// "_%s", "_FALSE", "  TRUE", " FALSE", "0x%08X", " %8d", " %4.2f", " %s".
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001fe590, 3608)
s32 ui_func_001fe590(void* scene) {
    DebugHudWork* hud = static_cast<DebugHudWork*>(AsdRef_Get(scene));
    s32 repeat = 0;                                 // r6

    // 0x001FE5B0..0x001FE5B4: six-entry jump table at 0x001FE5BC.
    switch (hud->state) {
    case 0:
        hud->state = 1;                             // 0x001FE5D4
        [[fallthrough]];
    case 1:
        if (hud->enabled != 0) {
            hud->state = 2;                         // 0x001FE5EC
        }
        break;
    case 2:
        hud->state = 3;                             // 0x001FE5F8
        break;
    case 3:
        break;
    case 4:
        break;
    case 5:
        return -1;                                  // 0x001FF398
    default:
        break;
    }

    if (hud->state != 3 || hud->enabled == 0 || hud->active == 0) {
        // 0x001FF370 tail.
        if (hud->frame_cb != nullptr && hud->state > 2) {
            hud->frame_cb(hud->frame_arg);          // 0x001FF384
        }
        return 0;
    }

    // ---- 0x001FE5FC..0x001FE61C: repeat speed (triggers 7 and 8) ----------
    if (UiInput_Trigger3(7) != 0) {
        repeat = 1;
    } else if (UiInput_Trigger3(8) != 0) {
        repeat = 2;
    }

    // ---- 0x001FE634..0x001FE6B0: analog-stick panel scroll --------------
    if ((hud->flags & 4u) != 0) {
        f32 axis_x = 0.0f;
        f32 axis_y = 0.0f;
        if (script_vm_func_0027fbc8(&axis_x, &axis_y, 0) != 0) {
            if (axis_x < -0.5f) {
                hud->x -= kTwo;                     // 0x001FE66C
            } else if (axis_x > 0.5f) {
                hud->x += kTwo;                     // 0x001FE67C
            }
            if (axis_y < -0.5f) {
                hud->y += kTwo;                     // 0x001FE694
            } else if (axis_y > 0.5f) {
                hud->y -= kTwo;                     // 0x001FE6A4
            }
        }
    }

    // ---- 0x001FE6C8..0x001FE934: panel background and border -------------
    Ui_DrawModel(g_AsdGpuState, nullptr);

    const DebugPalette& palette = g_DebugPalette[hud->palette];
    f32 color[4];
    ArgbToFloat4(palette.color[0], color);
    func_002b7a10(color, color, color, color,
                  hud->x, hud->y, hud->width, hud->height, 0.0f);

    // 0x001FE760..0x001FE7F4: inner top strip; uses palette entry +0x0C and
    // the line height at +0x5C as its depth.
    ArgbToFloat4(palette.color[3], color);
    func_002b7a10(color, color, color, color,
                  hud->x + kTwo, hud->y + kTwo, hud->width - kFour,
                  static_cast<f32>(hud->line_height), 0.0f);

    // 0x001FE7F8..0x001FE888: top border (palette entry +0x04).
    ArgbToFloat4(palette.color[1], color);
    func_002b7a10(color, color, color, color,
                  hud->x, hud->y, hud->width, kOne, 0.0f);

    // 0x001FE88C..0x001FE8B8: bottom border.
    func_002b7a10(color, color, color, color,
                  hud->x, hud->y + hud->height - kOne, hud->width, kOne, 0.0f);

    // 0x001FE8BC..0x001FE8EC: left border.
    func_002b7a10(color, color, color, color,
                  hud->x, hud->y, kOne, hud->height, 0.0f);

    // 0x001FE8F0..0x001FE91C: right border.
    func_002b7a10(color, color, color, color,
                  hud->x + hud->width - kOne, hud->y, kOne, hud->height, 0.0f);

    // 0x001FE920..0x001FE934: panel title buffer at HUD+0x8C.
    engine_func_002aefc8(0, hud->text, hud->x + kTwo, hud->y + kTwo);

    // ---- 0x001FE938..0x001FEA38: selected-row highlight ------------------
    // Skipped when bit 0 of HUD+0x38 is set (`tst r0,#1; bne 0x1FEA3C`).
    if ((hud->flags & 1u) == 0) {
        Ui_DrawModel(g_AsdGpuState, nullptr);

        ArgbToFloat4(palette.color[2], color);
        const f32 row_y = hud->y + kTwo
                        + static_cast<f32>(hud->line_height)
                        + static_cast<f32>(hud->scroll * hud->line_height);
        func_002b7a10(color, color, color, color,
                      hud->x + kTwo, row_y, hud->width - kFour,
                      static_cast<f32>(hud->line_height), 0.0f);
    }

    // ---- 0x001FEA3C..0x001FEE1C: value list ------------------------------
    // Cursor starts at (x+2, y+2+line_height).  `callback_y` mirrors the
    // second pointer handed to HUD+0x7C (sp+0x10C, initialised to -1.0f).
    f32 cursor_x = hud->x + kTwo;
    f32 cursor_y = hud->y + kTwo + static_cast<f32>(hud->line_height);
    f32 callback_y = -1.0f;
    char buffer[0x100];

    for (DebugListNode* node = hud->list; node != nullptr; node = node->next) {
        const u32 id = node->id;
        if (hud->first_id > static_cast<s32>(id)) {
            continue;                               // 0x001FEA84
        }
        if (static_cast<s32>(id) > hud->first_id + hud->visible_count - 1) {
            break;                                  // 0x001FEA9C
        }

        DebugValueEntry* entry = node->entry;
        if (hud->draw_text_cb != nullptr) {
            // 0x001FEABC: draw/measure the label through the HUD callback.
            hud->draw_text_cb(&cursor_x, &callback_y, entry->label);

            switch (entry->type) {
            case 0:
                break;                              // 0x001FEDF8
            case 1:
                // 0x001FEAE4..0x001FEB44: "_%s" from entry->text.
                UiFont_FormatString(buffer, "_%s", entry->text);
                cursor_x = hud->x + hud->width - kTwo
                         - static_cast<f32>(hud->measure_text_cb(buffer))
                         + static_cast<f32>(hud->char_width);
                hud->draw_text_cb(&cursor_x, &callback_y, buffer);
                break;
            case 2:
                // 0x001FEB48..0x001FEBC4: "_FALSE" then the boolean suffix.
                AsdString_Copy(buffer, "_FALSE", 0x100);
                cursor_x = hud->x + hud->width - kTwo
                         - static_cast<f32>(hud->measure_text_cb(buffer))
                         + static_cast<f32>(hud->char_width);
                hud->draw_text_cb(&cursor_x, &callback_y, buffer);
                hud->draw_text_cb(&cursor_x, &callback_y,
                                  entry->int_value != 0 ? "  TRUE" : " FALSE");
                break;
            case 3:
                // 0x001FEBC8..0x001FEC24: hex or decimal integer column.
                if (entry->hex != 0) {
                    UiFont_FormatString(buffer, "0x%08X",
                                        static_cast<u32>(entry->int_value));
                } else {
                    UiFont_FormatString(buffer, " %8d", entry->int_value);
                }
                cursor_x = hud->x + hud->width - kTwo
                         - static_cast<f32>(hud->measure_text_cb(buffer));
                hud->draw_text_cb(&cursor_x, &callback_y, buffer);
                break;
            case 4:
                // 0x001FEC40..0x001FEC60: float column.
                UiFont_FormatString(buffer, " %4.2f",
                                    AsDouble(entry->float_value));
                cursor_x = hud->x + hud->width - kTwo
                         - static_cast<f32>(hud->measure_text_cb(buffer));
                hud->draw_text_cb(&cursor_x, &callback_y, buffer);
                break;
            default:
                break;
            }
        } else {
            // 0x001FEC64..0x001FEDF4: direct text fallback (no callbacks).
            engine_func_002aefc8(0, entry->label, hud->x + kTwo, cursor_y);
            cursor_x = hud->x + hud->width - kTwo;

            switch (entry->type) {
            case 0:
                break;
            case 1: {
                const char* value = entry->text;
                const u32 length = AsdString_Length(value);
                cursor_x -= static_cast<f32>((length + 1u)
                                             * static_cast<u32>(hud->char_width));
                UiFont_FormatString(buffer, " %s", value);
                engine_func_002aefc8(0, buffer, cursor_x, cursor_y);
                break;
            }
            case 2:
                cursor_x -= static_cast<f32>(hud->char_width * 6);
                engine_func_002aefc8(0,
                                     entry->int_value != 0 ? "TRUE" : "FALSE",
                                     cursor_x, cursor_y);
                break;
            case 3:
                if (entry->hex != 0) {
                    cursor_x -= static_cast<f32>(hud->char_width * 11);
                    UiFont_FormatString(buffer, " 0x%08X",
                                        static_cast<u32>(entry->int_value));
                } else {
                    cursor_x -= static_cast<f32>(hud->char_width * 9);
                    UiFont_FormatString(buffer, " %8d", entry->int_value);
                }
                engine_func_002aefc8(0, buffer, cursor_x, cursor_y);
                break;
            case 4:
                cursor_x -= static_cast<f32>(hud->char_width * 8);
                UiFont_FormatString(buffer, " %4.2f",
                                    AsDouble(entry->float_value));
                engine_func_002aefc8(0, buffer, cursor_x, cursor_y);
                break;
            default:
                break;
            }
        }

        // 0x001FEDF8..0x001FEE0C: reset x, advance y by the line height.
        cursor_x = hud->x + kTwo;
        cursor_y += static_cast<f32>(hud->line_height);
    }

    // ---- 0x001FEE1C..0x001FEE6C: cursor hand-off -------------------------
    if ((hud->flags & 2u) != 0) {
        if (hud->frame_cb != nullptr && hud->state > 2) {
            hud->frame_cb(hud->frame_arg);
        }
        return 0;
    }
    if (hud->countdown > 0) {
        hud->countdown -= 1;                        // 0x001FEE30
        if (hud->frame_cb != nullptr && hud->state > 2) {
            hud->frame_cb(hud->frame_arg);
        }
        return 0;
    }
    if (camp_func_001ff3c4(&hud->list_state) != 0) {
        hud->first_id = hud->list_state.field_24;   // 0x001FEE54
        hud->scroll = hud->list_state.field_20;     // 0x001FEE60
        if (hud->frame_cb != nullptr && hud->state > 2) {
            hud->frame_cb(hud->frame_arg);
        }
        return 0;
    }

    // ---- 0x001FEEC0..0x001FF36C: edits --------------------------------
    if (UiInput_Trigger(3) != 0) {
        // 0x001FEEDC..0x001FF06C: increase.
        DebugValueEntry* item = FindEntryAtCursor(scene);
        if (item == nullptr) {
            goto tail;
        }
        switch (item->type) {
        case 2:
            item->int_value = item->int_value == 0 ? 1 : 0;
            break;
        case 3: {
            const s32 step = StepForRepeat(repeat);
            item->int_value += step;
            if (item->int_value > item->max_value) {
                item->int_value = UiInput_Trigger2(3) != 0
                                ? item->min_value : item->max_value;
            }
            break;
        }
        case 4: {
            const s32 step = StepForRepeat(repeat);
            item->float_value += static_cast<f32>(step) * kGaugeScale;
            if (item->float_value > static_cast<f32>(item->max_value)) {
                item->float_value = UiInput_Trigger2(3) != 0
                                  ? static_cast<f32>(item->min_value)
                                  : static_cast<f32>(item->max_value);
            }
            break;
        }
        default:
            break;
        }
    } else if (UiInput_Trigger(4) != 0) {
        // 0x001FF070..0x001FF234: decrease.
        DebugValueEntry* item = FindEntryAtCursor(scene);
        if (item == nullptr) {
            goto tail;
        }
        switch (item->type) {
        case 2:
            item->int_value = item->int_value != 0 ? 0 : 1;
            break;
        case 3: {
            const s32 step = StepForRepeat(repeat);
            item->int_value -= step;
            if (item->int_value < item->min_value) {
                item->int_value = UiInput_Trigger2(4) != 0
                                ? item->max_value : item->min_value;
            }
            break;
        }
        case 4: {
            const s32 step = StepForRepeat(repeat);
            item->float_value -= static_cast<f32>(step) * kGaugeScale;
            if (item->float_value < static_cast<f32>(item->min_value)) {
                item->float_value = UiInput_Trigger2(4) != 0
                                  ? static_cast<f32>(item->min_value)
                                  : static_cast<f32>(item->max_value);
            }
            break;
        }
        default:
            break;
        }
    } else if (UiInput_Trigger2(0) != 0) {
        // 0x001FF238..0x001FF36C: invoke the entry callback.
        DebugValueEntry* item = FindEntryAtCursor(scene);
        if (item == nullptr || item->callback == nullptr) {
            goto tail;
        }
        // The callback receives either the value slot directly (user == 0)
        // or a two-word descriptor { pointer, user } on the stack.
        switch (item->type) {
        case 0: {
            if (item->user == 0) {
                item->callback(nullptr);
            } else {
                const void* args[2] = {nullptr,
                    reinterpret_cast<const void*>(
                        static_cast<std::uintptr_t>(item->user))};
                item->callback(args);
            }
            break;
        }
        case 1: {
            if (item->user == 0) {
                item->callback(item->text);
            } else {
                const void* args[2] = {item->text,
                    reinterpret_cast<const void*>(
                        static_cast<std::uintptr_t>(item->user))};
                item->callback(args);
            }
            break;
        }
        case 2:
        case 3: {
            if (item->user == 0) {
                item->callback(&item->int_value);
            } else {
                const void* args[2] = {&item->int_value,
                    reinterpret_cast<const void*>(
                        static_cast<std::uintptr_t>(item->user))};
                item->callback(args);
            }
            break;
        }
        case 4: {
            if (item->user == 0) {
                item->callback(&item->float_value);
            } else {
                const void* args[2] = {&item->float_value,
                    reinterpret_cast<const void*>(
                        static_cast<std::uintptr_t>(item->user))};
                item->callback(args);
            }
            break;
        }
        default:
            break;
        }
    }

tail:
    // 0x001FF370: end-of-frame callback (only for state > 2).
    if (hud->frame_cb != nullptr && hud->state > 2) {
        hud->frame_cb(hud->frame_arg);
    }
    return 0;
}

// ---------------------------------------------------------------------------
// 0x002ED5D0: battle command panel.
//
// The routine renders one of seven command-panel states (work+0x04) with five
// sub-layouts for state 0 (work+0x08).  It brackets its drawing with the two
// GPU render-state stacks at 0x0044EA00+0x124C and +0x12AC and ends both
// passes through 0x002C1B64 / 0x002C1ABC.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002ed5d0, 3584)
s32 ui_func_002ed5d0(void* scene) {
    BattleCommandWork* work = static_cast<BattleCommandWork*>(AsdRef_Get(scene));

    // 0x002ED5E0..0x002ED604
    UiGpu_BeginPass(g_AsdGpuState);

    u8* gpu = g_AsdGpuState;
    UiRenderStack* stack_a =
        reinterpret_cast<UiRenderStack*>(gpu + 0x124C);
    UiRenderStack* stack_b =
        reinterpret_cast<UiRenderStack*>(gpu + 0x12AC);

    PushRenderState(stack_a,
                    static_cast<u32>(reinterpret_cast<std::uintptr_t>(
                        UiGpu_SetViewportParams(1, 0))));

    // ---- 0x002ED644..0x002ED6F8: gauge row when a command is active ------
    if (work->state != 0) {
        const s32 gauge = ui_func_0026e910(0x28, 0x50, 0x3C, work->gauge, 0);
        const f32 alpha = static_cast<f32>(gauge) * kGaugeScale;

        PushRenderState(stack_b,
                        static_cast<u32>(reinterpret_cast<std::uintptr_t>(
                            UiGpu_SetRenderMode(6, 1, 0))));
        UiSprite_SetGlobalAlpha(alpha);
        UiSprite_DrawPanel(2, 0x2D, 1, 0, 0, 0x0B);
        UiSprite_SetGlobalAlpha(kOne);
    }

    // ---- 0x002ED6FC..0x002ED744: command-list render state ---------------
    PushRenderState(stack_b,
                    static_cast<u32>(reinterpret_cast<std::uintptr_t>(
                        UiGpu_SetRenderMode(6, 7, 0))));

    // ---- 0x002ED744..0x002ED7CC: header text -----------------------------
    if (work->state != 0 || work->substate != 0) {
        UiSprite_DrawPanel(2, 0x2D, 0, 0, 0, 0x0C);

        const f32 width = script_vm_func_002594f0(work->text_a);
        const UiLayoutNode* node = static_cast<const UiLayoutNode*>(
            UiLayout_GetNode(0x2D, 2));
        const f32 x = static_cast<f32>(
            static_cast<s32>((kScreenWidth - width) * kHalf));
        engine_func_002b09b8(work->text_a,
                             static_cast<u32>(node->y), 0,
                             x, static_cast<f32>(node->y),
                             kIconScale, kOne);
    }

    // ---- 0x002ED7D8..0x002ED7E4: state dispatch --------------------------
    switch (work->state) {
    case 0:
        // 0x002ED808: five-entry sub-layout jump table at 0x002ED818.
        switch (work->substate) {
        case 0: {
            // 0x002ED82C..0x002ED8E4
            const f32 progress = ui_func_0024807c(
                -16.0f, 0.0f, kPanelSpan,
                static_cast<f32>(work->value_a));
            const f32 alpha = ui_func_0026e97c(
                0.0f, kOne, kPanelSpan,
                static_cast<f32>(work->value_b));
            UiSprite_SetGlobalAlpha(alpha);
            UiSprite_DrawPanel(2, 0x2D, 2, 0,
                               static_cast<s32>(progress), 0x0C);

            const f32 width = script_vm_func_002594f0(work->text_a);
            const UiLayoutNode* node = static_cast<const UiLayoutNode*>(
                UiLayout_GetNode(0x2D, 2));
            const f32 x = static_cast<f32>(
                static_cast<s32>((kScreenWidth - width) * kHalf));
            engine_func_002b09b8(work->text_a,
                                 static_cast<u32>(node->y), 0,
                                 x, static_cast<f32>(node->y) + progress,
                                 kIconScale, alpha);
            UiSprite_SetGlobalAlpha(kOne);
            break;
        }
        case 1: {
            // 0x002ED8E8..0x002ED9DC
            const UiLayoutNode* bar = static_cast<const UiLayoutNode*>(
                UiLayout_GetNode(0x2D, 0x0B));
            const f32 progress = ui_func_0026e97c(
                0.0f, static_cast<f32>(bar->rect->h), kPanelSpan,
                static_cast<f32>(work->value_a));
            const u32 progress_bits =
                static_cast<u32>(progress);

            const UiLayoutNode* row = static_cast<const UiLayoutNode*>(
                UiLayout_GetNode(0x2D, 0x0B));
            const s32 row_h = row->rect->h;
            const s32 row_w = row->rect->w;
            func_002b0908(2, 0x2D, 0x0B, 0,
                          static_cast<u32>(static_cast<s32>(
                              (static_cast<f32>(row_h) - progress) * kHalf)),
                          static_cast<u32>(row_w),
                          progress_bits, 0x0C);

            const UiLayoutNode* next = static_cast<const UiLayoutNode*>(
                UiLayout_GetNode(0x2D, 0x0C));
            const s32 h = next->rect->h;
            const s32 w = next->rect->w;
            func_002b0908(2, 0x2D, 0x0C, 0,
                          static_cast<u32>(static_cast<s32>(
                              (static_cast<f32>(h) - progress) * kHalf)),
                          static_cast<u32>(w),
                          progress_bits, 0x0C);
            break;
        }
        case 2:
            // 0x002EDA04..0x002EDA7C
            UiSprite_DrawPanel(2, 0x2D, 2, 0, 0, 0x0C);
            UiSprite_SetGlobalAlpha(ui_func_0026e97c(
                0.0f, kOne, kPanelSpan, static_cast<f32>(work->value_b)));
            UiSprite_DrawNode(2, 0x2D, 0x0D, 0, 0, 0x0D);
            UiSprite_DrawNode(2, 0x2D, 0x10, 0, 0, 0x0D);
            UiSprite_SetGlobalAlpha(kOne);
            break;
        case 3:
            // 0x002EDA80..0x002EDB28
            UiSprite_DrawPanel(2, 0x2D, 2, 0, 0, 0x0C);
            UiSprite_DrawNode(2, 0x2D, 0x0D, 0, 0, 0x0D);
            UiSprite_DrawNode(2, 0x2D, 0x10, 0, 0, 0x0D);
            UiSprite_SetGlobalAlpha(ui_func_0026e97c(
                0.0f, kOne, kPanelSpan, static_cast<f32>(work->value_b)));
            UiSprite_DrawNode(2, 0x2D, 0x0E, 0, 0, 0x0D);
            UiSprite_DrawNode(2, 0x2D, 0x0F, 0, 0, 0x0D);
            UiSprite_SetGlobalAlpha(kOne);
            break;
        case 4: {
            // 0x002EDB2C..0x002EDE24: icon row, fade alpha, two bar fills.
            const f32 progress = ui_func_0026e97c(
                0.0f, kOne, kPanelSpan, static_cast<f32>(work->value_b));
            UiSprite_SetGlobalAlpha(progress * kIconAlpha);

            PushRenderState(stack_b,
                            static_cast<u32>(reinterpret_cast<std::uintptr_t>(
                                UiGpu_SetRenderMode(6, 1, 0))));
            UiSprite_DrawPanel(2, 0x2D, 1, 0, 0, 0x0B);

            PushRenderState(stack_b,
                            static_cast<u32>(reinterpret_cast<std::uintptr_t>(
                                UiGpu_SetRenderMode(6, 7, 0))));
            UiSprite_SetGlobalAlpha(kOne);
            UiSprite_DrawPanel(2, 0x2D, 2, 0, 0, 0x0C);
            UiSprite_DrawNode(2, 0x2D, 0x0D, 0, 0, 0x0D);
            UiSprite_DrawNode(2, 0x2D, 0x0E, 0, 0, 0x0D);
            UiSprite_DrawNode(2, 0x2D, 0x0F, 0, 0, 0x0D);
            UiSprite_DrawNode(2, 0x2D, 0x10, 0, 0, 0x0D);
            UiSprite_SetGlobalAlpha(progress);
            UiSprite_DrawNode(2, 0x2D, 0x11, 0, 0, 0x0D);
            UiSprite_DrawNode(2, 0x2D, 0x13, 0, 0, 0x0F);
            UiSprite_DrawNode(2, 0x2D, 0x14, 0, 0, 0x10);

            // 0x002EDCEC..0x002EDD1C: the bar fill is value_a over the height
            // of layout node 0x17.
            const UiLayoutNode* bar = static_cast<const UiLayoutNode*>(
                UiLayout_GetNode(0x2D, 0x17));
            const f32 fill = ui_func_0026e97c(
                0.0f, static_cast<f32>(bar->rect->h), kPanelSpan,
                static_cast<f32>(work->value_a));
            const u32 fill_bits = static_cast<u32>(fill);

            const UiLayoutNode* row17 = static_cast<const UiLayoutNode*>(
                UiLayout_GetNode(0x2D, 0x17));
            func_002b0908(2, 0x2D, 0x17, 0,
                          static_cast<u32>(static_cast<s32>(
                              (static_cast<f32>(row17->rect->h) - fill)
                              * kHalf)),
                          static_cast<u32>(row17->rect->w),
                          fill_bits, 0x0C);

            const UiLayoutNode* row18 = static_cast<const UiLayoutNode*>(
                UiLayout_GetNode(0x2D, 0x18));
            func_002b0908(2, 0x2D, 0x18, 0,
                          static_cast<u32>(static_cast<s32>(
                              (static_cast<f32>(row18->rect->h) - fill)
                              * kHalf)),
                          static_cast<u32>(row18->rect->w),
                          fill_bits, 0x0C);

            // 0x002EDDD4..0x002EDE18: footer text scaled by the fade alpha.
            const f32 width = script_vm_func_002594f0(work->text_b);
            const UiLayoutNode* footer = static_cast<const UiLayoutNode*>(
                UiLayout_GetNode(0x2D, 0x19));
            const f32 x = static_cast<f32>(
                static_cast<s32>((kScreenWidth - width) * kHalf));
            engine_func_002b09b8(work->text_b,
                                 static_cast<u32>(footer->y), 0,
                                 x, static_cast<f32>(footer->y),
                                 kIconScale, progress);
            UiSprite_SetGlobalAlpha(kOne);
            break;
        }
        default:
            break;
        }
        break;

    case 1: {
        // 0x002EDE2C..0x002EDEA4
        ui_func_00247de4(work, 0x0B);
        UiSprite_DrawPanel(2, 0x2D, 3, 0, 0, 0x0C);
        const f32 width = script_vm_func_002594f0(work->text_b);
        const UiLayoutNode* node = static_cast<const UiLayoutNode*>(
            UiLayout_GetNode(0x2D, 0x19));
        const f32 x = static_cast<f32>(
            static_cast<s32>((kScreenWidth - width) * kHalf));
        engine_func_002b09b8(work->text_b,
                             static_cast<u32>(node->y), 0,
                             x, static_cast<f32>(node->y),
                             kIconScale, kOne);
        break;
    }

    case 2: {
        // 0x002EDEA8..0x002EDF54
        ui_func_00247de4(work, 0x0B);
        UiSprite_DrawPanel(2, 0x2D, 3, 0, 0, 0x0C);
        const f32 width = script_vm_func_002594f0(work->text_b);
        const UiLayoutNode* node = static_cast<const UiLayoutNode*>(
            UiLayout_GetNode(0x2D, 0x19));
        const f32 x = static_cast<f32>(
            static_cast<s32>((kScreenWidth - width) * kHalf));
        engine_func_002b09b8(work->text_b,
                             static_cast<u32>(node->y), 0,
                             x, static_cast<f32>(node->y),
                             kIconScale, kOne);

        const f32 value = ui_func_0024807c(
            kScreenWidth, 0.0f, kPanelSpan, static_cast<f32>(work->value_a));
        UiSprite_DrawPanel(2, 0x2D, 4, static_cast<s32>(value), 0, 0x0E);
        break;
    }

    case 3: {
        // 0x002EDF58..0x002EE000: eight icon cells at layout nodes 0x29..0x22.
        ui_func_00247de4(work, 0x0B);
        UiSprite_DrawPanel(2, 0x2D, 4, 0, 0, 0x0C);

        for (s32 i = 0; i < 8; ++i) {
            // 0x002EDF88..0x002EDF9C expands to signed remainder by 8:
            // `asr r1,r0,#31; add r1,r0,r1,lsr #29; bic r1,r1,#7;
            //  sub r6,r0,r1`.
            const s32 index = (work->value_a + i) % 8;

            const UiLayoutNode* node = static_cast<const UiLayoutNode*>(
                UiLayout_GetNode(0x2D, 0x29 - i));
            const s32 y = node->y;
            UiSprite_DrawNode(2, 0x2D,
                              static_cast<u32>(g_BattleCommandIcons[index]) + 0x1F,
                              node->x, y, 0x0D);
        }

        const UiLayoutNode* last = static_cast<const UiLayoutNode*>(
            UiLayout_GetNode(0x2D, 0x2A));
        UiSprite_DrawNode(2, 0x2D, 0x1F, last->x, last->y, 0x0D);
        break;
    }

    case 4: {
        // 0x002EE004..0x002EE1FC: icon row with two gradient strips.
        UiSprite_SetGlobalAlpha(ui_func_0026e97c(
            kOne, 0.0f, kPanelSpan, static_cast<f32>(work->value_b)));
        ui_func_00247de4(work, 0x0B);
        UiSprite_DrawPanel(2, 0x2D, 4, 0, 0, 0x0C);

        for (s32 i = 0; i < 8; ++i) {
            const UiLayoutNode* node = static_cast<const UiLayoutNode*>(
                UiLayout_GetNode(0x2D, 0x29 - i));
            UiSprite_DrawNode(2, 0x2D, 0x1F, node->x, node->y, 0x0D);
        }
        const UiLayoutNode* last = static_cast<const UiLayoutNode*>(
            UiLayout_GetNode(0x2D, 0x2A));
        UiSprite_DrawNode(2, 0x2D, 0x1F, last->x, last->y, 0x0D);
        UiSprite_SetGlobalAlpha(kOne);

        UiSprite_SetGlobalAlpha(ui_func_0026e97c(
            0.0f, kOne, kPanelSpan, static_cast<f32>(work->value_b)));

        const UiLayoutNode* bar = static_cast<const UiLayoutNode*>(
            UiLayout_GetNode(0x2D, 0x2F));
        const s32 bar_h = bar->rect->h;
        const f32 progress = ui_func_0026e97c(
            0.0f, static_cast<f32>(bar_h), kPanelSpan,
            static_cast<f32>(work->value_b));

        const UiLayoutNode* row30 = static_cast<const UiLayoutNode*>(
            UiLayout_GetNode(0x2D, 0x2E));
        const s32 row30_h = row30->rect->h;
        const s32 row30_w = row30->rect->w;
        // 0x002EE178..0x002EE18C stores h(row30) - h(row31) + progress,
        // not the bare progress word used by the second strip.
        func_002b0908(2, 0x2D, 0x2E, 0,
                      static_cast<u32>(static_cast<s32>(
                          (static_cast<f32>(row30_h) - progress) * kHalf)),
                      static_cast<u32>(row30_w),
                      static_cast<u32>(static_cast<s32>(
                          static_cast<f32>(row30_h) - static_cast<f32>(bar_h)
                          + progress)),
                      0x10);

        const UiLayoutNode* row31 = static_cast<const UiLayoutNode*>(
            UiLayout_GetNode(0x2D, 0x2F));
        const s32 row31_w = row31->rect->w;
        func_002b0908(2, 0x2D, 0x2F, 0,
                      static_cast<u32>(static_cast<s32>(
                          (static_cast<f32>(row31->rect->h) - progress)
                          * kHalf)),
                      static_cast<u32>(row31_w),
                      static_cast<u32>(progress),
                      0x11);

        UiSprite_SetGlobalAlpha(kOne);
        break;
    }

    case 5: {
        // 0x002EE200..0x002EE2E8
        UiSprite_DrawPanel(2, 0x2D, 5, 0, 0, 0x0C);
        const f32 value = ui_func_0024807c(
            kScreenWidth, 0.0f, kPanelSpan, static_cast<f32>(work->value_a));
        UiSprite_DrawNode(2, 0x2D, 0x30, static_cast<s32>(value), 0, 0x0D);

        const s32 gauge = ui_func_0026e910(0, 0x64, 0x0C, work->value_b, 0);
        const f32 alpha = static_cast<f32>(gauge) * kGaugeScale;

        PushRenderState(stack_b,
                        static_cast<u32>(reinterpret_cast<std::uintptr_t>(
                            UiGpu_SetRenderMode(6, 1, 0))));
        UiSprite_SetGlobalAlpha(alpha);
        UiSprite_DrawNode(2, 0x2D, 0x31, 0, 0, 0x0E);
        UiSprite_SetGlobalAlpha(kOne);
        PushRenderState(stack_b,
                        static_cast<u32>(reinterpret_cast<std::uintptr_t>(
                            UiGpu_SetRenderMode(6, 7, 0))));
        break;
    }

    case 6:
        // 0x002EE398..0x002EE3CC
        UiSprite_DrawPanel(2, 0x2D, 5, 0, 0, 0x0C);
        UiSprite_DrawNode(2, 0x2D, 0x30, 0, 0, 0x0D);
        break;

    default:
        break;
    }

    // 0x002EE330..0x002EE390: close both render passes.
    PopRenderState(stack_a);
    UiGpu_EndPass1(g_AsdGpuState);
    UiGpu_EndPass2(g_AsdGpuState);
    return 0;
}

// ---------------------------------------------------------------------------
// 0x0036C0A8 / 0x00368CF8: action-panel command emitters
// ---------------------------------------------------------------------------

// Observed call targets.  One declaration per binary address.
extern "C" {
// 0x002A2570: emits the command template at `src` and returns the payload
// pointer.  The callers write the payload and advance the cursor themselves.
u32* UiCmd_Emit(u32* cursor, const void* src);

// 0x002ACD38: memcpy-shaped command payload copy.
void ui_func_002acd38(void* dst, const void* src, u32 size);

// Battle-panel list helpers.
void func_003748d4(UiActionScene* scene, UiActionPanel* actor);
void battle_func_00374e60(UiActionPanel* frame, UiActionScene* scene);
void func_003744f8(UiActionPanel* frame, UiActionScene* scene,
                   void* list, u32 flag);
void func_00375504(void* base, void* node);
} // extern "C"

namespace {

// ---------------------------------------------------------------------------
// Reproduced .data/.bss globals
// ---------------------------------------------------------------------------

UiPanelFlags  g_UiPanelFlags_472088{};      // 0x00472088
u32           g_UiPanelA_4720a0 = 0;        // 0x004720A0
UiPanelShader g_UiPanelShader_4720b8{};     // 0x004720B8
u32           g_UiPanelMode_4720ec = 0;     // 0x004720EC
void*         g_UiPanelCmd_4720f0 = nullptr; // 0x004720F0
f32           g_UiPanelTimeA_4720f4 = 0.0f; // 0x004720F4
f32           g_UiPanelTimeB_4720f8 = 0.0f; // 0x004720F8
f32           g_UiPanelScale_4720fc = 0.0f; // 0x004720FC
u32           g_UiPanelVisibleMask_472100 = 0; // 0x00472100
u32           g_UiPanelCmdFlag_47663c = 0;  // 0x0047663C
UiPanelCommand g_UiPanelCommand_4efddc{};   // 0x004EFDDC

inline u32 FloatBits(f32 value) {
    u32 word = 0;
    std::memcpy(&word, &value, sizeof(word));
    return word;
}

inline f32 BitsFloat(u32 word) {
    f32 value = 0.0f;
    std::memcpy(&value, &word, sizeof(value));
    return value;
}

// 0x0036C408..0x0036C450: float-to-24-bit fixed conversion.  The exponent is
// kept in bits 16..22 and the mantissa in bits 0..15; the sign is bit 23.
u32 PackFixed(f32 value) {
    const u32 bits = FloatBits(value);
    u32 result = ((bits & 0x80000000u) != 0) ? 0x00800000u : 0u;
    const u32 exponent = (bits << 1) >> 24;
    u32 mantissa = (bits << 9) >> 9;
    if ((bits & 0x7FFFFFFFu) == 0) {
        mantissa >>= 7;
        return result | mantissa;
    }
    const s32 biased = static_cast<s32>(exponent) - 0x40;
    mantissa >>= 7;
    if (biased < 0) {
        return result;
    }
    if (biased > 0x7F) {
        return 0x007F0000u;
    }
    return result | mantissa | (static_cast<u32>(biased & 0x7F) << 16);
}

// 0x0036C214..0x0036C22C / 0x0036C304..0x0036C314: two-word command.
void EmitPair(u32 first, u32 second) {
    u32* cursor = engine::g_GpuCommandCursor;
    cursor[0] = first;
    cursor[1] = second;
    engine::g_GpuCommandCursor = cursor + 2;
}

// 0x0036C3A4..0x0036C480: shader/timing command built around the
// 0x004EFDDC template.
void EmitShaderCommand(UiActionPanel* panel) {
    // 0x0036C338..0x0036C35C
    g_UiPanelFlags_472088.field_06 =
        ((panel->field_104 & 1u) == 0) ? 1 : 0;
    g_UiPanelScale_4720fc = BitsFloat(panel->field_108);

    // 0x0036C36C..0x0036C3A0
    if ((g_UiPanelCmdFlag_47663c & 1u) == 0 &&
        AsdFlag_TestAndSet(&g_UiPanelCmdFlag_47663c) != 0) {
        g_UiPanelCommand_4efddc.word_04 = 0x0001006Du;
        g_UiPanelCommand_4efddc.word_0c = 0x8017004Du;
    }

    // 0x0036C3A4..0x0036C3C8
    f32 s0 = 0.0f;
    f32 s1 = -g_UiPanelScale_4720fc;
    const void* template_source = &g_UiPanelCommand_4efddc;
    if (g_UiPanelCmd_4720f0 != nullptr) {
        g_UiPanelCommand_4efddc.word_00 = 0;
        g_UiPanelCommand_4efddc.word_08 =
            static_cast<u32>(reinterpret_cast<std::uintptr_t>(
                g_UiPanelCmd_4720f0));
    } else {
        // 0x0036C94C..0x0036C980
        g_UiPanelCommand_4efddc.word_00 = 1;
        g_UiPanelCommand_4efddc.word_08 = g_UiPanelA_4720a0;
        s1 = (g_UiPanelTimeA_4720f4 - g_UiPanelTimeB_4720f8)
           * g_UiPanelScale_4720fc;
    }

    // 0x0036C3D4..0x0036C404
    if (g_UiPanelFlags_472088.field_06 != 0) {
        f32 s2;
        if (g_UiPanelMode_4720ec == 0x8100A5u) {
            s2 = BitsFloat(0x37800080u);            // 1/256
        } else {
            const f32 s3 = BitsFloat(0x43000000u);  // 128.0f
            s2 = BitsFloat(0x33800001u);
            s1 *= s3;
        }
        s0 -= s1 * s2;
    }

    // 0x0036C408..0x0036C45C
    g_UiPanelCommand_4efddc.color = PackFixed(s0);
    u32* dest = UiCmd_Emit(engine::g_GpuCommandCursor, template_source);
    dest[0] = panel->field_10c;
    dest[1] = panel->field_110;
    engine::g_GpuCommandCursor = dest + 2;
}

// 0x00472088..0x00472090 dirty-byte update used by the 0x118 state block.
void UpdateDirtyByte(u8* dirty, u8* stored, u8 value) {
    u8 previous = *stored;
    if (previous == 0) {
        previous = *dirty;
    }
    *dirty = (previous == value) ? 0 : 1;
    *stored = value;
}

// 0x0036CAA8..0x0036CDA0: the 0x118 state block of a panel.
void EmitPanelStateCommand(UiActionPanel* panel) {
    u8* state = reinterpret_cast<u8*>(panel) + 0x118;
    const u32 bit0 = (panel->field_118 & 1u) == 0 ? 1u : 0u;
    const u32 bit1 = (panel->field_118 & 2u) == 0 ? 1u : 0u;

    // 0x0036CAAC..0x0036CB28
    UpdateDirtyByte(&g_UiPanelFlags_472088.field_01,
                    &g_UiPanelFlags_472088.field_03, static_cast<u8>(bit0));
    UpdateDirtyByte(&g_UiPanelFlags_472088.field_01,
                    &g_UiPanelFlags_472088.field_05, static_cast<u8>(bit1));

    // 0x0036CB2C..0x0036CB8C: emit the 0x20-byte state record.
    u32* cursor = engine::g_GpuCommandCursor;
    const u32 first = (g_UiPanelFlags_472088.field_08 << 8) | 0x1000u;
    cursor[0] = first;
    cursor[1] = 0x00020107u;
    cursor[2] = static_cast<u32>(g_UiPanelFlags_472088.field_07) << 8;
    cursor[3] = 0x00020105u;
    cursor[4] = panel->field_11c;
    cursor[5] = panel->field_120;
    cursor[6] = panel->field_124;
    cursor[7] = panel->field_128;
    engine::g_GpuCommandCursor = cursor + 8;

    // 0x0036CB90..0x0036CBE8: optional 16-byte copy from +0x158.
    if (panel->field_158 != 0) {
        u8* source = reinterpret_cast<u8*>(
            static_cast<std::uintptr_t>(panel->field_158));
        if ((*reinterpret_cast<u32*>(source) & 1u) != 0) {
            UpdateDirtyByte(&g_UiPanelFlags_472088.field_01,
                            &g_UiPanelFlags_472088.field_04, 1);
            std::memcpy(engine::g_GpuCommandCursor, source, 0x10);
            engine::g_GpuCommandCursor += 4;
        } else {
            UpdateDirtyByte(&g_UiPanelFlags_472088.field_01,
                            &g_UiPanelFlags_472088.field_04, 0);
        }
    }

    // 0x0036CBEC..0x0036CC28: the high bit of +0x12C is the dirty source.
    const u32 high = (panel->field_12c & 0x80000000u) == 0 ? 1u : 0u;
    UpdateDirtyByte(&g_UiPanelFlags_472088.field_01,
                    &g_UiPanelFlags_472088.field_02,
                    static_cast<u8>(high ^ 1u));

    // 0x0036CC2C..0x0036CC38: reserve the state command.
    u32* dest = UiCmd_Emit(engine::g_GpuCommandCursor,
                           reinterpret_cast<void*>(state + 0x14));
    engine::g_GpuCommandCursor = dest;

    // 0x0036CC40..0x0036CC88: animation state at +0x28 (bits 0..1).
    const u32 mode = panel->field_140 & 3u;
    if (g_UiPanelFlags_472088.field_00 != static_cast<u8>(mode)) {
        g_UiPanelFlags_472088.field_00 = static_cast<u8>(mode);
        g_UiPanelFlags_472088.field_01 = 1;
    } else if (g_UiPanelFlags_472088.field_01 == 0) {
        goto emit_state;
    }

    // 0x0036CC88..0x0036CD84
    g_UiPanelFlags_472088.field_01 = 0;
    g_UiPanelShader_4720b8.field_10 = 0;
    g_UiPanelShader_4720b8.field_18 = 0;
    if (mode != 0) {
        g_UiPanelShader_4720b8.field_10 = 0x0F;
        g_UiPanelShader_4720b8.field_18 = 0x0F;
    } else if (g_UiPanelFlags_472088.field_08 != 0) {
        if (g_UiPanelFlags_472088.field_02 != 0 ||
            g_UiPanelFlags_472088.field_08 != 0x0F) {
            g_UiPanelShader_4720b8.field_10 = 0x0F;
        }
        g_UiPanelShader_4720b8.field_18 = 0x0F;
    }
    g_UiPanelShader_4720b8.field_1c = 0;
    g_UiPanelShader_4720b8.field_20 = 0;
    if (mode == 1) {
        g_UiPanelShader_4720b8.field_1c = 3;
    } else if (mode == 0) {
        if (g_UiPanelFlags_472088.field_03 != 0) {
            if (g_UiPanelFlags_472088.field_05 != 0) {
                g_UiPanelShader_4720b8.field_1c = 2;
                g_UiPanelShader_4720b8.field_20 = 2;
            } else if (g_UiPanelFlags_472088.field_08 != 0) {
                g_UiPanelShader_4720b8.field_1c = 2;
            }
        }
        if (g_UiPanelFlags_472088.field_04 != 0) {
            if (g_UiPanelFlags_472088.field_07 != 0) {
                g_UiPanelShader_4720b8.field_1c |= 1;
                g_UiPanelShader_4720b8.field_20 |= 1;
            } else if (g_UiPanelFlags_472088.field_08 != 0) {
                g_UiPanelShader_4720b8.field_1c |= 1;
            }
        }
    }

emit_state:
    // 0x0036CD84..0x0036CDA0
    ui_func_002acd38(engine::g_GpuCommandCursor, &g_UiPanelShader_4720b8,
                     0x28);
    engine::g_GpuCommandCursor += 0x0A;
}

} // namespace




// 0x0036C8E8..0x0036CA40 / 0x003695BC..0x00369678: six 28-byte entries at
// node+0x2C; each entry selects a panel word by its low byte and emits the
// four-word record at entry+4.
void EmitEffectEntries(u8* node) {
    if (node == nullptr) {
        return;
    }
    u32* cursor = UiCmd_Emit(engine::g_GpuCommandCursor, node + 0xDC);
    engine::g_GpuCommandCursor = cursor;
    for (s32 i = 0; i < 6; ++i) {
        u8* entry = node + 0x2C + i * 28;
        const u32 selector = *reinterpret_cast<u32*>(entry) & 0xFFu;
        u32 value;
        switch (selector) {
        case 0:  value = *reinterpret_cast<u32*>(entry + 0xC8); break;
        case 1:  value = *reinterpret_cast<u32*>(entry + 0xCC); break;
        case 2:  value = *reinterpret_cast<u32*>(entry + 0xD0); break;
        case 3:  value = *reinterpret_cast<u32*>(entry + 0xD4); break;
        case 4:  value = *reinterpret_cast<u32*>(entry + 0xD8); break;
        case 5:  value = *reinterpret_cast<u32*>(entry + 0xB0); break;
        case 6:  value = *reinterpret_cast<u32*>(entry + 0xB4); break;
        case 7:  value = *reinterpret_cast<u32*>(entry + 0xB8); break;
        case 8:  value = *reinterpret_cast<u32*>(entry + 0xBC); break;
        case 9:  value = *reinterpret_cast<u32*>(entry + 0xC0); break;
        default: value = *reinterpret_cast<u32*>(entry + 0xC4); break;
        }
        *reinterpret_cast<u32*>(entry + 0x14) = value;
        engine::g_GpuCommandCursor =
            UiCmd_Emit(engine::g_GpuCommandCursor, entry + 4);
    }
}

// ---------------------------------------------------------------------------
// 0x0036C0A8: single-panel action emitter.
//
// The routine reads the status bytes from frame+0x40 (+0xA0..+0xAB), snapshots
// frame+0x100..+0x128, and emits command records into the GPU stream at
// 0x004652A0.  All eleven state words are written back at 0x0036CDA4.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0036c0a8, 3480)
void ui_func_0036c0a8(void* unused, UiActionPanel* frame, UiActionSlot* slot) {
    (void)unused;
    if (frame == nullptr) {
        return;
    }

    UiActionScene* scene = static_cast<UiActionScene*>(frame->scene);
    UiActionPanel* panel = (slot != nullptr) ? slot->panel : nullptr;
    if (panel == nullptr) {
        return;
    }

    // 0x0036C0B8..0x0036C0E8: status bytes frame+0xE8..+0xEB.
    const s32 active_a = (frame->field_e8 != 0 || frame->field_e9 != 0) ? 1 : 0;
    const s32 active_b = (frame->field_ea != 0 || frame->field_eb != 0) ? 1 : 0;

    // 0x0036C0F4..0x0036C12C: early out when the list is empty and the
    // frame/panel pair is unchanged.
    if (frame->field_24 != 0) {
        u8* object = reinterpret_cast<u8*>(
            static_cast<std::uintptr_t>(frame->field_24));
        if (object[0x14] - object[0x10] == 0) {
            // 0x0036C118..0x0036C12C: [ [frame+0x24] + 8 ] must equal the
            // panel pointer for the early return.
            if (*reinterpret_cast<u32*>(object + 8) ==
                    static_cast<u32>(
                        reinterpret_cast<std::uintptr_t>(panel)) &&
                active_a == 0 && active_b == 0) {
                return;
            }
        }
    }

    // 0x0036C130..0x0036C198: snapshot of the frame's eleven state words.
    u32 s100 = frame->field_100;
    u32 s104 = frame->field_104;
    u32 s108 = frame->field_108;
    u32 s10c = frame->field_10c;
    u32 s110 = frame->field_110;
    u32 s114 = frame->field_114;
    u32 s118 = frame->field_118;
    u32 s11c = frame->field_11c;
    u32 s120 = frame->field_120;
    u32 s124 = frame->field_124;
    u32 s128 = frame->field_128;

    // 0x0036C19C..0x0036C1C4
    if (!(panel->field_2a4 != 0 && s100 == panel->field_2a4 &&
          frame->field_13 == 0)) {
        func_003748d4(scene, panel);
        s100 = panel->field_2a4;
    }

    // 0x0036C1C8..0x0036C230: scene 0x8000 bit and visibility record.
    const s32 visible =
        ((panel->field_18 & 1u) == 0 && frame->field_e4 != 0) ? 1 : 0;
    if (visible != 0) {
        scene->field_14 |= 0x8000u;
    } else {
        scene->field_14 &= ~0x8000u;
    }
    EmitPair(static_cast<u32>(visible ^ 1), 0x000101C6u);
    EmitPair(static_cast<u32>(visible), 0x0001008Fu);

    // 0x0036C230..0x0036C318
    u32 previous_2a0 = s104;
    if (!(panel->field_2a0 != 0 && previous_2a0 == panel->field_2a0 &&
          active_b == 0)) {
        UiActionList* list =
            static_cast<UiActionList*>(scene->list);
        if (list != nullptr) {
            // 0x0036C25C: the 0x1000 bit is only touched when the list has
            // at least one row.
            if (list->field_68 > 0) {
                if (frame->field_e0 > 0 &&
                    (panel->field_18 & 2u) == 0) {
                    panel->field_14 |= 0x1000u;
                } else {
                    panel->field_14 &= ~0x1000u;
                }
            }
            if ((list->flags & 4u) == 0) {
                if (frame->field_44 != 0 &&
                    (panel->field_18 & 4u) == 0) {
                    panel->field_14 |= 0x20u;
                    if ((panel->field_18 & 8u) != 0) {
                        panel->field_14 |= 0x40u;
                    } else {
                        panel->field_14 &= ~0x40u;
                    }
                } else {
                    panel->field_14 &= ~0x20u;
                }
            }
        }
        u32 value = 0;
        if ((panel->field_18 & 0x10u) != 0 && frame->field_a0 != 0) {
            value = 5;
        }
        EmitPair(value, 0x000100E0u);
        previous_2a0 = panel->field_2a0;
    }

    // 0x0036C31C..0x0036C480: shader state.
    if (!(panel->field_2b8 != 0 && s10c == panel->field_2b8)) {
        EmitShaderCommand(panel);
        s10c = panel->field_2b8;
    }

    // 0x0036C484..0x0036C4AC
    if (!(panel->field_2a8 != 0 && s110 == panel->field_2a8)) {
        battle_func_00374e60(frame, scene);
        s110 = panel->field_2a8;
    }

    // 0x0036C4B0..0x0036C55C: three sprite slots at panel+0x274.
    u32 previous_2b0 = s114;
    s32 list_flag = 1;
    if (!(panel->field_2b0 != 0 && previous_2b0 == panel->field_2b0)) {
        u32 mask = 0;
        for (s32 i = 0; i < 3; ++i) {
            u32* slot_field = &panel->field_274 + i;
            u32 relative = *slot_field;
            u8* object = (relative != 0)
                       ? reinterpret_cast<u8*>(slot_field) + relative
                       : nullptr;
            if (object == nullptr) {
                continue;
            }
            mask |= 1u << i;
            const u32 width = *reinterpret_cast<u32*>(object + 0x48);
            ui_func_002acd38(engine::g_GpuCommandCursor, object + 0x10, width);
            engine::g_GpuCommandCursor += (width & ~3u) / 4u;
        }
        EmitPair(mask | 0x10000u, 0x00050080u);
        previous_2b0 = panel->field_2b0;
        s114 = panel->field_2b0;
    }

    // 0x0036C560..0x0036C850: list record / flags.
    if ((panel->field_18 & 1u) == 0) {
        u8* node = (panel->rel_288 != 0)
                 ? reinterpret_cast<u8*>(panel) + 0x288 + panel->rel_288
                 : nullptr;
        u8* record = (node != nullptr) ? node + 0x10 : nullptr;
        list_flag = ((*reinterpret_cast<u32*>(record) & 0x20u) == 0) ? 1 : 0;

        if (!(panel->field_2bc != 0 && s118 == panel->field_2bc &&
              active_a == 0)) {
            // 0x0036C5E8..0x0036C6F4: 16-byte descriptor command.
            u8* data = record;
            const u32 b4 = *reinterpret_cast<u32*>(data + 4) & 0xFFu;
            const u32 b8 = *reinterpret_cast<u32*>(data + 8) & 0xFFu;
            const u32 bc = *reinterpret_cast<u32*>(data + 0xC) & 0xFFu;
            const u32 b14 = data[0x14];
            const u32 mask = (b14 != 0) ? 0u : 0xFFFFFFFFu;
            const u32 bit0 = ((mask & bc) == 0) ? 1u : 0u;
            const u32 flags = *reinterpret_cast<u32*>(data);
            const u32 word0 = 0x80000000u | (b8 << 2) | (b4 << 4)
                            | (bc << 28)
                            | (((flags & 1u) == 0 ? 1u : 0u) << 27)
                            | ((bit0 ^ 1u) << 30) | 0x400u;
            const u32 word1 = (((flags & 2u) == 0 ? 1u : 0u) << 16)
                            | (((flags & 4u) == 0 ? 1u : 0u) << 17)
                            | ((b8 == 0 ? 1u : 0u) << 19)
                            | ((flags & 0x20u) == 0 ? 7u : 0u) << 20
                            | 0x40000u;
            u32* cursor = engine::g_GpuCommandCursor;
            cursor[0] = word0;
            cursor[1] = 0x000F01C3u;
            cursor[2] = word1;
            cursor[3] = 0x000401C4u;
            engine::g_GpuCommandCursor = cursor + 4;

            // 0x0036C6F8..0x0036C80C: per-actor flags.
            const u32 bit3 = (flags & 8u) == 0 ? 1u : 0u;
            const u32 bit4 = (flags & 0x10u) == 0 ? 1u : 0u;
            if (frame->field_e4 > 0) {
                u32* entries = reinterpret_cast<u32*>(
                    static_cast<std::uintptr_t>(frame->field_64));
                for (s32 i = 0; i < static_cast<s32>(frame->field_e4); ++i) {
                    u8* entry = reinterpret_cast<u8*>(
                        static_cast<std::uintptr_t>(entries[i]));
                    const u32 pair = *reinterpret_cast<u32*>(entry + 0x18) & 2u;
                    const u32 pair_bit = pair >> 1;
                    const u32 actor_state =
                        *reinterpret_cast<u32*>(entry + 0xB8);
                    u32 selected = 0;
                    if (actor_state == 0 ||
                        ((g_UiPanelVisibleMask_472100 >> i) & 1u) != 0) {
                        selected = 1;
                    }
                    u32 word = selected;
                    if (pair_bit != 0) {
                        word |= 2u;
                    }
                    if (bit3 != 0) {
                        word |= 4u;
                    }
                    if (bit4 != 0) {
                        word |= 8u;
                    }
                    EmitPair(word, 0x00010149u + (static_cast<u32>(i) << 4));
                }
            }
        }

        // 0x0036C810..0x0036C854
        u8* node2 = (panel->rel_288 != 0)
                  ? reinterpret_cast<u8*>(panel) + 0x288 + panel->rel_288
                  : nullptr;
        u8* list_node = nullptr;
        if (node2 != nullptr) {
            const u32 rel_next = *reinterpret_cast<u32*>(node2 + 0x28);
            list_node = (rel_next != 0) ? node2 + 0x28 + rel_next : nullptr;
        }
        if (!(panel->field_2c0 != 0 && s11c == panel->field_2c0)) {
            func_00375504(record, list_node);
        }
    }

    // 0x0036C858..0x0036C9C8: the +0x2B4 list.
    if (!(panel->field_2b4 != 0 && s108 == panel->field_2b4 &&
          active_a == 0)) {
        func_003744f8(frame, scene, &panel->field_24,
                      static_cast<u32>(list_flag));
        u8* node = (panel->rel_288 != 0)
                 ? reinterpret_cast<u8*>(panel) + 0x288 + panel->rel_288
                 : nullptr;

        EmitEffectEntries(node);
        s108 = panel->field_2b4;
        s118 = panel->field_2bc;
        s11c = panel->field_2c0;
        s120 = panel->field_2c8;
    } else {
        // 0x0036C984..0x0036C9C8: re-run when the sub-object's +0x10 bit
        // differs from the previously latched list flag.
        bool changed = false;
        u8* node = nullptr;
        if (frame->field_24 != 0) {
            u8* object = reinterpret_cast<u8*>(
                static_cast<std::uintptr_t>(frame->field_24));
            u8* inner = *reinterpret_cast<u8**>(object + 8);
            if (inner != nullptr) {
                const u32 relative =
                    *reinterpret_cast<u32*>(inner + 0x288);
                node = (relative != 0) ? inner + 0x288 + relative : nullptr;
                if (node != nullptr) {
                    const bool bit =
                        (*reinterpret_cast<u32*>(node + 0x10) & 0x20u) == 0;
                    changed = (bit != (list_flag != 0));
                }
            }
        }
        if (changed) {
            func_003744f8(frame, scene, &panel->field_24,
                          static_cast<u32>(list_flag));
            EmitEffectEntries(node);
            s108 = panel->field_2b4;
            s118 = panel->field_2bc;
            s11c = panel->field_2c0;
            s120 = panel->field_2c8;
        }
    }

    // 0x0036CA44..0x0036CA88: the +0x2CC pair.
    {
        u8* node = (panel->rel_288 != 0)
                 ? reinterpret_cast<u8*>(panel) + 0x288 + panel->rel_288
                 : nullptr;
        const u32 value = panel->field_2cc;
        if (!(value != 0 && s128 == value)) {
            const u32 first = *reinterpret_cast<u32*>(node + 0xD4);
            const u32 second = *reinterpret_cast<u32*>(node + 0xD8);
            EmitPair(first, second);
            s128 = value;
        }
    }

    // 0x0036CA8C..0x0036CDA0: the +0x2D0 state block.
    if (!(panel->field_2d0 != 0 && s124 == panel->field_2d0)) {
        EmitPanelStateCommand(panel);
        s124 = panel->field_2d0;
    }

    // 0x0036CDA4..0x0036CDFC: write the snapshot back.
    frame->field_100 = s100;
    frame->field_104 = s104;
    frame->field_108 = s108;
    frame->field_10c = s10c;
    frame->field_110 = s110;
    frame->field_114 = s114;
    frame->field_118 = s118;
    frame->field_11c = s11c;
    frame->field_120 = s120;
    frame->field_124 = s124;
    frame->field_128 = s128;
}

// ---------------------------------------------------------------------------
// 0x00368CF8: multi-panel variant.  The same command blocks are emitted, but
// the panel components are fetched from `slots` (+0x28..+0x50) instead of a
// single panel.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00368cf8, 3452)
void ui_func_00368cf8(void* unused, UiActionPanel* frame,
                      UiActionSlotTable* slots) {
    (void)unused;
    if (frame == nullptr || slots == nullptr) {
        return;
    }

    UiActionScene* scene = static_cast<UiActionScene*>(frame->scene);
    UiActionPanel* actor = slots->actor;         // +0x2A4
    UiActionPanel* work = slots->field_2c;       // +0x18 / +0x2A0 / +0x104
    UiActionPanel* work_b4 = slots->field_30;    // +0x2B4
    UiActionPanel* work_b8 = slots->field_34;    // +0x2B8
    UiActionPanel* work_a8 = slots->field_38;    // +0x2A8
    UiActionPanel* sprite = slots->field_3c;     // +0x2B0
    UiActionPanel* work_bc = slots->field_40;    // +0x2BC
    UiActionPanel* work_c0 = slots->field_44;    // +0x2C0
    UiActionPanel* work_c8 = slots->field_48;    // +0x2C8
    UiActionPanel* work_cc = slots->field_4c;    // +0x2CC
    UiActionPanel* work_d0 = slots->field_50;    // +0x2D0

    // 0x00368D0C..0x00368D44
    const s32 active_a = (frame->field_e8 != 0 || frame->field_e9 != 0) ? 1 : 0;
    const s32 active_b = (frame->field_ea != 0 || frame->field_eb != 0) ? 1 : 0;

    // 0x00368DA8..0x00368DD4
    if (actor != nullptr && frame->field_100 == actor->field_2a4 &&
        actor->field_2a4 != 0 && frame->field_13 == 0) {
        // unchanged
    } else {
        func_003748d4(scene, actor);
    }

    u32 s100 = actor->field_2a4;
    u32 s104 = frame->field_104;
    u32 s108 = frame->field_108;
    u32 s10c = frame->field_10c;
    u32 s110 = frame->field_110;
    u32 s114 = frame->field_114;
    u32 s118 = frame->field_118;
    u32 s11c = frame->field_11c;
    u32 s120 = frame->field_120;
    u32 s124 = frame->field_124;
    u32 s128 = frame->field_128;

    // 0x00368DD8..0x00368E38
    const s32 visible =
        ((work->field_18 & 1u) == 0 && frame->field_e4 != 0) ? 1 : 0;
    if (visible != 0) {
        scene->field_14 |= 0x8000u;
    } else {
        scene->field_14 &= ~0x8000u;
    }
    EmitPair(static_cast<u32>(visible ^ 1), 0x000101C6u);
    EmitPair(static_cast<u32>(visible), 0x0001008Fu);

    // 0x00368E40..0x00368F30
    if (!(work->field_2a0 != 0 && s104 == work->field_2a0 &&
          active_b == 0)) {
        UiActionList* list =
            static_cast<UiActionList*>(scene->list);
        if (list != nullptr) {
            if (list->field_68 > 0) {
                if (frame->field_e0 > 0 &&
                    (work->field_18 & 2u) == 0) {
                    work->field_14 |= 0x1000u;
                } else {
                    work->field_14 &= ~0x1000u;
                }
            }
            if ((list->flags & 4u) == 0) {
                if (frame->field_44 != 0 && (work->field_18 & 4u) == 0) {
                    work->field_14 |= 0x20u;
                    if ((work->field_18 & 8u) != 0) {
                        work->field_14 |= 0x40u;
                    } else {
                        work->field_14 &= ~0x40u;
                    }
                } else {
                    work->field_14 &= ~0x20u;
                }
            }
        }
        u32 value = 0;
        if ((work->field_18 & 0x10u) != 0 && frame->field_a0 != 0) {
            value = 5;
        }
        EmitPair(value, 0x000100E0u);
        s104 = work->field_2a0;
    }

    // 0x00368F34..0x003690A0: shader state from slots+0x34.
    if (!(work_b8 != nullptr && s10c == work_b8->field_2b8 &&
          work_b8->field_2b8 != 0)) {
        EmitShaderCommand(work_b8);
        s10c = work_b8->field_2b8;
    }

    // 0x003690A4..0x00369108
    if (!(work_a8 != nullptr && s110 == work_a8->field_2a8 &&
          work_a8->field_2a8 != 0)) {
        battle_func_00374e60(frame, scene);
        s110 = work_a8->field_2a8;
    }

    // 0x0036910C..0x003691B4
    if (!(sprite != nullptr && s114 == sprite->field_2b0 &&
          sprite->field_2b0 != 0)) {
        u32 mask = 0;
        for (s32 i = 0; i < 3; ++i) {
            u32* slot_field = &sprite->field_274 + i;
            const u32 relative = *slot_field;
            u8* object = (relative != 0)
                       ? reinterpret_cast<u8*>(slot_field) + relative
                       : nullptr;
            if (object == nullptr) {
                continue;
            }
            mask |= 1u << i;
            const u32 width = *reinterpret_cast<u32*>(object + 0x48);
            ui_func_002acd38(engine::g_GpuCommandCursor, object + 0x10, width);
            engine::g_GpuCommandCursor += (width & ~3u) / 4u;
        }
        EmitPair(mask | 0x10000u, 0x00050080u);
        s114 = sprite->field_2b0;
    }

    // 0x003691B8..0x003691F8
    s32 list_flag = ((work->field_18 & 1u) == 0) ? 1 : 0;
    if ((work->field_18 & 1u) == 0) {
        u8* node = (work_bc->rel_288 != 0)
                 ? reinterpret_cast<u8*>(work_bc) + 0x288
                       + work_bc->rel_288
                 : nullptr;
        u8* record = (node != nullptr) ? node + 0x10 : nullptr;
        list_flag = ((*reinterpret_cast<u32*>(record) & 0x20u) == 0) ? 1 : 0;

        if (!(work_bc->field_2bc != 0 && s118 == work_bc->field_2bc &&
              active_a == 0)) {
            // same descriptor as 0x0036C5E8
            u8* data = record;
            const u32 b4 = *reinterpret_cast<u32*>(data + 4) & 0xFFu;
            const u32 b8 = *reinterpret_cast<u32*>(data + 8) & 0xFFu;
            const u32 bc = *reinterpret_cast<u32*>(data + 0xC) & 0xFFu;
            const u32 b14 = data[0x14];
            const u32 mask = (b14 != 0) ? 0u : 0xFFFFFFFFu;
            const u32 bit0 = ((mask & bc) == 0) ? 1u : 0u;
            const u32 flags = *reinterpret_cast<u32*>(data);
            const u32 word0 = 0x80000000u | (b8 << 2) | (b4 << 4)
                            | (bc << 28)
                            | (((flags & 1u) == 0 ? 1u : 0u) << 27)
                            | ((bit0 ^ 1u) << 30) | 0x400u;
            const u32 word1 = (((flags & 2u) == 0 ? 1u : 0u) << 16)
                            | (((flags & 4u) == 0 ? 1u : 0u) << 17)
                            | ((b8 == 0 ? 1u : 0u) << 19)
                            | ((flags & 0x20u) == 0 ? 7u : 0u) << 20
                            | 0x40000u;
            u32* cursor = engine::g_GpuCommandCursor;
            cursor[0] = word0;
            cursor[1] = 0x000F01C3u;
            cursor[2] = word1;
            cursor[3] = 0x000401C4u;
            engine::g_GpuCommandCursor = cursor + 4;

            const u32 bit3 = (flags & 8u) == 0 ? 1u : 0u;
            const u32 bit4 = (flags & 0x10u) == 0 ? 1u : 0u;
            if (frame->field_e4 > 0) {
                u32* entries = reinterpret_cast<u32*>(
                    static_cast<std::uintptr_t>(frame->field_64));
                for (s32 i = 0; i < static_cast<s32>(frame->field_e4); ++i) {
                    u8* entry = reinterpret_cast<u8*>(
                        static_cast<std::uintptr_t>(entries[i]));
                    const u32 pair = *reinterpret_cast<u32*>(entry + 0x18) & 2u;
                    const u32 pair_bit = pair >> 1;
                    const u32 actor_state =
                        *reinterpret_cast<u32*>(entry + 0xB8);
                    u32 selected = 0;
                    if (actor_state == 0 ||
                        ((g_UiPanelVisibleMask_472100 >> i) & 1u) != 0) {
                        selected = 1;
                    }
                    u32 word = selected;
                    if (pair_bit != 0) {
                        word |= 2u;
                    }
                    if (bit3 != 0) {
                        word |= 4u;
                    }
                    if (bit4 != 0) {
                        word |= 8u;
                    }
                    EmitPair(word, 0x00010149u + (static_cast<u32>(i) << 4));
                }
            }
        }

        // 0x00369474..0x003694B4
        u8* node2 = (work_bc->rel_288 != 0)
                  ? reinterpret_cast<u8*>(work_bc) + 0x288
                        + work_bc->rel_288
                  : nullptr;
        u8* list_node = nullptr;
        if (node2 != nullptr) {
            const u32 rel_next = *reinterpret_cast<u32*>(node2 + 0x28);
            list_node = (rel_next != 0) ? node2 + 0x28 + rel_next : nullptr;
        }
        if (!(work_c0->field_2c0 != 0 && s11c == work_c0->field_2c0)) {
            func_00375504(record, list_node);
        }
    }

    // 0x003694B8..0x00369508
    bool skip_c8 = false;
    if (!(work_b4 != nullptr && s108 == work_b4->field_2b4 &&
          work_b4->field_2b4 != 0)) {
        func_003744f8(frame, scene, &work_b4->field_24,
                      static_cast<u32>(list_flag));
        s108 = work_b4->field_2b4;
    } else {
        // 0x00369568..0x003695B4: no change, so the 0x2C8 block is skipped.
        skip_c8 = true;
    }

    // 0x00369510..0x0036967C
    if (!skip_c8 &&
        !(work_c8 != nullptr && s120 == work_c8->field_2c8 &&
          work_c8->field_2c8 != 0)) {
        u8* node = (work_bc->rel_288 != 0)
                 ? reinterpret_cast<u8*>(work_bc) + 0x288
                       + work_bc->rel_288
                 : nullptr;
        EmitEffectEntries(node);
        s120 = work_c8->field_2c8;
    }

    // 0x0036967C..0x003696C0
    {
        u8* node = (work_cc->rel_288 != 0)
                 ? reinterpret_cast<u8*>(work_cc) + 0x288
                       + work_cc->rel_288
                 : nullptr;
        const u32 value = work_cc->field_2cc;
        if (!(value != 0 && s128 == value)) {
            EmitPair(*reinterpret_cast<u32*>(node + 0xD4),
                     *reinterpret_cast<u32*>(node + 0xD8));
            s128 = value;
        }
    }

    // 0x003696C4..0x003699DC
    if (!(work_d0 != nullptr && s124 == work_d0->field_2d0 &&
          work_d0->field_2d0 != 0)) {
        EmitPanelStateCommand(work_d0);
        s124 = work_d0->field_2d0;
    }

    // 0x003699E0..0x00369A38
    frame->field_100 = s100;
    frame->field_104 = s104;
    frame->field_108 = s108;
    frame->field_10c = s10c;
    frame->field_110 = s110;
    frame->field_114 = s114;
    frame->field_118 = s118;
    frame->field_11c = s11c;
    frame->field_120 = s120;
    frame->field_124 = s124;
    frame->field_128 = s128;
}

} // namespace smt4::ui
