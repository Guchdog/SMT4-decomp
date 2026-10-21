#include "engine/tex_convert.h"

#include <cstdint>
#include <cstring>

/**
 * Three 3DS texture-format conversion blocks.
 *
 * The blocks at 0x00170D70, 0x00177370 and 0x0017D970 are identical except for
 * the tile stride (0x400 / 0x100 / 0x200).  Every block starts with a
 * descriptor initialiser, then runs sixty leaf converters, then (for the first
 * two blocks) a VXS2 program header.  The initialiser builds two 32-bit words
 * per destination component from the permutation tables:
 *
 *   +0x78:  64 words = kTexTranspose64[i] | (kTexPack64[group][i] << shift-2)
 *   +0x178: 16 words = kTexTranspose16[i] | (kTexPack16[group][i] << shift)
 *
 * where `group` is kTexGroupIndex[format] (format % 6) and `shift` is
 * 8 + kTexGroupShift[format] (8 + format / 6).  The two word tables are what
 * the converter leaves use to perform the channel re-pack.
 *
 * The leaves process one 8x8 / 4x4 tile per iteration.  Each reads a 16-byte
 * (or 8/4/2/1-byte) block from the source, advances by `stride`, and writes the
 * converted block to the destination, also advancing by `stride`.  The
 * "sliding" leaves read the *next* row before writing the current one, so they
 * emit `(row[i] + row[i+1])` per component and consume one extra row.
 *
 * Channel halving is the repeated ARM idiom
 *
 *     and  rX, ip, rX, lsr #1        ; ip = 0x7F7F7F7F
 *
 * i.e. `(value >> 1) & 0x7F7F7F7F`, which halves each of four 8-bit channels
 * without bleeding between them.  The packing leaves then recombine bytes with
 * `add`/`lsl` sequences; those are reproduced verbatim below because the
 * register schedule (and therefore the intermediate truncation) is part of the
 * observable result.
 */

namespace smt4::engine {
namespace {

// ---------------------------------------------------------------------------
// Tile access helpers
//
// The 3DS tile data is not naturally aligned, so every access goes through
// memcpy (compiled to a single mov on x86).  The target is little-endian, like
// the ARM11 loads/stores in the listing.
// ---------------------------------------------------------------------------

inline u32 Ld32(const u8* p)
{
    u32 value;
    std::memcpy(&value, p, sizeof value);
    return value;
}

inline u16 Ld16(const u8* p)
{
    u16 value;
    std::memcpy(&value, p, sizeof value);
    return value;
}

inline u8 Ld8(const u8* p)
{
    return *p;
}

inline void St32(u8* p, u32 value)
{
    std::memcpy(p, &value, sizeof value);
}

inline void St16(u8* p, u16 value)
{
    std::memcpy(p, &value, sizeof value);
}

inline void St8(u8* p, u8 value)
{
    *p = value;
}

// 0x00170AD4: six 64-byte 8x8 index permutations (one per format group);
// the identical copies live at 0x001770D4 and 0x0017D6D4.
const u8 kTexPack64[6][64] = {
    {
    0x14, 0x13, 0x13, 0x19, 0x12, 0x19, 0x13, 0x18, 0x18, 0x13, 0x14, 0x12, 0x20, 0x12, 0x14, 0x13,
    0x13, 0x18, 0x18, 0x13, 0x13, 0x19, 0x12, 0x19, 0x12, 0x19, 0x12, 0x19, 0x13, 0x18, 0x18, 0x13,
    0x13, 0x18, 0x18, 0x13, 0x12, 0x20, 0x12, 0x14, 0x12, 0x20, 0x12, 0x18, 0x18, 0x13, 0x13, 0x18,
    0x18, 0x12, 0x19, 0x12, 0x19, 0x12, 0x13, 0x18, 0x18, 0x13, 0x12, 0x20, 0x12, 0x18, 0x18, 0x12,
    },
    {
    0x16, 0x15, 0x15, 0x1c, 0x13, 0x1c, 0x15, 0x1a, 0x1a, 0x15, 0x16, 0x13, 0x23, 0x13, 0x16, 0x15,
    0x15, 0x1a, 0x1a, 0x15, 0x15, 0x1c, 0x13, 0x1c, 0x13, 0x1c, 0x13, 0x1c, 0x15, 0x1a, 0x1a, 0x15,
    0x15, 0x1a, 0x1a, 0x15, 0x13, 0x23, 0x13, 0x16, 0x13, 0x23, 0x13, 0x1a, 0x1a, 0x15, 0x15, 0x1a,
    0x1a, 0x13, 0x1c, 0x13, 0x1c, 0x13, 0x15, 0x1a, 0x1a, 0x15, 0x13, 0x23, 0x13, 0x1a, 0x1a, 0x13,
    },
    {
    0x1a, 0x18, 0x18, 0x21, 0x17, 0x21, 0x18, 0x1f, 0x1f, 0x18, 0x1a, 0x17, 0x2a, 0x17, 0x1a, 0x18,
    0x18, 0x1f, 0x1f, 0x18, 0x18, 0x21, 0x17, 0x21, 0x17, 0x21, 0x17, 0x21, 0x18, 0x1f, 0x1f, 0x18,
    0x18, 0x1f, 0x1f, 0x18, 0x17, 0x2a, 0x17, 0x1a, 0x17, 0x2a, 0x17, 0x1f, 0x1f, 0x18, 0x18, 0x1f,
    0x1f, 0x17, 0x21, 0x17, 0x21, 0x17, 0x18, 0x1f, 0x1f, 0x18, 0x17, 0x2a, 0x17, 0x1f, 0x1f, 0x17,
    },
    {
    0x1c, 0x1a, 0x1a, 0x23, 0x19, 0x23, 0x1a, 0x21, 0x21, 0x1a, 0x1c, 0x19, 0x2d, 0x19, 0x1c, 0x1a,
    0x1a, 0x21, 0x21, 0x1a, 0x1a, 0x23, 0x19, 0x23, 0x19, 0x23, 0x19, 0x23, 0x1a, 0x21, 0x21, 0x1a,
    0x1a, 0x21, 0x21, 0x1a, 0x19, 0x2d, 0x19, 0x1c, 0x19, 0x2d, 0x19, 0x21, 0x21, 0x1a, 0x1a, 0x21,
    0x21, 0x19, 0x23, 0x19, 0x23, 0x19, 0x1a, 0x21, 0x21, 0x1a, 0x19, 0x2d, 0x19, 0x21, 0x21, 0x19,
    },
    {
    0x20, 0x1e, 0x1e, 0x28, 0x1c, 0x28, 0x1e, 0x26, 0x26, 0x1e, 0x20, 0x1c, 0x33, 0x1c, 0x20, 0x1e,
    0x1e, 0x26, 0x26, 0x1e, 0x1e, 0x28, 0x1c, 0x28, 0x1c, 0x28, 0x1c, 0x28, 0x1e, 0x26, 0x26, 0x1e,
    0x1e, 0x26, 0x26, 0x1e, 0x1c, 0x33, 0x1c, 0x20, 0x1c, 0x33, 0x1c, 0x26, 0x26, 0x1e, 0x1e, 0x26,
    0x26, 0x1c, 0x28, 0x1c, 0x28, 0x1c, 0x1e, 0x26, 0x26, 0x1e, 0x1c, 0x33, 0x1c, 0x26, 0x26, 0x1c,
    },
    {
    0x24, 0x22, 0x22, 0x2e, 0x20, 0x2e, 0x22, 0x2b, 0x2b, 0x22, 0x24, 0x20, 0x3a, 0x20, 0x24, 0x22,
    0x22, 0x2b, 0x2b, 0x22, 0x22, 0x2e, 0x20, 0x2e, 0x20, 0x2e, 0x20, 0x2e, 0x22, 0x2b, 0x2b, 0x22,
    0x22, 0x2b, 0x2b, 0x22, 0x20, 0x3a, 0x20, 0x24, 0x20, 0x3a, 0x20, 0x2b, 0x2b, 0x22, 0x22, 0x2b,
    0x2b, 0x20, 0x2e, 0x20, 0x2e, 0x20, 0x22, 0x2b, 0x2b, 0x22, 0x20, 0x3a, 0x20, 0x2b, 0x2b, 0x20,
    },
};

// 0x00170C54: 64-byte identity permutation applied after kTexPack64.
const u8 kTexTranspose64[64] = {
    0x00, 0x01, 0x08, 0x10, 0x09, 0x02, 0x03, 0x0a, 0x11, 0x18, 0x20, 0x19, 0x12, 0x0b, 0x04, 0x05,
    0x0c, 0x13, 0x1a, 0x21, 0x28, 0x30, 0x29, 0x22, 0x1b, 0x14, 0x0d, 0x06, 0x07, 0x0e, 0x15, 0x1c,
    0x23, 0x2a, 0x31, 0x38, 0x39, 0x32, 0x2b, 0x24, 0x1d, 0x16, 0x0f, 0x17, 0x1e, 0x25, 0x2c, 0x33,
    0x3a, 0x3b, 0x34, 0x2d, 0x26, 0x1f, 0x27, 0x2e, 0x35, 0x3c, 0x3d, 0x36, 0x2f, 0x37, 0x3e, 0x3f,
};

// 0x00170C94: six 16-byte 4x4 index permutations.
const u8 kTexPack16[6][16] = {
    {
    0x0a, 0x0d, 0x0d, 0x0a, 0x10, 0x0a, 0x0d, 0x0d,
    0x0d, 0x0d, 0x10, 0x0a, 0x10, 0x0d, 0x0d, 0x10,
    },
    {
    0x0b, 0x0e, 0x0e, 0x0b, 0x12, 0x0b, 0x0e, 0x0e,
    0x0e, 0x0e, 0x12, 0x0b, 0x12, 0x0e, 0x0e, 0x12,
    },
    {
    0x0d, 0x10, 0x10, 0x0d, 0x14, 0x0d, 0x10, 0x10,
    0x10, 0x10, 0x14, 0x0d, 0x14, 0x10, 0x10, 0x14,
    },
    {
    0x0e, 0x12, 0x12, 0x0e, 0x17, 0x0e, 0x12, 0x12,
    0x12, 0x12, 0x17, 0x0e, 0x17, 0x12, 0x12, 0x17,
    },
    {
    0x10, 0x14, 0x14, 0x10, 0x19, 0x10, 0x14, 0x14,
    0x14, 0x14, 0x19, 0x10, 0x19, 0x14, 0x14, 0x19,
    },
    {
    0x12, 0x17, 0x17, 0x12, 0x1d, 0x12, 0x17, 0x17,
    0x17, 0x17, 0x1d, 0x12, 0x1d, 0x17, 0x17, 0x1d,
    },
};

// 0x00170CF4: 16-byte identity permutation applied after kTexPack16.
const u8 kTexTranspose16[16] = {
    0x00, 0x04, 0x01, 0x02, 0x05, 0x08, 0x0c, 0x09,
    0x06, 0x03, 0x07, 0x0a, 0x0d, 0x0e, 0x0b, 0x0f,
};

// 0x00170D04: byte at +format is the packing group (format / 6).
const u8 kTexGroupShift[54] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02,
    0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x05, 0x05, 0x05, 0x05, 0x05, 0x05,
    0x06, 0x06, 0x06, 0x06, 0x06, 0x06, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08,
};

// 0x00170D3A: byte at +format is the permutation entry (format % 6).
const u8 kTexGroupIndex[54] = {
    0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05,
    0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05,
    0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05,
};

// Strides of the three blocks (the only immediate that differs between the
// three copies of every leaf below).
constexpr u32 kTexStride_170d70 = 0x400u;
constexpr u32 kTexStride_177370 = 0x100u;
constexpr u32 kTexStride_17d970 = 0x200u;

// ---------------------------------------------------------------------------
// Sixty converter leaves
//
// Addresses in the comments are the first block's; the second and third block
// copies live at the same offset from 0x00177370 / 0x0017D970.  Bodies were
// transcribed instruction-for-instruction: the r3..r8/sb/sl/fp/ip/lr locals
// mirror the ARM registers, `s` is r0, `d` is r1 and `n` is r2.
// ---------------------------------------------------------------------------

// 0x00170e20 (0x00177420 / 0x0017da20), 28 B: 16 B/tile; 16 B block read.
[[maybe_unused]] static void TexConv_00170e20(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0;
    do {
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        r7 = Ld32(s + 8);
        r8 = Ld32(s + 12);
        s += stride;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r7);
        St32(d + 12, r8);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00170e3c (0x0017743c / 0x0017da3c), 144 B: 16 B/tile; 16 B block read; 2x unrolled.
[[maybe_unused]] static void TexConv_00170e3c(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s + 0);
    r4 = Ld32(s + 4);
    r5 = Ld32(s + 8);
    r6 = Ld32(s + 12);
    s += stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    do {
        r7 = Ld32(s + 0);
        r8 = Ld32(s + 4);
        sb = Ld32(s + 8);
        sl = Ld32(s + 12);
        s += stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        r5 = r5 + sb;
        r6 = r6 + sl;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r5);
        St32(d + 12, r6);
        d += stride;
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        r5 = Ld32(s + 8);
        r6 = Ld32(s + 12);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        sb = sb + r5;
        sl = sl + r6;
        St32(d + 0, r7);
        St32(d + 4, r8);
        St32(d + 8, sb);
        St32(d + 12, sl);
        d += stride;
        n -= 2u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00170ecc (0x001774cc / 0x0017dacc), 88 B: 16 B/tile; 16 B block read; byte gather.
[[maybe_unused]] static void TexConv_00170ecc(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    do {
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        r7 = Ld32(s + 8);
        r8 = Ld32(s + 12);
        sb = Ld8(s + 16);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r3 >> 8);
        r3 = r3 + (r4 << 24);
        r4 = r4 + (r4 >> 8);
        r4 = r4 + (r7 << 24);
        r7 = r7 + (r7 >> 8);
        r7 = r7 + (r8 << 24);
        r8 = r8 + (r8 >> 8);
        r8 = r8 + (sb << 24);
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r7);
        St32(d + 12, r8);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00170f24 (0x00177524 / 0x0017db24), 308 B: 16 B/tile; 16 B block read; byte gather; 2x unrolled.
[[maybe_unused]] static void TexConv_00170f24(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0, lr = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s + 0);
    r4 = Ld32(s + 4);
    r5 = Ld32(s + 8);
    r6 = Ld32(s + 12);
    lr = Ld8(s + 16);
    s += stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    lr = ip & (lr >> 1);
    r3 = r3 + (r3 >> 8);
    r3 = r3 + (r4 << 24);
    r4 = r4 + (r4 >> 8);
    r4 = r4 + (r5 << 24);
    r5 = r5 + (r5 >> 8);
    r5 = r5 + (r6 << 24);
    r6 = r6 + (r6 >> 8);
    r6 = r6 + (lr << 24);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    do {
        r7 = Ld32(s + 0);
        r8 = Ld32(s + 4);
        sb = Ld32(s + 8);
        sl = Ld32(s + 12);
        lr = Ld8(s + 16);
        s += stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        lr = ip & (lr >> 1);
        r7 = r7 + (r7 >> 8);
        r7 = r7 + (r8 << 24);
        r8 = r8 + (r8 >> 8);
        r8 = r8 + (sb << 24);
        sb = sb + (sb >> 8);
        sb = sb + (sl << 24);
        sl = sl + (sl >> 8);
        sl = sl + (lr << 24);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        r5 = r5 + sb;
        r6 = r6 + sl;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r5);
        St32(d + 12, r6);
        d += stride;
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        r5 = Ld32(s + 8);
        r6 = Ld32(s + 12);
        lr = Ld8(s + 16);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        lr = ip & (lr >> 1);
        r3 = r3 + (r3 >> 8);
        r3 = r3 + (r4 << 24);
        r4 = r4 + (r4 >> 8);
        r4 = r4 + (r5 << 24);
        r5 = r5 + (r5 >> 8);
        r5 = r5 + (r6 << 24);
        r6 = r6 + (r6 >> 8);
        r6 = r6 + (lr << 24);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        sb = sb + r5;
        sl = sl + r6;
        St32(d + 0, r7);
        St32(d + 4, r8);
        St32(d + 8, sb);
        St32(d + 12, sl);
        d += stride;
        n -= 2u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00171058 (0x00177658 / 0x0017dc58), 68 B: 16 B/tile; 16 B block read; byte gather.
[[maybe_unused]] static void TexConv_00171058(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0;
    s = s - 1;
    do {
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        r7 = Ld32(s + 8);
        r8 = Ld32(s + 12);
        sb = Ld8(s + 16);
        s += stride;
        r3 = r3 >> 8;
        r3 = r3 + (r4 << 24);
        r4 = r4 >> 8;
        r4 = r4 + (r7 << 24);
        r7 = r7 >> 8;
        r7 = r7 + (r8 << 24);
        r8 = r8 >> 8;
        r8 = r8 + (sb << 24);
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r7);
        St32(d + 12, r8);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x0017109c (0x0017769c / 0x0017dc9c), 252 B: 16 B/tile; 16 B block read; byte gather; 2x unrolled.
[[maybe_unused]] static void TexConv_0017109c(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0, lr = 0;
    s = s - 1;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s + 0);
    r4 = Ld32(s + 4);
    r5 = Ld32(s + 8);
    r6 = Ld32(s + 12);
    lr = Ld8(s + 16);
    s += stride;
    r3 = r3 >> 8;
    r3 = r3 + (r4 << 24);
    r4 = r4 >> 8;
    r4 = r4 + (r5 << 24);
    r5 = r5 >> 8;
    r5 = r5 + (r6 << 24);
    r6 = r6 >> 8;
    r6 = r6 + (lr << 24);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    do {
        r7 = Ld32(s + 0);
        r8 = Ld32(s + 4);
        sb = Ld32(s + 8);
        sl = Ld32(s + 12);
        lr = Ld8(s + 16);
        s += stride;
        r7 = r7 >> 8;
        r7 = r7 + (r8 << 24);
        r8 = r8 >> 8;
        r8 = r8 + (sb << 24);
        sb = sb >> 8;
        sb = sb + (sl << 24);
        sl = sl >> 8;
        sl = sl + (lr << 24);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        r5 = r5 + sb;
        r6 = r6 + sl;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r5);
        St32(d + 12, r6);
        d += stride;
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        r5 = Ld32(s + 8);
        r6 = Ld32(s + 12);
        lr = Ld8(s + 16);
        s += stride;
        r3 = r3 >> 8;
        r3 = r3 + (r4 << 24);
        r4 = r4 >> 8;
        r4 = r4 + (r5 << 24);
        r5 = r5 >> 8;
        r5 = r5 + (r6 << 24);
        r6 = r6 >> 8;
        r6 = r6 + (lr << 24);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        sb = sb + r5;
        sl = sl + r6;
        St32(d + 0, r7);
        St32(d + 4, r8);
        St32(d + 8, sb);
        St32(d + 12, sl);
        d += stride;
        n -= 2u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00171198 (0x00177798 / 0x0017dd98), 124 B: 16 B/tile; 16 B block read; halfword gather.
[[maybe_unused]] static void TexConv_00171198(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s - 1;
    do {
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        r7 = Ld32(s + 8);
        r8 = Ld32(s + 12);
        sb = Ld16(s + 16);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 >> 16;
        sl = sl + (r4 << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (r4 << 24);
        sl = r4 >> 16;
        sl = sl + (r7 << 16);
        sl = sl + (r4 >> 8);
        r4 = sl + (r7 << 24);
        sl = r7 >> 16;
        sl = sl + (r8 << 16);
        sl = sl + (r7 >> 8);
        r7 = sl + (r8 << 24);
        sl = r8 >> 16;
        sl = sl + (sb << 16);
        sl = sl + (r8 >> 8);
        r8 = sl + (sb << 24);
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r7);
        St32(d + 12, r8);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00171214 (0x00177814 / 0x0017de14), 408 B: 16 B/tile; 16 B block read; halfword gather; 2x unrolled.
[[maybe_unused]] static void TexConv_00171214(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, fp = 0, ip = 0, lr = 0;
    ip = 0x7f7f7f7fU;
    s = s - 1;
    r3 = Ld32(s + 0);
    r4 = Ld32(s + 4);
    r5 = Ld32(s + 8);
    r6 = Ld32(s + 12);
    lr = Ld16(s + 16);
    s += stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    lr = ip & (lr >> 1);
    fp = r3 >> 16;
    fp = fp + (r4 << 16);
    fp = fp + (r3 >> 8);
    r3 = fp + (r4 << 24);
    fp = r4 >> 16;
    fp = fp + (r5 << 16);
    fp = fp + (r4 >> 8);
    r4 = fp + (r5 << 24);
    fp = r5 >> 16;
    fp = fp + (r6 << 16);
    fp = fp + (r5 >> 8);
    r5 = fp + (r6 << 24);
    fp = r6 >> 16;
    fp = fp + (lr << 16);
    fp = fp + (r6 >> 8);
    r6 = fp + (lr << 24);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    do {
        r7 = Ld32(s + 0);
        r8 = Ld32(s + 4);
        sb = Ld32(s + 8);
        sl = Ld32(s + 12);
        lr = Ld16(s + 16);
        s += stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        lr = ip & (lr >> 1);
        fp = r7 >> 16;
        fp = fp + (r8 << 16);
        fp = fp + (r7 >> 8);
        r7 = fp + (r8 << 24);
        fp = r8 >> 16;
        fp = fp + (sb << 16);
        fp = fp + (r8 >> 8);
        r8 = fp + (sb << 24);
        fp = sb >> 16;
        fp = fp + (sl << 16);
        fp = fp + (sb >> 8);
        sb = fp + (sl << 24);
        fp = sl >> 16;
        fp = fp + (lr << 16);
        fp = fp + (sl >> 8);
        sl = fp + (lr << 24);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        r5 = r5 + sb;
        r6 = r6 + sl;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r5);
        St32(d + 12, r6);
        d += stride;
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        r5 = Ld32(s + 8);
        r6 = Ld32(s + 12);
        lr = Ld16(s + 16);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        lr = ip & (lr >> 1);
        fp = r3 >> 16;
        fp = fp + (r4 << 16);
        fp = fp + (r3 >> 8);
        r3 = fp + (r4 << 24);
        fp = r4 >> 16;
        fp = fp + (r5 << 16);
        fp = fp + (r4 >> 8);
        r4 = fp + (r5 << 24);
        fp = r5 >> 16;
        fp = fp + (r6 << 16);
        fp = fp + (r5 >> 8);
        r5 = fp + (r6 << 24);
        fp = r6 >> 16;
        fp = fp + (lr << 16);
        fp = fp + (r6 >> 8);
        r6 = fp + (lr << 24);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        sb = sb + r5;
        sl = sl + r6;
        St32(d + 0, r7);
        St32(d + 4, r8);
        St32(d + 8, sb);
        St32(d + 12, sl);
        d += stride;
        n -= 2u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x001713ac (0x001779ac / 0x0017dfac), 68 B: 16 B/tile; 12 B block read; halfword gather.
[[maybe_unused]] static void TexConv_001713ac(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0;
    s = s + 2;
    do {
        r3 = Ld16(s - 2);
        r4 = Ld32(s + 0);
        r7 = Ld32(s + 4);
        r8 = Ld32(s + 8);
        sb = Ld16(s + 12);
        s += stride;
        r3 = r3 + (r4 << 16);
        r4 = r4 >> 16;
        r4 = r4 + (r7 << 16);
        r7 = r7 >> 16;
        r7 = r7 + (r8 << 16);
        r8 = r8 >> 16;
        r8 = r8 + (sb << 16);
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r7);
        St32(d + 12, r8);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x001713f0 (0x001779f0 / 0x0017dff0), 252 B: 16 B/tile; 12 B block read; halfword gather; 2x unrolled.
[[maybe_unused]] static void TexConv_001713f0(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0, lr = 0;
    ip = 0x7f7f7f7fU;
    s = s + 2;
    r3 = Ld16(s - 2);
    r4 = Ld32(s + 0);
    r5 = Ld32(s + 4);
    r6 = Ld32(s + 8);
    lr = Ld16(s + 12);
    s += stride;
    r3 = r3 + (r4 << 16);
    r4 = r4 >> 16;
    r4 = r4 + (r5 << 16);
    r5 = r5 >> 16;
    r5 = r5 + (r6 << 16);
    r6 = r6 >> 16;
    r6 = r6 + (lr << 16);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    do {
        r7 = Ld16(s - 2);
        r8 = Ld32(s + 0);
        sb = Ld32(s + 4);
        sl = Ld32(s + 8);
        lr = Ld16(s + 12);
        s += stride;
        r7 = r7 + (r8 << 16);
        r8 = r8 >> 16;
        r8 = r8 + (sb << 16);
        sb = sb >> 16;
        sb = sb + (sl << 16);
        sl = sl >> 16;
        sl = sl + (lr << 16);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        r5 = r5 + sb;
        r6 = r6 + sl;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r5);
        St32(d + 12, r6);
        d += stride;
        r3 = Ld16(s - 2);
        r4 = Ld32(s + 0);
        r5 = Ld32(s + 4);
        r6 = Ld32(s + 8);
        lr = Ld16(s + 12);
        s += stride;
        r3 = r3 + (r4 << 16);
        r4 = r4 >> 16;
        r4 = r4 + (r5 << 16);
        r5 = r5 >> 16;
        r5 = r5 + (r6 << 16);
        r6 = r6 >> 16;
        r6 = r6 + (lr << 16);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        sb = sb + r5;
        sl = sl + r6;
        St32(d + 0, r7);
        St32(d + 4, r8);
        St32(d + 8, sb);
        St32(d + 12, sl);
        d += stride;
        n -= 2u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x001714ec (0x00177aec / 0x0017e0ec), 120 B: 16 B/tile; 16 B block read; halfword gather.
[[maybe_unused]] static void TexConv_001714ec(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 2;
    do {
        r3 = Ld16(s - 2);
        r4 = Ld32(s + 0);
        r7 = Ld32(s + 4);
        r8 = Ld32(s + 8);
        sb = Ld32(s + 12);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 + (r4 << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (r4 << 8);
        r4 = r4 >> 16;
        sl = r4 + (r7 << 16);
        sl = sl + (r4 >> 8);
        r4 = sl + (r7 << 8);
        r7 = r7 >> 16;
        sl = r7 + (r8 << 16);
        sl = sl + (r7 >> 8);
        r7 = sl + (r8 << 8);
        r8 = r8 >> 16;
        sl = r8 + (sb << 16);
        sl = sl + (r8 >> 8);
        r8 = sl + (sb << 8);
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r7);
        St32(d + 12, r8);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00171564 (0x00177b64 / 0x0017e164), 396 B: 16 B/tile; 16 B block read; halfword gather; 2x unrolled.
[[maybe_unused]] static void TexConv_00171564(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, fp = 0, ip = 0, lr = 0;
    ip = 0x7f7f7f7fU;
    s = s + 2;
    r3 = Ld16(s - 2);
    r4 = Ld32(s + 0);
    r5 = Ld32(s + 4);
    r6 = Ld32(s + 8);
    lr = Ld32(s + 12);
    s += stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    lr = ip & (lr >> 1);
    fp = r3 + (r4 << 16);
    fp = fp + (r3 >> 8);
    r3 = fp + (r4 << 8);
    r4 = r4 >> 16;
    fp = r4 + (r5 << 16);
    fp = fp + (r4 >> 8);
    r4 = fp + (r5 << 8);
    r5 = r5 >> 16;
    fp = r5 + (r6 << 16);
    fp = fp + (r5 >> 8);
    r5 = fp + (r6 << 8);
    r6 = r6 >> 16;
    fp = r6 + (lr << 16);
    fp = fp + (r6 >> 8);
    r6 = fp + (lr << 8);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    do {
        r7 = Ld16(s - 2);
        r8 = Ld32(s + 0);
        sb = Ld32(s + 4);
        sl = Ld32(s + 8);
        lr = Ld32(s + 12);
        s += stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        lr = ip & (lr >> 1);
        fp = r7 + (r8 << 16);
        fp = fp + (r7 >> 8);
        r7 = fp + (r8 << 8);
        r8 = r8 >> 16;
        fp = r8 + (sb << 16);
        fp = fp + (r8 >> 8);
        r8 = fp + (sb << 8);
        sb = sb >> 16;
        fp = sb + (sl << 16);
        fp = fp + (sb >> 8);
        sb = fp + (sl << 8);
        sl = sl >> 16;
        fp = sl + (lr << 16);
        fp = fp + (sl >> 8);
        sl = fp + (lr << 8);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        r5 = r5 + sb;
        r6 = r6 + sl;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r5);
        St32(d + 12, r6);
        d += stride;
        r3 = Ld16(s - 2);
        r4 = Ld32(s + 0);
        r5 = Ld32(s + 4);
        r6 = Ld32(s + 8);
        lr = Ld32(s + 12);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        lr = ip & (lr >> 1);
        fp = r3 + (r4 << 16);
        fp = fp + (r3 >> 8);
        r3 = fp + (r4 << 8);
        r4 = r4 >> 16;
        fp = r4 + (r5 << 16);
        fp = fp + (r4 >> 8);
        r4 = fp + (r5 << 8);
        r5 = r5 >> 16;
        fp = r5 + (r6 << 16);
        fp = fp + (r5 >> 8);
        r5 = fp + (r6 << 8);
        r6 = r6 >> 16;
        fp = r6 + (lr << 16);
        fp = fp + (r6 >> 8);
        r6 = fp + (lr << 8);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        sb = sb + r5;
        sl = sl + r6;
        St32(d + 0, r7);
        St32(d + 4, r8);
        St32(d + 8, sb);
        St32(d + 12, sl);
        d += stride;
        n -= 2u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x001716f0 (0x00177cf0 / 0x0017e2f0), 64 B: 16 B/tile; 16 B block read; byte gather.
[[maybe_unused]] static void TexConv_001716f0(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0;
    s = s + 1;
    do {
        r3 = Ld8(s - 1);
        r4 = Ld32(s + 0);
        r7 = Ld32(s + 4);
        r8 = Ld32(s + 8);
        sb = Ld32(s + 12);
        s += stride;
        r3 = r3 + (r4 << 8);
        r4 = r4 >> 24;
        r4 = r4 + (r7 << 8);
        r7 = r7 >> 24;
        r7 = r7 + (r8 << 8);
        r8 = r8 >> 24;
        r8 = r8 + (sb << 8);
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r7);
        St32(d + 12, r8);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00171730 (0x00177d30 / 0x0017e330), 240 B: 16 B/tile; 16 B block read; byte gather; 2x unrolled.
[[maybe_unused]] static void TexConv_00171730(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0, lr = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    r3 = Ld8(s - 1);
    r4 = Ld32(s + 0);
    r5 = Ld32(s + 4);
    r6 = Ld32(s + 8);
    lr = Ld32(s + 12);
    s += stride;
    r3 = r3 + (r4 << 8);
    r4 = r4 >> 24;
    r4 = r4 + (r5 << 8);
    r5 = r5 >> 24;
    r5 = r5 + (r6 << 8);
    r6 = r6 >> 24;
    r6 = r6 + (lr << 8);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    do {
        r7 = Ld8(s - 1);
        r8 = Ld32(s + 0);
        sb = Ld32(s + 4);
        sl = Ld32(s + 8);
        lr = Ld32(s + 12);
        s += stride;
        r7 = r7 + (r8 << 8);
        r8 = r8 >> 24;
        r8 = r8 + (sb << 8);
        sb = sb >> 24;
        sb = sb + (sl << 8);
        sl = sl >> 24;
        sl = sl + (lr << 8);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        r5 = r5 + sb;
        r6 = r6 + sl;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r5);
        St32(d + 12, r6);
        d += stride;
        r3 = Ld8(s - 1);
        r4 = Ld32(s + 0);
        r5 = Ld32(s + 4);
        r6 = Ld32(s + 8);
        lr = Ld32(s + 12);
        s += stride;
        r3 = r3 + (r4 << 8);
        r4 = r4 >> 24;
        r4 = r4 + (r5 << 8);
        r5 = r5 >> 24;
        r5 = r5 + (r6 << 8);
        r6 = r6 >> 24;
        r6 = r6 + (lr << 8);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        sb = sb + r5;
        sl = sl + r6;
        St32(d + 0, r7);
        St32(d + 4, r8);
        St32(d + 8, sb);
        St32(d + 12, sl);
        d += stride;
        n -= 2u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00171820 (0x00177e20 / 0x0017e420), 92 B: 16 B/tile; 16 B block read; byte gather.
[[maybe_unused]] static void TexConv_00171820(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    do {
        r3 = Ld8(s - 1);
        r4 = Ld32(s + 0);
        r7 = Ld32(s + 4);
        r8 = Ld32(s + 8);
        sb = Ld32(s + 12);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r4 << 8);
        r3 = r3 + r4;
        r4 = r7 + (r4 >> 24);
        r4 = r4 + (r7 << 8);
        r7 = r8 + (r7 >> 24);
        r7 = r7 + (r8 << 8);
        r8 = sb + (r8 >> 24);
        r8 = r8 + (sb << 8);
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r7);
        St32(d + 12, r8);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x0017187c (0x00177e7c / 0x0017e47c), 312 B: 16 B/tile; 16 B block read; byte gather; 2x unrolled.
[[maybe_unused]] static void TexConv_0017187c(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0, lr = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    r3 = Ld8(s - 1);
    r4 = Ld32(s + 0);
    r5 = Ld32(s + 4);
    r6 = Ld32(s + 8);
    lr = Ld32(s + 12);
    s += stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    lr = ip & (lr >> 1);
    r3 = r3 + (r4 << 8);
    r3 = r3 + r4;
    r4 = r5 + (r4 >> 24);
    r4 = r4 + (r5 << 8);
    r5 = r6 + (r5 >> 24);
    r5 = r5 + (r6 << 8);
    r6 = lr + (r6 >> 24);
    r6 = r6 + (lr << 8);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    do {
        r7 = Ld8(s - 1);
        r8 = Ld32(s + 0);
        sb = Ld32(s + 4);
        sl = Ld32(s + 8);
        lr = Ld32(s + 12);
        s += stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        lr = ip & (lr >> 1);
        r7 = r7 + (r8 << 8);
        r7 = r7 + r8;
        r8 = sb + (r8 >> 24);
        r8 = r8 + (sb << 8);
        sb = sl + (sb >> 24);
        sb = sb + (sl << 8);
        sl = lr + (sl >> 24);
        sl = sl + (lr << 8);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        r5 = r5 + sb;
        r6 = r6 + sl;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r5);
        St32(d + 12, r6);
        d += stride;
        r3 = Ld8(s - 1);
        r4 = Ld32(s + 0);
        r5 = Ld32(s + 4);
        r6 = Ld32(s + 8);
        lr = Ld32(s + 12);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        lr = ip & (lr >> 1);
        r3 = r3 + (r4 << 8);
        r3 = r3 + r4;
        r4 = r5 + (r4 >> 24);
        r4 = r4 + (r5 << 8);
        r5 = r6 + (r5 >> 24);
        r5 = r5 + (r6 << 8);
        r6 = lr + (r6 >> 24);
        r6 = r6 + (lr << 8);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        sb = sb + r5;
        sl = sl + r6;
        St32(d + 0, r7);
        St32(d + 4, r8);
        St32(d + 8, sb);
        St32(d + 12, sl);
        d += stride;
        n -= 2u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x001719b8 (0x00177fb8 / 0x0017e5b8), 28 B: 8 B/tile; 8 B block read.
[[maybe_unused]] static void TexConv_001719b8(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0;
    do {
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        s += stride;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x001719d4 (0x00177fd4 / 0x0017e5d4), 104 B: 8 B/tile; 8 B block read; sliding two-row average.
[[maybe_unused]] static void TexConv_001719d4(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s + 0);
    r4 = Ld32(s + 4);
    s += stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    do {
        r7 = Ld32(s + 0);
        r8 = Ld32(s + 4);
        s += stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        St32(d + 0, r7);
        St32(d + 4, r8);
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x00171a3c (0x0017803c / 0x0017e63c), 64 B: 8 B/tile; 8 B block read; byte gather.
[[maybe_unused]] static void TexConv_00171a3c(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    do {
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        sb = Ld8(s + 8);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r3 >> 8);
        r3 = r3 + (r4 << 24);
        r4 = r4 + (r4 >> 8);
        r4 = r4 + (sb << 24);
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00171a7c (0x0017807c / 0x0017e67c), 200 B: 8 B/tile; 8 B block read; byte gather; sliding two-row average.
[[maybe_unused]] static void TexConv_00171a7c(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s + 0);
    r4 = Ld32(s + 4);
    sb = Ld8(s + 8);
    s += stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    sb = ip & (sb >> 1);
    r3 = r3 + (r3 >> 8);
    r3 = r3 + (r4 << 24);
    r4 = r4 + (r4 >> 8);
    r4 = r4 + (sb << 24);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    do {
        r7 = Ld32(s + 0);
        r8 = Ld32(s + 4);
        sb = Ld8(s + 8);
        s += stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        r7 = r7 + (r7 >> 8);
        r7 = r7 + (r8 << 24);
        r8 = r8 + (r8 >> 8);
        r8 = r8 + (sb << 24);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        sb = Ld8(s + 8);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r3 >> 8);
        r3 = r3 + (r4 << 24);
        r4 = r4 + (r4 >> 8);
        r4 = r4 + (sb << 24);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        St32(d + 0, r7);
        St32(d + 4, r8);
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x00171b44 (0x00178144 / 0x0017e744), 52 B: 8 B/tile; 8 B block read; byte gather.
[[maybe_unused]] static void TexConv_00171b44(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, sb = 0;
    s = s - 1;
    do {
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        sb = Ld8(s + 8);
        s += stride;
        r3 = r3 >> 8;
        r3 = r3 + (r4 << 24);
        r4 = r4 >> 8;
        r4 = r4 + (sb << 24);
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00171b78 (0x00178178 / 0x0017e778), 168 B: 8 B/tile; 8 B block read; byte gather; sliding two-row average.
[[maybe_unused]] static void TexConv_00171b78(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, ip = 0;
    s = s - 1;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s + 0);
    r4 = Ld32(s + 4);
    sb = Ld8(s + 8);
    s += stride;
    r3 = r3 >> 8;
    r3 = r3 + (r4 << 24);
    r4 = r4 >> 8;
    r4 = r4 + (sb << 24);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    do {
        r7 = Ld32(s + 0);
        r8 = Ld32(s + 4);
        sb = Ld8(s + 8);
        s += stride;
        r7 = r7 >> 8;
        r7 = r7 + (r8 << 24);
        r8 = r8 >> 8;
        r8 = r8 + (sb << 24);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        sb = Ld8(s + 8);
        s += stride;
        r3 = r3 >> 8;
        r3 = r3 + (r4 << 24);
        r4 = r4 >> 8;
        r4 = r4 + (sb << 24);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        St32(d + 0, r7);
        St32(d + 4, r8);
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x00171c20 (0x00178220 / 0x0017e820), 84 B: 8 B/tile; 8 B block read; halfword gather.
[[maybe_unused]] static void TexConv_00171c20(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s - 1;
    do {
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        sb = Ld16(s + 8);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 >> 16;
        sl = sl + (r4 << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (r4 << 24);
        sl = r4 >> 16;
        sl = sl + (sb << 16);
        sl = sl + (r4 >> 8);
        r4 = sl + (sb << 24);
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00171c74 (0x00178274 / 0x0017e874), 252 B: 8 B/tile; 8 B block read; halfword gather; sliding two-row average.
[[maybe_unused]] static void TexConv_00171c74(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s - 1;
    r3 = Ld32(s + 0);
    r4 = Ld32(s + 4);
    sb = Ld16(s + 8);
    s += stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    sb = ip & (sb >> 1);
    sl = r3 >> 16;
    sl = sl + (r4 << 16);
    sl = sl + (r3 >> 8);
    r3 = sl + (r4 << 24);
    sl = r4 >> 16;
    sl = sl + (sb << 16);
    sl = sl + (r4 >> 8);
    r4 = sl + (sb << 24);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    do {
        r7 = Ld32(s + 0);
        r8 = Ld32(s + 4);
        sb = Ld16(s + 8);
        s += stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = r7 >> 16;
        sl = sl + (r8 << 16);
        sl = sl + (r7 >> 8);
        r7 = sl + (r8 << 24);
        sl = r8 >> 16;
        sl = sl + (sb << 16);
        sl = sl + (r8 >> 8);
        r8 = sl + (sb << 24);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        sb = Ld16(s + 8);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 >> 16;
        sl = sl + (r4 << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (r4 << 24);
        sl = r4 >> 16;
        sl = sl + (sb << 16);
        sl = sl + (r4 >> 8);
        r4 = sl + (sb << 24);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        St32(d + 0, r7);
        St32(d + 4, r8);
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x00171d70 (0x00178370 / 0x0017e970), 48 B: 8 B/tile; halfword gather.
[[maybe_unused]] static void TexConv_00171d70(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, sb = 0;
    do {
        r3 = Ld16(s);
        s += 2;
        r4 = Ld32(s);
        s += 4;
        sb = Ld16(s);
        s -= 6;
        s += stride;
        r3 = r3 + (r4 << 16);
        r4 = r4 >> 16;
        r4 = r4 + (sb << 16);
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00171da0 (0x001783a0 / 0x0017e9a0), 164 B: 8 B/tile; halfword gather; sliding two-row average.
[[maybe_unused]] static void TexConv_00171da0(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld16(s);
    s += 2;
    r4 = Ld32(s);
    s += 4;
    sb = Ld16(s);
    s -= 6;
    s += stride;
    r3 = r3 + (r4 << 16);
    r4 = r4 >> 16;
    r4 = r4 + (sb << 16);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    do {
        r7 = Ld16(s);
        s += 2;
        r8 = Ld32(s);
        s += 4;
        sb = Ld16(s);
        s -= 6;
        s += stride;
        r7 = r7 + (r8 << 16);
        r8 = r8 >> 16;
        r8 = r8 + (sb << 16);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld16(s);
        s += 2;
        r4 = Ld32(s);
        s += 4;
        sb = Ld16(s);
        s -= 6;
        s += stride;
        r3 = r3 + (r4 << 16);
        r4 = r4 >> 16;
        r4 = r4 + (sb << 16);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        St32(d + 0, r7);
        St32(d + 4, r8);
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x00171e44 (0x00178444 / 0x0017ea44), 80 B: 8 B/tile; 8 B block read; halfword gather.
[[maybe_unused]] static void TexConv_00171e44(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 2;
    do {
        r3 = Ld16(s - 2);
        r4 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 + (r4 << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (r4 << 8);
        r4 = r4 >> 16;
        sl = r4 + (sb << 16);
        sl = sl + (r4 >> 8);
        r4 = sl + (sb << 8);
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00171e94 (0x00178494 / 0x0017ea94), 240 B: 8 B/tile; 8 B block read; halfword gather; sliding two-row average.
[[maybe_unused]] static void TexConv_00171e94(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 2;
    r3 = Ld16(s - 2);
    r4 = Ld32(s + 0);
    sb = Ld32(s + 4);
    s += stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    sb = ip & (sb >> 1);
    sl = r3 + (r4 << 16);
    sl = sl + (r3 >> 8);
    r3 = sl + (r4 << 8);
    r4 = r4 >> 16;
    sl = r4 + (sb << 16);
    sl = sl + (r4 >> 8);
    r4 = sl + (sb << 8);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    do {
        r7 = Ld16(s - 2);
        r8 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = r7 + (r8 << 16);
        sl = sl + (r7 >> 8);
        r7 = sl + (r8 << 8);
        r8 = r8 >> 16;
        sl = r8 + (sb << 16);
        sl = sl + (r8 >> 8);
        r8 = sl + (sb << 8);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld16(s - 2);
        r4 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 + (r4 << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (r4 << 8);
        r4 = r4 >> 16;
        sl = r4 + (sb << 16);
        sl = sl + (r4 >> 8);
        r4 = sl + (sb << 8);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        St32(d + 0, r7);
        St32(d + 4, r8);
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x00171f84 (0x00178584 / 0x0017eb84), 48 B: 8 B/tile; 8 B block read; byte gather.
[[maybe_unused]] static void TexConv_00171f84(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, sb = 0;
    s = s + 1;
    do {
        r3 = Ld8(s - 1);
        r4 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += stride;
        r3 = r3 + (r4 << 8);
        r4 = r4 >> 24;
        r4 = r4 + (sb << 8);
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00171fb4 (0x001785b4 / 0x0017ebb4), 156 B: 8 B/tile; 8 B block read; byte gather; sliding two-row average.
[[maybe_unused]] static void TexConv_00171fb4(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    r3 = Ld8(s - 1);
    r4 = Ld32(s + 0);
    sb = Ld32(s + 4);
    s += stride;
    r3 = r3 + (r4 << 8);
    r4 = r4 >> 24;
    r4 = r4 + (sb << 8);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    do {
        r7 = Ld8(s - 1);
        r8 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += stride;
        r7 = r7 + (r8 << 8);
        r8 = r8 >> 24;
        r8 = r8 + (sb << 8);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld8(s - 1);
        r4 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += stride;
        r3 = r3 + (r4 << 8);
        r4 = r4 >> 24;
        r4 = r4 + (sb << 8);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        St32(d + 0, r7);
        St32(d + 4, r8);
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x00172050 (0x00178650 / 0x0017ec50), 68 B: 8 B/tile; 8 B block read; byte gather.
[[maybe_unused]] static void TexConv_00172050(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    do {
        r3 = Ld8(s - 1);
        r4 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r4 << 8);
        r3 = r3 + r4;
        r4 = sb + (r4 >> 24);
        r4 = r4 + (sb << 8);
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00172094 (0x00178694 / 0x0017ec94), 204 B: 8 B/tile; 8 B block read; byte gather; sliding two-row average.
[[maybe_unused]] static void TexConv_00172094(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    r3 = Ld8(s - 1);
    r4 = Ld32(s + 0);
    sb = Ld32(s + 4);
    s += stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    sb = ip & (sb >> 1);
    r3 = r3 + (r4 << 8);
    r3 = r3 + r4;
    r4 = sb + (r4 >> 24);
    r4 = r4 + (sb << 8);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    do {
        r7 = Ld8(s - 1);
        r8 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        r7 = r7 + (r8 << 8);
        r7 = r7 + r8;
        r8 = sb + (r8 >> 24);
        r8 = r8 + (sb << 8);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld8(s - 1);
        r4 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r4 << 8);
        r3 = r3 + r4;
        r4 = sb + (r4 >> 24);
        r4 = r4 + (sb << 8);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        St32(d + 0, r7);
        St32(d + 4, r8);
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x00172160 (0x00178760 / 0x0017ed60), 20 B: 4 B/tile.
[[maybe_unused]] static void TexConv_00172160(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0;
    do {
        r3 = Ld32(s);
        s += stride;
        St32(d, r3);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00172174 (0x00178774 / 0x0017ed74), 64 B: 4 B/tile; sliding two-row average.
[[maybe_unused]] static void TexConv_00172174(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s);
    s += stride;
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld32(s);
        s += stride;
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St32(d, r3);
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld32(s);
        s += stride;
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St32(d, r7);
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x001721b4 (0x001787b4 / 0x0017edb4), 48 B: 4 B/tile; byte gather.
[[maybe_unused]] static void TexConv_001721b4(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    do {
        r3 = Ld32(s);
        sb = Ld8(s + 4);
        s += stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r3 >> 8);
        r3 = r3 + (sb << 24);
        St32(d, r3);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x001721e4 (0x001787e4 / 0x0017ede4), 136 B: 4 B/tile; byte gather; sliding two-row average.
[[maybe_unused]] static void TexConv_001721e4(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s);
    sb = Ld8(s + 4);
    s += stride;
    r3 = ip & (r3 >> 1);
    sb = ip & (sb >> 1);
    r3 = r3 + (r3 >> 8);
    r3 = r3 + (sb << 24);
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld32(s);
        sb = Ld8(s + 4);
        s += stride;
        r7 = ip & (r7 >> 1);
        sb = ip & (sb >> 1);
        r7 = r7 + (r7 >> 8);
        r7 = r7 + (sb << 24);
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St32(d, r3);
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld32(s);
        sb = Ld8(s + 4);
        s += stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r3 >> 8);
        r3 = r3 + (sb << 24);
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St32(d, r7);
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x0017226c (0x0017886c / 0x0017ee6c), 40 B: 4 B/tile; byte gather.
[[maybe_unused]] static void TexConv_0017226c(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0;
    s = s - 1;
    do {
        r3 = Ld32(s);
        sb = Ld8(s + 4);
        s += stride;
        r3 = r3 >> 8;
        r3 = r3 + (sb << 24);
        St32(d, r3);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00172294 (0x00178894 / 0x0017ee94), 116 B: 4 B/tile; byte gather; sliding two-row average.
[[maybe_unused]] static void TexConv_00172294(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, ip = 0;
    s = s - 1;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s);
    sb = Ld8(s + 4);
    s += stride;
    r3 = r3 >> 8;
    r3 = r3 + (sb << 24);
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld32(s);
        sb = Ld8(s + 4);
        s += stride;
        r7 = r7 >> 8;
        r7 = r7 + (sb << 24);
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St32(d, r3);
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld32(s);
        sb = Ld8(s + 4);
        s += stride;
        r3 = r3 >> 8;
        r3 = r3 + (sb << 24);
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St32(d, r7);
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x00172308 (0x00178908 / 0x0017ef08), 60 B: 4 B/tile; halfword gather.
[[maybe_unused]] static void TexConv_00172308(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s - 1;
    do {
        r3 = Ld32(s);
        sb = Ld16(s + 4);
        s += stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 >> 16;
        sl = sl + (sb << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (sb << 24);
        St32(d, r3);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00172344 (0x00178944 / 0x0017ef44), 164 B: 4 B/tile; halfword gather; sliding two-row average.
[[maybe_unused]] static void TexConv_00172344(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s - 1;
    r3 = Ld32(s);
    sb = Ld16(s + 4);
    s += stride;
    r3 = ip & (r3 >> 1);
    sb = ip & (sb >> 1);
    sl = r3 >> 16;
    sl = sl + (sb << 16);
    sl = sl + (r3 >> 8);
    r3 = sl + (sb << 24);
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld32(s);
        sb = Ld16(s + 4);
        s += stride;
        r7 = ip & (r7 >> 1);
        sb = ip & (sb >> 1);
        sl = r7 >> 16;
        sl = sl + (sb << 16);
        sl = sl + (r7 >> 8);
        r7 = sl + (sb << 24);
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St32(d, r3);
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld32(s);
        sb = Ld16(s + 4);
        s += stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 >> 16;
        sl = sl + (sb << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (sb << 24);
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St32(d, r7);
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x001723e8 (0x001789e8 / 0x0017efe8), 32 B: 4 B/tile; halfword gather.
[[maybe_unused]] static void TexConv_001723e8(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0;
    do {
        r3 = Ld16(s);
        s += 2;
        sb = Ld16(s);
        s -= 2;
        s += stride;
        r3 = r3 + (sb << 16);
        St32(d, r3);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00172408 (0x00178a08 / 0x0017f008), 100 B: 4 B/tile; halfword gather; sliding two-row average.
[[maybe_unused]] static void TexConv_00172408(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld16(s);
    s += 2;
    sb = Ld16(s);
    s -= 2;
    s += stride;
    r3 = r3 + (sb << 16);
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld16(s);
        s += 2;
        sb = Ld16(s);
        s -= 2;
        s += stride;
        r7 = r7 + (sb << 16);
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St32(d, r3);
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld16(s);
        s += 2;
        sb = Ld16(s);
        s -= 2;
        s += stride;
        r3 = r3 + (sb << 16);
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St32(d, r7);
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x0017246c (0x00178a6c / 0x0017f06c), 52 B: 4 B/tile; halfword gather.
[[maybe_unused]] static void TexConv_0017246c(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 2;
    do {
        r3 = Ld16(s - 2);
        sb = Ld32(s);
        s += stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 + (sb << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (sb << 8);
        St32(d, r3);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x001724a0 (0x00178aa0 / 0x0017f0a0), 140 B: 4 B/tile; halfword gather; sliding two-row average.
[[maybe_unused]] static void TexConv_001724a0(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 2;
    r3 = Ld16(s - 2);
    sb = Ld32(s);
    s += stride;
    r3 = ip & (r3 >> 1);
    sb = ip & (sb >> 1);
    sl = r3 + (sb << 16);
    sl = sl + (r3 >> 8);
    r3 = sl + (sb << 8);
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld16(s - 2);
        sb = Ld32(s);
        s += stride;
        r7 = ip & (r7 >> 1);
        sb = ip & (sb >> 1);
        sl = r7 + (sb << 16);
        sl = sl + (r7 >> 8);
        r7 = sl + (sb << 8);
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St32(d, r3);
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld16(s - 2);
        sb = Ld32(s);
        s += stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 + (sb << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (sb << 8);
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St32(d, r7);
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x0017252c (0x00178b2c / 0x0017f12c), 32 B: 4 B/tile; byte gather.
[[maybe_unused]] static void TexConv_0017252c(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0;
    s = s + 1;
    do {
        r3 = Ld8(s - 1);
        sb = Ld32(s);
        s += stride;
        r3 = r3 + (sb << 8);
        St32(d, r3);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x0017254c (0x00178b4c / 0x0017f14c), 92 B: 4 B/tile; byte gather; sliding two-row average.
[[maybe_unused]] static void TexConv_0017254c(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    r3 = Ld8(s - 1);
    sb = Ld32(s);
    s += stride;
    r3 = r3 + (sb << 8);
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld8(s - 1);
        sb = Ld32(s);
        s += stride;
        r7 = r7 + (sb << 8);
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St32(d, r3);
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld8(s - 1);
        sb = Ld32(s);
        s += stride;
        r3 = r3 + (sb << 8);
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St32(d, r7);
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x001725a8 (0x00178ba8 / 0x0017f1a8), 48 B: 4 B/tile; byte gather.
[[maybe_unused]] static void TexConv_001725a8(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    do {
        r3 = Ld8(s - 1);
        sb = Ld32(s);
        s += stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (sb << 8);
        r3 = r3 + sb;
        St32(d, r3);
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x001725d8 (0x00178bd8 / 0x0017f1d8), 128 B: 4 B/tile; byte gather; sliding two-row average.
[[maybe_unused]] static void TexConv_001725d8(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    r3 = Ld8(s - 1);
    sb = Ld32(s);
    s += stride;
    r3 = ip & (r3 >> 1);
    sb = ip & (sb >> 1);
    r3 = r3 + (sb << 8);
    r3 = r3 + sb;
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld8(s - 1);
        sb = Ld32(s);
        s += stride;
        r7 = ip & (r7 >> 1);
        sb = ip & (sb >> 1);
        r7 = r7 + (sb << 8);
        r7 = r7 + sb;
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St32(d, r3);
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld8(s - 1);
        sb = Ld32(s);
        s += stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (sb << 8);
        r3 = r3 + sb;
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St32(d, r7);
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x00172658 (0x00178c58 / 0x0017f258), 28 B: 2 B/tile; halfword gather.
[[maybe_unused]] static void TexConv_00172658(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0;
    do {
        r3 = Ld16(s);
        s += stride;
        St16(d, static_cast<u16>(r3));
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x00172674 (0x00178c74 / 0x0017f274), 84 B: 2 B/tile; halfword gather; sliding two-row average.
[[maybe_unused]] static void TexConv_00172674(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld16(s);
    s += stride;
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld16(s);
        s += stride;
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St16(d, static_cast<u16>(r3));
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld16(s);
        s += stride;
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St16(d, static_cast<u16>(r7));
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x001726c8 (0x00178cc8 / 0x0017f2c8), 52 B: 2 B/tile; byte gather; halfword gather.
[[maybe_unused]] static void TexConv_001726c8(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    do {
        r3 = Ld16(s);
        sb = Ld8(s + 2);
        s += stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r3 >> 8);
        r3 = r3 + (sb << 8);
        St16(d, static_cast<u16>(r3));
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x001726fc (0x00178cfc / 0x0017f2fc), 144 B: 2 B/tile; byte gather; halfword gather; sliding two-row average.
[[maybe_unused]] static void TexConv_001726fc(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld16(s);
    sb = Ld8(s + 2);
    s += stride;
    r3 = ip & (r3 >> 1);
    sb = ip & (sb >> 1);
    r3 = r3 + (r3 >> 8);
    r3 = r3 + (sb << 8);
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld16(s);
        sb = Ld8(s + 2);
        s += stride;
        r7 = ip & (r7 >> 1);
        sb = ip & (sb >> 1);
        r7 = r7 + (r7 >> 8);
        r7 = r7 + (sb << 8);
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St16(d, static_cast<u16>(r3));
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld16(s);
        sb = Ld8(s + 2);
        s += stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r3 >> 8);
        r3 = r3 + (sb << 8);
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St16(d, static_cast<u16>(r7));
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x0017278c (0x00178d8c / 0x0017f38c), 36 B: 2 B/tile; byte gather.
[[maybe_unused]] static void TexConv_0017278c(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0;
    s = s + 1;
    do {
        r3 = Ld8(s - 1);
        sb = Ld8(s);
        s += stride;
        r3 = r3 + (sb << 8);
        St16(d, static_cast<u16>(r3));
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x001727b0 (0x00178db0 / 0x0017f3b0), 100 B: 2 B/tile; byte gather; sliding two-row average.
[[maybe_unused]] static void TexConv_001727b0(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, ip = 0;
    s = s + 1;
    ip = 0x7f7f7f7fU;
    r3 = Ld8(s - 1);
    sb = Ld8(s);
    s += stride;
    r3 = r3 + (sb << 8);
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld8(s - 1);
        sb = Ld8(s);
        s += stride;
        r7 = r7 + (sb << 8);
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St16(d, static_cast<u16>(r3));
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld8(s - 1);
        sb = Ld8(s);
        s += stride;
        r3 = r3 + (sb << 8);
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St16(d, static_cast<u16>(r7));
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x00172814 (0x00178e14 / 0x0017f414), 56 B: 2 B/tile; byte gather; halfword gather.
[[maybe_unused]] static void TexConv_00172814(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    do {
        r3 = Ld8(s);
        sb = Ld16(s + 1);
        s += stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        sl = sb << 24;
        sl = r3 + (sl >> 16);
        r3 = sl + sb;
        St16(d, static_cast<u16>(r3));
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x0017284c (0x00178e4c / 0x0017f44c), 156 B: 2 B/tile; byte gather; halfword gather; sliding two-row average.
[[maybe_unused]] static void TexConv_0017284c(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld8(s);
    sb = Ld16(s + 1);
    s += stride;
    r3 = ip & (r3 >> 1);
    sb = ip & (sb >> 1);
    sl = sb << 24;
    sl = r3 + (sl >> 16);
    r3 = sl + sb;
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld8(s);
        sb = Ld16(s + 1);
        s += stride;
        r7 = ip & (r7 >> 1);
        sb = ip & (sb >> 1);
        sl = sb << 24;
        sl = r7 + (sl >> 16);
        r7 = sl + sb;
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St16(d, static_cast<u16>(r3));
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld8(s);
        sb = Ld16(s + 1);
        s += stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        sl = sb << 24;
        sl = r3 + (sl >> 16);
        r3 = sl + sb;
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St16(d, static_cast<u16>(r7));
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x001728e8 (0x00178ee8 / 0x0017f4e8), 20 B: 1 B/tile; byte gather.
[[maybe_unused]] static void TexConv_001728e8(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0;
    do {
        r3 = Ld8(s);
        s += stride;
        St8(d, static_cast<u8>(r3));
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x001728fc (0x00178efc / 0x0017f4fc), 60 B: 1 B/tile; byte gather; sliding two-row average.
[[maybe_unused]] static void TexConv_001728fc(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0;
    r3 = Ld8(s);
    s += stride;
    r3 = r3 >> 1;
    do {
        r7 = Ld8(s);
        s += stride;
        r7 = r7 >> 1;
        r3 = r3 + r7;
        St8(d, static_cast<u8>(r3));
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld8(s);
        s += stride;
        r3 = r3 >> 1;
        r7 = r7 + r3;
        St8(d, static_cast<u8>(r7));
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x00172938 (0x00178f38 / 0x0017f538), 36 B: 1 B/tile; byte gather.
[[maybe_unused]] static void TexConv_00172938(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0;
    s = s + 1;
    do {
        r3 = Ld8(s - 1);
        sb = Ld8(s);
        s += stride;
        r3 = r3 >> 1;
        r3 = r3 + (sb >> 1);
        St8(d, static_cast<u8>(r3));
        d += stride;
        n -= 1u;
    } while (n != 0u);
    src = s;
    dst = d;
}

// 0x0017295c (0x00178f5c / 0x0017f55c), 96 B: 1 B/tile; byte gather; sliding two-row average.
[[maybe_unused]] static void TexConv_0017295c(const u8*& src, u8*& dst, u32 count, u32 stride)
{
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0;
    r3 = Ld8(s);
    s += 1;
    sb = Ld8(s);
    s += stride;
    r3 = r3 >> 1;
    r3 = r3 + (sb >> 1);
    r3 = r3 >> 1;
    do {
        r7 = Ld8(s - 1);
        sb = Ld8(s);
        s += stride;
        r7 = r7 >> 1;
        r7 = r7 + (sb >> 1);
        r7 = r7 >> 1;
        r3 = r3 + r7;
        St8(d, static_cast<u8>(r3));
        d += stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld8(s - 1);
        sb = Ld8(s);
        s += stride;
        r3 = r3 >> 1;
        r3 = r3 + (sb >> 1);
        r3 = r3 >> 1;
        r7 = r7 + r3;
        St8(d, static_cast<u8>(r7));
        d += stride;
        n -= 1u;
    } while (n != 0u);
done:
    src = s;
    dst = d;
}

// 0x001729BC..0x00172A90: VXS2 program header that
// follows the converter leaves in ledger entry 0x00170d70.
// +0x00 is the next header's offset table (+0x44 into 0x0016C3BC /
// 0x001729BC respectively); +0x04..+0x44 is 0xFFFFFFFF padding.
const u32 kTexProgram_170d70[53] = {
    0x0016c400, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff,
    0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff,
    0xffffffff, 0xea0005b7, 0x00000100, 0x20202035, 0x32535856, 0x00004a10, 0x00004abc, 0x00004c48,
    0x00004d88, 0x00004f9c, 0x000050dc, 0x000052e0, 0x00005410, 0x00004a2c, 0x00004b14, 0x00004c8c,
    0x00004e04, 0x00004fe0, 0x00005154, 0x00005320, 0x0000546c, 0x00005568, 0x000055ec, 0x000056f4,
    0x000057d0, 0x00005920, 0x000059f4, 0x00005b34, 0x00005c00, 0x00005584, 0x0000562c, 0x00005728,
    0x00005824, 0x00005950, 0x00005a44, 0x00005b64, 0x00005c44,
};

// 0x00178FBC..0x00179090: VXS2 program header that
// follows the converter leaves in ledger entry 0x00177370.
// +0x00 is the next header's offset table (+0x44 into 0x0016C3BC /
// 0x001729BC respectively); +0x04..+0x44 is 0xFFFFFFFF padding.
const u32 kTexProgram_177370[53] = {
    0x00172a00, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff,
    0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff,
    0xffffffff, 0xea0005b7, 0x00000200, 0x20202035, 0x32535856, 0x00004a10, 0x00004abc, 0x00004c48,
    0x00004d88, 0x00004f9c, 0x000050dc, 0x000052e0, 0x00005410, 0x00004a2c, 0x00004b14, 0x00004c8c,
    0x00004e04, 0x00004fe0, 0x00005154, 0x00005320, 0x0000546c, 0x00005568, 0x000055ec, 0x000056f4,
    0x000057d0, 0x00005920, 0x000059f4, 0x00005b34, 0x00005c00, 0x00005584, 0x0000562c, 0x00005728,
    0x00005824, 0x00005950, 0x00005a44, 0x00005b64, 0x00005c44,
};

// ---------------------------------------------------------------------------
// Tail of the third ledger entry, 0x0017F5BC..0x0017F624.
//
// The 7,348-byte size of 0x0017D970 ends four bytes into the following
// translation unit, so the tail contains the next block pointer plus four
// unrelated static-init/teardown thunks.  They are reproduced here for
// completeness; none of them is part of the converter.
// ---------------------------------------------------------------------------

// 0x0017F5BC: `.word 0x00179000` -- pointer to the second block's VXS2 header
// (+0x44 into the 0x178FBC blob).

// 0x0017F5C0 (12 B): `mov r1,#0` / `str r1,[r0]` / `bx lr`.
[[maybe_unused]] void TexTail_0017f5c0(u32* object)
{
    object[0] = 0;
}

// 0x0017F5CC (20 B): r0=0x004DACE0, r1=0x00361C24, r2=0x40, r3=2, then
// `b 0x002C68B4` (the shared copy tail inside AsdMemory_func_002c684c).
[[maybe_unused]] void TexTail_0017f5cc()
{
    std::memcpy(reinterpret_cast<void*>(static_cast<std::uintptr_t>(0x004DACE0u)),
                reinterpret_cast<const void*>(static_cast<std::uintptr_t>(0x00361C24u)),
                0x40u);
}

// 0x0017F5E8 (16 B) and the byte-identical 0x0017F5F8: `mov r1,#0`,
// `mov r2,r1`, `stm r0,{r1,r2}`, `bx lr`.
[[maybe_unused]] void TexTail_0017f5e8(u32* object)
{
    object[0] = 0;
    object[1] = 0;
}

[[maybe_unused]] void TexTail_0017f5f8(u32* object)
{
    object[0] = 0;
    object[1] = 0;
}

// 0x0017F608 (20 B): r0=0x004E5290, r1=0x003578E8, r2=4, r3=3, then
// `b 0x002C68B4`.
[[maybe_unused]] void TexTail_0017f608()
{
    std::memcpy(reinterpret_cast<void*>(static_cast<std::uintptr_t>(0x004E5290u)),
                reinterpret_cast<const void*>(static_cast<std::uintptr_t>(0x003578E8u)),
                4u);
}

} // namespace

// ---------------------------------------------------------------------------
// 0x00170D70: descriptor initialiser, first block (stride 0x400).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00170d70, 7456)
void func_00170d70(TexConvertDesc* desc, s32 format)
{
    // 0x00170D70: `cmp r4,#0xc` / `movlt r4,#0xc`.
    if (format < 0x0C)
        format = 0x0C;
    // 0x00170D78: `cmp r4,#0x34` / `movgt r4,#0x34`.
    if (format > 0x34)
        format = 0x34;
    // 0x00170D80: `str r4,[r0,#0x48]`.
    desc->format = static_cast<u32>(format);

    // 0x00170D84..0x00170D94: r6 = kTexGroupShift[format] + 8 (packing shift),
    // r5 = kTexGroupIndex[format] (permutation entry).
    const u32 shift = 8u + kTexGroupShift[static_cast<u32>(format)];
    const u32 group = kTexGroupIndex[static_cast<u32>(format)];

    // 0x00170D98..0x00170DAC: r4 = kTexPack16 + group*16, r7 = kTexTranspose16,
    // r8 = desc + 0x178.
    const u8* pack16 = kTexPack16[group];
    for (u32 i = 0; i < 16u; ++i) {
        // `ldrb sl,[r4],#1` / `ldrb fp,[r7],#1` / `orr fp,fp,sl,lsl r6`
        // / `str fp,[r8],#4`.
        desc->words_178[i] = static_cast<u32>(kTexTranspose16[i]) |
                             (static_cast<u32>(pack16[i]) << shift);
    }

    // 0x00170DC4: `sub r6,r6,#2` -- the 64-word table is packed two bits lower.
    const u32 shift64 = shift - 2u;

    // 0x00170DC8..0x00170DDC: r4 = kTexPack64 + group*64, r7 = kTexTranspose64,
    // r8 = desc + 0x78.
    const u8* pack64 = kTexPack64[group];
    for (u32 i = 0; i < 64u; ++i) {
        desc->words_78[i] = static_cast<u32>(kTexTranspose64[i]) |
                            (static_cast<u32>(pack64[i]) << shift64);
    }

    // 0x00170DF4..0x00170E18: eight component-selector bytes, all 9.
    desc->field_51 = 9;
    desc->field_52 = 9;
    desc->field_53 = 9;
    desc->field_54 = 9;
    desc->field_58 = 9;
    desc->field_60 = 9;
    desc->field_68 = 9;
    desc->field_70 = 9;

    // 0x00170E20..0x001729BC: the sixty leaves of this block are the
    // kTexStride_170d70 instantiation (see TexConv_* above).
    static_assert(kTexStride_170d70 == 0x400u);
}

// ---------------------------------------------------------------------------
// 0x00177370: descriptor initialiser, second block (stride 0x100).
//
// Byte-identical to 0x00170D70 apart from the PC-relative table bases, which
// sit at 0x001770D4 / 0x00177114 / 0x00177254 / 0x00177294 / 0x00177304 /
// 0x0017733A and hold the same 0x29C bytes as 0x00170AD4..0x00170D3A.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00177370, 7456)
void func_00177370(TexConvertDesc* desc, s32 format)
{
    if (format < 0x0C)                     // 0x00177370: cmp/movlt
        format = 0x0C;
    if (format > 0x34)                     // 0x00177378: cmp/movgt
        format = 0x34;
    desc->format = static_cast<u32>(format);                  // 0x00177380: str r4,[r0,#0x48]

    const u32 shift = 8u + kTexGroupShift[static_cast<u32>(format)];   // 0x00177384..0x0017738C
    const u32 group = kTexGroupIndex[static_cast<u32>(format)];        // 0x00177390..0x00177394

    const u8* pack16 = kTexPack16[group];            // 0x00177398..0x0017739C
    for (u32 i = 0; i < 16u; ++i) {
        desc->words_178[i] = static_cast<u32>(kTexTranspose16[i]) |
                             (static_cast<u32>(pack16[i]) << shift);
    }

    const u32 shift64 = shift - 2u;                  // 0x001773C4: sub r6,r6,#2
    const u8* pack64 = kTexPack64[group];            // 0x001773C8..0x001773CC
    for (u32 i = 0; i < 64u; ++i) {
        desc->words_78[i] = static_cast<u32>(kTexTranspose64[i]) |
                            (static_cast<u32>(pack64[i]) << shift64);
    }

    desc->field_51 = 9;                     // 0x001773FC..0x00177418
    desc->field_52 = 9;
    desc->field_53 = 9;
    desc->field_54 = 9;
    desc->field_58 = 9;
    desc->field_60 = 9;
    desc->field_68 = 9;
    desc->field_70 = 9;

    // 0x00177420..0x00178FBC: the sixty leaves of this block are the
    // kTexStride_177370 instantiation (see TexConv_* above).
    static_assert(kTexStride_177370 == 0x100u);
}

// ---------------------------------------------------------------------------
// 0x0017D970: descriptor initialiser, third block (stride 0x200).
//
// The tables sit at 0x0017D6D4..0x0017D970 and are again the same 0x29C bytes.
// This block is 108 bytes shorter than the other two because it is followed by
// the four unrelated thunks reproduced above instead of a VXS2 header.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0017d970, 7348)
void func_0017d970(TexConvertDesc* desc, s32 format)
{
    if (format < 0x0C)                     // 0x0017D970: cmp/movlt
        format = 0x0C;
    if (format > 0x34)                     // 0x0017D978: cmp/movgt
        format = 0x34;
    desc->format = static_cast<u32>(format);                  // 0x0017D980: str r4,[r0,#0x48]

    const u32 shift = 8u + kTexGroupShift[static_cast<u32>(format)];   // 0x0017D984..0x0017D98C
    const u32 group = kTexGroupIndex[static_cast<u32>(format)];        // 0x0017D990..0x0017D994

    const u8* pack16 = kTexPack16[group];            // 0x0017D998..0x0017D99C
    for (u32 i = 0; i < 16u; ++i) {
        desc->words_178[i] = static_cast<u32>(kTexTranspose16[i]) |
                             (static_cast<u32>(pack16[i]) << shift);
    }

    const u32 shift64 = shift - 2u;                  // 0x0017D9C4: sub r6,r6,#2
    const u8* pack64 = kTexPack64[group];            // 0x0017D9C8..0x0017D9CC
    for (u32 i = 0; i < 64u; ++i) {
        desc->words_78[i] = static_cast<u32>(kTexTranspose64[i]) |
                            (static_cast<u32>(pack64[i]) << shift64);
    }

    desc->field_51 = 9;                     // 0x0017D9FC..0x0017DA18
    desc->field_52 = 9;
    desc->field_53 = 9;
    desc->field_54 = 9;
    desc->field_58 = 9;
    desc->field_60 = 9;
    desc->field_68 = 9;
    desc->field_70 = 9;

    // 0x0017DA20..0x0017F5BC: the sixty leaves of this block are the
    // kTexStride_17d970 instantiation (see TexConv_* above).
    static_assert(kTexStride_17d970 == 0x200u);
}

} // namespace smt4::engine

