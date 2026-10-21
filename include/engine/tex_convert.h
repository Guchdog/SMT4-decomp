#pragma once
#include <cstddef>
#include "types.h"

/**
 * Texture / bitmap format conversion blocks at 0x00170D70, 0x00177370 and
 * 0x0017D970.
 *
 * Each of the three ledger entries is a *block* rather than a single C
 * function.  In binary order a block contains:
 *
 *   0x0000  + 0x00B0   format-descriptor initialiser (`func_00170d70`)
 *   0x00B0  + 0x1B9C   sixty tiled-pixel converter leaves
 *   0x1C4C  + 0x00D4   VXS2 program header (first and second blocks only)
 *
 * The three copies are instruction-for-instruction identical; they differ only
 * in the tile stride the leaves advance by (0x400, 0x100 and 0x200) and in the
 * PC-relative addresses of their tables.  `src/engine/tex_convert.cpp`
 * reconstructs the converter leaves once, parameterised by that stride, and
 * gives each block its own descriptor initialiser.
 *
 * All offsets below are proven by the initialiser at 0x00170D70.
 */

namespace smt4::engine {

/**
 * 0x1B8-byte format descriptor filled by 0x00170D70 / 0x00177370 / 0x0017D970.
 *
 * The initialiser only touches the bytes and word arrays named here.  +0x50
 * itself is never written (`add r4,r0,#0x50` is followed by `strb r5,[r4,#1]`
 * at 0x00170DFC), so it stays reserved.
 */
struct TexConvertDesc {
    u8  pad_00[0x48];                   // +0x00..+0x48
    u32 format;                         // +0x48: `str r4,[r0,#0x48]` (0x00170D80)
    u8  pad_4c[0x04];                   // +0x4C..+0x50
    u8  field_50;                       // +0x50: not written by the initialiser
    u8  field_51;                       // +0x51: `strb r5,[r4,#1]` with r5=9 (0x00170DFC)
    u8  field_52;                       // +0x52: `strb r5,[r4,#2]` (0x00170E00)
    u8  field_53;                       // +0x53: `strb r5,[r4,#3]` (0x00170E04)
    u8  field_54;                       // +0x54: `strb r5,[r4,#4]` (0x00170E08)
    u8  pad_55[0x03];                   // +0x55..+0x58
    u8  field_58;                       // +0x58: `strb r5,[r4,#8]` (0x00170E0C)
    u8  pad_59[0x07];                   // +0x59..+0x60
    u8  field_60;                       // +0x60: `strb r5,[r4,#0x10]` (0x00170E10)
    u8  pad_61[0x07];                   // +0x61..+0x68
    u8  field_68;                       // +0x68: `strb r5,[r4,#0x18]` (0x00170E14)
    u8  pad_69[0x07];                   // +0x69..+0x70
    u8  field_70;                       // +0x70: `strb r5,[r4,#0x20]` (0x00170E18)
    u8  pad_71[0x07];                   // +0x71..+0x78
    u32 words_78[0x40];                 // +0x78..+0x178: `str fp,[r8],#4` × 0x40 (0x00170DDC)
    u32 words_178[0x10];                // +0x178..+0x1B8: `str fp,[r8],#4` × 0x10 (0x00170DAC)
};
static_assert(offsetof(TexConvertDesc, format) == 0x48);
static_assert(offsetof(TexConvertDesc, field_50) == 0x50);
static_assert(offsetof(TexConvertDesc, field_51) == 0x51);
static_assert(offsetof(TexConvertDesc, field_54) == 0x54);
static_assert(offsetof(TexConvertDesc, field_58) == 0x58);
static_assert(offsetof(TexConvertDesc, field_60) == 0x60);
static_assert(offsetof(TexConvertDesc, field_68) == 0x68);
static_assert(offsetof(TexConvertDesc, field_70) == 0x70);
static_assert(offsetof(TexConvertDesc, words_78) == 0x78);
static_assert(offsetof(TexConvertDesc, words_178) == 0x178);
static_assert(sizeof(TexConvertDesc) == 0x1B8);

// ---------------------------------------------------------------------------
// Ledger block entry points -- block starts, not ordinary AAPCS routines.
//
// These three addresses are *block* starts, not ordinary AAPCS routines.  The
// initialiser at 0x00170D70 begins with `cmp r4,#0xc`: the format selector is
// already live in r4 on entry and is never loaded from r1.  The initialiser
// then ends with `mov pc,lr` at 0x00170E1C, so it returns normally instead of
// falling through into the leaves.
//
// The sixty converter leaves are separate ordinary AAPCS functions taking the
// source pointer in r0, the destination pointer in r1 and the tile count in
// r2 (each leaf bakes its own tile stride into its body).  Only the three
// block entries themselves are non-AAPCS, because they read `r4`.
//
// The declarations exist only so that the ledger's reconstructed spelling has
// a definition in src/engine/tex_convert.cpp.  Treat the parameters as a
// description of r0/r4, not as an ABI contract.
// ---------------------------------------------------------------------------
void func_00170d70(TexConvertDesc* desc, s32 format);   // 0x00170D70, 7456 B
void func_00177370(TexConvertDesc* desc, s32 format);   // 0x00177370, 7456 B
void func_0017d970(TexConvertDesc* desc, s32 format);   // 0x0017D970, 7348 B

} // namespace smt4::engine
