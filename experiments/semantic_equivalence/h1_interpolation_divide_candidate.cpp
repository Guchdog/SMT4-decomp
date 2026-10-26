#include <stdint.h>

namespace {

static uint32_t magnitude_bits(uint32_t value) {
    return (value & 0x80000000u) ? (0u - value) : value;
}

static uint64_t unsigned_divmod(uint32_t numerator, uint32_t denominator) {
    uint32_t quotient = 0;
    uint32_t remainder = 0;

    // Restoring long division. The carry records the 33rd bit of
    // (remainder << 1) so divisors with their high bit set work too.
    for (uint32_t bit = 0; bit < 32; ++bit) {
        const uint32_t shift = 31u - bit;
        const uint32_t carry = remainder >> 31;
        const uint32_t shifted = (remainder << 1) | ((numerator >> shift) & 1u);
        if (carry || shifted >= denominator) {
            remainder = shifted - denominator;
            quotient |= 1u << shift;
        } else {
            remainder = shifted;
        }
    }
    // A uint64_t return on this 32-bit ABI places quotient in r0 and remainder
    // in r1, matching the original helper's two-word result.
    return (static_cast<uint64_t>(remainder) << 32) | quotient;
}

} // namespace

// 0x002C615C returns signed quotient bits in r0 and signed remainder bits in
// r1. Its sign-bit path divides operand magnitudes and reapplies the quotient
// sign; for nonnegative inputs this is ordinary unsigned division. On divisor
// zero, the original hook returns r0=0 and preserves the numerator in r1.
// H1 passes a signed 12-bit-fixed delta and a positive u16 duration.
extern "C" __attribute__((noinline, used)) uint64_t
candidate_002c615c_divmod(int32_t numerator, int32_t denominator) {
    const uint32_t numerator_bits = static_cast<uint32_t>(numerator);
    const uint32_t denominator_bits = static_cast<uint32_t>(denominator);
    if (denominator_bits == 0)
        return static_cast<uint64_t>(numerator_bits) << 32;

    const bool numerator_negative = (numerator_bits & 0x80000000u) != 0;
    const bool denominator_negative = (denominator_bits & 0x80000000u) != 0;
    uint64_t result = unsigned_divmod(magnitude_bits(numerator_bits),
                                      magnitude_bits(denominator_bits));
    uint32_t quotient = static_cast<uint32_t>(result);
    uint32_t remainder = static_cast<uint32_t>(result >> 32);
    if (numerator_negative != denominator_negative)
        quotient = 0u - quotient;
    if (numerator_negative)
        remainder = 0u - remainder;
    result = (static_cast<uint64_t>(remainder) << 32) | quotient;
    return result;
}

// C-callable quotient projection used by callers that consume only r0.
extern "C" __attribute__((noinline, used)) int32_t
candidate_002c615c(int32_t numerator, int32_t denominator) {
    const uint32_t quotient = static_cast<uint32_t>(
        candidate_002c615c_divmod(numerator, denominator));
    return __builtin_bit_cast(int32_t, quotient);
}
