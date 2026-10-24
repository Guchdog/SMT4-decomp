#include <cstdint>

using u32 = uint32_t;

// The pinned routine reads the word at r2, advances r1 by one word, stores
// {1, loaded_word} at the advanced address, and returns 1 in r0.
// Keep accesses volatile so the differential harness can observe the exact
// ordinary-memory read/write footprint and the two stores remain ordered.
extern "C" __attribute__((noinline, used)) u32 candidate_003e89d8(
    u32, volatile u32* destination_base, const volatile u32* source) {
    // Pin the three architecturally visible scratch/result registers to the
    // same values as the leaf: r2 receives the load, r1 is advanced, r0=1.
    register u32 loaded asm("r2") = *source;
    register volatile u32* destination asm("r1") = destination_base;
    destination += 1;
    register u32 result asm("r0") = 1;
    asm volatile("" : "+r"(loaded), "+r"(destination), "+r"(result));
    destination[0] = result;
    destination[1] = loaded;
    return result;
}

extern "C" __attribute__((noinline, used)) u32 candidate_003e8a68(
    u32, volatile u32* destination_base, const volatile u32* source) {
    register u32 loaded asm("r2") = *source;
    register volatile u32* destination asm("r1") = destination_base;
    destination += 1;
    register u32 result asm("r0") = 1;
    asm volatile("" : "+r"(loaded), "+r"(destination), "+r"(result));
    destination[0] = result;
    destination[1] = loaded;
    return result;
}

// Deliberately incorrect controls: each should be caught by the harness.
extern "C" __attribute__((noinline, used)) u32 wrong_destination_offset(
    u32, volatile u32* destination_base, const volatile u32* source) {
    const u32 loaded = *source;
    volatile u32* destination = destination_base + 2;
    destination[0] = 1;
    destination[1] = loaded;
    return 1;
}

extern "C" __attribute__((noinline, used)) u32 wrong_store_order(
    u32, volatile u32* destination_base, const volatile u32* source) {
    const u32 loaded = *source;
    volatile u32* destination = destination_base + 1;
    destination[1] = loaded;
    destination[0] = 1;
    return 1;
}

extern "C" __attribute__((noinline, used)) u32 wrong_second_value(
    u32, volatile u32* destination_base, const volatile u32*) {
    volatile u32* destination = destination_base + 1;
    destination[0] = 1;
    destination[1] = 0;
    return 1;
}

extern "C" __attribute__((noinline, used)) u32 wrong_return_value(
    u32, volatile u32* destination_base, const volatile u32* source) {
    const u32 loaded = *source;
    volatile u32* destination = destination_base + 1;
    destination[0] = 1;
    destination[1] = loaded;
    return 0;
}
