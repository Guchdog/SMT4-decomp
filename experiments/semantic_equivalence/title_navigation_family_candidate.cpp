#include <stdint.h>

using u32 = uint32_t;

struct NavigationEventObservation {
    u32 count;
    u32 id;
    u32 cursor_at_call;
    u32 cached_cursor_at_call;
};

// Isolated reducer for the trigger-result-to-cursor portion of the title
// callback. gate_bits: bit 0 = Script_IsReadyToAdvance, bit 1 =
// Camp_IsPreviewReady. trigger_bits: bits 0..3 = IDs 5, 0xE, 6, 0xF.
// The event observation models only the caller-visible call contract at
// 0x002B91C4; it does not claim to reconstruct that event helper's internals.
extern "C" __attribute__((noinline)) u32 title_navigation_reduce(
    volatile u32* work, u32 gate_bits, u32 trigger_bits,
    volatile NavigationEventObservation* event) {
    const u32 original = work[2];
    if ((gate_bits & 3u) != 3u) {
        return original;
    }

    u32 provisional = original;
    if ((trigger_bits & (1u << 0)) != 0u) {
        provisional -= 1u;
    } else if ((trigger_bits & (1u << 1)) != 0u) {
        provisional -= 1u;
    }
    if ((trigger_bits & (1u << 2)) != 0u) {
        provisional += 1u;
    } else if ((trigger_bits & (1u << 3)) != 0u) {
        provisional += 1u;
    }

    // Match the inline ARM signed-remainder-by-four sequence without using
    // division/modulo operators (which could introduce a runtime helper).
    const u32 adjusted = provisional + 4u;
    const u32 sign_correction = (0u - (adjusted >> 31)) >> 30;
    const u32 multiple = (adjusted + sign_correction) & ~3u;
    const u32 normalized = adjusted - multiple;
    work[2] = normalized;

    if (normalized != work[3]) {
        event->count = 1u;
        event->id = 0x0100016Cu;
        event->cursor_at_call = normalized;
        event->cached_cursor_at_call = work[3];
        work[3] = normalized;
    }
    return normalized;
}
