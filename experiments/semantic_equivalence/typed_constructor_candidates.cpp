#include <stdint.h>

using u8 = uint8_t;
using u32 = uint32_t;

// Semantic reconstruction of the two verified ARM leaves at 0x003A80CC and
// 0x003A9644. Volatile preserves the observable byte/word stores and order.
#define DEFINE_TYPED_CONSTRUCTOR(name, tag)                              \
    extern "C" __attribute__((noinline, used)) volatile u32* name(      \
        volatile u8* base) {                                              \
        base[0x10] = 1;                                                   \
        volatile u32* fields =                                            \
            reinterpret_cast<volatile u32*>(base + 0x14);                \
        fields[0] = (tag);                                                \
        fields[1] = 0;                                                    \
        return fields;                                                    \
    }

DEFINE_TYPED_CONSTRUCTOR(candidate_003a80cc, 0x0d)
DEFINE_TYPED_CONSTRUCTOR(candidate_003a9644, 0x08)

DEFINE_TYPED_CONSTRUCTOR(negative_wrong_tag, 0x0c)

extern "C" __attribute__((noinline, used)) volatile u32* negative_wrong_offset(
    volatile u8* base) {
    base[0x10] = 1;
    volatile u32* fields = reinterpret_cast<volatile u32*>(base + 0x18);
    fields[0] = 0x0d;
    fields[1] = 0;
    return fields;
}

extern "C" __attribute__((noinline, used)) volatile u8* negative_wrong_return(
    volatile u8* base) {
    base[0x10] = 1;
    volatile u32* fields = reinterpret_cast<volatile u32*>(base + 0x14);
    fields[0] = 0x0d;
    fields[1] = 0;
    return base;
}
