// Isolated semantic candidates for four camp-state predicates.
// The values are loaded from raw 32-bit address offsets because the exact
// enclosing C++ structure types/names are not recovered.
#include <stdint.h>

using u32 = uint32_t;

static inline __attribute__((always_inline)) u32 load_word(u32 address) {
    return *reinterpret_cast<volatile const u32*>(static_cast<uintptr_t>(address));
}

#define DEFINE_PREDICATE(name, offset, value)                          \
    extern "C" __attribute__((noinline, used)) u32 name(u32 base) {    \
        return load_word(base + (offset)) != (value) ? 1u : 0u;        \
    }
#define DEFINE_WRONG_OFFSET(name, offset, value)                       \
    extern "C" __attribute__((noinline, used)) u32 name(u32 base) {    \
        return load_word(base + (offset) + 4u) != (value) ? 1u : 0u;    \
    }
#define DEFINE_WRONG_CONSTANT(name, offset, value)                    \
    extern "C" __attribute__((noinline, used)) u32 name(u32 base) {    \
        return load_word(base + (offset)) != ((value) + 1u) ? 1u : 0u;\
    }
#define DEFINE_WRONG_SENSE(name, offset, value)                       \
    extern "C" __attribute__((noinline, used)) u32 name(u32 base) {   \
        return load_word(base + (offset)) == (value) ? 1u : 0u;       \
    }

DEFINE_PREDICATE(candidate_0028c124, 0x2180u, 6u)
DEFINE_PREDICATE(candidate_0028c850, 0x2180u, 5u)
DEFINE_PREDICATE(candidate_0028c868, 0x3048u, 14u)
DEFINE_PREDICATE(candidate_002d01ec, 0x2180u, 4u)

DEFINE_WRONG_OFFSET(wrong_offset_0028c124, 0x2180u, 6u)
DEFINE_WRONG_OFFSET(wrong_offset_0028c850, 0x2180u, 5u)
DEFINE_WRONG_OFFSET(wrong_offset_0028c868, 0x3048u, 14u)
DEFINE_WRONG_OFFSET(wrong_offset_002d01ec, 0x2180u, 4u)

DEFINE_WRONG_CONSTANT(wrong_constant_0028c124, 0x2180u, 6u)
DEFINE_WRONG_CONSTANT(wrong_constant_0028c850, 0x2180u, 5u)
DEFINE_WRONG_CONSTANT(wrong_constant_0028c868, 0x3048u, 14u)
DEFINE_WRONG_CONSTANT(wrong_constant_002d01ec, 0x2180u, 4u)

DEFINE_WRONG_SENSE(wrong_sense_0028c124, 0x2180u, 6u)
DEFINE_WRONG_SENSE(wrong_sense_0028c850, 0x2180u, 5u)
DEFINE_WRONG_SENSE(wrong_sense_0028c868, 0x3048u, 14u)
DEFINE_WRONG_SENSE(wrong_sense_002d01ec, 0x2180u, 4u)

#undef DEFINE_PREDICATE
#undef DEFINE_WRONG_OFFSET
#undef DEFINE_WRONG_CONSTANT
#undef DEFINE_WRONG_SENSE
