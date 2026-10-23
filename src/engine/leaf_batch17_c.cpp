#include "types.h"

extern "C" void camp_func_0028fde4();
extern "C" void camp_func_0029e8e8();
extern "C" void camp_func_002c0144();
extern "C" void engine_func_0021f43c();
extern "C" void engine_func_00234a3c();
extern "C" void engine_func_0023963c();
extern "C" void engine_func_00246874();
extern "C" void engine_func_002adf14();
extern "C" void engine_func_002b96f0();
extern "C" void engine_func_002bc9d8();
extern "C" void engine_func_002c2b1c();
extern "C" void engine_func_0035ffd8();
extern "C" void func_001215dc();
extern "C" void func_0023a774();
extern "C" void func_00292300();
extern "C" void func_002aca14();
extern "C" void func_002bbd40();
extern "C" void func_002c85f0();
extern "C" void func_00356ed0();
extern "C" void func_003e698c();
extern "C" void func_003e69c0();
extern "C" void script_vm_func_00240e04();
extern "C" void script_vm_func_002b6700();
extern "C" void script_vm_func_002cc110();
extern "C" void shop_func_002337a0();
extern "C" void shop_func_002ae650();
extern "C" void ui_func_002bffbc();
extern "C" void ui_func_002c0ac8();
extern "C" void ui_func_002c0b94();
extern "C" void ui_func_00380b4c();

// DECOMP_FUNC(0x0037a548, 20)
extern "C" __attribute__((naked)) void func_0037a548() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl func_001215dc\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}
// DECOMP_FUNC(0x003bbec0, 20)
extern "C" __attribute__((naked)) void camp_func_003bbec0() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_0021f43c\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}
// DECOMP_FUNC(0x003c3044, 20)
extern "C" __attribute__((naked)) void camp_func_003c3044() {
    asm volatile(
        "push {r3, lr}\n"
        "mov ip, #0\n"
        "str ip, [sp]\n"
        "bl camp_func_002c0144\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x003c3058, 20)
extern "C" __attribute__((naked)) void camp_func_003c3058() {
    asm volatile(
        "push {r3, lr}\n"
        "mov ip, #3\n"
        "str ip, [sp]\n"
        "bl camp_func_002c0144\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x003dce60, 20)
extern "C" __attribute__((naked)) void script_vm_func_003dce60() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_00246874\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003dd1f4, 20)
extern "C" __attribute__((naked)) void engine_func_003dd1f4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_00246874\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003e0790, 20)
extern "C" __attribute__((naked)) void engine_func_003e0790() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_0023963c\n"
        "cmp r0, #0\n"
        "ldrne r0, [r0, #4]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003e7024, 20)
extern "C" __attribute__((naked)) void func_003e7024() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r0, [r0, #8]\n"
        "bl func_003e698c\n"
        "ldr r0, [r0]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003e706c, 20)
extern "C" __attribute__((naked)) void func_003e706c() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r0, [r0, #8]\n"
        "bl func_003e69c0\n"
        "ldr r0, [r0]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0022737c, 24)
extern "C" __attribute__((naked)) void ui_func_0022737c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r1\n"
        "mov r5, r2\n"
        "bl ui_func_002c0ac8\n"
        "strd r4, r5, [r0, #0x58]\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x00227394, 24)
extern "C" __attribute__((naked)) void ui_func_00227394() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r1\n"
        "mov r5, r2\n"
        "bl ui_func_002c0ac8\n"
        "strd r4, r5, [r0, #0x7c]\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0022ba54, 24)
extern "C" __attribute__((naked)) void engine_func_0022ba54() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl shop_func_002337a0\n"
        "add r0, r4, r0, lsl #2\n"
        "ldr r0, [r0, #0x530]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0022f34c, 24)
extern "C" __attribute__((naked)) void func_0022f34c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl shop_func_002ae650\n"
        "cmp r0, #0xa\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00240e04, 24)
extern "C" __attribute__((naked)) void script_vm_func_00240e04() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002adf14\n"
        "add r0, r0, r4, lsl #2\n"
        "add r0, r0, #0x200\n"
        "pop {r4, pc}\n"
    );
}
// DECOMP_FUNC(0x00241d70, 24)
extern "C" __attribute__((naked)) void script_vm_func_00241d70() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002adf14\n"
        "add r0, r0, r4, lsl #2\n"
        "ldrb r0, [r0, #0x201]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0025c064, 24)
extern "C" __attribute__((naked)) void engine_func_0025c064() {
    asm volatile(
        "push {r0, lr}\n"
        "vpush {d0, d1}\n"
        "mov r1, sp\n"
        "bl script_vm_func_002cc110\n"
        "add sp, sp, #0x14\n"
        "pop {pc}\n"
    );
}

// DECOMP_FUNC(0x002762d0, 24)
extern "C" __attribute__((naked)) void script_vm_func_002762d0() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002c2b1c\n"
        "add r0, r0, r4\n"
        "ldrb r0, [r0, #0xbd8]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00288918, 24)
extern "C" __attribute__((naked)) void script_vm_func_00288918() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_00240e04\n"
        "ldrb r0, [r0]\n"
        "and r0, r0, #0x40\n"
        "lsr r0, r0, #6\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00288930, 24)
extern "C" __attribute__((naked)) void script_vm_func_00288930() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_00240e04\n"
        "ldrb r0, [r0]\n"
        "and r0, r0, #0x20\n"
        "lsr r0, r0, #5\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0028ec78, 24)
extern "C" __attribute__((naked)) void battle_func_0028ec78() {
    asm volatile(
        "push {r4, lr}\n"
        "bl camp_func_0028fde4\n"
        "cmp r0, #0\n"
        "movgt r0, #1\n"
        "movle r0, #0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00299224, 24)
extern "C" __attribute__((naked)) void script_vm_func_00299224() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002b6700\n"
        "cmp r0, #0\n"
        "ldrbne r0, [r0, #7]\n"
        "andne r0, r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002a63f8, 24)
extern "C" __attribute__((naked)) void ui_func_002a63f8() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_002b96f0\n"
        "ldr r0, [r0, #0x10]\n"
        "ands r0, r0, #4\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002b7488, 24)
extern "C" __attribute__((naked)) void engine_func_002b7488() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r1, sp\n"
        "mov r0, #0x208\n"
        "bl engine_func_002bc9d8\n"
        "ldr r0, [sp]\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x002b756c, 24)
extern "C" __attribute__((naked)) void engine_func_002b756c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0ac8\n"
        "ldr r1, [r0, #4]\n"
        "ldr r0, [r0, #8]\n"
        "add r0, r0, r1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002c0c5c, 24)
extern "C" __attribute__((naked)) void ui_func_002c0c5c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0b94\n"
        "add r0, r0, #0x1ec00\n"
        "add r0, r0, #0x51\n"
        "ldrb r0, [r0]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002cd844, 24)
extern "C" __attribute__((naked)) void func_002cd844() {
    asm volatile(
        "mov r1, #1\n"
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl func_00292300\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002df798, 24)
extern "C" __attribute__((naked)) void engine_func_002df798() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002c2b1c\n"
        "add r0, r0, r4\n"
        "ldrb r0, [r0, #0xc18]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002e4238, 24)
extern "C" __attribute__((naked)) void camp_func_002e4238() {
    asm volatile(
        "mov r1, #0\n"
        "mov r0, r1\n"
        "push {r4, lr}\n"
        "bl camp_func_0029e8e8\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}
// DECOMP_FUNC(0x00310d00, 24)
extern "C" __attribute__((naked)) void func_00310d00() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_002c85f0\n"
        "cmp r0, #5\n"
        "moveq r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00316e2c, 24)
extern "C" __attribute__((naked)) void engine_func_00316e2c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_002c2b1c\n"
        "ldrb r0, [r0, #0x1c]\n"
        "cmp r0, #1\n"
        "movne r0, #0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0032483c, 24)
extern "C" __attribute__((naked)) void ui_func_0032483c() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl ui_func_002bffbc\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00328658, 24)
extern "C" __attribute__((naked)) void ui_func_00328658() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl ui_func_002bffbc\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00328670, 24)
extern "C" __attribute__((naked)) void ui_func_00328670() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl ui_func_002bffbc\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00343d28, 24)
extern "C" __attribute__((naked)) void engine_func_00343d28() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_002bbd40\n"
        "ldrb r0, [r0, #0x10]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00348a94, 24)
extern "C" __attribute__((naked)) void func_00348a94() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00380b4c\n"
        "mov r2, #0\n"
        "str r2, [r0, #0x20]\n"
        "str r2, [r0, #0x24]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00351028, 24)
extern "C" __attribute__((naked)) void func_00351028() {
    asm volatile(
        "add r0, r0, #0x158\n"
        "push {r4, lr}\n"
        "bl func_0023a774\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003537e8, 24)
extern "C" __attribute__((naked)) void func_003537e8() {
    asm volatile(
        "add r0, r0, #0x14\n"
        "push {r4, lr}\n"
        "bl engine_func_0035ffd8\n"
        "lsrs r1, r0, #0x1f\n"
        "moveq r0, #0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00354d50, 24)
extern "C" __attribute__((naked)) void func_00354d50() {
    asm volatile(
        "push {r3, lr}\n"
        "add r0, r0, #8\n"
        "ldr r1, [sp, #8]\n"
        "str r1, [sp]\n"
        "bl func_002aca14\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x00354d68, 24)
extern "C" __attribute__((naked)) void func_00354d68() {
    asm volatile(
        "push {r3, lr}\n"
        "add r0, r0, #8\n"
        "ldr ip, [sp, #8]\n"
        "str ip, [sp]\n"
        "bl func_00356ed0\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x00383884, 24)
extern "C" __attribute__((naked)) void script_vm_func_00383884() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r0, [r0, #0xd0c]\n"
        "uxth r0, r0\n"
        "bl script_vm_func_002b6700\n"
        "ldrh r0, [r0]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0038b600, 24)
extern "C" __attribute__((naked)) void func_0038b600() {
    asm volatile(
        "add r0, r0, #0x88\n"
        "push {r4, lr}\n"
        "bl engine_func_00234a3c\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}
