#include "types.h"

namespace {
using FadeGate = void (*)(void*, f32);

inline FadeGate fade_first() {
    return reinterpret_cast<FadeGate>(static_cast<std::uintptr_t>(0x002872A4u));
}

inline FadeGate fade_second() {
    return reinterpret_cast<FadeGate>(static_cast<std::uintptr_t>(0x0020FFA0u));
}

inline u32 load_word(const void* base, u32 offset) {
    return *reinterpret_cast<const u32*>(static_cast<const u8*>(base) + offset);
}

u32 run_title_fade(void* object, f32 fade_value, bool wrong_zero_boundary) {
    // The original preserves s0 across both calls. A C++ value parameter keeps
    // that input available even when either positive gate changes s0. Reload
    // object+8 after each external call, matching all three original loads.
    fade_first()(reinterpret_cast<void*>(load_word(object, 8)), fade_value);
    fade_second()(reinterpret_cast<void*>(load_word(object, 8)), fade_value);

    void* child = reinterpret_cast<void*>(load_word(object, 8));
    // Match the original's unconditional reload of the input fade into s0 at
    // 0x00210058, including the final-gate early-return path.
    __asm__ volatile("vmov.f32 s0, %0" : : "t"(fade_value) : "s0", "memory");
    const u32 final_gate = load_word(child, 0x68);
    if (wrong_zero_boundary ? static_cast<s32>(final_gate) < 0
                            : static_cast<s32>(final_gate) <= 0) {
        // Keep the original machine r0 for differential evidence. Callers
        // still need a separate contract before treating it as a return value.
        return reinterpret_cast<std::uintptr_t>(child);
    }

    // The original falls through into this adjacent body when the last gate
    // is positive. Keep its indirect callback and memory effects in the
    // pinned original implementation until that body is separately promoted.
    using FadeContinuation = u32 (*)(void*, f32);
    return reinterpret_cast<FadeContinuation>(
        static_cast<std::uintptr_t>(0x00210074u))(child, fade_value);
}
} // namespace

extern "C" u32 candidate_00210030(void* object, f32 fade_value) {
    return run_title_fade(object, fade_value, false);
}

extern "C" u32 wrong_candidate_00210030(void* object, f32 fade_value) {
    return run_title_fade(object, fade_value, true);
}
