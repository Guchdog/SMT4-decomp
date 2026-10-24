#include <stdint.h>

using u32 = uint32_t;

#define DEFINE_PAIR_INITIALIZER(name, offset)                            \
    extern "C" __attribute__((noinline, used)) volatile u32* name(      \
        volatile u8* base) {                                              \
        volatile u32* record = reinterpret_cast<volatile u32*>(base + (offset)); \
        record[0] = 1;                                                    \
        record[1] = 0;                                                    \
        return record;                                                    \
    }

using u8 = uint8_t;

DEFINE_PAIR_INITIALIZER(candidate_00399d4c, 0x04)
DEFINE_PAIR_INITIALIZER(candidate_003abcf4, 0x14)

DEFINE_PAIR_INITIALIZER(negative_wrong_offset, 0x08)

extern "C" __attribute__((noinline, used)) volatile u32* negative_wrong_value(
    volatile u8* base) {
    volatile u32* record = reinterpret_cast<volatile u32*>(base + 0x14);
    record[0] = 1;
    record[1] = 1;
    return record;
}

extern "C" __attribute__((noinline, used)) volatile u8* negative_wrong_return(
    volatile u8* base) {
    volatile u32* record = reinterpret_cast<volatile u32*>(base + 0x14);
    record[0] = 1;
    record[1] = 0;
    return base;
}
