#include <stdint.h>

using u8 = uint8_t;
using u32 = uint32_t;

// Isolated C++ candidates for three routines that store an ordered pair of
// words at different object offsets. Return the adjusted pointer as observed
// in r0, even though sampled production callers discard it.
#define DEFINE_PAIRED_STORE(name, offset)                              \
    extern "C" __attribute__((noinline, used)) volatile u32* name(    \
        volatile u8* base, u32 first, u32 second) {                    \
        volatile u32* destination =                                    \
            reinterpret_cast<volatile u32*>(base + (offset));          \
        destination[0] = first;                                        \
        destination[1] = second;                                       \
        return destination;                                            \
    }

DEFINE_PAIRED_STORE(candidate_00158784, 0x84)
DEFINE_PAIRED_STORE(candidate_0023347c, 0x40)
DEFINE_PAIRED_STORE(candidate_00292e88, 0x40)

// Negative controls: a wrong field offset, swapped stores, and wrong r0 return.
DEFINE_PAIRED_STORE(negative_wrong_offset, 0x80)

extern "C" __attribute__((noinline, used)) volatile u32* negative_swapped_store(
    volatile u8* base, u32 first, u32 second) {
    volatile u32* destination = reinterpret_cast<volatile u32*>(base + 0x40);
    destination[0] = second;
    destination[1] = first;
    return destination;
}

extern "C" __attribute__((noinline, used)) volatile u8* negative_wrong_return(
    volatile u8* base, u32 first, u32 second) {
    volatile u32* destination = reinterpret_cast<volatile u32*>(base + 0x40);
    destination[0] = first;
    destination[1] = second;
    return base;
}
