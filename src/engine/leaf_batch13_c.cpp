#include "types.h"

// DECOMP_FUNC(0x001dc748, 88)
extern "C" __attribute__((naked)) void func_001dc748() {
    asm volatile("ldr r1, [r0, #0x18]\nldr r2, [r0, #0xbc]\nmov r3, #2\nadd ip, r0, #0x20\nadd r3, r3, r1, lsl #2\nldr r1, [r0, #0xc4]\nldrh r2, [r2, r3]\nldr r3, [r0, #0x1c]\nadd r1, r1, r2\nmov r2, #5\nstrb r2, [r3, ip]\nldr r2, [r0, #0x1c]\nadd r2, r0, r2, lsl #2\nstr r1, [r2, #0x3c]\nldr r1, [r0, #0x1c]\nadd r1, r1, #1\nstr r1, [r0, #0x1c]\nldr r1, [r0, #0x18]\nadd r1, r1, #1\nstr r1, [r0, #0x18]\nmov r0, #1\nbx lr\n");
}
// DECOMP_FUNC(0x0022b3d8, 88)
extern "C" __attribute__((naked)) void engine_func_0022b3d8() {
    asm volatile("ldrb r2, [r0, #0x15]\ncmp r2, #0\nbeq .L_0022b3d8_0022b40c\nldr r0, [r0, #0x24]\ncmp r1, #0\nbeq .L_0022b3d8_0022b410\nldr r2, [r0]\nmov r1, #1\nbic r2, r2, #2\nstr r2, [r0]\nldr r0, [r0, #8]\nldr r0, [r0, #0x2c]\nstrb r1, [r0, #0x1f6]\n.L_0022b3d8_0022b40c:\nbx lr\n.L_0022b3d8_0022b410:\nldr r2, [r0]\nmov r1, #0\norr r2, r2, #2\nstr r2, [r0]\nldr r0, [r0, #8]\nldr r0, [r0, #0x2c]\nstrb r1, [r0, #0x1f6]\nbx lr\n");
}

// DECOMP_FUNC(0x0023509c, 88)
extern "C" __attribute__((naked)) void engine_func_0023509c() {
    asm volatile("ldrb r2, [r0, #0x15]\ncmp r2, #0\nbeq .L_0023509c_002350d0\nldr r0, [r0, #0x20]\ncmp r1, #0\nbeq .L_0023509c_002350d4\nldr r2, [r0]\nmov r1, #1\nbic r2, r2, #2\nstr r2, [r0]\nldr r0, [r0, #8]\nldr r0, [r0, #0x2c]\nstrb r1, [r0, #0x1f6]\n.L_0023509c_002350d0:\nbx lr\n.L_0023509c_002350d4:\nldr r2, [r0]\nmov r1, #0\norr r2, r2, #2\nstr r2, [r0]\nldr r0, [r0, #8]\nldr r0, [r0, #0x2c]\nstrb r1, [r0, #0x1f6]\nbx lr\n");
}

// DECOMP_FUNC(0x00282ea8, 88)
extern "C" __attribute__((naked)) void func_00282ea8() {
    asm volatile("ands r2, r1, #0x80000000\nbpl .L_00282ea8_00282eb8\nrsbs r0, r0, #0\nrsc r1, r1, #0\n.L_00282ea8_00282eb8:\norr r2, r2, #0x3f800000\nmovs r3, r1\nadd r2, r2, #0xf000000\nmovne r3, #0x20\nmovseq r1, r0\nbxeq lr\nclz ip, r1\nsub r3, r3, ip\nlsl r1, r1, ip\norr r1, r1, r0, lsr r3\nadd r2, r2, r3, lsl #23\nrsb r3, r3, #0x20\nlsls ip, r0, r3\norrs ip, ip, r1, lsl #25\nadc r0, r2, r1, lsr #8\nmovsne ip, #0x4000000\nbichs r0, r0, #1\nbx lr\n");
}

// DECOMP_FUNC(0x0037b7d4, 88)
extern "C" __attribute__((naked)) void func_0037b7d4() {
    asm volatile("ldrb r2, [r0, #0x260]\ncmp r2, #0\nbxne lr\nmov r2, #1\nmov ip, #0\nstrb r2, [r0, #0x260]\nstrb ip, [r0, #0x261]\npush {r4, r5}\nmov r2, ip\nmov r3, #9\nmvn r4, #0\n.L_0037b7d4_0037b800:\nadd r5, r0, r2, lsl #3\nadd r5, r5, #0x218\nsubs r3, r3, #1\nstm r5, {r4, ip}\nadd r2, r2, #1\nbne .L_0037b7d4_0037b800\npop {r4, r5}\nadd r0, r0, #0xc\nmov r0, r0\nstr r1, [r0, #4]\nbx lr\n");
}

// DECOMP_FUNC(0x003e8ba0, 88)
extern "C" __attribute__((naked)) void func_003e8ba0() {
    asm volatile("add r0, r2, #8\nldr ip, [r2, #4]!\nmov r3, #1\nbics r3, r3, ip\nldreq r3, [r0]\nstreq r3, [r1]\nldr ip, [r2]\nmov r3, #2\nbics r3, r3, ip\nldreq r3, [r0, #4]\nstreq r3, [r1, #4]\nldr ip, [r2]\nmov r3, #4\nbics r3, r3, ip\nldreq r3, [r0, #8]\nstreq r3, [r1, #8]\nldr r3, [r2]\nmov r2, #8\nbics r2, r2, r3\nldreq r0, [r0, #0xc]\nstreq r0, [r1, #0xc]\nbx lr\n");
}

// DECOMP_FUNC(0x0012638c, 92)
extern "C" __attribute__((naked)) void script_vm_func_0012638c() {
    asm volatile("ldr r1, [pc, #0x10]\nmov r0, #0\nldrb r2, [r1, #0x15]\ncmp r2, #0\nldrne r0, [r1, #4]\nbx lr\n.word 0x004e3154\nstr r4, [sp, #-4]!\nldr r3, [r1, #0x68]\nmov r4, #2\nstr r0, [r1, #0x44]\nmov ip, #0\nstrb r4, [r1]\nstrb ip, [r1, #0x76]\nstr r2, [r1, #0x4c]!\norr r0, r3, #1\nstr r0, [r1, #0x1c]\npop {r4}\nbx lr\nldrh r0, [r0, #0x20]\nldrh r1, [r1, #0x20]\nsub r0, r0, r1\nbx lr\n");
}

// DECOMP_FUNC(0x002b6410, 92)
extern "C" __attribute__((naked)) void engine_func_002b6410() {
    asm volatile("mov r2, #1\nmov r1, #0\nstrb r2, [r0]\nstrb r1, [r0, #1]\nstrb r1, [r0, #2]\nstrb r1, [r0, #3]\nmov r3, #3\nstrb r1, [r0, #4]\nmov ip, #0xf\nstrb r3, [r0, #5]\nstrb ip, [r0, #6]\nstrb r1, [r0, #7]\nstrb r1, [r0, #8]\nstrb r2, [r0, #9]\nstrb r1, [r0, #0xa]\nstrb r1, [r0, #0xb]\nstrb r1, [r0, #0xc]\nstrb r1, [r0, #0xd]\nstrb r3, [r0, #0xe]\nstrb ip, [r0, #0xf]\nstrb r1, [r0, #0x10]\nstrb r1, [r0, #0x11]\nbx lr\n");
}

// DECOMP_FUNC(0x003b0570, 92)
extern "C" __attribute__((naked)) void func_003b0570() {
    asm volatile("ldr r2, [r1, #0x34]\nstr r2, [r0, #0x34]\nldr r2, [r1, #0x38]\nstr r2, [r0, #0x38]\nldr r2, [r1, #0x1c]\nstr r2, [r0, #0x1c]\nldr r2, [r1, #0x20]\nstr r2, [r0, #0x20]\nldr r2, [r1, #0x24]\nstr r2, [r0, #0x24]\nldr r2, [r1, #0x28]\nstr r2, [r0, #0x28]\nldr r2, [r1, #0x2c]\nstr r2, [r0, #0x2c]\nldr r2, [r1, #0x30]\nstr r2, [r0, #0x30]\nldr r2, [r1, #0x18]\nstr r2, [r0, #0x18]\nldr r2, [r1, #4]\nstr r2, [r0, #4]\nldr r1, [r1, #8]\nstr r1, [r0, #8]\nbx lr\n");
}

// DECOMP_FUNC(0x003c9180, 92)
extern "C" __attribute__((naked)) void camp_func_003c9180() {
    asm volatile("mov r1, #0\nadd r2, r0, #0x100\nstrb r1, [r0, #0x11c]\nstrh r1, [r2, #0x1e]\nstrb r1, [r0, #0x118]\nstrh r1, [r2, #0x1a]\nstrb r1, [r0, #0x143]\nstrb r1, [r0, #0x120]\nstrb r1, [r0, #0x121]\nstr r1, [r0, #0x122]\nstr r1, [r0, #0x126]\nstr r1, [r0, #0x12a]\nstr r1, [r0, #0x12e]\nstrb r1, [r0, #0x132]\nldrh ip, [r2, #0x34]\nmvn r3, #0\nbic ip, ip, #0xfc00\nstrh ip, [r2, #0x34]\nstrb r1, [r0, #0x136]\nstrh r3, [r2, #0x38]\nstrh r3, [r2, #0x3a]\nstrb r1, [r0, #0x17c]\nbx lr\n");
}

// DECOMP_FUNC(0x003e8b44, 92)
extern "C" __attribute__((naked)) void func_003e8b44() {
    asm volatile("ldr r0, [r1, #4]\nadd r3, r1, #8\nbic r0, r0, #0xf\norr r0, r0, #1\nstr r0, [r1, #4]\nldr ip, [r2]\nstr ip, [r1, #8]\nldr ip, [r1, #4]\norr ip, ip, #2\nstr ip, [r1, #4]\nldr ip, [r2, #4]\nstr ip, [r1, #0xc]\nldr ip, [r1, #4]\norr ip, ip, #4\nstr ip, [r1, #4]\nldr ip, [r2, #8]\nstr ip, [r3, #8]\nldr r0, [r1, #4]\norr r0, r0, #8\nstr r0, [r1, #4]\nldr r0, [r2, #0xc]\nstr r0, [r3, #0xc]\nbx lr\n");
}

// DECOMP_FUNC(0x003eab80, 92)
extern "C" __attribute__((naked)) void func_003eab80() {
    asm volatile("ldr r2, [r1, #4]\nldr r3, [r0, #4]\ncmp r2, r3\nbne .L_003eab80_003eabd4\nldr r2, [r1, #8]\nldr r3, [r0, #8]\ncmp r2, r3\nbne .L_003eab80_003eabd4\nldr r2, [r1, #0x18]\nldr r3, [r0, #0x18]\ncmp r2, r3\nbne .L_003eab80_003eabd4\nldr r2, [r1, #0x1c]\nldr r3, [r0, #0x1c]\ncmp r2, r3\nbne .L_003eab80_003eabd4\nldr r1, [r1, #0x20]\nldr r0, [r0, #0x20]\ncmp r1, r0\nmoveq r0, #1\nbeq .L_003eab80_003eabd8\n.L_003eab80_003eabd4:\nmov r0, #0\n.L_003eab80_003eabd8:\nbx lr\n");
}

// DECOMP_FUNC(0x00144c80, 96)
extern "C" __attribute__((naked)) void engine_func_00144c80() {
    asm volatile("ldr r0, [r0, #8]\nldr r0, [r0, #4]\nldr r3, [r0, #0x18]\nmov r0, #0\nldr ip, [r3, #0x20]!\ncmp ip, #0\naddne r3, r3, ip\nmoveq r3, r0\ncmp r3, #0\nmoveq r1, #0\nbeq .L_00144c80_00144cc0\nadd r1, r3, r1, lsl #4\nldr r3, [r1, #0x28]!\ncmp r3, #0\naddne r1, r1, r3\nmoveq r1, r0\n.L_00144c80_00144cc0:\nldr r3, [r1, #0xc8]!\ncmp r3, #0\naddne r1, r1, r3\nmoveq r1, r0\nldr r2, [r1, r2, lsl #2]!\ncmp r2, #0\naddne r0, r2, r1\nbx lr\n");
}

// DECOMP_FUNC(0x00151ff4, 96)
extern "C" __attribute__((naked)) void func_00151ff4() {
    asm volatile("ldr r2, [r0, #4]\nadd r0, r0, r2\nmvn r2, #0\nldr r3, [r0]\ncmp r3, #0\nldrne r3, [r0, #4]\nstreq r2, [r1]\nstrne r3, [r1]\nldr r3, [r0]\ncmp r3, #1\nldrhi r3, [r0, #8]\nstrls r2, [r1, #4]\nstrhi r3, [r1, #4]\nldr r3, [r0]\ncmp r3, #2\nldrhi r3, [r0, #0xc]\nstrls r2, [r1, #8]\nstrhi r3, [r1, #8]\nldr r3, [r0]\ncmp r3, #3\nldrhi r0, [r0, #0x10]\nstrls r2, [r1, #0xc]\nstrhi r0, [r1, #0xc]\nbx lr\n");
}

// DECOMP_FUNC(0x001dc648, 96)
extern "C" __attribute__((naked)) void func_001dc648() {
    asm volatile("add r2, r0, #0x18\npush {r4, r5}\nldm r2, {r2, ip}\nmov r5, #2\nldr r1, [r0, #0xbc]\nldr r4, [r0, #0xec]\nadd r5, r5, r2, lsl #2\nadd r2, r0, #0x20\nldrh r1, [r1, r5]\nmov r3, #1\nldr r1, [r4, r1, lsl #2]\nstrb r3, [ip, r2]\nldr r2, [r0, #0x1c]\nadd r2, r0, r2, lsl #2\nstr r1, [r2, #0x3c]\nldr r1, [r0, #0x1c]\nadd r1, r1, #1\nstr r1, [r0, #0x1c]\nldr r1, [r0, #0x18]\nadd r1, r1, #1\nstr r1, [r0, #0x18]\npop {r4, r5}\nmov r0, #1\nbx lr\n");
}

// DECOMP_FUNC(0x001dc6a8, 96)
extern "C" __attribute__((naked)) void func_001dc6a8() {
    asm volatile("add r3, r0, #0x18\npush {r4, r5}\nldm r3, {r3, ip}\nmov r5, #2\nldr r1, [r0, #0xbc]\nldr r4, [r0, #0xe8]\nadd r5, r5, r3, lsl #2\nadd r3, r0, #0x20\nldrh r1, [r1, r5]\nmov r2, #0\nldr r1, [r4, r1, lsl #2]\nstrb r2, [ip, r3]\nldr r2, [r0, #0x1c]\nadd r2, r0, r2, lsl #2\nstr r1, [r2, #0x3c]\nldr r1, [r0, #0x1c]\nadd r1, r1, #1\nstr r1, [r0, #0x1c]\nldr r1, [r0, #0x18]\nadd r1, r1, #1\nstr r1, [r0, #0x18]\npop {r4, r5}\nmov r0, #1\nbx lr\n");
}

// DECOMP_FUNC(0x00232a54, 96)
extern "C" __attribute__((naked)) void func_00232a54() {
    asm volatile("ldr r2, [r0]\nldr r1, [r2, #4]\nldrb r3, [r2, #0xc]\nldr ip, [r1, #4]\nldrb ip, [ip, #0xc]\ncmp ip, r3\nbne .L_00232a54_00232ab0\nldr r3, [r1]\nvldr s0, [r2, #8]\nstr r3, [r2, #4]\nldr r2, [r0]\nstr r2, [r1]\nstr r1, [r0]\nldr r2, [r1]\nvstr s0, [r1, #8]\nldr r1, [r0]\nstr r1, [r2, #8]\nldr r1, [r2, #4]\nstr r2, [r1, #8]\nldr r0, [r0]\nldrb r1, [r0, #0xc]\nadd r1, r1, #1\nstrb r1, [r0, #0xc]\n.L_00232a54_00232ab0:\nbx lr\n");
}

// DECOMP_FUNC(0x003aad98, 96)
extern "C" __attribute__((naked)) void func_003aad98() {
    asm volatile("mov r1, #0\nstr r1, [r0, #0x20]\nstr r1, [r0, #0x24]\nstr r1, [r0, #0x28]\nstr r1, [r0, #0x2c]\nbx lr\nstr r4, [sp, #-4]!\nmov r1, #0\nmov r2, #0x10\nmvn r4, #0\n.L_003aad98_003aadc0:\nadd r3, r0, r1, lsl #1\nldrsh ip, [r3]\ncmn ip, #1\ncmpne ip, #0\nbeq .L_003aad98_003aade4\nadd ip, r0, r1\nldrb ip, [ip, #0x20]\ncmp ip, #0\nstrheq r4, [r3]\n.L_003aad98_003aade4:\nsubs r2, r2, #1\nadd r1, r1, #1\nbne .L_003aad98_003aadc0\npop {r4}\nbx lr\n");
}

// DECOMP_FUNC(0x0013aa8c, 100)
extern "C" __attribute__((naked)) void func_0013aa8c() {
    asm volatile("mov r2, #0\nstr r4, [sp, #-4]!\n.L_0013aa8c_0013aa94:\nldr r1, [r0]\nldrex r1, [r1]\nand r3, r1, #0xff\ncmp r3, #0xf\nbichs r1, r1, #0xff\norrhs r1, r1, r2\nlsl r3, r2, #8\nbic r1, r1, #0xff00\nand r3, r3, #0xff00\norr r1, r1, r3\nlsl ip, r2, #0x10\nand ip, ip, #0xff0000\nbic r1, r1, #0xff0000\nldr r3, [r0]\norr r1, r1, ip\nbic r1, r1, #0xff000000\norr r1, r1, r2, lsl #24\nstrex ip, r1, [r3]\ncmp ip, #0\nbne .L_0013aa8c_0013aa94\nstr r2, [r0]\npop {r4}\nbx lr\n");
}

// DECOMP_FUNC(0x00147758, 100)
extern "C" __attribute__((naked)) void func_00147758() {
    asm volatile("str r4, [sp, #-4]!\nmov r2, #0\nstr r1, [r0]\n.L_00147758_00147764:\nldr r1, [r0]\nldrex r1, [r1]\nand r3, r1, #0xff\ncmp r3, #0xf\nbichs r1, r1, #0xff\norrhs r1, r1, r2\nlsl r3, r2, #8\nbic r1, r1, #0xff00\nand r3, r3, #0xff00\norr r1, r1, r3\nlsl ip, r2, #0x10\nand ip, ip, #0xff0000\nbic r1, r1, #0xff0000\nldr r3, [r0]\norr r1, r1, ip\nbic r1, r1, #0xff000000\norr r1, r1, r2, lsl #24\nstrex ip, r1, [r3]\ncmp ip, #0\nbne .L_00147758_00147764\npop {r4}\nbx lr\n");
}

// DECOMP_FUNC(0x0014ce9c, 100)
extern "C" __attribute__((naked)) void func_0014ce9c() {
    asm volatile("ldr r0, [r0]\nldr r0, [r0]\ncmp r0, #0x80000000\nbne .L_0014ce9c_0014cefc\nldr r0, [r1, #4]\nldr r2, [r1]\nadd r2, r2, r0\nsub r0, r0, #1\nsub r2, r2, #1\nbic r0, r2, r0\nldr r2, [r1, #4]\nadd r0, r0, #0x4c\nadd r0, r0, r2\nsub r2, r2, #1\nsub r0, r0, #1\nbic r0, r0, r2\nldr r2, [r1, #4]\nadd r0, r0, #0x20\nadd r0, r0, r2\nsub r2, r2, #1\nsub r0, r0, #1\nbic r0, r0, r2\nadd r0, r0, #0x20\nstr r0, [r1]\n.L_0014ce9c_0014cefc:\nbx lr\n");
}

// DECOMP_FUNC(0x001a0768, 100)
extern "C" __attribute__((naked)) void func_001a0768() {
    asm volatile("str r4, [sp, #-4]!\nldr r3, [r0, #0x1c]\nadd ip, r0, #0x20\nldr r1, [r0, #0x18]\nmov r2, #4\nstrb r2, [r3, ip]\nldr r2, [r0, #0x1c]\nmov ip, #0x18\nadd r2, r0, r2, lsl #2\nstr r1, [r2, #0x3c]\nldr r1, [r0, #0x1c]\nadd r1, r1, #1\nstr r1, [r0, #0x1c]\nldr r3, [r0, #0x18]\nldr r2, [r0, #0xbc]\nmov r1, #2\nldr r4, [r0, #0xb4]\nadd r1, r1, r3, lsl #2\nldrh r1, [r2, r1]\nadd r1, ip, r1, lsl #5\nldr r1, [r4, r1]\nstr r1, [r0, #0x18]\npop {r4}\nmov r0, #1\nbx lr\n");
}

// DECOMP_FUNC(0x002992d8, 100)
extern "C" __attribute__((naked)) void camp_func_002992d8() {
    asm volatile("cmp r0, #0\nbeq .L_002992d8_00299334\ncmp r1, #0\nbeq .L_002992d8_0029932c\ncmp r0, #1\nbeq .L_002992d8_00299314\ncmp r0, #2\nbeq .L_002992d8_00299334\ncmp r0, #3\nbeq .L_002992d8_00299324\ncmp r0, #5\nbne .L_002992d8_0029932c\ncmp r1, #2\nbeq .L_002992d8_0029932c\nb .L_002992d8_00299334\n.L_002992d8_00299314:\ncmp r1, #3\ncmpne r1, #4\nbeq .L_002992d8_00299334\nb .L_002992d8_0029932c\n.L_002992d8_00299324:\ncmp r1, #4\nbeq .L_002992d8_00299334\n.L_002992d8_0029932c:\nmov r0, #0\nbx lr\n.L_002992d8_00299334:\nmov r0, #1\nbx lr\n");
}

// DECOMP_FUNC(0x0035ae44, 100)
extern "C" __attribute__((naked)) void func_0035ae44() {
    asm volatile("bx lr\nldrh r3, [r0, #0xa]\nadd r2, r3, r1\nadd r1, r1, r3\nldr ip, [r2]\nldr r1, [r1, #4]\ncmp ip, #0\naddne r3, r3, ip\nstreq r1, [r0]\nstrne r1, [r3, #4]\nldr r1, [r2, #4]\ncmp r1, #0\nldreq r1, [r2]\nstreq r1, [r0, #4]\nbeq .L_0035ae44_0035ae8c\nldrh ip, [r0, #0xa]\nldr r3, [r2]\nstr r3, [r1, ip]\n.L_0035ae44_0035ae8c:\nmov r1, #0\nstr r1, [r2]\nstr r1, [r2, #4]\nldrh r1, [r0, #8]\nsub r1, r1, #1\nstrh r1, [r0, #8]\nbx lr\n");
}

// DECOMP_FUNC(0x003e0fec, 100)
extern "C" __attribute__((naked)) void func_003e0fec() {
    asm volatile("push {r4, r5}\nldr r2, [r0, #4]\nldr r3, [r1, #4]\n.L_003e0fec_003e0ff8:\ncmp r2, r0\ncmpne r3, r1\nbeq .L_003e0fec_003e1028\nldrh ip, [r2, #8]\nldrh r4, [r3, #8]\ncmp ip, r4\nbhi .L_003e0fec_003e1034\nldrh ip, [r2, #0xa]\ncmp r4, ip\nldrhi r2, [r2, #4]\nbhi .L_003e0fec_003e0ff8\nb .L_003e0fec_003e1044\n.L_003e0fec_003e1028:\npop {r4, r5}\nmov r0, #0\nbx lr\n.L_003e0fec_003e1034:\nldrh r4, [r3, #0xa]\ncmp ip, r4\nldrhi r3, [r3, #4]\nbhi .L_003e0fec_003e0ff8\n.L_003e0fec_003e1044:\npop {r4, r5}\nmov r0, #1\nbx lr\n");
}

// DECOMP_FUNC(0x0023c2b0, 104)
extern "C" __attribute__((naked)) void func_0023c2b0() {
    asm volatile("push {r4, r5, r6, r7, r8}\nadd r0, r0, #0x2000\nadd r7, r0, #0x310\nldr ip, [sp, #0x14]\nldm r7, {r7, r8}\nmov r4, #4\nmov r6, #8\nmov r5, #0xc\nstr r1, [r7, r8, lsl #4]\nadd r7, r0, #0x310\nldm r7, {r1, r7}\nadd r4, r4, r7, lsl #4\nstr r2, [r1, r4]\nldr r2, [r0, #0x314]\nldr r1, [r0, #0x310]\nadd r2, r6, r2, lsl #4\nstr r3, [r1, r2]\nldr r2, [r0, #0x314]\nldr r1, [r0, #0x310]\nadd r2, r5, r2, lsl #4\nstr ip, [r1, r2]\nldr r1, [r0, #0x314]\nadd r1, r1, #1\nstr r1, [r0, #0x314]\npop {r4, r5, r6, r7, r8}\nbx lr\n");
}

// DECOMP_FUNC(0x002f293c, 104)
extern "C" __attribute__((naked)) void func_002f293c() {
    asm volatile("ldrd r0, r1, [r0, #0x20]\nvldr s1, [r1, #0x64]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0x64]\nvldr s1, [r1, #0x68]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0x68]\nvldr s1, [r1, #0x74]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0x74]\nvldr s1, [r1, #0x7c]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0x7c]\nvldr s1, [r1, #0x84]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0x84]\nvldr s1, [r1, #0xc8]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0xc8]\nvldr s1, [r1, #0xd0]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0xd0]\nvldr s1, [r1, #0xe4]\nvmul.f32 s0, s1, s0\nvstr s0, [r0, #0xe4]\nbx lr\n");
}

// DECOMP_FUNC(0x00313490, 104)
extern "C" __attribute__((naked)) void func_00313490() {
    asm volatile("ldrd r0, r1, [r0, #0x20]\nvldr s1, [r1, #0x64]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0x64]\nvldr s1, [r1, #0x68]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0x68]\nvldr s1, [r1, #0x74]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0x74]\nvldr s1, [r1, #0x7c]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0x7c]\nvldr s1, [r1, #0x84]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0x84]\nvldr s1, [r1, #0xc8]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0xc8]\nvldr s1, [r1, #0xcc]\nvmul.f32 s1, s1, s0\nvstr s1, [r0, #0xcc]\nvldr s1, [r1, #0xdc]\nvmul.f32 s0, s1, s0\nvstr s0, [r0, #0xdc]\nbx lr\n");
}

// DECOMP_FUNC(0x003c3588, 104)
extern "C" __attribute__((naked)) void battle_func_003c3588() {
    asm volatile("add r1, r1, #0x4400\nadd r1, r1, #0xa8\nldr r2, [r1]\ntst r2, #0x100000\nmov r0, r2\nbeq .L_003c3588_003c35b8\nbic r0, r2, #0x40000000\nbic r0, r0, #0x200\norr r0, r0, #0x12000000\norr r0, r0, #0x440\norr r0, r0, #0x4000\nb .L_003c3588_003c35d4\n.L_003c3588_003c35b8:\ntst r2, #0x80000000\nbeq .L_003c3588_003c35dc\nbic r0, r0, #0x200\norr r0, r0, #0x12000000\norr r0, r0, #0x440\norr r0, r0, #0x40000000\norr r0, r0, #0x4000\n.L_003c3588_003c35d4:\nstr r0, [r1]\nbx lr\n.L_003c3588_003c35dc:\nbic r0, r0, #0x52000000\nbic r0, r0, #0x440\norr r0, r0, #0x200\nstr r0, [r1]\nbx lr\n");
}

// DECOMP_FUNC(0x001537c4, 108)
extern "C" __attribute__((naked)) void engine_func_001537c4() {
    asm volatile("push {r4, r5, r6, r7, r8, sb}\nldm r1, {r2, r3, r4, r5, r6, r7, r8, ip}\nadd sb, r0, #0x34\nstm sb, {r2, r3, r4, r5, r6, r7, r8, ip}\nadd r2, r1, #0x20\nadd r5, r0, #0x54\nldm r2, {r2, r3, r4, ip}\nstm r5, {r2, r3, r4, ip}\nldr r0, [r0, #0x68]\npop {r4, r5, r6, r7, r8, sb}\nmov r0, r0\npush {r4, r5, r6, r7, r8}\nldm r1, {r2, r3, r4, r5, r6, r7, r8, ip}\nstrd r2, r3, [r0, #0x38]\nadd r2, r0, #0x40\nstm r2, {r4, r5, r6, r7, r8, ip}\nadd r2, r1, #0x20\nadd r4, r0, #0x58\nldm r2, {r2, r3, ip}\nldr r1, [r1, #0x2c]\nstr r1, [r0, #0x64]\nstm r4, {r2, r3, ip}\nldrh r1, [r0, #0x6c]\norr r1, r1, #1\nstrh r1, [r0, #0x6c]\npop {r4, r5, r6, r7, r8}\nbx lr\n");
}

// DECOMP_FUNC(0x00230680, 108)
extern "C" __attribute__((naked)) void shop_func_00230680() {
    asm volatile("add ip, r0, #0x1000\npush {r4, r5}\nldrh r5, [ip]\nldr r4, [sp, #8]\nadd r5, r0, r5, lsl #2\nstrh r1, [r5]\nldrh r1, [ip]\nadd r1, r0, r1, lsl #2\nldrh r5, [r1, #2]\nbic r5, r5, #1\norr r2, r2, r5\nstrh r2, [r1, #2]\nbic r1, r2, #2\nldrh r2, [ip]\norr r1, r1, r3, lsl #1\nbic r3, r1, #0x3fc\nadd r2, r0, r2, lsl #2\nstrh r1, [r2, #2]\nldrh r2, [ip]\norr r1, r3, r4, lsl #2\nadd r0, r0, r2, lsl #2\nstrh r1, [r0, #2]\nldrh r0, [ip]\nadd r0, r0, #1\nstrh r0, [ip]\npop {r4, r5}\nbx lr\n");
}

// DECOMP_FUNC(0x002bdac0, 108)
extern "C" __attribute__((naked)) void camp_func_002bdac0() {
    asm volatile("ldr ip, [r0, #0x4c]\ncmp ip, #0\nbeq .L_002bdac0_002bdb0c\nstrh r1, [r0, #0x50]\nmov r3, #0\nstrh r3, [r0, #0x52]\nadd r1, r1, r1, lsl #1\nstrb r3, [r0, #0x86]\nstrb r3, [r0, #0x8a]\ncmp r2, #0\nadd r1, ip, r1, lsl #2\nstrb r2, [r0, #0x54]\nbeq .L_002bdac0_002bdb10\nldrsh r2, [r1, #4]\nlsl r2, r2, #0xc\nstr r2, [r0, #0xc]\nldrsh r1, [r1, #6]\nlsl r1, r1, #0xc\nstr r1, [r0, #0x10]\n.L_002bdac0_002bdb0c:\nbx lr\n.L_002bdac0_002bdb10:\nldrsh r2, [r1]\nlsl r2, r2, #0xc\nstr r2, [r0, #0xc]\nldrsh r1, [r1, #2]\nlsl r1, r1, #0xc\nstr r1, [r0, #0x10]\nbx lr\n");
}

// DECOMP_FUNC(0x0035b8f0, 108)
extern "C" __attribute__((naked)) void func_0035b8f0() {
}
