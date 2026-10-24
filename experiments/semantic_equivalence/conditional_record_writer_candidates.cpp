#include <stdint.h>

using u8 = uint8_t;
using u32 = uint32_t;

// The input word is interpreted as signed: ARM's GT condition after CMP x,0
// means signed x > 0, not unsigned x > 0. The handle cell is reloaded between
// the byte write and the second conditional write to retain both pinned LDRs.
#define DEFINE_RECORD_WRITER(name, nonpositive_byte, positive_halfword)       \
    extern "C" __attribute__((noinline, used)) u32 name(                     \
        u8* record, u32* volatile* handle_cell) {                             \
        const volatile int32_t* condition = reinterpret_cast<               \
            const volatile int32_t*>(record + 0x18);                          \
        const int32_t value = *condition;                                     \
        u32* first_target = *handle_cell;                                     \
        if (value > 0) {                                                      \
            *reinterpret_cast<volatile u8*>(                                 \
                reinterpret_cast<volatile u8*>(first_target) + 8) = 0;        \
        } else {                                                              \
            *reinterpret_cast<volatile u8*>(                                 \
                reinterpret_cast<volatile u8*>(first_target) + 8) =           \
                (nonpositive_byte);                                           \
        }                                                                     \
        u32* second_target = *handle_cell;                                    \
        if (value > 0) {                                                      \
            *reinterpret_cast<volatile uint16_t*>(                           \
                reinterpret_cast<volatile u8*>(second_target) + 0xA) =        \
                (positive_halfword);                                          \
        } else {                                                              \
            *reinterpret_cast<volatile u8*>(                                 \
                reinterpret_cast<volatile u8*>(second_target) + 0xA) = 0;     \
        }                                                                     \
        volatile u32* counter = reinterpret_cast<volatile u32*>(record + 0x10);\
        *counter = *counter + 1;                                              \
        return 0;                                                             \
    }

DEFINE_RECORD_WRITER(candidate_0035b254, 7, 0x2E)
DEFINE_RECORD_WRITER(candidate_0035bf8c, 0x11, 0x5E)

// Targeted negative control: zeroes a halfword on the <= 0 path. The pinned
// routine writes only one byte there and must preserve the following byte.
extern "C" __attribute__((noinline, used)) u32 negative_wide_zero_on_else(
    u8* record, u32* volatile* handle_cell) {
    const volatile int32_t* condition = reinterpret_cast<
        const volatile int32_t*>(record + 0x18);
    const int32_t value = *condition;
    u32* first_target = *handle_cell;
    if (value > 0) {
        *reinterpret_cast<volatile u8*>(
            reinterpret_cast<volatile u8*>(first_target) + 8) = 0;
    } else {
        *reinterpret_cast<volatile u8*>(
            reinterpret_cast<volatile u8*>(first_target) + 8) = 7;
    }
    u32* second_target = *handle_cell;
    if (value > 0) {
        *reinterpret_cast<volatile uint16_t*>(
            reinterpret_cast<volatile u8*>(second_target) + 0xA) = 0x2E;
    } else {
        *reinterpret_cast<volatile uint16_t*>(
            reinterpret_cast<volatile u8*>(second_target) + 0xA) = 0;
    }
    volatile u32* counter = reinterpret_cast<volatile u32*>(record + 0x10);
    *counter = *counter + 1;
    return 0;
}
