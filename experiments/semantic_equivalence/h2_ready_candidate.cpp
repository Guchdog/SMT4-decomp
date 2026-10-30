// Experimental reconstruction of TitleConfig_IsReady (0x002FC0EC).
// The task-registration helper remains an explicit original-code dependency.

using u32 = unsigned int;

struct TitleConfigReadyWork {
    void* calc_task;
};

using TaskIsRegistered = u32 (*)(void* task);

static inline u32 call_task_is_registered(void* task) {
    const auto kTaskIsRegistered = reinterpret_cast<TaskIsRegistered>(0x002BF41Cu);
    return kTaskIsRegistered(task);
}

extern "C" __attribute__((used, noinline)) u32 candidate_002fc0ec() {
    auto* work = *reinterpret_cast<TitleConfigReadyWork* volatile*>(0x0044E2D0u);
    if (work == nullptr) {
        return 1;
    }

    // The title caller waits while this task remains registered. Once it has
    // been unregistered, state 10 may reset the title flow and return to state 5.
    return call_task_is_registered(work->calc_task) == 0 ? 1u : 0u;
}

extern "C" __attribute__((used, noinline)) u32 candidate_002fc0ec_bad() {
    // Deliberately wrong negative control: readiness is always reported.
    return 1;
}
