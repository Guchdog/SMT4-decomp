// Isolated semantic candidates for five null-aware pointer getters.
// These intentionally remain separate from production source.
#include <stdint.h>

using u32 = uint32_t;
static_assert(sizeof(void*) == 4, "The experiment targets 32-bit ARM pointers");

static inline __attribute__((always_inline)) u32 load_word(u32 address) {
    return *reinterpret_cast<volatile const u32*>(static_cast<uintptr_t>(address));
}

#define DEFINE_CHAIN(name, first_offset, second_offset)                 \
    extern "C" __attribute__((noinline, used)) u32 name(u32 base) {     \
        const u32 middle = load_word(base + (first_offset));             \
        return middle != 0 ? load_word(middle + (second_offset)) : 0;    \
    }

DEFINE_CHAIN(candidate_00141468, 8, 0)
DEFINE_CHAIN(candidate_002344b4, 4, 8)
DEFINE_CHAIN(candidate_003df578, 4, 4)
DEFINE_CHAIN(candidate_003df588, 4, 8)
DEFINE_CHAIN(candidate_003df598, 4, 4)

// Negative controls alter exactly one pointer-field offset. The runner checks
// that each is rejected by the corresponding prepared differential case.
DEFINE_CHAIN(wrong_root_00141468, 4, 0)
DEFINE_CHAIN(wrong_leaf_00141468, 8, 4)
DEFINE_CHAIN(wrong_root_002344b4, 8, 8)
DEFINE_CHAIN(wrong_leaf_002344b4, 4, 4)
DEFINE_CHAIN(wrong_root_003df578, 8, 4)
DEFINE_CHAIN(wrong_leaf_003df578, 4, 8)
DEFINE_CHAIN(wrong_root_003df588, 8, 8)
DEFINE_CHAIN(wrong_leaf_003df588, 4, 4)
DEFINE_CHAIN(wrong_root_003df598, 8, 4)
DEFINE_CHAIN(wrong_leaf_003df598, 4, 8)

#undef DEFINE_CHAIN
