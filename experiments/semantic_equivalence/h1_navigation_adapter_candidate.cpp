#include <stdint.h>

using u8 = uint8_t;
using u32 = uint32_t;
using s32 = int32_t;

namespace {
struct TitleMainNavigationWork {
    u8 pad_00[0x08];
    u32 selection;
    u32 cached_selection;
    u8 pad_10[0x50];
    u8 flags_60_63[4];
    float timer_64;
};
static_assert(__builtin_offsetof(TitleMainNavigationWork, selection) == 8);
static_assert(__builtin_offsetof(TitleMainNavigationWork, cached_selection) == 0xC);
static_assert(__builtin_offsetof(TitleMainNavigationWork, timer_64) == 0x64);

using ReadyPredicate = s32 (*)();
using TriggerQuery = s32 (*)(u32);
using EventRequest = void (*)(u32);

constexpr uintptr_t kTitleMainWorkSlot = 0x0044E300u;
constexpr uintptr_t kScriptIsReady = 0x00289924u;
constexpr uintptr_t kPreviewIsReady = 0x0025A2BCu;
constexpr uintptr_t kInputTrigger = 0x002B902Cu;
constexpr uintptr_t kEventRequest = 0x002B91C4u;
constexpr u32 kSelectionChangedEvent = 0x0100016Cu;
constexpr uintptr_t kCandidateAddress = 0x01002000u;
constexpr uintptr_t kCapturedWorkMailbox = 0x01003F00u;
constexpr uintptr_t kWorkSlotAddress = 0x0044E300u;
constexpr uintptr_t kContinueAddress = 0x001E9DE0u;
constexpr uintptr_t kGateFailureAddress = 0x001EA62Cu;

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

inline u32 normalize_signed_remainder_by_four(u32 provisional) {
    const u32 adjusted = provisional + 4u;
    const u32 correction = (0u - (adjusted >> 31)) >> 30;
    const u32 multiple = (adjusted + correction) & ~3u;
    return adjusted - multiple;
}

u32 navigation_reduce(u32* captured_work_out) {
    if (script_is_ready()() == 0) return 0;
    if (preview_is_ready()() == 0) return 0;

    auto* const global_work = reinterpret_cast<TitleMainNavigationWork* volatile*>(
        kTitleMainWorkSlot);
    TitleMainNavigationWork* const work = *global_work;
    // Publish the precise pointer sampled after readiness. The shim must use
    // this value for R4 even if a later external hook mutates the singleton.
    *captured_work_out = static_cast<u32>(reinterpret_cast<uintptr_t>(work));
    work->timer_64 = work->timer_64 + 1.0f;

    const auto trigger = input_trigger();
    if (trigger(5u) != 0 || trigger(0xEu) != 0)
        work->selection = work->selection - 1u;
    if (trigger(6u) != 0 || trigger(0xFu) != 0)
        work->selection = work->selection + 1u;

    const u32 selection = normalize_signed_remainder_by_four(work->selection);
    work->selection = selection;
    const u32 cached = work->cached_selection;
    if (selection != cached) {
        event_request()(kSelectionChangedEvent);
        work->cached_selection = selection;
    }
    return 1;
}
} // namespace

extern "C" __attribute__((noinline)) u32
h1_navigation_adapter_candidate(u32* captured_work_out) {
    return navigation_reduce(captured_work_out);
}

// This naked tail shim executes at the original inline-window entry. It calls
// the ordinary AAPCS candidate, then resumes the original callback at the
// status-specific continuation without returning to its caller.
extern "C" __attribute__((naked, noinline)) void h1_navigation_adapter_shim() {
    __asm__ volatile(
        "ldr r0, =0x01003F00\n"
        "ldr r12, =0x01002000\n"
        "blx r12\n"
        "cmp r0, #0\n"
        "beq 1f\n"
        "ldr r4, =0x01003F00\n"
        "ldr r4, [r4]\n"
        "ldr r8, =0x0044E300\n"
        "ldr r12, =0x3f800000\n"
        "vmov s17, r12\n"
        "ldr r12, =0x001E9DE0\n"
        "bx r12\n"
        "1: ldr r12, =0x001EA62C\n"
        "bx r12\n"
        ".ltorg\n");
}

// Negative control: a failed gate incorrectly resumes the success body.
extern "C" __attribute__((naked, noinline)) void
h1_navigation_wrong_status_target_shim() {
    __asm__ volatile(
        "ldr r0, =0x01003F00\n"
        "ldr r12, =0x01002000\n"
        "blx r12\n"
        "cmp r0, #0\n"
        "beq 1f\n"
        "ldr r4, =0x01003F00\n"
        "ldr r4, [r4]\n"
        "ldr r8, =0x0044E300\n"
        "ldr r12, =0x3f800000\n"
        "vmov s17, r12\n"
        "ldr r12, =0x001E9DE0\n"
        "bx r12\n"
        "1: ldr r4, =0x01003F00\n"
        "ldr r4, [r4]\n"
        "ldr r8, =0x0044E300\n"
        "ldr r12, =0x3f800000\n"
        "vmov s17, r12\n"
        "ldr r12, =0x001E9DE0\n"
        "bx r12\n"
        ".ltorg\n");
}

// Negative control: resume success without restoring the original live s17.
extern "C" __attribute__((naked, noinline)) void
h1_navigation_missing_s17_shim() {
    __asm__ volatile(
        "ldr r0, =0x01003F00\n"
        "ldr r12, =0x01002000\n"
        "blx r12\n"
        "cmp r0, #0\n"
        "beq 1f\n"
        "ldr r4, =0x01003F00\n"
        "ldr r4, [r4]\n"
        "ldr r8, =0x0044E300\n"
        "ldr r12, =0x001E9DE0\n"
        "bx r12\n"
        "1: ldr r12, =0x001EA62C\n"
        "bx r12\n"
        ".ltorg\n");
}

// Negative control: reread the mutable singleton instead of using the
// captured work pointer. The adversarial mutation must make this fail.
extern "C" __attribute__((naked, noinline)) void
h1_navigation_reload_pointer_shim() {
    __asm__ volatile(
        "ldr r0, =0x01003F00\n"
        "ldr r12, =0x01002000\n"
        "blx r12\n"
        "cmp r0, #0\n"
        "beq 1f\n"
        "ldr r8, =0x0044E300\n"
        "ldr r4, [r8]\n"
        "ldr r12, =0x3f800000\n"
        "vmov s17, r12\n"
        "ldr r12, =0x001E9DE0\n"
        "bx r12\n"
        "1: ldr r12, =0x001EA62C\n"
        "bx r12\n"
        ".ltorg\n");
}
