#include "types.h"

// Call targets are declared by ledger name so the ARM CALL relocations remain
// explicit and can be checked against their known code addresses.
extern "C" void AsdLoadFile_func_002ae6c8();
extern "C" void AsdSequence_func_002c59b8();
extern "C" void battle_func_0023f554();
extern "C" void battle_func_0024eed4();
extern "C" void battle_func_0028df54();
extern "C" void battle_func_002b087c();
extern "C" void battle_func_002c00b4();
extern "C" void camp_func_00288380();
extern "C" void camp_func_002b9364();
extern "C" void engine_func_00296f60();
extern "C" void engine_func_002ad630();
extern "C" void engine_func_002adf14();
extern "C" void engine_func_0035798c();
extern "C" void func_0011d1d0();
extern "C" void func_001564f0();
extern "C" void func_0015ef34();
extern "C" void func_0023a270();
extern "C" void func_00244f38();
extern "C" void func_002a6d94();
extern "C" void func_002c14a8();
extern "C" void func_00338424();
extern "C" void func_00356d94();
extern "C" void func_0036a54c();
extern "C" void func_0036a7b8();
extern "C" void func_003e46a4();
extern "C" void nn_sdk_func_00239c50();
extern "C" void script_vm_func_00256020();
extern "C" void script_vm_func_0025b920();
extern "C" void script_vm_func_0026fbd0();
extern "C" void script_vm_func_0027de00();
extern "C" void script_vm_func_002904d0();
extern "C" void script_vm_func_00290694();
extern "C" void script_vm_func_002b5f84();
extern "C" void script_vm_func_002b6700();
extern "C" void script_vm_func_002bd9ec();
extern "C" void script_vm_func_002f4edc();
extern "C" void shop_func_00297178();
extern "C" void ui_func_00293c98();
extern "C" void ui_func_00297004();
extern "C" void ui_func_002a0fec();
extern "C" void ui_func_002c0ac8();
extern "C" void ui_func_002c3b00();
extern "C" void ui_func_002ebb30();

// DECOMP_FUNC(0x003ba954, 32)
extern "C" __attribute__((naked)) void engine_func_003ba954() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "add r0, r0, #0x42\n"
        "bl script_vm_func_002bd9ec\n"
        "ldr r0, [r4, #0x20]\n"
        "orr r0, r0, #0x10\n"
        "str r0, [r4, #0x20]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003dfc38, 32)
extern "C" __attribute__((naked)) void func_003dfc38() {
    asm volatile(
        "push {r3, r4, r5, lr}\n"
        "mov r4, r1\n"
        "bl nn_sdk_func_00239c50\n"
        "str r0, [sp]\n"
        "mov r1, r4\n"
        "mov r0, sp\n"
        "bl func_00356d94\n"
        "pop {r3, r4, r5, pc}\n"
    );
}

// DECOMP_FUNC(0x003e5f34, 32)
extern "C" __attribute__((naked)) void func_003e5f34() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r1\n"
        "bl func_003e46a4\n"
        "mov r5, r0\n"
        "mov r0, r4\n"
        "bl func_0036a54c\n"
        "and r0, r0, r5\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x003e6004, 32)
extern "C" __attribute__((naked)) void func_003e6004() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r1\n"
        "bl func_003e46a4\n"
        "mov r5, r0\n"
        "mov r0, r4\n"
        "bl func_0036a7b8\n"
        "and r0, r0, r5\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x003e6a8c, 32)
extern "C" __attribute__((naked)) void func_003e6a8c() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #2\n"
        "mov r1, sp\n"
        "add r0, r0, #4\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x003e6aac, 32)
extern "C" __attribute__((naked)) void func_003e6aac() {
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

// DECOMP_FUNC(0x00110058, 36)
extern "C" __attribute__((naked)) void func_00110058() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_0011d1d0\n"
        "cmp r0, #0\n"
        "bne .L_18c_00110058_00110074\n"
        "bl func_002c14a8\n"
        "cmp r0, #0\n"
        "beq .L_18c_00110058_00110078\n"
        ".L_18c_00110058_00110074:\n"
        "mov r0, #1\n"
        ".L_18c_00110058_00110078:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001520d0, 36)
extern "C" __attribute__((naked)) void func_001520d0() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #1\n"
        "mov r1, sp\n"
        "add r0, r0, #0x14\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "andne r0, r0, #0xff\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x00152120, 36)
extern "C" __attribute__((naked)) void func_00152120() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #0x11\n"
        "mov r1, sp\n"
        "add r0, r0, #0x14\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "andne r0, r0, #1\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x0017fa7c, 36)
extern "C" __attribute__((naked)) void func_0017fa7c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r1, #9\n"
        "bl ui_func_002a0fec\n"
        "ldr r0, [r4, #0x18]\n"
        "add r0, r0, #1\n"
        "str r0, [r4, #0x18]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0017faa0, 36)
extern "C" __attribute__((naked)) void func_0017faa0() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r1, #8\n"
        "bl ui_func_002a0fec\n"
        "ldr r0, [r4, #0x18]\n"
        "add r0, r0, #1\n"
        "str r0, [r4, #0x18]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0018b26c, 36)
extern "C" __attribute__((naked)) void func_0018b26c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r1, #6\n"
        "bl ui_func_002a0fec\n"
        "ldr r0, [r4, #0x18]\n"
        "add r0, r0, #1\n"
        "str r0, [r4, #0x18]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0018b330, 36)
extern "C" __attribute__((naked)) void func_0018b330() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r1, #0xb\n"
        "bl ui_func_002a0fec\n"
        "ldr r0, [r4, #0x18]\n"
        "add r0, r0, #1\n"
        "str r0, [r4, #0x18]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0018b354, 36)
extern "C" __attribute__((naked)) void func_0018b354() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r1, #4\n"
        "bl ui_func_002a0fec\n"
        "ldr r0, [r4, #0x18]\n"
        "add r0, r0, #1\n"
        "str r0, [r4, #0x18]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0018b378, 36)
extern "C" __attribute__((naked)) void func_0018b378() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r1, #0xa\n"
        "bl ui_func_002a0fec\n"
        "ldr r0, [r4, #0x18]\n"
        "add r0, r0, #1\n"
        "str r0, [r4, #0x18]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001927a4, 36)
extern "C" __attribute__((naked)) void func_001927a4() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r1, #0\n"
        "bl ui_func_002a0fec\n"
        "ldr r0, [r4, #0x18]\n"
        "add r0, r0, #1\n"
        "str r0, [r4, #0x18]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001927c8, 36)
extern "C" __attribute__((naked)) void func_001927c8() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r1, #5\n"
        "bl ui_func_002a0fec\n"
        "ldr r0, [r4, #0x18]\n"
        "add r0, r0, #1\n"
        "str r0, [r4, #0x18]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001927ec, 36)
extern "C" __attribute__((naked)) void func_001927ec() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r1, #3\n"
        "bl ui_func_002a0fec\n"
        "ldr r0, [r4, #0x18]\n"
        "add r0, r0, #1\n"
        "str r0, [r4, #0x18]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0019283c, 36)
extern "C" __attribute__((naked)) void func_0019283c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r1, #2\n"
        "bl ui_func_002a0fec\n"
        "ldr r0, [r4, #0x18]\n"
        "add r0, r0, #1\n"
        "str r0, [r4, #0x18]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00192860, 36)
extern "C" __attribute__((naked)) void func_00192860() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r1, #7\n"
        "bl ui_func_002a0fec\n"
        "ldr r0, [r4, #0x18]\n"
        "add r0, r0, #1\n"
        "str r0, [r4, #0x18]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00192948, 36)
extern "C" __attribute__((naked)) void func_00192948() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r1, #1\n"
        "bl ui_func_002a0fec\n"
        "ldr r0, [r4, #0x18]\n"
        "add r0, r0, #1\n"
        "str r0, [r4, #0x18]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001b4b98, 36)
extern "C" __attribute__((naked)) void engine_func_001b4b98() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r1, r0\n"
        "mov r0, #0\n"
        "bl ui_func_00297004\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001db440, 36)
extern "C" __attribute__((naked)) void ui_func_001db440() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, #0\n"
        "bl ui_func_002ebb30\n"
        "bl engine_func_0035798c\n"
        "and r0, r0, #0x80000000\n"
        "cmp r0, #0\n"
        "movge r4, #1\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001eb71c, 36)
extern "C" __attribute__((naked)) void ui_func_001eb71c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0ac8\n"
        "add r1, r0, #0x34\n"
        "add r4, r0, #0x4c\n"
        "ldm r1, {r1, r2, r3}\n"
        "stm r4, {r1, r2, r3}\n"
        "mov r1, #1\n"
        "str r1, [r0, #0x78]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00205af0, 36)
extern "C" __attribute__((naked)) void engine_func_00205af0() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r1, r0\n"
        "mov r0, #0\n"
        "bl script_vm_func_00256020\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00222174, 36)
extern "C" __attribute__((naked)) void script_vm_func_00222174() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl script_vm_func_0027de00\n"
        "mov r0, r4\n"
        "bl script_vm_func_0026fbd0\n"
        "mov r0, #2\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0023a24c, 36)
extern "C" __attribute__((naked)) void func_0023a24c() {
    asm volatile(
        "push {r3, r4, r5, lr}\n"
        "mov r4, r0\n"
        "bl script_vm_func_002b5f84\n"
        "ldr r2, [r4]\n"
        "mov r1, sp\n"
        "bl func_0023a270\n"
        "lsrs r1, r0, #0x1f\n"
        "moveq r0, #0\n"
        "pop {r3, r4, r5, pc}\n"
    );
}

// DECOMP_FUNC(0x0027dbd8, 36)
extern "C" __attribute__((naked)) void script_vm_func_0027dbd8() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002904d0\n"
        "cmp r0, #0\n"
        "beq .L_18c_0027dbd8_0027dbf4\n"
        "bl script_vm_func_00290694\n"
        "cmp r0, #0\n"
        "bgt .L_18c_0027dbd8_0027dbf8\n"
        ".L_18c_0027dbd8_0027dbf4:\n"
        "mvn r0, #0\n"
        ".L_18c_0027dbd8_0027dbf8:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002931cc, 36)
extern "C" __attribute__((naked)) void battle_func_002931cc() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl battle_func_0023f554\n"
        "ldrb r0, [r0, r4, lsr #3]\n"
        "and r2, r4, #7\n"
        "mov r3, #1\n"
        "ands r0, r0, r3, lsl r2\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002a14e8, 36)
extern "C" __attribute__((naked)) void engine_func_002a14e8() {
    asm volatile(
        "str lr, [sp, #-4]!\n"
        "sub sp, sp, #0xc\n"
        "mov ip, #0\n"
        "str r3, [sp, #4]\n"
        "mov r3, ip\n"
        "str ip, [sp]\n"
        "bl AsdLoadFile_func_002ae6c8\n"
        "add sp, sp, #0xc\n"
        "pop {pc}\n"
    );
}

// DECOMP_FUNC(0x002bcfcc, 36)
extern "C" __attribute__((naked)) void script_vm_func_002bcfcc() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r1\n"
        "bl script_vm_func_002b6700\n"
        "cmp r0, #0\n"
        "beq .L_18c_002bcfcc_002bcfec\n"
        "cmp r4, #0\n"
        "addeq r0, r0, #8\n"
        "addne r0, r0, #0x38\n"
        ".L_18c_002bcfcc_002bcfec:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002c0ba8, 36)
extern "C" __attribute__((naked)) void script_vm_func_002c0ba8() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002adf14\n"
        "ldrb r0, [r0, r4, lsr #3]\n"
        "and r3, r4, #7\n"
        "mov r1, #1\n"
        "ands r0, r0, r1, lsl r3\n"
        "movne r0, r1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002cd85c, 36)
extern "C" __attribute__((naked)) void engine_func_002cd85c() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r0, #0\n"
        "str r0, [sp]\n"
        "mov r2, #4\n"
        "mov r1, sp\n"
        "mov r0, #0x13\n"
        "bl AsdSequence_func_002c59b8\n"
        "mov r0, #1\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x002cd910, 36)
extern "C" __attribute__((naked)) void engine_func_002cd910() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, #0\n"
        "mov r0, r4\n"
        "bl engine_func_00296f60\n"
        "bl script_vm_func_002f4edc\n"
        "cmp r0, #0\n"
        "movne r4, #1\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002e4034, 36)
extern "C" __attribute__((naked)) void engine_func_002e4034() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl script_vm_func_0025b920\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002e40c0, 36)
extern "C" __attribute__((naked)) void battle_func_002e40c0() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl battle_func_002b087c\n"
        "ldrb r0, [r0, #2]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002f11a0, 36)
extern "C" __attribute__((naked)) void ui_func_002f11a0() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "ldr r0, [r0, #0xe0]\n"
        "tst r0, #0x40000\n"
        "movne r0, #0\n"
        "moveq r0, #1\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002f7734, 36)
extern "C" __attribute__((naked)) void engine_func_002f7734() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl camp_func_002b9364\n"
        "ldrb r0, [r0, #0x30]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030012c, 36)
extern "C" __attribute__((naked)) void battle_func_0030012c() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl battle_func_002b087c\n"
        "ldr r0, [r0, #0x78]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030b534, 36)
extern "C" __attribute__((naked)) void ui_func_0030b534() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "ldr r0, [r0, #0xe0]\n"
        "tst r0, #0x80000\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00310590, 36)
extern "C" __attribute__((naked)) void battle_func_00310590() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r0, [r0, #0x2c]\n"
        "add r4, r0, #0x4c\n"
        "mov r0, r4\n"
        "bl battle_func_002c00b4\n"
        "ldr r0, [r4, #0x3c]\n"
        "orr r0, r0, #0x800\n"
        "str r0, [r4, #0x3c]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00312770, 36)
extern "C" __attribute__((naked)) void battle_func_00312770() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl battle_func_002b087c\n"
        "ldrh r0, [r0, #0x86]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00312c00, 36)
extern "C" __attribute__((naked)) void ui_func_00312c00() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "add r1, r0, #0x4000\n"
        "add r1, r1, #0x4a0\n"
        "mov r0, #1\n"
        "ldr r2, [r1, #4]\n"
        "orr r2, r2, #1\n"
        "str r2, [r1, #4]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0031874c, 36)
extern "C" __attribute__((naked)) void battle_func_0031874c() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl battle_func_002b087c\n"
        "ldrh r0, [r0, #0xa0]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00318974, 36)
extern "C" __attribute__((naked)) void battle_func_00318974() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl battle_func_002b087c\n"
        "ldrh r0, [r0, #0x84]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003189c4, 36)
extern "C" __attribute__((naked)) void engine_func_003189c4() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl camp_func_002b9364\n"
        "ldrb r0, [r0, #0x31]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003189e8, 36)
extern "C" __attribute__((naked)) void battle_func_003189e8() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl battle_func_002b087c\n"
        "ldr r0, [r0, #0x74]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00323590, 36)
extern "C" __attribute__((naked)) void ui_func_00323590() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "add r1, r0, #0x4000\n"
        "add r1, r1, #0x4a0\n"
        "mov r0, #1\n"
        "ldr r2, [r1]\n"
        "orr r2, r2, #0x20000\n"
        "str r2, [r1]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003235f8, 36)
extern "C" __attribute__((naked)) void engine_func_003235f8() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl ui_func_00293c98\n"
        "mov r1, r4\n"
        "bl func_00338424\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00324d48, 36)
extern "C" __attribute__((naked)) void engine_func_00324d48() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl func_00244f38\n"
        "mov r1, r0\n"
        "mov r0, #0\n"
        "bl battle_func_0024eed4\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00398b5c, 36)
extern "C" __attribute__((naked)) void func_00398b5c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r1, #1\n"
        "bl shop_func_00297178\n"
        "mov r0, #0x140\n"
        "mov r1, #0\n"
        "strd r0, r1, [r4, #0xa4]\n"
        "str r0, [r4, #0xac]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003aab30, 36)
extern "C" __attribute__((naked)) void func_003aab30() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r1\n"
        "ldrh r0, [r0]\n"
        "bl camp_func_00288380\n"
        "mov r5, r0\n"
        "ldrh r0, [r4]\n"
        "bl camp_func_00288380\n"
        "sub r0, r5, r0\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x003aaecc, 36)
extern "C" __attribute__((naked)) void func_003aaecc() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r1\n"
        "ldrh r0, [r0]\n"
        "bl camp_func_00288380\n"
        "mov r5, r0\n"
        "ldrh r0, [r4]\n"
        "bl camp_func_00288380\n"
        "sub r0, r0, r5\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x003e64cc, 36)
extern "C" __attribute__((naked)) void func_003e64cc() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #0\n"
        "mov r1, sp\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "moveq r0, #0x40\n"
        "andne r0, r0, #0xff\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x003e6b28, 36)
extern "C" __attribute__((naked)) void func_003e6b28() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #0x1f\n"
        "mov r1, sp\n"
        "add r0, r0, #0x14\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "mvneq r0, #0\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x0013a274, 40)
extern "C" __attribute__((naked)) void ui_func_0013a274() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldrb r0, [r0]\n"
        "cmp r0, #0\n"
        "bne .L_18c_0013a274_0013a298\n"
        "add r0, r4, #0x34\n"
        "bl ui_func_002c3b00\n"
        "mov r0, #1\n"
        "strb r0, [r4]\n"
        ".L_18c_0013a274_0013a298:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00146f1c, 40)
extern "C" __attribute__((naked)) void func_00146f1c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002ad630\n"
        "mov r1, r4\n"
        "pop {r4, lr}\n"
        "mov r0, r0\n"
        "ldrb r2, [r0, #0x30]\n"
        "cmp r2, #0\n"
        "strbeq r1, [r0, #8]\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0014d0f8, 40)
extern "C" __attribute__((naked)) void func_0014d0f8() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #0\n"
        "mov r1, sp\n"
        "add r0, r0, #4\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "moveq r0, #0x40\n"
        "andne r0, r0, #0xff\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x0014d14c, 40)
extern "C" __attribute__((naked)) void func_0014d14c() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #2\n"
        "mov r1, sp\n"
        "add r0, r0, #4\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "moveq r0, #0x40\n"
        "andne r0, r0, #0xff\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x0014d1e8, 40)
extern "C" __attribute__((naked)) void func_0014d1e8() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #1\n"
        "mov r1, sp\n"
        "add r0, r0, #4\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "moveq r0, #0x60\n"
        "andne r0, r0, #0xff\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x0014fac8, 40)
extern "C" __attribute__((naked)) void func_0014fac8() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002ad630\n"
        "mov r1, r0\n"
        "mov r0, r4\n"
        "pop {r4, lr}\n"
        "mov r0, r0\n"
        "ldm r1, {r1, r2}\n"
        "stm r0, {r1, r2}\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00151fa0, 40)
extern "C" __attribute__((naked)) void func_00151fa0() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #0\n"
        "mov r1, sp\n"
        "add r0, r0, #8\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "moveq r0, #0x40\n"
        "andne r0, r0, #0xff\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x00152074, 40)
extern "C" __attribute__((naked)) void func_00152074() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #1\n"
        "mov r1, sp\n"
        "add r0, r0, #0xc\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "moveq r0, #0x40\n"
        "andne r0, r0, #0xff\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x0015217c, 40)
extern "C" __attribute__((naked)) void func_0015217c() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #2\n"
        "mov r1, sp\n"
        "add r0, r0, #0x14\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "moveq r0, #0x40\n"
        "andne r0, r0, #0xff\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x0015d91c, 40)
extern "C" __attribute__((naked)) void func_0015d91c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0, r1, lsl #2]\n"
        "mov r5, r2\n"
        "mov r6, r3\n"
        "mov r1, r2\n"
        "bl func_001564f0\n"
        "cmp r6, #0\n"
        "strne r5, [r4, #0x1c]\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0015e7d0, 40)
extern "C" __attribute__((naked)) void func_0015e7d0() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "sub sp, sp, #0x18\n"
        "add lr, sp, #0x28\n"
        "ldm lr, {r4, r5, r6, ip}\n"
        "stm sp, {r3, r4, r5, r6, ip}\n"
        "mov r3, r2\n"
        "mov r2, #0\n"
        "bl func_0015ef34\n"
        "add sp, sp, #0x18\n"
        "pop {r4, r5, r6, pc}\n"
    );
}
