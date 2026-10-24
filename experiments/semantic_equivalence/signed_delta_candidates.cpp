#include <stdint.h>

// The original leaves use an ARM LDRD followed by CMP and two conditional,
// non-S instructions. Keep the exact instructions: ordinary C++ cannot
// promise preservation of the CMP-produced NZCV flags or LDRD access shape.
#define SIGNED_DELTA_FUNCTION(name, offset)                                      \
    extern "C" __attribute__((noinline, used)) int32_t name(                    \
        const uint32_t* object) {                                                \
        register uint32_t result asm("r0") =                                    \
            static_cast<uint32_t>(reinterpret_cast<uintptr_t>(object));          \
        asm volatile(                                                            \
            "ldrd r0, r1, [r0, #%c2]\n\t"                                      \
            "cmp r1, r0\n\t"                                                   \
            "movge r0, #0\n\t"                                                 \
            "sublt r0, r0, r1"                                                  \
            : "+r"(result)                                                      \
            : "i"(0), "i"(offset)                                              \
            : "r1", "cc", "memory");                                         \
        return static_cast<int32_t>(result);                                     \
    }

SIGNED_DELTA_FUNCTION(candidate_001220c4, 0x6c)
SIGNED_DELTA_FUNCTION(candidate_001220d8, 0x7c)

// Negative controls are deliberately wrong in one observable dimension.
extern "C" __attribute__((noinline, used)) int32_t wrong_offset_001220c4(
    const uint32_t* object) {
    register uint32_t result asm("r0") =
        static_cast<uint32_t>(reinterpret_cast<uintptr_t>(object));
    asm volatile("ldrd r0, r1, [r0, #0x70]\n\t"
                 "cmp r1, r0\n\t"
                 "movge r0, #0\n\t"
                 "sublt r0, r0, r1"
                 : "+r"(result) : : "r1", "cc", "memory");
    return static_cast<int32_t>(result);
}

extern "C" __attribute__((noinline, used)) int32_t wrong_signedness_001220c4(
    const uint32_t* object) {
    register uint32_t result asm("r0") =
        static_cast<uint32_t>(reinterpret_cast<uintptr_t>(object));
    asm volatile("ldrd r0, r1, [r0, #0x6c]\n\t"
                 "cmp r1, r0\n\t"
                 "movhs r0, #0\n\t"
                 "sublo r0, r0, r1"
                 : "+r"(result) : : "r1", "cc", "memory");
    return static_cast<int32_t>(result);
}

extern "C" __attribute__((noinline, used)) int32_t wrong_subtrahend_order_001220c4(
    const uint32_t* object) {
    register uint32_t result asm("r0") =
        static_cast<uint32_t>(reinterpret_cast<uintptr_t>(object));
    asm volatile("ldrd r0, r1, [r0, #0x6c]\n\t"
                 "cmp r1, r0\n\t"
                 "movge r0, #0\n\t"
                 "sublt r0, r1, r0"
                 : "+r"(result) : : "r1", "cc", "memory");
    return static_cast<int32_t>(result);
}

#undef SIGNED_DELTA_FUNCTION
