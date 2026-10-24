#include <stdint.h>

using u32 = uint32_t;

// Isolated semantic candidates for four field-equality predicates. These are
// experiments only; they do not alter production sources or the match ledger.
extern "C" __attribute__((noinline, used)) u32 candidate_0014e634(
    const u32* object) {
    return object[0] == 5;
}

extern "C" __attribute__((noinline, used)) u32 candidate_003358e0(
    const uint8_t* object) {
    return *reinterpret_cast<const u32*>(object + 0x0C) == 4;
}

extern "C" __attribute__((noinline, used)) u32 candidate_0034c9e0(
    const uint8_t* object) {
    return *reinterpret_cast<const u32*>(object + 0x2C) == 4;
}

extern "C" __attribute__((noinline, used)) u32 candidate_0034cb7c(
    const uint8_t* object) {
    return *reinterpret_cast<const u32*>(object + 0x2C) != 1;
}

// Targeted negative controls: wrong constants for the equality predicates,
// and inverted sense for the inequality predicate.
extern "C" __attribute__((noinline, used)) u32 wrong_constant_0014e634(
    const u32* object) {
    return object[0] == 4;
}

extern "C" __attribute__((noinline, used)) u32 wrong_constant_003358e0(
    const uint8_t* object) {
    return *reinterpret_cast<const u32*>(object + 0x0C) == 5;
}

extern "C" __attribute__((noinline, used)) u32 wrong_constant_0034c9e0(
    const uint8_t* object) {
    return *reinterpret_cast<const u32*>(object + 0x2C) == 5;
}

extern "C" __attribute__((noinline, used)) u32 wrong_sense_0034cb7c(
    const uint8_t* object) {
    return *reinterpret_cast<const u32*>(object + 0x2C) == 1;
}
