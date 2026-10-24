#include <cstdint>

using u32 = uint32_t;

// Isolated ordinary-C++ reconstruction candidates; deliberately not linked
// into production and not added to the exact-match ledger.
extern "C" __attribute__((noinline, used)) u32 candidate_00130fe8(
    u32 ignored_r0, u32 value) {
    (void)ignored_r0;
    return (value + 1u) * 0x144u;
}

extern "C" __attribute__((noinline, used)) void candidate_0015c408(
    volatile u32* object, u32 first, u32 delta) {
    object[7] = first;
    object[8] = first + delta;
}

extern "C" __attribute__((noinline, used)) u32 candidate_002a17d4(
    const volatile u32* object) {
    return (object[0x754 / 4] >> 16) & 1u;
}

// Targeted negative controls. Each is intentionally wrong in one observed
// detail and must be caught by differential execution.
extern "C" __attribute__((noinline, used)) u32 wrong_increment_00130fe8(
    u32 ignored_r0, u32 value) {
    (void)ignored_r0;
    return (value + 2u) * 0x144u;
}

extern "C" __attribute__((noinline, used)) void wrong_store_offset_0015c408(
    volatile u32* object, u32 first, u32 delta) {
    object[7] = first;
    object[9] = first + delta;
}

extern "C" __attribute__((noinline, used)) u32 wrong_bit_002a17d4(
    const volatile u32* object) {
    return (object[0x754 / 4] >> 17) & 1u;
}
