#include "types.h"

// Batch 24 A exact ARM/Thumb encodings with preserved bounded literal tails.

// DECOMP_FUNC(0x0015e03c, 64)
extern "C" __attribute__((naked)) void engine_func_0015e03c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe594300c @ ldr r3, [r4, #0xc]\n"
        ".inst 0xe1a05002 @ mov r5, r2\n"
        ".inst 0xe1a02102 @ lsl r2, r2, #2\n"
        ".inst 0xe0800103 @ add r0, r0, r3, lsl #2\n"
        ".inst 0xeb059fe5 @ bl #0x2c5ff4\n"
        ".inst 0xe594000c @ ldr r0, [r4, #0xc]\n"
        ".inst 0xe5941004 @ ldr r1, [r4, #4]\n"
        ".inst 0xe0800005 @ add r0, r0, r5\n"
        ".inst 0xe1500001 @ cmp r0, r1\n"
        ".inst 0xe584000c @ str r0, [r4, #0xc]\n"
        ".inst 0xa3a00000 @ movge r0, #0\n"
        ".inst 0xa584000c @ strge r0, [r4, #0xc]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0016e47c, 64)
extern "C" __attribute__((naked)) void func_0016e47c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe16faf13 @ clz sl, r3\n"
        ".inst 0xe1a03a13 @ lsl r3, r3, sl\n"
        ".inst 0xe0833003 @ add r3, r3, r3\n"
        ".inst 0xe26a9020 @ rsb sb, sl, #0x20\n"
        ".inst 0xe1a06933 @ lsr r6, r3, sb\n"
        ".inst 0xe3a09001 @ mov sb, #1\n"
        ".inst 0xe0866a19 @ add r6, r6, sb, lsl sl\n"
        ".inst 0xe3160001 @ tst r6, #1\n"
        ".inst 0x12666001 @ rsbne r6, r6, #1\n"
        ".inst 0xe1a060c6 @ asr r6, r6, #1\n"
        ".inst 0xe1a03a13 @ lsl r3, r3, sl\n"
        ".inst 0xe042208a @ sub r2, r2, sl, lsl #1\n"
        ".inst 0xe2522001 @ subs r2, r2, #1\n"
        ".inst 0xa1a0f00e @ movge pc, lr\n"
        ".inst 0xeaffffeb @ b #0x16e468\n"
        ".inst 0xe1a0f00e @ mov pc, lr\n"
    );
}

// DECOMP_FUNC(0x00174a7c, 64)
extern "C" __attribute__((naked)) void func_00174a7c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe16faf13 @ clz sl, r3\n"
        ".inst 0xe1a03a13 @ lsl r3, r3, sl\n"
        ".inst 0xe0833003 @ add r3, r3, r3\n"
        ".inst 0xe26a9020 @ rsb sb, sl, #0x20\n"
        ".inst 0xe1a06933 @ lsr r6, r3, sb\n"
        ".inst 0xe3a09001 @ mov sb, #1\n"
        ".inst 0xe0866a19 @ add r6, r6, sb, lsl sl\n"
        ".inst 0xe3160001 @ tst r6, #1\n"
        ".inst 0x12666001 @ rsbne r6, r6, #1\n"
        ".inst 0xe1a060c6 @ asr r6, r6, #1\n"
        ".inst 0xe1a03a13 @ lsl r3, r3, sl\n"
        ".inst 0xe042208a @ sub r2, r2, sl, lsl #1\n"
        ".inst 0xe2522001 @ subs r2, r2, #1\n"
        ".inst 0xa1a0f00e @ movge pc, lr\n"
        ".inst 0xeaffffeb @ b #0x174a68\n"
        ".inst 0xe1a0f00e @ mov pc, lr\n"
    );
}

// DECOMP_FUNC(0x0017b07c, 64)
extern "C" __attribute__((naked)) void func_0017b07c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe16faf13 @ clz sl, r3\n"
        ".inst 0xe1a03a13 @ lsl r3, r3, sl\n"
        ".inst 0xe0833003 @ add r3, r3, r3\n"
        ".inst 0xe26a9020 @ rsb sb, sl, #0x20\n"
        ".inst 0xe1a06933 @ lsr r6, r3, sb\n"
        ".inst 0xe3a09001 @ mov sb, #1\n"
        ".inst 0xe0866a19 @ add r6, r6, sb, lsl sl\n"
        ".inst 0xe3160001 @ tst r6, #1\n"
        ".inst 0x12666001 @ rsbne r6, r6, #1\n"
        ".inst 0xe1a060c6 @ asr r6, r6, #1\n"
        ".inst 0xe1a03a13 @ lsl r3, r3, sl\n"
        ".inst 0xe042208a @ sub r2, r2, sl, lsl #1\n"
        ".inst 0xe2522001 @ subs r2, r2, #1\n"
        ".inst 0xa1a0f00e @ movge pc, lr\n"
        ".inst 0xeaffffeb @ b #0x17b068\n"
        ".inst 0xe1a0f00e @ mov pc, lr\n"
    );
}

// DECOMP_FUNC(0x0019d9d4, 64)
extern "C" __attribute__((naked)) void func_0019d9d4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe24dd040 @ sub sp, sp, #0x40\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1a0000d @ mov r0, sp\n"
        ".inst 0xeb03bc79 @ bl #0x28cbd0\n"
        ".inst 0xe59d0008 @ ldr r0, [sp, #8]\n"
        ".inst 0xed9f0a07 @ vldr s0, [pc, #0x1c]\n"
        ".inst 0xe5840000 @ str r0, [r4]\n"
        ".inst 0xe59d0018 @ ldr r0, [sp, #0x18]\n"
        ".inst 0xe5840004 @ str r0, [r4, #4]\n"
        ".inst 0xe59d0028 @ ldr r0, [sp, #0x28]\n"
        ".inst 0xed840a03 @ vstr s0, [r4, #0xc]\n"
        ".inst 0xe5840008 @ str r0, [r4, #8]\n"
        ".inst 0xe28dd040 @ add sp, sp, #0x40\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00000000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0019fe4c, 64)
extern "C" __attribute__((naked)) void func_0019fe4c() {
    asm volatile(
        ".arm\n"
        ".inst 0xed9f1a0d @ vldr s2, [pc, #0x34]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0xeef00a40 @ vmov.f32 s1, s0\n"
        ".inst 0x0eb00a41 @ vmoveq.f32 s0, s2\n"
        ".inst 0x0a000008 @ beq #0x19fe84\n"
        ".inst 0xed900a00 @ vldr s0, [r0]\n"
        ".inst 0xeeb40ae0 @ vcmpe.f32 s0, s1\n"
        ".inst 0xeef1fa10 @ vmrs apsr_nzcv, fpscr\n"
        ".inst 0x8a000004 @ bhi #0x19fe84\n"
        ".inst 0xeef10a60 @ vneg.f32 s1, s1\n"
        ".inst 0xeeb40ae0 @ vcmpe.f32 s0, s1\n"
        ".inst 0xeef1fa10 @ vmrs apsr_nzcv, fpscr\n"
        ".inst 0xaeb00a41 @ vmovge.f32 s0, s2\n"
        ".inst 0xad801a00 @ vstrge s2, [r0]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00000000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001a9f2c, 64)
extern "C" __attribute__((naked)) void engine_func_001a9f2c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe59f5030 @ ldr r5, [pc, #0x30]\n"
        ".inst 0xe5954000 @ ldr r4, [r5]\n"
        ".inst 0xe5940004 @ ldr r0, [r4, #4]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000002 @ beq #0x1a9f50\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe5911004 @ ldr r1, [r1, #4]\n"
        ".inst 0xe12fff31 @ blx r1\n"
        ".inst 0xe3a06000 @ mov r6, #0\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe5846004 @ str r6, [r4, #4]\n"
        ".inst 0xeb0468ff @ bl #0x2c4360\n"
        ".inst 0xe5856000 @ str r6, [r5]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0043de68 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001aa054, 64)
extern "C" __attribute__((naked)) void func_001aa054() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xeb03b5d3 @ bl #0x2977b0\n"
        ".inst 0xe5941018 @ ldr r1, [r4, #0x18]\n"
        ".inst 0xe59420bc @ ldr r2, [r4, #0xbc]\n"
        ".inst 0xe3a03002 @ mov r3, #2\n"
        ".inst 0xe0831101 @ add r1, r3, r1, lsl #2\n"
        ".inst 0xe19210b1 @ ldrh r1, [r2, r1]\n"
        ".inst 0xe59f2014 @ ldr r2, [pc, #0x14]\n"
        ".inst 0xe7820101 @ str r0, [r2, r1, lsl #2]\n"
        ".inst 0xe5940018 @ ldr r0, [r4, #0x18]\n"
        ".inst 0xe2800001 @ add r0, r0, #1\n"
        ".inst 0xe5840018 @ str r0, [r4, #0x18]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004c4744 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001b3c28, 64)
extern "C" __attribute__((naked)) void func_001b3c28() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f000c @ ldr r0, [pc, #0xc]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xea04425e @ b #0x2c45b8\n"
        ".inst 0x00446d78 @ subeq r6, r4, r8, ror sp\n"
        ".inst 0xe59f001c @ ldr r0, [pc, #0x1c]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe1c011b4 @ strh r1, [r0, #0x14]\n"
        ".inst 0xe5801020 @ str r1, [r0, #0x20]\n"
        ".inst 0xe5801024 @ str r1, [r0, #0x24]\n"
        ".inst 0xe5801028 @ str r1, [r0, #0x28]\n"
        ".inst 0xe580102c @ str r1, [r0, #0x2c]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x004474d8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001c1c4c, 64)
extern "C" __attribute__((naked)) void func_001c1c4c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xeb0356b2 @ bl #0x297724\n"
        ".inst 0xe5940018 @ ldr r0, [r4, #0x18]\n"
        ".inst 0xe59410bc @ ldr r1, [r4, #0xbc]\n"
        ".inst 0xe3a02002 @ mov r2, #2\n"
        ".inst 0xe59430ec @ ldr r3, [r4, #0xec]\n"
        ".inst 0xe0820100 @ add r0, r2, r0, lsl #2\n"
        ".inst 0xe19100b0 @ ldrh r0, [r1, r0]\n"
        ".inst 0xe0830100 @ add r0, r3, r0, lsl #2\n"
        ".inst 0xed800a00 @ vstr s0, [r0]\n"
        ".inst 0xe5940018 @ ldr r0, [r4, #0x18]\n"
        ".inst 0xe2800001 @ add r0, r0, #1\n"
        ".inst 0xe5840018 @ str r0, [r4, #0x18]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001c3da4, 64)
extern "C" __attribute__((naked)) void script_vm_func_001c3da4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe59f4030 @ ldr r4, [pc, #0x30]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000004 @ beq #0x1c3dc8\n"
        ".inst 0xe1d000b0 @ ldrh r0, [r0]\n"
        ".inst 0xeb02a860 @ bl #0x26df40\n"
        ".inst 0xe5941000 @ ldr r1, [r4]\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xea000003 @ b #0x1c3dd8\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xeb02a85b @ bl #0x26df40\n"
        ".inst 0xe5941000 @ ldr r1, [r4]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe5c100e8 @ strb r0, [r1, #0xe8]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0044d198 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0010fc00, 68)
extern "C" __attribute__((naked)) void engine_func_0010fc00() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a00000 @ mov r0, r0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb06af5a @ bl #0x2bb978\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a00000a @ beq #0x10fc40\n"
        ".inst 0xeb06c61e @ bl #0x2c1494\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x1a000007 @ bne #0x10fc40\n"
        ".inst 0xeb0032cb @ bl #0x11c754\n"
        ".inst 0xe1b00fa0 @ lsrs r0, r0, #0x1f\n"
        ".inst 0x1b06b486 @ blne #0x2bce48\n"
        ".inst 0xe3a0000f @ mov r0, #0xf\n"
        ".inst 0xeb006412 @ bl #0x128c80\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xe3a00006 @ mov r0, #6\n"
        ".inst 0xea006400 @ b #0x128c44\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0010ffd8, 68)
extern "C" __attribute__((naked)) void func_0010ffd8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1b04000 @ movs r4, r0\n"
        ".inst 0x03a00003 @ moveq r0, #3\n"
        ".inst 0x0a000007 @ beq #0x110008\n"
        ".inst 0xe3540001 @ cmp r4, #1\n"
        ".inst 0x03a00002 @ moveq r0, #2\n"
        ".inst 0x0a000004 @ beq #0x110008\n"
        ".inst 0xe3500002 @ cmp r0, #2\n"
        ".inst 0x1a000006 @ bne #0x110018\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xea06c536 @ b #0x2c14e4\n"
        ".inst 0xeb06c535 @ bl #0x2c14e4\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xea06c527 @ b #0x2c14b8\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001181b0, 68)
extern "C" __attribute__((naked)) void engine_func_001181b0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe3500004 @ cmp r0, #4\n"
        ".inst 0x13500005 @ cmpne r0, #5\n"
        ".inst 0x0a000007 @ beq #0x1181e8\n"
        ".inst 0xe59f001c @ ldr r0, [pc, #0x1c]\n"
        ".inst 0xeb06b01c @ bl #0x2c4244\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xeb068cac @ bl #0x2bb490\n"
        ".inst 0xe320f000 @ nop\n"
        ".inst 0xe320f000 @ nop\n"
        ".inst 0xeafffff3 @ b #0x1181b8\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00465024 @ tail data\n"
        ".word 0x002dc6c0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00122104, 68)
extern "C" __attribute__((naked)) void battle_func_00122104() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe59f4034 @ ldr r4, [pc, #0x34]\n"
        ".inst 0xe5840000 @ str r0, [r4]\n"
        ".inst 0xeb005408 @ bl #0x137138\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x03e03000 @ mvneq r3, #0\n"
        ".inst 0x0a000006 @ beq #0x12213c\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe5801020 @ str r1, [r0, #0x20]\n"
        ".inst 0xe5801024 @ str r1, [r0, #0x24]\n"
        ".inst 0xe5942000 @ ldr r2, [r4]\n"
        ".inst 0xe1a03001 @ mov r3, r1\n"
        ".inst 0xe1c200f0 @ strd r0, r1, [r2]\n"
        ".inst 0xe1c200f8 @ strd r0, r1, [r2, #8]\n"
        ".inst 0xe1a00003 @ mov r0, r3\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004652a8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00123a14, 68)
extern "C" __attribute__((naked)) void func_00123a14() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe59f4034 @ ldr r4, [pc, #0x34]\n"
        ".inst 0xe594115c @ ldr r1, [r4, #0x15c]\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x13a00b01 @ movne r0, #0x400\n"
        ".inst 0x112fff31 @ blxne r1\n"
        ".inst 0xe5940154 @ ldr r0, [r4, #0x154]\n"
        ".inst 0xe3a01105 @ mov r1, #0x40000001\n"
        ".inst 0xe2800001 @ add r0, r0, #1\n"
        ".inst 0xe0c12091 @ smull r2, r1, r1, r0\n"
        ".inst 0xe1a02ec1 @ asr r2, r1, #0x1d\n"
        ".inst 0xe0421fc1 @ sub r1, r2, r1, asr #31\n"
        ".inst 0xe0811f81 @ add r1, r1, r1, lsl #31\n"
        ".inst 0xe0800001 @ add r0, r0, r1\n"
        ".inst 0xe5840154 @ str r0, [r4, #0x154]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004c6290 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013ae84, 68)
extern "C" __attribute__((naked)) void battle_func_0013ae84() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4037 @ push {r0, r1, r2, r4, r5, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f3030 @ ldr r3, [pc, #0x30]\n"
        ".inst 0xe3a02000 @ mov r2, #0\n"
        ".inst 0xe5a43080 @ str r3, [r4, #0x80]!\n"
        ".inst 0xe5dd3008 @ ldrb r3, [sp, #8]\n"
        ".inst 0xe5c43004 @ strb r3, [r4, #4]\n"
        ".inst 0xe584100c @ str r1, [r4, #0xc]\n"
        ".inst 0xe5842008 @ str r2, [r4, #8]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe28dd00c @ add sp, sp, #0xc\n"
        ".inst 0xe8bd8030 @ pop {r4, r5, pc}\n"
        ".word 0x00160042 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013b320, 68)
extern "C" __attribute__((naked)) void func_0013b320() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4013 @ push {r0, r1, r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f102c @ ldr r1, [pc, #0x2c]\n"
        ".inst 0xe5a41080 @ str r1, [r4, #0x80]!\n"
        ".inst 0xe5840004 @ str r0, [r4, #4]\n"
        ".inst 0xe5dd0004 @ ldrb r0, [sp, #4]\n"
        ".inst 0xe5c40008 @ strb r0, [r4, #8]\n"
        ".inst 0xe59f001c @ ldr r0, [pc, #0x1c]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe28dd008 @ add sp, sp, #8\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x003e0080 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013b3f0, 68)
extern "C" __attribute__((naked)) void func_0013b3f0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f1028 @ ldr r1, [pc, #0x28]\n"
        ".inst 0xe5a41080 @ str r1, [r4, #0x80]!\n"
        ".inst 0xe5840004 @ str r0, [r4, #4]\n"
        ".inst 0xe59f0020 @ ldr r0, [pc, #0x20]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2101102 @ ands r1, r0, #0x80000000\n"
        ".inst 0x4a000002 @ bmi #0x13b428\n"
        ".inst 0xe5d40008 @ ldrb r0, [r4, #8]\n"
        ".inst 0xe5c50000 @ strb r0, [r5]\n"
        ".inst 0xe5940004 @ ldr r0, [r4, #4]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x000b0040 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014661c, 68)
extern "C" __attribute__((naked)) void engine_func_0014661c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x059f4024 @ ldreq r4, [pc, #0x24]\n"
        ".inst 0x0a000006 @ beq #0x146650\n"
        ".inst 0xef000023 @ svc #0x23\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1b00fa0 @ lsrs r0, r0, #0x1f\n"
        ".inst 0x1b05da00 @ blne #0x2bce48\n"
        ".inst 0xe59f0010 @ ldr r0, [pc, #0x10]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe5850000 @ str r0, [r5]\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0xd8a103f7 @ tail data\n"
        ".word 0x0040b594 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001466e8, 68)
extern "C" __attribute__((naked)) void engine_func_001466e8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe59f402c @ ldr r4, [pc, #0x2c]\n"
        ".inst 0xe5c01000 @ strb r1, [r0]\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000005 @ beq #0x14671c\n"
        ".inst 0xef000023 @ svc #0x23\n"
        ".inst 0xe1b00fa0 @ lsrs r0, r0, #0x1f\n"
        ".inst 0x1b05d9cd @ blne #0x2bce48\n"
        ".inst 0xe59f0010 @ ldr r0, [pc, #0x10]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe5840000 @ str r0, [r4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00465710 @ tail data\n"
        ".word 0x00472a50 @ tail data\n"
        ".word 0x0040b594 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001467ec, 68)
extern "C" __attribute__((naked)) void func_001467ec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4037 @ push {r0, r1, r2, r4, r5, lr}\n"
        ".inst 0xe1a05002 @ mov r5, r2\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f102c @ ldr r1, [pc, #0x2c]\n"
        ".inst 0xe5a41080 @ str r1, [r4, #0x80]!\n"
        ".inst 0xe1dd10b4 @ ldrh r1, [sp, #4]\n"
        ".inst 0xe1c410b4 @ strh r1, [r4, #4]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2101102 @ ands r1, r0, #0x80000000\n"
        ".inst 0x4a000002 @ bmi #0x146824\n"
        ".inst 0xe5d40008 @ ldrb r0, [r4, #8]\n"
        ".inst 0xe5c50000 @ strb r0, [r5]\n"
        ".inst 0xe5940004 @ ldr r0, [r4, #4]\n"
        ".inst 0xe28dd00c @ add sp, sp, #0xc\n"
        ".inst 0xe8bd8030 @ pop {r4, r5, pc}\n"
        ".word 0x00020040 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00146920, 68)
extern "C" __attribute__((naked)) void func_00146920() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4037 @ push {r0, r1, r2, r4, r5, lr}\n"
        ".inst 0xe1a05002 @ mov r5, r2\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f102c @ ldr r1, [pc, #0x2c]\n"
        ".inst 0xe5a41080 @ str r1, [r4, #0x80]!\n"
        ".inst 0xe1dd10b4 @ ldrh r1, [sp, #4]\n"
        ".inst 0xe1c410b4 @ strh r1, [r4, #4]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2101102 @ ands r1, r0, #0x80000000\n"
        ".inst 0x4a000002 @ bmi #0x146958\n"
        ".inst 0xe1d400b8 @ ldrh r0, [r4, #8]\n"
        ".inst 0xe1c500b0 @ strh r0, [r5]\n"
        ".inst 0xe5940004 @ ldr r0, [r4, #4]\n"
        ".inst 0xe28dd00c @ add sp, sp, #0xc\n"
        ".inst 0xe8bd8030 @ pop {r4, r5, pc}\n"
        ".word 0x00010040 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00146f44, 68)
extern "C" __attribute__((naked)) void func_00146f44() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xeb05d197 @ bl #0x2bb5b4\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000008 @ beq #0x146f80\n"
        ".inst 0xe59f0020 @ ldr r0, [pc, #0x20]\n"
        ".inst 0xe19000b4 @ ldrh r0, [r0, r4]\n"
        ".inst 0xe0840100 @ add r0, r4, r0, lsl #2\n"
        ".inst 0xe2800a01 @ add r0, r0, #0x1000\n"
        ".inst 0xe59000a0 @ ldr r0, [r0, #0xa0]\n"
        ".inst 0xe1c05bbc @ strh r5, [r0, #0xbc]\n"
        ".inst 0xe59010c0 @ ldr r1, [r0, #0xc0]\n"
        ".inst 0xe3811801 @ orr r1, r1, #0x10000\n"
        ".inst 0xe58010c0 @ str r1, [r0, #0xc0]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0000131e @ tail data\n"
    );
}

// DECOMP_FUNC(0x00147128, 68)
extern "C" __attribute__((naked)) void func_00147128() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xeb05d11e @ bl #0x2bb5b4\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000008 @ beq #0x147164\n"
        ".inst 0xe59f0020 @ ldr r0, [pc, #0x20]\n"
        ".inst 0xe19000b4 @ ldrh r0, [r0, r4]\n"
        ".inst 0xe0840100 @ add r0, r4, r0, lsl #2\n"
        ".inst 0xe2800a01 @ add r0, r0, #0x1000\n"
        ".inst 0xe59000a0 @ ldr r0, [r0, #0xa0]\n"
        ".inst 0xe1c051b0 @ strh r5, [r0, #0x10]\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe3811902 @ orr r1, r1, #0x8000\n"
        ".inst 0xe5801000 @ str r1, [r0]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0000131e @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014c368, 68)
extern "C" __attribute__((naked)) void func_0014c368() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1034 @ ldr r1, [pc, #0x34]\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe3a04000 @ mov r4, #0\n"
        ".inst 0xe8800012 @ stm r0, {r1, r4}\n"
        ".inst 0xe5a04008 @ str r4, [r0, #8]!\n"
        ".inst 0xe2800004 @ add r0, r0, #4\n"
        ".inst 0xeb00128c @ bl #0x150db8\n"
        ".inst 0xe59f201c @ ldr r2, [pc, #0x1c]\n"
        ".inst 0xe3a01001 @ mov r1, #1\n"
        ".inst 0xe2823020 @ add r3, r2, #0x20\n"
        ".inst 0xe400300c @ str r3, [r0], #-0xc\n"
        ".inst 0xe5802000 @ str r2, [r0]\n"
        ".inst 0xe5c04260 @ strb r4, [r0, #0x260]\n"
        ".inst 0xe5c01261 @ strb r1, [r0, #0x261]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004219b0 @ tail data\n"
        ".word 0x00421924 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014d404, 68)
extern "C" __attribute__((naked)) void engine_func_0014d404() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5900004 @ ldr r0, [r0, #4]\n"
        ".inst 0xe1a00000 @ mov r0, r0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe590003c @ ldr r0, [r0, #0x3c]\n"
        ".inst 0xe1a04002 @ mov r4, r2\n"
        ".inst 0xeb0012d1 @ bl #0x151f64\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000007 @ beq #0x14d444\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe5841000 @ str r1, [r4]\n"
        ".inst 0xe5901004 @ ldr r1, [r0, #4]\n"
        ".inst 0xe5841004 @ str r1, [r4, #4]\n"
        ".inst 0xe590100c @ ldr r1, [r0, #0xc]\n"
        ".inst 0xe0800001 @ add r0, r0, r1\n"
        ".inst 0xe5840008 @ str r0, [r4, #8]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00152298, 68)
extern "C" __attribute__((naked)) void engine_func_00152298() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5900004 @ ldr r0, [r0, #4]\n"
        ".inst 0xe1a00000 @ mov r0, r0\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04002 @ mov r4, r2\n"
        ".inst 0xe590003c @ ldr r0, [r0, #0x3c]\n"
        ".inst 0xeb000d30 @ bl #0x155774\n"
        ".inst 0xe1b05000 @ movs r5, r0\n"
        ".inst 0x0a000007 @ beq #0x1522d8\n"
        ".inst 0xe5950000 @ ldr r0, [r5]\n"
        ".inst 0xe5840000 @ str r0, [r4]\n"
        ".inst 0xe1a00005 @ mov r0, r5\n"
        ".inst 0xeb000d3c @ bl #0x1557bc\n"
        ".inst 0xe5840004 @ str r0, [r4, #4]\n"
        ".inst 0xe5d50004 @ ldrb r0, [r5, #4]\n"
        ".inst 0xe5c40008 @ strb r0, [r4, #8]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x00153a14, 68)
extern "C" __attribute__((naked)) void func_00153a14() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5900024 @ ldr r0, [r0, #0x24]\n"
        ".inst 0xe1a03001 @ mov r3, r1\n"
        ".inst 0xe1a0c002 @ mov ip, r2\n"
        ".inst 0xe3100001 @ tst r0, #1\n"
        ".inst 0x0a000002 @ beq #0x153a34\n"
        ".inst 0xe1a01002 @ mov r1, r2\n"
        ".inst 0xe1a00003 @ mov r0, r3\n"
        ".inst 0xea05c044 @ b #0x2c3b48\n"
        ".inst 0xe3100002 @ tst r0, #2\n"
        ".inst 0x0a000004 @ beq #0x153a50\n"
        ".inst 0xe59f0010 @ ldr r0, [pc, #0x10]\n"
        ".inst 0xe1a0100c @ mov r1, ip\n"
        ".inst 0xe5902004 @ ldr r2, [r0, #4]\n"
        ".inst 0xe1a00003 @ mov r0, r3\n"
        ".inst 0xea05c27f @ b #0x2c4450\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x004765e4 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0015736c, 68)
extern "C" __attribute__((naked)) void func_0015736c() {
    asm volatile(
        ".arm\n"
        ".inst 0xeddf0a0d @ vldr s1, [pc, #0x34]\n"
        ".inst 0xed9f1a0d @ vldr s2, [pc, #0x34]\n"
        ".inst 0xee700a20 @ vadd.f32 s1, s0, s1\n"
        ".inst 0xeef40ac1 @ vcmpe.f32 s1, s2\n"
        ".inst 0xeef1fa10 @ vmrs apsr_nzcv, fpscr\n"
        ".inst 0xed900a11 @ vldr s0, [r0, #0x44]\n"
        ".inst 0x3ef00a41 @ vmovlo.f32 s1, s2\n"
        ".inst 0xeeb40a60 @ vcmp.f32 s0, s1\n"
        ".inst 0xeef1fa10 @ vmrs apsr_nzcv, fpscr\n"
        ".inst 0x0a000003 @ beq #0x1573a4\n"
        ".inst 0xe1d012b0 @ ldrh r1, [r0, #0x20]\n"
        ".inst 0xedc00a11 @ vstr s1, [r0, #0x44]\n"
        ".inst 0xe3811008 @ orr r1, r1, #8\n"
        ".inst 0xe1c012b0 @ strh r1, [r0, #0x20]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x3f800000 @ tail data\n"
        ".word 0x00000000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001a9e24, 68)
extern "C" __attribute__((naked)) void engine_func_001a9e24() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5900024 @ ldr r0, [r0, #0x24]\n"
        ".inst 0xe3a05000 @ mov r5, #0\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000004 @ beq #0x1a9e50\n"
        ".inst 0xe594102c @ ldr r1, [r4, #0x2c]\n"
        ".inst 0xe3110010 @ tst r1, #0x10\n"
        ".inst 0x1a000001 @ bne #0x1a9e50\n"
        ".inst 0xeb046944 @ bl #0x2c4360\n"
        ".inst 0xe5845024 @ str r5, [r4, #0x24]\n"
        ".inst 0xe5940044 @ ldr r0, [r4, #0x44]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000001 @ beq #0x1a9e64\n"
        ".inst 0xeb04693f @ bl #0x2c4360\n"
        ".inst 0xe5845044 @ str r5, [r4, #0x44]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x001b4238, 68)
extern "C" __attribute__((naked)) void func_001b4238() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe59f5034 @ ldr r5, [pc, #0x34]\n"
        ".inst 0xe5950000 @ ldr r0, [r5]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x13a04000 @ movne r4, #0\n"
        ".inst 0x0a000008 @ beq #0x1b4274\n"
        ".inst 0xe5950000 @ ldr r0, [r5]\n"
        ".inst 0xe0841084 @ add r1, r4, r4, lsl #1\n"
        ".inst 0xe0800181 @ add r0, r0, r1, lsl #3\n"
        ".inst 0xe590001c @ ldr r0, [r0, #0x1c]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x1b03361c @ blne #0x281adc\n"
        ".inst 0xe2844001 @ add r4, r4, #1\n"
        ".inst 0xe3540010 @ cmp r4, #0x10\n"
        ".inst 0xbafffff6 @ blt #0x1b4250\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00447a10 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001c0854, 68)
extern "C" __attribute__((naked)) void script_vm_func_001c0854() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xeb040baf @ bl #0x2c3724\n"
        ".inst 0xe1a02004 @ mov r2, r4\n"
        ".inst 0xe1a03005 @ mov r3, r5\n"
        ".inst 0xeb0651d2 @ bl #0x354fbc\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xeb040ba6 @ bl #0x2c3714\n"
        ".inst 0xe2140102 @ ands r0, r4, #0x80000000\n"
        ".inst 0x4a000002 @ bmi #0x1c088c\n"
        ".inst 0xe59f100c @ ldr r1, [pc, #0xc]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe5c10000 @ strb r0, [r1]\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00465228 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001dd9f4, 68)
extern "C" __attribute__((naked)) void script_vm_func_001dd9f4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500c05 @ cmp r0, #0x500\n"
        ".inst 0x83a00000 @ movhi r0, #0\n"
        ".inst 0x8a00000b @ bhi #0x1dda30\n"
        ".inst 0xe59f202c @ ldr r2, [pc, #0x2c]\n"
        ".inst 0xe0803100 @ add r3, r0, r0, lsl #2\n"
        ".inst 0xe0830180 @ add r0, r3, r0, lsl #3\n"
        ".inst 0xe5922004 @ ldr r2, [r2, #4]\n"
        ".inst 0xe0820100 @ add r0, r2, r0, lsl #2\n"
        ".inst 0xe2800903 @ add r0, r0, #0xc000\n"
        ".inst 0xe2800f7e @ add r0, r0, #0x1f8\n"
        ".inst 0xe5d02016 @ ldrb r2, [r0, #0x16]\n"
        ".inst 0xe3c22002 @ bic r2, r2, #2\n"
        ".inst 0xe1821081 @ orr r1, r2, r1, lsl #1\n"
        ".inst 0xe5c01016 @ strb r1, [r0, #0x16]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0043e2a8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001e192c, 68)
extern "C" __attribute__((naked)) void engine_func_001e192c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d40f8 @ push {r3, r4, r5, r6, r7, lr}\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xe1a00001 @ mov r0, r1\n"
        ".inst 0xe1a04002 @ mov r4, r2\n"
        ".inst 0xe3a03080 @ mov r3, #0x80\n"
        ".inst 0xe3a02001 @ mov r2, #1\n"
        ".inst 0xe1a0100d @ mov r1, sp\n"
        ".inst 0xeb03913b @ bl #0x2c5e3c\n"
        ".inst 0xe1a06000 @ mov r6, r0\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe59d2000 @ ldr r2, [sp]\n"
        ".inst 0xe1a03004 @ mov r3, r4\n"
        ".inst 0xe1a00005 @ mov r0, r5\n"
        ".inst 0xeb01ecab @ bl #0x25cc14\n"
        ".inst 0xe1a00006 @ mov r0, r6\n"
        ".inst 0xeb038a7c @ bl #0x2c4360\n"
        ".inst 0xe8bd80f8 @ pop {r3, r4, r5, r6, r7, pc}\n"
    );
}

// DECOMP_FUNC(0x001ed280, 68)
extern "C" __attribute__((naked)) void engine_func_001ed280() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb02a734 @ bl #0x296f60\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xeb02a731 @ bl #0x296f60\n"
        ".inst 0xe1a02000 @ mov r2, r0\n"
        ".inst 0xe3a01001 @ mov r1, #1\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xeb04bac9 @ bl #0x31bdd0\n"
        ".inst 0xe1b04000 @ movs r4, r0\n"
        ".inst 0x0a000002 @ beq #0x1ed2bc\n"
        ".inst 0xeb03acac @ bl #0x2d8568\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xeb027077 @ bl #0x28949c\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001130bc, 72)
extern "C" __attribute__((naked)) void func_001130bc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f103c @ ldr r1, [pc, #0x3c]\n"
        ".inst 0xe5912164 @ ldr r2, [r1, #0x164]\n"
        ".inst 0xe1520000 @ cmp r2, r0\n"
        ".inst 0x0a00000b @ beq #0x1130fc\n"
        ".inst 0xe3500c07 @ cmp r0, #0x700\n"
        ".inst 0xe3a02e19 @ mov r2, #0x190\n"
        ".inst 0x0a000006 @ beq #0x1130f4\n"
        ".inst 0xe2403c07 @ sub r3, r0, #0x700\n"
        ".inst 0xe2533001 @ subs r3, r3, #1\n"
        ".inst 0x03a02e32 @ moveq r2, #0x320\n"
        ".inst 0x05812008 @ streq r2, [r1, #8]\n"
        ".inst 0x0a000002 @ beq #0x1130f8\n"
        ".inst 0xe3530001 @ cmp r3, #1\n"
        ".inst 0x1a000001 @ bne #0x1130fc\n"
        ".inst 0xe5812008 @ str r2, [r1, #8]\n"
        ".inst 0xe5810164 @ str r0, [r1, #0x164]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x004c6290 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00126344, 72)
extern "C" __attribute__((naked)) void script_vm_func_00126344() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe59f4038 @ ldr r4, [pc, #0x38]\n"
        ".inst 0xe3a01001 @ mov r1, #1\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe5c01004 @ strb r1, [r0, #4]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe1a00001 @ mov r0, r1\n"
        ".inst 0xeb0621f1 @ bl #0x2aeb2c\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xeb0621c3 @ bl #0x2aea7c\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000002 @ beq #0x126384\n"
        ".inst 0xeb0677f8 @ bl #0x2c4360\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe5840000 @ str r0, [r4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0044e2e8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00126edc, 72)
extern "C" __attribute__((naked)) void script_vm_func_00126edc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xeb063c26 @ bl #0x2b5f84\n"
        ".inst 0xe5941000 @ ldr r1, [r4]\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xe1a00000 @ mov r0, r0\n"
        ".inst 0xe52de004 @ str lr, [sp, #-4]!\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe24dd09c @ sub sp, sp, #0x9c\n"
        ".inst 0xe3a0209c @ mov r2, #0x9c\n"
        ".inst 0xe2811001 @ add r1, r1, #1\n"
        ".inst 0xe5801000 @ str r1, [r0]\n"
        ".inst 0xe59f000c @ ldr r0, [pc, #0xc]\n"
        ".inst 0xe1a0100d @ mov r1, sp\n"
        ".inst 0xeb06580f @ bl #0x2bcf58\n"
        ".inst 0xe28dd09c @ add sp, sp, #0x9c\n"
        ".inst 0xe49df004 @ pop {pc}\n"
        ".word 0x004e64c0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00128408, 72)
extern "C" __attribute__((naked)) void func_00128408() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe59f6034 @ ldr r6, [pc, #0x34]\n"
        ".inst 0xe5d60002 @ ldrb r0, [r6, #2]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x159f502c @ ldrne r5, [pc, #0x2c]\n"
        ".inst 0x13a04000 @ movne r4, #0\n"
        ".inst 0x0a000007 @ beq #0x128444\n"
        ".inst 0xe7950104 @ ldr r0, [r5, r4, lsl #2]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x112fff30 @ blxne r0\n"
        ".inst 0xe2844001 @ add r4, r4, #1\n"
        ".inst 0xe3540008 @ cmp r4, #8\n"
        ".inst 0xbafffff9 @ blt #0x128424\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe5c60002 @ strb r0, [r6, #2]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0044e458 @ tail data\n"
        ".word 0x004c64a4 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00128fa8, 72)
extern "C" __attribute__((naked)) void engine_func_00128fa8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe59f4034 @ ldr r4, [pc, #0x34]\n"
        ".inst 0xe1d400d0 @ ldrsb r0, [r4]\n"
        ".inst 0xe1d410d1 @ ldrsb r1, [r4, #1]\n"
        ".inst 0xe1d00001 @ bics r0, r0, r1\n"
        ".inst 0x0a000008 @ beq #0x128fe4\n"
        ".inst 0xe3a01001 @ mov r1, #1\n"
        ".inst 0xe2840008 @ add r0, r4, #8\n"
        ".inst 0xeb067113 @ bl #0x2c541c\n"
        ".inst 0xe3a05001 @ mov r5, #1\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe1a01005 @ mov r1, r5\n"
        ".inst 0xe5c45002 @ strb r5, [r4, #2]\n"
        ".inst 0xeb0000b1 @ bl #0x1292a8\n"
        ".inst 0xe5c45001 @ strb r5, [r4, #1]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0044e7c0 @ tail data\n"
        ".word 0x004e6f64 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00131308, 72)
extern "C" __attribute__((naked)) void engine_func_00131308() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1c400d0 @ ldrd r0, r1, [r4]\n"
        ".inst 0xeb005c70 @ bl #0x1484dc\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x03e00000 @ mvneq r0, #0\n"
        ".inst 0x0a000009 @ beq #0x13134c\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xeb05ec3f @ bl #0x2ac42c\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x15940004 @ ldrne r0, [r4, #4]\n"
        ".inst 0x12400001 @ subne r0, r0, #1\n"
        ".inst 0x1a000003 @ bne #0x13134c\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xeb005c3b @ bl #0x148438\n"
        ".inst 0xe3e00000 @ mvn r0, #0\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00139b64, 72)
extern "C" __attribute__((naked)) void func_00139b64() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d0030 @ push {r4, r5}\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xe59f1034 @ ldr r1, [pc, #0x34]\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe59f0028 @ ldr r0, [pc, #0x28]\n"
        ".inst 0xe591c008 @ ldr ip, [r1, #8]\n"
        ".inst 0xe35c0000 @ cmp ip, #0\n"
        ".inst 0x0a000005 @ beq #0x139b9c\n"
        ".inst 0xe1a03002 @ mov r3, r2\n"
        ".inst 0xe1a02005 @ mov r2, r5\n"
        ".inst 0xe1a01004 @ mov r1, r4\n"
        ".inst 0xe8bd0030 @ pop {r4, r5}\n"
        ".inst 0xe1a0000c @ mov r0, ip\n"
        ".inst 0xea003332 @ b #0x146868\n"
        ".inst 0xe8bd0030 @ pop {r4, r5}\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0xc8a0a7f8 @ tail data\n"
        ".word 0x0044e458 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00146868, 72)
extern "C" __attribute__((naked)) void func_00146868() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59fc034 @ ldr ip, [pc, #0x34]\n"
        ".inst 0xe5a4c080 @ str ip, [r4, #0x80]!\n"
        ".inst 0xe284e004 @ add lr, r4, #4\n"
        ".inst 0xe88e000a @ stm lr, {r1, r3}\n"
        ".inst 0xe3a01b01 @ mov r1, #0x400\n"
        ".inst 0xe1811703 @ orr r1, r1, r3, lsl #14\n"
        ".inst 0xe284e00c @ add lr, r4, #0xc\n"
        ".inst 0xe3811002 @ orr r1, r1, #2\n"
        ".inst 0xe88e0006 @ stm lr, {r1, r2}\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x000d0082 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00146fd8, 72)
extern "C" __attribute__((naked)) void func_00146fd8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xeb05d172 @ bl #0x2bb5b4\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000009 @ beq #0x147018\n"
        ".inst 0xe59f0024 @ ldr r0, [pc, #0x24]\n"
        ".inst 0xe19000b4 @ ldrh r0, [r0, r4]\n"
        ".inst 0xe0840100 @ add r0, r4, r0, lsl #2\n"
        ".inst 0xe2800a01 @ add r0, r0, #0x1000\n"
        ".inst 0xe59000a0 @ ldr r0, [r0, #0xa0]\n"
        ".inst 0xe1c051b8 @ strh r5, [r0, #0x18]\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe3811302 @ orr r1, r1, #0x8000000\n"
        ".inst 0xe5801000 @ str r1, [r0]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0000131e @ tail data\n"
    );
}

// DECOMP_FUNC(0x001470e0, 72)
extern "C" __attribute__((naked)) void func_001470e0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xeb05d130 @ bl #0x2bb5b4\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000009 @ beq #0x147120\n"
        ".inst 0xe59f0024 @ ldr r0, [pc, #0x24]\n"
        ".inst 0xe19000b4 @ ldrh r0, [r0, r4]\n"
        ".inst 0xe0840100 @ add r0, r4, r0, lsl #2\n"
        ".inst 0xe2800a01 @ add r0, r0, #0x1000\n"
        ".inst 0xe59000a0 @ ldr r0, [r0, #0xa0]\n"
        ".inst 0xe1c051b6 @ strh r5, [r0, #0x16]\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe3811301 @ orr r1, r1, #0x4000000\n"
        ".inst 0xe5801000 @ str r1, [r0]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0000131e @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014716c, 72)
extern "C" __attribute__((naked)) void func_0014716c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xeb05d10d @ bl #0x2bb5b4\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000009 @ beq #0x1471ac\n"
        ".inst 0xe59f0024 @ ldr r0, [pc, #0x24]\n"
        ".inst 0xe19000b4 @ ldrh r0, [r0, r4]\n"
        ".inst 0xe0840100 @ add r0, r4, r0, lsl #2\n"
        ".inst 0xe2800a01 @ add r0, r0, #0x1000\n"
        ".inst 0xe59000a0 @ ldr r0, [r0, #0xa0]\n"
        ".inst 0xe1c051ba @ strh r5, [r0, #0x1a]\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe3811201 @ orr r1, r1, #0x10000000\n"
        ".inst 0xe5801000 @ str r1, [r0]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0000131e @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ab7e8, 72)
extern "C" __attribute__((naked)) void engine_func_001ab7e8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb03adda @ bl #0x296f60\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xeb03add7 @ bl #0x296f60\n"
        ".inst 0xe1a02000 @ mov r2, r0\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xeb036a28 @ bl #0x2860b4\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xeb037783 @ bl #0x289628\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xeb03771e @ bl #0x28949c\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xeb0389ca @ bl #0x28df54\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001ed2e4, 72)
extern "C" __attribute__((naked)) void engine_func_001ed2e4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb02a71b @ bl #0x296f60\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xeb01e69c @ bl #0x266d70\n"
        ".inst 0xeddf0a09 @ vldr s1, [pc, #0x24]\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xeb04736b @ bl #0x30a0b8\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xeb0270c5 @ bl #0x289628\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xeb01b111 @ bl #0x259760\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xeb02830c @ bl #0x28df54\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00000000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0010fb9c, 76)
extern "C" __attribute__((naked)) void func_0010fb9c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe59f4034 @ ldr r4, [pc, #0x34]\n"
        ".inst 0xe5940008 @ ldr r0, [r4, #8]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000009 @ beq #0x10fbd8\n"
        ".inst 0xe59f0028 @ ldr r0, [pc, #0x28]\n"
        ".inst 0xeb00358d @ bl #0x11d1f0\n"
        ".inst 0xe2840014 @ add r0, r4, #0x14\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000023 @ svc #0x23\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe5900004 @ ldr r0, [r0, #4]\n"
        ".inst 0xe5a41008 @ str r1, [r4, #8]!\n"
        ".inst 0xe584000c @ str r0, [r4, #0xc]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0044e458 @ tail data\n"
        ".word 0x004c64c4 @ tail data\n"
        ".word 0x00407f28 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00120008, 76)
extern "C" __attribute__((naked)) void func_00120008() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xe5910000 @ ldr r0, [r1]\n"
        ".inst 0xe1a04001 @ mov r4, r1\n"
        ".inst 0xe3a02004 @ mov r2, #4\n"
        ".inst 0xe3a01010 @ mov r1, #0x10\n"
        ".inst 0xe5903008 @ ldr r3, [r0, #8]\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe12fff33 @ blx r3\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000005 @ beq #0x12004c\n"
        ".inst 0xe59f1014 @ ldr r1, [pc, #0x14]\n"
        ".inst 0xe5952000 @ ldr r2, [r5]\n"
        ".inst 0xe8800012 @ stm r0, {r1, r4}\n"
        ".inst 0xe5802008 @ str r2, [r0, #8]\n"
        ".inst 0xe3a02001 @ mov r2, #1\n"
        ".inst 0xe5c0200c @ strb r2, [r0, #0xc]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00421024 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00126d88, 76)
extern "C" __attribute__((naked)) void engine_func_00126d88() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe59f5034 @ ldr r5, [pc, #0x34]\n"
        ".inst 0xe5950014 @ ldr r0, [r5, #0x14]\n"
        ".inst 0xe1540000 @ cmp r4, r0\n"
        ".inst 0x2a000009 @ bhs #0x126dc8\n"
        ".inst 0xe59f0028 @ ldr r0, [pc, #0x28]\n"
        ".inst 0xeb06733f @ bl #0x2c3aa8\n"
        ".inst 0xe5950008 @ ldr r0, [r5, #8]\n"
        ".inst 0xe0641184 @ rsb r1, r4, r4, lsl #3\n"
        ".inst 0xe7900201 @ ldr r0, [r0, r1, lsl #4]\n"
        ".inst 0xe3a01002 @ mov r1, #2\n"
        ".inst 0xeb00cd8d @ bl #0x15a3f4\n"
        ".inst 0xe8bd4070 @ pop {r4, r5, r6, lr}\n"
        ".inst 0xe59f0008 @ ldr r0, [pc, #8]\n"
        ".inst 0xea067316 @ b #0x2c3a24\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0044d0f8 @ tail data\n"
        ".word 0x004c40f8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00126ddc, 76)
extern "C" __attribute__((naked)) void engine_func_00126ddc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe59f5034 @ ldr r5, [pc, #0x34]\n"
        ".inst 0xe5950014 @ ldr r0, [r5, #0x14]\n"
        ".inst 0xe1540000 @ cmp r4, r0\n"
        ".inst 0x2a000009 @ bhs #0x126e1c\n"
        ".inst 0xe59f0028 @ ldr r0, [pc, #0x28]\n"
        ".inst 0xeb06732a @ bl #0x2c3aa8\n"
        ".inst 0xe5950008 @ ldr r0, [r5, #8]\n"
        ".inst 0xe0641184 @ rsb r1, r4, r4, lsl #3\n"
        ".inst 0xe7900201 @ ldr r0, [r0, r1, lsl #4]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xeb00cd78 @ bl #0x15a3f4\n"
        ".inst 0xe8bd4070 @ pop {r4, r5, r6, lr}\n"
        ".inst 0xe59f0008 @ ldr r0, [pc, #8]\n"
        ".inst 0xea067301 @ b #0x2c3a24\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0044d0f8 @ tail data\n"
        ".word 0x004c40f8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00128cbc, 76)
extern "C" __attribute__((naked)) void func_00128cbc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59fc034 @ ldr ip, [pc, #0x34]\n"
        ".inst 0xe5a4c080 @ str ip, [r4, #0x80]!\n"
        ".inst 0xe284e004 @ add lr, r4, #4\n"
        ".inst 0xe88e000e @ stm lr, {r1, r2, r3}\n"
        ".inst 0xe3a0200c @ mov r2, #0xc\n"
        ".inst 0xe5840014 @ str r0, [r4, #0x14]\n"
        ".inst 0xe59f0020 @ ldr r0, [pc, #0x20]\n"
        ".inst 0xe1821281 @ orr r1, r2, r1, lsl #5\n"
        ".inst 0xe5841010 @ str r1, [r4, #0x10]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x000b00c2 @ tail data\n"
        ".word 0x00471b64 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00129c70, 76)
extern "C" __attribute__((naked)) void battle_func_00129c70() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a00000 @ mov r0, r0\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe59f0034 @ ldr r0, [pc, #0x34]\n"
        ".inst 0xe3510007 @ cmp r1, #7\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xe590601c @ ldr r6, [r0, #0x1c]\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0x2a000007 @ bhs #0x129cb4\n"
        ".inst 0xe1a00006 @ mov r0, r6\n"
        ".inst 0xeb066782 @ bl #0x2c3aa8\n"
        ".inst 0xe0861105 @ add r1, r6, r5, lsl #2\n"
        ".inst 0xe1a00006 @ mov r0, r6\n"
        ".inst 0xe5915010 @ ldr r5, [r1, #0x10]\n"
        ".inst 0xe5814010 @ str r4, [r1, #0x10]\n"
        ".inst 0xeb06675c @ bl #0x2c3a24\n"
        ".inst 0xe1a00005 @ mov r0, r5\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00471a70 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001371a0, 76)
extern "C" __attribute__((naked)) void func_001371a0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d43f0 @ push {r4, r5, r6, r7, r8, sb, lr}\n"
        ".inst 0xe24dd024 @ sub sp, sp, #0x24\n"
        ".inst 0xe1a07000 @ mov r7, r0\n"
        ".inst 0xe28de040 @ add lr, sp, #0x40\n"
        ".inst 0xe1a08001 @ mov r8, r1\n"
        ".inst 0xe1a09002 @ mov sb, r2\n"
        ".inst 0xe89e1077 @ ldm lr, {r0, r1, r2, r4, r5, r6, ip}\n"
        ".inst 0xe28de004 @ add lr, sp, #4\n"
        ".inst 0xe58d3000 @ str r3, [sp]\n"
        ".inst 0xe1a03009 @ mov r3, sb\n"
        ".inst 0xe88e1077 @ stm lr, {r0, r1, r2, r4, r5, r6, ip}\n"
        ".inst 0xe1a02008 @ mov r2, r8\n"
        ".inst 0xe1a01007 @ mov r1, r7\n"
        ".inst 0xe59f000c @ ldr r0, [pc, #0xc]\n"
        ".inst 0xe590009c @ ldr r0, [r0, #0x9c]\n"
        ".inst 0xeb000153 @ bl #0x137730\n"
        ".inst 0xe28dd024 @ add sp, sp, #0x24\n"
        ".inst 0xe8bd83f0 @ pop {r4, r5, r6, r7, r8, sb, pc}\n"
        ".word 0x004c6290 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013728c, 76)
extern "C" __attribute__((naked)) void func_0013728c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe24dd018 @ sub sp, sp, #0x18\n"
        ".inst 0xe28de028 @ add lr, sp, #0x28\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xe1a06002 @ mov r6, r2\n"
        ".inst 0xe89e1007 @ ldm lr, {r0, r1, r2, ip}\n"
        ".inst 0xe28de004 @ add lr, sp, #4\n"
        ".inst 0xe58d3000 @ str r3, [sp]\n"
        ".inst 0xe1a03006 @ mov r3, r6\n"
        ".inst 0xe88e1007 @ stm lr, {r0, r1, r2, ip}\n"
        ".inst 0xe1a02005 @ mov r2, r5\n"
        ".inst 0xe1a01004 @ mov r1, r4\n"
        ".inst 0xe59f000c @ ldr r0, [pc, #0xc]\n"
        ".inst 0xe590009c @ ldr r0, [r0, #0x9c]\n"
        ".inst 0xeb002db3 @ bl #0x14299c\n"
        ".inst 0xe28dd018 @ add sp, sp, #0x18\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x004c6290 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013e224, 76)
extern "C" __attribute__((naked)) void func_0013e224() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xe3a02004 @ mov r2, #4\n"
        ".inst 0xe3a01010 @ mov r1, #0x10\n"
        ".inst 0xe5903008 @ ldr r3, [r0, #8]\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe12fff33 @ blx r3\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000005 @ beq #0x13e268\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe5804004 @ str r4, [r0, #4]\n"
        ".inst 0xe5c01008 @ strb r1, [r0, #8]\n"
        ".inst 0xe59f1008 @ ldr r1, [pc, #8]\n"
        ".inst 0xe5801000 @ str r1, [r0]\n"
        ".inst 0xe580500c @ str r5, [r0, #0xc]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00421104 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013e558, 76)
extern "C" __attribute__((naked)) void func_0013e558() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xe3a02004 @ mov r2, #4\n"
        ".inst 0xe3a01010 @ mov r1, #0x10\n"
        ".inst 0xe5903008 @ ldr r3, [r0, #8]\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe12fff33 @ blx r3\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000005 @ beq #0x13e59c\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe5804004 @ str r4, [r0, #4]\n"
        ".inst 0xe5c01008 @ strb r1, [r0, #8]\n"
        ".inst 0xe59f1008 @ ldr r1, [pc, #8]\n"
        ".inst 0xe5801000 @ str r1, [r0]\n"
        ".inst 0xe580500c @ str r5, [r0, #0xc]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0042114c @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013e60c, 76)
extern "C" __attribute__((naked)) void func_0013e60c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xe3a02004 @ mov r2, #4\n"
        ".inst 0xe3a01010 @ mov r1, #0x10\n"
        ".inst 0xe5903008 @ ldr r3, [r0, #8]\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe12fff33 @ blx r3\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000005 @ beq #0x13e650\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe5804004 @ str r4, [r0, #4]\n"
        ".inst 0xe5c01008 @ strb r1, [r0, #8]\n"
        ".inst 0xe59f1008 @ ldr r1, [pc, #8]\n"
        ".inst 0xe5801000 @ str r1, [r0]\n"
        ".inst 0xe580500c @ str r5, [r0, #0xc]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x004211f4 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001448b4, 76)
extern "C" __attribute__((naked)) void func_001448b4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xebff8dc9 @ bl #0x127fe8\n"
        ".inst 0xebff8ddb @ bl #0x128034\n"
        ".inst 0xebffce6f @ bl #0x138288\n"
        ".inst 0xe5942004 @ ldr r2, [r4, #4]\n"
        ".inst 0xe1c400d8 @ ldrd r0, r1, [r4, #8]\n"
        ".inst 0xe12fff32 @ blx r2\n"
        ".inst 0xe5941000 @ ldr r1, [r4]\n"
        ".inst 0xe594000c @ ldr r0, [r4, #0xc]\n"
        ".inst 0xe12fff31 @ blx r1\n"
        ".inst 0xe5d40014 @ ldrb r0, [r4, #0x14]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x15940010 @ ldrne r0, [r4, #0x10]\n"
        ".inst 0x1bffce68 @ blne #0x138294\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xe1a00000 @ mov r0, r0\n"
        ".inst 0xef000009 @ svc #9\n"
        ".inst 0xe12fff1e @ bx lr\n"
    );
}

// DECOMP_FUNC(0x00145e30, 76)
extern "C" __attribute__((naked)) void func_00145e30() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1040 @ ldr r1, [pc, #0x40]\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe2804a01 @ add r4, r0, #0x1000\n"
        ".inst 0xe7d11000 @ ldrb r1, [r1, r0]\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x0dd40a76 @ vldreq s1, [r4, #0x1d8]\n"
        ".inst 0x0ef40a40 @ vcmpeq.f32 s1, s0\n"
        ".inst 0x0ef1fa10 @ vmrseq apsr_nzcv, fpscr\n"
        ".inst 0x0a000005 @ beq #0x145e6c\n"
        ".inst 0xed840a76 @ vstr s0, [r4, #0x1d8]\n"
        ".inst 0xe590252c @ ldr r2, [r0, #0x52c]\n"
        ".inst 0xe2801a01 @ add r1, r0, #0x1000\n"
        ".inst 0xe2811f73 @ add r1, r1, #0x1cc\n"
        ".inst 0xe1a00002 @ mov r0, r2\n"
        ".inst 0xeb05c207 @ bl #0x2b668c\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe5c401dc @ strb r0, [r4, #0x1dc]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x000011dc @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014ff34, 76)
extern "C" __attribute__((naked)) void func_0014ff34() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f3034 @ ldr r3, [pc, #0x34]\n"
        ".inst 0xe3a02000 @ mov r2, #0\n"
        ".inst 0xe5a43080 @ str r3, [r4, #0x80]!\n"
        ".inst 0xe5841004 @ str r1, [r4, #4]\n"
        ".inst 0xe584000c @ str r0, [r4, #0xc]\n"
        ".inst 0xe59f0024 @ ldr r0, [pc, #0x24]\n"
        ".inst 0xe1821701 @ orr r1, r2, r1, lsl #14\n"
        ".inst 0xe3811002 @ orr r1, r1, #2\n"
        ".inst 0xe5841008 @ str r1, [r4, #8]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00400042 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00150ddc, 76)
extern "C" __attribute__((naked)) void func_00150ddc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4038 @ push {r3, r4, r5, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe3a05000 @ mov r5, #0\n"
        ".inst 0xe1a0100d @ mov r1, sp\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xebfff2da @ bl #0x14d960\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0xe320f000 @ nop\n"
        ".inst 0x0a000008 @ beq #0x150e24\n"
        ".inst 0xe59d0000 @ ldr r0, [sp]\n"
        ".inst 0xeb000df0 @ bl #0x1545cc\n"
        ".inst 0xee075fba @ mcr p15, #0, r5, c7, c10, #5\n"
        ".inst 0xe59d1000 @ ldr r1, [sp]\n"
        ".inst 0xe28400b4 @ add r0, r4, #0xb4\n"
        ".inst 0xebfff32b @ bl #0x14dac8\n"
        ".inst 0xe320f000 @ nop\n"
        ".inst 0xe320f000 @ nop\n"
        ".inst 0xeafffff0 @ b #0x150de8\n"
        ".inst 0xe8bd8038 @ pop {r3, r4, r5, pc}\n"
    );
}

// DECOMP_FUNC(0x001ad888, 76)
extern "C" __attribute__((naked)) void engine_func_001ad888() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe59f503c @ ldr r5, [pc, #0x3c]\n"
        ".inst 0xe1d500d1 @ ldrsb r0, [r5, #1]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0xca000008 @ bgt #0x1ad8c0\n"
        ".inst 0xe3a0001a @ mov r0, #0x1a\n"
        ".inst 0xeb045d60 @ bl #0x2c4e28\n"
        ".inst 0xe3a04000 @ mov r4, #0\n"
        ".inst 0xe1a01004 @ mov r1, r4\n"
        ".inst 0xe3a0001a @ mov r0, #0x1a\n"
        ".inst 0xeb046080 @ bl #0x2c5ab8\n"
        ".inst 0xe2844001 @ add r4, r4, #1\n"
        ".inst 0xe3540003 @ cmp r4, #3\n"
        ".inst 0xbafffff9 @ blt #0x1ad8a8\n"
        ".inst 0xe5d50001 @ ldrb r0, [r5, #1]\n"
        ".inst 0xe2800001 @ add r0, r0, #1\n"
        ".inst 0xe5c50001 @ strb r0, [r5, #1]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0044e140 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001db464, 76)
extern "C" __attribute__((naked)) void camp_func_001db464() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe3a04000 @ mov r4, #0\n"
        ".inst 0xe59f5038 @ ldr r5, [pc, #0x38]\n"
        ".inst 0xe5950004 @ ldr r0, [r5, #4]\n"
        ".inst 0xe8900006 @ ldm r0, {r1, r2}\n"
        ".inst 0xe5900018 @ ldr r0, [r0, #0x18]\n"
        ".inst 0xeb02202c @ bl #0x263534\n"
        ".inst 0xe2100102 @ ands r0, r0, #0x80000000\n"
        ".inst 0x4a000006 @ bmi #0x1db4a4\n"
        ".inst 0xe5950004 @ ldr r0, [r5, #4]\n"
        ".inst 0xe5901018 @ ldr r1, [r0, #0x18]\n"
        ".inst 0xe5910210 @ ldr r0, [r1, #0x210]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x01a00001 @ moveq r0, r1\n"
        ".inst 0x13a04001 @ movne r4, #1\n"
        ".inst 0x0b01770d @ bleq #0x2390dc\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00464fa8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001dcfbc, 76)
extern "C" __attribute__((naked)) void engine_func_001dcfbc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xeb02e7e5 @ bl #0x296f60\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xeb02e7e2 @ bl #0x296f60\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe3a00002 @ mov r0, #2\n"
        ".inst 0xeb02e7df @ bl #0x296f60\n"
        ".inst 0xe3540000 @ cmp r4, #0\n"
        ".inst 0xe1a02000 @ mov r2, r0\n"
        ".inst 0xb3a04000 @ movlt r4, #0\n"
        ".inst 0xe3520000 @ cmp r2, #0\n"
        ".inst 0xb3a02000 @ movlt r2, #0\n"
        ".inst 0xe1a01004 @ mov r1, r4\n"
        ".inst 0xe1a00005 @ mov r0, r5\n"
        ".inst 0xeb030d8f @ bl #0x2a0640\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0011d564, 80)
extern "C" __attribute__((naked)) void func_0011d564() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05002 @ mov r5, r2\n"
        ".inst 0xe1a06003 @ mov r6, r3\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f2030 @ ldr r2, [pc, #0x30]\n"
        ".inst 0xe5a42080 @ str r2, [r4, #0x80]!\n"
        ".inst 0xe1c400f4 @ strd r0, r1, [r4, #4]\n"
        ".inst 0xe59f0028 @ ldr r0, [pc, #0x28]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2101102 @ ands r1, r0, #0x80000000\n"
        ".inst 0x4a000004 @ bmi #0x11d5a8\n"
        ".inst 0xe594000c @ ldr r0, [r4, #0xc]\n"
        ".inst 0xe5850000 @ str r0, [r5]\n"
        ".inst 0xe5940010 @ ldr r0, [r4, #0x10]\n"
        ".inst 0xe5860000 @ str r0, [r6]\n"
        ".inst 0xe5940004 @ ldr r0, [r4, #4]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00020080 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d728, 80)
extern "C" __attribute__((naked)) void func_0011d728() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f5038 @ ldr r5, [pc, #0x38]\n"
        ".inst 0xe3a0c000 @ mov ip, #0\n"
        ".inst 0xe5a45080 @ str r5, [r4, #0x80]!\n"
        ".inst 0xe2846004 @ add r6, r4, #4\n"
        ".inst 0xe5843010 @ str r3, [r4, #0x10]\n"
        ".inst 0xe8861005 @ stm r6, {r0, r2, ip}\n"
        ".inst 0xe18c0702 @ orr r0, ip, r2, lsl #14\n"
        ".inst 0xe3800002 @ orr r0, r0, #2\n"
        ".inst 0xe1c401f4 @ strd r0, r1, [r4, #0x14]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x001f0084 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00126fcc, 80)
extern "C" __attribute__((naked)) void nn_sdk_func_00126fcc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1040 @ ldr r1, [pc, #0x40]\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe59f403c @ ldr r4, [pc, #0x3c]\n"
        ".inst 0xe5810010 @ str r0, [r1, #0x10]\n"
        ".inst 0xe59f0030 @ ldr r0, [pc, #0x30]\n"
        ".inst 0xe1a01004 @ mov r1, r4\n"
        ".inst 0xeb00092f @ bl #0x1294a8\n"
        ".inst 0xe1a0100f @ mov r1, pc\n"
        ".inst 0xe1b02fa0 @ lsrs r2, r0, #0x1f\n"
        ".inst 0x1b065346 @ blne #0x2bbd10\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xeb004e3d @ bl #0x13a8f4\n"
        ".inst 0xe1a0100f @ mov r1, pc\n"
        ".inst 0xe1b02fa0 @ lsrs r2, r0, #0x1f\n"
        ".inst 0x0a000001 @ beq #0x127010\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xea06533f @ b #0x2bbd10\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004d42c8 @ tail data\n"
        ".word 0x00000209 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00139ae0, 80)
extern "C" __attribute__((naked)) void camp_func_00139ae0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a00000 @ mov r0, r0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f3034 @ ldr r3, [pc, #0x34]\n"
        ".inst 0xe5a43080 @ str r3, [r4, #0x80]!\n"
        ".inst 0xe284c004 @ add ip, r4, #4\n"
        ".inst 0xe88c0006 @ stm ip, {r1, r2}\n"
        ".inst 0xe3a0200c @ mov r2, #0xc\n"
        ".inst 0xe5840010 @ str r0, [r4, #0x10]\n"
        ".inst 0xe59f0020 @ ldr r0, [pc, #0x20]\n"
        ".inst 0xe1821201 @ orr r1, r2, r1, lsl #4\n"
        ".inst 0xe584100c @ str r1, [r4, #0xc]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00010082 @ tail data\n"
        ".word 0x00472a50 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00146f88, 80)
extern "C" __attribute__((naked)) void func_00146f88() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xe1a04001 @ mov r4, r1\n"
        ".inst 0xeb05d186 @ bl #0x2bb5b4\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a00000b @ beq #0x146fd0\n"
        ".inst 0xe59f002c @ ldr r0, [pc, #0x2c]\n"
        ".inst 0xe3540902 @ cmp r4, #0x8000\n"
        ".inst 0x83a04902 @ movhi r4, #0x8000\n"
        ".inst 0xe19000b5 @ ldrh r0, [r0, r5]\n"
        ".inst 0xe0850100 @ add r0, r5, r0, lsl #2\n"
        ".inst 0xe2800a01 @ add r0, r0, #0x1000\n"
        ".inst 0xe59000a0 @ ldr r0, [r0, #0xa0]\n"
        ".inst 0xe1c042b2 @ strh r4, [r0, #0x22]\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe3811102 @ orr r1, r1, #0x80000000\n"
        ".inst 0xe5801000 @ str r1, [r0]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0000131e @ tail data\n"
    );
}

// DECOMP_FUNC(0x00147c98, 80)
extern "C" __attribute__((naked)) void func_00147c98() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05003 @ mov r5, r3\n"
        ".inst 0xe59d6010 @ ldr r6, [sp, #0x10]\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59fc034 @ ldr ip, [pc, #0x34]\n"
        ".inst 0xe3a03000 @ mov r3, #0\n"
        ".inst 0xe5a4c080 @ str ip, [r4, #0x80]!\n"
        ".inst 0xe584100c @ str r1, [r4, #0xc]\n"
        ".inst 0xe1c420f4 @ strd r2, r3, [r4, #4]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2101102 @ ands r1, r0, #0x80000000\n"
        ".inst 0x4a000004 @ bmi #0x147ce0\n"
        ".inst 0xe5940008 @ ldr r0, [r4, #8]\n"
        ".inst 0xe5860000 @ str r0, [r6]\n"
        ".inst 0xe5940010 @ ldr r0, [r4, #0x10]\n"
        ".inst 0xe5850000 @ str r0, [r5]\n"
        ".inst 0xe5940004 @ ldr r0, [r4, #4]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00130042 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014ad08, 80)
extern "C" __attribute__((naked)) void func_0014ad08() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe59f303c @ ldr r3, [pc, #0x3c]\n"
        ".inst 0xe3a04000 @ mov r4, #0\n"
        ".inst 0xe590c000 @ ldr ip, [r0]\n"
        ".inst 0xe35c0102 @ cmp ip, #0x80000000\n"
        ".inst 0x0a000002 @ beq #0x14ad30\n"
        ".inst 0xe35c0101 @ cmp ip, #0x40000000\n"
        ".inst 0x1a000007 @ bne #0x14ad4c\n"
        ".inst 0xea000003 @ b #0x14ad40\n"
        ".inst 0xe5933000 @ ldr r3, [r3]\n"
        ".inst 0xe12fff33 @ blx r3\n"
        ".inst 0xe1844000 @ orr r4, r4, r0\n"
        ".inst 0xea000002 @ b #0x14ad4c\n"
        ".inst 0xe5933004 @ ldr r3, [r3, #4]\n"
        ".inst 0xe12fff33 @ blx r3\n"
        ".inst 0xe1844000 @ orr r4, r4, r0\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0044e8d8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014c87c, 80)
extern "C" __attribute__((naked)) void ui_func_0014c87c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb001257 @ bl #0x1511e4\n"
        ".inst 0xe59f1038 @ ldr r1, [pc, #0x38]\n"
        ".inst 0xe3a02000 @ mov r2, #0\n"
        ".inst 0xe5802048 @ str r2, [r0, #0x48]\n"
        ".inst 0xe5801000 @ str r1, [r0]\n"
        ".inst 0xe2813030 @ add r3, r1, #0x30\n"
        ".inst 0xe580204c @ str r2, [r0, #0x4c]\n"
        ".inst 0xe5803044 @ str r3, [r0, #0x44]\n"
        ".inst 0xe58020d0 @ str r2, [r0, #0xd0]\n"
        ".inst 0xe58020d4 @ str r2, [r0, #0xd4]\n"
        ".inst 0xe59f1018 @ ldr r1, [pc, #0x18]\n"
        ".inst 0xe3a03008 @ mov r3, #8\n"
        ".inst 0xe3a02d0d @ mov r2, #0x340\n"
        ".inst 0xe28000d8 @ add r0, r0, #0xd8\n"
        ".inst 0xfa05e5a6 @ blx #0x2c5f58\n"
        ".inst 0xe24000d8 @ sub r0, r0, #0xd8\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00421a5c @ tail data\n"
        ".word 0x00150ef8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014feac, 80)
extern "C" __attribute__((naked)) void func_0014feac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f5038 @ ldr r5, [pc, #0x38]\n"
        ".inst 0xe3a0c000 @ mov ip, #0\n"
        ".inst 0xe5a45080 @ str r5, [r4, #0x80]!\n"
        ".inst 0xe2846004 @ add r6, r4, #4\n"
        ".inst 0xe5843010 @ str r3, [r4, #0x10]\n"
        ".inst 0xe8861005 @ stm r6, {r0, r2, ip}\n"
        ".inst 0xe18c0702 @ orr r0, ip, r2, lsl #14\n"
        ".inst 0xe3800002 @ orr r0, r0, #2\n"
        ".inst 0xe1c401f4 @ strd r0, r1, [r4, #0x14]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x001e0084 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0015d3fc, 80)
extern "C" __attribute__((naked)) void func_0015d3fc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xeb057869 @ bl #0x2bb5b4\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a00000b @ beq #0x15d444\n"
        ".inst 0xe59f002c @ ldr r0, [pc, #0x2c]\n"
        ".inst 0xe19000b4 @ ldrh r0, [r0, r4]\n"
        ".inst 0xe2000001 @ and r0, r0, #1\n"
        ".inst 0xe0800080 @ add r0, r0, r0, lsl #1\n"
        ".inst 0xe0840280 @ add r0, r4, r0, lsl #5\n"
        ".inst 0xe0800105 @ add r0, r0, r5, lsl #2\n"
        ".inst 0xe2800a01 @ add r0, r0, #0x1000\n"
        ".inst 0xe59000b0 @ ldr r0, [r0, #0xb0]\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe3811202 @ orr r1, r1, #0x20000000\n"
        ".inst 0xe5801000 @ str r1, [r0]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0000131a @ tail data\n"
    );
}

// DECOMP_FUNC(0x0015e458, 80)
extern "C" __attribute__((naked)) void func_0015e458() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe3a05000 @ mov r5, #0\n"
        ".inst 0xe5815000 @ str r5, [r1]\n"
        ".inst 0xe5c15017 @ strb r5, [r1, #0x17]\n"
        ".inst 0xe5c15015 @ strb r5, [r1, #0x15]\n"
        ".inst 0xe1a04001 @ mov r4, r1\n"
        ".inst 0xe5815008 @ str r5, [r1, #8]\n"
        ".inst 0xeb05737d @ bl #0x2bb270\n"
        ".inst 0xe1a01004 @ mov r1, r4\n"
        ".inst 0xebfff88e @ bl #0x15c6bc\n"
        ".inst 0xe594300c @ ldr r3, [r4, #0xc]\n"
        ".inst 0xe5c45014 @ strb r5, [r4, #0x14]\n"
        ".inst 0xe3530000 @ cmp r3, #0\n"
        ".inst 0x0a000004 @ beq #0x15e4a4\n"
        ".inst 0xe5942010 @ ldr r2, [r4, #0x10]\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe8bd4070 @ pop {r4, r5, r6, lr}\n"
        ".inst 0xe3a01003 @ mov r1, #3\n"
        ".inst 0xe12fff13 @ bx r3\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0015f2b8, 80)
extern "C" __attribute__((naked)) void func_0015f2b8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xeb0570ba @ bl #0x2bb5b4\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a00000b @ beq #0x15f300\n"
        ".inst 0xe59f002c @ ldr r0, [pc, #0x2c]\n"
        ".inst 0xe19000b4 @ ldrh r0, [r0, r4]\n"
        ".inst 0xe2000001 @ and r0, r0, #1\n"
        ".inst 0xe0800080 @ add r0, r0, r0, lsl #1\n"
        ".inst 0xe0840280 @ add r0, r4, r0, lsl #5\n"
        ".inst 0xe0800105 @ add r0, r0, r5, lsl #2\n"
        ".inst 0xe2800a01 @ add r0, r0, #0x1000\n"
        ".inst 0xe59000b0 @ ldr r0, [r0, #0xb0]\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe3811010 @ orr r1, r1, #0x10\n"
        ".inst 0xe5801000 @ str r1, [r0]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0000131a @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ed6d0, 80)
extern "C" __attribute__((naked)) void engine_func_001ed6d0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe59f5040 @ ldr r5, [pc, #0x40]\n"
        ".inst 0xe1d500d0 @ ldrsb r0, [r5]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0xca000009 @ bgt #0x1ed70c\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe3a0000d @ mov r0, #0xd\n"
        ".inst 0xeb036104 @ bl #0x2c5b04\n"
        ".inst 0xe3a04000 @ mov r4, #0\n"
        ".inst 0xe1a01004 @ mov r1, r4\n"
        ".inst 0xe3a0000d @ mov r0, #0xd\n"
        ".inst 0xeb02e2c4 @ bl #0x2a6214\n"
        ".inst 0xe2844001 @ add r4, r4, #1\n"
        ".inst 0xe3540005 @ cmp r4, #5\n"
        ".inst 0xbafffff9 @ blt #0x1ed6f4\n"
        ".inst 0xe5d50000 @ ldrb r0, [r5]\n"
        ".inst 0xe2800001 @ add r0, r0, #1\n"
        ".inst 0xe5c50000 @ strb r0, [r5]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0043dcc8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0010f564, 84)
extern "C" __attribute__((naked)) void nn_sdk_func_0010f564() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0044 @ ldr r0, [pc, #0x44]\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x1a00000b @ bne #0x10f5a8\n"
        ".inst 0xeb06c7fc @ bl #0x2c1570\n"
        ".inst 0xe1b01fa0 @ lsrs r1, r0, #0x1f\n"
        ".inst 0x1a000009 @ bne #0x10f5ac\n"
        ".inst 0xe59f0028 @ ldr r0, [pc, #0x28]\n"
        ".inst 0xeb06cf40 @ bl #0x2c3290\n"
        ".inst 0xe1a02000 @ mov r2, r0\n"
        ".inst 0xe59f101c @ ldr r1, [pc, #0x1c]\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe3a03000 @ mov r3, #0\n"
        ".inst 0xeb06c7e6 @ bl #0x2c153c\n"
        ".inst 0xe1b01fa0 @ lsrs r1, r0, #0x1f\n"
        ".inst 0x1a000000 @ bne #0x10f5ac\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00472a58 @ tail data\n"
        ".word 0x0040b59d @ tail data\n"
    );
}

// DECOMP_FUNC(0x0010f888, 84)
extern "C" __attribute__((naked)) void func_0010f888() {
    asm volatile(
        ".arm\n"
        ".inst 0xe52de004 @ str lr, [sp, #-4]!\n"
        ".inst 0xe24dd014 @ sub sp, sp, #0x14\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe58d0008 @ str r0, [sp, #8]\n"
        ".inst 0xe59f0038 @ ldr r0, [pc, #0x38]\n"
        ".inst 0xe5901008 @ ldr r1, [r0, #8]\n"
        ".inst 0xe58d100c @ str r1, [sp, #0xc]\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe28d0008 @ add r0, sp, #8\n"
        ".inst 0xeb000e4f @ bl #0x1131f0\n"
        ".inst 0xe59d1008 @ ldr r1, [sp, #8]\n"
        ".inst 0xe3a03001 @ mov r3, #1\n"
        ".inst 0xe28d200c @ add r2, sp, #0xc\n"
        ".inst 0xe1a0000d @ mov r0, sp\n"
        ".inst 0xef00003a @ svc #0x3a\n"
        ".inst 0xe59d0008 @ ldr r0, [sp, #8]\n"
        ".inst 0xef000023 @ svc #0x23\n"
        ".inst 0xe59d0000 @ ldr r0, [sp]\n"
        ".inst 0xe28dd014 @ add sp, sp, #0x14\n"
        ".inst 0xe49df004 @ pop {pc}\n"
        ".word 0x0040b684 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d610, 84)
extern "C" __attribute__((naked)) void func_0011d610() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59fc03c @ ldr ip, [pc, #0x3c]\n"
        ".inst 0xe3a03000 @ mov r3, #0\n"
        ".inst 0xe5a4c080 @ str ip, [r4, #0x80]!\n"
        ".inst 0xe284e004 @ add lr, r4, #4\n"
        ".inst 0xe584200c @ str r2, [r4, #0xc]\n"
        ".inst 0xe88e000a @ stm lr, {r1, r3}\n"
        ".inst 0xe1831701 @ orr r1, r3, r1, lsl #14\n"
        ".inst 0xe5840014 @ str r0, [r4, #0x14]\n"
        ".inst 0xe59f0020 @ ldr r0, [pc, #0x20]\n"
        ".inst 0xe3811002 @ orr r1, r1, #2\n"
        ".inst 0xe5841010 @ str r1, [r4, #0x10]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x002c0044 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d664, 84)
extern "C" __attribute__((naked)) void func_0011d664() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59fc03c @ ldr ip, [pc, #0x3c]\n"
        ".inst 0xe3a03000 @ mov r3, #0\n"
        ".inst 0xe5a4c080 @ str ip, [r4, #0x80]!\n"
        ".inst 0xe284e004 @ add lr, r4, #4\n"
        ".inst 0xe584200c @ str r2, [r4, #0xc]\n"
        ".inst 0xe88e000a @ stm lr, {r1, r3}\n"
        ".inst 0xe1831701 @ orr r1, r3, r1, lsl #14\n"
        ".inst 0xe5840014 @ str r0, [r4, #0x14]\n"
        ".inst 0xe59f0020 @ ldr r0, [pc, #0x20]\n"
        ".inst 0xe3811002 @ orr r1, r1, #2\n"
        ".inst 0xe5841010 @ str r1, [r4, #0x10]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00270044 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013b148, 84)
extern "C" __attribute__((naked)) void func_0013b148() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d40f0 @ push {r4, r5, r6, r7, lr}\n"
        ".inst 0xe24dd00c @ sub sp, sp, #0xc\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xe1a06002 @ mov r6, r2\n"
        ".inst 0xe1a07003 @ mov r7, r3\n"
        ".inst 0xeb060154 @ bl #0x2bb6b8\n"
        ".inst 0xe28dc004 @ add ip, sp, #4\n"
        ".inst 0xe1a03007 @ mov r3, r7\n"
        ".inst 0xe1a02006 @ mov r2, r6\n"
        ".inst 0xe1a01005 @ mov r1, r5\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe58dc000 @ str ip, [sp]\n"
        ".inst 0xeb003439 @ bl #0x148268\n"
        ".inst 0xe1a0100f @ mov r1, pc\n"
        ".inst 0xe1b02fa0 @ lsrs r2, r0, #0x1f\n"
        ".inst 0x1b0618d9 @ blne #0x2c14f4\n"
        ".inst 0xeb06012d @ bl #0x2bb648\n"
        ".inst 0xe1dd00d4 @ ldrsb r0, [sp, #4]\n"
        ".inst 0xe28dd00c @ add sp, sp, #0xc\n"
        ".inst 0xe8bd80f0 @ pop {r4, r5, r6, r7, pc}\n"
    );
}

// DECOMP_FUNC(0x00146758, 84)
extern "C" __attribute__((naked)) void func_00146758() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4030 @ push {r4, r5, lr}\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xe59f1040 @ ldr r1, [pc, #0x40]\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe59f0034 @ ldr r0, [pc, #0x34]\n"
        ".inst 0xe24dd00c @ sub sp, sp, #0xc\n"
        ".inst 0xe591c008 @ ldr ip, [r1, #8]\n"
        ".inst 0xe35c0000 @ cmp ip, #0\n"
        ".inst 0x03a01000 @ moveq r1, #0\n"
        ".inst 0x01c310b0 @ strheq r1, [r3]\n"
        ".inst 0x0a000005 @ beq #0x14679c\n"
        ".inst 0xe1cd20f0 @ strd r2, r3, [sp]\n"
        ".inst 0xe1a03005 @ mov r3, r5\n"
        ".inst 0xe3a02000 @ mov r2, #0\n"
        ".inst 0xe1a01004 @ mov r1, r4\n"
        ".inst 0xe1a0000c @ mov r0, ip\n"
        ".inst 0xeb00236b @ bl #0x14f54c\n"
        ".inst 0xe28dd00c @ add sp, sp, #0xc\n"
        ".inst 0xe8bd8030 @ pop {r4, r5, pc}\n"
        ".word 0xc8a0a7f8 @ tail data\n"
        ".word 0x0044e458 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00147020, 84)
extern "C" __attribute__((naked)) void func_00147020() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xe1a04001 @ mov r4, r1\n"
        ".inst 0xeb05d160 @ bl #0x2bb5b4\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a00000b @ beq #0x147068\n"
        ".inst 0xe59f0030 @ ldr r0, [pc, #0x30]\n"
        ".inst 0xe3540902 @ cmp r4, #0x8000\n"
        ".inst 0x259f4024 @ ldrhs r4, [pc, #0x24]\n"
        ".inst 0xe19000b5 @ ldrh r0, [r0, r5]\n"
        ".inst 0xe0850100 @ add r0, r5, r0, lsl #2\n"
        ".inst 0xe2800a01 @ add r0, r0, #0x1000\n"
        ".inst 0xe59000a0 @ ldr r0, [r0, #0xa0]\n"
        ".inst 0xe1c041bc @ strh r4, [r0, #0x1c]\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe3811202 @ orr r1, r1, #0x20000000\n"
        ".inst 0xe5801000 @ str r1, [r0]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00007fff @ tail data\n"
        ".word 0x0000131e @ tail data\n"
    );
}

// DECOMP_FUNC(0x00147bb8, 84)
extern "C" __attribute__((naked)) void func_00147bb8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d41f0 @ push {r4, r5, r6, r7, r8, lr}\n"
        ".inst 0xee1d5f70 @ mrc p15, #0, r5, c13, c0, #3\n"
        ".inst 0xe59f4040 @ ldr r4, [pc, #0x40]\n"
        ".inst 0xe3a0c000 @ mov ip, #0\n"
        ".inst 0xe5a54080 @ str r4, [r5, #0x80]!\n"
        ".inst 0xe2856004 @ add r6, r5, #4\n"
        ".inst 0xe886000a @ stm r6, {r1, r3}\n"
        ".inst 0xee1d1f70 @ mrc p15, #0, r1, c13, c0, #3\n"
        ".inst 0xe2814d06 @ add r4, r1, #0x180\n"
        ".inst 0xe18c1703 @ orr r1, ip, r3, lsl #14\n"
        ".inst 0xe3811002 @ orr r1, r1, #2\n"
        ".inst 0xe1c460d0 @ ldrd r6, r7, [r4]\n"
        ".inst 0xe8840006 @ stm r4, {r1, r2}\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xe1c460f0 @ strd r6, r7, [r4]\n"
        ".inst 0xa5950004 @ ldrge r0, [r5, #4]\n"
        ".inst 0xe8bd81f0 @ pop {r4, r5, r6, r7, r8, pc}\n"
        ".word 0x00040080 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014fbe8, 84)
extern "C" __attribute__((naked)) void func_0014fbe8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xe2800018 @ add r0, r0, #0x18\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xeb05d17a @ bl #0x2c41e8\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe3a06000 @ mov r6, #0\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000001 @ beq #0x14fc14\n"
        ".inst 0xef000023 @ svc #0x23\n"
        ".inst 0xe5846000 @ str r6, [r4]\n"
        ".inst 0xe2850010 @ add r0, r5, #0x10\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xeb05d171 @ bl #0x2c41e8\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000001 @ beq #0x14fc34\n"
        ".inst 0xef000023 @ svc #0x23\n"
        ".inst 0xe5846000 @ str r6, [r4]\n"
        ".inst 0xe1a00005 @ mov r0, r5\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0015f00c, 84)
extern "C" __attribute__((naked)) void func_0015f00c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xeb057165 @ bl #0x2bb5b4\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a00000c @ beq #0x15f058\n"
        ".inst 0xe59f0030 @ ldr r0, [pc, #0x30]\n"
        ".inst 0xe19000b4 @ ldrh r0, [r0, r4]\n"
        ".inst 0xe2000001 @ and r0, r0, #1\n"
        ".inst 0xe0800080 @ add r0, r0, r0, lsl #1\n"
        ".inst 0xe0840280 @ add r0, r4, r0, lsl #5\n"
        ".inst 0xe0800105 @ add r0, r0, r5, lsl #2\n"
        ".inst 0xe2800a01 @ add r0, r0, #0x1000\n"
        ".inst 0xe59010b0 @ ldr r1, [r0, #0xb0]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe5c100a0 @ strb r0, [r1, #0xa0]\n"
        ".inst 0xe5912000 @ ldr r2, [r1]\n"
        ".inst 0xe3822801 @ orr r2, r2, #0x10000\n"
        ".inst 0xe5812000 @ str r2, [r1]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0000131a @ tail data\n"
    );
}

// DECOMP_FUNC(0x001924a8, 84)
extern "C" __attribute__((naked)) void engine_func_001924a8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xeb03fdfc @ bl #0x291cac\n"
        ".inst 0xe59f5038 @ ldr r5, [pc, #0x38]\n"
        ".inst 0xe5954000 @ ldr r4, [r5]\n"
        ".inst 0xe3540000 @ cmp r4, #0\n"
        ".inst 0x0a000007 @ beq #0x1924e8\n"
        ".inst 0xe2840a12 @ add r0, r4, #0x12000\n"
        ".inst 0xe3a01008 @ mov r1, #8\n"
        ".inst 0xe2800fcd @ add r0, r0, #0x334\n"
        ".inst 0xeb08c17d @ bl #0x3c2ad0\n"
        ".inst 0xe2840040 @ add r0, r4, #0x40\n"
        ".inst 0xeb081e1a @ bl #0x399d4c\n"
        ".inst 0xe2840040 @ add r0, r4, #0x40\n"
        ".inst 0xeb082641 @ bl #0x39bdf0\n"
        ".inst 0xe5950000 @ ldr r0, [r5]\n"
        ".inst 0xe3a01001 @ mov r1, #1\n"
        ".inst 0xe5c0100a @ strb r1, [r0, #0xa]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x0044cdf0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001a14e4, 84)
extern "C" __attribute__((naked)) void camp_func_001a14e4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000010 @ beq #0x1a1530\n"
        ".inst 0xe3500f7d @ cmp r0, #0x1f4\n"
        ".inst 0x83a00000 @ movhi r0, #0\n"
        ".inst 0x8a00000d @ bhi #0x1a1530\n"
        ".inst 0xe59f1034 @ ldr r1, [pc, #0x34]\n"
        ".inst 0xe1a02fc0 @ asr r2, r0, #0x1f\n"
        ".inst 0xe3a03001 @ mov r3, #1\n"
        ".inst 0xe0802ea2 @ add r2, r0, r2, lsr #29\n"
        ".inst 0xe5911004 @ ldr r1, [r1, #4]\n"
        ".inst 0xe2811088 @ add r1, r1, #0x88\n"
        ".inst 0xe08111c2 @ add r1, r1, r2, asr #3\n"
        ".inst 0xe2811b92 @ add r1, r1, #0x24800\n"
        ".inst 0xe3c22007 @ bic r2, r2, #7\n"
        ".inst 0xe2811fcf @ add r1, r1, #0x33c\n"
        ".inst 0xe0402002 @ sub r2, r0, r2\n"
        ".inst 0xe5d10000 @ ldrb r0, [r1]\n"
        ".inst 0xe0100213 @ ands r0, r0, r3, lsl r2\n"
        ".inst 0x13a00001 @ movne r0, #1\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0043e2a8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001a8104, 84)
extern "C" __attribute__((naked)) void func_001a8104() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xeb0419bf @ bl #0x2ae818\n"
        ".inst 0xe1a06000 @ mov r6, r0\n"
        ".inst 0xe5950000 @ ldr r0, [r5]\n"
        ".inst 0xeb0419bc @ bl #0x2ae818\n"
        ".inst 0xe1d612b8 @ ldrh r1, [r6, #0x28]\n"
        ".inst 0xe1d002b8 @ ldrh r0, [r0, #0x28]\n"
        ".inst 0xe0510000 @ subs r0, r1, r0\n"
        ".inst 0x1a000007 @ bne #0x1a8154\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xeb0419b6 @ bl #0x2ae818\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5950000 @ ldr r0, [r5]\n"
        ".inst 0xeb0419b3 @ bl #0x2ae818\n"
        ".inst 0xe1d422b4 @ ldrh r2, [r4, #0x24]\n"
        ".inst 0xe1d002b4 @ ldrh r0, [r0, #0x24]\n"
        ".inst 0xe0420000 @ sub r0, r2, r0\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x001dc7b4, 84)
extern "C" __attribute__((naked)) void engine_func_001dc7b4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe24dd008 @ sub sp, sp, #8\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xeb02c5dd @ bl #0x28df3c\n"
        ".inst 0xe3a0400b @ mov r4, #0xb\n"
        ".inst 0xeb02a827 @ bl #0x28686c\n"
        ".inst 0xe1a06000 @ mov r6, r0\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xeb02e9e1 @ bl #0x296f60\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xeb02b397 @ bl #0x289640\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe1a02000 @ mov r2, r0\n"
        ".inst 0xe58d1000 @ str r1, [sp]\n"
        ".inst 0xe58d1004 @ str r1, [sp, #4]\n"
        ".inst 0xe1a03004 @ mov r3, r4\n"
        ".inst 0xe1a01005 @ mov r1, r5\n"
        ".inst 0xe1a00006 @ mov r0, r6\n"
        ".inst 0xeb02a849 @ bl #0x286928\n"
        ".inst 0xe28dd008 @ add sp, sp, #8\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x001eca84, 84)
extern "C" __attribute__((naked)) void engine_func_001eca84() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe24dd008 @ sub sp, sp, #8\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xeb028529 @ bl #0x28df3c\n"
        ".inst 0xe3a0400e @ mov r4, #0xe\n"
        ".inst 0xeb026773 @ bl #0x28686c\n"
        ".inst 0xe1a06000 @ mov r6, r0\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xeb02a92d @ bl #0x296f60\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xeb0272e3 @ bl #0x289640\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe1a02000 @ mov r2, r0\n"
        ".inst 0xe58d1000 @ str r1, [sp]\n"
        ".inst 0xe58d1004 @ str r1, [sp, #4]\n"
        ".inst 0xe1a03004 @ mov r3, r4\n"
        ".inst 0xe1a01005 @ mov r1, r5\n"
        ".inst 0xe1a00006 @ mov r0, r6\n"
        ".inst 0xeb026795 @ bl #0x286928\n"
        ".inst 0xe28dd008 @ add sp, sp, #8\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x001f4a54, 84)
extern "C" __attribute__((naked)) void engine_func_001f4a54() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04001 @ mov r4, r1\n"
        ".inst 0xe5911044 @ ldr r1, [r1, #0x44]\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe3a03801 @ mov r3, #0x10000\n"
        ".inst 0xeb018cfc @ bl #0x257e60\n"
        ".inst 0xe5942000 @ ldr r2, [r4]\n"
        ".inst 0xe3a01402 @ mov r1, #0x2000000\n"
        ".inst 0xe3a05001 @ mov r5, #1\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe582100c @ str r1, [r2, #0xc]\n"
        ".inst 0xe5941000 @ ldr r1, [r4]\n"
        ".inst 0xe581503c @ str r5, [r1, #0x3c]\n"
        ".inst 0xe5941000 @ ldr r1, [r4]\n"
        ".inst 0xe5815040 @ str r5, [r1, #0x40]\n"
        ".inst 0xe5941000 @ ldr r1, [r4]\n"
        ".inst 0xe5810038 @ str r0, [r1, #0x38]\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xeb032323 @ bl #0x2bd730\n"
        ".inst 0xe5c45048 @ strb r5, [r4, #0x48]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x001f6384, 84)
extern "C" __attribute__((naked)) void engine_func_001f6384() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1d000b0 @ ldrh r0, [r0]\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xeb02f90c @ bl #0x2b47cc\n"
        ".inst 0xe1a06000 @ mov r6, r0\n"
        ".inst 0xe1d500b0 @ ldrh r0, [r5]\n"
        ".inst 0xeb02f909 @ bl #0x2b47cc\n"
        ".inst 0xe1d006f6 @ ldrsh r0, [r0, #0x66]\n"
        ".inst 0xe1d616f6 @ ldrsh r1, [r6, #0x66]\n"
        ".inst 0xe0500001 @ subs r0, r0, r1\n"
        ".inst 0x1a000007 @ bne #0x1f63d4\n"
        ".inst 0xe1d400b0 @ ldrh r0, [r4]\n"
        ".inst 0xeb02f903 @ bl #0x2b47cc\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1d500b0 @ ldrh r0, [r5]\n"
        ".inst 0xeb02f900 @ bl #0x2b47cc\n"
        ".inst 0xe1d429b8 @ ldrh r2, [r4, #0x98]\n"
        ".inst 0xe1d009b8 @ ldrh r0, [r0, #0x98]\n"
        ".inst 0xe0420000 @ sub r0, r2, r0\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x001fc42c, 84)
extern "C" __attribute__((naked)) void engine_func_001fc42c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb032500 @ bl #0x2c583c\n"
        ".inst 0xe59f0010 @ ldr r0, [pc, #0x10]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe5900004 @ ldr r0, [r0, #4]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xea032059 @ b #0x2c45b8\n"
        ".inst 0x0044cfd0 @ ldrdeq ip, sp, [r4], #-0xf0\n"
        ".inst 0xe59f0020 @ ldr r0, [pc, #0x20]\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000003 @ beq #0x1fc478\n"
        ".inst 0xe2800a12 @ add r0, r0, #0x12000\n"
        ".inst 0xe2800fcd @ add r0, r0, #0x334\n"
        ".inst 0xeb0719a3 @ bl #0x3c2b04\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0044cdf0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011cfa4, 88)
extern "C" __attribute__((naked)) void func_0011cfa4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe2800e4a @ add r0, r0, #0x4a0\n"
        ".inst 0xe1a00000 @ mov r0, r0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe24dd028 @ sub sp, sp, #0x28\n"
        ".inst 0xe1a00001 @ mov r0, r1\n"
        ".inst 0xe1a0200d @ mov r2, sp\n"
        ".inst 0xe2841018 @ add r1, r4, #0x18\n"
        ".inst 0xeb007658 @ bl #0x13a92c\n"
        ".inst 0xe89d0007 @ ldm sp, {r0, r1, r2}\n"
        ".inst 0xe2843024 @ add r3, r4, #0x24\n"
        ".inst 0xe8830007 @ stm r3, {r0, r1, r2}\n"
        ".inst 0xe28d300c @ add r3, sp, #0xc\n"
        ".inst 0xe8930007 @ ldm r3, {r0, r1, r2}\n"
        ".inst 0xe2843030 @ add r3, r4, #0x30\n"
        ".inst 0xe284403c @ add r4, r4, #0x3c\n"
        ".inst 0xe8830007 @ stm r3, {r0, r1, r2}\n"
        ".inst 0xe28d3018 @ add r3, sp, #0x18\n"
        ".inst 0xe8930007 @ ldm r3, {r0, r1, r2}\n"
        ".inst 0xe8840007 @ stm r4, {r0, r1, r2}\n"
        ".inst 0xe28dd028 @ add sp, sp, #0x28\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001219a0, 88)
extern "C" __attribute__((naked)) void func_001219a0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d41f0 @ push {r4, r5, r6, r7, r8, lr}\n"
        ".inst 0xe1a06000 @ mov r6, r0\n"
        ".inst 0xe5d00000 @ ldrb r0, [r0]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x13a04000 @ movne r4, #0\n"
        ".inst 0x11a07004 @ movne r7, r4\n"
        ".inst 0x0a00000d @ beq #0x1219f4\n"
        ".inst 0xe20410ff @ and r1, r4, #0xff\n"
        ".inst 0xe1a00006 @ mov r0, r6\n"
        ".inst 0xeb064d3b @ bl #0x2b4eb8\n"
        ".inst 0xe0865104 @ add r5, r6, r4, lsl #2\n"
        ".inst 0xe6af0074 @ sxtb r0, r4\n"
        ".inst 0xe595107c @ ldr r1, [r5, #0x7c]\n"
        ".inst 0xe5952284 @ ldr r2, [r5, #0x284]\n"
        ".inst 0xeb064d30 @ bl #0x2b4ea0\n"
        ".inst 0xe2844001 @ add r4, r4, #1\n"
        ".inst 0xe585707c @ str r7, [r5, #0x7c]\n"
        ".inst 0xe3540002 @ cmp r4, #2\n"
        ".inst 0xe5857284 @ str r7, [r5, #0x284]\n"
        ".inst 0xbafffff2 @ blt #0x1219bc\n"
        ".inst 0xe5c67000 @ strb r7, [r6]\n"
        ".inst 0xe8bd81f0 @ pop {r4, r5, r6, r7, r8, pc}\n"
    );
}
