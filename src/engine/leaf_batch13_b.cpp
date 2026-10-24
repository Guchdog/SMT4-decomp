#include "types.h"

// DECOMP_FUNC(0x0023c22c, 72)
extern "C" __attribute__((naked)) void func_0023c22c() {
    asm volatile(
        "ldr r0, [r0]\n"
        "add r0, r0, #0x4400\n"
        "add r0, r0, #0xa8\n"
        "ldr r0, [r0]\n"
        "tst r0, #4\n"
        "movne r0, #0\n"
        "bne .L_func_0023c22c_0023c270\n"
        "add r0, r2, r2, lsl #2\n"
        "add r0, r1, r0, lsl #1\n"
        "add r1, r0, #0x900\n"
        "ldrh r0, [r1, #0xd4]\n"
        "add r0, r0, r3\n"
        "cmp r0, #0\n"
        "strhge r0, [r1, #0xd4]\n"
        "mov r0, #0\n"
        "strhlt r0, [r1, #0xd4]\n"
        "movlt r0, #1\n"
        ".L_func_0023c22c_0023c270:\n"
        "bx lr\n"
    );
}
// DECOMP_FUNC(0x002aa268, 72)
extern "C" __attribute__((naked)) void camp_func_002aa268() {
    asm volatile(
        "ldr ip, [r0, #0x64]\n"
        "cmp ip, #0\n"
        "beq .L_camp_func_002aa268_002aa2ac\n"
        "strh r1, [r0, #0x68]\n"
        "mov r3, #0\n"
        "add r1, r1, r1, lsl #1\n"
        "strh r3, [r0, #0x6a]\n"
        "strb r3, [r0, #0x88]\n"
        "add r1, ip, r1, lsl #2\n"
        "strb r3, [r0, #0x8a]\n"
        "cmp r2, #0\n"
        "strb r2, [r0, #0x6c]\n"
        "ldrne r1, [r1, #4]\n"
        "ldreq r1, [r1]\n"
        "str r1, [r0, #0x24]\n"
        "str r1, [r0, #0x28]\n"
        "str r1, [r0, #0x2c]\n"
        ".L_camp_func_002aa268_002aa2ac:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0034ef74, 72)
extern "C" __attribute__((naked)) void func_0034ef74() {
    asm volatile(
        "ldr r1, [r0, #0x58]\n"
        "ldr r2, [r0, #0x5c]\n"
        "subs r1, r1, r2\n"
        "beq .L_func_0034ef74_0034efb4\n"
        "ldr r1, [r0, #0x5c]\n"
        "and r1, r1, #3\n"
        "add r1, r1, r1, lsl #2\n"
        "add r1, r0, r1, lsl #2\n"
        "ldrb r1, [r1, #0x18]\n"
        "cmp r1, #0\n"
        "beq .L_func_0034ef74_0034efb4\n"
        "ldr r1, [r0, #0x5c]\n"
        "add r1, r1, #1\n"
        "str r1, [r0, #0x5c]\n"
        "mov r0, #1\n"
        "bx lr\n"
        ".L_func_0034ef74_0034efb4:\n"
        "mov r0, #0\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x001579d8, 76)
extern "C" __attribute__((naked)) void func_001579d8() {
    asm volatile(
        "ldr r2, [r0, #8]\n"
        "add r3, r0, #8\n"
        "cmp r2, r3\n"
        "bxeq lr\n"
        "str r4, [sp, #-4]!\n"
        ".L_func_001579d8_001579ec:\n"
        "ldrb r4, [r2, #-0x44]\n"
        "mov r3, r2\n"
        "ldr r2, [r2]\n"
        "cmp r4, #0\n"
        "mov ip, r2\n"
        "beq .L_func_001579d8_00157a10\n"
        "ldrh r4, [r3, #-0x38]\n"
        "orr r4, r4, r1\n"
        "strh r4, [r3, #-0x38]\n"
        ".L_func_001579d8_00157a10:\n"
        "add r3, r0, #8\n"
        "cmp ip, r3\n"
        "bne .L_func_001579d8_001579ec\n"
        "pop {r4}\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0015d568, 76)
extern "C" __attribute__((naked)) void func_0015d568() {
    asm volatile(
        "ldrb r1, [r0, #0x56]\n"
        "cmp r1, #0\n"
        "beq .L_func_0015d568_0015d5b0\n"
        "mov r2, #0\n"
        "strb r2, [r0, #0x56]\n"
        "str r2, [r0, #4]\n"
        "str r2, [r0, #8]\n"
        "str r2, [r0, #0xc]\n"
        "str r2, [r0, #0x10]\n"
        "ldrb r1, [r0, #0x55]\n"
        "cmp r1, #0\n"
        "movne r3, #0\n"
        "beq .L_func_0015d568_0015d5b0\n"
        ".L_func_0015d568_0015d59c:\n"
        "add ip, r0, r3, lsl #2\n"
        "subs r1, r1, #1\n"
        "add r3, r3, #1\n"
        "str r2, [ip, #0x1c]\n"
        "bne .L_func_0015d568_0015d59c\n"
        ".L_func_0015d568_0015d5b0:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x001ee3ac, 76)
extern "C" __attribute__((naked)) void func_001ee3ac() {
    asm volatile(
        "ldr r0, [r0, #0x28]\n"
        "lsl r0, r0, #0x17\n"
        "lsr r0, r0, #0x1c\n"
        "cmp r0, #9\n"
        "ldrlo pc, [pc, r0, lsl #2]\n"
        "b .L_func_001ee3ac_001ee3f0\n"
        ".word 0x001ee3f0\n"
        ".word 0x001ee3e8\n"
        ".word 0x001ee3f0\n"
        ".word 0x001ee3e8\n"
        ".word 0x001ee3f0\n"
        ".word 0x001ee3e8\n"
        ".word 0x001ee3e8\n"
        ".word 0x001ee3f0\n"
        ".word 0x001ee3e8\n"
        "mov r0, #1\n"
        "bx lr\n"
        ".L_func_001ee3ac_001ee3f0:\n"
        "mov r0, #0\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00232ab4, 76)
extern "C" __attribute__((naked)) void func_00232ab4() {
    asm volatile(
        "ldr r2, [r0]\n"
        "ldr r1, [r2]\n"
        "ldrb r3, [r2, #0xc]\n"
        "ldrb ip, [r1, #0xc]\n"
        "cmp ip, r3\n"
        "bne .L_func_00232ab4_00232afc\n"
        "ldr r3, [r1, #4]\n"
        "vldr s0, [r2, #8]\n"
        "str r3, [r2]\n"
        "ldr r2, [r0]\n"
        "str r2, [r1, #4]\n"
        "str r1, [r0]\n"
        "ldr r2, [r1, #4]\n"
        "vstr s0, [r1, #8]\n"
        "ldr r0, [r0]\n"
        "str r0, [r2, #8]\n"
        "ldr r0, [r2]\n"
        "str r2, [r0, #8]\n"
        ".L_func_00232ab4_00232afc:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00248744, 76)
extern "C" __attribute__((naked)) void func_00248744() {
    asm volatile(
        "cmp r0, #0\n"
        "beq .L_func_00248744_0024878c\n"
        "ldrh r2, [r0, #0x34]\n"
        "strh r2, [r1]\n"
        "ldrh r2, [r0, #0x36]\n"
        "strh r2, [r1, #2]\n"
        "ldrh r2, [r0, #0x38]\n"
        "strh r2, [r1, #4]\n"
        "ldrh r2, [r0, #0x3a]\n"
        "strh r2, [r1, #6]\n"
        "ldrh r2, [r0, #0x3c]\n"
        "strh r2, [r1, #8]\n"
        "ldrh r2, [r0, #0x3e]\n"
        "strh r2, [r1, #0xa]\n"
        "ldrh r2, [r0, #0x40]\n"
        "strh r2, [r1, #0xc]\n"
        "ldrh r0, [r0, #0x42]\n"
        "strh r0, [r1, #0xe]\n"
        ".L_func_00248744_0024878c:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002acb8c, 76)
extern "C" __attribute__((naked)) void func_002acb8c() {
    asm volatile(
        "mov ip, r0\n"
        "mov r0, r2\n"
        "cmp r1, r0\n"
        "push {r4, r5}\n"
        "movne r5, #0\n"
        "beq .L_func_002acb8c_002acbd0\n"
        ".L_func_002acb8c_002acba4:\n"
        "ldm r1, {r3, r4}\n"
        "cmp r3, r0\n"
        "str r4, [r3, #4]\n"
        "str r3, [r4]\n"
        "ldr r2, [ip]\n"
        "sub r2, r2, #1\n"
        "str r2, [ip]\n"
        "str r5, [r1]\n"
        "str r5, [r1, #4]\n"
        "mov r1, r3\n"
        "bne .L_func_002acb8c_002acba4\n"
        ".L_func_002acb8c_002acbd0:\n"
        "pop {r4, r5}\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002bb170, 76)
extern "C" __attribute__((naked)) void func_002bb170() {
    asm volatile(
        "mov r3, r0\n"
        "str r4, [sp, #-4]!\n"
        "ldr r0, [r1]\n"
        "cmp r1, r0\n"
        "movne r4, #0\n"
        "beq .L_func_002bb170_002bb1b4\n"
        ".L_func_002bb170_002bb188:\n"
        "ldm r1, {r2, ip}\n"
        "cmp r2, r0\n"
        "str ip, [r2, #4]\n"
        "str r2, [ip]\n"
        "ldr ip, [r3]\n"
        "sub ip, ip, #1\n"
        "str ip, [r3]\n"
        "str r4, [r1]\n"
        "str r4, [r1, #4]\n"
        "mov r1, r2\n"
        "bne .L_func_002bb170_002bb188\n"
        ".L_func_002bb170_002bb1b4:\n"
        "pop {r4}\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002c32f8, 76)
extern "C" __attribute__((naked)) void camp_func_002c32f8() {
    asm volatile(
        "push {r4, r5, r6}\n"
        "ldr r6, [sp, #0xc]\n"
        "ldr r5, [sp, #0x14]\n"
        "ldr ip, [sp, #0x1c]\n"
        "ldr r4, [sp, #0x24]\n"
        "vldr s0, [sp, #0x10]\n"
        "vldr s1, [sp, #0x18]\n"
        "vldr s2, [sp, #0x20]\n"
        "strh r2, [r0]\n"
        "strh r6, [r0, #2]\n"
        "strh r5, [r0, #4]\n"
        "strh ip, [r0, #6]\n"
        "strh r4, [r0, #8]\n"
        "str r1, [r0, #0xc]!\n"
        "str r3, [r0, #4]!\n"
        "add r0, r0, #4\n"
        "vstmia r0, {s0, s1, s2}\n"
        "pop {r4, r5, r6}\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00377ba4, 76)
extern "C" __attribute__((naked)) void func_00377ba4() {
    asm volatile(
        "add r0, r0, #0x2800\n"
        "add r0, r0, #0x17c\n"
        "ldr r0, [r0]\n"
        "mov r0, r0\n"
        "ldr r1, [r0]\n"
        "cmp r1, #0\n"
        "beq .L_func_00377ba4_00377bec\n"
        "add r1, r1, #0x2800\n"
        "add r1, r1, #0x17c\n"
        "mov r2, #0\n"
        "ldr r3, [r1]\n"
        "cmp r3, r0\n"
        "bne .L_func_00377ba4_00377be8\n"
        "str r2, [r1]\n"
        "ldr r1, [r0]\n"
        "cmp r1, #0\n"
        "beq .L_func_00377ba4_00377bec\n"
        ".L_func_00377ba4_00377be8:\n"
        "str r2, [r0]\n"
        ".L_func_00377ba4_00377bec:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00378f44, 76)
extern "C" __attribute__((naked)) void func_00378f44() {
    asm volatile(
        "ldrb r1, [r0, #0x5e]\n"
        "cmp r1, #0\n"
        "beq .L_func_00378f44_00378f8c\n"
        "mov r2, #0\n"
        "strb r2, [r0, #0x5e]\n"
        "str r2, [r0, #0xc]\n"
        "str r2, [r0, #0x10]\n"
        "str r2, [r0, #0x14]\n"
        "str r2, [r0, #0x18]\n"
        "ldrb r1, [r0, #0x5d]\n"
        "cmp r1, #0\n"
        "movne r3, #0\n"
        "beq .L_func_00378f44_00378f8c\n"
        ".L_func_00378f44_00378f78:\n"
        "add ip, r0, r3, lsl #2\n"
        "subs r1, r1, #1\n"
        "add r3, r3, #1\n"
        "str r2, [ip, #0x24]\n"
        "bne .L_func_00378f44_00378f78\n"
        ".L_func_00378f44_00378f8c:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0037bb14, 76)
extern "C" __attribute__((naked)) void func_0037bb14() {
    asm volatile(
        "mov ip, r0\n"
        "str r4, [sp, #-4]!\n"
        "ldr r1, [ip, #4]\n"
        "mov r3, #0x80\n"
        "mov r0, #0\n"
        ".L_func_0037bb14_0037bb28:\n"
        "add r2, ip, #4\n"
        "cmp r1, r2\n"
        "beq .L_func_0037bb14_0037bb58\n"
        "ldrb r4, [r1, #-0x54]\n"
        "ldr r2, [r1, #-0x9c]\n"
        "add r2, r2, r4\n"
        "usat r2, #7, r2\n"
        "cmp r3, r2\n"
        "subgt r0, r1, #0xec\n"
        "ldr r1, [r1]\n"
        "movgt r3, r2\n"
        "b .L_func_0037bb14_0037bb28\n"
        ".L_func_0037bb14_0037bb58:\n"
        "pop {r4}\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003b0170, 76)
extern "C" __attribute__((naked)) void func_003b0170() {
    asm volatile(
        "ldr r2, [r1, #0x1c]\n"
        "str r2, [r0, #0x1c]\n"
        "ldr r2, [r1, #0x20]\n"
        "str r2, [r0, #0x20]\n"
        "ldr r2, [r1, #0x24]\n"
        "str r2, [r0, #0x24]\n"
        "ldr r2, [r1, #0x28]\n"
        "str r2, [r0, #0x28]\n"
        "ldr r2, [r1, #0x2c]\n"
        "str r2, [r0, #0x2c]\n"
        "ldr r2, [r1, #0x30]\n"
        "str r2, [r0, #0x30]\n"
        "ldr r2, [r1, #0x18]\n"
        "str r2, [r0, #0x18]\n"
        "ldr r2, [r1, #4]\n"
        "str r2, [r0, #4]\n"
        "ldr r1, [r1, #8]\n"
        "str r1, [r0, #8]\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00128574, 80)
extern "C" __attribute__((naked)) void func_00128574() {
    asm volatile(
        "add r0, r0, #0xc\n"
        "mov r0, r0\n"
        "ldrb r3, [r0, #0xc]\n"
        "cmp r2, #0x91\n"
        "movgt r2, #0x91\n"
        "cmp r3, #0\n"
        "beq .L_func_00128574_001285b0\n"
        "cmp r3, #1\n"
        "strhne r2, [r0, #0xa]\n"
        "bne .L_func_00128574_001285ac\n"
        "cmp r1, #0x24\n"
        "movlt r1, #0x24\n"
        "strh r1, [r0, #2]\n"
        "strh r2, [r0, #8]\n"
        ".L_func_00128574_001285ac:\n"
        "bx lr\n"
        ".L_func_00128574_001285b0:\n"
        "cmp r1, #0x28\n"
        "movlt r1, #0x28\n"
        "strh r1, [r0]\n"
        "strh r2, [r0, #6]\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0015a3a4, 80)
extern "C" __attribute__((naked)) void func_0015a3a4() {
    asm volatile(
        "ldr r2, [r1]\n"
        "str r2, [r0, #0xc]\n"
        "ldr r2, [r1, #4]\n"
        "str r2, [r0, #0x10]\n"
        "ldrh r1, [r1, #8]\n"
        "strh r1, [r0, #0x14]\n"
        "ldr r2, [r0, #0x68]\n"
        "add r1, r0, #0xc\n"
        "mov r0, r2\n"
        "mov r0, r0\n"
        "ldr r2, [r1]\n"
        "str r2, [r0, #0x14]\n"
        "ldr r2, [r1, #4]\n"
        "str r2, [r0, #0x18]\n"
        "ldrh r1, [r1, #8]\n"
        "strh r1, [r0, #0x1c]\n"
        "ldrh r1, [r0, #0x6c]\n"
        "orr r1, r1, #0x10\n"
        "strh r1, [r0, #0x6c]\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00238d84, 80)
extern "C" __attribute__((naked)) void func_00238d84() {
    asm volatile(
        "str r4, [sp, #-4]!\n"
        "ldr r2, [r0]\n"
        "mov ip, #1\n"
        ".L_func_00238d84_00238d90:\n"
        "add r3, r2, #8\n"
        "ldr r2, [r2, #0xc]\n"
        "b .L_func_00238d84_00238dc4\n"
        ".L_func_00238d84_00238d9c:\n"
        "ldrb r4, [r2, #0xc]\n"
        "cmp r4, #4\n"
        "bne .L_func_00238d84_00238dc0\n"
        "ldrb r4, [r2, #0xe]\n"
        "tst r1, ip, lsl r4\n"
        "beq .L_func_00238d84_00238dc0\n"
        "ldr r2, [r2, #8]\n"
        "str r2, [r0]\n"
        "b .L_func_00238d84_00238d90\n"
        ".L_func_00238d84_00238dc0:\n"
        "ldr r2, [r2, #4]\n"
        ".L_func_00238d84_00238dc4:\n"
        "cmp r2, r3\n"
        "bne .L_func_00238d84_00238d9c\n"
        "pop {r4}\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002a22a8, 80)
extern "C" __attribute__((naked)) void func_002a22a8() {
    asm volatile(
        "ldr r2, [r0, #0xc]\n"
        "ldr r3, [r0, #8]\n"
        "vldr s1, [r0, #4]\n"
        "cmp r2, r3\n"
        "bge .L_func_002a22a8_002a22e0\n"
        "vmov s3, r2\n"
        "vldr s2, [r0]\n"
        "vmov s4, r3\n"
        "vsub.f32 s1, s1, s2\n"
        "vcvt.f32.s32 s3, s3\n"
        "vcvt.f32.s32 s4, s4\n"
        "vmul.f32 s3, s1, s3\n"
        "vdiv.f32 s1, s3, s4\n"
        "vadd.f32 s1, s1, s2\n"
        ".L_func_002a22a8_002a22e0:\n"
        "mov r2, #0\n"
        "vstr s1, [r0]\n"
        "vstr s0, [r0, #4]\n"
        "add r0, r0, #8\n"
        "stm r0, {r1, r2}\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002ad470, 80)
extern "C" __attribute__((naked)) void func_002ad470() {
    asm volatile(
        "str r4, [sp, #-4]!\n"
        "ldr r1, [r0]\n"
        "cmp r1, #1\n"
        "movne r2, #0\n"
        "mvnne r1, #0\n"
        "beq .L_func_002ad470_002ad4b4\n"
        ".L_func_002ad470_002ad488:\n"
        "ldrex r3, [r0]\n"
        "cmp r3, r2\n"
        "bne .L_func_002ad470_002ad4a4\n"
        "strex r4, r1, [r0]\n"
        "cmp r4, #0\n"
        "bne .L_func_002ad470_002ad488\n"
        "b .L_func_002ad470_002ad4a8\n"
        ".L_func_002ad470_002ad4a4:\n"
        "clrex\n"
        ".L_func_002ad470_002ad4a8:\n"
        "cmp r3, #0\n"
        "movne r0, #0\n"
        "bne .L_func_002ad470_002ad4b8\n"
        ".L_func_002ad470_002ad4b4:\n"
        "mov r0, #1\n"
        ".L_func_002ad470_002ad4b8:\n"
        "pop {r4}\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003e8a18, 80)
extern "C" __attribute__((naked)) void func_003e8a18() {
    asm volatile(
        "ldr ip, [r1, #4]\n"
        "mov r2, #1\n"
        "add r0, r1, #8\n"
        "bics ip, r2, ip\n"
        "ldrsb r2, [r3, #8]\n"
        "beq .L_func_003e8a18_003e8a44\n"
        "strb r2, [r0]\n"
        "ldr r2, [r1, #4]\n"
        "orr r2, r2, #1\n"
        "str r2, [r1, #4]\n"
        "b .L_func_003e8a18_003e8a54\n"
        ".L_func_003e8a18_003e8a44:\n"
        "ldrsb r1, [r0]\n"
        "orrs r1, r1, r2\n"
        "movne r1, #1\n"
        "strb r1, [r0]\n"
        ".L_func_003e8a18_003e8a54:\n"
        "ldrb r0, [r0]\n"
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00120e14, 84)
extern "C" __attribute__((naked)) void engine_func_00120e14() {
    asm volatile(
        "ldrb r2, [r0, #0x80]\n"
        "cmp r2, #0\n"
        "bne .L_engine_func_00120e14_00120e50\n"
        "vldr s0, [r1]\n"
        "vldr s1, [r0, #0x68]\n"
        "vsub.f32 s0, s0, s1\n"
        "vstr s0, [r0, #0x74]\n"
        "vldr s0, [r1, #4]\n"
        "vldr s1, [r0, #0x6c]\n"
        "vsub.f32 s0, s0, s1\n"
        "vstr s0, [r0, #0x78]\n"
        "vldr s0, [r1, #8]\n"
        "vldr s1, [r0, #0x70]\n"
        "vsub.f32 s0, s0, s1\n"
        "vstr s0, [r0, #0x7c]\n"
        ".L_engine_func_00120e14_00120e50:\n"
        "ldm r1, {r2, r3, ip}\n"
        "mov r1, #0\n"
        "str ip, [r0, #0x70]\n"
        "strd r2, r3, [r0, #0x68]\n"
        "strb r1, [r0, #0x80]\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0023e634, 84)
extern "C" __attribute__((naked)) void script_vm_func_0023e634() {
    asm volatile(
        "ldrh r1, [r0]\n"
        "tst r1, #0x40\n"
        "bicne r1, r1, #0x40\n"
        "strhne r1, [r0]\n"
        "uxth r1, r1\n"
        "tst r1, #0x80\n"
        "bicne r1, r1, #0x80\n"
        "strhne r1, [r0]\n"
        "uxth r1, r1\n"
        "tst r1, #0x100\n"
        "bicne r1, r1, #0x100\n"
        "strhne r1, [r0]\n"
        "uxth r1, r1\n"
        "tst r1, #0x10\n"
        "bicne r1, r1, #0x10\n"
        "strhne r1, [r0]\n"
        "uxth r1, r1\n"
        "tst r1, #8\n"
        "bicne r1, r1, #8\n"
        "strhne r1, [r0]\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00257554, 84)
extern "C" __attribute__((naked)) void func_00257554() {
    asm volatile(
        "vpush {d8, d9}\n"
        "vldmia r1, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15}\n"
        "vldmia r2, {s16, s17, s18}\n"
        "vmla.f32 s3, s0, s16\n"
        "vmla.f32 s7, s4, s16\n"
        "vmla.f32 s11, s8, s16\n"
        "vmla.f32 s15, s12, s16\n"
        "vmla.f32 s3, s1, s17\n"
        "vmla.f32 s7, s5, s17\n"
        "vmla.f32 s11, s9, s17\n"
        "vmla.f32 s15, s13, s17\n"
        "vmla.f32 s3, s2, s18\n"
        "vmla.f32 s7, s6, s18\n"
        "vmla.f32 s11, s10, s18\n"
        "vmla.f32 s15, s14, s18\n"
        "vpop {d8, d9}\n"
        "vstr s3, [r0]\n"
        "vstr s7, [r0, #4]\n"
        "vstr s11, [r0, #8]\n"
        "vstr s15, [r0, #0xc]\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002575a8, 84)
extern "C" void func_002575a8(const u32* source, u32 mask, u32* destination) {
    if (mask & 1) destination[0] = source[0x1c / 4];
    if (mask & 2) destination[0] = source[0x2c / 4];
    if (mask & 4) destination[0] = source[0x28 / 4];
    if (mask & 8) destination[0] = source[0x20 / 4];
    if (mask & 0x20) destination[0] = source[0x34 / 4];
    if (mask & 0x80) destination[0] = source[0x38 / 4];
    destination[1] = source[2];
}

// DECOMP_FUNC(0x002a1a3c, 84)
extern "C" __attribute__((naked)) void func_002a1a3c() {
    asm volatile(
        "vldmia r1!, {s0, s1, s2, s3, s4, s5, s6, s7}\n"
        "vstr s0, [r0, #0xc]\n"
        "vstr s1, [r0, #8]\n"
        "vstr s2, [r0, #4]\n"
        "vstr s3, [r0]\n"
        "vstr s4, [r0, #0x1c]\n"
        "vstr s5, [r0, #0x18]\n"
        "vstr s6, [r0, #0x14]\n"
        "vstr s7, [r0, #0x10]\n"
        "bx lr\n"
        "vldmia r1!, {s0, s1, s2, s3, s4, s5, s6, s7}\n"
        "str r2, [r0, #4]\n"
        "vstr s0, [r0, #0x10]\n"
        "vstr s1, [r0, #0xc]\n"
        "vstr s2, [r0, #8]\n"
        "vstr s3, [r0]\n"
        "vstr s4, [r0, #0x20]\n"
        "vstr s5, [r0, #0x1c]\n"
        "vstr s6, [r0, #0x18]\n"
        "vstr s7, [r0, #0x14]\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002b63bc, 84)
extern "C" __attribute__((naked)) void engine_func_002b63bc() {
    asm volatile(
        "mov r1, #0\n"
        "strb r1, [r0]\n"
        "strb r1, [r0, #1]\n"
        "strb r1, [r0, #2]\n"
        "mov r2, #0xf\n"
        "strb r1, [r0, #3]\n"
        "strb r2, [r0, #4]\n"
        "strb r2, [r0, #5]\n"
        "strb r2, [r0, #6]\n"
        "strb r1, [r0, #7]\n"
        "strb r1, [r0, #8]\n"
        "strb r1, [r0, #9]\n"
        "strb r1, [r0, #0xa]\n"
        "strb r1, [r0, #0xb]\n"
        "strb r1, [r0, #0xc]\n"
        "strb r2, [r0, #0xd]\n"
        "strb r2, [r0, #0xe]\n"
        "strb r2, [r0, #0xf]\n"
        "strb r1, [r0, #0x10]\n"
        "strb r1, [r0, #0x11]\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002c4b30, 84)
extern "C" __attribute__((naked)) void engine_func_002c4b30() {
    asm volatile(
        "mov r2, #0\n"
        "stmdb sp!, {lr}\n"
        "mov r3, r2\n"
        "mov ip, r2\n"
        "mov lr, r2\n"
        "subs r1, r1, #0x20\n"
        ".L_engine_func_002c4b30_002c4b48:\n"
        "stmhs r0!, {r2, r3, ip, lr}\n"
        "stmhs r0!, {r2, r3, ip, lr}\n"
        "subshs r1, r1, #0x20\n"
        "bhs .L_engine_func_002c4b30_002c4b48\n"
        "lsls r1, r1, #0x1c\n"
        "stmhs r0!, {r2, r3, ip, lr}\n"
        "stmmi r0!, {r2, r3}\n"
        "ldm sp!, {lr}\n"
        "lsls r1, r1, #2\n"
        "strhs r2, [r0], #4\n"
        "bxeq lr\n"
        "strhmi r2, [r0], #2\n"
        "tst r1, #0x40000000\n"
        "strbne r2, [r0], #1\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003e0e28, 84)
extern "C" __attribute__((naked)) void func_003e0e28() {
    asm volatile(
        "ldr r0, [r0, #8]\n"
        "ldrh r1, [r0]\n"
        "cmp r1, #0\n"
        "ldrheq r2, [r0, #-2]\n"
        "cmpeq r2, #0x2f\n"
        "beq .L_func_003e0e28_003e0e74\n"
        "cmp r1, #0x2e\n"
        "ldrheq r2, [r0, #2]\n"
        "cmpeq r2, #0\n"
        "beq .L_func_003e0e28_003e0e74\n"
        "cmp r1, #0x2e\n"
        "ldrheq r1, [r0, #2]\n"
        "cmpeq r1, #0x2e\n"
        "bne .L_func_003e0e28_003e0e6c\n"
        "ldrh r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "beq .L_func_003e0e28_003e0e74\n"
        ".L_func_003e0e28_003e0e6c:\n"
        "mov r0, #0\n"
        "bx lr\n"
        ".L_func_003e0e28_003e0e74:\n"
        "mov r0, #1\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00140854, 88)
extern "C" __attribute__((naked)) void func_00140854() {
    asm volatile(
        "mov r2, #0\n"
        "str r2, [r0, #4]\n"
        "strh r2, [r0, #8]\n"
        "str r2, [r0, #0xc]\n"
        "strh r2, [r0, #0x10]\n"
        "str r2, [r0, #0x14]\n"
        "add r1, r0, #0x18\n"
        "mvn ip, #0\n"
        "stm r1, {r2, ip}\n"
        "str r2, [r0, #0x2c]\n"
        "str r2, [r0, #0x30]\n"
        "str r2, [r0, #0xb8]\n"
        "strh r2, [r0, #0xbc]\n"
        "str r2, [r0, #0xc0]\n"
        "strh r2, [r0, #0xc4]\n"
        "str r2, [r0, #0xc8]\n"
        "add r3, r0, #0xcc\n"
        "stm r3, {r2, ip}\n"
        "str r2, [r0, #0xe0]\n"
        "str r2, [r0, #0xe4]\n"
        "strb r2, [r0, #0x18d]\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x001aa094, 88)
extern "C" __attribute__((naked)) void func_001aa094() {
    asm volatile(
        "str r4, [sp, #-4]!\n"
        "ldr r1, [r0, #0x18]\n"
        "add ip, r0, #0x20\n"
        "mov r2, #1\n"
        "add r1, r1, #1\n"
        "str r1, [r0, #0x18]\n"
        "ldr r4, [r0, #0xbc]\n"
        "ldr r3, [r0, #0x1c]\n"
        "ldr r1, [r4, r1, lsl #2]\n"
        "strb r2, [r3, ip]\n"
        "ldr r2, [r0, #0x1c]\n"
        "add r2, r0, r2, lsl #2\n"
        "str r1, [r2, #0x3c]\n"
        "ldr r1, [r0, #0x1c]\n"
        "add r1, r1, #1\n"
        "str r1, [r0, #0x1c]\n"
        "ldr r1, [r0, #0x18]\n"
        "add r1, r1, #1\n"
        "str r1, [r0, #0x18]\n"
        "pop {r4}\n"
        "mov r0, #1\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x001aa0ec, 88)
extern "C" __attribute__((naked)) void func_001aa0ec() {
    asm volatile(
        "str r4, [sp, #-4]!\n"
        "ldr r1, [r0, #0x18]\n"
        "add ip, r0, #0x20\n"
        "mov r2, #0\n"
        "add r1, r1, #1\n"
        "str r1, [r0, #0x18]\n"
        "ldr r4, [r0, #0xbc]\n"
        "ldr r3, [r0, #0x1c]\n"
        "ldr r1, [r4, r1, lsl #2]\n"
        "strb r2, [r3, ip]\n"
        "ldr r2, [r0, #0x1c]\n"
        "add r2, r0, r2, lsl #2\n"
        "str r1, [r2, #0x3c]\n"
        "ldr r1, [r0, #0x1c]\n"
        "add r1, r1, #1\n"
        "str r1, [r0, #0x1c]\n"
        "ldr r1, [r0, #0x18]\n"
        "add r1, r1, #1\n"
        "str r1, [r0, #0x18]\n"
        "pop {r4}\n"
        "mov r0, #1\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x001c1d2c, 88)
extern "C" __attribute__((naked)) void func_001c1d2c() {
    asm volatile(
        "add r1, r0, #0x18\n"
        "push {r4, r5}\n"
        "ldm r1, {r1, r3}\n"
        "mov r5, #2\n"
        "ldr r4, [r0, #0xbc]\n"
        "add ip, r0, #0x20\n"
        "add r1, r5, r1, lsl #2\n"
        "mov r2, #0\n"
        "ldrh r1, [r4, r1]\n"
        "strb r2, [r3, ip]\n"
        "ldr r2, [r0, #0x1c]\n"
        "add r2, r0, r2, lsl #2\n"
        "str r1, [r2, #0x3c]\n"
        "ldr r1, [r0, #0x1c]\n"
        "add r1, r1, #1\n"
        "str r1, [r0, #0x1c]\n"
        "ldr r1, [r0, #0x18]\n"
        "add r1, r1, #1\n"
        "str r1, [r0, #0x18]\n"
        "pop {r4, r5}\n"
        "mov r0, #1\n"
        "bx lr\n"
    );
}
