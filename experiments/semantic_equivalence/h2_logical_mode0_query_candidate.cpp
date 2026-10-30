#include "types.h"

static __attribute__((always_inline)) inline u32 h2_mode0_query_remainder(
    u32 dividend, u32 divisor) {
    u32 remainder;
    asm volatile(
        "mov r0, %1\n"
        "mov r1, %2\n"
        "ldr r12, 1f\n"
        "blx r12\n"
        "b 2f\n"
        ".balign 4\n"
        "1: .word 0x002c6c10\n"
        "2:\n"
        "mov %0, r1\n"
        : "=r"(remainder)
        : "r"(dividend), "r"(divisor)
        : "r0", "r1", "r2", "r3", "r12", "lr", "cc", "memory");
    return remainder;
}

extern "C" s32 candidate_002b902c(u32 id) {
    if (id >= 0x1fu) return 0;

    const u32 flags = *reinterpret_cast<const u32*>(0x004650A8u);
    u32 counter = 0;
    if ((flags & 1u) == 0) {
        counter = *reinterpret_cast<const u32*>(0x004E3C58u + id * 4u);
        if (counter == 1u) return 1;
    }

    const u32 threshold = *reinterpret_cast<const u32*>(0x004650ACu);
    if (counter <= threshold) return 0;
    const u32 selector = *reinterpret_cast<const u32*>(0x004650B0u);
    return h2_mode0_query_remainder(counter - threshold, selector) == 0 ? 1 : 0;
}

extern "C" s32 candidate_002b902c_bad_counter(u32 id) {
    if (id >= 0x1fu) return 0;
    const u32 flags = *reinterpret_cast<const u32*>(0x004650A8u);
    u32 counter = 0;
    if ((flags & 1u) == 0) {
        counter = *reinterpret_cast<const u32*>(0x004E3C58u + (id + 1u) * 4u);
        if (counter == 1u) return 1;
    }
    const u32 threshold = *reinterpret_cast<const u32*>(0x004650ACu);
    if (counter <= threshold) return 0;
    const u32 selector = *reinterpret_cast<const u32*>(0x004650B0u);
    return h2_mode0_query_remainder(counter - threshold, selector) == 0 ? 1 : 0;
}

extern "C" s32 candidate_002b902c_bad_threshold(u32 id) {
    if (id >= 0x1fu) return 0;
    const u32 flags = *reinterpret_cast<const u32*>(0x004650A8u);
    u32 counter = 0;
    if ((flags & 1u) == 0) {
        counter = *reinterpret_cast<const u32*>(0x004E3C58u + id * 4u);
        if (counter == 1u) return 1;
    }
    const u32 threshold = *reinterpret_cast<const u32*>(0x004650ACu) + 1u;
    if (counter <= threshold) return 0;
    const u32 selector = *reinterpret_cast<const u32*>(0x004650B0u);
    return h2_mode0_query_remainder(counter - threshold, selector) == 0 ? 1 : 0;
}

extern "C" s32 candidate_002b902c_bad_selector(u32 id) {
    if (id >= 0x1fu) return 0;
    const u32 flags = *reinterpret_cast<const u32*>(0x004650A8u);
    u32 counter = 0;
    if ((flags & 1u) == 0) {
        counter = *reinterpret_cast<const u32*>(0x004E3C58u + id * 4u);
        if (counter == 1u) return 1;
    }
    const u32 threshold = *reinterpret_cast<const u32*>(0x004650ACu);
    if (counter <= threshold) return 0;
    const u32 selector = *reinterpret_cast<const u32*>(0x004650B0u) + 1u;
    return h2_mode0_query_remainder(counter - threshold, selector) == 0 ? 1 : 0;
}
