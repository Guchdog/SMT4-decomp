#include "types.h"

// Call targets are declared by ledger name so the ARM CALL relocations remain
// explicit and can be checked against their known code addresses.
extern "C" void AsdSequence_func_002c59b8();
extern "C" void AsdTMTexTable_func_002c4e28();
extern "C" void Npc2d_func_00327634();
extern "C" void Tbb_GetGlobalSubTable();
extern "C" void Tbb_GetPayloadData();
extern "C" void battle_func_00245414();
extern "C" void battle_func_0028df54();
extern "C" void battle_func_002931cc();
extern "C" void battle_func_002934d4();
extern "C" void battle_func_002b6e60();
extern "C" void camp_func_0024ec64();
extern "C" void camp_func_0029c468();
extern "C" void camp_func_0029c49c();
extern "C" void camp_func_0029ed08();
extern "C" void camp_func_002a0fac();
extern "C" void camp_func_002a6214();
extern "C" void camp_func_0036f11c();
extern "C" void engine_func_0023a690();
extern "C" void engine_func_00246874();
extern "C" void engine_func_00259510();
extern "C" void engine_func_0027ddb0();
extern "C" void engine_func_0028949c();
extern "C" void engine_func_00296f60();
extern "C" void engine_func_002bb648();
extern "C" void engine_func_002bb6b8();
extern "C" void engine_func_002c2be8();
extern "C" void engine_func_002d1ae8();
extern "C" void engine_func_002d8568();
extern "C" void engine_func_002e12d0();
extern "C" void engine_func_00355160();
extern "C" void func_00146df8();
extern "C" void func_0014ff34();
extern "C" void func_0023a308();
extern "C" void func_002977b0();
extern "C" void func_002a6d94();
extern "C" void func_002bbd40();
extern "C" void func_002f463c();
extern "C" void func_0033f5d4();
extern "C" void func_00356dcc();
extern "C" void func_0035aea8();
extern "C" void func_003ea258();
extern "C" void func_003f8aa8();
extern "C" void nn_sdk_func_00239c50();
extern "C" void script_vm_func_0019dfbc();
extern "C" void script_vm_func_00247214();
extern "C" void script_vm_func_00254674();
extern "C" void script_vm_func_00259544();
extern "C" void script_vm_func_0027db24();
extern "C" void script_vm_func_0027de00();
extern "C" void script_vm_func_00287c44();
extern "C" void script_vm_func_002899c4();
extern "C" void script_vm_func_002912f4();
extern "C" void script_vm_func_00295780();
extern "C" void script_vm_func_00295798();
extern "C" void script_vm_func_002aec80();
extern "C" void script_vm_func_002b66ec();
extern "C" void script_vm_func_002c0ba8();
extern "C" void script_vm_func_002eb59c();
extern "C" void script_vm_func_002eb634();
extern "C" void ui_func_00282b94();
extern "C" void ui_func_00293c98();
extern "C" void ui_func_002adb40();
extern "C" void ui_func_002bbd58();
extern "C" void ui_func_002bbdac();
extern "C" void ui_func_002bffbc();
extern "C" void ui_func_002c0b94();
extern "C" void ui_func_002c17d4();
extern "C" void ui_func_0037dc24();
extern "C" void unite_func_00233804();

// DECOMP_FUNC(0x001fc4f4, 40)
extern "C" __attribute__((naked)) void engine_func_001fc4f4() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "and r0, r0, #0xff\n"
        "bl ui_func_002c17d4\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0021eb10, 40)
extern "C" __attribute__((naked)) void engine_func_0021eb10() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "and r0, r0, #0xff\n"
        "bl ui_func_002bffbc\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0022b1d0, 40)
extern "C" __attribute__((naked)) void engine_func_0022b1d0() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r3, #0xa\n"
        "mov r2, #5\n"
        "mov r1, #0x2a\n"
        "add r0, r0, #0x74\n"
        "bl unite_func_00233804\n"
        "mov r0, #1\n"
        "strb r0, [r4, #0x84]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00234b08, 40)
extern "C" __attribute__((naked)) void script_vm_func_00234b08() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldrd r0, r1, [r4]\n"
        "orrs r2, r0, r1\n"
        "beq .L_19a_00234b08_00234b2c\n"
        "bl func_0023a308\n"
        "mov r0, #0\n"
        "str r0, [r4]\n"
        "str r0, [r4, #4]\n"
        ".L_19a_00234b08_00234b2c:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00238e18, 40)
extern "C" __attribute__((naked)) void ui_func_00238e18() {
    asm volatile(
        "push {r4, lr}\n"
        "cmp r1, #0\n"
        "mov r4, r0\n"
        "beq .L_19a_00238e18_00238e30\n"
        "bl ui_func_002adb40\n"
        "b .L_19a_00238e18_00238e38\n"
        ".L_19a_00238e18_00238e30:\n"
        "nop \n"
        "bl script_vm_func_002912f4\n"
        ".L_19a_00238e18_00238e38:\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0023953c, 40)
extern "C" __attribute__((naked)) void ui_func_0023953c() {
    asm volatile(
        "push {r4, lr}\n"
        "cmp r1, #0\n"
        "mov r4, r0\n"
        "beq .L_19a_0023953c_00239554\n"
        "bl ui_func_002adb40\n"
        "b .L_19a_0023953c_0023955c\n"
        ".L_19a_0023953c_00239554:\n"
        "nop \n"
        "bl script_vm_func_002912f4\n"
        ".L_19a_0023953c_0023955c:\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00247344, 40)
extern "C" __attribute__((naked)) void script_vm_func_00247344() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002b66ec\n"
        "ldrsh r0, [r0, #0x74]\n"
        "cmn r0, #9\n"
        "movle r0, #5\n"
        "ble .L_19a_00247344_00247368\n"
        "cmp r0, #9\n"
        "movge r0, #4\n"
        "movlt r0, #1\n"
        ".L_19a_00247344_00247368:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00255398, 40)
extern "C" __attribute__((naked)) void script_vm_func_00255398() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r0\n"
        "mov r4, r1\n"
        "bl ui_func_00293c98\n"
        "mov r1, r5\n"
        "bl ui_func_00282b94\n"
        "cmp r0, #0\n"
        "addne r0, r0, r4, lsl #1\n"
        "ldrshne r0, [r0, #0x72]\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x002741cc, 40)
extern "C" __attribute__((naked)) void script_vm_func_002741cc() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, #0\n"
        ".L_19a_002741cc_002741d4:\n"
        "mov r2, #1\n"
        "mov r1, #0\n"
        "add r0, r4, #0x310\n"
        "bl script_vm_func_002899c4\n"
        "add r4, r4, #1\n"
        "cmp r4, #0x10\n"
        "blt .L_19a_002741cc_002741d4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00288aac, 40)
extern "C" __attribute__((naked)) void func_00288aac() {
    asm volatile(
        "str lr, [sp, #-4]!\n"
        "sub sp, sp, #0xc\n"
        "mov r3, r0\n"
        "stm sp, {r1, r2}\n"
        "mov r2, #9\n"
        "mov r1, #0x13\n"
        "mov r0, #2\n"
        "bl script_vm_func_002aec80\n"
        "add sp, sp, #0xc\n"
        "pop {pc}\n"
    );
}

// DECOMP_FUNC(0x0028f134, 40)
extern "C" __attribute__((naked)) void script_vm_func_0028f134() {
    asm volatile(
        "push {r4, lr}\n"
        "bl battle_func_002b6e60\n"
        "add r1, r0, #0x600\n"
        "mov r2, #0\n"
        "ldrh r3, [r1, #8]\n"
        "orr r3, r3, #1\n"
        "strh r3, [r1, #8]\n"
        "strh r2, [r0, #0x46]\n"
        "strh r2, [r1, #4]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0029066c, 40)
extern "C" __attribute__((naked)) void script_vm_func_0029066c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0b94\n"
        "add r0, r0, #0x24800\n"
        "add r0, r0, #0x384\n"
        "ldrb r0, [r0]\n"
        "sub r0, r0, #1\n"
        "cmp r0, #2\n"
        "movls r0, #1\n"
        "movhi r0, #0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002a0fc4, 40)
extern "C" __attribute__((naked)) void func_002a0fc4() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0, #0x18]\n"
        "cmp r0, #0\n"
        "beq .L_19a_002a0fc4_002a0fe8\n"
        "add r0, r4, #0x18\n"
        "bl func_0035aea8\n"
        "mov r0, #0\n"
        "str r0, [r4, #0x18]\n"
        ".L_19a_002a0fc4_002a0fe8:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002b70f0, 40)
extern "C" __attribute__((naked)) void func_002b70f0() {
    asm volatile(
        "str lr, [sp, #-4]!\n"
        "sub sp, sp, #0xc\n"
        "strd r2, r3, [sp]\n"
        "mov r3, r1\n"
        "mov r2, r0\n"
        "mov r1, #0x13\n"
        "mov r0, #2\n"
        "bl script_vm_func_002aec80\n"
        "add sp, sp, #0xc\n"
        "pop {pc}\n"
    );
}

// DECOMP_FUNC(0x002cd6bc, 40)
extern "C" __attribute__((naked)) void camp_func_002cd6bc() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl camp_func_0029c49c\n"
        "mov r2, #0\n"
        "mov r1, r4\n"
        "bl camp_func_0029c468\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002cd8e8, 40)
extern "C" __attribute__((naked)) void engine_func_002cd8e8() {
    asm volatile(
        "mov r0, #1\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r1, r4\n"
        "bl script_vm_func_00259544\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002d7804, 40)
extern "C" __attribute__((naked)) void camp_func_002d7804() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl camp_func_002a0fac\n"
        "add r0, r0, r4, lsr #3\n"
        "and r3, r4, #7\n"
        "ldrb r2, [r0, #0x51]\n"
        "mov r1, #1\n"
        "orr r1, r2, r1, lsl r3\n"
        "strb r1, [r0, #0x51]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002d8b98, 40)
extern "C" __attribute__((naked)) void engine_func_002d8b98() {
    asm volatile(
        "mov r0, #1\n"
        "push {r4, lr}\n"
        "bl engine_func_00259510\n"
        "mov r4, r0\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r1, r4\n"
        "bl script_vm_func_00254674\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002dbf80, 40)
extern "C" __attribute__((naked)) void ui_func_002dbf80() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "mov r4, r0\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "add r4, r4, #0x4800\n"
        "add r4, r4, #0x1dc\n"
        "str r0, [r4]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002f5f38, 40)
extern "C" __attribute__((naked)) void engine_func_002f5f38() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl Npc2d_func_00327634\n"
        "mov r4, r0\n"
        "bl engine_func_002d8568\n"
        "mov r0, r4\n"
        "bl engine_func_0028949c\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002f6154, 40)
extern "C" __attribute__((naked)) void script_vm_func_002f6154() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl script_vm_func_0027de00\n"
        "mov r0, r4\n"
        "bl script_vm_func_0027db24\n"
        "bl script_vm_func_002eb59c\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002f617c, 40)
extern "C" __attribute__((naked)) void script_vm_func_002f617c() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl script_vm_func_0027de00\n"
        "mov r0, r4\n"
        "bl script_vm_func_0027db24\n"
        "bl script_vm_func_002eb634\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002f670c, 40)
extern "C" __attribute__((naked)) void engine_func_002f670c() {
    asm volatile(
        "mov r0, #0\n"
        "push {r3, lr}\n"
        "bl engine_func_00296f60\n"
        "str r0, [sp]\n"
        "mov r2, #4\n"
        "mov r1, sp\n"
        "mov r0, #0xd\n"
        "bl AsdSequence_func_002c59b8\n"
        "mov r0, #1\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x002fe8bc, 40)
extern "C" __attribute__((naked)) void engine_func_002fe8bc() {
    asm volatile(
        "mov r0, #1\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r1, r4\n"
        "bl engine_func_002d1ae8\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002ffd94, 40)
extern "C" __attribute__((naked)) void ui_func_002ffd94() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "add r0, r0, #0x4000\n"
        "add r0, r0, #0x4a0\n"
        "ldr r0, [r0]\n"
        "ands r0, r0, #2\n"
        "movne r0, #1\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002fffec, 40)
extern "C" __attribute__((naked)) void script_vm_func_002fffec() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "mov r1, #1\n"
        "bl script_vm_func_00295798\n"
        "mov r0, #1\n"
        "bl script_vm_func_00295780\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030b578, 40)
extern "C" __attribute__((naked)) void engine_func_0030b578() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl camp_func_0024ec64\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00310724, 40)
extern "C" __attribute__((naked)) void camp_func_00310724() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r1, #0\n"
        "mov r0, #0x15\n"
        "bl Tbb_GetGlobalSubTable\n"
        "bl Tbb_GetPayloadData\n"
        "add r1, r4, r4, lsl #3\n"
        "add r1, r1, r4, lsl #4\n"
        "add r0, r0, r1, lsl #2\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00311158, 40)
extern "C" __attribute__((naked)) void engine_func_00311158() {
    asm volatile(
        "mov r0, #1\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r1, r4\n"
        "bl func_002f463c\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00312bd8, 40)
extern "C" __attribute__((naked)) void engine_func_00312bd8() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl ui_func_00293c98\n"
        "add r0, r0, #0x4800\n"
        "add r0, r0, #0x178\n"
        "str r4, [r0]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0031cca4, 40)
extern "C" __attribute__((naked)) void engine_func_0031cca4() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl camp_func_0029ed08\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0031ecf4, 40)
extern "C" __attribute__((naked)) void engine_func_0031ecf4() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "mov r0, #1\n"
        "bl engine_func_00296f60\n"
        "sxth r0, r4\n"
        "bl battle_func_00245414\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0033d638, 40)
extern "C" __attribute__((naked)) void func_0033d638() {
    asm volatile(
        "str lr, [sp, #-4]!\n"
        "sub sp, sp, #0xc\n"
        "mov ip, #0\n"
        "vldr s2, [sp, #0x10]\n"
        "vstr s2, [sp]\n"
        "str ip, [sp, #4]\n"
        "str ip, [sp, #8]\n"
        "bl func_0033f5d4\n"
        "add sp, sp, #0xc\n"
        "pop {pc}\n"
    );
}

// DECOMP_FUNC(0x0033fa2c, 40)
extern "C" __attribute__((naked)) void ui_func_0033fa2c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0b94\n"
        "add r0, r0, #0x1f800\n"
        "mov r1, #0\n"
        "str r1, [r0, #0x72]\n"
        "str r1, [r0, #0x76]\n"
        "str r1, [r0, #0x7a]\n"
        "str r1, [r0, #0x7e]\n"
        "strh r1, [r0, #0x82]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0034355c, 40)
extern "C" __attribute__((naked)) void camp_func_0034355c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl ui_func_002bbdac\n"
        "add r1, r4, #0x1000\n"
        "ldr r0, [r4, #0x52c]\n"
        "add r1, r1, #0x18c\n"
        "bl ui_func_002bbd58\n"
        "mov r0, #0\n"
        "strb r0, [r4, #0x5f4]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00350024, 40)
extern "C" __attribute__((naked)) void func_00350024() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "add r0, r0, #0x158\n"
        "bl engine_func_0023a690\n"
        "cmp r0, #0\n"
        "moveq r0, #7\n"
        "streq r0, [r4, #0xc]\n"
        "moveq r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00355304, 40)
extern "C" __attribute__((naked)) void engine_func_00355304() {
    asm volatile(
        "push {r4, lr}\n"
        "sub sp, sp, #0x10\n"
        "add lr, sp, #0x18\n"
        "ldm lr, {r4, ip}\n"
        "stm sp, {r3, r4, ip}\n"
        "mov r3, r2\n"
        "mov r2, #0\n"
        "bl engine_func_00355160\n"
        "add sp, sp, #0x10\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0035637c, 40)
extern "C" __attribute__((naked)) void func_0035637c() {
    asm volatile(
        "push {r3, r4, r5, lr}\n"
        "mov r5, r2\n"
        "mov r4, r3\n"
        "bl nn_sdk_func_00239c50\n"
        "str r0, [sp]\n"
        "mov r2, r5\n"
        "mov r3, r4\n"
        "mov r0, sp\n"
        "bl func_00356dcc\n"
        "pop {r3, r4, r5, pc}\n"
    );
}

// DECOMP_FUNC(0x0039d730, 40)
extern "C" __attribute__((naked)) void script_vm_func_0039d730() {
    asm volatile(
        "mov r0, #0x400\n"
        "push {r4, lr}\n"
        "bl script_vm_func_002c0ba8\n"
        "cmp r0, #0\n"
        "beq .L_19a_0039d730_0039d754\n"
        "mov r0, #0x76\n"
        "bl battle_func_002931cc\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        ".L_19a_0039d730_0039d754:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003ab9c0, 40)
extern "C" __attribute__((naked)) void script_vm_func_003ab9c0() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0, #0x5a0]\n"
        "bl script_vm_func_0019dfbc\n"
        "cmp r0, #2\n"
        "bne .L_19a_003ab9c0_003ab9e4\n"
        "mov r0, #3\n"
        "mov r1, #0\n"
        "strd r0, r1, [r4, #0x14]\n"
        ".L_19a_003ab9c0_003ab9e4:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003db9e0, 40)
extern "C" __attribute__((naked)) void ui_func_003db9e0() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "bl battle_func_002934d4\n"
        "cmp r0, #0\n"
        "bne .L_19a_003db9e0_003dba00\n"
        "bl engine_func_00246874\n"
        "cmp r0, #0\n"
        "beq .L_19a_003db9e0_003dba04\n"
        ".L_19a_003db9e0_003dba00:\n"
        "mov r0, #1\n"
        ".L_19a_003db9e0_003dba04:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003e64a4, 40)
extern "C" __attribute__((naked)) void func_003e64a4() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #0\n"
        "mov r1, sp\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "beq .L_19a_003e64a4_003e64c8\n"
        "ldr r0, [sp]\n"
        "asr r0, r0, #8\n"
        "sxtb r0, r0\n"
        ".L_19a_003e64a4_003e64c8:\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x003e6acc, 40)
extern "C" __attribute__((naked)) void func_003e6acc() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #0\n"
        "mov r1, sp\n"
        "add r0, r0, #4\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "moveq r0, #1\n"
        "andne r0, r0, #0xff\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x003e6b4c, 40)
extern "C" __attribute__((naked)) void func_003e6b4c() {
    asm volatile(
        "push {r3, r4, r5, lr}\n"
        "mov r4, r0\n"
        "mov r2, #8\n"
        "mov r1, sp\n"
        "add r0, r0, #0x14\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "addne r0, r0, r4\n"
        "pop {r3, r4, r5, pc}\n"
    );
}

// DECOMP_FUNC(0x003e7e28, 40)
extern "C" __attribute__((naked)) void func_003e7e28() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r0, r1\n"
        "ldr r1, [sp, #0xc]\n"
        "mov ip, r2\n"
        "mov r2, r3\n"
        "str r1, [sp]\n"
        "ldr r3, [sp, #8]\n"
        "mov r1, ip\n"
        "bl ui_func_0037dc24\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x003e852c, 40)
extern "C" __attribute__((naked)) void func_003e852c() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #0\n"
        "mov r1, sp\n"
        "add r0, r0, #4\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "moveq r0, #0x3c\n"
        "andne r0, r0, #0xff\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x003e85c4, 40)
extern "C" __attribute__((naked)) void func_003e85c4() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #2\n"
        "mov r1, sp\n"
        "add r0, r0, #4\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "moveq r0, #0x40\n"
        "andne r0, r0, #0xff\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x003e8660, 40)
extern "C" __attribute__((naked)) void func_003e8660() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #1\n"
        "mov r1, sp\n"
        "add r0, r0, #4\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "ldrne r0, [sp]\n"
        "moveq r0, #0x7f\n"
        "andne r0, r0, #0xff\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x003ea4d0, 40)
extern "C" __attribute__((naked)) void func_003ea4d0() {
    asm volatile(
        "str lr, [sp, #-4]!\n"
        "bl func_003ea258\n"
        "sub r1, r0, #0xff00\n"
        "subs r1, r1, #0xff\n"
        "movne r0, #1\n"
        "moveq r0, #0\n"
        "pop {pc}\n"
        "ldr r0, [r0, #8]\n"
        "ldrb r0, [r0, #0x14]\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x003f9078, 40)
extern "C" __attribute__((naked)) void func_003f9078() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl func_003f8aa8\n"
        "ldrh r0, [r0, #2]\n"
        "vldr s2, [r4, #8]\n"
        "vmov s0, r0\n"
        "vcvt.f32.u32 s1, s0\n"
        "vldr s0, [r4, #0xc]\n"
        "vmla.f32 s0, s1, s2\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0010f4bc, 44)
extern "C" __attribute__((naked)) void func_0010f4bc() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl func_002bbd40\n"
        "ldrb r1, [r0, r4, lsr #3]\n"
        "and r3, r4, #7\n"
        "mov r2, #1\n"
        "lsl r0, r2, r3\n"
        "and r0, r0, #0xff\n"
        "ands r0, r0, r1\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001218b0, 44)
extern "C" __attribute__((naked)) void func_001218b0() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldrb r0, [r0, #0x1f4]\n"
        "cmp r0, #0\n"
        "beq .L_19a_001218b0_001218d8\n"
        "mov r0, #1\n"
        "strb r0, [r4, #0x1f7]\n"
        "bl func_00146df8\n"
        "mov r0, #0\n"
        "strb r0, [r4, #0x1f4]\n"
        ".L_19a_001218b0_001218d8:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001481e4, 44)
extern "C" __attribute__((naked)) void func_001481e4() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r0\n"
        "mov r5, r1\n"
        "bl engine_func_002bb6b8\n"
        "mov r1, r5\n"
        "mov r0, r4\n"
        "bl func_0014ff34\n"
        "mov r4, r0\n"
        "bl engine_func_002bb648\n"
        "mov r0, r4\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0014d120, 44)
extern "C" __attribute__((naked)) void func_0014d120() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #2\n"
        "mov r1, sp\n"
        "add r0, r0, #4\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "beq .L_19a_0014d120_0014d148\n"
        "ldr r0, [sp]\n"
        "lsl r0, r0, #0x10\n"
        "lsr r0, r0, #0x18\n"
        ".L_19a_0014d120_0014d148:\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x00151fc8, 44)
extern "C" __attribute__((naked)) void func_00151fc8() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #0\n"
        "mov r1, sp\n"
        "add r0, r0, #8\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "beq .L_19a_00151fc8_00151ff0\n"
        "ldr r0, [sp]\n"
        "lsl r0, r0, #0x10\n"
        "lsr r0, r0, #0x18\n"
        ".L_19a_00151fc8_00151ff0:\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x001520f4, 44)
extern "C" __attribute__((naked)) void func_001520f4() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #1\n"
        "mov r1, sp\n"
        "add r0, r0, #0x14\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "beq .L_19a_001520f4_0015211c\n"
        "ldr r0, [sp]\n"
        "lsl r0, r0, #0x10\n"
        "lsr r0, r0, #0x18\n"
        ".L_19a_001520f4_0015211c:\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x00152144, 44)
extern "C" __attribute__((naked)) void func_00152144() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #2\n"
        "mov r1, sp\n"
        "add r0, r0, #0x14\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "beq .L_19a_00152144_0015216c\n"
        "ldr r0, [sp]\n"
        "lsl r0, r0, #0x10\n"
        "lsr r0, r0, #0x18\n"
        ".L_19a_00152144_0015216c:\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x00192778, 44)
extern "C" __attribute__((naked)) void engine_func_00192778() {
    asm volatile(
        "mov r0, #0x1d\n"
        "push {r4, lr}\n"
        "bl AsdTMTexTable_func_002c4e28\n"
        "mov r4, #0\n"
        ".L_19a_00192778_00192788:\n"
        "mov r1, r4\n"
        "mov r0, #0x1d\n"
        "bl camp_func_002a6214\n"
        "add r4, r4, #1\n"
        "cmp r4, #3\n"
        "blt .L_19a_00192778_00192788\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00192810, 44)
extern "C" __attribute__((naked)) void func_00192810() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0, #0x1c]\n"
        "cmp r0, #0\n"
        "beq .L_19a_00192810_00192838\n"
        "mov r0, r4\n"
        "bl func_002977b0\n"
        "add r0, r0, #1\n"
        "str r0, [r4, #0x18]\n"
        "mov r0, #1\n"
        ".L_19a_00192810_00192838:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001ed3c8, 44)
extern "C" __attribute__((naked)) void engine_func_001ed3c8() {
    asm volatile(
        "mov r0, #1\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r1, r4\n"
        "bl script_vm_func_00259544\n"
        "bl engine_func_0027ddb0\n"
        "mov r0, #2\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00200410, 44)
extern "C" __attribute__((naked)) void camp_func_00200410() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl camp_func_002a0fac\n"
        "add r1, r0, r4, lsr #3\n"
        "and r2, r4, #7\n"
        "ldrb r1, [r1, #0x51]\n"
        "mov r0, #1\n"
        "tst r1, r0, lsl r2\n"
        "movne r0, #0\n"
        "moveq r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002012ec, 44)
extern "C" __attribute__((naked)) void engine_func_002012ec() {
    asm volatile(
        "mov r0, #1\n"
        "push {r4, lr}\n"
        "bl engine_func_00259510\n"
        "mov r4, r0\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r1, r4\n"
        "bl script_vm_func_00254674\n"
        "bl engine_func_0027ddb0\n"
        "mov r0, #2\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00222894, 44)
extern "C" __attribute__((naked)) void engine_func_00222894() {
    asm volatile(
        "mov r0, #1\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r2, #0\n"
        "mov r1, r4\n"
        "bl script_vm_func_00287c44\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00241e88, 44)
extern "C" __attribute__((naked)) void camp_func_00241e88() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0, #8]\n"
        "cmp r0, #0\n"
        "beq .L_19a_00241e88_00241eb0\n"
        "bl engine_func_002e12d0\n"
        "add r0, r4, #0xc\n"
        "bl camp_func_0036f11c\n"
        "mov r0, #0\n"
        "str r0, [r4, #8]\n"
        ".L_19a_00241e88_00241eb0:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00245630, 44)
extern "C" __attribute__((naked)) void engine_func_00245630() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "cmp r3, #0\n"
        "mov r0, r2\n"
        "movne r2, #1\n"
        "moveq r2, #0\n"
        "bl script_vm_func_00247214\n"
        "add r4, r4, #0x1c00\n"
        "add r4, r4, #0xfc\n"
        "str r0, [r4]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002553c0, 44)
extern "C" __attribute__((naked)) void script_vm_func_002553c0() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r6, r0\n"
        "mov r5, r1\n"
        "mov r4, r2\n"
        "bl ui_func_00293c98\n"
        "mov r1, r6\n"
        "bl ui_func_00282b94\n"
        "cmp r0, #0\n"
        "addne r0, r0, r5, lsl #1\n"
        "strhne r4, [r0, #0x72]\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0025bcc4, 44)
extern "C" __attribute__((naked)) void ui_func_0025bcc4() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0xec\n"
        "vstmia r0, {s0, s1, s2, s3}\n"
        "ldr r0, [r4]\n"
        "add r0, r0, #0xec\n"
        "bl engine_func_002c2be8\n"
        "ldr r1, [r4]\n"
        "str r0, [r1, #0x108]\n"
        "pop {r4, pc}\n"
    );
}
