#include "types.h"

// DECOMP_FUNC(0x003ac9b4, 36)
extern "C" __attribute__((naked)) void func_003ac9b4() {
    asm volatile(
        "mov r2, r0\n"
        "ldrb r0, [r0, #0xc]\n"
        "ldrb r3, [r1, #0xc]\n"
        "subs r0, r0, r3\n"
        "bne .L_func_003ac9b4_003ac9d4\n"
        "ldrh r0, [r2]\n"
        "ldrh r1, [r1]\n"
        "sub r0, r0, r1\n"
        ".L_func_003ac9b4_003ac9d4:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003accd0, 36)
extern "C" __attribute__((naked)) void func_003accd0() {
    asm volatile(
        "mov r2, r0\n"
        "ldrb r0, [r1, #0xc]\n"
        "ldrb r3, [r2, #0xc]\n"
        "subs r0, r0, r3\n"
        "bne .L_func_003accd0_003accf0\n"
        "ldrh r0, [r1]\n"
        "ldrh r1, [r2]\n"
        "sub r0, r0, r1\n"
        ".L_func_003accd0_003accf0:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003acd98, 36)
extern "C" __attribute__((naked)) void func_003acd98() {
    asm volatile(
        "mov r2, r0\n"
        "ldrh r0, [r0, #0xe]\n"
        "ldrh r3, [r1, #0xe]\n"
        "subs r0, r0, r3\n"
        "bne .L_func_003acd98_003acdb8\n"
        "ldrh r0, [r2]\n"
        "ldrh r1, [r1]\n"
        "sub r0, r0, r1\n"
        ".L_func_003acd98_003acdb8:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003ad230, 36)
extern "C" __attribute__((naked)) void func_003ad230() {
    asm volatile(
        "mov r2, r0\n"
        "ldrh r0, [r1, #0xe]\n"
        "ldrh r3, [r2, #0xe]\n"
        "subs r0, r0, r3\n"
        "bne .L_func_003ad230_003ad250\n"
        "ldrh r0, [r1]\n"
        "ldrh r1, [r2]\n"
        "sub r0, r0, r1\n"
        ".L_func_003ad230_003ad250:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003be874, 36)
extern "C" __attribute__((naked)) void func_003be874() {
    asm volatile(
        "cmp r0, #0x13\n"
        "cmpne r0, #0x14\n"
        "moveq r0, #0x3e0\n"
        "beq .L_func_003be874_003be894\n"
        "cmp r0, #0x16\n"
        "movne r1, #1\n"
        "lslne r0, r1, r0\n"
        "moveq r0, #0x3e8\n"
        ".L_func_003be874_003be894:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003bf7ac, 36)
extern "C" __attribute__((naked)) void func_003bf7ac() {
    asm volatile(
        "vmov r1, s0\n"
        "cmp r1, #0x3f800000\n"
        "bge .L_func_003bf7ac_003bf7cc\n"
        "vmov s1, r0\n"
        "vcvt.f32.s32 s1, s1\n"
        "vmul.f32 s0, s1, s0\n"
        "vcvt.s32.f32 s0, s0\n"
        "vmov r0, s0\n"
        ".L_func_003bf7ac_003bf7cc:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003eae10, 36)
extern "C" __attribute__((naked)) void func_003eae10() {
    asm volatile(
        "ldr r3, [r0, #0x20c]\n"
        "cmp r3, #0\n"
        "moveq r0, #0\n"
        "beq .L_func_003eae10_003eae30\n"
        "mov r0, #4\n"
        "add r1, r0, r1, lsl #2\n"
        "ldr r0, [r3, r1]\n"
        "str r2, [r3, r1]\n"
        ".L_func_003eae10_003eae30:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x001521b0, 40)
extern "C" __attribute__((naked)) void engine_func_001521b0() {
    asm volatile(
        "ldrb r2, [r0, #0xc]\n"
        "cmp r2, #0\n"
        "moveq r0, #0\n"
        "beq .L_engine_func_001521b0_001521d4\n"
        "ldr r0, [r0, #4]\n"
        "add r1, r1, r1, lsl #1\n"
        "mov r2, #0xc\n"
        "add r1, r2, r1, lsl #2\n"
        "ldr r0, [r0, r1]\n"
        ".L_engine_func_001521b0_001521d4:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00155720, 40)
extern "C" __attribute__((naked)) void engine_func_00155720() {
    asm volatile(
        "ldrh r1, [r0, #0x14]\n"
        "cmp r1, #0x6800\n"
        "addeq r0, r0, #0x14\n"
        "beq .L_engine_func_00155720_00155740\n"
        "ldrh r1, [r0, #0x20]\n"
        "cmp r1, #0x6800\n"
        "addeq r0, r0, #0x20\n"
        "movne r0, #0\n"
        ".L_engine_func_00155720_00155740:\n"
        "ldr r0, [r0, #4]\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0015582c, 40)
extern "C" __attribute__((naked)) void func_0015582c() {
    asm volatile(
        "ldrh r1, [r0]\n"
        "cmp r1, #0\n"
        "beq .L_func_0015582c_0015584c\n"
        "sub r1, r1, #0x2000\n"
        "subs r1, r1, #0x20c\n"
        "ldreq r1, [r0, #4]\n"
        "addeq r0, r0, r1\n"
        "beq .L_func_0015582c_00155850\n"
        ".L_func_0015582c_0015584c:\n"
        "mov r0, #0\n"
        ".L_func_0015582c_00155850:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0015f77c, 40)
extern "C" __attribute__((naked)) void func_0015f77c() {
    asm volatile(
        "subs r3, r2, #0x20\n"
        "bpl .L_func_0015f77c_0015f798\n"
        "rsb r3, r2, #0x20\n"
        "lsr r0, r0, r2\n"
        "orr r0, r0, r1, lsl r3\n"
        "lsr r1, r1, r2\n"
        "bx lr\n"
        ".L_func_0015f77c_0015f798:\n"
        "lsr r0, r1, r3\n"
        "mov r1, #0\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0023a4e4, 40)
extern "C" __attribute__((naked)) void func_0023a4e4() {
    asm volatile(
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        "beq .L_func_0023a4e4_0023a508\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1400\n"
        "add r0, r0, #0x14\n"
        "ldr r0, [r0, #0x18]\n"
        "str r0, [r1]\n"
        "mov r0, #0\n"
        ".L_func_0023a4e4_0023a508:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0024ddb0, 40)
extern "C" __attribute__((naked)) void camp_func_0024ddb0() {
    asm volatile(
        "subs r3, r2, #0x20\n"
        "bpl .L_camp_func_0024ddb0_0024ddcc\n"
        "rsb r3, r2, #0x20\n"
        "lsl r1, r1, r2\n"
        "orr r1, r1, r0, lsr r3\n"
        "lsl r0, r0, r2\n"
        "bx lr\n"
        ".L_camp_func_0024ddb0_0024ddcc:\n"
        "lsl r1, r0, r3\n"
        "mov r0, #0\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002bd114, 40)
extern "C" u32 func_002bd114(u8* dst, volatile u32* count, u16 value, u32 flag) {
    if (flag == 0) {
        const u32 index = *count;
        *reinterpret_cast<volatile u16*>(dst + index * 2) = value;
    }
    *count = *count + 1;
    return 1;
}

// DECOMP_FUNC(0x002cffac, 40)
extern "C" __attribute__((naked)) void func_002cffac() {
    asm volatile(
        "add r0, r0, #0x3000\n"
        "ldr r0, [r0, #0x48]\n"
        "cmp r0, #3\n"
        "cmpne r0, #4\n"
        "beq .L_func_002cffac_002cffcc\n"
        "cmp r0, #5\n"
        "movne r0, #0\n"
        "bne .L_func_002cffac_002cffd0\n"
        ".L_func_002cffac_002cffcc:\n"
        "mov r0, #1\n"
        ".L_func_002cffac_002cffd0:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0034c9b8, 40)
extern "C" __attribute__((naked)) void func_0034c9b8() {
    asm volatile(
        "ldrb r0, [r1, #0x1f6]\n"
        "cmp r0, #0\n"
        "beq .L_func_0034c9b8_0034c9d8\n"
        "ldr r0, [r1, #0x21c]\n"
        "mov r1, #1\n"
        "bics r0, r1, r0\n"
        "moveq r0, #1\n"
        "beq .L_func_0034c9b8_0034c9dc\n"
        ".L_func_0034c9b8_0034c9d8:\n"
        "mov r0, #0\n"
        ".L_func_0034c9b8_0034c9dc:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0035a63c, 40)
extern "C" __attribute__((naked)) void func_0035a63c() {
    asm volatile(
        "cmp r0, #0xa\n"
        "beq .L_func_0035a63c_0035a65c\n"
        "cmp r0, #0xd\n"
        "movne r0, #0\n"
        "bne .L_func_0035a63c_0035a660\n"
        "cmp r1, #0xa\n"
        "moveq r0, #2\n"
        "beq .L_func_0035a63c_0035a660\n"
        ".L_func_0035a63c_0035a65c:\n"
        "mov r0, #1\n"
        ".L_func_0035a63c_0035a660:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003f5de0, 40)
extern "C" __attribute__((naked)) void func_003f5de0() {
    asm volatile(
        "ldr r0, [r0, #4]\n"
        "mov r0, r0\n"
        "cmp r0, #0\n"
        "beq .L_func_003f5de0_003f5e04\n"
        "ldr r3, [r0, #4]\n"
        "str r3, [r1]\n"
        "ldr r0, [r0, #0xc]\n"
        "str r0, [r2]\n"
        "mov r0, #1\n"
        ".L_func_003f5de0_003f5e04:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003f62f0, 40)
extern "C" __attribute__((naked)) void func_003f62f0() {
    asm volatile(
        "ldr r0, [r0, #4]\n"
        "mov r0, r0\n"
        "cmp r0, #0\n"
        "beq .L_func_003f62f0_003f6314\n"
        "ldr r3, [r0, #0x10]\n"
        "str r3, [r1]\n"
        "ldr r0, [r0, #0x18]\n"
        "str r0, [r2]\n"
        "mov r0, #1\n"
        ".L_func_003f62f0_003f6314:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0014bfb0, 44)
extern "C" __attribute__((naked)) void func_0014bfb0() {
    asm volatile(
        "add r2, r2, r1\n"
        "add r1, r1, #0x1f\n"
        "bic r1, r1, #0x1f\n"
        "cmp r1, r2\n"
        "movhi r0, #0\n"
        "bhi .L_func_0014bfb0_0014bfd8\n"
        "add r3, r0, #0xc\n"
        "stm r3, {r1, r2}\n"
        "str r1, [r0, #0x14]\n"
        "mov r0, #1\n"
        ".L_func_0014bfb0_0014bfd8:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00153134, 44)
extern "C" __attribute__((naked)) void script_vm_func_00153134() {
    asm volatile(
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "beq .L_script_vm_func_00153134_00153158\n"
        ".L_script_vm_func_00153134_00153140:\n"
        "ldr r2, [r0, #8]\n"
        "cmp r2, r1\n"
        "beq .L_script_vm_func_00153134_0015315c\n"
        "ldr r0, [r0, #0x18]\n"
        "cmp r0, #0\n"
        "bne .L_script_vm_func_00153134_00153140\n"
        ".L_script_vm_func_00153134_00153158:\n"
        "mov r0, #0\n"
        ".L_script_vm_func_00153134_0015315c:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x001556f4, 44)
extern "C" __attribute__((naked)) void engine_func_001556f4() {
    asm volatile(
        "ldrh r1, [r0, #0x14]\n"
        "cmp r1, #0x6800\n"
        "addeq r1, r0, #0x14\n"
        "beq .L_engine_func_001556f4_00155714\n"
        "ldrh r1, [r0, #0x20]\n"
        "cmp r1, #0x6800\n"
        "addeq r1, r0, #0x20\n"
        "movne r1, #0\n"
        ".L_engine_func_001556f4_00155714:\n"
        "ldr r1, [r1, #4]\n"
        "add r0, r0, r1\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x001557dc, 44)
extern "C" __attribute__((naked)) void func_001557dc() {
    asm volatile(
        "ldrh r1, [r0]\n"
        "cmp r1, #0\n"
        "subne r1, r1, #0x2000\n"
        "subsne r1, r1, #0x20c\n"
        "beq .L_func_001557dc_00155800\n"
        "cmp r1, #1\n"
        "ldreq r1, [r0, #4]\n"
        "addeq r0, r0, r1\n"
        "beq .L_func_001557dc_00155804\n"
        ".L_func_001557dc_00155800:\n"
        "mov r0, #0\n"
        ".L_func_001557dc_00155804:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002cf074, 44)
extern "C" __attribute__((naked)) void func_002cf074() {
    asm volatile(
        "ldr r0, [r0, #0x28]\n"
        "lsl r0, r0, #0x17\n"
        "lsrs r0, r0, #0x1c\n"
        "cmpne r0, #1\n"
        "beq .L_func_002cf074_002cf098\n"
        "cmp r0, #5\n"
        "cmpne r0, #6\n"
        "movne r0, #0\n"
        "bne .L_func_002cf074_002cf09c\n"
        ".L_func_002cf074_002cf098:\n"
        "mov r0, #1\n"
        ".L_func_002cf074_002cf09c:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002de8d0, 44)
extern "C" __attribute__((naked)) void engine_func_002de8d0() {
    asm volatile(
        "ldr r0, [r0, #0x8c]\n"
        "cmp r0, #0\n"
        "beq .L_engine_func_002de8d0_002de8f4\n"
        ".L_engine_func_002de8d0_002de8dc:\n"
        "ldr r2, [r0, #0x90]\n"
        "cmp r2, r1\n"
        "beq .L_engine_func_002de8d0_002de8f8\n"
        "ldr r0, [r0, #0xac]\n"
        "cmp r0, #0\n"
        "bne .L_engine_func_002de8d0_002de8dc\n"
        ".L_engine_func_002de8d0_002de8f4:\n"
        "mov r0, #0\n"
        ".L_engine_func_002de8d0_002de8f8:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002f2578, 44)
extern "C" __attribute__((naked)) void camp_func_002f2578() {
    asm volatile(
        "add r0, r0, #0x3000\n"
        "ldr r0, [r0, #0x48]\n"
        "cmp r0, #0x22\n"
        "cmpne r0, #0x23\n"
        "beq .L_camp_func_002f2578_002f259c\n"
        "cmp r0, #0x24\n"
        "cmpne r0, #0x25\n"
        "movne r0, #1\n"
        "bne .L_camp_func_002f2578_002f25a0\n"
        ".L_camp_func_002f2578_002f259c:\n"
        "mov r0, #0\n"
        ".L_camp_func_002f2578_002f25a0:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003683bc, 44)
extern "C" __attribute__((naked)) void func_003683bc() {
    asm volatile(
        "ldr r3, [r0, #0x14]\n"
        "ldr r2, [r0, #0xa0]\n"
        "bic r3, r3, #0xc0000000\n"
        "cmp r2, r3\n"
        "beq .L_func_003683bc_003683e4\n"
        "ldr r3, [r0, #0xc]\n"
        "str r1, [r3, r2, lsl #2]\n"
        "ldr r1, [r0, #0xa0]\n"
        "add r1, r1, #1\n"
        "str r1, [r0, #0xa0]\n"
        ".L_func_003683bc_003683e4:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003bb814, 44)
extern "C" __attribute__((naked)) void engine_func_003bb814() {
    asm volatile(
        "cmp r1, #0\n"
        "beq .L_engine_func_003bb814_003bb83c\n"
        "ldr r3, [r0, #0x52c]\n"
        "add r2, r0, #0x400\n"
        "add r2, r2, #0x12c\n"
        "add r0, r0, r3, lsl #2\n"
        "str r1, [r0, #0x530]\n"
        "ldr r0, [r2]\n"
        "add r0, r0, #1\n"
        "str r0, [r2]\n"
        ".L_engine_func_003bb814_003bb83c:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003c0cdc, 44)
extern "C" __attribute__((naked)) void func_003c0cdc() {
    asm volatile(
        "ldr r1, [r0, #0x50]\n"
        "tst r1, #1\n"
        "tstne r1, #0x80\n"
        "beq .L_func_003c0cdc_003c0d00\n"
        "tst r1, #2\n"
        "bne .L_func_003c0cdc_003c0d00\n"
        "ldr r0, [r0, #0x54]\n"
        "ands r0, r0, #4\n"
        "beq .L_func_003c0cdc_003c0d04\n"
        ".L_func_003c0cdc_003c0d00:\n"
        "mov r0, #1\n"
        ".L_func_003c0cdc_003c0d04:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003db7e8, 44)
extern "C" __attribute__((naked)) void engine_func_003db7e8() {
    asm volatile(
        "mov r1, #0\n"
        "mov r2, #0x6d\n"
        "mvn r3, #0\n"
        ".L_engine_func_003db7e8_003db7f4:\n"
        "add ip, r0, r1, lsl #3\n"
        "add ip, ip, #0x1000\n"
        "subs r2, r2, #1\n"
        "str r3, [ip, #0x30]\n"
        "add r1, r1, #1\n"
        "str r3, [ip, #0x34]\n"
        "bne .L_engine_func_003db7e8_003db7f4\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003ead70, 44)
extern "C" __attribute__((naked)) void func_003ead70() {
    asm volatile(
        "ldr r2, [r1, #4]\n"
        "ldr r3, [r0, #4]\n"
        "cmp r2, r3\n"
        "bne .L_func_003ead70_003ead94\n"
        "ldr r1, [r1, #8]\n"
        "ldr r0, [r0, #8]\n"
        "cmp r1, r0\n"
        "moveq r0, #1\n"
        "beq .L_func_003ead70_003ead98\n"
        ".L_func_003ead70_003ead94:\n"
        "mov r0, #0\n"
        ".L_func_003ead70_003ead98:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00139f54, 48)
extern "C" __attribute__((naked)) void func_00139f54() {
    asm volatile(
        "push {r0, r1, r2}\n"
        "ldrd r0, r1, [sp]\n"
        "cmp r0, r1\n"
        "beq .L_func_00139f54_00139f7c\n"
        ".L_func_00139f54_00139f64:\n"
        "add r1, r0, #4\n"
        "str r1, [sp]\n"
        "str r2, [r0]\n"
        "ldrd r0, r1, [sp]\n"
        "cmp r0, r1\n"
        "bne .L_func_00139f54_00139f64\n"
        ".L_func_00139f54_00139f7c:\n"
        "add sp, sp, #0xc\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0014f3fc, 48)
extern "C" __attribute__((naked)) void ui_func_0014f3fc() {
    asm volatile(
        "mov r1, r0\n"
        "ldr r0, [r0]\n"
        "ldrb r2, [r1, #3]\n"
        "bic r0, r0, #0xff000000\n"
        "orr r0, r0, r2, lsl #24\n"
        "lsrs r0, r0, #8\n"
        "bne .L_ui_func_0014f3fc_0014f428\n"
        "ldr r0, [r1, #4]\n"
        "ldrb r1, [r1, #7]\n"
        "bic r0, r0, #0xff000000\n"
        "orr r0, r0, r1, lsl #24\n"
        ".L_ui_func_0014f3fc_0014f428:\n"
        "bx lr\n"
    );
}
