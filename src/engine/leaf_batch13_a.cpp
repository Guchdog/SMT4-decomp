#include "types.h"

// DECOMP_FUNC(0x00132aa0, 56)
extern "C" __attribute__((naked)) void engine_func_00132aa0() {
    asm volatile("ldrh r1, [r0, #0x14]\ncmp r1, #0x2000\naddeq r0, r0, #0x14\nbeq 1f\nldrh r1, [r0, #0x20]\ncmp r1, #0x2000\naddeq r0, r0, #0x20\nbeq 1f\nldrh r1, [r0, #0x2c]\ncmp r1, #0x2000\naddeq r0, r0, #0x2c\nmovne r0, #0\n1:\nldr r0, [r0, #8]\nbx lr\n");
}

// DECOMP_FUNC(0x00132ad8, 56)
extern "C" __attribute__((naked)) void engine_func_00132ad8() {
    asm volatile("ldrh r1, [r0, #0x14]\ncmp r1, #0x2000\naddeq r0, r0, #0x14\nbeq 1f\nldrh r1, [r0, #0x20]\ncmp r1, #0x2000\naddeq r0, r0, #0x20\nbeq 1f\nldrh r1, [r0, #0x2c]\ncmp r1, #0x2000\naddeq r0, r0, #0x2c\nmovne r0, #0\n1:\nldr r0, [r0, #4]\nbx lr\n");
}

// DECOMP_FUNC(0x00235f90, 56)
extern "C" __attribute__((naked)) void func_00235f90() {
    asm volatile("push {r0, r1}\nldr r1, [r0, #0x1c]\nldrh r2, [sp, #4]\nldr r1, [r1, #0x188]\nbics r1, r2, r1\nldrne r0, [r0, #8]\nbne 1f\nldr r1, [r0, #0x24]\ncmp r1, #0\nldrgt r0, [r0, #0x10]\nldrgt r0, [r0]\nmovle r0, #0\n1:\nadd sp, sp, #8\nbx lr\n");
}

// DECOMP_FUNC(0x002364b0, 56)
extern "C" __attribute__((naked)) void func_002364b0() {
    asm volatile("ldr r1, [r0, #0x3c]\nmov r2, #0x10\nbics r2, r2, r1\nbeq 3f\nldr r2, [r0]\ncmp r2, #0x3f800000\nbne 1f\nldr r2, [r0, #0x14]\ncmp r2, #0x3f800000\norreq r1, r1, #0x80\nbeq 2f\n1:\nbic r1, r1, #0x80\n2:\nstr r1, [r0, #0x3c]\n3:\nbx lr\n");
}

// DECOMP_FUNC(0x0027e92c, 56)
extern "C" __attribute__((naked)) void engine_func_0027e92c() {
    asm volatile("ldr r2, [r0, #8]\nmov r0, #0\ncmp r2, #0\nbeq 3f\n1:\nldr r3, [r2, #8]\ncmp r3, r1\nbne 2f\nldrb r3, [r2, #5]\ntst r3, #4\naddeq r0, r0, #1\n2:\nldr r2, [r2, #0xc]\ncmp r2, #0\nbne 1b\n3:\nbx lr\n");
}

// DECOMP_FUNC(0x0035ebd0, 56)
extern "C" __attribute__((naked)) void func_0035ebd0() {
    asm volatile("mov r3, #0\nstr r4, [sp, #-4]!\nstr r3, [r0]\nldr r3, [r1, #4]\n1:\ncmp r3, r1\nstr r3, [r0]\nbeq 2f\nldr r4, [r2]\nldr ip, [r3, #8]\ncmp ip, r4\nldrne r3, [r3, #4]\nbne 1b\n2:\npop {r4}\nbx lr\n");
}

// DECOMP_FUNC(0x003aad60, 56)
extern "C" __attribute__((naked)) void unite_func_003aad60() {
    asm volatile("mov r1, #0\nmov r2, #0x10\nmov ip, r1\nmvn r3, #0\npush {r4, r5}\n1:\nadd r4, r0, r1, lsl #1\nadd r5, r0, r1\nstrh r3, [r4]\nsubs r2, r2, #1\nadd r1, r1, #1\nstrb ip, [r5, #0x20]\nbne 1b\npop {r4, r5}\nbx lr\n");
}

// DECOMP_FUNC(0x003e6884, 56)
extern "C" __attribute__((naked)) void func_003e6884() {
    asm volatile("ldrh r1, [r0, #0x14]\ncmp r1, #0x4000\naddeq r0, r0, #0x14\nbeq 1f\nldrh r1, [r0, #0x20]\ncmp r1, #0x4000\naddeq r0, r0, #0x20\nbeq 1f\nldrh r1, [r0, #0x2c]\ncmp r1, #0x4000\naddeq r0, r0, #0x2c\nmovne r0, #0\n1:\nldr r0, [r0, #8]\nbx lr\n");
}

// DECOMP_FUNC(0x003e68fc, 56)
extern "C" __attribute__((naked)) void func_003e68fc() {
    asm volatile("ldrh r1, [r0, #0x14]\ncmp r1, #0x4000\naddeq r0, r0, #0x14\nbeq 1f\nldrh r1, [r0, #0x20]\ncmp r1, #0x4000\naddeq r0, r0, #0x20\nbeq 1f\nldrh r1, [r0, #0x2c]\ncmp r1, #0x4000\naddeq r0, r0, #0x2c\nmovne r0, #0\n1:\nldr r0, [r0, #4]\nbx lr\n");
}

// DECOMP_FUNC(0x0014d230, 60)
extern "C" __attribute__((naked)) void func_0014d230() {
    asm volatile("mov r2, #4\ncmp r2, r1, lsr #24\nbne 1f\nldr r2, [r0, #0x2c]\nbic r1, r1, #0xff000000\nadd r0, r0, r2\nldr r2, [r0]\ncmp r2, r1\nbhi 2f\n1:\nmov r0, #0\nbx lr\n2:\nadd r1, r0, r1, lsl #3\nldr r1, [r1, #8]\nadd r0, r0, r1\nbx lr\n");
}

// DECOMP_FUNC(0x00151f64, 60)
extern "C" __attribute__((naked)) void func_00151f64() {
    asm volatile("mov r2, #2\ncmp r2, r1, lsr #24\nbne 1f\nldr r2, [r0, #0xc]\nbic r1, r1, #0xff000000\nadd r0, r0, r2\nldr r2, [r0]\ncmp r2, r1\nbhi 2f\n1:\nmov r0, #0\nbx lr\n2:\nadd r1, r0, r1, lsl #3\nldr r1, [r1, #8]\nadd r0, r0, r1\nbx lr\n");
}

// DECOMP_FUNC(0x00155774, 60)
extern "C" __attribute__((naked)) void engine_func_00155774() {
    asm volatile("mov r2, #5\ncmp r2, r1, lsr #24\nbne 1f\nldr r2, [r0, #0x1c]\nbic r1, r1, #0xff000000\nadd r0, r0, r2\nldr r2, [r0]\ncmp r2, r1\nbhi 2f\n1:\nmov r0, #0\nbx lr\n2:\nadd r1, r0, r1, lsl #3\nldr r1, [r1, #8]\nadd r0, r0, r1\nbx lr\n");
}

// DECOMP_FUNC(0x002347b8, 60)
extern "C" __attribute__((naked)) void engine_func_002347b8() {
    asm volatile("mov r3, #0\nstr r3, [r0]\nldr r1, [r1, #4]\ncmp r1, #0\nbeq 1f\nldr r3, [r1, #4]\ncmp r2, r3\nbhi 1f\nldr r1, [r1]\nadd r2, r2, r2, lsl #1\nadd r1, r1, r2, lsl #4\nb 2f\n1:\nmov r1, #0\n2:\nstr r1, [r0]\nbx lr\n");
}

// DECOMP_FUNC(0x002a6d58, 60)
extern "C" __attribute__((naked)) void func_002a6d58() {
    asm volatile("mov r2, #1\ncmp r2, r1, lsr #24\nbne 1f\nldr r2, [r0, #4]\nbic r1, r1, #0xff000000\nadd r0, r0, r2\nldr r2, [r0]\ncmp r2, r1\nbhi 2f\n1:\nmov r0, #0\nbx lr\n2:\nadd r1, r0, r1, lsl #3\nldr r1, [r1, #8]\nadd r0, r0, r1\nbx lr\n");
}

// DECOMP_FUNC(0x002bdbcc, 60)
extern "C" __attribute__((naked)) void engine_func_002bdbcc() {
    asm volatile("ldr r2, [r0]\ncmp r2, #0\nbeq 1f\nldr r3, [r2, #8]\nmov r1, #0\ncmp r3, r0\nstreq r1, [r2, #8]\nldr r2, [r0]\nldr r3, [r2, #0xc]\ncmp r3, r0\nstreq r1, [r2, #0xc]\nldr r2, [r0]\ncmp r2, #0\nstrne r1, [r0]\n1:\nbx lr\n");
}

// DECOMP_FUNC(0x00378d60, 60)
extern "C" __attribute__((naked)) void func_00378d60() {
    asm volatile("ldr r0, [r0, #0x254]\nmov r0, r0\nldr r1, [r0]\ncmp r1, #0\nbeq 2f\nldr r3, [r1, #0x254]\nmov r2, #0\ncmp r3, r0\nbne 1f\nstr r2, [r1, #0x254]\nldr r1, [r0]\ncmp r1, #0\nbeq 2f\n1:\nstr r2, [r0]\n2:\nbx lr\n");
}

// DECOMP_FUNC(0x003bd310, 60)
extern "C" __attribute__((naked)) void battle_func_003bd310() {
    asm volatile("tst r0, #2\ntsteq r0, #0x20\nbne 1f\ntst r0, #0x40\ntsteq r0, #0x80\nbne 1f\ntst r0, #0x100\ntsteq r0, #0x200\nbne 1f\ntst r0, #0x400\ntsteq r0, #4\nandseq r0, r0, #8\nbeq 2f\n1:\nmov r0, #1\n2:\nbx lr\n");
}

// DECOMP_FUNC(0x003e6a44, 60)
extern "C" __attribute__((naked)) void func_003e6a44() {
    asm volatile("mov r2, #6\ncmp r2, r1, lsr #24\nbne 1f\nldr r2, [r0, #0x24]\nbic r1, r1, #0xff000000\nadd r0, r0, r2\nldr r2, [r0]\ncmp r2, r1\nbhi 2f\n1:\nmov r0, #0\nbx lr\n2:\nadd r1, r0, r1, lsl #3\nldr r1, [r1, #8]\nadd r0, r0, r1\nbx lr\n");
}

// DECOMP_FUNC(0x003eac78, 60)
extern "C" __attribute__((naked)) void func_003eac78() {
    asm volatile("ldr r2, [r1, #4]\nldr r3, [r0, #4]\ncmp r2, r3\nbne 1f\nldr r2, [r1, #8]\nldr r3, [r0, #8]\ncmp r2, r3\nbne 1f\nldr r1, [r1, #0x18]\nldr r0, [r0, #0x18]\ncmp r1, r0\nmoveq r0, #1\nbeq 2f\n1:\nmov r0, #0\n2:\nbx lr\n");
}

// DECOMP_FUNC(0x0013add4, 64)
extern "C" __attribute__((naked)) void func_0013add4() {
    asm volatile("ldr r2, [r0, #4]\ncmp r2, #0\nbeq 2f\n1:\nldr r2, [r0, #4]\ncmp r1, #0\nldrex r2, [r2]\nlsr r3, r2, #0x18\norrne r3, r3, #1\nbiceq r3, r3, #1\nbic r2, r2, #0xff000000\norr r2, r2, r3, lsl #24\nldr r3, [r0, #4]\nstrex ip, r2, [r3]\ncmp ip, #0\nbne 1b\n2:\nbx lr\n");
}

// DECOMP_FUNC(0x0015d5b4, 64)
extern "C" __attribute__((naked)) void func_0015d5b4() {
    asm volatile("ldrb r1, [r0, #0x104]\ncmp r1, #0\nbeq 1f\nmov r1, #0\nstrb r1, [r0, #0x104]\nstr r1, [r0, #0x3c]\nstr r1, [r0, #0x4c]\nstr r1, [r0, #0x5c]\nstr r1, [r0, #0x60]\nstr r1, [r0, #0x7c]\nstr r1, [r0, #0x40]\nstr r1, [r0, #0x50]\nstr r1, [r0, #0x64]\nstr r1, [r0, #0x68]\nstr r1, [r0, #0x80]\n1:\nbx lr\n");
}

// DECOMP_FUNC(0x0023d460, 64)
extern "C" __attribute__((naked)) void battle_func_0023d460() {
    asm volatile("mov r2, #0\npush {r4, r5}\nmov r1, r2\nmov r3, #0xc\nmvn r4, #0\nstr r2, [r0]\n1:\nadd r5, r0, r1\nadd ip, r0, r1, lsl #2\nstrb r2, [r5, #4]\nstr r2, [ip, #0x10]!\nsubs r3, r3, #1\nadd r1, r1, #1\nstr r4, [ip, #0x30]\nbne 1b\npop {r4, r5}\nbx lr\n");
}

// DECOMP_FUNC(0x00249acc, 64)
extern "C" __attribute__((naked)) void camp_func_00249acc() {
    asm volatile("push {r4, lr}\nmov r4, r0\nadd r0, r0, #0x1c4\nldrsh r0, [r0, #0x50]\ncmp r0, #3\nbne 1f\nldrb r0, [r4, #0x218]\ncmp r0, #0\nbeq 2f\n1:\nmov r0, #1\npop {r4, pc}\n2:\nadd r0, r4, #0x1c4\npop {r4, lr}\nmov r0, r0\nldrsb r0, [r0, #0x8a]\nbx lr\n");
}

// DECOMP_FUNC(0x002af854, 64)
extern "C" __attribute__((naked)) void battle_func_002af854() {
    asm volatile("ldr ip, [r0, #0x58]\ncmp ip, #0\nbeq 1f\nstrh r1, [r0, #0x5c]\nmov r3, #0\nadd r1, r1, r1, lsl #1\nstrh r3, [r0, #0x5e]\nstrb r3, [r0, #0x87]\nadd r1, ip, r1, lsl #2\nstrb r3, [r0, #0x8a]\ncmp r2, #0\nstrb r2, [r0, #0x60]\nldrne r1, [r1, #4]\nldreq r1, [r1]\nstr r1, [r0, #0x20]\n1:\nbx lr\n");
}

// DECOMP_FUNC(0x0035b324, 64)
extern "C" __attribute__((naked)) void func_0035b324() {
    asm volatile("ldr r3, [r0, #0x18]\nldr r2, [r1]\ncmp r3, #0\nmovgt r1, #5\nstrbgt r1, [r2, #8]\nbgt 1f\nmov ip, #0\nstrb ip, [r2, #8]\nldr r1, [r1]\nmov r3, #0x2d\nstrh r3, [r1, #0xa]\n1:\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x00376678, 64)
extern "C" __attribute__((naked)) void func_00376678() {
    asm volatile("ldr r1, [r0, #0xc]\nldr r2, [r0, #0x38]\nldrsb r3, [r0, #0x30]\ncmp r1, #0\nbeq 1f\nldr r1, [r1, #0x38]\nmov ip, #1\nbics r1, ip, r1\nbne 2f\n1:\ncmp r3, #0\norrne r1, r2, #1\nbne 3f\n2:\nbic r1, r2, #1\n3:\nbic r1, r1, #2\nstr r1, [r0, #0x38]\nbx lr\n");
}

// DECOMP_FUNC(0x001465d8, 68)
extern "C" __attribute__((naked)) void func_001465d8() {
    asm volatile("push {r3, r4}\n1:\nldrex r3, [r0]\nstrex r4, r1, [r0]\ncmp r4, #0\nbne 1b\nmov r3, #0\nstrh r3, [sp]\nadd r1, r0, #4\nmov r3, sp\n2:\nldrexh ip, [r1]\nldrsh ip, [r3]\nstrexh r4, ip, [r1]\ncmp r4, #0\nbne 2b\nstrh r2, [r0, #6]\npop {r3, r4}\nbx lr\n");
}

// DECOMP_FUNC(0x00158790, 68)
extern "C" __attribute__((naked)) void func_00158790() {
    asm volatile("ldrb r3, [r0, #0xc]\ncmp r3, #0\nbeq 1f\ncmp r1, #0\nbeq 2f\ncmp r1, #1\nbne 1f\nvmov s0, r2\nvldr s1, [r0, #0x70]\nvcvt.f32.s32 s0, s0\nvadd.f32 s0, s1, s0\nvstr s0, [r0, #0x70]\n1:\nbx lr\n2:\nldr r1, [r0, #0x6c]\nadd r1, r1, r2\nstr r1, [r0, #0x6c]\nbx lr\n");
}

// DECOMP_FUNC(0x002baca8, 68)
extern "C" __attribute__((naked)) void engine_func_002baca8() {
    asm volatile("push {r4, r5, r6}\nldr ip, [r0, #0x754]\ntst ip, #1\nbne 1f\norr ip, ip, #5\ncmp r3, #0\nstr ip, [r0, #0x754]\nstrbne r3, [r0, #0xd50]\nldm r1, {r3, r4, r5, r6, ip}\nmov r1, #0\nstr r2, [r0, #0xd54]\nstr r1, [r0, #0xd58]\nadd r0, r0, #0x400\nadd r0, r0, #0x358\nstm r0, {r3, r4, r5, r6, ip}\n1:\npop {r4, r5, r6}\nbx lr\n");
}

// DECOMP_FUNC(0x00336fdc, 68)
extern "C" __attribute__((naked)) void func_00336fdc() {
    asm volatile("mov r1, #0\npush {r4, r5}\nmov r2, #0x2a\nmov ip, r1\nmvn r4, #0\n1:\nadd r3, r0, r1, lsl #3\nadd r5, r3, #0x1c00\nadd r5, r5, #0x3e4\nadd r3, r3, #0x1c00\nadd r3, r3, #0x3e8\nstr ip, [r5]\nsubs r2, r2, #1\nadd r1, r1, #1\nstr r4, [r3]\nbne 1b\npop {r4, r5}\nbx lr\n");
}

// DECOMP_FUNC(0x003aadf8, 68)
extern "C" __attribute__((naked)) void func_003aadf8() {
    asm volatile("mov r1, #0\npush {r4, r5}\nmov r2, #0x10\nmov r4, r1\nmvn ip, #0\n1:\nadd r3, r0, r1, lsl #1\nldrsh r5, [r3]\ncmn r5, #1\nbeq 2f\nadd r5, r0, r1\nstrh ip, [r3]\nstrb r4, [r5, #0x20]\n2:\nsubs r2, r2, #1\nadd r1, r1, #1\nbne 1b\npop {r4, r5}\nbx lr\n");
}

// DECOMP_FUNC(0x003e8474, 68)
extern "C" __attribute__((naked)) void func_003e8474() {
    asm volatile("ldr r2, [r0, #0xc]\nadd r2, r2, r0\nadd r3, r2, r1, lsl #3\nldrh r0, [r3, #4]\ncmp r0, #0x5900\nbeq 1f\nsub r0, r0, #0x5900\nsubs r0, r0, #3\nbeq 3f\nb 2f\n1:\nldr r0, [r2]\ncmp r0, r1\nldrhi r0, [r3, #8]\naddhi r0, r0, r2\nbhi 3f\n2:\nmov r0, #0\n3:\nbx lr\n");
}

// DECOMP_FUNC(0x001263e8, 72)
extern "C" __attribute__((naked)) void func_001263e8() {
    asm volatile("ldrb r1, [r0, #0x44]\ncmp r1, #2\nbne 2f\nldr r1, [r0, #0x34]\ntst r1, #0x20\nbeq 1f\nldr r2, [r0]\nldr r0, [r0, #8]\nadd r0, r2, r0, lsl #5\nldrh r0, [r0]\nsub r3, r0, #0xff00\nsubs r3, r3, #0xff\nbeq 2f\n1:\ntst r1, #0x80\nmoveq r0, #1\nbeq 3f\n2:\nmov r0, #0\n3:\nbx lr\n");
}

// DECOMP_FUNC(0x002215a0, 72)
extern "C" __attribute__((naked)) void func_002215a0() {
    asm volatile("mov r3, r0\nmov r1, #1\npush {r4, r5, r6}\nmov r0, #0\nmov r2, #0x1f4\nmov r4, r1\n1:\nasr ip, r1, #0x1f\nadd ip, r1, ip, lsr #29\nbic r6, ip, #7\nldrb ip, [r3, ip, asr #3]\nsub r5, r1, r6\nadd r1, r1, #1\ntst ip, r4, lsl r5\naddne r0, r0, #1\nsubs r2, r2, #1\nbne 1b\npop {r4, r5, r6}\nbx lr\n");
}
