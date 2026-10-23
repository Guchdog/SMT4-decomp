#include "types.h"

// Direct branch encodings are preserved to keep code-bin displacements unchanged.
// Bounded literal-pool/padding bytes after each return are emitted as data.

// DECOMP_FUNC(0x00100c44, 8)
extern "C" __attribute__((naked)) void crt_func_00100c44() {
    asm volatile(
        ".thumb\n"
        "push {r4, lr}\n"
        ".hword 0xf000 @ bl#0x10108c\n"
        ".hword 0xfa21 @ bl (continued)\n"
        "pop {r4, pc}\n"
        ".arm\n"
    );
}

// DECOMP_FUNC(0x0011c368, 12)
extern "C" __attribute__((naked)) void func_0011c368() {
    asm volatile(
        "ldr r0, [pc]\n"
        "bx lr\n"
        ".word 0x004e6c7c @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011c374, 12)
extern "C" __attribute__((naked)) void func_0011c374() {
    asm volatile(
        "ldr r0, [pc]\n"
        "bx lr\n"
        ".word 0x004e6c84 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011c5e0, 12)
extern "C" __attribute__((naked)) void func_0011c5e0() {
    asm volatile(
        "ldr r0, [pc]\n"
        "bx lr\n"
        ".word 0x004e6c74 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d300, 12)
extern "C" __attribute__((naked)) void func_0011d300() {
    asm volatile(
        "ldr r0, [pc]\n"
        "bx lr\n"
        ".word 0x004e529c @ tail data\n"
    );
}

// DECOMP_FUNC(0x0010f72c, 16)
extern "C" __attribute__((naked)) void func_0010f72c() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #8]\n"
        "bx lr\n"
        ".word 0x00471b48 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0010f878, 16)
extern "C" __attribute__((naked)) void func_0010f878() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #0x40]\n"
        "bx lr\n"
        ".word 0x1ff80000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011007c, 16)
extern "C" __attribute__((naked)) void func_0011007c() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011059c, 16)
extern "C" __attribute__((naked)) void func_0011059c() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrb r0, [r0, #5]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001174d4, 16)
extern "C" __attribute__((naked)) void func_001174d4() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1, #0x1e6]\n"
        "bx lr\n"
        ".word 0x004c5634 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011a0c8, 16)
extern "C" __attribute__((naked)) void engine_func_0011a0c8() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "ldr r0, [r1, r0, lsl #2]\n"
        "bx lr\n"
        ".word 0x00464c88 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011bab0, 16)
extern "C" __attribute__((naked)) void nn_sdk_func_0011bab0() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "str r0, [r1]\n"
        "bx lr\n"
        ".word 0x00471a68 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d0d4, 16)
extern "C" __attribute__((naked)) void func_0011d0d4() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "str r0, [r1, #0x18]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d11c, 16)
extern "C" __attribute__((naked)) void func_0011d11c() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrb r0, [r0, #0xa]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d1c0, 16)
extern "C" __attribute__((naked)) void func_0011d1c0() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrb r0, [r0, #0xb]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d1d0, 16)
extern "C" __attribute__((naked)) void func_0011d1d0() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #0xd]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d1e0, 16)
extern "C" __attribute__((naked)) void func_0011d1e0() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1, #0xd]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d270, 16)
extern "C" __attribute__((naked)) void func_0011d270() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "str r0, [r1, #0x14]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d2cc, 16)
extern "C" __attribute__((naked)) void func_0011d2cc() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "str r0, [r1]\n"
        "bx lr\n"
        ".word 0x00465668 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d2dc, 16)
extern "C" __attribute__((naked)) void func_0011d2dc() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "str r0, [r1, #8]\n"
        "bx lr\n"
        ".word 0x00465690 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d30c, 16)
extern "C" __attribute__((naked)) void func_0011d30c() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1, #1]\n"
        "bx lr\n"
        ".word 0x00465690 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d49c, 16)
extern "C" __attribute__((naked)) void func_0011d49c() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "str r0, [r1, #4]\n"
        "bx lr\n"
        ".word 0x00465690 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0012a654, 16)
extern "C" __attribute__((naked)) void func_0012a654() {
    asm volatile(
        "ldr r2, [pc, #4]\n"
        "strd r0, r1, [r2, #4]\n"
        "bx lr\n"
        ".word 0x00465630 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0012f4c0, 16)
extern "C" __attribute__((naked)) void engine_func_0012f4c0() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #1]\n"
        "bx lr\n"
        ".word 0x0044e908 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00138f34, 16)
extern "C" __attribute__((naked)) void func_00138f34() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrb r0, [r0, #3]\n"
        "bx lr\n"
        ".word 0x00473888 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013afb8, 16)
extern "C" __attribute__((naked)) void func_0013afb8() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #8]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013aff0, 16)
extern "C" __attribute__((naked)) void func_0013aff0() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #7]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013b19c, 16)
extern "C" __attribute__((naked)) void func_0013b19c() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrb r0, [r0, #3]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013b1ac, 16)
extern "C" __attribute__((naked)) void func_0013b1ac() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1, #4]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013b1bc, 16)
extern "C" __attribute__((naked)) void func_0013b1bc() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1, #3]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013b1ec, 16)
extern "C" __attribute__((naked)) void func_0013b1ec() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1, #2]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001456c0, 16)
extern "C" __attribute__((naked)) void func_001456c0() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "ldr r0, [r1, r0, lsl #2]\n"
        "bx lr\n"
        ".word 0x004e0b48 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001457a8, 16)
extern "C" __attribute__((naked)) void func_001457a8() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "ldr r0, [r1, r0, lsl #2]\n"
        "bx lr\n"
        ".word 0x004e0c48 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00147ce8, 16)
extern "C" __attribute__((naked)) void func_00147ce8() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #2]\n"
        "bx lr\n"
        ".word 0x00471a70 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0014f994, 16)
extern "C" __attribute__((naked)) void func_0014f994() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #0x32c]\n"
        "bx lr\n"
        ".word 0x004e7f64 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00152790, 16)
extern "C" __attribute__((naked)) void script_vm_func_00152790() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "ldr r0, [r1, r0, lsl #2]\n"
        "bx lr\n"
        ".word 0x00464bb4 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0015e7f8, 16)
extern "C" __attribute__((naked)) void func_0015e7f8() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #4]\n"
        "bx lr\n"
        ".word 0x0044e7c0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00193b44, 16)
extern "C" __attribute__((naked)) void camp_func_00193b44() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #3]\n"
        "bx lr\n"
        ".word 0x0043e310 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00193b54, 16)
extern "C" __attribute__((naked)) void func_00193b54() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #2]\n"
        "bx lr\n"
        ".word 0x0043e310 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001a15a0, 16)
extern "C" __attribute__((naked)) void script_vm_func_001a15a0() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1]\n"
        "bx lr\n"
        ".word 0x0044db88 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001a1e6c, 16)
extern "C" __attribute__((naked)) void camp_func_001a1e6c() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1, #3]\n"
        "bx lr\n"
        ".word 0x0043e310 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ab8c8, 16)
extern "C" __attribute__((naked)) void func_001ab8c8() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0]\n"
        "bx lr\n"
        ".word 0x00433278 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001db7f4, 16)
extern "C" __attribute__((naked)) void func_001db7f4() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #0x10]\n"
        "bx lr\n"
        ".word 0x004651e8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00100238, 20)
extern "C" __attribute__((naked)) void crt_func_00100238() {
    asm volatile(
        ".thumb\n"
        "movs r2, r1\n"
        "movs r1, r0\n"
        "push {r4, lr}\n"
        "ldr r0, [pc, #8]\n"
        ".hword 0xf1c6 @ bl#0x2c6af2\n"
        ".hword 0xfc57 @ bl (continued)\n"
        "pop {r4, pc}\n"
        ".hword 0x0000 @ tail data\n"
        ".hword 0xfcb4 @ tail data\n"
        ".hword 0x004e @ tail data\n"
        ".arm\n"
    );
}

// DECOMP_FUNC(0x0010fa60, 20)
extern "C" __attribute__((naked)) void func_0010fa60() {
    asm volatile(
        "mrc p15, #0, r0, c13, c0, #3\n"
        "ldr r1, [pc, #4]\n"
        "str r0, [r1, #4]\n"
        "bx lr\n"
        ".word 0x0044e7ac @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011001c, 20)
extern "C" __attribute__((naked)) void func_0011001c() {
    asm volatile(
        "ldr r2, [pc, #8]\n"
        "str r0, [r2, #0x2c]!\n"
        "str r1, [r2, #0x40]\n"
        "bx lr\n"
        ".word 0x0044e3b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00110030, 20)
extern "C" __attribute__((naked)) void func_00110030() {
    asm volatile(
        "ldr r2, [pc, #8]\n"
        "str r0, [r2, #0x20]!\n"
        "str r1, [r2, #0x40]\n"
        "bx lr\n"
        ".word 0x0044e3b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d00c, 20)
extern "C" __attribute__((naked)) void func_0011d00c() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "mov r0, #1\n"
        "strb r0, [r1, #1]\n"
        "bx lr\n"
        ".word 0x00471a70 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011d2ec, 20)
extern "C" __attribute__((naked)) void func_0011d2ec() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "mov r0, #1\n"
        "strb r0, [r1]\n"
        "bx lr\n"
        ".word 0x00465690 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00129cbc, 20)
extern "C" __attribute__((naked)) void battle_func_00129cbc() {
    asm volatile(
        "mov r0, r0\n"
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #0xc]\n"
        "bx lr\n"
        ".word 0x00471a70 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0012a28c, 20)
extern "C" __attribute__((naked)) void func_0012a28c() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "mov r0, #1\n"
        "strb r0, [r1, #9]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013afa4, 20)
extern "C" __attribute__((naked)) void func_0013afa4() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "mov r0, #1\n"
        "strb r0, [r1, #8]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013afc8, 20)
extern "C" __attribute__((naked)) void func_0013afc8() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "mov r0, #0\n"
        "strb r0, [r1, #8]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013afdc, 20)
extern "C" __attribute__((naked)) void func_0013afdc() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "mov r0, #1\n"
        "strb r0, [r1, #7]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013b000, 20)
extern "C" __attribute__((naked)) void func_0013b000() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "mov r0, #0\n"
        "strb r0, [r1, #7]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013b1cc, 20)
extern "C" __attribute__((naked)) void func_0013b1cc() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "mov r0, #0\n"
        "strb r0, [r1, #3]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0013b1fc, 20)
extern "C" __attribute__((naked)) void func_0013b1fc() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "mov r0, #0\n"
        "strb r0, [r1, #2]\n"
        "bx lr\n"
        ".word 0x0044e380 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00145774, 20)
extern "C" __attribute__((naked)) void func_00145774() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0, #4]\n"
        "ldr r0, [r0, #0x84]\n"
        "bx lr\n"
        ".word 0x0044ea58 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00158524, 20)
extern "C" __attribute__((naked)) void func_00158524() {
    asm volatile(
        "ldr r2, [pc, #8]\n"
        "add r0, r2, r0, lsl #1\n"
        "strh r1, [r0]\n"
        "bx lr\n"
        ".word 0x004ea494 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0015eef8, 20)
extern "C" __attribute__((naked)) void func_0015eef8() {
    asm volatile(
        "ldrb r1, [r0, #0xd]\n"
        "cmp r1, #0\n"
        ".inst 0x1a000000 @ bne #0x15ef08\n"
        ".inst 0xea00006b @ b #0x15f0b8\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0018af58, 20)
extern "C" __attribute__((naked)) void engine_func_0018af58() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "mov r0, #1\n"
        "strb r0, [r1]\n"
        "bx lr\n"
        ".word 0x00446fd0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0018bfd8, 20)
extern "C" __attribute__((naked)) void func_0018bfd8() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0, #0xc]\n"
        "ldrh r0, [r0]\n"
        "bx lr\n"
        ".word 0x0043e2a8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001921e4, 20)
extern "C" __attribute__((naked)) void func_001921e4() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #0x18]\n"
        "bx lr\n"
        ".word 0x0044e050 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001e18ec, 20)
extern "C" __attribute__((naked)) void func_001e18ec() {
    asm volatile(
        "ldr r0, [r0, #0x4c]\n"
        "cmp r0, #0\n"
        ".inst 0x0a000000 @ beq #0x1e18fc\n"
        ".inst 0xeafffff1 @ b #0x1e18c4\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x001fb434, 20)
extern "C" __attribute__((naked)) void script_vm_func_001fb434() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0]\n"
        "ldrsb r0, [r0, #9]\n"
        "bx lr\n"
        ".word 0x00448c20 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00113104, 24)
extern "C" __attribute__((naked)) void battle_func_00113104() {
    asm volatile(
        "ldr r3, [pc, #0xc]\n"
        "str r2, [r3, #0x170]!\n"
        "add r3, r3, #8\n"
        "stm r3, {r0, r1}\n"
        "bx lr\n"
        ".word 0x004c6290 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00121d58, 24)
extern "C" __attribute__((naked)) void ui_func_00121d58() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb003daf @ bl #0x131420\n"
        "ldr r1, [pc, #4]\n"
        "str r1, [r0]\n"
        "pop {r4, pc}\n"
        ".word 0x00421d58 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0012342c, 24)
extern "C" __attribute__((naked)) void func_0012342c() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldr r1, [r1, #0x9c]\n"
        "cmp r1, #0\n"
        "strne r0, [r1, #0x38]\n"
        "bx lr\n"
        ".word 0x004c6290 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00129c58, 24)
extern "C" __attribute__((naked)) void battle_func_00129c58() {
    asm volatile(
        "mov r0, r0\n"
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0, #0x1c]\n"
        "ldrsb r0, [r0, #0x75]\n"
        "bx lr\n"
        ".word 0x00471a70 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00152d64, 24)
extern "C" __attribute__((naked)) void script_vm_func_00152d64() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldr r2, [r1, r0, lsl #2]\n"
        "bic r2, r2, #1\n"
        "str r2, [r1, r0, lsl #2]\n"
        "bx lr\n"
        ".word 0x00464b74 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00158350, 24)
extern "C" __attribute__((naked)) void func_00158350() {
    asm volatile(
        "ldr r2, [pc, #0xc]\n"
        "push {r4, lr}\n"
        "ldrd r2, r3, [r2, #0x20]\n"
        ".inst 0xeb052776 @ bl #0x2a213c\n"
        "pop {r4, pc}\n"
        ".word 0x0040b7b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001583ec, 24)
extern "C" __attribute__((naked)) void func_001583ec() {
    asm volatile(
        "ldr r2, [pc, #0xc]\n"
        "push {r4, lr}\n"
        "ldrd r2, r3, [r2, #0x18]\n"
        ".inst 0xeb05274f @ bl #0x2a213c\n"
        "pop {r4, pc}\n"
        ".word 0x0040b7b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00158418, 24)
extern "C" __attribute__((naked)) void func_00158418() {
    asm volatile(
        "ldr r2, [pc, #0xc]\n"
        "push {r4, lr}\n"
        "ldrd r2, r3, [r2, #0x10]\n"
        ".inst 0xeb052744 @ bl #0x2a213c\n"
        "pop {r4, pc}\n"
        ".word 0x0040b7b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00158430, 24)
extern "C" __attribute__((naked)) void func_00158430() {
    asm volatile(
        "ldr r2, [pc, #0xc]\n"
        "push {r4, lr}\n"
        "ldrd r2, r3, [r2, #0x30]\n"
        ".inst 0xeb05273e @ bl #0x2a213c\n"
        "pop {r4, pc}\n"
        ".word 0x0040b7b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001584dc, 24)
extern "C" __attribute__((naked)) void func_001584dc() {
    asm volatile(
        "ldr r2, [pc, #0xc]\n"
        "push {r4, lr}\n"
        "ldrd r2, r3, [r2, #0x48]\n"
        ".inst 0xeb052713 @ bl #0x2a213c\n"
        "pop {r4, pc}\n"
        ".word 0x0040b7b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001584f4, 24)
extern "C" __attribute__((naked)) void func_001584f4() {
    asm volatile(
        "ldr r2, [pc, #0xc]\n"
        "push {r4, lr}\n"
        "ldrd r2, r3, [r2, #0x50]\n"
        ".inst 0xeb05270d @ bl #0x2a213c\n"
        "pop {r4, pc}\n"
        ".word 0x0040b7b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0015850c, 24)
extern "C" __attribute__((naked)) void func_0015850c() {
    asm volatile(
        "ldr r2, [pc, #0xc]\n"
        "push {r4, lr}\n"
        "ldrd r2, r3, [r2, #0x40]\n"
        ".inst 0xeb052707 @ bl #0x2a213c\n"
        "pop {r4, pc}\n"
        ".word 0x0040b7b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00158658, 24)
extern "C" __attribute__((naked)) void func_00158658() {
    asm volatile(
        "ldr r2, [pc, #0xc]\n"
        "push {r4, lr}\n"
        "ldrd r2, r3, [r2, #0x28]\n"
        ".inst 0xeb0526b4 @ bl #0x2a213c\n"
        "pop {r4, pc}\n"
        ".word 0x0040b7b0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ad8d4, 24)
extern "C" __attribute__((naked)) void script_vm_func_001ad8d4() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldr r1, [r1, #4]\n"
        "cmp r1, #0\n"
        "strbne r0, [r1, #0x10]\n"
        "bx lr\n"
        ".word 0x0043dd38 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001b0ae8, 24)
extern "C" __attribute__((naked)) void ui_func_001b0ae8() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bx lr\n"
        ".word 0x00432fe0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001c34e8, 24)
extern "C" __attribute__((naked)) void func_001c34e8() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1c000\n"
        "add r0, r0, #0x2b80\n"
        "bx lr\n"
        ".word 0x0043e2a8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001c3588, 24)
extern "C" __attribute__((naked)) void script_vm_func_001c3588() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "ldr r0, [r0, #0x660]\n"
        "sxth r0, r0\n"
        "bx lr\n"
        ".word 0x0043dcb0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001c35a0, 24)
extern "C" __attribute__((naked)) void func_001c35a0() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0, #4]\n"
        "ldr r0, [r0, #0x664]\n"
        "sxth r0, r0\n"
        "bx lr\n"
        ".word 0x0043dcb0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001db538, 24)
extern "C" __attribute__((naked)) void script_vm_func_001db538() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldr r2, [r1, r0, lsl #2]\n"
        "orr r2, r2, #1\n"
        "str r2, [r1, r0, lsl #2]\n"
        "bx lr\n"
        ".word 0x00464b74 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001e2860, 24)
extern "C" __attribute__((naked)) void func_001e2860() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb01e68a @ bl #0x25c294\n"
        "ldr r1, [pc, #4]\n"
        "ldrb r0, [r1, r0]\n"
        "pop {r4, pc}\n"
        ".word 0x00447620 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ea7f0, 24)
extern "C" __attribute__((naked)) void script_vm_func_001ea7f0() {
    asm volatile(
        "cmp r0, #0xb\n"
        "ldrlo r1, [pc, #8]\n"
        "ldrblo r0, [r1, r0]\n"
        "movhs r0, #0x50\n"
        "bx lr\n"
        ".word 0x004077f6 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ed164, 24)
extern "C" __attribute__((naked)) void func_001ed164() {
    asm volatile(
        "add r1, r0, r0, lsl #3\n"
        "add r0, r1, r0, lsl #5\n"
        "ldr r1, [pc, #4]\n"
        "add r0, r1, r0, lsl #3\n"
        "bx lr\n"
        ".word 0x00478000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001f2f40, 24)
extern "C" __attribute__((naked)) void camp_func_001f2f40() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "ldrbne r0, [r0, #0x420]\n"
        "bx lr\n"
        ".word 0x0043dd68 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001fe3b8, 24)
extern "C" __attribute__((naked)) void script_vm_func_001fe3b8() {
    asm volatile(
        "cmp r0, #0xb\n"
        "ldrlo r1, [pc, #8]\n"
        "ldrblo r0, [r1, r0]\n"
        "movhs r0, #0x32\n"
        "bx lr\n"
        ".word 0x004077eb @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ffadc, 24)
extern "C" __attribute__((naked)) void camp_func_001ffadc() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bx lr\n"
        ".word 0x0043dad0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00111f04, 28)
extern "C" __attribute__((naked)) void func_00111f04() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r1, [r0]\n"
        "cmp r1, #0\n"
        "movne r1, #0\n"
        "strne r1, [r0]\n"
        "bx lr\n"
        ".word 0x004655c0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x0011239c, 28)
extern "C" __attribute__((naked)) void func_0011239c() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r1, [r0]\n"
        "cmp r1, #0\n"
        "movne r1, #0\n"
        "strne r1, [r0]\n"
        "bx lr\n"
        ".word 0x0044e32c @ tail data\n"
    );
}

// DECOMP_FUNC(0x001182c0, 28)
extern "C" __attribute__((naked)) void ui_func_001182c0() {
    asm volatile(
        "str r1, [r0, #0x50]\n"
        "bic r1, r2, #0xff\n"
        "ldr r2, [pc, #8]\n"
        "str r1, [r2, #0xc]\n"
        "vstr s0, [r0, #0x58]\n"
        "bx lr\n"
        ".word 0x00464d48 @ tail data\n"
    );
}

// DECOMP_FUNC(0x00139230, 28)
extern "C" __attribute__((naked)) void func_00139230() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xebffbea0 @ bl #0x128cbc\n"
        "lsrs r0, r0, #0x1f\n"
        ".inst 0x0a000001 @ beq #0x139248\n"
        "pop {r4, lr}\n"
        ".inst 0xea060eff @ b #0x2bce48\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0013af88, 28)
extern "C" __attribute__((naked)) void battle_func_0013af88() {
    asm volatile(
        "mov r0, r0\n"
        "ldr r0, [pc]\n"
        ".inst 0xea0622a3 @ b #0x2c3a24\n"
        "subeq r6, lr, ip, asr ip\n"
        "mov r1, #0\n"
        "str r1, [r0]\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x00195408, 28)
extern "C" __attribute__((naked)) void script_vm_func_00195408() {
    asm volatile(
        "ldr r1, [pc, #0x10]\n"
        "ldr r1, [r1, #4]\n"
        "add r1, r1, #0x24000\n"
        "add r1, r1, #0xbb0\n"
        "strb r0, [r1]\n"
        "bx lr\n"
        ".word 0x0043e2a8 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001ab8ac, 28)
extern "C" __attribute__((naked)) void func_001ab8ac() {
    asm volatile(
        "add r1, r0, r0, lsl #3\n"
        "add r0, r1, r0, lsl #5\n"
        "ldr r1, [pc, #8]\n"
        "add r0, r1, r0, lsl #3\n"
        "add r0, r0, #0xbc\n"
        "bx lr\n"
        ".word 0x00478000 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001c05f4, 28)
extern "C" __attribute__((naked)) void engine_func_001c05f4() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "movlt r0, #0\n"
        "movge r0, #1\n"
        "bx lr\n"
        ".word 0x00432ce0 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001db4e4, 28)
extern "C" __attribute__((naked)) void func_001db4e4() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        ".inst 0x0a000000 @ beq #0x1db4f8\n"
        ".inst 0xe12fff10 @ bx r0\n"
        "bx lr\n"
        ".word 0x00465108 @ tail data\n"
    );
}

// DECOMP_FUNC(0x001eca68, 28)
extern "C" __attribute__((naked)) void func_001eca68() {
    asm volatile(
        "ldr r1, [pc, #0x10]\n"
        "mov r2, #5\n"
        "ldr r1, [r1]\n"
        "str r2, [r1, #0x14]\n"
        "strh r0, [r1, #0x18]\n"
        "bx lr\n"
        ".word 0x0043e0f8 @ tail data\n"
    );
}
