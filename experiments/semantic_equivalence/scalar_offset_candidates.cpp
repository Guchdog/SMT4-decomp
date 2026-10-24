#include <stdint.h>

using u32 = uint32_t;

// Isolated candidates for three leaf functions that add a fixed offset to r0.
// Unsigned arithmetic preserves the original ARM modulo-2^32 behavior.
#define DEFINE_OFFSET_GETTER(name, offset)                             \
    extern "C" __attribute__((noinline, used)) u32 name(u32 base) {   \
        return base + static_cast<u32>(offset);                       \
    }

DEFINE_OFFSET_GETTER(candidate_00343550, 0x5B4)
DEFINE_OFFSET_GETTER(candidate_00343584, 0xC04)
DEFINE_OFFSET_GETTER(candidate_00343590, 0x6FC)

extern "C" __attribute__((noinline, used)) u32 negative_candidate_00343550(
    u32 base) {
    return base + 0x5B5u;
}

extern "C" __attribute__((noinline, used)) u32 negative_candidate_00343584(
    u32 base) {
    return base + 0xC05u;
}

extern "C" __attribute__((noinline, used)) u32 negative_candidate_00343590(
    u32 base) {
    return base + 0x6FDu;
}
