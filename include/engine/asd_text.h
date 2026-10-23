#pragma once
#include <cstddef>
#include "types.h"

/**
 * Atlus AsdSDK text / font / list-box layout objects.
 *
 * The functions reconstructed in `src/engine/asd_text.cpp` come from three
 * different original translation units:
 *
 *   AsdText   c:\SMT4\XRD686\AsdSDK\Source\Gfx\Text\AsdText.cpp
 *   AsdFont   c:\SMT4\XRD686\AsdSDK\Source\Gfx\Font\AsdFont.cpp
 *   message   c:\SMT4\XRD686\sdds4\program\font\message.cpp
 *   AsdListBox c:\SMT4\XRD686\AsdSDK\Source\Util\AsdListBox.cpp
 *
 * Per the milestone preflight ruling the `AsdText` / `AsdFont` ledger entries
 * live in `smt4::engine` while the `message` / `AsdListBox` entries live in
 * `smt4::ui`.  Both groups are declared here because they share the glyph /
 * font hand-off structures.
 *
 * Every named field below is backed by an `LDR/STR [reg, #imm]` (or a
 * `LDM/STM` base+offset) inside one of the eight reconstructed functions.
 * Unproven ranges stay as `pad_NN`.
 */

namespace smt4::engine {

// ---------------------------------------------------------------------------
// AsdText (0x00286c5c / 0x00296de0)
// ---------------------------------------------------------------------------

/**
 * One 32-byte laid-out glyph record in `AsdText::glyphs`.
 *
 * `+0x00` receives the (byte-swapped) source code, `+0x04` is the 24-byte
 * destination block handed to the font-info virtual `+0x40` callback and
 * `+0x1C` receives the result of `AsdFont_GetGlyph` (0x00248130).
 */
struct AsdTextGlyph {
    u16 code;                           // +0x00: `strh r6,[r7]` (0x00286e4c)
    u8  pad_02[0x02];                   // +0x02..+0x04
    u8  shape[0x18];                    // +0x04: `add r1,r7,#4` -> vtable+0x40
    void* bitmap;                       // +0x1C: `str r0,[r7,#0x1c]` (0x00286f38)
};
static_assert(offsetof(AsdTextGlyph, shape) == 0x04);
static_assert(offsetof(AsdTextGlyph, bitmap) == 0x1C);
static_assert(sizeof(AsdTextGlyph) == 0x20);

struct AsdFontEntry;
struct AsdFontInfo;
struct AsdFontHeader;
struct AsdFontTexture;

/**
 * `AsdText` instance.  Offsets are the union of the stores in
 * `AsdText_func_00286c5c`; the glyph buffer is allocated as
 * `count * 32` bytes (0x00286d70).
 */
struct AsdText {
    AsdTextGlyph* glyphs;               // +0x00: `str r0,[r5]` (0x00286d84)
    u32 glyph_count;                    // +0x04: `str r0,[r5,#4]` (0x00286d5c)
    u32 field_08;                       // +0x08: cleared (0x00286cec)
    u32 field_0c;                       // +0x0C: cleared (0x00286cf4)
    u32 field_10;                       // +0x10: cleared (0x00286cf0)
    AsdFontEntry* font;                 // +0x14: `str r1,[r5,#0x14]` (0x00286ca4)
    f32 scale_x;                        // +0x18: `vstr s1,[r5,#0x18]` (0x00286c88)
    f32 scale_y;                        // +0x1C: `vstr s0,[r5,#0x1c]` (0x00286c90)
    s32 mode;                           // +0x20: `str r0,[r5,#0x20]` (0x00286c84)
    u32 field_24;                       // +0x24: cleared (0x00286ce8)
    u8  pad_28[0x0C];                   // +0x28..+0x34
    u32 flags;                          // +0x34: `bic r0,r0,#0x10` (0x00286ce0)
    u8  pad_38[0x04];                   // +0x38..+0x3C
    s32 line_count;                     // +0x3C: `str r7,[r5,#0x3c]` = 1 (0x00286dc8)
    u32 field_40;                       // +0x40: cleared (0x00286cf8)
    u8  field_44;                       // +0x44: `strb r7,[r5,#0x44]` = 1 (0x00286cfc)
    u8  pad_45[0x01];                   // +0x45
    u16 field_46;                       // +0x46: `strh r6,[r5,#0x46]` (0x00286d00)
    u16 field_48;                       // +0x48: `strh r6,[r5,#0x48]` (0x00286d04)
    u8  pad_4a[0x02];                   // +0x4A..+0x4C
    f32 field_4c;                       // +0x4C: `vstr s16,[r5,#0x4c]` (0x00286d08)
    s32 font2_id;                       // +0x50: compared with -1 (0x00286ca8)
    AsdFontEntry* font2;                // +0x54: `str r0,[r5,#0x54]` (0x00286cb8)
    u8  pad_58[0x04];                   // +0x58..+0x5C
    u32 field_5c[16];                   // +0x5C..+0x98: sixteen stores (0x00286dd0..0x00286e1c)
    s32 font3_id;                       // +0x9C: compared with -1 (0x00286cc0)
    u8  pad_a0[0x04];                   // +0xA0..+0xA4
    AsdFontEntry* font3;                // +0xA4: `str r0,[r5,#0xa4]` (0x00286cd0)
    u8  pad_a8[0x08];                   // +0xA8..+0xB0
    u32 field_b0;                       // +0xB0: cleared (0x00286d0c)
};
static_assert(offsetof(AsdText, glyph_count) == 0x04);
static_assert(offsetof(AsdText, font) == 0x14);
static_assert(offsetof(AsdText, scale_x) == 0x18);
static_assert(offsetof(AsdText, mode) == 0x20);
static_assert(offsetof(AsdText, flags) == 0x34);
static_assert(offsetof(AsdText, line_count) == 0x3C);
static_assert(offsetof(AsdText, font2_id) == 0x50);
static_assert(offsetof(AsdText, font2) == 0x54);
static_assert(offsetof(AsdText, field_5c) == 0x5C);
static_assert(offsetof(AsdText, font3_id) == 0x9C);
static_assert(offsetof(AsdText, font3) == 0xA4);
static_assert(offsetof(AsdText, field_b0) == 0xB0);

/**
 * Global code table used while normalising control code points
 * (`0x00464D48`). `+0x02` is the fallback glyph code and `+0x20` the code
 * that is remapped to `0x8140` in the primary-font path. Other words are
 * retained as address-pinned fields until their meanings are recovered; the
 * startup clear at `0x003EBF08` reaches through offsets `+0x38` and `+0x3C`.
 */
struct AsdTextCodes {
    u8  pad_00[0x02];                   // +0x00..+0x02
    u16 default_code;                   // +0x02: `ldrh r6,[r0,#2]` (0x00286fc4)
    u8  pad_04[0x10];                   // +0x04..+0x14
    u32 field_14;                       // +0x14: 0x0010af38 setter
    u32 field_18;                       // +0x18: not yet identified
    u32 field_1c;                       // +0x1C: 0x0010a6fc setter
    u32 special_code;                   // +0x20: `ldr r0,[r0,#0x20]` (0x00286fcc)
    u8  pad_24[0x0C];                   // +0x24..+0x30
    u32 field_30;                       // +0x30: 0x0010b340 setter
    u32 field_34;                       // +0x34: not yet identified
    u32 field_38;                       // +0x38: startup clear sentinel
    u32 field_3c;                       // +0x3C: startup clear sentinel
};
static_assert(offsetof(AsdTextCodes, default_code) == 0x02);
static_assert(offsetof(AsdTextCodes, field_14) == 0x14);
static_assert(offsetof(AsdTextCodes, field_1c) == 0x1C);
static_assert(offsetof(AsdTextCodes, special_code) == 0x20);
static_assert(offsetof(AsdTextCodes, field_30) == 0x30);
static_assert(offsetof(AsdTextCodes, field_38) == 0x38);
static_assert(offsetof(AsdTextCodes, field_3c) == 0x3C);
static_assert(sizeof(AsdTextCodes) == 0x40);

extern AsdTextCodes g_AsdTextCodes;     // 0x00464D48
void AsdText_SetCodeField14(u32 val);    // 0x0010af38
void AsdText_SetCodeField1C(u32 val);    // 0x0010a6fc
void AsdText_SetCodeField30(u32 val);    // 0x0010b340

// ---------------------------------------------------------------------------
// AsdFont (0x0010a588 / 0x002c4710)
// ---------------------------------------------------------------------------

/**
 * Chunk header walked by the linear scanner in `AsdFont_func_002c4710`.
 * The record is tagged with `0x464E4946` ("FINF") and the scan stores
 * `cursor + 8` in `AsdFontEntry::field_04`; the real header pointer is the
 * word at `cursor + 0x10`.
 */
struct AsdFontChunk {
    u32 tag;                            // +0x00: compared against 0x464E4946
    u32 next;                           // +0x04: `ldr r5,[r0,#4]` (0x002c4838)
    u8  pad_08[0x08];                   // +0x08..+0x10
    AsdFontHeader* header;              // +0x10: `ldr r5,[r1,#8]` with r1=cursor+8
};
static_assert(offsetof(AsdFontChunk, next) == 0x04);
static_assert(offsetof(AsdFontChunk, header) == 0x10);

/**
 * Font description header reached through `AsdFontChunk::header`.
 * `+0x04` is both the per-glyph source stride and a raw word copied into
 * `AsdFontTexture::field_28`; `+0x08`/`+0x0A` are the glyph count and format
 * selector used by the 12-entry jump table at 0x002C48A8.
 */
struct AsdFontHeader {
    u8  pad_00[0x04];                   // +0x00..+0x04
    u32 glyph_stride;                   // +0x04: `lsl r7,r7,...`/`add r7,r7,r0` (0x002c4a64)
    u16 glyph_count;                    // +0x08: `ldrh r0,[r5,#8]` (0x002c4858)
    u16 format;                         // +0x0A: `ldrh r0,[r5,#0xa]` (0x002c4894)
    u8  pad_0c[0x04];                   // +0x0C..+0x10
    u16 width;                          // +0x10: `ldrh r2,[r5,#0x10]` (0x002c4a24)
    u16 height;                         // +0x12: `ldrh r3,[r5,#0x12]` (0x002c4a28)
    void* glyph_data;                   // +0x14: `ldr r1,[r5,#0x14]` (0x002c4a20)
};
static_assert(offsetof(AsdFontHeader, glyph_stride) == 0x04);
static_assert(offsetof(AsdFontHeader, glyph_count) == 0x08);
static_assert(offsetof(AsdFontHeader, format) == 0x0A);
static_assert(offsetof(AsdFontHeader, width) == 0x10);
static_assert(offsetof(AsdFontHeader, height) == 0x12);
static_assert(offsetof(AsdFontHeader, glyph_data) == 0x14);
static_assert(sizeof(AsdFontHeader) == 0x18);

/** Virtual slots actually observed on the font-info object (0x00286fac). */
struct AsdFontInfoVtable {
    u8  pad_00[0x40];                   // +0x00..+0x40
    void (*store)(AsdFontInfo* self, void* dst, u32 code);  // +0x40 (0x00286ff4)
    int  (*has_glyph)(AsdFontInfo* self, u32 code);         // +0x44 (0x00286fb0)
};

/**
 * Font-info object stored at `AsdFontEntry::field_08`.  Only the vtable word
 * is read by the two reconstructed AsdFont functions.
 */
struct AsdFontInfo {
    AsdFontInfoVtable* vtable;          // +0x00: `ldr r0,[r0]` (0x00286fac)
};
static_assert(offsetof(AsdFontInfo, vtable) == 0x00);

/**
 * One 44-byte entry in the global font table at `0x00464A70`.
 * Table base/count live in `AsdFontManager` (+0x00/+0x04); the getter
 * 0x002AED40 and the inlined index math in 0x002C4730 both use a 44-byte
 * stride.
 */
struct AsdFontEntry {
    void* resource;                     // +0x00: arg stored by 0x002c47d8
    u8*   chunk;                        // +0x04: `str r1,[r4,#4]` = tagged cursor+8
    AsdFontInfo* info;                  // +0x08: 0x18-byte object (0x002c47ec)
    AsdFontTexture** textures;          // +0x0C: `str r0,[r4,#0xc]` (0x002c4880)
    u32 texture_count;                  // +0x10: `str r0,[r4,#0x10]` (0x002c488c)
    u16 format;                         // +0x14: `strh r0,[r4,#0x14]` (0x002c489c)
    u8  pad_16[0x02];                   // +0x16..+0x18
    u32 field_18;                       // +0x18: switch result (0x002c4a2c)
    u32 field_1c;                       // +0x1C: switch result (0x002c4a30)
    u32 field_20;                       // +0x20: switch result (0x002c48e8..)
    u8  encoding;                       // +0x24: 1 or 2 (0x002c49e4/0x002c49e8)
    u8  pad_25[0x03];                   // +0x25..+0x28
    f32 field_28;                       // +0x28: `vstr s0,[r4,#0x28]` (0x002c4890)
};
static_assert(offsetof(AsdFontEntry, resource) == 0x00);
static_assert(offsetof(AsdFontEntry, chunk) == 0x04);
static_assert(offsetof(AsdFontEntry, info) == 0x08);
static_assert(offsetof(AsdFontEntry, textures) == 0x0C);
static_assert(offsetof(AsdFontEntry, texture_count) == 0x10);
static_assert(offsetof(AsdFontEntry, format) == 0x14);
static_assert(offsetof(AsdFontEntry, field_18) == 0x18);
static_assert(offsetof(AsdFontEntry, encoding) == 0x24);
static_assert(offsetof(AsdFontEntry, field_28) == 0x28);
static_assert(sizeof(AsdFontEntry) == 0x2C);

/**
 * Texture descriptor created by 0x002BD940 for every glyph slot.
 * Only the words written by `AsdFont_func_002c4710` are named.
 */
struct AsdFontTexture {
    u8  pad_00[0x04];                   // +0x00..+0x04
    u32 field_04;                       // +0x04: 0xDE1 (0x002c4a48)
    u32 field_08;                       // +0x08: 0x10000 (0x002c4a48)
    u32 field_0c;                       // +0x0C: 0x2000000 (0x002c4a48)
    u32 field_10;                       // +0x10: zero (0x002c4a38)
    u32 width;                          // +0x14: header+0x10 (0x002c4a3c)
    u32 height;                         // +0x18: header+0x12 (0x002c4a3c)
    u32 field_1c;                       // +0x1C: entry+0x18 (0x002c4a3c)
    u32 field_20;                       // +0x20: entry+0x1C (0x002c4a4c)
    void* data;                         // +0x24: glyph_data + accumulated offset
    u32 field_28;                       // +0x28: header+0x04 raw word (0x002c4a54)
};
static_assert(offsetof(AsdFontTexture, field_04) == 0x04);
static_assert(offsetof(AsdFontTexture, field_10) == 0x10);
static_assert(offsetof(AsdFontTexture, width) == 0x14);
static_assert(offsetof(AsdFontTexture, field_1c) == 0x1C);
static_assert(offsetof(AsdFontTexture, data) == 0x24);
static_assert(offsetof(AsdFontTexture, field_28) == 0x28);

/** Process-wide font table (`g_AsdFontManager`, 0x00464A70). */
struct AsdFontManager {
    AsdFontEntry* entries;              // +0x00: `ldr r2,[r1]` (0x002c471c)
    u32 count;                          // +0x04: `ldr r1,[r1,#4]` (0x002c4724)
};
static_assert(offsetof(AsdFontManager, entries) == 0x00);
static_assert(offsetof(AsdFontManager, count) == 0x04);

extern AsdFontManager g_AsdFontManager; // 0x00464A70

// ---------------------------------------------------------------------------
// Ledger entry points (address / size match config/functions.csv)
// ---------------------------------------------------------------------------

void AsdFont_func_0010a588(s32 count);                                  // 0x0010a588,  152 B
int  AsdFont_func_002c4710(u32 index, const void* data);                // 0x002c4710, 1004 B
void AsdText_func_00286c5c(AsdText* text, s32 font_id, s32 mode,
                           s32 width, s32 height, const char* utf8);    // 0x00286c5c, 1596 B
void AsdText_func_00296de0(AsdText* text, s32 font_id, s32 mode,
                           s32 width, s32 height, const char* utf8);     // 0x00296de0,  280 B

} // namespace smt4::engine

namespace smt4::ui {

// ---------------------------------------------------------------------------
// message (0x002c4c2c)
// ---------------------------------------------------------------------------

/** 32-byte layout descriptor initialised by 0x002C32F8. */
struct AsdLayoutRect {
    u16 field_00;                       // +0x00: `strh r2,[r0]`
    u16 field_02;                       // +0x02: `strh r6,[r0,#2]`
    u16 field_04;                       // +0x04: `strh r5,[r0,#4]`
    u16 field_06;                       // +0x06: `strh ip,[r0,#6]`
    u16 field_08;                       // +0x08: `strh r4,[r0,#8]`
    u8  pad_0a[0x02];                   // +0x0A..+0x0C
    u32 field_0c;                       // +0x0C: `str r1,[r0,#0xc]!`
    u32 field_10;                       // +0x10: `str r3,[r0,#4]!`
    u32 field_14;                       // +0x14: `vstmia r0,{s0,s1,s2}`
    u32 field_18;                       // +0x18
    u32 field_1c;                       // +0x1C
};
static_assert(offsetof(AsdLayoutRect, field_00) == 0x00);
static_assert(offsetof(AsdLayoutRect, field_0c) == 0x0C);
static_assert(offsetof(AsdLayoutRect, field_14) == 0x14);
static_assert(sizeof(AsdLayoutRect) == 0x20);

/**
 * `message` UI object allocated by `message_func_002c4c2c` (0xA3C bytes,
 * zeroed by 0x002C4B30 before the fields below are written).
 */
struct Message {
    void* ui;                           // +0x00: `str r0,[r4]` (0x002c4d08)
    void* text;                         // +0x04: `str r0,[r4,#4]` (0x002c4c88)
    u8  field_08;                       // +0x08: `strb r5,[r4,#8]` (0x002c4cc0)
    u8  pad_09[0x29];                   // +0x09..+0x32
    u8  field_32;                       // +0x32: cleared (0x002c4cd0)
    u8  field_33;                       // +0x33: cleared (0x002c4ce0)
    u8  field_34;                       // +0x34: cleared (0x002c4cc4)
    u8  field_35;                       // +0x35: cleared (0x002c4cc8)
    u8  pad_36[0x47];                   // +0x36..+0x7D
    u8  field_7d;                       // +0x7D: cleared (0x002c4cd4)
    u8  field_7e;                       // +0x7E: cleared (0x002c4cd8)
    u8  pad_7f[0x25];                   // +0x7F..+0xA4
    AsdLayoutRect layout;               // +0xA4: 0x002C3344 / 0x002C32F8
    u8  pad_c4[0x94D];                  // +0xC4..+0xA11
    u8  field_a11;                      // +0xA11: `strb r1,[r4,#0xa11]` = 0x14
    u8  pad_a12[0x14];                  // +0xA12..+0xA26
    u8  field_a26;                      // +0xA26: `strb r6,[r4,#0xa26]` = 1
    u8  pad_a27[0x11];                  // +0xA27..+0xA38
    s32 field_a38;                      // +0xA38: `str r1,[r4,#0xa38]` = -2
};
static_assert(offsetof(Message, ui) == 0x00);
static_assert(offsetof(Message, text) == 0x04);
static_assert(offsetof(Message, field_32) == 0x32);
static_assert(offsetof(Message, field_34) == 0x34);
static_assert(offsetof(Message, field_7d) == 0x7D);
static_assert(offsetof(Message, layout) == 0xA4);
static_assert(offsetof(Message, field_a11) == 0xA11);
static_assert(offsetof(Message, field_a26) == 0xA26);
static_assert(offsetof(Message, field_a38) == 0xA38);
static_assert(sizeof(Message) == 0xA3C);

// ---------------------------------------------------------------------------
// AsdListBox (0x002272d0 / 0x0025c550 / 0x00263408)
// ---------------------------------------------------------------------------

/**
 * 32-byte item description array element consumed by
 * `AsdListBox_func_0025c550` (`add r5, fp, r8, lsl #5`).
 */
struct AsdListBoxEntry {
    const char* name;                   // +0x00: `ldr sl,[r5]` (0x0025c580)
    u8  type;                           // +0x04: `ldrb r0,[r5,#4]` (0x0025c618)
    u8  pad_05[0x03];                   // +0x05..+0x08
    const char* text;                   // +0x08: `ldr r6,[r5,#8]` (0x0025c640)
    s32 value;                          // +0x0C: `ldr r0,[r5,#0xc]` (0x0025c690)
    u32 param_a;                        // +0x10: `vldmia r0,{s16,s17}` (0x0025c6ec)
    u32 param_b;                        // +0x14
    u8  subtype;                        // +0x18: `ldrb r6,[r5,#0x18]` (0x0025c6e4)
    u8  pad_19[0x03];                   // +0x19..+0x1C
    const AsdListBoxEntry* next;        // +0x1C: `ldr r5,[r5,#0x1c]` (0x0025c778)
};
static_assert(offsetof(AsdListBoxEntry, name) == 0x00);
static_assert(offsetof(AsdListBoxEntry, type) == 0x04);
static_assert(offsetof(AsdListBoxEntry, text) == 0x08);
static_assert(offsetof(AsdListBoxEntry, value) == 0x0C);
static_assert(offsetof(AsdListBoxEntry, param_a) == 0x10);
static_assert(offsetof(AsdListBoxEntry, param_b) == 0x14);
static_assert(offsetof(AsdListBoxEntry, subtype) == 0x18);
static_assert(offsetof(AsdListBoxEntry, next) == 0x1C);
static_assert(sizeof(AsdListBoxEntry) == 0x20);

/**
 * 0x220-byte list-box row allocated by both 0x002272D0 and 0x0025C550.
 * The two 0x100-byte name buffers start at +0x06 and +0x106; the row id
 * doubles as the lookup key passed to 0x00254FF0.
 */
struct AsdListBoxItem {
    u32 id;                             // +0x00: `str r0,[r5]` (0x00227334)
    u8  type;                           // +0x04: `strb r0,[r5,#4]` (0x00227324)
    u8  subtype;                        // +0x05: case 3 store (0x0025c71c)
    char name[0x100];                   // +0x06: 0x00262B60 destination +6
    char name2[0x100];                  // +0x106: 0x0025C668 destination
    u8  pad_206[0x02];                  // +0x206..+0x208
    u32 field_208;                      // +0x208: `str r6,[r0,#0x208]!` (0x0025c6c0)
    f32 field_20c;                      // +0x20C: case 4 `vstmia r2,{s16,s17}` (0x0025c760)
    u32 field_210;                      // +0x210: cases 2/3/4
    u32 field_214;                      // +0x214: cases 2/3/4
    u8  pad_218[0x04];                  // +0x218..+0x21C
    void* link;                         // +0x21C: `strne r5,[r0,#0x21c]` (0x0025c794)
};
static_assert(offsetof(AsdListBoxItem, id) == 0x00);
static_assert(offsetof(AsdListBoxItem, type) == 0x04);
static_assert(offsetof(AsdListBoxItem, name) == 0x06);
static_assert(offsetof(AsdListBoxItem, name2) == 0x106);
static_assert(offsetof(AsdListBoxItem, field_208) == 0x208);
static_assert(offsetof(AsdListBoxItem, field_20c) == 0x20C);
static_assert(offsetof(AsdListBoxItem, field_210) == 0x210);
static_assert(offsetof(AsdListBoxItem, field_214) == 0x214);
static_assert(offsetof(AsdListBoxItem, link) == 0x21C);
static_assert(sizeof(AsdListBoxItem) == 0x220);

/**
 * Object returned by the handle resolver 0x002C0AC8.  Only the two counters
 * touched by the reconstructed AsdListBox functions are named.
 */
struct AsdListBox {
    u8  pad_00[0x28];                   // +0x00..+0x28
    u32 field_28;                       // +0x28: reloaded through `[r4,#0xc]`+0x1c
    u8  pad_2c[0x40];                   // +0x2C..+0x6C
    u32 field_6c;                       // +0x6C: `str r0,[r4,#0x6c]` (0x00227364)
    u32 item_count;                     // +0x70: incremented at 0x00227340
};
static_assert(offsetof(AsdListBox, field_28) == 0x28);
static_assert(offsetof(AsdListBox, field_6c) == 0x6C);
static_assert(offsetof(AsdListBox, item_count) == 0x70);

/**
 * UI widget created by 0x002C5978 and configured by
 * `AsdListBox_func_00263408`.  Only the words written by that function are
 * named; `+0x48..+0x54` hold the two 128.0f defaults and the scaled widget
 * size.
 */
struct AsdListBoxWidget {
    u8  pad_00[0x34];                   // +0x00..+0x34
    u32 field_34;                       // +0x34: cleared (0x00263510)
    u32 field_38;                       // +0x38: `orr r2,r2,#4` (0x002634cc)
    u8  field_3c;                       // +0x3C: `strb r5,[r4,#0x3c]` (0x002634ac)
    u8  pad_3d[0x0B];                   // +0x3D..+0x48
    f32 field_48;                       // +0x48: `vstmia r3,{s1,s2}` (0x002634d0)
    f32 field_4c;                       // +0x4C
    f32 field_50;                       // +0x50: 128.0f (0x002634b0)
    f32 field_54;                       // +0x54: 128.0f (0x002634bc)
    u32 field_58;                       // +0x58: 0x0A (0x002634d8)
    u32 field_5c;                       // +0x5C: 0x0D (0x002634d4)
    u8  pad_60[0x08];                   // +0x60..+0x68
    u32 field_68;                       // +0x68: 0x0A (0x002634e8)
};
static_assert(offsetof(AsdListBoxWidget, field_34) == 0x34);
static_assert(offsetof(AsdListBoxWidget, field_38) == 0x38);
static_assert(offsetof(AsdListBoxWidget, field_3c) == 0x3C);
static_assert(offsetof(AsdListBoxWidget, field_48) == 0x48);
static_assert(offsetof(AsdListBoxWidget, field_50) == 0x50);
static_assert(offsetof(AsdListBoxWidget, field_58) == 0x58);
static_assert(offsetof(AsdListBoxWidget, field_5c) == 0x5C);
static_assert(offsetof(AsdListBoxWidget, field_68) == 0x68);

// ---------------------------------------------------------------------------
// Ledger entry points (address / size match config/functions.csv)
// ---------------------------------------------------------------------------

void* message_func_002c4c2c();                                             // 0x002c4c2c, 508 B
u32   AsdListBox_func_002272d0(void* handle, const char* name);            // 0x002272d0, 172 B
void  AsdListBox_func_0025c550(void* handle, const AsdListBoxEntry* entries,
                               s32 count);                                 // 0x0025c550, 628 B
void* AsdListBox_func_00263408(void* handle, const char* name, s32 width,
                               s32 height, u32 flag);                      // 0x00263408, 300 B

} // namespace smt4::ui
