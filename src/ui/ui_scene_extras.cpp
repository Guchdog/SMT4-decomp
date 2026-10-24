#include "ui/ui_scene_extras.h"
#include "engine/asd_symbols.h"
#include "engine/asd_model.h"
#include "engine/map_runtime.h"
#include "script/script_vm_extras.h"
#include <cmath>
#include <cstring>

namespace smt4::ui {

TalkOverlayFlags g_TalkOverlayFlags{};                 // 0x0049FB1C (BSS)
EffMenuScene g_EffMenuScene{};                         // 0x004D8F40 (BSS)
EffMenuScroll g_EffMenuScroll{};                       // 0x004D9290 (BSS)
EffMenuAnimConfig g_EffMenuAnimConfig{};               // 0x004D92B4 (BSS)
// 0x0044FCA8 (.data image): +0x04=0x00A8, +0x08=0x0050,
// +0x10=0x00000014, +0x14=0x0044F9A8, +0x18=0x00000008.
AsdUiObject g_EffMenuObjectA = {
    {0x00, 0x00, 0x00, 0x00, 0xA8, 0x00, 0x00, 0x00,
     0x50, 0x00, 0x00, 0x00},                           // pad_00: +0x04/+0x08
    0,                                                  // field_0c
    0x14u,                                              // flags_10 (0x0044FCA8+0x10)
    reinterpret_cast<u32*>(0x0044F9A8u),                // table_14 (0x0044FCA8+0x14)
    {0x08, 0x00, 0x00, 0x00},                           // pad_18: +0x18=0x08
    nullptr,                                            // user_1c
    {},                                                 // pad_20
    nullptr,                                            // child_34
};
// 0x0044F970 (.data image): +0x04=0x00000168, +0x08=0x00000008,
// flags_10 is zero, +0x14=0x00463EF0, +0x18=0x00000004.
AsdUiObject g_EffMenuObjectB = {
    {0x00, 0x00, 0x00, 0x00, 0x68, 0x01, 0x00, 0x00,
     0x08, 0x00, 0x00, 0x00},                           // pad_00: +0x04/+0x08
    0,                                                  // field_0c
    0u,                                                 // flags_10
    reinterpret_cast<u32*>(0x00463EF0u),                // table_14
    {0x04, 0x00, 0x00, 0x00},                           // pad_18: +0x18=0x04
    nullptr,                                            // user_1c
    {},                                                 // pad_20
    nullptr,                                            // child_34
};
// 0x004342C8 (.data), observed words:
//   +00 0, +04 0x3E19999A (0.15f), +08 0x3DCCCCCD (0.1f), +0C 5,
//   +10 0, +14 0.0f, +18 -1, +1C 5, +20 -1, +24 5.
ResultAnimConfig g_ResultAnim = {
    0u, 0.15f, 0.1f, 5, 0, 0.0f, -1, 5, -1, 5,
};
f32 g_ResultOrigin[3] = {0.0f, 0.0f, 0.0f};            // 0x00493530 (.data)
TalkAnimRow* g_TalkAnimRows =                           // 0x00447E58 (.data)
    reinterpret_cast<TalkAnimRow*>(0x004BB7B0u);        // observed pointer
// 0x00407FC0: 4096-byte .rodata palette transcribed byte-for-byte from
// code.bin (256 rows of four floats; row 0 starts { 0, 1, ... }).
UiColorEntry g_UiColorTable[256] = {
#include "ui_color_table.inc"
};

namespace {
// Aliases to the owners of the shared addresses.  Keeping one definition per
// binary address avoids a second symbol for the map IF work (0x00447A78), the
// script camera slot (0x004474F4), the shared map state (0x0049F91C), the
// effect-editor singleton (0x0044EA80) and the projection tables (0x004B5D30).
inline TalkWork*& TalkWorkSlot() {
    return *reinterpret_cast<TalkWork**>(&engine::g_MapIfWork);
}
inline TalkCamera*& TalkCameraSlot() {
    return *reinterpret_cast<TalkCamera**>(&script::g_ScriptCameraWork);
}
inline UiWindowState& UiWindowSlot() {
    return *reinterpret_cast<UiWindowState*>(engine::g_MapRuntimeState);
}
inline EffMenuWork& EffMenuState() {
    return *reinterpret_cast<EffMenuWork*>(&engine::g_EffectEditor);
}
inline f32* QuadTableBase() {
    return reinterpret_cast<f32*>(&engine::g_MapIfProjectionTables);
}
// 0x004B6FC0: the detail-ring output quad written by the loop at
// 0x001E9260 (`sl = fp + 0xC60`, where fp = 0x004B6360).  This is a separate
// object from the 0xC90-byte g_MapIfProjectionTables at 0x004B5D30, so model
// it as its own block instead of pointer arithmetic past that object.
struct DetailRingOutputBlock {
    f32 points[4][3];                                   // four transformed points
};
static_assert(sizeof(DetailRingOutputBlock) == 0x30);
DetailRingOutputBlock g_UiDetailRingOutput{};           // 0x004B6FC0
inline f32* DetailRingOutputBase() {
    return &g_UiDetailRingOutput.points[0][0];
}
} // namespace

namespace {

extern "C" {
    extern u8* g_AsdGpuState;                                                   // 0x0044EA00

    // Common UI helpers (canonical spellings used by the other UI TUs).
    void* UiGpu_SetViewportParams(s32 a0, s32 a1);                              // 0x002C5F7C
    void* UiGpu_SetRenderMode(s32 a0, s32 a1, s32 a2);                          // 0x002C5FA4
    s32   UiAnimSprite_GetPosX(const UiAnimSprite* sprite);                     // 0x002BEF7C
    s32   UiAnimSprite_GetPosY(const UiAnimSprite* sprite);                     // 0x002BEF70
    void  UiSprite_DrawNode(u32 screen, u32 group, u32 node,
                            s32 x, s32 y, s32 prio);                            // 0x002BF460
    void  UiSprite_DrawPanel(u32 screen, u32 group, u32 panel,
                             s32 x, s32 y, s32 prio);                           // 0x002BF558
    void  UiFont_FormatString(char* dst, const char* fmt, ...);                 // 0x002BE7FC
    void  UiFont_DrawText(u32 font_id, u32 rgba, const char* text,
                          f32 x, f32 y, f32 scale_x, f32 rot, f32 scale_y);     // 0x002BE77C
    void  UiFont_DrawFormatted(u32 screen, s32 x, s32 y, s32 mode, s32 width,
                               s32 prio, const char* fmt, s32 value);           // 0x002BE16C
    void  UiSprite_SetGlobalAlpha(f32 alpha);                                   // 0x002BF710
    s32   UiTouch_GetRegionTouchState(s16 handle);                              // 0x0029D8FC
    s32   UiListCursor_GetRowCount(const UiListCursor* cursor);                 // 0x0029F0F4
    s32   UiListCursor_GetSelectedRow(const UiListCursor* cursor);              // 0x0029F248
    s32   UiListCursor_GetScrollOffset(const UiListCursor* cursor);             // 0x0029F260
    void  UiSkill_DrawItemIconAndCount(s32 item_id, s32 x, s32 y,
                                       s32 prio, s32 a4);                       // 0x002B6A98
    // 0x002B6F74 reads both trailing words from the stack: +0x00 is the
    // integer draw-bars gate (`cmp r4,#0`, 0x002B7000), +0x04 the row offset.
    void  UiParty_DrawDemonBars(s16 demon_id, s32 x, s32 y, s32 prio,
                                s32 draw_bars, s32 a5);                         // 0x002B6F74
    const char* Quest_GetObjectiveName(u16 entry_id);                           // 0x002BE828
    void  Quest_DrawObjectiveIcon(u16 entry_id, s32 x, s32 y, s32 prio);        // 0x002BE548
    void* Battle_GetTalkEntry(u32 id);                                          // 0x002B9364

    // Effect-menu helpers (0x00243E8C call graph).
    void* AsdMem_Alloc(u32 align, u32 line, u32 zero_flag, u32 size, u32 flag); // 0x002C4B84
    void* AsdWork_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 a5);      // 0x002C34A4
    void  UiEffectList_Push(void* node, u32 type);                              // 0x002573EC
    void  EffMenu_DrawQuadRect(s32 a, s32 b, s32 c, s32 d,
                               u32 color0, u32 color1);                          // 0x00282944
    void  EffMenu_DrawQuadBar(s32 a, s32 b, s32 c, s32 d,
                              f32 s0, f32 s1);                                   // 0x002829F0
    int   UiInput_Trigger(u32 id);                                              // 0x002B902C
    int   UiInput_Trigger3(u32 id);                                             // 0x002C17D4
    u8    UiInput_Reset(u32 id);                                                // 0x0024DF94
    int   UiInput_Trigger2(u32 id);                                             // 0x002BFFBC
    void  UiText_Draw(u32 a0, u32 a1, u32 a2, const char* fmt, ...);            // 0x0024DF14
    void  AsdUiObject_Update(void* object);                                     // 0x0024DF5C
    void* AsdUiObject_CreateAndReset(void* object);                             // 0x0024DFA4

    // Battle command helpers (0x002F150C call graph).
    void* Battle_GetTalkUnit(u16 id);                                           // 0x002B087C
    u8*   Camp_GetGlobalWork();                                                 // 0x002A8A08
    void* Camp_GetActorRecord(s32 index);                                       // 0x002A89E4
    s32   Battle_CommandState(void* work, s32 mode);                            // 0x00297F40
    void* Ui_GetGlobalWork();                                                   // 0x00293C98
    void  UiSkill_DrawRowIcon(u16 slot, s32 x, s32 y, s32 prio);                // 0x002B6C80
    void  UiSkill_DrawRowIconAlt(u16 id, s32 x, s32 y, s32 prio);               // 0x002B70F0
    s32   UiText_MeasureWidth(const char* text, s32 mode);                      // 0x002B7118
    const char* Ui_GetRowName(s32 id);                                          // 0x002BCFF0
    s32   UiRow_GetValue(s32 id);                                               // 0x0028FDE4
    s16   UiRow_GetGroupIcon(u16 id);                                           // 0x0024504C
    const char* Ui_GetGroupName(u32 group);                                     // 0x0025CDF8
    s32   UiParty_GetSpareId(void* work, s32 index);                            // 0x0028D58C
    s32   UiParty_GetSpareIdAlt(void* work);                                    // 0x0028D4F0
    bool  Battle_CheckFlag(s32 id);                                             // 0x002931CC
    s32   Battle_ScriptRowA();                                                  // 0x0025CEC4
    bool  Battle_ScriptRowB();                                                  // 0x0025CE8C
    s32   Battle_ScriptRowC();                                                  // 0x0025CE6C
    s32   Party_GetDemonActiveIndex(s16 demon_id);                              // 0x0029ABC0
    s32   Party_GetDemonOrderNumber(s16 demon_id, s32 flag);                    // 0x0029AC70

    // Result-panel helpers (0x003D7630 call graph).
    f32   UiMath_Ease(s32 mode, s32 duration, s32 elapsed);                     // 0x00227414
    f32   ui_func_002b740c(f32 angle);                                                // 0x002B740C
    f32   ui_func_002820a4(f32 y, f32 x);                                           // 0x002820A4
    s32   ui_func_00297004(s32 min, s32 max);                                 // 0x00297004
    void  UiMath_SinCos(f32* out_sin, f32* out_cos, f32 angle);                 // 0x002AD5A0
    void  Matrix_TransformPoint(f32* out, const void* matrix, const f32* in);   // 0x002AD6D8
    void  Matrix_FromEuler(void* dst, u32 mode, f32 x, f32 y, f32 z);           // 0x00292C7C
    void  Effect_SetScale(void* work, f32 a, f32 b);                            // 0x002C1774
    void  Effect_SetAlphaScale(void* work, s32 a1, f32 a, f32 b, f32 c);        // 0x001DB28C
    void  UiObject_UpdateBounds(void* object);                                  // 0x002580A8
    void  UiObject_GetSize(void* object, f32* w, f32* h);                       // 0x0023ABC0
    bool  UiObject_IsReady(void* object);                                       // 0x002273F0
    void* UiScene_GetFocus();                                                   // 0x002582E8 (returns global)
    void  UiMath_ApplyMatrixA(f32* vec);                                        // 0x00211B44
    void  UiMath_ApplyMatrixB(f32* vec);                                        // 0x00211B6C
    void  UiMath_ScaleCurrent(f32 scale);                                       // 0x00221A60
    void* UiScene_GetTransform(void* scene);                                    // 0x0018F554
    void  Result_DrawEffect(ResultWork* work, void* effect, const f32* pos,
                            f32* p1, f32* p2, f32* p3);                         // 0x003D5D1C
    void  Result_UpdateSpin(ResultWork* work, s32 mode);                        // 0x003D64CC
    void  Result_UpdateFade(ResultWork* work, s32 mode);                        // 0x003D58C4
    void  Result_UpdateSlide(ResultWork* work);                                 // 0x003D6A48
    void  Result_UpdateBars(ResultWork* work);                                  // 0x003D6300
    void  Result_UpdatePanel(ResultWork* work);                                 // 0x003D704C
    void  Result_UpdateScale(ResultWork* work);                                 // 0x003D6B64
    void  Result_StartShake(ResultWork* work, s32 a, s32 b, f32 v);             // 0x003D86C0
    void  Title_DrawQuad(u32 object, u32 a, u32 b, u32 c,
                               f32 s0, f32 s1, f32 s2, f32 s3,
                               f32 s4, f32 s5, f32 s6, f32 s7,
                               f32 s8, f32 s9, f32 s10, f32 s11,
                               f32 s12, f32 s13, f32 s14, f32 s15,
                               f32 t0, f32 t1, f32 t2, f32 t3);             // 0x002BA520
    void  UiSpriteStack_Build(void* object, f32 a, f32 b, f32 c, f32 d);       // 0x0025A434
    void  Ui_DrawModel(void* gpu_state, void* model);                          // 0x002C1D3C
    f32   UiCamera_GetAngle();                                                  // 0x002F3590
    void  Battle_ClearTargets();                                                // 0x0020F564
    bool  Camp_CheckTransfer(s32 type, s32 bit);                                // 0x0025A378
    void  TalkMode_UpdateA();                                                   // 0x001F9EC0
    void  TalkMode_UpdateB();                                                   // 0x001B3DA8
    void  TalkMode_UpdateC();                                                   // 0x001B4238

}

// ---------------------------------------------------------------------------
// Shared primitives
// ---------------------------------------------------------------------------

/** 0x24C GPU viewport ring push.  The listing advances the cursor
 *  (`ldr r1,[r4]` / `add r2,r1,#1` / `str r2,[r4]`, 0x001E846C..0x001E8480)
 *  and writes the value at `8+(cursor+1)*4` (`add r3,r4,r2,lsl #2` /
 *  `str r0,[r3,#8]`, 0x001E8474..0x001E8484).  The previous value is read
 *  from `8+cursor*4` and the `+0x1C` callback runs when `+0x18` is set or the
 *  value changed (0x001E8488..0x001E84A4). */
void GpuModeSlotPush(u32 slot_offset, u32 value) {
    u8* slot = g_AsdGpuState + 0x1000 + slot_offset;
    const u32 cursor = *reinterpret_cast<u32*>(slot);      // 0x001E846C
    const u32 next = cursor + 1;                          // 0x001E8470
    const u32 old = *reinterpret_cast<u32*>(slot + 8 + cursor * 4);
    *reinterpret_cast<u32*>(slot) = next;                 // 0x001E8478/80
    *reinterpret_cast<u32*>(slot + 8 + next * 4) = value; // 0x001E8484
    if (slot[0x18] != 0 || old != value) {
        reinterpret_cast<void (*)(u32)>(*reinterpret_cast<u32*>(slot + 0x1C))(value);
        slot[0x18] = 0;
    }
}

/** 0x2AC GPU render-mode ring set.  These sites do NOT advance or store the
 *  cursor: `ldr r1,[rX]` / `add r2,rX,r1,lsl #2` / `ldr r1,[r2,#8]` /
 *  `str r0,[r2,#8]` (0x001E8B44..0x1E8B50, 0x001E8BE4..0x1E8BF0,
 *  0x001E8C5C, 0x001E8CFC, 0x001E8D94, 0x001E8E34; 0x002F18A8..0x2F18B4,
 *  0x002F1920..0x2F192C, 0x002F1A48..0x2F1A54, 0x002F1AC0..0x2F1ACC,
 *  0x002F1BA8..0x002F1BB4, 0x002F1C18..0x002F1C24).  Only the hook test
 *  remains. */
void GpuModeSlotSet(u32 slot_offset, u32 value) {
    u8* slot = g_AsdGpuState + 0x1000 + slot_offset;
    const u32 cursor = *reinterpret_cast<u32*>(slot);
    u32* entry = reinterpret_cast<u32*>(slot + 8 + cursor * 4);
    const u32 old = *entry;
    *entry = value;
    if (slot[0x18] != 0 || old != value) {
        reinterpret_cast<void (*)(u32)>(*reinterpret_cast<u32*>(slot + 0x1C))(value);
        slot[0x18] = 0;
    }
}

/** Pop one slot from the same ring (0x001E8E8C..0x001E8ECC). */
void GpuModeSlotPop(u32 slot_offset) {
    u8* slot = g_AsdGpuState + 0x1000 + slot_offset;
    u32 cursor = *reinterpret_cast<u32*>(slot);
    u32* top = reinterpret_cast<u32*>(slot + 8 + cursor * 4);
    const u32 old = *top;
    --cursor;
    *reinterpret_cast<u32*>(slot) = cursor;
    const u32 value = *reinterpret_cast<u32*>(slot + 8 + cursor * 4);
    if (slot[0x18] != 0 || old != value) {
        reinterpret_cast<void (*)(u32)>(*reinterpret_cast<u32*>(slot + 0x1C))(value);
        slot[0x18] = 0;
    }
}

/** 0x00287D54: sqrt((s3-s0)^2 + (s4-s1)^2 + (s5-s2)^2). */
f32 Distance3(f32 ax, f32 ay, f32 az, f32 bx, f32 by, f32 bz) {
    const f32 dx = bx - ax;
    const f32 dy = by - ay;
    const f32 dz = bz - az;
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}

/** 0x00227414 with the three modes selected by r0 (0x00227418..0x002274B4):
 *  0 = elapsed/duration, 1 = sin ramp, 2 = (1-cos) ramp, others = 0. */
f32 Ease(s32 mode, s32 duration, s32 elapsed) {
    if (duration == 0 || mode < 0 || mode > 2) {
        return 0.0f;
    }
    if (mode == 0) {
        return static_cast<f32>(elapsed) / static_cast<f32>(duration);
    }
    if (mode == 1) {
        const f32 t = static_cast<f32>(elapsed) * 1.570796f /
                      static_cast<f32>(duration);
        return ui_func_002b740c(t * 1.5707964f);
    }
    const f32 t = static_cast<f32>(elapsed) * 1.570796f /
                  static_cast<f32>(duration);
    return 1.0f + ui_func_002b740c(t + 4.7123889f);
}

/** 0x00297004: inclusive LCG range helper.  The listing swaps r0/r1 when
 *  min > max, multiplies [0x004651C0] by 0x41C64E6D and adds 0x3039
 *  (0x00297008..0x00297050). */
s32 RandomInclusive(s32 min, s32 max) {
    if (min > max) {
        const s32 tmp = min;
        min = max;
        max = tmp;
    }
    return ui_func_00297004(min, max);
}

/** Typed offset helpers keep every access traceable to its listing offset. */
inline f32* F32At(void* base, u32 offset) {
    return reinterpret_cast<f32*>(static_cast<u8*>(base) + offset);
}
inline s32* I32At(void* base, u32 offset) {
    return reinterpret_cast<s32*>(static_cast<u8*>(base) + offset);
}
inline u32* U32At(void* base, u32 offset) {
    return reinterpret_cast<u32*>(static_cast<u8*>(base) + offset);
}
inline u16* U16At(void* base, u32 offset) {
    return reinterpret_cast<u16*>(static_cast<u8*>(base) + offset);
}
inline s16* S16At(void* base, u32 offset) {
    return reinterpret_cast<s16*>(static_cast<u8*>(base) + offset);
}
inline u8* U8At(void* base, u32 offset) {
    return static_cast<u8*>(base) + offset;
}

// ---------------------------------------------------------------------------
// 0x002F150C: battle command ring
// ---------------------------------------------------------------------------

/** The layout node used by the 0x002BF6D0 helper.  `+0x08/+0x0A` are the
 *  signed anchor (`ldrsh r1,[r0,#8]` / `ldrsh r1,[r0,#0xa]`, 0x002F1844) and
 *  `+0x0C` points at the width word (`ldr r2,[r4,#0xc]; ldrsh r2,[r2]`,
 *  0x002F1D34..0x002F1D3C). */
struct CommandLayoutNode {
    u8  pad_00[0x08];
    s16 x;
    s16 y;
    const s16* width;
};
static_assert(offsetof(CommandLayoutNode, x) == 0x08);
static_assert(offsetof(CommandLayoutNode, y) == 0x0A);
static_assert(offsetof(CommandLayoutNode, width) == 0x0C);

namespace {

/** Draw the centered command caption at node 0x12E using the formatted
 *  buffer.  Mirrors 0x002F205C..0x002F20A4 (and the identical copies in the
 *  state-7 path at 0x002F2314). */
void Command_DrawCaption(const char* text, s32 ex, s32 ey) {
    const CommandLayoutNode* node =
        static_cast<const CommandLayoutNode*>(UiLayout_GetNode(0x15, 0x12E));
    UiFont_DrawText(3, 0x72E027FFu, text,
                    static_cast<f32>(node->x + ex),
                    static_cast<f32>(node->y + ey),
                    0.0f, 0.0f, 1.0f);
}

/** Formatted value under the caption (node 0x129, format "%d"). */
void Command_DrawValue(s32 value, s32 ex, s32 ey) {
    const CommandLayoutNode* node =
        static_cast<const CommandLayoutNode*>(UiLayout_GetNode(0x15, 0x129));
    UiFont_DrawFormatted(2, node->x + ex, node->y + ey, 1, 4, 0xC9, "%d", value);
}

/** Highlight overlay used by the two list variants:
 *  alpha -> mode slot 0x2AC push -> DrawNode(0x19D/0x124) -> mode slot pop. */
void Command_DrawSelection(BattleCommandWork* work, u32 node_id, s32 x, s32 y,
                           s32 prio) {
    UiSprite_SetGlobalAlpha(work->alpha_124c);
    GpuModeSlotSet(0x2AC, reinterpret_cast<u32>(UiGpu_SetRenderMode(6, 1, 0)));
    UiSprite_DrawNode(2, 0x15, node_id, x, y, prio);
    GpuModeSlotSet(0x2AC, reinterpret_cast<u32>(UiGpu_SetRenderMode(6, 7, 0)));
    UiSprite_SetGlobalAlpha(1.0f);
}

} // namespace
} // namespace

// The four ledger entry points below live at smt4::ui scope so that their
// declarations in ui_scene_extras.h bind to these definitions.

// DECOMP_FUNC(0x002f150c, 4204)
__attribute__((naked)) void ui_func_002f150c(BattleCommandWork* work) {
    asm volatile(
        ".word 0xe92d4ff0\n"
        ".word 0xe1a09000\n"
        ".word 0xe2800a01\n"
        ".word 0xed2d8b02\n"
        ".word 0xe2800e1a\n"
        ".word 0xe24dd05c\n"
        ".word 0xe1a05000\n"
        ".word 0xebff3693\n"
        ".word 0xe1a04000\n"
        ".word 0xe1a00005\n"
        ".word 0xebff368d\n"
        ".word 0xe1a05000\n"
        ".word 0xe2890a01\n"
        ".word 0xe2800fae\n"
        ".word 0xe1a06000\n"
        ".word 0xebff368b\n"
        ".word 0xe0808004\n"
        ".word 0xe1a00006\n"
        ".word 0xebff3685\n"
        ".word 0xe0807005\n"
        ".word 0xe3a00000\n"
        ".word 0xe3a010ab\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1a03000\n"
        ".word 0xe3a02004\n"
        ".word 0xe3a01019\n"
        ".word 0xe3a00002\n"
        ".word 0xebff37f6\n"
        ".word 0xe3a050b5\n"
        ".word 0xe1a03008\n"
        ".word 0xe3a02e11\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff37b0\n"
        ".word 0xe3a040b6\n"
        ".word 0xe1a03008\n"
        ".word 0xe284205b\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff37a8\n"
        ".word 0xe1a03008\n"
        ".word 0xe284205c\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff37a1\n"
        ".word 0xe1a03008\n"
        ".word 0xe284205d\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff379a\n"
        ".word 0xe1a03008\n"
        ".word 0xe3a02f45\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff3793\n"
        ".word 0xe1a03008\n"
        ".word 0xe284205f\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff378c\n"
        ".word 0xe1a03008\n"
        ".word 0xe2842060\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff3785\n"
        ".word 0xe1a03008\n"
        ".word 0xe2842061\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff377e\n"
        ".word 0xe1a03008\n"
        ".word 0xe3a02f46\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff3777\n"
        ".word 0xe3a040b7\n"
        ".word 0xe1a03008\n"
        ".word 0xe2842062\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff376f\n"
        ".word 0xe1a03008\n"
        ".word 0xe2842063\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff3768\n"
        ".word 0xe1a03008\n"
        ".word 0xe2842064\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff3761\n"
        ".word 0xe1a03008\n"
        ".word 0xe3a02f47\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff375a\n"
        ".word 0xe3a000bb\n"
        ".word 0xe2802062\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a03008\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d7000\n"
        ".word 0xebff3752\n"
        ".word 0xe289bc57\n"
        ".word 0xe1db03f8\n"
        ".word 0xebfeb076\n"
        ".word 0xe3500001\n"
        ".word 0x13500002\n"
        ".word 0xe3a000c3\n"
        ".word 0xe1a03008\n"
        ".word 0xe58d0004\n"
        ".word 0xe58d7000\n"
        ".word 0x0a000026\n"
        ".word 0xe280205e\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xebff3744\n"
        ".word 0xe2890b15\n"
        ".word 0xe2800fd6\n"
        ".word 0xe3a01000\n"
        ".word 0xe58d0050\n"
        ".word 0xe58d1008\n"
        ".word 0xe5900000\n"
        ".word 0xeddf8ae7\n"
        ".word 0xe3500000\n"
        ".word 0xda00013d\n"
        ".word 0xeeb08a68\n"
        ".word 0xe2890a01\n"
        ".word 0xe2800f8b\n"
        ".word 0xe58d000c\n"
        ".word 0xe59d0008\n"
        ".word 0xe0801080\n"
        ".word 0xe0810180\n"
        ".word 0xe0895100\n"
        ".word 0xe285ac57\n"
        ".word 0xe5da0078\n"
        ".word 0xe3500000\n"
        ".word 0x0a00012a\n"
        ".word 0xe1da06b0\n"
        ".word 0xebfefc34\n"
        ".word 0xe5d00003\n"
        ".word 0xe3100001\n"
        ".word 0x0a0000da\n"
        ".word 0xe5db005f\n"
        ".word 0xe3500000\n"
        ".word 0x0a00000c\n"
        ".word 0xe3a01e1a\n"
        ".word 0xe3a00015\n"
        ".word 0xebff37c0\n"
        ".word 0xe1a04000\n"
        ".word 0xe320f000\n"
        ".word 0xea000019\n"
        ".word 0xe59f232c\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xebff371d\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffffd5\n"
        ".word 0xe59f0314\n"
        ".word 0xe7900005\n"
        ".word 0xe2401c01\n"
        ".word 0xe241103b\n"
        ".word 0xe3510004\n"
        ".word 0x82400c01\n"
        ".word 0x82400059\n"
        ".word 0x83500003\n"
        ".word 0x8a000005\n"
        ".word 0xe59f12f4\n"
        ".word 0xe3a00015\n"
        ".word 0xebff37aa\n"
        ".word 0xe1a04000\n"
        ".word 0xe320f000\n"
        ".word 0xea000003\n"
        ".word 0xe59f12e0\n"
        ".word 0xe3a00015\n"
        ".word 0xebff37a4\n"
        ".word 0xe1a04000\n"
        ".word 0xe3a010c9\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a02009\n"
        ".word 0xe0800007\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a01015\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xebff373b\n"
        ".word 0xe5da0088\n"
        ".word 0xe3500000\n"
        ".word 0x0a000038\n"
        ".word 0xe59d000c\n"
        ".word 0xed900a08\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xebff37a1\n"
        ".word 0xe59f028c\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe5906000\n"
        ".word 0xe3a00006\n"
        ".word 0xebff51c0\n"
        ".word 0xe2866a01\n"
        ".word 0xe2866fab\n"
        ".word 0xe5961000\n"
        ".word 0xe0862101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d62018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe596101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c60018\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a010ce\n"
        ".word 0xe28120cf\n"
        ".word 0xe0800007\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a01015\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xebff36d7\n"
        ".word 0xe59f0214\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe5904000\n"
        ".word 0xe3a00006\n"
        ".word 0xebff51a2\n"
        ".word 0xe2844a01\n"
        ".word 0xe2844fab\n"
        ".word 0xe5941000\n"
        ".word 0xe0842101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d42018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c40018\n"
        ".word 0xeeb00a48\n"
        ".word 0xebff376d\n"
        ".word 0xe2850901\n"
        ".word 0xe2800d5e\n"
        ".word 0xe3a04000\n"
        ".word 0xe58d0054\n"
        ".word 0xe5db005f\n"
        ".word 0xe3500000\n"
        ".word 0x0a000006\n"
        ".word 0xe2841c01\n"
        ".word 0xe28110a1\n"
        ".word 0xe3a00015\n"
        ".word 0xebff3752\n"
        ".word 0xe1a05000\n"
        ".word 0xe320f000\n"
        ".word 0xea000014\n"
        ".word 0xe59d0054\n"
        ".word 0xe5900000\n"
        ".word 0xe2401c01\n"
        ".word 0xe241103b\n"
        ".word 0xe3510004\n"
        ".word 0x82400c01\n"
        ".word 0x82400059\n"
        ".word 0x83500003\n"
        ".word 0x8a000006\n"
        ".word 0xe2841c01\n"
        ".word 0xe281103b\n"
        ".word 0xe3a00015\n"
        ".word 0xebff3742\n"
        ".word 0xe1a05000\n"
        ".word 0xe320f000\n"
        ".word 0xea000004\n"
        ".word 0xe2841c01\n"
        ".word 0xe281104a\n"
        ".word 0xe3a00015\n"
        ".word 0xebff373b\n"
        ".word 0xe1a05000\n"
        ".word 0xe0890084\n"
        ".word 0xe1d520fa\n"
        ".word 0xe1d510f8\n"
        ".word 0xe2800b0d\n"
        ".word 0xe0822007\n"
        ".word 0xe1d00fb8\n"
        ".word 0xe0811008\n"
        ".word 0xe3a030d3\n"
        ".word 0xebff149d\n"
        ".word 0xe5da0088\n"
        ".word 0xe3500000\n"
        ".word 0x0a000038\n"
        ".word 0xe59d000c\n"
        ".word 0xed900a08\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xebff3739\n"
        ".word 0xe59f00ec\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe5906000\n"
        ".word 0xe3a00006\n"
        ".word 0xebff5158\n"
        ".word 0xe2866a01\n"
        ".word 0xe2866fab\n"
        ".word 0xe5961000\n"
        ".word 0xe0862101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d62018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe596101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c60018\n"
        ".word 0xe1d500fa\n"
        ".word 0xe3a010d8\n"
        ".word 0xe3a02f49\n"
        ".word 0xe0800007\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d500f8\n"
        ".word 0xe3a01015\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xebff366f\n"
        ".word 0xe59f0074\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe5905000\n"
        ".word 0xe3a00006\n"
        ".word 0xebff513a\n"
        ".word 0xe2855a01\n"
        ".word 0xe2855fab\n"
        ".word 0xe5951000\n"
        ".word 0xe0852101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d52018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe595101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c50018\n"
        ".word 0xeeb00a48\n"
        ".word 0xebff3705\n"
        ".word 0xe2844001\n"
        ".word 0xe3540005\n"
        ".word 0xbaffff98\n"
        ".word 0xea000050\n"
        ".word 0x3f800000\n"
        ".word 0x00000122\n"
        ".word 0x00005780\n"
        ".word 0x0000019e\n"
        ".word 0x0000019f\n"
        ".word 0x0044ea00\n"
        ".word 0xe2855901\n"
        ".word 0xe2855d5e\n"
        ".word 0xe3a00015\n"
        ".word 0xe5951000\n"
        ".word 0xebff36e6\n"
        ".word 0xe3a06000\n"
        ".word 0xe58d6000\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d010f8\n"
        ".word 0xe1da06f0\n"
        ".word 0xe0822007\n"
        ".word 0xe0811008\n"
        ".word 0xe3a030c9\n"
        ".word 0xebff13cf\n"
        ".word 0xe5da0088\n"
        ".word 0xe3500000\n"
        ".word 0x0a000039\n"
        ".word 0xe59d000c\n"
        ".word 0xed900a08\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xebff36e5\n"
        ".word 0xe5951000\n"
        ".word 0xe3a00015\n"
        ".word 0xebff36d2\n"
        ".word 0xe51fa070\n"
        ".word 0xe1a05000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe59a4000\n"
        ".word 0xe3a00006\n"
        ".word 0xebff5100\n"
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
        ".word 0xe5c46018\n"
        ".word 0xe1d500fa\n"
        ".word 0xe3a010ce\n"
        ".word 0xe3a02f49\n"
        ".word 0xe0800007\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d500f8\n"
        ".word 0xe3a01015\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xebff3618\n"
        ".word 0xe59a4000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe3a00006\n"
        ".word 0xebff50e4\n"
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
        ".word 0xe5c46018\n"
        ".word 0xeeb00a48\n"
        ".word 0xebff36b0\n"
        ".word 0xe59d0050\n"
        ".word 0xe5901000\n"
        ".word 0xe59d0008\n"
        ".word 0xe2800001\n"
        ".word 0xe1500001\n"
        ".word 0xe58d0008\n"
        ".word 0xbafffec5\n"
        ".word 0xe2895b0d\n"
        ".word 0xe285500c\n"
        ".word 0xe3a04000\n"
        ".word 0xe5950000\n"
        ".word 0xebfeb578\n"
        ".word 0xe1a06000\n"
        ".word 0xe5950000\n"
        ".word 0xebfeb56f\n"
        ".word 0xe0865000\n"
        ".word 0xe3a01001\n"
        ".word 0xe1a00009\n"
        ".word 0xebfe98a9\n"
        ".word 0xe59fa2f4\n"
        ".word 0xed9f8abd\n"
        ".word 0xe3500001\n"
        ".word 0xe18ab24a\n"
        ".word 0x0a00003b\n"
        ".word 0xe3a01001\n"
        ".word 0xe1a00009\n"
        ".word 0xebfe98a1\n"
        ".word 0xe3500002\n"
        ".word 0xe320f000\n"
        ".word 0x0a000123\n"
        ".word 0xe3a01001\n"
        ".word 0xe1a00009\n"
        ".word 0xebfe989b\n"
        ".word 0xe3500007\n"
        ".word 0xe320f000\n"
        ".word 0x0a000177\n"
        ".word 0xe3a01001\n"
        ".word 0xe1a00009\n"
        ".word 0xebfe9895\n"
        ".word 0xe3500003\n"
        ".word 0xe320f000\n"
        ".word 0x0a0001ce\n"
        ".word 0xe3a01001\n"
        ".word 0xe1a00009\n"
        ".word 0xebfe988f\n"
        ".word 0xe350000b\n"
        ".word 0xe320f000\n"
        ".word 0x1a000020\n"
        ".word 0xe28f1fa2\n"
        ".word 0xe28d0010\n"
        ".word 0xfaff32b8\n"
        ".word 0xe3a01f47\n"
        ".word 0xe3a00015\n"
        ".word 0xebff366a\n"
        ".word 0xe1a04000\n"
        ".word 0xe3a01003\n"
        ".word 0xe28d0010\n"
        ".word 0xebff14f8\n"
        ".word 0xe594200c\n"
        ".word 0xe1d410f8\n"
        ".word 0xe1d220f0\n"
        ".word 0xe0420000\n"
        ".word 0xe0800fa0\n"
        ".word 0xe08140c0\n"
        ".word 0xe28a1010\n"
        ".word 0xe3a00015\n"
        ".word 0xebff365d\n"
        ".word 0xe1d010fa\n"
        ".word 0xe0880004\n"
        ".word 0xee000a10\n"
        ".word 0xe0811007\n"
        ".word 0xee001a90\n"
        ".word 0xeeb01a48\n"
        ".word 0xeeb02a68\n"
        ".word 0xe59f1228\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe28d2010\n"
        ".word 0xeef80ae0\n"
        ".word 0xeef01a41\n"
        ".word 0xe3a00003\n"
        ".word 0xebff327a\n"
        ".word 0xe28dd05c\n"
        ".word 0xecbd8b02\n"
        ".word 0xe8bd8ff0\n"
        ".word 0xe3a060c3\n"
        ".word 0xe1a03008\n"
        ".word 0xe1a0200a\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d6004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff35a8\n"
        ".word 0xe1a03008\n"
        ".word 0xe1a0200b\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d6004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff35a1\n"
        ".word 0xe289ba03\n"
        ".word 0xe59b005c\n"
        ".word 0xe3500000\n"
        ".word 0x0a00001e\n"
        ".word 0xe3a00000\n"
        ".word 0xe3a06001\n"
        ".word 0xe58d0000\n"
        ".word 0xebfedb03\n"
        ".word 0xe59b105c\n"
        ".word 0xe2800c91\n"
        ".word 0xe2800007\n"
        ".word 0xe19100d0\n"
        ".word 0xebfedaf5\n"
        ".word 0xe3550000\n"
        ".word 0xe1a0a000\n"
        ".word 0x0a000069\n"
        ".word 0xebfe879e\n"
        ".word 0xe2800b11\n"
        ".word 0xe28000a8\n"
        ".word 0xe5900000\n"
        ".word 0xe3100040\n"
        ".word 0x0a00007b\n"
        ".word 0xe6bf4075\n"
        ".word 0xe1a00004\n"
        ".word 0xebff2c6c\n"
        ".word 0xe1a02000\n"
        ".word 0xe28f1e16\n"
        ".word 0xe28d0010\n"
        ".word 0xfaff326b\n"
        ".word 0xe1a00004\n"
        ".word 0xe320f000\n"
        ".word 0xebfea359\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea00007c\n"
        ".word 0xe3a00001\n"
        ".word 0xe3550000\n"
        ".word 0xe1a06000\n"
        ".word 0xe58d0000\n"
        ".word 0x0a000002\n"
        ".word 0xe3550001\n"
        ".word 0x0a00000a\n"
        ".word 0xea000018\n"
        ".word 0xe28f2e12\n"
        ".word 0xe28f1f46\n"
        ".word 0xe28d0010\n"
        ".word 0xfaff3259\n"
        ".word 0xe3a05000\n"
        ".word 0xe320f000\n"
        ".word 0xebfdac08\n"
        ".word 0xe6bf4070\n"
        ".word 0xe3a06000\n"
        ".word 0xea00006b\n"
        ".word 0xe320f000\n"
        ".word 0xebfdabf5\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000009\n"
        ".word 0xe28f20ec\n"
        ".word 0xe28f10dc\n"
        ".word 0xe28d0010\n"
        ".word 0xfaff324a\n"
        ".word 0xe3a05000\n"
        ".word 0xe320f000\n"
        ".word 0xebfdabe3\n"
        ".word 0xe6bf4070\n"
        ".word 0xe3a06000\n"
        ".word 0xea00005c\n"
        ".word 0xe3a04002\n"
        ".word 0xebfdabe6\n"
        ".word 0xe3500000\n"
        ".word 0x03a04001\n"
        ".word 0xebfe8766\n"
        ".word 0xe2800b11\n"
        ".word 0xe28000a8\n"
        ".word 0xe5900000\n"
        ".word 0xe3100040\n"
        ".word 0x0a00000e\n"
        ".word 0xe0450004\n"
        ".word 0xe2800001\n"
        ".word 0xe6bf4070\n"
        ".word 0xe1a00004\n"
        ".word 0xebff2c32\n"
        ".word 0xe1a02000\n"
        ".word 0xe28f1078\n"
        ".word 0xe28d0010\n"
        ".word 0xfaff3231\n"
        ".word 0xe3a01001\n"
        ".word 0xe1a00004\n"
        ".word 0xebfea34b\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000042\n"
        ".word 0xe59b005c\n"
        ".word 0xe0451004\n"
        ".word 0xe59f4060\n"
        ".word 0xe0890200\n"
        ".word 0xe0800081\n"
        ".word 0xe19040f4\n"
        ".word 0xe1a00004\n"
        ".word 0xebff2c20\n"
        ".word 0xe1a02000\n"
        ".word 0xe28f1030\n"
        ".word 0xe28d0010\n"
        ".word 0xfaff321f\n"
        ".word 0xe3a01001\n"
        ".word 0xe1a00004\n"
        ".word 0xebfea339\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000030\n"
        ".word 0x0000011e\n"
        ".word 0x00000000\n"
        ".word 0x6c616e41\n"
        ".word 0x00657a79\n"
        ".word 0x72e027ff\n"
        ".word 0x00007325\n"
        ".word 0x61747441\n"
        ".word 0x00006b63\n"
        ".word 0x6f6f6853\n"
        ".word 0x00000074\n"
        ".word 0x0000341c\n"
        ".word 0xe1da04b6\n"
        ".word 0xebff1ce6\n"
        ".word 0xe5d0000a\n"
        ".word 0xe3500001\n"
        ".word 0x0a000006\n"
        ".word 0xe24f2030\n"
        ".word 0xe24f1038\n"
        ".word 0xe28d0010\n"
        ".word 0xfaff3205\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000003\n"
        ".word 0xe24f2044\n"
        ".word 0xe24f1054\n"
        ".word 0xe28d0010\n"
        ".word 0xfaff31fe\n"
        ".word 0xe35a0000\n"
        ".word 0xe3a05000\n"
        ".word 0x0a000013\n"
        ".word 0xe1da04b6\n"
        ".word 0xebfd4c0d\n"
        ".word 0xe6bf4070\n"
        ".word 0xe3a06000\n"
        ".word 0xea00000e\n"
        ".word 0xe59b005c\n"
        ".word 0xe59f43e8\n"
        ".word 0xe0890200\n"
        ".word 0xe0800085\n"
        ".word 0xe19040f4\n"
        ".word 0xe1a00004\n"
        ".word 0xebff2bec\n"
        ".word 0xe1a02000\n"
        ".word 0xe24f10a0\n"
        ".word 0xe28d0010\n"
        ".word 0xfaff31eb\n"
        ".word 0xe1a00004\n"
        ".word 0xe320f000\n"
        ".word 0xebfea2d9\n"
        ".word 0xe1a05000\n"
        ".word 0xe59f13b4\n"
        ".word 0xe3a00015\n"
        ".word 0xebff3599\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d000f8\n"
        ".word 0xeeb01a48\n"
        ".word 0xe0811007\n"
        ".word 0xe0800008\n"
        ".word 0xee001a90\n"
        ".word 0xee000a10\n"
        ".word 0xeeb02a68\n"
        ".word 0xeef01a41\n"
        ".word 0xe51f10f0\n"
        ".word 0xe28d2010\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe3a00003\n"
        ".word 0xebff31b5\n"
        ".word 0xe59f1370\n"
        ".word 0xe3a00015\n"
        ".word 0xebff3587\n"
        ".word 0xe3560000\n"
        ".word 0xe320f000\n"
        ".word 0x0a00000b\n"
        ".word 0xe3a01000\n"
        ".word 0xe58d1004\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d000f8\n"
        ".word 0xe3a030c9\n"
        ".word 0xe0812007\n"
        ".word 0xe0801008\n"
        ".word 0xe1a00004\n"
        ".word 0xebff13a4\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000006\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d000f8\n"
        ".word 0xe3a030c9\n"
        ".word 0xe0812007\n"
        ".word 0xe0801008\n"
        ".word 0xe1a00004\n"
        ".word 0xebff13f9\n"
        ".word 0xe59f1310\n"
        ".word 0xe3a00015\n"
        ".word 0xebff356e\n"
        ".word 0xe3a02004\n"
        ".word 0xe28d4004\n"
        ".word 0xe28f3c03\n"
        ".word 0xe3a010c9\n"
        ".word 0xe58d2000\n"
        ".word 0xe884002a\n"
        ".word 0xe3a03001\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0812007\n"
        ".word 0xe0801008\n"
        ".word 0xe3a00002\n"
        ".word 0xebff3008\n"
        ".word 0xe28dd05c\n"
        ".word 0xecbd8b02\n"
        ".word 0xe8bd8ff0\n"
        ".word 0xe3a040c3\n"
        ".word 0xe1a03008\n"
        ".word 0xe1a0200a\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff34ba\n"
        ".word 0xe1a03008\n"
        ".word 0xe1a0200b\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d7000\n"
        ".word 0xebff34b3\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xebfe86be\n"
        ".word 0xe2800b11\n"
        ".word 0xe28000a8\n"
        ".word 0xe5900000\n"
        ".word 0xe3100040\n"
        ".word 0x0a000006\n"
        ".word 0xebfe86b8\n"
        ".word 0xe1a01005\n"
        ".word 0xe320f000\n"
        ".word 0xebfe6cf2\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000004\n"
        ".word 0xe320f000\n"
        ".word 0xebfe86b0\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xebfe6cc3\n"
        ".word 0xe6bf4070\n"
        ".word 0xe1a00004\n"
        ".word 0xebff2b80\n"
        ".word 0xe1a02000\n"
        ".word 0xe24f1e25\n"
        ".word 0xe28d0010\n"
        ".word 0xfaff317f\n"
        ".word 0xe59f1214\n"
        ".word 0xe3a00015\n"
        ".word 0xebff3531\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d020f8\n"
        ".word 0xeeb01a48\n"
        ".word 0xe0810007\n"
        ".word 0xe0821008\n"
        ".word 0xee000a90\n"
        ".word 0xee001a10\n"
        ".word 0xeeb02a68\n"
        ".word 0xeef01a41\n"
        ".word 0xe51f1290\n"
        ".word 0xe28d2010\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe3a00003\n"
        ".word 0xebff314d\n"
        ".word 0xe59f11d0\n"
        ".word 0xe3a00015\n"
        ".word 0xebff351f\n"
        ".word 0xe3a05000\n"
        ".word 0xe58d5000\n"
        ".word 0xe58d5004\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d000f8\n"
        ".word 0xe3a030c9\n"
        ".word 0xe0812007\n"
        ".word 0xe0801008\n"
        ".word 0xe1a00004\n"
        ".word 0xebff133e\n"
        ".word 0xe59f11a0\n"
        ".word 0xe3a00015\n"
        ".word 0xebff3512\n"
        ".word 0xe3a01004\n"
        ".word 0xe28f3f65\n"
        ".word 0xe3a020c9\n"
        ".word 0xe88d002e\n"
        ".word 0xe3a03001\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0812007\n"
        ".word 0xe0801008\n"
        ".word 0xe3a00002\n"
        ".word 0xebff2fae\n"
        ".word 0xe28dd05c\n"
        ".word 0xecbd8b02\n"
        ".word 0xe8bd8ff0\n"
        ".word 0xe3a000c3\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a03008\n"
        ".word 0xe1a0200a\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d7000\n"
        ".word 0xebff3460\n"
        ".word 0xe0890085\n"
        ".word 0xe3a04dd2\n"
        ".word 0xe3a01000\n"
        ".word 0xe19040f4\n"
        ".word 0xe1a00004\n"
        ".word 0xebff314c\n"
        ".word 0xe1a02000\n"
        ".word 0xe24f1fd6\n"
        ".word 0xe28d0010\n"
        ".word 0xfaff313d\n"
        ".word 0xe1a00004\n"
        ".word 0xe320f000\n"
        ".word 0xebfe76b4\n"
        ".word 0xe1a05000\n"
        ".word 0xe59f10fc\n"
        ".word 0xe3a00015\n"
        ".word 0xebff34eb\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d000f8\n"
        ".word 0xeeb01a48\n"
        ".word 0xe0811007\n"
        ".word 0xe0800008\n"
        ".word 0xee001a90\n"
        ".word 0xee000a10\n"
        ".word 0xeeb02a68\n"
        ".word 0xeef01a41\n"
        ".word 0xe51f13a8\n"
        ".word 0xe28d2010\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe3a00003\n"
        ".word 0xebff3107\n"
        ".word 0xe59f10b8\n"
        ".word 0xe3a00015\n"
        ".word 0xebff34d9\n"
        ".word 0xe3a01000\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d000f8\n"
        ".word 0xe3a030c9\n"
        ".word 0xe0812007\n"
        ".word 0xe0801008\n"
        ".word 0xe1a00004\n"
        ".word 0xebff306e\n"
        ".word 0xe59f6094\n"
        ".word 0xe3a00015\n"
        ".word 0xe1a01006\n"
        ".word 0xebff34cc\n"
        ".word 0xe28f1088\n"
        ".word 0xe3a040c9\n"
        ".word 0xe3a02001\n"
        ".word 0xe58d1008\n"
        ".word 0xe88d0014\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d000f8\n"
        ".word 0xe3a03001\n"
        ".word 0xe0812007\n"
        ".word 0xe0801008\n"
        ".word 0xe3a00002\n"
        ".word 0xebff2f67\n"
        ".word 0xe1a01006\n"
        ".word 0xe3a00015\n"
        ".word 0xebff34bd\n"
        ".word 0xe3a01004\n"
        ".word 0xe88d0012\n"
        ".word 0xe28d1008\n"
        ".word 0xe28f2038\n"
        ".word 0xe8810024\n"
        ".word 0xe3a03001\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0812007\n"
        ".word 0xe0801008\n"
        ".word 0xe3a00002\n"
        ".word 0xebff2f58\n"
        ".word 0xe28dd05c\n"
        ".word 0xecbd8b02\n"
        ".word 0xe8bd8ff0\n"
        ".word 0x0000341a\n"
        ".word 0x0000012e\n"
        ".word 0x0000012f\n"
        ".word 0x00000129\n"
        ".word 0x00006425\n"
        ".word 0x0000012d\n"
        ".word 0x0000002a\n"
        ".word 0xe3a000c3\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a03008\n"
        ".word 0xe1a0200a\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d7000\n"
        ".word 0xebff3403\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xebfe860e\n"
        ".word 0xe2800b11\n"
        ".word 0xe28000a8\n"
        ".word 0xe5900000\n"
        ".word 0xe3100a01\n"
        ".word 0x03a06000\n"
        ".word 0x01a04006\n"
        ".word 0x0a000008\n"
        ".word 0xe20500ff\n"
        ".word 0xebfdaa5d\n"
        ".word 0xe1a02000\n"
        ".word 0xe28f10e8\n"
        ".word 0xe28d0010\n"
        ".word 0xfaff30da\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000013\n"
        ".word 0xe284002e\n"
        ".word 0xebfe8349\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a00000b\n"
        ".word 0xe1560005\n"
        ".word 0x12866001\n"
        ".word 0x1a000008\n"
        ".word 0xe20400ff\n"
        ".word 0xebfdaa4c\n"
        ".word 0xe1a02000\n"
        ".word 0xe28f10a4\n"
        ".word 0xe28d0010\n"
        ".word 0xfaff30c9\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000002\n"
        ".word 0xe2844001\n"
        ".word 0xe3540006\n"
        ".word 0xbaffffeb\n"
        ".word 0xe51f10dc\n"
        ".word 0xe3a00015\n"
        ".word 0xebff3475\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d010f8\n"
        ".word 0xeeb01a48\n"
        ".word 0xe0820007\n"
        ".word 0xe0811008\n"
        ".word 0xee000a90\n"
        ".word 0xee001a10\n"
        ".word 0xeeb02a68\n"
        ".word 0xeef01a41\n"
        ".word 0xe51f1580\n"
        ".word 0xe28d2010\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe3a00003\n"
        ".word 0xebff3091\n"
        ".word 0xe51f1120\n"
        ".word 0xe3a00015\n"
        ".word 0xebff3463\n"
        ".word 0xe3a01000\n"
        ".word 0xe58d1000\n"
        ".word 0xe58d1004\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d000f8\n"
        ".word 0xe3a030c9\n"
        ".word 0xe0812007\n"
        ".word 0xe0801008\n"
        ".word 0xe3e00002\n"
        ".word 0xebff1282\n"
        ".word 0xe28dd05c\n"
        ".word 0xecbd8b02\n"
        ".word 0xe8bd8ff0\n"
        ".word 0x00007325\n"
    );
}
#if 0
// Original partial readable draft retained for reconstruction; not compiled.
void ui_func_002f150c(BattleCommandWork* work) {
    // Anchor sprites: 0x11A0 then 0x12B8; the two positions are summed into
    // (ex, ey) at 0x002F1528..0x002F1558.
    const s32 x0 = UiAnimSprite_GetPosX(&work->sprite_11a0);
    const s32 y0 = UiAnimSprite_GetPosY(&work->sprite_11a0);
    const s32 x1 = UiAnimSprite_GetPosX(&work->sprite_12b8);
    const s32 y1 = UiAnimSprite_GetPosY(&work->sprite_12b8);
    const s32 ex = x1 + x0;                                  // r8
    const s32 ey = y1 + y0;                                  // r7

    // Fixed command-ring chrome.  Every id below is the literal loaded before
    // the corresponding 0x002BF460/0x002BF558 call in 0x002F1578..0x002F1710.
    UiSprite_DrawPanel(2, 0x19, 4, 0, 0, 0xAB);              // 0x002F1578
    UiSprite_DrawNode(2, 0x15, 0x110, ex, ey, 0xB5);         // 0x002F1598
    UiSprite_DrawNode(2, 0x15, 0x111, ex, ey, 0xB6);         // 0x002F15B8
    UiSprite_DrawNode(2, 0x15, 0x112, ex, ey, 0xB6);         // 0x002F15D4
    UiSprite_DrawNode(2, 0x15, 0x113, ex, ey, 0xB6);         // 0x002F15F0
    UiSprite_DrawNode(2, 0x15, 0x114, ex, ey, 0xB6);         // 0x002F160C
    UiSprite_DrawNode(2, 0x15, 0x115, ex, ey, 0xB6);         // 0x002F1628
    UiSprite_DrawNode(2, 0x15, 0x116, ex, ey, 0xB6);         // 0x002F1644
    UiSprite_DrawNode(2, 0x15, 0x117, ex, ey, 0xB6);         // 0x002F1660
    UiSprite_DrawNode(2, 0x15, 0x118, ex, ey, 0xB6);         // 0x002F167C
    UiSprite_DrawNode(2, 0x15, 0x119, ex, ey, 0xB7);         // 0x002F169C
    UiSprite_DrawNode(2, 0x15, 0x11A, ex, ey, 0xB7);         // 0x002F16B8
    UiSprite_DrawNode(2, 0x15, 0x11B, ex, ey, 0xB7);         // 0x002F16D4
    UiSprite_DrawNode(2, 0x15, 0x11C, ex, ey, 0xB5);         // 0x002F16F0
    UiSprite_DrawNode(2, 0x15, 0x11D, ex, ey, 0xBB);         // 0x002F1710

    // Touch region at work+0x5738: state 1/2 selects the pressed variant
    // (0x002F1718..0x002F1738).
    const s16 touch_handle = *reinterpret_cast<const s16*>(
        reinterpret_cast<const u8*>(work) + 0x5738);
    const s32 touch = UiTouch_GetRegionTouchState(touch_handle);
    if (touch == 1 || touch == 2) {
        UiSprite_DrawNode(2, 0x15, 0x122, ex, ey, 0xC3);     // 0x002F17D8
    } else {
        UiSprite_DrawNode(2, 0x15, 0x121, ex, ey, 0xC3);     // 0x002F1748
    }

    // Row loop.  Count at work+0x5758, records at work+0x5700, stride 0x2C
    // (0x002F1760..0x002F178C).
    const s32 count = work->count_5758;
    for (s32 i = 0; i < count; ++i) {
        // Slot arithmetic exactly as in the listing: work + i*0x2C, then the
        // record fields at +0x5700+0x60/+0x78/+0x88 (0x002F178C..0x002F17A0).
        u8* const entry = reinterpret_cast<u8*>(work) + 0x5700 + i * 0x2C;
        const u16 entry_id = *reinterpret_cast<const u16*>(entry + 0x60);
        if (entry[0x78] == 0) {                              // 0x002F1794
            continue;
        }
        void* unit = Battle_GetTalkUnit(entry_id);           // 0x002F17A0
        const u8 unit_flags = *reinterpret_cast<const u8*>(
            static_cast<const u8*>(unit) + 3);
        if ((unit_flags & 1) != 0) {                         // 0x002F17AC
            // Icon anchor: variant 0x1A0, otherwise 0x19E for the two id
            // ranges and 0x19F for everything else (0x002F17B4..0x002F1838).
            u32 node_id;
            if (work->variant_575f != 0) {
                node_id = 0x1A0;
            } else {
                const u32 value = *reinterpret_cast<const u32*>(
                    reinterpret_cast<const u8*>(work) + 0x5780 + i * 0x2C);
                if (value - 0x13B <= 4 || value - 0x159 <= 3) {
                    node_id = 0x19E;
                } else {
                    node_id = 0x19F;
                }
            }
            const CommandLayoutNode* node =
                static_cast<const CommandLayoutNode*>(
                    UiLayout_GetNode(0x15, node_id));
            UiSprite_DrawPanel(2, 0x15, 9, node->x + ex, node->y + ey, 0xC9);

            // 0x002F18D8: the 0x19D selection quad uses the icon node's
            // anchor, not the raw ring origin.
            if (entry[0x88] != 0) {                          // 0x002F1868
                Command_DrawSelection(work, 0x19D,
                                      node->x + ex, node->y + ey, 0xCE);
            }

            // Five party-slot icons under the row (0x002F1958..0x002F1B00).
            for (s32 j = 0; j < 5; ++j) {
                u32 id;
                if (work->variant_575f != 0) {
                    id = static_cast<u32>(0x1A1 + j);        // 0x002F1974
                } else {
                    const u32 value = *reinterpret_cast<const u32*>(
                        reinterpret_cast<const u8*>(work) + 0x5780 + i * 0x2C);
                    if (value - 0x13B <= 4 || value - 0x159 <= 3) {
                        id = static_cast<u32>(0x13B + j);    // 0x002F19B4
                    } else {
                        id = static_cast<u32>(0x14A + j);    // 0x002F19D0
                    }
                }
                const CommandLayoutNode* slot_node =
                    static_cast<const CommandLayoutNode*>(
                        UiLayout_GetNode(0x15, id));
                const u16 slot = work->party_ids_34f8[j];
                UiSkill_DrawRowIcon(slot, slot_node->x + ex,
                                    slot_node->y + ey, 0xD3);
                if (entry[0x88] != 0) {                      // 0x002F1A08
                    Command_DrawSelection(work, 0x124,
                                          slot_node->x + ex,
                                          slot_node->y + ey, 0xD8);
                }
            }
        } else {
            // Unavailable row: draw the generic icon at the id from +0x80
            // (0x002F1B20..0x002F1B54), then a single 0x124 marker at that
            // node's anchor (0x002F1BD4), with no party-slot loop.
            const u32 id = *reinterpret_cast<const u32*>(
                reinterpret_cast<const u8*>(work) + 0x5780 + i * 0x2C);
            const CommandLayoutNode* node =
                static_cast<const CommandLayoutNode*>(UiLayout_GetNode(0x15, id));
            UiSkill_DrawItemIconAndCount(entry_id, node->x + ex,
                                         node->y + ey, 0xC9, 0);
            if (entry[0x88] != 0) {                          // 0x002F1B58
                node = static_cast<const CommandLayoutNode*>(
                    UiLayout_GetNode(0x15, id));             // 0x002F1B80
                Command_DrawSelection(work, 0x124,
                                      node->x + ex, node->y + ey, 0xCE);
            }
        }
    }

    // Scroll cursor: work+0x340C, scroll + selected gives the absolute row
    // (0x002F1C68..0x002F1C90).
    UiListCursor* cursor = work->cursor_340c;
    const s32 scroll = UiListCursor_GetScrollOffset(cursor);
    const s32 selected = UiListCursor_GetSelectedRow(cursor);
    const s32 row = scroll + selected;                       // r5
    const s32 state = Battle_CommandState(work, 1);          // 0x002F1C94

    if (state == 1) {
        // Attack/command page (0x002F1D9C..0x002F2148).  The second id is
        // `0x11E | (0x11E >> 4)` = 0x11F (0x002F1C98..0x002F1CA8).
        UiSprite_DrawNode(2, 0x15, 0x11E, ex, ey, 0xC3);
        UiSprite_DrawNode(2, 0x15, 0x11F, ex, ey, 0xC3);

        const s32 actor = *reinterpret_cast<const s32*>(
            reinterpret_cast<const u8*>(work) + 0x305C);     // [fp+0x5C]
        char text[0x40] = {};
        s32 value = 0;                                       // r5
        s32 bars = 1;                                        // r6
        s32 target_id = 0;                                   // r4
        // 0x002F1DE8/0x002F1E64: the stack draw-bars gate is 0 on the actor
        // path and 1 on the non-actor path (both paths keep r6 = 1).
        const s32 draw_bars_gate = (actor == 0) ? 1 : 0;

        if (actor != 0) {
            // Actor path: the camp work holds a row byte at +0x9107+actor
            // which 0x002A89E4 turns into the actor record.
            u8* camp = Camp_GetGlobalWork();                 // 0x002F1DF4
            const s8 actor_row = *reinterpret_cast<const s8*>(
                camp + 0x9107 + actor);                      // 0x002F1DFC
            void* const record = Camp_GetActorRecord(actor_row); // 0x002F1E08
            if (row == 0) {
                // 0x002F1FC0..0x002F201C: talk-entry category selects the
                // caption, then the record's +0x46 id drives the icon.
                const u16 talk_id = *reinterpret_cast<const u16*>(
                    static_cast<const u8*>(record) + 0x46);
                const u8* talk = static_cast<const u8*>(
                    Battle_GetTalkEntry(talk_id));
                UiFont_FormatString(text, talk[0x0A] == 1 ? "Shoot" : "Attack");
                value = 0;
                if (record != nullptr) {
                    target_id = UiRow_GetGroupIcon(talk_id);
                    bars = 0;
                }
            } else {
                // 0x002F1E18..0x002F1F48: flags bit 0x40 selects the plain
                // row id, otherwise the indexed +0x341A table.
                const void* global = Ui_GetGlobalWork();
                const u32 flags = *reinterpret_cast<const u32*>(
                    static_cast<const u8*>(global) + 0x44A8);
                if ((flags & 0x40) != 0) {
                    target_id = row;
                } else {
                    target_id = *reinterpret_cast<const s16*>(
                        reinterpret_cast<const u8*>(work) + 0x341A +
                        actor * 0x10 + row * 2);
                }
                UiFont_FormatString(text, "%s", Ui_GetRowName(target_id));
                value = Party_GetDemonActiveIndex(static_cast<s16>(target_id));
            }
        } else if (row == 0) {
            UiFont_FormatString(text, "Attack");             // 0x002F1E90
            target_id = Battle_ScriptRowA();                 // 0x002F1E9C
            bars = 0;                                        // 0x002F1EA4
        } else if (row == 1) {
            if (Battle_ScriptRowB()) {                       // 0x002F1EB0
                UiFont_FormatString(text, "Shoot");          // 0x002F1ECC
                target_id = Battle_ScriptRowC();             // 0x002F1ED8
                bars = 0;
            } else {
                // Fall through to the generic indexed path with r4 = 1.
                const s32 base = 1;
                const void* global = Ui_GetGlobalWork();
                const u32 flags = *reinterpret_cast<const u32*>(
                    static_cast<const u8*>(global) + 0x44A8);
                if ((flags & 0x40) != 0) {
                    target_id = row - base + 1;              // 0x002F1F18
                } else {
                    target_id = *reinterpret_cast<const s16*>(
                        reinterpret_cast<const u8*>(work) + 0x341C +
                        (row - base) * 2);                   // 0x002F1F60
                }
                UiFont_FormatString(text, "%s", Ui_GetRowName(target_id));
                value = Party_GetDemonOrderNumber(
                    static_cast<s16>(target_id), 1);
            }
        } else {
            // 0x002F1EE8..0x002F1F90: r4 is 1 or 2 depending on the script
            // row-B query, and the indexed table is +0x341C.
            const s32 base = Battle_ScriptRowB() ? 2 : 1;
            const void* global = Ui_GetGlobalWork();
            const u32 flags = *reinterpret_cast<const u32*>(
                static_cast<const u8*>(global) + 0x44A8);
            if ((flags & 0x40) != 0) {
                target_id = row - base + 1;                  // 0x002F1F10
            } else {
                target_id = *reinterpret_cast<const s16*>(
                    reinterpret_cast<const u8*>(work) + 0x341C +
                    (row - base) * 2);                       // 0x002F1F60
            }
            UiFont_FormatString(text, "%s", Ui_GetRowName(target_id));
            value = Party_GetDemonOrderNumber(static_cast<s16>(target_id), 1);
        }

        Command_DrawCaption(text, ex, ey);                   // 0x002F205C
        const CommandLayoutNode* icon =
            static_cast<const CommandLayoutNode*>(UiLayout_GetNode(0x15, 0x12F));
        if (bars != 0) {
            UiParty_DrawDemonBars(static_cast<s16>(target_id),
                                  icon->x + ex, icon->y + ey, 0xC9,
                                  draw_bars_gate, 0);
        } else {
            UiSkill_DrawRowIconAlt(static_cast<u16>(target_id),
                                   icon->x + ex, icon->y + ey, 0xC9);
        }
        Command_DrawValue(value, ex, ey);                    // 0x002F2108
        return;
    }

    if (state == 2) {
        // Skill/item page (0x002F2154..0x002F22B8), same 0x11E/0x11F pair.
        UiSprite_DrawNode(2, 0x15, 0x11E, ex, ey, 0xC3);
        UiSprite_DrawNode(2, 0x15, 0x11F, ex, ey, 0xC3);

        const void* global = Ui_GetGlobalWork();
        s32 target_id;
        const u32 flags = *reinterpret_cast<const u32*>(
            static_cast<const u8*>(global) + 0x44A8);
        if ((flags & 0x40) != 0) {
            // 0x002F21B0 reloads the work pointer before the id lookup.
            target_id = UiParty_GetSpareId(
                const_cast<void*>(Ui_GetGlobalWork()), row);
        } else {
            // 0x002F21CC
            target_id = UiParty_GetSpareIdAlt(
                const_cast<void*>(Ui_GetGlobalWork()));
        }
        char text[0x40] = {};
        UiFont_FormatString(text, "%s", Ui_GetRowName(target_id));
        Command_DrawCaption(text, ex, ey);
        const CommandLayoutNode* icon =
            static_cast<const CommandLayoutNode*>(UiLayout_GetNode(0x15, 0x12F));
        UiParty_DrawDemonBars(static_cast<s16>(target_id),
                              icon->x + ex, icon->y + ey, 0xC9, 0, 0);
        Command_DrawValue(0, ex, ey);
        return;
    }

    if (state == 7) {
        // Enemy/row page (0x002F22BC..0x002F2410).
        UiSprite_DrawNode(2, 0x15, 0x11E, ex, ey, 0xC3);
        const s16 target_id = work->row_ids_3480[row];
        char text[0x40] = {};
        UiFont_FormatString(text, "%s", Quest_GetObjectiveName(
            static_cast<u16>(target_id)));
        const s32 value = UiRow_GetValue(target_id);
        Command_DrawCaption(text, ex, ey);

        const CommandLayoutNode* icon =
            static_cast<const CommandLayoutNode*>(UiLayout_GetNode(0x15, 0x12F));
        Quest_DrawObjectiveIcon(static_cast<u16>(target_id),
                                icon->x + ex, icon->y + ey, 0xC9);

        const CommandLayoutNode* mark =
            static_cast<const CommandLayoutNode*>(UiLayout_GetNode(0x15, 0x12D));
        UiFont_DrawFormatted(2, mark->x + ex, mark->y + ey, 1, 1, 0xC9,
                             "*", 0);
        UiFont_DrawFormatted(2, mark->x + ex, mark->y + ey, 1, 4, 0xC9,
                             "%d", value);
        return;
    }

    if (state == 3) {
        // Group page (0x002F2430..0x002F2570).
        UiSprite_DrawNode(2, 0x15, 0x11E, ex, ey, 0xC3);
        const void* global = Ui_GetGlobalWork();
        const u32 flags = *reinterpret_cast<const u32*>(
            static_cast<const u8*>(global) + 0x44A8);
        char text[0x40] = {};
        if ((flags & 0x1000) != 0) {
            UiFont_FormatString(text, "%s",
                                Ui_GetGroupName(static_cast<u32>(row) & 0xFF));
        } else {
            s32 found = 0;                                   // r6
            for (s32 g = 0; g < 6; ++g) {                    // r4
                if (!Battle_CheckFlag(g + 0x2E)) {
                    continue;
                }
                if (found != row) {
                    ++found;
                    continue;
                }
                UiFont_FormatString(text, "%s",
                                    Ui_GetGroupName(static_cast<u32>(g) & 0xFF));
                break;
            }
        }
        Command_DrawCaption(text, ex, ey);
        const CommandLayoutNode* icon =
            static_cast<const CommandLayoutNode*>(UiLayout_GetNode(0x15, 0x12F));
        // 0x002F2560: mvn r0,#2 -> -3, not -2.
        UiParty_DrawDemonBars(-3, icon->x + ex, icon->y + ey, 0xC9, 0, 0);
        return;
    }

    if (state == 11) {
        // "Analyze" label centered inside node 0x11C (0x002F1D0C..0x002F1D90).
        char text[0x40] = {};
        UiFont_FormatString(text, "Analyze");
        const CommandLayoutNode* node =
            static_cast<const CommandLayoutNode*>(UiLayout_GetNode(0x15, 0x11C));
        const s32 width = UiText_MeasureWidth(text, 3);
        s32 offset = *node->width - width;
        offset += static_cast<u32>(offset) >> 31;
        const s32 cx = ex + node->x + (offset >> 1);
        const CommandLayoutNode* anchor =
            static_cast<const CommandLayoutNode*>(UiLayout_GetNode(0x15, 0x12E));
        UiFont_DrawText(3, 0x72E027FFu, text,
                        static_cast<f32>(cx),
                        static_cast<f32>(ey + anchor->y),
                        0.0f, 0.0f, 1.0f);
        return;
    }
}
#endif

// ---------------------------------------------------------------------------
// 0x00243E8C: effect-menu option-row renderer (effMenu.cpp)
// ---------------------------------------------------------------------------

namespace {

/** List node allocated through 0x002C34A4 and linked by 0x002573EC.  The
 *  listing stores the node type at +0x04 and up to six words at +0x08
 *  (0x00244904..0x00244924 and the identical blocks at 0x0024496C..0x00244990,
 *  0x00244A00..0x00244A0C, 0x00244B3C..0x00244B5C, 0x00244C88..0x00244CB0,
 *  0x00244CDC..0x00244CFC and 0x00244D38..0x00244E54). */
struct EffMenuListNode {
    u32 field_00;
    u32 type_04;                    // +0x04: 4 (bar) or 6 (sprite)
    u32 field_08[6];                // +0x08..+0x1C
};
static_assert(offsetof(EffMenuListNode, type_04) == 0x04);
static_assert(offsetof(EffMenuListNode, field_08) == 0x08);

void EffMenu_PushNode(u32 type, u32 a, u32 b, u32 c, u32 d, u32 e, u32 f) {
    // 0x002448F8..0x00244900 stores [sp]=0x10 (a4) and [sp+4]=1 (flag).
    EffMenuListNode* node = static_cast<EffMenuListNode*>(
        AsdWork_Alloc(0x10000, 0x100, 0, 0x68, 0x10, 1));
    node->type_04 = type;
    node->field_08[0] = a;
    node->field_08[1] = b;
    node->field_08[2] = c;
    node->field_08[3] = d;
    node->field_08[4] = e;
    node->field_08[5] = f;
    UiEffectList_Push(node, 3);
}

/** Color word expansion used by the three-bar loop at 0x00244A98..0x00244AFC:
 *  v | v<<16 | 0xFF000000 | v<<8. */
u32 EffMenu_ExpandColor(u32 value) {
    return (value | (value << 16)) | (0xFF000000u | (value << 8));
}

/** Clamp a float loaded from the scene to [0,1] (0x0024461C..0x00244688). */
f32 Clamp01(f32 value) {
    if (value < 0.0f) {
        return 0.0f;
    }
    if (value > 1.0f) {
        return 1.0f;
    }
    return value;
}

} // namespace

// DECOMP_FUNC(0x00243e8c, 4216)
__attribute__((naked)) s32 ui_func_00243e8c(EffMenuItemState* item, EffMenuSlot* slot, s32 count) {
    asm volatile(
        ".word 0xe92d4ff7\n"
        ".word 0xe1a04000\n"
        ".word 0xed2d8b06\n"
        ".word 0xe24dd038\n"
        ".word 0xe59d0058\n"
        ".word 0xeddf9abb\n"
        ".word 0xed9f9abb\n"
        ".word 0xe3500000\n"
        ".word 0xdeb08a69\n"
        ".word 0xe59f02e4\n"
        ".word 0xe58d0030\n"
        ".word 0xda000002\n"
        ".word 0xed9d0a16\n"
        ".word 0xeeb80ac0\n"
        ".word 0xee898a00\n"
        ".word 0xed941a01\n"
        ".word 0xe28d2008\n"
        ".word 0xed8d1a02\n"
        ".word 0xedcd9a07\n"
        ".word 0xe5d40000\n"
        ".word 0xed940a03\n"
        ".word 0xedd40a05\n"
        ".word 0xe3500001\n"
        ".word 0xe3a06001\n"
        ".word 0x0a00002d\n"
        ".word 0xe3500002\n"
        ".word 0x13a00000\n"
        ".word 0x15c40000\n"
        ".word 0x0a000031\n"
        ".word 0xe5941008\n"
        ".word 0xe59f7294\n"
        ".word 0xe28d001c\n"
        ".word 0xe0803106\n"
        ".word 0xe7821106\n"
        ".word 0xed839a00\n"
        ".word 0xe5973050\n"
        ".word 0xe59f0280\n"
        ".word 0xe1530006\n"
        ".word 0x85876050\n"
        ".word 0xe5975050\n"
        ".word 0xe2843018\n"
        ".word 0xe7922105\n"
        ".word 0xe38224ff\n"
        ".word 0xe587205c\n"
        ".word 0xe28d201c\n"
        ".word 0xe0829105\n"
        ".word 0xe5992000\n"
        ".word 0xe5872084\n"
        ".word 0xedd41a00\n"
        ".word 0xed942a04\n"
        ".word 0xecd32a02\n"
        ".word 0xe2803fda\n"
        ".word 0xedc01ad4\n"
        ".word 0xed801ad5\n"
        ".word 0xe5801358\n"
        ".word 0xed800ad7\n"
        ".word 0xed802ad8\n"
        ".word 0xedc00ad9\n"
        ".word 0xecc32a02\n"
        ".word 0xe5941020\n"
        ".word 0xe5801370\n"
        ".word 0xe59d1054\n"
        ".word 0xe891100c\n"
        ".word 0xe591100c\n"
        ".word 0xe5801380\n"
        ".word 0xe2800fdd\n"
        ".word 0xe880100c\n"
        ".word 0xe5d70009\n"
        ".word 0xe3500000\n"
        ".word 0x1a00001c\n"
        ".word 0xea000015\n"
        ".word 0xed8d0a03\n"
        ".word 0xe5940010\n"
        ".word 0xe3a06002\n"
        ".word 0xe35005fe\n"
        ".word 0xe58d0020\n"
        ".word 0xcd8d9a08\n"
        ".word 0xcd849a04\n"
        ".word 0xeaffffcd\n"
        ".word 0xed8d0a03\n"
        ".word 0xe5940010\n"
        ".word 0xe3a06003\n"
        ".word 0xe58d0020\n"
        ".word 0xedcd0a04\n"
        ".word 0xe5941018\n"
        ".word 0xe35005fe\n"
        ".word 0xe58d1024\n"
        ".word 0xcd8d9a08\n"
        ".word 0xcd849a04\n"
        ".word 0xe35105fe\n"
        ".word 0xcd8d9a09\n"
        ".word 0xcd849a06\n"
        ".word 0xeaffffbf\n"
        ".word 0xe59f01a0\n"
        ".word 0xeb0027e6\n"
        ".word 0xe597004c\n"
        ".word 0xe3500001\n"
        ".word 0x059f0194\n"
        ".word 0x0b0027e2\n"
        ".word 0xe597004c\n"
        ".word 0xe59f818c\n"
        ".word 0xe3a0a001\n"
        ".word 0xe3500000\n"
        ".word 0x1a000173\n"
        ".word 0xe5970058\n"
        ".word 0xe59fb184\n"
        ".word 0xeddf8a5e\n"
        ".word 0xed9faa5e\n"
        ".word 0xe3500000\n"
        ".word 0x0a000004\n"
        ".word 0xe3500001\n"
        ".word 0x0a00009b\n"
        ".word 0xe3500002\n"
        ".word 0x1a000169\n"
        ".word 0xea00013a\n"
        ".word 0xe3550000\n"
        ".word 0x0a000046\n"
        ".word 0xe1550006\n"
        ".word 0x0a000044\n"
        ".word 0xe3a00003\n"
        ".word 0xeb01d3ee\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000007\n"
        ".word 0xe3a00003\n"
        ".word 0xeb0027c3\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb01d3e6\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000005\n"
        ".word 0xe3a00007\n"
        ".word 0xeb01f5cb\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a00000b\n"
        ".word 0xea000005\n"
        ".word 0xe3a00004\n"
        ".word 0xeb01d3db\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a00001e\n"
        ".word 0xea000015\n"
        ".word 0xe3a00018\n"
        ".word 0xeb01f5bf\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000002\n"
        ".word 0xed970a21\n"
        ".word 0xee080a28\n"
        ".word 0xea000021\n"
        ".word 0xe3a00008\n"
        ".word 0xeb01f5b7\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000005\n"
        ".word 0xe3a0001c\n"
        ".word 0xeb01f5b2\n"
        ".word 0xe3500000\n"
        ".word 0x0d970a21\n"
        ".word 0x0e300a08\n"
        ".word 0x0a000016\n"
        ".word 0xed970a21\n"
        ".word 0xee080a0a\n"
        ".word 0xea000013\n"
        ".word 0xe3a00004\n"
        ".word 0xeb002799\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb01d3bc\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a00000d\n"
        ".word 0xe3a00007\n"
        ".word 0xeb01f5a1\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000004\n"
        ".word 0xe3a00018\n"
        ".word 0xeb01f59c\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000014\n"
        ".word 0xed970a21\n"
        ".word 0xee080a68\n"
        ".word 0xed870a21\n"
        ".word 0xe58db030\n"
        ".word 0xe3a00005\n"
        ".word 0xeb01d3a9\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000021\n"
        ".word 0xea000018\n"
        ".word 0x00000000\n"
        ".word 0x3f800000\n"
        ".word 0x00400001\n"
        ".word 0x0044ea80\n"
        ".word 0x004d8f40\n"
        ".word 0x0044fca8\n"
        ".word 0x0044f970\n"
        ".word 0x004d92b4\n"
        ".word 0x41200000\n"
        ".word 0x42c80000\n"
        ".word 0x00400003\n"
        ".word 0xe3a00008\n"
        ".word 0xeb01f582\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000005\n"
        ".word 0xe3a0001c\n"
        ".word 0xeb01f57d\n"
        ".word 0xe3500000\n"
        ".word 0x0d970a21\n"
        ".word 0x0e300a48\n"
        ".word 0x0affffe1\n"
        ".word 0xed970a21\n"
        ".word 0xee080a4a\n"
        ".word 0xeaffffde\n"
        ".word 0xe3a00005\n"
        ".word 0xeb002764\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb01d387\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000005\n"
        ".word 0xe5970050\n"
        ".word 0xe3500000\n"
        ".word 0xc2400001\n"
        ".word 0xda0000f4\n"
        ".word 0xe5870050\n"
        ".word 0xea0000f2\n"
        ".word 0xe3a00006\n"
        ".word 0xeb01d37c\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000007\n"
        ".word 0xe3a00006\n"
        ".word 0xeb002751\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb01d374\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000006\n"
        ".word 0xe5970050\n"
        ".word 0xe1500006\n"
        ".word 0x25970058\n"
        ".word 0xe2800001\n"
        ".word 0x3affffeb\n"
        ".word 0xe5870058\n"
        ".word 0xea0000de\n"
        ".word 0xe3a00000\n"
        ".word 0xeb01ef4c\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000007\n"
        ".word 0xe3a00000\n"
        ".word 0xeb00273d\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb01ef44\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a0000d1\n"
        ".word 0xe587a04c\n"
        ".word 0xea0000cf\n"
        ".word 0xe3a00003\n"
        ".word 0xeb01d359\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000007\n"
        ".word 0xe3a00003\n"
        ".word 0xeb00272e\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb01d351\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000005\n"
        ".word 0xe3a00007\n"
        ".word 0xeb01f536\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a00000b\n"
        ".word 0xea000005\n"
        ".word 0xe3a00004\n"
        ".word 0xeb01d346\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a00002f\n"
        ".word 0xea000026\n"
        ".word 0xe3a00018\n"
        ".word 0xeb01f52a\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000007\n"
        ".word 0xe5970054\n"
        ".word 0xe3500001\n"
        ".word 0x0d980a02\n"
        ".word 0x1d980a03\n"
        ".word 0xee080a28\n"
        ".word 0x0a000011\n"
        ".word 0xed880a03\n"
        ".word 0xea000010\n"
        ".word 0xe3a00008\n"
        ".word 0xeb01f51d\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000004\n"
        ".word 0xe3a0001c\n"
        ".word 0xeb01f518\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000008\n"
        ".word 0xe5970054\n"
        ".word 0xe3500001\n"
        ".word 0x0d980a02\n"
        ".word 0x1d980a03\n"
        ".word 0xee080a0a\n"
        ".word 0x1affffed\n"
        ".word 0xed880a02\n"
        ".word 0xe58db030\n"
        ".word 0xea000096\n"
        ".word 0xe5970054\n"
        ".word 0xe3500001\n"
        ".word 0x1d980a03\n"
        ".word 0x0d980a02\n"
        ".word 0xee300a08\n"
        ".word 0x1affffe4\n"
        ".word 0xeafffff5\n"
        ".word 0xe3a00004\n"
        ".word 0xeb0026f3\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb01d316\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000005\n"
        ".word 0xe3a00007\n"
        ".word 0xeb01f4fb\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a00000b\n"
        ".word 0xea000005\n"
        ".word 0xe3a00005\n"
        ".word 0xeb01d30b\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a00002c\n"
        ".word 0xea000023\n"
        ".word 0xe3a00018\n"
        ".word 0xeb01f4ef\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000006\n"
        ".word 0xe5970054\n"
        ".word 0xe3500001\n"
        ".word 0x0d980a02\n"
        ".word 0x1d980a03\n"
        ".word 0xee080a68\n"
        ".word 0x0affffd6\n"
        ".word 0xeaffffc3\n"
        ".word 0xe3a00008\n"
        ".word 0xeb01f4e3\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000004\n"
        ".word 0xe3a0001c\n"
        ".word 0xeb01f4de\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000006\n"
        ".word 0xe5970054\n"
        ".word 0xe3500001\n"
        ".word 0x0d980a02\n"
        ".word 0x1d980a03\n"
        ".word 0xee080a4a\n"
        ".word 0x1affffb3\n"
        ".word 0xeaffffc4\n"
        ".word 0xe5970054\n"
        ".word 0xe3500001\n"
        ".word 0x1d980a03\n"
        ".word 0x0d980a02\n"
        ".word 0xee300a48\n"
        ".word 0x1affffac\n"
        ".word 0xeaffffbd\n"
        ".word 0xe3a00005\n"
        ".word 0xeb0026bb\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb01d2de\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000006\n"
        ".word 0xe5970054\n"
        ".word 0xe3500002\n"
        ".word 0x15970058\n"
        ".word 0x0587a054\n"
        ".word 0x12400001\n"
        ".word 0x0a000049\n"
        ".word 0xeaffff67\n"
        ".word 0xe3a00006\n"
        ".word 0xeb01d2d2\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000007\n"
        ".word 0xe3a00006\n"
        ".word 0xeb0026a7\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb01d2ca\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a00003b\n"
        ".word 0xe5970054\n"
        ".word 0xe3500001\n"
        ".word 0x03a00002\n"
        ".word 0x05870054\n"
        ".word 0x0a000036\n"
        ".word 0xe5971058\n"
        ".word 0xe51f0384\n"
        ".word 0xe2811001\n"
        ".word 0xe5871058\n"
        ".word 0xe580a00c\n"
        ".word 0xe5901010\n"
        ".word 0xe3c11010\n"
        ".word 0xe5801010\n"
        ".word 0xea00002d\n"
        ".word 0xe3a00005\n"
        ".word 0xeb01d2b7\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000007\n"
        ".word 0xe3a00005\n"
        ".word 0xeb00268c\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb01d2af\n"
        ".word 0xe3500000\n"
        ".word 0x03a0b000\n"
        ".word 0x0a000009\n"
        ".word 0xe51f13d8\n"
        ".word 0xe5910010\n"
        ".word 0xe3100020\n"
        ".word 0x0a00001c\n"
        ".word 0xe5972058\n"
        ".word 0xe3800010\n"
        ".word 0xe2422001\n"
        ".word 0xe5872058\n"
        ".word 0xe5810010\n"
        ".word 0xea000016\n"
        ".word 0xe3a00006\n"
        ".word 0xeb01d2a0\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000007\n"
        ".word 0xe3a00006\n"
        ".word 0xeb002675\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb01d298\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000009\n"
        ".word 0xe51f1434\n"
        ".word 0xe5910010\n"
        ".word 0xe3100020\n"
        ".word 0x0a000005\n"
        ".word 0xe587b058\n"
        ".word 0xe587a054\n"
        ".word 0xe3800010\n"
        ".word 0xe587b050\n"
        ".word 0xe5810010\n"
        ".word 0xea000004\n"
        ".word 0xe5970050\n"
        ".word 0xe3500000\n"
        ".word 0xb3a00000\n"
        ".word 0xb5870050\n"
        ".word 0xba000002\n"
        ".word 0xe5970050\n"
        ".word 0xe1500006\n"
        ".word 0x85876050\n"
        ".word 0xed970a21\n"
        ".word 0xee100a10\n"
        ".word 0xeeb40ae9\n"
        ".word 0xeef1fa10\n"
        ".word 0x3dc79a21\n"
        ".word 0x3a000001\n"
        ".word 0xe35005fe\n"
        ".word 0xcd879a21\n"
        ".word 0xed980a02\n"
        ".word 0xee100a10\n"
        ".word 0xeeb40ae9\n"
        ".word 0xeef1fa10\n"
        ".word 0x3dc89a02\n"
        ".word 0x3a000003\n"
        ".word 0xe35005fe\n"
        ".word 0xceb00a49\n"
        ".word 0xde000a10\n"
        ".word 0xed880a02\n"
        ".word 0xed980a03\n"
        ".word 0xee100a10\n"
        ".word 0xeeb40ae9\n"
        ".word 0xeef1fa10\n"
        ".word 0x3dc89a03\n"
        ".word 0x3a000003\n"
        ".word 0xe35005fe\n"
        ".word 0xceb00a49\n"
        ".word 0xde000a10\n"
        ".word 0xed880a03\n"
        ".word 0xedd80a02\n"
        ".word 0xed980a03\n"
        ".word 0xeef40ac0\n"
        ".word 0xeef1fa10\n"
        ".word 0xda000010\n"
        ".word 0xe51f3500\n"
        ".word 0xe3a01008\n"
        ".word 0xe59f23f0\n"
        ".word 0xe593000c\n"
        ".word 0xe5933014\n"
        ".word 0xe0800080\n"
        ".word 0xe0810180\n"
        ".word 0xe7930000\n"
        ".word 0xe1500002\n"
        ".word 0x0a000012\n"
        ".word 0xe5970058\n"
        ".word 0xe3500001\n"
        ".word 0x1a000002\n"
        ".word 0xe5970054\n"
        ".word 0xe3500001\n"
        ".word 0x0a00000c\n"
        ".word 0xed880a02\n"
        ".word 0xe59f03b8\n"
        ".word 0xe2462001\n"
        ".word 0xe5d01000\n"
        ".word 0xe1510002\n"
        ".word 0x0a00000c\n"
        ".word 0xe3510001\n"
        ".word 0xed9f0ae9\n"
        ".word 0x0d800a04\n"
        ".word 0x0a000008\n"
        ".word 0xe3510002\n"
        ".word 0x0a000002\n"
        ".word 0xea000005\n"
        ".word 0xedc80a03\n"
        ".word 0xeafffff1\n"
        ".word 0xedd00a04\n"
        ".word 0xee700a89\n"
        ".word 0xee200a80\n"
        ".word 0xed800a06\n"
        ".word 0xe51f0590\n"
        ".word 0xe59d1054\n"
        ".word 0xe3550000\n"
        ".word 0xe2802fdd\n"
        ".word 0xe892180c\n"
        ".word 0xe881180c\n"
        ".word 0xe2801e35\n"
        ".word 0xec910a08\n"
        ".word 0xec840a08\n"
        ".word 0xe5900370\n"
        ".word 0xe5840020\n"
        ".word 0x0597005c\n"
        ".word 0x05840004\n"
        ".word 0x0a000017\n"
        ".word 0xe1550006\n"
        ".word 0x0597005c\n"
        ".word 0x05840008\n"
        ".word 0x0a000013\n"
        ".word 0xe597105c\n"
        ".word 0xe0840185\n"
        ".word 0xe3560002\n"
        ".word 0xe5801004\n"
        ".word 0xed970a21\n"
        ".word 0xed800a02\n"
        ".word 0x9a00000c\n"
        ".word 0xe3550001\n"
        ".word 0x9a000005\n"
        ".word 0xedd00a00\n"
        ".word 0xeef40ac0\n"
        ".word 0xeef1fa10\n"
        ".word 0xcd800a00\n"
        ".word 0xcd090a01\n"
        ".word 0xea000004\n"
        ".word 0xedd00a04\n"
        ".word 0xeeb40ae0\n"
        ".word 0xeef1fa10\n"
        ".word 0xcd800a04\n"
        ".word 0xcd890a01\n"
        ".word 0xed9d0a16\n"
        ".word 0xe51f4630\n"
        ".word 0xe28d0008\n"
        ".word 0xeef80ac0\n"
        ".word 0xeef81ac0\n"
        ".word 0xe594105c\n"
        ".word 0xeeb81ac0\n"
        ".word 0xe3a030b0\n"
        ".word 0xe7801105\n"
        ".word 0xed940a21\n"
        ".word 0xe3a020c8\n"
        ".word 0xed890a00\n"
        ".word 0xe3a01008\n"
        ".word 0xee600a20\n"
        ".word 0xe3a000a0\n"
        ".word 0xeebd0ae0\n"
        ".word 0xed840a22\n"
        ".word 0xed980a02\n"
        ".word 0xee200a21\n"
        ".word 0xeebd0ac0\n"
        ".word 0xed840a23\n"
        ".word 0xed980a03\n"
        ".word 0xee200a01\n"
        ".word 0xeebd0ac0\n"
        ".word 0xed840a24\n"
        ".word 0xeb00f870\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe1a00000\n"
        ".word 0xe51f0698\n"
        ".word 0xe320f000\n"
        ".word 0xeb0025c5\n"
        ".word 0xe594004c\n"
        ".word 0xe3500001\n"
        ".word 0x02840eef\n"
        ".word 0x0b0025c1\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe1a00000\n"
        ".word 0xe59f0244\n"
        ".word 0xe3a014ff\n"
        ".word 0xe3a03010\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe3a020b8\n"
        ".word 0xe1a01003\n"
        ".word 0xe3a000a8\n"
        ".word 0xeb00f830\n"
        ".word 0xeddf8a8a\n"
        ".word 0xe3560000\n"
        ".word 0xe3a0b010\n"
        ".word 0xe3a04000\n"
        ".word 0x9a000042\n"
        ".word 0xe28d001c\n"
        ".word 0xe0800104\n"
        ".word 0xe28d1008\n"
        ".word 0xec900a02\n"
        ".word 0xe0812104\n"
        ".word 0xe7910104\n"
        ".word 0xe5921004\n"
        ".word 0xee200a28\n"
        ".word 0xee600aa8\n"
        ".word 0xe38194ff\n"
        ".word 0xe38084ff\n"
        ".word 0xeebd0ac0\n"
        ".word 0xeefd0ae0\n"
        ".word 0xee101a10\n"
        ".word 0xee100a90\n"
        ".word 0xe28150a8\n"
        ".word 0xe28000a8\n"
        ".word 0xe0407005\n"
        ".word 0xe59f11d0\n"
        ".word 0xe28f0e1d\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a03068\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58da004\n"
        ".word 0xe58db000\n"
        ".word 0xeb01fae7\n"
        ".word 0xe2801008\n"
        ".word 0xe3a03004\n"
        ".word 0xe8810820\n"
        ".word 0xe2802010\n"
        ".word 0xe5803004\n"
        ".word 0xe8820880\n"
        ".word 0xe3a01003\n"
        ".word 0xe1c081f8\n"
        ".word 0xeb004ab0\n"
        ".word 0xe51f0790\n"
        ".word 0xe5901050\n"
        ".word 0xe1540001\n"
        ".word 0x05900058\n"
        ".word 0x03500000\n"
        ".word 0x0a0000c5\n"
        ".word 0xe59f1190\n"
        ".word 0xe3e07000\n"
        ".word 0xe28f0f5a\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a03068\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58da004\n"
        ".word 0xe58db000\n"
        ".word 0xeb01facd\n"
        ".word 0xe3a03006\n"
        ".word 0xe280800c\n"
        ".word 0xe9800028\n"
        ".word 0xe3a0100c\n"
        ".word 0xe8880022\n"
        ".word 0xe2808014\n"
        ".word 0xe3a02024\n"
        ".word 0xe3a01003\n"
        ".word 0xe8880084\n"
        ".word 0xeb004a95\n"
        ".word 0xe2844001\n"
        ".word 0xe1540006\n"
        ".word 0x3affffbc\n"
        ".word 0xe51f0808\n"
        ".word 0xe5900050\n"
        ".word 0xe1560000\n"
        ".word 0x1a000003\n"
        ".word 0xe51f0818\n"
        ".word 0xe5900058\n"
        ".word 0xe3500000\n"
        ".word 0x0a0000cf\n"
        ".word 0xe3a04e16\n"
        ".word 0xe59f110c\n"
        ".word 0xe59f010c\n"
        ".word 0xe3a0500c\n"
        ".word 0xe1a06004\n"
        ".word 0xe3a07024\n"
        ".word 0xe3e08000\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a03068\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58da004\n"
        ".word 0xe58db000\n"
        ".word 0xeb01faa9\n"
        ".word 0xe2802004\n"
        ".word 0xe3a01006\n"
        ".word 0xe88201f2\n"
        ".word 0xe3a01003\n"
        ".word 0xeb004a76\n"
        ".word 0xe3a00000\n"
        ".word 0xe58d0008\n"
        ".word 0xedcd9a07\n"
        ".word 0xe59d1054\n"
        ".word 0xe59d3054\n"
        ".word 0xe59f2080\n"
        ".word 0xe3a054ff\n"
        ".word 0xe5911000\n"
        ".word 0xe58d100c\n"
        ".word 0xe5933008\n"
        ".word 0xe58d1010\n"
        ".word 0xe59d1054\n"
        ".word 0xe58d3020\n"
        ".word 0xe3a03010\n"
        ".word 0xe591100c\n"
        ".word 0xe58d0014\n"
        ".word 0xe3a000a8\n"
        ".word 0xe58d1024\n"
        ".word 0xed8d9a0a\n"
        ".word 0xe88d0024\n"
        ".word 0xe3a020b8\n"
        ".word 0xe3a0102c\n"
        ".word 0xeb00f7b5\n"
        ".word 0xe3a04000\n"
        ".word 0xe3a0902c\n"
        ".word 0xe28d201c\n"
        ".word 0xe0822104\n"
        ".word 0xe28d0008\n"
        ".word 0xec920a02\n"
        ".word 0xe3a014ff\n"
        ".word 0xe7903104\n"
        ".word 0xe080c104\n"
        ".word 0xee200a28\n"
        ".word 0xee600aa8\n"
        ".word 0xe1832803\n"
        ".word 0xea00000f\n"
        ".word 0x004d92bc\n"
        ".word 0x004d9290\n"
        ".word 0x3f000000\n"
        ".word 0x80808080\n"
        ".word 0x43380000\n"
        ".word 0x0000026d\n"
        ".word 0x532f2e2e\n"
        ".word 0x6372756f\n"
        ".word 0x66472f65\n"
        ".word 0x66452f78\n"
        ".word 0x74636566\n"
        ".word 0x6666652f\n"
        ".word 0x756e654d\n"
        ".word 0x0000682e\n"
        ".word 0x00000295\n"
        ".word 0x004093d8\n"
        ".word 0xeebd0ac0\n"
        ".word 0xeefd0ae0\n"
        ".word 0xe59c0004\n"
        ".word 0xe181c403\n"
        ".word 0xe182700c\n"
        ".word 0xe1803800\n"
        ".word 0xe1810400\n"
        ".word 0xe1838000\n"
        ".word 0xee100a10\n"
        ".word 0xee101a90\n"
        ".word 0xe28050a8\n"
        ".word 0xe28100a8\n"
        ".word 0xe0406005\n"
        ".word 0xe51f1068\n"
        ".word 0xe24f0068\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a03068\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58da004\n"
        ".word 0xe58db000\n"
        ".word 0xeb01fa59\n"
        ".word 0xe2802004\n"
        ".word 0xe3a01004\n"
        ".word 0xe8820222\n"
        ".word 0xe2802010\n"
        ".word 0xe3a01003\n"
        ".word 0xe8820840\n"
        ".word 0xe2802018\n"
        ".word 0xe8820180\n"
        ".word 0xeb004a22\n"
        ".word 0xe51f09c8\n"
        ".word 0xe5901054\n"
        ".word 0xe1540001\n"
        ".word 0x05900058\n"
        ".word 0x03500001\n"
        ".word 0x0a00008b\n"
        ".word 0xe51f10a8\n"
        ".word 0xe3e06000\n"
        ".word 0xe24f00d0\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a03068\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58da004\n"
        ".word 0xe58db000\n"
        ".word 0xeb01fa3f\n"
        ".word 0xe3a03006\n"
        ".word 0xe280700c\n"
        ".word 0xe9800028\n"
        ".word 0xe3a01028\n"
        ".word 0xe8870022\n"
        ".word 0xe2807014\n"
        ".word 0xe3a02040\n"
        ".word 0xe3a01003\n"
        ".word 0xe8870044\n"
        ".word 0xeb004a07\n"
        ".word 0xe2844001\n"
        ".word 0xe3540003\n"
        ".word 0x3affffa6\n"
        ".word 0xe3a04e16\n"
        ".word 0xe51f110c\n"
        ".word 0xe51f010c\n"
        ".word 0xe3a05028\n"
        ".word 0xe1a06004\n"
        ".word 0xe3a07040\n"
        ".word 0xe3e08000\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a03068\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58da004\n"
        ".word 0xe58db000\n"
        ".word 0xeb01fa23\n"
        ".word 0xe2802004\n"
        ".word 0xe3a01006\n"
        ".word 0xe88201f2\n"
        ".word 0xe3a01003\n"
        ".word 0xeb0049f0\n"
        ".word 0xe59d0058\n"
        ".word 0xe28f3d0b\n"
        ".word 0xe3a02008\n"
        ".word 0xe58d0000\n"
        ".word 0xe3a01044\n"
        ".word 0xe3a000a4\n"
        ".word 0xeb0024b3\n"
        ".word 0xe1a0000a\n"
        ".word 0xeb01ecdb\n"
        ".word 0xe3500000\n"
        ".word 0x1a000088\n"
        ".word 0xea00007f\n"
        ".word 0xe2457001\n"
        ".word 0xe51f118c\n"
        ".word 0xe1a08007\n"
        ".word 0xe24f0f6d\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a03068\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58da004\n"
        ".word 0xe58db000\n"
        ".word 0xeb01fa06\n"
        ".word 0xe59f126c\n"
        ".word 0xe280200c\n"
        ".word 0xe3a09024\n"
        ".word 0xe5801018\n"
        ".word 0xe5807008\n"
        ".word 0xe3a07006\n"
        ".word 0xe3a0100c\n"
        ".word 0xe5807004\n"
        ".word 0xe8820302\n"
        ".word 0xe3a01003\n"
        ".word 0xeb0049cd\n"
        ".word 0xe51f11e4\n"
        ".word 0xe24f0f82\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a03068\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58da004\n"
        ".word 0xe58db000\n"
        ".word 0xeb01f9f1\n"
        ".word 0xe59f2218\n"
        ".word 0xe280300c\n"
        ".word 0xe3a0100c\n"
        ".word 0xe5802018\n"
        ".word 0xe5805008\n"
        ".word 0xe5807004\n"
        ".word 0xe8830222\n"
        ".word 0xe3a01003\n"
        ".word 0xeaffff23\n"
        ".word 0xe59f61f8\n"
        ".word 0xe59f91f0\n"
        ".word 0xe51f0234\n"
        ".word 0xe3a0400c\n"
        ".word 0xe3a05024\n"
        ".word 0xe2861f4d\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a03068\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58da004\n"
        ".word 0xe58db000\n"
        ".word 0xeb01f9da\n"
        ".word 0xe3a08006\n"
        ".word 0xe280200c\n"
        ".word 0xe5806008\n"
        ".word 0xe5808004\n"
        ".word 0xe8820050\n"
        ".word 0xe2802014\n"
        ".word 0xe3a01003\n"
        ".word 0xe8820220\n"
        ".word 0xeb0049a3\n"
        ".word 0xe3a04e16\n"
        ".word 0xe51f1290\n"
        ".word 0xe51f0290\n"
        ".word 0xe3a0500c\n"
        ".word 0xe1a06004\n"
        ".word 0xe3a07024\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a03068\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58da004\n"
        ".word 0xe58db000\n"
        ".word 0xeb01f9c3\n"
        ".word 0xe2802008\n"
        ".word 0xe5808004\n"
        ".word 0xe3a01003\n"
        ".word 0xe88202f0\n"
        ".word 0xeaffff18\n"
        ".word 0xe2456001\n"
        ".word 0xe51f12dc\n"
        ".word 0xe1a07006\n"
        ".word 0xe24f0fc1\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a03068\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58da004\n"
        ".word 0xe58db000\n"
        ".word 0xeb01f9b2\n"
        ".word 0xe59f111c\n"
        ".word 0xe5806008\n"
        ".word 0xe3a06006\n"
        ".word 0xe5801018\n"
        ".word 0xe3a01040\n"
        ".word 0xe5801014\n"
        ".word 0xe5806004\n"
        ".word 0xe3a08028\n"
        ".word 0xe5807010\n"
        ".word 0xe3a01003\n"
        ".word 0xe580800c\n"
        ".word 0xeb004978\n"
        ".word 0xe51f1338\n"
        ".word 0xe24f0fd7\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a03068\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58da004\n"
        ".word 0xe58db000\n"
        ".word 0xeb01f99c\n"
        ".word 0xe59f10c4\n"
        ".word 0xe5805008\n"
        ".word 0xe3a02040\n"
        ".word 0xe5801018\n"
        ".word 0xe5802014\n"
        ".word 0xe5805010\n"
        ".word 0xe5806004\n"
        ".word 0xe3a01003\n"
        ".word 0xe580800c\n"
        ".word 0xeaffff5b\n"
        ".word 0xe3a00001\n"
        ".word 0xeb00244c\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb01ec53\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a00000a\n"
        ".word 0xe51f0ce0\n"
        ".word 0xe590104c\n"
        ".word 0xe3510000\n"
        ".word 0x13a01000\n"
        ".word 0x1580104c\n"
        ".word 0x0a000014\n"
        ".word 0xe51f0cf0\n"
        ".word 0xe5900010\n"
        ".word 0xe3100008\n"
        ".word 0x0a00000b\n"
        ".word 0xea000007\n"
        ".word 0xe51f0d0c\n"
        ".word 0xe590004c\n"
        ".word 0xe3500000\n"
        ".word 0x0afffff6\n"
        ".word 0xe51f0d10\n"
        ".word 0xe5900010\n"
        ".word 0xe3100008\n"
        ".word 0x0a000002\n"
        ".word 0xe59d0030\n"
        ".word 0xe3800002\n"
        ".word 0xe58d0030\n"
        ".word 0xe59d0030\n"
        ".word 0xe28dd038\n"
        ".word 0xecbd8b06\n"
        ".word 0xe28dd00c\n"
        ".word 0xe8bd8ff0\n"
        ".word 0xe59d0030\n"
        ".word 0xe3c00001\n"
        ".word 0xe58d0030\n"
        ".word 0xeaffffe6\n"
        ".word 0x35312530\n"
        ".word 0x00000064\n"
        ".word 0xff00ff00\n"
        ".word 0x00000161\n"
    );
}
#if 0
// Original partial readable draft retained for reconstruction; not compiled.
s32 ui_func_00243e8c(EffMenuItemState* item, EffMenuSlot* slot, s32 count) {
    u32 result_flags = 0x00400001u;                       // [sp+0x30]
    f32 step;                                             // s16
    if (count > 0) {
        step = 1.0f / static_cast<f32>(count);            // 0x00243EBC
    } else {
        step = 0.0f;                                      // 0x00243EAC
    }

    f32 field_04 = item->field_04;                        // s2 / [sp+8]
    f32 field_0c = item->field_0c;                        // s0 / [sp+0xC]
    f32 field_14 = item->field_14;                        // s1 / [sp+0x10]
    // [sp+8] is the colour/position stack and [sp+0x1C] the value stack.
    // 0x00243EC8/D0: colour[0] = field_04; 0x00243ED4: value[0] = 0.
    u32 colors[8] = {};                                   // [sp+8]
    colors[0] = *reinterpret_cast<const u32*>(&field_04);
    f32 values[8] = {};                                   // [sp+0x1C]
    values[0] = 0.0f;

    s32 span = 1;                                         // r6
    switch (item->state) {                                // 0x00243ED8
    case 1:
        // 0x00243FA8..0x00243FC4: [sp+0xC] = field_0C, [sp+0x20] = field_10
        // (value[1]), then the >1.0 clamp.
        colors[1] = *reinterpret_cast<const u32*>(&field_0c);
        values[1] = item->field_10;
        span = 2;
        if (item->field_10 > 1.0f) {
            values[1] = 1.0f;
            item->field_10 = 1.0f;
        }
        break;
    case 2:
        // 0x00243FC8..0x00243FFC: [sp+0xC]=field_0C, [sp+0x10]=field_14,
        // [sp+0x20]=field_10 (value[1]), [sp+0x24]=field_18 (value[2]).
        colors[1] = *reinterpret_cast<const u32*>(&field_0c);
        colors[2] = *reinterpret_cast<const u32*>(&field_14);
        values[1] = item->field_10;
        values[2] = item->field_18;
        span = 3;
        if (item->field_10 > 1.0f) {
            values[1] = 1.0f;
            item->field_10 = 1.0f;
        }
        if (item->field_18 > 1.0f) {
            values[2] = 1.0f;
            item->field_18 = 1.0f;
        }
        break;
    default:
        item->state = 0;                                  // 0x00243EF4
        break;
    }

    // Common prologue (0x00243F00..0x00243F98).
    const u32 field_08 = item->field_08;
    colors[span] = field_08;
    values[span] = 1.0f;
    if (EffMenuState().column_50 > span) {
        EffMenuState().column_50 = span;
    }
    const s32 column = EffMenuState().column_50;           // r5
    EffMenuState().color_5c = colors[column] | 0xFF000000u;
    const f32 current = values[column];                   // [sb]
    EffMenuState().value_84 = current;                     // 0x00243F48

    // Copy the row state into the scene buffer (0x00243F4C..0x00243F80).
    g_EffMenuScene.state_350[0] = *reinterpret_cast<f32*>(&item->state);
    g_EffMenuScene.state_350[1] = field_04;
    g_EffMenuScene.state_350[2] = *reinterpret_cast<const f32*>(&field_08);
    g_EffMenuScene.state_350[3] = field_0c;
    g_EffMenuScene.state_350[4] = item->field_10;
    g_EffMenuScene.state_350[5] = field_14;
    g_EffMenuScene.state_350[6] = item->field_18;
    g_EffMenuScene.state_350[7] = item->field_1c;
    g_EffMenuScene.field_370 = item->field_20;
    g_EffMenuScene.slot_374[0] = slot->word[0];
    g_EffMenuScene.slot_374[1] = slot->word[1];
    g_EffMenuScene.slot_374[2] = slot->word[2];
    g_EffMenuScene.slot_374[3] = slot->word[3];

    // 0x00243F98..0x00244014
    if (EffMenuState().field_09 == 0) {
        AsdUiObject_CreateAndReset(&g_EffMenuObjectA);
        if (EffMenuState().mode_4c == 1) {
            AsdUiObject_CreateAndReset(&g_EffMenuObjectB);
        }
    }

    const bool mode_zero = EffMenuState().mode_4c == 0;     // 0x00244024

    if (mode_zero) {
        const s32 page = EffMenuState().page_58;           // 0x0024402C
        if (page == 0) {
            // ---- page 0: three columns, value bar -------------------------
            if (column != 0 && column != span) {          // 0x00244058
                if (UiInput_Trigger(3)) {                   // 0x0024406C
                    goto page0_right;                        // 0x00244078 -> 0x0024409C
                }
                {
                    const u8 prev = UiInput_Reset(3);     // 0x00244080
                    if (UiInput_Trigger(prev)) {
                        goto page0_right;
                    }
                }
                if (UiInput_Trigger(4)) {                   // 0x002440B4
                    goto page0_left;
                }
                {
                    const u8 prev = UiInput_Reset(4);     // 0x00244124
                    if (UiInput_Trigger(prev)) {
                        goto page0_left;
                    }
                    goto page0_updown;
                }
            page0_left:
                if (UiInput_Trigger3(7)) {
                    EffMenuState().value_84 -= step * 20.0f;
                    result_flags = 0x00400003u;
                    goto page_done;
                }
                if (UiInput_Trigger3(0x18)) {
                    EffMenuState().value_84 -= step * 20.0f;
                    result_flags = 0x00400003u;
                    goto page_done;
                }
                if (UiInput_Trigger3(8)) {
                    EffMenuState().value_84 -= step * 100.0f;
                    result_flags = 0x00400003u;
                    goto page_done;
                }
                if (UiInput_Trigger3(0x1C)) {
                    EffMenuState().value_84 -= step * 100.0f;
                    result_flags = 0x00400003u;
                    goto page_done;
                }
                EffMenuState().value_84 -= step;
                result_flags = 0x00400003u;
                goto page_done;
            page0_right:
                if (UiInput_Trigger3(7)) {
                    EffMenuState().value_84 += step * 20.0f;
                    result_flags = 0x00400003u;
                    goto page_done;
                }
                if (UiInput_Trigger3(0x18)) {
                    EffMenuState().value_84 += step * 20.0f;
                    result_flags = 0x00400003u;
                    goto page_done;
                }
                if (UiInput_Trigger3(8)) {                  // 0x002440EC
                    EffMenuState().value_84 += step * 100.0f;
                    result_flags = 0x00400003u;
                    goto page_done;
                }
                if (UiInput_Trigger3(0x1C)) {                // 0x00244100
                    EffMenuState().value_84 += step * 100.0f;
                    result_flags = 0x00400003u;
                    goto page_done;
                }
                EffMenuState().value_84 += step;
                result_flags = 0x00400003u;
                goto page_done;
            }

        page0_updown:
            if (UiInput_Trigger(5)) {                       // 0x0024417C
                if (EffMenuState().column_50 > 0) {
                    --EffMenuState().column_50;            // 0x00244220
                }
                goto page_done;
            }
            {
                const u8 prev = UiInput_Reset(5);         // 0x002441FC
                if (UiInput_Trigger(prev)) {
                    if (EffMenuState().column_50 > 0) {
                        --EffMenuState().column_50;
                    }
                    goto page_done;
                }
            }
            if (UiInput_Trigger(6)) {                       // 0x00244234
                if (EffMenuState().column_50 >= span) {
                    ++EffMenuState().page_58;              // 0x00244274
                }
                goto page_done;
            }
            {
                const u8 prev = UiInput_Reset(6);         // 0x00244248
                if (!UiInput_Trigger(prev)) {
                    goto page_done;
                }
            }
            if (UiInput_Trigger2(0)) {                  // 0x00244284
                EffMenuState().mode_4c = 1;                // 0x002442B4
                goto page_done;
            }
            {
                const u8 prev = UiInput_Reset(0);         // 0x00244298
                if (UiInput_Trigger2(prev)) {
                    EffMenuState().mode_4c = 1;
                }
            }
        } else if (page == 1) {
            // ---- page 1: two sub-columns, 0..1000 value -------------------
            if (UiInput_Trigger(3)) {                       // 0x002442C0
                goto page1_right;
            }
            {
                const u8 prev = UiInput_Reset(3);         // 0x002442D4
                if (UiInput_Trigger(prev)) {
                    goto page1_right;
                }
            }
            if (UiInput_Trigger(4)) {                       // 0x0024430C
                goto page1_left;
            }
            {
                const u8 prev = UiInput_Reset(4);         // 0x002443C0
                if (UiInput_Trigger(prev)) {
                    goto page1_left;
                }
                goto page1_updown;
            }
        page1_left:
            if (UiInput_Trigger3(7)) {
                if (EffMenuState().field_54 == 1) {
                    EffMenuAnimConfig& a = g_EffMenuAnimConfig;
                    a.field_08 += step * 20.0f;
                } else {
                    g_EffMenuAnimConfig.field_0c += step * 20.0f;
                }
                result_flags = 0x00400003u;
                goto page_done;
            }
            if (UiInput_Trigger3(0x18)) {
                if (EffMenuState().field_54 == 1) {
                    g_EffMenuAnimConfig.field_08 += step * 20.0f;
                } else {
                    g_EffMenuAnimConfig.field_0c += step * 20.0f;
                }
                result_flags = 0x00400003u;
                goto page_done;
            }
            if (UiInput_Trigger3(8)) {
                if (EffMenuState().field_54 == 1) {
                    g_EffMenuAnimConfig.field_08 += step * 100.0f;
                } else {
                    g_EffMenuAnimConfig.field_0c += step * 100.0f;
                }
                result_flags = 0x00400003u;
                goto page_done;
            }
            if (UiInput_Trigger3(0x1C)) {
                if (EffMenuState().field_54 == 1) {
                    g_EffMenuAnimConfig.field_08 += step * 100.0f;
                } else {
                    g_EffMenuAnimConfig.field_0c += step * 100.0f;
                }
                result_flags = 0x00400003u;
                goto page_done;
            }
            if (EffMenuState().field_54 == 1) {
                g_EffMenuAnimConfig.field_08 += step;
            } else {
                g_EffMenuAnimConfig.field_0c += step;
            }
            result_flags = 0x00400003u;
            goto page_done;
        page1_right:
            if (UiInput_Trigger3(7)) {
                if (EffMenuState().field_54 == 1) {
                    g_EffMenuAnimConfig.field_08 -= step * 20.0f;
                } else {
                    g_EffMenuAnimConfig.field_0c -= step * 20.0f;
                }
                result_flags = 0x00400003u;
                goto page_done;
            }
            if (UiInput_Trigger3(0x18)) {
                if (EffMenuState().field_54 == 1) {
                    g_EffMenuAnimConfig.field_08 -= step * 20.0f;
                } else {
                    g_EffMenuAnimConfig.field_0c -= step * 20.0f;
                }
                result_flags = 0x00400003u;
                goto page_done;
            }
            if (UiInput_Trigger3(8)) {
                if (EffMenuState().field_54 == 1) {
                    g_EffMenuAnimConfig.field_08 -= step * 100.0f;
                } else {
                    g_EffMenuAnimConfig.field_0c -= step * 100.0f;
                }
                result_flags = 0x00400003u;
                goto page_done;
            }
            if (UiInput_Trigger3(0x1C)) {
                if (EffMenuState().field_54 == 1) {
                    g_EffMenuAnimConfig.field_08 -= step * 100.0f;
                } else {
                    g_EffMenuAnimConfig.field_0c -= step * 100.0f;
                }
                result_flags = 0x00400003u;
                goto page_done;
            }
            if (EffMenuState().field_54 == 1) {
                g_EffMenuAnimConfig.field_08 -= step;
            } else {
                g_EffMenuAnimConfig.field_0c -= step;
            }
            result_flags = 0x00400003u;
            goto page_done;

        page1_updown:
            if (UiInput_Trigger(5)) {                       // 0x0024449C
                if (EffMenuState().field_54 == 2) {
                    EffMenuState().field_54 = 1;
                } else {
                    --EffMenuState().page_58;
                }
                goto page_done;
            }
            {
                const u8 prev = UiInput_Reset(5);         // 0x002444A0
                if (UiInput_Trigger(prev)) {
                    if (EffMenuState().field_54 == 2) {
                        EffMenuState().field_54 = 1;
                    } else {
                        --EffMenuState().page_58;
                    }
                    goto page_done;
                }
            }
            if (UiInput_Trigger(6)) {                       // 0x002444D8
                if (EffMenuState().field_54 == 1) {
                    EffMenuState().field_54 = 2;
                } else {
                    ++EffMenuState().page_58;
                    g_EffMenuObjectA.field_0c = 1;        // 0x00244530
                    g_EffMenuObjectA.flags_10 &= ~0x10u;
                }
                goto page_done;
            }
            {
                const u8 prev = UiInput_Reset(6);         // 0x002444F0
                if (UiInput_Trigger(prev)) {
                    if (EffMenuState().field_54 == 1) {
                        EffMenuState().field_54 = 2;
                    } else {
                        ++EffMenuState().page_58;
                        g_EffMenuObjectA.field_0c = 1;
                        g_EffMenuObjectA.flags_10 &= ~0x10u;
                    }
                }
            }
        } else if (page == 2) {
            // ---- page 2: confirm / cancel ---------------------------------
            if (UiInput_Trigger(5)) {                       // 0x00244548
                goto page2_confirm;
            }
            {
                const u8 prev = UiInput_Reset(5);         // 0x0024455C
                if (UiInput_Trigger(prev)) {
                    goto page2_confirm;
                }
            }
            if (UiInput_Trigger(6)) {                       // 0x002445A4
                goto page2_accept;
            }
            {
                const u8 prev = UiInput_Reset(6);         // 0x002445B8
                if (UiInput_Trigger(prev)) {
                    goto page2_accept;
                }
            }
            goto page_done;

        page2_confirm:
            // 0x00244578..0x0024459C: gated by object A's 0x20 bit.
            if ((g_EffMenuObjectA.flags_10 & 0x20u) == 0) {
                goto page_done;
            }
            --EffMenuState().page_58;
            g_EffMenuObjectA.flags_10 |= 0x10u;
            goto page_done;

        page2_accept:
            // 0x002445D4..0x002445F8: gated by object A's 0x20 bit.
            if ((g_EffMenuObjectA.flags_10 & 0x20u) == 0) {
                goto page_done;
            }
            EffMenuState().page_58 = 0;
            EffMenuState().field_54 = 1;
            EffMenuState().column_50 = 0;
            g_EffMenuObjectA.flags_10 |= 0x10u;
            goto clamp_common;
        }
    }

page_done:
clamp_common:
    // ---- common clamp/tail (0x002445FC..0x0024472C) ------------------------
    if (EffMenuState().column_50 < 0) {
        EffMenuState().column_50 = 0;
    } else if (EffMenuState().column_50 > span) {
        EffMenuState().column_50 = span;
    }

    EffMenuState().value_84 = Clamp01(EffMenuState().value_84);   // 0x0024461C
    g_EffMenuAnimConfig.field_08 = Clamp01(g_EffMenuAnimConfig.field_08);
    g_EffMenuAnimConfig.field_0c = Clamp01(g_EffMenuAnimConfig.field_0c);

    if (g_EffMenuAnimConfig.field_08 > g_EffMenuAnimConfig.field_0c) {
        const u32 index = static_cast<u32>(g_EffMenuObjectA.field_0c) * 3u;
        const u32 value = g_EffMenuObjectA.table_14[2u + index * 2u];
        if (value == reinterpret_cast<u32>(&g_EffMenuAnimConfig.field_08) ||
            (EffMenuState().page_58 == 1 && EffMenuState().field_54 == 1)) {
            g_EffMenuAnimConfig.field_08 = g_EffMenuAnimConfig.field_0c;
        }
    } else if (g_EffMenuAnimConfig.field_08 < g_EffMenuAnimConfig.field_0c) {
        g_EffMenuAnimConfig.field_0c = g_EffMenuAnimConfig.field_08;
    }

    if (g_EffMenuScroll.column != span - 1) {                  // 0x002446E4
        if (g_EffMenuScroll.column == 1) {
            g_EffMenuScroll.field_10 = 0.5f;
        } else if (g_EffMenuScroll.column == 2) {
            g_EffMenuScroll.field_18 =
                (g_EffMenuScroll.field_10 + 1.0f) * 0.5f;
        }
    }

    // ---- copy the scene back into the caller's item/slot -------------------
    slot->word[0] = g_EffMenuScene.slot_374[0];                // 0x00244730
    slot->word[1] = g_EffMenuScene.slot_374[1];
    slot->word[2] = g_EffMenuScene.slot_374[2];
    slot->word[3] = g_EffMenuScene.slot_374[3];
    *reinterpret_cast<f32*>(&item->state) = g_EffMenuScene.state_350[0];
    item->field_04 = g_EffMenuScene.state_350[1];
    item->field_08 = *reinterpret_cast<const u32*>(&g_EffMenuScene.state_350[2]);
    item->field_0c = g_EffMenuScene.state_350[3];
    item->field_10 = g_EffMenuScene.state_350[4];
    item->field_14 = g_EffMenuScene.state_350[5];
    item->field_18 = g_EffMenuScene.state_350[6];
    item->field_1c = g_EffMenuScene.state_350[7];
    item->field_20 = g_EffMenuScene.field_370;

    const s32 column2 = EffMenuState().column_50;               // r5
    if (column2 == 0) {
        item->field_04 = *reinterpret_cast<const f32*>(
            &EffMenuState().color_5c);
    } else if (column2 == span) {
        item->field_08 = EffMenuState().color_5c;
    } else {
        u8* entry = reinterpret_cast<u8*>(item) + column2 * 8;
        *reinterpret_cast<u32*>(entry + 4) = EffMenuState().color_5c;
        *reinterpret_cast<f32*>(entry + 8) = EffMenuState().value_84;
        if (span > 2) {
            if (column2 > 1) {
                if (*reinterpret_cast<f32*>(entry) >
                    EffMenuState().value_84) {
                    *reinterpret_cast<f32*>(entry) = EffMenuState().value_84;
                    *reinterpret_cast<f32*>(entry - 4) = EffMenuState().value_84;
                }
            } else if (EffMenuState().value_84 >
                       *reinterpret_cast<f32*>(entry + 0x10)) {
                *reinterpret_cast<f32*>(entry + 0x10) =
                    EffMenuState().value_84;
                *reinterpret_cast<f32*>(entry + 4) = EffMenuState().value_84;
            }
        }
    }

    // ---- scale the three values by the item count (0x002447C4..0x0024482C) --
    const f32 count_f = static_cast<f32>(count);
    colors[column2] = EffMenuState().color_5c;
    values[column2] = EffMenuState().value_84;
    EffMenuState().field_88 =
        static_cast<s32>(EffMenuState().value_84 * count_f);
    EffMenuState().field_8c =
        static_cast<s32>(g_EffMenuAnimConfig.field_08 * count_f);
    EffMenuState().field_90 =
        static_cast<s32>(g_EffMenuAnimConfig.field_0c * count_f);

    EffMenu_DrawQuadBar(0xA0, 8, 0xC8, 0xB0,
                        static_cast<f32>(EffMenuState().field_90),
                        static_cast<f32>(EffMenuState().field_88));

    AsdUiObject_Update(&g_EffMenuObjectA);                     // 0x00244840
    if (EffMenuState().mode_4c == 1) {
        AsdUiObject_Update(&g_EffMenuObjectB);                 // 0x00244850
    }

    EffMenu_DrawQuadRect(0xA8, 0x10, 0xB8, 0x10,
                         0x80808080u, 0xFF000000u);             // 0x0024487C

    // ---- per-value bars (0x00244880..0x0024499C) --------------------------
    for (s32 i = 0; i < span; ++i) {
        const f32 a = values[i] * 184.0f;
        const f32 b = values[i + 1] * 184.0f;
        const s32 x = static_cast<s32>(a) + 0xA8;
        const s32 width = static_cast<s32>(b) - x + 0xA8;
        const u32 color0 = (colors[i] | 0xFF000000u);
        const u32 color1 = (colors[i + 1] | 0xFF000000u);
        EffMenu_PushNode(4, static_cast<u32>(x), 0x10,
                         static_cast<u32>(width), 0x10, color0, color1);
    }

    // ---- selection highlight when the value column is active --------------
    // 0x00244928: the loop counter is r4 == span after the first loop.
    const bool selected_last = (span == EffMenuState().column_50) &&
                               (EffMenuState().page_58 == 0);
    if (selected_last) {
        // 0x00244C58..0x00244CFC: two marker quads at (span-1, span).
        EffMenu_PushNode(6, static_cast<u32>(span - 1), 0x0C,
                         static_cast<u32>(span - 1), 0x24,
                         0xFF00FF00u, 0);
        EffMenu_PushNode(6, static_cast<u32>(span), 0x0C,
                         static_cast<u32>(span), 0x24,
                         0xFF00FF00u, 0);
    }

    // 0x002449A0: re-tests the same condition; after the 0x00244C58 path the
    // counter has advanced, so both node groups are emitted.
    if (selected_last) {
        // 0x00244D00..0x00244D58
        EffMenu_PushNode(6, 0x161, 0x0C, 0x161, 0x24, 0xFF00FF00u, 0);
        // 0x00244D5C..0x00244DA4
        EffMenu_PushNode(6, 0x160, 0x0C, 0x160, 0x24, 0xFF00FF00u, 0);
    } else {
        // 0x002449C0..0x00244A0C
        EffMenu_PushNode(6, 0x160, 0x0C, 0x160, 0x24, 0xFFFFFFFFu, 0);
    }

    // ---- secondary three-bar gauge (0x00244A10..0x00244BD4) ----------------
    colors[0] = 0;
    values[0] = 0.0f;
    EffMenu_DrawQuadRect(0xA8, 0x2C, 0xB8, 0x10,
                         0x80808080u, 0xFF000000u);
    for (s32 i = 0; i < 3; ++i) {
        const f32 a = values[i] * 184.0f;
        const f32 b = values[i + 1] * 184.0f;
        const s32 x = static_cast<s32>(a) + 0xA8;
        const s32 width = static_cast<s32>(b) - x + 0xA8;
        const u32 raw0 = colors[i];
        const u32 raw1 = colors[i + 1];
        EffMenu_PushNode(4, static_cast<u32>(x), 0x2C,
                         static_cast<u32>(width), 0x10,
                         EffMenu_ExpandColor(raw0),
                         EffMenu_ExpandColor(raw1));
        // 0x00244B60..0x00244B74: page 1's active sub-column gets two extra
        // marker quads in addition to the bar above.
        if (i == EffMenuState().field_54 && EffMenuState().page_58 == 1) {
            // 0x00244DA8..0x00244D58
            EffMenu_PushNode(6, 0x161, 0x0C, 0x161, 0x24,
                             0xFF00FF00u, 0);
            // 0x00244D5C..0x00244DA4
            EffMenu_PushNode(6, 0x160, 0x0C, 0x160, 0x24,
                             0xFF00FF00u, 0);
        }
    }

    // ---- slider chrome (0x00244BD8..0x00244C40) ----------------------------
    EffMenu_PushNode(6, 0x160, 0x28, 0x160, 0x40, 0xFFFFFFFFu, 0);
    UiText_Draw(0xA4, 0x44, 8, "0%15d", count);

    if (UiInput_Trigger2(1)) {                              // 0x00244C44
        goto input_done;
    }
    {
        const u8 id = UiInput_Reset(1);                        // 0x00244E5C
        if (UiInput_Trigger2(id)) {
            goto input_done;
        }
        if (EffMenuState().mode_4c == 0) {
            goto check_object_a;
        }
        if ((g_EffMenuObjectB.flags_10 & 8u) != 0) {
            result_flags |= 2u;
        }
        goto return_flags;
    }

input_done:
    if (EffMenuState().mode_4c != 0) {
        EffMenuState().mode_4c = 0;
        goto check_object_a;
    }
    result_flags &= ~1u;

check_object_a:
    if ((g_EffMenuObjectA.flags_10 & 8u) != 0) {
        result_flags |= 2u;
    }

return_flags:
    return static_cast<s32>(result_flags);
}
#endif

// ---------------------------------------------------------------------------
// 0x003D7630: battle-result panel state machine
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x003d7630, 4308)
__attribute__((naked)) s32 ui_func_003d7630(ResultWork* work, s32 frame) {
    asm volatile(
        ".word 0xe92d4ff0\n"
        ".word 0xe1a04000\n"
        ".word 0xed2d8b06\n"
        ".word 0xe24dd0cc\n"
        ".word 0xe5900028\n"
        ".word 0xe3500000\n"
        ".word 0x0a000416\n"
        ".word 0xe3500001\n"
        ".word 0x0a000003\n"
        ".word 0xe3500002\n"
        ".word 0x03e00000\n"
        ".word 0x0a000412\n"
        ".word 0xea000410\n"
        ".word 0xe5940634\n"
        ".word 0xe2846b01\n"
        ".word 0xe2866f8d\n"
        ".word 0xe3100001\n"
        ".word 0x0a00000d\n"
        ".word 0xe2845b01\n"
        ".word 0xe594163c\n"
        ".word 0xe2855f8f\n"
        ".word 0xe1a00004\n"
        ".word 0xebfffb8f\n"
        ".word 0xe5950000\n"
        ".word 0xe2800001\n"
        ".word 0xe5850000\n"
        ".word 0xe5941638\n"
        ".word 0xe1500001\n"
        ".word 0xda000002\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00001\n"
        ".word 0xe5860000\n"
        ".word 0xe5940634\n"
        ".word 0xed9faae4\n"
        ".word 0xeddf9ae4\n"
        ".word 0xe3100002\n"
        ".word 0xe2845b01\n"
        ".word 0x0a00002f\n"
        ".word 0xe594064c\n"
        ".word 0xeeb08a69\n"
        ".word 0xe2847b01\n"
        ".word 0xe3500000\n"
        ".word 0x0d9f8add\n"
        ".word 0xe2877f95\n"
        ".word 0x0a000001\n"
        ".word 0xe3500001\n"
        ".word 0x0eb08a4a\n"
        ".word 0xe3a01064\n"
        ".word 0xe3e00063\n"
        ".word 0xebfafe42\n"
        ".word 0xee000a10\n"
        ".word 0xeddfaad5\n"
        ".word 0xe3a01064\n"
        ".word 0xe3e00063\n"
        ".word 0xeeb80ac0\n"
        ".word 0xee280a00\n"
        ".word 0xee209a2a\n"
        ".word 0xebfafe3a\n"
        ".word 0xee000a10\n"
        ".word 0xe3a01064\n"
        ".word 0xe3e00063\n"
        ".word 0xeeb80ac0\n"
        ".word 0xee280a00\n"
        ".word 0xee608a2a\n"
        ".word 0xebfafe33\n"
        ".word 0xee000a10\n"
        ".word 0xed859a90\n"
        ".word 0xedc58a91\n"
        ".word 0xeeb80ac0\n"
        ".word 0xee280a00\n"
        ".word 0xee200a2a\n"
        ".word 0xed850a92\n"
        ".word 0xe5940654\n"
        ".word 0xe2800001\n"
        ".word 0xe5870000\n"
        ".word 0xe5941650\n"
        ".word 0xe1500001\n"
        ".word 0xda000007\n"
        ".word 0xe5940634\n"
        ".word 0xeef0aa69\n"
        ".word 0xe3c00002\n"
        ".word 0xe5860000\n"
        ".word 0xe2840d19\n"
        ".word 0xedc0aa02\n"
        ".word 0xedc0aa01\n"
        ".word 0xedc0aa00\n"
        ".word 0xe5940634\n"
        ".word 0xe284ab01\n"
        ".word 0xe284bb01\n"
        ".word 0xe3100004\n"
        ".word 0xe28aaf6b\n"
        ".word 0xe28bbf5a\n"
        ".word 0x0a000015\n"
        ".word 0xed9a0a00\n"
        ".word 0xeddb0a00\n"
        ".word 0xe2847b01\n"
        ".word 0xe2848b01\n"
        ".word 0xee308a60\n"
        ".word 0xe5942668\n"
        ".word 0xe594066c\n"
        ".word 0xe5941664\n"
        ".word 0xe2877f9a\n"
        ".word 0xe2888f99\n"
        ".word 0xebf93f10\n"
        ".word 0xee200a08\n"
        ".word 0xed850a96\n"
        ".word 0xe5970000\n"
        ".word 0xe2800001\n"
        ".word 0xe5870000\n"
        ".word 0xe5981000\n"
        ".word 0xe1500001\n"
        ".word 0xda000002\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00004\n"
        ".word 0xe5860000\n"
        ".word 0xe5940634\n"
        ".word 0xe3100008\n"
        ".word 0x0a000015\n"
        ".word 0xed950a77\n"
        ".word 0xedd50a66\n"
        ".word 0xe2847b01\n"
        ".word 0xe2848b01\n"
        ".word 0xee308a60\n"
        ".word 0xe5942678\n"
        ".word 0xe594067c\n"
        ".word 0xe5941674\n"
        ".word 0xe2877f9e\n"
        ".word 0xe2888f9d\n"
        ".word 0xebf93ef7\n"
        ".word 0xee200a08\n"
        ".word 0xed850a9c\n"
        ".word 0xe5970000\n"
        ".word 0xe2800001\n"
        ".word 0xe5870000\n"
        ".word 0xe5981000\n"
        ".word 0xe1500001\n"
        ".word 0xda000002\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00008\n"
        ".word 0xe5860000\n"
        ".word 0xe5940634\n"
        ".word 0xe3100010\n"
        ".word 0x0a00000d\n"
        ".word 0xe2847b01\n"
        ".word 0xe5941684\n"
        ".word 0xe2877fa1\n"
        ".word 0xe1a00004\n"
        ".word 0xebfff810\n"
        ".word 0xe5970000\n"
        ".word 0xe2800001\n"
        ".word 0xe5870000\n"
        ".word 0xe5941680\n"
        ".word 0xe1500001\n"
        ".word 0xda000002\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00010\n"
        ".word 0xe5860000\n"
        ".word 0xe5940634\n"
        ".word 0xeddfaa6b\n"
        ".word 0xe3100020\n"
        ".word 0x0a00000f\n"
        ".word 0xe5940694\n"
        ".word 0xe59f81a0\n"
        ".word 0xe2847b01\n"
        ".word 0xee000a10\n"
        ".word 0xe2877fa5\n"
        ".word 0xedd80a02\n"
        ".word 0xeeb80ac0\n"
        ".word 0xee200a20\n"
        ".word 0xee200a2a\n"
        ".word 0xebfb7ecb\n"
        ".word 0xedd80a01\n"
        ".word 0xee200a20\n"
        ".word 0xed850aa3\n"
        ".word 0xe5970000\n"
        ".word 0xe2800001\n"
        ".word 0xe5870000\n"
        ".word 0xe5940634\n"
        ".word 0xe3100702\n"
        ".word 0x0a00001f\n"
        ".word 0xe284000c\n"
        ".word 0xe594172c\n"
        ".word 0xe5942728\n"
        ".word 0xec900a06\n"
        ".word 0xe3a00000\n"
        ".word 0xee318ac0\n"
        ".word 0xee728a60\n"
        ".word 0xee329ac1\n"
        ".word 0xebf93ebb\n"
        ".word 0xe284000c\n"
        ".word 0xedd40a05\n"
        ".word 0xec901a02\n"
        ".word 0xee490a00\n"
        ".word 0xe2840b01\n"
        ".word 0xe2800fca\n"
        ".word 0xee081a00\n"
        ".word 0xee481a80\n"
        ".word 0xe8900003\n"
        ".word 0xe2800001\n"
        ".word 0xe5840728\n"
        ".word 0xedc40a02\n"
        ".word 0xe1500001\n"
        ".word 0xec841a02\n"
        ".word 0xda000007\n"
        ".word 0xe2841018\n"
        ".word 0xe5943020\n"
        ".word 0xe8910006\n"
        ".word 0xe8840006\n"
        ".word 0xe5843008\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00702\n"
        ".word 0xe5860000\n"
        ".word 0xe5940634\n"
        ".word 0xe3100502\n"
        ".word 0x11a00004\n"
        ".word 0x1bfffc2d\n"
        ".word 0xe5940634\n"
        ".word 0xe2841b01\n"
        ".word 0xe2811ffa\n"
        ".word 0xe58d10b4\n"
        ".word 0xe2841b02\n"
        ".word 0xe2811018\n"
        ".word 0xe58d10b0\n"
        ".word 0xe2841d21\n"
        ".word 0xe58d107c\n"
        ".word 0xe2841e81\n"
        ".word 0xe58d1078\n"
        ".word 0xe2841e7e\n"
        ".word 0xe58d1080\n"
        ".word 0xe2841b01\n"
        ".word 0xe2811fef\n"
        ".word 0xe58d1084\n"
        ".word 0xe2841b01\n"
        ".word 0xe2849b01\n"
        ".word 0xe2847b01\n"
        ".word 0xe2811fe9\n"
        ".word 0xe3100c01\n"
        ".word 0xe2899fb9\n"
        ".word 0xe2877f63\n"
        ".word 0xe58d10b8\n"
        ".word 0x1a0000e6\n"
        ".word 0xe3100c02\n"
        ".word 0x0a00001c\n"
        ".word 0xe2840b01\n"
        ".word 0xe2841b01\n"
        ".word 0xe2800fa7\n"
        ".word 0xe2811fa7\n"
        ".word 0xe58d0068\n"
        ".word 0xe891000e\n"
        ".word 0xe2848e6a\n"
        ".word 0xe1a00003\n"
        ".word 0xebf93e7c\n"
        ".word 0xedd50a77\n"
        ".word 0xee200a20\n"
        ".word 0xed850aa6\n"
        ".word 0xe5981000\n"
        ".word 0xe2811001\n"
        ".word 0xe5881000\n"
        ".word 0xe59d0068\n"
        ".word 0xe5900000\n"
        ".word 0xe1510000\n"
        ".word 0xda000009\n"
        ".word 0xea000005\n"
        ".word 0x3f800000\n"
        ".word 0x00000000\n"
        ".word 0x3e4ccccd\n"
        ".word 0x3c23d70a\n"
        ".word 0x4222f983\n"
        ".word 0x004342c8\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00c02\n"
        ".word 0xe5860000\n"
        ".word 0xe5941634\n"
        ".word 0xe3110b01\n"
        ".word 0x0a000017\n"
        ".word 0xe3110602\n"
        ".word 0xe2848e6b\n"
        ".word 0x0a000131\n"
        ".word 0xed950a7b\n"
        ".word 0xedd50a8c\n"
        ".word 0xe2841b01\n"
        ".word 0xe2811fab\n"
        ".word 0xee308a60\n"
        ".word 0xe8910006\n"
        ".word 0xe59406b4\n"
        ".word 0xebf93e5a\n"
        ".word 0xedd50a8c\n"
        ".word 0xee480a00\n"
        ".word 0xedc50aaa\n"
        ".word 0xe59406b0\n"
        ".word 0xe2800001\n"
        ".word 0xe5880000\n"
        ".word 0xe59416ac\n"
        ".word 0xe1500001\n"
        ".word 0xda000003\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00602\n"
        ".word 0xe3c00b01\n"
        ".word 0xe5860000\n"
        ".word 0xe5940634\n"
        ".word 0xe3100b02\n"
        ".word 0x0a000017\n"
        ".word 0xed950a7a\n"
        ".word 0xedd50a8b\n"
        ".word 0xe2840b01\n"
        ".word 0xe2841b01\n"
        ".word 0xee308a60\n"
        ".word 0xe2800faf\n"
        ".word 0xe2811faf\n"
        ".word 0xe58d00bc\n"
        ".word 0xe891000e\n"
        ".word 0xe2848d1b\n"
        ".word 0xe1a00003\n"
        ".word 0xebf93e3e\n"
        ".word 0xee200a08\n"
        ".word 0xed850a69\n"
        ".word 0xe5981000\n"
        ".word 0xe2811001\n"
        ".word 0xe5881000\n"
        ".word 0xe59d00bc\n"
        ".word 0xe5900000\n"
        ".word 0xe1510000\n"
        ".word 0xda000002\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00b02\n"
        ".word 0xe5860000\n"
        ".word 0xe5940634\n"
        ".word 0xe2841b01\n"
        ".word 0xe2848b01\n"
        ".word 0xe2811fb7\n"
        ".word 0xe3100a01\n"
        ".word 0xe2888fb6\n"
        ".word 0xe58d10bc\n"
        ".word 0x0a000014\n"
        ".word 0xed9a0a00\n"
        ".word 0xeddb0a00\n"
        ".word 0xe2841b01\n"
        ".word 0xe2811fb6\n"
        ".word 0xee308a60\n"
        ".word 0xe8910006\n"
        ".word 0xe59406e0\n"
        ".word 0xebf93e22\n"
        ".word 0xee280a00\n"
        ".word 0xed850ab3\n"
        ".word 0xe59d00bc\n"
        ".word 0xe59d10bc\n"
        ".word 0xe5900000\n"
        ".word 0xe2800001\n"
        ".word 0xe5810000\n"
        ".word 0xe5981000\n"
        ".word 0xe1500001\n"
        ".word 0xda000002\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00a01\n"
        ".word 0xe5860000\n"
        ".word 0xe5940634\n"
        ".word 0xe2841b01\n"
        ".word 0xe2811f71\n"
        ".word 0xe58d10c8\n"
        ".word 0xe2841e6f\n"
        ".word 0xe2848b01\n"
        ".word 0xe3100a02\n"
        ".word 0xe2888fbd\n"
        ".word 0xe58d10c4\n"
        ".word 0x0a000021\n"
        ".word 0xe2890004\n"
        ".word 0xed971a00\n"
        ".word 0xedd92a00\n"
        ".word 0xedd70a01\n"
        ".word 0xed970a02\n"
        ".word 0xee311a62\n"
        ".word 0xecd01a02\n"
        ".word 0xe2841e6f\n"
        ".word 0xe59d00c8\n"
        ".word 0xe8910006\n"
        ".word 0xee700ae1\n"
        ".word 0xee300a42\n"
        ".word 0xecd01a03\n"
        ".word 0xe59406f8\n"
        ".word 0xee319ac1\n"
        ".word 0xee728a60\n"
        ".word 0xee328ac0\n"
        ".word 0xebf93df9\n"
        ".word 0xee690a00\n"
        ".word 0xee281a80\n"
        ".word 0xee280a00\n"
        ".word 0xe2850fb9\n"
        ".word 0xed850abb\n"
        ".word 0xecc00a02\n"
        ".word 0xe5980000\n"
        ".word 0xe2800001\n"
        ".word 0xe5880000\n"
        ".word 0xe59d10c4\n"
        ".word 0xe5911000\n"
        ".word 0xe1500001\n"
        ".word 0xda000002\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00a02\n"
        ".word 0xe5860000\n"
        ".word 0xe5940634\n"
        ".word 0xe3100902\n"
        ".word 0x0a000025\n"
        ".word 0xe59d00c8\n"
        ".word 0xe2841e6f\n"
        ".word 0xe8910006\n"
        ".word 0xed902a00\n"
        ".word 0xed901a01\n"
        ".word 0xed900a02\n"
        ".word 0xe59f0820\n"
        ".word 0xedd02a00\n"
        ".word 0xedd01a01\n"
        ".word 0xedd00a02\n"
        ".word 0xee328a62\n"
        ".word 0xee718a61\n"
        ".word 0xee309a60\n"
        ".word 0xe59406f8\n"
        ".word 0xebf93dd7\n"
        ".word 0xee680a00\n"
        ".word 0xe59f07f8\n"
        ".word 0xee281a80\n"
        ".word 0xee290a00\n"
        ".word 0xedd01a00\n"
        ".word 0xee710aa0\n"
        ".word 0xedc90a00\n"
        ".word 0xedd00a01\n"
        ".word 0xee700a81\n"
        ".word 0xedc90a01\n"
        ".word 0xedd00a02\n"
        ".word 0xee300a80\n"
        ".word 0xed890a02\n"
        ".word 0xe5980000\n"
        ".word 0xe2800001\n"
        ".word 0xe5880000\n"
        ".word 0xe59d10c4\n"
        ".word 0xe5911000\n"
        ".word 0xe1500001\n"
        ".word 0xda000002\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00902\n"
        ".word 0xe5860000\n"
        ".word 0xe5940634\n"
        ".word 0xe3100801\n"
        ".word 0x0a00000a\n"
        ".word 0xe1a00004\n"
        ".word 0xebfff976\n"
        ".word 0xe5941718\n"
        ".word 0xe2811001\n"
        ".word 0xe5841718\n"
        ".word 0xe5940714\n"
        ".word 0xe1510000\n"
        ".word 0xda000002\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00801\n"
        ".word 0xe5860000\n"
        ".word 0xe5940634\n"
        ".word 0xe3100802\n"
        ".word 0x0a00000b\n"
        ".word 0xe1a00004\n"
        ".word 0xebfffcbb\n"
        ".word 0xe59406dc\n"
        ".word 0xe59d10bc\n"
        ".word 0xe2800001\n"
        ".word 0xe5810000\n"
        ".word 0xe59416d8\n"
        ".word 0xe1500001\n"
        ".word 0xda000002\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00802\n"
        ".word 0xe5860000\n"
        ".word 0xe5940634\n"
        ".word 0xe3100c01\n"
        ".word 0x0a000078\n"
        ".word 0xe5940634\n"
        ".word 0xe3100c02\n"
        ".word 0x0a000012\n"
        ".word 0xe51f8344\n"
        ".word 0xe59427a4\n"
        ".word 0xe5980010\n"
        ".word 0xe598100c\n"
        ".word 0xed988a05\n"
        ".word 0xebf93d97\n"
        ".word 0xee200a08\n"
        ".word 0xed850ae5\n"
        ".word 0xe59d00b8\n"
        ".word 0xe59d10b8\n"
        ".word 0xe5900000\n"
        ".word 0xe2800001\n"
        ".word 0xe5810000\n"
        ".word 0xe598100c\n"
        ".word 0xe1500001\n"
        ".word 0xda000002\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00c02\n"
        ".word 0xe5860000\n"
        ".word 0xe5940634\n"
        ".word 0xe3100b01\n"
        ".word 0x0a000013\n"
        ".word 0xe2841b01\n"
        ".word 0xe2811fee\n"
        ".word 0xe59407c0\n"
        ".word 0xe8910006\n"
        ".word 0xed958a7b\n"
        ".word 0xebf93d81\n"
        ".word 0xee200a08\n"
        ".word 0xed850aeb\n"
        ".word 0xe59d0084\n"
        ".word 0xe59d1084\n"
        ".word 0xe5900000\n"
        ".word 0xe2800001\n"
        ".word 0xe5810000\n"
        ".word 0xe51f13d0\n"
        ".word 0xe5911018\n"
        ".word 0xe1500001\n"
        ".word 0xda000002\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00b01\n"
        ".word 0xe5860000\n"
        ".word 0xe5940634\n"
        ".word 0xe3100b02\n"
        ".word 0x0a000015\n"
        ".word 0xed950a7a\n"
        ".word 0xedd50a8b\n"
        ".word 0xe2841b01\n"
        ".word 0xe2811ff7\n"
        ".word 0xee308a60\n"
        ".word 0xe8910006\n"
        ".word 0xe59407e4\n"
        ".word 0xebf93d68\n"
        ".word 0xee200a08\n"
        ".word 0xed850af1\n"
        ".word 0xe59d0080\n"
        ".word 0xe5900000\n"
        ".word 0xe2801001\n"
        ".word 0xe59d0080\n"
        ".word 0xe5801000\n"
        ".word 0xe51f0434\n"
        ".word 0xe590001c\n"
        ".word 0xe1510000\n"
        ".word 0xda000002\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00b02\n"
        ".word 0xe5860000\n"
        ".word 0xe5940634\n"
        ".word 0xe3100a01\n"
        ".word 0x0a000015\n"
        ".word 0xed9a0a00\n"
        ".word 0xeddb0a00\n"
        ".word 0xe2841b02\n"
        ".word 0xe281100c\n"
        ".word 0xee308a60\n"
        ".word 0xe8910006\n"
        ".word 0xe5940814\n"
        ".word 0xebf93d4f\n"
        ".word 0xee200a08\n"
        ".word 0xed850afa\n"
        ".word 0xe59d0078\n"
        ".word 0xe5900000\n"
        ".word 0xe2801001\n"
        ".word 0xe59d0078\n"
        ".word 0xe5801000\n"
        ".word 0xe51f0498\n"
        ".word 0xe5900020\n"
        ".word 0xe1510000\n"
        ".word 0xda000002\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00a01\n"
        ".word 0xe5860000\n"
        ".word 0xe5940634\n"
        ".word 0xe3100a02\n"
        ".word 0x0a000028\n"
        ".word 0xe1a00004\n"
        ".word 0xebfffb10\n"
        ".word 0xe5940840\n"
        ".word 0xe2801001\n"
        ".word 0xe59d007c\n"
        ".word 0xe5801000\n"
        ".word 0xe51f04d8\n"
        ".word 0xe5900024\n"
        ".word 0xe1510000\n"
        ".word 0xda00001e\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00a02\n"
        ".word 0xe5860000\n"
        ".word 0xea00001a\n"
        ".word 0xe2841b01\n"
        ".word 0xe2811fab\n"
        ".word 0xe59406b4\n"
        ".word 0xe8910006\n"
        ".word 0xebf93d2b\n"
        ".word 0xedd50a7b\n"
        ".word 0xee200a20\n"
        ".word 0xed850aaa\n"
        ".word 0xeafffecf\n"
        ".word 0xedc59ae5\n"
        ".word 0xedc59aeb\n"
        ".word 0xedc59af4\n"
        ".word 0xedc59af1\n"
        ".word 0xe59d00b4\n"
        ".word 0xedc09a02\n"
        ".word 0xedc09a01\n"
        ".word 0xedc09a00\n"
        ".word 0xe59d00b0\n"
        ".word 0xedc09a02\n"
        ".word 0xedc09a01\n"
        ".word 0xedc09a00\n"
        ".word 0xe3a00000\n"
        ".word 0xe58407a4\n"
        ".word 0xe58407bc\n"
        ".word 0xe58407e0\n"
        ".word 0xe5840810\n"
        ".word 0xe5840840\n"
        ".word 0xedcd9a19\n"
        ".word 0xedcd9a18\n"
        ".word 0xe5940634\n"
        ".word 0xe3100901\n"
        ".word 0x0a00000b\n"
        ".word 0xebfa00c4\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xebfa0031\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xebfa00be\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xebf6dd56\n"
        ".word 0xe1c000d0\n"
        ".word 0xe1cd06f0\n"
        ".word 0xe5940634\n"
        ".word 0xe3100701\n"
        ".word 0x0a000014\n"
        ".word 0xe2840030\n"
        ".word 0xebfa0024\n"
        ".word 0xe28d1060\n"
        ".word 0xe28d2064\n"
        ".word 0xe2840030\n"
        ".word 0xebf98ae6\n"
        ".word 0xe2840030\n"
        ".word 0xe320f000\n"
        ".word 0xebf93cef\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000008\n"
        ".word 0xe3a00000\n"
        ".word 0xe5840030\n"
        ".word 0xe5840034\n"
        ".word 0xe5840038\n"
        ".word 0xe584003c\n"
        ".word 0xe5840040\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00701\n"
        ".word 0xe5860000\n"
        ".word 0xedcd9a23\n"
        ".word 0xedcd9a22\n"
        ".word 0xe5940634\n"
        ".word 0xe3100501\n"
        ".word 0x0a000014\n"
        ".word 0xe2840044\n"
        ".word 0xebfa000a\n"
        ".word 0xe28d1088\n"
        ".word 0xe28d208c\n"
        ".word 0xe2840044\n"
        ".word 0xebf98acc\n"
        ".word 0xe2840044\n"
        ".word 0xe320f000\n"
        ".word 0xebf93cd5\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000008\n"
        ".word 0xe3a00000\n"
        ".word 0xe5840044\n"
        ".word 0xe5840048\n"
        ".word 0xe584004c\n"
        ".word 0xe5840050\n"
        ".word 0xe5840054\n"
        ".word 0xe5940634\n"
        ".word 0xe3c00501\n"
        ".word 0xe5860000\n"
        ".word 0xeeb00a69\n"
        ".word 0xe3a01001\n"
        ".word 0xeddf0af9\n"
        ".word 0xe28d0028\n"
        ".word 0xed8d0a24\n"
        ".word 0xeeb01a40\n"
        ".word 0xed8daa25\n"
        ".word 0xed8d0a26\n"
        ".word 0xebfaeae3\n"
        ".word 0xe2840d16\n"
        ".word 0xeddd5a0a\n"
        ".word 0xed901a00\n"
        ".word 0xed9d5a0e\n"
        ".word 0xeddd4a12\n"
        ".word 0xee259a81\n"
        ".word 0xee258a01\n"
        ".word 0xee648a81\n"
        ".word 0xedd00a01\n"
        ".word 0xed9d4a0b\n"
        ".word 0xeddd3a0f\n"
        ".word 0xed9d3a13\n"
        ".word 0xed900a02\n"
        ".word 0xeddd2a0c\n"
        ".word 0xed9d2a10\n"
        ".word 0xee049a20\n"
        ".word 0xee038aa0\n"
        ".word 0xee438a20\n"
        ".word 0xeddd1a14\n"
        ".word 0xeddf0ae0\n"
        ".word 0xe28d10b8\n"
        ".word 0xe28d007c\n"
        ".word 0xee029a80\n"
        ".word 0xee028a00\n"
        ".word 0xee418a80\n"
        ".word 0xed950a67\n"
        ".word 0xee200a20\n"
        ".word 0xee200a2a\n"
        ".word 0xebfb550f\n"
        ".word 0xee290a09\n"
        ".word 0xed9d3a2e\n"
        ".word 0xeddd1a1f\n"
        ".word 0xe2840d16\n"
        ".word 0xee3a2a43\n"
        ".word 0xeeb04a43\n"
        ".word 0xe28d3014\n"
        ".word 0xee080a08\n"
        ".word 0xee080aa8\n"
        ".word 0xeef10ac0\n"
        ".word 0xee8a0a20\n"
        ".word 0xee692a00\n"
        ".word 0xee281a00\n"
        ".word 0xee280a80\n"
        ".word 0xee620a22\n"
        ".word 0xee623a01\n"
        ".word 0xee628aa2\n"
        ".word 0xee617a01\n"
        ".word 0xee208a00\n"
        ".word 0xee206a81\n"
        ".word 0xee606a80\n"
        ".word 0xee235a80\n"
        ".word 0xeef03a43\n"
        ".word 0xee024a28\n"
        ".word 0xee023a08\n"
        ".word 0xee423a27\n"
        ".word 0xeef05a46\n"
        ".word 0xeeb07a66\n"
        ".word 0xeef04a45\n"
        ".word 0xee016a80\n"
        ".word 0xee416ac1\n"
        ".word 0xee015aa2\n"
        ".word 0xee415ac0\n"
        ".word 0xee017a81\n"
        ".word 0xee414ae2\n"
        ".word 0xed8d4a0a\n"
        ".word 0xedcd5a0b\n"
        ".word 0xed8d7a0c\n"
        ".word 0xedcd9a0d\n"
        ".word 0xed8d6a0e\n"
        ".word 0xedcd3a0f\n"
        ".word 0xedcd4a10\n"
        ".word 0xedcd9a11\n"
        ".word 0xedcd6a12\n"
        ".word 0xed8d5a13\n"
        ".word 0xed8d3a14\n"
        ".word 0xedcd9a15\n"
        ".word 0xed900a00\n"
        ".word 0xed902a01\n"
        ".word 0xedd00a02\n"
        ".word 0xee641a00\n"
        ".word 0xee261a00\n"
        ".word 0xee260a80\n"
        ".word 0xe2840b01\n"
        ".word 0xe2800f5a\n"
        ".word 0xee451a82\n"
        ".word 0xee031a82\n"
        ".word 0xee050a02\n"
        ".word 0xee471a20\n"
        ".word 0xee041aa0\n"
        ".word 0xee030a20\n"
        ".word 0xedcd1a02\n"
        ".word 0xed8d1a03\n"
        ".word 0xed8d0a04\n"
        ".word 0xe8900007\n"
        ".word 0xe8830007\n"
        ".word 0xe2840b01\n"
        ".word 0xe2800f96\n"
        ".word 0xeddd0a05\n"
        ".word 0xed902a00\n"
        ".word 0xee700a82\n"
        ".word 0xee021a10\n"
        ".word 0xedcd0a05\n"
        ".word 0xedd02a01\n"
        ".word 0xee322a22\n"
        ".word 0xee022a90\n"
        ".word 0xed8d2a06\n"
        ".word 0xed903a02\n"
        ".word 0xee722a83\n"
        ".word 0xedcd2a07\n"
        ".word 0xe59d00b4\n"
        ".word 0xed903a00\n"
        ".word 0xee700a83\n"
        ".word 0xedcd0a05\n"
        ".word 0xed903a01\n"
        ".word 0xee322a03\n"
        ".word 0xed8d2a06\n"
        ".word 0xed903a02\n"
        ".word 0xe2840b01\n"
        ".word 0xe2800fb3\n"
        ".word 0xee723a83\n"
        ".word 0xedcd3a07\n"
        ".word 0xedd02a00\n"
        ".word 0xee303aa2\n"
        ".word 0xed8d3a05\n"
        ".word 0xedd00a01\n"
        ".word 0xee722a20\n"
        ".word 0xedcd2a06\n"
        ".word 0xedd00a02\n"
        ".word 0xe28d0008\n"
        ".word 0xee730aa0\n"
        ".word 0xedcd0a07\n"
        ".word 0xed952a9c\n"
        ".word 0xee700a82\n"
        ".word 0xedcd0a07\n"
        ".word 0xed952ae5\n"
        ".word 0xee700a82\n"
        ".word 0xedcd0a07\n"
        ".word 0xed952aa6\n"
        ".word 0xee302a82\n"
        ".word 0xed8d2a07\n"
        ".word 0xedd50a66\n"
        ".word 0xee611aa0\n"
        ".word 0xee200a20\n"
        ".word 0xee211a20\n"
        ".word 0xedcd1a02\n"
        ".word 0xee710a83\n"
        ".word 0xee701a02\n"
        ".word 0xed8d1a03\n"
        ".word 0xee311a22\n"
        ".word 0xed8d0a04\n"
        ".word 0xecc00a03\n"
        ".word 0xe59d00b0\n"
        ".word 0xed900a00\n"
        ".word 0xee300a80\n"
        ".word 0xed8d0a02\n"
        ".word 0xedd00a01\n"
        ".word 0xee710a20\n"
        ".word 0xedcd0a03\n"
        ".word 0xed901a02\n"
        ".word 0xe2840d19\n"
        ".word 0xee311a81\n"
        ".word 0xed8d1a04\n"
        ".word 0xedd91a00\n"
        ".word 0xee300a21\n"
        ".word 0xed8d0a02\n"
        ".word 0xedd91a01\n"
        ".word 0xee700aa1\n"
        ".word 0xedcd0a03\n"
        ".word 0xedd91a02\n"
        ".word 0xee311a21\n"
        ".word 0xed8d1a04\n"
        ".word 0xedd01a00\n"
        ".word 0xee300a21\n"
        ".word 0xed8d0a02\n"
        ".word 0xedd01a01\n"
        ".word 0xee700aa1\n"
        ".word 0xedcd0a03\n"
        ".word 0xedd01a02\n"
        ".word 0xee311a21\n"
        ".word 0xe2840b01\n"
        ".word 0xe2800fa2\n"
        ".word 0xed8d1a04\n"
        ".word 0xe5941634\n"
        ".word 0xe3110040\n"
        ".word 0x0a000008\n"
        ".word 0xedd01a00\n"
        ".word 0xee300a21\n"
        ".word 0xed8d0a02\n"
        ".word 0xed900a01\n"
        ".word 0xee300a80\n"
        ".word 0xed8d0a03\n"
        ".word 0xed900a02\n"
        ".word 0xee310a00\n"
        ".word 0xed8d0a04\n"
        ".word 0xe5941634\n"
        ".word 0xe3110080\n"
        ".word 0x0a000008\n"
        ".word 0xed900a00\n"
        ".word 0xee330a00\n"
        ".word 0xed8d0a05\n"
        ".word 0xed900a01\n"
        ".word 0xee320a80\n"
        ".word 0xed8d0a06\n"
        ".word 0xed900a02\n"
        ".word 0xee320a00\n"
        ".word 0xed8d0a07\n"
        ".word 0xe28d0008\n"
        ".word 0xeddd0a18\n"
        ".word 0xed9d0a22\n"
        ".word 0xed9d2a19\n"
        ".word 0xe2846b01\n"
        ".word 0xec901a02\n"
        ".word 0xe28d0014\n"
        ".word 0xe2866fd9\n"
        ".word 0xee311a20\n"
        ".word 0xee711a82\n"
        ".word 0xee311a00\n"
        ".word 0xed8d1a02\n"
        ".word 0xeddd2a23\n"
        ".word 0xee711aa2\n"
        ".word 0xedcd1a03\n"
        ".word 0xec903a02\n"
        ".word 0xee730a20\n"
        ".word 0xee332a82\n"
        ".word 0xee300a80\n"
        ".word 0xee720a22\n"
        ".word 0xec800a02\n"
        ".word 0xed962a00\n"
        ".word 0xee311a02\n"
        ".word 0xed8d1a02\n"
        ".word 0xed962a01\n"
        ".word 0xee711a82\n"
        ".word 0xedcd1a03\n"
        ".word 0xedd62a02\n"
        ".word 0xed9d2a04\n"
        ".word 0xee322a22\n"
        ".word 0xed8d2a04\n"
        ".word 0xedd42a00\n"
        ".word 0xee311a22\n"
        ".word 0xed8d1a02\n"
        ".word 0xed941a01\n"
        ".word 0xee311a81\n"
        ".word 0xea000002\n"
        ".word 0x00493530\n"
        ".word 0x42800000\n"
        ".word 0x3cc90fdb\n"
        ".word 0xed8d1a03\n"
        ".word 0xed941a02\n"
        ".word 0xe2848b01\n"
        ".word 0xe2888fce\n"
        ".word 0xee321a01\n"
        ".word 0xed8d1a04\n"
        ".word 0xed941a00\n"
        ".word 0xee300a01\n"
        ".word 0xed8d0a05\n"
        ".word 0xed941a01\n"
        ".word 0xee700a81\n"
        ".word 0xedcd0a06\n"
        ".word 0xedd41a02\n"
        ".word 0xed9d1a07\n"
        ".word 0xee311a21\n"
        ".word 0xed8d1a07\n"
        ".word 0xedd81a00\n"
        ".word 0xee300a21\n"
        ".word 0xed8d0a05\n"
        ".word 0xed980a01\n"
        ".word 0xee300a80\n"
        ".word 0xed8d0a06\n"
        ".word 0xed980a02\n"
        ".word 0xee310a00\n"
        ".word 0xed8d0a07\n"
        ".word 0xe5940634\n"
        ".word 0xe3100303\n"
        ".word 0x0a000006\n"
        ".word 0xeef00a4a\n"
        ".word 0xed950a59\n"
        ".word 0xe2840058\n"
        ".word 0xebfba48b\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000003\n"
        ".word 0xeef00a4a\n"
        ".word 0xed950a58\n"
        ".word 0xe2840058\n"
        ".word 0xebfba484\n"
        ".word 0xed950a69\n"
        ".word 0xedd50af1\n"
        ".word 0xedcd9a27\n"
        ".word 0xedcd9a28\n"
        ".word 0xee300a20\n"
        ".word 0xe28d109c\n"
        ".word 0xe28d0090\n"
        ".word 0xe28d3008\n"
        ".word 0xe28d2014\n"
        ".word 0xed8d0a29\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe2841058\n"
        ".word 0xe1a00004\n"
        ".word 0xebfff5e0\n"
        ".word 0xed950a6a\n"
        ".word 0xedd50aeb\n"
        ".word 0xed951aaa\n"
        ".word 0xe3a01000\n"
        ".word 0xee300a20\n"
        ".word 0xeddf0a42\n"
        ".word 0xe2840058\n"
        ".word 0xee308a01\n"
        ".word 0xed9f1a3e\n"
        ".word 0xeeb00a48\n"
        ".word 0xebf80b31\n"
        ".word 0xe28d0014\n"
        ".word 0xe320f000\n"
        ".word 0xebf8e55c\n"
        ".word 0xe28d0008\n"
        ".word 0xe320f000\n"
        ".word 0xebf8e563\n"
        ".word 0xeeb00a48\n"
        ".word 0xe320f000\n"
        ".word 0xebf9251d\n"
        ".word 0xe28d9014\n"
        ".word 0xe2840b01\n"
        ".word 0xe899000e\n"
        ".word 0xe2800f5d\n"
        ".word 0xe880000e\n"
        ".word 0xe28d3008\n"
        ".word 0xe8930007\n"
        ".word 0xee000a10\n"
        ".word 0xe8870007\n"
        ".word 0xe2840b01\n"
        ".word 0xedd60a00\n"
        ".word 0xe2800fdf\n"
        ".word 0xe2844b01\n"
        ".word 0xee300a60\n"
        ".word 0xe2844fe2\n"
        ".word 0xed870a00\n"
        ".word 0xee001a10\n"
        ".word 0xedd60a01\n"
        ".word 0xee300a60\n"
        ".word 0xed870a01\n"
        ".word 0xee002a10\n"
        ".word 0xedd60a02\n"
        ".word 0xee300a60\n"
        ".word 0xed870a02\n"
        ".word 0xedd80a00\n"
        ".word 0xed9d0a05\n"
        ".word 0xee300a60\n"
        ".word 0xed800a00\n"
        ".word 0xedd80a01\n"
        ".word 0xed9d0a06\n"
        ".word 0xee300a60\n"
        ".word 0xed800a01\n"
        ".word 0xedd80a02\n"
        ".word 0xed9d0a07\n"
        ".word 0xee300a60\n"
        ".word 0xed800a02\n"
        ".word 0xedd60a00\n"
        ".word 0xed9d0a02\n"
        ".word 0xee300a60\n"
        ".word 0xed840a00\n"
        ".word 0xedd60a01\n"
        ".word 0xed9d0a03\n"
        ".word 0xee300a60\n"
        ".word 0xed840a01\n"
        ".word 0xedd60a02\n"
        ".word 0xed9d0a04\n"
        ".word 0xee300a60\n"
        ".word 0xed840a02\n"
        ".word 0xe3a00000\n"
        ".word 0xe28dd0cc\n"
        ".word 0xecbd8b06\n"
        ".word 0xe8bd8ff0\n"
        ".word 0x46c80000\n"
        ".word 0x3dcccccd\n"
        ".word 0xe2803b01\n"
        ".word 0xeddf0a0d\n"
        ".word 0xed830a7a\n"
        ".word 0xe58016bc\n"
        ".word 0xe58026c4\n"
        ".word 0xedc30aae\n"
        ".word 0xe59025a4\n"
        ".word 0xe3a01000\n"
        ".word 0xe58016c0\n"
        ".word 0xe2801b01\n"
        ".word 0xe580262c\n"
        ".word 0xe5900634\n"
        ".word 0xe2811f8d\n"
        ".word 0xe3800b02\n"
        ".word 0xe5810000\n"
        ".word 0xe12fff1e\n"
        ".word 0x00000000\n"
    );
}
#if 0
// Original partial readable draft retained for reconstruction; not compiled.
s32 ui_func_003d7630(ResultWork* work, s32 frame) {
    (void)frame;                                          // r1 is unused
    if (work->state_28 == 0) {                            // 0x003D7640
        return 0;
    }
    if (work->state_28 == 2) {
        return -1;                                        // 0x003D7658
    }
    if (work->state_28 != 1) {
        return 0;
    }

    // The listing writes `[r6]` (work+0x634) after every clear; binding a
    // reference keeps the sub-calls observing the same bits.
    u32& flags = work->flags_634;
    u8* const base = reinterpret_cast<u8*>(work);

    // ---- bit 0: spin timer (0x003D7664..0x003D76B0) ------------------------
    if ((flags & 1u) != 0) {
        Result_UpdateSpin(work, *I32At(work, 0x63C));
        const s32 t = *I32At(work, 0x63C) + 1;
        *I32At(work, 0x63C) = t;
        if (t > *I32At(work, 0x638)) {
            flags &= ~1u;
        }
    }

    // ---- bit 1: random jitter (0x003D76B4..0x003D7784) ---------------------
    if ((flags & 2u) != 0) {
        f32 amount;
        if (work->mode_64c == 0) {
            amount = 0.2f;                                // 0x3E4CCCCD
        } else if (work->mode_64c == 1) {
            amount = 1.0f;
        } else {
            amount = 0.0f;
        }
        const f32 rx = static_cast<f32>(RandomInclusive(-100, 100));
        const f32 ry = static_cast<f32>(RandomInclusive(-100, 100));
        const f32 rz = static_cast<f32>(RandomInclusive(-100, 100));
        *F32At(work, 0x640) = amount * rx * 0.01f;        // 0x003D7738
        *F32At(work, 0x644) = amount * ry * 0.01f;
        *F32At(work, 0x648) = amount * rz * 0.01f;
        const s32 t = work->timer_654 + 1;
        work->timer_654 = t;
        if (t > work->limit_650) {                        // 0x003D7760
            flags &= ~2u;
            *F32At(work, 0x640) = 0.0f;                   // 0x003D7778
            *F32At(work, 0x644) = 0.0f;
            *F32At(work, 0x648) = 0.0f;
        }
    }

    // ---- bit 2: X interpolation (0x003D7788..0x003D77FC) ------------------
    if ((flags & 4u) != 0) {
        const f32 delta = *F32At(work, 0x5AC) - *F32At(work, 0x568);
        const f32 e = UiMath_Ease(*I32At(work, 0x66C), *I32At(work, 0x664),
                                  *I32At(work, 0x668));
        *F32At(work, 0x658) = e * delta;                  // 0x003D77D4
        const s32 t = *I32At(work, 0x668) + 1;
        *I32At(work, 0x668) = t;
        if (t > *I32At(work, 0x664)) {
            flags &= ~4u;
        }
    }

    // ---- bit 3: Y interpolation (0x003D77FC..0x003D7860) ------------------
    if ((flags & 8u) != 0) {
        const f32 delta = *F32At(work, 0x5DC) - *F32At(work, 0x598);
        const f32 e = UiMath_Ease(*I32At(work, 0x67C), *I32At(work, 0x674),
                                  *I32At(work, 0x678));
        *F32At(work, 0x670) = e * delta;                  // 0x003D7838
        const s32 t = *I32At(work, 0x678) + 1;
        *I32At(work, 0x678) = t;
        if (t > *I32At(work, 0x674)) {
            flags &= ~8u;
        }
    }

    // ---- bit 4: fade timer (0x003D7860..0x003D78A4) -----------------------
    if ((flags & 0x10u) != 0) {
        Result_UpdateFade(work, *I32At(work, 0x684));
        const s32 t = *I32At(work, 0x684) + 1;
        *I32At(work, 0x684) = t;
        if (t > *I32At(work, 0x680)) {
            flags &= ~0x10u;
        }
    }

    // ---- bit 5: sine pulse (0x003D78A4..0x003D78F4) -----------------------
    if ((flags & 0x20u) != 0) {
        const f32 angle = static_cast<f32>(*I32At(work, 0x694)) *
                          g_ResultAnim.field_08 * 40.7436638f;
        *F32At(work, 0x68C) =
            ui_func_002b740c(angle) * g_ResultAnim.field_04;
        ++*I32At(work, 0x694);
    }

    // ---- bit 0x80000: slide-in interpolation (0x003D78F4..0x003D7980) -----
    if ((flags & 0x80000u) != 0) {
        // 0x003D790C: vldmia [work+0x0C] {s0..s5}, then
        //   s16 = s3-s0 = work[0x18]-work[0x0C]
        //   s17 = s4-s1 = work[0x1C]-work[0x10]
        //   s18 = s5-s2 = work[0x20]-work[0x14]
        const f32 dx = *F32At(work, 0x18) - *F32At(work, 0x0C);
        const f32 dy = *F32At(work, 0x1C) - *F32At(work, 0x10);
        const f32 dz = *F32At(work, 0x20) - *F32At(work, 0x14);
        const f32 e = UiMath_Ease(0, *I32At(work, 0x72C),
                                  *I32At(work, 0x728));
        // 0x003D7924..0x003D7958: interpolate from the +0x0C triple and
        // store X/Y/Z as work[0x00]/[0x04]/[0x08].
        *F32At(work, 0x00) = *F32At(work, 0x0C) + dx * e;
        *F32At(work, 0x04) = *F32At(work, 0x10) + dy * e;
        *F32At(work, 0x08) = *F32At(work, 0x14) + dz * e;
        const s32 t = *I32At(work, 0x728) + 1;
        *I32At(work, 0x728) = t;
        if (t > *I32At(work, 0x72C)) {
            *F32At(work, 0x00) = *F32At(work, 0x18);
            *F32At(work, 0x04) = *F32At(work, 0x1C);
            *F32At(work, 0x08) = *F32At(work, 0x20);
            flags &= ~0x80000u;
        }
    }

    // ---- bit 0x800000: slide update (0x003D7980..0x003D7990) --------------
    if ((flags & 0x800000u) != 0) {
        Result_UpdateSlide(work);
    }

    // Group pointers rebuilt at 0x003D7994..0x003D79F0.
    const u32 p_7e8 = 0x7E8;                              // [sp+0xB4]
    const u32 p_818 = 0x818;                              // [sp+0xB0]
    const u32 p_840 = 0x840;                              // [sp+0x7C]
    const u32 p_810 = 0x810;                              // [sp+0x78]
    const u32 p_7e0 = 0x7E0;                              // [sp+0x80]
    const u32 p_7bc = 0x7BC;                              // [sp+0x84]
    const u32 p_7a4 = 0x7A4;                              // [sp+0xB8]
    const u32 p_6e4 = 0x6E4;                              // sb
    const u32 p_58c = 0x58C;                              // r7

    if ((flags & 0x100u) == 0) {
        // ---- first animation group (0x003D79F4..0x003D7D84) ---------------
        if ((flags & 0x200u) != 0) {
            const f32 e = UiMath_Ease(*I32At(work, 0x6A4),
                                      *I32At(work, 0x69C),
                                      *I32At(work, 0x6A0));
            *F32At(work, 0x698) = e * *F32At(work, 0x5DC);
            const s32 t = *I32At(work, 0x6A0) + 1;
            *I32At(work, 0x6A0) = t;
            if (t > *I32At(work, 0x69C)) {
                flags &= ~0x200u;
            }
        }
        if ((flags & 0x400u) != 0) {
            if ((flags & 0x200000u) != 0) {
                const f32 delta = *F32At(work, 0x5EC) - *F32At(work, 0x630);
                const f32 e = UiMath_Ease(*I32At(work, 0x6B4),
                                          *I32At(work, 0x6AC),
                                          *I32At(work, 0x6B0));
                *F32At(work, 0x6A8) =
                    *F32At(work, 0x630) + delta * e;
                const s32 t = *I32At(work, 0x6B0) + 1;
                *I32At(work, 0x6B0) = t;
                if (t > *I32At(work, 0x6AC)) {
                    flags &= ~0x200000u;
                    flags &= ~0x400u;
                }
            } else {
                // 0x003D7F50: hold at the end position, then reuse the timer.
                const f32 e = UiMath_Ease(*I32At(work, 0x6B4),
                                          *I32At(work, 0x6AC),
                                          *I32At(work, 0x6B0));
                *F32At(work, 0x6A8) = e * *F32At(work, 0x5EC);
                const s32 t = *I32At(work, 0x6B0) + 1;
                *I32At(work, 0x6B0) = t;
                if (t > *I32At(work, 0x6AC)) {
                    flags &= ~0x200000u;
                    flags &= ~0x400u;
                }
            }
        }
        if ((flags & 0x800u) != 0) {
            const f32 delta = *F32At(work, 0x5E8) - *F32At(work, 0x62C);
            const f32 e = UiMath_Ease(*I32At(work, 0x6C4),
                                      *I32At(work, 0x6BC),
                                      *I32At(work, 0x6C0));
            *F32At(work, 0x5A4) = e * delta;
            const s32 t = *I32At(work, 0x6C0) + 1;
            *I32At(work, 0x6C0) = t;
            if (t > *I32At(work, 0x6BC)) {
                flags &= ~0x800u;
            }
        }
        if ((flags & 0x1000u) != 0) {
            const f32 delta = *F32At(work, 0x5AC) - *F32At(work, 0x568);
            const f32 e = UiMath_Ease(*I32At(work, 0x6E0),
                                      *I32At(work, 0x6D8),
                                      *I32At(work, 0x6DC));
            *F32At(work, 0x6CC) = e * delta;
            const s32 t = *I32At(work, 0x6DC) + 1;
            *I32At(work, 0x6DC) = t;
            if (t > *I32At(work, 0x6D8)) {
                flags &= ~0x1000u;
            }
        }
        if ((flags & 0x2000u) != 0) {
            const f32 dx = *F32At(work, p_58c) - *F32At(work, p_6e4);
            const f32 dy = *F32At(work, 0x590) - *F32At(work, 0x6E8);
            const f32 dz = *F32At(work, 0x594) - *F32At(work, 0x6EC);
            const f32 e = UiMath_Ease(*I32At(work, 0x6F8),
                                      *I32At(work, 0x6F0),
                                      *I32At(work, 0x6F4));
            *F32At(work, p_6e4) =
                (*F32At(work, 0x5C4) - dx) * e;
            *F32At(work, 0x6E8) =
                (*F32At(work, 0x5C8) - dy) * e;
            *F32At(work, 0x6EC) =
                (*F32At(work, 0x5CC) - dz) * e;
            const s32 t = *I32At(work, 0x6F4) + 1;
            *I32At(work, 0x6F4) = t;
            if (t > *I32At(work, 0x6F0)) {
                flags &= ~0x2000u;
            }
        }
        if ((flags & 0x8000u) != 0) {
            const f32 dx = *F32At(work, 0x5C4) - g_ResultOrigin[0];
            const f32 dy = *F32At(work, 0x5C8) - g_ResultOrigin[1];
            const f32 dz = *F32At(work, 0x5CC) - g_ResultOrigin[2];
            const f32 e = UiMath_Ease(*I32At(work, 0x6F8),
                                      *I32At(work, 0x6F0),
                                      *I32At(work, 0x6F4));
            *F32At(work, p_6e4) = g_ResultOrigin[0] + dx * e;
            *F32At(work, 0x6E8) = g_ResultOrigin[1] + dy * e;
            *F32At(work, 0x6EC) = g_ResultOrigin[2] + dz * e;
            const s32 t = *I32At(work, 0x6F4) + 1;
            *I32At(work, 0x6F4) = t;
            if (t > *I32At(work, 0x6F0)) {
                flags &= ~0x8000u;
            }
        }
        if ((flags & 0x10000u) != 0) {
            Result_UpdateBars(work);                       // 0x003D7D20
            const s32 t = *I32At(work, 0x718) + 1;
            *I32At(work, 0x718) = t;
            if (t > *I32At(work, 0x714)) {
                flags &= ~0x10000u;
            }
        }
        if ((flags & 0x20000u) != 0) {
            Result_UpdatePanel(work);                      // 0x003D7D58
            const s32 t = *I32At(work, 0x6DC) + 1;
            *I32At(work, 0x6DC) = t;
            if (t > *I32At(work, 0x6D8)) {
                flags &= ~0x20000u;
            }
        }
    } else {
        // ---- second animation group (0x003D7D90..0x003D7D84) --------------
        if ((flags & 0x200u) != 0) {
            const f32 e = UiMath_Ease(g_ResultAnim.field_10,
                                      g_ResultAnim.field_0c,
                                      *I32At(work, p_7a4));
            *F32At(work, 0x794) = e * g_ResultAnim.field_14;
            const s32 t = *I32At(work, 0x7A4) + 1;
            *I32At(work, 0x7A4) = t;
            if (t > g_ResultAnim.field_0c) {
                flags &= ~0x200u;
            }
        }
        if ((flags & 0x400u) != 0) {
            const f32 e = UiMath_Ease(*I32At(work, 0x7C0),
                                      *I32At(work, 0x7B8),
                                      *I32At(work, 0x7BC));
            *F32At(work, 0x7AC) = e * *F32At(work, 0x5EC);
            const s32 t = *I32At(work, p_7bc) + 1;
        *I32At(work, p_7bc) = t;
            if (t > g_ResultAnim.field_18) {
                flags &= ~0x400u;
            }
        }
        if ((flags & 0x800u) != 0) {
            const f32 delta = *F32At(work, 0x5E8) - *F32At(work, 0x62C);
            const f32 e = UiMath_Ease(*I32At(work, 0x7E4),
                                      *I32At(work, 0x7DC),
                                      *I32At(work, 0x7E0));
            *F32At(work, 0x7C4) = e * delta;
            const s32 t = *I32At(work, p_7e0) + 1;
        *I32At(work, p_7e0) = t;
            if (t > g_ResultAnim.field_1c) {
                flags &= ~0x800u;
            }
        }
        if ((flags & 0x1000u) != 0) {
            const f32 delta = *F32At(work, 0x5AC) - *F32At(work, 0x568);
            const f32 e = UiMath_Ease(*I32At(work, 0x814),
                                      *I32At(work, 0x80C),
                                      *I32At(work, 0x810));
            *F32At(work, p_7e8) = e * delta;
            const s32 t = *I32At(work, p_810) + 1;
        *I32At(work, p_810) = t;
            if (t > g_ResultAnim.field_20) {
                flags &= ~0x1000u;
            }
        }
        if ((flags & 0x2000u) != 0) {
            Result_UpdateScale(work);                      // 0x003D7F1C
            const s32 t = *I32At(work, p_840) + 1;
        *I32At(work, p_840) = t;
            if (t > g_ResultAnim.field_24) {
                flags &= ~0x2000u;
            }
        }
    }

    if ((flags & 0x100u) == 0) {
        // ---- reset the second-group values (0x003D7F74..0x003D7FB8) -------
        *F32At(work, 0x794) = 0.0f;
        *F32At(work, 0x7AC) = 0.0f;
        *F32At(work, 0x7D0) = 0.0f;
        *F32At(work, 0x7C4) = 0.0f;
        *F32At(work, p_7e8) = 0.0f;
        *F32At(work, 0x7EC) = 0.0f;
        *F32At(work, 0x7F0) = 0.0f;
        *F32At(work, p_818) = 0.0f;
        *F32At(work, 0x81C) = 0.0f;
        *F32At(work, 0x820) = 0.0f;
        work->field_7a4 = 0;
        work->field_7bc = 0;
        work->field_7e0 = 0;
        work->field_810 = 0;
        work->field_840 = 0;
    }

    // ---- object bounds probes (0x003D7FBC..0x003D80C4) --------------------
    f32 bound_w = 0.0f;                                   // [sp+0x60]
    f32 bound_h = 0.0f;                                   // [sp+0x64]
    f32 bound_w2 = 0.0f;                                  // [sp+0x88]
    f32 bound_h2 = 0.0f;                                  // [sp+0x8C]
    if ((flags & 0x4000u) != 0) {
        void* scene = UiScene_GetFocus();
        UiObject_UpdateBounds(scene);
        void* record = UiScene_GetTransform(UiScene_GetFocus());
        bound_w = *reinterpret_cast<const f32*>(record);
        bound_h = *reinterpret_cast<const f32*>(
            static_cast<const u8*>(record) + 4);
    }
    if ((flags & 0x40000u) != 0) {
        UiObject_UpdateBounds(base + 0x30);
        UiObject_GetSize(base + 0x30, &bound_w, &bound_h);
        if (UiObject_IsReady(base + 0x30)) {
            for (s32 i = 0; i < 5; ++i) {
                *I32At(work, 0x30 + i * 4) = 0;
            }
            flags &= ~0x40000u;
        }
    }
    if ((flags & 0x400000u) != 0) {
        UiObject_UpdateBounds(base + 0x44);
        UiObject_GetSize(base + 0x44, &bound_w2, &bound_h2);
        if (UiObject_IsReady(base + 0x44)) {
            for (s32 i = 0; i < 5; ++i) {
                *I32At(work, 0x44 + i * 4) = 0;
            }
            flags &= ~0x400000u;
        }
    }

    // ---- transform build (0x003D80C8..0x003D8260) -------------------------
    f32 m[12] = {};                                       // [sp+0x28]
    // The listing sets [sp+0x90..0x98] = {0,1,0}; the euler constructor only
    // consumes the three float arguments in s0..s2.
    f32 up[3] = {0.0f, 1.0f, 0.0f};                       // [sp+0x90]
    Matrix_FromEuler(m, 1, 0.0f, 64.0f, 0.0f);             // 0x003D80E8

    const f32 sx = work->scale_580[0];
    const f32 sy = work->scale_580[1];
    const f32 sz = work->scale_580[2];
    f32 vx = m[0] * sx + m[1] * sy + m[2] * sz;
    f32 vy = m[4] * sx + m[5] * sy + m[6] * sz;
    f32 vz = m[8] * sx + m[9] * sy + m[10] * sz;

    const f32 len = std::sqrt(vx * vx + vy * vy + vz * vz);
    const f32 inv = (len != 0.0f) ? (1.0f / len) : 0.0f;
    vx *= inv;
    vy *= inv;
    vz *= inv;

    // 0x003D8138..0x003D8218: sine/cos from the rotation angle at +0x59C,
    // then a Rodrigues matrix into m[].
    f32 sin_a = 0.0f;
    f32 cos_a = 1.0f;
    {
        const f32 angle = *F32At(work, 0x59C) * 0.024543693f *
                          40.7436638f;
        UiMath_SinCos(&sin_a, &cos_a, angle);
    }
    const f32 t = 1.0f - cos_a;
    const f32 xx = vx * vx;
    const f32 yy = vy * vy;
    const f32 zz = vz * vz;
    const f32 xy = vx * vy;
    const f32 xz = vx * vz;
    const f32 yz = vy * vz;
    f32 rot[12] = {};
    rot[0] = cos_a + t * xx;
    rot[1] = t * xy - sin_a * vz;
    rot[2] = t * xz + sin_a * vy;
    rot[4] = t * xy + sin_a * vz;
    rot[5] = cos_a + t * yy;
    rot[6] = t * yz - sin_a * vx;
    rot[8] = t * xz - sin_a * vy;
    rot[9] = t * yz + sin_a * vx;
    rot[10] = cos_a + t * zz;

    f32 scaled[3];
    scaled[0] = rot[0] * sx + rot[1] * sy + rot[2] * sz;
    scaled[1] = rot[4] * sx + rot[5] * sy + rot[6] * sz;
    scaled[2] = rot[8] * sx + rot[9] * sy + rot[10] * sz;

    f32 pos[3];                                            // [sp+0x14]
    pos[0] = *F32At(work, 0x568) + *F32At(work, 0x658);
    pos[1] = *F32At(work, 0x56C) + *F32At(work, 0x65C);
    pos[2] = *F32At(work, 0x570) + *F32At(work, 0x660);
    pos[0] += *F32At(work, p_7e8);
    pos[1] += *F32At(work, 0x7EC);
    pos[2] += *F32At(work, 0x7F0);
    pos[0] += *F32At(work, 0x6CC);
    pos[1] += *F32At(work, 0x6D0);
    pos[2] += *F32At(work, 0x6D4);
    pos[2] += *F32At(work, 0x670);
    pos[2] += *F32At(work, 0x794);
    pos[2] += *F32At(work, 0x698);

    const f32 scale = *F32At(work, 0x598);
    scaled[0] *= scale;
    scaled[1] *= scale;
    scaled[2] *= scale;

    f32 p8[3];                                             // [sp+8]
    p8[0] = scaled[0] + pos[0];
    p8[1] = scaled[1] + pos[1];
    p8[2] = scaled[2] + pos[2];
    p8[0] += *F32At(work, p_818);
    p8[1] += *F32At(work, 0x81C);
    p8[2] += *F32At(work, 0x820);
    p8[0] += *F32At(work, p_6e4);
    p8[1] += *F32At(work, 0x6E8);
    p8[2] += *F32At(work, 0x6EC);
    p8[0] += *F32At(work, 0x640);
    p8[1] += *F32At(work, 0x644);
    p8[2] += *F32At(work, 0x648);
    if ((flags & 0x40u) != 0) {
        p8[0] += *F32At(work, 0x688);
        p8[1] += *F32At(work, 0x68C);
        p8[2] += *F32At(work, 0x690);
    }
    if ((flags & 0x80u) != 0) {
        pos[0] += *F32At(work, 0x688);
        pos[1] += *F32At(work, 0x68C);
        pos[2] += *F32At(work, 0x690);
    }

    // 0x003D8424..0x003D8474: fold in the two bound sizes.
    p8[0] += bound_w;
    p8[1] += bound_h;
    p8[0] += bound_w2;
    p8[1] += bound_h2;
    pos[0] += bound_w;
    pos[1] += bound_h;
    pos[0] += bound_w2;
    pos[1] += bound_h2;

    p8[0] += *F32At(work, 0x764);
    p8[1] += *F32At(work, 0x768);
    p8[2] += *F32At(work, 0x76C);
    p8[0] += *F32At(work, 0x000);
    p8[1] += *F32At(work, 0x004);
    p8[2] += *F32At(work, 0x008);
    pos[0] += *F32At(work, 0x000);
    pos[1] += *F32At(work, 0x004);
    pos[2] += *F32At(work, 0x008);
    pos[0] += *F32At(work, 0x738);
    pos[1] += *F32At(work, 0x73C);
    pos[2] += *F32At(work, 0x740);

    // 0x003D8528..0x003D8560
    if ((flags & 0x0C000000u) != 0) {
        Effect_SetScale(base + 0x58, *F32At(work, 0x564), 1.0f);
    } else {
        Effect_SetScale(base + 0x58, *F32At(work, 0x560), 1.0f);
    }

    f32 effect_out[3] = {0.0f, 0.0f, 0.0f};                // [sp+0x9C]
    effect_out[2] = *F32At(work, 0x5A4) + *F32At(work, 0x7C4);

    Result_DrawEffect(work, base + 0x58, pos, p8, up,
                      effect_out);                        // 0x003D8594

    const f32 alpha = *F32At(work, 0x5A8) + *F32At(work, 0x7AC) +
                      *F32At(work, 0x6A8);
    // 0x003D85A4 sets r1=0 in addition to s0/s1/s2.
    Effect_SetAlphaScale(base + 0x58, 0, alpha, 0.1f, 100.0f); // 0x003D85C0

    UiMath_ApplyMatrixA(pos);                              // 0x003D85CC
    UiMath_ApplyMatrixB(p8);                               // 0x003D85D8
    UiMath_ScaleCurrent(alpha);                            // 0x003D85E4

    *F32At(work, 0x574) = pos[0];
    *F32At(work, 0x578) = pos[1];
    *F32At(work, 0x57C) = pos[2];
    *F32At(work, p_58c) = p8[0];
    *F32At(work, 0x590) = p8[1];
    *F32At(work, 0x594) = p8[2];

    *F32At(work, p_58c) -= *F32At(work, 0x764);            // 0x003D860C
    *F32At(work, 0x590) -= *F32At(work, 0x768);
    *F32At(work, 0x594) -= *F32At(work, 0x76C);
    *F32At(work, 0x77C) = pos[0] - *F32At(work, 0x738);
    *F32At(work, 0x780) = pos[1] - *F32At(work, 0x73C);
    *F32At(work, 0x784) = pos[2] - *F32At(work, 0x740);
    *F32At(work, 0x788) = p8[0] - *F32At(work, 0x764);
    *F32At(work, 0x78C) = p8[1] - *F32At(work, 0x768);
    *F32At(work, 0x790) = p8[2] - *F32At(work, 0x76C);

    return 0;                                             // 0x003D86A8
}
#endif

/** Tail routine inside the 0x003D7630 ledger span (0x003D86C0..0x003D8700).
 *  It arms the 0x800 shake bit and seeds the three vectors:
 *  +0x5E8 = s0, +0x6BC = r1, +0x6C4 = r2, +0x6B8 = 0,
 *  +0x62C = +0x5A4, +0x6C0 = 0 (0x003D86C0..0x003D86FC). */
void Result_BeginShake(ResultWork* work, s32 a, s32 b, f32 value) {
    *F32At(work, 0x5E8) = value;
    *I32At(work, 0x6BC) = a;
    *I32At(work, 0x6C4) = b;
    *F32At(work, 0x6B8) = 0.0f;
    const s32 seed = *I32At(work, 0x5A4);
    *I32At(work, 0x62C) = seed;
    *I32At(work, 0x6C0) = 0;
    *U32At(work, 0x634) |= 0x800u;
}

// ---------------------------------------------------------------------------
// 0x001E83FC: talk-target / model selection overlay
// ---------------------------------------------------------------------------

namespace {

/** 0x002BA520 wrapper.  Most quads repeat one model handle four times, but
 *  the case-1 primary quad (0x001E87BC..0x001E87DC) and the marker quads pass
 *  0xFFFFFFFF in all four handle registers. */
void TalkDrawQuad(u32 object, u32 a, u32 b, u32 c, const f32* m,
                  f32 s12, f32 s13, f32 s14, f32 s15,
                  f32 t0, f32 t1, f32 t2, f32 t3) {
    Title_DrawQuad(object, a, b, c,
                         m[0], m[1], m[2], m[3], m[4], m[5],
                         m[6], m[7], m[8], m[9], m[10], m[11],
                         s12, s13, s14, s15, t0, t1, t2, t3);
}

/** `ldr r0,[pc]=0x0044ea00; ldr r0,[r0]; bl 0x002c1d3c` pattern. */
void TalkSetModel(u32 model) {
    Ui_DrawModel(g_AsdGpuState, reinterpret_cast<void*>(model));
}

/** Plain "handle 0x080 + matrix 0x090" draw used by cases 1/2/3/4/5/6/18. */
void TalkDrawMain(const TalkTargetEntry* e) {
    TalkDrawQuad(e->handle_080, e->handle_080, e->handle_080,
                 e->handle_080, e->matrix_090,
                 0.0f, 0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f, 1.0f);
}

/** 0x001E8A30: refresh the secondary model and the main quad. */
void TalkDrawSecondary(TalkTargetEntry* e, TalkRenderer* rend) {
    (void)rend;
    TalkSetModel(e->handle_188);
    TalkDrawMain(e);
}

/** 0x001E89E4: marker quad for the 0x180/0x18C pair. */
void TalkDrawMarker(TalkTargetEntry* e) {
    TalkDrawQuad(0xFFFFFFFFu, 0xFFFFFFFFu, 0xFFFFFFFFu, 0xFFFFFFFFu,
                 e->matrix_0c0, 0.0f, 0.0f, 0.0f, 1.0f,
                 static_cast<f32>(e->handle_180), 0.0f,
                 static_cast<f32>(e->handle_180), 1.0f);
}

/** Size of one 0x001E83FC target record and the table base offset. */
constexpr s32 kTalkEntryStride = 0x194;

/** Detail-card ring: builds the procedural palette matrix and transforms the
 *  four 12-byte points selected by `r6 + 3` (0x001E9250..0x001E9368).
 *  Register aliases at 0x001E9258..0x001E9260:
 *    sb = 0x004B5D30 (case 1/3 source)
 *    fp = 0x004B6360 (case 4 source)
 *    r8 = 0x004B6990 (case 0/2 source)
 *    sl = 0x004B6FC0 (destination block, sb + 0x1290)
 *  `r6` is zero, so `r5 = r6 + 3` selects case 3: read sb, write sl.  The
 *  loop branch at 0x001E9368 returns to 0x001E9264, so the selection is
 *  loop-invariant. */
void TalkDrawDetailRing(TalkWork* work, TalkRenderer* rend, s32 ex, s32 ey) {
    TalkSetModel(rend->handle_18);
    const f32 off_x = work->field_24;                     // s20
    const f32 off_y = work->field_28 + 130.0f;            // s21
    const f32 off_z = work->field_2c;                     // s19
    f32 angle = UiCamera_GetAngle() + work->field_b0;
    angle *= 0.7111111f;                                  // 0x3F360B61

    // 0x001E90C0..0x001E9118: |angle| wrapped down to [0, 65536) by the
    // 0x47800000 (65536.0f) constant.  The second wrap loop at 0x001E9100
    // operates on the zero in s0 and is dead in this build.
    const bool negative = angle < 0.0f;                   // movlo r5,#1
    f32 wrapped = std::fabs(angle);
    while (wrapped >= 65536.0f) {
        wrapped -= 65536.0f;                              // 0x001E90F0
    }

    // 0x001E911C..0x001E9170: index = trunc(|angle|), frac = |angle| - index;
    // palette rows 0 and (index & 0xFF) are the two endpoints.
    const u32 index = static_cast<u32>(wrapped);
    const f32 frac = wrapped - static_cast<f32>(index);
    const UiColorEntry& p0 = g_UiColorTable[0];
    const UiColorEntry& p = g_UiColorTable[index & 0xFF];

    // 0x001E9174..0x001E91CC: four-endpoint lerp.
    //   A (s6)  = p0.r + 0 * p0.b = p0.r   (s4 = 0, 0x001E9190)
    //   B (s2)  = p0.g + 0 * p0.a = p0.g   (s5 = 0, 0x001E91A0)
    //   C (s0)  = p.r  + frac * p.b
    //   D (s1)  = p.g  + frac * p.a
    //   E (s9)  = p0.r   (the +0.0 lerp leaves it unchanged)
    //   F (s7)  = p0.g
    const f32 a = p0.r;
    const f32 b = p0.g;
    const f32 c = p.r + frac * p.b;
    const f32 d = p.g + frac * p.a;
    const f32 e = p0.r;
    const f32 f = p0.g;

    // 0x001E91D0/0x001E91D8/0x001E91E0: vnegne.  The first and third are
    // conditioned on r4/ip, both zero here; the second mirrors the sign of
    // the input angle.
    const f32 cn = negative ? -c : c;

    // 0x001E91E4..0x001E9248: cross basis, stored as 12 words at [sp+8].
    f32 m[12] = {};
    m[0] = f * d;                                         // s11
    m[1] = b * e - a * f * cn;                            // s12
    m[2] = a * e + b * f * cn;                            // s10
    m[3] = 0.0f;
    m[4] = e * d;                                         // s7
    m[5] = b * f + a * e * cn;                            // s8
    m[6] = a * f - b * e * cn;                            // s5
    m[7] = 0.0f;
    m[8] = -cn;                                           // s13
    m[9] = a * d;                                         // s6
    m[10] = b * d;                                        // s1
    m[11] = 0.0f;

    // 0x001E9264..0x001E9314: `ldrlo pc,[pc,r5,lsl #2]` with r5 = 3.
    // Entries: 0/2 -> r8 (0x004B6990), 1/3 -> sb (0x004B5D30),
    //          4 -> fp (0x004B6360).
    constexpr u32 kBlockFloats = 0x630 / 4;               // 0x630-byte blocks
    f32* const base = QuadTableBase();
    const s32 selector = 3;                                // r5 = r6 + 3, r6 = 0
    const f32* src = base;                                 // case 3 -> sb
    switch (selector) {
    case 0:
    case 2: src = base + 2 * kBlockFloats; break;         // 0x004B6990 (sb + 0xC60)
    case 1:
    case 3: src = base; break;                             // 0x004B5D30
    case 4: src = base + kBlockFloats; break;              // 0x004B6360
    default: break;
    }
    f32* const dst = DetailRingOutputBase();               // 0x004B6FC0

    for (s32 i = 0; i < 4; ++i) {
        const f32* const in = src + i * 3;
        f32 point[3];
        point[0] = in[0];
        point[1] = in[1];
        point[2] = in[2] + 0.0f;                          // s18 == 0, 0x001E9324
        f32 out[3];
        Matrix_TransformPoint(out, m, point);              // 0x001E9338
        // 0x001E933C..0x001E9364: always write block sl (0x004B6FC0).
        dst[i * 3 + 0] = out[0] + off_x;
        dst[i * 3 + 1] = out[1] + off_y;
        dst[i * 3 + 2] = out[2] + off_z;
    }

    // 0x001E936C: final quad over the transformed block sl.
    TalkDrawQuad(0xFFFFFFFFu, 0xFFFFFFFFu, 0xFFFFFFFFu, 0xFFFFFFFFu,
                 dst,
                 0.0f, 0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f, 1.0f);
    (void)ex;
    (void)ey;
}

} // namespace

// DECOMP_FUNC(0x001e83fc, 4380)
__attribute__((naked)) void ui_func_001e83fc() {
    asm volatile(
        ".word 0xe92d5ff0\n"
        ".word 0xe59f03f0\n"
        ".word 0xed2d8b08\n"
        ".word 0xe24dde4a\n"
        ".word 0xe5901380\n"
        ".word 0xe3510000\n"
        ".word 0xe59f13e0\n"
        ".word 0xe5916000\n"
        ".word 0x0a0003f8\n"
        ".word 0xe5d01022\n"
        ".word 0xe3510000\n"
        ".word 0x1a0003f5\n"
        ".word 0xe5d00024\n"
        ".word 0xe3500000\n"
        ".word 0x1a0003f2\n"
        ".word 0xe59f73c0\n"
        ".word 0xe5970000\n"
        ".word 0xe5900000\n"
        ".word 0xe3500003\n"
        ".word 0x0a0003ed\n"
        ".word 0xe59f03b0\n"
        ".word 0xe3a08000\n"
        ".word 0xe1a01008\n"
        ".word 0xe5904000\n"
        ".word 0xe3a00005\n"
        ".word 0xeb0376c5\n"
        ".word 0xe2844a01\n"
        ".word 0xe2844f93\n"
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
        ".word 0x0a000003\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c40018\n"
        ".word 0xe59fa358\n"
        ".word 0xe59fb35c\n"
        ".word 0xed9faad5\n"
        ".word 0xe3a05000\n"
        ".word 0xe28d9fa2\n"
        ".word 0xe28d7088\n"
        ".word 0xe3a00065\n"
        ".word 0xe0000095\n"
        ".word 0xe0864100\n"
        ".word 0xe5f401d0\n"
        ".word 0xe3500000\n"
        ".word 0x11d400fc\n"
        ".word 0x13500000\n"
        ".word 0x15d41042\n"
        ".word 0x13510000\n"
        ".word 0x0a000051\n"
        ".word 0xe350000c\n"
        ".word 0x0a000014\n"
        ".word 0xaa000006\n"
        ".word 0xe3500000\n"
        ".word 0x0a00004c\n"
        ".word 0xe3500006\n"
        ".word 0x13500008\n"
        ".word 0x1350000a\n"
        ".word 0x1a00001e\n"
        ".word 0xea00000c\n"
        ".word 0xe350000e\n"
        ".word 0x0a00000e\n"
        ".word 0xe350000f\n"
        ".word 0x0a000010\n"
        ".word 0xe3500011\n"
        ".word 0x0a000012\n"
        ".word 0xe3500012\n"
        ".word 0x05db002a\n"
        ".word 0x03500000\n"
        ".word 0x05db0029\n"
        ".word 0x03500000\n"
        ".word 0x1a000011\n"
        ".word 0xea00003a\n"
        ".word 0xe5db002a\n"
        ".word 0xe3500000\n"
        ".word 0x1a00000d\n"
        ".word 0xea000036\n"
        ".word 0xe5db002a\n"
        ".word 0xe3500000\n"
        ".word 0x1a000009\n"
        ".word 0xea000032\n"
        ".word 0xe5db002a\n"
        ".word 0xe3500000\n"
        ".word 0x1a000005\n"
        ".word 0xea00002e\n"
        ".word 0xe5db002a\n"
        ".word 0xe3500000\n"
        ".word 0x05db0029\n"
        ".word 0x03500000\n"
        ".word 0x0a000029\n"
        ".word 0xe2840090\n"
        ".word 0xec900a06\n"
        ".word 0xe28400ac\n"
        ".word 0xee701a21\n"
        ".word 0xee700a82\n"
        ".word 0xee310a22\n"
        ".word 0xec902a02\n"
        ".word 0xe28400b4\n"
        ".word 0xed941a2a\n"
        ".word 0xee311a81\n"
        ".word 0xee700a82\n"
        ".word 0xee300a22\n"
        ".word 0xecd01a03\n"
        ".word 0xe59f023c\n"
        ".word 0xe5900000\n"
        ".word 0xee311a21\n"
        ".word 0xee700a82\n"
        ".word 0xee300a22\n"
        ".word 0xe280004c\n"
        ".word 0xee611a0a\n"
        ".word 0xee202a8a\n"
        ".word 0xee602a0a\n"
        ".word 0xec900a03\n"
        ".word 0xeb027dda\n"
        ".word 0xe5940014\n"
        ".word 0xe3500001\n"
        ".word 0x13500003\n"
        ".word 0x0a000050\n"
        ".word 0xe3500002\n"
        ".word 0x13500004\n"
        ".word 0x0a00004d\n"
        ".word 0xe3500005\n"
        ".word 0x13500007\n"
        ".word 0x0a00004a\n"
        ".word 0xe59f01fc\n"
        ".word 0xee101a10\n"
        ".word 0xe1500001\n"
        ".word 0xca000003\n"
        ".word 0xe0890108\n"
        ".word 0xe7875108\n"
        ".word 0xed800a00\n"
        ".word 0xe2888001\n"
        ".word 0xe2855001\n"
        ".word 0xe3550080\n"
        ".word 0xbaffffa0\n"
        ".word 0xe248a001\n"
        ".word 0xe35a0000\n"
        ".word 0xe3a00000\n"
        ".word 0xc1a0e009\n"
        ".word 0xda000018\n"
        ".word 0xe0482000\n"
        ".word 0xe3520000\n"
        ".word 0xda000012\n"
        ".word 0xe08e1100\n"
        ".word 0xe1a0c001\n"
        ".word 0xe0873100\n"
        ".word 0xeddc0a00\n"
        ".word 0xed910a00\n"
        ".word 0xeef40ac0\n"
        ".word 0xeef1fa10\n"
        ".word 0x2a000006\n"
        ".word 0xe7979100\n"
        ".word 0xe5935000\n"
        ".word 0xe5839000\n"
        ".word 0xe59c9000\n"
        ".word 0xe5819000\n"
        ".word 0xe7875100\n"
        ".word 0xed8c0a00\n"
        ".word 0xe2522001\n"
        ".word 0xe2811004\n"
        ".word 0xe2833004\n"
        ".word 0x1affffef\n"
        ".word 0xe2800001\n"
        ".word 0xe15a0000\n"
        ".word 0xcaffffe6\n"
        ".word 0xe59f915c\n"
        ".word 0xed9f8a57\n"
        ".word 0xeddf8a57\n"
        ".word 0xe3580000\n"
        ".word 0xe3a05000\n"
        ".word 0xda0001eb\n"
        ".word 0xe7971105\n"
        ".word 0xe3a00065\n"
        ".word 0xe0000091\n"
        ".word 0xe0860100\n"
        ".word 0xe2804e1d\n"
        ".word 0xe1d400fc\n"
        ".word 0xe3500013\n"
        ".word 0x379ff100\n"
        ".word 0xea0001df\n"
        ".word 0x001e8e70\n"
        ".word 0x001e874c\n"
        ".word 0x001e882c\n"
        ".word 0x001e8918\n"
        ".word 0x001e8978\n"
        ".word 0x001e89d0\n"
        ".word 0x001e8a88\n"
        ".word 0x001e89d0\n"
        ".word 0x001e8a88\n"
        ".word 0x001e89d0\n"
        ".word 0x001e8a88\n"
        ".word 0x001e89d0\n"
        ".word 0x001e8a88\n"
        ".word 0x001e8978\n"
        ".word 0x001e8af4\n"
        ".word 0x001e8b04\n"
        ".word 0x001e8b14\n"
        ".word 0x001e8c18\n"
        ".word 0x001e8d50\n"
        ".word 0xee100a10\n"
        ".word 0xe150000a\n"
        ".word 0xbaffffb9\n"
        ".word 0xeaffffb4\n"
        ".word 0xe59f00a8\n"
        ".word 0xe5900004\n"
        ".word 0xe5901060\n"
        ".word 0xe59f00a4\n"
        ".word 0xe5900000\n"
        ".word 0xeb036575\n"
        ".word 0xe1d402f8\n"
        ".word 0xe0800fa0\n"
        ".word 0xe1a000c0\n"
        ".word 0xe1a01fc0\n"
        ".word 0xe0801f21\n"
        ".word 0xe3c11003\n"
        ".word 0xe0500001\n"
        ".word 0x0ef09a68\n"
        ".word 0x0eb09a68\n"
        ".word 0x0a00000a\n"
        ".word 0xe3500001\n"
        ".word 0x0ef09a68\n"
        ".word 0x0eb09a4a\n"
        ".word 0x0a000006\n"
        ".word 0xe3500002\n"
        ".word 0x0ef09a68\n"
        ".word 0x0d9f9a1e\n"
        ".word 0x0a000002\n"
        ".word 0xe3500003\n"
        ".word 0x0ef09a68\n"
        ".word 0x0d9f9a1b\n"
        ".word 0xe284a090\n"
        ".word 0xe3e03000\n"
        ".word 0xee797a0a\n"
        ".word 0xeef06a49\n"
        ".word 0xee390a88\n"
        ".word 0xeeb07a69\n"
        ".word 0xeeb06a69\n"
        ".word 0xe1a02003\n"
        ".word 0xe1a01003\n"
        ".word 0xe1a00003\n"
        ".word 0xedcd7a03\n"
        ".word 0xed8d0a02\n"
        ".word 0xed8d9a01\n"
        ".word 0xed8d0a00\n"
        ".word 0xec9a0a0c\n"
        ".word 0xea000045\n"
        ".word 0x0049f91c\n"
        ".word 0x00447a78\n"
        ".word 0x004474f4\n"
        ".word 0x0044ea00\n"
        ".word 0x43520000\n"
        ".word 0x3e800000\n"
        ".word 0x0049fb1c\n"
        ".word 0x43250000\n"
        ".word 0x3c23d70a\n"
        ".word 0x3f800000\n"
        ".word 0x00000000\n"
        ".word 0x3f000000\n"
        ".word 0x3f400000\n"
        ".word 0xe51f0038\n"
        ".word 0xe51fa034\n"
        ".word 0xe5900004\n"
        ".word 0xe5901068\n"
        ".word 0xe59a0000\n"
        ".word 0xeb03653d\n"
        ".word 0xe5940084\n"
        ".word 0xe3500000\n"
        ".word 0x0a00000d\n"
        ".word 0xeef07a48\n"
        ".word 0xeeb06a68\n"
        ".word 0xe284c0f0\n"
        ".word 0xe1a03000\n"
        ".word 0xe1a02003\n"
        ".word 0xedcd7a03\n"
        ".word 0xedcd7a02\n"
        ".word 0xed8d6a01\n"
        ".word 0xedcd7a00\n"
        ".word 0xeeb07a46\n"
        ".word 0xec9c0a0c\n"
        ".word 0xeef06a46\n"
        ".word 0xe1a01002\n"
        ".word 0xeb034725\n"
        ".word 0xe5940088\n"
        ".word 0xe3500000\n"
        ".word 0x0a00000d\n"
        ".word 0xeef07a48\n"
        ".word 0xeeb06a68\n"
        ".word 0xe284ce12\n"
        ".word 0xe1a03000\n"
        ".word 0xe1a02003\n"
        ".word 0xedcd7a03\n"
        ".word 0xedcd7a02\n"
        ".word 0xed8d6a01\n"
        ".word 0xedcd7a00\n"
        ".word 0xeeb07a46\n"
        ".word 0xec9c0a0c\n"
        ".word 0xeef06a46\n"
        ".word 0xe1a01002\n"
        ".word 0xeb034714\n"
        ".word 0xe5941184\n"
        ".word 0xe59a0000\n"
        ".word 0xeb036518\n"
        ".word 0xeef07a48\n"
        ".word 0xeeb06a68\n"
        ".word 0xe284c090\n"
        ".word 0xedcd7a03\n"
        ".word 0xedcd7a02\n"
        ".word 0xed8d6a01\n"
        ".word 0xedcd7a00\n"
        ".word 0xe5940080\n"
        ".word 0xeeb07a46\n"
        ".word 0xec9c0a0c\n"
        ".word 0xeef06a46\n"
        ".word 0xe1a03000\n"
        ".word 0xe1a02000\n"
        ".word 0xe1a01000\n"
        ".word 0xeb034702\n"
        ".word 0xea000155\n"
        ".word 0xe51f0124\n"
        ".word 0xe5900004\n"
        ".word 0xe590104c\n"
        ".word 0xe51f0128\n"
        ".word 0xe5900000\n"
        ".word 0xeb036502\n"
        ".word 0xeef07a48\n"
        ".word 0xeeb06a68\n"
        ".word 0xe284a090\n"
        ".word 0xedcd7a03\n"
        ".word 0xedcd7a02\n"
        ".word 0xed8d6a01\n"
        ".word 0xedcd7a00\n"
        ".word 0xe5940080\n"
        ".word 0xeeb07a46\n"
        ".word 0xec9a0a0c\n"
        ".word 0xeef06a46\n"
        ".word 0xe1a03000\n"
        ".word 0xe1a02000\n"
        ".word 0xe1a01000\n"
        ".word 0xeb0346ec\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea00013d\n"
        ".word 0xe51f017c\n"
        ".word 0xe5941184\n"
        ".word 0xe5900000\n"
        ".word 0xeb0364ec\n"
        ".word 0xeef07a48\n"
        ".word 0xeeb06a68\n"
        ".word 0xe284a090\n"
        ".word 0xedcd7a03\n"
        ".word 0xedcd7a02\n"
        ".word 0xed8d6a01\n"
        ".word 0xedcd7a00\n"
        ".word 0xe5940080\n"
        ".word 0xeeb07a46\n"
        ".word 0xec9a0a0c\n"
        ".word 0xeef06a46\n"
        ".word 0xe1a03000\n"
        ".word 0xe1a02000\n"
        ".word 0xe1a01000\n"
        ".word 0xeb0346d6\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000127\n"
        ".word 0xe594118c\n"
        ".word 0xe3510000\n"
        ".word 0x15940180\n"
        ".word 0x11500009\n"
        ".word 0xda000012\n"
        ".word 0xe51f01e8\n"
        ".word 0xe5900000\n"
        ".word 0xeb0364d2\n"
        ".word 0xeef07a48\n"
        ".word 0xeeb06a68\n"
        ".word 0xe284a0c0\n"
        ".word 0xe3e03000\n"
        ".word 0xe1a02003\n"
        ".word 0xedcd7a03\n"
        ".word 0xe5940180\n"
        ".word 0xeeb07a46\n"
        ".word 0xeef06a46\n"
        ".word 0xe58d0008\n"
        ".word 0xed8d6a01\n"
        ".word 0xe58d0000\n"
        ".word 0xe1a01003\n"
        ".word 0xec9a0a0c\n"
        ".word 0xe1a00003\n"
        ".word 0xeb0346bb\n"
        ".word 0xe51f0234\n"
        ".word 0xe5941188\n"
        ".word 0xe5900000\n"
        ".word 0xeb0364be\n"
        ".word 0xeef07a48\n"
        ".word 0xeeb06a68\n"
        ".word 0xe284a090\n"
        ".word 0xedcd7a03\n"
        ".word 0xedcd7a02\n"
        ".word 0xed8d6a01\n"
        ".word 0xedcd7a00\n"
        ".word 0xe5940080\n"
        ".word 0xeeb07a46\n"
        ".word 0xec9a0a0c\n"
        ".word 0xeef06a46\n"
        ".word 0xe1a03000\n"
        ".word 0xe1a02000\n"
        ".word 0xe1a01000\n"
        ".word 0xeb0346a8\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea0000f9\n"
        ".word 0xe5db002a\n"
        ".word 0xe3500000\n"
        ".word 0x0a0000f6\n"
        ".word 0xe594118c\n"
        ".word 0xe3510000\n"
        ".word 0x0affffe3\n"
        ".word 0xe51f02a4\n"
        ".word 0xe5900000\n"
        ".word 0xeb0364a3\n"
        ".word 0xeef07a48\n"
        ".word 0xeeb06a68\n"
        ".word 0xe284a0c0\n"
        ".word 0xe3e03000\n"
        ".word 0xe1a02003\n"
        ".word 0xedcd7a03\n"
        ".word 0xedcd7a02\n"
        ".word 0xed8d6a01\n"
        ".word 0xedcd7a00\n"
        ".word 0xeeb07a46\n"
        ".word 0xec9a0a0c\n"
        ".word 0xeef06a46\n"
        ".word 0xe1a01003\n"
        ".word 0xe1a00003\n"
        ".word 0xeb03468d\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffffce\n"
        ".word 0xe5db002a\n"
        ".word 0xe3500000\n"
        ".word 0x0a0000db\n"
        ".word 0xeaffff9c\n"
        ".word 0xe5db002a\n"
        ".word 0xe3500000\n"
        ".word 0x0a0000d7\n"
        ".word 0xeaffffc6\n"
        ".word 0xe5940014\n"
        ".word 0xe3500025\n"
        ".word 0x13500026\n"
        ".word 0x0affff94\n"
        ".word 0xe51f0328\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe590a000\n"
        ".word 0xe3a00006\n"
        ".word 0xeb037519\n"
        ".word 0xe28aaa01\n"
        ".word 0xe28aafab\n"
        ".word 0xe59a1000\n"
        ".word 0xe08a2101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5da2018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe59a101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5ca0018\n"
        ".word 0xe51f0380\n"
        ".word 0xe51fa37c\n"
        ".word 0xe5900004\n"
        ".word 0xe5901088\n"
        ".word 0xe59a0000\n"
        ".word 0xeb03646b\n"
        ".word 0xeef07a48\n"
        ".word 0xeeb06a68\n"
        ".word 0xe284ce15\n"
        ".word 0xedcd7a03\n"
        ".word 0xedcd7a02\n"
        ".word 0xed8d6a01\n"
        ".word 0xedcd7a00\n"
        ".word 0xe5940080\n"
        ".word 0xeeb07a46\n"
        ".word 0xec9c0a0c\n"
        ".word 0xeef06a46\n"
        ".word 0xe1a03000\n"
        ".word 0xe1a02000\n"
        ".word 0xe1a01000\n"
        ".word 0xeb034655\n"
        ".word 0xe59aa000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe3a00006\n"
        ".word 0xeb0374f1\n"
        ".word 0xe28aaa01\n"
        ".word 0xe28aafab\n"
        ".word 0xe59a1000\n"
        ".word 0xe08a2101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5da2018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0affff5c\n"
        ".word 0xe59a101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5ca0018\n"
        ".word 0xeaffff57\n"
        ".word 0xe5db002a\n"
        ".word 0xe3500000\n"
        ".word 0x05db0029\n"
        ".word 0x03500000\n"
        ".word 0x0a000090\n"
        ".word 0xe5940014\n"
        ".word 0xe3500025\n"
        ".word 0x13500026\n"
        ".word 0x0a00003b\n"
        ".word 0xe51f0440\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe590a000\n"
        ".word 0xe3a00006\n"
        ".word 0xeb0374d3\n"
        ".word 0xe28aaa01\n"
        ".word 0xe28aafab\n"
        ".word 0xe59a1000\n"
        ".word 0xe08a2101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5da2018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe59a101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5ca0018\n"
        ".word 0xe51f0498\n"
        ".word 0xe51fa494\n"
        ".word 0xe5900004\n"
        ".word 0xe5901088\n"
        ".word 0xe59a0000\n"
        ".word 0xeb036425\n"
        ".word 0xeef07a48\n"
        ".word 0xeeb06a68\n"
        ".word 0xe284ce15\n"
        ".word 0xedcd7a03\n"
        ".word 0xedcd7a02\n"
        ".word 0xed8d6a01\n"
        ".word 0xedcd7a00\n"
        ".word 0xe5940080\n"
        ".word 0xeeb07a46\n"
        ".word 0xec9c0a0c\n"
        ".word 0xeef06a46\n"
        ".word 0xe1a03000\n"
        ".word 0xe1a02000\n"
        ".word 0xe1a01000\n"
        ".word 0xeb03460f\n"
        ".word 0xe59aa000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe3a00006\n"
        ".word 0xeb0374ab\n"
        ".word 0xe28aaa01\n"
        ".word 0xe28aafab\n"
        ".word 0xe59a1000\n"
        ".word 0xe08a2101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5da2018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe59a101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5ca0018\n"
        ".word 0xe5db002a\n"
        ".word 0xe3500000\n"
        ".word 0x0a00004d\n"
        ".word 0xe594118c\n"
        ".word 0xe3510000\n"
        ".word 0x15940180\n"
        ".word 0x11500009\n"
        ".word 0xdaffff38\n"
        ".word 0xeaffff24\n"
        ".word 0xe5db002a\n"
        ".word 0xe3500000\n"
        ".word 0x05db0029\n"
        ".word 0x03500000\n"
        ".word 0x0a000042\n"
        ".word 0xe5940014\n"
        ".word 0xe3500025\n"
        ".word 0x13500026\n"
        ".word 0x0a00003b\n"
        ".word 0xe51f0578\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe590a000\n"
        ".word 0xe3a00006\n"
        ".word 0xeb037485\n"
        ".word 0xe28aaa01\n"
        ".word 0xe28aafab\n"
        ".word 0xe59a1000\n"
        ".word 0xe08a2101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5da2018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe59a101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5ca0018\n"
        ".word 0xe51f05d0\n"
        ".word 0xe51fa5cc\n"
        ".word 0xe5900004\n"
        ".word 0xe5901088\n"
        ".word 0xe59a0000\n"
        ".word 0xeb0363d7\n"
        ".word 0xeef07a48\n"
        ".word 0xeeb06a68\n"
        ".word 0xe284ce15\n"
        ".word 0xedcd7a03\n"
        ".word 0xedcd7a02\n"
        ".word 0xed8d6a01\n"
        ".word 0xedcd7a00\n"
        ".word 0xe5940080\n"
        ".word 0xeeb07a46\n"
        ".word 0xec9c0a0c\n"
        ".word 0xeef06a46\n"
        ".word 0xe1a03000\n"
        ".word 0xe1a02000\n"
        ".word 0xe1a01000\n"
        ".word 0xeb0345c1\n"
        ".word 0xe59aa000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe3a00006\n"
        ".word 0xeb03745d\n"
        ".word 0xe28aaa01\n"
        ".word 0xe28aafab\n"
        ".word 0xe59a1000\n"
        ".word 0xe08a2101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5da2018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe59a101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5ca0018\n"
        ".word 0xe5db002a\n"
        ".word 0xe3500000\n"
        ".word 0x1afffeef\n"
        ".word 0xe2855001\n"
        ".word 0xe1550008\n"
        ".word 0xbafffe13\n"
        ".word 0xe51f7680\n"
        ".word 0xe5970000\n"
        ".word 0xe2805a01\n"
        ".word 0xe2855f93\n"
        ".word 0xe5950000\n"
        ".word 0xe2401001\n"
        ".word 0xe0852100\n"
        ".word 0xe5920008\n"
        ".word 0xe5851000\n"
        ".word 0xe0851101\n"
        ".word 0xe5912008\n"
        ".word 0xe5d51018\n"
        ".word 0xe3510000\n"
        ".word 0x01500002\n"
        ".word 0x0a000004\n"
        ".word 0xe595101c\n"
        ".word 0xe1a00002\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c50018\n"
        ".word 0xe5975000\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a00005\n"
        ".word 0xeb037427\n"
        ".word 0xe2855a01\n"
        ".word 0xe2855f93\n"
        ".word 0xe5951000\n"
        ".word 0xe2812001\n"
        ".word 0xe0853101\n"
        ".word 0xe5931008\n"
        ".word 0xe0853102\n"
        ".word 0xe5852000\n"
        ".word 0xe5830008\n"
        ".word 0xe5d52018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe595101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c50018\n"
        ".word 0xe5db0029\n"
        ".word 0xe3500000\n"
        ".word 0x15db002a\n"
        ".word 0x13500000\n"
        ".word 0x0a000121\n"
        ".word 0xe5d60016\n"
        ".word 0xe3500000\n"
        ".word 0x0a000041\n"
        ".word 0xe51f5750\n"
        ".word 0xe5d50018\n"
        ".word 0xe3500000\n"
        ".word 0x1a00003d\n"
        ".word 0xe3a00002\n"
        ".word 0xe586004c\n"
        ".word 0xe59f032c\n"
        ".word 0xe59621cc\n"
        ".word 0xeddf0ac7\n"
        ".word 0xe2863098\n"
        ".word 0xe5901000\n"
        ".word 0xe0620182\n"
        ".word 0xe286403c\n"
        ".word 0xe0810180\n"
        ".word 0xe280101c\n"
        ".word 0xe5900024\n"
        ".word 0xe8910006\n"
        ".word 0xed9f0abf\n"
        ".word 0xeddf1ac1\n"
        ".word 0xee012a10\n"
        ".word 0xe8830006\n"
        ".word 0xe28630a0\n"
        ".word 0xe8830007\n"
        ".word 0xee710a20\n"
        ".word 0xe58600ac\n"
        ".word 0xed9f1ab9\n"
        ".word 0xe1a00004\n"
        ".word 0xedc40a1b\n"
        ".word 0xed840a23\n"
        ".word 0xed848a60\n"
        ".word 0xeddf0ab6\n"
        ".word 0xed9f0ab6\n"
        ".word 0xeb01c51b\n"
        ".word 0xe5940180\n"
        ".word 0xe1590000\n"
        ".word 0xaa00001d\n"
        ".word 0xe5950000\n"
        ".word 0xe3500064\n"
        ".word 0xe51f07e4\n"
        ".word 0xe5900004\n"
        ".word 0xaa000005\n"
        ".word 0xe5901020\n"
        ".word 0xe5970000\n"
        ".word 0xeb036352\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000002\n"
        ".word 0xe5901074\n"
        ".word 0xe5970000\n"
        ".word 0xeb03634c\n"
        ".word 0xeef07a48\n"
        ".word 0xeeb06a68\n"
        ".word 0xe28450c0\n"
        ".word 0xe3e03000\n"
        ".word 0xe1a02003\n"
        ".word 0xedcd7a03\n"
        ".word 0xe5940180\n"
        ".word 0xeeb07a46\n"
        ".word 0xeef06a46\n"
        ".word 0xe58d0008\n"
        ".word 0xed8d6a01\n"
        ".word 0xe58d0000\n"
        ".word 0xe1a01003\n"
        ".word 0xec950a0c\n"
        ".word 0xe1a00003\n"
        ".word 0xeb034535\n"
        ".word 0xe5d60020\n"
        ".word 0xe3500000\n"
        ".word 0x0a0000d3\n"
        ".word 0xe51f0864\n"
        ".word 0xe5d00018\n"
        ".word 0xe3500000\n"
        ".word 0x1a0000cf\n"
        ".word 0xe5940014\n"
        ".word 0xe3500022\n"
        ".word 0xaa0000cc\n"
        ".word 0xe51f087c\n"
        ".word 0xe5900004\n"
        ".word 0xe5901018\n"
        ".word 0xe5970000\n"
        ".word 0xeb03632d\n"
        ".word 0xedd69a0b\n"
        ".word 0xe2866024\n"
        ".word 0xeeb09a68\n"
        ".word 0xec96aa02\n"
        ".word 0xed9fba81\n"
        ".word 0xeb04293c\n"
        ".word 0xedd40a1d\n"
        ".word 0xee7aaa8b\n"
        ".word 0xe59f01fc\n"
        ".word 0xee300a20\n"
        ".word 0xeddf0a7c\n"
        ".word 0xe3a06000\n"
        ".word 0xe3a0c000\n"
        ".word 0xe1a04006\n"
        ".word 0xe1a0800c\n"
        ".word 0xee200a20\n"
        ".word 0xeeb40ae8\n"
        ".word 0xeef1fa10\n"
        ".word 0xeeb0ba68\n"
        ".word 0xeef00ac0\n"
        ".word 0x33a05001\n"
        ".word 0x23a05000\n"
        ".word 0xed9f1a72\n"
        ".word 0xeeb00a4b\n"
        ".word 0xee101a90\n"
        ".word 0xe1510000\n"
        ".word 0xba000003\n"
        ".word 0xee700ac1\n"
        ".word 0xee101a90\n"
        ".word 0xe1510000\n"
        ".word 0xaafffffb\n"
        ".word 0xee101a10\n"
        ".word 0xe1510000\n"
        ".word 0xba000003\n"
        ".word 0xee300a41\n"
        ".word 0xee101a10\n"
        ".word 0xe1510000\n"
        ".word 0xaafffffb\n"
        ".word 0xeebc1ae8\n"
        ".word 0xe59f3188\n"
        ".word 0xe3540000\n"
        ".word 0xee110a10\n"
        ".word 0xeebc1ae0\n"
        ".word 0xe6ff2070\n"
        ".word 0xee110a10\n"
        ".word 0xeebc1ac0\n"
        ".word 0xe6ff1070\n"
        ".word 0xee011a90\n"
        ".word 0xe20110ff\n"
        ".word 0xe0831201\n"
        ".word 0xee110a10\n"
        ".word 0xee012a10\n"
        ".word 0xeef81a61\n"
        ".word 0xe20220ff\n"
        ".word 0xe6ff0070\n"
        ".word 0xee020a10\n"
        ".word 0xe20000ff\n"
        ".word 0xeeb81a41\n"
        ".word 0xe0832202\n"
        ".word 0xe0830200\n"
        ".word 0xed923a00\n"
        ".word 0xeef82a42\n"
        ".word 0xee701ae1\n"
        ".word 0xedd10a01\n"
        ".word 0xedd04a00\n"
        ".word 0xed924a02\n"
        ".word 0xedd03a01\n"
        ".word 0xee382ac1\n"
        ".word 0xe2800008\n"
        ".word 0xed921a01\n"
        ".word 0xed925a03\n"
        ".word 0xee702a62\n"
        ".word 0xed910a00\n"
        ".word 0xe2811008\n"
        ".word 0xecd06a02\n"
        ".word 0xe28d0018\n"
        ".word 0xecd15a02\n"
        ".word 0xee023a04\n"
        ".word 0xee021a05\n"
        ".word 0xee010aa5\n"
        ".word 0xee424aa6\n"
        ".word 0xee423a87\n"
        ".word 0xee410a86\n"
        ".word 0x1eb13a43\n"
        ".word 0xe3550000\n"
        ".word 0x1eb10a40\n"
        ".word 0xe35c0000\n"
        ".word 0x1ef14a64\n"
        ".word 0xee632a23\n"
        ".word 0xee214a23\n"
        ".word 0xee635aa0\n"
        ".word 0xeef16a40\n"
        ".word 0xee611a24\n"
        ".word 0xee232a24\n"
        ".word 0xee643aa0\n"
        ".word 0xee233a20\n"
        ".word 0xee610a20\n"
        ".word 0xeeb06a61\n"
        ".word 0xeeb05a42\n"
        ".word 0xed8d3a0b\n"
        ".word 0xedcd0a0c\n"
        ".word 0xee126a80\n"
        ".word 0xee512a80\n"
        ".word 0xee045a00\n"
        ".word 0xee024a00\n"
        ".word 0xedcd2a08\n"
        ".word 0xed8d5a04\n"
        ".word 0xedcd6a0a\n"
        ".word 0xecc03a02\n"
        ".word 0xe28d0008\n"
        ".word 0xecc05a02\n"
        ".word 0xe58d8014\n"
        ".word 0xe58d8024\n"
        ".word 0xe58d8034\n"
        ".word 0xe59f8060\n"
        ".word 0xe3a04000\n"
        ".word 0xe2865003\n"
        ".word 0xe2489ec6\n"
        ".word 0xe289be63\n"
        ".word 0xe28baec6\n"
        ".word 0xe3550005\n"
        ".word 0x379ff105\n"
        ".word 0xea000029\n"
        ".word 0x001e92b8\n"
        ".word 0x001e92dc\n"
        ".word 0x001e92b8\n"
        ".word 0x001e92dc\n"
        ".word 0x001e92f8\n"
        ".word 0x43fa0000\n"
        ".word 0xc3b40000\n"
        ".word 0x00447e58\n"
        ".word 0xc40e8000\n"
        ".word 0xc2280000\n"
        ".word 0x43a80000\n"
        ".word 0x44a80000\n"
        ".word 0x43020000\n"
        ".word 0x3f360b61\n"
        ".word 0x47800000\n"
        ".word 0x47800000\n"
        ".word 0x00407fc0\n"
        ".word 0x004b6990\n"
        ".word 0xe0840084\n"
        ".word 0xe0880100\n"
        ".word 0xe5901004\n"
        ".word 0xe5902000\n"
        ".word 0xe5900008\n"
        ".word 0xe58d1044\n"
        ".word 0xe58d2040\n"
        ".word 0xe58d0048\n"
        ".word 0xea00000e\n"
        ".word 0xe0840084\n"
        ".word 0xe0891100\n"
        ".word 0xe5912000\n"
        ".word 0xe1c100d4\n"
        ".word 0xe58d2040\n"
        ".word 0xe1cd04f4\n"
        ".word 0xea000007\n"
        ".word 0xe0840084\n"
        ".word 0xe08b0100\n"
        ".word 0xe5901004\n"
        ".word 0xe5902000\n"
        ".word 0xe5900008\n"
        ".word 0xe58d1044\n"
        ".word 0xe58d2040\n"
        ".word 0xe58d0048\n"
        ".word 0xed9d0a12\n"
        ".word 0xe0840084\n"
        ".word 0xe28d2040\n"
        ".word 0xee300a09\n"
        ".word 0xe08a0100\n"
        ".word 0xe1a06000\n"
        ".word 0xe28d1008\n"
        ".word 0xed8d0a12\n"
        ".word 0xeb0310e6\n"
        ".word 0xed960a00\n"
        ".word 0xe2844001\n"
        ".word 0xe3540004\n"
        ".word 0xee300a0a\n"
        ".word 0xed860a00\n"
        ".word 0xed960a01\n"
        ".word 0xee300a2a\n"
        ".word 0xed860a01\n"
        ".word 0xed960a02\n"
        ".word 0xee300a29\n"
        ".word 0xed860a02\n"
        ".word 0xbaffffbd\n"
        ".word 0xeef07a48\n"
        ".word 0xeeb06a4b\n"
        ".word 0xe3e03000\n"
        ".word 0xe1a02003\n"
        ".word 0xe1a01003\n"
        ".word 0xedcd7a03\n"
        ".word 0xedcd7a02\n"
        ".word 0xed8d6a01\n"
        ".word 0xedcd7a00\n"
        ".word 0xeeb07a46\n"
        ".word 0xec9a0a0c\n"
        ".word 0xeef06a46\n"
        ".word 0xe1a00003\n"
        ".word 0xeb03445e\n"
        ".word 0xe3a01005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb01c3f1\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1b009869\n"
        ".word 0xe5970000\n"
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
        ".word 0x0a000003\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c40018\n"
        ".word 0xe28dde4a\n"
        ".word 0xe3a00000\n"
        ".word 0xecbd8b08\n"
        ".word 0xe8bd9ff0\n"
        ".word 0xe59f00f4\n"
        ".word 0xe92d4070\n"
        ".word 0xe5900000\n"
        ".word 0xe5900024\n"
        ".word 0xe3500015\n"
        ".word 0xba000036\n"
        ".word 0xe350006e\n"
        ".word 0xaa000034\n"
        ".word 0xe2401054\n"
        ".word 0xe351000b\n"
        ".word 0x9a000031\n"
        ".word 0xe3500018\n"
        ".word 0x0a00002f\n"
        ".word 0xe59f50c4\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a00005\n"
        ".word 0xe5954000\n"
        ".word 0xeb0372c7\n"
        ".word 0xe2844a01\n"
        ".word 0xe2844f93\n"
        ".word 0xe3a06000\n"
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
        ".word 0xe5c46018\n"
        ".word 0xe320f000\n"
        ".word 0xeb004285\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xebff2a3c\n"
        ".word 0xe5950000\n"
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
        ".word 0xe5c46018\n"
        ".word 0xe320f000\n"
        ".word 0xebff2b4d\n"
        ".word 0xe3a00000\n"
        ".word 0xe8bd8070\n"
        ".word 0xe3a00000\n"
        ".word 0xe8bd8070\n"
        ".word 0x00447e28\n"
        ".word 0x0044ea00\n"
    );
}
#if 0
// Original partial readable draft retained for reconstruction; not compiled.
void ui_func_001e83fc() {
    UiWindowState* const win = &UiWindowSlot();
    TalkWork* const work = TalkWorkSlot();
    TalkCamera* const cam = TalkCameraSlot();
    if (win->enabled_380 == 0) {                          // 0x001E840C
        return;
    }
    if (win->field_22 != 0 || win->field_24 != 0) {        // 0x001E8420
        return;
    }
    if (cam->mode_00 == 3) {                              // 0x001E8440
        return;
    }

    // 0x001E844C..0x001E84A4: push viewport mode 5/0 onto ring slot 0x24C.
    GpuModeSlotPush(0x24C,
                   reinterpret_cast<u32>(UiGpu_SetViewportParams(5, 0)));

    s32 order[0x80] = {};                                  // [sp+0x88]
    f32 sort_key[0x80] = {};                               // [sp+0x288]
    s32 visible = 0;                                       // r8

    // ---- collection loop (0x001E84B4..0x001E8638) -------------------------
    for (s32 i = 0; i < 0x80; ++i) {
        TalkTargetEntry* const e =
            reinterpret_cast<TalkTargetEntry*>(
                reinterpret_cast<u8*>(work) + 0x1D0 + i * kTalkEntryStride);
        if (e->active_000 == 0 || e->kind_00c == 0 ||
            e->flag_042 == 0) {                            // 0x001E84CC..0x001E84E4
            continue;
        }

        bool include = true;
        switch (e->kind_00c) {
        case 0:
            include = false;
            break;
        case 6:
        case 8:
        case 10:
        case 12:
        case 14:
        case 15:
            include = g_TalkOverlayFlags.field_2a != 0;    // 0x001E852C
            break;
        case 17:
        case 18:
            include = (g_TalkOverlayFlags.field_2a != 0 ||
                       g_TalkOverlayFlags.field_29 != 0);  // 0x001E8574
            break;
        default:
            break;
        }
        if (!include) {
            continue;
        }

        // 0x001E8588..0x001E85DC: average of the four matrix columns.
        const f32* const m = e->matrix_090;
        const f32 px = (m[0] + m[3] + m[6] + m[9]) * 0.25f;
        const f32 py = (m[1] + m[4] + m[7] + m[10]) * 0.25f;
        const f32 pz = (m[2] + m[5] + m[8] + m[11]) * 0.25f;
        const f32 dist = Distance3(cam->pos_4c[0], cam->pos_4c[1],
                                   cam->pos_4c[2], px, py, pz);

        // 0x001E85E8..0x001E8638: special types require distance >= 210,
        // all others distance >= 200 (signed bit-pattern compares).
        bool keep;
        switch (e->type_014) {
        case 1:
        case 2:
        case 3:
        case 4:
        case 5:
        case 7:
            keep = !(dist < 210.0f);                       // 0x001E873C
            break;
        default:
            keep = !(200.0f > dist);                       // 0x001E8610
            break;
        }
        if (!keep) {
            continue;
        }
        order[visible] = i;
        sort_key[visible] = dist;
        ++visible;
    }

    // ---- descending selection sort on the distance keys -------------------
    // 0x001E863C..0x001E86B0: ip stays at key[i] while r1 walks key[j]; the
    // swap executes when key[i] < key[j] (`vcmpe` + `bhs`).
    for (s32 i = 0; i < visible - 1; ++i) {
        for (s32 j = i; j < visible; ++j) {
            if (sort_key[i] < sort_key[j]) {
                const s32 tmp_i = order[i];
                order[i] = order[j];
                order[j] = tmp_i;
                const f32 tmp_f = sort_key[i];
                sort_key[i] = sort_key[j];
                sort_key[j] = tmp_f;
            }
        }
    }

    TalkRenderer* const rend = work->renderer_04;

    // ---- render loop (0x001E86C0..0x001E8E78) -----------------------------
    for (s32 vi = 0; vi < visible; ++vi) {
        TalkTargetEntry* const e =
            reinterpret_cast<TalkTargetEntry*>(
                reinterpret_cast<u8*>(work) + 0x1D0 +
                order[vi] * kTalkEntryStride);
        switch (e->kind_00c) {
        case 1: {
            // 0x001E874C..0x001E8914
            TalkSetModel(rend->handle_60);
            // 0x001E8764..0x001E8780: signed quarter-phase.
            s32 q = e->frame_028;
            q += static_cast<u32>(q) >> 31;
            q >>= 1;
            s32 qmod = q >> 31;
            qmod = q + (static_cast<u32>(qmod) >> 30);
            qmod &= ~3;
            q -= qmod;
            f32 ox = 0.0f;
            f32 oy = 0.0f;
            if (q == 1) {
                oy = 0.25f;
            } else if (q == 2) {
                oy = 0.5f;
            } else if (q == 3) {
                oy = 0.75f;
            }
            // 0x001E87BC..0x001E87F0: mvn r3,#0 then r2=r1=r0=r3, so all four
            // handle registers are 0xFFFFFFFF; matrix_090 is loaded at sl.
            TalkDrawQuad(0xFFFFFFFFu, 0xFFFFFFFFu, 0xFFFFFFFFu,
                         0xFFFFFFFFu, e->matrix_090,
                         ox, oy, ox, oy + 0.25f,
                         ox + 1.0f, oy, ox + 1.0f, oy + 0.25f);
            if (e->handle_084 != 0) {
                TalkDrawQuad(e->handle_084, e->handle_084, e->handle_084,
                             e->handle_084, e->matrix_0f0,
                             0.0f, 0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f, 1.0f);
            }
            if (e->handle_088 != 0) {
                TalkDrawQuad(e->handle_088, e->handle_088, e->handle_088,
                             e->handle_088, e->matrix_120,
                             0.0f, 0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f, 1.0f);
            }
            TalkSetModel(e->handle_184);                   // 0x001E88CC
            TalkDrawMain(e);
            break;
        }
        case 2: {
            // 0x001E882C..0x001E88CC
            TalkSetModel(rend->handle_68);
            if (e->handle_084 != 0) {
                TalkDrawQuad(e->handle_084, e->handle_084, e->handle_084,
                             e->handle_084, e->matrix_0f0,
                             0.0f, 0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f, 1.0f);
            }
            if (e->handle_088 != 0) {
                TalkDrawQuad(e->handle_088, e->handle_088, e->handle_088,
                             e->handle_088, e->matrix_120,
                             0.0f, 0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f, 1.0f);
            }
            TalkSetModel(e->handle_184);
            TalkDrawMain(e);
            break;
        }
        case 3:
            // 0x001E8918..0x001E896C
            TalkSetModel(rend->handle_4c);
            TalkDrawMain(e);
            break;
        case 4:
        case 13:
            // 0x001E8978..0x001E89CC
            TalkSetModel(e->handle_184);
            TalkDrawMain(e);
            break;
        case 5:
        case 7:
        case 9:
        case 11:
            // 0x001E89D0..0x001E8A84
            if (e->flag_18c != 0 &&
                static_cast<s32>(e->handle_180) > static_cast<s32>(0x3C23D70Au)) {
                TalkSetModel(e->flag_18c);
                TalkDrawMarker(e);
            }
            TalkDrawSecondary(e, rend);
            break;
        case 6:
        case 8:
        case 10:
        case 12: {
            // 0x001E8A88..0x001E8AF0
            if (g_TalkOverlayFlags.field_2a == 0) {
                break;
            }
            if (e->flag_18c != 0) {
                TalkSetModel(e->flag_18c);
                TalkDrawQuad(0xFFFFFFFFu, 0xFFFFFFFFu, 0xFFFFFFFFu,
                             0xFFFFFFFFu, e->matrix_0c0,
                             0.0f, 0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f, 1.0f);
            }
            TalkDrawSecondary(e, rend);
            break;
        }
        case 14:
            // 0x001E8AF4: gated on flag 0x2A, then the case-4 draw.
            if (g_TalkOverlayFlags.field_2a != 0) {
                TalkSetModel(e->handle_184);
                TalkDrawMain(e);
            }
            break;
        case 15:
            // 0x001E8B04: gated on flag 0x2A, then the secondary draw.
            if (g_TalkOverlayFlags.field_2a != 0) {
                TalkDrawSecondary(e, rend);
            }
            break;
        case 16:
            // 0x001E8B14..0x001E8C14
            if (e->type_014 == 0x25 || e->type_014 == 0x26) {
                TalkSetModel(e->handle_184);
                TalkDrawMain(e);
                break;
            }
            GpuModeSlotSet(0x2AC, reinterpret_cast<u32>(
                UiGpu_SetRenderMode(6, 1, 0)));
            TalkSetModel(rend->handle_88);
            TalkDrawQuad(e->handle_080, e->handle_080, e->handle_080,
                         e->handle_080, e->matrix_150,
                         0.0f, 0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f, 1.0f);
            GpuModeSlotSet(0x2AC, reinterpret_cast<u32>(
                UiGpu_SetRenderMode(6, 7, 0)));
            TalkSetModel(e->handle_184);
            TalkDrawMain(e);
            break;
        case 17: {
            // 0x001E8C18..0x001E8D4C
            if (g_TalkOverlayFlags.field_2a == 0 &&
                g_TalkOverlayFlags.field_29 == 0) {
                break;
            }
            if (e->type_014 != 0x25 && e->type_014 != 0x26) {
                GpuModeSlotSet(0x2AC, reinterpret_cast<u32>(
                    UiGpu_SetRenderMode(6, 1, 0)));
                TalkSetModel(rend->handle_88);
                TalkDrawQuad(e->handle_080, e->handle_080, e->handle_080,
                             e->handle_080, e->matrix_150,
                             0.0f, 0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f, 1.0f);
                GpuModeSlotSet(0x2AC, reinterpret_cast<u32>(
                    UiGpu_SetRenderMode(6, 7, 0)));
            }
            if (g_TalkOverlayFlags.field_2a == 0) {
                break;
            }
            if (e->flag_18c != 0 &&
                static_cast<s32>(e->handle_180) >
                    static_cast<s32>(0x3C23D70Au)) {
                TalkSetModel(e->flag_18c);
                TalkDrawMarker(e);
            } else {
                TalkDrawSecondary(e, rend);
            }
            break;
        }
        case 18: {
            // 0x001E8D50..0x001E8E6C
            if (g_TalkOverlayFlags.field_2a == 0 &&
                g_TalkOverlayFlags.field_29 == 0) {
                break;
            }
            if (e->type_014 != 0x25 && e->type_014 != 0x26) {
                GpuModeSlotSet(0x2AC, reinterpret_cast<u32>(
                    UiGpu_SetRenderMode(6, 1, 0)));
                TalkSetModel(rend->handle_88);
                TalkDrawQuad(e->handle_080, e->handle_080, e->handle_080,
                             e->handle_080, e->matrix_150,
                             0.0f, 0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f, 1.0f);
                GpuModeSlotSet(0x2AC, reinterpret_cast<u32>(
                    UiGpu_SetRenderMode(6, 7, 0)));
            }
            if (g_TalkOverlayFlags.field_2a != 0) {
                TalkDrawSecondary(e, rend);
            }
            break;
        }
        default:
            break;
        }
    }

    // ---- pop/push viewport mode (0x001E8E7C..0x001E8F20) ------------------
    GpuModeSlotPop(0x24C);
    GpuModeSlotPush(0x24C,
                   reinterpret_cast<u32>(UiGpu_SetViewportParams(5, 0)));

    if (g_TalkOverlayFlags.field_29 != 0 &&
        g_TalkOverlayFlags.field_2a != 0) {
        if (work->field_16 != 0 && win->busy_18 == 0) {
            // 0x001E8F40..0x001E8FC4: seed the detail-card header from the
            // selected 56-byte animation row.
            work->mode_4c = 2;
            // 0x00447E58 holds the observed 0x004BB7B0 pointer.  Keep the
            // defensive zero-row fallback for tests that clear the global.
            static const TalkAnimRow kZeroAnimRow{};
            const TalkAnimRow* const row = g_TalkAnimRows
                ? &g_TalkAnimRows[work->selected_1cc] : &kZeroAnimRow;
            work->field_98[0] = row->field_1c;
            work->field_98[1] = row->field_20;
            work->field_a0[0] = row->field_24;
            work->field_a0[1] = *reinterpret_cast<const u32*>(&row->field_1c);
            work->field_a0[2] = *reinterpret_cast<const u32*>(&row->field_20);
            work->field_ac = row->field_24;
            *F32At(work, 0xA8) = row->field_20 + 500.0f;   // 0x001E8F9C
            *F32At(work, 0xC8) = -360.0f;                  // 0xC3B40000
            *F32At(work, 0x1BC) = 1.0f;                    // 0x001E8FB4
            // 0x001E8FB8 loads s1 with 0x43A80000 (336.0f) and 0x001E8FBC
            // loads s0 with 0x44A80000 (1344.0f).  The register order is
            // therefore (s0,s1,s2,s3) = (1344, 336, -570, -42), which is what
            // 0x0025A434 consumes at 0x0025A450..0x0025A45C.
            UiSpriteStack_Build(work->field_3c, 1344.0f, 336.0f,
                                -570.0f, -42.0f);          // 0x001E8FC0

            // Dead-at-runtime guard kept verbatim: `cmp sb,r0` compares the
            // 0x3C23D70A constant (1.0e9 as an integer) with the 1.0f word.
            if (static_cast<s32>(0x3C23D70Au) <
                static_cast<s32>(*reinterpret_cast<const u32*>(&work->field_1bc))) {
                const u32 window_word =
                    *reinterpret_cast<const u32*>(&UiWindowSlot());
                const u32 model = (window_word < 0x64)
                                      ? rend->handle_20 : rend->handle_74;
                TalkSetModel(model);
                TalkDrawQuad(0xFFFFFFFFu, 0xFFFFFFFFu, 0xFFFFFFFFu,
                             0xFFFFFFFFu, F32At(work, 0xFC),
                             0.0f, 0.0f, 0.0f, 1.0f,
                             static_cast<f32>(work->field_1bc), 0.0f,
                             static_cast<f32>(work->field_1bc), 1.0f);
            }
        }

        if (work->field_20 != 0 && win->busy_18 == 0 &&
            *I32At(work, 0x50) < 0x22) {
            TalkDrawDetailRing(work, rend, 0, 0);          // 0x001E9048..0x001E93A4
        }

        // 0x001E93A4..0x001E93B8 is only reached when both flags survive the
        // 0x001E8F20/0x001E8F30 gate; the zero-flag path jumps to 0x001E93BC.
        if (Camp_CheckTransfer(2, 5)) {
            Battle_ClearTargets();
        }
    }

    GpuModeSlotPop(0x24C);                                 // 0x001E93BC
}
#endif

/** Second routine inside the 0x001E83FC ledger span (0x001E9414..0x001E9518).
 *  It gates on the word at `[0x00447E28]+0x24`, pushes viewport mode 5/0,
 *  runs the two 0x1F9EC0/0x1B3DA8 updates, pops the mode, then calls
 *  0x1B4238.  The three exclusion ranges are:
 *    value < 0x15, value >= 0x6E, (value-0x54) <= 0xB, value == 0x18.
 *  (0x001E9414..0x001E9508). */
s32 TalkOverlay_PollMode() {
    // 0x00447E28 is the canonical engine::g_MapMainWork pointer slot.
    const u8* const guard =
        reinterpret_cast<const u8*>(engine::g_MapMainWork);
    const s32 value = *reinterpret_cast<const s32*>(guard + 0x24);
    if (value < 0x15 || value >= 0x6E ||
        static_cast<u32>(value - 0x54) <= 0x0Bu || value == 0x18) {
        return 0;
    }
    GpuModeSlotPush(0x24C,
                   reinterpret_cast<u32>(UiGpu_SetViewportParams(5, 0)));
    TalkMode_UpdateA();                                    // 0x001E94A4
    TalkMode_UpdateB();                                    // 0x001E94B0
    GpuModeSlotPop(0x24C);                                 // 0x001E94B4
    TalkMode_UpdateC();                                    // 0x001E94FC
    return 0;
}

} // namespace smt4::ui
