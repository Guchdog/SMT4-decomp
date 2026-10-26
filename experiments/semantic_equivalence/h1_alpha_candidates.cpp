#include <cstdint>
#include <cstddef>

namespace {

struct UiAlphaTarget {
    std::uint8_t reserved[0x40];
    float alpha;
};

struct UiAlphaChild {
    std::uint8_t reserved_00[0x34];
    std::int32_t alpha_enabled;
    std::uint8_t reserved_38[0x14];
    UiAlphaTarget* target;
    std::uint8_t reserved_50[0x24];
    float component_scale;
    float alpha;
};

static_assert(offsetof(UiAlphaChild, alpha_enabled) == 0x34);
static_assert(offsetof(UiAlphaChild, target) == 0x4C);
static_assert(offsetof(UiAlphaChild, component_scale) == 0x74);
static_assert(offsetof(UiAlphaChild, alpha) == 0x78);
static_assert(offsetof(UiAlphaTarget, alpha) == 0x40);

}  // namespace

extern "C" void candidate_0029bdb4(UiAlphaChild* child, float alpha) {
    child->alpha = alpha;
    if (child->alpha_enabled > 0) {
        // The original multiplies before checking the optional target pointer.
        // Preserve the original's unconditional +0x74 load even when target is null.
        const float component_scale = *reinterpret_cast<volatile const float*>(
            &child->component_scale);
        // The original reads +0x4c before multiplying; keep the read sequenced
        // before the VFP operation, including when the pointer is null.
        UiAlphaTarget* const target = *reinterpret_cast<UiAlphaTarget* volatile*>(
            &child->target);
        // Clang's ARMv6K target ignores STDC FENV_ACCESS; keep the VFP multiply
        // because the original updates FPSCR even when the target is null.
        float scaled_alpha;
        asm volatile("vmul.f32 %0, %1, %2"
                     : "=w"(scaled_alpha)
                     : "w"(component_scale), "w"(alpha)
                     : "memory");
        if (target != nullptr) {
            target->alpha = scaled_alpha;
        }
    }
}

// Deliberately incorrect fixture: writes the child alpha to +0x7C.
extern "C" __attribute__((naked)) void negative_wrong_offset() {
    asm volatile("vstr s0, [r0, #0x7c]\n bx lr\n");
}

