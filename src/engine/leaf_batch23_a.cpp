#include "types.h"

// Batch 23 A exact leaf encodings; literal and bounded post-return data bytes are preserved.

// DECOMP_FUNC(0x001e4928, 52)
extern "C" __attribute__((naked)) void ui_func_001e4928() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb037065 @ bl #0x2c0ac8\n"
        ".inst 0xe59f2020 @ ldr r2, [pc, #0x20]\n"
        ".inst 0xe5922000 @ ldr r2, [r2]\n"
        ".inst 0xe3520000 @ cmp r2, #0\n"
        ".inst 0x03a00000 @ moveq r0, #0\n"
        ".inst 0x0a000003 @ beq #0x1e4954\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xe1a00002 @ mov r0, r2\n"
        ".inst 0xea07cb36 @ b #0x3d7630\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004342c8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001e495c, 52)
extern "C" __attribute__((naked)) void ui_func_001e495c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb037058 @ bl #0x2c0ac8\n"
        ".inst 0xe59f2020 @ ldr r2, [pc, #0x20]\n"
        ".inst 0xe5922000 @ ldr r2, [r2]\n"
        ".inst 0xe3520000 @ cmp r2, #0\n"
        ".inst 0x03a00000 @ moveq r0, #0\n"
        ".inst 0x0a000003 @ beq #0x1e4988\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xe1a00002 @ mov r0, r2\n"
        ".inst 0xea07d200 @ b #0x3d918c\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00435ce8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ee948, 52)
extern "C" __attribute__((naked)) void script_vm_func_001ee948() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0024 @ ldr r0, [pc, #0x24]\n"
        ".inst 0xe5900004 @ ldr r0, [r0, #4]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000005 @ beq #0x1ee970\n"
        ".inst 0xe3a02002 @ mov r2, #2\n"
        ".inst 0xed9f0a05 @ vldr s0, [pc, #0x14]\n"
        ".inst 0xe5802004 @ str r2, [r0, #4]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xed800a03 @ vstr s0, [r0, #0xc]\n"
        ".inst 0xe5801008 @ str r1, [r0, #8]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0043dd38 @ tail data\n"
        ".word 0x00000000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001fc610, 52)
extern "C" __attribute__((naked)) void ui_func_001fc610() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb03112b @ bl #0x2c0ac8\n"
        ".inst 0xe59f2020 @ ldr r2, [pc, #0x20]\n"
        ".inst 0xe5922000 @ ldr r2, [r2]\n"
        ".inst 0xe3520000 @ cmp r2, #0\n"
        ".inst 0x03a00000 @ moveq r0, #0\n"
        ".inst 0x0a000003 @ beq #0x1fc63c\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xe1a00002 @ mov r0, r2\n"
        ".inst 0xea04e16d @ b #0x334bf4\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00435d30 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ffaa8, 52)
extern "C" __attribute__((naked)) void engine_func_001ffaa8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe3a04000 @ mov r4, #0\n"
        ".inst 0xe24dd008 @ sub sp, sp, #8\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe1a0c004 @ mov ip, r4\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe3a02004 @ mov r2, #4\n"
        ".inst 0xe1a03004 @ mov r3, r4\n"
        ".inst 0xe88d1010 @ stm sp, {r4, ip}\n"
        ".inst 0xeb030fdc @ bl #0x2c3a44\n"
        ".inst 0xe28dd008 @ add sp, sp, #8\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004c3930 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0010fb34, 56)
extern "C" __attribute__((naked)) void func_0010fb34() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f002c @ ldr r0, [pc, #0x2c]\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe3a012bf @ mov r1, #0xf000000b\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xeb002f45 @ bl #0x11b860\n"
        ".inst 0xe2101102 @ ands r1, r0, #0x80000000\n"
        ".inst 0x5a000004 @ bpl #0x10fb64\n"
        ".inst 0xe1a0100f @ mov r1, pc\n"
        ".inst 0xe1b02fa0 @ lsrs r2, r0, #0x1f\n"
        ".inst 0x0a000001 @ beq #0x10fb64\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xea06af88 @ b #0x2bb988\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00471b5c @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011b558, 56)
extern "C" __attribute__((naked)) void func_0011b558() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe590000c @ ldr r0, [r0, #0xc]\n"
        ".inst 0xe3700001 @ cmn r0, #1\n"
        ".inst 0x0a000007 @ beq #0x11b58c\n"
        ".inst 0xe5d41024 @ ldrb r1, [r4, #0x24]\n"
        ".inst 0xe3510001 @ cmp r1, #1\n"
        ".inst 0x1a000004 @ bne #0x11b58c\n"
        ".inst 0xeb002e00 @ bl #0x126d80\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe5c41024 @ strb r1, [r4, #0x24]\n"
        ".inst 0xe5c40025 @ strb r0, [r4, #0x25]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0011c71c, 56)
extern "C" __attribute__((naked)) void func_0011c71c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3e02000 @ mvn r2, #0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe8800006 @ stm r0, {r1, r2}\n"
        ".inst 0xe280000c @ add r0, r0, #0xc\n"
        ".inst 0xeb002fdc @ bl #0x1286a4\n"
        ".inst 0xe240000c @ sub r0, r0, #0xc\n"
        ".inst 0xe3a03001 @ mov r3, #1\n"
        ".inst 0xe5c03030 @ strb r3, [r0, #0x30]\n"
        ".inst 0xe3e01000 @ mvn r1, #0\n"
        ".inst 0xe2803038 @ add r3, r0, #0x38\n"
        ".inst 0xe1a02001 @ mov r2, r1\n"
        ".inst 0xe8830006 @ stm r3, {r1, r2}\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".inst 0xe12fff1e @ bx lr\n"
    );
}

// DECOMP_FUNC(0x0011d0e4, 56)
extern "C" __attribute__((naked)) void func_0011d0e4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe59f4028 @ ldr r4, [pc, #0x28]\n"
        ".inst 0xe5941040 @ ldr r1, [r4, #0x40]\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x15940080 @ ldrne r0, [r4, #0x80]\n"
        ".inst 0x112fff31 @ blxne r1\n"
        ".inst 0xe5941044 @ ldr r1, [r4, #0x44]\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x0a000002 @ beq #0x11d114\n"
        ".inst 0xe5940084 @ ldr r0, [r4, #0x84]\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xe12fff11 @ bx r1\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0044e3b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d7e4, 56)
extern "C" __attribute__((naked)) void func_0011d7e4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f1020 @ ldr r1, [pc, #0x20]\n"
        ".inst 0xe5a41080 @ str r1, [r4, #0x80]!\n"
        ".inst 0xe5840004 @ str r0, [r4, #4]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00190040 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d81c, 56)
extern "C" __attribute__((naked)) void func_0011d81c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f1020 @ ldr r1, [pc, #0x20]\n"
        ".inst 0xe5a41080 @ str r1, [r4, #0x80]!\n"
        ".inst 0xe5840004 @ str r0, [r4, #4]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00030040 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001272d4, 56)
extern "C" __attribute__((naked)) void nn_sdk_func_001272d4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f2024 @ ldr r2, [pc, #0x24]\n"
        ".inst 0xe5a42080 @ str r2, [r4, #0x80]!\n"
        ".inst 0xe5841004 @ str r1, [r4, #4]\n"
        ".inst 0xe3a01020 @ mov r1, #0x20\n"
        ".inst 0xe5841008 @ str r1, [r4, #8]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x08610042 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00129cd0, 56)
extern "C" __attribute__((naked)) void func_00129cd0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4013 @ push {r0, r1, r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f1024 @ ldr r1, [pc, #0x24]\n"
        ".inst 0xe5a41080 @ str r1, [r4, #0x80]!\n"
        ".inst 0xe5dd1004 @ ldrb r1, [sp, #4]\n"
        ".inst 0xe5c41004 @ strb r1, [r4, #4]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe28dd008 @ add sp, sp, #8\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x000b0040 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0012a664, 56)
extern "C" __attribute__((naked)) void engine_func_0012a664() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe1a00000 @ mov r0, r0\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xeb06440d @ bl #0x2bb6b8\n"
        ".inst 0xe1a01005 @ mov r1, r5\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xeb004369 @ bl #0x13b434\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xeb0643ec @ bl #0x2bb648\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0012ce1c, 56)
extern "C" __attribute__((naked)) void func_0012ce1c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe5910000 @ ldr r0, [r1]\n"
        ".inst 0xe1a04001 @ mov r4, r1\n"
        ".inst 0xe3a02004 @ mov r2, #4\n"
        ".inst 0xe3a01008 @ mov r1, #8\n"
        ".inst 0xe5903008 @ ldr r3, [r0, #8]\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe12fff33 @ blx r3\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000001 @ beq #0x12ce4c\n"
        ".inst 0xe59f1004 @ ldr r1, [pc, #4]\n"
        ".inst 0xe8800012 @ stm r0, {r1, r4}\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00420fc4 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0012ce54, 56)
extern "C" __attribute__((naked)) void func_0012ce54() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe3a02004 @ mov r2, #4\n"
        ".inst 0xe3a01008 @ mov r1, #8\n"
        ".inst 0xe5903008 @ ldr r3, [r0, #8]\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe12fff33 @ blx r3\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000001 @ beq #0x12ce84\n"
        ".inst 0xe59f1004 @ ldr r1, [pc, #4]\n"
        ".inst 0xe8800012 @ stm r0, {r1, r4}\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00421014 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0012d0e8, 56)
extern "C" __attribute__((naked)) void func_0012d0e8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe5910000 @ ldr r0, [r1]\n"
        ".inst 0xe1a04001 @ mov r4, r1\n"
        ".inst 0xe3a02004 @ mov r2, #4\n"
        ".inst 0xe3a01008 @ mov r1, #8\n"
        ".inst 0xe5903008 @ ldr r3, [r0, #8]\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe12fff33 @ blx r3\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000001 @ beq #0x12d118\n"
        ".inst 0xe59f1004 @ ldr r1, [pc, #4]\n"
        ".inst 0xe8800012 @ stm r0, {r1, r4}\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0042113c @ tail data\n"
    );
}

// DECOMP_FUNC(0x0012d504, 56)
extern "C" __attribute__((naked)) void func_0012d504() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe3a02004 @ mov r2, #4\n"
        ".inst 0xe3a01008 @ mov r1, #8\n"
        ".inst 0xe5903008 @ ldr r3, [r0, #8]\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe12fff33 @ blx r3\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000001 @ beq #0x12d534\n"
        ".inst 0xe59f1004 @ ldr r1, [pc, #4]\n"
        ".inst 0xe8800012 @ stm r0, {r1, r4}\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0042128c @ tail data\n"
    );
}

// DECOMP_FUNC(0x001316b4, 56)
extern "C" __attribute__((naked)) void func_001316b4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe52de004 @ str lr, [sp, #-4]!\n"
        ".inst 0xe24dd024 @ sub sp, sp, #0x24\n"
        ".inst 0xe59f3024 @ ldr r3, [pc, #0x24]\n"
        ".inst 0xe1cd10b8 @ strh r1, [sp, #8]\n"
        ".inst 0xe58d3000 @ str r3, [sp]\n"
        ".inst 0xe5901430 @ ldr r1, [r0, #0x430]\n"
        ".inst 0xe3a03018 @ mov r3, #0x18\n"
        ".inst 0xe28d0008 @ add r0, sp, #8\n"
        ".inst 0xfa060c80 @ blx #0x2b48dc\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0xe28dd024 @ add sp, sp, #0x24\n"
        ".inst 0x12800002 @ addne r0, r0, #2\n"
        ".inst 0xe49df004 @ pop {pc}\n"
        ".word 0x00140dec @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013a8f4, 56)
extern "C" __attribute__((naked)) void func_0013a8f4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f1020 @ ldr r1, [pc, #0x20]\n"
        ".inst 0xe5a41080 @ str r1, [r4, #0x80]!\n"
        ".inst 0xe5840004 @ str r0, [r4, #4]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00090040 @ tail data\n"
        ".word 0x00471ba4 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013b234, 56)
extern "C" __attribute__((naked)) void func_0013b234() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f2020 @ ldr r2, [pc, #0x20]\n"
        ".inst 0xe5a42080 @ str r2, [r4, #0x80]!\n"
        ".inst 0xe1c400f4 @ strd r0, r1, [r4, #4]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00420080 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013b26c, 56)
extern "C" __attribute__((naked)) void func_0013b26c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f1020 @ ldr r1, [pc, #0x20]\n"
        ".inst 0xe5a41080 @ str r1, [r4, #0x80]!\n"
        ".inst 0xe5840004 @ str r0, [r4, #4]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00430040 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013b434, 56)
extern "C" __attribute__((naked)) void engine_func_0013b434() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f2020 @ ldr r2, [pc, #0x20]\n"
        ".inst 0xe5a42080 @ str r2, [r4, #0x80]!\n"
        ".inst 0xe1c400f4 @ strd r0, r1, [r4, #4]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004f0080 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00141984, 56)
extern "C" __attribute__((naked)) void engine_func_00141984() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5900004 @ ldr r0, [r0, #4]\n"
        ".inst 0xe1a00000 @ mov r0, r0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe590003c @ ldr r0, [r0, #0x3c]\n"
        ".inst 0xe1a04002 @ mov r4, r2\n"
        ".inst 0xeb002e24 @ bl #0x14d230\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000004 @ beq #0x1419b8\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe5841000 @ str r1, [r4]\n"
        ".inst 0xeb002e17 @ bl #0x14d210\n"
        ".inst 0xe5840004 @ str r0, [r4, #4]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00146830, 56)
extern "C" __attribute__((naked)) void func_00146830() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4013 @ push {r0, r1, r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f1024 @ ldr r1, [pc, #0x24]\n"
        ".inst 0xe5a41080 @ str r1, [r4, #0x80]!\n"
        ".inst 0xe1dd10b4 @ ldrh r1, [sp, #4]\n"
        ".inst 0xe1c410b4 @ strh r1, [r4, #4]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe28dd008 @ add sp, sp, #8\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00170040 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00146964, 56)
extern "C" __attribute__((naked)) void ui_func_00146964() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe3a00b42 @ mov r0, #0x10800\n"
        ".inst 0xe5a40080 @ str r0, [r4, #0x80]!\n"
        ".inst 0xe2840004 @ add r0, r4, #4\n"
        ".inst 0xe3a02080 @ mov r2, #0x80\n"
        ".inst 0xeb05d974 @ bl #0x2bcf58\n"
        ".inst 0xe5950000 @ ldr r0, [r5]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x00148350, 56)
extern "C" __attribute__((naked)) void func_00148350() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f1020 @ ldr r1, [pc, #0x20]\n"
        ".inst 0xe5a41080 @ str r1, [r4, #0x80]!\n"
        ".inst 0xe5840004 @ str r0, [r4, #4]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x003f0040 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014ce64, 56)
extern "C" __attribute__((naked)) void ui_func_0014ce64() {
    asm volatile(
        ".arm\n"
        ".inst 0xeddf0a0b @ vldr s1, [pc, #0x2c]\n"
        ".inst 0xeeb40ae0 @ vcmpe.f32 s0, s1\n"
        ".inst 0xeef1fa10 @ vmrs apsr_nzcv, fpscr\n"
        ".inst 0x9eb00a60 @ vmovls.f32 s0, s1\n"
        ".inst 0x9a000006 @ bls #0x14ce94\n"
        ".inst 0xedd01a14 @ vldr s3, [r0, #0x50]\n"
        ".inst 0xed901a17 @ vldr s2, [r0, #0x5c]\n"
        ".inst 0xedd00a13 @ vldr s1, [r0, #0x4c]\n"
        ".inst 0xee701a61 @ vsub.f32 s3, s0, s3\n"
        ".inst 0xee211a21 @ vmul.f32 s2, s2, s3\n"
        ".inst 0xeec11a00 @ vdiv.f32 s3, s2, s0\n"
        ".inst 0xee810aa0 @ vdiv.f32 s0, s3, s1\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00000000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014f514, 56)
extern "C" __attribute__((naked)) void func_0014f514() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4013 @ push {r0, r1, r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f1024 @ ldr r1, [pc, #0x24]\n"
        ".inst 0xe5a41080 @ str r1, [r4, #0x80]!\n"
        ".inst 0xe1dd10b4 @ ldrh r1, [sp, #4]\n"
        ".inst 0xe1c410b4 @ strh r1, [r4, #4]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe28dd008 @ add sp, sp, #8\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00070040 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014fc3c, 56)
extern "C" __attribute__((naked)) void func_0014fc3c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe59f0000 @ ldr r0, [pc]\n"
        ".inst 0xea000d8d @ b #0x153280\n"
        ".inst 0x004e6f14 @ subeq r6, lr, r4, lsl pc\n"
        ".inst 0xeddf0a07 @ vldr s1, [pc, #0x1c]\n"
        ".inst 0xe1d016bc @ ldrh r1, [r0, #0x6c]\n"
        ".inst 0xeeb40ae0 @ vcmpe.f32 s0, s1\n"
        ".inst 0xe3811002 @ orr r1, r1, #2\n"
        ".inst 0xeef1fa10 @ vmrs apsr_nzcv, fpscr\n"
        ".inst 0xbeb00a60 @ vmovlt.f32 s0, s1\n"
        ".inst 0xed800a09 @ vstr s0, [r0, #0x24]\n"
        ".inst 0xe1c016bc @ strh r1, [r0, #0x6c]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00000000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014fefc, 56)
extern "C" __attribute__((naked)) void func_0014fefc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f1020 @ ldr r1, [pc, #0x20]\n"
        ".inst 0xe5a41080 @ str r1, [r4, #0x80]!\n"
        ".inst 0xe5840004 @ str r0, [r4, #4]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00160040 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014ff80, 56)
extern "C" __attribute__((naked)) void func_0014ff80() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f1020 @ ldr r1, [pc, #0x20]\n"
        ".inst 0xe5a41080 @ str r1, [r4, #0x80]!\n"
        ".inst 0xe5840004 @ str r0, [r4, #4]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00180040 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00150f1c, 56)
extern "C" __attribute__((naked)) void func_00150f1c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xe5b04008 @ ldr r4, [r0, #8]!\n"
        ".inst 0xe1540000 @ cmp r4, r0\n"
        ".inst 0x0a000007 @ beq #0x150f50\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe5944000 @ ldr r4, [r4]\n"
        ".inst 0xe2400f4f @ sub r0, r0, #0x13c\n"
        ".inst 0xe3a01001 @ mov r1, #1\n"
        ".inst 0xeb0010b0 @ bl #0x155208\n"
        ".inst 0xe2850008 @ add r0, r5, #8\n"
        ".inst 0xe1540000 @ cmp r4, r0\n"
        ".inst 0x1afffff7 @ bne #0x150f30\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x00152688, 56)
extern "C" __attribute__((naked)) void func_00152688() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb000c99 @ bl #0x1558f8\n"
        ".inst 0x3effffed @ cdplo p15, #0xf, c15, c15, c13, #7\n"
        ".inst 0xe11c03a1 @ tst ip, r1, lsr #7\n"
        ".inst 0x0a000002 @ beq #0x1526a8\n"
        ".inst 0xe3d0c102 @ bics ip, r0, #0x80000000\n"
        ".inst 0x13a00000 @ movne r0, #0\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".inst 0xe59f0000 @ ldr r0, [pc]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".inst 0x7fc00000 @ svcvc #0xc00000\n"
        ".inst 0xef00003c @ svc #0x3c\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".inst 0xe12fff1e @ bx lr\n"
    );
}

// DECOMP_FUNC(0x00152dac, 56)
extern "C" __attribute__((naked)) void engine_func_00152dac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f002c @ ldr r0, [pc, #0x2c]\n"
        ".inst 0xe1d010b2 @ ldrh r1, [r0, #2]\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x0a000007 @ beq #0x152ddc\n"
        ".inst 0xe2411001 @ sub r1, r1, #1\n"
        ".inst 0xe1a01801 @ lsl r1, r1, #0x10\n"
        ".inst 0xe1b01821 @ lsrs r1, r1, #0x10\n"
        ".inst 0xe1c010b2 @ strh r1, [r0, #2]\n"
        ".inst 0x1a000002 @ bne #0x152ddc\n"
        ".inst 0xe1d010b0 @ ldrh r1, [r0]\n"
        ".inst 0xe5900008 @ ldr r0, [r0, #8]\n"
        ".inst 0xe1c013b8 @ strh r1, [r0, #0x38]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00465120 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00157588, 56)
extern "C" __attribute__((naked)) void func_00157588() {
    asm volatile(
        ".arm\n"
        ".inst 0xeddf0a0b @ vldr s1, [pc, #0x2c]\n"
        ".inst 0xeeb40ae0 @ vcmpe.f32 s0, s1\n"
        ".inst 0xeef1fa10 @ vmrs apsr_nzcv, fpscr\n"
        ".inst 0x3eb00a60 @ vmovlo.f32 s0, s1\n"
        ".inst 0xedd00a09 @ vldr s1, [r0, #0x24]\n"
        ".inst 0xeef40a40 @ vcmp.f32 s1, s0\n"
        ".inst 0xeef1fa10 @ vmrs apsr_nzcv, fpscr\n"
        ".inst 0x0a000003 @ beq #0x1575b8\n"
        ".inst 0xe1d012b0 @ ldrh r1, [r0, #0x20]\n"
        ".inst 0xed800a09 @ vstr s0, [r0, #0x24]\n"
        ".inst 0xe3811040 @ orr r1, r1, #0x40\n"
        ".inst 0xe1c012b0 @ strh r1, [r0, #0x20]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00000000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00158d80, 56)
extern "C" __attribute__((naked)) void func_00158d80() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5d01000 @ ldrb r1, [r0]\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x1a000004 @ bne #0x158da0\n"
        ".inst 0xedd00a04 @ vldr s1, [r0, #0x10]\n"
        ".inst 0xed9f0a06 @ vldr s0, [pc, #0x18]\n"
        ".inst 0xeef40a40 @ vcmp.f32 s1, s0\n"
        ".inst 0xeef1fa10 @ vmrs apsr_nzcv, fpscr\n"
        ".inst 0x0a000002 @ beq #0x158dac\n"
        ".inst 0xed900a01 @ vldr s0, [r0, #4]\n"
        ".inst 0xeddf0a02 @ vldr s1, [pc, #8]\n"
        ".inst 0xee200a20 @ vmul.f32 s0, s0, s1\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00000000 @ tail data\n"
        ".word 0x3dcccccd @ tail data\n"
    );
}

// DECOMP_FUNC(0x0015bc74, 56)
extern "C" __attribute__((naked)) void func_0015bc74() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1028 @ ldr r1, [pc, #0x28]\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe59f4024 @ ldr r4, [pc, #0x24]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x13a00002 @ movne r0, #2\n"
        ".inst 0xe58100b0 @ str r0, [r1, #0xb0]\n"
        ".inst 0xe59f1010 @ ldr r1, [pc, #0x10]\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xeb051b64 @ bl #0x2a2a2c\n"
        ".inst 0xe5840000 @ str r0, [r4]\n"
        ".inst 0xe3a00f4e @ mov r0, #0x138\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00471dc8 @ tail data\n"
        ".word 0x004652a0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0015e808, 56)
extern "C" __attribute__((naked)) void func_0015e808() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xeb057367 @ bl #0x2bb5b4\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x03e00000 @ mvneq r0, #0\n"
        ".inst 0x0a000005 @ beq #0x15e838\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe19000b4 @ ldrh r0, [r0, r4]\n"
        ".inst 0xe0840100 @ add r0, r4, r0, lsl #2\n"
        ".inst 0xe2800a01 @ add r0, r0, #0x1000\n"
        ".inst 0xe59000a8 @ ldr r0, [r0, #0xa8]\n"
        ".inst 0xe1d000b2 @ ldrh r0, [r0, #2]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0000131c @ tail data\n"
    );
}

// DECOMP_FUNC(0x0016afec, 56)
extern "C" __attribute__((naked)) void func_0016afec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4ff0 @ push {r4, r5, r6, r7, r8, sb, sl, fp, lr}\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe5902004 @ ldr r2, [r0, #4]\n"
        ".inst 0xe24f3b0f @ sub r3, pc, #0x3c00\n"
        ".inst 0xe2433f55 @ sub r3, r3, #0x154\n"
        ".inst 0xe24f4b02 @ sub r4, pc, #0x800\n"
        ".inst 0xe2444f5d @ sub r4, r4, #0x174\n"
        ".inst 0xe1510002 @ cmp r1, r2\n"
        ".inst 0x11a03004 @ movne r3, r4\n"
        ".inst 0xe12fff33 @ blx r3\n"
        ".inst 0xebfff19e @ bl #0x167694\n"
        ".inst 0xe8bd8ff0 @ pop {r4, r5, r6, r7, r8, sb, sl, fp, pc}\n"
        ".word 0x0016afbc @ tail data\n"
        ".word 0x0016afec @ tail data\n"
    );
}

// DECOMP_FUNC(0x001a826c, 56)
extern "C" __attribute__((naked)) void func_001a826c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5900018 @ ldr r0, [r0, #0x18]\n"
        ".inst 0xe59f1020 @ ldr r1, [pc, #0x20]\n"
        ".inst 0xe0800080 @ add r0, r0, r0, lsl #1\n"
        ".inst 0xe0810180 @ add r0, r1, r0, lsl #3\n"
        ".inst 0xe5901008 @ ldr r1, [r0, #8]\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe12fff31 @ blx r1\n"
        ".inst 0xe594001c @ ldr r0, [r4, #0x1c]\n"
        ".inst 0xe2800001 @ add r0, r0, #1\n"
        ".inst 0xe584001c @ str r0, [r4, #0x1c]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00472480 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001b3c68, 56)
extern "C" __attribute__((naked)) void script_vm_func_001b3c68() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe59f4028 @ ldr r4, [pc, #0x28]\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe590000c @ ldr r0, [r0, #0xc]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x1bfe7b9d @ blne #0x152af8\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe5900010 @ ldr r0, [r0, #0x10]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000001 @ beq #0x1b3c98\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xeafe7b97 @ b #0x152af8\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004474d8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001b4200, 56)
extern "C" __attribute__((naked)) void ui_func_001b4200() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe3a04000 @ mov r4, #0\n"
        ".inst 0xe59f5024 @ ldr r5, [pc, #0x24]\n"
        ".inst 0xe0841084 @ add r1, r4, r4, lsl #1\n"
        ".inst 0xe5950000 @ ldr r0, [r5]\n"
        ".inst 0xe0800181 @ add r0, r0, r1, lsl #3\n"
        ".inst 0xe590001c @ ldr r0, [r0, #0x1c]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x1b0336fe @ blne #0x281e20\n"
        ".inst 0xe2844001 @ add r4, r4, #1\n"
        ".inst 0xe3540010 @ cmp r4, #0x10\n"
        ".inst 0xbafffff6 @ blt #0x1b420c\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00447a10 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001d3598, 56)
extern "C" __attribute__((naked)) void script_vm_func_001d3598() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe3a04000 @ mov r4, #0\n"
        ".inst 0xe59f5024 @ ldr r5, [pc, #0x24]\n"
        ".inst 0xe0840184 @ add r0, r4, r4, lsl #3\n"
        ".inst 0xe5951000 @ ldr r1, [r5]\n"
        ".inst 0xe0810180 @ add r0, r1, r0, lsl #3\n"
        ".inst 0xe590003c @ ldr r0, [r0, #0x3c]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x1bfdfd4e @ blne #0x152af8\n"
        ".inst 0xe2844001 @ add r4, r4, #1\n"
        ".inst 0xe3540018 @ cmp r4, #0x18\n"
        ".inst 0xbafffff6 @ blt #0x1d35a4\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00447e70 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001e38c0, 56)
extern "C" __attribute__((naked)) void engine_func_001e38c0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00c01 @ mov r0, #0x100\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb037aca @ bl #0x2c23f8\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000002 @ beq #0x1e38e0\n"
        ".inst 0xeb02c46f @ bl #0x294a98\n"
        ".inst 0xe59f1010 @ ldr r1, [pc, #0x10]\n"
        ".inst 0xe5801000 @ str r1, [r0]\n"
        ".inst 0xe59f100c @ ldr r1, [pc, #0xc]\n"
        ".inst 0xe5911000 @ ldr r1, [r1]\n"
        ".inst 0xe5810194 @ str r0, [r1, #0x194]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00420420 @ tail data\n"
        ".word 0x00447e88 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001fa5dc, 56)
extern "C" __attribute__((naked)) void script_vm_func_001fa5dc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe3a04017 @ mov r4, #0x17\n"
        ".inst 0xe59f5024 @ ldr r5, [pc, #0x24]\n"
        ".inst 0xe0840104 @ add r0, r4, r4, lsl #2\n"
        ".inst 0xe5951000 @ ldr r1, [r5]\n"
        ".inst 0xe0810180 @ add r0, r1, r0, lsl #3\n"
        ".inst 0xe5900034 @ ldr r0, [r0, #0x34]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x1bfd613d @ blne #0x152af8\n"
        ".inst 0xe2544001 @ subs r4, r4, #1\n"
        ".inst 0xe320f000 @ nop\n"
        ".inst 0x5afffff6 @ bpl #0x1fa5e8\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00447a48 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0010f83c, 60)
extern "C" __attribute__((naked)) void func_0010f83c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4038 @ push {r3, r4, r5, lr}\n"
        ".inst 0xe59f402c @ ldr r4, [pc, #0x2c]\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x1a000007 @ bne #0x10f870\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe58d0000 @ str r0, [sp]\n"
        ".inst 0xe1a0000d @ mov r0, sp\n"
        ".inst 0xeb000e5d @ bl #0x1131d8\n"
        ".inst 0xe2000102 @ and r0, r0, #0x80000000\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0xa59d0000 @ ldrge r0, [sp]\n"
        ".inst 0xa5840000 @ strge r0, [r4]\n"
        ".inst 0xe8bd8038 @ pop {r3, r4, r5, pc}\n"
        ".word 0x00471b58 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0010fa24, 60)
extern "C" __attribute__((naked)) void func_0010fa24() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500020 @ cmp r0, #0x20\n"
        ".inst 0x92800020 @ addls r0, r0, #0x20\n"
        ".inst 0x9a000008 @ bls #0x10fa54\n"
        ".inst 0xe59f1020 @ ldr r1, [pc, #0x20]\n"
        ".inst 0xe0811000 @ add r1, r1, r0\n"
        ".inst 0xe3510027 @ cmp r1, #0x27\n"
        ".inst 0x92810018 @ addls r0, r1, #0x18\n"
        ".inst 0x9a000003 @ bls #0x10fa54\n"
        ".inst 0xe59f1010 @ ldr r1, [pc, #0x10]\n"
        ".inst 0xe0800001 @ add r0, r0, r1\n"
        ".inst 0xe3500040 @ cmp r0, #0x40\n"
        ".inst 0x83e00000 @ mvnhi r0, #0\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0xaef62b00 @ tail data\n"
        ".word 0x93725b00 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d7a8, 60)
extern "C" __attribute__((naked)) void func_0011d7a8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4031 @ push {r0, r4, r5, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f0024 @ ldr r0, [pc, #0x24]\n"
        ".inst 0xe5a40080 @ str r0, [r4, #0x80]!\n"
        ".inst 0xe5dd0000 @ ldrb r0, [sp]\n"
        ".inst 0xe5c40004 @ strb r0, [r4, #4]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8038 @ pop {r3, r4, r5, pc}\n"
        ".word 0x00220040 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00126444, 60)
extern "C" __attribute__((naked)) void ui_func_00126444() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04001 @ mov r4, r1\n"
        ".inst 0xeb06699d @ bl #0x2c0ac8\n"
        ".inst 0xe5900008 @ ldr r0, [r0, #8]\n"
        ".inst 0xe59f2010 @ ldr r2, [pc, #0x10]\n"
        ".inst 0xe0841084 @ add r1, r4, r4, lsl #1\n"
        ".inst 0xe2411004 @ sub r1, r1, #4\n"
        ".inst 0xe0800002 @ add r0, r0, r2\n"
        ".inst 0xe7d00001 @ ldrb r0, [r0, r1]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".inst 0x00403834 @ subeq r3, r0, r4, lsr r8\n"
        ".inst 0xe1d002b0 @ ldrh r0, [r0, #0x20]\n"
        ".inst 0xe1d112b0 @ ldrh r1, [r1, #0x20]\n"
        ".inst 0xe0400001 @ sub r0, r0, r1\n"
        ".inst 0xe12fff1e @ bx lr\n"
    );
}

// DECOMP_FUNC(0x00128c80, 60)
extern "C" __attribute__((naked)) void func_00128c80() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a00000 @ mov r0, r0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f1020 @ ldr r1, [pc, #0x20]\n"
        ".inst 0xe5a41080 @ str r1, [r4, #0x80]!\n"
        ".inst 0xe5840004 @ str r0, [r4, #4]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00140040 @ tail data\n"
        ".word 0x00472ad8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00128d08, 60)
extern "C" __attribute__((naked)) void func_00128d08() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe3a00703 @ mov r0, #0xc0000\n"
        ".inst 0xe5a40080 @ str r0, [r4, #0x80]!\n"
        ".inst 0xe59f001c @ ldr r0, [pc, #0x1c]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2101102 @ ands r1, r0, #0x80000000\n"
        ".inst 0x4a000002 @ bmi #0x128d3c\n"
        ".inst 0xe5940008 @ ldr r0, [r4, #8]\n"
        ".inst 0xe5850000 @ str r0, [r5]\n"
        ".inst 0xe5940004 @ ldr r0, [r4, #4]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00471b64 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00129510, 60)
extern "C" __attribute__((naked)) void func_00129510() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f0024 @ ldr r0, [pc, #0x24]\n"
        ".inst 0xe5a40080 @ str r0, [r4, #0x80]!\n"
        ".inst 0xe3a00020 @ mov r0, #0x20\n"
        ".inst 0xe5840004 @ str r0, [r4, #4]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00010002 @ tail data\n"
        ".word 0x00471ba4 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001295a8, 60)
extern "C" __attribute__((naked)) void engine_func_001295a8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe3a0080b @ mov r0, #0xb0000\n"
        ".inst 0xe5a40080 @ str r0, [r4, #0x80]!\n"
        ".inst 0xe59f001c @ ldr r0, [pc, #0x1c]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2101102 @ ands r1, r0, #0x80000000\n"
        ".inst 0x4a000002 @ bmi #0x1295dc\n"
        ".inst 0xe5940008 @ ldr r0, [r4, #8]\n"
        ".inst 0xe5850000 @ str r0, [r5]\n"
        ".inst 0xe5940004 @ ldr r0, [r4, #4]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00471ba4 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0012a69c, 60)
extern "C" __attribute__((naked)) void func_0012a69c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4031 @ push {r0, r4, r5, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f0024 @ ldr r0, [pc, #0x24]\n"
        ".inst 0xe5a40080 @ str r0, [r4, #0x80]!\n"
        ".inst 0xe5dd0000 @ ldrb r0, [sp]\n"
        ".inst 0xe5c40004 @ strb r0, [r4, #4]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8038 @ pop {r3, r4, r5, pc}\n"
        ".word 0x003b0040 @ tail data\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001310ec, 60)
extern "C" __attribute__((naked)) void ui_func_001310ec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1a0c001 @ mov ip, r1\n"
        ".inst 0xe5842004 @ str r2, [r4, #4]\n"
        ".inst 0xe584300c @ str r3, [r4, #0xc]\n"
        ".inst 0xe1a00002 @ mov r0, r2\n"
        ".inst 0xe1a01003 @ mov r1, r3\n"
        ".inst 0xe584c000 @ str ip, [r4]\n"
        ".inst 0xeb0656bf @ bl #0x2c6c10\n"
        ".inst 0xe3c0101f @ bic r1, r0, #0x1f\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe5840014 @ str r0, [r4, #0x14]\n"
        ".inst 0xe5841008 @ str r1, [r4, #8]\n"
        ".inst 0xe5840010 @ str r0, [r4, #0x10]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001312cc, 60)
extern "C" __attribute__((naked)) void func_001312cc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000008 @ beq #0x131304\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xeb05ec73 @ bl #0x2ac4b8\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe3a01003 @ mov r1, #3\n"
        ".inst 0xeb007b30 @ bl #0x14ffb8\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xeb002b7c @ bl #0x13c0f0\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe5840000 @ str r0, [r4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001372d8, 60)
extern "C" __attribute__((naked)) void func_001372d8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe52de004 @ str lr, [sp, #-4]!\n"
        ".inst 0xe24dd00c @ sub sp, sp, #0xc\n"
        ".inst 0xe1a0c000 @ mov ip, r0\n"
        ".inst 0xe59d0010 @ ldr r0, [sp, #0x10]\n"
        ".inst 0xe58d3000 @ str r3, [sp]\n"
        ".inst 0xe1a03002 @ mov r3, r2\n"
        ".inst 0xe58d0004 @ str r0, [sp, #4]\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe1a02001 @ mov r2, r1\n"
        ".inst 0xe1a0100c @ mov r1, ip\n"
        ".inst 0xe590009c @ ldr r0, [r0, #0x9c]\n"
        ".inst 0xeb002df1 @ bl #0x142ad0\n"
        ".inst 0xe28dd00c @ add sp, sp, #0xc\n"
        ".inst 0xe49df004 @ pop {pc}\n"
        ".word 0x004c6290 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013b808, 60)
extern "C" __attribute__((naked)) void func_0013b808() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe3a0070f @ mov r0, #0x3c0000\n"
        ".inst 0xe5a40080 @ str r0, [r4, #0x80]!\n"
        ".inst 0xe59f001c @ ldr r0, [pc, #0x1c]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2101102 @ ands r1, r0, #0x80000000\n"
        ".inst 0x4a000002 @ bmi #0x13b83c\n"
        ".inst 0xe5d40008 @ ldrb r0, [r4, #8]\n"
        ".inst 0xe5c50000 @ strb r0, [r5]\n"
        ".inst 0xe5940004 @ ldr r0, [r4, #4]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00472a34 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013b844, 60)
extern "C" __attribute__((naked)) void func_0013b844() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4031 @ push {r0, r4, r5, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f0024 @ ldr r0, [pc, #0x24]\n"
        ".inst 0xe5a40080 @ str r0, [r4, #0x80]!\n"
        ".inst 0xe5dd0000 @ ldrb r0, [sp]\n"
        ".inst 0xe5c40004 @ strb r0, [r4, #4]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8038 @ pop {r3, r4, r5, pc}\n"
        ".word 0x003d0040 @ tail data\n"
        ".word 0x00472a34 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013b880, 60)
extern "C" __attribute__((naked)) void func_0013b880() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe3a0083b @ mov r0, #0x3b0000\n"
        ".inst 0xe5a40080 @ str r0, [r4, #0x80]!\n"
        ".inst 0xe59f001c @ ldr r0, [pc, #0x1c]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2101102 @ ands r1, r0, #0x80000000\n"
        ".inst 0x4a000002 @ bmi #0x13b8b4\n"
        ".inst 0xe5d40008 @ ldrb r0, [r4, #8]\n"
        ".inst 0xe5c50000 @ strb r0, [r5]\n"
        ".inst 0xe5940004 @ ldr r0, [r4, #4]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00472a34 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013b8bc, 60)
extern "C" __attribute__((naked)) void func_0013b8bc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4031 @ push {r0, r4, r5, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f0024 @ ldr r0, [pc, #0x24]\n"
        ".inst 0xe5a40080 @ str r0, [r4, #0x80]!\n"
        ".inst 0xe5dd0000 @ ldrb r0, [sp]\n"
        ".inst 0xe5c40004 @ strb r0, [r4, #4]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8038 @ pop {r3, r4, r5, pc}\n"
        ".word 0x00130040 @ tail data\n"
        ".word 0x00472a34 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013fdb0, 60)
extern "C" __attribute__((naked)) void engine_func_0013fdb0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xe5b04004 @ ldr r4, [r0, #4]!\n"
        ".inst 0xe1a06001 @ mov r6, r1\n"
        ".inst 0xe1540000 @ cmp r4, r0\n"
        ".inst 0x0a000007 @ beq #0x13fde8\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe5944000 @ ldr r4, [r4]\n"
        ".inst 0xe24000dc @ sub r0, r0, #0xdc\n"
        ".inst 0xe1a01006 @ mov r1, r6\n"
        ".inst 0xeb05f78a @ bl #0x2bdc08\n"
        ".inst 0xe2850004 @ add r0, r5, #4\n"
        ".inst 0xe1540000 @ cmp r4, r0\n"
        ".inst 0x1afffff7 @ bne #0x13fdc8\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x001468e4, 60)
extern "C" __attribute__((naked)) void func_001468e4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f5028 @ ldr r5, [pc, #0x28]\n"
        ".inst 0xe3a0c000 @ mov ip, #0\n"
        ".inst 0xe5a45080 @ str r5, [r4, #0x80]!\n"
        ".inst 0xe2846004 @ add r6, r4, #4\n"
        ".inst 0xe5841010 @ str r1, [r4, #0x10]\n"
        ".inst 0xe886100c @ stm r6, {r2, r3, ip}\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00150082 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00147c0c, 60)
extern "C" __attribute__((naked)) void func_00147c0c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f5028 @ ldr r5, [pc, #0x28]\n"
        ".inst 0xe3a0c000 @ mov ip, #0\n"
        ".inst 0xe5a45080 @ str r5, [r4, #0x80]!\n"
        ".inst 0xe2846004 @ add r6, r4, #4\n"
        ".inst 0xe5841010 @ str r1, [r4, #0x10]\n"
        ".inst 0xe886100c @ stm r6, {r2, r3, ip}\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00080082 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014d080, 60)
extern "C" __attribute__((naked)) void func_0014d080() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5902014 @ ldr r2, [r0, #0x14]\n"
        ".inst 0xe0800002 @ add r0, r0, r2\n"
        ".inst 0xe59f2028 @ ldr r2, [pc, #0x28]\n"
        ".inst 0xe5903000 @ ldr r3, [r0]\n"
        ".inst 0xe1530001 @ cmp r3, r1\n"
        ".inst 0x9a000005 @ bls #0x14d0b0\n"
        ".inst 0xe0801181 @ add r1, r0, r1, lsl #3\n"
        ".inst 0xe1d130b4 @ ldrh r3, [r1, #4]\n"
        ".inst 0xe1530002 @ cmp r3, r2\n"
        ".inst 0x05911008 @ ldreq r1, [r1, #8]\n"
        ".inst 0x00800001 @ addeq r0, r0, r1\n"
        ".inst 0x0a000000 @ beq #0x14d0b4\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00004902 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014d0bc, 60)
extern "C" __attribute__((naked)) void func_0014d0bc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4038 @ push {r3, r4, r5, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe3a02009 @ mov r2, #9\n"
        ".inst 0xe1a0100d @ mov r1, sp\n"
        ".inst 0xe2800004 @ add r0, r0, #4\n"
        ".inst 0xeb05672f @ bl #0x2a6d94\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x059f0014 @ ldreq r0, [pc, #0x14]\n"
        ".inst 0x0a000003 @ beq #0x14d0f0\n"
        ".inst 0xe59d0000 @ ldr r0, [sp]\n"
        ".inst 0xe0800004 @ add r0, r0, r4\n"
        ".inst 0xe5901004 @ ldr r1, [r0, #4]\n"
        ".inst 0xe0800001 @ add r0, r0, r1\n"
        ".inst 0xe8bd8038 @ pop {r3, r4, r5, pc}\n"
        ".word 0x004765dd @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014d2a8, 60)
extern "C" __attribute__((naked)) void engine_func_0014d2a8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe5d0100c @ ldrb r1, [r0, #0xc]\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x0a000007 @ beq #0x14d2d8\n"
        ".inst 0xe5904000 @ ldr r4, [r0]\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xeb056ac4 @ bl #0x2a7dd8\n"
        ".inst 0xe59f1014 @ ldr r1, [pc, #0x14]\n"
        ".inst 0xe7940000 @ ldr r0, [r4, r0]\n"
        ".inst 0xe1500001 @ cmp r0, r1\n"
        ".inst 0x03a00001 @ moveq r0, #1\n"
        ".inst 0x0a000000 @ beq #0x14d2dc\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x54415743 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014f5b4, 60)
extern "C" __attribute__((naked)) void func_0014f5b4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05002 @ mov r5, r2\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f2024 @ ldr r2, [pc, #0x24]\n"
        ".inst 0xe5a42080 @ str r2, [r4, #0x80]!\n"
        ".inst 0xe5841004 @ str r1, [r4, #4]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2101102 @ ands r1, r0, #0x80000000\n"
        ".inst 0x4a000002 @ bmi #0x14f5e8\n"
        ".inst 0xe5940008 @ ldr r0, [r4, #8]\n"
        ".inst 0xe5850000 @ str r0, [r5]\n"
        ".inst 0xe5940004 @ ldr r0, [r4, #4]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x000c0040 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00155ce4, 60)
extern "C" __attribute__((naked)) void func_00155ce4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f5028 @ ldr r5, [pc, #0x28]\n"
        ".inst 0xe3a0c000 @ mov ip, #0\n"
        ".inst 0xe5a45080 @ str r5, [r4, #0x80]!\n"
        ".inst 0xe2846004 @ add r6, r4, #4\n"
        ".inst 0xe5841010 @ str r1, [r4, #0x10]\n"
        ".inst 0xe886100c @ stm r6, {r2, r3, ip}\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
        ".word 0x00130082 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0015754c, 60)
extern "C" __attribute__((naked)) void func_0015754c() {
    asm volatile(
        ".arm\n"
        ".inst 0xeddf0a0c @ vldr s1, [pc, #0x30]\n"
        ".inst 0xe0801101 @ add r1, r0, r1, lsl #2\n"
        ".inst 0xeeb40ae0 @ vcmpe.f32 s0, s1\n"
        ".inst 0xeef1fa10 @ vmrs apsr_nzcv, fpscr\n"
        ".inst 0x3eb00a60 @ vmovlo.f32 s0, s1\n"
        ".inst 0xedd10a12 @ vldr s1, [r1, #0x48]\n"
        ".inst 0xeef40a40 @ vcmp.f32 s1, s0\n"
        ".inst 0xeef1fa10 @ vmrs apsr_nzcv, fpscr\n"
        ".inst 0x0a000003 @ beq #0x157580\n"
        ".inst 0xed810a12 @ vstr s0, [r1, #0x48]\n"
        ".inst 0xe1d012b0 @ ldrh r1, [r0, #0x20]\n"
        ".inst 0xe3811008 @ orr r1, r1, #8\n"
        ".inst 0xe1c012b0 @ strh r1, [r0, #0x20]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00000000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0015ed54, 60)
extern "C" __attribute__((naked)) void func_0015ed54() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1d006bc @ ldrh r0, [r0, #0x6c]\n"
        ".inst 0xe3100902 @ tst r0, #0x8000\n"
        ".inst 0x0a000007 @ beq #0x15ed88\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe1d420f4 @ ldrsh r2, [r4, #4]\n"
        ".inst 0xe20010ff @ and r1, r0, #0xff\n"
        ".inst 0xe59f0010 @ ldr r0, [pc, #0x10]\n"
        ".inst 0xeb0000b8 @ bl #0x15f060\n"
        ".inst 0xe1d406bc @ ldrh r0, [r4, #0x6c]\n"
        ".inst 0xe3c00902 @ bic r0, r0, #0x8000\n"
        ".inst 0xe1c406bc @ strh r0, [r4, #0x6c]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004e6f64 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001a95b8, 60)
extern "C" __attribute__((naked)) void func_001a95b8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb0378ff @ bl #0x2879c0\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000008 @ beq #0x1a95ec\n"
        ".inst 0xe59f0020 @ ldr r0, [pc, #0x20]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe5901030 @ ldr r1, [r0, #0x30]\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x13a00000 @ movne r0, #0\n"
        ".inst 0x1a000002 @ bne #0x1a95ec\n"
        ".inst 0xe2800040 @ add r0, r0, #0x40\n"
        ".inst 0xeb07d701 @ bl #0x39f1f0\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0044cdf0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ad124, 60)
extern "C" __attribute__((naked)) void battle_func_001ad124() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f202c @ ldr r2, [pc, #0x2c]\n"
        ".inst 0xe5922000 @ ldr r2, [r2]\n"
        ".inst 0xe0422000 @ sub r2, r2, r0\n"
        ".inst 0xe2522001 @ subs r2, r2, #1\n"
        ".inst 0x4a000006 @ bmi #0x1ad154\n"
        ".inst 0xe0802180 @ add r2, r0, r0, lsl #3\n"
        ".inst 0xe0820280 @ add r0, r2, r0, lsl #5\n"
        ".inst 0xec910a08 @ vldmia r1, {s0, s1, s2, s3, s4, s5, s6, s7}\n"
        ".inst 0xe59f2010 @ ldr r2, [pc, #0x10]\n"
        ".inst 0xe0820180 @ add r0, r2, r0, lsl #3\n"
        ".inst 0xe28000fc @ add r0, r0, #0xfc\n"
        ".inst 0xec800a08 @ vstmia r0, {s0, s1, s2, s3, s4, s5, s6, s7}\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00433278 @ tail data\n"
        ".word 0x00478000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ad160, 60)
extern "C" __attribute__((naked)) void battle_func_001ad160() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f202c @ ldr r2, [pc, #0x2c]\n"
        ".inst 0xe5922000 @ ldr r2, [r2]\n"
        ".inst 0xe0422000 @ sub r2, r2, r0\n"
        ".inst 0xe2522001 @ subs r2, r2, #1\n"
        ".inst 0x4a000006 @ bmi #0x1ad190\n"
        ".inst 0xe0802180 @ add r2, r0, r0, lsl #3\n"
        ".inst 0xe0820280 @ add r0, r2, r0, lsl #5\n"
        ".inst 0xec910a08 @ vldmia r1, {s0, s1, s2, s3, s4, s5, s6, s7}\n"
        ".inst 0xe59f2010 @ ldr r2, [pc, #0x10]\n"
        ".inst 0xe0820180 @ add r0, r2, r0, lsl #3\n"
        ".inst 0xe2800f47 @ add r0, r0, #0x11c\n"
        ".inst 0xec800a08 @ vstmia r0, {s0, s1, s2, s3, s4, s5, s6, s7}\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00433278 @ tail data\n"
        ".word 0x00478000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ad19c, 60)
extern "C" __attribute__((naked)) void battle_func_001ad19c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f202c @ ldr r2, [pc, #0x2c]\n"
        ".inst 0xe5922000 @ ldr r2, [r2]\n"
        ".inst 0xe0422000 @ sub r2, r2, r0\n"
        ".inst 0xe2522001 @ subs r2, r2, #1\n"
        ".inst 0x4a000006 @ bmi #0x1ad1cc\n"
        ".inst 0xe0802180 @ add r2, r0, r0, lsl #3\n"
        ".inst 0xe0820280 @ add r0, r2, r0, lsl #5\n"
        ".inst 0xec910a08 @ vldmia r1, {s0, s1, s2, s3, s4, s5, s6, s7}\n"
        ".inst 0xe59f2010 @ ldr r2, [pc, #0x10]\n"
        ".inst 0xe0820180 @ add r0, r2, r0, lsl #3\n"
        ".inst 0xe28000bc @ add r0, r0, #0xbc\n"
        ".inst 0xec800a08 @ vstmia r0, {s0, s1, s2, s3, s4, s5, s6, s7}\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00433278 @ tail data\n"
        ".word 0x00478000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ad380, 60)
extern "C" __attribute__((naked)) void battle_func_001ad380() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f202c @ ldr r2, [pc, #0x2c]\n"
        ".inst 0xe5922000 @ ldr r2, [r2]\n"
        ".inst 0xe0422000 @ sub r2, r2, r0\n"
        ".inst 0xe2522001 @ subs r2, r2, #1\n"
        ".inst 0x4a000006 @ bmi #0x1ad3b0\n"
        ".inst 0xe0802180 @ add r2, r0, r0, lsl #3\n"
        ".inst 0xe0820280 @ add r0, r2, r0, lsl #5\n"
        ".inst 0xec910a08 @ vldmia r1, {s0, s1, s2, s3, s4, s5, s6, s7}\n"
        ".inst 0xe59f2010 @ ldr r2, [pc, #0x10]\n"
        ".inst 0xe0820180 @ add r0, r2, r0, lsl #3\n"
        ".inst 0xe28000dc @ add r0, r0, #0xdc\n"
        ".inst 0xec800a08 @ vstmia r0, {s0, s1, s2, s3, s4, s5, s6, s7}\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00433278 @ tail data\n"
        ".word 0x00478000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001c1c8c, 60)
extern "C" __attribute__((naked)) void func_001c1c8c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xeb0356c5 @ bl #0x2977b0\n"
        ".inst 0xe5941018 @ ldr r1, [r4, #0x18]\n"
        ".inst 0xe59420bc @ ldr r2, [r4, #0xbc]\n"
        ".inst 0xe3a03002 @ mov r3, #2\n"
        ".inst 0xe594c0e8 @ ldr ip, [r4, #0xe8]\n"
        ".inst 0xe0831101 @ add r1, r3, r1, lsl #2\n"
        ".inst 0xe19210b1 @ ldrh r1, [r2, r1]\n"
        ".inst 0xe78c0101 @ str r0, [ip, r1, lsl #2]\n"
        ".inst 0xe5940018 @ ldr r0, [r4, #0x18]\n"
        ".inst 0xe2800001 @ add r0, r0, #1\n"
        ".inst 0xe5840018 @ str r0, [r4, #0x18]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001db94c, 60)
extern "C" __attribute__((naked)) void ui_func_001db94c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe3a01048 @ mov r1, #0x48\n"
        ".inst 0xeb03a474 @ bl #0x2c4b30\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe59f301c @ ldr r3, [pc, #0x1c]\n"
        ".inst 0xe3a01002 @ mov r1, #2\n"
        ".inst 0xe584003c @ str r0, [r4, #0x3c]\n"
        ".inst 0xe3a02801 @ mov r2, #0x10000\n"
        ".inst 0xe5841038 @ str r1, [r4, #0x38]\n"
        ".inst 0xe5842008 @ str r2, [r4, #8]\n"
        ".inst 0xe5843004 @ str r3, [r4, #4]\n"
        ".inst 0xe5840040 @ str r0, [r4, #0x40]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00000de1 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001dc88c, 60)
extern "C" __attribute__((naked)) void engine_func_001dc88c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe59f402c @ ldr r4, [pc, #0x2c]\n"
        ".inst 0xe1d400d1 @ ldrsb r0, [r4, #1]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0xca000004 @ bgt #0x1dc8b4\n"
        ".inst 0xe3a00011 @ mov r0, #0x11\n"
        ".inst 0xeb03a15f @ bl #0x2c4e28\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe3a00011 @ mov r0, #0x11\n"
        ".inst 0xeb03a480 @ bl #0x2c5ab8\n"
        ".inst 0xe5d40001 @ ldrb r0, [r4, #1]\n"
        ".inst 0xe2800001 @ add r0, r0, #1\n"
        ".inst 0xe5c40001 @ strb r0, [r4, #1]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0043dc20 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001dcf80, 60)
extern "C" __attribute__((naked)) void battle_func_001dcf80() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb02e7f4 @ bl #0x296f60\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xeb02e7f1 @ bl #0x296f60\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xeb04cef2 @ bl #0x310b70\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xeb02b19e @ bl #0x289628\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xeb02c3e7 @ bl #0x28df54\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001e15ec, 60)
extern "C" __attribute__((naked)) void script_vm_func_001e15ec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xe1d000b0 @ ldrh r0, [r0]\n"
        ".inst 0xeb035440 @ bl #0x2b6700\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1d500b0 @ ldrh r0, [r5]\n"
        ".inst 0xeb03543d @ bl #0x2b6700\n"
        ".inst 0xe3540000 @ cmp r4, #0\n"
        ".inst 0x03a00000 @ moveq r0, #0\n"
        ".inst 0x13500000 @ cmpne r0, #0\n"
        ".inst 0x0a000002 @ beq #0x1e1624\n"
        ".inst 0xe1d410b4 @ ldrh r1, [r4, #4]\n"
        ".inst 0xe1d000b4 @ ldrh r0, [r0, #4]\n"
        ".inst 0xe0410000 @ sub r0, r1, r0\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x001e1f10, 60)
extern "C" __attribute__((naked)) void battle_func_001e1f10() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a00000 @ mov r0, r0\n"
        ".inst 0xe59f0024 @ ldr r0, [pc, #0x24]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xeb0389a2 @ bl #0x2c45b8\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe5901754 @ ldr r1, [r0, #0x754]\n"
        ".inst 0xe3c11070 @ bic r1, r1, #0x70\n"
        ".inst 0xe5801754 @ str r1, [r0, #0x754]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0043e0d0 @ tail data\n"
        ".word 0x00432fc8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ed4d4, 60)
extern "C" __attribute__((naked)) void engine_func_001ed4d4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe3a04000 @ mov r4, #0\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xeb02a69e @ bl #0x296f60\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xeb01b007 @ bl #0x259510\n"
        ".inst 0xfafc4db7 @ blx #0x100bd4\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe1a00005 @ mov r0, r5\n"
        ".inst 0xebfff76a @ bl #0x1eb2ac\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x13a04001 @ movne r4, #1\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0010f524, 64)
extern "C" __attribute__((naked)) void func_0010f524() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f1028 @ ldr r1, [pc, #0x28]\n"
        ".inst 0xe5a41080 @ str r1, [r4, #0x80]!\n"
        ".inst 0xe5840004 @ str r0, [r4, #4]\n"
        ".inst 0xe3a00020 @ mov r0, #0x20\n"
        ".inst 0xe5840008 @ str r0, [r4, #8]\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00400042 @ tail data\n"
        ".word 0x004655f8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d9bc, 64)
extern "C" __attribute__((naked)) void func_0011d9bc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe3a02004 @ mov r2, #4\n"
        ".inst 0xe3a0100c @ mov r1, #0xc\n"
        ".inst 0xe5903008 @ ldr r3, [r0, #8]\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe12fff33 @ blx r3\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000003 @ beq #0x11d9f4\n"
        ".inst 0xe59f200c @ ldr r2, [pc, #0xc]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe5801008 @ str r1, [r0, #8]\n"
        ".inst 0xe8800014 @ stm r0, {r2, r4}\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00420d20 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011fee0, 64)
extern "C" __attribute__((naked)) void func_0011fee0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe5910000 @ ldr r0, [r1]\n"
        ".inst 0xe1a04001 @ mov r4, r1\n"
        ".inst 0xe3a02004 @ mov r2, #4\n"
        ".inst 0xe3a0100c @ mov r1, #0xc\n"
        ".inst 0xe5903008 @ ldr r3, [r0, #8]\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe12fff33 @ blx r3\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000003 @ beq #0x11ff18\n"
        ".inst 0xe59f200c @ ldr r2, [pc, #0xc]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe5801008 @ str r1, [r0, #8]\n"
        ".inst 0xe8800014 @ stm r0, {r2, r4}\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00420eb4 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00120dd4, 64)
extern "C" __attribute__((naked)) void engine_func_00120dd4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5d00081 @ ldrb r0, [r0, #0x81]\n"
        ".inst 0xe1a05002 @ mov r5, r2\n"
        ".inst 0xe1a06001 @ mov r6, r1\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x1a000007 @ bne #0x120e10\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xeb003944 @ bl #0x12f30c\n"
        ".inst 0xe3a01001 @ mov r1, #1\n"
        ".inst 0xe5c41081 @ strb r1, [r4, #0x81]\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe584505c @ str r5, [r4, #0x5c]\n"
        ".inst 0xe5c40082 @ strb r0, [r4, #0x82]\n"
        ".inst 0xe5846060 @ str r6, [r4, #0x60]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x00121a98, 64)
extern "C" __attribute__((naked)) void engine_func_00121a98() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d41f0 @ push {r4, r5, r6, r7, r8, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe2805004 @ add r5, r0, #4\n"
        ".inst 0xe1a06001 @ mov r6, r1\n"
        ".inst 0xe1a07002 @ mov r7, r2\n"
        ".inst 0xe1a00005 @ mov r0, r5\n"
        ".inst 0xeb0687fc @ bl #0x2c3aa8\n"
        ".inst 0xe1a02007 @ mov r2, r7\n"
        ".inst 0xe1a01006 @ mov r1, r6\n"
        ".inst 0xe2840010 @ add r0, r4, #0x10\n"
        ".inst 0xeb003de0 @ bl #0x131248\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe1a00005 @ mov r0, r5\n"
        ".inst 0xeb0687d4 @ bl #0x2c3a24\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe8bd81f0 @ pop {r4, r5, r6, r7, r8, pc}\n"
    );
}

// DECOMP_FUNC(0x00123050, 64)
extern "C" __attribute__((naked)) void battle_func_00123050() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe59f4030 @ ldr r4, [pc, #0x30]\n"
        ".inst 0xe5840000 @ str r0, [r4]\n"
        ".inst 0xeb004fd0 @ bl #0x136fa4\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe2800004 @ add r0, r0, #4\n"
        ".inst 0xeb003fd2 @ bl #0x132fb8\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe2800008 @ add r0, r0, #8\n"
        ".inst 0xeb007cd1 @ bl #0x1423c0\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe280000c @ add r0, r0, #0xc\n"
        ".inst 0xeb004101 @ bl #0x13348c\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0044e32c @ tail data\n"
    );
}

// DECOMP_FUNC(0x00123444, 64)
extern "C" __attribute__((naked)) void func_00123444() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f2034 @ ldr r2, [pc, #0x34]\n"
        ".inst 0xe592209c @ ldr r2, [r2, #0x9c]\n"
        ".inst 0xe3520000 @ cmp r2, #0\n"
        ".inst 0x0a000009 @ beq #0x12347c\n"
        ".inst 0xe3500c02 @ cmp r0, #0x200\n"
        ".inst 0x0582102c @ streq r1, [r2, #0x2c]\n"
        ".inst 0x0a000006 @ beq #0x12347c\n"
        ".inst 0xe2400c02 @ sub r0, r0, #0x200\n"
        ".inst 0xe250000f @ subs r0, r0, #0xf\n"
        ".inst 0x1a000003 @ bne #0x12347c\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x13a00001 @ movne r0, #1\n"
        ".inst 0x03a00000 @ moveq r0, #0\n"
        ".inst 0xe5c2003d @ strb r0, [r2, #0x3d]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x004c6290 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00130fa8, 64)
extern "C" __attribute__((naked)) void engine_func_00130fa8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5d00010 @ ldrb r0, [r0, #0x10]\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xe1a06002 @ mov r6, r2\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x1a000007 @ bne #0x130fe4\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe3a03f51 @ mov r3, #0x144\n"
        ".inst 0xeb061027 @ bl #0x2b5070\n"
        ".inst 0xe2843014 @ add r3, r4, #0x14\n"
        ".inst 0xe3a01001 @ mov r1, #1\n"
        ".inst 0xe8830021 @ stm r3, {r0, r5}\n"
        ".inst 0xe5c41010 @ strb r1, [r4, #0x10]\n"
        ".inst 0xe584601c @ str r6, [r4, #0x1c]\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x00132a20, 64)
extern "C" __attribute__((naked)) void engine_func_00132a20() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1034 @ ldr r1, [pc, #0x34]\n"
        ".inst 0xe1d021b4 @ ldrh r2, [r0, #0x14]\n"
        ".inst 0xe1520001 @ cmp r2, r1\n"
        ".inst 0x02800014 @ addeq r0, r0, #0x14\n"
        ".inst 0x0a000007 @ beq #0x132a54\n"
        ".inst 0xe1d022b0 @ ldrh r2, [r0, #0x20]\n"
        ".inst 0xe1520001 @ cmp r2, r1\n"
        ".inst 0x02800020 @ addeq r0, r0, #0x20\n"
        ".inst 0x0a000003 @ beq #0x132a54\n"
        ".inst 0xe1d022bc @ ldrh r2, [r0, #0x2c]\n"
        ".inst 0xe1520001 @ cmp r2, r1\n"
        ".inst 0x0280002c @ addeq r0, r0, #0x2c\n"
        ".inst 0x13a00000 @ movne r0, #0\n"
        ".inst 0xe5900008 @ ldr r0, [r0, #8]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00002001 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00132a60, 64)
extern "C" __attribute__((naked)) void engine_func_00132a60() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1034 @ ldr r1, [pc, #0x34]\n"
        ".inst 0xe1d021b4 @ ldrh r2, [r0, #0x14]\n"
        ".inst 0xe1520001 @ cmp r2, r1\n"
        ".inst 0x02800014 @ addeq r0, r0, #0x14\n"
        ".inst 0x0a000007 @ beq #0x132a94\n"
        ".inst 0xe1d022b0 @ ldrh r2, [r0, #0x20]\n"
        ".inst 0xe1520001 @ cmp r2, r1\n"
        ".inst 0x02800020 @ addeq r0, r0, #0x20\n"
        ".inst 0x0a000003 @ beq #0x132a94\n"
        ".inst 0xe1d022bc @ ldrh r2, [r0, #0x2c]\n"
        ".inst 0xe1520001 @ cmp r2, r1\n"
        ".inst 0x0280002c @ addeq r0, r0, #0x2c\n"
        ".inst 0x13a00000 @ movne r0, #0\n"
        ".inst 0xe5900004 @ ldr r0, [r0, #4]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00002001 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013a234, 64)
extern "C" __attribute__((naked)) void func_0013a234() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d47f0 @ push {r4, r5, r6, r7, r8, sb, sl, lr}\n"
        ".inst 0xe24dd010 @ sub sp, sp, #0x10\n"
        ".inst 0xe1a08000 @ mov r8, r0\n"
        ".inst 0xe28d0030 @ add r0, sp, #0x30\n"
        ".inst 0xe1a09001 @ mov sb, r1\n"
        ".inst 0xe89000e0 @ ldm r0, {r5, r6, r7}\n"
        ".inst 0xe1a0a002 @ mov sl, r2\n"
        ".inst 0xe1a04003 @ mov r4, r3\n"
        ".inst 0xeb05ccf5 @ bl #0x2ad630\n"
        ".inst 0xe1a0300a @ mov r3, sl\n"
        ".inst 0xe1a02009 @ mov r2, sb\n"
        ".inst 0xe1a01008 @ mov r1, r8\n"
        ".inst 0xe88d00f0 @ stm sp, {r4, r5, r6, r7}\n"
        ".inst 0xeb0032be @ bl #0x146d68\n"
        ".inst 0xe28dd010 @ add sp, sp, #0x10\n"
        ".inst 0xe8bd87f0 @ pop {r4, r5, r6, r7, r8, sb, sl, pc}\n"
    );
}

// DECOMP_FUNC(0x0013b7c8, 64)
extern "C" __attribute__((naked)) void func_0013b7c8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe59f402c @ ldr r4, [pc, #0x2c]\n"
        ".inst 0xe5d40000 @ ldrb r0, [r4]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000007 @ beq #0x13b7fc\n"
        ".inst 0xe5d40001 @ ldrb r0, [r4, #1]\n"
        ".inst 0xeb000035 @ bl #0x13b8bc\n"
        ".inst 0xe59f1018 @ ldr r1, [pc, #0x18]\n"
        ".inst 0xe1500001 @ cmp r0, r1\n"
        ".inst 0x1a000002 @ bne #0x13b7fc\n"
        ".inst 0xe5d40001 @ ldrb r0, [r4, #1]\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xea000011 @ b #0x13b844\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004656c8 @ tail data\n"
        ".word 0xc9405001 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014150c, 64)
extern "C" __attribute__((naked)) void func_0014150c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1034 @ ldr r1, [pc, #0x34]\n"
        ".inst 0xe1d021b4 @ ldrh r2, [r0, #0x14]\n"
        ".inst 0xe1520001 @ cmp r2, r1\n"
        ".inst 0x02800014 @ addeq r0, r0, #0x14\n"
        ".inst 0x0a000007 @ beq #0x141540\n"
        ".inst 0xe1d022b0 @ ldrh r2, [r0, #0x20]\n"
        ".inst 0xe1520001 @ cmp r2, r1\n"
        ".inst 0x02800020 @ addeq r0, r0, #0x20\n"
        ".inst 0x0a000003 @ beq #0x141540\n"
        ".inst 0xe1d022bc @ ldrh r2, [r0, #0x2c]\n"
        ".inst 0xe1520001 @ cmp r2, r1\n"
        ".inst 0x0280002c @ addeq r0, r0, #0x2c\n"
        ".inst 0x13a00000 @ movne r0, #0\n"
        ".inst 0xe5900004 @ ldr r0, [r0, #4]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00002002 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00144e60, 64)
extern "C" __attribute__((naked)) void engine_func_00144e60() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1034 @ ldr r1, [pc, #0x34]\n"
        ".inst 0xe5d12000 @ ldrb r2, [r1]\n"
        ".inst 0xe3520000 @ cmp r2, #0\n"
        ".inst 0x15d12001 @ ldrbne r2, [r1, #1]\n"
        ".inst 0x13520000 @ cmpne r2, #0\n"
        ".inst 0x0a000007 @ beq #0x144e98\n"
        ".inst 0xe5912004 @ ldr r2, [r1, #4]\n"
        ".inst 0xe2821c4e @ add r1, r2, #0x4e00\n"
        ".inst 0xe1d130f0 @ ldrsh r3, [r1]\n"
        ".inst 0xe063c183 @ rsb ip, r3, r3, lsl #3\n"
        ".inst 0xe08c3283 @ add r3, ip, r3, lsl #5\n"
        ".inst 0xe7c20183 @ strb r0, [r2, r3, lsl #3]\n"
        ".inst 0xe1d100b0 @ ldrh r0, [r1]\n"
        ".inst 0xe1c100b4 @ strh r0, [r1, #4]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x004729b8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001467ac, 64)
extern "C" __attribute__((naked)) void func_001467ac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a03000 @ mov r3, r0\n"
        ".inst 0xe59f0030 @ ldr r0, [pc, #0x30]\n"
        ".inst 0xe3e02000 @ mvn r2, #0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe5812000 @ str r2, [r1]\n"
        ".inst 0xe5900008 @ ldr r0, [r0, #8]\n"
        ".inst 0xe59f4018 @ ldr r4, [pc, #0x18]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000002 @ beq #0x1467dc\n"
        ".inst 0xe1a02001 @ mov r2, r1\n"
        ".inst 0xe1a01003 @ mov r1, r3\n"
        ".inst 0xeb002375 @ bl #0x14f5b4\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0xc8a0a7f8 @ tail data\n"
        ".word 0x0044e458 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001521d8, 64)
extern "C" __attribute__((naked)) void engine_func_001521d8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5d0000c @ ldrb r0, [r0, #0xc]\n"
        ".inst 0xe1a05001 @ mov r5, r1\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000008 @ beq #0x152214\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xeb0556f7 @ bl #0x2a7dd8\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe5940004 @ ldr r0, [r4, #4]\n"
        ".inst 0xe0852085 @ add r2, r5, r5, lsl #1\n"
        ".inst 0xe0800102 @ add r0, r0, r2, lsl #2\n"
        ".inst 0xe5900008 @ ldr r0, [r0, #8]\n"
        ".inst 0xe0800001 @ add r0, r0, r1\n"
        ".inst 0xe2800008 @ add r0, r0, #8\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}
