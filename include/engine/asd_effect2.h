#pragma once
#include <cstddef>
#include "types.h"

/**
 * Effect subsystem, part 2: particle clone/build, polygon ring/thunder/flash/
 * track geometry, and the geometry engine's vertex buffers.
 *
 * These thirteen ledger entries come from five original translation units:
 *
 *   effParticle.cpp        effParticle_func_002de41c / _002e7c30
 *   effObjectParticle.cpp  effObjectParticle_func_00313908
 *   effPolygonRing.cpp     effPolygonRing_func_0030efb0 / _0031551c / _00315700
 *   effPolygonThunder.cpp  effPolygonThunder_func_0031596c / _0032170c / _00327d90
 *   effPolygonFlash.cpp    effPolygonFlash_func_003243bc
 *   effPolygonTrack.cpp    effPolygonTrack_func_0024fab8
 *   effGeometry.cpp        effGeometry_func_002691f0
 *   effGeomEngine.cpp      effGeomEngine_func_001f68b0
 *
 * Only the fields touched by these bodies are named.  Every offset below cites
 * the instruction that proves it; unproven ranges stay `pad_NN`.
 */

namespace smt4::engine {

// ---------------------------------------------------------------------------
// effParticle.cpp
// ---------------------------------------------------------------------------

/**
 * Source object accepted by `effParticle_func_002de41c` and
 * `effObjectParticle_func_00313908`.
 *
 * `AsdRes_ResolveOffset` (0x0024C60C) reads +0x10 as a record-relative offset
 * and +0x18 as the "already absolute" flag; the second resolver
 * `AsdRes_ResolveRelative` (0x0024C5EC) reads the same pair at +0x20/+0x28.
 */
struct EffParticleSource {
    u8 pad_00[0x0C];
    u16 type;                       // +0x0C: `ldrh r5,[r7,#0xc]` (0x002de4a4)
    u8 pad_0e[0x02];
    u32 data;                       // +0x10: `ldr r0,[r0,#0x10]` (0x0024c614)
    u8 pad_14[0x08];
    u16 mode;                       // +0x1C: `ldrh r0,[r7,#0x1c]` (0x002de4ec)
    u8 pad_1e[0x02];
    u32 relative;                   // +0x20: `ldr r0,[r0,#0x20]` (0x0024c5f4)
    u32 length;                     // +0x24: `ldr r7,[r5,#0x24]` (0x003139e8)
    u32 absolute;                   // +0x28: `ldr r2,[r0,#0x28]` (0x0024c5f4)
};
static_assert(offsetof(EffParticleSource, type) == 0x0C);
static_assert(offsetof(EffParticleSource, data) == 0x10);
static_assert(offsetof(EffParticleSource, mode) == 0x1C);
static_assert(offsetof(EffParticleSource, relative) == 0x20);
static_assert(offsetof(EffParticleSource, length) == 0x24);
static_assert(offsetof(EffParticleSource, absolute) == 0x28);
static_assert(sizeof(EffParticleSource) == 0x2C);

/**
 * Resolved record behind a source object.
 *
 * +0x20/+0x24 are the clamped spawn-count pair (`ldr r0,[r5,#0x20]` /
 * `ldr r1,[r5,#0x24]`, 0x002de430/0x002de434); +0xB8 is the alternate count
 * read when +0x20 is zero (0x002de440).  +0x00 is the texture-table id used by
 * the switch cases (`ldr r0,[r5]` + `uxth`, 0x002de5f0/0x002de860).
 */
struct EffParticleResolved {
    u32 field_00;                   // +0x00: texture id, low 16 bits used
    u8 pad_04[0x1C];
    u32 count;                      // +0x20: primary spawn count
    u32 multiplier;                 // +0x24: count multiplier
    u8 pad_28[0x90];
    u32 alternate_count;            // +0xB8: used when +0x20 is zero
};
static_assert(offsetof(EffParticleResolved, field_00) == 0x00);
static_assert(offsetof(EffParticleResolved, count) == 0x20);
static_assert(offsetof(EffParticleResolved, multiplier) == 0x24);
static_assert(offsetof(EffParticleResolved, alternate_count) == 0xB8);
static_assert(sizeof(EffParticleResolved) == 0xBC);

/**
 * Live particle effect built by `effParticle_func_002de41c` (0x5C-byte
 * allocation at 0x002de474) and cloned by `effParticle_func_002e7c30`.
 *
 * The two pointer arrays hold `effParts_func_0024fe64` records and
 * `effParts_func_002a51dc` parts; their byte capacities are +0x38/+0x40.
 */
struct EffParticle {
    u32 count;                      // +0x00: `str r6,[r4]` (0x002de494)
    s32 field_04;                   // +0x04: `str r0,[r4,#4]` with r0=-1
    f32 field_08;                   // +0x08: `vstr s0,[r4,#8]` with 1.0f
    u16 type;                       // +0x0C: `strh r0,[r4,#0xc]` (0x002de8c0)
    u8 flags;                       // +0x0E: `orr r1,r0,#1` (0x002de4c8)
    u8 pad_0f;
    u8 pad_10[0x24];
    void** particles;               // +0x34: `str r0,[r4,#0x34]` (0x002de6d4)
    void* particle_alloc;           // +0x38: owned allocation, freed at 0x002de690
    void** parts;                   // +0x3C: `str r0,[r4,#0x3c]` (0x002de7ac)
    void* part_alloc;               // +0x40: owned allocation, freed at 0x002de764
    void* p2a;                      // +0x44: `str r0,[r4,#0x44]` (0x002de5d0)
    void* tlp;                      // +0x48: `str r0,[r4,#0x48]` (0x002de83c)
    void* behavior;                 // +0x4C: `str r0,[r4,#0x4c]` (0x002de4c0)
    void* geometry;                 // +0x50: set by 0x00249508
    f32 width;                      // +0x54: `vstr s0,[r4,#0x54]` (0x002de894)
    f32 height;                     // +0x58: `vstr s0,[r4,#0x58]` (0x002de898)
};
static_assert(offsetof(EffParticle, count) == 0x00);
static_assert(offsetof(EffParticle, type) == 0x0C);
static_assert(offsetof(EffParticle, particles) == 0x34);
static_assert(offsetof(EffParticle, particle_alloc) == 0x38);
static_assert(offsetof(EffParticle, parts) == 0x3C);
static_assert(offsetof(EffParticle, part_alloc) == 0x40);
static_assert(offsetof(EffParticle, p2a) == 0x44);
static_assert(offsetof(EffParticle, tlp) == 0x48);
static_assert(offsetof(EffParticle, behavior) == 0x4C);
static_assert(offsetof(EffParticle, geometry) == 0x50);
static_assert(offsetof(EffParticle, width) == 0x54);
static_assert(offsetof(EffParticle, height) == 0x58);
static_assert(sizeof(EffParticle) == 0x5C);

// ---------------------------------------------------------------------------
// effObjectParticle.cpp
// ---------------------------------------------------------------------------

/**
 * Resolved data record consumed by `effObjectParticle_func_00313908`.
 *
 * The 0x44-byte prefix is copied verbatim to object+0x10 (`AsdMem_CopyLarge`,
 * 0x00313998); +0x64/+0x68 select the count and +0xFC is the fallback count
 * (`ldreq r0,[r6,#0xfc]`, 0x0031392c).
 */
struct EffObjectParticleData {
    u8 copied[0x44];                // +0x00..+0x43: copied to object+0x10
    u8 field_44[0x20];              // +0x44: passed to 0x003137C4
    u32 count;                      // +0x64: `ldr r0,[r0,#0x64]` (0x0031391c)
    u32 multiplier;                 // +0x68: `ldr r1,[r6,#0x68]` (0x00313920)
    u8 pad_6c[0x90];
    u32 alternate_count;            // +0xFC: `ldreq r0,[r6,#0xfc]` (0x0031392c)
};
static_assert(offsetof(EffObjectParticleData, copied) == 0x00);
static_assert(offsetof(EffObjectParticleData, field_44) == 0x44);
static_assert(offsetof(EffObjectParticleData, count) == 0x64);
static_assert(offsetof(EffObjectParticleData, multiplier) == 0x68);
static_assert(offsetof(EffObjectParticleData, alternate_count) == 0xFC);
static_assert(sizeof(EffObjectParticleData) == 0x100);

/**
 * Live object created by `effObjectParticle_func_00313908` (0xA8 bytes at
 * 0x00313968).  +0x9C is the behavior built by 0x003137C4, +0xA0 its record
 * array and +0xA4 the allocation freed on the next rebuild.
 */
struct EffObjectParticle {
    u32 count;                      // +0x00: `str r7,[r4]` (0x00313984)
    s32 field_04;                   // +0x04: -1 (0x00313978)
    f32 field_08;                   // +0x08: 1.0f (0x00313988)
    u16 type;                       // +0x0C: `strh r0,[r4,#0xc]` (0x00313a80)
    u8 pad_0e[0x02];
    u8 copied[0x44];                // +0x10: `copy(object+0x10, data, 0x44)`
    void* model;                    // +0x54: `str r0,[r4,#0x54]` (0x00313a5c)
    void* copy;                     // +0x58: `str r0,[r4,#0x58]` (0x00313a3c)
    u8 pad_5c[0x40];
    void* behavior;                 // +0x9C: `str r1,[r7,#0x9c]` (0x003137fc)
    void* records;                  // +0xA0: `str r0,[r7,#0xa0]` (0x00313854)
    void* record_alloc;             // +0xA4: freed at 0x00313804
};
static_assert(offsetof(EffObjectParticle, count) == 0x00);
static_assert(offsetof(EffObjectParticle, type) == 0x0C);
static_assert(offsetof(EffObjectParticle, copied) == 0x10);
static_assert(offsetof(EffObjectParticle, model) == 0x54);
static_assert(offsetof(EffObjectParticle, copy) == 0x58);
static_assert(offsetof(EffObjectParticle, behavior) == 0x9C);
static_assert(offsetof(EffObjectParticle, records) == 0xA0);
static_assert(offsetof(EffObjectParticle, record_alloc) == 0xA4);
static_assert(sizeof(EffObjectParticle) == 0xA8);

// ---------------------------------------------------------------------------
// effPolygonRing.cpp
// ---------------------------------------------------------------------------

/**
 * Ring source object.
 *
 * `effPolygonRing_func_0030efb0` copies the first 0x5C bytes onto itself at
 * +0x5C (`add r0,r8,#0x5c`, 0x0030f020) and then passes +0x5C to
 * 0x002C7A54, so +0x5C..+0xB7 is a second, independent 0x5C-byte image.
 * The two floats at +0xC8/+0xCC scale the per-point value written after each
 * vertex record (`vldr s1,[r8,#0xcc]`, 0x0030f16c).
 */
struct EffPolygonRing {
    u8 pad_00[0x38];
    u32 count;                      // +0x38: `ldr fp,[r0,#0x38]` (0x0030efc4)
    u8 pad_3c[0x08];
    u32 color_00;                   // +0x44: `ldr r5,[r8,#0x44]` (0x0030f080)
    u32 color_04;                   // +0x48: `ldr r0,[r8,#0x48]` (0x0030f07c)
    u32 color_08;                   // +0x4C: `ldm r4,{r2,fp}` second word (0x003155bc)
    u8 pad_50[0x0C];
    u8 copy[0x5C];                  // +0x5C: self-copy destination
    u8 pad_b8[0x10];
    f32 field_c8;                   // +0xC8: `vldr s0,[r8,#0xc8]` (0x0030f184)
    f32 field_cc;                   // +0xCC: `vldr s1,[r8,#0xcc]` (0x0030f16c)
};
static_assert(offsetof(EffPolygonRing, count) == 0x38);
static_assert(offsetof(EffPolygonRing, color_00) == 0x44);
static_assert(offsetof(EffPolygonRing, color_04) == 0x48);
static_assert(offsetof(EffPolygonRing, color_08) == 0x4C);
static_assert(offsetof(EffPolygonRing, copy) == 0x5C);
static_assert(offsetof(EffPolygonRing, field_c8) == 0xC8);
static_assert(offsetof(EffPolygonRing, field_cc) == 0xCC);
static_assert(sizeof(EffPolygonRing) == 0xD0);

// ---------------------------------------------------------------------------
// effPolygonThunder.cpp
// ---------------------------------------------------------------------------

/**
 * Thunder source object.
 *
 * +0x38 is the segment count, +0x3C the ring-point count (clamped to 3), the
 * two +0x68/+0x6C floats scale the point ratio, and +0x70/+0x74/+0x78 are the
 * three ARGB colours whose high bytes are blended by the point ratio.
 */
struct EffPolygonThunder {
    u8 pad_00[0x38];
    u32 segments;                   // +0x38: `ldr r0,[r0,#0x38]` (0x00327da4)
    u32 points;                     // +0x3C: `ldr r0,[r0,#0x3c]` (0x00327df4)
    u8 pad_40[0x28];
    f32 scale_x;                    // +0x68: `vldmia r1,{s1,s2}` first (0x00327e34)
    f32 scale_y;                    // +0x6C: second word of the same `vldmia`
    u32 color_00;                   // +0x70: `ldr r2,[r0,#0x70]` (0x00327e2c)
    u32 color_04;                   // +0x74: `ldr r1,[r0,#0x74]` (0x00327e3c)
    u32 color_08;                   // +0x78: `ldr r0,[r0,#0x78]` (0x00327e40)
};
static_assert(offsetof(EffPolygonThunder, segments) == 0x38);
static_assert(offsetof(EffPolygonThunder, points) == 0x3C);
static_assert(offsetof(EffPolygonThunder, scale_x) == 0x68);
static_assert(offsetof(EffPolygonThunder, scale_y) == 0x6C);
static_assert(offsetof(EffPolygonThunder, color_00) == 0x70);
static_assert(offsetof(EffPolygonThunder, color_04) == 0x74);
static_assert(offsetof(EffPolygonThunder, color_08) == 0x78);
static_assert(sizeof(EffPolygonThunder) == 0x7C);

// ---------------------------------------------------------------------------
// effPolygonFlash.cpp
// ---------------------------------------------------------------------------

/**
 * Name table reached through flash object +0x30: word 0 is returned by
 * `effPolygonFlash_func_003243bc` and the string starts at +0xC
 * (`ldr r2,[r0,#0xc]` before the formatter, 0x003243d0).
 */
struct EffPolygonFlashNameTable {
    u32 field_00;                   // +0x00: `ldr r0,[r0]` (0x00324414)
    u8 pad_04[0x08];
    char name[0x10];                // +0x0C: `add r2,r0,#0xc` (0x003243d0)
};
static_assert(offsetof(EffPolygonFlashNameTable, field_00) == 0x00);
static_assert(offsetof(EffPolygonFlashNameTable, name) == 0x0C);

/**
 * Flash source object.  +0x30 is the name table, +0x38 the segment count
 * (`ldr r0,[r0,#0x38]` at 0x0032442c) and +0x70 the minimum point count
 * (`ldr r1,[r4,#0x70]`, 0x00324474).
 */
struct EffPolygonFlash {
    u8 pad_00[0x30];
    EffPolygonFlashNameTable* names; // +0x30: `ldr r0,[r0,#0x30]` (0x003243c4)
    u8 pad_34[0x04];
    u32 count;                      // +0x38: `ldr r0,[r0,#0x38]` (0x0032442c)
    u8 pad_3c[0x34];
    u32 field_70;                   // +0x70: `ldr r1,[r4,#0x70]` (0x00324474)
};
static_assert(offsetof(EffPolygonFlash, names) == 0x30);
static_assert(offsetof(EffPolygonFlash, count) == 0x38);
static_assert(offsetof(EffPolygonFlash, field_70) == 0x70);
static_assert(sizeof(EffPolygonFlash) == 0x74);

// ---------------------------------------------------------------------------
// effPolygonTrack.cpp
// ---------------------------------------------------------------------------

/**
 * Seven-word configuration copied to `EffPolygonTrack::data` by the 7-word
 * `ldm`/`stm` pair at 0x0024fac8/0x0024fad0.  The uploader at 0x003053C4
 * receives this object + 8 (`add r1,r7,#8`, 0x0024fcac).
 */
struct EffPolygonTrackConfig {
    u32 count;                      // +0x00: `ldr r0,[r7]` (0x0024fb08)
    u32 field_04;                   // +0x04
    u32 field_08;                   // +0x08: uploader base
    u32 field_0c;                   // +0x0C
    u32 field_10;                   // +0x10
    u32 field_14;                   // +0x14
    u32 field_18;                   // +0x18
};
static_assert(offsetof(EffPolygonTrackConfig, count) == 0x00);
static_assert(offsetof(EffPolygonTrackConfig, field_18) == 0x18);
static_assert(sizeof(EffPolygonTrackConfig) == 0x1C);

/**
 * Track object.  +0x28 holds the 0x1C+count*2 allocation created at
 * 0x0024fb18..0x0024fb50.
 */
struct EffPolygonTrack {
    u32 count;                      // +0x00: `ldr r0,[r6]` (0x0024fad4)
    u8 pad_04[0x08];
    u32 data[7];                    // +0x0C: 7-word `stm r6` target
    void* track;                    // +0x28: `ldr r4,[r6,#0x28]` (0x0024fae0)
};
static_assert(offsetof(EffPolygonTrack, count) == 0x00);
static_assert(offsetof(EffPolygonTrack, data) == 0x0C);
static_assert(offsetof(EffPolygonTrack, track) == 0x28);
static_assert(sizeof(EffPolygonTrack) == 0x2C);

/**
 * The two 0x1C+count*2 allocations made by `effPolygonTrack_func_0024fab8`.
 * +0x10/+0x14 are the two render arrays and +0x18 is the vertex cursor
 * (`add r0,r4,#0x1c` / `str r0,[r4,#0x18]`, 0x0024fb54/0x0024fb58).
 */
struct EffPolygonTrackData {
    u8 pad_00[0x10];
    void* render_0;                 // +0x10: `str r0,[r4,#0x10]` (0x0024fb78)
    void* render_1;                 // +0x14: `str r0,[r4,#0x14]` (0x0024fba0)
    void* vertices;                 // +0x18: `str r0,[r4,#0x18]` (0x0024fb58)
};
static_assert(offsetof(EffPolygonTrackData, render_0) == 0x10);
static_assert(offsetof(EffPolygonTrackData, render_1) == 0x14);
static_assert(offsetof(EffPolygonTrackData, vertices) == 0x18);

// ---------------------------------------------------------------------------
// effGeometry.cpp / effGeomEngine.cpp
// ---------------------------------------------------------------------------

/**
 * Render-data block shared by the geometry constructors.
 *
 * +0x04 is the array base used by the track colour loop
 * (`ldr r3,[r4,#0x10]` then `ldr r3,[r3,#4]`, 0x0024fbb0/0x0024fbc0);
 * +0x38 and +0x3C are the two vertex arrays used by the ring/thunder and
 * flash bodies respectively; +0x48 is the u16 index array.
 */
struct EffGeometryRender {
    u8 pad_00[0x04];
    u8* array_04;                   // +0x04: `ldr r3,[r3,#4]` (0x0024fbc0)
    u8 pad_08[0x30];
    u8* vertices_38;                // +0x38: `ldr r1,[r1,#0x38]` (0x003155ac)
    u8* vertices_3c;                // +0x3C: `ldr r0,[r0,#0x3c]` (0x003244d4)
    u8 pad_40[0x08];
    u16* indices;                   // +0x48: `ldr r8,[sl,#0x48]` (0x00247540)
};
static_assert(offsetof(EffGeometryRender, array_04) == 0x04);
static_assert(offsetof(EffGeometryRender, vertices_38) == 0x38);
static_assert(offsetof(EffGeometryRender, vertices_3c) == 0x3C);
static_assert(offsetof(EffGeometryRender, indices) == 0x48);
static_assert(sizeof(EffGeometryRender) == 0x4C);

/**
 * 0x58-byte geometry descriptor built by 0x002451C8 / 0x002474A0 and
 * 0x002691F0.
 *
 * +0x00/+0x02 are the format flag and primitive count, +0x08 the render block,
 * +0x0C the geometry engine (used by the 0x200-flag path), +0x40..+0x4C the
 * four-word override, and +0x54 the draw flags (`orr r2,r2,#0x20`).
 */
struct EffGeometry {
    u16 flags;                      // +0x00: `strh fp,[r6]` (0x0024752c)
    u16 count;                      // +0x02: `strh r8,[r6,#2]` (0x00247538)
    void* texture;                  // +0x04: `str r0,[r5,#4]` (0x00269350)
    EffGeometryRender* render;      // +0x08: `str sb,[r6,#8]` (0x00247530)
    void* engine;                   // +0x0C: engine descriptor pointer
    u8 pad_10[0x30];
    f32 field_40;                   // +0x40: override word 0
    f32 field_44;                   // +0x44: override word 1
    f32 field_48;                   // +0x48: override word 2
    f32 field_4c;                   // +0x4C: override word 3
    u8 pad_50[0x04];
    u32 field_54;                   // +0x54: `orr r1,r1,#0x20` (0x0030f074)
};
static_assert(offsetof(EffGeometry, flags) == 0x00);
static_assert(offsetof(EffGeometry, count) == 0x02);
static_assert(offsetof(EffGeometry, texture) == 0x04);
static_assert(offsetof(EffGeometry, render) == 0x08);
static_assert(offsetof(EffGeometry, engine) == 0x0C);
static_assert(offsetof(EffGeometry, field_40) == 0x40);
static_assert(offsetof(EffGeometry, field_44) == 0x44);
static_assert(offsetof(EffGeometry, field_48) == 0x48);
static_assert(offsetof(EffGeometry, field_4c) == 0x4C);
static_assert(offsetof(EffGeometry, field_54) == 0x54);
static_assert(sizeof(EffGeometry) == 0x58);

/**
 * Input record reached through geometry source +0x08.
 *
 * +0x0C and +0x14 are the two element counts passed to 0x00269614, +0x18 is
 * the copied index count and +0x48 the source index array (0x00269354..).
 */
struct EffGeometrySourceRecord {
    u32 field_00;
    u32 field_04;
    u32 field_08;
    u32 count_0c;                   // +0x0C: `ldr r7,[r0,#0xc]!` (0x002692d0)
    u32 field_10;
    u32 count_14;                   // +0x14: `ldr sb,[r0,#8]` (0x002692d4)
    u32 count_18;                   // +0x18: `ldr r0,[r1,#0x18]` (0x0026935c)
    u8 pad_1c[0x2C];
    u16* indices;                   // +0x48: `ldr ip,[r1,#0x48]` (0x002693a4)
};
static_assert(offsetof(EffGeometrySourceRecord, count_0c) == 0x0C);
static_assert(offsetof(EffGeometrySourceRecord, count_14) == 0x14);
static_assert(offsetof(EffGeometrySourceRecord, count_18) == 0x18);
static_assert(offsetof(EffGeometrySourceRecord, indices) == 0x48);
static_assert(sizeof(EffGeometrySourceRecord) == 0x4C);

/**
 * Source descriptor accepted by `effGeometry_func_002691f0`.
 *
 * +0x00 selects the two construction paths (`tst r6,#0x200`);
 * +0x04 is the inherited texture, +0x08 the element record and +0x0C the
 * pre-built engine used by the 0x200 path.
 */
struct EffGeometrySource {
    u16 flags;                      // +0x00: `ldrh r6,[r0]` (0x00269200)
    u8 pad_02[0x02];
    void* texture;                  // +0x04: `ldr r0,[r4,#4]` (0x00269348)
    EffGeometrySourceRecord* record; // +0x08: `ldr r0,[r4,#8]` (0x002692c8)
    void* engine;                   // +0x0C: `ldr r0,[r4,#0xc]` (0x00269210)
};
static_assert(offsetof(EffGeometrySource, flags) == 0x00);
static_assert(offsetof(EffGeometrySource, texture) == 0x04);
static_assert(offsetof(EffGeometrySource, record) == 0x08);
static_assert(offsetof(EffGeometrySource, engine) == 0x0C);
static_assert(sizeof(EffGeometrySource) == 0x10);

/**
 * 0xB8-byte geometry engine header built by `effGeomEngine_func_001f68b0`;
 * the vertex data follows it (`add r3,r4,#0xb8`, 0x001f6918).
 *
 * The flag bits map to the +0x1C/+0x20/+0x28/+0x2C/+0x34/+0x38 offsets in the
 * tail of the function (0x001f69f8..0x001f6a68); +0x64..+0x67 are four 0xFF
 * bytes (0x001f69c4..0x001f69d0) and +0x68 is the 16-float matrix passed to
 * Filter_Submit (0x001f69b0).
 */
struct EffGeomEngine {
    u8* data;                       // +0x00: `str r1,[r4]` = object+0xB8
    u32 count;                      // +0x04: `str r7,[r4,#4]`
    u32 stride;                     // +0x08: `str r5,[r4,#8]`
    u32 field_0c;                   // +0x0C: `str sl,[r4,#0xc]` = 1
    u8 pad_10[0x04];
    u32 flags;                      // +0x14: `str r6,[r4,#0x14]`
    void* render;                   // +0x18: `str r0,[r4,#0x18]`
    u8* field_1c;                   // +0x1C: flag bit 0 stream
    u8* field_20;                   // +0x20: flag bit 3 stream
    u8 pad_24[0x04];
    u8* field_28;                   // +0x28: flag bit 2 stream
    u8* field_2c;                   // +0x2C: flag bit 1 stream
    u8 pad_30[0x04];
    u8* field_34;                   // +0x34: flag bit 5 stream
    u8* field_38;                   // +0x38: flag bit 7 stream
    u8 pad_3c[0x04];
    u32 field_40;                   // +0x40: override from 0x004737F8
    u32 field_44;                   // +0x44
    u32 field_48;                   // +0x48
    u32 field_4c;                   // +0x4C
    u8 pad_50[0x10];
    u32 field_60;                   // +0x60: `str r8,[r0,#0x60]` = 0
    u8 field_64[0x04];              // +0x64: four 0xFF bytes
    f32 matrix[16];                 // +0x68: 0x001f6978..0x001f699c
    u32 field_a8;                   // +0xA8: `str r8,[r4,#0xa8]`
    u8 pad_ac[0x08];
    void* texture;                  // +0xB4: `str r0,[r1,#0xb4]` (0x002692b4)
    u8 vertices[1];                 // +0xB8: vertex data follows the header
};
static_assert(offsetof(EffGeomEngine, data) == 0x00);
static_assert(offsetof(EffGeomEngine, count) == 0x04);
static_assert(offsetof(EffGeomEngine, stride) == 0x08);
static_assert(offsetof(EffGeomEngine, field_0c) == 0x0C);
static_assert(offsetof(EffGeomEngine, flags) == 0x14);
static_assert(offsetof(EffGeomEngine, render) == 0x18);
static_assert(offsetof(EffGeomEngine, field_1c) == 0x1C);
static_assert(offsetof(EffGeomEngine, field_20) == 0x20);
static_assert(offsetof(EffGeomEngine, field_28) == 0x28);
static_assert(offsetof(EffGeomEngine, field_2c) == 0x2C);
static_assert(offsetof(EffGeomEngine, field_34) == 0x34);
static_assert(offsetof(EffGeomEngine, field_38) == 0x38);
static_assert(offsetof(EffGeomEngine, field_40) == 0x40);
static_assert(offsetof(EffGeomEngine, field_4c) == 0x4C);
static_assert(offsetof(EffGeomEngine, field_60) == 0x60);
static_assert(offsetof(EffGeomEngine, field_64) == 0x64);
static_assert(offsetof(EffGeomEngine, matrix) == 0x68);
static_assert(offsetof(EffGeomEngine, field_a8) == 0xA8);
static_assert(offsetof(EffGeomEngine, texture) == 0xB4);
static_assert(offsetof(EffGeomEngine, vertices) == 0xB8);

/**
 * The four-word block copied from global 0x004737F8 when source flags bit
 * 0x80000 is set (0x0026927C..0x00269294): +0x10/+0x14/+0x18 go to geometry
 * +0x40/+0x44/+0x48 and +0x1C to geometry +0x4C.
 */
struct EffGeometryOverride {
    u8 pad_00[0x10];
    f32 field_10;
    f32 field_14;
    f32 field_18;
    f32 field_1c;
};
static_assert(offsetof(EffGeometryOverride, field_10) == 0x10);
static_assert(offsetof(EffGeometryOverride, field_1c) == 0x1C);
static_assert(sizeof(EffGeometryOverride) == 0x20);

// ---------------------------------------------------------------------------
// Reconstructed functions
// ---------------------------------------------------------------------------

// effParticle.cpp
void* effParticle_func_002de41c(EffParticleSource* source);
void  effParticle_func_002e7c30(EffParticle* dest, const EffParticle* source);

// effObjectParticle.cpp
void* effObjectParticle_func_00313908(EffParticleSource* source);

// effPolygonRing.cpp
void* effPolygonRing_func_0030efb0(EffPolygonRing* object);
void* effPolygonRing_func_0031551c(EffPolygonRing* object);
void* effPolygonRing_func_00315700(EffPolygonRing* object);

// effPolygonThunder.cpp
void* effPolygonThunder_func_0031596c(EffPolygonThunder* object);
void* effPolygonThunder_func_0032170c(EffPolygonThunder* object);
void* effPolygonThunder_func_00327d90(EffPolygonThunder* object);

// effPolygonFlash.cpp
s32   effPolygonFlash_func_003243bc(EffPolygonFlash* object, char* buffer);
// 0x00324420 is the second ARM entry inside the 0x003243BC ledger row; the
// two bodies are split here so each binary address keeps one declaration.
void* effPolygonFlash_func_00324420(EffPolygonFlash* object,
                                    const void* texture);

// effPolygonTrack.cpp
void  effPolygonTrack_func_0024fab8(EffPolygonTrack* object,
                                    const EffPolygonTrackConfig* config);

// effGeometry.cpp
EffGeometry* effGeometry_func_002691f0(const EffGeometrySource* source);

// effGeomEngine.cpp
EffGeomEngine* effGeomEngine_func_001f68b0(u32 count, u32 flags, u32 mode);

} // namespace smt4::engine
