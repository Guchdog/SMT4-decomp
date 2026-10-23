#include "types.h"

// Call targets are declared by ledger name so the ARM CALL relocations remain
// explicit and can be checked against their known code addresses.
extern "C" void func_0022c780();
extern "C" void engine_func_001182dc();
extern "C" void engine_func_00117504();
extern "C" void engine_func_00118848();
extern "C" void engine_func_00124714();
extern "C" void ui_func_002c0ac8();
extern "C" void script_vm_func_002bc210();
extern "C" void camp_func_002a8a08();
extern "C" void engine_func_002c2b1c();
extern "C" void script_vm_func_002b66ec();
extern "C" void engine_func_002b96f0();
extern "C" void script_vm_func_00252630();
extern "C" void ui_func_002d7f0c();
extern "C" void script_vm_func_002b8b70();
extern "C" void script_vm_func_00256364();
extern "C" void camp_func_0028c13c();
extern "C" void btlTalkBustUp_func_002959c4();
extern "C" void script_vm_func_002563d4();
extern "C" void ui_func_002df484();
extern "C" void engine_func_002fb1f8();
extern "C" void func_002bbd40();
extern "C" void engine_func_0036072c();
extern "C" void func_0036a7b8();

// DECOMP_FUNC(0x003b00a8, 12)
extern "C" __attribute__((naked)) void func_003b00a8() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_0022c780\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003b0164, 12)
extern "C" __attribute__((naked)) void func_003b0164() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_0022c780\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003b0388, 12)
extern "C" __attribute__((naked)) void func_003b0388() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_0022c780\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003b0564, 12)
extern "C" __attribute__((naked)) void func_003b0564() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_0022c780\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0010b7d4, 16)
extern "C" __attribute__((naked)) void func_0010b7d4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_001182dc\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0010b7e4, 16)
extern "C" __attribute__((naked)) void func_0010b7e4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_00117504\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0010d224, 16)
extern "C" __attribute__((naked)) void func_0010d224() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_00118848\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00118838, 16)
extern "C" __attribute__((naked)) void engine_func_00118838() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_00124714\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00126084, 16)
extern "C" __attribute__((naked)) void ui_func_00126084() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0ac8\n"
        "ldrsb r0, [r0, #0x8c]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001260a8, 16)
extern "C" __attribute__((naked)) void ui_func_001260a8() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0ac8\n"
        "ldr r0, [r0]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00126220, 16)
extern "C" __attribute__((naked)) void ui_func_00126220() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0ac8\n"
        "ldrsb r0, [r0, #0x94]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00126628, 16)
extern "C" __attribute__((naked)) void ui_func_00126628() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0ac8\n"
        "ldr r0, [r0, #0x38]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00126638, 16)
extern "C" __attribute__((naked)) void ui_func_00126638() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0ac8\n"
        "ldr r0, [r0, #0x3c]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001eb70c, 16)
extern "C" __attribute__((naked)) void ui_func_001eb70c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0ac8\n"
        "vldr s0, [r0, #0x3c]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x001ed510, 16)
extern "C" __attribute__((naked)) void func_001ed510() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002bc210\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0022ebbc, 16)
extern "C" __attribute__((naked)) void script_vm_func_0022ebbc() {
    asm volatile(
        "push {r4, lr}\n"
        "bl camp_func_002a8a08\n"
        "ldr r0, [r0]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0026fbc0, 16)
extern "C" __attribute__((naked)) void script_vm_func_0026fbc0() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_002c2b1c\n"
        "ldrsh r0, [r0, #0x20]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002857e4, 16)
extern "C" __attribute__((naked)) void script_vm_func_002857e4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_002c2b1c\n"
        "ldrb r0, [r0, #3]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0028d5b4, 16)
extern "C" __attribute__((naked)) void camp_func_0028d5b4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002b66ec\n"
        "ldrsh r0, [r0, #0x2a]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002b74b4, 16)
extern "C" __attribute__((naked)) void ui_func_002b74b4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0ac8\n"
        "ldr r0, [r0]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002b755c, 16)
extern "C" __attribute__((naked)) void ui_func_002b755c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002c0ac8\n"
        "ldr r0, [r0]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002bd3ec, 16)
extern "C" __attribute__((naked)) void script_vm_func_002bd3ec() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002b66ec\n"
        "add r0, r0, #0x4c\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002c1de4, 16)
extern "C" __attribute__((naked)) void script_vm_func_002c1de4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_002b96f0\n"
        "ldr r0, [r0, #8]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002f7684, 16)
extern "C" __attribute__((naked)) void func_002f7684() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_00252630\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002faf3c, 16)
extern "C" __attribute__((naked)) void script_vm_func_002faf3c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_002c2b1c\n"
        "ldr r0, [r0, #0x18]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x002fccd4, 16)
extern "C" __attribute__((naked)) void func_002fccd4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002d7f0c\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030a868, 16)
extern "C" __attribute__((naked)) void script_vm_func_0030a868() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002b8b70\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030a97c, 16)
extern "C" __attribute__((naked)) void script_vm_func_0030a97c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_00256364\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030b5d8, 16)
extern "C" __attribute__((naked)) void func_0030b5d8() {
    asm volatile(
        "push {r4, lr}\n"
        "bl camp_func_0028c13c\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0030b5e8, 16)
extern "C" __attribute__((naked)) void ui_func_0030b5e8() {
    asm volatile(
        "push {r4, lr}\n"
        "bl btlTalkBustUp_func_002959c4\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003112a4, 16)
extern "C" __attribute__((naked)) void script_vm_func_003112a4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002563d4\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0031ec8c, 16)
extern "C" __attribute__((naked)) void func_0031ec8c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl ui_func_002df484\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00322ce0, 16)
extern "C" __attribute__((naked)) void engine_func_00322ce0() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_002fb1f8\n"
        "mov r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003341e4, 16)
extern "C" __attribute__((naked)) void script_vm_func_003341e4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002b66ec\n"
        "ldrsh r0, [r0, #0x2c]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0033426c, 16)
extern "C" __attribute__((naked)) void script_vm_func_0033426c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002b66ec\n"
        "ldrsh r0, [r0, #0x1c]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x0033427c, 16)
extern "C" __attribute__((naked)) void script_vm_func_0033427c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl script_vm_func_002b66ec\n"
        "ldrsh r0, [r0, #0x1e]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00343c8c, 16)
extern "C" __attribute__((naked)) void func_00343c8c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_002bbd40\n"
        "ldrh r0, [r0, #0x1a]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00343c9c, 16)
extern "C" __attribute__((naked)) void func_00343c9c() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_002bbd40\n"
        "ldrh r0, [r0, #0x16]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00343cd4, 16)
extern "C" __attribute__((naked)) void func_00343cd4() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_002bbd40\n"
        "ldrh r0, [r0, #0x14]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00343e00, 16)
extern "C" __attribute__((naked)) void func_00343e00() {
    asm volatile(
        "push {r4, lr}\n"
        "bl func_002bbd40\n"
        "ldrh r0, [r0, #0x18]\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x00351d38, 16)
extern "C" __attribute__((naked)) void func_00351d38() {
    asm volatile(
        "push {r4, lr}\n"
        "bl engine_func_0036072c\n"
        "eor r0, r0, #1\n"
        "pop {r4, pc}\n"
    );
}

// DECOMP_FUNC(0x003e5214, 16)
extern "C" __attribute__((naked)) void func_003e5214() {
    asm volatile(
        "mov r0, r1\n"
        "push {r4, lr}\n"
        "bl func_0036a7b8\n"
        "pop {r4, pc}\n"
    );
}
