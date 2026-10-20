#pragma once
#include <cstddef>
#include "types.h"
#include "engine/asd_symbols.h"

/**
 * Atlus AsdSDK texture / texture-table / primitive plumbing.
 *
 * The ten functions reconstructed in `src/engine/asd_texture.cpp` come from
 * eight different original translation units:
 *
 *   AsdPrim         c:\SMT4\XRD686\AsdSDK\Source\Gfx\Prim\AsdPrim.cpp
 *   AsdTMSpr        c:\SMT4\XRD686\AsdSDK\Source\Gfx\AsdTexManager\AsdTMSpr.cpp
 *   AsdTexTMX       c:\SMT4\XRD686\AsdSDK\Source\Gfx\Tex\AsdTexTMX.cpp
 *   AsdTexTGA       c:\SMT4\XRD686\AsdSDK\Source\Gfx\Tex\AsdTexTGA.cpp
 *   AsdTexture      c:\SMT4\XRD686\AsdSDK\Source\Gfx\Tex\AsdTexture.cpp
 *   AsdTMTexTable   c:\SMT4\XRD686\AsdSDK\Source\Gfx\AsdTexManager\AsdTMTexTable.cpp
 *   AsdPrimRenderData c:\SMT4\XRD686\AsdSDK\Source\Gfx\Prim\AsdPrimRenderData.cpp
 *   AsdMemory       c:\SMT4\XRD686\AsdSDK\Source\Sys\Mem\AsdMemory.cpp
 *
 * Only the offsets actually touched by those ten functions are named.  Every
 * field carries the instruction that proves it; unproven ranges stay `pad_NN`.
 */

namespace smt4::engine {

// ---------------------------------------------------------------------------
// AsdPrim (0x001042c8)
// ---------------------------------------------------------------------------

/**
 * Global primitive workspace at `0x004DAEC0`.
 *
 * `AsdPrim_func_001042c8` fills the two 64 KiB buffers and then clears the
 * three words at +0x08/+0x0C/+0x10 before storing its argument at +0x14.
 */
struct AsdPrimState {
    void* buffers[2];                   // +0x00: `str r0,[r5,r4,lsl #2]` (0x00104314)
    void* field_08;                     // +0x08: `str r7,[r0,#8]` with r7=0 (0x00104324)
    void* field_0c;                     // +0x0C: `str r7,[r0,#8]` with r0=r5+4 (0x00104324)
    void* field_10;                     // +0x10: `str r7,[r5,#0x10]!` (0x0010432c)
    void* owner;                        // +0x14: `str r6,[r5,#4]` after writeback (0x00104330)
};
static_assert(offsetof(AsdPrimState, field_08) == 0x08);
static_assert(offsetof(AsdPrimState, field_0c) == 0x0C);
static_assert(offsetof(AsdPrimState, field_10) == 0x10);
static_assert(offsetof(AsdPrimState, owner) == 0x14);
static_assert(sizeof(AsdPrimState) == 0x18);

extern AsdPrimState g_AsdPrimState;     // 0x004DAEC0

// ---------------------------------------------------------------------------
// AsdTexture (0x002BD940 / 0x002BD730 / 0x0019FB58 / 0x00257E6C)
// ---------------------------------------------------------------------------

/**
 * Texture object allocated as exactly 0x48 bytes by
 * `AsdTexture_func_002bd940` and finalised by `AsdTexture_func_002bd730`.
 *
 * The TMX (0x0019FB58) and TGA (0x00257E6C) loaders only fill the metadata
 * half; both store their GPU work buffer at +0x24.  +0x2C is untouched by
 * every function reconstructed here and therefore stays padding.
 */
struct AsdTexture {
    u32 ref_count;                      // +0x00: `ldr r0,[r4]`/`str r0,[r4]` (0x002bd9d0)
    u32 format;                         // +0x04: 0xDE1 (0x002bd9c4 / 0x00257ec8)
    u32 kind;                           // +0x08: 0x10000 in 0x002bd9bc; 0x20000/0x30000 in 0x002bd7d0
    u8  pad_0c[0x04];                   // +0x0C..+0x10
    u32 field_10;                       // +0x10: `str r6,[r4,#0x10]` with r6=0 (0x00280d8c)
    u32 width;                          // +0x14: `str r1,[r4,#0x14]` (0x00257ec4)
    u32 height;                         // +0x18: `str r0,[r4,#0x18]` (0x00257ec0)
    u32 format2;                        // +0x1C: 0x6752/0x675B/0x675A (0x0019fdf0 / 0x00257fc4)
    u32 param;                          // +0x20: 0x1401 (0x0019fdf4 / 0x00257f9c)
    void* data;                         // +0x24: `str r0,[r4,#0x24]` (0x00257f40 / 0x0019fdf0)
    u32 data_size;                      // +0x28: `str r1,[r4,#0x28]` (0x00257f14)
    u8  pad_2c[0x04];                   // +0x2C..+0x30
    u32 gpu_address;                    // +0x30: `str r0,[r4,#0x30]` (0x002bd8e8)
    u32 gpu_format;                     // +0x34: `str r0,[r2]` inside 0x002A6A24 (0x002bd784)
    u32 field_38;                       // +0x38: 2 (0x002bd9c8)
    u32 field_3c;                       // +0x3C: 0 (0x002bd9c8)
    u32 field_40;                       // +0x40: 0 (0x002bd9cc)
    void* converted;                    // +0x44: `str r0,[r4,#0x44]` (0x002bd814/0x002bd844)
};
static_assert(offsetof(AsdTexture, ref_count) == 0x00);
static_assert(offsetof(AsdTexture, format) == 0x04);
static_assert(offsetof(AsdTexture, kind) == 0x08);
static_assert(offsetof(AsdTexture, field_10) == 0x10);
static_assert(offsetof(AsdTexture, width) == 0x14);
static_assert(offsetof(AsdTexture, height) == 0x18);
static_assert(offsetof(AsdTexture, format2) == 0x1C);
static_assert(offsetof(AsdTexture, param) == 0x20);
static_assert(offsetof(AsdTexture, data) == 0x24);
static_assert(offsetof(AsdTexture, data_size) == 0x28);
static_assert(offsetof(AsdTexture, gpu_address) == 0x30);
static_assert(offsetof(AsdTexture, gpu_format) == 0x34);
static_assert(offsetof(AsdTexture, field_38) == 0x38);
static_assert(offsetof(AsdTexture, field_40) == 0x40);
static_assert(offsetof(AsdTexture, converted) == 0x44);
static_assert(sizeof(AsdTexture) == 0x48);

/**
 * TMX header.  The palette starts at a fixed +0x40; its entry count is 16
 * for the 4-bit formats and 256 for the 8-bit formats, and each entry is
 * four bytes (`sb = 4` shifts of 4 and 8 in 0x0019FB58).
 */
struct AsdTMXHeader {
    u8  pad_00[0x11];                   // +0x00..+0x11
    u8  field_11;                       // +0x11: `ldrb r0,[r1,#0x11]` (0x0019fb68)
    u16 width;                          // +0x12: `ldrh r4,[r1,#0x12]` (0x0019fb6c)
    u16 height;                         // +0x14: `ldrh r6,[r1,#0x14]` (0x0019fb70)
    u8  format;                         // +0x16: `ldrb r0,[r5,#0x16]` (0x0019fbb8)
    u8  pad_17[0x29];                   // +0x17..+0x40
};
static_assert(offsetof(AsdTMXHeader, field_11) == 0x11);
static_assert(offsetof(AsdTMXHeader, width) == 0x12);
static_assert(offsetof(AsdTMXHeader, height) == 0x14);
static_assert(offsetof(AsdTMXHeader, format) == 0x16);
static_assert(sizeof(AsdTMXHeader) == 0x40);

/**
 * NW4C TGA container header.
 *
 * The 16-byte signature is checked at +0x12 (0x00257e80) and the first child
 * block offset is read from the *unaligned* +0x22 (0x00257ed0,
 * `ldr r0,[r6,#0x10]` with r6 = data + 0x12).  A u32 member would be placed
 * at +0x24 by the ABI, so the offset is assembled byte-wise in
 * `AsdTexTGA_func_00257e6c` instead.
 */
struct AsdTGAHeader {
    u8   pad_00[0x0C];                  // +0x00..+0x0C
    u16  width;                         // +0x0C: `ldrb r2,[r5,#0xc]` (0x00257ea8)
    u16  height;                        // +0x0E: `ldrb r0,[r5,#0xe]` (0x00257ea4)
    u8   pad_10[0x02];                  // +0x10..+0x12
    char signature[0x10];               // +0x12..+0x22: compared with "NW4C_Tga Ver1.0"
};
static_assert(offsetof(AsdTGAHeader, width) == 0x0C);
static_assert(offsetof(AsdTGAHeader, height) == 0x0E);
static_assert(offsetof(AsdTGAHeader, signature) == 0x12);
static_assert(sizeof(AsdTGAHeader) == 0x22);

/** Child block of a NW4C TGA container (`nw4c_txd` / `nw4c_tfm` / `nw4c_end`). */
struct AsdTGABlock {
    char tag[8];                        // +0x00: compared with 8-byte tags (0x00257eec)
    u32  size;                          // +0x08: `ldr r0,[r5,#8]` (0x00257f08)
    // Payload starts at +0x0C; its length is `size - 0x0C`.
};
static_assert(offsetof(AsdTGABlock, size) == 0x08);
static_assert(sizeof(AsdTGABlock) == 0x0C);

// ---------------------------------------------------------------------------
// AsdTMTexTable (0x002C4E28 / 0x002C5B04)
// ---------------------------------------------------------------------------

struct AsdTMTexTable;
struct AsdTMTexRef;
struct AsdTMTexGroupHeader;
struct AsdTMTexGroupRecord;

/** Two normalised directory strings owned by the texture manager. */
struct AsdTMTexPaths {
    char root[0x80];                    // +0x00: strcpy source/destination (0x002c4e6c)
    char base[0x80];                    // +0x80: `add sb,r8,#0x80` (0x002c5d00)
};
static_assert(offsetof(AsdTMTexPaths, base) == 0x80);

/** 24-byte group entry in the global array reached through `0x0044EA28`. */
struct AsdTMTexGroupEntry {
    AsdTMTexTable* table;               // +0x00: `str r6,[r7]` (0x002c5d60)
    void* group;                        // +0x04: `str r0,[sb,#4]` (0x002c4f18)
    char name[0x10];                    // +0x08: `%s` destination/source (0x002c4ec0)
};
static_assert(offsetof(AsdTMTexGroupEntry, table) == 0x00);
static_assert(offsetof(AsdTMTexGroupEntry, group) == 0x04);
static_assert(offsetof(AsdTMTexGroupEntry, name) == 0x08);
static_assert(sizeof(AsdTMTexGroupEntry) == 0x18);

/** Global texture-manager root at `0x0044EA28`. */
struct AsdTMTexTableGlobal {
    AsdTMTexGroupEntry* groups;         // +0x00: `ldr r2,[r0]` (0x002c4e50)
    AsdTMTexPaths* paths;               // +0x04: `ldr r5,[r0,#4]` (0x002c4e64)
};
static_assert(offsetof(AsdTMTexTableGlobal, paths) == 0x04);

extern AsdTMTexTableGlobal g_AsdTMTexTable;     // 0x0044EA28

/** Eight-byte .tgd group context allocated by 0x002C4E28. */
struct AsdTMTexGroup {
    AsdTMTexGroupHeader* header;        // +0x00: `str r0,[r1]` (0x002c4f50)
    AsdTMTexGroupRecord* first;         // +0x04: `streq r4,[r1,#4]` (0x002c503c)
};
static_assert(offsetof(AsdTMTexGroup, first) == 0x04);
static_assert(sizeof(AsdTMTexGroup) == 0x08);

/** 0x40-byte header copied verbatim from the start of a .tgd GroupTable. */
struct AsdTMTexGroupHeader {
    u8  pad_00[0x20];                   // +0x00..+0x20
    s32 record_count;                   // +0x20: `ldr r0,[fp,#0x20]` (0x002c4f78)
    u8  pad_24[0x1C];                   // +0x24..+0x40
};
static_assert(offsetof(AsdTMTexGroupHeader, record_count) == 0x20);
static_assert(sizeof(AsdTMTexGroupHeader) == 0x40);

/**
 * 0x14-byte .tgd group record.  The record is immediately followed by
 * `item_count` 20-byte items; `0x002C4E28` advances its cursor by
 * `0xC + item_count * 20`.
 */
struct AsdTMTexGroupRecord {
    u32 field_00;                       // +0x00: byte loaded into a word (0x002c4fa8)
    u32 item_count;                     // +0x04: `ldr r1,[r5,#4]` (0x002c4fb8)
    u8  field_08;                       // +0x08: `strb r1,[r0,#8]` (0x002c4fc8)
    u8  pad_09[0x03];                   // +0x09..+0x0C
    void* items;                        // +0x0C: `str r0,[r4,#0xc]` (0x002c5000)
    AsdTMTexGroupRecord* next;          // +0x10: `strne r4,[r7,#0x10]` (0x002c5044)
};
static_assert(offsetof(AsdTMTexGroupRecord, item_count) == 0x04);
static_assert(offsetof(AsdTMTexGroupRecord, items) == 0x0C);
static_assert(offsetof(AsdTMTexGroupRecord, next) == 0x10);
static_assert(sizeof(AsdTMTexGroupRecord) == 0x14);

/** Header of a `.ttd` texture-table file (0x002C5B04). */
struct AsdTMTexFile {
    u8   pad_00[0x04];                  // +0x00..+0x04
    char name[0x10];                    // +0x04: `%s` argument via `add r3,r4,#4` (0x002c5d48)
    u32  node_offset;                   // +0x14: `ldr ip,[r4,#0x14]` (0x002c5bd0)
    u8   pad_18[0x04];                  // +0x18..+0x1C
    u32  entry_offset;                  // +0x1C: `ldm r0,{r0,r1,r2}` with r0=file+0x1c (0x002c5bd4)
    s32  entry_count;                   // +0x20: `cmp r1,#0` (0x002c5bec)
    u32  ref_offset;                    // +0x24: second word of the 0x1c triple (0x002c5bd4)
    s32  ref_count;                     // +0x28: `ldr r2,[r4,#0x28]` (0x002c5c2c)
    u32  data_offset;                   // +0x2C: `ldr fp,[r4,#0x2c]` (0x002c5bdc)
};
static_assert(offsetof(AsdTMTexFile, name) == 0x04);
static_assert(offsetof(AsdTMTexFile, node_offset) == 0x14);
static_assert(offsetof(AsdTMTexFile, entry_offset) == 0x1C);
static_assert(offsetof(AsdTMTexFile, entry_count) == 0x20);
static_assert(offsetof(AsdTMTexFile, ref_offset) == 0x24);
static_assert(offsetof(AsdTMTexFile, ref_count) == 0x28);
static_assert(offsetof(AsdTMTexFile, data_offset) == 0x2C);

/** Opaque 0x50-byte node referenced by `AsdTMTexEntry::node_offset`. */
struct AsdTMTexNode {
    u8 bytes[0x50];                     // via `add r0,r6,r0,lsl #4` after `*5`
};
static_assert(sizeof(AsdTMTexNode) == 0x50);

/** 20-byte entry in the `.ttd` entry array. */
struct AsdTMTexEntry {
    u8  pad_00[0x0C];                   // +0x00..+0x0C
    u32 node_offset;                    // +0x0C: `ldr r0,[r2,#0xc]` (0x002c5bfc)
    u8  pad_10[0x04];                   // +0x10..+0x14
};
static_assert(offsetof(AsdTMTexEntry, node_offset) == 0x0C);
static_assert(sizeof(AsdTMTexEntry) == 0x14);

/** 16-byte `.ttd` reference rewritten in place by 0x002C5B04. */
struct AsdTMTexRef {
    u32 node_index;                     // +0x00: `ldr r2,[r0]` (0x002c5c40)
    u32 field_04;                       // +0x04
    u32 data_offset;                    // +0x08: `ldr r2,[r0,#8]` (0x002c5c54)
    u32 field_0c;                       // +0x0C
};
static_assert(offsetof(AsdTMTexRef, data_offset) == 0x08);
static_assert(sizeof(AsdTMTexRef) == 0x10);

/** 0x20-byte descriptor allocated in `AsdTMTexTable::entries`. */
struct AsdTMTexTableEntry {
    AsdTMTexTable* owner;               // +0x00: `str r6,[r0]` (0x002c5cd4)
    AsdTMTexRef* record;                // +0x04: `str r5,[r0,#4]` (0x002c5cd0)
    u8 pad_08[0x18];                    // +0x08..+0x20
};
static_assert(offsetof(AsdTMTexTableEntry, record) == 0x04);
static_assert(sizeof(AsdTMTexTableEntry) == 0x20);

/** 0x2C-byte table object allocated by 0x002C5B04. */
struct AsdTMTexTable {
    AsdTMTexTableEntry* entries;        // +0x00: `str r0,[r6]` (0x002c5cb8)
    void* file;                         // +0x04: `str r4,[r6,#4]` (0x002c5cf0)
    void* file_alt;                     // +0x08: `str r4,[r6,#8]` (0x002c5cf4)
    char path[0x20];                    // +0x0C: `sprintf(r6+0xc, "%s%s/")` (0x002c5d54)
};
static_assert(offsetof(AsdTMTexTable, file) == 0x04);
static_assert(offsetof(AsdTMTexTable, file_alt) == 0x08);
static_assert(offsetof(AsdTMTexTable, path) == 0x0C);
static_assert(sizeof(AsdTMTexTable) == 0x2C);

// ---------------------------------------------------------------------------
// AsdPrimRenderData (0x00346DB0)
// ---------------------------------------------------------------------------

/**
 * Eight-byte attribute descriptor passed to 0x0023BB2C by 0x00346DB0.
 *
 * The bytes `{0,1,0xFF,0xFF}` occupy the first four bytes of each descriptor
 * (`strb` at +0x18..+0x1B, +0x10..+0x13 and +0x08..+0x0B) and the zero word
 * is stored at +0x04 (`str [sp,#0x1c]` / `#0x14` / `#0x0c`).
 */
struct AsdPrimUploadDesc {
    u8  rgba[4];                        // +0x00: {0,1,0xFF,0xFF} (0x00346dc8..0x00346dfc)
    u32 field_04;                       // +0x04: zeroed (0x00346dc4 etc.)
};
static_assert(offsetof(AsdPrimUploadDesc, rgba) == 0x00);
static_assert(offsetof(AsdPrimUploadDesc, field_04) == 0x04);
static_assert(sizeof(AsdPrimUploadDesc) == 0x08);

/**
 * Primitive render-data workspace (`0x7E8` bytes).
 *
 * `0x00346DB0` builds up to five vertex streams plus the index buffer inside
 * one allocation and only flushes them when bit 0x100 of `flags` is set.
 */
struct AsdPrimRenderData {
    u8  pad_00[0x04];                   // +0x00..+0x04
    u32 flags;                          // +0x04: `ldr r0,[r4,#4]` (0x00346e04)
    u8  pad_08[0x04];                   // +0x08..+0x0C
    u32 vertex_count;                   // +0x0C: `ldr r2,[r4,#0xc]` (0x00346ea4)
    u8  pad_10[0x08];                   // +0x10..+0x18
    u32 index_count;                    // +0x18: `ldr r0,[r4,#0x18]` (0x00347120)
    u8  pad_1c[0x10];                   // +0x1C..+0x2C
    void* buffer;                       // +0x2C: `str r0,[r4,#0x2c]` (0x00346e48)
    void* positions;                    // +0x30: `str r1,[r4,#0x30]` (0x00346ea0)
    void* uv;                           // +0x34: `str r0,[r4,#0x34]` (0x00346ee8)
    void* colors;                       // +0x38: `str r0,[r4,#0x38]` (0x00346f80)
    void* indices;                      // +0x3C: `str r1,[r4,#0x3c]` (0x00347010)
    u8  pad_40[0x08];                   // +0x40..+0x48
    void* index_buffer;                 // +0x48: `str r0,[r4,#0x48]` (0x00347074)
    u8  command_queue[0x790];           // +0x4C..+0x7DC: base passed to 0x0023BB2C
    u32 index_address;                  // +0x7DC: `stm r2,{r0,r1}` (0x00347134)
    u32 index_address_count;            // +0x7E0: second word of the same store
    u8  index_uploaded;                 // +0x7E4: `strb r6,[r4,#0x7e4]` (0x00347138)
};
static_assert(offsetof(AsdPrimRenderData, flags) == 0x04);
static_assert(offsetof(AsdPrimRenderData, vertex_count) == 0x0C);
static_assert(offsetof(AsdPrimRenderData, index_count) == 0x18);
static_assert(offsetof(AsdPrimRenderData, buffer) == 0x2C);
static_assert(offsetof(AsdPrimRenderData, positions) == 0x30);
static_assert(offsetof(AsdPrimRenderData, uv) == 0x34);
static_assert(offsetof(AsdPrimRenderData, colors) == 0x38);
static_assert(offsetof(AsdPrimRenderData, indices) == 0x3C);
static_assert(offsetof(AsdPrimRenderData, index_buffer) == 0x48);
static_assert(offsetof(AsdPrimRenderData, command_queue) == 0x4C);
static_assert(offsetof(AsdPrimRenderData, index_address) == 0x7DC);
static_assert(offsetof(AsdPrimRenderData, index_address_count) == 0x7E0);
static_assert(offsetof(AsdPrimRenderData, index_uploaded) == 0x7E4);
static_assert(sizeof(AsdPrimRenderData) == 0x7E8);

// ---------------------------------------------------------------------------
// Ledger entry points (address / size match config/functions.csv)
// ---------------------------------------------------------------------------

void  AsdPrim_func_001042c8(void* owner);                                   // 0x001042c8, 176 B
void  AsdTexTMX_func_0019fb58(AsdTexture* texture, const AsdTMXHeader* tmx,
                              u32 unused, u32 texture_kind);                // 0x0019fb58, 756 B
void  AsdTexTGA_func_00257e6c(AsdTexture* texture, const AsdTGAHeader* tga,
                              const void* unused, u32 texture_kind);        // 0x00257e6c, 436 B
void  AsdTexture_func_002bd730(AsdTexture* texture);                        // 0x002bd730, 528 B
void* AsdTexture_func_002bd940(u32 kind);                                   // 0x002bd940, 172 B
void* AsdTMTexTable_func_002c4e28(u32 group_id);                            // 0x002c4e28, 620 B
void* AsdTMTexTable_func_002c5b04(u32 group_id, u32 flags);                 // 0x002c5b04, 652 B
void  AsdPrimRenderData_func_00346db0(AsdPrimRenderData* data);             // 0x00346db0, 992 B

} // namespace smt4::engine

namespace smt4::ui {

/**
 * Two-word header of the TMSprite object handled by
 * `AsdTMSpr_func_00144fbc`.  Only the type byte is read by this function;
 * the callees at 0x0014F3FC/0x0014F070/0x0014F30C/0x0014F1CC read the rest.
 */
struct AsdTMSpr {
    u8 type;                            // +0x00: `ldrb r0,[r0]`; high nibble 0x10/0x20/0x30
};
static_assert(offsetof(AsdTMSpr, type) == 0x00);

void* AsdTMSpr_func_00144fbc(AsdTMSpr* sprite, u32 flags,
                             u32 alignment, u32 unused);                    // 0x00144fbc, 416 B

} // namespace smt4::ui
