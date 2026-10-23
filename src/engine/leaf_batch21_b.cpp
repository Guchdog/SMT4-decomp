#include "types.h"

// Trailing literal words are bounded and referenced by in-function PC-relative loads.
// DECOMP_FUNC(0x002741f4, 12)
extern "C" __attribute__((naked)) void engine_func_002741f4() {
    asm volatile(
        "ldr r0, [pc]\n"
        "bx lr\n"
        ".word 0x00493784\n"
    );
}

// DECOMP_FUNC(0x002ad4f0, 12)
extern "C" __attribute__((naked)) void battle_func_002ad4f0() {
    asm volatile(
        "ldr r0, [pc]\n"
        "bx lr\n"
        ".word 0x00471a84\n"
    );
}

// DECOMP_FUNC(0x002b5b38, 12)
extern "C" __attribute__((naked)) void func_002b5b38() {
    asm volatile(
        "ldr r0, [pc]\n"
        "bx lr\n"
        ".word 0x004eac74\n"
    );
}

// DECOMP_FUNC(0x002b5f84, 12)
extern "C" __attribute__((naked)) void script_vm_func_002b5f84() {
    asm volatile(
        "ldr r0, [pc]\n"
        "bx lr\n"
        ".word 0x00471a38\n"
    );
}

// DECOMP_FUNC(0x002bb7b0, 12)
extern "C" __attribute__((naked)) void engine_func_002bb7b0() {
    asm volatile(
        "ldr r0, [pc]\n"
        "bx lr\n"
        ".word 0x004e6f08\n"
    );
}

// DECOMP_FUNC(0x002c5e20, 12)
extern "C" __attribute__((naked)) void script_vm_func_002c5e20() {
    asm volatile(
        "ldr r0, [pc]\n"
        "bx lr\n"
        ".word 0x00464b38\n"
    );
}

// DECOMP_FUNC(0x002c6bf4, 12)
extern "C" __attribute__((naked)) void func_002c6bf4() {
    asm volatile(
        "ldr r0, [pc]\n"
        "bx lr\n"
        ".word 0x004efca0\n"
    );
}

// DECOMP_FUNC(0x002cec9c, 12)
extern "C" __attribute__((naked)) void script_vm_func_002cec9c() {
    asm volatile(
        "ldr r0, [pc]\n"
        "bx lr\n"
        ".word 0x004bd04c\n"
    );
}

// DECOMP_FUNC(0x00256780, 16)
extern "C" __attribute__((naked)) void func_00256780() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #0x18]\n"
        "bx lr\n"
        ".word 0x00446db0\n"
    );
}

// DECOMP_FUNC(0x002582e8, 16)
extern "C" __attribute__((naked)) void func_002582e8() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0]\n"
        "bx lr\n"
        ".word 0x00433d10\n"
    );
}

// DECOMP_FUNC(0x0025a0a4, 16)
extern "C" __attribute__((naked)) void script_vm_func_0025a0a4() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrb r0, [r0]\n"
        "bx lr\n"
        ".word 0x0044e098\n"
    );
}

// DECOMP_FUNC(0x0025b968, 16)
extern "C" __attribute__((naked)) void script_vm_func_0025b968() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1]\n"
        "bx lr\n"
        ".word 0x00465040\n"
    );
}

// DECOMP_FUNC(0x0025b978, 16)
extern "C" __attribute__((naked)) void script_vm_func_0025b978() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0]\n"
        "bx lr\n"
        ".word 0x00465040\n"
    );
}

// DECOMP_FUNC(0x00262a44, 16)
extern "C" __attribute__((naked)) void func_00262a44() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0]\n"
        "bx lr\n"
        ".word 0x0043dd68\n"
    );
}

// DECOMP_FUNC(0x00269cb8, 16)
extern "C" __attribute__((naked)) void ui_func_00269cb8() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0]\n"
        "bx lr\n"
        ".word 0x004640d0\n"
    );
}

// DECOMP_FUNC(0x0026b844, 16)
extern "C" __attribute__((naked)) void ui_func_0026b844() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #4]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x0026b854, 16)
extern "C" __attribute__((naked)) void ui_func_0026b854() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #3]\n"
        "bx lr\n"
        ".word 0x0043e2f0\n"
    );
}

// DECOMP_FUNC(0x0026b864, 16)
extern "C" __attribute__((naked)) void ui_func_0026b864() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0]\n"
        "bx lr\n"
        ".word 0x0043e2f0\n"
    );
}

// DECOMP_FUNC(0x0028756c, 16)
extern "C" __attribute__((naked)) void engine_func_0028756c() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #0xf8]\n"
        "bx lr\n"
        ".word 0x0049fb1c\n"
    );
}

// DECOMP_FUNC(0x00289a18, 16)
extern "C" __attribute__((naked)) void script_vm_func_00289a18() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1, #3]\n"
        "bx lr\n"
        ".word 0x0043e0b8\n"
    );
}

// DECOMP_FUNC(0x00289a28, 16)
extern "C" __attribute__((naked)) void script_vm_func_00289a28() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #3]\n"
        "bx lr\n"
        ".word 0x0043e0b8\n"
    );
}

// DECOMP_FUNC(0x00289a38, 16)
extern "C" __attribute__((naked)) void script_vm_func_00289a38() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1, #2]\n"
        "bx lr\n"
        ".word 0x0043e0b8\n"
    );
}

// DECOMP_FUNC(0x00289a48, 16)
extern "C" __attribute__((naked)) void script_vm_func_00289a48() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #2]\n"
        "bx lr\n"
        ".word 0x0043e0b8\n"
    );
}

// DECOMP_FUNC(0x00293c98, 16)
extern "C" __attribute__((naked)) void ui_func_00293c98() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0]\n"
        "bx lr\n"
        ".word 0x00435d90\n"
    );
}

// DECOMP_FUNC(0x002972e8, 16)
extern "C" __attribute__((naked)) void ui_func_002972e8() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1]\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002a3494, 16)
extern "C" __attribute__((naked)) void camp_func_002a3494() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "ldr r0, [r1, r0, lsl #2]\n"
        "bx lr\n"
        ".word 0x00464b9c\n"
    );
}

// DECOMP_FUNC(0x002a44f8, 16)
extern "C" __attribute__((naked)) void script_vm_func_002a44f8() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "ldr r0, [r1, r0, lsl #2]\n"
        "bx lr\n"
        ".word 0x00464b7c\n"
    );
}

// DECOMP_FUNC(0x002a4508, 16)
extern "C" __attribute__((naked)) void script_vm_func_002a4508() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "ldr r0, [r1, r0, lsl #2]\n"
        "bx lr\n"
        ".word 0x00464bac\n"
    );
}

// DECOMP_FUNC(0x002a4518, 16)
extern "C" __attribute__((naked)) void script_vm_func_002a4518() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "ldr r0, [r1, r0, lsl #2]\n"
        "bx lr\n"
        ".word 0x00464ba4\n"
    );
}

// DECOMP_FUNC(0x002a462c, 16)
extern "C" __attribute__((naked)) void ui_func_002a462c() {
    asm volatile(
        "vldr s0, [pc, #4]\n"
        "vmul.f32 s0, s0, s0\n"
        "bx lr\n"
        ".word 0x10000000\n"
    );
}

// DECOMP_FUNC(0x002a84dc, 16)
extern "C" __attribute__((naked)) void func_002a84dc() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #0x10]\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002ad45c, 16)
extern "C" __attribute__((naked)) void func_002ad45c() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "str r0, [r1, #0x10]\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002ad4c0, 16)
extern "C" __attribute__((naked)) void func_002ad4c0() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrb r0, [r0, #2]\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002ad4d0, 16)
extern "C" __attribute__((naked)) void func_002ad4d0() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #0x1c]\n"
        "bx lr\n"
        ".word 0x00471a70\n"
    );
}

// DECOMP_FUNC(0x002ad4e0, 16)
extern "C" __attribute__((naked)) void func_002ad4e0() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0]\n"
        "bx lr\n"
        ".word 0x00471a70\n"
    );
}

// DECOMP_FUNC(0x002b3ca0, 16)
extern "C" __attribute__((naked)) void engine_func_002b3ca0() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #1]\n"
        "bx lr\n"
        ".word 0x00471a70\n"
    );
}

// DECOMP_FUNC(0x002bb410, 16)
extern "C" __attribute__((naked)) void func_002bb410() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0]\n"
        "bx lr\n"
        ".word 0x0044e3b0\n"
    );
}

// DECOMP_FUNC(0x002bb440, 16)
extern "C" __attribute__((naked)) void func_002bb440() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #0x14]\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002bb450, 16)
extern "C" __attribute__((naked)) void func_002bb450() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #0x18]\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002bb460, 16)
extern "C" __attribute__((naked)) void func_002bb460() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1, #6]\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002bb470, 16)
extern "C" __attribute__((naked)) void func_002bb470() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1, #5]\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002bb480, 16)
extern "C" __attribute__((naked)) void func_002bb480() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1, #0xa]\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002bb5b4, 16)
extern "C" __attribute__((naked)) void func_002bb5b4() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #1]\n"
        "bx lr\n"
        ".word 0x0044e458\n"
    );
}

// DECOMP_FUNC(0x002bb7a0, 16)
extern "C" __attribute__((naked)) void func_002bb7a0() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1, #0xc]\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002bb978, 16)
extern "C" __attribute__((naked)) void func_002bb978() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #2]\n"
        "bx lr\n"
        ".word 0x0044e360\n"
    );
}

// DECOMP_FUNC(0x002bc9c8, 16)
extern "C" __attribute__((naked)) void func_002bc9c8() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #1]\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002bff9c, 16)
extern "C" __attribute__((naked)) void script_vm_func_002bff9c() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrb r0, [r0, #0x1e5]\n"
        "bx lr\n"
        ".word 0x004c5634\n"
    );
}

// DECOMP_FUNC(0x002bffac, 16)
extern "C" __attribute__((naked)) void script_vm_func_002bffac() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrb r0, [r0, #0x1e4]\n"
        "bx lr\n"
        ".word 0x004c5634\n"
    );
}

// DECOMP_FUNC(0x002c14a8, 16)
extern "C" __attribute__((naked)) void func_002c14a8() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrb r0, [r0, #0xc]\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002c14e4, 16)
extern "C" __attribute__((naked)) void func_002c14e4() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1, #0xb]\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002c31d8, 16)
extern "C" __attribute__((naked)) void engine_func_002c31d8() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #8]\n"
        "bx lr\n"
        ".word 0x00465170\n"
    );
}

// DECOMP_FUNC(0x002c3618, 16)
extern "C" __attribute__((naked)) void func_002c3618() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0]\n"
        "bx lr\n"
        ".word 0x004651e8\n"
    );
}

// DECOMP_FUNC(0x002c3714, 16)
extern "C" __attribute__((naked)) void func_002c3714() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "str r0, [r1, #0x10]\n"
        "bx lr\n"
        ".word 0x004651e8\n"
    );
}

// DECOMP_FUNC(0x002c3724, 16)
extern "C" __attribute__((naked)) void func_002c3724() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #4]\n"
        "bx lr\n"
        ".word 0x004651e8\n"
    );
}

// DECOMP_FUNC(0x002c3b88, 16)
extern "C" __attribute__((naked)) void engine_func_002c3b88() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #4]\n"
        "bx lr\n"
        ".word 0x00471b48\n"
    );
}

// DECOMP_FUNC(0x002c3b98, 16)
extern "C" __attribute__((naked)) void engine_func_002c3b98() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0]\n"
        "bx lr\n"
        ".word 0x00471b48\n"
    );
}

// DECOMP_FUNC(0x002c540c, 16)
extern "C" __attribute__((naked)) void ui_func_002c540c() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #0x1c8]\n"
        "bx lr\n"
        ".word 0x004e39e0\n"
    );
}

// DECOMP_FUNC(0x002c57a4, 16)
extern "C" __attribute__((naked)) void func_002c57a4() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #9]\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002c57b4, 16)
extern "C" __attribute__((naked)) void func_002c57b4() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrb r0, [r0, #6]\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002c583c, 16)
extern "C" __attribute__((naked)) void engine_func_002c583c() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "ldr r0, [r1, r0, lsl #2]\n"
        "bx lr\n"
        ".word 0x00446da0\n"
    );
}

// DECOMP_FUNC(0x002c5e10, 16)
extern "C" __attribute__((naked)) void script_vm_func_002c5e10() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #0x44]\n"
        "bx lr\n"
        ".word 0x00464af0\n"
    );
}

// DECOMP_FUNC(0x002cc17c, 16)
extern "C" __attribute__((naked)) void func_002cc17c() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrb r0, [r0, #0x6c]\n"
        "bx lr\n"
        ".word 0x004d4680\n"
    );
}

// DECOMP_FUNC(0x002cc18c, 16)
extern "C" __attribute__((naked)) void func_002cc18c() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #0x90]\n"
        "bx lr\n"
        ".word 0x004d4880\n"
    );
}

// DECOMP_FUNC(0x002d568c, 16)
extern "C" __attribute__((naked)) void camp_func_002d568c() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #0x18]\n"
        "bx lr\n"
        ".word 0x004e411c\n"
    );
}

// DECOMP_FUNC(0x002ebb30, 16)
extern "C" __attribute__((naked)) void ui_func_002ebb30() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #0x10]\n"
        "bx lr\n"
        ".word 0x00465170\n"
    );
}

// DECOMP_FUNC(0x002ebdf0, 16)
extern "C" __attribute__((naked)) void func_002ebdf0() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #0x93]\n"
        "bx lr\n"
        ".word 0x004d4880\n"
    );
}

// DECOMP_FUNC(0x002ebe00, 16)
extern "C" __attribute__((naked)) void func_002ebe00() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #0x91]\n"
        "bx lr\n"
        ".word 0x004d4880\n"
    );
}

// DECOMP_FUNC(0x002ef814, 16)
extern "C" __attribute__((naked)) void script_vm_func_002ef814() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #0x240]\n"
        "bx lr\n"
        ".word 0x004bce8c\n"
    );
}

// DECOMP_FUNC(0x002f3470, 16)
extern "C" __attribute__((naked)) void script_vm_func_002f3470() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0]\n"
        "bx lr\n"
        ".word 0x004937a0\n"
    );
}

// DECOMP_FUNC(0x002feb94, 16)
extern "C" __attribute__((naked)) void ui_func_002feb94() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #2]\n"
        "bx lr\n"
        ".word 0x0043e2f0\n"
    );
}

// DECOMP_FUNC(0x002feba4, 16)
extern "C" __attribute__((naked)) void ui_func_002feba4() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #1]\n"
        "bx lr\n"
        ".word 0x0043e2f0\n"
    );
}

// DECOMP_FUNC(0x0025487c, 20)
extern "C" __attribute__((naked)) void camp_func_0025487c() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0x48\n"
        "bx lr\n"
        ".word 0x0043daa8\n"
    );
}

// DECOMP_FUNC(0x0026b830, 20)
extern "C" __attribute__((naked)) void ui_func_0026b830() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x80\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x0026f460, 20)
extern "C" __attribute__((naked)) void script_vm_func_0026f460() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #0xcf8]\n"
        "bx lr\n"
        ".word 0x0043daa8\n"
    );
}

// DECOMP_FUNC(0x0027de00, 20)
extern "C" __attribute__((naked)) void script_vm_func_0027de00() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "mov r0, #0\n"
        "strb r0, [r1]\n"
        "bx lr\n"
        ".word 0x004937a0\n"
    );
}

// DECOMP_FUNC(0x0027f13c, 20)
extern "C" __attribute__((naked)) void script_vm_func_0027f13c() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0]\n"
        "bx lr\n"
        ".word 0x00447e88\n"
    );
}

// DECOMP_FUNC(0x0028686c, 20)
extern "C" __attribute__((naked)) void func_0028686c() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0, #0x20]\n"
        "ldr r0, [r0, #0xc0]\n"
        "bx lr\n"
        ".word 0x0044de98\n"
    );
}

// DECOMP_FUNC(0x00289640, 20)
extern "C" __attribute__((naked)) void engine_func_00289640() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0, #0x20]\n"
        "ldr r0, [r0, #0xd0]\n"
        "bx lr\n"
        ".word 0x0044de98\n"
    );
}

// DECOMP_FUNC(0x00291140, 20)
extern "C" __attribute__((naked)) void script_vm_func_00291140() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0, #8]\n"
        "ldr r0, [r0, #0x18]\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002954b8, 20)
extern "C" __attribute__((naked)) void script_vm_func_002954b8() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "ldr r1, [r1, #4]\n"
        "strb r0, [r1, #0x4cb]\n"
        "bx lr\n"
        ".word 0x0043da28\n"
    );
}

// DECOMP_FUNC(0x00297674, 20)
extern "C" __attribute__((naked)) void script_vm_func_00297674() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0, #8]\n"
        "ldr r0, [r0, #0x1c]\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x00298fec, 20)
extern "C" __attribute__((naked)) void ui_func_00298fec() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "ldr r1, [r1, #4]\n"
        "str r0, [r1, #0x80]\n"
        "bx lr\n"
        ".word 0x0044ea58\n"
    );
}

// DECOMP_FUNC(0x0029bc1c, 20)
extern "C" __attribute__((naked)) void camp_func_0029bc1c() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "ldr r1, [r1]\n"
        "strb r0, [r1, #0x134]\n"
        "bx lr\n"
        ".word 0x00447e88\n"
    );
}

// DECOMP_FUNC(0x002a0dd4, 20)
extern "C" __attribute__((naked)) void camp_func_002a0dd4() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #0x194]\n"
        "bx lr\n"
        ".word 0x00447e88\n"
    );
}

// DECOMP_FUNC(0x002a8a08, 20)
extern "C" __attribute__((naked)) void camp_func_002a8a08() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x8c\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002b66ec, 20)
extern "C" __attribute__((naked)) void script_vm_func_002b66ec() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x90\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002b9094, 20)
extern "C" __attribute__((naked)) void camp_func_002b9094() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0, #4]\n"
        "ldrb r0, [r0, #8]\n"
        "bx lr\n"
        ".word 0x0043dcb0\n"
    );
}

// DECOMP_FUNC(0x002bb4c0, 20)
extern "C" __attribute__((naked)) void func_002bb4c0() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "mov r0, #0\n"
        "strb r0, [r1, #1]\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002bd100, 20)
extern "C" __attribute__((naked)) void func_002bd100() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "add r0, r0, r0, lsl #1\n"
        "add r0, r1, r0, lsl #5\n"
        "bx lr\n"
        ".word 0x004def48\n"
    );
}

// DECOMP_FUNC(0x002c0b94, 20)
extern "C" __attribute__((naked)) void ui_func_002c0b94() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x88\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002c1494, 20)
extern "C" __attribute__((naked)) void func_002c1494() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0, #0x18]\n"
        "and r0, r0, #7\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002c23e4, 20)
extern "C" __attribute__((naked)) void engine_func_002c23e4() {
    asm volatile(
        "vldr s0, [pc, #8]\n"
        "vstr s0, [r0, #0x50]\n"
        "vstr s0, [r0, #0x5c]\n"
        "bx lr\n"
        ".word 0x00000000\n"
    );
}

// DECOMP_FUNC(0x002c5218, 20)
extern "C" __attribute__((naked)) void ui_func_002c5218() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0, #4]\n"
        "ldr r0, [r0, #0x80]\n"
        "bx lr\n"
        ".word 0x0044ea58\n"
    );
}

// DECOMP_FUNC(0x002c85f0, 20)
extern "C" __attribute__((naked)) void func_002c85f0() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #0xcc]\n"
        "bx lr\n"
        ".word 0x00447060\n"
    );
}

// DECOMP_FUNC(0x002cf754, 20)
extern "C" __attribute__((naked)) void camp_func_002cf754() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "ldr r1, [r1]\n"
        "strh r0, [r1, #0xc]\n"
        "bx lr\n"
        ".word 0x0043dd90\n"
    );
}
// DECOMP_FUNC(0x002d65e8, 20)
extern "C" __attribute__((naked)) void nn_sdk_func_002d65e8() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "ldr r1, [r1, #4]\n"
        "strb r0, [r1, #0x4c4]\n"
        "bx lr\n"
        ".word 0x0043da28\n"
    );
}

// DECOMP_FUNC(0x002d8160, 20)
extern "C" __attribute__((naked)) void func_002d8160() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "mov r0, #1\n"
        "str r0, [r1, #0x54]\n"
        "bx lr\n"
        ".word 0x0044ea80\n"
    );
}

// DECOMP_FUNC(0x002d8bc0, 20)
extern "C" __attribute__((naked)) void camp_func_002d8bc0() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0, #8]\n"
        "ldr r0, [r0, #4]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002e28d4, 20)
extern "C" __attribute__((naked)) void ui_func_002e28d4() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "ldr r1, [r1, #4]\n"
        "strb r0, [r1, #0xa34]\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002e32b4, 20)
extern "C" __attribute__((naked)) void camp_func_002e32b4() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "ldr r1, [r1]\n"
        "strb r0, [r1, #0x20]\n"
        "bx lr\n"
        ".word 0x0043dd90\n"
    );
}
