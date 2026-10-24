#include "types.h"

// DECOMP_FUNC(0x00259d6c, 28)
extern "C" __attribute__((naked)) void func_00259d6c() {
    asm volatile("vldmia r1, {s0, s1, s2, s3, s4, s5, s6, s7}\nadd r1, r1, #0x20\nvstmia r0, {s0, s1, s2, s3, s4, s5, s6, s7}\nadd r0, r0, #0x20\nvldmia r1, {s0, s1, s2, s3, s4, s5, s6, s7}\nvstmia r0, {s0, s1, s2, s3, s4, s5, s6, s7}\nbx lr\n");
}

// DECOMP_FUNC(0x002a2570, 28)
extern "C" __attribute__((naked)) void func_002a2570() {
    asm volatile("push {r4, r5, sb, sl, fp}\nldm r1!, {r2, r3, r4, r5}\nldm r1!, {fp, ip}\nstm r0!, {r2, r3, r4, r5}\nstm r0!, {fp, ip}\npop {r4, r5, sb, sl, fp}\nbx lr\n");
}

// DECOMP_FUNC(0x002a3788, 28)
extern "C" __attribute__((naked)) void func_002a3788() {
    asm volatile("vldmia r2, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}\nvldmia r1, {s12, s13, s14}\nvadd.f32 s3, s3, s12\nvadd.f32 s7, s7, s13\nvadd.f32 s11, s11, s14\nvstmia r0, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}\nbx lr\n");
}

// DECOMP_FUNC(0x002b0418, 28)
extern "C" __attribute__((naked)) void engine_func_002b0418() {
    asm volatile("ldr r2, [r0]\ncmp r2, #0\nmov r2, #0\nmoveq r2, #1\nstreq r1, [r0, #0x24]\nmov r0, r2\nbx lr\n");
}

// DECOMP_FUNC(0x0030c028, 28)
extern "C" __attribute__((naked)) void func_0030c028() {
    asm volatile("ldr r0, [r0, #0x4c]\nmov r0, r0\nldr r0, [r0, #0x20]\nvldmia r1, {s0, s1, s2, s3}\nadd r0, r0, #0x10\nvstmia r0, {s0, s1, s2, s3}\nbx lr\n");
}

// DECOMP_FUNC(0x0034f8dc, 28)
extern "C" __attribute__((naked)) void func_0034f8dc() {
    asm volatile("cmp r1, #0\ncmpne r2, #0\naddne r0, r0, #4\nmoveq r0, #0\nstmne r0, {r1, r2}\nmovne r0, #1\nbx lr\n");
}

// DECOMP_FUNC(0x0035a080, 28)
extern "C" u32 engine_func_0035a080(volatile u8* object, u32* optional_out, u32* first_out) {
    *first_out = *reinterpret_cast<volatile u32*>(object + 0x134);
    if (optional_out != 0) {
        *optional_out = *reinterpret_cast<volatile u32*>(object + 0x138);
    }
    return *reinterpret_cast<volatile u32*>(object + 0x138);
}

// DECOMP_FUNC(0x00383780, 28)
extern "C" __attribute__((naked)) void func_00383780() {
    asm volatile("ldr r1, [r0]\nmov r2, #0\norr r1, r1, #1\nstr r1, [r0], #4\nmov r1, #0x11\nstm r0, {r1, r2}\nbx lr\n");
}

// DECOMP_FUNC(0x003a1a6c, 28)
extern "C" __attribute__((naked)) void func_003a1a6c() {
    asm volatile("ldr r1, [r0]\nmov r2, #0\norr r1, r1, #1\nstr r1, [r0], #4\nmov r1, #0x13\nstm r0, {r1, r2}\nbx lr\n");
}

// DECOMP_FUNC(0x003a80cc, 28)
extern "C" __attribute__((naked)) void func_003a80cc() {
    asm volatile("mov r3, #1\nstrb r3, [r0, #0x10]\nadd r0, r0, #0x14\nmov r1, #0xd\nmov r2, #0\nstm r0, {r1, r2}\nbx lr\n");
}

// DECOMP_FUNC(0x003a9644, 28)
extern "C" __attribute__((naked)) void func_003a9644() {
    asm volatile("mov r3, #1\nstrb r3, [r0, #0x10]\nadd r0, r0, #0x14\nmov r1, #8\nmov r2, #0\nstm r0, {r1, r2}\nbx lr\n");
}

// DECOMP_FUNC(0x003b0394, 28)
extern "C" __attribute__((naked)) void func_003b0394() {
    asm volatile("ldr r2, [r1, #0x18]\nstr r2, [r0, #0x18]\nldr r2, [r1, #4]\nstr r2, [r0, #4]\nldr r1, [r1, #8]\nstr r1, [r0, #8]\nbx lr\n");
}

// DECOMP_FUNC(0x003bcb94, 28)
extern "C" __attribute__((naked)) void camp_func_003bcb94() {
    asm volatile("add r2, r0, r1, lsr #3\nand r1, r1, #7\nldrb r2, [r2, #0x4c]\nmov r0, #1\nands r0, r2, r0, lsl r1\nmovne r0, #1\nbx lr\n");
}

// DECOMP_FUNC(0x003e698c, 28)
extern "C" __attribute__((naked)) void func_003e698c() {
    asm volatile("ldrh r1, [r0, #8]\nsub r2, r1, #0x100\nsubs r2, r2, #1\nldreq r1, [r0, #0xc]\nmovne r0, #0\naddeq r0, r0, r1\nbx lr\n");
}

// DECOMP_FUNC(0x003e69c0, 28)
extern "C" __attribute__((naked)) void func_003e69c0() {
    asm volatile("ldrh r1, [r0, #0x10]\nsub r2, r1, #0x100\nsubs r2, r2, #1\nldreq r1, [r0, #0x14]\nmovne r0, #0\naddeq r0, r0, r1\nbx lr\n");
}

// DECOMP_FUNC(0x0011d8c4, 32)
extern "C" __attribute__((naked)) void func_0011d8c4() {
    asm volatile("ldr r1, [pc, #8]\nmov r0, #1\nstrb r0, [r1, #1]\nbx lr\n.word 0x0044e380\nbx lr\nbx lr\nbx lr\n");
}

// DECOMP_FUNC(0x001246f4, 32)
extern "C" __attribute__((naked)) void func_001246f4() {
    asm volatile("ldrh r0, [r0, #0x48]\ncmp r0, #0\nmovne r0, #1\nbx lr\nldrsh r0, [r0, #0x20]\nldrsh r1, [r1, #0x20]\nsub r0, r0, r1\nbx lr\n");
}

// DECOMP_FUNC(0x00145788, 32)
extern "C" __attribute__((naked)) void func_00145788() {
    asm volatile("ldr r1, [pc, #4]\nldrb r0, [r1, r0]\nbx lr\n.word 0x004e0d48\ncmp r0, #0\nldrne r0, [r0]\naddne r0, r0, r1, lsl #5\nbx lr\n");
}

// DECOMP_FUNC(0x00146cf0, 32)
extern "C" __attribute__((naked)) void engine_func_00146cf0() {
    asm volatile("ldrh r3, [r0, #0x36]\nadd r2, r0, #0x24\nand r1, r1, #1\nand r0, r3, #1\nbic r3, r3, #1\norr r1, r1, r3\nstrh r1, [r2, #0x12]\nbx lr\n");
}

// DECOMP_FUNC(0x00147244, 32)
extern "C" __attribute__((naked)) void func_00147244() {
    asm volatile("ldr r0, [r0, #0x68]\nmov r0, r0\nldrh r2, [r0, #0x1e]\nand r1, r1, #3\nbic r2, r2, #3\norr r1, r1, r2\nstrh r1, [r0, #0x1e]\nbx lr\n");
}

// DECOMP_FUNC(0x00147288, 32)
extern "C" __attribute__((naked)) void engine_func_00147288() {
    asm volatile("vstr s0, [r0, #0x64]\nldr r0, [r0, #0x68]\nmov r0, r0\nldrh r1, [r0, #0x6c]\nvstr s0, [r0, #0x68]\norr r1, r1, #1\nstrh r1, [r0, #0x6c]\nbx lr\n");
}

// DECOMP_FUNC(0x00207b78, 32)
extern "C" __attribute__((naked)) void func_00207b78() {
    asm volatile("ldr r0, [r0, #0x4c]\nldr r0, [r0, #0x24]\nldr r1, [r0, #0x20]\ncmp r1, #0\nldrne r0, [r0, #0xb8]\nmoveq r0, #0\naddne r0, r0, r1\nbx lr\n");
}

// DECOMP_FUNC(0x0023d348, 32)
extern "C" __attribute__((naked)) void func_0023d348() {
    asm volatile("ldr r2, [r0, #0x10]\nldrh r2, [r2, #4]\ncmp r2, r1\nldrgt r0, [r0, #0x14]\naddgt r0, r0, r1, lsl #5\nldrgt r0, [r0, #0x18]\nmovle r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0025c0f0, 32)
extern "C" __attribute__((naked)) void engine_func_0025c0f0() {
    asm volatile("ldr r0, [r0, #0x2c]\nadd r0, r0, #0x4c\nadd r1, r0, #0x30\nvstmia r1, {s0, s1, s2}\nldr r1, [r0, #0x3c]\norr r1, r1, #0x800\nstr r1, [r0, #0x3c]\nbx lr\n");
}

// DECOMP_FUNC(0x00287d54, 32)
extern "C" __attribute__((naked)) void engine_func_00287d54() {
    asm volatile("vsub.f32 s3, s3, s0\nvsub.f32 s0, s4, s1\nvsub.f32 s1, s5, s2\nvmul.f32 s2, s3, s3\nvmla.f32 s2, s0, s0\nvmla.f32 s2, s1, s1\nvsqrt.f32 s0, s2\nbx lr\n");
}

// DECOMP_FUNC(0x00296ef8, 32)
extern "C" void ui_func_00296ef8(volatile u8* block, u8 a1, u8 a2, u8 a3, u8 a4) {
    block[4] = a1;
    block[5] = a2;
    block[6] = a3;
    block[7] = a4;
    *reinterpret_cast<volatile u32*>(block + 8) = *reinterpret_cast<volatile u32*>(block + 4);
}

// DECOMP_FUNC(0x0029a2b0, 32)
extern "C" void engine_func_0029a2b0(void* part, u32 mode, f32 x, f32 y, f32 z) {
    (void)mode;
    u8* object = *reinterpret_cast<u8**>(static_cast<u8*>(part) + 0x2c);
    *reinterpret_cast<volatile f32*>(object + 0x58) = x;
    *reinterpret_cast<volatile f32*>(object + 0x68) = y;
    *reinterpret_cast<volatile f32*>(object + 0x78) = z;
    *reinterpret_cast<volatile u32*>(object + 0x88) |= 0x800;
}

// DECOMP_FUNC(0x002b2ccc, 32)
extern "C" void engine_func_002b2ccc(const u8* object, u32 unused, u32* result) {
    const u8* fields = *reinterpret_cast<const u8* const*>(object + 0x2c);
    result[0] = *reinterpret_cast<const u32*>(fields + 0x58);
    result[1] = *reinterpret_cast<const u32*>(fields + 0x68);
    result[2] = *reinterpret_cast<const u32*>(fields + 0x78);
}

// DECOMP_FUNC(0x002c00b4, 32)
extern "C" __attribute__((naked)) void battle_func_002c00b4() {
    asm volatile("cmp r1, r0\nbxeq lr\nvldmia r1!, {s0, s1, s2, s3, s4, s5}\nmov r2, r0\nvldmia r1, {s6, s7, s8, s9, s10, s11}\nvstmia r2!, {s0, s1, s2, s3, s4, s5}\nvstmia r2, {s6, s7, s8, s9, s10, s11}\nbx lr\n");
}

// DECOMP_FUNC(0x002df440, 32)
extern "C" __attribute__((naked)) void func_002df440() {
    asm volatile("ldr r0, [r0, #0x30]\nldr r0, [r0, #0x24]\nldr r1, [r0, #0x20]\ncmp r1, #0\nldrne r0, [r0, #0xb8]\nmoveq r0, #0\naddne r0, r0, r1\nbx lr\n");
}

// DECOMP_FUNC(0x002f300c, 32)
extern "C" __attribute__((naked)) void func_002f300c() {
    asm volatile("ldr r0, [r0, #0x9c]\nldr r0, [r0, #0x24]\nldr r1, [r0, #0x20]\ncmp r1, #0\nldrne r0, [r0, #0xb8]\nmoveq r0, #0\naddne r0, r0, r1\nbx lr\n");
}

// DECOMP_FUNC(0x00350804, 32)
extern "C" __attribute__((naked)) void func_00350804() {
    asm volatile("cmp r1, #0\nldrge r2, [r0, #0x484]\ncmpge r2, r1\naddgt r0, r0, r1, lsl #4\naddgt r0, r0, #0x400\nmovle r0, #0\naddgt r0, r0, #0xa8\nbx lr\n");
}

// DECOMP_FUNC(0x00350824, 32)
extern "C" __attribute__((naked)) void func_00350824() {
    asm volatile("cmp r1, #0\nldrge r2, [r0, #0x2e8]\ncmpge r2, r1\naddgt r1, r1, r1, lsl #2\nmovle r0, #0\naddgt r0, r0, r1, lsl #3\naddgt r0, r0, #0x30c\nbx lr\n");
}

// DECOMP_FUNC(0x0035ec08, 32)
extern "C" __attribute__((naked)) void func_0035ec08() {
    asm volatile("mov r3, #0\nstr r3, [r0, #8]\nadd r3, r0, #0xc\nstr r0, [r0]\nstm r3, {r1, r2}\nadd r3, r0, #4\nstm r3, {r0, r2}\nbx lr\n");
}
