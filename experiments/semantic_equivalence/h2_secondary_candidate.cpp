#include <cstdint>

namespace {
using u8 = std::uint8_t;
using u16 = std::uint16_t;
using s16 = std::int16_t;
using u32 = std::uint32_t;

using PairService = void (*)(void*);
using CounterService = void (*)(s16);
using TaskIsRegistered = u32 (*)(void*);
using TaskSetState = void (*)(void*, u32);

template <typename Function>
Function at(std::uintptr_t address) {
    return reinterpret_cast<Function>(address);
}

constexpr std::uintptr_t kCounterService = 0x002B9008;
constexpr std::uintptr_t kScriptCleanup = 0x002A755C;
constexpr std::uintptr_t kRelease = 0x002C4360;
constexpr std::uintptr_t kTaskIsRegistered = 0x002BF41C;
constexpr std::uintptr_t kTaskSetState = 0x002C45B8;
constexpr std::uintptr_t kWorkGlobal = 0x0044E2D0;

struct WorkPrefix {
    u32 calc_task;
    u8 fields[0x158 - sizeof(u32)];
};
static_assert(sizeof(WorkPrefix) == 0x158);

template <bool OmitLastFirstLoopCall, bool ReverseTwoResourceReleases>
void cleanup_orchestration(void*) {
    auto** const global_work = reinterpret_cast<WorkPrefix**>(kWorkGlobal);
    WorkPrefix* const work = *global_work;
    work->fields[0] = 1;  // work + 4

    u32 completed = 0;
    for (;;) {
        const s16 current = *reinterpret_cast<volatile s16*>(work->fields + 0x16);
        if (current <= static_cast<s16>(completed)) break;
        if constexpr (OmitLastFirstLoopCall) {
            if (current == static_cast<s16>(completed + 1)) break;
        }
        at<CounterService>(kCounterService)(current);
        ++completed;
    }

    completed = 0;
    for (;;) {
        const s16 current = *reinterpret_cast<volatile s16*>(work->fields + 0x20);
        if (current <= static_cast<s16>(completed)) break;
        at<CounterService>(kCounterService)(current);
        ++completed;
    }

    if (const u32 script = *reinterpret_cast<u32*>(work->fields + 0x150)) {
        at<PairService>(kScriptCleanup)(reinterpret_cast<void*>(script));
        *reinterpret_cast<u32*>(work->fields + 0x150) = 0;
    }

    u32* const first = reinterpret_cast<u32*>(work->fields + 0x148);  // +0x14c
    u32* const second = reinterpret_cast<u32*>(work->fields + 0x14c); // +0x150
    if constexpr (ReverseTwoResourceReleases) {
        if (*second) { at<PairService>(kRelease)(reinterpret_cast<void*>(*second)); *second = 0; }
        if (*first) { at<PairService>(kRelease)(reinterpret_cast<void*>(*first)); *first = 0; }
    } else {
        if (*first) { at<PairService>(kRelease)(reinterpret_cast<void*>(*first)); *first = 0; }
        if (*second) { at<PairService>(kRelease)(reinterpret_cast<void*>(*second)); *second = 0; }
    }

    if (at<TaskIsRegistered>(kTaskIsRegistered)(reinterpret_cast<void*>(work->calc_task))) {
        at<TaskSetState>(kTaskSetState)(reinterpret_cast<void*>(work->calc_task), 0);
    }

    if (WorkPrefix* const reloaded = *global_work) {
        at<PairService>(kRelease)(reloaded);
        *global_work = nullptr;
    }
}
}  // namespace

// Experiment ABI shim. r0 models the ignored original callback context; r1
// provides no extra state because the candidate reads the same absolute global
// and calls the pinned helper entries by address.
extern "C" void candidate_002caef0(void* ignored_context) {
    cleanup_orchestration<false, false>(ignored_context);
}

// Deliberate call-count negative control: omit the final helper call of loop 1.
extern "C" void candidate_002caef0_wrong_count(void* ignored_context) {
    cleanup_orchestration<true, false>(ignored_context);
}

// Deliberate order negative control: swap the +0x14c / +0x150 release calls.
extern "C" void candidate_002caef0_wrong_order(void* ignored_context) {
    cleanup_orchestration<false, true>(ignored_context);
}
