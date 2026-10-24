// Isolated semantic candidates for three chained pointer getters.
// These are experimental only and do not replace production functions.
#include <stdint.h>

using u32 = uint32_t;
static_assert(sizeof(void*) == 4, "The experiment targets 32-bit ARM pointers");

static inline __attribute__((always_inline)) u32 load_word(u32 address) {
    return *reinterpret_cast<volatile const u32*>(static_cast<uintptr_t>(address));
}

#define DEFINE_CHAIN(name, root_offset, middle_offset, value_offset, sum_offset) \
    extern "C" __attribute__((noinline, used)) u32 name(u32 base) {             \
        const u32 first = load_word(base + (root_offset));                       \
        const u32 second = load_word(first + (middle_offset));                   \
        const u32 value = load_word(second + (value_offset));                    \
        if (value == 0) return 0;                                                \
        return value + load_word(second + (sum_offset));                        \
    }

#define DEFINE_UNCONDITIONAL(name, root_offset)                                  \
    extern "C" __attribute__((noinline, used)) u32 name(u32 base) {             \
        const u32 first = load_word(base + (root_offset));                       \
        const u32 second = load_word(first + 0x24);                              \
        const u32 value = load_word(second + 0x20);                              \
        return value + load_word(second + 0xb8);                                \
    }

DEFINE_CHAIN(candidate_00207b78, 0x4c, 0x24, 0x20, 0xb8)
DEFINE_CHAIN(candidate_002df440, 0x30, 0x24, 0x20, 0xb8)
DEFINE_CHAIN(candidate_002f300c, 0x9c, 0x24, 0x20, 0xb8)

// One-field offset controls for each candidate. Prepared memory makes each
// substituted slot point down a valid but distinguishable path.
DEFINE_CHAIN(wrong_root_00207b78, 0x50, 0x24, 0x20, 0xb8)
DEFINE_CHAIN(wrong_middle_00207b78, 0x4c, 0x28, 0x20, 0xb8)
DEFINE_CHAIN(wrong_value_00207b78, 0x4c, 0x24, 0x24, 0xb8)
DEFINE_CHAIN(wrong_sum_00207b78, 0x4c, 0x24, 0x20, 0xbc)

DEFINE_CHAIN(wrong_root_002df440, 0x34, 0x24, 0x20, 0xb8)
DEFINE_CHAIN(wrong_middle_002df440, 0x30, 0x28, 0x20, 0xb8)
DEFINE_CHAIN(wrong_value_002df440, 0x30, 0x24, 0x24, 0xb8)
DEFINE_CHAIN(wrong_sum_002df440, 0x30, 0x24, 0x20, 0xbc)

DEFINE_CHAIN(wrong_root_002f300c, 0xa0, 0x24, 0x20, 0xb8)
DEFINE_CHAIN(wrong_middle_002f300c, 0x9c, 0x28, 0x20, 0xb8)
DEFINE_CHAIN(wrong_value_002f300c, 0x9c, 0x24, 0x24, 0xb8)
DEFINE_CHAIN(wrong_sum_002f300c, 0x9c, 0x24, 0x20, 0xbc)

// Branch control deliberately performs the fourth read even when value is 0.
DEFINE_UNCONDITIONAL(unconditional_00207b78, 0x4c)
DEFINE_UNCONDITIONAL(unconditional_002df440, 0x30)
DEFINE_UNCONDITIONAL(unconditional_002f300c, 0x9c)

#undef DEFINE_UNCONDITIONAL
#undef DEFINE_CHAIN
