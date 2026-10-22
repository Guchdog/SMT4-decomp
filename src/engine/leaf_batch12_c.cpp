#include "types.h"

// DECOMP_FUNC(0x0023ec0c, 48)
extern "C" __attribute__((naked)) void func_0023ec0c() {
    asm volatile(
        "cmp r0, #0\n"
        "beq .L_func_0023ec0c_0023ec38\n"
        "ldrsh r2, [r0, #0xe]\n"
        "cmp r1, r2\n"
        "movgt r1, r2\n"
        "bgt .L_func_0023ec0c_0023ec2c\n"
        "cmp r1, #1\n"
        "movlt r1, #1\n"
        ".L_func_0023ec0c_0023ec2c:\n"
        "sxth r1, r1\n"
        "strh r1, [r0, #0x2a]\n"
        "mov r0, r1\n"
        ".L_func_0023ec0c_0023ec38:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00245198, 48)
extern "C" __attribute__((naked)) void func_00245198() {
    asm volatile(
        "add r0, r0, r1, lsl #2\n"
        "add r0, r0, #0x4800\n"
        "add r0, r0, #0x224\n"
        "ldr r0, [r0]\n"
        "cmp r0, #4\n"
        "cmpne r0, #5\n"
        "beq .L_func_00245198_002451c0\n"
        "cmp r0, #6\n"
        "movne r0, #1\n"
        "bne .L_func_00245198_002451c4\n"
        ".L_func_00245198_002451c0:\n"
        "mov r0, #0\n"
        ".L_func_00245198_002451c4:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002453e4, 48)
extern "C" __attribute__((naked)) void func_002453e4() {
    asm volatile(
        "add r0, r0, r1, lsl #2\n"
        "add r0, r0, #0x4800\n"
        "add r0, r0, #0x224\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "cmpne r0, #1\n"
        "beq .L_func_002453e4_0024540c\n"
        "cmp r0, #2\n"
        "movne r0, #1\n"
        "bne .L_func_002453e4_00245410\n"
        ".L_func_002453e4_0024540c:\n"
        "mov r0, #0\n"
        ".L_func_002453e4_00245410:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0027e628, 48)
extern "C" __attribute__((naked)) void script_vm_func_0027e628() {
    asm volatile(
        "ldr r1, [r0]\n"
        "cmp r1, #0\n"
        "beq .L_script_vm_func_0027e628_0027e648\n"
        "cmp r1, #0xa\n"
        "bne .L_script_vm_func_0027e628_0027e650\n"
        "ldr r0, [r0, #0x28]\n"
        "cmp r0, #1\n"
        "bge .L_script_vm_func_0027e628_0027e650\n"
        ".L_script_vm_func_0027e628_0027e648:\n"
        "mov r0, #0\n"
        "bx lr\n"
        ".L_script_vm_func_0027e628_0027e650:\n"
        "mov r0, #1\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002a6d28, 48)
extern "C" __attribute__((naked)) void func_002a6d28() {
    asm volatile(
        "ldrh r0, [r0, #0xc]\n"
        "sub r0, r0, #0x2200\n"
        "subs r0, r0, #1\n"
        "moveq r0, #2\n"
        "beq .L_func_002a6d28_002a6d54\n"
        "cmp r0, #1\n"
        "moveq r0, #3\n"
        "beq .L_func_002a6d28_002a6d54\n"
        "cmp r0, #2\n"
        "movne r0, #0\n"
        "moveq r0, #1\n"
        ".L_func_002a6d28_002a6d54:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x002a7f94, 48)
extern "C" __attribute__((naked)) void func_002a7f94() {
    asm volatile(
        "ldr r0, [r0]\n"
        "ldr r1, [r0]\n"
        "cmp r1, #0x80000000\n"
        "beq .L_func_002a7f94_002a7fc0\n"
        "cmp r1, #0x40000000\n"
        "bne .L_func_002a7f94_002a7fbc\n"
        "ldr r1, [r0, #0xc]!\n"
        "cmp r1, #0\n"
        "addne r0, r0, r1\n"
        "bne .L_func_002a7f94_002a7fc0\n"
        ".L_func_002a7f94_002a7fbc:\n"
        "mov r0, #0\n"
        ".L_func_002a7f94_002a7fc0:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00345164, 48)
extern "C" __attribute__((naked)) void func_00345164() {
    asm volatile(
        "mov r2, r0\n"
        "mov r0, #0\n"
        "ldr r2, [r2, #8]\n"
        "cmp r2, #0\n"
        "beq .L_func_00345164_00345190\n"
        ".L_func_00345164_00345178:\n"
        "ldrsb r3, [r2, #4]\n"
        "ldr r2, [r2, #0xc]\n"
        "cmp r3, r1\n"
        "addeq r0, r0, #1\n"
        "cmp r2, #0\n"
        "bne .L_func_00345164_00345178\n"
        ".L_func_00345164_00345190:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003b0358, 48)
extern "C" __attribute__((naked)) void func_003b0358() {
    asm volatile(
        "cmp r2, #0\n"
        "beq .L_func_003b0358_003b0380\n"
        "ldrb r3, [r1], #1\n"
        "subs r2, r2, #1\n"
        "str r3, [r0, #0x14]\n"
        "beq .L_func_003b0358_003b0380\n"
        "ldrb r1, [r1]\n"
        "str r1, [r0, #0x18]\n"
        "mov r0, #2\n"
        "bx lr\n"
        ".L_func_003b0358_003b0380:\n"
        "mvn r0, #0\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003bcbb0, 48)
extern "C" __attribute__((naked)) void func_003bcbb0() {
    asm volatile(
        "cmp r0, #0\n"
        "beq .L_func_003bcbb0_003bcbdc\n"
        "ldrsh r2, [r0, #0x10]\n"
        "cmp r1, r2\n"
        "movgt r1, r2\n"
        "bgt .L_func_003bcbb0_003bcbd0\n"
        "cmp r1, #1\n"
        "movlt r1, #1\n"
        ".L_func_003bcbb0_003bcbd0:\n"
        "sxth r1, r1\n"
        "strh r1, [r0, #0x2c]\n"
        "mov r0, r1\n"
        ".L_func_003bcbb0_003bcbdc:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003c2f7c, 48)
extern "C" __attribute__((naked)) void shop_func_003c2f7c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "add r0, r0, #0x10\n"
        "ldrsb r0, [r0, #0x61]\n"
        "cmp r0, #0\n"
        "bne .L_shop_func_003c2f7c_003c2fa4\n"
        "add r0, r4, #0x10\n"
        "ldrsb r0, [r0, #0x60]\n"
        "cmp r0, #0\n"
        "beq .L_shop_func_003c2f7c_003c2fa8\n"
        ".L_shop_func_003c2f7c_003c2fa4:\n"
        "mov r0, #1\n"
        ".L_shop_func_003c2f7c_003c2fa8:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003e873c, 48)
extern "C" __attribute__((naked)) void func_003e873c() {
    asm volatile(
        "add r0, r0, #8\n"
        "mov r0, r0\n"
        "mov r1, r0\n"
        "mov r0, #0\n"
        "ldr r1, [r1]\n"
        "cmp r1, #0\n"
        "beq .L_func_003e873c_003e8768\n"
        ".L_func_003e873c_003e8758:\n"
        "ldr r1, [r1]\n"
        "add r0, r0, #1\n"
        "cmp r1, #0\n"
        "bne .L_func_003e873c_003e8758\n"
        ".L_func_003e873c_003e8768:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00125d54, 52)
extern "C" __attribute__((naked)) void func_00125d54() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "ldrbne r0, [r0, #0x67c]\n"
        "cmpne r0, #0\n"
        "movne r0, #1\n"
        "beq .L_func_00125d54_00125d70\n"
        ".L_func_00125d54_00125d70:\n"
        "bx lr\n"
        ".word 0x0043dcb0\n"
        "ldrh r0, [r0, #0x20]\n"
        "ldrh r1, [r1, #0x20]\n"
        "sub r0, r0, r1\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0014c3ac, 52)
extern "C" __attribute__((naked)) void engine_func_0014c3ac() {
    asm volatile(
        "ldrb r3, [r0, #0xc]\n"
        "cmp r3, #0\n"
        "ldrne r3, [r0, #8]\n"
        "cmpne r3, #0\n"
        "beq .L_engine_func_0014c3ac_0014c3d8\n"
        "ldr r0, [r0, #4]\n"
        "ldr r0, [r0]\n"
        "cmp r0, r1\n"
        "ldrhi r0, [r3, r1, lsl #2]\n"
        "strhi r2, [r3, r1, lsl #2]\n"
        "bhi .L_engine_func_0014c3ac_0014c3dc\n"
        ".L_engine_func_0014c3ac_0014c3d8:\n"
        "mov r0, #0\n"
        ".L_engine_func_0014c3ac_0014c3dc:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0022a60c, 52)
extern "C" __attribute__((naked)) void shop_func_0022a60c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r0\n"
        "ldrb r0, [r0, #0x62]\n"
        "mov r5, r1\n"
        "cmp r0, #0\n"
        "bne .L_shop_func_0022a60c_0022a63c\n"
        "add r0, r4, #0x28\n"
        "ldr r0, [r0, #0x24]\n"
        "cmp r0, r5\n"
        "movne r0, #1\n"
        "strbne r0, [r4, #0x61]\n"
        "str r5, [r4, #0x4c]\n"
        ".L_shop_func_0022a60c_0022a63c:\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x00236420, 52)
extern "C" __attribute__((naked)) void func_00236420() {
    asm volatile(
        "ldr r1, [r0, #0x3c]\n"
        "mov r2, #0x180\n"
        "bic r1, r1, #0x60\n"
        "bics r2, r2, r1\n"
        "str r1, [r0, #0x3c]\n"
        "bne .L_func_00236420_00236450\n"
        "orr r1, r1, #0x40\n"
        "mov r2, #0x200\n"
        "bics r2, r2, r1\n"
        "str r1, [r0, #0x3c]\n"
        "orreq r1, r1, #0x20\n"
        "streq r1, [r0, #0x3c]\n"
        ".L_func_00236420_00236450:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00294180, 52)
extern "C" __attribute__((naked)) void ui_func_00294180() {
    asm volatile(
        "ldr r1, [r0, #4]\n"
        "cmp r1, #0\n"
        "ldreq r1, [r0, #0x10]\n"
        "cmpeq r1, #0\n"
        "bne .L_ui_func_00294180_002941ac\n"
        "ldr r1, [r0, #0x60]\n"
        "cmp r1, #0\n"
        "ldreq r0, [r0, #0xb0]\n"
        "cmpeq r0, #0\n"
        "moveq r0, #1\n"
        "beq .L_ui_func_00294180_002941b0\n"
        ".L_ui_func_00294180_002941ac:\n"
        "mov r0, #0\n"
        ".L_ui_func_00294180_002941b0:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00299000, 52)
extern "C" __attribute__((naked)) void script_vm_func_00299000() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r0\n"
        "ldrb r0, [r0, #0x62]\n"
        "mov r5, r1\n"
        "cmp r0, #0\n"
        "bne .L_script_vm_func_00299000_00299030\n"
        "mov r0, r4\n"
        "ldr r0, [r0, #0x24]\n"
        "cmp r0, r5\n"
        "movne r0, #1\n"
        "strbne r0, [r4, #0x60]\n"
        "str r5, [r4, #0x24]\n"
        ".L_script_vm_func_00299000_00299030:\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x002b4fb0, 52)
extern "C" __attribute__((naked)) void func_002b4fb0() {
    asm volatile(
        "ldr r3, [r0]\n"
        "add r2, r2, r1\n"
        "cmp r3, #0\n"
        "beq .L_func_002b4fb0_002b4fe0\n"
        ".L_func_002b4fb0_002b4fc0:\n"
        "cmp r1, r3\n"
        "cmpls r3, r2\n"
        "ldrlo ip, [r3]\n"
        "movhs r0, r3\n"
        "strlo ip, [r0]\n"
        "ldr r3, [r3]\n"
        "cmp r3, #0\n"
        "bne .L_func_002b4fb0_002b4fc0\n"
        ".L_func_002b4fb0_002b4fe0:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003385a4, 52)
extern "C" __attribute__((naked)) void func_003385a4() {
    asm volatile(
        "mov r1, #0\n"
        "mov r3, #0x6d\n"
        "mvn r2, #0\n"
        ".L_func_003385a4_003385b0:\n"
        "rsb ip, r1, r1, lsl #3\n"
        "subs r3, r3, #1\n"
        "add ip, r0, ip, lsl #2\n"
        "add ip, ip, #0x2000\n"
        "add r1, r1, #1\n"
        "str r2, [ip, #0x318]\n"
        "str r2, [ip, #0x31c]\n"
        "str r2, [ip, #0x330]\n"
        "bne .L_func_003385a4_003385b0\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0033b590, 52)
extern "C" __attribute__((naked)) void func_0033b590() {
    asm volatile(
        "add r0, r0, r1, lsl #2\n"
        "add r0, r0, #0x4800\n"
        "add r0, r0, #0x224\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "cmpne r0, #1\n"
        "beq .L_func_0033b590_0033b5bc\n"
        "cmp r0, #2\n"
        "cmpne r0, #3\n"
        "movne r0, #0\n"
        "bne .L_func_0033b590_0033b5c0\n"
        ".L_func_0033b590_0033b5bc:\n"
        "mov r0, #1\n"
        ".L_func_0033b590_0033b5c0:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0033b5c4, 52)
extern "C" __attribute__((naked)) void func_0033b5c4() {
    asm volatile(
        "add r0, r0, r1, lsl #2\n"
        "add r0, r0, #0x4800\n"
        "add r0, r0, #0x224\n"
        "ldr r0, [r0]\n"
        "cmp r0, #4\n"
        "cmpne r0, #5\n"
        "beq .L_func_0033b5c4_0033b5f0\n"
        "cmp r0, #6\n"
        "cmpne r0, #7\n"
        "movne r0, #0\n"
        "bne .L_func_0033b5c4_0033b5f4\n"
        ".L_func_0033b5c4_0033b5f0:\n"
        "mov r0, #1\n"
        ".L_func_0033b5c4_0033b5f4:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0037bc14, 52)
extern "C" __attribute__((naked)) void func_0037bc14() {
    asm volatile(
        "mov r1, #0\n"
        "str r4, [sp, #-4]!\n"
        "mov r2, #9\n"
        "mov ip, r1\n"
        "mvn r4, #0\n"
        ".L_func_0037bc14_0037bc28:\n"
        "add r3, r0, r1, lsl #3\n"
        "add r3, r3, #0x218\n"
        "subs r2, r2, #1\n"
        "stm r3, {r4, ip}\n"
        "add r1, r1, #1\n"
        "bne .L_func_0037bc14_0037bc28\n"
        "pop {r4}\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003803ec, 52)
extern "C" __attribute__((naked)) void func_003803ec() {
    asm volatile(
        "mov r3, r0\n"
        "mov r0, r1\n"
        "ldrb r1, [r3, r0]!\n"
        "cmp r1, #0xfe\n"
        "movne r1, #1\n"
        "strne r1, [r2]\n"
        "bne .L_func_003803ec_0038041c\n"
        "ldrb r1, [r3, #1]\n"
        "ldrb r3, [r3, #2]\n"
        "add r0, r0, #3\n"
        "orr r1, r3, r1, lsl #8\n"
        "str r1, [r2]\n"
        ".L_func_003803ec_0038041c:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003ac980, 52)
extern "C" __attribute__((naked)) void func_003ac980() {
    asm volatile(
        "mov r2, r0\n"
        "ldrh r0, [r0, #0xe]\n"
        "ldrh r3, [r1, #0xe]\n"
        "subs r0, r0, r3\n"
        "bne .L_func_003ac980_003ac9b0\n"
        "ldrb r0, [r2, #0xc]\n"
        "ldrb r3, [r1, #0xc]\n"
        "subs r0, r0, r3\n"
        "bne .L_func_003ac980_003ac9b0\n"
        "ldrh r0, [r2]\n"
        "ldrh r1, [r1]\n"
        "sub r0, r0, r1\n"
        ".L_func_003ac980_003ac9b0:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003ac9d8, 52)
extern "C" __attribute__((naked)) void func_003ac9d8() {
    asm volatile(
        "mov r2, r0\n"
        "ldrh r0, [r0, #0x12]\n"
        "ldrh r3, [r1, #0x12]\n"
        "subs r0, r0, r3\n"
        "bne .L_func_003ac9d8_003aca08\n"
        "ldrb r0, [r2, #0xc]\n"
        "ldrb r3, [r1, #0xc]\n"
        "subs r0, r0, r3\n"
        "bne .L_func_003ac9d8_003aca08\n"
        "ldrh r0, [r2]\n"
        "ldrh r1, [r1]\n"
        "sub r0, r0, r1\n"
        ".L_func_003ac9d8_003aca08:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003acc9c, 52)
extern "C" __attribute__((naked)) void func_003acc9c() {
    asm volatile(
        "mov r2, r0\n"
        "ldrh r0, [r1, #0xe]\n"
        "ldrh r3, [r2, #0xe]\n"
        "subs r0, r0, r3\n"
        "bne .L_func_003acc9c_003acccc\n"
        "ldrb r0, [r1, #0xc]\n"
        "ldrb r3, [r2, #0xc]\n"
        "subs r0, r0, r3\n"
        "bne .L_func_003acc9c_003acccc\n"
        "ldrh r0, [r1]\n"
        "ldrh r1, [r2]\n"
        "sub r0, r0, r1\n"
        ".L_func_003acc9c_003acccc:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003accf4, 52)
extern "C" __attribute__((naked)) void func_003accf4() {
    asm volatile(
        "mov r2, r0\n"
        "ldrh r0, [r1, #0x12]\n"
        "ldrh r3, [r2, #0x12]\n"
        "subs r0, r0, r3\n"
        "bne .L_func_003accf4_003acd24\n"
        "ldrb r0, [r1, #0xc]\n"
        "ldrb r3, [r2, #0xc]\n"
        "subs r0, r0, r3\n"
        "bne .L_func_003accf4_003acd24\n"
        "ldrh r0, [r1]\n"
        "ldrh r1, [r2]\n"
        "sub r0, r0, r1\n"
        ".L_func_003accf4_003acd24:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003ace08, 52)
extern "C" __attribute__((naked)) void func_003ace08() {
    asm volatile(
        "mov r2, r0\n"
        "ldrb r0, [r0, #2]\n"
        "ldrb r3, [r1, #2]\n"
        "subs r0, r0, r3\n"
        "bne .L_func_003ace08_003ace38\n"
        "ldrb r0, [r2, #0xc]\n"
        "ldrb r3, [r1, #0xc]\n"
        "subs r0, r0, r3\n"
        "bne .L_func_003ace08_003ace38\n"
        "ldrh r0, [r2]\n"
        "ldrh r1, [r1]\n"
        "sub r0, r0, r1\n"
        ".L_func_003ace08_003ace38:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003c2ad0, 52)
extern "C" __attribute__((naked)) void engine_func_003c2ad0() {
    asm volatile(
        "ldr r2, [r0, #4]\n"
        "cmp r2, #1\n"
        "beq .L_engine_func_003c2ad0_003c2b00\n"
        "strb r1, [r0, #0xa]\n"
        "mov r2, #1\n"
        "strb r1, [r0, #0xb]\n"
        "mov r3, #0\n"
        "str r2, [r0, #4]\n"
        "strb r3, [r0, #9]\n"
        "ldrb r1, [r0]\n"
        "orr r1, r1, #1\n"
        "strb r1, [r0]\n"
        ".L_engine_func_003c2ad0_003c2b00:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003c91f0, 52)
extern "C" __attribute__((naked)) void camp_func_003c91f0() {
    asm volatile(
        "strb r1, [r0, #0x120]\n"
        "cmp r3, #0\n"
        "strb r2, [r0, #0x121]\n"
        "beq .L_camp_func_003c91f0_003c9220\n"
        "ldr r1, [r3]\n"
        "str r1, [r0, #0x122]\n"
        "ldr r1, [r3, #4]\n"
        "str r1, [r0, #0x126]\n"
        "ldr r1, [r3, #8]\n"
        "str r1, [r0, #0x12a]\n"
        "ldr r1, [r3, #0xc]\n"
        "str r1, [r0, #0x12e]\n"
        ".L_camp_func_003c91f0_003c9220:\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003da7e0, 52)
extern "C" __attribute__((naked)) void func_003da7e0() {
    asm volatile(
        "add r0, r0, #0x3000\n"
        "ldr r1, [r0, #0x54]\n"
        "cmp r1, #0\n"
        "beq .L_func_003da7e0_003da80c\n"
        "ldrb r1, [r1, #8]\n"
        "tst r1, #1\n"
        "beq .L_func_003da7e0_003da80c\n"
        "ldr r0, [r0, #0x28]\n"
        "and r0, r0, #0x2000\n"
        "lsr r0, r0, #0xd\n"
        "bx lr\n"
        ".L_func_003da7e0_003da80c:\n"
        "mov r0, #1\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003df544, 52)
extern "C" __attribute__((naked)) void script_vm_func_003df544() {
    asm volatile(
        "ldr r1, [r1, #4]\n"
        "cmp r1, #0\n"
        "beq .L_script_vm_func_003df544_003df56c\n"
        "ldr r3, [r1, #4]\n"
        "cmp r2, r3\n"
        "bhi .L_script_vm_func_003df544_003df56c\n"
        "ldr r1, [r1]\n"
        "add r2, r2, r2, lsl #1\n"
        "add r1, r1, r2, lsl #4\n"
        "b .L_script_vm_func_003df544_003df570\n"
        ".L_script_vm_func_003df544_003df56c:\n"
        "mov r1, #0\n"
        ".L_script_vm_func_003df544_003df570:\n"
        "str r1, [r0]\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003f5a08, 52)
extern "C" __attribute__((naked)) void func_003f5a08() {
    asm volatile(
        "ldr r0, [r0, #4]\n"
        "mov r0, r0\n"
        "cmp r0, #0\n"
        "beq .L_func_003f5a08_003f5a38\n"
        "ldr ip, [r0, #0x18]\n"
        "ldr r3, [r0]\n"
        "cmp ip, #1\n"
        "addeq r3, r3, #0x20\n"
        "str r3, [r1]\n"
        "ldr r0, [r0, #8]\n"
        "str r0, [r2]\n"
        "mov r0, #1\n"
        ".L_func_003f5a08_003f5a38:\n"
        "bx lr\n"
    );
}
