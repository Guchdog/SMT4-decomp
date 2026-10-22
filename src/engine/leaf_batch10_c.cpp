#include "types.h"

// Batch 10, group C: candidates 68-100 from tools/find_candidates.py.

// DECOMP_FUNC(0x002a2db4, 40)
extern "C" __attribute__((naked)) void func_002a2db4() {
    asm volatile("ldr r1, [r1]\nldr r2, [r1, #4]!\ncmp r2, #0\naddne r1, r1, r2\nmoveq r1, #0\nldr r2, [r1, #0x48]\nadd r1, r1, #0x10\nstr r1, [r0, #4]\nstr r2, [r0]\nbx lr\n");
}

// DECOMP_FUNC(0x002c3344, 40)
extern "C" __attribute__((naked)) void camp_func_002c3344() {
    asm volatile("mov r1, #0\nstr r1, [r0]\nstr r1, [r0, #4]\nstr r1, [r0, #8]\nstr r1, [r0, #0xc]\nstr r1, [r0, #0x10]\nstr r1, [r0, #0x14]\nstr r1, [r0, #0x18]\nstr r1, [r0, #0x1c]\nbx lr\n");
}

// DECOMP_FUNC(0x002c5f7c, 40)
extern "C" __attribute__((naked)) void ui_func_002c5f7c() {
    asm volatile("cmp r0, #1\nmov r2, #1\nmoveq r2, #0\ncmp r1, #0\norr r1, r2, r0, lsl #4\nmovne r0, #0x1000\nmoveq r0, #0\norr r0, r0, r1\norr r0, r0, #0xf00\nbx lr\n");
}

// DECOMP_FUNC(0x003105b4, 40)
extern "C" __attribute__((naked)) void func_003105b4() {
    asm volatile("str r4, [sp, #-4]!\nldr r4, [sp, #8]\nldr ip, [sp, #4]\norr ip, ip, r4, lsl #8\norr r0, ip, r0, lsl #16\norr r0, r0, r1, lsl #20\norr r0, r0, r2, lsl #24\npop {r4}\norr r0, r0, r3, lsl #28\nbx lr\n");
}

// DECOMP_FUNC(0x00337c40, 40)
extern "C" __attribute__((naked)) void camp_func_00337c40() {
    asm volatile("ldr r3, [r0, #0x3f0]\nadd r3, r0, r3, lsl #3\nstr r2, [r3, #0x1f0]\nldr r2, [r0, #0x3f0]\nadd r2, r0, r2, lsl #3\nstr r1, [r2, #0x1f4]\nldr r1, [r0, #0x3f0]\nadd r1, r1, #1\nstr r1, [r0, #0x3f0]\nbx lr\n");
}

// DECOMP_FUNC(0x0034dd44, 40)
extern "C" __attribute__((naked)) void func_0034dd44() {
    asm volatile("ldr r0, [r0, #4]\nadd r3, r1, r1, lsl #2\nadd r1, r3, r1, lsl #6\nadd r0, r0, #0x1c00\nadd r0, r0, #0x298\nmov r2, #0x5a\nldr r0, [r0]\nadd r1, r2, r1, lsl #2\nldrh r0, [r0, r1]\nbx lr\n");
}

// DECOMP_FUNC(0x0035d9d0, 40)
extern "C" __attribute__((naked)) void func_0035d9d0() {
    asm volatile("mov r2, #0\nadd r1, r0, #4\nstr r2, [r0]\nstr r1, [r0, #4]\nstr r2, [r0, #0xc]\nstr r1, [r0, #8]\nstr r2, [r0, #0x10]\nstr r2, [r0, #0x14]\nstr r2, [r0, #0x18]\nbx lr\n");
}

// DECOMP_FUNC(0x00385d6c, 40)
extern "C" __attribute__((naked)) void func_00385d6c() {
    asm volatile("bx lr\nbx lr\nldrh r0, [r0]\nldrh r1, [r1]\nsub r0, r0, r1\nbx lr\nldrh r0, [r0]\nldrh r1, [r1]\nsub r0, r0, r1\nbx lr\n");
}

// DECOMP_FUNC(0x003eb258, 40)
extern "C" __attribute__((naked)) void func_003eb258() {
    asm volatile("add r2, r0, #0x10\nldm r2, {r2, r3, ip}\nstm r1, {r2, r3, ip}\nadd r2, r0, #0x1c\nldm r2, {r2, r3, ip}\nstr ip, [r1, #0x14]\nstrd r2, r3, [r1, #0xc]\nldr r0, [r0, #0xc]\nstr r0, [r1, #0x1c]\nbx lr\n");
}

// DECOMP_FUNC(0x0027f170, 44)
extern "C" __attribute__((naked)) void script_vm_func_0027f170() {
    asm volatile("vsub.f32 s0, s0, s4\nvsub.f32 s1, s2, s6\nvadd.f32 s3, s3, s7\nvmul.f32 s0, s0, s0\nvmla.f32 s0, s1, s1\nvsqrt.f32 s1, s0\nvcmpe.f32 s3, s1\nvmrs apsr_nzcv, fpscr\nmovge r0, #1\nmovlt r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x002a4600, 44)
extern "C" __attribute__((naked)) void ui_func_002a4600() {
    asm volatile("lsl r1, r0, #1\nlsls r0, r1, #8\nmovne r0, #4\nlsrs r2, r1, #0x18\norrne r0, r0, #1\nmov r2, #0xff000000\nbics r1, r2, r1\norreq r0, r0, #2\ncmp r0, #1\nmoveq r0, #5\nbx lr\n");
}

// DECOMP_FUNC(0x002b777c, 44)
extern "C" __attribute__((naked)) void engine_func_002b777c() {
    asm volatile("mov r2, r0\nldm r1, {r0, r3}\nmov ip, #0\nstr r3, [r0, #4]\nstr r0, [r3]\nldr r3, [r2]\nsub r3, r3, #1\nstr r3, [r2]\nstr ip, [r1]\nstr ip, [r1, #4]\nbx lr\n");
}

// DECOMP_FUNC(0x0034dd6c, 44)
extern "C" __attribute__((naked)) void func_0034dd6c() {
    asm volatile("ldr r0, [r0, #4]\nadd r3, r1, r1, lsl #2\nadd r1, r3, r1, lsl #6\nadd r0, r0, #0x1c00\nadd r0, r0, #0x298\nmov r2, #0x40\nldr r0, [r0]\nadd r1, r2, r1, lsl #2\nadd r0, r0, r1\nvldr s0, [r0]\nbx lr\n");
}

// DECOMP_FUNC(0x0035b6fc, 44)
extern "C" __attribute__((naked)) void func_0035b6fc() {
    asm volatile("ldr ip, [r1]\nmov r3, #0x11\nmov r2, #4\nstrb r3, [ip, #8]\nldr r1, [r1]\nstrb r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035b728, 44)
extern "C" __attribute__((naked)) void func_0035b728() {
    asm volatile("ldr ip, [r1]\nmov r3, #0x11\nmov r2, #3\nstrb r3, [ip, #8]\nldr r1, [r1]\nstrb r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035b754, 44)
extern "C" __attribute__((naked)) void func_0035b754() {
    asm volatile("ldr ip, [r1]\nmov r3, #8\nmov r2, #1\nstrb r3, [ip, #8]\nldr r1, [r1]\nstrb r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035b814, 44)
extern "C" __attribute__((naked)) void func_0035b814() {
    asm volatile("ldr ip, [r1]\nmov r3, #8\nmov r2, #2\nstrb r3, [ip, #8]\nldr r1, [r1]\nstrb r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035b840, 44)
extern "C" __attribute__((naked)) void func_0035b840() {
    asm volatile("ldr ip, [r1]\nmov r3, #8\nmov r2, #3\nstrb r3, [ip, #8]\nldr r1, [r1]\nstrb r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035b86c, 44)
extern "C" __attribute__((naked)) void func_0035b86c() {
    asm volatile("ldr ip, [r1]\nmov r3, #0x11\nmov r2, #6\nstrb r3, [ip, #8]\nldr r1, [r1]\nstrb r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035b898, 44)
extern "C" __attribute__((naked)) void func_0035b898() {
    asm volatile("ldr ip, [r1]\nmov r3, #0\nmov r2, #7\nstrb r3, [ip, #8]\nldr r1, [r1]\nstrh r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, r3\nbx lr\n");
}

// DECOMP_FUNC(0x0035b8c4, 44)
extern "C" __attribute__((naked)) void func_0035b8c4() {
    asm volatile("ldr ip, [r1]\nmov r3, #0x11\nmov r2, #2\nstrb r3, [ip, #8]\nldr r1, [r1]\nstrb r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035b95c, 44)
extern "C" __attribute__((naked)) void func_0035b95c() {
    asm volatile("ldr ip, [r1]\nmov r3, #7\nmov r2, #1\nstrb r3, [ip, #8]\nldr r1, [r1]\nstrb r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035b988, 44)
extern "C" __attribute__((naked)) void func_0035b988() {
    asm volatile("ldr ip, [r1]\nmov r3, #0\nmov r2, #0x1b\nstrb r3, [ip, #8]\nldr r1, [r1]\nstrh r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, r3\nbx lr\n");
}

// DECOMP_FUNC(0x0035b9b4, 44)
extern "C" __attribute__((naked)) void func_0035b9b4() {
    asm volatile("ldr ip, [r1]\nmov r3, #0\nmov r2, #0xc\nstrb r3, [ip, #8]\nldr r1, [r1]\nstrh r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, r3\nbx lr\n");
}

// DECOMP_FUNC(0x0035b9e0, 44)
extern "C" __attribute__((naked)) void func_0035b9e0() {
    asm volatile("ldr ip, [r1]\nmov r3, #0\nmov r2, #0xa\nstrb r3, [ip, #8]\nldr r1, [r1]\nstrh r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, r3\nbx lr\n");
}

// DECOMP_FUNC(0x0035baa0, 44)
extern "C" __attribute__((naked)) void func_0035baa0() {
    asm volatile("ldr ip, [r1]\nmov r3, #0\nmov r2, #0xd\nstrb r3, [ip, #8]\nldr r1, [r1]\nstrh r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, r3\nbx lr\n");
}

// DECOMP_FUNC(0x0035bacc, 44)
extern "C" __attribute__((naked)) void func_0035bacc() {
    asm volatile("ldr ip, [r1]\nmov r3, #7\nmov r2, #2\nstrb r3, [ip, #8]\nldr r1, [r1]\nstrb r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035baf8, 44)
extern "C" __attribute__((naked)) void func_0035baf8() {
    asm volatile("ldr ip, [r1]\nmov r3, #0\nmov r2, #9\nstrb r3, [ip, #8]\nldr r1, [r1]\nstrh r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, r3\nbx lr\n");
}

// DECOMP_FUNC(0x0035bb48, 44)
extern "C" __attribute__((naked)) void func_0035bb48() {
    asm volatile("ldr ip, [r1]\nmov r3, #7\nmov r2, #3\nstrb r3, [ip, #8]\nldr r1, [r1]\nstrb r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035bb98, 44)
extern "C" __attribute__((naked)) void func_0035bb98() {
    asm volatile("ldr ip, [r1]\nmov r3, #0x11\nmov r2, #5\nstrb r3, [ip, #8]\nldr r1, [r1]\nstrb r2, [r1, #0xa]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035c210, 44)
extern "C" __attribute__((naked)) void func_0035c210() {
    asm volatile("ldr r2, [r1]\nmov r1, #4\nstrb r1, [r2, #8]\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nldr r1, [r0, #0x18]\nsub r1, r1, #1\nstr r1, [r0, #0x18]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x00379ad0, 44)
extern "C" __attribute__((naked)) void func_00379ad0() {
    asm volatile("ldr r1, [r0, #0x70]\nldr r2, [r0, #0x6c]\ncmp r1, r2\naddlt r1, r1, #1\nstrlt r1, [r0, #0x70]\nldr r1, [r0, #0xac]\nldr r2, [r0, #0xa8]\ncmp r1, r2\naddlt r1, r1, #1\nstrlt r1, [r0, #0xac]\nbx lr\n");
}

// DECOMP_FUNC(0x00380884, 44)
extern "C" __attribute__((naked)) void func_00380884() {
    asm volatile("ldr r0, [r0, #0x190]\ncmp r0, #0\nmovne r0, #1\nbx lr\ncmp r0, #0\nmoveq r0, #4\nmovne r0, #2\nstrne r1, [r3, #0x450]\nstrb r0, [r3, #0x45c]\nstrne r2, [r3, #0x454]\nbx lr\n");
}
