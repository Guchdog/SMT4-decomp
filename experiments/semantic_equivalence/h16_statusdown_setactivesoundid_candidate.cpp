#include <cstdint>
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" void* g_SoundCtx_0044e190;

extern "C" __attribute__((naked)) void h16_statusdown_setactivesoundid_candidate(u16 soundId) {
    asm volatile(
        "ldr r1, 1f\n\t"
        "ldr r1, [r1]\n\t"
        "cmp r1, #0\n\t"
        "addne r1, r1, #0x400\n\t"
        "strhne r0, [r1, #0x7e]\n\t"
        "bx lr\n\t"
        ".align 2\n"
        "1: .word g_SoundCtx_0044e190"
    );
}

extern "C" __attribute__((naked)) void h16_statusdown_setactivesoundid_mutation(u16 soundId) {
    asm volatile(
        "ldr r1, 1f\n\t"
        "ldr r1, [r1]\n\t"
        "cmp r1, #0\n\t"
        "addne r1, r1, #0x400\n\t"
        "mvn r0, r0\n\t"
        "strhne r0, [r1, #0x7e]\n\t"
        "bx lr\n\t"
        ".align 2\n"
        "1: .word g_SoundCtx_0044e190"
    );
}
