#include <stdint.h>

using u8 = uint8_t;
using u32 = uint32_t;
using s32 = int32_t;

namespace {

// Only fields touched in the bounded 0x001E9D08..0x001E9DE0 caller window.
// The absolute singleton slot is the same one loaded by the original at
// 0x001E9D2C..0x001E9D38.
struct TitleMainNavigationWork {
    u8 pad_00[0x08];
    u32 selection;          // +0x08
    u32 cached_selection;   // +0x0C
    u8 pad_10[0x50];
    u8 flags_60_63[4];
    float timer_64;         // +0x64, incremented only after both gates pass
};
static_assert(__builtin_offsetof(TitleMainNavigationWork, selection) == 0x08);
static_assert(__builtin_offsetof(TitleMainNavigationWork, cached_selection) == 0x0C);
static_assert(__builtin_offsetof(TitleMainNavigationWork, timer_64) == 0x64);

using ReadyPredicate = s32 (*)();
using TriggerQuery = s32 (*)(u32 logical_id);
using EventRequest = void (*)(u32 event_id);

constexpr uintptr_t kTitleMainWorkSlot = 0x0044E300u;
constexpr uintptr_t kScriptIsReady = 0x00289924u;
constexpr uintptr_t kPreviewIsReady = 0x0025A2BCu;
constexpr uintptr_t kInputTrigger = 0x002B902Cu;
constexpr uintptr_t kEventRequest = 0x002B91C4u;
constexpr u32 kSelectionChangedEvent = 0x0100016Cu;

inline ReadyPredicate script_is_ready() {
    return reinterpret_cast<ReadyPredicate>(kScriptIsReady);
}

inline ReadyPredicate preview_is_ready() {
    return reinterpret_cast<ReadyPredicate>(kPreviewIsReady);
}

inline TriggerQuery input_trigger() {
    return reinterpret_cast<TriggerQuery>(kInputTrigger);
}

inline EventRequest event_request() {
    return reinterpret_cast<EventRequest>(kEventRequest);
}

// The original ARM sequence at 0x001E9DAC..0x001E9DC0 computes
// signed-remainder-by-four behavior with word operations. Keep every step
// unsigned so wrap and shifts are defined in C++ for every 32-bit input.
inline u32 normalize_signed_remainder_by_four(u32 provisional) {
    const u32 adjusted = provisional + 4u;
    const u32 correction = (0u - (adjusted >> 31)) >> 30;
    const u32 multiple = (adjusted + correction) & ~3u;
    return adjusted - multiple;
}

} // namespace

// Returns 0 when an original readiness gate branches to 0x001EA62C, and 1
// when the selected cursor/cache update reaches the original continuation
// 0x001E9DE0 (before its VFP blend clamp and the touch path).
extern "C" __attribute__((noinline)) u32 h1_navigation_caller_candidate() {
    // These two helpers take no formal arguments and return their result in
    // r0. The original arrives with incidental values in r0 (state 5, then
    // the first result); this candidate likewise leaves such values outside
    // the helper's formal contract.
    if (script_is_ready()() == 0) {
        return 0;
    }
    if (preview_is_ready()() == 0) {
        return 0;
    }

    // The original performs the singleton lookup only after both readiness
    // gates succeed (0x001E9D2C..0x001E9D38).
    auto* const global_work = reinterpret_cast<TitleMainNavigationWork* volatile*>(
        kTitleMainWorkSlot);
    TitleMainNavigationWork* const work = *global_work;
    work->timer_64 = work->timer_64 + 1.0f;

    // Preserve the original helper order, alias short-circuit, and two
    // directions' sequential order. The helpers observe the shared work
    // block through the title singleton.
    const auto trigger = input_trigger();
    if (trigger(5u) != 0 || trigger(0xEu) != 0) {
        work->selection = work->selection - 1u;
    }
    if (trigger(6u) != 0 || trigger(0xFu) != 0) {
        work->selection = work->selection + 1u;
    }

    const u32 selection = normalize_signed_remainder_by_four(work->selection);
    work->selection = selection;
    const u32 cached = work->cached_selection;
    if (selection != cached) {
        // ABI: UiEvent_Request has one formal u32 argument in r0 and no
        // stack arguments. r1-r3 are caller-saved/non-arguments at this call.
        event_request()(kSelectionChangedEvent);
        work->cached_selection = selection;
    }
    return 1;
}

// Deliberately wrong test control. This omits the original normalization's
// +4 correction and demonstrates why raw signed `% 4` is not equivalent at -1.
extern "C" __attribute__((noinline)) u32
h1_navigation_wrong_raw_signed_modulo(u32 provisional) {
    return static_cast<u32>(static_cast<s32>(provisional) % 4);
}
