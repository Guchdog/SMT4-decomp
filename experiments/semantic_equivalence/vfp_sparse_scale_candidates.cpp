#include <stdint.h>

using u8 = uint8_t;
using u32 = uint32_t;

// C++ may commute multiplication, but ARM VFP NaN payload propagation can
// depend on operand order. Preserve the reference's source-times-scale order.
static inline float exact_vmulf32(float source_value, float scale) {
    float result;
    __asm__ volatile("vmul.f32 %0, %1, %2"
                     : "=w"(result) : "w"(source_value), "w"(scale));
    return result;
}

// Each original loads destination/source pointers from object+0x20 and then
// performs ten ordered binary32 multiply-stores using the incoming s0 scale.
// Volatile accesses preserve the original order for overlapping buffers.
#define DEFINE_SPARSE_SCALE(name, penultimate_source, last_source)        \
    extern "C" __attribute__((noinline, used)) void name(                \
        u32* object, float scale) {                                       \
        const u32* const links = object + 8;                              \
        volatile float* const destination =                              \
            reinterpret_cast<volatile float*>(                           \
                static_cast<uintptr_t>(links[0]));                       \
        volatile const float* const source =                              \
            reinterpret_cast<volatile const float*>(                     \
                static_cast<uintptr_t>(links[1]));                       \
        destination[0x64 / 4] = exact_vmulf32(source[0x64 / 4], scale);   \
        destination[0x68 / 4] = exact_vmulf32(source[0x68 / 4], scale);   \
        destination[0x74 / 4] = exact_vmulf32(source[0x74 / 4], scale);   \
        destination[0x7C / 4] = exact_vmulf32(source[0x7C / 4], scale);   \
        destination[0x84 / 4] = exact_vmulf32(source[0x84 / 4], scale);   \
        destination[0xC8 / 4] = exact_vmulf32(source[0xC8 / 4], scale);   \
        destination[0xCC / 4] = exact_vmulf32(source[0xCC / 4], scale);   \
        destination[0xD4 / 4] = exact_vmulf32(source[0xD4 / 4], scale);   \
        destination[(penultimate_source) / 4] =                           \
            exact_vmulf32(source[(penultimate_source) / 4], scale);      \
        destination[(last_source) / 4] =                                 \
            exact_vmulf32(source[(last_source) / 4], scale);             \
    }

DEFINE_SPARSE_SCALE(candidate_002e5b24, 0xD8, 0xE0)
DEFINE_SPARSE_SCALE(candidate_002f29a4, 0xE4, 0xF0)
DEFINE_SPARSE_SCALE(candidate_0030c8bc, 0xD8, 0xE0)
DEFINE_SPARSE_SCALE(candidate_003134f8, 0xD8, 0xE0)

// Controls for the two independently observed behaviors: wrong member
// routing and omission of a populated field.
extern "C" __attribute__((noinline, used)) void negative_wrong_offset(
    u32* object, float scale) {
    const u32* const links = object + 8;
    volatile float* destination = reinterpret_cast<volatile float*>(
        static_cast<uintptr_t>(links[0]));
    volatile const float* source = reinterpret_cast<volatile const float*>(
        static_cast<uintptr_t>(links[1]));
    destination[0x64 / 4] = exact_vmulf32(source[0x68 / 4], scale);
}

extern "C" __attribute__((noinline, used)) void negative_omit_final(
    u32* object, float scale) {
    const u32* const links = object + 8;
    volatile float* destination = reinterpret_cast<volatile float*>(
        static_cast<uintptr_t>(links[0]));
    volatile const float* source = reinterpret_cast<volatile const float*>(
        static_cast<uintptr_t>(links[1]));
    destination[0x64 / 4] = exact_vmulf32(source[0x64 / 4], scale);
}
