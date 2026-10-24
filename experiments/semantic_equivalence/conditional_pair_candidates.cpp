#include <stdint.h>

using u8 = uint8_t;
using u32 = uint32_t;

// Isolated candidates for the two conditional pair-store helpers. r1 is a
// stored value and null sentinel (not a dereferenced source pointer); r2 is
// the second stored word. The result is the observed boolean in r0.
#define DEFINE_CONDITIONAL_PAIR(name, offset)                          \
    extern "C" __attribute__((noinline, used)) u32 name(              \
        volatile u8* context, u32 first, u32 second) {                  \
        if (first == 0)                                                 \
            return 0;                                                   \
        volatile u32* fields = reinterpret_cast<volatile u32*>(        \
            context + (offset));                                        \
        fields[0] = first;                                              \
        fields[1] = second;                                             \
        return 1;                                                       \
    }

DEFINE_CONDITIONAL_PAIR(candidate_00110c2c, 0x1C)
DEFINE_CONDITIONAL_PAIR(candidate_00121150, 0x30)

// Negative controls: wrong offset, reversed values, missing null guard, and
// a wrong non-null boolean result.
DEFINE_CONDITIONAL_PAIR(negative_wrong_offset, 0x18)

extern "C" __attribute__((noinline, used)) u32 negative_reversed_pair(
    volatile u8* context, u32 first, u32 second) {
    if (first == 0)
        return 0;
    volatile u32* fields = reinterpret_cast<volatile u32*>(context + 0x30);
    fields[0] = second;
    fields[1] = first;
    return 1;
}

extern "C" __attribute__((noinline, used)) u32 negative_unconditional_store(
    volatile u8* context, u32 first, u32 second) {
    volatile u32* fields = reinterpret_cast<volatile u32*>(context + 0x30);
    fields[0] = first;
    fields[1] = second;
    return first != 0;
}

extern "C" __attribute__((noinline, used)) u32 negative_wrong_boolean(
    volatile u8* context, u32 first, u32 second) {
    if (first == 0)
        return 0;
    volatile u32* fields = reinterpret_cast<volatile u32*>(context + 0x1C);
    fields[0] = first;
    fields[1] = second;
    return 0;
}
