// Reconstructed interior entry at 0x0015555C.  The preceding 0x00155540
// routine returns at 0x00155558; this callback is entered by BLX and uses the
// ARM hard-float argument/result convention (s0, s1, s2 -> s0).
static bool vfp_greater_than(float lhs, float rhs) {
    int result = 0;
    // VCMPE marks unordered operands with NZCV=0011, where GT is false.
    // Keep the signaling compare so FPSCR exception status matches the image.
    asm volatile("vcmpe.f32 %1, %2\n\t"
                 "vmrs APSR_nzcv, FPSCR\n\t"
                 "movgt %0, #1"
                 : "+r"(result) : "t"(lhs), "t"(rhs) : "cc");
    return result != 0;
}

static bool vfp_less(float lhs, float rhs) {
    int result = 0;
    // The original lower-bound path uses LO after VCMPE, not C++'s ordered
    // comparison lowering, so retain the exact FPSCR flags as well.
    asm volatile("vcmpe.f32 %1, %2\n\t"
                 "vmrs APSR_nzcv, FPSCR\n\t"
                 "movlo %0, #1"
                 : "+r"(result) : "t"(lhs), "t"(rhs) : "cc");
    return result != 0;
}

extern "C" float h1_type0_callback(float lower, float upper, float value) {
    // The original upper-clamp branches immediately only when value > upper.
    // For unordered operands GT is false, so execution reaches the lower
    // compare; LO is false there too and the input value is returned unchanged.
    if (vfp_greater_than(value, upper)) {
        return upper;
    }
    if (vfp_less(value, lower)) {
        value = lower;
    }
    return value;
}

// Deliberately wrong evidence control: ordered C++ comparisons preserve the
// same result for NaNs but lower to a quiet comparison, so FPSCR signaling
// invalid status differs from the original VCMPE sequence.
extern "C" float h1_type0_callback_wrong_nan(float lower, float upper,
                                               float value) {
    if (value > upper) {
        value = upper;
    }
    if (value < lower) {
        value = lower;
    }
    return value;
}
