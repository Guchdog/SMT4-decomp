#include <stdint.h>

// The pinned originals are `mov r0, r0; bx lr`. They leave every general
// register, NZCV, and memory unchanged. An empty C-linkage leaf is an
// intentionally untyped no-op candidate: it makes no assumptions about the
// callers' argument or return-value interpretation.
#define DEFINE_NOP(name) \
    extern "C" __attribute__((noinline, used)) void name(void) {}

DEFINE_NOP(candidate_0023a350)
DEFINE_NOP(candidate_0036a29c)
DEFINE_NOP(candidate_00381464)

// Deliberately wrong controls. They must be detected by the same comparison
// policy as the candidates, respectively for r0, a caller-saved register,
// NZCV, and ordinary RAM.
extern "C" __attribute__((noinline, used)) void negative_clobber_r0(void) {
    __asm__ volatile("mov r0, #0");
}

extern "C" __attribute__((noinline, used)) void negative_clobber_r1(void) {
    __asm__ volatile("mov r1, #0");
}

extern "C" __attribute__((noinline, used)) void negative_clobber_flags(void) {
    __asm__ volatile("cmp r0, r0" ::: "cc");
}

extern "C" __attribute__((noinline, used)) void negative_write_memory(
    volatile uint32_t* pointer) {
    *pointer = 0;
}
