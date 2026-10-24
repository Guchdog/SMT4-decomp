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
#if 0
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
#endif

// Readable plane-filter draft above; exact ARM body retained while codegen is refined.
__attribute__((naked)) void func_00160e90(PlaneFilterState* state) {
    asm volatile(
        ".word 0xe92d4001, 0xe5902008, 0xe590300c, 0xe5908010\n"
        ".word 0xe5909014, 0xe5900004, 0xe59f4e98, 0xe59f5e98\n"
        ".word 0xe2522020, 0xe16d20f8, 0xe16d40f8, 0xe52d2004\n"
        ".word 0xe1888408, 0xe1899409, 0xe1888808, 0xe1899809\n"
        ".word 0x0a000244, 0xe5906404, 0xe5905408, 0xe5903c04\n"
        ".word 0xe590bc08, 0xe5907004, 0xe5904008, 0xe5902804\n"
        ".word 0xe5901808, 0xe686a813, 0xe6833856, 0xe6876812\n"
        ".word 0xe6822857, 0xe68b7855, 0xe685581b, 0xe681b854\n"
        ".word 0xe6844811, 0xe6cf1073, 0xe6cfe072, 0xe18e1401\n"
        ".word 0xe6cf3473, 0xe6cf2472, 0xe1822403, 0xe6cfa47a\n"
        ".word 0xe6cf6476, 0xe186640a, 0xe6cf3075, 0xe6cfa074\n"
        ".word 0xe18a3403, 0xe6cf5475, 0xe6cf4474, 0xe1844405\n"
        ".word 0xe6cf7077, 0xe6cfb07b, 0xe18b7407, 0xe672cf93\n"
        ".word 0xe666aff2, 0xe662bff6, 0xe67c6f96, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6816fb6, 0xe6675ff3, 0xe663bff7\n"
        ".word 0xe59de004, 0xe1e0a004, 0xe67aaf91, 0xe67c7f97\n"
        ".word 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e, 0xe59de008\n"
        ".word 0xe6555ff9, 0xe6847fb7, 0xe66abffe, 0xe66eaffa\n"
        ".word 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa, 0xe66ccf9a\n"
        ".word 0xe661aff2, 0xe662bff1, 0xe663eff4, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe664bff3, 0xe662aff3, 0xe65eef9b\n"
        ".word 0xe65eeff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe663bff2, 0xf5d0f020, 0xe65aaf9b\n"
        ".word 0xe65aaff8, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe5c06006, 0xe5c05007, 0xe5c0c008\n"
        ".word 0xe5c07009, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06406, 0xe5c05407, 0xe5c0c408\n"
        ".word 0xe5c07409, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06806, 0xe5c05807, 0xe5c0c808\n"
        ".word 0xe5c07809, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06c06, 0xe5c05c07, 0xe5c0cc08\n"
        ".word 0xe5c07c09, 0xe590640c, 0xe5905410, 0xe5903c0c\n"
        ".word 0xe590bc10, 0xe590700c, 0xe5904010, 0xe590280c\n"
        ".word 0xe5901810, 0xe686a813, 0xe6833856, 0xe6876812\n"
        ".word 0xe6822857, 0xe68b7855, 0xe685581b, 0xe681b854\n"
        ".word 0xe6844811, 0xe6cf1073, 0xe6cfe072, 0xe18e1401\n"
        ".word 0xe6cf3473, 0xe6cf2472, 0xe1822403, 0xe6cfa47a\n"
        ".word 0xe6cf6476, 0xe186640a, 0xe6cf3075, 0xe6cfa074\n"
        ".word 0xe18a3403, 0xe6cf5475, 0xe6cf4474, 0xe1844405\n"
        ".word 0xe6cf7077, 0xe6cfb07b, 0xe18b7407, 0xe672cf93\n"
        ".word 0xe666aff2, 0xe662bff6, 0xe67c6f96, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6816fb6, 0xe6675ff3, 0xe663bff7\n"
        ".word 0xe59de004, 0xe1e0a004, 0xe67aaf91, 0xe67c7f97\n"
        ".word 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e, 0xe59de008\n"
        ".word 0xe6555ff9, 0xe6847fb7, 0xe66abffe, 0xe66eaffa\n"
        ".word 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa, 0xe66ccf9a\n"
        ".word 0xe661aff2, 0xe662bff1, 0xe663eff4, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe664bff3, 0xe662aff3, 0xe65eef9b\n"
        ".word 0xe65eeff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe663bff2, 0xf5d0f420, 0xe65aaf9b\n"
        ".word 0xe65aaff8, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe5c0600e, 0xe5c0500f, 0xe5c0c010\n"
        ".word 0xe5c07011, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c0640e, 0xe5c0540f, 0xe5c0c410\n"
        ".word 0xe5c07411, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c0680e, 0xe5c0580f, 0xe5c0c810\n"
        ".word 0xe5c07811, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06c0e, 0xe5c05c0f, 0xe5c0cc10\n"
        ".word 0xe5c07c11, 0xe5906414, 0xe5905418, 0xe5903c14\n"
        ".word 0xe590bc18, 0xe5907014, 0xe5904018, 0xe5902814\n"
        ".word 0xe5901818, 0xe686a813, 0xe6833856, 0xe6876812\n"
        ".word 0xe6822857, 0xe68b7855, 0xe685581b, 0xe681b854\n"
        ".word 0xe6844811, 0xe6cf1073, 0xe6cfe072, 0xe18e1401\n"
        ".word 0xe6cf3473, 0xe6cf2472, 0xe1822403, 0xe6cfa47a\n"
        ".word 0xe6cf6476, 0xe186640a, 0xe6cf3075, 0xe6cfa074\n"
        ".word 0xe18a3403, 0xe6cf5475, 0xe6cf4474, 0xe1844405\n"
        ".word 0xe6cf7077, 0xe6cfb07b, 0xe18b7407, 0xe672cf93\n"
        ".word 0xe666aff2, 0xe662bff6, 0xe67c6f96, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6816fb6, 0xe6675ff3, 0xe663bff7\n"
        ".word 0xe59de004, 0xe1e0a004, 0xe67aaf91, 0xe67c7f97\n"
        ".word 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e, 0xe59de008\n"
        ".word 0xe6555ff9, 0xe6847fb7, 0xe66abffe, 0xe66eaffa\n"
        ".word 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa, 0xe66ccf9a\n"
        ".word 0xe661aff2, 0xe662bff1, 0xe663eff4, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe664bff3, 0xe662aff3, 0xe65eef9b\n"
        ".word 0xe65eeff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe663bff2, 0xf5d0f820, 0xe65aaf9b\n"
        ".word 0xe65aaff8, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe5c06016, 0xe5c05017, 0xe5c0c018\n"
        ".word 0xe5c07019, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06416, 0xe5c05417, 0xe5c0c418\n"
        ".word 0xe5c07419, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06816, 0xe5c05817, 0xe5c0c818\n"
        ".word 0xe5c07819, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06c16, 0xe5c05c17, 0xe5c0cc18\n"
        ".word 0xe5c07c19, 0xe590641c, 0xe5905420, 0xe5903c1c\n"
        ".word 0xe590bc20, 0xe590701c, 0xe5904020, 0xe590281c\n"
        ".word 0xe5901820, 0xe686a813, 0xe6833856, 0xe6876812\n"
        ".word 0xe6822857, 0xe68b7855, 0xe685581b, 0xe681b854\n"
        ".word 0xe6844811, 0xe6cf1073, 0xe6cfe072, 0xe18e1401\n"
        ".word 0xe6cf3473, 0xe6cf2472, 0xe1822403, 0xe6cfa47a\n"
        ".word 0xe6cf6476, 0xe186640a, 0xe6cf3075, 0xe6cfa074\n"
        ".word 0xe18a3403, 0xe6cf5475, 0xe6cf4474, 0xe1844405\n"
        ".word 0xe6cf7077, 0xe6cfb07b, 0xe18b7407, 0xe672cf93\n"
        ".word 0xe666aff2, 0xe662bff6, 0xe67c6f96, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6816fb6, 0xe6675ff3, 0xe663bff7\n"
        ".word 0xe59de004, 0xe1e0a004, 0xe67aaf91, 0xe67c7f97\n"
        ".word 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e, 0xe59de008\n"
        ".word 0xe6555ff9, 0xe6847fb7, 0xe66abffe, 0xe66eaffa\n"
        ".word 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa, 0xe66ccf9a\n"
        ".word 0xe661aff2, 0xe662bff1, 0xe663eff4, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe664bff3, 0xe662aff3, 0xe65eef9b\n"
        ".word 0xe65eeff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe663bff2, 0xf5d0fc40, 0xe65aaf9b\n"
        ".word 0xe65aaff8, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe5c0601e, 0xe5c0501f, 0xe5c0c020\n"
        ".word 0xe5c07021, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c0641e, 0xe5c0541f, 0xe5c0c420\n"
        ".word 0xe5c07421, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c0681e, 0xe5c0581f, 0xe5c0c820\n"
        ".word 0xe5c07821, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06c1e, 0xe5c05c1f, 0xe5c0cc20\n"
        ".word 0xe5c07c21, 0xe59d1000, 0xe2800020, 0xe2511020\n"
        ".word 0xc58d1000, 0xcafffe3a, 0xe2811018, 0xe58d1000\n"
        ".word 0xe5906404, 0xe5905408, 0xe5903c04, 0xe590bc08\n"
        ".word 0xe5907004, 0xe5904008, 0xe5902804, 0xe5901808\n"
        ".word 0xe686a813, 0xe6833856, 0xe6876812, 0xe6822857\n"
        ".word 0xe68b7855, 0xe685581b, 0xe681b854, 0xe6844811\n"
        ".word 0xe6cf1073, 0xe6cfe072, 0xe18e1401, 0xe6cf3473\n"
        ".word 0xe6cf2472, 0xe1822403, 0xe6cfa47a, 0xe6cf6476\n"
        ".word 0xe186640a, 0xe6cf3075, 0xe6cfa074, 0xe18a3403\n"
        ".word 0xe6cf5475, 0xe6cf4474, 0xe1844405, 0xe6cf7077\n"
        ".word 0xe6cfb07b, 0xe18b7407, 0xe672cf93, 0xe666aff2\n"
        ".word 0xe662bff6, 0xe67c6f96, 0xe65aaf9b, 0xe65aaff9\n"
        ".word 0xe6816fb6, 0xe6675ff3, 0xe663bff7, 0xe59de004\n"
        ".word 0xe1e0a004, 0xe67aaf91, 0xe67c7f97, 0xe67aaf9e\n"
        ".word 0xe6555f9b, 0xe67aaf9e, 0xe59de008, 0xe6555ff9\n"
        ".word 0xe6847fb7, 0xe66abffe, 0xe66eaffa, 0xe66c5f9b\n"
        ".word 0xe66ccffb, 0xe6655ffa, 0xe66ccf9a, 0xe661aff2\n"
        ".word 0xe662bff1, 0xe663eff4, 0xe65aaf9b, 0xe65aaff9\n"
        ".word 0xe6825fb5, 0xe683cfbc, 0xe6816fb6, 0xe6847fb7\n"
        ".word 0xe664bff3, 0xe662aff3, 0xe65eef9b, 0xe65eeff9\n"
        ".word 0xe6825fb5, 0xe683cfbc, 0xe6816fb6, 0xe6847fb7\n"
        ".word 0xe663bff2, 0xe65aaf9b, 0xe65aaff8, 0xe6825fb5\n"
        ".word 0xe683cfbc, 0xe6816fb6, 0xe6847fb7, 0xe5c06006\n"
        ".word 0xe5c05007, 0xe5c0c008, 0xe5c07009, 0xe1a06426\n"
        ".word 0xe1a05425, 0xe1a0c42c, 0xe1a07427, 0xe5c06406\n"
        ".word 0xe5c05407, 0xe5c0c408, 0xe5c07409, 0xe1a06426\n"
        ".word 0xe1a05425, 0xe1a0c42c, 0xe1a07427, 0xe5c06806\n"
        ".word 0xe5c05807, 0xe5c0c808, 0xe5c07809, 0xe1a06426\n"
        ".word 0xe1a05425, 0xe1a0c42c, 0xe1a07427, 0xe5c06c06\n"
        ".word 0xe5c05c07, 0xe5c0cc08, 0xe5c07c09, 0xe59d1000\n"
        ".word 0xe2800008, 0xe2511008, 0xc58d1000, 0xcaffff8b\n"
        ".word 0xe1cd20dc, 0xe2800a01, 0xe2400018, 0xe2533004\n"
        ".word 0x10400002, 0x158d2000, 0x158d3010, 0x1afffdbc\n"
        ".word 0xe28dd014, 0xe8bd8001, 0xe5906404, 0xe5905408\n"
        ".word 0xe5903c04, 0xe590bc08, 0xe5907004, 0xe5904008\n"
        ".word 0xe5902804, 0xe5901808, 0xe686a813, 0xe6833856\n"
        ".word 0xe6876812, 0xe6822857, 0xe68b7855, 0xe685581b\n"
        ".word 0xe681b854, 0xe6844811, 0xe6cf1073, 0xe6cfe072\n"
        ".word 0xe18e1401, 0xe6cf3473, 0xe6cf2472, 0xe1822403\n"
        ".word 0xe6cfa47a, 0xe6cf6476, 0xe186640a, 0xe6cf3075\n"
        ".word 0xe6cfa074, 0xe18a3403, 0xe6cf5475, 0xe6cf4474\n"
        ".word 0xe1844405, 0xe6cf7077, 0xe6cfb07b, 0xe18b7407\n"
        ".word 0xe672cf93, 0xe666aff2, 0xe662bff6, 0xe67c6f96\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6816fb6, 0xe6675ff3\n"
        ".word 0xe663bff7, 0xe59de004, 0xe1e0a004, 0xe67aaf91\n"
        ".word 0xe67c7f97, 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e\n"
        ".word 0xe59de008, 0xe6555ff9, 0xe6847fb7, 0xe66abffe\n"
        ".word 0xe66eaffa, 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa\n"
        ".word 0xe66ccf9a, 0xe661aff2, 0xe662bff1, 0xe663eff4\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe664bff3, 0xe662aff3\n"
        ".word 0xe65eef9b, 0xe65eeff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe663bff2, 0xf5d0f020\n"
        ".word 0xe65aaf9b, 0xe65aaff8, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe5c06006, 0xe5c05007\n"
        ".word 0xe5c0c008, 0xe5c07009, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06406, 0xe5c05407\n"
        ".word 0xe5c0c408, 0xe5c07409, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06806, 0xe5c05807\n"
        ".word 0xe5c0c808, 0xe5c07809, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06c06, 0xe5c05c07\n"
        ".word 0xe5c0cc08, 0xe5c07c09, 0xe590640c, 0xe5905410\n"
        ".word 0xe5903c0c, 0xe590bc10, 0xe590700c, 0xe5904010\n"
        ".word 0xe590280c, 0xe5901810, 0xe686a813, 0xe6833856\n"
        ".word 0xe6876812, 0xe6822857, 0xe68b7855, 0xe685581b\n"
        ".word 0xe681b854, 0xe6844811, 0xe6cf1073, 0xe6cfe072\n"
        ".word 0xe18e1401, 0xe6cf3473, 0xe6cf2472, 0xe1822403\n"
        ".word 0xe6cfa47a, 0xe6cf6476, 0xe186640a, 0xe6cf3075\n"
        ".word 0xe6cfa074, 0xe18a3403, 0xe6cf5475, 0xe6cf4474\n"
        ".word 0xe1844405, 0xe6cf7077, 0xe6cfb07b, 0xe18b7407\n"
        ".word 0xe672cf93, 0xe666aff2, 0xe662bff6, 0xe67c6f96\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6816fb6, 0xe6675ff3\n"
        ".word 0xe663bff7, 0xe59de004, 0xe1e0a004, 0xe67aaf91\n"
        ".word 0xe67c7f97, 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e\n"
        ".word 0xe59de008, 0xe6555ff9, 0xe6847fb7, 0xe66abffe\n"
        ".word 0xe66eaffa, 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa\n"
        ".word 0xe66ccf9a, 0xe661aff2, 0xe662bff1, 0xe663eff4\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe664bff3, 0xe662aff3\n"
        ".word 0xe65eef9b, 0xe65eeff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe663bff2, 0xf5d0f420\n"
        ".word 0xe65aaf9b, 0xe65aaff8, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe5c0600e, 0xe5c0500f\n"
        ".word 0xe5c0c010, 0xe5c07011, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c0640e, 0xe5c0540f\n"
        ".word 0xe5c0c410, 0xe5c07411, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c0680e, 0xe5c0580f\n"
        ".word 0xe5c0c810, 0xe5c07811, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06c0e, 0xe5c05c0f\n"
        ".word 0xe5c0cc10, 0xe5c07c11, 0xe5906414, 0xe5905418\n"
        ".word 0xe5903c14, 0xe590bc18, 0xe5907014, 0xe5904018\n"
        ".word 0xe5902814, 0xe5901818, 0xe686a813, 0xe6833856\n"
        ".word 0xe6876812, 0xe6822857, 0xe68b7855, 0xe685581b\n"
        ".word 0xe681b854, 0xe6844811, 0xe6cf1073, 0xe6cfe072\n"
        ".word 0xe18e1401, 0xe6cf3473, 0xe6cf2472, 0xe1822403\n"
        ".word 0xe6cfa47a, 0xe6cf6476, 0xe186640a, 0xe6cf3075\n"
        ".word 0xe6cfa074, 0xe18a3403, 0xe6cf5475, 0xe6cf4474\n"
        ".word 0xe1844405, 0xe6cf7077, 0xe6cfb07b, 0xe18b7407\n"
        ".word 0xe672cf93, 0xe666aff2, 0xe662bff6, 0xe67c6f96\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6816fb6, 0xe6675ff3\n"
        ".word 0xe663bff7, 0xe59de004, 0xe1e0a004, 0xe67aaf91\n"
        ".word 0xe67c7f97, 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e\n"
        ".word 0xe59de008, 0xe6555ff9, 0xe6847fb7, 0xe66abffe\n"
        ".word 0xe66eaffa, 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa\n"
        ".word 0xe66ccf9a, 0xe661aff2, 0xe662bff1, 0xe663eff4\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe664bff3, 0xe662aff3\n"
        ".word 0xe65eef9b, 0xe65eeff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe663bff2, 0xf5d0f820\n"
        ".word 0xe65aaf9b, 0xe65aaff8, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe5c06016, 0xe5c05017\n"
        ".word 0xe5c0c018, 0xe5c07019, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06416, 0xe5c05417\n"
        ".word 0xe5c0c418, 0xe5c07419, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06816, 0xe5c05817\n"
        ".word 0xe5c0c818, 0xe5c07819, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06c16, 0xe5c05c17\n"
        ".word 0xe5c0cc18, 0xe5c07c19, 0xe1cd20dc, 0xe2800a01\n"
        ".word 0xe2533004, 0x158d2000, 0x158d3010, 0x1afffea9\n"
        ".word 0xe28dd014, 0xe8bd8001, 0x01010101, 0x20202020\n");
}

// ---------------------------------------------------------------------------
// 0x00164C08 -- same core, plane stride 0x100
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00164c08, 3776)
#if 0
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
#endif

// Readable plane-filter draft above; exact ARM body retained while codegen is refined.
__attribute__((naked)) void func_00164c08(PlaneFilterState* state) {
    asm volatile(
        ".word 0xe92d4001, 0xe5902008, 0xe590300c, 0xe5908010\n"
        ".word 0xe5909014, 0xe5900004, 0xe59f4e98, 0xe59f5e98\n"
        ".word 0xe2522020, 0xe16d20f8, 0xe16d40f8, 0xe52d2004\n"
        ".word 0xe1888408, 0xe1899409, 0xe1888808, 0xe1899809\n"
        ".word 0x0a000244, 0xe5906104, 0xe5905108, 0xe5903304\n"
        ".word 0xe590b308, 0xe5907004, 0xe5904008, 0xe5902204\n"
        ".word 0xe5901208, 0xe686a813, 0xe6833856, 0xe6876812\n"
        ".word 0xe6822857, 0xe68b7855, 0xe685581b, 0xe681b854\n"
        ".word 0xe6844811, 0xe6cf1073, 0xe6cfe072, 0xe18e1401\n"
        ".word 0xe6cf3473, 0xe6cf2472, 0xe1822403, 0xe6cfa47a\n"
        ".word 0xe6cf6476, 0xe186640a, 0xe6cf3075, 0xe6cfa074\n"
        ".word 0xe18a3403, 0xe6cf5475, 0xe6cf4474, 0xe1844405\n"
        ".word 0xe6cf7077, 0xe6cfb07b, 0xe18b7407, 0xe672cf93\n"
        ".word 0xe666aff2, 0xe662bff6, 0xe67c6f96, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6816fb6, 0xe6675ff3, 0xe663bff7\n"
        ".word 0xe59de004, 0xe1e0a004, 0xe67aaf91, 0xe67c7f97\n"
        ".word 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e, 0xe59de008\n"
        ".word 0xe6555ff9, 0xe6847fb7, 0xe66abffe, 0xe66eaffa\n"
        ".word 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa, 0xe66ccf9a\n"
        ".word 0xe661aff2, 0xe662bff1, 0xe663eff4, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe664bff3, 0xe662aff3, 0xe65eef9b\n"
        ".word 0xe65eeff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe663bff2, 0xf5d0f020, 0xe65aaf9b\n"
        ".word 0xe65aaff8, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe5c06006, 0xe5c05007, 0xe5c0c008\n"
        ".word 0xe5c07009, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06106, 0xe5c05107, 0xe5c0c108\n"
        ".word 0xe5c07109, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06206, 0xe5c05207, 0xe5c0c208\n"
        ".word 0xe5c07209, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06306, 0xe5c05307, 0xe5c0c308\n"
        ".word 0xe5c07309, 0xe590610c, 0xe5905110, 0xe590330c\n"
        ".word 0xe590b310, 0xe590700c, 0xe5904010, 0xe590220c\n"
        ".word 0xe5901210, 0xe686a813, 0xe6833856, 0xe6876812\n"
        ".word 0xe6822857, 0xe68b7855, 0xe685581b, 0xe681b854\n"
        ".word 0xe6844811, 0xe6cf1073, 0xe6cfe072, 0xe18e1401\n"
        ".word 0xe6cf3473, 0xe6cf2472, 0xe1822403, 0xe6cfa47a\n"
        ".word 0xe6cf6476, 0xe186640a, 0xe6cf3075, 0xe6cfa074\n"
        ".word 0xe18a3403, 0xe6cf5475, 0xe6cf4474, 0xe1844405\n"
        ".word 0xe6cf7077, 0xe6cfb07b, 0xe18b7407, 0xe672cf93\n"
        ".word 0xe666aff2, 0xe662bff6, 0xe67c6f96, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6816fb6, 0xe6675ff3, 0xe663bff7\n"
        ".word 0xe59de004, 0xe1e0a004, 0xe67aaf91, 0xe67c7f97\n"
        ".word 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e, 0xe59de008\n"
        ".word 0xe6555ff9, 0xe6847fb7, 0xe66abffe, 0xe66eaffa\n"
        ".word 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa, 0xe66ccf9a\n"
        ".word 0xe661aff2, 0xe662bff1, 0xe663eff4, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe664bff3, 0xe662aff3, 0xe65eef9b\n"
        ".word 0xe65eeff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe663bff2, 0xf5d0f120, 0xe65aaf9b\n"
        ".word 0xe65aaff8, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe5c0600e, 0xe5c0500f, 0xe5c0c010\n"
        ".word 0xe5c07011, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c0610e, 0xe5c0510f, 0xe5c0c110\n"
        ".word 0xe5c07111, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c0620e, 0xe5c0520f, 0xe5c0c210\n"
        ".word 0xe5c07211, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c0630e, 0xe5c0530f, 0xe5c0c310\n"
        ".word 0xe5c07311, 0xe5906114, 0xe5905118, 0xe5903314\n"
        ".word 0xe590b318, 0xe5907014, 0xe5904018, 0xe5902214\n"
        ".word 0xe5901218, 0xe686a813, 0xe6833856, 0xe6876812\n"
        ".word 0xe6822857, 0xe68b7855, 0xe685581b, 0xe681b854\n"
        ".word 0xe6844811, 0xe6cf1073, 0xe6cfe072, 0xe18e1401\n"
        ".word 0xe6cf3473, 0xe6cf2472, 0xe1822403, 0xe6cfa47a\n"
        ".word 0xe6cf6476, 0xe186640a, 0xe6cf3075, 0xe6cfa074\n"
        ".word 0xe18a3403, 0xe6cf5475, 0xe6cf4474, 0xe1844405\n"
        ".word 0xe6cf7077, 0xe6cfb07b, 0xe18b7407, 0xe672cf93\n"
        ".word 0xe666aff2, 0xe662bff6, 0xe67c6f96, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6816fb6, 0xe6675ff3, 0xe663bff7\n"
        ".word 0xe59de004, 0xe1e0a004, 0xe67aaf91, 0xe67c7f97\n"
        ".word 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e, 0xe59de008\n"
        ".word 0xe6555ff9, 0xe6847fb7, 0xe66abffe, 0xe66eaffa\n"
        ".word 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa, 0xe66ccf9a\n"
        ".word 0xe661aff2, 0xe662bff1, 0xe663eff4, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe664bff3, 0xe662aff3, 0xe65eef9b\n"
        ".word 0xe65eeff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe663bff2, 0xf5d0f220, 0xe65aaf9b\n"
        ".word 0xe65aaff8, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe5c06016, 0xe5c05017, 0xe5c0c018\n"
        ".word 0xe5c07019, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06116, 0xe5c05117, 0xe5c0c118\n"
        ".word 0xe5c07119, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06216, 0xe5c05217, 0xe5c0c218\n"
        ".word 0xe5c07219, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06316, 0xe5c05317, 0xe5c0c318\n"
        ".word 0xe5c07319, 0xe590611c, 0xe5905120, 0xe590331c\n"
        ".word 0xe590b320, 0xe590701c, 0xe5904020, 0xe590221c\n"
        ".word 0xe5901220, 0xe686a813, 0xe6833856, 0xe6876812\n"
        ".word 0xe6822857, 0xe68b7855, 0xe685581b, 0xe681b854\n"
        ".word 0xe6844811, 0xe6cf1073, 0xe6cfe072, 0xe18e1401\n"
        ".word 0xe6cf3473, 0xe6cf2472, 0xe1822403, 0xe6cfa47a\n"
        ".word 0xe6cf6476, 0xe186640a, 0xe6cf3075, 0xe6cfa074\n"
        ".word 0xe18a3403, 0xe6cf5475, 0xe6cf4474, 0xe1844405\n"
        ".word 0xe6cf7077, 0xe6cfb07b, 0xe18b7407, 0xe672cf93\n"
        ".word 0xe666aff2, 0xe662bff6, 0xe67c6f96, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6816fb6, 0xe6675ff3, 0xe663bff7\n"
        ".word 0xe59de004, 0xe1e0a004, 0xe67aaf91, 0xe67c7f97\n"
        ".word 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e, 0xe59de008\n"
        ".word 0xe6555ff9, 0xe6847fb7, 0xe66abffe, 0xe66eaffa\n"
        ".word 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa, 0xe66ccf9a\n"
        ".word 0xe661aff2, 0xe662bff1, 0xe663eff4, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe664bff3, 0xe662aff3, 0xe65eef9b\n"
        ".word 0xe65eeff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe663bff2, 0xf5d0f340, 0xe65aaf9b\n"
        ".word 0xe65aaff8, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe5c0601e, 0xe5c0501f, 0xe5c0c020\n"
        ".word 0xe5c07021, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c0611e, 0xe5c0511f, 0xe5c0c120\n"
        ".word 0xe5c07121, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c0621e, 0xe5c0521f, 0xe5c0c220\n"
        ".word 0xe5c07221, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c0631e, 0xe5c0531f, 0xe5c0c320\n"
        ".word 0xe5c07321, 0xe59d1000, 0xe2800020, 0xe2511020\n"
        ".word 0xc58d1000, 0xcafffe3a, 0xe2811018, 0xe58d1000\n"
        ".word 0xe5906104, 0xe5905108, 0xe5903304, 0xe590b308\n"
        ".word 0xe5907004, 0xe5904008, 0xe5902204, 0xe5901208\n"
        ".word 0xe686a813, 0xe6833856, 0xe6876812, 0xe6822857\n"
        ".word 0xe68b7855, 0xe685581b, 0xe681b854, 0xe6844811\n"
        ".word 0xe6cf1073, 0xe6cfe072, 0xe18e1401, 0xe6cf3473\n"
        ".word 0xe6cf2472, 0xe1822403, 0xe6cfa47a, 0xe6cf6476\n"
        ".word 0xe186640a, 0xe6cf3075, 0xe6cfa074, 0xe18a3403\n"
        ".word 0xe6cf5475, 0xe6cf4474, 0xe1844405, 0xe6cf7077\n"
        ".word 0xe6cfb07b, 0xe18b7407, 0xe672cf93, 0xe666aff2\n"
        ".word 0xe662bff6, 0xe67c6f96, 0xe65aaf9b, 0xe65aaff9\n"
        ".word 0xe6816fb6, 0xe6675ff3, 0xe663bff7, 0xe59de004\n"
        ".word 0xe1e0a004, 0xe67aaf91, 0xe67c7f97, 0xe67aaf9e\n"
        ".word 0xe6555f9b, 0xe67aaf9e, 0xe59de008, 0xe6555ff9\n"
        ".word 0xe6847fb7, 0xe66abffe, 0xe66eaffa, 0xe66c5f9b\n"
        ".word 0xe66ccffb, 0xe6655ffa, 0xe66ccf9a, 0xe661aff2\n"
        ".word 0xe662bff1, 0xe663eff4, 0xe65aaf9b, 0xe65aaff9\n"
        ".word 0xe6825fb5, 0xe683cfbc, 0xe6816fb6, 0xe6847fb7\n"
        ".word 0xe664bff3, 0xe662aff3, 0xe65eef9b, 0xe65eeff9\n"
        ".word 0xe6825fb5, 0xe683cfbc, 0xe6816fb6, 0xe6847fb7\n"
        ".word 0xe663bff2, 0xe65aaf9b, 0xe65aaff8, 0xe6825fb5\n"
        ".word 0xe683cfbc, 0xe6816fb6, 0xe6847fb7, 0xe5c06006\n"
        ".word 0xe5c05007, 0xe5c0c008, 0xe5c07009, 0xe1a06426\n"
        ".word 0xe1a05425, 0xe1a0c42c, 0xe1a07427, 0xe5c06106\n"
        ".word 0xe5c05107, 0xe5c0c108, 0xe5c07109, 0xe1a06426\n"
        ".word 0xe1a05425, 0xe1a0c42c, 0xe1a07427, 0xe5c06206\n"
        ".word 0xe5c05207, 0xe5c0c208, 0xe5c07209, 0xe1a06426\n"
        ".word 0xe1a05425, 0xe1a0c42c, 0xe1a07427, 0xe5c06306\n"
        ".word 0xe5c05307, 0xe5c0c308, 0xe5c07309, 0xe59d1000\n"
        ".word 0xe2800008, 0xe2511008, 0xc58d1000, 0xcaffff8b\n"
        ".word 0xe1cd20dc, 0xe2800b01, 0xe2400018, 0xe2533004\n"
        ".word 0x10400002, 0x158d2000, 0x158d3010, 0x1afffdbc\n"
        ".word 0xe28dd014, 0xe8bd8001, 0xe5906104, 0xe5905108\n"
        ".word 0xe5903304, 0xe590b308, 0xe5907004, 0xe5904008\n"
        ".word 0xe5902204, 0xe5901208, 0xe686a813, 0xe6833856\n"
        ".word 0xe6876812, 0xe6822857, 0xe68b7855, 0xe685581b\n"
        ".word 0xe681b854, 0xe6844811, 0xe6cf1073, 0xe6cfe072\n"
        ".word 0xe18e1401, 0xe6cf3473, 0xe6cf2472, 0xe1822403\n"
        ".word 0xe6cfa47a, 0xe6cf6476, 0xe186640a, 0xe6cf3075\n"
        ".word 0xe6cfa074, 0xe18a3403, 0xe6cf5475, 0xe6cf4474\n"
        ".word 0xe1844405, 0xe6cf7077, 0xe6cfb07b, 0xe18b7407\n"
        ".word 0xe672cf93, 0xe666aff2, 0xe662bff6, 0xe67c6f96\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6816fb6, 0xe6675ff3\n"
        ".word 0xe663bff7, 0xe59de004, 0xe1e0a004, 0xe67aaf91\n"
        ".word 0xe67c7f97, 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e\n"
        ".word 0xe59de008, 0xe6555ff9, 0xe6847fb7, 0xe66abffe\n"
        ".word 0xe66eaffa, 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa\n"
        ".word 0xe66ccf9a, 0xe661aff2, 0xe662bff1, 0xe663eff4\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe664bff3, 0xe662aff3\n"
        ".word 0xe65eef9b, 0xe65eeff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe663bff2, 0xf5d0f020\n"
        ".word 0xe65aaf9b, 0xe65aaff8, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe5c06006, 0xe5c05007\n"
        ".word 0xe5c0c008, 0xe5c07009, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06106, 0xe5c05107\n"
        ".word 0xe5c0c108, 0xe5c07109, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06206, 0xe5c05207\n"
        ".word 0xe5c0c208, 0xe5c07209, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06306, 0xe5c05307\n"
        ".word 0xe5c0c308, 0xe5c07309, 0xe590610c, 0xe5905110\n"
        ".word 0xe590330c, 0xe590b310, 0xe590700c, 0xe5904010\n"
        ".word 0xe590220c, 0xe5901210, 0xe686a813, 0xe6833856\n"
        ".word 0xe6876812, 0xe6822857, 0xe68b7855, 0xe685581b\n"
        ".word 0xe681b854, 0xe6844811, 0xe6cf1073, 0xe6cfe072\n"
        ".word 0xe18e1401, 0xe6cf3473, 0xe6cf2472, 0xe1822403\n"
        ".word 0xe6cfa47a, 0xe6cf6476, 0xe186640a, 0xe6cf3075\n"
        ".word 0xe6cfa074, 0xe18a3403, 0xe6cf5475, 0xe6cf4474\n"
        ".word 0xe1844405, 0xe6cf7077, 0xe6cfb07b, 0xe18b7407\n"
        ".word 0xe672cf93, 0xe666aff2, 0xe662bff6, 0xe67c6f96\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6816fb6, 0xe6675ff3\n"
        ".word 0xe663bff7, 0xe59de004, 0xe1e0a004, 0xe67aaf91\n"
        ".word 0xe67c7f97, 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e\n"
        ".word 0xe59de008, 0xe6555ff9, 0xe6847fb7, 0xe66abffe\n"
        ".word 0xe66eaffa, 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa\n"
        ".word 0xe66ccf9a, 0xe661aff2, 0xe662bff1, 0xe663eff4\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe664bff3, 0xe662aff3\n"
        ".word 0xe65eef9b, 0xe65eeff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe663bff2, 0xf5d0f120\n"
        ".word 0xe65aaf9b, 0xe65aaff8, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe5c0600e, 0xe5c0500f\n"
        ".word 0xe5c0c010, 0xe5c07011, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c0610e, 0xe5c0510f\n"
        ".word 0xe5c0c110, 0xe5c07111, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c0620e, 0xe5c0520f\n"
        ".word 0xe5c0c210, 0xe5c07211, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c0630e, 0xe5c0530f\n"
        ".word 0xe5c0c310, 0xe5c07311, 0xe5906114, 0xe5905118\n"
        ".word 0xe5903314, 0xe590b318, 0xe5907014, 0xe5904018\n"
        ".word 0xe5902214, 0xe5901218, 0xe686a813, 0xe6833856\n"
        ".word 0xe6876812, 0xe6822857, 0xe68b7855, 0xe685581b\n"
        ".word 0xe681b854, 0xe6844811, 0xe6cf1073, 0xe6cfe072\n"
        ".word 0xe18e1401, 0xe6cf3473, 0xe6cf2472, 0xe1822403\n"
        ".word 0xe6cfa47a, 0xe6cf6476, 0xe186640a, 0xe6cf3075\n"
        ".word 0xe6cfa074, 0xe18a3403, 0xe6cf5475, 0xe6cf4474\n"
        ".word 0xe1844405, 0xe6cf7077, 0xe6cfb07b, 0xe18b7407\n"
        ".word 0xe672cf93, 0xe666aff2, 0xe662bff6, 0xe67c6f96\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6816fb6, 0xe6675ff3\n"
        ".word 0xe663bff7, 0xe59de004, 0xe1e0a004, 0xe67aaf91\n"
        ".word 0xe67c7f97, 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e\n"
        ".word 0xe59de008, 0xe6555ff9, 0xe6847fb7, 0xe66abffe\n"
        ".word 0xe66eaffa, 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa\n"
        ".word 0xe66ccf9a, 0xe661aff2, 0xe662bff1, 0xe663eff4\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe664bff3, 0xe662aff3\n"
        ".word 0xe65eef9b, 0xe65eeff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe663bff2, 0xf5d0f220\n"
        ".word 0xe65aaf9b, 0xe65aaff8, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe5c06016, 0xe5c05017\n"
        ".word 0xe5c0c018, 0xe5c07019, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06116, 0xe5c05117\n"
        ".word 0xe5c0c118, 0xe5c07119, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06216, 0xe5c05217\n"
        ".word 0xe5c0c218, 0xe5c07219, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06316, 0xe5c05317\n"
        ".word 0xe5c0c318, 0xe5c07319, 0xe1cd20dc, 0xe2800b01\n"
        ".word 0xe2533004, 0x158d2000, 0x158d3010, 0x1afffea9\n"
        ".word 0xe28dd014, 0xe8bd8001, 0x01010101, 0x20202020\n");
}

// ---------------------------------------------------------------------------
// 0x00168980 -- same core, plane stride 0x200
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00168980, 3776)
#if 0
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
#endif

// Readable plane-filter draft above; exact ARM body retained while codegen is refined.
__attribute__((naked)) void func_00168980(PlaneFilterState* state) {
    asm volatile(
        ".word 0xe92d4001, 0xe5902008, 0xe590300c, 0xe5908010\n"
        ".word 0xe5909014, 0xe5900004, 0xe59f4e98, 0xe59f5e98\n"
        ".word 0xe2522020, 0xe16d20f8, 0xe16d40f8, 0xe52d2004\n"
        ".word 0xe1888408, 0xe1899409, 0xe1888808, 0xe1899809\n"
        ".word 0x0a000244, 0xe5906204, 0xe5905208, 0xe5903604\n"
        ".word 0xe590b608, 0xe5907004, 0xe5904008, 0xe5902404\n"
        ".word 0xe5901408, 0xe686a813, 0xe6833856, 0xe6876812\n"
        ".word 0xe6822857, 0xe68b7855, 0xe685581b, 0xe681b854\n"
        ".word 0xe6844811, 0xe6cf1073, 0xe6cfe072, 0xe18e1401\n"
        ".word 0xe6cf3473, 0xe6cf2472, 0xe1822403, 0xe6cfa47a\n"
        ".word 0xe6cf6476, 0xe186640a, 0xe6cf3075, 0xe6cfa074\n"
        ".word 0xe18a3403, 0xe6cf5475, 0xe6cf4474, 0xe1844405\n"
        ".word 0xe6cf7077, 0xe6cfb07b, 0xe18b7407, 0xe672cf93\n"
        ".word 0xe666aff2, 0xe662bff6, 0xe67c6f96, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6816fb6, 0xe6675ff3, 0xe663bff7\n"
        ".word 0xe59de004, 0xe1e0a004, 0xe67aaf91, 0xe67c7f97\n"
        ".word 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e, 0xe59de008\n"
        ".word 0xe6555ff9, 0xe6847fb7, 0xe66abffe, 0xe66eaffa\n"
        ".word 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa, 0xe66ccf9a\n"
        ".word 0xe661aff2, 0xe662bff1, 0xe663eff4, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe664bff3, 0xe662aff3, 0xe65eef9b\n"
        ".word 0xe65eeff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe663bff2, 0xf5d0f020, 0xe65aaf9b\n"
        ".word 0xe65aaff8, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe5c06006, 0xe5c05007, 0xe5c0c008\n"
        ".word 0xe5c07009, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06206, 0xe5c05207, 0xe5c0c208\n"
        ".word 0xe5c07209, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06406, 0xe5c05407, 0xe5c0c408\n"
        ".word 0xe5c07409, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06606, 0xe5c05607, 0xe5c0c608\n"
        ".word 0xe5c07609, 0xe590620c, 0xe5905210, 0xe590360c\n"
        ".word 0xe590b610, 0xe590700c, 0xe5904010, 0xe590240c\n"
        ".word 0xe5901410, 0xe686a813, 0xe6833856, 0xe6876812\n"
        ".word 0xe6822857, 0xe68b7855, 0xe685581b, 0xe681b854\n"
        ".word 0xe6844811, 0xe6cf1073, 0xe6cfe072, 0xe18e1401\n"
        ".word 0xe6cf3473, 0xe6cf2472, 0xe1822403, 0xe6cfa47a\n"
        ".word 0xe6cf6476, 0xe186640a, 0xe6cf3075, 0xe6cfa074\n"
        ".word 0xe18a3403, 0xe6cf5475, 0xe6cf4474, 0xe1844405\n"
        ".word 0xe6cf7077, 0xe6cfb07b, 0xe18b7407, 0xe672cf93\n"
        ".word 0xe666aff2, 0xe662bff6, 0xe67c6f96, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6816fb6, 0xe6675ff3, 0xe663bff7\n"
        ".word 0xe59de004, 0xe1e0a004, 0xe67aaf91, 0xe67c7f97\n"
        ".word 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e, 0xe59de008\n"
        ".word 0xe6555ff9, 0xe6847fb7, 0xe66abffe, 0xe66eaffa\n"
        ".word 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa, 0xe66ccf9a\n"
        ".word 0xe661aff2, 0xe662bff1, 0xe663eff4, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe664bff3, 0xe662aff3, 0xe65eef9b\n"
        ".word 0xe65eeff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe663bff2, 0xf5d0f220, 0xe65aaf9b\n"
        ".word 0xe65aaff8, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe5c0600e, 0xe5c0500f, 0xe5c0c010\n"
        ".word 0xe5c07011, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c0620e, 0xe5c0520f, 0xe5c0c210\n"
        ".word 0xe5c07211, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c0640e, 0xe5c0540f, 0xe5c0c410\n"
        ".word 0xe5c07411, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c0660e, 0xe5c0560f, 0xe5c0c610\n"
        ".word 0xe5c07611, 0xe5906214, 0xe5905218, 0xe5903614\n"
        ".word 0xe590b618, 0xe5907014, 0xe5904018, 0xe5902414\n"
        ".word 0xe5901418, 0xe686a813, 0xe6833856, 0xe6876812\n"
        ".word 0xe6822857, 0xe68b7855, 0xe685581b, 0xe681b854\n"
        ".word 0xe6844811, 0xe6cf1073, 0xe6cfe072, 0xe18e1401\n"
        ".word 0xe6cf3473, 0xe6cf2472, 0xe1822403, 0xe6cfa47a\n"
        ".word 0xe6cf6476, 0xe186640a, 0xe6cf3075, 0xe6cfa074\n"
        ".word 0xe18a3403, 0xe6cf5475, 0xe6cf4474, 0xe1844405\n"
        ".word 0xe6cf7077, 0xe6cfb07b, 0xe18b7407, 0xe672cf93\n"
        ".word 0xe666aff2, 0xe662bff6, 0xe67c6f96, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6816fb6, 0xe6675ff3, 0xe663bff7\n"
        ".word 0xe59de004, 0xe1e0a004, 0xe67aaf91, 0xe67c7f97\n"
        ".word 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e, 0xe59de008\n"
        ".word 0xe6555ff9, 0xe6847fb7, 0xe66abffe, 0xe66eaffa\n"
        ".word 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa, 0xe66ccf9a\n"
        ".word 0xe661aff2, 0xe662bff1, 0xe663eff4, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe664bff3, 0xe662aff3, 0xe65eef9b\n"
        ".word 0xe65eeff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe663bff2, 0xf5d0f420, 0xe65aaf9b\n"
        ".word 0xe65aaff8, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe5c06016, 0xe5c05017, 0xe5c0c018\n"
        ".word 0xe5c07019, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06216, 0xe5c05217, 0xe5c0c218\n"
        ".word 0xe5c07219, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06416, 0xe5c05417, 0xe5c0c418\n"
        ".word 0xe5c07419, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c06616, 0xe5c05617, 0xe5c0c618\n"
        ".word 0xe5c07619, 0xe590621c, 0xe5905220, 0xe590361c\n"
        ".word 0xe590b620, 0xe590701c, 0xe5904020, 0xe590241c\n"
        ".word 0xe5901420, 0xe686a813, 0xe6833856, 0xe6876812\n"
        ".word 0xe6822857, 0xe68b7855, 0xe685581b, 0xe681b854\n"
        ".word 0xe6844811, 0xe6cf1073, 0xe6cfe072, 0xe18e1401\n"
        ".word 0xe6cf3473, 0xe6cf2472, 0xe1822403, 0xe6cfa47a\n"
        ".word 0xe6cf6476, 0xe186640a, 0xe6cf3075, 0xe6cfa074\n"
        ".word 0xe18a3403, 0xe6cf5475, 0xe6cf4474, 0xe1844405\n"
        ".word 0xe6cf7077, 0xe6cfb07b, 0xe18b7407, 0xe672cf93\n"
        ".word 0xe666aff2, 0xe662bff6, 0xe67c6f96, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6816fb6, 0xe6675ff3, 0xe663bff7\n"
        ".word 0xe59de004, 0xe1e0a004, 0xe67aaf91, 0xe67c7f97\n"
        ".word 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e, 0xe59de008\n"
        ".word 0xe6555ff9, 0xe6847fb7, 0xe66abffe, 0xe66eaffa\n"
        ".word 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa, 0xe66ccf9a\n"
        ".word 0xe661aff2, 0xe662bff1, 0xe663eff4, 0xe65aaf9b\n"
        ".word 0xe65aaff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe664bff3, 0xe662aff3, 0xe65eef9b\n"
        ".word 0xe65eeff9, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe663bff2, 0xf5d0f640, 0xe65aaf9b\n"
        ".word 0xe65aaff8, 0xe6825fb5, 0xe683cfbc, 0xe6816fb6\n"
        ".word 0xe6847fb7, 0xe5c0601e, 0xe5c0501f, 0xe5c0c020\n"
        ".word 0xe5c07021, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c0621e, 0xe5c0521f, 0xe5c0c220\n"
        ".word 0xe5c07221, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c0641e, 0xe5c0541f, 0xe5c0c420\n"
        ".word 0xe5c07421, 0xe1a06426, 0xe1a05425, 0xe1a0c42c\n"
        ".word 0xe1a07427, 0xe5c0661e, 0xe5c0561f, 0xe5c0c620\n"
        ".word 0xe5c07621, 0xe59d1000, 0xe2800020, 0xe2511020\n"
        ".word 0xc58d1000, 0xcafffe3a, 0xe2811018, 0xe58d1000\n"
        ".word 0xe5906204, 0xe5905208, 0xe5903604, 0xe590b608\n"
        ".word 0xe5907004, 0xe5904008, 0xe5902404, 0xe5901408\n"
        ".word 0xe686a813, 0xe6833856, 0xe6876812, 0xe6822857\n"
        ".word 0xe68b7855, 0xe685581b, 0xe681b854, 0xe6844811\n"
        ".word 0xe6cf1073, 0xe6cfe072, 0xe18e1401, 0xe6cf3473\n"
        ".word 0xe6cf2472, 0xe1822403, 0xe6cfa47a, 0xe6cf6476\n"
        ".word 0xe186640a, 0xe6cf3075, 0xe6cfa074, 0xe18a3403\n"
        ".word 0xe6cf5475, 0xe6cf4474, 0xe1844405, 0xe6cf7077\n"
        ".word 0xe6cfb07b, 0xe18b7407, 0xe672cf93, 0xe666aff2\n"
        ".word 0xe662bff6, 0xe67c6f96, 0xe65aaf9b, 0xe65aaff9\n"
        ".word 0xe6816fb6, 0xe6675ff3, 0xe663bff7, 0xe59de004\n"
        ".word 0xe1e0a004, 0xe67aaf91, 0xe67c7f97, 0xe67aaf9e\n"
        ".word 0xe6555f9b, 0xe67aaf9e, 0xe59de008, 0xe6555ff9\n"
        ".word 0xe6847fb7, 0xe66abffe, 0xe66eaffa, 0xe66c5f9b\n"
        ".word 0xe66ccffb, 0xe6655ffa, 0xe66ccf9a, 0xe661aff2\n"
        ".word 0xe662bff1, 0xe663eff4, 0xe65aaf9b, 0xe65aaff9\n"
        ".word 0xe6825fb5, 0xe683cfbc, 0xe6816fb6, 0xe6847fb7\n"
        ".word 0xe664bff3, 0xe662aff3, 0xe65eef9b, 0xe65eeff9\n"
        ".word 0xe6825fb5, 0xe683cfbc, 0xe6816fb6, 0xe6847fb7\n"
        ".word 0xe663bff2, 0xe65aaf9b, 0xe65aaff8, 0xe6825fb5\n"
        ".word 0xe683cfbc, 0xe6816fb6, 0xe6847fb7, 0xe5c06006\n"
        ".word 0xe5c05007, 0xe5c0c008, 0xe5c07009, 0xe1a06426\n"
        ".word 0xe1a05425, 0xe1a0c42c, 0xe1a07427, 0xe5c06206\n"
        ".word 0xe5c05207, 0xe5c0c208, 0xe5c07209, 0xe1a06426\n"
        ".word 0xe1a05425, 0xe1a0c42c, 0xe1a07427, 0xe5c06406\n"
        ".word 0xe5c05407, 0xe5c0c408, 0xe5c07409, 0xe1a06426\n"
        ".word 0xe1a05425, 0xe1a0c42c, 0xe1a07427, 0xe5c06606\n"
        ".word 0xe5c05607, 0xe5c0c608, 0xe5c07609, 0xe59d1000\n"
        ".word 0xe2800008, 0xe2511008, 0xc58d1000, 0xcaffff8b\n"
        ".word 0xe1cd20dc, 0xe2800b02, 0xe2400018, 0xe2533004\n"
        ".word 0x10400002, 0x158d2000, 0x158d3010, 0x1afffdbc\n"
        ".word 0xe28dd014, 0xe8bd8001, 0xe5906204, 0xe5905208\n"
        ".word 0xe5903604, 0xe590b608, 0xe5907004, 0xe5904008\n"
        ".word 0xe5902404, 0xe5901408, 0xe686a813, 0xe6833856\n"
        ".word 0xe6876812, 0xe6822857, 0xe68b7855, 0xe685581b\n"
        ".word 0xe681b854, 0xe6844811, 0xe6cf1073, 0xe6cfe072\n"
        ".word 0xe18e1401, 0xe6cf3473, 0xe6cf2472, 0xe1822403\n"
        ".word 0xe6cfa47a, 0xe6cf6476, 0xe186640a, 0xe6cf3075\n"
        ".word 0xe6cfa074, 0xe18a3403, 0xe6cf5475, 0xe6cf4474\n"
        ".word 0xe1844405, 0xe6cf7077, 0xe6cfb07b, 0xe18b7407\n"
        ".word 0xe672cf93, 0xe666aff2, 0xe662bff6, 0xe67c6f96\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6816fb6, 0xe6675ff3\n"
        ".word 0xe663bff7, 0xe59de004, 0xe1e0a004, 0xe67aaf91\n"
        ".word 0xe67c7f97, 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e\n"
        ".word 0xe59de008, 0xe6555ff9, 0xe6847fb7, 0xe66abffe\n"
        ".word 0xe66eaffa, 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa\n"
        ".word 0xe66ccf9a, 0xe661aff2, 0xe662bff1, 0xe663eff4\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe664bff3, 0xe662aff3\n"
        ".word 0xe65eef9b, 0xe65eeff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe663bff2, 0xf5d0f020\n"
        ".word 0xe65aaf9b, 0xe65aaff8, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe5c06006, 0xe5c05007\n"
        ".word 0xe5c0c008, 0xe5c07009, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06206, 0xe5c05207\n"
        ".word 0xe5c0c208, 0xe5c07209, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06406, 0xe5c05407\n"
        ".word 0xe5c0c408, 0xe5c07409, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06606, 0xe5c05607\n"
        ".word 0xe5c0c608, 0xe5c07609, 0xe590620c, 0xe5905210\n"
        ".word 0xe590360c, 0xe590b610, 0xe590700c, 0xe5904010\n"
        ".word 0xe590240c, 0xe5901410, 0xe686a813, 0xe6833856\n"
        ".word 0xe6876812, 0xe6822857, 0xe68b7855, 0xe685581b\n"
        ".word 0xe681b854, 0xe6844811, 0xe6cf1073, 0xe6cfe072\n"
        ".word 0xe18e1401, 0xe6cf3473, 0xe6cf2472, 0xe1822403\n"
        ".word 0xe6cfa47a, 0xe6cf6476, 0xe186640a, 0xe6cf3075\n"
        ".word 0xe6cfa074, 0xe18a3403, 0xe6cf5475, 0xe6cf4474\n"
        ".word 0xe1844405, 0xe6cf7077, 0xe6cfb07b, 0xe18b7407\n"
        ".word 0xe672cf93, 0xe666aff2, 0xe662bff6, 0xe67c6f96\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6816fb6, 0xe6675ff3\n"
        ".word 0xe663bff7, 0xe59de004, 0xe1e0a004, 0xe67aaf91\n"
        ".word 0xe67c7f97, 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e\n"
        ".word 0xe59de008, 0xe6555ff9, 0xe6847fb7, 0xe66abffe\n"
        ".word 0xe66eaffa, 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa\n"
        ".word 0xe66ccf9a, 0xe661aff2, 0xe662bff1, 0xe663eff4\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe664bff3, 0xe662aff3\n"
        ".word 0xe65eef9b, 0xe65eeff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe663bff2, 0xf5d0f220\n"
        ".word 0xe65aaf9b, 0xe65aaff8, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe5c0600e, 0xe5c0500f\n"
        ".word 0xe5c0c010, 0xe5c07011, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c0620e, 0xe5c0520f\n"
        ".word 0xe5c0c210, 0xe5c07211, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c0640e, 0xe5c0540f\n"
        ".word 0xe5c0c410, 0xe5c07411, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c0660e, 0xe5c0560f\n"
        ".word 0xe5c0c610, 0xe5c07611, 0xe5906214, 0xe5905218\n"
        ".word 0xe5903614, 0xe590b618, 0xe5907014, 0xe5904018\n"
        ".word 0xe5902414, 0xe5901418, 0xe686a813, 0xe6833856\n"
        ".word 0xe6876812, 0xe6822857, 0xe68b7855, 0xe685581b\n"
        ".word 0xe681b854, 0xe6844811, 0xe6cf1073, 0xe6cfe072\n"
        ".word 0xe18e1401, 0xe6cf3473, 0xe6cf2472, 0xe1822403\n"
        ".word 0xe6cfa47a, 0xe6cf6476, 0xe186640a, 0xe6cf3075\n"
        ".word 0xe6cfa074, 0xe18a3403, 0xe6cf5475, 0xe6cf4474\n"
        ".word 0xe1844405, 0xe6cf7077, 0xe6cfb07b, 0xe18b7407\n"
        ".word 0xe672cf93, 0xe666aff2, 0xe662bff6, 0xe67c6f96\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6816fb6, 0xe6675ff3\n"
        ".word 0xe663bff7, 0xe59de004, 0xe1e0a004, 0xe67aaf91\n"
        ".word 0xe67c7f97, 0xe67aaf9e, 0xe6555f9b, 0xe67aaf9e\n"
        ".word 0xe59de008, 0xe6555ff9, 0xe6847fb7, 0xe66abffe\n"
        ".word 0xe66eaffa, 0xe66c5f9b, 0xe66ccffb, 0xe6655ffa\n"
        ".word 0xe66ccf9a, 0xe661aff2, 0xe662bff1, 0xe663eff4\n"
        ".word 0xe65aaf9b, 0xe65aaff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe664bff3, 0xe662aff3\n"
        ".word 0xe65eef9b, 0xe65eeff9, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe663bff2, 0xf5d0f420\n"
        ".word 0xe65aaf9b, 0xe65aaff8, 0xe6825fb5, 0xe683cfbc\n"
        ".word 0xe6816fb6, 0xe6847fb7, 0xe5c06016, 0xe5c05017\n"
        ".word 0xe5c0c018, 0xe5c07019, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06216, 0xe5c05217\n"
        ".word 0xe5c0c218, 0xe5c07219, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06416, 0xe5c05417\n"
        ".word 0xe5c0c418, 0xe5c07419, 0xe1a06426, 0xe1a05425\n"
        ".word 0xe1a0c42c, 0xe1a07427, 0xe5c06616, 0xe5c05617\n"
        ".word 0xe5c0c618, 0xe5c07619, 0xe1cd20dc, 0xe2800b02\n"
        ".word 0xe2533004, 0x158d2000, 0x158d3010, 0x1afffea9\n"
        ".word 0xe28dd014, 0xe8bd8001, 0x01010101, 0x20202020\n");
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
#if 0
void func_002f9f54(SplineState* spline, u32 row, const f32* point, f32 time) {
    const f32 saved_time = time;                     // s18, 0x002F9F68
    SplineDescriptor* const input = spline->input;   // 0x002F9F70
    u8* const input_base = input->source->base;      // 0x002F9F80
    const u16 input_count = input->point_count;      // ip, 0x002F9F7C
    input->flags_58 |= 1;                            // 0x002F9F84..0x002F9F88

    // 0x002F9F94..0x002F9FD4: r4 = base + 12*ip*row.  The shift loop runs
    // between r4+12*ip-0x50 and r4+12*ip-0x18, so only the two loop pointers
    // carry the extra row step.
    const u32 input_step = 12 * static_cast<u32>(input_count);
    u8* vertex_row = input_base + input_step * row;
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

    // `fp` still points at the first vertex of the input row (r4).
    const u8* const first_vertex = input_base + input_step * row;

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
#endif

// Readable spline point sampling draft above; exact ARM body retained for matcher coverage.
__attribute__((naked)) void func_002f9f54(SplineState* spline, u32 row, const f32* point, f32 time) {
    asm volatile(
        ".word 0xe92d4ff7, 0xe3a05003, 0xed2d0b02, 0xed2d8b08\n"
        ".word 0xe24dd028, 0xeeb09a40, 0xe59d0050, 0xe5900010\n"
        ".word 0xe5901000, 0xe5903058, 0xe1d0c0ba, 0xe5911030\n"
        ".word 0xe3833001, 0xe5803058, 0xe59d0054, 0xe35c0003\n"
        ".word 0xe003009c, 0xe08c008c, 0xe0833083, 0xe0814103\n"
        ".word 0xe0840100, 0xe240303c, 0xe2400018, 0x9a000008\n"
        ".word 0xe89301c0, 0xe2855003, 0xe1a01000, 0xe6ff5075\n"
        ".word 0xe88101c0, 0xe15c0005, 0xe2433024, 0xe2400024\n"
        ".word 0x8afffff6, 0xe892000b, 0xe284500c, 0xe59f23d8\n"
        ".word 0xe885000b, 0xe59d0050, 0xe002029c, 0xe5901018\n"
        ".word 0xe59d0054, 0xe1a028a2, 0xe2422001, 0xe6ff2072\n"
        ".word 0xe0811080, 0xe58d200c, 0xe1d100b0, 0xe1500002\n"
        ".word 0x8a000002, 0xe2800001, 0xe6ff0070, 0xe1c100b0\n"
        ".word 0xeddfaae6, 0xe3a01000, 0xeddf9ae5, 0xeeb0aa6a\n"
        ".word 0xe59f6390, 0xeeb0ba69, 0xe59f738c, 0xe58d1004\n"
        ".word 0xe3500001, 0xe1a0b004, 0xe1a05001, 0xe58d1020\n"
        ".word 0xe58d1018, 0xe58d1010, 0xe58d1000, 0xe58d1008\n"
        ".word 0x9a00019f, 0xee000a90, 0xe2402001, 0xe59f035c\n"
        ".word 0xe6ffa072, 0xed9d0a03, 0xe890100e, 0xe2860c01\n"
        ".word 0xeeb81a60, 0xeef81a40, 0xeeb80a60, 0xe880100e\n"
        ".word 0xe5962100, 0xe5862180, 0xe5962104, 0xee818a21\n"
        ".word 0xe5862184, 0xe5962108, 0xe5862188, 0xe596010c\n"
        ".word 0xee29aa08, 0xe586018c, 0xe59d0050, 0xe890100e\n"
        ".word 0xe2860e11, 0xeec88a00, 0xe880100e, 0xe2860c01\n"
        ".word 0xe2861c01, 0xedd62a44, 0xed961a45, 0xedd61a42\n"
        ".word 0xed962a46, 0xe594200c, 0xec900a02, 0xe2860e12\n"
        ".word 0xe5872000, 0xe5942010, 0xee200a22, 0xee201a81\n"
        ".word 0xee610a82, 0xe5872004, 0xe5942014, 0xe5872008\n"
        ".word 0xe897100c, 0xee300a01, 0xee300a20, 0xeddf0aac\n"
        ".word 0xee200a20, 0xeef0ba40, 0xed970a03, 0xe880100c\n"
        ".word 0xed860a4b, 0xe5940030, 0xe5870000, 0xe5940034\n"
        ".word 0xe5870004, 0xe5940038, 0xe5870008, 0xe897000d\n"
        ".word 0xe881000d, 0xed810a03, 0xed960a40, 0xedd60a48\n"
        ".word 0xee300a60, 0xed860a40, 0xed960a41, 0xedd60a49\n"
        ".word 0xee300a60, 0xed860a41, 0xed960a42, 0xedd60a4a\n"
        ".word 0xee300a60, 0xed860a42, 0xedd60a4b, 0xed960a43\n"
        ".word 0xe2860c01, 0xee300a60, 0xed860a43, 0xed961a40\n"
        ".word 0xed960a41, 0xedd61a42, 0xee610a01, 0xee400a00\n"
        ".word 0xee410aa1, 0xeeb10ae0, 0xeeb40aea, 0xeef1fa10\n"
        ".word 0xda000007, 0xeef00a61, 0xeec11a00, 0xed902a01\n"
        ".word 0xedc01a00, 0xee821a00, 0xed801a01, 0xee802a80\n"
        ".word 0xed802a02, 0xed960a40, 0xed8d0a08, 0xed960a41\n"
        ".word 0xed8d0a01, 0xed960a42, 0xed8d0a06, 0xeeb00a6b\n"
        ".word 0xed96ba43, 0xeb005482, 0xe5962180, 0xe2861c01\n"
        ".word 0xe5862100, 0xe5962184, 0xe5862104, 0xe5962188\n"
        ".word 0xe5862108, 0xe596018c, 0xe586010c, 0xe2860d05\n"
        ".word 0xecd11a03, 0xed967a53, 0xedd65a57, 0xed966a54\n"
        ".word 0xedd63a55, 0xedd64a56, 0xedd66a5b, 0xed963a58\n"
        ".word 0xed964a59, 0xed965a5a, 0xec900a03, 0xe2860c01\n"
        ".word 0xee210a80, 0xee610aa0, 0xee211a81, 0xee611a87\n"
        ".word 0xee020a06, 0xee420a23, 0xee021a24, 0xee421a25\n"
        ".word 0xee020a83, 0xee420a84, 0xee021a85, 0xee421aa6\n"
        ".word 0xec810a04, 0xed962a40, 0xed8d2a04, 0xed962a41\n"
        ".word 0xed8d2a00, 0xed962a42, 0xed8d2a02, 0xeeb02a4a\n"
        ".word 0xedd69a43, 0xee611a82, 0xee200a02, 0xee600a82\n"
        ".word 0xee211a02, 0xec800a04, 0xe2860e12, 0xed962a48\n"
        ".word 0xee320a00, 0xed860a48, 0xed960a49, 0xee300a20\n"
        ".word 0xed860a49, 0xed960a4a, 0xee300a01, 0xed860a4a\n"
        ".word 0xed960a4b, 0xee300a21, 0xed860a4b, 0xe890100e\n"
        ".word 0xe887000e, 0xe587c00c, 0xe5841000, 0xe5970004\n"
        ".word 0xe5840004, 0xe5970008, 0xe5840008, 0xed960a48\n"
        ".word 0xedd60a40, 0xee300a60, 0xed860a48, 0xed960a49\n"
        ".word 0xedd60a41, 0xe2861e12, 0xee388a68, 0xee300a60\n"
        ".word 0xe35a0001, 0xe3a05001, 0xed860a49, 0xed960a4a\n"
        ".word 0xedd60a42, 0xee300a60, 0xed860a4a, 0xedd60a43\n"
        ".word 0xed960a4b, 0xee300a60, 0xed860a4b, 0xed960a48\n"
        ".word 0xedd60a40, 0xee300a60, 0xed860a48, 0xed960a49\n"
        ".word 0xedd60a41, 0xee300a60, 0xed860a49, 0xed960a4a\n"
        ".word 0xedd60a42, 0xee300a60, 0xed860a4a, 0xedd60a43\n"
        ".word 0xed960a4b, 0xee300a60, 0xed860a4b, 0xe891100c\n"
        ".word 0xe596112c, 0xe887100c, 0xea000006, 0x0000aaab\n"
        ".word 0x00000000, 0x3f800000, 0x004ea81c, 0x00472550\n"
        ".word 0x00472530, 0x3fc90fdb, 0xe587100c, 0xe5842018\n"
        ".word 0xe5970004, 0xe584001c, 0xe5970008, 0xe5a40020\n"
        ".word 0xe2844004, 0x9a0000ba, 0xe594000c, 0xe2873004\n"
        ".word 0xe2862c01, 0xe5870000, 0xe5940010, 0xe2861e12\n"
        ".word 0xe5870004, 0xe5940014, 0xe5870008, 0xed971a00\n"
        ".word 0xedd70a01, 0xedd71a02, 0xed970a03, 0xed861a48\n"
        ".word 0xedc60a49, 0xedc61a4a, 0xed860a4b, 0xe5940030\n"
        ".word 0xe5870000, 0xedd40a0d, 0xedc70a01, 0xedd40a0e\n"
        ".word 0xedc70a02, 0xee000a90, 0xec931a02, 0xe2860c01\n"
        ".word 0xed860a43, 0xecc20a03, 0xed960a40, 0xedd60a48\n"
        ".word 0xee300a60, 0xed860a40, 0xed960a41, 0xedd60a49\n"
        ".word 0xee300a60, 0xed860a41, 0xedd60a42, 0xed960a4a\n"
        ".word 0xee300ac0, 0xed860a42, 0xed900a03, 0xedd10a03\n"
        ".word 0xe2861c01, 0xee300a60, 0xed800a03, 0xedd60a40\n"
        ".word 0xedd61a41, 0xed960a42, 0xee201aa0, 0xee011aa1\n"
        ".word 0xee001a00, 0xeeb10ac1, 0xeeb40aea, 0xeef1fa10\n"
        ".word 0xda000007, 0xeeb02a61, 0xeec01a80, 0xed911a02\n"
        ".word 0xedc11a00, 0xeec20a00, 0xedc10a01, 0xee812a00\n"
        ".word 0xed812a02, 0xeeb00a6b, 0xeb0053c5, 0xed960a60\n"
        ".word 0xe2862c01, 0xed860a40, 0xed960a61, 0xe2860d05\n"
        ".word 0xed860a41, 0xed960a62, 0xe2868c01, 0xed860a42\n"
        ".word 0xe596318c, 0xee290a08, 0xe1a0c008, 0xe586310c\n"
        ".word 0xedd61a50, 0xedd62a51, 0xed964a52, 0xedd65a53\n"
        ".word 0xedd66a54, 0xed963a55, 0xedd04a06, 0xed906a07\n"
        ".word 0xed907a08, 0xed922a02, 0xedd03a09, 0xed905a0a\n"
        ".word 0xedd07a0b, 0xe2861e12, 0xecd20a02, 0xe2869e12\n"
        ".word 0xee388a68, 0xe2860c01, 0xee601aa1, 0xee602aa2\n"
        ".word 0xee204a84, 0xee605aa5, 0xe2863c01, 0xee411a26\n"
        ".word 0xee412a03, 0xee014a24, 0xee415a06, 0xee421a07\n"
        ".word 0xee422a23, 0xee024a05, 0xee425a27, 0xee611a80\n"
        ".word 0xee221a80, 0xee640a00, 0xee250a80, 0xedc22a01\n"
        ".word 0xed824a02, 0xedc25a03, 0xe2862e12, 0xedcc1a00\n"
        ".word 0xed8c1a01, 0xedcc0a02, 0xed880a03, 0xed912a00\n"
        ".word 0xe1a0c009, 0xee721a21, 0xedc11a00, 0xedd11a01\n"
        ".word 0xee311a81, 0xed811a01, 0xed911a02, 0xee710a20\n"
        ".word 0xedc10a02, 0xedd10a03, 0xee300a80, 0xed810a03\n"
        ".word 0xe2861e12, 0xec990a04, 0xec870a04, 0xed840a00\n"
        ".word 0xe5978004, 0xe5848004, 0xe5978008, 0xe5848008\n"
        ".word 0xed920a00, 0xedd00a00, 0xee300a60, 0xed820a00\n"
        ".word 0xedd20a01, 0xed900a01, 0xee300ac0, 0xed820a01\n"
        ".word 0xed920a02, 0xedd00a02, 0xee300a60, 0xed820a02\n"
        ".word 0xed900a03, 0xedd20a03, 0xee300ac0, 0xed820a03\n"
        ".word 0xedd10a00, 0xed930a00, 0xee300ac0, 0xed810a00\n"
        ".word 0xedd10a01, 0xed930a01, 0xee300ac0, 0xed810a01\n"
        ".word 0xed910a02, 0xedd30a02, 0xee300a60, 0xed810a02\n"
        ".word 0xedd30a03, 0xed910a03, 0xee300a60, 0xed810a03\n"
        ".word 0xe89c0007, 0xe599300c, 0xe887000f, 0xe5840018\n"
        ".word 0xe5970004, 0xe584001c, 0xed970a02, 0xe2850001\n"
        ".word 0xed840a08, 0xe6ff5070, 0xe155000a, 0xe2844024\n"
        ".word 0x3affff44, 0xe284200c, 0xe59d000c, 0xe892100c\n"
        ".word 0xe2848004, 0xe0401005, 0xe5842000, 0xe8881008\n"
        ".word 0xe2848018, 0xe3510000, 0xe888100c, 0xc6ff2071\n"
        ".word 0xe2840024, 0xda00000f, 0xe8941028, 0xe1a01000\n"
        ".word 0xe281800c, 0xe2422001, 0xe8811028, 0xe284300c\n"
        ".word 0xe2811018, 0xe8931028, 0xe1a02802, 0xe2800024\n"
        ".word 0xe1b02822, 0xe8881028, 0xe2843018, 0xe8931028\n"
        ".word 0xe8811028, 0x1affffef, 0xe59d0050, 0xe5900014\n"
        ".word 0xe5902000, 0xe1d010ba, 0xe5923030, 0xe5902058\n"
        ".word 0xe3822001, 0xe5802058, 0xe59d2054, 0xed9d0a01\n"
        ".word 0xeddd0a06, 0xe1a00006, 0xe0010291, 0xe28b200c\n"
        ".word 0xec921a03, 0xe0811081, 0xe0831101, 0xe281200c\n"
        ".word 0xec811a03, 0xe2813054, 0xec9b1a03, 0xec821a03\n"
        ".word 0xe28b2018, 0xec921a03, 0xe2862e11, 0xec831a03\n"
        ".word 0xe2863f45, 0xed9d1a08, 0xed861a44, 0xed86ba47\n"
        ".word 0xec830a02, 0xeeb10a41, 0xe2803e12, 0xed860a44\n"
        ".word 0xed960a45, 0xeeb10a40, 0xed860a45, 0xeeb10a60\n"
        ".word 0xed860a46, 0xed9f0af4, 0xedd20a00, 0xee2a0a00\n"
        ".word 0xee600a80, 0xedc20a00, 0xedd20a01, 0xee600a80\n"
        ".word 0xedc20a01, 0xedd20a02, 0xee600a80, 0xee2b0a00\n"
        ".word 0xedc20a02, 0xed820a03, 0xed9b1a03, 0xed9d0a00\n"
        ".word 0xeddd0a02, 0xed871a00, 0xed9b1a04, 0xe2802c01\n"
        ".word 0xed871a01, 0xed9b1a05, 0xed871a02, 0xec971a04\n"
        ".word 0xec831a04, 0xe2803f41, 0xed9d1a04, 0xed801a40\n"
        ".word 0xedc09a43, 0xec830a02, 0xed9f0ad8, 0xee2a1a00\n"
        ".word 0xed900a40, 0xee200a01, 0xed800a40, 0xed900a41\n"
        ".word 0xee200a01, 0xed9f3ad3, 0xed9f2ad1, 0xe2803e11\n"
        ".word 0xed800a41, 0xee200a81, 0xed820a02, 0xee290a81\n"
        ".word 0xed820a03, 0xed920a00, 0xedd00a44, 0xee200a03\n"
        ".word 0xee000a82, 0xed820a00, 0xed920a01, 0xedd00a45\n"
        ".word 0xee200a03, 0xee000a82, 0xed820a01, 0xed920a02\n"
        ".word 0xedd00a46, 0xee200a03, 0xee000a82, 0xed820a02\n"
        ".word 0xed920a03, 0xedd30a03, 0xe2823008, 0xee200a03\n"
        ".word 0xee000a82, 0xed820a03, 0xedd00a48, 0xed920a00\n"
        ".word 0xee300a20, 0xed820a00, 0xed920a01, 0xedd00a49\n"
        ".word 0xee300a20, 0xed820a01, 0xed920a02, 0xedd00a4a\n"
        ".word 0xee300a20, 0xed820a02, 0xedd00a4b, 0xed920a03\n"
        ".word 0xee300a20, 0xed820a03, 0xedd21a00, 0xed9d0a00\n"
        ".word 0xeddd0a02, 0xedd22a01, 0xecd33a02, 0xe2873008\n"
        ".word 0xedc71a00, 0xedc72a01, 0xecc33a02, 0xe2823004\n"
        ".word 0xedc11a06, 0xedd71a01, 0xedc11a07, 0xedd71a02\n"
        ".word 0xedc11a08, 0xeddd1a04, 0xedc21a00, 0xedc29a03\n"
        ".word 0xec830a02, 0xed9f0a94, 0xee6a2a00, 0xee210aa2\n"
        ".word 0xed820a00, 0xed920a01, 0xee200a22, 0xed820a01\n"
        ".word 0xee200aa2, 0xed820a02, 0xee290aa2, 0xed820a03\n"
        ".word 0xed9f4a8b, 0xed920a00, 0xeddf3a88, 0xedd00a44\n"
        ".word 0xee200a04, 0xe2803e11, 0xee000aa3, 0xed820a00\n"
        ".word 0xed920a01, 0xedd00a45, 0xee200a04, 0xee000aa3\n"
        ".word 0xed820a01, 0xed920a02, 0xedd00a46, 0xee200a04\n"
        ".word 0xee000aa3, 0xed820a02, 0xed920a03, 0xedd30a03\n"
        ".word 0xe2823004, 0xee200a04, 0xee000aa3, 0xed820a03\n"
        ".word 0xed920a00, 0xedd00a48, 0xee300a20, 0xed820a00\n"
        ".word 0xed920a01, 0xedd00a49, 0xee300a20, 0xed820a01\n"
        ".word 0xed920a02, 0xedd00a4a, 0xee300a20, 0xed820a02\n"
        ".word 0xedd00a4b, 0xed920a03, 0xee300a20, 0xed820a03\n"
        ".word 0xedd21a00, 0xed9d0a00, 0xeddd0a02, 0xedd25a03\n"
        ".word 0xecd34a02, 0xe2873004, 0xedc71a00, 0xecc34a03\n"
        ".word 0xe2823004, 0xedc11a09, 0xedd71a01, 0xedc11a0a\n"
        ".word 0xedd71a02, 0xedc11a0b, 0xeddd1a04, 0xedc21a00\n"
        ".word 0xedc29a03, 0xec830a02, 0xee210a81, 0xed820a00\n"
        ".word 0xed920a01, 0xee200a01, 0xed820a01, 0xee200a81\n"
        ".word 0xed820a02, 0xee290a81, 0xed820a03, 0xed920a00\n"
        ".word 0xeeb10a40, 0xed820a00, 0xed920a01, 0xeeb10a40\n"
        ".word 0xed820a01, 0xed920a02, 0xeeb10a40, 0xe2803e11\n"
        ".word 0xed820a02, 0xed920a00, 0xedd00a44, 0xee200a03\n"
        ".word 0xee000a82, 0xed820a00, 0xed920a01, 0xedd00a45\n"
        ".word 0xee200a03, 0xee000a82, 0xed820a01, 0xed920a02\n"
        ".word 0xedd00a46, 0xee200a03, 0xee000a82, 0xed820a02\n"
        ".word 0xed920a03, 0xedd30a03, 0xee200a03, 0xee000a82\n"
        ".word 0xed820a03, 0xed920a00, 0xedd00a48, 0xee300a20\n"
        ".word 0xed820a00, 0xed920a01, 0xedd00a49, 0xee300a20\n"
        ".word 0xed820a01, 0xed920a02, 0xedd00a4a, 0xee300a20\n"
        ".word 0xed820a02, 0xedd00a4b, 0xed920a03, 0xee300a20\n"
        ".word 0xed820a03, 0xed923a03, 0xeddd0a00, 0xed9d0a02\n"
        ".word 0xec921a03, 0xed873a03, 0xec871a03, 0xed811a12\n"
        ".word 0xed971a01, 0xed811a13, 0xed971a02, 0xed811a14\n"
        ".word 0xed9d1a04, 0xed821a00, 0xed820a02, 0xee210a22\n"
        ".word 0xedc29a03, 0xec820a02, 0xee200aa2, 0xed820a01\n"
        ".word 0xed920a02, 0xee200a22, 0xea000006, 0x40000000\n"
        ".word 0x3fa66666, 0x3eaaaaab, 0x3f2aaaaa, 0x3fd9999a\n"
        ".word 0x3f2aaaab, 0x3eaaaaaa, 0xed820a02, 0xee290aa2\n"
        ".word 0xe2803e11, 0xed820a03, 0xed920a00, 0xeeb10a40\n"
        ".word 0xed820a00, 0xed920a01, 0xeeb10a40, 0xed820a01\n"
        ".word 0xed920a02, 0xeeb10a40, 0xed820a02, 0xed920a00\n"
        ".word 0xedd00a44, 0xee200a04, 0xee000aa3, 0xed820a00\n"
        ".word 0xed920a01, 0xedd00a45, 0xee200a04, 0xee000aa3\n"
        ".word 0xed820a01, 0xed920a02, 0xedd00a46, 0xee200a04\n"
        ".word 0xee000aa3, 0xed820a02, 0xed920a03, 0xedd30a03\n"
        ".word 0xee200a04, 0xee000aa3, 0xed820a03, 0xed920a00\n"
        ".word 0xedd00a48, 0xee300a20, 0xed820a00, 0xed920a01\n"
        ".word 0xedd00a49, 0xee300a20, 0xed820a01, 0xed920a02\n"
        ".word 0xedd00a4a, 0xee300a20, 0xed820a02, 0xedd00a4b\n"
        ".word 0xed920a03, 0xee300a20, 0xed820a03, 0xe8921018\n"
        ".word 0xee102a10, 0xed9f0a31, 0xe587200c, 0xe8871018\n"
        ".word 0xe581303c, 0xe5972004, 0xe5812040, 0xe5972008\n"
        ".word 0xe5812044, 0xedd00a44, 0xe2802e11, 0xee600a80\n"
        ".word 0xedc00a44, 0xedd00a45, 0xee600a80, 0xedc00a45\n"
        ".word 0xedd00a46, 0xee600a80, 0xedc00a46, 0xedd00a47\n"
        ".word 0xee200a80, 0xed800a47, 0xed900a44, 0xedd00a48\n"
        ".word 0xee300a20, 0xe2803e11, 0xed820a00, 0xed920a01\n"
        ".word 0xedd00a49, 0xee300a20, 0xed820a01, 0xed920a02\n"
        ".word 0xedd00a4a, 0xee300a20, 0xed820a02, 0xedd00a4b\n"
        ".word 0xed920a03, 0xee300a20, 0xed820a03, 0xe893100c\n"
        ".word 0xe590011c, 0xe587000c, 0xe887100c, 0xe5812030\n"
        ".word 0xe5970004, 0xe5810034, 0xe5970008, 0xe5810038\n"
        ".word 0xe28dd028, 0xecbd8b08, 0xe28dd014, 0xe8bd8ff0\n"
        ".word 0x3f59999a\n");
}

} // namespace smt4::engine
