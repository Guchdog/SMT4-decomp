#include "types.h"

// Direct branch encodings stay as raw ARM words to preserve their code-bin displacement.
// Literal-pool words after each terminal return are retained as data.

// DECOMP_FUNC(0x00102338, 52)
extern "C" __attribute__((naked)) void crt_func_00102338() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "ldr r4, [pc, #0x20]\n"
        "ldr r5, [pc, #0x20]\n"
        "cmp r4, r5\n"
        ".inst 0x2a000004 @ bhs #0x102360\n"
        "ldr r0, [r4]\n"
        ".inst 0xe12fff30 @ blx r0\n"
        "add r4, r4, #4\n"
        "cmp r4, r5\n"
        ".inst 0x3afffffa @ blo #0x10234c\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x0042ab78 @ literal/data\n"
        ".word 0x0042ab78 @ literal/data\n"
    );
}
// DECOMP_FUNC(0x0010236c, 84)
extern "C" __attribute__((naked)) void crt_func_0010236c() {
    asm volatile(
        "ldr r1, [pc, #0x44]\n"
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "mov r0, r0\n"
        "ldr r1, [pc, #0x38]\n"
        "mov r0, #0\n"
        "mov r0, r0\n"
        ".inst 0xeb071219 @ bl #0x2c6bf4\n"
        "mov r4, r0\n"
        "mov r1, #0\n"
        "mov r0, r1\n"
        ".inst 0xeb00d79a @ bl #0x138208\n"
        "add r0, r0, #1\n"
        "mov r1, #0\n"
        "str r0, [r4, #4]\n"
        "mov r0, r1\n"
        ".inst 0xeb012d55 @ bl #0x14d908\n"
        "str r0, [r4, #0xc]\n"
        "pop {r4, pc}\n"
        ".word 0x04000000 @ literal/data\n"
        ".word 0x04000026 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x001023e0, 88)
extern "C" __attribute__((naked)) void crt_func_001023e0() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        ".inst 0xeb003723 @ bl #0x11007c\n"
        "cmp r0, #0\n"
        ".inst 0x1a00000c @ bne #0x102428\n"
        "ldr r1, [pc, #0x34]\n"
        "mov r0, #1\n"
        "bic r4, r4, #7\n"
        "strb r0, [r1, #3]\n"
        "ldr r0, [pc, #0x28]\n"
        "mov r1, #0x100\n"
        ".inst 0xeb009c25 @ bl #0x1294a8\n"
        "mov r2, #0xf\n"
        "mov r1, r4\n"
        "mov r0, #0x300\n"
        ".inst 0xeb00378d @ bl #0x110258\n"
        "ands r1, r0, #0x80000000\n"
        ".inst 0x4a000000 @ bmi #0x10242c\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x0044e360 @ literal/data\n"
        ".word 0x004c641c @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00102634, 68)
extern "C" __attribute__((naked)) void engine_func_00102634() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r4, [pc, #0x34]\n"
        "ldrb r0, [r4]\n"
        "cmp r0, #0\n"
        ".inst 0x1a000008 @ bne #0x10266c\n"
        ".inst 0xeb070b6f @ bl #0x2c540c\n"
        "cmp r0, #1\n"
        ".inst 0x1a000005 @ bne #0x10266c\n"
        "ldrb r0, [r4, #1]\n"
        "cmp r0, #0\n"
        ".inst 0x0a000002 @ beq #0x10266c\n"
        "ldr r0, [r4, #8]\n"
        "mov r1, #1\n"
        ".inst 0xeb070b20 @ bl #0x2c52f0\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x00446db0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00102678, 76)
extern "C" __attribute__((naked)) void engine_func_00102678() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r4, [pc, #0x3c]\n"
        "ldrb r0, [r4]\n"
        "cmp r0, #0\n"
        ".inst 0x1a000008 @ bne #0x1026b0\n"
        ".inst 0xeb070b5e @ bl #0x2c540c\n"
        "cmp r0, #1\n"
        ".inst 0x1a000005 @ bne #0x1026b0\n"
        "ldrb r0, [r4, #1]\n"
        "cmp r0, #0\n"
        ".inst 0x0a000002 @ beq #0x1026b0\n"
        "ldr r0, [r4, #0xc]\n"
        "mov r1, #1\n"
        ".inst 0xeb070b0f @ bl #0x2c52f0\n"
        "mov r0, #0x400\n"
        ".inst 0xeb070adc @ bl #0x2c522c\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x00446db0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x001026c4, 96)
extern "C" __attribute__((naked)) void ui_func_001026c4() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb070ad2 @ bl #0x2c5218\n"
        "cmp r0, #0\n"
        ".inst 0x0a000004 @ beq #0x1026e8\n"
        ".inst 0xeb070acf @ bl #0x2c5218\n"
        "mov r1, r0\n"
        "ldr r0, [pc, #0x38]\n"
        "ldr r0, [r0]\n"
        ".inst 0xeb070aa7 @ bl #0x2c5188\n"
        "ldr r4, [pc, #0x30]\n"
        "ldrb r0, [r4]\n"
        "cmp r0, #0\n"
        ".inst 0x1a000006 @ bne #0x102714\n"
        "ldrb r0, [r4, #1]\n"
        "cmp r0, #0\n"
        ".inst 0x0a000003 @ beq #0x102714\n"
        ".inst 0xeb070b40 @ bl #0x2c540c\n"
        "cmp r0, #1\n"
        "ldreq r0, [r4, #8]\n"
        ".inst 0x0b070a6e @ bleq #0x2c50d0\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x0044ea00 @ literal/data\n"
        ".word 0x00446db0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00102724, 60)
extern "C" __attribute__((naked)) void engine_func_00102724() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r4, [pc, #0x2c]\n"
        "ldrb r0, [r4]\n"
        "cmp r0, #0\n"
        ".inst 0x1a000006 @ bne #0x102754\n"
        ".inst 0xeb070b33 @ bl #0x2c540c\n"
        "cmp r0, #1\n"
        ".inst 0x1a000003 @ bne #0x102754\n"
        "ldrb r0, [r4, #1]\n"
        "cmp r0, #0\n"
        "ldrne r0, [r4, #0xc]\n"
        ".inst 0x1b070a5e @ blne #0x2c50d0\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x00446db0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00102760, 96)
extern "C" __attribute__((naked)) void ui_func_00102760() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb070b28 @ bl #0x2c540c\n"
        "cmp r0, #1\n"
        ".inst 0x1a00000f @ bne #0x1027b0\n"
        "ldr r4, [pc, #0x40]\n"
        "ldrb r0, [r4, #1]\n"
        "cmp r0, #0\n"
        ".inst 0x0a00000b @ beq #0x1027b0\n"
        ".inst 0xeb070aa4 @ bl #0x2c5218\n"
        "cmp r0, #0\n"
        ".inst 0x0a000004 @ beq #0x1027a0\n"
        ".inst 0xeb070aa1 @ bl #0x2c5218\n"
        "mov r1, r0\n"
        "ldr r0, [pc, #0x20]\n"
        "ldr r0, [r0]\n"
        ".inst 0xeb070a79 @ bl #0x2c5188\n"
        "ldrb r0, [r4]\n"
        "cmp r0, #0\n"
        "ldreq r0, [r4, #8]\n"
        ".inst 0x0b070a38 @ bleq #0x2c5094\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x00446db0 @ literal/data\n"
        ".word 0x0044ea00 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x001027c0, 80)
extern "C" __attribute__((naked)) void func_001027c0() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r4, [pc, #0x40]\n"
        "ldrb r0, [r4]\n"
        "cmp r0, #0\n"
        ".inst 0x1a000006 @ bne #0x1027f0\n"
        ".inst 0xeb070b0c @ bl #0x2c540c\n"
        "cmp r0, #1\n"
        ".inst 0x1a000003 @ bne #0x1027f0\n"
        "ldrb r0, [r4, #1]\n"
        "cmp r0, #0\n"
        "ldrne r0, [r4, #0xc]\n"
        ".inst 0x1b070a28 @ blne #0x2c5094\n"
        "nop\n"
        ".inst 0xeb070b04 @ bl #0x2c540c\n"
        "cmp r0, #1\n"
        "moveq r0, #0x410\n"
        ".inst 0x0b070a89 @ bleq #0x2c522c\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x00446db0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00102810, 56)
extern "C" __attribute__((naked)) void func_00102810() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb070afc @ bl #0x2c540c\n"
        "cmp r0, #1\n"
        ".inst 0x1a000006 @ bne #0x10283c\n"
        "ldr r0, [pc, #0x1c]\n"
        "ldrb r1, [r0, #1]\n"
        "cmp r1, #0\n"
        ".inst 0x0a000002 @ beq #0x10283c\n"
        "ldrb r0, [r0]\n"
        "cmp r0, #0\n"
        ".inst 0x0b00248f @ bleq #0x10ba7c\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x00446db0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00103484, 68)
extern "C" __attribute__((naked)) void func_00103484() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r4, [pc, #0x30]\n"
        "add r0, r4, #0x184\n"
        ".inst 0xeb003982 @ bl #0x111aa0\n"
        "cmp r0, #0\n"
        ".inst 0x0a000002 @ beq #0x1034a8\n"
        ".inst 0xeb002abc @ bl #0x10df94\n"
        "add r0, r4, #0x184\n"
        ".inst 0xeb003519 @ bl #0x110910\n"
        "ldr r0, [pc, #0x14]\n"
        "ldrb r1, [r0, #0x15]\n"
        "cmp r1, #0\n"
        "movne r1, #1\n"
        "strbne r1, [r0, #0x16]\n"
        "pop {r4, pc}\n"
        ".word 0x004e1f68 @ literal/data\n"
        ".word 0x004e3154 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x001035d4, 12)
extern "C" __attribute__((naked)) void func_001035d4() {
    asm volatile(
        "ldr r0, [pc]\n"
        "bx lr\n"
        ".word 0x00464b40 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00103744, 16)
extern "C" __attribute__((naked)) void func_00103744() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0]\n"
        "bx lr\n"
        ".word 0x00446fd0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00103754, 12)
extern "C" __attribute__((naked)) void func_00103754() {
    asm volatile(
        "ldr r0, [pc]\n"
        "bx lr\n"
        ".word 0x00464b4c @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00103760, 12)
extern "C" __attribute__((naked)) void func_00103760() {
    asm volatile(
        "ldr r0, [pc]\n"
        "bx lr\n"
        ".word 0x00464b3c @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00103ba0, 104)
extern "C" __attribute__((naked)) void engine_func_00103ba0() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb070618 @ bl #0x2c540c\n"
        "cmp r0, #1\n"
        ".inst 0x1a000011 @ bne #0x103bf8\n"
        "ldr r0, [pc, #0x48]\n"
        "ldrb r0, [r0, #1]\n"
        "cmp r0, #0\n"
        ".inst 0x0a00000d @ beq #0x103bf8\n"
        "mov r0, #1\n"
        ".inst 0xeb06fefa @ bl #0x2c37b4\n"
        "ldr r4, [pc, #0x34]\n"
        "mov r1, #1\n"
        "ldr r0, [r4]\n"
        "str r1, [r0, #0x528]\n"
        ".inst 0xeb06e84f @ bl #0x2bdd1c\n"
        "mov r1, #0\n"
        "mov r0, #1\n"
        ".inst 0xeb06fed2 @ bl #0x2c3734\n"
        "ldr r0, [r4]\n"
        ".inst 0xeb070009 @ bl #0x2c3c18\n"
        "ldr r0, [r4]\n"
        ".inst 0xeb06ffeb @ bl #0x2c3ba8\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x00446db0 @ literal/data\n"
        ".word 0x0044ea00 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00103c20, 52)
extern "C" __attribute__((naked)) void script_vm_func_00103c20() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb06febe @ bl #0x2c3724\n"
        ".inst 0xeb0700f4 @ bl #0x2c4000\n"
        "mov r4, r0\n"
        ".inst 0xeb06feb7 @ bl #0x2c3714\n"
        "ands r0, r4, #0x80000000\n"
        ".inst 0x4a000002 @ bmi #0x103c48\n"
        "ldr r1, [pc, #0xc]\n"
        "mov r0, #0\n"
        "strb r0, [r1]\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
        ".word 0x00465228 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00103c70, 76)
extern "C" __attribute__((naked)) void func_00103c70() {
    asm volatile(
        "ldr r3, [pc, #0x3c]\n"
        "mov r0, #0\n"
        "vldr s0, [pc, #0x38]\n"
        "mov r2, r0\n"
        "mov ip, #0xff\n"
        "add r1, r0, r0, lsl #2\n"
        "add r0, r0, #1\n"
        "add r1, r3, r1, lsl #2\n"
        "and r0, r0, #0xff\n"
        "vstr s0, [r1]\n"
        "str r2, [r1, #4]\n"
        "str r2, [r1, #8]\n"
        "str ip, [r1, #0xc]\n"
        "cmp r0, #2\n"
        "strb r2, [r1, #0x10]\n"
        ".inst 0x3afffff4 @ blo #0x103c84\n"
        "bx lr\n"
        ".word 0x004d9758 @ literal/data\n"
        ".word 0x00000000 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00103cbc, 16)
extern "C" void func_00103cbc(u32 value) {
    *reinterpret_cast<volatile u32*>(0x004651c0) = value;
}

// DECOMP_FUNC(0x00103ccc, 68)
extern "C" __attribute__((naked)) void func_00103ccc() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "ldr r5, [pc, #0x34]\n"
        "ldrb r0, [r5]\n"
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        ".inst 0x0a000008 @ beq #0x103d08\n"
        ".inst 0xeb06fe4b @ bl #0x2c3618\n"
        ".inst 0xeb0700c4 @ bl #0x2c4000\n"
        "mov r4, r0\n"
        ".inst 0xeb06fe87 @ bl #0x2c3714\n"
        "and r0, r4, #0x80000000\n"
        "cmp r0, #0\n"
        "mov r0, #0\n"
        "strbge r0, [r5]\n"
        "movge r0, #1\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x00465210 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00103dd4, 16)
extern "C" __attribute__((naked)) void func_00103dd4() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0, #2]\n"
        "bx lr\n"
        ".word 0x0043e2a8 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00103de4, 16)
extern "C" __attribute__((naked)) void func_00103de4() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "str r0, [r1]\n"
        "bx lr\n"
        ".word 0x00435e48 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00103ef8, 28)
extern "C" __attribute__((naked)) void func_00103ef8() {
    asm volatile(
        "cmp r0, #0\n"
        ".inst 0x0a000002 @ beq #0x103f0c\n"
        "ldr r1, [pc, #8]\n"
        "str r0, [r1, #0x10]\n"
        "mov r0, #1\n"
        "bx lr\n"
        ".word 0x004650a0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00103f14, 92)
extern "C" __attribute__((naked)) void func_00103f14() {
    asm volatile(
        "ldr r0, [pc, #0x50]\n"
        "mov r2, #0\n"
        "ldr ip, [r0, #4]\n"
        "cmp ip, #0\n"
        ".inst 0xd12fff1e @ bxle lr\n"
        "str r4, [sp, #-4]!\n"
        "ldr r4, [r0]\n"
        "ldr r0, [r4, r2, lsl #3]\n"
        "cmp r0, #0\n"
        ".inst 0x0a000006 @ beq #0x103f58\n"
        "ldr r1, [r0, #0x1c]\n"
        "tst r1, #0x80000\n"
        "orrne r1, r1, #0x200000\n"
        "strne r1, [r0, #0x1c]\n"
        "ldr r0, [r0, #0x4c]\n"
        "cmp r0, #0\n"
        ".inst 0x1afffff8 @ bne #0x103f3c\n"
        "add r2, r2, #1\n"
        "cmp ip, r2\n"
        ".inst 0xcafffff2 @ bgt #0x103f30\n"
        "pop {r4}\n"
        "bx lr\n"
        ".word 0x004e3cf4 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00103f70, 28)
extern "C" __attribute__((naked)) void func_00103f70() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "mov r1, #0\n"
        "str r1, [r0]\n"
        "mov r1, #0x64\n"
        "str r1, [r0, #4]\n"
        "bx lr\n"
        ".word 0x00464ce8 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00103f8c, 36)
extern "C" __attribute__((naked)) void func_00103f8c() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "mov r2, #0\n"
        "ldr r1, [r0, #0x10]\n"
        "rsb r1, r1, #1\n"
        "str r1, [r0, #0x10]\n"
        "add r3, r0, r1, lsl #2\n"
        "str r2, [r3, #8]\n"
        "bx lr\n"
        ".word 0x004daec0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00103fb0, 72)
extern "C" __attribute__((naked)) void func_00103fb0() {
    asm volatile(
        "ldr r1, [pc, #0x3c]\n"
        "ldr r3, [pc, #0x38]\n"
        "ldr r2, [pc, #0x30]\n"
        "ldr r1, [r1, #4]\n"
        "ldr r3, [r3, #4]\n"
        "add r1, r1, #0x1f000\n"
        "add r1, r1, #0x4e0\n"
        "add ip, r3, #0x88\n"
        "ldr r3, [r1]\n"
        "add r1, ip, #0x1f400\n"
        "add r1, r1, #0x58\n"
        "add r0, r0, r3\n"
        "cmp r0, r2\n"
        "strhi r2, [r1]\n"
        "strls r0, [r1]\n"
        "bx lr\n"
        ".word 0x022550ff @ literal/data\n"
        ".word 0x0043e2a8 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00104184, 16)
extern "C" __attribute__((naked)) void func_00104184() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0]\n"
        "bx lr\n"
        ".word 0x00465210 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00104194, 16)
extern "C" __attribute__((naked)) void func_00104194() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0]\n"
        "bx lr\n"
        ".word 0x00465228 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x001041a4, 52)
extern "C" __attribute__((naked)) void func_001041a4() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb0028e8 @ bl #0x10e550\n"
        ".inst 0xeb06ff93 @ bl #0x2c4000\n"
        "mov r4, r0\n"
        ".inst 0xeb06fd56 @ bl #0x2c3714\n"
        "ands r0, r4, #0x80000000\n"
        ".inst 0x4a000002 @ bmi #0x1041cc\n"
        "ldr r1, [pc, #0xc]\n"
        "mov r0, #0\n"
        "strb r0, [r1]\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
        ".word 0x00465240 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010428c, 12)
extern "C" __attribute__((naked)) void func_0010428c() {
    asm volatile(
        "ldr r0, [pc]\n"
        "bx lr\n"
        ".word 0x00464b50 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00104298, 48)
extern "C" __attribute__((naked)) void func_00104298() {
    asm volatile(
        "ldr r0, [pc, #0x1c]\n"
        "vldr s0, [pc, #0x1c]\n"
        "ldr r1, [pc, #0x1c]\n"
        "vstr s0, [r0]\n"
        "vstr s0, [r0, #4]\n"
        "vstr s0, [r0, #8]\n"
        "vstr s0, [r0, #0xc]\n"
        "str r0, [r1]\n"
        "bx lr\n"
        ".word 0x004daed8 @ literal/data\n"
        ".word 0x3f800000 @ literal/data\n"
        ".word 0x00464c40 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00104db0, 28)
extern "C" __attribute__((naked)) void func_00104db0() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldrb r0, [r0, #4]\n"
        "cmp r0, #2\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x00464af0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00104dcc, 28)
extern "C" __attribute__((naked)) void func_00104dcc() {
    asm volatile(
        "cmp r0, #0\n"
        ".inst 0x0a000002 @ beq #0x104de0\n"
        "ldr r1, [pc, #8]\n"
        "str r0, [r1, #0xc]\n"
        "mov r0, #1\n"
        "bx lr\n"
        ".word 0x004650a0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00104de8, 16)
extern "C" __attribute__((naked)) void func_00104de8() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1]\n"
        "bx lr\n"
        ".word 0x004650e0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00105070, 16)
extern "C" __attribute__((naked)) void func_00105070() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0]\n"
        "bx lr\n"
        ".word 0x00465240 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00105194, 100)
extern "C" __attribute__((naked)) void engine_func_00105194() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, #0\n"
        ".inst 0xeb002bad @ bl #0x110058\n"
        "cmp r0, #0\n"
        ".inst 0x0a00000e @ beq #0x1051e4\n"
        "ldr r0, [pc, #0x3c]\n"
        "ldrb r0, [r0, #1]\n"
        "cmp r0, #0\n"
        ".inst 0x0a000007 @ beq #0x1051d8\n"
        "ldr r0, [pc, #0x30]\n"
        ".inst 0xeb00cf66 @ bl #0x138f5c\n"
        "ldr r0, [pc, #0x2c]\n"
        ".inst 0xeb06f902 @ bl #0x2c35d4\n"
        "cmp r0, #0\n"
        "moveq r4, #2\n"
        "movne r4, #3\n"
        ".inst 0xea000002 @ b #0x1051e4\n"
        "nop\n"
        ".inst 0xeb06ef3f @ bl #0x2c0ee0\n"
        "mov r4, #1\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
        ".word 0x00465198 @ literal/data\n"
        ".word 0x004651a4 @ literal/data\n"
        ".word 0x004e4138 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00105bac, 112)
extern "C" __attribute__((naked)) void func_00105bac() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb0014c4 @ bl #0x10aec8\n"
        "ldr r4, [pc, #0x58]\n"
        "mov r0, #0\n"
        "str r0, [r4, #0x1bc]\n"
        "ldr r0, [r4, #0x1cc]\n"
        "cmp r0, #0\n"
        ".inst 0xba000009 @ blt #0x105bf4\n"
        "add r2, r4, #0x1c8\n"
        "mvn r1, #0\n"
        "cmp r0, #0\n"
        "stm r2, {r0, r1}\n"
        "moveq r0, #0x700\n"
        ".inst 0x0a000002 @ beq #0x105bf0\n"
        "cmp r0, #1\n"
        "ldreq r0, [pc, #0x28]\n"
        ".inst 0x1a000000 @ bne #0x105bf4\n"
        ".inst 0xeb003531 @ bl #0x1130bc\n"
        "ldr r0, [pc, #0x18]\n"
        "ldrb r0, [r0, #0x1d0]\n"
        "cmp r0, #0\n"
        ".inst 0x1a000002 @ bne #0x105c10\n"
        ".inst 0xeb005d05 @ bl #0x11d020\n"
        "mov r0, #1\n"
        "strb r0, [r4, #0x1d0]\n"
        "pop {r4, pc}\n"
        ".word 0x004e39e0 @ literal/data\n"
        ".word 0x00000702 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00105c1c, 40)
extern "C" __attribute__((naked)) void func_00105c1c() {
    asm volatile(
        "ldr r0, [pc, #0x1c]\n"
        "mov r3, #0x32\n"
        "mov r1, #0x50\n"
        "mov r2, #0x30\n"
        "strb r3, [r0]\n"
        "strb r1, [r0, #1]\n"
        "strb r1, [r0, #2]\n"
        "strb r2, [r0, #3]\n"
        "bx lr\n"
        ".word 0x0044e0f8 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00105c44, 12)
extern "C" __attribute__((naked)) void func_00105c44() {
    asm volatile(
        "ldr r0, [pc]\n"
        "bx lr\n"
        ".word 0x00464b54 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00105da4, 16)
extern "C" __attribute__((naked)) void func_00105da4() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "vldr s0, [r0, #0x1c4]\n"
        "bx lr\n"
        ".word 0x004e39e0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00105db4, 24)
extern "C" __attribute__((naked)) void func_00105db4() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "add r0, r1, r0, lsl #4\n"
        "add r0, r0, #0x174\n"
        "vstmia r0, {s0, s1, s2, s3}\n"
        "bx lr\n"
        ".word 0x004e39e0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00105dcc, 16)
extern "C" __attribute__((naked)) void func_00105dcc() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1, #3]\n"
        "bx lr\n"
        ".word 0x00464af0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00105ddc, 24)
extern "C" __attribute__((naked)) void func_00105ddc() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldr r2, [r1, #0x1c8]\n"
        "cmp r2, r0\n"
        "strne r0, [r1, #0x1cc]\n"
        "bx lr\n"
        ".word 0x004e39e0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00105df4, 56)
extern "C" __attribute__((naked)) void func_00105df4() {
    asm volatile(
        "add r1, r0, #1\n"
        "vmov s0, r1\n"
        "vldr s1, [pc, #0x1c]\n"
        "vldr s2, [pc, #0x1c]\n"
        "ldr r1, [pc, #0x1c]\n"
        "vcvt.f32.s32 s3, s0\n"
        "vdiv.f32 s0, s1, s3\n"
        "vdiv.f32 s1, s2, s0\n"
        "vstr s1, [r1, #0x1c4]\n"
        "str r0, [r1, #0x1c0]\n"
        "bx lr\n"
        ".word 0x426f52f2 @ literal/data\n"
        ".word 0x49742400 @ literal/data\n"
        ".word 0x004e39e0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00105e2c, 16)
extern "C" __attribute__((naked)) void func_00105e2c() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1]\n"
        "bx lr\n"
        ".word 0x00465170 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00105e3c, 96)
extern "C" __attribute__((naked)) void func_00105e3c() {
    asm volatile(
        "ldr r2, [pc, #0x54]\n"
        "cmp r0, #0\n"
        "add r3, r2, #0\n"
        "ldr r3, [r3, #0xc0]\n"
        ".inst 0x0a00000a @ beq #0x105e7c\n"
        "add ip, r2, #0\n"
        "cmp r0, #1\n"
        "ldr ip, [ip, #0x138]\n"
        ".inst 0x0a000009 @ beq #0x105e88\n"
        "cmp r0, #2\n"
        ".inst 0x1a000006 @ bne #0x105e84\n"
        "cmp r3, #0x500\n"
        "strbne r1, [r2, #0x200]\n"
        "cmp ip, #0x500\n"
        ".inst 0x0a000002 @ beq #0x105e84\n"
        ".inst 0xea000004 @ b #0x105e90\n"
        "cmp r3, #0x500\n"
        "strbne r1, [r2, #0x200]\n"
        "bx lr\n"
        "cmp ip, #0x500\n"
        ".inst 0x0afffffc @ beq #0x105e84\n"
        "strb r1, [r2, #0x201]\n"
        "bx lr\n"
        ".word 0x004e39e0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00106130, 48)
extern "C" __attribute__((naked)) void ui_func_00106130() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb06fc37 @ bl #0x2c5218\n"
        "cmp r0, #0\n"
        ".inst 0x0a000004 @ beq #0x106154\n"
        ".inst 0xeb06fc34 @ bl #0x2c5218\n"
        "mov r1, r0\n"
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        ".inst 0xeb06fc0c @ bl #0x2c5188\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x0044ea00 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00106160, 48)
extern "C" __attribute__((naked)) void ui_func_00106160() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb06fc2b @ bl #0x2c5218\n"
        "cmp r0, #0\n"
        ".inst 0x0a000004 @ beq #0x106184\n"
        ".inst 0xeb06fc28 @ bl #0x2c5218\n"
        "mov r1, r0\n"
        "ldr r0, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        ".inst 0xeb06fc00 @ bl #0x2c5188\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x0044ea00 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00106ce4, 116)
extern "C" __attribute__((naked)) void engine_func_00106ce4() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r4, [pc, #0x5c]\n"
        "ldrb r0, [r4]\n"
        "cmp r0, #0\n"
        ".inst 0x1a000013 @ bne #0x106d48\n"
        ".inst 0xeb00222e @ bl #0x10f5b8\n"
        ".inst 0xeb06fcae @ bl #0x2c5fbc\n"
        ".inst 0xeb002217 @ bl #0x10f564\n"
        "lsrs r1, r0, #0x1f\n"
        ".inst 0x1a000009 @ bne #0x106d34\n"
        "ldr r1, [pc, #0x3c]\n"
        "ldr r0, [pc, #0x3c]\n"
        ".inst 0xeb002429 @ bl #0x10fdc0\n"
        "lsrs r1, r0, #0x1f\n"
        ".inst 0x1a000002 @ bne #0x106d2c\n"
        ".inst 0xeb002440 @ bl #0x10fe28\n"
        "lsrs r1, r0, #0x1f\n"
        "moveq r0, #0\n"
        "lsrs r1, r0, #0x1f\n"
        "moveq r0, #0\n"
        "mov r1, pc\n"
        "lsrs r2, r0, #0x1f\n"
        ".inst 0x1b06e9ec @ blne #0x2c14f4\n"
        "mov r0, #1\n"
        "strb r0, [r4]\n"
        "pop {r4, pc}\n"
        ".word 0x0044e598 @ literal/data\n"
        ".word 0x00407f6b @ literal/data\n"
        ".word 0x004719e8 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00106d78, 16)
extern "C" __attribute__((naked)) void func_00106d78() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1]\n"
        "bx lr\n"
        ".word 0x0044e7a8 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00106d88, 44)
extern "C" __attribute__((naked)) void func_00106d88() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r4, [pc, #0x1c]\n"
        "ldrb r0, [r4]\n"
        "cmp r0, #0\n"
        ".inst 0x1a000003 @ bne #0x106dac\n"
        ".inst 0xeb002364 @ bl #0x10fb34\n"
        ".inst 0xeb0084bc @ bl #0x128098\n"
        "mov r0, #1\n"
        "strb r0, [r4]\n"
        "pop {r4, pc}\n"
        ".word 0x0044e7bc @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00106db4, 80)
extern "C" __attribute__((naked)) void engine_func_00106db4() {
    asm volatile(
        "ldr r0, [pc, #0x40]\n"
        "push {r4, lr}\n"
        "ldr r4, [r0, #4]\n"
        "ldr r0, [pc, #0x38]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        ".inst 0x1a000008 @ bne #0x106df4\n"
        "mov r0, r4\n"
        ".inst 0xeb06f12d @ bl #0x2c3290\n"
        "mov r2, r0\n"
        "ldr r0, [pc, #0x1c]\n"
        "mov r3, #0\n"
        "mov r1, r4\n"
        ".inst 0xeb06e9d3 @ bl #0x2c153c\n"
        "lsrs r1, r0, #0x1f\n"
        ".inst 0x1a000000 @ bne #0x106df8\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x004091bc @ literal/data\n"
        ".word 0x00471b64 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00107020, 48)
extern "C" __attribute__((naked)) void engine_func_00107020() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r4, [pc, #0x20]\n"
        "ldr r0, [r4]\n"
        "cmp r0, #0\n"
        ".inst 0x1a000004 @ bne #0x107048\n"
        "mov r0, #0x450\n"
        ".inst 0xeb06ecee @ bl #0x2c23f8\n"
        "cmp r0, #0\n"
        ".inst 0x1b002750 @ blne #0x110d88\n"
        "str r0, [r4]\n"
        "pop {r4, pc}\n"
        ".word 0x00433158 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00107144, 112)
extern "C" __attribute__((naked)) void engine_func_00107144() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "push {r4, lr}\n"
        ".inst 0xeb06eca9 @ bl #0x2c23f8\n"
        "cmp r0, #0\n"
        ".inst 0x1b0027cd @ blne #0x111090\n"
        "ldr r1, [pc, #8]\n"
        "str r0, [r1]\n"
        "pop {r4, pc}\n"
        "andeq r0, r0, r8, ror #26\n"
        "subeq r2, r3, r8, asr #31\n"
        "mov r1, #0x40\n"
        "str r1, [r0]\n"
        "str r1, [r0, #4]\n"
        "mov r3, #8\n"
        "mov r2, #4\n"
        "str r1, [r0, #8]\n"
        "strd r2, r3, [r0, #0xc]\n"
        "str r3, [r0, #0x14]\n"
        "str r2, [r0, #0x1c]\n"
        "str r3, [r0, #0x18]\n"
        "str r2, [r0, #0x20]\n"
        "str r1, [r0, #0x28]\n"
        "str r2, [r0, #0x24]\n"
        "mov ip, #0\n"
        "str r1, [r0, #0x30]\n"
        "str ip, [r0, #0x34]\n"
        "str ip, [r0, #0x38]\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x001071b4, 84)
extern "C" __attribute__((naked)) void camp_func_001071b4() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r1, #3\n"
        "mov r0, #2\n"
        ".inst 0xeb06e73f @ bl #0x2c0ec4\n"
        "mov r4, r0\n"
        ".inst 0xeb06e733 @ bl #0x2c0e9c\n"
        "mov r6, r0\n"
        "mov r0, r4\n"
        ".inst 0xeb06e71c @ bl #0x2c0e4c\n"
        "subs r5, r0, #0\n"
        "mov r4, #0\n"
        ".inst 0xda000007 @ ble #0x107204\n"
        "add r0, r6, r4, lsl #1\n"
        "mov r2, #0\n"
        "ldrb r1, [r0, #1]\n"
        "ldrb r0, [r0]\n"
        ".inst 0xeb06e69e @ bl #0x2c0c74\n"
        "add r4, r4, #1\n"
        "cmp r5, r4\n"
        ".inst 0xcafffff7 @ bgt #0x1071e4\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x001074dc, 96)
extern "C" __attribute__((naked)) void ui_func_001074dc() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        ".inst 0xeb06e5aa @ bl #0x2c0b94\n"
        "add r1, r0, #0x1ec00\n"
        "ldrh r2, [r1, #0x52]\n"
        "add r2, r2, r4\n"
        "uxth r2, r2\n"
        "cmp r2, #0x384\n"
        "movlo r0, #0\n"
        "strh r2, [r1, #0x52]\n"
        ".inst 0x3a00000b @ blo #0x107538\n"
        "add r0, r0, #0x1ec00\n"
        "sub r2, r2, #0x384\n"
        "add r0, r0, #0x51\n"
        "strh r2, [r1, #0x52]\n"
        "ldrb r1, [r0]\n"
        "add r1, r1, #1\n"
        "and r1, r1, #0xff\n"
        "cmp r1, #0x18\n"
        "strb r1, [r0]\n"
        "subhs r1, r1, #0x18\n"
        "strbhs r1, [r0]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001076a0, 56)
extern "C" __attribute__((naked)) void func_001076a0() {
    asm volatile(
        "ldr r0, [pc, #0x28]\n"
        "ldrb r1, [r0, #0x84]\n"
        "cmp r1, #0\n"
        ".inst 0x1a000005 @ bne #0x1076c8\n"
        "vldr s0, [r0, #0x80]\n"
        "vldr s1, [pc, #0x18]\n"
        "vcmpe.f32 s0, s1\n"
        "vmrs apsr_nzcv, fpscr\n"
        "movhi r0, #1\n"
        ".inst 0x8a000000 @ bhi #0x1076cc\n"
        "mov r0, #0\n"
        "bx lr\n"
        ".word 0x1ff81000 @ literal/data\n"
        ".word 0x00000000 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00107890, 72)
extern "C" __attribute__((naked)) void ui_func_00107890() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb06e48b @ bl #0x2c0ac8\n"
        "mov r4, r0\n"
        "ldr r0, [r0, #4]\n"
        ".inst 0xeb06e471 @ bl #0x2c0a6c\n"
        "ldr r0, [r4, #8]\n"
        ".inst 0xeb06e46f @ bl #0x2c0a6c\n"
        "ldr r0, [r4, #0xf20]\n"
        ".inst 0xeb06e46d @ bl #0x2c0a6c\n"
        "ldr r0, [r4, #0xf24]\n"
        ".inst 0xeb06e46b @ bl #0x2c0a6c\n"
        "mov r0, r4\n"
        ".inst 0xeb06f2a6 @ bl #0x2c4360\n"
        "ldr r1, [pc, #8]\n"
        "mov r0, #0\n"
        "str r0, [r1]\n"
        "pop {r4, pc}\n"
        ".word 0x0043e278 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00108018, 76)
extern "C" __attribute__((naked)) void script_vm_func_00108018() {
    asm volatile(
        "push {r4, lr}\n"
        "movs r4, r0\n"
        ".inst 0x0a000003 @ beq #0x108034\n"
        ".inst 0xeb004444 @ bl #0x11913c\n"
        "cmp r0, #0\n"
        ".inst 0x0a000005 @ beq #0x108048\n"
        ".inst 0xea000009 @ b #0x10805c\n"
        "nop\n"
        ".inst 0xeb06e03a @ bl #0x2c0128\n"
        "nop\n"
        "nop\n"
        ".inst 0xea000004 @ b #0x10805c\n"
        "mov r0, r4\n"
        ".inst 0xeb00437a @ bl #0x118e3c\n"
        "cmp r0, #0\n"
        "moveq r0, #2\n"
        ".inst 0x0b06e02c @ bleq #0x2c0110\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00108064, 108)
extern "C" __attribute__((naked)) void ui_func_00108064() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb06e296 @ bl #0x2c0ac8\n"
        "ldrb r2, [r0, #0xe8c]\n"
        "add r1, r0, #0xe00\n"
        "cmp r2, #0\n"
        "ldrbne r2, [r1, #0x8d]\n"
        "cmpne r2, #0\n"
        ".inst 0x0a000010 @ beq #0x1080c8\n"
        "ldrb r1, [r1, #0x95]\n"
        "cmp r1, #0\n"
        "ldrne r1, [r0, #0xfdc]\n"
        "cmpne r1, #0\n"
        ".inst 0x0a00000b @ beq #0x1080c8\n"
        "add r0, r0, #0xf00\n"
        "ldrb r1, [r0, #0xd8]\n"
        "cmp r1, #0\n"
        ".inst 0x1a000007 @ bne #0x1080c8\n"
        "ldrb r0, [r0, #0xe0]\n"
        "cmp r0, #0\n"
        "mov r0, #1\n"
        ".inst 0x0a000001 @ beq #0x1080c0\n"
        ".inst 0xeb00444a @ bl #0x1191e8\n"
        ".inst 0xea000001 @ b #0x1080c8\n"
        "nop\n"
        ".inst 0xeb003e29 @ bl #0x117970\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00108154, 108)
extern "C" __attribute__((naked)) void ui_func_00108154() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb06e25a @ bl #0x2c0ac8\n"
        "ldrb r2, [r0, #0xedc]\n"
        "add r1, r0, #0xe00\n"
        "cmp r2, #0\n"
        "ldrbne r2, [r1, #0xdd]\n"
        "cmpne r2, #0\n"
        ".inst 0x0a000007 @ beq #0x108194\n"
        "ldrb r1, [r1, #0xe5]\n"
        "cmp r1, #0\n"
        "ldrne r1, [r0, #0xfdc]\n"
        "cmpne r1, #0\n"
        ".inst 0x0a000002 @ beq #0x108194\n"
        "ldrb r0, [r0, #0xfd8]\n"
        "cmp r0, #0\n"
        ".inst 0x0a000001 @ beq #0x10819c\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0]\n"
        ".inst 0xeb06ee7f @ bl #0x2c3ba8\n"
        "mov r0, #1\n"
        "nop\n"
        ".inst 0xeb003ebb @ bl #0x117ca4\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x0044ea00 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00108244, 16)
extern "C" __attribute__((naked)) void func_00108244() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1]\n"
        "bx lr\n"
        ".word 0x0044e098 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00108254, 96)
extern "C" __attribute__((naked)) void ui_func_00108254() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r4, [pc, #0x48]\n"
        "ldr r0, [r4, #0x18]\n"
        "cmp r0, #0\n"
        ".inst 0x0a000009 @ beq #0x108290\n"
        "mov r0, #9\n"
        ".inst 0xeb06df52 @ bl #0x2bffbc\n"
        "cmp r0, #0\n"
        ".inst 0x0a000005 @ beq #0x108290\n"
        "ldr r0, [r4, #8]\n"
        "ldr r1, [r0, #0x24]\n"
        "cmp r1, #0x8800000\n"
        "moveq r1, #0x14000000\n"
        "movne r1, #0x8800000\n"
        "str r1, [r0, #0x24]\n"
        "ldr r2, [pc, #0x14]\n"
        "ldr r1, [pc, #0x14]\n"
        "mov r0, #0\n"
        ".inst 0xeb00364b @ bl #0x115bd0\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x00465120 @ literal/data\n"
        ".word 0x00116868 @ literal/data\n"
        ".word 0x00118b64 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x001082b4, 76)
extern "C" __attribute__((naked)) void script_vm_func_001082b4() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r0\n"
        "mov r6, r1\n"
        ".inst 0xeb06df39 @ bl #0x2bffac\n"
        "cmp r4, #1\n"
        "cmpne r4, #3\n"
        "mov r5, r0\n"
        "orreq r5, r0, #4\n"
        ".inst 0xeb06df30 @ bl #0x2bff9c\n"
        "vldr s0, [pc, #0x1c]\n"
        "mov r2, r0\n"
        "mov r3, r5\n"
        "vmov.f32 s1, s0\n"
        "mov r1, r6\n"
        "mov r0, r4\n"
        ".inst 0xeb06dec1 @ bl #0x2bfdfc\n"
        "mov r0, #1\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x3f34fdf4 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00108ab0, 96)
extern "C" __attribute__((naked)) void ui_func_00108ab0() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb06e003 @ bl #0x2c0ac8\n"
        "mov r4, r0\n"
        "add r0, r0, #0xf00\n"
        "ldrb r1, [r0, #0x28]\n"
        "cmp r1, #0\n"
        ".inst 0x0a00000a @ beq #0x108af8\n"
        "ldrb r0, [r0, #0x2b]\n"
        "cmp r0, #0\n"
        ".inst 0x0a000008 @ beq #0x108afc\n"
        "mov r0, #0\n"
        ".inst 0xeb06dd81 @ bl #0x2c00e8\n"
        "cmp r0, #0\n"
        ".inst 0x1a000003 @ bne #0x108af8\n"
        "ldrb r0, [r4, #0x1c]\n"
        "cmp r0, #0\n"
        "movne r0, #0\n"
        ".inst 0x1b002a07 @ blne #0x113318\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0xe59f1004 @ literal/data\n"
        ".word 0xe5c10001 @ literal/data\n"
        ".word 0xea0045cd @ literal/data\n"
        ".word 0x0044e0b0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x001092b0, 60)
extern "C" __attribute__((naked)) void func_001092b0() {
    asm volatile(
        "push {r3, r4, r5, lr}\n"
        "mov r4, r0\n"
        "mvn r0, #0\n"
        "str r0, [sp]\n"
        "mov r5, r1\n"
        "mov r0, r4\n"
        ".inst 0xeb06d981 @ bl #0x2bf8d4\n"
        "cmp r0, #0\n"
        ".inst 0x1a000003 @ bne #0x1092e4\n"
        "mov r2, #0\n"
        "mov r1, r5\n"
        "mov r0, r4\n"
        ".inst 0xeb003f21 @ bl #0x118f6c\n"
        "mov r0, #1\n"
        "pop {r3, r4, r5, pc}\n"
    );
}

// DECOMP_FUNC(0x001094c4, 96)
extern "C" __attribute__((naked)) void ui_func_001094c4() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb06dd7e @ bl #0x2c0ac8\n"
        "add r0, r0, #0xf00\n"
        "ldrb r1, [r0, #0x9a]\n"
        "cmp r1, #0\n"
        ".inst 0x0a000006 @ beq #0x1094f8\n"
        "ldrb r0, [r0, #0x9c]\n"
        "cmp r0, #0\n"
        ".inst 0x0a000004 @ beq #0x1094fc\n"
        "mov r0, #0\n"
        ".inst 0xeb06dafd @ bl #0x2c00e8\n"
        "cmp r0, #0\n"
        ".inst 0x0a000001 @ beq #0x109500\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0]\n"
        ".inst 0xeb06e9a6 @ bl #0x2c3ba8\n"
        "mov r0, #0\n"
        "nop\n"
        ".inst 0xeb00273b @ bl #0x113208\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x0044ea00 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00109614, 16)
extern "C" __attribute__((naked)) void func_00109614() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "strb r0, [r1, #0x1e5]\n"
        "bx lr\n"
        ".word 0x004c5634 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x00109ed8, 116)
extern "C" __attribute__((naked)) void ui_func_00109ed8() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb06daf9 @ bl #0x2c0ac8\n"
        "mov r4, r0\n"
        "add r0, r0, #0xf00\n"
        "ldrb r1, [r0, #0x9a]\n"
        "cmp r1, #0\n"
        ".inst 0x0a000002 @ beq #0x109f00\n"
        "ldrb r0, [r0, #0x9c]\n"
        "cmp r0, #0\n"
        ".inst 0x0a000001 @ beq #0x109f08\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        "ldr r0, [pc, #0x38]\n"
        "ldr r0, [r0]\n"
        ".inst 0xeb06e724 @ bl #0x2c3ba8\n"
        "ldr r1, [r4, #4]\n"
        "mov r0, #0x200\n"
        "str r0, [r1, #0x14]\n"
        "ldr r1, [r4, #4]\n"
        "str r0, [r1, #0x18]\n"
        "ldr r1, [r4, #4]\n"
        "mov r0, #0\n"
        ".inst 0xeb06d75f @ bl #0x2bfcb4\n"
        "strb r0, [r4, #0xf9b]\n"
        "mov r1, #1\n"
        "mov r0, #0\n"
        "strb r1, [r4, #0xf9c]\n"
        "pop {r4, pc}\n"
        ".word 0x0044ea00 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010a0a8, 100)
extern "C" __attribute__((naked)) void ui_func_0010a0a8() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb06da85 @ bl #0x2c0ac8\n"
        "mov r4, r0\n"
        "add r0, r0, #0xf00\n"
        "ldrb r1, [r0, #0x60]\n"
        "cmp r1, #0\n"
        ".inst 0x0a00000e @ beq #0x10a100\n"
        "ldrb r0, [r0, #0x63]\n"
        "cmp r0, #0\n"
        ".inst 0x0a00000c @ beq #0x10a104\n"
        "mov r0, #0\n"
        ".inst 0xeb06d803 @ bl #0x2c00e8\n"
        "cmp r0, #0\n"
        ".inst 0x1a000007 @ bne #0x10a100\n"
        "ldrb r0, [r4, #0xc]\n"
        "cmp r0, #0\n"
        ".inst 0x0a000004 @ beq #0x10a100\n"
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0]\n"
        ".inst 0xeb06e6ab @ bl #0x2c3ba8\n"
        "mov r0, #0\n"
        ".inst 0xeb002581 @ bl #0x113708\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x0044ea00 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010a10c, 48)
extern "C" __attribute__((naked)) void engine_func_0010a10c() {
    asm volatile(
        "ldr ip, [pc, #0x24]\n"
        "vldmia sp, {s0, s1, s2, s3}\n"
        "str r0, [ip, #0x1c]\n"
        "str r2, [ip, #0x20]\n"
        "str r1, [ip, #0x2c]\n"
        "str r3, [ip, #0x30]\n"
        "vstr s0, [ip, #0x24]\n"
        "vstr s1, [ip, #0x34]\n"
        "vstr s2, [ip, #0x28]\n"
        "vstr s3, [ip, #0x38]\n"
        "bx lr\n"
        ".word 0x00465120 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010a13c, 20)
extern "C" __attribute__((naked)) void func_0010a13c() {
    asm volatile(
        "ldr r3, [pc, #8]\n"
        "mov ip, #0\n"
        "stm r3, {r0, r1, r2, ip}\n"
        "bx lr\n"
        ".word 0x004e3f64 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010a4a8, 28)
extern "C" __attribute__((naked)) void ui_func_0010a4a8() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb06d985 @ bl #0x2c0ac8\n"
        "ldr r1, [pc, #8]\n"
        "mov r0, #0\n"
        "str r0, [r1, #0x10]\n"
        "pop {r4, pc}\n"
        ".word 0x00465120 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010a4c4, 24)
extern "C" __attribute__((naked)) void func_0010a4c4() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "ldr r1, [r0]\n"
        "rsb r1, r1, #1\n"
        "str r1, [r0]\n"
        "bx lr\n"
        ".word 0x00465058 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010ba24, 88)
extern "C" __attribute__((naked)) void ui_func_0010ba24() {
    asm volatile(
        "ldr ip, [pc, #0x44]\n"
        "mov r3, #0\n"
        "str r4, [sp, #-4]!\n"
        "ldr r4, [ip, r3, lsl #2]\n"
        "cmp r4, #0\n"
        ".inst 0x0a000004 @ beq #0x10ba50\n"
        "add r3, r3, #1\n"
        "cmp r3, #8\n"
        ".inst 0xbafffff9 @ blt #0x10ba30\n"
        "pop {r4}\n"
        "bx lr\n"
        "ldr r4, [pc, #0x1c]\n"
        "str r2, [ip, r3, lsl #2]\n"
        "add r4, r4, r3, lsl #1\n"
        "strh r0, [r4]\n"
        "ldr r0, [pc, #0x10]\n"
        "str r1, [r0, r3, lsl #2]\n"
        "pop {r4}\n"
        "bx lr\n"
        ".word 0x004daee8 @ literal/data\n"
        ".word 0x004def18 @ literal/data\n"
        ".word 0x004def28 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010be60, 32)
extern "C" __attribute__((naked)) void ui_func_0010be60() {
    asm volatile(
        "ldr r1, [pc, #0x14]\n"
        "ldr r2, [r1, #4]\n"
        "cmp r0, r2\n"
        "strlo r0, [r1, #8]\n"
        "movhs r0, #0\n"
        "movlo r0, #1\n"
        "bx lr\n"
        ".word 0x00464a70 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010be80, 72)
extern "C" __attribute__((naked)) void engine_func_0010be80() {
    asm volatile(
        "ldr r2, [pc, #0x3c]\n"
        "lsr r3, r0, #0x14\n"
        "ldr ip, [r2]\n"
        "lsl r2, r0, #0xc\n"
        "ldr r0, [ip, r3, lsl #3]\n"
        "lsr r2, r2, #0xc\n"
        "cmp r0, #0\n"
        ".inst 0x0a000005 @ beq #0x10beb8\n"
        "ldr r3, [r0, #0x24]\n"
        "cmp r3, r2\n"
        ".inst 0x0a000003 @ beq #0x10bebc\n"
        "ldr r0, [r0, #0x4c]\n"
        "cmp r0, #0\n"
        ".inst 0x1afffff9 @ bne #0x10bea0\n"
        "mov r0, #0\n"
        "str r1, [r0, #0x64]\n"
        "bx lr\n"
        ".word 0x004e3cf4 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010bec8, 52)
extern "C" __attribute__((naked)) void engine_func_0010bec8() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r0\n"
        "ldr r4, [pc, #0x20]\n"
        "mov r0, r4\n"
        ".inst 0xeb06ce5f @ bl #0x2bf85c\n"
        "cmp r0, #0\n"
        ".inst 0x0a000003 @ beq #0x10bef4\n"
        "mov r1, r5\n"
        "mov r0, r4\n"
        "pop {r4, r5, r6, lr}\n"
        ".inst 0xea009c1f @ b #0x132f74\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x004e1f68 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010d180, 40)
extern "C" __attribute__((naked)) void battle_func_0010d180() {
    asm volatile(
        "ldr r1, [pc, #0x1c]\n"
        "mov r2, #0\n"
        "sub r3, r1, #0xc\n"
        "str r2, [r3]\n"
        "ldr r2, [r0]\n"
        "str r2, [r1]\n"
        "ldr r0, [r0, #4]\n"
        "str r0, [r1, #4]\n"
        "bx lr\n"
        ".word 0x00465064 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010d1a8, 124)
extern "C" __attribute__((naked)) void engine_func_0010d1a8() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r4, [pc, #0x6c]\n"
        "cmp r0, #0\n"
        "add r1, r4, #0\n"
        "ldr r0, [r4, #8]\n"
        "ldrsb r1, [r1, #0x10]\n"
        ".inst 0x0a000009 @ beq #0x10d1ec\n"
        "cmp r1, #0\n"
        ".inst 0x1a000013 @ bne #0x10d21c\n"
        "cmp r0, #0\n"
        ".inst 0x0a000003 @ beq #0x10d1e4\n"
        "ldr r1, [r0, #0x64]\n"
        "cmp r1, #0\n"
        "ldreq r0, [r0, #0x60]\n"
        ".inst 0x0b06dfba @ bleq #0x2c50d0\n"
        "mov r0, #1\n"
        ".inst 0xea00000a @ b #0x10d218\n"
        "cmp r1, #1\n"
        ".inst 0x1a000009 @ bne #0x10d21c\n"
        "cmp r0, #0\n"
        ".inst 0x0a000005 @ beq #0x10d214\n"
        "ldr r1, [r0, #0x64]\n"
        "cmp r1, #0\n"
        ".inst 0x1a000002 @ bne #0x10d214\n"
        "ldr r0, [r0, #0x60]\n"
        "mov r1, #0\n"
        ".inst 0xeb06e036 @ bl #0x2c52f0\n"
        "mov r0, #0\n"
        "strb r0, [r4, #0x10]\n"
        "pop {r4, pc}\n"
        ".word 0x004e3cf4 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010d234, 24)
extern "C" __attribute__((naked)) void func_0010d234() {
    asm volatile(
        "ldr r1, [pc, #0xc]\n"
        "ldrb r2, [r1, #0x15]\n"
        "cmp r2, #0\n"
        "strbne r0, [r1, #0x17]\n"
        "bx lr\n"
        ".word 0x004e3154 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010d610, 28)
extern "C" __attribute__((naked)) void ui_func_0010d610() {
    asm volatile(
        "ldr r2, [pc, #4]\n"
        "strd r0, r1, [r2]\n"
        "bx lr\n"
        ".word 0x00464d90 @ literal/data\n"
        ".word 0xe59f0000 @ literal/data\n"
        ".word 0xea06db06 @ literal/data\n"
        ".word 0x0046519c @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010db6c, 84)
extern "C" __attribute__((naked)) void engine_func_0010db6c() {
    asm volatile(
        "push {r4, lr}\n"
        ".inst 0xeb00081c @ bl #0x10fbe8\n"
        ".inst 0xebfff196 @ bl #0x10a1d4\n"
        ".inst 0xebfff2e3 @ bl #0x10a70c\n"
        "pop {r4, lr}\n"
        "mov r0, r0\n"
        "ldr r0, [pc, #0x30]\n"
        "mov r1, #0x70\n"
        "push {r4, lr}\n"
        ".inst 0xeb06dbe6 @ bl #0x2c4b30\n"
        "ldr r0, [pc, #0x20]\n"
        "mov r3, #0\n"
        "mov r2, #0x40\n"
        "mov r1, #1\n"
        "strh r3, [r0]\n"
        "strh r2, [r0, #2]\n"
        "strb r1, [r0, #4]\n"
        "str r1, [r0, #8]\n"
        "mov r0, r1\n"
        "pop {r4, pc}\n"
        ".word 0x004eaae0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010dcc8, 92)
extern "C" __attribute__((naked)) void engine_func_0010dcc8() {
    asm volatile(
        "cmp r0, #0\n"
        ".inst 0x0a000012 @ beq #0x10dd1c\n"
        "vldr s2, [pc, #0x48]\n"
        "vcmpe.f32 s2, s0\n"
        "vmrs apsr_nzcv, fpscr\n"
        ".inst 0x8a00000e @ bhi #0x10dd1c\n"
        "vmov r1, s0\n"
        "cmp r1, #0x3f800000\n"
        ".inst 0xca00000b @ bgt #0x10dd1c\n"
        "vcmpe.f32 s2, s1\n"
        "vmrs apsr_nzcv, fpscr\n"
        ".inst 0x8a000008 @ bhi #0x10dd1c\n"
        "vmov r1, s1\n"
        "cmp r1, #0x3f800000\n"
        ".inst 0xca000005 @ bgt #0x10dd1c\n"
        "vstr s1, [r0, #0x3c]\n"
        "vstr s0, [r0, #0x40]\n"
        "ldr r2, [r0, #0x38]\n"
        "add r1, r0, #0x3c\n"
        "mov r0, r2\n"
        ".inst 0xea0116a9 @ b #0x1537c4\n"
        "bx lr\n"
        ".word 0x00000000 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010dd24, 76)
extern "C" __attribute__((naked)) void ui_func_0010dd24() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r4, [pc, #0x34]\n"
        "add r0, r4, #8\n"
        ".inst 0xeb06d772 @ bl #0x2c3b00\n"
        ".inst 0xeb06be3d @ bl #0x2bd630\n"
        "mov r1, #0\n"
        "str r1, [r0, #0x1ec]\n"
        "mcr p15, #0, r1, c7, c10, #5\n"
        "ldr r3, [pc, #0x1c]\n"
        "mov r2, #1\n"
        "mov r1, #0x14\n"
        "str r3, [r0, #0x1e8]\n"
        "ldr r0, [pc, #0x10]\n"
        "str r1, [r0]\n"
        "strb r2, [r4, #0x15]\n"
        "pop {r4, pc}\n"
        ".word 0x004e3154 @ literal/data\n"
        ".word 0x001197c4 @ literal/data\n"
        ".word 0x0044e90c @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010e550, 16)
extern "C" __attribute__((naked)) void func_0010e550() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #8]\n"
        "bx lr\n"
        ".word 0x004651e8 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010e560, 16)
extern "C" __attribute__((naked)) void func_0010e560() {
    asm volatile(
        "ldr r2, [pc, #4]\n"
        "strd r0, r1, [r2]\n"
        "bx lr\n"
        ".word 0x00465108 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010e570, 16)
extern "C" __attribute__((naked)) void ui_func_0010e570() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "str r0, [r1, #0x10]\n"
        "bx lr\n"
        ".word 0x00464d48 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010e580, 60)
extern "C" __attribute__((naked)) void func_0010e580() {
    asm volatile(
        "ldr r1, [pc, #0x30]\n"
        "add r0, r1, #0x400\n"
        "add r1, r1, #0x1000\n"
        "add r1, r1, #0x184\n"
        "add r0, r0, #0x384\n"
        "ldrb r1, [r1, #0x48]\n"
        "cmp r1, #0\n"
        ".inst 0x0a000004 @ beq #0x10e5b4\n"
        "add r1, r0, #0x800\n"
        "add r0, r0, #0x800\n"
        "vstr s0, [r1, #0x234]\n"
        "add r0, r0, #0x17c\n"
        ".inst 0xea004a64 @ b #0x120f48\n"
        "bx lr\n"
        ".word 0x004e1f68 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010e5bc, 16)
extern "C" __attribute__((naked)) void ui_func_0010e5bc() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "str r0, [r1, #0x28]\n"
        "bx lr\n"
        ".word 0x00464d48 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010e5cc, 20)
extern "C" __attribute__((naked)) void ui_func_0010e5cc() {
    asm volatile(
        "ldr r1, [pc, #8]\n"
        "bic r0, r0, #0xff\n"
        "str r0, [r1, #8]\n"
        "bx lr\n"
        ".word 0x00464d48 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010e5e0, 16)
extern "C" __attribute__((naked)) void battle_func_0010e5e0() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "str r0, [r1, #4]\n"
        "bx lr\n"
        ".word 0x00465058 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010e8c4, 96)
extern "C" __attribute__((naked)) void engine_func_0010e8c4() {
    asm volatile(
        "ldr r1, [pc, #0x30]\n"
        "add r0, r1, #0x400\n"
        "add r1, r1, #0x1000\n"
        "add r1, r1, #0x184\n"
        "add r0, r0, #0x384\n"
        "ldrb r1, [r1, #0x48]\n"
        "cmp r1, #0\n"
        ".inst 0x0a000004 @ beq #0x10e8f8\n"
        "add r1, r0, #0x800\n"
        "add r0, r0, #0x800\n"
        "vstr s0, [r1, #0x238]\n"
        "add r0, r0, #0x17c\n"
        ".inst 0xea004991 @ b #0x120f40\n"
        "bx lr\n"
        "subeq r1, lr, r8, ror #30\n"
        "ldr r0, [pc, #0x18]\n"
        "push {r4, lr}\n"
        ".inst 0xeb00a993 @ bl #0x138f5c\n"
        ".inst 0xeb06b82d @ bl #0x2bc9c8\n"
        "cmp r0, #0\n"
        "movne r0, #2\n"
        "moveq r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0046519c @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010e9cc, 32)
extern "C" __attribute__((naked)) void engine_func_0010e9cc() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r4, [pc, #0x10]\n"
        "ldr r0, [r4, #4]\n"
        ".inst 0xeb06d660 @ bl #0x2c4360\n"
        "mov r0, #0\n"
        "str r0, [r4, #4]\n"
        "pop {r4, pc}\n"
        ".word 0x0044ea58 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010ec3c, 16)
extern "C" __attribute__((naked)) void func_0010ec3c() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldr r0, [r0, #0x1c0]\n"
        "bx lr\n"
        ".word 0x004e39e0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010ec4c, 32)
extern "C" __attribute__((naked)) void ui_func_0010ec4c() {
    asm volatile(
        "ldr r1, [pc, #4]\n"
        "str r0, [r1, #0x24]\n"
        "bx lr\n"
        "subeq r4, r6, r8, asr #26\n"
        "ldr r1, [pc, #4]\n"
        "str r0, [r1, #0x2c]\n"
        "bx lr\n"
        ".word 0x00464d48 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010ed98, 60)
extern "C" __attribute__((naked)) void func_0010ed98() {
    asm volatile(
        "ldr r1, [pc, #0x30]\n"
        "add r0, r1, #0x400\n"
        "add r1, r1, #0x1000\n"
        "add r1, r1, #0x184\n"
        "add r0, r0, #0x384\n"
        "ldrb r1, [r1, #0x48]\n"
        "cmp r1, #0\n"
        ".inst 0x0a000004 @ beq #0x10edcc\n"
        "add r1, r0, #0x800\n"
        "add r0, r0, #0x800\n"
        "vstr s0, [r1, #0x23c]\n"
        "add r0, r0, #0x17c\n"
        ".inst 0xea00485a @ b #0x120f38\n"
        "bx lr\n"
        ".word 0x004e1f68 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010f110, 16)
extern "C" __attribute__((naked)) void func_0010f110() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrb r0, [r0]\n"
        "bx lr\n"
        ".word 0x0044e0b0 @ literal/data\n"
    );
}

// DECOMP_FUNC(0x0010f4e8, 60)
extern "C" __attribute__((naked)) void engine_func_0010f4e8() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "ldr r4, [pc, #0x28]\n"
        "mov r0, r4\n"
        ".inst 0xeb06d16b @ bl #0x2c3aa8\n"
        "ldr r0, [pc, #0x20]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "movne r5, #1\n"
        "moveq r5, #0\n"
        "mov r0, r4\n"
        ".inst 0xeb06d143 @ bl #0x2c3a24\n"
        "mov r0, r5\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x004c6410 @ literal/data\n"
        ".word 0x00465600 @ literal/data\n"
    );
}
