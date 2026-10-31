#include <cstdint>
typedef uint32_t u32;

extern "C" void* _ZTV7AocIcon_00421e64;

extern "C" __attribute__((naked)) void h17_aocicon_init_candidate(void* self) {
    asm volatile(
        "ldr r2, 1f\n\t"
        "mov r1, #0\n\t"
        "str r1, [r0, #4]\n\t"
        "str r2, [r0]\n\t"
        "str r1, [r0, #8]\n\t"
        "bx lr\n\t"
        ".align 2\n"
        "1: .word _ZTV7AocIcon_00421e64"
    );
}

extern "C" __attribute__((naked)) void h17_aocicon_init_mutation(void* self) {
    asm volatile(
        "mov r1, #0\n\t"
        "str r1, [r0]\n\t"
        "str r1, [r0, #4]\n\t"
        "str r1, [r0, #8]\n\t"
        "bx lr"
    );
}
