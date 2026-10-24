#include <cstdint>

using u8 = uint8_t;
using u32 = uint32_t;

#define DEFINE_SCRIPT_VM_INITIALIZER(name)                                  \
    extern "C" __attribute__((noinline, used)) volatile u32* name(         \
        volatile u32* base, u32 value1, u32 value2) {                       \
        base[0] = 0;                                                         \
        base[1] = 0;                                                         \
        base[2] = 0;                                                         \
        base[3] = 0;                                                         \
        base[4] = 0;                                                         \
        base[5] = 0;                                                         \
        base[6] = 0;                                                         \
        base[7] = 0;                                                         \
        base[8] = 0;                                                         \
        base[9] = 0;                                                         \
        reinterpret_cast<volatile u8*>(base)[0x28] = 0;                      \
        base[11] = value1;                                                   \
        base[12] = value2;                                                   \
        return base;                                                         \
    }

DEFINE_SCRIPT_VM_INITIALIZER(candidate_00353124)
DEFINE_SCRIPT_VM_INITIALIZER(candidate_003531ac)

extern "C" __attribute__((noinline, used)) volatile u32* negative_skip_byte(
    volatile u32* base, u32 value1, u32 value2) {
    base[0] = 0;
    base[1] = 0;
    base[2] = 0;
    base[3] = 0;
    base[4] = 0;
    base[5] = 0;
    base[6] = 0;
    base[7] = 0;
    base[8] = 0;
    base[9] = 0;
    base[11] = value1;
    base[12] = value2;
    return base;
}

extern "C" __attribute__((noinline, used)) volatile u32* negative_word_at_byte(
    volatile u32* base, u32 value1, u32 value2) {
    base[0] = 0;
    base[1] = 0;
    base[2] = 0;
    base[3] = 0;
    base[4] = 0;
    base[5] = 0;
    base[6] = 0;
    base[7] = 0;
    base[8] = 0;
    base[9] = 0;
    base[10] = 0;
    base[11] = value1;
    base[12] = value2;
    return base;
}

extern "C" __attribute__((noinline, used)) volatile u32* negative_swapped_values(
    volatile u32* base, u32 value1, u32 value2) {
    base[0] = 0;
    base[1] = 0;
    base[2] = 0;
    base[3] = 0;
    base[4] = 0;
    base[5] = 0;
    base[6] = 0;
    base[7] = 0;
    base[8] = 0;
    base[9] = 0;
    reinterpret_cast<volatile u8*>(base)[0x28] = 0;
    base[11] = value2;
    base[12] = value1;
    return base;
}
