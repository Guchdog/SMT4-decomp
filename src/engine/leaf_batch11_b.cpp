#include "types.h"

// DECOMP_FUNC(0x002a1a90, 56)
extern "C" __attribute__((naked)) void func_002a1a90() {
    asm volatile("vldmia r1!, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}\nvstr s0, [r0, #0xc]\nvstr s1, [r0, #8]\nvstr s2, [r0, #4]\nvstr s3, [r0]\nvstr s4, [r0, #0x1c]\nvstr s5, [r0, #0x18]\nvstr s6, [r0, #0x14]\nvstr s7, [r0, #0x10]\nvstr s8, [r0, #0x2c]\nvstr s9, [r0, #0x28]\nvstr s10, [r0, #0x24]\nvstr s11, [r0, #0x20]\nbx lr\n");
}

// DECOMP_FUNC(0x002a37a4, 56)
extern "C" __attribute__((naked)) void func_002a37a4() {
    asm volatile("vldmia r1!, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}\nvldmia r2, {s12, s13, s14}\nvmla.f32 s3, s0, s12\nvmla.f32 s7, s4, s12\nvmla.f32 s11, s8, s12\nvmla.f32 s3, s1, s13\nvmla.f32 s7, s5, s13\nvmla.f32 s11, s9, s13\nvmla.f32 s3, s2, s14\nvmla.f32 s7, s6, s14\nvmla.f32 s11, s10, s14\nvldmia r1!, {s12, s13, s14, s15}\nvstmia r0, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15}\nbx lr\n");
}

// DECOMP_FUNC(0x002d5644, 56)
extern "C" __attribute__((naked)) void camp_func_002d5644() {
    asm volatile("ldr r0, [pc, #0x1c]\nmov r2, #0\nmov r1, #0x2d\nstrb r2, [r0, #0x10]\nstrh r1, [r0, #2]\nstrh r1, [r0, #6]\nstrh r1, [r0, #0xa]\nstrh r1, [r0, #0xe]\nbx lr\n.word 0x00465278\nldr r0, [r0, #0x1c]\nbx lr\nldr r0, [r0, #0x24]\nbx lr\n");
}

// DECOMP_FUNC(0x003f61f0, 56)
extern "C" __attribute__((naked)) void nn_sdk_func_003f61f0() {
    asm volatile("push {r4, r5, r6, lr}\nmov r4, r0\nmov r5, r1\nldr r1, [pc, #0x10]\nmov r0, #0\nmov r0, r0\nldr r0, [pc, #8]\nstrd r4, r5, [r0]\npop {r4, r5, r6, pc}\n.word 0x0400008a\n.word 0x0044e948\nldr r0, [r0]\nmov r0, r0\nbx lr\n");
}

// DECOMP_FUNC(0x0023afb4, 60)
extern "C" __attribute__((naked)) void func_0023afb4() {
    asm volatile("vldmia r1!, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}\nstr r2, [r0, #4]\nvstr s0, [r0, #0x10]\nvstr s1, [r0, #0xc]\nvstr s2, [r0, #8]\nvstr s3, [r0]\nvstr s4, [r0, #0x20]\nvstr s5, [r0, #0x1c]\nvstr s6, [r0, #0x18]\nvstr s7, [r0, #0x14]\nvstr s8, [r0, #0x30]\nvstr s9, [r0, #0x2c]\nvstr s10, [r0, #0x28]\nvstr s11, [r0, #0x24]\nbx lr\n");
}

// DECOMP_FUNC(0x002a4b4c, 60)
extern "C" __attribute__((naked)) void func_002a4b4c() {
    asm volatile("add ip, r2, #8\nsub r0, r0, #0x1400\nmul r1, ip, r1\nsubs r0, r0, #6\nmov r0, #1\nmoveq r0, #4\nadd r2, r3, #0x1f\nmul r0, r1, r0\nbic r1, r2, #0x1f\nadd r1, r1, r0\nadd r1, r1, #0x1f\nbic r1, r1, #0x1f\nadd r1, r1, r0\nadd r0, r0, r1\nbx lr\n");
}

// DECOMP_FUNC(0x002ad6d8, 60)
extern "C" __attribute__((naked)) void battle_func_002ad6d8() {
    asm volatile("vldmia r1, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}\nvldmia r2, {s12, s13, s14}\nvmla.f32 s3, s0, s12\nvmla.f32 s7, s4, s12\nvmla.f32 s11, s8, s12\nvmla.f32 s3, s1, s13\nvmla.f32 s7, s5, s13\nvmla.f32 s11, s9, s13\nvmla.f32 s3, s2, s14\nvmla.f32 s7, s6, s14\nvmla.f32 s11, s10, s14\nvstr s3, [r0]\nvstr s7, [r0, #4]\nvstr s11, [r0, #8]\nbx lr\n");
}

// DECOMP_FUNC(0x00353124, 60)
extern "C" __attribute__((naked)) void script_vm_func_00353124() {
    asm volatile("mov r3, #0\nstr r3, [r0]\nstr r3, [r0, #4]\nstr r3, [r0, #8]\nstr r3, [r0, #0xc]\nstr r3, [r0, #0x10]\nstr r3, [r0, #0x14]\nstr r3, [r0, #0x18]\nstr r3, [r0, #0x1c]\nstr r3, [r0, #0x20]\nstr r3, [r0, #0x24]\nstrb r3, [r0, #0x28]\nadd r3, r0, #0x2c\nstm r3, {r1, r2}\nbx lr\n");
}

// DECOMP_FUNC(0x003531ac, 60)
extern "C" __attribute__((naked)) void script_vm_func_003531ac() {
    asm volatile("mov r3, #0\nstr r3, [r0]\nstr r3, [r0, #4]\nstr r3, [r0, #8]\nstr r3, [r0, #0xc]\nstr r3, [r0, #0x10]\nstr r3, [r0, #0x14]\nstr r3, [r0, #0x18]\nstr r3, [r0, #0x1c]\nstr r3, [r0, #0x20]\nstr r3, [r0, #0x24]\nstrb r3, [r0, #0x28]\nadd r3, r0, #0x2c\nstm r3, {r1, r2}\nbx lr\n");
}

// DECOMP_FUNC(0x0015f6d4, 64)
extern "C" __attribute__((naked)) void battle_func_0015f6d4() {
    asm volatile("vldmia r2, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}\nvldmia r1, {s12, s13, s14}\nvmul.f32 s0, s0, s12\nvmul.f32 s1, s1, s12\nvmul.f32 s2, s2, s12\nvmul.f32 s3, s3, s12\nvmul.f32 s4, s4, s13\nvmul.f32 s5, s5, s13\nvmul.f32 s6, s6, s13\nvmul.f32 s7, s7, s13\nvmul.f32 s8, s8, s14\nvmul.f32 s9, s9, s14\nvmul.f32 s10, s10, s14\nvmul.f32 s11, s11, s14\nvstmia r0, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}\nbx lr\n");
}

// DECOMP_FUNC(0x001dc708, 64)
extern "C" __attribute__((naked)) void func_001dc708() {
    asm volatile("ldr r2, [r0, #0x1c]\nldrb r1, [r0, #0x3b]\nadd r3, r0, #0x20\nstrb r1, [r2, r3]\nldr r1, [r0, #0x1c]\nldr r2, [r0, #0xa8]\nadd r1, r0, r1, lsl #2\nstr r2, [r1, #0x3c]\nldr r1, [r0, #0x1c]\nadd r1, r1, #1\nstr r1, [r0, #0x1c]\nldr r1, [r0, #0x18]\nadd r1, r1, #1\nstr r1, [r0, #0x18]\nmov r0, #1\nbx lr\n");
}

// DECOMP_FUNC(0x00256ed8, 64)
extern "C" __attribute__((naked)) void func_00256ed8() {
    asm volatile("vldmia r2, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}\nvldmia r1, {s12, s13, s14}\nvmul.f32 s0, s0, s12\nvmul.f32 s1, s1, s12\nvmul.f32 s2, s2, s12\nvmul.f32 s3, s3, s12\nvmul.f32 s4, s4, s13\nvmul.f32 s5, s5, s13\nvmul.f32 s6, s6, s13\nvmul.f32 s7, s7, s13\nvmul.f32 s8, s8, s14\nvmul.f32 s9, s9, s14\nvmul.f32 s10, s10, s14\nvmul.f32 s11, s11, s14\nvstmia r0, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}\nbx lr\n");
}

// DECOMP_FUNC(0x0035b254, 64)
extern "C" __attribute__((naked)) void func_0035b254() {
    asm volatile("ldr ip, [r0, #0x18]\nldr r2, [r1]\nmov r3, #0\ncmp ip, #0\nmovle ip, #7\nstrbgt r3, [r2, #8]\nstrble ip, [r2, #8]\nldr r1, [r1]\nmovgt ip, #0x2e\nstrhgt ip, [r1, #0xa]\nstrble r3, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035bf8c, 64)
extern "C" __attribute__((naked)) void func_0035bf8c() {
    asm volatile("ldr ip, [r0, #0x18]\nldr r2, [r1]\nmov r3, #0\ncmp ip, #0\nmovle ip, #0x11\nstrbgt r3, [r2, #8]\nstrble ip, [r2, #8]\nldr r1, [r1]\nmovgt ip, #0x5e\nstrhgt ip, [r1, #0xa]\nstrble r3, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x002f28f8, 68)
extern "C" __attribute__((naked)) void func_002f28f8() {
    asm volatile("ldrd r0, r1, [r0, #0x20]\nvldr s1, [r1, #0x64]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0x64]\nvldr s1, [r1, #0x68]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0x68]\nvldr s1, [r1, #0x74]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0x74]\nvldr s1, [r1, #0x7c]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0x7c]\nvldr s1, [r1, #0x84]\nvmul.f32 s0, s1, s0\nvstr s0, [r0, #0x84]\nbx lr\n");
}

// DECOMP_FUNC(0x00121ed8, 72)
extern "C" __attribute__((naked)) void engine_func_00121ed8() {
    asm volatile("mov r1, #0\nstr r1, [r0]\nstr r1, [r0, #4]\nstrb r1, [r0, #8]\nstr r1, [r0, #0xc]\nstr r1, [r0, #0x10]\nstr r1, [r0, #0x14]\nstrb r1, [r0, #0x18]\nstrb r1, [r0, #0x19]\nstrb r1, [r0, #0x1a]\nstrh r1, [r0, #0x1c]\nstr r1, [r0, #0x1e]\nstr r1, [r0, #0x22]\nstr r1, [r0, #0x26]\nstr r1, [r0, #0x2a]\nstr r1, [r0, #0x2e]\nstr r1, [r0, #0x32]\nbx lr\n");
}

// DECOMP_FUNC(0x0013d938, 72)
extern "C" __attribute__((naked)) void func_0013d938() {
    asm volatile("ldr r1, [r0, #4]\nmov r2, #0x20\nstr r2, [r0, #4]\nldr r3, [r0, #8]\ncmp r3, #0x20\nmovhs r2, r3\nstr r2, [r0, #8]\nldr r2, [r0]\nstr r1, [r0, #4]\nadd r2, r2, #0x1f\nbic r2, r2, #0x1f\nadd r2, r2, #0x860\nstr r2, [r0]\nldr r2, [r0, #8]\ncmp r2, r1\nmovhs r1, r2\nstr r1, [r0, #8]\nbx lr\n");
}

// DECOMP_FUNC(0x00296f18, 72)
extern "C" __attribute__((naked)) void ui_func_00296f18() {
    asm volatile("mov ip, #0\nstr r2, [r0, #0x1c]\nstr ip, [r0]\nstr ip, [r0, #4]\nstr ip, [r0, #8]\nstr ip, [r0, #0xc]\nstr ip, [r0, #0x20]\nmov r3, #2\nstr r1, [r0, #0x10]\nstr r3, [r0, #0x14]\nstr ip, [r0, #0x24]\ncmp r1, #0\nstr r1, [r0, #0x18]\nmovle r1, #0\nstr r1, [r0, #0x18]\nmov r1, #6\nstr r1, [r0]\nbx lr\n");
}

// DECOMP_FUNC(0x002b7aa8, 72)
extern "C" __attribute__((naked)) void ui_func_002b7aa8() {
    asm volatile("vldr s0, [r1]\nvldr s1, [r1, #0x10]\nvldr s2, [r1, #0x20]\nvldr s3, [r1, #0x30]\nvldr s4, [r1, #4]\nvldr s5, [r1, #0x14]\nvldr s6, [r1, #0x24]\nvldr s7, [r1, #0x34]\nvldr s8, [r1, #8]\nvldr s9, [r1, #0x18]\nvldr s10, [r1, #0x28]\nvldr s11, [r1, #0x38]\nvldr s12, [r1, #0xc]\nvldr s13, [r1, #0x1c]\nvldr s14, [r1, #0x2c]\nvldr s15, [r1, #0x3c]\nvstmia r0, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15}\nbx lr\n");
}

// DECOMP_FUNC(0x00127fe8, 76)
extern "C" __attribute__((naked)) void func_00127fe8() {
    asm volatile("mrc p15, #0, r0, c13, c0, #3\nmov r1, #0\nstr r1, [r0]\nstr r1, [r0, #4]\nstr r1, [r0, #8]\nstr r1, [r0, #0xc]\nstr r1, [r0, #0x10]\nstr r1, [r0, #0x14]\nstr r1, [r0, #0x18]\nstr r1, [r0, #0x1c]\nstr r1, [r0, #0x20]\nstr r1, [r0, #0x24]\nstr r1, [r0, #0x28]\nstr r1, [r0, #0x2c]\nstr r1, [r0, #0x30]\nstr r1, [r0, #0x34]\nstr r1, [r0, #0x38]\nstr r1, [r0, #0x3c]\nbx lr\n");
}

// DECOMP_FUNC(0x001285c4, 76)
extern "C" __attribute__((naked)) void func_001285c4() {
    asm volatile("ldrsh r1, [r0]\ncmp r1, #0x28\nmovlt r1, #0x28\nstrhlt r1, [r0]\nldrsh r1, [r0, #2]\ncmp r1, #0x24\nmovlt r1, #0x24\nstrhlt r1, [r0, #2]\nldrsh r2, [r0, #6]\nmov r1, #0x91\ncmp r2, #0x91\nstrhgt r1, [r0, #6]\nldrsh r2, [r0, #8]\ncmp r2, #0x91\nstrhgt r1, [r0, #8]\nldrsh r2, [r0, #0xa]\ncmp r2, #0x91\nstrhgt r1, [r0, #0xa]\nbx lr\n");
}

// DECOMP_FUNC(0x0023aff0, 76)
extern "C" __attribute__((naked)) void func_0023aff0() {
    asm volatile("vldmia r1!, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15}\nstr r2, [r0, #4]\nvstr s0, [r0, #0x10]\nvstr s1, [r0, #0xc]\nvstr s2, [r0, #8]\nvstr s3, [r0]\nvstr s4, [r0, #0x20]\nvstr s5, [r0, #0x1c]\nvstr s6, [r0, #0x18]\nvstr s7, [r0, #0x14]\nvstr s8, [r0, #0x30]\nvstr s9, [r0, #0x2c]\nvstr s10, [r0, #0x28]\nvstr s11, [r0, #0x24]\nvstr s12, [r0, #0x40]\nvstr s13, [r0, #0x3c]\nvstr s14, [r0, #0x38]\nvstr s15, [r0, #0x34]\nbx lr\n");
}

// DECOMP_FUNC(0x00245e2c, 76)
extern "C" __attribute__((naked)) void script_vm_func_00245e2c() {
    asm volatile("mov r1, r0\ncmp r1, #0xc\nmov r0, #0\nldrlo pc, [pc, r1, lsl #2]\nbx lr\n.word 0x00245e3c\n.word 0x00245e3c\n.word 0x00245e3c\n.word 0x00245e3c\n.word 0x00245e3c\n.word 0x00245e3c\n.word 0x00245e3c\n.word 0x00245e70\n.word 0x00245e70\n.word 0x00245e70\n.word 0x00245e70\n.word 0x00245e70\nmvn r0, #2\nbx lr\n");
}

// DECOMP_FUNC(0x00286700, 76)
extern "C" __attribute__((naked)) void func_00286700() {
    asm volatile("mov r2, #0\nmov r3, #0x3f800000\nstr r2, [r0, #4]\nstr r3, [r0]\nstr r2, [r0, #8]\nldr ip, [r1]\nstr ip, [r0, #0xc]\nstrd r2, r3, [r0, #0x10]\nstr r2, [r0, #0x18]\nldr ip, [r1, #4]\nstr r2, [r0, #0x20]\nstr ip, [r0, #0x1c]\nstrd r2, r3, [r0, #0x24]\nldr r1, [r1, #8]\nadd ip, r0, #0x2c\nstm ip, {r1, r2}\nstr r2, [r0, #0x34]\nstrd r2, r3, [r0, #0x38]\nbx lr\n");
}

// DECOMP_FUNC(0x002a1b4c, 76)
extern "C" __attribute__((naked)) void func_002a1b4c() {
    asm volatile("vldmia r1!, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15}\nstr r2, [r0, #4]\nvstr s0, [r0, #0x10]\nvstr s1, [r0, #0xc]\nvstr s2, [r0, #8]\nvstr s3, [r0]\nvstr s4, [r0, #0x20]\nvstr s5, [r0, #0x1c]\nvstr s6, [r0, #0x18]\nvstr s7, [r0, #0x14]\nvstr s8, [r0, #0x30]\nvstr s9, [r0, #0x2c]\nvstr s10, [r0, #0x28]\nvstr s11, [r0, #0x24]\nvstr s12, [r0, #0x40]\nvstr s13, [r0, #0x3c]\nvstr s14, [r0, #0x38]\nvstr s15, [r0, #0x34]\nbx lr\n");
}
