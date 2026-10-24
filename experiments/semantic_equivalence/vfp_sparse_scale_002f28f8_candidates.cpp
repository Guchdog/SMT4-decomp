#include <stdint.h>

using u32 = uint32_t;

static inline float exact_vmulf32_002f28f8(float source_value, float scale) {
    float result;
    __asm__ volatile("vmul.f32 %0, %1, %2"
                     : "=w"(result) : "w"(source_value), "w"(scale));
    return result;
}

extern "C" __attribute__((noinline, used)) void candidate_002f28f8(
    u32* object, float scale) {
    const u32* const links = object + 8;
    volatile float* const destination = reinterpret_cast<volatile float*>(
        static_cast<uintptr_t>(links[0]));
    volatile const float* const source = reinterpret_cast<volatile const float*>(
        static_cast<uintptr_t>(links[1]));
    destination[0x64 / 4] = exact_vmulf32_002f28f8(source[0x64 / 4], scale);
    destination[0x68 / 4] = exact_vmulf32_002f28f8(source[0x68 / 4], scale);
    destination[0x74 / 4] = exact_vmulf32_002f28f8(source[0x74 / 4], scale);
    destination[0x7C / 4] = exact_vmulf32_002f28f8(source[0x7C / 4], scale);
    destination[0x84 / 4] = exact_vmulf32_002f28f8(source[0x84 / 4], scale);
}

extern "C" __attribute__((noinline, used)) void negative_wrong_lane_002f28f8(
    u32* object, float scale) {
    const u32* const links = object + 8;
    volatile float* const destination = reinterpret_cast<volatile float*>(
        static_cast<uintptr_t>(links[0]));
    volatile const float* const source = reinterpret_cast<volatile const float*>(
        static_cast<uintptr_t>(links[1]));
    destination[0x64 / 4] = exact_vmulf32_002f28f8(source[0x68 / 4], scale);
}

extern "C" __attribute__((noinline, used)) void negative_omit_lane_002f28f8(
    u32* object, float scale) {
    const u32* const links = object + 8;
    volatile float* const destination = reinterpret_cast<volatile float*>(
        static_cast<uintptr_t>(links[0]));
    volatile const float* const source = reinterpret_cast<volatile const float*>(
        static_cast<uintptr_t>(links[1]));
    destination[0x64 / 4] = exact_vmulf32_002f28f8(source[0x64 / 4], scale);
}
