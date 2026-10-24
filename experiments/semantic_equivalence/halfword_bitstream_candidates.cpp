#include <cstdint>

// These are source-level semantic models, not direct drop-in replacements.
// The original uses a private register ABI (inputs in r1/r2/r3, result in r3)
// and writes AAPCS callee-saved r9/r10. These functions expose the accumulator
// through the ordinary C++ return register r0 so their value semantics can be
// tested without pretending that the calling convention is compatible.
static inline __attribute__((always_inline)) uint32_t arm_lsl_register(
    uint32_t value, uint32_t amount) {
    const uint32_t shift = amount & 0xffu;
    if (shift == 0u) return value;
    if (shift < 32u) return value << shift;
    return 0u;
}

static inline __attribute__((always_inline)) uint32_t semantic_halfword_or(
    const volatile uint16_t* stream, uint32_t count, uint32_t accumulator) {
    const uint32_t word = *stream;
    // add r2,#16; rsb sb,r2,#16 is modulo-2^32 negation of incoming r2.
    // ARM register shifts inspect only the low eight bits of the amount.
    const uint32_t amount = 0u - count;
    return accumulator | arm_lsl_register(word, amount);
}

extern "C" __attribute__((noinline, used)) uint32_t candidate_0016e468(
    uint32_t ignored_r0, const volatile uint16_t* stream, uint32_t count,
    uint32_t accumulator) {
    (void)ignored_r0;
    return semantic_halfword_or(stream, count, accumulator);
}

extern "C" __attribute__((noinline, used)) uint32_t candidate_00174a68(
    uint32_t ignored_r0, const volatile uint16_t* stream, uint32_t count,
    uint32_t accumulator) {
    (void)ignored_r0;
    return semantic_halfword_or(stream, count, accumulator);
}

extern "C" __attribute__((noinline, used)) uint32_t candidate_0017b068(
    uint32_t ignored_r0, const volatile uint16_t* stream, uint32_t count,
    uint32_t accumulator) {
    (void)ignored_r0;
    return semantic_halfword_or(stream, count, accumulator);
}

// Deliberately incorrect controls: using the un-negated count and reducing the
// amount modulo 32 both disagree with ARM's register-specified LSL semantics.
extern "C" __attribute__((noinline, used)) uint32_t wrong_sign_0016e468(
    uint32_t, const volatile uint16_t* stream, uint32_t count,
    uint32_t accumulator) {
    return accumulator | arm_lsl_register(*stream, count);
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_width_0016e468(
    uint32_t, const volatile uint16_t* stream, uint32_t count,
    uint32_t accumulator) {
    const uint32_t amount = (0u - count) & 0xffu;
    const uint32_t shift = amount & 31u;
    const uint32_t shifted = shift == 0u ? *stream : uint32_t(*stream) << shift;
    return accumulator | shifted;
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_sign_00174a68(
    uint32_t, const volatile uint16_t* stream, uint32_t count,
    uint32_t accumulator) {
    return accumulator | arm_lsl_register(*stream, count);
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_width_00174a68(
    uint32_t, const volatile uint16_t* stream, uint32_t count,
    uint32_t accumulator) {
    const uint32_t amount = (0u - count) & 0xffu;
    const uint32_t shift = amount & 31u;
    const uint32_t shifted = shift == 0u ? *stream : uint32_t(*stream) << shift;
    return accumulator | shifted;
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_sign_0017b068(
    uint32_t, const volatile uint16_t* stream, uint32_t count,
    uint32_t accumulator) {
    return accumulator | arm_lsl_register(*stream, count);
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_width_0017b068(
    uint32_t, const volatile uint16_t* stream, uint32_t count,
    uint32_t accumulator) {
    const uint32_t amount = (0u - count) & 0xffu;
    const uint32_t shift = amount & 31u;
    const uint32_t shifted = shift == 0u ? *stream : uint32_t(*stream) << shift;
    return accumulator | shifted;
}
