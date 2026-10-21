#pragma once
#include <cstddef>
#include "types.h"

/**
 * Second group of large runtime blocks recovered from the shipped 3DS image.
 *
 * ---------------------------------------------------------------------------
 * 0x00160E90 (3,776 B) -- four-plane 2:1 horizontal decimator (stride 0x400)
 * 0x00164C08 (3,776 B) -- same core, plane stride 0x100
 * 0x00168980 (3,776 B) -- same core, plane stride 0x200
 * ---------------------------------------------------------------------------
 * The three 0x0016xxxx entries share one instruction stream.  Every listing
 * difference is an immediate derived from the plane stride: the plane
 * load/store displacements (0x404/0x408/0x804/0x808/0xC04/0xC08 in
 * 0x00160E90 become 0x104/0x108/0x204/0x208/0x304/0x308 and
 * 0x204/0x208/0x404/0x408/0x604/0x608 respectively), the `pld`
 * displacement (0x420 / 0x120 / 0x220) and both row-step `add` immediates:
 * `#0x1000` at 0x001617C4 with its width==32 counterpart at 0x00161D2C,
 * `#0x400` at 0x0016553C / 0x00165AA4, `#0x800` at 0x001692B4 / 0x0016981C.
 * The row step is always four plane strides.
 *
 * The driver keeps a signed counter at `cols - 32`.  It consumes four 8-byte
 * groups per 32-byte iteration while the counter stays positive
 * (0x00160ED4..0x001615E4), then adds 0x18 and consumes one 8-byte group per
 * 8-byte iteration while it stays positive (0x001615F0..0x001617BC).  For
 * `cols` a multiple of 32 the pointer advances `cols - 8` bytes; the
 * `subne r0,r0,r2` at 0x001617D0 then places the next row `4*stride` bytes
 * after the previous row base.  `cols == 32` instead enters the three-group
 * block at 0x001617E8..0x00161D24, which has no per-group counter.
 *
 * Each group loads two consecutive 32-bit words per plane (group+4 and
 * group+8) and overwrites bytes group+6..group+9 -- bytes 2-3 of the first
 * word and bytes 0-1 of the second -- with the four filtered plane bytes:
 *
 *   plane 0 at +0x000, plane 1 at +stride, plane 2 at +2*stride,
 *   plane 3 at +3*stride.
 *
 * The pixel filter is the ARMv6 SIMD sequence at 0x00160F14..0x00161024
 * (pkhtb/pkhbt byte transpose, uhadd8/uqsub8/uadd8/usub8 edge weights and
 * the `sel` choose stages).  The two lane thresholds come from state+0x10 and
 * state+0x14 and are byte-replicated by the `orr r8,r8,r8,lsl #8` /
 * `orr sb,sb,sb,lsl #8` pair at 0x00160EC0..0x00160ECC.
 *
 * ---------------------------------------------------------------------------
 * 0x002F9F54 (3,636 B) -- ribbon cross-section builder
 * ---------------------------------------------------------------------------
 * `r0` is a spline row owner, `r1` a row index, `r2` a three-float source
 * point and `s0` a time value.  The owner holds a four-float head vector at
 * +0x00, a spline descriptor at +0x10 and a u16 sample counter array at
 * +0x18.  Two descriptors are used: +0x10 for the input vertex row and +0x14
 * for the output cross-section row.  Both cache `descriptor->source->base`
 * (`ldr r1,[r0]` / `ldr r1,[r1,#0x30]`, 0x002F9F74..0x002F9F80 and
 * 0x002FA764..0x002FA76C), a u16 point count at +0x0A and a flags word at
 * +0x58 whose bit 0 is set on entry (`orr r3,r3,#1` 0x002F9F84, 0x002FA774).
 *
 * Every sample is written as three vec3s into a 0x24-byte vertex:
 * position +0x00, tangent +0x0C, normal +0x18.  The routine first copies the
 * source row backwards in 12-byte units (0x002F9FB4..0x002F9FD4), stores the
 * supplied point at element +3 (0x002F9FD8..0x002F9FE4), then builds
 * `max(0, (count*0xAAAB)>>17 - 1)` samples.  Sample 1 is unrolled at
 * 0x002FA068..0x002FA3F0, samples 2..count-1 run the loop at
 * 0x002FA3FC..0x002FA6E4, and the tail at 0x002FA6E8..0x002FA758 replicates
 * the last vertex when the counter overshoots.
 *
 * The rotation matrix at 0x004EA81C+0x140 is produced by 0x0030F418 from the
 * angle `(v0*c0 + v1*c1 + v2*c2) * pi/2` (0x002FA104..0x002FA128); the matrix
 * is applied as a row-vector multiply (0x002FA264..0x002FA294 and
 * 0x002FA57C..0x002FA5C4).  The second half (0x002FA75C..0x002FAD70) copies
 * the first vertex and writes the eight cross-section vec3s at
 * +0x00/+0x0C/+0x18/+0x24/+0x30/+0x3C/+0x48/+0x54 of the output row, using
 * the 1.3/1.7/2.0 scales and the 1/3,2/3 blends at 0x002FA86C..0x002FAD70.
 */

namespace smt4::engine {

// ---------------------------------------------------------------------------
// 0x00160E90 / 0x00164C08 / 0x00168980 support type
// ---------------------------------------------------------------------------

// Descriptor passed in r0.  `data` is the plane base; `cols` seeds the signed
// group counter (`ldr r2,[r0,#8]` then `subs r2,r2,#0x20`, 0x00160E94 and
// 0x00160EB0); `rows` is the countdown decremented by four per row
// (`ldr r3,[r0,#0xc]`, 0x00160E98).  The two threshold words are read at
// 0x00160E9C/0x00160EA0 and their low byte is replicated across all four
// lanes.
struct PlaneFilterState {
    u32 field_00;        // +0x00 (never read by the three routines)
    u8* data;            // +0x04 (`ldr r0,[r0,#4]`, 0x00160EA4)
    u32 cols;            // +0x08 (`subs r2,r2,#0x20`, 0x00160EB0)
    u32 rows;            // +0x0C (`subs r3,r3,#4`, 0x001617CC)
    u32 threshold_a;     // +0x10 (`ldr r8,[r0,#0x10]`, 0x00160E9C)
    u32 threshold_b;     // +0x14 (`ldr sb,[r0,#0x14]`, 0x00160EA0)
};
static_assert(offsetof(PlaneFilterState, field_00) == 0x00);
static_assert(offsetof(PlaneFilterState, data) == 0x04);
static_assert(offsetof(PlaneFilterState, cols) == 0x08);
static_assert(offsetof(PlaneFilterState, rows) == 0x0C);
static_assert(offsetof(PlaneFilterState, threshold_a) == 0x10);
static_assert(offsetof(PlaneFilterState, threshold_b) == 0x14);
static_assert(sizeof(PlaneFilterState) == 0x18);

// ---------------------------------------------------------------------------
// 0x002F9F54 support types
// ---------------------------------------------------------------------------

// Object reachable through descriptor+0x00.  The point base sits at +0x30
// (`ldr r1,[r1,#0x30]`, 0x002F9F80 / 0x002FA76C).
struct SplineSource {
    u8  pad_00[0x30];    // +0x00..+0x2F
    u8* base;            // +0x30 (`ldr r1,[r1,#0x30]`)
};
static_assert(offsetof(SplineSource, base) == 0x30);

// Descriptor shared by owner+0x10 and owner+0x14 (`ldr r0,[r0,#0x10]`
// 0x002F9F70, `ldr r0,[r0,#0x14]` 0x002FA760).
struct SplineDescriptor {
    SplineSource* source;   // +0x00 (`ldr r1,[r0]`, 0x002F9F74)
    u8  pad_04[0x06];       // +0x04..+0x09
    u16 point_count;        // +0x0A (`ldrh ip,[r0,#0xa]`, 0x002F9F7C)
    u8  pad_0c[0x4C];       // +0x0C..+0x57
    u32 flags_58;           // +0x58 (`orr r3,r3,#1`, 0x002F9F84)
};
static_assert(offsetof(SplineDescriptor, source) == 0x00);
static_assert(offsetof(SplineDescriptor, point_count) == 0x0A);
static_assert(offsetof(SplineDescriptor, flags_58) == 0x58);

// Owner passed in r0.  The four-float head is copied to 0x004EA81C+0x110 at
// 0x002FA0C0; the two descriptors are read at 0x002F9F70 and 0x002FA760; the
// u16 counter array is indexed by the row argument (`add r1,r1,r0,lsl #1`,
// 0x002FA004).
struct SplineState {
    f32 vector[4];              // +0x00 (`ldm r0,{r1,r2,r3,ip}`, 0x002FA0C0)
    SplineDescriptor* input;    // +0x10 (`ldr r0,[r0,#0x10]`, 0x002F9F70)
    SplineDescriptor* output;   // +0x14 (`ldr r0,[r0,#0x14]`, 0x002FA760)
    u16* counters;              // +0x18 (`ldr r1,[r0,#0x18]`, 0x002F9FF0)
};
static_assert(offsetof(SplineState, vector) == 0x00);
static_assert(offsetof(SplineState, input) == 0x10);
static_assert(offsetof(SplineState, output) == 0x14);
static_assert(offsetof(SplineState, counters) == 0x18);
static_assert(sizeof(SplineState) == 0x1C);

// One output vertex (0x24-byte stride, `add r4,r4,#0x24` 0x002FA6E0).
struct SplineVertex {
    f32 position[3];    // +0x00 (`str r1,[r4]`, 0x002FA30C)
    f32 tangent[3];     // +0x0C (`ldr r2,[r4,#0xc]`, 0x002FA0E8)
    f32 normal[3];      // +0x18 (`str r2,[r4,#0x18]`, 0x002FA3E0)
};
static_assert(offsetof(SplineVertex, position) == 0x00);
static_assert(offsetof(SplineVertex, tangent) == 0x0C);
static_assert(offsetof(SplineVertex, normal) == 0x18);
static_assert(sizeof(SplineVertex) == 0x24);

// ---------------------------------------------------------------------------
// Reconstructed entry points
// ---------------------------------------------------------------------------

// 0x00160E90: four-plane 2:1 horizontal decimator, plane stride 0x400.
void func_00160e90(PlaneFilterState* state);

// 0x00164C08: same core as 0x00160E90 with plane stride 0x100.
void func_00164c08(PlaneFilterState* state);

// 0x00168980: same core as 0x00160E90 with plane stride 0x200.
void func_00168980(PlaneFilterState* state);

// 0x002F9F54: append one ribbon cross-section row.
void func_002f9f54(SplineState* spline, u32 row, const f32* point, f32 time);

} // namespace smt4::engine
