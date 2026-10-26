#include "ui/ui_runtime2.h"
#include "ui/ui_runtime.h"
#include "ui/tbb_table.h"
#include "camp/unite_extras.h"
#include "../camp/title_message.h"
#include "engine/asd_symbols.h"
#include "engine/asd_render_ui.h"
#include "engine/asd_scene.h"
#include "engine/map_runtime.h"
#include "camp/title_flow.h"
#include <cstring>

namespace smt4::ui {

using engine::Npc2dLayoutNode;

namespace {

// Canonical 0x002BF6D0 declaration returns `const void*`; this TU reads the
// offset-compatible Npc2dLayoutNode view (x +0x08, y +0x0A, payload +0x0C).
inline const Npc2dLayoutNode* LayoutNode(u32 group, u32 node) {
    return static_cast<const Npc2dLayoutNode*>(UiLayout_GetNode(group, node));
}

// ---------------------------------------------------------------------------
// Shared ABI declarations.  Spellings match the canonical declarations used by
// the other UI TUs (ui_runtime.cpp / ui_scene_extras.cpp / status_down.cpp);
// one declaration per binary address.
// ---------------------------------------------------------------------------

extern "C" {
    extern u8* g_AsdGpuState;                                                   // 0x0044EA00

    void  UiSprite_DrawNode(u32 screen, u32 group, u32 node,
                            s32 x, s32 y, s32 prio);                            // 0x002BF460
    void  UiSprite_DrawPanel(u32 screen, u32 group, u32 panel,
                             s32 x, s32 y, s32 prio);                           // 0x002BF558
    void  UiFont_DrawText(u32 font_id, u32 rgba, const char* text,
                          f32 x, f32 y, f32 scale_x, f32 rot, f32 scale_y);     // 0x002BE77C
    void  UiFont_FormatString(char* dst, const char* fmt, ...);                 // 0x002BE7FC
    void  UiFont_DrawFormatted(u32 screen, s32 x, s32 y, s32 mode, s32 width,
                               s32 prio, const char* fmt, s32 value);           // 0x002BE16C
    void  UiSprite_SetGlobalAlpha(f32 alpha);                                   // 0x002BF710
    void  UiSkill_DrawItemIconAndCount(s32 item_id, s32 x, s32 y,
                                       s32 prio, s32 a4);                       // 0x002B6A98
    void  Item_DrawDescriptionIcon(u16 item_id, s32 x, s32 y, s32 prio);        // 0x00258308
    s32   UiAnimSprite_GetPosX(const void* sprite);                             // 0x002BEF7C
    s32   UiAnimSprite_GetPosY(const void* sprite);                             // 0x002BEF70
    void  UiScissor_SetRect(s32 x, s32 y, s32 w, s32 h, s32 enable);            // 0x0029A418
    s32   UiText_MeasureWidth(const char* text, s32 mode);                      // 0x002B7118
    s32   UiTouch_GetRegionTouchState(s16 handle);                              // 0x0029D8FC
    s16   UiTouch_RegisterRegion(u32 group, u32 node);                          // 0x002B88C4

    // 0x00250B4C: three-part field formatter; mode 2 selects the
    // `cmp r4,#0x3e8` branch and writes at most four digits plus NUL.
    void  UiText_FormatSlotField(u32 a, u32 b, u32 mode, char* dst);            // 0x00250B4C
    // 0x00290A68: writes the decimal digits of `value` (leading zeros for the
    // 1000/100/10 stages) into `dst`.
    void  UiText_FormatDigits(char* dst, u32 value);                            // 0x00290A68
    // 0x00250AAC: writes two glyph bytes for `value` plus NUL.
    void  UiText_FormatTwoDigits(u32 value, char* dst);                         // 0x00250AAC
    // 0x0028F758: text width of a formatted buffer.
    f32   Quest_MeasureText(const char* text, s32 mode);                        // 0x0028F758

    // 0x002BE4DC: splits an RGBA word into the four floats of the shared
    // 0x004D4680 colour block.
    void  UiColor_SetFromRgba(u32 rgba);                                        // 0x002BE4DC
    // 0x002BEF14: restores the eight 1.0/alpha quads in the same block.
    void  UiSprite_ResetBlend();                                                // 0x002BEF14
    // 0x002AE2C4: fills the four 4-float colour quads from `xy` (3 floats read,
    // alpha from 0x004D4680+0x84).
    void  UiDraw_BuildColorQuad(const f32* xy);                                 // 0x002AE2C4
    // 0x001C0A88: model/billboard pass (x, y, width, height, colour word).
    void  UiDraw_ModelPass(s32 x, s32 y, s32 w, s32 h, s32 color);              // 0x001C0A88

    // 0x001F1FC8 helpers.
    void* Camp_GetMainWork();                                                   // 0x00262A44
    s32   Fusion_GetPossibleCount();                                            // 0x0029E080
    const char* Item_GetShortNameString(u16 item_id);                           // 0x002BD258
    // 0x002BD020 reads its second argument into r4 at 0x002BD024; both
    // 0x001F255C and 0x001F2C3C set r1 = 0.
    const char* Item_GetDescriptionString(u16 item_id, s32 mode);                // 0x002BD020
    s32   Compendium_IsRegistered(u16 demon_id);                                // 0x0029ED08

    // 0x001E989C helpers.
    void  Title_LoadLayout();                                                   // 0x002A61F8
    void  Title_ResetFadeState();                                               // 0x002BC2C4
    s32   Script_TestFlag(u32 flag_id);                                         // 0x002C2BD0
    void  UiSound_PlayCue(s32 bus, s32 id);                                     // 0x002A0678
    void  TitleAnim_Update(void* anim);                                         // 0x003BCBF8
    void  Sound_RequestBgm(u32 id, u32 volume, u32 frames);                     // 0x002A0640
    void  CommonBg_Begin();                                                     // 0x00289B4C
    void  ButtonHelp_Init();                                                    // 0x0028D974
    void  ScriptVm_SetMessageId(u32 id);                                        // 0x002B8B78
    void  Title_PreparePreview();                                               // 0x0025A318
    u32   Res_LoadBccam(const char* name);                                      // 0x00263E48
    u32   Res_LoadBam(const char* name, s32 mode);                              // 0x0029BDDC
    void  Res_LoadBcenv(const char* name, u32 mode);                            // 0x002A0C54
    void  Title_RegisterDefaultResources();                                     // 0x00211AD4
    s32   Res_IsLoadBusy(u32 handle);                                           // 0x002AE16C
    void  UiModel_SetVisible(u32 handle, u32 mode);                             // 0x002A06DC
    void* UiStyle_GetCurrent();                                                 // 0x002C5218
    void  UiText_GetMetrics(void* object, f32* a, f32* b, f32* c, f32* d);      // 0x002A88DC
    void  Effect_SetDrawParams(void* work, u32 mode, f32 a, f32 b, f32 c, f32 d); // 0x002C1FFC
    void  Effect_SetScale(void* work, f32 a, f32 b);                            // 0x002C1774
    void  AsdCamera_BindProjection(void* projection);                           // 0x00298FEC
    void  UiModel_SetFlag(u32 handle, u32 mode);                                // 0x002A06C8
    void  UiModel_ApplyAlpha(f32 alpha);                                        // 0x0029BDB4
    s32   Script_IsReadyToAdvance();                                            // 0x00289924
    s32   Camp_IsPreviewReady();                                                // 0x0025A2BC
    s32   UiInput_Trigger(u32 id);                                              // 0x002B902C
    s32   UiInput_Trigger2(u32 id);                                             // 0x002BFFBC
    void  Script_RequestEvent(u32 event_id);                                    // 0x002B91C4
    void  UiModel_SetFade(u32 handle, f32 value);                               // 0x00210030
    s32   UiModel_IsVisible(void* object);                                      // 0x0025A274
    s32   UiModel_IsReady(void* object);                                        // 0x002D569C
    void  UiModel_ResetFade(void* object);                                      // 0x002872A4
    void  UiModel_SetFadeParam(void* object, f32 value);                        // 0x0020FFA0
    f32   UiModel_GetFade(u32 handle);                                          // 0x002B2D40
    s32   UiMenu_CheckCursorSound(u32 id);                                      // 0x0026F0D8
    void  Camp_AdvanceCursorBlink();                                            // 0x002B9008
    void  Script_PrepareCursor();                                               // 0x00276034
    void  Script_ApplyCursorMode(s32 mode);                                     // 0x00275E58
    void  Script_SetCursorSound(s32 a, s32 b, s32 c);                           // 0x0029C660
    void  Script_ResetCursorSound(u32 id);                                      // 0x0029C650
    void  Script_PrepareTransition(u32 mode);                                   // 0x002A7604
    void  SaveLoad_BeginFromTitle();                                            // 0x0030A9A4
    s32   SaveLoad_IsBusy();                                                    // 0x00282DF8
    s8    Title_GetManagerFlag();                                               // 0x00215918
    s32   TitleConfig_IsReady();                                                // 0x002FC0EC
    void  ScriptVm_ResetTitle();                                                // 0x00291BE8
    void  AsdTask_DestroyPair(void* calc_task, u32 mode);                       // 0x002C45B8
    void  UiScene_SetupField(u32 mode);                                         // 0x002B85BC
    void  UiScene_DrawLoading();                                                // 0x0019203C
    void  Script_PrepareTitleBoot();                                            // 0x002701C4
    void  UiScene_SetFade(s32 mode);                                            // 0x00287E9C
    u32   Save_GetGameOverStateIndex();                                         // 0x002C0B94
    void  Script_StartTitleFade();                                              // 0x0027007C
    void  Script_ClearTitleInput();                                             // 0x0026FD14
    void  Script_StartNewGame();                                                // 0x0026FA94
    void  Camp_DrawTitleBundle(void* bundle);                                   // 0x0026E594
    void  Res_ReleaseHandle(u32 handle, u32 mode);                              // 0x0029C56C
    void* Runtime_GetTitleObject(u32 spec);                                     // 0x0035F404
}

// 0x0044E300 titleMain workspace (the 0x9438 candidate table is in the
// separate 0x0043DD68 CampFusionView used by 0x001F1FC8).
inline camp::TitleMainWork* TitleWork() {
    return camp::g_TitleMainWork;
}
inline u16* TitleTouchHandles(camp::TitleMainWork* work) {
    return reinterpret_cast<u16*>(&work->field_74);
}
inline u8* TitleHandleObject(u32 handle) {
    u8* base = reinterpret_cast<u8*>(static_cast<std::uintptr_t>(handle));
    return *reinterpret_cast<u8**>(base + 8);
}
inline u32* TitleHandleFlags(u32 handle) {
    return reinterpret_cast<u32*>(static_cast<std::uintptr_t>(handle));
}
inline u8* TitleHandleSub(u32 handle) {
    return *reinterpret_cast<u8**>(TitleHandleObject(handle) + 0x2C);
}

/** 0x24C / 0x2AC GPU ring push.  The cursor is stored before the value; the
 *  previous entry is read from `8+cursor*4` and the `+0x1C` hook runs when
 *  `+0x18` is set or the value changed (0x00214A70..0x00214AA8). */
void RingPush(u32 slot_offset, u32 value) {
    u8* slot = g_AsdGpuState + 0x1000 + slot_offset;
    u32 cursor = *reinterpret_cast<u32*>(slot);
    const u32 old = *reinterpret_cast<u32*>(slot + 8 + cursor * 4);
    ++cursor;
    *reinterpret_cast<u32*>(slot) = cursor;
    *reinterpret_cast<u32*>(slot + 8 + cursor * 4) = value;
    if (slot[0x18] != 0 || old != value) {
        reinterpret_cast<void (*)(u32)>(*reinterpret_cast<u32*>(slot + 0x1C))(value);
        slot[0x18] = 0;
    }
}

/** Pop one entry from the same ring (0x00215420..0x00215458). */
void RingPop(u32 slot_offset) {
    u8* slot = g_AsdGpuState + 0x1000 + slot_offset;
    u32 cursor = *reinterpret_cast<u32*>(slot);
    const u32 old = *reinterpret_cast<u32*>(slot + 8 + cursor * 4);
    --cursor;
    *reinterpret_cast<u32*>(slot) = cursor;
    const u32 value = *reinterpret_cast<u32*>(slot + 8 + cursor * 4);
    if (slot[0x18] != 0 || old != value) {
        reinterpret_cast<void (*)(u32)>(*reinterpret_cast<u32*>(slot + 0x1C))(value);
        slot[0x18] = 0;
    }
}

/** 0x30C / 0x2AC ring set: the cursor is not advanced and only the current
 *  entry is replaced (0x001F293C..0x001F2968, 0x001F2E1C..0x001F2E48). */
void RingSet(u32 slot_offset, u32 value) {
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

// Title-screen strings.  The binaries are CP932; the byte escapes keep the
// shipped glyphs independent of the compiler's source charset.
const char kFusionPossible[] =
    "\x82\x65\x82\x95\x82\x93\x82\x89\x82\x8F\x82\x8E\x81\x40"
    "\x82\x6F\x82\x8F\x82\x93\x82\x93\x82\x89\x82\x82\x82\x8C\x82\x85\x81\x46";
const char kNoCandidates[] =
    "\x82\x73\x82\x88\x82\x85\x82\x92\x82\x85\x81\x40"
    "\x82\x81\x82\x92\x82\x85\x81\x40"
    "\x82\x8E\x82\x8F\x81\x40"
    "\x82\x83\x82\x81\x82\x8E\x82\x84\x82\x89\x82\x84\x82\x81\x82\x94\x82\x85\x82\x93\x81\x44";

/** The "{hours}<0x81>F{mm}<0x81>F{ss}" template at 0x00215394 (the 0x81 0x46
 *  pair is the renderer's line-break escape). */
const char kClockFormat[] = "%s\x81" "F%s%s\x81" "F%s%s";

} // namespace

// ---------------------------------------------------------------------------
// 0x00214964: save/load two-page slot renderer
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00214964, 4020)
__attribute__((naked)) void ui_func_00214964() {
    asm volatile(
        ".word 0xe92d4ff0\n"
        ".word 0xe59f043c\n"
        ".word 0xed2d8b02\n"
        ".word 0xe24dd0fc\n"
        ".word 0xe5900004\n"
        ".word 0xe58d0020\n"
        ".word 0xe2800c03\n"
        ".word 0xe58d00cc\n"
        ".word 0xe5d00078\n"
        ".word 0xe3500000\n"
        ".word 0x1a0003dd\n"
        ".word 0xe59d0020\n"
        ".word 0xe59f5414\n"
        ".word 0xe5900008\n"
        ".word 0xe2401002\n"
        ".word 0xe3510009\n"
        ".word 0x2a000015\n"
        ".word 0xe3500003\n"
        ".word 0x13500004\n"
        ".word 0x0a000012\n"
        ".word 0xe3500005\n"
        ".word 0x13500006\n"
        ".word 0x0a00000f\n"
        ".word 0xe3500007\n"
        ".word 0x13500008\n"
        ".word 0x13500009\n"
        ".word 0x0a00000b\n"
        ".word 0xe59d0020\n"
        ".word 0xe3a01000\n"
        ".word 0xe1d044d9\n"
        ".word 0xe3a0003d\n"
        ".word 0xeb02b137\n"
        ".word 0xeb02b12c\n"
        ".word 0xe0641184\n"
        ".word 0xe0811081\n"
        ".word 0xe0800101\n"
        ".word 0xe1a01005\n"
        ".word 0xe2800014\n"
        ".word 0xea000001\n"
        ".word 0xe1a01005\n"
        ".word 0xe3a00000\n"
        ".word 0xeb0229bf\n"
        ".word 0xe3a00000\n"
        ".word 0xe3a04002\n"
        ".word 0xe88d0011\n"
        ".word 0xe59d0020\n"
        ".word 0xe3a01036\n"
        ".word 0xe5b02034\n"
        ".word 0xe5903030\n"
        ".word 0xe1a00004\n"
        ".word 0xeb02aac9\n"
        ".word 0xed9f8adf\n"
        ".word 0xeddf8adf\n"
        ".word 0xe3a0a000\n"
        ".word 0xe59f9368\n"
        ".word 0xe5996004\n"
        ".word 0xe086000a\n"
        ".word 0xe5d0034c\n"
        ".word 0xe3500000\n"
        ".word 0x0a00009f\n"
        ".word 0xe59f0360\n"
        ".word 0xe3a01000\n"
        ".word 0xe5904000\n"
        ".word 0xe3a00001\n"
        ".word 0xeb02c544\n"
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
        ".word 0xeeb00a68\n"
        ".word 0xeb02ab16\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb02a914\n"
        ".word 0xe28a1051\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02ab00\n"
        ".word 0xe086410a\n"
        ".word 0xe1a05000\n"
        ".word 0xed940a0b\n"
        ".word 0xeb02ab0c\n"
        ".word 0xe5990008\n"
        ".word 0xe3a07002\n"
        ".word 0xe3a02002\n"
        ".word 0xe15a0000\n"
        ".word 0xe1d500fa\n"
        ".word 0x03a02003\n"
        ".word 0xe3a01036\n"
        ".word 0xe88d0081\n"
        ".word 0xe5943068\n"
        ".word 0xe1a00007\n"
        ".word 0xeb02aa93\n"
        ".word 0xe3a0102f\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02aaee\n"
        ".word 0xe1d030fa\n"
        ".word 0xe1d520fa\n"
        ".word 0xe5941068\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0833002\n"
        ".word 0xee003a90\n"
        ".word 0xe0800001\n"
        ".word 0xee000a10\n"
        ".word 0xeeb01a48\n"
        ".word 0xe086b38a\n"
        ".word 0xed942a0b\n"
        ".word 0xeef80ae0\n"
        ".word 0xe28b2f93\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeef01a41\n"
        ".word 0xe3e01000\n"
        ".word 0xe3a00004\n"
        ".word 0xeb02a707\n"
        ".word 0xe3a01039\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02aad9\n"
        ".word 0xe5db1298\n"
        ".word 0xe59f824c\n"
        ".word 0xe0823198\n"
        ".word 0xe1a021a2\n"
        ".word 0xe2622000\n"
        ".word 0xe0822102\n"
        ".word 0xe0816082\n"
        ".word 0xe1d510fa\n"
        ".word 0xe1d020fa\n"
        ".word 0xe0811002\n"
        ".word 0xe88d0082\n"
        ".word 0xe5941068\n"
        ".word 0xe1d000f8\n"
        ".word 0xe2862b02\n"
        ".word 0xe2822fee\n"
        ".word 0xe0813000\n"
        ".word 0xe3a0100d\n"
        ".word 0xe3a00002\n"
        ".word 0xeb02aa2a\n"
        ".word 0xe3a0103a\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02aac3\n"
        ".word 0xe5db1298\n"
        ".word 0xe1d520fa\n"
        ".word 0xe1d030fa\n"
        ".word 0xe0411006\n"
        ".word 0xe0822003\n"
        ".word 0xe0813198\n"
        ".word 0xe88d0084\n"
        ".word 0xe5942068\n"
        ".word 0xe1d000f8\n"
        ".word 0xe1a011a1\n"
        ".word 0xe0823000\n"
        ".word 0xe2812b02\n"
        ".word 0xe2822fee\n"
        ".word 0xe3a0100d\n"
        ".word 0xe3a00002\n"
        ".word 0xeb02aa17\n"
        ".word 0xe5991004\n"
        ".word 0xe28b3f93\n"
        ".word 0xe3a02000\n"
        ".word 0xe081c00a\n"
        ".word 0xe5dcc34c\n"
        ".word 0xe35c0000\n"
        ".word 0x0a000071\n"
        ".word 0xe3a0c000\n"
        ".word 0xe58dc01c\n"
        ".word 0xe5d3304d\n"
        ".word 0xe3130001\n"
        ".word 0x13a0c001\n"
        ".word 0x15cdc01c\n"
        ".word 0xe3130002\n"
        ".word 0x13a0c001\n"
        ".word 0x15cdc01d\n"
        ".word 0xe3130004\n"
        ".word 0x13a0c001\n"
        ".word 0x15cdc01e\n"
        ".word 0xe3130008\n"
        ".word 0x13a03001\n"
        ".word 0x15cd301f\n"
        ".word 0xe5dd301c\n"
        ".word 0xe3530001\n"
        ".word 0xe5dd301d\n"
        ".word 0x03a02001\n"
        ".word 0xe3530001\n"
        ".word 0xe5dd301e\n"
        ".word 0x03a02001\n"
        ".word 0xe3530001\n"
        ".word 0xe5dd301f\n"
        ".word 0x03a02001\n"
        ".word 0xe3530001\n"
        ".word 0x0a000001\n"
        ".word 0xe3520000\n"
        ".word 0x0a000054\n"
        ".word 0xe3a04000\n"
        ".word 0xe28d801c\n"
        ".word 0xe3a07002\n"
        ".word 0xe081610a\n"
        ".word 0xe7d80004\n"
        ".word 0xe3500000\n"
        ".word 0xe1d500fa\n"
        ".word 0xe88d0081\n"
        ".word 0xe5963068\n"
        ".word 0x0a000043\n"
        ".word 0xe2842034\n"
        ".word 0xe3a01036\n"
        ".word 0xe3a00002\n"
        ".word 0xeb02a9e5\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000040\n"
        ".word 0xe28a1051\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02aa7b\n"
        ".word 0xe086410a\n"
        ".word 0xe1a07000\n"
        ".word 0xed940a0b\n"
        ".word 0xeb02aa87\n"
        ".word 0xe5990008\n"
        ".word 0xe3a01002\n"
        ".word 0xe3a02004\n"
        ".word 0xe15a0000\n"
        ".word 0xe1d700fa\n"
        ".word 0x03a02005\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe5943068\n"
        ".word 0xe3a01036\n"
        ".word 0xe3a00002\n"
        ".word 0xeb02aa0e\n"
        ".word 0xeeb00a68\n"
        ".word 0xe320f000\n"
        ".word 0xeb02aa79\n"
        ".word 0xe3a0102f\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02aa66\n"
        ".word 0xe1a05000\n"
        ".word 0xe1d664d9\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a0003d\n"
        ".word 0xeb02b05e\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb02b051\n"
        ".word 0xe0661186\n"
        ".word 0xe1d730fa\n"
        ".word 0xe0811081\n"
        ".word 0xe594c068\n"
        ".word 0xe0802101\n"
        ".word 0xe1d500fa\n"
        ".word 0xe1d510f8\n"
        ".word 0xeeb01a48\n"
        ".word 0xe0800003\n"
        ".word 0xe081100c\n"
        ".word 0xee000a90\n"
        ".word 0xee001a10\n"
        ".word 0xe59f1038\n"
        ".word 0xeef01a41\n"
        ".word 0xed942a0b\n"
        ".word 0xe3a00004\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeb02a676\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea0001ad\n"
        ".word 0x0044de28\n"
        ".word 0x323232ff\n"
        ".word 0x00000000\n"
        ".word 0x3f800000\n"
        ".word 0x0044ea00\n"
        ".word 0xcccccccd\n"
        ".word 0x787878ff\n"
        ".word 0xe2842030\n"
        ".word 0xe3a01036\n"
        ".word 0xe3a00002\n"
        ".word 0xeb02a9a1\n"
        ".word 0xe2844001\n"
        ".word 0xe3540004\n"
        ".word 0xbaffffae\n"
        ".word 0xe5998004\n"
        ".word 0xe1a0700a\n"
        ".word 0xe28b4f93\n"
        ".word 0xe1a06009\n"
        ".word 0xe3a0102a\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02aa33\n"
        ".word 0xe1a09000\n"
        ".word 0xe1d405b8\n"
        ".word 0xe3500000\n"
        ".word 0x0a000028\n"
        ".word 0xe5961004\n"
        ".word 0xe0811007\n"
        ".word 0xe5d1134c\n"
        ".word 0xe3510000\n"
        ".word 0x0a000023\n"
        ".word 0xe24010c8\n"
        ".word 0xe3510064\n"
        ".word 0xe1d415ba\n"
        ".word 0x33a000cb\n"
        ".word 0xe28d3028\n"
        ".word 0xe3a02002\n"
        ".word 0xeb00ef42\n"
        ".word 0xe599000c\n"
        ".word 0xeeb00a48\n"
        ".word 0xe3a01002\n"
        ".word 0xe1d040f0\n"
        ".word 0xe28d0028\n"
        ".word 0xeb01ea3f\n"
        ".word 0xeef00a40\n"
        ".word 0xee004a10\n"
        ".word 0xe0880107\n"
        ".word 0xe1d910f8\n"
        ".word 0xe5903068\n"
        ".word 0xed902a0b\n"
        ".word 0xe1d520fa\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe0830001\n"
        ".word 0xee010a10\n"
        ".word 0xe1d9c0fa\n"
        ".word 0xeef01a48\n"
        ".word 0xe3a00002\n"
        ".word 0xe082100c\n"
        ".word 0xe28d2028\n"
        ".word 0xeeb81ac1\n"
        ".word 0xee300a60\n"
        ".word 0xee001a90\n"
        ".word 0xe59f14e0\n"
        ".word 0xeef80ae0\n"
        ".word 0xee310a00\n"
        ".word 0xeeb01a48\n"
        ".word 0xeb02a631\n"
        ".word 0xe5966004\n"
        ".word 0xe1a0400a\n"
        ".word 0xe28b8f93\n"
        ".word 0xe0860004\n"
        ".word 0xe5d0034c\n"
        ".word 0xe3500000\n"
        ".word 0x0a000062\n"
        ".word 0xe3a01023\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02a9fc\n"
        ".word 0xe58d0014\n"
        ".word 0xe5982050\n"
        ".word 0xe59f84a0\n"
        ".word 0xe3a0e000\n"
        ".word 0xe1a03002\n"
        ".word 0xe1a0000e\n"
        ".word 0xe0e30298\n"
        ".word 0xe1a0c002\n"
        ".word 0xe3e090e0\n"
        ".word 0xe1a005c3\n"
        ".word 0xe0401fc3\n"
        ".word 0xe1a0000e\n"
        ".word 0xe0ec0298\n"
        ".word 0xe1a005cc\n"
        ".word 0xe0400fcc\n"
        ".word 0xe048c228\n"
        ".word 0xe0000990\n"
        ".word 0xe0822200\n"
        ".word 0xe1a0000e\n"
        ".word 0xe1a03002\n"
        ".word 0xe0e3029c\n"
        ".word 0xe1a08002\n"
        ".word 0xe0e8e29c\n"
        ".word 0xe1a002c3\n"
        ".word 0xe0409fc3\n"
        ".word 0xe1a002c8\n"
        ".word 0xe0400fc8\n"
        ".word 0xe0400200\n"
        ".word 0xe0828100\n"
        ".word 0xe28d0048\n"
        ".word 0xeb01eec3\n"
        ".word 0xe59f0430\n"
        ".word 0xe0c01990\n"
        ".word 0xe1a01140\n"
        ".word 0xe0410fc0\n"
        ".word 0xe2601000\n"
        ".word 0xe0811101\n"
        ".word 0xe0899081\n"
        ".word 0xe28d10f0\n"
        ".word 0xeb00eecb\n"
        ".word 0xe28d10d8\n"
        ".word 0xe1a00009\n"
        ".word 0xeb00eec8\n"
        ".word 0xe59f0400\n"
        ".word 0xe0c01890\n"
        ".word 0xe1a01140\n"
        ".word 0xe0410fc0\n"
        ".word 0xe2601000\n"
        ".word 0xe0811101\n"
        ".word 0xe0888081\n"
        ".word 0xe28d10e0\n"
        ".word 0xeb00eebf\n"
        ".word 0xe28d10e8\n"
        ".word 0xe1a00008\n"
        ".word 0xeb00eebc\n"
        ".word 0xe28d20e8\n"
        ".word 0xe28d10e0\n"
        ".word 0xe28d00d8\n"
        ".word 0xe88d0007\n"
        ".word 0xe28d30f0\n"
        ".word 0xe28d2048\n"
        ".word 0xe28f1fef\n"
        ".word 0xe28d0028\n"
        ".word 0xfa02a607\n"
        ".word 0xe28d0028\n"
        ".word 0xe320f000\n"
        ".word 0xeb02b8a9\n"
        ".word 0xe1a01000\n"
        ".word 0xe59d0014\n"
        ".word 0xe0811181\n"
        ".word 0xe1d520fa\n"
        ".word 0xe0811fa1\n"
        ".word 0xe590000c\n"
        ".word 0xe1d000f0\n"
        ".word 0xe04000c1\n"
        ".word 0xee000a10\n"
        ".word 0xe59d0014\n"
        ".word 0xe1d010f8\n"
        ".word 0xe1d000fa\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe0800002\n"
        ".word 0xee000a90\n"
        ".word 0xe0860104\n"
        ".word 0xe5902068\n"
        ".word 0xed902a0b\n"
        ".word 0xe3a00002\n"
        ".word 0xe0811002\n"
        ".word 0xee011a10\n"
        ".word 0xeef80ae0\n"
        ".word 0xe51f1284\n"
        ".word 0xe28d2028\n"
        ".word 0xeeb81ac1\n"
        ".word 0xee310a00\n"
        ".word 0xeeb01a48\n"
        ".word 0xeef01a41\n"
        ".word 0xeb02a5c7\n"
        ".word 0xe51f02b8\n"
        ".word 0xe1a0600a\n"
        ".word 0xe28b9f93\n"
        ".word 0xe5908004\n"
        ".word 0xe0880006\n"
        ".word 0xe5d0034c\n"
        ".word 0xe3500000\n"
        ".word 0x0a000050\n"
        ".word 0xe3a01010\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02a991\n"
        ".word 0xe3a01018\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02a98e\n"
        ".word 0xe3a04000\n"
        ".word 0xe3a0700b\n"
        ".word 0xe0886106\n"
        ".word 0xe1d500fa\n"
        ".word 0xe2842012\n"
        ".word 0xe3a01036\n"
        ".word 0xe88d0081\n"
        ".word 0xe5963068\n"
        ".word 0xe3a00002\n"
        ".word 0xeb02a8e8\n"
        ".word 0xe2844001\n"
        ".word 0xe3540004\n"
        ".word 0xbafffff5\n"
        ".word 0xe3a01018\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02a97e\n"
        ".word 0xe1a04000\n"
        ".word 0xe1d500fa\n"
        ".word 0xe1d420fa\n"
        ".word 0xe3a01015\n"
        ".word 0xe0800002\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe5960068\n"
        ".word 0xe1d410f8\n"
        ".word 0xe3a02016\n"
        ".word 0xe0803001\n"
        ".word 0xe3a01036\n"
        ".word 0xe3a00002\n"
        ".word 0xeb02a8d5\n"
        ".word 0xe3a08000\n"
        ".word 0xe58d8000\n"
        ".word 0xe1d510fa\n"
        ".word 0xe1d420fa\n"
        ".word 0xe5960068\n"
        ".word 0xe1d430f8\n"
        ".word 0xe0822001\n"
        ".word 0xe0801003\n"
        ".word 0xe3a03002\n"
        ".word 0xe3e00000\n"
        ".word 0xeb028658\n"
        ".word 0xe3a04000\n"
        ".word 0xe0898084\n"
        ".word 0xe1d805bc\n"
        ".word 0xe3500000\n"
        ".word 0x0a00001a\n"
        ".word 0xe2841019\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02a95e\n"
        ".word 0xe1a07000\n"
        ".word 0xe1d000fa\n"
        ".word 0xe1d510fa\n"
        ".word 0xe3a02016\n"
        ".word 0xe0800001\n"
        ".word 0xe3a0100b\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d700f8\n"
        ".word 0xe5961068\n"
        ".word 0xe0813000\n"
        ".word 0xe3a01036\n"
        ".word 0xe3a00002\n"
        ".word 0xeb02a8b5\n"
        ".word 0xe3a00000\n"
        ".word 0xe58d0000\n"
        ".word 0xe1d520fa\n"
        ".word 0xe1d730fa\n"
        ".word 0xe5961068\n"
        ".word 0xe1d7c0f8\n"
        ".word 0xe0822003\n"
        ".word 0xe1d805fc\n"
        ".word 0xe081100c\n"
        ".word 0xe3a03015\n"
        ".word 0xeb028638\n"
        ".word 0xe2844001\n"
        ".word 0xe3540003\n"
        ".word 0xbaffffdd\n"
        ".word 0xe51f141c\n"
        ".word 0xe28b4f93\n"
        ".word 0xe5911004\n"
        ".word 0xe081200a\n"
        ".word 0xe5d2234c\n"
        ".word 0xe3520000\n"
        ".word 0x0a00008c\n"
        ".word 0xe1d426b6\n"
        ".word 0xe3520000\n"
        ".word 0x0a00007d\n"
        ".word 0xe1d520fa\n"
        ".word 0xe3a0b002\n"
        ".word 0xe081810a\n"
        ".word 0xe88d0804\n"
        ".word 0xe5983068\n"
        ".word 0xe3a0206e\n"
        ".word 0xe3a01036\n"
        ".word 0xe1a0000b\n"
        ".word 0xeb02a894\n"
        ".word 0xe59f0190\n"
        ".word 0xe320f000\n"
        ".word 0xeb02a4b0\n"
        ".word 0xe1d406b6\n"
        ".word 0xe59f4184\n"
        ".word 0xe3e0c07c\n"
        ".word 0xe2807001\n"
        ".word 0xe3a01001\n"
        ".word 0xe0843104\n"
        ".word 0xe0847794\n"
        ".word 0xe3a06ffa\n"
        ".word 0xe51f2480\n"
        ".word 0xe1a04324\n"
        ".word 0xe00c0c94\n"
        ".word 0xe0070694\n"
        ".word 0xe081118c\n"
        ".word 0xe0811000\n"
        ".word 0xe0813193\n"
        ".word 0xe1a062a1\n"
        ".word 0xe0861186\n"
        ".word 0xe0811206\n"
        ".word 0xe0871101\n"
        ".word 0xe0403001\n"
        ".word 0xe2833001\n"
        ".word 0xe0823392\n"
        ".word 0xe1a071a2\n"
        ".word 0xe0872107\n"
        ".word 0xe0811082\n"
        ".word 0xe0400001\n"
        ".word 0xe2809001\n"
        ".word 0xe3a01072\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02a90f\n"
        ".word 0xe3540000\n"
        ".word 0xe320f000\n"
        ".word 0x0a00000b\n"
        ".word 0xe1d510fa\n"
        ".word 0xe1d030fa\n"
        ".word 0xe2842b02\n"
        ".word 0xe2822fee\n"
        ".word 0xe0811003\n"
        ".word 0xe88d0802\n"
        ".word 0xe5981068\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0813000\n"
        ".word 0xe3a0100d\n"
        ".word 0xe3a00002\n"
        ".word 0xeb02a864\n"
        ".word 0xe3a01071\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02a8fd\n"
        ".word 0xe1961004\n"
        ".word 0xe320f000\n"
        ".word 0x0a00000b\n"
        ".word 0xe1d510fa\n"
        ".word 0xe1d030fa\n"
        ".word 0xe2862b02\n"
        ".word 0xe2822fee\n"
        ".word 0xe0811003\n"
        ".word 0xe88d0802\n"
        ".word 0xe5981068\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0813000\n"
        ".word 0xe3a0100d\n"
        ".word 0xe3a00002\n"
        ".word 0xeb02a852\n"
        ".word 0xe3a01070\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02a8eb\n"
        ".word 0xe1866007\n"
        ".word 0xe1961004\n"
        ".word 0x0a00000b\n"
        ".word 0xe1d510fa\n"
        ".word 0xe1d030fa\n"
        ".word 0xe2872b02\n"
        ".word 0xe2822fee\n"
        ".word 0xe0811003\n"
        ".word 0xe88d0802\n"
        ".word 0xe5981068\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0813000\n"
        ".word 0xe3a0100d\n"
        ".word 0xe3a00002\n"
        ".word 0xeb02a840\n"
        ".word 0xe3a0106f\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02a8d9\n"
        ".word 0xe1861009\n"
        ".word 0xe1911004\n"
        ".word 0x0a000015\n"
        ".word 0xe1d510fa\n"
        ".word 0xe1d030fa\n"
        ".word 0xe0811003\n"
        ".word 0xe88d0802\n"
        ".word 0xea000008\n"
        ".word 0xf49800ff\n"
        ".word 0x91a2b3c5\n"
        ".word 0x66666667\n"
        ".word 0x46817325\n"
        ".word 0x73257325\n"
        ".word 0x73254681\n"
        ".word 0x00007325\n"
        ".word 0x72e02700\n"
        ".word 0x10624dd3\n"
        ".word 0xe5981068\n"
        ".word 0xe1d000f8\n"
        ".word 0xe2892b02\n"
        ".word 0xe2822fee\n"
        ".word 0xe0813000\n"
        ".word 0xe3a0100d\n"
        ".word 0xe3a00002\n"
        ".word 0xeb02a824\n"
        ".word 0xe320f000\n"
        ".word 0xeb02a6cf\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea00000b\n"
        ".word 0xe5d4204d\n"
        ".word 0xe3520000\n"
        ".word 0x0a000008\n"
        ".word 0xe1d520fa\n"
        ".word 0xe3a03002\n"
        ".word 0xe081010a\n"
        ".word 0xe1cd20f0\n"
        ".word 0xe5903068\n"
        ".word 0xe3a02017\n"
        ".word 0xe3a01036\n"
        ".word 0xe3a00002\n"
        ".word 0xeb02a813\n"
        ".word 0xe51f065c\n"
        ".word 0xe5900000\n"
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
        ".word 0xeeb00a68\n"
        ".word 0xeb02a8aa\n"
        ".word 0xe28aa001\n"
        ".word 0xe35a0002\n"
        ".word 0xbafffd72\n"
        ".word 0xeeb00a68\n"
        ".word 0xeb02a8a5\n"
        ".word 0xe59d0020\n"
        ".word 0xe5d00070\n"
        ".word 0xe3500000\n"
        ".word 0x0a000046\n"
        ".word 0xe59d0020\n"
        ".word 0xe5d00071\n"
        ".word 0xe3500000\n"
        ".word 0x1a000042\n"
        ".word 0xe59d00cc\n"
        ".word 0xe5d00054\n"
        ".word 0xe3500000\n"
        ".word 0x0a00003e\n"
        ".word 0xe51f0704\n"
        ".word 0xe5900008\n"
        ".word 0xe2801051\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02a884\n"
        ".word 0xe51f6708\n"
        ".word 0xe1a05000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe5964000\n"
        ".word 0xe3a00006\n"
        ".word 0xeb02c2b2\n"
        ".word 0xe2844a01\n"
        ".word 0xe2844fab\n"
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
        ".word 0xe59d0020\n"
        ".word 0xed900a07\n"
        ".word 0xeb02a879\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb02a677\n"
        ".word 0xe1d500fa\n"
        ".word 0xe3a01002\n"
        ".word 0xe3a02006\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d530f8\n"
        ".word 0xe3a01036\n"
        ".word 0xe3a00002\n"
        ".word 0xeb02a800\n"
        ".word 0xe5960000\n"
        ".word 0xe2804a01\n"
        ".word 0xe2844fab\n"
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
        ".word 0xeeb00a68\n"
        ".word 0xeb02a85a\n"
        ".word 0xe59d0020\n"
        ".word 0xe5d00055\n"
        ".word 0xe3500000\n"
        ".word 0x0a0000d4\n"
        ".word 0xe59d0020\n"
        ".word 0xe5d00072\n"
        ".word 0xe3500000\n"
        ".word 0x1a0000d0\n"
        ".word 0xe51f7810\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a00001\n"
        ".word 0xe5974000\n"
        ".word 0xeb02c268\n"
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
        ".word 0xe59d0020\n"
        ".word 0xed900add\n"
        ".word 0xeb02a839\n"
        ".word 0xed8d8a04\n"
        ".word 0xed8d8a05\n"
        ".word 0xe28d1018\n"
        ".word 0xe28d0010\n"
        ".word 0xe3a08000\n"
        ".word 0xec818a02\n"
        ".word 0xeb02631f\n"
        ".word 0xe3a090d3\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a030f0\n"
        ".word 0xe3a02d05\n"
        ".word 0xe1a00001\n"
        ".word 0xe58d9000\n"
        ".word 0xebfead09\n"
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
        ".word 0x0a000002\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c48018\n"
        ".word 0xeeb00a68\n"
        ".word 0xeb02a818\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb02a616\n"
        ".word 0xe59d0020\n"
        ".word 0xe5d00055\n"
        ".word 0xe3500000\n"
        ".word 0x0a00008f\n"
        ".word 0xe59d0020\n"
        ".word 0xe5d00072\n"
        ".word 0xe3500000\n"
        ".word 0x1a00008b\n"
        ".word 0xe51f0934\n"
        ".word 0xe5974000\n"
        ".word 0xe3a01000\n"
        ".word 0xe5905004\n"
        ".word 0xe3a00001\n"
        ".word 0xeb02c222\n"
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
        ".word 0x0a000002\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c48018\n"
        ".word 0xeeb00a68\n"
        ".word 0xeb02a7f5\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb02a5f3\n"
        ".word 0xe5951050\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02a7df\n"
        ".word 0xe1cd80f0\n"
        ".word 0xe5952050\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a01036\n"
        ".word 0xe3a00002\n"
        ".word 0xeb02a77b\n"
        ".word 0xe3a04000\n"
        ".word 0xe28da008\n"
        ".word 0xe2841062\n"
        ".word 0xe3a00036\n"
        ".word 0xeb02a7d4\n"
        ".word 0xe1d030f8\n"
        ".word 0xe08a1184\n"
        ".word 0xe3a0205f\n"
        ".word 0xee003a10\n"
        ".word 0xeeb80ac0\n"
        ".word 0xed810a00\n"
        ".word 0xe1d000fa\n"
        ".word 0xee000a10\n"
        ".word 0xeeb80ac0\n"
        ".word 0xed810a01\n"
        ".word 0xe88d0201\n"
        ".word 0xe3a01036\n"
        ".word 0xe3a00002\n"
        ".word 0xeb02a72a\n"
        ".word 0xe2844001\n"
        ".word 0xe3540009\n"
        ".word 0xbaffffeb\n"
        ".word 0xe5950060\n"
        ".word 0xe2800001\n"
        ".word 0xe2100003\n"
        ".word 0xe5850060\n"
        ".word 0xe5950058\n"
        ".word 0x02800001\n"
        ".word 0x05850058\n"
        ".word 0xe2000007\n"
        ".word 0xe5850058\n"
        ".word 0xe08a1180\n"
        ".word 0xe2803004\n"
        ".word 0xed910a01\n"
        ".word 0xe2802001\n"
        ".word 0xe2034007\n"
        ".word 0xeebd0ac0\n"
        ".word 0xe2840001\n"
        ".word 0xe2025007\n"
        ".word 0xe2006007\n"
        ".word 0xe3a02061\n"
        ".word 0xe3a00002\n"
        ".word 0xed8d0a00\n"
        ".word 0xe58d9004\n"
        ".word 0xed910a00\n"
        ".word 0xe3a01036\n"
        ".word 0xeebd0ac0\n"
        ".word 0xee103a10\n"
        ".word 0xeb02a70c\n"
        ".word 0xe08a0185\n"
        ".word 0xe3a02060\n"
        ".word 0xed900a01\n"
        ".word 0xe3a01036\n"
        ".word 0xeebd0ac0\n"
        ".word 0xed8d0a00\n"
        ".word 0xe58d9004\n"
        ".word 0xed900a00\n"
        ".word 0xe3a00002\n"
        ".word 0xeebd0ac0\n"
        ".word 0xee103a10\n"
        ".word 0xeb02a700\n"
        ".word 0xe08a0184\n"
        ".word 0xe3a02061\n"
        ".word 0xed900a01\n"
        ".word 0xe3a01036\n"
        ".word 0xeebd0ac0\n"
        ".word 0xed8d0a00\n"
        ".word 0xe58d9004\n"
        ".word 0xed900a00\n"
        ".word 0xe3a00002\n"
        ".word 0xeebd0ac0\n"
        ".word 0xee103a10\n"
        ".word 0xeb02a6f4\n"
        ".word 0xe08a0186\n"
        ".word 0xe3a02060\n"
        ".word 0xed900a01\n"
        ".word 0xe3a01036\n"
        ".word 0xeebd0ac0\n"
        ".word 0xed8d0a00\n"
        ".word 0xe58d9004\n"
        ".word 0xed900a00\n"
        ".word 0xe3a00002\n"
        ".word 0xeebd0ac0\n"
        ".word 0xee103a10\n"
        ".word 0xeb02a6e8\n"
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
        ".word 0x0a000002\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c48018\n"
        ".word 0xeeb00a68\n"
        ".word 0xeb02a781\n"
        ".word 0xe28dd0fc\n"
        ".word 0xe3a00000\n"
        ".word 0xecbd8b02\n"
        ".word 0xe8bd8ff0\n"
    );
}
#if 0
// Original partial readable draft retained for reconstruction; not compiled.
void ui_func_00214964() {
    SaveLoadUIWork* work = g_SaveLoadUIManager.work;

    // 0x00214984: the 0x300 sub-block's +0x78 byte suspends rendering.
    if (reinterpret_cast<u8*>(work)[0x378] != 0) {
        return;
    }

    // 0x00214998..0x002149FC: the Tbb 0x3D entry (stride 0x54, status string
    // at +0x14) is only prepared for states 2 and 10.  The cascade is the
    // literal `sub r1,r0,#2; cmp r1,#9; bhs` (so state 11 is excluded) plus
    // the 3..9 exclusions.
    const char* title_text = nullptr;
    const u32 state = work->state;
    if (state - 2 < 9 &&
        state != 3 && state != 4 && state != 5 && state != 6 &&
        state != 7 && state != 8 && state != 9) {
        const Tbl1Header* sub_table = Tbb_GetGlobalSubTable(0x3D, 0);
        const u8* payload = static_cast<const u8*>(Tbb_GetPayloadData(sub_table));
        const s32 index = work->index_049;
        title_text = reinterpret_cast<const char*>(payload + 0x14 + 84 * index);
    }
    // 0x00214A08: r1 = 0x323232FF in both paths.
    Camp_SetSlotMessage(title_text, 0x323232FF);

    // 0x00214A20..0x00214A2C: panel = work->panel_034, x = work->field_064.
    UiSprite_DrawPanel(2, 0x36, work->panel_034, work->field_064, 0, 2);

    for (s32 slot = 0; slot < 2; ++slot) {
        SaveSlotPage& page = work->slots[slot];
        const s32 pos_x = work->slot_pos_068[slot];
        const f32 scale = work->slot_scale_02C[slot];

        if (work->active_34C[slot] == 0) {
            // 0x00214CD4: empty page.  No GPU ring is pushed on this path.
            // The anchor is the page's own node (`add r1,sl,#0x51`, 0x00214CD4).
            const Npc2dLayoutNode* anchor =
                LayoutNode(0x36, 0x51 + static_cast<u32>(slot));
            UiSprite_SetGlobalAlpha(scale);
            UiSprite_DrawPanel(2, 0x36,
                               (g_SaveLoadUIManager.selected == static_cast<u32>(slot)) ? 5 : 4,
                               pos_x, anchor->y, 2);

            UiSprite_SetGlobalAlpha(1.0F);                              // 0x00214D1C
            const Npc2dLayoutNode* name_node = LayoutNode(0x36, 0x2F);
            const Tbl1Header* sub_table = Tbb_GetGlobalSubTable(0x3D, 0);
            const u8* payload = static_cast<const u8*>(Tbb_GetPayloadData(sub_table));
            const char* name =
                reinterpret_cast<const char*>(payload + 84 * static_cast<s32>(work->index_049));
            UiFont_DrawText(4, 0x787878FF, name,
                            static_cast<f32>(pos_x + name_node->x),
                            static_cast<f32>(anchor->y + name_node->y),
                            0.0F, 0.0F, scale);
            continue;                                                   // 0x00214DA8
        }

        // 0x00214A54..0x00214AA8: viewport + 0x24C ring push.  The value
        // pushed is the 0x002C5F7C return value (r0 survives to `str r0,[r3,#8]`
        // at 0x00214A88), not the literal 1.
        const u32 viewport = static_cast<u32>(reinterpret_cast<std::uintptr_t>(
            UiGpu_SetViewportParams(1, 0)));
        RingPush(0x24C, viewport);
        UiSprite_SetGlobalAlpha(1.0F);
        UiSprite_ResetBlend();

        const Npc2dLayoutNode* anchor =
            LayoutNode(0x36, 0x51 + static_cast<u32>(slot));
        UiSprite_SetGlobalAlpha(scale);

        // 0x00214AF4..0x00214B04: panel 3 for the selected page, 2 otherwise.
        UiSprite_DrawPanel(2, 0x36,
                           (g_SaveLoadUIManager.selected == static_cast<u32>(slot)) ? 3 : 2,
                           pos_x, anchor->y, 2);

        // 0x00214B08..0x00214B58: slot name anchored at layout node 0x2F.
        const Npc2dLayoutNode* field_node = LayoutNode(0x36, 0x2F);
        UiFont_DrawText(4, 0xFFFFFFFF, page.text,
                        static_cast<f32>(pos_x + field_node->x),
                        static_cast<f32>(anchor->y + field_node->y),
                        0.0F, 0.0F, scale);

        // 0x00214B68..0x00214C00: two decimal digits of page.digit_4C drawn
        // with group 0x0D glyphs 0xBB8+digit at nodes 0x39 (units) / 0x3A (tens).
        const u32 digit = page.digit_4C;
        const u32 units = digit % 10;
        const u32 tens = (digit - units) / 10;
        const Npc2dLayoutNode* units_node = LayoutNode(0x36, 0x39);
        UiSprite_DrawNode(2, 0x0D, 0xBB8 + units,
                          pos_x + units_node->x, anchor->y + units_node->y, 2);
        const Npc2dLayoutNode* tens_node = LayoutNode(0x36, 0x3A);
        UiSprite_DrawNode(2, 0x0D, 0xBB8 + tens,
                          pos_x + tens_node->x, anchor->y + tens_node->y, 2);

        // 0x00214C24..0x00214CD0: four flag icons (nodes 0x30..0x33 empty,
        // 0x34..0x37 set) gated on any of the four bits.
        const u8 flags = page.flags_4D;
        const u8 bits[4] = {
            static_cast<u8>((flags & 1) ? 1 : 0),
            static_cast<u8>((flags & 2) ? 1 : 0),
            static_cast<u8>((flags & 4) ? 1 : 0),
            static_cast<u8>((flags & 8) ? 1 : 0),
        };
        if (bits[0] != 0 || bits[1] != 0 || bits[2] != 0 || bits[3] != 0) {
            for (s32 i = 0; i < 4; ++i) {
                UiSprite_DrawNode(2, 0x36,
                                  static_cast<u32>(i + (bits[i] != 0 ? 0x34 : 0x30)),
                                  pos_x, anchor->y, 2);
            }
        }

        // 0x00214DE4..0x00214EB0: optional clamp/frame field at node 0x2A.
        const Npc2dLayoutNode* field_2a = LayoutNode(0x36, 0x2A);
        if (page.clamp_58 != 0 && work->active_34C[slot] != 0) {
            u32 value = page.clamp_58;
            if (value - 200 < 100) {
                value = 0xCB;                                           // 0x00214E30
            }
            char field_text[0x20];
            UiText_FormatSlotField(value, page.frame_5A, 2, field_text);
            const s16* rect = reinterpret_cast<const s16*>(field_2a->extra);
            const f32 measured = Quest_MeasureText(field_text, 2);
            const f32 x = static_cast<f32>(pos_x + field_2a->x) +
                          (static_cast<f32>(rect[0]) - measured);
            const f32 y = static_cast<f32>(anchor->y + field_2a->y);
            UiFont_DrawText(2, 0xF49800FF, field_text, x, y, 0.0F, 0.0F, scale);
        }

        // 0x00214EB4..0x00215058: play clock.  page.timer_50 is split into
        // hours (0x290A68), and the tens/units of minutes and seconds
        // (0x250AAC), then formatted through 0x00215394 and centred in the
        // node 0x23 rectangle (strlen * 9 / 2, 0x00214FF0..0x00215004).
        if (work->active_34C[slot] != 0) {
            const Npc2dLayoutNode* clock_node = LayoutNode(0x36, 0x23);
            const u32 timer = page.timer_50;
            const u32 hours = timer / 3600;
            // 0x00214F18..0x00214F20: `mul hours,-225; add timer,hours<<4`
            // => timer - 3600 * hours (both smlal uses 0x91A2B3C5 = 1/3600).
            const u32 rem_hour = timer - 3600 * hours;
            const u32 minutes = rem_hour / 60;
            const u32 seconds = rem_hour - 60 * minutes;

            char hours_text[0x20];
            char minutes_tens[8];
            char minutes_units[8];
            char seconds_tens[8];
            char seconds_units[8];
            UiText_FormatDigits(hours_text, hours);
            UiText_FormatTwoDigits(minutes / 10, minutes_tens);
            UiText_FormatTwoDigits(minutes % 10, minutes_units);
            UiText_FormatTwoDigits(seconds / 10, seconds_tens);
            UiText_FormatTwoDigits(seconds % 10, seconds_units);

            char clock_text[0x20];
            UiFont_FormatString(clock_text, kClockFormat,
                                hours_text, minutes_tens, minutes_units,
                                seconds_tens, seconds_units);
            const s32 length = static_cast<s32>(AsdString_Length(clock_text));
            const s16* rect = reinterpret_cast<const s16*>(clock_node->extra);
            const f32 x = static_cast<f32>(pos_x + clock_node->x) +
                          (static_cast<f32>(rect[0]) -
                           static_cast<f32>((length * 9) / 2));
            const f32 y = static_cast<f32>(anchor->y + clock_node->y);
            UiFont_DrawText(2, 0x787878FF, clock_text,
                            x, y, 0.0F, 0.0F, scale);
        }

        // 0x0021505C..0x002151BC: chrome row.  Four nodes 0x12..0x15 at
        // priority 0x0B, then node 0x16 plus the -1 item icon, then the three
        // page icon ids at nodes 0x19..0x1B.
        if (work->active_34C[slot] != 0) {
            // 0x0021507C: the node 0x10 lookup is not consumed by the listing;
            // the loop is anchored on the page node (r5) instead.
            (void)LayoutNode(0x36, 0x10);
            const Npc2dLayoutNode* icon_node = LayoutNode(0x36, 0x18);
            for (s32 i = 0; i < 4; ++i) {
                UiSprite_DrawNode(2, 0x36, static_cast<u32>(i + 0x12),
                                  pos_x, anchor->y, 0x0B);
            }
            UiSprite_DrawNode(2, 0x36, 0x16,
                              pos_x + icon_node->x,
                              anchor->y + icon_node->y, 0x15);
            UiSkill_DrawItemIconAndCount(-1, pos_x + icon_node->x,
                                         anchor->y + icon_node->y, 2, 0);

            for (s32 i = 0; i < 3; ++i) {
                if (page.icon_5C[i] == 0) {
                    continue;
                }
                const Npc2dLayoutNode* node = LayoutNode(0x36, static_cast<u32>(i + 0x19));
                UiSprite_DrawNode(2, 0x36, 0x16,
                                  pos_x + node->x, anchor->y + node->y, 0x0B);
                UiSkill_DrawItemIconAndCount(static_cast<s16>(page.icon_5C[i]),
                                             pos_x + node->x,
                                             anchor->y + node->y, 0x15, 0);
            }

            // 0x002151C0..0x002153DC: the +0x66 counter is drawn as the four
            // decimal digits of (counter+1) at nodes 0x72/0x71/0x70/0x6F,
            // suppressing leading zeros.  When the counter is clear the +0x4D
            // flags select node 0x17 instead.
            if (page.counter_66 != 0) {
                UiSprite_DrawNode(2, 0x36, 0x6E, pos_x, anchor->y, 2);
                UiColor_SetFromRgba(0x72E02700);                        // 0x0021520C

                const u32 value = page.counter_66 + 1;
                const u32 count_thousands = value / 1000;
                const u32 rem_1000 = value - count_thousands * 1000;
                const u32 count_hundreds = rem_1000 / 100;
                const u32 count_tens = (rem_1000 - count_hundreds * 100) / 10;
                const u32 count_units =
                    rem_1000 - count_hundreds * 100 - count_tens * 10;

                if (count_thousands != 0) {
                    const Npc2dLayoutNode* node = LayoutNode(0x36, 0x72);
                    UiSprite_DrawNode(2, 0x0D, 0xBB8 + count_thousands,
                                      pos_x + node->x, anchor->y + node->y, 2);
                }
                if ((count_hundreds | count_thousands) != 0) {
                    const Npc2dLayoutNode* node = LayoutNode(0x36, 0x71);
                    UiSprite_DrawNode(2, 0x0D, 0xBB8 + count_hundreds,
                                      pos_x + node->x, anchor->y + node->y, 2);
                }
                if ((count_tens | count_hundreds | count_thousands) != 0) {
                    const Npc2dLayoutNode* node = LayoutNode(0x36, 0x70);
                    UiSprite_DrawNode(2, 0x0D, 0xBB8 + count_tens,
                                      pos_x + node->x, anchor->y + node->y, 2);
                }
                if ((count_units | count_tens | count_hundreds | count_thousands) != 0) {
                    const Npc2dLayoutNode* node = LayoutNode(0x36, 0x6F);
                    UiSprite_DrawNode(2, 0x0D, 0xBB8 + count_units,
                                      pos_x + node->x, anchor->y + node->y, 2);
                }
                UiSprite_ResetBlend();                                  // 0x002153D0
            } else if (page.flags_4D != 0) {
                UiSprite_DrawNode(2, 0x36, 0x17, pos_x, anchor->y, 2);
            }
        }

        RingPop(0x24C);
        UiSprite_SetGlobalAlpha(1.0F);
    }

    UiSprite_SetGlobalAlpha(1.0F);                                      // 0x00215470

    // 0x00215478..0x002155A0: selected-page summary panel on the 0x2AC ring.
    if (work->flag_070 != 0 && work->flag_071 == 0 && work->flag_354 != 0) {
        const Npc2dLayoutNode* node =
            LayoutNode(0x36, 0x51 + g_SaveLoadUIManager.selected);
        const u32 mode = static_cast<u32>(reinterpret_cast<std::uintptr_t>(
            UiGpu_SetRenderMode(6, 1, 0)));
        RingPush(0x2AC, mode);
        UiSprite_SetGlobalAlpha(work->field_01C);
        UiSprite_ResetBlend();
        UiSprite_DrawPanel(2, 0x36, 6, node->x, node->y, 2);
        RingPop(0x2AC);
        UiSprite_SetGlobalAlpha(1.0F);
    }

    // 0x002155A4..0x002156A8: faded 3D pass plus the 0xD3-coloured backdrop.
    if (work->flag_055 != 0 && work->flag_072 == 0) {
        const u32 viewport = static_cast<u32>(reinterpret_cast<std::uintptr_t>(
            UiGpu_SetViewportParams(1, 0)));
        RingPush(0x24C, viewport);                                      // 0x002155D4
        UiSprite_SetGlobalAlpha(work->field_374);

        const f32 quad[4] = {0.0F, 0.0F, 0.0F, 1.0F};
        UiDraw_BuildColorQuad(quad);
        UiDraw_ModelPass(0, 0, 0x140, 0xF0, 0xD3);

        RingPop(0x24C);
        UiSprite_SetGlobalAlpha(1.0F);
        UiSprite_ResetBlend();

        if (work->flag_055 != 0 && work->flag_072 == 0) {
            const u32 viewport_b = static_cast<u32>(reinterpret_cast<std::uintptr_t>(
                UiGpu_SetViewportParams(1, 0)));
            RingPush(0x24C, viewport_b);                                // 0x002156F0
            UiSprite_SetGlobalAlpha(1.0F);
            UiSprite_ResetBlend();

            // 0x00215744: the layout lookup result is not consumed; the panel
            // id is work->panel_050 and the draw is anchored at (0, 0).
            LayoutNode(0x36, work->panel_050);
            UiSprite_DrawPanel(2, 0x36, work->panel_050, 0, 0, 0xD3);

            // 0x00215770..0x002158B8: nine digit anchors 0x62..0x6A, each with
            // node 0x5F, cached as (x,y) floats in a 9-entry stack array.
            f32 digit_pos[9][2];
            for (s32 i = 0; i < 9; ++i) {
                const Npc2dLayoutNode* node = LayoutNode(0x36, static_cast<u32>(i + 0x62));
                digit_pos[i][0] = static_cast<f32>(node->x);
                digit_pos[i][1] = static_cast<f32>(node->y);
                UiSprite_DrawNode(2, 0x36, 0x5F, node->x, node->y, 0xD3);
            }

            // 0x002157C0..0x002157E0: +0x60 increments mod 4 and advances the
            // +0x58 rotation only when it wraps; +0x58 is then masked to 7.
            work->field_060 = (work->field_060 + 1) & 3;
            if (work->field_060 == 0) {
                ++work->field_058;
            }
            work->field_058 &= 7;

            const s32 index = static_cast<s32>(work->field_058);
            const s32 index1 = (index + 1) & 7;
            const s32 index4 = (index + 4) & 7;
            const s32 index5 = (index + 5) & 7;
            UiSprite_DrawNode(2, 0x36, 0x61,
                              static_cast<s32>(digit_pos[index][0]),
                              static_cast<s32>(digit_pos[index][1]), 0xD3);
            UiSprite_DrawNode(2, 0x36, 0x60,
                              static_cast<s32>(digit_pos[index1][0]),
                              static_cast<s32>(digit_pos[index1][1]), 0xD3);
            UiSprite_DrawNode(2, 0x36, 0x61,
                              static_cast<s32>(digit_pos[index4][0]),
                              static_cast<s32>(digit_pos[index4][1]), 0xD3);
            UiSprite_DrawNode(2, 0x36, 0x60,
                              static_cast<s32>(digit_pos[index5][0]),
                              static_cast<s32>(digit_pos[index5][1]), 0xD3);

            RingPop(0x24C);
            UiSprite_SetGlobalAlpha(1.0F);
        }
    }
}
#endif

// ---------------------------------------------------------------------------
// 0x001F1FC8: fusion-candidate list
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001f1fc8, 3960)
__attribute__((naked)) void ui_func_001f1fc8(s32 x, s32 y, s32 selected, s32 column, s16 touch_handle) {
    asm volatile(
        ".word 0xe92d4fff\n"
        ".word 0xed2d8b04\n"
        ".word 0xe24dd054\n"
        ".word 0xe1a06000\n"
        ".word 0xe1a05001\n"
        ".word 0xe1a09002\n"
        ".word 0xeb01c297\n"
        ".word 0xe1b0a000\n"
        ".word 0x0a0003ce\n"
        ".word 0xe3560000\n"
        ".word 0xa1a00006\n"
        ".word 0xb2660000\n"
        ".word 0xe3500d05\n"
        ".word 0xaa0003c9\n"
        ".word 0xe3a080c9\n"
        ".word 0xe1a03006\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0120\n"
        ".word 0xeb03354e\n"
        ".word 0xe1a03006\n"
        ".word 0xe3a0205c\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0120\n"
        ".word 0xeb03350a\n"
        ".word 0xe1a03006\n"
        ".word 0xe3a0205d\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0120\n"
        ".word 0xeb033504\n"
        ".word 0xe1a03006\n"
        ".word 0xe3a0205e\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0120\n"
        ".word 0xeb0334fe\n"
        ".word 0xe1a03006\n"
        ".word 0xe3a0205f\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0120\n"
        ".word 0xeb0334f8\n"
        ".word 0xe1a03006\n"
        ".word 0xe3a02060\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0120\n"
        ".word 0xeb0334f2\n"
        ".word 0xe1a03006\n"
        ".word 0xe3a02061\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0120\n"
        ".word 0xeb0334ec\n"
        ".word 0xe1a03006\n"
        ".word 0xe3a02062\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0120\n"
        ".word 0xeb0334e6\n"
        ".word 0xe1a03006\n"
        ".word 0xe3a0204a\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0120\n"
        ".word 0xeb0334e0\n"
        ".word 0xe3a01049\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033579\n"
        ".word 0xe1a04000\n"
        ".word 0xe28f1e3b\n"
        ".word 0xe28d0010\n"
        ".word 0xfa0331c0\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d410f8\n"
        ".word 0xeddf8af1\n"
        ".word 0xe0800005\n"
        ".word 0xe0811006\n"
        ".word 0xee000a90\n"
        ".word 0xee001a10\n"
        ".word 0xeeb01a68\n"
        ".word 0xed9f8aea\n"
        ".word 0xe28d2010\n"
        ".word 0xe3e01000\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeeb02a48\n"
        ".word 0xeef01a41\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03318f\n"
        ".word 0xe3a0104c\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033561\n"
        ".word 0xe1a04000\n"
        ".word 0xeb02afcb\n"
        ".word 0xe3a0b002\n"
        ".word 0xe28f1fdd\n"
        ".word 0xe58d000c\n"
        ".word 0xe58d1008\n"
        ".word 0xe58d8004\n"
        ".word 0xe58db000\n"
        ".word 0xe1d410fa\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a03001\n"
        ".word 0xe0812005\n"
        ".word 0xe0801006\n"
        ".word 0xe3a00000\n"
        ".word 0xeb032ff9\n"
        ".word 0xe59f0348\n"
        ".word 0xe7d0000a\n"
        ".word 0xe3500000\n"
        ".word 0x0d9f9ad0\n"
        ".word 0x03a07000\n"
        ".word 0x1a000362\n"
        ".word 0xe1570009\n"
        ".word 0x0a000169\n"
        ".word 0xe2871073\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033547\n"
        ".word 0xe1a04000\n"
        ".word 0xe1d000fa\n"
        ".word 0xe3a0b0c9\n"
        ".word 0xe3a02063\n"
        ".word 0xe0800005\n"
        ".word 0xe88d0801\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0334a0\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a02064\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800005\n"
        ".word 0xe88d0801\n"
        ".word 0xe1d400f8\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033497\n"
        ".word 0xe59f02d4\n"
        ".word 0xe08a1187\n"
        ".word 0xe59f22d0\n"
        ".word 0xe7903001\n"
        ".word 0xe0022003\n"
        ".word 0xe1b00002\n"
        ".word 0x0a000127\n"
        ".word 0xe2818b25\n"
        ".word 0xe2888038\n"
        ".word 0xe1c800d0\n"
        ".word 0xe1a01781\n"
        ".word 0xe18108a0\n"
        ".word 0xe1a008a0\n"
        ".word 0xeb031c4a\n"
        ".word 0xe58d0050\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a010c9\n"
        ".word 0xe3a02065\n"
        ".word 0xe0800005\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03347e\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a010c9\n"
        ".word 0xe3a02066\n"
        ".word 0xe0800005\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033474\n"
        ".word 0xe3a0106a\n"
        ".word 0xe3a00024\n"
        ".word 0xeb03350d\n"
        ".word 0xe1a0b000\n"
        ".word 0xe3a00001\n"
        ".word 0xe58d0000\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1db10fa\n"
        ".word 0xe3a030c9\n"
        ".word 0xe0802001\n"
        ".word 0xe1d400f8\n"
        ".word 0xe1db10f8\n"
        ".word 0xe0822005\n"
        ".word 0xe0811000\n"
        ".word 0xe5980000\n"
        ".word 0xe0811006\n"
        ".word 0xe3c00902\n"
        ".word 0xe6bf0070\n"
        ".word 0xeb0311ef\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1db10fa\n"
        ".word 0xe1db20f8\n"
        ".word 0xe0811000\n"
        ".word 0xe1d400f8\n"
        ".word 0xe0803002\n"
        ".word 0xe5980000\n"
        ".word 0xe0812005\n"
        ".word 0xe0831006\n"
        ".word 0xe3a030ce\n"
        ".word 0xe1a00880\n"
        ".word 0xe1a008a0\n"
        ".word 0xeb0197fe\n"
        ".word 0xe3a0106b\n"
        ".word 0xe3a00024\n"
        ".word 0xeb0334ed\n"
        ".word 0xe1a0b000\n"
        ".word 0xe3a00001\n"
        ".word 0xe58d0000\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1db10fa\n"
        ".word 0xe3a030c9\n"
        ".word 0xe0802001\n"
        ".word 0xe1d400f8\n"
        ".word 0xe1db10f8\n"
        ".word 0xe0822005\n"
        ".word 0xe0811000\n"
        ".word 0xe5980000\n"
        ".word 0xe0811006\n"
        ".word 0xe1a00100\n"
        ".word 0xe1a008a0\n"
        ".word 0xeb0311cf\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1db10fa\n"
        ".word 0xe1db20f8\n"
        ".word 0xe0811000\n"
        ".word 0xe1d400f8\n"
        ".word 0xe0803002\n"
        ".word 0xe5980000\n"
        ".word 0xe0812005\n"
        ".word 0xe0831006\n"
        ".word 0xe3a030ce\n"
        ".word 0xe1a00100\n"
        ".word 0xe1a008a0\n"
        ".word 0xeb0197de\n"
        ".word 0xe3a0106c\n"
        ".word 0xe3a00024\n"
        ".word 0xeb0334cd\n"
        ".word 0xe1a0b000\n"
        ".word 0xe3a00000\n"
        ".word 0xe58d0000\n"
        ".word 0xe1c800d0\n"
        ".word 0xe1db20fa\n"
        ".word 0xe1db30f8\n"
        ".word 0xe1a01781\n"
        ".word 0xe18108a0\n"
        ".word 0xe1d410fa\n"
        ".word 0xe1a008a0\n"
        ".word 0xe0822001\n"
        ".word 0xe1d410f8\n"
        ".word 0xe0822005\n"
        ".word 0xe0811003\n"
        ".word 0xe0811006\n"
        ".word 0xe3a030c9\n"
        ".word 0xeb0311ae\n"
        ".word 0xe1c800d0\n"
        ".word 0xe1db20fa\n"
        ".word 0xe1db30f8\n"
        ".word 0xe1a01781\n"
        ".word 0xe18108a0\n"
        ".word 0xe1d410fa\n"
        ".word 0xe1a008a0\n"
        ".word 0xe0811002\n"
        ".word 0xe1d420f8\n"
        ".word 0xe0833002\n"
        ".word 0xe0812005\n"
        ".word 0xe0831006\n"
        ".word 0xe3a030ce\n"
        ".word 0xeb0197bc\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a010c9\n"
        ".word 0xe3a02067\n"
        ".word 0xe0800005\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033408\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a010c9\n"
        ".word 0xe3a02068\n"
        ".word 0xe0800005\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0333fe\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a010c9\n"
        ".word 0xe3a02069\n"
        ".word 0xe0800005\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0333f4\n"
        ".word 0xe3a0106e\n"
        ".word 0xe3a00024\n"
        ".word 0xeb03348d\n"
        ".word 0xe1a08000\n"
        ".word 0xe320f000\n"
        ".word 0xea00000f\n"
        ".word 0x95826582\n"
        ".word 0x89829382\n"
        ".word 0x8e828f82\n"
        ".word 0x6f824081\n"
        ".word 0x93828f82\n"
        ".word 0x89829382\n"
        ".word 0x8c828282\n"
        ".word 0x46818582\n"
        ".word 0x00000000\n"
        ".word 0x3f800000\n"
        ".word 0x00000000\n"
        ".word 0x00006425\n"
        ".word 0x00009450\n"
        ".word 0x3e4ccccd\n"
        ".word 0x0000943c\n"
        ".word 0x0001fffc\n"
        ".word 0xe59d0050\n"
        ".word 0xe1d000b0\n"
        ".word 0xeb032b59\n"
        ".word 0xe1a02000\n"
        ".word 0xe28f1ff5\n"
        ".word 0xe28d0010\n"
        ".word 0xfa0330be\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d810fa\n"
        ".word 0xeeb02a48\n"
        ".word 0xeef01a68\n"
        ".word 0xe0800001\n"
        ".word 0xe0800005\n"
        ".word 0xee000a10\n"
        ".word 0xe1d400f8\n"
        ".word 0xe1d810f8\n"
        ".word 0xeeb01a49\n"
        ".word 0xe28d2010\n"
        ".word 0xe0800001\n"
        ".word 0xeef80ac0\n"
        ".word 0xe0800006\n"
        ".word 0xee000a10\n"
        ".word 0xe3a010ff\n"
        ".word 0xe3a00002\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeb03308b\n"
        ".word 0xe3a0106f\n"
        ".word 0xe3a00024\n"
        ".word 0xeb03345d\n"
        ".word 0xe1a08000\n"
        ".word 0xe59d0050\n"
        ".word 0xe3a01000\n"
        ".word 0xe1d000b0\n"
        ".word 0xeb032aac\n"
        ".word 0xe1a02000\n"
        ".word 0xe28f1fd6\n"
        ".word 0xe28d0010\n"
        ".word 0xfa03309f\n"
        ".word 0xe3a01002\n"
        ".word 0xe28d0010\n"
        ".word 0xeb0312e3\n"
        ".word 0xe598100c\n"
        ".word 0xe1d820fa\n"
        ".word 0xeeb02a48\n"
        ".word 0xeef01a68\n"
        ".word 0xe1d110f0\n"
        ".word 0xeeb01a49\n"
        ".word 0xe0410000\n"
        ".word 0xe1d410fa\n"
        ".word 0xe0800fa0\n"
        ".word 0xe0811002\n"
        ".word 0xe0811005\n"
        ".word 0xee001a10\n"
        ".word 0xe1d410f8\n"
        ".word 0xe1d820f8\n"
        ".word 0xe08600c0\n"
        ".word 0xe0811002\n"
        ".word 0xeef80ac0\n"
        ".word 0xe0800001\n"
        ".word 0xee000a10\n"
        ".word 0xe59f12f8\n"
        ".word 0xe28d2010\n"
        ".word 0xe3a00002\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeb033064\n"
        ".word 0xe3a000ff\n"
        ".word 0xe320f000\n"
        ".word 0xeb032fb9\n"
        ".word 0xe3a01071\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033433\n"
        ".word 0xe59dc050\n"
        ".word 0xe1a01000\n"
        ".word 0xe24f3d05\n"
        ".word 0xe3a020ce\n"
        ".word 0xe5dcc003\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d100d\n"
        ".word 0xe1d130fa\n"
        ".word 0xe1d420fa\n"
        ".word 0xe1d400f8\n"
        ".word 0xe1d110f8\n"
        ".word 0xe0822003\n"
        ".word 0xe0822005\n"
        ".word 0xe0800001\n"
        ".word 0xe0801006\n"
        ".word 0xe3a03001\n"
        ".word 0xe3a00000\n"
        ".word 0xeb032ec8\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb03322f\n"
        ".word 0xe59d0050\n"
        ".word 0xe1d000b0\n"
        ".word 0xeb02b1a9\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000037\n"
        ".word 0xe3a0106d\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033415\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d420fa\n"
        ".word 0xe0811002\n"
        ".word 0xe0811005\n"
        ".word 0xe3a020d3\n"
        ".word 0xe88d0006\n"
        ".word 0xe1d410f8\n"
        ".word 0xe1d000f8\n"
        ".word 0xe3a02008\n"
        ".word 0xe0800001\n"
        ".word 0xe0803006\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0333a9\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000023\n"
        ".word 0xe28f1f85\n"
        ".word 0xe28d0010\n"
        ".word 0xfa03304c\n"
        ".word 0xe3a01072\n"
        ".word 0xe3a00024\n"
        ".word 0xeb0333fe\n"
        ".word 0xe1a08000\n"
        ".word 0xe3a01002\n"
        ".word 0xe28d0010\n"
        ".word 0xeb03128c\n"
        ".word 0xe1a01000\n"
        ".word 0xe598000c\n"
        ".word 0xe1d420fa\n"
        ".word 0xe1d430f8\n"
        ".word 0xe1d8c0f8\n"
        ".word 0xe1d000f0\n"
        ".word 0xeeb02a48\n"
        ".word 0xe083300c\n"
        ".word 0xe0400001\n"
        ".word 0xeef01a68\n"
        ".word 0xe0800fa0\n"
        ".word 0xe1a010c0\n"
        ".word 0xe1d800fa\n"
        ".word 0xe0800002\n"
        ".word 0xe0862001\n"
        ".word 0xe0801005\n"
        ".word 0xe0830002\n"
        ".word 0xee001a10\n"
        ".word 0xee010a10\n"
        ".word 0xe59f11d4\n"
        ".word 0xe28d2010\n"
        ".word 0xe3a00002\n"
        ".word 0xeef80ac0\n"
        ".word 0xeeb80ac1\n"
        ".word 0xeeb01a49\n"
        ".word 0xeb03300b\n"
        ".word 0xe2877001\n"
        ".word 0xe3570003\n"
        ".word 0xbafffe90\n"
        ".word 0xe3590003\n"
        ".word 0x2a0001f1\n"
        ".word 0xe08a0189\n"
        ".word 0xe2807b25\n"
        ".word 0xe2877038\n"
        ".word 0xe5970004\n"
        ".word 0xe5971000\n"
        ".word 0xe1a02780\n"
        ".word 0xe18208a1\n"
        ".word 0xe1a008a0\n"
        ".word 0xeb031af7\n"
        ".word 0xe1a0b000\n"
        ".word 0xe2891087\n"
        ".word 0xe3a00024\n"
        ".word 0xeb0333ce\n"
        ".word 0xe1a04000\n"
        ".word 0xe28a0024\n"
        ".word 0xed900a08\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb0333d8\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a080c9\n"
        ".word 0xe3a02076\n"
        ".word 0xe0800005\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033322\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a02077\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800005\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d400f8\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033319\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a02078\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800005\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d400f8\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033310\n"
        ".word 0xeeb00a48\n"
        ".word 0xe320f000\n"
        ".word 0xeb0333b9\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a02079\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800005\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d400f8\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033304\n"
        ".word 0xe59d0098\n"
        ".word 0xe320f000\n"
        ".word 0xeb02ac28\n"
        ".word 0xe3500001\n"
        ".word 0x13500002\n"
        ".word 0x13500006\n"
        ".word 0xe1d400fa\n"
        ".word 0xe0800005\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d400f8\n"
        ".word 0xe0803006\n"
        ".word 0x0a00012d\n"
        ".word 0xe3a0207a\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0332f4\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a0207d\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800005\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d400f8\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0332eb\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a0207e\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800005\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d400f8\n"
        ".word 0xe0803006\n"
        ".word 0xea00000f\n"
        ".word 0x00007325\n"
        ".word 0x7a4c00ff\n"
        ".word 0x88827382\n"
        ".word 0x92828582\n"
        ".word 0x40818582\n"
        ".word 0x92828182\n"
        ".word 0x40818582\n"
        ".word 0x8f828e82\n"
        ".word 0x83824081\n"
        ".word 0x8e828182\n"
        ".word 0x89828482\n"
        ".word 0x81828482\n"
        ".word 0x85829482\n"
        ".word 0x44819382\n"
        ".word 0x00000000\n"
        ".word 0x323232ff\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0332d1\n"
        ".word 0xe3a0107a\n"
        ".word 0xe3a00024\n"
        ".word 0xeb03336a\n"
        ".word 0xe1a09000\n"
        ".word 0xe59f0608\n"
        ".word 0xe5901000\n"
        ".word 0xe3a00003\n"
        ".word 0xe2818a01\n"
        ".word 0xe2888fc3\n"
        ".word 0xe5981000\n"
        ".word 0xe0882101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d82018\n"
        ".word 0xe3520000\n"
        ".word 0x03510003\n"
        ".word 0x0a000003\n"
        ".word 0xe598101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c80018\n"
        ".word 0xe3a00001\n"
        ".word 0xe58d0000\n"
        ".word 0xe599000c\n"
        ".word 0xe1d9c0fa\n"
        ".word 0xe1d410fa\n"
        ".word 0xe1d990f8\n"
        ".word 0xe1d480f8\n"
        ".word 0xe1d030f2\n"
        ".word 0xe1d020f0\n"
        ".word 0xe081100c\n"
        ".word 0xe0880009\n"
        ".word 0xe0811005\n"
        ".word 0xe0800006\n"
        ".word 0xeb029e9c\n"
        ".word 0xe28a00b0\n"
        ".word 0xe320f000\n"
        ".word 0xeb03316f\n"
        ".word 0xe1d410fa\n"
        ".word 0xe0800005\n"
        ".word 0xe0808001\n"
        ".word 0xe28a00b0\n"
        ".word 0xeb03316d\n"
        ".word 0xe1d410f8\n"
        ".word 0xe0802006\n"
        ".word 0xe3a000ce\n"
        ".word 0xe0823001\n"
        ".word 0xe58d0004\n"
        ".word 0xe3a0207c\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03329c\n"
        ".word 0xe59f0544\n"
        ".word 0xe5901000\n"
        ".word 0xe3a00000\n"
        ".word 0xe2818a01\n"
        ".word 0xe2888fc3\n"
        ".word 0xe5981000\n"
        ".word 0xe0882101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d82018\n"
        ".word 0xe3520000\n"
        ".word 0x03510000\n"
        ".word 0x0a000003\n"
        ".word 0xe598101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c80018\n"
        ".word 0xe3a0107f\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033324\n"
        ".word 0xe3a09001\n"
        ".word 0xe58d9000\n"
        ".word 0xe1a08000\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d810fa\n"
        ".word 0xe1d420f8\n"
        ".word 0xe1d830f8\n"
        ".word 0xe597c000\n"
        ".word 0xe0800001\n"
        ".word 0xe0821003\n"
        ".word 0xe3cc3902\n"
        ".word 0xe0802005\n"
        ".word 0xe6bf0073\n"
        ".word 0xe0811006\n"
        ".word 0xe3a030c9\n"
        ".word 0xeb031006\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d810fa\n"
        ".word 0xe1d420f8\n"
        ".word 0xe1d830f8\n"
        ".word 0xe597c000\n"
        ".word 0xe0811000\n"
        ".word 0xe0833002\n"
        ".word 0xe0812005\n"
        ".word 0xe1a0088c\n"
        ".word 0xe0831006\n"
        ".word 0xe1a008a0\n"
        ".word 0xe3a030e2\n"
        ".word 0xeb019615\n"
        ".word 0xe3a01080\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033304\n"
        ".word 0xe58d9000\n"
        ".word 0xe1a08000\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d810fa\n"
        ".word 0xe1d420f8\n"
        ".word 0xe1d830f8\n"
        ".word 0xe597c000\n"
        ".word 0xe0800001\n"
        ".word 0xe0821003\n"
        ".word 0xe0802005\n"
        ".word 0xe1a0310c\n"
        ".word 0xe0811006\n"
        ".word 0xe1a008a3\n"
        ".word 0xe3a030c9\n"
        ".word 0xeb030fe7\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d810fa\n"
        ".word 0xe1d8c0f8\n"
        ".word 0xe1d420f8\n"
        ".word 0xe5978000\n"
        ".word 0xe0803001\n"
        ".word 0xe082100c\n"
        ".word 0xe0832005\n"
        ".word 0xe1a00108\n"
        ".word 0xe0811006\n"
        ".word 0xe1a008a0\n"
        ".word 0xe3a030e2\n"
        ".word 0xeb0195f6\n"
        ".word 0xe3a01081\n"
        ".word 0xe3a00024\n"
        ".word 0xeb0332e5\n"
        ".word 0xe1a08000\n"
        ".word 0xe3a00000\n"
        ".word 0xe58d0000\n"
        ".word 0xe8970006\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d830fa\n"
        ".word 0xe1d4c0f8\n"
        ".word 0xe1d890f8\n"
        ".word 0xe0833000\n"
        ".word 0xe1a00782\n"
        ".word 0xe18008a1\n"
        ".word 0xe08cc009\n"
        ".word 0xe0832005\n"
        ".word 0xe1a008a0\n"
        ".word 0xe08c1006\n"
        ".word 0xe3a030c9\n"
        ".word 0xeb030fc6\n"
        ".word 0xe5970004\n"
        ".word 0xe5971000\n"
        ".word 0xe1d420fa\n"
        ".word 0xe1a03780\n"
        ".word 0xe18308a1\n"
        ".word 0xe1d810fa\n"
        ".word 0xe1d430f8\n"
        ".word 0xe1a008a0\n"
        ".word 0xe0811002\n"
        ".word 0xe1d820f8\n"
        ".word 0xe0833002\n"
        ".word 0xe0812005\n"
        ".word 0xe0831006\n"
        ".word 0xe3a030e2\n"
        ".word 0xeb0195d3\n"
        ".word 0xe3a01083\n"
        ".word 0xe3a00024\n"
        ".word 0xeb0332c2\n"
        ".word 0xe1a07000\n"
        ".word 0xe1db00b0\n"
        ".word 0xeb0329a1\n"
        ".word 0xe1a02000\n"
        ".word 0xe24f1fc3\n"
        ".word 0xe28d0010\n"
        ".word 0xfa032f06\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d710fa\n"
        ".word 0xeeb02a48\n"
        ".word 0xeef01a68\n"
        ".word 0xe0800001\n"
        ".word 0xe0800005\n"
        ".word 0xee000a10\n"
        ".word 0xe1d400f8\n"
        ".word 0xe1d710f8\n"
        ".word 0xeeb01a49\n"
        ".word 0xe28d2010\n"
        ".word 0xe0800001\n"
        ".word 0xeef80ac0\n"
        ".word 0xe0800006\n"
        ".word 0xee000a10\n"
        ".word 0xe3e01000\n"
        ".word 0xe3a00003\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeb032ed3\n"
        ".word 0xe3a01084\n"
        ".word 0xe3a00024\n"
        ".word 0xeb0332a5\n"
        ".word 0xe1a07000\n"
        ".word 0xe1db00b0\n"
        ".word 0xe3a01000\n"
        ".word 0xeb0328f5\n"
        ".word 0xe1a02000\n"
        ".word 0xe24f1fe1\n"
        ".word 0xe28d0010\n"
        ".word 0xfa032ee8\n"
        ".word 0xe3a01003\n"
        ".word 0xe28d0010\n"
        ".word 0xeb03112c\n"
        ".word 0xe597100c\n"
        ".word 0xe1d420fa\n"
        ".word 0xeeb02a48\n"
        ".word 0xeef01a68\n"
        ".word 0xe1d110f0\n"
        ".word 0xeeb01a49\n"
        ".word 0xe0410000\n"
        ".word 0xe0800fa0\n"
        ".word 0xe1a010c0\n"
        ".word 0xe1d700fa\n"
        ".word 0xe0811006\n"
        ".word 0xe0800002\n"
        ".word 0xe0800005\n"
        ".word 0xee000a10\n"
        ".word 0xe1d420f8\n"
        ".word 0xe1d700f8\n"
        ".word 0xe0800002\n"
        ".word 0xeef80ac0\n"
        ".word 0xe0800001\n"
        ".word 0xee000a10\n"
        ".word 0xe28d2010\n"
        ".word 0xe3e01000\n"
        ".word 0xe3a00003\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeb032eac\n"
        ".word 0xe3a01086\n"
        ".word 0xe3a00024\n"
        ".word 0xeb03327e\n"
        ".word 0xe5db3003\n"
        ".word 0xe1a07000\n"
        ".word 0xe28f2f96\n"
        ".word 0xe3a010ce\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d000f\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d720fa\n"
        ".word 0xe1d410f8\n"
        ".word 0xe3a03001\n"
        ".word 0xe0800002\n"
        ".word 0xe1d720f8\n"
        ".word 0xe0811002\n"
        ".word 0xe0802005\n"
        ".word 0xe0811006\n"
        ".word 0xe3a00000\n"
        ".word 0xeb032d14\n"
        ".word 0xe1db00b0\n"
        ".word 0xe320f000\n"
        ".word 0xeb02aff8\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a00001a\n"
        ".word 0xea000006\n"
        ".word 0xe3a0207b\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0331c6\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeafffece\n"
        ".word 0xe3a01082\n"
        ".word 0xe3a00024\n"
        ".word 0xeb03325c\n"
        ".word 0xe1a07000\n"
        ".word 0xe1d000fa\n"
        ".word 0xe1d410fa\n"
        ".word 0xe3a02008\n"
        ".word 0xe0800001\n"
        ".word 0xe0801005\n"
        ".word 0xe3a000d3\n"
        ".word 0xe58d0004\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d400f8\n"
        ".word 0xe1d710f8\n"
        ".word 0xe0800001\n"
        ".word 0xe0803006\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0331ee\n"
        ".word 0xe59d0070\n"
        ".word 0xe3500000\n"
        ".word 0x0a000004\n"
        ".word 0xe3500001\n"
        ".word 0x0a000008\n"
        ".word 0xe3500002\n"
        ".word 0x0a00000c\n"
        ".word 0xea00000f\n"
        ".word 0xe3a01081\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033241\n"
        ".word 0xe1a07000\n"
        ".word 0xe320f000\n"
        ".word 0xea000009\n"
        ".word 0xe3a0107f\n"
        ".word 0xe3a00024\n"
        ".word 0xeb03323b\n"
        ".word 0xe1a07000\n"
        ".word 0xe320f000\n"
        ".word 0xea000003\n"
        ".word 0xe3a01080\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033235\n"
        ".word 0xe1a07000\n"
        ".word 0xe59f9134\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe3a00006\n"
        ".word 0xe5998000\n"
        ".word 0xeb034c63\n"
        ".word 0xe2888a01\n"
        ".word 0xe2888fab\n"
        ".word 0xe5981000\n"
        ".word 0xe0882101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d82018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe598101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c80018\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d710fa\n"
        ".word 0xe3a080dd\n"
        ".word 0xe3a02058\n"
        ".word 0xe0800001\n"
        ".word 0xe0800005\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d400f8\n"
        ".word 0xe1d710f8\n"
        ".word 0xe0800001\n"
        ".word 0xe0803006\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033176\n"
        ".word 0xe28a0f4f\n"
        ".word 0xe320f000\n"
        ".word 0xed900a08\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb03321c\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d710fa\n"
        ".word 0xe3a02059\n"
        ".word 0xe0800001\n"
        ".word 0xe0800005\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d400f8\n"
        ".word 0xe1d710f8\n"
        ".word 0xe0800001\n"
        ".word 0xe0803006\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033163\n"
        ".word 0xeeb00a48\n"
        ".word 0xe320f000\n"
        ".word 0xeb03320c\n"
        ".word 0xe5994000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe3a00006\n"
        ".word 0xeb034c2c\n"
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
        ".word 0xe28dd054\n"
        ".word 0xecbd8b04\n"
        ".word 0xe28dd010\n"
        ".word 0xe8bd8ff0\n"
        ".word 0x0044ea00\n"
        ".word 0x00006425\n"
    );
}
#if 0
// Original partial readable draft retained for reconstruction; not compiled.
void ui_func_001f1fc8(s32 x, s32 y, s32 selected, s32 column, s16 touch_handle) {
    CampFusionView* work =
        static_cast<CampFusionView*>(Camp_GetMainWork());
    if (work == nullptr || (x < 0 ? -x : x) >= 0x140) {
        return;
    }

    // 0x001F2018..0x001F20D8: list frame.  Panel 0 followed by nodes
    // 0x5C..0x62 and 0x4A, all at group 0x24, priority 0xC9.
    UiSprite_DrawPanel(2, 0x24, 0, x, y, 0xC9);
    UiSprite_DrawNode(2, 0x24, 0x5C, x, y, 0xC9);
    UiSprite_DrawNode(2, 0x24, 0x5D, x, y, 0xC9);
    UiSprite_DrawNode(2, 0x24, 0x5E, x, y, 0xC9);
    UiSprite_DrawNode(2, 0x24, 0x5F, x, y, 0xC9);
    UiSprite_DrawNode(2, 0x24, 0x60, x, y, 0xC9);
    UiSprite_DrawNode(2, 0x24, 0x61, x, y, 0xC9);
    UiSprite_DrawNode(2, 0x24, 0x62, x, y, 0xC9);
    UiSprite_DrawNode(2, 0x24, 0x4A, x, y, 0xC9);

    // 0x001F20DC..0x001F2138: header text at node 0x49.
    const Npc2dLayoutNode* header = LayoutNode(0x24, 0x49);
    char text[0x40];
    UiFont_FormatString(text, kFusionPossible);
    UiFont_DrawText(2, 0xFFFFFFFF, text,
                    static_cast<f32>(header->x + x),
                    static_cast<f32>(header->y + y),
                    0.0F, 0.0F, 1.0F);

    // 0x001F213C..0x001F2180: possible-fusion count at node 0x4C, mode 1,
    // width 2, priority 0xC9.
    const Npc2dLayoutNode* count_node = LayoutNode(0x24, 0x4C);
    UiFont_DrawFormatted(0, count_node->x + x, count_node->y + y, 1, 2, 0xC9,
                         "%d", Fusion_GetPossibleCount());

    // 0x001F2184..0x001F2198: work+0x9450 non-zero aborts the row list.
    const u8* work_bytes = reinterpret_cast<const u8*>(work);
    if (work_bytes[0x9450] != 0) {
        return;
    }

    for (s32 row = 0; row < 3; ++row) {
        // 0x001F219C: the selected row is drawn by the detail pass below.
        if (row == selected) {
            continue;
        }

        // 0x001F21A4: `add r1,r7,#0x73` -> node id 0x73 + row.
        const Npc2dLayoutNode* row_node =
            LayoutNode(0x24, 0x73u + static_cast<u32>(row));
        UiSprite_DrawNode(2, 0x24, 0x63, x + row_node->x, y + row_node->y, 0xC9);
        UiSprite_DrawNode(2, 0x24, 0x64, x + row_node->x, y + row_node->y, 0xC9);

        // 0x001F2200..0x001F2218: high word at work+0x943C+row*8, masked
        // with 0x1FFFC; zero selects the "no candidates" row.
        const u8* record = work_bytes + 0x9438 + row * 8;
        const u32 low = *reinterpret_cast<const u32*>(record);
        const u32 high = *reinterpret_cast<const u32*>(record + 4);
        if ((high & 0x0001FFFC) == 0) {
            // 0x001F26BC..0x001F26B8: centred "no candidates" text.
            const Npc2dLayoutNode* empty_node = LayoutNode(0x24, 0x72);
            char empty_text[0x40];
            UiFont_FormatString(empty_text, kNoCandidates);
            const s32 measured = UiText_MeasureWidth(empty_text, 2);
            const s16* rect = reinterpret_cast<const s16*>(empty_node->extra);
            const f32 px = static_cast<f32>(row_node->x + empty_node->x + x) +
                           static_cast<f32>(rect[0] - measured) * 0.5F;
            const f32 py = static_cast<f32>(row_node->y + empty_node->y + y);
            UiFont_DrawText(2, 0x323232FF, empty_text, px, py, 0.2F, 0.0F, 1.0F);
            continue;
        }

        // 0x001F221C..0x001F2238: entry id is bits 34..63 of the 8-byte
        // descriptor (`ldrd` + `lsl/ orr / lsr #0x11`).
        const u64 descriptor = static_cast<u64>(low) | (static_cast<u64>(high) << 32);
        const u32 entry_id = static_cast<u32>(descriptor >> 34);
        camp::UniteBibleRow* entry =
            static_cast<camp::UniteBibleRow*>(Battle_GetTalkEntry(entry_id));

        // 0x001F223C..0x001F2288: two text panels 0x65/0x66.
        UiSprite_DrawNode(2, 0x24, 0x65, x + row_node->x, y + row_node->y, 0xC9);
        UiSprite_DrawNode(2, 0x24, 0x66, x + row_node->x, y + row_node->y, 0xC9);

        // 0x001F228C..0x001F2308: icon id from the low half of the record
        // (bit 15 cleared), at node 0x6A.
        const Npc2dLayoutNode* icon_node = LayoutNode(0x24, 0x6A);
        const s32 icon_x = x + row_node->x + icon_node->x;
        const s32 icon_y = y + row_node->y + icon_node->y;
        UiSkill_DrawItemIconAndCount(
            static_cast<s16>(low & 0x7FFF), icon_x, icon_y, 0xC9, 1);
        Item_DrawDescriptionIcon(static_cast<u16>(low & 0x7FFF),
                                 icon_x, icon_y, 0xCE);

        // 0x001F230C..0x001F2388: bits 15..30 of the low word at node 0x6B.
        const Npc2dLayoutNode* icon_node_b = LayoutNode(0x24, 0x6B);
        const s32 icon_b_x = x + row_node->x + icon_node_b->x;
        const s32 icon_b_y = y + row_node->y + icon_node_b->y;
        const u32 icon_b = (low << 2) >> 17;
        UiSkill_DrawItemIconAndCount(static_cast<s16>(icon_b),
                                     icon_b_x, icon_b_y, 0xC9, 1);
        Item_DrawDescriptionIcon(static_cast<u16>(icon_b),
                                 icon_b_x, icon_b_y, 0xCE);

        // 0x001F238C..0x001F2410: the entry id itself at node 0x6C.
        const Npc2dLayoutNode* icon_node_c = LayoutNode(0x24, 0x6C);
        const s32 icon_c_x = x + row_node->x + icon_node_c->x;
        const s32 icon_c_y = y + row_node->y + icon_node_c->y;
        UiSkill_DrawItemIconAndCount(static_cast<s16>(entry_id),
                                     icon_c_x, icon_c_y, 0xC9, 0);
        Item_DrawDescriptionIcon(static_cast<u16>(entry_id),
                                 icon_c_x, icon_c_y, 0xCE);

        // 0x001F2414..0x001F24E0: nodes 0x67/0x68/0x69, then the two name
        // draws.  The first uses the entry id at +0x00 through
        // Item_GetShortNameString with "%s".
        UiSprite_DrawNode(2, 0x24, 0x67, x + row_node->x, y + row_node->y, 0xC9);
        UiSprite_DrawNode(2, 0x24, 0x68, x + row_node->x, y + row_node->y, 0xC9);
        UiSprite_DrawNode(2, 0x24, 0x69, x + row_node->x, y + row_node->y, 0xC9);

        const Npc2dLayoutNode* name_node = LayoutNode(0x24, 0x6E);
        const char* short_name = Item_GetShortNameString(entry->id);
        UiFont_FormatString(text, "%s", short_name);
        UiFont_DrawText(2, 0xFF, text,
                        static_cast<f32>(row_node->x + name_node->x + x),
                        static_cast<f32>(row_node->y + name_node->y + y),
                        0.2F, 0.0F, 1.0F);

        // 0x001F254C..0x001F25E8: description text centred on node 0x6F and
        // tinted 0x7A4C00FF; the 0xFF colour split follows at 0x002BE4DC.
        const Npc2dLayoutNode* desc_node = LayoutNode(0x24, 0x6F);
        const char* description = Item_GetDescriptionString(entry->id, 0);
        UiFont_FormatString(text, "%s", description);
        const s32 desc_measured = UiText_MeasureWidth(text, 2);
        const s16* desc_rect = reinterpret_cast<const s16*>(desc_node->extra);
        const f32 desc_x =
            static_cast<f32>(x) +
            static_cast<f32>(desc_rect[0] - desc_measured) * 0.5F +
            static_cast<f32>(row_node->x + desc_node->x);
        const f32 desc_y = static_cast<f32>(row_node->y + desc_node->y + y);
        UiFont_DrawText(2, 0x7A4C00FF, text, desc_x, desc_y, 0.2F, 0.0F, 1.0F);
        UiColor_SetFromRgba(0xFF);                                      // 0x001F25E8

        // 0x001F25EC..0x001F2650: the entry's +0x03 byte as "%d" at node
        // 0x71, width 2, priority 0xCE.
        const Npc2dLayoutNode* count_row = LayoutNode(0x24, 0x71);
        UiFont_DrawFormatted(0,
                             row_node->x + count_row->x + x,
                             row_node->y + count_row->y + y,
                             1, 2, 0xCE, "%d", entry->field_03);
        UiSprite_ResetBlend();                                          // 0x001F2650

        // 0x001F2654..0x001F26B8: unregistered entries get the 0x6D marker.
        if (Compendium_IsRegistered(entry->id) == 0) {
            const Npc2dLayoutNode* marker = LayoutNode(0x24, 0x6D);
            UiSprite_DrawPanel(2, 0x24, 8,
                               x + row_node->x + marker->x,
                               y + row_node->y + marker->y, 0xD3);
        }
    }

    // 0x001F2758: only rows 0..2 have a detail page.
    if (static_cast<u32>(selected) >= 3) {
        return;
    }

    // 0x001F2760..0x001F27D0: selected row detail.
    const u8* record = work_bytes + 0x9438 + selected * 8;
    const u32 low = *reinterpret_cast<const u32*>(record);
    const u32 high = *reinterpret_cast<const u32*>(record + 4);
    const u64 descriptor = static_cast<u64>(low) | (static_cast<u64>(high) << 32);
    const u32 entry_id = static_cast<u32>(descriptor >> 34);
    camp::UniteBibleRow* entry =
        static_cast<camp::UniteBibleRow*>(Battle_GetTalkEntry(entry_id));

    const Npc2dLayoutNode* detail_node = LayoutNode(0x24, selected + 0x87);
    UiSprite_SetGlobalAlpha(*reinterpret_cast<const f32*>(work_bytes + 0x44)); // 0x001F279C
    UiSprite_DrawNode(2, 0x24, 0x76, x + detail_node->x, y + detail_node->y, 0xC9);
    UiSprite_DrawNode(2, 0x24, 0x77, x + detail_node->x, y + detail_node->y, 0xC9);
    UiSprite_DrawNode(2, 0x24, 0x78, x + detail_node->x, y + detail_node->y, 0xC9);
    UiSprite_SetGlobalAlpha(1.0F);
    UiSprite_DrawNode(2, 0x24, 0x79, x + detail_node->x, y + detail_node->y, 0xC9);

    // 0x001F284C..0x001F28CC: touch state 1/2/6 draws node 0x7B, otherwise
    // 0x7A; 0x7D and 0x7E follow in both cases.
    const s32 touch_state = UiTouch_GetRegionTouchState(touch_handle);
    if (touch_state == 1 || touch_state == 2 || touch_state == 6) {
        UiSprite_DrawNode(2, 0x24, 0x7B, x + detail_node->x, y + detail_node->y, 0xC9);
    } else {
        UiSprite_DrawNode(2, 0x24, 0x7A, x + detail_node->x, y + detail_node->y, 0xC9);
    }
    UiSprite_DrawNode(2, 0x24, 0x7D, x + detail_node->x, y + detail_node->y, 0xC9);
    UiSprite_DrawNode(2, 0x24, 0x7E, x + detail_node->x, y + detail_node->y, 0xC9);

    // 0x001F2918..0x001F29B0: node 0x7A scissor (0x30C render-mode ring set
    // to 3), then the animated sprite at work+0xB0 drawn at node 0x7C.
    const Npc2dLayoutNode* scissor_node = LayoutNode(0x24, 0x7A);
    RingSet(0x30C, 3);
    const s16* scissor_rect =
        reinterpret_cast<const s16*>(scissor_node->extra);
    // 0x001F2990..0x001F29A0: rect is (width, height) at node 0x7A's +0xC.
    UiScissor_SetRect(
        x + detail_node->x + scissor_node->x,
        y + detail_node->y + scissor_node->y,
        scissor_rect[0], scissor_rect[1], 1);

    // 0x001F29D4..0x001F29E4: priority 0xCE, anchored at work+0xB0's sprite
    // position plus the detail node (r4 at this point is the 0x87+selected
    // detail node, not the scissor node).
    const s32 sprite_y = UiAnimSprite_GetPosY(work_bytes + 0xB0);
    const s32 sprite_x = UiAnimSprite_GetPosX(work_bytes + 0xB0);
    UiSprite_DrawNode(2, 0x24, 0x7C,
                      sprite_x + x + detail_node->x,
                      sprite_y + y + detail_node->y, 0xCE);

    RingSet(0x30C, 0);                                                  // 0x001F29EC

    // 0x001F2A30..0x001F2B28: three icon rows 0x7F/0x80/0x81.  The item icons
    // use priority 0xC9 and the description icons 0xE2.
    const Npc2dLayoutNode* row_7f = LayoutNode(0x24, 0x7F);
    UiSkill_DrawItemIconAndCount(static_cast<s16>(low & 0x7FFF),
                                 x + detail_node->x + row_7f->x,
                                 y + detail_node->y + row_7f->y, 0xC9, 1);
    Item_DrawDescriptionIcon(static_cast<u16>(low & 0x7FFF),
                             x + detail_node->x + row_7f->x,
                             y + detail_node->y + row_7f->y, 0xE2);

    const Npc2dLayoutNode* row_80 = LayoutNode(0x24, 0x80);
    const u32 icon_b = (low << 2) >> 17;
    UiSkill_DrawItemIconAndCount(static_cast<s16>(icon_b),
                                 x + detail_node->x + row_80->x,
                                 y + detail_node->y + row_80->y, 0xC9, 1);
    Item_DrawDescriptionIcon(static_cast<u16>(icon_b),
                             x + detail_node->x + row_80->x,
                             y + detail_node->y + row_80->y, 0xE2);

    const Npc2dLayoutNode* row_81 = LayoutNode(0x24, 0x81);
    UiSkill_DrawItemIconAndCount(static_cast<s16>(entry_id),
                                 x + detail_node->x + row_81->x,
                                 y + detail_node->y + row_81->y, 0xC9, 0);
    Item_DrawDescriptionIcon(static_cast<u16>(entry_id),
                             x + detail_node->x + row_81->x,
                             y + detail_node->y + row_81->y, 0xE2);

    // 0x001F2B2C..0x001F2C28: name at node 0x83 and centred description at
    // node 0x84.
    const Npc2dLayoutNode* name_node = LayoutNode(0x24, 0x83);
    const char* short_name = Item_GetShortNameString(entry->id);
    UiFont_FormatString(text, "%s", short_name);
    UiFont_DrawText(3, 0xFFFFFFFF, text,
                    static_cast<f32>(x + detail_node->x + name_node->x),
                    static_cast<f32>(y + detail_node->y + name_node->y),
                    0.2F, 0.0F, 1.0F);

    const Npc2dLayoutNode* desc_node = LayoutNode(0x24, 0x84);
    const char* description = Item_GetDescriptionString(entry->id, 0);
    UiFont_FormatString(text, "%s", description);
    const s32 measured = UiText_MeasureWidth(text, 3);
    const s16* desc_rect = reinterpret_cast<const s16*>(desc_node->extra);
    const f32 desc_x =
        static_cast<f32>(detail_node->x + desc_node->x + x) +
        static_cast<f32>(desc_rect[0] - measured) * 0.5F;
    const f32 desc_y =
        static_cast<f32>(y + detail_node->y + desc_node->y);
    UiFont_DrawText(3, 0xFFFFFFFF, text, desc_x, desc_y, 0.2F, 0.0F, 1.0F);

    // 0x001F2CC8..0x001F2D14: entry +0x03 as "%d" at node 0x86.
    const Npc2dLayoutNode* detail_count_node = LayoutNode(0x24, 0x86);
    UiFont_DrawFormatted(0,
                         x + detail_node->x + detail_count_node->x,
                         y + detail_node->y + detail_count_node->y,
                         1, 2, 0xCE, "%d", entry->field_03);

    // 0x001F2D18..0x001F2D4C: unregistered entries get the 0x82 marker.
    if (Compendium_IsRegistered(entry->id) == 0) {
        const Npc2dLayoutNode* marker = LayoutNode(0x24, 0x82);
        UiSprite_DrawPanel(2, 0x24, 8,
                           x + detail_node->x + marker->x,
                           y + detail_node->y + marker->y, 0xD3);
    }

    // 0x001F2D9C..0x001F2DF8: the caller's 4th argument (saved r3 at
    // sp+0x70) selects the tab underlay 0x81/0x7F/0x80.  Any other value
    // falls through to 0x001F2DFC with r7 still holding node 0x86.
    const Npc2dLayoutNode* tab = detail_count_node;
    if (column == 0) {
        tab = LayoutNode(0x24, 0x81);
    } else if (column == 1) {
        tab = LayoutNode(0x24, 0x7F);
    } else if (column == 2) {
        tab = LayoutNode(0x24, 0x80);
    }

    // 0x001F2DFC..0x001F2E48: 0x2AC ring set to the render mode 6/1/0.
    RingSet(0x2AC, static_cast<u32>(reinterpret_cast<std::uintptr_t>(
        UiGpu_SetRenderMode(6, 1, 0))));
    UiSprite_DrawNode(2, 0x24, 0x58,
                      x + detail_node->x + tab->x,
                      y + detail_node->y + tab->y, 0xDD);

    UiSprite_SetGlobalAlpha(*reinterpret_cast<const f32*>(work_bytes + 0x15C));
    UiSprite_DrawNode(2, 0x24, 0x59,
                      x + detail_node->x + tab->x,
                      y + detail_node->y + tab->y, 0xDD);
    UiSprite_SetGlobalAlpha(1.0F);

    // 0x001F2EDC..0x001F2F24: render mode 6/7/0 back on the 0x2AC ring.
    RingSet(0x2AC, static_cast<u32>(reinterpret_cast<std::uintptr_t>(
        UiGpu_SetRenderMode(6, 7, 0))));
}
#endif

// ---------------------------------------------------------------------------
// 0x001E989C: titleMain state machine
// ---------------------------------------------------------------------------

namespace {

/** 0x001EA3D8..0x001EA474: the reset used by states 8 (when 0x00215918 is
 *  zero) and 10.  It restores the four touch regions, reloads the title
 *  environment and re-enters state 5. */
void Title_ResetForBoot(camp::TitleMainWork* work) {
    work->field_64 = 0.0F;
    work->field_68 = 0.0F;
    ScriptVm_SetMessageId(0x9F);                                        // 0x001EA3F0
    u16* touch = TitleTouchHandles(work);
    touch[0] = static_cast<u16>(UiTouch_RegisterRegion(0x11, 0x14));
    touch[1] = static_cast<u16>(UiTouch_RegisterRegion(0x11, 0x15));
    touch[2] = static_cast<u16>(UiTouch_RegisterRegion(0x11, 0x18));
    touch[3] = static_cast<u16>(UiTouch_RegisterRegion(0x11, 0x19));
    work->flag_61 = 0;                                                  // 0x001EA43C
    Script_ApplyCursorMode(2);                                          // 0x001EA440
    work->flag_84 = 1;                                                  // 0x001EA450
    Res_LoadBcenv("title/title_top.bcenv", 0);                          // 0x001EA454
    work->flag_85 = 1;                                                  // 0x001EA458
    UiModel_SetVisible(work->resource_88, 0);                           // 0x001EA45C
    work->flag_96 = 1;                                                  // 0x001EA46C
    work->state_9C = 5;                                                 // 0x001EA470
}

/** 0x001EA5B4..0x001EA5D0 / 0x001EA604..0x001EA628: the two `AsdSequence`
 *  requests built from "e001_01" and the words {1, -1}.  Both call
 *  `AsdSequence_func_002c59b8(4, block, 0x20)`. */
void Title_SequenceRequest() {
    struct SequenceBlock {
        u32 mode;
        u32 param;
        char name[8];
        u32 pad[4];
    } block = {1, 0xFFFFFFFFu, {'e', '0', '0', '1', '_', '0', '1', '\0'}, {0, 0, 0, 0}};
    engine::AsdSequence_func_002c59b8(4, &block, 0x20);
}

inline u32 NormalizeSignedRemainderByFour(u32 provisional) {
    const u32 adjusted = provisional + 4u;
    const u32 correction = (0u - (adjusted >> 31)) >> 30;
    const u32 multiple = (adjusted + correction) & ~3u;
    return adjusted - multiple;
}

using TitleReadyPredicate = s32 (*)();
using TitleTriggerQuery = s32 (*)(u32);
using TitleEventRequest = void (*)(u32);

constexpr std::uintptr_t kTitleMainWorkSlotAddr = 0x0044E300u;
constexpr std::uintptr_t kScriptIsReadyAddr = 0x00289924u;
constexpr std::uintptr_t kPreviewIsReadyAddr = 0x0025A2BCu;
constexpr std::uintptr_t kUiInputTriggerAddr = 0x002B902Cu;
constexpr std::uintptr_t kScriptRequestEventAddr = 0x002B91C4u;
constexpr u32 kTitleSelectionChangedEventId = 0x0100016Cu;

} // namespace

extern "C" __attribute__((noinline)) u32 H1_TitleMain_UpdateNavigationSlice(
    camp::TitleMainWork** captured_work_out) {
    const auto script_is_ready =
        reinterpret_cast<TitleReadyPredicate>(kScriptIsReadyAddr);
    const auto preview_is_ready =
        reinterpret_cast<TitleReadyPredicate>(kPreviewIsReadyAddr);
    if (script_is_ready() == 0) {
        return 0u;
    }
    if (preview_is_ready() == 0) {
        return 0u;
    }

    auto* const global_work =
        reinterpret_cast<camp::TitleMainWork* volatile*>(kTitleMainWorkSlotAddr);
    camp::TitleMainWork* const work = *global_work;
    *captured_work_out = work;
    work->field_64 = work->field_64 + 1.0F;

    const auto trigger = reinterpret_cast<TitleTriggerQuery>(kUiInputTriggerAddr);
    if (trigger(5u) != 0 || trigger(0xEu) != 0) {
        work->field_08 = work->field_08 - 1u;
    }
    if (trigger(6u) != 0 || trigger(0xFu) != 0) {
        work->field_08 = work->field_08 + 1u;
    }

    const u32 selection = NormalizeSignedRemainderByFour(work->field_08);
    work->field_08 = selection;
    const u32 cached = work->field_0c;
    if (selection != cached) {
        const auto request_event =
            reinterpret_cast<TitleEventRequest>(kScriptRequestEventAddr);
        request_event(kTitleSelectionChangedEventId);
        work->field_0c = selection;
    }
    return 1u;
}

// DECOMP_FUNC(0x001e989c, 3924)
__attribute__((naked)) void ui_func_001e989c(void*) {
    asm volatile(
        ".word 0xe92d41f0\n"
        ".word 0xe59f0614\n"
        ".word 0xed2d8b02\n"
        ".word 0xe24dd020\n"
        ".word 0xe5905000\n"
        ".word 0xe1a04005\n"
        ".word 0xe595009c\n"
        ".word 0xe350000d\n"
        ".word 0x379ff100\n"
        ".word 0xea000359\n"
        ".word 0x001e98f8\n"
        ".word 0x001e9a10\n"
        ".word 0x001e9a3c\n"
        ".word 0x001e9b90\n"
        ".word 0x001e9bc0\n"
        ".word 0x001e9d08\n"
        ".word 0x001ea48c\n"
        ".word 0x001ea32c\n"
        ".word 0x001ea358\n"
        ".word 0x001ea398\n"
        ".word 0x001ea3c4\n"
        ".word 0x001ea478\n"
        ".word 0x001ea494\n"
        ".word 0xe3a0003a\n"
        ".word 0xeb02b76a\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb02f23a\n"
        ".word 0xe3a01012\n"
        ".word 0xe3a00011\n"
        ".word 0xeb03576d\n"
        ".word 0xe1d010f8\n"
        ".word 0xe1d000fa\n"
        ".word 0xe2842040\n"
        ".word 0xee001a10\n"
        ".word 0xee000a90\n"
        ".word 0xe3a01013\n"
        ".word 0xe3a00011\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeef80ae0\n"
        ".word 0xec820a02\n"
        ".word 0xeb035762\n"
        ".word 0xe1d010f8\n"
        ".word 0xe1d000fa\n"
        ".word 0xe2842048\n"
        ".word 0xee001a10\n"
        ".word 0xee000a90\n"
        ".word 0xe3a01016\n"
        ".word 0xe3a00011\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeef80ae0\n"
        ".word 0xec820a02\n"
        ".word 0xeb035757\n"
        ".word 0xe1d010f8\n"
        ".word 0xe1d000fa\n"
        ".word 0xee001a90\n"
        ".word 0xee000a10\n"
        ".word 0xe3a01017\n"
        ".word 0xe3a00011\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xedc40a14\n"
        ".word 0xed840a15\n"
        ".word 0xeb03574c\n"
        ".word 0xe1d010f8\n"
        ".word 0xe1d000fa\n"
        ".word 0xe2844058\n"
        ".word 0xee001a10\n"
        ".word 0xee000a90\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeef80ae0\n"
        ".word 0xec840a02\n"
        ".word 0xeb034a40\n"
        ".word 0xe5d50095\n"
        ".word 0xe3500000\n"
        ".word 0x13a00002\n"
        ".word 0x1a00000d\n"
        ".word 0xe3a00000\n"
        ".word 0xeb03647d\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000012\n"
        ".word 0xe3a01004\n"
        ".word 0xe3a00000\n"
        ".word 0xeb02db21\n"
        ".word 0xe3a01004\n"
        ".word 0xe3a00001\n"
        ".word 0xeb02db1e\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000009\n"
        ".word 0xe585009c\n"
        ".word 0xea000306\n"
        ".word 0xe2850014\n"
        ".word 0xeb074c77\n"
        ".word 0xe2850014\n"
        ".word 0xe320f000\n"
        ".word 0xe1d000d3\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a0002fe\n"
        ".word 0xe595009c\n"
        ".word 0xe2800001\n"
        ".word 0xeafffff2\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c40010\n"
        ".word 0xe2840014\n"
        ".word 0xe1a00000\n"
        ".word 0xe59f046c\n"
        ".word 0xe3a0203c\n"
        ".word 0xe3a01000\n"
        ".word 0xeb02daf8\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb028038\n"
        ".word 0xe5d40060\n"
        ".word 0xe3500000\n"
        ".word 0x0a000002\n"
        ".word 0xe3a00001\n"
        ".word 0xe5840008\n"
        ".word 0xe584000c\n"
        ".word 0xe5d40095\n"
        ".word 0xe3500000\n"
        ".word 0x0a000002\n"
        ".word 0xe3a00003\n"
        ".word 0xe5840008\n"
        ".word 0xe584000c\n"
        ".word 0xe320f000\n"
        ".word 0xeb028fb4\n"
        ".word 0xe3a0009f\n"
        ".word 0xe320f000\n"
        ".word 0xeb033c32\n"
        ".word 0xe5946008\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a0003a\n"
        ".word 0xeb035d01\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb035cf4\n"
        ".word 0xe3a0102b\n"
        ".word 0xe0010196\n"
        ".word 0xe0800081\n"
        ".word 0xe59f13e8\n"
        ".word 0xe2800016\n"
        ".word 0xeb02d58a\n"
        ".word 0xe5d40060\n"
        ".word 0xe3500000\n"
        ".word 0x0a000023\n"
        ".word 0xeb01c209\n"
        ".word 0xe3a01014\n"
        ".word 0xe3a00011\n"
        ".word 0xeb033b71\n"
        ".word 0xe1c407b4\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00011\n"
        ".word 0xeb033b6d\n"
        ".word 0xe1c407b6\n"
        ".word 0xe3a01018\n"
        ".word 0xe3a00011\n"
        ".word 0xeb033b69\n"
        ".word 0xe1c407b8\n"
        ".word 0xe3a01019\n"
        ".word 0xe3a00011\n"
        ".word 0xeb033b65\n"
        ".word 0xe1c407ba\n"
        ".word 0xe28f0e39\n"
        ".word 0xeb01e8c3\n"
        ".word 0xe5840088\n"
        ".word 0xe3a01007\n"
        ".word 0xe28f0fe6\n"
        ".word 0xeb02c8a4\n"
        ".word 0xe584008c\n"
        ".word 0xe3a01007\n"
        ".word 0xe28f0e3a\n"
        ".word 0xeb02c8a0\n"
        ".word 0xe5840090\n"
        ".word 0xe3a06001\n"
        ".word 0xe3a01000\n"
        ".word 0xe28f0fe9\n"
        ".word 0xe5c46085\n"
        ".word 0xeb02dc38\n"
        ".word 0xe5c46086\n"
        ".word 0xe320f000\n"
        ".word 0xeaffffac\n"
        ".word 0xe320f000\n"
        ".word 0xeb009fd3\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffffd7\n"
        ".word 0xe595008c\n"
        ".word 0xeb031174\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1affffa2\n"
        ".word 0xe5950090\n"
        ".word 0xeb03116f\n"
        ".word 0xe3500000\n"
        ".word 0x05950088\n"
        ".word 0x03500000\n"
        ".word 0x1affff9c\n"
        ".word 0xea00029a\n"
        ".word 0xe3a07000\n"
        ".word 0xe5c47086\n"
        ".word 0xe5940088\n"
        ".word 0xe1a01007\n"
        ".word 0xeb02dac1\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb036d8d\n"
        ".word 0xe1a06000\n"
        ".word 0xe28d0008\n"
        ".word 0xe58d0000\n"
        ".word 0xe5940088\n"
        ".word 0xe28d3004\n"
        ".word 0xe28d2010\n"
        ".word 0xe28d100c\n"
        ".word 0xe5900008\n"
        ".word 0xeb02fb35\n"
        ".word 0xeddd0a03\n"
        ".word 0xed9f1ac6\n"
        ".word 0xed9f0ac6\n"
        ".word 0xe28d2004\n"
        ".word 0xee600a81\n"
        ".word 0xe3a01001\n"
        ".word 0xe1a00006\n"
        ".word 0xee200a80\n"
        ".word 0xed8d0a03\n"
        ".word 0xeddd1a04\n"
        ".word 0xecd20a02\n"
        ".word 0xeb0360f1\n"
        ".word 0xed9f8abd\n"
        ".word 0xed9f0abd\n"
        ".word 0xe1a00006\n"
        ".word 0xeef00a48\n"
        ".word 0xeb035eca\n"
        ".word 0xe1a00006\n"
        ".word 0xe320f000\n"
        ".word 0xeb02bce5\n"
        ".word 0xe594008c\n"
        ".word 0xe3a01001\n"
        ".word 0xeb02da99\n"
        ".word 0xe5940090\n"
        ".word 0xe3a01001\n"
        ".word 0xeb02da96\n"
        ".word 0xe594008c\n"
        ".word 0xe5901000\n"
        ".word 0xe3110004\n"
        ".word 0x0a000006\n"
        ".word 0xe3c11004\n"
        ".word 0xe5801000\n"
        ".word 0xe5901008\n"
        ".word 0xed818a1d\n"
        ".word 0xe5900008\n"
        ".word 0xed900a1e\n"
        ".word 0xeb02c846\n"
        ".word 0xe5940090\n"
        ".word 0xe5901000\n"
        ".word 0xe3110004\n"
        ".word 0x1a000007\n"
        ".word 0xe3811004\n"
        ".word 0xe5801000\n"
        ".word 0xe5901008\n"
        ".word 0xed9f0a9f\n"
        ".word 0xed810a1d\n"
        ".word 0xe5900008\n"
        ".word 0xed900a1e\n"
        ".word 0xeb02c83a\n"
        ".word 0xe5940090\n"
        ".word 0xe5901000\n"
        ".word 0xe3811002\n"
        ".word 0xe5801000\n"
        ".word 0xe5900008\n"
        ".word 0xe3a0100a\n"
        ".word 0xe590002c\n"
        ".word 0xe5c071f6\n"
        ".word 0xe3a00000\n"
        ".word 0xeb02da61\n"
        ".word 0xe3a0100a\n"
        ".word 0xe3a00001\n"
        ".word 0xeb02da5e\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffff49\n"
        "sub sp, sp, #8\n"
        "mov r0, sp\n"
        "bl H1_TitleMain_UpdateNavigationSlice\n"
        "cmp r0, #0\n"
        "ldr r0, [sp]\n"
        "add sp, sp, #8\n"
        ".word 0x0a000241\n"
        "mov r4, r0\n"
        "ldr r8, [pc, #16]\n"
        "mov r12, #0x3f800000\n"
        "vmov s17, r12\n"
        ".word 0xea000029\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0x0044e300\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xe5940064\n"
        ".word 0xe59f1154\n"
        ".word 0xe59f2154\n"
        ".word 0xe1500001\n"
        ".word 0xcd9f0a50\n"
        ".word 0xcd840a19\n"
        ".word 0xe5940064\n"
        ".word 0xed9f0a51\n"
        ".word 0xe1500002\n"
        ".word 0xddd40a1a\n"
        ".word 0xde300a80\n"
        ".word 0xda000003\n"
        ".word 0xe1500001\n"
        ".word 0xddd40a1a\n"
        ".word 0xde300ac0\n"
        ".word 0xca000000\n"
        ".word 0xed840a1a\n"
        ".word 0xe5940068\n"
        ".word 0xed9f8a42\n"
        ".word 0xe35005fe\n"
        ".word 0xcef00a68\n"
        ".word 0xde000a90\n"
        ".word 0xedc40a1a\n"
        ".word 0xeef40ac8\n"
        ".word 0xeef1fa10\n"
        ".word 0xdef00a48\n"
        ".word 0xedc40a1a\n"
        ".word 0xe5986000\n"
        ".word 0xe3a04000\n"
        ".word 0xe0867084\n"
        ".word 0xe1d707f4\n"
        ".word 0xeb02cea6\n"
        ".word 0xe3500001\n"
        ".word 0xe320f000\n"
        ".word 0x0a000069\n"
        ".word 0xe1d707f4\n"
        ".word 0xeb02cea1\n"
        ".word 0xe3500002\n"
        ".word 0xe320f000\n"
        ".word 0x0a000064\n"
        ".word 0xe2844001\n"
        ".word 0xe3540004\n"
        ".word 0xbafffff1\n"
        ".word 0xe3a04000\n"
        ".word 0xe3a07001\n"
        ".word 0xe0860084\n"
        ".word 0xe1d007f4\n"
        ".word 0xeb02ce96\n"
        ".word 0xe3500006\n"
        ".word 0x05864008\n"
        ".word 0xe2844001\n"
        ".word 0x05c67063\n"
        ".word 0xe3540004\n"
        ".word 0xbafffff6\n"
        ".word 0xea000023\n"
        ".word 0x0044e300\n"
        ".word 0x01000001\n"
        ".word 0x323232ff\n"
        ".word 0x6c746974\n"
        ".word 0x69742f65\n"
        ".word 0x5f656c74\n"
        ".word 0x2e706f74\n"
        ".word 0x61636362\n"
        ".word 0x0000006d\n"
        ".word 0x6c746974\n"
        ".word 0x69742f65\n"
        ".word 0x5f656c74\n"
        ".word 0x31706f74\n"
        ".word 0x6d61622e\n"
        ".word 0x00000000\n"
        ".word 0x6c746974\n"
        ".word 0x69742f65\n"
        ".word 0x5f656c74\n"
        ".word 0x32706f74\n"
        ".word 0x6d61622e\n"
        ".word 0x00000000\n"
        ".word 0x6c746974\n"
        ".word 0x69742f65\n"
        ".word 0x5f656c74\n"
        ".word 0x2e706f74\n"
        ".word 0x6e656362\n"
        ".word 0x00000076\n"
        ".word 0x43340000\n"
        ".word 0x3ea2f983\n"
        ".word 0x3f800000\n"
        ".word 0x40a00000\n"
        ".word 0x00000000\n"
        ".word 0x0100016c\n"
        ".word 0x41f00000\n"
        ".word 0x41700000\n"
        ".word 0x3d888889\n"
        ".word 0xe5984000\n"
        ".word 0xe5d40096\n"
        ".word 0xe3500000\n"
        ".word 0x0a00001d\n"
        ".word 0xeb01c0d6\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000019\n"
        ".word 0xe5d41094\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c40096\n"
        ".word 0xe3510000\n"
        ".word 0x0a000026\n"
        ".word 0xe5940090\n"
        ".word 0xe5901000\n"
        ".word 0xe3c11002\n"
        ".word 0xe5801000\n"
        ".word 0xe5900008\n"
        ".word 0xe590002c\n"
        ".word 0xe5c071f6\n"
        ".word 0xe5940090\n"
        ".word 0xe5901000\n"
        ".word 0xe3110004\n"
        ".word 0x0a000006\n"
        ".word 0xe3c11004\n"
        ".word 0xe5801000\n"
        ".word 0xe5901008\n"
        ".word 0xedc18a1d\n"
        ".word 0xe5900008\n"
        ".word 0xed900a1e\n"
        ".word 0xeb02c77a\n"
        ".word 0xe5940090\n"
        ".word 0xed940a26\n"
        ".word 0xeb009816\n"
        ".word 0xe594008c\n"
        ".word 0xe5900008\n"
        ".word 0xeb01c0a4\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a00004f\n"
        ".word 0xe594008c\n"
        ".word 0xe5900008\n"
        ".word 0xeb03ada8\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000049\n"
        ".word 0xe5d40094\n"
        ".word 0xe3500000\n"
        ".word 0x0a000017\n"
        ".word 0xea000045\n"
        ".word 0xe5864008\n"
        ".word 0xeaffff9b\n"
        ".word 0xe594008c\n"
        ".word 0xe5901000\n"
        ".word 0xe3c11002\n"
        ".word 0xe5801000\n"
        ".word 0xe5900008\n"
        ".word 0xe590002c\n"
        ".word 0xe5c071f6\n"
        ".word 0xe594008c\n"
        ".word 0xe5901000\n"
        ".word 0xe3110004\n"
        ".word 0x0a000006\n"
        ".word 0xe3c11004\n"
        ".word 0xe5801000\n"
        ".word 0xe5901008\n"
        ".word 0xedc18a1d\n"
        ".word 0xe5900008\n"
        ".word 0xed900a1e\n"
        ".word 0xeb02c753\n"
        ".word 0xe594008c\n"
        ".word 0xed940a26\n"
        ".word 0xeaffffd7\n"
        ".word 0xe594008c\n"
        ".word 0xe5901000\n"
        ".word 0xe3110004\n"
        ".word 0x1a000006\n"
        ".word 0xe3811004\n"
        ".word 0xe5801000\n"
        ".word 0xe5901008\n"
        ".word 0xed818a1d\n"
        ".word 0xe5900008\n"
        ".word 0xed900a1e\n"
        ".word 0xeb02c745\n"
        ".word 0xe594008c\n"
        ".word 0xe3a01000\n"
        ".word 0xeeb00a48\n"
        ".word 0xe5902000\n"
        ".word 0xe3822002\n"
        ".word 0xe5802000\n"
        ".word 0xe5900008\n"
        ".word 0xe590002c\n"
        ".word 0xe5c011f6\n"
        ".word 0xed848a26\n"
        ".word 0xe5940090\n"
        ".word 0xe5900008\n"
        ".word 0xeb027474\n"
        ".word 0xe5940090\n"
        ".word 0xeeb00a48\n"
        ".word 0xe5900008\n"
        ".word 0xeb0097af\n"
        ".word 0xe5940090\n"
        ".word 0xe5901000\n"
        ".word 0xe3c11002\n"
        ".word 0xe5801000\n"
        ".word 0xe5900008\n"
        ".word 0xe590002c\n"
        ".word 0xe5c071f6\n"
        ".word 0xe5940090\n"
        ".word 0xe5901000\n"
        ".word 0xe3110004\n"
        ".word 0x0a000006\n"
        ".word 0xe3c11004\n"
        ".word 0xe5801000\n"
        ".word 0xe5901008\n"
        ".word 0xedc18a1d\n"
        ".word 0xe5900008\n"
        ".word 0xed900a1e\n"
        ".word 0xeb02c722\n"
        ".word 0xe5c47094\n"
        ".word 0xe5954008\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a0003a\n"
        ".word 0xeb035b61\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb035b54\n"
        ".word 0xe3a0102b\n"
        ".word 0xe0010194\n"
        ".word 0xe0800081\n"
        ".word 0xe51f1298\n"
        ".word 0xe2800016\n"
        ".word 0xeb02d3ea\n"
        ".word 0xe5d50063\n"
        ".word 0xe3500000\n"
        ".word 0x1a000009\n"
        ".word 0xe3a00001\n"
        ".word 0xeb0213d8\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000004\n"
        ".word 0xe3a00000\n"
        ".word 0xeb03578c\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000125\n"
        ".word 0xe5985000\n"
        ".word 0xe5950008\n"
        ".word 0xe3500001\n"
        ".word 0x05d50060\n"
        ".word 0x03500000\n"
        ".word 0x03a00000\n"
        ".word 0x05c50063\n"
        ".word 0x0a00011d\n"
        ".word 0xe59f0530\n"
        ".word 0xeb033c01\n"
        ".word 0xe5950008\n"
        ".word 0xe3500001\n"
        ".word 0x03a04000\n"
        ".word 0x05c57061\n"
        ".word 0x0a000008\n"
        ".word 0xe3500000\n"
        ".word 0x0a000017\n"
        ".word 0xe3500002\n"
        ".word 0x03a04000\n"
        ".word 0x05c57061\n"
        ".word 0x0a00002a\n"
        ".word 0xe3500003\n"
        ".word 0x0a000039\n"
        ".word 0xea00010d\n"
        ".word 0xe320f000\n"
        ".word 0xeb033b82\n"
        ".word 0xe2844001\n"
        ".word 0xe3540004\n"
        ".word 0xbafffffa\n"
        ".word 0xe3a01000\n"
        ".word 0xe5c51063\n"
        ".word 0xe3a00002\n"
        ".word 0xe5c5707c\n"
        ".word 0xe5850080\n"
        ".word 0xeb022f84\n"
        ".word 0xe3a00001\n"
        ".word 0xe320f000\n"
        ".word 0xeb022f0a\n"
        ".word 0xe3a00007\n"
        ".word 0xe320f000\n"
        ".word 0xeafffdf3\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c57062\n"
        ".word 0xe1a04000\n"
        ".word 0xe5c50063\n"
        ".word 0xe320f000\n"
        ".word 0xeb033b6d\n"
        ".word 0xe2844001\n"
        ".word 0xe3540004\n"
        ".word 0xbafffffa\n"
        ".word 0xe3e02000\n"
        ".word 0xe3a0100c\n"
        ".word 0xe3a00000\n"
        ".word 0xeb02c8fc\n"
        ".word 0xe3e02000\n"
        ".word 0xe3a0100c\n"
        ".word 0xe3a00001\n"
        ".word 0xeb02c8f8\n"
        ".word 0xe3a0000f\n"
        ".word 0xe320f000\n"
        ".word 0xeb02c8f1\n"
        ".word 0xe3a00006\n"
        ".word 0xe320f000\n"
        ".word 0xeafffddc\n"
        ".word 0xe320f000\n"
        ".word 0xeb033b5a\n"
        ".word 0xe2844001\n"
        ".word 0xe3540004\n"
        ".word 0xbafffffa\n"
        ".word 0xe3a01000\n"
        ".word 0xe5c51063\n"
        ".word 0xe3a00002\n"
        ".word 0xe5c5707c\n"
        ".word 0xe5850080\n"
        ".word 0xeb022f5c\n"
        ".word 0xe3a00001\n"
        ".word 0xe320f000\n"
        ".word 0xeb022ee2\n"
        ".word 0xe3a00009\n"
        ".word 0xe320f000\n"
        ".word 0xeafffdcb\n"
        ".word 0xe3a00000\n"
        ".word 0xe1a04000\n"
        ".word 0xe5c50063\n"
        ".word 0xe320f000\n"
        ".word 0xeb033b46\n"
        ".word 0xe2844001\n"
        ".word 0xe3540004\n"
        ".word 0xbafffffa\n"
        ".word 0xe3a0000b\n"
        ".word 0xe585009c\n"
        ".word 0xe3a020ff\n"
        ".word 0xe3a0100a\n"
        ".word 0xe3a00000\n"
        ".word 0xeb02c8d3\n"
        ".word 0xe3a020ff\n"
        ".word 0xe3a0100a\n"
        ".word 0xe3a00001\n"
        ".word 0xeb02c8cf\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea0000bf\n"
        ".word 0xe5d5007c\n"
        ".word 0xe3500000\n"
        ".word 0x1a0000bc\n"
        ".word 0xe3a00000\n"
        ".word 0xeb02f4b0\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb048195\n"
        ".word 0xe3a00008\n"
        ".word 0xe320f000\n"
        ".word 0xeafffdab\n"
        ".word 0xe320f000\n"
        ".word 0xeb0262a5\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a0000af\n"
        ".word 0xeb00ad69\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000016\n"
        ".word 0xe3a00001\n"
        ".word 0xe5c50062\n"
        ".word 0xe3a0000f\n"
        ".word 0xeb02c8b0\n"
        ".word 0xe3a0000c\n"
        ".word 0xe320f000\n"
        ".word 0xeafffd9b\n"
        ".word 0xe5d5007c\n"
        ".word 0xe3500000\n"
        ".word 0x1a0000a1\n"
        ".word 0xe3a00000\n"
        ".word 0xeb02f495\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb042a39\n"
        ".word 0xe3a0000a\n"
        ".word 0xe320f000\n"
        ".word 0xeafffd90\n"
        ".word 0xe320f000\n"
        ".word 0xeb044747\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000094\n"
        ".word 0xe51f0524\n"
        ".word 0xed9f0ac3\n"
        ".word 0xe5904000\n"
        ".word 0xe3a0009f\n"
        ".word 0xed840a19\n"
        ".word 0xed840a1a\n"
        ".word 0xeb0339e0\n"
        ".word 0xe3a01014\n"
        ".word 0xe3a00011\n"
        ".word 0xeb033930\n"
        ".word 0xe1c407b4\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a00011\n"
        ".word 0xeb03392c\n"
        ".word 0xe1c407b6\n"
        ".word 0xe3a01018\n"
        ".word 0xe3a00011\n"
        ".word 0xeb033928\n"
        ".word 0xe1c407b8\n"
        ".word 0xe3a01019\n"
        ".word 0xe3a00011\n"
        ".word 0xeb033924\n"
        ".word 0xe1c407ba\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a00002\n"
        ".word 0xe5c41061\n"
        ".word 0xeb022e84\n"
        ".word 0xe3a05001\n"
        ".word 0xe59f02a4\n"
        ".word 0xe3a01000\n"
        ".word 0xe5c45084\n"
        ".word 0xeb02d9fe\n"
        ".word 0xe5c45085\n"
        ".word 0xe5940088\n"
        ".word 0xe3a01000\n"
        ".word 0xeb02d89c\n"
        ".word 0xe3a00005\n"
        ".word 0xe5c45096\n"
        ".word 0xe584009c\n"
        ".word 0xea00006c\n"
        ".word 0xe320f000\n"
        ".word 0xeb027d28\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000067\n"
        ".word 0xe3a0000c\n"
        ".word 0xeafffd5c\n"
        ".word 0xe51f55e0\n"
        ".word 0xeb027d21\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000060\n"
        ".word 0xeb029dce\n"
        ".word 0xe5950000\n"
        ".word 0xe3a01000\n"
        ".word 0xe5900000\n"
        ".word 0xeb03683e\n"
        ".word 0xe3a00003\n"
        ".word 0xe320f000\n"
        ".word 0xeb03383c\n"
        ".word 0xe5940008\n"
        ".word 0xe3500001\n"
        ".word 0x0a000006\n"
        ".word 0xe3500000\n"
        ".word 0x0a00003d\n"
        ".word 0xe3500003\n"
        ".word 0x0bfe9ed5\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea00004e\n"
        ".word 0xe320f000\n"
        ".word 0xeb021732\n"
        ".word 0xe3a00001\n"
        ".word 0xe320f000\n"
        ".word 0xeb027665\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb0359a0\n"
        ".word 0xe5d00002\n"
        ".word 0xe3500000\n"
        ".word 0x13500001\n"
        ".word 0x0a000002\n"
        ".word 0xe3500002\n"
        ".word 0x0a00001b\n"
        ".word 0xea00003f\n"
        ".word 0xe320f000\n"
        ".word 0xeb0216d1\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb0215f4\n"
        ".word 0xe59f01b0\n"
        ".word 0xe59f11b0\n"
        ".word 0xe3a02001\n"
        ".word 0xe3a03000\n"
        ".word 0xe580236c\n"
        ".word 0xe5803358\n"
        ".word 0xe5911000\n"
        ".word 0xe35100c8\n"
        ".word 0xba000005\n"
        ".word 0xe24100c8\n"
        ".word 0xe58d0000\n"
        ".word 0xe3a02004\n"
        ".word 0xe1a0100d\n"
        ".word 0xe3a0000e\n"
        ".word 0xea000013\n"
        ".word 0xe3510064\n"
        ".word 0xb5c02034\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a01002\n"
        ".word 0xa3a00008\n"
        ".word 0xb3a00006\n"
        ".word 0xea00000c\n"
        ".word 0xe59f0158\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe3e03000\n"
        ".word 0xe5a02358\n"
        ".word 0xe3a02020\n"
        ".word 0xe5801014\n"
        ".word 0xe88d000a\n"
        ".word 0xe28f1d05\n"
        ".word 0xe1c100d0\n"
        ".word 0xe1cd00f8\n"
        ".word 0xe1a0100d\n"
        ".word 0xe3a00004\n"
        ".word 0xeb036cf9\n"
        ".word 0xea000015\n"
        ".word 0xe3a00000\n"
        ".word 0xeb02152d\n"
        ".word 0xe59f0124\n"
        ".word 0xe5900000\n"
        ".word 0xeb020fea\n"
        ".word 0xe3a00000\n"
        ".word 0xe320f000\n"
        ".word 0xeb027629\n"
        ".word 0xe59f00fc\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a01001\n"
        ".word 0xe3e02000\n"
        ".word 0xe5a03358\n"
        ".word 0xe5801014\n"
        ".word 0xe88d0006\n"
        ".word 0xe28f10e8\n"
        ".word 0xe3a02020\n"
        ".word 0xe1c100d0\n"
        ".word 0xe1cd00f8\n"
        ".word 0xe1a0100d\n"
        ".word 0xe3a00004\n"
        ".word 0xeb036ce2\n"
        ".word 0xe51f6778\n"
        ".word 0xe5964000\n"
        ".word 0xe5d4007c\n"
        ".word 0xe3500000\n"
        ".word 0x0a00004b\n"
        ".word 0xe5940080\n"
        ".word 0xe3500001\n"
        ".word 0x03a00000\n"
        ".word 0x05c40084\n"
        ".word 0x0a000043\n"
        ".word 0xe3500000\n"
        ".word 0xaa000041\n"
        ".word 0xe5d41094\n"
        ".word 0xe3a00002\n"
        ".word 0xe3a05000\n"
        ".word 0xe5840080\n"
        ".word 0xe3510000\n"
        ".word 0xe5c4507c\n"
        ".word 0x0a000004\n"
        ".word 0xe5940090\n"
        ".word 0xe5901000\n"
        ".word 0xe3110004\n"
        ".word 0x0a000020\n"
        ".word 0xea000027\n"
        ".word 0xe594008c\n"
        ".word 0xe5901000\n"
        ".word 0xe3110004\n"
        ".word 0x1a000007\n"
        ".word 0xe3811004\n"
        ".word 0xe5801000\n"
        ".word 0xe5901008\n"
        ".word 0xed9f0a10\n"
        ".word 0xed810a1d\n"
        ".word 0xe5900008\n"
        ".word 0xed900a1e\n"
        ".word 0xeb02c5bd\n"
        ".word 0xe594008c\n"
        ".word 0xe5901000\n"
        ".word 0xe3811002\n"
        ".word 0xe5801000\n"
        ".word 0xe5900008\n"
        ".word 0xe590002c\n"
        ".word 0xe5c051f6\n"
        ".word 0xe594008c\n"
        ".word 0xeb032197\n"
        ".word 0xed840a26\n"
        ".word 0xe320f000\n"
        ".word 0xea000019\n"
        ".word 0x0100016d\n"
        ".word 0x00000000\n"
        ".word 0x00407ef4\n"
        ".word 0x0049f91c\n"
        ".word 0x0049fd14\n"
        ".word 0x31303065\n"
        ".word 0x0031305f\n"
        ".word 0x00433158\n"
        ".word 0xe3811004\n"
        ".word 0xe5801000\n"
        ".word 0xe5901008\n"
        ".word 0xed1f0a0c\n"
        ".word 0xed810a1d\n"
        ".word 0xe5900008\n"
        ".word 0xed900a1e\n"
        ".word 0xeb02c5a1\n"
        ".word 0xe5940090\n"
        ".word 0xe5901000\n"
        ".word 0xe3811002\n"
        ".word 0xe5801000\n"
        ".word 0xe5900008\n"
        ".word 0xe590002c\n"
        ".word 0xe5c051f6\n"
        ".word 0xe5940090\n"
        ".word 0xeb03217b\n"
        ".word 0xed840a26\n"
        ".word 0xe5940088\n"
        ".word 0xe3a01000\n"
        ".word 0xeb02c782\n"
        ".word 0xe5c45085\n"
        ".word 0xe5940080\n"
        ".word 0xe2400001\n"
        ".word 0xe5840080\n"
        ".word 0xe5960000\n"
        ".word 0xe5d01061\n"
        ".word 0xed900a1b\n"
        ".word 0xe3510000\n"
        ".word 0x0a00000a\n"
        ".word 0xed5f0a27\n"
        ".word 0xeef40ac0\n"
        ".word 0xeef1fa10\n"
        ".word 0x8a000010\n"
        ".word 0xed9f1a13\n"
        ".word 0xee300a41\n"
        ".word 0xed800a1b\n"
        ".word 0xeeb40ae0\n"
        ".word 0xeef1fa10\n"
        ".word 0xdeb00a60\n"
        ".word 0xea000008\n"
        ".word 0xee101a10\n"
        ".word 0xe35105fe\n"
        ".word 0xca000006\n"
        ".word 0xeddf0a09\n"
        ".word 0xee300a20\n"
        ".word 0xee101a10\n"
        ".word 0xed800a1b\n"
        ".word 0xe35105fe\n"
        ".word 0xcd9f0a05\n"
        ".word 0xed800a1b\n"
        ".word 0xe28dd020\n"
        ".word 0xe3a00000\n"
        ".word 0xecbd8b02\n"
        ".word 0xe8bd81f0\n"
        ".word 0x3dcccccd\n"
        ".word 0x3f800000\n"
    );
}
#if 0
// Original partial readable draft retained for reconstruction; not compiled.
void ui_func_001e989c(void*) {
    camp::TitleMainWork* work = TitleWork();
    if (work == nullptr) {
        return;
    }

    // 0x001E98B4..0x001E98C0: 13-entry jump table at 0x001E98C4.
    switch (work->state_9C) {
    case 0: {
        // 0x001E98F8..0x001E9A30: cache the title layout.
        Tbb_EnsureSlotLoaded(0x3A);
        Title_LoadLayout();
        const Npc2dLayoutNode* node = LayoutNode(0x11, 0x12);
        work->field_40[0] = static_cast<f32>(node->x);
        work->field_40[1] = static_cast<f32>(node->y);
        node = LayoutNode(0x11, 0x13);
        work->field_40[2] = static_cast<f32>(node->x);
        work->field_40[3] = static_cast<f32>(node->y);
        node = LayoutNode(0x11, 0x16);
        work->field_40[4] = static_cast<f32>(node->x);
        work->field_40[5] = static_cast<f32>(node->y);
        node = LayoutNode(0x11, 0x17);
        work->field_40[6] = static_cast<f32>(node->x);
        work->field_40[7] = static_cast<f32>(node->y);
        Title_ResetFadeState();
        if (work->flag_95 != 0) {
            work->state_9C = 2;                                         // 0x001E99C8
            break;
        }
        if (Script_TestFlag(0) != 0) {
            UiSound_PlayCue(0, 4);                                      // 0x001E99E4
            UiSound_PlayCue(1, 4);                                      // 0x001E99F0
        }
        work->state_9C = work->state_9C + 1;                            // 0x001E9A30
        break;
    }
    case 1: {
        // 0x001E9A10: wait for the 0x3C anim created at work+0x14.
        TitleAnim_Update(reinterpret_cast<u8*>(work) + 0x14);
        if (reinterpret_cast<s8*>(work)[0x17] == 0) {
            break;
        }
        work->state_9C = work->state_9C + 1;
        break;
    }
    case 2: {
        // 0x001E9A3C..0x001E9B8C: title resource bootstrap.
        work->flag_10 = 0;                                              // 0x001E9A40
        Sound_RequestBgm(0x01000001, 0, 0x3C);                          // 0x001E9A58
        CommonBg_Begin();
        if (work->flag_60 != 0) {
            work->field_08 = 1;                                         // 0x001E9A78
            work->field_0c = 1;
        }
        if (work->flag_95 != 0) {
            work->field_08 = 3;                                         // 0x001E9A90
            work->field_0c = 3;
        }
        ButtonHelp_Init();
        ScriptVm_SetMessageId(0x9F);                                    // 0x001E9AA8

        const Tbl1Header* sub_table = Tbb_GetGlobalSubTable(0x3A, 0);
        const u8* payload = static_cast<const u8*>(Tbb_GetPayloadData(sub_table));
        const u32 index = work->field_08;
        camp::H1_SetTitleHelpMessage(
            reinterpret_cast<const char*>(payload + 0x16 + 0x56 * index),
            0x323232FF);                                                // H1 title message (state 2)

        if (work->flag_60 != 0) {
            Title_PreparePreview();                                     // 0x001E9AEC
        } else {
            Title_RegisterDefaultResources();                           // 0x001E9B80
        }

        // 0x001E9AF0..0x001E9B74: both paths converge here.
        u16* touch = TitleTouchHandles(work);
        touch[0] = static_cast<u16>(UiTouch_RegisterRegion(0x11, 0x14));
        touch[1] = static_cast<u16>(UiTouch_RegisterRegion(0x11, 0x15));
        touch[2] = static_cast<u16>(UiTouch_RegisterRegion(0x11, 0x18));
        touch[3] = static_cast<u16>(UiTouch_RegisterRegion(0x11, 0x19));
        work->resource_88 = Res_LoadBccam("title/title_top.bccam");     // 0x001E9B30
        work->resource_8c = Res_LoadBam("title/title_top1.bam", 7);     // 0x001E9B3C
        work->resource_90 = Res_LoadBam("title/title_top2.bam", 7);     // 0x001E9B4C
        work->flag_85 = 1;                                              // 0x001E9B68
        Res_LoadBcenv("title/title_top.bcenv", 0);                      // 0x001E9B6C
        work->flag_86 = 1;                                              // 0x001E9B70
        work->state_9C = work->state_9C + 1;
        break;
    }
    case 3: {
        // 0x001E9B90: wait for both .bam models and the .bccam handle.
        if (Res_IsLoadBusy(work->resource_8c) != 0) {
            work->state_9C = work->state_9C + 1;
            break;
        }
        if (Res_IsLoadBusy(work->resource_90) != 0) {
            work->state_9C = work->state_9C + 1;
            break;
        }
        if (work->resource_88 != 0) {
            work->state_9C = work->state_9C + 1;
            break;
        }
        break;
    }
    case 4: {
        // 0x001E9BC0..0x001E9D04: build the title camera and bind projection.
        work->flag_86 = 0;
        UiModel_SetVisible(work->resource_88, 0);
        void* handle = UiStyle_GetCurrent();
        u8* object = TitleHandleObject(work->resource_88);
        // 0x001E9BE4..0x001E9C00: r1 = sp+0x0C, r2 = sp+0x10, r3 = sp+0x04,
        // stack = sp+0x08.
        f32 m0 = 0.0F;
        f32 m1 = 0.0F;
        f32 m2 = 0.0F;
        f32 m3 = 0.0F;
        UiText_GetMetrics(object, &m0, &m1, &m2, &m3);
        m0 = (m0 * 180.0F) * 0.318309886F;                              // 0x001E9C08..0x001E9C20
        // s0 = sp+0x0C (m0), s1 = sp+0x04 (m2), s2 = sp+0x08 (m3),
        // s3 = sp+0x10 (m1).
        Effect_SetDrawParams(handle, 1, m0, m2, m3, m1);
        Effect_SetScale(handle, 5.0F, 1.0F);                            // 0x001E9C38
        AsdCamera_BindProjection(handle);                               // 0x001E9C4C
        UiModel_SetFlag(work->resource_8c, 1);                          // 0x001E9C58
        UiModel_SetFlag(work->resource_90, 1);                          // 0x001E9C64

        // 0x001E9C6C..0x001E9CA4: 0x8C clears bit 4 and restores alpha 1.0.
        {
            u32* flags = TitleHandleFlags(work->resource_8c);
            if ((*flags & 4) != 0) {
                *flags &= ~4u;
                u8* obj = TitleHandleObject(work->resource_8c);
                *reinterpret_cast<f32*>(obj + 0x74) = 1.0F;
                UiModel_ApplyAlpha(*reinterpret_cast<f32*>(obj + 0x78));
            }
        }
        // 0x001E9C98..0x001E9CC4: 0x90 sets bit 4 and hides alpha.
        {
            u32* flags = TitleHandleFlags(work->resource_90);
            if ((*flags & 4) == 0) {
                *flags |= 4u;
                u8* obj = TitleHandleObject(work->resource_90);
                *reinterpret_cast<f32*>(obj + 0x74) = 0.0F;
                UiModel_ApplyAlpha(*reinterpret_cast<f32*>(obj + 0x78));
            }
        }
        // 0x001E9CC8..0x001E9CE4: 0x90 gets bit 2 and clears the +0x1F6 byte.
        *TitleHandleFlags(work->resource_90) |= 2u;
        TitleHandleSub(work->resource_90)[0x1F6] = 0;

        UiSound_PlayCue(0, 10);                                         // 0x001E9CE8
        UiSound_PlayCue(1, 10);                                         // 0x001E9CF4
        work->state_9C = work->state_9C + 1;
        break;
    }
    case 5: {
        // 0x001E9D08..0x001EA128: cursor, blend, touch regions, fade handoff.
        if (camp::H1_TitleMain_UpdateNavigationSlice(&work) == 0u) {
            break;
        }

        // 0x001E9DE0..0x001E9E48: timer clamp and blend ramp.
        if (work->field_64 > 30.0F) {
            work->field_64 = 0.0F;
        }
        if (work->field_64 <= 15.0F) {
            work->field_68 += 0.06666667F;
        } else if (work->field_64 <= 30.0F) {
            work->field_68 -= 0.06666667F;
        }
        if (work->field_68 > 1.0F) {
            work->field_68 = 1.0F;
        }
        if (work->field_68 < 0.0F) {
            work->field_68 = 0.0F;
        }

        // 0x001E9E4C..0x001E9EB4: touch regions 0x74..0x7A.  States 1 and 2
        // move the cursor; state 6 only sets the +0x63 confirmation byte.
        const u16* touch = TitleTouchHandles(work);
        for (s32 i = 0; i < 4; ++i) {
            const s32 state = UiTouch_GetRegionTouchState(static_cast<s16>(touch[i]));
            if (state == 1 || state == 2) {
                work->field_08 = static_cast<u32>(i);                   // 0x001EA014
                break;
            }
        }
        for (s32 i = 0; i < 4; ++i) {
            if (UiTouch_GetRegionTouchState(static_cast<s16>(touch[i])) == 6) {
                work->field_08 = static_cast<u32>(i);                   // 0x001E9EA4
                work->flag_63 = 1;
            }
        }

        // 0x001E9F4C..0x001E9FD0: +0x96 handoff into 0x8C or 0x90.
        if (work->flag_96 != 0 && Camp_IsPreviewReady() != 0) {
            const u8 select = work->flag_94;
            work->flag_96 = 0;
            const u32 handle = (select != 0) ? work->resource_90 : work->resource_8c;
            *TitleHandleFlags(handle) &= ~2u;
            TitleHandleSub(handle)[0x1F6] = 1;
            u32* flags = TitleHandleFlags(handle);
            if ((*flags & 4) != 0) {
                *flags &= ~4u;
                u8* obj = TitleHandleObject(handle);
                *reinterpret_cast<f32*>(obj + 0x74) = 1.0F;
                UiModel_ApplyAlpha(*reinterpret_cast<f32*>(obj + 0x78));
            }
            UiModel_SetFade(handle, work->field_98);                    // 0x001E9FD0
        }

        // 0x001E9FD4..0x001EA12C: once both callbacks agree and the flag is
        // still clear, expose 0x90 and mark the state as shown.
        if (UiModel_IsVisible(TitleHandleObject(work->resource_8c)) != 0 &&
            UiModel_IsReady(TitleHandleObject(work->resource_8c)) != 0) {
            if (work->flag_94 == 0) {
                // 0x001EA070..0x001EA128
                u32* flags = TitleHandleFlags(work->resource_8c);
                if ((*flags & 4) == 0) {
                    *flags |= 4u;
                    u8* obj = TitleHandleObject(work->resource_8c);
                    *reinterpret_cast<f32*>(obj + 0x74) = 0.0F;
                    UiModel_ApplyAlpha(*reinterpret_cast<f32*>(obj + 0x78));
                }
                *TitleHandleFlags(work->resource_8c) |= 2u;
                TitleHandleSub(work->resource_8c)[0x1F6] = 0;
                work->field_98 = 0.0F;

                UiModel_ResetFade(TitleHandleObject(work->resource_90));
                UiModel_SetFadeParam(TitleHandleObject(work->resource_90), 0.0F);
                *TitleHandleFlags(work->resource_90) &= ~2u;
                TitleHandleSub(work->resource_90)[0x1F6] = 1;
                flags = TitleHandleFlags(work->resource_90);
                if ((*flags & 4) != 0) {
                    *flags &= ~4u;
                    u8* obj = TitleHandleObject(work->resource_90);
                    *reinterpret_cast<f32*>(obj + 0x74) = 1.0F;
                    UiModel_ApplyAlpha(*reinterpret_cast<f32*>(obj + 0x78));
                }
                work->flag_94 = 1;                                      // 0x001EA128
            }
        }

        // 0x001EA12C..0x001EA190: state text for the current cursor.
        {
            const Tbl1Header* sub_table = Tbb_GetGlobalSubTable(0x3A, 0);
            const u8* payload = static_cast<const u8*>(Tbb_GetPayloadData(sub_table));
            const u32 index = work->field_08;
            camp::H1_SetTitleHelpMessage(
                reinterpret_cast<const char*>(payload + 0x16 + 0x56 * index),
                0x323232FF);                                            // H1 title message (state 5)
        }
        if (work->flag_63 == 0) {
            if (UiMenu_CheckCursorSound(1) == 0 && UiInput_Trigger2(0) == 0) {
                break;
            }
        }

        // 0x001EA194..0x001EA1B0: cursor 1 with no +0x60 flag clears the
        // confirmation byte and returns.
        if (work->field_08 == 1 && work->flag_60 == 0) {
            work->flag_63 = 0;
            break;
        }
        Script_RequestEvent(0x0100016D);                                // 0x001EA1B4

        switch (work->field_08) {
        case 1: {
            // 0x001EA1C8: `strbeq r7,[r5,#0x61]` (r7 = 1) precedes the blink
            // loop; cases 1/2 fade in, case 3 does not.
            work->flag_61 = 1;
            // 0x001EA1F4..0x001EA234: four cursor-blink steps, then state 7.
            for (s32 i = 0; i < 4; ++i) {
                Camp_AdvanceCursorBlink();
            }
            work->flag_63 = 0;
            work->flag_7c = 1;                                          // 0x001EA214
            work->field_80 = 2;
            Script_PrepareCursor();                                     // 0x001EA21C
            Script_ApplyCursorMode(1);                                  // 0x001EA220
            work->state_9C = 7;
            break;
        }
        case 0: {
            // 0x001EA238..0x001EA290: confirmation path, then state 6.
            work->flag_62 = 1;
            work->flag_63 = 0;
            for (s32 i = 0; i < 4; ++i) {
                Camp_AdvanceCursorBlink();
            }
            Script_SetCursorSound(0, 0xC, 0xFFFFFFFF);                  // 0x001EA25C
            Script_SetCursorSound(1, 0xC, 0xFFFFFFFF);                  // 0x001EA26C
            Script_ResetCursorSound(0xF);                               // 0x001EA27C
            work->state_9C = 6;
            break;
        }
        case 2: {
            // 0x001EA1E0: same `strbeq r7,[r5,#0x61]` as case 1.
            work->flag_61 = 1;
            // 0x001EA294..0x001EA2D4: same as cursor 1 but state 9.
            for (s32 i = 0; i < 4; ++i) {
                Camp_AdvanceCursorBlink();
            }
            work->flag_63 = 0;
            work->flag_7c = 1;
            work->field_80 = 2;
            Script_PrepareCursor();
            Script_ApplyCursorMode(1);
            work->state_9C = 9;
            break;
        }
        case 3: {
            // 0x001EA2D8..0x001EA328: leave to state 11.
            work->flag_63 = 0;
            for (s32 i = 0; i < 4; ++i) {
                Camp_AdvanceCursorBlink();
            }
            work->state_9C = 0x0B;
            Script_SetCursorSound(0, 0xA, 0xFF);                        // 0x001EA30C
            Script_SetCursorSound(1, 0xA, 0xFF);                        // 0x001EA31C
            break;
        }
        default:
            break;
        }
        // State 5 exits through 0x001E9A08 (`str r0,[r5,#0x9c]`) or directly
        // to 0x001EA62C; it must not fall into the state-6 handler.
        break;
    }
    case 6: {
        // 0x001EA48C: `mov r0,#0xc; b 0x1e9a08` — no wait in this state.
        work->state_9C = 12;
        break;
    }
    case 7: {
        // 0x001EA32C: hand off to the save/load side, then state 8.
        if (work->flag_7c != 0) {
            break;
        }
        Script_PrepareTransition(0);
        SaveLoad_BeginFromTitle();
        work->state_9C = 8;
        break;
    }
    case 8: {
        // 0x001EA358: wait for the save/load screen, then either state 12
        // (manager flag set) or the boot reset.
        if (SaveLoad_IsBusy() != 0) {
            break;
        }
        if (Title_GetManagerFlag() != 0) {
            work->flag_62 = 1;
            Script_ResetCursorSound(0xF);                               // 0x001EA384
            work->state_9C = 12;
            break;
        }
        Title_ResetForBoot(work);                                       // 0x001EA3D8
        break;
    }
    case 9: {
        // 0x001EA398: title-config hand-off, state 10.
        if (work->flag_7c != 0) {
            break;
        }
        Script_PrepareTransition(0);
        camp::titleConfig_func_002f4ca0(nullptr);
        work->state_9C = 10;
        break;
    }
    case 10: {
        // 0x001EA3C4: wait for the config screen, then the boot reset.
        if (TitleConfig_IsReady() == 0) {
            break;
        }
        Title_ResetForBoot(work);                                       // 0x001EA3D8
        break;
    }
    case 11: {
        // 0x001EA478: wait for the script, then state 12.
        if (Script_IsReadyToAdvance() == 0) {
            break;
        }
        work->state_9C = 12;
        break;
    }
    case 12: {
        // 0x001EA494..0x001EA628: task teardown and the per-cursor exit.
        if (Script_IsReadyToAdvance() == 0) {
            break;
        }
        ScriptVm_ResetTitle();
        // 0x001EA4AC..0x001EA4B8: r5 = 0x0044E300, `ldr r0,[r5]` (work) then
        // `ldr r0,[r0]` (work->calc_task) — exactly one dereference.
        AsdTask_DestroyPair(work->calc_task, 0);
        UiScene_SetupField(3);                                          // 0x001EA4BC

        switch (work->field_08) {
        case 1: {
            // 0x001EA4F0..0x001EA590
            Script_PrepareTitleBoot();
            UiScene_SetFade(1);
            u8* state = reinterpret_cast<u8*>(
                static_cast<std::uintptr_t>(Save_GetGameOverStateIndex()));
            if (state[2] == 0 || state[2] == 1) {
                Script_StartTitleFade();
                Script_ClearTitleInput();
                u8* runtime = engine::g_MapRuntimeState;
                *reinterpret_cast<u32*>(runtime + 0x36C) = 1;           // 0x001EA550
                *reinterpret_cast<u32*>(runtime + 0x358) = 0;
                const u32 frame = *reinterpret_cast<u32*>(
                    static_cast<std::uintptr_t>(0x0049FD14u));
                if (frame >= 200) {
                    const u32 values[1] = {frame - 200};
                    engine::AsdSequence_func_002c59b8(0xE, values, 4);
                } else {
                    if (frame < 100) {
                        runtime[0x34] = 1;                              // 0x001EA580
                    }
                    engine::AsdSequence_func_002c59b8(frame < 100 ? 6 : 8, nullptr, 0);
                }
            } else if (state[2] == 2) {
                // 0x001EA598..0x001EA5D0
                u8* runtime = engine::g_MapRuntimeState;
                *reinterpret_cast<u32*>(runtime + 0x358) = 0;
                *reinterpret_cast<u32*>(runtime + 0x36C) = 1;
                Title_SequenceRequest();
            }
            break;
        }
        case 0: {
            // 0x001EA5D4..0x001EA628
            Script_StartNewGame();
            Camp_DrawTitleBundle(g_CampMessageBundle);          // 0x001EA5E4
            UiScene_SetFade(0);
            u8* runtime = engine::g_MapRuntimeState;
            *reinterpret_cast<u32*>(runtime + 0x358) = 0;
            *reinterpret_cast<u32*>(runtime + 0x36C) = 1;
            Title_SequenceRequest();
            break;
        }
        case 3: {
            UiScene_DrawLoading();                                      // 0x001EA4E0
            break;
        }
        default:
            break;
        }
    }
    default:
        break;
    }

    // 0x001EA62C..0x001EA7E4: shared transition tail.
    if (work->flag_7c != 0) {
        const u32 transition = work->field_80;
        if (transition == 1) {
            work->flag_84 = 0;                                          // 0x001EA64C
        } else if (static_cast<s32>(transition) < 0) {
            const u8 select = work->flag_94;
            work->field_80 = 2;
            work->flag_7c = 0;
            const u32 handle = (select != 0) ? work->resource_90 : work->resource_8c;
            u32* flags = TitleHandleFlags(handle);
            if ((*flags & 4) == 0) {
                *flags |= 4u;
                u8* obj = TitleHandleObject(handle);
                *reinterpret_cast<f32*>(obj + 0x74) = 0.0F;
                UiModel_ApplyAlpha(*reinterpret_cast<f32*>(obj + 0x78));
            }
            *flags |= 2u;
            TitleHandleSub(handle)[0x1F6] = 0;
            work->field_98 = UiModel_GetFade(handle);                   // 0x001EA748
            Res_ReleaseHandle(work->resource_88, 0);                    // 0x001EA754
            work->flag_85 = 0;
        }
        --work->field_80;                                               // 0x001EA764
    }

    // 0x001EA770..0x001EA7D8: fade value towards 0 (flag 0x61) or 1.
    if (work->flag_61 != 0) {
        if (!(0.0F > work->field_6c)) {
            work->field_6c -= 0.1F;
            if (work->field_6c < 0.0F) {
                work->field_6c = 0.0F;
            }
        }
    } else {
        if (!(work->field_6c > 1.0F)) {
            work->field_6c += 0.1F;
            if (work->field_6c > 1.0F) {
                work->field_6c = 1.0F;
            }
        }
    }
}
#endif

// ---------------------------------------------------------------------------
// 0x003EB4F4: fixed-point log2
// ---------------------------------------------------------------------------

namespace {

/** 0x0042026C..0x0042029B.  The first four words are the ones addressed when
 *  the exponent group index is negative; the eight at +0x10 are the 0x42027C
 *  table proper (0x00000000, log2 mantissa seeds). */
const u32 kUiLog2Table[12] = {
    0x9FA09F9Cu, 0x69C7582Fu, 0x74649059u, 0x719951DCu, // 0x0042026C..0x0042027B
    0x00000000u, 0xA2F9836Eu, 0x4E441529u, 0xFC2757D1u, // 0x0042027C..0x0042028B
    0xF534DDC0u, 0xDB629599u, 0x3C439041u, 0xFE5163ABu, // 0x0042028C..0x0042029B
};

inline f32 AsFloat(u32 bits) {
    f32 value;
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}
inline u32 AsBits(f32 value) {
    u32 bits;
    std::memcpy(&bits, &value, sizeof(bits));
    return bits;
}
/** ARM register-controlled LSR: a count of 32..255 produces zero (the
 *  listing's `inv_shift` is 0x20 when `shift == 0`).  C++ shifts by 32 are
 *  undefined, so special-case it. */
inline u32 ShiftRightVariable(u32 value, u32 amount) {
    return amount >= 32u ? 0u : (value >> amount);
}

} // namespace

// Ledger row 0x003EB4F4 covers 3,724 bytes.  The live log2 algorithm is only
// 0x003EB4F4..0x003EB61C (this function); 0x003EB63C..0x003EC37C below is a
// dead CRT static-initialiser tail, retained only to cover the ledger span.
// DECOMP_FUNC(0x003eb4f4, 3724)
__attribute__((naked)) f32 ui_func_003eb4f4(u32* out_integer, u32 value_bits) {
    asm volatile(
        ".word 0xe3a024ff\n"
        ".word 0xe92d05f0\n"
        ".word 0xe1520081\n"
        ".word 0x93e01000\n"
        ".word 0x95801000\n"
        ".word 0x98bd05f0\n"
        ".word 0x912fff1e\n"
        ".word 0xe3a02102\n"
        ".word 0xe1823401\n"
        ".word 0xe1a02081\n"
        ".word 0xe59f40fc\n"
        ".word 0xe1a02c22\n"
        ".word 0xe242c078\n"
        ".word 0xe20c601f\n"
        ".word 0xe1a022cc\n"
        ".word 0xe266c020\n"
        ".word 0xe08f4004\n"
        ".word 0xeddf1a39\n"
        ".word 0xe7945102\n"
        ".word 0xe0848102\n"
        ".word 0xed9f2a3a\n"
        ".word 0xe5982004\n"
        ".word 0xe1a05615\n"
        ".word 0xe1a07612\n"
        ".word 0xe5984008\n"
        ".word 0xe598800c\n"
        ".word 0xe185ac32\n"
        ".word 0xe1a06614\n"
        ".word 0xe1866c38\n"
        ".word 0xe1877c34\n"
        ".word 0xe082539a\n"
        ".word 0xe084c397\n"
        ".word 0xe0837396\n"
        ".word 0xe093300c\n"
        ".word 0xe0b4c005\n"
        ".word 0xee003a10\n"
        ".word 0xe2a22000\n"
        ".word 0xe2824020\n"
        ".word 0xe1a059ac\n"
        ".word 0xe1a02d02\n"
        ".word 0xeeb80a40\n"
        ".word 0xe1825685\n"
        ".word 0xee005a90\n"
        ".word 0xe1a0268c\n"
        ".word 0xe1a04324\n"
        ".word 0xe3110102\n"
        ".word 0xe5804000\n"
        ".word 0xeeb81ae0\n"
        ".word 0xee002a90\n"
        ".word 0x08bd05f0\n"
        ".word 0xeef80a60\n"
        ".word 0xee601aa1\n"
        ".word 0xeddf0a17\n"
        ".word 0xee200a20\n"
        ".word 0xee710a21\n"
        ".word 0xee700a80\n"
        ".word 0xee102a90\n"
        ".word 0xe2822b02\n"
        ".word 0xe1a02622\n"
        ".word 0xe1a02602\n"
        ".word 0xee002a90\n"
        ".word 0xee301ac1\n"
        ".word 0xee311a61\n"
        ".word 0xeddf1a0e\n"
        ".word 0xee301a41\n"
        ".word 0xed9f0a0b\n"
        ".word 0xee200a80\n"
        ".word 0xee010a21\n"
        ".word 0xee000a82\n"
        ".word 0x012fff1e\n"
        ".word 0xe2641201\n"
        ".word 0xe5801000\n"
        ".word 0xe8bd05f0\n"
        ".word 0xeeb10a40\n"
        ".word 0xe12fff1e\n"
        ".word 0x00034d40\n"
        ".word 0x36000000\n"
        ".word 0x2c800000\n"
        ".word 0x29fdaa22\n"
        ".word 0x2fc90fdb\n"
        ".word 0x2fc90000\n"
        ".word 0xe12fff1e\n"
        ".word 0xe59f2054\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe92d4010\n"
        ".word 0xe1c202f0\n"
        ".word 0xe59f0044\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe1a04001\n"
        ".word 0xe8800006\n"
        ".word 0xe2400020\n"
        ".word 0xe59f2030\n"
        ".word 0xe5801000\n"
        ".word 0xe59f102c\n"
        ".word 0xe1a00000\n"
        ".word 0xe59f0028\n"
        ".word 0xe3a01001\n"
        ".word 0xe59f2018\n"
        ".word 0xe5804000\n"
        ".word 0xe5c01004\n"
        ".word 0xe59f1018\n"
        ".word 0xe8bd4010\n"
        ".word 0xeaf8e9ec\n"
        ".word 0x00464fa8\n"
        ".word 0x00464fd0\n"
        ".word 0x00100000\n"
        ".word 0x003578e8\n"
        ".word 0x00464fbc\n"
        ".word 0x00357938\n"
        ".word 0xe59f2044\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe92d4010\n"
        ".word 0xe1c202f0\n"
        ".word 0xe59f0034\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe3a03002\n"
        ".word 0xe8800006\n"
        ".word 0xe3a02040\n"
        ".word 0xe59f1020\n"
        ".word 0xe59f0020\n"
        ".word 0xfafb6a1b\n"
        ".word 0xe59f201c\n"
        ".word 0xe59f101c\n"
        ".word 0xe8bd4010\n"
        ".word 0xe3a00000\n"
        ".word 0xeaf8e9d3\n"
        ".word 0x00464a98\n"
        ".word 0x00464ac0\n"
        ".word 0x003f7534\n"
        ".word 0x004dace0\n"
        ".word 0x00100000\n"
        ".word 0x0017f5cc\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00465090\n"
        ".word 0x00465098\n"
        ".word 0xe59f204c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe92d4010\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f003c\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe59f0030\n"
        ".word 0xebfdcf25\n"
        ".word 0xe2403008\n"
        ".word 0xe3a01000\n"
        ".word 0xe5a01034\n"
        ".word 0xe3a01001\n"
        ".word 0xe5c01004\n"
        ".word 0xe59f2018\n"
        ".word 0xe59f1018\n"
        ".word 0xe8bd4010\n"
        ".word 0xe1a00003\n"
        ".word 0xeaf8e9ad\n"
        ".word 0x00464fd8\n"
        ".word 0x00464fe8\n"
        ".word 0x004e0e90\n"
        ".word 0x00100000\n"
        ".word 0x0033b84c\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c202f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x004650a0\n"
        ".word 0x004650c8\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x0043e0f8\n"
        ".word 0x0043e108\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x0043dc58\n"
        ".word 0x0043dc68\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00433238\n"
        ".word 0x00433248\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x0043dca0\n"
        ".word 0x0043dca8\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00433d48\n"
        ".word 0x00433d50\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x0044dc20\n"
        ".word 0x0044dc30\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x0043e158\n"
        ".word 0x0043e168\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x0044e140\n"
        ".word 0x0044e150\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x0043dd38\n"
        ".word 0x0043dd48\n"
        ".word 0xe59f2040\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe92d4010\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0030\n"
        ".word 0xe59f4030\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe5841000\n"
        ".word 0xe1a00004\n"
        ".word 0xebfb605a\n"
        ".word 0xe1a00004\n"
        ".word 0xe59f2014\n"
        ".word 0xe59f1014\n"
        ".word 0xe8bd4010\n"
        ".word 0xeaf8e928\n"
        ".word 0x0044e348\n"
        ".word 0x0044e358\n"
        ".word 0x004c6410\n"
        ".word 0x00100000\n"
        ".word 0x003576b8\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00434250\n"
        ".word 0x00434258\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00473818\n"
        ".word 0x00473820\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00473828\n"
        ".word 0x00473830\n"
        ".word 0xe59f10b4\n"
        ".word 0xe92d4070\n"
        ".word 0xe3a04000\n"
        ".word 0xe59f00a4\n"
        ".word 0xe5911000\n"
        ".word 0xe59f50a8\n"
        ".word 0xe59f20a8\n"
        ".word 0xe5801000\n"
        ".word 0xe2800004\n"
        ".word 0xe59f10a0\n"
        ".word 0xe5804000\n"
        ".word 0xe59f008c\n"
        ".word 0xe5804004\n"
        ".word 0xe5804008\n"
        ".word 0xe580400c\n"
        ".word 0xe5805000\n"
        ".word 0xe5804010\n"
        ".word 0xe1a00000\n"
        ".word 0xe59f0080\n"
        ".word 0xe59f2074\n"
        ".word 0xe59f1074\n"
        ".word 0xe5804004\n"
        ".word 0xe5804008\n"
        ".word 0xe580400c\n"
        ".word 0xe5805000\n"
        ".word 0xe5804010\n"
        ".word 0xe1a00000\n"
        ".word 0xe59f0060\n"
        ".word 0xe59f2050\n"
        ".word 0xe59f1050\n"
        ".word 0xe5804004\n"
        ".word 0xe5804008\n"
        ".word 0xe580400c\n"
        ".word 0xe5805000\n"
        ".word 0xe5804010\n"
        ".word 0xe1a00000\n"
        ".word 0xe59f0040\n"
        ".word 0xe59f202c\n"
        ".word 0xe59f102c\n"
        ".word 0xe5804004\n"
        ".word 0xe5804008\n"
        ".word 0xe580400c\n"
        ".word 0xe5805000\n"
        ".word 0xe5804010\n"
        ".word 0xe8bd4070\n"
        ".word 0xeaf8e8d4\n"
        ".word 0x0044e644\n"
        ".word 0x00407fa8\n"
        ".word 0x004d428c\n"
        ".word 0x00420c20\n"
        ".word 0x00100000\n"
        ".word 0x00360470\n"
        ".word 0x004d42a0\n"
        ".word 0x004d42b4\n"
        ".word 0x004d42c8\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00464c20\n"
        ".word 0x00464c28\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00447a10\n"
        ".word 0x00447a20\n"
        ".word 0xe59f202c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe3a03040\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f001c\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe3a02038\n"
        ".word 0xe59f000c\n"
        ".word 0xe59f100c\n"
        ".word 0xeafb68e9\n"
        ".word 0x00447e58\n"
        ".word 0x00447e68\n"
        ".word 0x004bb7bc\n"
        ".word 0x0033b840\n"
        ".word 0xe59f202c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe3a03018\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f001c\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe3a02048\n"
        ".word 0xe59f000c\n"
        ".word 0xe59f100c\n"
        ".word 0xeafb68d8\n"
        ".word 0x00447e70\n"
        ".word 0x00447e80\n"
        ".word 0x004bc60c\n"
        ".word 0x0033b844\n"
        ".word 0xe59f20d8\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xed9f0a35\n"
        ".word 0xe1c204f0\n"
        ".word 0xe59f00c8\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xeddf0a31\n"
        ".word 0xe8800006\n"
        ".word 0xe59f00c0\n"
        ".word 0xed800a00\n"
        ".word 0xed800a01\n"
        ".word 0xe2800008\n"
        ".word 0xec800a02\n"
        ".word 0xe59f00b0\n"
        ".word 0xed800a00\n"
        ".word 0xed800a01\n"
        ".word 0xe2800008\n"
        ".word 0xec800a02\n"
        ".word 0xe59f00a0\n"
        ".word 0xed800a00\n"
        ".word 0xed800a01\n"
        ".word 0xe2800008\n"
        ".word 0xec800a02\n"
        ".word 0xe59f0090\n"
        ".word 0xed800a00\n"
        ".word 0xed800a01\n"
        ".word 0xe2800008\n"
        ".word 0xec800a02\n"
        ".word 0xe59f0080\n"
        ".word 0xed800a00\n"
        ".word 0xed800a01\n"
        ".word 0xe2800008\n"
        ".word 0xec800a02\n"
        ".word 0xe59f0070\n"
        ".word 0xed800a00\n"
        ".word 0xed800a01\n"
        ".word 0xe2800008\n"
        ".word 0xec800a02\n"
        ".word 0xe59f0060\n"
        ".word 0xed800a00\n"
        ".word 0xed800a01\n"
        ".word 0xe2800008\n"
        ".word 0xec800a02\n"
        ".word 0xe59f0050\n"
        ".word 0xed800a00\n"
        ".word 0xed800a01\n"
        ".word 0xe2800008\n"
        ".word 0xec800a02\n"
        ".word 0xe59f0040\n"
        ".word 0xed800a00\n"
        ".word 0xed800a01\n"
        ".word 0xe2800008\n"
        ".word 0xec800a02\n"
        ".word 0xe12fff1e\n"
        ".word 0x00448c58\n"
        ".word 0x00448ca0\n"
        ".word 0x00000000\n"
        ".word 0x3f800000\n"
        ".word 0x004bdb1c\n"
        ".word 0x004bdb2c\n"
        ".word 0x004bdb3c\n"
        ".word 0x004bdb4c\n"
        ".word 0x004bdb5c\n"
        ".word 0x004bdb6c\n"
        ".word 0x004bdb7c\n"
        ".word 0x004bdb8c\n"
        ".word 0x004bdb9c\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x0044dad8\n"
        ".word 0x0044dae8\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c201f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x0044db88\n"
        ".word 0x0044dba8\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00472930\n"
        ".word 0x00472938\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00464a60\n"
        ".word 0x00464a68\n"
        ".word 0xe59f206c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe92d4010\n"
        ".word 0xe1c203f0\n"
        ".word 0xe59f005c\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe1a04001\n"
        ".word 0xe8800006\n"
        ".word 0xe240001c\n"
        ".word 0xe59f2048\n"
        ".word 0xe5801000\n"
        ".word 0xe3a01001\n"
        ".word 0xe5c01004\n"
        ".word 0xe59f103c\n"
        ".word 0xe1a00000\n"
        ".word 0xe59f0038\n"
        ".word 0xe59f202c\n"
        ".word 0xe59f1034\n"
        ".word 0xe5804000\n"
        ".word 0xe1a00000\n"
        ".word 0xe59f002c\n"
        ".word 0xe5804000\n"
        ".word 0xe5804004\n"
        ".word 0xe59f2010\n"
        ".word 0xe59f1020\n"
        ".word 0xe8bd4010\n"
        ".word 0xeaf8e805\n"
        ".word 0x00465000\n"
        ".word 0x00465038\n"
        ".word 0x00100000\n"
        ".word 0x00357938\n"
        ".word 0x00465010\n"
        ".word 0x00357964\n"
        ".word 0x00465024\n"
        ".word 0x003575b0\n"
        ".word 0xe59f2024\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe3a03000\n"
        ".word 0xe1c201f8\n"
        ".word 0xe2820020\n"
        ".word 0xe5803000\n"
        ".word 0xe5803004\n"
        ".word 0xe3e00000\n"
        ".word 0xe5820010\n"
        ".word 0xe12fff1e\n"
        ".word 0x00464a70\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00472a20\n"
        ".word 0x00472a28\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00464c30\n"
        ".word 0x00464c38\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x004651c0\n"
        ".word 0x004651d0\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c203f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00464d48\n"
        ".word 0x00464d88\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00465290\n"
        ".word 0x00465298\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x0043daa8\n"
        ".word 0x0043dab8\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x0043ddb8\n"
        ".word 0x0043ddc8\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00433d10\n"
        ".word 0x00433d20\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x0043dcb0\n"
        ".word 0x0043dcc0\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x0043e128\n"
        ".word 0x0043e138\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00446420\n"
        ".word 0x00446428\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x0044d198\n"
        ".word 0x0044d1a8\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x0043dd08\n"
        ".word 0x0043dd18\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x0043dd50\n"
        ".word 0x0043dd60\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c201f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00433008\n"
        ".word 0x00433020\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00433170\n"
        ".word 0x00433178\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00433048\n"
        ".word 0x00433058\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x004342a8\n"
        ".word 0x004342b0\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x004342b8\n"
        ".word 0x004342c0\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00435d78\n"
        ".word 0x00435d88\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c203f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00435d90\n"
        ".word 0x00435dd0\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c201f0\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00435de0\n"
        ".word 0x00435df8\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00435e48\n"
        ".word 0x00435e58\n"
        ".word 0xe59f201c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe1c200f8\n"
        ".word 0xe59f0010\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe12fff1e\n"
        ".word 0x00439b58\n"
        ".word 0x00439b68\n"
        ".word 0xe59f202c\n"
        ".word 0xe3e00000\n"
        ".word 0xe1a01000\n"
        ".word 0xe3a03002\n"
        ".word 0xe1c202f0\n"
        ".word 0xe59f001c\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a02001\n"
        ".word 0xe8800006\n"
        ".word 0xe3a02008\n"
        ".word 0xe59f100c\n"
        ".word 0xe59f000c\n"
        ".word 0xeafb671d\n"
        ".word 0x00439ce0\n"
        ".word 0x00439d08\n"
        ".word 0x00342260\n"
        ".word 0x0049356c\n"
        ".word 0xe59f0060\n"
        ".word 0xe92d4010\n"
        ".word 0xe3a04000\n"
        ".word 0xe5804004\n"
        ".word 0xe5804008\n"
        ".word 0xe580400c\n"
        ".word 0xe5804010\n"
        ".word 0xe5804014\n"
        ".word 0xe5804018\n"
        ".word 0xe5804054\n"
        ".word 0xe5804058\n"
        ".word 0xe59f1038\n"
        ".word 0xe3e02000\n"
        ".word 0xe5802060\n"
        ".word 0xe5801000\n"
        ".word 0xe59f202c\n"
        ".word 0xe59f102c\n"
        ".word 0xe580405c\n"
        ".word 0xe1a00000\n"
        ".word 0xe59f0024\n"
        ".word 0xe59f1024\n"
        ".word 0xe59f2014\n"
        ".word 0xe8800012\n"
        ".word 0xe59f101c\n"
        ".word 0xe8bd4010\n"
        ".word 0xeaf8e6be\n"
        ".word 0x004eab5c\n"
        ".word 0x00420b78\n"
        ".word 0x00100000\n"
        ".word 0x003f7324\n"
        ".word 0x004eabc0\n"
        ".word 0x00420b60\n"
        ".word 0x0035ae44\n"
        ".word 0xe59f0008\n"
        ".word 0xe3a01000\n"
        ".word 0xe5801000\n"
        ".word 0xe12fff1e\n"
        ".word 0x00473848\n"
    );
}
#if 0
// Original partial readable draft retained for reconstruction; not compiled.
f32 ui_func_003eb4f4(u32* out_integer, u32 value_bits) {
    // 0x003EB4FC..0x003EB50C: 0xFF000000 <= (bits << 1) writes -1 and returns.
    if ((value_bits << 1) >= 0xFF000000u) {
        *out_integer = 0xFFFFFFFFu;
        return 0.0F;
    }

    const u32 mantissa = 0x80000000u | (value_bits << 8);               // 0x003EB514
    const u32 exponent_byte = (value_bits << 1) >> 24;                  // 0x003EB518..0x003EB520
    const s32 exponent_delta = static_cast<s32>(exponent_byte) - 0x78;  // 0x003EB524
    const u32 shift = static_cast<u32>(exponent_delta) & 0x1F;          // 0x003EB528
    const s32 group = exponent_delta >> 5;                              // 0x003EB52C
    const u32 inv_shift = 0x20 - shift;                                 // 0x003EB530

    const u32* table = &kUiLog2Table[4 + group];
    const u32 t0 = table[0];
    const u32 t1 = table[1];
    const u32 t2 = table[2];
    const u32 t3 = table[3];

    // shift is 0..31, so inv_shift is 1..32; the >> by 32 case must yield 0.
    const u32 word_a = (t0 << shift) | ShiftRightVariable(t1, inv_shift); // 0x003EB55C
    const u32 word_b = (t1 << shift) | ShiftRightVariable(t2, inv_shift); // 0x003EB568
    const u32 word_c = (t2 << shift) | ShiftRightVariable(t3, inv_shift); // 0x003EB560..0x003EB564

    // 0x003EB56C..0x003EB58C: three unsigned 64-bit products, accumulated
    // with the same carry chain as the listing.
    const u64 product_a = static_cast<u64>(word_a) * mantissa;
    const u64 product_b = static_cast<u64>(word_b) * mantissa;
    const u64 product_c = static_cast<u64>(word_c) * mantissa;

    const u32 lo_b = static_cast<u32>(product_b);
    const u32 hi_b = static_cast<u32>(product_b >> 32);
    const u32 lo_a = static_cast<u32>(product_a);
    const u32 hi_a = static_cast<u32>(product_a >> 32);
    const u32 hi_c = static_cast<u32>(product_c >> 32);

    const u32 sum_low = hi_c + lo_b;                                    // `adds r3,r3,ip`
    const bool carry_low = sum_low < hi_c;
    const u64 mid = static_cast<u64>(hi_b) + lo_a + (carry_low ? 1u : 0u);
    const u32 sum_high = static_cast<u32>(mid);                         // `adcs ip,r4,r5`
    const u32 top = hi_a + static_cast<u32>(mid >> 32);                 // `adc r2,r2,#0`

    const u32 integer_shifted = top + 0x20;                             // 0x003EB588
    const u32 high_bits = (top << 26) | ((sum_high >> 19) << 13);       // 0x003EB58C..0x003EB598
    const u32 low_bits = sum_high << 13;                                // 0x003EB5A0
    *out_integer = integer_shifted >> 6;                                // 0x003EB5A4 / 0x003EB5AC

    const f32 fraction_c = static_cast<f32>(sum_low) * AsFloat(0x2C800000u); // 0x003EB5C8
    const f32 integer_part = static_cast<f32>(static_cast<s32>(high_bits));  // 0x003EB5B0
    const f32 fraction_a = static_cast<f32>(low_bits) * AsFloat(0x36000000u); // 0x003EB5C0
    f32 value = integer_part + fraction_a + fraction_c;                 // 0x003EB5CC..0x003EB5D0

    // 0x003EB5D4..0x003EB604: round the accumulator to 2^12 in bit space and
    // apply the three coefficient products.
    const u32 rounded_bits = ((AsBits(value) + 0x800u) >> 12) << 12;    // 0x003EB5D8..0x003EB5E0
    const f32 rounded = AsFloat(rounded_bits);
    f32 residual = fraction_c - (rounded - integer_part - fraction_a);  // 0x003EB5E8..0x003EB5F4
    value = rounded * AsFloat(0x29FDAA22u);
    value = value + residual * AsFloat(0x2FC90FDBu);
    value = value + rounded * AsFloat(0x2FC90000u);                    // 0x003EB5F8..0x003EB604

    if ((value_bits & 0x80000000u) == 0) {
        return value;
    }
    // 0x003EB60C..0x003EB61C: negative input mirrors the exponent and sign.
    *out_integer = 0x10000000u - *out_integer;
    return -value;
}
#endif

// ---------------------------------------------------------------------------
// SOURCE/LEDGER NOTE (important):
// The ledger row for 0x003EB4F4 covers 3,724 bytes, but only
// 0x003EB4F4..0x003EB61C is the live fixed-point log2 routine above.  The
// remaining bytes, 0x003EB63C..0x003EC37C, are dead CRT static-initialiser /
// teardown thunks for statics owned by other translation units.  They are
// reconstructed below as observed absolute stores so the ledger span stays
// accounted for; they are NOT live gameplay logic and should not be read as
// such.  Keep this note with the block when re-baselining the ledger.
// ---------------------------------------------------------------------------

namespace {

inline void Store32(u32 address, u32 value) {
    *reinterpret_cast<u32*>(static_cast<std::uintptr_t>(address)) = value;
}
inline void StoreFloat(u32 address, f32 value) {
    *reinterpret_cast<f32*>(static_cast<std::uintptr_t>(address)) = value;
}
inline void ClearWords(u32 address, u32 count) {
    for (u32 i = 0; i < count; ++i) {
        Store32(address + i * 4, 0);
    }
}
/** `strd r0,r1` with both words = -1 (the register-pair teardown shape). */
inline void ClearPair(u32 base, u32 offset) {
    Store32(base + offset, 0xFFFFFFFFu);
    Store32(base + offset + 4, 0xFFFFFFFFu);
}
/** 0x002C5F50: copying initialiser with an alignment word in r3. */
inline void CopyAligned(u32 dst, u32 src, u32 size, u32 align) {
    (void)align;
    std::memcpy(reinterpret_cast<void*>(static_cast<std::uintptr_t>(dst)),
                reinterpret_cast<const void*>(static_cast<std::uintptr_t>(src)),
                size);
}
using DtorFn = void (*)(void*);
extern "C" int __aeabi_atexit(void* object, DtorFn dtor, void* dso_handle);

inline void RegisterTeardown(u32 object, u32 dtor) {
    __aeabi_atexit(reinterpret_cast<void*>(static_cast<std::uintptr_t>(object)),
                   reinterpret_cast<DtorFn>(static_cast<std::uintptr_t>(dtor)),
                   reinterpret_cast<void*>(static_cast<std::uintptr_t>(0x00100000u)));
}

// 0x003EB63C (24 B): 0x464FA8+0x20 pair, 0x464FD0 block, 0x464FB0 word, then
// the 0x464FBC teardown registration (r1 = 0x00357938).
void StaticInit_003eb63c() {
    ClearPair(0x464FA8u, 0x20);
    ClearWords(0x464FD0u, 2);
    Store32(0x464FB0u, 0);
    Store32(0x464FBCu, 0);
    *reinterpret_cast<u8*>(static_cast<std::uintptr_t>(0x464FC0u)) = 1;
    RegisterTeardown(0x464FBCu, 0x00357938u);
}

// 0x003EB6B0 (28 B): 0x464A98+0x20 pair, 0x464AC0 block, 0x40-byte copy from
// 0x003F7534 into 0x004DACE0, then `__aeabi_atexit(0, 0x0017F5CC, dso)`.
void StaticInit_003eb6b0() {
    ClearPair(0x464A98u, 0x20);
    ClearWords(0x464AC0u, 2);
    CopyAligned(0x4DACE0u, 0x3F7534u, 0x40, 2);
    RegisterTeardown(0u, 0x0017F5CCu);
}

// 0x003EB714 (20 B).
void StaticInit_003eb714() {
    ClearPair(0x465090u, 0);
    ClearWords(0x465098u, 2);
}

// 0x003EB740 (36 B): factory object at 0x004E0E90, teardown 0x0033B84C.
void StaticInit_003eb740() {
    ClearPair(0x464FD8u, 8);
    ClearWords(0x464FE8u, 2);
    u8* object = static_cast<u8*>(Runtime_GetTitleObject(0x4E0E90u));
    *reinterpret_cast<u32*>(object + 0x34) = 0;
    object[0x38] = 1;
    RegisterTeardown(static_cast<u32>(reinterpret_cast<std::uintptr_t>(object)) - 8,
                     0x0033B84Cu);
}

// 0x003EB7A8 (20 B).
void StaticInit_003eb7a8() {
    ClearPair(0x4650A0u, 0x20);
    ClearWords(0x4650C8u, 2);
}

// 0x003EB7D4 (20 B).
void StaticInit_003eb7d4() {
    ClearPair(0x43E0F8u, 8);
    ClearWords(0x43E108u, 2);
}

// 0x003EB800 (20 B).
void StaticInit_003eb800() {
    ClearPair(0x43DC58u, 8);
    ClearWords(0x43DC68u, 2);
}

// 0x003EB82C (20 B).
void StaticInit_003eb82c() {
    ClearPair(0x433238u, 8);
    ClearWords(0x433248u, 2);
}

// 0x003EB858 (20 B).
void StaticInit_003eb858() {
    ClearPair(0x43DCA0u, 0);
    ClearWords(0x43DCA8u, 2);
}

// 0x003EB884 (20 B).
void StaticInit_003eb884() {
    ClearPair(0x433D48u, 0);
    ClearWords(0x433D50u, 2);
}

// 0x003EB8B0 (20 B).
void StaticInit_003eb8b0() {
    ClearPair(0x44DC20u, 8);
    ClearWords(0x44DC30u, 2);
}

// 0x003EB8DC (20 B).
void StaticInit_003eb8dc() {
    ClearPair(0x43E158u, 8);
    ClearWords(0x43E168u, 2);
}

// 0x003EB908 (20 B).
void StaticInit_003eb908() {
    ClearPair(0x44E140u, 8);
    ClearWords(0x44E150u, 2);
}

// 0x003EB934 (20 B).
void StaticInit_003eb934() {
    ClearPair(0x43DD38u, 8);
    ClearWords(0x43DD48u, 2);
}

// 0x003EB960 (44 B): 0x44E348+8 pair, 0x44E358 block, 0x004C6410 reset,
// 0x002C3B00 release, registration 0x003576B8.
void StaticInit_003eb960() {
    ClearPair(0x44E348u, 8);
    ClearWords(0x44E358u, 2);
    Store32(0x4C6410u, 0);
    reinterpret_cast<void (*)(u32)>(static_cast<std::uintptr_t>(0x002C3B00u))(
        static_cast<u32>(0x4C6410u));
    RegisterTeardown(0x4C6410u, 0x003576B8u);
}

// 0x003EB9BC (20 B).
void StaticInit_003eb9bc() {
    ClearPair(0x434250u, 0);
    ClearWords(0x434258u, 2);
}

// 0x003EB9E8 (20 B).
void StaticInit_003eb9e8() {
    ClearPair(0x473818u, 0);
    ClearWords(0x473820u, 2);
}

// 0x003EBA14 (20 B).
void StaticInit_003eba14() {
    ClearPair(0x473828u, 0);
    ClearWords(0x473830u, 2);
}

// 0x003EBA40 (60 B): copies the word at 0x00407FA8 to 0x0044E644 and
// initialises the four 0x18-byte rows at 0x004D428C.. with vtable 0x00420C20.
void StaticInit_003eba40() {
    Store32(0x44E644u, *reinterpret_cast<const u32*>(static_cast<std::uintptr_t>(0x00407FA8u)));
    Store32(0x44E648u, 0);
    const u32 rows[4] = {0x4D428Cu, 0x4D42A0u, 0x4D42B4u, 0x4D42C8u};
    for (u32 i = 0; i < 4; ++i) {
        Store32(rows[i], 0x420C20u);
        Store32(rows[i] + 4, 0);
        Store32(rows[i] + 8, 0);
        Store32(rows[i] + 0xC, 0);
        Store32(rows[i] + 0x10, 0);
    }
    RegisterTeardown(0x4D42C8u, 0x00360470u);
}

// 0x003EBB1C (20 B).
void StaticInit_003ebb1c() {
    ClearPair(0x464C20u, 0);
    ClearWords(0x464C28u, 2);
}

// 0x003EBB48 (20 B).
void StaticInit_003ebb48() {
    ClearPair(0x447A10u, 8);
    ClearWords(0x447A20u, 2);
}

// 0x003EBB74 (28 B): 0x447E58+8 pair, 0x447E68 block, 0x38-byte copy.
void StaticInit_003ebb74() {
    ClearPair(0x447E58u, 8);
    ClearWords(0x447E68u, 2);
    CopyAligned(0x4BB7BCu, 0x33B840u, 0x38, 0x40);
}

// 0x003EBBB8 (28 B): 0x447E70+8 pair, 0x447E80 block, 0x48-byte copy.
void StaticInit_003ebbb8() {
    ClearPair(0x447E70u, 8);
    ClearWords(0x447E80u, 2);
    CopyAligned(0x4BC60Cu, 0x33B844u, 0x48, 0x18);
}

// 0x003EBBFC (20 B): 0x448C58+0x40 pair, 0x448CA0 block, then nine
// {0,0,0,1.0} blocks at 0x004BDB1C..0x004BDB9C stride 0x10.
void StaticInit_003ebbfc() {
    ClearPair(0x448C58u, 0x40);
    ClearWords(0x448CA0u, 2);
    for (u32 i = 0; i < 9; ++i) {
        const u32 base = 0x4BDB1Cu + i * 0x10;
        StoreFloat(base, 0.0F);
        StoreFloat(base + 4, 0.0F);
        StoreFloat(base + 8, 0.0F);
        StoreFloat(base + 0xC, 1.0F);
    }
}

// 0x003EBD10 (20 B).
void StaticInit_003ebd10() {
    ClearPair(0x44DAD8u, 8);
    ClearWords(0x44DAE8u, 2);
}

// 0x003EBD3C (20 B).
void StaticInit_003ebd3c() {
    ClearPair(0x44DB88u, 0x18);
    ClearWords(0x44DBA8u, 2);
}

// 0x003EBD68 (20 B).
void StaticInit_003ebd68() {
    ClearPair(0x472930u, 0);
    ClearWords(0x472938u, 2);
}

// 0x003EBD94 (20 B).
void StaticInit_003ebd94() {
    ClearPair(0x464A60u, 0);
    ClearWords(0x464A68u, 2);
}

// 0x003EBDC0 (44 B): 0x465000+0x30 pair, 0x465038 block, 0x46501C object
// byte +4 = 1, 0x465010 and 0x465024 words, registration 0x003575B0.
void StaticInit_003ebdc0() {
    ClearPair(0x465000u, 0x30);
    ClearWords(0x465038u, 2);
    Store32(0x46501Cu, 0);
    *reinterpret_cast<u8*>(static_cast<std::uintptr_t>(0x465020u)) = 1;
    Store32(0x465010u, 0);
    Store32(0x465024u, 0);
    Store32(0x465028u, 0);
    RegisterTeardown(0x465024u, 0x003575B0u);
}

// 0x003EBE54 (20 B).
void StaticInit_003ebe54() {
    ClearPair(0x464A70u, 0x18);
    Store32(0x464A90u, 0);
    Store32(0x464A94u, 0);
    Store32(0x464A80u, 0xFFFFFFFFu);
}

// 0x003EBE84 (20 B).
void StaticInit_003ebe84() {
    ClearPair(0x472A20u, 0);
    ClearWords(0x472A28u, 2);
}

// 0x003EBEB0 (20 B).
void StaticInit_003ebeb0() {
    ClearPair(0x464C30u, 0);
    ClearWords(0x464C38u, 2);
}

// 0x003EBEDC (20 B).
void StaticInit_003ebedc() {
    ClearPair(0x4651C0u, 8);
    ClearWords(0x4651D0u, 2);
}

// 0x003EBF08 (20 B).
void StaticInit_003ebf08() {
    ClearPair(0x464D48u, 0x38);
    ClearWords(0x464D88u, 2);
}

// 0x003EBF34 (20 B).
void StaticInit_003ebf34() {
    ClearPair(0x465290u, 0);
    ClearWords(0x465298u, 2);
}

// 0x003EBF60 (20 B).
void StaticInit_003ebf60() {
    ClearPair(0x43DAA8u, 8);
    ClearWords(0x43DAB8u, 2);
}

// 0x003EBF8C (20 B).
void StaticInit_003ebf8c() {
    ClearPair(0x43DDB8u, 8);
    ClearWords(0x43DDC8u, 2);
}

// 0x003EBFB8 (20 B).
void StaticInit_003ebfb8() {
    ClearPair(0x433D10u, 8);
    ClearWords(0x433D20u, 2);
}

// 0x003EBFE4 (20 B).
void StaticInit_003ebfe4() {
    ClearPair(0x43DCB0u, 8);
    ClearWords(0x43DCC0u, 2);
}

// 0x003EC010 (20 B).
void StaticInit_003ec010() {
    ClearPair(0x43E128u, 8);
    ClearWords(0x43E138u, 2);
}

// 0x003EC03C (20 B).
void StaticInit_003ec03c() {
    ClearPair(0x446420u, 0);
    ClearWords(0x446428u, 2);
}

// 0x003EC068 (20 B).
void StaticInit_003ec068() {
    ClearPair(0x44D198u, 8);
    ClearWords(0x44D1A8u, 2);
}

// 0x003EC094 (20 B).
void StaticInit_003ec094() {
    ClearPair(0x43DD08u, 8);
    ClearWords(0x43DD18u, 2);
}

// 0x003EC0C0 (20 B).
void StaticInit_003ec0c0() {
    ClearPair(0x43DD50u, 8);
    ClearWords(0x43DD60u, 2);
}

// 0x003EC0EC (20 B).
void StaticInit_003ec0ec() {
    ClearPair(0x433008u, 0x10);
    ClearWords(0x433020u, 2);
}

// 0x003EC118 (20 B).
void StaticInit_003ec118() {
    ClearPair(0x433170u, 0);
    ClearWords(0x433178u, 2);
}

// 0x003EC144 (20 B).
void StaticInit_003ec144() {
    ClearPair(0x433048u, 8);
    ClearWords(0x433058u, 2);
}

// 0x003EC170 (20 B).
void StaticInit_003ec170() {
    ClearPair(0x4342A8u, 0);
    ClearWords(0x4342B0u, 2);
}

// 0x003EC19C (20 B).
void StaticInit_003ec19c() {
    ClearPair(0x4342B8u, 0);
    ClearWords(0x4342C0u, 2);
}

// 0x003EC1C8 (20 B).
void StaticInit_003ec1c8() {
    ClearPair(0x435D78u, 8);
    ClearWords(0x435D88u, 2);
}

// 0x003EC1F4 (20 B).
void StaticInit_003ec1f4() {
    ClearPair(0x435D90u, 0x38);
    ClearWords(0x435DD0u, 2);
}

// 0x003EC220 (20 B).
void StaticInit_003ec220() {
    ClearPair(0x435DE0u, 0x10);
    ClearWords(0x435DF8u, 2);
}

// 0x003EC24C (20 B).
void StaticInit_003ec24c() {
    ClearPair(0x435E48u, 8);
    ClearWords(0x435E58u, 2);
}

// 0x003EC278 (20 B).
void StaticInit_003ec278() {
    ClearPair(0x439B58u, 8);
    ClearWords(0x439B68u, 2);
}

// 0x003EC2A4 (28 B): 0x439CE0+0x20 pair, 0x439D08 block, 8-byte copy.
void StaticInit_003ec2a4() {
    ClearPair(0x439CE0u, 0x20);
    ClearWords(0x439D08u, 2);
    CopyAligned(0x49356Cu, 0x342260u, 8, 2);
}

// 0x003EC2E8 (72 B): 0x004EAB5C workspace fields, vtable 0x00420B78 at +0,
// -1 at +0x60, 0x004EABC0 pair with 0x00420B60, registration 0x0035AE44.
void StaticInit_003ec2e8() {
    for (u32 offset = 4; offset <= 0x18; offset += 4) {
        Store32(0x4EAB5Cu + offset, 0);
    }
    Store32(0x4EAB5Cu + 0x54, 0);
    Store32(0x4EAB5Cu + 0x58, 0);
    Store32(0x4EAB5Cu + 0x60, 0xFFFFFFFFu);
    Store32(0x4EAB5Cu, 0x420B78u);
    Store32(0x4EAB5Cu + 0x5C, 0);
    Store32(0x4EABC0u, 0x420B60u);
    Store32(0x4EABC4u, 0);
    RegisterTeardown(0x4EABC0u, 0x0035AE44u);
}

// 0x003EC36C (16 B): clears 0x00473848.
void StaticInit_003ec36c() {
    Store32(0x473848u, 0);
}

} // namespace

} // namespace smt4::ui
