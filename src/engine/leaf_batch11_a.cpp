#include "types.h"

// DECOMP_FUNC(0x003b00b4, 44)
extern "C" __attribute__((naked)) void func_003b00b4() {
    asm volatile("ldr r2, [r1, #0x1c]\nstr r2, [r0, #0x1c]\nldr r2, [r1, #0x20]\nstr r2, [r0, #0x20]\nldr r2, [r1, #0x18]\nstr r2, [r0, #0x18]\nldr r2, [r1, #4]\nstr r2, [r0, #4]\nldr r1, [r1, #8]\nstr r1, [r0, #8]\nbx lr\n");
}

// DECOMP_FUNC(0x003e8ad4, 44)
extern "C" __attribute__((naked)) void func_003e8ad4() {
    asm volatile("ldr r3, [r2]\nadd r0, r1, #8\nmov ip, #0\ncmp r3, #0\naddsne r2, r2, r3\nsubne r2, r2, r0\nstreq ip, [r0]\nstrne r2, [r0]\nmov r0, #1\nstr r0, [r1, #4]\nbx lr\n");
}

// DECOMP_FUNC(0x003f8808, 44)
extern "C" __attribute__((naked)) void func_003f8808() {
    asm volatile("ldr r0, [sp]\nlsl r2, r2, #0x1e\nlsl ip, r0, #0x18\norr r3, ip, r3, lsl #13\norr r2, r3, r2, lsr #8\nmov r0, #0\nmov r3, r0\norr r2, r2, #0x200000\norr r0, r0, r1\norr r1, r2, r3\nbx lr\n");
}

// DECOMP_FUNC(0x003f88e4, 44)
extern "C" __attribute__((naked)) void func_003f88e4() {
    asm volatile("ldr r0, [sp]\nlsl r2, r2, #0x1e\nlsl ip, r0, #0x18\norr r3, ip, r3, lsl #13\norr r2, r3, r2, lsr #8\nmov r0, #0\nmov r3, r0\norr r2, r2, #0x200000\norr r0, r0, r1\norr r1, r2, r3\nbx lr\n");
}

// DECOMP_FUNC(0x003f89cc, 44)
extern "C" __attribute__((naked)) void func_003f89cc() {
    asm volatile("ldr r0, [sp]\nlsl r2, r2, #0x1e\nlsl ip, r0, #0x18\norr r3, ip, r3, lsl #13\norr r2, r3, r2, lsr #8\nmov r0, #0\nmov r3, r0\norr r2, r2, #0x200000\norr r0, r0, r1\norr r1, r2, r3\nbx lr\n");
}

// DECOMP_FUNC(0x001dd7b8, 48)
extern "C" __attribute__((naked)) void func_001dd7b8() {
    asm volatile("ldr r0, [pc, #0x1c]\nmov r1, #1\nldr r0, [r0]\ncmp r0, #0\nldrne r0, [r0, #0xf0]\ncmpne r0, #7\nmovne r1, #0\neor r0, r1, #1\nbx lr\n.word 0x0044d198\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x00227dc4, 48)
extern "C" __attribute__((naked)) void func_00227dc4() {
    asm volatile("sub r0, r0, #4\ncmp r0, #0x32\nmovlo r0, #0\nmovhs r0, #1\nsub r1, r1, #4\ncmp r1, #0x32\nmovlo r1, #0\nmovhs r1, #1\ncmp r0, r1\nmoveq r0, #1\nmovne r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x002a260c, 48)
extern "C" __attribute__((naked)) void func_002a260c() {
    asm volatile("push {r4, r5, sb, sl, fp}\nldm r1!, {r2, r3, r4, r5}\npld [r1, #0x40]\nldm r1!, {sb, sl, fp, ip}\nstm r0!, {r2, r3, r4, r5}\nstm r0!, {sb, sl, fp, ip}\nldm r1!, {r2, r3, r4, r5}\nldm r1!, {fp, ip}\nstm r0!, {r2, r3, r4, r5}\nstm r0!, {fp, ip}\npop {r4, r5, sb, sl, fp}\nbx lr\n");
}

// DECOMP_FUNC(0x002b49a0, 48)
extern "C" __attribute__((naked)) void engine_func_002b49a0() {
    asm volatile("ldr r3, [r0, #0x14]\nadd r1, r0, r1, lsl #4\ncmp r2, #0\nadd r1, r1, r3\nldrne r3, [r1, #4]\nstrne r3, [r2]\nldr r2, [r1, #4]\ncmp r2, #0\nldrne r1, [r1, #8]\nmoveq r0, #0\naddne r0, r0, r1\nbx lr\n");
}

// DECOMP_FUNC(0x003811cc, 48)
extern "C" __attribute__((naked)) void func_003811cc() {
    asm volatile("ldr r2, [r0, #0x3c]\nmov ip, #0x180\nbics ip, ip, r1\nbic r3, r2, #0x7e0\nbic r2, r1, #0x60\norreq r2, r2, #0x40\nmov ip, #0x240\nbics r1, ip, r1\norreq r2, r2, #0x20\norr r1, r3, r2\nstr r1, [r0, #0x3c]\nbx lr\n");
}

// DECOMP_FUNC(0x0015a2ec, 52)
extern "C" __attribute__((naked)) void func_0015a2ec() {
    asm volatile("cmp r1, #0\nldrb r1, [r0, #7]\norrne r1, r1, #1\nbiceq r1, r1, #1\nstrb r1, [r0, #7]\nldr r0, [r0, #0x68]\nand r1, r1, #0xff\nmov r0, r0\nldrh r2, [r0, #0x6c]\nstrb r1, [r0, #0xf]\norr r1, r2, #4\nstrh r1, [r0, #0x6c]\nbx lr\n");
}

// DECOMP_FUNC(0x001a083c, 52)
extern "C" __attribute__((naked)) void func_001a083c() {
    asm volatile("str r4, [sp, #-4]!\nldr r1, [r0, #0x18]\nldrd r2, r3, [r0, #0xb8]\nmov ip, #2\nmov r4, #0x18\nadd r1, ip, r1, lsl #2\nldrh r1, [r3, r1]\nadd r1, r4, r1, lsl #5\nldr r1, [r2, r1]\nstr r1, [r0, #0x18]\npop {r4}\nmov r0, #1\nbx lr\n");
}

// DECOMP_FUNC(0x002263a0, 52)
extern "C" __attribute__((naked)) void func_002263a0() {
    asm volatile("vldmia r2, {s7, s8}\nvldr s6, [r1]\nvldr s4, [r2, #8]\nvldr s3, [r1, #4]\nvldr s5, [r1, #8]\nvmul.f32 s2, s6, s8\nvmul.f32 s0, s3, s4\nvmul.f32 s1, s5, s7\nvmls.f32 s2, s3, s7\nvmls.f32 s0, s5, s8\nvmls.f32 s1, s6, s4\nvstmia r0, {s0, s1, s2}\nbx lr\n");
}

// DECOMP_FUNC(0x0023d368, 52)
extern "C" __attribute__((naked)) void func_0023d368() {
    asm volatile("vldmia r1, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}\nvldmia r2, {s12, s13, s14}\nvmul.f32 s0, s0, s12\nvmul.f32 s1, s1, s13\nvmul.f32 s2, s2, s14\nvmul.f32 s4, s4, s12\nvmul.f32 s5, s5, s13\nvmul.f32 s6, s6, s14\nvmul.f32 s8, s8, s12\nvmul.f32 s9, s9, s13\nvmul.f32 s10, s10, s14\nvstmia r0, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}\nbx lr\n");
}

// DECOMP_FUNC(0x0023d39c, 52)
extern "C" __attribute__((naked)) void func_0023d39c() {
    asm volatile("vldmia r1, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}\nvldmia r2, {s12, s13, s14}\nvmla.f32 s3, s0, s12\nvmla.f32 s7, s4, s12\nvmla.f32 s11, s8, s12\nvmla.f32 s3, s1, s13\nvmla.f32 s7, s5, s13\nvmla.f32 s11, s9, s13\nvmla.f32 s3, s2, s14\nvmla.f32 s7, s6, s14\nvmla.f32 s11, s10, s14\nvstmia r0, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}\nbx lr\n");
}

// DECOMP_FUNC(0x0023e55c, 52)
extern "C" __attribute__((naked)) void func_0023e55c() {
    asm volatile("vldmia r1, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}\nvldmia r2, {s12, s13, s14}\nvmul.f32 s0, s0, s12\nvmul.f32 s1, s1, s13\nvmul.f32 s2, s2, s14\nvmul.f32 s4, s4, s12\nvmul.f32 s5, s5, s13\nvmul.f32 s6, s6, s14\nvmul.f32 s8, s8, s12\nvmul.f32 s9, s9, s13\nvmul.f32 s10, s10, s14\nvstmia r0, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}\nbx lr\n");
}

// DECOMP_FUNC(0x002a1a08, 52)
extern "C" __attribute__((naked)) void func_002a1a08() {
    asm volatile("vldmia r1!, {s0, s1, s2, s3}\nvstr s0, [r0, #0xc]\nvstr s1, [r0, #8]\nvstr s2, [r0, #4]\nvstr s3, [r0]\nbx lr\nvldmia r1!, {s0, s1, s2, s3}\nstr r2, [r0, #4]\nvstr s0, [r0, #0x10]\nvstr s1, [r0, #0xc]\nvstr s2, [r0, #8]\nvstr s3, [r0]\nbx lr\n");
}

// DECOMP_FUNC(0x002a7060, 52)
extern "C" __attribute__((naked)) void func_002a7060() {
    asm volatile("str r4, [sp, #-4]!\nmov ip, #0\nvldr s0, [sp, #4]\nstr ip, [r0, #0x10]\nstr ip, [r0, #0x14]\nmov r4, #1\nstr ip, [r0, #0x18]\nstrh r4, [r0, #0x2c]\nstrh r4, [r0, #0x2e]\nstm r0, {r1, r2, r3}\nvstr s0, [r0, #0xc]\npop {r4}\nbx lr\n");
}

// DECOMP_FUNC(0x002a8a58, 52)
extern "C" __attribute__((naked)) void engine_func_002a8a58() {
    asm volatile("vldmia r1, {s0, s1, s2, s3, s4, s5, s6, s7, s8}\nvldmia r2, {s9, s10, s11}\nvmul.f32 s12, s0, s9\nvmul.f32 s13, s3, s9\nvmul.f32 s14, s6, s9\nvmla.f32 s12, s1, s10\nvmla.f32 s13, s4, s10\nvmla.f32 s14, s7, s10\nvmla.f32 s12, s2, s11\nvmla.f32 s13, s5, s11\nvmla.f32 s14, s8, s11\nvstmia r0, {s12, s13, s14}\nbx lr\n");
}

// DECOMP_FUNC(0x0035bbc4, 52)
extern "C" __attribute__((naked)) void func_0035bbc4() {
    asm volatile("ldr r3, [r1]\nmov r2, #0\nstrb r2, [r3, #8]\nldrd r2, r3, [r0, #0xc]\nldr r1, [r1]\nadd r2, r2, r3, lsl #1\nldrh r2, [r2]\nstrh r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035c00c, 52)
extern "C" __attribute__((naked)) void func_0035c00c() {
    asm volatile("ldr r3, [r1]\nmov r2, #0\nstrb r2, [r3, #8]\nldrd r2, r3, [r0, #0xc]\nldr r1, [r1]\nadd r2, r2, r3, lsl #1\nldrh r2, [r2]\nstrh r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035c2f8, 52)
extern "C" __attribute__((naked)) void func_0035c2f8() {
    asm volatile("mov r1, #0\nstr r1, [r0, #8]\nstr r0, [r0]\nadd r2, r0, #0xc\nstr r1, [r0, #0x14]\nstr r2, [r0, #0xc]\nstr r0, [r0, #4]\nstr r1, [r0, #0x18]\nstr r2, [r0, #0x10]\nstr r1, [r0, #0x1c]\nstr r1, [r0, #0x20]\nstrb r1, [r0, #0x24]\nbx lr\n");
}

// DECOMP_FUNC(0x0014720c, 56)
extern "C" __attribute__((naked)) void func_0014720c() {
    asm volatile("subs r2, r1, #0\nmov r3, #0\nmovlt r2, r3\nstr r2, [r0, #0x18]\nldr r0, [r0, #0x68]\nmov r0, r0\ncmp r1, #0\nmov r2, #0\nmovlt r1, r2\nldrh r2, [r0, #0x6c]\nstr r1, [r0, #0x20]\norr r2, r2, #2\nstrh r2, [r0, #0x6c]\nbx lr\n");
}

// DECOMP_FUNC(0x001a0870, 56)
extern "C" __attribute__((naked)) void func_001a0870() {
    asm volatile("str r4, [sp, #-4]!\nldr r1, [r0, #0x18]\nldr r2, [r0, #0xbc]\nmov ip, #2\nldr r3, [r0, #0xb4]\nadd r1, ip, r1, lsl #2\nmov r4, #0x18\nldrh r1, [r2, r1]\nadd r1, r4, r1, lsl #5\nldr r1, [r3, r1]\nstr r1, [r0, #0x18]\npop {r4}\nmov r0, #1\nbx lr\n");
}

// DECOMP_FUNC(0x0023d5ac, 56)
extern "C" __attribute__((naked)) void camp_func_0023d5ac() {
    asm volatile("cmp r0, #0\nmovne r0, #0x100\ncmp r1, #0\nmovne r1, #0x200\ncmp r2, #0\norr r0, r0, r1\nmovne r1, #0x400\nmoveq r1, #0\ncmp r3, #0\norr r0, r0, r1\nmovne r1, #0x800\nmoveq r1, #0\norr r0, r0, r1\nbx lr\n");
}
