#include <stdint.h>

using u32 = uint32_t;

static inline float exact_vmulf32(float source_value, float scale) {
    float result;
    __asm__ volatile("vmul.f32 %0, %1, %2"
                     : "=w"(result) : "w"(source_value), "w"(scale));
    return result;
}

#define SETUP_SCALE()                                                     \
    const u32* const links = object + 8;                                  \
    volatile float* const destination =                                   \
        reinterpret_cast<volatile float*>(static_cast<uintptr_t>(links[0])); \
    volatile const float* const source =                                  \
        reinterpret_cast<volatile const float*>(static_cast<uintptr_t>(links[1]))
#define SCALE_FIELD(offset)                                               \
    destination[(offset) / 4] =                                           \
        exact_vmulf32(source[(offset) / 4], scale)
#define DEFINE_SPARSE_SCALE(name, fields)                                 \
    extern "C" __attribute__((noinline, used)) void name(u32* object, float scale) { \
        SETUP_SCALE();                                                     \
        fields                                                              \
    }

// Each function has its own pinned ordered lane map in the companion runner.
DEFINE_SPARSE_SCALE(candidate_002dd08c,
    SCALE_FIELD(0x64); SCALE_FIELD(0x68); SCALE_FIELD(0x74); SCALE_FIELD(0x7C);
    SCALE_FIELD(0x84); SCALE_FIELD(0xC8); SCALE_FIELD(0xD0); SCALE_FIELD(0xDC);
    SCALE_FIELD(0xE4);)
DEFINE_SPARSE_SCALE(candidate_002e5ba4,
    SCALE_FIELD(0x64); SCALE_FIELD(0x68); SCALE_FIELD(0x74); SCALE_FIELD(0x7C);
    SCALE_FIELD(0x84); SCALE_FIELD(0xC8); SCALE_FIELD(0xD0); SCALE_FIELD(0xD8);
    SCALE_FIELD(0xDC);)
DEFINE_SPARSE_SCALE(candidate_0030c93c,
    SCALE_FIELD(0x64); SCALE_FIELD(0x68); SCALE_FIELD(0x74); SCALE_FIELD(0x7C);
    SCALE_FIELD(0x84); SCALE_FIELD(0xC8); SCALE_FIELD(0xDC); SCALE_FIELD(0xE4);
    SCALE_FIELD(0xE8);)
DEFINE_SPARSE_SCALE(candidate_0030c9b0,
    SCALE_FIELD(0x64); SCALE_FIELD(0x68); SCALE_FIELD(0x74); SCALE_FIELD(0x7C);
    SCALE_FIELD(0x84); SCALE_FIELD(0xC8); SCALE_FIELD(0xD8); SCALE_FIELD(0xE0);
    SCALE_FIELD(0xE4);)
DEFINE_SPARSE_SCALE(candidate_0031341c,
    SCALE_FIELD(0x64); SCALE_FIELD(0x68); SCALE_FIELD(0x74); SCALE_FIELD(0x7C);
    SCALE_FIELD(0x84); SCALE_FIELD(0xC8); SCALE_FIELD(0xD8); SCALE_FIELD(0xE0);
    SCALE_FIELD(0xE4);)
DEFINE_SPARSE_SCALE(candidate_00313578,
    SCALE_FIELD(0x64); SCALE_FIELD(0x68); SCALE_FIELD(0x74); SCALE_FIELD(0x7C);
    SCALE_FIELD(0x84); SCALE_FIELD(0xC8); SCALE_FIELD(0xD0); SCALE_FIELD(0xD8);
    SCALE_FIELD(0xDC);)
DEFINE_SPARSE_SCALE(candidate_002f293c,
    SCALE_FIELD(0x64); SCALE_FIELD(0x68); SCALE_FIELD(0x74); SCALE_FIELD(0x7C);
    SCALE_FIELD(0x84); SCALE_FIELD(0xC8); SCALE_FIELD(0xD0); SCALE_FIELD(0xE4);)
DEFINE_SPARSE_SCALE(candidate_00313490,
    SCALE_FIELD(0x64); SCALE_FIELD(0x68); SCALE_FIELD(0x74); SCALE_FIELD(0x7C);
    SCALE_FIELD(0x84); SCALE_FIELD(0xC8); SCALE_FIELD(0xCC); SCALE_FIELD(0xDC);)

extern "C" __attribute__((noinline, used)) void extension_negative_wrong_lane(
    u32* object, float scale) {
    SETUP_SCALE();
    SCALE_FIELD(0x64);
    destination[0x68 / 4] = exact_vmulf32(source[0x74 / 4], scale);
}

extern "C" __attribute__((noinline, used)) void extension_negative_omit_lane(
    u32* object, float scale) {
    SETUP_SCALE();
    SCALE_FIELD(0x64);
}

#undef DEFINE_SPARSE_SCALE
#undef SCALE_FIELD
#undef SETUP_SCALE
