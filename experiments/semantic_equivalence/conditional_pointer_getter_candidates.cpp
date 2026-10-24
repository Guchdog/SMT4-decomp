#include <stdint.h>

using u8 = uint8_t;
using u32 = uint32_t;

// Return the pointer-like word only while byte flag +0x62 is clear.
// Volatile loads make the reference's narrow flag read and conditional word
// read observable to the differential harness.
#define DEFINE_CONDITIONAL_POINTER_GETTER(name, offset)                    \
    extern "C" __attribute__((noinline, used)) u32 name(const u8* object) {\
        const volatile u8* bytes = reinterpret_cast<const volatile u8*>(object); \
        if (bytes[0x62] != 0)                                              \
            return 0;                                                      \
        return *reinterpret_cast<const volatile u32*>(bytes + (offset));   \
    }

DEFINE_CONDITIONAL_POINTER_GETTER(candidate_00240ea4, 0x48)
DEFINE_CONDITIONAL_POINTER_GETTER(candidate_0029e3bc, 0x20)

// Targeted negative controls: violate one part of the observed contract.
extern "C" __attribute__((noinline, used)) u32 negative_wrong_offset_00240ea4(
    const u8* object) {
    const volatile u8* bytes = reinterpret_cast<const volatile u8*>(object);
    if (bytes[0x62] != 0)
        return 0;
    return *reinterpret_cast<const volatile u32*>(bytes + 0x20);
}

extern "C" __attribute__((noinline, used)) u32 negative_wrong_flag_width(
    const u8* object) {
    const volatile u8* bytes = reinterpret_cast<const volatile u8*>(object);
    if (*reinterpret_cast<const volatile u32*>(bytes + 0x62) != 0)
        return 0;
    return *reinterpret_cast<const volatile u32*>(bytes + 0x48);
}

extern "C" __attribute__((noinline, used)) u32 negative_wrong_flag_sense(
    const u8* object) {
    const volatile u8* bytes = reinterpret_cast<const volatile u8*>(object);
    if (bytes[0x62] == 0)
        return 0;
    return *reinterpret_cast<const volatile u32*>(bytes + 0x48);
}
