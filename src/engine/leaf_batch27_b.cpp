#include "types.h"

// Batch 27 B: full ARM instruction coverage, explicit returns, and bounded referenced literal tails.

// DECOMP_FUNC(0x0020fe3c, 56)
extern "C" __attribute__((naked)) void script_vm_func_0020fe3c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe3a00001\n"
        ".inst 0xeb0109e0\n"
        ".inst 0xe5941000\n"
        ".inst 0xe7911105\n"
        ".inst 0xeb02c10b\n"
        ".inst 0xe59f000c\n"
        ".inst 0xe5901000\n"
        ".inst 0xe2811001\n"
        ".inst 0xe5801000\n"
        ".inst 0xe8bd8070\n"
        ".word 0x004dad80\n"
    );
}

// DECOMP_FUNC(0x00221a78, 56)
extern "C" __attribute__((naked)) void func_00221a78() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f102c\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5911000\n"
        ".inst 0xe0411000\n"
        ".inst 0xe2511001\n"
        ".inst 0x4a000004\n"
        ".inst 0xebff2db3\n"
        ".inst 0xe59000d8\n"
        ".inst 0xe3500000\n"
        ".inst 0xc3a00001\n"
        ".inst 0xca000000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00433278\n"
    );
}

// DECOMP_FUNC(0x00222a00, 56)
extern "C" __attribute__((naked)) void battle_func_00222a00() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe59f5028\n"
        ".inst 0xe5954000\n"
        ".inst 0xe3540000\n"
        ".inst 0x0a000006\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3a01000\n"
        ".inst 0xeb0286e5\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb02864d\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5850000\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0044d1b0\n"
    );
}

// DECOMP_FUNC(0x00223bb0, 56)
extern "C" __attribute__((naked)) void camp_func_00223bb0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f002c\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe5904000\n"
        ".inst 0xe2840e66\n"
        ".inst 0xeb01eda6\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe2840e66\n"
        ".inst 0xeb01ed9d\n"
        ".inst 0xe0800005\n"
        ".inst 0xe0840080\n"
        ".inst 0xe2800c07\n"
        ".inst 0xe1d008ba\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0043dd50\n"
    );
}

// DECOMP_FUNC(0x0023a3a4, 56)
extern "C" __attribute__((naked)) void func_0023a3a4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f4024\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe59f0020\n"
        ".inst 0xe5942000\n"
        ".inst 0xe0800302\n"
        ".inst 0xe3a02040\n"
        ".inst 0xeb0201e5\n"
        ".inst 0xe5940000\n"
        ".inst 0xe2800001\n"
        ".inst 0xe5840000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00471a50\n"
        ".word 0x004e655c\n"
    );
}

// DECOMP_FUNC(0x00248320, 56)
extern "C" __attribute__((naked)) void script_vm_func_00248320() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00030\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb01e2e4\n"
        ".inst 0xeb01e2c5\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0014\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe3a01027\n"
        ".inst 0xe5900000\n"
        ".inst 0xeb004f70\n"
        ".inst 0xe0800004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x00248f6c, 56)
extern "C" __attribute__((naked)) void engine_func_00248f6c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00031\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb01dfd1\n"
        ".inst 0xeb01dfb2\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0014\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe3a01026\n"
        ".inst 0xe5900000\n"
        ".inst 0xeb004c5d\n"
        ".inst 0xe0800004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x0024aef0, 56)
extern "C" __attribute__((naked)) void script_vm_func_0024aef0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a0002d\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb01d7f0\n"
        ".inst 0xeb01d7d1\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0014\n"
        ".inst 0xe3a02001\n"
        ".inst 0xe3a01025\n"
        ".inst 0xe5900000\n"
        ".inst 0xeb00447c\n"
        ".inst 0xe0800004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x0024f210, 56)
extern "C" __attribute__((naked)) void engine_func_0024f210() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a0002d\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb01c728\n"
        ".inst 0xeb01c709\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0014\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe3a01025\n"
        ".inst 0xe5900000\n"
        ".inst 0xeb0033b4\n"
        ".inst 0xe0800004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x0024f6fc, 56)
extern "C" __attribute__((naked)) void script_vm_func_0024f6fc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00029\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb01c5ed\n"
        ".inst 0xeb01c5ce\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0014\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe3a01023\n"
        ".inst 0xe5900000\n"
        ".inst 0xeb003279\n"
        ".inst 0xe0800004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x002673e8, 56)
extern "C" __attribute__((naked)) void engine_func_002673e8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00032\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb0166b2\n"
        ".inst 0xeb016693\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0014\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe3a01028\n"
        ".inst 0xe5900000\n"
        ".inst 0xebffd33e\n"
        ".inst 0xe0800004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x0026a5f4, 56)
extern "C" __attribute__((naked)) void camp_func_0026a5f4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f102c\n"
        ".inst 0xe5911000\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe3500000\n"
        ".inst 0xe59f0018\n"
        ".inst 0x13a01000\n"
        ".inst 0x03a01001\n"
        ".inst 0xe5900000\n"
        ".inst 0xe2800a01\n"
        ".inst 0xe2800e7f\n"
        ".inst 0xe5c01000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043dcf0\n"
    );
}

// DECOMP_FUNC(0x0026f25c, 56)
extern "C" __attribute__((naked)) void camp_func_0026f25c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe350000c\n"
        ".inst 0xe3a01000\n"
        ".inst 0x2a000007\n"
        ".inst 0xe59f2020\n"
        ".inst 0xe0801080\n"
        ".inst 0xe0811200\n"
        ".inst 0xe5922004\n"
        ".inst 0xe2820088\n"
        ".inst 0xe0800101\n"
        ".inst 0xe2801b91\n"
        ".inst 0xe2811fe3\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002934d4, 56)
extern "C" __attribute__((naked)) void battle_func_002934d4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f002c\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5900000\n"
        ".inst 0xebffadac\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000005\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3100080\n"
        ".inst 0x1a000001\n"
        ".inst 0xe2100a01\n"
        ".inst 0x0a000000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x00295624, 56)
extern "C" __attribute__((naked)) void script_vm_func_00295624() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f102c\n"
        ".inst 0xe3500008\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe5911204\n"
        ".inst 0x2a000005\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe0810100\n"
        ".inst 0xe5900020\n"
        ".inst 0xe3500000\n"
        ".inst 0x13a02001\n"
        ".inst 0xe1a00002\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004e2f68\n"
    );
}

// DECOMP_FUNC(0x002cd598, 56)
extern "C" __attribute__((naked)) void camp_func_002cd598() {
    asm volatile(
        ".arm\n"
        ".inst 0xe350000c\n"
        ".inst 0xe3a01000\n"
        ".inst 0x2a000007\n"
        ".inst 0xe59f2020\n"
        ".inst 0xe5922000\n"
        ".inst 0xe3520000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe0801080\n"
        ".inst 0xe0810200\n"
        ".inst 0xe0820100\n"
        ".inst 0xe2801080\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043de68\n"
    );
}

// DECOMP_FUNC(0x002e1470, 56)
extern "C" __attribute__((naked)) void battle_func_002e1470() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f202c\n"
        ".inst 0xe3500004\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe3e00000\n"
        ".inst 0x2a000006\n"
        ".inst 0xe0811101\n"
        ".inst 0xe0821201\n"
        ".inst 0xe2811b01\n"
        ".inst 0xe28110bc\n"
        ".inst 0xe5912010\n"
        ".inst 0xe3520000\n"
        ".inst 0x15910044\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004e1f68\n"
    );
}

// DECOMP_FUNC(0x002e289c, 56)
extern "C" __attribute__((naked)) void engine_func_002e289c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfed1ad\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xebfddb16\n"
        ".inst 0xe59f2014\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe282005c\n"
        ".inst 0xe5824054\n"
        ".inst 0xebff73e8\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0049f91c\n"
    );
}

// DECOMP_FUNC(0x002e3a58, 56)
extern "C" __attribute__((naked)) void engine_func_002e3a58() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfecd3e\n"
        ".inst 0xe59f4020\n"
        ".inst 0xe5840000\n"
        ".inst 0xebfd932d\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3a01000\n"
        ".inst 0xebfee315\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00434228\n"
    );
}

// DECOMP_FUNC(0x002e3eb4, 56)
extern "C" __attribute__((naked)) void ui_func_002e3eb4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfebf76\n"
        ".inst 0xe59f4024\n"
        ".inst 0xe19040f4\n"
        ".inst 0xebfebf73\n"
        ".inst 0xe2800c49\n"
        ".inst 0xe1d006fa\n"
        ".inst 0xe1500004\n"
        ".inst 0xc1a04000\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfea81c\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00004968\n"
    );
}

// DECOMP_FUNC(0x002e4434, 56)
extern "C" __attribute__((naked)) void camp_func_002e4434() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f102c\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5914000\n"
        ".inst 0xe3540000\n"
        ".inst 0x0a000005\n"
        ".inst 0xebff53c5\n"
        ".inst 0xe1d009b0\n"
        ".inst 0xe59412f8\n"
        ".inst 0xe1500001\n"
        ".inst 0x03a00001\n"
        ".inst 0x0a000000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00434210\n"
    );
}

// DECOMP_FUNC(0x002eeeb4, 56)
extern "C" __attribute__((naked)) void engine_func_002eeeb4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfea027\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xebfda990\n"
        ".inst 0xe59f2014\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe282005c\n"
        ".inst 0xe5824054\n"
        ".inst 0xebff4262\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0049f91c\n"
    );
}

// DECOMP_FUNC(0x002f47cc, 56)
extern "C" __attribute__((naked)) void camp_func_002f47cc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a0002d\n"
        ".inst 0xe3a01004\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebff31b9\n"
        ".inst 0xebff319a\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0014\n"
        ".inst 0xe3a02004\n"
        ".inst 0xe3a01025\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfd9e45\n"
        ".inst 0xe0800004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x002fb3b8, 56)
extern "C" __attribute__((naked)) void engine_func_002fb3b8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a0002d\n"
        ".inst 0xe3a01003\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebff16be\n"
        ".inst 0xebff169f\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0014\n"
        ".inst 0xe3a02003\n"
        ".inst 0xe3a01025\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfd834a\n"
        ".inst 0xe0800004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x002fb468, 56)
extern "C" __attribute__((naked)) void engine_func_002fb468() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a0002a\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebff1692\n"
        ".inst 0xebff1673\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0014\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe3a01024\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfd831e\n"
        ".inst 0xe0800004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x00201690, 60)
extern "C" __attribute__((naked)) void camp_func_00201690() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0030\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5904004\n"
        ".inst 0xe5d40035\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000006\n"
        ".inst 0xe5d41009\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb02dd9b\n"
        ".inst 0xe3a01003\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5c41008\n"
        ".inst 0xe5c40035\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x002032fc, 60)
extern "C" __attribute__((naked)) void script_vm_func_002032fc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000\n"
        ".inst 0x13500001\n"
        ".inst 0x1a000009\n"
        ".inst 0xe59f3024\n"
        ".inst 0xe5933004\n"
        ".inst 0xe2833088\n"
        ".inst 0xe0830180\n"
        ".inst 0xe2803b92\n"
        ".inst 0xe2833fcb\n"
        ".inst 0xe2800909\n"
        ".inst 0xe2800eb3\n"
        ".inst 0xe5831000\n"
        ".inst 0xe5802000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x00208a28, 60)
extern "C" __attribute__((naked)) void script_vm_func_00208a28() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f002c\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5902370\n"
        ".inst 0xe59f0024\n"
        ".inst 0xe3520001\n"
        ".inst 0xe5900004\n"
        ".inst 0x058010c4\n"
        ".inst 0x0a000003\n"
        ".inst 0xe3a02002\n"
        ".inst 0xe5801000\n"
        ".inst 0xe58020c4\n"
        ".inst 0xe58010ac\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0049f91c\n"
        ".word 0x004474f0\n"
    );
}

// DECOMP_FUNC(0x0020fd8c, 60)
extern "C" __attribute__((naked)) void engine_func_0020fd8c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a05000\n"
        ".inst 0xe59f4028\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xeb02d16d\n"
        ".inst 0xe5845000\n"
        ".inst 0xe5940004\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xeb02d168\n"
        ".inst 0xe5845004\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0044e0e0\n"
    );
}

// DECOMP_FUNC(0x002227fc, 60)
extern "C" __attribute__((naked)) void script_vm_func_002227fc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500c05\n"
        ".inst 0x83a00000\n"
        ".inst 0x8a000009\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe0802100\n"
        ".inst 0xe0820180\n"
        ".inst 0xe5911004\n"
        ".inst 0xe0810100\n"
        ".inst 0xe2800903\n"
        ".inst 0xe2800f7e\n"
        ".inst 0xe1d002be\n"
        ".inst 0xe1a00c00\n"
        ".inst 0xe1a00d20\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x0023c274, 60)
extern "C" __attribute__((naked)) void battle_func_0023c274() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05003\n"
        ".inst 0xe1a03001\n"
        ".inst 0xe6bf1070\n"
        ".inst 0xe59f0020\n"
        ".inst 0xe1a04002\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe5900000\n"
        ".inst 0xebffaa24\n"
        ".inst 0xe3a01011\n"
        ".inst 0xe5c01004\n"
        ".inst 0xe5804028\n"
        ".inst 0xe580504c\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00434290\n"
    );
}

// DECOMP_FUNC(0x0023f518, 60)
extern "C" __attribute__((naked)) void ui_func_0023f518() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe892100a\n"
        ".inst 0xe2804084\n"
        ".inst 0xed9f0a09\n"
        ".inst 0xe884100a\n"
        ".inst 0xe590002c\n"
        ".inst 0xecf21a01\n"
        ".inst 0xe280004c\n"
        ".inst 0xecd20a02\n"
        ".inst 0xee600a80\n"
        ".inst 0xee211a00\n"
        ".inst 0xee210a80\n"
        ".inst 0xeb00331f\n"
        ".inst 0xe8bd8010\n"
        ".word 0x3c8efa35\n"
    );
}

// DECOMP_FUNC(0x002486ec, 60)
extern "C" __attribute__((naked)) void func_002486ec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe52de004\n"
        ".inst 0xe24dd044\n"
        ".inst 0xe1a0100d\n"
        ".inst 0xeb031c89\n"
        ".inst 0xec9d0a08\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe2801d05\n"
        ".inst 0xe2800e16\n"
        ".inst 0xec810a08\n"
        ".inst 0xe28d1020\n"
        ".inst 0xec910a08\n"
        ".inst 0xec800a08\n"
        ".inst 0xe28dd044\n"
        ".inst 0xe49df004\n"
        ".word 0x004ea81c\n"
    );
}

// DECOMP_FUNC(0x00254c6c, 60)
extern "C" __attribute__((naked)) void engine_func_00254c6c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5902000\n"
        ".inst 0xe3120001\n"
        ".inst 0x15900050\n"
        ".inst 0x0590004c\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000005\n"
        ".inst 0xe3510000\n"
        ".inst 0x059f1010\n"
        ".inst 0x159f1010\n"
        ".inst 0xe3a02001\n"
        ".inst 0xe5c02058\n"
        ".inst 0xe580104c\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0015555c\n"
        ".word 0x00151404\n"
    );
}

// DECOMP_FUNC(0x002599bc, 60)
extern "C" __attribute__((naked)) void camp_func_002599bc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1030\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5912000\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3520000\n"
        ".inst 0x13500000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe5922004\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe1a00002\n"
        ".inst 0xeb0588f3\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043de68\n"
    );
}

// DECOMP_FUNC(0x0027e584, 60)
extern "C" __attribute__((naked)) void engine_func_0027e584() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0030\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5904020\n"
        ".inst 0xe2840008\n"
        ".inst 0xeb0036e2\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe2840c22\n"
        ".inst 0xeb0036d0\n"
        ".inst 0xe3500000\n"
        ".inst 0x13a00001\n"
        ".inst 0x1a000000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00439c88\n"
    );
}

// DECOMP_FUNC(0x0027e5c0, 60)
extern "C" __attribute__((naked)) void engine_func_0027e5c0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0030\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5904020\n"
        ".inst 0xe2840008\n"
        ".inst 0xeb00389e\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe2840c22\n"
        ".inst 0xebff2d39\n"
        ".inst 0xe3500000\n"
        ".inst 0x13a00001\n"
        ".inst 0x1a000000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00439c88\n"
    );
}

// DECOMP_FUNC(0x0029ed08, 60)
extern "C" __attribute__((naked)) void camp_func_0029ed08() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500c05\n"
        ".inst 0x83a00000\n"
        ".inst 0x8a000009\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe0802100\n"
        ".inst 0xe0820180\n"
        ".inst 0xe5911004\n"
        ".inst 0xe0810100\n"
        ".inst 0xe2800903\n"
        ".inst 0xe2800f7e\n"
        ".inst 0xe1d002be\n"
        ".inst 0xe2000002\n"
        ".inst 0xe1a000a0\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002bc2c4, 60)
extern "C" __attribute__((naked)) void ui_func_002bc2c4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0030\n"
        ".inst 0xed9f0a0a\n"
        ".inst 0xe52de004\n"
        ".inst 0xe24dd014\n"
        ".inst 0xed800a21\n"
        ".inst 0xed8d0a00\n"
        ".inst 0xed8d0a01\n"
        ".inst 0xed8d0a02\n"
        ".inst 0xed8d0a03\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xebffc7f4\n"
        ".inst 0xe28dd014\n"
        ".inst 0xe49df004\n"
        ".word 0x3f800000\n"
        ".word 0x004d4680\n"
    );
}

// DECOMP_FUNC(0x002c5094, 60)
extern "C" __attribute__((naked)) void battle_func_002c5094() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4038\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900014\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe1a0100d\n"
        ".inst 0xebffde48\n"
        ".inst 0xe2844014\n"
        ".inst 0xe59d0000\n"
        ".inst 0xe8940006\n"
        ".inst 0xebf9c893\n"
        ".inst 0xebffe87a\n"
        ".inst 0xe8bd8038\n"
        ".word 0x00000207\n"
    );
}

// DECOMP_FUNC(0x002d8774, 60)
extern "C" __attribute__((naked)) void func_002d8774() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f402c\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x03a00001\n"
        ".inst 0x0a000006\n"
        ".inst 0xebfec3ab\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a000002\n"
        ".inst 0xe5941000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe5c10008\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0044dc50\n"
    );
}

// DECOMP_FUNC(0x002e32c8, 60)
extern "C" __attribute__((naked)) void unite_func_002e32c8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0030\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5904000\n"
        ".inst 0xe2844b25\n"
        ".inst 0xe2844f73\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000004\n"
        ".inst 0xebf9be02\n"
        ".inst 0xe5940000\n"
        ".inst 0xebff11ea\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043dd68\n"
    );
}

// DECOMP_FUNC(0x002e3abc, 60)
extern "C" __attribute__((naked)) void engine_func_002e3abc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfecd25\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0020\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfe6c2f\n"
        ".inst 0xe5901028\n"
        ".inst 0xe3a02002\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe2811c01\n"
        ".inst 0xe1c124bc\n"
        ".inst 0xe1c144be\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002f01c8, 60)
extern "C" __attribute__((naked)) void script_vm_func_002f01c8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f402c\n"
        ".inst 0xe5940000\n"
        ".inst 0xebfe3a6f\n"
        ".inst 0xe5900028\n"
        ".inst 0xe3a0100b\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe2800c01\n"
        ".inst 0xe1c014bc\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3a0100f\n"
        ".inst 0xebfd718b\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002f3590, 60)
extern "C" __attribute__((naked)) void ui_func_002f3590() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f002c\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5900004\n"
        ".inst 0xed900a13\n"
        ".inst 0xedd01a16\n"
        ".inst 0xedd00a15\n"
        ".inst 0xed901a18\n"
        ".inst 0xee300a61\n"
        ".inst 0xee700ac1\n"
        ".inst 0xebfe3aba\n"
        ".inst 0xeddf0a02\n"
        ".inst 0xee200a20\n"
        ".inst 0xe8bd8010\n"
        ".word 0x004474f0\n"
        ".word 0x42654ca3\n"
    );
}

// DECOMP_FUNC(0x002f5fa8, 60)
extern "C" __attribute__((naked)) void engine_func_002f5fa8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0030\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe5900564\n"
        ".inst 0xe3500002\n"
        ".inst 0x03a00001\n"
        ".inst 0x0a000003\n"
        ".inst 0xea000001\n"
        ".inst 0xe320f000\n"
        ".inst 0xeb0000bd\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043df98\n"
    );
}

// DECOMP_FUNC(0x002fcce4, 60)
extern "C" __attribute__((naked)) void func_002fcce4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a05000\n"
        ".inst 0xe59f4028\n"
        ".inst 0xe5940040\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xebfd29aa\n"
        ".inst 0xe5845040\n"
        ".inst 0xe594003c\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xebfd2995\n"
        ".inst 0xe584503c\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0044ea80\n"
    );
}

// DECOMP_FUNC(0x002fecc0, 60)
extern "C" __attribute__((naked)) void camp_func_002fecc0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a00025\n"
        ".inst 0xe59f5028\n"
        ".inst 0xe5954000\n"
        ".inst 0xebfe9729\n"
        ".inst 0xebfd4e55\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3a01000\n"
        ".inst 0xebff1634\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebff159c\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5850000\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0043dd90\n"
    );
}

// DECOMP_FUNC(0x002012ac, 64)
extern "C" __attribute__((naked)) void battle_func_002012ac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f4030\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe5900000\n"
        ".inst 0xeb02f854\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5900000\n"
        ".inst 0xeb030cb5\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043dfc0\n"
    );
}

// DECOMP_FUNC(0x002221b0, 64)
extern "C" __attribute__((naked)) void battle_func_002221b0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f4030\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe5900000\n"
        ".inst 0xeb027493\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5900000\n"
        ".inst 0xeb0288f4\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043e088\n"
    );
}

// DECOMP_FUNC(0x0022a458, 64)
extern "C" __attribute__((naked)) void script_vm_func_0022a458() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe59f002c\n"
        ".inst 0xe1a04001\n"
        ".inst 0xe5900000\n"
        ".inst 0xeb01f2f6\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000005\n"
        ".inst 0xe1a02004\n"
        ".inst 0xe3a0101e\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb01f2c5\n"
        ".inst 0xe3500000\n"
        ".inst 0x13a00001\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00432fc8\n"
    );
}

// DECOMP_FUNC(0x0022a498, 64)
extern "C" __attribute__((naked)) void func_0022a498() {
    asm volatile(
        ".arm\n"
        ".inst 0xe2800b0b\n"
        ".inst 0xe2800fe6\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5801000\n"
        ".inst 0xeb008e71\n"
        ".inst 0xeb00e1eb\n"
        ".inst 0xe59f0018\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe5901634\n"
        ".inst 0xe3c11302\n"
        ".inst 0xe5801634\n"
        ".inst 0xe8bd8010\n"
        ".word 0x004342c8\n"
    );
}

// DECOMP_FUNC(0x0022b818, 64)
extern "C" __attribute__((naked)) void engine_func_0022b818() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1034\n"
        ".inst 0xe3a02001\n"
        ".inst 0xe5c122f8\n"
        ".inst 0xe1d023fc\n"
        ".inst 0xe28220c8\n"
        ".inst 0xe58122fc\n"
        ".inst 0xe581231c\n"
        ".inst 0xe5900d60\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5d02020\n"
        ".inst 0xe5812300\n"
        ".inst 0xe5d00020\n"
        ".inst 0xe5810320\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0049f91c\n"
    );
}

// DECOMP_FUNC(0x002335c0, 64)
extern "C" __attribute__((naked)) void ui_func_002335c0() {
    asm volatile(
        ".arm\n"
        ".inst 0xed9f0a0c\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe1a00001\n"
        ".inst 0xeef01a40\n"
        ".inst 0xeeb01a40\n"
        ".inst 0xed9f2a06\n"
        ".inst 0xe3a01001\n"
        ".inst 0xeddf0a06\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb022c64\n"
        ".inst 0xeebd0ac0\n"
        ".inst 0xee100a10\n"
        ".inst 0xe8bd8010\n"
        ".word 0x3f800000\n"
        ".word 0x00000000\n"
        ".word 0xc1a00000\n"
    );
}

// DECOMP_FUNC(0x0027db38, 64)
extern "C" __attribute__((naked)) void script_vm_func_0027db38() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0030\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5900004\n"
        ".inst 0xe2800b7d\n"
        ".inst 0xe28000dc\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a000003\n"
        ".inst 0xe59f0014\n"
        ".inst 0xeb010c11\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043e2a8\n"
        ".word 0x00000528\n"
    );
}

// DECOMP_FUNC(0x0027e9e4, 64)
extern "C" __attribute__((naked)) void script_vm_func_0027e9e4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe59f002c\n"
        ".inst 0xe3a06001\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe1a01002\n"
        ".inst 0xe5904000\n"
        ".inst 0xe2840044\n"
        ".inst 0xe5846008\n"
        ".inst 0xeb00fc2c\n"
        ".inst 0xe5c45023\n"
        ".inst 0xe3a0001e\n"
        ".inst 0xe5c46020\n"
        ".inst 0xe5840010\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0043e128\n"
    );
}

// DECOMP_FUNC(0x00289984, 64)
extern "C" __attribute__((naked)) void script_vm_func_00289984() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0034\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5904004\n"
        ".inst 0xe5d40008\n"
        ".inst 0xe3500000\n"
        ".inst 0x13540000\n"
        ".inst 0x0a000006\n"
        ".inst 0xe5d41009\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb00bcdd\n"
        ".inst 0xe3a01003\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5c41008\n"
        ".inst 0xe5c40035\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x0029a384, 64)
extern "C" __attribute__((naked)) void engine_func_0029a384() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f2034\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe5924004\n"
        ".inst 0xe2840c13\n"
        ".inst 0xebfecdf0\n"
        ".inst 0xe2840c1e\n"
        ".inst 0xe2800066\n"
        ".inst 0xe2844b07\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe2844fae\n"
        ".inst 0xe3a02001\n"
        ".inst 0xe5c01000\n"
        ".inst 0xe5c42000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x002bf6d0, 64)
extern "C" __attribute__((naked)) void camp_func_002bf6d0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04001\n"
        ".inst 0xebffc2aa\n"
        ".inst 0xe59f1028\n"
        ".inst 0xe3e0207c\n"
        ".inst 0xe5900004\n"
        ".inst 0xe0c13491\n"
        ".inst 0xe5900000\n"
        ".inst 0xe1a03341\n"
        ".inst 0xe0431fc1\n"
        ".inst 0xe0010291\n"
        ".inst 0xe0841181\n"
        ".inst 0xe0811101\n"
        ".inst 0xe0800101\n"
        ".inst 0xe8bd8010\n"
        ".word 0x10624dd3\n"
    );
}

// DECOMP_FUNC(0x002d3d6c, 64)
extern "C" __attribute__((naked)) void script_vm_func_002d3d6c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0034\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe5905000\n"
        ".inst 0xe2854903\n"
        ".inst 0xe2844ec7\n"
        ".inst 0xe5940020\n"
        ".inst 0xebff4f45\n"
        ".inst 0xe3a06000\n"
        ".inst 0xe5846020\n"
        ".inst 0xe2854b33\n"
        ".inst 0xe2844094\n"
        ".inst 0xe5940020\n"
        ".inst 0xebff4f3f\n"
        ".inst 0xe5846020\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00447a78\n"
    );
}

// DECOMP_FUNC(0x002dbb9c, 64)
extern "C" __attribute__((naked)) void engine_func_002dbb9c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfeeced\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0024\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfe8bf7\n"
        ".inst 0xe5900028\n"
        ".inst 0xe1d000b2\n"
        ".inst 0xe1500004\n"
        ".inst 0x03a00001\n"
        ".inst 0x13a00000\n"
        ".inst 0xebfec8e0\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002dfdf0, 64)
extern "C" __attribute__((naked)) void script_vm_func_002dfdf0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0034\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe5905000\n"
        ".inst 0xe2854903\n"
        ".inst 0xe2844ec7\n"
        ".inst 0xe5940020\n"
        ".inst 0xebf9cb3a\n"
        ".inst 0xe3a06000\n"
        ".inst 0xe5c46000\n"
        ".inst 0xe2854b33\n"
        ".inst 0xe2844094\n"
        ".inst 0xe5940020\n"
        ".inst 0xebf9cb34\n"
        ".inst 0xe5c46000\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00447a78\n"
    );
}

// DECOMP_FUNC(0x002e3c28, 64)
extern "C" __attribute__((naked)) void engine_func_002e3c28() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfeccca\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0024\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfe6bd4\n"
        ".inst 0xe5901028\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe1d11fba\n"
        ".inst 0xe0110410\n"
        ".inst 0x13a00001\n"
        ".inst 0xebfea8bd\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002e8b60, 64)
extern "C" __attribute__((naked)) void script_vm_func_002e8b60() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0030\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5904000\n"
        ".inst 0xe59f0028\n"
        ".inst 0xe7900004\n"
        ".inst 0xebf9a7df\n"
        ".inst 0xe2841b33\n"
        ".inst 0xe28110d8\n"
        ".inst 0xe2844b33\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe28440dc\n"
        ".inst 0xe5c10000\n"
        ".inst 0xe5840000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00447a78\n"
        ".word 0x0000cbec\n"
    );
}

// DECOMP_FUNC(0x002f063c, 64)
extern "C" __attribute__((naked)) void engine_func_002f063c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a00000\n"
        ".inst 0xebfe9a45\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0024\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfe394f\n"
        ".inst 0xe5901028\n"
        ".inst 0xe3a05001\n"
        ".inst 0xe1d10fba\n"
        ".inst 0xe0100415\n"
        ".inst 0x13a00001\n"
        ".inst 0xebfe7638\n"
        ".inst 0xe1a00005\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002f60e0, 64)
extern "C" __attribute__((naked)) void camp_func_002f60e0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0034\n"
        ".inst 0xe5900000\n"
        ".inst 0xe2800c02\n"
        ".inst 0xe5d010b4\n"
        ".inst 0xe3510000\n"
        ".inst 0x05d010b5\n"
        ".inst 0x03510000\n"
        ".inst 0x1a000004\n"
        ".inst 0xe5d010b6\n"
        ".inst 0xe3510000\n"
        ".inst 0x05d000b7\n"
        ".inst 0x03500000\n"
        ".inst 0x0a000000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043dc88\n"
    );
}

// DECOMP_FUNC(0x002032b8, 68)
extern "C" __attribute__((naked)) void func_002032b8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500c05\n"
        ".inst 0x83a00000\n"
        ".inst 0x8a00000b\n"
        ".inst 0xe59f202c\n"
        ".inst 0xe0803100\n"
        ".inst 0xe0830180\n"
        ".inst 0xe5922004\n"
        ".inst 0xe0820100\n"
        ".inst 0xe2800903\n"
        ".inst 0xe2800f7e\n"
        ".inst 0xe1d022be\n"
        ".inst 0xe3c22002\n"
        ".inst 0xe1821081\n"
        ".inst 0xe1c012be\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x002116c4, 68)
extern "C" __attribute__((naked)) void script_vm_func_002116c4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe59f5034\n"
        ".inst 0xe5954000\n"
        ".inst 0xeb0103a7\n"
        ".inst 0xeb01e36e\n"
        ".inst 0xeb020142\n"
        ".inst 0xeb0200de\n"
        ".inst 0xebffffef\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3a01000\n"
        ".inst 0xeb02cbb1\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb02cb19\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5850000\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0043da90\n"
    );
}

// DECOMP_FUNC(0x00221f70, 68)
extern "C" __attribute__((naked)) void engine_func_00221f70() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb01d3f8\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xeb01d3f5\n"
        ".inst 0xe59f1020\n"
        ".inst 0xe1a03000\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe791c104\n"
        ".inst 0xe1a01002\n"
        ".inst 0xe1a0000c\n"
        ".inst 0xeb03a0b9\n"
        ".inst 0xeb01afea\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043df70\n"
    );
}

// DECOMP_FUNC(0x0026a5b0, 68)
extern "C" __attribute__((naked)) void camp_func_0026a5b0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0038\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5904008\n"
        ".inst 0xeb015974\n"
        ".inst 0xe2800b7d\n"
        ".inst 0xe2800054\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x03a00001\n"
        ".inst 0x0a000004\n"
        ".inst 0xe2840b01\n"
        ".inst 0xe3a01007\n"
        ".inst 0xe2800fd5\n"
        ".inst 0xeb015291\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043e188\n"
    );
}

// DECOMP_FUNC(0x0029c784, 68)
extern "C" __attribute__((naked)) void script_vm_func_0029c784() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe59f1030\n"
        ".inst 0xe5914004\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe2840a01\n"
        ".inst 0xe2800e8b\n"
        ".inst 0xebfec48f\n"
        ".inst 0xe3550000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe2840b06\n"
        ".inst 0xe1d01bbc\n"
        ".inst 0xe1d02bbe\n"
        ".inst 0xe1c01bb8\n"
        ".inst 0xe1c02bba\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x002a8988, 68)
extern "C" __attribute__((naked)) void script_vm_func_002a8988() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900080\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000009\n"
        ".inst 0xe5940010\n"
        ".inst 0xeb001861\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe5941010\n"
        ".inst 0xe5942084\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfff695\n"
        ".inst 0xe3e01000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe1c408f0\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00433158\n"
    );
}

// DECOMP_FUNC(0x002b2530, 68)
extern "C" __attribute__((naked)) void ui_func_002b2530() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1038\n"
        ".inst 0xe1a02a20\n"
        ".inst 0xe5913000\n"
        ".inst 0xe1a01600\n"
        ".inst 0xe7930182\n"
        ".inst 0xe1a01621\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000005\n"
        ".inst 0xe5902024\n"
        ".inst 0xe1520001\n"
        ".inst 0x0a000003\n"
        ".inst 0xe590004c\n"
        ".inst 0xe3500000\n"
        ".inst 0x1afffff9\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004e3cf4\n"
    );
}

// DECOMP_FUNC(0x002cdb0c, 68)
extern "C" __attribute__((naked)) void engine_func_002cdb0c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0034\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5d002f8\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a000003\n"
        ".inst 0xe59f0024\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3700001\n"
        ".inst 0x0a000003\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe1a01002\n"
        ".inst 0xe3a00006\n"
        ".inst 0xebffdf9d\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0049f91c\n"
        ".word 0x0049fd14\n"
    );
}

// DECOMP_FUNC(0x002d8d4c, 68)
extern "C" __attribute__((naked)) void engine_func_002d8d4c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0034\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5d002f8\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a000003\n"
        ".inst 0xe59f0024\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3700001\n"
        ".inst 0x0a000003\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe1a01002\n"
        ".inst 0xe3a00008\n"
        ".inst 0xebffb30d\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0049f91c\n"
        ".word 0x0049fd14\n"
    );
}

// DECOMP_FUNC(0x002de1c4, 68)
extern "C" __attribute__((naked)) void engine_func_002de1c4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe590100c\n"
        ".inst 0xe59f4030\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe1d030b8\n"
        ".inst 0xe5902010\n"
        ".inst 0xe594001c\n"
        ".inst 0xebfdad50\n"
        ".inst 0xe594001c\n"
        ".inst 0xebfdc71c\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe320f000\n"
        ".inst 0xebfdc890\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0044ea80\n"
    );
}

// DECOMP_FUNC(0x002e43f0, 68)
extern "C" __attribute__((naked)) void ui_func_002e43f0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0038\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a05000\n"
        ".inst 0xe5904000\n"
        ".inst 0xe3540000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe2840020\n"
        ".inst 0xe1d008da\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a000003\n"
        ".inst 0xe2840020\n"
        ".inst 0xe1d005fc\n"
        ".inst 0xe350000a\n"
        ".inst 0x03a05001\n"
        ".inst 0xe1a00005\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00434210\n"
    );
}

// DECOMP_FUNC(0x002f06ec, 68)
extern "C" __attribute__((naked)) void engine_func_002f06ec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe9a19\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0028\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfe3923\n"
        ".inst 0xe5900028\n"
        ".inst 0xe2800c01\n"
        ".inst 0xe1d000b0\n"
        ".inst 0xe1500004\n"
        ".inst 0xa3a00001\n"
        ".inst 0xb3a00000\n"
        ".inst 0xebfe760b\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x00211d44, 72)
extern "C" __attribute__((naked)) void engine_func_00211d44() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb021483\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xeb015404\n"
        ".inst 0xeddf0a09\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb0417dc\n"
        ".inst 0xe1a04000\n"
        ".inst 0xeb01de2d\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb011e79\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb01f074\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00000000\n"
    );
}

// DECOMP_FUNC(0x0022013c, 72)
extern "C" __attribute__((naked)) void func_0022013c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f103c\n"
        ".inst 0xe1a02a20\n"
        ".inst 0xe5913000\n"
        ".inst 0xe1a01600\n"
        ".inst 0xe7930182\n"
        ".inst 0xe1a01621\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000005\n"
        ".inst 0xe5902024\n"
        ".inst 0xe1520001\n"
        ".inst 0x0a000003\n"
        ".inst 0xe590004c\n"
        ".inst 0xe3500000\n"
        ".inst 0x1afffff9\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5900030\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004e3cf4\n"
    );
}

// DECOMP_FUNC(0x0023e48c, 72)
extern "C" __attribute__((naked)) void engine_func_0023e48c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3520000\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a04001\n"
        ".inst 0x0a000004\n"
        ".inst 0xe59f0028\n"
        ".inst 0xe5900000\n"
        ".inst 0xeb01a2e7\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000005\n"
        ".inst 0xe1a02004\n"
        ".inst 0xe3a0100c\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb01a2b6\n"
        ".inst 0xe3500000\n"
        ".inst 0x13a00001\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00432fc8\n"
    );
}

// DECOMP_FUNC(0x0023e500, 72)
extern "C" __attribute__((naked)) void engine_func_0023e500() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3520000\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a04001\n"
        ".inst 0x0a000004\n"
        ".inst 0xe59f0028\n"
        ".inst 0xe5900000\n"
        ".inst 0xeb01a2ca\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000005\n"
        ".inst 0xe1a02004\n"
        ".inst 0xe3a01010\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb01a299\n"
        ".inst 0xe3500000\n"
        ".inst 0x13a00001\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00432fc8\n"
    );
}

// DECOMP_FUNC(0x00270250, 72)
extern "C" __attribute__((naked)) void script_vm_func_00270250() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a05000\n"
        ".inst 0xe59f4034\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xeb01503c\n"
        ".inst 0xe5845000\n"
        ".inst 0xe5940030\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe5941034\n"
        ".inst 0xe3a00038\n"
        ".inst 0xeb00fa28\n"
        ".inst 0xe5845034\n"
        ".inst 0xe5845030\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00448c58\n"
    );
}

// DECOMP_FUNC(0x0029a320, 72)
extern "C" __attribute__((naked)) void engine_func_0029a320() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f203c\n"
        ".inst 0xe3500000\n"
        ".inst 0xe5922004\n"
        ".inst 0x02822b07\n"
        ".inst 0x02822faa\n"
        ".inst 0x0a000008\n"
        ".inst 0xe3500001\n"
        ".inst 0x02822b07\n"
        ".inst 0x02822fab\n"
        ".inst 0x05821000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe3500002\n"
        ".inst 0x02822a01\n"
        ".inst 0x02822eeb\n"
        ".inst 0x1a000000\n"
        ".inst 0xe5821000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0044e140\n"
    );
}

// DECOMP_FUNC(0x002a7ebc, 72)
extern "C" __attribute__((naked)) void engine_func_002a7ebc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0034\n"
        ".inst 0xe3a05000\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe8840021\n"
        ".inst 0xe284000c\n"
        ".inst 0xe5845008\n"
        ".inst 0xe584500c\n"
        ".inst 0xe5845010\n"
        ".inst 0xeb00754c\n"
        ".inst 0xe5c45014\n"
        ".inst 0xe284000c\n"
        ".inst 0xe5845018\n"
        ".inst 0xeb0070d2\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00421960\n"
    );
}

// DECOMP_FUNC(0x002e226c, 72)
extern "C" __attribute__((naked)) void engine_func_002e226c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfed339\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xebfe12ba\n"
        ".inst 0xeddf0a09\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb009f89\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfe9ce3\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfddd2f\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfeaf2a\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x41700000\n"
    );
}

// DECOMP_FUNC(0x002ec05c, 72)
extern "C" __attribute__((naked)) void ui_func_002ec05c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4030\n"
        ".inst 0xe24dd00c\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a04001\n"
        ".inst 0xebff4ba8\n"
        ".inst 0xed9f0a0a\n"
        ".inst 0xebff4da5\n"
        ".inst 0xe3a00076\n"
        ".inst 0xe58d0004\n"
        ".inst 0xe1a03005\n"
        ".inst 0xe3a0200d\n"
        ".inst 0xe3a01039\n"
        ".inst 0xe3a00002\n"
        ".inst 0xe58d4000\n"
        ".inst 0xebff4d2f\n"
        ".inst 0xe28dd00c\n"
        ".inst 0xe8bd8030\n"
        ".word 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x002f5f60, 72)
extern "C" __attribute__((naked)) void engine_func_002f5f60() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe83fc\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xebfdc37d\n"
        ".inst 0xeddf0a09\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb008755\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfe4da6\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfd8df2\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfe5fed\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x41700000\n"
    );
}

// DECOMP_FUNC(0x002f70c0, 72)
extern "C" __attribute__((naked)) void engine_func_002f70c0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe7fa4\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f002c\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfe1eae\n"
        ".inst 0xe5901028\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe0811084\n"
        ".inst 0xe2811c01\n"
        ".inst 0xe1d112b6\n"
        ".inst 0xe1500521\n"
        ".inst 0x13a00000\n"
        ".inst 0xebfe5b95\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x002fea58, 72)
extern "C" __attribute__((naked)) void ui_func_002fea58() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfe997c\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebff0816\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900064\n"
        ".inst 0xe3a05000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xebff205e\n"
        ".inst 0xe5845064\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebff1633\n"
        ".inst 0xe59f0004\n"
        ".inst 0xe5805004\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0044d048\n"
    );
}

// DECOMP_FUNC(0x0020043c, 76)
extern "C" __attribute__((naked)) void camp_func_0020043c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe59f0038\n"
        ".inst 0xe3a05000\n"
        ".inst 0xe5904000\n"
        ".inst 0xe3540000\n"
        ".inst 0x13560000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe5940004\n"
        ".inst 0xeb06ee96\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5940004\n"
        ".inst 0xe1a01006\n"
        ".inst 0xeb06ee3e\n"
        ".inst 0xe3a05001\n"
        ".inst 0xe1a00005\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0043de68\n"
    );
}

// DECOMP_FUNC(0x0022ccec, 76)
extern "C" __attribute__((naked)) void func_0022ccec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f103c\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe4801020\n"
        ".inst 0xeb016a1f\n"
        ".inst 0xe28000a8\n"
        ".inst 0xeb000643\n"
        ".inst 0xe59f2028\n"
        ".inst 0xe24000c8\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe580255c\n"
        ".inst 0xe5c0101c\n"
        ".inst 0xe5c0101d\n"
        ".inst 0xe5c0101e\n"
        ".inst 0xe58015a0\n"
        ".inst 0xe5801598\n"
        ".inst 0xe580159c\n"
        ".inst 0xe8bd8010\n"
        ".word 0x004220cc\n"
        ".word 0x004221d8\n"
    );
}

// DECOMP_FUNC(0x0023b834, 76)
extern "C" __attribute__((naked)) void func_0023b834() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f2040\n"
        ".inst 0xe52d4004\n"
        ".inst 0xe5923010\n"
        ".inst 0xe082c103\n"
        ".inst 0xe59c1008\n"
        ".inst 0xe311000f\n"
        ".inst 0x0a000004\n"
        ".inst 0xe1a04fc1\n"
        ".inst 0xe0814e24\n"
        ".inst 0xe3c4400f\n"
        ".inst 0xe0414004\n"
        ".inst 0xe0811004\n"
        ".inst 0xe7922103\n"
        ".inst 0xe0813000\n"
        ".inst 0xe58c3008\n"
        ".inst 0xe49d4004\n"
        ".inst 0xe0820001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004daec0\n"
    );
}

// DECOMP_FUNC(0x0023c748, 76)
extern "C" __attribute__((naked)) void battle_func_0023c748() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05003\n"
        ".inst 0xe1a03001\n"
        ".inst 0xe6bf1070\n"
        ".inst 0xe59f0030\n"
        ".inst 0xe1a04002\n"
        ".inst 0xed2d8b02\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe5900000\n"
        ".inst 0xed9d8a06\n"
        ".inst 0xebffa8ed\n"
        ".inst 0xe3a01018\n"
        ".inst 0xe5c01004\n"
        ".inst 0xe1c042b4\n"
        ".inst 0xe1c052b6\n"
        ".inst 0xed808a0a\n"
        ".inst 0xecbd8b02\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00434290\n"
    );
}

// DECOMP_FUNC(0x00240660, 76)
extern "C" __attribute__((naked)) void battle_func_00240660() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05003\n"
        ".inst 0xe1a03001\n"
        ".inst 0xe6bf1070\n"
        ".inst 0xe59f0030\n"
        ".inst 0xe1a04002\n"
        ".inst 0xed2d8b02\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe5900000\n"
        ".inst 0xed9d8a06\n"
        ".inst 0xebff9927\n"
        ".inst 0xe3a01009\n"
        ".inst 0xe5c01004\n"
        ".inst 0xe5804014\n"
        ".inst 0xe5805028\n"
        ".inst 0xed808a13\n"
        ".inst 0xecbd8b02\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00434290\n"
    );
}

// DECOMP_FUNC(0x00245888, 76)
extern "C" __attribute__((naked)) void func_00245888() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500c05\n"
        ".inst 0x83a00000\n"
        ".inst 0x8a00000c\n"
        ".inst 0xe59f2030\n"
        ".inst 0xe080c100\n"
        ".inst 0xe08c0180\n"
        ".inst 0xe6ff1071\n"
        ".inst 0xe5923004\n"
        ".inst 0xe59f2020\n"
        ".inst 0xe0830100\n"
        ".inst 0xe2800903\n"
        ".inst 0xe2800f7e\n"
        ".inst 0xe1510002\n"
        ".inst 0xe1c012bc\n"
        ".inst 0x81c022bc\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043e2a8\n"
        ".word 0x0000270f\n"
    );
}

// DECOMP_FUNC(0x00248c0c, 76)
extern "C" __attribute__((naked)) void engine_func_00248c0c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a04000\n"
        ".inst 0xe59f5038\n"
        ".inst 0xe5950004\n"
        ".inst 0xe8900006\n"
        ".inst 0xe5900018\n"
        ".inst 0xeb006a42\n"
        ".inst 0xe2100102\n"
        ".inst 0x4a000006\n"
        ".inst 0xe5950004\n"
        ".inst 0xe5901018\n"
        ".inst 0xe5910210\n"
        ".inst 0xe3500000\n"
        ".inst 0x11a04000\n"
        ".inst 0xe1a00001\n"
        ".inst 0xebffc123\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00464fa8\n"
    );
}

// DECOMP_FUNC(0x0027fd08, 76)
extern "C" __attribute__((naked)) void script_vm_func_0027fd08() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1038\n"
        ".inst 0xe5911000\n"
        ".inst 0xe5912000\n"
        ".inst 0xe1520000\n"
        ".inst 0x0a000009\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe3500001\n"
        ".inst 0xe8810005\n"
        ".inst 0x0d9f0a07\n"
        ".inst 0xe5812008\n"
        ".inst 0x0d810a16\n"
        ".inst 0x0a000002\n"
        ".inst 0xe3500003\n"
        ".inst 0x159f000c\n"
        ".inst 0x15c0217c\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00447e88\n"
        ".word 0x40a00000\n"
        ".word 0x0049f91c\n"
    );
}

// DECOMP_FUNC(0x002883bc, 76)
extern "C" __attribute__((naked)) void camp_func_002883bc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500c05\n"
        ".inst 0x83a00000\n"
        ".inst 0x8a00000d\n"
        ".inst 0xe59f2034\n"
        ".inst 0xe0803100\n"
        ".inst 0xe0830180\n"
        ".inst 0xe5922004\n"
        ".inst 0xe0820100\n"
        ".inst 0xe2800903\n"
        ".inst 0xe2800f7e\n"
        ".inst 0xec900a08\n"
        ".inst 0xe2800020\n"
        ".inst 0xec810a08\n"
        ".inst 0xe2811020\n"
        ".inst 0xec900a05\n"
        ".inst 0xe3a00001\n"
        ".inst 0xec810a05\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043e2a8\n"
    );
}

// DECOMP_FUNC(0x0029e3d0, 76)
extern "C" __attribute__((naked)) void camp_func_0029e3d0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0040\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe5904004\n"
        ".inst 0xe3a0004b\n"
        ".inst 0xe5d4174c\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000009\n"
        ".inst 0xe2840b01\n"
        ".inst 0xe2800fe2\n"
        ".inst 0xe1a05000\n"
        ".inst 0xeb000398\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb00038f\n"
        ".inst 0xe0800006\n"
        ".inst 0xe0800004\n"
        ".inst 0xe5d00758\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0043dd20\n"
    );
}
