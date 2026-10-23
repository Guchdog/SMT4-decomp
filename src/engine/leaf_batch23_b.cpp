#include "types.h"

// Direct ARM BL targets are ledger symbols so supported R_ARM_CALL relocations can be resolved.
extern "C" void battle_func_0028df54();
extern "C" void camp_func_0022e4e8();
extern "C" void camp_func_00297688();
extern "C" void engine_func_00296f60();
extern "C" void engine_func_002adf14();
extern "C" void engine_func_002c4360();
extern "C" void func_00291950();
extern "C" void func_003dc244();
extern "C" void script_vm_func_00247084();
extern "C" void script_vm_func_0024c828();
extern "C" void script_vm_func_00287d74();
extern "C" void script_vm_func_002971e4();
extern "C" void script_vm_func_002b66ec();
extern "C" void ui_func_002c0ac8();

// Bounded post-return literal words remain at their original PC-relative offsets.
// DECOMP_FUNC(0x002f61a4, 32)
extern "C" __attribute__((naked)) void func_002f61a4() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0, #4]\n"
        "ldrb r0, [r0, #8]\n"
        "cmp r0, #4\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002fec24, 32)
extern "C" __attribute__((naked)) void script_vm_func_002fec24() {
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

// DECOMP_FUNC(0x0025bd48, 36)
extern "C" __attribute__((naked)) void ui_func_0025bd48() {
    asm volatile(
        "add r2, r1, r1, lsl #5\n"
        "add r1, r2, r1, lsl #7\n"
        "ldr r2, [pc, #0x10]\n"
        "add r1, r2, r1, lsl #2\n"
        "add r0, r1, r0, lsl #2\n"
        "ldr r0, [r0, #0x264]\n"
        "ldr r0, [r0, #8]\n"
        "bx lr\n"
        ".word 0x004d9d88\n"
    );
}

// DECOMP_FUNC(0x0026ada8, 36)
extern "C" __attribute__((naked)) void camp_func_0026ada8() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "ldrbne r0, [r0, #0x430]\n"
        "cmpne r0, #0\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0043dd68\n"
    );
}

// DECOMP_FUNC(0x0027ceb8, 36)
extern "C" __attribute__((naked)) void script_vm_func_0027ceb8() {
    asm volatile(
        "ldr r2, [pc, #0x18]\n"
        "mov r3, #0\n"
        "ldr r2, [r2]\n"
        "strh r3, [r2, #8]\n"
        "strh r3, [r2, #0xa]\n"
        "strh r0, [r2, #4]\n"
        "strh r1, [r2, #6]\n"
        "bx lr\n"
        ".word 0x0044cd88\n"
    );
}

// DECOMP_FUNC(0x0027db00, 36)
extern "C" __attribute__((naked)) void script_vm_func_0027db00() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "mov r1, #2\n"
        "mov r2, #0xff\n"
        "ldr r0, [r0]\n"
        "add r3, r0, #0x30\n"
        "stm r3, {r1, r2}\n"
        "str r1, [r0, #0x38]\n"
        "bx lr\n"
        ".word 0x00447a78\n"
    );
}

// DECOMP_FUNC(0x0027de14, 36)
extern "C" __attribute__((naked)) void script_vm_func_0027de14() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "mov r2, #1\n"
        "mov r1, #0\n"
        "ldr r0, [r0]\n"
        "strb r2, [r0, #0xfd8]\n"
        "strb r1, [r0, #0xe96]\n"
        "strb r1, [r0, #0xe95]\n"
        "bx lr\n"
        ".word 0x0043e278\n"
    );
}

// DECOMP_FUNC(0x0028f914, 36)
extern "C" __attribute__((naked)) void camp_func_0028f914() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "ldrne r0, [r0, #0x400]\n"
        "cmpne r0, #0x24\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0043dd68\n"
    );
}

// DECOMP_FUNC(0x0029111c, 36)
extern "C" __attribute__((naked)) void shop_func_0029111c() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0, #8]\n"
        "cmp r0, #0\n"
        "ldrbne r0, [r0, #8]\n"
        "cmpne r0, #0\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002958bc, 36)
extern "C" __attribute__((naked)) void script_vm_func_002958bc() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1000\n"
        "ldr r0, [r0, #0x2dc]\n"
        "cmp r0, #3\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x002958e0, 36)
extern "C" __attribute__((naked)) void script_vm_func_002958e0() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1000\n"
        "ldr r0, [r0, #0x2dc]\n"
        "cmp r0, #8\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x0029e398, 36)
extern "C" __attribute__((naked)) void script_vm_func_0029e398() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1000\n"
        "ldr r0, [r0, #0x2dc]\n"
        "cmp r0, #1\n"
        "moveq r0, #0\n"
        "movne r0, #1\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x0029e468, 36)
extern "C" __attribute__((naked)) void camp_func_0029e468() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "ldrne r0, [r0, #0x744]\n"
        "cmpne r0, #4\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0043dd20\n"
    );
}

// DECOMP_FUNC(0x002a0f88, 36)
extern "C" __attribute__((naked)) void script_vm_func_002a0f88() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "ldrbne r0, [r0, #8]\n"
        "cmpne r0, #0\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002a3068, 36)
extern "C" __attribute__((naked)) void battle_func_002a3068() {
    asm volatile(
        "ldr r1, [pc, #0x18]\n"
        "add r0, r0, r0, lsl #1\n"
        "mov r3, #1\n"
        "add r0, r1, r0, lsl #3\n"
        "mov r2, #0\n"
        "strb r3, [r0, #4]\n"
        "strb r2, [r0, #5]\n"
        "bx lr\n"
        ".word 0x004dad80\n"
    );
}

// DECOMP_FUNC(0x002a89e4, 36)
extern "C" __attribute__((naked)) void camp_func_002a89e4() {
    asm volatile(
        "ldr r2, [pc, #0x18]\n"
        "add r1, r0, r0, lsl #7\n"
        "add r1, r1, r0, lsl #8\n"
        "ldr r2, [r2, #4]\n"
        "add r0, r2, #0x8c\n"
        "add r0, r0, r1, lsl #2\n"
        "add r0, r0, #0x90\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002a8a8c, 36)
extern "C" __attribute__((naked)) void ui_func_002a8a8c() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x600\n"
        "ldrsh r1, [r0, #0x4c]\n"
        "cmp r1, #0\n"
        "subgt r1, r1, #1\n"
        "strhgt r1, [r0, #0x4c]\n"
        "bx lr\n"
        ".word 0x0043dcb0\n"
    );
}

// DECOMP_FUNC(0x002b9008, 36)
extern "C" __attribute__((naked)) void camp_func_002b9008() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x600\n"
        "ldrsh r1, [r0, #0x4a]\n"
        "cmp r1, #0xa\n"
        "subgt r1, r1, #1\n"
        "strhgt r1, [r0, #0x4a]\n"
        "bx lr\n"
        ".word 0x0043dcb0\n"
    );
}

// DECOMP_FUNC(0x002c2684, 36)
extern "C" __attribute__((naked)) void battle_func_002c2684() {
    asm volatile(
        "ldr r2, [pc, #0x18]\n"
        "ldr r3, [r2, #0x124]\n"
        "add r3, r2, r3, lsl #2\n"
        "str r0, [r3, #0x134]\n"
        "ldr r0, [r2, #0x124]\n"
        "add r0, r2, r0, lsl #2\n"
        "str r1, [r0, #0x140]\n"
        "bx lr\n"
        ".word 0x004c6290\n"
    );
}

// DECOMP_FUNC(0x002c58cc, 36)
extern "C" __attribute__((naked)) void script_vm_func_002c58cc() {
    asm volatile(
        "ldr r1, [pc, #0x18]\n"
        "ldr r2, [r1, #0x18]\n"
        "bics r0, r2, r0\n"
        "str r0, [r1, #0x18]\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "strb r0, [r1, #2]\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002e10a4, 36)
extern "C" __attribute__((naked)) void func_002e10a4() {
    asm volatile(
        "add r2, r1, r1, lsl #5\n"
        "add r1, r2, r1, lsl #7\n"
        "ldr r2, [pc, #0x10]\n"
        "add r1, r2, r1, lsl #2\n"
        "add r0, r1, r0, lsl #2\n"
        "ldr r0, [r0, #0x264]\n"
        "ldr r0, [r0, #8]\n"
        "bx lr\n"
        ".word 0x004d9880\n"
    );
}

// DECOMP_FUNC(0x002e3118, 36)
extern "C" __attribute__((naked)) void func_002e3118() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1e00\n"
        "ldrb r0, [r0, #0xb4]\n"
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x002ed3e0, 36)
extern "C" __attribute__((naked)) void func_002ed3e0() {
    asm volatile(
        "mov r0, r0\n"
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0, #8]\n"
        "ldrb r0, [r0, #0x7c]\n"
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002597cc, 40)
extern "C" __attribute__((naked)) void camp_func_002597cc() {
    asm volatile(
        "ldr r1, [pc, #0x18]\n"
        "ldr r2, [pc, #0x18]\n"
        "ldr r1, [r1, #4]\n"
        "add r1, r1, #0x88\n"
        "ldrb r1, [r1, r2]\n"
        "ands r0, r0, r1\n"
        "movne r0, #1\n"
        "bx lr\n"
        ".word 0x0043e2a8\n"
        ".word 0x00024b27\n"
    );
}

// DECOMP_FUNC(0x00276034, 40)
extern "C" __attribute__((naked)) void script_vm_func_00276034() {
    asm volatile(
        "ldr r0, [pc, #0x1c]\n"
        "mov r2, #1\n"
        "mov r1, #0\n"
        "ldr r0, [r0]\n"
        "strb r2, [r0, #0xf28]\n"
        "strb r1, [r0, #0xf2b]\n"
        "strb r1, [r0, #0xf2c]\n"
        "strb r1, [r0, #0xf2d]\n"
        "bx lr\n"
        ".word 0x0043e278\n"
    );
}

// DECOMP_FUNC(0x00298fc4, 40)
extern "C" __attribute__((naked)) void camp_func_00298fc4() {
    asm volatile(
        "ldr r2, [pc, #0x1c]\n"
        "ldr r2, [r2, #4]\n"
        "add r3, r2, #0x1c00\n"
        "add r3, r3, #0x268\n"
        "add r2, r2, #0x1c00\n"
        "add r2, r2, #0x26c\n"
        "str r0, [r3]\n"
        "str r1, [r2]\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x0029d8fc, 40)
extern "C" __attribute__((naked)) void ui_func_0029d8fc() {
    asm volatile(
        "ldr r1, [pc, #0x18]\n"
        "ldr r2, [pc, #0x18]\n"
        "ldr r1, [r1, #4]\n"
        "ldrsh r2, [r2, r1]\n"
        "cmp r2, r0\n"
        "ldrbeq r0, [r1, #8]\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0043dcb0\n"
        ".word 0x0000064e\n"
    );
}

// DECOMP_FUNC(0x0029e8c0, 40)
extern "C" __attribute__((naked)) void camp_func_0029e8c0() {
    asm volatile(
        "ldr r2, [pc, #0x1c]\n"
        "mov r3, #1\n"
        "ldr r2, [r2, #8]\n"
        "strb r1, [r2, #0x81]\n"
        "str r0, [r2, #0x70]\n"
        "str r0, [r2, #0x74]\n"
        "mov r0, r3\n"
        "strb r3, [r2, #0x80]\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x0029eb30, 40)
extern "C" __attribute__((naked)) void camp_func_0029eb30() {
    asm volatile(
        "ldr r2, [pc, #0x1c]\n"
        "cmp r0, #0\n"
        "ldr r2, [r2, #4]\n"
        "add r2, r2, #0x1000\n"
        "strb r0, [r2, #0x2ef]\n"
        "movlt r0, #0\n"
        "strblt r0, [r2, #0x2f4]\n"
        "strbge r1, [r2, #0x2f4]\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x002a0678, 40)
extern "C" __attribute__((naked)) void ui_func_002a0678() {
    asm volatile(
        "ldr r2, [pc, #0x1c]\n"
        "add r0, r0, r0, lsl #2\n"
        "mov r3, #0\n"
        "add r0, r2, r0, lsl #2\n"
        "mov r2, #2\n"
        "str r1, [r0, #8]\n"
        "str r3, [r0, #4]\n"
        "strb r2, [r0, #0x10]\n"
        "bx lr\n"
        ".word 0x004d9758\n"
    );
}

// DECOMP_FUNC(0x002db968, 40)
extern "C" __attribute__((naked)) void func_002db968() {
    asm volatile(
        "vldmia r0, {s0, s1, s2, s3, s4, s5, s6, s7}\n"
        "add r0, r0, #0x20\n"
        "ldr r1, [pc, #0x14]\n"
        "add r2, r1, #0x180\n"
        "add r1, r1, #0x1a0\n"
        "vstmia r2, {s0, s1, s2, s3, s4, s5, s6, s7}\n"
        "vldmia r0, {s0, s1, s2, s3, s4, s5, s6, s7}\n"
        "vstmia r1, {s0, s1, s2, s3, s4, s5, s6, s7}\n"
        "bx lr\n"
        ".word 0x004ea81c\n"
    );
}

// DECOMP_FUNC(0x002e0594, 40)
extern "C" __attribute__((naked)) void script_vm_func_002e0594() {
    asm volatile(
        "ldm r0, {r1, r2, ip}\n"
        "mov r3, #1\n"
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0]\n"
        "str r1, [r0, #0x1c]\n"
        "add r1, r0, #0x20\n"
        "stm r1, {r2, ip}\n"
        "strb r3, [r0, #9]\n"
        "bx lr\n"
        ".word 0x0044cdf0\n"
    );
}

// DECOMP_FUNC(0x002f98ec, 40)
extern "C" __attribute__((naked)) void func_002f98ec() {
    asm volatile(
        "ldr r2, [r1]\n"
        "vldr s0, [pc, #0x18]\n"
        "str r2, [r0, #0x20]\n"
        "ldr r2, [r1, #4]\n"
        "str r2, [r0, #0x24]\n"
        "ldr r1, [r1, #8]\n"
        "str r1, [r0, #0x28]\n"
        "vstr s0, [r0, #0x2c]\n"
        "bx lr\n"
        ".word 0x00000000\n"
    );
}

// DECOMP_FUNC(0x002faf14, 40)
extern "C" __attribute__((naked)) void func_002faf14() {
    asm volatile(
        "ldr r2, [r1]\n"
        "vldr s0, [pc, #0x18]\n"
        "str r2, [r0, #0x20]\n"
        "ldr r2, [r1, #4]\n"
        "str r2, [r0, #0x24]\n"
        "ldr r1, [r1, #8]\n"
        "str r1, [r0, #0x28]\n"
        "vstr s0, [r0, #0x2c]\n"
        "bx lr\n"
        ".word 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x002fea30, 40)
extern "C" __attribute__((naked)) void func_002fea30() {
    asm volatile(
        "ldr r0, [pc, #0x1c]\n"
        "mov r1, #0\n"
        "ldr r2, [r0, #4]\n"
        "cmp r2, #0\n"
        "strbne r1, [r2, #0x5f]\n"
        "ldr r0, [r0, #8]\n"
        "cmp r0, #0\n"
        "strbne r1, [r0, #0x5f]\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x0027605c, 44)
extern "C" __attribute__((naked)) void script_vm_func_0027605c() {
    asm volatile(
        "ldr r0, [pc, #0x20]\n"
        "mov r2, #1\n"
        "mov r1, #0\n"
        "ldr r0, [r0]\n"
        "strb r2, [r0, #0xf60]\n"
        "strb r1, [r0, #0xf63]\n"
        "strb r1, [r0, #0xf64]\n"
        "strb r1, [r0, #0xf65]\n"
        "strb r1, [r0, #0xf99]\n"
        "bx lr\n"
        ".word 0x0043e278\n"
    );
}

// DECOMP_FUNC(0x0027e5fc, 44)
extern "C" __attribute__((naked)) void engine_func_0027e5fc() {
    asm volatile(
        "mov r2, #9\n"
        "mov r1, #0\n"
        "str r2, [r0]\n"
        "strb r1, [r0, #0x2c]\n"
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0x2c00\n"
        "add r0, r0, #0x398\n"
        "str r1, [r0]\n"
        "bx lr\n"
        ".word 0x00435d18\n"
    );
}

// DECOMP_FUNC(0x0029c660, 44)
extern "C" __attribute__((naked)) void script_vm_func_0029c660() {
    asm volatile(
        "ldr r3, [pc, #0x20]\n"
        "add r0, r0, r0, lsl #2\n"
        "mov ip, #0\n"
        "add r0, r3, r0, lsl #2\n"
        "mov r3, #1\n"
        "str r1, [r0, #8]\n"
        "str ip, [r0, #4]\n"
        "strb r3, [r0, #0x10]\n"
        "str r2, [r0, #0xc]\n"
        "bx lr\n"
        ".word 0x004d9758\n"
    );
}

// DECOMP_FUNC(0x002a49d0, 44)
extern "C" __attribute__((naked)) void func_002a49d0() {
    asm volatile(
        "vldr s0, [pc, #0x1c]\n"
        "mov r2, #1\n"
        "vldr s1, [pc, #0x18]\n"
        "vstr s0, [r0]\n"
        "strb r2, [r0, #0xc]\n"
        "mov r1, #0\n"
        "vstr s1, [r0, #4]\n"
        "str r1, [r0, #8]\n"
        "bx lr\n"
        ".word 0x00000000\n"
        ".word 0x40c80000\n"
    );
}

// DECOMP_FUNC(0x002aed40, 44)
extern "C" __attribute__((naked)) void engine_func_002aed40() {
    asm volatile(
        "ldr r2, [pc, #0x20]\n"
        "ldr r1, [r2]\n"
        "cmp r1, #0\n"
        "ldrne r2, [r2, #4]\n"
        "cmpne r2, r0\n"
        "addhi r2, r0, r0, lsl #1\n"
        "addhi r0, r2, r0, lsl #3\n"
        "movls r0, #0\n"
        "addhi r0, r1, r0, lsl #2\n"
        "bx lr\n"
        ".word 0x00464a70\n"
    );
}

// DECOMP_FUNC(0x002c2ba4, 44)
extern "C" __attribute__((naked)) void script_vm_func_002c2ba4() {
    asm volatile(
        "ldr r3, [pc, #0x20]\n"
        "add r0, r0, r0, lsl #2\n"
        "mov ip, #0\n"
        "add r0, r3, r0, lsl #2\n"
        "mov r3, #2\n"
        "str r1, [r0, #8]\n"
        "str ip, [r0, #4]\n"
        "strb r3, [r0, #0x10]\n"
        "str r2, [r0, #0xc]\n"
        "bx lr\n"
        ".word 0x004d9758\n"
    );
}

// DECOMP_FUNC(0x002d5618, 44)
extern "C" __attribute__((naked)) void camp_func_002d5618() {
    asm volatile(
        "ldr ip, [pc, #0x20]\n"
        "str r4, [sp, #-4]!\n"
        "mov r4, #1\n"
        "strb r4, [ip, #0x10]\n"
        "strh r0, [ip, #2]\n"
        "strh r1, [ip, #6]\n"
        "strh r2, [ip, #0xa]\n"
        "strh r3, [ip, #0xe]\n"
        "pop {r4}\n"
        "bx lr\n"
        ".word 0x00465278\n"
    );
}

// DECOMP_FUNC(0x002fde90, 44)
extern "C" __attribute__((naked)) void func_002fde90() {
    asm volatile(
        "add r3, r0, r0, lsl #3\n"
        "add r0, r3, r0, lsl #5\n"
        "ldr r3, [pc, #0x18]\n"
        "add r1, r1, r1, lsl #2\n"
        "mov r2, #6\n"
        "add r0, r3, r0, lsl #3\n"
        "add r1, r2, r1, lsl #2\n"
        "ldr r0, [r0, #0x13c]\n"
        "ldrsh r0, [r0, r1]\n"
        "bx lr\n"
        ".word 0x00478000\n"
    );
}

// DECOMP_FUNC(0x002573ec, 48)
extern "C" __attribute__((naked)) void ui_func_002573ec() {
    asm volatile(
        "ldr r2, [pc, #0x24]\n"
        "add r3, r2, #0x14\n"
        "ldr ip, [r2, r1, lsl #2]\n"
        "cmp ip, #0\n"
        "streq r0, [r2, r1, lsl #2]\n"
        "ldrne r2, [r3, r1, lsl #2]\n"
        "strne r0, [r2]\n"
        "mov r2, #0\n"
        "str r0, [r3, r1, lsl #2]\n"
        "str r2, [r0]\n"
        "bx lr\n"
        ".word 0x004ea7d4\n"
    );
}

// DECOMP_FUNC(0x0026e85c, 48)
extern "C" __attribute__((naked)) void camp_func_0026e85c() {
    asm volatile(
        "cmp r1, #0\n"
        "ldr r1, [pc, #0x20]\n"
        "ldr r2, [pc, #0x18]\n"
        "ldr r1, [r1, #4]\n"
        "add r1, r1, #0x88\n"
        "ldrb r2, [r1, r2]!\n"
        "orrne r0, r0, r2\n"
        "biceq r0, r2, r0\n"
        "strb r0, [r1]\n"
        "bx lr\n"
        ".word 0x00024b27\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x00273610, 48)
extern "C" __attribute__((naked)) void script_vm_func_00273610() {
    asm volatile(
        "ldr r1, [pc, #0x24]\n"
        "mov r3, #1\n"
        "mov r2, #0\n"
        "ldr r1, [r1]\n"
        "strb r3, [r1, #0xf9a]\n"
        "strb r2, [r1, #0xf9c]\n"
        "strb r2, [r1, #0xf9d]\n"
        "strb r2, [r1, #0xf9e]\n"
        "str r2, [r1, #0xfd0]!\n"
        "str r0, [r1, #4]\n"
        "bx lr\n"
        ".word 0x0043e278\n"
    );
}

// DECOMP_FUNC(0x00287990, 48)
extern "C" __attribute__((naked)) void script_vm_func_00287990() {
    asm volatile(
        "ldr r1, [pc, #0x20]\n"
        "add r0, r0, r0, lsl #2\n"
        "vldr s0, [pc, #0x1c]\n"
        "add r0, r1, r0, lsl #2\n"
        "mov r1, #0\n"
        "str r1, [r0, #4]\n"
        "str r1, [r0, #8]\n"
        "strb r1, [r0, #0x10]\n"
        "vstr s0, [r0]\n"
        "bx lr\n"
        ".word 0x004d9758\n"
        ".word 0x00000000\n"
    );
}

// DECOMP_FUNC(0x0029c6dc, 48)
extern "C" __attribute__((naked)) void camp_func_0029c6dc() {
    asm volatile(
        "ldr r2, [pc, #0x24]\n"
        "mov ip, #3\n"
        "mov r3, #0\n"
        "ldr r2, [r2, #8]\n"
        "strb ip, [r2, #0x7c]\n"
        "str r0, [r2, #0x70]\n"
        "str r0, [r2, #0x74]\n"
        "strb r1, [r2, #0x81]\n"
        "mov r0, #1\n"
        "str r3, [r2, #0x64]\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002cf2d8, 48)
extern "C" __attribute__((naked)) void ui_func_002cf2d8() {
    asm volatile(
        "ldr r0, [pc, #0x24]\n"
        "mov r1, #0\n"
        "mov r2, #2\n"
        "ldr r0, [r0, #4]\n"
        "strb r1, [r0, #0x74c]\n"
        "str r2, [r0, #0x744]\n"
        "ldrb r2, [r0, #0x74d]\n"
        "cmp r2, #0\n"
        "moveq r1, #1\n"
        "strb r1, [r0, #0x74d]\n"
        "bx lr\n"
        ".word 0x0043dd20\n"
    );
}

// DECOMP_FUNC(0x00259510, 52)
extern "C" __attribute__((naked)) void engine_func_00259510() {
    asm volatile(
        "ldr r1, [pc, #0x28]\n"
        "ldr r1, [r1, #0x20]\n"
        "ldr r2, [r1, #0x1c]\n"
        "sub r0, r2, r0\n"
        "sub r0, r0, #1\n"
        "add r2, r1, r0\n"
        "ldrb r2, [r2, #0x20]\n"
        "cmp r2, #5\n"
        "addeq r0, r1, r0, lsl #2\n"
        "movne r0, #0\n"
        "ldreq r0, [r0, #0x3c]\n"
        "bx lr\n"
        ".word 0x0044de98\n"
    );
}

// DECOMP_FUNC(0x00276088, 52)
extern "C" __attribute__((naked)) void script_vm_func_00276088() {
    asm volatile(
        "ldr r0, [pc, #0x28]\n"
        "mov r2, #4\n"
        "ldr r3, [pc, #0x1c]\n"
        "mov r1, #0\n"
        "ldr r0, [r0]\n"
        "str r2, [r0, #4]!\n"
        "str r1, [r0, #4]\n"
        "sub r0, r3, #0x100\n"
        "strh r1, [r3, #0x94]\n"
        "strb r1, [r0, #0x199]\n"
        "bx lr\n"
        ".word 0x0049fa1c\n"
        ".word 0x00447600\n"
    );
}

// DECOMP_FUNC(0x00282e6c, 52)
extern "C" __attribute__((naked)) void script_vm_func_00282e6c() {
    asm volatile(
        "ldr r2, [pc, #0x24]\n"
        "add r0, r0, r0, lsl #2\n"
        "mov r3, #0\n"
        "add r0, r2, r0, lsl #2\n"
        "mov r2, #3\n"
        "str r1, [r0, #0xc]\n"
        "vldr s0, [pc, #0x10]\n"
        "str r3, [r0, #4]\n"
        "strb r2, [r0, #0x10]\n"
        "vstr s0, [r0]\n"
        "bx lr\n"
        ".word 0x004d9758\n"
        ".word 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x00289010, 52)
extern "C" __attribute__((naked)) void func_00289010() {
    asm volatile(
        "ldr r2, [pc, #0x28]\n"
        "lsl r1, r1, #0xc\n"
        "smull r2, r1, r2, r1\n"
        "sub r1, r1, r1, asr #31\n"
        "add r1, r1, r1, lsl #2\n"
        "lsl r1, r1, #2\n"
        "cmp r1, #0x1000\n"
        "movlo r1, #0x1000\n"
        "cmp r1, r0, lsl #12\n"
        "movhs r0, #1\n"
        "movlo r0, #0\n"
        "bx lr\n"
        ".word 0x028f5c29\n"
    );
}

// DECOMP_FUNC(0x0029c538, 52)
extern "C" __attribute__((naked)) void camp_func_0029c538() {
    asm volatile(
        "ldr r2, [pc, #0x28]\n"
        "ldr r2, [r2]\n"
        "ldrh r3, [r2, #0x1e]\n"
        "add r3, r2, r3, lsl #1\n"
        "strh r0, [r3, #0xe]\n"
        "ldrh r0, [r2, #0x1e]\n"
        "add r0, r2, r0, lsl #1\n"
        "strh r1, [r0, #0x16]\n"
        "ldrh r0, [r2, #0x1e]\n"
        "add r0, r0, #1\n"
        "strh r0, [r2, #0x1e]\n"
        "bx lr\n"
        ".word 0x0043dd90\n"
    );
}

// DECOMP_FUNC(0x00286834, 56)
extern "C" __attribute__((naked)) void engine_func_00286834() {
    asm volatile(
        "vldr s2, [pc, #0x28]\n"
        "vldr s1, [pc, #0x28]\n"
        "cmp r0, #1\n"
        "mov r1, #1\n"
        "vmla.f32 s1, s0, s2\n"
        "moveq r1, #0\n"
        "orr r1, r1, r0, lsl #4\n"
        "vcvt.u32.f32 s0, s1\n"
        "vmov r0, s0\n"
        "and r0, r0, #0xff\n"
        "orr r0, r1, r0, lsl #8\n"
        "bx lr\n"
        ".word 0x437f0000\n"
        ".word 0x3f000000\n"
    );
}

// DECOMP_FUNC(0x002b3b34, 56)
extern "C" __attribute__((naked)) void func_002b3b34() {
    asm volatile(
        "and r1, r0, #0xff\n"
        "vmov s0, r1\n"
        "vldr s1, [pc, #0x20]\n"
        "ldr r1, [pc, #0x20]\n"
        "lsr r0, r0, #8\n"
        "add r0, r1, r0, lsl #4\n"
        "vcvt.f32.u32 s0, s0\n"
        "vldr s2, [r0, #8]\n"
        "vmul.f32 s1, s0, s1\n"
        "vldr s0, [r0]\n"
        "vmla.f32 s0, s2, s1\n"
        "bx lr\n"
        ".word 0x3b800000\n"
        ".word 0x00407fc0\n"
    );
}

// DECOMP_FUNC(0x002c0bcc, 56)
extern "C" __attribute__((naked)) void engine_func_002c0bcc() {
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
        ".word 0x004651c0\n"
        ".word 0x41c64e6d\n"
    );
}

// DECOMP_FUNC(0x002d3ddc, 56)
extern "C" __attribute__((naked)) void script_vm_func_002d3ddc() {
    asm volatile(
        "ldr r2, [pc, #0x2c]\n"
        "mov r3, #0\n"
        "cmp r0, #0x16\n"
        "mov ip, #0xa\n"
        "ldr r2, [r2]\n"
        "strh r0, [r2, #0xc]\n"
        "strh r1, [r2, #0xe]\n"
        "str r3, [r2, #4]\n"
        "str r3, [r2, #8]\n"
        "movne r0, #0x63\n"
        "str ip, [r2]\n"
        "strne r0, [r2]\n"
        "bx lr\n"
        ".word 0x00447e10\n"
    );
}

// DECOMP_FUNC(0x002d8174, 56)
extern "C" __attribute__((naked)) void func_002d8174() {
    asm volatile(
        "ldr r0, [pc, #0x28]\n"
        "ldr r1, [pc, #0x28]\n"
        "mov r2, #0\n"
        "mov r3, #1\n"
        "str r2, [r0, #0x4c]\n"
        "str r2, [r0, #0x58]\n"
        "strd r2, r3, [r0, #0x50]\n"
        "str r3, [r1, #0xc]\n"
        "ldr r0, [r1, #0x10]\n"
        "orr r0, r0, #0x10\n"
        "str r0, [r1, #0x10]\n"
        "bx lr\n"
        ".word 0x0044ea80\n"
        ".word 0x0044fca8\n"
    );
}

// DECOMP_FUNC(0x0029a3c4, 60)
extern "C" __attribute__((naked)) void script_vm_func_0029a3c4() {
    asm volatile(
        "ldr r1, [pc, #0x30]\n"
        "ldr r2, [pc, #0x2c]\n"
        "cmp r0, #7\n"
        "moveq r3, #1\n"
        "ldr r1, [r1, #4]\n"
        "ldr r2, [r2, #4]\n"
        "movne r3, #0\n"
        "add r1, r1, #0x1000\n"
        "add r2, r2, #0x1e00\n"
        "add r2, r2, #0x67\n"
        "moveq r0, #3\n"
        "strb r3, [r1, #0x2f3]\n"
        "strb r0, [r2]\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x002b7b34, 60)
extern "C" __attribute__((naked)) void engine_func_002b7b34() {
    asm volatile(
        "vldr s0, [r1]\n"
        "vldr s1, [r1, #0x10]\n"
        "vldr s2, [r1, #0x20]\n"
        "vldr s3, [pc, #0x24]\n"
        "vldr s4, [r1, #4]\n"
        "vldr s5, [r1, #0x14]\n"
        "vldr s6, [r1, #0x24]\n"
        "vldr s7, [pc, #0x14]\n"
        "vldr s8, [r1, #8]\n"
        "vldr s9, [r1, #0x18]\n"
        "vldr s10, [r1, #0x28]\n"
        "vldr s11, [pc, #4]\n"
        "vstmia r0, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}\n"
        "bx lr\n"
        ".word 0x00000000\n"
    );
}

// DECOMP_FUNC(0x0027dc18, 64)
extern "C" __attribute__((naked)) void ui_func_0027dc18() {
    asm volatile(
        "ldr r0, [pc, #0x2c]\n"
        "ldr r1, [pc, #0x2c]\n"
        "vldr s1, [pc, #0x2c]\n"
        "ldr r2, [r0]\n"
        "mul r1, r2, r1\n"
        "add r1, r1, #0x3000\n"
        "add r1, r1, #0x39\n"
        "str r1, [r0]\n"
        "lsr r0, r1, #0x10\n"
        "vmov s0, r0\n"
        "vcvt.f32.u32 s0, s0\n"
        "vmul.f32 s0, s0, s1\n"
        "bx lr\n"
        ".word 0x004651c0\n"
        ".word 0x41c64e6d\n"
        ".word 0x37800080\n"
    );
}

// DECOMP_FUNC(0x002735c8, 72)
extern "C" __attribute__((naked)) void script_vm_func_002735c8() {
    asm volatile(
        "ldr r1, [pc, #0x34]\n"
        "mov r2, #0\n"
        "mov r3, #0xa\n"
        "vldr s0, [pc, #0x2c]\n"
        "ldr r1, [r1, #4]\n"
        "vldr s1, [pc, #0x28]\n"
        "str r0, [r1, #0x208]\n"
        "strb r2, [r1, #0xb0]\n"
        "strb r2, [r1, #0xb1]\n"
        "strh r3, [r1, #0xb2]\n"
        "strh r2, [r1, #0xb4]\n"
        "vstr s0, [r1, #0xb8]\n"
        "add r1, r1, #0xbc\n"
        "vstmia r1, {s0, s1}\n"
        "bx lr\n"
        ".word 0x004474f0\n"
        ".word 0x00000000\n"
        ".word 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x002dffd8, 72)
extern "C" __attribute__((naked)) void engine_func_002dffd8() {
    asm volatile(
        "ldr r0, [pc, #0x3c]\n"
        "mov r1, #0x2840\n"
        "ldr r0, [r0]\n"
        "ldr r1, [r1, r0]\n"
        "add r2, r1, r1, lsl #5\n"
        "add r1, r2, r1, lsl #7\n"
        "mov r2, #0\n"
        "add r0, r0, r1, lsl #2\n"
        "ldr r1, [r0, #0x280]\n"
        "add r1, r1, r1, lsl #2\n"
        "add r1, r0, r1, lsl #3\n"
        "str r2, [r1], #4\n"
        "vstmia r1, {s0, s1, s2}\n"
        "ldr r1, [r0, #0x280]\n"
        "add r1, r1, #1\n"
        "str r1, [r0, #0x280]\n"
        "bx lr\n"
        ".word 0x00447e40\n"
    );
}

// DECOMP_FUNC(0x002f4fbc, 72)
extern "C" __attribute__((naked)) void camp_func_002f4fbc() {
    asm volatile(
        "ldr r1, [pc, #0x3c]\n"
        "ldr r3, [pc, #0x38]\n"
        "ldr r2, [pc, #0x30]\n"
        "ldr r1, [r1, #4]\n"
        "ldr r3, [r3, #4]\n"
        "add r1, r1, #0x24800\n"
        "add r1, r1, #0x3a8\n"
        "add ip, r3, #0x88\n"
        "ldr r3, [r1]\n"
        "add r1, ip, #0x24000\n"
        "add r1, r1, #0xb20\n"
        "add r0, r0, r3\n"
        "cmp r0, r2\n"
        "strhi r2, [r1]\n"
        "strls r0, [r1]\n"
        "bx lr\n"
        ".word 0x0098967f\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002bf710, 76)
extern "C" __attribute__((naked)) void ui_func_002bf710() {
    asm volatile(
        "vmov r0, s0\n"
        "vldr s1, [pc, #0x38]\n"
        "mov r1, #1\n"
        "cmp r0, #0x3f800000\n"
        "vldrgt s0, [pc, #0x28]\n"
        "ldr r0, [pc, #0x2c]\n"
        "vcmpe.f32 s0, s1\n"
        "vmrs apsr_nzcv, fpscr\n"
        "vmovlo.f32 s0, s1\n"
        "vstr s0, [r0, #0x84]\n"
        "vstr s0, [r0, #0x38]\n"
        "vstr s0, [r0, #0x48]\n"
        "vstr s0, [r0, #0x58]\n"
        "vstr s0, [r0, #0x68]\n"
        "strb r1, [r0, #0x7d]\n"
        "bx lr\n"
        ".word 0x3f800000\n"
        ".word 0x00000000\n"
        ".word 0x004d4680\n"
    );
}

// DECOMP_FUNC(0x00256c3c, 84)
extern "C" __attribute__((naked)) void engine_func_00256c3c() {
    asm volatile(
        "vldr s1, [pc, #0x48]\n"
        "vldr s0, [pc, #0x40]\n"
        "vstr s1, [r0, #0x3c]\n"
        "vstr s1, [r0, #0x28]\n"
        "vstr s1, [r0, #0x14]\n"
        "vstr s1, [r0]\n"
        "vstr s0, [r0, #0xc]\n"
        "vstr s0, [r0, #0x1c]\n"
        "vstr s0, [r0, #0x2c]\n"
        "vstr s0, [r0, #0x10]\n"
        "vstr s0, [r0, #8]\n"
        "vstr s0, [r0, #4]\n"
        "vstr s0, [r0, #0x24]\n"
        "vstr s0, [r0, #0x20]\n"
        "vstr s0, [r0, #0x18]\n"
        "vstr s0, [r0, #0x38]\n"
        "vstr s0, [r0, #0x34]\n"
        "vstr s0, [r0, #0x30]\n"
        "bx lr\n"
        ".word 0x00000000\n"
        ".word 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x0024ba44, 88)
extern "C" __attribute__((naked)) void engine_func_0024ba44() {
    asm volatile(
        "cmp r0, #0\n"
        "ldreq r0, [pc, #0x44]\n"
        "str r4, [sp, #-4]!\n"
        "vldr s1, [pc, #0x40]\n"
        "ldm r0, {r1, r2, r3, ip}\n"
        "str r2, [r0, #8]\n"
        "str r1, [r0, #4]\n"
        "lsl r4, ip, #1\n"
        "lsl ip, r2, #2\n"
        "orr r4, r4, r3, lsr #31\n"
        "orr r2, ip, r1, lsr #30\n"
        "eor r1, r2, r4\n"
        "str r1, [r0], #0xc\n"
        "str r3, [r0]\n"
        "bic r0, r1, #0xff000000\n"
        "vmov s0, r0\n"
        "pop {r4}\n"
        "vcvt.f32.u32 s0, s0\n"
        "vmul.f32 s0, s0, s1\n"
        "bx lr\n"
        ".word 0x004d9748\n"
        ".word 0x33800000\n"
    );
}

// DECOMP_FUNC(0x0026e8a0, 92)
extern "C" __attribute__((naked)) void shop_func_0026e8a0() {
    asm volatile(
        "ldr r1, [pc, #0x50]\n"
        "ldr r3, [pc, #0x48]\n"
        "ldr r2, [r1, #4]\n"
        "add r1, r2, #0x9800\n"
        "add r1, r1, #0x6c\n"
        "add r2, r2, #0x9000\n"
        "ldr ip, [r1]\n"
        "add r2, r2, #0x870\n"
        "add ip, ip, r0\n"
        "str ip, [r1]\n"
        "ldr r1, [r2]\n"
        "add r1, r1, r0\n"
        "ldr r0, [pc, #0x20]\n"
        "str r1, [r2]\n"
        "cmp r1, r3\n"
        "movls r3, r1\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x9000\n"
        "add r0, r0, #0x870\n"
        "str r3, [r0]\n"
        "bx lr\n"
        ".word 0x0000270f\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002bef14, 92)
extern "C" __attribute__((naked)) void script_vm_func_002bef14() {
    asm volatile(
        "ldr r0, [pc, #0x4c]\n"
        "vldr s0, [pc, #0x4c]\n"
        "ldr r2, [r0, #0x84]\n"
        "vstr s0, [r0, #0x2c]\n"
        "vstr s0, [r0, #0x30]\n"
        "vstr s0, [r0, #0x34]\n"
        "str r2, [r0, #0x38]\n"
        "vstr s0, [r0, #0x3c]\n"
        "vstr s0, [r0, #0x40]\n"
        "vstr s0, [r0, #0x44]\n"
        "str r2, [r0, #0x48]\n"
        "vstr s0, [r0, #0x4c]\n"
        "vstr s0, [r0, #0x50]\n"
        "vstr s0, [r0, #0x54]\n"
        "str r2, [r0, #0x58]!\n"
        "add r0, r0, #4\n"
        "vstr s0, [r0]\n"
        "vstr s0, [r0, #4]\n"
        "vstr s0, [r0, #8]\n"
        "str r2, [r0, #0xc]\n"
        "bx lr\n"
        ".word 0x004d4680\n"
        ".word 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x00246d94, 100)
extern "C" __attribute__((naked)) void func_00246d94() {
    asm volatile(
        "ldr r0, [pc, #0x58]\n"
        "vldr s0, [pc, #0x50]\n"
        "vldmia r0, {s1, s2, s3, s4}\n"
        "vmul.f32 s1, s1, s0\n"
        "vmul.f32 s2, s2, s0\n"
        "vmul.f32 s3, s3, s0\n"
        "vmul.f32 s4, s4, s0\n"
        "vcvt.u32.f32 s0, s1\n"
        "vcvt.u32.f32 s1, s2\n"
        "vmov r0, s0\n"
        "vmov r1, s1\n"
        "vcvt.u32.f32 s1, s3\n"
        "vcvt.u32.f32 s0, s4\n"
        "and r3, r1, #0xff\n"
        "lsl r0, r0, #0x18\n"
        "orr r0, r0, r3, lsl #16\n"
        "vmov r2, s1\n"
        "vmov r1, s0\n"
        "and r2, r2, #0xff\n"
        "and r1, r1, #0xff\n"
        "orr r0, r0, r2, lsl #8\n"
        "orr r0, r0, r1\n"
        "bx lr\n"
        ".word 0x437f0000\n"
        ".word 0x004ea91c\n"
    );
}

// DECOMP_FUNC(0x00246df8, 100)
extern "C" __attribute__((naked)) void func_00246df8() {
    asm volatile(
        "lsl r1, r0, #8\n"
        "lsl r3, r0, #0x10\n"
        "lsr r2, r1, #0x18\n"
        "lsr r1, r0, #0x18\n"
        "lsr r3, r3, #0x18\n"
        "and ip, r0, #0xff\n"
        "vmov s4, r1\n"
        "vmov s2, r2\n"
        "vmov s3, r3\n"
        "vmov s1, ip\n"
        "vldr s0, [pc, #0x2c]\n"
        "ldr r0, [pc, #0x2c]\n"
        "vcvt.f32.u32 s5, s4\n"
        "vcvt.f32.u32 s2, s2\n"
        "vcvt.f32.u32 s3, s3\n"
        "vcvt.f32.u32 s4, s1\n"
        "vmul.f32 s1, s5, s0\n"
        "vmul.f32 s2, s2, s0\n"
        "vmul.f32 s3, s3, s0\n"
        "vmul.f32 s0, s4, s0\n"
        "vstr s0, [r0, #0xc]\n"
        "vstmia r0, {s1, s2, s3}\n"
        "bx lr\n"
        ".word 0x3b808081\n"
        ".word 0x004ea91c\n"
    );
}

// DECOMP_FUNC(0x00257614, 100)
extern "C" __attribute__((naked)) void func_00257614() {
    asm volatile(
        "lsl r1, r0, #8\n"
        "lsl r3, r0, #0x10\n"
        "lsr r2, r1, #0x18\n"
        "lsr r1, r0, #0x18\n"
        "lsr r3, r3, #0x18\n"
        "and ip, r0, #0xff\n"
        "vmov s4, r1\n"
        "vmov s2, r2\n"
        "vmov s3, r3\n"
        "vmov s1, ip\n"
        "vldr s0, [pc, #0x2c]\n"
        "ldr r0, [pc, #0x2c]\n"
        "vcvt.f32.u32 s5, s4\n"
        "vcvt.f32.u32 s2, s2\n"
        "vcvt.f32.u32 s3, s3\n"
        "vcvt.f32.u32 s4, s1\n"
        "vmul.f32 s1, s5, s0\n"
        "vmul.f32 s2, s2, s0\n"
        "vmul.f32 s3, s3, s0\n"
        "vmul.f32 s0, s4, s0\n"
        "vstr s0, [r0, #0xc]\n"
        "vstmia r0, {s1, s2, s3}\n"
        "bx lr\n"
        ".word 0x3b808081\n"
        ".word 0x004ea91c\n"
    );
}

// DECOMP_FUNC(0x0024603c, 120)
extern "C" __attribute__((naked)) void func_0024603c() {
    asm volatile(
        "ldr r0, [pc, #0x6c]\n"
        "add r1, r0, #0x100\n"
        "add r0, r0, #0x140\n"
        "vldr s0, [r1]\n"
        "vldr s5, [r0, #8]\n"
        "vldr s14, [r0, #0xc]\n"
        "add r2, r0, #0x10\n"
        "vldmia r0, {s2, s3}\n"
        "vmul.f32 s5, s0, s5\n"
        "vldr s1, [r1, #4]\n"
        "add r0, r0, #0x20\n"
        "vmul.f32 s2, s0, s2\n"
        "vmul.f32 s3, s0, s3\n"
        "vmul.f32 s0, s0, s14\n"
        "vldmia r2, {s10, s11, s12, s13}\n"
        "vldr s4, [r1, #8]\n"
        "vldmia r0, {s6, s7, s8, s9}\n"
        "vmla.f32 s5, s1, s12\n"
        "vmla.f32 s2, s1, s10\n"
        "vmla.f32 s3, s1, s11\n"
        "vmla.f32 s0, s1, s13\n"
        "vmla.f32 s5, s4, s8\n"
        "vmla.f32 s2, s4, s6\n"
        "vmla.f32 s3, s4, s7\n"
        "vmla.f32 s0, s4, s9\n"
        "vstr s5, [r1, #8]\n"
        "vstr s0, [r1, #0xc]\n"
        "vstmia r1, {s2, s3}\n"
        "bx lr\n"
        ".word 0x004ea81c\n"
    );
}

// DECOMP_FUNC(0x0024511c, 124)
extern "C" __attribute__((naked)) void func_0024511c() {
    asm volatile(
        "push {r4, r5, r6, r7, r8, sb}\n"
        "mov r4, #4\n"
        "add r0, r0, r1, lsl #2\n"
        "ldr r6, [pc, #0x64]\n"
        "ldr ip, [sp, #0x18]\n"
        "mov r5, #0\n"
        "orr r7, r6, r4, lsl #1\n"
        "add r8, r7, r4, lsl #1\n"
        "str r4, [r6, r0]\n"
        "str r5, [r7, r0]\n"
        "ldr r1, [pc, #0x44]\n"
        "orr sb, r8, r4, lsl #1\n"
        "str r3, [r8, r0]\n"
        "bic r3, r7, r4, lsl #3\n"
        "str r2, [sb, r0]\n"
        "add r1, r1, r2, lsl #2\n"
        "ldr r3, [r3, r0]\n"
        "add r2, r0, #0x4800\n"
        "add r2, r2, #0x214\n"
        "add r0, r0, #0x4800\n"
        "str r3, [r2]\n"
        "ldr r1, [r1]\n"
        "add r0, r0, #0x21c\n"
        "rev r1, r1\n"
        "bic r1, r1, #0xff\n"
        "orr r1, r1, ip\n"
        "str r1, [r0]\n"
        "pop {r4, r5, r6, r7, r8, sb}\n"
        "bx lr\n"
        ".word 0x00439a3c\n"
        ".word 0x00004a24\n"
    );
}

// DECOMP_FUNC(0x002a2ea0, 124)
extern "C" __attribute__((naked)) void ui_func_002a2ea0() {
    asm volatile(
        "ldr r0, [pc, #0x70]\n"
        "add r1, r0, #0x110\n"
        "add r2, r0, #0x100\n"
        "vldmia r1, {s2, s3}\n"
        "add r1, r0, #0x100\n"
        "vldr s11, [r0, #0x108]\n"
        "vldr s9, [r0, #0x118]\n"
        "vldr s8, [r0, #0x10c]\n"
        "vmul.f32 s1, s11, s2\n"
        "vldmia r2, {s6, s7}\n"
        "vldr s10, [r0, #0x11c]\n"
        "add r0, r0, #0x108\n"
        "vmul.f32 s5, s6, s2\n"
        "vmul.f32 s0, s7, s9\n"
        "vmul.f32 s4, s6, s3\n"
        "vmls.f32 s1, s6, s9\n"
        "vmla.f32 s5, s7, s3\n"
        "vmls.f32 s0, s11, s3\n"
        "vmls.f32 s4, s7, s2\n"
        "vmla.f32 s1, s3, s8\n"
        "vmla.f32 s5, s11, s9\n"
        "vmla.f32 s0, s2, s8\n"
        "vmla.f32 s4, s9, s8\n"
        "vmla.f32 s1, s7, s10\n"
        "vnmls.f32 s5, s8, s10\n"
        "vmla.f32 s0, s6, s10\n"
        "vmla.f32 s4, s11, s10\n"
        "vstmia r1, {s0, s1}\n"
        "vstmia r0, {s4, s5}\n"
        "bx lr\n"
        ".word 0x004ea81c\n"
    );
}

// DECOMP_FUNC(0x0023ebf0, 28)
extern "C" __attribute__((naked)) void camp_func_0023ebf0() {
    asm volatile(
        "push {r4, lr}\n"
        "bl camp_func_00297688\n"
        "ldr r1, [pc, #8]\n"
        "add r0, r0, r0, lsl #3\n"
        "add r0, r1, r0, lsl #2\n"
        "pop {r4, pc}\n"
        ".word 0x00439ae8\n"
    );
}

// DECOMP_FUNC(0x00262648, 28)
extern "C" __attribute__((naked)) void script_vm_func_00262648() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl script_vm_func_002b66ec\n"
        "ldrh r1, [r0, #0x72]\n"
        "bic r1, r1, r4\n"
        "strh r1, [r0, #0x72]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002fff04, 28)
extern "C" __attribute__((naked)) void func_002fff04() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "push {r4, lr}\n"
        "ldr r0, [r0]\n"
        "bl func_003dc244\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x00435d18\n"
    );
}

// DECOMP_FUNC(0x0021ebe0, 32)
extern "C" __attribute__((naked)) void ui_func_0021ebe0() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0ac8\n"
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #8]\n"
        "cmp r0, #0\n"
        "movne r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x00434388\n"
    );
}

// DECOMP_FUNC(0x002543d8, 32)
extern "C" __attribute__((naked)) void script_vm_func_002543d8() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002adf14\n"
        "add r0, r0, r4, lsl #2\n"
        "ldrb r1, [r0, #0x200]\n"
        "bic r1, r1, #0x60\n"
        "strb r1, [r0, #0x200]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00258020, 32)
extern "C" __attribute__((naked)) void script_vm_func_00258020() {
    asm volatile(
        "mov r2, r1\n"
        "mov r1, r0\n"
        "push {r3, lr}\n"
        "mov r0, sp\n"
        "bl camp_func_0022e4e8\n"
        "ldrh r0, [sp]\n"
        "bic r0, r0, #0xfc00\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x0027f150, 32)
extern "C" __attribute__((naked)) void script_vm_func_0027f150() {
    asm volatile(
        "str lr, [sp, #-4]!\n"
        "bl script_vm_func_00287d74\n"
        "vldr s1, [pc, #0xc]\n"
        "vcmpe.f32 s0, s1\n"
        "vmrs apsr_nzcv, fpscr\n"
        "vneglo.f32 s0, s0\n"
        "pop {pc}\n"
        ".word 0x00000000\n"
    );
}

// DECOMP_FUNC(0x002cd824, 32)
extern "C" __attribute__((naked)) void func_002cd824() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r4, [pc, #0x10]\n"
        "ldr r0, [r4]\n"
        "bl func_00291950\n"
        "mov r0, #0\n"
        "str r0, [r4]\n"
        "pop {r4, pc}\n"
        ".word 0x00433a58\n"
    );
}

// DECOMP_FUNC(0x002e3664, 32)
extern "C" __attribute__((naked)) void engine_func_002e3664() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r4, [pc, #0x10]\n"
        "ldr r0, [r4]\n"
        "bl engine_func_002c4360\n"
        "mov r0, #0\n"
        "str r0, [r4]\n"
        "pop {r4, pc}\n"
        ".word 0x0043ded0\n"
    );
}

// DECOMP_FUNC(0x002efec8, 32)
extern "C" __attribute__((naked)) void engine_func_002efec8() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "ldr r1, [pc, #8]\n"
        "str r0, [r1, #4]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x00432ce0\n"
    );
}

// DECOMP_FUNC(0x002f7664, 32)
extern "C" __attribute__((naked)) void script_vm_func_002f7664() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "push {r4, lr}\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_00247084\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x00435d18\n"
    );
}

// DECOMP_FUNC(0x002f7928, 32)
extern "C" __attribute__((naked)) void battle_func_002f7928() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "push {r4, lr}\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #0x30]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x00439b58\n"
    );
}

// DECOMP_FUNC(0x00224d24, 36)
extern "C" __attribute__((naked)) void func_00224d24() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "push {r4, lr}\n"
        "mov r2, #0\n"
        "mov r1, #1\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0024c828\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002cfb80, 36)
extern "C" __attribute__((naked)) void func_002cfb80() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "push {r4, lr}\n"
        "mov r2, #0\n"
        "mov r1, #2\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0024c828\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002dbee0, 36)
extern "C" __attribute__((naked)) void func_002dbee0() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "push {r4, lr}\n"
        "mov r2, #0\n"
        "mov r1, #0xf\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0024c828\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002dbf04, 36)
extern "C" __attribute__((naked)) void func_002dbf04() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "push {r4, lr}\n"
        "mov r2, #0\n"
        "mov r1, #0x10\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0024c828\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002e3efc, 36)
extern "C" __attribute__((naked)) void func_002e3efc() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "push {r4, lr}\n"
        "mov r2, #0\n"
        "mov r1, #0xb\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0024c828\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002e3f20, 36)
extern "C" __attribute__((naked)) void func_002e3f20() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "push {r4, lr}\n"
        "mov r2, #0\n"
        "mov r1, #4\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0024c828\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002e3f44, 36)
extern "C" __attribute__((naked)) void func_002e3f44() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "push {r4, lr}\n"
        "mov r2, #0\n"
        "mov r1, #3\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0024c828\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002e3f68, 36)
extern "C" __attribute__((naked)) void func_002e3f68() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "push {r4, lr}\n"
        "mov r2, #0\n"
        "mov r1, #6\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0024c828\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002e3f8c, 36)
extern "C" __attribute__((naked)) void func_002e3f8c() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "push {r4, lr}\n"
        "mov r2, #0\n"
        "mov r1, #5\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0024c828\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002ffe4c, 36)
extern "C" __attribute__((naked)) void func_002ffe4c() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "push {r4, lr}\n"
        "mov r2, #0\n"
        "mov r1, #0xc\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0024c828\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x00210be4, 40)
extern "C" __attribute__((naked)) void script_vm_func_00210be4() {
    asm volatile(
        "mov r1, r0\n"
        "ldr r0, [pc, #0x18]\n"
        "push {r4, lr}\n"
        "ldr r0, [r0, #4]\n"
        "ldr r0, [r0, #0x560]\n"
        "bl script_vm_func_002971e4\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043da28\n"
    );
}

// DECOMP_FUNC(0x00287ab4, 40)
extern "C" __attribute__((naked)) void engine_func_00287ab4() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r1\n"
        "mov r4, r0\n"
        "bl engine_func_002adf14\n"
        "add r0, r0, r4, lsl #2\n"
        "ldrb r1, [r0, #0x202]\n"
        "bic r1, r1, #2\n"
        "orr r1, r1, r5, lsl #1\n"
        "strb r1, [r0, #0x202]\n"
        "pop {r4, r5, r6, pc}\n"
    );
}
