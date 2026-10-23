#include "types.h"

// Batch 22 A: fixed-width instruction encodings preserve original bytes and Thumb state.
// Bounded post-return literal/padding bytes are emitted as data.

// DECOMP_FUNC(0x001174e4, 32)
extern "C" __attribute__((naked)) void ui_func_001174e4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb06a576 @ bl #0x2c0ac8\n"
        ".inst 0xeb06b39b @ bl #0x2c4360\n"
        ".inst 0xe59f1008 @ ldr r1, [pc, #8]\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe5810000 @ str r0, [r1]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00464ad8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d0b4, 32)
extern "C" __attribute__((naked)) void func_0011d0b4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5900018 @ ldr r0, [r0, #0x18]\n"
        ".inst 0xe2000007 @ and r0, r0, #7\n"
        ".inst 0xe3500006 @ cmp r0, #6\n"
        ".inst 0x03a00001 @ moveq r0, #1\n"
        ".inst 0x13a00000 @ movne r0, #0\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00121f20, 32)
extern "C" __attribute__((naked)) void engine_func_00121f20() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a00001 @ mov r0, r1\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb007e7d @ bl #0x141924\n"
        ".inst 0xe3a01004 @ mov r1, #4\n"
        ".inst 0xe0810100 @ add r0, r1, r0, lsl #2\n"
        ".inst 0xe2800003 @ add r0, r0, #3\n"
        ".inst 0xe3c00003 @ bic r0, r0, #3\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0015c434, 32)
extern "C" __attribute__((naked)) void func_0015c434() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5900030 @ ldr r0, [r0, #0x30]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000003 @ beq #0x15c450\n"
        ".inst 0xe1a03002 @ mov r3, r2\n"
        ".inst 0xe1a02001 @ mov r2, r1\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xea000532 @ b #0x15d91c\n"
        ".inst 0xe12fff1e @ bx lr\n"
    );
}

// DECOMP_FUNC(0x0019da44, 32)
extern "C" __attribute__((naked)) void func_0019da44() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe59f0010 @ ldr r0, [pc, #0x10]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000000 @ beq #0x19da5c\n"
        ".inst 0xea065f3b @ b #0x33574c\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00434260 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001a1538, 32)
extern "C" __attribute__((naked)) void ui_func_001a1538() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe3a01001 @ mov r1, #1\n"
        ".inst 0xe5900008 @ ldr r0, [r0, #8]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x15c01030 @ strbne r1, [r0, #0x30]\n"
        ".inst 0xe5c01031 @ strb r1, [r0, #0x31]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0043e188 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001adc78, 32)
extern "C" __attribute__((naked)) void camp_func_001adc78() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe590047c @ ldr r0, [r0, #0x47c]\n"
        ".inst 0xe3a0203c @ mov r2, #0x3c\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xeb03ca6c @ bl #0x2a0640\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0043dd68 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001b41e0, 32)
extern "C" __attribute__((naked)) void script_vm_func_001b41e0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe3a01003 @ mov r1, #3\n"
        ".inst 0xe3a02000 @ mov r2, #0\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe2800004 @ add r0, r0, #4\n"
        ".inst 0xe8800006 @ stm r0, {r1, r2}\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00447600 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001c35b8, 32)
extern "C" __attribute__((naked)) void func_001c35b8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5900004 @ ldr r0, [r0, #4]\n"
        ".inst 0xe5901660 @ ldr r1, [r0, #0x660]\n"
        ".inst 0xe5900658 @ ldr r0, [r0, #0x658]\n"
        ".inst 0xe0410000 @ sub r0, r1, r0\n"
        ".inst 0xe6bf0070 @ sxth r0, r0\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0043dcb0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001c87b8, 32)
extern "C" __attribute__((naked)) void func_001c87b8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe5901008 @ ldr r1, [r0, #8]\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x11d001d0 @ ldrsbne r0, [r0, #0x10]\n"
        ".inst 0x03a00000 @ moveq r0, #0\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0043e140 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001dc86c, 32)
extern "C" __attribute__((naked)) void engine_func_001dc86c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb02e9b9 @ bl #0x296f60\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0xc6ff0070 @ uxthgt r0, r0\n"
        ".inst 0xcbfd1f0c @ blgt #0x1244b8\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001dd158, 32)
extern "C" __attribute__((naked)) void script_vm_func_001dd158() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1014 @ ldr r1, [pc, #0x14]\n"
        ".inst 0xe5911004 @ ldr r1, [r1, #4]\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x10810180 @ addne r0, r1, r0, lsl #3\n"
        ".inst 0x11d000fa @ ldrshne r0, [r0, #0xa]\n"
        ".inst 0x03a00000 @ moveq r0, #0\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0043dcb0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001dd7e8, 32)
extern "C" __attribute__((naked)) void func_001dd7e8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000001 @ beq #0x1dd800\n"
        ".inst 0xe2800034 @ add r0, r0, #0x34\n"
        ".inst 0xea0385de @ b #0x2bef7c\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0043e140 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001dd808, 32)
extern "C" __attribute__((naked)) void func_001dd808() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000001 @ beq #0x1dd820\n"
        ".inst 0xe2800034 @ add r0, r0, #0x34\n"
        ".inst 0xea0385d3 @ b #0x2bef70\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0043e140 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001dfb40, 32)
extern "C" __attribute__((naked)) void ui_func_001dfb40() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb0383df @ bl #0x2c0ac8\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe591100c @ ldr r1, [r1, #0xc]\n"
        ".inst 0xe12fff31 @ blx r1\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001e255c, 32)
extern "C" __attribute__((naked)) void script_vm_func_001e255c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe1d011b4 @ ldrh r1, [r0, #0x14]\n"
        ".inst 0xe3510001 @ cmp r1, #1\n"
        ".inst 0x03a01002 @ moveq r1, #2\n"
        ".inst 0x01c011b4 @ strheq r1, [r0, #0x14]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x004474d8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001e38a0, 32)
extern "C" __attribute__((naked)) void script_vm_func_001e38a0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb01e1f3 @ bl #0x25c07c\n"
        ".inst 0xe59f1008 @ ldr r1, [pc, #8]\n"
        ".inst 0xe5911000 @ ldr r1, [r1]\n"
        ".inst 0xe58106d4 @ str r0, [r1, #0x6d4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00447e70 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001e444c, 32)
extern "C" __attribute__((naked)) void script_vm_func_001e444c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe590002c @ ldr r0, [r0, #0x2c]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000000 @ beq #0x1e4464\n"
        ".inst 0xeafdb9a4 @ b #0x152af8\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0044cda0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001eb740, 32)
extern "C" __attribute__((naked)) void func_001eb740() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5900004 @ ldr r0, [r0, #4]\n"
        ".inst 0xe5900010 @ ldr r0, [r0, #0x10]\n"
        ".inst 0xe3500002 @ cmp r0, #2\n"
        ".inst 0x03a00001 @ moveq r0, #1\n"
        ".inst 0x13a00000 @ movne r0, #0\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0043da28 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ed2c4, 32)
extern "C" __attribute__((naked)) void engine_func_001ed2c4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0b0404f1 @ bleq #0x2ee6a0\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0043ded0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ee97c, 32)
extern "C" __attribute__((naked)) void camp_func_001ee97c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe5900004 @ ldr r0, [r0, #4]\n"
        ".inst 0xe3500008 @ cmp r0, #8\n"
        ".inst 0x03a00001 @ moveq r0, #1\n"
        ".inst 0x13a00000 @ movne r0, #0\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0043dd90 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001f5db4, 32)
extern "C" __attribute__((naked)) void camp_func_001f5db4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5d01218 @ ldrb r1, [r0, #0x218]\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x1a000003 @ bne #0x1f5dd0\n"
        ".inst 0xe3a02001 @ mov r2, #1\n"
        ".inst 0xe3a01002 @ mov r1, #2\n"
        ".inst 0xe2800f71 @ add r0, r0, #0x1c4\n"
        ".inst 0xea031f3b @ b #0x2bdac0\n"
        ".inst 0xe12fff1e @ bx lr\n"
    );
}

// DECOMP_FUNC(0x00100b64, 36)
extern "C" __attribute__((naked)) void crt_func_00100b64() {
    asm volatile(
        ".thumb\n"
        ".hword 0xb51c\n"
        ".hword 0x4b07\n"
        ".hword 0x000c\n"
        ".hword 0x447b\n"
        ".hword 0x4669\n"
        ".hword 0x9000\n"
        ".hword 0x0020\n"
        ".hword 0xf1c5\n"
        ".hword 0xff5c\n"
        ".hword 0x0004\n"
        ".hword 0x4669\n"
        ".hword 0x2000\n"
        ".hword 0xf1c5\n"
        ".hword 0xff4d\n"
        ".hword 0x0020\n"
        ".hword 0xbd1c\n"
        ".hword 0x5ead @ tail data\n"
        ".hword 0x001c @ tail data\n"
        ".arm\n"
    );
}

// DECOMP_FUNC(0x001384f8, 36)
extern "C" __attribute__((naked)) void func_001384f8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5d01001 @ ldrb r1, [r0, #1]\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x15d00002 @ ldrbne r0, [r0, #2]\n"
        ".inst 0x13500000 @ cmpne r0, #0\n"
        ".inst 0x03a00000 @ moveq r0, #0\n"
        ".inst 0x13a00001 @ movne r0, #1\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00464af0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00144f98, 36)
extern "C" __attribute__((naked)) void engine_func_00144f98() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f2018 @ ldr r2, [pc, #0x18]\n"
        ".inst 0xe5d23000 @ ldrb r3, [r2]\n"
        ".inst 0xe3530000 @ cmp r3, #0\n"
        ".inst 0x15d23001 @ ldrbne r3, [r2, #1]\n"
        ".inst 0x13530000 @ cmpne r3, #0\n"
        ".inst 0x11c200fc @ strdne r0, r1, [r2, #0xc]\n"
        ".inst 0x0affffff @ beq #0x144fb4\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x004729b8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00150db8, 36)
extern "C" __attribute__((naked)) void ui_func_00150db8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f2018 @ ldr r2, [pc, #0x18]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe3a03f82 @ mov r3, #0x208\n"
        ".inst 0xe5801004 @ str r1, [r0, #4]\n"
        ".inst 0xe5802000 @ str r2, [r0]\n"
        ".inst 0xe18310b0 @ strh r1, [r3, r0]\n"
        ".inst 0xe5c0120a @ strb r1, [r0, #0x20a]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x004218e0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001a1558, 36)
extern "C" __attribute__((naked)) void script_vm_func_001a1558() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x159000f0 @ ldrne r0, [r0, #0xf0]\n"
        ".inst 0x13500007 @ cmpne r0, #7\n"
        ".inst 0x03a00001 @ moveq r0, #1\n"
        ".inst 0x13a00000 @ movne r0, #0\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0044d198 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001a157c, 36)
extern "C" __attribute__((naked)) void camp_func_001a157c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x15900344 @ ldrne r0, [r0, #0x344]\n"
        ".inst 0x13500003 @ cmpne r0, #3\n"
        ".inst 0x03a00001 @ moveq r0, #1\n"
        ".inst 0x13a00000 @ movne r0, #0\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0043dd08 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001b4b74, 36)
extern "C" __attribute__((naked)) void camp_func_001b4b74() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5900004 @ ldr r0, [r0, #4]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x15900008 @ ldrne r0, [r0, #8]\n"
        ".inst 0x13500000 @ cmpne r0, #0\n"
        ".inst 0x0a000000 @ beq #0x1b4b90\n"
        ".inst 0xea08176c @ b #0x3ba944\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0044cfd0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001eb348, 36)
extern "C" __attribute__((naked)) void ui_func_001eb348() {
    asm volatile(
        ".arm\n"
        ".inst 0xe28f0010 @ add r0, pc, #0x10\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb00d40f @ bl #0x220394\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x13a00001 @ movne r0, #1\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x72617453 @ tail data\n"
        ".word 0x6e654d74 @ tail data\n"
        ".word 0x00000075 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0012a62c, 40)
extern "C" __attribute__((naked)) void func_0012a62c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f001c @ ldr r0, [pc, #0x1c]\n"
        ".inst 0xe5d01001 @ ldrb r1, [r0, #1]\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x03a00000 @ moveq r0, #0\n"
        ".inst 0x0a000002 @ beq #0x12a64c\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe5c01001 @ strb r1, [r0, #1]\n"
        ".inst 0xea0041d7 @ b #0x13adac\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0044e360 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00141940, 40)
extern "C" __attribute__((naked)) void engine_func_00141940() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5900004 @ ldr r0, [r0, #4]\n"
        ".inst 0xe1a00000 @ mov r0, r0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe590003c @ ldr r0, [r0, #0x3c]\n"
        ".inst 0xeb059500 @ bl #0x2a6d58\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000001 @ beq #0x141964\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xea0594f0 @ b #0x2a6d28\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00149a1c, 40)
extern "C" __attribute__((naked)) void func_00149a1c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f201c @ ldr r2, [pc, #0x1c]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe0823101 @ add r3, r2, r1, lsl #2\n"
        ".inst 0xe2811001 @ add r1, r1, #1\n"
        ".inst 0xe3510018 @ cmp r1, #0x18\n"
        ".inst 0xe5830000 @ str r0, [r3]\n"
        ".inst 0xbafffff9 @ blt #0x149a24\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x004e9dc8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0015ef0c, 40)
extern "C" __attribute__((naked)) void func_0015ef0c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe20010ff @ and r1, r0, #0xff\n"
        ".inst 0xe59f000c @ ldr r0, [pc, #0xc]\n"
        ".inst 0xeb000039 @ bl #0x15f00c\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe5c4000c @ strb r0, [r4, #0xc]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004e6f64 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0017fa54, 40)
extern "C" __attribute__((naked)) void engine_func_0017fa54() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f001c @ ldr r0, [pc, #0x1c]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000003 @ beq #0x17fa74\n"
        ".inst 0xe5900018 @ ldr r0, [r0, #0x18]\n"
        ".inst 0xe3500030 @ cmp r0, #0x30\n"
        ".inst 0x03a00001 @ moveq r0, #1\n"
        ".inst 0x13a00000 @ movne r0, #0\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0043da90 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001a9948, 40)
extern "C" __attribute__((naked)) void engine_func_001a9948() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe59f4018 @ ldr r4, [pc, #0x18]\n"
        ".inst 0xe5940004 @ ldr r0, [r4, #4]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000002 @ beq #0x1a9968\n"
        ".inst 0xeb046a7f @ bl #0x2c4360\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe5840004 @ str r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00434278 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ab7c0, 40)
extern "C" __attribute__((naked)) void engine_func_001ab7c0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb03ade4 @ bl #0x296f60\n"
        ".inst 0xeb0454bd @ bl #0x2c0ac8\n"
        ".inst 0xed9f0a03 @ vldr s0, [pc, #0xc]\n"
        ".inst 0xed800a09 @ vstr s0, [r0, #0x24]\n"
        ".inst 0xed800a0a @ vstr s0, [r0, #0x28]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00000000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ab8d8, 40)
extern "C" __attribute__((naked)) void script_vm_func_001ab8d8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0008 @ ldr r0, [pc, #8]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe590000c @ ldr r0, [r0, #0xc]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".inst 0x0043e128 @ subeq lr, r3, r8, lsr #2\n"
        ".inst 0xe59f1008 @ ldr r1, [pc, #8]\n"
        ".inst 0xe5911000 @ ldr r1, [r1]\n"
        ".inst 0xe581000c @ str r0, [r1, #0xc]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0043e128 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001b71b8, 40)
extern "C" __attribute__((naked)) void ui_func_001b71b8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb042641 @ bl #0x2c0ac8\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000001 @ beq #0x1b71d8\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xea082633 @ b #0x3c0aa8\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00439b58 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ca620, 40)
extern "C" __attribute__((naked)) void engine_func_001ca620() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f001c @ ldr r0, [pc, #0x1c]\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x0a000002 @ beq #0x1ca640\n"
        ".inst 0xe591100c @ ldr r1, [r1, #0xc]\n"
        ".inst 0xe3510003 @ cmp r1, #3\n"
        ".inst 0x03a00001 @ moveq r0, #1\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0043df28 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001d2e24, 40)
extern "C" __attribute__((naked)) void script_vm_func_001d2e24() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f201c @ ldr r2, [pc, #0x1c]\n"
        ".inst 0xe3a0c000 @ mov ip, #0\n"
        ".inst 0xe3a03001 @ mov r3, #1\n"
        ".inst 0xe5922000 @ ldr r2, [r2]\n"
        ".inst 0xe1c2c0b8 @ strh ip, [r2, #8]\n"
        ".inst 0xe1c200b4 @ strh r0, [r2, #4]\n"
        ".inst 0xe1c210b6 @ strh r1, [r2, #6]\n"
        ".inst 0xe5c2300a @ strb r3, [r2, #0xa]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x004474d8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001e5d5c, 40)
extern "C" __attribute__((naked)) void engine_func_001e5d5c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe59f4018 @ ldr r4, [pc, #0x18]\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000002 @ beq #0x1e5d7c\n"
        ".inst 0xeb03797a @ bl #0x2c4360\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe5840000 @ str r0, [r4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00447a78 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001eb760, 40)
extern "C" __attribute__((naked)) void script_vm_func_001eb760() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f001c @ ldr r0, [pc, #0x1c]\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe5900004 @ ldr r0, [r0, #4]\n"
        ".inst 0xe5900560 @ ldr r0, [r0, #0x560]\n"
        ".inst 0xebfeca11 @ bl #0x19dfbc\n"
        ".inst 0xe3500002 @ cmp r0, #2\n"
        ".inst 0x03a00001 @ moveq r0, #1\n"
        ".inst 0x13a00000 @ movne r0, #0\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0043da28 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ebcfc, 40)
extern "C" __attribute__((naked)) void camp_func_001ebcfc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f001c @ ldr r0, [pc, #0x1c]\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x0a000002 @ beq #0x1ebd1c\n"
        ".inst 0xe5911d28 @ ldr r1, [r1, #0xd28]\n"
        ".inst 0xe351000f @ cmp r1, #0xf\n"
        ".inst 0x03a00001 @ moveq r0, #1\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0043daa8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011ba54, 44)
extern "C" __attribute__((naked)) void nn_sdk_func_0011ba54() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f101c @ ldr r1, [pc, #0x1c]\n"
        ".inst 0xe92d4008 @ push {r3, lr}\n"
        ".inst 0xe5810010 @ str r0, [r1, #0x10]\n"
        ".inst 0xe58d0000 @ str r0, [sp]\n"
        ".inst 0xe59f1010 @ ldr r1, [pc, #0x10]\n"
        ".inst 0xe1a0000d @ mov r0, sp\n"
        ".inst 0xeb002e18 @ bl #0x1272d4\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe8bd8008 @ pop {r3, pc}\n"
        ".word 0x0044e650 @ tail data\n"
        ".word 0x040201c8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d020, 44)
extern "C" __attribute__((naked)) void func_0011d020() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a00000 @ mov r0, r0\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5d00000 @ ldrb r0, [r0]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000002 @ beq #0x11d040\n"
        ".inst 0xe59f000c @ ldr r0, [pc, #0xc]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xea003323 @ b #0x129cd0\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00471a70 @ tail data\n"
        ".word 0x00471a84 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00130de4, 44)
extern "C" __attribute__((naked)) void func_00130de4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070 @ push {r4, r5, r6, lr}\n"
        ".inst 0xe1a05000 @ mov r5, r0\n"
        ".inst 0xe3a04000 @ mov r4, #0\n"
        ".inst 0xe7950104 @ ldr r0, [r5, r4, lsl #2]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x1b063208 @ blne #0x2bd620\n"
        ".inst 0xe2844001 @ add r4, r4, #1\n"
        ".inst 0xe3540002 @ cmp r4, #2\n"
        ".inst 0xbafffff9 @ blt #0x130df0\n"
        ".inst 0xe1a00005 @ mov r0, r5\n"
        ".inst 0xe8bd8070 @ pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x001311ac, 44)
extern "C" __attribute__((naked)) void engine_func_001311ac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f2020 @ ldr r2, [pc, #0x20]\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe3e01000 @ mvn r1, #0\n"
        ".inst 0xe0823080 @ add r3, r2, r0, lsl #1\n"
        ".inst 0xe2800002 @ add r0, r0, #2\n"
        ".inst 0xe1c310b0 @ strh r1, [r3]\n"
        ".inst 0xe1c310b2 @ strh r1, [r3, #2]\n"
        ".inst 0xe3500010 @ cmp r0, #0x10\n"
        ".inst 0xbafffff9 @ blt #0x1311b8\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x004ea494 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00139bac, 44)
extern "C" __attribute__((naked)) void func_00139bac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f2020 @ ldr r2, [pc, #0x20]\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5922008 @ ldr r2, [r2, #8]\n"
        ".inst 0xe3520000 @ cmp r2, #0\n"
        ".inst 0x0a000001 @ beq #0x139bcc\n"
        ".inst 0xe1a00002 @ mov r0, r2\n"
        ".inst 0xea003318 @ b #0x146830\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0xc8a0a7f8 @ tail data\n"
        ".word 0x0044e458 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00139bd8, 44)
extern "C" __attribute__((naked)) void func_00139bd8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f2020 @ ldr r2, [pc, #0x20]\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5922008 @ ldr r2, [r2, #8]\n"
        ".inst 0xe3520000 @ cmp r2, #0\n"
        ".inst 0x0a000001 @ beq #0x139bf8\n"
        ".inst 0xe1a00002 @ mov r0, r2\n"
        ".inst 0xea00332d @ b #0x1468b0\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0xc8a0a7f8 @ tail data\n"
        ".word 0x0044e458 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013c030, 44)
extern "C" __attribute__((naked)) void engine_func_0013c030() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a0c002 @ mov ip, r2\n"
        ".inst 0xe92d000f @ push {r0, r1, r2, r3}\n"
        ".inst 0xe28cc001 @ add ip, ip, #1\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe151000c @ cmp r1, ip\n"
        ".inst 0xe59d2014 @ ldr r2, [sp, #0x14]\n"
        ".inst 0xe28d3018 @ add r3, sp, #0x18\n"
        ".inst 0x81a0100c @ movhi r1, ip\n"
        ".inst 0xfa05d947 @ blx #0x2b2574\n"
        ".inst 0xe49d4004 @ pop {r4}\n"
        ".inst 0xe49df014 @ ldr pc, [sp], #0x14\n"
    );
}

// DECOMP_FUNC(0x0014672c, 44)
extern "C" __attribute__((naked)) void func_0014672c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f2020 @ ldr r2, [pc, #0x20]\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5922008 @ ldr r2, [r2, #8]\n"
        ".inst 0xe3520000 @ cmp r2, #0\n"
        ".inst 0x0a000001 @ beq #0x14674c\n"
        ".inst 0xe1a00002 @ mov r0, r2\n"
        ".inst 0xea002371 @ b #0x14f514\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0xc8a0a7f8 @ tail data\n"
        ".word 0x0044e458 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00150ea0, 44)
extern "C" __attribute__((naked)) void func_00150ea0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1018 @ ldr r1, [pc, #0x18]\n"
        ".inst 0xe59f3018 @ ldr r3, [pc, #0x18]\n"
        ".inst 0xe59f2018 @ ldr r2, [pc, #0x18]\n"
        ".inst 0xe5910000 @ ldr r0, [r1]\n"
        ".inst 0xe0222390 @ mla r2, r0, r3, r2\n"
        ".inst 0xe5812000 @ str r2, [r1]\n"
        ".inst 0xe1a00822 @ lsr r0, r2, #0x10\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00473548 @ tail data\n"
        ".word 0x0019660d @ tail data\n"
        ".word 0x3c6ef35f @ tail data\n"
    );
}

// DECOMP_FUNC(0x00156c88, 44)
extern "C" __attribute__((naked)) void func_00156c88() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4008 @ push {r3, lr}\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe5b010c4 @ ldr r1, [r0, #0xc4]!\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x10800001 @ addne r0, r0, r1\n"
        ".inst 0x03a00000 @ moveq r0, #0\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0xe58d0000 @ str r0, [sp]\n"
        ".inst 0x11a0000d @ movne r0, sp\n"
        ".inst 0x1b052d91 @ blne #0x2a22f8\n"
        ".inst 0xe8bd8008 @ pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x0015d85c, 44)
extern "C" __attribute__((naked)) void func_0015d85c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4008 @ push {r3, lr}\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe5b01028 @ ldr r1, [r0, #0x28]!\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x10800001 @ addne r0, r0, r1\n"
        ".inst 0x03a00000 @ moveq r0, #0\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0xe58d0000 @ str r0, [sp]\n"
        ".inst 0x11a0000d @ movne r0, sp\n"
        ".inst 0x1b000297 @ blne #0x15e2e4\n"
        ".inst 0xe8bd8008 @ pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x0015e010, 44)
extern "C" __attribute__((naked)) void func_0015e010() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xeb0001f9 @ bl #0x15e808\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0xba000002 @ blt #0x15e034\n"
        ".inst 0xe5941030 @ ldr r1, [r4, #0x30]\n"
        ".inst 0xe0800001 @ add r0, r0, r1\n"
        ".inst 0xe5840030 @ str r0, [r4, #0x30]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004e6f64 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0018ab7c, 44)
extern "C" __attribute__((naked)) void engine_func_0018ab7c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0020 @ ldr r0, [pc, #0x20]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe5801000 @ str r1, [r0]\n"
        ".inst 0xe1c010b4 @ strh r1, [r0, #4]\n"
        ".inst 0xe1c010b6 @ strh r1, [r0, #6]\n"
        ".inst 0xe1c010b8 @ strh r1, [r0, #8]\n"
        ".inst 0xe580100c @ str r1, [r0, #0xc]\n"
        ".inst 0xe5801010 @ str r1, [r0, #0x10]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x004474d8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001a839c, 44)
extern "C" __attribute__((naked)) void func_001a839c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1d010b4 @ ldrh r1, [r0, #4]\n"
        ".inst 0xe59f201c @ ldr r2, [pc, #0x1c]\n"
        ".inst 0xe0811201 @ add r1, r1, r1, lsl #4\n"
        ".inst 0xe0821101 @ add r1, r2, r1, lsl #2\n"
        ".inst 0xe591101c @ ldr r1, [r1, #0x1c]\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x0a000001 @ beq #0x1a83c0\n"
        ".inst 0xe5900008 @ ldr r0, [r0, #8]\n"
        ".inst 0xe12fff11 @ bx r1\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00464110 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001e1900, 44)
extern "C" __attribute__((naked)) void engine_func_001e1900() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1d020b4 @ ldrh r2, [r0, #4]\n"
        ".inst 0xe59f301c @ ldr r3, [pc, #0x1c]\n"
        ".inst 0xe0822202 @ add r2, r2, r2, lsl #4\n"
        ".inst 0xe0832102 @ add r2, r3, r2, lsl #2\n"
        ".inst 0xe5922030 @ ldr r2, [r2, #0x30]\n"
        ".inst 0xe3520000 @ cmp r2, #0\n"
        ".inst 0x0a000001 @ beq #0x1e1924\n"
        ".inst 0xe5900008 @ ldr r0, [r0, #8]\n"
        ".inst 0xe12fff12 @ bx r2\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00464110 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001e3874, 44)
extern "C" __attribute__((naked)) void script_vm_func_001e3874() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f2020 @ ldr r2, [pc, #0x20]\n"
        ".inst 0xe3a0c00a @ mov ip, #0xa\n"
        ".inst 0xe3a03000 @ mov r3, #0\n"
        ".inst 0xe5922000 @ ldr r2, [r2]\n"
        ".inst 0xe1c2c0b8 @ strh ip, [r2, #8]\n"
        ".inst 0xe1c230ba @ strh r3, [r2, #0xa]\n"
        ".inst 0xe1c200b4 @ strh r0, [r2, #4]\n"
        ".inst 0xe1c210b6 @ strh r1, [r2, #6]\n"
        ".inst 0xe5823010 @ str r3, [r2, #0x10]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00447e70 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001f71dc, 44)
extern "C" __attribute__((naked)) void engine_func_001f71dc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1d020b4 @ ldrh r2, [r0, #4]\n"
        ".inst 0xe59f301c @ ldr r3, [pc, #0x1c]\n"
        ".inst 0xe0822202 @ add r2, r2, r2, lsl #4\n"
        ".inst 0xe0832102 @ add r2, r3, r2, lsl #2\n"
        ".inst 0xe5922024 @ ldr r2, [r2, #0x24]\n"
        ".inst 0xe3520000 @ cmp r2, #0\n"
        ".inst 0x0a000001 @ beq #0x1f7200\n"
        ".inst 0xe5900008 @ ldr r0, [r0, #8]\n"
        ".inst 0xe12fff12 @ bx r2\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00464110 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001f8cd8, 44)
extern "C" __attribute__((naked)) void engine_func_001f8cd8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb03278e @ bl #0x2c2b1c\n"
        ".inst 0xe3a01001 @ mov r1, #1\n"
        ".inst 0xe2803b03 @ add r3, r0, #0xc00\n"
        ".inst 0xed9f0a04 @ vldr s0, [pc, #0x10]\n"
        ".inst 0xe5801dc0 @ str r1, [r0, #0xdc0]\n"
        ".inst 0xe3a02000 @ mov r2, #0\n"
        ".inst 0xed830a71 @ vstr s0, [r3, #0x1c4]\n"
        ".inst 0xe5c02dc8 @ strb r2, [r0, #0xdc8]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00000000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0010fb6c, 48)
extern "C" __attribute__((naked)) void func_0010fb6c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe59f4020 @ ldr r4, [pc, #0x20]\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe5d41001 @ ldrb r1, [r4, #1]\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0x0a000003 @ beq #0x10fb94\n"
        ".inst 0xe5940008 @ ldr r0, [r4, #8]\n"
        ".inst 0xeb00a843 @ bl #0x139c9c\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe5c41001 @ strb r1, [r4, #1]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0044e458 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0010fe28, 48)
extern "C" __attribute__((naked)) void func_0010fe28() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe3a00821 @ mov r0, #0x210000\n"
        ".inst 0xe5a40080 @ str r0, [r4, #0x80]!\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004719e8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011b388, 48)
extern "C" __attribute__((naked)) void engine_func_0011b388() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a02000 @ mov r2, #0\n"
        ".inst 0xe5c01004 @ strb r1, [r0, #4]\n"
        ".inst 0xe5802000 @ str r2, [r0]\n"
        ".inst 0xe5802008 @ str r2, [r0, #8]\n"
        ".inst 0xe580200c @ str r2, [r0, #0xc]\n"
        ".inst 0xe5802010 @ str r2, [r0, #0x10]\n"
        ".inst 0xe5802014 @ str r2, [r0, #0x14]\n"
        ".inst 0xe59f2008 @ ldr r2, [pc, #8]\n"
        ".inst 0xe7921101 @ ldr r1, [r2, r1, lsl #2]\n"
        ".inst 0xe580101c @ str r1, [r0, #0x1c]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00464cb8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011ba80, 48)
extern "C" __attribute__((naked)) void nn_sdk_func_0011ba80() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe59f201c @ ldr r2, [pc, #0x1c]\n"
        ".inst 0xe5a42080 @ str r2, [r4, #0x80]!\n"
        ".inst 0xe5841004 @ str r1, [r4, #4]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x08620040 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d778, 48)
extern "C" __attribute__((naked)) void func_0011d778() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe3a0082b @ mov r0, #0x2b0000\n"
        ".inst 0xe5a40080 @ str r0, [r4, #0x80]!\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004656b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001244b8, 48)
extern "C" __attribute__((naked)) void func_001244b8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1024 @ ldr r1, [pc, #0x24]\n"
        ".inst 0xe591200c @ ldr r2, [r1, #0xc]\n"
        ".inst 0xe1d210b0 @ ldrh r1, [r2]\n"
        ".inst 0xe1510000 @ cmp r1, r0\n"
        ".inst 0x3a000004 @ blo #0x1244e0\n"
        ".inst 0xe0411000 @ sub r1, r1, r0\n"
        ".inst 0xe1c210b0 @ strh r1, [r2]\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe1a00002 @ mov r0, r2\n"
        ".inst 0xea005312 @ b #0x13912c\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0043e2a8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00128bcc, 48)
extern "C" __attribute__((naked)) void func_00128bcc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe3a00811 @ mov r0, #0x110000\n"
        ".inst 0xe5a40080 @ str r0, [r4, #0x80]!\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00472ab0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00128bfc, 48)
extern "C" __attribute__((naked)) void func_00128bfc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xee1d4f70 @ mrc p15, #0, r4, c13, c0, #3\n"
        ".inst 0xe3a00812 @ mov r0, #0x120000\n"
        ".inst 0xe5a40080 @ str r0, [r4, #0x80]!\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xef000032 @ svc #0x32\n"
        ".inst 0xe2001102 @ and r1, r0, #0x80000000\n"
        ".inst 0xe3510000 @ cmp r1, #0\n"
        ".inst 0xa5940004 @ ldrge r0, [r4, #4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00472ab0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013bff4, 48)
extern "C" __attribute__((naked)) void func_0013bff4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0020 @ ldr r0, [pc, #0x20]\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb05b063 @ bl #0x2a8190\n"
        ".inst 0xe1b01fa0 @ lsrs r1, r0, #0x1f\n"
        ".inst 0x159f1014 @ ldrne r1, [pc, #0x14]\n"
        ".inst 0x11500001 @ cmpne r0, r1\n"
        ".inst 0x0a000001 @ beq #0x13c018\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xea06038b @ b #0x2bce48\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00000406 @ tail data\n"
        ".word 0xc8a0cffc @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014bfdc, 48)
extern "C" __attribute__((naked)) void func_0014bfdc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f2024 @ ldr r2, [pc, #0x24]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe5801004 @ str r1, [r0, #4]\n"
        ".inst 0xe5802000 @ str r2, [r0]\n"
        ".inst 0xe5801008 @ str r1, [r0, #8]\n"
        ".inst 0xe580100c @ str r1, [r0, #0xc]\n"
        ".inst 0xe5801010 @ str r1, [r0, #0x10]\n"
        ".inst 0xe5801014 @ str r1, [r0, #0x14]\n"
        ".inst 0xe5801018 @ str r1, [r0, #0x18]\n"
        ".inst 0xe580101c @ str r1, [r0, #0x1c]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00421724 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014e604, 48)
extern "C" __attribute__((naked)) void ui_func_0014e604() {
    asm volatile(
        ".arm\n"
        ".inst 0xea000fb8 @ b #0x1524ec\n"
        ".inst 0xe240100a @ sub r1, r0, #0xa\n"
        ".inst 0xe0400120 @ sub r0, r0, r0, lsr #2\n"
        ".inst 0xe0800220 @ add r0, r0, r0, lsr #4\n"
        ".inst 0xe0800420 @ add r0, r0, r0, lsr #8\n"
        ".inst 0xe0800820 @ add r0, r0, r0, lsr #16\n"
        ".inst 0xe1a001a0 @ lsr r0, r0, #3\n"
        ".inst 0xe0802100 @ add r2, r0, r0, lsl #2\n"
        ".inst 0xe0511082 @ subs r1, r1, r2, lsl #1\n"
        ".inst 0x52800001 @ addpl r0, r0, #1\n"
        ".inst 0x4281100a @ addmi r1, r1, #0xa\n"
        ".inst 0xe12fff1e @ bx lr\n"
    );
}

// DECOMP_FUNC(0x00152d7c, 48)
extern "C" __attribute__((naked)) void engine_func_00152d7c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1024 @ ldr r1, [pc, #0x24]\n"
        ".inst 0xe2812000 @ add r2, r1, #0\n"
        ".inst 0xe1d130b2 @ ldrh r3, [r1, #2]\n"
        ".inst 0xe5922008 @ ldr r2, [r2, #8]\n"
        ".inst 0xe3530000 @ cmp r3, #0\n"
        ".inst 0xe2833001 @ add r3, r3, #1\n"
        ".inst 0x01d2c3b8 @ ldrheq ip, [r2, #0x38]\n"
        ".inst 0x01c1c0b0 @ strheq ip, [r1]\n"
        ".inst 0xe1c130b2 @ strh r3, [r1, #2]\n"
        ".inst 0xe1c203b8 @ strh r0, [r2, #0x38]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00465120 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0015459c, 48)
extern "C" __attribute__((naked)) void ui_func_0015459c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe59f4020 @ ldr r4, [pc, #0x20]\n"
        ".inst 0xe59f1018 @ ldr r1, [pc, #0x18]\n"
        ".inst 0xe3a02e17 @ mov r2, #0x170\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xeb0561e0 @ bl #0x2acd38\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe2800e17 @ add r0, r0, #0x170\n"
        ".inst 0xe5840000 @ str r0, [r4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00471c58 @ tail data\n"
        ".word 0x004652a0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00155a08, 48)
extern "C" __attribute__((naked)) void func_00155a08() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d48c0 @ push {r6, r7, fp, lr}\n"
        ".inst 0xe1a0b002 @ mov fp, r2\n"
        ".inst 0xe92d0030 @ push {r4, r5}\n"
        ".inst 0xe8910038 @ ldm r1, {r3, r4, r5}\n"
        ".inst 0xe8900007 @ ldm r0, {r0, r1, r2}\n"
        ".inst 0xe1d1c080 @ bics ip, r1, r0, lsl #1\n"
        ".inst 0x41d4c083 @ bicsmi ip, r4, r3, lsl #1\n"
        ".inst 0x5a000001 @ bpl #0x155a30\n"
        ".inst 0xeb000d7e @ bl #0x159028\n"
        ".inst 0xeb000e4f @ bl #0x159370\n"
        ".inst 0xe8bd00f0 @ pop {r4, r5, r6, r7}\n"
        ".inst 0xe8bd8800 @ pop {fp, pc}\n"
    );
}

// DECOMP_FUNC(0x001634cc, 48)
extern "C" __attribute__((naked)) void func_001634cc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4ff0 @ push {r4, r5, r6, r7, r8, sb, sl, fp, lr}\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe5902004 @ ldr r2, [r0, #4]\n"
        ".inst 0xe24f3a03 @ sub r3, pc, #0x3000\n"
        ".inst 0xe2433f81 @ sub r3, r3, #0x204\n"
        ".inst 0xe24f4b05 @ sub r4, pc, #0x1400\n"
        ".inst 0xe2444fe6 @ sub r4, r4, #0x398\n"
        ".inst 0xe1510002 @ cmp r1, r2\n"
        ".inst 0x11a03004 @ movne r3, r4\n"
        ".inst 0xe12fff33 @ blx r3\n"
        ".inst 0xebfff665 @ bl #0x160e90\n"
        ".inst 0xe8bd8ff0 @ pop {r4, r5, r6, r7, r8, sb, sl, fp, pc}\n"
    );
}

// DECOMP_FUNC(0x00167244, 48)
extern "C" __attribute__((naked)) void func_00167244() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4ff0 @ push {r4, r5, r6, r7, r8, sb, sl, fp, lr}\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe5902004 @ ldr r2, [r0, #4]\n"
        ".inst 0xe24f3a03 @ sub r3, pc, #0x3000\n"
        ".inst 0xe2433f81 @ sub r3, r3, #0x204\n"
        ".inst 0xe24f4b05 @ sub r4, pc, #0x1400\n"
        ".inst 0xe2444fe6 @ sub r4, r4, #0x398\n"
        ".inst 0xe1510002 @ cmp r1, r2\n"
        ".inst 0x11a03004 @ movne r3, r4\n"
        ".inst 0xe12fff33 @ blx r3\n"
        ".inst 0xebfff665 @ bl #0x164c08\n"
        ".inst 0xe8bd8ff0 @ pop {r4, r5, r6, r7, r8, sb, sl, fp, pc}\n"
    );
}

// DECOMP_FUNC(0x0016afbc, 48)
extern "C" __attribute__((naked)) void func_0016afbc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4ff0 @ push {r4, r5, r6, r7, r8, sb, sl, fp, lr}\n"
        ".inst 0xe5901000 @ ldr r1, [r0]\n"
        ".inst 0xe5902004 @ ldr r2, [r0, #4]\n"
        ".inst 0xe24f3a03 @ sub r3, pc, #0x3000\n"
        ".inst 0xe2433f81 @ sub r3, r3, #0x204\n"
        ".inst 0xe24f4b05 @ sub r4, pc, #0x1400\n"
        ".inst 0xe2444fe6 @ sub r4, r4, #0x398\n"
        ".inst 0xe1510002 @ cmp r1, r2\n"
        ".inst 0x11a03004 @ movne r3, r4\n"
        ".inst 0xe12fff33 @ blx r3\n"
        ".inst 0xebfff665 @ bl #0x168980\n"
        ".inst 0xe8bd8ff0 @ pop {r4, r5, r6, r7, r8, sb, sl, fp, pc}\n"
    );
}

// DECOMP_FUNC(0x001ab830, 48)
extern "C" __attribute__((naked)) void engine_func_001ab830() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb03adc8 @ bl #0x296f60\n"
        ".inst 0xeb0454a1 @ bl #0x2c0ac8\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000002 @ beq #0x1ab854\n"
        ".inst 0xed9f0a03 @ vldr s0, [pc, #0xc]\n"
        ".inst 0xed800a03 @ vstr s0, [r0, #0xc]\n"
        ".inst 0xed800a04 @ vstr s0, [r0, #0x10]\n"
        ".inst 0xe3a00001 @ mov r0, #1\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00000000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001d2320, 48)
extern "C" __attribute__((naked)) void func_001d2320() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe590004c @ ldr r0, [r0, #0x4c]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000004 @ beq #0x1d2348\n"
        ".inst 0xeb025c98 @ bl #0x26959c\n"
        ".inst 0xe1a00004 @ mov r0, r4\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xed9f0a01 @ vldr s0, [pc, #4]\n"
        ".inst 0xea03d435 @ b #0x2c7420\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x3f800000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001d371c, 48)
extern "C" __attribute__((naked)) void script_vm_func_001d371c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0024 @ ldr r0, [pc, #0x24]\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe2804010 @ add r4, r0, #0x10\n"
        ".inst 0xe590002c @ ldr r0, [r0, #0x2c]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000002 @ beq #0x1d3744\n"
        ".inst 0xeb0350d8 @ bl #0x2a7aa0\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe584001c @ str r0, [r4, #0x1c]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x0044cda0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001fa68c, 48)
extern "C" __attribute__((naked)) void script_vm_func_001fa68c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0024 @ ldr r0, [pc, #0x24]\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe2804903 @ add r4, r0, #0xc000\n"
        ".inst 0xe2844ebd @ add r4, r4, #0xbd0\n"
        ".inst 0xe594001c @ ldr r0, [r4, #0x1c]\n"
        ".inst 0xeb02b4fd @ bl #0x2a7aa0\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe584001c @ str r0, [r4, #0x1c]\n"
        ".inst 0xe5c40000 @ strb r0, [r4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00447a78 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0010f9bc, 52)
extern "C" __attribute__((naked)) void func_0010f9bc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a02001 @ mov r2, r1\n"
        ".inst 0xe59f1020 @ ldr r1, [pc, #0x20]\n"
        ".inst 0xe5d13000 @ ldrb r3, [r1]\n"
        ".inst 0xe3530000 @ cmp r3, #0\n"
        ".inst 0x1a000004 @ bne #0x10f9e4\n"
        ".inst 0xe3a03001 @ mov r3, #1\n"
        ".inst 0xe5c13000 @ strb r3, [r1]\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe59f0008 @ ldr r0, [pc, #8]\n"
        ".inst 0xea004fc4 @ b #0x1238f8\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00471b54 @ tail data\n"
        ".word 0x004e6ef0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011311c, 52)
extern "C" __attribute__((naked)) void battle_func_0011311c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f2028 @ ldr r2, [pc, #0x28]\n"
        ".inst 0xe3500b01 @ cmp r0, #0x400\n"
        ".inst 0x0582115c @ streq r1, [r2, #0x15c]\n"
        ".inst 0x0a000006 @ beq #0x113148\n"
        ".inst 0xe2400b01 @ sub r0, r0, #0x400\n"
        ".inst 0xe2500001 @ subs r0, r0, #1\n"
        ".inst 0x05821160 @ streq r1, [r2, #0x160]\n"
        ".inst 0x0a000002 @ beq #0x113148\n"
        ".inst 0xe3500001 @ cmp r0, #1\n"
        ".inst 0x0582115c @ streq r1, [r2, #0x15c]\n"
        ".inst 0x05821160 @ streq r1, [r2, #0x160]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x004c6290 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011cc00, 52)
extern "C" __attribute__((naked)) void func_0011cc00() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe1a04000 @ mov r4, r0\n"
        ".inst 0xe5d00000 @ ldrb r0, [r0]\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000005 @ beq #0x11cc2c\n"
        ".inst 0xe59f0014 @ ldr r0, [pc, #0x14]\n"
        ".inst 0xeb003091 @ bl #0x128e64\n"
        ".inst 0xe3e01000 @ mvn r1, #0\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe584104c @ str r1, [r4, #0x4c]\n"
        ".inst 0xe5c40000 @ strb r0, [r4]\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004ead10 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00131420, 52)
extern "C" __attribute__((naked)) void ui_func_00131420() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f3028 @ ldr r3, [pc, #0x28]\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xe5801004 @ str r1, [r0, #4]\n"
        ".inst 0xe5803000 @ str r3, [r0]\n"
        ".inst 0xe5801008 @ str r1, [r0, #8]\n"
        ".inst 0xe580100c @ str r1, [r0, #0xc]\n"
        ".inst 0xe1c011b4 @ strh r1, [r0, #0x14]\n"
        ".inst 0xe3e02000 @ mvn r2, #0\n"
        ".inst 0xe3a01006 @ mov r1, #6\n"
        ".inst 0xe1c021b6 @ strh r2, [r0, #0x16]\n"
        ".inst 0xe5801010 @ str r1, [r0, #0x10]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00421ce4 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00139b30, 52)
extern "C" __attribute__((naked)) void func_00139b30() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a02001 @ mov r2, r1\n"
        ".inst 0xe59f1024 @ ldr r1, [pc, #0x24]\n"
        ".inst 0xe1a0c000 @ mov ip, r0\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5913008 @ ldr r3, [r1, #8]\n"
        ".inst 0xe3530000 @ cmp r3, #0\n"
        ".inst 0x0a000002 @ beq #0x139b58\n"
        ".inst 0xe1a0100c @ mov r1, ip\n"
        ".inst 0xe1a00003 @ mov r0, r3\n"
        ".inst 0xea003324 @ b #0x1467ec\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0xc8a0a7f8 @ tail data\n"
        ".word 0x0044e458 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00139e30, 52)
extern "C" __attribute__((naked)) void func_00139e30() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a02001 @ mov r2, r1\n"
        ".inst 0xe59f1024 @ ldr r1, [pc, #0x24]\n"
        ".inst 0xe1a0c000 @ mov ip, r0\n"
        ".inst 0xe59f0018 @ ldr r0, [pc, #0x18]\n"
        ".inst 0xe5913008 @ ldr r3, [r1, #8]\n"
        ".inst 0xe3530000 @ cmp r3, #0\n"
        ".inst 0x0a000002 @ beq #0x139e58\n"
        ".inst 0xe1a0100c @ mov r1, ip\n"
        ".inst 0xe1a00003 @ mov r0, r3\n"
        ".inst 0xea0032b1 @ b #0x146920\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0xc8a0a7f8 @ tail data\n"
        ".word 0x0044e458 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014c988, 52)
extern "C" __attribute__((naked)) void func_0014c988() {
    asm volatile(
        ".arm\n"
        ".inst 0xe52de004 @ str lr, [sp, #-4]!\n"
        ".inst 0xe24dd074 @ sub sp, sp, #0x74\n"
        ".inst 0xe59f2020 @ ldr r2, [pc, #0x20]\n"
        ".inst 0xe1cd12b8 @ strh r1, [sp, #0x28]\n"
        ".inst 0xe3a03068 @ mov r3, #0x68\n"
        ".inst 0xe58d2000 @ str r2, [sp]\n"
        ".inst 0xe5b02434 @ ldr r2, [r0, #0x434]!\n"
        ".inst 0xe5901004 @ ldr r1, [r0, #4]\n"
        ".inst 0xe28d0008 @ add r0, sp, #8\n"
        ".inst 0xfa059fca @ blx #0x2b48dc\n"
        ".inst 0xe28dd074 @ add sp, sp, #0x74\n"
        ".inst 0xe49df004 @ pop {pc}\n"
        ".word 0x00151a8c @ tail data\n"
    );
}

// DECOMP_FUNC(0x00151d60, 52)
extern "C" __attribute__((naked)) void engine_func_00151d60() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1028 @ ldr r1, [pc, #0x28]\n"
        ".inst 0xe1d021b4 @ ldrh r2, [r0, #0x14]\n"
        ".inst 0xe1520001 @ cmp r2, r1\n"
        ".inst 0x02801014 @ addeq r1, r0, #0x14\n"
        ".inst 0x0a000003 @ beq #0x151d84\n"
        ".inst 0xe1d022b0 @ ldrh r2, [r0, #0x20]\n"
        ".inst 0xe1520001 @ cmp r2, r1\n"
        ".inst 0x02801020 @ addeq r1, r0, #0x20\n"
        ".inst 0x13a01000 @ movne r1, #0\n"
        ".inst 0xe5911004 @ ldr r1, [r1, #4]\n"
        ".inst 0xe0800001 @ add r0, r0, r1\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00006801 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0015d828, 52)
extern "C" __attribute__((naked)) void func_0015d828() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5900000 @ ldr r0, [r0]\n"
        ".inst 0xe59f1024 @ ldr r1, [pc, #0x24]\n"
        ".inst 0xe5902000 @ ldr r2, [r0]\n"
        ".inst 0xe3520102 @ cmp r2, #0x80000000\n"
        ".inst 0x0a000003 @ beq #0x15d84c\n"
        ".inst 0xe3520101 @ cmp r2, #0x40000000\n"
        ".inst 0x1a000003 @ bne #0x15d854\n"
        ".inst 0xe5911004 @ ldr r1, [r1, #4]\n"
        ".inst 0xe12fff11 @ bx r1\n"
        ".inst 0xe5911000 @ ldr r1, [r1]\n"
        ".inst 0xe12fff11 @ bx r1\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x0044e8e0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001a0e70, 52)
extern "C" __attribute__((naked)) void engine_func_001a0e70() {
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
        ".inst 0xeb048aea @ bl #0x2c3a44\n"
        ".inst 0xe28dd008 @ add sp, sp, #8\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004c38d8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001b41ac, 52)
extern "C" __attribute__((naked)) void script_vm_func_001b41ac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1028 @ ldr r1, [pc, #0x28]\n"
        ".inst 0xe5911000 @ ldr r1, [r1]\n"
        ".inst 0xe5912004 @ ldr r2, [r1, #4]\n"
        ".inst 0xe3520000 @ cmp r2, #0\n"
        ".inst 0x0a000005 @ beq #0x1b41d8\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x03a00007 @ moveq r0, #7\n"
        ".inst 0x13a00008 @ movne r0, #8\n"
        ".inst 0xe5810004 @ str r0, [r1, #4]\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe5810008 @ str r0, [r1, #8]\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x00447600 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001c2a14, 52)
extern "C" __attribute__((naked)) void engine_func_001c2a14() {
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
        ".inst 0xeb040401 @ bl #0x2c3a44\n"
        ".inst 0xe28dd008 @ add sp, sp, #8\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004c3880 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001d3ca4, 52)
extern "C" __attribute__((naked)) void ui_func_001d3ca4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb03b386 @ bl #0x2c0ac8\n"
        ".inst 0xe59f2020 @ ldr r2, [pc, #0x20]\n"
        ".inst 0xe5922008 @ ldr r2, [r2, #8]\n"
        ".inst 0xe3520000 @ cmp r2, #0\n"
        ".inst 0x03a00000 @ moveq r0, #0\n"
        ".inst 0x0a000003 @ beq #0x1d3cd0\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xe1a00002 @ mov r0, r2\n"
        ".inst 0xea07ca90 @ b #0x3c6714\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00434388 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001d3cd8, 52)
extern "C" __attribute__((naked)) void ui_func_001d3cd8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb03b379 @ bl #0x2c0ac8\n"
        ".inst 0xe59f2020 @ ldr r2, [pc, #0x20]\n"
        ".inst 0xe5922000 @ ldr r2, [r2]\n"
        ".inst 0xe3520000 @ cmp r2, #0\n"
        ".inst 0x03a00000 @ moveq r0, #0\n"
        ".inst 0x0a000003 @ beq #0x1d3d04\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xe1a00002 @ mov r0, r2\n"
        ".inst 0xea07cf63 @ b #0x3c7a94\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00435d48 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001d3d0c, 52)
extern "C" __attribute__((naked)) void ui_func_001d3d0c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xeb03b36c @ bl #0x2c0ac8\n"
        ".inst 0xe59f2020 @ ldr r2, [pc, #0x20]\n"
        ".inst 0xe5922004 @ ldr r2, [r2, #4]\n"
        ".inst 0xe3520000 @ cmp r2, #0\n"
        ".inst 0x03a00000 @ moveq r0, #0\n"
        ".inst 0x0a000003 @ beq #0x1d3d38\n"
        ".inst 0xe1a01000 @ mov r1, r0\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xe1a00002 @ mov r0, r2\n"
        ".inst 0xea07d1ad @ b #0x3c83f0\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x004398d0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001db258, 52)
extern "C" __attribute__((naked)) void battle_func_001db258() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0028 @ ldr r0, [pc, #0x28]\n"
        ".inst 0xe92d4010 @ push {r4, lr}\n"
        ".inst 0xe5904000 @ ldr r4, [r0]\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xeb03906b @ bl #0x2bf41c\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0x0a000003 @ beq #0x1db284\n"
        ".inst 0xe5940000 @ ldr r0, [r4]\n"
        ".inst 0xe8bd4010 @ pop {r4, lr}\n"
        ".inst 0xe3a01000 @ mov r1, #0\n"
        ".inst 0xea03a4cc @ b #0x2c45b8\n"
        ".inst 0xe8bd8010 @ pop {r4, pc}\n"
        ".word 0x00432ce0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001db4b0, 52)
extern "C" __attribute__((naked)) void func_001db4b0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000 @ cmp r0, #0\n"
        ".inst 0xba000007 @ blt #0x1db4d8\n"
        ".inst 0xe59f2020 @ ldr r2, [pc, #0x20]\n"
        ".inst 0xe0811101 @ add r1, r1, r1, lsl #2\n"
        ".inst 0xe0821101 @ add r1, r2, r1, lsl #2\n"
        ".inst 0xe1d120f0 @ ldrsh r2, [r1]\n"
        ".inst 0xe1500002 @ cmp r0, r2\n"
        ".inst 0xb0810100 @ addlt r0, r1, r0, lsl #2\n"
        ".inst 0xb5900004 @ ldrlt r0, [r0, #4]\n"
        ".inst 0xba000000 @ blt #0x1db4dc\n"
        ".inst 0xe3a00000 @ mov r0, #0\n"
        ".inst 0xe12fff1e @ bx lr\n"
        ".word 0x004daca0 @ tail data\n"
    );
}
