#pragma once
#include <cstddef>
#include "types.h"
#include "engine/asd_model.h"
#include "engine/asd_text.h"
#include "engine/asd_texture.h"

/**
 * FrameTex / Npc2d / SmokeFade scene objects and the EffectEditor scene-list
 * hook reconstructed in `src/engine/asd_frame.cpp`.
 *
 * The eight functions come from four original translation units:
 *
 *   FrameTex      c:\SMT4\XRD686\sdds4\program\frame_tex\FrameTex.cpp
 *   Npc2d         c:\SMT4\XRD686\sdds4\program\event\2dEvent\Npc2d.cpp
 *   SmokeFade     c:\SMT4\XRD686\sdds4\program\event\2dEvent\SmokeFade.cpp
 *   EffectEditor  c:\SMT4\XRD686\AsdSDK\Source\Gfx\EffectEditor\EffectEditor.cpp
 *
 * Every field carries the instruction and address that proves it.  Objects
 * allocated by `AsdMem_Alloc(..., size, 1)` in the listing carry a `sizeof`
 * assertion; input records owned by other TUs only assert their offsets.
 */

namespace smt4::engine {

// ---------------------------------------------------------------------------
// FrameTex.cpp (0x00104378, 0x00280D30)
// ---------------------------------------------------------------------------

/**
 * FrameTex scene singleton (`g_FrameTex`, 0x0043E278).
 *
 * Allocated as exactly 0xFEC bytes by `FrameTex_func_00104378`
 * (`mov r5,#0xfec`, 0x0010438C) and zeroed with `AsdMem_Zero(r4, 0xfec)`
 * (0x001043BC).
 */
struct FrameTexScene {
    void* main_widget;                  // +0x00: `str r0,[r4]` (0x001044A8)
    AsdTexture* textures[2];            // +0x04/+0x08: `str r0,[r4,#4]`/`[r4,#8]` (0x001043C8/0x001043D4)
    u8  field_0c;                       // +0x0C: `strb r5,[r4,#0xc]` (0x001043F8)
    u32 field_10;                       // +0x10: `str r5,[r4,#0x10]` (0x001043FC)
    u32 field_14;                       // +0x14: `str r5,[r4,#0x14]` (0x00104400)
    u32 field_18;                       // +0x18: `str r5,[r4,#0x18]` (0x00104404)
    u8  field_1c;                       // +0x1C: `strb r5,[r4,#0x1c]` (0x0010440C)
    u8  pad_1d[0x0B];                   // +0x1D..+0x28
    f32 field_28;                       // +0x28: `vstr s0` with 0.25f (0x00104458)
    f32 field_2c;                       // +0x2C: `vstr s0` with 0.25f (0x0010445C)
    f32 field_30;                       // +0x30: `vstr s1` with 20.0f (0x00104460)
    smt4::ui::AsdLayoutRect header;     // +0x34: `add r0,r4,#0x34` (0x00104408/0x00104448)
    u8  pad_54[0xE38];                  // +0x54..+0xE8C
    u8  field_e8c;                      // +0xE8C: `strb r5,[r2,#0xe8c]` (0x00104474)
    u8  pad_e8d[0x08];                  // +0xE8D..+0xE95
    u8  field_e95;                      // +0xE95: `strb r6,[r5,#0xe95]` (0x00280DD4)
    u8  field_e96;                      // +0xE96: `strb r6,[r5,#0xe96]` (0x00280DD0)
    u8  pad_e97[0x45];                  // +0xE97..+0xEDC
    u8  field_edc;                      // +0xEDC: `strb r5,[r2,#0xedc]` (0x00104478)
    u8  pad_edd[0x43];                  // +0xEDD..+0xF20
    AsdTexture* overlay_textures[2];    // +0xF20/+0xF24: `str r0,[r4,#0xf20]`/`[r4,#0xf24]` (0x001043E0/0x001043EC)
    u8  field_f28;                      // +0xF28: `strb r5,[r4,#0xf28]` (0x0010447C)
    u8  pad_f29[0x02];                  // +0xF29..+0xF2B
    u8  field_f2b;                      // +0xF2B: `strb r5,[r4,#0xf2b]` (0x00104480)
    u8  field_f2c;                      // +0xF2C: `strb r5,[r4,#0xf2c]` (0x00104484)
    u8  pad_f2d[0x6B];                  // +0xF2D..+0xF98
    u8  field_f98;                      // +0xF98: `strb r5,[r4,#0xf98]` (0x00104488)
    u8  field_f99;                      // +0xF99: `strb r5,[r4,#0xf99]` (0x0010448C)
    u8  pad_f9a[0x3E];                  // +0xF9A..+0xFD8
    u8  field_fd8;                      // +0xFD8: `strb r6,[r5,#0xfd8]` (0x00280DCC)
    u8  pad_fd9[0x03];                  // +0xFD9..+0xFDC
    AsdTexture* field_fdc;              // +0xFDC: `ldr r0,[r5,#0xfdc]` (0x00280D4C)
    u8  field_fe0;                      // +0xFE0: `strb r6,[r5,#0xfe0]` (0x00280D80)
    u8  pad_fe1[0x03];                  // +0xFE1..+0xFE4
    AsdTexture* field_fe4;              // +0xFE4: `str r4,[r5,#0xfe4]` (0x00280E90)
    AsdTexture* field_fe8;              // +0xFE8: `str r4,[r5,#0xfe8]` (0x00280EF0)
};
static_assert(offsetof(FrameTexScene, textures) == 0x04);
static_assert(offsetof(FrameTexScene, field_0c) == 0x0C);
static_assert(offsetof(FrameTexScene, field_28) == 0x28);
static_assert(offsetof(FrameTexScene, header) == 0x34);
static_assert(offsetof(FrameTexScene, field_e8c) == 0xE8C);
static_assert(offsetof(FrameTexScene, field_e95) == 0xE95);
static_assert(offsetof(FrameTexScene, field_edc) == 0xEDC);
static_assert(offsetof(FrameTexScene, overlay_textures) == 0xF20);
static_assert(offsetof(FrameTexScene, field_fd8) == 0xFD8);
static_assert(offsetof(FrameTexScene, field_fdc) == 0xFDC);
static_assert(offsetof(FrameTexScene, field_fe0) == 0xFE0);
static_assert(sizeof(FrameTexScene) == 0xFEC);   // `mov r5,#0xfec` (0x0010438C)

extern FrameTexScene* g_FrameTex;       // 0x0043E278

// ---------------------------------------------------------------------------
// Npc2d.cpp (0x002523D0, 0x002860B4, 0x002FDFB8, 0x0031BDD0)
// ---------------------------------------------------------------------------

/**
 * 0x98-byte 2D-NPC sprite allocated by all four Npc2d functions
 * (`mov r3,#0x98` / `AsdMem_Zero(r4, 0x98)`).
 */
struct Npc2dSprite {
    u32 field_00;                       // +0x00: `str r0,[r4]` (0x0025248C / 0x0028616C / 0x0031BE64)
    u32 field_04;                       // +0x04: `stm r2,{r1,r7}` with r1=0x1F (0x00252438);
                                        //        `mov r1,#4`/`#0x41` (0x002FE014 / 0x0031BE68)
    u32 field_08;                       // +0x08: `stm r2,{r1,r7}` with r7=arg1 (0x00252438)
    u32 field_0c;                       // +0x0C: reset/loading state: 1 or 2 (0x00252460/0x0025247C)
    u32 field_10;                       // +0x10: `str r5,[r4,#0x10]` (0x00252434)
    s32 field_14;                       // +0x14: `str r0,[r4,#0x14]` with r0=-8 (0x002FE058)
    f32 field_18;                       // +0x18: `vstr s0` 1/3 (0x002524DC) or 0.3 (0x0031BF78)
    f32 field_1c;                       // +0x1C: -48/48/0 in the variant switch (0x0031BEBC/0x0031BED8/0x0031BEF0)
    f32 field_20;                       // +0x20: `vstmia r2,{s0,s1,s2}` 1.0 (0x0025242C)
    f32 field_24;                       // +0x24: 0.0 (0x0025242C) / 1.0 (0x0031BE50)
    f32 field_28;                       // +0x28: 0.25 (0x0025242C) / 0.0 (0x002FE004)
    u8  pad_2c[0x04];                   // +0x2C..+0x30
    u8  field_30;                       // +0x30: `strb r0,[r4,#0x30]` (0x00252440)
    u8  pad_31[0x07];                   // +0x31..+0x38
    u32 field_38;                       // +0x38: `str r0,[r4,#0x38]` (0x002524C8 / 0x002861A4 / 0x0031BEC0)
    u32 field_3c;                       // +0x3C: table key 2/3 (0x002FE020 / 0x0031BE78)
    u32 field_40;                       // +0x40: row key (0x002FE05C / 0x0031BE94)
    s32 field_44;                       // +0x44: `mvn r0,#0` = -1 (0x0031BE5C)
    u32 field_48;                       // +0x48: `str r0,[r4,#0x48]` (0x00252478)
    s32 field_4c;                       // +0x4C: row +0x88 / -row +0x22 (0x00252454 / 0x00286138)
    u32 field_50;                       // +0x50: `str r5,[r4,#0x50]` argument (0x0031BE70)
    void* field_54;                     // +0x54: `str r0,[r4,#0x54]` NPC row (0x0031BE80)
    u8  pad_58[0x04];                   // +0x58..+0x5C
    u8  field_5c;                       // +0x5C: `strb r8,[r4,#0x5c]` = 1 (0x00252448)
    u8  pad_5d[0x3B];                   // +0x5D..+0x98
};
static_assert(offsetof(Npc2dSprite, field_04) == 0x04);
static_assert(offsetof(Npc2dSprite, field_0c) == 0x0C);
static_assert(offsetof(Npc2dSprite, field_14) == 0x14);
static_assert(offsetof(Npc2dSprite, field_18) == 0x18);
static_assert(offsetof(Npc2dSprite, field_1c) == 0x1C);
static_assert(offsetof(Npc2dSprite, field_20) == 0x20);
static_assert(offsetof(Npc2dSprite, field_30) == 0x30);
static_assert(offsetof(Npc2dSprite, field_38) == 0x38);
static_assert(offsetof(Npc2dSprite, field_3c) == 0x3C);
static_assert(offsetof(Npc2dSprite, field_44) == 0x44);
static_assert(offsetof(Npc2dSprite, field_48) == 0x48);
static_assert(offsetof(Npc2dSprite, field_4c) == 0x4C);
static_assert(offsetof(Npc2dSprite, field_54) == 0x54);
static_assert(offsetof(Npc2dSprite, field_5c) == 0x5C);
static_assert(sizeof(Npc2dSprite) == 0x98);      // `mov r3,#0x98` (0x00252400)

// ---------------------------------------------------------------------------
// SmokeFade.cpp (0x002CF0A0)
// ---------------------------------------------------------------------------

/**
 * One 0xC-byte entry of the two-entry texture table at 0x0043DF40.
 *
 * `r4 = i*3` and `ldr r0,[sb,r4,lsl #2]` (0x002CF1B4/0x002CF1B8) index the
 * table at a 12-byte stride; the flags at +0x08/+0x09 are raised after the
 * table/row lookups succeed (0x002CF1DC / 0x002CF208).
 */
struct SmokeFadeTexture {
    u32 group_id;                       // +0x00: `ldr r0,[sb,r4,lsl #2]` (0x002CF1B8)
    u32 row_id;                         // +0x04: `ldr r1,[r6,#4]` (0x002CF1E8)
    u8  row_loaded;                     // +0x08: `strb r8,[r6,#8]` (0x002CF208)
    u8  table_loaded;                   // +0x09: `strb r8,[r0,#9]` (0x002CF1DC)
    u8  pad_0a[0x02];                   // +0x0A..+0x0C
};
static_assert(offsetof(SmokeFadeTexture, row_id) == 0x04);
static_assert(offsetof(SmokeFadeTexture, row_loaded) == 0x08);
static_assert(offsetof(SmokeFadeTexture, table_loaded) == 0x09);
static_assert(sizeof(SmokeFadeTexture) == 0x0C);

/**
 * SmokeFade singleton (`g_SmokeFade`, 0x0043DF28), allocated as exactly
 * 0x28 bytes (`mov r3,#0x28`, 0x002CF0D4).
 */
struct SmokeFadeScene {
    void* calc;                         // +0x00: `str r0,[r7]` (0x002CF13C)
    u32 field_04;                       // +0x04: zero-fill only (0x002CF0F8); child handle discarded
    u32 field_08;                       // +0x08: zero-fill only (0x002CF0FC); child handle discarded
    u32 field_0c;                       // +0x0C: `str r6,[r7,#0xc]` (0x002CF198)
    u32 field_10;                       // +0x10: `strd r4,r5,[r7,#0x10]` (0x002CF1AC)
    u32 field_14;                       // +0x14: second half of the same `strd`
    u32 field_18;                       // +0x18: `str r6,[r7,#0x18]` (0x002CF190)
    f32 field_1c;                       // +0x1C: `vstr s0` 1.0f (0x002CF1A8)
    f32 field_20;                       // +0x20: `vstr s0` 1.0f (0x002CF1A0)
    u32 field_24;                       // +0x24: word clear (0x002CF11C); byte store 0 (0x002CF19C)
};
static_assert(offsetof(SmokeFadeScene, field_0c) == 0x0C);
static_assert(offsetof(SmokeFadeScene, field_10) == 0x10);
static_assert(offsetof(SmokeFadeScene, field_14) == 0x14);
static_assert(offsetof(SmokeFadeScene, field_1c) == 0x1C);
static_assert(offsetof(SmokeFadeScene, field_24) == 0x24);
static_assert(sizeof(SmokeFadeScene) == 0x28);    // `mov r3,#0x28` (0x002CF0D4)

extern SmokeFadeScene* g_SmokeFade;              // 0x0043DF28
extern SmokeFadeTexture g_SmokeFadeTextures[2];  // 0x0043DF40

// ---------------------------------------------------------------------------
// EffectEditor scene-list hook (0x0024246C)
// ---------------------------------------------------------------------------

/**
 * Descriptor reached through `EffectEditorSlot::desc`.
 *
 * `name` at +0x00 is formatted into the menu (`ldr r2,[r0]`, 0x002424E4),
 * +0x04 is the 16-bit part id handed to 0x00192168 (0x00242658), +0x08 is the
 * 16-bit source key for 0x0024972C (0x00242670), +0x0C/+0x10 are the copy
 * source and length (0x00242664/0x00242674), +0x18 is the key for 0x001E192C
 * (0x00242688) and +0x1C its pointer (0x0024267C).
 */
struct EffectEditorPartDesc {
    const char* name;                   // +0x00
    u16 id;                             // +0x04
    u8  pad_06[0x02];                   // +0x06..+0x08
    u16 key;                            // +0x08
    u8  pad_0a[0x02];                   // +0x0A..+0x0C
    void* data;                         // +0x0C
    u32 data_size;                      // +0x10
    u32 value;                          // +0x14: never read by 0x0024246C
    u16 key2;                           // +0x18
    u8  pad_1a[0x02];                   // +0x1A..+0x1C
    void* row;                          // +0x1C
};
static_assert(offsetof(EffectEditorPartDesc, id) == 0x04);
static_assert(offsetof(EffectEditorPartDesc, key) == 0x08);
static_assert(offsetof(EffectEditorPartDesc, data) == 0x0C);
static_assert(offsetof(EffectEditorPartDesc, data_size) == 0x10);
static_assert(offsetof(EffectEditorPartDesc, key2) == 0x18);
static_assert(offsetof(EffectEditorPartDesc, row) == 0x1C);
static_assert(sizeof(EffectEditorPartDesc) == 0x20);

/**
 * One 0x1C-byte input record of `EffectEditor_func_0024246c`.
 *
 * The caller's array is walked with `rsb r0,r4,r4,lsl #3` /
 * `ldr r0,[r8,r0,lsl #2]` (0x002424D4/0x002424D8), i.e. a 28-byte stride.
 */
struct EffectEditorSlot {
    EffectEditorPartDesc* desc;         // +0x00: `ldr r2,[r0]` (0x002424E4)
    void* owner;                        // +0x04: `ldr r0,[r4,#4]` (0x00242774/0x002427A4)
    void* element;                      // +0x08: `ldr r0,[r4,#8]` (0x0024261C)
    u32 field_0c;                       // +0x0C: `ldr r1,[r4,#0xc]` (0x00242700)
    u32 field_10;                       // +0x10: `ldr r1,[r4,#0x10]` (0x00242710)
    u32 field_14;                       // +0x14: `ldr r1,[r4,#0x14]` (0x00242718)
    u8  pad_18[0x04];                   // +0x18..+0x1C: unobserved fourth word,
                                        //        present only to reach the 0x1C stride
};
static_assert(offsetof(EffectEditorSlot, owner) == 0x04);
static_assert(offsetof(EffectEditorSlot, element) == 0x08);
static_assert(offsetof(EffectEditorSlot, field_0c) == 0x0C);
static_assert(offsetof(EffectEditorSlot, field_14) == 0x14);
static_assert(sizeof(EffectEditorSlot) == 0x1C);

/**
 * Prefix of the object `g_EffectEditor.menu_current` points to; only the two
 * words copied into `g_EffectEditorList` are modelled
 * (`ldr r2,[r1,#4]` / `ldr r1,[r1,#8]`, 0x00242548/0x00242550).
 */
struct EffectEditorMenuTarget {
    u8  pad_00[0x04];                   // +0x00..+0x04
    u32 field_04;                       // +0x04
    u32 field_08;                       // +0x08
};
static_assert(offsetof(EffectEditorMenuTarget, field_04) == 0x04);
static_assert(offsetof(EffectEditorMenuTarget, field_08) == 0x08);

extern EffectEditorWidget g_EffectEditorCursor;     // 0x0044F858
extern EffectEditorWidget g_EffectEditorList;       // 0x0044F8C8

// ---------------------------------------------------------------------------
// Ledger entry points (address / size match config/functions.csv)
// ---------------------------------------------------------------------------

void  FrameTex_func_00104378();                             // 0x00104378, 1508 B
void  FrameTex_func_00280d30(u32 alternate);                // 0x00280d30,  524 B
void* Npc2d_func_002523d0(u32 id, u32 arg1, s32 pose_arg);  // 0x002523d0,  336 B
void* Npc2d_func_002860b4(u32 id, u32 arg1, s32 pose_arg);  // 0x002860b4,  324 B
void* Npc2d_func_002fdfb8(u32 row_index);                   // 0x002fdfb8,  336 B
void* Npc2d_func_0031bdd0(u32 id, u32 variant, u32 arg2);   // 0x0031bdd0,  508 B
void  SmokeFade_func_002cf0a0(u32 arg0, u32 arg1);           // 0x002cf0a0,  568 B
u32   EffectEditor_func_0024246c(void* owner,
                                 const EffectEditorSlot* slots,
                                 u32 count);                 // 0x0024246c, 1272 B

} // namespace smt4::engine
