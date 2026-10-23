#include "types.h"

// Literal-pool words following each unconditional return are kept in place.
// DECOMP_FUNC(0x002003f8, 24)
extern "C" __attribute__((naked)) void camp_func_002003f8() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bx lr\n"
        ".word 0x0043db10\n"
    );
}
// DECOMP_FUNC(0x00200860, 28)
extern "C" __attribute__((naked)) void func_00200860() {
    asm volatile(
        "ldr r1, [pc, #0x10]\n"
        "mov r2, #3\n"
        "ldr r1, [r1]\n"
        "str r2, [r1, #0x14]\n"
        "strh r0, [r1, #0x18]\n"
        "bx lr\n"
        ".word 0x0043e0f8\n"
    );
}

// DECOMP_FUNC(0x00200b1c, 28)
extern "C" __attribute__((naked)) void func_00200b1c() {
    asm volatile(
        "cmp r0, #0xe\n"
        "movge r0, #0\n"
        "ldr r1, [pc, #8]\n"
        "add r0, r0, r0, lsl #1\n"
        "add r0, r1, r0, lsl #4\n"
        "bx lr\n"
        ".word 0x00433a70\n"
    );
}

// DECOMP_FUNC(0x002013d4, 20)
extern "C" __attribute__((naked)) void camp_func_002013d4() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "ldr r1, [r1]\n"
        "strb r0, [r1, #0x25]\n"
        "bx lr\n"
        ".word 0x0043e278\n"
    );
}

// DECOMP_FUNC(0x00201440, 24)
extern "C" __attribute__((naked)) void script_vm_func_00201440() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "ldr r0, [r0, #0x670]\n"
        "sxth r0, r0\n"
        "bx lr\n"
        ".word 0x0043dcb0\n"
    );
}

// DECOMP_FUNC(0x00201458, 20)
extern "C" __attribute__((naked)) void script_vm_func_00201458() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #0x10]\n"
        "bx lr\n"
        ".word 0x0043e128\n"
    );
}

// DECOMP_FUNC(0x0020146c, 20)
extern "C" __attribute__((naked)) void script_vm_func_0020146c() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "ldr r1, [r1]\n"
        "str r0, [r1, #0x10]\n"
        "bx lr\n"
        ".word 0x0043e128\n"
    );
}

// DECOMP_FUNC(0x0020194c, 24)
extern "C" __attribute__((naked)) void func_0020194c() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bx lr\n"
        ".word 0x0043dcf0\n"
    );
}

// DECOMP_FUNC(0x00208a70, 20)
extern "C" __attribute__((naked)) void ui_func_00208a70() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "mov r0, #0\n"
        "strb r0, [r1, #0x2f8]\n"
        "bx lr\n"
        ".word 0x0049f91c\n"
    );
}

// DECOMP_FUNC(0x0020ce84, 36)
extern "C" __attribute__((naked)) void script_vm_func_0020ce84() {
    asm volatile(
        "ldr r2, [pc, #0x18]\n"
        "mov r3, #0\n"
        "mov ip, #1\n"
        "ldr r2, [r2]\n"
        "str r3, [r2, #8]\n"
        "str ip, [r2, #4]\n"
        "strd r0, r1, [r2, #0xc]\n"
        "bx lr\n"
        ".word 0x00447600\n"
    );
}

// DECOMP_FUNC(0x0020ced4, 44)
extern "C" __attribute__((naked)) void script_vm_func_0020ced4() {
    asm volatile(
        "ldr r2, [pc, #0x20]\n"
        "mov r3, #0\n"
        "ldr r2, [r2]\n"
        "strh r3, [r2, #0xa]\n"
        "strh r3, [r2, #0xc]\n"
        "strh r0, [r2, #6]\n"
        "strh r1, [r2, #8]\n"
        "str r3, [r2, #0x10]\n"
        "strb r3, [r2, #0x14]\n"
        "bx lr\n"
        ".word 0x00447a48\n"
    );
}

// DECOMP_FUNC(0x0020cf00, 36)
extern "C" __attribute__((naked)) void script_vm_func_0020cf00() {
    asm volatile(
        "ldr r2, [pc, #0x18]\n"
        "mov r3, #0\n"
        "ldr r2, [r2]\n"
        "strh r3, [r2, #8]\n"
        "strh r3, [r2, #0xa]\n"
        "strh r0, [r2, #4]\n"
        "strh r1, [r2, #6]\n"
        "bx lr\n"
        ".word 0x00447a60\n"
    );
}

// DECOMP_FUNC(0x0020e5a4, 24)
extern "C" __attribute__((naked)) void engine_func_0020e5a4() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldr r1, [r1]\n"
        "add r0, r1, r0, lsl #3\n"
        "ldr r0, [r0, #0x780]\n"
        "bx lr\n"
        ".word 0x00448c58\n"
    );
}

// DECOMP_FUNC(0x0020e5bc, 24)
extern "C" __attribute__((naked)) void script_vm_func_0020e5bc() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r1, [r0]\n"
        "mov r0, #1\n"
        "strb r0, [r1, #0xc]\n"
        "bx lr\n"
        ".word 0x0044cda0\n"
    );
}

// DECOMP_FUNC(0x0020fdc8, 24)
extern "C" __attribute__((naked)) void script_vm_func_0020fdc8() {
    asm volatile(
        "cmp r0, #0xb\n"
        "ldrlo r1, [pc, #8]\n"
        "ldrblo r0, [r1, r0]\n"
        "movhs r0, #0x30\n"
        "bx lr\n"
        ".word 0x0040780c\n"
    );
}

// DECOMP_FUNC(0x002107b4, 16)
extern "C" __attribute__((naked)) void func_002107b4() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #0x92]\n"
        "bx lr\n"
        ".word 0x004d4880\n"
    );
}

// DECOMP_FUNC(0x00210f94, 28)
extern "C" __attribute__((naked)) void camp_func_00210f94() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0]\n"
        "ldrb r0, [r0, #0x125]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bx lr\n"
        ".word 0x0043dad0\n"
    );
}

// DECOMP_FUNC(0x00211688, 28)
extern "C" __attribute__((naked)) void camp_func_00211688() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0]\n"
        "ldrb r0, [r0, #0x15c]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bx lr\n"
        ".word 0x0043db10\n"
    );
}

// DECOMP_FUNC(0x0021176c, 32)
extern "C" __attribute__((naked)) void func_0021176c() {
    asm volatile(
        "ldr r2, [pc, #0x14]\n"
        "mov r3, #2\n"
        "ldr r2, [r2]\n"
        "str r3, [r2, #0x14]\n"
        "strh r0, [r2, #0x18]\n"
        "strb r1, [r2, #0x11]\n"
        "bx lr\n"
        ".word 0x0043e0f8\n"
    );
}

// DECOMP_FUNC(0x002117e8, 60)
extern "C" __attribute__((naked)) void func_002117e8() {
    asm volatile(
        "ldr r1, [pc, #0x30]\n"
        "str r4, [sp, #-4]!\n"
        "mov r2, r0\n"
        "mov r4, #3\n"
        "ldr r1, [r1, #8]\n"
        "mov r3, #0\n"
        "mov r0, #1\n"
        "strb r4, [r1, #0x7c]\n"
        "str r2, [r1, #0x70]\n"
        "str r2, [r1, #0x74]\n"
        "strb r3, [r1, #0x81]\n"
        "str r3, [r1, #0x64]\n"
        "pop {r4}\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x00211b44, 40)
extern "C" __attribute__((naked)) void func_00211b44() {
    asm volatile(
        "ldr r1, [pc, #0x1c]\n"
        "ldr r1, [r1]\n"
        "ldrd r2, r3, [r0]\n"
        "ldr r0, [r0, #8]\n"
        "str r0, [r1, #0x510]\n"
        "add r1, r1, #0x400\n"
        "add r1, r1, #0x108\n"
        "stm r1, {r2, r3}\n"
        "bx lr\n"
        ".word 0x00433260\n"
    );
}

// DECOMP_FUNC(0x00211b6c, 40)
extern "C" __attribute__((naked)) void func_00211b6c() {
    asm volatile(
        "ldr r1, [pc, #0x1c]\n"
        "ldr r1, [r1]\n"
        "ldrd r2, r3, [r0]\n"
        "ldr r0, [r0, #8]\n"
        "str r0, [r1, #0x51c]\n"
        "add r1, r1, #0x400\n"
        "add r1, r1, #0x114\n"
        "stm r1, {r2, r3}\n"
        "bx lr\n"
        ".word 0x00433260\n"
    );
}

// DECOMP_FUNC(0x00215918, 16)
extern "C" __attribute__((naked)) void ui_func_00215918() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0]\n"
        "bx lr\n"
        ".word 0x0044de28\n"
    );
}

// DECOMP_FUNC(0x00215928, 16)
extern "C" __attribute__((naked)) void engine_func_00215928() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #1]\n"
        "bx lr\n"
        ".word 0x0044de28\n"
    );
}

// DECOMP_FUNC(0x00215b60, 64)
extern "C" __attribute__((naked)) void func_00215b60() {
    asm volatile(
        "ldr r1, [pc, #0x34]\n"
        "ldr r2, [pc, #0x30]\n"
        "ldr r1, [r1, #4]\n"
        "ldr r2, [r2, #4]\n"
        "add r1, r1, #0x9000\n"
        "add r1, r1, #0x870\n"
        "add r3, r2, #0x8c\n"
        "ldr r2, [r1]\n"
        "add r1, r3, #0x9400\n"
        "add r1, r1, #0x3e4\n"
        "cmp r2, r0\n"
        "movlo r0, #0\n"
        "subhs r0, r2, r0\n"
        "str r0, [r1]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x00215ba0, 32)
extern "C" __attribute__((naked)) void script_vm_func_00215ba0() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0043dd50\n"
    );
}

// DECOMP_FUNC(0x00215bc0, 24)
extern "C" __attribute__((naked)) void camp_func_00215bc0() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0x500\n"
        "ldrsb r0, [r0, #0xc5]\n"
        "bx lr\n"
        ".word 0x0043dd50\n"
    );
}

// DECOMP_FUNC(0x002168b4, 28)
extern "C" __attribute__((naked)) void ui_func_002168b4() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0044dc50\n"
    );
}

// DECOMP_FUNC(0x0021e668, 24)
extern "C" __attribute__((naked)) void script_vm_func_0021e668() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r1, [r0]\n"
        "mov r0, #0\n"
        "str r0, [r1, #0x6d4]\n"
        "bx lr\n"
        ".word 0x00447e70\n"
    );
}

// DECOMP_FUNC(0x0021f3f8, 24)
extern "C" __attribute__((naked)) void script_vm_func_0021f3f8() {
    asm volatile(
        "cmp r0, #0xb\n"
        "ldrlo r1, [pc, #8]\n"
        "ldrblo r0, [r1, r0]\n"
        "movhs r0, #0x50\n"
        "bx lr\n"
        ".word 0x00407801\n"
    );
}

// DECOMP_FUNC(0x00220bf8, 24)
extern "C" __attribute__((naked)) void func_00220bf8() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x400\n"
        "ldrsb r0, [r0, #0xc5]\n"
        "bx lr\n"
        ".word 0x0043da28\n"
    );
}

// DECOMP_FUNC(0x00220c10, 24)
extern "C" __attribute__((naked)) void camp_func_00220c10() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x500\n"
        "ldrsb r0, [r0, #0x5c]\n"
        "bx lr\n"
        ".word 0x0043da28\n"
    );
}

// DECOMP_FUNC(0x00220c28, 20)
extern "C" __attribute__((naked)) void ui_func_00220c28() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "ldr r1, [r1, #4]\n"
        "strb r0, [r1, #0x55c]\n"
        "bx lr\n"
        ".word 0x0043da28\n"
    );
}

// DECOMP_FUNC(0x00221678, 72)
extern "C" __attribute__((naked)) void func_00221678() {
    asm volatile(
        "ldr r1, [pc, #0x38]\n"
        "ldr r3, [pc, #0x38]\n"
        "mov r0, #0\n"
        "str r0, [r1, #0x60]\n"
        "str r0, [r1, #0x64]\n"
        "str r0, [r1, #0x68]\n"
        "ldr r1, [r3, #0x10]\n"
        "add r2, r3, #0x70\n"
        "orr r1, r1, #0x10\n"
        "str r1, [r3, #0x10]\n"
        "ldr r1, [r2, #0x10]\n"
        "orr r1, r1, #0x10\n"
        "str r1, [r2, #0x10]\n"
        "str r0, [r3, #0xc]\n"
        "str r0, [r2, #0xc]\n"
        "bx lr\n"
        ".word 0x0044ea80\n"
        ".word 0x0044fd88\n"
    );
}

// DECOMP_FUNC(0x00221a60, 24)
extern "C" __attribute__((naked)) void func_00221a60() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0x400\n"
        "vstr s0, [r0, #0x120]\n"
        "bx lr\n"
        ".word 0x00433260\n"
    );
}

// DECOMP_FUNC(0x002227dc, 32)
extern "C" __attribute__((naked)) void camp_func_002227dc() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r1, [pc, #0x10]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x88\n"
        "ldrb r0, [r0, r1]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
        ".word 0x00024b27\n"
    );
}

// DECOMP_FUNC(0x00223a18, 28)
extern "C" __attribute__((naked)) void func_00223a18() {
    asm volatile(
        "ldr r1, [pc, #0x10]\n"
        "ldr r1, [r1, #4]\n"
        "add r1, r1, #0x1f400\n"
        "add r1, r1, #0xdc\n"
        "str r0, [r1]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x00223be8, 24)
extern "C" __attribute__((naked)) void camp_func_00223be8() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0x500\n"
        "ldrsb r0, [r0, #0xc6]\n"
        "bx lr\n"
        ".word 0x0043dd50\n"
    );
}

// DECOMP_FUNC(0x00223fa0, 36)
extern "C" __attribute__((naked)) void func_00223fa0() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0x9500\n"
        "ldrb r0, [r0, #0x6c]\n"
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0043dd68\n"
    );
}

// DECOMP_FUNC(0x00225134, 32)
extern "C" __attribute__((naked)) void camp_func_00225134() {
    asm volatile(
        "add r0, r0, #0x2000\n"
        "ldr r0, [r0, #0x180]\n"
        "cmp r0, #2\n"
        "movne r0, #1\n"
        "moveq r0, #0\n"
        "bx lr\n"
        ".word 0xe3500000\n"
        ".word 0x012fff1e\n"
    );
}

// DECOMP_FUNC(0x002253c8, 24)
extern "C" __attribute__((naked)) void ui_func_002253c8() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bx lr\n"
        ".word 0x00434210\n"
    );
}

// DECOMP_FUNC(0x002253e0, 28)
extern "C" __attribute__((naked)) void camp_func_002253e0() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "addne r0, r0, #0x200\n"
        "ldrsbne r0, [r0, #0xf5]\n"
        "bx lr\n"
        ".word 0x00434210\n"
    );
}

// DECOMP_FUNC(0x00225704, 76)
extern "C" __attribute__((naked)) void func_00225704() {
    asm volatile(
        "vdiv.f32 s6, s4, s5\n"
        "vldr s10, [pc, #0x34]\n"
        "vldr s7, [pc, #0x34]\n"
        "vldr s9, [pc, #0x34]\n"
        "vsub.f32 s8, s0, s2\n"
        "vnmls.f32 s7, s6, s10\n"
        "vsub.f32 s2, s6, s9\n"
        "vmul.f32 s3, s6, s3\n"
        "vmul.f32 s5, s6, s6\n"
        "vmul.f32 s6, s8, s7\n"
        "vmul.f32 s1, s2, s1\n"
        "vmul.f32 s2, s4, s2\n"
        "vmla.f32 s0, s6, s5\n"
        "vadd.f32 s1, s1, s3\n"
        "vmla.f32 s0, s2, s1\n"
        "bx lr\n"
        ".word 0x40000000\n"
        ".word 0x40400000\n"
        ".word 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x00228b14, 28)
extern "C" __attribute__((naked)) void func_00228b14() {
    asm volatile(
        "cmp r1, #0\n"
        "vldrne s1, [pc, #8]\n"
        "vldreq s1, [pc, #8]\n"
        "vmul.f32 s0, s0, s1\n"
        "bx lr\n"
        ".word 0x3fc00000\n"
        ".word 0x3f2aaaab\n"
    );
}

// DECOMP_FUNC(0x00229c68, 60)
extern "C" __attribute__((naked)) void func_00229c68() {
    asm volatile(
        "ldr r1, [r0]\n"
        "ldr ip, [pc, #0x2c]\n"
        "ldr r2, [pc, #0x24]\n"
        "ldr r0, [r1, #0x84]\n"
        "ldr r3, [r1, #0x7c]\n"
        "ldr r1, [r2, #4]\n"
        "mul r0, r0, ip\n"
        "tst r3, #1\n"
        "add r0, r1, r0, lsl #2\n"
        "movne r1, #0xa\n"
        "moveq r1, #0xb\n"
        "strb r1, [r0, #9]\n"
        "bx lr\n"
        ".word 0x00434278\n"
        ".word 0x000003c7\n"
    );
}

// DECOMP_FUNC(0x0022a018, 16)
extern "C" __attribute__((naked)) void camp_func_0022a018() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #0xc]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x0022af18, 24)
extern "C" __attribute__((naked)) void ui_func_0022af18() {
    asm volatile(
        "ldr r2, [pc, #0xc]\n"
        "ldr r2, [r2, #4]\n"
        "cmp r2, #0\n"
        "strdne r0, r1, [r2]\n"
        "bx lr\n"
        ".word 0x00464fa8\n"
    );
}

// DECOMP_FUNC(0x0022b130, 20)
extern "C" __attribute__((naked)) void engine_func_0022b130() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "ldr r1, [r1]\n"
        "strb r0, [r1, #0x20]\n"
        "bx lr\n"
        ".word 0x0043e128\n"
    );
}

// DECOMP_FUNC(0x0022cb04, 24)
extern "C" __attribute__((naked)) void unite_func_0022cb04() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "add r0, r0, r0, lsl #1\n"
        "ldr r1, [r1]\n"
        "add r0, r1, r0, lsl #3\n"
        "bx lr\n"
        ".word 0x0044ea28\n"
    );
}

// DECOMP_FUNC(0x0022e614, 36)
extern "C" __attribute__((naked)) void engine_func_0022e614() {
    asm volatile(
        "vldr s0, [pc, #0x18]\n"
        "mvn r1, #0\n"
        "vstr s0, [r0]\n"
        "vstr s0, [r0, #4]\n"
        "vstr s0, [r0, #8]\n"
        "vstr s0, [r0, #0xc]\n"
        "str r1, [r0, #0x10]\n"
        "bx lr\n"
        ".word 0x00000000\n"
    );
}

// DECOMP_FUNC(0x0022e7c4, 24)
extern "C" __attribute__((naked)) void func_0022e7c4() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x700\n"
        "ldrsb r0, [r0, #0x4d]\n"
        "bx lr\n"
        ".word 0x0043dd20\n"
    );
}

// DECOMP_FUNC(0x0023077c, 20)
extern "C" __attribute__((naked)) void engine_func_0023077c() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "ldr r1, [r1]\n"
        "strb r0, [r1, #0x10]\n"
        "bx lr\n"
        ".word 0x0043e140\n"
    );
}

// DECOMP_FUNC(0x00230f84, 20)
extern "C" __attribute__((naked)) void shop_func_00230f84() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "ldr r1, [r1, #8]\n"
        "strb r0, [r1, #0x32]\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x00231318, 32)
extern "C" __attribute__((naked)) void func_00231318() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0, #4]\n"
        "ldr r0, [r0, #0x10]\n"
        "cmp r0, #1\n"
        "movne r0, #1\n"
        "moveq r0, #0\n"
        "bx lr\n"
        ".word 0x0043da28\n"
    );
}

// DECOMP_FUNC(0x00231b38, 28)
extern "C" __attribute__((naked)) void func_00231b38() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldm r1, {r1, r2}\n"
        "ldr r0, [r0]\n"
        "str r1, [r0, #0x38]\n"
        "str r2, [r0, #0x3c]\n"
        "bx lr\n"
        ".word 0x0044cdf0\n"
    );
}

// DECOMP_FUNC(0x00231f44, 20)
extern "C" __attribute__((naked)) void func_00231f44() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0]\n"
        "vldr s0, [r0, #0x18]\n"
        "bx lr\n"
        ".word 0x0044cdf0\n"
    );
}

// DECOMP_FUNC(0x00231f58, 20)
extern "C" __attribute__((naked)) void func_00231f58() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0x38\n"
        "bx lr\n"
        ".word 0x0044cdf0\n"
    );
}

// DECOMP_FUNC(0x00231f6c, 20)
extern "C" __attribute__((naked)) void func_00231f6c() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #0xc]\n"
        "bx lr\n"
        ".word 0x0044cdf0\n"
    );
}

// DECOMP_FUNC(0x002327c4, 20)
extern "C" __attribute__((naked)) void func_002327c4() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #0x10]\n"
        "bx lr\n"
        ".word 0x0044cdf0\n"
    );
}

// DECOMP_FUNC(0x002327d8, 20)
extern "C" __attribute__((naked)) void func_002327d8() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #0x28]\n"
        "bx lr\n"
        ".word 0x0044cdf0\n"
    );
}

// DECOMP_FUNC(0x002327ec, 20)
extern "C" __attribute__((naked)) void func_002327ec() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0x1c\n"
        "bx lr\n"
        ".word 0x00447e88\n"
    );
}

// DECOMP_FUNC(0x00232800, 44)
extern "C" __attribute__((naked)) void unite_func_00232800() {
    asm volatile(
        "vmov s2, r2\n"
        "vmov s1, r1\n"
        "vldr s0, [pc, #0x18]\n"
        "str r3, [r0, #0x10]\n"
        "vstr s0, [r0, #8]\n"
        "vstr s0, [r0, #0xc]\n"
        "vcvt.f32.s32 s2, s2\n"
        "vcvt.f32.s32 s1, s1\n"
        "vstmia r0, {s1, s2}\n"
        "bx lr\n"
        ".word 0x00000000\n"
    );
}

// DECOMP_FUNC(0x002333ac, 16)
extern "C" __attribute__((naked)) void func_002333ac() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "vldr s0, [r0, #0x84]\n"
        "bx lr\n"
        ".word 0x004d4680\n"
    );
}

// DECOMP_FUNC(0x002333bc, 24)
extern "C" __attribute__((naked)) void unite_func_002333bc() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "mov r2, #0\n"
        "str r1, [r0]\n"
        "strh r2, [r0, #4]\n"
        "bx lr\n"
        ".word 0x004221e4\n"
    );
}

// DECOMP_FUNC(0x002356d4, 24)
extern "C" __attribute__((naked)) void shop_func_002356d4() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldr r1, [r1, #8]\n"
        "cmp r1, #0\n"
        "strbne r0, [r1, #0x2f]\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x00235744, 20)
extern "C" __attribute__((naked)) void script_vm_func_00235744() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "ldr r1, [r1, #8]\n"
        "strb r0, [r1, #0x33]\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x00235df8, 16)
extern "C" __attribute__((naked)) void func_00235df8() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "str r1, [r0]\n"
        "bx lr\n"
        ".word 0x00421960\n"
    );
}

// DECOMP_FUNC(0x00237a94, 64)
extern "C" __attribute__((naked)) void ui_func_00237a94() {
    asm volatile(
        "vldr s1, [pc, #0x30]\n"
        "ldr r1, [pc, #0x30]\n"
        "vmul.f32 s1, s0, s1\n"
        "vcvt.u32.f32 s0, s1\n"
        "vmov r0, s0\n"
        "uxth r0, r0\n"
        "vmov s0, r0\n"
        "add r0, r1, r0, lsl #3\n"
        "vldr s2, [r0, #4]\n"
        "vcvt.f32.u32 s0, s0\n"
        "vsub.f32 s1, s1, s0\n"
        "vldr s0, [r0]\n"
        "vmla.f32 s0, s1, s2\n"
        "bx lr\n"
        ".word 0x42000000\n"
        ".word 0x0044e6a0\n"
    );
}

// DECOMP_FUNC(0x00239bec, 16)
extern "C" __attribute__((naked)) void engine_func_00239bec() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0]\n"
        "bx lr\n"
        ".word 0x00472a40\n"
    );
}

// DECOMP_FUNC(0x00239bfc, 84)
extern "C" __attribute__((naked)) void func_00239bfc() {
    asm volatile(
        "mov r3, #0xc\n"
        "vldr s0, [pc, #0x44]\n"
        "strb r3, [r0, #8]\n"
        "mov r1, #0\n"
        "vstr s0, [r0, #0x10]\n"
        "str r1, [r0]\n"
        "strh r1, [r0, #4]\n"
        "mov r2, #2\n"
        "strh r1, [r0, #6]\n"
        "strb r2, [r0, #9]\n"
        "strb r2, [r0, #0xa]\n"
        "strb r1, [r0, #0xb]\n"
        "strb r1, [r0, #0xc]\n"
        "strb r1, [r0, #0x14]\n"
        "strb r1, [r0, #0x15]\n"
        "strb r1, [r0, #0x16]\n"
        "strb r1, [r0, #0x17]\n"
        "strb r1, [r0, #0x18]\n"
        "strb r1, [r0, #0x19]\n"
        "bx lr\n"
        ".word 0x00000000\n"
    );
}

// DECOMP_FUNC(0x0023cd20, 60)
extern "C" __attribute__((naked)) void func_0023cd20() {
    asm volatile(
        "add r3, r0, #0x400\n"
        "vldr s1, [pc, #0x2c]\n"
        "vstr s0, [r3, #0x1dc]\n"
        "str r1, [r0, #0x69c]\n"
        "str r2, [r0, #0x6a4]\n"
        "mov ip, #0\n"
        "vstr s1, [r3, #0x298]\n"
        "add r1, r0, #0x400\n"
        "str ip, [r0, #0x6a0]\n"
        "ldr r0, [r0, #0x634]\n"
        "add r1, r1, #0x234\n"
        "orr r0, r0, #0x200\n"
        "str r0, [r1]\n"
        "bx lr\n"
        ".word 0x00000000\n"
    );
}

// DECOMP_FUNC(0x0023d448, 24)
extern "C" __attribute__((naked)) void func_0023d448() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1c400\n"
        "add r0, r0, #0x22c\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x0023ec3c, 56)
extern "C" __attribute__((naked)) void script_vm_func_0023ec3c() {
    asm volatile(
        "ldr r1, [pc, #0x28]\n"
        "ldr r2, [pc, #0x28]\n"
        "add r0, r0, #1\n"
        "ldr r3, [r1]\n"
        "mul r2, r3, r2\n"
        "add r2, r2, #0x3000\n"
        "add r2, r2, #0x39\n"
        "str r2, [r1]\n"
        "lsr r3, r2, #0x10\n"
        "mul r0, r3, r0\n"
        "lsr r0, r0, #0x10\n"
        "bx lr\n"
        ".word 0x00435e48\n"
        ".word 0x41c64e6d\n"
    );
}

// DECOMP_FUNC(0x0023f554, 24)
extern "C" __attribute__((naked)) void battle_func_0023f554() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x9800\n"
        "add r0, r0, #0x1e\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x00241ac0, 32)
extern "C" __attribute__((naked)) void camp_func_00241ac0() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0043dd50\n"
    );
}

// DECOMP_FUNC(0x00241b28, 28)
extern "C" __attribute__((naked)) void camp_func_00241b28() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "ldrne r0, [r0, #0x434]\n"
        "mvneq r0, #0\n"
        "bx lr\n"
        ".word 0x0043dd68\n"
    );
}

// DECOMP_FUNC(0x00241b74, 32)
extern "C" __attribute__((naked)) void camp_func_00241b74() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0, #4]\n"
        "ldrb r0, [r0, #0x1c]\n"
        "cmp r0, #5\n"
        "moveq r0, #0\n"
        "movne r0, #1\n"
        "bx lr\n"
        ".word 0x0043d9e0\n"
    );
}

// DECOMP_FUNC(0x00244f20, 24)
extern "C" __attribute__((naked)) void camp_func_00244f20() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldr r2, [r1, #8]\n"
        "orr r0, r0, r2\n"
        "str r0, [r1, #8]\n"
        "bx lr\n"
        ".word 0x00464af0\n"
    );
}

// DECOMP_FUNC(0x00245394, 80)
extern "C" __attribute__((naked)) void func_00245394() {
    asm volatile(
        "add r0, r0, r1, lsl #2\n"
        "ldr r1, [pc, #0x40]\n"
        "str r4, [sp, #-4]!\n"
        "mov r3, #0\n"
        "add ip, r1, #8\n"
        "str r3, [r1, r0]\n"
        "add r4, r1, #0x10\n"
        "sub r1, r1, #0x18\n"
        "str r3, [ip, r0]\n"
        "str r2, [r4, r0]\n"
        "ldr r2, [r1, r0]\n"
        "add r1, r0, #0x4800\n"
        "add r1, r1, #0x214\n"
        "add r0, r0, #0x4800\n"
        "add r0, r0, #0x21c\n"
        "str r2, [r1]\n"
        "str r3, [r0]\n"
        "pop {r4}\n"
        "bx lr\n"
        ".word 0x00004a24\n"
    );
}

// DECOMP_FUNC(0x00246d40, 84)
extern "C" __attribute__((naked)) void func_00246d40() {
    asm volatile(
        "ldr r0, [pc, #0x48]\n"
        "add r1, r0, #0x110\n"
        "add r0, r0, #0x100\n"
        "vldr s1, [r1]\n"
        "vldr s0, [r0]\n"
        "vmul.f32 s0, s0, s1\n"
        "vstr s0, [r0]\n"
        "vldr s0, [r0, #4]\n"
        "vldr s1, [r1, #4]\n"
        "vmul.f32 s0, s0, s1\n"
        "vstr s0, [r0, #4]\n"
        "vldr s0, [r0, #8]\n"
        "vldr s1, [r1, #8]\n"
        "vmul.f32 s0, s0, s1\n"
        "vstr s0, [r0, #8]\n"
        "vldr s1, [r1, #0xc]\n"
        "vldr s0, [r0, #0xc]\n"
        "vmul.f32 s0, s0, s1\n"
        "vstr s0, [r0, #0xc]\n"
        "bx lr\n"
        ".word 0x004ea81c\n"
    );
}

// DECOMP_FUNC(0x00248728, 28)
extern "C" __attribute__((naked)) void script_vm_func_00248728() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #8]\n"
        "ldrb r0, [r0, #0x7d]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002497d0, 84)
extern "C" __attribute__((naked)) void ui_func_002497d0() {
    asm volatile(
        "ldr r0, [pc, #0x48]\n"
        "add r1, r0, #0x110\n"
        "add r0, r0, #0x100\n"
        "vldr s1, [r1]\n"
        "vldr s0, [r0]\n"
        "vadd.f32 s0, s0, s1\n"
        "vstr s0, [r0]\n"
        "vldr s0, [r0, #4]\n"
        "vldr s1, [r1, #4]\n"
        "vadd.f32 s0, s0, s1\n"
        "vstr s0, [r0, #4]\n"
        "vldr s0, [r0, #8]\n"
        "vldr s1, [r1, #8]\n"
        "vadd.f32 s0, s0, s1\n"
        "vstr s0, [r0, #8]\n"
        "vldr s1, [r1, #0xc]\n"
        "vldr s0, [r0, #0xc]\n"
        "vadd.f32 s0, s0, s1\n"
        "vstr s0, [r0, #0xc]\n"
        "bx lr\n"
        ".word 0x004ea81c\n"
    );
}

// DECOMP_FUNC(0x0024abfc, 20)
extern "C" __attribute__((naked)) void camp_func_0024abfc() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0xa0\n"
        "bx lr\n"
        ".word 0x0043daa8\n"
    );
}

// DECOMP_FUNC(0x0024ae60, 28)
extern "C" __attribute__((naked)) void ui_func_0024ae60() {
    asm volatile(
        "ldr r1, [pc, #0x10]\n"
        "cmp r0, #2\n"
        "ldr r0, [r1, #4]\n"
        "ldreq r0, [r0, #0x84]\n"
        "ldrne r0, [r0, #0x80]\n"
        "bx lr\n"
        ".word 0x0044ea58\n"
    );
}

// DECOMP_FUNC(0x0024ae7c, 20)
extern "C" __attribute__((naked)) void func_0024ae7c() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "ldr r1, [r1]\n"
        "strb r0, [r1, #0xedc]\n"
        "bx lr\n"
        ".word 0x0043e278\n"
    );
}

// DECOMP_FUNC(0x0024ae90, 20)
extern "C" __attribute__((naked)) void func_0024ae90() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "ldr r1, [r1]\n"
        "strb r0, [r1, #0xe8c]\n"
        "bx lr\n"
        ".word 0x0043e278\n"
    );
}

// DECOMP_FUNC(0x0024b990, 64)
extern "C" __attribute__((naked)) void engine_func_0024b990() {
    asm volatile(
        "cmp r0, #0\n"
        "ldreq r0, [pc, #0x30]\n"
        "str r4, [sp, #-4]!\n"
        "ldm r0, {r1, r2, r3, ip}\n"
        "str r1, [r0, #4]\n"
        "lsl r4, r2, #2\n"
        "lsl ip, ip, #1\n"
        "orr r1, r4, r1, lsr #30\n"
        "orr ip, ip, r3, lsr #31\n"
        "eor r1, r1, ip\n"
        "str r1, [r0]\n"
        "strd r2, r3, [r0, #8]\n"
        "pop {r4}\n"
        "mov r0, r1\n"
        "bx lr\n"
        ".word 0x004d9748\n"
    );
}

// DECOMP_FUNC(0x0024bd24, 40)
extern "C" __attribute__((naked)) void engine_func_0024bd24() {
    asm volatile(
        "ldr r2, [pc, #0x1c]\n"
        "add r0, r0, r0, lsl #1\n"
        "mov r1, #0\n"
        "ldr r2, [r2]\n"
        "ldr r0, [r2, r0, lsl #3]\n"
        "cmp r0, #0\n"
        "movne r1, #1\n"
        "mov r0, r1\n"
        "bx lr\n"
        ".word 0x0044ea28\n"
    );
}

// DECOMP_FUNC(0x0024c5dc, 16)
extern "C" __attribute__((naked)) void engine_func_0024c5dc() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "ldr r0, [r1, r0, lsl #2]\n"
        "bx lr\n"
        ".word 0x004d96f0\n"
    );
}

// DECOMP_FUNC(0x0024df00, 16)
extern "C" __attribute__((naked)) void battle_func_0024df00() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "str r0, [r1]\n"
        "bx lr\n"
        ".word 0x00433d10\n"
    );
}

// DECOMP_FUNC(0x0024df94, 16)
extern "C" __attribute__((naked)) void ui_func_0024df94() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "ldrb r0, [r1, r0]\n"
        "bx lr\n"
        ".word 0x00409ab8\n"
    );
}

// DECOMP_FUNC(0x0024f1f8, 24)
extern "C" __attribute__((naked)) void func_0024f1f8() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "ldrsbne r0, [r0, #0xc]\n"
        "bx lr\n"
        ".word 0x0043e278\n"
    );
}

// DECOMP_FUNC(0x002526bc, 64)
extern "C" __attribute__((naked)) void engine_func_002526bc() {
    asm volatile(
        "vsub.f32 s3, s3, s0\n"
        "vsub.f32 s0, s4, s1\n"
        "vsub.f32 s1, s5, s2\n"
        "vldr s4, [pc, #0x28]\n"
        "vmul.f32 s2, s3, s3\n"
        "vmla.f32 s2, s0, s0\n"
        "vmla.f32 s2, s1, s1\n"
        "vsqrt.f32 s5, s2\n"
        "vdiv.f32 s2, s4, s5\n"
        "vmul.f32 s3, s3, s2\n"
        "vmul.f32 s1, s1, s2\n"
        "vmul.f32 s0, s0, s2\n"
        "vstmia r0!, {s3}\n"
        "vstmia r0, {s0, s1}\n"
        "bx lr\n"
        ".word 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x00254228, 32)
extern "C" __attribute__((naked)) void camp_func_00254228() {
    asm volatile(
        "ldr ip, [pc, #0x14]\n"
        "ldr ip, [ip, #4]\n"
        "str r0, [ip, #0x550]\n"
        "strb r1, [ip, #0x554]\n"
        "strb r2, [ip, #0x555]\n"
        "strb r3, [ip, #0x556]\n"
        "bx lr\n"
        ".word 0x0043da28\n"
    );
}

// DECOMP_FUNC(0x00254248, 80)
extern "C" __attribute__((naked)) void script_vm_func_00254248() {
    asm volatile(
        "ldrsh r3, [r0, #4]\n"
        "ldr r2, [pc, #0x40]\n"
        "mov r1, r0\n"
        "mov r0, #1\n"
        "cmp r3, r2\n"
        "ldrsh r3, [r1, #6]\n"
        "movlt r0, #0\n"
        "cmp r3, r2\n"
        "ldrsh r3, [r1, #8]\n"
        "movlt r0, #0\n"
        "cmp r3, r2\n"
        "ldrsh r3, [r1, #0xa]\n"
        "ldrsh r1, [r1, #0xc]\n"
        "movlt r0, #0\n"
        "cmp r3, r2\n"
        "movlt r0, #0\n"
        "cmp r1, r2\n"
        "movlt r0, #0\n"
        "bx lr\n"
        ".word 0x000003e7\n"
    );
}

// DECOMP_FUNC(0x002544e4, 24)
extern "C" __attribute__((naked)) void camp_func_002544e4() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1f400\n"
        "add r0, r0, #0xe4\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002544fc, 24)
extern "C" __attribute__((naked)) void ui_func_002544fc() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldr r1, [r1, #0x20]\n"
        "add r0, r1, r0, lsl #2\n"
        "ldr r0, [r0, #0xd8]\n"
        "bx lr\n"
        ".word 0x0044de98\n"
    );
}

// DECOMP_FUNC(0x00254514, 24)
extern "C" __attribute__((naked)) void ui_func_00254514() {
    asm volatile(
        "ldr r2, [pc, #0xc]\n"
        "ldr r2, [r2, #0x20]\n"
        "add r0, r2, r0, lsl #2\n"
        "str r1, [r0, #0xd8]\n"
        "bx lr\n"
        ".word 0x0044de98\n"
    );
}

// DECOMP_FUNC(0x00254674, 80)
extern "C" __attribute__((naked)) void script_vm_func_00254674() {
    asm volatile(
        "ldr r2, [pc, #0x44]\n"
        "mov ip, #1\n"
        "mvn r3, #0\n"
        "strb ip, [r2]\n"
        "ldr ip, [r1]\n"
        "str ip, [r2, #0xc]\n"
        "ldr ip, [r1, #4]\n"
        "str ip, [r2, #0x10]\n"
        "ldr ip, [r1, #8]\n"
        "str ip, [r2, #0x14]\n"
        "ldr ip, [r1, #0xc]\n"
        "str ip, [r2, #0x18]\n"
        "ldr ip, [r1, #0x10]\n"
        "str ip, [r2, #0x1c]\n"
        "ldr r1, [r1, #0x14]\n"
        "str r1, [r2, #0x20]\n"
        "add r2, r2, #4\n"
        "stm r2, {r0, r3}\n"
        "bx lr\n"
        ".word 0x004937a0\n"
    );
}

// DECOMP_FUNC(0x002547a8, 36)
extern "C" __attribute__((naked)) void func_002547a8() {
    asm volatile(
        "add r2, r0, r0, lsl #3\n"
        "add r0, r2, r0, lsl #5\n"
        "ldr r2, [pc, #0x10]\n"
        "add r1, r1, r1, lsl #2\n"
        "add r0, r2, r0, lsl #3\n"
        "ldr r0, [r0, #0x13c]\n"
        "ldr r0, [r0, r1, lsl #2]\n"
        "bx lr\n"
        ".word 0x00478000\n"
    );
}
