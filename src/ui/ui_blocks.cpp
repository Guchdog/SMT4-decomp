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

    // 0x0027FBC8 (320 B): calibrated axis reader. A neutral sample can return
    // 1 and write zero outputs when the deadzone threshold is zero.
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
__attribute__((naked)) s32 ui_func_001fe590(void* scene) {
    asm volatile(
        ".word 0xe92d47f0\n"
        ".word 0xed2d8b08\n"
        ".word 0xe24dde11\n"
        ".word 0xe1a08000\n"
        ".word 0xeb030948\n"
        ".word 0xe1a04000\n"
        ".word 0xe5900034\n"
        ".word 0xe3a06000\n"
        ".word 0xe3500006\n"
        ".word 0x379ff100\n"
        ".word 0xea00036c\n"
        ".word 0x001fe5d4\n"
        ".word 0x001fe5dc\n"
        ".word 0x001fe5f4\n"
        ".word 0x001fe5fc\n"
        ".word 0x001ff370\n"
        ".word 0x001ff398\n"
        ".word 0xe3a00001\n"
        ".word 0xe5840034\n"
        ".word 0xe5d4003d\n"
        ".word 0xe3500000\n"
        ".word 0x13a00002\n"
        ".word 0x0a000360\n"
        ".word 0xe5840034\n"
        ".word 0xea00035e\n"
        ".word 0xe3a00003\n"
        ".word 0xeafffffb\n"
        ".word 0xe3a00007\n"
        ".word 0xeb030c73\n"
        ".word 0xe3500000\n"
        ".word 0x13a06001\n"
        ".word 0x1a000003\n"
        ".word 0xe3a00008\n"
        ".word 0xeb030c6e\n"
        ".word 0xe3500000\n"
        ".word 0x13a06002\n"
        ".word 0xe5d4003d\n"
        ".word 0xe3500000\n"
        ".word 0x1594006c\n"
        ".word 0x13500000\n"
        ".word 0x0a00034e\n"
        ".word 0xe5940038\n"
        ".word 0xed9f8af4\n"
        ".word 0xe3100004\n"
        ".word 0x0a00001a\n"
        ".word 0xe3a02000\n"
        ".word 0xe28d1004\n"
        ".word 0xe1a0000d\n"
        ".word 0xeb02055c\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000013\n"
        ".word 0xe59d0000\n"
        ".word 0xe35004bf\n"
        ".word 0x8d940a12\n"
        ".word 0x8e300a48\n"
        ".word 0x8a000003\n"
        ".word 0xe350043f\n"
        ".word 0xcd940a12\n"
        ".word 0xce300a08\n"
        ".word 0xda000000\n"
        ".word 0xed840a12\n"
        ".word 0xe59d0004\n"
        ".word 0xe35004bf\n"
        ".word 0x8d940a13\n"
        ".word 0x8e300a08\n"
        ".word 0x8a000003\n"
        ".word 0xe350043f\n"
        ".word 0xcd940a13\n"
        ".word 0xce300a48\n"
        ".word 0xda000000\n"
        ".word 0xed840a13\n"
        ".word 0xeddf8ad7\n"
        ".word 0xe59f735c\n"
        ".word 0xedcd8a00\n"
        ".word 0xedcd8a01\n"
        ".word 0xedcd8a02\n"
        ".word 0xedcd8a03\n"
        ".word 0xe5970000\n"
        ".word 0xe3a01000\n"
        ".word 0xeb030d99\n"
        ".word 0xe2840048\n"
        ".word 0xe59f533c\n"
        ".word 0xed9faacf\n"
        ".word 0xed9fbacf\n"
        ".word 0xe28d9008\n"
        ".word 0xec900a04\n"
        ".word 0xe5d4003c\n"
        ".word 0xe7950200\n"
        ".word 0xe20028ff\n"
        ".word 0xe1a01c20\n"
        ".word 0xee021a90\n"
        ".word 0xe2003cff\n"
        ".word 0xe1a02822\n"
        ".word 0xee032a10\n"
        ".word 0xe20000ff\n"
        ".word 0xe1a03423\n"
        ".word 0xee020a10\n"
        ".word 0xee033a90\n"
        ".word 0xeeb84a62\n"
        ".word 0xeef82a43\n"
        ".word 0xe1a0300d\n"
        ".word 0xe1a02003\n"
        ".word 0xeeb83a42\n"
        ".word 0xeef83a63\n"
        ".word 0xe1a01002\n"
        ".word 0xe1a00001\n"
        ".word 0xee242a0a\n"
        ".word 0xee224a8a\n"
        ".word 0xee233a0a\n"
        ".word 0xee632a8a\n"
        ".word 0xed8d2a00\n"
        ".word 0xed8d4a01\n"
        ".word 0xeeb02a4b\n"
        ".word 0xecc92a02\n"
        ".word 0xeb02e4ab\n"
        ".word 0xe5d4003c\n"
        ".word 0xed940a14\n"
        ".word 0xeddfaaae\n"
        ".word 0xed942a12\n"
        ".word 0xe0850200\n"
        ".word 0xee301a6a\n"
        ".word 0xe590000c\n"
        ".word 0xee320a08\n"
        ".word 0xedd41a17\n"
        ".word 0xe20028ff\n"
        ".word 0xe2003cff\n"
        ".word 0xe1a01c20\n"
        ".word 0xe20000ff\n"
        ".word 0xee020a10\n"
        ".word 0xe1a03423\n"
        ".word 0xee033a90\n"
        ".word 0xe1a02822\n"
        ".word 0xee021a90\n"
        ".word 0xee032a10\n"
        ".word 0xeeb82a42\n"
        ".word 0xedd40a13\n"
        ".word 0xeef83a63\n"
        ".word 0xeef81ae1\n"
        ".word 0xeef82a62\n"
        ".word 0xeeb83a43\n"
        ".word 0xee700a88\n"
        ".word 0xe1a0300d\n"
        ".word 0xe1a02003\n"
        ".word 0xe1a01002\n"
        ".word 0xee222a0a\n"
        ".word 0xe1a00001\n"
        ".word 0xee633a8a\n"
        ".word 0xee622a8a\n"
        ".word 0xee233a0a\n"
        ".word 0xed8d2a03\n"
        ".word 0xeeb02a4b\n"
        ".word 0xeccd2a03\n"
        ".word 0xeb02e485\n"
        ".word 0xe5d4003c\n"
        ".word 0xe0850200\n"
        ".word 0xe5900004\n"
        ".word 0xe20028ff\n"
        ".word 0xe2001cff\n"
        ".word 0xe1a02822\n"
        ".word 0xe1a03c20\n"
        ".word 0xee002a90\n"
        ".word 0xe1a01421\n"
        ".word 0xee013a10\n"
        ".word 0xe20000ff\n"
        ".word 0xee011a90\n"
        ".word 0xee000a10\n"
        ".word 0xeef82a60\n"
        ".word 0xe28d0008\n"
        ".word 0xeeb82a41\n"
        ".word 0xe1a0300d\n"
        ".word 0xeef80a61\n"
        ".word 0xeeb81a40\n"
        ".word 0xe1a02003\n"
        ".word 0xe1a01002\n"
        ".word 0xee621a0a\n"
        ".word 0xee222a8a\n"
        ".word 0xee200a8a\n"
        ".word 0xee610a0a\n"
        ".word 0xec800a02\n"
        ".word 0xe1a00001\n"
        ".word 0xeccd1a02\n"
        ".word 0xeeb02a4b\n"
        ".word 0xedd4ba14\n"
        ".word 0xedd49a12\n"
        ".word 0xed949a13\n"
        ".word 0xeef01a68\n"
        ".word 0xeeb01a6b\n"
        ".word 0xeef00a49\n"
        ".word 0xeeb00a69\n"
        ".word 0xeb02e460\n"
        ".word 0xed940a15\n"
        ".word 0xe1a0300d\n"
        ".word 0xeeb02a4b\n"
        ".word 0xee300a68\n"
        ".word 0xe1a02003\n"
        ".word 0xeef01a68\n"
        ".word 0xeeb01a6b\n"
        ".word 0xe1a01002\n"
        ".word 0xe1a00001\n"
        ".word 0xee700a09\n"
        ".word 0xeeb00a69\n"
        ".word 0xeb02e454\n"
        ".word 0xe2849048\n"
        ".word 0xedd4ba15\n"
        ".word 0xe1a0300d\n"
        ".word 0xec999a02\n"
        ".word 0xeeb02a4b\n"
        ".word 0xe1a02003\n"
        ".word 0xeef01a6b\n"
        ".word 0xeeb01a68\n"
        ".word 0xeef00a69\n"
        ".word 0xeeb00a49\n"
        ".word 0xe1a01002\n"
        ".word 0xe1a00001\n"
        ".word 0xeb02e447\n"
        ".word 0xed940a14\n"
        ".word 0xe1a0300d\n"
        ".word 0xeeb02a4b\n"
        ".word 0xee300a68\n"
        ".word 0xe1a02003\n"
        ".word 0xeef01a6b\n"
        ".word 0xeeb01a68\n"
        ".word 0xeef00a69\n"
        ".word 0xe1a01002\n"
        ".word 0xe1a00001\n"
        ".word 0xee300a09\n"
        ".word 0xeb02e43b\n"
        ".word 0xec990a02\n"
        ".word 0xe284108c\n"
        ".word 0xe3a00000\n"
        ".word 0xee300a08\n"
        ".word 0xee700a88\n"
        ".word 0xeb02c1a3\n"
        ".word 0xe5940038\n"
        ".word 0xe3100001\n"
        ".word 0x1a00003d\n"
        ".word 0xedcd8a00\n"
        ".word 0xedcd8a01\n"
        ".word 0xedcd8a02\n"
        ".word 0xedcd8a03\n"
        ".word 0xe5970000\n"
        ".word 0xe3a01000\n"
        ".word 0xeb030cf6\n"
        ".word 0xe1c405dc\n"
        ".word 0xedd40a13\n"
        ".word 0xedd42a14\n"
        ".word 0xee000a10\n"
        ".word 0xe0010091\n"
        ".word 0xee700a88\n"
        ".word 0xee010a90\n"
        ".word 0xe5d4003c\n"
        ".word 0xeeb80ac0\n"
        ".word 0xee011a10\n"
        ".word 0xed942a12\n"
        ".word 0xe0850200\n"
        ".word 0xeef81ae1\n"
        ".word 0xe5900008\n"
        ".word 0xeeb83ac1\n"
        ".word 0xe20018ff\n"
        ".word 0xe1a02c20\n"
        ".word 0xee700a20\n"
        ".word 0xee321aea\n"
        ".word 0xe200ccff\n"
        ".word 0xe20030ff\n"
        ".word 0xee320a08\n"
        ".word 0xe1a00821\n"
        ".word 0xee022a90\n"
        ".word 0xee020a10\n"
        ".word 0xe1a0142c\n"
        ".word 0xee031a90\n"
        ".word 0xee730a20\n"
        ".word 0xee033a10\n"
        ".word 0xeef82a62\n"
        ".word 0xeeb82a42\n"
        ".word 0xe1a0300d\n"
        ".word 0xe1a02003\n"
        ".word 0xe1a01002\n"
        ".word 0xeeb84a43\n"
        ".word 0xeeb83a63\n"
        ".word 0xee622a8a\n"
        ".word 0xee222a0a\n"
        ".word 0xee643a0a\n"
        ".word 0xee233a0a\n"
        ".word 0xedcd2a00\n"
        ".word 0xed8d2a01\n"
        ".word 0xeeb02a4b\n"
        ".word 0xea000006\n"
        ".word 0x40000000\n"
        ".word 0x3f800000\n"
        ".word 0x0044ea00\n"
        ".word 0x00409b60\n"
        ".word 0x3b808081\n"
        ".word 0x00000000\n"
        ".word 0x40800000\n"
        ".word 0xe28d9008\n"
        ".word 0xe1a00001\n"
        ".word 0xec893a02\n"
        ".word 0xeb02e3f4\n"
        ".word 0xe3e0a000\n"
        ".word 0xe58da108\n"
        ".word 0xe58da10c\n"
        ".word 0xedd40a13\n"
        ".word 0xed940a17\n"
        ".word 0xed941a12\n"
        ".word 0xee700a88\n"
        ".word 0xeeb80ac0\n"
        ".word 0xee718a08\n"
        ".word 0xee300a20\n"
        ".word 0xedcd8a40\n"
        ".word 0xed8d0a41\n"
        ".word 0xe5945000\n"
        ".word 0xe3550000\n"
        ".word 0x0a0000e8\n"
        ".word 0xe5950000\n"
        ".word 0xe5941064\n"
        ".word 0xe1510000\n"
        ".word 0xc5955018\n"
        ".word 0xca0000e1\n"
        ".word 0xe5942068\n"
        ".word 0xe0811002\n"
        ".word 0xe2411001\n"
        ".word 0xe1500001\n"
        ".word 0xca0000de\n"
        ".word 0xe594307c\n"
        ".word 0xe5957008\n"
        ".word 0xe3530000\n"
        ".word 0x0a00006c\n"
        ".word 0xe2872006\n"
        ".word 0xe28d1f43\n"
        ".word 0xe28d0c01\n"
        ".word 0xe12fff33\n"
        ".word 0xe5d70004\n"
        ".word 0xe3500005\n"
        ".word 0x379ff100\n"
        ".word 0xea0000c9\n"
        ".word 0x001fedf8\n"
        ".word 0x001feae4\n"
        ".word 0x001feb48\n"
        ".word 0x001febc8\n"
        ".word 0x001fec40\n"
        ".word 0xe2872c01\n"
        ".word 0xe2822006\n"
        ".word 0xe28f1fdf\n"
        ".word 0xe1a0000d\n"
        ".word 0xfa02ff40\n"
        ".word 0xe5941080\n"
        ".word 0xe1a0000d\n"
        ".word 0xe12fff31\n"
        ".word 0xed941a12\n"
        ".word 0xedd41a14\n"
        ".word 0xee000a90\n"
        ".word 0xed940a16\n"
        ".word 0xee311a21\n"
        ".word 0xe1a0200d\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe28d1f42\n"
        ".word 0xeef80ae0\n"
        ".word 0xe28d0c01\n"
        ".word 0xee311a48\n"
        ".word 0xee710a60\n"
        ".word 0xee300a80\n"
        ".word 0xed8d0a40\n"
        ".word 0xe594307c\n"
        ".word 0xe12fff33\n"
        ".word 0xea0000ab\n"
        ".word 0xe3a02c01\n"
        ".word 0xe28f1e32\n"
        ".word 0xe1a0000d\n"
        ".word 0xeb019001\n"
        ".word 0xe5941080\n"
        ".word 0xe1a0000d\n"
        ".word 0xe12fff31\n"
        ".word 0xed941a12\n"
        ".word 0xedd41a14\n"
        ".word 0xee000a10\n"
        ".word 0xedd40a16\n"
        ".word 0xee311a21\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xee311a48\n"
        ".word 0xee310a40\n"
        ".word 0xee300a20\n"
        ".word 0xed8d0a40\n"
        ".word 0xe5970208\n"
        ".word 0xe594307c\n"
        ".word 0xe3500000\n"
        ".word 0x0a000004\n"
        ".word 0xe28f2fb5\n"
        ".word 0xe28d1f42\n"
        ".word 0xe28d0c01\n"
        ".word 0xe12fff33\n"
        ".word 0xea000090\n"
        ".word 0xe28f2fb2\n"
        ".word 0xe28d1f42\n"
        ".word 0xe28d0c01\n"
        ".word 0xe12fff33\n"
        ".word 0xea00008b\n"
        ".word 0xe5d70005\n"
        ".word 0xe5972208\n"
        ".word 0xe3500000\n"
        ".word 0x0a000013\n"
        ".word 0xe28f1fab\n"
        ".word 0xe1a0000d\n"
        ".word 0xfa02ff05\n"
        ".word 0xe5941080\n"
        ".word 0xe1a0000d\n"
        ".word 0xe12fff31\n"
        ".word 0xedd40a12\n"
        ".word 0xed941a14\n"
        ".word 0xee000a10\n"
        ".word 0xe1a0200d\n"
        ".word 0xee700a81\n"
        ".word 0xe28d1f42\n"
        ".word 0xe28d0c01\n"
        ".word 0xeeb80ac0\n"
        ".word 0xee700ac8\n"
        ".word 0xee300ac0\n"
        ".word 0xed8d0a40\n"
        ".word 0xe594307c\n"
        ".word 0xe12fff33\n"
        ".word 0xea000073\n"
        ".word 0xe28f1f99\n"
        ".word 0xe1a0000d\n"
        ".word 0xfa02fef1\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffffe8\n"
        ".word 0xed970a83\n"
        ".word 0xe28f1e25\n"
        ".word 0xe1a0000d\n"
        ".word 0xeeb70ac0\n"
        ".word 0xec532b10\n"
        ".word 0xfa02fee8\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffffdf\n"
        ".word 0xeeb00a68\n"
        ".word 0xeddd0a41\n"
        ".word 0xe2871006\n"
        ".word 0xe3a00000\n"
        ".word 0xeb02c0d3\n"
        ".word 0xedd40a12\n"
        ".word 0xed940a14\n"
        ".word 0xee300a80\n"
        ".word 0xee300a48\n"
        ".word 0xed8d0a40\n"
        ".word 0xe5d70004\n"
        ".word 0xe3500005\n"
        ".word 0x379ff100\n"
        ".word 0xea000056\n"
        ".word 0x001fedf8\n"
        ".word 0x001fecb0\n"
        ".word 0x001fecfc\n"
        ".word 0x001fed34\n"
        ".word 0x001fedb4\n"
        ".word 0xe2870c01\n"
        ".word 0xe2800006\n"
        ".word 0xe1a07000\n"
        ".word 0xeb031173\n"
        ".word 0xe5941058\n"
        ".word 0xe2800001\n"
        ".word 0xeddd0a40\n"
        ".word 0xe1a02007\n"
        ".word 0xe0000190\n"
        ".word 0xe28f1f72\n"
        ".word 0xee000a10\n"
        ".word 0xe1a0000d\n"
        ".word 0xeeb80a40\n"
        ".word 0xee300ac0\n"
        ".word 0xed8d0a40\n"
        ".word 0xfa02fec2\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea00001b\n"
        ".word 0xe5940058\n"
        ".word 0xe0800080\n"
        ".word 0xe1a00080\n"
        ".word 0xee000a90\n"
        ".word 0xeef80a60\n"
        ".word 0xee300a60\n"
        ".word 0xed8d0a40\n"
        ".word 0xe5970208\n"
        ".word 0xeddd0a41\n"
        ".word 0xe3500000\n"
        ".word 0x028f1f5f\n"
        ".word 0x128f1d06\n"
        ".word 0xe3a00000\n"
        ".word 0xea000011\n"
        ".word 0xe5d70005\n"
        ".word 0xe3500000\n"
        ".word 0xe5940058\n"
        ".word 0x0a00000f\n"
        ".word 0xe0801080\n"
        ".word 0xe0810180\n"
        ".word 0xee000a90\n"
        ".word 0xe28f1e16\n"
        ".word 0xe1a0000d\n"
        ".word 0xeef80ae0\n"
        ".word 0xee300a60\n"
        ".word 0xed8d0a40\n"
        ".word 0xe5972208\n"
        ".word 0xfa02fea3\n"
        ".word 0xe28d2c01\n"
        ".word 0xe1a0100d\n"
        ".word 0xec920a02\n"
        ".word 0xe3a00000\n"
        ".word 0xeb02c091\n"
        ".word 0xea00001c\n"
        ".word 0xe0800180\n"
        ".word 0xee000a90\n"
        ".word 0xe28f1c01\n"
        ".word 0xe1a0000d\n"
        ".word 0xeef80ae0\n"
        ".word 0xee300a60\n"
        ".word 0xed8d0a40\n"
        ".word 0xe5972208\n"
        ".word 0xfa02fe94\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffffed\n"
        ".word 0xe5940058\n"
        ".word 0xe28f10dc\n"
        ".word 0xe1a00180\n"
        ".word 0xee000a90\n"
        ".word 0xe1a0000d\n"
        ".word 0xeef80ae0\n"
        ".word 0xee300a60\n"
        ".word 0xed8d0a40\n"
        ".word 0xed970a83\n"
        ".word 0xeeb70ac0\n"
        ".word 0xec532b10\n"
        ".word 0xfa02fe85\n"
        ".word 0xe28d2c01\n"
        ".word 0xe1a0100d\n"
        ".word 0xec920a02\n"
        ".word 0xe3a00000\n"
        ".word 0xeb02c073\n"
        ".word 0xedcd8a40\n"
        ".word 0xed940a17\n"
        ".word 0xeddd0a41\n"
        ".word 0xeeb80ac0\n"
        ".word 0xee300a80\n"
        ".word 0xed8d0a41\n"
        ".word 0xe5955018\n"
        ".word 0xe3550000\n"
        ".word 0x1affff16\n"
        ".word 0xe5940038\n"
        ".word 0xe3100002\n"
        ".word 0x1a000151\n"
        ".word 0xe5940040\n"
        ".word 0xe3500000\n"
        ".word 0xc2400001\n"
        ".word 0xc5840040\n"
        ".word 0xca00014c\n"
        ".word 0xe284000c\n"
        ".word 0xeb00015f\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a00001b\n"
        ".word 0xe284000c\n"
        ".word 0xe5900024\n"
        ".word 0xe5840064\n"
        ".word 0xe284000c\n"
        ".word 0xe5900020\n"
        ".word 0xe5840060\n"
        ".word 0xe320f000\n"
        ".word 0xea00013f\n"
        ".word 0x0073255f\n"
        ".word 0x4c41465f\n"
        ".word 0x00004553\n"
        ".word 0x52542020\n"
        ".word 0x00004555\n"
        ".word 0x4c414620\n"
        ".word 0x00004553\n"
        ".word 0x30257830\n"
        ".word 0x00005838\n"
        ".word 0x64382520\n"
        ".word 0x00000000\n"
        ".word 0x2e342520\n"
        ".word 0x00006632\n"
        ".word 0x00732520\n"
        ".word 0x534c4146\n"
        ".word 0x00000045\n"
        ".word 0x45555254\n"
        ".word 0x00000000\n"
        ".word 0x25783020\n"
        ".word 0x00583830\n"
        ".word 0xe3a00003\n"
        ".word 0xeb02e858\n"
        ".word 0xe59f734c\n"
        ".word 0xe59f934c\n"
        ".word 0xed9f8ad3\n"
        ".word 0xe3500000\n"
        ".word 0x0a000064\n"
        ".word 0xe1a00008\n"
        ".word 0xeb0306f8\n"
        ".word 0xe5901060\n"
        ".word 0xe5900064\n"
        ".word 0xe0815000\n"
        ".word 0xe1a00008\n"
        ".word 0xeb0306f3\n"
        ".word 0xe5900000\n"
        ".word 0xe3500000\n"
        ".word 0x0a000008\n"
        ".word 0xe5902000\n"
        ".word 0xe5901008\n"
        ".word 0xe1520005\n"
        ".word 0x1a000001\n"
        ".word 0xe591a000\n"
        ".word 0xea000002\n"
        ".word 0xe5900018\n"
        ".word 0xe3500000\n"
        ".word 0x1afffff6\n"
        ".word 0xe1a0100a\n"
        ".word 0xe1a00008\n"
        ".word 0xeb01582e\n"
        ".word 0xe1b05000\n"
        ".word 0xe320f000\n"
        ".word 0x0a00010b\n"
        ".word 0xe5d50004\n"
        ".word 0xe3500005\n"
        ".word 0x379ff100\n"
        ".word 0xea000107\n"
        ".word 0x001ff370\n"
        ".word 0x001ff370\n"
        ".word 0x001fef64\n"
        ".word 0x001fef80\n"
        ".word 0x001feff4\n"
        ".word 0xe5950208\n"
        ".word 0xe3500000\n"
        ".word 0x1a000001\n"
        ".word 0xe3a00001\n"
        ".word 0xea00001c\n"
        ".word 0xe3a00000\n"
        ".word 0xea00001a\n"
        ".word 0xe3560001\n"
        ".word 0xe3a00001\n"
        ".word 0x03a0000a\n"
        ".word 0x0a00000a\n"
        ".word 0xe3560002\n"
        ".word 0x03a00064\n"
        ".word 0x0a000007\n"
        ".word 0xe3560003\n"
        ".word 0x03a00ffa\n"
        ".word 0x0a000004\n"
        ".word 0xe3560004\n"
        ".word 0x01a00007\n"
        ".word 0x0a000001\n"
        ".word 0xe3560005\n"
        ".word 0x01a00009\n"
        ".word 0xe5952208\n"
        ".word 0xe5951214\n"
        ".word 0xe0800002\n"
        ".word 0xe1500001\n"
        ".word 0xe5850208\n"
        ".word 0xda0000e6\n"
        ".word 0xe3a00003\n"
        ".word 0xeb0303f7\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000068\n"
        ".word 0xea000065\n"
        ".word 0xe5850208\n"
        ".word 0xea0000de\n"
        ".word 0xe3560001\n"
        ".word 0xe3a00001\n"
        ".word 0x03a0000a\n"
        ".word 0x0a00000a\n"
        ".word 0xe3560002\n"
        ".word 0x03a00064\n"
        ".word 0x0a000007\n"
        ".word 0xe3560003\n"
        ".word 0x03a00ffa\n"
        ".word 0x0a000004\n"
        ".word 0xe3560004\n"
        ".word 0x01a00007\n"
        ".word 0x0a000001\n"
        ".word 0xe3560005\n"
        ".word 0x01a00009\n"
        ".word 0xee000a90\n"
        ".word 0xed950a83\n"
        ".word 0xed951a85\n"
        ".word 0xeef80ae0\n"
        ".word 0xee000a88\n"
        ".word 0xeef80ac1\n"
        ".word 0xed850a83\n"
        ".word 0xeeb40ae0\n"
        ".word 0xeef1fa10\n"
        ".word 0xda0000c5\n"
        ".word 0xe3a00003\n"
        ".word 0xeb0303d6\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a00006e\n"
        ".word 0xea000066\n"
        ".word 0xe3a00004\n"
        ".word 0xeb02e7ec\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a00006c\n"
        ".word 0xe1a00008\n"
        ".word 0xeb03068e\n"
        ".word 0xe5901060\n"
        ".word 0xe5900064\n"
        ".word 0xe0815000\n"
        ".word 0xe1a00008\n"
        ".word 0xeb030689\n"
        ".word 0xe5900000\n"
        ".word 0xe3500000\n"
        ".word 0x0a000008\n"
        ".word 0xe5902000\n"
        ".word 0xe5901008\n"
        ".word 0xe1520005\n"
        ".word 0x1a000001\n"
        ".word 0xe591a000\n"
        ".word 0xea000002\n"
        ".word 0xe5900018\n"
        ".word 0xe3500000\n"
        ".word 0x1afffff6\n"
        ".word 0xe1a0100a\n"
        ".word 0xe1a00008\n"
        ".word 0xeb0157c4\n"
        ".word 0xe1b05000\n"
        ".word 0xe320f000\n"
        ".word 0x0a0000a1\n"
        ".word 0xe5d50004\n"
        ".word 0xe3500005\n"
        ".word 0x379ff100\n"
        ".word 0xea00009d\n"
        ".word 0x001ff370\n"
        ".word 0x001ff370\n"
        ".word 0x001ff10c\n"
        ".word 0x001ff11c\n"
        ".word 0x001ff194\n"
        ".word 0xe5950208\n"
        ".word 0xe3500000\n"
        ".word 0x1affff97\n"
        ".word 0xeaffff94\n"
        ".word 0xe3560001\n"
        ".word 0xe3a00001\n"
        ".word 0x03a0000a\n"
        ".word 0x0a00000a\n"
        ".word 0xe3560002\n"
        ".word 0x03a00064\n"
        ".word 0x0a000007\n"
        ".word 0xe3560003\n"
        ".word 0x03a00ffa\n"
        ".word 0x0a000004\n"
        ".word 0xe3560004\n"
        ".word 0x01a00007\n"
        ".word 0x0a000001\n"
        ".word 0xe3560005\n"
        ".word 0x01a00009\n"
        ".word 0xe5952208\n"
        ".word 0xe5951210\n"
        ".word 0xe0420000\n"
        ".word 0xe1500001\n"
        ".word 0xe5850208\n"
        ".word 0xaa00007f\n"
        ".word 0xe3a00004\n"
        ".word 0xeb030390\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000001\n"
        ".word 0xe5950214\n"
        ".word 0xeaffff97\n"
        ".word 0xe5950210\n"
        ".word 0xeaffff95\n"
        ".word 0xe3560001\n"
        ".word 0xe3a00001\n"
        ".word 0x03a0000a\n"
        ".word 0x0a00000a\n"
        ".word 0xe3560002\n"
        ".word 0x03a00064\n"
        ".word 0x0a000007\n"
        ".word 0xe3560003\n"
        ".word 0x03a00ffa\n"
        ".word 0x0a000004\n"
        ".word 0xe3560004\n"
        ".word 0x01a00007\n"
        ".word 0x0a000001\n"
        ".word 0xe3560005\n"
        ".word 0x01a00009\n"
        ".word 0xee000a90\n"
        ".word 0xed950a83\n"
        ".word 0xed951a84\n"
        ".word 0xeef80ae0\n"
        ".word 0xee000ac8\n"
        ".word 0xeef80ac1\n"
        ".word 0xed850a83\n"
        ".word 0xeeb40ae0\n"
        ".word 0xeef1fa10\n"
        ".word 0x2a00005d\n"
        ".word 0xe3a00004\n"
        ".word 0xeb03036e\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000006\n"
        ".word 0xed950a85\n"
        ".word 0xeeb80ac0\n"
        ".word 0xed850a83\n"
        ".word 0xea000054\n"
        ".word 0x00002710\n"
        ".word 0x000186a0\n"
        ".word 0x3c23d70a\n"
        ".word 0xed950a84\n"
        ".word 0xeeb80ac0\n"
        ".word 0xed850a83\n"
        ".word 0xea00004d\n"
        ".word 0xe3a00000\n"
        ".word 0xeb03035e\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000048\n"
        ".word 0xe1a00008\n"
        ".word 0xeb03061c\n"
        ".word 0xe5901060\n"
        ".word 0xe5900064\n"
        ".word 0xe0815000\n"
        ".word 0xe1a00008\n"
        ".word 0xeb030617\n"
        ".word 0xe5900000\n"
        ".word 0xe3500000\n"
        ".word 0x0a000008\n"
        ".word 0xe5901000\n"
        ".word 0xe5902008\n"
        ".word 0xe1510005\n"
        ".word 0x1a000001\n"
        ".word 0xe592a000\n"
        ".word 0xea000002\n"
        ".word 0xe5900018\n"
        ".word 0xe3500000\n"
        ".word 0x1afffff6\n"
        ".word 0xe1a0100a\n"
        ".word 0xe1a00008\n"
        ".word 0xeb015752\n"
        ".word 0xe3500000\n"
        ".word 0x1590121c\n"
        ".word 0x13510000\n"
        ".word 0x0a00002e\n"
        ".word 0xe5d02004\n"
        ".word 0xe3520005\n"
        ".word 0x379ff102\n"
        ".word 0xea00002a\n"
        ".word 0x001ff2d8\n"
        ".word 0x001ff2fc\n"
        ".word 0x001ff328\n"
        ".word 0x001ff328\n"
        ".word 0x001ff34c\n"
        ".word 0xe5902218\n"
        ".word 0xe3520000\n"
        ".word 0x03a00000\n"
        ".word 0x0a000020\n"
        ".word 0xe3a01000\n"
        ".word 0xe88d0006\n"
        ".word 0xe590121c\n"
        ".word 0xe1a0000d\n"
        ".word 0xea00001b\n"
        ".word 0xe5902218\n"
        ".word 0xe3520000\n"
        ".word 0x02800c01\n"
        ".word 0x02800006\n"
        ".word 0x0a000016\n"
        ".word 0xe2801c01\n"
        ".word 0xe2811006\n"
        ".word 0xe88d0006\n"
        ".word 0xe590121c\n"
        ".word 0xe1a0000d\n"
        ".word 0xea000010\n"
        ".word 0xe5902218\n"
        ".word 0xe3520000\n"
        ".word 0x02800f82\n"
        ".word 0x0a00000c\n"
        ".word 0xe2801f82\n"
        ".word 0xe88d0006\n"
        ".word 0xe590121c\n"
        ".word 0xe1a0000d\n"
        ".word 0xea000007\n"
        ".word 0xe5902218\n"
        ".word 0xe3520000\n"
        ".word 0x02800f83\n"
        ".word 0x0a000003\n"
        ".word 0xe2801f83\n"
        ".word 0xe88d0006\n"
        ".word 0xe590121c\n"
        ".word 0xe1a0000d\n"
        ".word 0xe12fff31\n"
        ".word 0xe5941074\n"
        ".word 0xe3510000\n"
        ".word 0x15940034\n"
        ".word 0x13500002\n"
        ".word 0xc5940078\n"
        ".word 0xc12fff31\n"
        ".word 0xe28dde11\n"
        ".word 0xe3a00000\n"
        ".word 0xecbd8b08\n"
        ".word 0xe8bd87f0\n"
        ".word 0xe28dde11\n"
        ".word 0xe3e00000\n"
        ".word 0xecbd8b08\n"
        ".word 0xe8bd87f0\n"
    );
}
#if 0
// Original partial readable draft retained for reconstruction; not compiled.
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
#endif

// ---------------------------------------------------------------------------
// 0x002ED5D0: battle command panel.
//
// The routine renders one of seven command-panel states (work+0x04) with five
// sub-layouts for state 0 (work+0x08).  It brackets its drawing with the two
// GPU render-state stacks at 0x0044EA00+0x124C and +0x12AC and ends both
// passes through 0x002C1B64 / 0x002C1ABC.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002ed5d0, 3584)
__attribute__((naked)) s32 ui_func_002ed5d0(void* scene) {
    asm volatile(
        ".word 0xe92d4ff0\n"
        ".word 0xed2d8b08\n"
        ".word 0xe24dd014\n"
        ".word 0xebff4d39\n"
        ".word 0xe59f83f8\n"
        ".word 0xe1a05000\n"
        ".word 0xe5980000\n"
        ".word 0xebff596d\n"
        ".word 0xe5984000\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a00001\n"
        ".word 0xebff625e\n"
        ".word 0xe2844a01\n"
        ".word 0xe2844f93\n"
        ".word 0xe3a07000\n"
        ".word 0xe5941000\n"
        ".word 0xe2812001\n"
        ".word 0xe0843101\n"
        ".word 0xe5931008\n"
        ".word 0xe0843102\n"
        ".word 0xe5842000\n"
        ".word 0xe5830008\n"
        ".word 0xe5d42018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c47018\n"
        ".word 0xe5950004\n"
        ".word 0xeddfaae5\n"
        ".word 0xed9faae5\n"
        ".word 0xe3500000\n"
        ".word 0xe3a0a00b\n"
        ".word 0x0a000027\n"
        ".word 0xe58d7000\n"
        ".word 0xe5953020\n"
        ".word 0xe3a0203c\n"
        ".word 0xe3a01050\n"
        ".word 0xe3a00028\n"
        ".word 0xebfe04a6\n"
        ".word 0xee000a10\n"
        ".word 0xe5984000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe3a00006\n"
        ".word 0xeeb80ac0\n"
        ".word 0xee208a2a\n"
        ".word 0xebff6243\n"
        ".word 0xe2844a01\n"
        ".word 0xe2844fab\n"
        ".word 0xe5941000\n"
        ".word 0xe0842101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d42018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c47018\n"
        ".word 0xeeb00a48\n"
        ".word 0xebff480f\n"
        ".word 0xe3a0000b\n"
        ".word 0xe58d0004\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02001\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d7000\n"
        ".word 0xebff4799\n"
        ".word 0xeeb00a4a\n"
        ".word 0xe320f000\n"
        ".word 0xebff4804\n"
        ".word 0xe5984000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe3a00006\n"
        ".word 0xebff6224\n"
        ".word 0xe2844a01\n"
        ".word 0xe2844fab\n"
        ".word 0xe5941000\n"
        ".word 0xe0842101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d42018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c47018\n"
        ".word 0xe5950004\n"
        ".word 0xed9f9aa7\n"
        ".word 0xeddf8aa7\n"
        ".word 0xe3500000\n"
        ".word 0x05950008\n"
        ".word 0xeddf9aa5\n"
        ".word 0xe3a0600c\n"
        ".word 0x03500000\n"
        ".word 0x0a000018\n"
        ".word 0xe3a03000\n"
        ".word 0xe1a02003\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d6004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff4774\n"
        ".word 0xe595000c\n"
        ".word 0xe320f000\n"
        ".word 0xebfdaf57\n"
        ".word 0xeeb08a40\n"
        ".word 0xe3a01002\n"
        ".word 0xe3a0002d\n"
        ".word 0xebff47cb\n"
        ".word 0xee390a48\n"
        ".word 0xe1d010fa\n"
        ".word 0xeef01a4a\n"
        ".word 0xeeb01a69\n"
        ".word 0xee001a90\n"
        ".word 0xe595000c\n"
        ".word 0xee200a28\n"
        ".word 0xeef80ae0\n"
        ".word 0xeebd0ac0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xebff0c7a\n"
        ".word 0xe5950004\n"
        ".word 0xed9fba88\n"
        ".word 0xeddfba88\n"
        ".word 0xe3500007\n"
        ".word 0xe3a0b00e\n"
        ".word 0xe3a0900d\n"
        ".word 0x379ff100\n"
        ".word 0xea0002d0\n"
        ".word 0x002ed808\n"
        ".word 0x002ede2c\n"
        ".word 0x002edea8\n"
        ".word 0x002edf58\n"
        ".word 0x002ee004\n"
        ".word 0x002ee200\n"
        ".word 0x002ee398\n"
        ".word 0xe5950008\n"
        ".word 0xe3500005\n"
        ".word 0x379ff100\n"
        ".word 0xea0002c5\n"
        ".word 0x002ed82c\n"
        ".word 0x002ed8e8\n"
        ".word 0x002eda04\n"
        ".word 0x002eda80\n"
        ".word 0x002edb2c\n"
        ".word 0xed950a06\n"
        ".word 0xeeb01a4b\n"
        ".word 0xeef00a6b\n"
        ".word 0xeef81ac0\n"
        ".word 0xed9f0a6f\n"
        ".word 0xebfd6a0d\n"
        ".word 0xeeb08a40\n"
        ".word 0xed950a07\n"
        ".word 0xeeb01a4b\n"
        ".word 0xeeb0ba4a\n"
        ".word 0xeef81ac0\n"
        ".word 0xeeb00a6b\n"
        ".word 0xeef00a4b\n"
        ".word 0xebfe0445\n"
        ".word 0xeeb0aa40\n"
        ".word 0xe320f000\n"
        ".word 0xebff47a7\n"
        ".word 0xeebd0ac8\n"
        ".word 0xe3a03000\n"
        ".word 0xe1a02003\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xed8d0a00\n"
        ".word 0xe58d6004\n"
        ".word 0xebff4731\n"
        ".word 0xe595000c\n"
        ".word 0xe320f000\n"
        ".word 0xebfdaf14\n"
        ".word 0xeef0aa40\n"
        ".word 0xe3a01002\n"
        ".word 0xe3a0002d\n"
        ".word 0xebff4788\n"
        ".word 0xee390a6a\n"
        ".word 0xe1d010fa\n"
        ".word 0xeeb01a69\n"
        ".word 0xe595000c\n"
        ".word 0xee200a28\n"
        ".word 0xeefd1ac0\n"
        ".word 0xee001a10\n"
        ".word 0xeeb80ac0\n"
        ".word 0xee700a08\n"
        ".word 0xeeb80ae1\n"
        ".word 0xeef01a4a\n"
        ".word 0xebff0c36\n"
        ".word 0xeeb00a4b\n"
        ".word 0xe320f000\n"
        ".word 0xea000063\n"
        ".word 0xe3a0100b\n"
        ".word 0xe3a0002d\n"
        ".word 0xebff4776\n"
        ".word 0xe590000c\n"
        ".word 0xed950a06\n"
        ".word 0xeeb01a4b\n"
        ".word 0xe1d000f2\n"
        ".word 0xeef81ac0\n"
        ".word 0xeeb00a6b\n"
        ".word 0xee000a90\n"
        ".word 0xeef80ae0\n"
        ".word 0xebfe0418\n"
        ".word 0xeeb09a40\n"
        ".word 0xe3a0100b\n"
        ".word 0xe3a0002d\n"
        ".word 0xebff4769\n"
        ".word 0xe590000c\n"
        ".word 0xeebc8ac9\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a0200b\n"
        ".word 0xe1d010f2\n"
        ".word 0xe1d000f0\n"
        ".word 0xee001a10\n"
        ".word 0xee000a90\n"
        ".word 0xe3a0102d\n"
        ".word 0xed8d8a02\n"
        ".word 0xe3a00002\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeef80ae0\n"
        ".word 0xee300a49\n"
        ".word 0xeefc0ae0\n"
        ".word 0xee200a28\n"
        ".word 0xeebd0ac0\n"
        ".word 0xec8d0a02\n"
        ".word 0xe58d600c\n"
        ".word 0xebff0be3\n"
        ".word 0xe3a0100c\n"
        ".word 0xe3a0002d\n"
        ".word 0xebff4752\n"
        ".word 0xe590000c\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a0200c\n"
        ".word 0xe1d010f2\n"
        ".word 0xe1d000f0\n"
        ".word 0xee001a90\n"
        ".word 0xee000a10\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xeeb81ae0\n"
        ".word 0xeef80ac0\n"
        ".word 0xee311a49\n"
        ".word 0xeebc0ae0\n"
        ".word 0xee610a28\n"
        ".word 0xeefd0ae0\n"
        ".word 0xedcd0a00\n"
        ".word 0xed8d0a01\n"
        ".word 0xed8d8a02\n"
        ".word 0xe58d600c\n"
        ".word 0xebff0bcc\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000253\n"
        ".word 0x0044ea00\n"
        ".word 0x3c23d70a\n"
        ".word 0x3f800000\n"
        ".word 0x43a00000\n"
        ".word 0x3f000000\n"
        ".word 0x3f730000\n"
        ".word 0x41000000\n"
        ".word 0x00000000\n"
        ".word 0xc1800000\n"
        ".word 0xe3a02002\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a0102d\n"
        ".word 0xe1a00002\n"
        ".word 0xe58d6004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff46cd\n"
        ".word 0xed950a07\n"
        ".word 0xeeb01a4b\n"
        ".word 0xeef00a4a\n"
        ".word 0xeef81ac0\n"
        ".word 0xeeb00a6b\n"
        ".word 0xebfe03d0\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xebff4732\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a0200d\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0280\n"
        ".word 0xebff4680\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02010\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0280\n"
        ".word 0xebff467a\n"
        ".word 0xeeb00a4a\n"
        ".word 0xebff4724\n"
        ".word 0xea00022b\n"
        ".word 0xe3a02002\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a0102d\n"
        ".word 0xe1a00002\n"
        ".word 0xe58d6004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff46ae\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a0200d\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0280\n"
        ".word 0xebff466a\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02010\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0280\n"
        ".word 0xebff4664\n"
        ".word 0xed950a07\n"
        ".word 0xeeb01a4b\n"
        ".word 0xeef00a4a\n"
        ".word 0xeef81ac0\n"
        ".word 0xeeb00a6b\n"
        ".word 0xebfe03a5\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xebff4707\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a0200e\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0280\n"
        ".word 0xebff4655\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a0200f\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0280\n"
        ".word 0xebff464f\n"
        ".word 0xeeb00a4a\n"
        ".word 0xe320f000\n"
        ".word 0xeaffffd2\n"
        ".word 0xed950a07\n"
        ".word 0xeef0aa6b\n"
        ".word 0xeeb01a4b\n"
        ".word 0xeef81ac0\n"
        ".word 0xeef00a4a\n"
        ".word 0xeeb00a6a\n"
        ".word 0xebfe038c\n"
        ".word 0xeeb08a40\n"
        ".word 0xed9f0ab5\n"
        ".word 0xee280a00\n"
        ".word 0xebff46ed\n"
        ".word 0xe5984000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe3a00006\n"
        ".word 0xebff610d\n"
        ".word 0xe2844a01\n"
        ".word 0xe2844fab\n"
        ".word 0xe5941000\n"
        ".word 0xe0842101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d42018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c47018\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02001\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0480\n"
        ".word 0xebff4667\n"
        ".word 0xe5984000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe3a00006\n"
        ".word 0xebff60f5\n"
        ".word 0xe2844a01\n"
        ".word 0xe2844fab\n"
        ".word 0xe5941000\n"
        ".word 0xe0842101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d42018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c47018\n"
        ".word 0xeef0ba4a\n"
        ".word 0xeeb00a6b\n"
        ".word 0xebff46c0\n"
        ".word 0xe3a02002\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a0102d\n"
        ".word 0xe1a00002\n"
        ".word 0xe58d6004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff464b\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a0200d\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0280\n"
        ".word 0xebff4607\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a0200e\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0280\n"
        ".word 0xebff4601\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a0200f\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0280\n"
        ".word 0xebff45fb\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02010\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0280\n"
        ".word 0xebff45f5\n"
        ".word 0xeeb00a48\n"
        ".word 0xe320f000\n"
        ".word 0xebff469e\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02011\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0280\n"
        ".word 0xebff45ec\n"
        ".word 0xe3a0000f\n"
        ".word 0xe58d0004\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02013\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d7000\n"
        ".word 0xebff45e4\n"
        ".word 0xe3a00010\n"
        ".word 0xe58d0004\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02014\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d7000\n"
        ".word 0xebff45dc\n"
        ".word 0xe3a01017\n"
        ".word 0xe3a0002d\n"
        ".word 0xebff4675\n"
        ".word 0xe590000c\n"
        ".word 0xed950a06\n"
        ".word 0xeeb01a4b\n"
        ".word 0xe1d000f2\n"
        ".word 0xeef81ac0\n"
        ".word 0xeeb00a6a\n"
        ".word 0xee000a90\n"
        ".word 0xeef80ae0\n"
        ".word 0xebfe0317\n"
        ".word 0xeeb0aa40\n"
        ".word 0xe3a01017\n"
        ".word 0xe3a0002d\n"
        ".word 0xebff4668\n"
        ".word 0xe590000c\n"
        ".word 0xeefcaaca\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02017\n"
        ".word 0xe1d010f2\n"
        ".word 0xe1d000f0\n"
        ".word 0xee001a10\n"
        ".word 0xe3a0102d\n"
        ".word 0xedcdaa02\n"
        ".word 0xeef80ac0\n"
        ".word 0xee000a10\n"
        ".word 0xe3a00002\n"
        ".word 0xeeb80ac0\n"
        ".word 0xee700aca\n"
        ".word 0xee201aa8\n"
        ".word 0xeefc0ac0\n"
        ".word 0xeebd0ac1\n"
        ".word 0xec8d0a02\n"
        ".word 0xe58d600c\n"
        ".word 0xebff0ae2\n"
        ".word 0xe3a01018\n"
        ".word 0xe3a0002d\n"
        ".word 0xebff4651\n"
        ".word 0xe590000c\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02018\n"
        ".word 0xe1d010f2\n"
        ".word 0xe1d000f0\n"
        ".word 0xedcdaa02\n"
        ".word 0xee001a10\n"
        ".word 0xee000a90\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeef80ae0\n"
        ".word 0xee300a4a\n"
        ".word 0xeefc0ae0\n"
        ".word 0xee200a28\n"
        ".word 0xeebd0ac0\n"
        ".word 0xec8d0a02\n"
        ".word 0xe58d600c\n"
        ".word 0xebff0acc\n"
        ".word 0xe5950010\n"
        ".word 0xe320f000\n"
        ".word 0xebfdadc3\n"
        ".word 0xeeb0aa40\n"
        ".word 0xe3a01019\n"
        ".word 0xe3a0002d\n"
        ".word 0xebff4637\n"
        ".word 0xee390a4a\n"
        ".word 0xe1d010fa\n"
        ".word 0xeeb01a69\n"
        ".word 0xeef01a48\n"
        ".word 0xee001a90\n"
        ".word 0xe5950010\n"
        ".word 0xee200a28\n"
        ".word 0xeef80ae0\n"
        ".word 0xeebd0ac0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xebff0ae6\n"
        ".word 0xeeb00a6b\n"
        ".word 0xe320f000\n"
        ".word 0xeaffff13\n"
        ".word 0x3ecccccd\n"
        ".word 0xe3a0100b\n"
        ".word 0xe1a00005\n"
        ".word 0xebfd67ea\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02003\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d6004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff45c0\n"
        ".word 0xe5950010\n"
        ".word 0xe320f000\n"
        ".word 0xebfdada3\n"
        ".word 0xeeb08a40\n"
        ".word 0xe3a01019\n"
        ".word 0xe3a0002d\n"
        ".word 0xebff4617\n"
        ".word 0xee390a48\n"
        ".word 0xe1d010fa\n"
        ".word 0xeef01a4a\n"
        ".word 0xeeb01a69\n"
        ".word 0xee001a90\n"
        ".word 0xe5950010\n"
        ".word 0xee200a28\n"
        ".word 0xeef80ae0\n"
        ".word 0xeebd0ac0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xebff0ac6\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000121\n"
        ".word 0xe3a0100b\n"
        ".word 0xe1a00005\n"
        ".word 0xebfd67cb\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02003\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d6004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff45a1\n"
        ".word 0xe5950010\n"
        ".word 0xe320f000\n"
        ".word 0xebfdad84\n"
        ".word 0xeeb08a40\n"
        ".word 0xe3a01019\n"
        ".word 0xe3a0002d\n"
        ".word 0xebff45f8\n"
        ".word 0xee390a48\n"
        ".word 0xe1d010fa\n"
        ".word 0xeef01a4a\n"
        ".word 0xeeb01a69\n"
        ".word 0xee001a90\n"
        ".word 0xe5950010\n"
        ".word 0xee200a28\n"
        ".word 0xeef80ae0\n"
        ".word 0xeebd0ac0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xebff0aa7\n"
        ".word 0xed950a06\n"
        ".word 0xeeb01a4b\n"
        ".word 0xeef00a6b\n"
        ".word 0xeef81ac0\n"
        ".word 0xeeb00a49\n"
        ".word 0xebfd6852\n"
        ".word 0xeebd0ac0\n"
        ".word 0xe3a02004\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0880\n"
        ".word 0xee103a10\n"
        ".word 0xebff4582\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea0000f5\n"
        ".word 0xe3a0100b\n"
        ".word 0xe1a00005\n"
        ".word 0xebfd679f\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02004\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d6004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff4575\n"
        ".word 0xe59fa444\n"
        ".word 0xe3a04000\n"
        ".word 0xe5950018\n"
        ".word 0xe0800004\n"
        ".word 0xe1a01fc0\n"
        ".word 0xe0801ea1\n"
        ".word 0xe3c11007\n"
        ".word 0xe0406001\n"
        ".word 0xe2641029\n"
        ".word 0xe3a0002d\n"
        ".word 0xebff45c8\n"
        ".word 0xe1d010fa\n"
        ".word 0xe88d0202\n"
        ".word 0xe7da1006\n"
        ".word 0xe1d030f8\n"
        ".word 0xe3a00002\n"
        ".word 0xe281201f\n"
        ".word 0xe3a0102d\n"
        ".word 0xebff4524\n"
        ".word 0xe2844001\n"
        ".word 0xe3540008\n"
        ".word 0xbaffffeb\n"
        ".word 0xe3a0102a\n"
        ".word 0xe3a0002d\n"
        ".word 0xebff45ba\n"
        ".word 0xe1d010fa\n"
        ".word 0xe3a0201f\n"
        ".word 0xe88d0202\n"
        ".word 0xe1d030f8\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xebff4517\n"
        ".word 0xea0000ca\n"
        ".word 0xed950a07\n"
        ".word 0xeef0aa6b\n"
        ".word 0xeeb01a4b\n"
        ".word 0xeef81ac0\n"
        ".word 0xeeb00a4a\n"
        ".word 0xeef00a6a\n"
        ".word 0xebfe0256\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xebff45b8\n"
        ".word 0xe3a0100b\n"
        ".word 0xe1a00005\n"
        ".word 0xebfd676a\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02004\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d6004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff4540\n"
        ".word 0xe3a04000\n"
        ".word 0xe2641029\n"
        ".word 0xe3a0002d\n"
        ".word 0xebff459a\n"
        ".word 0xe1d010fa\n"
        ".word 0xe3a0201f\n"
        ".word 0xe88d0202\n"
        ".word 0xe1d030f8\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xebff44f7\n"
        ".word 0xe2844001\n"
        ".word 0xe3540008\n"
        ".word 0xbafffff2\n"
        ".word 0xe3a0102a\n"
        ".word 0xe3a0002d\n"
        ".word 0xebff458d\n"
        ".word 0xe1d010fa\n"
        ".word 0xe3a0201f\n"
        ".word 0xe88d0202\n"
        ".word 0xe1d030f8\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xebff44ea\n"
        ".word 0xeeb00a4a\n"
        ".word 0xe320f000\n"
        ".word 0xebff4593\n"
        ".word 0xed950a07\n"
        ".word 0xeeb01a4b\n"
        ".word 0xeef00a4a\n"
        ".word 0xeef81ac0\n"
        ".word 0xeeb00a6a\n"
        ".word 0xebfe0228\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xebff458a\n"
        ".word 0xe3a0102f\n"
        ".word 0xe3a0002d\n"
        ".word 0xebff4577\n"
        ".word 0xe1a04000\n"
        ".word 0xe590000c\n"
        ".word 0xed950a07\n"
        ".word 0xeeb01a4b\n"
        ".word 0xe1d000f2\n"
        ".word 0xeef81ac0\n"
        ".word 0xeeb00a6a\n"
        ".word 0xee000a90\n"
        ".word 0xeef80ae0\n"
        ".word 0xebfe0218\n"
        ".word 0xe594000c\n"
        ".word 0xeeb09a40\n"
        ".word 0xe3a0102e\n"
        ".word 0xe1d000f2\n"
        ".word 0xee000a10\n"
        ".word 0xe3a0002d\n"
        ".word 0xeef80ac0\n"
        ".word 0xeef89ac0\n"
        ".word 0xee300ac9\n"
        ".word 0xee208a28\n"
        ".word 0xebff4562\n"
        ".word 0xe590100c\n"
        ".word 0xeebd8ac8\n"
        ".word 0xe3a00010\n"
        ".word 0xe3a03000\n"
        ".word 0xe1d120f2\n"
        ".word 0xe1d110f0\n"
        ".word 0xee002a10\n"
        ".word 0xe3a0202e\n"
        ".word 0xed8d8a00\n"
        ".word 0xeef80ac0\n"
        ".word 0xee001a10\n"
        ".word 0xe3a0102d\n"
        ".word 0xeeb81ac0\n"
        ".word 0xee700ae9\n"
        ".word 0xee300a89\n"
        ".word 0xeefc0ac1\n"
        ".word 0xeebc0ac0\n"
        ".word 0xedcd0a01\n"
        ".word 0xed8d0a02\n"
        ".word 0xe58d000c\n"
        ".word 0xe3a00002\n"
        ".word 0xebff09da\n"
        ".word 0xe3a0102f\n"
        ".word 0xe3a0002d\n"
        ".word 0xebff4549\n"
        ".word 0xe590000c\n"
        ".word 0xeebc0ac9\n"
        ".word 0xe3a01011\n"
        ".word 0xe3a03000\n"
        ".word 0xe1d000f0\n"
        ".word 0xed8d8a00\n"
        ".word 0xe3a0202f\n"
        ".word 0xee000a90\n"
        ".word 0xe3a00002\n"
        ".word 0xeef80ae0\n"
        ".word 0xeefc0ae0\n"
        ".word 0xedcd0a01\n"
        ".word 0xed8d0a02\n"
        ".word 0xe58d100c\n"
        ".word 0xe3a0102d\n"
        ".word 0xebff09c7\n"
        ".word 0xeeb00a4a\n"
        ".word 0xe320f000\n"
        ".word 0xebff4546\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea00004b\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02005\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d6004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff44ce\n"
        ".word 0xed950a06\n"
        ".word 0xeeb01a4b\n"
        ".word 0xeef00a6b\n"
        ".word 0xeef81ac0\n"
        ".word 0xeeb00a49\n"
        ".word 0xebfd6791\n"
        ".word 0xeebd0ac0\n"
        ".word 0xe3a02030\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0280\n"
        ".word 0xee103a10\n"
        ".word 0xebff4483\n"
        ".word 0xe58d7000\n"
        ".word 0xe595301c\n"
        ".word 0xe3a0200c\n"
        ".word 0xe3a01064\n"
        ".word 0xe3a00000\n"
        ".word 0xebfe01a9\n"
        ".word 0xee000a10\n"
        ".word 0xe5984000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe3a00006\n"
        ".word 0xeeb80ac0\n"
        ".word 0xee208a2a\n"
        ".word 0xebff5f46\n"
        ".word 0xe2844a01\n"
        ".word 0xe2844fab\n"
        ".word 0xe5941000\n"
        ".word 0xe0842101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d42018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c47018\n"
        ".word 0xeeb00a48\n"
        ".word 0xebff4512\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02031\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0880\n"
        ".word 0xebff4460\n"
        ".word 0xeeb00a4a\n"
        ".word 0xe320f000\n"
        ".word 0xebff4509\n"
        ".word 0xe5984000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe3a00006\n"
        ".word 0xebff5f29\n"
        ".word 0xe2844a01\n"
        ".word 0xe2844fab\n"
        ".word 0xe5941000\n"
        ".word 0xe0842101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d42018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c47018\n"
        ".word 0xe5980000\n"
        ".word 0xe2804a01\n"
        ".word 0xe2844f93\n"
        ".word 0xe5940000\n"
        ".word 0xe0841100\n"
        ".word 0xe2400001\n"
        ".word 0xe5911008\n"
        ".word 0xe5840000\n"
        ".word 0xe0840100\n"
        ".word 0xe5d42018\n"
        ".word 0xe5900008\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c47018\n"
        ".word 0xe5980000\n"
        ".word 0xebff4df9\n"
        ".word 0xe5980000\n"
        ".word 0xe320f000\n"
        ".word 0xebff4dcc\n"
        ".word 0xe28dd014\n"
        ".word 0xe3a00000\n"
        ".word 0xecbd8b08\n"
        ".word 0xe8bd8ff0\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02005\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d6004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff4468\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02030\n"
        ".word 0xe3a0102d\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0280\n"
        ".word 0xeaffff0b\n"
        ".word 0x0043dc2c\n"
    );
}
#if 0
// Original partial readable draft retained for reconstruction; not compiled.
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
#endif

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
    g_UiPanelScale_4720fc = BitsFloat(panel->field_10c);

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
    dest[0] = panel->field_110;
    dest[1] = panel->field_114;
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
// node+0x2C; each entry selects a word from the enclosing panel's +0x24 base
// (panel+0x24 / work_b4+0x24) by its low byte and emits the four-word record
// at entry+4.
void EmitEffectEntries(u8* node, u8* values) {
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
        case 0:  value = *reinterpret_cast<u32*>(values + 0xC8); break;
        case 1:  value = *reinterpret_cast<u32*>(values + 0xCC); break;
        case 2:  value = *reinterpret_cast<u32*>(values + 0xD0); break;
        case 3:  value = *reinterpret_cast<u32*>(values + 0xD4); break;
        case 4:  value = *reinterpret_cast<u32*>(values + 0xD8); break;
        case 5:  value = *reinterpret_cast<u32*>(values + 0xB0); break;
        case 6:  value = *reinterpret_cast<u32*>(values + 0xB4); break;
        case 7:  value = *reinterpret_cast<u32*>(values + 0xB8); break;
        case 8:  value = *reinterpret_cast<u32*>(values + 0xBC); break;
        case 9:  value = *reinterpret_cast<u32*>(values + 0xC0); break;
        default: value = *reinterpret_cast<u32*>(values + 0xC4); break;
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
__attribute__((naked)) void ui_func_0036c0a8(void* unused, UiActionPanel* frame, UiActionSlot* slot) {
    asm volatile(
        ".word 0xe92d4ff7\n"
        ".word 0xe24dd078\n"
        ".word 0xe59d007c\n"
        ".word 0xe2806040\n"
        ".word 0xe5d000e8\n"
        ".word 0xe5d610aa\n"
        ".word 0xe3500000\n"
        ".word 0x05d600a9\n"
        ".word 0x03500000\n"
        ".word 0x13a00001\n"
        ".word 0xe3510000\n"
        ".word 0xe58d0064\n"
        ".word 0x05d600ab\n"
        ".word 0x03500000\n"
        ".word 0xe59d007c\n"
        ".word 0x13a08001\n"
        ".word 0x03a08000\n"
        ".word 0xe5900024\n"
        ".word 0xe58d0014\n"
        ".word 0xe5921008\n"
        ".word 0xe3500000\n"
        ".word 0x0a00000b\n"
        ".word 0xe2800010\n"
        ".word 0xe8900005\n"
        ".word 0xe0420000\n"
        ".word 0xe1b00140\n"
        ".word 0x1a000006\n"
        ".word 0xe59d0014\n"
        ".word 0xe5900008\n"
        ".word 0xe1500001\n"
        ".word 0x059d0064\n"
        ".word 0x03500000\n"
        ".word 0x03580000\n"
        ".word 0x0a000333\n"
        ".word 0xe59d007c\n"
        ".word 0xe59142a4\n"
        ".word 0xe1a05001\n"
        ".word 0xe5902100\n"
        ".word 0xe5907008\n"
        ".word 0xe3540000\n"
        ".word 0xe58d2018\n"
        ".word 0xe5902104\n"
        ".word 0xe58d2024\n"
        ".word 0xe5902108\n"
        ".word 0xe58d2028\n"
        ".word 0xe590210c\n"
        ".word 0xe58d2040\n"
        ".word 0xe5902110\n"
        ".word 0xe58d202c\n"
        ".word 0xe5902114\n"
        ".word 0xe58d2030\n"
        ".word 0xe5902118\n"
        ".word 0xe58d2048\n"
        ".word 0xe590211c\n"
        ".word 0xe58d2034\n"
        ".word 0xe5902120\n"
        ".word 0xe58d2038\n"
        ".word 0xe5902124\n"
        ".word 0xe58d2044\n"
        ".word 0xe5900128\n"
        ".word 0xe58d003c\n"
        ".word 0x0a000006\n"
        ".word 0xe59d0018\n"
        ".word 0xe1500004\n"
        ".word 0x1a000003\n"
        ".word 0xe59d007c\n"
        ".word 0xe5d00013\n"
        ".word 0xe3500000\n"
        ".word 0x0a000002\n"
        ".word 0xe1a00007\n"
        ".word 0xeb0021c3\n"
        ".word 0xe58d4018\n"
        ".word 0xe5951018\n"
        ".word 0xe59fa564\n"
        ".word 0xe59fb564\n"
        ".word 0xe3a00001\n"
        ".word 0xe1d00001\n"
        ".word 0xe1a04005\n"
        ".word 0xe1a09005\n"
        ".word 0x1a000003\n"
        ".word 0xe59600a4\n"
        ".word 0xe3500000\n"
        ".word 0x13a00001\n"
        ".word 0x1a000000\n"
        ".word 0xe3a00000\n"
        ".word 0xe5972014\n"
        ".word 0xe59f3538\n"
        ".word 0xe3500000\n"
        ".word 0x13822902\n"
        ".word 0x03c22902\n"
        ".word 0xe5872014\n"
        ".word 0xe593c000\n"
        ".word 0xe2201001\n"
        ".word 0xe28ce008\n"
        ".word 0xe28c2010\n"
        ".word 0xe88e0801\n"
        ".word 0xe88c0402\n"
        ".word 0xe5832000\n"
        ".word 0xe59402a0\n"
        ".word 0xe3500000\n"
        ".word 0x0a000004\n"
        ".word 0xe59d1024\n"
        ".word 0xe1510000\n"
        ".word 0x1a000001\n"
        ".word 0xe3580000\n"
        ".word 0x0a000032\n"
        ".word 0xe597c008\n"
        ".word 0xe5991018\n"
        ".word 0xe59c3068\n"
        ".word 0xe3530000\n"
        ".word 0xda00000a\n"
        ".word 0xe59630a0\n"
        ".word 0xe3530000\n"
        ".word 0xda000004\n"
        ".word 0xe3a03002\n"
        ".word 0xe1d33001\n"
        ".word 0x05973014\n"
        ".word 0x03833a01\n"
        ".word 0x0a000001\n"
        ".word 0xe5973014\n"
        ".word 0xe3c33a01\n"
        ".word 0xe5873014\n"
        ".word 0xe59cc000\n"
        ".word 0xe3a03004\n"
        ".word 0xe1d3c00c\n"
        ".word 0x1a000007\n"
        ".word 0xe596c004\n"
        ".word 0xe35c0000\n"
        ".word 0x0a000001\n"
        ".word 0xe1d33001\n"
        ".word 0x0a000007\n"
        ".word 0xe5973014\n"
        ".word 0xe3c33020\n"
        ".word 0xe5873014\n"
        ".word 0xe3a0c010\n"
        ".word 0xe1dc1001\n"
        ".word 0xe3a03000\n"
        ".word 0x1a00000c\n"
        ".word 0xea000008\n"
        ".word 0xe5973014\n"
        ".word 0xe3a0c008\n"
        ".word 0xe1dcc001\n"
        ".word 0xe3833020\n"
        ".word 0xe5873014\n"
        ".word 0x03833040\n"
        ".word 0x13c33040\n"
        ".word 0xe5873014\n"
        ".word 0xeafffff1\n"
        ".word 0xe5961060\n"
        ".word 0xe3510000\n"
        ".word 0x13a03005\n"
        ".word 0xe59f4438\n"
        ".word 0xe59fc430\n"
        ".word 0xe2821008\n"
        ".word 0xe8820018\n"
        ".word 0xe58c1000\n"
        ".word 0xe58d0024\n"
        ".word 0xe59542b8\n"
        ".word 0xe2851f41\n"
        ".word 0xe3540000\n"
        ".word 0x0a000002\n"
        ".word 0xe59d0040\n"
        ".word 0xe1500004\n"
        ".word 0x0a000052\n"
        ".word 0xe58d101c\n"
        ".word 0xe5910000\n"
        ".word 0xe59fa400\n"
        ".word 0xe3a08001\n"
        ".word 0xe1d80000\n"
        ".word 0x03a00001\n"
        ".word 0x13a00000\n"
        ".word 0xe5ca0000\n"
        ".word 0xe59f03ec\n"
        ".word 0xe5911008\n"
        ".word 0xe59fb3e8\n"
        ".word 0xe59f93e8\n"
        ".word 0xe5801000\n"
        ".word 0xe59f03e4\n"
        ".word 0xe5900000\n"
        ".word 0xe3100001\n"
        ".word 0x1a000009\n"
        ".word 0xe59f03d4\n"
        ".word 0xfafd4f53\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000004\n"
        ".word 0xe59f03c4\n"
        ".word 0xe5a09004\n"
        ".word 0xe580b008\n"
        ".word 0xe59f03b4\n"
        ".word 0xe1a00000\n"
        ".word 0xe59f03b4\n"
        ".word 0xe5903000\n"
        ".word 0xe3530000\n"
        ".word 0x0a000165\n"
        ".word 0xe59f23a0\n"
        ".word 0xe3a00000\n"
        ".word 0xed9f0ae8\n"
        ".word 0xe4820008\n"
        ".word 0xe59f0380\n"
        ".word 0xe5823000\n"
        ".word 0xedd00a00\n"
        ".word 0xeef10a60\n"
        ".word 0xe5da0000\n"
        ".word 0xe3500000\n"
        ".word 0x0a000009\n"
        ".word 0xe59f0380\n"
        ".word 0xe5900000\n"
        ".word 0xe2402c81\n"
        ".word 0xe25220a5\n"
        ".word 0x0d9f1add\n"
        ".word 0x0a000002\n"
        ".word 0xeddf1adc\n"
        ".word 0xed9f1adc\n"
        ".word 0xee600aa1\n"
        ".word 0xee000ac1\n"
        ".word 0xee101a10\n"
        ".word 0xe2110102\n"
        ".word 0xe1a02081\n"
        ".word 0x13a00502\n"
        ".word 0xe1a03c22\n"
        ".word 0xe1a02481\n"
        ".word 0xe3d11102\n"
        ".word 0xe1a024a2\n"
        ".word 0x01a023a2\n"
        ".word 0x0a000005\n"
        ".word 0xe2531040\n"
        ".word 0xe1a023a2\n"
        ".word 0x4a000005\n"
        ".word 0xe351007f\n"
        ".word 0xc3a0087f\n"
        ".word 0xca000002\n"
        ".word 0xe201107f\n"
        ".word 0xe1800002\n"
        ".word 0xe1800801\n"
        ".word 0xe59f1300\n"
        ".word 0xe59f82e0\n"
        ".word 0xe5810010\n"
        ".word 0xe5980000\n"
        ".word 0xebfcd841\n"
        ".word 0xe59d301c\n"
        ".word 0xe2802008\n"
        ".word 0xe593100c\n"
        ".word 0xe5933010\n"
        ".word 0xe880000a\n"
        ".word 0xe5882000\n"
        ".word 0xe58d4040\n"
        ".word 0xe59542a8\n"
        ".word 0xe1a02005\n"
        ".word 0xe3540000\n"
        ".word 0x0a000002\n"
        ".word 0xe59d002c\n"
        ".word 0xe1500004\n"
        ".word 0x0a000003\n"
        ".word 0xe59d007c\n"
        ".word 0xe1a01007\n"
        ".word 0xeb00226c\n"
        ".word 0xe58d402c\n"
        ".word 0xe59502b0\n"
        ".word 0xe3500000\n"
        ".word 0xe58d0004\n"
        ".word 0x0a000003\n"
        ".word 0xe59d0030\n"
        ".word 0xe59d1004\n"
        ".word 0xe1500001\n"
        ".word 0x0a000023\n"
        ".word 0xe59fb268\n"
        ".word 0xe3a09000\n"
        ".word 0xe1a0a005\n"
        ".word 0xe1a04009\n"
        ".word 0xe3a00f9d\n"
        ".word 0xe0800104\n"
        ".word 0xe08a1000\n"
        ".word 0xe5910000\n"
        ".word 0xe3500000\n"
        ".word 0x10800001\n"
        ".word 0xe3500000\n"
        ".word 0x0a00000c\n"
        ".word 0xe3a01001\n"
        ".word 0xe1a0c411\n"
        ".word 0xe5908048\n"
        ".word 0xe59b3000\n"
        ".word 0xe2801010\n"
        ".word 0xe189900c\n"
        ".word 0xe1a02008\n"
        ".word 0xe1a00003\n"
        ".word 0xebfd0204\n"
        ".word 0xe59b0000\n"
        ".word 0xe3c81003\n"
        ".word 0xe0800001\n"
        ".word 0xe58b0000\n"
        ".word 0xe2844001\n"
        ".word 0xe3540003\n"
        ".word 0xbaffffe7\n"
        ".word 0xe59b0000\n"
        ".word 0xe59f322c\n"
        ".word 0xe3892801\n"
        ".word 0xe2801008\n"
        ".word 0xe1c020f0\n"
        ".word 0xe58b1000\n"
        ".word 0xe59d0004\n"
        ".word 0xe58d0030\n"
        ".word 0xe3a00000\n"
        ".word 0xe58d0004\n"
        ".word 0xe5950018\n"
        ".word 0xe3a01001\n"
        ".word 0xe1d10000\n"
        ".word 0x03a00001\n"
        ".word 0x13a00000\n"
        ".word 0xe3500000\n"
        ".word 0xe59502bc\n"
        ".word 0xe58d004c\n"
        ".word 0xe59502c0\n"
        ".word 0xe58d0050\n"
        ".word 0x0a0000b0\n"
        ".word 0xe5950288\n"
        ".word 0xe2851fa2\n"
        ".word 0xe3500000\n"
        ".word 0x10800001\n"
        ".word 0xe2800010\n"
        ".word 0xe58d0020\n"
        ".word 0xe5900000\n"
        ".word 0xe3a01020\n"
        ".word 0xe1d10000\n"
        ".word 0xe59d104c\n"
        ".word 0x03a00001\n"
        ".word 0x13a00000\n"
        ".word 0xe3510000\n"
        ".word 0xe58d0004\n"
        ".word 0x0a000005\n"
        ".word 0xe59d0048\n"
        ".word 0xe1500001\n"
        ".word 0x1a000002\n"
        ".word 0xe59d0064\n"
        ".word 0xe3500000\n"
        ".word 0x0a000089\n"
        ".word 0xe59d9020\n"
        ".word 0xe3a00001\n"
        ".word 0xe59fb184\n"
        ".word 0xe2891004\n"
        ".word 0xe59f4180\n"
        ".word 0xe891100e\n"
        ".word 0xe20110ff\n"
        ".word 0xe20380ff\n"
        ".word 0xe20c30ff\n"
        ".word 0xe58d1068\n"
        ".word 0xe5d9c014\n"
        ".word 0xe20220ff\n"
        ".word 0xe35c0000\n"
        ".word 0x13a0c001\n"
        ".word 0xe24cc001\n"
        ".word 0xe11c0003\n"
        ".word 0x03a01001\n"
        ".word 0x13a01000\n"
        ".word 0xe58d1070\n"
        ".word 0xe599a000\n"
        ".word 0xe59d1068\n"
        ".word 0xe1a0c00a\n"
        ".word 0xe1d0000c\n"
        ".word 0xe1a00102\n"
        ".word 0xe1800201\n"
        ".word 0xe59d1070\n"
        ".word 0x03a0e001\n"
        ".word 0x13a0e000\n"
        ".word 0xe1800b08\n"
        ".word 0xe1800d8e\n"
        ".word 0xe2211001\n"
        ".word 0xe1800e03\n"
        ".word 0xe1800f01\n"
        ".word 0xe380e102\n"
        ".word 0xe3a00002\n"
        ".word 0xe1d0000c\n"
        ".word 0x03a08001\n"
        ".word 0x13a08000\n"
        ".word 0xe3a00004\n"
        ".word 0xe1d0000c\n"
        ".word 0x03a01001\n"
        ".word 0x13a01000\n"
        ".word 0xe3a00020\n"
        ".word 0xe1d0000a\n"
        ".word 0xe2280001\n"
        ".word 0xe2211001\n"
        ".word 0x03a03001\n"
        ".word 0x13a03000\n"
        ".word 0xe1a00800\n"
        ".word 0xe3520000\n"
        ".word 0xe1801881\n"
        ".word 0x03a00001\n"
        ".word 0x13a00000\n"
        ".word 0xe3530000\n"
        ".word 0xe1810980\n"
        ".word 0xe59f8074\n"
        ".word 0x13a01000\n"
        ".word 0x03a01007\n"
        ".word 0xe38eeb01\n"
        ".word 0xe1800a01\n"
        ".word 0xe5981000\n"
        ".word 0xe3802701\n"
        ".word 0xe2813008\n"
        ".word 0xe581b004\n"
        ".word 0xe581e000\n"
        ".word 0xe8830014\n"
        ".word 0xe2810010\n"
        ".word 0xe5880000\n"
        ".word 0xe5990000\n"
        ".word 0xe3a01008\n"
        ".word 0xe1d11000\n"
        ".word 0x03a03001\n"
        ".word 0x13a03000\n"
        ".word 0xe3a01010\n"
        ".word 0xe1d10000\n"
        ".word 0xe59610a4\n"
        ".word 0x03a02001\n"
        ".word 0x13a02000\n"
        ".word 0xe3510000\n"
        ".word 0xe3a00000\n"
        ".word 0xda000038\n"
        ".word 0xe59fc050\n"
        ".word 0xe3a0e001\n"
        ".word 0xea000013\n"
        ".word 0x000101c6\n"
        ".word 0x0001008f\n"
        ".word 0x004652a0\n"
        ".word 0x000100e0\n"
        ".word 0x0047208e\n"
        ".word 0x004720fc\n"
        ".word 0x8017004d\n"
        ".word 0x0001006d\n"
        ".word 0x0047663c\n"
        ".word 0x004efddc\n"
        ".word 0x004720f0\n"
        ".word 0x00000000\n"
        ".word 0x004720ec\n"
        ".word 0x37800080\n"
        ".word 0x43000000\n"
        ".word 0x33800001\n"
        ".word 0x00050080\n"
        ".word 0x000f01c3\n"
        ".word 0x000401c4\n"
        ".word 0x00472100\n"
        ".word 0xe59cb000\n"
        ".word 0xe596c024\n"
        ".word 0xe79cc100\n"
        ".word 0xe59cc008\n"
        ".word 0xe59c4018\n"
        ".word 0xe59cc0b8\n"
        ".word 0xe2044002\n"
        ".word 0xe35c0000\n"
        ".word 0xe1a040a4\n"
        ".word 0x0a000002\n"
        ".word 0xe1a0c03b\n"
        ".word 0xe21cc001\n"
        ".word 0x0a000000\n"
        ".word 0xe3a0c001\n"
        ".word 0xe35c0000\n"
        ".word 0xe3a0c000\n"
        ".word 0x11a0c00e\n"
        ".word 0xe3540000\n"
        ".word 0xe51f4098\n"
        ".word 0xe59f862c\n"
        ".word 0x138cc002\n"
        ".word 0xe3530000\n"
        ".word 0xe5949000\n"
        ".word 0xe0888200\n"
        ".word 0x138cc004\n"
        ".word 0xe3520000\n"
        ".word 0x138cc008\n"
        ".word 0xe5898004\n"
        ".word 0xe289a008\n"
        ".word 0xe2800001\n"
        ".word 0xe589c000\n"
        ".word 0xe1500001\n"
        ".word 0xe584a000\n"
        ".word 0xbaffffde\n"
        ".word 0xe5950288\n"
        ".word 0xe2851fa2\n"
        ".word 0xe3500000\n"
        ".word 0x10811000\n"
        ".word 0x03a01000\n"
        ".word 0xe5b10028\n"
        ".word 0xe3500000\n"
        ".word 0x10811000\n"
        ".word 0xe59d0050\n"
        ".word 0x03a01000\n"
        ".word 0xe3500000\n"
        ".word 0x0a000003\n"
        ".word 0xe59d0034\n"
        ".word 0xe59d2050\n"
        ".word 0xe1500002\n"
        ".word 0x0a000001\n"
        ".word 0xe59d0020\n"
        ".word 0xeb00232a\n"
        ".word 0xe59d004c\n"
        ".word 0xe2859024\n"
        ".word 0xe58d0048\n"
        ".word 0xe59d0050\n"
        ".word 0xe58d0034\n"
        ".word 0xe59582b4\n"
        ".word 0xe3580000\n"
        ".word 0x0a000005\n"
        ".word 0xe59d0028\n"
        ".word 0xe1500008\n"
        ".word 0x1a000002\n"
        ".word 0xe59d0064\n"
        ".word 0xe3500000\n"
        ".word 0x0a00003c\n"
        ".word 0xe3a04001\n"
        ".word 0xe59d3004\n"
        ".word 0xe1a02009\n"
        ".word 0xe1a01007\n"
        ".word 0xe1a00006\n"
        ".word 0xeb001f13\n"
        ".word 0xe58d8028\n"
        ".word 0xe5950288\n"
        ".word 0xe59582c8\n"
        ".word 0xe2851fa2\n"
        ".word 0xe3500000\n"
        ".word 0x10807001\n"
        ".word 0x03a07000\n"
        ".word 0xe3580000\n"
        ".word 0x0a000003\n"
        ".word 0xe59d0038\n"
        ".word 0xe1500008\n"
        ".word 0x03a00000\n"
        ".word 0x0a000000\n"
        ".word 0xe3a00001\n"
        ".word 0xe1900004\n"
        ".word 0x0a000056\n"
        ".word 0xe1a06009\n"
        ".word 0xe51f91b4\n"
        ".word 0xe28710dc\n"
        ".word 0xe5990000\n"
        ".word 0xebfcd71c\n"
        ".word 0xe3a04000\n"
        ".word 0xe5890000\n"
        ".word 0xe0640184\n"
        ".word 0xe0870100\n"
        ".word 0xe5b0102c\n"
        ".word 0xe20110ff\n"
        ".word 0xe351000b\n"
        ".word 0x379ff101\n"
        ".word 0xea00003e\n"
        ".word 0x0036ca1c\n"
        ".word 0x0036c9cc\n"
        ".word 0x0036c9d4\n"
        ".word 0x0036c9dc\n"
        ".word 0x0036c9e4\n"
        ".word 0x0036c9ec\n"
        ".word 0x0036c9f4\n"
        ".word 0x0036c9fc\n"
        ".word 0x0036ca04\n"
        ".word 0x0036ca0c\n"
        ".word 0x0036ca14\n"
        ".word 0xe51f01f8\n"
        ".word 0xe59f24b8\n"
        ".word 0xe59f14b0\n"
        ".word 0xe5808000\n"
        ".word 0xe5922000\n"
        ".word 0xe5802008\n"
        ".word 0xe59f04a8\n"
        ".word 0xed910a00\n"
        ".word 0xed901a00\n"
        ".word 0xe51f022c\n"
        ".word 0xee301a41\n"
        ".word 0xedd00a00\n"
        ".word 0xee610a20\n"
        ".word 0xeafffe93\n"
        ".word 0xe59d0014\n"
        ".word 0xe3a04000\n"
        ".word 0xe3500000\n"
        ".word 0x0affffc5\n"
        ".word 0xe5901008\n"
        ".word 0xe5b10288\n"
        ".word 0xe3500000\n"
        ".word 0x10811000\n"
        ".word 0x03a01000\n"
        ".word 0xe3a00020\n"
        ".word 0xe5911010\n"
        ".word 0xe1d00001\n"
        ".word 0xe59d1004\n"
        ".word 0x03a00001\n"
        ".word 0x13a00000\n"
        ".word 0xe0314000\n"
        ".word 0x0affffb8\n"
        ".word 0xeaffffb1\n"
        ".word 0xe59610c8\n"
        ".word 0xea000012\n"
        ".word 0xe59610cc\n"
        ".word 0xea000010\n"
        ".word 0xe59610d0\n"
        ".word 0xea00000e\n"
        ".word 0xe59610d4\n"
        ".word 0xea00000c\n"
        ".word 0xe59610d8\n"
        ".word 0xea00000a\n"
        ".word 0xe59610b0\n"
        ".word 0xea000008\n"
        ".word 0xe59610b4\n"
        ".word 0xea000006\n"
        ".word 0xe59610b8\n"
        ".word 0xea000004\n"
        ".word 0xe59610bc\n"
        ".word 0xea000002\n"
        ".word 0xe59610c0\n"
        ".word 0xea000000\n"
        ".word 0xe59610c4\n"
        ".word 0xe5801014\n"
        ".word 0xe2801004\n"
        ".word 0xe5990000\n"
        ".word 0xebfcd6cf\n"
        ".word 0xe2844001\n"
        ".word 0xe3540006\n"
        ".word 0xe5890000\n"
        ".word 0x3affffb0\n"
        ".word 0xe58d8038\n"
        ".word 0xe5950288\n"
        ".word 0xe2851fa2\n"
        ".word 0xe3500000\n"
        ".word 0x10800001\n"
        ".word 0xe28010d4\n"
        ".word 0xe59502cc\n"
        ".word 0xe3500000\n"
        ".word 0x0a000002\n"
        ".word 0xe59d203c\n"
        ".word 0xe1520000\n"
        ".word 0x0a000006\n"
        ".word 0xe51f2338\n"
        ".word 0xe8911010\n"
        ".word 0xe5923000\n"
        ".word 0xe2831008\n"
        ".word 0xe8831010\n"
        ".word 0xe5821000\n"
        ".word 0xe58d003c\n"
        ".word 0xe59542d0\n"
        ".word 0xe2850f46\n"
        ".word 0xe3540000\n"
        ".word 0x0a000002\n"
        ".word 0xe59d1044\n"
        ".word 0xe1510004\n"
        ".word 0x0a0000be\n"
        ".word 0xe59f7368\n"
        ".word 0xe5901000\n"
        ".word 0xe280b040\n"
        ".word 0xe2803014\n"
        ".word 0xe1a0a000\n"
        ".word 0xe3a00001\n"
        ".word 0xe59fc354\n"
        ".word 0xe5d72000\n"
        ".word 0xe1d00001\n"
        ".word 0x03a00001\n"
        ".word 0x13a00000\n"
        ".word 0xe3520000\n"
        ".word 0x01dc20d0\n"
        ".word 0xe59fc338\n"
        ".word 0xe3a05002\n"
        ".word 0x01520000\n"
        ".word 0x13a02001\n"
        ".word 0x03a02000\n"
        ".word 0xe5c72000\n"
        ".word 0xe5cc0000\n"
        ".word 0xe1d50001\n"
        ".word 0xe59f131c\n"
        ".word 0x03a0c001\n"
        ".word 0x13a0c000\n"
        ".word 0xe3520000\n"
        ".word 0x01d100d0\n"
        ".word 0xe51fe3d8\n"
        ".word 0xe59f930c\n"
        ".word 0x0150000c\n"
        ".word 0x13a06001\n"
        ".word 0x03a06000\n"
        ".word 0xe5c76000\n"
        ".word 0xe5c1c000\n"
        ".word 0xe59f22f8\n"
        ".word 0xe59f82ec\n"
        ".word 0xe59e5000\n"
        ".word 0xe5991000\n"
        ".word 0xe5d22000\n"
        ".word 0xe2480002\n"
        ".word 0xe585000c\n"
        ".word 0xe1a01401\n"
        ".word 0xe1a02402\n"
        ".word 0xe5852008\n"
        ".word 0xe181160c\n"
        ".word 0xe28a2004\n"
        ".word 0xe8850102\n"
        ".word 0xe2851010\n"
        ".word 0xe2850020\n"
        ".word 0xe8920120\n"
        ".word 0xe1a0c00e\n"
        ".word 0xe8810120\n"
        ".word 0xe59a200c\n"
        ".word 0xe59a5010\n"
        ".word 0xe5812008\n"
        ".word 0xe581500c\n"
        ".word 0xe59f52a4\n"
        ".word 0xe1b0200b\n"
        ".word 0xe58e0000\n"
        ".word 0x0a000015\n"
        ".word 0xe5921000\n"
        ".word 0xe2111001\n"
        ".word 0x0a000031\n"
        ".word 0xe3560000\n"
        ".word 0xe3a01001\n"
        ".word 0x1a000003\n"
        ".word 0xe5d56000\n"
        ".word 0xe3560001\n"
        ".word 0x03a06000\n"
        ".word 0x0a000000\n"
        ".word 0xe3a06001\n"
        ".word 0xe5c76000\n"
        ".word 0xe5c51000\n"
        ".word 0xe8920140\n"
        ".word 0xe2801010\n"
        ".word 0xe1a0c00e\n"
        ".word 0xe8800140\n"
        ".word 0xe5926008\n"
        ".word 0xe59b200c\n"
        ".word 0xe5a06008\n"
        ".word 0xe5802004\n"
        ".word 0xe58e1000\n"
        ".word 0xe5931000\n"
        ".word 0xe3a00102\n"
        ".word 0xe59f8238\n"
        ".word 0xe1d00001\n"
        ".word 0xe5d71000\n"
        ".word 0x03a00001\n"
        ".word 0x13a00000\n"
        ".word 0xe3510000\n"
        ".word 0x01d810d0\n"
        ".word 0xe2200001\n"
        ".word 0xe1a0600c\n"
        ".word 0x01510000\n"
        ".word 0x13a01001\n"
        ".word 0x03a01000\n"
        ".word 0xe5c71000\n"
        ".word 0xe5c80000\n"
        ".word 0xe59c0000\n"
        ".word 0xe2831014\n"
        ".word 0xebfcd64d\n"
        ".word 0xe1a0c000\n"
        ".word 0xe5860000\n"
        ".word 0xe59a0028\n"
        ".word 0xe59f21ec\n"
        ".word 0xe2001003\n"
        ".word 0xe5d20000\n"
        ".word 0xe1500001\n"
        ".word 0x0a000008\n"
        ".word 0xe3a00001\n"
        ".word 0xe5c21000\n"
        ".word 0xe5c70000\n"
        ".word 0xea000007\n"
        ".word 0xe3560000\n"
        ".word 0x05d56000\n"
        ".word 0x03560000\n"
        ".word 0x0affffd1\n"
        ".word 0xeaffffcf\n"
        ".word 0xe5d70000\n"
        ".word 0xe3500000\n"
        ".word 0x0a00003e\n"
        ".word 0xe59f01ac\n"
        ".word 0xe3a01000\n"
        ".word 0xe5c71000\n"
        ".word 0xe5801010\n"
        ".word 0xe5801018\n"
        ".word 0xe5d22000\n"
        ".word 0xe3520000\n"
        ".word 0x13a0300f\n"
        ".word 0x15803010\n"
        ".word 0x1a000008\n"
        ".word 0xe5993000\n"
        ".word 0xe3530000\n"
        ".word 0x0a000006\n"
        ".word 0xe5d87000\n"
        ".word 0xe3570000\n"
        ".word 0x0353000f\n"
        ".word 0x13a0300f\n"
        ".word 0x15803010\n"
        ".word 0xe3a0300f\n"
        ".word 0xe5803018\n"
        ".word 0xe580101c\n"
        ".word 0xe3520001\n"
        ".word 0xe5801020\n"
        ".word 0x03a01003\n"
        ".word 0x0a000024\n"
        ".word 0xe3520000\n"
        ".word 0x1a000023\n"
        ".word 0xe59f1120\n"
        ".word 0xe5d11000\n"
        ".word 0xe3510000\n"
        ".word 0x0a00000b\n"
        ".word 0xe59f1114\n"
        ".word 0xe5d11000\n"
        ".word 0xe3510000\n"
        ".word 0x0a000003\n"
        ".word 0xe3a01002\n"
        ".word 0xe580101c\n"
        ".word 0xe5801020\n"
        ".word 0xea000003\n"
        ".word 0xe5991000\n"
        ".word 0xe3510000\n"
        ".word 0x13a01002\n"
        ".word 0x1580101c\n"
        ".word 0xe5d51000\n"
        ".word 0xe3510000\n"
        ".word 0x0a000010\n"
        ".word 0xe59f10e4\n"
        ".word 0xe5d11000\n"
        ".word 0xe3510000\n"
        ".word 0x0a000006\n"
        ".word 0xe590101c\n"
        ".word 0xe3811001\n"
        ".word 0xe580101c\n"
        ".word 0xe5901020\n"
        ".word 0xe3811001\n"
        ".word 0xe5801020\n"
        ".word 0xea000005\n"
        ".word 0xe5991000\n"
        ".word 0xe3510000\n"
        ".word 0x1590101c\n"
        ".word 0x13811001\n"
        ".word 0x0a000000\n"
        ".word 0xe580101c\n"
        ".word 0xe59f10b0\n"
        ".word 0xe3a02028\n"
        ".word 0xe1a0000c\n"
        ".word 0xebfcffe8\n"
        ".word 0xe5960000\n"
        ".word 0xe2800028\n"
        ".word 0xe5860000\n"
        ".word 0xe58d4044\n"
        ".word 0xe59d007c\n"
        ".word 0xe59d1018\n"
        ".word 0xe5801100\n"
        ".word 0xe59d1024\n"
        ".word 0xe5801104\n"
        ".word 0xe59d1028\n"
        ".word 0xe5801108\n"
        ".word 0xe59d1040\n"
        ".word 0xe580110c\n"
        ".word 0xe59d102c\n"
        ".word 0xe5801110\n"
        ".word 0xe59d1030\n"
        ".word 0xe5801114\n"
        ".word 0xe59d1048\n"
        ".word 0xe5801118\n"
        ".word 0xe59d1034\n"
        ".word 0xe580111c\n"
        ".word 0xe59d1038\n"
        ".word 0xe5801120\n"
        ".word 0xe59d1044\n"
        ".word 0xe5801124\n"
        ".word 0xe59d103c\n"
        ".word 0xe5801128\n"
        ".word 0xe28dd084\n"
        ".word 0xe8bd8ff0\n"
        ".word 0x00010149\n"
        ".word 0x004720f4\n"
        ".word 0x004720a0\n"
        ".word 0x004720f8\n"
        ".word 0x00472089\n"
        ".word 0x0047208b\n"
        ".word 0x0047208d\n"
        ".word 0x00020107\n"
        ".word 0x00472090\n"
        ".word 0x0047208f\n"
        ".word 0x0047208c\n"
        ".word 0x0047208a\n"
        ".word 0x00472088\n"
        ".word 0x004720b8\n"
    );
}
#if 0
// Original partial readable draft retained for reconstruction; not compiled.
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
    // `bics r0,#1,r1` leaves r0 zero only when bit 0 is set.
    const s32 visible =
        ((panel->field_18 & 1u) != 0 && frame->field_e4 != 0) ? 1 : 0;
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
                    (panel->field_18 & 2u) != 0) {
                    panel->field_14 |= 0x1000u;
                } else {
                    panel->field_14 &= ~0x1000u;
                }
            }
            if ((list->flags & 4u) != 0) {
                if (frame->field_44 != 0 &&
                    (panel->field_18 & 4u) != 0) {
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
    s32 list_flag = 0;                              // [sp+0x04]
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

    // 0x0036C560..0x0036C850: list record / flags.  The record block runs
    // only when bit 0 is set (0x0036C57C..0x0036C590).
    if ((panel->field_18 & 1u) != 0) {
        u8* node = (panel->rel_288 != 0)
                 ? reinterpret_cast<u8*>(panel) + 0x288 + panel->rel_288
                 : nullptr;
        u8* record = (node != nullptr) ? node + 0x10 : nullptr;
        list_flag = ((*reinterpret_cast<u32*>(record) & 0x20u) != 0) ? 1 : 0;

        if (!(panel->field_2bc != 0 && s118 == panel->field_2bc &&
              active_a == 0)) {
            // 0x0036C5E8..0x0036C6F4: 16-byte descriptor command.
            u8* data = record;
            const u32 b4 = *reinterpret_cast<u32*>(data + 4) & 0xFFu;
            const u32 b8 = *reinterpret_cast<u32*>(data + 8) & 0xFFu;
            const u32 bc = *reinterpret_cast<u32*>(data + 0xC) & 0xFFu;
            const u32 b10 = *reinterpret_cast<u32*>(data + 0x10) & 0xFFu;
            const u32 b14 = data[0x14];
            const u32 mask = (b14 != 0) ? 0u : 0xFFFFFFFFu;
            const u32 bit0 = ((mask & b10) == 0) ? 1u : 0u;
            const u32 flags = *reinterpret_cast<u32*>(data);
            const u32 word0 = 0x80000000u | (b8 << 2) | (b4 << 4)
                            | (bc << 22) | (b10 << 28)
                            | (((flags & 1u) == 0 ? 1u : 0u) << 27)
                            | ((bit0 ^ 1u) << 30) | 0x400u;
            const u32 word1 = (((flags & 2u) != 0 ? 1u : 0u) << 16)
                            | (((flags & 4u) != 0 ? 1u : 0u) << 17)
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
                    // 0x0036C78C..0x0036C79C: entries[i] is dereferenced at
                    // +0x08; +0x18/+0xB8 live on that inner object.
                    u8* inner = *reinterpret_cast<u8**>(entry + 8);
                    const u32 pair = *reinterpret_cast<u32*>(inner + 0x18) & 2u;
                    const u32 pair_bit = pair >> 1;
                    const u32 actor_state =
                        *reinterpret_cast<u32*>(inner + 0xB8);
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

        EmitEffectEntries(node, reinterpret_cast<u8*>(panel) + 0x24);
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
            EmitEffectEntries(node, reinterpret_cast<u8*>(panel) + 0x24);
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
#endif

// ---------------------------------------------------------------------------
// 0x00368CF8: multi-panel variant.  The same command blocks are emitted, but
// the panel components are fetched from `slots` (+0x28..+0x50) instead of a
// single panel.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00368cf8, 3452)
__attribute__((naked)) void ui_func_00368cf8(void* unused, UiActionPanel* frame,
                      UiActionSlotTable* slots) {
    asm volatile(
        ".word 0xe92d4ff7\n"
        ".word 0xe24dd078\n"
        ".word 0xe1a08002\n"
        ".word 0xe59d007c\n"
        ".word 0xe2805040\n"
        ".word 0xe5d010e8\n"
        ".word 0xe5906008\n"
        ".word 0xe3510000\n"
        ".word 0x05d500a9\n"
        ".word 0xe5d510aa\n"
        ".word 0x03500000\n"
        ".word 0x13a00001\n"
        ".word 0xe3510000\n"
        ".word 0xe58d005c\n"
        ".word 0x05d500ab\n"
        ".word 0xe5982028\n"
        ".word 0x03500000\n"
        ".word 0xe59d007c\n"
        ".word 0x13a07001\n"
        ".word 0x03a07000\n"
        ".word 0xe5901100\n"
        ".word 0xe58d100c\n"
        ".word 0xe5901104\n"
        ".word 0xe58d1018\n"
        ".word 0xe5901108\n"
        ".word 0xe58d101c\n"
        ".word 0xe590110c\n"
        ".word 0xe58d1024\n"
        ".word 0xe5901110\n"
        ".word 0xe58d104c\n"
        ".word 0xe5901114\n"
        ".word 0xe58d1020\n"
        ".word 0xe5901118\n"
        ".word 0xe59242a4\n"
        ".word 0xe58d1014\n"
        ".word 0xe590111c\n"
        ".word 0xe58d1028\n"
        ".word 0xe5901120\n"
        ".word 0xe58d102c\n"
        ".word 0xe5901124\n"
        ".word 0xe58d1034\n"
        ".word 0xe5900128\n"
        ".word 0xe59d100c\n"
        ".word 0xe58d0030\n"
        ".word 0xe1510004\n"
        ".word 0x1a000005\n"
        ".word 0xe3540000\n"
        ".word 0x0a000003\n"
        ".word 0xe59d007c\n"
        ".word 0xe5d00013\n"
        ".word 0xe3500000\n"
        ".word 0x0a000003\n"
        ".word 0xe1a01002\n"
        ".word 0xe1a00006\n"
        ".word 0xeb002ebf\n"
        ".word 0xe58d400c\n"
        ".word 0xe598102c\n"
        ".word 0xe59f4578\n"
        ".word 0xe59f9578\n"
        ".word 0xe58d1038\n"
        ".word 0xe5911018\n"
        ".word 0xe3a00001\n"
        ".word 0xe1d00001\n"
        ".word 0x1a000003\n"
        ".word 0xe59500a4\n"
        ".word 0xe3500000\n"
        ".word 0x13a00001\n"
        ".word 0x1a000000\n"
        ".word 0xe3a00000\n"
        ".word 0xe5962014\n"
        ".word 0xe59f354c\n"
        ".word 0xe3500000\n"
        ".word 0x13822902\n"
        ".word 0x03c22902\n"
        ".word 0xe5862014\n"
        ".word 0xe593c000\n"
        ".word 0xe2201001\n"
        ".word 0xe28ca008\n"
        ".word 0xe28c2010\n"
        ".word 0xe88a0201\n"
        ".word 0xe88c0012\n"
        ".word 0xe5832000\n"
        ".word 0xe59d0038\n"
        ".word 0xe59d1018\n"
        ".word 0xe59002a0\n"
        ".word 0xe1510000\n"
        ".word 0x1a000003\n"
        ".word 0xe3500000\n"
        ".word 0x0a000001\n"
        ".word 0xe3570000\n"
        ".word 0x0a000033\n"
        ".word 0xe596c008\n"
        ".word 0xe59d1038\n"
        ".word 0xe59c3068\n"
        ".word 0xe5911018\n"
        ".word 0xe3530000\n"
        ".word 0xda00000a\n"
        ".word 0xe59530a0\n"
        ".word 0xe3530000\n"
        ".word 0xda000004\n"
        ".word 0xe3a03002\n"
        ".word 0xe1d33001\n"
        ".word 0x05963014\n"
        ".word 0x03833a01\n"
        ".word 0x0a000001\n"
        ".word 0xe5963014\n"
        ".word 0xe3c33a01\n"
        ".word 0xe5863014\n"
        ".word 0xe59cc000\n"
        ".word 0xe3a03004\n"
        ".word 0xe1d3c00c\n"
        ".word 0x1a000007\n"
        ".word 0xe595c004\n"
        ".word 0xe35c0000\n"
        ".word 0x0a000001\n"
        ".word 0xe1d33001\n"
        ".word 0x0a000007\n"
        ".word 0xe5963014\n"
        ".word 0xe3c33020\n"
        ".word 0xe5863014\n"
        ".word 0xe3a0c010\n"
        ".word 0xe1dc1001\n"
        ".word 0xe3a03000\n"
        ".word 0x1a00000c\n"
        ".word 0xea000008\n"
        ".word 0xe5963014\n"
        ".word 0xe3a0c008\n"
        ".word 0xe1dcc001\n"
        ".word 0xe3833020\n"
        ".word 0xe5863014\n"
        ".word 0x03833040\n"
        ".word 0x13c33040\n"
        ".word 0xe5863014\n"
        ".word 0xeafffff1\n"
        ".word 0xe5951060\n"
        ".word 0xe3510000\n"
        ".word 0x13a03005\n"
        ".word 0xe59f4444\n"
        ".word 0xe59fc43c\n"
        ".word 0xe2821008\n"
        ".word 0xe8820018\n"
        ".word 0xe58c1000\n"
        ".word 0xe58d0018\n"
        ".word 0xe5980034\n"
        ".word 0xe59d1024\n"
        ".word 0xe59042b8\n"
        ".word 0xe1510004\n"
        ".word 0x1a000001\n"
        ".word 0xe3540000\n"
        ".word 0x1a000054\n"
        ".word 0xe2800f41\n"
        ".word 0xe58d0004\n"
        ".word 0xe5900000\n"
        ".word 0xe59fa408\n"
        ".word 0xe3a07001\n"
        ".word 0xe1d70000\n"
        ".word 0x03a00001\n"
        ".word 0x13a00000\n"
        ".word 0xe5ca0000\n"
        ".word 0xe59d0004\n"
        ".word 0xe59fb3f4\n"
        ".word 0xe59f93f4\n"
        ".word 0xe5901008\n"
        ".word 0xe59f03e4\n"
        ".word 0xe5801000\n"
        ".word 0xe59f03e8\n"
        ".word 0xe5900000\n"
        ".word 0xe3100001\n"
        ".word 0x1a000009\n"
        ".word 0xe59f03d8\n"
        ".word 0xfafd5c4b\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000004\n"
        ".word 0xe59f03c8\n"
        ".word 0xe5a09004\n"
        ".word 0xe580b008\n"
        ".word 0xe59f03b8\n"
        ".word 0xe1a00000\n"
        ".word 0xe59f03b8\n"
        ".word 0xe5903000\n"
        ".word 0xe3530000\n"
        ".word 0x0a00003b\n"
        ".word 0xe59f23a4\n"
        ".word 0xe3a00000\n"
        ".word 0xed9f0ae9\n"
        ".word 0xe4820008\n"
        ".word 0xe59f0384\n"
        ".word 0xe5823000\n"
        ".word 0xedd00a00\n"
        ".word 0xeef10a60\n"
        ".word 0xe5da0000\n"
        ".word 0xe3500000\n"
        ".word 0x0a000009\n"
        ".word 0xe59f0384\n"
        ".word 0xe5900000\n"
        ".word 0xe2402c81\n"
        ".word 0xe25220a5\n"
        ".word 0x0d9f1ade\n"
        ".word 0x0a000002\n"
        ".word 0xeddf1add\n"
        ".word 0xed9f1add\n"
        ".word 0xee600aa1\n"
        ".word 0xee000ac1\n"
        ".word 0xee101a10\n"
        ".word 0xe2110102\n"
        ".word 0xe1a02081\n"
        ".word 0x13a00502\n"
        ".word 0xe1a03c22\n"
        ".word 0xe1a02481\n"
        ".word 0xe3d11102\n"
        ".word 0xe1a024a2\n"
        ".word 0x01a023a2\n"
        ".word 0x0a000005\n"
        ".word 0xe2531040\n"
        ".word 0xe1a023a2\n"
        ".word 0x4a000005\n"
        ".word 0xe351007f\n"
        ".word 0xc3a0087f\n"
        ".word 0xca000002\n"
        ".word 0xe201107f\n"
        ".word 0xe1800002\n"
        ".word 0xe1800801\n"
        ".word 0xe59f1304\n"
        ".word 0xe59f72e4\n"
        ".word 0xe5810010\n"
        ".word 0xe5970000\n"
        ".word 0xebfce539\n"
        ".word 0xe59d3004\n"
        ".word 0xe2802008\n"
        ".word 0xe593100c\n"
        ".word 0xe5933010\n"
        ".word 0xe880000a\n"
        ".word 0xe5872000\n"
        ".word 0xe58d4024\n"
        ".word 0xe5982038\n"
        ".word 0xe59d004c\n"
        ".word 0xe59242a8\n"
        ".word 0xe1500004\n"
        ".word 0x1a000010\n"
        ".word 0xe3540000\n"
        ".word 0x1a000012\n"
        ".word 0xea00000d\n"
        ".word 0xe59f02b4\n"
        ".word 0xe59f22d0\n"
        ".word 0xe59f12c8\n"
        ".word 0xe5807000\n"
        ".word 0xe5922000\n"
        ".word 0xe5802008\n"
        ".word 0xe59f02c0\n"
        ".word 0xed910a00\n"
        ".word 0xed901a00\n"
        ".word 0xe59f0280\n"
        ".word 0xee301a41\n"
        ".word 0xedd00a00\n"
        ".word 0xee610a20\n"
        ".word 0xeaffffbd\n"
        ".word 0xe59d007c\n"
        ".word 0xe1a01006\n"
        ".word 0xeb002f55\n"
        ".word 0xe58d404c\n"
        ".word 0xe598a03c\n"
        ".word 0xe59d1020\n"
        ".word 0xe59a02b0\n"
        ".word 0xe1510000\n"
        ".word 0xe58d0004\n"
        ".word 0x1a000001\n"
        ".word 0xe3500000\n"
        ".word 0x1a000022\n"
        ".word 0xe59fb230\n"
        ".word 0xe3a09000\n"
        ".word 0xe1a04009\n"
        ".word 0xe3a00f9d\n"
        ".word 0xe0800104\n"
        ".word 0xe08a1000\n"
        ".word 0xe5910000\n"
        ".word 0xe3500000\n"
        ".word 0x10800001\n"
        ".word 0xe3500000\n"
        ".word 0x0a00000c\n"
        ".word 0xe3a01001\n"
        ".word 0xe1a0c411\n"
        ".word 0xe5907048\n"
        ".word 0xe59b3000\n"
        ".word 0xe2801010\n"
        ".word 0xe189900c\n"
        ".word 0xe1a02007\n"
        ".word 0xe1a00003\n"
        ".word 0xebfd0eee\n"
        ".word 0xe59b0000\n"
        ".word 0xe3c71003\n"
        ".word 0xe0800001\n"
        ".word 0xe58b0000\n"
        ".word 0xe2844001\n"
        ".word 0xe3540003\n"
        ".word 0xbaffffe7\n"
        ".word 0xe59b0000\n"
        ".word 0xe59f3204\n"
        ".word 0xe3892801\n"
        ".word 0xe2801008\n"
        ".word 0xe1c020f0\n"
        ".word 0xe58b1000\n"
        ".word 0xe59d0004\n"
        ".word 0xe58d0020\n"
        ".word 0xe3a00000\n"
        ".word 0xe58d0004\n"
        ".word 0xe59d0038\n"
        ".word 0xe3a01001\n"
        ".word 0xe5900018\n"
        ".word 0xe1d10000\n"
        ".word 0xe5980044\n"
        ".word 0xe5981040\n"
        ".word 0x03a02001\n"
        ".word 0x13a02000\n"
        ".word 0xe3520000\n"
        ".word 0xe58d0060\n"
        ".word 0xe59122bc\n"
        ".word 0xe58d2038\n"
        ".word 0xe59002c0\n"
        ".word 0xe58d003c\n"
        ".word 0x0a0000ae\n"
        ".word 0xe5b10288\n"
        ".word 0xe3500000\n"
        ".word 0x10800001\n"
        ".word 0xe2800010\n"
        ".word 0xe58d0040\n"
        ".word 0xe5900000\n"
        ".word 0xe3a01020\n"
        ".word 0xe1d10000\n"
        ".word 0xe59d1014\n"
        ".word 0x03a00001\n"
        ".word 0x13a00000\n"
        ".word 0xe1510002\n"
        ".word 0xe58d0004\n"
        ".word 0x1a000004\n"
        ".word 0xe3520000\n"
        ".word 0x0a000002\n"
        ".word 0xe59d005c\n"
        ".word 0xe3500000\n"
        ".word 0x0a00008a\n"
        ".word 0xe59d9040\n"
        ".word 0xe3a00001\n"
        ".word 0xe59fb154\n"
        ".word 0xe2891004\n"
        ".word 0xe59f4150\n"
        ".word 0xe891100e\n"
        ".word 0xe20110ff\n"
        ".word 0xe20370ff\n"
        ".word 0xe20c30ff\n"
        ".word 0xe58d1068\n"
        ".word 0xe5d9c014\n"
        ".word 0xe20220ff\n"
        ".word 0xe35c0000\n"
        ".word 0x13a0c001\n"
        ".word 0xe24cc001\n"
        ".word 0xe11c0003\n"
        ".word 0x03a01001\n"
        ".word 0x13a01000\n"
        ".word 0xe58d1070\n"
        ".word 0xe599c000\n"
        ".word 0xe59d1068\n"
        ".word 0xe1a0a00c\n"
        ".word 0xe1d0000a\n"
        ".word 0xe1a00102\n"
        ".word 0xe1800201\n"
        ".word 0xe59d1070\n"
        ".word 0x03a0e001\n"
        ".word 0x13a0e000\n"
        ".word 0xe1800b07\n"
        ".word 0xe1800d8e\n"
        ".word 0xe2211001\n"
        ".word 0xe1800e03\n"
        ".word 0xe1800f01\n"
        ".word 0xe380e102\n"
        ".word 0xe3a00002\n"
        ".word 0xe1d0000a\n"
        ".word 0x03a07001\n"
        ".word 0x13a07000\n"
        ".word 0xe3a00004\n"
        ".word 0xe1d0000a\n"
        ".word 0x03a01001\n"
        ".word 0x13a01000\n"
        ".word 0xe3a00020\n"
        ".word 0xe1d0000c\n"
        ".word 0xe2270001\n"
        ".word 0xe2211001\n"
        ".word 0x03a03001\n"
        ".word 0x13a03000\n"
        ".word 0xe1a00800\n"
        ".word 0xe3520000\n"
        ".word 0xe1801881\n"
        ".word 0x03a00001\n"
        ".word 0x13a00000\n"
        ".word 0xe3530000\n"
        ".word 0xe1810980\n"
        ".word 0xe59f7038\n"
        ".word 0x13a01000\n"
        ".word 0x03a01007\n"
        ".word 0xe38eeb01\n"
        ".word 0xe1800a01\n"
        ".word 0xe5971000\n"
        ".word 0xe3802701\n"
        ".word 0xe2813008\n"
        ".word 0xe581b004\n"
        ".word 0xe581e000\n"
        ".word 0xe2810010\n"
        ".word 0xe3a01008\n"
        ".word 0xe8830014\n"
        ".word 0xea000015\n"
        ".word 0x000101c6\n"
        ".word 0x0001008f\n"
        ".word 0x004652a0\n"
        ".word 0x000100e0\n"
        ".word 0x0047208e\n"
        ".word 0x004720fc\n"
        ".word 0x8017004d\n"
        ".word 0x0001006d\n"
        ".word 0x0047663c\n"
        ".word 0x004efddc\n"
        ".word 0x004720f0\n"
        ".word 0x00000000\n"
        ".word 0x004720ec\n"
        ".word 0x37800080\n"
        ".word 0x43000000\n"
        ".word 0x33800001\n"
        ".word 0x004720f4\n"
        ".word 0x004720a0\n"
        ".word 0x004720f8\n"
        ".word 0x00050080\n"
        ".word 0x000f01c3\n"
        ".word 0x000401c4\n"
        ".word 0xe5870000\n"
        ".word 0xe5990000\n"
        ".word 0xe1d11000\n"
        ".word 0x03a03001\n"
        ".word 0x13a03000\n"
        ".word 0xe3a01010\n"
        ".word 0xe1d10000\n"
        ".word 0xe59510a4\n"
        ".word 0x03a02001\n"
        ".word 0x13a02000\n"
        ".word 0xe3510000\n"
        ".word 0xe3a00000\n"
        ".word 0xda000022\n"
        ".word 0xe59fc654\n"
        ".word 0xe3a0e001\n"
        ".word 0xe59cc000\n"
        ".word 0xe5954024\n"
        ".word 0xe7944100\n"
        ".word 0xe5944008\n"
        ".word 0xe5947018\n"
        ".word 0xe59440b8\n"
        ".word 0xe2077002\n"
        ".word 0xe3540000\n"
        ".word 0xe1a070a7\n"
        ".word 0x0a000002\n"
        ".word 0xe1a0403c\n"
        ".word 0xe2144001\n"
        ".word 0x0a000000\n"
        ".word 0xe3a04001\n"
        ".word 0xe3540000\n"
        ".word 0xe3a04000\n"
        ".word 0x11a0400e\n"
        ".word 0xe3570000\n"
        ".word 0xe51f70dc\n"
        ".word 0xe59f9604\n"
        ".word 0x13844002\n"
        ".word 0xe3530000\n"
        ".word 0xe597a000\n"
        ".word 0x13844004\n"
        ".word 0xe3520000\n"
        ".word 0xe0899200\n"
        ".word 0x13844008\n"
        ".word 0xe88a0210\n"
        ".word 0xe28ab008\n"
        ".word 0xe2800001\n"
        ".word 0xe1500001\n"
        ".word 0xe587b000\n"
        ".word 0xbaffffdf\n"
        ".word 0xe59d0028\n"
        ".word 0xe59d103c\n"
        ".word 0xe1500001\n"
        ".word 0x1a000001\n"
        ".word 0xe3510000\n"
        ".word 0x1a00000a\n"
        ".word 0xe59d1060\n"
        ".word 0xe5b10288\n"
        ".word 0xe3500000\n"
        ".word 0x10811000\n"
        ".word 0x03a01000\n"
        ".word 0xe5b10028\n"
        ".word 0xe3500000\n"
        ".word 0x10811000\n"
        ".word 0xe59d0040\n"
        ".word 0x03a01000\n"
        ".word 0xeb003012\n"
        ".word 0xe59d0038\n"
        ".word 0xe5981030\n"
        ".word 0xe58d0014\n"
        ".word 0xe59d003c\n"
        ".word 0xe2819024\n"
        ".word 0xe58d0028\n"
        ".word 0xe59172b4\n"
        ".word 0xe59d001c\n"
        ".word 0xe1500007\n"
        ".word 0x1a000004\n"
        ".word 0xe3570000\n"
        ".word 0x0a000002\n"
        ".word 0xe59d005c\n"
        ".word 0xe3500000\n"
        ".word 0x0a00001c\n"
        ".word 0xe3a04001\n"
        ".word 0xe59d3004\n"
        ".word 0xe1a02009\n"
        ".word 0xe1a01006\n"
        ".word 0xe1a00005\n"
        ".word 0xeb002bfa\n"
        ".word 0xe58d701c\n"
        ".word 0xe5981048\n"
        ".word 0xe59d002c\n"
        ".word 0xe59172c8\n"
        ".word 0xe1500007\n"
        ".word 0x1a000023\n"
        ".word 0xe3570000\n"
        ".word 0x13a00000\n"
        ".word 0x0a000020\n"
        ".word 0xe1900004\n"
        ".word 0x0a000050\n"
        ".word 0xe5b10288\n"
        ".word 0xe1a05009\n"
        ".word 0xe51f91e4\n"
        ".word 0xe3500000\n"
        ".word 0x10806001\n"
        ".word 0x03a06000\n"
        ".word 0xe5990000\n"
        ".word 0xe28610dc\n"
        ".word 0xebfce404\n"
        ".word 0xe3a04000\n"
        ".word 0xe5890000\n"
        ".word 0xea000014\n"
        ".word 0xe59d007c\n"
        ".word 0xe3a04000\n"
        ".word 0xe5900024\n"
        ".word 0xe3500000\n"
        ".word 0x0affffe4\n"
        ".word 0xe5901044\n"
        ".word 0xe5b10288\n"
        ".word 0xe3500000\n"
        ".word 0x10811000\n"
        ".word 0x03a01000\n"
        ".word 0xe3a00020\n"
        ".word 0xe5911010\n"
        ".word 0xe1d00001\n"
        ".word 0xe59d1004\n"
        ".word 0x03a00001\n"
        ".word 0x13a00000\n"
        ".word 0xe0314000\n"
        ".word 0x0affffd7\n"
        ".word 0xeaffffd0\n"
        ".word 0xe3a00001\n"
        ".word 0xeaffffdc\n"
        ".word 0xe0640184\n"
        ".word 0xe0860100\n"
        ".word 0xe5b0102c\n"
        ".word 0xe20110ff\n"
        ".word 0xe351000b\n"
        ".word 0x379ff101\n"
        ".word 0xea00001e\n"
        ".word 0x00369654\n"
        ".word 0x00369604\n"
        ".word 0x0036960c\n"
        ".word 0x00369614\n"
        ".word 0x0036961c\n"
        ".word 0x00369624\n"
        ".word 0x0036962c\n"
        ".word 0x00369634\n"
        ".word 0x0036963c\n"
        ".word 0x00369644\n"
        ".word 0x0036964c\n"
        ".word 0xe59510c8\n"
        ".word 0xea000012\n"
        ".word 0xe59510cc\n"
        ".word 0xea000010\n"
        ".word 0xe59510d0\n"
        ".word 0xea00000e\n"
        ".word 0xe59510d4\n"
        ".word 0xea00000c\n"
        ".word 0xe59510d8\n"
        ".word 0xea00000a\n"
        ".word 0xe59510b0\n"
        ".word 0xea000008\n"
        ".word 0xe59510b4\n"
        ".word 0xea000006\n"
        ".word 0xe59510b8\n"
        ".word 0xea000004\n"
        ".word 0xe59510bc\n"
        ".word 0xea000002\n"
        ".word 0xe59510c0\n"
        ".word 0xea000000\n"
        ".word 0xe59510c4\n"
        ".word 0xe5801014\n"
        ".word 0xe2801004\n"
        ".word 0xe5990000\n"
        ".word 0xebfce3c1\n"
        ".word 0xe2844001\n"
        ".word 0xe3540006\n"
        ".word 0xe5890000\n"
        ".word 0x3affffd0\n"
        ".word 0xe58d702c\n"
        ".word 0xe598204c\n"
        ".word 0xe59d1030\n"
        ".word 0xe59202cc\n"
        ".word 0xe1510000\n"
        ".word 0x1a000001\n"
        ".word 0xe3500000\n"
        ".word 0x1a00000a\n"
        ".word 0xe5b21288\n"
        ".word 0xe3510000\n"
        ".word 0x10811002\n"
        ".word 0xe51f2348\n"
        ".word 0xe28110d4\n"
        ".word 0xe8911010\n"
        ".word 0xe5923000\n"
        ".word 0xe2831008\n"
        ".word 0xe8831010\n"
        ".word 0xe5821000\n"
        ".word 0xe58d0030\n"
        ".word 0xe5980050\n"
        ".word 0xe59d1034\n"
        ".word 0xe59042d0\n"
        ".word 0xe1510004\n"
        ".word 0x1a000001\n"
        ".word 0xe3540000\n"
        ".word 0x1a0000bf\n"
        ".word 0xe2800f46\n"
        ".word 0xe59f7360\n"
        ".word 0xe5901000\n"
        ".word 0xe280b040\n"
        ".word 0xe2803014\n"
        ".word 0xe1a0a000\n"
        ".word 0xe3a00001\n"
        ".word 0xe59fc34c\n"
        ".word 0xe5d72000\n"
        ".word 0xe1d00001\n"
        ".word 0x03a00001\n"
        ".word 0x13a00000\n"
        ".word 0xe3520000\n"
        ".word 0x01dc20d0\n"
        ".word 0xe59fc330\n"
        ".word 0xe3a05002\n"
        ".word 0x01520000\n"
        ".word 0x13a02001\n"
        ".word 0x03a02000\n"
        ".word 0xe5c72000\n"
        ".word 0xe5cc0000\n"
        ".word 0xe1d50001\n"
        ".word 0xe59f1314\n"
        ".word 0x03a0c001\n"
        ".word 0x13a0c000\n"
        ".word 0xe3520000\n"
        ".word 0x01d100d0\n"
        ".word 0xe51fe3f0\n"
        ".word 0xe59f9304\n"
        ".word 0x0150000c\n"
        ".word 0x13a06001\n"
        ".word 0x03a06000\n"
        ".word 0xe5c76000\n"
        ".word 0xe5c1c000\n"
        ".word 0xe59f22f0\n"
        ".word 0xe59f82e4\n"
        ".word 0xe59e5000\n"
        ".word 0xe5991000\n"
        ".word 0xe5d22000\n"
        ".word 0xe2480002\n"
        ".word 0xe585000c\n"
        ".word 0xe1a01401\n"
        ".word 0xe1a02402\n"
        ".word 0xe5852008\n"
        ".word 0xe181160c\n"
        ".word 0xe28a2004\n"
        ".word 0xe8850102\n"
        ".word 0xe2851010\n"
        ".word 0xe2850020\n"
        ".word 0xe8920120\n"
        ".word 0xe1a0c00e\n"
        ".word 0xe8810120\n"
        ".word 0xe59a200c\n"
        ".word 0xe59a5010\n"
        ".word 0xe5812008\n"
        ".word 0xe581500c\n"
        ".word 0xe59f529c\n"
        ".word 0xe1b0200b\n"
        ".word 0xe58e0000\n"
        ".word 0x0a000015\n"
        ".word 0xe5921000\n"
        ".word 0xe2111001\n"
        ".word 0x0a000031\n"
        ".word 0xe3560000\n"
        ".word 0xe3a01001\n"
        ".word 0x1a000003\n"
        ".word 0xe5d56000\n"
        ".word 0xe3560001\n"
        ".word 0x03a06000\n"
        ".word 0x0a000000\n"
        ".word 0xe3a06001\n"
        ".word 0xe5c76000\n"
        ".word 0xe5c51000\n"
        ".word 0xe8920140\n"
        ".word 0xe2801010\n"
        ".word 0xe1a0c00e\n"
        ".word 0xe8800140\n"
        ".word 0xe5926008\n"
        ".word 0xe59b200c\n"
        ".word 0xe5a06008\n"
        ".word 0xe5802004\n"
        ".word 0xe58e1000\n"
        ".word 0xe5931000\n"
        ".word 0xe3a00102\n"
        ".word 0xe59f8230\n"
        ".word 0xe1d00001\n"
        ".word 0xe5d71000\n"
        ".word 0x03a00001\n"
        ".word 0x13a00000\n"
        ".word 0xe3510000\n"
        ".word 0x01d810d0\n"
        ".word 0xe2200001\n"
        ".word 0xe1a0600c\n"
        ".word 0x01510000\n"
        ".word 0x13a01001\n"
        ".word 0x03a01000\n"
        ".word 0xe5c71000\n"
        ".word 0xe5c80000\n"
        ".word 0xe59c0000\n"
        ".word 0xe2831014\n"
        ".word 0xebfce33e\n"
        ".word 0xe1a0c000\n"
        ".word 0xe5860000\n"
        ".word 0xe59a0028\n"
        ".word 0xe59f21e4\n"
        ".word 0xe2001003\n"
        ".word 0xe5d20000\n"
        ".word 0xe1500001\n"
        ".word 0x0a000008\n"
        ".word 0xe3a00001\n"
        ".word 0xe5c21000\n"
        ".word 0xe5c70000\n"
        ".word 0xea000007\n"
        ".word 0xe3560000\n"
        ".word 0x05d56000\n"
        ".word 0x03560000\n"
        ".word 0x0affffd1\n"
        ".word 0xeaffffcf\n"
        ".word 0xe5d70000\n"
        ".word 0xe3500000\n"
        ".word 0x0a00003e\n"
        ".word 0xe59f01a4\n"
        ".word 0xe3a01000\n"
        ".word 0xe5c71000\n"
        ".word 0xe5801010\n"
        ".word 0xe5801018\n"
        ".word 0xe5d22000\n"
        ".word 0xe3520000\n"
        ".word 0x13a0300f\n"
        ".word 0x15803010\n"
        ".word 0x1a000008\n"
        ".word 0xe5993000\n"
        ".word 0xe3530000\n"
        ".word 0x0a000006\n"
        ".word 0xe5d87000\n"
        ".word 0xe3570000\n"
        ".word 0x0353000f\n"
        ".word 0x13a0300f\n"
        ".word 0x15803010\n"
        ".word 0xe3a0300f\n"
        ".word 0xe5803018\n"
        ".word 0xe580101c\n"
        ".word 0xe3520001\n"
        ".word 0xe5801020\n"
        ".word 0x03a01003\n"
        ".word 0x0a000024\n"
        ".word 0xe3520000\n"
        ".word 0x1a000023\n"
        ".word 0xe59f1118\n"
        ".word 0xe5d11000\n"
        ".word 0xe3510000\n"
        ".word 0x0a00000b\n"
        ".word 0xe59f110c\n"
        ".word 0xe5d11000\n"
        ".word 0xe3510000\n"
        ".word 0x0a000003\n"
        ".word 0xe3a01002\n"
        ".word 0xe580101c\n"
        ".word 0xe5801020\n"
        ".word 0xea000003\n"
        ".word 0xe5991000\n"
        ".word 0xe3510000\n"
        ".word 0x13a01002\n"
        ".word 0x1580101c\n"
        ".word 0xe5d51000\n"
        ".word 0xe3510000\n"
        ".word 0x0a000010\n"
        ".word 0xe59f10dc\n"
        ".word 0xe5d11000\n"
        ".word 0xe3510000\n"
        ".word 0x0a000006\n"
        ".word 0xe590101c\n"
        ".word 0xe3811001\n"
        ".word 0xe580101c\n"
        ".word 0xe5901020\n"
        ".word 0xe3811001\n"
        ".word 0xe5801020\n"
        ".word 0xea000005\n"
        ".word 0xe5991000\n"
        ".word 0xe3510000\n"
        ".word 0x1590101c\n"
        ".word 0x13811001\n"
        ".word 0x0a000000\n"
        ".word 0xe580101c\n"
        ".word 0xe59f10a8\n"
        ".word 0xe3a02028\n"
        ".word 0xe1a0000c\n"
        ".word 0xebfd0cd9\n"
        ".word 0xe5960000\n"
        ".word 0xe2800028\n"
        ".word 0xe5860000\n"
        ".word 0xe58d4034\n"
        ".word 0xe59d007c\n"
        ".word 0xe59d100c\n"
        ".word 0xe5801100\n"
        ".word 0xe59d1018\n"
        ".word 0xe5801104\n"
        ".word 0xe59d101c\n"
        ".word 0xe5801108\n"
        ".word 0xe59d1024\n"
        ".word 0xe580110c\n"
        ".word 0xe59d104c\n"
        ".word 0xe5801110\n"
        ".word 0xe59d1020\n"
        ".word 0xe5801114\n"
        ".word 0xe59d1014\n"
        ".word 0xe5801118\n"
        ".word 0xe59d1028\n"
        ".word 0xe580111c\n"
        ".word 0xe59d102c\n"
        ".word 0xe5801120\n"
        ".word 0xe59d1034\n"
        ".word 0xe5801124\n"
        ".word 0xe59d1030\n"
        ".word 0xe5801128\n"
        ".word 0xe28dd084\n"
        ".word 0xe8bd8ff0\n"
        ".word 0x00472100\n"
        ".word 0x00010149\n"
        ".word 0x00472089\n"
        ".word 0x0047208b\n"
        ".word 0x0047208d\n"
        ".word 0x00020107\n"
        ".word 0x00472090\n"
        ".word 0x0047208f\n"
        ".word 0x0047208c\n"
        ".word 0x0047208a\n"
        ".word 0x00472088\n"
        ".word 0x004720b8\n"
    );
}
#if 0
// Original partial readable draft retained for reconstruction; not compiled.
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
        ((work->field_18 & 1u) != 0 && frame->field_e4 != 0) ? 1 : 0;
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
                    (work->field_18 & 2u) != 0) {
                    work->field_14 |= 0x1000u;
                } else {
                    work->field_14 &= ~0x1000u;
                }
            }
            if ((list->flags & 4u) != 0) {
                if (frame->field_44 != 0 && (work->field_18 & 4u) != 0) {
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
    s32 list_flag = 0;                              // [sp+0x04]
    if ((work->field_18 & 1u) != 0) {
        u8* node = (work_bc->rel_288 != 0)
                 ? reinterpret_cast<u8*>(work_bc) + 0x288
                       + work_bc->rel_288
                 : nullptr;
        u8* record = (node != nullptr) ? node + 0x10 : nullptr;
        list_flag = ((*reinterpret_cast<u32*>(record) & 0x20u) != 0) ? 1 : 0;

        if (!(work_bc->field_2bc != 0 && s118 == work_bc->field_2bc &&
              active_a == 0)) {
            // same descriptor as 0x0036C5E8
            u8* data = record;
            const u32 b4 = *reinterpret_cast<u32*>(data + 4) & 0xFFu;
            const u32 b8 = *reinterpret_cast<u32*>(data + 8) & 0xFFu;
            const u32 bc = *reinterpret_cast<u32*>(data + 0xC) & 0xFFu;
            const u32 b10 = *reinterpret_cast<u32*>(data + 0x10) & 0xFFu;
            const u32 b14 = data[0x14];
            const u32 mask = (b14 != 0) ? 0u : 0xFFFFFFFFu;
            const u32 bit0 = ((mask & b10) == 0) ? 1u : 0u;
            const u32 flags = *reinterpret_cast<u32*>(data);
            const u32 word0 = 0x80000000u | (b8 << 2) | (b4 << 4)
                            | (bc << 22) | (b10 << 28)
                            | (((flags & 1u) == 0 ? 1u : 0u) << 27)
                            | ((bit0 ^ 1u) << 30) | 0x400u;
            const u32 word1 = (((flags & 2u) != 0 ? 1u : 0u) << 16)
                            | (((flags & 4u) != 0 ? 1u : 0u) << 17)
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
                    // 0x0036C78C..0x0036C79C: entries[i] is dereferenced at
                    // +0x08; +0x18/+0xB8 live on that inner object.
                    u8* inner = *reinterpret_cast<u8**>(entry + 8);
                    const u32 pair = *reinterpret_cast<u32*>(inner + 0x18) & 2u;
                    const u32 pair_bit = pair >> 1;
                    const u32 actor_state =
                        *reinterpret_cast<u32*>(inner + 0xB8);
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
    bool rerun = false;
    if (!(work_b4 != nullptr && s108 == work_b4->field_2b4 &&
          work_b4->field_2b4 != 0)) {
        rerun = true;
    } else {
        // 0x00369568..0x003695B4: compare the 0x20 bit reached through
        // [frame+0x24]+0x44/+0x288 with the latched list flag; a change
        // jumps to 0x003694F8 and re-runs the 0x2B4 block.
        if (frame->field_24 != 0) {
            u8* object = reinterpret_cast<u8*>(
                static_cast<std::uintptr_t>(frame->field_24));
            u8* inner = *reinterpret_cast<u8**>(object + 0x44);
            if (inner != nullptr) {
                const u32 relative =
                    *reinterpret_cast<u32*>(inner + 0x288);
                u8* node = (relative != 0) ? inner + 0x288 + relative
                                           : nullptr;
                if (node != nullptr) {
                    const bool bit =
                        (*reinterpret_cast<u32*>(node + 0x10) & 0x20u) != 0;
                    rerun = (bit != (list_flag != 0));
                }
            }
        }
    }
    if (rerun) {
        func_003744f8(frame, scene, &work_b4->field_24,
                      static_cast<u32>(list_flag));
        s108 = work_b4->field_2b4;
    }

    // 0x00369510..0x0036967C: the 0x2C8 block also runs after a rerun.
    if (rerun ||
        !(work_c8 != nullptr && s120 == work_c8->field_2c8 &&
          work_c8->field_2c8 != 0)) {
        u8* node = (work_bc->rel_288 != 0)
                 ? reinterpret_cast<u8*>(work_bc) + 0x288
                       + work_bc->rel_288
                 : nullptr;
        EmitEffectEntries(node, reinterpret_cast<u8*>(work_b4) + 0x24);
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
#endif

} // namespace smt4::ui
