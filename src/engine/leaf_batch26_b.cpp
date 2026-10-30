#include "types.h"

// Batch 26 B: complete ARM instruction coverage, explicit returns, and bounded literal tails.

// DECOMP_FUNC(0x002bb09c, 24)
extern "C" __attribute__((naked)) void engine_func_002bb09c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f100c\n"
        ".inst 0xe5801000\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5801004\n"
        ".inst 0xe12fff1e\n"
        ".word 0xe7e3ffff\n"
    );
}

// DECOMP_FUNC(0x002f80c8, 28)
extern "C" __attribute__((naked)) void ui_func_002f80c8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe6ef1\n"
        ".inst 0xe59f1008\n"
        ".inst 0xebfd3b60\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0100003a\n"
    );
}

// DECOMP_FUNC(0x002c584c, 32)
extern "C" __attribute__((naked)) void func_002c584c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500c02\n"
        ".inst 0xaa000003\n"
        ".inst 0xe59f200c\n"
        ".inst 0xe3510000\n"
        ".inst 0x13a01001\n"
        ".inst 0xe7c21000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004e3d0c\n"
    );
}

// DECOMP_FUNC(0x0024bd00, 36)
extern "C" __attribute__((naked)) void func_0024bd00() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe5901000\n"
        ".inst 0xe59f200c\n"
        ".inst 0xe1510002\n"
        ".inst 0x05900004\n"
        ".inst 0x13a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x4e494246\n"
    );
}

// DECOMP_FUNC(0x00263140, 36)
extern "C" __attribute__((naked)) void camp_func_00263140() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0018\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x15d00042\n"
        ".inst 0x13500000\n"
        ".inst 0x13a00001\n"
        ".inst 0x0affffff\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043dcf0\n"
    );
}

// DECOMP_FUNC(0x00282f00, 36)
extern "C" __attribute__((naked)) void ui_func_00282f00() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0018\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe2800b01\n"
        ".inst 0xe2800f42\n"
        ".inst 0xec800a03\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0044e178\n"
    );
}

// DECOMP_FUNC(0x0028796c, 36)
extern "C" __attribute__((naked)) void engine_func_0028796c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000\n"
        ".inst 0x059f0010\n"
        ".inst 0x0a000002\n"
        ".inst 0xe3500001\n"
        ".inst 0x059f0008\n"
        ".inst 0x13a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004c4404\n"
        ".word 0x004c45a4\n"
    );
}

// DECOMP_FUNC(0x002d81ac, 36)
extern "C" __attribute__((naked)) void engine_func_002d81ac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0018\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x15d0006c\n"
        ".inst 0x13500000\n"
        ".inst 0x13a00001\n"
        ".inst 0x0affffff\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00433a58\n"
    );
}

// DECOMP_FUNC(0x0021edec, 40)
extern "C" __attribute__((naked)) void engine_func_0021edec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f4018\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000002\n"
        ".inst 0xeb029556\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00447600\n"
    );
}

// DECOMP_FUNC(0x0023ebc8, 40)
extern "C" __attribute__((naked)) void script_vm_func_0023ebc8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500043\n"
        ".inst 0x23a00000\n"
        ".inst 0x2a000004\n"
        ".inst 0xe59f1010\n"
        ".inst 0xe0810200\n"
        ".inst 0xe5900004\n"
        ".inst 0xe3500000\n"
        ".inst 0x13a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0049382c\n"
    );
}

// DECOMP_FUNC(0x00246874, 40)
extern "C" __attribute__((naked)) void engine_func_00246874() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe5900304\n"
        ".inst 0xe3500004\n"
        ".inst 0x03a00001\n"
        ".inst 0x0a000002\n"
        ".inst 0xe3500005\n"
        ".inst 0x13a00000\n"
        ".inst 0x03e00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0047e200\n"
    );
}

// DECOMP_FUNC(0x002546c4, 40)
extern "C" __attribute__((naked)) void script_vm_func_002546c4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe5901000\n"
        ".inst 0xe59f2010\n"
        ".inst 0xe1510002\n"
        ".inst 0x05900008\n"
        ".inst 0x0a000000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x52434254\n"
    );
}

// DECOMP_FUNC(0x0026a004, 40)
extern "C" __attribute__((naked)) void camp_func_0026a004() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f101c\n"
        ".inst 0xe5911000\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe5c10420\n"
        ".inst 0xe5812400\n"
        ".inst 0xe58123fc\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043dd68\n"
    );
}

// DECOMP_FUNC(0x0028c880, 40)
extern "C" __attribute__((naked)) void engine_func_0028c880() {
    asm volatile(
        ".arm\n"
        ".inst 0xeddf1a07\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe590002c\n"
        ".inst 0xee211a21\n"
        ".inst 0xee600aa1\n"
        ".inst 0xee200a21\n"
        ".inst 0xe280004c\n"
        ".inst 0xebfefe4a\n"
        ".inst 0xe8bd8010\n"
        ".word 0x3c8efa35\n"
    );
}

// DECOMP_FUNC(0x0028df70, 40)
extern "C" __attribute__((naked)) void camp_func_0028df70() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500006\n"
        ".inst 0x23a00000\n"
        ".inst 0x2a000004\n"
        ".inst 0xe59f1010\n"
        ".inst 0xe5911004\n"
        ".inst 0xe0810100\n"
        ".inst 0xe2800b01\n"
        ".inst 0xe1d009b6\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043da28\n"
    );
}

// DECOMP_FUNC(0x00291154, 40)
extern "C" __attribute__((naked)) void script_vm_func_00291154() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe5900008\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe5d00008\n"
        ".inst 0xe3500001\n"
        ".inst 0x0a000000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x00293d04, 40)
extern "C" __attribute__((naked)) void ui_func_00293d04() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe590001c\n"
        ".inst 0xe3500003\n"
        ".inst 0x03a00001\n"
        ".inst 0x13a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043dcf0\n"
    );
}

// DECOMP_FUNC(0x0029e2cc, 40)
extern "C" __attribute__((naked)) void camp_func_0029e2cc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe5900004\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe2800a01\n"
        ".inst 0xe59002e4\n"
        ".inst 0xe3500000\n"
        ".inst 0x13a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x0029f0cc, 40)
extern "C" __attribute__((naked)) void camp_func_0029f0cc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe5900004\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe5d00008\n"
        ".inst 0xe3500001\n"
        ".inst 0x0a000000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002ae474, 40)
extern "C" __attribute__((naked)) void func_002ae474() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f101c\n"
        ".inst 0xe3500000\n"
        ".inst 0x13500001\n"
        ".inst 0x059100b8\n"
        ".inst 0x0a000002\n"
        ".inst 0xe3500002\n"
        ".inst 0x05910130\n"
        ".inst 0x13a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004e39e0\n"
    );
}

// DECOMP_FUNC(0x002ae49c, 40)
extern "C" __attribute__((naked)) void func_002ae49c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f101c\n"
        ".inst 0xe3500000\n"
        ".inst 0x13500001\n"
        ".inst 0x059100bc\n"
        ".inst 0x0a000002\n"
        ".inst 0xe3500002\n"
        ".inst 0x05910134\n"
        ".inst 0x13a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004e39e0\n"
    );
}

// DECOMP_FUNC(0x002b7354, 40)
extern "C" __attribute__((naked)) void func_002b7354() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f4018\n"
        ".inst 0xe5940004\n"
        ".inst 0xe1a00100\n"
        ".inst 0xebffe0b1\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840000\n"
        ".inst 0xe5840004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x004729e0\n"
    );
}

// DECOMP_FUNC(0x002b737c, 40)
extern "C" __attribute__((naked)) void func_002b737c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4008\n"
        ".inst 0xe1a0100d\n"
        ".inst 0xe3a00f82\n"
        ".inst 0xeb001592\n"
        ".inst 0xe59f000c\n"
        ".inst 0xe59d1000\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe8800006\n"
        ".inst 0xe8bd8008\n"
        ".word 0x004729e0\n"
    );
}

// DECOMP_FUNC(0x002b89d4, 40)
extern "C" __attribute__((naked)) void script_vm_func_002b89d4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5900018\n"
        ".inst 0xe3500036\n"
        ".inst 0x03a00000\n"
        ".inst 0x13a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043da90\n"
    );
}

// DECOMP_FUNC(0x002baaa4, 40)
extern "C" __attribute__((naked)) void func_002baaa4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebf9df79\n"
        ".inst 0xe59f1014\n"
        ".inst 0xe5911004\n"
        ".inst 0xe2811088\n"
        ".inst 0xe0810100\n"
        ".inst 0xe2800b7b\n"
        ".inst 0xe2800054\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002c00e8, 40)
extern "C" __attribute__((naked)) void func_002c00e8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f101c\n"
        ".inst 0xe3500000\n"
        ".inst 0x13500001\n"
        ".inst 0x01d100d0\n"
        ".inst 0x0a000002\n"
        ".inst 0xe3500002\n"
        ".inst 0x01d100d1\n"
        ".inst 0x13a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004e3be0\n"
    );
}

// DECOMP_FUNC(0x002c1784, 40)
extern "C" __attribute__((naked)) void engine_func_002c1784() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f101c\n"
        ".inst 0xe3500000\n"
        ".inst 0x13500001\n"
        ".inst 0x0591001c\n"
        ".inst 0x0a000002\n"
        ".inst 0xe3500002\n"
        ".inst 0x05910074\n"
        ".inst 0x13a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004e39e0\n"
    );
}

// DECOMP_FUNC(0x002c17ac, 40)
extern "C" __attribute__((naked)) void engine_func_002c17ac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f101c\n"
        ".inst 0xe3500000\n"
        ".inst 0x13500001\n"
        ".inst 0x05910018\n"
        ".inst 0x0a000002\n"
        ".inst 0xe3500002\n"
        ".inst 0x05910070\n"
        ".inst 0x13a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004e39e0\n"
    );
}

// DECOMP_FUNC(0x002cd934, 40)
extern "C" __attribute__((naked)) void engine_func_002cd934() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe5901000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe5911008\n"
        ".inst 0xe3510002\n"
        ".inst 0x03a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043dee8\n"
    );
}

// DECOMP_FUNC(0x002cdc9c, 40)
extern "C" __attribute__((naked)) void func_002cdc9c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5900004\n"
        ".inst 0xe3500002\n"
        ".inst 0x03a00000\n"
        ".inst 0x13a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0044d1b0\n"
    );
}

// DECOMP_FUNC(0x002d8568, 40)
extern "C" __attribute__((naked)) void engine_func_002d8568() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe59f0014\n"
        ".inst 0xe1a01005\n"
        ".inst 0xe5904000\n"
        ".inst 0xe5940000\n"
        ".inst 0xebffafb6\n"
        ".inst 0xe5845030\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0043ded0\n"
    );
}

// DECOMP_FUNC(0x002d874c, 40)
extern "C" __attribute__((naked)) void battle_func_002d874c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfd241f\n"
        ".inst 0xe59f1010\n"
        ".inst 0xe5810004\n"
        ".inst 0xebfdc5f3\n"
        ".inst 0xebfdd5e5\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043e088\n"
    );
}

// DECOMP_FUNC(0x002dbe8c, 40)
extern "C" __attribute__((naked)) void script_vm_func_002dbe8c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfe8b3e\n"
        ".inst 0xe5900028\n"
        ".inst 0xe1d00ef8\n"
        ".inst 0xebfec82a\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002f5ea0, 40)
extern "C" __attribute__((naked)) void func_002f5ea0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f4018\n"
        ".inst 0xe5940048\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000002\n"
        ".inst 0xebfd692b\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840048\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0044ea80\n"
    );
}

// DECOMP_FUNC(0x002fea08, 40)
extern "C" __attribute__((naked)) void engine_func_002fea08() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f4018\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe5840050\n"
        ".inst 0xe3a00000\n"
        ".inst 0xebfe614f\n"
        ".inst 0xe5840074\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0049f91c\n"
    );
}

// DECOMP_FUNC(0x0020cea8, 44)
extern "C" __attribute__((naked)) void script_vm_func_0020cea8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0020\n"
        ".inst 0xe5900000\n"
        ".inst 0xe5901004\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe2800004\n"
        ".inst 0xe3a01009\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe8800006\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00447600\n"
    );
}

// DECOMP_FUNC(0x00213af8, 44)
extern "C" __attribute__((naked)) void camp_func_00213af8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0020\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe590001c\n"
        ".inst 0xe3500015\n"
        ".inst 0x03a00000\n"
        ".inst 0x0a000000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043dcf0\n"
    );
}

// DECOMP_FUNC(0x0021f410, 44)
extern "C" __attribute__((naked)) void engine_func_0021f410() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f101c\n"
        ".inst 0xe3a02004\n"
        ".inst 0xe3a0000d\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb029964\n"
        ".inst 0xe59f100c\n"
        ".inst 0xe3e00000\n"
        ".inst 0xe5810004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00432ce4\n"
        ".word 0x00432ce0\n"
    );
}

// DECOMP_FUNC(0x002228c0, 44)
extern "C" __attribute__((naked)) void engine_func_002228c0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb01d1a4\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xeb028bd8\n"
        ".inst 0xe59f0008\n"
        ".inst 0xe5804000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0044cfb8\n"
    );
}

// DECOMP_FUNC(0x00222a38, 44)
extern "C" __attribute__((naked)) void camp_func_00222a38() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0020\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe590001c\n"
        ".inst 0xe350000f\n"
        ".inst 0x03a00000\n"
        ".inst 0x0a000000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043dcf0\n"
    );
}

// DECOMP_FUNC(0x00224d48, 44)
extern "C" __attribute__((naked)) void engine_func_00224d48() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb01c882\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe3a0100d\n"
        ".inst 0xe5900000\n"
        ".inst 0xeb009eaf\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x0023c71c, 44)
extern "C" __attribute__((naked)) void battle_func_0023c71c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a03001\n"
        ".inst 0xe6bf1070\n"
        ".inst 0xe59f0018\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe5900000\n"
        ".inst 0xebffa8fc\n"
        ".inst 0xe3a0102e\n"
        ".inst 0xe5c01004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00434290\n"
    );
}

// DECOMP_FUNC(0x00248418, 44)
extern "C" __attribute__((naked)) void camp_func_00248418() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00023\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb01e2a6\n"
        ".inst 0xeb01e287\n"
        ".inst 0xe59f100c\n"
        ".inst 0xe5911000\n"
        ".inst 0xe59113e4\n"
        ".inst 0xe0800001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x0024abd0, 44)
extern "C" __attribute__((naked)) void func_0024abd0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0020\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3e02000\n"
        ".inst 0xe1c013bc\n"
        ".inst 0xe1c024b0\n"
        ".inst 0xe1c013be\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043dcf0\n"
    );
}

// DECOMP_FUNC(0x0024c538, 44)
extern "C" __attribute__((naked)) void script_vm_func_0024c538() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00023\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb01d25e\n"
        ".inst 0xeb01d23f\n"
        ".inst 0xe59f100c\n"
        ".inst 0xe5911000\n"
        ".inst 0xe59113ec\n"
        ".inst 0xe0800001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x002546ec, 44)
extern "C" __attribute__((naked)) void func_002546ec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000006\n"
        ".inst 0xec800a02\n"
        ".inst 0xe2622000\n"
        ".inst 0xed9f1a04\n"
        ".inst 0xe1c011b0\n"
        ".inst 0xe1c021b2\n"
        ".inst 0xed801a02\n"
        ".inst 0xed801a03\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000\n"
    );
}

// DECOMP_FUNC(0x00256ad8, 44)
extern "C" __attribute__((naked)) void battle_func_00256ad8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a03001\n"
        ".inst 0xe6bf1070\n"
        ".inst 0xe59f0018\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe5900000\n"
        ".inst 0xebff400d\n"
        ".inst 0xe3a01019\n"
        ".inst 0xe5c01004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00434290\n"
    );
}

// DECOMP_FUNC(0x002c8604, 44)
extern "C" __attribute__((naked)) void func_002c8604() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1020\n"
        ".inst 0xe5911000\n"
        ".inst 0xe59120cc\n"
        ".inst 0xe1520000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe28130cc\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe8830005\n"
        ".inst 0xe58120d4\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00447060\n"
    );
}

// DECOMP_FUNC(0x002cfb54, 44)
extern "C" __attribute__((naked)) void engine_func_002cfb54() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebff1cff\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe3a01007\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfdf32c\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002dbeb4, 44)
extern "C" __attribute__((naked)) void engine_func_002dbeb4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfeec27\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe3a01007\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfdc254\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002dbf28, 44)
extern "C" __attribute__((naked)) void engine_func_002dbf28() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfeec0a\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe3a0101b\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfdc237\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002dbf54, 44)
extern "C" __attribute__((naked)) void engine_func_002dbf54() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfeebff\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe3a01014\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfdc22c\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002e1558, 44)
extern "C" __attribute__((naked)) void func_002e1558() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1020\n"
        ".inst 0xe5912000\n"
        ".inst 0xe3e01000\n"
        ".inst 0xe3520000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe3500004\n"
        ".inst 0x30820100\n"
        ".inst 0x35901630\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043dfc0\n"
    );
}

// DECOMP_FUNC(0x002e3a90, 44)
extern "C" __attribute__((naked)) void script_vm_func_002e3a90() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0020\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfe6c3d\n"
        ".inst 0xe5900028\n"
        ".inst 0xe3a01006\n"
        ".inst 0xe2800c01\n"
        ".inst 0xe1c014bc\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002e3fb0, 44)
extern "C" __attribute__((naked)) void engine_func_002e3fb0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfecbe8\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe3a01013\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfda215\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002e3fdc, 44)
extern "C" __attribute__((naked)) void engine_func_002e3fdc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfecbdd\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe3a0100e\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfda20a\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002e426c, 44)
extern "C" __attribute__((naked)) void script_vm_func_002e426c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfecb39\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe5900000\n"
        ".inst 0xeb0371d2\n"
        ".inst 0xe3500000\n"
        ".inst 0x13a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00439b58\n"
    );
}

// DECOMP_FUNC(0x002f1058, 44)
extern "C" __attribute__((naked)) void engine_func_002f1058() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe97be\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe3a01011\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfd6deb\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002f1084, 44)
extern "C" __attribute__((naked)) void engine_func_002f1084() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe97b3\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe3a01012\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfd6de0\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002f10b0, 44)
extern "C" __attribute__((naked)) void engine_func_002f10b0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe97a8\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe3a01008\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfd6dd5\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002f25a4, 44)
extern "C" __attribute__((naked)) void ui_func_002f25a4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0020\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe59012f8\n"
        ".inst 0xe3510000\n"
        ".inst 0xa5900308\n"
        ".inst 0xb3a00000\n"
        ".inst 0xa6ff0070\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00434210\n"
    );
}

// DECOMP_FUNC(0x002f64f8, 44)
extern "C" __attribute__((naked)) void camp_func_002f64f8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0020\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe2800c06\n"
        ".inst 0xe1d00bfc\n"
        ".inst 0xe3500000\n"
        ".inst 0xd3a00000\n"
        ".inst 0xc3a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043dcf0\n"
    );
}

// DECOMP_FUNC(0x002f760c, 44)
extern "C" __attribute__((naked)) void engine_func_002f760c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe7e51\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe3a01008\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfd547e\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002f7638, 44)
extern "C" __attribute__((naked)) void engine_func_002f7638() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe7e46\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe3a01018\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfd5473\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002ffe70, 44)
extern "C" __attribute__((naked)) void engine_func_002ffe70() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe5c38\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe3a01017\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfd3265\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002034ac, 48)
extern "C" __attribute__((naked)) void camp_func_002034ac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0024\n"
        ".inst 0xe5900000\n"
        ".inst 0xe5900004\n"
        ".inst 0xe3500011\n"
        ".inst 0x13500012\n"
        ".inst 0x0a000002\n"
        ".inst 0xe3500013\n"
        ".inst 0x13a00001\n"
        ".inst 0x1a000000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043dd50\n"
    );
}

// DECOMP_FUNC(0x0020d660, 48)
extern "C" __attribute__((naked)) void engine_func_0020d660() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0024\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5900000\n"
        ".inst 0xe2804903\n"
        ".inst 0xe2844ec1\n"
        ".inst 0xe594001c\n"
        ".inst 0xeb026908\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe584001c\n"
        ".inst 0xe5c40000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00447a78\n"
    );
}

// DECOMP_FUNC(0x00223cac, 48)
extern "C" __attribute__((naked)) void camp_func_00223cac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0024\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5904000\n"
        ".inst 0xe3540000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe5940000\n"
        ".inst 0xeb01dd30\n"
        ".inst 0xe2844b25\n"
        ".inst 0xe2844064\n"
        ".inst 0xe5840000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043dd68\n"
    );
}

// DECOMP_FUNC(0x00241b44, 48)
extern "C" __attribute__((naked)) void camp_func_00241b44() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb01d4c4\n"
        ".inst 0xe1d004b6\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe5900000\n"
        ".inst 0xe5900008\n"
        ".inst 0xe3500000\n"
        ".inst 0x13a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043e110\n"
    );
}

// DECOMP_FUNC(0x00245bb8, 48)
extern "C" __attribute__((naked)) void func_00245bb8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0020\n"
        ".inst 0xe590116c\n"
        ".inst 0xe1510000\n"
        ".inst 0x03a00000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe1510000\n"
        ".inst 0x03a00001\n"
        ".inst 0x13a00002\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004e39e0\n"
        ".word 0x004e3a0c\n"
    );
}

// DECOMP_FUNC(0x00248238, 48)
extern "C" __attribute__((naked)) void engine_func_00248238() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0024\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5900000\n"
        ".inst 0xe2804903\n"
        ".inst 0xe2844ec3\n"
        ".inst 0xe594001c\n"
        ".inst 0xeb017e12\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe584001c\n"
        ".inst 0xe5c40000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00447a78\n"
    );
}

// DECOMP_FUNC(0x0024aea4, 48)
extern "C" __attribute__((naked)) void engine_func_0024aea4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0024\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5900000\n"
        ".inst 0xe2804903\n"
        ".inst 0xe2844ec5\n"
        ".inst 0xe594001c\n"
        ".inst 0xeb0172f7\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe584001c\n"
        ".inst 0xe5c40000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00447a78\n"
    );
}

// DECOMP_FUNC(0x00263164, 48)
extern "C" __attribute__((naked)) void func_00263164() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0024\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe2800020\n"
        ".inst 0xe1d008da\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00434210\n"
    );
}

// DECOMP_FUNC(0x00276b74, 48)
extern "C" __attribute__((naked)) void script_vm_func_00276b74() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0024\n"
        ".inst 0xe5900000\n"
        ".inst 0xe2800b33\n"
        ".inst 0xe1d01bb8\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe3a02003\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe1c02bb8\n"
        ".inst 0xe1c01bba\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00447a78\n"
    );
}

// DECOMP_FUNC(0x0028753c, 48)
extern "C" __attribute__((naked)) void engine_func_0028753c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0024\n"
        ".inst 0xe5d002f8\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe59f0014\n"
        ".inst 0xe59002fc\n"
        ".inst 0xe35000c8\n"
        ".inst 0xa3a00001\n"
        ".inst 0xaa000000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0049f91c\n"
    );
}

// DECOMP_FUNC(0x00299034, 48)
extern "C" __attribute__((naked)) void script_vm_func_00299034() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000\n"
        ".inst 0x13500001\n"
        ".inst 0x1a000005\n"
        ".inst 0xe59f1018\n"
        ".inst 0xe5911004\n"
        ".inst 0xe2811088\n"
        ".inst 0xe0810180\n"
        ".inst 0xe2801b92\n"
        ".inst 0xe2811fcb\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002a7bd4, 48)
extern "C" __attribute__((naked)) void ui_func_002a7bd4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe59f501c\n"
        ".inst 0xe5954000\n"
        ".inst 0xe5940000\n"
        ".inst 0xeb007272\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb0071da\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5850000\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0043e140\n"
    );
}

// DECOMP_FUNC(0x002a7dd8, 48)
extern "C" __attribute__((naked)) void engine_func_002a7dd8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe1d021b4\n"
        ".inst 0xe1520001\n"
        ".inst 0x02800014\n"
        ".inst 0x0a000003\n"
        ".inst 0xe1d022b0\n"
        ".inst 0xe1520001\n"
        ".inst 0x02800020\n"
        ".inst 0x13a00000\n"
        ".inst 0xe5900004\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00006801\n"
    );
}

// DECOMP_FUNC(0x002aa908, 48)
extern "C" __attribute__((naked)) void func_002aa908() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500020\n"
        ".inst 0x2a000006\n"
        ".inst 0xe59f101c\n"
        ".inst 0xe5911000\n"
        ".inst 0xe0810100\n"
        ".inst 0xe5900828\n"
        ".inst 0xe3500000\n"
        ".inst 0x15900000\n"
        ".inst 0x1a000000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004655e8\n"
    );
}

// DECOMP_FUNC(0x002bcff0, 48)
extern "C" __attribute__((naked)) void engine_func_002bcff0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe59f0014\n"
        ".inst 0xe5900000\n"
        ".inst 0xebf9d1a6\n"
        ".inst 0xe3500000\n"
        ".inst 0x059f0008\n"
        ".inst 0x07900104\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00433158\n"
        ".word 0x00446548\n"
    );
}

// DECOMP_FUNC(0x002c2a2c, 48)
extern "C" __attribute__((naked)) void battle_func_002c2a2c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500b01\n"
        ".inst 0xe59f1020\n"
        ".inst 0x12402b01\n"
        ".inst 0x12522001\n"
        ".inst 0x02400b01\n"
        ".inst 0x0a000002\n"
        ".inst 0xe352000f\n"
        ".inst 0x03a00002\n"
        ".inst 0x1a000000\n"
        ".inst 0xe5810124\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004c6290\n"
    );
}

// DECOMP_FUNC(0x002ceca8, 48)
extern "C" __attribute__((naked)) void battle_func_002ceca8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe59f501c\n"
        ".inst 0xe5954000\n"
        ".inst 0xe5940000\n"
        ".inst 0xebffd63d\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebffd5a5\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5850000\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0043e158\n"
    );
}

// DECOMP_FUNC(0x002d3dac, 48)
extern "C" __attribute__((naked)) void engine_func_002d3dac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0024\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5900000\n"
        ".inst 0xe2804903\n"
        ".inst 0xe2844ebf\n"
        ".inst 0xe594001c\n"
        ".inst 0xebff4f35\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe584001c\n"
        ".inst 0xe5c40000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00447a78\n"
    );
}

// DECOMP_FUNC(0x002d8da8, 48)
extern "C" __attribute__((naked)) void script_vm_func_002d8da8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0024\n"
        ".inst 0xe5900008\n"
        ".inst 0xe5d0107d\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5d0007c\n"
        ".inst 0xe3500002\n"
        ".inst 0x03a00001\n"
        ".inst 0x0a000000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002eff30, 48)
extern "C" __attribute__((naked)) void ui_func_002eff30() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfed446\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebff42e0\n"
        ".inst 0xe59f4010\n"
        ".inst 0xe5940000\n"
        ".inst 0xebff5103\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043df98\n"
    );
}

// DECOMP_FUNC(0x00203b64, 52)
extern "C" __attribute__((naked)) void engine_func_00203b64() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe3a04000\n"
        ".inst 0xe24dd008\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe1a0c004\n"
        ".inst 0xe59f0014\n"
        ".inst 0xe3a02004\n"
        ".inst 0xe1a03004\n"
        ".inst 0xe88d1010\n"
        ".inst 0xeb02ffad\n"
        ".inst 0xe28dd008\n"
        ".inst 0xe8bd8010\n"
        ".word 0x004c3828\n"
    );
}

// DECOMP_FUNC(0x00216880, 52)
extern "C" __attribute__((naked)) void camp_func_00216880() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0028\n"
        ".inst 0xe5900000\n"
        ".inst 0xe5901400\n"
        ".inst 0xe3510002\n"
        ".inst 0x1a000004\n"
        ".inst 0xe2800b25\n"
        ".inst 0xe5d00050\n"
        ".inst 0xe3500000\n"
        ".inst 0x03a00001\n"
        ".inst 0x0a000000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043dd68\n"
    );
}

// DECOMP_FUNC(0x002278e4, 52)
extern "C" __attribute__((naked)) void battle_func_002278e4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a03001\n"
        ".inst 0xe6bf1070\n"
        ".inst 0xe59f0020\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04002\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfffc89\n"
        ".inst 0xe3a01005\n"
        ".inst 0xe5c01004\n"
        ".inst 0xe5804028\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00434290\n"
    );
}

// DECOMP_FUNC(0x002458d4, 52)
extern "C" __attribute__((naked)) void script_vm_func_002458d4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500c05\n"
        ".inst 0x83a00000\n"
        ".inst 0x8a000007\n"
        ".inst 0xe59f101c\n"
        ".inst 0xe0802100\n"
        ".inst 0xe0820180\n"
        ".inst 0xe5911004\n"
        ".inst 0xe0810100\n"
        ".inst 0xe2800903\n"
        ".inst 0xe2800f7e\n"
        ".inst 0xe1d002bc\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x00295e74, 52)
extern "C" __attribute__((naked)) void script_vm_func_00295e74() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0028\n"
        ".inst 0xe5900000\n"
        ".inst 0xe5900008\n"
        ".inst 0xe3500003\n"
        ".inst 0x13500004\n"
        ".inst 0x0a000003\n"
        ".inst 0xe3500001\n"
        ".inst 0x13500002\n"
        ".inst 0x13a00000\n"
        ".inst 0x1a000000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043e128\n"
    );
}

// DECOMP_FUNC(0x002b89a0, 52)
extern "C" __attribute__((naked)) void camp_func_002b89a0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0028\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000005\n"
        ".inst 0xe2800b0d\n"
        ".inst 0xe2800f4b\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500014\n"
        ".inst 0x13a00000\n"
        ".inst 0x1a000000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0044dc20\n"
    );
}

// DECOMP_FUNC(0x002c87d0, 52)
extern "C" __attribute__((naked)) void func_002c87d0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0028\n"
        ".inst 0xe3a02010\n"
        ".inst 0xe5901000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe2811024\n"
        ".inst 0xe5d13000\n"
        ".inst 0xe281103c\n"
        ".inst 0xe3530000\n"
        ".inst 0x12800001\n"
        ".inst 0xe2522001\n"
        ".inst 0x1afffff9\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00447a60\n"
    );
}

// DECOMP_FUNC(0x002cd720, 52)
extern "C" __attribute__((naked)) void engine_func_002cd720() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebff260c\n"
        ".inst 0xe59f101c\n"
        ".inst 0xe5912004\n"
        ".inst 0xe5820a38\n"
        ".inst 0xe5912008\n"
        ".inst 0xe5820a38\n"
        ".inst 0xe591100c\n"
        ".inst 0xe5810a38\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002d886c, 52)
extern "C" __attribute__((naked)) void engine_func_002d886c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfef9b9\n"
        ".inst 0xe3500000\n"
        ".inst 0x03a000ff\n"
        ".inst 0x13e00000\n"
        ".inst 0xed9f0a04\n"
        ".inst 0xe3a02001\n"
        ".inst 0xe3a01000\n"
        ".inst 0xebfe0331\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x002e143c, 52)
extern "C" __attribute__((naked)) void engine_func_002e143c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a00000\n"
        ".inst 0xe59f0024\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe2804b01\n"
        ".inst 0xe5900478\n"
        ".inst 0xe2844078\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000002\n"
        ".inst 0xebff8bbf\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x004e1f68\n"
    );
}

// DECOMP_FUNC(0x002e1b00, 52)
extern "C" __attribute__((naked)) void engine_func_002e1b00() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0028\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5904008\n"
        ".inst 0xe3a00000\n"
        ".inst 0xebfed512\n"
        ".inst 0xe1c409b8\n"
        ".inst 0xe3a0200a\n"
        ".inst 0xe3a01003\n"
        ".inst 0xe5842084\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe5c41088\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002ebbdc, 52)
extern "C" __attribute__((naked)) void script_vm_func_002ebbdc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1028\n"
        ".inst 0xe3500010\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe3e00000\n"
        ".inst 0x2a000005\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe0811102\n"
        ".inst 0xe591187c\n"
        ".inst 0xe3510000\n"
        ".inst 0x1591009c\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004e26ec\n"
    );
}

// DECOMP_FUNC(0x002f503c, 52)
extern "C" __attribute__((naked)) void engine_func_002f503c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900008\n"
        ".inst 0xeddf1a07\n"
        ".inst 0xe28000b8\n"
        ".inst 0xec800a04\n"
        ".inst 0xe5940008\n"
        ".inst 0xe28000b8\n"
        ".inst 0xebff36e1\n"
        ".inst 0xe5941008\n"
        ".inst 0xe58100c8\n"
        ".inst 0xe8bd8010\n"
        ".word 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x002f6120, 52)
extern "C" __attribute__((naked)) void engine_func_002f6120() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe838c\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe3e02000\n"
        ".inst 0xe3a000c9\n"
        ".inst 0xebfe02b9\n"
        ".inst 0xe59f100c\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5c102f8\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0049f91c\n"
    );
}

// DECOMP_FUNC(0x002fc0ec, 52)
extern "C" u32 battle_func_002bf41c(void* task);

extern "C" __attribute__((used, noinline)) u32 ui_func_002fc0ec() {
    auto* const work = *reinterpret_cast<void* volatile*>(0x0044E2D0u);
    if (work == nullptr) {
        return 1;
    }

    const u32 registered = battle_func_002bf41c(*reinterpret_cast<void**>(work));
    return registered == 0 ? 1u : 0u;
}
