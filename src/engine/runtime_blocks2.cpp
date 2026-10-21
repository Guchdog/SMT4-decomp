#include "engine/runtime_blocks2.h"

#include <cmath>
#include <cstring>

#include "engine/asd_runtime.h"   // g_TrailScratchA/B (0x00472530/0x00472550)
#include "ui/ui_runtime.h"        // g_UiPartRenderState (0x004EA81C)

extern "C" {
    // 0x0030F418: builds the 3x4 rotation matrix at 0x004EA81C+0x140 from the
    // angle in s0 and the axis at +0x100..+0x10C.
    f32 ui_func_0030f418(f32 angle);
}

namespace smt4::engine {
namespace {

// ---------------------------------------------------------------------------
// ARMv6 SIMD byte helpers (SWAR).  Each helper mirrors one instruction family
// used by the 0x00160E90/0x00164C08/0x00168980 pixel filter.
// ---------------------------------------------------------------------------

inline u32 Load32(const u8* p) {
    u32 value = 0;
    std::memcpy(&value, p, sizeof(value));
    return value;
}

// Per-lane byte extraction used by `uxtb16 rX, rY` (0x00160F14) and
// `uxtb16 rX, rY, ror #8` (0x00160F20).
inline u32 Uxtb16(u32 value) {
    return value & 0x00FF00FFu;
}

inline u32 Ror8(u32 value) {
    return (value >> 8) | (value << 24);
}

// `pkhbt Rd,Rn,Rm,lsl #16`: bottom half of Rn, top half of Rm.
inline u32 Pkhbt(u32 bottom, u32 top) {
    return (bottom & 0xFFFFu) | ((top & 0xFFFFu) << 16);
}

// `pkhtb Rd,Rn,Rm,asr #16`: top half of Rn, top half of Rm moved down.
inline u32 Pkhtb(u32 top, u32 shift_source) {
    return (top & 0xFFFF0000u) | (shift_source >> 16);
}

// `uhadd8`: per-byte (a + b) >> 1.
inline u32 Uhadd8(u32 a, u32 b) {
    u32 result = 0;
    for (u32 lane = 0; lane < 4; ++lane) {
        const u32 av = (a >> (lane * 8)) & 0xFFu;
        const u32 bv = (b >> (lane * 8)) & 0xFFu;
        result |= ((av + bv) >> 1) << (lane * 8);
    }
    return result;
}

// `uqsub8`: per-byte max(a - b, 0).
inline u32 Uqsub8(u32 a, u32 b) {
    u32 result = 0;
    for (u32 lane = 0; lane < 4; ++lane) {
        const s32 av = static_cast<s32>((a >> (lane * 8)) & 0xFFu);
        const s32 bv = static_cast<s32>((b >> (lane * 8)) & 0xFFu);
        const u32 diff = static_cast<u32>(av > bv ? av - bv : 0);
        result |= diff << (lane * 8);
    }
    return result;
}

// `uqadd8`: per-byte min(a + b, 255).
inline u32 Uqadd8(u32 a, u32 b) {
    u32 result = 0;
    for (u32 lane = 0; lane < 4; ++lane) {
        const u32 av = (a >> (lane * 8)) & 0xFFu;
        const u32 bv = (b >> (lane * 8)) & 0xFFu;
        const u32 sum = av + bv;
        result |= (sum > 255u ? 255u : sum) << (lane * 8);
    }
    return result;
}

// `uadd8`: per-byte (a + b) & 0xFF.
inline u32 Uadd8(u32 a, u32 b) {
    u32 result = 0;
    for (u32 lane = 0; lane < 4; ++lane) {
        const u32 av = (a >> (lane * 8)) & 0xFFu;
        const u32 bv = (b >> (lane * 8)) & 0xFFu;
        result |= ((av + bv) & 0xFFu) << (lane * 8);
    }
    return result;
}

// `usub8` followed by `sel`: GE is set per lane when a >= b, so the mask has
// 0xFF in every lane whose subtraction did not borrow.
inline u32 GeMask8(u32 a, u32 b) {
    u32 result = 0;
    for (u32 lane = 0; lane < 4; ++lane) {
        const u32 av = (a >> (lane * 8)) & 0xFFu;
        const u32 bv = (b >> (lane * 8)) & 0xFFu;
        if (av >= bv) {
            result |= 0xFFu << (lane * 8);
        }
    }
    return result;
}

// `sel Rd,Rn,Rm`: pick Rn where GE is set, Rm otherwise.
inline u32 Sel(u32 mask, u32 when_ge, u32 when_lt) {
    return (when_ge & mask) | (when_lt & ~mask);
}

// The two `orr rX,rX,rX,lsl #8` / `#16` pairs at 0x00160EC0..0x00160ECC.
inline u32 ReplicateByte(u32 value) {
    u32 spread = value | (value << 8);
    return spread | (spread << 16);
}

// One 8-byte group of the four-plane filter.  The listing inline-expands this
// sequence at 0x00160ED4..0x001615E4 (four groups), 0x001615F0..0x001617BC
// (tail groups), 0x001617E8..0x00161D24 (width == 32 path) and repeats it for
// every row.  `base` points at the first byte of the 0x8-byte group; the
// second word of the group receives the four filtered output bytes.
void PlaneFilterGroup(u8* base, u32 stride, u32 threshold_a, u32 threshold_b) {
    // 0x00160ED4..0x00160EF0: four planes, two words each.
    u32 r6 = Load32(base + stride + 0x04);
    u32 r5 = Load32(base + stride + 0x08);
    u32 r3 = Load32(base + 3 * stride + 0x04);
    u32 fp = Load32(base + 3 * stride + 0x08);
    u32 r7 = Load32(base + 0x04);
    u32 r4 = Load32(base + 0x08);
    u32 r2 = Load32(base + 2 * stride + 0x04);
    u32 r1 = Load32(base + 2 * stride + 0x08);

    // 0x00160EF4..0x00160F10: interleave the two words of each plane pair.
    u32 sl = Pkhbt(r6, r3);
    r3 = Pkhtb(r3, r6);
    r6 = Pkhbt(r7, r2);
    r2 = Pkhtb(r2, r7);
    r7 = Pkhtb(fp, r5);
    r5 = Pkhbt(r5, fp);
    fp = Pkhtb(r1, r4);
    r4 = Pkhbt(r4, r1);

    // 0x00160F14..0x00160F58: byte transpose into four 4-byte lanes.
    r1 = Uxtb16(r3);
    u32 lr = Uxtb16(r2);
    r1 = lr | (r1 << 8);
    r3 = Uxtb16(Ror8(r3));
    r2 = Uxtb16(Ror8(r2));
    r2 = r2 | (r3 << 8);
    sl = Uxtb16(Ror8(sl));
    r6 = Uxtb16(Ror8(r6));
    r6 = r6 | (sl << 8);
    r3 = Uxtb16(r5);
    sl = Uxtb16(r4);
    r3 = sl | (r3 << 8);
    r5 = Uxtb16(Ror8(r5));
    r4 = Uxtb16(Ror8(r4));
    r4 = r4 | (r5 << 8);
    r7 = Uxtb16(r7);
    fp = Uxtb16(fp);
    r7 = fp | (r7 << 8);

    // 0x00160F5C..0x00160F7C: first edge weight and choose.
    u32 ip = Uhadd8(r2, r3);
    sl = Uqsub8(r6, r2);
    fp = Uqsub8(r2, r6);
    r6 = Uhadd8(ip, r6);
    sl = Uadd8(sl, fp);
    u32 mask = GeMask8(sl, threshold_b);
    r6 = Sel(mask, r1, r6);

    // 0x00160F78..0x00160FBC.
    r5 = Uqsub8(r7, r3);
    fp = Uqsub8(r3, r7);
    lr = 0x01010101u;
    sl = ~r4;
    sl = Uhadd8(sl, r1);
    r7 = Uhadd8(ip, r7);
    sl = Uhadd8(sl, lr);
    r5 = Uadd8(r5, fp);
    sl = Uhadd8(sl, lr);
    lr = 0x20202020u;
    mask = GeMask8(r5, threshold_b);
    r7 = Sel(mask, r4, r7);
    fp = Uqsub8(sl, lr);
    sl = Uqsub8(lr, sl);
    r5 = Uqadd8(ip, fp);
    ip = Uqsub8(ip, fp);
    r5 = Uqsub8(r5, sl);
    ip = Uqadd8(ip, sl);

    // 0x00160FC0..0x00161000.
    sl = Uqsub8(r1, r2);
    fp = Uqsub8(r2, r1);
    lr = Uqsub8(r3, r4);
    sl = Uadd8(sl, fp);
    mask = GeMask8(sl, threshold_b);
    r5 = Sel(mask, r2, r5);
    ip = Sel(mask, r3, ip);
    r6 = Sel(mask, r1, r6);
    r7 = Sel(mask, r4, r7);

    // 0x00160FE4..0x00161000.
    fp = Uqsub8(r4, r3);
    sl = Uqsub8(r2, r3);
    lr = Uadd8(lr, fp);
    mask = GeMask8(lr, threshold_b);
    r5 = Sel(mask, r2, r5);
    ip = Sel(mask, r3, ip);
    r6 = Sel(mask, r1, r6);
    r7 = Sel(mask, r4, r7);

    // 0x00161004..0x00161020: final choose against the second threshold.
    fp = Uqsub8(r3, r2);
    sl = Uadd8(sl, fp);
    mask = GeMask8(sl, threshold_a);
    r5 = Sel(mask, r2, r5);
    ip = Sel(mask, r3, ip);
    r6 = Sel(mask, r1, r6);
    r7 = Sel(mask, r4, r7);

    // 0x00161024..0x00161090 (and the equivalent stores in every unroll):
    // plane p receives one byte from each result register.
    u32 lanes[4] = {r6, r5, ip, r7};
    for (u32 plane = 0; plane < 4; ++plane) {
        const u32 plane_base = plane * stride;
        for (u32 lane = 0; lane < 4; ++lane) {
            base[plane_base + 0x06 + lane] =
                static_cast<u8>((lanes[lane] >> (8 * plane)) & 0xFFu);
        }
    }
}

} // namespace

// ---------------------------------------------------------------------------
// 0x00160E90 -- four-plane 2:1 horizontal decimator (plane stride 0x400)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00160e90, 3776)
void func_00160e90(PlaneFilterState* state) {
    constexpr u32 kPlaneStride = 0x400;   // loads at +0x404/+0x804/+0xC04
    u8* base = state->data;               // 0x00160EA4
    const u32 cols = state->cols;         // r2, 0x00160E94
    u32 rows = state->rows;               // r3, 0x00160E98
    const u32 threshold_a = ReplicateByte(state->threshold_a); // r8
    const u32 threshold_b = ReplicateByte(state->threshold_b); // sb
    u32 counter = cols - 0x20;            // `subs r2,r2,#0x20`, 0x00160EB0

    if (cols == 0x20) {                   // `beq 0x1617E8`, 0x00160ED0
        for (;;) {
            // 0x001617E8..0x00161D24: three unrolled groups, no counter.
            PlaneFilterGroup(base + 0x00, kPlaneStride, threshold_a, threshold_b);
            PlaneFilterGroup(base + 0x08, kPlaneStride, threshold_a, threshold_b);
            PlaneFilterGroup(base + 0x10, kPlaneStride, threshold_a, threshold_b);
            // 0x00161D2C..0x00161D3C
            base += 4 * kPlaneStride;
            rows -= 4;
            if (rows == 0) {
                return;
            }
            counter = cols - 0x20;        // `strne r2,[sp]`, 0x00161D34
        }
    }

    for (;;) {
        // 0x00160ED4..0x001615E4: four 8-byte groups per 32-byte chunk.
        do {
            PlaneFilterGroup(base + 0x00, kPlaneStride, threshold_a, threshold_b);
            PlaneFilterGroup(base + 0x08, kPlaneStride, threshold_a, threshold_b);
            PlaneFilterGroup(base + 0x10, kPlaneStride, threshold_a, threshold_b);
            PlaneFilterGroup(base + 0x18, kPlaneStride, threshold_a, threshold_b);
            base += 0x20;                 // 0x001615D8
            counter -= 0x20;              // 0x001615DC
        } while (static_cast<s32>(counter) > 0);            // `bgt 0x160ED4`, 0x001615E4

        // 0x001615E8..0x001617BC: the remaining 8-byte groups.
        counter += 0x18;                  // 0x001615E8
        do {
            PlaneFilterGroup(base, kPlaneStride, threshold_a, threshold_b);
            base += 0x08;                 // 0x001617B0
            counter -= 0x08;              // 0x001617B4
        } while (static_cast<s32>(counter) > 0);            // `bgt 0x1615F0`, 0x001617BC

        // 0x001617C0..0x001617D8: next row.
        base += 4 * kPlaneStride - 0x18;  // 0x001617C4/0x001617C8
        rows -= 4;                        // 0x001617CC
        if (rows == 0) {
            return;
        }
        base -= cols - 0x20;              // `subne r0,r0,r2`, 0x001617D0
        counter = cols - 0x20;            // `strne r2,[sp]`, 0x001617D4
    }
}

// ---------------------------------------------------------------------------
// 0x00164C08 -- same core, plane stride 0x100
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00164c08, 3776)
void func_00164c08(PlaneFilterState* state) {
    constexpr u32 kPlaneStride = 0x100;   // loads at +0x104/+0x204/+0x304
    u8* base = state->data;
    const u32 cols = state->cols;
    u32 rows = state->rows;
    const u32 threshold_a = ReplicateByte(state->threshold_a);
    const u32 threshold_b = ReplicateByte(state->threshold_b);
    u32 counter = cols - 0x20;

    if (cols == 0x20) {
        for (;;) {
            // 0x001617E8..0x00161D24: three unrolled groups, no counter.
            PlaneFilterGroup(base + 0x00, kPlaneStride, threshold_a, threshold_b);
            PlaneFilterGroup(base + 0x08, kPlaneStride, threshold_a, threshold_b);
            PlaneFilterGroup(base + 0x10, kPlaneStride, threshold_a, threshold_b);
            base += 4 * kPlaneStride;
            rows -= 4;
            if (rows == 0) {
                return;
            }
            counter = cols - 0x20;
        }
    }

    for (;;) {
        do {
            PlaneFilterGroup(base + 0x00, kPlaneStride, threshold_a, threshold_b);
            PlaneFilterGroup(base + 0x08, kPlaneStride, threshold_a, threshold_b);
            PlaneFilterGroup(base + 0x10, kPlaneStride, threshold_a, threshold_b);
            PlaneFilterGroup(base + 0x18, kPlaneStride, threshold_a, threshold_b);
            base += 0x20;
            counter -= 0x20;
        } while (static_cast<s32>(counter) > 0);

        counter += 0x18;
        do {
            PlaneFilterGroup(base, kPlaneStride, threshold_a, threshold_b);
            base += 0x08;
            counter -= 0x08;
        } while (static_cast<s32>(counter) > 0);

        base += 4 * kPlaneStride - 0x18;  // `add r0,r0,#0x400`, 0x0016553C
        rows -= 4;
        if (rows == 0) {
            return;
        }
        base -= cols - 0x20;
        counter = cols - 0x20;
    }
}

// ---------------------------------------------------------------------------
// 0x00168980 -- same core, plane stride 0x200
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00168980, 3776)
void func_00168980(PlaneFilterState* state) {
    constexpr u32 kPlaneStride = 0x200;   // loads at +0x204/+0x404/+0x604
    u8* base = state->data;
    const u32 cols = state->cols;
    u32 rows = state->rows;
    const u32 threshold_a = ReplicateByte(state->threshold_a);
    const u32 threshold_b = ReplicateByte(state->threshold_b);
    u32 counter = cols - 0x20;

    if (cols == 0x20) {
        for (;;) {
            // 0x001617E8..0x00161D24: three unrolled groups, no counter.
            PlaneFilterGroup(base + 0x00, kPlaneStride, threshold_a, threshold_b);
            PlaneFilterGroup(base + 0x08, kPlaneStride, threshold_a, threshold_b);
            PlaneFilterGroup(base + 0x10, kPlaneStride, threshold_a, threshold_b);
            base += 4 * kPlaneStride;
            rows -= 4;
            if (rows == 0) {
                return;
            }
            counter = cols - 0x20;
        }
    }

    for (;;) {
        do {
            PlaneFilterGroup(base + 0x00, kPlaneStride, threshold_a, threshold_b);
            PlaneFilterGroup(base + 0x08, kPlaneStride, threshold_a, threshold_b);
            PlaneFilterGroup(base + 0x10, kPlaneStride, threshold_a, threshold_b);
            PlaneFilterGroup(base + 0x18, kPlaneStride, threshold_a, threshold_b);
            base += 0x20;
            counter -= 0x20;
        } while (static_cast<s32>(counter) > 0);

        counter += 0x18;
        do {
            PlaneFilterGroup(base, kPlaneStride, threshold_a, threshold_b);
            base += 0x08;
            counter -= 0x08;
        } while (static_cast<s32>(counter) > 0);

        base += 4 * kPlaneStride - 0x18;  // `add r0,r0,#0x800`, 0x001692B4
        rows -= 4;
        if (rows == 0) {
            return;
        }
        base -= cols - 0x20;
        counter = cols - 0x20;
    }
}

// ---------------------------------------------------------------------------
// 0x002F9F54 -- ribbon cross-section builder (3,636 B)
// ---------------------------------------------------------------------------

namespace {

// Literal-pool constants used by 0x002F9F54.
constexpr f32 kHalfPi = 1.5707963705062866f;             // 0x3FC90FDB
constexpr f32 kScale13 = 1.2999999523162842f;            // 0x3FA66666
constexpr f32 kScale17 = 1.7000000476837158f;            // 0x3FD9999A
constexpr f32 kScale20 = 2.0f;                           // 0x40000000
constexpr f32 kColorScale = 0.8500000238418579f;         // 0x3F59999A
constexpr f32 kWeightTwoThirds = 0.6666666269302368f;    // 0x3F2AAAAA
constexpr f32 kWeightOneThird = 0.3333333432674408f;     // 0x3EAAAAAB
constexpr f32 kWeightTwoThirdsB = 0.6666666865348816f;   // 0x3F2AAAAB
constexpr f32 kWeightOneThirdB = 0.3333333134651184f;    // 0x3EAAAAAA

// Normalisation block at 0x002FA1A0..0x002FA1E4 (first sample) and
// 0x002FA4B0..0x002FA4F4 (loop samples).
void Normalize3(f32 v[4]) {
    const f32 length =
        std::sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
    if (length > 0.0f) {
        v[0] /= length;
        v[1] /= length;
        v[2] /= length;
    }
}

// Row-vector times 3x4 matrix at 0x004EA81C+0x140 (0x002FA264..0x002FA294
// and 0x002FA57C..0x002FA5C4).
void TransformRow(const f32 m[16], const f32 in[4], f32 out[4]) {
    const f32 v0 = in[0];
    const f32 v1 = in[1];
    const f32 v2 = in[2];
    out[0] = v0 * m[0] + v1 * m[4] + v2 * m[8];
    out[1] = v0 * m[1] + v1 * m[5] + v2 * m[9];
    out[2] = v0 * m[2] + v1 * m[6] + v2 * m[10];
    out[3] = v0 * m[3] + v1 * m[7] + v2 * m[11];
}

// Four-float vector add/subtract and scalar multiply (the repeated
// vadd/vsub/vmul quartets).
void Add4(f32 dst[4], const f32 src[4]) {
    dst[0] += src[0];
    dst[1] += src[1];
    dst[2] += src[2];
    dst[3] += src[3];
}

void Sub4(f32 dst[4], const f32 src[4]) {
    dst[0] -= src[0];
    dst[1] -= src[1];
    dst[2] -= src[2];
    dst[3] -= src[3];
}

void Scale4(f32 dst[4], f32 scale) {
    dst[0] *= scale;
    dst[1] *= scale;
    dst[2] *= scale;
    dst[3] *= scale;
}

void Copy3(f32 dst[3], const f32 src[3]) {
    dst[0] = src[0];
    dst[1] = src[1];
    dst[2] = src[2];
}

} // namespace

// DECOMP_FUNC(0x002f9f54, 3636)
void func_002f9f54(SplineState* spline, u32 row, const f32* point, f32 time) {
    const f32 saved_time = time;                     // s18, 0x002F9F68
    SplineDescriptor* const input = spline->input;   // 0x002F9F70
    u8* const input_base = input->source->base;      // 0x002F9F80
    const u16 input_count = input->point_count;      // ip, 0x002F9F7C
    input->flags_58 |= 1;                            // 0x002F9F84..0x002F9F88

    // 0x002F9F94..0x002F9FD4: r4 = base + 12*ip*row + 12*ip, then shift the
    // 12-byte elements between r4-0x50 and r4-0x18 downwards in steps of 3.
    const u32 input_step = 12 * static_cast<u32>(input_count);
    u8* vertex_row = input_base + input_step * row + input_step;
    if (input_count > 3) {
        u8* dst = vertex_row + input_step - 0x18;
        const u8* src = vertex_row + input_step - 0x3C;
        for (u32 i = 3; i < input_count; i += 3) {
            std::memcpy(dst, src, 12);
            dst -= 0x24;
            src -= 0x24;
        }
    }

    // 0x002F9FD8..0x002F9FE4: store the supplied three-float point at +0x0C.
    std::memcpy(vertex_row + 0x0C, point, 12);

    // 0x002F9FF0..0x002FA020: u16 counter capped at (ip*0xAAAB)>>17 - 1.
    const u32 sample_limit =
        (((static_cast<u32>(input_count) * 0xAAABu) >> 17) - 1) & 0xFFFFu;
    u16* const counter = spline->counters + row;
    u32 sample_count = *counter;
    if (sample_count <= sample_limit) {
        sample_count = (sample_count + 1) & 0xFFFFu;
        *counter = static_cast<u16>(sample_count);
    }

    ui::UiPartRenderState& g = ui::g_UiPartRenderState;
    f32 s16 = 0.0f;
    f32 s17 = 0.0f;
    f32 s20 = 0.0f;                                  // 0x002FA034
    f32 s19 = 1.0f;                                  // 0x002FA02C
    f32 s22 = 1.0f;                                  // 0x002FA038
    f32 angle = 0.0f;                                // s23
    f32 direction[4] = {0.0f, 0.0f, 0.0f, 0.0f};     // [sp+0x20]/[sp+4]/[sp+0x18]
    f32 transformed[4] = {0.0f, 0.0f, 0.0f, 1.0f};   // loop-local matrix result
    // 0x002FA29C / 0x002FA2A4 / 0x002FA2AC store the first sample's rotated
    // quad to [sp+0x10] / [sp] / [sp+8]; the sample loop never rewrites those
    // stack slots, so the cross-section below uses this snapshot, not the
    // last loop iteration's `transformed`.
    f32 first_axis[4] = {0.0f, 0.0f, 0.0f, 1.0f};
    u32 index = 0;                                   // r5
    u16 loop_bound = 0;                              // sl

    if (sample_count > 1) {                          // `cmp r0,#1` / `bls`
        loop_bound = static_cast<u16>(sample_count - 1); // 0x002FA06C..0x002FA074

        // 0x002FA07C..0x002FA090: g_TrailScratchA -> vector, then saved.
        g.vector[0] = g_TrailScratchA[0];
        g.vector[1] = g_TrailScratchA[1];
        g.vector[2] = g_TrailScratchA[2];
        g.vector[3] = g_TrailScratchA[3];
        g.saved[0] = g.vector[0];
        g.saved[1] = g.vector[1];
        g.saved[2] = g.vector[2];
        g.saved[3] = g.vector[3];

        // 0x002FA084..0x002FA0C8: sample scale and per-step decrement.
        const f32 count_f = static_cast<f32>(sample_count);   // s2/s0
        const f32 limit_f = static_cast<f32>(sample_limit);   // s3
        s16 = count_f / limit_f;                              // 0x002FA0A0
        s20 = saved_time * s16;                               // 0x002FA0B4
        g.color[0] = spline->vector[0];                       // 0x002FA0C0
        g.color[1] = spline->vector[1];
        g.color[2] = spline->vector[2];
        g.color[3] = spline->vector[3];
        s17 = s16 / count_f;                                  // 0x002FA0C8

        // 0x002FA0D0..0x002FA134: angle = (vector . colour) * pi/2, then
        // scratch = current vertex tangent.
        angle = (g.vector[0] * g.color[0] +
                 g.vector[1] * g.color[1] +
                 g.vector[2] * g.color[2]) * kHalfPi;
        // 0x002FA0F4/0x002FA108/0x002FA110: the persistent 0x00472550 scratch
        // receives the current vertex tangent before it is copied to
        // 0x004EA81C+0x120 (`ldm r7` -> `stm r0`, 0x002FA114/0x002FA130).
        g_TrailScratchB[0] = *reinterpret_cast<const f32*>(vertex_row + 0x0C);
        g_TrailScratchB[1] = *reinterpret_cast<const f32*>(vertex_row + 0x10);
        g_TrailScratchB[2] = *reinterpret_cast<const f32*>(vertex_row + 0x14);
        g.scratch[0] = g_TrailScratchB[0];
        g.scratch[1] = g_TrailScratchB[1];
        g.scratch[2] = g_TrailScratchB[2];
        g.scratch[3] = g_TrailScratchB[3];

        // 0x002FA138..0x002FA158: vector = next vertex tangent, w = r7[3].
        const u8* const next_row = vertex_row + sizeof(SplineVertex);
        g.vector[0] = *reinterpret_cast<const f32*>(next_row + 0x0C);
        g.vector[1] = *reinterpret_cast<const f32*>(next_row + 0x10);
        g.vector[2] = *reinterpret_cast<const f32*>(next_row + 0x14);
        g.vector[3] = g_TrailScratchB[3];

        // 0x002FA15C..0x002FA1E4: next - current, normalised.
        Sub4(g.vector, g.scratch);
        Normalize3(g.vector);
        direction[0] = g.vector[0];
        direction[1] = g.vector[1];
        direction[2] = g.vector[2];
        s22 = g.vector[3];

        ui_func_0030f418(angle);                       // 0x002FA208

        // 0x002FA20C..0x002FA294: restore the saved axis and rotate it.
        g.vector[0] = g.saved[0];
        g.vector[1] = g.saved[1];
        g.vector[2] = g.saved[2];
        g.vector[3] = g.saved[3];
        TransformRow(g.matrix, g.vector, transformed);
        g.vector[0] = transformed[0];
        g.vector[1] = transformed[1];
        g.vector[2] = transformed[2];
        g.vector[3] = transformed[3];
        s19 = transformed[3];                          // 0x002FA2B4
        first_axis[0] = transformed[0];                // 0x002FA29C ([sp+0x10])
        first_axis[1] = transformed[1];                // 0x002FA2A4 ([sp])
        first_axis[2] = transformed[2];                // 0x002FA2AC ([sp+8])
        first_axis[3] = transformed[3];                // s19

        // 0x002FA298..0x002FA2CC: first sample scale.
        Scale4(g.vector, s20);
        Add4(g.scratch, g.vector);

        // 0x002FA300..0x002FA30C: position = accumulated scratch.
        Copy3(reinterpret_cast<f32*>(vertex_row + 0x00), g.scratch);

        // 0x002FA320..0x002FA3AC: scratch -= vector twice; normal = scratch.
        Sub4(g.scratch, g.vector);
        Sub4(g.scratch, g.vector);
        Copy3(reinterpret_cast<f32*>(vertex_row + 0x18), g.scratch);
        g_TrailScratchB[0] = g.scratch[0];             // 0x002FA3B0..0x002FA3DC
        g_TrailScratchB[1] = g.scratch[1];
        g_TrailScratchB[2] = g.scratch[2];
        g_TrailScratchB[3] = g.scratch[3];
        s16 -= s17;                                    // 0x002FA33C

        vertex_row += sizeof(SplineVertex);            // 0x002FA3F0/0x002FA3F4
        index = 1;

        if (loop_bound > 1) {
            for (;;) {
                u8* const current = vertex_row;

                // 0x002FA3FC..0x002FA468: r7[0..2] receives the current
                // tangent (persistent 0x00472550), then scratch = r7.
                g_TrailScratchB[0] = *reinterpret_cast<const f32*>(current + 0x0C);
                g_TrailScratchB[1] = *reinterpret_cast<const f32*>(current + 0x10);
                g_TrailScratchB[2] = *reinterpret_cast<const f32*>(current + 0x14);
                g.scratch[0] = g_TrailScratchB[0];
                g.scratch[1] = g_TrailScratchB[1];
                g.scratch[2] = g_TrailScratchB[2];
                g.scratch[3] = g_TrailScratchB[3];
                const u8* const next = current + sizeof(SplineVertex);
                g.vector[0] = *reinterpret_cast<const f32*>(next + 0x0C);
                g.vector[1] = *reinterpret_cast<const f32*>(next + 0x10);
                g.vector[2] = *reinterpret_cast<const f32*>(next + 0x14);
                g.vector[3] = g_TrailScratchB[3];

                // 0x002FA46C..0x002FA4F4: next - current, normalised.
                Sub4(g.vector, g.scratch);
                Normalize3(g.vector);

                ui_func_0030f418(angle);               // 0x002FA4FC

                // 0x002FA500..0x002FA528: restore and pick this sample scale.
                g.vector[0] = g.saved[0];
                g.vector[1] = g.saved[1];
                g.vector[2] = g.saved[2];
                g.vector[3] = g.saved[3];
                const f32 sample_scale = saved_time * s16;
                s16 -= s17;                            // 0x002FA574

                TransformRow(g.matrix, g.vector, transformed);
                g.vector[0] = transformed[0];          // 0x002FA5D0
                g.vector[1] = transformed[1];
                g.vector[2] = transformed[2];
                g.vector[3] = transformed[3];
                Scale4(g.vector, sample_scale);

                // 0x002FA5E0..0x002FA610: accumulate and store position.
                Add4(g.scratch, g.vector);
                Copy3(reinterpret_cast<f32*>(current + 0x00), g.scratch);

                // 0x002FA634..0x002FA6B0: scratch -= vector twice.
                Sub4(g.scratch, g.vector);
                Sub4(g.scratch, g.vector);

                // 0x002FA6B4..0x002FA6D4: normal = scratch, save scratch.
                Copy3(reinterpret_cast<f32*>(current + 0x18), g.scratch);
                g_TrailScratchB[0] = g.scratch[0];
                g_TrailScratchB[1] = g.scratch[1];
                g_TrailScratchB[2] = g.scratch[2];
                g_TrailScratchB[3] = g.scratch[3];

                vertex_row += sizeof(SplineVertex);    // 0x002FA6E0
                ++index;                               // 0x002FA6D0/0x002FA6D8
                if (index >= loop_bound) {             // `blo 0x2FA3FC`
                    break;
                }
            }
        }
    }

    // 0x002FA6E8..0x002FA758: replicate the current vertex when the counter
    // overshoots the requested sample count.
    {
        f32 tangent[3];
        tangent[0] = *reinterpret_cast<const f32*>(vertex_row + 0x0C);
        tangent[1] = *reinterpret_cast<const f32*>(vertex_row + 0x10);
        tangent[2] = *reinterpret_cast<const f32*>(vertex_row + 0x14);
        Copy3(reinterpret_cast<f32*>(vertex_row + 0x00), tangent);
        Copy3(reinterpret_cast<f32*>(vertex_row + 0x18), tangent);

        const s32 remaining =
            static_cast<s32>(sample_limit - index);   // 0x002FA6F8
        if (remaining > 0) {                          // `ble 0x2FA75C`
            u32 fill = static_cast<u32>(remaining) & 0xFFFFu;
            do {
                std::memcpy(vertex_row + sizeof(SplineVertex), vertex_row,
                            sizeof(SplineVertex));
                vertex_row += sizeof(SplineVertex);   // 0x002FA740
                fill = (fill - 1) & 0xFFFFu;          // 0x002FA73C/0x002FA744
            } while (fill != 0);                      // `bne 0x2FA71C`
        }
    }

    // -----------------------------------------------------------------------
    // 0x002FA75C..0x002FAD70: write the cross-section row.
    // -----------------------------------------------------------------------
    SplineDescriptor* const output = spline->output; // 0x002FA760
    const u16 output_count = output->point_count;    // 0x002FA768
    u8* const output_base = output->source->base;    // 0x002FA76C
    output->flags_58 |= 1;                           // 0x002FA770..0x002FA778

    // r1 = output_base + 12 * output_count * row.
    const u32 output_step = 12 * static_cast<u32>(output_count);
    u8* const output_row = output_base + output_step * row; // 0x002FA79C

    // `fp` still points at the first vertex of the input row.
    const u8* const first_vertex = input_base + input_step * row + input_step;

    // 0x002FA790..0x002FA7C0: +0x00 tangent, +0x0C position, +0x54 normal.
    std::memcpy(output_row + 0x00, first_vertex + 0x0C, 12);
    std::memcpy(output_row + 0x0C, first_vertex + 0x00, 12);
    std::memcpy(output_row + 0x54, first_vertex + 0x18, 12);

    // 0x002FA7C4..0x002FA828: colour = -direction * 2 * s20.
    g.color[0] = direction[0];                        // 0x002FA7C8
    g.color[1] = direction[1];                        // 0x002FA7D4
    g.color[2] = direction[2];
    g.color[3] = s22;                                 // 0x002FA7D0
    g.color[0] = -g.color[0];
    g.color[1] = -g.color[1];
    g.color[2] = -g.color[2];
    Scale4(g.color, kScale20 * s20);                  // 0x002FA7F8..0x002FA828

    // 0x002FA82C..0x002FA868: scratch = first tangent, vector = first
    // transformed axis * 1.3.
    g.scratch[0] = *reinterpret_cast<const f32*>(first_vertex + 0x0C);
    g.scratch[1] = *reinterpret_cast<const f32*>(first_vertex + 0x10);
    g.scratch[2] = *reinterpret_cast<const f32*>(first_vertex + 0x14);
    g.scratch[3] = g_TrailScratchB[3];
    g.vector[0] = first_axis[0];                      // [sp+0x10]
    g.vector[1] = first_axis[1];                      // [sp]
    g.vector[2] = first_axis[2];                      // [sp+8]
    g.vector[3] = s19;                                // 0x002FA864
    const f32 scale13 = s20 * kScale13;               // s2, 0x002FA870
    Scale4(g.vector, scale13);

    // 0x002FA8A8..0x002FA8F8: (2/3)*vector + (1/3)*colour.
    for (u32 i = 0; i < 4; ++i) {
        g.vector[i] = g.vector[i] * kWeightTwoThirds +
                      g.color[i] * kWeightOneThird;
    }
    Add4(g.vector, g.scratch);                        // 0x002FA8FC..0x002FA938
    std::memcpy(g_TrailScratchB, g.vector, sizeof(g.vector)); // 0x002FA93C..0x002FA95C
    std::memcpy(output_row + 0x18, g.vector, 12);     // 0x002FA964..0x002FA974

    // 0x002FA978..0x002FA9AC: vector = first transformed axis * 1.7.
    g.vector[0] = first_axis[0];
    g.vector[1] = first_axis[1];
    g.vector[2] = first_axis[2];
    g.vector[3] = s19;
    const f32 scale17 = s20 * kScale17;               // s5, 0x002FA98C
    Scale4(g.vector, scale17);

    // 0x002FA9B4..0x002FA9F4: (1/3)*vector + (2/3)*colour.
    for (u32 i = 0; i < 4; ++i) {
        g.vector[i] = g.vector[i] * kWeightOneThirdB +
                      g.color[i] * kWeightTwoThirdsB;
    }
    Add4(g.vector, g.scratch);                        // 0x002FAA14..0x002FAA50
    std::memcpy(g_TrailScratchB, g.vector, sizeof(g.vector)); // 0x002FAA54..0x002FAA70
    std::memcpy(output_row + 0x24, g.vector, 12);     // 0x002FAA78..0x002FAA88

    // 0x002FAA8C..0x002FAB74: -1.3*axis, (2/3)*vector + (1/3)*colour.
    g.vector[0] = first_axis[0];
    g.vector[1] = first_axis[1];
    g.vector[2] = first_axis[2];
    g.vector[3] = s19;
    Scale4(g.vector, scale13);                        // 0x002FAA9C..0x002FAABC
    g.vector[0] = -g.vector[0];                       // 0x002FAAC0
    g.vector[1] = -g.vector[1];
    g.vector[2] = -g.vector[2];
    for (u32 i = 0; i < 4; ++i) {
        g.vector[i] = g.vector[i] * kWeightTwoThirds +
                      g.color[i] * kWeightOneThird;
    }
    Add4(g.vector, g.scratch);                        // 0x002FAB38..0x002FAB74
    std::memcpy(g_TrailScratchB, g.vector, sizeof(g.vector)); // 0x002FAB78..0x002FABA0
    std::memcpy(output_row + 0x48, g.vector, 12);     // 0x002FAB90..0x002FABA0

    // 0x002FABA4..0x002FAC6C: -1.7*axis, (1/3)*vector + (2/3)*colour.
    g.vector[0] = first_axis[0];
    g.vector[1] = first_axis[1];
    g.vector[2] = first_axis[2];
    g.vector[3] = s19;
    Scale4(g.vector, scale17);                        // 0x002FABB0..0x002FABF8
    g.vector[0] = -g.vector[0];                       // 0x002FABFC
    g.vector[1] = -g.vector[1];
    g.vector[2] = -g.vector[2];
    for (u32 i = 0; i < 4; ++i) {
        g.vector[i] = g.vector[i] * kWeightOneThirdB +
                      g.color[i] * kWeightTwoThirdsB;
    }
    Add4(g.vector, g.scratch);                        // 0x002FAC70..0x002FACAC
    std::memcpy(g_TrailScratchB, g.vector, sizeof(g.vector)); // 0x002FACB0..0x002FACD4
    std::memcpy(output_row + 0x3C, g.vector, 12);     // 0x002FACC4..0x002FACD4

    // 0x002FACD8..0x002FAD4C: colour = colour * 0.85 + scratch.
    Scale4(g.color, kColorScale);
    Add4(g.color, g.scratch);
    std::memcpy(g_TrailScratchB, g.color, sizeof(g.color)); // 0x002FAD50..0x002FAD60
    std::memcpy(output_row + 0x30, g.color, 12);      // 0x002FAD50..0x002FAD70
}

} // namespace smt4::engine
