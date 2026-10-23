#include "types.h"

extern "C" void func_0036a54c();
extern "C" void func_0011d1c0();
extern "C" void script_vm_func_002b6700();
extern "C" void func_00128bfc();
extern "C" void ui_func_002c0ac8();
extern "C" void func_001483f4();
extern "C" void func_001476d8();
extern "C" void func_00155c48();
extern "C" void script_vm_func_0029c650();
extern "C" void ui_func_00254ff0();
extern "C" void camp_func_002c0144();
extern "C" void func_0023a24c();
extern "C" void ui_func_002c0b94();
extern "C" void AsdListBox_func_00263408();
extern "C" void script_vm_func_002912f4();
extern "C" void engine_func_002c2b1c();
extern "C" void engine_func_002adf14();
extern "C" void camp_func_002544e4();
extern "C" void camp_func_002b492c();
extern "C" void script_vm_func_0029117c();
extern "C" void battle_func_0028df54();
extern "C" void ui_func_00126920();
extern "C" void func_00307964();
extern "C" void camp_func_002b9364();
extern "C" void camp_func_0033d164();
extern "C" void func_002bbd40();
extern "C" void engine_func_00357c48();
extern "C" void func_0035a784();
extern "C" void func_0035ab1c();
extern "C" void engine_func_002bdbcc();
extern "C" void func_0037b9d4();

// DECOMP_FUNC(0x003e5fa4, 16)
extern "C" __attribute__((naked)) void func_003e5fa4() {
    asm volatile(
        "mov r0, r1\n"
        "push {r4, lr}\n"
        "bl func_0036a54c\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00110044, 20)
extern "C" __attribute__((naked)) void func_00110044() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_0011d1c0\n"
        "cmp r0, #1\n"
        "movne r0, #0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0011b374, 20)
extern "C" __attribute__((naked)) void script_vm_func_0011b374() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002b6700\n"
        "cmp r0, #0\n"
        "addne r0, r0, #0xb8\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0011c5cc, 20)
extern "C" __attribute__((naked)) void func_0011c5cc() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl func_00128bfc\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00126094, 20)
extern "C" __attribute__((naked)) void ui_func_00126094() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r1\n"
        "bl ui_func_002c0ac8\n"
        "strb r4, [r0, #0x8c]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00126330, 20)
extern "C" __attribute__((naked)) void ui_func_00126330() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r1\n"
        "bl ui_func_002c0ac8\n"
        "strb r4, [r0, #0x94]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0013c0f0, 20)
extern "C" __attribute__((naked)) void func_0013c0f0() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl func_001483f4\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00142928, 20)
extern "C" __attribute__((naked)) void battle_func_00142928() {
    asm volatile(
        "push {r3, lr}\n"
        "mov ip, #1\n"
        "str ip, [sp]\n"
        "bl func_001476d8\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x00153990, 20)
extern "C" __attribute__((naked)) void func_00153990() {
    asm volatile(
        "push {r3, lr}\n"
        "mov ip, #3\n"
        "str ip, [sp]\n"
        "bl func_00155c48\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x001c34cc, 20)
extern "C" __attribute__((naked)) void script_vm_func_001c34cc() {
    asm volatile(
        "mov r0, #0xf\n"
        "push {r4, lr}\n"
        "bl script_vm_func_0029c650\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0022a4d8, 20)
extern "C" __attribute__((naked)) void battle_func_0022a4d8() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00254ff0\n"
        "cmp r0, #0\n"
        "addne r0, r0, #0x20c\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0022a5f8, 20)
extern "C" __attribute__((naked)) void battle_func_0022a5f8() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00254ff0\n"
        "cmp r0, #0\n"
        "addne r0, r0, #0x208\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002315b4, 20)
extern "C" __attribute__((naked)) void func_002315b4() {
    asm volatile(
        "push {r3, lr}\n"
        "mov ip, #1\n"
        "str ip, [sp]\n"
        "bl camp_func_002c0144\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x0023a390, 20)
extern "C" __attribute__((naked)) void func_0023a390() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_0023a24c\n"
        "lsrs r1, r0, #0x1f\n"
        "moveq r0, #0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0024bd4c, 20)
extern "C" __attribute__((naked)) void script_vm_func_0024bd4c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0b94\n"
        "add r0, r0, #0x1f800\n"
        "add r0, r0, #0x72\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0025c7c4, 20)
extern "C" __attribute__((naked)) void battle_func_0025c7c4() {
    asm volatile(
        "push {r3, lr}\n"
        "mov ip, #0\n"
        "str ip, [sp]\n"
        "bl AsdListBox_func_00263408\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x00263720, 20)
extern "C" __attribute__((naked)) void engine_func_00263720() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl script_vm_func_002912f4\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0026e8fc, 20)
extern "C" __attribute__((naked)) void engine_func_0026e8fc() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r1\n"
        "bl ui_func_002c0ac8\n"
        "strb r4, [r0, #0x31]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0026fca0, 20)
extern "C" __attribute__((naked)) void script_vm_func_0026fca0() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002c2b1c\n"
        "str r4, [r0, #0x18]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0027d81c, 20)
extern "C" __attribute__((naked)) void script_vm_func_0027d81c() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002c2b1c\n"
        "strb r4, [r0, #3]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0027db24, 20)
extern "C" __attribute__((naked)) void script_vm_func_0027db24() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002c2b1c\n"
        "strh r4, [r0, #0x20]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00287afc, 20)
extern "C" __attribute__((naked)) void script_vm_func_00287afc() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002b6700\n"
        "cmp r0, #0\n"
        "ldrbne r0, [r0, #6]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002897fc, 20)
extern "C" __attribute__((naked)) void script_vm_func_002897fc() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0b94\n"
        "add r0, r0, #0x24800\n"
        "add r0, r0, #0x384\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00290694, 20)
extern "C" __attribute__((naked)) void script_vm_func_00290694() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_002adf14\n"
        "add r0, r0, #0x800\n"
        "ldrh r0, [r0, #0x40]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00290a38, 20)
extern "C" __attribute__((naked)) void camp_func_00290a38() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl camp_func_002544e4\n"
        "ldr r0, [r0, r4, lsl #2]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002ae650, 20)
extern "C" __attribute__((naked)) void shop_func_002ae650() {
    asm volatile(
        "push {r4, lr}\n"
        "bl camp_func_002b492c\n"
        "cmp r0, #0\n"
        "ldrbne r0, [r0, #8]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002b74a0, 20)
extern "C" __attribute__((naked)) void ui_func_002b74a0() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r1\n"
        "bl ui_func_002c0ac8\n"
        "strb r4, [r0, #0x31]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002d8590, 20)
extern "C" __attribute__((naked)) void ui_func_002d8590() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r1\n"
        "bl ui_func_002c0ac8\n"
        "strb r4, [r0, #0x16]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002ef21c, 20)
extern "C" __attribute__((naked)) void script_vm_func_002ef21c() {
    asm volatile(
        "mov r0, #0x1e\n"
        "push {r4, lr}\n"
        "bl script_vm_func_0029117c\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002fdfa4, 20)
extern "C" __attribute__((naked)) void script_vm_func_002fdfa4() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r1\n"
        "bl ui_func_002c0ac8\n"
        "str r4, [r0, #0x38]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00317f20, 20)
extern "C" __attribute__((naked)) void battle_func_00317f20() {
    asm volatile(
        "mov r0, #0\n"
        "push {r4, lr}\n"
        "bl battle_func_0028df54\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0031c198, 20)
extern "C" __attribute__((naked)) void func_0031c198() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_00126920\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0031ec9c, 20)
extern "C" __attribute__((naked)) void func_0031ec9c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_00307964\n"
        "cmp r0, #0\n"
        "movne r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0033c2f4, 20)
extern "C" __attribute__((naked)) void script_vm_func_0033c2f4() {
    asm volatile(
        "push {r4, lr}\n"
        "ldrh r0, [r0, #0x46]\n"
        "bl camp_func_002b9364\n"
        "ldrh r0, [r0, #0x2a]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0033d618, 20)
extern "C" __attribute__((naked)) void battle_func_0033d618() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl camp_func_0033d164\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00343d80, 20)
extern "C" __attribute__((naked)) void engine_func_00343d80() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_002bbd40\n"
        "mov r1, #1\n"
        "strb r1, [r0, #0x10]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00357c34, 20)
extern "C" __attribute__((naked)) void func_00357c34() {
    asm volatile(
        "push {r3, lr}\n"
        "mov ip, #1\n"
        "str ip, [sp]\n"
        "bl engine_func_00357c48\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x0035a614, 20)
extern "C" __attribute__((naked)) void func_0035a614() {
    asm volatile(
        "push {r3, lr}\n"
        "mov ip, #0\n"
        "str ip, [sp]\n"
        "bl func_0035a784\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x0035a628, 20)
extern "C" __attribute__((naked)) void engine_func_0035a628() {
    asm volatile(
        "push {r3, lr}\n"
        "mov ip, #0\n"
        "str ip, [sp]\n"
        "bl func_0035ab1c\n"
        "pop {r3, pc}\n"
    );
}

// DECOMP_FUNC(0x00376b84, 20)
extern "C" __attribute__((naked)) void func_00376b84() {
    asm volatile(
        "push {r4, lr}\n"
        "mov r4, r0\n"
        "bl engine_func_002bdbcc\n"
        "mov r0, r4\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00377624, 20)
extern "C" __attribute__((naked)) void func_00377624() {
    asm volatile(
        "add r0, r0, #0xc\n"
        "push {r4, lr}\n"
        "bl func_0037b9d4\n"
        "sub r0, r0, #0xc\n"
        "pop {r4, pc}\n"
    );
}
