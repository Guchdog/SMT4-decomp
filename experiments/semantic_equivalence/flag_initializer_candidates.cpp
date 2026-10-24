#include <stdint.h>

using u32 = uint32_t;

#define DEFINE_FLAG_INITIALIZER(name, tag)                              \
    extern "C" __attribute__((noinline, used)) volatile u32* name(      \
        volatile u32* base) {                                             \
        const u32 flags = base[0];                                        \
        base[0] = flags | 1u;                                             \
        base[1] = tag;                                                    \
        base[2] = 0;                                                      \
        return base + 1;                                                  \
    }

DEFINE_FLAG_INITIALIZER(candidate_00383780, 0x11u)
DEFINE_FLAG_INITIALIZER(candidate_003a1a6c, 0x13u)

extern "C" __attribute__((noinline, used)) volatile u32* negative_wrong_flag(
    volatile u32* base) {
    const u32 flags = base[0];
    base[0] = flags | 2u;
    base[1] = 0x11u;
    base[2] = 0;
    return base + 1;
}

extern "C" __attribute__((noinline, used)) volatile u32* negative_wrong_constant(
    volatile u32* base) {
    const u32 flags = base[0];
    base[0] = flags | 1u;
    base[1] = 0x12u;
    base[2] = 0;
    return base + 1;
}

extern "C" __attribute__((noinline, used)) volatile u32* negative_wrong_offset(
    volatile u32* base) {
    const u32 flags = base[0];
    base[0] = flags | 1u;
    base[2] = 0x11u;
    base[3] = 0;
    return base + 2;
}

extern "C" __attribute__((noinline, used)) volatile u32* negative_wrong_return(
    volatile u32* base) {
    const u32 flags = base[0];
    base[0] = flags | 1u;
    base[1] = 0x11u;
    base[2] = 0;
    return base;
}
