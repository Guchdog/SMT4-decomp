#include "engine/asd_frame.h"
#include "engine/asd_effect.h"
#include "engine/asd_symbols.h"
#include "ui/tbb_table.h"
#include <cstdint>

namespace smt4::engine {

// ---------------------------------------------------------------------------
// Globals (addresses are the storage locations used by the listing)
// ---------------------------------------------------------------------------

FrameTexScene* g_FrameTex = nullptr;            // 0x0043E278
SmokeFadeScene* g_SmokeFade = nullptr;          // 0x0043DF28

// 0x0043DF40 (.data) is a two-entry table of {group 0x2D, row 4} and
// {group 0x2D, row 5}; the +0x08/+0x09 load flags start clear.
SmokeFadeTexture g_SmokeFadeTextures[2] = {
    {0x2D, 4, 0, 0},
    {0x2D, 5, 0, 0},
};

// 0x0044F858 and 0x0044F8C8 are two instances of the same AsdUi-style
// widget; `EffectEditor_func_0024246c` fills the second one and stores its
// address into the object at slot->owner + 0x34 (0x002427B0).
//
// Their .data images are not zero: the cursor widget carries the raw owner
// 0x00425A1E and both share the five-entry menu at 0x00463D28.
EffectEditorWidget g_EffectEditorCursor{
    reinterpret_cast<void*>(static_cast<std::uintptr_t>(0x00425A1E)),
    8,                                              // +0x04
    8,                                              // +0x08
    0,                                              // +0x0C mode
    0,                                              // +0x10 flags
    reinterpret_cast<void*>(static_cast<std::uintptr_t>(0x00463D28)),
    5,                                              // +0x18 menu_count
};                                                  // 0x0044F858
EffectEditorWidget g_EffectEditorList{
    nullptr,                                        // +0x00 owner
    8,                                              // +0x04
    8,                                              // +0x08
    0,                                              // +0x0C mode
    0,                                              // +0x10 flags
    reinterpret_cast<void*>(static_cast<std::uintptr_t>(0x00463D28)),
    5,                                              // +0x18 menu_count
};                                                  // 0x0044F8C8

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

extern "C" {
    // AsdMemory (c:\SMT4\XRD686\AsdSDK\Source\Sys\Mem\AsdMemory.cpp)
    void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);        // 0x002c4b84
    void* AsdMem_AllocAlign(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);   // 0x002c54f0
    void  AsdMem_Zero(void* ptr, u32 size);                                // 0x002c4b30
    void  AsdMem_Free(void* ptr);                                          // 0x002c4360
    void  AsdMem_Copy(void* dst, const void* src, u32 size);               // 0x002c5ff4
    void* AsdWork_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 a5); // 0x002c34a4

    // AsdGxRenderSystem (AsdGxRenderSystem.cpp): allocates and configures one
    // AsdTexture for the requested kind and returns it.
    void* AsdGxRenderSystem_func_002c336c(u32 kind);                       // 0x002c336c
    u32   AsdGpu_Address(const void* ptr);                                 // 0x002bc300

    // The 0x002C3344 / 0x002C32F8 layout helpers are declared canonically as
    // UiSpriteGroup_Init / UiSpriteGroup_BindTable in engine/asd_symbols.h.

    // 2D NPC tables / script hooks
    bool  Flag_CheckEventBit(u32 flag_id);                                 // 0x002c0ba8
    void* AsdTable_FindBattleRow(u32 id);                                  // 0x002b087c
    void* AsdTable_FindNpcRow(u32 id);                                     // 0x00245b44
    void* AsdTable_GetRowEntry(void* row, u32 index);                      // 0x002aef6c
    int   AsdRow_Has(void* bundle, u32 key, u32 sub, u32 mode);            // 0x002aec20
    void* AsdRow_Request(void* bundle, u32 key, u32 sub, u32 flags);       // 0x002aeb78
    void* AsdRow_LoadNow(u32 key, u32 sub);                                // 0x002c5ab8
    void* Npc2d_CreateSprite(s32 row_value, u32 mode);                     // 0x00294334
    s32   AsdScene_LoadMode();                                             // 0x002c1f28

    // AsdTMTexTable / resource cache
    int   AsdTMTexTable_IsGroupLoaded(u32 group_id);                       // 0x0024bd24
    int   AsdRes_IsLoaded(u32 key, u32 sub);                               // 0x002a63f8
    void  AsdRes_Request(u32 key, u32 sub);                                // 0x002a6214
    void  ScriptVm_LoadTable(const char* name, void* out, u32 value);      // 0x00297704

    // EffectEditor plumbing (shared names with src/engine/asd_model.cpp)
    void  AsdUiObject_Update(void* object);                                // 0x0024df5c
    int   UiInput_Trigger2(u32 id);                                        // 0x002bffbc
    void  UiInput_Reset(u32 id);                                           // 0x0024df94
    void  UiText_Format(char* dst, const char* fmt, ...);                  // 0x002be7fc
    u32   AsdParts_Count(void* parts);                                     // 0x00246a74
    void  AsdPart_Update3(void* part);                                     // 0x00250440
    void  AsdPart_Close(void* part, s32 mode);                             // 0x00262bd4
    void  AsdPart_Release(void* part, s32 mode);                           // 0x00262c1c
    void* EffParts_WrapElement(void* parts, void* element);                // 0x002c79c8
    void* EffParts_LoadElement(void* element);                             // 0x0019da14
    void* AsdRes_ResolveOffset(void* record);                              // 0x0024c60c
    void  EffParts_SetRow(void* part, const void* row, u32 key);           // 0x001e192c
    void  AsdDrawDesc_Init(void* desc);                                    // 0x002a3ff8
}

namespace {

// 0x004D8CA0: the editor's live 0x80-byte draw descriptor.  AsdDrawDesc_Init
// resets it (0x00242618 / 0x002428E8) and the selected slot's three values are
// written to +0x40/+0x44/+0x48 (0x002428F0-0x00242904).
constexpr std::uintptr_t kEditorDrawDesc = 0x004D8CA0;

// `bl trigger2; bne taken; bl reset; bl trigger2` -- the editor input helper,
// identical to Ui_PressedB in src/engine/asd_model.cpp.
int Ui_PressedB(u32 id)
{
    if (UiInput_Trigger2(id) != 0) {
        return 1;
    }
    UiInput_Reset(id);
    return UiInput_Trigger2(id) != 0 ? 1 : 0;
}

// Npc2d pose selection written to +0x38: 0x00252480-0x002524C4 and the
// identical 0x00286164-0x002861A4 sequence.
s32 Npc2d_PoseFromArgument(s32 value)
{
    if (value <= -0x64) {           // cmn r5,#0x64 / movle r0,#0x10
        return 0x10;
    }
    if (value <= -0x3C) {           // cmn r5,#0x3c / movle r0,#3
        return 0x03;
    }
    if (value >= 0x64) {            // cmp r5,#0x64 / movge r0,#0x11
        return 0x11;
    }
    if (value >= 0x28) {            // cmp r5,#0x28 / movge r0,#4
        return 0x04;
    }
    if (value < 0) {                // cmp r5,#0 / movlt r0,#0x12
        return 0x12;
    }
    return 0x05;                    // movge r0,#5
}

// Shared tail of the two sprite-table constructors
// (0x00252458-0x0025247C / 0x0028613C-0x00286160): on the fallback path the
// +0x4C row value is turned into a sprite block at +0x48 and the state becomes
// 2.  There is no bundle lookup in these two functions.
void Npc2d_SetupSpriteData(Npc2dSprite* sprite)
{
    if (AsdScene_LoadMode() != 0) {                             // 0x002c1f28
        sprite->field_0c = 1;
        return;
    }

    // `ldr r0,[r4,#0x4c]; mov r1,#1; bl 0x00294334` (0x00252468).
    sprite->field_48 = static_cast<u32>(reinterpret_cast<std::uintptr_t>(
        Npc2d_CreateSprite(sprite->field_4c, 1)));
    sprite->field_0c = 2;                                       // 0x0025247C `str r1,[r4,#0xc]`
}

// Shared tail of the two row-table constructors
// (0x002FE064-0x002FE0B4 / 0x0031BF04-0x0031BF64): the +0x3C/+0x40 key pair
// is either requested from the camp bundle or loaded synchronously.
void Npc2d_LoadRowKey(Npc2dSprite* sprite)
{
    if (AsdScene_LoadMode() != 0) {                             // 0x002c1f28
        sprite->field_0c = 1;
        return;
    }

    sprite->field_0c = 0;
    void* bundle = g_CampMessageBundle;
    const u32 key = sprite->field_3c;
    const u32 sub = sprite->field_40;
    if (AsdRow_Has(bundle, key, sub, 1) != 0) {
        AsdRow_Request(bundle, key, sub, 0x10000);
    } else {
        AsdRow_LoadNow(key, sub);
    }
}

// 0x002524F0 / 0x002861CC / 0x002FE0DC / 0x0031BF8C: every 2D NPC constructor
// ends with the same "EVE_2dTex" widget.
void* Npc2d_CreateWidget(Npc2dSprite* sprite)
{
    return AsdUi_Create("EVE_2dTex", 2, 0, 0,
                        0x001DFB60, 0x002DB8C4, sprite);
}

} // namespace

// ===========================================================================
// FrameTex.cpp
// ===========================================================================

// ---------------------------------------------------------------------------
// 0x00104378 -- construct the FrameTex scene and its 22 widgets.
//
// Atlus source: c:\SMT4\XRD686\sdds4\program\frame_tex\FrameTex.cpp
// Allocation: 0xFEC bytes, line 0x15A, zero-filled (0x001043A8-0x001043BC).
// Four AsdGxRenderSystem textures are created before the scene is published
// (0x001043C0-0x001043EC).  The layout descriptor at +0x34 is cleared by
// 0x002C3344 and filled by 0x002C32F8 (0x00104408/0x0010444C).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00104378, 1508)
void FrameTex_func_00104378()
{
    // 0x00104380-0x001043A8: AsdMem_Alloc(0x100, 0x100, 0, 0xFEC, 1).
    FrameTexScene* scene = static_cast<FrameTexScene*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0xFEC, 1));
    g_FrameTex = scene;                                     // 0x001043B8 `str r0,[r6]`
    AsdMem_Zero(scene, 0xFEC);                              // 0x001043BC

    scene->textures[0] = static_cast<AsdTexture*>(
        AsdGxRenderSystem_func_002c336c(0));                // 0x001043C0-0x001043C8
    scene->textures[1] = static_cast<AsdTexture*>(
        AsdGxRenderSystem_func_002c336c(0));                // 0x001043CC-0x001043D4
    scene->overlay_textures[0] = static_cast<AsdTexture*>(
        AsdGxRenderSystem_func_002c336c(0));                // 0x001043D8-0x001043E0
    scene->overlay_textures[1] = static_cast<AsdTexture*>(
        AsdGxRenderSystem_func_002c336c(0));                // 0x001043E4-0x001043EC

    scene->field_fdc = nullptr;                             // 0x001043F4 `str r5,[r4,#0xfdc]`
    scene->field_0c = 0;                                    // 0x001043F8
    scene->field_10 = 0;                                    // 0x001043FC
    scene->field_14 = 0;                                    // 0x00104400
    scene->field_18 = 0;                                    // 0x00104404
    scene->field_1c = 0;                                    // 0x0010440C
    UiSpriteGroup_Init(&scene->header);                     // 0x00104410

    // 0x00104414-0x0010444C: the descriptor constants are passed in r1/r3 and
    // on the stack (see the parameter mapping in include/engine/asd_text.h).
    UiSpriteGroup_BindTable(&scene->header,
                   0x0040420C, 0x18, 0x00404224,
                   0x0C, 0x00404230, 0x0C, 0, 0, 0x0040423C, 0x70);

    scene->field_28 = 0.25f;                                // 0x00104458 `vstr s0`
    scene->field_2c = 0.25f;                                // 0x0010445C
    scene->field_30 = 20.0f;                                // 0x00104460 `vstr s1`

    scene->field_e8c = 0;                                   // 0x00104474 `strb r5,[r2,#0xe8c]`
    scene->field_edc = 0;                                   // 0x00104478
    scene->field_f28 = 0;                                   // 0x0010447C
    scene->field_f2b = 0;                                   // 0x00104480
    scene->field_f2c = 0;                                   // 0x00104484
    scene->field_f98 = 0;                                   // 0x00104488
    scene->field_f99 = 0;                                   // 0x0010448C
    scene->field_fe0 = 0;                                   // 0x00104490

    // 0x00104494-0x001044A8: AsdUi_Create("HDRCL", 0x6A, 0, 0,
    // cb0=0x00108300, cb1=0x00107890, obj=scene).
    scene->main_widget = AsdUi_Create("HDRCL", 0x6A, 0, 0,
                                      0x00108300, 0x00107890, scene);

    // 0x001044AC-0x00104924: 21 child widgets parented on +0x00.  Every call
    // passes (label, id, 0, 0, callback, 0, scene, main_widget).
    const u32 cb_hdr_cr = 0x001084F0;                       // 0x001044B4
    const u32 cb_hdr_dl = 0x00108064;                       // 0x001044D8
    const u32 cb_hdr_dr = 0x001080D0;                       // 0x00104500
    const u32 cb_zan_cl = 0x001086F8;                       // 0x00104528
    const u32 cb_zan_cr = 0x00108798;                       // 0x00104550
    const u32 cb_zan_dl = 0x00108154;                       // 0x00104578
    const u32 cb_zan_dr = 0x001081C0;                       // 0x001045A0
    const u32 cb_camp_cl = 0x001092EC;                      // 0x001045C8
    const u32 cb_camp_cr = 0x0010938C;                      // 0x001045F0
    const u32 cb_camp_dl = 0x00108840;                      // 0x00104618
    const u32 cb_camp_dr = 0x00108AB0;                      // 0x00104640
    const u32 cb_enceff_cl = 0x0010A33C;                    // 0x00104668
    const u32 cb_enceff_cr = 0x0010A3E8;                    // 0x00104690
    const u32 cb_enceff_dl = 0x00109FD4;                    // 0x001046B8
    const u32 cb_enceff_dr = 0x0010A0A8;                    // 0x001046E0
    const u32 cb_info_show = 0x0010B1B4;                    // 0x00104708 InfoWin_ShowMessage
    const u32 cb_info_timer = 0x0010B260;                   // 0x00104858 InfoWin_UpdateTimer
    const u32 cb_xfade_cl = 0x00109ED8;                     // 0x00104880
    const u32 cb_xfade_cr = 0x00109F4C;                     // 0x001048A8
    const u32 cb_xfade_dl = 0x00109440;                     // 0x001048D0
    const u32 cb_xfade_dr = 0x001094C4;                     // 0x001048F8

    const u32 parent = static_cast<u32>(reinterpret_cast<std::uintptr_t>(
        scene->main_widget));

    AsdUi_CreateLabel("HDRCR", 0xCE, 0, 0, cb_hdr_cr, 0, scene, parent);       // 0x001044D4
    AsdUi_CreateLabel("HDRDL", 0x6B, 0, 0, cb_hdr_dl, 0, scene, parent);       // 0x001044FC
    AsdUi_CreateLabel("HDRDR", 0xCF, 0, 0, cb_hdr_dr, 0, scene, parent);       // 0x00104524
    AsdUi_CreateLabel("ZanCL", 0x6D, 0, 0, cb_zan_cl, 0, scene, parent);       // 0x0010454C
    AsdUi_CreateLabel("ZanCR", 0xD1, 0, 0, cb_zan_cr, 0, scene, parent);       // 0x00104574
    AsdUi_CreateLabel("ZanDL", 0x6C, 0, 0, cb_zan_dl, 0, scene, parent);       // 0x0010459C
    AsdUi_CreateLabel("ZanDR", 0xD0, 0, 0, cb_zan_dr, 0, scene, parent);       // 0x001045C4
    AsdUi_CreateLabel("CAMPCL", 0x78, 0, 0, cb_camp_cl, 0, scene, parent);     // 0x001045EC
    AsdUi_CreateLabel("CAMPCR", 0xD6, 0, 0, cb_camp_cr, 0, scene, parent);     // 0x00104614
    AsdUi_CreateLabel("CAMPDL", 0x65, 0, 0, cb_camp_dl, 0, scene, parent);     // 0x0010463C
    AsdUi_CreateLabel("CAMPDR", 0xCC, 0, 0, cb_camp_dr, 0, scene, parent);     // 0x00104664
    AsdUi_CreateLabel("ENCEFFCL", 0x77, 0, 0, cb_enceff_cl, 0, scene, parent); // 0x0010468C
    AsdUi_CreateLabel("ENCEFFCR", 0xD5, 0, 0, cb_enceff_cr, 0, scene, parent); // 0x001046B4
    AsdUi_CreateLabel("ENCEFFDL", 0x82, 0, 0, cb_enceff_dl, 0, scene, parent); // 0x001046DC
    AsdUi_CreateLabel("ENCEFFDR", 0xE0, 0, 0, cb_enceff_dr, 0, scene, parent); // 0x00104704

    // 0x00104730 `b 0x00104858` skips the first literal pool; the two
    // duplicate labels carry the InfoWin callbacks.
    AsdUi_CreateLabel("ENCEFFCL", 0x7E, 0, 0, cb_info_show, 0, scene, parent);  // 0x0010472C
    AsdUi_CreateLabel("ENCEFFCR", 0xDC, 0, 0, cb_info_timer, 0, scene, parent); // 0x0010487C
    AsdUi_CreateLabel("XFADECL", 0x77, 0, 0, cb_xfade_cl, 0, scene, parent);    // 0x001048A4
    AsdUi_CreateLabel("XFADECR", 0xD5, 0, 0, cb_xfade_cr, 0, scene, parent);    // 0x001048CC
    AsdUi_CreateLabel("XFADEDL", 0x79, 0, 0, cb_xfade_dl, 0, scene, parent);    // 0x001048F4
    AsdUi_CreateLabel("XFADEDR", 0xD7, 0, 0, cb_xfade_dr, 0, scene, parent);    // 0x0010491C
}

// ---------------------------------------------------------------------------
// 0x00280D30 -- create the frame-capture textures for the active mode.
//
// `alternate == 0` builds a 0x200x0x190 texture plus two 0x100/0x80 helper
// textures into +0xFE4/+0xFE8 (0x00280DDC-0x00280EF0); otherwise a single
// 0x30000-kind texture is built (0x00280D80-0x00280DC8).  +0xFD8/+0xE96/+0xE95
// are cleared in both paths (0x00280DCC-0x00280DD4).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00280d30, 524)
void FrameTex_func_00280d30(u32 alternate)
{
    FrameTexScene* scene = g_FrameTex;                          // 0x00280D38-0x00280D3C
    AsdTexture* texture = static_cast<AsdTexture*>(
        AsdTexture_func_002bd940(0));                           // 0x00280D44

    if (scene->field_fdc != nullptr) {                          // 0x00280D4C-0x00280D54
        return;
    }

    // Shared 0x200x0x190 setup of the first texture.  r0/r1/r2/r8/sb carry
    // 0x200, 0x190, 0x64000, 0x8D62 and 0x1403 (0x00280D64-0x00280D74).
    texture->field_10 = 0;                                      // 0x00280D8C / 0x00280DE8
    texture->data_size = 0x64000;                               // 0x00280D84 / 0x00280DE0
    texture->width = 0x200;                                     // `stm r3,{r0,r1,r8,sb}` (0x00280D94)
    texture->height = 0x190;
    texture->format2 = 0x8D62;
    texture->param = 0x1403;
    texture->gpu_format = 3;                                    // 0x00280D90 / 0x00280DEC

    if (alternate != 0) {
        scene->field_fe0 = 0;                                   // 0x00280D80
        texture->data = AsdMem_AllocAlign(0x30000, 0x100, 0,
                                          texture->data_size, 1); // 0x00280DB8
        texture->gpu_address = AsdGpu_Address(texture->data);   // 0x00280DC0
        scene->field_fdc = texture;                             // 0x00280DC8
    } else {
        scene->field_fe0 = 1;                                   // 0x00280DDC
        texture->data = AsdMem_AllocAlign(0x20000, 0x100, 0,
                                          texture->data_size, 1); // 0x00280E14
        texture->gpu_address = AsdGpu_Address(texture->data);   // 0x00280E20
        scene->field_fdc = texture;                             // 0x00280E2C

        // 0x00280E30-0x00280E90: 0x100x0x100 helper (data size 0x20000).
        AsdTexture* second = static_cast<AsdTexture*>(
            AsdTexture_func_002bd940(0));                       // 0x00280E30
        second->field_10 = 0;                                   // 0x00280E44
        second->data_size = 0x20000;                            // 0x00280E3C
        second->width = 0x100;                                  // `stm r3,{r1,r8,sb}` (0x00280E54)
        second->height = 0x100;
        second->format2 = 0x8D62;
        second->param = 0x1403;
        second->gpu_format = 3;                                 // 0x00280E4C
        second->data = AsdMem_AllocAlign(0x20000, 0x100, 0,
                                         second->data_size, 1); // 0x00280E78
        second->gpu_address = AsdGpu_Address(second->data);     // 0x00280E84
        scene->field_fe4 = second;                              // 0x00280E90

        // 0x00280E94-0x00280EF0: 0x80x0x80 helper (data size 0x8000).
        AsdTexture* third = static_cast<AsdTexture*>(
            AsdTexture_func_002bd940(0));                       // 0x00280E94
        third->field_10 = 0;                                    // 0x00280EA8
        third->data_size = 0x8000;                              // 0x00280EA4
        third->width = 0x80;                                    // `stm r3,{r1,r8,sb}` (0x00280EB8)
        third->height = 0x80;
        third->format2 = 0x8D62;
        third->param = 0x1403;
        third->gpu_format = 3;                                  // 0x00280EB0
        third->data = AsdMem_AllocAlign(0x20000, 0x100, 0,
                                        third->data_size, 1);   // 0x00280EDC
        third->gpu_address = AsdGpu_Address(third->data);       // 0x00280EE8
        scene->field_fe8 = third;                               // 0x00280EF0
    }

    scene->field_fd8 = 0;                                       // 0x00280DCC
    scene->field_e96 = 0;                                       // 0x00280DD0
    scene->field_e95 = 0;                                       // 0x00280DD4
}

// ===========================================================================
// Npc2d.cpp
// ===========================================================================

// ---------------------------------------------------------------------------
// 0x002523D0 -- create a 2D NPC sprite from a battle-table row.
//
// Allocation: 0x98 bytes, line 0x279 (0x002523DC-0x00252414).
// The row lookup is `AsdTable_FindBattleRow((u16)id)` and the signed halfword
// at row+0x88 becomes +0x4C (0x00252444-0x00252454).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002523d0, 336)
void* Npc2d_func_002523d0(u32 id, u32 arg1, s32 pose_arg)
{
    Npc2dSprite* sprite = static_cast<Npc2dSprite*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x98, 1));                    // 0x00252408
    AsdMem_Zero(sprite, 0x98);                                  // 0x00252414

    sprite->field_20 = 1.0f;                                    // 0x0025242C `vstmia`
    sprite->field_24 = 0.0f;
    sprite->field_28 = 0.25f;
    sprite->field_04 = 0x1F;                                    // 0x00252438 `stm r2,{r1,r7}`
    sprite->field_08 = arg1;
    sprite->field_10 = pose_arg;                                // 0x00252434 `str r5,[r4,#0x10]`
    sprite->field_30 = 0;                                       // 0x00252440
    sprite->field_5c = 1;                                       // 0x00252448

    void* row = AsdTable_FindBattleRow(id & 0xFFFFu);           // 0x00252444 `uxth r0,r6`
    sprite->field_4c = *reinterpret_cast<const s16*>(
        static_cast<const u8*>(row) + 0x88);                    // 0x00252450 `ldrsh r0,[r0,#0x88]`

    Npc2d_SetupSpriteData(sprite);                              // 0x00252458-0x0025247C

    sprite->field_00 = static_cast<u16>(0u - id);               // 0x00252480-0x0025248C
    sprite->field_38 = static_cast<u32>(Npc2d_PoseFromArgument(pose_arg)); // 0x00252490-0x002524C8
    sprite->field_18 = 1.0f / 3.0f;                             // 0x3EA8F5C3 (0x002524DC)

    return Npc2d_CreateWidget(sprite);                          // 0x002524F0
}

// ---------------------------------------------------------------------------
// 0x002860B4 -- create a 2D NPC sprite from an NPC-table row.
//
// Allocation: 0x98 bytes, line 0x2C8 (0x002860C0-0x002860F8).
// The row lookup is `AsdTable_FindNpcRow(id)` and the unsigned halfword at
// row+0x22 is negated into +0x4C (0x0028612C-0x00286138).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002860b4, 324)
void* Npc2d_func_002860b4(u32 id, u32 arg1, s32 pose_arg)
{
    Npc2dSprite* sprite = static_cast<Npc2dSprite*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x98, 1));                    // 0x002860EC
    AsdMem_Zero(sprite, 0x98);                                  // 0x002860F8

    sprite->field_20 = 1.0f;                                    // 0x00286110 `vstmia`
    sprite->field_24 = 0.0f;
    sprite->field_28 = 0.25f;
    sprite->field_04 = 0x1F;                                    // 0x0028611C `stm r2,{r1,r6}`
    sprite->field_08 = arg1;
    sprite->field_10 = pose_arg;                                // 0x00286118
    sprite->field_30 = 0;                                       // 0x00286124

    void* row = AsdTable_FindNpcRow(id);                        // 0x0028612C
    sprite->field_4c = -static_cast<s32>(
        *reinterpret_cast<const u16*>(static_cast<const u8*>(row) + 0x22)); // 0x00286130-0x00286138

    Npc2d_SetupSpriteData(sprite);                              // 0x0028613C-0x00286160

    sprite->field_00 = id;                                      // 0x0028616C `str r7,[r4]`
    sprite->field_38 = static_cast<u32>(Npc2d_PoseFromArgument(pose_arg)); // 0x00286164-0x002861A4
    sprite->field_18 = 1.0f / 3.0f;                             // 0x3EA8F5C3 (0x002861B8)

    return Npc2d_CreateWidget(sprite);                          // 0x002861CC
}

// ---------------------------------------------------------------------------
// 0x002FDFB8 -- create a 2D NPC sprite from TBB slot 0x1A.
//
// Allocation: 0x98 bytes, line 0x354 (0x002FDFC4-0x002FDFF4).
// `Tbb_GetGlobalSubTable(0x1A, 0)` is read at 0x002FE028; the caller's index
// selects a signed halfword from the payload ((index - 1) * 2, 0x002FE044).
// The table key pair is 2/+0x40 (0x002FE01C-0x002FE05C).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002fdfb8, 336)
void* Npc2d_func_002fdfb8(u32 row_index)
{
    Npc2dSprite* sprite = static_cast<Npc2dSprite*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x98, 1));                    // 0x002FDFE8
    AsdMem_Zero(sprite, 0x98);                                  // 0x002FDFF4

    sprite->field_20 = 1.0f;                                    // 0x002FE000
    sprite->field_24 = 1.0f;                                    // 0x002FE00C `vstmia`
    sprite->field_28 = 0.0f;
    sprite->field_04 = 4;                                       // 0x002FE014
    sprite->field_00 = 0;                                       // 0x002FE01C
    sprite->field_3c = 2;                                       // 0x002FE020

    const smt4::ui::Tbl1Header* table =
        smt4::ui::Tbb_GetGlobalSubTable(0x1A, 0);               // 0x002FE028-0x002FE030
    const void* payload = smt4::ui::Tbb_GetPayloadData(table);  // 0x002FE034
    // 0x002FE03C: the row count is fetched but r0 is immediately replaced by
    // the constant -8, so the result is not observed.
    (void)smt4::ui::Tbb_GetRowCount(table);

    const u8* row = static_cast<const u8*>(payload) + (row_index - 1) * 2; // 0x002FE044-0x002FE04C
    sprite->field_14 = -8;                                      // 0x002FE058 `mvn r0,#7`
    sprite->field_40 = static_cast<u32>(
        *reinterpret_cast<const s16*>(row));                    // 0x002FE054 `ldrsh r1,[r1]`
    sprite->field_10 = -0x38;                                   // 0x002FE060 `mvn r2,#0x37`

    Npc2d_LoadRowKey(sprite);                                   // 0x002FE064-0x002FE0B4

    sprite->field_18 = 1.0f / 3.0f;                             // 0x3EA8F5C3 (0x002FE0C8)

    return Npc2d_CreateWidget(sprite);                          // 0x002FE0DC
}

// ---------------------------------------------------------------------------
// 0x0031BDD0 -- create a 2D NPC sprite for a pose variant.
//
// If event bit 0x522 is set the row must already contain `arg2`
// (0x0031BDEC-0x0031BE0C), otherwise the sprite is not created.  The variant
// argument selects the +0x10/+0x1C/+0x24/+0x28 transform triple
// (0x0031BE98-0x0031BF00) and the +0x3C table key is 3 (0x0031BE78).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0031bdd0, 508)
void* Npc2d_func_0031bdd0(u32 id, u32 variant, u32 arg2)
{
    if (Flag_CheckEventBit(0x522)) {                            // 0x0031BDEC-0x0031BDF4
        void* row = AsdTable_FindNpcRow(id);                    // 0x0031BDF8-0x0031BDFC
        if (AsdTable_GetRowEntry(row, arg2) == nullptr) {       // 0x0031BE00-0x0031BE08
            return nullptr;                                    // 0x0031BE0C
        }
    }

    Npc2dSprite* sprite = static_cast<Npc2dSprite*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x98, 1));                    // 0x0031BE34
    AsdMem_Zero(sprite, 0x98);                                  // 0x0031BE40

    sprite->field_20 = 1.0f;                                    // 0x0031BE4C
    sprite->field_24 = 1.0f;                                    // 0x0031BE50
    sprite->field_28 = 0.0f;                                    // 0x0031BE58
    sprite->field_44 = -1;                                      // 0x0031BE5C `mvn r0,#0`
    sprite->field_00 = id;                                      // 0x0031BE64
    sprite->field_04 = 0x41;                                    // 0x0031BE68
    sprite->field_50 = arg2;                                    // 0x0031BE70
    sprite->field_3c = 3;                                       // 0x0031BE78

    sprite->field_54 = AsdTable_FindNpcRow(id);                 // 0x0031BE7C-0x0031BE80
    void* entry = AsdTable_GetRowEntry(sprite->field_54,
                                       sprite->field_50);       // 0x0031BE84-0x0031BE8C
    sprite->field_40 = *reinterpret_cast<const u16*>(entry);    // 0x0031BE8C-0x0031BE94

    switch (variant) {
    case 0:
        sprite->field_10 = 0xFFFFFFEC;                          // 0x0031BEB0 `mvn r0,#0x13` = -0x14
        sprite->field_1c = -48.0f;                              // 0x0031BEBC (0xC2400000)
        sprite->field_38 = 3;                                   // 0x0031BEC0
        break;
    case 1:
        sprite->field_10 = 0xA0;                                // 0x0031BEC8
        sprite->field_1c = 48.0f;                               // 0x0031BED8 (0x42400000)
        sprite->field_38 = 4;                                   // 0x0031BED4/0x0031BEFC
        break;
    case 2:
        sprite->field_10 = 0x48;                                // 0x0031BEE0
        sprite->field_28 = 0.25f;                               // 0x0031BEEC (0x3E800000)
        sprite->field_1c = 0.0f;                                // 0x0031BEF0 `vstr s16`
        sprite->field_24 = 0.0f;                                // 0x0031BEF8
        sprite->field_38 = 5;                                   // 0x0031BEF4/0x0031BEFC
        break;
    default:
        break;
    }

    Npc2d_LoadRowKey(sprite);                                   // 0x0031BF04-0x0031BF64

    sprite->field_18 = 0.3f;                                    // 0x3E99999A (0x0031BF78)

    return Npc2d_CreateWidget(sprite);                          // 0x0031BF8C
}

// ===========================================================================
// SmokeFade.cpp
// ===========================================================================

// ---------------------------------------------------------------------------
// 0x002CF0A0 -- construct the smoke-fade overlay and start its table load.
//
// Allocation: 0x28 bytes, line 0x59 (0x002CF0C4-0x002CF0E8).  Two draw
// widgets are parented on the calc widget returned by AsdUi_Create
// (0x002CF164 / 0x002CF18C).  The texture table at 0x0043DF40 has two 0x0C
// byte entries whose group/row lookups are forced at 0x002CF1B4-0x002CF214.
// The listing tail-calls 0x00297704 with ("event/smoke_fade.tbl", scene+8, 0)
// at 0x002CF228.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002cf0a0, 568)
void SmokeFade_func_002cf0a0(u32 arg0, u32 arg1)
{
    if (g_SmokeFade == nullptr) {                               // 0x002CF0B8-0x002CF0C0
        g_SmokeFade = static_cast<SmokeFadeScene*>(
            AsdMem_Alloc(0x100, 0x100, 0, 0x28, 1));                // 0x002CF0E4
    }

    SmokeFadeScene* scene = g_SmokeFade;

    // 0x002CF0F4-0x002CF11C: ten word-sized zero stores at +0x00..+0x24.
    scene->calc = nullptr;
    scene->field_04 = 0;
    scene->field_08 = 0;
    scene->field_0c = 0;
    scene->field_10 = 0;
    scene->field_14 = 0;
    scene->field_18 = 0;
    scene->field_1c = 0.0f;
    scene->field_20 = 0.0f;
    scene->field_24 = 0;

    // 0x002CF138: AsdUi_Create("SmokeFade Calc", 1, 0, 0,
    // cb0=0x001AD5F8, cb1=0, obj=nullptr).
    scene->calc = AsdUi_Create("SmokeFade Calc", 1, 0, 0,
                               0x001AD5F8, 0, nullptr);

    // 0x002CF164 / 0x002CF18C: both children use the calc widget as parent;
    // the returned handles are discarded (r0 is reloaded from +0x00).
    AsdUi_CreateLabel("SmokeFade DrawUpLeft", 0x81, 0, 0, 0x001AD3F0, 0,
                      nullptr,
                      static_cast<u32>(reinterpret_cast<std::uintptr_t>(scene->calc)));
    AsdUi_CreateLabel("SmokeFade DrawUpRight", 0xDF, 0, 0, 0x001AD3F0, 0,
                      nullptr,
                      static_cast<u32>(reinterpret_cast<std::uintptr_t>(scene->calc)));

    scene->field_18 = 0;                                        // 0x002CF190
    scene->field_0c = 0;                                        // 0x002CF198
    scene->field_24 = 0;                                        // 0x002CF19C
    scene->field_20 = 1.0f;                                     // 0x002CF1A0
    scene->field_1c = 1.0f;                                     // 0x002CF1A8
    scene->field_10 = arg0;                                     // 0x002CF1AC `strd r4,r5,[r7,#0x10]`
    scene->field_14 = arg1;

    for (u32 i = 0; i < 2; ++i) {
        SmokeFadeTexture* entry = &g_SmokeFadeTextures[i];      // sb + i*3 words (0x002CF1B4)

        if (AsdTMTexTable_IsGroupLoaded(entry->group_id) == 0) { // 0x002CF1B8-0x002CF1C8
            AsdTMTexTable_func_002c5b04(entry->group_id, 0);    // 0x002CF1D4
            entry->table_loaded = 1;                            // 0x002CF1DC `strb r8,[r0,#9]`
        }

        if (AsdRes_IsLoaded(entry->group_id, entry->row_id) == 0) { // 0x002CF1EC-0x002CF1F8
            AsdRes_Request(entry->group_id, entry->row_id);     // 0x002CF204
            entry->row_loaded = 1;                              // 0x002CF208 `strb r8,[r6,#8]`
        }
    }

    // 0x002CF21C-0x002CF22C: tail call with r0="event/smoke_fade.tbl",
    // r1=&scene->field_08, r2=0.
    ScriptVm_LoadTable("event/smoke_fade.tbl", &scene->field_08, 0);
}

// ===========================================================================
// EffectEditor.cpp
// ===========================================================================

// ---------------------------------------------------------------------------
// 0x0024246C -- rebuild the editor's scene list and service the two scene
// selection keys.
//
// Atlus source:
//   c:\SMT4\XRD686\AsdSDK\Source\Gfx\EffectEditor\EffectEditor.cpp
//
// Work buffer: count * 0x2C bytes from the 0x10000 work arena
// (0x00242470-0x002424AC).  The first count*0x18 bytes hold the 0x18-byte
// menu records, the remaining count*0x14 bytes hold the formatted labels
// (0x002424B4-0x00242530).  Return value (r6):
//   0x00800000 -- the slot selected by key 0 was rebuilt (0x002427AC);
//   0x00200001 -- key 1 stayed inactive across a reset (0x0024285C);
//   0           -- otherwise.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0024246c, 1272)
u32 EffectEditor_func_0024246c(void* owner, const EffectEditorSlot* slots,
                               u32 count)
{
    const u32 work_size = count * 0x2C;                         // 0x00242470-0x00242478
    u8* work = static_cast<u8*>(
        AsdWork_Alloc(0x10000, 0x100, 0, work_size, 0x10, 1));  // 0x002424AC

    EffectEditorMenuEntry* menu = reinterpret_cast<EffectEditorMenuEntry*>(work);
    char* label = reinterpret_cast<char*>(work + count * 0x18); // 0x002424B4-0x002424C4
    u32 menu_count = 0;                                         // 0x002424C8 `mov r5,sl`

    if (count != 0) {                                           // 0x002424BC-0x002424D0
        for (u32 i = 0; i < count; ++i) {
            const EffectEditorSlot* slot = reinterpret_cast<const EffectEditorSlot*>(
                reinterpret_cast<const u8*>(slots) + i * sizeof(EffectEditorSlot)); // 0x002424D4
            if (slot->desc == nullptr) {                        // 0x002424DC-0x002424E0
                continue;
            }

            UiText_Format(label, "%-14s", slot->desc->name);    // 0x002424E4-0x002424F0

            menu[menu_count].name = label;                      // 0x00242508 `str r1,[r0]`
            menu[menu_count].type = 0;                          // 0x00242510
            menu[menu_count].callback_a = nullptr;              // 0x00242514
            menu[menu_count].callback_b = nullptr;              // 0x0024251C
            menu[menu_count].payload = nullptr;                 // 0x00242518
            menu[menu_count].value = static_cast<f32>(i);       // 0x00242524 `vstr s0,[r0,#0x14]`
            ++menu_count;                                       // 0x00242520
            label += 0x14;                                      // 0x00242504
        }
    }

    EffectEditorWidget& list = g_EffectEditorList;              // 0x0044F8C8
    list.menu_count = menu_count;                               // 0x0024253C
    list.menu = menu;                                           // 0x00242540

    const EffectEditorMenuTarget* target =
        static_cast<const EffectEditorMenuTarget*>(g_EffectEditor.menu_current);
    list.field_04 = target->field_04;                           // 0x00242548-0x0024254C
    list.field_08 = target->field_08;                           // 0x00242550-0x00242554

    if (menu_count <= list.mode) {                              // 0x00242558-0x00242560 `subls`
        list.mode = menu_count - 1;
    }

    const u32 previous_selection = list.mode;                   // 0x0024256C-0x00242570
    list.owner = owner;                                         // 0x00242578

    if (g_EffectEditor.speed_mode == 0) {                       // 0x0024257C-0x00242588
        AsdUiObject_CreateAndReset(&list);
    }
    AsdUiObject_Update(&list);                                  // 0x002425A0

    u32 result;

    // 0x002425B8-0x002425E4: trigger2(0) or (reset(0), trigger2(0)) sends the
    // editor down the rebuild path; an untouched key falls to 0x00242830.
    if (Ui_PressedB(0) && menu_count != 0) {                    // 0x002425EC
        const u32 index = static_cast<u32>(menu[list.mode].value); // 0x002425F0-0x00242608
        const EffectEditorSlot* slot = reinterpret_cast<const EffectEditorSlot*>(
            reinterpret_cast<const u8*>(slots) + index * sizeof(EffectEditorSlot)); // 0x0024260C

        AsdDrawDesc_Init(reinterpret_cast<void*>(kEditorDrawDesc)); // 0x00242618

        void* part;
        if (slot->element != nullptr) {                         // 0x0024261C-0x00242628
            part = EffParts_LoadElement(slot->element);         // 0x0024262C
            AsdMem_Copy(slot->desc->data,
                        AsdRes_ResolveOffset(part),
                        slot->desc->data_size);                 // 0x00242638-0x00242648
        } else {
            part = EffParts_CreateById(slot->desc->id);         // 0x00242658-0x0024265C
            if (slot->desc->data != nullptr) {                  // 0x00242664-0x0024266C
                EffParts_SetData(part, slot->desc->data,
                                 slot->desc->data_size,
                                 slot->desc->key);              // 0x00242678
            }
            if (slot->desc->row != nullptr) {                   // 0x0024267C-0x00242684
                EffParts_SetRow(part, slot->desc->row,
                                slot->desc->key2);              // 0x00242690
            } else {
                u32 zero = 0;                                   // 0x002426B0 `str sl,[sp,#8]`
                EffParts_SetValue(part, &zero, 4, 4);           // 0x002426B4
            }
        }

        g_EffectEditor.field_4c = 0;                            // 0x002426C0
        g_EffectEditor.field_50 = 0;                            // 0x002426C8
        g_EffectEditor.field_54 = 1;                            // 0x002426CC `stm r2,{r1,sl}`
        g_EffectEditor.field_58 = 0;
        g_EffectEditor.field_60 = 0;                            // 0x002426D4
        g_EffectEditor.field_64 = 0;                            // 0x002426D8
        g_EffectEditor.field_68 = 0;                            // 0x002426DC

        u8* track = static_cast<u8*>(
            EffParts_WrapElement(g_EffectEditor.parts, part));  // 0x002426E0-0x002426E4
        g_EffectEditor.part_track = track;                      // 0x002426EC

        AsdString_Strcpy(reinterpret_cast<char*>(track + 0x9C),
                         slot->desc->name);                     // 0x002426F0-0x002426FC
        *reinterpret_cast<u32*>(track + 0x40) = slot->field_0c; // 0x00242700-0x0024270C
        *reinterpret_cast<u32*>(track + 0x44) = slot->field_10; // 0x00242710-0x00242714
        *reinterpret_cast<u32*>(track + 0x48) = slot->field_14; // 0x00242718-0x0024271C
        *reinterpret_cast<u8*>(track + 0x88) = 8;               // 0x00242720
        *reinterpret_cast<u8*>(track + 0x89) = 0;               // 0x00242724
        *reinterpret_cast<u8*>(track + 0x8A) = 0;               // 0x00242730

        // 0x00242734: AsdMem_CopyLarge(dst=0x004D8CA0, src=track, size=0x80).
        AsdMem_CopyLarge(reinterpret_cast<void*>(kEditorDrawDesc), track, 0x80);

        g_EffectEditor.element =
            *reinterpret_cast<void**>(track + 0x90);            // 0x00242738-0x0024273C

        if (slot->desc->data != nullptr) {                      // 0x00242740-0x0024274C
            EffParts_SetData(g_EffectEditor.element, slot->desc->data,
                             slot->desc->data_size,
                             slot->desc->key);                  // 0x00242758
        }

        void* active = AsdPart_Wrap(g_EffectEditor.element);    // 0x0024275C-0x00242760
        AsdPart_Update3(active);                                // 0x0024276C
        g_EffectEditor.active_element = active;                 // 0x00242770
        g_EffectEditor.menu_pending = slot->owner;              // 0x00242774-0x00242778

        const u32 part_count = AsdParts_Count(g_EffectEditor.parts); // 0x00242780
        if (part_count > 0x15) {                                // 0x00242784-0x00242794
            g_EffectEditor.list_offset = static_cast<s32>(part_count - 0x15);
            g_EffectEditorCursor.mode = 0x14;
        } else {
            g_EffectEditor.list_offset = 0;
            g_EffectEditorCursor.mode = part_count - 1;
        }

        // 0x002427A4-0x002427B0: the slot owner's +0x34 points at the cursor
        // widget (0x0044F858).
        *reinterpret_cast<void**>(static_cast<u8*>(slot->owner) + 0x34) =
            &g_EffectEditorCursor;

        g_EffectEditor.field_4c = 0;                            // 0x002427B8
        g_EffectEditor.field_50 = 0;                            // 0x002427BC
        g_EffectEditor.field_54 = 1;                            // 0x002427C0 `stm r0,{r2,sl}`
        g_EffectEditor.field_58 = 0;
        g_EffectEditor.field_60 = 0;                            // 0x002427C4
        g_EffectEditor.field_64 = 0;                            // 0x002427C8
        g_EffectEditor.field_68 = 0;                            // 0x002427CC

        result = 0x00800000u;                                   // 0x002427AC
        // 0x002427D0 -> 0x00242868: bit 0 is clear, so the work part closes.
        if (g_EffectEditor.work_part != nullptr) {              // 0x00242940-0x00242948
            AsdPart_Close(g_EffectEditor.work_part, 3);         // 0x00242950
            g_EffectEditor.work_part = nullptr;                 // 0x00242954
        }
    } else {
        // 0x00242830-0x00242860: 0x00200001 only when key 1 is inactive before
        // and after the reset.
        if (UiInput_Trigger2(1) == 0) {                         // 0x00242830-0x00242840
            UiInput_Reset(1);                                   // 0x00242848
            result = UiInput_Trigger2(1) == 0 ? 0x00200001u : 0u; // 0x00242854-0x0024285C
        } else {
            result = 0;                                         // 0x00242864
        }

        if ((result & 1u) != 0) {                               // 0x00242868-0x0024286C
            if (menu_count != 0) {                              // 0x00242870-0x00242874
                const u32 selection = list.mode;                // 0x0024287C
                const u32 index = static_cast<u32>(
                    menu[selection].value);                     // 0x00242880-0x0024289C
                const EffectEditorSlot* slot =
                    reinterpret_cast<const EffectEditorSlot*>(
                        reinterpret_cast<const u8*>(slots) +
                        index * sizeof(EffectEditorSlot));      // 0x002428BC

                bool unchanged = false;
                if (g_EffectEditor.work_part != nullptr) {      // 0x00242880-0x002428A0
                    if (selection == previous_selection) {      // 0x002428A8
                        unchanged = true;                       // 0x002428AC -> epilogue
                    } else {
                        AsdPart_Close(g_EffectEditor.work_part, 3); // 0x002428B4
                        g_EffectEditor.work_part = nullptr;     // 0x002428B8
                    }
                }

                if (!unchanged && slot->element != nullptr) {   // 0x002428C0-0x002428C8
                    if (g_EffectEditor.selected_part != nullptr) { // 0x002428CC-0x002428D4
                        AsdPart_Release(g_EffectEditor.selected_part, 3); // 0x002428DC
                        g_EffectEditor.selected_part = nullptr;  // 0x002428E0
                    }

                    AsdDrawDesc_Init(reinterpret_cast<void*>(kEditorDrawDesc)); // 0x002428E8
                    *reinterpret_cast<u32*>(
                        reinterpret_cast<u8*>(kEditorDrawDesc) + 0x40) = slot->field_0c; // 0x002428F4
                    *reinterpret_cast<u32*>(
                        reinterpret_cast<u8*>(kEditorDrawDesc) + 0x44) = slot->field_10; // 0x002428FC
                    *reinterpret_cast<u32*>(
                        reinterpret_cast<u8*>(kEditorDrawDesc) + 0x48) = slot->field_14; // 0x00242904

                    void* element = EffParts_LoadElement(slot->element); // 0x00242908-0x0024290C
                    g_EffectEditor.work_part = AsdPart_Wrap(element); // 0x00242918
                    AsdPart_Close(element, 3);                  // 0x00242928
                }
            }
        } else if (g_EffectEditor.work_part != nullptr) {       // 0x00242940-0x00242948
            AsdPart_Close(g_EffectEditor.work_part, 3);         // 0x00242950
            g_EffectEditor.work_part = nullptr;                 // 0x00242954
        }
    }

    AsdMem_Free(work);                                          // 0x00242930
    return result;                                              // 0x00242938
}

} // namespace smt4::engine
