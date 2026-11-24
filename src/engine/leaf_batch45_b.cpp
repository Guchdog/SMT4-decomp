#include "types.h"

// Batch 45 B: 100 CFG-checked, disjoint TODO functions encoded byte-for-byte.

namespace script_vm_2900b0_calls {
extern "C" void script_vm_func_0028efe0(u32 quest_id, u32 a1, u32 a2);
extern "C" void* script_vm_func_00385edc(void* bundle, u32 quest_id);
extern "C" void ui_func_002be7fc(char* dst, const char* fmt, ...);
extern "C" void* script_vm_func_002c5e2c(const char* path);
extern "C" void script_vm_func_00296d8c(void* text, u32 a1, u32 a2, u32 a3, u32 a4, void* mbm, u32 idx);
extern "C" s32 script_vm_func_00241d70(u32 quest_id);
extern "C" s32 script_vm_func_00333910(u32 quest_id, u32 mode);
extern "C" void* script_vm_func_002b6700(u32 quest_id);
extern "C" const char* script_vm_func_002bd1b0(const void* src, u32 a1);
extern "C" void AsdText_func_00296de0_call(void* text, u32 a1, u32 a2, u32 a3, u32 a4, const char* fmt, const char* s)
    __asm__("_ZN4smt46engine21AsdText_func_00296de0EPNS0_7AsdTextEiiiiPKc");
extern "C" void script_vm_func_0029025c(u32 quest_id);
} // namespace script_vm_2900b0_calls

// DECOMP_FUNC(0x002900b0, 428)
extern "C" void script_vm_func_002900b0(u32 quest_id, u32 mode) {
    using namespace script_vm_2900b0_calls;

    u8* const quest_work = *reinterpret_cast<u8* volatile*>(0x0043DD50u);
    if (quest_id == 0) {
        return;
    }

    script_vm_func_0028efe0(quest_id, 1, 1);

    void* const bundle = *reinterpret_cast<void**>(0x00433158u);
    void* mbm = script_vm_func_00385edc(bundle, quest_id);
    if (mbm != nullptr) {
        *reinterpret_cast<void**>(quest_work + 0x5E0) = mbm;
        quest_work[0x5F7] = 1;
    } else {
        char path[0x34];
        ui_func_002be7fc(path, "event/quest/quest%03d.mbm", quest_id);
        mbm = script_vm_func_002c5e2c(path);
        *reinterpret_cast<void**>(quest_work + 0x5E0) = mbm;
        quest_work[0x5F7] = 0;
    }

    script_vm_func_00296d8c(
        *reinterpret_cast<void**>(quest_work + 0x5D4),
        3, 0xFFFFFFFFu, 0, 3, mbm, 0);

    const s32 sub_idx = script_vm_func_00241d70(quest_id);
    if (sub_idx > 0) {
        script_vm_func_00296d8c(
            *reinterpret_cast<void**>(quest_work + 0x5DC),
            3, 0xFFFFFFFFu, 0, 3,
            *reinterpret_cast<void**>(quest_work + 0x5E0),
            static_cast<u32>(sub_idx));
    }

    script_vm_func_0028efe0(quest_id, 1, 0);

    const s32 msg_idx = script_vm_func_00333910(quest_id, mode);
    if (msg_idx < 0) {
        u8* const row = static_cast<u8*>(script_vm_func_002b6700(quest_id));
        const char* const text = script_vm_func_002bd1b0(row + 0xE8, 0);
        AsdText_func_00296de0_call(
            *reinterpret_cast<void**>(quest_work + 0x5D8),
            3, 0xFFFFFFFFu, 0, 3, "%s", text);
    } else {
        script_vm_func_00296d8c(
            *reinterpret_cast<void**>(quest_work + 0x5D8),
            3, 0xFFFFFFFFu, 0, 3,
            *reinterpret_cast<void**>(quest_work + 0x5E4),
            static_cast<u32>(msg_idx));
    }

    script_vm_func_0029025c(quest_id);
}

// ---------------------------------------------------------------------------
// 0x00288424 (432 B): single-precision tanf(x).
//
//   * |x| < 2^-12 returns x unchanged (VFP arithmetic is not entered).
//   * 2^-12 <= |x| < pi/4 uses the literal value (quadrant 0, no reduction).
//   * pi/4 <= |x| < 12867.5712890625 reduces with q = round(x * 2/pi) and the
//     four-term split of pi/2, keeping q & 3 as the quadrant.
//   * larger magnitudes and non-finite values go through the generic
//     reduction helper at 0x003EB4F4, which writes the quadrant (0..3, or
//     0xFFFFFFFF for non-finite input) and returns the reduced angle.
//
// The tail evaluates tan(r) = r + r^3 * P(r^2) and, for odd quadrants,
// returns -1/tan(r) (tan(r + k*pi/2)).  Quadrant -1 marks the non-reduced
// cases: NaN returns NaN, infinity sets errno through 0x002A464E and returns
// the VFP default NaN, and a subnormal reduced value additionally runs the
// 16-byte underflow probe at 0x002A462C whose result is discarded.
//
// The 432-byte extent includes the literal pool at 0x00288594..0x002885D4.
// ---------------------------------------------------------------------------
namespace engine_288424 {
constexpr u32 F32ToBits(f32 value) noexcept {
    return __builtin_bit_cast(u32, value);
}

// Bit-pattern magnitude comparisons on (bits << 1), which drops the sign.
constexpr u32 kPiOverFourShift = 0x7E921FB6u;   // (bits of pi/4) << 1
constexpr u32 kTinyShift = 0x73000000u;         // (bits of 2^-12) << 1
constexpr u32 kReductionLimit = 0x46490E49u;    // bits of 12867.5712890625f

// Reduction constants: 2/pi, the 2^23 round-to-integer magic, and the
// four-term split of pi/2 (1.57079632679 = p0 + p1 + p2 + p3).
constexpr f32 kTwoOverPi = 0.6366197466850281f;        // 0x3F22F983
constexpr f32 kRoundMagic = 8388608.0f;                // 0x4B000000
constexpr f32 kHalfPiPart0 = 1.5703125f;               // 0x3FC90000
constexpr f32 kHalfPiPart1 = 0.0004837512969970703f;   // 0x39FDA000
constexpr f32 kHalfPiPart2 = 7.549533620476723e-08f;   // 0x33A22000
constexpr f32 kHalfPiPart3 = 2.5633440682570896e-12f;  // 0x2C34611A

// Odd minimax coefficients for tan(r) = r + r^3 * P(r^2), lowest first.
constexpr f32 kTanC0 = 0.0020511774346232414f;   // 0x3B066D0C
constexpr f32 kTanC1 = 0.009943420998752117f;    // 0x3C22E9BB
constexpr f32 kTanC2 = 0.025203008204698563f;    // 0x3CCE768A
constexpr f32 kTanC3 = 0.05315177142620087f;     // 0x3D59B5AC
constexpr f32 kTanC4 = 0.1334274560213089f;      // 0x3E08A135
constexpr f32 kTanC5 = 0.3333294689655304f;      // 0x3EAAAA29

static_assert(F32ToBits(kTwoOverPi) == 0x3F22F983u);
static_assert(F32ToBits(kRoundMagic) == 0x4B000000u);
static_assert(F32ToBits(kHalfPiPart0) == 0x3FC90000u);
static_assert(F32ToBits(kHalfPiPart1) == 0x39FDA000u);
static_assert(F32ToBits(kHalfPiPart2) == 0x33A22000u);
static_assert(F32ToBits(kHalfPiPart3) == 0x2C34611Au);
static_assert(F32ToBits(kTanC0) == 0x3B066D0Cu);
static_assert(F32ToBits(kTanC1) == 0x3C22E9BBu);
static_assert(F32ToBits(kTanC2) == 0x3CCE768Au);
static_assert(F32ToBits(kTanC3) == 0x3D59B5ACu);
static_assert(F32ToBits(kTanC4) == 0x3E08A135u);
static_assert(F32ToBits(kTanC5) == 0x3EAAAA29u);
}  // namespace engine_288424

namespace engine_288424_calls {
// 0x002A4600 (44 B): classifies an IEEE-754 single bit pattern passed in r0.
// Returns 0 zero, 3 infinity, 4 subnormal, 5 finite normal, 7 NaN (1 is
// remapped to 5 and never leaves the routine).
extern "C" u32 ui_func_002a4600(u32 value_bits);
// 0x002A462C (16 B): evaluates a constant square that underflows to +0.0f;
// only an underflow probe, its result is discarded.
extern "C" f32 ui_func_002a462c(f32 value);
// 0x003EB4F4 (296 B live body): generic Payne-Hanek-style reduction of r1.
// Writes the quadrant (0..3, or 0xFFFFFFFF for non-finite input) to *r0 and
// returns the reduced angle in s0; for non-finite input it leaves s0 as the
// incoming value.
extern "C" f32 ui_func_003eb4f4(u32* out_integer, u32 value_bits);
// 0x002A464E (Thumb, 12 B): stores its argument through *__errno_location().
// The surrounding libm helper is unresolved; only the EDOM store is used.
extern "C" s32* func_002a464e_errno_set(s32 value);
}  // namespace engine_288424_calls

// DECOMP_FUNC(0x00288424, 432)
extern "C" f32 engine_func_00288424(f32 x) {
    using namespace engine_288424;
    using namespace engine_288424_calls;

    const u32 bits = F32ToBits(x);
    s32 quadrant;
    f32 reduced;

    if ((bits << 1) >= kPiOverFourShift) {
        if ((bits & 0x7FFFFFFFu) >= kReductionLimit) {
            reduced = ui_func_003eb4f4(reinterpret_cast<u32*>(&quadrant), bits);
        } else {
            // q = round-to-nearest(x * 2/pi) through the 2^23 add/subtract
            // trick; the sign of x selects the subtraction direction.
            const f32 scaled = x * kTwoOverPi;
            f32 rounded;
            if ((bits & 0x80000000u) != 0) {
                const f32 biased = scaled - kRoundMagic;
                rounded = biased + kRoundMagic;
            } else {
                const f32 biased = scaled + kRoundMagic;
                rounded = biased - kRoundMagic;
            }
            quadrant = static_cast<s32>(rounded) & 3;

            // r = x - q*(pi/2), each part subtracted with one rounding.
            reduced = x - rounded * kHalfPiPart0;
            reduced = reduced - rounded * kHalfPiPart1;
            reduced = reduced - rounded * kHalfPiPart2;
            reduced = reduced - rounded * kHalfPiPart3;
        }
    } else {
        quadrant = ((bits << 1) < kTinyShift) ? -1 : 0;
        reduced = x;
    }

    if (quadrant < 0) {
        const u32 magnitude = F32ToBits(reduced) << 1;
        if (magnitude > 0xFF000000u) {
            return reduced + reduced;        // NaN propagates through VADD
        }
        if (magnitude == 0xFF000000u) {
            (void)func_002a464e_errno_set(1);   // *__errno_location() = EDOM
            volatile f32 zero = 0.0f;
            return zero / zero;              // VFP default NaN
        }
        if (ui_func_002a4600(F32ToBits(reduced)) == 4u) {
            (void)ui_func_002a462c(reduced);
        }
        return reduced;
    }

    const f32 square = reduced * reduced;
    f32 poly = kTanC0 + square * kTanC1;
    poly = kTanC2 + square * poly;
    poly = kTanC3 + square * poly;
    poly = kTanC4 + square * poly;
    poly = kTanC5 + square * poly;
    const f32 tangent = reduced + reduced * (poly * square);

    if ((quadrant & 1) == 0) {
        return tangent;
    }
    return -1.0f / tangent;        // tan(r + k*pi/2) for odd k
}

namespace battle_2176ec_calls {
// Reads work[0x1c] - selector - 1 through a tagged union table.  The caller
// only uses selector 0 and compares the result as a signed index.
extern "C" s32 engine_func_00296f60(u32 selector);

// Dereferences the global slot passed in r0 and selects an entry from the
// table at 0x00434278 when its +0x84 field is in [0, 4); returns 0 otherwise.
extern "C" void* script_vm_func_0027eb98(void* global_slot);

// Returns the UI context pointer stored at 0x00435D90.
extern "C" void* ui_func_00293c98();

// Scans 109 rows of 50 signed halfwords at base+0x1FC0 and returns the row
// whose entry equals index, or 0 when the index is not present.
extern "C" const u8* ui_func_00282b94(void* base, u32 index);

// Clears per-actor effect state for all 109 rows.
extern "C" void func_00250960(void* base);

// The trailing arguments at positions 7, 8 and 23 are transmitted as raw
// 32-bit words on the stack; the callee consumes the same words as f32 bit
// patterns (softfp/variadic convention in the pinned image).
extern "C" s32 battle_func_002553ec(
    s32 base, void* actor, void* attack, u32 a3,
    s32 a4, s32 a5, s32 a6, u32 a7_bits, u32 a8_bits,
    s32 a9, s32 a10, s32 a11, s32 a12, s32 a13, s32 a14, s32 a15,
    s32 a16, s32 a17, s32 a18, s32 a19, s32 a20, s32 a21, s32 a22,
    u32 a23_bits, s32 a24);

extern "C" s32 battle_func_002508c0(s32 arg0, void* arg1, void* arg2);

// Returns manager[+4] + 0x11C + index * 385 (element stride 0x604).
extern "C" void* camp_func_002a89e4(u32 index);

extern "C" void battle_func_0026e88c(void* p, u32 bit);

// r2 is stored at +0x28 and s0 at +0x30 of the action record.
extern "C" void battle_func_003dde9c(s32 id, u32 key, u32 value, f32 scale);

// r0-r3 plus three architected stack words.
extern "C" void battle_func_00250800(
    u32 a0, u32 a1, u32 a2, u32 a3,
    u32 a4, u32 a5, u32 a6);

// The two stack words at [sp] and [sp+4] are consumed as f32 bit patterns,
// the third as the halfword written to +0x26.
extern "C" void battle_func_003dddf8(
    s32 arg0, void* arg1, u32 arg2, u32 arg3,
    u32 arg4_bits, u32 arg5_bits, u32 arg6);
} // namespace battle_2176ec_calls

// DECOMP_FUNC(0x002176ec, 436)
//
// Indexed per-actor battle-effect dispatch:
//   * index = engine_func_00296f60(0), compared as a signed value against 109;
//   * index < 109 resolves a 276-byte unit row at
//     *(base+0x1E98) + index*276 and a 648-byte action slot via
//     ui_func_00282b94, then submits a full 25-argument effect (21 stack
//     words) and a 3-argument follow-up for action id 0x19;
//   * index >= 109 clears halfword +0x2A of camp row (index-109), raises
//     effect bit 1 and posts a single action with scale 8.0f;
//   * both paths emit the shared 0x01000178 action followed by the 7-argument
//     animation update (stack words 2, 0xB4, 3) and return 1.
extern "C" s32 battle_func_002176ec() {
    using namespace battle_2176ec_calls;

    const s32 index = engine_func_00296f60(0);
    void* const global = *reinterpret_cast<void**>(0x0043427Cu);
    void* const ref = script_vm_func_0027eb98(global);

    if (index < 0x6D) {
        void* const base = ui_func_00293c98();
        void* const units = *reinterpret_cast<void**>(
            static_cast<u8*>(base) + 0x1E98);
        void* const row = static_cast<u8*>(units) +
                          static_cast<u32>(index) * 276u;

        const u8* const slot = ui_func_00282b94(
            ui_func_00293c98(), static_cast<u32>(index));
        func_00250960(ui_func_00293c98());

        const s32 field_b6 = *reinterpret_cast<const s16*>(slot + 0x1B6);
        const s32 field_b4 = *reinterpret_cast<const s16*>(slot + 0x1B4);

        battle_func_002553ec(
            0, ref, row, 0,
            field_b6, -1, -1,
            static_cast<u32>(field_b4), static_cast<u32>(field_b6),
            0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1);
        battle_func_002508c0(0x19, ref, row);
    } else {
        void* const obj =
            camp_func_002a89e4(static_cast<u32>(index) - 0x6Du);
        *reinterpret_cast<u16*>(static_cast<u8*>(obj) + 0x2A) = 0;
        battle_func_0026e88c(obj, 1);
        battle_func_003dde9c(0, reinterpret_cast<u32>(ref), 0xF, 8.0f);
    }

    battle_func_00250800(0, reinterpret_cast<u32>(ref), 0x01000178u, 0, 0, 0, 0);
    battle_func_003dddf8(0, ref, 0, 1, 2, 0xB4, 3);
    return 1;
}

// Tail of the same 436-byte ledger extent: an unnamed entry point at
// 0x00217858 (72 B) with no direct caller (no BL, literal or fallthrough
// reaches it in the pinned image).  It returns 1 only when the five flag
// fields at p+0x5925..p+0x5928 and the unaligned word at p+0x5929 are zero.
extern "C" s32 func_00217858(const u8* p) {
    const u8* const q = p + 0x5900;
    if (q[0x25] != 0 || q[0x26] != 0 || q[0x27] != 0 || q[0x28] != 0) {
        return 0;
    }
    return *reinterpret_cast<const u32*>(q + 0x29) == 0 ? 1 : 0;
}

namespace camp_191cf4_calls {
extern "C" void* camp_func_002a0fac();
extern "C" void func_002b7f0a(void* base, s32 count, s32 size, u32 comparator);
} // namespace camp_191cf4_calls

// DECOMP_FUNC(0x00191cf4, 440)
extern "C" void camp_func_00191cf4() {
    using namespace camp_191cf4_calls;

    u8* const camp = *reinterpret_cast<u8**>(0x0043DD68u);
    u8* const cfg = static_cast<u8*>(camp_func_002a0fac());
    const u8* const slot = (camp[0x420] == 1) ? (cfg + 0x12) : (cfg + 0x11);
    const u32 asc = ((*slot & 0x80u) == 0) ? 1u : 0u;
    void* const list = camp + 0x6278;

    if ((*slot & 0x7Fu) == 1u) {
        const s32 count = *reinterpret_cast<const s32*>(camp + 0x6670);
        func_002b7f0a(list, count, 2, (asc != 0) ? 0x00207280u : 0x002E4ABCu);
    }
    if ((*slot & 0x7Fu) == 2u) {
        const s32 count = *reinterpret_cast<const s32*>(camp + 0x6670);
        func_002b7f0a(list, count, 2, (asc != 0) ? 0x001D1C78u : 0x002C6E04u);
    }
    if ((*slot & 0x7Fu) == 0x31u) {
        const s32 count = *reinterpret_cast<const s32*>(camp + 0x6670);
        func_002b7f0a(list, count, 2, (asc != 0) ? 0x00219624u : 0x002F2878u);
    }
    if ((*slot & 0x7Fu) == 3u) {
        const s32 count = *reinterpret_cast<const s32*>(camp + 0x6670);
        func_002b7f0a(list, count, 2, (asc != 0) ? 0x001F643Cu : 0x002DCEACu);
    }
}

namespace engine_1b4664_calls {
extern "C" void* AsdMemory_func_002c23f8_call(u32 size)
    __asm__("_ZN4smt46engine23AsdMemory_func_002c23f8Ej");
extern "C" void ui_func_00294a98(void* obj);
} // namespace engine_1b4664_calls

// DECOMP_FUNC(0x001b4664, 440)
extern "C" void engine_func_001b4664() {
    using namespace engine_1b4664_calls;

    u8* const p = *reinterpret_cast<u8**>(0x00447E88u);
    *reinterpret_cast<u32*>(p + 0x00) = 0;
    *reinterpret_cast<u32*>(p + 0x04) = 0;
    *reinterpret_cast<u32*>(p + 0x08) = 0;
    p[0x10] = 0;
    *reinterpret_cast<f32*>(p + 0x14) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x1C) = 10.0f;
    *reinterpret_cast<f32*>(p + 0x20) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x24) = 10.0f;
    *reinterpret_cast<f32*>(p + 0x28) = 10.0f;
    *reinterpret_cast<f32*>(p + 0x2C) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x30) = 10.0f;
    *reinterpret_cast<f32*>(p + 0x40) = 10.0f;
    *reinterpret_cast<f32*>(p + 0x44) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x48) = 10.0f;
    *reinterpret_cast<f32*>(p + 0x4C) = -90.0f;
    *reinterpret_cast<f32*>(p + 0x50) = -90.0f;
    *reinterpret_cast<f32*>(p + 0x68) = 0.0f;
    p[0x6C] = 0;
    *reinterpret_cast<u32*>(p + 0x54) = 0;
    *reinterpret_cast<f32*>(p + 0x58) = 5.0f;
    p[0x5C] = 0;
    *reinterpret_cast<u32*>(p + 0x60) = 0;
    *reinterpret_cast<u32*>(p + 0x70) = 0;
    *reinterpret_cast<f32*>(p + 0x74) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x78) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x7C) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x80) = 0.0f;
    *reinterpret_cast<u32*>(p + 0x84) = 0;
    p[0x88] = 0;
    *reinterpret_cast<u32*>(p + 0x90) = 0;
    *reinterpret_cast<f32*>(p + 0x94) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x15C) = 100.0f;
    *reinterpret_cast<f32*>(p + 0x160) = 1000.0f;
    p[0x134] = 1;

    u32* const obj = static_cast<u32*>(AsdMemory_func_002c23f8_call(0x100));
    if (obj != nullptr) {
        ui_func_00294a98(obj);
        obj[0] = 0x00420420u;
    }

    u8* const p2 = *reinterpret_cast<u8**>(0x00447E88u);
    *reinterpret_cast<void**>(p2 + 0x194) = obj;
    p2[0x198] = 0;
    *reinterpret_cast<u32*>(p2 + 0x19C) = 0;
    *reinterpret_cast<u32*>(p2 + 0x1A0) = 0;
    *reinterpret_cast<u32*>(p2 + 0x1A4) = 0;
    *reinterpret_cast<u32*>(p2 + 0x1A8) = 0;
    *reinterpret_cast<u32*>(p2 + 0x1AC) = 0;
    *reinterpret_cast<u32*>(p2 + 0x1B0) = 0;
    *reinterpret_cast<u16*>(p2 + 0x1B4) = 0;
    *reinterpret_cast<u16*>(p2 + 0x1B6) = 0;
    *reinterpret_cast<u16*>(p2 + 0x1B8) = 0;
    *reinterpret_cast<u32*>(p2 + 0x164) = 0;
    *reinterpret_cast<u32*>(p2 + 0x188) = 0;
    *reinterpret_cast<u32*>(p2 + 0x174) = 0;
    *reinterpret_cast<u32*>(p2 + 0x178) = 0;
    *reinterpret_cast<u32*>(p2 + 0x17C) = 0;
    p2[0x180] = 0;
    p2[0x181] = 0;
    p2[0x182] = 0;
    p2[0x183] = 0;
    p2[0x184] = 0;
    *reinterpret_cast<u32*>(p2 + 0x18C) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(p2 + 0x170) = 0;
    *reinterpret_cast<u32*>(p2 + 0x190) = 0;

    u8* const g = reinterpret_cast<u8*>(0x0049FA1Cu);
    g[0x7C] = 0;
    *reinterpret_cast<f32*>(g + 0x80) = 0.0f;
    *reinterpret_cast<f32*>(g + 0x84) = 0.0f;
    *reinterpret_cast<f32*>(g + 0x88) = 0.0f;
    *reinterpret_cast<f32*>(g + 0x8C) = 0.0f;
    *reinterpret_cast<u16*>(g + 0x94) = 0;
    g[0x98] = 0;
    g[0x99] = 0;
    g[0x9A] = 0;
    g[0xA0] = 0;
    *reinterpret_cast<u32*>(g + 0xA4) = 0;
    *reinterpret_cast<f32*>(g + 0xA8) = 0.0f;
    *reinterpret_cast<f32*>(g + 0xAC) = 0.0f;
    *reinterpret_cast<f32*>(g + 0xB0) = 0.0f;
    *reinterpret_cast<f32*>(g + 0xB4) = 0.0f;
}

// DECOMP_FUNC(0x0034bb5c, 444)
namespace ui_34bb5c_calls {
extern "C" s32 ui_func_00297004(u32 a0, s32 a1);
extern "C" u32 engine_func_002c0bcc(u32 a0);
extern "C" f32 ui_func_002b73a4(f32 angle);
extern "C" f32 ui_func_002b740c(f32 angle);
} // namespace ui_34bb5c_calls

extern "C" void ui_func_0034bb5c(u8* self) {
    using namespace ui_34bb5c_calls;

    void* const p14 = *reinterpret_cast<void**>(self + 0x14);
    u8* const vtbl = *reinterpret_cast<u8**>(p14);
    (*reinterpret_cast<void (**)(void*)>(vtbl + 0x0C))(p14);

    const u32* const cfg = *reinterpret_cast<const u32**>(self + 0x1C);
    u32* const dst = *reinterpret_cast<u32**>(self + 0x04);
    dst[0x0C / 4] = cfg[0];
    dst[0x10 / 4] = cfg[1];
    dst[0x20 / 4] = cfg[0];
    dst[0x24 / 4] = cfg[3];
    dst[0x34 / 4] = cfg[2];
    dst[0x38 / 4] = cfg[1];
    dst[0x48 / 4] = cfg[2];
    dst[0x4C / 4] = cfg[3];

    const s32 count = *reinterpret_cast<const s32*>(
        reinterpret_cast<const u8*>(cfg) + 0x2C);
    for (s32 i = 0; i < count; ++i) {
        const u8* const cbytes = *reinterpret_cast<const u8**>(self + 0x1C);
        u8* const arr = *reinterpret_cast<u8**>(self + 0x18);
        const u32 stride = static_cast<u32>(i) * 0x50u;
        *reinterpret_cast<u32*>(arr + stride + 0x4C) =
            *reinterpret_cast<const u32*>(cbytes + 0x30) * static_cast<u32>(i);

        const s32 r_scale = ui_func_00297004(0xFFFF8001u, 0x8000);
        const u8* const cbytes2 = *reinterpret_cast<const u8**>(self + 0x1C);
        const f32 min_s = *reinterpret_cast<const f32*>(cbytes2 + 0x24);
        const f32 max_s = *reinterpret_cast<const f32*>(cbytes2 + 0x28);
        const f32 scale =
            min_s + (max_s - min_s) * (static_cast<f32>(r_scale) * 3.0517578125e-05f);

        const u32 r_ang = engine_func_002c0bcc(0xFFFFu);
        const f32 angle = (static_cast<f32>(r_ang) * 1.52587890625e-05f) * 256.0f;
        const f32 cval = ui_func_002b73a4(angle);
        const f32 sval = ui_func_002b740c(angle);

        f32* const vec = reinterpret_cast<f32*>(
            *reinterpret_cast<u8**>(self + 0x18) + stride + 0x40);
        vec[0] = cval;
        vec[1] = sval;
        vec[2] = 0.0f;

        f32* const vec2 = reinterpret_cast<f32*>(
            *reinterpret_cast<u8**>(self + 0x18) + stride + 0x40);
        vec2[0] = vec2[0] * scale;
        vec2[1] = vec2[1] * scale;
        vec2[2] = vec2[2] * scale;
    }
}

// DECOMP_FUNC(0x00352974, 444)
//
// Resolves a UI icon resource from a 64-bit key pair. The zero key selects a
// fixed default directly. Any other key formats the UTF-8 icon name
// "/icons/%u.icn" from the caller-supplied id, widens it to UTF-16 while
// counting code units, and asks the resource table for a holder. The lookup
// status then selects one of three outcomes: the special default icon, an
// encoded status value, or the result of a second virtual lookup that is
// invoked only when the status is non-negative and not the special icon tag.
// The 64-bit result is written through `out`; both verified callers ignore the
// incidental r0/r1 values left at return.
namespace ui_352974_calls {
extern "C" u64* engine_func_002bad80(u64* out, u32 code);
extern "C" s32 ui_func_0023a2ec(u8* dst, u32 capacity, const char* format,
                                u32 value);
extern "C" u32 ui_func_002acb3c(u16* dst, const u8* utf8, u32 capacity);
extern "C" u32 ui_func_002b5c2c(const u16* text);
extern "C" s32 ui_func_00355f78(u32* holder, u32 id_low, u32 id_high,
                                const u32* descriptor, u32 flag);
extern "C" s32 ui_func_002a4df0(u8* dst, u32 holder, u32 a2, u32 a3,
                                u32 stack0, u32 stack1);
extern "C" void engine_func_002b93f0(void* object);

constexpr u32 kZeroKeyDefault = 0xE0A13882u;
constexpr u32 kSpecialIcon = 0xD881388Cu;
constexpr u32 kIconStatusTag = 0x11u;
constexpr u32 kIconIndexMin = 100u;
constexpr u32 kIconIndexMax = 179u;
constexpr u32 kDescriptorType = 4u;
constexpr u32 kLookupFlag = 1u;
constexpr u32 kSecondLookupStack1 = 0x1200u;
constexpr char kIconFormat[] = "/icons/%u.icn";
} // namespace ui_352974_calls

extern "C" void ui_func_00352974(u8* out, const u32* key, u32 a2, u32 a3) {
    using namespace ui_352974_calls;

    if (key[0] == 0 && key[1] == 0) {
        engine_func_002bad80(reinterpret_cast<u64*>(out), kZeroKeyDefault);
        return;
    }

    // Layout matches the original frame: UTF-8 scratch at sp+0x78, its UTF-16
    // widening at sp+8, the descriptor at sp+0x68 and the holder at sp+0x74.
    u8 utf8[0x30];
    u16 text[0x30];
    u32 descriptor[3];
    u32 holder;

    ui_func_0023a2ec(utf8, static_cast<u32>(sizeof(utf8)), kIconFormat, a3);
    ui_func_002acb3c(text, utf8,
                     static_cast<u32>(sizeof(text) / sizeof(text[0])));

    holder = 0;
    const u32 id_low = key[0];
    const u32 id_high = key[1];

    descriptor[1] = reinterpret_cast<u32>(text);
    descriptor[0] = kDescriptorType;
    const u32 units = ui_func_002b5c2c(text);
    descriptor[2] = (units + 1) * 2;

    const s32 status =
        ui_func_00355f78(&holder, id_low, id_high, descriptor, kLookupFlag);

    u64 value;
    u64 alt;
    u64 second_dst;

    const u32 status_bits = static_cast<u32>(status);
    const u32 status_index = status_bits & 0x3FFu;
    const bool special_icon =
        ((status_bits & 0x3FC00u) >> 10) == kIconStatusTag &&
        status_index >= kIconIndexMin && status_index <= kIconIndexMax;

    const u8* source;
    if (special_icon) {
        engine_func_002bad80(&value, kSpecialIcon);
        source = reinterpret_cast<const u8*>(&value);
    } else if (status < 0) {
        engine_func_002bad80(&value, status_bits);
        source = reinterpret_cast<const u8*>(&value);
    } else {
        // The two outgoing stack words occupy the same frame slots that later
        // receive the second lookup result; only the passed values matter.
        u32* const call_words = reinterpret_cast<u32*>(&value);
        call_words[0] = a2;
        call_words[1] = kSecondLookupStack1;
        const s32 second = ui_func_002a4df0(
            reinterpret_cast<u8*>(&second_dst), holder, 0, 0,
            call_words[0], call_words[1]);
        if (second < 0) {
            engine_func_002bad80(&value, static_cast<u32>(second));
            source = reinterpret_cast<const u8*>(&value);
        } else {
            engine_func_002bad80(&alt, 0);
            source = reinterpret_cast<const u8*>(&alt);
        }
    }

    if (holder != 0) {
        engine_func_002b93f0(reinterpret_cast<void*>(holder));
    }

    *reinterpret_cast<u64*>(out) = *reinterpret_cast<const u64*>(source);
}

// DECOMP_FUNC(0x0025b6e8, 448)
namespace engine_25b6e8_calls {
extern "C" f32 func_0024bd60(s32 a0, s32 a1, const void* elem,
                             f32 x, f32 y, f32 z, f32 limit);
} // namespace engine_25b6e8_calls

extern "C" s32 engine_func_0025b6e8(const f32* p0, const f32* p1, f32* out) {
    using namespace engine_25b6e8_calls;

    const u8* const g = reinterpret_cast<const u8*>(0x00446FE8u);
    const f32 x0 = p0[0];
    const f32 y0 = p0[1];
    const f32 z0 = p0[2];
    const f32 x1 = p1[0];
    const f32 y1 = p1[1];
    const f32 z1 = p1[2];

    for (s32 pass = 2; pass < 4; ++pass) {
        const s32 count = *reinterpret_cast<const s32*>(
            g + ((pass == 2) ? 0x0Cu : 0x10u));
        const u8* const base = *reinterpret_cast<const u8* const*>(
            g + ((pass == 2) ? 0x20u : 0x24u));

        for (s32 i = 0; i < count; ++i) {
            const u8* const elem = base + i * 0xA8;
            if (elem[8] == 0) {
                continue;
            }

            const f32* const plane = reinterpret_cast<const f32*>(elem + 0x0C);
            const f32 d0 = x0 * plane[0] + y0 * plane[1] + z0 * plane[2] - plane[3];
            const f32 d1 = x1 * plane[0] + y1 * plane[1] + z1 * plane[2] - plane[3];

            const bool crosses =
                (d0 >= 0.0f && d1 < 0.0f) || (d0 < 0.0f && d1 >= 0.0f);
            if (!crosses) {
                continue;
            }

            const f32 ad0 = __builtin_fabsf(d0);
            const f32 ad1 = __builtin_fabsf(d1);
            const f32 denom = ad0 + ad1;
            const f32 t = ad0 / denom;
            const f32 hx = x0 + (x1 - x0) * t;
            const f32 hy = y0 + (y1 - y0) * t;
            const f32 hz = z0 + (z1 - z0) * t;

            const f32 dist = func_0024bd60(
                static_cast<s8>(elem[4]),
                static_cast<s8>(elem[5]),
                elem, hx, hy, hz, 10.0f);
            if (dist >= 0.0f) {
                if (out != nullptr) {
                    const f32 t2 = (ad0 + dist) / denom;
                    out[0] = x0 + (x1 - x0) * t2;
                    out[1] = y0 + (y1 - y0) * t2;
                    out[2] = z0 + (z1 - z0) * t2;
                }
                return i;
            }
        }
    }

    return -1;
}

// ---------------------------------------------------------------------------
// 0x00238ED4 (452 B): one-shot engine setup step, serialised by the recursive
// lock object at 0x004E629C and gated by the three state bytes at 0x004656CA.
//
//   flags[0] == 0  -> only a non-zero `engine_func_00239bec()` (the signed byte
//                     at 0x00472A40) lets the call continue; otherwise it
//                     returns the failure value without taking the lock.
//   flags[1] == 0  -> nothing has been initialised yet: unlock and return
//                     0xC8A10BF0 (the same sentinel as the sibling setup
//                     routine at 0x00357A3C).
//   flags[2] == 0  -> run the one-shot driver `func_0035b0a4(0)`; a negative
//                     Result unlocks and returns that Result, otherwise the
//                     0x00F42400 (16,000,000) tick deadline is armed and
//                     flags[2] is set to 1.
//   mode != 0      -> allocate the kind-selected engine slot (0x0C when the
//                     kind word is non-zero, 0x0B otherwise) and return it.
//   mode == 0      -> allocate the same slot, then poll the `svc #0x25`
//                     trampoline at 0x002C42FC up to 62 times before closing
//                     the returned kernel handle with `svc #0x23`.
//
// The poll loop only continues while the trampoline Result shifted left by 22
// equals 0xFF800000 (i.e. its low ten bits are 0x3FE) and the 0x00359088 wait
// helper did not report status 1; after 62 bodies the failure value is
// returned.  A negative trampoline Result is reported through 0x002C5468 and
// execution continues (the reporter is non-returning in the real engine).
// ---------------------------------------------------------------------------
namespace engine_238ed4_calls {
extern "C" s8 engine_func_00239bec();                    // 0x00239BEC
extern "C" u32 func_00239bb0(u32 index);                 // 0x00239BB0
extern "C" void engine_func_002c3aa8(void* a0);          // 0x002C3AA8 enter
extern "C" void engine_func_002c3a24(void* a0);          // 0x002C3A24 leave
extern "C" u32 func_0035b0a4(u32 index);                 // 0x0035B0A4
extern "C" void camp_func_002bb490(u64 nanos);           // 0x002BB490
// 0x002C42FC: `svc #0x25` trampoline; stores the kernel's r1 into `out_idx`.
extern "C" s32 engine_func_002c42fc(u32* out_idx, u32* handles, s32 count,
                                    u32 wait_all, s64 timeout);
extern "C" void engine_func_002c5468(s32 err);           // 0x002C5468 fatal
extern "C" u32 func_00359288(u32* out_value);            // 0x00359288 wait
extern "C" u32 func_00359088(u32* out_value);            // 0x00359088 wait
} // namespace engine_238ed4_calls

// DECOMP_FUNC(0x00238ed4, 452)
extern "C" u32 engine_func_00238ed4(u32 kind, u32 mode) {
    using namespace engine_238ed4_calls;

    constexpr u32 kFailure = 0xC8A10BF0u;
    constexpr u32 kWaitIterationLimit = 0x3Cu;

    u8* const flags = reinterpret_cast<u8*>(0x004656CAu);
    void* const lock = reinterpret_cast<void*>(0x004E629Cu);

    if (flags[0] == 0 && engine_func_00239bec() == 0) {
        return kFailure;
    }

    engine_func_002c3aa8(lock);

    if (flags[1] == 0) {
        engine_func_002c3a24(lock);
        return kFailure;
    }

    if (flags[2] == 0) {
        const u32 setup_rc = func_0035b0a4(0);
        if ((setup_rc & 0x80000000u) != 0) {
            engine_func_002c3a24(lock);
            return setup_rc;
        }
        camp_func_002bb490(0x00F42400u);
        flags[2] = 1;
    }

    u32 handle = 0;
    if (mode == 0) {
        // 0x00359288 writes one word; a negative Result discards it and leaves
        // the handle at zero.
        if ((func_00359288(&handle) & 0x80000000u) != 0) {
            handle = 0;
        }
    }

    u32 result = func_00239bb0((kind != 0) ? 0x0Cu : 0x0Bu);

    if (mode == 0) {
        for (s32 iteration = 0;; ++iteration) {
            u32 key_out = 0;
            const s32 wait_rc = engine_func_002c42fc(
                &key_out, &handle, 1, 0, static_cast<s64>(0x3B9ACA00u));
            if (wait_rc < 0) {
                engine_func_002c5468(wait_rc);
            }
            if ((static_cast<u32>(wait_rc) << 22) != 0xFF800000u) {
                break;
            }

            u32 status = 0;
            func_00359088(&status);
            if (status == 1) {
                break;
            }
            if (iteration > static_cast<s32>(kWaitIterationLimit)) {
                result = kFailure;
                break;
            }
        }

        if (handle != 0) {
            // 0x00239064: `movs r0, r4; svcne #0x23` = svcCloseHandle(handle).
            register u32 handle_reg asm("r0") = handle;
            asm volatile("svc 0x23" : "+r"(handle_reg) : : "r1", "r2", "r3");
        }
    }

    engine_func_002c3a24(lock);
    return result;
}

// DECOMP_FUNC(0x00245e78, 452)
namespace ui_245e78_calls {
extern "C" void* ui_func_00293c98();
extern "C" const u8* ui_func_00282b94(void* p, u32 a0);
extern "C" void ui_func_002be7fc(char* dst, const char* fmt, ...);
extern "C" u32 script_vm_func_0023ec3c(u32 max_val);
} // namespace ui_245e78_calls

extern "C" u32 ui_func_00245e78(u32 a0, s32 kind) {
    using namespace ui_245e78_calls;

    const u8* const row = ui_func_00282b94(ui_func_00293c98(), a0);

    f32 base = 0.0f;
    s32 slot = 0;
    const char* fmt = nullptr;
    if (kind == 3) {
        base = 5.0f;
        slot = 0x19;
        fmt = "\x8d\x8f\x88\xf3";
    } else if (kind == 6) {
        base = 25.0f;
        slot = 0x17;
        fmt = "\x8d\xac\x97\x90";
    } else if (kind == 7) {
        base = 30.0f;
        slot = 0x16;
        fmt = "\x90\x87\x96\xb0";
    } else if (kind == 8) {
        base = 20.0f;
        slot = 0x18;
        fmt = "\x8b\xd9\x94\x9b";
    } else {
        return 1u;
    }

    const s16 stat = *reinterpret_cast<const s16*>(row + 0x1C4);
    const u8* const row2 = ui_func_00282b94(ui_func_00293c98(), a0);
    const s16 bonus = (row2 != nullptr)
        ? *reinterpret_cast<const s16*>(row2 + slot * 2 + 0x72)
        : 0;

    f32 rate = base + (base * static_cast<f32>(stat)) * 0.01f;
    if (rate > 80.0f) {
        rate = 80.0f;
    }
    rate += static_cast<f32>(bonus) * 20.0f;

    char buf[32] = {};
    ui_func_002be7fc(buf, fmt);

    const u32 roll = script_vm_func_0023ec3c(0x63u);
    return (static_cast<f32>(roll) >= rate) ? 0u : 1u;
}

// DECOMP_FUNC(0x0027af3c, 452)
namespace script_vm_27af3c_calls {
extern "C" void battle_func_00267420(s32 a0, f32 f0, f32 f1, f32 f2,
                                     f32 f3, f32 f4, f32 f5, f32 f6);
} // namespace script_vm_27af3c_calls

extern "C" void script_vm_func_0027af3c() {
    using namespace script_vm_27af3c_calls;

    for (s32 i = 0; i < 24; ++i) {
        const u8* const base = *reinterpret_cast<const u8* const*>(0x00447A48u);
        const u8* const elem = base + i * 40 + 0x1C;
        if (elem[0] == 0) {
            continue;
        }

        const u16 kind = *reinterpret_cast<const u16*>(elem + 0x16);
        const f32* const f = reinterpret_cast<const f32*>(elem + 4);
        const s32 arg0 = *reinterpret_cast<const s16*>(elem + 0x1C);

        if (kind == 0x10u) {
            battle_func_00267420(arg0, f[0], f[1], f[2], f[3], 500.0f, 300.0f, 15.0f);
        } else if (kind == 0x0Au) {
            battle_func_00267420(arg0, f[0], f[1], f[2], f[3], 1000.0f, 300.0f, 15.0f);
        } else if (kind == 0x0Bu) {
            battle_func_00267420(arg0, f[0], f[1], f[2], f[3], 500.0f, 300.0f, 15.0f);
        } else if (kind == 0x0Cu) {
            battle_func_00267420(arg0, f[0], f[1], f[2], f[3], 600.0f, 350.0f, 160.0f);
        } else if (kind == 0x17u) {
            battle_func_00267420(arg0, f[0], f[1], f[2], f[3], 1100.0f, 600.0f, 60.0f);
        } else if (kind == 0x15u) {
            battle_func_00267420(arg0, f[0], f[1], f[2], f[3], 600.0f, 600.0f, 60.0f);
        } else if (kind == 0x14u) {
            battle_func_00267420(arg0, f[0], f[1], f[2], f[3], 600.0f, 600.0f, 80.0f);
        }
    }
}

// ---------------------------------------------------------------------------
// 0x0028277c (456 B): single-precision sine, matching the pinned libm routine
// (ledger name script_vm_func_0028277c).
//
//   * |x| < pi/4         : minimax sine/cosine on x itself; quadrant = -1 when
//                          |x| < 2^-12 so the caller returns x unchanged.
//   * pi/4 <= |x| < 12867.5712890625 : inline q = round(x*2/pi) through the
//                          2^23 magic and r = x - q*(pi/2) split into four
//                          Horner terms.
//   * larger, or non-finite : the generic reduction helper fills *quadrant and
//                          returns r; it stores -1 and leaves r = x for
//                          non-finite inputs.
//   * quadrant 0/1/2/3 selects sin(r)/cos(r)/-sin(r)/-cos(r).
//   * tiny inputs return x; subnormals additionally run the discarded
//     underflow probe; infinities set *__errno_location() = 1 and return the
//     VFP default NaN (0/0); NaN propagates through x + x.
//
// All direct calls are libm-internal helpers of the pinned image.  Their
// declarations live in engine_28277c_calls; the polynomial coefficients are
// written by value with static_assert checks against the pinned bit patterns.
// ---------------------------------------------------------------------------
namespace engine_28277c {
constexpr u32 F32ToBits(f32 value) noexcept {
    return __builtin_bit_cast(u32, value);
}

// Magnitudes compared as (bits << 1), which drops the sign bit.
constexpr u32 kPiOverFourShift = 0x7E921FB6u;  // (bits of pi/4) << 1
constexpr u32 kTinyShift = 0x73000000u;        // (bits of 2^-12) << 1
constexpr u32 kReductionLimit = 0x46490E49u;   // bits of 12867.5712890625f
constexpr u32 kInfinityShift = 0xFF000000u;    // (bits of +inf) << 1

constexpr f32 kTwoOverPi = 0.6366197466850281f;        // 0x3F22F983
constexpr f32 kRoundMagic = 8388608.0f;                // 0x4B000000
constexpr f32 kHalfPiPart0 = 1.5703125f;               // 0x3FC90000
constexpr f32 kHalfPiPart1 = 0.0004837512969970703f;   // 0x39FDA000
constexpr f32 kHalfPiPart2 = 7.549533620476723e-08f;   // 0x33A22000
constexpr f32 kHalfPiPart3 = 2.5633440682570896e-12f;  // 0x2C34611A

// sin(r) = r + r^3 * (C2 + r^2 * (C0 - r^2 * C1))
constexpr f32 kSinC0 = 0.00833197869360447f;      // 0x3C0882DA
constexpr f32 kSinC1 = 0.000194956359337084f;     // 0x394C6D33
constexpr f32 kSinC2 = -0.16666650772094727f;     // 0xBE2AAAA0
// cos(r) = 1 + r^2 * (C2 + r^2 * (C1 + r^2 * C0))
constexpr f32 kCosC0 = -0.0013597822980955243f;   // 0xBAB23AB9
constexpr f32 kCosC1 = 0.04165629297494888f;      // 0x3D2A9FCA
constexpr f32 kCosC2 = -0.49999895691871643f;     // 0xBEFFFFDD

static_assert(F32ToBits(kTwoOverPi) == 0x3F22F983u);
static_assert(F32ToBits(kRoundMagic) == 0x4B000000u);
static_assert(F32ToBits(kHalfPiPart0) == 0x3FC90000u);
static_assert(F32ToBits(kHalfPiPart1) == 0x39FDA000u);
static_assert(F32ToBits(kHalfPiPart2) == 0x33A22000u);
static_assert(F32ToBits(kHalfPiPart3) == 0x2C34611Au);
static_assert(F32ToBits(kSinC0) == 0x3C0882DAu);
static_assert(F32ToBits(kSinC1) == 0x394C6D33u);
static_assert(F32ToBits(kSinC2) == 0xBE2AAAA0u);
static_assert(F32ToBits(kCosC0) == 0xBAB23AB9u);
static_assert(F32ToBits(kCosC1) == 0x3D2A9FCAu);
static_assert(F32ToBits(kCosC2) == 0xBEFFFFDDu);
}  // namespace engine_28277c

namespace engine_28277c_calls {
// 0x002A4600 (44 B): classifies an IEEE-754 single bit pattern in r0.
// Returns 0 zero, 3 infinity, 4 subnormal, 5 finite normal, 7 NaN.
extern "C" u32 ui_func_002a4600(u32 value_bits);
// 0x002A462C (16 B): square of a constant that underflows to +0.0f; the
// result is discarded and only the underflow probe is observable.
extern "C" f32 ui_func_002a462c(f32 value);
// 0x003EB4F4 (296 B): generic range reduction of the bits in r1.  Writes the
// quadrant (0..3, or 0xFFFFFFFF when non-finite) through out_integer and
// returns the reduced angle in s0, leaving s0 untouched when non-finite.
extern "C" f32 ui_func_003eb4f4(u32* out_integer, u32 value_bits);
// 0x002A464E (Thumb, 12 B): stores its argument through *__errno_location().
extern "C" s32* func_002a464e_errno_set(s32 value);
}  // namespace engine_28277c_calls

// The C symbol keeps its historical name for the callers that take its
// address; the differing C++ spelling avoids clashing with the historical
// void() declaration used by engine_func_002d4fe0.  That declaration is
// repeated here because this block precedes its original occurrence.
extern "C" void script_vm_func_0028277c();
extern "C" f32 sin_0028277c(f32 x) __asm__("script_vm_func_0028277c");

// DECOMP_FUNC(0x0028277c, 456)
extern "C" f32 sin_0028277c(f32 x) {
    using namespace engine_28277c;
    using namespace engine_28277c_calls;

    const u32 bits = F32ToBits(x);
    s32 quadrant;
    f32 reduced;

    if ((bits << 1) >= kPiOverFourShift) {
        if ((bits & 0x7FFFFFFFu) >= kReductionLimit) {
            reduced = ui_func_003eb4f4(reinterpret_cast<u32*>(&quadrant), bits);
        } else {
            // q = round-to-nearest(x * 2/pi) using the 2^23 add/subtract trick;
            // the sign of x picks the subtraction direction.
            const f32 scaled = x * kTwoOverPi;
            f32 rounded;
            if ((bits & 0x80000000u) != 0) {
                const f32 biased = scaled - kRoundMagic;
                rounded = biased + kRoundMagic;
            } else {
                const f32 biased = scaled + kRoundMagic;
                rounded = biased - kRoundMagic;
            }
            quadrant = static_cast<s32>(rounded) & 3;

            // r = x - q*(pi/2), each pi/2 part subtracted with one rounding.
            reduced = x - rounded * kHalfPiPart0;
            reduced = reduced - rounded * kHalfPiPart1;
            reduced = reduced - rounded * kHalfPiPart2;
            reduced = reduced - rounded * kHalfPiPart3;
        }
    } else {
        quadrant = ((bits << 1) < kTinyShift) ? -1 : 0;
        reduced = x;
    }

    if (quadrant < 0) {
        const u32 magnitude = F32ToBits(reduced) << 1;
        if (magnitude > kInfinityShift) {
            return reduced + reduced;  // NaN propagates through VADD
        }
        if (magnitude == kInfinityShift) {
            (void)func_002a464e_errno_set(1);  // *__errno_location() = EDOM
            volatile f32 zero = 0.0f;
            return zero / zero;  // VFP default NaN
        }
        if (ui_func_002a4600(F32ToBits(reduced)) == 4u) {
            (void)ui_func_002a462c(reduced);
        }
        return reduced;
    }

    const f32 square = reduced * reduced;
    if ((quadrant & 1) != 0) {
        f32 poly = kCosC1 + square * kCosC0;
        poly = kCosC2 + square * poly;
        f32 cosine = 1.0f + square * poly;
        if ((quadrant & 2) != 0) {
            cosine = -cosine;
        }
        return cosine;
    }

    f32 poly = kSinC0 - square * kSinC1;
    poly = kSinC2 + square * poly;
    const f32 sine = reduced + reduced * (poly * square);
    if ((quadrant & 2) != 0) {
        return -sine;
    }
    return sine;
}

// ---------------------------------------------------------------------------
// 0x0012FBF4 (464 B): rebuilds the two-slot pursuit table and the clamped
// fractional pair of one engine object.
//
// Fields read from self (r0):
//   +0x0C u32, +0x10 u32, +0x14 u32   (each converted with VCVT.F32.U32)
//   +0x18 f32, +0x1C f32, +0x24 f32, +0x28 f32
//   +0x2D u8  mirror selector (0 = direct, 1 = mirrored)
//   +0x30 u32, +0x34 u32              zero-fill pointer and length (tail call)
//   +0x38 u32, +0x3C u32              copied to +0xB4 / +0xB8
//   +0x40 u32                         copied to +0xCC
//
// The +0x0C and +0x14 unsigned integers are clamped up to 4.888f
// (0x409C6A7F) before being scaled by 0.20458264648914337f (0x3E517E1D); the
// truncated product times 160 is stored as the pair {value, 0} at +0xA4 and
// +0xAC respectively.
//
// Both +0xB4 entries (loaded from +0x38/+0x3C) are converted signed and fed to
// powf(10.0f, value * -3.0f / scale), where
//   scale = ((f32)(u32)self[+0x10] * 0.001f) * 32728.0f
// and the truncated result times 128.0f is stored at +0xC4 / +0xC8.
//
// The +0x1C field is clamped down to 0.95f (bit pattern 0x3F733333) with a
// signed bit-pattern compare.  The +0xF0/+0xF4 pair is then either mirrored
// (self[+0x2D] == 1: {(a - 1)*128, a * -128}) or direct
// ({(1 - a)*128, a * 128}).  These stores come after the +0xCC/+0xD0,
// +0xD4, +0xE8 and +0xEC stores, exactly as in the original schedule.
//
// The only call in the live body is the powf helper; the epilogue releases the
// callee-saved registers and tail-calls the requested-size zero-fill routine
// with r0 = self[+0x30] and r1 = self[+0x34].
//
// The 464-byte extent includes the literal pool at 0x0012FD94..0x0012FDC0.
// ---------------------------------------------------------------------------
namespace engine_12fbf4 {
constexpr u32 F32ToBits(f32 value) noexcept {
    return __builtin_bit_cast(u32, value);
}

// Literal pool constants (0x0012FD94..0x0012FDC0).
constexpr f32 kMinLength = 4.888000011444092f;        // 0x409C6A7F
constexpr f32 kSlotStep = 0.20458264648914337f;       // 0x3E517E1D
constexpr f32 kThousandth = 0.0010000000474974513f;   // 0x3A83126F
constexpr f32 kScaleCeiling = 32728.0f;               // 0x46FFB000
constexpr f32 kExponentFactor = -3.0f;                // 0xC0400000
constexpr f32 kPowBase = 10.0f;                       // 0x41200000
constexpr f32 kResultScale = 128.0f;                  // 0x43000000
constexpr f32 kMirrorScale = -128.0f;                 // 0xC3000000
constexpr f32 kRatioMax = 0.9499999880790710f;        // 0x3F733333
constexpr f32 kOne = 1.0f;                            // 0x3F800000

static_assert(F32ToBits(kMinLength) == 0x409C6A7Fu);
static_assert(F32ToBits(kSlotStep) == 0x3E517E1Du);
static_assert(F32ToBits(kThousandth) == 0x3A83126Fu);
static_assert(F32ToBits(kScaleCeiling) == 0x46FFB000u);
static_assert(F32ToBits(kExponentFactor) == 0xC0400000u);
static_assert(F32ToBits(kPowBase) == 0x41200000u);
static_assert(F32ToBits(kResultScale) == 0x43000000u);
static_assert(F32ToBits(kMirrorScale) == 0xC3000000u);
static_assert(F32ToBits(kRatioMax) == 0x3F733333u);
static_assert(F32ToBits(kOne) == 0x3F800000u);
}  // namespace engine_12fbf4

// 0x002B9CF8 (1908 B): single-precision powf(base, exponent).  Both operands
// arrive in s0/s1 and the result returns in s0.  The body is a self-contained
// argument-reduction implementation whose only calls are to the errno setter at
// 0x002A464E for pole/domain errors.
extern "C" f32 camp_func_002b9cf8(f32 base, f32 exponent);
// 0x002C3B48 (64 B): zero-fill of r1 bytes starting at r0 (the callee forces
// the fill value to zero).  The caller observes no return value.
extern "C" void engine_func_002c3b48(void* dst, u32 size);

// DECOMP_FUNC(0x0012fbf4, 464)
extern "C" void engine_func_0012fbf4(void* self_raw) {
    using namespace engine_12fbf4;

    u8* const self = static_cast<u8*>(self_raw);

    const auto load_u32 = [self](u32 offset) {
        return *reinterpret_cast<const u32*>(self + offset);
    };
    const auto store_u32 = [self](u32 offset, u32 value) {
        *reinterpret_cast<u32*>(self + offset) = value;
    };
    const auto load_f32 = [self](u32 offset) {
        return *reinterpret_cast<const f32*>(self + offset);
    };
    const auto store_f32 = [self](u32 offset, f32 value) {
        *reinterpret_cast<f32*>(self + offset) = value;
    };

    // +0xA4: slot size derived from the +0x0C unsigned count.  The converted
    // count is clamped up to kMinLength with a signed bit-pattern compare.
    {
        f32 length = static_cast<f32>(load_u32(0x0C));
        if (!(F32ToBits(length) > F32ToBits(kMinLength))) {
            length = kMinLength;
        }
        const u32 slots = static_cast<u32>(length * kSlotStep);
        store_u32(0xA4, slots * 160u);
        store_u32(0xA8, 0u);
    }

    // +0xAC: identical computation from the +0x14 unsigned count.
    {
        f32 length = static_cast<f32>(load_u32(0x14));
        if (!(F32ToBits(length) > F32ToBits(kMinLength))) {
            length = kMinLength;
        }
        const u32 slots = static_cast<u32>(length * kSlotStep);
        store_u32(0xAC, slots * 160u);
        store_u32(0xB0, 0u);
    }

    // +0xB4/+0xB8 are the +0x38/+0x3C pair, copied before the scale is built.
    const u32 pair_lo = load_u32(0x38);
    const u32 pair_hi = load_u32(0x3C);
    store_u32(0xB4, pair_lo);
    store_u32(0xB8, pair_hi);

    // Shared reciprocal-like scale for the two powf exponents.
    const f32 scale = (static_cast<f32>(load_u32(0x10)) * kThousandth) * kScaleCeiling;

    for (u32 i = 0; i < 2; ++i) {
        store_u32(0xBC + i * 4, 0u);
        const s32 raw = static_cast<s32>(load_u32(0xB4 + i * 4));
        const f32 exponent = (static_cast<f32>(raw) * kExponentFactor) / scale;
        const f32 result = camp_func_002b9cf8(kPowBase, exponent);
        store_u32(0xC4 + i * 4, static_cast<u32>(static_cast<s32>(result * kResultScale)));
    }

    // The +0x1C ratio is clamped down to kRatioMax using the signed ordering of
    // the IEEE-754 bit patterns, so negative values and the equality case are
    // left untouched.
    f32 ratio = load_f32(0x1C);
    if (static_cast<s32>(load_u32(0x1C)) > static_cast<s32>(0x3F733333u)) {
        ratio = kRatioMax;
    }

    const s32 scaled_24 = static_cast<s32>(load_f32(0x24) * kResultScale);
    const s32 scaled_28 = static_cast<s32>(load_f32(0x28) * kResultScale);
    const s32 scaled_18 = static_cast<s32>(load_f32(0x18) * kResultScale);

    store_u32(0xCC, load_u32(0x40));
    store_u32(0xD0, 0u);
    store_u32(0xE8, static_cast<u32>(scaled_24));
    store_u32(0xEC, static_cast<u32>(scaled_28));
    store_u32(0xD4, static_cast<u32>(scaled_18));

    if (self[0x2D] == 1u) {
        store_u32(0xF0, static_cast<u32>(static_cast<s32>((ratio - kOne) * kResultScale)));
        store_u32(0xF4, static_cast<u32>(static_cast<s32>(ratio * kMirrorScale)));
    } else {
        store_u32(0xF0, static_cast<u32>(static_cast<s32>((kOne - ratio) * kResultScale)));
        store_u32(0xF4, static_cast<u32>(static_cast<s32>(ratio * kResultScale)));
    }

    const void* const fill_target = reinterpret_cast<const void*>(load_u32(0x30));
    const u32 fill_size = load_u32(0x34);
    engine_func_002c3b48(const_cast<void*>(fill_target), fill_size);
}

// DECOMP_FUNC(0x0026eccc, 464)
extern "C" void engine_func_0026eccc(
    s32 axis, s32 vert_idx, f32* out_normal, f32* out_d,
    f32 px, f32 py, f32 pz,
    f32 ax, f32 ay, f32 az,
    f32 bx, f32 by, f32 bz) {
    struct Vec3 {
        f32 x;
        f32 y;
        f32 z;
    };

    Vec3 p0{};
    Vec3 p1{};
    Vec3 p2{};
    if (axis == 0) {
        p0 = { 0.0f, ay, az };
        p1 = { 0.0f, by, bz };
        p2 = { 10.0f, by, bz };
    } else if (axis == 1) {
        p0 = { ax, 0.0f, az };
        p1 = { bx, 0.0f, bz };
        p2 = { bx, 10.0f, bz };
    } else if (axis == 2) {
        p0 = { ax, ay, 0.0f };
        p1 = { bx, by, 0.0f };
        p2 = { bx, by, 10.0f };
    }

    const Vec3 v0 = { p1.x - p0.x, p1.y - p0.y, p1.z - p0.z };
    const Vec3 v1 = { p2.x - p1.x, p2.y - p1.y, p2.z - p1.z };

    const f32 cx = v0.y * v1.z - v0.z * v1.y;
    const f32 cy = v0.z * v1.x - v0.x * v1.z;
    const f32 cz = v0.x * v1.y - v0.y * v1.x;

    const f32 len_sq = cx * cx + cy * cy + cz * cz;
    f32 len = 0.0f;
    asm("vsqrt.f32 %0, %1" : "=t"(len) : "t"(len_sq));
    const f32 inv = 1.0f / len;
    auto clamp_eps = [](f32 v) -> f32 {
        return (v > -9.999999747378752e-05f && v < 9.999999747378752e-05f) ? 0.0f : v;
    };
    f32 nx = clamp_eps(cx * inv);
    f32 ny = clamp_eps(cy * inv);
    f32 nz = clamp_eps(cz * inv);

    const Vec3 pref = (vert_idx == 0) ? p0 : ((vert_idx == 1) ? p1 : p2);
    f32 d = nx * pref.x + ny * pref.y + nz * pref.z;
    const f32 dist = (px * nx + py * ny + pz * nz) - d;
    if (dist < 0.0f) {
        nx = -nx;
        ny = -ny;
        nz = -nz;
        d = nx * pref.x + ny * pref.y + nz * pref.z;
    }

    out_normal[0] = nx;
    out_normal[1] = ny;
    out_normal[2] = nz;
    *out_d = d;
}

// Row writer reached from func_0016ba30 (0x0016BA64, BA74, BA84, BA94) with a
// hand-written, non-AAPCS register contract:
//   r3   u16* destination cursor; advanced by every halfword store
//   r4   u32* source-index cursor; advanced by every index read
//   r6   u16 value placed in the "empty" positions (the call sites pass 0)
//   r7   base of the u32 lookup table (already offset to the selected row)
//   r8   number of leading empty halfwords (call sites use 0..3)
//   sl   byte stride added to the destination cursor after each store
// r0, r5, r10 and r11 are left untouched by the original; r9 (sb) and r12 (ip)
// are scratch. The last 16 bytes of the 476-byte ledger span (0x0016BA20) are
// the caller's literal pool, loaded with negative PC-relative offsets from
// func_0016ba30, not data of this helper.
//
// Behaviour: read 21 u32 indices, look up one u32 table word per index, and
// store its low halfword at destination positions lead + 3*k (k = 0..20).
// Every other one of the 64 positions receives `zero`. The 21 table stores are
// unrolled in the original (20 value/zero/zero triplets + one final value); the
// leading group and the 3 - lead trailing group are counted loops.
extern "C" u16* engine_stride_row_writer(const u32** src_cursor, u16* dst,
                                         u16 zero, const u32* table,
                                         u32 lead, u32 stride) {
    const u32* src = *src_cursor;
    u8* cursor = reinterpret_cast<u8*>(dst);

    auto store = [&](u16 value) {
        *reinterpret_cast<u16*>(cursor) = value;
        cursor += stride;
    };

    for (u32 i = 0; i < lead; ++i) {
        store(zero);
    }

    for (u32 i = 0; i < 20; ++i) {
        store(static_cast<u16>(table[*src++]));
        store(zero);
        store(zero);
    }

    store(static_cast<u16>(table[*src++]));

    // Unsigned 3 - lead mirrors `rsbs ip, r8, #3`: the callers use lead 0..3;
    // larger values make the original spin a 32-bit wrapping count.
    u32 tail = 3u - lead;
    while (tail != 0u) {
        store(zero);
        --tail;
    }

    *src_cursor = src;
    return reinterpret_cast<u16*>(cursor);
}

// DECOMP_FUNC(0x0016b854, 476)
extern "C" __attribute__((naked)) void func_0016b854() {
    asm volatile(
        ".arm\n"
        "push {r5, lr}\n"
        "sub  sp, sp, #24\n"
        "str  r0, [sp, #8]\n"
        "str  r4, [sp, #12]\n"
        "str  r8, [sp, #0]\n"
        "str  sl, [sp, #4]\n"
        "add  r0, sp, #12\n"
        "mov  r1, r3\n"
        "mov  r2, r6\n"
        "mov  r3, r7\n"
        "bl   engine_stride_row_writer\n"
        "mov  r3, r0\n"
        "ldr  r4, [sp, #12]\n"
        "ldr  r0, [sp, #8]\n"
        "add  sp, sp, #24\n"
        "pop  {r5, lr}\n"
        "bx   lr\n"
    );
}

// DECOMP_FUNC(0x00317cdc, 476)
namespace evttex_317cdc_calls {
extern "C" void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);
extern "C" void AsdMem_Zero(void* ptr, u32 size);
extern "C" const u8* AsdTable_FindBattleRow(u32 id);
extern "C" s32 AsdScene_LoadMode();
extern "C" void* Npc2d_CreateSprite(s32 sprite_id, u32 a1);
extern "C" void* AsdTask_CreateCalc(const char* name, u32 prio, u32 a2, u32 a3,
                                    void (*cb)(void*), u32 a5, u32 a6);
extern "C" void* AsdTask_CreateDraw(const char* name, u32 prio, u32 a2, u32 a3,
                                    void (*cb)(void*), u32 a5, u32 a6, void* parent);
} // namespace evttex_317cdc_calls

extern "C" void* decomp_func_00317cdc(u32 id, f32 x, f32 z)
    asm("3dEventTex_func_00317cdc");

extern "C" void* decomp_func_00317cdc(u32 id, f32 x, f32 z) {
    using namespace evttex_317cdc_calls;

    u8* const p = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, 0x48, 1));
    AsdMem_Zero(p, 0x48);

    *reinterpret_cast<f32*>(p + 0x08) = 1.0f;
    *reinterpret_cast<f32*>(p + 0x0C) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x10) = 0.25f;
    p[0x14] = 0;
    p[0x17] = 0;

    const u8* const row = AsdTable_FindBattleRow(id & 0xFFFFu);
    const s32 sprite_id = *reinterpret_cast<const s16*>(row + 0x88);
    *reinterpret_cast<s32*>(p + 0x38) = sprite_id;
    p[0x44] = 1;

    if (AsdScene_LoadMode() != 0) {
        *reinterpret_cast<u32*>(p + 0x04) = 1u;
    } else {
        *reinterpret_cast<void**>(p + 0x34) = Npc2d_CreateSprite(sprite_id, 1);
        *reinterpret_cast<u32*>(p + 0x04) = 2u;
    }

    *reinterpret_cast<u32*>(p + 0x00) = static_cast<u16>(0u - id);

    u32 pose = 5u;
    if (x <= -4.0f) {
        pose = 0x10u;
    } else if (x <= -3.0f) {
        pose = 3u;
    } else if (x >= 3.0f) {
        pose = 0x11u;
    } else if (x >= 1.5f) {
        pose = 4u;
    } else if (x < 0.0f) {
        pose = 0x12u;
    }
    *reinterpret_cast<u32*>(p + 0x3C) = pose;

    *reinterpret_cast<f32*>(p + 0x2C) = x;
    *reinterpret_cast<f32*>(p + 0x30) = z;
    p[0x16] = 1;
    p[0x15] = 0;

    void* const task = AsdTask_CreateCalc(
        "EVE_BtlTex", 2, 0, 0,
        reinterpret_cast<void (*)(void*)>(0x001DFFBCu),
        0x002DB938u,
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(p)));

    AsdTask_CreateDraw(
        "EVE_BtlTexDraw", 0x6Fu, 0, 0,
        reinterpret_cast<void (*)(void*)>(0x001E0138u),
        0,
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(p)),
        task);

    return task;
}

// DECOMP_FUNC(0x0015b5b8, 484)
extern "C" u32 AsdGpu_Address(const void* ptr);

extern "C" void engine_func_0015b5b8(u8* dst, const u8* src) {
    auto word_at = [](u8* base, u32 off) -> u32& {
        return *reinterpret_cast<u32*>(base + off);
    };
    auto cword_at = [](const u8* base, u32 off) -> u32 {
        return *reinterpret_cast<const u32*>(base + off);
    };
    auto rel_ptr = [](const u8* slot) -> const u8* {
        const s32 off = *reinterpret_cast<const s32*>(slot);
        return off != 0 ? (slot + off) : nullptr;
    };

    word_at(dst, 0x48u) = 0x38u;

    const u32 src_fmt = cword_at(src, 0x34u);
    word_at(dst, 0x10u) = (word_at(dst, 0x10u) & ~0xFu) | (src_fmt & 0xFu);
    word_at(dst, 0x1Cu) = (word_at(dst, 0x1Cu) & ~0x0FF00000u) | 0x00900000u;
    word_at(dst, 0x20u) = (word_at(dst, 0x20u) & 0xF800F800u)
                        | (cword_at(src, 0x18u) & 0x7FFu)
                        | ((cword_at(src, 0x1Cu) & 0x7FFu) << 16);

    word_at(dst, 0x24u) &= ~0x30u;
    if (src_fmt == 0xCu) {
        word_at(dst, 0x24u) |= 0x20u;
    }

    word_at(dst, 0x28u) &= ~0x000F0000u;
    word_at(dst, 0x2Cu) &= 0xF0000000u;
    for (u32 off = 0x30u; off <= 0x40u; off += 4u) {
        word_at(dst, off) &= ~0x003FFFFFu;
    }

    const u8* meta = rel_ptr(dst + 0x0Cu);
    const u32 meta_type = cword_at(meta, 0x08u) & 0xFFu;
    if (meta_type != 0u && meta_type != 1u) {
        word_at(dst, 0x28u) |= ((cword_at(src, 0x28u) - 1u) & 0xFu) << 16;
    }

    for (u32 i = 0u; i < 6u; ++i) {
        const u8* sub = rel_ptr(src + 0x38u + i * 4u);
        const u32 direct = cword_at(sub, 0x18u);
        const void* data_ptr = direct != 0u
            ? reinterpret_cast<const void*>(static_cast<std::uintptr_t>(direct))
            : static_cast<const void*>(rel_ptr(sub + 0x0Cu));
        const u32 gpu_addr = AsdGpu_Address(data_ptr);
        if (i == 0u) {
            word_at(dst, 0x2Cu) |= (gpu_addr & 0x7FFFFFFFu) >> 3;
        } else {
            word_at(dst, 0x2Cu + i * 4u) |= (gpu_addr >> 3) & 0xE03FFFFFu;
        }
    }
}

// DECOMP_FUNC(0x0012f768, 492)
extern "C" void engine_func_0013fdb0(void* elem, u32 zero);
extern "C" void* engine_func_002bb218();
extern "C" u32 engine_func_002bb0b4(void* obj, u32 mode);
extern "C" void engine_func_002b4d78(void* obj, u32 val);
extern "C" void func_001409b8(void* ptr);
extern "C" void func_002acb8c(void* field_ptr, u32 val, void* src_ptr);
extern "C" void func_002b4fa8(void* dst, u32 a, u32 b);

extern "C" void engine_func_0012f768(u8* obj) {
    auto word_at = [](u8* base, u32 off) -> u32& {
        return *reinterpret_cast<u32*>(base + off);
    };

    word_at(obj, 0x04u) = 0u;
    word_at(obj, 0xA0u) = 0u;

    const u32 count0 = word_at(obj, 0x20u);
    u8* const arr0 = reinterpret_cast<u8*>(static_cast<std::uintptr_t>(word_at(obj, 0x24u)));
    for (u32 i = 0u; i < count0; ++i) {
        engine_func_0013fdb0(arr0 + i * 0x48u, 0u);
    }

    void* const mgr = engine_func_002bb218();
    const u32 handle = engine_func_002bb0b4(mgr, 1u);
    engine_func_002b4d78(mgr, handle);

    word_at(obj, 0x20u) = 0u;
    word_at(obj, 0x24u) = 0u;
    func_001409b8(obj + 0x88u);

    if (word_at(obj, 0xB4u) == 0u) {
        return;
    }

    auto destroy_block = [&word_at](u8* block, u32 stride) {
        u8* elem = reinterpret_cast<u8*>(static_cast<std::uintptr_t>(word_at(block, 0x00u)));
        const u32 count = word_at(block, 0x04u) / stride;
        for (u32 i = 0u; i < count; ++i) {
            using DtorFn = void (*)(void*);
            const u32* vtbl = *reinterpret_cast<const u32* const*>(elem);
            DtorFn dtor = reinterpret_cast<DtorFn>(static_cast<std::uintptr_t>(vtbl[1]));
            dtor(elem);
            elem += stride;
        }
        func_002acb8c(block + 0x14u, word_at(block, 0x18u), block + 0x18u);
        func_002acb8c(block + 0x08u, word_at(block, 0x0Cu), block + 0x0Cu);
    };

    destroy_block(obj + 0x28u, 0x558u);
    func_002b4fa8(obj + 0xA4u, word_at(obj, 0xB4u), word_at(obj, 0xB8u));
    destroy_block(obj + 0x48u, 0x460u);
    destroy_block(obj + 0x68u, 0x2BD4u);

    word_at(obj, 0xB4u) = 0u;
    word_at(obj, 0xB8u) = 0u;
}

// DECOMP_FUNC(0x00354a44, 492)
extern "C" s32 engine_func_002b45f8(const char* a, const char* b, u32 max_len);
extern "C" void engine_func_002c14f4(u32 code, const void* caller_pc);

extern "C" u32 engine_func_00354a44(const u8* obj) {
    struct Entry {
        const char* key;
        const char* val;
    };
    struct Table {
        const Entry* entries;
        u32 count;
    };

    const u32 kErr = 0xF9613903u;
    auto lookup = [&](const char* key) -> const char* {
        const Table* tbl = *reinterpret_cast<const Table* const*>(obj + 4);
        for (u32 i = 0u; i < tbl->count; ++i) {
            if (engine_func_002b45f8(tbl->entries[i].key, key, 0x40u) == 0) {
                const char* val = tbl->entries[i].val;
                if (val != nullptr) {
                    return val;
                }
                break;
            }
        }
        engine_func_002c14f4(kErr, __builtin_return_address(0));
        return nullptr;
    };

    const char* status = lookup("sys.ECardStatus");
    if (engine_func_002b45f8("REDEEMABLE", status, 11u) == 0) {
        const char* cur = lookup("sys.ECardCurrency");
        if (engine_func_002b45f8("GUNIT", cur, 6u) == 0) {
            return 0u;
        }
        if (engine_func_002b45f8("POINTS", cur, 7u) == 0) {
            return 0xC8A13904u;
        }
        return 0xC8A13906u;
    }
    if (engine_func_002b45f8("REDEEMED", status, 9u) == 0) {
        return 0xC8A13900u;
    }
    if (engine_func_002b45f8("REVOKED", status, 8u) == 0) {
        return 0xC8A13901u;
    }
    if (engine_func_002b45f8("INACTIVE", status, 9u) == 0) {
        return 0xC8A13902u;
    }
    return kErr;
}

// DECOMP_FUNC(0x00381d9c, 492)
extern "C" void script_vm_func_003854d8(void* obj);
extern "C" void engine_func_002c4b30(void* dst, u32 size);
extern "C" void script_vm_func_00297704(const char* path, void* dst, u32 flag);
extern "C" void camp_func_002c3344(void* group);
extern "C" u32 camp_func_002c32f8(
    u8* group, u32 table, u32 count, u32 reg_word,
    u32 stack_0, u32 stack_1, u32 stack_2,
    u32 stack_3, u32 stack_4, u32 stack_5, u32 stack_6);
extern "C" void script_vm_func_00385cbc(void* ptr);
extern "C" void script_vm_func_00385cfc(void* ptr);
extern "C" void script_vm_func_00385d04(void* ptr);
extern "C" void AsdTMTexTable_func_002c4e28(u32 id);
extern "C" void camp_func_002a6214(u32 id, u32 flag);
extern "C" u32 AsdText_func_002bda1c(u32 arg);
extern "C" void PlaceWin_Init();
extern "C" void ui_func_002a7540(u32 arg);
extern "C" void script_vm_func_001a15a0(u32 arg);
extern "C" void* script_vm_func_002b6700(u32 quest_id);
extern "C" u32 script_vm_func_0029923c(u32 qid, u32 mode);
extern "C" void script_vm_func_0028f15c(u32 qid);

extern "C" void script_vm_func_00381d9c(u8* obj) {
    auto word_at = [](u8* base, u32 off) -> u32& {
        return *reinterpret_cast<u32*>(base + off);
    };

    script_vm_func_003854d8(obj);

    word_at(obj, 0x000u) = 0u;
    word_at(obj, 0x00Cu) = 0u;
    word_at(obj, 0x014u) = 0u;
    word_at(obj, 0x5A0u) = 0u;
    word_at(obj, 0x5A8u) = 0u;
    word_at(obj, 0x5ACu) = 0u;
    word_at(obj, 0x5B0u) = 0u;
    word_at(obj, 0x5B4u) = 0u;
    word_at(obj, 0x5B8u) = 0u;
    word_at(obj, 0x5BCu) = 0u;
    word_at(obj, 0x5C0u) = 0u;
    word_at(obj, 0x5A4u) = 0u;

    engine_func_002c4b30(obj + 0x6CCu, 0x640u);
    script_vm_func_00297704("quest_center/common/qc_common.bf", obj + 0x5A0u, 0u);
    script_vm_func_00297704("quest_center/common/qc_common.mbm", obj + 0x5A4u, 0u);

    camp_func_002c3344(obj + 0x024u);
    camp_func_002c32f8(
        obj + 0x024u, 0u, 0u, 0x00405898u,
        0x18u, 0u, 0u, 0u, 0u, 0x004058B0u, 0xA8u);

    script_vm_func_00385cbc(obj + 0x020u);
    script_vm_func_00385cfc(obj + 0x020u);
    script_vm_func_00385d04(obj + 0x020u);

    word_at(obj, 0xDA4u) = 0u;
    word_at(obj, 0xFB4u) = 0u;
    word_at(obj, 0xFB0u) = 0u;
    word_at(obj, 0xD8Cu) = 0u;
    word_at(obj, 0x01Cu) = 0xFFFFFFFFu;
    word_at(obj, 0x59Cu) = 0u;
    obj[0xD40u] = 0u;

    AsdTMTexTable_func_002c4e28(0x31u);
    camp_func_002a6214(0x31u, 0u);

    for (u32 i = 0u; i < 4u; ++i) {
        word_at(obj, 0x28Cu + i * 4u) = 0u;
        word_at(obj, 0x28Cu + i * 4u) = AsdText_func_002bda1c(0u);
    }

    PlaceWin_Init();
    ui_func_002a7540(0u);
    script_vm_func_001a15a0(0u);

    for (u32 qid = 0x15Eu; qid < 0x190u; ++qid) {
        const u8* node = static_cast<const u8*>(script_vm_func_002b6700(qid));
        if (node != nullptr && node[6] == 0u) {
            if (script_vm_func_0029923c(qid, 1u) == 0u) {
                script_vm_func_0028f15c(qid);
            }
        }
    }
}

// DECOMP_FUNC(0x002f38bc, 496)
extern "C" void func_0024742c(
    u32 color, float x0, float y0, float z0, float x1, float y1, float z1);

extern "C" void func_002f38bc() {
    auto draw_seg = [](u32 color, const float* a, const float* b) {
        func_0024742c(color, a[0], a[1], a[2], b[0], b[1], b[2]);
    };
    auto draw_ray = [](const float* origin, const float* dir) {
        const float end_x = origin[0] + dir[0] * 300.0f;
        const float end_y = origin[1] + dir[1] * 300.0f;
        const float end_z = origin[2] + dir[2] * 300.0f;
        func_0024742c(0xFF0000FFu, origin[0], origin[1], origin[2], end_x, end_y, end_z);
    };

    const s32* const count_ptr = reinterpret_cast<const s32*>(0x00447A28u);
    const u8* const* const objs = reinterpret_cast<const u8* const*>(0x004A0FE4u);
    const u8* const boxes = reinterpret_cast<const u8*>(0x004A0FE4u + 0x280u);

    for (s32 i = 0; i < *count_ptr; ++i) {
        const u8* const obj = objs[i];
        const u8* const inner = *reinterpret_cast<const u8* const*>(obj + 0x14u);
        const u32 mode = **reinterpret_cast<const u32* const*>(inner + 0x1Cu);
        const u8* const box = boxes + static_cast<u32>(i) * 0x178u;
        auto vec_at = [box](u32 off) -> const float* {
            return reinterpret_cast<const float*>(box + off);
        };

        if (mode == 1u) {
            const u32 kind = *reinterpret_cast<const u32*>(inner + 0x04u);
            if (kind == 0x27u) {
                draw_seg(0x00FF00FFu, vec_at(0x00u), vec_at(0x0Cu));
                draw_seg(0x00FF00FFu, vec_at(0x00u), vec_at(0x18u));
                draw_seg(0x00FF00FFu, vec_at(0x0Cu), vec_at(0x24u));
                draw_seg(0x00FF00FFu, vec_at(0x18u), vec_at(0x24u));
            } else {
                draw_seg(0x00FF00FFu, vec_at(0x18u), vec_at(0x24u));
            }
            draw_ray(vec_at(0x60u), vec_at(0x6Cu));
        } else if (mode == 2u) {
            draw_seg(0x00FF00FFu, vec_at(0x30u), vec_at(0x3Cu));
            draw_seg(0x00FF00FFu, vec_at(0x3Cu), vec_at(0x54u));
            draw_seg(0x00FF00FFu, vec_at(0x48u), vec_at(0x54u));
            draw_seg(0x00FF00FFu, vec_at(0x30u), vec_at(0x48u));
            draw_ray(vec_at(0x60u), vec_at(0x6Cu));
        }
    }
}

// DECOMP_FUNC(0x00125d88, 500)
extern "C" u32 ui_func_002c5f7c(u32 a, u32 b);
extern "C" void ui_func_002bf710(float alpha);
extern "C" void script_vm_func_002bef14();
extern "C" void ui_func_002bf460(u32 a, u32 b, u32 c, u32 d, u32 s0, u32 s1);
extern "C" u32 engine_func_002c583c(u32 a);
extern "C" void ui_func_002be77c(
    u32 a, s32 b, const char* text,
    float x, float y, float z, float sx, float sy);
extern "C" void engine_func_002aefc8(u32 a, const void* ptr, float x, float y);

extern "C" u32 ui_func_00125d88() {
    struct StateStack {
        u32 index;
        u32 reserved;
        u32 entries[4];
        u8 dirty;
        u8 pad[3];
        void (*on_change)(u32);
    };

    const u8* const overlay = *reinterpret_cast<const u8* const*>(0x0044E2E8u);
    if (*reinterpret_cast<const u32*>(overlay + 8u) != 1u) {
        return 0u;
    }

    auto sync_stack = [](StateStack* stk, u32 prev, u32 next) {
        if (stk->dirty != 0u || prev != next) {
            stk->on_change(next);
            stk->dirty = 0u;
        }
    };

    auto get_stack = []() -> StateStack* {
        u8* const base = *reinterpret_cast<u8* const*>(0x0044EA00u);
        return reinterpret_cast<StateStack*>(base + 0x124Cu);
    };

    const u32 pushed = ui_func_002c5f7c(1u, 0u);
    {
        StateStack* const stk = get_stack();
        const u32 idx = stk->index;
        const u32 prev = stk->entries[idx];
        stk->index = idx + 1u;
        stk->entries[idx + 1u] = pushed;
        sync_stack(stk, prev, pushed);
    }

    ui_func_002bf710(1.0f);
    script_vm_func_002bef14();
    ui_func_002bf460(2u, 0u, 0u, 0u, 0u, 0xBu);

    {
        StateStack* const stk = get_stack();
        const u32 old_idx = stk->index;
        const u32 prev = stk->entries[old_idx];
        const u32 new_idx = old_idx - 1u;
        stk->index = new_idx;
        const u32 top = stk->entries[new_idx];
        sync_stack(stk, prev, top);
    }

    static const char kLabelAlt[] = {
        '\x82', '\x6f', '\x82', '\x62', '\x83', '\x8d', '\x81', '\x5b', '\x83', '\x68', '\x00'
    };
    static const char kLabelNow[] = {
        '\x82', '\x71', '\x82', '\x6e', '\x82', '\x6c', '\x83', '\x8d', '\x81', '\x5b', '\x83', '\x68', '\x00'
    };
    static const char kLabelMsg[] = {
        '\x90', '\x5e', '\x81', '\x45', '\x8f', '\x97', '\x90', '\x5f', '\x93', '\x5d', '\x90', '\xb6', '\x87', '\x57', '\x00'
    };

    const char* const mode_label = (engine_func_002c583c(0u) != 0u) ? kLabelAlt : kLabelNow;
    ui_func_002be77c(3u, -1, mode_label, 296.0f, 194.0f, 0.0f, 1.0f, 1.0f);
    ui_func_002be77c(3u, -1, kLabelMsg, 296.0f, 208.0f, 0.0f, 1.0f, 1.0f);
    engine_func_002aefc8(1u, overlay + 0x10u, 228.0f, 228.0f);
    return 0u;
}

// DECOMP_FUNC(0x0015eb60, 500)
extern "C" float camp_func_002b9cf8(float base, float exp);
extern "C" void engine_func_002c3b48(void* ptr, u32 size);

extern "C" void func_0015eb60(u8* obj) {
    auto word_at = [obj](u32 off) -> u32& {
        return *reinterpret_cast<u32*>(obj + off);
    };
    auto sword_at = [obj](u32 off) -> s32& {
        return *reinterpret_cast<s32*>(obj + off);
    };
    auto float_at = [obj](u32 off) -> float {
        return *reinterpret_cast<const float*>(obj + off);
    };
    auto quantize_rate = [](u32 raw) -> u32 {
        float f = static_cast<float>(raw);
        if (!(f > 4.888f)) {
            f = 4.888f;
        }
        return static_cast<u32>(f * 0.20458265f) * 160u;
    };

    word_at(0x9Cu) = quantize_rate(word_at(0x04u));
    word_at(0xA0u) = 0u;
    word_at(0xA4u) = quantize_rate(word_at(0x0Cu));
    word_at(0xA8u) = 0u;

    sword_at(0xACu) = sword_at(0x30u);
    sword_at(0xB0u) = sword_at(0x34u);

    const float denom = (static_cast<float>(word_at(0x08u)) * 0.001f) * 32728.0f;
    for (u32 i = 0u; i < 2u; ++i) {
        word_at(0xB4u + i * 4u) = 0u;
        const float exp_val = (static_cast<float>(sword_at(0xACu + i * 4u)) * -3.0f) / denom;
        sword_at(0xBCu + i * 4u) = static_cast<s32>(camp_func_002b9cf8(10.0f, exp_val) * 128.0f);
    }

    word_at(0xC4u) = word_at(0x38u);
    word_at(0xC8u) = 0u;
    sword_at(0xCCu) = static_cast<s32>(float_at(0x10u) * 128.0f);
    sword_at(0xE0u) = static_cast<s32>(float_at(0x1Cu) * 128.0f);
    sword_at(0xE4u) = static_cast<s32>(float_at(0x20u) * 128.0f);

    float p = float_at(0x14u);
    if (sword_at(0x14u) > 0x3F733333) {
        p = 0.95f;
    }
    if (obj[0x24u] == 1u) {
        sword_at(0xE8u) = static_cast<s32>((p - 1.0f) * 128.0f);
        sword_at(0xECu) = static_cast<s32>(p * -128.0f);
    } else {
        sword_at(0xE8u) = static_cast<s32>((1.0f - p) * 128.0f);
        sword_at(0xECu) = static_cast<s32>(p * 128.0f);
    }

    engine_func_002c3b48(
        reinterpret_cast<void*>(static_cast<std::uintptr_t>(word_at(0x28u))),
        word_at(0x2Cu));
}

// DECOMP_FUNC(0x001e1d1c, 500)
extern "C" u32 engine_func_002c5978(
    const char* name, u32 prio, u32 a2, u32 a3, u32 fn, u32 dtor, u32 a6);
extern "C" void engine_func_002bf86c(char* dst, const char* src);
extern "C" void engine_func_0025c7d8(u32 id);
extern "C" void script_vm_func_0020118c();
extern "C" void camp_func_002c4c00(
    const char* name, u32 prio, u32 a2, u32 a3, u32 fn, u32 dtor, u32 a6, u32 parent);

extern "C" void engine_func_001e1d1c(const u8* launch) {
    u8* const obj = *reinterpret_cast<u8* const*>(0x0043E0D0u);
    auto word_at = [obj](u32 off) -> u32& {
        return *reinterpret_cast<u32*>(obj + off);
    };

    word_at(0x08u) = 0u;
    word_at(0x0Cu) = 0u;
    word_at(0x10u) = 0u;
    word_at(0x14u) = 0u;
    word_at(0x18u) = 0u;
    word_at(0x1Cu) = 0u;
    word_at(0x28u) = 0u;
    word_at(0x2Cu) = 0u;
    word_at(0x30u) = 0u;
    word_at(0x34u) = 0u;
    obj[0x20u] = 0u;
    obj[0x21u] = 0u;
    obj[0x22u] = 0u;
    obj[0x23u] = 0u;
    obj[0x24u] = 0u;
    obj[0x04u] = 0u;

    if (launch != nullptr) {
        u8* const params = reinterpret_cast<u8*>(0x004937C4u);
        *reinterpret_cast<u32*>(params + 0u) = *reinterpret_cast<const u32*>(launch + 0u);
        const u32 mode = *reinterpret_cast<const u32*>(launch + 4u);
        *reinterpret_cast<u32*>(params + 4u) = mode;
        if (mode == 0xFFFFFFFFu) {
            engine_func_002bf86c(
                reinterpret_cast<char*>(params + 8u),
                reinterpret_cast<const char*>(launch + 8u));
        } else {
            params[8u] = 0u;
        }
        word_at(0x00u) = engine_func_002c5978(
            "EVENT CALC", 2u, 0u, 0u, 0x0019F2D8u, 0x002CA010u, 0u);
        return;
    }

    if (engine_func_002c583c(2u) == 0u) {
        engine_func_0025c7d8(0x19u);
        engine_func_0025c7d8(0x1Bu);
        engine_func_0025c7d8(0x1Cu);
        script_vm_func_0020118c();
    }

    const u32 task = engine_func_002c5978(
        "EVENT VIEW CALC", 2u, 0u, 0u, 0x001E4C7Cu, 0x002CA010u, 0u);
    word_at(0x00u) = task;
    camp_func_002c4c00(
        "EVENT VIEW UDRAW", 0x73u, 0u, 0u, 0x0020F55Cu, 0x002E07A8u, 0u, task);
    camp_func_002c4c00(
        "EVENT VIEW DDRAW", 0xE6u, 0u, 0u, 0x002CA028u, 0x002F4AE0u, 0u, word_at(0x00u));
}

// DECOMP_FUNC(0x0038d59c, 500)
extern "C" void engine_func_002bb09c(void* dst);
extern "C" u64* engine_func_002bad80(u64* out, u32 arg);
extern "C" u32 func_0038b600(void* mgr);
extern "C" u32 engine_func_0039444c(void* ptr, u32* err_out, u32* flag_out);
extern "C" u32 func_0023a24c(void* ptr);
extern "C" void engine_func_0038b470(u64* out, void* mgr);
extern "C" u32 engine_func_002a1578(void* ptr);
extern "C" void func_002b49f4(void* mgr);
extern "C" u32 nn_sdk_func_0038b664(void* mgr);

extern "C" void engine_func_0038d59c(u8* out, u8* ctx) {
    out[0] = 1u;
    engine_func_002bb09c(out + 4);
    *reinterpret_cast<u32*>(out + 0x0Cu) = 0u;
    *reinterpret_cast<u32*>(out + 0x10u) = 0u;

    u64 tmp_ts = 0u;
    *reinterpret_cast<u64*>(out + 4) = *engine_func_002bad80(&tmp_ts, 0u);

    u8* const mgr = *reinterpret_cast<u8* const*>(0x00432FC8u);
    u32* const state_ptr = reinterpret_cast<u32*>(ctx + 4);
    const u32 state = *state_ptr;

    if (state == 0u) {
        u32 err = 0xE7E3FFFFu;
        u32 flag = 0u;
        if (engine_func_0039444c(ctx + 0x18u, &err, &flag) != 0u) {
            if ((func_0023a24c(mgr + 0x80u) & 0x80000000u) == 0u) {
                *state_ptr = 1u;
                return;
            }
            u64 ts2 = 0u;
            engine_func_0038b470(&ts2, mgr);
            *reinterpret_cast<u64*>(ctx + 0x0Cu) = ts2;
            if ((engine_func_002a1578(ctx + 0x0Cu) & 0x80000000u) == 0u) {
                *state_ptr = 1u;
                return;
            }
            *reinterpret_cast<u32*>(out + 4u) = *reinterpret_cast<const u32*>(ctx + 0x0Cu);
            *reinterpret_cast<u32*>(out + 8u) = *reinterpret_cast<const u32*>(ctx + 0x10u);
            out[0] = 0x64u;
            return;
        }
        if ((err & 0x80000000u) != 0u) {
            u64 ts2 = 0u;
            *reinterpret_cast<u64*>(out + 4u) = *engine_func_002bad80(&ts2, err);
            if (flag == 0u) {
                out[0] = 0x66u;
            } else {
                func_002b49f4(mgr);
                out[0] = 0x67u;
            }
        }
        return;
    }

    if (state == 1u) {
        if (nn_sdk_func_0038b664(mgr) != 0u) {
            *state_ptr = 2u;
            return;
        }
        *state_ptr = 3u;
        out[0] = 0u;
        return;
    }

    if (state == 2u) {
        if (func_0038b600(mgr) != 0u) {
            *state_ptr = 3u;
            out[0] = 0u;
        }
    }
}

// DECOMP_FUNC(0x0028640c, 504)
extern "C" void func_002b22fc(void* out_mtx, float rx, float ry, float rz);
extern "C" void func_002b71f8(void* dst_mtx, const void* a, const void* b);

extern "C" void func_0028640c(void* mat, s32 deg_x, s32 deg_y, s32 deg_z) {
    auto wrap_angle = [](s32 deg) -> float {
        s32 rem = deg % 360;
        if (deg < 0) {
            rem += 360;
        }
        return static_cast<float>(360 - rem) * (256.0f / 360.0f);
    };

    u8 tmp_mtx[0x40];
    if (deg_y != 0) {
        func_002b22fc(tmp_mtx, 0.0f, wrap_angle(deg_y), 0.0f);
        func_002b71f8(mat, mat, tmp_mtx);
    }
    if (deg_x != 0) {
        func_002b22fc(tmp_mtx, wrap_angle(deg_x), 0.0f, 0.0f);
        func_002b71f8(mat, mat, tmp_mtx);
    }
    if (deg_z != 0) {
        func_002b22fc(tmp_mtx, 0.0f, 0.0f, wrap_angle(deg_z));
        func_002b71f8(mat, mat, tmp_mtx);
    }
}

// DECOMP_FUNC(0x0035f1b0, 504)
extern "C" void func_0035f4a0(u16* dst, u32 max_len, const char* src);
extern "C" u32 func_0035f454(u8* obj, const u16* key, u32 max_len);
extern "C" void func_0035edd4(
    u8* obj, u32* out_flags, const u16* line, u32 len, u16* const* slots, u32 num_keys);

extern "C" u32 func_0035f1b0(
    u8* obj, u32* out_flags, void* stream, const char* const* keys, u32 num_keys) {
    u16* slots[16];
    u8* const slot_base = *reinterpret_cast<u8* const*>(obj + 0x2Cu);
    for (u32 i = 0u; i < 16u; ++i) {
        slots[i] = reinterpret_cast<u16*>(slot_base + i * 0x80u);
    }

    for (u32 i = 0u; i < num_keys; ++i) {
        if (keys[i] == nullptr) {
            return 0xE0E0EBF6u;
        }
        func_0035f4a0(slots[i], 0x40u, keys[i]);
    }

    if (obj[0x1Au] == 0u) {
        const u32 bit = 1u << obj[0x1Bu];
        for (u32 i = 0u; i < num_keys; ++i) {
            if (func_0035f454(obj, slots[i], 0x40u) != 0u) {
                out_flags[i] |= bit;
            }
        }
    }

    using GetSizeFn = u32 (*)(void*);
    using ReadFn = u32 (*)(void*, void*, u32);
    const u32* const vtbl = *reinterpret_cast<const u32* const*>(stream);
    const u32 size = reinterpret_cast<GetSizeFn>(static_cast<std::uintptr_t>(vtbl[9]))(stream);
    if (size < 2u || static_cast<s32>(size) > 0x4000) {
        return 0xD820EBECu;
    }

    void* const read_buf = *reinterpret_cast<void* const*>(obj + 0x24u);
    const u32 read_bytes = reinterpret_cast<ReadFn>(static_cast<std::uintptr_t>(vtbl[11]))(
        stream, read_buf, size);
    if (read_bytes != size) {
        return 0xD820EBECu;
    }

    const u16* const buf = reinterpret_cast<const u16*>(read_buf);
    if (buf[0] != 0xFEFFu) {
        return 0xF820EBF0u;
    }

    u32 start = 1u;
    u32 idx = 1u;
    if (size > 2u) {
        while (idx * 2u < size) {
            const u16 ch = buf[idx];
            if (ch == 0x000Au) {
                idx += 1u;
                func_0035edd4(obj, out_flags, buf + start, idx - start - 1u, slots, num_keys);
                start = idx;
            } else if (ch == 0x0000u) {
                return 0xF820EBF0u;
            }
            idx += 1u;
        }
        if (idx - 1u == start) {
            return 0u;
        }
    }

    func_0035edd4(obj, out_flags, buf + start, idx - start, slots, num_keys);
    return 0u;
}

// DECOMP_FUNC(0x0024ecc0, 532)
extern "C" u32 func_0026f370(
    float* out_val, u32 total_steps, u32 curr_step, float start_val, float target_val);
extern "C" u32 func_0026f294(
    s32* out_val, s32 target_x, s32 target_y, s32 total_steps, s32 curr_step, s32 mode);

extern "C" u32 script_vm_func_0024ecc0(u8* obj, u32 show) {
    auto word_at = [obj](u32 off) -> u32& {
        return *reinterpret_cast<u32*>(obj + off);
    };
    auto step_alpha = [&](u32 steps, float start_v, float end_v) {
        for (u32 i = 0u; i < 2u; ++i) {
            u8* const slot = obj + i * 0x14u;
            u32* const step = reinterpret_cast<u32*>(slot + 0x20u);
            func_0026f370(reinterpret_cast<float*>(slot + 0x14u), steps, *step, start_v, end_v);
            *step += 1u;
        }
    };
    auto step_pos = [&](u32 i, s32 tx, s32 ty, s32 steps) {
        u8* const slot = obj + i * 0x14u;
        u32* const step = reinterpret_cast<u32*>(slot + 0x48u);
        if (func_0026f294(reinterpret_cast<s32*>(slot + 0x40u), tx, ty, steps, *step, 1) != 0) {
            slot[0x4Cu] = 1u;
        } else {
            *step += 1u;
        }
    };

    if (show == 0u) {
        for (u32 i = 0u; i < 3u; ++i) {
            step_pos(i, 0, -330, 4);
        }
        if (word_at(0x114u) != 2u) {
            step_alpha(4u, 1.0f, 0.0f);
        }
    } else {
        if (word_at(0x108u) != 4u) {
            step_alpha(0xCu, 0.0f, 1.0f);
        }
        if (word_at(0x108u) != 2u) {
            for (u32 i = 0u; i < 3u; ++i) {
                u8* const slot = obj + i * 0x14u;
                if (i == 0u || *reinterpret_cast<const s32*>(slot + 0x34u) > 2) {
                    step_pos(i, 330, 0, 12);
                }
                *reinterpret_cast<float*>(slot + 0x3Cu) = 1.0f;
            }
        }
    }

    u32 done = 0u;
    if (*reinterpret_cast<const s32*>(obj + 0x28u) >= 0x3F800000
        && word_at(0x108u) == 2u
        && show != 0u) {
        done = 1u;
    }
    if (obj[0x74u] == 1u) {
        done = 1u;
    }
    return done;
}

// DECOMP_FUNC(0x003b8e60, 536)
extern "C" u32 script_vm_func_0022b2e0(void* ptr);
extern "C" u32 script_vm_func_0019dfbc(u32 handle);
extern "C" void script_vm_func_0022b1f8(void* obj);
extern "C" u32 shop_func_002337a0(void* ptr);
extern "C" void script_vm_func_0027e9e4(u32 a, u32 b);
extern "C" void script_vm_func_0027ea24(u32 a, u32 b);
extern "C" u32 script_vm_func_00291018(u32 bf, const char* entry);
extern "C" void script_vm_func_002971e4(u32 proc, u32 idx);
extern "C" void script_vm_func_002b8b78(u32 id);
extern "C" void* script_vm_func_002c5e2c(const char* path);
extern "C" u8* scrScriptProcess_func_002972f8(u32 bf, u32 mbm);

extern "C" void script_vm_func_003b8e60(u8* obj) {
    auto word_at = [obj](u32 off) -> u32& {
        return *reinterpret_cast<u32*>(obj + off);
    };
    auto set_state = [&](u32 s) {
        word_at(0x28u) = s;
        word_at(0x2Cu) = 0u;
    };

    const u32 ready = script_vm_func_0022b2e0(obj + 0x9Cu);
    if (script_vm_func_0019dfbc(word_at(0xD74u)) != 2u || ready == 0u) {
        return;
    }

    script_vm_func_0022b1f8(obj);
    *reinterpret_cast<u16*>(obj + 0x4Cu) = static_cast<u16>(shop_func_002337a0(obj + 0x9Cu));

    u8* const mgr = *reinterpret_cast<u8* const*>(0x00432FC8u);
    if (mgr[0xC1u] != 0u) {
        mgr[0xC1u] = 0u;
        set_state(0xAu);
        return;
    }

    const u32 mode = word_at(0xDB0u);
    if (mode == 1u) {
        set_state(9u);
        const u32 idx = script_vm_func_00291018(word_at(0xD94u), "scr_sbq_sysbtl");
        script_vm_func_002971e4(word_at(0xD9Cu), idx);
        word_at(0xDB0u) = 0u;
    } else if (mode == 2u) {
        set_state(9u);
        script_vm_func_002b8b78(0x9Eu);
        const u32 idx = script_vm_func_00291018(word_at(0xD94u), "scr_sbq_sysbtl");
        script_vm_func_002971e4(word_at(0xD9Cu), idx);
        word_at(0xDB0u) = 0u;
    } else if (mode == 3u) {
        set_state(0xBu);
        const u32 bf = static_cast<u32>(reinterpret_cast<std::uintptr_t>(
            script_vm_func_002c5e2c("battle/Result.bf")));
        word_at(0xDA0u) = bf;
        const u32 mbm = static_cast<u32>(reinterpret_cast<std::uintptr_t>(
            script_vm_func_002c5e2c("battle/ResultMsg.mbm")));
        word_at(0xDA4u) = mbm;
        u8* const proc = scrScriptProcess_func_002972f8(word_at(0xDA0u), mbm);
        word_at(0xDA8u) = static_cast<u32>(reinterpret_cast<std::uintptr_t>(proc));
        *reinterpret_cast<u32*>(proc + 0x108u) = 3u;
        const u32 idx = script_vm_func_00291018(word_at(0xDA0u), "ProcCharonRequestFirst");
        script_vm_func_002971e4(word_at(0xDA8u), idx);
        word_at(0xDB0u) = 0u;
    } else {
        script_vm_func_0027e9e4(0u, 0u);
        const u8* const d5c = *reinterpret_cast<const u8* const*>(obj + 0xD5Cu);
        script_vm_func_0027ea24(word_at(0xD80u), d5c[0x3Fu]);
        set_state(5u);
        if (mode == 4u) {
            word_at(0xDB0u) = 0u;
        }
    }
}

// DECOMP_FUNC(0x00294848, 540)
extern "C" const u8* engine_func_002b47cc(u32 item_id);
extern "C" u32 engine_func_0023d04c(void* obj, u32 slot, u32 a, u32 b, u32 body_id);
extern "C" void ui_func_002be7fc(char* dst, const char* fmt, ...);
extern "C" void engine_func_0023f440(void* obj, u32 slot, const char* path, u32 arg3);
extern "C" const u16* script_vm_func_002b66ec();

extern "C" void engine_func_00294848(void* obj, u32 slot, u32 item_id, u32 arg3) {
    const u8* const item = engine_func_002b47cc(item_id);
    char path[0x40];

    auto load_slot = [&](u32 s, const u8* it, const char* fmt, u32 body_id) {
        const u16 a = *reinterpret_cast<const u16*>(it + 0x70u);
        const u16 b = *reinterpret_cast<const u16*>(it + 0x72u);
        const u32 var = engine_func_0023d04c(obj, s, a, b, body_id);
        ui_func_002be7fc(path, fmt, a, b, var);
        engine_func_0023f440(obj, s, path, arg3);
    };

    if (slot == 0u) {
        if (item[0x52u] != 4u) {
            return;
        }
        load_slot(0u, item, "player/pl%02d_%03dhd%d.bam", 0u);
        return;
    }

    if (slot == 1u) {
        if (item[0x52u] != 5u) {
            return;
        }
        const u16 a = *reinterpret_cast<const u16*>(item + 0x70u);
        const u16 b = *reinterpret_cast<const u16*>(item + 0x72u);
        ui_func_002be7fc(path, "player/pl%02d_%03dbd0.bam", a, b);
        engine_func_0023f440(obj, 1u, path, arg3);

        const u16* const defaults = script_vm_func_002b66ec();
        load_slot(0u, engine_func_002b47cc(defaults[3]), "player/pl%02d_%03dhd%d.bam", item_id);
        load_slot(2u, engine_func_002b47cc(defaults[5]), "player/pl%02d_%03dlg%d.bam", item_id);
        return;
    }

    if (slot == 2u) {
        if (item[0x52u] != 6u) {
            return;
        }
        load_slot(2u, item, "player/pl%02d_%03dlg%d.bam", 0u);
        return;
    }

    engine_func_0023f440(obj, slot, path, arg3);
}

// DECOMP_FUNC(0x002dfad4, 544)
extern "C" u32 engine_func_002c0bcc(u32 max_val);
extern "C" float script_vm_func_00282600(float rad);
extern "C" float script_vm_func_00287e4c(
    float x0, float y0, float z0, float x1, float y1, float z1);

extern "C" u32 engine_func_002dfad4(u8* out) {
    u8* const g_state = *reinterpret_cast<u8* const*>(0x00447600u) + 0x3000u;

    for (s32 attempt = 0; attempt < 4; ++attempt) {
        const u8* const g_tgt = *reinterpret_cast<const u8* const*>(0x00447E88u);
        const u8* const g_cam = *reinterpret_cast<const u8* const*>(0x004474F4u);
        const u16 flag = *reinterpret_cast<const u16*>(0x0049FB1Cu + 0x44u);

        float px = *reinterpret_cast<const float*>(g_tgt + 0x1Cu);
        const float py = *reinterpret_cast<const float*>(g_tgt + 0x20u);
        float pz = *reinterpret_cast<const float*>(g_tgt + 0x24u);
        float ang = *reinterpret_cast<const float*>(g_cam + 0x18u);
        const s32 cnt = *reinterpret_cast<const s32*>(g_state + 0x44u);

        float dist;
        if (flag != 0u) {
            if (cnt > 0) {
                const float step = static_cast<float>((cnt + 1) >> 1) * 25.0f;
                ang += (cnt & 1) ? -step : step;
            }
            const float base_dist = (cnt > 12) ? 500.0f : 900.0f;
            dist = static_cast<float>(engine_func_002c0bcc(0x32u)) + base_dist;
        } else {
            if (cnt > 0) {
                const float step = static_cast<float>((cnt + 1) >> 1) * 35.0f;
                ang += (cnt & 1) ? -step : step;
            }
            const float base_dist = (cnt > 12) ? 250.0f : 560.0f;
            dist = static_cast<float>(engine_func_002c0bcc(0x32u)) + base_dist;
        }

        const float rad = ang * 0.017453292f;
        px += reinterpret_cast<float (*)(float)>(script_vm_func_0028277c)(rad) * dist;
        pz += script_vm_func_00282600(rad) * dist;
        *reinterpret_cast<s32*>(g_state + 0x44u) = cnt + 1;

        const float cand_pos[3] = {px, py + 35.0f, pz};
        const u8* const g_tgt2 = *reinterpret_cast<const u8* const*>(0x00447E88u);
        const float tgt_pos[3] = {
            *reinterpret_cast<const float*>(g_tgt2 + 0x1Cu),
            *reinterpret_cast<const float*>(g_tgt2 + 0x20u) + 35.0f,
            *reinterpret_cast<const float*>(g_tgt2 + 0x24u),
        };

        if (engine_func_0025b6e8(tgt_pos, cand_pos, nullptr) == -1) {
            *reinterpret_cast<float*>(out + 0x20u) = px;
            *reinterpret_cast<float*>(out + 0x24u) = py;
            *reinterpret_cast<float*>(out + 0x28u) = pz;
            *reinterpret_cast<float*>(out + 0x2Cu) = script_vm_func_00287e4c(
                cand_pos[0], cand_pos[1], cand_pos[2],
                tgt_pos[0], tgt_pos[1], tgt_pos[2]);
            return 1u;
        }
    }

    return 0u;
}

// DECOMP_FUNC(0x0032acb8, 544)
extern "C" s32 camp_func_0029f0f4(void* cursor);

extern "C" void script_vm_func_0032acb8(u32 skip) {
    using namespace camp_191cf4_calls;

    u8* const camp = *reinterpret_cast<u8* const*>(0x0043DD50u);
    if (skip != 0u) {
        return;
    }

    const u8* const slot = static_cast<const u8*>(camp_func_002a0fac()) + 0x0Eu;
    void* const cursor = camp + 0x660u;
    void* const list = camp + 0x78Au;
    const u32 asc = ((*slot & 0x80u) == 0u) ? 1u : 0u;

    if ((*slot & 0x7Fu) == 0x22u) {
        func_002b7f0a(list, camp_func_0029f0f4(cursor), 2, (asc != 0u) ? 0x001E15ECu : 0x002D03C4u);
    }
    if ((*slot & 0x7Fu) == 0x21u) {
        func_002b7f0a(list, camp_func_0029f0f4(cursor), 2, (asc != 0u) ? 0x001F6204u : 0x002DCAF8u);
    }
    if ((*slot & 0x7Fu) == 0x18u) {
        func_002b7f0a(list, camp_func_0029f0f4(cursor), 2, (asc != 0u) ? 0x0021938Cu : 0x002F274Cu);
    }
    if ((*slot & 0x7Fu) == 0x19u) {
        func_002b7f0a(list, camp_func_0029f0f4(cursor), 2, (asc != 0u) ? 0x001B1720u : 0x002192C0u);
    }
    if ((*slot & 0x7Fu) == 0x1Au) {
        func_002b7f0a(list, camp_func_0029f0f4(cursor), 2, (asc != 0u) ? 0x001E1694u : 0x002D0400u);
    }
}

// DECOMP_FUNC(0x00111090, 556)
extern "C" void* engine_func_0011b850(void* ptr);
extern "C" void* engine_func_0011b838(void* ptr);
extern "C" void* engine_func_002bac24(void* ptr);
extern "C" void* engine_func_002bac28(void* ptr);
extern "C" void* engine_func_00121ec4(void* ptr);
extern "C" void engine_func_002c541c(void* ptr, u32 zero);
extern "C" void* engine_func_00121ed8(void* ptr);
extern "C" u64 script_vm_func_00126edc(void* ptr);
extern "C" void engine_func_002bab5c(void* dst, const char* src, u32 len);
extern "C" void aocThread_func_00121e08(void* ptr, u32 stack_sz);
extern "C" void engine_func_0012701c(void* ptr);
extern "C" void engine_func_002baacc(void* ptr);

extern "C" u8* engine_func_00111090(u8* obj) {
    auto word_at = [obj](u32 off) -> u32& {
        return *reinterpret_cast<u32*>(obj + off);
    };

    engine_func_0011b850(obj + 0x20u);
    engine_func_0011b838(obj + 0x28u);
    engine_func_002bac24(obj + 0x7Cu);
    engine_func_002bac28(obj + 0x80u);
    engine_func_002bac24(obj + 0x84u);
    engine_func_00121ec4(obj + 0x88u);

    word_at(0x98u) = 0u;
    word_at(0x9Cu) = 0u;
    engine_func_002c541c(obj + 0x98u, 0u);

    word_at(0xA0u) = 0u;
    word_at(0xA4u) = 0u;
    engine_func_002c541c(obj + 0xA0u, 0u);

    engine_func_00121ed8(obj + 0xA8u);

    word_at(0x364u) = 0u;
    word_at(0x5A8u) = 0u;
    word_at(0x5ACu) = 0u;
    word_at(0x5B0u) = 0u;
    word_at(0x5B4u) = 0u;
    word_at(0x678u) = 0u;
    word_at(0x684u) = 0u;
    word_at(0x688u) = 0u;
    word_at(0x754u) = 0u;

    obj[0x758u] = 1u;
    engine_func_002bb09c(obj + 0x75Cu);
    word_at(0x764u) = 0u;
    word_at(0x768u) = 0u;
    u64 ts = 0u;
    *reinterpret_cast<u64*>(obj + 0x75Cu) = *engine_func_002bad80(&ts, 0u);

    word_at(0x76Cu) = 0u;
    obj[0xD50u] = 1u;
    word_at(0xD60u) = 0u;
    word_at(0x754u) = 0u;

    const u64 v1 = script_vm_func_00126edc(obj + 0x80u);
    word_at(0x14u) = (static_cast<u32>(v1 >> 32) & 0xFFFF0000u) | 2u;
    word_at(0x10u) = 0x00000E5Cu;

    const u64 v2 = script_vm_func_00126edc(obj + 0x80u);
    word_at(0x18u) = 0x00000E5Cu;
    word_at(0x1Cu) = static_cast<u32>(v2) & 0xFFFF0000u;

    script_vm_func_00126edc(obj + 0x80u);
    engine_func_002c4b30(obj + 0x04u, 0xBu);
    engine_func_002bab5c(obj + 0x04u, "1738159478", 0xBu);

    for (u32 off = 0x694u; off <= 0x6D0u; off += 4u) {
        word_at(off) = 0u;
    }

    engine_func_002c4b30(obj + 0x6D4u, 0x80u);
    aocThread_func_00121e08(obj + 0x88u, 0x8000u);
    engine_func_0012701c(obj + 0x98u);
    engine_func_002baacc(obj + 0x76Cu);

    word_at(0xD64u) = engine_func_002c5978(
        "Aoc Error Handling CALC", 2u, 0u, 0u, 0x00121D7Cu, 0u,
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(obj)));
    return obj;
}

// DECOMP_FUNC(0x002ac0c4, 560)
//
// Single-precision e^x (expf).  The pinned code reduces x with
// n = trunc(x * (4/ln2) +/- 0.5) so the remainder r = x - n*ln(2)/4 lies in
// [-ln2/8, ln2/8]; e^r - 1 is evaluated with a four-term polynomial and the
// result is scaled by 2^(n/4) = 2^(n>>2) * 2^((n&3)/4) using three tables.
// Edge paths special-case tiny inputs (result 1), +-inf/NaN, and the range
// error / overflow / underflow regions.
//
// The pinned binary calls three library helpers; all are declared here.
extern "C" int math_func_002a4600(u32 bits);   // 0x002A4600 raw-float classifier
extern "C" float math_func_002a462c(void);     // 0x002A462C synthetic underflow -> +0
extern "C" void math_func_002a464e(u32 code);  // 0x002A464E store code into errno (Thumb)

namespace expf_002ac0c4_data {
// 2^(i/4) is split into the coarse float C[i] and the residual A[i] = B[i]-C[i]
// so that C + A + B*(e^r-1) reproduces B*e^r with one extra rounding.
static const float kResidual[4] = {
    0x0.0p+0f, 0x1.fc1464p-13f, 0x1.3cccfep-13f, 0x1.3f32b6p-13f,
};
static const float kScaleHi[4] = {
    0x1.0p+0f, 0x1.306fep+0f, 0x1.6a09e6p+0f, 0x1.ae89fap+0f,
};
static const float kScaleCoarse[4] = {
    0x1.0p+0f, 0x1.3060p+0f, 0x1.6a0p+0f, 0x1.ae80p+0f,
};
} // namespace expf_002ac0c4_data

static inline u32 expf_002ac0c4_bits(float value) {
    return __builtin_bit_cast(u32, value);
}

static inline float expf_002ac0c4_from_bits(u32 bits) {
    return __builtin_bit_cast(float, bits);
}

static inline __attribute__((always_inline)) float expf_002ac0c4_poly(
    float x, u32 raw, bool split) {
    using namespace expf_002ac0c4_data;

    // n = trunc(x * (4/ln2) +/- 0.5); the sign-dependent half is added first.
    const float half = (raw & 0x80000000u) ? -0.5f : 0.5f;
    const float shifted = half + x * 0x1.715476p+2f;
    const s32 n = static_cast<s32>(shifted);
    const float nf = static_cast<float>(n);
    const u32 index = static_cast<u32>(n) & 3u;

    // r = x - n*ln(2)/4, using the two split literals of the original.
    float r = x - nf * 0x1.62ep-3f;
    r = r - nf * 0x1.0bfbe8p-17f;

    // e^r - 1 = r + r^2/2 + r^3/6 + r^4/24.
    float poly = 0x1.557624p-3f + r * 0x1.557624p-5f;
    poly = 0x1.fffffep-2f + r * poly;
    poly = 0x1.fffffep-1f + r * poly;
    const float rem = poly * r;

    float acc = kResidual[index] + kScaleHi[index] * rem;
    acc = acc + kScaleCoarse[index];

    const s32 exponent = n >> 2;
    if (!split) {
        const float power = expf_002ac0c4_from_bits(
            0x3f800000u + (static_cast<u32>(exponent) << 23));
        return power * acc;
    }

    // Split the exponent so neither intermediate multiply overflows.
    const s32 adjusted = exponent + ((exponent < 0) ? 1 : 0);
    const s32 hi_half = adjusted >> 1;
    const s32 lo_half = exponent - hi_half;
    float scaled = expf_002ac0c4_from_bits(
                       0x3f800000u + (static_cast<u32>(hi_half) << 23)) * acc;
    const float result = expf_002ac0c4_from_bits(
                             0x3f800000u + (static_cast<u32>(lo_half) << 23)) * scaled;

    const u32 result_bits = expf_002ac0c4_bits(result);
    if (result_bits == 0u) {                        // underflowed to +0
        math_func_002a464e(2u);
        return math_func_002a462c();
    }
    if (result_bits == 0x7f800000u) {               // exactly +inf (overflow)
        math_func_002a464e(2u);
        const float huge = expf_002ac0c4_from_bits(0x70000000u);
        return huge * huge;
    }
    if (math_func_002a4600(result_bits) == 4) {     // denormal: raise underflow
        (void)math_func_002a462c();
    }
    return result;
}

extern "C" float func_002ac0c4(float x) {
    const u32 raw = expf_002ac0c4_bits(x);

    // Normal band: 2*raw in [0x67000000, 0x85500000] (|x| in [2^-24, ~84]).
    if (0x99000000u + (raw << 1) <= 0x1e500000u) {
        return expf_002ac0c4_poly(x, raw, false);
    }

    // Exponent 0xFF selects +-inf/NaN: -inf maps to +0, everything else to 2*x.
    if ((((~raw) << 1) >> 24) == 0u) {
        return (raw == 0xff800000u) ? 0.0f : x + x;
    }

    // |x| below 2^-24 rounds to 1.
    if (0x67000000u > (raw << 1)) {
        return 1.0f;
    }

    // Upper normal band reuses the split-exponent path.
    if (0x85a00000u >= (raw << 1)) {
        return expf_002ac0c4_poly(x, raw, true);
    }

    // |x| > 104: raise ERANGE, then overflow to +inf or underflow to +0.
    math_func_002a464e(2u);
    if ((raw & 0x80000000u) == 0u) {
        const float huge = expf_002ac0c4_from_bits(0x70000000u);
        return huge * huge;
    }
    return math_func_002a462c();
}

// DECOMP_FUNC(0x002f2c00, 572)
//
// This span is the second half of the text-entry routine that starts at
// ui_func_002f2a5c (0x002F2A5C); the preceding raw block ends with branches into
// it and it ends with that routine's shared epilogue.  Three internal entry
// points are reachable from the first half, so each one is reconstructed here
// and the redraw tail is shared.
//
// Object layout (`r4` on entry):
//   +0x00 s32 x                 text origin (also the returned base)
//   +0x04 s32 y
//   +0x08 s32 state             0 = editing, 1 = confirmed, 2 = cancelled
//   +0x0C s32 cursor            0x00..0x25 grid, 0x26 filler, 0x27 "BS", 0x28 "OK"
//   +0x10 s32 length            characters currently in `name`
//   +0x14 s32 capacity          maximum characters (9)
//   +0x18 s32 suppress_draw     non-zero skips the grid and is returned
//   +0x1C u8  extension[5]      fixed suffix, e.g. ".EP"
//   +0x21 u8  name[10]          capacity + terminating NUL
//
// The pinned image has four NOP-patched call sites in this span (0x2F2D30,
// 0x2F2DA0, 0x2F2DF4 and 0x2F2E14).  Their argument registers are still
// prepared, but no call instruction exists, so they have no observable effect;
// they are documented here instead of being reproduced.

extern "C" u32 ui_func_002829f0(s32 x, s32 y, u32 a2, u32 a3);
extern "C" u32 ui_func_002bffbc(u32 key);
extern "C" void ui_func_002be7fc(char* dst, const char* fmt, ...);

namespace ui_2f2c00 {
struct Object {
    s32 x;              // +0x00
    s32 y;              // +0x04
    s32 state;          // +0x08
    s32 cursor;         // +0x0C
    s32 length;         // +0x10
    s32 capacity;       // +0x14
    s32 suppress_draw;  // +0x18
    u8 extension[5];    // +0x1C
    u8 name[10];        // +0x21
};
static_assert(__builtin_offsetof(Object, extension) == 0x1C, "layout");
static_assert(__builtin_offsetof(Object, name) == 0x21, "layout");

// Character grid: "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" (38 glyphs).
constexpr u32 kGridFiller = 0x26u;  // not a glyph; skipped by the grid pass
constexpr u32 kBackspace = 0x27u;
constexpr u32 kConfirm = 0x28u;
constexpr u32 kDeleteIndex = 0x2Au;  // synthetic index for the delete branch

static inline __attribute__((always_inline)) const u8* char_table() {
    return reinterpret_cast<const u8*>(0x004724F0u);
}

// The original writes the current glyph to the shared .data byte at 0x004724C9
// once per cell.  The byte is outside this translation unit, so the volatile
// access keeps all 38 stores observable.
static inline __attribute__((always_inline)) void probe_cell(u32 index) {
    *reinterpret_cast<volatile u8*>(0x004724C9u) = char_table()[index];
}

// 0x2F2CA4..0x2F2CE8: apply a cursor value ("append glyph", "delete" or "none").
static inline __attribute__((always_inline)) void apply_index(Object* obj,
                                                              s32 index) {
    if (index > static_cast<s32>(0x29)) {  // signed compare: delete request
        if (obj->length > 0) {             // signed compare
            obj->length -= 1;
            return;
        }
    }
    if (index == -1) {                     // CMN r5, #1
        return;
    }
    if (static_cast<u32>(index) >= kGridFiller) {  // unsigned compare
        return;
    }
    obj->name[obj->length] = char_table()[index];
    if (obj->length < obj->capacity) {
        obj->length += 1;
    }
}

// 0x2F2CEC..0x2F2E1C: draw the two header lines and walk the 13x3 glyph grid.
// `terminate` is the name-terminating store at 0x2F2CEC, which the redraw-only
// entry (0x2F2CF8) skips.  Returns the value the original leaves in r0.
static inline __attribute__((always_inline)) u32 redraw(Object* obj,
                                                         bool terminate) {
    if (terminate) {
        obj->name[obj->length] = 0u;
    }

    ui_func_002829f0(obj->x, obj->y, 0x86u, 0x14u);

    char text[0x14];
    ui_func_002be7fc(text, "%s%s", obj->name, obj->extension);

    // 0x2F2D20 prepares (x + 4, y + 4, 0, text) for a call that is a NOP.
    ui_func_002829f0(obj->x, obj->y + 0x18, 0x86u, 0x44u);

    if (obj->suppress_draw != 0) {
        return static_cast<u32>(obj->suppress_draw);
    }

    u32 cell = 0;
    for (s32 row = 0; row < 3; ++row) {
        for (s32 column = 0; column < 13; ++column) {
            if (cell < kGridFiller) {
                probe_cell(cell);
            }
            ++cell;
        }
    }

    // 0x2F2DD0 and 0x2F2DF8 prepare the "BS"/"OK" labels and their highlight
    // state; both call sites are NOPs, so only the return value remains.
    return static_cast<u32>(obj->x) + 0x72u;
}
}  // namespace ui_2f2c00

// 0x002F2C00: key-input entry.  The first half branches here when neither key
// 3 nor key 0x1E is active.
extern "C" u32 ui_func_002f2c00(u8* object) {
    using namespace ui_2f2c00;
    Object* obj = reinterpret_cast<Object*>(object);

    if (ui_func_002bffbc(0u) == 0u) {
        if (ui_func_002bffbc(0x14u) == 0u) {
            u32 pressed = ui_func_002bffbc(1u);
            if (pressed == 0u) {
                pressed = ui_func_002bffbc(0x16u);
            }
            if (pressed != 0u) {
                obj->state = 2;
            }
            if (obj->cursor == static_cast<s32>(kGridFiller)) {
                obj->cursor = static_cast<s32>(kBackspace);
            }
            apply_index(obj, -1);
            return redraw(obj, true);
        }
    }

    const s32 cursor = obj->cursor;
    if (cursor == static_cast<s32>(kConfirm)) {
        if (obj->length > 0) {
            obj->state = 1;
        }
    } else if (cursor == static_cast<s32>(kBackspace)) {
        apply_index(obj, static_cast<s32>(kDeleteIndex));
    } else if (cursor == static_cast<s32>(kGridFiller)) {
        obj->cursor = static_cast<s32>(kBackspace);
        apply_index(obj, -1);
    } else {
        apply_index(obj, cursor);
    }
    return redraw(obj, true);
}

// 0x002F2C94: cursor-move entry.  The first half branches here after changing
// the cursor; its incoming index is always -1.
extern "C" u32 ui_func_002f2c94(u8* object) {
    using namespace ui_2f2c00;
    Object* obj = reinterpret_cast<Object*>(object);

    if (obj->cursor == static_cast<s32>(kGridFiller)) {
        obj->cursor = static_cast<s32>(kBackspace);
    }
    apply_index(obj, -1);
    return redraw(obj, true);
}

// 0x002F2CF8: redraw-only entry, taken when state is already 1.  It skips the
// name-terminating store at 0x2F2CEC.
extern "C" u32 ui_func_002f2cf8(u8* object) {
    return ui_2f2c00::redraw(reinterpret_cast<ui_2f2c00::Object*>(object), false);
}

// DECOMP_FUNC(0x002f5348, 572)
extern "C" u32 engine_func_0024ada8(void* obj, const void* path, u32 mode);
extern "C" u32 engine_func_0024acf0(void* obj, const void* path, u32 mode);
extern "C" u32 engine_func_002cbf38(void* obj, const void* path, u32 mode);
extern "C" u32 engine_func_001ff988(void* obj, const void* path, u32 mode);
extern "C" u32 engine_func_00210188(void* obj, u32 zero, u32 off, u32 sz);
extern "C" u32 engine_func_001ff88c(void* obj, u32 zero, u32 off, u32 sz);
extern "C" u32 engine_func_001ffa08(void* obj, u32 zero, u32 off, u32 sz);
extern "C" u32 engine_func_0024ac80(void* obj);
extern "C" u32 engine_func_0024ac48(void* obj);
extern "C" u32 engine_func_0024ac10(void* obj);
extern "C" u32 engine_func_0024acb8(void* obj);
extern "C" void engine_func_002bb9c8(void* obj, u32 zero);

extern "C" u32 engine_func_002f5348(u32 kind, const void* path, u32 offset, u32 size) {
    u32 obj[7] = {0u, 0u, 0u, 0u, 0u, 0u, 0u};
    const u32* const vtt = reinterpret_cast<const u32*>(0x00420768u);
    const u32 vtbl0 = vtt[0];
    obj[0] = vtbl0;
    const s32 vbase_off = *reinterpret_cast<const s32*>(
        static_cast<std::uintptr_t>(vtbl0 - 0x30u));
    *reinterpret_cast<u32*>(reinterpret_cast<u8*>(obj) + vbase_off) = vtt[8];
    obj[1] = vtt[9];

    constexpr u32 kErr = 0xE7E3FFFFu;
    u32 open_res = kErr;
    if (kind == 0u) {
        open_res = engine_func_0024ada8(obj, path, 2u);
    } else if (kind == 1u) {
        open_res = engine_func_0024acf0(obj, path, 2u);
    } else if (kind == 2u) {
        open_res = engine_func_002cbf38(obj, path, 2u);
    } else if (kind == 3u) {
        open_res = engine_func_001ff988(obj, path, 2u);
    }

    if ((open_res & 0x80000000u) != 0u) {
        engine_func_002bb9c8(obj, 0u);
        return 0u;
    }

    u32 act_res = kErr;
    if (kind == 0u) {
        act_res = engine_func_00210188(obj, 0u, offset, size);
    } else if (kind == 1u) {
        act_res = engine_func_001ff88c(obj, 0u, offset, size);
    } else if (kind == 3u) {
        act_res = engine_func_001ffa08(obj, 0u, offset, size);
    }

    auto close_stream = [&]() -> u32 {
        if (kind == 0u) return engine_func_0024ac80(obj);
        if (kind == 1u) return engine_func_0024ac48(obj);
        if (kind == 2u) return engine_func_0024ac10(obj);
        if (kind == 3u) return engine_func_0024acb8(obj);
        return kErr;
    };

    if ((act_res & 0x80000000u) != 0u) {
        close_stream();
        engine_func_002bb9c8(obj, 0u);
        return 0u;
    }

    const u32 close_res = close_stream();
    engine_func_002bb9c8(obj, 0u);
    return ((close_res & 0x80000000u) == 0u) ? 1u : 0u;
}

// DECOMP_FUNC(0x00340328, 580)
extern "C" void* ui_func_00293c98();
extern "C" u32 script_vm_func_00240420(void* fs, const char* path);
extern "C" void engine_func_002a0c54(const char* path, u32 zero);
extern "C" u32 engine_func_0029a2d0(const char* path, u32 arg3);
extern "C" void* Tbb_GetSubTable(const void* container, u32 table_index);
extern "C" const u8* Tbb_GetPayloadData(void* table);
extern "C" u32 Tbb_GetRowCount(void* table);

extern "C" void battle_func_00340328(u8* obj, u32 map_id, u32 sub_id, u32 arg3) {
    auto word_at = [obj](u32 off) -> u32& {
        return *reinterpret_cast<u32*>(obj + off);
    };

    word_at(0x08u) = map_id;
    word_at(0x0Cu) = sub_id;

    constexpr const char* kDir = "battle/battle_map/";
    char path[0x40];

    ui_func_002be7fc(path, "%se%03d_%02d.bcenv", kDir, map_id, sub_id);
    if (script_vm_func_00240420(ui_func_00293c98(), path) == 0u) {
        ui_func_002be7fc(path, "%se%03d_%02d.bcenv", kDir, 1u, 1u);
        word_at(0x08u) = 1u;
        word_at(0x0Cu) = 1u;
    }
    engine_func_002a0c54(path, 0u);

    ui_func_002be7fc(path, "%sb%03d_%02d.bam", kDir, map_id, sub_id);
    if (script_vm_func_00240420(ui_func_00293c98(), path) == 0u) {
        ui_func_002be7fc(path, "%sb%03d_%02d.bam", kDir, 1u, 1u);
        word_at(0x08u) = 1u;
        word_at(0x0Cu) = 1u;
    }
    word_at(0x10u) = engine_func_0029a2d0(path, arg3);

    void* const sub_tbl = Tbb_GetSubTable(*reinterpret_cast<const void* const*>(0x004341F8u), 0u);
    const u8* const rows = Tbb_GetPayloadData(sub_tbl);
    const u32 count = Tbb_GetRowCount(sub_tbl);
    if (count == 0u) {
        return;
    }

    const u32 target_map = word_at(0x08u);
    for (u32 i = 0u; i < count; ++i) {
        const u8* const row = rows + i * 0x4Cu;
        if (*reinterpret_cast<const u16*>(row + 0u) == target_map
            && *reinterpret_cast<const u16*>(row + 2u) == word_at(0x0Cu)) {
            if (row == nullptr) {
                return;
            }
            for (u32 k = 0u; k < 2u; ++k) {
                const u8* const sub_entry = row + k * 0x24u;
                if (sub_entry[4u] != '0') {
                    ui_func_002be7fc(
                        path, "%s%s.bam", kDir, reinterpret_cast<const char*>(sub_entry + 4u));
                    word_at(0x14u + k * 4u) = engine_func_0029a2d0(path, arg3);
                    float* const pos = reinterpret_cast<float*>(obj + 0x28u + k * 0x0Cu);
                    pos[0] = static_cast<float>(*reinterpret_cast<const u16*>(sub_entry + 0x22u));
                    pos[1] = static_cast<float>(*reinterpret_cast<const u16*>(sub_entry + 0x24u));
                    pos[2] = static_cast<float>(*reinterpret_cast<const u16*>(sub_entry + 0x26u));
                }
            }
            return;
        }
    }
}

// DECOMP_FUNC(0x0026bed8, 584)
extern "C" void camp_func_001d12b0();

extern "C" void camp_func_0026bed8() {
    using namespace camp_191cf4_calls;

    u8* const camp = *reinterpret_cast<u8* const*>(0x0043DCF0u);
    const u8* const cfg = static_cast<const u8*>(camp_func_002a0fac());
    const u8 b = cfg[0];
    const u32 asc = ((b & 0x80u) == 0u) ? 1u : 0u;
    const u32 key = b & 0x7Fu;
    void* const list = camp + 0x738u;

    if (key == 2u) {
        func_002b7f0a(list, 0x18, 8, (asc != 0u) ? 0x0029226Cu : 0x0025CD64u);
    }
    if (key == 1u) {
        func_002b7f0a(list, 0x18, 8, (asc != 0u) ? 0x001B17ECu : 0x0021948Cu);
    }
    if (key == 4u) {
        func_002b7f0a(list, 0x18, 8, (asc != 0u) ? 0x00292200u : 0x0025CCF8u);
    }
    if (key == 5u) {
        func_002b7f0a(list, 0x18, 8, (asc != 0u) ? 0x0019205Cu : 0x001E1628u);
    }
    if (key == 0x1Fu) {
        func_002b7f0a(list, 0x18, 8, (asc != 0u) ? 0x001A8158u : 0x0020718Cu);
    }
    if (key == 3u) {
        func_002b7f0a(list, 0x18, 8, (asc != 0u) ? 0x001A8098u : 0x002070CCu);
    }

    camp_func_001d12b0();
}

// DECOMP_FUNC(0x0026adcc, 592)
extern "C" s32 ui_func_0029d8fc(s32 key);
extern "C" s32 func_001c35a0();
extern "C" s32 engine_func_0029ebf8(void* cursor);
extern "C" s32 script_vm_func_001c3588();
extern "C" s32 ui_func_002c615c(s32 num, s32 den);
extern "C" void camp_func_0029eb58(void* cursor, s32 idx);
extern "C" s32 camp_func_0029f260(void* cursor);
extern "C" s32 camp_func_0029f248(void* cursor);
extern "C" s32 camp_func_0029ebdc(void* cursor);
extern "C" s32 engine_func_0029eba8(void* cursor);
extern "C" void camp_func_0029edfc(void* cursor, s32 idx);
extern "C" void script_vm_func_002b91c4(u32 se_id);

extern "C" u32 camp_func_0026adcc(
    void* cursor, u32 pos_packed, u32 size_packed, s32 hold_key,
    s32 up_key, s32 down_key, u32 is_grid, u32 play_se) {
    const s32 st_up = ui_func_0029d8fc(static_cast<s16>(up_key));
    const s32 st_dn = ui_func_0029d8fc(static_cast<s16>(down_key));
    const s32 st_hd = ui_func_0029d8fc(static_cast<s16>(hold_key));
    constexpr u32 kSeId = 0x0100016Cu;

    if (st_up == 6 || st_up == 2) {
        s32 target = camp_func_0029f260(cursor) + camp_func_0029f248(cursor) - 1;
        if (is_grid != 0u) {
            target = camp_func_0029ebdc(cursor) + engine_func_0029eba8(cursor) - 1;
        }
        if (target >= 0) {
            if (is_grid != 0u) {
                camp_func_0029eb58(cursor, target);
            } else {
                camp_func_0029edfc(cursor, target);
            }
            if (play_se != 0u) {
                script_vm_func_002b91c4(kSeId);
            }
        }
        return 1u;
    }

    if (st_dn == 6 || st_dn == 2) {
        s32 target = camp_func_0029f260(cursor) + camp_func_0029f248(cursor) + 1;
        if (is_grid != 0u) {
            target = camp_func_0029ebdc(cursor) + engine_func_0029eba8(cursor) + 1;
            if (engine_func_0029ebf8(cursor) > target) {
                camp_func_0029eb58(cursor, target);
                if (play_se != 0u) {
                    script_vm_func_002b91c4(kSeId);
                }
            }
        } else {
            if (camp_func_0029f0f4(cursor) > target) {
                camp_func_0029edfc(cursor, target);
                if (play_se != 0u) {
                    script_vm_func_002b91c4(kSeId);
                }
            }
        }
        return 1u;
    }

    if (st_hd == 0) {
        return 0u;
    }

    const s32 rows = camp_func_0029f0f4(cursor);
    const s32 ty = static_cast<s16>(func_001c35a0() - (static_cast<s32>(pos_packed) >> 16));
    if (is_grid != 0u) {
        const s32 cols = engine_func_0029ebf8(cursor);
        const s32 tx = static_cast<s16>(script_vm_func_001c3588() - static_cast<s16>(pos_packed));
        const s32 w = static_cast<s16>(size_packed);
        if (tx >= 0 && w > tx) {
            const s32 idx = static_cast<s16>(ui_func_002c615c(tx * cols, w));
            camp_func_0029eb58(cursor, idx);
        }
    } else {
        const s32 h = static_cast<s32>(size_packed) >> 16;
        if (ty >= 0 && h > ty) {
            const s32 idx = static_cast<s16>(ui_func_002c615c(ty * rows, h));
            const s32 cur = camp_func_0029f248(cursor) + camp_func_0029f260(cursor);
            if (cur != idx && play_se != 0u) {
                script_vm_func_002b91c4(kSeId);
            }
            camp_func_0029edfc(cursor, idx);
        }
    }
    return 1u;
}

extern "C" u8* Task_func_002861f8(u32 a0, u32 a1, u32 a2, u32 a3, u32 s0_bits, u32 size, u32 prio, u32 a7, u32 a8);
extern "C" void ui_func_002bcf58(void* dst, const void* src, u32 size);
extern "C" void battle_func_00193b64(void* task);

// DECOMP_FUNC(0x002d81d0, 596)
extern "C" void* ui_func_002d81d0(
    u32 arg0, const void* arg1, const u8* arg2, u32 arg3, const u8* cfg,
    u32 s17_bits, u32 s0_bits, u32 r8_u, u32 /*pad*/, u32 r7_u, u32 s18_bits) {
    const u32 cfg_w0 = *reinterpret_cast<const u32*>(cfg);
    const u8 b11 = cfg[0x11];
    const u32 prio = ((cfg_w0 & 2u) != 0u || b11 == 3u || b11 == 1u) ? 4u : 3u;

    u8* task = nullptr;
    if (b11 == 0u) {
        task = Task_func_002861f8(0x001929BCu, 0x001AAC60u, 0u, 0u, s0_bits, 0x3F0u, prio, 0u, 0u);
    } else if (b11 == 1u) {
        task = Task_func_002861f8(0x001929BCu, 0u, 0x001AA5A0u, 0u, s0_bits, 0x3F0u, prio, 0u, 0u);
    } else if (b11 == 3u) {
        task = Task_func_002861f8(0x001929BCu, 0u, 0u, 0x001AA5A0u, s0_bits, 0x3F0u, prio, 0u, 0u);
    }

    if (task == nullptr) {
        return nullptr;
    }

    engine_func_002c4b30(task, 0x3F0u);

    constexpr u32 kNegHalf = 0xBF000000u;
    constexpr u32 kPosHalf = 0x3F000000u;
    *reinterpret_cast<u32*>(task + 0x26C) = kNegHalf;
    *reinterpret_cast<u32*>(task + 0x270) = kNegHalf;
    *reinterpret_cast<u32*>(task + 0x274) = 0u;
    *reinterpret_cast<u32*>(task + 0x280) = 0x00FF00FFu;

    *reinterpret_cast<u32*>(task + 0x284) = kNegHalf;
    *reinterpret_cast<u32*>(task + 0x288) = kPosHalf;
    *reinterpret_cast<u32*>(task + 0x28C) = 0u;
    *reinterpret_cast<u32*>(task + 0x298) = 0xFF0000FFu;

    *reinterpret_cast<u32*>(task + 0x29C) = kPosHalf;
    *reinterpret_cast<u32*>(task + 0x2A0) = kNegHalf;
    *reinterpret_cast<u32*>(task + 0x2A4) = 0u;
    *reinterpret_cast<u32*>(task + 0x2B0) = 0x0000FFFFu;

    *reinterpret_cast<u32*>(task + 0x2B4) = kPosHalf;
    *reinterpret_cast<u32*>(task + 0x2B8) = kPosHalf;
    *reinterpret_cast<u32*>(task + 0x2BC) = 0u;
    *reinterpret_cast<u32*>(task + 0x2C8) = 0xFFFF00FFu;

    task[0x380] = static_cast<u8>(arg3);
    ui_func_002bcf58(task, arg1, 0x134u);
    *reinterpret_cast<const u8**>(task + 0x354) = cfg;
    *reinterpret_cast<u32*>(task + 0x2D4) = 0u;
    *reinterpret_cast<u32*>(task + 0x2D8) = 0u;
    *reinterpret_cast<u32*>(task + 0x2DC) = 0u;

    if (task[0x380] != 0u) {
        ui_func_002bcf58(task + 0x134, arg2, 0xB0u);
    } else {
        for (u32 i = 0; i < 4u; ++i) {
            task[0x1DA + i] = arg2[0xA6 + i];
        }
    }

    *reinterpret_cast<u32*>(task + 0x268) = s18_bits;
    *reinterpret_cast<u16*>(task + 0x2D0) = 0u;
    *reinterpret_cast<u32*>(task + 0x37C) = arg0;
    battle_func_00193b64(task);
    *reinterpret_cast<u32*>(task + 0x384) = s17_bits;
    task[0x3E9] = static_cast<u8>(r8_u);
    *reinterpret_cast<u16*>(task + 0x3EC) = static_cast<u16>(r7_u);
    *reinterpret_cast<u16*>(task + 0x3EA) = static_cast<u16>(r7_u);
    return task;
}

extern "C" void func_001078d8();
extern "C" void func_00108b10();
extern "C" u32 engine_func_002c00d4(void* guard);
extern "C" void* func_0011c374();
extern "C" void func_0011c544(void* obj, void* arg);
extern "C" void script_vm_func_002bd9ec(void* dst, const void* src);
extern "C" void func_0011c404(void* obj, const void* src);
extern "C" void func_0011c4c8(void* obj, void* a1, u32 a2, void* a3, s32 a4);

// DECOMP_FUNC(0x0010b578, 604)
extern "C" u32 engine_func_0010b578() {
    func_001078d8();
    func_00108b10();

    u32* const guard = reinterpret_cast<u32*>(0x004729F8u);
    u8* const obj = reinterpret_cast<u8*>(0x004EAA88u);
    if ((*guard & 1u) == 0u && engine_func_002c00d4(guard) != 0u) {
        func_0011c544(obj, func_0011c374());
    }

    u8* const sub = obj + 0x58;
    if (*reinterpret_cast<u32*>(sub + 8) != 0u) {
        *reinterpret_cast<u16*>(obj + 4) = *reinterpret_cast<u16*>(sub + 0);
        *reinterpret_cast<u16*>(obj + 6) = *reinterpret_cast<u16*>(sub + 2);
        *reinterpret_cast<u32*>(sub + 8) = 0u;
    }

    script_vm_func_002bd9ec(sub + 0x12, sub + 0x0C);
    for (u32 i = 0; i < 3u; ++i) {
        *reinterpret_cast<u32*>(obj + 0x7C + i * 4u) = *reinterpret_cast<u32*>(obj + 0x70 + i * 4u);
    }
    func_0011c404(obj, sub + 0x0C);

    if (sub[5] == 1u) {
        const float vx = static_cast<float>(*reinterpret_cast<s16*>(sub + 0x0C));
        const float vy = static_cast<float>(*reinterpret_cast<s16*>(sub + 0x0E));
        const float vz = static_cast<float>(*reinterpret_cast<s16*>(sub + 0x10));
        const float len_sq = vx * vx + vy * vy + vz * vz;
        float len;
        asm("vsqrt.f32 %0, %1" : "=t"(len) : "t"(len_sq));
        const float inv_len = 1.0f / len;
        const float nx = vx * inv_len;
        const float ny = vy * inv_len;
        const float nz = vz * inv_len;

        const float* const r0 = reinterpret_cast<const float*>(sub + 0x30);
        const float* const r1 = reinterpret_cast<const float*>(sub + 0x40);
        const float* const r2 = reinterpret_cast<const float*>(sub + 0x50);
        const float ox = (r0[0] * nx + r0[1] * ny + r0[2] * nz) * len;
        const float oy = (r1[0] * nx + r1[1] * ny + r1[2] * nz) * len;
        const float oz = (r2[0] * nx + r2[1] * ny + r2[2] * nz) * len;

        auto clamp_s16 = [](s16 v) -> s16 {
            if (v <= -930) {
                return -930;
            }
            if (v > 930) {
                return 930;
            }
            return v;
        };
        *reinterpret_cast<s16*>(sub + 0x0C) = clamp_s16(static_cast<s16>(static_cast<s32>(ox)));
        *reinterpret_cast<s16*>(sub + 0x0E) = clamp_s16(static_cast<s16>(static_cast<s32>(oy)));
        *reinterpret_cast<s16*>(sub + 0x10) = clamp_s16(static_cast<s16>(static_cast<s32>(oz)));
    }

    func_0011c4c8(obj, sub + 0x18, 1u, sub + 0x0C, -1);
    return 1u;
}

extern "C" const u8* ui_func_00282b94(void* p, u32 a0);

// DECOMP_FUNC(0x003c1710, 612)
extern "C" void ui_func_003c1710(u32 arg0, u8* obj) {
    const u8* const g = reinterpret_cast<const u8*>(0x00439CE0u);
    const s32 fade_frames = *reinterpret_cast<const s32*>(g + 0x0C);
    if ((*reinterpret_cast<const u32*>(obj + 0x50) & 2u) == 0u) {
        return;
    }

    const u8* const unit = ui_func_00282b94(
        reinterpret_cast<void*>(arg0),
        static_cast<u32>(*reinterpret_cast<const s16*>(obj + 0x62)));
    if (unit == nullptr) {
        return;
    }

    if ((*reinterpret_cast<const u32*>(unit) & 0x80000u) == 0u ||
        *reinterpret_cast<const u32*>(obj + 0x64) == 0xFFFFu) {
        *reinterpret_cast<u32*>(obj + 0x6C) = 0xFFFFFFFFu;
        return;
    }

    u32 slot = *reinterpret_cast<u32*>(obj + 0x94);
    const u16 mask = *reinterpret_cast<const u16*>(unit + 0x1C6);
    if (slot == 0u) {
        for (u32 i = 0u; i < 11u; ++i) {
            if ((mask & (1u << i)) != 0u) {
                *reinterpret_cast<u32*>(obj + 0x94) = i;
                slot = i;
                break;
            }
        }
    }

    u32 target_color = *reinterpret_cast<const u32*>(g + 0x18);
    if (slot == 7u) {
        target_color = 0x52DEE7FFu;
    } else if (slot == 5u) {
        target_color = 0xB252CEFFu;
    } else if (slot == 6u) {
        target_color = 0xF721F9FFu;
    } else if (slot == 8u) {
        target_color = 0xEFD629FFu;
    } else if (slot == 9u) {
        target_color = 0x7E620CFFu;
    } else if (slot == 3u) {
        target_color = 0xFF4000FFu;
    }

    if (*reinterpret_cast<u32*>(obj + 0x90) != target_color) {
        *reinterpret_cast<u32*>(obj + 0x8C) = *reinterpret_cast<u32*>(obj + 0x6C);
        *reinterpret_cast<u32*>(obj + 0x90) = target_color;
        *reinterpret_cast<u32*>(obj + 0x80) = 0u;
    }

    const s32 timer = *reinterpret_cast<s32*>(obj + 0x80);
    if (timer < fade_frames) {
        const s32 next = timer + 1;
        *reinterpret_cast<s32*>(obj + 0x80) = next;
        const float t = static_cast<float>(next) / static_cast<float>(fade_frames);
        const u32 start_color = *reinterpret_cast<u32*>(obj + 0x8C);

        const s32 s3 = static_cast<s32>((start_color >> 24) & 0xFFu);
        const s32 s2 = static_cast<s32>((start_color >> 16) & 0xFFu);
        const s32 s1 = static_cast<s32>((start_color >> 8) & 0xFFu);
        const s32 s0 = static_cast<s32>(start_color & 0xFFu);

        const s32 d3 = static_cast<s32>((target_color >> 24) & 0xFFu) - s3;
        const s32 d2 = static_cast<s32>((target_color >> 16) & 0xFFu) - s2;
        const s32 d1 = static_cast<s32>((target_color >> 8) & 0xFFu) - s1;
        const s32 d0 = static_cast<s32>(target_color & 0xFFu) - s0;

        const u32 o3 = static_cast<u32>(s3 + static_cast<s32>(static_cast<float>(d3) * t));
        const u32 o2 = static_cast<u32>(s2 + static_cast<s32>(static_cast<float>(d2) * t));
        const u32 o1 = static_cast<u32>(s1 + static_cast<s32>(static_cast<float>(d1) * t));
        const u32 o0 = static_cast<u32>(s0 + static_cast<s32>(static_cast<float>(d0) * t)) & 0xFFu;

        *reinterpret_cast<u32*>(obj + 0x6C) = (o3 << 24) + (o2 << 16) + (o1 << 8) + o0;
        return;
    }

    *reinterpret_cast<u32*>(obj + 0x6C) = target_color;
    const s32 next = timer + 1;
    *reinterpret_cast<s32*>(obj + 0x80) = next;

    const float limit = (static_cast<float>(fade_frames) + 20.0f) + 4.0f;
    if (limit < static_cast<float>(next)) {
        u32 cand = slot + 1u;
        do {
            if ((mask & (1u << cand)) != 0u) {
                *reinterpret_cast<u32*>(obj + 0x94) = cand;
                break;
            }
            ++cand;
            if (cand > 10u) {
                cand = 0u;
            }
        } while (cand != slot);
    }
}

extern "C" u32 shop_func_00240e8c(void* p);
extern "C" const u8* camp_func_002bf6c8(void* obj, u32 id);
extern "C" void func_00230e54(void* obj, u32 id);
extern "C" void camp_func_00231d60(void* obj, u32 id, s32 x, s32 y, u32 layer, u32 flag);
extern "C" u32 battle_func_002c5fa4(u32 a0, u32 a1, u32 a2);
extern "C" void func_00230c80(void* obj, u32 a1, s32 x, s32 y, u32 a4, u32 a5, u32 color, u32 layer, const char* text);

// DECOMP_FUNC(0x003a11a4, 616)
extern "C" void shop_func_003a11a4(u8* self) {
    const u32 layer = *reinterpret_cast<const u32*>(self + 0x37C) + 6u;
    const u32 mode = *reinterpret_cast<const u32*>(self + 0x860);
    const u32 offset = (mode == 7u || mode == 8u) ? 1u : 2u;
    const u32 idx = shop_func_00240e8c(self + 0x880 + mode * 0x74u);

    const u8* const p0 = camp_func_002bf6c8(self + 0x394, idx + offset + 0x4Fu);
    s32 x = *reinterpret_cast<const s16*>(p0 + 8);
    s32 y = *reinterpret_cast<const s16*>(p0 + 0xA);
    const u8* const p1 = camp_func_002bf6c8(self + 0x394, 0xC8u);
    x += *reinterpret_cast<const s16*>(p1 + 8);
    y += *reinterpret_cast<const s16*>(p1 + 0xA);

    func_00230e54(self + 0x394, (mode == 8u) ? 9u : 8u);
    camp_func_00231d60(self + 0x394, 0xC2u, x, y, layer, 1u);
    camp_func_00231d60(self + 0x394, 0xC3u, x, y, layer, 1u);

    typedef void (*ApplyBlendFn)(u32);
    u8* const stack_base = *reinterpret_cast<u8**>(0x0044EA00u);
    u8* const stack = stack_base + 0x12AC;
    const u32 blend_val = battle_func_002c5fa4(6u, 1u, 0u);
    const u32 depth = *reinterpret_cast<u32*>(stack);
    const u32 prev_val = *reinterpret_cast<u32*>(stack + 8 + depth * 4u);
    const u32 next_depth = depth + 1u;
    *reinterpret_cast<u32*>(stack) = next_depth;
    *reinterpret_cast<u32*>(stack + 8 + next_depth * 4u) = blend_val;
    if (stack[0x18] != 0u || prev_val != blend_val) {
        reinterpret_cast<ApplyBlendFn>(*reinterpret_cast<const u32*>(stack + 0x1C))(blend_val);
        stack[0x18] = 0u;
    }

    if (self[0x878] != 0u) {
        camp_func_00231d60(self + 0x394, 0xC4u, x, y, layer + 1u, 1u);
    }
    if (self[0x879] != 0u) {
        camp_func_00231d60(self + 0x394, 0xC5u, x, y, layer + 1u, 1u);
    }

    u8* const stack2 = *reinterpret_cast<u8**>(0x0044EA00u) + 0x12AC;
    const u32 depth2 = *reinterpret_cast<u32*>(stack2);
    const u32 popped_val = *reinterpret_cast<u32*>(stack2 + 8 + depth2 * 4u);
    const u32 prev_depth = depth2 - 1u;
    *reinterpret_cast<u32*>(stack2) = prev_depth;
    const u32 restore_val = *reinterpret_cast<u32*>(stack2 + 8 + prev_depth * 4u);
    if (stack2[0x18] != 0u || popped_val != restore_val) {
        reinterpret_cast<ApplyBlendFn>(*reinterpret_cast<const u32*>(stack2 + 0x1C))(restore_val);
        stack2[0x18] = 0u;
    }

    const u32 count = *reinterpret_cast<const u32*>(self + 0x868);
    const u8* const p2 = camp_func_002bf6c8(self + 0x394, 0xC7u);
    const u32 color = (count == *reinterpret_cast<const u32*>(self + 0x86C)) ? 0xF49800FFu : 0xFFFFFFFFu;
    const s32 tx = x + *reinterpret_cast<const s16*>(p2 + 8);
    const s32 ty = y + *reinterpret_cast<const s16*>(p2 + 0xA);

    char buf[36];
    ui_func_002be7fc(buf, "%2d", count);
    func_00230c80(self + 0x394, 0u, tx, ty, 0u, 7u, color, layer, buf);
}

extern "C" u32 ui_func_002a63f8(u32 a0, u32 a1);
extern "C" void script_vm_func_003ba974(void* self);
extern "C" u32 script_vm_func_002c0ba8(u32 id);
extern "C" void engine_func_002350f4(u8* self, const char* name1, const char* name2);
extern "C" const u8* engine_func_0022ba54(void* p);
extern "C" void engine_func_0022b158(void* p, u32 a1, s32 a2);
extern "C" void engine_func_00234e70(void* p, s32 a1, u32 a2);
extern "C" const u8* engine_func_003bbd00(void* local_out);
extern "C" s32 engine_func_0022b144(void* local_in, s32 idx);
extern "C" u32 engine_func_002c32f0(const char* path, void* meta_out, u32 flag);
extern "C" void engine_func_002a06a0(void* p, u32 a1, u32 a2);
extern "C" void engine_func_0022b3d8(void* p, u32 a1);
extern "C" void engine_func_0023509c(void* p, u32 a1);
extern "C" void PlaceWin_ShowMessage(const void* msg);

// DECOMP_FUNC(0x003b97c4, 616)
extern "C" void engine_func_003b97c4(u8* self) {
    if (ui_func_002a63f8(0x21u, *reinterpret_cast<const u32*>(self + 0x90)) == 0u ||
        *reinterpret_cast<const u32*>(self + 0xD6C) == 0u ||
        *reinterpret_cast<const u32*>(self + 0xD70) == 0u) {
        return;
    }

    script_vm_func_003ba974(self);
    *reinterpret_cast<u32*>(self + 0x28) = 3u;
    *reinterpret_cast<u32*>(self + 0x2C) = 0u;

    auto call_2350f4 = reinterpret_cast<void (*)(void*, const char*, const char*)>(engine_func_002350f4);
    const u8* const info = *reinterpret_cast<const u8* const*>(self + 0xD5C);
    if (info[0x40] != 0x30u) {
        self[0xE58] = 1u;
        char path[0x80];
        char path2[0x80];
        ui_func_002be7fc(path, "mikado/%s", info + 0x40);

        u8* const e5c = *reinterpret_cast<u8**>(self + 0xE5C);
        const u16 h64 = *reinterpret_cast<const u16*>(info + 0x64);
        const u16 h66 = *reinterpret_cast<const u16*>((*reinterpret_cast<const u8* const*>(self + 0xD5C)) + 0x66);
        const bool use_alt = (h64 != 0u && script_vm_func_002c0ba8(h64) != 0u) ||
                             (h66 != 0u && script_vm_func_002c0ba8(h66) != 0u);
        if (use_alt) {
            ui_func_002be7fc(path2, "mikado/%s", (*reinterpret_cast<const u8* const*>(self + 0xD5C)) + 0x68);
            call_2350f4(e5c, path, path2);
        } else {
            call_2350f4(e5c, path, nullptr);
        }

        const u8* const sb = engine_func_0022ba54(self + 0x9C);
        engine_func_0022b158(*reinterpret_cast<void**>(self + 0xE5C), 0u, -1);
        engine_func_00234e70(*reinterpret_cast<void**>(self + 0xE5C), *reinterpret_cast<const s16*>(sb + 0x28), 1u);

        if (*reinterpret_cast<const s32*>((*reinterpret_cast<const u8* const*>(self + 0xD5C)) + 0x60) >= 0) {
            u32 local = 0u;
            const u8* anim_list = engine_func_003bbd00(&local);
            if (anim_list != nullptr) {
                for (s32 i = 0;
                     i < engine_func_0022b144(&local, *reinterpret_cast<const s32*>((*reinterpret_cast<const u8* const*>(self + 0xD5C)) + 0x60));
                     ++i) {
                    ui_func_002be7fc(path, "mikado/%s.bam", anim_list + i * 0x20);
                    *reinterpret_cast<u32*>(self + 0xE60 + i * 4) =
                        engine_func_002c32f0(path, self + 0xE88 + i * 4, 1u);
                }
                const s32 idx = *reinterpret_cast<const s8*>(sb + 0x2B);
                engine_func_002a06a0(
                    *reinterpret_cast<void**>(self + 0xE5C),
                    *reinterpret_cast<const u32*>(self + 0xE60 + idx * 4),
                    *reinterpret_cast<const u32*>(self + 0xE88 + idx * 4));
            }
        }

        const s16 s3c = *reinterpret_cast<const s16*>(self + 0x3C);
        const s16 sb28 = *reinterpret_cast<const s16*>(sb + 0x28);
        if ((s3c == 4 || s3c == 3) && (sb28 == 0 || sb28 == 6)) {
            engine_func_0022b3d8(*reinterpret_cast<void**>(self + 0xE5C), 1u);
            engine_func_0023509c(*reinterpret_cast<void**>(self + 0xE5C), 0u);
        } else {
            engine_func_0022b3d8(*reinterpret_cast<void**>(self + 0xE5C), 0u);
            engine_func_0023509c(*reinterpret_cast<void**>(self + 0xE5C), 1u);
        }
    }

    if (*reinterpret_cast<const u32*>(self + 0xDB0) != 1u) {
        PlaceWin_ShowMessage((*reinterpret_cast<const u8* const*>(self + 0xD5C)) + 2);
    }
}

extern "C" f32 func_0024bd60(s32 a0, s32 a1, const void* elem, f32 x, f32 y, f32 z, f32 eps);

// DECOMP_FUNC(0x002fca68, 620)
extern "C" s32 ui_func_002fca68(const float* p0, const float* p1, float* out) {
    s32 hit_idx = -1;
    const u8* const g = reinterpret_cast<const u8*>(0x00446FE8u);
    float cur_x = p0[0];
    float cur_y = p0[1];
    float cur_z = p0[2];
    float end_x = p1[0];
    float end_y = p1[1];
    float end_z = p1[2];

    auto vfp_fabsf = [](float x) -> float {
        float res;
        asm("vabs.f32 %0, %1" : "=t"(res) : "t"(x));
        return res;
    };

    for (s32 pass = 1; pass < 3; ++pass) {
        const u8* planes = nullptr;
        s32 count = 0;
        float eps = 5.0f;
        if (pass == 1) {
            planes = *reinterpret_cast<const u8* const*>(g + 0x20);
            count = *reinterpret_cast<const s32*>(g + 0x0C);
            eps = 8.0f;
            if (hit_idx == -1) {
                const float x0 = p0[0];
                const float y0 = p0[1];
                const float z0 = p0[2];
                end_x = p1[0];
                end_y = p1[1];
                end_z = p1[2];
                const float dx = x0 - end_x;
                const float dy = y0 - end_y;
                const float dz = z0 - end_z;
                const float len_sq = dx * dx + dy * dy + dz * dz;
                float len;
                asm("vsqrt.f32 %0, %1" : "=t"(len) : "t"(len_sq));
                const float inv_len = 1.0f / len;
                cur_x = x0 + (dx * inv_len) * 8.0f;
                cur_y = y0 + (dy * inv_len) * 8.0f;
                cur_z = z0 + (dz * inv_len) * 8.0f;
            }
        } else {
            planes = *reinterpret_cast<const u8* const*>(g + 0x24);
            count = *reinterpret_cast<const s32*>(g + 0x10);
        }

        for (s32 i = 0; i < count; ++i, planes += 0xA8) {
            if (planes[8] == 0u || (*reinterpret_cast<const u32*>(planes) & 1u) == 0u) {
                continue;
            }
            const float nx = *reinterpret_cast<const float*>(planes + 0x0C);
            const float ny = *reinterpret_cast<const float*>(planes + 0x10);
            const float nz = *reinterpret_cast<const float*>(planes + 0x14);
            const float pd = *reinterpret_cast<const float*>(planes + 0x18);

            const float d0 = (cur_x * nx + cur_y * ny + cur_z * nz) - pd;
            const float d1 = (end_x * nx + end_y * ny + end_z * nz) - pd;
            if (!((d0 < 0.0f && d1 >= 0.0f) || (d0 >= 0.0f && d1 < 0.0f))) {
                continue;
            }

            const float a0 = vfp_fabsf(d0);
            const float a1 = vfp_fabsf(d1);
            const float sum = a0 + a1;
            const float t = a0 / sum;
            const float vx = end_x - cur_x;
            const float vy = end_y - cur_y;
            const float vz = end_z - cur_z;
            const float dist = func_0024bd60(
                *reinterpret_cast<const s8*>(planes + 4),
                *reinterpret_cast<const s8*>(planes + 5),
                planes,
                cur_x + vx * t,
                cur_y + vy * t,
                cur_z + vz * t,
                eps);
            if (dist >= 0.0f) {
                hit_idx = i;
                const float t2 = (a0 + dist) / sum;
                cur_x = cur_x + vx * t2;
                cur_y = cur_y + vy * t2;
                cur_z = cur_z + vz * t2;
            }
        }
    }

    if (hit_idx == -1) {
        out[0] = p0[0];
        out[1] = p0[1];
        out[2] = p0[2];
    } else {
        out[0] = cur_x;
        out[1] = cur_y;
        out[2] = cur_z;
    }
    return hit_idx;
}

extern "C" u32 script_vm_func_00297674();
extern "C" void shop_func_00297178(void* self, u32 state);
extern "C" u32 script_vm_func_002a0f88();
extern "C" void func_00232974(void* self, void* buf);
extern "C" void script_vm_func_00295904(u32 id, const void* buf);
extern "C" void battle_func_002af854(void* p, u32 a1, u32 a2);
extern "C" void camp_func_0026a96c();
extern "C" const u32* camp_func_00220eb4(const void* buf, const void* rhs, u32 flag);
extern "C" s32 camp_func_00309f94(const void* buf, const void* rhs);

// DECOMP_FUNC(0x00397d5c, 624)
extern "C" void script_vm_func_00397d5c(u8* self) {
    u8 buf[0x14];
    if (self[0x658] == 0u) {
        if (script_vm_func_002a0f88() == 0u) {
            return;
        }
        func_00232974(self, buf);
        script_vm_func_00295904(0x32u, buf);
        script_vm_func_002971e4(*reinterpret_cast<const u32*>(self + 0x654), 1u);
        self[0x658] = 1u;
        script_vm_func_002b8b78(0x9Au);
        return;
    }

    if (script_vm_func_0019dfbc(*reinterpret_cast<const u32*>(self + 0x654)) != 2u) {
        return;
    }

    if (script_vm_func_00297674() != 0u) {
        shop_func_00297178(self, 2u);
        if (self[0x29] != 0u) {
            script_vm_func_002b8b78(0x97u);
            return;
        }
        const s8 b20 = *reinterpret_cast<const s8*>(self + 0x20);
        if (b20 == 2 || b20 == 6) {
            script_vm_func_002b8b78(0x96u);
        } else {
            script_vm_func_002b8b78(0x95u);
        }
        return;
    }

    battle_func_002af854(self + 0x794, 0u, 1u);
    const s8 b649 = *reinterpret_cast<const s8*>(self + 0x649);
    if (b649 != 0 && b649 != 1) {
        camp_func_0026a96c();
        shop_func_00297178(self, 7u);
        return;
    }

    func_00232974(self, buf);
    const s16* const t1_keys = reinterpret_cast<const s16*>(0x00405160u);
    const u16* const t1_vals = reinterpret_cast<const u16*>(0x00405368u);
    const s16* const t2_keys = reinterpret_cast<const s16*>(0x00405570u);
    const u16* const t2_vals = reinterpret_cast<const u16*>(0x00405618u);

    for (s32 i = 0; i <= 8; ++i) {
        const u8 b0 = self[0xB0 + i * 2];
        const s8 b1 = *reinterpret_cast<const s8*>(self + 0xB1 + i * 2);
        const s16 key = static_cast<s16>((static_cast<u16>(b0) << 8) | static_cast<u8>(b1));

        bool found = false;
        for (s32 j = 0; j < 0x104; ++j) {
            if (t1_keys[j] == key) {
                const u16 val = t1_vals[j];
                buf[i * 2] = static_cast<u8>(val >> 8);
                buf[i * 2 + 1] = static_cast<u8>(val);
                found = true;
                break;
            }
        }
        if (!found) {
            for (s32 j = 0; j < 0x54; ++j) {
                if (t2_keys[j] == key) {
                    const u16 val = t2_vals[j];
                    buf[i * 2] = static_cast<u8>(val >> 8);
                    buf[i * 2 + 1] = static_cast<u8>(val);
                    break;
                }
            }
        }
    }

    const u32* const res_ptr = camp_func_00220eb4(buf, self + 0x94E, 1u);
    const s32 len = camp_func_00309f94(buf, self + 0x94E);
    if (*res_ptr == 0u && len < 6) {
        camp_func_0026a96c();
        shop_func_00297178(self, 7u);
    } else {
        shop_func_00297178(self, 6u);
        script_vm_func_002971e4(*reinterpret_cast<const u32*>(self + 0x654), 4u);
    }
}

extern "C" u32 engine_func_0017f928(s32 b1, s32 b0);
extern "C" u32 engine_func_002c3290(const char* s);

// DECOMP_FUNC(0x001eb498, 628)
extern "C" s32 engine_func_001eb498(const s8* src, u16* dst, s32 count_only) {
    struct TagEntry {
        u16 code;
        u16 pad0;
        s32 has_arg;
        u32 pad1;
        const char* prefix;
    };

    const TagEntry* const table = reinterpret_cast<const TagEntry*>(0x00464DA8u);
    s32 src_off = 0;
    s32 out_idx = 0;

    for (;;) {
        const s8* const cur = src + src_off;
        const u32 ch = engine_func_0017f928(cur[1], cur[0]);
        if (ch == 0xFFFFu) {
            if (count_only == 0) {
                dst[out_idx] = 0xFFFFu;
            }
            return out_idx + 1;
        }

        bool handled_tag = false;
        for (s32 t = 0; table[t].code != 0xF890u; ++t) {
            const TagEntry& entry = table[t];
            if (entry.prefix == nullptr) {
                continue;
            }
            const u32 plen = engine_func_002c3290(entry.prefix);
            if (engine_func_002b45f8(entry.prefix, reinterpret_cast<const char*>(cur), plen) != 0) {
                continue;
            }

            u32 pos = engine_func_002c3290(entry.prefix);
            s32 has_extra = 0;
            u16 extra_val = 0;
            if (entry.has_arg != 0) {
                u32 acc = 0u;
                while (static_cast<u8>(cur[pos]) != 0u) {
                    const s8 c = cur[pos];
                    if (c == '>') {
                        ++pos;
                        break;
                    }
                    acc <<= 4;
                    if (c >= '0' && c <= '9') {
                        acc += static_cast<u32>(c - '0');
                    } else if (c >= 'A' && c <= 'F') {
                        acc += static_cast<u32>(c - 'A' + 10);
                    } else if (c >= 'a' && c <= 'f') {
                        acc += static_cast<u32>(c - 'a' + 10);
                    }
                    ++pos;
                }
                if (acc == 0xFFu) {
                    acc = 0u;
                }
                has_extra = 1;
                extra_val = static_cast<u16>(acc + 1u);
            }

            if (entry.code == 0xFFFFu) {
                break;
            }

            if (count_only == 0) {
                dst[out_idx] = static_cast<u16>((entry.code >> 8) | ((entry.code & 0xFFu) << 8));
            }
            ++out_idx;
            src_off += static_cast<s32>(pos);
            if (has_extra != 0) {
                if (count_only == 0) {
                    dst[out_idx] = extra_val;
                }
                ++out_idx;
            }
            handled_tag = true;
            break;
        }
        if (handled_tag) {
            continue;
        }

        if (count_only == 0) {
            dst[out_idx] = static_cast<u16>(ch);
        }
        ++out_idx;
        src_off += 2;

        const u16 rev_ch = static_cast<u16>(((ch >> 8) & 0xFFu) | ((ch & 0xFFu) << 8));
        if (rev_ch >= 0xF801u && rev_ch <= 0xF890u) {
            s32 n_extra = 0;
            for (s32 t = 0; table[t].code != 0xF890u; ++t) {
                if (table[t].code == rev_ch) {
                    n_extra = table[t].has_arg;
                    break;
                }
            }
            for (s32 k = 0; k < n_extra; ++k) {
                const u32 ex = engine_func_0017f928(src[src_off + 1], src[src_off]);
                if (count_only == 0) {
                    dst[out_idx] = static_cast<u16>(ex);
                }
                ++out_idx;
                src_off += 2;
            }
        }
    }
}

extern "C" u32 func_0023ebc0(void* p);
extern "C" u32 func_00385d0c(void* p);
extern "C" u32 func_00385d2c(void* p);
extern "C" const u8* script_vm_func_00235510(void* p, u32 idx);
extern "C" s32 camp_func_00385d14(void* p);
extern "C" void camp_func_002b7f08(void* base, u32 count, u32 elem_size, const void* cmp);
extern "C" s32 ui_func_00297004(u32 a0, s32 a1);
extern "C" void engine_func_0031e438(void* obj, const char* name, u32 a2);

// DECOMP_FUNC(0x0038350c, 628)
extern "C" void script_vm_func_0038350c(u8* self) {
    if (func_0023ebc0(self + 0x20) == 0u ||
        func_00385d0c(self + 0x20) == 0u ||
        func_00385d2c(self + 0x20) == 0u) {
        return;
    }

    const u8* const base = script_vm_func_00235510(self + 0x20, 0u);
    if (camp_func_00385d14(self + 0x20) > 0) {
        s32 i = 0;
        do {
            const u8* const entry = base + i * 0x88u;
            const s32 target = *reinterpret_cast<const s8*>(self + 0x10);
            if (static_cast<s32>(*reinterpret_cast<const u16*>(entry + 0x60)) == target) {
                const u16 req_flag = *reinterpret_cast<const u16*>(entry + 0x66);
                const u16 blk_flag = *reinterpret_cast<const u16*>(entry + 0x68);
                if ((req_flag == 0u || script_vm_func_002c0ba8(req_flag) != 0u) &&
                    (blk_flag == 0u || script_vm_func_002c0ba8(blk_flag) == 0u)) {
                    const s32 count = *reinterpret_cast<const s32*>(self + 0xD8C);
                    const u32 key = *reinterpret_cast<const u16*>(entry + 0x62);
                    bool dup = false;
                    for (s32 j = 0; j < count; ++j) {
                        if (*reinterpret_cast<const u32*>(self + 0xD60 + j * 8) == key) {
                            dup = true;
                            break;
                        }
                    }
                    if (!dup) {
                        *reinterpret_cast<s32*>(self + 0xD5C + count * 8) = i;
                        *reinterpret_cast<u32*>(self + 0xD60 + count * 8) = key;
                        const u32 next_count = static_cast<u32>(*reinterpret_cast<const s32*>(self + 0xD8C) + 1);
                        *reinterpret_cast<u32*>(self + 0xD8C) = next_count;
                        if (next_count >= 6u) {
                            break;
                        }
                    }
                }
            }
            ++i;
        } while (i < camp_func_00385d14(self + 0x20));
    }

    camp_func_002b7f08(
        self + 0xD5C,
        *reinterpret_cast<const u32*>(self + 0xD8C),
        8u,
        reinterpret_cast<const void*>(0x00381D8Cu));

    if (self[0x18] == 1u) {
        for (u32 slot = 0u; slot < 6u; ++slot) {
            const s32 count = *reinterpret_cast<const s32*>(self + 0xD8C);
            const u32 want = slot + 1u;
            s32 val = -1;
            for (s32 j = 0; j < count; ++j) {
                if (*reinterpret_cast<const u32*>(self + 0xD60 + j * 8) == want) {
                    const u8* const e = script_vm_func_00235510(
                        self + 0x20,
                        *reinterpret_cast<const u32*>(self + 0xD5C + j * 8));
                    const u16 h64 = *reinterpret_cast<const u16*>(e + 0x64);
                    val = (h64 == 2u) ? 1 : 2;
                    break;
                }
            }
            if (val < 0) {
                val = ui_func_00297004(1u, 2);
            }

            char name[0x40];
            ui_func_002be7fc(name, "hunter_company_npc%d_%d", want, val);
            void* const obj0 = *reinterpret_cast<void**>(*reinterpret_cast<u8**>(self + 0xD10 + slot * 4u) + 8);
            engine_func_0031e438(obj0, name, 0u);

            ui_func_002be7fc(name, "hunter_company_npc%d_%d_add1", want, val);
            void* const obj1 = *reinterpret_cast<void**>(*reinterpret_cast<u8**>(self + 0xD28 + slot * 4u) + 8);
            engine_func_0031e438(obj1, name, 0u);
        }
    }

    *reinterpret_cast<u32*>(self + 4) = 2u;
    *reinterpret_cast<u32*>(self + 8) = 0u;
}

extern "C" s32 engine_func_002c54d8(u32* out, u32 a1, u32 a2);
extern "C" void engine_func_002c5468(s32 err);
extern "C" s32 engine_func_002c5450(u32* out, u32 handle, u32 a2);
extern "C" void* engine_func_002c34a4(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 a5);
extern "C" void nn_sdk_func_002bcf34(void* dst, void* buf, u32 size);
extern "C" u32 nn_sdk_func_002bce50(
    void* thread_out, const void* desc, u32 entry, void* arg_ptr,
    u32 stack_top, u32 prio, s32 core, u32 a7);
extern "C" u32 func_002cbdac(u32 rc);

// DECOMP_FUNC(0x002237a0, 632)
extern "C" u32 SaveLoad_Thread_func_002237a0(u8* self, u32 mode) {
    self[1] = static_cast<u8>(mode);

    u32 tmp = 0u;
    s32 res = engine_func_002c54d8(&tmp, 0u, 1u);
    if (res >= 0) {
        *reinterpret_cast<u32*>(self + 0x4C) = tmp;
        res = 0;
    }
    if (res < 0) {
        engine_func_002c5468(res);
    }

    const s32 res2 = engine_func_002c5450(&tmp, *reinterpret_cast<const u32*>(self + 0x4C), 1u);
    if (res2 < 0) {
        engine_func_002c5468(res2);
    }

    void* const buf = engine_func_002c34a4(0x100u, 0x100u, 0u, 0x2000u, 0x1000u, 1u);
    *reinterpret_cast<void**>(self + 0x28) = buf;
    nn_sdk_func_002bcf34(self + 0x2C, buf, 0x2000u);

    u32 rc = 0xE7E3FFFFu;
    if (mode <= 3u) {
        struct ThreadDesc {
            u32 w0;
            u32 name_addr;
            u32 w2;
            u32 entry_addr;
        };
        u32 entry_addr = 0u;
        if (mode == 1u) {
            entry_addr = 0x002EF824u;
        } else if (mode == 0u || mode == 3u) {
            entry_addr = 0x002D8E0Cu;
        } else {
            entry_addr = 0x002D8ED4u;
        }

        ThreadDesc desc;
        desc.w0 = 4u;
        desc.name_addr = 0x003F70B0u;
        desc.w2 = 0x003F7210u;
        desc.entry_addr = 0x003F717Cu;
        u8* self_arg = self;
        const u32 stack_top = *reinterpret_cast<const u32*>(self + 0x34) + *reinterpret_cast<const u32*>(self + 0x38);
        rc = nn_sdk_func_002bce50(self + 0x44, &desc, entry_addr, &self_arg, stack_top, 0x11u, -2, 0u);
        if ((rc & 0x07E00000u) != 0x00600000u && static_cast<s32>(rc) < 0) {
            engine_func_002c5468(static_cast<s32>(rc));
        }
    }

    return (func_002cbdac(rc) == 0u) ? 1u : 0u;
}

extern "C" u8* ui_func_002c0ac8();
extern "C" void ui_func_002c1b64(void* g);
extern "C" void ui_func_002c3ba8(void* g);
extern "C" void func_0032af00();
extern "C" void ui_func_002c1d3c(void* g, u32 a1);
extern "C" void func_002b7a10(
    const float* c0, const float* c1, const float* c2, const float* c3,
    float x, float y, float w, float h, float z);
extern "C" void ui_func_002c1abc(void* g);
extern "C" void script_vm_func_00262a54(char* dst, const char* src, u32 max_len);

// DECOMP_FUNC(0x002016cc, 640)
extern "C" u32 ui_func_002016cc() {
    u8* const state = ui_func_002c0ac8();
    u8* const g = *reinterpret_cast<u8**>(0x0044EA00u);

    if (*reinterpret_cast<const u32*>(state + 0x10) != 1u) {
        ui_func_002c1b64(*reinterpret_cast<void**>(0x0044EA00u));
        ui_func_002c3ba8(*reinterpret_cast<void**>(0x0044EA00u));
        func_0032af00();

        const float alpha = *reinterpret_cast<const float*>(state + 0x6C);
        if (alpha != 0.0f) {
            ui_func_002c3ba8(*reinterpret_cast<void**>(0x0044EA00u));

            typedef void (*ApplyBlendFn)(u32);
            u8* const stack = *reinterpret_cast<u8**>(0x0044EA00u) + 0x124C;
            const u32 val = ui_func_002c5f7c(1u, 0u);
            const u32 depth = *reinterpret_cast<u32*>(stack);
            const u32 prev_val = *reinterpret_cast<u32*>(stack + 8 + depth * 4u);
            const u32 next_depth = depth + 1u;
            *reinterpret_cast<u32*>(stack) = next_depth;
            *reinterpret_cast<u32*>(stack + 8 + next_depth * 4u) = val;
            if (stack[0x18] != 0u || prev_val != val) {
                reinterpret_cast<ApplyBlendFn>(*reinterpret_cast<const u32*>(stack + 0x1C))(val);
                stack[0x18] = 0u;
            }

            float quad[4];
            quad[0] = 1.0f;
            quad[1] = 1.0f;
            quad[2] = 1.0f;
            quad[3] = *reinterpret_cast<const float*>(state + 0x6C);
            ui_func_002c1d3c(*reinterpret_cast<void**>(0x0044EA00u), 0u);
            func_002b7a10(quad, quad, quad, quad, 0.0f, 0.0f, 400.0f, 240.0f, 0.95703125f);

            u8* const stack2 = *reinterpret_cast<u8**>(0x0044EA00u) + 0x124C;
            const u32 depth2 = *reinterpret_cast<u32*>(stack2);
            const u32 popped = *reinterpret_cast<u32*>(stack2 + 8 + depth2 * 4u);
            const u32 prev_depth = depth2 - 1u;
            *reinterpret_cast<u32*>(stack2) = prev_depth;
            const u32 restore = *reinterpret_cast<u32*>(stack2 + 8 + prev_depth * 4u);
            if (stack2[0x18] != 0u || popped != restore) {
                reinterpret_cast<ApplyBlendFn>(*reinterpret_cast<const u32*>(stack2 + 0x1C))(restore);
                stack2[0x18] = 0u;
            }
        }
    } else {
        const s32 total = *reinterpret_cast<const s32*>(state + 0x60);
        s32 count = 10;
        s32 start = 0;
        if (total < 10) {
            count = total;
        } else {
            const s32 sel = *reinterpret_cast<const s32*>(state + 0x68);
            if (sel >= 10) {
                start = sel - 9;
            }
        }

        for (s32 i = 0; i < count; ++i) {
            const s32 idx = i + start;
            s32 color = -1;
            if (*reinterpret_cast<const s32*>(state + 0x68) == idx) {
                color = 0x00FF00FF;
                ui_func_002be77c(2u, 0x00FF00FF, ">", 8.0f, static_cast<float>(i * 14), 0.1f, 0.0f, 1.0f);
            }
            const char* const items = *reinterpret_cast<const char* const*>(state + 0x64);
            char buf[0x44];
            script_vm_func_00262a54(buf, items + idx * 0x228u, 0x40u);
            ui_func_002be77c(2u, color, buf, 20.0f, static_cast<float>(i * 14), 0.1f, 1.0f, 1.0f);
        }
    }

    (void)g;
    ui_func_002c1b64(*reinterpret_cast<void**>(0x0044EA00u));
    ui_func_002c1abc(*reinterpret_cast<void**>(0x0044EA00u));
    return 0u;
}

extern "C" u32 engine_func_0027d010();
extern "C" void script_vm_func_00152af8(void* p);
extern "C" void script_vm_func_002a7aa0(void* p);
extern "C" void engine_func_0028c8a8(void* sub, u32 a1, const void* vec);
extern "C" void engine_func_0028c880(void* sub, u32 a1, float f0, float f1, float f2);
extern "C" void engine_func_002a5a54(void* sub, float f0);
extern "C" void battle_func_00267420(s32 a0, f32 f0, f32 f1, f32 f2, f32 f3, f32 f4, f32 f5, f32 f6);

// DECOMP_FUNC(0x0027521c, 640)
extern "C" void engine_func_0027521c() {
    u8* const* const g_ptr = reinterpret_cast<u8* const*>(0x00447A48u);
    u8* const obj = *g_ptr;

    if (obj[4] == 0u) {
        const u8* const g8 = reinterpret_cast<const u8*>(0x0049F91Cu);
        for (s32 i = 0; i < 24; ++i) {
            u8* const e = (*g_ptr) + 0x1C + i * 0x28u;
            if (e[0] == 0u) {
                continue;
            }
            u32* const node_flags = *reinterpret_cast<u32**>(e + 0x18);
            const u32 flags = *node_flags;
            if (g8[0x22] != 0u) {
                if ((flags & 2u) == 0u) {
                    *node_flags = flags | 2u;
                    u8* const sub = *reinterpret_cast<u8**>(reinterpret_cast<u8*>(node_flags) + 8);
                    (*reinterpret_cast<u8**>(sub + 0x2C))[0x1F6] = 0u;
                }
                continue;
            }

            if ((flags & 2u) != 0u) {
                *node_flags = flags & ~2u;
                u8* const sub = *reinterpret_cast<u8**>(reinterpret_cast<u8*>(node_flags) + 8);
                (*reinterpret_cast<u8**>(sub + 0x2C))[0x1F6] = 1u;
            }

            if (e[1] != 0u) {
                u8* const sub0 = *reinterpret_cast<u8**>((*reinterpret_cast<u8**>(e + 0x18)) + 8);
                engine_func_0028c8a8(sub0, 0u, e + 4);
                u8* const sub1 = *reinterpret_cast<u8**>((*reinterpret_cast<u8**>(e + 0x18)) + 8);
                engine_func_0028c880(sub1, 0u, 0.0f, *reinterpret_cast<const float*>(e + 0x10), 0.0f);
                u8* const sub2 = *reinterpret_cast<u8**>((*reinterpret_cast<u8**>(e + 0x18)) + 8);
                if (*reinterpret_cast<const s32*>(sub2 + 0x38) != static_cast<s32>(*reinterpret_cast<const s16*>(e + 0x14))) {
                    engine_func_002a5a54(sub2, 0.0f);
                }
                e[1] = 0u;
            }
        }
        return;
    }

    const u32 state = *reinterpret_cast<const u32*>(obj);
    if (state == 0u) {
        for (s32 i = 23; i >= 0; --i) {
            void* const p = *reinterpret_cast<void**>((*g_ptr) + 0x34 + i * 0x28u);
            if (p != nullptr) {
                script_vm_func_00152af8(p);
            }
        }
        *reinterpret_cast<u32*>(*g_ptr) += 1u;
    } else if (state == 1u) {
        for (s32 i = 23; i >= 0; --i) {
            void* const p = *reinterpret_cast<void**>((*g_ptr) + 0x34 + i * 0x28u);
            if (p != nullptr) {
                script_vm_func_002a7aa0(p);
                *reinterpret_cast<u32*>((*g_ptr) + 0x34 + i * 0x28u) = 0u;
            }
        }
        u8* const o2 = *g_ptr;
        for (s32 i = 0; i < 24; ++i) {
            o2[0x1C + i * 0x28u] = 0u;
        }
        *reinterpret_cast<u32*>(o2) += 1u;
    } else if (state == 2u) {
        if (engine_func_0027d010() != 0u) {
            for (s32 i = 0; i < 24; ++i) {
                const u8* const e = (*g_ptr) + 0x1C + i * 0x28u;
                if (e[0] != 0u && *reinterpret_cast<const u16*>(e + 0x16) == 0x0Cu) {
                    const float* const f = reinterpret_cast<const float*>(e + 4);
                    battle_func_00267420(
                        *reinterpret_cast<const s16*>(e + 0x1C),
                        f[0], f[1], f[2], f[3], 600.0f, 350.0f, 160.0f);
                }
            }
            u8* const o2 = *g_ptr;
            o2[4] = 0u;
            *reinterpret_cast<u32*>(o2) = 0u;
        }
    }
}

// DECOMP_FUNC(0x0036ee9c, 640)
extern "C" u8* engine_func_0036ee9c(const u8* desc, void* alloc) {
    typedef u8* (*AllocFn)(void* alloc, u32 size, u32 align);
    auto call_alloc = [&](u32 size, u32 align) -> u8* {
        void** const vtbl = *reinterpret_cast<void***>(alloc);
        return reinterpret_cast<AllocFn>(vtbl[2])(alloc, size, align);
    };

    const u32 fmt = *reinterpret_cast<const u32*>(desc + 0x14);
    const s32 min_dim = (fmt == 0xCu) ? 16 : 8;

    u8* const hdr = call_alloc(0x3Cu, 4u);
    if (hdr != nullptr) {
        for (u32 i = 0; i < 15u; ++i) {
            *reinterpret_cast<u32*>(hdr + i * 4u) = 0u;
        }
    }

    const u32* const t0 = reinterpret_cast<const u32*>(0x004091F8u);
    const u32* const t1 = t0 + 0x0E;
    *reinterpret_cast<u32*>(hdr + 0x00) = 0x20000011u;
    *reinterpret_cast<u32*>(hdr + 0x04) = 0x4D495854u;
    *reinterpret_cast<u32*>(hdr + 0x08) = 0x05000000u;
    *reinterpret_cast<u32*>(hdr + 0x0C) = 0u;
    *reinterpret_cast<u32*>(hdr + 0x10) = 0u;
    *reinterpret_cast<u32*>(hdr + 0x14) = 0u;
    *reinterpret_cast<u32*>(hdr + 0x18) = *reinterpret_cast<const u32*>(desc + 0x00);
    *reinterpret_cast<u32*>(hdr + 0x1C) = *reinterpret_cast<const u32*>(desc + 0x04);
    *reinterpret_cast<u32*>(hdr + 0x20) = t0[fmt];
    *reinterpret_cast<u32*>(hdr + 0x24) = t1[fmt];
    *reinterpret_cast<u32*>(hdr + 0x28) = *reinterpret_cast<const u32*>(desc + 0x08);
    *reinterpret_cast<u32*>(hdr + 0x2C) = 0u;
    *reinterpret_cast<u32*>(hdr + 0x30) = *reinterpret_cast<const u32*>(desc + 0x0C);
    *reinterpret_cast<u32*>(hdr + 0x34) = fmt;

    u8* const sub = call_alloc(0x20u, 4u);
    if (sub != nullptr) {
        for (u32 i = 0; i < 8u; ++i) {
            *reinterpret_cast<u32*>(sub + i * 4u) = 0u;
        }
    }

    *reinterpret_cast<void**>(sub + 0x10) = alloc;
    *reinterpret_cast<u32*>(sub + 0x00) = *reinterpret_cast<const u32*>(desc + 0x00);
    *reinterpret_cast<u32*>(sub + 0x04) = *reinterpret_cast<const u32*>(desc + 0x04);
    *reinterpret_cast<u32*>(sub + 0x18) = *reinterpret_cast<const u32*>(desc + 0x10);
    const float bpp = reinterpret_cast<const float*>(0x00409268u)[fmt];
    *reinterpret_cast<u32*>(sub + 0x14) = static_cast<u32>(bpp * 8.0f);

    s32 w = *reinterpret_cast<const s32*>(desc + 0x00);
    s32 h = *reinterpret_cast<const s32*>(desc + 0x04);
    const s32 mips = *reinterpret_cast<const s32*>(desc + 0x08);
    s32 rem = mips;
    u32 total_bytes = 0u;
    while (rem > 0) {
        const u32 mip_bytes = static_cast<u32>(bpp * static_cast<float>(w) * static_cast<float>(h));
        total_bytes += mip_bytes;
        if (w == min_dim && h == min_dim) {
            *reinterpret_cast<u32*>(hdr + 0x28) = static_cast<u32>(mips - rem + 1);
            break;
        }
        if (w > min_dim) {
            w /= 2;
        }
        if (h > min_dim) {
            h /= 2;
        }
        --rem;
    }

    if (desc[0x19] == 0u) {
        *reinterpret_cast<u32*>(sub + 0x08) = 0u;
        *reinterpret_cast<u32*>(sub + 0x0C) = 0u;
    } else {
        u8* const px = call_alloc(total_bytes, 0x80u);
        if (desc[0x18] != 0u && total_bytes != 0u) {
            for (u32 i = 0; i < total_bytes; ++i) {
                px[i] = 0u;
            }
        }
        *reinterpret_cast<u32*>(sub + 0x08) = total_bytes;
        *reinterpret_cast<u32*>(sub + 0x0C) =
            (px != nullptr) ? static_cast<u32>(px - (sub + 0x0C)) : 0u;
    }

    *reinterpret_cast<u32*>(hdr + 0x38) =
        (sub != nullptr) ? static_cast<u32>(sub - (hdr + 0x38)) : 0u;
    return hdr;
}

extern "C" void func_0020d788();
extern "C" void func_002aa418(
    u32 c0, u32 c1, u32 c2, u32 c3,
    float x, float y, float w, float h,
    float u0, float v0, float u1, float v1, float z);

// DECOMP_FUNC(0x001f9c3c, 644)
extern "C" void func_001f9c3c() {
    u8* const g = *reinterpret_cast<u8* const*>(0x00447600u);
    if (g == nullptr || *reinterpret_cast<const u32*>(g + 4) != 8u ||
        reinterpret_cast<const u8*>(0x0049F91Cu)[0x20] != 0u) {
        return;
    }

    for (s32 i = 0; i < 32; ++i) {
        u8* const e = g + 0x34 + i * 0x180u;
        if (e[0] == 0u) {
            continue;
        }
        e[0x15C] = 0u;
        if (e[0x13E] == 0u || e[0x17C] == 0u || e[0x144] == 0u) {
            continue;
        }

        func_0020d788();
        if (e[0x7E] != 0u) {
            continue;
        }

        const float f80 = *reinterpret_cast<const float*>(e + 0x80);
        float px = 0.0f;
        float py = 0.0f;
        if (f80 > 0.0f) {
            if (f80 <= 90.0f) {
                px = 0.0f;
                py = f80 * 2.2f;
            } else {
                px = (f80 - 90.0f) * 1.9888889f;
                py = 198.0f;
            }
        } else {
            const float neg = -f80;
            if (neg <= 90.0f) {
                px = 358.0f;
                py = neg * 2.2f;
            } else {
                px = 358.0f - (neg - 90.0f) * 1.9888889f;
                py = 198.0f;
            }
        }

        const s32 rem = *reinterpret_cast<const s32*>(e + 0x140) % 20;
        const float u0 = (rem < 10) ? 0.0f : 0.328125f;
        const float u1 = 0.328125f;

        const s32 val148 = *reinterpret_cast<const s32*>(e + 0x148);
        u32 c0 = 0xFFFFFFFFu;
        u32 c1 = 0x2DB5FFFFu;
        if (val148 < 0x43C80000) {
            c0 = 0xEF6C3EFFu;
            c1 = 0xFE0B22FFu;
        } else if (val148 < 0x44480000) {
            c0 = 0xFBC30DFFu;
            c1 = 0xFF6C2BFFu;
        } else if (val148 < 0x44960000) {
            c0 = 0xFFF2C0FFu;
            c1 = 0xFFD52DFFu;
        }

        e[0x15C] = 1u;
        *reinterpret_cast<float*>(e + 0x160) = px + 12.0f;
        *reinterpret_cast<float*>(e + 0x164) = py + 12.0f;
        func_002aa418(c0, c1, c0, c1, px, py, 42.0f, 42.0f, u0, 0.0f, u1, 0.65625f, 0.0f);
        func_002aa418(0xFFu, 0xFFu, 0xFFu, 0xFFu, px, py, 42.0f, 42.0f, 0.65625f, 0.0f, 0.328125f, 0.65625f, 0.0f);
    }
}

extern "C" s32 shop_func_0029ebc4(void* p);
extern "C" s32 unite_func_002338ac(void* p);
extern "C" const u8* camp_func_002b9364(u32 id);
extern "C" u32 camp_func_0029d100(u32 item_id, u32 mode, u32 a2, u32 a3, u32 a4);

// DECOMP_FUNC(0x0022d33c, 652)
extern "C" void camp_func_0022d33c(u8* self) {
    if (*reinterpret_cast<const u32*>(self + 0x28) == 0u) {
        return;
    }

    const s32 start_idx = shop_func_0029ebc4(self + 0x20);
    const s32 count = unite_func_002338ac(self + 0x20);
    s32* const g_last = reinterpret_cast<s32*>(0x0043D9C8u);
    if (start_idx == g_last[1]) {
        return;
    }
    g_last[1] = start_idx;
    if (count <= 0) {
        return;
    }

    for (s32 i = 0; i < count; ++i) {
        const u16 item_id = *reinterpret_cast<const u16*>(self + (start_idx + i) * 32 + 0x5AC);
        const bool has_a4 = (self[0x5A4] != 0u);
        u32 color_cmp = 0xFFFFFFFFu;

        const s32 cur_idx = shop_func_0029ebc4(self + 0x20) + i;
        const u8* const entry = self + cur_idx * 32 + 0x5AC;
        const u8 mode = self[0x5A5];
        u32 val8 = 0u;
        if (has_a4) {
            if (mode == 0u) {
                val8 = entry[0xC];
            } else if (mode == 1u) {
                val8 = entry[0xD];
            }
        } else {
            if (mode == 0u) {
                const u8* const info = camp_func_002b9364(*reinterpret_cast<const u16*>(entry));
                if (info != nullptr) {
                    val8 = info[3];
                }
            } else if (mode == 1u) {
                val8 = entry[0xC];
            } else if (mode == 2u) {
                val8 = entry[0xD];
            }
        }

        if (self[0x5A4] == 1u && self[0x5A5] == 1u) {
            const s32 cur_idx2 = shop_func_0029ebc4(self + 0x20) + i;
            const u8* const entry2 = self + cur_idx2 * 32 + 0x5AC;
            u32 base_val = 0u;
            if (has_a4) {
                base_val = entry2[0xC];
            } else {
                const u8* const info = camp_func_002b9364(*reinterpret_cast<const u16*>(entry2));
                if (info != nullptr) {
                    base_val = info[3];
                }
            }
            if (val8 > base_val) {
                color_cmp = 0x72E027FFu;
            } else if (val8 < base_val) {
                color_cmp = 0xDC0F14FFu;
            }
        }

        u32* const g_arr = reinterpret_cast<u32*>(0x0049357Cu);
        g_arr[i] = val8;
        g_arr[10 + i] = color_cmp;

        const u32 arg_a4 = (self[0x5A4] != 0u) ? 1u : 0u;
        const u8* const pos0 = camp_func_002bf6c8(self + 0xC8, static_cast<u32>(i + 0x42F));
        const s32 x0 = *reinterpret_cast<const s16*>(pos0 + 8);
        const s32 y0 = *reinterpret_cast<const s16*>(pos0 + 0xA);
        const u32 ge100 = (*reinterpret_cast<const s8*>(self + 0x94) >= 100) ? 1u : 0u;
        const u32 price = camp_func_0029d100(item_id, self[0x5A5], arg_a4, ge100, 0u);

        u32 price_color = 0xFFFFFFFFu;
        if (self[0x5A4] == 1u) {
            const u32 ge100_2 = (*reinterpret_cast<const s8*>(self + 0x94) >= 100) ? 1u : 0u;
            const u32 base_price = camp_func_0029d100(item_id, 0u, arg_a4, ge100_2, 0u);
            if (price < base_price) {
                price_color = 0xDC0F14FFu;
            } else if (price > base_price) {
                price_color = 0x72E027FFu;
            }
        }

        const u8* const pos1 = camp_func_002bf6c8(self + 0xC8, 0x4C6u);
        u8* const g_out = reinterpret_cast<u8*>(0x004935CCu);
        *reinterpret_cast<s32*>(g_out + i * 4) = *reinterpret_cast<const s16*>(pos1 + 8) + x0;
        *reinterpret_cast<s32*>(g_out + 0x28 + i * 4) = *reinterpret_cast<const s16*>(pos1 + 0xA) + y0;
        ui_func_002be7fc(reinterpret_cast<char*>(g_out + 0x50 + i * 0x20), "%8u", price);
        *reinterpret_cast<u32*>(reinterpret_cast<u8*>(0x0049375Cu) + i * 4) = price_color;
    }
}

extern "C" u32 ui_func_0026b7cc();
extern "C" void engine_func_002b8584(u32 a0);
extern "C" void engine_func_002a150c(void* dst, u32 a1);
extern "C" void shop_func_002339e8(void* p);
extern "C" void shop_func_002339ac(void* p);
extern "C" void camp_func_00233ac0(void* self, s32 a1, u32 a2);
extern "C" u32 func_002f61a4();
extern "C" u32 camp_func_002c1830(u32 a0, u32 a1);
extern "C" void camp_func_002bc200(u32 id);
extern "C" void script_vm_func_00289984();
extern "C" void script_vm_func_0023554c();
extern "C" void func_002fea30();
extern "C" void camp_func_002b9008();
extern "C" void script_vm_func_00262bcc(u32 a0, u32 a1);

// DECOMP_FUNC(0x00392060, 656)
extern "C" void script_vm_func_00392060(u8* self) {
    auto finish_with_status = [&](u32 status) {
        *reinterpret_cast<u32*>(self + 4) = status;
        *reinterpret_cast<u32*>(self + 8) = 0u;
        u8* const vobj = *reinterpret_cast<u8**>(self + 0x208);
        if (vobj != nullptr) {
            typedef void (*Vfunc1)(u8*);
            void** const vtbl = *reinterpret_cast<void***>(vobj);
            reinterpret_cast<Vfunc1>(vtbl[1])(vobj);
            *reinterpret_cast<u32*>(self + 0x208) = 0u;
        }
    };

    const u32 state = *reinterpret_cast<const u32*>(self + 8);
    if (state == 0u) {
        engine_func_002b8584(0u);
        u32 tmp = 0u;
        engine_func_002a150c(&tmp, *reinterpret_cast<const u32*>(0x00433158u));
        *reinterpret_cast<u32*>(self) &= ~0x10u;

        u8* const g = *reinterpret_cast<u8* const*>(0x00432FC8u);
        *reinterpret_cast<u32*>(g + 0x754) &= ~0x100u;
        (*reinterpret_cast<u8* const*>(0x00433130u))[0x450C] = 0u;

        shop_func_002339e8(self + 0x2E8);
        shop_func_002339ac(self + 0x2B4);
        (*reinterpret_cast<u8* const*>(0x00432FC8u))[0xD50] = 2u;

        const u32 h = script_vm_func_00291018(*reinterpret_cast<const u32*>(self + 0x350), "aoc_IsConnect");
        script_vm_func_002971e4(*reinterpret_cast<const u32*>(self + 0x358), h);
        camp_func_00233ac0(self, 0, 1u);
        *reinterpret_cast<u32*>(self + 8) = 1u;
    } else if (state == 1u) {
        if (script_vm_func_0019dfbc(*reinterpret_cast<const u32*>(self + 0x358)) != 2u) {
            if (func_002f61a4() != 0u && camp_func_002c1830(1u, 1u) != 0u) {
                camp_func_002bc200(0x0100016Du);
                script_vm_func_00289984();
                script_vm_func_0023554c();
                func_002fea30();
                camp_func_002b9008();
                camp_func_002b9008();
                finish_with_status(0xFu);
            }
            return;
        }

        const u32 r = script_vm_func_00297674();
        if (r == 0u) {
            *reinterpret_cast<u32*>(self + 8) = 2u;
            script_vm_func_00126edc((*reinterpret_cast<u8* const*>(0x00432FC8u)) + 0x80);

            struct TimestampRec {
                u32 hdr;
                u64 ts;
                u32 w3;
                u32 w4;
            } rec{};
            rec.hdr = 0u;
            engine_func_002bb09c(&rec.ts);
            rec.w3 = 0u;
            rec.w4 = 0u;
            u64 tmp_ts = 0u;
            rec.ts = *engine_func_002bad80(&tmp_ts, 0u);
            *reinterpret_cast<u32*>(self + 0x210) = rec.hdr;
            *reinterpret_cast<u64*>(self + 0x214) = rec.ts;
            *reinterpret_cast<u32*>(self + 0x21C) = rec.w3;
            *reinterpret_cast<u32*>(self + 0x220) = rec.w4;

            camp_func_00233ac0(self, -1, 0u);
            script_vm_func_00262bcc(0x01000001u, 0xAu);
        } else if (r == 1u) {
            finish_with_status(0xFu);
        }
    } else if (state == 2u) {
        if (ui_func_0026b7cc() != 0u) {
            finish_with_status(4u);
        }
    }
}

// DECOMP_FUNC(0x0023f65c, 668)
extern "C" void engine_func_002c4b30(void* dst, u32 size);
extern "C" const char* engine_func_00240578(void* ctx);
extern "C" void engine_func_002bf86c(char* dst, const char* src);
extern "C" u32 script_vm_func_00240420(void* fs, const char* path);
extern "C" void engine_func_002c4360(u32 handle);
extern "C" void script_vm_func_00297704(const char* path, void* dst, u32 flag);
extern "C" void script_vm_func_00240158(u32* self, u8* ctx);
extern "C" void script_vm_func_00270298(u32 a0);
extern "C" void func_0033868c(void* ctx);
extern "C" void func_0033a378(void* ctx);
extern "C" void func_00338658(void* ctx);
extern "C" void func_0033a014(void* ctx);
extern "C" void func_003d7228(void* obj);
extern "C" const u8* ui_func_0027dca0(void* ctx, s32 id);
extern "C" u32 func_002406f8(void* ctx, u32 id);
extern "C" void battle_func_00250800(u32 a0, u32 a1, u32 a2, u32 a3, u32 a4, u32 a5, u32 a6);
extern "C" void script_vm_func_00255198(void* ctx);
extern "C" void ui_func_00394e88(u32 a0);
extern "C" u32 script_vm_func_002c2bd0(u32 ch);
extern "C" void script_vm_func_002c2ba4(u32 ch, u32 a1, u32 a2);
extern "C" u32 script_vm_func_00289924();
extern "C" void battle_func_0023fd38(void* self, void* ctx);

extern "C" void script_vm_func_0023f65c(u32* self, u8* ctx) {
    char buf0[0x80];
    engine_func_002c4b30(buf0, 0x80u);
    engine_func_002bf86c(buf0, engine_func_00240578(ctx));
    if (script_vm_func_00240420(ctx, buf0) != 0u) {
        self[0] = 0xBu;
        char buf1[0x80];
        engine_func_002c4b30(buf1, 0x80u);
        engine_func_002bf86c(buf1, engine_func_00240578(ctx));
        if (self[1] != 0u) {
            engine_func_002c4360(self[1]);
            self[1] = 0u;
        }
        script_vm_func_00297704(buf1, &self[1], 0u);
        self[0] = 0xCu;
        reinterpret_cast<void (*)(void*, void*)>(script_vm_func_00240158)(self, ctx);
        return;
    }

    u32* const f44a0 = reinterpret_cast<u32*>(ctx + 0x44A0);
    self[0] = 0xDu;
    if ((*f44a0 & 0x40000000u) == 0u) {
        script_vm_func_00270298(2u);
        *f44a0 |= 0x40000000u;
    }

    func_0033868c(ctx);
    func_0033a378(ctx);
    func_00338658(ctx);
    func_0033a014(ctx);
    func_003d7228(*reinterpret_cast<void* const*>(0x004342C8u));

    if (ctx[0x44B7] == 0u &&
        ((*reinterpret_cast<const u32*>(ctx + 0xE0) & 0x02000000u) != 0u || (*f44a0 & 2u) != 0u)) {
        for (s32 i = 4; i < 0x36; ++i) {
            u8* const e = (*reinterpret_cast<u8* const*>(ctx + 0x1E98)) + i * 0x114u;
            const u32 w50 = *reinterpret_cast<const u32*>(e + 0x50);
            if ((w50 & 1u) != 0u && (w50 & 2u) != 0u) {
                const u32 w54 = *reinterpret_cast<const u32*>(e + 0x54);
                if ((w54 & 8u) != 0u) {
                    *reinterpret_cast<u32*>(e + 0x54) = w54 & ~8u;
                    if ((*reinterpret_cast<const u16*>(e + 0x58) & 0x800u) == 0u) {
                        const u8* const unit = ui_func_0027dca0(ctx, *reinterpret_cast<const s16*>(e + 0x62));
                        if (func_002406f8(ctx, *reinterpret_cast<const u16*>(unit + 2)) == 0u) {
                            *reinterpret_cast<u16*>(e + 0x58) |= 0x800u;
                        }
                    }
                }
            }
        }

        battle_func_00250800(0u, 0u, 0x0100017Bu, 0u, 0u, 0u, 0u);
        script_vm_func_00255198(ctx);
        *f44a0 |= 0x00200000u;
        if ((*reinterpret_cast<const u32*>(ctx + 0xE4) & 0x20u) == 0u) {
            ui_func_00394e88(3u);
        }
    }

    if (script_vm_func_002c2bd0(0u) == 3u) {
        script_vm_func_002c2ba4(0u, 0xAu, 0xFFu);
    }
    if (script_vm_func_002c2bd0(1u) == 3u) {
        script_vm_func_002c2ba4(1u, 0xAu, 0xFFu);
    }
    if (script_vm_func_00289924() != 0u) {
        self[0] = 0xEu;
        self[3] = 0u;
        battle_func_0023fd38(self, ctx);
    }
}

// DECOMP_FUNC(0x0014a998, 672)
extern "C" float func_002ac0c4(float x);

static inline u32 f32_bits_14a998(float v) {
    u32 u;
    __builtin_memcpy(&u, &v, sizeof(u));
    return u;
}

extern "C" void func_0014a998(const u8* ctx0, u8* out_desc, const u8* params, const u8* proj) {
    auto out_ptr = [out_desc]() -> u32* {
        const u32 off = *reinterpret_cast<const u32*>(out_desc + 0x10);
        return (off != 0u) ? reinterpret_cast<u32*>(out_desc + 0x10 + off) : nullptr;
    };

    out_ptr()[0] = 0u;
    out_ptr()[1] = 0x000F00E6u;
    out_ptr()[3] = 0x07FF00E8u;

    const auto exp_fn = reinterpret_cast<float (*)(float)>(func_002ac0c4);
    const u32 mode = *reinterpret_cast<const u32*>(params) & 0xFFu;
    const float p1 = *reinterpret_cast<const float*>(params + 4);
    const float p2 = *reinterpret_cast<const float*>(params + 8);
    const float p3 = *reinterpret_cast<const float*>(params + 0xC);

    float prev = 0.0f;
    s32 idx = 0;

    for (s32 step = 0; step <= 0x80; ++step) {
        float cur;
        if (*reinterpret_cast<const float*>(ctx0 + 0x160) == 0.0f) {
            const float t = static_cast<float>(step) * (-1.0f / 128.0f);
            const float num = *reinterpret_cast<const float*>(proj + 0x2C) +
                              *reinterpret_cast<const float*>(proj + 0x28) * t;
            const float den = *reinterpret_cast<const float*>(proj + 0x3C) +
                              *reinterpret_cast<const float*>(proj + 0x38) * t;
            cur = (-num) / den;
        } else {
            const float a = *reinterpret_cast<const float*>(ctx0 + 0x158);
            const float b = *reinterpret_cast<const float*>(ctx0 + 0x15C);
            const float t = static_cast<float>(step) * (1.0f / 128.0f);
            cur = a + t * (b - a);
        }

        if (cur <= p1) {
            cur = 1.0f;
        } else if (cur > p2) {
            cur = 0.0f;
        } else if (mode == 1u) {
            cur = (p2 - cur) / (p2 - p1);
        } else if (mode == 2u) {
            cur = exp_fn(-((cur - p1) * p3) / (p2 - p1));
        } else if (mode == 3u) {
            const float y = ((cur - p1) * p3) / (p2 - p1);
            cur = exp_fn(-(y * y));
        }

        if (step > 0) {
            float delta = (cur - prev + 2.0f) * 2048.0f;
            if (delta < 0.0f) {
                delta = 0.0f;
            } else if (static_cast<s32>(f32_bits_14a998(delta)) >= 0x46000000) {
                delta = 8191.0f;
            }
            const u32 diff_u13 = static_cast<u32>(static_cast<s32>(delta - 4096.0f)) & 0x1FFFu;

            u32 val_u11;
            const u32 prev_bits = f32_bits_14a998(prev);
            if (prev <= 0.0f || ((prev_bits << 1) >> 24) == 0xFFu) {
                val_u11 = 0u;
            } else {
                const float scaled = prev * 2048.0f;
                if (scaled >= 2048.0f) {
                    val_u11 = 0x7FFu;
                } else {
                    val_u11 = static_cast<u32>(scaled) & 0x7FFu;
                }
            }

            const u32 packed = diff_u13 | (val_u11 << 13);
            const u32 word_idx = (idx == 0) ? 2u : static_cast<u32>(idx + 3);
            ++idx;
            out_ptr()[word_idx] = packed;
        }

        prev = cur;
    }
}

// DECOMP_FUNC(0x0015b8f8, 680)
extern "C" void func_0015d888(u8** mat);
extern "C" u32 engine_func_002bc300(u32 ptr);

static inline u32 f32_bits_15b8f8(float v) {
    u32 u;
    __builtin_memcpy(&u, &v, sizeof(u));
    return u;
}

extern "C" void engine_func_0015b8f8(u8* self, const u8* src) {
    *reinterpret_cast<u32*>(self + 0x48) = 0x38u;
    u32* const desc = reinterpret_cast<u32*>(self + 0x10);
    desc[0] &= ~0xFu;
    desc[3] &= ~0x0FF00000u;
    desc[4] &= 0xF800F800u;
    desc[5] = (desc[5] & ~0x30u) & ~0x70000000u;
    desc[6] &= ~0x000F0000u;
    desc[7] &= 0xF0000000u;
    desc[13] = 0u;

    const u32 tex_off = *reinterpret_cast<const u32*>(src + 0x38);
    const u8* const tex_obj = (tex_off != 0u) ? (src + 0x38 + tex_off) : nullptr;
    u32 tex_ptr = *reinterpret_cast<const u32*>(tex_obj + 0x18);
    if (tex_ptr == 0u) {
        const u32 data_off = *reinterpret_cast<const u32*>(tex_obj + 0x0C);
        tex_ptr = (data_off != 0u) ? reinterpret_cast<u32>(tex_obj + 0x0C + data_off) : 0u;
    }

    desc[0] |= (*reinterpret_cast<const u32*>(src + 0x34) & 0xFu);
    desc[3] |= 0x00A00000u;
    desc[1] |= 0x000F0000u;
    desc[4] |= (*reinterpret_cast<const u32*>(src + 0x18) & 0x7FFu);
    desc[4] |= ((*reinterpret_cast<const u32*>(src + 0x1C) & ~0xF800u) << 16);
    desc[5] |= 0x20000000u;

    const u32 mat_off = *reinterpret_cast<const u32*>(self + 0x0C);
    u8* mat = (mat_off != 0u) ? (self + 0x0C + mat_off) : nullptr;
    if (mat != nullptr && (*reinterpret_cast<const u32*>(mat) & 0x80000000u) == 0u) {
        mat = nullptr;
    }

    desc[5] |= 0x00100000u;
    *reinterpret_cast<u32*>(mat + 8) = 1u;

    auto mat_sub = [](u8* m) -> u8* {
        const u32 moff = *reinterpret_cast<const u32*>(m + 4);
        return (moff != 0u) ? (m + 4 + moff) : nullptr;
    };

    u32* const sub24_init = reinterpret_cast<u32*>(mat_sub(mat) + 0x24);
    const u32 g0 = *reinterpret_cast<const u32*>(0x00422204u + 4u);
    const u32 g1 = *reinterpret_cast<const u32*>(0x0042221Cu + 4u);
    *sub24_init = (*sub24_init & ~4u) | ((g0 & 1u) << 2);
    *sub24_init = (*sub24_init & ~0x01000000u) | ((g1 & 1u) << 24);

    func_0015d888(&mat);

    *reinterpret_cast<u32*>(mat_sub(mat) + 0x24) |= 2u;
    u32* const sub24_b = reinterpret_cast<u32*>(mat_sub(mat) + 0x24);
    *sub24_b = (*sub24_b & ~0x7000u) | 0x1000u;
    u32* const sub24_c = reinterpret_cast<u32*>(mat_sub(mat) + 0x24);
    *sub24_c = (*sub24_c & ~0x700u) | 0x100u;

    const u32 gpu_addr = engine_func_002bc300(tex_ptr);
    desc[7] |= ((gpu_addr << 1) >> 4);
    desc[13] |= (src[0x3C] == 0u) ? 1u : 0u;

    const float f40 = *reinterpret_cast<const float*>(src + 0x40);
    const u32 f40_bits = f32_bits_15b8f8(f40);
    u32 val24;
    if (f40 <= 0.0f || ((f40_bits << 1) >> 24) == 0xFFu) {
        val24 = 0u;
    } else {
        const float scaled = f40 * 16777216.0f;
        if (static_cast<s32>(f32_bits_15b8f8(scaled)) >= 0x4B800000) {
            val24 = 0x00FFFFFFu;
        } else {
            val24 = static_cast<u32>(scaled);
        }
    }
    desc[13] |= (val24 & 0x00FFFFFEu);
}

// DECOMP_FUNC(0x002626fc, 684)
extern "C" const u8* camp_func_00311d20(u32 id1, u32 id2);
extern "C" u32 camp_func_0029ed44(void* self, u32 id);
extern "C" u32 camp_func_003c8fdc(void* self, u32 id1, u32 id2, u32 res_id);
extern "C" const u8* camp_func_002b9364(u32 id);
extern "C" const u8* camp_func_0029ec14(u32 id);
extern "C" void func_002b7f0a(void* base, s32 count, s32 size, u32 comparator);
extern "C" u32 camp_func_003c997c(void* self, u32 id1, u32 id2, u32 res_id);

extern "C" u32 camp_func_002626fc(u8* self, u32 id1, u32 id2, u32* out) {
    const u8* const pair = (id1 < id2) ? camp_func_00311d20(id1, id2) : camp_func_00311d20(id2, id1);
    if (pair == nullptr) {
        return 0u;
    }

    const u16 res_id = static_cast<u16>(*reinterpret_cast<const u32*>(pair + 4));
    if (res_id == 0u) {
        return 0u;
    }
    if (camp_func_0029ed44(self, res_id) == 0u) {
        return 0u;
    }
    if (camp_func_003c8fdc(self, id1, id2, *reinterpret_cast<const u32*>(pair + 4) & 0xFFFFu) == 0u) {
        return 0u;
    }

    u32 w0 = ((out[0] >> 15) << 15) | (id1 & ~0x8000u);
    w0 = (w0 & ~0x3FFF8000u) | ((id2 << 15) & 0x3FFF8000u);
    out[0] = w0;

    u32 w1 = (out[1] & 3u) | ((*reinterpret_cast<const u32*>(pair + 4) << 2) & 0x0001FFFFu);
    w1 = (w1 << 15) >> 15;
    out[1] = w1;

    const u8* const info = camp_func_002b9364(static_cast<u16>(*reinterpret_cast<const u32*>(pair + 4)));
    u16* const slots = reinterpret_cast<u16*>(self + 0x146);
    u32* const count_ptr = reinterpret_cast<u32*>(self + 0x178);

    for (s32 i = 0; i < 8; ++i) {
        const u16 sk = *reinterpret_cast<const u16*>(info + 0x3C + i * 2);
        if (sk != 0u) {
            slots[*count_ptr] = sk;
            *count_ptr += 1u;
        }
    }

    if (static_cast<s32>(*count_ptr) < 0x18) {
        slots[*count_ptr] = 0u;
    }

    for (s32 i = 0; i < 0x18; ++i) {
        if (slots[i] != 0u) {
            const u8* const sinfo = camp_func_0029ec14(slots[i]);
            if ((sinfo[3] & 0x20u) == 0u) {
                slots[i] = 0u;
            }
        }
    }

    func_002b7f0a(slots, static_cast<s32>(*count_ptr), 2, 0x002C6E7Cu);

    const s32 prev_count = static_cast<s32>(*count_ptr);
    *count_ptr = 0u;
    for (s32 i = 0; i < prev_count; ++i) {
        if (slots[i] == 0u) {
            break;
        }
        *count_ptr += 1u;
    }

    if (self[0x17D] != 0u) {
        u32 cost = info[3] * 20u;
        cost += *reinterpret_cast<const u16*>(info + 0x1A);
        cost += *reinterpret_cast<const u16*>(info + 0x1C);
        cost += *reinterpret_cast<const u16*>(info + 0x1E);
        cost += *reinterpret_cast<const u16*>(info + 0x20);
        cost += *reinterpret_cast<const u16*>(info + 0x22);
        for (s32 i = 0; i < 0x18; ++i) {
            if (slots[i] != 0u) {
                const u8* const sinfo = camp_func_0029ec14(slots[i]);
                cost += (sinfo[3] & 0x1Fu) * 5u;
            }
        }
        out[1] = (out[1] & 0x0001FFFFu) | (cost << 17);
    }

    return camp_func_003c997c(self, id1, id2, (out[1] & 0x0001FFFFu) >> 2);
}

// DECOMP_FUNC(0x0033ceb8, 684)
extern "C" void ui_func_002c1d3c(void* obj, u32 flag);
extern "C" void ui_func_002b7978(const float* a, const float* b, const float* c, const float* d,
                                 float s0, float s1, float s2, float s3, float s4);
extern "C" void ui_func_002bc2c4();
extern "C" void ui_func_002bf710(float alpha);
extern "C" float ui_func_0024807c(float s0, float s1, float s2, float s3);
extern "C" void ui_func_0033c960(void* self, s32 a1, float x, float y, float alpha);

extern "C" void ui_func_0033ceb8(u8* self) {
    if (*reinterpret_cast<const s32*>(self + 0x390) == 4) {
        return;
    }

    const float f394 = *reinterpret_cast<const float*>(self + 0x394);
    const float f398 = *reinterpret_cast<const float*>(self + 0x398);
    const float s17 = 1.0f - f394 * 0.25f;
    float rect[4] = {0.0f, 0.0f, 0.0f, (f398 * 0.25f) * s17 * 0.5f};

    ui_func_002c1d3c(*reinterpret_cast<void* const*>(0x0044EA00u), 0u);
    ui_func_002b7978(rect, rect, rect, rect, 0.0f, 0.0f, 400.0f, 240.0f, 0.87109375f);
    ui_func_002bc2c4();
    ui_func_002bf710(s17);

    const float f39c = *reinterpret_cast<const float*>(self + 0x39C);
    const float y_off = (4.0f - f39c) * 20.0f;
    const u32 y_pos = static_cast<u32>(static_cast<s32>(0.0f + y_off));
    ui_func_002bf460(2u, 0x14u, 0x54u, 0u, y_pos, 0x23u);
    ui_func_002bf460(2u, 0x14u, 0x55u, 0u, y_pos, 0x23u);

    const float f3a0 = *reinterpret_cast<const float*>(self + 0x3A0);
    const float x_off = ui_func_0024807c(30.0f, 0.0f, 8.0f, f3a0);
    const float item_alpha = (f3a0 * 0.125f) * s17;

    const s32 count = *reinterpret_cast<const s32*>(self + 0x2F4);
    for (s32 i = 0; i < count; ++i) {
        const u8* const item = self + i * 0x54;
        if (item[0x40] == 0u) {
            const s32 idx = *reinterpret_cast<const s32*>(item + 0x48);
            const float* const pt = reinterpret_cast<const float*>(self + 0x368 + idx * 8);
            ui_func_0033c960(self, 0x24, pt[0], pt[1] + y_off, s17);
        } else {
            const s32 n_2f8 = *reinterpret_cast<const s32*>(self + 0x2F8);
            const s32 n_2fc = *reinterpret_cast<const s32*>(self + 0x2FC);
            const s32 mode44 = *reinterpret_cast<const s32*>(item + 0x44);
            const s32 idx48 = *reinterpret_cast<const s32*>(item + 0x48);
            float x;
            float y;
            if (n_2f8 != 0 && n_2fc != 0) {
                if (mode44 == 1) {
                    x = static_cast<float>(idx48) * 76.0f + (400.0f - static_cast<float>(n_2f8) * 76.0f) * 0.5f + x_off;
                    y = *reinterpret_cast<const float*>(self + 0x388);
                } else {
                    x = static_cast<float>(idx48) * 76.0f + (400.0f - static_cast<float>(n_2fc) * 76.0f) * 0.5f + x_off;
                    y = *reinterpret_cast<const float*>(self + 0x38C);
                }
            } else {
                const s32 denom = (mode44 == 1) ? n_2f8 : n_2fc;
                const float y0 = *reinterpret_cast<const float*>(self + 0x388);
                const float y1 = *reinterpret_cast<const float*>(self + 0x38C);
                x = static_cast<float>(idx48) * 76.0f + (400.0f - static_cast<float>(denom) * 76.0f) * 0.5f + x_off;
                y = (y1 + y0) * 0.5f;
            }
            ui_func_0033c960(self, 0x24, x, y, item_alpha);
        }
    }
}

// DECOMP_FUNC(0x002bdeb8, 692)
extern "C" void func_002be4dc(u32 color);
extern "C" s32 ui_func_002c615c(s32 a, s32 b);
extern "C" const s16* camp_func_002bf6d0(u32 a, u32 b);
extern "C" void script_vm_func_002bef14();

extern "C" void ui_func_002bdeb8(s32 val, s32 x, s32 y, u32 show_sign) {
    const s16* layout = nullptr;
    s32 u_val = val;
    s32 first_pos = -1;

    if (show_sign != 0u) {
        if (val > 0) {
            func_002be4dc(0x008400FFu);
        } else if (val == 0) {
            func_002be4dc(0x787878FFu);
        } else {
            func_002be4dc(0xDC0F14FFu);
            u_val = -val;
            func_002be4dc(0xFF0000FFu);
        }
    } else {
        func_002be4dc(0xFFu);
        if (val < 0) {
            u_val = -val;
            func_002be4dc(0xFF0000FFu);
        }
    }

    auto draw_glyph = [&](u32 glyph) {
        ui_func_002bf460(2u, 0xDu, glyph,
                         static_cast<u32>(layout[4] + x),
                         static_cast<u32>(layout[5] + y),
                         0x10u);
    };

    if (u_val == 0) {
        layout = camp_func_002bf6d0(0xEu, 0x5Cu);
        draw_glyph(0u);
    } else {
        const s32 abs_val = (val < 0) ? -val : val;
        s32 div = 100000000;
        for (s32 pos = 0; div > 0; ++pos, div /= 10) {
            if (abs_val >= div) {
                if (first_pos < 0) {
                    first_pos = pos;
                }
                const s32 digit = ui_func_002c615c(u_val, div);
                layout = camp_func_002bf6d0(0xEu, static_cast<u32>(0x64 - pos));
                draw_glyph(static_cast<u32>(digit));
                u_val -= div * digit;
                if (pos == 2) {
                    layout = camp_func_002bf6d0(0xEu, 0x67u);
                    draw_glyph(0xCu);
                } else if (pos == 5) {
                    layout = camp_func_002bf6d0(0xEu, 0x66u);
                    draw_glyph(0xCu);
                }
            }
        }
    }

    if (show_sign != 0u) {
        if (first_pos >= 0) {
            layout = camp_func_002bf6d0(0xEu, static_cast<u32>(0x65 - first_pos));
        }
        if (val < 0) {
            draw_glyph(0xBu);
        } else if (val > 0) {
            draw_glyph(0xAu);
        }
    }

    script_vm_func_002bef14();
}

// DECOMP_FUNC(0x001e4190, 700)
extern "C" void script_vm_func_002aeb2c(u32 a0, u32 a1);
extern "C" void engine_func_002c5ab8(u32 a0, u32 a1);
extern "C" u32 script_vm_func_002c1de4(u32 a0, u32 a1);
extern "C" void ui_func_001a94fc(u32 a0, float s0, float s1, float s2, float s3, float s4, float s5);
extern "C" void func_001e38f8(u32 a0, u32 a1, u32 a2, u32 a3, float s0, float s1,
                              u32 s2, u32 s3, u32 s4, u32 s5, u32 s6,
                              u32 s7, u32 s8, s32 s9, s32 s10);
extern "C" void func_0025b98c();

static inline u32 f32_bits_1e4190(float v) {
    u32 u;
    __builtin_memcpy(&u, &v, sizeof(u));
    return u;
}

extern "C" void script_vm_func_001e4190(u32 a0, s32 a1) {
    const s32 r2 = (a1 == 0) ? 0 : ((a1 > 1) ? a1 : 0xF);
    u32* const g7 = reinterpret_cast<u32*>(0x00448C58u);
    u8* const g6 = reinterpret_cast<u8*>(0x0049F91Cu);

    g7[0x2C / 4] = a0;
    if (g6[0x228] != 0u) {
        g7[0x2C / 4] = 0u;
    }

    const u32 idx = g7[0x2C / 4];
    *reinterpret_cast<u32*>(g6 + 0x390) = idx;
    const u8* const entry = *reinterpret_cast<const u8* const*>(0x00448C58u) + idx * 0x30u;

    const s32 e0 = *reinterpret_cast<const s16*>(entry + 0);
    const s32 e2 = *reinterpret_cast<const s16*>(entry + 2);
    const s32 e4 = *reinterpret_cast<const s16*>(entry + 4);
    const s32 e6 = *reinterpret_cast<const s16*>(entry + 6);

    *reinterpret_cast<s32*>(g6 + 0x398) = e0;
    *reinterpret_cast<s32*>(g6 + 0x39C) = e2;
    *reinterpret_cast<s32*>(g6 + 0x3A0) = e4;
    *reinterpret_cast<s32*>(g6 + 0x3A4) = e6;

    if (r2 == 0) {
        *reinterpret_cast<float*>(g7 + 0x20 / 4) = 1.0f;
        g7[0x1C / 4] = static_cast<u32>(e0);
        *reinterpret_cast<float*>(g7 + 0x24 / 4) = 1.0f;
        g7[0x18 / 4] = static_cast<u32>(e0);
    } else {
        *reinterpret_cast<float*>(g7 + 0x20 / 4) = 0.0f;
        g7[0x1C / 4] = g7[0x18 / 4];
        *reinterpret_cast<float*>(g7 + 0x24 / 4) = static_cast<float>(r2);
        g7[0x18 / 4] = static_cast<u32>(e0);
    }

    s32* const table = reinterpret_cast<s32*>(g7[1]);
    table[e0 * 73] = e6;

    if (g7[0x30 / 4] != 0u) {
        script_vm_func_002aeb2c(0x38u, g7[0x34 / 4]);
        g7[0x30 / 4] = 0u;
    }

    g7[0x34 / 4] = (e0 > 0x31) ? 0u : static_cast<u32>(e0);
    engine_func_002c5ab8(0x38u, g7[0x34 / 4]);
    g7[0x30 / 4] = script_vm_func_002c1de4(0x38u, g7[0x34 / 4]);

    g7[0x0C / 4] = static_cast<u32>(e2);
    *reinterpret_cast<float*>(g7 + 0x10 / 4) = 0.0f;
    g7[0x14 / 4] = 0u;
    g7[0x3C / 4] = static_cast<u32>(e6);
    g7[0x28 / 4] = static_cast<u32>(e4);

    const float inv255 = 1.0f / 255.0f;
    ui_func_001a94fc(
        entry[8],
        static_cast<float>(entry[9]) * inv255,
        static_cast<float>(entry[10]) * inv255,
        static_cast<float>(entry[11]) * inv255,
        static_cast<float>(*reinterpret_cast<const s16*>(entry + 0xC)) * 100.0f,
        static_cast<float>(*reinterpret_cast<const s16*>(entry + 0xE)) * 100.0f,
        *reinterpret_cast<const float*>(entry + 0x10));

    func_001e38f8(
        0u, entry[0x14], entry[0x15], entry[0x16],
        static_cast<float>(*reinterpret_cast<const s16*>(entry + 0x1A)),
        *reinterpret_cast<const float*>(entry + 0x1C),
        entry[0x17], entry[0x18], entry[0x19], entry[0x20], entry[0x21],
        entry[0x22], entry[0x23],
        *reinterpret_cast<const s16*>(entry + 0x24),
        *reinterpret_cast<const s16*>(entry + 0x26));

    *reinterpret_cast<u32*>(g6 + 0x3A8) = entry[0x28];
    const s32 s2a = static_cast<s8>(entry[0x2A]);
    *reinterpret_cast<s32*>(g6 + 0x3AC) = s2a;
    *reinterpret_cast<s32*>(g6 + 0x3B0) = (s2a * 3) / 5;
    *reinterpret_cast<u32*>(g6 + 0x3B4) = entry[0x2B];
    *reinterpret_cast<u32*>(g6 + 0x3B8) = entry[0x2C];
    *reinterpret_cast<u32*>(g6 + 0x3BC) = entry[0x29];
    *reinterpret_cast<u32*>(g6 + 0x3C0) = entry[0x2D];
    *reinterpret_cast<u32*>(g6 + 0x3C4) = entry[0x2E];
    *reinterpret_cast<u32*>(g6 + 0x3C8) = entry[0x2F];

    float ang = static_cast<float>(*reinterpret_cast<const s16*>(entry + 0x1A)) + 180.0f;
    float* const g_f8fc = reinterpret_cast<float*>(0x0049F8F8u + 4u);
    *g_f8fc = ang;
    if (static_cast<s32>(f32_bits_1e4190(ang)) > 0x43B40000) {
        ang -= 360.0f;
        *g_f8fc = ang;
    }

    g7[0x38 / 4] = 0u;
    func_0025b98c();
}

// DECOMP_FUNC(0x003661c0, 708)
extern "C" void battle_func_003e3afc(u32 a0, u8* fbc, float* scale, u8* f4c, const void* sp0, const void* sp4);
extern "C" void func_0023d368(u8* f8c, u8* fbc, u8* f7c);
extern "C" u32 engine_func_002acbd8();
extern "C" void battle_func_002c00b4(u8* mtx, u32 val);

static inline u32 f32_bits_3661c0(float v) {
    u32 u;
    __builtin_memcpy(&u, &v, sizeof(u));
    return u;
}

extern "C" void engine_func_003661c0(u8* self, u32 a1, u32 a2) {
    u32* const f88 = reinterpret_cast<u32*>(self + 0x88);
    u32* const f38 = reinterpret_cast<u32*>(self + 0x38);

    if ((*f88 & 1u) == 0u) {
        *f38 &= ~2u;
    } else if ((*f38 & 2u) != 0u) {
        u8* const obj = *reinterpret_cast<u8* const*>(self + 0x0C);
        const void* sp0 = nullptr;
        const void* sp4 = nullptr;

        if (obj != nullptr) {
            using Fn18 = const void* (*)(u8*);
            using Fn1C = const void* (*)(u8*);
            sp0 = (*reinterpret_cast<Fn18* const*>(obj))[0x18 / 4](obj);
            sp4 = (*reinterpret_cast<Fn1C* const*>(obj))[0x1C / 4](obj);
        } else {
            u32* const guard = reinterpret_cast<u32*>(0x00476640u);
            u8* const def_mtx = reinterpret_cast<u8*>(0x004EFDF4u);
            for (s32 pass = 0; pass < 2; ++pass) {
                if ((*guard & 1u) == 0u && engine_func_002c00d4(guard) != 0u) {
                    battle_func_002c00b4(def_mtx, engine_func_002acbd8());
                    *reinterpret_cast<float*>(def_mtx + 0x30) = 1.0f;
                    *reinterpret_cast<float*>(def_mtx + 0x34) = 1.0f;
                    *reinterpret_cast<float*>(def_mtx + 0x38) = 1.0f;
                    *reinterpret_cast<u32*>(def_mtx + 0x3C) = 0x7E1u;
                }
            }
            sp0 = def_mtx;
            sp4 = def_mtx;
        }

        u8* const fbc = self + 0xBC;
        u8* const f4c = self + 0x4C;
        u8* const f8c = self + 0x8C;
        float scale[3];
        battle_func_003e3afc(a1, fbc, scale, f4c, sp0, sp4);

        const float len2 = scale[0] * scale[0] + scale[1] * scale[1] + scale[2] * scale[2];
        if (static_cast<s32>(f32_bits_3661c0(len2)) < 0x358637BE) {
            float eps;
            const u32 eps_bits = 0x358637BEu;
            __builtin_memcpy(&eps, &eps_bits, sizeof(eps));
            scale[0] = (scale[0] < 0.0f) ? -eps : eps;
            scale[1] = (scale[1] < 0.0f) ? -eps : eps;
            scale[2] = (scale[2] < 0.0f) ? -eps : eps;
        }

        *reinterpret_cast<float*>(fbc + 0x30) = scale[0];
        *reinterpret_cast<float*>(fbc + 0x34) = scale[1];
        *reinterpret_cast<float*>(fbc + 0x38) = scale[2];
        func_0023d368(f8c, fbc, f4c + 0x30);

        u32* const f3c = reinterpret_cast<u32*>(fbc + 0x3C);
        *f3c &= ~0x7E0u;
        if ((*f3c & 8u) == 0u) {
            *f3c &= ~0x600u;
            const float sx = *reinterpret_cast<const float*>(fbc + 0x30);
            const float sy = *reinterpret_cast<const float*>(fbc + 0x34);
            const float sz = *reinterpret_cast<const float*>(fbc + 0x38);
            if (sx == sy && sx == sz) {
                *f3c |= 0x400u;
                if (f32_bits_3661c0(sx) == 0x3F800000u) {
                    *f3c |= 0x200u;
                }
            }
        }

        self[0x12C] = 0u;
    }

    using Fn28 = void (*)(u8*);
    (*reinterpret_cast<Fn28* const*>(self))[0x28 / 4](self);

    *f88 &= ~0x800u;
    u8* const list = *reinterpret_cast<u8* const*>(self + 0x130);
    u8** it = *reinterpret_cast<u8***>(list + 8);
    u8** const end = *reinterpret_cast<u8***>(list + 0xC);
    for (; it != end; ++it) {
        u8* const child = *it;
        using FnChild = void (*)(u8*, u8*, u32);
        (*reinterpret_cast<FnChild* const*>(child))[0](child, self, a2);
    }
}

// DECOMP_FUNC(0x0013a62c, 712)
extern "C" void engine_func_002c5ff4(u32 a0, u8* a1, u32 size);
extern "C" void func_00139b64(u32 a0, const u16* a1, u32 size);
extern "C" void func_0014672c(u32 a0);
extern "C" void engine_func_002c3aa8(void* a0);
extern "C" s32 engine_func_002c42fc(u32* out_idx, u32* handles, s32 count, u32 wait_all, s64 timeout);
extern "C" void engine_func_002c5468(s32 err);
extern "C" void engine_func_002c3a24(void* a0);
extern "C" void func_00146758(u32 a0, void* dst, u32 size, u32* out_len);
extern "C" void func_001467ac(u32 id, void* dst);

extern "C" void engine_func_0013a62c(u8* self, s32 a1) {
    if (self[0x1318] != 0u) {
        return;
    }

    u16 sp30[2] = {0u, 0u};
    if (a1 == 0) {
        sp30[0] = 0u;
    } else {
        sp30[0] = 2u;
        engine_func_002c5ff4(*reinterpret_cast<const u32*>(self + 0x10A8), self + 0x18, 0x1080u);
        asm volatile("mcr p15, 0, %0, c7, c10, 4" : : "r"(0u) : "memory");
    }
    func_00139b64(2u, sp30, 4u);

    func_0014672c(0x4000u);
    engine_func_002c3aa8(self + 8);

    u32 sp_a4 = 0u;
    u32 sp_9c = *reinterpret_cast<const u32*>(self + 0);
    const s32 sync_res = engine_func_002c42fc(&sp_a4, &sp_9c, 1, 0u, -1);
    if (sync_res < 0) {
        engine_func_002c5468(sync_res);
    }

    s32 svc19_r0 = *reinterpret_cast<const s32*>(self + 0);
    asm volatile("svc 0x19" : "+r"(svc19_r0) : : "r1", "r2", "r3", "memory");
    if (svc19_r0 < 0) {
        engine_func_002c5468(svc19_r0);
    }

    self[0x1319] = static_cast<u8>(self[0x1319] + 1u);
    engine_func_002c3a24(self + 8);

    u16 sp28 = 0u;
    u32 sp_a0 = 0u;
    func_00146758(2u, &sp28, 2u, &sp_a0);

    u16 sp70[16];
    func_00146758(2u, sp70, (static_cast<u32>(sp28) << 1) & 0xFFFFu, &sp_a0);

    u32 sp10[2] = {0u, 0u};
    u32 sp18[2] = {0u, 0u};
    u32 sp20[2] = {0u, 0u};
    u32 sp90[2] = {0u, 0u};

    void* ptrs[15] = {
        self + 0x1098,
        sp90,
        sp18,
        sp20,
        self + 0x10A0,
        self + 0x10A8,
        self + 0x1300,
        sp10,
        self + 0x1308,
        self + 0x1310,
        self + 0x1584,
        self + 0x158C,
        self + 0x1594,
        self + 0x159C,
        self + 0x15A4,
    };

    for (s32 i = 0; i < static_cast<s32>(sp28); ++i) {
        func_001467ac(sp70[i], ptrs[i]);
        func_001467ac(static_cast<u32>(sp70[i]) | 0x10000u, static_cast<u8*>(ptrs[i]) + 4);
    }

    *reinterpret_cast<u32*>(self + 0x12F0) = sp10[0];
    *reinterpret_cast<u32*>(self + 0x12F4) = sp10[0] + 0xA00u;
    *reinterpret_cast<u32*>(self + 0x12F8) = sp10[1];
    *reinterpret_cast<u32*>(self + 0x12FC) = sp10[1] + 0xA00u;

    for (s32 i = 0; i < 0x18; ++i) {
        u8* const base = self + i * 4 + 0x1000;
        *reinterpret_cast<u32*>(base + 0x0B0) = sp90[0] + static_cast<u32>(i) * 0xC0u;
        *reinterpret_cast<u32*>(base + 0x170) = sp18[0] + static_cast<u32>(i) * 0x0Cu;
        *reinterpret_cast<u32*>(base + 0x230) = sp20[0] + static_cast<u32>(i) * 0x20u;
        *reinterpret_cast<u32*>(base + 0x110) = sp90[1] + static_cast<u32>(i) * 0xC0u;
        *reinterpret_cast<u32*>(base + 0x1D0) = sp18[1] + static_cast<u32>(i) * 0x0Cu;
        *reinterpret_cast<u32*>(base + 0x290) = sp20[1] + static_cast<u32>(i) * 0x20u;
    }

    func_0014672c(0x4000u);
    self[0x1319] = 0u;
    *reinterpret_cast<u16*>(self + 0x131A) = 4u;
    **reinterpret_cast<u16**>(self + 0x1098) = 4u;
    *reinterpret_cast<u16*>(self + 0x131A) = static_cast<u16>(*reinterpret_cast<const u16*>(self + 0x131A) + 1u);

    s32 svc18_r0 = *reinterpret_cast<const s32*>(self + 4);
    asm volatile("svc 0x18" : "+r"(svc18_r0) : : "r1", "r2", "r3", "memory");
    if (svc18_r0 < 0) {
        engine_func_002c5468(svc18_r0);
    }

    const u16 parity = *reinterpret_cast<const u16*>(self + 0x131A) & 1u;
    *reinterpret_cast<u16*>(self + 0x131E) = parity;
    *reinterpret_cast<u16*>(self + 0x131C) = parity;
    self[0x1318] = 1u;
}

// DECOMP_FUNC(0x00240158, 712)
extern "C" void ui_func_002bcf58(void* dst, const void* src, u32 size);
extern "C" void func_0033a250(void* ctx);
extern "C" void func_0033a06c(void* ctx);

extern "C" void script_vm_func_00240158(u32* self, u8* ctx) {
    const u8* const hdr = reinterpret_cast<const u8*>(self[1]);
    if (hdr == nullptr) {
        return;
    }

    u32* const f44a0 = reinterpret_cast<u32*>(ctx + 0x44A0);
    if ((*f44a0 & 0x200u) == 0u && hdr[0xA] == 1u) {
        const s32 ver = static_cast<s8>(hdr[4]) * 1000 +
                        static_cast<s8>(hdr[5]) * 100 +
                        static_cast<s8>(hdr[6]) * 10 +
                        static_cast<s8>(hdr[7]) - 0xD050;
        const u16 off8 = *reinterpret_cast<const u16*>(hdr + 8);
        const u32 total_sz = *reinterpret_cast<const u32*>(hdr + 0xC);
        const u8* src_ptr = hdr + off8;

        float* const f1ea4 = reinterpret_cast<float*>(ctx + 0x1EA4);
        for (s32 i = 0; i < 6; ++i) {
            f1ea4[i] = 0.0f;
        }
        *reinterpret_cast<u32*>(ctx + 0x1EBC) = 0u;

        if (ver == 0x44C) {
            ui_func_002bcf58(ctx + 0x1EA4, src_ptr, 0x118u);
            src_ptr += 0x118;
        }

        const u32 rem = total_sz - 0x118u;
        const u32 max_slots = static_cast<u32>((static_cast<u64>(rem) * 0xAAAAAAABull) >> 36);
        const s32 cap = static_cast<s32>(ctx[0x1E9D]);
        const u32 n = (cap < static_cast<s32>(max_slots)) ? static_cast<u32>(cap) : max_slots;
        ui_func_002bcf58(*reinterpret_cast<void* const*>(ctx + 0x1FBC), src_ptr, n * 0x18u);
    }

    func_0033a250(ctx);
    func_0033a06c(ctx);
    func_003d7228(*reinterpret_cast<void* const*>(0x004342C8u));

    if (ctx[0x44B7] == 0u &&
        ((*reinterpret_cast<const u32*>(ctx + 0xE0) & 0x02000000u) != 0u || (*f44a0 & 2u) != 0u)) {
        for (s32 i = 4; i < 0x36; ++i) {
            u8* const e = (*reinterpret_cast<u8* const*>(ctx + 0x1E98)) + i * 0x114u;
            const u32 w50 = *reinterpret_cast<const u32*>(e + 0x50);
            if ((w50 & 1u) != 0u && (w50 & 2u) != 0u) {
                const u32 w54 = *reinterpret_cast<const u32*>(e + 0x54);
                if ((w54 & 8u) != 0u) {
                    *reinterpret_cast<u32*>(e + 0x54) = w54 & ~8u;
                    if ((*reinterpret_cast<const u16*>(e + 0x58) & 0x800u) == 0u) {
                        const u8* const unit = ui_func_0027dca0(ctx, *reinterpret_cast<const s16*>(e + 0x62));
                        if (func_002406f8(ctx, *reinterpret_cast<const u16*>(unit + 2)) == 0u) {
                            *reinterpret_cast<u16*>(e + 0x58) |= 0x800u;
                        }
                    }
                }
            }
        }
        battle_func_00250800(0u, 0u, 0x0100017Bu, 0u, 0u, 0u, 0u);
    }

    self[0] = 0xDu;
    if ((*f44a0 & 0x40000000u) == 0u) {
        script_vm_func_00270298(2u);
        *f44a0 |= 0x40000000u;
    }
    if (script_vm_func_002c2bd0(0u) == 3u) {
        script_vm_func_002c2ba4(0u, 0xAu, 0xFFu);
    }
    if (script_vm_func_002c2bd0(1u) == 3u) {
        script_vm_func_002c2ba4(1u, 0xAu, 0xFFu);
    }
    if (script_vm_func_00289924() != 0u) {
        self[0] = 0xEu;
        self[3] = 0u;
        battle_func_0023fd38(self, ctx);
    }
}

// DECOMP_FUNC(0x00348188, 712)
extern "C" void func_0023e55c(float* dst, const float* src, const float* scale);

static inline u32 f32_bits_348188(float v) {
    u32 u;
    __builtin_memcpy(&u, &v, sizeof(u));
    return u;
}

static inline void sincos_lut_348188(float deg_scaled, float& out_s, float& out_c) {
    const s32 neg = (deg_scaled < 0.0f) ? 1 : 0;
    float a = (deg_scaled < 0.0f) ? -deg_scaled : deg_scaled;
    while (static_cast<s32>(f32_bits_348188(a)) >= 0x47800000) {
        a -= 65536.0f;
    }
    const u16 u = static_cast<u16>(static_cast<u32>(a));
    const u32 idx = u & 0xFFu;
    const float frac = a - static_cast<float>(u);
    const float* const entry = reinterpret_cast<const float*>(0x00407FC0u) + idx * 4u;
    float s = entry[0] + frac * entry[2];
    const float c = entry[1] + frac * entry[3];
    if (neg != 0) {
        s = -s;
    }
    out_s = s;
    out_c = c;
}

extern "C" void func_00348188(u8* self) {
    u8* const obj14 = *reinterpret_cast<u8* const*>(self + 0x14);
    using Fn8 = void (*)(u8*);
    (*reinterpret_cast<Fn8* const*>(obj14))[8 / 4](obj14);

    const s32 n = *reinterpret_cast<const s32*>(*reinterpret_cast<const u8* const*>(self + 0x60));
    if (n + 1 > 0) {
        for (s32 i = 0; i < n + 1; ++i) {
            u8* const arr = *reinterpret_cast<u8* const*>(self + 4);
            const u8* const cfg = *reinterpret_cast<const u8* const*>(self + 0x60);
            *reinterpret_cast<float*>(arr + i * 20 + 0x0C) += *reinterpret_cast<const float*>(cfg + 0x30);
            *reinterpret_cast<float*>(arr + i * 20 + 0x10) += *reinterpret_cast<const float*>(cfg + 0x34);
        }
    }

    const u8* const cfg = *reinterpret_cast<const u8* const*>(self + 0x60);
    float ang = *reinterpret_cast<const float*>(self + 0x58) + *reinterpret_cast<const float*>(cfg + 0x38);
    *reinterpret_cast<float*>(self + 0x58) = ang;
    if (static_cast<s32>(f32_bits_348188(ang)) >= 0x43B40000) {
        ang -= 360.0f;
        *reinterpret_cast<float*>(self + 0x58) = ang;
    } else if (ang < 0.0f) {
        ang += 360.0f;
        *reinterpret_cast<float*>(self + 0x58) = ang;
    }

    float sx, cx, sy, cy, sz, cz;
    sincos_lut_348188(0.0f, sx, cx);
    sincos_lut_348188(0.0f, sy, cy);
    sincos_lut_348188(ang * (256.0f / 360.0f), sz, cz);

    float* const m = reinterpret_cast<float*>(self + 0x18);
    m[0] = cz * cy;
    m[1] = (sx * cz) * sy - (cx * sz);
    m[2] = (sx * sz) + (cx * cz) * sy;
    m[3] = 0.0f;
    m[4] = sz * cy;
    m[5] = (cx * cz) + (sx * sz) * sy;
    m[6] = (cx * sz) * sy - (sx * cz);
    m[7] = 0.0f;
    m[8] = -sy;
    m[9] = sx * cy;
    m[10] = cx * cy;
    m[11] = 0.0f;
    m[12] = 0.0f;
    m[13] = 0.0f;
    m[14] = 0.0f;
    m[15] = 1.0f;

    const float sc = *reinterpret_cast<const float*>(self + 0x5C) + *reinterpret_cast<const float*>(cfg + 0x3C);
    *reinterpret_cast<float*>(self + 0x5C) = sc;
    const float v[3] = {sc, sc, 1.0f};
    func_0023e55c(m, m, v);
}

// DECOMP_FUNC(0x00266e88, 724)
static inline u32 f32_bits_266e88(float v) {
    u32 u;
    __builtin_memcpy(&u, &v, sizeof(u));
    return u;
}

static inline float vsqrt_266e88(float x) {
    float r;
    asm("vsqrt.f32 %0, %1" : "=t"(r) : "t"(x));
    return r;
}

static inline float vabs_266e88(float x) {
    float r;
    asm("vabs.f32 %0, %1" : "=t"(r) : "t"(x));
    return r;
}

extern "C" s32 script_vm_func_00266e88(const float* p0, const float* p1, float* out_pos) {
    const u8* const g_sl = reinterpret_cast<const u8*>(0x00446FE8u);
    s32 hit = -1;

    float cur_x = p0[0];
    float cur_y = p0[1];
    float cur_z = p0[2];
    float p1_x = p1[0];
    float p1_y = p1[1];
    float p1_z = p1[2];

    for (s32 pass = 0; pass < 3; ++pass) {
        const u8* arr;
        s32 count;
        float radius;

        if (pass == 0) {
            arr = reinterpret_cast<const u8*>(0x00493C5Cu);
            count = *reinterpret_cast<const s32*>(g_sl + 0x14);
            radius = 28.0f;
            if (hit == -1) {
                const float dx = cur_x - p1_x;
                const float dy = cur_y - p1_y;
                const float dz = cur_z - p1_z;
                const float inv_len = 1.0f / vsqrt_266e88(dx * dx + dy * dy + dz * dz);
                cur_x += (dx * inv_len) * radius;
                cur_y += (dy * inv_len) * radius;
                cur_z += (dz * inv_len) * radius;
            }
        } else if (pass == 1) {
            arr = *reinterpret_cast<const u8* const*>(g_sl + 0x20);
            count = *reinterpret_cast<const s32*>(g_sl + 0x0C);
            radius = 8.0f;
            if (hit == -1) {
                const float a0 = p0[0];
                const float a1 = p0[1];
                const float a2 = p0[2];
                p1_x = p1[0];
                p1_y = p1[1];
                p1_z = p1[2];
                const float dx = a0 - p1_x;
                const float dy = a1 - p1_y;
                const float dz = a2 - p1_z;
                const float inv_len = 1.0f / vsqrt_266e88(dx * dx + dy * dy + dz * dz);
                cur_x = a0 + (dx * inv_len) * radius;
                cur_y = a1 + (dy * inv_len) * radius;
                cur_z = a2 + (dz * inv_len) * radius;
            }
        } else {
            arr = *reinterpret_cast<const u8* const*>(g_sl + 0x24);
            count = *reinterpret_cast<const s32*>(g_sl + 0x10);
            radius = 8.0f;
        }

        for (s32 i = 0; i < count; ++i, arr += 0xA8) {
            if (arr[8] == 0u) {
                continue;
            }
            if (pass == 0 && arr[9] != 3u) {
                continue;
            }

            const float sx = cur_x;
            const float sy = cur_y;
            const float sz = cur_z;

            const float nx = *reinterpret_cast<const float*>(arr + 0x0C);
            const float ny = *reinterpret_cast<const float*>(arr + 0x10);
            const float nz = *reinterpret_cast<const float*>(arr + 0x14);
            const float pd = *reinterpret_cast<const float*>(arr + 0x18);

            const float d0 = sx * nx + sy * ny + sz * nz - pd;
            const float d1 = p1_x * nx + p1_y * ny + p1_z * nz - pd;

            if (!((d0 < 0.0f && d1 >= 0.0f) || (d0 >= 0.0f && d1 < 0.0f))) {
                continue;
            }

            const float ad0 = vabs_266e88(d0);
            const float ad1 = vabs_266e88(d1);
            const float denom = ad0 + ad1;
            const float vx = p1_x - sx;
            const float vy = p1_y - sy;
            const float vz = p1_z - sz;
            const float t = ad0 / denom;

            const float res = func_0024bd60(
                static_cast<s8>(arr[4]),
                static_cast<s8>(arr[5]),
                arr,
                sx + vx * t,
                sy + vy * t,
                sz + vz * t,
                radius);
            if (res < 0.0f) {
                continue;
            }

            const float t2 = (ad0 + res) / denom;
            if (static_cast<s32>(f32_bits_266e88(t2)) < 0x3F800000) {
                cur_x = sx + vx * t2;
                cur_y = sy + vy * t2;
                cur_z = sz + vz * t2;
            } else {
                cur_x = p1_x + vx * (-24.0f);
                cur_y = p1_y + vy * (-24.0f);
                cur_z = p1_z + vz * (-24.0f);
            }
            hit = i;
        }
    }

    if (hit == -1) {
        out_pos[0] = p0[0];
        out_pos[1] = p0[1];
        out_pos[2] = p0[2];
    } else {
        out_pos[0] = cur_x;
        out_pos[1] = cur_y;
        out_pos[2] = cur_z;
    }
    return hit;
}

// DECOMP_FUNC(0x002eef44, 728)
extern "C" s32 engine_func_00296f60(u32 idx);
extern "C" void battle_func_002ad6d8(float* dst, const float* mtx, const float* src);
extern "C" void script_vm_func_0027fe84(u32 mode);
extern "C" void script_vm_func_0027fd08(u32 id);
extern "C" void script_vm_func_00273ab0(u32 flag);

extern "C" u32 engine_func_002eef44() {
    const float p0 = static_cast<float>(engine_func_00296f60(0u));
    const float p1 = static_cast<float>(engine_func_00296f60(1u));
    const float p2 = static_cast<float>(engine_func_00296f60(2u));
    const float p3 = static_cast<float>(engine_func_00296f60(3u));

    float sx, cx, sy, cy, sz, cz;
    sincos_lut_348188(0.0f, sx, cx);
    sincos_lut_348188(p3 * (256.0f / 360.0f), sy, cy);
    sincos_lut_348188(0.0f, sz, cz);

    float m[12];
    m[0] = cz * cy;
    m[1] = (sx * cz) * sy - (cx * sz);
    m[2] = (sx * sz) + (cx * cz) * sy;
    m[3] = 0.0f;
    m[4] = sz * cy;
    m[5] = (cx * cz) + (sx * sz) * sy;
    m[6] = (cx * sz) * sy - (sx * cz);
    m[7] = 0.0f;
    m[8] = -sy;
    m[9] = sx * cy;
    m[10] = cx * cy;
    m[11] = 0.0f;

    float vec[3] = {0.0f, 0.0f, -1.0f};
    battle_func_002ad6d8(vec, m, vec);

    vec[0] = p0 - vec[0] * 500.0f;
    vec[1] = p1 - vec[1] * 500.0f;
    vec[2] = p2 - vec[2] * 500.0f;

    u8* const cam = reinterpret_cast<u8*>(0x0049F91Cu);
    *reinterpret_cast<float*>(cam + 0xC4) = vec[0];
    *reinterpret_cast<float*>(cam + 0xC8) = vec[1];
    *reinterpret_cast<float*>(cam + 0xCC) = vec[2];
    *reinterpret_cast<float*>(cam + 0xD0) = p0;
    *reinterpret_cast<float*>(cam + 0xD4) = p1;
    *reinterpret_cast<float*>(cam + 0xD8) = p2;
    *reinterpret_cast<float*>(cam + 0xDC) = 40.0f;

    u8* const st = *reinterpret_cast<u8* const*>(0x004474F4u);
    if (*reinterpret_cast<const u32*>(st) != 3u) {
        st[0xA4] = 1u;
        script_vm_func_0027fe84(3u);
        script_vm_func_0027fd08(0x1Du);
    }

    script_vm_func_00273ab0(1u);
    return 1u;
}

// DECOMP_FUNC(0x00352d98, 740)
extern "C" s32 func_003538d4(u8* self, u32 a1, u32 a2);
extern "C" u32 func_003538b8(u8* self);
extern "C" u32 func_003538c4(u8* self);
extern "C" void func_0035334c();
extern "C" void func_0023a3a4(const char* s);
extern "C" void func_003532a8(u8 flag);
extern "C" s32 func_0035fad8(u32 a1, u32 a2, const void* fp, u32 a3_4,
                              u32 s0, u32 s1, u32 s2, u32 s3, u32 s4,
                              u32 s5, u32 s6, u32 s7, u32 s8, u32 s9,
                              u32 s10, u32 s11, u32 s12, u32 s13, u32 s14);
extern "C" s32 engine_func_002b45f8(const char* a, const char* b, u32 max_len);
extern "C" u32 script_vm_func_002c607c(const char* s, char** endptr, s32 base);
extern "C" s32 func_0035382c(u8* self, const u32* pair, u16 code);

extern "C" s32 engine_func_00352d98(u8* self, u32 a1, u32 a2, const u8* a3) {
    const s32 r0 = func_003538d4(self, *reinterpret_cast<const u32*>(a3 + 0x10),
                                 *reinterpret_cast<const u32*>(a3 + 0x14));
    if (r0 < 0) {
        return r0;
    }

    const u32 v_38b8 = func_003538b8(self);
    const u32 v_38c4 = func_003538c4(self);
    func_0035334c();
    func_0023a3a4("Prices");
    func_0023a3a4("Ratings");
    func_0023a3a4("NewSince");
    func_0023a3a4("TitleVersion");
    func_0023a3a4("sys.ItemCode");
    func_003532a8(a3[0x28]);

    const void* const fp = (*reinterpret_cast<const u32*>(a3 + 0) != 0u)
        ? reinterpret_cast<const void*>(*reinterpret_cast<const u32*>(a3 + 0))
        : a3;
    const u32 r0_8 = (*reinterpret_cast<const u32*>(a3 + 8) != 0u)
        ? *reinterpret_cast<const u32*>(a3 + 8)
        : reinterpret_cast<u32>(a3);
    const u32 r1_18 = (*reinterpret_cast<const u32*>(a3 + 0x18) != 0u)
        ? *reinterpret_cast<const u32*>(a3 + 0x18)
        : reinterpret_cast<u32>(a3);
    const u32 r8_flag = (*reinterpret_cast<const u32*>(a3 + 0x18) != 0u) ? 1u : 0u;

    const s32 res = func_0035fad8(
        a1, a2, fp, *reinterpret_cast<const u32*>(a3 + 4),
        0x004E655Cu,
        *reinterpret_cast<const u32*>(0x00471A50u),
        r0_8,
        *reinterpret_cast<const u32*>(a3 + 0x0C),
        0x004E675Cu,
        *reinterpret_cast<const u32*>(0x00471A54u),
        v_38b8,
        v_38c4,
        r1_18,
        r8_flag,
        *reinterpret_cast<const u32*>(a3 + 0x2C),
        *reinterpret_cast<const u32*>(a3 + 0x30),
        reinterpret_cast<u32>(self + 4),
        *reinterpret_cast<const u32*>(self + 8),
        *reinterpret_cast<const u32*>(self + 0x0C));
    if (res < 0) {
        return res;
    }

    const u8* const hdr = *reinterpret_cast<const u8* const*>(self + 4);
    if (hdr == nullptr || *reinterpret_cast<const u32*>(hdr + 4) == 0u) {
        return 0;
    }

    for (u32 idx = 0u; ; ++idx) {
        const u8* const cur_hdr = *reinterpret_cast<const u8* const*>(self + 4);
        const u8* const item = (cur_hdr != nullptr && idx <= *reinterpret_cast<const u32*>(cur_hdr + 4))
            ? (*reinterpret_cast<const u8* const*>(cur_hdr) + idx * 0x30u)
            : nullptr;

        const u32 cnt = *reinterpret_cast<const u32*>(item + 0x1C);
        const char* str = nullptr;
        for (u32 k = 0u; k < cnt; ++k) {
            const char* const* const pairs = *reinterpret_cast<const char* const* const*>(item + 0x18);
            if (engine_func_002b45f8(pairs[k * 2u], "TitleVersion", 0x40u) == 0) {
                str = pairs[k * 2u + 1u];
                break;
            }
        }

        const u16 code = static_cast<u16>(script_vm_func_002c607c(str, nullptr, 10));
        const u32 w0 = *reinterpret_cast<const u32*>(item + 0);
        const u32 w4 = *reinterpret_cast<const u32*>(item + 4);

        const u32 p0 = (((w4 << 24) | (w0 >> 8)) << 12) >> 12;
        u32 lo8;
        if ((w4 >> 14) == 0x10u && static_cast<u16>(w4) == 0x8Cu) {
            lo8 = 0u;
        } else if ((w4 >> 14) == 0x10u && static_cast<u16>(w4) == 0xDu) {
            lo8 = 1u;
        } else {
            lo8 = 0xFFu;
        }
        const u32 hi16 = ((w4 >> 14) == 0x10u) ? 0u : ((w4 << 24) & 0xFFFF0000u);
        const u32 p1 = hi16 | ((w0 << 8) & 0xFF00u) | lo8;

        const u32 out_pair[2] = {p0, p1};
        const s32 sret = func_0035382c(self, out_pair, code);
        if (sret < 0) {
            return sret;
        }

        const u8* const next_hdr = *reinterpret_cast<const u8* const*>(self + 4);
        const u32 next_cnt = (next_hdr != nullptr) ? *reinterpret_cast<const u32*>(next_hdr + 4) : 0u;
        if (idx + 1u >= next_cnt) {
            break;
        }
    }

    return 0;
}

// DECOMP_FUNC(0x00396d24, 740)
extern "C" const u8* script_vm_func_0024f734(u32 id);
extern "C" u32 camp_func_00253634(u32 a0, u32 a1);
extern "C" u8* engine_func_00232c00(u8* self, u32 a1, u32 a2);
extern "C" void engine_func_00232b3c(u8* ent, u32 a1);
extern "C" void func_00232b28(u8* ent, const float* pos);
extern "C" void func_00232b14(u8* ent, const float* rot);
extern "C" void func_00232b00(u8* ent, const float* scl);
extern "C" u32 func_001e2860(u32 id);
extern "C" u32 battle_func_001fa3f4(u32 id);
extern "C" u32 script_vm_func_002c0ba8(u32 id);

static inline u32 f32_bits_396d24(float v) {
    u32 u;
    __builtin_memcpy(&u, &v, sizeof(u));
    return u;
}

static inline float vsqrt_396d24(float x) {
    float r;
    asm("vsqrt.f32 %0, %1" : "=t"(r) : "t"(x));
    return r;
}

extern "C" void engine_func_00396d24(u8* self, u32 mode) {
    const s32 total = *reinterpret_cast<const u16*>(self + 0xA0);
    if (total <= 0) {
        return;
    }

    u16 cand_ids[0x200];
    u16 cand_count = 0u;
    for (s32 i = 0; i < total; ++i) {
        const u16 id = *reinterpret_cast<const u16*>(self + 0xA2 + i * 2);
        bool used = false;
        for (s32 j = 0; j < 0x20; ++j) {
            const u8* const slot = *reinterpret_cast<const u8* const*>(self + 0x18 + j * 4);
            if (slot != nullptr && *reinterpret_cast<const u32*>(slot + 0x20) == id) {
                used = true;
                break;
            }
        }
        if (!used) {
            cand_ids[cand_count] = id;
            cand_count = static_cast<u16>(cand_count + 1u);
        }
    }

    if (cand_count == 0u) {
        return;
    }

    u32 chosen_id = 0u;
    if (mode == 0u) {
        chosen_id = cand_ids[engine_func_002c0bcc(static_cast<u16>(cand_count - 1u))];
    } else if (mode == 1u || mode == 2u) {
        const u8* const ref = *reinterpret_cast<const u8* const*>(0x00447E88u);
        const float px = *reinterpret_cast<const float*>(ref + 0x1C);
        const float py = *reinterpret_cast<const float*>(ref + 0x20);
        const float pz = *reinterpret_cast<const float*>(ref + 0x24);

        u16 filt_ids[0x200];
        u16 filt_count = 0u;
        for (s32 i = 0; i < cand_count; ++i) {
            const u8* const pt = script_vm_func_0024f734(cand_ids[i]);
            const float dx = px - static_cast<float>(*reinterpret_cast<const s16*>(pt + 2));
            const float dy = py - static_cast<float>(*reinterpret_cast<const s16*>(pt + 4));
            const float dz = pz - static_cast<float>(*reinterpret_cast<const s16*>(pt + 6));
            const float dist = vsqrt_396d24(dx * dx + dy * dy + dz * dz);
            const u32 bits = f32_bits_396d24(dist);

            bool keep = false;
            if (mode == 1u) {
                keep = static_cast<u32>(bits - 0x44610001u) < 0x00DA7FFFu;
            } else {
                keep = static_cast<u32>(bits + 0xBC69FFFFu) < 0x01E3FFFFu;
            }
            if (keep) {
                filt_ids[filt_count] = cand_ids[i];
                filt_count = static_cast<u16>(filt_count + 1u);
            }
        }
        if (filt_count == 0u) {
            return;
        }
        chosen_id = filt_ids[engine_func_002c0bcc(static_cast<u16>(filt_count - 1u))];
    }

    const u8* const pt = script_vm_func_0024f734(chosen_id);
    const float pos[3] = {
        static_cast<float>(*reinterpret_cast<const s16*>(pt + 2)),
        static_cast<float>(*reinterpret_cast<const s16*>(pt + 4)),
        static_cast<float>(*reinterpret_cast<const s16*>(pt + 6)),
    };
    const float rot[3] = {0.0f, 0.0f, 0.0f};
    const float scl[3] = {50.0f, 50.0f, 50.0f};

    const u32 r6_val = camp_func_00253634(
        *reinterpret_cast<const u32*>(self + 4),
        *reinterpret_cast<const u32*>(self + 8));
    u8* const ent = engine_func_00232c00(self, 0u, 0u);
    if (ent == nullptr) {
        return;
    }

    engine_func_00232b3c(ent, *reinterpret_cast<const u32*>(self + 0x98));
    func_00232b28(ent, pos);
    func_00232b14(ent, rot);
    func_00232b00(ent, scl);

    *reinterpret_cast<u32*>(ent + 0x1C) = r6_val;
    *reinterpret_cast<u32*>(ent + 0x20) = chosen_id;
    *reinterpret_cast<u32*>(ent + 0x60) = func_001e2860(r6_val);
    *reinterpret_cast<u32*>(ent + 0x64) = battle_func_001fa3f4(r6_val);

    if (script_vm_func_002c0ba8(0x529u) != 0u && mode == 1u) {
        using Fn14 = void (*)(u8*);
        (*reinterpret_cast<Fn14* const*>(ent))[0x14 / 4](ent);
    }
}

// DECOMP_FUNC(0x002d4fe0, 744)
extern "C" void engine_func_002c2b1c();
extern "C" s32 func_00256780();
extern "C" void script_vm_func_0027fbc8(float* x, float* y, s32 pad);
extern "C" void script_vm_func_00264368();
extern "C" float ui_func_002820a4(float x, float y);
extern "C" void script_vm_func_0028277c();
extern "C" float script_vm_func_00282600(float rad);
extern "C" void func_002ed03c();

static inline u32 f32_bits_2d4fe0(float v) {
    u32 u;
    __builtin_memcpy(&u, &v, sizeof(u));
    return u;
}

extern "C" void engine_func_002d4fe0(u8* self) {
    engine_func_002c2b1c();
    const u8* const g8 = reinterpret_cast<const u8*>(0x0049FC1Cu);
    if (g8[0x48] != 0u || *(g8 - 0x300 + 0x18) != 0u) {
        *reinterpret_cast<u32*>(self + 0xD94) = 0u;
        return;
    }

    u8* const player = *reinterpret_cast<u8* const*>(0x00447E88u);
    const float init_x = *reinterpret_cast<const float*>(player + 0x1C);
    const float init_y = *reinterpret_cast<const float*>(player + 0x20);
    const float init_z = *reinterpret_cast<const float*>(player + 0x24);
    *reinterpret_cast<float*>(player + 0x28) = init_x;
    *reinterpret_cast<float*>(player + 0x2C) = init_y;
    *reinterpret_cast<float*>(player + 0x30) = init_z;

    const s32 dash = func_00256780();
    float speed_scale = 1.0f;
    const float d_scaled = static_cast<float>(dash) * 0.01f;
    if (static_cast<s32>(f32_bits_2d4fe0(d_scaled)) > 0x40000000) {
        speed_scale = 2.0f;
    } else if (static_cast<s32>(f32_bits_2d4fe0(d_scaled)) > 0x3F800000) {
        speed_scale = d_scaled;
    }

    float stick_x = 0.0f;
    float stick_y = 0.0f;
    script_vm_func_0027fbc8(&stick_x, &stick_y, 0);
    script_vm_func_00264368();
    *reinterpret_cast<u32*>(self + 0xC0) = 0u;

    const u32 bx = f32_bits_2d4fe0(stick_x);
    const u32 by = f32_bits_2d4fe0(stick_y);
    const bool active = (bx >= 0xBF000000u) || (static_cast<s32>(bx) >= 0x3F000000) ||
                        (by >= 0xBF000000u) || (static_cast<s32>(by) >= 0x3F000000);

    if (!active) {
        const float spd = *reinterpret_cast<const float*>(self + 0x3C) * 0.7f;
        *reinterpret_cast<float*>(self + 0x3C) = spd;
        if (static_cast<s32>(f32_bits_2d4fe0(spd)) < 0x3A83126F) {
            *reinterpret_cast<float*>(self + 0x3C) = 0.0f;
        }
    } else {
        const u32 s3c_bits = *reinterpret_cast<const u32*>(self + 0x3C);
        const float base_spd = (static_cast<s32>(s3c_bits) > 0x3F800000)
            ? *reinterpret_cast<const float*>(self + 0x3C)
            : 1.0f;
        float spd = base_spd + base_spd * 0.7f;
        *reinterpret_cast<float*>(self + 0x3C) = spd;
        if (static_cast<s32>(f32_bits_2d4fe0(spd)) > 0x42700000) {
            spd = 60.0f;
        }
        *reinterpret_cast<float*>(self + 0x3C) = spd;

        const float rad = ui_func_002820a4(stick_x, stick_y);
        float yaw = -(rad * 57.3248405f - *reinterpret_cast<const float*>(self + 0x50));
        if (yaw < 0.0f) {
            yaw += 360.0f;
        }
        if (static_cast<s32>(f32_bits_2d4fe0(yaw)) > 0x43B40000) {
            yaw -= 360.0f;
        }
        *reinterpret_cast<float*>(*reinterpret_cast<u8* const*>(0x00447E88u) + 0x50) = yaw;
        *reinterpret_cast<u32*>(self + 0xC0) = 1u;
    }

    const s32 steps = (static_cast<s32>(*reinterpret_cast<const u32*>(self + 0x3C)) > 0x420C0000) ? 2 : 1;
    s32 col_res = 0;
    const auto sin_fn = reinterpret_cast<float (*)(float)>(script_vm_func_0028277c);
    const auto col_fn = reinterpret_cast<s32 (*)(float*, const float*)>(func_002ed03c);

    for (s32 step = 0; step < steps; ++step) {
        u8* const p = *reinterpret_cast<u8* const*>(0x00447E88u);
        const float prev_pos[3] = {
            *reinterpret_cast<const float*>(p + 0x1C),
            *reinterpret_cast<const float*>(p + 0x20),
            *reinterpret_cast<const float*>(p + 0x24),
        };
        *reinterpret_cast<float*>(p + 0x28) = prev_pos[0];
        *reinterpret_cast<float*>(p + 0x2C) = prev_pos[1];
        *reinterpret_cast<float*>(p + 0x30) = prev_pos[2];

        const float step_dist = (*reinterpret_cast<const float*>(self + 0x3C) / static_cast<float>(steps)) * speed_scale;
        const float sx = sin_fn(*reinterpret_cast<const float*>(p + 0x50) * 0.0174532924f);
        u8* const p2 = *reinterpret_cast<u8* const*>(0x00447E88u);
        *reinterpret_cast<float*>(p2 + 0x28) += sx * step_dist;

        const float cz = script_vm_func_00282600(*reinterpret_cast<const float*>(p2 + 0x50) * 0.0174532924f);
        u8* const p3 = *reinterpret_cast<u8* const*>(0x00447E88u);
        *reinterpret_cast<float*>(p3 + 0x30) += cz * step_dist;

        if (*reinterpret_cast<const u8*>(0x0049FC1Cu + 0xCC) == 0u) {
            col_res = col_fn(reinterpret_cast<float*>(p3 + 0x28), prev_pos);
        }

        u8* const p4 = *reinterpret_cast<u8* const*>(0x00447E88u);
        *reinterpret_cast<float*>(p4 + 0x1C) = (*reinterpret_cast<const float*>(p4 + 0x28) - *reinterpret_cast<const float*>(p4 + 0x1C)) +
                                               *reinterpret_cast<const float*>(p4 + 0x1C);
        *reinterpret_cast<float*>(p4 + 0x24) = (*reinterpret_cast<const float*>(p4 + 0x30) - *reinterpret_cast<const float*>(p4 + 0x24)) +
                                               *reinterpret_cast<const float*>(p4 + 0x24);
        if (col_res != 0) {
            break;
        }
    }

    u8* const pf = *reinterpret_cast<u8* const*>(0x00447E88u);
    *reinterpret_cast<u32*>(pf + 0x4C) = *reinterpret_cast<const u32*>(pf + 0x50);
    *reinterpret_cast<u32*>(pf + 0x40) = *reinterpret_cast<const u32*>(pf + 0x1C);
    *reinterpret_cast<u32*>(pf + 0x44) = *reinterpret_cast<const u32*>(pf + 0x20);
    *reinterpret_cast<u32*>(pf + 0x48) = *reinterpret_cast<const u32*>(pf + 0x24);
    *reinterpret_cast<float*>(pf + 0x34) = init_x;
    *reinterpret_cast<float*>(pf + 0x38) = init_y;
    *reinterpret_cast<float*>(pf + 0x3C) = init_z;
}

// 0x001524E8: divide-by-zero hook. The pinned body is a no-op
// (`mov r0, r0; bx lr`), and 0x002AA504 primes r0 = r1 = 0 before calling it.
extern "C" u32 script_vm_func_001524e8(u32 r0, u32 r1);

// Width (0..64) of an unsigned 64-bit value. ARMv6K has a native `clz`, so this
// never emits a libgcc helper call.
static u32 script_vm_002aa504_bit_length(u64 value) {
    if (value == 0) {
        return 0;
    }
    const u32 hi = static_cast<u32>(value >> 32);
    if (hi != 0) {
        return 64u - static_cast<u32>(__builtin_clz(hi));
    }
    return 32u - static_cast<u32>(__builtin_clz(static_cast<u32>(value)));
}

// DECOMP_FUNC(0x002aa504, 752)
//
// Unsigned 64-bit divide with the ARM EABI `__aeabi_uldivmod` register
// contract: the numerator arrives in r0:r1, the divisor in r2:r3, the quotient
// is returned in r0:r1 and the remainder is published in r2:r3.  A zero divisor
// calls 0x001524E8 and leaves quotient 0 with remainder = numerator, matching
// the pinned body.
//
// The original is a shift/subtract divider with a 16-entry reciprocal table
// (0x002AA7B4..0x002AA7F3) and several exponent-range specialisations.  The
// straightforward restoring loop below produces the same quotient/remainder
// for every 64-bit input pair (verified exhaustively over targeted boundaries
// and randomized pairs in tools/test_leaf_002aa504.py).
extern "C" u64 script_vm_func_002aa504(u64 numerator, u64 divisor) {
    u64 quotient = 0;
    u64 remainder = numerator;

    if (divisor == 0) {
        script_vm_func_001524e8(0, 0);
    } else {
        // Align the divisor's leading bit with the numerator's, then subtract
        // it back down one bit at a time; each successful subtraction sets the
        // corresponding quotient bit.  `shifted` never exceeds `numerator`, so
        // the shifted divisor always fits in 64 bits.
        const u32 num_bits = script_vm_002aa504_bit_length(numerator);
        const u32 den_bits = script_vm_002aa504_bit_length(divisor);
        if (num_bits >= den_bits) {
            u32 shift = num_bits - den_bits;
            u64 shifted = divisor << shift;
            for (;;) {
                if (remainder >= shifted) {
                    remainder -= shifted;
                    quotient |= static_cast<u64>(1) << shift;
                }
                if (shift == 0) {
                    break;
                }
                --shift;
                shifted >>= 1;
            }
        }
    }

    // Publish the remainder in r2:r3 to satisfy the EABI caller contract even
    // though the C-level return value is only the quotient.
    register u32 rem_lo __asm__("r2") = static_cast<u32>(remainder);
    register u32 rem_hi __asm__("r3") = static_cast<u32>(remainder >> 32);
    __asm__ volatile("" : "+r"(rem_lo), "+r"(rem_hi));
    return quotient;
}

extern "C" u8* engine_func_0029bddc(const char* path, u32 flag);
extern "C" void engine_func_002a06c8(u8* mod, u32 flag);
extern "C" void engine_func_00341578(u8* self, const char* path);
extern "C" void script_vm_func_002a0790(u32 a0);
extern "C" const u32* engine_func_002a8948(const u8* obj);
extern "C" const char* crt_func_00100c4c(const char* s1, const char* s2);

// DECOMP_FUNC(0x002350f4, 756)
extern "C" void engine_func_002350f4(u8* self, const char* name1, const char* name2) {
    *reinterpret_cast<u32*>(self + 0x1C) = 0u;
    *reinterpret_cast<u32*>(self + 0x18) = 0u;
    *reinterpret_cast<u32*>(self + 0x00) = 0u;
    *reinterpret_cast<u32*>(self + 0x08) = 0u;
    *reinterpret_cast<u32*>(self + 0x04) = 0u;
    *reinterpret_cast<u32*>(self + 0x0C) = 0u;
    self[0x15] = 0u;

    engine_func_002c4b30(self + 0x56C, 0x80u);

    char buf[0x80];
    ui_func_002be7fc(buf, "%s.bam", (name2 != nullptr) ? name2 : name1);
    *reinterpret_cast<u8**>(self + 0x1C) = engine_func_0029bddc(buf, 7u);
    engine_func_002a06c8(*reinterpret_cast<u8**>(self + 0x1C), 1u);

    ui_func_002be7fc(buf, "%s.bccam", name1);
    engine_func_00341578(self, buf);

    ui_func_002be7fc(buf, "%s.bcenv", name1);
    engine_func_002a0c54(buf, 0u);
    script_vm_func_002a0790(0u);

    const u8* const p56c = *reinterpret_cast<const u8* const*>(self + 0x56C);
    u32* const f1634 = reinterpret_cast<u32*>(self + 0x1634);
    f1634[0] = *reinterpret_cast<const u32*>(p56c + 0x58);
    f1634[1] = *reinterpret_cast<const u32*>(p56c + 0x68);
    f1634[2] = *reinterpret_cast<const u32*>(p56c + 0x78);

    const u32* const p_2a8 = engine_func_002a8948(p56c);
    u32* const f1640 = reinterpret_cast<u32*>(self + 0x1640);
    f1640[0] = p_2a8[0];
    f1640[1] = p_2a8[1];
    f1640[2] = p_2a8[2];

    u32* const f1610 = reinterpret_cast<u32*>(self + 0x1610);
    f1610[0] = f1640[0];
    f1610[1] = f1640[1];
    f1610[2] = f1640[2];

    u32* const f1604 = reinterpret_cast<u32*>(self + 0x1604);
    f1604[0] = f1634[0];
    f1604[1] = f1634[1];
    f1604[2] = f1634[2];

    const u8* const m1 = *reinterpret_cast<const u8* const*>(*reinterpret_cast<const u8* const*>(self + 0x1C) + 8);
    const u8* const m2 = *reinterpret_cast<const u8* const*>(m1 + 0x2C);
    const u8* node = *reinterpret_cast<const u8* const*>(m2 + 8);
    if (node != nullptr && (0x40000092u & ~(*reinterpret_cast<const u32*>(node))) != 0u) {
        node = nullptr;
    }

    const u32 off_e0 = *reinterpret_cast<const u32*>(node + 0xE0);
    const u8* const grp = (off_e0 != 0u) ? (node + 0xE0 + off_e0) : nullptr;
    const s32 count = *reinterpret_cast<const s32*>(grp + 0x18);
    for (s32 i = 0; i < count; ++i) {
        const u32 off_1c = *reinterpret_cast<const u32*>(grp + 0x1C);
        const u8* const arr = (off_1c != 0u) ? (grp + 0x1C + off_1c) : nullptr;
        const u8* entry = nullptr;
        if (arr != nullptr) {
            const u8* const base = arr + i * 0x10 + 0x28;
            const u32 off_e = *reinterpret_cast<const u32*>(base);
            if (off_e != 0u) {
                entry = base + off_e;
            }
        }
        const u32 off_name = *reinterpret_cast<const u32*>(entry);
        const char* const ename = (off_name != 0u) ? reinterpret_cast<const char*>(entry + off_name) : nullptr;
        if (crt_func_00100c4c(ename, "Dum_") != nullptr) {
            const u32* const src = reinterpret_cast<const u32*>(entry + 0x38);
            const s32 idx = *reinterpret_cast<const s32*>(self + 0x0C);
            u32* const dst = reinterpret_cast<u32*>(self + 0x1670 + idx * 12);
            dst[0] = src[0];
            dst[1] = src[1];
            dst[2] = src[2];
            *reinterpret_cast<s32*>(self + 0x0C) = idx + 1;
        }
    }

    if (*reinterpret_cast<const s32*>(self + 0x0C) > 0) {
        self[0x15] = 1u;

        ui_func_002be7fc(buf, "mikado/yaji.bam");
        *reinterpret_cast<u8**>(self + 0x24) = engine_func_0029bddc(buf, 7u);
        engine_func_002a06c8(*reinterpret_cast<u8**>(self + 0x24), 1u);

        ui_func_002be7fc(buf, "mikado/point.bam");
        *reinterpret_cast<u8**>(self + 0x20) = engine_func_0029bddc(buf, 7u);
        engine_func_002a06c8(*reinterpret_cast<u8**>(self + 0x20), 1u);

        const u32* const first_pt = reinterpret_cast<const u32*>(self + 0x1670);
        u32* const f1658 = reinterpret_cast<u32*>(self + 0x1658);
        f1658[0] = first_pt[0];
        f1658[1] = first_pt[1];
        f1658[2] = first_pt[2];

        void* const sub20 = *reinterpret_cast<void* const*>(*reinterpret_cast<const u8* const*>(self + 0x20) + 8);
        engine_func_0028c8a8(sub20, 0u, f1658);
    }
}

extern "C" f32 func_003e7430(u8* p, u32 idx);
extern "C" void func_0037fd88(u8* p, u8 b, f32 f);

// DECOMP_FUNC(0x00235ac4, 760)
extern "C" void ui_func_00235ac4(u8* self) {
    if (self[5] == 0u) {
        return;
    }
    u8* node = *reinterpret_cast<u8**>(self + 0xC4);
    if (node == nullptr) {
        return;
    }

    static constexpr f32 kInv127Cubed = 1.0f / (127.0f * 127.0f * 127.0f);
    static constexpr f32 kInv128 = 1.0f / 128.0f;
    static constexpr f32 kInv63 = 1.0f / 63.0f;
    static constexpr f32 kInv127 = 1.0f / 127.0f;

    const s32 v_6e = *reinterpret_cast<const signed short*>(self + 0x6E);
    const s32 v_70 = *reinterpret_cast<const signed short*>(self + 0x70);
    u8 interp0;
    if (v_6e <= v_70) {
        interp0 = self[0x6D];
    } else {
        const s32 d = static_cast<s32>(self[0x6D]) - static_cast<s32>(self[0x6C]);
        interp0 = static_cast<u8>((ui_func_002c615c(d * v_70, v_6e) + static_cast<s32>(self[0x6C])) & 0xFF);
    }

    u8* const p_c0 = *reinterpret_cast<u8**>(self + 0xC0);
    const u32 prod = static_cast<u32>(interp0) * static_cast<u32>(self[0x84]) * static_cast<u32>(p_c0[0x74]);
    const f32 t = static_cast<f32>(prod) * kInv127Cubed;
    const f32 s17 = (*reinterpret_cast<const f32*>(self + 0x08) * *reinterpret_cast<const f32*>(p_c0 + 0x14)) * (t * t);

    const s32 v_80 = *reinterpret_cast<const signed short*>(self + 0x80);
    const s32 v_82 = *reinterpret_cast<const signed short*>(self + 0x82);
    signed char v_s1;
    if (v_82 >= v_80) {
        v_s1 = *reinterpret_cast<const signed char*>(self + 0x7F);
    } else {
        const s32 d = static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x7F)) -
                      static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x7E));
        v_s1 = static_cast<signed char>(ui_func_002c615c(d * v_82, v_80) +
                                        static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x7E)));
    }

    const f32 s19 = *reinterpret_cast<const f32*>(p_c0 + 0x18) * *reinterpret_cast<const f32*>(self + 0x0C);
    const f32 s18 = (static_cast<f32>(v_s1) * kInv128) * static_cast<f32>(self[0x86]);

    const s32 v_74 = *reinterpret_cast<const signed short*>(self + 0x74);
    const s32 v_76 = *reinterpret_cast<const signed short*>(self + 0x76);
    signed char v_s2;
    if (v_76 >= v_74) {
        v_s2 = *reinterpret_cast<const signed char*>(self + 0x73);
    } else {
        const s32 d = static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x73)) -
                      static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x72));
        v_s2 = static_cast<signed char>(ui_func_002c615c(d * v_76, v_74) +
                                        static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x72)));
    }

    f32 s22 = static_cast<f32>(v_s2) * kInv63;
    if (s22 > 1.0f) {
        s22 = 1.0f;
    } else if (s22 < -1.0f) {
        s22 = -1.0f;
    }
    const f32 s16 = (*reinterpret_cast<const f32*>(self + 0x10) + *reinterpret_cast<const f32*>(p_c0 + 0x1C)) +
                    s22 * (*reinterpret_cast<const f32*>(self + 0x18) * *reinterpret_cast<const f32*>(p_c0 + 0x60));

    const s32 v_7a = *reinterpret_cast<const signed short*>(self + 0x7A);
    const s32 v_7c = *reinterpret_cast<const signed short*>(self + 0x7C);
    signed char v_s3;
    if (v_7c >= v_7a) {
        v_s3 = *reinterpret_cast<const signed char*>(self + 0x79);
    } else {
        const s32 d = static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x79)) -
                      static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x78));
        v_s3 = static_cast<signed char>(ui_func_002c615c(d * v_7c, v_7a) +
                                        static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x78)));
    }

    f32 s0_b = static_cast<f32>(v_s3) * kInv63;
    if (s0_b > 2.0f) {
        s0_b = 2.0f;
    } else if (s0_b < 0.0f) {
        s0_b = 0.0f;
    }
    const f32 s20 = s0_b + (*reinterpret_cast<const f32*>(self + 0x14) + *reinterpret_cast<const f32*>(p_c0 + 0x20));
    const f32 s21 = *reinterpret_cast<const f32*>(self + 0x98) + *reinterpret_cast<const f32*>(p_c0 + 0x24);
    const u8 r7 = (p_c0[0x2C] != 0u) ? p_c0[0x2C] : self[0x95];
    const f32 s23 = (p_c0[0x2C] != 0u) ? *reinterpret_cast<const f32*>(p_c0 + 0x28)
                                       : *reinterpret_cast<const f32*>(self + 0x9C);
    const f32 s22_out = ((static_cast<f32>(self[0x92]) * kInv127) - 1.0f) + *reinterpret_cast<const f32*>(p_c0 + 0x30);

    f32 arr[2];
    for (s32 i = 0; i < 2; ++i) {
        arr[i] = func_003e7430(p_c0, static_cast<u32>(i & 0xFF)) + static_cast<f32>(self[0x93 + i]) * kInv127;
    }

    while (node != nullptr) {
        *reinterpret_cast<f32*>(node + 0xCC) = s17;
        *reinterpret_cast<f32*>(node + 0xF0) = s18;
        *reinterpret_cast<f32*>(node + 0xD0) = s19;
        *reinterpret_cast<f32*>(node + 0xD4) = s16;
        *reinterpret_cast<f32*>(node + 0xD8) = s20;
        *reinterpret_cast<f32*>(node + 0xDC) = s21;
        func_0037fd88(node, r7, s23);
        *reinterpret_cast<f32*>(node + 0xE4) = s22_out;
        *reinterpret_cast<f32*>(node + 0xE8) = arr[0];
        *reinterpret_cast<f32*>(node + 0xEC) = arr[1];

        const u32* const src54 = reinterpret_cast<const u32*>(self + 0x54);
        u32* const dst_ac = reinterpret_cast<u32*>(node + 0xAC);
        dst_ac[0] = src54[0];
        dst_ac[1] = src54[1];
        dst_ac[2] = src54[2];
        *reinterpret_cast<u32*>(node + 0xB8) = *reinterpret_cast<const u32*>(self + 0x60);
        node[0xC4] = self[0x64];
        node = *reinterpret_cast<u8**>(node + 0x138);
    }
}

struct AocStatus0038ff58 {
    u32 w[5];
};

extern "C" void engine_func_00234278(void* out);
extern "C" u32 camp_func_0027ec84(const void* s);
extern "C" void battle_func_00233f0c(void* self);
extern "C" void shop_func_00297128();
extern "C" void engine_func_00234004(void* self, u32 a1, u32 a2);
extern "C" void engine_func_00233f4c(void* self, u32 a1);
extern "C" u8* engine_func_00234160(void* p, u32 a1);
extern "C" u32 engine_func_002a17c0(const void* s);
extern "C" u32 ui_func_0026f0d8(u32 a0);
extern "C" u32 shop_func_0029111c();

// DECOMP_FUNC(0x0038ff58, 760)
extern "C" void script_vm_func_0038ff58(u8* self) {
    AocStatus0038ff58 st;
    engine_func_00234278(&st);

    const u8* const g = *reinterpret_cast<const u8* const*>(0x00432FC8u);
    const s32 state = *reinterpret_cast<const s32*>(self + 8);

    switch (state) {
        case 0: {
            *reinterpret_cast<u32*>(self) |= 0x10000u;
            engine_func_00233f4c(self, 3u);
            const u32 h = script_vm_func_00291018(*reinterpret_cast<const u32*>(self + 0x350), "aoc_ExeDelete");
            script_vm_func_002971e4(*reinterpret_cast<const u32*>(self + 0x358), h);
            *reinterpret_cast<u32*>(self + 8) = 1u;
            camp_func_00233ac0(self, -1, 0u);
            break;
        }
        case 1: {
            if (ui_func_0026b7cc() == 0u) {
                break;
            }
            if ((*reinterpret_cast<const u32*>(self) & 0x200u) == 0u) {
                break;
            }
            script_vm_func_0019dfbc(*reinterpret_cast<const u32*>(self + 0x358));
            u8* const obj = engine_func_00234160(self + 0x20C, 3u);
            *reinterpret_cast<u8**>(self + 0x208) = obj;
            const u32 idx = shop_func_002337a0(self + 0x240);
            const u8* const tbl = *reinterpret_cast<const u8* const*>(g + 0x678);
            const u16 val = *reinterpret_cast<const u16*>(tbl + 0x9AAu + idx * 0x139u * 8u);
            *reinterpret_cast<u32*>(obj + 0x14) = val;
            *reinterpret_cast<u32*>(self + 8) = 2u;
            break;
        }
        case 2: {
            script_vm_func_0019dfbc(*reinterpret_cast<const u32*>(self + 0x358));
            void* const obj = *reinterpret_cast<void**>(self + 0x208);
            using QueryFn = AocStatus0038ff58 (*)(void*);
            const QueryFn fn = (*reinterpret_cast<QueryFn* const*>(obj))[3];
            st = fn(obj);
            if (camp_func_0027ec84(&st) != 0u) {
                battle_func_00233f0c(self);
                shop_func_00297128();
                *reinterpret_cast<u32*>(self + 8) = 3u;
            } else if (engine_func_002a17c0(&st) != 0u) {
                battle_func_00233f0c(self);
                shop_func_00297128();
                *reinterpret_cast<u32*>(self + 8) = 9999u;
                *reinterpret_cast<AocStatus0038ff58*>(self + 0x210) = st;
            }
            break;
        }
        case 3: {
            if (script_vm_func_002a0f88() == 0u) {
                break;
            }
            const u32 h = script_vm_func_00291018(*reinterpret_cast<const u32*>(self + 0x350), "aoc_Deleted");
            script_vm_func_002971e4(*reinterpret_cast<const u32*>(self + 0x358), h);
            engine_func_002b8584(0u);
            camp_func_00233ac0(self, 3, 1u);
            *reinterpret_cast<u32*>(self + 8) = 4u;
            break;
        }
        case 4: {
            script_vm_func_0019dfbc(*reinterpret_cast<const u32*>(self + 0x358));
            if (ui_func_0026f0d8(0x10u) == 0u) {
                break;
            }
            camp_func_002bc200(0x0100016Du);
            shop_func_00297128();
            *reinterpret_cast<u32*>(self + 8) = 5u;
            break;
        }
        case 5: {
            if (script_vm_func_002a0f88() == 0u) {
                break;
            }
            if (shop_func_0029111c() == 0u) {
                break;
            }
            void* const obj = *reinterpret_cast<void**>(self + 0x208);
            *reinterpret_cast<u32*>(self + 4) = 10u;
            *reinterpret_cast<u32*>(self + 8) = 0u;
            if (obj != nullptr) {
                using DtorFn = void (*)(void*);
                const DtorFn dtor = (*reinterpret_cast<DtorFn* const*>(obj))[1];
                dtor(obj);
                *reinterpret_cast<void**>(self + 0x208) = nullptr;
            }
            break;
        }
        case 9999: {
            engine_func_00234004(self, 5u, 3u);
            break;
        }
        default:
            break;
    }
}

extern "C" void func_002bf558(u32 a, u32 b, u32 c, u32 d, u32 s0, u32 s1);
extern "C" const char* engine_func_00234920(void* g, u32 id);
extern "C" void engine_func_0023494c(void* g, const char* s, char* out);
extern "C" s32 ui_func_002335c0(const char* s, u32 a1);

// DECOMP_FUNC(0x0038fb3c, 772)
extern "C" u32 ui_func_0038fb3c() {
    u8* const st = ui_func_002c0ac8();
    const u32 timer = *reinterpret_cast<const u32*>(st + 0x1798);
    void* const g_432fc8 = *reinterpret_cast<void* const*>(0x00432FC8u);

    ui_func_002c3ba8(*reinterpret_cast<void* const*>(0x0044EA00u));
    const u32 pushed = ui_func_002c5f7c(1u, 0u);

    u8* const stk = *reinterpret_cast<u8* const*>(0x0044EA00u) + 0x124Cu;
    const u32 idx0 = *reinterpret_cast<const u32*>(stk);
    const u32 prev = *reinterpret_cast<const u32*>(stk + 8u + idx0 * 4u);
    const u32 idx1 = idx0 + 1u;
    *reinterpret_cast<u32*>(stk) = idx1;
    *reinterpret_cast<u32*>(stk + 8u + idx1 * 4u) = pushed;
    if (stk[0x18] != 0u || prev != pushed) {
        using Cb = void (*)(u32);
        (*reinterpret_cast<const Cb*>(stk + 0x1C))(pushed);
        stk[0x18] = 0u;
    }

    func_002bf558(2u, 0x3Au, 5u, 0u, 0u, 0x81u);

    static const u32 kIds[4] = {0x6Eu, 0x6Fu, 0x70u, 0x71u};
    const u32 sel = *reinterpret_cast<const u32*>(st + 0x179Cu);
    const char* const key = engine_func_00234920(g_432fc8, kIds[sel]);
    char buf[0x400];
    engine_func_0023494c(g_432fc8, key, buf);
    const s32 width = ui_func_002335c0(buf, 3u);

    const signed short* const lay = camp_func_002bf6d0(0x3Au, 0x2Du);
    const s32 l_x = lay[4];
    const s32 l_y = lay[5];
    const signed short* const sub_p =
        *reinterpret_cast<const signed short* const*>(reinterpret_cast<const u8*>(lay) + 0x0C);
    const s32 x0 = (l_x + (static_cast<s32>(sub_p[0]) >> 1)) - (width >> 1) - 9;

    ui_func_002be77c(3u, static_cast<s32>(0xF49800FFu), buf,
                     static_cast<float>(x0), static_cast<float>(l_y),
                     0.5f, 0.0f, 1.0f);

    const s32 q = static_cast<s32>(timer / 5u);
    const s32 p0 = q % 8;
    const s32 p0_prev = (p0 + 7) % 8;
    const s32 p1 = (q + 4) % 8;
    const s32 p1_prev = (p1 + 7) % 8;
    const s32 sb = x0 + width;

    for (s32 row = 0; row < 3; ++row) {
        for (s32 col = 0; col < 3; ++col) {
            const s32 cell = row * 3 + col;
            const signed short* const lay31 = camp_func_002bf6d0(0x3Au, 0x31u);
            const s32 base_x = lay31[4];
            const signed short* const lay_i = camp_func_002bf6d0(0x3Au, static_cast<u32>(0x31 + cell));
            const s32 ix = lay_i[4];
            const s32 iy = lay_i[5];
            const u32 px = static_cast<u32>((ix - base_x) + sb + 4);

            if (p0 == cell || p1 == cell) {
                ui_func_002bf460(2u, 0xEu, 0x155u, px, static_cast<u32>(iy), 0x81u);
            } else if (p0_prev == cell || p1_prev == cell) {
                ui_func_002bf460(2u, 0xEu, 0x156u, px, static_cast<u32>(iy), 0x81u);
            } else {
                ui_func_002bf460(2u, 0xEu, 0x154u, px, static_cast<u32>(iy), 0x81u);
            }
        }
    }

    u8* const stk2 = *reinterpret_cast<u8* const*>(0x0044EA00u) + 0x124Cu;
    const u32 cur_idx = *reinterpret_cast<const u32*>(stk2);
    const u32 popped = *reinterpret_cast<const u32*>(stk2 + 8u + cur_idx * 4u);
    const u32 new_idx = cur_idx - 1u;
    *reinterpret_cast<u32*>(stk2) = new_idx;
    const u32 next_val = *reinterpret_cast<const u32*>(stk2 + 8u + new_idx * 4u);
    if (stk2[0x18] != 0u || popped != next_val) {
        using Cb = void (*)(u32);
        (*reinterpret_cast<const Cb*>(stk2 + 0x1C))(next_val);
        stk2[0x18] = 0u;
    }

    return 0u;
}

extern "C" u32 ui_func_002c17d4(u32 a);
extern "C" u32 ui_func_002bffbc(u32 a);
extern "C" u32 script_vm_func_00276550();
extern "C" float script_vm_func_00287d74(const void* vec2);
extern "C" float script_vm_func_0027f150(float a, float b);

// DECOMP_FUNC(0x00264368, 776)
extern "C" void script_vm_func_00264368() {
    u8* const g_7060 = *reinterpret_cast<u8* const*>(0x00447060u);
    u8* const g_74f4 = *reinterpret_cast<u8* const*>(0x004474F4u);

    *reinterpret_cast<u32*>(g_74f4 + 0x18) = *reinterpret_cast<const u32*>(g_7060 + 0x50);

    if (g_7060[0x94] != 0u) {
        g_74f4[0xB0] = 0u;
        g_74f4[0xB1] = 0u;
        *reinterpret_cast<u16*>(g_74f4 + 0xB2) = 10u;
        *reinterpret_cast<u16*>(g_74f4 + 0xB4) = 0u;
        *reinterpret_cast<float*>(g_74f4 + 0xB8) = 0.0f;
        *reinterpret_cast<float*>(g_74f4 + 0xBC) = 0.0f;
        *reinterpret_cast<float*>(g_74f4 + 0xC0) = 1.0f;
    }

    const signed short cur_b2 = *reinterpret_cast<const signed short*>(g_74f4 + 0xB2);
    if (cur_b2 > 0) {
        *reinterpret_cast<signed short*>(g_74f4 + 0xB2) = static_cast<signed short>(cur_b2 - 1);
    }

    u32 r5 = 0u;
    u32 r6 = 0u;
    u32 r7 = 0u;

    const u8* const g_49 = reinterpret_cast<const u8*>(0x0049F91Cu);
    if (g_49[0x18] == 0u && *reinterpret_cast<const u32*>(g_49 + 0x1C) == 0u) {
        if (g_74f4[0xB0] != 0u) {
            goto active_turn;
        }

        if (g_74f4[0xB1] != 0u) {
            if (ui_func_002c17d4(8u) == 0u && ui_func_002c17d4(7u) == 0u) {
                g_74f4[0xB1] = 0u;
            }
        }

        if (*reinterpret_cast<const signed short*>(g_74f4 + 0xB2) <= 6) {
            if (ui_func_002c17d4(8u) != 0u) {
                r5 = 1u;
            }
            if (ui_func_002c17d4(7u) != 0u) {
                r6 = 1u;
            }
            if (*reinterpret_cast<const u16*>(g_74f4 + 0xB2) == 0u) {
                if (script_vm_func_00276550() != 0u) {
                    r5 = 0u;
                    r6 = 0u;
                    r7 = 1u;
                } else if (ui_func_002c17d4(8u) != 0u &&
                           ui_func_002c17d4(7u) != 0u &&
                           ui_func_002bffbc(8u) == 0u &&
                           ui_func_002bffbc(7u) == 0u &&
                           g_74f4[0xB1] == 0u) {
                    r5 = 0u;
                    r6 = 0u;
                    r7 = 1u;
                }
            }
        }
    }

    if (g_74f4[0xB0] == 0u) {
        if (r7 == 0u) {
            goto manual_turn;
        }
        g_74f4[0xB0] = 1u;
        *reinterpret_cast<float*>(g_74f4 + 0x20C) = 0.0f;
        *reinterpret_cast<float*>(g_74f4 + 0x210) = 0.0f;
        *reinterpret_cast<float*>(g_74f4 + 0xB8) = *reinterpret_cast<const float*>(g_74f4 + 0x18);
        *reinterpret_cast<float*>(g_74f4 + 0xBC) = 180.0f;
        const float dir = script_vm_func_00287d74(g_74f4 + 0xB8);
        *reinterpret_cast<u16*>(g_74f4 + 0xB4) = 0u;
        *reinterpret_cast<float*>(g_74f4 + 0xC0) = (dir < 0.0f) ? -1.0f : 1.0f;
        if (g_74f4[0xB0] == 0u) {
            goto manual_turn;
        }
    }

active_turn:
    {
        const float dist = script_vm_func_0027f150(
            *reinterpret_cast<const float*>(g_74f4 + 0x18),
            *reinterpret_cast<const float*>(g_74f4 + 0xBC));
        if (dist <= 15.5f) {
            *reinterpret_cast<u32*>(g_74f4 + 0x18) = *reinterpret_cast<const u32*>(g_74f4 + 0xBC);
            g_74f4[0xB0] = 0u;
            *reinterpret_cast<u16*>(g_74f4 + 0xB2) = 10u;
            g_74f4[0xB1] = 1u;
        } else {
            float ang = *reinterpret_cast<const float*>(g_74f4 + 0x18);
            if (*reinterpret_cast<const float*>(g_74f4 + 0xC0) >= 0.0f) {
                ang += 15.0f;
            } else {
                ang -= 15.0f;
            }
            *reinterpret_cast<float*>(g_74f4 + 0x18) = ang;
        }
        if (g_74f4[0xB0] != 0u) {
            goto finish;
        }
        goto wrap_angle;
    }

manual_turn:
    if (r5 != 0u) {
        *reinterpret_cast<float*>(g_74f4 + 0x18) += 3.0f;
    } else if (r6 != 0u) {
        *reinterpret_cast<float*>(g_74f4 + 0x18) -= 3.0f;
    }

wrap_angle:
    {
        float ang = *reinterpret_cast<const float*>(g_74f4 + 0x18);
        if (ang < 0.0f) {
            ang += 360.0f;
            *reinterpret_cast<float*>(g_74f4 + 0x18) = ang;
        }
        union {
            float f;
            s32 i;
        } u;
        u.f = ang;
        if (u.i >= 0x43B40000) {
            ang -= 360.0f;
            *reinterpret_cast<float*>(g_74f4 + 0x18) = ang;
        }
    }

finish:
    *reinterpret_cast<u32*>(g_7060 + 0x50) = *reinterpret_cast<const u32*>(g_74f4 + 0x18);
}

extern "C" void func_002916b8(u32 slot);
extern "C" void func_00291950(void* p);
extern "C" void func_002915e4(void* a0, void* a1, void* a2, void* a3, void* s0);
extern "C" u8* func_002915b4(
    void* a0, void* a1, void* a2, u32 a3,
    void* s0, void* s1, u32 s2, u32 s3, u32 s4, u32 s5);
extern "C" float ui_func_002918c4(u32 a0, u32 a1, u32 a2);
extern "C" float ui_func_002914d8(u32 a0, u32 a1, u32 a2, u32 a3);
extern "C" float func_00291430(u32 a0, u32 a1, u32 a2);
extern "C" void func_00291304(
    void* a0, void* a1, void* a2, void* a3,
    void* s0, void* s1, void* s2, void* s3);

// DECOMP_FUNC(0x00193024, 784)
extern "C" void func_00193024(u8* self) {
    if (*reinterpret_cast<const u32*>(self + 0x184) == *reinterpret_cast<const u32*>(self + 0x24)) {
        signed short& v300 = *reinterpret_cast<signed short*>(self + 0x300);
        v300 = static_cast<signed short>(v300 - 1);
        *reinterpret_cast<u32*>(self + 0x24) = 0u;
        if (v300 <= 0) {
            for (s32 i = 0; i < 50; ++i) {
                func_002916b8(*reinterpret_cast<const u32*>(self + 0x238 + i * 4));
            }
            *reinterpret_cast<u32*>(self + 0x24) = 0u;
            *reinterpret_cast<u32*>(self + 0x28) = 0u;
            *reinterpret_cast<u32*>(self + 0x2C) = 0u;
            *reinterpret_cast<u32*>(self + 0x30) = 0u;
            u32* const flag228 = *reinterpret_cast<u32**>(self + 0x228);
            if (flag228 != nullptr) {
                *flag228 = 0u;
            }
            func_00291950(self);
            return;
        }
        *reinterpret_cast<u32*>(self + 0x00) = 0u;
        *reinterpret_cast<u32*>(self + 0x04) = 0u;
        *reinterpret_cast<u32*>(self + 0x08) = 0u;
        *reinterpret_cast<u32*>(self + 0x0C) = 0u;
        *reinterpret_cast<u32*>(self + 0x10) = 0u;
        *reinterpret_cast<u32*>(self + 0x14) = 0u;
        *reinterpret_cast<u32*>(self + 0x18) = 0u;
        *reinterpret_cast<u32*>(self + 0x1C) = 0u;
        *reinterpret_cast<u32*>(self + 0x20) = 0u;
        *reinterpret_cast<u32*>(self + 0x28) = 0u;
        *reinterpret_cast<u32*>(self + 0x2C) = 0u;
        *reinterpret_cast<u32*>(self + 0x30) = 0u;
        *reinterpret_cast<u32*>(self + 0x34) = 0u;
        func_002915e4(self + 0x16C, self + 0x28, self + 0x30, self + 0x0C, self + 0x18);
        return;
    }

    s32 cur_idx = *reinterpret_cast<const s32*>(self + 0x230);
    if (cur_idx >= 0 && *reinterpret_cast<const u32*>(self + 0x238 + cur_idx * 4) == 0u) {
        const s32 target = *reinterpret_cast<const s32*>(self + 0x234);
        while (target != cur_idx) {
            cur_idx = (cur_idx + 1) % 50;
            *reinterpret_cast<s32*>(self + 0x230) = cur_idx;
            if (*reinterpret_cast<const u32*>(self + 0x238 + cur_idx * 4) != 0u) {
                break;
            }
        }
    }

    const s32 target_n = static_cast<s32>(*reinterpret_cast<const float*>(self + 0x00));
    const s32 count = target_n - *reinterpret_cast<const s32*>(self + 0x34);
    for (s32 i = 0; i < count; ++i) {
        const s32 next_idx = (*reinterpret_cast<const s32*>(self + 0x234) + 1) % 50;
        if (*reinterpret_cast<const s32*>(self + 0x230) < 0) {
            *reinterpret_cast<s32*>(self + 0x230) = 0;
        } else {
            const u32 prev = *reinterpret_cast<const u32*>(self + 0x238 + next_idx * 4);
            if (prev != 0u) {
                func_00291950(reinterpret_cast<void*>(prev));
            }
        }

        const u32 sl = static_cast<u32>(*reinterpret_cast<const float*>(self + 0x17C) * 10.0f);
        u8* const node = func_002915b4(
            *reinterpret_cast<void* const*>(self + 0x224),
            self + 0x38,
            self + 0x16C,
            2u,
            *reinterpret_cast<void* const*>(self + 0x21C),
            self + 0x238 + next_idx * 4,
            static_cast<u32>(next_idx & 0xFF),
            static_cast<u32>(self[0x22C]),
            1u,
            *reinterpret_cast<const u32*>(self + 0x220));
        *reinterpret_cast<u8**>(self + 0x238 + next_idx * 4) = node;

        *reinterpret_cast<float*>(node + 0x120) +=
            ui_func_002918c4(2u, *reinterpret_cast<const u32*>(self + 0x180), 0x64u);
        *reinterpret_cast<float*>(node + 0x1F4) *= ui_func_002914d8(0u, sl, 10u, 10u);
        *reinterpret_cast<float*>(node + 0x34C) =
            static_cast<float>(*reinterpret_cast<const s32*>(self + 0x188));
        const float v1 = ui_func_002918c4(0u, *reinterpret_cast<const u32*>(self + 0x170), 0x64u);
        *reinterpret_cast<float*>(node + 0x340) =
            v1 + static_cast<float>(*reinterpret_cast<const s32*>(self + 0x16C)) * 0.01f;
        *reinterpret_cast<float*>(node + 0x33C) = 0.0f;
        *reinterpret_cast<float*>(node + 0x344) =
            func_00291430(2u, *reinterpret_cast<const u32*>(self + 0x174), 0x64u);

        *reinterpret_cast<s32*>(self + 0x34) += 1;
        *reinterpret_cast<s32*>(self + 0x234) = next_idx;
    }

    func_00291304(
        self + 0x16C, self + 0x2C, self + 0x28, self + 0x30,
        self, self + 0x0C, self + 0x18, self + 0x34);
    *reinterpret_cast<u32*>(self + 0x24) += 1u;
}

extern "C" u32 func_0010df5c(u32 ch_id);
extern "C" const char* engine_func_0010bec8(u32 track_id);
extern "C" s32 engine_func_002c1a48(const char* s1, const char* s2, u32 n);
extern "C" u32 func_0010f110();
extern "C" void engine_func_0010dd70(u32 ch_id, u32 track_id, u32 vol, u32 fade);
extern "C" u32 engine_func_0010c534(u32 ch_id, u32 fade);
extern "C" u32 func_0010d24c(u32 ch_id, u32 mode, u32 fade);

// DECOMP_FUNC(0x001062e0, 788)
extern "C" void engine_func_001062e0() {
    if (engine_func_002c583c(1u) != 0u) {
        return;
    }

    u8* const g_c53c4 = reinterpret_cast<u8*>(0x004C53C4u);
    u8* const g_4e098 = reinterpret_cast<u8*>(0x0044E098u);

    for (s32 i = 0; i < 2; ++i) {
        u8* const ch = g_c53c4 + i * 0x20;
        u8* other = nullptr;
        if (i == 0) {
            other = g_c53c4 + 0x20;
        } else if (i == 1) {
            other = g_c53c4;
        }

        u32 flags = *reinterpret_cast<u32*>(ch + 0x1C);
        if ((flags & 1u) == 0u) {
            if ((flags & 0x100u) != 0u && (flags & 0x3Eu) == 0u) {
                const u32 p18 = *reinterpret_cast<const u32*>(ch + 0x18);
                flags |= 1u;
                *reinterpret_cast<u32*>(ch + 0x1C) = flags;
                if (p18 != 0u) {
                    flags |= 4u;
                    *reinterpret_cast<u32*>(ch + 0x1C) = flags;
                }
                const u32 p10 = *reinterpret_cast<const u32*>(ch + 0x10);
                *reinterpret_cast<u32*>(ch + 0x10) = 0u;
                *reinterpret_cast<u32*>(ch + 0x04) = p18;
                *reinterpret_cast<u32*>(ch + 0x0C) = p10;
                *reinterpret_cast<u32*>(ch + 0x18) = 0u;
                *reinterpret_cast<u32*>(ch + 0x1C) = flags & ~0x100u;
            }
            continue;
        }

        if ((flags & 2u) == 0u) {
            if ((flags & 0x800u) != 0u) {
                const s32 cnt = *reinterpret_cast<const s32*>(ch + 0x14);
                if (cnt <= 15) {
                    *reinterpret_cast<s32*>(ch + 0x14) = cnt + 1;
                    continue;
                }
                *reinterpret_cast<u32*>(ch + 0x1C) = flags & ~0x800u;
                *reinterpret_cast<s32*>(ch + 0x14) = 0;
            }

            const u32 track_id = *reinterpret_cast<const u32*>(ch + 0x0C);
            const char* const name = engine_func_0010bec8(track_id);
            u32 vol = g_4e098[0];
            if (engine_func_002c1a48(name, "STRM_ENV", 8u) == 0) {
                const u32 id = *reinterpret_cast<const u32*>(ch + 0x0C);
                if (id != 0x0100007Bu && id != 0x0100007Cu && id != 0x0100007Du &&
                    id != 0x01000081u && id != 0x01000082u && id != 0x01000083u &&
                    id != 0x0100008Au && id != 0x0100008Bu && id != 0x0100008Cu &&
                    id != 0x010000A4u) {
                    vol = func_0010f110();
                }
            }
            engine_func_0010dd70(
                *reinterpret_cast<const u32*>(ch + 0x00),
                *reinterpret_cast<const u32*>(ch + 0x0C),
                vol,
                *reinterpret_cast<const u32*>(ch + 0x04));
            *reinterpret_cast<u32*>(ch + 0x1C) |= 2u;
            continue;
        }

        const u32 st = func_0010df5c(*reinterpret_cast<const u32*>(ch + 0x00));
        flags = *reinterpret_cast<u32*>(ch + 0x1C);
        if ((flags & 4u) != 0u) {
            if ((st & 0x20u) == 0u) {
                *reinterpret_cast<u32*>(ch + 0x1C) = flags & ~4u;
            }
            continue;
        }

        if ((flags & 8u) != 0u) {
            if (engine_func_0010c534(*reinterpret_cast<const u32*>(ch + 0x00),
                                     *reinterpret_cast<const u32*>(ch + 0x08)) == 0u) {
                continue;
            }
            flags = *reinterpret_cast<u32*>(ch + 0x1C) & ~0xAu;
            *reinterpret_cast<u32*>(ch + 0x1C) = flags;
            *reinterpret_cast<u32*>(ch + 0x0C) = 0u;
            *reinterpret_cast<u32*>(ch + 0x04) = 0u;
            *reinterpret_cast<u32*>(ch + 0x08) = 0u;
            *reinterpret_cast<u32*>(ch + 0x14) = 0u;
            if ((flags & 0x100u) != 0u) {
                const u32 p10 = *reinterpret_cast<const u32*>(ch + 0x10);
                const u32 p18 = *reinterpret_cast<const u32*>(ch + 0x18);
                *reinterpret_cast<u32*>(ch + 0x10) = 0u;
                *reinterpret_cast<u32*>(ch + 0x0C) = p10;
                *reinterpret_cast<u32*>(ch + 0x04) = p18;
                *reinterpret_cast<u32*>(ch + 0x18) = 0u;
                *reinterpret_cast<u32*>(ch + 0x1C) = (flags | 5u) & ~0x100u;
            } else {
                *reinterpret_cast<u32*>(ch + 0x1C) = 0u;
                const u32 active = *reinterpret_cast<const u32*>(g_4e098 + 4);
                if (*reinterpret_cast<const u32*>(ch + 0x00) == active &&
                    (*reinterpret_cast<const u32*>(other + 0x1C) & 0x400u) == 0u) {
                    *reinterpret_cast<u32*>(g_4e098 + 4) = (active == 0u) ? 1u : 0u;
                }
            }
            continue;
        }

        if ((flags & 0x10u) != 0u) {
            if (func_0010d24c(*reinterpret_cast<const u32*>(ch + 0x00), 0u,
                              *reinterpret_cast<const u32*>(ch + 0x08)) == 0u) {
                continue;
            }
            *reinterpret_cast<u32*>(ch + 0x1C) = (*reinterpret_cast<u32*>(ch + 0x1C) & ~0x10u) | 0x20u;
            const u32 active = *reinterpret_cast<const u32*>(g_4e098 + 4);
            if (*reinterpret_cast<const u32*>(ch + 0x00) == active &&
                (*reinterpret_cast<const u32*>(other + 0x1C) & 0x400u) == 0u) {
                *reinterpret_cast<u32*>(g_4e098 + 4) = (active == 0u) ? 1u : 0u;
            }
            continue;
        }

        if ((flags & 0x40u) != 0u) {
            if (func_0010d24c(*reinterpret_cast<const u32*>(ch + 0x00), 1u,
                              *reinterpret_cast<const u32*>(ch + 0x04)) == 0u) {
                continue;
            }
            flags = *reinterpret_cast<u32*>(ch + 0x1C) & ~0x40u;
            *reinterpret_cast<u32*>(ch + 0x1C) = flags;
            if ((flags & 0x200u) != 0u) {
                *reinterpret_cast<u32*>(ch + 0x1C) = (flags & ~0xA00u) | 0x10u;
            } else if ((flags & 0x800u) != 0u) {
                *reinterpret_cast<u32*>(ch + 0x1C) = (flags & ~0x800u) | 8u;
            }
            continue;
        }
    }
}

// DECOMP_FUNC(0x002f5584, 788)
//
// Writes `size` bytes from `buf` to `path` through the storage backend selected
// by `kind` (0..3). The stack FileStream is initialised from the VTT at
// 0x00420768 and destroyed on every exit path. Returns 1 on success, else 0.
//
// The open/close/destroy helpers share their C prototypes with the sibling
// reader engine_func_002f5348 (declared above); the write-path helpers are
// declared here because they are only used by this writer.

// Open an existing file for reading (mode 1); returns an nn::Result-style word.
// (engine_func_0024ada8 / 0024acf0 / 002cbf38 / 001ff988 are declared above.)

// Open for writing; args are (stream, path, size).
extern "C" u32 engine_func_002cbde4(void* obj, const void* path, u32 size);
extern "C" u32 engine_func_00220234(void* obj, const void* path, u32 size);
extern "C" u32 engine_func_002e130c(void* obj, const void* path, u32 size);

// Delete an existing file before retrying the write open.
extern "C" u32 engine_func_002cbee0(const void* path);
extern "C" u32 engine_func_0022033c(const void* path);
extern "C" u32 engine_func_002e13e4(const void* path);

// Write buffered data; args are (stream, 0, buf, size).
extern "C" u32 engine_func_00220184(void* obj, u32 zero, const void* buf, u32 size);
extern "C" u32 engine_func_00210364(void* obj, u32 zero, const void* buf, u32 size);
extern "C" u32 engine_func_002d5f20(void* obj, u32 zero, const void* buf, u32 size);

extern "C" u32 engine_func_002f5584(u32 kind, const void* path, const void* buf, u32 size) {
    // 0x20-byte stack FileStream: vptr at +0x00, vbase slot at
    // *(vptr - 0x30), and two VTT words. The last word (+0x1C) is untouched.
    u32 stream[8] = {0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u};
    const u32* const vtt = reinterpret_cast<const u32*>(0x00420768u);
    const u32 vtbl0 = vtt[0];
    stream[0] = vtbl0;
    const s32 vbase_off = *reinterpret_cast<const s32*>(
        static_cast<std::uintptr_t>(vtbl0 - 0x30u));
    *reinterpret_cast<u32*>(reinterpret_cast<u8*>(stream) + vbase_off) = vtt[8];
    stream[1] = vtt[9];

    // Default result when no backend call is made (kind > 3): an error word.
    constexpr u32 kErr = 0xE7E3FFFFu;
    // Reported when a delete is required but the path is null.
    constexpr u32 kNullPathErr = 0xC8804464u;

    // 1. Probe/open the target in read mode 1.
    u32 open_res = kErr;
    if (kind == 0u) {
        open_res = engine_func_0024ada8(stream, path, 1u);
    } else if (kind == 1u) {
        open_res = engine_func_0024acf0(stream, path, 1u);
    } else if (kind == 2u) {
        open_res = engine_func_002cbf38(stream, path, 1u);
    } else if (kind == 3u) {
        open_res = engine_func_001ff988(stream, path, 1u);
    }

    // Open for write when the probe failed, or when the existing file must be
    // recreated (module 0x11, summary 0x64..0xB3).
    const u32 module = (open_res >> 10) & 0xFFu;
    const u32 summary = open_res & 0x3FFu;
    if ((open_res & 0x80000000u) != 0u ||
        (module == 0x11u && summary >= 0x64u && summary <= 0xB3u)) {
        u32 write_open = kErr;
        if (kind == 0u) {
            write_open = engine_func_002cbde4(stream, path, size);
        } else if (kind == 1u) {
            write_open = engine_func_00220234(stream, path, size);
        } else if (kind == 2u) {
            write_open = engine_func_002e130c(stream, path, size);
        }

        if ((write_open & 0x80000000u) != 0u) {
            // 2. Delete the stale file (or record the null-path error) and
            //    retry the write open once.
            if (path == nullptr) {
                *reinterpret_cast<u32*>(0x004651E8u + 0x10u) = kNullPathErr;
            } else if (kind == 0u) {
                engine_func_002cbee0(path);
            } else if (kind == 1u) {
                engine_func_0022033c(path);
            } else if (kind == 2u) {
                engine_func_002e13e4(path);
            }

            write_open = kErr;
            if (kind == 0u) {
                write_open = engine_func_002cbde4(stream, path, size);
            } else if (kind == 1u) {
                write_open = engine_func_00220234(stream, path, size);
            } else if (kind == 2u) {
                write_open = engine_func_002e130c(stream, path, size);
            }
        }

        // The original re-tests the write-open result here.
        open_res = write_open;
    }

    if ((open_res & 0x80000000u) != 0u) {
        engine_func_002bb9c8(stream, 0u);
        return 0u;
    }

    // 3. Write the buffer at offset 0.
    u32 write_res = kErr;
    if (kind == 0u) {
        write_res = engine_func_00220184(stream, 0u, buf, size);
    } else if (kind == 1u) {
        write_res = engine_func_00210364(stream, 0u, buf, size);
    } else if (kind == 2u) {
        write_res = engine_func_002d5f20(stream, 0u, buf, size);
    }

    if ((write_res & 0x80000000u) != 0u) {
        engine_func_002bb9c8(stream, 0u);
        return 0u;
    }

    // 4. Close the stream.
    u32 close_res = kErr;
    if (kind == 0u) {
        close_res = engine_func_0024ac80(stream);
    } else if (kind == 1u) {
        close_res = engine_func_0024ac48(stream);
    } else if (kind == 2u) {
        close_res = engine_func_0024ac10(stream);
    } else if (kind == 3u) {
        close_res = engine_func_0024acb8(stream);
    }

    // 5. Destroy the stream and report success unless close failed.
    engine_func_002bb9c8(stream, 0u);
    return ((close_res & 0x80000000u) == 0u) ? 1u : 0u;
}

// DECOMP_FUNC(0x003525b8, 796)
extern "C" s32 func_003538d4(u8* self, u32 a1, u32 a2);
extern "C" u32 func_003538b8(u8* self);
extern "C" u32 func_003538c4(u8* self);
extern "C" void func_0035334c();
extern "C" void func_0023a3a4(const char* s);
extern "C" void func_003532a8(u8 flag);
extern "C" s32 func_0035fa44(
    u32 a1, u32 a2, const void* fp, u32 a3_4,
    u32 s0, u32 s1, u32 s2, u32 s3, u32 s4, u32 s5,
    u32 s6, u32 s7, u32 s8, u32 s9, u32 s10, u32 s11,
    u32 s12, u32 s13, u32 s14, u32 s15, u32 s16);
extern "C" s32 engine_func_002b45f8(const char* a, const char* b, u32 max_len);
extern "C" u32 script_vm_func_002c607c(const char* s, char** endptr, s32 base);
extern "C" s32 func_0035382c(u8* self, const u32* pair, u16 code);

// Error sentinel returned by the original when the parsed catalog header or its
// trailing word is absent at loop exit.
constexpr u32 kEngine3525b8MissingItem = 0xC8A13908u;

extern "C" s32 engine_func_003525b8(u8* self, u32 a1, u32 a2, const u8* a3) {
    // 1. Open/fetch the catalog source; a negative result aborts immediately.
    const s32 open_rc = func_003538d4(self,
                                      *reinterpret_cast<const u32*>(a3 + 0x10),
                                      *reinterpret_cast<const u32*>(a3 + 0x14));
    if (open_rc < 0) {
        return open_rc;
    }

    // 2. Register the five metadata keys and publish the header byte.
    const u32 v_38b8 = func_003538b8(self);
    const u32 v_38c4 = func_003538c4(self);
    func_0035334c();
    func_0023a3a4("Prices");
    func_0023a3a4("Ratings");
    func_0023a3a4("NewSince");
    func_0023a3a4("TitleVersion");
    func_0023a3a4("sys.ItemCode");
    func_003532a8(a3[0x28]);

    // 3. Null descriptor words fall back to the descriptor itself.
    const u32 sel_self = (*reinterpret_cast<const u32*>(a3 + 0x00) != 0u)
        ? *reinterpret_cast<const u32*>(a3 + 0x00)
        : reinterpret_cast<u32>(a3);
    const u32 sel_08 = (*reinterpret_cast<const u32*>(a3 + 0x08) != 0u)
        ? *reinterpret_cast<const u32*>(a3 + 0x08)
        : reinterpret_cast<u32>(a3);
    const u32 sel_18 = (*reinterpret_cast<const u32*>(a3 + 0x18) != 0u)
        ? *reinterpret_cast<const u32*>(a3 + 0x18)
        : reinterpret_cast<u32>(a3);
    const u32 flag_18 = (*reinterpret_cast<const u32*>(a3 + 0x18) != 0u) ? 1u : 0u;
    const u32 sel_1C = (*reinterpret_cast<const u32*>(a3 + 0x1C) != 0u)
        ? *reinterpret_cast<const u32*>(a3 + 0x1C)
        : reinterpret_cast<u32>(a3);
    const u32 flag_1C = (*reinterpret_cast<const u32*>(a3 + 0x1C) != 0u) ? 1u : 0u;

    const s32 ser_rc = func_0035fa44(
        a1,
        a2,
        reinterpret_cast<const void*>(sel_self),
        *reinterpret_cast<const u32*>(a3 + 0x04),
        0x004E655Cu,
        *reinterpret_cast<const u32*>(0x00471A50u),
        sel_08,
        *reinterpret_cast<const u32*>(a3 + 0x0C),
        0x004E675Cu,
        *reinterpret_cast<const u32*>(0x00471A54u),
        v_38b8,
        v_38c4,
        sel_18,
        flag_18,
        sel_1C,
        flag_1C,
        *reinterpret_cast<const u32*>(a3 + 0x2C),
        *reinterpret_cast<const u32*>(a3 + 0x30),
        reinterpret_cast<u32>(self + 4),
        *reinterpret_cast<const u32*>(self + 8),
        *reinterpret_cast<const u32*>(self + 0x0C));
    if (ser_rc < 0) {
        return ser_rc;
    }

    // 4. Walk the parsed items (stride 0x30) and submit one packed pair each.
    const u8* const hdr = *reinterpret_cast<const u8* const*>(self + 4);
    if (hdr != nullptr && *reinterpret_cast<const u32*>(hdr + 4) != 0u) {
        for (u32 idx = 0u; ; ++idx) {
            const u8* const cur = *reinterpret_cast<const u8* const*>(self + 4);
            const u8* const item =
                (cur != nullptr && idx <= *reinterpret_cast<const u32*>(cur + 4))
                ? (*reinterpret_cast<const u8* const*>(cur) + idx * 0x30u)
                : nullptr;

            const u32 pair_count = *reinterpret_cast<const u32*>(item + 0x1C);
            const char* value = nullptr;
            for (u32 k = 0u; k < pair_count; ++k) {
                const char* const* const pairs =
                    *reinterpret_cast<const char* const* const*>(item + 0x18);
                if (engine_func_002b45f8(pairs[k * 2u], "TitleVersion", 0x40u) == 0) {
                    value = pairs[k * 2u + 1u];
                    break;
                }
            }

            const u16 code =
                static_cast<u16>(script_vm_func_002c607c(value, nullptr, 10));
            const u32 w0 = *reinterpret_cast<const u32*>(item + 0x00);
            const u32 w4 = *reinterpret_cast<const u32*>(item + 0x04);

            const u32 p0 = (((w4 << 24) | (w0 >> 8)) << 12) >> 12;
            u32 lo8;
            if ((w4 >> 14) == 0x10u && static_cast<u16>(w4) == 0x8Cu) {
                lo8 = 0u;
            } else if ((w4 >> 14) == 0x10u && static_cast<u16>(w4) == 0x0Du) {
                lo8 = 1u;
            } else {
                lo8 = 0xFFu;
            }
            const u32 hi16 = ((w4 >> 14) == 0x10u) ? 0u : (w4 << 24);
            const u32 p1 = hi16 | ((w0 << 8) & 0xFF00u) | lo8;

            const u32 out_pair[2] = {p0, p1};
            const s32 put_rc = func_0035382c(self, out_pair, code);
            if (put_rc < 0) {
                return put_rc;
            }

            const u8* const next = *reinterpret_cast<const u8* const*>(self + 4);
            const u32 next_count = (next != nullptr)
                ? *reinterpret_cast<const u32*>(next + 4)
                : 0u;
            if (idx + 1u >= next_count) {
                break;
            }
        }
    }

    // 5. Success only when the header pointer and its trailing word are present.
    const u8* const tail = *reinterpret_cast<const u8* const*>(self + 4);
    if (tail != nullptr && *reinterpret_cast<const u32*>(tail + 8) != 0u) {
        return 0;
    }
    return static_cast<s32>(kEngine3525b8MissingItem);
}

extern "C" void* camp_func_0032839c(s32 key0, s32 key1);
extern "C" void script_vm_func_0026fc24(void);
extern "C" u32 script_vm_func_001fb434(void);
extern "C" void script_vm_func_00275984(void);
extern "C" s32 script_vm_func_00255050(u32 type);
extern "C" u32 script_vm_func_002857e4(void);
extern "C" u32 script_vm_func_002c0ba8(u32 id);
extern "C" void script_vm_func_001b48c0(u32 type, u32 id);
extern "C" s32 script_vm_func_0026fcb4(u32 type, u32 id);
extern "C" s32 ui_func_002876d0(u32 id);
extern "C" u32 script_vm_func_00290694(void);
extern "C" u32 script_vm_func_00287afc(void);
extern "C" s32 engine_func_00287590(u32 id);

// DECOMP_FUNC(0x0027d35c, 800)
//
// Selects and publishes the "hud" descriptor at 0x0049F91C+0x28, then reports
// the publication state through ui_func_002876d0. The state object is reached
// via the pointer stored at 0x00447E28; its fields 0x24/0x2C/0x30/0x40/0x45
// drive the mode decisions. The 92-byte entry table at 0x00448E18 is indexed
// by script_vm_func_0026fcb4; entry fields +8/+0xC/+0xE/+0x10/+0x14 are used.
// Returns 1 on the early "busy" path, otherwise the result of the 0x00287590
// tail call (or ui_func_002876d0's unexpected non-zero, non-3 result).
extern "C" s32 script_vm_func_0027d35c(void) {
    u8* const state = *reinterpret_cast<u8* volatile*>(0x00447E28u);
    u8* const hud = reinterpret_cast<u8*>(0x0049F91Cu);
    const u8* const status = reinterpret_cast<const u8*>(0x0049FA1Cu);
    u8* const entries = reinterpret_cast<u8*>(0x00448E18u);

    // 1. Optional lookup keyed by the two state words at 0x2C/0x30.
    {
        u8* const row = static_cast<u8*>(camp_func_0032839c(
            static_cast<s32>(*reinterpret_cast<const u32*>(state + 0x2C)),
            static_cast<s32>(*reinterpret_cast<const u32*>(state + 0x30))));
        if (row != nullptr) {
            const u8 byte = row[2];
            const s8 value = static_cast<s8>(byte);
            *reinterpret_cast<u16*>(hud + 0x2C) =
                static_cast<u16>(static_cast<s16>(value));
            hud[0x2E] = byte;
        }
    }

    // 2. Busy path: flag bytes at 0x0049FA1C and in the state object.
    if (status[0x45] != 0 || status[0x1D] == 0 || state[0x45] != 0) {
        script_vm_func_0026fc24();
        hud[0x11D] = 1;
        return 1;
    }

    // 3. Two preparatory paths converge on the table lookup below.
    if (script_vm_func_001fb434() == 0) {
        script_vm_func_001b48c0(
            *reinterpret_cast<const u32*>(state + 0x2C),
            *reinterpret_cast<const u32*>(state + 0x30));
    } else {
        const u32 mode = *reinterpret_cast<const u32*>(state + 0x24);
        if (mode != 0x17u && mode != 0x18u) {
            script_vm_func_00275984();
        }
    }

    // 4. Type 0x18 shortcut: only for helper result 1 and flag 0x2C clear.
    if (*reinterpret_cast<const u32*>(state + 0x2C) == 0x18u) {
        if (script_vm_func_002857e4() == 1u &&
            script_vm_func_002c0ba8(0x2Cu) == 0u) {
            const u32 id = 0x01000086u;
            *reinterpret_cast<u32*>(hud + 0x28) = id;
            const s32 rc = ui_func_002876d0(id);
            if (rc == 0 || rc == 3) {
                goto tail_call;
            }
            return rc;
        }
    } else if (script_vm_func_00255050(
                   *reinterpret_cast<const u32*>(state + 0x2C)) == 1) {
        // 5. Lookup with the raw state pair, then take entry field +0x14.
        const s32 index = script_vm_func_0026fcb4(
            *reinterpret_cast<const u32*>(state + 0x2C),
            *reinterpret_cast<const u32*>(state + 0x30));
        u8* const entry = entries + static_cast<u32>(index) * 92u;
        const u32 candidate = *reinterpret_cast<const u32*>(entry + 0x14);
        if (candidate != 0u) {
            *reinterpret_cast<u32*>(hud + 0x28) = candidate;
            const s32 rc = ui_func_002876d0(candidate);
            if (rc == 0 || rc == 3) {
                goto tail_call;
            }
            return rc;
        }
    }

    // 6. Main table lookup; type 0x18 uses the fixed key 1.
    {
        const u32 type = *reinterpret_cast<const u32*>(state + 0x2C);
        const u32 key = (type == 0x18u)
            ? 1u
            : *reinterpret_cast<const u32*>(state + 0x30);
        const s32 index = script_vm_func_0026fcb4(type, key);
        u8* const entry = entries + static_cast<u32>(index) * 92u;

        *reinterpret_cast<u32*>(hud + 0x28) =
            *reinterpret_cast<const u32*>(entry + 0x08);

        // 7. Entry field +0x10 overrides the published id unless one of the
        //    signed 16-bit flags at +0xC/+0xE selects the earlier value.
        if (*reinterpret_cast<const u32*>(entry + 0x10) != 0u) {
            const s16 flag0 = *reinterpret_cast<const s16*>(entry + 0x0C);
            const bool keep = (flag0 != 0) &&
                (script_vm_func_002c0ba8(
                     static_cast<u32>(static_cast<s32>(flag0))) == 0u);
            if (!keep) {
                const s16 flag1 = *reinterpret_cast<const s16*>(entry + 0x0E);
                const bool override_id = (flag1 == 0) ||
                    (script_vm_func_002c0ba8(
                         static_cast<u32>(static_cast<s32>(flag1))) == 0u);
                if (override_id) {
                    *reinterpret_cast<u32*>(hud + 0x28) =
                        *reinterpret_cast<const u32*>(entry + 0x10);
                }
            }
        }
    }

    // 8. Mode-specific publication tweaks. Type 0x13 (or 0x18 with helper
    //    result 5) consults flags 0x62C/0x648; type 0x13 with sub-mode <= 4
    //    consults flag 0xB8.
    {
        const u32 type = *reinterpret_cast<const u32*>(state + 0x2C);
        if (type == 0x13u ||
            (type == 0x18u && script_vm_func_002857e4() == 5u)) {
            if (script_vm_func_002c0ba8(0x62Cu) != 0u &&
                script_vm_func_002c0ba8(0x648u) == 0u) {
                *reinterpret_cast<u32*>(hud + 0x28) = 0x0100007Au;
                goto publish;
            }
            if (type == 0x13u &&
                static_cast<s32>(*reinterpret_cast<const u32*>(state + 0x30)) <= 4 &&
                script_vm_func_002c0ba8(0xB8u) == 0u) {
                goto publish;
            }
        }
    }

    // 9. Generic publication selection.
    {
        const u32 mode = *reinterpret_cast<const u32*>(state + 0x40);
        if (mode == 1u || mode == 2u) {
            goto publish;
        }
        const u32 type = *reinterpret_cast<const u32*>(state + 0x2C);
        if (type == 0x29u || type == 0x2Au || type == 0x2Bu) {
            goto publish;
        }
        const u32 probe = script_vm_func_00290694();
        if (probe == 0u || probe == 0x15Fu || probe == 0x160u ||
            probe == 0x161u || probe == 0x164u || probe == 0x165u ||
            probe == 0x166u || probe == 0x167u || probe == 0x168u) {
            goto publish;
        }
        *reinterpret_cast<u32*>(hud + 0x28) =
            (script_vm_func_00287afc() == 1u) ? 0x01000037u : 0x01000038u;
    }

publish:
    // 10. Report and tail-publish the chosen id.
    {
        const s32 rc = ui_func_002876d0(*reinterpret_cast<const u32*>(hud + 0x28));
        if (rc == 3) {
            goto tail_call;
        }
        if (rc != 0) {
            return rc;
        }
    }
    script_vm_func_0026fc24();

tail_call:
    return engine_func_00287590(*reinterpret_cast<const u32*>(hud + 0x28));
}

// Direct callees of ui_func_0037dc24. func_0037f8e0 is a virtual-dispatch
// thunk (owner->[0x7C]->[0]->[8]) that receives its descriptor pointer in r2;
// its r3 is loaded from 0x00411A08 and discarded. func_0037fd70 consumes its
// float in s0 (hard-float ABI), which is the slot-descaling value.
extern "C" void func_001311d8(u8* obj);
extern "C" u8* func_0037f8e0(u8* owner, u32 a1, const void* desc);
extern "C" void func_00235a4c(u8* dst, u32 value);
extern "C" void func_00235a08(u8* obj);
extern "C" void func_00379ea0(u8* dst, u32 index);
extern "C" void func_00379e28(u8* dst, u32 value);
extern "C" void func_00379e08(u8* dst, u32 value);
extern "C" void func_0037fd70(u8* obj, float value, u32 a1, u32 a2);
extern "C" u32 func_002c615c(u32 numerator, u32 denominator);
extern "C" void func_002a2224(u32 a0, s32 a1);

namespace ui_0037dc24_desc {
// Eight-word descriptor staged on the stack and passed by pointer to
// func_0037f8e0. Every field is written from the register evidence.
struct Desc {
    u32 f00;  // self->[0x50]
    u32 f04;  // b
    u32 f08;  // fixed-point scalar (s32 bit pattern)
    u32 f0C;  // flag ? 0xFFFFFFFF : sb
    u32 f10;  // (s32)(s8)self[0x87]
    u32 f14;  // self->[0xC0]->[0x75] + self[0x89]
    u32 f18;  // *(u32*)0x00411A10
    u32 f1C;  // self
};
} // namespace ui_0037dc24_desc

// DECOMP_FUNC(0x0037dc24, 800)
//
// Configure or allocate a UI animation node hanging off self->[0xC4] and
// publish its fade/slot state. The static-constant multiply at 0x81020409
// yields a signed fixed-point scalar (high 32 bits, then /64 truncating with
// the original's negative-multiple quirk). The scalar is converted to a float
// with 1/127 and squared into node->[0x100]. Heap nodes are created by
// func_0037f8e0, prepended to the self->[0xC4] list, and any earlier node with
// the same id byte at [0x128] is cleared (func_00235A4C(...,0x7E) then
// func_00235A08). Returns the node, or nullptr when func_0037f8e0 fails.
extern "C" u8* ui_func_0037dc24(u8* self, u32 b, u32 c, u32 sb, u32 flag) {
    namespace desc_ns = ui_0037dc24_desc;
    constexpr float kInv127 = 0.0078740157f;  // 0x3C010204, 1/127

    // 1. Signed fixed-point scalar: (high32((s32)(self[0x85] * c) * 0x81020409))
    //    divided by 64 the way the original subtracts the sign bit.
    const u32 mixed = static_cast<u32>(self[0x85]) * c;
    const s64 wide = static_cast<s64>(static_cast<s32>(mixed)) * 0x81020409LL;
    const s32 scalar_hi =
        static_cast<s32>(static_cast<u32>(static_cast<u64>(wide) >> 32));
    const s32 scaled = (scalar_hi >> 6) - (scalar_hi >> 31);
    const float ratio = static_cast<float>(scaled) * kInv127;
    const float fade = ratio * ratio;

    // 2. Optional pre-update of the flag-selected node.
    u8* obj = (flag != 0u) ? *reinterpret_cast<u8**>(self + 0xC4) : nullptr;
    if (flag != 0u && obj != nullptr) {
        obj[0x126] = static_cast<u8>(b);
        *reinterpret_cast<float*>(obj + 0x100) = fade;
    }

    // 3. Reuse an existing node or fall through to allocation.
    bool reuse = false;
    if (self[0x27] != 0u) {
        obj = *reinterpret_cast<u8**>(self + 0xC4);
        if (obj == nullptr) {
            reuse = false;
        } else if (obj[0x90] == 4u) {
            func_001311d8(obj);
            reuse = false;
        } else {
            *reinterpret_cast<u32*>(obj + 0x120) = sb;
            obj[0x126] = static_cast<u8>(b);
            *reinterpret_cast<float*>(obj + 0x100) = fade;
            reuse = true;
        }
    } else if (obj != nullptr) {
        reuse = true;
    }

    // 4. Allocate, clear duplicate ids, and prepend to the list.
    if (!reuse) {
        desc_ns::Desc desc;
        desc.f00 = *reinterpret_cast<const u32*>(self + 0x50);
        desc.f04 = b;
        desc.f08 = static_cast<u32>(scaled);
        desc.f0C = (flag != 0u) ? 0xFFFFFFFFu : sb;
        desc.f10 = static_cast<u32>(
            static_cast<s32>(static_cast<s8>(self[0x87])));
        desc.f14 = static_cast<u32>(self[0x89]) +
            static_cast<u32>(
                (*reinterpret_cast<const u8**>(self + 0xC0))[0x75]);
        desc.f18 = *reinterpret_cast<const u32*>(0x00411A10u);
        desc.f1C = reinterpret_cast<u32>(self);

        obj = func_0037f8e0(
            *reinterpret_cast<u8**>(self + 0xC0), self[0x4D], &desc);
        if (obj == nullptr) {
            return nullptr;
        }

        if (obj[0x128] != 0u) {
            u8* cur = *reinterpret_cast<u8**>(self + 0xC4);
            while (cur != nullptr) {
                if (cur[0x128] == obj[0x128]) {
                    func_00235a4c(cur + 0x90, 0x7Eu);
                    func_00235a08(cur);
                }
                cur = *reinterpret_cast<u8**>(cur + 0x138);
            }
        }
        *reinterpret_cast<u8**>(obj + 0x138) =
            *reinterpret_cast<u8**>(self + 0xC4);
        *reinterpret_cast<u8**>(self + 0xC4) = obj;
    }

    // 5. Publish the sub-slot selectors (unsigned <= 0x7F, except the signed
    //    halfword at self+0x90 which uses a signed <= 0x7F test).
    {
        const u32 sel_8C = self[0x8C];
        if (sel_8C <= 0x7Fu) {
            func_00379ea0(obj + 0x90, sel_8C);
        }
        const u32 sel_8D = self[0x8D];
        if (sel_8D <= 0x7Fu) {
            func_00379e28(obj + 0x90, sel_8D);
        }
        const u32 sel_8E = self[0x8E];
        if (sel_8E <= 0x7Fu) {
            obj[0x90 + 0x18] = static_cast<u8>(sel_8E);
        }
        const u32 sel_8F = self[0x8F];
        if (sel_8F <= 0x7Fu) {
            func_00235a4c(obj + 0x90, sel_8F);
        }
        const s32 sel_90 = static_cast<s16>(
            *reinterpret_cast<const u16*>(self + 0x90));
        if (sel_90 <= 0x7F) {
            func_00379e08(obj + 0x90, static_cast<u32>(sel_90));
        }
    }

    // 6. Frame fade value, optionally biased by (self[0x8A] - b).
    float value = *reinterpret_cast<const float*>(self + 0x68);
    if (self[0x4B] != 0u) {
        value = static_cast<float>(static_cast<s32>(
            static_cast<u32>(self[0x8A]) - b)) + value;
    }

    // 7. Slot transition step: |value| * (self[0x8B]^2), >>5 then *5.
    if (self[0x8B] != 0u) {
        const u32 square = static_cast<u32>(self[0x8B]) *
            static_cast<u32>(self[0x8B]);
        const float magnitude = (value >= 0.0f) ? value : -value;
        const s32 converted =
            static_cast<s32>(magnitude *
                             static_cast<float>(static_cast<s32>(square)));
        const u32 step = static_cast<u32>(converted >> 5) * 5u;
        func_0037fd70(obj, value, step, 1u);
    } else {
        func_0037fd70(obj, value, sb, 0u);
    }

    // 8. Byte lerp state at obj+0x110; publishes self[0x8A] = (u8)b.
    {
        u8* const anim = obj + 0x110;
        self[0x8A] = static_cast<u8>(b);
        const u8 target = (self[0x49] != 0u) ? 0x00u : 0xFFu;
        const u32 elapsed = *reinterpret_cast<const u16*>(anim + 4);
        const u32 duration = *reinterpret_cast<const u16*>(anim + 2);
        u32 current;
        if (elapsed >= duration) {
            current = anim[1];
        } else {
            const u32 delta = static_cast<u32>(anim[1]) -
                static_cast<u32>(anim[0]);
            const u32 interpolated =
                func_002c615c(delta * elapsed, duration);
            current = (interpolated + static_cast<u32>(anim[0])) & 0xFFu;
        }
        anim[0] = static_cast<u8>(current);
        anim[1] = target;
        *reinterpret_cast<u16*>(anim + 2) = 0u;
        *reinterpret_cast<u16*>(anim + 4) = 0u;
    }

    // 9. Copy three owner bytes and report the signed selector at self[0x41].
    {
        u8* const owner = *reinterpret_cast<u8**>(self + 0xC0);
        obj[0xC9] = owner[0x5C];
        obj[0x124] = owner[0x34];
        obj[0x125] = owner[0x35];
    }
    func_002a2224(*reinterpret_cast<const u32*>(obj + 0x134),
                  static_cast<s32>(static_cast<s8>(self[0x41])));
    return obj;
}

// ---------------------------------------------------------------------------
// 0x0027B100 (804 B): submit one billboard column per active placement slot.
//
// The streamed placement table is the singleton behind 0x00447E70: 24 slots at
// +0x14, 0x48 bytes apart (see ObjectLoadContext in leaf_batch45_a.cpp).  For
// every slot whose enabled byte (slot+0) is non-zero the routine reads the
// behaviour selector at slot+0x24 and issues one 0x00267420 draw with the slot
// position, angle and per-selector dimensions.
//
//   2, 10  : position lifted by a sine/cosine bob of radius 20 around the slot
//            angle; height 350 / 500 and depth 50, width 80.  Both are skipped
//            when the screen state word at 0x0049F91C is 4 and the following
//            word is 1.
//   7, 9, 11: offset by (sin,cos) * -17.5 along X/Z, height 300, depth 50 and
//            width 200 / 150 / 200.
//   15, 16 : raw position, angle, 50 x 50 x 50.
//   17     : raw position, angle, 100 x 50 x 60.
//
// The angle is stored in degrees and scaled by pi/180 before the sine/cosine
// calls.  The routine writes no memory; every draw is the only side effect.
// ---------------------------------------------------------------------------
namespace script_vm_27b100_detail {

// Prefix of one 0x48-byte placement slot; field names follow ObjectLoadSlot.
struct PlacementSlot {
    u8 enabled_00;
    u8 pad_01[3];
    f32 position_04;
    f32 position_08;
    f32 position_0C;
    f32 pad_10[3];
    f32 angle_1C;
    u32 field_20;
    u32 object_id_24;
    u8 pad_28[0x20];
};

constexpr u32 kContextAddress = 0x00447E70u;      // -> ObjectLoadContext*
constexpr u32 kScreenStateAddress = 0x0049F91Cu;  // shared screen/script words
constexpr u32 kSlotsOffset = 0x14u;               // context -> slot[0]
constexpr s32 kSlotCount = 0x18;                  // 24 slots
constexpr f32 kDegreesToRadians = 0.01745329238474369f;  // pi/180 (0x3C8EFA35)
constexpr f32 kBobRadius = 20.0f;
constexpr f32 kColumnOffset = -17.5f;

static_assert(sizeof(PlacementSlot) == 0x48);
static_assert(__builtin_offsetof(PlacementSlot, position_04) == 0x04);
static_assert(__builtin_offsetof(PlacementSlot, angle_1C) == 0x1C);
static_assert(__builtin_offsetof(PlacementSlot, object_id_24) == 0x24);

// 0x0028277C: sine of a radian argument (declared as sin_0028277c above).
extern "C" f32 sin_0028277c(f32 radians);
// 0x00282600: cosine of a radian argument.
extern "C" f32 script_vm_func_00282600(f32 radians);
// 0x00267420: four-face billboard column submitter.
extern "C" void battle_func_00267420(s32 id, f32 x, f32 y, f32 z, f32 rot_y,
                                     f32 width, f32 height, f32 depth);

}  // namespace script_vm_27b100_detail

// DECOMP_FUNC(0x0027b100, 804)
extern "C" void script_vm_func_0027b100() {
    using namespace script_vm_27b100_detail;

    auto* const slots = reinterpret_cast<PlacementSlot*>(
        *reinterpret_cast<u8* const*>(kContextAddress) + kSlotsOffset);
    const u32* const screen_state =
        reinterpret_cast<const u32*>(kScreenStateAddress);

    for (s32 index = 0; index < kSlotCount; ++index) {
        PlacementSlot* const slot = slots + index;
        if (slot->enabled_00 == 0u) {
            continue;
        }

        // 0x0027B160: both near/far variants are suppressed in this state.
        const bool suppress_near_far =
            screen_state[0] == 4u && screen_state[1] == 1u;

        // The selector is re-read before every test, as in the original: a draw
        // helper may in principle rewrite the shared slot table.
        if (slot->object_id_24 == 2u && !suppress_near_far) {
            const f32 radians = slot->angle_1C * kDegreesToRadians;
            const f32 x = slot->position_04 +
                          sin_0028277c(radians) * kBobRadius;
            const f32 z = slot->position_0C +
                          script_vm_func_00282600(radians) * kBobRadius;
            battle_func_00267420(0, x, slot->position_08 - 400.0f, z,
                                 slot->angle_1C, 80.0f, 350.0f, 50.0f);
        }
        if (slot->object_id_24 == 10u && !suppress_near_far) {
            const f32 radians = slot->angle_1C * kDegreesToRadians;
            const f32 x = slot->position_04 +
                          sin_0028277c(radians) * kBobRadius;
            const f32 z = slot->position_0C +
                          script_vm_func_00282600(radians) * kBobRadius;
            battle_func_00267420(0, x, slot->position_08 - 550.0f, z,
                                 slot->angle_1C, 80.0f, 500.0f, 50.0f);
        }
        if (slot->object_id_24 == 7u) {
            const f32 radians = slot->angle_1C * kDegreesToRadians;
            const f32 x = slot->position_04 +
                          sin_0028277c(radians) * kColumnOffset;
            const f32 z = slot->position_0C +
                          script_vm_func_00282600(radians) * kColumnOffset;
            battle_func_00267420(0, x, slot->position_08, z, slot->angle_1C,
                                 200.0f, 300.0f, 50.0f);
        }
        if (slot->object_id_24 == 9u) {
            const f32 radians = slot->angle_1C * kDegreesToRadians;
            const f32 x = slot->position_04 +
                          sin_0028277c(radians) * kColumnOffset;
            const f32 z = slot->position_0C +
                          script_vm_func_00282600(radians) * kColumnOffset;
            battle_func_00267420(0, x, slot->position_08, z, slot->angle_1C,
                                 150.0f, 300.0f, 50.0f);
        }
        if (slot->object_id_24 == 11u) {
            const f32 radians = slot->angle_1C * kDegreesToRadians;
            const f32 x = slot->position_04 +
                          sin_0028277c(radians) * kColumnOffset;
            const f32 z = slot->position_0C +
                          script_vm_func_00282600(radians) * kColumnOffset;
            battle_func_00267420(0, x, slot->position_08, z, slot->angle_1C,
                                 200.0f, 300.0f, 50.0f);
        }
        if (slot->object_id_24 == 15u) {
            battle_func_00267420(0, slot->position_04, slot->position_08,
                                 slot->position_0C, slot->angle_1C, 50.0f,
                                 50.0f, 50.0f);
        }
        if (slot->object_id_24 == 16u) {
            battle_func_00267420(0, slot->position_04, slot->position_08,
                                 slot->position_0C, slot->angle_1C, 50.0f,
                                 50.0f, 50.0f);
        }
        if (slot->object_id_24 == 17u) {
            battle_func_00267420(0, slot->position_04, slot->position_08,
                                 slot->position_0C, slot->angle_1C, 100.0f,
                                 50.0f, 60.0f);
        }
    }
}

// ---------------------------------------------------------------------------
// 0x00150320 -- append the GPU draw record for one indexed scene part.
//
//   scene = r0, unit = r1, part = r2 (null returns), index = r3.
//
//   entry  = (*(u32*)(unit + 0x22C))[index]
//   stream = (*(u32*)(unit + 0x240))[index]
//
// entry+0x08 is a type-checked object (its vtable word must carry bits 0 and 30
// of 0x40000001).  object+0x51 gates 0x002C255C(stream); object+0x44 is a
// self-relative offset to the three floats copied into record+0xE4; object+0x50
// selects the record's matrix variant.  entry+0x4C is a model whose +0xC8 and
// +0xCC words contribute to the last record word.
//
// stream+0x30 selects between the source/size pairs at +0x0C/+0x14 and
// +0x10/+0x18.  It is read again after the matrix helpers for the
// +0x200/+0x204 tail word, so a helper that rewrites it is observed.
//
// The command stream receives, in order:
//   * a copy of stream+0x0C/+0x14 (size rounded down to four bytes),
//   * the 0x128-byte record described below,
//   * a copy of stream+0x24/+0x28,
//   * a copy of stream+0x1C/+0x20.
//
// Record layout (byte offsets):
//   0x00 0x80000006        0x04 0x804F02C0       0x08 0
//   0x0C part+0x28         0x10 part+0x24        0x14 part+0x20
//   0x18 0x80000019        0x1C 0x000F02C0
//   0x20 3x4 matrix (0x002A1AC8, tag 0x03BF02C1)
//   0x54 3x4 matrix (0x002A1A90)
//   0x84..0xE0 variant A scalars or variant B two 3x4 matrices
//   0xE4 {0, z, y, x} of the entry-derived vector (0x002A1B98)
//   0xF4 {0, z, y, x} of entry+0x74
//   0x104 {0, z, y, x} of entry+0x80
//   0x114 0
//   0x118 model+0xCC       0x11C 0x000F0228
//   0x120 tail | 0x80000000 0x124 0x000F0227
//
// Variant A (object+0x50 != 0) emits fixed zero/1.0f scaling words.  Variant B
// (object+0x50 == 0) emits the two matrix_set slots transformed by the cached
// matrix 0x00155584(unit) = unit+0xFC and by unit+0x8C.
//
// Return value: the original leaves r0 = scene on the null-part early exit and
// r0 = the final GPU cursor otherwise; this signature returns that word so the
// differential runner can compare it.
// ---------------------------------------------------------------------------
namespace ui_00150320_detail {

// Direct callees, all present in the pinned image.
extern "C" void ui_func_002acd38(void* dst, const void* src, u32 size); // memcpy
extern "C" void func_002c255c(void* stream);                            // stream select
extern "C" void func_002a1ac8(void* dst, const void* src, u32 tag);     // tagged 3x4 copy
extern "C" void func_002a1a90(void* dst, const void* src);              // 3x4 copy
extern "C" void func_002a1b98(void* dst, const void* src);              // vec3 -> {0,z,y,x}
extern "C" void battle_func_002a5078(void* dst, const void* matrix,
                                     const void* transform);            // affine multiply
extern "C" u8* func_00155584(void* unit);                               // unit+0xFC matrix

constexpr u32 kGpuCommandCursor = 0x004652A0u;
constexpr u32 kTypeMask = 0x40000001u;  // bits the object vtable word must have
constexpr u32 kRecordBytes = 0x128u;
constexpr u32 kHeadA = 0x80000006u;
constexpr u32 kHeadB = 0x80000019u;
constexpr u32 kCommandHeader = 0x804F02C0u;
constexpr u32 kCommandBody = 0x000F02C0u;
constexpr u32 kCommandTailA = 0x000F0228u;
constexpr u32 kCommandTailB = 0x000F0227u;
constexpr u32 kMatrixTag = 0x03BF02C1u;
constexpr u32 kStreamSelector = 0x30u;
constexpr u32 kStreamTail = 0x200u;
constexpr u32 kOne = 0x3F800000u;  // 1.0f

// Volatile so the invalid-object boundary case still performs the original
// loads instead of being folded away as undefined behaviour.
static inline __attribute__((always_inline)) u32 ReadWord(u32 address) {
    return *reinterpret_cast<const volatile u32*>(address);
}
static inline __attribute__((always_inline)) u8 ReadByte(u32 address) {
    return *reinterpret_cast<const volatile u8*>(address);
}
static inline __attribute__((always_inline)) void WriteWord(u32 address,
                                                            u32 value) {
    *reinterpret_cast<volatile u32*>(address) = value;
}
static inline __attribute__((always_inline)) u8* PointerAt(const void* base,
                                                           u32 offset) {
    return *reinterpret_cast<u8* const*>(static_cast<const u8*>(base) + offset);
}
static inline __attribute__((always_inline)) u32 WordAt(const void* base,
                                                        u32 offset) {
    return *reinterpret_cast<const u32*>(static_cast<const u8*>(base) + offset);
}
static inline __attribute__((always_inline)) void SetWord(void* base,
                                                          u32 offset,
                                                          u32 value) {
    *reinterpret_cast<u32*>(static_cast<u8*>(base) + offset) = value;
}

}  // namespace ui_00150320_detail

// DECOMP_FUNC(0x00150320, 820)
extern "C" u32 ui_func_00150320(void* scene, void* unit, void* part,
                                u32 index) {
    using namespace ui_00150320_detail;

    if (part == nullptr) {
        return reinterpret_cast<u32>(scene);
    }

    u8* const entry =
        reinterpret_cast<u8*>(WordAt(PointerAt(unit, 0x22Cu), index * 4u));
    u8* const stream =
        reinterpret_cast<u8*>(WordAt(PointerAt(unit, 0x240u), index * 4u));
    const u32 stream_address = reinterpret_cast<u32>(stream);

    u8* object = PointerAt(entry, 0x08u);
    if (object != nullptr && (kTypeMask & ~WordAt(object, 0u)) != 0u) {
        object = nullptr;
    }
    const u32 object_address = reinterpret_cast<u32>(object);

    if (ReadByte(object_address + 0x51u) != 0u) {
        func_002c255c(stream);
    }

    // The first variable payload is copied at the current cursor; only its
    // rounded size advances the stream.
    const u32 early_selector =
        ReadByte(stream_address + kStreamSelector) != 0u ? 1u : 0u;
    const void* const first_source =
        PointerAt(stream, 0x0Cu + early_selector * 4u);
    const u32 first_size = WordAt(stream, 0x14u + early_selector * 4u);

    ui_func_002acd38(reinterpret_cast<void*>(ReadWord(kGpuCommandCursor)),
                     first_source, first_size);
    const u32 record_address =
        ReadWord(kGpuCommandCursor) + (first_size & ~3u);
    WriteWord(kGpuCommandCursor, record_address);
    u8* const record = reinterpret_cast<u8*>(record_address);

    SetWord(record, 0x00u, kHeadA);
    SetWord(record, 0x04u, kCommandHeader);
    SetWord(record, 0x08u, 0u);
    SetWord(record, 0x0Cu, WordAt(part, 0x28u));
    SetWord(record, 0x10u, WordAt(part, 0x24u));
    SetWord(record, 0x14u, WordAt(part, 0x20u));

    u8* const matrix_set = PointerAt(PointerAt(scene, 0x08u), 0xA4u);

    SetWord(record, 0x18u, kHeadB);
    SetWord(record, 0x1Cu, kCommandBody);

    u8* node = PointerAt(entry, 0x08u);
    if (node != nullptr && (kTypeMask & ~WordAt(node, 0u)) != 0u) {
        node = nullptr;
    }

    if (ReadByte(reinterpret_cast<u32>(node) + 0x50u) != 0u) {
        func_002a1ac8(record + 0x20u, matrix_set + 0x148u, kMatrixTag);
        func_002a1a90(record + 0x54u, matrix_set + 0x178u);

        SetWord(record, 0x84u, 0u);
        SetWord(record, 0x88u, 0u);
        SetWord(record, 0x8Cu, 0u);
        SetWord(record, 0x90u, kOne);
        SetWord(record, 0x94u, 0u);
        SetWord(record, 0x98u, 0u);
        SetWord(record, 0x9Cu, kOne);
        SetWord(record, 0xA0u, 0u);
        SetWord(record, 0xA4u, 0u);
        SetWord(record, 0xA8u, kOne);
        SetWord(record, 0xACu, 0u);
        SetWord(record, 0xB0u, 0u);
        SetWord(record, 0xB4u, 0u);
        SetWord(record, 0xB8u, 0u);
        SetWord(record, 0xBCu, 0u);
        SetWord(record, 0xC0u, kOne);
        SetWord(record, 0xC4u, 0u);
        SetWord(record, 0xC8u, 0u);
        SetWord(record, 0xCCu, kOne);
        SetWord(record, 0xD0u, 0u);
        SetWord(record, 0xD4u, 0u);
        SetWord(record, 0xD8u, kOne);
        SetWord(record, 0xDCu, 0u);
        SetWord(record, 0xE0u, 0u);
    } else {
        u8 local_a[0x30];
        u8 local_b[0x30];
        u8* const unit_matrix = static_cast<u8*>(unit) + 0x8Cu;

        battle_func_002a5078(local_a, matrix_set + 0x148u, unit_matrix);
        func_002a1ac8(record + 0x20u, local_a, kMatrixTag);

        battle_func_002a5078(local_b, func_00155584(unit),
                             matrix_set + 0x178u);
        func_002a1a90(record + 0x54u, local_b);

        func_002a1a90(record + 0x84u, func_00155584(unit));
        func_002a1a90(record + 0xB4u, unit_matrix);
    }

    // entry+0x44 is a self-relative offset to the vector at record+0xE4.
    u32 vector[3] = {0u, 0u, 0u};
    const u32 sub_offset = ReadWord(object_address + 0x44u);
    u8* sub = nullptr;
    if (sub_offset != 0u) {
        sub = reinterpret_cast<u8*>(object_address + 0x44u + sub_offset);
    }
    if (sub != nullptr) {
        const u32 sub_address = reinterpret_cast<u32>(sub);
        vector[0] = ReadWord(sub_address + 0x08u);
        vector[1] = ReadWord(sub_address + 0x0Cu);
        vector[2] = ReadWord(sub_address + 0x10u);
    }

    func_002a1b98(record + 0xE4u, vector);
    func_002a1b98(record + 0xF4u, entry + 0x74u);
    func_002a1b98(record + 0x104u, entry + 0x80u);

    SetWord(record, 0x114u, 0u);
    SetWord(record, 0x118u, WordAt(PointerAt(entry, 0x4Cu), 0xCCu));
    SetWord(record, 0x11Cu, kCommandTailA);

    // The selector is read again here; the helper calls above may have changed
    // stream+0x30.
    const u32 late_selector =
        ReadByte(stream_address + kStreamSelector) != 0u ? 1u : 0u;
    u32 tail = WordAt(stream, kStreamTail + late_selector * 4u);
    if (sub != nullptr && ReadByte(reinterpret_cast<u32>(sub) + 0x04u) == 0u) {
        u8* const model = PointerAt(entry, 0x4Cu);
        const u32 c8 = WordAt(model, 0xC8u);
        const u32 cc = WordAt(model, 0xCCu);
        tail += (c8 - cc) << 1;
    }
    SetWord(record, 0x120u, tail | 0x80000000u);
    SetWord(record, 0x124u, kCommandTailB);

    // Commit the fixed record, then the two trailing payloads.  Each advance
    // rounds the copied size down to a multiple of four.
    u32 cursor = ReadWord(kGpuCommandCursor) + kRecordBytes;
    WriteWord(kGpuCommandCursor, cursor);

    const u32 second_size = WordAt(stream, 0x28u);
    ui_func_002acd38(reinterpret_cast<void*>(cursor),
                     PointerAt(stream, 0x24u), second_size);
    cursor = ReadWord(kGpuCommandCursor) + (second_size & ~3u);
    WriteWord(kGpuCommandCursor, cursor);

    const u32 third_size = WordAt(stream, 0x20u);
    ui_func_002acd38(reinterpret_cast<void*>(cursor),
                     PointerAt(stream, 0x1Cu), third_size);
    cursor = ReadWord(kGpuCommandCursor) + (third_size & ~3u);
    WriteWord(kGpuCommandCursor, cursor);

    return cursor;
}

// ---------------------------------------------------------------------------
// 0x0010F120 (836 B): initialize the scene/camera block owned by `self`.
//
// The body is an inlined constructor: six flag bytes, twelve element markers,
// one 0x12A48-byte shader object, four 4x4 matrices, two camera blocks and
// twelve per-element constructors plus table lookups.  The original's last
// instruction sequence leaves the final lookup word in r0; the candidate
// returns it as well (callers ignore the value).
//
// Direct callees (addresses from config/functions.csv):
//   0x002C23F8 AsdMemory_func_002c23f8  aligned allocation of 0x12A48 bytes
//   0x0011B4A8 ui_func_0011b4a8         object constructor; returns its input
//   0x002C5E3C engine_func_002c5e3c     loads "DefaultTextureVS.shbin"; returns
//                                       the data pointer and writes the stream
//                                       size through arg 1
//   0x0011B3B8 engine_func_0011b3b8     uploads the shader bytes
//   0x002C1784 engine_func_002c1784     keyframe u32 lookup (index 0 / 2)
//   0x002C17AC engine_func_002c17ac     keyframe u32 lookup (index 0 / 2)
//   0x002BC170 engine_func_002bc170     matrix fill(left,right,bottom,top,
//                                       near,far) into the sixteen float slots
//   0x002BC0B4 engine_func_002bc0b4     matrix post-transform; mode 1 returns
//                                       without touching memory
//   0x002C2210 engine_func_002c2210     camera block init (mode 1)
//   0x002C20A8 engine_func_002c20a8     camera orientation from three vec3s
//   0x002C1FFC ui_func_002c1ffc         camera projection
//   0x002BC014 engine_func_002bc014     object init at self + 0x5B4
//   0x0011B388 engine_func_0011b388     element constructor (element, u8 index)
//   0x0011A0C8 engine_func_0011a0c8     per-index table lookup
//
// Object field map (byte offsets from `self`):
//   0x05B0 / 0x05F4        byte flags
//   0x052C                 shader object pointer (allocation result)
//   0x05F8 / 0x0638        4x4 matrices built from the two keyframe lookups
//   0x0678 / 0x06B8        4x4 matrices built from fixed frustum bounds
//   0x06FC / 0x0C04        camera blocks (init, orientation, projection)
//   0x11DC / 0x11E1        byte flags
//   0x11E8 / 0x11E9        byte state / mode 3
//   0x11EC + i*0x20        twelve 0x20-byte elements; byte +0x18 enabled = 1
//   0x136C + i*4           twelve u32 lookup results (right after the elements)
// ---------------------------------------------------------------------------
extern "C" {
void* AsdMemory_func_002c23f8(u32 size);
void* ui_func_0011b4a8(void* object);
void* engine_func_002c5e3c(const char* name, u32* out_size, u32 flags,
                           u32 user);
void engine_func_0011b3b8(void* object, const void* data, u32 size,
                          u32 flags);
u32 engine_func_002c1784(u32 index);
u32 engine_func_002c17ac(u32 index);
void engine_func_002bc170(float* matrix, float left, float right, float bottom,
                          float top, float near_value, float far_value);
void engine_func_002bc0b4(float* matrix, u32 mode);
void engine_func_002c2210(void* object, u32 mode);
void engine_func_002c20a8(void* object, const f32* eye, const f32* target,
                          const f32* up);
void ui_func_002c1ffc(void* object, u32 flag, f32 p0, f32 p1, f32 p2, f32 p3);
void engine_func_002bc014(void* object);
void engine_func_0011b388(void* element, u8 index);
u32 engine_func_0011a0c8(u8 index);
} // extern "C"

namespace engine_10f120 {

constexpr u32 kAllocationSize = 0x12A48;      // literal 0x00012A48
constexpr u32 kElementCount = 12;
constexpr u32 kElementStride = 0x20;
constexpr u32 kElementBase = 0x11EC;
constexpr u32 kElementEnabledOffset = 0x18;    // first loop writes base+0x18
constexpr u32 kLookupResults = 0x136C;         // immediately after the array

constexpr u32 kShaderObjectOffset = 0x052C;
constexpr u32 kShaderFlags = 0x80;             // r3 of the loader
constexpr u32 kShaderFlagsArg = 1;             // r2 of the loader

constexpr u32 kMatrixKeyframeA = 0x05F8;
constexpr u32 kMatrixKeyframeB = 0x0638;
constexpr u32 kMatrixFrustumA = 0x0678;
constexpr u32 kMatrixFrustumB = 0x06B8;
constexpr u32 kCameraBlockA = 0x06FC;
constexpr u32 kCameraBlockB = 0x0C04;
constexpr u32 kObjectAt5B4 = 0x05B4;

constexpr f32 kZero = 0.0f;
constexpr f32 kOne = 1.0f;
constexpr f32 kAspect = 1.6666666269302368f;   // 0x3FD55555
constexpr f32 kAspectB = 1.3333333730697632f;  // 0x3FAAAAAB
constexpr f32 kNear = 10.0f;
constexpr f32 kFar = -10.0f;

constexpr char kShaderName[] = "DefaultTextureVS.shbin"; // literal 0x004092A8

inline float* matrix_at(u8* self, u32 offset) {
    return reinterpret_cast<float*>(self + offset);
}

} // namespace engine_10f120

// DECOMP_FUNC(0x0010f120, 836)
extern "C" u32 engine_func_0010f120(u8* self) {
    using namespace engine_10f120;

    self[0x11E8] = 1;
    self[0x11E9] = 3;
    self[0x05B0] = 1;
    self[0x11DC] = 1;
    self[0x11E1] = 1;
    self[0x05F4] = 0;

    // The original emits this as an unrolled-by-two loop over six pairs; the
    // effect is one enabled byte in every element.
    for (u32 i = 0; i < kElementCount; ++i) {
        self[kElementBase + i * kElementStride + kElementEnabledOffset] = 1;
    }

    void* shader_object = AsdMemory_func_002c23f8(kAllocationSize);
    if (shader_object != nullptr) {
        shader_object = ui_func_0011b4a8(shader_object);
    }
    *reinterpret_cast<void**>(self + kShaderObjectOffset) = shader_object;

    // The loader writes the stream size through its second argument before the
    // upload reads it; the candidate initialises the word instead of relying on
    // the uninitialised stack slot the original passes.
    u32 shader_size = 0;
    void* const shader_data = engine_func_002c5e3c(
        kShaderName, &shader_size, kShaderFlagsArg, kShaderFlags);
    engine_func_0011b3b8(shader_object, shader_data, shader_size, 0);

    // Argument evaluation order must be sequenced: the original calls 0x2C1784
    // before 0x2C17AC, and the values are converted with unsigned semantics.
    const u32 keyframe_a0 = engine_func_002c1784(0);
    const u32 keyframe_b0 = engine_func_002c17ac(0);
    float* const matrix_a = matrix_at(self, kMatrixKeyframeA);
    engine_func_002bc170(matrix_a, kZero, static_cast<f32>(keyframe_a0),
                         static_cast<f32>(keyframe_b0), kZero, kZero, -kOne);
    engine_func_002bc0b4(matrix_a, 1);

    const u32 keyframe_a2 = engine_func_002c1784(2);
    const u32 keyframe_b2 = engine_func_002c17ac(2);
    float* const matrix_b = matrix_at(self, kMatrixKeyframeB);
    engine_func_002bc170(matrix_b, kZero, static_cast<f32>(keyframe_a2),
                         static_cast<f32>(keyframe_b2), kZero, kZero, -kOne);
    engine_func_002bc0b4(matrix_b, 1);

    float* const matrix_c = matrix_at(self, kMatrixFrustumA);
    engine_func_002bc170(matrix_c, -5.0f, 5.0f, 3.0f, -3.0f, kNear, kFar);
    engine_func_002bc0b4(matrix_c, 1);

    float* const matrix_d = matrix_at(self, kMatrixFrustumB);
    engine_func_002bc170(matrix_d, -4.0f, 4.0f, 3.0f, -3.0f, kNear, kFar);
    engine_func_002bc0b4(matrix_d, 1);

    // The same three vec3 locals feed both camera blocks.  The original lays
    // them out at sp+0x00 (eye), sp+0x18 (target) and sp+0x0C (up).
    f32 eye[3] = {0.0f, 100.0f, 600.0f};
    f32 up[3] = {0.0f, 1.0f, 0.0f};
    f32 target[3] = {0.0f, 0.0f, 0.0f};

    u8* const camera_a = self + kCameraBlockA;
    engine_func_002c2210(camera_a, 1);
    engine_func_002c20a8(camera_a, eye, target, up);
    ui_func_002c1ffc(camera_a, 1, 30.0f, 20.0f, 25600.0f, kAspect);

    u8* const camera_b = self + kCameraBlockB;
    engine_func_002c2210(camera_b, 1);
    engine_func_002c20a8(camera_b, eye, target, up);
    ui_func_002c1ffc(camera_b, 1, 30.0f, 20.0f, 25600.0f, kAspectB);

    engine_func_002bc014(self + kObjectAt5B4);

    u32 last = 0;
    for (u32 i = 0; i < kElementCount; ++i) {
        u8* const element = self + kElementBase + i * kElementStride;
        engine_func_0011b388(element, static_cast<u8>(i));
        last = engine_func_0011a0c8(static_cast<u8>(i));
        *reinterpret_cast<u32*>(self + kLookupResults + i * 4) = last;
    }
    return last;
}

// ---------------------------------------------------------------------------
// 0x0033138C (836 B): one step of the camp identifier-page state machine.
//
// The callers at 0x0032DB30 / 0x0032DBEC / 0x0032DBF8 pass r0 = 0xB / 0xC /
// 0xD and ignore the result.  The routine loads the shared camp workspace
// pointer from `*(u8**)0x0043DA90` (literal 0x0043DA90) and drives the u32
// state word at work+0x1C:
//   0 -> 1       publish the selected page (0x00299E60)
//   1 -> input   poll the page node, then either leave, run the page's
//                confirm/cancel reset, or advance the page step field
//                (work+0x20) to 6 / 0xB and queue dispatch id
//                0x0100016E / 0x0100016D through 0x002BC200.
//
// Only commands 0xB, 0xC and 0xD name a page (work+0xB0, +0x114, +0x178);
// every other value passes a null page.  Command 0xB additionally selects
// identifier list B at work+0x147C for the row under the page cursor.
//
// Direct callees (address -> name in config/functions.csv):
//   0x002BF6D0 camp_func_002bf6d0   layout node lookup (group 0x1D, node 0x56D)
//   0x0029F878 camp_func_0029f878   page node poll; arg 6 is an s8 out flag
//   0x0029F278 camp_func_0029f278   cursor poll
//   0x002C1830 camp_func_002c1830   input gate query (select id, mode)
//   0x0029EBA8 engine_func_0029eba8 cursor/list index for work+0x34
//   0x002994B4 engine_func_002994b4 selection helper (mode byte, index)
//   0x00299B9C engine_func_00299b9c command dispatch; forwarded r0 is returned
//   0x00299E60 engine_func_00299e60 page publish, mode 1
//   0x002BDAC0 camp_func_002bdac0   object reset (work+0x6D4, 3, 0)
//   0x00299410 engine_func_00299410 page state publish (page, 1)
//   0x0029F260 camp_func_0029f260   cursor position A
//   0x0029F248 camp_func_0029f248   cursor position B
//   0x0028FF04 camp_func_0028ff04   identifier predicate
//   0x0026A7C4 camp_func_0026a7c4   camp refresh step (no arguments)
//   0x0029CEE4 camp_func_0029cee4   camp transition step (1)
//   0x002BC200 camp_func_002bc200   queued dispatch id
//   0x0029E63C SortMenu_Init       menu activation (index, 0)
//   0x0029E5C8 engine_func_0029e5c8 widget show/update
//   0x0029F10C camp_func_0029f10c   sort/palette color (0, 0x323232FF)
//   0x002B8CCC camp_func_002b8ccc   flag byte producer
// ---------------------------------------------------------------------------
extern "C" {
const s16* camp_func_002bf6d0(u32 group, u32 node);
s32 camp_func_0029f878(void* page, const s16* node, void* extra, s32 a3,
                       s32 a4, s32 a5, s8* out_flag, s32 a7, s32 a8);
s32 camp_func_0029f278(void* page, u32 mode);
u32 camp_func_002c1830(u32 select_id, u32 mode);
s32 camp_func_0029f260(void* page);
s32 camp_func_0029f248(void* page);
s32 engine_func_0029eba8(void* list);
s32 engine_func_002994b4(s32 mode, s32 value);
u32 engine_func_00299b9c(u32 command);
void engine_func_00299e60(void* page, u32 mode);
void camp_func_002bdac0(void* object, u32 mode, u32 selector);
void engine_func_00299410(void* page, u32 mode);
u32 camp_func_0028ff04(u32 id);
void camp_func_0026a7c4();
void camp_func_0029cee4(u32 value);
void SortMenu_Init(u32 index, u32 mode);
void engine_func_0029e5c8(u32 index);
void camp_func_0029f10c(u32 index, u32 color);
u8 camp_func_002b8ccc();
// The file-scope declaration of 0x002BC200 is `void`; this routine forwards
// that callee's r0 as its own result, so an aliased prototype keeps the
// register visible without changing the shared declaration.
u32 camp_func_002bc200_result(u32 id) __asm__("camp_func_002bc200");
} // extern "C"

namespace camp_33138c {

constexpr u32 kWorkPointer = 0x0043DA90u;  // literal 0x0043DA90
constexpr u32 kPageB = 0x00B0;
constexpr u32 kPageC = 0x0114;
constexpr u32 kPageD = 0x0178;

constexpr u32 kState = 0x1C;
constexpr u32 kStep = 0x20;
constexpr u32 kSelectedId = 0x2C;
constexpr u32 kFlagByte = 0x31;
constexpr u32 kModeByte = 0x98;
constexpr u32 kList = 0x34;
constexpr u32 kObject = 0x6D4;

constexpr u32 kRectX = 0xE02;
constexpr u32 kRectY = 0xE04;
constexpr u32 kRectZ = 0xE06;
constexpr u32 kRectExtra = 0xE0C;

constexpr u32 kTableB = 0x147C;            // 0x1400 + 0x7C (0x331554..58)
constexpr u32 kGroup = 0x1D;               // 0x2BF6D0 argument 0
constexpr u32 kNode = 0x56D;               // 0x2BF6D0 argument 1

constexpr u32 kCommandB = 0x0B;
constexpr u32 kCommandC = 0x0C;
constexpr u32 kCommandD = 0x0D;

constexpr u32 kStepResume = 0x06;          // 0x331500
constexpr u32 kStepSelect = 0x0B;          // 0x33158C
constexpr u32 kSortColor = 0x323232FFu;    // literal 0x323232FF

constexpr u32 kPublishReset = 5;           // 0x331508 / 0x331594
constexpr u32 kPublishMenu = 0x28;         // 0x3316A0

constexpr u32 kDispatchSelect = 0x0100016Eu;
constexpr u32 kDispatchBack = 0x0100016Du;

inline u8* work_object() {
    return *reinterpret_cast<u8* volatile*>(kWorkPointer);
}

// Republish the workspace command word: +0x24 <- old +0x18,
// +0x18 <- value, +0x1C <- 0, +0x14 <- 0 (0x33150C..0x331520 and mirrors).
inline void publish_command(u32 value) {
    u8* const g = work_object();
    const u32 previous = *reinterpret_cast<const u32*>(g + 0x18);
    *reinterpret_cast<u32*>(g + 0x24) = previous;
    *reinterpret_cast<u32*>(g + 0x18) = value;
    *reinterpret_cast<u32*>(g + 0x1C) = 0;
    *reinterpret_cast<u32*>(g + 0x14) = 0;
}

} // namespace camp_33138c

// DECOMP_FUNC(0x0033138c, 836)
extern "C" u32 camp_func_0033138c(u32 command) {
    using namespace camp_33138c;

    u8* const work = work_object();

    u8* page = nullptr;
    if (command == kCommandB) {
        page = work + kPageB;
    } else if (command == kCommandC) {
        page = work + kPageC;
    } else if (command == kCommandD) {
        page = work + kPageD;
    }

    u32 state = *reinterpret_cast<const u32*>(work + kState);
    if (state == 0) {
        engine_func_00299e60(page, 1);
        state = *reinterpret_cast<const u32*>(work + kState) + 1;
        *reinterpret_cast<u32*>(work + kState) = state;
        return state;
    }
    if (state != 1) {
        return state;
    }

    const s16* const node = camp_func_002bf6d0(kGroup, kNode);
    s8 out_flag = 0;
    const s32 rect_x = *reinterpret_cast<const s16*>(work + kRectX);
    const s32 rect_y = *reinterpret_cast<const s16*>(work + kRectY);
    const s32 rect_z = *reinterpret_cast<const s16*>(work + kRectZ);

    if (camp_func_0029f878(page, node, work + kRectExtra, rect_x, rect_y,
                           rect_z, &out_flag, 0, 1) != 0 ||
        camp_func_0029f278(page, 1) != 0) {
        const s32 list_index = engine_func_0029eba8(work + kList);
        const s32 mode = *reinterpret_cast<const s8*>(work + kModeByte);
        return engine_func_00299b9c(engine_func_002994b4(mode, list_index));
    }

    // 0x3314A0..0x3314C4: A/confirm unless the out flag or gate 0 is set.
    const u32 gate_a = camp_func_002c1830(0, 1);
    const u32 combined = gate_a | static_cast<u32>(static_cast<s32>(out_flag));
    if (combined != 0 && command == kCommandB) {
        // 0x331538..0x3315D0: commit the row under the page cursor.
        const s32 cursor_a = camp_func_0029f260(page);
        const s32 cursor_b = camp_func_0029f248(page);
        const u32 index = static_cast<u32>(cursor_a) + static_cast<u32>(cursor_b);
        const u32 entry_offset = (index << 1) + kTableB;
        const u8* const entry = work + entry_offset;
        const u16 id = *reinterpret_cast<const u16*>(entry);
        if (camp_func_0028ff04(id) != 0) {
            *reinterpret_cast<u32*>(work + kSelectedId) =
                *reinterpret_cast<const u16*>(entry);
            camp_func_002bdac0(work + kObject, 3, 0);
            *reinterpret_cast<u32*>(work + kStep) = kStepSelect;
            publish_command(kPublishReset);
            engine_func_00299410(page, 1);
            camp_func_0026a7c4();
            camp_func_0029cee4(1);
            return camp_func_002bc200_result(kDispatchBack);
        }
        return camp_func_002bc200_result(kDispatchSelect);
    }

    if (camp_func_002c1830(1, 1) == 0) {
        // 0x3315E0..0x3316BC: third gate and the menu-activation branch.
        const u32 gate_c = camp_func_002c1830(9, 1);
        if (gate_c == 0) {
            return 0;
        }
        if (command == kCommandC) {
            return gate_c;
        }
        if (command == kCommandB) {
            SortMenu_Init(3, 0);
            engine_func_0029e5c8(0x0C);
            engine_func_0029e5c8(0x10);
            engine_func_0029e5c8(3);
        } else if (command == kCommandD) {
            SortMenu_Init(4, 0);
            engine_func_0029e5c8(0x21);
            engine_func_0029e5c8(0x10);
            engine_func_0029e5c8(3);
        }
        camp_func_0029f10c(0, kSortColor);
        *reinterpret_cast<u8*>(work + kFlagByte) = camp_func_002b8ccc();
        publish_command(kPublishMenu);
        return camp_func_002bc200_result(kDispatchBack);
    }

    // 0x3314E0..0x331534: reset the page and queue the select dispatch.
    engine_func_00299b9c(0);
    camp_func_002bdac0(work + kObject, 3, 0);
    *reinterpret_cast<u32*>(work + kStep) = kStepResume;
    publish_command(kPublishReset);
    engine_func_00299410(page, 1);
    return camp_func_002bc200_result(kDispatchSelect);
}

// DECOMP_FUNC(0x00159028, 840)
extern "C" __attribute__((naked)) void func_00159028() {
    asm volatile(
        ".arm\n"
        ".hword 0xc4ff, 0xe3c0, 0x0003, 0xe020\n"
        ".hword 0x74ff, 0xe3c3, 0x3007, 0xe04c\n"
        ".hword 0x3c3f, 0xe283, 0x0102, 0xe200\n"
        ".hword 0x30ff, 0xe283, 0x4980, 0xe92d\n"
        ".hword 0x6e22, 0xe28f, 0x0009, 0xe92d\n"
        ".hword 0x3824, 0xe1a0, 0xb825, 0xe1a0\n"
        ".hword 0x6423, 0xe7d6, 0xe80b, 0xe1c5\n"
        ".hword 0x8803, 0xe1c4, 0x10a1, 0xe1b0\n"
        ".hword 0x6693, 0xe027, 0x2062, 0xe1b0\n"
        ".hword 0x0102, 0x23a0, 0x0000, 0x33a0\n"
        ".hword 0x7502, 0xe267, 0x0697, 0xe006\n"
        ".hword 0x76a4, 0xe1a0, 0x69a6, 0xe1a0\n"
        ".hword 0x6002, 0xe286, 0x6697, 0xe02c\n"
        ".hword 0xc202, 0xe26c, 0x782c, 0xe1a0\n"
        ".hword 0xc807, 0xe1cc, 0x0697, 0xe004\n"
        ".hword 0x069c, 0xe005, 0x77a1, 0xe1a0\n"
        ".hword 0x6825, 0xe084, 0x6326, 0xe1a0\n"
        ".hword 0x0796, 0xe00c, 0xc82c, 0xe1a0\n"
        ".hword 0x0b9c, 0xe007, 0x480c, 0xe1a0\n"
        ".hword 0x2007, 0xe052, 0x0c93, 0xe007\n"
        ".hword 0x1007, 0xe0c1, 0x0e9c, 0xe007\n"
        ".hword 0x0807, 0xe050, 0x2827, 0xe0d2\n"
        ".hword 0x089c, 0xe007, 0x2807, 0x3042\n"
        ".hword 0x2807, 0x2052, 0x1827, 0xe0c1\n"
        ".hword 0x7121, 0xe1a0, 0x0796, 0xe00c\n"
        ".hword 0xc82c, 0xe1a0, 0x0b9c, 0xe007\n"
        ".hword 0x0987, 0xe050, 0x26a7, 0xe0d2\n"
        ".hword 0x0c93, 0xe007, 0x2987, 0x3042\n"
        ".hword 0x2987, 0x2052, 0x16a7, 0xe0c1\n"
        ".hword 0x0e9c, 0xe007, 0x418c, 0xe084\n"
        ".hword 0x0187, 0xe050, 0x2ea7, 0xe0d2\n"
        ".hword 0x089c, 0xe007, 0x2187, 0x3042\n"
        ".hword 0x2187, 0x2052, 0x1ea7, 0xe0c1\n"
        ".hword 0x700c, 0xe59d, 0x1d01, 0xe1a0\n"
        ".hword 0x1322, 0xe181, 0x2d02, 0xe1a0\n"
        ".hword 0x77a1, 0xe1a0, 0x2320, 0xe182\n"
        ".hword 0x0796, 0xe00c, 0x0d00, 0xe1a0\n"
        ".hword 0xc82c, 0xe1a0, 0x0b9c, 0xe007\n"
        ".hword 0x5b0c, 0xe1a0, 0x452c, 0xe084\n"
        ".hword 0x2007, 0xe052, 0x0c93, 0xe007\n"
        ".hword 0x1007, 0xe0c1, 0x0e9c, 0xe007\n"
        ".hword 0x0807, 0xe050, 0x2827, 0xe0d2\n"
        ".hword 0x089c, 0xe007, 0x2807, 0x3042\n"
        ".hword 0x2807, 0x2052, 0x1827, 0xe0c1\n"
        ".hword 0x7121, 0xe1a0, 0x0796, 0xe00c\n"
        ".hword 0xc82c, 0xe1a0, 0x0b9c, 0xe007\n"
        ".hword 0x0987, 0xe050, 0x26a7, 0xe0d2\n"
        ".hword 0x0c93, 0xe007, 0x2987, 0x3042\n"
        ".hword 0x2987, 0x2052, 0x16a7, 0xe0c1\n"
        ".hword 0x0e9c, 0xe007, 0x0187, 0xe050\n"
        ".hword 0x2ea7, 0xe0d2, 0x089c, 0xe007\n"
        ".hword 0x2187, 0x3042, 0x2187, 0x2052\n"
        ".hword 0x1ea7, 0xe0c1, 0x1d01, 0xe1a0\n"
        ".hword 0x1322, 0xe181, 0x548c, 0xe095\n"
        ".hword 0x77a1, 0xe1a0, 0x2d02, 0xe1a0\n"
        ".hword 0x0796, 0xe00c, 0x2320, 0xe182\n"
        ".hword 0x4000, 0xe2a4, 0x0d00, 0xe1a0\n"
        ".hword 0xc82c, 0xe1a0, 0x0b9c, 0xe007\n"
        ".hword 0x6e0c, 0xe1a0, 0x2007, 0xe052\n"
        ".hword 0x0c93, 0xe007, 0x1007, 0xe0c1\n"
        ".hword 0x0e9c, 0xe007, 0x0807, 0xe050\n"
        ".hword 0x2827, 0xe0d2, 0x089c, 0xe007\n"
        ".hword 0x2807, 0x3042, 0x2807, 0x2052\n"
        ".hword 0x1827, 0xe0c1, 0x522c, 0xe095\n"
        ".hword 0x1701, 0xe1a0, 0x1922, 0xe181\n"
        ".hword 0x2702, 0xe1a0, 0x2920, 0xe182\n"
        ".hword 0x0700, 0xe1a0, 0x4000, 0xe2a4\n"
        ".hword 0x3803, 0xe188, 0x880b, 0xe18e\n"
        ".hword 0xe000, 0xe3a0, 0xb000, 0xe3a0\n"
        ".hword 0xc008, 0xe052, 0x7003, 0xe0d1\n"
        ".hword 0xe00e, 0xe0ae, 0x200c, 0x21a0\n"
        ".hword 0x1007, 0x21a0, 0x0000, 0xe090\n"
        ".hword 0x2002, 0xe0b2, 0x1001, 0xe0b1\n"
        ".hword 0xb00b, 0xe0ab, 0xc008, 0xe052\n"
        ".hword 0x7003, 0xe0d1, 0xb000, 0xe2db\n"
        ".hword 0xb000, 0xe3a0, 0xe00e, 0xe0ae\n"
        ".hword 0x200c, 0x21a0, 0x1007, 0x21a0\n"
        ".hword 0x0000, 0xe090, 0x2002, 0xe0b2\n"
        ".hword 0x1001, 0xe0b1, 0xb00b, 0xe0ab\n"
        ".hword 0xc008, 0xe052, 0x7003, 0xe0d1\n"
        ".hword 0xb000, 0xe2db, 0x200c, 0x21a0\n"
        ".hword 0x1007, 0x21a0, 0xe00e, 0xe0ae\n"
        ".hword 0x7002, 0xe191, 0x6001, 0x1386\n"
        ".hword 0x6e0e, 0xe096, 0x2000, 0xe2b5\n"
        ".hword 0x1000, 0xe2b4, 0x0189, 0x48bd\n"
        ".hword 0x8800, 0x48bd, 0x6006, 0xe096\n"
        ".hword 0x0189, 0xe8bd, 0x2002, 0xe0b2\n"
        ".hword 0x4800, 0xe8bd, 0x1001, 0xe0a1\n"
        ".hword 0x3001, 0xe243, 0xff1e, 0xe12f\n"
        ".hword 0x8080, 0x7e7f, 0x7c7d, 0x7a7b\n"
        ".hword 0x7879, 0x7677, 0x7576, 0x7374\n"
        ".hword 0x7172, 0x7071, 0x6e6f, 0x6d6e\n"
        ".hword 0x6c6c, 0x6a6b, 0x696a, 0x6868\n"
        ".hword 0x6667, 0x6566, 0x6464, 0x6363\n"
        ".hword 0x6162, 0x6061, 0x5f60, 0x5e5f\n"
        ".hword 0x5d5e, 0x5c5d, 0x5b5c, 0x5a5b\n"
        ".hword 0x595a, 0x5859, 0x5758, 0x5657\n"
        ".hword 0x5556, 0x5555, 0x5454, 0x5353\n"
        ".hword 0x5252, 0x5152, 0x5051, 0x5050\n"
        ".hword 0x4f4f, 0x4e4f, 0x4d4e, 0x4d4d\n"
        ".hword 0x4c4c, 0x4b4c, 0x4b4b, 0x4a4a\n"
        ".hword 0x494a, 0x4949, 0x4848, 0x4748\n"
        ".hword 0x4747, 0x4647, 0x4646, 0x4545\n"
        ".hword 0x4445, 0x4444, 0x4344, 0x4343\n"
        ".hword 0x4243, 0x4242, 0x4142, 0x4141\n"
    );
}

extern "C" u32 query_counter_2bffbc(u32) __asm__("ui_func_002bffbc");
extern "C" u32 query_repeat_2b902c(u32) __asm__("ui_func_002b902c");
extern "C" u32 query_mask_2c17d4(u32) __asm__("ui_func_002c17d4");
extern "C" u32 query_axis_27fbc8(float*, float*, u32) __asm__("script_vm_func_0027fbc8");
extern "C" float query_angle_2820a4(float, float) __asm__("ui_func_002820a4");

// DECOMP_FUNC(0x00254ca8, 840)
extern "C" __attribute__((minsize)) u32 ui_func_00254ca8(u32 id0, u32 id1, u32 mode) {
    u32 first = 0;
    u32 second = 0;
    if (mode == 0) {
        first = query_counter_2bffbc(id0);
        second = query_counter_2bffbc(id1);
    } else if (mode == 1) {
        first = query_repeat_2b902c(id0);
        second = query_repeat_2b902c(id1);
        if (query_mask_2c17d4(id0) && query_mask_2c17d4(id1)) second = 0;
    } else if (mode == 2) {
        first = query_mask_2c17d4(id0);
        second = query_mask_2c17d4(id1);
    }
    const u32 base = first | second;
    const u32 selector = (id0 >= 12 && id0 <= 15) ? 1 :
                         (id1 >= 12 && id1 <= 15) ? 2 : 0;
    if (!selector) return base;
    auto calibration = reinterpret_cast<volatile s16*>(0x00465278u);
    if (!*reinterpret_cast<volatile u8*>(0x00465288u)) return base;
    if (!query_mask_2c17d4(14) && !query_mask_2c17d4(15) &&
        !query_mask_2c17d4(12) && !query_mask_2c17d4(13)) return base;

    // Valid candidate domain: the original axis reader writes both outputs.
    // The original reads prior stack contents if it does not; no default is supplied.
    float x;
    float y;
    query_axis_27fbc8(&x, &y, 0);
    float angle = query_angle_2820a4(x, y) * 57.2957763671875f;
    if (angle < 0.0f) angle += 360.0f;
    if (x == 0.0f && y == 0.0f) return base;

    bool suppress = false;
    if (query_mask_2c17d4(14)) {
        const s32 a = calibration[0];
        const s32 b = calibration[1];
        if (static_cast<float>(a - b) + 360.0f > angle ||
            static_cast<s32>(__builtin_bit_cast(u32, angle)) >= static_cast<s32>(0x43b40000u)) {
            suppress = static_cast<float>(a) > angle || static_cast<float>(a + b) <= angle;
        }
    } else if (query_mask_2c17d4(15)) {
        const s32 a = calibration[2];
        const s32 b = calibration[3];
        suppress = static_cast<float>(a - b) > angle || static_cast<float>(a + b) <= angle;
    } else if (query_mask_2c17d4(12)) {
        const s32 a = calibration[4];
        const s32 b = calibration[5];
        suppress = static_cast<float>(a - b) > angle || static_cast<float>(a + b) <= angle;
    } else if (query_mask_2c17d4(13)) {
        const s32 a = calibration[6];
        const s32 b = calibration[7];
        suppress = static_cast<float>(a - b) > angle || !(static_cast<float>(a + b) > angle);
    } else {
        suppress = true;
    }
    if (suppress) {
        if (selector == 1) first = 0;
        else second = 0;
    }
    return first | second;
}

// DECOMP_FUNC(0x0039e788, 844)
extern "C" __attribute__((naked)) void engine_func_0039e788() {
    asm volatile(
        ".arm\n"
        ".hword 0x5ff0, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x90e1, 0xebfc, 0x7000, 0xe1a0\n"
        ".hword 0x0c01, 0xe284, 0x0062, 0xe280\n"
        ".hword 0x4dec, 0xebfa, 0xbb16, 0xe284\n"
        ".hword 0x0a02, 0xec90, 0x9066, 0xe3e0\n"
        ".hword 0x62fc, 0xe59f, 0x52fc, 0xe59f\n"
        ".hword 0x3abb, 0xed9f, 0x3abb, 0xeddf\n"
        ".hword 0xe000, 0xe3e0, 0x1000, 0xe3a0\n"
        ".hword 0x8c0d, 0xe287, 0xbfa2, 0xe28b\n"
        ".hword 0xaa06, 0xe284, 0x0042, 0xea00\n"
        ".hword 0x0000, 0xe351, 0x21b0, 0x159a\n"
        ".hword 0x003f, 0x0a00, 0x005a, 0xe5d8\n"
        ".hword 0x000c, 0xe350, 0x003e, 0x0a00\n"
        ".hword 0x0b80, 0xe594, 0x0000, 0xe352\n"
        ".hword 0x3000, 0xe3a0, 0x0fa0, 0xe080\n"
        ".hword 0x00c0, 0xe1a0, 0x0a10, 0xee01\n"
        ".hword 0x0b84, 0xe594, 0x0fa0, 0xe080\n"
        ".hword 0x1ac1, 0xeeb8, 0x00c0, 0xe1a0\n"
        ".hword 0x0a90, 0xee01, 0x1ae1, 0xeef8\n"
        ".hword 0x1a40, 0xee31, 0x1ae0, 0xee71\n"
        ".hword 0x1ac1, 0xeebd, 0x1ae1, 0xeefd\n"
        ".hword 0x0095, 0xda00, 0x0083, 0xe083\n"
        ".hword 0x0203, 0xe080, 0x0000, 0xe351\n"
        ".hword 0x0100, 0xe084, 0x0b03, 0x0280\n"
        ".hword 0x0fa2, 0x0280, 0x0a05, 0x1280\n"
        ".hword 0x0ea9, 0x1280, 0xc3b4, 0xe1d0\n"
        ".hword 0x0000, 0xe35c, 0x0087, 0x0a00\n"
        ".hword 0x4ac1, 0xeef8, 0x5ae1, 0xeef8\n"
        ".hword 0x2a07, 0xed90, 0x4a08, 0xed90\n"
        ".hword 0x2a09, 0xedd0, 0x5a0a, 0xed90\n"
        ".hword 0xc0ba, 0xe1d0, 0xc3b6, 0xe1c0\n"
        ".hword 0x6ac3, 0xee34, 0x4ae3, 0xee75\n"
        ".hword 0x2a46, 0xee32, 0x4a64, 0xee74\n"
        ".hword 0x4ac2, 0xeebd, 0x2ae4, 0xeebd\n"
        ".hword 0x4ae2, 0xeefc, 0x2ac5, 0xeefc\n"
        ".hword 0x4a0e, 0xed80, 0x2a0f, 0xed80\n"
        ".hword 0x4a10, 0xedc0, 0x2a11, 0xedc0\n"
        ".hword 0x7008, 0xe596, 0xc004, 0xe5d0\n"
        ".hword 0x0007, 0xe15c, 0x007e, 0x0a00\n"
        ".hword 0x008d, 0xe35c, 0x005c, 0x0a00\n"
        ".hword 0x008e, 0xe35c, 0x005d, 0x0a00\n"
        ".hword 0x005c, 0xe35c, 0x005e, 0x0a00\n"
        ".hword 0x005d, 0xe35c, 0x005f, 0x0a00\n"
        ".hword 0x0060, 0xea00, 0x2000, 0xe59b\n"
        ".hword 0xffbd, 0xeaff, 0x0d2e, 0xe284\n"
        ".hword 0x0000, 0xe352, 0x1001, 0xe890\n"
        ".hword 0x3000, 0xe3a0, 0x0a10, 0xee01\n"
        ".hword 0xca90, 0xee01, 0x2ac1, 0xeeb8\n"
        ".hword 0x1ae1, 0xeeb8, 0x1a40, 0xee72\n"
        ".hword 0x1a60, 0xee31, 0x1ae1, 0xeefd\n"
        ".hword 0x1ac1, 0xeebd, 0x005a, 0xda00\n"
        ".hword 0x0083, 0xe083, 0x0203, 0xe080\n"
        ".hword 0x0000, 0xe351, 0x0100, 0xe084\n"
        ".hword 0x0b03, 0x0280, 0x0fa2, 0x0280\n"
        ".hword 0x0a05, 0x1280, 0x0ea9, 0x1280\n"
        ".hword 0xc3b4, 0xe1d0, 0x0000, 0xe35c\n"
        ".hword 0x0031, 0x0a00, 0x4ae1, 0xeef8\n"
        ".hword 0x5ac1, 0xeef8, 0x2a03, 0xed90\n"
        ".hword 0x4a04, 0xed90, 0x2a05, 0xedd0\n"
        ".hword 0x5a06, 0xed90, 0xc0b8, 0xe1d0\n"
        ".hword 0xc3b6, 0xe1c0, 0x6ac3, 0xee34\n"
        ".hword 0x4ae3, 0xee75, 0x2a46, 0xee32\n"
        ".hword 0x4a64, 0xee74, 0x4ac2, 0xeebd\n"
        ".hword 0x2ae4, 0xeebd, 0x4ae2, 0xeefc\n"
        ".hword 0x2ac5, 0xeefc, 0x4a0e, 0xed80\n"
        ".hword 0x2a0f, 0xed80, 0x4a10, 0xedc0\n"
        ".hword 0x2a11, 0xedc0, 0x7008, 0xe596\n"
        ".hword 0xc004, 0xe5d0, 0x0007, 0xe15c\n"
        ".hword 0x001d, 0x0a00, 0x008d, 0xe35c\n"
        ".hword 0x0006, 0x0a00, 0x008e, 0xe35c\n"
        ".hword 0x0007, 0x0a00, 0x005c, 0xe35c\n"
        ".hword 0x0008, 0x0a00, 0x005d, 0xe35c\n"
        ".hword 0x0009, 0x0a00, 0x000a, 0xea00\n"
        ".hword 0x008e, 0xe357, 0x0012, 0x0a00\n"
        ".hword 0x0007, 0xea00, 0x008d, 0xe357\n"
        ".hword 0x000f, 0x0a00, 0x0004, 0xea00\n"
        ".hword 0x005d, 0xe357, 0x000c, 0x0a00\n"
        ".hword 0x0001, 0xea00, 0x005c, 0xe357\n"
        ".hword 0x0009, 0x0a00, 0xc2bc, 0xe1d0\n"
        ".hword 0x0000, 0xe35c, 0x0004, 0x135c\n"
        ".hword 0x9048, 0x0580, 0x0000, 0x0a00\n"
        ".hword 0xe048, 0xe580, 0x3001, 0xe283\n"
        ".hword 0x0002, 0xe153, 0xffbf, 0xbaff\n"
        ".hword 0x0019, 0xea00, 0xc2bc, 0xe1d0\n"
        ".hword 0x0000, 0xe35c, 0x0004, 0x135c\n"
        ".hword 0x5048, 0x0580, 0xfff6, 0x0aff\n"
        ".hword 0xfff4, 0xeaff, 0x008e, 0xe357\n"
        ".hword 0x001d, 0x0a00, 0x0007, 0xea00\n"
        ".hword 0x008d, 0xe357, 0x001a, 0x0a00\n"
        ".hword 0x0004, 0xea00, 0x005d, 0xe357\n"
        ".hword 0x0017, 0x0a00, 0x0001, 0xea00\n"
        ".hword 0x005c, 0xe357, 0x0014, 0x0a00\n"
        ".hword 0xc2bc, 0xe1d0, 0x0000, 0xe35c\n"
        ".hword 0x0004, 0x135c, 0x9048, 0x0580\n"
        ".hword 0x0000, 0x0a00, 0xe048, 0xe580\n"
        ".hword 0x3001, 0xe283, 0x0002, 0xe153\n"
        ".hword 0xff69, 0xbaff, 0x1001, 0xe281\n"
        ".hword 0x0002, 0xe351, 0xff4f, 0xbaff\n"
        ".hword 0x4c5a, 0xe284, 0x408d, 0xe284\n"
        ".hword 0x0000, 0xe3a0, 0x0000, 0xe5c4\n"
        ".hword 0x9ff0, 0xe8bd, 0x0000, 0x4320\n"
        ".hword 0x0000, 0x42f0, 0xf91c, 0x0049\n"
        ".hword 0x83ff, 0xb4ff, 0xc2bc, 0xe1d0\n"
        ".hword 0x0000, 0xe35c, 0x0004, 0x135c\n"
        ".hword 0x5048, 0x0580, 0xffeb, 0x0aff\n"
        ".hword 0xffe9, 0xeaff\n"
    );
}

// DECOMP_FUNC(0x00195044, 868)
extern "C" __attribute__((naked)) void camp_func_00195044() {
    asm volatile(
        ".arm\n"
        ".hword 0x034c, 0xe59f, 0x43f0, 0xe92d\n"
        ".hword 0xd01c, 0xe24d, 0x4000, 0xe590\n"
        ".hword 0x0344, 0xe594, 0x0000, 0xe350\n"
        ".hword 0x5000, 0x03a0, 0x0005, 0x0a00\n"
        ".hword 0x0001, 0xe350, 0x0027, 0x0a00\n"
        ".hword 0x0002, 0xe350, 0x5000, 0x03a0\n"
        ".hword 0x00b4, 0x1a00, 0x00b8, 0xea00\n"
        ".hword 0x0340, 0xe594, 0x0005, 0xe150\n"
        ".hword 0x0005, 0xba00, 0x0185, 0xe065\n"
        ".hword 0x1000, 0xe3a0, 0x0100, 0xe080\n"
        ".hword 0x0100, 0xe084, 0x0020, 0xe280\n"
        ".hword 0x905f, 0xeb04, 0x5001, 0xe285\n"
        ".hword 0x0005, 0xe355, 0xfff3, 0xbaff\n"
        ".hword 0x0e25, 0xe284, 0x08da, 0xe1d0\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x00a2, 0x0a00, 0x101a, 0xe3a0\n"
        ".hword 0x0030, 0xe3a0, 0x8dfd, 0xeb04\n"
        ".hword 0x5c03, 0xe284, 0x101b, 0xe3a0\n"
        ".hword 0x04b8, 0xe1c5, 0x0030, 0xe3a0\n"
        ".hword 0x8df8, 0xeb04, 0x04ba, 0xe1c5\n"
        ".hword 0x101c, 0xe3a0, 0x0030, 0xe3a0\n"
        ".hword 0x8df4, 0xeb04, 0x04bc, 0xe1c5\n"
        ".hword 0x05b8, 0xe1d5, 0x1001, 0xe3a0\n"
        ".hword 0x0003, 0xe280, 0x05b8, 0xe1c5\n"
        ".hword 0x1344, 0xe584, 0x008f, 0xea00\n"
        ".hword 0x5000, 0xe3a0, 0x0fb7, 0xe284\n"
        ".hword 0x27f6, 0xeb04, 0x0000, 0xe350\n"
        ".hword 0x9000, 0xe3a0, 0x001c, 0xda00\n"
        ".hword 0x6270, 0xe59f, 0x0085, 0xe084\n"
        ".hword 0x1000, 0xe3a0, 0x60f6, 0xe190\n"
        ".hword 0x0037, 0xe3a0, 0xaf61, 0xeb04\n"
        ".hword 0x8000, 0xe1a0, 0xf000, 0xe320\n"
        ".hword 0xaf54, 0xeb04, 0x7000, 0xe1a0\n"
        ".hword 0x0008, 0xe1a0, 0xaf3d, 0xeb04\n"
        ".hword 0x0000, 0xe156, 0xf000, 0xe320\n"
        ".hword 0x0007, 0x2a00, 0x0306, 0xe097\n"
        ".hword 0x0005, 0x0a00, 0x00f0, 0xe1d0\n"
        ".hword 0x0000, 0xe350, 0x0002, 0xaa00\n"
        ".hword 0xee34, 0xeb03, 0x1105, 0xe084\n"
        ".hword 0x035c, 0xe581, 0x5001, 0xe285\n"
        ".hword 0x0fb7, 0xe284, 0x27d9, 0xeb04\n"
        ".hword 0x0005, 0xe150, 0xf000, 0xe320\n"
        ".hword 0xffe2, 0xcaff, 0x101c, 0xe3a0\n"
        ".hword 0x0030, 0xe3a0, 0x9014, 0xe5cd\n"
        ".hword 0xa949, 0xeb04, 0x6000, 0xe1a0\n"
        ".hword 0x0fb7, 0xe284, 0x282a, 0xeb04\n"
        ".hword 0x5000, 0xe1a0, 0x0c03, 0xe284\n"
        ".hword 0x3004, 0xe28d, 0x14fa, 0xe1d0\n"
        ".hword 0x2014, 0xe28d, 0x0206, 0xe883\n"
        ".hword 0x2000, 0xe3a0, 0x9010, 0xe58d\n"
        ".hword 0x14f8, 0xe1d0, 0x1000, 0xe58d\n"
        ".hword 0x34fc, 0xe1d0, 0x1006, 0xe1a0\n"
        ".hword 0x0fb7, 0xe284, 0x29a2, 0xeb04\n"
        ".hword 0x61ac, 0xe59f, 0x0000, 0xe350\n"
        ".hword 0x0009, 0x0a00, 0x0fb7, 0xe284\n"
        ".hword 0x2817, 0xeb04, 0x0005, 0xe150\n"
        ".hword 0xf000, 0xe320, 0x004f, 0x0a00\n"
        ".hword 0x0006, 0xe1a0, 0x9bfa, 0xeb04\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x004a, 0xea00, 0x1000, 0xe3a0\n"
        ".hword 0x0fb7, 0xe284, 0x2812, 0xeb04\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x002f, 0x0a00, 0x0fb7, 0xe284\n"
        ".hword 0x27ac, 0xeb04, 0x0005, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0024, 0xda00\n"
        ".hword 0x0fb7, 0xe284, 0x2802, 0xeb04\n"
        ".hword 0x0005, 0xe150, 0xf000, 0xe320\n"
        ".hword 0x001f, 0x1a00, 0x0fb7, 0xe284\n"
        ".hword 0x27fd, 0xeb04, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0004, 0x1a00\n"
        ".hword 0x0fb7, 0xe284, 0x27f2, 0xeb04\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0015, 0x0a00, 0x0fb7, 0xe284\n"
        ".hword 0x27f3, 0xeb04, 0x7000, 0xe1a0\n"
        ".hword 0x0fb7, 0xe284, 0x2795, 0xeb04\n"
        ".hword 0x0005, 0xe240, 0x0000, 0xe157\n"
        ".hword 0x0004, 0x1a00, 0x0fb7, 0xe284\n"
        ".hword 0x27e5, 0xeb04, 0x0004, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0008, 0x0a00\n"
        ".hword 0x1000, 0xe3a0, 0x0fb7, 0xe284\n"
        ".hword 0x27eb, 0xeb04, 0x0fb7, 0xe284\n"
        ".hword 0xf000, 0xe320, 0x27e2, 0xeb04\n"
        ".hword 0x0005, 0xe150, 0xf000, 0xe320\n"
        ".hword 0xffdf, 0x0aff, 0x0fb7, 0xe284\n"
        ".hword 0x27dd, 0xeb04, 0x0005, 0xe150\n"
        ".hword 0xf000, 0xe320, 0x0015, 0x0a00\n"
        ".hword 0xffc4, 0xeaff, 0x1001, 0xe3a0\n"
        ".hword 0x0001, 0xe1a0, 0xb14a, 0xeb04\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x000e, 0x0a00, 0x008c, 0xe59f\n"
        ".hword 0x9bb9, 0xeb04, 0x5000, 0xe3a0\n"
        ".hword 0x2000, 0xe3a0, 0x0185, 0xe065\n"
        ".hword 0x1001, 0xe3a0, 0x0100, 0xe080\n"
        ".hword 0x0100, 0xe084, 0x0020, 0xe280\n"
        ".hword 0xa1e1, 0xeb04, 0x5001, 0xe285\n"
        ".hword 0x0005, 0xe355, 0xfff5, 0xbaff\n"
        ".hword 0x0002, 0xe3a0, 0x0344, 0xe584\n"
        ".hword 0x0340, 0xe594, 0x0001, 0xe280\n"
        ".hword 0x0340, 0xe584, 0xd01c, 0xe28d\n"
        ".hword 0x83f0, 0xe8bd, 0x0185, 0xe065\n"
        ".hword 0x0100, 0xe080, 0x0100, 0xe084\n"
        ".hword 0x0020, 0xe280, 0xa99e, 0xeb04\n"
        ".hword 0x5001, 0xe285, 0x0005, 0xe355\n"
        ".hword 0xfff7, 0xbaff, 0x0e25, 0xe284\n"
        ".hword 0x08da, 0xe1d0, 0x0000, 0xe350\n"
        ".hword 0x0003, 0x13a0, 0xffed, 0x0aff\n"
        ".hword 0xffeb, 0xeaff, 0xdd08, 0x0043\n"
        ".hword 0x0424, 0x0000, 0x016c, 0x0100\n"
        ".hword 0x016e, 0x0100\n"
    );
}

// DECOMP_FUNC(0x002668dc, 892)
extern "C" __attribute__((naked)) void script_vm_func_002668dc() {
    asm volatile(
        ".arm\n"
        ".hword 0x47f0, 0xe92d, 0x7310, 0xe59f\n"
        ".hword 0x8b0a, 0xed2d, 0xde51, 0xe24d\n"
        ".hword 0x5000, 0xe597, 0x0000, 0xe355\n"
        ".hword 0x00bc, 0x0a00, 0x0a98, 0xe595\n"
        ".hword 0x102a, 0xe3a0, 0xc1ec, 0xeb02\n"
        ".hword 0x82f0, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x0a9c, 0xe585, 0x1a94, 0xe585\n"
        ".hword 0x1a98, 0xe585, 0x0000, 0xe598\n"
        ".hword 0x6000, 0xe597, 0x0065, 0xe350\n"
        ".hword 0x001a, 0x1a00, 0x0004, 0xe598\n"
        ".hword 0x0001, 0xe350, 0x0046, 0x0a00\n"
        ".hword 0x0002, 0xe350, 0x0078, 0x0287\n"
        ".hword 0x0048, 0x0a00, 0x0003, 0xe350\n"
        ".hword 0x02b4, 0x059f, 0x0045, 0x0a00\n"
        ".hword 0x0004, 0xe350, 0x02ac, 0x059f\n"
        ".hword 0x0042, 0x0a00, 0x0005, 0xe350\n"
        ".hword 0x02a4, 0x059f, 0x003f, 0x0a00\n"
        ".hword 0x0006, 0xe350, 0x029c, 0x059f\n"
        ".hword 0x003c, 0x0a00, 0x0007, 0xe350\n"
        ".hword 0x0294, 0x059f, 0x0039, 0x0a00\n"
        ".hword 0x0008, 0xe350, 0x028c, 0x059f\n"
        ".hword 0x0036, 0x0a00, 0x0009, 0xe350\n"
        ".hword 0x0284, 0x059f, 0x0033, 0x0a00\n"
        ".hword 0x0a9c, 0xe596, 0x4000, 0xe3a0\n"
        ".hword 0x0004, 0xe590, 0x0000, 0xe350\n"
        ".hword 0x9001, 0xc3a0, 0x0012, 0xda00\n"
        ".hword 0x0a9c, 0xe596, 0x1004, 0xe1a0\n"
        ".hword 0xa520, 0xebfe, 0x0000, 0xe597\n"
        ".hword 0x0000, 0xe350, 0x0004, 0x0a00\n"
        ".hword 0x1204, 0xe084, 0x0181, 0xe080\n"
        ".hword 0x1b30, 0xe5d0, 0x0000, 0xe351\n"
        ".hword 0x9b30, 0x05c0, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0xfcef, 0xebff\n"
        ".hword 0x0a9c, 0xe596, 0x4001, 0xe284\n"
        ".hword 0x0004, 0xe590, 0x0004, 0xe150\n"
        ".hword 0xffec, 0xcaff, 0x0a9c, 0xe595\n"
        ".hword 0x4000, 0xe3a0, 0x0004, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x0077, 0xda00\n"
        ".hword 0x7208, 0xe59f, 0xca82, 0xeddf\n"
        ".hword 0xca82, 0xed9f, 0x8a82, 0xed9f\n"
        ".hword 0x8a82, 0xeddf, 0x9a82, 0xed9f\n"
        ".hword 0x9a82, 0xeddf, 0xaa82, 0xed9f\n"
        ".hword 0xaa82, 0xeddf, 0xba82, 0xed9f\n"
        ".hword 0xba82, 0xeddf, 0x900d, 0xe1a0\n"
        ".hword 0x6028, 0xe28d, 0x0000, 0xe597\n"
        ".hword 0x0001, 0xe310, 0x0018, 0x1a00\n"
        ".hword 0x0006, 0xea00, 0x01f0, 0xe59f\n"
        ".hword 0x0679, 0xeb03, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0xffe4, 0xeaff\n"
        ".hword 0x0675, 0xeb03, 0xffe2, 0xeaff\n"
        ".hword 0x01a8, 0xe59f, 0x6597, 0xfa01\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x000b, 0x0a00, 0x11c4, 0xe59f\n"
        ".hword 0x0190, 0xe59f, 0xca00, 0xedc1\n"
        ".hword 0x8a01, 0xed81, 0x8a02, 0xed81\n"
        ".hword 0x8a03, 0xed81, 0xca04, 0xedc1\n"
        ".hword 0x8a05, 0xed81, 0x8a06, 0xed81\n"
        ".hword 0x8a07, 0xed81, 0xca08, 0xedc1\n"
        ".hword 0x0000, 0xe1a0, 0x1194, 0xe59f\n"
        ".hword 0x0009, 0xe1a0, 0x7e4d, 0xeb00\n"
        ".hword 0x0004, 0xe598, 0x1a62, 0xeddf\n"
        ".hword 0x0063, 0xe350, 0x0a9c, 0xe595\n"
        ".hword 0x0a4c, 0x0eb0, 0x0a68, 0x1eb0\n"
        ".hword 0x2a61, 0xeeb0, 0x0000, 0xe590\n"
        ".hword 0x1104, 0xe790, 0x2008, 0xe591\n"
        ".hword 0x100c, 0xe5b2, 0x0000, 0xe351\n"
        ".hword 0x1002, 0x1081, 0x00d7, 0xe1d1\n"
        ".hword 0x20d5, 0xe1d1, 0x30d8, 0xe1d1\n"
        ".hword 0x0030, 0xe240, 0x1031, 0xe242\n"
        ".hword 0x0100, 0xe080, 0x1a10, 0xee01\n"
        ".hword 0x2080, 0xe1a0, 0x2030, 0xe242\n"
        ".hword 0x2003, 0xe082, 0x2001, 0xe242\n"
        ".hword 0x2a90, 0xee00, 0x3040, 0xe595\n"
        ".hword 0x1ac1, 0xeeb8, 0x8a0a, 0xed8d\n"
        ".hword 0x8a0b, 0xed8d, 0x3064, 0xe243\n"
        ".hword 0x2ae0, 0xeef8, 0x8a0c, 0xed8d\n"
        ".hword 0x9a0d, 0xed8d, 0x8a0e, 0xed8d\n"
        ".hword 0x0083, 0xe083, 0x8a11, 0xed8d\n"
        ".hword 0x8a14, 0xed8d, 0x1100, 0xe086\n"
        ".hword 0x2a28, 0xee01, 0xba15, 0xedcd\n"
        ".hword 0x003c, 0xe28d, 0x1aa8, 0xee42\n"
        ".hword 0x9a02, 0xecc0, 0x0048, 0xe28d\n"
        ".hword 0x0a38, 0xeddf, 0xaa02, 0xecc0\n"
        ".hword 0x1a00, 0xed91, 0x2a02, 0xedd1\n"
        ".hword 0x1204, 0xe084, 0x1a02, 0xee31\n"
        ".hword 0x1aa1, 0xee72, 0x0181, 0xe085\n"
        ".hword 0x1b02, 0xe280, 0x1fab, 0xe281\n"
        ".hword 0x000c, 0xe28d, 0x2a40, 0xeef0\n"
        ".hword 0x2a40, 0xeeb0, 0x4001, 0xe284\n"
        ".hword 0x1a00, 0xed81, 0x0a01, 0xedc1\n"
        ".hword 0x1a02, 0xedc1, 0x0a03, 0xecdd\n"
        ".hword 0x3a05, 0xec90, 0x000c, 0xe281\n"
        ".hword 0x0a03, 0xecc0, 0x0018, 0xe281\n"
        ".hword 0x3a05, 0xec80, 0x0020, 0xe59d\n"
        ".hword 0x002c, 0xe581, 0x0a0c, 0xed81\n"
        ".hword 0x1034, 0xe281, 0x2a02, 0xec81\n"
        ".hword 0x0a9c, 0xe595, 0x0004, 0xe590\n"
        ".hword 0x0004, 0xe150, 0xff94, 0xcaff\n"
        ".hword 0xde51, 0xe28d, 0x8b0a, 0xecbd\n"
        ".hword 0x87f0, 0xe8bd, 0x7060, 0x0044\n"
        ".hword 0xf91c, 0x0049, 0x7128, 0x0044\n"
        ".hword 0x7178, 0x0044, 0x71c8, 0x0044\n"
        ".hword 0x7218, 0x0044, 0x7268, 0x0044\n"
        ".hword 0x72b8, 0x0044, 0x7308, 0x0044\n"
        ".hword 0x6630, 0x0047, 0x0000, 0x3f80\n"
        ".hword 0xf000, 0x456b, 0x0000, 0x0000\n"
        ".hword 0x7000, 0x455f, 0xe000, 0xc6bf\n"
        ".hword 0xb400, 0xc682, 0x2000, 0xc67d\n"
        ".hword 0xe000, 0xc671, 0x0000, 0xc63e\n"
        ".hword 0xc000, 0xc65a, 0x7088, 0x0044\n"
        ".hword 0xfd48, 0x004e, 0x7000, 0x44df\n"
        ".hword 0x0000, 0x4120\n"
    );
}

// DECOMP_FUNC(0x00159a44, 896)
extern "C" __attribute__((naked)) void engine_func_00159a44() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0x5000, 0xe1a0\n"
        ".hword 0x4001, 0xe1a0, 0x8b04, 0xed2d\n"
        ".hword 0xd034, 0xe24d, 0x00dd, 0xe1d0\n"
        ".hword 0x0000, 0xe350, 0x0001, 0x1350\n"
        ".hword 0x0021, 0x1a00, 0x0000, 0xe595\n"
        ".hword 0x0000, 0xe350, 0x0008, 0x1595\n"
        ".hword 0x0000, 0x1350, 0x001c, 0x0a00\n"
        ".hword 0x0a03, 0xedd4, 0x0abf, 0xed9f\n"
        ".hword 0x0ac0, 0xeef4, 0xfa10, 0xeef1\n"
        ".hword 0x0017, 0x3a00, 0x0a90, 0xee10\n"
        ".hword 0x05fe, 0xe350, 0x0014, 0xca00\n"
        ".hword 0x0a04, 0xedd4, 0x0ac0, 0xeef4\n"
        ".hword 0xfa10, 0xeef1, 0x0010, 0x3a00\n"
        ".hword 0x0a90, 0xee10, 0x05fe, 0xe350\n"
        ".hword 0x000d, 0xca00, 0x0a06, 0xedd4\n"
        ".hword 0x0ac0, 0xeef4, 0xfa10, 0xeef1\n"
        ".hword 0x0009, 0x3a00, 0x0a90, 0xee10\n"
        ".hword 0x05fe, 0xe350, 0x0006, 0xca00\n"
        ".hword 0x0a07, 0xedd4, 0x0ac0, 0xeef4\n"
        ".hword 0xfa10, 0xeef1, 0x0002, 0x3a00\n"
        ".hword 0x0a90, 0xee10, 0x05fe, 0xe350\n"
        ".hword 0x0003, 0xda00, 0xd034, 0xe28d\n"
        ".hword 0x0000, 0xe3a0, 0x8b04, 0xecbd\n"
        ".hword 0x8ff0, 0xe8bd, 0x1000, 0xe594\n"
        ".hword 0x2ffa, 0xe3a0, 0x0278, 0xe59f\n"
        ".hword 0x0a9e, 0xeddf, 0x0291, 0xe001\n"
        ".hword 0x9aa0, 0xed9f, 0x9aa0, 0xeddf\n"
        ".hword 0x8aa0, 0xed9f, 0x2190, 0xe081\n"
        ".hword 0x2ffa, 0xe3a0, 0x6000, 0xe3a0\n"
        ".hword 0xb00d, 0xe1a0, 0xa621, 0xe1a0\n"
        ".hword 0x1008, 0xe594, 0x0001, 0xe35a\n"
        ".hword 0xa001, 0xb3a0, 0xa1bc, 0xe1cd\n"
        ".hword 0x0291, 0xe001, 0x1190, 0xe080\n"
        ".hword 0x9620, 0xe1a0, 0x0001, 0xe359\n"
        ".hword 0x9001, 0xb3a0, 0x0002, 0xe3a0\n"
        ".hword 0x91be, 0xe1cd, 0x00b6, 0xe1cd\n"
        ".hword 0x0004, 0xe594, 0x7014, 0xe594\n"
        ".hword 0x0a10, 0xee00, 0x0000, 0xe357\n"
        ".hword 0x7214, 0x059f, 0x0214, 0xe59f\n"
        ".hword 0x0a40, 0xeeb8, 0x1000, 0xe597\n"
        ".hword 0x2190, 0xe081, 0x0a20, 0xee20\n"
        ".hword 0x13a1, 0xe1a0, 0x12b0, 0xe1cd\n"
        ".hword 0x1004, 0xe597, 0x0a7e, 0xeddf\n"
        ".hword 0x1190, 0xe080, 0x8a20, 0xee60\n"
        ".hword 0x03a0, 0xe1a0, 0x02b2, 0xe1cd\n"
        ".hword 0x8086, 0xe08b, 0x02f0, 0xe1d8\n"
        ".hword 0x0100, 0xe080, 0x0280, 0xe1a0\n"
        ".hword 0x0a10, 0xee00, 0x0ac0, 0xeeb8\n"
        ".hword 0x0a09, 0xee20, 0x0a28, 0xeec0\n"
        ".hword 0x0a69, 0xeeb0, 0x8048, 0xeb05\n"
        ".hword 0x0a08, 0xee20, 0x6001, 0xe286\n"
        ".hword 0x0002, 0xe356, 0x0ac0, 0xeebd\n"
        ".hword 0x0a10, 0xee10, 0x02bc, 0xe1c8\n"
        ".hword 0xffee, 0xbaff, 0x0a06, 0xed94\n"
        ".hword 0x1198, 0xe59f, 0x21a8, 0xe59f\n"
        ".hword 0x0a08, 0xee20, 0x0a6a, 0xeddf\n"
        ".hword 0x0ac0, 0xeebc, 0x0a10, 0xee10\n"
        ".hword 0x02b6, 0xe1cd, 0x0a07, 0xed94\n"
        ".hword 0x0a08, 0xee20, 0x0ac0, 0xeebc\n"
        ".hword 0x0a10, 0xee10, 0x02b8, 0xe1cd\n"
        ".hword 0x0a03, 0xed94, 0x0a08, 0xee20\n"
        ".hword 0x0ac0, 0xeebc, 0x0a10, 0xee10\n"
        ".hword 0x02ba, 0xe1cd, 0x0008, 0xe597\n"
        ".hword 0x1091, 0xe080, 0x03a0, 0xe1a0\n"
        ".hword 0x02b4, 0xe1cd, 0x0a04, 0xed94\n"
        ".hword 0x0a10, 0xee10, 0x0002, 0xe150\n"
        ".hword 0x0020, 0xe5d4, 0x0a53, 0xcd9f\n"
        ".hword 0x0001, 0xe350, 0x0ac0, 0x1e70\n"
        ".hword 0x0052, 0x0a00, 0x1a08, 0xee20\n"
        ".hword 0x010a, 0xe08a, 0x3004, 0xe3a0\n"
        ".hword 0x1400, 0xe1a0, 0x30b0, 0xe1cd\n"
        ".hword 0x0a88, 0xee60, 0x0ae0, 0xeebd\n"
        ".hword 0x0ac1, 0xeefd, 0x2a10, 0xee10\n"
        ".hword 0x0a90, 0xee10, 0x23b0, 0xe1cd\n"
        ".hword 0x03b2, 0xe1cd, 0x0000, 0xe595\n"
        ".hword 0x2303, 0xe280, 0x2822, 0xe1a0\n"
        ".hword 0x2800, 0xe182, 0x2008, 0xe58d\n"
        ".hword 0x2008, 0xe595, 0x0001, 0xe152\n"
        ".hword 0x0021, 0x3a00, 0x2001, 0xe080\n"
        ".hword 0x3303, 0xe282, 0xc109, 0xe089\n"
        ".hword 0x3823, 0xe1a0, 0x2802, 0xe183\n"
        ".hword 0x200c, 0xe58d, 0x2008, 0xe595\n"
        ".hword 0x140c, 0xe081, 0x0001, 0xe152\n"
        ".hword 0x0017, 0x3a00, 0x2001, 0xe080\n"
        ".hword 0x3303, 0xe282, 0x3823, 0xe1a0\n"
        ".hword 0x2802, 0xe183, 0x2010, 0xe58d\n"
        ".hword 0x22f0, 0xe1dd, 0x2102, 0xe082\n"
        ".hword 0x1402, 0xe081, 0x2001, 0xe080\n"
        ".hword 0x3303, 0xe282, 0x3823, 0xe1a0\n"
        ".hword 0x2802, 0xe183, 0x32f2, 0xe1dd\n"
        ".hword 0x2014, 0xe58d, 0x2008, 0xe595\n"
        ".hword 0x3103, 0xe083, 0x1403, 0xe081\n"
        ".hword 0x0001, 0xe152, 0x0004, 0x3a00\n"
        ".hword 0x0001, 0xe080, 0x1303, 0xe280\n"
        ".hword 0x1821, 0xe1a0, 0x0800, 0xe181\n"
        ".hword 0x0018, 0xe58d, 0x0006, 0xe3a0\n"
        ".hword 0x00b0, 0xe1cd, 0x0000, 0xe595\n"
        ".hword 0x1008, 0xe595, 0xa77c, 0xeb05\n"
        ".hword 0x0000, 0xe595, 0x1008, 0xe595\n"
        ".hword 0x2c14, 0xeb05, 0x40dd, 0xe1d5\n"
        ".hword 0xf000, 0xe320, 0x8690, 0xeb05\n"
        ".hword 0x200d, 0xe1a0, 0x1004, 0xe1a0\n"
        ".hword 0xf123, 0xebff, 0xd034, 0xe28d\n"
        ".hword 0x8b04, 0xecbd, 0x8ff0, 0xe8bd\n"
        ".hword 0x0000, 0x0000, 0x3cc1, 0xd685\n"
        ".hword 0x126f, 0x3a83, 0x3278, 0x0047\n"
        ".hword 0xcccd, 0xcccc, 0xb000, 0x46ff\n"
        ".hword 0x0000, 0xc040, 0x0000, 0x4120\n"
        ".hword 0x0000, 0x4300, 0x3333, 0x3f73\n"
        ".hword 0x3333, 0x3f73, 0x0000, 0x3f80\n"
        ".hword 0x1a40, 0xeeb0, 0x0a40, 0xeeb1\n"
        ".hword 0x0a60, 0xee71, 0xffa8, 0xeaff\n"
    );
}

// DECOMP_FUNC(0x003a604c, 900)
extern "C" __attribute__((naked)) void engine_func_003a604c() {
    asm volatile(
        ".arm\n"
        ".hword 0x47f0, 0xe92d, 0x6001, 0xe1a0\n"
        ".hword 0x5002, 0xe1a0, 0x9000, 0xe3a0\n"
        ".hword 0x4003, 0xe1a0, 0x9380, 0xe480\n"
        ".hword 0x216a, 0xebfa, 0x0014, 0xe280\n"
        ".hword 0x2168, 0xebfa, 0x1334, 0xe59f\n"
        ".hword 0x3009, 0xe3a0, 0x2074, 0xe3a0\n"
        ".hword 0x1494, 0xe580, 0x0b01, 0xe280\n"
        ".hword 0x1324, 0xe59f, 0x00ec, 0xe280\n"
        ".hword 0x7fb1, 0xfafc, 0x0b01, 0xe280\n"
        ".hword 0x2318, 0xe59f, 0x1318, 0xe59f\n"
        ".hword 0x3009, 0xe3a0, 0x0014, 0xe280\n"
        ".hword 0x7fab, 0xfafc, 0x0a09, 0xe280\n"
        ".hword 0x0014, 0xe280, 0x8531, 0xebfb\n"
        ".hword 0x7b27, 0xe240, 0x70a8, 0xe247\n"
        ".hword 0x0007, 0xe1a0, 0xf99b, 0xebff\n"
        ".hword 0xc2f0, 0xe59f, 0x6010, 0xe587\n"
        ".hword 0x9000, 0xe587, 0xae86, 0xe287\n"
        ".hword 0x5014, 0xe5c7, 0x1000, 0xe3e0\n"
        ".hword 0x4018, 0xe587, 0x3004, 0xe28c\n"
        ".hword 0x0202, 0xe88a, 0x2018, 0xe283\n"
        ".hword 0x9007, 0xe78c, 0x0004, 0xe282\n"
        ".hword 0x9007, 0xe783, 0x9007, 0xe782\n"
        ".hword 0x1004, 0xe280, 0x9007, 0xe780\n"
        ".hword 0x9007, 0xe781, 0x9160, 0xe587\n"
        ".hword 0x9164, 0xe587, 0x9168, 0xe587\n"
        ".hword 0x9370, 0xe587, 0x9374, 0xe587\n"
        ".hword 0x9378, 0xe587, 0x901c, 0xe5c7\n"
        ".hword 0x0fea, 0xe287, 0x901d, 0xe5c7\n"
        ".hword 0x3533, 0xebfa, 0x302b, 0xe3a0\n"
        ".hword 0x2000, 0xe3a0, 0x1d05, 0xe3a0\n"
        ".hword 0x0d0e, 0xe287, 0x31ae, 0xebfa\n"
        ".hword 0x302b, 0xe3a0, 0x2000, 0xe3a0\n"
        ".hword 0x1d05, 0xe3a0, 0x0fe5, 0xe287\n"
        ".hword 0x31a9, 0xebfa, 0x1008, 0xe1a0\n"
        ".hword 0x0068, 0xe3a0, 0x70a4, 0xebfc\n"
        ".hword 0x0000, 0xe350, 0x0002, 0x0a00\n"
        ".hword 0x3492, 0xebfa, 0x1248, 0xe59f\n"
        ".hword 0x1000, 0xe580, 0x085c, 0xe587\n"
        ".hword 0xf61c, 0xebfa, 0x0014, 0xe5d7\n"
        ".hword 0x1018, 0xe597, 0x0000, 0xe350\n"
        ".hword 0x2006, 0x03a0, 0x2001, 0x13a0\n"
        ".hword 0x6a9a, 0xebfc, 0x00b0, 0xe1d0\n"
        ".hword 0x0000, 0xe350, 0x0001, 0x13a0\n"
        ".hword 0x001c, 0x15c7, 0x0010, 0xe597\n"
        ".hword 0x0001, 0xe350, 0x0011, 0x0a00\n"
        ".hword 0x001f, 0xe3a0, 0x037c, 0xe587\n"
        ".hword 0x9004, 0xe587, 0x0007, 0xe1a0\n"
        ".hword 0x9008, 0xe587, 0xedba, 0xebff\n"
        ".hword 0x10ff, 0xe3a0, 0x0000, 0xe3a0\n"
        ".hword 0x7324, 0xebfb, 0x10ff, 0xe3a0\n"
        ".hword 0x0001, 0xe3a0, 0x7321, 0xebfb\n"
        ".hword 0x61d8, 0xe59f, 0x0000, 0xe355\n"
        ".hword 0x001d, 0x0a00, 0x0001, 0xe355\n"
        ".hword 0x0032, 0x0a00, 0x004c, 0xea00\n"
        ".hword 0x1004, 0xe287, 0x000d, 0xe3a0\n"
        ".hword 0x0201, 0xe881, 0x9e91, 0xebfb\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x9dd6, 0xebfb, 0x002b, 0xe3a0\n"
        ".hword 0xf000, 0xe320, 0x7b00, 0xebfc\n"
        ".hword 0x1000, 0xe3a0, 0x002b, 0xe3a0\n"
        ".hword 0x7e21, 0xebfc, 0x0083, 0xe3a0\n"
        ".hword 0x037c, 0xe587, 0x0007, 0xe1a0\n"
        ".hword 0xf975, 0xebff, 0x001d, 0xe5c7\n"
        ".hword 0x1001, 0xe3a0, 0x0000, 0xe3a0\n"
        ".hword 0xe909, 0xebfb, 0x1001, 0xe3a0\n"
        ".hword 0x0001, 0xe1a0, 0xe906, 0xebfb\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x004e, 0xea00, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x76b2, 0xebfe\n"
        ".hword 0x0006, 0xe354, 0x0007, 0x1354\n"
        ".hword 0x0008, 0x0a00, 0x0008, 0xe354\n"
        ".hword 0x0029, 0x0a00, 0x4138, 0xe59f\n"
        ".hword 0x0004, 0xe1a0, 0x850e, 0xebfb\n"
        ".hword 0x0001, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0023, 0x0a00, 0x0015, 0xea00\n"
        ".hword 0x0006, 0xe1a0, 0x8508, 0xebfb\n"
        ".hword 0x0001, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0019, 0x1a00, 0x001c, 0xea00\n"
        ".hword 0xe8df, 0xebfb, 0x001a, 0xea00\n"
        ".hword 0x1001, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0x7684, 0xebfe, 0x0005, 0xe354\n"
        ".hword 0xf000, 0xe320, 0x000b, 0x0a00\n"
        ".hword 0x0009, 0xe354, 0x0012, 0x0a00\n"
        ".hword 0x40e0, 0xe59f, 0x0004, 0xe1a0\n"
        ".hword 0x84f7, 0xebfb, 0x0001, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x000c, 0x0a00\n"
        ".hword 0x203c, 0xe3a0, 0x1000, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0xffeb, 0xeaff\n"
        ".hword 0x0006, 0xe1a0, 0x84ee, 0xebfb\n"
        ".hword 0x0001, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0003, 0x0a00, 0x203c, 0xe3a0\n"
        ".hword 0x1000, 0xe3a0, 0x0006, 0xe1a0\n"
        ".hword 0xffe2, 0xeaff, 0x0007, 0xe1a0\n"
        ".hword 0xf937, 0xebff, 0x8000, 0xe3a0\n"
        ".hword 0x001d, 0xe5c7, 0x0588, 0xe088\n"
        ".hword 0x4000, 0xe3a0, 0x5080, 0xe087\n"
        ".hword 0x6b07, 0xe285, 0x09b4, 0xe1d6\n"
        ".hword 0x0000, 0xe350, 0x000b, 0xda00\n"
        ".hword 0x0104, 0xe085, 0x0b03, 0xe280\n"
        ".hword 0x19b6, 0xe1d0, 0x0001, 0xe311\n"
        ".hword 0x0002, 0x0a00, 0x09b4, 0xe1d0\n"
        ".hword 0x1001, 0xe3a0, 0x76b1, 0xebfe\n"
        ".hword 0x09b4, 0xe1d6, 0x4001, 0xe284\n"
        ".hword 0x0004, 0xe150, 0xfff3, 0xcaff\n"
        ".hword 0x8001, 0xe288, 0x0009, 0xe358\n"
        ".hword 0xffe9, 0xbaff, 0x1001, 0xe3a0\n"
        ".hword 0x001c, 0xe3a0, 0xd755, 0xebfb\n"
        ".hword 0x0007, 0xe1a0, 0x87f0, 0xe8bd\n"
        ".hword 0x21d8, 0x0042, 0x757c, 0x0028\n"
        ".hword 0x1002, 0x0000, 0x0320, 0x003a\n"
        ".hword 0x5d24, 0x0001, 0x1ff8, 0x0042\n"
        ".hword 0x0060, 0x0100, 0x005b, 0x0100\n"
        ".hword 0x005c, 0x0100\n"
    );
}

// DECOMP_FUNC(0x003477f8, 904)
extern "C" __attribute__((naked)) void ui_func_003477f8() {
    asm volatile(
        ".arm\n"
        ".hword 0x43f0, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x8b02, 0xed2d, 0xd00c, 0xe24d\n"
        ".hword 0x0014, 0xe590, 0x1000, 0xe590\n"
        ".hword 0x1008, 0xe591, 0xff31, 0xe12f\n"
        ".hword 0x0004, 0xe594, 0x1060, 0xe594\n"
        ".hword 0x6338, 0xe59f, 0x8ace, 0xeddf\n"
        ".hword 0x0a03, 0xed90, 0x0a08, 0xedd1\n"
        ".hword 0x8acc, 0xed9f, 0x0a20, 0xee30\n"
        ".hword 0x0a03, 0xed80, 0x0004, 0xe594\n"
        ".hword 0x1060, 0xe594, 0x0a04, 0xed90\n"
        ".hword 0x0a09, 0xedd1, 0x0a20, 0xee30\n"
        ".hword 0x0a04, 0xed80, 0x0004, 0xe594\n"
        ".hword 0x1060, 0xe594, 0x0a08, 0xed90\n"
        ".hword 0x0a08, 0xedd1, 0x0a20, 0xee30\n"
        ".hword 0x0a08, 0xed80, 0x0004, 0xe594\n"
        ".hword 0x1060, 0xe594, 0x0a09, 0xed90\n"
        ".hword 0x0a09, 0xedd1, 0x0a20, 0xee30\n"
        ".hword 0x0a09, 0xed80, 0x0004, 0xe594\n"
        ".hword 0x1060, 0xe594, 0x0a0d, 0xed90\n"
        ".hword 0x0a08, 0xedd1, 0x0a20, 0xee30\n"
        ".hword 0x0a0d, 0xed80, 0x0004, 0xe594\n"
        ".hword 0x1060, 0xe594, 0x0a0e, 0xed90\n"
        ".hword 0x0a09, 0xedd1, 0x0a20, 0xee30\n"
        ".hword 0x0a0e, 0xed80, 0x0004, 0xe594\n"
        ".hword 0x1060, 0xe594, 0x0a12, 0xed90\n"
        ".hword 0x0a08, 0xedd1, 0x0a20, 0xee30\n"
        ".hword 0x0a12, 0xed80, 0x0004, 0xe594\n"
        ".hword 0x1060, 0xe594, 0x0a13, 0xed90\n"
        ".hword 0x0a09, 0xedd1, 0x0a20, 0xee30\n"
        ".hword 0x0a13, 0xed80, 0x5060, 0xe594\n"
        ".hword 0x1030, 0xe595, 0x0000, 0xe351\n"
        ".hword 0x0011, 0x0a00, 0x0014, 0xe594\n"
        ".hword 0x0004, 0xe590, 0xfa16, 0xebfd\n"
        ".hword 0x0000, 0xe351, 0x001a, 0x1a00\n"
        ".hword 0x0a0a, 0xedd5, 0x0a16, 0xed94\n"
        ".hword 0x0a20, 0xee30, 0x0a10, 0xee10\n"
        ".hword 0x0a16, 0xed84, 0x0006, 0xe150\n"
        ".hword 0x000c, 0xaa00, 0x0ac8, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x000e, 0x3a00\n"
        ".hword 0x000f, 0xea00, 0x0a16, 0xed84\n"
        ".hword 0x000d, 0xea00, 0x0a0a, 0xedd5\n"
        ".hword 0x0a16, 0xed94, 0x0a20, 0xee30\n"
        ".hword 0x0a10, 0xee10, 0x0a16, 0xed84\n"
        ".hword 0x0006, 0xe150, 0x0001, 0xba00\n"
        ".hword 0x0a68, 0xee30, 0xfff4, 0xeaff\n"
        ".hword 0x0ac8, 0xeeb4, 0xfa10, 0xeef1\n"
        ".hword 0x0001, 0x2a00, 0x0a28, 0xee30\n"
        ".hword 0xffef, 0xeaff, 0x0a16, 0xed94\n"
        ".hword 0x0a7b, 0xeddf, 0x11ec, 0xe59f\n"
        ".hword 0x5000, 0xe3a0, 0x0a20, 0xee20\n"
        ".hword 0x0a48, 0xeef0, 0x0018, 0xe284\n"
        ".hword 0xc005, 0xe1a0, 0x3000, 0xe3a0\n"
        ".hword 0x0ac8, 0xeeb4, 0xfa10, 0xeef1\n"
        ".hword 0x0ac0, 0xeeb0, 0x6001, 0x33a0\n"
        ".hword 0x6000, 0x23a0, 0x2a10, 0xee10\n"
        ".hword 0x0001, 0xe152, 0x1a6e, 0xad9f\n"
        ".hword 0x0003, 0xba00, 0x0a41, 0xee30\n"
        ".hword 0x2a10, 0xee10, 0x0001, 0xe152\n"
        ".hword 0xfffb, 0xaaff, 0x1ae0, 0xeebc\n"
        ".hword 0x0000, 0xe355, 0x1a10, 0xee11\n"
        ".hword 0x1ac8, 0xeebc, 0x1071, 0xe6ff\n"
        ".hword 0x80ff, 0xe201, 0x2a10, 0xee11\n"
        ".hword 0x1ac0, 0xeebc, 0x2072, 0xe6ff\n"
        ".hword 0x7a10, 0xee11, 0x1a10, 0xee01\n"
        ".hword 0x1178, 0xe59f, 0x7077, 0xe6ff\n"
        ".hword 0x90ff, 0xe207, 0x1a41, 0xeef8\n"
        ".hword 0x2a10, 0xee01, 0x20ff, 0xe202\n"
        ".hword 0x2202, 0xe081, 0x2a41, 0xeef8\n"
        ".hword 0x7a10, 0xee01, 0x7208, 0xe081\n"
        ".hword 0x1209, 0xe081, 0x3a01, 0xedd7\n"
        ".hword 0x3a00, 0xed91, 0x4a01, 0xed91\n"
        ".hword 0x2a41, 0xeeb8, 0x1ae1, 0xee30\n"
        ".hword 0x0a00, 0xedd7, 0x1a62, 0xee78\n"
        ".hword 0x7008, 0xe287, 0x2a01, 0xedd2\n"
        ".hword 0x1008, 0xe281, 0x4a02, 0xecd7\n"
        ".hword 0x6a02, 0xecd1, 0x2a42, 0xee30\n"
        ".hword 0x0a00, 0xed92, 0x2008, 0xe282\n"
        ".hword 0x0a24, 0xee41, 0x5a02, 0xecd2\n"
        ".hword 0x3a05, 0xee41, 0x15fe, 0xe3a0\n"
        ".hword 0x0aa5, 0xee01, 0x2a86, 0xee41\n"
        ".hword 0x3a26, 0xee02, 0x4a07, 0xee02\n"
        ".hword 0x0a60, 0x1ef1, 0x0000, 0xe35c\n"
        ".hword 0x0a40, 0x1eb1, 0x0000, 0xe356\n"
        ".hword 0x3a43, 0x1eb1, 0x4a84, 0xee60\n"
        ".hword 0x2a84, 0xee23, 0x4a22, 0xee24\n"
        ".hword 0x6a40, 0xeeb1, 0x5a83, 0xee23\n"
        ".hword 0x5a83, 0xee60, 0x3a22, 0xee23\n"
        ".hword 0x0aa2, 0xee60, 0x2aa2, 0xee63\n"
        ".hword 0x4a00, 0xed80, 0x1a45, 0xeef0\n"
        ".hword 0x1a65, 0xeeb0, 0x3a04, 0xed80\n"
        ".hword 0x0a09, 0xedc0, 0x2a0a, 0xedc0\n"
        ".hword 0x1a80, 0xee54, 0x4a00, 0xee55\n"
        ".hword 0x1a00, 0xee02, 0x2a80, 0xee05\n"
        ".hword 0x1a01, 0xedc0, 0x4a06, 0xedc0\n"
        ".hword 0x1a02, 0xed80, 0x2a05, 0xed80\n"
        ".hword 0x6a08, 0xed80, 0x300c, 0xe580\n"
        ".hword 0x301c, 0xe580, 0x302c, 0xe580\n"
        ".hword 0x3030, 0xe580, 0x3034, 0xe580\n"
        ".hword 0x3038, 0xe5a0, 0x0a1a, 0xeddf\n"
        ".hword 0x1004, 0xe580, 0x0060, 0xe594\n"
        ".hword 0x0a17, 0xed94, 0x5004, 0xe28d\n"
        ".hword 0x1018, 0xe284, 0x1a0b, 0xed90\n"
        ".hword 0x200d, 0xe1a0, 0x0a01, 0xee30\n"
        ".hword 0x0a17, 0xed84, 0x1a0b, 0xed90\n"
        ".hword 0x0001, 0xe1a0, 0x1a20, 0xee31\n"
        ".hword 0x0a01, 0xee20, 0x0a17, 0xed84\n"
        ".hword 0x0a00, 0xed8d, 0x0a02, 0xec85\n"
        ".hword 0xda81, 0xebfb, 0xd00c, 0xe28d\n"
        ".hword 0x8b02, 0xecbd, 0x83f0, 0xe8bd\n"
        ".hword 0x0000, 0x43b4, 0x0000, 0x43b4\n"
        ".hword 0x0000, 0x0000, 0x0b61, 0x3f36\n"
        ".hword 0x0000, 0x4780, 0x0000, 0x4780\n"
        ".hword 0x7fc0, 0x0040, 0x0000, 0x3f80\n"
    );
}

// DECOMP_FUNC(0x001a7898, 928)
extern "C" __attribute__((naked)) void ui_func_001a7898() {
    asm volatile(
        ".arm\n"
        ".hword 0x4070, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x8b0a, 0xed2d, 0x765b, 0xeb04\n"
        ".hword 0x5000, 0xe1a0, 0x0017, 0xe5d4\n"
        ".hword 0x635c, 0xe59f, 0x0ad2, 0xeddf\n"
        ".hword 0xcad2, 0xed9f, 0x8ad2, 0xeddf\n"
        ".hword 0xaad2, 0xeddf, 0x8ad3, 0xed9f\n"
        ".hword 0x0000, 0xe350, 0x004c, 0x0a00\n"
        ".hword 0x1a04, 0xed95, 0x2a01, 0xed95\n"
        ".hword 0x0a06, 0xed95, 0x1a03, 0xedd5\n"
        ".hword 0x1a42, 0xee31, 0x0a61, 0xee30\n"
        ".hword 0x1a01, 0xee61, 0x1a08, 0xee48\n"
        ".hword 0x1a00, 0xee40, 0x2ae1, 0xeeb1\n"
        ".hword 0x1a82, 0xeeca, 0x9a21, 0xee61\n"
        ".hword 0x9a21, 0xee20, 0xaa21, 0xee28\n"
        ".hword 0x0a29, 0xee28, 0x0a0a, 0xee08\n"
        ".hword 0x0a89, 0xee08, 0x0a10, 0xee10\n"
        ".hword 0x05fe, 0xe350, 0x8a0a, 0x0d84\n"
        ".hword 0x000f, 0x0a00, 0x0a10, 0xee10\n"
        ".hword 0x0006, 0xe150, 0x0a0a, 0x0dc4\n"
        ".hword 0x000b, 0x0a00, 0x8326, 0xeb03\n"
        ".hword 0x0a0c, 0xee20, 0x0a48, 0xeef0\n"
        ".hword 0x0a0a, 0xed84, 0x0aa9, 0xee28\n"
        ".hword 0x0ac9, 0xee00, 0x8ac0, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x0002, 0xda00\n"
        ".hword 0x0a0a, 0xed94, 0x0a40, 0xeeb1\n"
        ".hword 0x0a0a, 0xed84, 0x0a06, 0xed94\n"
        ".hword 0x1a01, 0xedd5, 0x0a08, 0xedd4\n"
        ".hword 0x1a03, 0xed95, 0x0a61, 0xee30\n"
        ".hword 0x1ac1, 0xee30, 0x0a00, 0xee60\n"
        ".hword 0x1a60, 0xeef0, 0x0a08, 0xee48\n"
        ".hword 0x1a08, 0xee48, 0x0a01, 0xee41\n"
        ".hword 0x1a01, 0xee41, 0x8ae1, 0xeef1\n"
        ".hword 0x1ae0, 0xeef1, 0x0aa1, 0xeeca\n"
        ".hword 0x0a20, 0xee20, 0x1a20, 0xee68\n"
        ".hword 0x0a20, 0xee61, 0x0a29, 0xee20\n"
        ".hword 0x0a8a, 0xee01, 0x0a89, 0xee00\n"
        ".hword 0x0a10, 0xee10, 0x05fe, 0xe350\n"
        ".hword 0x0a10, 0x1e10, 0x0006, 0x1150\n"
        ".hword 0x8a80, 0x1e68, 0x1a0a, 0xed95\n"
        ".hword 0x1a91, 0xeddf, 0x0a91, 0xeddf\n"
        ".hword 0x0a91, 0xed9f, 0x1a21, 0xee21\n"
        ".hword 0x0a20, 0xee61, 0x0a80, 0xee20\n"
        ".hword 0x828d, 0xeb03, 0x1a8d, 0xed9f\n"
        ".hword 0x0a00, 0xeec1, 0x0aa0, 0xee88\n"
        ".hword 0x0a09, 0xed84, 0x8b0a, 0xecbd\n"
        ".hword 0x8070, 0xe8bd, 0x0a0b, 0xed94\n"
        ".hword 0x1a87, 0xed9f, 0x000c, 0xe285\n"
        ".hword 0x0a01, 0xee20, 0x0a0b, 0xed84\n"
        ".hword 0x2a01, 0xed95, 0x0a06, 0xed95\n"
        ".hword 0x1a02, 0xec90, 0x9a41, 0xee30\n"
        ".hword 0x9ac2, 0xee71, 0x0aa9, 0xee29\n"
        ".hword 0x0a08, 0xee08, 0x0a09, 0xee09\n"
        ".hword 0xbac0, 0xeef1, 0x0aab, 0xee8a\n"
        ".hword 0xaa80, 0xee69, 0xba00, 0xee28\n"
        ".hword 0xaa00, 0xee29, 0x0a2a, 0xee28\n"
        ".hword 0x0a0b, 0xee08, 0x0a8a, 0xee08\n"
        ".hword 0x0a10, 0xee10, 0x05fe, 0xe350\n"
        ".hword 0x0a48, 0x0eb0, 0x000e, 0x0a00\n"
        ".hword 0x0a10, 0xee10, 0x0006, 0xe150\n"
        ".hword 0x0a0a, 0x0dc4, 0x000b, 0x0a00\n"
        ".hword 0x82d5, 0xeb03, 0x0a0c, 0xee20\n"
        ".hword 0x0a48, 0xeef0, 0x0a0a, 0xed84\n"
        ".hword 0x0aaa, 0xee28, 0x0aca, 0xee00\n"
        ".hword 0x0ac0, 0xeef4, 0xfa10, 0xeef1\n"
        ".hword 0x0a0a, 0xcd94, 0x0a40, 0xceb1\n"
        ".hword 0x0000, 0xda00, 0x0a0a, 0xed84\n"
        ".hword 0x0180, 0xe59f, 0xca48, 0xeef0\n"
        ".hword 0x1b01, 0xe280, 0x0a00, 0xedd0\n"
        ".hword 0x1a02, 0xedd0, 0x0a01, 0xed90\n"
        ".hword 0x1a03, 0xed90, 0x0aa1, 0xee4c\n"
        ".hword 0x2a01, 0xedd1, 0x0a81, 0xee0c\n"
        ".hword 0x1a00, 0xed91, 0x2a02, 0xed91\n"
        ".hword 0x1a03, 0xedd1, 0x0010, 0xe595\n"
        ".hword 0x1ac2, 0xee1c, 0x2aa1, 0xee4c\n"
        ".hword 0x0018, 0xe584, 0x1a60, 0xeef0\n"
        ".hword 0x2a60, 0xeeb0, 0x3a40, 0xeeb0\n"
        ".hword 0x4a82, 0xee61, 0x1a40, 0xeef0\n"
        ".hword 0x2a40, 0xeeb0, 0x5a20, 0xee23\n"
        ".hword 0x3a22, 0xee63, 0x4a41, 0xeeb1\n"
        ".hword 0x1a82, 0xee61, 0x2a60, 0xeeb0\n"
        ".hword 0x0aa2, 0xee60, 0x8aa9, 0xee63\n"
        ".hword 0x2a03, 0xee22, 0x3a22, 0xee20\n"
        ".hword 0x0a64, 0xeeb0, 0x2a45, 0xeef0\n"
        ".hword 0x0a81, 0xee01, 0x1a81, 0xee44\n"
        ".hword 0x2a01, 0xee52, 0x2a01, 0xee15\n"
        ".hword 0x1a60, 0xeeb0, 0xca29, 0xee21\n"
        ".hword 0x9a29, 0xee64, 0x8a88, 0xee42\n"
        ".hword 0xca88, 0xee01, 0x9a88, 0xee40\n"
        ".hword 0x8a09, 0xee40, 0xca09, 0xee02\n"
        ".hword 0x9a09, 0xee43, 0xa802, 0xeb00\n"
        ".hword 0x0000, 0xe350, 0xca07, 0x1dc4\n"
        ".hword 0x0003, 0x1a00, 0x0a05, 0xed95\n"
        ".hword 0x0a2d, 0xeddf, 0x0a60, 0xee30\n"
        ".hword 0x0a07, 0xed84, 0x0018, 0xe595\n"
        ".hword 0x0020, 0xe584, 0x0a0b, 0xed94\n"
        ".hword 0x1a06, 0xedd4, 0x0a00, 0xee6c\n"
        ".hword 0x1a80, 0xee29, 0x0a80, 0xee28\n"
        ".hword 0x0a80, 0xee31, 0x0a06, 0xed84\n"
        ".hword 0x0a07, 0xed94, 0x0a20, 0xee30\n"
        ".hword 0x0a07, 0xed84, 0x0a08, 0xed94\n"
        ".hword 0x0a01, 0xee30, 0x0a08, 0xed84\n"
        ".hword 0x0a0c, 0xed94, 0x1a06, 0xedd4\n"
        ".hword 0x0a40, 0xeeb1, 0x1a00, 0xee2b\n"
        ".hword 0x0a00, 0xee6a, 0x0a80, 0xee2a\n"
        ".hword 0x0a80, 0xee31, 0x0a06, 0xed84\n"
        ".hword 0x0a07, 0xed94, 0x0a01, 0xee30\n"
        ".hword 0x0a07, 0xed84, 0x0a08, 0xed94\n"
        ".hword 0x0a20, 0xee30, 0x0a08, 0xed84\n"
        ".hword 0x0a0c, 0xed94, 0x8ac0, 0xee7b\n"
        ".hword 0xff71, 0xeaff, 0x0000, 0x4300\n"
        ".hword 0xf983, 0x4222, 0x0000, 0xbf80\n"
        ".hword 0x0000, 0x3f80, 0x0000, 0xbf80\n"
        ".hword 0x0000, 0x0000, 0x0000, 0x3f00\n"
        ".hword 0x0b61, 0x3bb6, 0x0fdb, 0x4049\n"
        ".hword 0x0000, 0x42f0, 0xcccd, 0x3dcc\n"
        ".hword 0x7fc0, 0x0040, 0x0000, 0x42dc\n"
    );
}

// DECOMP_FUNC(0x002ed03c, 932)
extern "C" __attribute__((naked)) void func_002ed03c() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff3, 0xe92d, 0x0000, 0xe3e0\n"
        ".hword 0x2000, 0xe3a0, 0x8000, 0xe1a0\n"
        ".hword 0x9002, 0xe1a0, 0x735c, 0xe59f\n"
        ".hword 0x535c, 0xe59f, 0xc35c, 0xe59f\n"
        ".hword 0x8b0a, 0xed2d, 0xd004, 0xe24d\n"
        ".hword 0x1030, 0xe59d, 0x0a03, 0xecd1\n"
        ".hword 0x102c, 0xe59d, 0x8a00, 0xed91\n"
        ".hword 0x0a01, 0xed91, 0x8a02, 0xedd1\n"
        ".hword 0x03d0, 0xe587, 0xca48, 0xeeb0\n"
        ".hword 0xca40, 0xeef0, 0xba68, 0xeef0\n"
        ".hword 0x03d4, 0xe587, 0x1004, 0xe595\n"
        ".hword 0x0000, 0xe351, 0x0008, 0xda00\n"
        ".hword 0x0001, 0xe24c, 0x0001, 0xe311\n"
        ".hword 0x2001, 0x15e0, 0x10c1, 0xe1b0\n"
        ".hword 0x0003, 0x0a00, 0x2001, 0xe5c0\n"
        ".hword 0x1001, 0xe251, 0x2002, 0xe5e0\n"
        ".hword 0xfffb, 0x1aff, 0x1008, 0xe595\n"
        ".hword 0x42f4, 0xe59f, 0x0000, 0xe351\n"
        ".hword 0x0008, 0xda00, 0x0001, 0xe244\n"
        ".hword 0x0001, 0xe311, 0x2001, 0x15e0\n"
        ".hword 0x10c1, 0xe1b0, 0x0003, 0x0a00\n"
        ".hword 0x2001, 0xe5c0, 0x1001, 0xe251\n"
        ".hword 0x2002, 0xe5e0, 0xfffb, 0x1aff\n"
        ".hword 0x000c, 0xe595, 0xb2c4, 0xe59f\n"
        ".hword 0x0000, 0xe350, 0x0009, 0xda00\n"
        ".hword 0x0001, 0xe310, 0x0001, 0xe24b\n"
        ".hword 0x2001, 0x15e0, 0x100c, 0xe595\n"
        ".hword 0x10c1, 0xe1b0, 0x0003, 0x0a00\n"
        ".hword 0x2001, 0xe5c0, 0x1001, 0xe251\n"
        ".hword 0x2002, 0xe5e0, 0xfffb, 0x1aff\n"
        ".hword 0x0010, 0xe595, 0x3290, 0xe59f\n"
        ".hword 0x0000, 0xe350, 0x0009, 0xda00\n"
        ".hword 0x0001, 0xe310, 0x0001, 0xe243\n"
        ".hword 0x2001, 0x15e0, 0x1010, 0xe595\n"
        ".hword 0x10c1, 0xe1b0, 0x0003, 0x0a00\n"
        ".hword 0x2001, 0xe5c0, 0x1001, 0xe251\n"
        ".hword 0x2002, 0xe5e0, 0xfffb, 0x1aff\n"
        ".hword 0x2a60, 0xee78, 0x2a41, 0xee30\n"
        ".hword 0x0ae1, 0xee78, 0x1254, 0xe59f\n"
        ".hword 0x1aa2, 0xee22, 0x1a02, 0xee02\n"
        ".hword 0x1aa0, 0xee00, 0x0ac1, 0xeef1\n"
        ".hword 0x0a90, 0xee10, 0x0000, 0xe151\n"
        ".hword 0x0001, 0xc3a0, 0x0064, 0xca00\n"
        ".hword 0x6000, 0xe3a0, 0x0a8c, 0xeddf\n"
        ".hword 0xaa8c, 0xed9f, 0xa001, 0xe3a0\n"
        ".hword 0x9a20, 0xee30, 0xba8a, 0xed9f\n"
        ".hword 0x0050, 0xea00, 0x0000, 0xe356\n"
        ".hword 0x6001, 0x03a0, 0xfffc, 0x0aff\n"
        ".hword 0x0001, 0xe356, 0x6002, 0x03a0\n"
        ".hword 0xfff9, 0x0aff, 0x01e8, 0xe59f\n"
        ".hword 0x0002, 0xe356, 0x5000, 0xe3a0\n"
        ".hword 0x700c, 0x05b0, 0x4014, 0x0590\n"
        ".hword 0x7010, 0x15b0, 0x4014, 0x1590\n"
        ".hword 0x0000, 0xe357, 0x0041, 0xda00\n"
        ".hword 0x0008, 0xe5d4, 0x0000, 0xe350\n"
        ".hword 0x003a, 0x0a00, 0x0a03, 0xedd4\n"
        ".hword 0x0a04, 0xed94, 0x1a05, 0xed94\n"
        ".hword 0x0a20, 0xee68, 0x0a00, 0xee49\n"
        ".hword 0x0a06, 0xed94, 0x0a81, 0xee48\n"
        ".hword 0x9ac0, 0xee70, 0x0a4a, 0xeeb0\n"
        ".hword 0xaae9, 0xeef0, 0x0aea, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x002d, 0xda00\n"
        ".hword 0x1a4a, 0xeef0, 0x1a68, 0xeeb0\n"
        ".hword 0x0a49, 0xeef0, 0x0a48, 0xeeb0\n"
        ".hword 0x20d5, 0xe1d4, 0x10d4, 0xe1d4\n"
        ".hword 0x3004, 0xe1a0, 0x000d, 0xe1a0\n"
        ".hword 0x0712, 0xebfe, 0x0a00, 0xed9d\n"
        ".hword 0xbac0, 0xeeb4, 0xfa10, 0xeef1\n"
        ".hword 0x0020, 0xca00, 0x000c, 0xe284\n"
        ".hword 0x0a03, 0xecd0, 0x0004, 0xe5d4\n"
        ".hword 0x0aa9, 0xee60, 0x1a29, 0xee21\n"
        ".hword 0x1aa9, 0xee61, 0x0001, 0xe350\n"
        ".hword 0x0a60, 0xee78, 0x1a41, 0xee39\n"
        ".hword 0x1ae1, 0xee78, 0x002a, 0x0a00\n"
        ".hword 0x0002, 0xe356, 0xa005, 0x07cb\n"
        ".hword 0x0002, 0x0a00, 0x0003, 0xe356\n"
        ".hword 0x0124, 0x059f, 0xa005, 0x07c0\n"
        ".hword 0x9acb, 0xeef4, 0xfa10, 0xeef1\n"
        ".hword 0x000c, 0x3a00, 0xaac0, 0xeef4\n"
        ".hword 0xfa10, 0xeef1, 0xaa00, 0xcdcd\n"
        ".hword 0x0a00, 0xed9d, 0x2a03, 0xedd4\n"
        ".hword 0x2a04, 0xed94, 0x3a05, 0xed94\n"
        ".hword 0x2a80, 0xee62, 0x2a00, 0xee22\n"
        ".hword 0x0a00, 0xee23, 0x8aa2, 0xee30\n"
        ".hword 0x9a02, 0xee31, 0x8a80, 0xee71\n"
        ".hword 0x5001, 0xe285, 0x0007, 0xe155\n"
        ".hword 0x40a8, 0xe284, 0xffbd, 0xbaff\n"
        ".hword 0x6001, 0xe286, 0x0004, 0xe356\n"
        ".hword 0xffab, 0xbaff, 0x002c, 0xe59d\n"
        ".hword 0x0a34, 0xed9f, 0x0a40, 0xee39\n"
        ".hword 0x8a00, 0xed80, 0x0a01, 0xed80\n"
        ".hword 0x8a02, 0xedc0, 0x0030, 0xe59d\n"
        ".hword 0xba02, 0xedc0, 0xca02, 0xec80\n"
        ".hword 0x0009, 0xe1a0, 0xd004, 0xe28d\n"
        ".hword 0x8b0a, 0xecbd, 0xd008, 0xe28d\n"
        ".hword 0x8ff0, 0xe8bd, 0x0074, 0xe59f\n"
        ".hword 0x0000, 0xe356, 0x63d0, 0xe5a0\n"
        ".hword 0x5004, 0xe580, 0x006c, 0x059f\n"
        ".hword 0x0002, 0x0a00, 0x0001, 0xe356\n"
        ".hword 0x0064, 0x059f, 0x0000, 0x1a00\n"
        ".hword 0xa005, 0xe7c0, 0x0001, 0xe378\n"
        ".hword 0x0002, 0xda00, 0x0aea, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0xaa00, 0x3dcd\n"
        ".hword 0x000c, 0xe284, 0x0a00, 0xed9d\n"
        ".hword 0x3a05, 0xedd4, 0x9001, 0xe3a0\n"
        ".hword 0x2a02, 0xec90, 0x3a00, 0xee22\n"
        ".hword 0x2a80, 0xee62, 0x2a80, 0xee23\n"
        ".hword 0x8a83, 0xee30, 0x0a4a, 0xeef0\n"
        ".hword 0x9a22, 0xee31, 0x8a82, 0xee71\n"
        ".hword 0x0a60, 0xeeb4, 0xfa10, 0xeef1\n"
        ".hword 0x8005, 0x01a0, 0xffcb, 0xeaff\n"
        ".hword 0xf91c, 0x0049, 0x6fe8, 0x0044\n"
        ".hword 0xe45c, 0x0049, 0xe65c, 0x0049\n"
        ".hword 0xe7dc, 0x0049, 0xe87c, 0x0049\n"
        ".hword 0xd70a, 0x3c23, 0x0000, 0x4170\n"
        ".hword 0x0000, 0x437a, 0x0000, 0x0000\n"
        ".hword 0x0000, 0x41c8\n"
    );
}

// DECOMP_FUNC(0x003c3c24, 936)
extern "C" __attribute__((naked)) void battle_func_003c3c24() {
    asm volatile(
        ".arm\n"
        ".hword 0x41f0, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x6001, 0xe1a0, 0x005c, 0xe591\n"
        ".hword 0x3000, 0xe3a0, 0xd008, 0xe24d\n"
        ".hword 0x2003, 0xe1a0, 0x1073, 0xe3a0\n"
        ".hword 0x62de, 0xebfa, 0x134c, 0xe59f\n"
        ".hword 0x201d, 0xe3a0, 0x0010, 0xe584\n"
        ".hword 0x623d, 0xebfa, 0x0010, 0xe594\n"
        ".hword 0x1001, 0xe3a0, 0x622f, 0xebfa\n"
        ".hword 0x0010, 0xe594, 0x1e33, 0xe28f\n"
        ".hword 0x7bb3, 0xebfa, 0x5b11, 0xe286\n"
        ".hword 0x50a8, 0xe285, 0x0010, 0xe594\n"
        ".hword 0x1000, 0xe595, 0x1004, 0xe201\n"
        ".hword 0x2121, 0xe1a0, 0x1000, 0xe3a0\n"
        ".hword 0x9a40, 0xebf9, 0x1000, 0xe595\n"
        ".hword 0x0010, 0xe594, 0x1008, 0xe201\n"
        ".hword 0x21a1, 0xe1a0, 0x1001, 0xe3a0\n"
        ".hword 0x9a3a, 0xebf9, 0x1000, 0xe595\n"
        ".hword 0x0010, 0xe594, 0x1010, 0xe201\n"
        ".hword 0x2221, 0xe1a0, 0x1002, 0xe3a0\n"
        ".hword 0x9a34, 0xebf9, 0x1000, 0xe595\n"
        ".hword 0x0010, 0xe594, 0x1020, 0xe201\n"
        ".hword 0x22a1, 0xe1a0, 0x1003, 0xe3a0\n"
        ".hword 0x9a2e, 0xebf9, 0x1000, 0xe595\n"
        ".hword 0x0010, 0xe594, 0x1040, 0xe201\n"
        ".hword 0x2321, 0xe1a0, 0x1005, 0xe3a0\n"
        ".hword 0x9a28, 0xebf9, 0x1000, 0xe595\n"
        ".hword 0x0010, 0xe594, 0x1080, 0xe201\n"
        ".hword 0x23a1, 0xe1a0, 0x1006, 0xe3a0\n"
        ".hword 0x9a22, 0xebf9, 0x02a0, 0xe59f\n"
        ".hword 0x7000, 0xe3a0, 0x3007, 0xe1a0\n"
        ".hword 0x0081, 0xe88d, 0x0294, 0xe59f\n"
        ".hword 0x1004, 0xe3a0, 0x2006, 0xe790\n"
        ".hword 0x0010, 0xe594, 0x9a03, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1c01, 0xe201, 0x2421, 0xe1a0\n"
        ".hword 0x1007, 0xe3a0, 0x9a13, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1c02, 0xe201, 0x24a1, 0xe1a0\n"
        ".hword 0x1008, 0xe3a0, 0x9a0d, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1b01, 0xe201, 0x2521, 0xe1a0\n"
        ".hword 0x1009, 0xe3a0, 0x9a07, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1b02, 0xe201, 0x25a1, 0xe1a0\n"
        ".hword 0x100a, 0xe3a0, 0x9a01, 0xebf9\n"
        ".hword 0x0e19, 0xe3a0, 0x0081, 0xe88d\n"
        ".hword 0x021c, 0xe59f, 0x3000, 0xe3a0\n"
        ".hword 0x100b, 0xe3a0, 0x2006, 0xe790\n"
        ".hword 0x0010, 0xe594, 0x99e3, 0xebf9\n"
        ".hword 0x9315, 0xebfb, 0x1204, 0xe59f\n"
        ".hword 0x2000, 0xe590, 0x3000, 0xe3a0\n"
        ".hword 0x0082, 0xe88d, 0x0010, 0xe594\n"
        ".hword 0x100c, 0xe3a0, 0x99db, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1802, 0xe201, 0x28a1, 0xe1a0\n"
        ".hword 0x100d, 0xe3a0, 0x99eb, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1501, 0xe201, 0x2b21, 0xe1a0\n"
        ".hword 0x100e, 0xe3a0, 0x99e5, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1502, 0xe201, 0x2ba1, 0xe1a0\n"
        ".hword 0x100f, 0xe3a0, 0x99df, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1401, 0xe201, 0x2c21, 0xe1a0\n"
        ".hword 0x1010, 0xe3a0, 0x99d9, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1402, 0xe201, 0x2ca1, 0xe1a0\n"
        ".hword 0x1011, 0xe3a0, 0x99d3, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1301, 0xe201, 0x2d21, 0xe1a0\n"
        ".hword 0x1012, 0xe3a0, 0x99cd, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1302, 0xe201, 0x2da1, 0xe1a0\n"
        ".hword 0x1013, 0xe3a0, 0x99c7, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1201, 0xe201, 0x2e21, 0xe1a0\n"
        ".hword 0x1014, 0xe3a0, 0x99c1, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1202, 0xe201, 0x2ea1, 0xe1a0\n"
        ".hword 0x1015, 0xe3a0, 0x99bb, 0xebf9\n"
        ".hword 0x5b11, 0xe286, 0x50ac, 0xe285\n"
        ".hword 0x1016, 0xe3a0, 0x0000, 0xe595\n"
        ".hword 0x0001, 0xe200, 0x0007, 0xe190\n"
        ".hword 0x0010, 0xe594, 0x2001, 0x13a0\n"
        ".hword 0x2000, 0x03a0, 0x99b1, 0xebf9\n"
        ".hword 0x0000, 0xe595, 0x1017, 0xe3a0\n"
        ".hword 0x0002, 0xe200, 0x0007, 0xe190\n"
        ".hword 0x0010, 0xe594, 0x2001, 0x13a0\n"
        ".hword 0x2000, 0x03a0, 0x99a9, 0xebf9\n"
        ".hword 0x80cc, 0xe59f, 0x00cc, 0xe59f\n"
        ".hword 0x7004, 0xe58d, 0x8000, 0xe58d\n"
        ".hword 0x3000, 0xe3e0, 0x2006, 0xe790\n"
        ".hword 0x0010, 0xe594, 0x1018, 0xe3a0\n"
        ".hword 0x998a, 0xebf9, 0x0000, 0xe595\n"
        ".hword 0x1019, 0xe3a0, 0x0004, 0xe200\n"
        ".hword 0x0007, 0xe190, 0x0010, 0xe594\n"
        ".hword 0x2001, 0x13a0, 0x2000, 0x03a0\n"
        ".hword 0x9998, 0xebf9, 0x0004, 0xe3a0\n"
        ".hword 0x6b0b, 0xe286, 0x6fcd, 0xe286\n"
        ".hword 0x0081, 0xe88d, 0x2000, 0xe596\n"
        ".hword 0x0010, 0xe594, 0x3000, 0xe3a0\n"
        ".hword 0x101a, 0xe3a0, 0x9979, 0xebf9\n"
        ".hword 0x106c, 0xe59f, 0x7004, 0xe58d\n"
        ".hword 0x8000, 0xe58d, 0x0010, 0xe594\n"
        ".hword 0x2000, 0xe591, 0x3000, 0xe3e0\n"
        ".hword 0x101b, 0xe3a0, 0x9971, 0xebf9\n"
        ".hword 0x0000, 0xe595, 0x101c, 0xe3a0\n"
        ".hword 0x0040, 0xe200, 0x0007, 0xe190\n"
        ".hword 0x0010, 0xe594, 0xd008, 0xe28d\n"
        ".hword 0x2001, 0x13a0, 0x41f0, 0xe8bd\n"
        ".hword 0x2000, 0x03a0, 0x997d, 0xeaf9\n"
        ".hword 0x46e8, 0x0043, 0x7462, 0x206c\n"
        ".hword 0x6c46, 0x6761, 0x4d20, 0x6e65\n"
        ".hword 0x0075, 0x0000, 0x869f, 0x0001\n"
        ".hword 0x4a50, 0x0000, 0x49c8, 0x0000\n"
        ".hword 0xc9ff, 0x3b9a, 0x03e7, 0x0000\n"
        ".hword 0x2f2c, 0x0000, 0x9ad4, 0x0043\n"
    );
}

// DECOMP_FUNC(0x003655ec, 940)
extern "C" __attribute__((naked)) void engine_func_003655ec() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0xd014, 0xe24d\n"
        ".hword 0x7000, 0xe1a0, 0x0000, 0xe3a0\n"
        ".hword 0x5001, 0xe1a0, 0x0000, 0xe58d\n"
        ".hword 0x1028, 0xe597, 0x0000, 0xe351\n"
        ".hword 0x1004, 0xe58d, 0x002a, 0x0a00\n"
        ".hword 0x4008, 0xe597, 0x8000, 0xe3a0\n"
        ".hword 0x00e0, 0xe284, 0x10e0, 0xe594\n"
        ".hword 0x0000, 0xe351, 0xb000, 0x1081\n"
        ".hword 0x0220, 0xe597, 0xb008, 0x01a0\n"
        ".hword 0x1000, 0xe590, 0x100c, 0xe591\n"
        ".hword 0xff31, 0xe12f, 0x0220, 0xe597\n"
        ".hword 0x1000, 0xe590, 0x102c, 0xe591\n"
        ".hword 0xff31, 0xe12f, 0x0008, 0xe58d\n"
        ".hword 0x1028, 0xe594, 0x6000, 0xe3a0\n"
        ".hword 0x0000, 0xe351, 0x202c, 0xc594\n"
        ".hword 0x0014, 0xda00, 0x0000, 0xe352\n"
        ".hword 0x002c, 0xe284, 0x0002, 0x1080\n"
        ".hword 0x0008, 0x01a0, 0x0000, 0xe350\n"
        ".hword 0xa000, 0x03a0, 0x0004, 0x0a00\n"
        ".hword 0x0206, 0xe080, 0x3028, 0xe5b0\n"
        ".hword 0x0000, 0xe353, 0xa000, 0x1083\n"
        ".hword 0xa008, 0x01a0, 0x0004, 0xe59a\n"
        ".hword 0x300c, 0xe59a, 0x0001, 0xe210\n"
        ".hword 0x0001, 0x0a00, 0x0001, 0xe353\n"
        ".hword 0x0005, 0x0a00, 0x6001, 0xe286\n"
        ".hword 0x0001, 0xe156, 0xffea, 0xbaff\n"
        ".hword 0x0000, 0xe59d, 0xd014, 0xe28d\n"
        ".hword 0x8ff0, 0xe8bd, 0x00ff, 0xe3c0\n"
        ".hword 0x9001, 0xe380, 0x0000, 0xe595\n"
        ".hword 0x4005, 0xe1a0, 0x2004, 0xe3a0\n"
        ".hword 0x1068, 0xe3a0, 0x3008, 0xe590\n"
        ".hword 0x0005, 0xe1a0, 0xff33, 0xe12f\n"
        ".hword 0x0000, 0xe350, 0x0018, 0x0a00\n"
        ".hword 0x2007, 0xe1a0, 0x3004, 0xe1a0\n"
        ".hword 0x100a, 0xe1a0, 0x480c, 0xebfb\n"
        ".hword 0x5000, 0xe1a0, 0x1079, 0xe6af\n"
        ".hword 0x4491, 0xebfb, 0x0102, 0xe210\n"
        ".hword 0xf000, 0xe320, 0x0003, 0x4a00\n"
        ".hword 0x0000, 0xe355, 0x0000, 0x159d\n"
        ".hword 0x000f, 0x1a00, 0x000b, 0xea00\n"
        ".hword 0x0000, 0xe355, 0x0008, 0x0a00\n"
        ".hword 0x0000, 0xe595, 0x1000, 0xe590\n"
        ".hword 0x0005, 0xe1a0, 0xff31, 0xe12f\n"
        ".hword 0x0004, 0xe595, 0x1000, 0xe590\n"
        ".hword 0x200c, 0xe591, 0x1005, 0xe1a0\n"
        ".hword 0xff32, 0xe12f, 0x5008, 0xe1a0\n"
        ".hword 0x0000, 0xe59d, 0x0102, 0xe380\n"
        ".hword 0x0000, 0xe58d, 0x1fa0, 0xe1b0\n"
        ".hword 0xffd3, 0x1aff, 0x0008, 0xe595\n"
        ".hword 0x4000, 0xe3a0, 0xa010, 0xe590\n"
        ".hword 0x0000, 0xe35a, 0x0047, 0xda00\n"
        ".hword 0x0008, 0xe595, 0x1014, 0xe5b0\n"
        ".hword 0x0000, 0xe351, 0x0001, 0x1080\n"
        ".hword 0x0000, 0x03a0, 0x0000, 0xe350\n"
        ".hword 0x0004, 0x0a00, 0x0204, 0xe080\n"
        ".hword 0x1028, 0xe5b0, 0x0000, 0xe351\n"
        ".hword 0x8000, 0x1081, 0x0000, 0x1a00\n"
        ".hword 0x8000, 0xe3a0, 0x0004, 0xe288\n"
        ".hword 0x1004, 0xe598, 0x0000, 0xe351\n"
        ".hword 0x9000, 0x1081, 0x101c, 0xe59b\n"
        ".hword 0x9000, 0x03a0, 0x001c, 0xe28b\n"
        ".hword 0x0000, 0xe351, 0x0001, 0x1080\n"
        ".hword 0x0000, 0x03a0, 0x0000, 0xe350\n"
        ".hword 0x100c, 0xe28d, 0x0000, 0x1359\n"
        ".hword 0x000c, 0xe58d, 0x1010, 0xe58d\n"
        ".hword 0x000c, 0x0a00, 0x0009, 0xe1a0\n"
        ".hword 0x76a3, 0xebfd, 0x2000, 0xe1a0\n"
        ".hword 0x0010, 0xe59d, 0x1009, 0xe1a0\n"
        ".hword 0x7675, 0xebfd, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0003, 0x0a00\n"
        ".hword 0x100c, 0xe5b0, 0x0000, 0xe351\n"
        ".hword 0x0001, 0x1080, 0x0000, 0x1a00\n"
        ".hword 0x0000, 0xe3a0, 0x1024, 0xe595\n"
        ".hword 0x2008, 0xe59d, 0x0008, 0xe590\n"
        ".hword 0x0104, 0xe781, 0x1000, 0xe592\n"
        ".hword 0x201c, 0xe5b1, 0x0000, 0xe352\n"
        ".hword 0x1002, 0x1081, 0x1000, 0x03a0\n"
        ".hword 0x0000, 0xe351, 0x0004, 0x0a00\n"
        ".hword 0x0200, 0xe081, 0x1028, 0xe5b0\n"
        ".hword 0x0000, 0xe351, 0x0001, 0x1080\n"
        ".hword 0x0000, 0x1a00, 0x0000, 0xe3a0\n"
        ".hword 0x2054, 0xe595, 0x0020, 0xe280\n"
        ".hword 0x0104, 0xe782, 0x0010, 0xe598\n"
        ".hword 0x0000, 0xe350, 0x0000, 0x13a0\n"
        ".hword 0x0011, 0x0a00, 0x1034, 0xe595\n"
        ".hword 0x0104, 0xe781, 0x4001, 0xe284\n"
        ".hword 0x000a, 0xe154, 0xffb7, 0xbaff\n"
        ".hword 0x0004, 0xe59d, 0x1f8a, 0xe287\n"
        ".hword 0x000c, 0xe590, 0x5106, 0xe780\n"
        ".hword 0x00d4, 0xe59f, 0x0060, 0xe881\n"
        ".hword 0x1005, 0xe1a0, 0x20d7, 0xe190\n"
        ".hword 0x0007, 0xe1a0, 0xccde, 0xebf7\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0xff78, 0xeaff, 0x001c, 0xe5b8\n"
        ".hword 0x0000, 0xe350, 0x8000, 0x1088\n"
        ".hword 0x0008, 0xe597, 0x8000, 0x03a0\n"
        ".hword 0x0000, 0xe350, 0x0003, 0x0a00\n"
        ".hword 0x2000, 0xe590, 0x1094, 0xe59f\n"
        ".hword 0x1002, 0xe1d1, 0x0000, 0x13a0\n"
        ".hword 0x9010, 0xe28d, 0x10e0, 0xe5b0\n"
        ".hword 0x0000, 0xe351, 0x0001, 0x1080\n"
        ".hword 0x0000, 0x03a0, 0x101c, 0xe5b0\n"
        ".hword 0x0000, 0xe351, 0x0001, 0x1080\n"
        ".hword 0x0000, 0x03a0, 0x0000, 0xe350\n"
        ".hword 0x0000, 0x1358, 0x0010, 0xe58d\n"
        ".hword 0x000c, 0x0a00, 0x0008, 0xe1a0\n"
        ".hword 0x7653, 0xebfd, 0x2000, 0xe1a0\n"
        ".hword 0x1008, 0xe1a0, 0x0009, 0xe1a0\n"
        ".hword 0x7625, 0xebfd, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0003, 0x0a00\n"
        ".hword 0x100c, 0xe5b0, 0x0000, 0xe351\n"
        ".hword 0x0001, 0x1080, 0x0000, 0x1a00\n"
        ".hword 0x0000, 0xe3a0, 0x8008, 0xe590\n"
        ".hword 0x0220, 0xe597, 0x1000, 0xe590\n"
        ".hword 0x100c, 0xe591, 0xff31, 0xe12f\n"
        ".hword 0x0004, 0xe590, 0x0308, 0xe080\n"
        ".hword 0xffbf, 0xeaff, 0x0231, 0x0000\n"
        ".hword 0x0092, 0x4000\n"
    );
}

// DECOMP_FUNC(0x00194a08, 948)
extern "C" __attribute__((naked)) void camp_func_00194a08() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0x0330, 0xe59f\n"
        ".hword 0x4000, 0xe3a0, 0x8b02, 0xed2d\n"
        ".hword 0xd094, 0xe24d, 0x5000, 0xe590\n"
        ".hword 0x0fb7, 0xe285, 0x23ae, 0xeb04\n"
        ".hword 0x0000, 0xe350, 0x00a2, 0xda00\n"
        ".hword 0xb00b, 0xe3a0, 0x8ac3, 0xeddf\n"
        ".hword 0x8ac3, 0xed9f, 0x8c03, 0xe285\n"
        ".hword 0x0184, 0xe064, 0x0100, 0xe080\n"
        ".hword 0x0100, 0xe085, 0x0020, 0xe280\n"
        ".hword 0xa949, 0xeb04, 0x0000, 0xe354\n"
        ".hword 0x9000, 0xe1a0, 0x0006, 0x1a00\n"
        ".hword 0x0000, 0xe3a0, 0x2000, 0xe1a0\n"
        ".hword 0x0801, 0xe88d, 0x3009, 0xe1a0\n"
        ".hword 0x1030, 0xe3a0, 0x0002, 0xe3a0\n"
        ".hword 0xaab6, 0xeb04, 0x0fb7, 0xe285\n"
        ".hword 0x2397, 0xeb04, 0x0001, 0xe240\n"
        ".hword 0x0004, 0xe150, 0x0017, 0x1a00\n"
        ".hword 0x14fa, 0xe1d8, 0x04f8, 0xe1d8\n"
        ".hword 0x6020, 0xe28d, 0xc000, 0xe3a0\n"
        ".hword 0x1803, 0xe886, 0x2006, 0xe3a0\n"
        ".hword 0x3004, 0xe3a0, 0x04fc, 0xe1d8\n"
        ".hword 0xe00c, 0xe28d, 0x3014, 0xe58d\n"
        ".hword 0x2018, 0xe58d, 0x001c, 0xe58d\n"
        ".hword 0xa005, 0xe3a0, 0x1003, 0xe3a0\n"
        ".hword 0x0402, 0xe88e, 0xc009, 0xe3a0\n"
        ".hword 0x7008, 0xe3a0, 0x6007, 0xe3a0\n"
        ".hword 0x3030, 0xe3a0, 0x2000, 0xe3a0\n"
        ".hword 0x1009, 0xe1a0, 0x0fb7, 0xe285\n"
        ".hword 0x10c0, 0xe88d, 0xf051, 0xeb03\n"
        ".hword 0x1015, 0xe284, 0x0030, 0xe3a0\n"
        ".hword 0xaaf4, 0xeb04, 0x6000, 0xe1a0\n"
        ".hword 0x00fa, 0xe1d0, 0x2001, 0xe3a0\n"
        ".hword 0x1030, 0xe3a0, 0x0801, 0xe88d\n"
        ".hword 0x00f8, 0xe1d6, 0x3009, 0xe080\n"
        ".hword 0x0002, 0xe3a0, 0xaa8d, 0xeb04\n"
        ".hword 0x0fb7, 0xe285, 0xf000, 0xe320\n"
        ".hword 0x29cc, 0xeb04, 0x721c, 0xe59f\n"
        ".hword 0x0004, 0xe080, 0x1000, 0xe3a0\n"
        ".hword 0x0080, 0xe085, 0x70f7, 0xe190\n"
        ".hword 0x0037, 0xe3a0, 0xb0de, 0xeb04\n"
        ".hword 0x0000, 0xe58d, 0xf000, 0xe320\n"
        ".hword 0xb0d1, 0xeb04, 0xa000, 0xe1a0\n"
        ".hword 0x0000, 0xe59d, 0xb0ba, 0xeb04\n"
        ".hword 0x0000, 0xe157, 0xf000, 0xe320\n"
        ".hword 0x004d, 0x2a00, 0x7307, 0xe09a\n"
        ".hword 0x004b, 0x0a00, 0x1013, 0xe3a0\n"
        ".hword 0x0030, 0xe3a0, 0xaad3, 0xeb04\n"
        ".hword 0xa000, 0xe1a0, 0x2002, 0xe287\n"
        ".hword 0x1f71, 0xe28f, 0x0030, 0xe28d\n"
        ".hword 0xa719, 0xfa04, 0x00f8, 0xe1d6\n"
        ".hword 0x20f8, 0xe1da, 0x30fa, 0xe1d6\n"
        ".hword 0x10fa, 0xe1da, 0x2000, 0xe082\n"
        ".hword 0x1a48, 0xeeb0, 0x0001, 0xe083\n"
        ".hword 0x1009, 0xe082, 0x0a90, 0xee00\n"
        ".hword 0x1a10, 0xee00, 0x2a68, 0xeeb0\n"
        ".hword 0x1a41, 0xeef0, 0x118c, 0xe59f\n"
        ".hword 0x2030, 0xe28d, 0x0ae0, 0xeef8\n"
        ".hword 0x0ac0, 0xeeb8, 0x0002, 0xe3a0\n"
        ".hword 0xa6e7, 0xeb04, 0x1014, 0xe3a0\n"
        ".hword 0x0030, 0xe3a0, 0xaab9, 0xeb04\n"
        ".hword 0xa000, 0xe1a0, 0x003f, 0xe5d7\n"
        ".hword 0x0001, 0xe350, 0x0033, 0x0a00\n"
        ".hword 0x0037, 0xe5d7, 0x0030, 0xe350\n"
        ".hword 0x0fb7, 0xe285, 0x005b, 0x0a00\n"
        ".hword 0x2994, 0xeb04, 0x0004, 0xe080\n"
        ".hword 0x0080, 0xe085, 0x0b01, 0xe280\n"
        ".hword 0x02f4, 0xe1d0, 0x0100, 0xe085\n"
        ".hword 0x135c, 0xe590, 0x0070, 0xe28d\n"
        ".hword 0xef8e, 0xeb03, 0x3037, 0xe287\n"
        ".hword 0x2070, 0xe28d, 0x1e12, 0xe28f\n"
        ".hword 0x0030, 0xe28d, 0xa6ee, 0xfa04\n"
        ".hword 0x1002, 0xe3a0, 0x0030, 0xe28d\n"
        ".hword 0x8932, 0xeb04, 0x200c, 0xe59a\n"
        ".hword 0x10f8, 0xe1da, 0x30f8, 0xe1d6\n"
        ".hword 0x2a68, 0xeeb0, 0x20f0, 0xe1d2\n"
        ".hword 0x1002, 0xe081, 0x0000, 0xe041\n"
        ".hword 0x10fa, 0xe1da, 0x20fa, 0xe1d6\n"
        ".hword 0xc000, 0xe089, 0x0001, 0xe082\n"
        ".hword 0x100c, 0xe083, 0x0a10, 0xee00\n"
        ".hword 0x1a10, 0xee01, 0x2030, 0xe28d\n"
        ".hword 0x10ff, 0xe3a0, 0x0002, 0xe3a0\n"
        ".hword 0x0ac0, 0xeef8, 0x0ac1, 0xeeb8\n"
        ".hword 0x1a48, 0xeeb0, 0x1a41, 0xeef0\n"
        ".hword 0xa6b5, 0xeb04, 0x4001, 0xe284\n"
        ".hword 0x0fb7, 0xe285, 0x230c, 0xeb04\n"
        ".hword 0x0004, 0xe150, 0xf000, 0xe320\n"
        ".hword 0xff60, 0xcaff, 0xd094, 0xe28d\n"
        ".hword 0x8b02, 0xecbd, 0x8ff0, 0xe8bd\n"
        ".hword 0x0fb7, 0xe285, 0x2963, 0xeb04\n"
        ".hword 0x0004, 0xe080, 0x1088, 0xe59f\n"
        ".hword 0x0080, 0xe085, 0x0b01, 0xe280\n"
        ".hword 0x02f4, 0xe1d0, 0x0100, 0xe085\n"
        ".hword 0x035c, 0xe590, 0x2091, 0xe081\n"
        ".hword 0x20e0, 0xe3e0, 0x15a1, 0xe1a0\n"
        ".hword 0x0291, 0xe003, 0x2064, 0xe59f\n"
        ".hword 0x0203, 0xe080, 0x2092, 0xe080\n"
        ".hword 0x72a0, 0xe1a0, 0x0070, 0xe28d\n"
        ".hword 0xef54, 0xeb03, 0x1007, 0xe1a0\n"
        ".hword 0x7070, 0xe28d, 0x0080, 0xe28d\n"
        ".hword 0xef50, 0xeb03, 0x3010, 0xe287\n"
        ".hword 0x2070, 0xe28d, 0x1038, 0xe28f\n"
        ".hword 0x0030, 0xe28d, 0xa6b0, 0xfa04\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0xffbe, 0xeaff, 0xdd08, 0x0043\n"
        ".hword 0x0000, 0x3f80, 0x0000, 0x0000\n"
        ".hword 0x0424, 0x0000, 0x7325, 0x0000\n"
        ".hword 0x00ff, 0xe098, 0x7325, 0x4081\n"
        ".hword 0x7325, 0x0000, 0xb3c5, 0x91a2\n"
        ".hword 0x8889, 0x8888, 0x7325, 0x6782\n"
        ".hword 0x4081, 0x7325, 0x6c82, 0x0000\n"
        ".hword 0xf000, 0xe320, 0x2937, 0xeb04\n"
        ".hword 0x0004, 0xe080, 0x0080, 0xe085\n"
        ".hword 0x0b01, 0xe280, 0x02f4, 0xe1d0\n"
        ".hword 0x0100, 0xe085, 0x135c, 0xe590\n"
        ".hword 0x0070, 0xe28d, 0xef31, 0xeb03\n"
        ".hword 0x2070, 0xe28d, 0x1058, 0xe24f\n"
        ".hword 0x0030, 0xe28d, 0xa692, 0xfa04\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0xffa0, 0xeaff\n"
    );
}

// End of Batch 45 B.
