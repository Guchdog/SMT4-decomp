#pragma once
#include <cstddef>
#include "types.h"

/**
 * Effect part, P2A and TLP primitives from the AsdSDK effect subsystem.
 *
 * The thirteen functions reconstructed in `src/engine/asd_effect.cpp` come
 * from three original translation units (the first eleven all carry the
 * effParts.cpp source string, even the low-address instances):
 *
 *   effParts  c:\SMT4\XRD686\AsdSDK\Source\Gfx\Effect\effParts.cpp
 *   effP2A    c:\SMT4\XRD686\AsdSDK\Source\Gfx\Effect\effP2A.cpp
 *   effTLP    c:\SMT4\XRD686\AsdSDK\Source\Gfx\Effect\effTLP.cpp
 *
 * Only the fields touched by these functions are named.  Every offset and
 * size below cites the instruction that proves it; unproven ranges stay
 * `pad_NN`.  A loaded file header and a live manager share the same prefix up
 * to +0x88, but +0x88 is a *relative record offset* in a file header and the
 * tail link in a live manager, so it is modelled as a union.
 */

namespace smt4::engine {

struct EffPartsNode;

// ---------------------------------------------------------------------------
// Common prefix (0x00..0x88) shared by the manager/header and child nodes
// ---------------------------------------------------------------------------

struct EffPartsVec4 {
    f32 value[4];
};
static_assert(sizeof(EffPartsVec4) == 0x10);

/**
 * Prefix read by `effParts_func_002a51dc`, `effParts_func_002490e0` and
 * `effParts_func_001e1970`.
 *
 * `AsdDrawDesc_Init` (0x002A3FF8) zeroes 0x80 bytes of this prefix, so an
 * object allocated as 0x90/0xC0 starts with these fields cleared and then
 * receives its defaults from that call.
 */
struct EffPartsCommon {
    EffPartsVec4 field_00;          // +0x00: `ldm sl,{r0,r1,r2,r3}` (0x002a5244)
    EffPartsVec4 field_10;          // +0x10: second `ldm`/`stm` pair (0x002a5250)
    u8 pad_20[0x48];                // +0x20..+0x68: untouched here
    u32 field_68;                   // +0x68: `ldr r0,[sl,#0x68]` (0x002a5260)
    u8 pad_6c[0x08];                // +0x6C..+0x74
    f32 field_74;                   // +0x74: `ldr r0,[sl,#0x74]` (0x002a5258)
    u8 pad_78[0x08];                // +0x78..+0x80
    u32 count;                      // +0x80: `ldr r0,[sl,#0x80]` (0x002a5508)
    u32 field_84;                   // +0x84: `str r5,[r4,#0x84]` = 1 (0x0025caf8)
};
static_assert(offsetof(EffPartsCommon, field_00) == 0x00);
static_assert(offsetof(EffPartsCommon, field_10) == 0x10);
static_assert(offsetof(EffPartsCommon, field_68) == 0x68);
static_assert(offsetof(EffPartsCommon, field_74) == 0x74);
static_assert(offsetof(EffPartsCommon, count) == 0x80);
static_assert(offsetof(EffPartsCommon, field_84) == 0x84);
static_assert(sizeof(EffPartsCommon) == 0x88);

/**
 * Live manager (`EffParts_Create` argument in asd_model.cpp) or the 0x90-byte
 * header of a loaded effParts file.
 *
 * Live list: +0x88 is the tail (`ldr r0,[r4,#0x88]`, 0x002a5420) and +0x8C the
 * head (`ldr r5,[sl,#0x8c]`, 0x002a5268).  File header: +0x8C is zero, so the
 * same read of +0x88 yields the relative offset of the 0xC0-byte record array
 * (`ldr r5,[sl,#0x88]` followed by `add r5,r5,sl`, 0x002a550c/0x002a5518).
 */
struct EffPartsSource : EffPartsCommon {
    union {
        EffPartsNode* last;         // +0x88 live manager: tail link
        u32 record_offset;          // +0x88 file header: relative array offset
    } children;
    EffPartsNode* first;            // +0x8C live manager: head link
};
static_assert(offsetof(EffPartsSource, children) == 0x88);
static_assert(offsetof(EffPartsSource, first) == 0x8C);
static_assert(sizeof(EffPartsSource) == 0x90);

// ---------------------------------------------------------------------------
// Per-particle record (0x2C bytes)
// ---------------------------------------------------------------------------

/**
 * Owner record created by `effParts_func_00192168` / `effParts_func_0024fda4`
 * / `effParts_func_0024fe64` (alloc size 0x2C at 0x0019218C, 0x0024FDCC and
 * 0x0024FE8C) and consumed by the dispatch table at 0x00464110.
 *
 * The two variable buffers mirror `effParts_func_0024972c` (+0x0C/+0x10/
 * +0x14/+0x18) and `effParts_func_0025cc14` (+0x1C/+0x20/+0x24/+0x28).  In a
 * record that comes straight from a file, `alloc_*` is zero and `data_*` holds
 * a relative offset from the record base; after `SetData`/`SetValue` both
 * point at the allocated copy (0x0028C9B0..0x0028CA14).
 */
struct EffPartsParticle {
    u32 field_00;                   // +0x00: 0xDC (`str r2,[r0]`, 0x0024FE10) or `[src]`
    u16 type;                       // +0x04: `ldrh r6,[r0,#4]` (0x0024FDAC)
    u8 pad_06[0x02];
    void* instance;                 // +0x08: `str r0,[r4,#8]` (0x0024FE4C)
    u16 field_0c;                   // +0x0C: `strh r1,[r0,#0xc]` (0x0024FE20)
    u8 pad_0e[0x02];
    u32 data_0;                     // +0x10: `str r0,[r4,#0x10]` (0x0024979C..0x002497AC)
    u32 size_0;                     // +0x14: `stm r4,{r0,r5}` second word (0x002497AC)
    void* alloc_0;                  // +0x18: `str r0,[r4,#0x18]` (0x002497A0)
    u16 field_1c;                   // +0x1C: `strh r6,[r4,#0x1c]` (0x0025CC84)
    u8 pad_1e[0x02];
    u32 data_1;                     // +0x20: `stm r4,{r0,r5}` first word (0x0025CC94)
    u32 size_1;                     // +0x24: second word (0x0025CC94)
    void* alloc_1;                  // +0x28: `str r0,[r4,#0x28]` (0x0025CC88)
};
static_assert(offsetof(EffPartsParticle, field_00) == 0x00);
static_assert(offsetof(EffPartsParticle, type) == 0x04);
static_assert(offsetof(EffPartsParticle, instance) == 0x08);
static_assert(offsetof(EffPartsParticle, field_0c) == 0x0C);
static_assert(offsetof(EffPartsParticle, data_0) == 0x10);
static_assert(offsetof(EffPartsParticle, size_0) == 0x14);
static_assert(offsetof(EffPartsParticle, alloc_0) == 0x18);
static_assert(offsetof(EffPartsParticle, field_1c) == 0x1C);
static_assert(offsetof(EffPartsParticle, data_1) == 0x20);
static_assert(offsetof(EffPartsParticle, size_1) == 0x24);
static_assert(offsetof(EffPartsParticle, alloc_1) == 0x28);
static_assert(sizeof(EffPartsParticle) == 0x2C);

// ---------------------------------------------------------------------------
// Child node (0xC0 bytes)
// ---------------------------------------------------------------------------

/**
 * One effect child, allocated as 0xC0 bytes by `effParts_func_0025caa8`
 * (`mov r3,#0xc0`, 0x0025cac8).
 *
 * The first 0x90 bytes are copied verbatim from the source node
 * (`AsdMem_CopyLarge(child, node, 0x90)`, 0x002a540c), which is why +0x88 has
 * its own byte triplet format here rather than the manager's tail pointer.
 */
union EffPartsTarget {
    EffPartsParticle* particle;     // live object: `str r7,[r6,#0x90]` (0x002a53fc)
    u32 link;                       // file record: index when flags&1, else relative offset
};

struct EffPartsNode : EffPartsCommon {
    u8 field_88;                    // +0x88: `strb r0,[r4,#0x88]` with r0=8 (0x0025cb00)
    u8 field_89;                    // +0x89: `strb r0,[r4,#0x89]` with r0=0 (0x0025cb04)
    u8 field_8a;                    // +0x8A: `strb r0,[r4,#0x8a]` with r0=0 (0x0025cb08)
    u8 pad_8b;
    EffPartsNode* first;            // +0x8C: `ldr r4,[r0,#0x8c]` child list (0x002a39b4)
    EffPartsTarget target;          // +0x90: `ldr r1,[r5,#0x90]` / `ldr r8,[r0,#0x90]`
    u32 field_94;                   // +0x94: `ldr r0,[r5,#0x94]` (0x002a5738)
    u32 flags;                      // +0x98: `ldr r0,[r5,#0x98]` / `tst r0,#1` (0x002a52d8)
    char name[0x10];                // +0x9C: `AsdString_Strcpy(r6+0x9c, r5+0x9c)` (0x002a5418)
    EffPartsNode* next;             // +0xAC: `ldr r5,[r5,#0xac]` (0x002a544c)
    EffPartsNode* prev;             // +0xB0: `strne r0,[r6,#0xb0]` (0x002a5430)
    u8 pad_b4[0x0C];                // +0xB4..+0xC0: untouched by these functions
};
static_assert(offsetof(EffPartsNode, field_88) == 0x88);
static_assert(offsetof(EffPartsNode, field_89) == 0x89);
static_assert(offsetof(EffPartsNode, field_8a) == 0x8A);
static_assert(offsetof(EffPartsNode, first) == 0x8C);
static_assert(offsetof(EffPartsNode, target) == 0x90);
static_assert(offsetof(EffPartsNode, field_94) == 0x94);
static_assert(offsetof(EffPartsNode, flags) == 0x98);
static_assert(offsetof(EffPartsNode, name) == 0x9C);
static_assert(offsetof(EffPartsNode, next) == 0xAC);
static_assert(offsetof(EffPartsNode, prev) == 0xB0);
static_assert(sizeof(EffPartsNode) == 0xC0);

// ---------------------------------------------------------------------------
// Type dispatch table (0x00464110)
// ---------------------------------------------------------------------------

/**
 * One 0x44-byte entry of the global effect-type table at 0x00464110.
 *
 * Stride proof: `add r2,r0,r0,lsl #4` (index*17) followed by `lsl #2`
 * (0x002a53e4/0x002a53ec, 0x0024fe34/0x0024fe38) = 68 bytes.  The two
 * constructors below are the only members reached from this TU; the drawing
 * hooks at +0x20/+0x24/+0x28/+0x2C/+0x30 are reached by 0x002A37DC /
 * 0x002A399C / 0x002A3BF8 / 0x002A3D50.
 */
struct EffPartsTypeEntry {
    void* (*create_record)(void* particle);         // +0x00: `ldr r1,[r0,r1,lsl #2]` (0x002a58c0)
    u8 pad_04[0x10];
    void* (*create_instance)(void* instance);       // +0x14: `ldr r1,[r1,#0x14]` (0x002a53f0)
    u8 pad_18[0x2C];
};
static_assert(offsetof(EffPartsTypeEntry, create_record) == 0x00);
static_assert(offsetof(EffPartsTypeEntry, create_instance) == 0x14);
static_assert(sizeof(EffPartsTypeEntry) == 0x44);

extern EffPartsTypeEntry g_EffPartsTypeTable[];     // 0x00464110

// ---------------------------------------------------------------------------
// effP2A.cpp objects
// ---------------------------------------------------------------------------

/**
 * One 0x14-byte animation entry inside the copied P2A header.
 *
 * The table base is header+8 (`object->entries` = object+0x24, i.e. the copy's
 * +8, 0x002493A0) and the stride is 0x14 (`add r1,r0,r0,lsl #2` then
 * `lsl #2`, 0x00249438/0x0024943C).
 */
struct EffP2AEntry {
    u32 field_00;                   // +0x00: read by 0x001D21A0
    u32 field_04;                   // +0x04: read by 0x001D21A0
    u32 field_08;                   // +0x08: `ldr r1,[r1,#8]`, tested for 0x40/0x80
    u32 field_0c;                   // +0x0C: `ldrne r1,[r1,#0xc]` (0x00249448)
    u32 field_10;                   // +0x10: `ldr r4,[r1,#0x10]`, tested for 0x10000000
};
static_assert(offsetof(EffP2AEntry, field_00) == 0x00);
static_assert(offsetof(EffP2AEntry, field_04) == 0x04);
static_assert(offsetof(EffP2AEntry, field_08) == 0x08);
static_assert(offsetof(EffP2AEntry, field_0c) == 0x0C);
static_assert(offsetof(EffP2AEntry, field_10) == 0x10);
static_assert(sizeof(EffP2AEntry) == 0x14);

/**
 * P2A object created by `effP2A_func_00249324`.
 *
 * Allocation is `header_size + 0x1C + texture_count*4`
 * (0x00249348..0x00249358).  The 0x1C-byte prefix is followed by the copied
 * header; `header` and `entries` point into that copy and `textures` sits 8
 * bytes past it (`add r0,r0,#8`, 0x002493BC).
 */
struct EffP2AObject {
    void* header;                   // +0x00: `strd r0,r1,[r5]` first (0x002493A8)
    void* entries;                  // +0x04: second (0x002493A8)
    u32 mode;                       // +0x08: `str sl,[r5,#8]` initial 1 (0x00249418)
    u32 texture_count;              // +0x0C: `str r8,[r5,#0xc]` (0x002493A4)
    u32 field_10;                   // +0x10: `str sl,[r5,#0x10]` = 1 (0x00249414)
    void** textures;                // +0x14: `str r0,[r5,#0x14]` (0x002493C0)
    void* self;                     // +0x18: `str r5,[r5,#0x18]` (0x0024938C)
};
static_assert(offsetof(EffP2AObject, header) == 0x00);
static_assert(offsetof(EffP2AObject, entries) == 0x04);
static_assert(offsetof(EffP2AObject, mode) == 0x08);
static_assert(offsetof(EffP2AObject, texture_count) == 0x0C);
static_assert(offsetof(EffP2AObject, field_10) == 0x10);
static_assert(offsetof(EffP2AObject, textures) == 0x14);
static_assert(offsetof(EffP2AObject, self) == 0x18);
static_assert(sizeof(EffP2AObject) == 0x1C);

/**
 * Animation wrapper returned by `effP2A_func_00249324`.
 *
 * Allocation is `0x18 + mode*0x14` (`mov r0,#0x18`, `add r4,r0,r1,lsl #2`,
 * 0x00249464/0x0024946C), so +0x18 is the first 0x14-byte entry.
 */
struct EffP2AAnim {
    EffP2AObject* object;           // +0x00: `str r5,[r0]` (0x002494A8)
    u8 pad_04[0x0C];                // +0x04..+0x10: filled by 0x001D21A0
    u8* entries;                    // +0x10: `str r1,[r0,#0x10]` with r1=r0+0x18 (0x0024949C)
    u16 count;                      // +0x14: `strh sl,[r4,#0x14]` = 1 (0x002494B0)
    u8 pad_16[0x02];
};
static_assert(offsetof(EffP2AAnim, object) == 0x00);
static_assert(offsetof(EffP2AAnim, entries) == 0x10);
static_assert(offsetof(EffP2AAnim, count) == 0x14);
static_assert(sizeof(EffP2AAnim) == 0x18);

// ---------------------------------------------------------------------------
// effTLP.cpp objects
// ---------------------------------------------------------------------------

/**
 * One 0x10-byte TLP vertex record.
 *
 * `object->entries` is `r6+0x28` and the texture table is
 * `r6+0x28+count*16` (`add r3,r1,r8,lsl #4`, 0x002495F0), proving a 16-byte
 * stride.  `field_00` is the value accumulated at 0x002496A4..0x002496D4 and
 * `field_04` is the texture-block step added by the pre-indexed load at
 * 0x0024966C.
 */
struct EffTLPEntry {
    u32 field_00;                   // +0x00: `ldr r0,[r1,#0x10]!` (0x002496A4)
    u32 field_04;                   // +0x04: `ldr r0,[r5,#4]!` (0x0024966C)
    u32 field_08;                   // +0x08: copied verbatim
    u32 field_0c;                   // +0x0C: copied verbatim
};
static_assert(offsetof(EffTLPEntry, field_00) == 0x00);
static_assert(offsetof(EffTLPEntry, field_04) == 0x04);
static_assert(offsetof(EffTLPEntry, field_08) == 0x08);
static_assert(offsetof(EffTLPEntry, field_0c) == 0x0C);
static_assert(sizeof(EffTLPEntry) == 0x10);

/**
 * TLP object created by `effTLP_func_00249588`.
 *
 * Allocation is `0x28 + count*20` (`lsl r0,r8,#4`, `add r0,r0,r8,lsl #2`,
 * `add r4,r0,#0x28`, 0x0024959C..0x002495A4).
 */
struct EffTLPObject {
    u32 field_00;                   // +0x00: `ldr r0,[sb]` / `str r0,[r6]` (0x002495FC/0x00249608)
    u32 count;                      // +0x04: `ldr r8,[r0,#4]` (0x00249598)
    u32 field_08;                   // +0x08: `ldr r0,[sb,#8]` (0x00249614)
    u32 field_0c;                   // +0x0C: `ldr r0,[sb,#0xc]` (0x0024961C)
    EffTLPEntry* entries;           // +0x10: `stm r0,{r1,r3}` first (0x002495F4)
    void** textures;                // +0x14: second (0x002495F4)
    u32 total;                      // +0x18: `str r0,[r6,#0x18]` (0x002496E0)
    u32 generation;                 // +0x1C: `str r0,[r6,#0x1c]` old+1 (0x002496E8)
    s32 field_20;                   // +0x20: `mvn r2,#0` (0x002495DC)
    void* self;                     // +0x24: `stm r7,{r0,r2,r6}` third (0x002495E4)
};
static_assert(offsetof(EffTLPObject, field_00) == 0x00);
static_assert(offsetof(EffTLPObject, count) == 0x04);
static_assert(offsetof(EffTLPObject, field_08) == 0x08);
static_assert(offsetof(EffTLPObject, field_0c) == 0x0C);
static_assert(offsetof(EffTLPObject, entries) == 0x10);
static_assert(offsetof(EffTLPObject, textures) == 0x14);
static_assert(offsetof(EffTLPObject, total) == 0x18);
static_assert(offsetof(EffTLPObject, generation) == 0x1C);
static_assert(offsetof(EffTLPObject, field_20) == 0x20);
static_assert(offsetof(EffTLPObject, self) == 0x24);
static_assert(sizeof(EffTLPObject) == 0x28);

// ---------------------------------------------------------------------------
// Reconstructed functions
// ---------------------------------------------------------------------------

// effParts.cpp
//
// The five routines below are also called from AsdModel / AsdFrame through the
// EffParts_* / AsdPart_* spelling.  Those spellings are inline adapters over
// the canonical ledger entry points so that each address still has exactly one
// externally visible declaration.
EffPartsSource*   effParts_func_002a51dc(EffPartsSource* source);
EffPartsSource*   effParts_func_002490e0(EffPartsSource* source);
void              effParts_func_0024972c(EffPartsParticle* part, const void* data,
                                         s32 size, u16 key);
EffPartsParticle* effParts_func_0024fda4(EffPartsParticle* source);
EffPartsParticle* effParts_func_0024fe64(EffPartsParticle* source);
EffPartsNode*     effParts_func_0025caa8();
void              effParts_func_0025cc14(EffPartsParticle* part, const void* data,
                                         s32 size, u16 key);
EffPartsParticle* effParts_func_0028c920(EffPartsParticle* source);
EffPartsParticle* effParts_func_00192168(u32 id);
EffPartsSource*   effParts_func_001d2460();
EffPartsSource*   effParts_func_001e1970(const char* path);

// effP2A.cpp
EffP2AAnim*       effP2A_func_00249324(const void* file);

// effTLP.cpp
EffTLPObject*     effTLP_func_00249588(const void* resource);

// ---------------------------------------------------------------------------
// Call-site adapters (one external symbol per address)
// ---------------------------------------------------------------------------

// 0x002A51DC: open a part container from a loaded effParts file.
static inline void* EffParts_Create(const void* entry)
{
    return effParts_func_002a51dc(
        reinterpret_cast<EffPartsSource*>(const_cast<void*>(entry)));
}

// 0x0024FE64: wrap a live particle element as a part.
static inline void* AsdPart_Wrap(void* element)
{
    return effParts_func_0024fe64(
        static_cast<EffPartsParticle*>(element));
}

// 0x001D2460: create the parts manager.
static inline void* AsdPartsManager_Create()
{
    return effParts_func_001d2460();
}

// 0x00192168: create one owner record from a type id.
static inline void* EffParts_CreateById(u32 id)
{
    return effParts_func_00192168(id);
}

// 0x0024972C: install the primary variable-size buffer.
static inline void EffParts_SetData(void* part, const void* data, u32 size, u32 key)
{
    effParts_func_0024972c(static_cast<EffPartsParticle*>(part), data,
                           static_cast<s32>(size), static_cast<u16>(key));
}

// 0x0025CC14: install the secondary variable-size buffer.
static inline void EffParts_SetValue(void* part, const void* data, u32 size, u32 key)
{
    effParts_func_0025cc14(static_cast<EffPartsParticle*>(part), data,
                           static_cast<s32>(size), static_cast<u16>(key));
}

} // namespace smt4::engine
