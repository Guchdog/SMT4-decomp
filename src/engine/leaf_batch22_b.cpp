#include "types.h"

// Literal words after each unconditional return stay at their original PC-relative offsets.
// DECOMP_FUNC(0x00259544, 24)
extern "C" __attribute__((naked)) void script_vm_func_00259544() {
    asm volatile(
        "ldr r2, [pc, #0xc]\n"
        "mov r3, #1\n"
        "strb r3, [r2]\n"
        "strd r0, r1, [r2, #4]\n"
        "bx lr\n"
        ".word 0x004937a0\n"
    );
}
// DECOMP_FUNC(0x00269f1c, 24)
extern "C" __attribute__((naked)) void camp_func_00269f1c() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldr r1, [r1]\n"
        "cmp r1, #0\n"
        "strne r0, [r1, #0xd34]\n"
        "bx lr\n"
        ".word 0x0043daa8\n"
    );
}

// DECOMP_FUNC(0x0026ca0c, 24)
extern "C" __attribute__((naked)) void script_vm_func_0026ca0c() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "mov r1, #0\n"
        "ldr r0, [r0]\n"
        "str r1, [r0, #0x14]\n"
        "bx lr\n"
        ".word 0x0043e0f8\n"
    );
}

// DECOMP_FUNC(0x0026dd50, 24)
extern "C" __attribute__((naked)) void script_vm_func_0026dd50() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1e00\n"
        "ldrsb r0, [r0, #0x61]\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x00273a98, 24)
extern "C" __attribute__((naked)) void script_vm_func_00273a98() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "mov r1, #2\n"
        "ldr r0, [r0]\n"
        "str r1, [r0, #0x30]\n"
        "bx lr\n"
        ".word 0x00447a78\n"
    );
}

// DECOMP_FUNC(0x00282e54, 24)
extern "C" __attribute__((naked)) void battle_func_00282e54() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x9800\n"
        "add r0, r0, #0x74\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x00282f24, 24)
extern "C" __attribute__((naked)) void script_vm_func_00282f24() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bx lr\n"
        ".word 0x0043daa8\n"
    );
}

// DECOMP_FUNC(0x002891c8, 24)
extern "C" __attribute__((naked)) void ui_func_002891c8() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1f800\n"
        "add r0, r0, #0xe8\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x0028d838, 24)
extern "C" __attribute__((naked)) void camp_func_0028d838() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x400\n"
        "ldrsb r0, [r0, #0xcb]\n"
        "bx lr\n"
        ".word 0x0043da28\n"
    );
}

// DECOMP_FUNC(0x0028df3c, 24)
extern "C" __attribute__((naked)) void ui_func_0028df3c() {
    asm volatile(
        "add r1, r0, #1\n"
        "cmp r1, #3\n"
        "ldrlo r1, [pc, #4]\n"
        "strlo r0, [r1, #4]\n"
        "bx lr\n"
        ".word 0x0043e0b8\n"
    );
}

// DECOMP_FUNC(0x00291000, 24)
extern "C" __attribute__((naked)) void script_vm_func_00291000() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldr r1, [r1, #4]\n"
        "cmp r1, #0\n"
        "strbne r0, [r1, #0x4c9]\n"
        "bx lr\n"
        ".word 0x0043da28\n"
    );
}

// DECOMP_FUNC(0x00295780, 24)
extern "C" __attribute__((naked)) void script_vm_func_00295780() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldr r1, [r1]\n"
        "cmp r1, #0\n"
        "strbne r0, [r1, #0x2f4]\n"
        "bx lr\n"
        ".word 0x00434210\n"
    );
}

// DECOMP_FUNC(0x00299084, 24)
extern "C" __attribute__((naked)) void script_vm_func_00299084() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "cmp r0, r1\n"
        "movhs r0, #1\n"
        "movlo r0, #0\n"
        "bx lr\n"
        ".word 0x0000015e\n"
    );
}

// DECOMP_FUNC(0x0029a400, 24)
extern "C" __attribute__((naked)) void engine_func_0029a400() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldr r1, [r1, #4]\n"
        "add r1, r1, #0x1000\n"
        "strb r0, [r1, #0x2ee]\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x0029c6ac, 24)
extern "C" __attribute__((naked)) void camp_func_0029c6ac() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1000\n"
        "ldr r0, [r0, #0x2e4]\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x0029e248, 24)
extern "C" __attribute__((naked)) void camp_func_0029e248() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1e00\n"
        "ldrsb r0, [r0, #0x60]\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x002a0f50, 24)
extern "C" __attribute__((naked)) void script_vm_func_002a0f50() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "ldrbne r0, [r0, #0x4ca]\n"
        "bx lr\n"
        ".word 0x0043da28\n"
    );
}

// DECOMP_FUNC(0x002a0fac, 24)
extern "C" __attribute__((naked)) void camp_func_002a0fac() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1ec00\n"
        "add r0, r0, #0x18\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002adf14, 24)
extern "C" __attribute__((naked)) void engine_func_002adf14() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0xb800\n"
        "add r0, r0, #0x1a4\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002af630, 24)
extern "C" __attribute__((naked)) void func_002af630() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldr r2, [r1]\n"
        "add r0, r0, r2\n"
        "str r0, [r1]\n"
        "bx lr\n"
        ".word 0x004652a0\n"
    );
}

// DECOMP_FUNC(0x002b6e60, 24)
extern "C" __attribute__((naked)) void battle_func_002b6e60() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x9000\n"
        "add r0, r0, #0x198\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002b8ccc, 24)
extern "C" __attribute__((naked)) void camp_func_002b8ccc() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "ldrbne r0, [r0, #0x4c9]\n"
        "bx lr\n"
        ".word 0x0043da28\n"
    );
}

// DECOMP_FUNC(0x002b90a8, 24)
extern "C" __attribute__((naked)) void camp_func_002b90a8() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x600\n"
        "ldrsh r0, [r0, #0x4e]\n"
        "bx lr\n"
        ".word 0x0043dcb0\n"
    );
}

// DECOMP_FUNC(0x002bbd40, 24)
extern "C" __attribute__((naked)) void func_002bbd40() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1e800\n"
        "add r0, r0, #0x1ac\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002bf2b4, 24)
extern "C" __attribute__((naked)) void battle_func_002bf2b4() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "mov r2, #0\n"
        "ldr r0, [r1]\n"
        "str r2, [r1]\n"
        "bx lr\n"
        ".word 0x0044e328\n"
    );
}

// DECOMP_FUNC(0x002c0110, 24)
extern "C" __attribute__((naked)) void engine_func_002c0110() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldr r1, [r1, #4]\n"
        "cmp r1, #0\n"
        "strbne r0, [r1, #0xa11]\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002c2b1c, 24)
extern "C" __attribute__((naked)) void engine_func_002c2b1c() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x8000\n"
        "add r0, r0, #0x28c0\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002c2bd0, 24)
extern "C" __attribute__((naked)) void script_vm_func_002c2bd0() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "add r0, r0, r0, lsl #2\n"
        "add r0, r1, r0, lsl #2\n"
        "ldrb r0, [r0, #0x10]\n"
        "bx lr\n"
        ".word 0x004d9758\n"
    );
}

// DECOMP_FUNC(0x002cc1f4, 24)
extern "C" __attribute__((naked)) void camp_func_002cc1f4() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldr r1, [r1, #4]\n"
        "add r0, r1, r0, lsl #6\n"
        "add r0, r0, #0x4d0\n"
        "bx lr\n"
        ".word 0x0043da28\n"
    );
}

// DECOMP_FUNC(0x002ccb60, 24)
extern "C" __attribute__((naked)) void camp_func_002ccb60() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bx lr\n"
        ".word 0x0043daf8\n"
    );
}

// DECOMP_FUNC(0x002cf68c, 24)
extern "C" __attribute__((naked)) void camp_func_002cf68c() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0x500\n"
        "ldrsb r0, [r0, #0xf4]\n"
        "bx lr\n"
        ".word 0x0043dd50\n"
    );
}

// DECOMP_FUNC(0x002cf6a4, 24)
extern "C" __attribute__((naked)) void camp_func_002cf6a4() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0x500\n"
        "ldrsb r0, [r0, #0xf3]\n"
        "bx lr\n"
        ".word 0x0043dd50\n"
    );
}

// DECOMP_FUNC(0x002cf6bc, 24)
extern "C" __attribute__((naked)) void camp_func_002cf6bc() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0x500\n"
        "ldrsb r0, [r0, #0xc7]\n"
        "bx lr\n"
        ".word 0x0043dd50\n"
    );
}

// DECOMP_FUNC(0x002d1c1c, 24)
extern "C" __attribute__((naked)) void script_vm_func_002d1c1c() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "ldrsbne r0, [r0, #0xb]\n"
        "bx lr\n"
        ".word 0x00447060\n"
    );
}

// DECOMP_FUNC(0x002d652c, 24)
extern "C" __attribute__((naked)) void ui_func_002d652c() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldr r1, [r1]\n"
        "cmp r1, #0\n"
        "strbne r0, [r1, #0x5f2]\n"
        "bx lr\n"
        ".word 0x0043dfc0\n"
    );
}

// DECOMP_FUNC(0x002d8dd8, 24)
extern "C" __attribute__((naked)) void camp_func_002d8dd8() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "ldrbne r0, [r0, #0x66c]\n"
        "bx lr\n"
        ".word 0x0043dcf0\n"
    );
}

// DECOMP_FUNC(0x002d963c, 24)
extern "C" __attribute__((naked)) void camp_func_002d963c() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1200\n"
        "ldrsh r0, [r0, #0xfc]\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x002d9654, 24)
extern "C" __attribute__((naked)) void camp_func_002d9654() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bx lr\n"
        ".word 0x0043dd50\n"
    );
}

// DECOMP_FUNC(0x002efee8, 24)
extern "C" __attribute__((naked)) void camp_func_002efee8() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0x900\n"
        "ldrh r0, [r0, #0x80]\n"
        "bx lr\n"
        ".word 0x0043dd50\n"
    );
}

// DECOMP_FUNC(0x002eff00, 24)
extern "C" __attribute__((naked)) void camp_func_002eff00() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0x500\n"
        "ldrsb r0, [r0, #0xf5]\n"
        "bx lr\n"
        ".word 0x0043dd50\n"
    );
}

// DECOMP_FUNC(0x002eff18, 24)
extern "C" __attribute__((naked)) void ui_func_002eff18() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r1, [r0]\n"
        "mov r0, #1\n"
        "strb r0, [r1, #8]\n"
        "bx lr\n"
        ".word 0x0044dc50\n"
    );
}

// DECOMP_FUNC(0x00254840, 28)
extern "C" __attribute__((naked)) void camp_func_00254840() {
    asm volatile(
        "ldr r1, [pc, #0x10]\n"
        "ldr r1, [r1, #4]\n"
        "add r1, r1, #0x24800\n"
        "add r1, r1, #0x388\n"
        "strh r0, [r1, #0x24]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x00259490, 28)
extern "C" __attribute__((naked)) void func_00259490() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #8]\n"
        "cmp r0, #0\n"
        "movne r1, #1\n"
        "strbne r1, [r0, #0x30]\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x00259a38, 28)
extern "C" __attribute__((naked)) void camp_func_00259a38() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x24800\n"
        "add r0, r0, #0x3a4\n"
        "ldr r0, [r0]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x00259a54, 28)
extern "C" __attribute__((naked)) void camp_func_00259a54() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x24800\n"
        "add r0, r0, #0x3a8\n"
        "ldr r0, [r0]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x0025a0b4, 28)
extern "C" __attribute__((naked)) void script_vm_func_0025a0b4() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "addne r0, r0, #0x600\n"
        "ldrshne r0, [r0, #0x50]\n"
        "bx lr\n"
        ".word 0x0043dcb0\n"
    );
}

// DECOMP_FUNC(0x0025c508, 28)
extern "C" __attribute__((naked)) void func_0025c508() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #0x20]\n"
        "add r0, r0, #0x5400\n"
        "add r0, r0, #0xdc\n"
        "strb r1, [r0]\n"
        "bx lr\n"
        ".word 0x00439c88\n"
    );
}

// DECOMP_FUNC(0x002631a4, 28)
extern "C" __attribute__((naked)) void camp_func_002631a4() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x24800\n"
        "add r0, r0, #0x388\n"
        "ldrsh r0, [r0, #0x24]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x00276ba4, 28)
extern "C" __attribute__((naked)) void script_vm_func_00276ba4() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "mov r1, #1\n"
        "ldr r0, [r0]\n"
        "str r1, [r0, #0x30]\n"
        "str r1, [r0, #0x38]\n"
        "bx lr\n"
        ".word 0x00447a78\n"
    );
}

// DECOMP_FUNC(0x0027d6e4, 28)
extern "C" __attribute__((naked)) void script_vm_func_0027d6e4() {
    asm volatile(
        "ldr r3, [pc, #0x10]\n"
        "ldr r3, [r3]\n"
        "add ip, r3, #0xc\n"
        "stm ip, {r0, r1, r2}\n"
        "vstr s0, [r3, #0x18]\n"
        "bx lr\n"
        ".word 0x0044cdf0\n"
    );
}

// DECOMP_FUNC(0x0027dbfc, 28)
extern "C" __attribute__((naked)) void script_vm_func_0027dbfc() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1ec00\n"
        "add r0, r0, #0xd8\n"
        "ldrb r0, [r0]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x0027dd78, 28)
extern "C" __attribute__((naked)) void ui_func_0027dd78() {
    asm volatile(
        "ldr r1, [pc, #0x10]\n"
        "cmp r0, #0\n"
        "ldr r0, [r1, #4]\n"
        "ldreq r0, [r0, #0x80]\n"
        "ldrne r0, [r0, #0x84]\n"
        "bx lr\n"
        ".word 0x0044ea58\n"
    );
}

// DECOMP_FUNC(0x0027dd94, 28)
extern "C" __attribute__((naked)) void script_vm_func_0027dd94() {
    asm volatile(
        "ldr r1, [pc, #0x10]\n"
        "ldr r1, [r1, #4]\n"
        "add r1, r1, #0x1ec00\n"
        "add r1, r1, #0xd8\n"
        "strb r0, [r1]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x00289fc0, 28)
extern "C" __attribute__((naked)) void unite_func_00289fc0() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldrsb r0, [r0]\n"
        "cmp r0, #0\n"
        "movgt r0, #1\n"
        "movle r0, #0\n"
        "bx lr\n"
        ".word 0x0043da28\n"
    );
}

// DECOMP_FUNC(0x0028df54, 28)
extern "C" __attribute__((naked)) void battle_func_0028df54() {
    asm volatile(
        "ldr r1, [pc, #0x10]\n"
        "mov r2, #0\n"
        "ldr r1, [r1, #0x20]\n"
        "strb r2, [r1, #0x3b]\n"
        "str r0, [r1, #0xa8]\n"
        "bx lr\n"
        ".word 0x0044de98\n"
    );
}

// DECOMP_FUNC(0x00290a4c, 28)
extern "C" __attribute__((naked)) void camp_func_00290a4c() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1f000\n"
        "add r0, r0, #0x4e0\n"
        "ldr r0, [r0]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x00292e94, 28)
extern "C" __attribute__((naked)) void script_vm_func_00292e94() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1f400\n"
        "add r0, r0, #0xdc\n"
        "ldr r0, [r0]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002958a0, 28)
extern "C" __attribute__((naked)) void script_vm_func_002958a0() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "addne r0, r0, #0x200\n"
        "ldrsbne r0, [r0, #0xf4]\n"
        "bx lr\n"
        ".word 0x00434210\n"
    );
}

// DECOMP_FUNC(0x00295f90, 28)
extern "C" __attribute__((naked)) void script_vm_func_00295f90() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x9000\n"
        "add r0, r0, #0x870\n"
        "ldr r0, [r0]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x00297688, 28)
extern "C" __attribute__((naked)) void camp_func_00297688() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x24000\n"
        "add r0, r0, #0xbb0\n"
        "ldrb r0, [r0]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x0029a020, 28)
extern "C" __attribute__((naked)) void engine_func_0029a020() {
    asm volatile(
        "ldr r1, [pc, #0x10]\n"
        "ldr r1, [r1, #4]\n"
        "add r1, r1, #0x1c00\n"
        "add r1, r1, #0x2a4\n"
        "strb r0, [r1]\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x0029c74c, 28)
extern "C" __attribute__((naked)) void camp_func_0029c74c() {
    asm volatile(
        "ldr r1, [pc, #0x10]\n"
        "ldr r1, [r1, #4]\n"
        "add r1, r1, #0x1c00\n"
        "add r1, r1, #0x2b8\n"
        "strb r0, [r1]\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x0029c768, 28)
extern "C" __attribute__((naked)) void script_vm_func_0029c768() {
    asm volatile(
        "ldr r1, [pc, #0x10]\n"
        "ldr r1, [r1, #4]\n"
        "add r1, r1, #0x1e00\n"
        "add r1, r1, #0x62\n"
        "strb r0, [r1]\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x0029e2b0, 28)
extern "C" __attribute__((naked)) void camp_func_0029e2b0() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1000\n"
        "ldr r0, [r0, #0x2e8]\n"
        "sxtb r0, r0\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x0029eb14, 28)
extern "C" __attribute__((naked)) void ui_func_0029eb14() {
    asm volatile(
        "ldr r1, [pc, #0x10]\n"
        "ldr r1, [r1, #4]\n"
        "add r1, r1, #0x1e00\n"
        "add r1, r1, #0x61\n"
        "strb r0, [r1]\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x002a7540, 28)
extern "C" __attribute__((naked)) void ui_func_002a7540() {
    asm volatile(
        "ldr r1, [pc, #0x10]\n"
        "ldr r2, [r1, #8]\n"
        "strb r0, [r2, #0xa26]\n"
        "ldr r1, [r1, #4]\n"
        "strb r0, [r1, #0xa26]\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002b49d8, 28)
extern "C" __attribute__((naked)) void script_vm_func_002b49d8() {
    asm volatile(
        "cmp r0, #0x43\n"
        "ldrlo r1, [pc, #0xc]\n"
        "addlo r0, r1, r0, lsl #4\n"
        "ldrlo r0, [r0, #4]\n"
        "movhs r0, #0\n"
        "bx lr\n"
        ".word 0x0049382c\n"
    );
}

// DECOMP_FUNC(0x002b6e44, 28)
extern "C" __attribute__((naked)) void script_vm_func_002b6e44() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #8]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bx lr\n"
        ".word 0x0043e128\n"
    );
}

// DECOMP_FUNC(0x002bb608, 28)
extern "C" __attribute__((naked)) void func_002bb608() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #0x18]\n"
        "tst r0, #7\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002c0128, 28)
extern "C" __attribute__((naked)) void script_vm_func_002c0128() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "movne r1, #0x14\n"
        "strbne r1, [r0, #0xa11]\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002c1f28, 28)
extern "C" __attribute__((naked)) void engine_func_002c1f28() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r1, [r0, #4]\n"
        "cmp r1, #0\n"
        "ldrsblt r0, [r0]\n"
        "movge r0, #0\n"
        "bx lr\n"
        ".word 0x0043e0b8\n"
    );
}

// DECOMP_FUNC(0x002c31bc, 28)
extern "C" __attribute__((naked)) void engine_func_002c31bc() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldrb r1, [r0]\n"
        "cmp r1, #0\n"
        "ldrne r0, [r0, #8]\n"
        "ldreq r0, [r0, #0xc]\n"
        "bx lr\n"
        ".word 0x00465170\n"
    );
}

// DECOMP_FUNC(0x002cd6a0, 28)
extern "C" __attribute__((naked)) void func_002cd6a0() {
    asm volatile(
        "ldr r1, [pc, #0x10]\n"
        "mov r2, #4\n"
        "ldr r1, [r1]\n"
        "str r2, [r1, #0x14]\n"
        "strh r0, [r1, #0x18]\n"
        "bx lr\n"
        ".word 0x0043e0f8\n"
    );
}

// DECOMP_FUNC(0x002cdb50, 28)
extern "C" __attribute__((naked)) void func_002cdb50() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #8]\n"
        "ldrb r0, [r0, #0x7e]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002cdcc4, 28)
extern "C" __attribute__((naked)) void camp_func_002cdcc4() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "addne r0, r0, #0x1000\n"
        "ldrne r0, [r0, #0x158]\n"
        "bx lr\n"
        ".word 0x0043dcf0\n"
    );
}

// DECOMP_FUNC(0x002cf4c4, 28)
extern "C" __attribute__((naked)) void ui_func_002cf4c4() {
    asm volatile(
        "ldr r2, [pc, #0x10]\n"
        "ldr r2, [r2, #4]\n"
        "add r2, r2, #0x400\n"
        "add r2, r2, #0x3ec\n"
        "stm r2, {r0, r1}\n"
        "bx lr\n"
        ".word 0x0043dd20\n"
    );
}

// DECOMP_FUNC(0x002d73f4, 28)
extern "C" __attribute__((naked)) void camp_func_002d73f4() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0]\n"
        "ldrb r0, [r0, #0x40]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bx lr\n"
        ".word 0x0043daf8\n"
    );
}

// DECOMP_FUNC(0x002d8df0, 28)
extern "C" __attribute__((naked)) void camp_func_002d8df0() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "addne r0, r0, #0x1000\n"
        "ldrne r0, [r0, #0x154]\n"
        "bx lr\n"
        ".word 0x0043dcf0\n"
    );
}

// DECOMP_FUNC(0x002de940, 28)
extern "C" __attribute__((naked)) void func_002de940() {
    asm volatile(
        "vstr s0, [r0, #0x20]\n"
        "vstr s0, [r0, #0x24]\n"
        "vldr s1, [pc, #8]\n"
        "add r0, r0, #0x28\n"
        "vstmia r0, {s0, s1}\n"
        "bx lr\n"
        ".word 0x00000000\n"
    );
}

// DECOMP_FUNC(0x002df468, 28)
extern "C" __attribute__((naked)) void func_002df468() {
    asm volatile(
        "vstr s0, [r0, #0x20]\n"
        "vstr s0, [r0, #0x24]\n"
        "vldr s1, [pc, #8]\n"
        "add r0, r0, #0x28\n"
        "vstmia r0, {s0, s1}\n"
        "bx lr\n"
        ".word 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x002e05bc, 28)
extern "C" __attribute__((naked)) void func_002e05bc() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "mov r1, #1\n"
        "ldr r0, [r0, #0x20]\n"
        "strb r1, [r0, #0x3b]\n"
        "vstr s0, [r0, #0xa8]\n"
        "bx lr\n"
        ".word 0x0044de98\n"
    );
}

// DECOMP_FUNC(0x002e80f8, 28)
extern "C" __attribute__((naked)) void func_002e80f8() {
    asm volatile(
        "vstr s0, [r0, #0x20]\n"
        "vstr s0, [r0, #0x24]\n"
        "vldr s1, [pc, #8]\n"
        "add r0, r0, #0x28\n"
        "vstmia r0, {s0, s1}\n"
        "bx lr\n"
        ".word 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x002594ac, 32)
extern "C" __attribute__((naked)) void ui_func_002594ac() {
    asm volatile(
        "ldr r1, [pc, #0x14]\n"
        "mov r2, #0\n"
        "strb r2, [r1, #2]\n"
        "ldr r2, [r1, #0x18]\n"
        "orr r0, r0, r2\n"
        "str r0, [r1, #0x18]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x00259a18, 32)
extern "C" __attribute__((naked)) void camp_func_00259a18() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r1, [pc, #0x10]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x88\n"
        "ldrb r0, [r0, r1]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
        ".word 0x00024b26\n"
    );
}

// DECOMP_FUNC(0x0026b7cc, 32)
extern "C" __attribute__((naked)) void ui_func_0026b7cc() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0, #4]\n"
        "ldr r0, [r0, #0x10]\n"
        "cmp r0, #3\n"
        "movne r0, #1\n"
        "moveq r0, #0\n"
        "bx lr\n"
        ".word 0x0043da28\n"
    );
}

// DECOMP_FUNC(0x00273a78, 32)
extern "C" __attribute__((naked)) void script_vm_func_00273a78() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #0x34]\n"
        "cmp r0, #0xff\n"
        "movne r0, #1\n"
        "moveq r0, #0\n"
        "bx lr\n"
        ".word 0x00447a78\n"
    );
}

// DECOMP_FUNC(0x002892a0, 32)
extern "C" __attribute__((naked)) void func_002892a0() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "ldrne r0, [r0, #0x1c]\n"
        "cmpne r0, #0\n"
        "moveq r0, #0\n"
        "bx lr\n"
        ".word 0x0044db88\n"
    );
}

// DECOMP_FUNC(0x002897dc, 32)
extern "C" __attribute__((naked)) void script_vm_func_002897dc() {
    asm volatile(
        "ldr r3, [pc, #0x14]\n"
        "mvn ip, #0\n"
        "stm r3, {r0, r1, ip}\n"
        "add ip, r3, #0x10\n"
        "vstmia ip, {s0, s1, s2, s3, s4}\n"
        "str r2, [r3, #0xc]\n"
        "bx lr\n"
        ".word 0x0049fd14\n"
    );
}

// DECOMP_FUNC(0x0029c68c, 32)
extern "C" __attribute__((naked)) void camp_func_0029c68c() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0, #8]\n"
        "ldrb r0, [r0, #0x7c]\n"
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002a0f68, 32)
extern "C" __attribute__((naked)) void camp_func_002a0f68() {
    asm volatile(
        "ldr r1, [pc, #0x14]\n"
        "ldr r1, [r1, #4]\n"
        "cmp r1, #0\n"
        "addne r1, r1, #0x1c00\n"
        "addne r1, r1, #0x264\n"
        "strbne r0, [r1]\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x002a5058, 32)
extern "C" __attribute__((naked)) void ui_func_002a5058() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0, #4]\n"
        "add r1, r0, #0x88\n"
        "add r2, r0, #0x590\n"
        "add r0, r0, #0x80\n"
        "stm r0, {r1, r2}\n"
        "bx lr\n"
        ".word 0x0044ea58\n"
    );
}

// DECOMP_FUNC(0x002bb420, 32)
extern "C" __attribute__((naked)) void func_002bb420() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0, #0x18]\n"
        "and r0, r0, #7\n"
        "cmp r0, #2\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0044e380\n"
    );
}

// DECOMP_FUNC(0x002c43d4, 32)
extern "C" __attribute__((naked)) void func_002c43d4() {
    asm volatile(
        "ldr r1, [pc, #0x14]\n"
        "cmp r0, #0\n"
        "ldr r0, [r1, #8]\n"
        "orrne r0, r0, #1\n"
        "biceq r0, r0, #1\n"
        "str r0, [r1, #8]\n"
        "bx lr\n"
        ".word 0x004650a0\n"
    );
}

// DECOMP_FUNC(0x002c8b0c, 32)
extern "C" __attribute__((naked)) void func_002c8b0c() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "mov r1, #0\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0xe00\n"
        "strh r1, [r0, #0x3e]\n"
        "strh r1, [r0, #0x40]\n"
        "bx lr\n"
        ".word 0x00447e58\n"
    );
}

// DECOMP_FUNC(0x002dfab4, 32)
extern "C" __attribute__((naked)) void script_vm_func_002dfab4() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #2\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x00447600\n"
    );
}

// DECOMP_FUNC(0x002e313c, 32)
extern "C" __attribute__((naked)) void script_vm_func_002e313c() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0xd\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0043dd50\n"
    );
}

// DECOMP_FUNC(0x002ed564, 32)
extern "C" __attribute__((naked)) void camp_func_002ed564() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0, #8]\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #7\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0043dc20\n"
    );
}

// DECOMP_FUNC(0x002f3570, 32)
extern "C" __attribute__((naked)) void func_002f3570() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #0xc8]\n"
        "cmp r0, #0x3f000000\n"
        "movlt r0, #0\n"
        "movge r0, #1\n"
        "bx lr\n"
        ".word 0x00447060\n"
    );
}

// DECOMP_FUNC(0x002f3aac, 32)
extern "C" __attribute__((naked)) void func_002f3aac() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0]\n"
        "ldrb r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "movne r0, #0\n"
        "moveq r0, #1\n"
        "bx lr\n"
        ".word 0x00447a48\n"
    );
}

// DECOMP_FUNC(0x002f463c, 32)
extern "C" __attribute__((naked)) void func_002f463c() {
    asm volatile(
        "vmov s0, r1\n"
        "ldr r2, [pc, #0x10]\n"
        "ldr r1, [r2]\n"
        "vcvt.f32.s32 s0, s0\n"
        "str r0, [r1, #0x54]\n"
        "vstr s0, [r1, #0x58]\n"
        "bx lr\n"
        ".word 0x00447e88\n"
    );
}
