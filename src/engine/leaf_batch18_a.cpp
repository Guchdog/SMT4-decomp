#include "types.h"

// Call targets are declared by ledger name so the ARM CALL relocations remain
// explicit and can be checked against their known code addresses.
extern "C" void AsdCamera_func_00310124();
extern "C" void AsdFile_func_002b0434();
extern "C" void WhisperEffect_func_002f6734();
extern "C" void battle_func_0028df54();
extern "C" void battle_func_002931cc();
extern "C" void battle_func_002b087c();
extern "C" void battle_func_00336e20();
extern "C" void camp_func_0021e054();
extern "C" void camp_func_002347f4();
extern "C" void camp_func_0025c294();
extern "C" void camp_func_0028fde4();
extern "C" void camp_func_002a8a08();
extern "C" void camp_func_002a8a1c();
extern "C" void camp_func_002c85d4();
extern "C" void camp_func_002ed404();
extern "C" void engine_func_00263e60();
extern "C" void engine_func_00296f60();
extern "C" void engine_func_002adf14();
extern "C" void engine_func_002c2b1c();
extern "C" void engine_func_002c3290();
extern "C" void engine_func_002c4b30();
extern "C" void engine_func_002c583c();
extern "C" void engine_func_002c60ec();
extern "C" void engine_func_00348c20();
extern "C" void engine_func_00395024();
extern "C" void func_0011059c();
extern "C" void func_00128d08();
extern "C" void func_0014150c();
extern "C" void func_0014d26c();
extern "C" void func_0014d284();
extern "C" void func_0018bfd8();
extern "C" void func_0020fde0();
extern "C" void func_00223a18();
extern "C" void func_00236834();
extern "C" void func_00262664();
extern "C" void func_002892a0();
extern "C" void func_002a7094();
extern "C" void func_002b5b38();
extern "C" void func_002c3618();
extern "C" void func_002c3714();
extern "C" void func_003369f8();
extern "C" void func_00354e14();
extern "C" void func_00354e70();
extern "C" void func_003f6228();
extern "C" void script_vm_func_0024de30();
extern "C" void script_vm_func_002562e4();
extern "C" void script_vm_func_0026fca0();
extern "C" void script_vm_func_00273610();
extern "C" void script_vm_func_0027d67c();
extern "C" void script_vm_func_00285f14();
extern "C" void script_vm_func_00290694();
extern "C" void script_vm_func_00292e94();
extern "C" void script_vm_func_00295fcc();
extern "C" void script_vm_func_0029c178();
extern "C" void script_vm_func_002b66ec();
extern "C" void script_vm_func_002bf9e8();
extern "C" void script_vm_func_002c0ba8();
extern "C" void script_vm_func_002c5e2c();
extern "C" void script_vm_func_00334064();
extern "C" void script_vm_func_00381cf0();
extern "C" void ui_func_00138f44();
extern "C" void ui_func_00269cb8();
extern "C" void ui_func_00293c98();
extern "C" void ui_func_002c0ac8();

// DECOMP_FUNC(0x00128e50, 20)
extern "C" __attribute__((naked)) void func_00128e50() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_002b5b38\n"
        "pop {r4, lr}\n"
        "mov r0, r0\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x001dc7a0, 20)
extern "C" __attribute__((naked)) void battle_func_001dc7a0() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_0018bfd8\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001fa3f4, 20)
extern "C" __attribute__((naked)) void battle_func_001fa3f4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl camp_func_0025c294\n"
        "bl battle_func_002b087c\n"
        "ldrb r0, [r0, #2]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0022109c, 20)
extern "C" __attribute__((naked)) void script_vm_func_0022109c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_00292e94\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002e4298, 20)
extern "C" __attribute__((naked)) void ui_func_002e4298() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "bl battle_func_00336e20\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002fe8e4, 20)
extern "C" __attribute__((naked)) void func_002fe8e4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl camp_func_0021e054\n"
        "bl camp_func_002c85d4\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00311098, 20)
extern "C" __attribute__((naked)) void camp_func_00311098() {
    asm volatile(
        "push {r4, lr}\n"
        "bl camp_func_002a8a1c\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00311328, 20)
extern "C" __attribute__((naked)) void script_vm_func_00311328() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_00290694\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0031133c, 20)
extern "C" __attribute__((naked)) void battle_func_0031133c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_002c60ec\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001ab87c, 24)
extern "C" __attribute__((naked)) void engine_func_001ab87c() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl script_vm_func_00295fcc\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001eb410, 24)
extern "C" __attribute__((naked)) void func_001eb410() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_00354e70\n"
        "mov r4, r0\n"
        "bl func_002c3714\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001ed3b0, 24)
extern "C" __attribute__((naked)) void engine_func_001ed3b0() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl engine_func_00395024\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00201678, 24)
extern "C" __attribute__((naked)) void engine_func_00201678() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl script_vm_func_0027d67c\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002211fc, 24)
extern "C" __attribute__((naked)) void engine_func_002211fc() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl func_00223a18\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00222198, 24)
extern "C" __attribute__((naked)) void battle_func_00222198() {
    asm volatile(
        "mov r0, #4\n"
        "push {r4, lr}\n"
        "bl script_vm_func_0024de30\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00263e48, 24)
extern "C" __attribute__((naked)) void camp_func_00263e48() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002c5e2c\n"
        "mov r4, r0\n"
        "bl AsdCamera_func_00310124\n"
        "str r4, [r0, #0x14]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002d8854, 24)
extern "C" __attribute__((naked)) void battle_func_002d8854() {
    asm volatile(
        "mov r0, #5\n"
        "push {r4, lr}\n"
        "bl script_vm_func_0024de30\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002d8d90, 24)
extern "C" __attribute__((naked)) void engine_func_002d8d90() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl script_vm_func_00273610\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002dc004, 24)
extern "C" __attribute__((naked)) void script_vm_func_002dc004() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002b66ec\n"
        "ldrsh r0, [r0, #0x2a]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002dc01c, 24)
extern "C" __attribute__((naked)) void script_vm_func_002dc01c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002b66ec\n"
        "ldrb r0, [r0, #0x76]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002dc034, 24)
extern "C" __attribute__((naked)) void script_vm_func_002dc034() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002b66ec\n"
        "ldrsh r0, [r0, #0x2c]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002dc04c, 24)
extern "C" __attribute__((naked)) void engine_func_002dc04c() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl camp_func_002ed404\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002e28e8, 24)
extern "C" __attribute__((naked)) void battle_func_002e28e8() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_002892a0\n"
        "ldr r0, [r0, #0xfbc]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002e40e4, 24)
extern "C" __attribute__((naked)) void camp_func_002e40e4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl camp_func_002a8a08\n"
        "ldr r0, [r0]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002ee9b0, 24)
extern "C" __attribute__((naked)) void ui_func_002ee9b0() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl WhisperEffect_func_002f6734\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002ef274, 24)
extern "C" __attribute__((naked)) void engine_func_002ef274() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl script_vm_func_0026fca0\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002f7b9c, 24)
extern "C" __attribute__((naked)) void script_vm_func_002f7b9c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002b66ec\n"
        "bl func_00262664\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002f7bb4, 24)
extern "C" __attribute__((naked)) void script_vm_func_002f7bb4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002b66ec\n"
        "ldrsh r0, [r0, #0x1e]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030a98c, 24)
extern "C" __attribute__((naked)) void engine_func_0030a98c() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl script_vm_func_002562e4\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003125fc, 24)
extern "C" __attribute__((naked)) void ui_func_003125fc() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "bl func_003369f8\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0010541c, 28)
extern "C" __attribute__((naked)) void func_0010541c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, #0\n"
        "bl func_0011059c\n"
        "cmp r0, #0\n"
        "movne r4, #1\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0012f4d0, 28)
extern "C" __attribute__((naked)) void engine_func_0012f4d0() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "str r1, [r0, #4]\n"
        "mov r0, r1\n"
        "bl func_0014150c\n"
        "str r0, [r4, #0x108]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0013924c, 28)
extern "C" __attribute__((naked)) void func_0013924c() {
    asm volatile(
        "push {r3, lr}\n"
        "mov r0, #0\n"
        "str r0, [sp]\n"
        "mov r0, sp\n"
        "bl func_00128d08\n"
        "ldr r0, [sp]\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x00141924, 28)
extern "C" __attribute__((naked)) void engine_func_00141924() {
    asm volatile(
        "ldr r0, [r0, #4]\n"
        "mov r0, r0\n"
        "push {r4, lr}\n"
        "ldr r0, [r0, #0x3c]\n"
        "bl func_0014d26c\n"
        "ldr r0, [r0]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00141968, 28)
extern "C" __attribute__((naked)) void engine_func_00141968() {
    asm volatile(
        "ldr r0, [r0, #4]\n"
        "mov r0, r0\n"
        "push {r4, lr}\n"
        "ldr r0, [r0, #0x3c]\n"
        "bl func_0014d284\n"
        "ldr r0, [r0]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00155bbc, 28)
extern "C" __attribute__((naked)) void engine_func_00155bbc() {
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r4, r2\n"
        "mov r5, r3\n"
        "bl AsdFile_func_002b0434\n"
        "add r2, r0, #0x130\n"
        "stm r2, {r4, r5}\n"
        "pop {r4, r5, r6, pc}\n"
    );
}

// DECOMP_FUNC(0x00193b28, 28)
extern "C" __attribute__((naked)) void engine_func_00193b28() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_002c3290\n"
        "mov r4, r0\n"
        "mov r0, #0\n"
        "bl func_0020fde0\n"
        "mul r0, r4, r0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001ab860, 28)
extern "C" __attribute__((naked)) void engine_func_001ab860() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl script_vm_func_002bf9e8\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001eb3f4, 28)
extern "C" __attribute__((naked)) void func_001eb3f4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_002c3618\n"
        "bl func_00354e14\n"
        "mov r4, r0\n"
        "bl func_002c3714\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001f7208, 28)
extern "C" __attribute__((naked)) void func_001f7208() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl ui_func_00269cb8\n"
        "ldr r1, [r4, #0x2c]\n"
        "add r0, r0, r1\n"
        "str r0, [r4, #0x2c]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0020ea44, 28)
extern "C" __attribute__((naked)) void engine_func_0020ea44() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl script_vm_func_002c0ba8\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002143b0, 28)
extern "C" __attribute__((naked)) void engine_func_002143b0() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl engine_func_00348c20\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00221d08, 28)
extern "C" __attribute__((naked)) void script_vm_func_00221d08() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0ac8\n"
        "ldr r0, [r0, #0xc]\n"
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00255050, 28)
extern "C" __attribute__((naked)) void script_vm_func_00255050() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002c2b1c\n"
        "add r0, r0, r4\n"
        "add r0, r0, #0xe00\n"
        "ldrsb r0, [r0, #0x14]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0027ebe4, 28)
extern "C" __attribute__((naked)) void camp_func_0027ebe4() {
    asm volatile(
        "add r0, r0, #0x2e8\n"
        "push {r4, lr}\n"
        "bl camp_func_002347f4\n"
        "sub r0, r0, #0x34\n"
        "bl engine_func_00263e60\n"
        "sub r0, r0, #0x2b4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002904d0, 28)
extern "C" __attribute__((naked)) void script_vm_func_002904d0() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_002adf14\n"
        "add r0, r0, #0x800\n"
        "ldrh r0, [r0, #0x40]\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002c3b00, 28)
extern "C" __attribute__((naked)) void ui_func_002c3b00() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl ui_func_00138f44\n"
        "mov r0, #0\n"
        "str r0, [r4, #4]\n"
        "str r0, [r4, #8]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002cfbe0, 28)
extern "C" __attribute__((naked)) void battle_func_002cfbe0() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl battle_func_002931cc\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002dbfe8, 28)
extern "C" __attribute__((naked)) void engine_func_002dbfe8() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl camp_func_0028fde4\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002de95c, 28)
extern "C" __attribute__((naked)) void func_002de95c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl ui_func_00269cb8\n"
        "ldr r1, [r4, #0x2c]\n"
        "add r0, r0, r1\n"
        "str r0, [r4, #0x2c]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002e2900, 28)
extern "C" __attribute__((naked)) void engine_func_002e2900() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_002c583c\n"
        "mov r0, #0x64\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002e3e98, 28)
extern "C" __attribute__((naked)) void ui_func_002e3e98() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "add r0, r0, #0x1f00\n"
        "ldrsh r0, [r0, #0xc6]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002f5004, 28)
extern "C" __attribute__((naked)) void engine_func_002f5004() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "sxth r0, r0\n"
        "bl script_vm_func_00285f14\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002f5fe4, 28)
extern "C" __attribute__((naked)) void engine_func_002f5fe4() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "sxth r0, r0\n"
        "bl script_vm_func_00334064\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030051c, 28)
extern "C" __attribute__((naked)) void engine_func_0030051c() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "uxth r0, r0\n"
        "bl script_vm_func_0029c178\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030a960, 28)
extern "C" __attribute__((naked)) void engine_func_0030a960() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl engine_func_00296f60\n"
        "bl script_vm_func_00381cf0\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030b42c, 28)
extern "C" __attribute__((naked)) void ui_func_0030b42c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "add r0, r0, #0x1f00\n"
        "ldrsh r0, [r0, #0xca]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030b644, 28)
extern "C" __attribute__((naked)) void ui_func_0030b644() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "add r0, r0, #0x2200\n"
        "ldrsh r0, [r0, #0x5a]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0031256c, 28)
extern "C" __attribute__((naked)) void ui_func_0031256c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "add r0, r0, #0x4900\n"
        "ldrsh r0, [r0, #0x68]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00312588, 28)
extern "C" __attribute__((naked)) void ui_func_00312588() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00293c98\n"
        "add r0, r0, #0x4900\n"
        "ldrsh r0, [r0, #0x6a]\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00334110, 28)
extern "C" __attribute__((naked)) void script_vm_func_00334110() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002b66ec\n"
        "ldrh r1, [r0, #0x1c]\n"
        "ldrh r2, [r0, #0x1e]\n"
        "strh r1, [r0, #0x2a]\n"
        "strh r2, [r0, #0x2c]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0034f260, 28)
extern "C" __attribute__((naked)) void func_0034f260() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "ldr r0, [r0]\n"
        "bl func_003f6228\n"
        "mov r0, #0\n"
        "str r0, [r4]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00361350, 28)
extern "C" __attribute__((naked)) void engine_func_00361350() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "mov r1, #0xe30\n"
        "bl engine_func_002c4b30\n"
        "mov r0, #2\n"
        "strh r0, [r4]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00366a3c, 28)
extern "C" __attribute__((naked)) void func_00366a3c() {
    asm volatile(
        "push {r3, lr}\n"
        "ldr r0, [r0, #8]\n"
        "str r1, [sp]\n"
        "mov r1, sp\n"
        "add r0, r0, #8\n"
        "bl func_00236834\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x00367240, 28)
extern "C" __attribute__((naked)) void func_00367240() {
    asm volatile(
        "push {r3, lr}\n"
        "ldr r0, [r0, #8]\n"
        "str r1, [sp]\n"
        "mov r1, sp\n"
        "add r0, r0, #8\n"
        "bl func_00236834\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x00389910, 28)
extern "C" __attribute__((naked)) void func_00389910() {
    asm volatile(
        "mov r2, r1\n"
        "mov r1, #0xc\n"
        "push {r4, lr}\n"
        "bl func_002a7094\n"
        "cmp r0, #0\n"
        "ldrsbne r0, [r0, #0xd]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00389fd0, 28)
extern "C" __attribute__((naked)) void func_00389fd0() {
    asm volatile(
        "mov r2, r1\n"
        "mov r1, #0x10\n"
        "push {r4, lr}\n"
        "bl func_002a7094\n"
        "cmp r0, #0\n"
        "ldrsbne r0, [r0, #0xd]\n"
        "pop {r4, pc}\n"
    );
}
