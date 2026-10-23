#include "types.h"

// DECOMP_FUNC(0x00147c70, 40)
extern "C" __attribute__((naked)) void func_00147c70() {
    asm volatile(
        "push {r4, lr}\n"
        "mrc p15, #0, r4, c13, c0, #3\n"
        "mov r1, #0x1a0000\n"
        "str r1, [r4, #0x80]!\n"
        "ldr r0, [r0]\n"
        "svc #0x32\n"
        "and r1, r0, #0x80000000\n"
        "cmp r1, #0\n"
        "ldrge r0, [r4, #4]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00153918, 40)
extern "C" __attribute__((naked)) void func_00153918() {
    asm volatile(
        "push {r4, lr}\n"
        "mrc p15, #0, r4, c13, c0, #3\n"
        "mov r1, #0xc0000\n"
        "str r1, [r4, #0x80]!\n"
        "ldr r0, [r0]\n"
        "svc #0x32\n"
        "and r1, r0, #0x80000000\n"
        "cmp r1, #0\n"
        "ldrge r0, [r4, #4]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002377e4, 40)
extern "C" __attribute__((naked)) void func_002377e4() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0, #4]\n"
        "ldr r1, [r4, #0x148]\n"
        "ldr r2, [r0]\n"
        "ldr r2, [r2, #0xc]\n"
        "blx r2\n"
        "mov r0, #0\n"
        "str r0, [r4, #0x148]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00246a4c, 40)
extern "C" __attribute__((naked)) void engine_func_00246a4c() {
    asm volatile(
        "ldr r0, [r0, #0x8c]\n"
        "cmp r0, #0\n"
        "beq .Lbatch15b_246a6c\n"
        ".Lbatch15b_246a58:\n"
        "subs r1, r1, #1\n"
        "blo .Lbatch15b_246a70\n"
        "ldr r0, [r0, #0xac]\n"
        "cmp r0, #0\n"
        "bne .Lbatch15b_246a58\n"
        ".Lbatch15b_246a6c:\n"
        "mov r0, #0\n"
        ".Lbatch15b_246a70:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00289ac0, 40)
extern "C" __attribute__((naked)) void script_vm_func_00289ac0() {
    asm volatile(
        "cmp r1, #0\n"
        "blt .Lbatch15b_289ae0\n"
        "ldr r2, [r0, #0xb0]\n"
        "ldr r2, [r2, #8]\n"
        "cmp r1, r2\n"
        "ldrlt r0, [r0, #0xb4]\n"
        "addlt r0, r0, r1, lsl #5\n"
        "blt .Lbatch15b_289ae4\n"
        ".Lbatch15b_289ae0:\n"
        "mov r0, #0\n"
        ".Lbatch15b_289ae4:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0028d58c, 40)
extern "C" __attribute__((naked)) void camp_func_0028d58c() {
    asm volatile(
        "cmp r1, #0\n"
        "blt .Lbatch15b_28d5ac\n"
        "ldrsh r2, [r0, #0xb4]\n"
        "sub r2, r2, #1\n"
        "cmp r1, r2\n"
        "addle r0, r0, r1, lsl #1\n"
        "ldrhle r0, [r0, #0x8c]\n"
        "ble .Lbatch15b_28d5b0\n"
        ".Lbatch15b_28d5ac:\n"
        "mov r0, #0\n"
        ".Lbatch15b_28d5b0:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0029bdb4, 40)
extern "C" __attribute__((naked)) void ui_func_0029bdb4() {
    asm volatile(
        "ldr r1, [r0, #0x34]\n"
        "vstr s0, [r0, #0x78]\n"
        "cmp r1, #0\n"
        "ble .Lbatch15b_29bdd8\n"
        "vldr s1, [r0, #0x74]\n"
        "ldr r0, [r0, #0x4c]\n"
        "vmul.f32 s0, s1, s0\n"
        "cmp r0, #0\n"
        "vstrne s0, [r0, #0x40]\n"
        ".Lbatch15b_29bdd8:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002cba20, 40)
extern "C" __attribute__((naked)) void ui_func_002cba20() {
    asm volatile(
        "cmp r1, #0\n"
        "ldrge r3, [r0, #0x28]\n"
        "cmpge r3, r1\n"
        "ble .Lbatch15b_2cba44\n"
        "add r1, r0, #0x84\n"
        "ldr r0, [r0, #0x8c]\n"
        "ldm r1, {r1, r3}\n"
        "str r0, [r2, #8]\n"
        "stm r2, {r1, r3}\n"
        ".Lbatch15b_2cba44:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00356524, 40)
extern "C" __attribute__((naked)) void func_00356524() {
    asm volatile(
        "push {r4, lr}\n"
        "add r4, r0, #4\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "beq .Lbatch15b_356544\n"
        "svc #0x23\n"
        "mov r0, #0\n"
        "str r0, [r4]\n"
        ".Lbatch15b_356544:\n"
        "sub r0, r4, #4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003566d0, 40)
extern "C" __attribute__((naked)) void func_003566d0() {
    asm volatile(
        "push {r4, lr}\n"
        "add r4, r0, #4\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "beq .Lbatch15b_3566f0\n"
        "svc #0x23\n"
        "mov r0, #0\n"
        "str r0, [r4]\n"
        ".Lbatch15b_3566f0:\n"
        "sub r0, r4, #4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003578e8, 40)
extern "C" __attribute__((naked)) void func_003578e8() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "beq .Lbatch15b_357908\n"
        "svc #0x23\n"
        "mov r0, #0\n"
        "str r0, [r4]\n"
        ".Lbatch15b_357908:\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00357910, 40)
extern "C" __attribute__((naked)) void func_00357910() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "beq .Lbatch15b_357930\n"
        "svc #0x23\n"
        "mov r0, #0\n"
        "str r0, [r4]\n"
        ".Lbatch15b_357930:\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00357964, 40)
extern "C" __attribute__((naked)) void func_00357964() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "beq .Lbatch15b_357984\n"
        "svc #0x23\n"
        "mov r0, #0\n"
        "str r0, [r4]\n"
        ".Lbatch15b_357984:\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00155748, 44)
extern "C" __attribute__((naked)) void func_00155748() {
    asm volatile(
        "ldr r2, [r0, #0x34]\n"
        "bic r1, r1, #0xff000000\n"
        "add r0, r0, r2\n"
        "ldr r2, [r0]\n"
        "cmp r2, r1\n"
        "movls r0, #0\n"
        "bls .Lbatch15b_155770\n"
        "add r1, r0, r1, lsl #3\n"
        "ldr r1, [r1, #8]\n"
        "add r0, r0, r1\n"
        ".Lbatch15b_155770:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00379ee0, 44)
extern "C" __attribute__((naked)) void func_00379ee0() {
    asm volatile(
        "ldr r2, [r0, #0x14]\n"
        "ldr r3, [r0, #0x10]\n"
        "add r1, r1, r2\n"
        "cmp r3, r1\n"
        "movlo r0, #0\n"
        "blo .Lbatch15b_379f08\n"
        "add r1, r1, #0x1f\n"
        "bic r1, r1, #0x1f\n"
        "str r1, [r0, #0x14]\n"
        "mov r0, r2\n"
        ".Lbatch15b_379f08:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003e62fc, 44)
extern "C" __attribute__((naked)) void func_003e62fc() {
    asm volatile(
        "ldr r0, [r0, #0x218]\n"
        "cmp r0, #0\n"
        "beq .Lbatch15b_3e6324\n"
        "ldr r2, [r0]\n"
        "cmp r2, r1\n"
        "movls r0, #0\n"
        "bls .Lbatch15b_3e6324\n"
        "mov r2, #4\n"
        "add r1, r2, r1, lsl #2\n"
        "ldr r0, [r0, r1]\n"
        ".Lbatch15b_3e6324:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003eaf14, 44)
extern "C" __attribute__((naked)) void func_003eaf14() {
    asm volatile(
        "ldr r0, [r0, #0x20c]\n"
        "cmp r0, #0\n"
        "beq .Lbatch15b_3eaf3c\n"
        "ldr r2, [r0]\n"
        "cmp r2, r1\n"
        "movls r0, #0\n"
        "bls .Lbatch15b_3eaf3c\n"
        "mov r2, #4\n"
        "add r1, r2, r1, lsl #2\n"
        "ldr r0, [r0, r1]\n"
        ".Lbatch15b_3eaf3c:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0014cf00, 48)
extern "C" __attribute__((naked)) void ui_func_0014cf00() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r0, [r0, #0x258]\n"
        "ldr r1, [r0]\n"
        "ldr r1, [r1, #0x14]\n"
        "blx r1\n"
        "cmp r0, #0\n"
        "beq .Lbatch15b_14cf28\n"
        "ldr r1, [r0]\n"
        "tst r1, #0x40000000\n"
        "moveq r0, #0\n"
        ".Lbatch15b_14cf28:\n"
        "add r0, r0, #0x14\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0014cfa4, 48)
extern "C" __attribute__((naked)) void ui_func_0014cfa4() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r0, [r0, #0x258]\n"
        "ldr r1, [r0]\n"
        "ldr r1, [r1, #0x14]\n"
        "blx r1\n"
        "cmp r0, #0\n"
        "beq .Lbatch15b_14cfcc\n"
        "ldr r1, [r0]\n"
        "tst r1, #0x80000000\n"
        "moveq r0, #0\n"
        ".Lbatch15b_14cfcc:\n"
        "vldr s0, [r0, #0x14]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002a8948, 48)
extern "C" __attribute__((naked)) void engine_func_002a8948() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r0, [r0, #0x258]\n"
        "ldr r1, [r0]\n"
        "ldr r1, [r1, #0x14]\n"
        "blx r1\n"
        "cmp r0, #0\n"
        "beq .Lbatch15b_2a8970\n"
        "ldr r1, [r0]\n"
        "tst r1, #0x20000000\n"
        "moveq r0, #0\n"
        ".Lbatch15b_2a8970:\n"
        "add r0, r0, #8\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0037f8e0, 48)
extern "C" __attribute__((naked)) void func_0037f8e0() {
    asm volatile(
        "mov ip, r0\n"
        "push {r4, r5}\n"
        "ldr r0, [r0, #0x7c]\n"
        "mov r5, r1\n"
        "mov r3, r2\n"
        "mov r2, r5\n"
        "ldr r1, [r0]\n"
        "ldr r4, [r1, #8]\n"
        "mov r1, ip\n"
        "mov ip, r4\n"
        "pop {r4, r5}\n"
        "bx ip\n"
    );
}

// DECOMP_FUNC(0x003da2e8, 48)
extern "C" __attribute__((naked)) void func_003da2e8() {
    asm volatile(
        "push {r4, lr}\n"
        "add r4, r0, #0x1c00\n"
        "add r4, r4, #0xf8\n"
        "ldr r0, [r4]\n"
        "cmp r0, #0\n"
        "beq .Lbatch15b_3da314\n"
        "ldr r1, [r0]\n"
        "ldr r1, [r1, #4]\n"
        "blx r1\n"
        "mov r0, #0\n"
        "str r0, [r4]\n"
        ".Lbatch15b_3da314:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003decdc, 48)
extern "C" __attribute__((naked)) void camp_func_003decdc() {
    asm volatile(
        "ldr r2, [r0, #0x10]\n"
        "cmp r2, #0\n"
        "ldrhne r2, [r2, #0xe]\n"
        "cmpne r2, r1\n"
        "movle r0, #0\n"
        "ble .Lbatch15b_3ded08\n"
        "ldrd r2, r3, [r0, #0x20]\n"
        "add r0, r3, r1, lsl #2\n"
        "ldrh r0, [r0]\n"
        "add r0, r0, r0, lsl #1\n"
        "ldr r0, [r2, r0, lsl #3]\n"
        ".Lbatch15b_3ded08:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x001468b0, 52)
extern "C" __attribute__((naked)) void func_001468b0() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r1\n"
        "mrc p15, #0, r4, c13, c0, #3\n"
        "mov r1, #0x160000\n"
        "str r1, [r4, #0x80]!\n"
        "ldr r0, [r0]\n"
        "svc #0x32\n"
        "ands r1, r0, #0x80000000\n"
        "bmi .Lbatch15b_1468e0\n"
        "ldr r0, [r4, #0xc]\n"
        "str r0, [r5]\n"
        "ldr r0, [r4, #4]\n"
        ".Lbatch15b_1468e0:\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0014d04c, 52)
extern "C" __attribute__((naked)) void func_0014d04c() {
    asm volatile(
        "ldr r2, [r0, #0xc]\n"
        "add r0, r0, r2\n"
        "ldr r2, [r0]\n"
        "cmp r2, r1\n"
        "bls .Lbatch15b_14d078\n"
        "add r1, r0, r1, lsl #3\n"
        "ldrh r2, [r1, #4]\n"
        "cmp r2, #0x4900\n"
        "ldreq r1, [r1, #8]\n"
        "addeq r0, r0, r1\n"
        "beq .Lbatch15b_14d07c\n"
        ".Lbatch15b_14d078:\n"
        "mov r0, #0\n"
        ".Lbatch15b_14d07c:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002197d8, 52)
extern "C" __attribute__((naked)) void func_002197d8() {
    asm volatile(
        "ldr r0, [r0, #0x24]\n"
        "add r0, r0, #0xc0\n"
        "ldr r1, [r0, #0xc]\n"
        "tst r1, #0xff000000\n"
        "beq .Lbatch15b_219808\n"
        "ldr r1, [r0]\n"
        "mov r0, #0\n"
        "cmp r1, #0\n"
        "ble .Lbatch15b_219808\n"
        ".Lbatch15b_2197fc:\n"
        "add r0, r0, #1\n"
        "cmp r1, r0\n"
        "bgt .Lbatch15b_2197fc\n"
        ".Lbatch15b_219808:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0022c198, 52)
extern "C" __attribute__((naked)) void func_0022c198() {
    asm volatile(
        "cmp r1, #8\n"
        "movlo r0, #0x10\n"
        "blo .Lbatch15b_22c1c8\n"
        "cmp r1, #0x400\n"
        "addhs r0, r1, #0x300\n"
        "addhs r0, r0, #0xff\n"
        "lsrhs r0, r0, #0xa\n"
        "lslhs r0, r0, #0xa\n"
        "bhs .Lbatch15b_22c1c8\n"
        "cmp r1, r0, lsl #1\n"
        "lsllo r0, r0, #1\n"
        "movhs r0, r1\n"
        ".Lbatch15b_22c1c8:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00238308, 52)
extern "C" __attribute__((naked)) void func_00238308() {
    asm volatile(
        "ldr r3, [r0, #4]\n"
        "sub r3, r1, r3\n"
        "ldr r1, [r0]\n"
        "lsr r0, r3, #4\n"
        "add r2, r2, r0\n"
        "cmp r2, r0\n"
        "movhi r3, #0\n"
        "bls .Lbatch15b_238338\n"
        ".Lbatch15b_238328:\n"
        "strb r3, [r1, r0]\n"
        "add r0, r0, #1\n"
        "cmp r2, r0\n"
        "bhi .Lbatch15b_238328\n"
        ".Lbatch15b_238338:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002e6f00, 52)
extern "C" __attribute__((naked)) void func_002e6f00() {
    asm volatile(
        "ldr r0, [r0, #0x24]\n"
        "add r0, r0, #0xc0\n"
        "ldr r1, [r0, #0xc]\n"
        "tst r1, #0xff000000\n"
        "beq .Lbatch15b_2e6f30\n"
        "ldr r1, [r0]\n"
        "mov r0, #0\n"
        "cmp r1, #0\n"
        "ble .Lbatch15b_2e6f30\n"
        ".Lbatch15b_2e6f24:\n"
        "add r0, r0, #1\n"
        "cmp r1, r0\n"
        "bgt .Lbatch15b_2e6f24\n"
        ".Lbatch15b_2e6f30:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002f2a28, 52)
extern "C" __attribute__((naked)) void func_002f2a28() {
    asm volatile(
        "ldr r0, [r0, #0x24]\n"
        "add r0, r0, #0xc0\n"
        "ldr r1, [r0, #0xc]\n"
        "tst r1, #0xff000000\n"
        "beq .Lbatch15b_2f2a58\n"
        "ldr r1, [r0]\n"
        "mov r0, #0\n"
        "cmp r1, #0\n"
        "ble .Lbatch15b_2f2a58\n"
        ".Lbatch15b_2f2a4c:\n"
        "add r0, r0, #1\n"
        "cmp r1, r0\n"
        "bgt .Lbatch15b_2f2a4c\n"
        ".Lbatch15b_2f2a58:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0034fba4, 52)
extern "C" __attribute__((naked)) void func_0034fba4() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r1\n"
        "ldr r0, [r2]\n"
        "mov r4, r2\n"
        "ldr r1, [r0]\n"
        "mov r0, r2\n"
        "blx r1\n"
        "ldr r0, [r5]\n"
        "mov r1, r4\n"
        "ldr r2, [r0, #4]\n"
        "mov r0, r5\n"
        "pop {r4, r5, r6, lr}\n"
        "bx r2\n"
    );
}

// DECOMP_FUNC(0x0034fbe0, 52)
extern "C" __attribute__((naked)) void func_0034fbe0() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r1\n"
        "ldr r0, [r2]\n"
        "mov r4, r2\n"
        "ldr r1, [r0]\n"
        "mov r0, r2\n"
        "blx r1\n"
        "ldr r0, [r5]\n"
        "mov r1, r4\n"
        "ldr r2, [r0, #4]\n"
        "mov r0, r5\n"
        "pop {r4, r5, r6, lr}\n"
        "bx r2\n"
    );
}

// DECOMP_FUNC(0x00361bf0, 52)
extern "C" __attribute__((naked)) void func_00361bf0() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldrd r0, r1, [r4]\n"
        "cmp r0, #0\n"
        "str r1, [r4, #8]\n"
        "ldrne r1, [r4, #4]\n"
        "cmpne r1, #0\n"
        "beq .Lbatch15b_361c1c\n"
        "ldr r2, [r0]\n"
        "ldr r2, [r2, #0xc]\n"
        "blx r2\n"
        ".Lbatch15b_361c1c:\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}
