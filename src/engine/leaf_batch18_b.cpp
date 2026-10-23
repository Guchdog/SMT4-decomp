#include "types.h"

// Call targets are declared by ledger name so the ARM CALL relocations remain
// explicit and can be checked against their known code addresses.
extern "C" void AsdLoadFile_func_002ae6c8();
extern "C" void AsdSequence_func_002c59b8();
extern "C" void battle_func_0028df54();
extern "C" void camp_func_0022e4e8();
extern "C" void camp_func_00290a4c();
extern "C" void camp_func_002a0640();
extern "C" void camp_func_002c0144();
extern "C" void camp_func_003bf674();
extern "C" void crt_func_001023e0();
extern "C" void engine_func_0010fc00();
extern "C" void engine_func_002310d8();
extern "C" void engine_func_00266d70();
extern "C" void engine_func_00286928();
extern "C" void engine_func_00296f60();
extern "C" void engine_func_002adf14();
extern "C" void engine_func_002bd630();
extern "C" void engine_func_002bdbcc();
extern "C" void engine_func_002bf85c();
extern "C" void engine_func_002c2b1c();
extern "C" void engine_func_002c5e3c();
extern "C" void func_00106d78();
extern "C" void func_0013728c();
extern "C" void func_0013aaf0();
extern "C" void func_0014699c();
extern "C" void func_001477bc();
extern "C" void func_00147930();
extern "C" void func_00147b4c();
extern "C" void func_0014f42c();
extern "C" void func_00223a18();
extern "C" void func_0025c1dc();
extern "C" void func_002a6d94();
extern "C" void func_002a7094();
extern "C" void func_002b5058();
extern "C" void func_002e05bc();
extern "C" void func_002e1ac8();
extern "C" void func_0035230c();
extern "C" void func_00352368();
extern "C" void func_0035242c();
extern "C" void func_00352508();
extern "C" void func_00356c48();
extern "C" void func_00356c78();
extern "C" void func_0035a288();
extern "C" void func_0037c490();
extern "C" void func_003e6a80();
extern "C" void func_003f6d54();
extern "C" void func_003f73b8();
extern "C" void nn_sdk_func_0010fed8();
extern "C" void nn_sdk_func_00239c50();
extern "C" void nn_sdk_func_002bbcdc();
extern "C" void script_vm_func_002458d4();
extern "C" void script_vm_func_0024ecc0();
extern "C" void script_vm_func_00255398();
extern "C" void script_vm_func_0027dbfc();
extern "C" void script_vm_func_002899c4();
extern "C" void script_vm_func_00295780();
extern "C" void script_vm_func_002b66ec();
extern "C" void script_vm_func_002b6700();
extern "C" void shop_func_00297178();
extern "C" void ui_func_00254ff0();
extern "C" void ui_func_00282b94();
extern "C" void ui_func_00293c98();
extern "C" void ui_func_002a63f8();
extern "C" void ui_func_002c0b94();

// DECOMP_FUNC(0x00398b3c, 28)
extern "C" __attribute__((naked)) void func_00398b3c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r1, #9\n"
        "bl shop_func_00297178\n"
        "mov r0, #1\n"
        "strb r0, [r4]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003bb570, 28)
extern "C" __attribute__((naked)) void ui_func_003bb570() {
    asm volatile(
        "mov r1, #0\n"
        "mov r0, #0x2a\n"
        "push {r4, lr}\n"
        "bl ui_func_002a63f8\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003bf77c, 28)
extern "C" __attribute__((naked)) void ui_func_003bf77c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl ui_func_00293c98\n"
        "mov r1, r4\n"
        "bl ui_func_00282b94\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003e7324, 28)
extern "C" __attribute__((naked)) void func_003e7324() {
    asm volatile(
        "ldr r0, [r0, #4]\n"
        "mov r0, r0\n"
        "push {r4, lr}\n"
        "ldr r0, [r0, #0x3c]\n"
        "bl func_003e6a80\n"
        "ldr r0, [r0]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003f74e0, 28)
extern "C" __attribute__((naked)) void func_003f74e0() {
    asm volatile(
        "push {r3, lr}\n"
        "ldr ip, [r1]\n"
        "mov r3, r2\n"
        "mov r2, sp\n"
        "str ip, [sp]\n"
        "bl func_003f73b8\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x001023c0, 32)
extern "C" __attribute__((naked)) void crt_func_001023c0() {
    asm volatile(
        "push {r4, lr}\n"
        "bl nn_sdk_func_0010fed8\n"
        "mov r0, #0\n"
        "bl func_00106d78\n"
        "mov r0, #0\n"
        "bl crt_func_001023e0\n"
        "bl engine_func_0010fc00\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00111aa0, 32)
extern "C" __attribute__((naked)) void engine_func_00111aa0() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "beq .L_18b_00111aa0_00111abc\n"
        "bl engine_func_002bf85c\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        ".L_18b_00111aa0_00111abc:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00121890, 32)
extern "C" __attribute__((naked)) void func_00121890() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl func_002b5058\n"
        "add r0, r4, #0xb4\n"
        "bl func_002b5058\n"
        "mov r0, #0\n"
        "strb r0, [r4, #0x18d]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001376a4, 32)
extern "C" __attribute__((naked)) void func_001376a4() {
    asm volatile(
        "push {r4, r5, lr}\n"
        "sub sp, sp, #0xc\n"
        "add lr, sp, #0x18\n"
        "ldm lr, {r4, r5, ip}\n"
        "stm sp, {r4, r5, ip}\n"
        "bl func_0013aaf0\n"
        "add sp, sp, #0xc\n"
        "pop {r4, r5, pc}\n"
    );
}

// DECOMP_FUNC(0x0014293c, 32)
extern "C" __attribute__((naked)) void battle_func_0014293c() {
    asm volatile(
        "push {r4, r5, lr}\n"
        "sub sp, sp, #0xc\n"
        "add lr, sp, #0x18\n"
        "ldm lr, {r4, r5, ip}\n"
        "stm sp, {r4, r5, ip}\n"
        "bl func_00147b4c\n"
        "add sp, sp, #0xc\n"
        "pop {r4, r5, pc}\n"
    );
}

// DECOMP_FUNC(0x0014295c, 32)
extern "C" __attribute__((naked)) void battle_func_0014295c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "sub sp, sp, #0x10\n"
        "add lr, sp, #0x20\n"
        "ldm lr, {r4, r5, r6, ip}\n"
        "stm sp, {r4, r5, r6, ip}\n"
        "bl func_001477bc\n"
        "add sp, sp, #0x10\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0014297c, 32)
extern "C" __attribute__((naked)) void battle_func_0014297c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "sub sp, sp, #0x10\n"
        "add lr, sp, #0x20\n"
        "ldm lr, {r4, r5, r6, ip}\n"
        "stm sp, {r4, r5, r6, ip}\n"
        "bl func_00147930\n"
        "add sp, sp, #0x10\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x00145e7c, 32)
extern "C" __attribute__((naked)) void nn_sdk_func_00145e7c() {
    asm volatile(
        "push {r3, r4, r5, lr}\n"
        "mov r4, r0\n"
        "bl nn_sdk_func_002bbcdc\n"
        "str r0, [sp]\n"
        "mov r1, r4\n"
        "mov r0, sp\n"
        "bl func_0014f42c\n"
        "pop {r3, r4, r5, pc}\n"
    );
}

// DECOMP_FUNC(0x0014d210, 32)
extern "C" __attribute__((naked)) void func_0014d210() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #1\n"
        "mov r1, sp\n"
        "add r0, r0, #4\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x00152054, 32)
extern "C" __attribute__((naked)) void func_00152054() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #0\n"
        "mov r1, sp\n"
        "add r0, r0, #0xc\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x001557bc, 32)
extern "C" __attribute__((naked)) void engine_func_001557bc() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #1\n"
        "mov r1, sp\n"
        "add r0, r0, #8\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x0019203c, 32)
extern "C" __attribute__((naked)) void engine_func_0019203c() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r0, #0\n"
        "strb r0, [sp]\n"
        "mov r2, #1\n"
        "mov r1, sp\n"
        "mov r0, #0x17\n"
        "bl AsdSequence_func_002c59b8\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x001c34ac, 32)
extern "C" __attribute__((naked)) void engine_func_001c34ac() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r2, #0x3c\n"
        "mov r1, #0\n"
        "bl camp_func_002a0640\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001d3a9c, 32)
extern "C" __attribute__((naked)) void func_001d3a9c() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00266d70\n"
        "vmov.f32 s1, s0\n"
        "vsqrt.f32 s0, s1\n"
        "bl func_002e05bc\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001f5e18, 32)
extern "C" __attribute__((naked)) void engine_func_001f5e18() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r0, #0\n"
        "str r0, [sp]\n"
        "mov r2, #4\n"
        "mov r1, sp\n"
        "mov r0, #0x15\n"
        "bl AsdSequence_func_002c59b8\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x001fc4d4, 32)
extern "C" __attribute__((naked)) void engine_func_001fc4d4() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r2, #1\n"
        "mov r1, r2\n"
        "bl script_vm_func_002899c4\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0020ea60, 32)
extern "C" __attribute__((naked)) void engine_func_0020ea60() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r2, #1\n"
        "mov r1, #0\n"
        "bl script_vm_func_002899c4\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00220c3c, 32)
extern "C" __attribute__((naked)) void func_00220c3c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, #0\n"
        "mov r1, r4\n"
        "bl script_vm_func_0024ecc0\n"
        "cmp r0, #0\n"
        "movne r4, #1\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0022a5d8, 32)
extern "C" __attribute__((naked)) void battle_func_0022a5d8() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00254ff0\n"
        "cmp r0, #0\n"
        "ldrne r0, [r0, #0x208]\n"
        "cmpne r0, #0\n"
        "movne r0, #1\n"
        "beq .L_18b_0022a5d8_0022a5f4\n"
        ".L_18b_0022a5d8_0022a5f4:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00231b54, 32)
extern "C" __attribute__((naked)) void func_00231b54() {
    asm volatile(
        "mov r0, #0\n"
        "push {r3, lr}\n"
        "mov r3, #0xf0\n"
        "mov r2, #0x140\n"
        "mov r1, r0\n"
        "str r0, [sp]\n"
        "bl camp_func_002c0144\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x0025506c, 32)
extern "C" __attribute__((naked)) void script_vm_func_0025506c() {
    asm volatile(
        "push {r4, lr}\n"
        "sub sp, sp, #8\n"
        "mov ip, #0\n"
        "ldr r4, [sp, #0x10]\n"
        "stm sp, {r4, ip}\n"
        "bl engine_func_00286928\n"
        "add sp, sp, #8\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00269e34, 32)
extern "C" __attribute__((naked)) void script_vm_func_00269e34() {
    asm volatile(
        "mov r2, r1\n"
        "mov r1, r0\n"
        "push {r3, lr}\n"
        "mov r0, sp\n"
        "bl camp_func_0022e4e8\n"
        "ldrh r0, [sp]\n"
        "lsr r0, r0, #0xa\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x00273bdc, 32)
extern "C" __attribute__((naked)) void script_vm_func_00273bdc() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl ui_func_002c0b94\n"
        "vldmia r4, {s0, s1, s2, s3, s4, s5}\n"
        "add r0, r0, #0x24800\n"
        "add r0, r0, #0x384\n"
        "vstmia r0, {s0, s1, s2, s3, s4, s5}\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002854ec, 32)
extern "C" __attribute__((naked)) void script_vm_func_002854ec() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002c2b1c\n"
        "cmp r4, #0\n"
        "movne r1, #1\n"
        "moveq r1, #0\n"
        "strb r1, [r0, #0x1c]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00287adc, 32)
extern "C" __attribute__((naked)) void script_vm_func_00287adc() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002adf14\n"
        "add r0, r0, r4, lsl #2\n"
        "ldrb r0, [r0, #0x202]\n"
        "and r0, r0, #2\n"
        "lsr r0, r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00295fac, 32)
extern "C" __attribute__((naked)) void script_vm_func_00295fac() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl script_vm_func_002b66ec\n"
        "ldrh r0, [r0, #0x72]\n"
        "mov r1, #1\n"
        "ands r0, r0, r1, lsl r4\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00297704, 32)
extern "C" __attribute__((naked)) void script_vm_func_00297704() {
    asm volatile(
        "str lr, [sp, #-4]!\n"
        "sub sp, sp, #0xc\n"
        "mov ip, #4\n"
        "mov r3, #0\n"
        "stm sp, {r3, ip}\n"
        "bl AsdLoadFile_func_002ae6c8\n"
        "add sp, sp, #0xc\n"
        "pop {pc}\n"
    );
}

// DECOMP_FUNC(0x00299064, 32)
extern "C" __attribute__((naked)) void script_vm_func_00299064() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002adf14\n"
        "add r0, r0, r4, lsl #2\n"
        "ldrb r0, [r0, #0x200]\n"
        "and r0, r0, #2\n"
        "lsr r0, r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0029909c, 32)
extern "C" __attribute__((naked)) void script_vm_func_0029909c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002b6700\n"
        "cmp r0, #0\n"
        "beq .L_18b_0029909c_002990b8\n"
        "ldrb r0, [r0, #7]\n"
        "and r0, r0, #2\n"
        "lsr r0, r0, #1\n"
        ".L_18b_0029909c_002990b8:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002990bc, 32)
extern "C" __attribute__((naked)) void script_vm_func_002990bc() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002adf14\n"
        "add r0, r0, r4, lsl #2\n"
        "ldrb r0, [r0, #0x200]\n"
        "and r0, r0, #8\n"
        "lsr r0, r0, #3\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002b3378, 32)
extern "C" __attribute__((naked)) void func_002b3378() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "add r0, r0, #0x18\n"
        "bl func_0014699c\n"
        "ldr r0, [r4, #0x54]\n"
        "sub r0, r0, #1\n"
        "str r0, [r4, #0x54]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002b67c0, 32)
extern "C" __attribute__((naked)) void engine_func_002b67c0() {
    asm volatile(
        "push {r4, lr}\n"
        "sub sp, sp, #8\n"
        "mov ip, #4\n"
        "ldr r4, [sp, #0x10]\n"
        "stm sp, {r4, ip}\n"
        "bl AsdLoadFile_func_002ae6c8\n"
        "add sp, sp, #8\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002c4afc, 32)
extern "C" __attribute__((naked)) void ui_func_002c4afc() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r1, #0\n"
        "str r1, [sp]\n"
        "mov r3, #0x80\n"
        "mov r2, #1\n"
        "mov r1, sp\n"
        "bl engine_func_002c5e3c\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x002d298c, 32)
extern "C" __attribute__((naked)) void engine_func_002d298c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r0\n"
        "mov r5, r1\n"
        "bl engine_func_002c2b1c\n"
        "cmp r4, #0x40\n"
        "addlt r0, r0, r4\n"
        "strblt r5, [r0, #0xbd8]\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x002fffcc, 32)
extern "C" __attribute__((naked)) void engine_func_002fffcc() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bl script_vm_func_00295780\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030b448, 32)
extern "C" __attribute__((naked)) void ui_func_0030b448() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "add r0, r0, #0x4000\n"
        "add r0, r0, #0x9c0\n"
        "ldr r0, [r0]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030b558, 32)
extern "C" __attribute__((naked)) void script_vm_func_0030b558() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_0027dbfc\n"
        "cmp r0, #4\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030b624, 32)
extern "C" __attribute__((naked)) void engine_func_0030b624() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl script_vm_func_002458d4\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00312614, 32)
extern "C" __attribute__((naked)) void battle_func_00312614() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_0025c1dc\n"
        "cmp r0, #0xe10\n"
        "movhs r0, #1\n"
        "movlo r0, #0\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0031872c, 32)
extern "C" __attribute__((naked)) void engine_func_0031872c() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r1, #3\n"
        "bl script_vm_func_00255398\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00318a14, 32)
extern "C" __attribute__((naked)) void battle_func_00318a14() {
    asm volatile(
        "push {r4, lr}\n"
        "bl camp_func_003bf674\n"
        "mov r4, r0\n"
        "bl func_00223a18\n"
        "mov r0, r4\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0033424c, 32)
extern "C" __attribute__((naked)) void script_vm_func_0033424c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl script_vm_func_002b66ec\n"
        "ldrh r1, [r0, #0x72]\n"
        "mov r2, #1\n"
        "orr r1, r1, r2, lsl r4\n"
        "strh r1, [r0, #0x72]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0033b570, 32)
extern "C" __attribute__((naked)) void func_0033b570() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, #0\n"
        ".L_18b_0033b570_0033b578:\n"
        "mov r0, r4\n"
        "bl func_002e1ac8\n"
        "add r4, r4, #1\n"
        "cmp r4, #0xc\n"
        "blt .L_18b_0033b570_0033b578\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00349758, 32)
extern "C" __attribute__((naked)) void func_00349758() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "add r0, r0, #4\n"
        "bl engine_func_002bdbcc\n"
        "mov r0, r4\n"
        "bl engine_func_002bdbcc\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00351d60, 32)
extern "C" __attribute__((naked)) void func_00351d60() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0]\n"
        "bl func_003f6d54\n"
        "mov r0, #0\n"
        "str r0, [r4]\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00352288, 32)
extern "C" __attribute__((naked)) void func_00352288() {
    asm volatile(
        "str lr, [sp, #-4]!\n"
        "sub sp, sp, #0xc\n"
        "add lr, sp, #0x10\n"
        "ldm lr, {r1, ip}\n"
        "stm sp, {r1, ip}\n"
        "bl func_0035230c\n"
        "add sp, sp, #0xc\n"
        "pop {pc}\n"
    );
}

// DECOMP_FUNC(0x003522a8, 32)
extern "C" __attribute__((naked)) void func_003522a8() {
    asm volatile(
        "push {r4, lr}\n"
        "sub sp, sp, #8\n"
        "add lr, sp, #0x10\n"
        "ldm lr, {r4, ip}\n"
        "stm sp, {r4, ip}\n"
        "bl func_00352368\n"
        "add sp, sp, #8\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003522c8, 32)
extern "C" __attribute__((naked)) void func_003522c8() {
    asm volatile(
        "push {r4, r5, lr}\n"
        "sub sp, sp, #0xc\n"
        "add lr, sp, #0x18\n"
        "ldm lr, {r4, r5, ip}\n"
        "stm sp, {r4, r5, ip}\n"
        "bl func_0035242c\n"
        "add sp, sp, #0xc\n"
        "pop {r4, r5, pc}\n"
    );
}

// DECOMP_FUNC(0x003522ec, 32)
extern "C" __attribute__((naked)) void func_003522ec() {
    asm volatile(
        "push {r4, lr}\n"
        "sub sp, sp, #0x10\n"
        "add lr, sp, #0x18\n"
        "ldm lr, {r3, r4, ip}\n"
        "stm sp, {r3, r4, ip}\n"
        "bl func_00352508\n"
        "add sp, sp, #0x10\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003563a4, 32)
extern "C" __attribute__((naked)) void func_003563a4() {
    asm volatile(
        "push {r3, r4, r5, lr}\n"
        "mov r4, r1\n"
        "bl nn_sdk_func_00239c50\n"
        "str r0, [sp]\n"
        "mov r1, r4\n"
        "mov r0, sp\n"
        "bl func_00356c78\n"
        "pop {r3, r4, r5, pc}\n"
    );
}

// DECOMP_FUNC(0x003563c4, 32)
extern "C" __attribute__((naked)) void func_003563c4() {
    asm volatile(
        "push {r3, r4, r5, lr}\n"
        "mov r4, r1\n"
        "bl nn_sdk_func_00239c50\n"
        "str r0, [sp]\n"
        "mov r1, r4\n"
        "mov r0, sp\n"
        "bl func_00356c48\n"
        "pop {r3, r4, r5, pc}\n"
    );
}

// DECOMP_FUNC(0x0035a2c4, 32)
extern "C" __attribute__((naked)) void func_0035a2c4() {
    asm volatile(
        "mov r0, r0\n"
        "push {r3, lr}\n"
        "mov r0, #0\n"
        "strb r0, [sp]\n"
        "mov r0, sp\n"
        "bl func_0035a288\n"
        "ldrb r0, [sp]\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x00374240, 32)
extern "C" __attribute__((naked)) void func_00374240() {
    asm volatile(
        "str lr, [sp, #-4]!\n"
        "sub sp, sp, #0x14\n"
        "add ip, sp, #0x18\n"
        "vldmia ip, {s0, s1, s2, s3}\n"
        "vstmia sp, {s0, s1, s2, s3}\n"
        "bl func_0013728c\n"
        "add sp, sp, #0x14\n"
        "pop {pc}\n"
    );
}

// DECOMP_FUNC(0x0037e834, 32)
extern "C" __attribute__((naked)) void func_0037e834() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002bd630\n"
        "add r1, r4, #0x50\n"
        "bl func_0037c490\n"
        "mov r0, #1\n"
        "strb r0, [r4, #0xd]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0037f8c0, 32)
extern "C" __attribute__((naked)) void func_0037f8c0() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002bd630\n"
        "add r1, r4, #0x50\n"
        "bl func_0037c490\n"
        "mov r0, #1\n"
        "strb r0, [r4, #0xd]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00381cd0, 32)
extern "C" __attribute__((naked)) void engine_func_00381cd0() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r0, #0\n"
        "strb r0, [r4, #9]\n"
        "strb r0, [r4, #8]\n"
        "bl camp_func_00290a4c\n"
        "str r0, [r4, #4]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0038a164, 32)
extern "C" __attribute__((naked)) void func_0038a164() {
    asm volatile(
        "mov r2, r1\n"
        "mov r1, #0xc\n"
        "push {r4, lr}\n"
        "bl func_002a7094\n"
        "cmp r0, #0\n"
        "movne r1, #0\n"
        "strbne r1, [r0, #0xd]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0038a344, 32)
extern "C" __attribute__((naked)) void func_0038a344() {
    asm volatile(
        "mov r2, r1\n"
        "mov r1, #0x10\n"
        "push {r4, lr}\n"
        "bl func_002a7094\n"
        "cmp r0, #0\n"
        "movne r1, #0\n"
        "strbne r1, [r0, #0xd]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0039ff40, 32)
extern "C" __attribute__((naked)) void func_0039ff40() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r1\n"
        "bl engine_func_002310d8\n"
        "mov r4, r0\n"
        "mov r0, r5\n"
        "bl engine_func_002310d8\n"
        "sub r0, r0, r4\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x003a0274, 32)
extern "C" __attribute__((naked)) void func_003a0274() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r1\n"
        "bl engine_func_002310d8\n"
        "mov r5, r0\n"
        "mov r0, r4\n"
        "bl engine_func_002310d8\n"
        "sub r0, r5, r0\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x003a65c4, 32)
extern "C" __attribute__((naked)) void func_003a65c4() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r1\n"
        "bl engine_func_002310d8\n"
        "mov r4, r0\n"
        "mov r0, r5\n"
        "bl engine_func_002310d8\n"
        "sub r0, r4, r0\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x003a6718, 32)
extern "C" __attribute__((naked)) void func_003a6718() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r1\n"
        "bl engine_func_002310d8\n"
        "mov r5, r0\n"
        "mov r0, r4\n"
        "bl engine_func_002310d8\n"
        "sub r0, r5, r0\n"
        "pop {r4, r5, r6, pc}\n"
    );
}
