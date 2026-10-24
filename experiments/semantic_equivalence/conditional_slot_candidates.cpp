#include <stdint.h>

using u8 = uint8_t;
using u32 = uint32_t;

// Try to initialize one pointer slot only when the object's first word is 0.
#define DEFINE_TRY_SLOT(name, offset)                                    \
    extern "C" __attribute__((noinline, used)) u32 name(                \
        u32* object, u32 value) {                                         \
        if (object[0] != 0)                                               \
            return 0;                                                     \
        *reinterpret_cast<volatile u32*>(                                \
            reinterpret_cast<volatile u8*>(object) + (offset)) = value;  \
        return 1;                                                         \
    }

DEFINE_TRY_SLOT(candidate_0014e744, 0x28)
DEFINE_TRY_SLOT(candidate_002b0418, 0x24)

// Negative controls: the wrong field and a store that ignores the empty-slot
// condition. The experiment must catch both against their targeted fixtures.
DEFINE_TRY_SLOT(negative_wrong_field, 0x2C)

extern "C" __attribute__((noinline, used)) u32 negative_store_unconditionally(
    u32* object, u32 value) {
    *reinterpret_cast<volatile u32*>(
        reinterpret_cast<volatile u8*>(object) + 0x24) = value;
    return object[0] == 0;
}
