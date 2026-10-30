#include "types.h"

// Call targets are declared by ledger name so the ARM CALL relocations remain
// explicit and can be checked against their known code addresses.
extern "C" void AsdCamera_func_00310124();
extern "C" void AsdModel_func_002a9acc();
extern "C" void AsdProcess_func_00118488();
extern "C" void Tbb_GetPayloadData();
extern "C" void battle_func_0013aef0();
extern "C" void battle_func_0024eed4();
extern "C" void battle_func_0028df54();
extern "C" void battle_func_002ad4f0();
extern "C" void battle_func_002ae3f0();
extern "C" void battle_func_002b6e60();
extern "C" void battle_func_002bf41c();
extern "C" void battle_func_002c45b8();
extern "C" void camp_func_0022a0c4();
extern "C" void camp_func_00253fa0();
extern "C" void camp_func_002ae4c4();
extern "C" void camp_func_002b4854();
extern "C" void engine_func_00296f60();
extern "C" void engine_func_002a728c();
extern "C" void engine_func_002aad14();
extern "C" void engine_func_002b47cc();
extern "C" void engine_func_002c2b1c();
extern "C" void engine_func_002c3628();
extern "C" void engine_func_002c3a44();
extern "C" void engine_func_002f6ac0();
extern "C" void engine_func_003492d8();
extern "C" void engine_func_003513dc();
extern "C" void engine_func_00377dac();
extern "C" void func_0015a044();
extern "C" void func_0015a050();
extern "C" void func_0015eef8();
extern "C" void func_00225dac();
extern "C" void func_00235ddc();
extern "C" void func_0023d448();
extern "C" void func_00245318();
extern "C" void func_002546ec();
extern "C" void func_0028412c();
extern "C" void func_002a337c();
extern "C" void func_002a6d94();
extern "C" void func_002a7094();
extern "C" void func_002ad714();
extern "C" void func_002b5a1c();
extern "C" void func_00322cc4();
extern "C" void func_00379660();
extern "C" void func_003aff38();
extern "C" void func_003e69a8();
extern "C" void func_003f8b6c();
extern "C" void script_vm_func_002954cc();
extern "C" void script_vm_func_0029923c();
extern "C" void script_vm_func_002b66ec();
extern "C" void script_vm_func_002b6e78();
extern "C" void script_vm_func_00324db0();
extern "C" void script_vm_func_0033b2e0();
extern "C" void ui_func_00138f44();
extern "C" void ui_func_00249da4();
extern "C" void ui_func_0026f0d8();
extern "C" void ui_func_00282d98();
extern "C" void ui_func_00293c98();
extern "C" s32 ui_func_002b902c(u32 id);
extern "C" s32 ui_func_002bffbc(u32 id);
extern "C" void ui_func_002c0a6c();
extern "C" void ui_func_002c0ac8();
extern "C" void ui_func_002c0b94();
extern "C" void ui_func_002c615c();
extern "C" void ui_func_002d81d0();

// DECOMP_FUNC(0x00276550, 48)
extern "C" __attribute__((naked)) void script_vm_func_00276550() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, #0\n"
        "mov r0, #2\n"
        "bl ui_func_0026f0d8\n"
        "cmp r0, #0\n"
        "movne r4, #1\n"
        "mov r0, #1\n"
        "bl ui_func_002bffbc\n"
        "cmp r0, #0\n"
        "movne r4, #1\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0027f10c, 48)
extern "C" __attribute__((naked)) void script_vm_func_0027f10c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, #0\n"
        "mov r0, #1\n"
        "bl ui_func_0026f0d8\n"
        "cmp r0, #0\n"
        "movne r4, #1\n"
        "mov r0, #0\n"
        "bl ui_func_002bffbc\n"
        "cmp r0, #0\n"
        "movne r4, #1\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0028ec44, 48)
extern "C" __attribute__((naked)) void battle_func_0028ec44() {
    asm volatile(
        "sub r1, r0, #1\n"
        "cmp r1, #0x3b\n"
        "push {r4, lr}\n"
        "bhi .L_19c_0028ec44_0028ec6c\n"
        "bl camp_func_002b4854\n"
        "ldrb r0, [r0, #0x6d]\n"
        "cmp r0, #2\n"
        "cmpne r0, #3\n"
        "moveq r0, #1\n"
        "beq .L_19c_0028ec44_0028ec70\n"
        ".L_19c_0028ec44_0028ec6c:\n"
        "mov r0, #0\n"
        ".L_19c_0028ec44_0028ec70:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002915b4, 48)
extern "C" __attribute__((naked)) void func_002915b4() {
    asm volatile(
        "str lr, [sp, #-4]!\n"
        "sub sp, sp, #0x1c\n"
        "add ip, sp, #0x20\n"
        "add lr, sp, #0xc\n"
        "vldmia ip, {s0, s1, s2, s3, s4, s5}\n"
        "mov ip, #0\n"
        "vstmia sp, {s0, s1}\n"
        "vstmia lr, {s2, s3, s4, s5}\n"
        "str ip, [sp, #8]\n"
        "bl ui_func_002d81d0\n"
        "add sp, sp, #0x1c\n"
        "pop {pc}\n"
    );
}

// DECOMP_FUNC(0x002b6e10, 48)
extern "C" __attribute__((naked)) void battle_func_002b6e10() {
    asm volatile(
        "push {r4, lr}\n"
        "bl battle_func_002b6e60\n"
        "ldrh r1, [r0, #0x46]\n"
        "cmp r1, #0\n"
        "beq .L_19c_002b6e10_002b6e38\n"
        "add r0, r0, #0x600\n"
        "ldrh r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bne .L_19c_002b6e10_002b6e3c\n"
        ".L_19c_002b6e10_002b6e38:\n"
        "mov r0, #0\n"
        ".L_19c_002b6e10_002b6e3c:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002c5978, 48)
extern "C" __attribute__((naked)) void engine_func_002c5978() {
    asm volatile(
        "str lr, [sp, #-4]!\n"
        "sub sp, sp, #0x14\n"
        "add ip, sp, #0x18\n"
        "add lr, sp, #4\n"
        "vldmia ip, {s0, s1, s2}\n"
        "mov ip, #0\n"
        "vstmia lr, {s0, s1, s2}\n"
        "str ip, [sp, #0x10]\n"
        "str ip, [sp]\n"
        "bl AsdProcess_func_00118488\n"
        "add sp, sp, #0x14\n"
        "pop {pc}\n"
    );
}

// DECOMP_FUNC(0x002d87b0, 48)
extern "C" __attribute__((naked)) void battle_func_002d87b0() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl battle_func_002bf41c\n"
        "cmp r0, #0\n"
        "beq .L_19c_002d87b0_002d87d8\n"
        "mov r1, #0\n"
        "mov r0, r4\n"
        "bl battle_func_002c45b8\n"
        ".L_19c_002d87b0_002d87d8:\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002dcd38, 48)
extern "C" __attribute__((naked)) void engine_func_002dcd38() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r1\n"
        "ldrh r0, [r0]\n"
        "bl engine_func_002b47cc\n"
        "mov r5, r0\n"
        "ldrh r0, [r4]\n"
        "bl engine_func_002b47cc\n"
        "mov r1, r0\n"
        "ldrh r0, [r5, #0x98]\n"
        "ldrh r1, [r1, #0x98]\n"
        "sub r0, r0, r1\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x002e231c, 48)
extern "C" __attribute__((naked)) void engine_func_002e231c() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "mov r0, #1\n"
        "bl engine_func_00296f60\n"
        "mov r1, r0\n"
        "mov r2, #0\n"
        "mov r0, r4\n"
        "bl ui_func_00249da4\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002e291c, 48)
extern "C" __attribute__((naked)) void engine_func_002e291c() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r4, r0\n"
        "mov r0, #1\n"
        "bl engine_func_00296f60\n"
        "mov r1, r0\n"
        "mov r0, r4\n"
        "bl script_vm_func_0029923c\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002e4968, 48)
extern "C" __attribute__((naked)) void func_002e4968() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r1\n"
        "ldrh r0, [r0]\n"
        "bl camp_func_002ae4c4\n"
        "mov r5, r0\n"
        "ldrh r0, [r4]\n"
        "bl camp_func_002ae4c4\n"
        "mov r1, r0\n"
        "ldrb r0, [r5, #0x54]\n"
        "ldrb r1, [r1, #0x54]\n"
        "sub r0, r0, r1\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x002ee9c8, 48)
extern "C" __attribute__((naked)) void battle_func_002ee9c8() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl battle_func_002bf41c\n"
        "cmp r0, #0\n"
        "beq .L_19c_002ee9c8_002ee9f0\n"
        "mov r1, #0\n"
        "mov r0, r4\n"
        "bl battle_func_002c45b8\n"
        ".L_19c_002ee9c8_002ee9f0:\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002fe184, 48)
extern "C" __attribute__((naked)) void battle_func_002fe184() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl battle_func_002bf41c\n"
        "cmp r0, #0\n"
        "beq .L_19c_002fe184_002fe1ac\n"
        "mov r1, #0\n"
        "mov r0, r4\n"
        "bl battle_func_002c45b8\n"
        ".L_19c_002fe184_002fe1ac:\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030bb60, 48)
extern "C" __attribute__((naked)) void engine_func_0030bb60() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "mov r0, #1\n"
        "bl engine_func_00296f60\n"
        "mov r1, r0\n"
        "mov r0, r4\n"
        "bl script_vm_func_002954cc\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0031c204, 48)
extern "C" __attribute__((naked)) void func_0031c204() {
    asm volatile(
        "mov r1, #1\n"
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl battle_func_0024eed4\n"
        "mov r1, #2\n"
        "mov r0, #0\n"
        "bl battle_func_0024eed4\n"
        "mov r1, #3\n"
        "mov r0, #0\n"
        "bl battle_func_0024eed4\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0034dff8, 48)
extern "C" __attribute__((naked)) void ui_func_0034dff8() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0, #0x10]\n"
        "mov r5, #0\n"
        "str r5, [r0, #0x24]\n"
        "ldr r0, [r4, #0x10]\n"
        "bl ui_func_002c0a6c\n"
        "str r5, [r4, #0x10]\n"
        "pop {r4, r5, r6, pc}\n"
        "mov r1, #0\n"
        "str r1, [r0, #0x10]\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00377bf0, 48)
extern "C" __attribute__((naked)) void func_00377bf0() {
    asm volatile(
        "push {r4, lr}\n"
        "sub sp, sp, #0x10\n"
        "mov r4, #0\n"
        "ldr ip, [sp, #0x18]\n"
        "add lr, sp, #4\n"
        "str r4, [sp]\n"
        "stm lr, {r3, ip}\n"
        "mov r3, r4\n"
        "bl engine_func_00377dac\n"
        "add sp, sp, #0x10\n"
        "and r0, r0, #0xff\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00380500, 48)
extern "C" __attribute__((naked)) void func_00380500() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl func_00379660\n"
        "mov r0, #0\n"
        "str r0, [r4, #0x190]\n"
        "mov r1, #1\n"
        "strb r0, [r4, #0x45c]\n"
        "strb r1, [r4, #0x45d]\n"
        "strb r0, [r4, #0x45e]\n"
        "str r0, [r4, #0x450]\n"
        "str r0, [r4, #0x454]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003c2c7c, 48)
extern "C" __attribute__((naked)) void ui_func_003c2c7c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r0\n"
        "mov r0, #5\n"
        "bl ui_func_002b902c\n"
        "cmp r5, #0\n"
        "mov r4, r0\n"
        "beq .L_19c_003c2c7c_003c2ca4\n"
        "mov r0, #0xe\n"
        "bl ui_func_002b902c\n"
        "orr r4, r4, r0\n"
        ".L_19c_003c2c7c_003c2ca4:\n"
        "mov r0, r4\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x003c2cac, 48)
extern "C" __attribute__((naked)) void ui_func_003c2cac() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r0\n"
        "mov r0, #5\n"
        "bl ui_func_002bffbc\n"
        "cmp r5, #0\n"
        "mov r4, r0\n"
        "beq .L_19c_003c2cac_003c2cd4\n"
        "mov r0, #0xe\n"
        "bl ui_func_002bffbc\n"
        "orr r4, r4, r0\n"
        ".L_19c_003c2cac_003c2cd4:\n"
        "mov r0, r4\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x003c2cdc, 48)
extern "C" __attribute__((naked)) void ui_func_003c2cdc() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r0\n"
        "mov r0, #6\n"
        "bl ui_func_002b902c\n"
        "cmp r5, #0\n"
        "mov r4, r0\n"
        "beq .L_19c_003c2cdc_003c2d04\n"
        "mov r0, #0xf\n"
        "bl ui_func_002b902c\n"
        "orr r4, r4, r0\n"
        ".L_19c_003c2cdc_003c2d04:\n"
        "mov r0, r4\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x003c2d0c, 48)
extern "C" __attribute__((naked)) void ui_func_003c2d0c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r0\n"
        "mov r0, #4\n"
        "bl ui_func_002b902c\n"
        "cmp r5, #0\n"
        "mov r4, r0\n"
        "beq .L_19c_003c2d0c_003c2d34\n"
        "mov r0, #0xd\n"
        "bl ui_func_002b902c\n"
        "orr r4, r4, r0\n"
        ".L_19c_003c2d0c_003c2d34:\n"
        "mov r0, r4\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x003c2d3c, 48)
extern "C" __attribute__((naked)) void ui_func_003c2d3c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r0\n"
        "mov r0, #3\n"
        "bl ui_func_002b902c\n"
        "cmp r5, #0\n"
        "mov r4, r0\n"
        "beq .L_19c_003c2d3c_003c2d64\n"
        "mov r0, #0xc\n"
        "bl ui_func_002b902c\n"
        "orr r4, r4, r0\n"
        ".L_19c_003c2d3c_003c2d64:\n"
        "mov r0, r4\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x003c2d6c, 48)
extern "C" __attribute__((naked)) void ui_func_003c2d6c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r0\n"
        "mov r0, #6\n"
        "bl ui_func_002bffbc\n"
        "cmp r5, #0\n"
        "mov r4, r0\n"
        "beq .L_19c_003c2d6c_003c2d94\n"
        "mov r0, #0xf\n"
        "bl ui_func_002bffbc\n"
        "orr r4, r4, r0\n"
        ".L_19c_003c2d6c_003c2d94:\n"
        "mov r0, r4\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x003c8a78, 48)
extern "C" __attribute__((naked)) void script_vm_func_003c8a78() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, #0\n"
        "bl script_vm_func_002b6e78\n"
        "cmp r0, #2\n"
        "bne .L_19c_003c8a78_003c8aa0\n"
        "bl battle_func_002b6e60\n"
        "ldrh r0, [r0, #0x46]\n"
        "bl camp_func_0022a0c4\n"
        "ldrh r0, [r0, #4]\n"
        "lsr r4, r0, #1\n"
        ".L_19c_003c8a78_003c8aa0:\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003d701c, 48)
extern "C" __attribute__((naked)) void func_003d701c() {
    asm volatile(
        "vcvt.s32.f32 s2, s2\n"
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r2, #0\n"
        "vmov r0, s2\n"
        "sxth r1, r0\n"
        "add r0, r4, #0x44\n"
        "bl func_002546ec\n"
        "ldr r1, [r4, #0x634]\n"
        "orr r1, r1, #0x400000\n"
        "str r1, [r4, #0x634]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003db168, 48)
extern "C" __attribute__((naked)) void func_003db168() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "cmp r3, #0\n"
        "mov r0, r2\n"
        "uxth r1, r1\n"
        "movne r2, #1\n"
        "moveq r2, #0\n"
        "bl engine_func_002f6ac0\n"
        "add r4, r4, #0x1c00\n"
        "add r4, r4, #0xfc\n"
        "str r0, [r4]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003e70f8, 48)
extern "C" __attribute__((naked)) void func_003e70f8() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r0, [r0, #4]\n"
        "mov r4, r1\n"
        "bl func_003e69a8\n"
        "vldmia r0, {s0, s1, s2, s3, s4, s5, s6, s7}\n"
        "add r0, r0, #0x20\n"
        "vstmia r4, {s0, s1, s2, s3, s4, s5, s6, s7}\n"
        "add r4, r4, #0x20\n"
        "vldmia r0, {s0, s1, s2, s3, s4, s5}\n"
        "mov r0, #1\n"
        "vstmia r4, {s0, s1, s2, s3, s4, s5}\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003f7240, 48)
extern "C" __attribute__((naked)) void engine_func_003f7240() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr ip, [r0, #4]\n"
        "ldrb r3, [r0, #8]\n"
        "ldrb r4, [r0, #9]\n"
        "ldrsb r0, [r0, #0xa]\n"
        "sub sp, sp, #8\n"
        "str r0, [sp, #4]\n"
        "mov r0, ip\n"
        "str r4, [sp]\n"
        "bl engine_func_002c3a44\n"
        "add sp, sp, #8\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003f9150, 48)
extern "C" __attribute__((naked)) void func_003f9150() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl func_003f8b6c\n"
        "ldrb r1, [r0, #1]\n"
        "ldrb r0, [r0, #2]\n"
        "vldr s2, [r4, #8]\n"
        "add r0, r1, r0, lsl #8\n"
        "vmov s0, r0\n"
        "vcvt.f32.u32 s1, s0\n"
        "vldr s0, [r4, #0xc]\n"
        "vmla.f32 s0, s1, s2\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00129c24, 52)
extern "C" __attribute__((naked)) void battle_func_00129c24() {
    asm volatile(
        "mov r0, r0\n"
        "push {r3, r4, r5, r6, r7, lr}\n"
        "mov r5, r0\n"
        "mov r6, r1\n"
        "mov r7, r2\n"
        "mov r4, r3\n"
        "bl battle_func_002ad4f0\n"
        "mov r3, r7\n"
        "mov r2, r6\n"
        "mov r1, r5\n"
        "str r4, [sp]\n"
        "bl battle_func_0013aef0\n"
        "pop {r3, r4, r5, r6, r7, pc}\n"
    );
}

// DECOMP_FUNC(0x0012a5f8, 52)
extern "C" __attribute__((naked)) void func_0012a5f8() {
    asm volatile(
        "str lr, [sp, #-4]!\n"
        "sub sp, sp, #0x14\n"
        "mov r3, #0\n"
        "str r0, [sp, #8]\n"
        "strb r1, [sp, #0xc]\n"
        "add r1, sp, #8\n"
        "mov r0, #5\n"
        "mov r2, #8\n"
        "str r3, [sp]\n"
        "str r3, [sp, #4]\n"
        "bl func_002b5a1c\n"
        "add sp, sp, #0x14\n"
        "pop {pc}\n"
    );
}

// DECOMP_FUNC(0x00139f20, 52)
extern "C" __attribute__((naked)) void func_00139f20() {
    asm volatile(
        "push {r4, lr}\n"
        "ldrsh ip, [r1, #0xa]\n"
        "ldrsb r3, [r1, #8]\n"
        "ldrsb r4, [r1, #9]\n"
        "ldrsb r2, [r1, #7]\n"
        "sub sp, sp, #0x10\n"
        "stm sp, {r2, r3, r4, ip}\n"
        "ldrsb r3, [r1, #5]\n"
        "ldrsb r2, [r1, #4]\n"
        "ldr r1, [r1]\n"
        "bl func_002ad714\n"
        "add sp, sp, #0x10\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00139fd8, 52)
extern "C" __attribute__((naked)) void func_00139fd8() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r0\n"
        "mov r4, #0\n"
        ".L_19c_00139fd8_00139fe4:\n"
        "add r0, r5, r4, lsl #2\n"
        "add r0, r0, #0x1400\n"
        "add r0, r0, #0x1dc\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #0x68]\n"
        "bl func_0015a044\n"
        "add r4, r4, #1\n"
        "cmp r4, #0x18\n"
        "blt .L_19c_00139fd8_00139fe4\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0015209c, 52)
extern "C" __attribute__((naked)) void func_0015209c() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #1\n"
        "mov r1, sp\n"
        "add r0, r0, #0xc\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "beq .L_19c_0015209c_001520c8\n"
        "ldr r0, [sp]\n"
        "lsl r0, r0, #0x10\n"
        "lsrs r0, r0, #0x18\n"
        "beq .L_19c_0015209c_001520cc\n"
        ".L_19c_0015209c_001520c8:\n"
        "mov r0, #1\n"
        ".L_19c_0015209c_001520cc:\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x0015dd3c, 52)
extern "C" __attribute__((naked)) void func_0015dd3c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r0\n"
        "mov r4, #0\n"
        ".L_19c_0015dd3c_0015dd48:\n"
        "add r0, r5, r4, lsl #2\n"
        "add r0, r0, #0x1400\n"
        "add r0, r0, #0x1dc\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #0x68]\n"
        "bl func_0015a050\n"
        "add r4, r4, #1\n"
        "cmp r4, #0x18\n"
        "blt .L_19c_0015dd3c_0015dd48\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0015dee8, 52)
extern "C" __attribute__((naked)) void func_0015dee8() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r0\n"
        "mov r4, #0\n"
        ".L_19c_0015dee8_0015def4:\n"
        "add r0, r5, r4, lsl #2\n"
        "add r0, r0, #0x1400\n"
        "add r0, r0, #0x1dc\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #0x68]\n"
        "bl func_0015eef8\n"
        "add r4, r4, #1\n"
        "cmp r4, #0x18\n"
        "blt .L_19c_0015dee8_0015def4\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0023a518, 52)
extern "C" __attribute__((naked)) void func_0023a518() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r0, [r0, #4]\n"
        "bl func_00225dac\n"
        "cmp r0, #0\n"
        "ldrne r0, [r0, #0x10]\n"
        "cmpne r0, #0\n"
        "moveq r0, #0xe\n"
        "beq .L_19c_0023a518_0023a548\n"
        "bl func_003aff38\n"
        "cmp r0, #0\n"
        "moveq r0, #0x14\n"
        "movne r0, #0\n"
        ".L_19c_0023a518_0023a548:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002487e4, 52)
extern "C" __attribute__((naked)) void engine_func_002487e4() {
    asm volatile(
        "mov r3, r0\n"
        "mov r0, r1\n"
        "push {r4, lr}\n"
        "bl engine_func_002a728c\n"
        "cmn r0, #1\n"
        "moveq r0, #0\n"
        "beq .L_19c_002487e4_00248814\n"
        "mov r1, r0\n"
        "mov r0, r3\n"
        "bl func_002a7094\n"
        "cmp r0, #0\n"
        "ldrsbne r0, [r0, #0xd]\n"
        ".L_19c_002487e4_00248814:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00258074, 52)
extern "C" __attribute__((naked)) void script_vm_func_00258074() {
    asm volatile(
        "push {r4, lr}\n"
        "sub sp, sp, #0x28\n"
        "mov r4, r0\n"
        "bl script_vm_func_002b66ec\n"
        "mov r1, r0\n"
        "mov r0, sp\n"
        "bl camp_func_00253fa0\n"
        "mov r0, sp\n"
        "add r0, r0, r4, lsl #1\n"
        "ldrh r0, [r0]\n"
        "add sp, sp, #0x28\n"
        "lsr r0, r0, #0xa\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002a6410, 52)
extern "C" __attribute__((naked)) void engine_func_002a6410() {
    asm volatile(
        "mov r3, r0\n"
        "mov r0, r1\n"
        "push {r4, lr}\n"
        "bl engine_func_002a728c\n"
        "cmn r0, #1\n"
        "mov r1, r0\n"
        "beq .L_19c_002a6410_002a6440\n"
        "mov r0, r3\n"
        "bl func_002a7094\n"
        "cmp r0, #0\n"
        "movne r1, #0\n"
        "strbne r1, [r0, #0xd]\n"
        ".L_19c_002a6410_002a6440:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002c3188, 52)
extern "C" __attribute__((naked)) void engine_func_002c3188() {
    asm volatile(
        "str lr, [sp, #-4]!\n"
        "sub sp, sp, #0x14\n"
        "add ip, sp, #4\n"
        "mov r3, #0\n"
        "stm ip, {r1, r2, r3}\n"
        "mov r2, r3\n"
        "str r3, [sp, #0x10]\n"
        "ldr r1, [r0]\n"
        "str r1, [sp]\n"
        "mov r1, r3\n"
        "bl engine_func_002aad14\n"
        "add sp, sp, #0x14\n"
        "pop {pc}\n"
    );
}

// DECOMP_FUNC(0x002c541c, 52)
extern "C" __attribute__((naked)) void engine_func_002c541c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r0\n"
        "mov r5, r1\n"
        "add r0, r0, #4\n"
        "bl ui_func_00138f44\n"
        "cmp r5, #0\n"
        "mvnne r1, #1\n"
        "mvneq r1, #0\n"
        ".L_19c_002c541c_002c543c:\n"
        "ldrex r0, [r4]\n"
        "strex r2, r1, [r4]\n"
        "cmp r2, #0\n"
        "bne .L_19c_002c541c_002c543c\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x002e2040, 52)
extern "C" __attribute__((naked)) void engine_func_002e2040() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_00322cc4\n"
        "cmn r0, #1\n"
        "mov r4, r0\n"
        "beq .L_19c_002e2040_002e2070\n"
        "bl battle_func_002bf41c\n"
        "cmp r0, #0\n"
        "beq .L_19c_002e2040_002e2070\n"
        "mov r0, r4\n"
        "bl ui_func_002c0ac8\n"
        "mov r1, #0\n"
        "strb r1, [r0, #0x94]\n"
        ".L_19c_002e2040_002e2070:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002e3b7c, 52)
extern "C" __attribute__((naked)) void engine_func_002e3b7c() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl ui_func_00293c98\n"
        "add r0, r0, #0x1f00\n"
        "ldrsh r0, [r0, #0xc6]\n"
        "cmp r0, r4\n"
        "movle r0, #1\n"
        "movgt r0, #0\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002e42ac, 52)
extern "C" __attribute__((naked)) void engine_func_002e42ac() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl ui_func_00293c98\n"
        "add r0, r0, #0x4800\n"
        "add r0, r0, #0x1bc\n"
        "mov r1, #1\n"
        "ldr r2, [r0]\n"
        "orr r1, r2, r1, lsl r4\n"
        "str r1, [r0]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003002dc, 52)
extern "C" __attribute__((naked)) void engine_func_003002dc() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "mov r0, #1\n"
        "bl engine_func_00296f60\n"
        "mov r5, r0\n"
        "bl ui_func_00293c98\n"
        "uxth r1, r4\n"
        "mov r2, r5\n"
        "bl script_vm_func_0033b2e0\n"
        "mov r0, #1\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x00312538, 52)
extern "C" __attribute__((naked)) void engine_func_00312538() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl ui_func_00293c98\n"
        "add r0, r0, #0x1f00\n"
        "ldrsh r0, [r0, #0xca]\n"
        "cmp r0, r4\n"
        "movle r0, #1\n"
        "movgt r0, #0\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0031c34c, 52)
extern "C" __attribute__((naked)) void engine_func_0031c34c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "bl engine_func_002c2b1c\n"
        "mov r4, r0\n"
        "mov r0, #1\n"
        "bl engine_func_00296f60\n"
        "mov r5, r0\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "add r0, r4, r0, lsl #1\n"
        "add r0, r0, #0xd00\n"
        "strh r5, [r0, #0x5c]\n"
        "mov r0, #1\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x00322d3c, 52)
extern "C" __attribute__((naked)) void engine_func_00322d3c() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r4, r0\n"
        "mov r0, #1\n"
        "bl engine_func_00296f60\n"
        "cmp r0, #1\n"
        "moveq r1, #1\n"
        "movne r1, #0\n"
        "mov r0, r4\n"
        "bl engine_func_003492d8\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00325410, 52)
extern "C" __attribute__((naked)) void engine_func_00325410() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl ui_func_00293c98\n"
        "mov r1, #4\n"
        "bl func_00245318\n"
        "bl Tbb_GetPayloadData\n"
        "add r0, r0, r4, lsl #2\n"
        "ldrh r0, [r0, #2]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00325444, 52)
extern "C" __attribute__((naked)) void engine_func_00325444() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl ui_func_00293c98\n"
        "mov r1, #4\n"
        "bl func_00245318\n"
        "bl Tbb_GetPayloadData\n"
        "add r0, r0, r4, lsl #2\n"
        "ldrh r0, [r0]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00328c0c, 52)
extern "C" __attribute__((naked)) void engine_func_00328c0c() {
    asm volatile(
        "push {r3, lr}\n"
        "ldr r3, [r0, #4]\n"
        "mov r2, r1\n"
        "ldr r1, [r3, #8]\n"
        "str r1, [r3, #0x18]\n"
        "ldr r1, [r0, #4]\n"
        "mov r3, #0\n"
        "ldr r1, [r1, #8]\n"
        "str r1, [sp]\n"
        "mov r1, r0\n"
        "mov r0, sp\n"
        "bl AsdModel_func_002a9acc\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x003340dc, 52)
extern "C" __attribute__((naked)) void battle_func_003340dc() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r1\n"
        "bl battle_func_002ae3f0\n"
        "cmp r0, #0\n"
        "beq .L_19c_003340dc_0033410c\n"
        "ldrb r4, [r0, #0x22]\n"
        "mov r2, #4\n"
        "mov r1, r5\n"
        "bl func_0028412c\n"
        "sub r0, r4, r0\n"
        "cmp r0, #0\n"
        "movle r0, #1\n"
        ".L_19c_003340dc_0033410c:\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0034227c, 52)
extern "C" __attribute__((naked)) void func_0034227c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl func_0023d448\n"
        "add r0, r0, #0x1000\n"
        "add r0, r0, #0x2f0\n"
        "ldrb r1, [r0, r4, lsr #3]\n"
        "and r3, r4, #7\n"
        "mov r2, #1\n"
        "lsl r0, r2, r3\n"
        "and r0, r0, #0xff\n"
        "ands r0, r0, r1\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00342338, 52)
extern "C" __attribute__((naked)) void func_00342338() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl func_0023d448\n"
        "add r0, r0, #0x2000\n"
        "add r0, r0, #0x2f0\n"
        "ldrb r1, [r0, r4, lsr #3]\n"
        "and r3, r4, #7\n"
        "mov r2, #1\n"
        "lsl r0, r2, r3\n"
        "and r0, r0, #0xff\n"
        "ands r0, r0, r1\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003492a4, 52)
extern "C" __attribute__((naked)) void ui_func_003492a4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0b94\n"
        "add r1, r0, #0x1f400\n"
        "add r0, r0, #0x1f800\n"
        "add r1, r1, #0x58\n"
        "add r0, r0, #0x5c\n"
        "ldr r1, [r1]\n"
        "ldr r0, [r0]\n"
        "sub r0, r1, r0\n"
        "cmp r0, #0x384\n"
        "movhs r0, #1\n"
        "movlo r0, #0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0034fda4, 52)
extern "C" __attribute__((naked)) void engine_func_0034fda4() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        ".L_19c_0034fda4_0034fdac:\n"
        "add r0, r4, #0x20\n"
        "bl engine_func_002c3628\n"
        "ldrb r0, [r4, #0x10]\n"
        "cmp r0, #1\n"
        "beq .L_19c_0034fda4_0034fdd4\n"
        "mov r0, r4\n"
        "bl engine_func_003513dc\n"
        "nop \n"
        "nop \n"
        "b .L_19c_0034fda4_0034fdac\n"
        ".L_19c_0034fda4_0034fdd4:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0037da34, 52)
extern "C" __attribute__((naked)) void func_0037da34() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r0\n"
        "ldr r4, [r0, #0xc4]\n"
        "cmp r4, #0\n"
        "beq .L_19c_0037da34_0037da5c\n"
        ".L_19c_0037da34_0037da48:\n"
        "mov r0, r4\n"
        "bl func_00235ddc\n"
        "ldr r4, [r4, #0x138]\n"
        "cmp r4, #0\n"
        "bne .L_19c_0037da34_0037da48\n"
        ".L_19c_0037da34_0037da5c:\n"
        "mov r0, #0\n"
        "str r0, [r5, #0xc4]\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0038126c, 52)
extern "C" __attribute__((naked)) void func_0038126c() {
    asm volatile(
        "push {r4, lr}\n"
        "vpush {d8}\n"
        "vmov.f32 s17, s0\n"
        "vsub.f32 s16, s2, s1\n"
        "vsub.f32 s3, s17, s1\n"
        "vdiv.f32 s0, s3, s16\n"
        "bl func_002a337c\n"
        "vcvt.s32.f32 s1, s0\n"
        "vmov.f32 s0, s17\n"
        "vcvt.f32.s32 s1, s1\n"
        "vmls.f32 s0, s1, s16\n"
        "vpop {d8}\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003812f0, 52)
extern "C" __attribute__((naked)) void func_003812f0() {
    asm volatile(
        "push {r4, lr}\n"
        "vpush {d8}\n"
        "vmov.f32 s17, s0\n"
        "vsub.f32 s16, s2, s1\n"
        "vsub.f32 s3, s17, s1\n"
        "vdiv.f32 s0, s3, s16\n"
        "bl func_002a337c\n"
        "vcvt.s32.f32 s1, s0\n"
        "vmov.f32 s0, s17\n"
        "vcvt.f32.s32 s1, s1\n"
        "vmls.f32 s0, s1, s16\n"
        "vpop {d8}\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00381f88, 52)
extern "C" __attribute__((naked)) void ui_func_00381f88() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl ui_func_00282d98\n"
        "cmp r0, #0\n"
        "bne .L_19c_00381f88_00381fb8\n"
        "ldrb r1, [r4, #0x11]\n"
        "mov r0, #0\n"
        "cmp r1, #1\n"
        "movne r1, #4\n"
        "moveq r1, #5\n"
        "str r1, [r4, #4]!\n"
        "str r0, [r4, #4]\n"
        ".L_19c_00381f88_00381fb8:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003a1a88, 52)
extern "C" __attribute__((naked)) void ui_func_003a1a88() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl ui_func_00282d98\n"
        "cmp r0, #0\n"
        "bne .L_19c_003a1a88_003a1ab8\n"
        "ldr r0, [r4]\n"
        "mov r1, #0\n"
        "orr r0, r0, #0x100\n"
        "orr r0, r0, #2\n"
        "str r0, [r4]\n"
        "mov r0, #2\n"
        "strd r0, r1, [r4, #4]\n"
        ".L_19c_003a1a88_003a1ab8:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003ad8cc, 52)
extern "C" __attribute__((naked)) void ui_func_003ad8cc() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r0, #0x64\n"
        "mul r0, r4, r0\n"
        "bl ui_func_002c615c\n"
        "ands r0, r0, #0xff\n"
        "beq .L_19c_003ad8cc_003ad8f4\n"
        "cmp r0, #0x64\n"
        "movhi r0, #0x64\n"
        "pop {r4, pc}\n"
        ".L_19c_003ad8cc_003ad8f4:\n"
        "cmp r4, #0\n"
        "movgt r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003d6d74, 52)
extern "C" __attribute__((naked)) void engine_func_003d6d74() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r0\n"
        "add r5, r0, #0x400\n"
        "ldr r0, [r0, #0x734]\n"
        "add r5, r5, #0x334\n"
        "cmp r0, #0\n"
        "beq .L_19c_003d6d74_003d6da4\n"
        "bl AsdCamera_func_00310124\n"
        "str r0, [r4, #0x730]\n"
        "ldr r1, [r5]\n"
        "str r1, [r0, #0x14]\n"
        "mov r0, #1\n"
        ".L_19c_003d6d74_003d6da4:\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x003dc334, 52)
extern "C" __attribute__((naked)) void func_003dc334() {
    asm volatile(
        "push {r4, lr}\n"
        "cmp r3, #0\n"
        "ldr ip, [sp, #8]\n"
        "mov r4, r0\n"
        "mov r0, r2\n"
        "movne r2, #1\n"
        "moveq r2, #0\n"
        "mov r3, ip\n"
        "bl script_vm_func_00324db0\n"
        "add r4, r4, #0x1c00\n"
        "add r4, r4, #0xfc\n"
        "str r0, [r4]\n"
        "pop {r4, pc}\n"
    );
}
