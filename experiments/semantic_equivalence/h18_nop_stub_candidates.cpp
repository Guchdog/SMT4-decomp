// QUARANTINED INSTRUCTION-EFFECT FIXTURE — NOT WHOLE-FUNCTION CANDIDATES.
// Each 4-byte MOV entry falls through into meaningful code at address+4.
// Empty functions below return and therefore do not reproduce the original
// containing function. Do not promote or link these as replacements.
#include <cstdint>

#define H18_STUB(address) \
    extern "C" __attribute__((noinline, used)) void candidate_##address() {}

H18_STUB(00235df4)
H18_STUB(0023de14)
H18_STUB(0026b0cc)
H18_STUB(0027375c)
H18_STUB(002767ac)
H18_STUB(002819f4)
H18_STUB(0028ec74)
H18_STUB(0028fde0)
H18_STUB(00295ea8)
H18_STUB(002a4db0)
H18_STUB(002ad46c)
H18_STUB(002ae64c)
H18_STUB(002b0204)
H18_STUB(002b6e40)
H18_STUB(002bac24)
H18_STUB(002bbb28)
H18_STUB(002bce44)
H18_STUB(002bd258)
H18_STUB(002bdd1c)
H18_STUB(002bf2b0)
H18_STUB(002bf9e4)

// Deliberately incorrect controls. These are not reconstruction candidates.
extern "C" __attribute__((naked, used)) void negative_clobber_r0() {
    asm volatile("mov r0, #0\n bx lr");
}
extern "C" __attribute__((naked, used)) void negative_clobber_r1() {
    asm volatile("mov r1, #0\n bx lr");
}
extern "C" __attribute__((naked, used)) void negative_clobber_flags() {
    asm volatile("cmp r0, #0\n bx lr");
}
extern "C" __attribute__((naked, used)) void negative_write_memory() {
    asm volatile("str r1, [r0]\n bx lr");
}
