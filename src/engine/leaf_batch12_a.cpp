#include "types.h"

// DECOMP_FUNC(0x0037b370, 20)
extern "C" __attribute__((naked)) void func_0037b370() {
    asm volatile(
        "cmp r0, #0\n"
        "cmpne r0, #1\n"
        "movne r0, #3\n"
        "beq .L_func_0037b370_0037b380\n"
        ".L_func_0037b370_0037b380:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00138f44, 24)
extern "C" __attribute__((naked)) void ui_func_00138f44() {
    asm volatile(
        "mov r1, #1\n"
        ".L_ui_func_00138f44_00138f48:\n"
        "ldrex r2, [r0]\n"
        "strex r3, r1, [r0]\n"
        "cmp r3, #0\n"
        "bne .L_ui_func_00138f44_00138f48\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00235ddc, 24)
extern "C" __attribute__((naked)) void func_00235ddc() {
    asm volatile(
        "cmp r0, #0\n"
        "beq .L_func_00235ddc_00235df0\n"
        "mov r1, #0\n"
        "str r1, [r0, #0x12c]\n"
        "str r1, [r0, #0x130]\n"
        ".L_func_00235ddc_00235df0:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003bcbe0, 24)
extern "C" __attribute__((naked)) void camp_func_003bcbe0() {
    asm volatile(
        "cmp r0, #0\n"
        "ldrhne r0, [r0, #0x46]\n"
        "cmpne r0, #0\n"
        "movne r0, #1\n"
        "beq .L_camp_func_003bcbe0_003bcbf4\n"
        ".L_camp_func_003bcbe0_003bcbf4:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003c9328, 28)
extern "C" __attribute__((naked)) void camp_func_003c9328() {
    asm volatile(
        "cmp r2, #0\n"
        "strb r1, [r0, #0x132]\n"
        "beq .L_camp_func_003c9328_003c9340\n"
        "ldrh r1, [r2]\n"
        "add r0, r0, #0x100\n"
        "strh r1, [r0, #0x34]\n"
        ".L_camp_func_003c9328_003c9340:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00234a1c, 32)
extern "C" __attribute__((naked)) void func_00234a1c() {
    asm volatile(
        "ldrb r1, [r0, #0x45]\n"
        "cmp r1, #0\n"
        "moveq r0, #0\n"
        "beq .L_func_00234a1c_00234a38\n"
        "ldr r0, [r0, #0x48]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        ".L_func_00234a1c_00234a38:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00235dbc, 32)
extern "C" __attribute__((naked)) void func_00235dbc() {
    asm volatile(
        "ldrsb r2, [r0, #0x17]\n"
        "cmp r2, r1\n"
        "beq .L_func_00235dbc_00235dd8\n"
        "ldrh r2, [r0, #0x20]\n"
        "strb r1, [r0, #0x17]\n"
        "orr r1, r2, #2\n"
        "strh r1, [r0, #0x20]\n"
        ".L_func_00235dbc_00235dd8:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0024c5ec, 32)
extern "C" __attribute__((naked)) void engine_func_0024c5ec() {
    asm volatile(
        "ldr r2, [r0, #0x28]\n"
        "mov r1, r0\n"
        "ldr r0, [r0, #0x20]\n"
        "cmp r2, #0\n"
        "bne .L_engine_func_0024c5ec_0024c608\n"
        "cmp r0, #0\n"
        "addne r0, r0, r1\n"
        ".L_engine_func_0024c5ec_0024c608:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0024c60c, 32)
extern "C" __attribute__((naked)) void engine_func_0024c60c() {
    asm volatile(
        "ldr r2, [r0, #0x18]\n"
        "mov r1, r0\n"
        "ldr r0, [r0, #0x10]\n"
        "cmp r2, #0\n"
        "bne .L_engine_func_0024c60c_0024c628\n"
        "cmp r0, #0\n"
        "addne r0, r0, r1\n"
        ".L_engine_func_0024c60c_0024c628:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00295760, 32)
extern "C" __attribute__((naked)) void script_vm_func_00295760() {
    asm volatile(
        "cmp r0, #0\n"
        "beq .L_script_vm_func_00295760_0029577c\n"
        "ldrh r1, [r0, #0xe]\n"
        "ldrh r2, [r0, #0x10]\n"
        "strh r1, [r0, #0x2a]\n"
        "strh r2, [r0, #0x2c]\n"
        "mov r0, #1\n"
        ".L_script_vm_func_00295760_0029577c:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002ae16c, 32)
extern "C" __attribute__((naked)) void engine_func_002ae16c() {
    asm volatile(
        "cmp r0, #0\n"
        "ldrne r0, [r0, #8]\n"
        "cmpne r0, #0\n"
        "beq .L_engine_func_002ae16c_002ae188\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        ".L_engine_func_002ae16c_002ae188:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002c1a28, 32)
extern "C" __attribute__((naked)) void engine_func_002c1a28() {
    asm volatile(
        "cmp r0, #0\n"
        "mov r1, #0\n"
        "beq .L_engine_func_002c1a28_002c1a40\n"
        "ldr r0, [r0, #0x90]\n"
        "and r0, r0, #2\n"
        "lsr r1, r0, #1\n"
        ".L_engine_func_002c1a28_002c1a40:\n"
        "mov r0, r1\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0037b350, 32)
extern "C" __attribute__((naked)) void func_0037b350() {
    asm volatile(
        "ldrb r1, [r0, #8]\n"
        "cmp r1, #0\n"
        "beq .L_func_0037b350_0037b36c\n"
        "mov r1, #0\n"
        "str r1, [r0]\n"
        "str r1, [r0, #4]\n"
        "strb r1, [r0, #8]\n"
        ".L_func_0037b350_0037b36c:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0037c2d4, 32)
extern "C" __attribute__((naked)) void func_0037c2d4() {
    asm volatile(
        "ldrb r2, [r0, #0x2c]\n"
        "cmp r2, r1\n"
        "beq .L_func_0037c2d4_0037c2f0\n"
        "ldrh r2, [r0, #0x20]\n"
        "strb r1, [r0, #0x2c]\n"
        "orr r1, r2, #8\n"
        "strh r1, [r0, #0x20]\n"
        ".L_func_0037c2d4_0037c2f0:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0037c2f4, 32)
extern "C" __attribute__((naked)) void func_0037c2f4() {
    asm volatile(
        "ldrb r2, [r0, #0x2d]\n"
        "cmp r2, r1\n"
        "beq .L_func_0037c2f4_0037c310\n"
        "ldrh r2, [r0, #0x20]\n"
        "strb r1, [r0, #0x2d]\n"
        "orr r1, r2, #8\n"
        "strh r1, [r0, #0x20]\n"
        ".L_func_0037c2f4_0037c310:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003823c8, 32)
extern "C" __attribute__((naked)) void func_003823c8() {
    asm volatile(
        "ldr r1, [r0, #0xda8]\n"
        "mov r0, #5\n"
        "cmp r1, #0\n"
        "beq .L_func_003823c8_003823e4\n"
        "ldr r1, [r1, #4]\n"
        "cmp r1, #6\n"
        "moveq r0, #4\n"
        ".L_func_003823c8_003823e4:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003abfa8, 32)
extern "C" __attribute__((naked)) void func_003abfa8() {
    asm volatile(
        "ldr r1, [r0, #0x598]\n"
        "cmp r1, #0\n"
        "moveq r0, #0\n"
        "beq .L_func_003abfa8_003abfc4\n"
        "ldr r0, [r0, #0x59c]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        ".L_func_003abfa8_003abfc4:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003ad7dc, 32)
extern "C" __attribute__((naked)) void func_003ad7dc() {
    asm volatile(
        "ldr r1, [r0, #0x598]\n"
        "cmp r1, #0\n"
        "moveq r0, #0\n"
        "beq .L_func_003ad7dc_003ad7f8\n"
        "ldr r0, [r0, #0x59c]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        ".L_func_003ad7dc_003ad7f8:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003e73fc, 32)
extern "C" __attribute__((naked)) void func_003e73fc() {
    asm volatile(
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "beq .L_func_003e73fc_003e7418\n"
        "ldrb r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        ".L_func_003e73fc_003e7418:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00155808, 36)
extern "C" __attribute__((naked)) void func_00155808() {
    asm volatile(
        "ldrh r0, [r0]\n"
        "cmp r0, #0\n"
        "beq .L_func_00155808_00155824\n"
        "sub r0, r0, #0x2000\n"
        "subs r0, r0, #0x20c\n"
        "cmpne r0, #1\n"
        "beq .L_func_00155808_00155828\n"
        ".L_func_00155808_00155824:\n"
        "mov r0, #2\n"
        ".L_func_00155808_00155828:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00157348, 36)
extern "C" __attribute__((naked)) void func_00157348() {
    asm volatile(
        "vldr s1, [r0, #0x38]\n"
        "vcmp.f32 s1, s0\n"
        "vmrs apsr_nzcv, fpscr\n"
        "beq .L_func_00157348_00157368\n"
        "ldrh r1, [r0, #0x20]\n"
        "vstr s0, [r0, #0x38]\n"
        "orr r1, r1, #0x10\n"
        "strh r1, [r0, #0x20]\n"
        ".L_func_00157348_00157368:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x001573b0, 36)
extern "C" __attribute__((naked)) void func_001573b0() {
    asm volatile(
        "vldr s1, [r0, #0x34]\n"
        "vcmp.f32 s1, s0\n"
        "vmrs apsr_nzcv, fpscr\n"
        "beq .L_func_001573b0_001573d0\n"
        "ldrh r1, [r0, #0x20]\n"
        "vstr s0, [r0, #0x34]\n"
        "orr r1, r1, #8\n"
        "strh r1, [r0, #0x20]\n"
        ".L_func_001573b0_001573d0:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0015743c, 36)
extern "C" __attribute__((naked)) void func_0015743c() {
    asm volatile(
        "vldr s1, [r0, #0x30]\n"
        "vcmp.f32 s1, s0\n"
        "vmrs apsr_nzcv, fpscr\n"
        "beq .L_func_0015743c_0015745c\n"
        "ldrh r1, [r0, #0x20]\n"
        "vstr s0, [r0, #0x30]\n"
        "orr r1, r1, #8\n"
        "strh r1, [r0, #0x20]\n"
        ".L_func_0015743c_0015745c:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00157528, 36)
extern "C" __attribute__((naked)) void func_00157528() {
    asm volatile(
        "vldr s1, [r0, #0x28]\n"
        "vcmp.f32 s1, s0\n"
        "vmrs apsr_nzcv, fpscr\n"
        "beq .L_func_00157528_00157548\n"
        "ldrh r1, [r0, #0x20]\n"
        "vstr s0, [r0, #0x28]\n"
        "orr r1, r1, #4\n"
        "strh r1, [r0, #0x20]\n"
        ".L_func_00157528_00157548:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002273bc, 36)
extern "C" __attribute__((naked)) void func_002273bc() {
    asm volatile(
        "cmp r0, #0\n"
        "beq .L_func_002273bc_002273dc\n"
        "mov r1, #0\n"
        "str r1, [r0]\n"
        "str r1, [r0, #4]\n"
        "str r1, [r0, #8]\n"
        "str r1, [r0, #0xc]\n"
        "str r1, [r0, #0x10]\n"
        ".L_func_002273bc_002273dc:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00246a74, 36)
extern "C" __attribute__((naked)) void engine_func_00246a74() {
    asm volatile(
        "ldr r1, [r0, #0x8c]\n"
        "mov r0, #0\n"
        "cmp r1, #0\n"
        "beq .L_engine_func_00246a74_00246a94\n"
        ".L_engine_func_00246a74_00246a84:\n"
        "ldr r1, [r1, #0xac]\n"
        "add r0, r0, #1\n"
        "cmp r1, #0\n"
        "bne .L_engine_func_00246a74_00246a84\n"
        ".L_engine_func_00246a74_00246a94:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00299558, 36)
extern "C" __attribute__((naked)) void engine_func_00299558() {
    asm volatile(
        "ldrb r2, [r0, #0x62]\n"
        "cmp r2, #0\n"
        "bne .L_engine_func_00299558_00299578\n"
        "ldr r2, [r0, #0x48]\n"
        "cmp r2, r1\n"
        "movne r2, #1\n"
        "strbne r2, [r0, #0x61]\n"
        "str r1, [r0, #0x48]\n"
        ".L_engine_func_00299558_00299578:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0029d8c0, 36)
extern "C" __attribute__((naked)) void camp_func_0029d8c0() {
    asm volatile(
        "ldrb r2, [r0, #0x62]\n"
        "cmp r2, #0\n"
        "bne .L_camp_func_0029d8c0_0029d8e0\n"
        "ldr r2, [r0, #0x20]\n"
        "cmp r2, r1\n"
        "movne r2, #1\n"
        "strbne r2, [r0, #0x60]\n"
        "str r1, [r0, #0x20]\n"
        ".L_camp_func_0029d8c0_0029d8e0:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002f8174, 36)
extern "C" __attribute__((naked)) void func_002f8174() {
    asm volatile(
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "str r0, [r1, #8]\n"
        "beq .L_func_002f8174_002f8194\n"
        "ldr r2, [r0, #0x14]\n"
        "str r2, [r1]\n"
        "ldr r0, [r0, #0x18]\n"
        "str r0, [r1, #4]\n"
        ".L_func_002f8174_002f8194:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003505bc, 36)
extern "C" __attribute__((naked)) void func_003505bc() {
    asm volatile(
        "cmp r1, #0\n"
        "moveq r0, #0\n"
        "beq .L_func_003505bc_003505dc\n"
        "ldr r0, [r1, #8]\n"
        "cmp r0, #0\n"
        "cmpne r0, #1\n"
        "moveq r0, #2\n"
        "movne r0, #1\n"
        ".L_func_003505bc_003505dc:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003683e8, 36)
extern "C" __attribute__((naked)) void func_003683e8() {
    asm volatile(
        "ldr r2, [r0, #0xa4]\n"
        "cmp r2, #8\n"
        "beq .L_func_003683e8_00368408\n"
        "ldr r3, [r0, #0x24]\n"
        "str r1, [r3, r2, lsl #2]\n"
        "ldr r1, [r0, #0xa4]\n"
        "add r1, r1, #1\n"
        "str r1, [r0, #0xa4]\n"
        ".L_func_003683e8_00368408:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0037bf28, 36)
extern "C" __attribute__((naked)) void func_0037bf28() {
    asm volatile(
        "ldrb r1, [r0, #0xc]\n"
        "cmp r1, #0\n"
        "beq .L_func_0037bf28_0037bf48\n"
        "mov r1, #0\n"
        "str r1, [r0]\n"
        "str r1, [r0, #4]\n"
        "str r1, [r0, #8]\n"
        "strb r1, [r0, #0xc]\n"
        ".L_func_0037bf28_0037bf48:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003aaafc, 36)
extern "C" __attribute__((naked)) void func_003aaafc() {
    asm volatile(
        "mov r2, r0\n"
        "ldr r0, [r1, #8]\n"
        "ldr r3, [r2, #8]\n"
        "subs r0, r0, r3\n"
        "bne .L_func_003aaafc_003aab1c\n"
        "ldrh r0, [r2]\n"
        "ldrh r1, [r1]\n"
        "sub r0, r0, r1\n"
        ".L_func_003aaafc_003aab1c:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003aaea8, 36)
extern "C" __attribute__((naked)) void func_003aaea8() {
    asm volatile(
        "mov r2, r0\n"
        "ldr r0, [r0, #8]\n"
        "ldr r3, [r1, #8]\n"
        "subs r0, r0, r3\n"
        "bne .L_func_003aaea8_003aaec8\n"
        "ldrh r0, [r1]\n"
        "ldrh r1, [r2]\n"
        "sub r0, r0, r1\n"
        ".L_func_003aaea8_003aaec8:\n"
        "bx lr\n"
    );
}
