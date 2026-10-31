#include <cstdint>
typedef uint32_t u32;

extern "C" void* g_CecSettingWork_0043daf8;

extern "C" __attribute__((naked)) u32 h17_campcec_getworkhandle_candidate() {
    asm volatile(
        "ldr r0, 1f\n\t"
        "ldr r0, [r0]\n\t"
        "ldrb r0, [r0, #0x40]\n\t"
        "cmp r0, #0\n\t"
        "movne r0, #1\n\t"
        "bx lr\n\t"
        ".align 2\n"
        "1: .word g_CecSettingWork_0043daf8"
    );
}

extern "C" __attribute__((naked)) u32 h17_campcec_getworkhandle_mutation() {
    asm volatile(
        "ldr r0, 1f\n\t"
        "ldr r0, [r0]\n\t"
        "ldrb r0, [r0, #0x40]\n\t"
        "cmp r0, #0\n\t"
        "moveq r0, #1\n\t"
        "movne r0, #0\n\t"
        "bx lr\n\t"
        ".align 2\n"
        "1: .word g_CecSettingWork_0043daf8"
    );
}
