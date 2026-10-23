#include "types.h"

// DECOMP_FUNC(0x002b4d64, 8)
extern "C" __attribute__((naked)) void script_vm_func_002b4d64() {
    asm volatile(
        "add ip, pc, #1\n"
        "bx ip\n"
    );
}

// DECOMP_FUNC(0x001240c0, 12)
extern "C" __attribute__((naked)) void battle_func_001240c0() {
    asm volatile(
        "mov r0, r0\n"
        "svc #0x28\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003e62f0, 12)
extern "C" __attribute__((naked)) void func_003e62f0() {
    asm volatile(
        "ldr r2, [r0]\n"
        "ldr r2, [r2, #0x14]\n"
        "bx r2\n"
    );
}

// DECOMP_FUNC(0x003eaf40, 12)
extern "C" __attribute__((naked)) void func_003eaf40() {
    asm volatile(
        "ldr r2, [r0, #-0xc]!\n"
        "ldr r2, [r2, #0x10]\n"
        "bx r2\n"
    );
}

// DECOMP_FUNC(0x003eb060, 12)
extern "C" __attribute__((naked)) void func_003eb060() {
    asm volatile(
        "ldr r1, [r0, #-0x44]!\n"
        "ldr r1, [r1, #0x14]\n"
        "bx r1\n"
    );
}

// DECOMP_FUNC(0x003eb10c, 12)
extern "C" __attribute__((naked)) void func_003eb10c() {
    asm volatile(
        "ldr r1, [r0, #-0x50]!\n"
        "ldr r1, [r1, #0x14]\n"
        "bx r1\n"
    );
}

// DECOMP_FUNC(0x003eb1bc, 12)
extern "C" __attribute__((naked)) void func_003eb1bc() {
    asm volatile(
        "ldr r1, [r0, #-0x50]!\n"
        "ldr r1, [r1, #0x14]\n"
        "bx r1\n"
    );
}

// DECOMP_FUNC(0x0011fff8, 16)
extern "C" __attribute__((naked)) void func_0011fff8() {
    asm volatile(
        "ldr r0, [r0, #8]\n"
        "ldr r1, [r0]\n"
        "ldr r1, [r1, #0x10]\n"
        "bx r1\n"
    );
}

// DECOMP_FUNC(0x0034240c, 16)
extern "C" __attribute__((naked)) void func_0034240c() {
    asm volatile(
        "ldr r1, [r0, #8]\n"
        "ldr r0, [r0, #4]\n"
        "ldr r1, [r1, #0x1c]\n"
        "bx r1\n"
    );
}

// DECOMP_FUNC(0x0034241c, 16)
extern "C" __attribute__((naked)) void func_0034241c() {
    asm volatile(
        "ldr r2, [r0, #8]\n"
        "ldr r0, [r0, #4]\n"
        "ldr r2, [r2]\n"
        "bx r2\n"
    );
}

// DECOMP_FUNC(0x0034243c, 16)
extern "C" __attribute__((naked)) void func_0034243c() {
    asm volatile(
        "ldr r2, [r0, #8]\n"
        "ldr r0, [r0, #4]\n"
        "ldr r2, [r2, #0xc]\n"
        "bx r2\n"
    );
}

// DECOMP_FUNC(0x00343b0c, 16)
extern "C" __attribute__((naked)) void func_00343b0c() {
    asm volatile(
        "ldr r0, [r0, #0x14]\n"
        "ldr r1, [r0]\n"
        "ldr r1, [r1, #0x10]\n"
        "bx r1\n"
    );
}

// DECOMP_FUNC(0x0035568c, 16)
extern "C" __attribute__((naked)) void func_0035568c() {
    asm volatile(
        "ldr r0, [r0, #8]\n"
        "ldr r2, [r0]\n"
        "ldr r2, [r2, #0x20]\n"
        "bx r2\n"
    );
}

// DECOMP_FUNC(0x003556a8, 16)
extern "C" __attribute__((naked)) void func_003556a8() {
    asm volatile(
        "ldr r0, [r0, #4]\n"
        "ldr r2, [r0]\n"
        "ldr r2, [r2, #0x44]\n"
        "bx r2\n"
    );
}

// DECOMP_FUNC(0x001131d8, 24)
extern "C" __attribute__((naked)) void func_001131d8() {
    asm volatile(
        "str r0, [sp, #-4]!\n"
        "svc #0x21\n"
        "ldr r2, [sp]\n"
        "str r1, [r2]\n"
        "add sp, sp, #4\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x001131f0, 24)
extern "C" __attribute__((naked)) void func_001131f0() {
    asm volatile(
        "str r0, [sp, #-4]!\n"
        "svc #0x38\n"
        "ldr r2, [sp]\n"
        "str r1, [r2]\n"
        "add sp, sp, #4\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00144900, 24)
extern "C" __attribute__((naked)) void func_00144900() {
    asm volatile(
        "str r0, [sp, #-4]!\n"
        "svc #0x35\n"
        "ldr r2, [sp]\n"
        "str r1, [r2]\n"
        "add sp, sp, #4\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0015f764, 24)
extern "C" __attribute__((naked)) void func_0015f764() {
    asm volatile(
        "str r0, [sp, #-4]!\n"
        "svc #0x27\n"
        "ldr r2, [sp]\n"
        "str r1, [r2]\n"
        "add sp, sp, #4\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0022df64, 24)
extern "C" __attribute__((naked)) void script_vm_func_0022df64() {
    asm volatile(
        "mov r0, #0\n"
        ".L_script_vm_func_0022df64_0022df68:\n"
        "add r0, r0, #1\n"
        "cmp r0, #0x10\n"
        "blt .L_script_vm_func_0022df64_0022df68\n"
        "mov r0, #0\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002a8898, 24)
extern "C" __attribute__((naked)) void engine_func_002a8898() {
    asm volatile(
        "push {r4, r5}\n"
        "ldr r4, [sp, #8]\n"
        "ldr r5, [sp, #0xc]\n"
        "svc #0x22\n"
        "pop {r4, r5}\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002b5a04, 24)
extern "C" __attribute__((naked)) void nn_sdk_func_002b5a04() {
    asm volatile(
        "str r0, [sp, #-4]!\n"
        "svc #0x17\n"
        "ldr r2, [sp]\n"
        "str r1, [r2]\n"
        "add sp, sp, #4\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002c5450, 24)
extern "C" __attribute__((naked)) void engine_func_002c5450() {
    asm volatile(
        "str r0, [sp, #-4]!\n"
        "svc #0x16\n"
        "ldr r2, [sp]\n"
        "str r1, [r2]\n"
        "add sp, sp, #4\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002c54d8, 24)
extern "C" __attribute__((naked)) void engine_func_002c54d8() {
    asm volatile(
        "str r0, [sp, #-4]!\n"
        "svc #0x15\n"
        "ldr r2, [sp]\n"
        "str r1, [r2]\n"
        "add sp, sp, #4\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0015f748, 28)
extern "C" __attribute__((naked)) void func_0015f748() {
    asm volatile(
        "str r0, [sp, #-4]!\n"
        "ldr r0, [sp, #4]\n"
        "svc #0x1e\n"
        "ldr r2, [sp]\n"
        "str r1, [r2]\n"
        "add sp, sp, #4\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003e6054, 28)
extern "C" __attribute__((naked)) void func_003e6054() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r0, [r0, #0x260]\n"
        "ldr r1, [r0]\n"
        "ldr r1, [r1, #0x14]\n"
        "blx r1\n"
        "vldr s0, [r0, #8]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003e6070, 28)
extern "C" __attribute__((naked)) void func_003e6070() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r0, [r0, #0x260]\n"
        "ldr r1, [r0]\n"
        "ldr r1, [r1, #0x14]\n"
        "blx r1\n"
        "vldr s0, [r0, #4]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003e8858, 32)
extern "C" __attribute__((naked)) void func_003e8858() {
    asm volatile(
        "ldr r2, [r0, #0x14]!\n"
        "cmp r2, r1\n"
        "movls r0, #0\n"
        "bls .L_func_003e8858_003e8874\n"
        "add r1, r0, r1, lsl #3\n"
        "ldr r1, [r1, #8]\n"
        "add r0, r0, r1\n"
        ".L_func_003e8858_003e8874:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0012409c, 36)
extern "C" __attribute__((naked)) void nn_sdk_func_0012409c() {
    asm volatile(
        "push {r0, r4}\n"
        "ldr r0, [sp, #8]\n"
        "ldr r4, [sp, #0xc]\n"
        "svc #8\n"
        "ldr r2, [sp]\n"
        "str r1, [r2]\n"
        "add sp, sp, #4\n"
        "pop {r4}\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002273f0, 36)
extern "C" __attribute__((naked)) void engine_func_002273f0() {
    asm volatile(
        "ldrsh r1, [r0, #0x10]\n"
        "cmn r1, #1\n"
        "beq .L_engine_func_002273f0_0022740c\n"
        "ldrsh r0, [r0, #0x12]\n"
        "cmp r1, r0\n"
        "movle r0, #1\n"
        "ble .L_engine_func_002273f0_00227410\n"
        ".L_engine_func_002273f0_0022740c:\n"
        "mov r0, #0\n"
        ".L_engine_func_002273f0_00227410:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002bbb04, 36)
extern "C" __attribute__((naked)) void func_002bbb04() {
    asm volatile(
        "push {r0, r4}\n"
        "ldr r0, [sp, #8]\n"
        "ldr r4, [sp, #0xc]\n"
        "svc #1\n"
        "ldr r2, [sp]\n"
        "str r1, [r2]\n"
        "add sp, sp, #4\n"
        "pop {r4}\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00139c9c, 40)
extern "C" __attribute__((naked)) void func_00139c9c() {
    asm volatile(
        "push {r4, lr}\n"
        "mrc p15, #0, r4, c13, c0, #3\n"
        "mov r1, #0x120000\n"
        "str r1, [r4, #0x80]!\n"
        "ldr r0, [r0]\n"
        "svc #0x32\n"
        "and r1, r0, #0x80000000\n"
        "cmp r1, #0\n"
        "ldrge r0, [r4, #4]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0013aec8, 40)
extern "C" __attribute__((naked)) void func_0013aec8() {
    asm volatile(
        "push {r4, lr}\n"
        "mrc p15, #0, r4, c13, c0, #3\n"
        "mov r1, #0x170000\n"
        "str r1, [r4, #0x80]!\n"
        "ldr r0, [r0]\n"
        "svc #0x32\n"
        "and r1, r0, #0x80000000\n"
        "cmp r1, #0\n"
        "ldrge r0, [r4, #4]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0013af50, 40)
extern "C" __attribute__((naked)) void func_0013af50() {
    asm volatile(
        "push {r4, lr}\n"
        "mrc p15, #0, r4, c13, c0, #3\n"
        "mov r1, #0x140000\n"
        "str r1, [r4, #0x80]!\n"
        "ldr r0, [r0]\n"
        "svc #0x32\n"
        "and r1, r0, #0x80000000\n"
        "cmp r1, #0\n"
        "ldrge r0, [r4, #4]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00147c48, 40)
extern "C" __attribute__((naked)) void func_00147c48() {
    asm volatile(
        "push {r4, lr}\n"
        "mrc p15, #0, r4, c13, c0, #3\n"
        "mov r1, #0x190000\n"
        "str r1, [r4, #0x80]!\n"
        "ldr r0, [r0]\n"
        "svc #0x32\n"
        "and r1, r0, #0x80000000\n"
        "cmp r1, #0\n"
        "ldrge r0, [r4, #4]\n"
        "pop {r4, pc}\n"
    );
}
