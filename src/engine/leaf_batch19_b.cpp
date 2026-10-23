#include "types.h"

// Call targets are declared by ledger name so the ARM CALL relocations remain
// explicit and can be checked against their known code addresses.
extern "C" void AsdPrimRenderData_func_00346db0();
extern "C" void AsdProcess_func_00118488();
extern "C" void AsdTMTexTable_func_002c5b04();
extern "C" void AsdTexture_func_002bd730();
extern "C" void Npc2d_func_002fdfb8();
extern "C" void Tbb_GetGlobalSubTable();
extern "C" void Tbb_GetPayloadData();
extern "C" void battle_func_0028df54();
extern "C" void battle_func_002b087c();
extern "C" void battle_func_002b6e60();
extern "C" void battle_func_002bc3c8();
extern "C" void battle_func_002bf41c();
extern "C" void battle_func_002c45b8();
extern "C" void camp_func_0022a0c4();
extern "C" void camp_func_0022e58c();
extern "C" void camp_func_0028d5c4();
extern "C" void camp_func_00298a74();
extern "C" void camp_func_002ae4c4();
extern "C" void camp_func_002b4854();
extern "C" void effParts_func_0028c920();
extern "C" void engine_func_00131308();
extern "C" void engine_func_001419bc();
extern "C" void engine_func_001455ec();
extern "C" void engine_func_0015e7c0();
extern "C" void engine_func_0028949c();
extern "C" void engine_func_00289628();
extern "C" void engine_func_00296f60();
extern "C" void engine_func_002acbd8();
extern "C" void engine_func_002adf14();
extern "C" void engine_func_002b47cc();
extern "C" void engine_func_002bd630();
extern "C" void engine_func_002c0bcc();
extern "C" void engine_func_002c2b1c();
extern "C" void engine_func_002c2be8();
extern "C" void engine_func_002c3a24();
extern "C" void engine_func_002c3aa8();
extern "C" void engine_func_002c41e8();
extern "C" void engine_func_002c4360();
extern "C" void engine_func_002c5ab8();
extern "C" void engine_func_002c5e3c();
extern "C" void engine_func_002df524();
extern "C" void engine_func_002e84f0();
extern "C" void engine_func_003da814();
extern "C" void engine_func_003dad58();
extern "C" void engine_func_003dba08();
extern "C" void engine_func_003dc8b8();
extern "C" void func_001372d8();
extern "C" void func_00151d94();
extern "C" void func_0023a24c();
extern "C" void func_002a3438();
extern "C" void func_002a6d94();
extern "C" void func_002b4a0c();
extern "C" void func_002b5a1c();
extern "C" void func_002b7770();
extern "C" void func_002bbd40();
extern "C" void func_003972c8();
extern "C" void func_003f8c24();
extern "C" void nn_sdk_func_003f6188();
extern "C" void script_vm_func_00152af8();
extern "C" void script_vm_func_0019dfbc();
extern "C" void script_vm_func_00262bcc();
extern "C" void script_vm_func_002705f4();
extern "C" void script_vm_func_002a7aa0();
extern "C" void script_vm_func_002b66ec();
extern "C" void script_vm_func_002b6e78();
extern "C" void script_vm_func_002b8b78();
extern "C" void shop_func_002ae650();
extern "C" void ui_func_00259d88();
extern "C" void ui_func_0026f0d8();
extern "C" void ui_func_0027dca0();
extern "C" void ui_func_00293c98();
extern "C" void ui_func_002b902c();
extern "C" void ui_func_002bffbc();
extern "C" void ui_func_002c0ac8();

// DECOMP_FUNC(0x0025bcf0, 44)
extern "C" __attribute__((naked)) void ui_func_0025bcf0() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0xdc\n"
        "vstmia r0, {s0, s1, s2, s3}\n"
        "ldr r0, [r4]\n"
        "add r0, r0, #0xdc\n"
        "bl engine_func_002c2be8\n"
        "ldr r1, [r4]\n"
        "str r0, [r1, #0x104]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0025bd1c, 44)
extern "C" __attribute__((naked)) void ui_func_0025bd1c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0]\n"
        "add r0, r0, #0xcc\n"
        "vstmia r0, {s0, s1, s2, s3}\n"
        "ldr r0, [r4]\n"
        "add r0, r0, #0xcc\n"
        "bl engine_func_002c2be8\n"
        "ldr r1, [r4]\n"
        "str r0, [r1, #0x100]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0025c524, 44)
extern "C" __attribute__((naked)) void battle_func_0025c524() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r1\n"
        "mov r6, r0\n"
        "bl ui_func_002c0ac8\n"
        "mov r4, r0\n"
        "mov r0, r6\n"
        "bl ui_func_00259d88\n"
        "mov r0, #2\n"
        "strb r5, [r4, #0x3d]\n"
        "str r0, [r4, #0x40]\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x002705c8, 44)
extern "C" __attribute__((naked)) void script_vm_func_002705c8() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r0\n"
        "mov r4, r1\n"
        "bl engine_func_002c2b1c\n"
        "mov r1, r0\n"
        "mov r0, r5\n"
        "bl script_vm_func_002705f4\n"
        "cmp r0, #0\n"
        "addne r0, r1, r5\n"
        "strbne r4, [r0, #0xe14]\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x002961cc, 44)
extern "C" __attribute__((naked)) void script_vm_func_002961cc() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r1, #1\n"
        "mov r0, #9\n"
        "bl Tbb_GetGlobalSubTable\n"
        "bl Tbb_GetPayloadData\n"
        "cmp r4, #0x63\n"
        "addlt r0, r0, r4, lsl #2\n"
        "movge r0, #0\n"
        "ldrlt r0, [r0, #-4]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002a7144, 44)
extern "C" __attribute__((naked)) void engine_func_002a7144() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0, #8]\n"
        "cmp r0, #0\n"
        "beq .L_19b_002a7144_002a716c\n"
        "bl AsdTexture_func_002bd730\n"
        "ldr r0, [r4, #0x10]\n"
        "orr r0, r0, #4\n"
        "str r0, [r4, #0x10]\n"
        "mov r0, #1\n"
        ".L_19b_002a7144_002a716c:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002bb774, 44)
extern "C" __attribute__((naked)) void func_002bb774() {
    asm volatile(
        "push {r0, lr}\n"
        "sub sp, sp, #8\n"
        "mov r3, #0\n"
        "add r1, sp, #8\n"
        "mov r0, #7\n"
        "mov r2, #4\n"
        "str r3, [sp]\n"
        "str r3, [sp, #4]\n"
        "bl func_002b5a1c\n"
        "add sp, sp, #0xc\n"
        "pop {pc}\n"
    );
}

// DECOMP_FUNC(0x002bfc88, 44)
extern "C" __attribute__((naked)) void func_002bfc88() {
    asm volatile(
        "push {r3, r4, r5, lr}\n"
        "mov r4, r0\n"
        "mov r5, r1\n"
        "bl battle_func_002bc3c8\n"
        "ldr r0, [r4, #0x1c]\n"
        "str r0, [sp]\n"
        "ldr r1, [r5, #0x24]\n"
        "ldr r0, [r4, #0x24]\n"
        "ldrd r2, r3, [r4, #0x14]\n"
        "bl func_001372d8\n"
        "pop {r3, r4, r5, pc}\n"
    );
}

// DECOMP_FUNC(0x002c0efc, 44)
extern "C" __attribute__((naked)) void func_002c0efc() {
    asm volatile(
        "mov r1, #0\n"
        "str lr, [sp, #-4]!\n"
        "sub sp, sp, #0xc\n"
        "mov r0, #4\n"
        "mov r3, r1\n"
        "mov r2, r1\n"
        "str r1, [sp]\n"
        "str r1, [sp, #4]\n"
        "bl func_002b5a1c\n"
        "add sp, sp, #0xc\n"
        "pop {pc}\n"
    );
}

// DECOMP_FUNC(0x002c4c00, 44)
extern "C" __attribute__((naked)) void camp_func_002c4c00() {
    asm volatile(
        "str lr, [sp, #-4]!\n"
        "sub sp, sp, #0x14\n"
        "add ip, sp, #0x18\n"
        "add lr, sp, #4\n"
        "vldmia ip, {s0, s1, s2, s3}\n"
        "mov ip, #0\n"
        "vstmia lr, {s0, s1, s2, s3}\n"
        "str ip, [sp]\n"
        "bl AsdProcess_func_00118488\n"
        "add sp, sp, #0x14\n"
        "pop {pc}\n"
    );
}

// DECOMP_FUNC(0x002e4008, 44)
extern "C" __attribute__((naked)) void ui_func_002e4008() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "add r1, r0, #0x4000\n"
        "add r1, r1, #0x4a0\n"
        "mov r0, #0xdd\n"
        "ldr r2, [r1]\n"
        "orr r2, r2, #0x100000\n"
        "str r2, [r1]\n"
        "bl script_vm_func_002b8b78\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002e4094, 44)
extern "C" __attribute__((naked)) void ui_func_002e4094() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl ui_func_00293c98\n"
        "mov r1, r4\n"
        "bl ui_func_0027dca0\n"
        "ldrh r0, [r0, #2]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002f127c, 44)
extern "C" __attribute__((naked)) void ui_func_002f127c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "mov r4, r0\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "add r0, r4, r0, lsl #2\n"
        "add r0, r0, #0x2000\n"
        "ldr r0, [r0, #0x2a8]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002f284c, 44)
extern "C" __attribute__((naked)) void func_002f284c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r1\n"
        "ldrh r0, [r0]\n"
        "bl camp_func_002b4854\n"
        "mov r5, r0\n"
        "ldrh r0, [r4]\n"
        "bl camp_func_002b4854\n"
        "ldrb r0, [r0, #0x6f]\n"
        "ldrb r1, [r5, #0x6f]\n"
        "sub r0, r0, r1\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x002f6cc4, 44)
extern "C" __attribute__((naked)) void ui_func_002f6cc4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "add r0, r0, #0x4000\n"
        "add r0, r0, #0x4a0\n"
        "ldr r0, [r0]\n"
        "tst r0, #2\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002fe8f8, 44)
extern "C" __attribute__((naked)) void engine_func_002fe8f8() {
    asm volatile(
        "mov r0, #1\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "mov r0, #0\n"
        "bl engine_func_00296f60\n"
        "mov r1, r4\n"
        "bl engine_func_002df524\n"
        "bl engine_func_002e84f0\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030adbc, 44)
extern "C" __attribute__((naked)) void engine_func_0030adbc() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl ui_func_00293c98\n"
        "add r1, r0, #0x1b4\n"
        "ldr r0, [r0, #0x1b4]\n"
        "add r0, r0, r4\n"
        "str r0, [r1]\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030b5f8, 44)
extern "C" __attribute__((naked)) void ui_func_0030b5f8() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl ui_func_00293c98\n"
        "mov r1, r4\n"
        "bl ui_func_0027dca0\n"
        "ldrsb r0, [r0, #0xd4]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030bf0c, 44)
extern "C" __attribute__((naked)) void engine_func_0030bf0c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r1\n"
        "ldrh r0, [r0]\n"
        "bl engine_func_002b47cc\n"
        "mov r5, r0\n"
        "ldrh r0, [r4]\n"
        "bl engine_func_002b47cc\n"
        "ldrh r0, [r0, #0x98]\n"
        "ldrh r1, [r5, #0x98]\n"
        "sub r0, r0, r1\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0031339c, 44)
extern "C" __attribute__((naked)) void func_0031339c() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r1\n"
        "ldrh r0, [r0]\n"
        "bl camp_func_002ae4c4\n"
        "mov r5, r0\n"
        "ldrh r0, [r4]\n"
        "bl camp_func_002ae4c4\n"
        "ldrb r0, [r0, #0x54]\n"
        "ldrb r1, [r5, #0x54]\n"
        "sub r0, r0, r1\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x003186d4, 44)
extern "C" __attribute__((naked)) void battle_func_003186d4() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl battle_func_002b087c\n"
        "ldrh r0, [r0, #0x16]\n"
        "lsl r0, r0, #0x19\n"
        "lsr r0, r0, #0x1f\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00318700, 44)
extern "C" __attribute__((naked)) void battle_func_00318700() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl battle_func_002b087c\n"
        "ldrh r0, [r0, #0x16]\n"
        "lsl r0, r0, #0x1a\n"
        "lsr r0, r0, #0x1f\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00318998, 44)
extern "C" __attribute__((naked)) void battle_func_00318998() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl battle_func_002b087c\n"
        "ldrh r0, [r0, #0x16]\n"
        "lsl r0, r0, #0x18\n"
        "lsr r0, r0, #0x1f\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0031cccc, 44)
extern "C" __attribute__((naked)) void battle_func_0031cccc() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl battle_func_002b087c\n"
        "ldrh r0, [r0, #0x16]\n"
        "lsl r0, r0, #0x17\n"
        "lsr r0, r0, #0x1f\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0031f548, 44)
extern "C" __attribute__((naked)) void battle_func_0031f548() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl battle_func_002b087c\n"
        "ldrb r0, [r0, #0xa5]\n"
        "lsl r0, r0, #0x1e\n"
        "lsr r0, r0, #0x1f\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003341f4, 44)
extern "C" __attribute__((naked)) void script_vm_func_003341f4() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl script_vm_func_002b66ec\n"
        "ldrsh r1, [r0, #0x1c]\n"
        "cmp r4, r1\n"
        "bgt .L_19b_003341f4_00334218\n"
        "cmp r4, #1\n"
        "movlt r4, #1\n"
        "mov r1, r4\n"
        ".L_19b_003341f4_00334218:\n"
        "strh r1, [r0, #0x2a]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00334220, 44)
extern "C" __attribute__((naked)) void script_vm_func_00334220() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl script_vm_func_002b66ec\n"
        "ldrsh r1, [r0, #0x1e]\n"
        "cmp r4, r1\n"
        "bgt .L_19b_00334220_00334244\n"
        "cmp r4, #1\n"
        "movlt r4, #1\n"
        "mov r1, r4\n"
        ".L_19b_00334220_00334244:\n"
        "strh r1, [r0, #0x2c]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00341c48, 44)
extern "C" __attribute__((naked)) void script_vm_func_00341c48() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0, #0x28]\n"
        "cmp r0, #0\n"
        "beq .L_19b_00341c48_00341c70\n"
        "bl script_vm_func_00152af8\n"
        "ldr r0, [r4, #0x28]\n"
        "bl script_vm_func_002a7aa0\n"
        "mov r0, #0\n"
        "str r0, [r4, #0x28]\n"
        ".L_19b_00341c48_00341c70:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00348d58, 44)
extern "C" __attribute__((naked)) void engine_func_00348d58() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002adf14\n"
        "add r0, r0, r4, lsl #2\n"
        "ldrb r1, [r0, #0x202]\n"
        "ldrb r3, [r0, #0x200]\n"
        "orr r2, r1, #1\n"
        "orr r1, r3, #0x80\n"
        "strb r2, [r0, #0x202]\n"
        "strb r1, [r0, #0x200]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0034ef48, 44)
extern "C" __attribute__((naked)) void nn_sdk_func_0034ef48() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl nn_sdk_func_003f6188\n"
        "cmp r0, #0\n"
        "beq .L_19b_0034ef48_0034ef70\n"
        "mov r0, #0\n"
        "str r0, [r4, #0x58]\n"
        "str r0, [r4, #0x5c]\n"
        "strb r0, [r4, #6]\n"
        "mov r0, #1\n"
        ".L_19b_0034ef48_0034ef70:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00353800, 44)
extern "C" __attribute__((naked)) void func_00353800() {
    asm volatile(
        "push {r0, r1, r4, lr}\n"
        "mov r4, r0\n"
        "add r0, sp, #4\n"
        "bl func_0023a24c\n"
        "lsrs r1, r0, #0x1f\n"
        "bne .L_19b_00353800_00353824\n"
        "ldr r0, [sp, #4]\n"
        "str r0, [r4]\n"
        "mov r0, #0\n"
        ".L_19b_00353800_00353824:\n"
        "add sp, sp, #8\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003577b0, 44)
extern "C" __attribute__((naked)) void func_003577b0() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl func_002a3438\n"
        "ldr r0, [r4, #0x14]!\n"
        "cmp r0, #0\n"
        "beq .L_19b_003577b0_003577d4\n"
        "svc #0x23\n"
        "mov r0, #0\n"
        "str r0, [r4]\n"
        ".L_19b_003577b0_003577d4:\n"
        "sub r0, r4, #0x14\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00357938, 44)
extern "C" __attribute__((naked)) void func_00357938() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002c41e8\n"
        "ldr r0, [r4]\n"
        "cmp r0, #0\n"
        "beq .L_19b_00357938_0035795c\n"
        "svc #0x23\n"
        "mov r0, #0\n"
        "str r0, [r4]\n"
        ".L_19b_00357938_0035795c:\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0037e7cc, 44)
extern "C" __attribute__((naked)) void func_0037e7cc() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldrb r0, [r0, #0xd]\n"
        "cmp r0, #0\n"
        "beq .L_19b_0037e7cc_0037e7f4\n"
        "bl engine_func_002bd630\n"
        "add r1, r4, #0x50\n"
        "bl func_002b7770\n"
        "mov r0, #0\n"
        "strb r0, [r4, #0xd]\n"
        ".L_19b_0037e7cc_0037e7f4:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003834e0, 44)
extern "C" __attribute__((naked)) void script_vm_func_003834e0() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0, #0x5c4]\n"
        "ldr r0, [r0]\n"
        "bl script_vm_func_0019dfbc\n"
        "cmp r0, #2\n"
        "bne .L_19b_003834e0_00383508\n"
        "mov r0, #4\n"
        "mov r1, #0\n"
        "strd r0, r1, [r4, #4]\n"
        ".L_19b_003834e0_00383508:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0038b638, 44)
extern "C" __attribute__((naked)) void func_0038b638() {
    asm volatile(
        "push {r0, r1, r2, lr}\n"
        "add r0, sp, #4\n"
        "bl engine_func_0015e7c0\n"
        "cmp r0, #0\n"
        "beq .L_19b_0038b638_0038b65c\n"
        "add r0, sp, #4\n"
        "ldr r0, [r0, #4]\n"
        "bl func_002b4a0c\n"
        "mov r0, #1\n"
        ".L_19b_0038b638_0038b65c:\n"
        "add sp, sp, #0xc\n"
        "pop {pc}\n"
    );
}

// DECOMP_FUNC(0x003959fc, 44)
extern "C" __attribute__((naked)) void engine_func_003959fc() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0, #0xc]\n"
        "add r5, r0, #0x24\n"
        "mov r0, #0x12c\n"
        "bl engine_func_002c0bcc\n"
        "add r1, r0, #0x96\n"
        "mov r0, #0\n"
        "str r1, [r5, #0x34]\n"
        "str r0, [r4, #0x1c]\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0039729c, 44)
extern "C" __attribute__((naked)) void func_0039729c() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r1, [r0, #4]\n"
        "mov r4, r0\n"
        "bl func_003972c8\n"
        "add r0, r4, #8\n"
        "str r0, [r4, #0x10]\n"
        "mov r1, #0\n"
        "str r0, [r4, #4]\n"
        "strd r0, r1, [r4, #0x1c]\n"
        "str r0, [r4, #0x18]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003a6598, 44)
extern "C" __attribute__((naked)) void shop_func_003a6598() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl shop_func_002ae650\n"
        "cmp r0, #0xa\n"
        "movne r0, #0\n"
        "bne .L_19b_003a6598_003a65c0\n"
        "mov r0, r4\n"
        "bl camp_func_0022e58c\n"
        "cmp r0, #0\n"
        "ldrhne r0, [r0, #0x2a]\n"
        ".L_19b_003a6598_003a65c0:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003c85dc, 44)
extern "C" __attribute__((naked)) void script_vm_func_003c85dc() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, #0\n"
        "bl script_vm_func_002b6e78\n"
        "cmp r0, #2\n"
        "bne .L_19b_003c85dc_003c8600\n"
        "bl battle_func_002b6e60\n"
        "ldrh r0, [r0, #0x46]\n"
        "bl camp_func_0022a0c4\n"
        "ldrh r4, [r0, #6]\n"
        ".L_19b_003c85dc_003c8600:\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003c87f0, 44)
extern "C" __attribute__((naked)) void script_vm_func_003c87f0() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, #0\n"
        "bl script_vm_func_002b6e78\n"
        "cmp r0, #2\n"
        "bne .L_19b_003c87f0_003c8814\n"
        "bl battle_func_002b6e60\n"
        "ldrh r0, [r0, #0x46]\n"
        "bl camp_func_0022a0c4\n"
        "ldrh r4, [r0, #8]\n"
        ".L_19b_003c87f0_003c8814:\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003db5a4, 44)
extern "C" __attribute__((naked)) void engine_func_003db5a4() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_003dad58\n"
        "mov r0, r4\n"
        "bl engine_func_003da814\n"
        "mov r0, r4\n"
        "bl engine_func_003dba08\n"
        "mov r0, r4\n"
        "bl engine_func_003dc8b8\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003e6140, 44)
extern "C" __attribute__((naked)) void func_003e6140() {
    asm volatile(
        "push {r4, lr}\n"
        "ldr r0, [r0, #0xc]\n"
        "cmp r0, #0\n"
        "beq .L_19b_003e6140_003e6160\n"
        "ldr r1, [r0]\n"
        "ldr r1, [r1, #0x14]\n"
        "pop {r4, lr}\n"
        "bx r1\n"
        ".L_19b_003e6140_003e6160:\n"
        "nop \n"
        "bl engine_func_002acbd8\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003e84c4, 44)
extern "C" __attribute__((naked)) void func_003e84c4() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #4\n"
        "mov r1, sp\n"
        "add r0, r0, #4\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "beq .L_19b_003e84c4_003e84ec\n"
        "ldr r0, [sp]\n"
        "lsl r0, r0, #0x10\n"
        "lsr r0, r0, #0x18\n"
        ".L_19b_003e84c4_003e84ec:\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x003e8554, 44)
extern "C" __attribute__((naked)) void func_003e8554() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #4\n"
        "mov r1, sp\n"
        "add r0, r0, #4\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "beq .L_19b_003e8554_003e857c\n"
        "ldr r0, [sp]\n"
        "ands r0, r0, #0xff\n"
        "movne r0, #1\n"
        ".L_19b_003e8554_003e857c:\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x003e8598, 44)
extern "C" __attribute__((naked)) void func_003e8598() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r2, #4\n"
        "mov r1, sp\n"
        "add r0, r0, #4\n"
        "bl func_002a6d94\n"
        "cmp r0, #0\n"
        "beq .L_19b_003e8598_003e85c0\n"
        "ldr r0, [sp]\n"
        "lsl r0, r0, #8\n"
        "lsr r0, r0, #0x18\n"
        ".L_19b_003e8598_003e85c0:\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x003f9180, 44)
extern "C" __attribute__((naked)) void func_003f9180() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl func_003f8c24\n"
        "ldr r0, [r0]\n"
        "vldr s2, [r4, #8]\n"
        "lsr r0, r0, #0xc\n"
        "vmov s0, r0\n"
        "vcvt.f32.u32 s1, s0\n"
        "vldr s0, [r4, #0xc]\n"
        "vmla.f32 s0, s1, s2\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0010f480, 48)
extern "C" __attribute__((naked)) void func_0010f480() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl func_002bbd40\n"
        "add r0, r0, #4\n"
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

// DECOMP_FUNC(0x00121b50, 48)
extern "C" __attribute__((naked)) void engine_func_00121b50() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r0\n"
        "add r5, r0, #4\n"
        "mov r0, r5\n"
        "bl engine_func_002c3aa8\n"
        "add r0, r4, #0x10\n"
        "bl engine_func_00131308\n"
        "mov r4, r0\n"
        "mov r0, r5\n"
        "bl engine_func_002c3a24\n"
        "mov r0, r4\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x00122094, 48)
extern "C" __attribute__((naked)) void engine_func_00122094() {
    asm volatile(
        "push {r4, lr}\n"
        "sub sp, sp, #0x20\n"
        "mov r0, r1\n"
        "mov r4, #0\n"
        "mov r1, sp\n"
        "bl engine_func_001419bc\n"
        "cmp r0, #0\n"
        "ldrne r4, [sp, #0x10]\n"
        "add sp, sp, #0x20\n"
        "add r0, r4, r4, lsl #2\n"
        "lsl r0, r0, #0xd\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00138b38, 48)
extern "C" __attribute__((naked)) void engine_func_00138b38() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r5, r0\n"
        "ldr r4, [r0, #0xc]\n"
        "cmp r4, #0\n"
        "beq .L_19b_00138b38_00138b64\n"
        ".L_19b_00138b38_00138b4c:\n"
        "ldr r0, [r4, #8]\n"
        "mov r1, r5\n"
        "bl engine_func_001455ec\n"
        "ldr r4, [r4, #0x18]\n"
        "cmp r4, #0\n"
        "bne .L_19b_00138b38_00138b4c\n"
        ".L_19b_00138b38_00138b64:\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0014d2e4, 48)
extern "C" __attribute__((naked)) void engine_func_0014d2e4() {
    asm volatile(
        "ldr r0, [r0, #4]\n"
        "mov r0, r0\n"
        "push {r4, lr}\n"
        "ldr r0, [r0, #0x3c]\n"
        "mov r4, r2\n"
        "bl func_00151d94\n"
        "cmp r0, #0\n"
        "beq .L_19b_0014d2e4_0014d310\n"
        "ldr r0, [r0]\n"
        "str r0, [r4]\n"
        "mov r0, #1\n"
        ".L_19b_0014d2e4_0014d310:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0019da14, 48)
extern "C" __attribute__((naked)) void engine_func_0019da14() {
    asm volatile(
        "push {r3, r4, r5, lr}\n"
        "mov r3, #0x80\n"
        "mov r2, #1\n"
        "mov r1, sp\n"
        "bl engine_func_002c5e3c\n"
        "mov r5, r0\n"
        "bl effParts_func_0028c920\n"
        "mov r4, r0\n"
        "mov r0, r5\n"
        "bl engine_func_002c4360\n"
        "mov r0, r4\n"
        "pop {r3, r4, r5, pc}\n"
    );
}

// DECOMP_FUNC(0x001a0f1c, 48)
extern "C" __attribute__((naked)) void engine_func_001a0f1c() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl Npc2d_func_002fdfb8\n"
        "mov r4, r0\n"
        "bl engine_func_00289628\n"
        "mov r0, r4\n"
        "bl engine_func_0028949c\n"
        "mov r0, r4\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001c33f0, 48)
extern "C" __attribute__((naked)) void battle_func_001c33f0() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "bl battle_func_002bf41c\n"
        "cmp r0, #0\n"
        "beq .L_19b_001c33f0_001c3418\n"
        "mov r1, #0\n"
        "mov r0, r4\n"
        "bl battle_func_002c45b8\n"
        ".L_19b_001c33f0_001c3418:\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001dc618, 48)
extern "C" __attribute__((naked)) void engine_func_001dc618() {
    asm volatile(
        "mov r1, #0\n"
        "mov r0, #0x25\n"
        "push {r4, lr}\n"
        "bl AsdTMTexTable_func_002c5b04\n"
        "mov r4, #0\n"
        ".L_19b_001dc618_001dc62c:\n"
        "mov r1, r4\n"
        "mov r0, #0x25\n"
        "bl engine_func_002c5ab8\n"
        "add r4, r4, #1\n"
        "cmp r4, #4\n"
        "blt .L_19b_001dc618_001dc62c\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001dd008, 48)
extern "C" __attribute__((naked)) void engine_func_001dd008() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "mov r4, r0\n"
        "mov r0, #1\n"
        "bl engine_func_00296f60\n"
        "subs r1, r0, #0\n"
        "movlt r1, #0\n"
        "mov r0, r4\n"
        "bl script_vm_func_00262bcc\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001e4c4c, 48)
extern "C" __attribute__((naked)) void ui_func_001e4c4c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0ac8\n"
        "add r0, r0, #0x1000\n"
        "add r0, r0, #0xea0\n"
        "ldr r1, [r0]\n"
        "add r1, r1, #1\n"
        "cmp r1, #0x1e\n"
        "str r1, [r0]\n"
        "subge r1, r1, #0x1e\n"
        "strge r1, [r0]\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00219510, 48)
extern "C" __attribute__((naked)) void func_00219510() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r1\n"
        "ldrh r0, [r0]\n"
        "bl camp_func_002b4854\n"
        "mov r5, r0\n"
        "ldrh r0, [r4]\n"
        "bl camp_func_002b4854\n"
        "mov r1, r0\n"
        "ldrb r0, [r5, #0x6f]\n"
        "ldrb r1, [r1, #0x6f]\n"
        "sub r0, r0, r1\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x00219540, 48)
extern "C" __attribute__((naked)) void func_00219540() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r1\n"
        "ldrh r0, [r0]\n"
        "bl camp_func_002b4854\n"
        "mov r5, r0\n"
        "ldrh r0, [r4]\n"
        "bl camp_func_002b4854\n"
        "mov r1, r0\n"
        "ldrb r0, [r5, #0x6f]\n"
        "ldrb r1, [r1, #0x6f]\n"
        "sub r0, r0, r1\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x0022fc98, 48)
extern "C" __attribute__((naked)) void shop_func_0022fc98() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, #0\n"
        "mov r0, #6\n"
        "bl ui_func_0026f0d8\n"
        "cmp r0, #0\n"
        "movne r4, #1\n"
        "mov r0, #7\n"
        "bl ui_func_002b902c\n"
        "cmp r0, #0\n"
        "movne r4, #1\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0022fcc8, 48)
extern "C" __attribute__((naked)) void shop_func_0022fcc8() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, #0\n"
        "mov r0, #5\n"
        "bl ui_func_0026f0d8\n"
        "cmp r0, #0\n"
        "movne r4, #1\n"
        "mov r0, #8\n"
        "bl ui_func_002b902c\n"
        "cmp r0, #0\n"
        "movne r4, #1\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0024c48c, 48)
extern "C" __attribute__((naked)) void ui_func_0024c48c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, #0\n"
        "mov r0, #4\n"
        "bl ui_func_0026f0d8\n"
        "cmp r0, #0\n"
        "movne r4, #1\n"
        "mov r0, #0xa\n"
        "bl ui_func_002bffbc\n"
        "cmp r0, #0\n"
        "movne r4, #1\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00256750, 48)
extern "C" __attribute__((naked)) void shop_func_00256750() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, #0\n"
        "mov r0, #3\n"
        "bl ui_func_0026f0d8\n"
        "cmp r0, #0\n"
        "movne r4, #1\n"
        "mov r0, #9\n"
        "bl ui_func_002bffbc\n"
        "cmp r0, #0\n"
        "movne r4, #1\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0025ce3c, 48)
extern "C" __attribute__((naked)) void func_0025ce3c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r1\n"
        "bl camp_func_00298a74\n"
        "cmp r0, #0\n"
        "beq .L_19b_0025ce3c_0025ce64\n"
        "mov r0, r4\n"
        "bl camp_func_0028d5c4\n"
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        "beq .L_19b_0025ce3c_0025ce68\n"
        ".L_19b_0025ce3c_0025ce64:\n"
        "mov r0, #0\n"
        ".L_19b_0025ce3c_0025ce68:\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00263784, 48)
extern "C" __attribute__((naked)) void func_00263784() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl func_002bbd40\n"
        "add r0, r0, #8\n"
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

// DECOMP_FUNC(0x00269614, 48)
extern "C" __attribute__((naked)) void engine_func_00269614() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "str r1, [r0, #4]!\n"
        "str r2, [r0, #0x14]\n"
        "mov r0, #0\n"
        "str r3, [r4, #0xc]\n"
        "strb r0, [r4, #8]\n"
        "mov r0, r4\n"
        "bl AsdPrimRenderData_func_00346db0\n"
        "mov r0, #1\n"
        "strb r0, [r4]\n"
        "pop {r4, pc}\n"
    );
}
