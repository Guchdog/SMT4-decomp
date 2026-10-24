#include <stdint.h>

using u8 = uint8_t;
using u32 = uint32_t;

// Experimental, offset-specific reconstructions. Keep every source load
// sequenced before any destination store, matching the original snapshot
// behavior when source and destination overlap.
#define DEFINE_COPY3(name, offset)                                      \
    extern "C" __attribute__((noinline, used)) u32* name(               \
        u32* destination_base, const u32* source) {                      \
        const volatile u32* input = reinterpret_cast<const volatile u32*>(source); \
        volatile u32* output = reinterpret_cast<volatile u32*>(           \
            reinterpret_cast<volatile u8*>(destination_base) + (offset)); \
        const u32 first = input[0];                                      \
        const u32 second = input[1];                                     \
        const u32 third = input[2];                                      \
        output[2] = third;                                               \
        output[0] = first;                                               \
        output[1] = second;                                              \
        return destination_base;                                         \
    }

DEFINE_COPY3(candidate_00232b00, 0x4C)
DEFINE_COPY3(candidate_00232b14, 0x40)
DEFINE_COPY3(candidate_00232b28, 0x28)

// Wrong-offset control: must be caught by the isolated differential check.
DEFINE_COPY3(negative_wrong_destination, 0x50)

// Deliberately violate snapshot semantics: the first store can clobber the
// second source word when output starts four bytes after input.
extern "C" __attribute__((noinline, used)) u32* negative_late_load(
    u32* destination_base, const u32* source) {
    volatile u32* output = reinterpret_cast<volatile u32*>(
        reinterpret_cast<volatile u8*>(destination_base) + 0x40);
    const volatile u32* input = reinterpret_cast<const volatile u32*>(source);
    const u32 first = input[0];
    output[0] = first;
    const u32 second = input[1];
    const u32 third = input[2];
    output[2] = third;
    output[1] = second;
    return destination_base;
}
