#include "types.h"

namespace {
using IntegralFloatHelper = f32 (*)(f32 value);
using FloatDifferenceHelper = f32 (*)(f32 left, f32 right);

constexpr uintptr_t kIntegralFloatHelper = 0x002A337Cu;
constexpr uintptr_t kFloatDifferenceHelper = 0x0014D608u;

inline IntegralFloatHelper integral_float_helper() {
    return reinterpret_cast<IntegralFloatHelper>(kIntegralFloatHelper);
}

inline FloatDifferenceHelper float_difference_helper() {
    return reinterpret_cast<FloatDifferenceHelper>(kFloatDifferenceHelper);
}

// The original uses VCMPE + VMRS + BLE here. ARM BLE treats unordered as
// true (N != V), unlike the C++ expression `left <= right` for NaN.
inline bool arm_vcmpe_ble(f32 left, f32 right) {
    u32 take_ble;
    __asm__ volatile(
        "vcmpe.f32 %1, %2\n\t"
        "vmrs APSR_nzcv, FPSCR\n\t"
        "movle %0, #1\n\t"
        "movgt %0, #0"
        : "=&r"(take_ble)
        : "t"(left), "t"(right)
        : "cc");
    return take_ble != 0;
}

f32 run_type1_callback(void* context, f32 start, f32 end, f32 sample,
                       bool use_cxx_ordered_branch, bool skip_integral_helper) {
    (void)context;
    const f32 saved_start = start;
    const f32 zero = 0.0f;
    const f32 interval = end - saved_start;

    // Original 0x00151418 uses VCMP (quiet), then BEQ. If the interval is
    // exactly zero, it sets s0=start and branches directly to the epilogue.
    if (interval == zero) {
        return saved_start;
    }

    const f32 relative_sample = sample - saved_start;
    const bool take_nonnegative_path = use_cxx_ordered_branch
        ? (zero <= relative_sample)
        : arm_vcmpe_ble(zero, relative_sample);

    f32 normalized = zero;
    if (!take_nonnegative_path) {
        const f32 quotient = -relative_sample / interval;
        normalized = skip_integral_helper
            ? quotient
            : integral_float_helper()(quotient);
    }

    // Mirrors VADD, VMLA, then the direct ARM soft-float subtraction call.
    f32 adjusted_sample = relative_sample;
    if (!take_nonnegative_path) {
        const f32 offset = normalized + 1.0f;
        adjusted_sample += offset * interval;
    }
    const f32 difference = float_difference_helper()(adjusted_sample, interval);
    return difference + saved_start;
}
} // namespace

extern "C" __attribute__((noinline)) f32
candidate_00151404(void* context, f32 start, f32 end, f32 sample) {
    return run_type1_callback(context, start, end, sample, false, false);
}

// Negative control: C++ ordered <= is false for NaN, unlike ARM BLE after
// VCMPE, which takes the branch on unordered flags.
extern "C" __attribute__((noinline)) f32
wrong_ordered_nan_branch_00151404(void* context, f32 start, f32 end, f32 sample) {
    return run_type1_callback(context, start, end, sample, true, false);
}

// Negative control: substitutes the quotient for the original 0x002A337C
// helper result, demonstrating why the helper boundary cannot be elided.
extern "C" __attribute__((noinline)) f32
wrong_skip_integral_helper_00151404(void* context, f32 start, f32 end, f32 sample) {
    return run_type1_callback(context, start, end, sample, false, true);
}
