#include <stdint.h>

using u32 = uint32_t;
using s32 = int32_t;

// Semantic model for 0x001E9DAC..0x001E9DC0 only. The caller passes the
// original work+8 field address and the provisional cursor value.
extern "C" __attribute__((noinline)) u32 title_cursor_normalize_store(
    u32* cursor_field, u32 provisional) {
    const u32 adjusted = provisional + 4u;
    const u32 negative_correction = (0u - (adjusted >> 31)) >> 30;
    const u32 truncated_multiple = (adjusted + negative_correction) & ~3u;
    const u32 normalized = adjusted - truncated_multiple;
    *cursor_field = normalized;
    return normalized;
}

// Targeted negative control: signed remainder without the original +4
// normalization. It returns -1 for provisional -1, unlike the reference.
extern "C" __attribute__((noinline)) u32 title_cursor_negative_no_bias(
    u32* cursor_field, u32 provisional) {
    const s32 signed_value = static_cast<s32>(provisional);
    const u32 wrong = static_cast<u32>(signed_value % 4);
    *cursor_field = wrong;
    return wrong;
}
