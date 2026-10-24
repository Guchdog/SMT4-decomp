#include <stdint.h>

using u8 = uint8_t;
using u16 = uint16_t;
using u32 = uint32_t;

// Isolated candidates for the callback entries referenced from the table at
// 0x00473080..0x00473248. The volatile accesses preserve the original order,
// including its second load through the incoming r1 slot. This file is not
// production code and does not claim equivalence for MMIO or concurrent state.
#define DEFINE_BYTE_CALLBACK(name, type_value, field_value)           \
    extern "C" __attribute__((noinline, used)) u32 name(             \
        volatile u32* context, volatile u8* volatile* slot) {         \
        volatile u8* first_record = *slot;                            \
        first_record[8] = static_cast<u8>(type_value);                \
        volatile u8* second_record = *slot;                           \
        second_record[0xA] = static_cast<u8>(field_value);            \
        volatile u32* counter = context + 4;                          \
        *counter = *counter + 1;                                      \
        return 0;                                                       \
    }

#define DEFINE_HALFWORD_CALLBACK(name, field_value)                    \
    extern "C" __attribute__((noinline, used)) u32 name(             \
        volatile u32* context, volatile u8* volatile* slot) {         \
        volatile u8* first_record = *slot;                            \
        first_record[8] = 0;                                          \
        volatile u8* second_record = *slot;                           \
        *reinterpret_cast<volatile u16*>(second_record + 0xA) =        \
            static_cast<u16>(field_value);                            \
        volatile u32* counter = context + 4;                          \
        *counter = *counter + 1;                                      \
        return 0;                                                       \
    }

DEFINE_BYTE_CALLBACK(candidate_0035b6fc, 0x11, 4)
DEFINE_BYTE_CALLBACK(candidate_0035b728, 0x11, 3)
DEFINE_BYTE_CALLBACK(candidate_0035b754, 8, 1)
DEFINE_BYTE_CALLBACK(candidate_0035b814, 8, 2)
DEFINE_BYTE_CALLBACK(candidate_0035b840, 8, 3)
DEFINE_BYTE_CALLBACK(candidate_0035b86c, 0x11, 6)
DEFINE_BYTE_CALLBACK(candidate_0035b8c4, 0x11, 2)
DEFINE_BYTE_CALLBACK(candidate_0035b95c, 7, 1)
DEFINE_BYTE_CALLBACK(candidate_0035bacc, 7, 2)
DEFINE_BYTE_CALLBACK(candidate_0035bb48, 7, 3)
DEFINE_BYTE_CALLBACK(candidate_0035bb98, 0x11, 5)

DEFINE_HALFWORD_CALLBACK(candidate_0035b898, 7)
DEFINE_HALFWORD_CALLBACK(candidate_0035b988, 0x1B)
DEFINE_HALFWORD_CALLBACK(candidate_0035b9b4, 0xC)
DEFINE_HALFWORD_CALLBACK(candidate_0035b9e0, 0xA)
DEFINE_HALFWORD_CALLBACK(candidate_0035baa0, 0xD)
DEFINE_HALFWORD_CALLBACK(candidate_0035baf8, 9)

// Negative controls used to prove the differential harness catches a changed
// record-field constant in each store-width family.
DEFINE_BYTE_CALLBACK(negative_byte_field, 0x11, 5)
DEFINE_HALFWORD_CALLBACK(negative_halfword_field, 8)
