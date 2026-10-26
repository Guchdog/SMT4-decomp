#include "types.h"

namespace {
using PreviewAnimCalc = s32 (*)(void* sprite);

constexpr uintptr_t kFrameTexGlobalSlot = 0x0043E278u;
constexpr uintptr_t kPreviewAnimCalc = 0x002BF9F0u;
constexpr u32 kPrimaryReadyFlag = 0xF2B;
constexpr u32 kSecondaryReadyFlag = 0x1C;
constexpr u32 kBusySignedByte = 0xD6D;
constexpr u32 kPreviewSprite = 0xD74;

template <u32 PrimaryFlagOffset, u32 PreviewSpriteOffset,
          bool ReversePrimaryBranch, bool ReverseHelperResult>
__attribute__((always_inline)) inline s32 evaluate_gate() {
    auto* const global_slot = reinterpret_cast<u8**>(kFrameTexGlobalSlot);
    u8* const scene = *global_slot;

    const bool primary_set = scene[PrimaryFlagOffset] != 0;
    if constexpr (ReversePrimaryBranch) {
        if (primary_set) {
            return 1;
        }
    } else {
        if (!primary_set) {
            return 1;
        }
    }

    if (scene[kSecondaryReadyFlag] == 0) {
        return 1;
    }

    const s8 busy = *reinterpret_cast<const s8*>(scene + kBusySignedByte);
    if (busy != 0) {
        return 0;
    }

    const auto calc = reinterpret_cast<PreviewAnimCalc>(kPreviewAnimCalc);
    const s32 calc_result = calc(scene + PreviewSpriteOffset);
    if constexpr (ReverseHelperResult) {
        return calc_result == 0 ? 1 : 0;
    }
    return calc_result != 0 ? 1 : 0;
}
} // namespace

// No formal arguments. The fixed scene pointer and preview sprite are read
// from the original global/object layout; only the external helper is opaque.
extern "C" s32 h1_preview_gate_candidate() {
    return evaluate_gate<kPrimaryReadyFlag, kPreviewSprite, false, false>();
}

// Deliberate wrong-offset control: pass the next byte as the sprite object.
extern "C" s32 negative_preview_gate_wrong_offset() {
    return evaluate_gate<kPrimaryReadyFlag, kPreviewSprite + 1, false, false>();
}

// Deliberate wrong-branch-polarity control for the primary ready flag.
extern "C" s32 negative_preview_gate_wrong_branch() {
    return evaluate_gate<kPrimaryReadyFlag, kPreviewSprite, true, false>();
}

// Deliberate helper-result-polarity control.
extern "C" s32 negative_preview_gate_wrong_helper_polarity() {
    return evaluate_gate<kPrimaryReadyFlag, kPreviewSprite, false, true>();
}
