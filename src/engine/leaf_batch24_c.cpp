#include "types.h"

extern "C" void AsdList_func_002b2814();
extern "C" void AsdMdlManager_func_002a135c();
extern "C" void AsdMdlManager_func_002b2928();
extern "C" void AsdMemory_func_002c23f8();
extern "C" void AsdModel_func_002a94e8();
extern "C" void AsdModel_func_002b2b78();
extern "C" void AsdModel_func_0031dc4c();
extern "C" void Tbb_GetGlobalSubTable();
extern "C" void Tbb_GetPayloadData();
extern "C" void Tbb_GetRowCount();
extern "C" void battle_func_00201040();
extern "C" void battle_func_00220458();
extern "C" void battle_func_002459c0();
extern "C" void battle_func_002461ec();
extern "C" void battle_func_002465c0();
extern "C" void battle_func_00246ea4();
extern "C" void battle_func_00246f90();
extern "C" void battle_func_00250800();
extern "C" void battle_func_002553ec();
extern "C" void battle_func_00267f68();
extern "C" void battle_func_0028df54();
extern "C" void battle_func_002b087c();
extern "C" void battle_func_002bf41c();
extern "C" void battle_func_002bf8d4();
extern "C" void battle_func_002c45b8();
extern "C" void battle_func_003de7fc();
extern "C" void camp_func_0024ec64();
extern "C" void camp_func_002631c0();
extern "C" void camp_func_0029c468();
extern "C" void camp_func_0029c49c();
extern "C" void camp_func_0029c68c();
extern "C" void camp_func_0029ee4c();
extern "C" void camp_func_002a0640();
extern "C" void camp_func_002a89e4();
extern "C" void camp_func_002a8a08();
extern "C" void camp_func_002b9364();
extern "C" void camp_func_002bdac0();
extern "C" void camp_func_002bf030();
extern "C" void camp_func_002bf6d0();
extern "C" void camp_func_002c4450();
extern "C" void effParts_func_0025cc14();
extern "C" void engine_func_001db718();
extern "C" void engine_func_00219ec8();
extern "C" void engine_func_0024736c();
extern "C" void engine_func_002487e4();
extern "C" void engine_func_00259510();
extern "C" void engine_func_0025c110();
extern "C" void engine_func_00286928();
extern "C" void engine_func_00289640();
extern "C" void engine_func_00296f60();
extern "C" void engine_func_002a65a8();
extern "C" void engine_func_002a671c();
extern "C" void engine_func_002a691c();
extern "C" void engine_func_002b47cc();
extern "C" void engine_func_002c0bcc();
extern "C" void engine_func_002c2cf0();
extern "C" void engine_func_002c31bc();
extern "C" void engine_func_002c34a4();
extern "C" void engine_func_002c4360();
extern "C" void engine_func_002c4b30();
extern "C" void engine_func_002c583c();
extern "C" void engine_func_002d3e14();
extern "C" void engine_func_00326bcc();
extern "C" void engine_func_00326e04();
extern "C" void engine_func_0032814c();
extern "C" void engine_func_00328bd4();
extern "C" void engine_func_00328c0c();
extern "C" void engine_func_0038a184();
extern "C" void func_00245318();
extern "C" void func_00245908();
extern "C" void func_00246554();
extern "C" void func_00250960();
extern "C" void func_0028686c();
extern "C" void func_00288ad4();
extern "C" void func_002b06a0();
extern "C" void func_002b8574();
extern "C" void func_002c3714();
extern "C" void func_002c8b0c();
extern "C" void func_002f3aac();
extern "C" void func_0031ec60();
extern "C" void func_00338294();
extern "C" void func_003946ac();
extern "C" void func_003af2d0();
extern "C" void func_003c0a90();
extern "C" void nn_sdk_func_003550f0();
extern "C" void saveLoadUI_Calc();
extern "C" void script_vm_func_00242a80();
extern "C" void script_vm_func_0024c828();
extern "C" void script_vm_func_00255198();
extern "C" void script_vm_func_0026ca8c();
extern "C" void script_vm_func_00270298();
extern "C" void script_vm_func_00276580();
extern "C" void script_vm_func_0027eb98();
extern "C" void script_vm_func_002897fc();
extern "C" void script_vm_func_00289924();
extern "C" void script_vm_func_002954cc();
extern "C" void script_vm_func_00295eac();
extern "C" void script_vm_func_00296020();
extern "C" void script_vm_func_002a755c();
extern "C" void script_vm_func_002b91c4();
extern "C" void script_vm_func_002c0ba8();
extern "C" void script_vm_func_002dfcf4();
extern "C" void ui_func_002462a0();
extern "C" void ui_func_002473ac();
extern "C" void ui_func_00282b94();
extern "C" void ui_func_00293c98();
extern "C" void ui_func_002a63f8();
extern "C" void ui_func_002adb40();
extern "C" void ui_func_002c0a6c();
extern "C" void ui_func_002c0ac8();
extern "C" void ui_func_002c17d4();
extern "C" void ui_func_002c615c();
extern "C" void ui_func_002d18c8();

// DECOMP_FUNC(0x00300014, 280)
extern "C" __attribute__((naked)) void ui_func_00300014() {
    asm volatile(
        "push {r4, r5, r6, r7, lr}\n"
        "sub sp, sp, #0x54\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "mov r0, #1\n"
        "bl engine_func_00296f60\n"
        "mov r5, r0\n"
        "ldr r0, [pc, #0xe8]\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0027eb98\n"
        "mov r6, r0\n"
        "bl ui_func_00293c98\n"
        "mov r1, r4\n"
        "bl ui_func_00282b94\n"
        "mov r4, r0\n"
        "bl ui_func_00293c98\n"
        "bl func_00250960\n"
        "bl ui_func_00293c98\n"
        "ldrsh r2, [r4, #8]\n"
        "add r1, r0, #0x1c00\n"
        "add r1, r1, #0x298\n"
        "mov r0, #1\n"
        "ldr r1, [r1]\n"
        "add r3, r2, r2, lsl #2\n"
        "add r2, r3, r2, lsl #6\n"
        "mov r7, #0\n"
        "add r2, r1, r2, lsl #2\n"
        "add r1, sp, #0x48\n"
        "str r0, [sp, #0x44]\n"
        "stm r1, {r0, r7}\n"
        "add r1, sp, #0x3c\n"
        "str r0, [sp, #0x50]\n"
        "str r7, [sp, #0x34]\n"
        "str r7, [sp, #0x38]\n"
        "stm r1, {r0, r7}\n"
        "add r1, sp, #0x24\n"
        "stm r1, {r0, r7}\n"
        "add r0, r4, #0x100\n"
        "str r7, [sp, #0x2c]\n"
        "str r7, [sp, #0x30]\n"
        "str r7, [sp, #0x14]\n"
        "str r7, [sp, #0x18]\n"
        "str r7, [sp, #0x1c]\n"
        "str r7, [sp, #0x20]\n"
        "ldrsh r3, [r0, #0xb6]\n"
        "ldrsh r0, [r0, #0xb4]\n"
        "mvn r1, #0\n"
        "add r4, sp, #0xc\n"
        "str r1, [sp, #4]\n"
        "str r1, [sp, #8]\n"
        "str r5, [sp]\n"
        "stm r4, {r0, r3}\n"
        "mov r3, #0\n"
        "mov r1, r6\n"
        "mov r0, r3\n"
        "bl battle_func_002553ec\n"
        "mov r3, #0\n"
        "ldr r2, [pc, #0x24]\n"
        "mov r1, r6\n"
        "mov r0, r3\n"
        "str r7, [sp]\n"
        "str r7, [sp, #4]\n"
        "str r7, [sp, #8]\n"
        "bl battle_func_00250800\n"
        "add sp, sp, #0x54\n"
        "mov r0, #1\n"
        "pop {r4, r5, r6, r7, pc}\n"
        ".word 0x0043427c\n"
        ".word 0x01000185\n"
    );
}

// DECOMP_FUNC(0x00300310, 100)
extern "C" __attribute__((naked)) void ui_func_00300310() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r6, r0\n"
        "bl ui_func_00293c98\n"
        "mov r4, r0\n"
        "ldr r0, [pc, #0x40]\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0027eb98\n"
        "mov r5, r0\n"
        "mov r1, r6\n"
        "mov r0, r4\n"
        "bl ui_func_00282b94\n"
        "mov r2, r0\n"
        "mov r1, r5\n"
        "mov r0, #0\n"
        "bl battle_func_002465c0\n"
        "add r1, r4, #0x4000\n"
        "add r1, r1, #0x4a0\n"
        "mov r0, #1\n"
        "ldr r2, [r1]\n"
        "orr r2, r2, #0x10000\n"
        "str r2, [r1]\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x00300374, 328)
extern "C" __attribute__((naked)) void battle_func_00300374() {
    asm volatile(
        "push {r4, r5, r6, r7, r8, sb, lr}\n"
        "sub sp, sp, #0xc\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r5, r0\n"
        "mov r0, #1\n"
        "bl engine_func_00296f60\n"
        "mov r6, r0\n"
        "mov r0, #2\n"
        "bl engine_func_00296f60\n"
        "mov r7, r0\n"
        "ldr r0, [pc, #0x104]\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0027eb98\n"
        "mov r8, r0\n"
        "bl ui_func_00293c98\n"
        "cmp r6, #0\n"
        "mov r4, r0\n"
        "mov sb, #1\n"
        "beq .L_0030043c\n"
        "cmp r7, #0\n"
        "mov r6, #0\n"
        "beq .L_00300460\n"
        "mov r0, r5\n"
        "bl func_00246554\n"
        "mov r1, r0\n"
        "mvn r3, #0\n"
        "mov r2, #2\n"
        "mov r0, #0\n"
        "bl ui_func_002462a0\n"
        "tst r0, #0x10000\n"
        "beq .L_00300460\n"
        "mov r0, #4\n"
        "add r4, r4, #0x1c00\n"
        "add r4, r4, #0x298\n"
        "str r0, [sp]\n"
        "mov r1, #0\n"
        "ldr r3, [r4]\n"
        "mov r2, r8\n"
        "mov r0, r1\n"
        "bl battle_func_002461ec\n"
        "mov r3, #0\n"
        "ldr r2, [pc, #0x8c]\n"
        "mov r1, r8\n"
        "mov r0, r3\n"
        "str r6, [sp, #4]\n"
        "str sb, [sp]\n"
        "str r6, [sp, #8]\n"
        "bl battle_func_00250800\n"
        "b .L_003004a0\n"
        ".L_0030043c:\n"
        "ldr r4, [pc, #0x70]\n"
        "lsl r3, sb, r5\n"
        "mov r1, r8\n"
        "ldr r2, [r4, r0]\n"
        "mov r0, #0\n"
        "bl battle_func_00246ea4\n"
        "nop \n"
        "nop \n"
        "b .L_003004a0\n"
        ".L_00300460:\n"
        "add r4, r4, #0x1c00\n"
        "add r4, r4, #0x298\n"
        "lsl r3, sb, r5\n"
        "str sb, [sp]\n"
        "ldr r2, [r4]\n"
        "mov r1, r8\n"
        "mov r0, #0\n"
        "bl battle_func_00246f90\n"
        "mov r3, #0\n"
        "ldr r2, [pc, #0x2c]\n"
        "mov r1, r8\n"
        "mov r0, r3\n"
        "str r6, [sp]\n"
        "str r6, [sp, #4]\n"
        "str r6, [sp, #8]\n"
        "bl battle_func_00250800\n"
        ".L_003004a0:\n"
        "add sp, sp, #0xc\n"
        "mov r0, #1\n"
        "pop {r4, r5, r6, r7, r8, sb, pc}\n"
        ".word 0x0043427c\n"
        ".word 0x010001ea\n"
        ".word 0x00001e98\n"
        ".word 0x010001bd\n"
    );
}

// DECOMP_FUNC(0x00302458, 60)
extern "C" __attribute__((naked)) void engine_func_00302458() {
    asm volatile(
        "ldr r1, [pc, #0x30]\n"
        "mov r0, #0\n"
        "add r2, r1, #0x14\n"
        "str r0, [r1]\n"
        "str r0, [r2]\n"
        "str r0, [r1, #4]\n"
        "str r0, [r2, #4]\n"
        "str r0, [r1, #8]\n"
        "str r0, [r2, #8]\n"
        "str r0, [r1, #0xc]\n"
        "str r0, [r2, #0xc]\n"
        "str r0, [r1, #0x10]\n"
        "str r0, [r2, #0x10]\n"
        "bx lr\n"
        ".word 0x004ea7d4\n"
    );
}

// DECOMP_FUNC(0x00303aac, 28)
extern "C" __attribute__((naked)) void func_00303aac() {
    asm volatile(
        "ldr r0, [r0, #0x3c]\n"
        "ldr r1, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "ldr r1, [r1]\n"
        "str r1, [r0, #0x50]\n"
        "bx lr\n"
        ".word 0x00472560\n"
    );
}

// DECOMP_FUNC(0x00304128, 28)
extern "C" __attribute__((naked)) void func_00304128() {
    asm volatile(
        "ldr r0, [r0, #0x3c]\n"
        "ldr r1, [pc, #0xc]\n"
        "ldr r0, [r0]\n"
        "ldr r1, [r1]\n"
        "str r1, [r0, #0x50]\n"
        "bx lr\n"
        ".word 0x00472560\n"
    );
}

// DECOMP_FUNC(0x00306500, 160)
extern "C" __attribute__((naked)) void effPolygonWind_func_00306500() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r1, #0xc\n"
        "ldr r6, [r0, #0x3c]!\n"
        "sub sp, sp, #8\n"
        "ldr r4, [r0, #4]\n"
        "ldr r0, [r4, #0x38]\n"
        "add r2, r0, r0, lsl #1\n"
        "add r0, r2, r0, lsl #3\n"
        "add r5, r1, r0, lsl #2\n"
        "ldr r1, [pc, #0x6c]\n"
        "ldr r0, [pc, #0x6c]\n"
        "mov r0, r0\n"
        "mov r1, #1\n"
        "mov r0, #0x10\n"
        "strd r0, r1, [sp]\n"
        "mov r3, r5\n"
        "mov r2, #0\n"
        "mov r1, #0x100\n"
        "mov r0, #0x10000\n"
        "bl engine_func_002c34a4\n"
        "add r1, r0, #0xc\n"
        "str r1, [r0]\n"
        "str r0, [r0, #8]\n"
        "ldr r1, [r4, #0x8c]\n"
        "mov r5, r0\n"
        "cmp r1, #3\n"
        "movls r1, #3\n"
        "str r1, [r4, #0x8c]\n"
        "ldr r0, [r6, #4]\n"
        "bl engine_func_00219ec8\n"
        "mov r1, r0\n"
        "str r1, [r5, #4]\n"
        "mov r0, r5\n"
        "mov r1, r4\n"
        "bl engine_func_00326bcc\n"
        "add sp, sp, #8\n"
        "mov r0, r5\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x00000411\n"
        ".word 0x004102fc\n"
    );
}

// DECOMP_FUNC(0x00307340, 152)
extern "C" __attribute__((naked)) void effPolygonWind_func_00307340() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r1, #0xc\n"
        "ldr r6, [r0, #0x3c]!\n"
        "sub sp, sp, #8\n"
        "ldr r4, [r0, #4]\n"
        "ldr r0, [r4, #0x38]\n"
        "add r0, r0, r0, lsl #1\n"
        "add r5, r1, r0, lsl #4\n"
        "ldr r0, [pc, #0x6c]\n"
        "mov r1, #0x5a\n"
        "mov r0, r0\n"
        "mov r1, #1\n"
        "mov r0, #0x10\n"
        "strd r0, r1, [sp]\n"
        "mov r3, r5\n"
        "mov r2, #0\n"
        "mov r1, #0x100\n"
        "mov r0, #0x10000\n"
        "bl engine_func_002c34a4\n"
        "add r1, r0, #0xc\n"
        "str r1, [r0]\n"
        "str r0, [r0, #8]\n"
        "ldr r1, [r4, #0x8c]\n"
        "mov r5, r0\n"
        "cmp r1, #3\n"
        "movls r1, #3\n"
        "str r1, [r4, #0x8c]\n"
        "ldr r0, [r6, #4]\n"
        "bl engine_func_00219ec8\n"
        "mov r1, r0\n"
        "str r1, [r5, #4]\n"
        "mov r0, r5\n"
        "mov r1, r4\n"
        "bl engine_func_00326e04\n"
        "add sp, sp, #8\n"
        "mov r0, r5\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x004102fc\n"
    );
}

// DECOMP_FUNC(0x0030947c, 252)
extern "C" __attribute__((naked)) void ui_func_0030947c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, #1\n"
        "ldr r6, [pc, #0xe4]\n"
        "ldr r4, [r6]\n"
        "vldr s0, [r4, #0x64]\n"
        "vldr s1, [r4, #0x148]\n"
        "vcmpe.f32 s0, s1\n"
        "vmrs apsr_nzcv, fpscr\n"
        "strblo r5, [r4, #0x128]\n"
        "strblo r5, [r4, #0x75c]\n"
        "blo .L_003094ec\n"
        "ldr r1, [r4, #0x758]\n"
        "mov r0, #0\n"
        "mov r2, #0xc\n"
        "add r1, r1, #1\n"
        "str r1, [r4, #0x758]\n"
        ".L_003094bc:\n"
        "add r1, r4, r0, lsl #3\n"
        "vldr s1, [r4, #0x150]\n"
        "vldr s0, [r1, #0xc]\n"
        "subs r2, r2, #1\n"
        "add r0, r0, #1\n"
        "vsub.f32 s0, s0, s1\n"
        "vstr s0, [r1, #0xc]\n"
        "vldr s1, [r4, #0x150]\n"
        "vldr s0, [r1, #0x6c]\n"
        "vsub.f32 s0, s0, s1\n"
        "vstr s0, [r1, #0x6c]\n"
        "bne .L_003094bc\n"
        ".L_003094ec:\n"
        "mov r0, #9\n"
        "bl ui_func_002c17d4\n"
        "cmp r0, #0\n"
        "nop \n"
        "bne .L_00309514\n"
        "mov r0, #6\n"
        "bl ui_func_002c17d4\n"
        "cmp r0, #0\n"
        "nop \n"
        "beq .L_00309530\n"
        ".L_00309514:\n"
        "ldrb r0, [r4, #0x128]\n"
        "cmp r0, #0\n"
        "bne .L_00309530\n"
        "ldr r0, [pc, #0x4c]\n"
        "bl script_vm_func_002c0ba8\n"
        "cmp r0, #0\n"
        "strbne r5, [r4, #0x128]\n"
        ".L_00309530:\n"
        "ldrb r0, [r4, #0x75c]\n"
        "cmp r0, #0\n"
        "ldrb r0, [r4, #0x128]\n"
        "beq .L_00309558\n"
        "cmp r0, #0\n"
        "beq .L_00309554\n"
        "ldr r1, [r6]\n"
        "mov r0, #6\n"
        "str r0, [r1, #0x14c]\n"
        ".L_00309554:\n"
        "pop {r4, r5, r6, pc}\n"
        ".L_00309558:\n"
        "cmp r0, #0\n"
        "beq .L_00309554\n"
        "ldr r1, [r6]\n"
        "mov r0, #3\n"
        "str r0, [r1, #0x14c]\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x00432cc8\n"
        ".word 0x00000565\n"
    );
}

// DECOMP_FUNC(0x00309a24, 320)
extern "C" __attribute__((naked)) void script_vm_func_00309a24() {
    asm volatile(
        "push {r4, r5, r6, r7, r8, lr}\n"
        "mov r6, r0\n"
        "mov r4, r2\n"
        "mov r5, r3\n"
        "vpush {d8}\n"
        "sub sp, sp, #8\n"
        "add r0, sp, #0x28\n"
        "vldr s16, [sp, #0x30]\n"
        "ldm r0, {r7, r8}\n"
        "ands r0, r6, #0x80000000\n"
        "bpl .L_00309b4c\n"
        "and r0, r6, #0x3fc00\n"
        "lsr r1, r0, #0xa\n"
        "lsl r0, r6, #0x16\n"
        "cmp r1, #0x11\n"
        "lsr r0, r0, #0x16\n"
        "bne .L_00309ab4\n"
        "cmp r0, #0x64\n"
        "blt .L_00309ab4\n"
        "cmp r0, #0xb3\n"
        "mov r2, r0\n"
        "bgt .L_00309ab4\n"
        "cmp r2, #0x82\n"
        "bge .L_00309b4c\n"
        ".L_00309a84:\n"
        "vstr s16, [sp]\n"
        "mov r3, r8\n"
        "mov r2, r7\n"
        "mov r0, r4\n"
        "mov r1, r5\n"
        "bl engine_func_001db718\n"
        "mov r6, r0\n"
        "nop \n"
        "bl func_002c3714\n"
        "nop \n"
        "nop \n"
        "b .L_00309b4c\n"
        ".L_00309ab4:\n"
        "cmp r1, #0x11\n"
        "bne .L_00309af4\n"
        "cmp r0, #0x154\n"
        "blt .L_00309af4\n"
        "cmp r0, #0x168\n"
        "bge .L_00309af4\n"
        "mov r0, r4\n"
        "mov r1, r3\n"
        "bl nn_sdk_func_003550f0\n"
        "mov r6, r0\n"
        "nop \n"
        "bl func_002c3714\n"
        "ands r0, r6, #0x80000000\n"
        "nop \n"
        "bmi .L_00309b4c\n"
        "b .L_00309a84\n"
        ".L_00309af4:\n"
        "cmp r1, #0x11\n"
        "bne .L_00309b10\n"
        "cmp r0, #0x168\n"
        "blt .L_00309b10\n"
        "ldr r3, [pc, #0x50]\n"
        "cmp r0, r3\n"
        "ble .L_00309b4c\n"
        ".L_00309b10:\n"
        "cmp r1, #0x11\n"
        "bne .L_00309b4c\n"
        "ldr r2, [pc, #0x40]\n"
        "cmp r2, r0\n"
        "cmple r0, #0x190\n"
        "bge .L_00309b4c\n"
        "mov r0, r4\n"
        "mov r1, r5\n"
        "bl nn_sdk_func_003550f0\n"
        "mov r6, r0\n"
        "nop \n"
        "bl func_002c3714\n"
        "ands r0, r6, #0x80000000\n"
        "nop \n"
        "bpl .L_00309a84\n"
        ".L_00309b4c:\n"
        "add sp, sp, #8\n"
        "mov r0, r6\n"
        "vpop {d8}\n"
        "pop {r4, r5, r6, r7, r8, pc}\n"
        ".word 0x00000185\n"
        ".word 0x00000186\n"
    );
}

// DECOMP_FUNC(0x00309b64, 40)
extern "C" __attribute__((naked)) void engine_func_00309b64() {
    asm volatile(
        "ldr r0, [pc, #0x1c]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "beq .L_00309b84\n"
        "ldr r0, [r0, #0x5ec]\n"
        "cmp r0, #5\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        ".L_00309b84:\n"
        "bx lr\n"
        ".word 0x0043dfc0\n"
    );
}

// DECOMP_FUNC(0x0030a09c, 28)
extern "C" __attribute__((naked)) void func_0030a09c() {
    asm volatile(
        "add r1, r0, r0, lsl #3\n"
        "add r0, r1, r0, lsl #5\n"
        "ldr r1, [pc, #8]\n"
        "add r0, r1, r0, lsl #3\n"
        "ldr r0, [r0, #0x28]\n"
        "bx lr\n"
        ".word 0x00478000\n"
    );
}

// DECOMP_FUNC(0x0030a428, 112)
extern "C" __attribute__((naked)) void engine_func_0030a428() {
    asm volatile(
        "push {r3, r4, r5, lr}\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "bl ui_func_002c0ac8\n"
        "ldr r4, [r0]\n"
        "mov r0, #1\n"
        "bl engine_func_00296f60\n"
        "mov r5, r0\n"
        "mvn r0, #0\n"
        "mov r3, #1\n"
        "str r0, [sp]\n"
        "mov r2, r3\n"
        "mov r1, r5\n"
        "mov r0, r4\n"
        "bl battle_func_002bf8d4\n"
        "ldr r0, [pc, #0x24]\n"
        "bl script_vm_func_002c0ba8\n"
        "cmp r0, #0\n"
        "beq .L_0030a488\n"
        "ldr r0, [pc, #0x18]\n"
        "mov r1, #1\n"
        "str r1, [r0, #4]\n"
        "str r5, [r0]\n"
        "str r1, [r0, #8]\n"
        ".L_0030a488:\n"
        "mov r0, #1\n"
        "pop {r3, r4, r5, pc}\n"
        ".word 0x00000522\n"
        ".word 0x0043e068\n"
    );
}

// DECOMP_FUNC(0x0030a6f4, 292)
extern "C" __attribute__((naked)) void func_0030a6f4() {
    asm volatile(
        "push {r4, r5, r6, r7, r8}\n"
        "mov r3, r0\n"
        "mov r0, #0x3e8\n"
        "ldrsb r4, [r2, #4]\n"
        "ldrsb r6, [r2, #5]\n"
        "add ip, r0, #0x12c\n"
        "sub r8, r4, #0x30\n"
        "ldrsb r7, [r2, #6]\n"
        "smulbb r0, r8, r0\n"
        "add r8, r6, r6, lsl #3\n"
        "add r6, r8, r6, lsl #4\n"
        "add r7, r7, r7, lsl #2\n"
        "add r0, r0, r6, lsl #2\n"
        "ldrsb r5, [r2, #7]\n"
        "ldrb r4, [r2, #0xa]\n"
        "sub r0, r0, #0x12c0\n"
        "add r0, r0, r7, lsl #1\n"
        "sub r0, r0, #0x210\n"
        "cmp r4, #0\n"
        "add r0, r0, r5\n"
        "beq .L_0030a7f0\n"
        "cmp r4, #1\n"
        "movne r0, #0\n"
        "bne .L_0030a7e8\n"
        "ldrh r4, [r2, #8]\n"
        "cmp r0, ip\n"
        "add ip, r4, r2\n"
        "ldr r2, [r2, #0xc]\n"
        "addge r5, ip, #0xf0\n"
        "addlt r5, ip, #0xd8\n"
        "ldr ip, [pc, #0xa0]\n"
        "subge r2, r2, #0xf0\n"
        "sublt r2, r2, #0xd8\n"
        "cmp r0, ip\n"
        "blt .L_0030a78c\n"
        "cmp r0, #0x4b0\n"
        "add r5, r5, #4\n"
        "subge r2, r2, #4\n"
        ".L_0030a78c:\n"
        "mov r0, #0\n"
        "lsr r6, r2, #5\n"
        "cmp r6, #0\n"
        "mov r4, r0\n"
        "ble .L_0030a7e8\n"
        ".L_0030a7a0:\n"
        "cmp r1, r0\n"
        "ble .L_0030a7e8\n"
        "cmp r0, #0\n"
        "ldrgt ip, [r5, r4, lsl #5]\n"
        "mov r2, #0\n"
        "ble .L_0030a7d0\n"
        ".L_0030a7b8:\n"
        "ldr r7, [r3, r2, lsl #2]\n"
        "cmp r7, ip\n"
        "beq .L_0030a7dc\n"
        "add r2, r2, #1\n"
        "cmp r0, r2\n"
        "bgt .L_0030a7b8\n"
        ".L_0030a7d0:\n"
        "ldr r2, [r5, r4, lsl #5]\n"
        "str r2, [r3, r0, lsl #2]\n"
        "add r0, r0, #1\n"
        ".L_0030a7dc:\n"
        "add r4, r4, #1\n"
        "cmp r4, r6\n"
        "blt .L_0030a7a0\n"
        ".L_0030a7e8:\n"
        "pop {r4, r5, r6, r7, r8}\n"
        "bx lr\n"
        ".L_0030a7f0:\n"
        "cmp r0, ip\n"
        "ldrh r0, [r2, #8]\n"
        "add r0, r0, r2\n"
        "ldrge r0, [r0, #0x18]\n"
        "ldrlt r0, [r0]\n"
        "str r0, [r3]\n"
        "pop {r4, r5, r6, r7, r8}\n"
        "mov r0, #1\n"
        "bx lr\n"
        ".word 0x0000044c\n"
    );
}

// DECOMP_FUNC(0x0030a9a4, 120)
extern "C" __attribute__((naked)) void ui_func_0030a9a4() {
    asm volatile(
        "mov r1, #0\n"
        "push {r4, r5, r6, lr}\n"
        "mov r0, r1\n"
        "bl saveLoadUI_Calc\n"
        "ldr r0, [pc, #0x5c]\n"
        "mov r5, #0\n"
        "mov r6, #1\n"
        "mov r1, #3\n"
        "ldr r4, [r0, #4]\n"
        "str r5, [r4, #0x14]\n"
        "strb r5, [r0]\n"
        "strb r5, [r0, #1]\n"
        "strb r5, [r4, #0x49]\n"
        "mov r0, #0x36\n"
        "strb r6, [r4, #0x379]\n"
        "bl camp_func_002bf6d0\n"
        "ldrsh r1, [r0, #8]\n"
        "mov r2, #9\n"
        "vmov s0, r1\n"
        "vcvt.f32.s32 s0, s0\n"
        "vstr s0, [r4, #0x38]\n"
        "ldrsh r0, [r0, #0xa]\n"
        "vmov s0, r0\n"
        "vcvt.f32.s32 s0, s0\n"
        "vstr s0, [r4, #0x3c]\n"
        "strb r5, [r4, #0x49]\n"
        "str r6, [r4, #0x34]!\n"
        "str r2, [r4, #0x1c]\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x0044de28\n"
    );
}

// DECOMP_FUNC(0x0030aa1c, 124)
extern "C" __attribute__((naked)) void ui_func_0030aa1c() {
    asm volatile(
        "push {r4, r5, r6, r7, r8, lr}\n"
        "mov r5, r0\n"
        "mov r1, #0\n"
        "mov r0, r1\n"
        "bl saveLoadUI_Calc\n"
        "ldr r0, [pc, #0x5c]\n"
        "mov r6, #0\n"
        "mov r7, #1\n"
        "mov r1, #2\n"
        "ldr r4, [r0, #4]\n"
        "str r6, [r4, #0x14]\n"
        "strb r6, [r0]\n"
        "strb r6, [r0, #1]\n"
        "strb r7, [r4, #0x49]\n"
        "mov r0, #0x36\n"
        "strb r5, [r4, #0x379]\n"
        "bl camp_func_002bf6d0\n"
        "ldrsh r1, [r0, #8]\n"
        "mov r2, #8\n"
        "vmov s0, r1\n"
        "vcvt.f32.s32 s0, s0\n"
        "vstr s0, [r4, #0x38]\n"
        "ldrsh r0, [r0, #0xa]\n"
        "vmov s0, r0\n"
        "vcvt.f32.s32 s0, s0\n"
        "vstr s0, [r4, #0x3c]\n"
        "strb r7, [r4, #0x49]\n"
        "str r6, [r4, #0x34]!\n"
        "str r2, [r4, #0x1c]\n"
        "pop {r4, r5, r6, r7, r8, pc}\n"
        ".word 0x0044de28\n"
    );
}

// DECOMP_FUNC(0x0030ade8, 68)
extern "C" __attribute__((naked)) void camp_func_0030ade8() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl camp_func_0029c49c\n"
        "mov r5, r0\n"
        "mov r2, #0\n"
        "mov r1, r4\n"
        "bl camp_func_0029c468\n"
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0]\n"
        "mov r0, r0\n"
        "mov r0, r5\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x00439ca8\n"
    );
}

// DECOMP_FUNC(0x0030b254, 84)
extern "C" __attribute__((naked)) void battle_func_0030b254() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "ldr r0, [pc, #0x38]\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0027eb98\n"
        "ldr r0, [r0, #0x20]\n"
        "mov r1, r4\n"
        "bl battle_func_002459c0\n"
        "cmp r0, #0\n"
        "beq .L_0030b294\n"
        "mov r0, #1\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".L_0030b294:\n"
        "mov r0, #0\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x0030b2a8, 84)
extern "C" __attribute__((naked)) void battle_func_0030b2a8() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "ldr r0, [pc, #0x38]\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0027eb98\n"
        "ldr r0, [r0, #0x20]\n"
        "mov r1, r4\n"
        "bl func_00245908\n"
        "cmp r0, #0\n"
        "beq .L_0030b2e8\n"
        "mov r0, #1\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".L_0030b2e8:\n"
        "mov r0, #0\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x0030b468, 40)
extern "C" __attribute__((naked)) void engine_func_0030b468() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl ui_func_00293c98\n"
        "ldr r1, [pc, #8]\n"
        "str r4, [r1, r0]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x000049c0\n"
    );
}

// DECOMP_FUNC(0x0030b490, 76)
extern "C" __attribute__((naked)) void engine_func_0030b490() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "cmp r0, #0\n"
        "mov r2, #0\n"
        "moveq r2, #7\n"
        "beq .L_0030b4c0\n"
        "cmp r0, #1\n"
        "moveq r2, #0xa\n"
        "beq .L_0030b4c0\n"
        "cmp r0, #2\n"
        "moveq r2, #0xb\n"
        ".L_0030b4c0:\n"
        "ldr r0, [pc, #0x10]\n"
        "mov r1, #0x1a\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0024c828\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x0030b4dc, 44)
extern "C" __attribute__((naked)) void engine_func_0030b4dc() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r2, r0\n"
        "ldr r0, [pc, #0x10]\n"
        "mov r1, #0x15\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0024c828\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x0030b508, 44)
extern "C" __attribute__((naked)) void engine_func_0030b508() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r2, r0\n"
        "ldr r0, [pc, #0x10]\n"
        "mov r1, #0x16\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0024c828\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x0030b790, 88)
extern "C" __attribute__((naked)) void engine_func_0030b790() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "ldr r0, [pc, #0x38]\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0027eb98\n"
        "mov r5, r0\n"
        "bl ui_func_00293c98\n"
        "ldr r1, [pc, #0x28]\n"
        "add r2, r4, r4, lsl #2\n"
        "mov r3, #1\n"
        "ldr r0, [r1, r0]\n"
        "add r1, r2, r4, lsl #6\n"
        "add r2, r0, r1, lsl #2\n"
        "mov r1, r5\n"
        "mov r0, #0\n"
        "bl battle_func_003de7fc\n"
        "mov r0, #1\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x0043427c\n"
        ".word 0x00001e98\n"
    );
}

// DECOMP_FUNC(0x0030b96c, 52)
extern "C" __attribute__((naked)) void camp_func_0030b96c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "bl camp_func_0029c68c\n"
        "cmp r0, #1\n"
        "mov r4, r0\n"
        "bne .L_0030b994\n"
        "ldr r5, [pc, #0x14]\n"
        "ldr r0, [r5]\n"
        "bl script_vm_func_00295eac\n"
        "mov r0, #0\n"
        "str r0, [r5]\n"
        ".L_0030b994:\n"
        "mov r0, r4\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x00434228\n"
    );
}

// DECOMP_FUNC(0x0030b9a0, 448)
extern "C" __attribute__((naked)) void battle_func_0030b9a0() {
    asm volatile(
        "push {r4, r5, r6, r7, r8, sb, sl, fp, lr}\n"
        "sub sp, sp, #0x1c\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r8, r0\n"
        "mov r0, #1\n"
        "bl engine_func_00296f60\n"
        "str r0, [sp, #0x14]\n"
        "mov r0, #2\n"
        "bl engine_func_00296f60\n"
        "str r0, [sp, #0x18]\n"
        "ldr r0, [pc, #0x180]\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0027eb98\n"
        "str r0, [sp, #0xc]\n"
        "bl ui_func_00293c98\n"
        "mov sl, #1\n"
        "lsl r1, sl, r8\n"
        "mov r4, #0\n"
        "add r7, r0, #0x1c00\n"
        "mov fp, #4\n"
        "mov sb, r4\n"
        "add r6, r0, #0x1fc0\n"
        "add r7, r7, #0x298\n"
        "str r1, [sp, #0x10]\n"
        ".L_0030ba04:\n"
        "ldr r0, [r6]\n"
        "add r1, r4, r4, lsl #4\n"
        "add r1, r1, r4, lsl #6\n"
        "add r5, r0, r1, lsl #3\n"
        "ldr r0, [r5]\n"
        "tst r0, #1\n"
        "beq .L_0030bb3c\n"
        "tst r0, #0x40\n"
        "bne .L_0030bb3c\n"
        "ldrsh r0, [r5, #8]\n"
        "cmp r0, #0\n"
        "blt .L_0030bb3c\n"
        "ldr r1, [sp, #0x14]\n"
        "cmp r1, #0\n"
        "beq .L_0030bac8\n"
        "ldr r0, [sp, #0x18]\n"
        "cmp r0, #0\n"
        "beq .L_0030baf4\n"
        "mov r0, r8\n"
        "bl func_00246554\n"
        "mov r1, r0\n"
        "ldrsh r0, [r5, #8]\n"
        "mvn r3, #0\n"
        "mov r2, #2\n"
        "bl ui_func_002462a0\n"
        "tst r0, #0x10000\n"
        "nop \n"
        "beq .L_0030baf4\n"
        "str fp, [sp]\n"
        "ldrsh r0, [r5, #8]\n"
        "ldr r1, [r7]\n"
        "add r2, r0, r0, lsl #2\n"
        "add r0, r2, r0, lsl #6\n"
        "ldr r2, [sp, #0xc]\n"
        "add r3, r1, r0, lsl #2\n"
        "mov r1, #0\n"
        "mov r0, r1\n"
        "bl battle_func_002461ec\n"
        "mov r3, #0\n"
        "ldr r2, [pc, #0xb0]\n"
        "ldr r1, [sp, #0xc]\n"
        "mov r0, r3\n"
        "str sb, [sp, #4]\n"
        "str sl, [sp]\n"
        "str sb, [sp, #8]\n"
        "bl battle_func_00250800\n"
        "nop \n"
        "nop \n"
        "b .L_0030bb3c\n"
        ".L_0030bac8:\n"
        "ldr r1, [r7]\n"
        "add r2, r0, r0, lsl #2\n"
        "add r0, r2, r0, lsl #6\n"
        "add r5, sp, #0xc\n"
        "add r2, r1, r0, lsl #2\n"
        "ldm r5, {r1, r3}\n"
        "mov r0, #0\n"
        "bl battle_func_00246ea4\n"
        "nop \n"
        "nop \n"
        "b .L_0030bb3c\n"
        ".L_0030baf4:\n"
        "str sl, [sp]\n"
        "ldrsh r0, [r5, #8]\n"
        "ldr r1, [r7]\n"
        "add ip, sp, #0xc\n"
        "add r2, r0, r0, lsl #2\n"
        "add r0, r2, r0, lsl #6\n"
        "add r2, r1, r0, lsl #2\n"
        "ldm ip, {r1, r3}\n"
        "mov r0, #0\n"
        "bl battle_func_00246f90\n"
        "mov r3, #0\n"
        "ldr r2, [pc, #0x34]\n"
        "ldr r1, [sp, #0xc]\n"
        "mov r0, r3\n"
        "str sb, [sp]\n"
        "str sb, [sp, #4]\n"
        "str sb, [sp, #8]\n"
        "bl battle_func_00250800\n"
        ".L_0030bb3c:\n"
        "add r4, r4, #1\n"
        "cmp r4, #4\n"
        "blt .L_0030ba04\n"
        "add sp, sp, #0x1c\n"
        "mov r0, #1\n"
        "pop {r4, r5, r6, r7, r8, sb, sl, fp, pc}\n"
        ".word 0x0043427c\n"
        ".word 0x010001ea\n"
        ".word 0x010001bd\n"
    );
}

// DECOMP_FUNC(0x0030bc5c, 88)
extern "C" __attribute__((naked)) void battle_func_0030bc5c() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "ldr r1, [pc, #0x3c]\n"
        "ldr r1, [r1]\n"
        "cmp r1, #0\n"
        "moveq r0, #0\n"
        "beq .L_0030bca0\n"
        "cmp r0, #0\n"
        "beq .L_0030bc94\n"
        "ldr r0, [pc, #0x24]\n"
        "ldrh r0, [r0, r1]\n"
        "bl battle_func_0028df54\n"
        "b .L_0030bca4\n"
        ".L_0030bc94:\n"
        "nop \n"
        "bl camp_func_002631c0\n"
        "ldrh r0, [r0, #0x46]\n"
        ".L_0030bca0:\n"
        "bl battle_func_0028df54\n"
        ".L_0030bca4:\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043daa8\n"
        ".word 0x00000126\n"
    );
}

// DECOMP_FUNC(0x0030bf38, 240)
extern "C" __attribute__((naked)) void engine_func_0030bf38() {
    asm volatile(
        "push {r0, r1, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}\n"
        "ldr r0, [sp]\n"
        "ldrh r0, [r0]\n"
        "bl engine_func_002b47cc\n"
        "mov r8, r0\n"
        "ldr r0, [sp, #4]\n"
        "ldrh r0, [r0]\n"
        "bl engine_func_002b47cc\n"
        "mov sb, r0\n"
        "ldr r0, [pc, #0xc0]\n"
        "mov r5, #0\n"
        "mov r6, r5\n"
        "mov r4, r5\n"
        "ldrd sl, fp, [r0, #8]\n"
        ".L_0030bf70:\n"
        "add r7, r8, r4, lsl #1\n"
        "mov r0, r5\n"
        "ldrsh r1, [r7, #0x74]\n"
        "asr r1, r1, #0xa\n"
        "bl func_00288ad4\n"
        "cmp r0, #0\n"
        "nop \n"
        "ble .L_0030bf9c\n"
        "ldrsh r0, [r7, #0x74]\n"
        "mov sl, r4\n"
        "asr r5, r0, #0xa\n"
        ".L_0030bf9c:\n"
        "add r7, sb, r4, lsl #1\n"
        "mov r0, r6\n"
        "ldrsh r1, [r7, #0x74]\n"
        "asr r1, r1, #0xa\n"
        "bl func_00288ad4\n"
        "cmp r0, #0\n"
        "nop \n"
        "ble .L_0030bfc8\n"
        "ldrsh r0, [r7, #0x74]\n"
        "mov fp, r4\n"
        "asr r6, r0, #0xa\n"
        ".L_0030bfc8:\n"
        "add r4, r4, #1\n"
        "cmp r4, #7\n"
        "ble .L_0030bf70\n"
        "subs r0, fp, sl\n"
        "bne .L_0030c01c\n"
        "mov r1, r5\n"
        "mov r0, r6\n"
        "bl func_00288ad4\n"
        "cmp r0, #0\n"
        "nop \n"
        "bne .L_0030c01c\n"
        "ldr r0, [sp]\n"
        "ldrh r0, [r0]\n"
        "bl engine_func_002b47cc\n"
        "mov r4, r0\n"
        "ldr r0, [sp, #4]\n"
        "ldrh r0, [r0]\n"
        "bl engine_func_002b47cc\n"
        "ldrh r0, [r0, #0x98]\n"
        "ldrh r1, [r4, #0x98]\n"
        "sub r0, r0, r1\n"
        ".L_0030c01c:\n"
        "add sp, sp, #8\n"
        "pop {r4, r5, r6, r7, r8, sb, sl, fp, ip, pc}\n"
        ".word 0x00402688\n"
    );
}

// DECOMP_FUNC(0x0030ed48, 16)
extern "C" __attribute__((naked)) void func_0030ed48() {
    asm volatile(
        "ldr r0, [pc, #4]\n"
        "ldrsb r0, [r0]\n"
        "bx lr\n"
        ".word 0x004724c8\n"
    );
}

// DECOMP_FUNC(0x0030ee2c, 24)
extern "C" __attribute__((naked)) void engine_func_0030ee2c() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "vldr s1, [r0, #4]\n"
        "vadd.f32 s0, s1, s0\n"
        "vstr s0, [r0, #4]\n"
        "bx lr\n"
        ".word 0x004724c8\n"
    );
}

// DECOMP_FUNC(0x0030ee44, 24)
extern "C" __attribute__((naked)) void engine_func_0030ee44() {
    asm volatile(
        "ldr r0, [pc, #0xc]\n"
        "vldr s1, [r0, #8]\n"
        "vadd.f32 s0, s1, s0\n"
        "vstr s0, [r0, #8]\n"
        "bx lr\n"
        ".word 0x004724c8\n"
    );
}

// DECOMP_FUNC(0x0030f534, 36)
extern "C" __attribute__((naked)) void script_vm_func_0030f534() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "ldrne r0, [r0, #4]\n"
        "cmpne r0, #0\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x00447600\n"
    );
}

// DECOMP_FUNC(0x0030f6fc, 44)
extern "C" __attribute__((naked)) void camp_func_0030f6fc() {
    asm volatile(
        "mov r0, #0x23\n"
        "mov r1, #5\n"
        "push {r4, lr}\n"
        "bl Tbb_GetGlobalSubTable\n"
        "bl Tbb_GetRowCount\n"
        "ldr r1, [pc, #0xc]\n"
        "ldr r1, [r1]\n"
        "ldr r1, [r1, #0x40c]\n"
        "add r0, r0, r1\n"
        "pop {r4, pc}\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x0030f728, 56)
extern "C" __attribute__((naked)) void engine_func_0030f728() {
    asm volatile(
        "mov r0, #0x2d\n"
        "mov r1, #2\n"
        "push {r4, lr}\n"
        "bl Tbb_GetGlobalSubTable\n"
        "bl Tbb_GetRowCount\n"
        "mov r4, r0\n"
        "ldr r0, [pc, #0x14]\n"
        "mov r2, #2\n"
        "mov r1, #0x25\n"
        "ldr r0, [r0]\n"
        "bl engine_func_0025c110\n"
        "add r0, r0, r4\n"
        "pop {r4, pc}\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x003100e4, 64)
extern "C" __attribute__((naked)) void engine_func_003100e4() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_002c583c\n"
        "bl script_vm_func_002897fc\n"
        "ldrb r0, [r0]\n"
        "cmp r0, #1\n"
        "cmpne r0, #2\n"
        "cmpne r0, #3\n"
        "bne .L_00310118\n"
        "ldr r0, [pc, #0x10]\n"
        "mov r1, #1\n"
        "ldr r0, [r0]\n"
        "strb r1, [r0, #0xc0]\n"
        ".L_00310118:\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x00432fc8\n"
    );
}

// DECOMP_FUNC(0x003106dc, 72)
extern "C" __attribute__((naked)) void engine_func_003106dc() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "ldr r5, [pc, #0x38]\n"
        "ldr r4, [r5]\n"
        "ldr r0, [r4, #8]\n"
        "bl engine_func_002c4360\n"
        "ldr r0, [r4, #0xc]\n"
        "bl engine_func_002c4360\n"
        "ldr r0, [r4, #4]\n"
        "bl script_vm_func_002a755c\n"
        "ldr r0, [r4]\n"
        "mov r1, #0\n"
        "bl battle_func_002c45b8\n"
        "mov r0, r4\n"
        "bl engine_func_002c4360\n"
        "mov r0, #0\n"
        "str r0, [r5]\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x0043daf8\n"
    );
}

// DECOMP_FUNC(0x00310768, 44)
extern "C" __attribute__((naked)) void func_00310768() {
    asm volatile(
        "ldr r0, [pc, #0x20]\n"
        "mvn r1, #1\n"
        "ldr r2, [r0, #4]\n"
        "str r1, [r2, #0xa38]\n"
        "ldr r2, [r0, #8]\n"
        "str r1, [r2, #0xa38]\n"
        "ldr r0, [r0, #0xc]\n"
        "str r1, [r0, #0xa38]\n"
        "mov r0, #1\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x00310840, 32)
extern "C" __attribute__((naked)) void func_00310840() {
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r0, [r0, #8]\n"
        "ldrb r0, [r0, #0x88]\n"
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x003108e8, 44)
extern "C" __attribute__((naked)) void engine_func_003108e8() {
    asm volatile(
        "ldr r0, [pc, #0x20]\n"
        "push {r4, lr}\n"
        "ldr r4, [r0, #4]\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "strb r0, [r4, #0x34]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x00310b24, 76)
extern "C" __attribute__((naked)) void ui_func_00310b24() {
    asm volatile(
        "push {r4, r5, r6, r7, r8, lr}\n"
        "mov r4, #0\n"
        "mov r7, r4\n"
        "ldr r6, [pc, #0x34]\n"
        ".L_00310b34:\n"
        "add r0, r4, r4, lsl #1\n"
        "add r0, r0, r4, lsl #4\n"
        "add r5, r6, r0, lsl #2\n"
        "ldrb r0, [r5, #0x4a]\n"
        "cmp r0, #1\n"
        "ldrne r0, [r5]\n"
        "cmpne r0, #0\n"
        "beq .L_00310b5c\n"
        "bl ui_func_002c0a6c\n"
        "str r7, [r5]\n"
        ".L_00310b5c:\n"
        "add r4, r4, #1\n"
        "cmp r4, #0x1a\n"
        "blo .L_00310b34\n"
        "pop {r4, r5, r6, r7, r8, pc}\n"
        ".word 0x004332a0\n"
    );
}

// DECOMP_FUNC(0x003110ac, 172)
extern "C" __attribute__((naked)) void script_vm_func_003110ac() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r4, [pc, #0x9c]\n"
        "ldr r0, [r4, #8]\n"
        "cmp r0, #0\n"
        "beq .L_003110dc\n"
        "cmp r0, #1\n"
        "beq .L_003110fc\n"
        "cmp r0, #2\n"
        "beq .L_00311114\n"
        "cmp r0, #3\n"
        "bne .L_0031114c\n"
        "b .L_00311128\n"
        ".L_003110dc:\n"
        "nop \n"
        "bl script_vm_func_00276580\n"
        "nop \n"
        "nop \n"
        "bl script_vm_func_002dfcf4\n"
        "mov r0, #1\n"
        ".L_003110f4:\n"
        "str r0, [r4, #8]\n"
        "b .L_0031114c\n"
        ".L_003110fc:\n"
        "nop \n"
        "bl func_002f3aac\n"
        "cmp r0, #0\n"
        "movne r0, #2\n"
        "bne .L_003110f4\n"
        "b .L_0031114c\n"
        ".L_00311114:\n"
        "nop \n"
        "bl func_002c8b0c\n"
        "mov r0, #3\n"
        "str r0, [r4, #8]\n"
        "b .L_0031114c\n"
        ".L_00311128:\n"
        "nop \n"
        "bl engine_func_002d3e14\n"
        "cmp r0, #0\n"
        "nop \n"
        "beq .L_0031114c\n"
        "mov r0, #0\n"
        "str r0, [r4, #8]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".L_0031114c:\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x00447518\n"
    );
}

// DECOMP_FUNC(0x00311280, 36)
extern "C" __attribute__((naked)) void camp_func_00311280() {
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "beq .L_0031129c\n"
        "add r1, r0, #0x600\n"
        "mov r0, #0\n"
        "strh r0, [r1, #0xbc]\n"
        ".L_0031129c:\n"
        "bx lr\n"
        ".word 0x0043dcf0\n"
    );
}

// DECOMP_FUNC(0x003115f8, 32)
extern "C" __attribute__((naked)) void script_vm_func_003115f8() {
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

// DECOMP_FUNC(0x00312148, 100)
extern "C" __attribute__((naked)) void engine_func_00312148() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "cmp r0, #0\n"
        "mov r4, #0\n"
        "moveq r4, #7\n"
        "beq .L_00312178\n"
        "cmp r0, #1\n"
        "moveq r4, #0xa\n"
        "beq .L_00312178\n"
        "cmp r0, #2\n"
        "moveq r4, #0xb\n"
        ".L_00312178:\n"
        "ldr r0, [pc, #0x28]\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0027eb98\n"
        "ldr r0, [r0, #0x20]\n"
        "add r0, r0, r4, lsl #1\n"
        "ldrsh r0, [r0, #0x72]\n"
        "cmp r0, #1\n"
        "movge r0, #1\n"
        "movlt r0, #0\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x00312b8c, 76)
extern "C" __attribute__((naked)) void ui_func_00312b8c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "ldr r1, [pc, #0x38]\n"
        "ldr r1, [r1, r0]\n"
        "tst r1, #2\n"
        "bne .L_00312bcc\n"
        "ldrh r4, [r0, #0xf2]\n"
        "cmp r4, #0\n"
        "beq .L_00312bcc\n"
        "mov r0, r4\n"
        "bl camp_func_002b9364\n"
        "cmp r0, #0\n"
        "beq .L_00312bcc\n"
        "mov r1, #3\n"
        "mov r0, r4\n"
        "bl script_vm_func_002954cc\n"
        ".L_00312bcc:\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x000044a0\n"
    );
}

// DECOMP_FUNC(0x00312f78, 580)
extern "C" __attribute__((naked)) void ui_func_00312f78() {
    asm volatile(
        "push {r4, r5, r6, r7, r8, sb, sl, lr}\n"
        "sub sp, sp, #8\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r5, r0\n"
        "mov r0, #1\n"
        "bl engine_func_00296f60\n"
        "bl ui_func_00293c98\n"
        "mov r1, #6\n"
        "bl func_00245318\n"
        "mov r4, r0\n"
        "bl Tbb_GetPayloadData\n"
        "mov r6, r0\n"
        "mov r0, r4\n"
        "bl Tbb_GetRowCount\n"
        "bl ui_func_00293c98\n"
        "mov r1, #7\n"
        "bl func_00245318\n"
        "bl Tbb_GetPayloadData\n"
        "add r1, r0, r5, lsl #3\n"
        "mov r0, sp\n"
        "bl ui_func_002adb40\n"
        "add r0, r6, r5, lsl #3\n"
        "mov r4, #0\n"
        "ldrh r1, [r0]\n"
        "mov r8, r4\n"
        "cmp r1, #0\n"
        "strheq r8, [sp]\n"
        "ldrh r1, [r0, #2]\n"
        "ldrhne r4, [sp]\n"
        "cmp r1, #0\n"
        "ldrhne r1, [sp, #2]\n"
        "strheq r8, [sp, #2]\n"
        "addne r4, r4, r1\n"
        "ldrh r1, [r0, #4]\n"
        "cmp r1, #0\n"
        "ldrhne r1, [sp, #4]\n"
        "strheq r8, [sp, #4]\n"
        "ldrh r0, [r0, #6]\n"
        "addne r4, r4, r1\n"
        "cmp r0, #0\n"
        "ldrhne r0, [sp, #6]\n"
        "strheq r8, [sp, #6]\n"
        "addne r4, r4, r0\n"
        "ldrh r0, [sp]\n"
        "cmp r0, #0\n"
        "moveq r5, r8\n"
        "beq .L_0031304c\n"
        "mov r1, #0x64\n"
        "mul r0, r0, r1\n"
        "mov r1, r4\n"
        "bl ui_func_002c615c\n"
        "mov r5, r0\n"
        ".L_0031304c:\n"
        "ldrh r0, [sp, #2]\n"
        "cmp r0, #0\n"
        "moveq r6, r8\n"
        "beq .L_00313070\n"
        "mov r1, #0x64\n"
        "mul r0, r0, r1\n"
        "mov r1, r4\n"
        "bl ui_func_002c615c\n"
        "mov r6, r0\n"
        ".L_00313070:\n"
        "ldrh r0, [sp, #4]\n"
        "cmp r0, #0\n"
        "moveq r7, r8\n"
        "beq .L_00313094\n"
        "mov r1, #0x64\n"
        "mul r0, r0, r1\n"
        "mov r1, r4\n"
        "bl ui_func_002c615c\n"
        "mov r7, r0\n"
        ".L_00313094:\n"
        "ldrh r0, [sp, #6]\n"
        "cmp r0, #0\n"
        "moveq r4, r8\n"
        "beq .L_003130b8\n"
        "mov r1, #0x64\n"
        "mul r0, r0, r1\n"
        "mov r1, r4\n"
        "bl ui_func_002c615c\n"
        "mov r4, r0\n"
        ".L_003130b8:\n"
        "add r8, r6, r5\n"
        "add sb, r7, r8\n"
        "add sl, r4, sb\n"
        "sub r0, sl, #1\n"
        "uxth r0, r0\n"
        "bl engine_func_002c0bcc\n"
        "mov r1, r0\n"
        "cmp r5, #0\n"
        "cmpgt r5, r1\n"
        "mvn r0, #0\n"
        "movgt r0, #1\n"
        "bgt .L_00313114\n"
        "cmp r6, #0\n"
        "cmpgt r8, r1\n"
        "movgt r0, #2\n"
        "bgt .L_00313114\n"
        "cmp r7, #0\n"
        "cmpgt sb, r1\n"
        "movgt r0, #3\n"
        "bgt .L_00313114\n"
        "cmp r4, #0\n"
        "cmpgt sl, r1\n"
        "movgt r0, #4\n"
        ".L_00313114:\n"
        "nop \n"
        "bl battle_func_0028df54\n"
        "add sp, sp, #8\n"
        "mov r0, #1\n"
        "pop {r4, r5, r6, r7, r8, sb, sl, pc}\n"
        "add ip, r0, #0x5400\n"
        "add ip, ip, #0x358\n"
        "push {r4, r5}\n"
        "ldr r4, [ip]\n"
        "cmp r4, #0\n"
        "ble .L_003131b0\n"
        "mov r3, #0\n"
        "and r1, r4, #1\n"
        "cmp r1, #1\n"
        "mov r2, r3\n"
        "bne .L_00313160\n"
        "ldr r5, [pc, #0x5c]\n"
        "mov r3, #1\n"
        "strb r2, [r5, r0]\n"
        ".L_00313160:\n"
        "cmp r4, r1\n"
        "ble .L_003131b0\n"
        ".L_00313168:\n"
        "add r5, r3, r3, lsl #1\n"
        "add r5, r5, r3, lsl #3\n"
        "add r4, r3, #1\n"
        "add r5, r0, r5, lsl #2\n"
        "add r3, r4, r4, lsl #1\n"
        "add r3, r3, r4, lsl #3\n"
        "add r5, r5, #0x5400\n"
        "add r3, r0, r3, lsl #2\n"
        "add r5, r5, #0x378\n"
        "add r3, r3, #0x5400\n"
        "add r3, r3, #0x378\n"
        "strb r2, [r5]\n"
        "strb r2, [r3]\n"
        "add r3, r4, #1\n"
        "ldr r4, [ip]\n"
        "add r1, r1, #2\n"
        "cmp r4, r1\n"
        "bgt .L_00313168\n"
        ".L_003131b0:\n"
        "pop {r4, r5}\n"
        "bx lr\n"
        ".word 0x00005778\n"
    );
}

// DECOMP_FUNC(0x003131bc, 44)
extern "C" __attribute__((naked)) void camp_func_003131bc() {
    asm volatile(
        "ldr r1, [pc, #0x20]\n"
        "ldr r1, [r1]\n"
        "cmp r1, #0\n"
        "beq .L_003131dc\n"
        "ldr r1, [r1, #0x2f8]\n"
        "cmp r1, r0\n"
        "moveq r0, #1\n"
        "beq .L_003131e0\n"
        ".L_003131dc:\n"
        "mov r0, #0\n"
        ".L_003131e0:\n"
        "bx lr\n"
        ".word 0x00434210\n"
    );
}

// DECOMP_FUNC(0x003165fc, 156)
extern "C" __attribute__((naked)) void effPolygonWind_func_003165fc() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r1, #0xc\n"
        "ldr r6, [r0, #0x3c]!\n"
        "sub sp, sp, #8\n"
        "ldr r4, [r0, #4]\n"
        "ldr r0, [r4, #0x38]\n"
        "add r0, r0, r0, lsl #1\n"
        "add r5, r1, r0, lsl #4\n"
        "ldr r1, [pc, #0x6c]\n"
        "ldr r0, [pc, #0x6c]\n"
        "mov r0, r0\n"
        "mov r1, #1\n"
        "mov r0, #0x10\n"
        "strd r0, r1, [sp]\n"
        "mov r3, r5\n"
        "mov r2, #0\n"
        "mov r1, #0x100\n"
        "mov r0, #0x10000\n"
        "bl engine_func_002c34a4\n"
        "add r1, r0, #0xc\n"
        "str r1, [r0]\n"
        "str r0, [r0, #8]\n"
        "ldr r1, [r4, #0x8c]\n"
        "mov r5, r0\n"
        "cmp r1, #3\n"
        "movls r1, #3\n"
        "str r1, [r4, #0x8c]\n"
        "ldr r0, [r6, #4]\n"
        "bl engine_func_00219ec8\n"
        "mov r1, r0\n"
        "str r1, [r5, #4]\n"
        "mov r0, r5\n"
        "mov r1, r4\n"
        "bl engine_func_0032814c\n"
        "add sp, sp, #8\n"
        "mov r0, r5\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x0000022e\n"
        ".word 0x004102fc\n"
    );
}

// DECOMP_FUNC(0x00316ffc, 108)
extern "C" __attribute__((naked)) void script_vm_func_00316ffc() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_00289640\n"
        "cmp r0, #0\n"
        "beq .L_0031702c\n"
        "bl engine_func_00289640\n"
        "cmp r0, #1\n"
        "beq .L_00317048\n"
        "bl engine_func_00289640\n"
        "cmp r0, #3\n"
        "movlt r0, #0\n"
        "movge r0, #1\n"
        "pop {r4, pc}\n"
        ".L_0031702c:\n"
        "nop \n"
        "bl func_0031ec60\n"
        "mov r0, #3\n"
        "nop \n"
        "bl script_vm_func_00270298\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".L_00317048:\n"
        "ldr r0, [pc, #0x14]\n"
        "bl script_vm_func_002b91c4\n"
        "mov r0, #1\n"
        "nop \n"
        "bl script_vm_func_00270298\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
        ".word 0x01000184\n"
    );
}

// DECOMP_FUNC(0x00317068, 56)
extern "C" __attribute__((naked)) void script_vm_func_00317068() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_00289924\n"
        "cmp r0, #0\n"
        "beq .L_00317098\n"
        "mov r2, #0x3c\n"
        "mov r1, #0\n"
        "mov r0, #0x1000000\n"
        "bl camp_func_002a0640\n"
        "ldr r0, [pc, #0xc]\n"
        "mov r1, #2\n"
        "ldr r0, [r0]\n"
        "str r1, [r0, #0x14c]\n"
        ".L_00317098:\n"
        "pop {r4, pc}\n"
        ".word 0x00432cc8\n"
    );
}

// DECOMP_FUNC(0x003170b8, 232)
extern "C" __attribute__((naked)) void engine_func_003170b8() {
    asm volatile(
        "push {r4, r5, r6, r7, r8, lr}\n"
        "mov r6, r0\n"
        "mov r4, r1\n"
        "mov r0, #4\n"
        "bl AsdMemory_func_002c23f8\n"
        "ldr r7, [pc, #0xc8]\n"
        "cmp r0, #0\n"
        "strne r6, [r0]\n"
        "tst r4, #8\n"
        "mov r5, r0\n"
        "add r8, r7, #0x10000\n"
        "movne r1, r7\n"
        "beq .L_00317110\n"
        ".L_003170ec:\n"
        "bl engine_func_002a691c\n"
        ".L_003170f0:\n"
        "tst r4, #0x20\n"
        "beq .L_00317124\n"
        "mov r1, r7\n"
        "mov r0, r5\n"
        "bl engine_func_002a671c\n"
        "nop \n"
        "nop \n"
        "b .L_00317138\n"
        ".L_00317110:\n"
        "tst r4, #0x40\n"
        "movne r1, r8\n"
        "movne r0, r5\n"
        "bne .L_003170ec\n"
        "b .L_003170f0\n"
        ".L_00317124:\n"
        "tst r4, #0x100\n"
        "beq .L_00317138\n"
        "mov r1, r8\n"
        "mov r0, r5\n"
        "bl engine_func_002a671c\n"
        ".L_00317138:\n"
        "tst r4, #0x10\n"
        "beq .L_00317158\n"
        "mov r1, r7\n"
        "mov r0, r5\n"
        "bl engine_func_002a65a8\n"
        "nop \n"
        "nop \n"
        "b .L_0031716c\n"
        ".L_00317158:\n"
        "tst r4, #0x80\n"
        "beq .L_0031716c\n"
        "mov r1, r8\n"
        "mov r0, r5\n"
        "bl engine_func_002a65a8\n"
        ".L_0031716c:\n"
        "nop \n"
        "bl engine_func_002c31bc\n"
        "mov r1, r0\n"
        "ldr r2, [r5]\n"
        "mov r0, r5\n"
        "bl engine_func_002c2cf0\n"
        "mov r0, r5\n"
        "nop \n"
        "bl AsdModel_func_0031dc4c\n"
        "add r1, r0, #0x20\n"
        "stm r1, {r5, r6}\n"
        "pop {r4, r5, r6, r7, r8, pc}\n"
        ".word 0x02020000\n"
    );
}

// DECOMP_FUNC(0x00317ba8, 48)
extern "C" __attribute__((naked)) void camp_func_00317ba8() {
    asm volatile(
        "ldr r0, [pc, #0x24]\n"
        "push {r4, lr}\n"
        "mov r1, #7\n"
        "ldr r4, [r0, #8]\n"
        "add r0, r4, #0x800\n"
        "add r0, r0, #0x184\n"
        "bl camp_func_002bf030\n"
        "mov r0, #4\n"
        "strb r0, [r4, #0x88]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x00317eb8, 32)
extern "C" __attribute__((naked)) void ui_func_00317eb8() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0ac8\n"
        "bl engine_func_002c4360\n"
        "ldr r1, [pc, #8]\n"
        "mov r0, #0\n"
        "str r0, [r1]\n"
        "pop {r4, pc}\n"
        ".word 0x0043e088\n"
    );
}

// DECOMP_FUNC(0x00317fa4, 32)
extern "C" __attribute__((naked)) void func_00317fa4() {
    asm volatile(
        "ldr r1, [pc, #0x14]\n"
        "ldr r1, [r1, #4]\n"
        "cmp r1, #0\n"
        "addne r1, r1, #0x1800\n"
        "addne r1, r1, #0x98\n"
        "strne r0, [r1]\n"
        "bx lr\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x00318178, 180)
extern "C" __attribute__((naked)) void script_vm_func_00318178() {
    asm volatile(
        "push {r4, r5, r6, r7, r8, lr}\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "ldr r7, [pc, #0x9c]\n"
        "mov r4, r0\n"
        "ldr r0, [r7]\n"
        "bl script_vm_func_0027eb98\n"
        "ldr r0, [r0, #0x28]\n"
        "mov r1, #0xc\n"
        "add r0, r0, #0x100\n"
        "strh r1, [r0, #0x4c]\n"
        "bl ui_func_00293c98\n"
        "orr r1, r4, #0x20000\n"
        "add r2, r0, #0x1000\n"
        "add r2, r2, #0xfd0\n"
        "asr r0, r1, #0x1f\n"
        "str r0, [r2, #4]\n"
        "mov r6, #1\n"
        "mov r5, #0\n"
        "mov r4, #4\n"
        "str r1, [r2]\n"
        ".L_003181cc:\n"
        "nop \n"
        "bl ui_func_00293c98\n"
        "add r0, r0, #0x1fc0\n"
        "add r1, r4, r4, lsl #4\n"
        "ldr r0, [r0]\n"
        "add r1, r1, r4, lsl #6\n"
        "ldr r0, [r0, r1, lsl #3]\n"
        "tst r0, #1\n"
        "tsteq r0, #0x40\n"
        "bne .L_00318214\n"
        "ldr r0, [r7]\n"
        "bl script_vm_func_0027eb98\n"
        "add r1, r5, #1\n"
        "add r0, r0, r4\n"
        "sxtb r5, r1\n"
        "cmp r5, r6\n"
        "strb r4, [r0, #0x38]\n"
        "bge .L_00318220\n"
        ".L_00318214:\n"
        "add r4, r4, #1\n"
        "cmp r4, #0x36\n"
        "blt .L_003181cc\n"
        ".L_00318220:\n"
        "mov r0, #1\n"
        "pop {r4, r5, r6, r7, r8, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x00318494, 100)
extern "C" __attribute__((naked)) void engine_func_00318494() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "cmp r0, #0\n"
        "mov r4, #0\n"
        "moveq r4, #7\n"
        "beq .L_003184c4\n"
        "cmp r0, #1\n"
        "moveq r4, #0xa\n"
        "beq .L_003184c4\n"
        "cmp r0, #2\n"
        "moveq r4, #0xb\n"
        ".L_003184c4:\n"
        "ldr r0, [pc, #0x28]\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0027eb98\n"
        "ldr r0, [r0, #0x20]\n"
        "add r0, r0, r4, lsl #1\n"
        "ldrsh r0, [r0, #0x72]\n"
        "cmn r0, #1\n"
        "movle r0, #1\n"
        "movgt r0, #0\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x00318624, 52)
extern "C" __attribute__((naked)) void script_vm_func_00318624() {
    asm volatile(
        "ldr r0, [pc, #0x28]\n"
        "push {r4, lr}\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0027eb98\n"
        "ldr r0, [r0, #0x24]\n"
        "mov r1, #0x20000\n"
        "bl ui_func_002d18c8\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x00318a34, 456)
extern "C" __attribute__((naked)) void camp_func_00318a34() {
    asm volatile(
        "push {r4, r5, r6, r7, r8, sb, sl, fp, lr}\n"
        "sub sp, sp, #0x1c\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov sl, r0\n"
        "mov r0, #0\n"
        "str r0, [sp]\n"
        "mvn r8, #0\n"
        "mov r6, r0\n"
        "mov r7, r0\n"
        "mov r4, r0\n"
        "str r0, [sp, #4]\n"
        "str r0, [sp, #8]\n"
        "str r0, [sp, #0xc]\n"
        "str r0, [sp, #0x10]\n"
        "str r0, [sp, #0x14]\n"
        "bl camp_func_002a8a08\n"
        "add r0, r0, #0x9000\n"
        "ldrb r0, [r0, #0x10b]\n"
        "cmp r0, #0\n"
        "movgt fp, sp\n"
        "ble .L_00318be4\n"
        ".L_00318a8c:\n"
        "nop \n"
        "bl camp_func_002a8a08\n"
        "ldr r5, [pc, #0x15c]\n"
        "add r0, r0, r4\n"
        "ldrsb r5, [r0, r5]\n"
        "cmp r5, #0\n"
        "blt .L_00318b24\n"
        "mov r0, r5\n"
        "bl camp_func_002a89e4\n"
        "mov sb, r0\n"
        "mov r1, #1\n"
        "bl camp_func_0029ee4c\n"
        "cmp r0, #0\n"
        "nop \n"
        "bne .L_00318b24\n"
        "mov r1, #0xa\n"
        "mov r0, sb\n"
        "bl camp_func_0029ee4c\n"
        "cmp r0, #0\n"
        "nop \n"
        "bne .L_00318b24\n"
        "mov r1, #2\n"
        "mov r0, sb\n"
        "bl camp_func_0029ee4c\n"
        "cmp r0, #0\n"
        "nop \n"
        "bne .L_00318b24\n"
        "ldrh r0, [sb, #0x46]\n"
        "cmp r0, sl\n"
        "beq .L_00318b24\n"
        "mov r0, sb\n"
        "bl script_vm_func_00296020\n"
        "cmp r0, #0\n"
        "addeq r0, r6, #1\n"
        "strbeq r5, [fp, r6]\n"
        "sxtbeq r6, r0\n"
        "addne r0, r7, #1\n"
        "sxtbne r7, r0\n"
        ".L_00318b24:\n"
        "add r4, r4, #1\n"
        "bl camp_func_002a8a08\n"
        "add r0, r0, #0x9000\n"
        "ldrb r0, [r0, #0x10b]\n"
        "cmp r0, r4\n"
        "bgt .L_00318a8c\n"
        "cmp r6, #0\n"
        "ble .L_00318b60\n"
        "sub r0, r6, #1\n"
        "uxth r0, r0\n"
        "bl engine_func_002c0bcc\n"
        "sxtb r0, r0\n"
        "ldrsb r0, [fp, r0]\n"
        "add r8, r0, #0x6d\n"
        "b .L_00318be4\n"
        ".L_00318b60:\n"
        "cmp r7, #0\n"
        "ble .L_00318be4\n"
        "sub r0, r7, #1\n"
        "uxth r0, r0\n"
        "bl engine_func_002c0bcc\n"
        "mov r5, #0\n"
        "mov r4, r5\n"
        "sxtb r6, r0\n"
        ".L_00318b80:\n"
        "nop \n"
        "bl ui_func_00293c98\n"
        "add r0, r0, #0x1fc0\n"
        "add r1, r4, r4, lsl #4\n"
        "ldr r0, [r0]\n"
        "add r1, r1, r4, lsl #6\n"
        "ldr r1, [r0, r1, lsl #3]!\n"
        "tst r1, #1\n"
        "beq .L_00318bd8\n"
        "tst r1, #0x40\n"
        "bne .L_00318bd8\n"
        "ldrsh r2, [r0, #8]\n"
        "cmp r2, #0\n"
        "blt .L_00318bd8\n"
        "tst r1, #8\n"
        "beq .L_00318bd8\n"
        "cmp r6, r5\n"
        "addne r0, r5, #1\n"
        "sxtbne r5, r0\n"
        "bne .L_00318bd8\n"
        "ldrsh r8, [r0, #8]\n"
        "b .L_00318be4\n"
        ".L_00318bd8:\n"
        "add r4, r4, #1\n"
        "cmp r4, #0x6d\n"
        "blt .L_00318b80\n"
        ".L_00318be4:\n"
        "mov r0, r8\n"
        "bl battle_func_0028df54\n"
        "add sp, sp, #0x1c\n"
        "mov r0, #1\n"
        "pop {r4, r5, r6, r7, r8, sb, sl, fp, pc}\n"
        ".word 0x000090f0\n"
    );
}

// DECOMP_FUNC(0x00318c88, 288)
extern "C" __attribute__((naked)) void camp_func_00318c88() {
    asm volatile(
        "push {r4, r5, r6, r7, r8, sb, lr}\n"
        "sub sp, sp, #0x114\n"
        "ldr r8, [pc, #0x10c]\n"
        "ldr r0, [r8]\n"
        "bl func_003c0a90\n"
        "mov r4, r0\n"
        "bl Tbb_GetRowCount\n"
        "mov r6, r0\n"
        "mov r0, r4\n"
        "bl Tbb_GetPayloadData\n"
        "mov r7, r0\n"
        "mov r5, #0\n"
        "mvn r2, #0\n"
        "mov r1, #0x80\n"
        "add r0, sp, #0x80\n"
        "bl camp_func_002c4450\n"
        "cmp r6, #0\n"
        "mov r4, #0\n"
        "addgt sb, sp, #0x80\n"
        "ble .L_00318d1c\n"
        ".L_00318cd8:\n"
        "rsb r0, r4, r4, lsl #5\n"
        "add r0, r7, r0, lsl #2\n"
        "ldr r1, [r0, #0x74]\n"
        "cmp r1, #0\n"
        "beq .L_00318d10\n"
        "ldr r0, [r0, #0x78]\n"
        "cmp r0, #0\n"
        "beq .L_00318d08\n"
        "bl script_vm_func_002c0ba8\n"
        "cmp r0, #0\n"
        "nop \n"
        "beq .L_00318d0c\n"
        ".L_00318d08:\n"
        "str r4, [sb, r5, lsl #2]\n"
        ".L_00318d0c:\n"
        "add r5, r5, #1\n"
        ".L_00318d10:\n"
        "add r4, r4, #1\n"
        "cmp r4, r6\n"
        "blt .L_00318cd8\n"
        ".L_00318d1c:\n"
        "mov r4, #0\n"
        "mvn r2, #0\n"
        "mov r1, #0x80\n"
        "mov r0, sp\n"
        "bl camp_func_002c4450\n"
        "ldr r3, [r8]\n"
        "add r0, sp, #0x80\n"
        "mov r1, #0x20\n"
        "mov r5, sp\n"
        ".L_00318d40:\n"
        "ldr r2, [r0]\n"
        "cmn r2, #1\n"
        "beq .L_00318d60\n"
        "add ip, r3, r2, lsl #2\n"
        "ldr ip, [ip, #0x34]\n"
        "cmn ip, #1\n"
        "streq r2, [r5, r4, lsl #2]\n"
        "addeq r4, r4, #1\n"
        ".L_00318d60:\n"
        "subs r1, r1, #1\n"
        "add r0, r0, #4\n"
        "bne .L_00318d40\n"
        "cmp r4, #0\n"
        "moveq r4, #1\n"
        "sub r0, r4, #1\n"
        "uxth r0, r0\n"
        "bl engine_func_002c0bcc\n"
        "ldr r0, [r5, r0, lsl #2]\n"
        "ldr r2, [r8]\n"
        "mvn r1, #0\n"
        "add r2, r2, r0, lsl #2\n"
        "str r1, [r2, #0x34]\n"
        "bl battle_func_0028df54\n"
        "add sp, sp, #0x114\n"
        "mov r0, #1\n"
        "pop {r4, r5, r6, r7, r8, sb, pc}\n"
        ".word 0x00439b58\n"
    );
}

// DECOMP_FUNC(0x00318da8, 56)
extern "C" __attribute__((naked)) void camp_func_00318da8() {
    asm volatile(
        "ldr r1, [pc, #0x2c]\n"
        "push {r4, lr}\n"
        "ldr r1, [r1, r0]\n"
        "cmp r1, #0x27\n"
        "moveq r0, #0\n"
        "beq .L_00318dd8\n"
        "add r0, r0, #0x1000\n"
        "mov r2, #0\n"
        "mov r1, #9\n"
        "add r0, r0, #0x2b8\n"
        "bl camp_func_002bdac0\n"
        "mov r0, #1\n"
        ".L_00318dd8:\n"
        "pop {r4, pc}\n"
        ".word 0x00003048\n"
    );
}

// DECOMP_FUNC(0x0031b8fc, 44)
extern "C" __attribute__((naked)) void camp_func_0031b8fc() {
    asm volatile(
        "mov r0, #0x23\n"
        "mov r1, #2\n"
        "push {r4, lr}\n"
        "bl Tbb_GetGlobalSubTable\n"
        "bl Tbb_GetRowCount\n"
        "ldr r1, [pc, #0xc]\n"
        "ldr r1, [r1]\n"
        "ldr r1, [r1, #0x3f4]\n"
        "add r0, r0, r1\n"
        "pop {r4, pc}\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x0031b928, 56)
extern "C" __attribute__((naked)) void engine_func_0031b928() {
    asm volatile(
        "mov r0, #0x2a\n"
        "mov r1, #1\n"
        "push {r4, lr}\n"
        "bl Tbb_GetGlobalSubTable\n"
        "bl Tbb_GetRowCount\n"
        "mov r4, r0\n"
        "ldr r0, [pc, #0x14]\n"
        "mov r2, #1\n"
        "mov r1, #0x24\n"
        "ldr r0, [r0]\n"
        "bl engine_func_0025c110\n"
        "add r0, r0, r4\n"
        "pop {r4, pc}\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x0031bb60, 40)
extern "C" __attribute__((naked)) void func_0031bb60() {
    asm volatile(
        "ldr r0, [pc, #0x1c]\n"
        "mov r1, #1\n"
        "strb r1, [r0, #7]\n"
        "ldr r1, [r0, #0x34]\n"
        "ldr r1, [r1, #0x34]\n"
        "cmp r1, #0\n"
        "strne r1, [r0, #0x38]\n"
        "mov r0, #0\n"
        "bx lr\n"
        ".word 0x0044ea80\n"
    );
}

// DECOMP_FUNC(0x0031bbf4, 60)
extern "C" __attribute__((naked)) void func_0031bbf4() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, #0\n"
        "ldr r4, [pc, #0x28]\n"
        "ldr r0, [r4, #0x40]\n"
        "cmp r0, #0\n"
        "beq .L_0031bc14\n"
        "bl ui_func_002473ac\n"
        "str r5, [r4, #0x40]\n"
        ".L_0031bc14:\n"
        "ldr r0, [r4, #0x3c]\n"
        "cmp r0, #0\n"
        "beq .L_0031bc28\n"
        "bl engine_func_0024736c\n"
        "str r5, [r4, #0x3c]\n"
        ".L_0031bc28:\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x0044ea80\n"
    );
}

// DECOMP_FUNC(0x0031bdbc, 20)
extern "C" __attribute__((naked)) void func_0031bdbc() {
    asm volatile(
        "ldr r0, [pc, #8]\n"
        "ldr r0, [r0]\n"
        "ldr r0, [r0, #0x30]\n"
        "bx lr\n"
        ".word 0x0043ded0\n"
    );
}

// DECOMP_FUNC(0x0031c3c4, 28)
extern "C" __attribute__((naked)) void func_0031c3c4() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r1, [r0]\n"
        "mov r0, #0\n"
        "cmp r1, #0\n"
        "ldrshne r0, [r1, #0x3c]\n"
        "bx lr\n"
        ".word 0x0043dcf0\n"
    );
}

// DECOMP_FUNC(0x0031c7ec, 180)
extern "C" __attribute__((naked)) void script_vm_func_0031c7ec() {
    asm volatile(
        "push {r4, r5, r6, r7, r8, lr}\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "ldr r7, [pc, #0x9c]\n"
        "mov r4, r0\n"
        "ldr r0, [r7]\n"
        "bl script_vm_func_0027eb98\n"
        "ldr r0, [r0, #0x28]\n"
        "mov r1, #0xc\n"
        "add r0, r0, #0x100\n"
        "strh r1, [r0, #0x4c]\n"
        "bl ui_func_00293c98\n"
        "orr r1, r4, #0x40000\n"
        "add r2, r0, #0x1000\n"
        "add r2, r2, #0xfd0\n"
        "asr r0, r1, #0x1f\n"
        "str r0, [r2, #4]\n"
        "mov r6, #1\n"
        "mov r5, #0\n"
        "mov r4, #4\n"
        "str r1, [r2]\n"
        ".L_0031c840:\n"
        "nop \n"
        "bl ui_func_00293c98\n"
        "add r0, r0, #0x1fc0\n"
        "add r1, r4, r4, lsl #4\n"
        "ldr r0, [r0]\n"
        "add r1, r1, r4, lsl #6\n"
        "ldr r0, [r0, r1, lsl #3]\n"
        "tst r0, #1\n"
        "tsteq r0, #0x40\n"
        "bne .L_0031c888\n"
        "ldr r0, [r7]\n"
        "bl script_vm_func_0027eb98\n"
        "add r1, r5, #1\n"
        "add r0, r0, r4\n"
        "sxtb r5, r1\n"
        "cmp r5, r6\n"
        "strb r4, [r0, #0x38]\n"
        "bge .L_0031c894\n"
        ".L_0031c888:\n"
        "add r4, r4, #1\n"
        "cmp r4, #0x36\n"
        "blt .L_0031c840\n"
        ".L_0031c894:\n"
        "mov r0, #1\n"
        "pop {r4, r5, r6, r7, r8, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x0031cc38, 52)
extern "C" __attribute__((naked)) void script_vm_func_0031cc38() {
    asm volatile(
        "ldr r0, [pc, #0x28]\n"
        "push {r4, lr}\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0027eb98\n"
        "ldr r0, [r0, #0x24]\n"
        "mov r1, #0x40000\n"
        "bl ui_func_002d18c8\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x0031e8e8, 156)
extern "C" __attribute__((naked)) void engine_func_0031e8e8() {
    asm volatile(
        "push {r4, r5, r6, r7, r8, lr}\n"
        "sub sp, sp, #8\n"
        "ldr r5, [pc, #0x88]\n"
        "ldr r4, [r5, #4]\n"
        "bl battle_func_00220458\n"
        "bl battle_func_00201040\n"
        "ldr r0, [r5, #4]\n"
        "mov r5, #6\n"
        "cmp r0, #0\n"
        "movne r1, #0x14\n"
        "strbne r1, [r0, #0xa11]\n"
        "bl func_0028686c\n"
        "mov r7, r0\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r6, r0\n"
        "bl engine_func_00289640\n"
        "mov r8, #0\n"
        "mov r2, r0\n"
        "mov r3, r5\n"
        "mov r1, r6\n"
        "mov r0, r7\n"
        "str r8, [sp]\n"
        "str r8, [sp, #4]\n"
        "bl engine_func_00286928\n"
        "mov r5, r0\n"
        "bl engine_func_00289640\n"
        "cmp r0, #0\n"
        "bne .L_0031e974\n"
        "ldr r0, [r4, #4]\n"
        "bl func_002b8574\n"
        "ldr r0, [r4, #0xc]\n"
        "strb r8, [r4, #0xa10]\n"
        "orr r0, r0, #0x20\n"
        "str r0, [r4, #0xc]\n"
        ".L_0031e974:\n"
        "add sp, sp, #8\n"
        "mov r0, r5\n"
        "pop {r4, r5, r6, r7, r8, pc}\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x0031ec60, 44)
extern "C" __attribute__((naked)) void func_0031ec60() {
    asm volatile(
        "ldr r0, [pc, #0x20]\n"
        "mov r2, #1\n"
        "mov r1, #0\n"
        "ldr r0, [r0]\n"
        "strb r2, [r0, #0xf60]\n"
        "strb r1, [r0, #0xf63]\n"
        "strb r1, [r0, #0xf64]\n"
        "strb r1, [r0, #0xf65]\n"
        "strb r2, [r0, #0xf99]\n"
        "bx lr\n"
        ".word 0x0043e278\n"
    );
}

// DECOMP_FUNC(0x0031ed1c, 500)
extern "C" __attribute__((naked)) void camp_func_0031ed1c() {
    asm volatile(
        "push {r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, lr}\n"
        "sub sp, sp, #0x24\n"
        "mov r4, r0\n"
        "mov r5, r0\n"
        "mov r0, #0x17\n"
        "mov fp, r1\n"
        "add r1, sp, #0x60\n"
        "ldm r1, {r6, sb, sl}\n"
        "add r1, sp, #0x58\n"
        "ldm r1, {r7, r8}\n"
        "str r0, [sp, #0xc]\n"
        "cmp r7, #0\n"
        "beq .L_0031edac\n"
        "cmp r5, #0\n"
        "movlt r4, #0\n"
        "blt .L_0031edac\n"
        "uxth r0, r5\n"
        "bl camp_func_002b9364\n"
        "movs r4, r0\n"
        "beq .L_0031ee80\n"
        "uxth r0, r5\n"
        "bl battle_func_002b087c\n"
        "ldrb r1, [r0, #3]\n"
        "tst r1, #1\n"
        "beq .L_0031ed98\n"
        "ldrsh r4, [r0, #0x88]\n"
        "mov r0, #0x23\n"
        "str r0, [sp, #0xc]\n"
        "cmp r4, #0x81\n"
        "bge .L_0031ee80\n"
        "b .L_0031edac\n"
        ".L_0031ed98:\n"
        "ldrh r1, [r4, #0x90]\n"
        "ldr r0, [pc, #0x164]\n"
        "add r4, r1, #1\n"
        "cmp r4, r0\n"
        "bge .L_0031ee80\n"
        ".L_0031edac:\n"
        "mov r0, #0x17\n"
        "cmp r7, #0\n"
        "mov r1, r5\n"
        "str r0, [sp]\n"
        "beq .L_0031ee20\n"
        "cmp r5, #0\n"
        "movlt r1, #0\n"
        "blt .L_0031ee20\n"
        "uxth r0, r5\n"
        "bl camp_func_002b9364\n"
        "movs r7, r0\n"
        "nop \n"
        "beq .L_0031ee80\n"
        "uxth r0, r5\n"
        "bl battle_func_002b087c\n"
        "ldrb r1, [r0, #3]\n"
        "tst r1, #1\n"
        "beq .L_0031ee0c\n"
        "ldrsh r1, [r0, #0x88]\n"
        "mov r0, #0x23\n"
        "str r0, [sp]\n"
        "cmp r1, #0x81\n"
        "bge .L_0031ee80\n"
        "b .L_0031ee20\n"
        ".L_0031ee0c:\n"
        "ldrh r1, [r7, #0x90]\n"
        "ldr r0, [pc, #0xf0]\n"
        "add r1, r1, #1\n"
        "cmp r1, r0\n"
        "bge .L_0031ee80\n"
        ".L_0031ee20:\n"
        "ldr r0, [sp]\n"
        "bl ui_func_002a63f8\n"
        "cmp r0, #0\n"
        "nop \n"
        "beq .L_0031ee80\n"
        "ldr r7, [pc, #0xd0]\n"
        "ldr r1, [sp, #0xc]\n"
        "mov r2, r4\n"
        "ldr r0, [r7]\n"
        "bl engine_func_002487e4\n"
        "cmp r0, #0\n"
        "nop \n"
        "beq .L_0031ee88\n"
        "add r0, sp, #0x10\n"
        "str r8, [sp, #0xc]\n"
        "stm r0, {r6, sb, sl}\n"
        "mov r3, r4\n"
        "ldrd r0, r1, [sp, #0x2c]\n"
        "str fp, [sp]\n"
        "mov r2, #2\n"
        "strd r0, r1, [sp, #4]\n"
        "ldr r0, [r7]\n"
        "mov r1, r5\n"
        "bl engine_func_0038a184\n"
        ".L_0031ee80:\n"
        "add sp, sp, #0x34\n"
        "pop {r4, r5, r6, r7, r8, sb, sl, fp, pc}\n"
        ".L_0031ee88:\n"
        "add r1, r4, r4, lsl #1\n"
        "rsb r1, r1, r4, lsl #7\n"
        "mov r0, #1\n"
        "add r4, r0, r1, lsl #3\n"
        "ldr r0, [sp, #0xc]\n"
        "mov r1, r4\n"
        "bl camp_func_002bf6d0\n"
        "ldrh r1, [r0]\n"
        "sub r2, r8, fp\n"
        "ldr r3, [sp, #0x2c]\n"
        "add r1, r1, r2\n"
        "str r1, [sp, #0x18]\n"
        "ldr r2, [sp, #0x30]\n"
        "add r1, r1, sb\n"
        "str r1, [sp, #0x1c]\n"
        "ldrh r0, [r0, #2]\n"
        "sub r3, r6, r3\n"
        "add r1, sp, #4\n"
        "add r0, r0, r3\n"
        "str r0, [sp, #0x10]\n"
        "add r0, r0, sl\n"
        "str r0, [sp, #0x14]\n"
        "add ip, sp, #0x10\n"
        "str r6, [sp]\n"
        "stm r1, {r2, ip}\n"
        "mov r3, r8\n"
        "ldr r1, [sp, #0xc]\n"
        "mov r2, r4\n"
        "mov r0, #2\n"
        "bl func_002b06a0\n"
        "add sp, sp, #0x34\n"
        "pop {r4, r5, r6, r7, r8, sb, sl, fp, pc}\n"
        ".word 0x00000266\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x0031f124, 76)
extern "C" __attribute__((naked)) void battle_func_0031f124() {
    asm volatile(
        "ldr r0, [pc, #0x40]\n"
        "push {r4, lr}\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0027eb98\n"
        "ldr r0, [r0, #0x20]\n"
        "ldrsh r1, [r0, #0x8e]\n"
        "cmp r1, #0\n"
        "ble .L_0031f150\n"
        "mov r0, #1\n"
        "bl battle_func_0028df54\n"
        "b .L_0031f164\n"
        ".L_0031f150:\n"
        "ldrsh r0, [r0, #0x92]\n"
        "cmp r0, #0\n"
        "movgt r0, #1\n"
        "movle r0, #0\n"
        "bl battle_func_0028df54\n"
        ".L_0031f164:\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x0031f57c, 292)
extern "C" __attribute__((naked)) void ui_func_0031f57c() {
    asm volatile(
        "push {r4, r5, r6, r7, r8, sb, lr}\n"
        "sub sp, sp, #0x1b4\n"
        "bl ui_func_00293c98\n"
        "ldr r4, [pc, #0x10c]\n"
        "ldrsh r4, [r0, r4]\n"
        "bl ui_func_00293c98\n"
        "mov r1, r4\n"
        "bl ui_func_00282b94\n"
        "mov r7, r0\n"
        "mov r1, #0x1b4\n"
        "mov r0, sp\n"
        "bl engine_func_002c4b30\n"
        "mov r6, #0\n"
        "mov r4, r6\n"
        "mov sb, sp\n"
        "add r8, r7, #0x100\n"
        ".L_0031f5bc:\n"
        "nop \n"
        "bl ui_func_00293c98\n"
        "add r0, r0, #0x1fc0\n"
        "add r1, r4, r4, lsl #4\n"
        "ldr r0, [r0]\n"
        "add r1, r1, r4, lsl #6\n"
        "add r5, r0, r1, lsl #3\n"
        "ldr r0, [r5]\n"
        "tst r0, #1\n"
        "beq .L_0031f660\n"
        "tst r0, #0x40\n"
        "bne .L_0031f660\n"
        "tst r0, #0x10\n"
        "beq .L_0031f660\n"
        "ldrsh r0, [r5, #0x6e]\n"
        "ldrsh r1, [r7, #0x6e]\n"
        "cmp r0, r1\n"
        "beq .L_0031f660\n"
        "mov r0, #0x1cc\n"
        "ldrh r1, [r8, #0xcc]\n"
        "ldrh r0, [r0, r5]\n"
        "cmp r0, r1\n"
        "bhi .L_0031f660\n"
        "ldrh r0, [r5, #0xce]\n"
        "bl camp_func_0024ec64\n"
        "cmp r0, #0\n"
        "nop \n"
        "bne .L_0031f660\n"
        "ldr r0, [r5, #0x284]\n"
        "cmp r0, #0\n"
        "beq .L_0031f660\n"
        "ldrh r0, [r0, #0x16]\n"
        "tst r0, #0x200\n"
        "beq .L_0031f660\n"
        "ldrh r0, [r7, #0xce]\n"
        "ldrh r1, [r5, #0xce]\n"
        "cmp r0, r1\n"
        "beq .L_0031f660\n"
        "add r0, r6, #1\n"
        "str r5, [sb, r6, lsl #2]\n"
        "and r6, r0, #0xff\n"
        ".L_0031f660:\n"
        "add r4, r4, #1\n"
        "cmp r4, #0x6d\n"
        "blt .L_0031f5bc\n"
        "cmp r6, #0\n"
        "mvneq r0, #0\n"
        "beq .L_0031f68c\n"
        "sub r0, r6, #1\n"
        "uxth r0, r0\n"
        "bl engine_func_002c0bcc\n"
        "ldr r0, [sb, r0, lsl #2]\n"
        "ldrsh r0, [r0, #8]\n"
        ".L_0031f68c:\n"
        "bl battle_func_0028df54\n"
        "add sp, sp, #0x1b4\n"
        "mov r0, #1\n"
        "pop {r4, r5, r6, r7, r8, sb, pc}\n"
        ".word 0x0000225a\n"
    );
}

// DECOMP_FUNC(0x00321aa4, 44)
extern "C" __attribute__((naked)) void camp_func_00321aa4() {
    asm volatile(
        "mov r0, #0x23\n"
        "mov r1, #4\n"
        "push {r4, lr}\n"
        "bl Tbb_GetGlobalSubTable\n"
        "bl Tbb_GetRowCount\n"
        "ldr r1, [pc, #0xc]\n"
        "ldr r1, [r1]\n"
        "ldr r1, [r1, #0x404]\n"
        "add r0, r0, r1\n"
        "pop {r4, pc}\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x00321b78, 40)
extern "C" __attribute__((naked)) void script_vm_func_00321b78() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_00289924\n"
        "cmp r0, #0\n"
        "beq .L_00321b98\n"
        "ldr r0, [pc, #0xc]\n"
        "mov r1, #5\n"
        "ldr r0, [r0]\n"
        "str r1, [r0, #0x14c]\n"
        ".L_00321b98:\n"
        "pop {r4, pc}\n"
        ".word 0x00432cc8\n"
    );
}

// DECOMP_FUNC(0x00321e54, 52)
extern "C" __attribute__((naked)) void engine_func_00321e54() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r0, #0\n"
        "str r0, [sp]\n"
        "ldr r0, [pc, #0x18]\n"
        "mov r3, #4\n"
        "mov r2, r3\n"
        "mov r1, sp\n"
        "ldr r0, [r0, #0x1c]\n"
        "bl effParts_func_0025cc14\n"
        "ldr r0, [pc, #4]\n"
        "pop {r3, pc}\n"
        ".word 0x0044ea80\n"
        ".word 0x00400002\n"
    );
}

// DECOMP_FUNC(0x00322c98, 44)
extern "C" __attribute__((naked)) void func_00322c98() {
    asm volatile(
        "add r3, r0, r0, lsl #3\n"
        "add r0, r3, r0, lsl #5\n"
        "ldr r3, [pc, #0x18]\n"
        "add r1, r1, r1, lsl #2\n"
        "mov r2, #8\n"
        "add r0, r3, r0, lsl #3\n"
        "add r1, r2, r1, lsl #2\n"
        "ldr r0, [r0, #0x13c]\n"
        "add r0, r0, r1\n"
        "bx lr\n"
        ".word 0x00478000\n"
    );
}

// DECOMP_FUNC(0x00322cc4, 28)
extern "C" __attribute__((naked)) void func_00322cc4() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r1, [r0]\n"
        "mvn r0, #0\n"
        "cmp r1, #0\n"
        "ldrne r0, [r1, #0x30]\n"
        "bx lr\n"
        ".word 0x0043ded0\n"
    );
}

// DECOMP_FUNC(0x00323574, 28)
extern "C" __attribute__((naked)) void func_00323574() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "push {r4, lr}\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0026ca8c\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x00439ca8\n"
    );
}

// DECOMP_FUNC(0x003236c0, 56)
extern "C" __attribute__((naked)) void camp_func_003236c0() {
    asm volatile(
        "mov r0, #0x29\n"
        "mov r1, #1\n"
        "push {r4, lr}\n"
        "bl Tbb_GetGlobalSubTable\n"
        "bl Tbb_GetRowCount\n"
        "mov r4, r0\n"
        "ldr r0, [pc, #0x14]\n"
        "mov r2, #1\n"
        "mov r1, #0x23\n"
        "ldr r0, [r0]\n"
        "bl engine_func_0025c110\n"
        "add r0, r0, r4\n"
        "pop {r4, pc}\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x003236f8, 56)
extern "C" __attribute__((naked)) void camp_func_003236f8() {
    asm volatile(
        "mov r0, #0x29\n"
        "mov r1, #2\n"
        "push {r4, lr}\n"
        "bl Tbb_GetGlobalSubTable\n"
        "bl Tbb_GetRowCount\n"
        "mov r4, r0\n"
        "ldr r0, [pc, #0x14]\n"
        "mov r2, #2\n"
        "mov r1, #0x23\n"
        "ldr r0, [r0]\n"
        "bl engine_func_0025c110\n"
        "add r0, r0, r4\n"
        "pop {r4, pc}\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x00323730, 56)
extern "C" __attribute__((naked)) void camp_func_00323730() {
    asm volatile(
        "mov r0, #0x29\n"
        "mov r1, #3\n"
        "push {r4, lr}\n"
        "bl Tbb_GetGlobalSubTable\n"
        "bl Tbb_GetRowCount\n"
        "mov r4, r0\n"
        "ldr r0, [pc, #0x14]\n"
        "mov r2, #3\n"
        "mov r1, #0x23\n"
        "ldr r0, [r0]\n"
        "bl engine_func_0025c110\n"
        "add r0, r0, r4\n"
        "pop {r4, pc}\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x00323768, 56)
extern "C" __attribute__((naked)) void camp_func_00323768() {
    asm volatile(
        "mov r0, #0x29\n"
        "mov r1, #4\n"
        "push {r4, lr}\n"
        "bl Tbb_GetGlobalSubTable\n"
        "bl Tbb_GetRowCount\n"
        "mov r4, r0\n"
        "ldr r0, [pc, #0x14]\n"
        "mov r2, #4\n"
        "mov r1, #0x23\n"
        "ldr r0, [r0]\n"
        "bl engine_func_0025c110\n"
        "add r0, r0, r4\n"
        "pop {r4, pc}\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x003237a0, 40)
extern "C" __attribute__((naked)) void battle_func_003237a0() {
    asm volatile(
        "ldr r0, [pc, #0x1c]\n"
        "push {r4, lr}\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "addne r0, r0, #0xd000\n"
        "ldrne r0, [r0, #0x40]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0044dc20\n"
    );
}

// DECOMP_FUNC(0x003237c8, 60)
extern "C" __attribute__((naked)) void engine_func_003237c8() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "sxth r4, r0\n"
        "mov r0, #1\n"
        "bl engine_func_00259510\n"
        "mov r2, r0\n"
        "ldr r0, [pc, #0x14]\n"
        "mov r1, r4\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0xa8\n"
        "bl func_003946ac\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x00432fc8\n"
    );
}

// DECOMP_FUNC(0x00324138, 28)
extern "C" __attribute__((naked)) void script_vm_func_00324138() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #8]\n"
        "cmp r0, #0\n"
        "movne r1, #0\n"
        "strbne r1, [r0, #0x30]\n"
        "bx lr\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x00324318, 28)
extern "C" __attribute__((naked)) void battle_func_00324318() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "push {r4, lr}\n"
        "ldr r0, [r0]\n"
        "bl battle_func_00267f68\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x00439ca8\n"
    );
}

// DECOMP_FUNC(0x00324738, 120)
extern "C" __attribute__((naked)) void battle_func_00324738() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "ldr r1, [pc, #0x5c]\n"
        "ldr r1, [r1]\n"
        "cmp r1, #0\n"
        "beq .L_00324798\n"
        "ldr r2, [pc, #0x50]\n"
        "cmp r0, #0\n"
        "ldr r0, [r2, r1]\n"
        "add r2, r0, r0, lsl #4\n"
        "add r0, r2, r0, lsl #5\n"
        "add r0, r1, r0, lsl #5\n"
        "add r0, r0, #0x3400\n"
        "add r0, r0, #0x254\n"
        "ldrhne r0, [r0, #0x4a]\n"
        "beq .L_00324784\n"
        ".L_0032477c:\n"
        "bl battle_func_0028df54\n"
        "b .L_003247a0\n"
        ".L_00324784:\n"
        "ldrsb r0, [r0]\n"
        "bl camp_func_002a89e4\n"
        "ldrh r0, [r0, #0x46]\n"
        "nop \n"
        "b .L_0032477c\n"
        ".L_00324798:\n"
        "mov r0, #0\n"
        "bl battle_func_0028df54\n"
        ".L_003247a0:\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0044dc20\n"
        ".word 0x0000cf78\n"
    );
}

// DECOMP_FUNC(0x00324d1c, 44)
extern "C" __attribute__((naked)) void func_00324d1c() {
    asm volatile(
        "add r3, r0, r0, lsl #3\n"
        "add r0, r3, r0, lsl #5\n"
        "ldr r3, [pc, #0x18]\n"
        "add r1, r1, r1, lsl #2\n"
        "mov r2, #4\n"
        "add r0, r3, r0, lsl #3\n"
        "add r1, r2, r1, lsl #2\n"
        "ldr r0, [r0, #0x13c]\n"
        "ldrsh r0, [r0, r1]\n"
        "bx lr\n"
        ".word 0x00478000\n"
    );
}

// DECOMP_FUNC(0x003253d8, 56)
extern "C" __attribute__((naked)) void ui_func_003253d8() {
    asm volatile(
        "ldr r0, [pc, #0x2c]\n"
        "push {r4, lr}\n"
        "mov r1, #1\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_00242a80\n"
        "bl ui_func_00293c98\n"
        "add r1, r0, #0x4000\n"
        "add r1, r1, #0x4a0\n"
        "mov r0, #1\n"
        "ldr r2, [r1]\n"
        "orr r2, r2, #0x20000000\n"
        "str r2, [r1]\n"
        "pop {r4, pc}\n"
        ".word 0x00439ca8\n"
    );
}

// DECOMP_FUNC(0x0032703c, 56)
extern "C" __attribute__((naked)) void camp_func_0032703c() {
    asm volatile(
        "mov r0, #0x32\n"
        "mov r1, #1\n"
        "push {r4, lr}\n"
        "bl Tbb_GetGlobalSubTable\n"
        "bl Tbb_GetRowCount\n"
        "mov r4, r0\n"
        "ldr r0, [pc, #0x14]\n"
        "mov r2, #1\n"
        "mov r1, #0x28\n"
        "ldr r0, [r0]\n"
        "bl engine_func_0025c110\n"
        "add r0, r0, r4\n"
        "pop {r4, pc}\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x003275f4, 64)
extern "C" __attribute__((naked)) void script_vm_func_003275f4() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r0\n"
        "ldr r6, [pc, #0x2c]\n"
        "mov r4, #0\n"
        ".L_00327604:\n"
        "ldr r0, [r6, r4, lsl #2]\n"
        "bl battle_func_002bf41c\n"
        "cmp r0, #0\n"
        "nop \n"
        "beq .L_00327628\n"
        "add r4, r4, #1\n"
        "cmp r4, #4\n"
        "blt .L_00327604\n"
        "pop {r4, r5, r6, pc}\n"
        ".L_00327628:\n"
        "str r5, [r6, r4, lsl #2]\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x00493790\n"
    );
}

// DECOMP_FUNC(0x00327bd0, 76)
extern "C" __attribute__((naked)) void battle_func_00327bd0() {
    asm volatile(
        "ldr r0, [pc, #0x40]\n"
        "push {r4, lr}\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0027eb98\n"
        "ldr r0, [r0, #0x20]\n"
        "ldrsh r1, [r0, #0x90]\n"
        "cmp r1, #0\n"
        "ble .L_00327bfc\n"
        "mov r0, #1\n"
        "bl battle_func_0028df54\n"
        "b .L_00327c10\n"
        ".L_00327bfc:\n"
        "ldrsh r0, [r0, #0x94]\n"
        "cmp r0, #0\n"
        "movgt r0, #1\n"
        "movle r0, #0\n"
        "bl battle_func_0028df54\n"
        ".L_00327c10:\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x00327d24, 108)
extern "C" __attribute__((naked)) void ui_func_00327d24() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "mov r4, r0\n"
        "add r0, r0, #0x4900\n"
        "ldrh r1, [r0, #0x70]\n"
        "strh r1, [r0, #0x68]\n"
        "ldrh r1, [r0, #0x72]\n"
        "strh r1, [r0, #0x6a]\n"
        "ldr r0, [pc, #0x40]\n"
        "ldr r0, [r0]\n"
        "bl func_003af2d0\n"
        "add r0, r4, #0x4000\n"
        "add r0, r0, #0x4a0\n"
        "ldr r1, [r0]\n"
        "tst r1, #0x1000\n"
        "beq .L_00327d78\n"
        "ldr r2, [r0]\n"
        "bic r2, r2, #0x1000\n"
        "str r2, [r0]\n"
        "mov r0, r4\n"
        "bl script_vm_func_00255198\n"
        ".L_00327d78:\n"
        "mov r1, #1\n"
        "mov r0, r4\n"
        "bl func_00338294\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x00439ca8\n"
    );
}

// DECOMP_FUNC(0x00328578, 120)
extern "C" __attribute__((naked)) void engine_func_00328578() {
    asm volatile(
        "push {r4, r5, r6, r7, r8, lr}\n"
        "mov r5, r2\n"
        "mov r7, r0\n"
        "mov r8, r1\n"
        "mov r6, r3\n"
        "bl AsdMdlManager_func_002a135c\n"
        "mov r4, r0\n"
        "ldr r0, [r0, #8]\n"
        "mov r1, r8\n"
        "str r5, [r0, #8]\n"
        "mov r0, r7\n"
        "bl AsdModel_func_002b2b78\n"
        "mov r1, r0\n"
        "ldr r0, [r4, #8]\n"
        "str r1, [r0, #4]\n"
        "ldr r2, [r6, #8]\n"
        "ldr r0, [r4, #8]\n"
        "mov r1, r5\n"
        "bl engine_func_00328bd4\n"
        "ldr r0, [r4, #8]\n"
        "bl AsdModel_func_002a94e8\n"
        "mov r0, r4\n"
        "bl AsdMdlManager_func_002b2928\n"
        "ldr r0, [pc, #0x10]\n"
        "mov r2, #0\n"
        "mov r1, r4\n"
        "bl AsdList_func_002b2814\n"
        "mov r0, r4\n"
        "pop {r4, r5, r6, r7, r8, pc}\n"
        ".word 0x004dad60\n"
    );
}

// DECOMP_FUNC(0x003285f0, 104)
extern "C" __attribute__((naked)) void engine_func_003285f0() {
    asm volatile(
        "push {r4, r5, r6, r7, r8, lr}\n"
        "mov r6, r0\n"
        "mov r7, r1\n"
        "mov r5, r2\n"
        "bl AsdMdlManager_func_002a135c\n"
        "mov r4, r0\n"
        "ldr r0, [r0, #8]\n"
        "mov r1, r7\n"
        "str r5, [r0, #8]\n"
        "mov r0, r6\n"
        "bl AsdModel_func_002b2b78\n"
        "mov r1, r0\n"
        "ldr r0, [r4, #8]\n"
        "str r1, [r0, #4]\n"
        "ldr r0, [r4, #8]\n"
        "mov r1, r5\n"
        "bl engine_func_00328c0c\n"
        "mov r0, r4\n"
        "bl AsdMdlManager_func_002b2928\n"
        "ldr r0, [pc, #0x10]\n"
        "mov r2, #0\n"
        "mov r1, r4\n"
        "bl AsdList_func_002b2814\n"
        "mov r0, r4\n"
        "pop {r4, r5, r6, r7, r8, pc}\n"
        ".word 0x004dad60\n"
    );
}

// DECOMP_FUNC(0x003286a4, 32)
extern "C" __attribute__((naked)) void func_003286a4() {
    asm volatile(
        "ldr r1, [pc, #0x14]\n"
        "ldr r0, [r1, #0x34]\n"
        "ldr r0, [r0, #0x34]\n"
        "cmp r0, #0\n"
        "strne r0, [r1, #0x38]\n"
        "mov r0, #0\n"
        "bx lr\n"
        ".word 0x0044ea80\n"
    );
}

// DECOMP_FUNC(0x003286d4, 44)
extern "C" __attribute__((naked)) void func_003286d4() {
    asm volatile(
        "ldr r1, [pc, #0x1c]\n"
        "ldr r0, [pc, #0x1c]\n"
        "ldrb r2, [r1, #0x88]\n"
        "strb r2, [r0, #2]\n"
        "ldrb r2, [r1, #0x89]\n"
        "strb r2, [r0, #3]\n"
        "ldrb r1, [r1, #0x8a]\n"
        "strb r1, [r0, #4]\n"
        "bx lr\n"
        ".word 0x004d8b40\n"
        ".word 0x0044ea80\n"
    );
}

// DECOMP_FUNC(0x00328700, 72)
extern "C" __attribute__((naked)) void battle_func_00328700() {
    asm volatile(
        "ldr r0, [pc, #0x38]\n"
        "push {r4, lr}\n"
        "ldr r0, [r0]\n"
        "cmp r0, #0\n"
        "beq .L_00328738\n"
        "ldr r1, [pc, #0x28]\n"
        "ldr r1, [r1, r0]\n"
        "add r2, r1, r1, lsl #4\n"
        "add r1, r2, r1, lsl #5\n"
        "add r0, r0, r1, lsl #5\n"
        "add r0, r0, #0x3c00\n"
        "add r0, r0, #0x54\n"
        "ldrh r0, [r0, #8]\n"
        "bl battle_func_0028df54\n"
        ".L_00328738:\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0044dc20\n"
        ".word 0x0000cf78\n"
    );
}

// DECOMP_FUNC(0x00328a00, 40)
extern "C" __attribute__((naked)) void battle_func_00328a00() {
    asm volatile(
        "ldr r0, [pc, #0x1c]\n"
        "push {r4, lr}\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0x6c00\n"
        "add r0, r0, #0x78\n"
        "ldr r0, [r0]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
        ".word 0x0043dd68\n"
    );
}
