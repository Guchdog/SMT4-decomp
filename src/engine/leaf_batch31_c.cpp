#include "types.h"

// Batch 31 C: exact ARM bytes; post-return literal words are preserved as data.

// DECOMP_FUNC(0x00201040, 168)
extern "C" __attribute__((naked)) void battle_func_00201040() {
    asm volatile(".arm\n.inst 0xe59f009c\n.inst 0xe92d4070\n.inst 0xe5905000\n.inst 0xe3550000\n.inst 0x0a000022\n.inst 0xe595002c\n.inst 0xe3a04000\n.inst 0xe3500000\n.inst 0xda000011\n.inst 0xe0856104\n.inst 0xe5960004\n.inst 0xeb02f8ea\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000007\n.inst 0xe5960004\n.inst 0xeb02d939\n.inst 0xe3500004\n.inst 0xe320f000\n.inst 0x0a000002\n.inst 0xe5960004\n.inst 0xe3a01001\n.inst 0xeb02d91c\n.inst 0xe595002c\n.inst 0xe2844001\n.inst 0xe1500004\n.inst 0xcaffffed\n.inst 0xe3a04000\n.inst 0xe0856104\n.inst 0xe5960034\n.inst 0xeb02f8d7\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000002\n.inst 0xe5960034\n.inst 0xe3a01001\n.inst 0xeb02d8fb\n.inst 0xe2844001\n.inst 0xe354000a\n.inst 0xbafffff3\n.inst 0xe8bd8070\n.word 0x0043ded0\n");
}

// DECOMP_FUNC(0x002010e8, 164)
extern "C" __attribute__((naked)) void camp_func_002010e8() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe1a09000\n.inst 0xeb014d73\n.inst 0xe1a06000\n.inst 0xe3a01000\n.inst 0xe1a00009\n.inst 0xeb02ac7b\n.inst 0xe1a04000\n.inst 0xeb02ff63\n.inst 0xe1a05000\n.inst 0xe1a00004\n.inst 0xeb02ff4c\n.inst 0xe2508000\n.inst 0xe3a07000\n.inst 0x9a000018\n.inst 0xe5d5002a\n.inst 0xe3500000\n.inst 0x0a000011\n.inst 0xe3560001\n.inst 0xe3a04001\n.inst 0x9a00000e\n.inst 0xe1a01004\n.inst 0xe1a00009\n.inst 0xeb02ac6a\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xeb02ff51\n.inst 0xe5900000\n.inst 0xe1d512f0\n.inst 0xe1500001\n.inst 0x1a000001\n.inst 0xe5c5402a\n.inst 0xea000002\n.inst 0xe2844001\n.inst 0xe1560004\n.inst 0x8afffff0\n.inst 0xe2877001\n.inst 0xe1570008\n.inst 0xe285502c\n.inst 0x3affffe6\n.inst 0xe8bd87f0\n");
}

// DECOMP_FUNC(0x0020118c, 168)
extern "C" __attribute__((naked)) void script_vm_func_0020118c() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a00019\n.inst 0xeb02ce0f\n.inst 0xeb014d49\n.inst 0xe1a06000\n.inst 0xe3a01000\n.inst 0xe3a00019\n.inst 0xeb02ff45\n.inst 0xe1a04000\n.inst 0xeb02ff39\n.inst 0xe1a05000\n.inst 0xe1a00004\n.inst 0xeb02ff22\n.inst 0xe2508000\n.inst 0xe3a07000\n.inst 0x9a000018\n.inst 0xe5d5002a\n.inst 0xe3500000\n.inst 0x0a000011\n.inst 0xe3560001\n.inst 0xe3a04001\n.inst 0x9a00000e\n.inst 0xe1a01004\n.inst 0xe3a00019\n.inst 0xeb02ff34\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xeb02ff27\n.inst 0xe5900000\n.inst 0xe1d512f0\n.inst 0xe1500001\n.inst 0x1a000001\n.inst 0xe5c5402a\n.inst 0xea000002\n.inst 0xe2844001\n.inst 0xe1560004\n.inst 0x8afffff0\n.inst 0xe2877001\n.inst 0xe1570008\n.inst 0xe285502c\n.inst 0x3affffe6\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x00212394, 168)
extern "C" __attribute__((naked)) void ui_func_00212394() {
    asm volatile(".arm\n.inst 0xee001a10\n.inst 0xec901a04\n.inst 0xee002a90\n.inst 0xe1a0c003\n.inst 0xe59d3000\n.inst 0xe1a0200c\n.inst 0xee311a02\n.inst 0xeeb80ac0\n.inst 0xee711aa2\n.inst 0xeef80ae0\n.inst 0xee310a00\n.inst 0xee311aa0\n.inst 0xeefd0ac0\n.inst 0xeebd0ac1\n.inst 0xee100a90\n.inst 0xee101a10\n.inst 0xe1a00000\n.inst 0xe92d40f0\n.inst 0xe1a05000\n.inst 0xe24dd00c\n.inst 0xe5d30000\n.inst 0xe1a06001\n.inst 0xe1a07002\n.inst 0xe3500000\n.inst 0xe1a04003\n.inst 0x0a00000c\n.inst 0xe1d400d0\n.inst 0xe3500020\n.inst 0x0a000005\n.inst 0xe2402030\n.inst 0xe1a03005\n.inst 0xe3a0100d\n.inst 0xe3a00002\n.inst 0xe1cd60f0\n.inst 0xeb02b40f\n.inst 0xe5f40001\n.inst 0xe2855007\n.inst 0xe3500000\n.inst 0x1afffff2\n.inst 0xe28dd00c\n.inst 0xe8bd80f0\n.inst 0xe12fff1e\n");
}

// DECOMP_FUNC(0x002143cc, 160)
extern "C" __attribute__((naked)) void script_vm_func_002143cc() {
    asm volatile(".arm\n.inst 0xe92d4038\n.inst 0xe3a00000\n.inst 0xeb020ae1\n.inst 0xe6ff5070\n.inst 0xeb01d497\n.inst 0xe3500000\n.inst 0x1a000007\n.inst 0xe3a01000\n.inst 0xe1a00001\n.inst 0xeb010047\n.inst 0xe3a02001\n.inst 0xe3a01000\n.inst 0xe1a00005\n.inst 0xeb01eaf6\n.inst 0xeb02af47\n.inst 0xe3a0001e\n.inst 0xeb028171\n.inst 0xe1a04000\n.inst 0xe3a00000\n.inst 0xeb010037\n.inst 0xe3a01000\n.inst 0xe1a02000\n.inst 0xe58d1000\n.inst 0xe3a03006\n.inst 0xe3a01010\n.inst 0xe1a00004\n.inst 0xeb01030c\n.inst 0xe1a04000\n.inst 0xe3a00000\n.inst 0xeb01002d\n.inst 0xe2801001\n.inst 0xe3a00000\n.inst 0xeb010030\n.inst 0xe3540001\n.inst 0x13a00000\n.inst 0x1a000002\n.inst 0xe1a00005\n.inst 0xeb04d203\n.inst 0xe3a00001\n.inst 0xe8bd8038\n");
}

// DECOMP_FUNC(0x00219570, 180)
extern "C" __attribute__((naked)) void func_00219570() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a04000\n.inst 0xe1a05001\n.inst 0xe5900000\n.inst 0xeb0254a4\n.inst 0xe1a08000\n.inst 0xe5950000\n.inst 0xeb0254a1\n.inst 0xe1a07000\n.inst 0xe5940000\n.inst 0xeb01a5a9\n.inst 0xe1a06000\n.inst 0xe5950000\n.inst 0xeb01a5a6\n.inst 0xe3560002\n.inst 0x0a000003\n.inst 0xe3500002\n.inst 0x03e00000\n.inst 0x0a00000f\n.inst 0xea000002\n.inst 0xe3500002\n.inst 0x13a00001\n.inst 0x1a00000b\n.inst 0xe1d702b6\n.inst 0xe1d812b6\n.inst 0xe0500001\n.inst 0x1a000007\n.inst 0xe5940000\n.inst 0xeb02548c\n.inst 0xe1a04000\n.inst 0xe5950000\n.inst 0xeb025489\n.inst 0xe1d002b4\n.inst 0xe1d412b4\n.inst 0xe0400001\n.inst 0xe8bd81f0\n.inst 0xe1a02000\n.inst 0xe1d100b2\n.inst 0xe1d230b2\n.inst 0xe0500003\n.inst 0x1a000002\n.inst 0xe1d200b0\n.inst 0xe1d110b0\n.inst 0xe0400001\n.inst 0xe12fff1e\n");
}

// DECOMP_FUNC(0x0021a0a8, 172)
extern "C" __attribute__((naked)) void engine_func_0021a0a8() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe1a04001\n.inst 0xed2d8b02\n.inst 0xeeb08a40\n.inst 0xe24dd058\n.inst 0xe28d6018\n.inst 0xe1b01002\n.inst 0xe1a00006\n.inst 0x0a000001\n.inst 0xeb00d884\n.inst 0xea000001\n.inst 0xe320f000\n.inst 0xeb00f2d6\n.inst 0xee180a10\n.inst 0xe35005fe\n.inst 0x0a000006\n.inst 0xed8d8a04\n.inst 0xed8d8a03\n.inst 0xed8d8a02\n.inst 0xe3a02002\n.inst 0xe28d1008\n.inst 0xe1a00006\n.inst 0xeb00d7ff\n.inst 0xe3540000\n.inst 0x0a000009\n.inst 0xe5940000\n.inst 0xe3a02002\n.inst 0xe28d1008\n.inst 0xe58d0008\n.inst 0xe5940004\n.inst 0xe58d000c\n.inst 0xe5940008\n.inst 0xe58d0010\n.inst 0xe1a00006\n.inst 0xeb00d7a0\n.inst 0xe3a02000\n.inst 0xe28d1018\n.inst 0xe2850010\n.inst 0xeb00d777\n.inst 0xe28dd058\n.inst 0xecbd8b02\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x0021bd04, 160)
extern "C" __attribute__((naked)) void script_vm_func_0021bd04() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a00000\n.inst 0xe59f7084\n.inst 0xeb00ce87\n.inst 0xe3500000\n.inst 0x0a00001d\n.inst 0xe59f0078\n.inst 0xe3a01b01\n.inst 0xeb02a381\n.inst 0xeb00ce73\n.inst 0xe2505000\n.inst 0xc59f6068\n.inst 0xc59f8060\n.inst 0xe3a01000\n.inst 0xe1a04001\n.inst 0xe5871004\n.inst 0xda000012\n.inst 0xe1a00004\n.inst 0xeb00ce78\n.inst 0xe1d010d0\n.inst 0xe3710001\n.inst 0x0a00000a\n.inst 0xe5962000\n.inst 0xe1510002\n.inst 0x1a000007\n.inst 0xe5961004\n.inst 0xe1d000d1\n.inst 0xe1500001\n.inst 0x1a000003\n.inst 0xe5970004\n.inst 0xe2801001\n.inst 0xe7884100\n.inst 0xe5871004\n.inst 0xe2844001\n.inst 0xe1540005\n.inst 0xbaffffec\n.inst 0xe8bd81f0\n.word 0x00447600\n.word 0x004a0be4\n.word 0x0049f91c\n");
}

// DECOMP_FUNC(0x0021de1c, 164)
extern "C" __attribute__((naked)) void script_vm_func_0021de1c() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3e05000\n.inst 0xe3a04000\n.inst 0xe59f6084\n.inst 0xe59f7084\n.inst 0xe59f8084\n.inst 0xe0841104\n.inst 0xe5970000\n.inst 0xe0800181\n.inst 0xe5f0101c\n.inst 0xe3510000\n.inst 0x0a00000d\n.inst 0xe1d011b6\n.inst 0xe351000f\n.inst 0x1a00000a\n.inst 0xe2800004\n.inst 0xecd01a03\n.inst 0xe5980000\n.inst 0xe280001c\n.inst 0xec900a03\n.inst 0xeb01a7b8\n.inst 0xeebd0ac0\n.inst 0xee100a10\n.inst 0xe1500006\n.inst 0xb1a06000\n.inst 0xb1a05004\n.inst 0xe2844001\n.inst 0xe3540018\n.inst 0xbaffffe8\n.inst 0xe3750001\n.inst 0x0a000005\n.inst 0xe5970000\n.inst 0xe0852105\n.inst 0xe3a01001\n.inst 0xe0800182\n.inst 0xe1c013b0\n.inst 0xe5c0101d\n.inst 0xe8bd81f0\n.word 0x0001869f\n.word 0x00447a48\n.word 0x00447e88\n");
}

// DECOMP_FUNC(0x0021dec0, 156)
extern "C" __attribute__((naked)) void script_vm_func_0021dec0() {
    asm volatile(".arm\n.inst 0xe59f1090\n.inst 0xe92d0030\n.inst 0xe3a00000\n.inst 0xe1a02000\n.inst 0xe591c000\n.inst 0xe3a03080\n.inst 0xe3a04006\n.inst 0xe3a05001\n.inst 0xe5cc0017\n.inst 0xe3a00065\n.inst 0xe0000092\n.inst 0xe08c0100\n.inst 0xe5d011d0\n.inst 0xe3510000\n.inst 0x159011e4\n.inst 0x1351001d\n.inst 0x0a00000f\n.inst 0xe3510026\n.inst 0x1351001e\n.inst 0x0a00000c\n.inst 0xe351001f\n.inst 0x13510025\n.inst 0x0a000009\n.inst 0xe59011d4\n.inst 0xe3510008\n.inst 0x1351000a\n.inst 0x0a000003\n.inst 0xe351000c\n.inst 0x1351000e\n.inst 0x13510010\n.inst 0x1a000001\n.inst 0xe2800f75\n.inst 0xe8800030\n.inst 0xe2533001\n.inst 0xe2822001\n.inst 0x1affffe4\n.inst 0xe8bd0030\n.inst 0xe12fff1e\n.word 0x00447a78\n");
}

// DECOMP_FUNC(0x00221c60, 168)
extern "C" __attribute__((naked)) void battle_func_00221c60() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe59f5098\n.inst 0xe5951000\n.inst 0xe3510000\n.inst 0x0a000012\n.inst 0xe3500000\n.inst 0xe3a04000\n.inst 0xe5c1005c\n.inst 0x0a00000f\n.inst 0xe5950000\n.inst 0xe0800104\n.inst 0xe5900034\n.inst 0xeb0275e1\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000004\n.inst 0xe5950000\n.inst 0xe3a01001\n.inst 0xe0800104\n.inst 0xe5900034\n.inst 0xeb02da36\n.inst 0xe2844001\n.inst 0xe354000a\n.inst 0xbafffff0\n.inst 0xe8bd8070\n.inst 0xe5950000\n.inst 0xe0800104\n.inst 0xe5900034\n.inst 0xeb0275d1\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000004\n.inst 0xe5950000\n.inst 0xe3a01000\n.inst 0xe0800104\n.inst 0xe5900034\n.inst 0xeb02da26\n.inst 0xe2844001\n.inst 0xe354000a\n.inst 0xbafffff0\n.inst 0xe8bd8070\n.word 0x0043ded0\n");
}

// DECOMP_FUNC(0x0022a210, 160)
extern "C" __attribute__((naked)) void script_vm_func_0022a210() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe59f008c\n.inst 0xe3a05000\n.inst 0xe5900000\n.inst 0xe5902754\n.inst 0xe2021010\n.inst 0xe3c22070\n.inst 0xe1b01221\n.inst 0xe5802754\n.inst 0x0a000012\n.inst 0xe5940008\n.inst 0xe3a01001\n.inst 0xe5841000\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb026842\n.inst 0xe5845008\n.inst 0xe594000c\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb02683d\n.inst 0xe584500c\n.inst 0xe5940010\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb026838\n.inst 0xe5845010\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.inst 0xe5940010\n.inst 0xe594100c\n.inst 0xeb01b418\n.inst 0xe3a01002\n.inst 0xe5840014\n.inst 0xe5801108\n.inst 0xe3a00000\n.inst 0xe5845000\n.inst 0xe8bd8070\n.word 0x00432fc8\n");
}

// DECOMP_FUNC(0x0022a76c, 184)
extern "C" __attribute__((naked)) void battle_func_0022a76c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe24dd010\n.inst 0xe1a06000\n.inst 0xe1a05001\n.inst 0xe1a04002\n.inst 0xeb01a544\n.inst 0xe59f1094\n.inst 0xe7911000\n.inst 0xe3110040\n.inst 0x03110c01\n.inst 0x13a00000\n.inst 0x1a00001e\n.inst 0xe3550000\n.inst 0x0a000009\n.inst 0xe2801a02\n.inst 0xe3a0000d\n.inst 0xe5913230\n.inst 0xe58d0008\n.inst 0xe1a02006\n.inst 0xe3a01000\n.inst 0xe3a00001\n.inst 0xe58d4004\n.inst 0xe58d5000\n.inst 0xea000011\n.inst 0xe320f000\n.inst 0xeb01a530\n.inst 0xe2802901\n.inst 0xe2822e4a\n.inst 0xe1a01000\n.inst 0xe5922000\n.inst 0xe3a00000\n.inst 0xe3120040\n.inst 0x03120c01\n.inst 0x1a000008\n.inst 0xe2812a02\n.inst 0xe3e01000\n.inst 0xe5923230\n.inst 0xe58d1008\n.inst 0xe3a01000\n.inst 0xe88d0011\n.inst 0xe1a02006\n.inst 0xe1a00001\n.inst 0xebffff89\n.inst 0xe28dd010\n.inst 0xe8bd8070\n.word 0x000044a0\n");
}

// DECOMP_FUNC(0x0022b858, 180)
extern "C" __attribute__((naked)) void engine_func_0022b858() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe3a00000\n.inst 0xe5c50631\n.inst 0xe5c50632\n.inst 0xe5850c58\n.inst 0xe5850c5c\n.inst 0xe1a04000\n.inst 0xe5850cb8\n.inst 0xe0640184\n.inst 0xe3a02000\n.inst 0xe0800100\n.inst 0xe1a01002\n.inst 0xe0850100\n.inst 0xe2800b01\n.inst 0xe2800f95\n.inst 0xeb020fed\n.inst 0xe2844001\n.inst 0xe354000a\n.inst 0xbafffff4\n.inst 0xe3a01000\n.inst 0xe28500a8\n.inst 0xeb001ec7\n.inst 0xe3a01001\n.inst 0xe28500a8\n.inst 0xeb001ec4\n.inst 0xe1a00005\n.inst 0xe320f000\n.inst 0xeb001fb4\n.inst 0xe0850100\n.inst 0xe5900530\n.inst 0xe1d005ba\n.inst 0xe2801001\n.inst 0xe2802002\n.inst 0xe0854001\n.inst 0xe5851c64\n.inst 0xe5852c60\n.inst 0xe5d40c78\n.inst 0xe3500000\n.inst 0x1a000003\n.inst 0xe3a0002a\n.inst 0xeb01ea44\n.inst 0xe3a00001\n.inst 0xe5c40c78\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x0022cc38, 180)
extern "C" __attribute__((naked)) void func_0022cc38() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3510064\n.inst 0xe1a04001\n.inst 0xba000011\n.inst 0xe59f1090\n.inst 0xe59f3090\n.inst 0xe3a00000\n.inst 0xe0802200\n.inst 0xe0812082\n.inst 0xe1d220f0\n.inst 0xe3720001\n.inst 0x0a00001a\n.inst 0xe1520004\n.inst 0x1a000003\n.inst 0xe0800200\n.inst 0xe0810080\n.inst 0xe2800002\n.inst 0xe8bd8070\n.inst 0xe2800001\n.inst 0xe1530000\n.inst 0xcafffff1\n.inst 0xea000010\n.inst 0xe3a05000\n.inst 0xeb008ad3\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0xda00000b\n.inst 0xe1a00005\n.inst 0xeb008abe\n.inst 0xe1d012f0\n.inst 0xe3710001\n.inst 0x0a000006\n.inst 0xe1510004\n.inst 0x0affffee\n.inst 0xe2855001\n.inst 0xeb008ac7\n.inst 0xe1500005\n.inst 0xe320f000\n.inst 0xcafffff3\n.inst 0xe59f000c\n.inst 0xe5900004\n.inst 0xe8bd8070\n.word 0x0044ce08\n.word 0x000003e7\n.word 0x0044cdf0\n");
}

// DECOMP_FUNC(0x0022e4e8, 164)
extern "C" __attribute__((naked)) void camp_func_0022e4e8() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe1d104b6\n.inst 0xe1a05001\n.inst 0xe1a06002\n.inst 0xeb022b98\n.inst 0xe0801086\n.inst 0xe1d400b0\n.inst 0xe1d126bc\n.inst 0xe2000b3f\n.inst 0xe3c22b3f\n.inst 0xe1800002\n.inst 0xe1c400b0\n.inst 0xe1d116bc\n.inst 0xe3c00b3f\n.inst 0xe2011b3f\n.inst 0xe1800001\n.inst 0xe1c400b0\n.inst 0xe1b01b00\n.inst 0x1a000002\n.inst 0xe2000b3f\n.inst 0xe3800001\n.inst 0xe1c400b0\n.inst 0xe1a01006\n.inst 0xe2850034\n.inst 0xebff18e8\n.inst 0xe1a05000\n.inst 0xe1d400b0\n.inst 0xe1a01005\n.inst 0xe1a00520\n.inst 0xeb01ab5c\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000005\n.inst 0xe1d400b0\n.inst 0xe3a01b3f\n.inst 0xe0011505\n.inst 0xe3c00b3f\n.inst 0xe1800001\n.inst 0xe1c400b0\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002303c8, 164)
extern "C" __attribute__((naked)) void engine_func_002303c8() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xeb016fb4\n.inst 0xe5940010\n.inst 0xe3500001\n.inst 0x03a00003\n.inst 0x13a00007\n.inst 0xeb01a7f6\n.inst 0xe3a00000\n.inst 0xeb018ad4\n.inst 0xeb0218bd\n.inst 0xe1a05000\n.inst 0xe3a00001\n.inst 0xeb01b0d9\n.inst 0xe1a00005\n.inst 0xeb01a7de\n.inst 0xe1a00005\n.inst 0xeb01a7d5\n.inst 0xe59f004c\n.inst 0xe3a01001\n.inst 0xe7801004\n.inst 0xe1a00001\n.inst 0xeb0000b1\n.inst 0xe3a00000\n.inst 0xeb0000d3\n.inst 0xe2845b57\n.inst 0xe2855f52\n.inst 0xe5950000\n.inst 0xe3500000\n.inst 0x1a000003\n.inst 0xe59f0020\n.inst 0xe3a01007\n.inst 0xeb01a7a0\n.inst 0xe5850000\n.inst 0xe2844b57\n.inst 0xe2844f4a\n.inst 0xe3a00000\n.inst 0xe5840000\n.inst 0xe8bd8070\n.word 0x00015d24\n.word 0x00407738\n");
}

// DECOMP_FUNC(0x00233804, 168)
extern "C" __attribute__((naked)) void unite_func_00233804() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe1a04000\n.inst 0xe1a08001\n.inst 0xe3a09000\n.inst 0xe980000e\n.inst 0xe3e00000\n.inst 0xe1c401b4\n.inst 0xe5c49011\n.inst 0xe5c49012\n.inst 0xe1d403f0\n.inst 0xe1a07002\n.inst 0xe1a06003\n.inst 0xe3500000\n.inst 0xc3a05000\n.inst 0xe1c491b6\n.inst 0xda00000a\n.inst 0xe320f000\n.inst 0xeb0215ee\n.inst 0xe1d403f0\n.inst 0xe2855001\n.inst 0xe1500005\n.inst 0xcafffff9\n.inst 0xe3e02000\n.inst 0xe3a01018\n.inst 0xe2840018\n.inst 0xe1c493b0\n.inst 0xeb0242f7\n.inst 0xe3560000\n.inst 0xe3a05000\n.inst 0xda00000a\n.inst 0xe0871005\n.inst 0xe1a00008\n.inst 0xeb02140e\n.inst 0xe0841085\n.inst 0xe2855001\n.inst 0xe1c101b8\n.inst 0xe1d403b0\n.inst 0xe1560005\n.inst 0xe2800001\n.inst 0xe1c403b0\n.inst 0xcafffff4\n.inst 0xe8bd87f0\n");
}

// DECOMP_FUNC(0x00237738, 172)
extern "C" __attribute__((naked)) void func_00237738() {
    asm volatile(".arm\n.inst 0xe5803004\n.inst 0xe59f309c\n.inst 0xe5801008\n.inst 0xe3a01000\n.inst 0xe580100c\n.inst 0xe5803000\n.inst 0xe5801010\n.inst 0xe5801014\n.inst 0xe590c018\n.inst 0xe5801018\n.inst 0xe580201c\n.inst 0xe5801020\n.inst 0xe5801024\n.inst 0xe5801028\n.inst 0xe590302c\n.inst 0xe5801030\n.inst 0xe2033103\n.inst 0xe3c33103\n.inst 0xe580302c\n.inst 0xe5801034\n.inst 0xe5801038\n.inst 0xe590303c\n.inst 0xe5801040\n.inst 0xe2033103\n.inst 0xe3c33103\n.inst 0xe580303c\n.inst 0xe5801044\n.inst 0xe5801048\n.inst 0xe590304c\n.inst 0xe5801050\n.inst 0xe2033103\n.inst 0xe3c33103\n.inst 0xe580304c\n.inst 0xe5801054\n.inst 0xe5801058\n.inst 0xe590305c\n.inst 0xe5801060\n.inst 0xe2033103\n.inst 0xe3c33103\n.inst 0xe580305c\n.inst 0xe5c01064\n.inst 0xe12fff1e\n.word 0x00421500\n");
}

// DECOMP_FUNC(0x00238b30, 184)
extern "C" __attribute__((naked)) void func_00238b30() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a06000\n.inst 0xe0827003\n.inst 0xe1520007\n.inst 0xe1a05001\n.inst 0xe1a04002\n.inst 0x2a000024\n.inst 0xe5961000\n.inst 0xe5950000\n.inst 0xe0811084\n.inst 0xe1d110b0\n.inst 0xe1d000ba\n.inst 0xe1510000\n.inst 0x0a000017\n.inst 0xeb00001e\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000012\n.inst 0xe1d010b2\n.inst 0xe3510000\n.inst 0x0a00000e\n.inst 0xe5962000\n.inst 0xe0822084\n.inst 0xe1d220b0\n.inst 0xe1520001\n.inst 0x0a00000b\n.inst 0xe1d010b4\n.inst 0xe3510000\n.inst 0x0a000006\n.inst 0xe1520001\n.inst 0x0a000006\n.inst 0xe1d000b6\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xe1520000\n.inst 0x0a000001\n.inst 0xe3a00000\n.inst 0xe8bd81f0\n.inst 0xe5950000\n.inst 0xe2844001\n.inst 0xe1540007\n.inst 0xe5900004\n.inst 0xe5850000\n.inst 0x3affffda\n.inst 0xe3a00001\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x0023963c, 188)
extern "C" __attribute__((naked)) void engine_func_0023963c() {
    asm volatile(".arm\n.inst 0xe3510000\n.inst 0xe92d4070\n.inst 0xe24dd008\n.inst 0xe0801102\n.inst 0x0a00001d\n.inst 0xe59033c0\n.inst 0xe1530002\n.inst 0x9a000023\n.inst 0xe590c560\n.inst 0xe15c0003\n.inst 0x159103cc\n.inst 0x1a000014\n.inst 0xe1a04000\n.inst 0xe0800182\n.inst 0xe2801b01\n.inst 0xe2811f59\n.inst 0xe1a0000d\n.inst 0xebfffde4\n.inst 0xe1a06000\n.inst 0xe59403c0\n.inst 0xe3a05000\n.inst 0xe3500000\n.inst 0x9a000014\n.inst 0xe0840105\n.inst 0xe59003cc\n.inst 0xe2801020\n.inst 0xe1a00006\n.inst 0xeb069dc3\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000008\n.inst 0xe0840105\n.inst 0xe59003cc\n.inst 0xe28dd008\n.inst 0xe8bd8070\n.inst 0xe5900210\n.inst 0xe1500002\n.inst 0x8591021c\n.inst 0x8afffff9\n.inst 0xea000003\n.inst 0xe59403c0\n.inst 0xe2855001\n.inst 0xe1500005\n.inst 0x8affffea\n.inst 0xe28dd008\n.inst 0xe3a00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x0023abd4, 180)
extern "C" __attribute__((naked)) void engine_func_0023abd4() {
    asm volatile(".arm\n.inst 0xe5902004\n.inst 0xe5d0301c\n.inst 0xe5922010\n.inst 0xe3530000\n.inst 0x0a000006\n.inst 0xe5900008\n.inst 0xe590000c\n.inst 0xe2800014\n.inst 0xecd00a02\n.inst 0xeef80ae0\n.inst 0xeeb81ac1\n.inst 0xea00000c\n.inst 0xe1d232b4\n.inst 0xe1d2c2b6\n.inst 0xe2800010\n.inst 0xee003a90\n.inst 0xee01ca10\n.inst 0xec902a02\n.inst 0xeddf1a17\n.inst 0xeef80a60\n.inst 0xeeb81a41\n.inst 0xeeb02ac2\n.inst 0xeef02ae2\n.inst 0xee420a21\n.inst 0xee021aa1\n.inst 0xeef40ac1\n.inst 0xeef1fa10\n.inst 0xcdc10a01\n.inst 0xcdc10a00\n.inst 0xdef00a41\n.inst 0xdd811a01\n.inst 0xdd811a00\n.inst 0xed9f1a0a\n.inst 0xee600a80\n.inst 0xedc10a00\n.inst 0xedc10a01\n.inst 0xe1d202b4\n.inst 0xee000a90\n.inst 0xeef80a60\n.inst 0xee200a80\n.inst 0xee200a01\n.inst 0xed810a02\n.inst 0xe12fff1e\n.word 0x40000000\n.word 0x3f000000\n");
}

// DECOMP_FUNC(0x0023bc5c, 160)
extern "C" __attribute__((naked)) void func_0023bc5c() {
    asm volatile(".arm\n.inst 0xe92d00f0\n.inst 0xe3a03001\n.inst 0xe5d20008\n.inst 0xe59f6080\n.inst 0xe3500000\n.inst 0xe59f0074\n.inst 0x13a05000\n.inst 0x03a05102\n.inst 0xe2464038\n.inst 0xe590c000\n.inst 0xe5920000\n.inst 0xe8810048\n.inst 0xe26cc000\n.inst 0xe080c18c\n.inst 0xe2810008\n.inst 0xe185700c\n.inst 0xe4807004\n.inst 0xe59fc04c\n.inst 0xe4804004\n.inst 0xe5922004\n.inst 0xe0845003\n.inst 0xe3a01000\n.inst 0xe4802004\n.inst 0xe1844183\n.inst 0xe4805004\n.inst 0xe0842083\n.inst 0xe8a01002\n.inst 0xe8a00018\n.inst 0xe8a01008\n.inst 0xe4803004\n.inst 0xe4802004\n.inst 0xe59f2018\n.inst 0xe8a00006\n.inst 0xe8a00006\n.inst 0xe8bd00f0\n.inst 0xe12fff1e\n.word 0x0044e670\n.word 0x000f025f\n.word 0x00010245\n.word 0x0008025e\n");
}

// DECOMP_FUNC(0x0023c4c4, 192)
extern "C" __attribute__((naked)) void battle_func_0023c4c4() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe1a06001\n.inst 0xe1a08003\n.inst 0xe1a03001\n.inst 0xe59f90a4\n.inst 0xe6bf1070\n.inst 0xed2d8b02\n.inst 0xe1a07000\n.inst 0xe1a05002\n.inst 0xe59da028\n.inst 0xe59d4034\n.inst 0xe5990000\n.inst 0xeddd8a0b\n.inst 0xed9d8a0c\n.inst 0xe3a02000\n.inst 0xebffa989\n.inst 0xe3540000\n.inst 0x1a000002\n.inst 0xe5d01005\n.inst 0xe3811004\n.inst 0xe5c01005\n.inst 0xe3a01021\n.inst 0xe5c01004\n.inst 0xe5805014\n.inst 0xedc08a0a\n.inst 0xe580804c\n.inst 0xe087000a\n.inst 0xe3a08000\n.inst 0xe6bf1070\n.inst 0xe5990000\n.inst 0xe1a03006\n.inst 0xe1a02008\n.inst 0xebffa978\n.inst 0xe3540000\n.inst 0xe320f000\n.inst 0x1a000002\n.inst 0xe5d01005\n.inst 0xe3811004\n.inst 0xe5c01005\n.inst 0xe3a01022\n.inst 0xe5805014\n.inst 0xe5c01004\n.inst 0xed808a0a\n.inst 0xe580804c\n.inst 0xe3a00001\n.inst 0xecbd8b02\n.inst 0xe8bd87f0\n.word 0x00434290\n");
}

// DECOMP_FUNC(0x0023e590, 164)
extern "C" __attribute__((naked)) void camp_func_0023e590() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe5d00022\n.inst 0xe1a04001\n.inst 0xe1a06002\n.inst 0xe3500000\n.inst 0xe5950038\n.inst 0x0a000007\n.inst 0xe2801057\n.inst 0xe3a00019\n.inst 0xeb020444\n.inst 0xe1d010f8\n.inst 0xe5841000\n.inst 0xe1d000fa\n.inst 0xe5860000\n.inst 0xe8bd8070\n.inst 0xe350000f\n.inst 0xc240000c\n.inst 0xe280102d\n.inst 0xe3a00019\n.inst 0xeb02043a\n.inst 0xe1d010f8\n.inst 0xe5841000\n.inst 0xe1d000fa\n.inst 0xe5860000\n.inst 0xe595003c\n.inst 0xe3500000\n.inst 0xe5950038\n.inst 0x0a000006\n.inst 0xe2400004\n.inst 0xe350000b\n.inst 0x95940000\n.inst 0x92400e19\n.inst 0x8affffec\n.inst 0xe5840000\n.inst 0xe8bd8070\n.inst 0xe350000f\n.inst 0xc5940000\n.inst 0xc2800e19\n.inst 0xcafffff9\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x00243234, 180)
extern "C" __attribute__((naked)) void ui_func_00243234() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a03001\n.inst 0xe59f50a0\n.inst 0xe1a04002\n.inst 0xe3a06000\n.inst 0xe595103c\n.inst 0xe3510000\n.inst 0x0a000018\n.inst 0xe5950040\n.inst 0xeb02d404\n.inst 0xe5950040\n.inst 0xe5900008\n.inst 0xe5840100\n.inst 0xe5950040\n.inst 0xe1a01004\n.inst 0xeb0380fa\n.inst 0xe58400fc\n.inst 0xe5950040\n.inst 0xeb0356dd\n.inst 0xe5840104\n.inst 0xe5950040\n.inst 0xe28410c8\n.inst 0xeb03844a\n.inst 0xe5940100\n.inst 0xe3500001\n.inst 0x1a000005\n.inst 0xe5950040\n.inst 0xeb001041\n.inst 0xe5856040\n.inst 0xe595003c\n.inst 0xeb00102e\n.inst 0xe585603c\n.inst 0xe8bd8070\n.inst 0xe1a01003\n.inst 0xe3a00000\n.inst 0xe585003c\n.inst 0xe320f000\n.inst 0xeb032ea2\n.inst 0xe3a0201c\n.inst 0xe3a010ba\n.inst 0xe5850040\n.inst 0xe8800006\n.inst 0xe5846100\n.inst 0xe8bd8070\n.word 0x0044ea80\n");
}

// DECOMP_FUNC(0x002432e8, 168)
extern "C" __attribute__((naked)) void ui_func_002432e8() {
    asm volatile(".arm\n.inst 0xe59f009c\n.inst 0xed2d8b04\n.inst 0xe2801c01\n.inst 0xe2800d05\n.inst 0xe2802018\n.inst 0xed910a01\n.inst 0xedd04a05\n.inst 0xed905a04\n.inst 0xedd10a02\n.inst 0xee604a24\n.inst 0xecd23a02\n.inst 0xe2802030\n.inst 0xee205a05\n.inst 0xec922a03\n.inst 0xee603a23\n.inst 0xe2802020\n.inst 0xee204a04\n.inst 0xecd25a04\n.inst 0xe2802008\n.inst 0xed911a00\n.inst 0xedd01a0f\n.inst 0xedd08a01\n.inst 0xed909a00\n.inst 0xee404a86\n.inst 0xecd27a02\n.inst 0xee403aa6\n.inst 0xee004a87\n.inst 0xee412a28\n.inst 0xee013a27\n.inst 0xee411a08\n.inst 0xee012a09\n.inst 0xee005aa5\n.inst 0xee341aa2\n.inst 0xee330a83\n.inst 0xee741a21\n.inst 0xee750a02\n.inst 0xed810a02\n.inst 0xedc11a03\n.inst 0xecc10a02\n.inst 0xecbd8b04\n.inst 0xe12fff1e\n.word 0x004ea81c\n");
}

// DECOMP_FUNC(0x0024558c, 164)
extern "C" __attribute__((naked)) void battle_func_0024558c() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe1a06001\n.inst 0xe1a08003\n.inst 0xe1a03001\n.inst 0xe59f9088\n.inst 0xe6bf1070\n.inst 0xed2d8b02\n.inst 0xe1a07002\n.inst 0xed9d8a0a\n.inst 0xe1cd42dc\n.inst 0xe5990000\n.inst 0xe3a02000\n.inst 0xebff855a\n.inst 0xe3a0102c\n.inst 0xe5c01004\n.inst 0xe5807014\n.inst 0xe5808028\n.inst 0xe3540000\n.inst 0xed808a13\n.inst 0xba000010\n.inst 0xeb0139ad\n.inst 0xe1d716f2\n.inst 0xeb00f56a\n.inst 0xe3500000\n.inst 0x0a00000b\n.inst 0xe3550000\n.inst 0xba000009\n.inst 0xe1a07000\n.inst 0xe6bf1074\n.inst 0xe5990000\n.inst 0xe1a03006\n.inst 0xe3a02000\n.inst 0xebff8546\n.inst 0xe3a01006\n.inst 0xe5c01004\n.inst 0xe5a07018\n.inst 0xe5805010\n.inst 0xe3a00001\n.inst 0xecbd8b02\n.inst 0xe8bd87f0\n.word 0x00434290\n");
}

// DECOMP_FUNC(0x002461ec, 180)
extern "C" __attribute__((naked)) void battle_func_002461ec() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a06003\n.inst 0xe59f30a0\n.inst 0xe59d5010\n.inst 0xe593c000\n.inst 0xe59c3008\n.inst 0xe3530000\n.inst 0x0a000002\n.inst 0xe593300c\n.inst 0xe3530000\n.inst 0x1afffffc\n.inst 0xe1a03002\n.inst 0xe6bf2071\n.inst 0xe6bf1070\n.inst 0xe1a0000c\n.inst 0xebff823f\n.inst 0xe1a04000\n.inst 0xe3a00007\n.inst 0xe5c40004\n.inst 0xe5845028\n.inst 0xe5846014\n.inst 0xe1d606f2\n.inst 0xe3a01001\n.inst 0xeb003c52\n.inst 0xe2400001\n.inst 0xe3550004\n.inst 0xe1c402b4\n.inst 0x0a00000d\n.inst 0xe3550003\n.inst 0x0a000003\n.inst 0xe5d40005\n.inst 0xe3800004\n.inst 0xe5c40005\n.inst 0xea000007\n.inst 0xe320f000\n.inst 0xeb013686\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xeb013492\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x1afffff3\n.inst 0xe1a00004\n.inst 0xe8bd8070\n.word 0x00434290\n");
}

// DECOMP_FUNC(0x00246ab0, 168)
extern "C" __attribute__((naked)) void camp_func_00246ab0() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe3a01002\n.inst 0xe3a0002e\n.inst 0xeb01e8fe\n.inst 0xeb01e8df\n.inst 0xe3500000\n.inst 0xc3a08000\n.inst 0xda00001d\n.inst 0xe3a01002\n.inst 0xe3a0002e\n.inst 0xeb01e8f7\n.inst 0xe1a07000\n.inst 0xe320f000\n.inst 0xeb01e8ea\n.inst 0xe1a06000\n.inst 0xe1a00007\n.inst 0xeb01e8d3\n.inst 0xe1540000\n.inst 0x21a00008\n.inst 0x2a000002\n.inst 0xe0841084\n.inst 0xe0810184\n.inst 0xe0860100\n.inst 0xe1d012f0\n.inst 0xe3710001\n.inst 0x0a00000b\n.inst 0xe1510005\n.inst 0x0a00000a\n.inst 0xe2844001\n.inst 0xe3a01002\n.inst 0xe3a0002e\n.inst 0xeb01e8e2\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xeb01e8c1\n.inst 0xe1500004\n.inst 0xe320f000\n.inst 0xcaffffe1\n.inst 0xe3a00000\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x00247170, 164)
extern "C" __attribute__((naked)) void battle_func_00247170() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe5900000\n.inst 0xe3100010\n.inst 0x03a04000\n.inst 0x0a00000c\n.inst 0xe2850c02\n.inst 0xe1d012f0\n.inst 0xe3510002\n.inst 0x13510003\n.inst 0x1a00001b\n.inst 0xe1d002f2\n.inst 0xeb019c92\n.inst 0xe3500000\n.inst 0x0a000017\n.inst 0xebfe9c7e\n.inst 0xe3500000\n.inst 0x0a000014\n.inst 0xea00000e\n.inst 0xe0850184\n.inst 0xe2800c02\n.inst 0xe1d012f8\n.inst 0xe3510002\n.inst 0x13510003\n.inst 0x1a00000a\n.inst 0xe1d002fa\n.inst 0xeb019c84\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000005\n.inst 0xebfe9c6f\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000001\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe3540005\n.inst 0xbaffffeb\n.inst 0xe3a00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x00248650, 156)
extern "C" __attribute__((naked)) void ui_func_00248650() {
    asm volatile(".arm\n.inst 0xeddf0a23\n.inst 0xe52de004\n.inst 0xed2d8b02\n.inst 0xee608a20\n.inst 0xe24dd044\n.inst 0xeeb00a68\n.inst 0xeb01bb4d\n.inst 0xeeb08a40\n.inst 0xeeb00a68\n.inst 0xeb01bb64\n.inst 0xeef08a40\n.inst 0xe1a0000d\n.inst 0xeb00396d\n.inst 0xeeb10a68\n.inst 0xed8d8a05\n.inst 0xedcd8a06\n.inst 0xe59f0050\n.inst 0xed8d0a09\n.inst 0xed8d8a0a\n.inst 0xeddd3a07\n.inst 0xe2801d05\n.inst 0xec9d0a06\n.inst 0xedc08a56\n.inst 0xedc03a57\n.inst 0xec810a06\n.inst 0xe28d1020\n.inst 0xec910a02\n.inst 0xe28d102c\n.inst 0xecd11a05\n.inst 0xe2801e16\n.inst 0xed808a5a\n.inst 0xe2800f5b\n.inst 0xec810a02\n.inst 0xecc01a05\n.inst 0xe28dd044\n.inst 0xecbd8b02\n.inst 0xe49df004\n.word 0x4222f983\n.word 0x004ea81c\n");
}

// DECOMP_FUNC(0x0024f9e8, 172)
extern "C" __attribute__((naked)) void engine_func_0024f9e8() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe1a04001\n.inst 0xed2d8b02\n.inst 0xeeb08a40\n.inst 0xe24dd058\n.inst 0xe28d6018\n.inst 0xe1b01002\n.inst 0xe1a00006\n.inst 0x0a000001\n.inst 0xeb000234\n.inst 0xea000001\n.inst 0xe320f000\n.inst 0xeb001c86\n.inst 0xee180a10\n.inst 0xe35005fe\n.inst 0x0a000006\n.inst 0xed8d8a04\n.inst 0xed8d8a03\n.inst 0xed8d8a02\n.inst 0xe3a02002\n.inst 0xe28d1008\n.inst 0xe1a00006\n.inst 0xeb0001af\n.inst 0xe3540000\n.inst 0x0a000009\n.inst 0xe5940000\n.inst 0xe3a02002\n.inst 0xe28d1008\n.inst 0xe58d0008\n.inst 0xe5940004\n.inst 0xe58d000c\n.inst 0xe5940008\n.inst 0xe58d0010\n.inst 0xe1a00006\n.inst 0xeb000150\n.inst 0xe3a02000\n.inst 0xe28d1018\n.inst 0xe2850018\n.inst 0xeb000127\n.inst 0xe28dd058\n.inst 0xecbd8b02\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x00250800, 192)
extern "C" __attribute__((naked)) void battle_func_00250800() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a04002\n.inst 0xe1a07003\n.inst 0xe59f80a8\n.inst 0xe1a03001\n.inst 0xed2d8b02\n.inst 0xe6bf1070\n.inst 0xe59d5020\n.inst 0xe59d6028\n.inst 0xe5980000\n.inst 0xed9d8a09\n.inst 0xe3a02000\n.inst 0xebff58bd\n.inst 0xe3550000\n.inst 0x0a000015\n.inst 0xe5981000\n.inst 0xe5911008\n.inst 0xe3510000\n.inst 0x0a000011\n.inst 0xe5d13004\n.inst 0xe591200c\n.inst 0xe3530031\n.inst 0x1a00000b\n.inst 0xe1d130f0\n.inst 0xe1d0c0f0\n.inst 0xe153000c\n.inst 0x0591102c\n.inst 0x01510004\n.inst 0x1a000005\n.inst 0xe1d010f2\n.inst 0xe3510000\n.inst 0xba000002\n.inst 0xe3e01000\n.inst 0xe1c010b2\n.inst 0xea000001\n.inst 0xe1b01002\n.inst 0x1affffed\n.inst 0xe3a01031\n.inst 0xe5c01004\n.inst 0xe3570000\n.inst 0xe580402c\n.inst 0xed808a13\n.inst 0x13a01001\n.inst 0x15801028\n.inst 0xe1c062b4\n.inst 0xecbd8b02\n.inst 0xe8bd81f0\n.word 0x00434290\n");
}

// DECOMP_FUNC(0x002508c0, 160)
extern "C" __attribute__((naked)) void battle_func_002508c0() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a06000\n.inst 0xe1a07001\n.inst 0xe5920050\n.inst 0xe1a05002\n.inst 0xe3100001\n.inst 0x13100080\n.inst 0x0a00001b\n.inst 0xeb010cec\n.inst 0xe1d516f2\n.inst 0xeb00c8a9\n.inst 0xe1a04000\n.inst 0xe5900000\n.inst 0xe3a02001\n.inst 0xe1a01005\n.inst 0xe3800d09\n.inst 0xe5840000\n.inst 0xe59f004c\n.inst 0xe5900000\n.inst 0xeb00b751\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xe5940000\n.inst 0xe3100010\n.inst 0x1a00000a\n.inst 0xe59f0030\n.inst 0xe6bf1076\n.inst 0xe1a03007\n.inst 0xe3a05001\n.inst 0xe5900000\n.inst 0xe3a02000\n.inst 0xebff587a\n.inst 0xe3a01024\n.inst 0xe5c01004\n.inst 0xe5a04018\n.inst 0xe5805010\n.inst 0xe3a00001\n.inst 0xe8bd81f0\n.word 0x00435d48\n.word 0x00434290\n");
}

// DECOMP_FUNC(0x00258308, 156)
extern "C" __attribute__((naked)) void camp_func_00258308() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe24dd008\n.inst 0xe1a07001\n.inst 0xe1a04002\n.inst 0xe1a05003\n.inst 0xe1a08000\n.inst 0xeb01613f\n.inst 0xe1b06000\n.inst 0x0a000008\n.inst 0xe3a0100a\n.inst 0xeb011ac5\n.inst 0xe3500000\n.inst 0x1a000004\n.inst 0xe3a01002\n.inst 0xe1a00006\n.inst 0xeb011ac0\n.inst 0xe3500000\n.inst 0x0a00000c\n.inst 0xe1a00008\n.inst 0xeb011a6b\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000005\n.inst 0xe1a03007\n.inst 0xe3a0205a\n.inst 0xe3a01024\n.inst 0xe3a00002\n.inst 0xe1cd40f0\n.inst 0xeb019c38\n.inst 0xe28dd008\n.inst 0xe8bd81f0\n.inst 0xe1a03007\n.inst 0xe3a0205b\n.inst 0xe3a01024\n.inst 0xe3a00002\n.inst 0xe1cd40f0\n.inst 0xeb019c30\n.inst 0xe28dd008\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x0025a378, 188)
extern "C" __attribute__((naked)) void camp_func_0025a378() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1b04000\n.inst 0xe3a00001\n.inst 0xe1a07110\n.inst 0x13540002\n.inst 0x13540003\n.inst 0x1a000003\n.inst 0xeb0170d4\n.inst 0xe1d007b2\n.inst 0xe1100007\n.inst 0x1a00001c\n.inst 0xe3540000\n.inst 0x13540001\n.inst 0x0a000003\n.inst 0xe3540002\n.inst 0x13540003\n.inst 0x0a000008\n.inst 0xea00001a\n.inst 0xe320f000\n.inst 0xeb013994\n.inst 0xe1a06000\n.inst 0xe320f000\n.inst 0xeb01398c\n.inst 0xe2805a09\n.inst 0xe28550f0\n.inst 0xea000003\n.inst 0xe3a06003\n.inst 0xeb013987\n.inst 0xe2805a09\n.inst 0xe2855f42\n.inst 0xe3560000\n.inst 0xe3a04000\n.inst 0xda00000b\n.inst 0xe19500d4\n.inst 0xe3500000\n.inst 0xba000005\n.inst 0xeb013975\n.inst 0xe1d004b4\n.inst 0xe1100007\n.inst 0x0a000001\n.inst 0xe3a00001\n.inst 0xe8bd81f0\n.inst 0xe2844001\n.inst 0xe1540006\n.inst 0xbafffff3\n.inst 0xe3a00000\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x0025c1dc, 184)
extern "C" __attribute__((naked)) void func_0025c1dc() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe24dd010\n.inst 0xe59f60a4\n.inst 0xe596000c\n.inst 0xe5900004\n.inst 0xe3500000\n.inst 0x03e00000\n.inst 0x0a000022\n.inst 0xe1a0000d\n.inst 0xeb01a599\n.inst 0xe1cd00d0\n.inst 0xe1cd00f8\n.inst 0xe28d0008\n.inst 0xebffe101\n.inst 0xe1a05000\n.inst 0xe28d0008\n.inst 0xebffe0e8\n.inst 0xe1a04000\n.inst 0xe28d0008\n.inst 0xebffe0cf\n.inst 0xe1a02005\n.inst 0xe1a01004\n.inst 0xeb01313d\n.inst 0xe0800080\n.inst 0xe1a04180\n.inst 0xe28d0008\n.inst 0xeb061318\n.inst 0xe0800004\n.inst 0xe0600200\n.inst 0xe1a04100\n.inst 0xe28d0008\n.inst 0xeb06132d\n.inst 0xe0800004\n.inst 0xe0600200\n.inst 0xe1a04100\n.inst 0xe28d0008\n.inst 0xeb061343\n.inst 0xe596100c\n.inst 0xe0800004\n.inst 0xe5911004\n.inst 0xe1510000\n.inst 0x90400001\n.inst 0x83a00000\n.inst 0xe28dd010\n.inst 0xe8bd8070\n.word 0x0043e2a8\n");
}

// DECOMP_FUNC(0x002646d4, 160)
extern "C" __attribute__((naked)) void script_vm_func_002646d4() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe3a04000\n.inst 0xe59f8088\n.inst 0xe5980004\n.inst 0xe3500000\n.inst 0xc59f7080\n.inst 0xc3a09001\n.inst 0xda00001c\n.inst 0xe0640204\n.inst 0xe0800284\n.inst 0xe0875180\n.inst 0xe2856c01\n.inst 0xe5d50164\n.inst 0xe3500000\n.inst 0x1a000011\n.inst 0xe595012c\n.inst 0xe3500000\n.inst 0x0a00000e\n.inst 0xe1d606f0\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xeb01711e\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000006\n.inst 0xe1d606f2\n.inst 0xe3500000\n.inst 0x0a000004\n.inst 0xeb017117\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000000\n.inst 0xe5c59164\n.inst 0xe5980004\n.inst 0xe2844001\n.inst 0xe1540000\n.inst 0xbaffffe2\n.inst 0xe8bd87f0\n.word 0x00447a28\n.word 0x004a1264\n");
}

// DECOMP_FUNC(0x00264900, 192)
extern "C" __attribute__((naked)) void script_vm_func_00264900() {
    asm volatile(".arm\n.inst 0xe59f10b0\n.inst 0xe92d41f0\n.inst 0xe1a06000\n.inst 0xe3a00000\n.inst 0xe5915000\n.inst 0xe3a02001\n.inst 0xe3a01065\n.inst 0xe0010190\n.inst 0xe2800001\n.inst 0xe0851101\n.inst 0xe5f131d0\n.inst 0xe3530000\n.inst 0x15812008\n.inst 0xe3500080\n.inst 0xbafffff6\n.inst 0xe59f7078\n.inst 0xe3a04000\n.inst 0xe3a00001\n.inst 0xebfe050d\n.inst 0xe3560000\n.inst 0xe320f000\n.inst 0x0a000006\n.inst 0xe5970000\n.inst 0xe2801028\n.inst 0xedd01a13\n.inst 0xe2800034\n.inst 0xec910a03\n.inst 0xec902a03\n.inst 0xeb007171\n.inst 0xe2844001\n.inst 0xe3540003\n.inst 0xbafffff0\n.inst 0xe3a00000\n.inst 0xe3a02010\n.inst 0xe3a01065\n.inst 0xe0010190\n.inst 0xe2800001\n.inst 0xe0851101\n.inst 0xe5f131d0\n.inst 0xe3530000\n.inst 0x15913044\n.inst 0x13530000\n.inst 0xc5812044\n.inst 0xe3500080\n.inst 0xbafffff4\n.inst 0xe8bd81f0\n.word 0x00447a78\n.word 0x00447e88\n");
}

// DECOMP_FUNC(0x0026ac34, 172)
extern "C" __attribute__((naked)) void script_vm_func_0026ac34() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a0c000\n.inst 0xe1a05001\n.inst 0xe59d0018\n.inst 0xe1a04002\n.inst 0xe1a07003\n.inst 0xe3500000\n.inst 0x13a00000\n.inst 0x1a000020\n.inst 0xe3a06000\n.inst 0xe1a0000c\n.inst 0xeb0139bf\n.inst 0xe1a0c000\n.inst 0xe3a01000\n.inst 0xe08c0101\n.inst 0xe1d024be\n.inst 0xe3520000\n.inst 0x11d004bc\n.inst 0x11500005\n.inst 0x83a00000\n.inst 0x9a000010\n.inst 0xe0843080\n.inst 0xe1d380b0\n.inst 0xe1580002\n.inst 0x0a000007\n.inst 0xe1d330b2\n.inst 0xe1530002\n.inst 0x1a000001\n.inst 0xe2800001\n.inst 0xea000002\n.inst 0xe2800002\n.inst 0xe3500008\n.inst 0xbafffff3\n.inst 0xe3500008\n.inst 0xba000002\n.inst 0xe0870086\n.inst 0xe2866001\n.inst 0xe1c020b0\n.inst 0xe2811001\n.inst 0xe3510008\n.inst 0xbaffffe4\n.inst 0xe1a00006\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x0026c8c0, 188)
extern "C" __attribute__((naked)) void script_vm_func_0026c8c0() {
    asm volatile(".arm\n.inst 0xe92d43f8\n.inst 0xe1a05000\n.inst 0xe1a06001\n.inst 0xe1a00002\n.inst 0xe1a07003\n.inst 0xeb0106c5\n.inst 0xe1b04000\n.inst 0x03a00001\n.inst 0x0a000024\n.inst 0xe3a08000\n.inst 0xe1a02000\n.inst 0xe1a03007\n.inst 0xe1a01006\n.inst 0xe1a00005\n.inst 0xe58d8000\n.inst 0xebffb1c5\n.inst 0xe1a06000\n.inst 0xe1900007\n.inst 0x1a000019\n.inst 0xe2550000\n.inst 0xaa00000c\n.inst 0xeb012774\n.inst 0xe1a05000\n.inst 0xe1d402b0\n.inst 0xe3a01001\n.inst 0xeb00b8d1\n.inst 0xe1d512bc\n.inst 0xe0410000\n.inst 0xe6bf1070\n.inst 0xe3510000\n.inst 0xe1c512bc\n.inst 0xaa00000c\n.inst 0xe1c582bc\n.inst 0xea00000a\n.inst 0xe320f000\n.inst 0xeb00f024\n.inst 0xe1a05000\n.inst 0xe1d402b0\n.inst 0xeb00b898\n.inst 0xe1d512bc\n.inst 0xe0410000\n.inst 0xe6bf1070\n.inst 0xe3510000\n.inst 0xe1c512bc\n.inst 0xbafffff2\n.inst 0xe1a00006\n.inst 0xe8bd83f8\n");
}

// DECOMP_FUNC(0x002711e0, 160)
extern "C" __attribute__((naked)) void script_vm_func_002711e0() {
    asm volatile(".arm\n.inst 0xe92d4030\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xed2d8b02\n.inst 0xe24dd01c\n.inst 0xe8900007\n.inst 0xe28d300c\n.inst 0xeddf8a1d\n.inst 0xed9f8a1d\n.inst 0xe88d0007\n.inst 0xe8950007\n.inst 0xe8830007\n.inst 0xea00000a\n.inst 0xe3540000\n.inst 0x1d9d0a01\n.inst 0x1e300a48\n.inst 0x0a000006\n.inst 0xe28d100c\n.inst 0xe1a0000d\n.inst 0xed8d0a01\n.inst 0xeb003931\n.inst 0xe3500000\n.inst 0x1a000009\n.inst 0xea000002\n.inst 0xed9d0a01\n.inst 0xee300a28\n.inst 0xeafffff5\n.inst 0xe89d0007\n.inst 0xe28d300c\n.inst 0xe2844001\n.inst 0xe3540006\n.inst 0xe8830007\n.inst 0xbaffffeb\n.inst 0xe89d0007\n.inst 0xe8850007\n.inst 0xe28dd01c\n.inst 0xecbd8b02\n.inst 0xe8bd8030\n.word 0x3f800000\n.word 0x41700000\n");
}

// DECOMP_FUNC(0x00275a8c, 188)
extern "C" __attribute__((naked)) void script_vm_func_00275a8c() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe59f60ac\n.inst 0xe5960000\n.inst 0xe5d01009\n.inst 0xe3510000\n.inst 0x0a000026\n.inst 0xe5d01008\n.inst 0xe3510000\n.inst 0x1a000023\n.inst 0xe5902004\n.inst 0xe3a01001\n.inst 0xe3a04000\n.inst 0xe3520000\n.inst 0xc3a07000\n.inst 0xe5c01008\n.inst 0xda00001c\n.inst 0xe5960000\n.inst 0xe0805284\n.inst 0xe5f5000c\n.inst 0xe3500000\n.inst 0x0a000012\n.inst 0xe1d501f0\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xe3500001\n.inst 0x0a000005\n.inst 0xea00000c\n.inst 0xe5950008\n.inst 0xeb0047ce\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xea000006\n.inst 0xe595000c\n.inst 0xe3500000\n.inst 0x0a000004\n.inst 0xe5950008\n.inst 0xeb0047c6\n.inst 0xe585700c\n.inst 0xe1c571b2\n.inst 0xe5857008\n.inst 0xe5960000\n.inst 0xe2844001\n.inst 0xe5900004\n.inst 0xe1500004\n.inst 0xcaffffe2\n.inst 0xe8bd81f0\n.word 0x00448c20\n");
}

// DECOMP_FUNC(0x002760bc, 180)
extern "C" __attribute__((naked)) void script_vm_func_002760bc() {
    asm volatile(".arm\n.inst 0xe59f009c\n.inst 0xe59f109c\n.inst 0xe5d02284\n.inst 0xe5911000\n.inst 0xe3520000\n.inst 0x13a01000\n.inst 0x15c01284\n.inst 0x1a00001f\n.inst 0xe3a0c001\n.inst 0xe5c0c2f8\n.inst 0xe591c02c\n.inst 0xe59f2078\n.inst 0xe59f3078\n.inst 0xe580c2fc\n.inst 0xe591c030\n.inst 0xe580c300\n.inst 0xe590c008\n.inst 0xe580c304\n.inst 0xe5922000\n.inst 0xe282c01c\n.inst 0xec9c0a03\n.inst 0xe280cfc2\n.inst 0xec8c0a03\n.inst 0xe592c04c\n.inst 0xe580c314\n.inst 0xe5933000\n.inst 0xe593c018\n.inst 0xe580c318\n.inst 0xe591c02c\n.inst 0xe580c31c\n.inst 0xe5911030\n.inst 0xe282c01c\n.inst 0xe5801320\n.inst 0xec9c0a03\n.inst 0xe280cfc9\n.inst 0xec8c0a03\n.inst 0xe592104c\n.inst 0xe5801330\n.inst 0xe5931018\n.inst 0xe5801334\n.inst 0xe12fff1e\n.word 0x0049f91c\n.word 0x00447e28\n.word 0x00447e88\n.word 0x004474f4\n");
}

// DECOMP_FUNC(0x0027ea24, 192)
extern "C" __attribute__((naked)) void script_vm_func_0027ea24() {
    asm volatile(".arm\n.inst 0xe59f20b0\n.inst 0xe92d4070\n.inst 0xe24dd010\n.inst 0xe3a05000\n.inst 0xe5924000\n.inst 0xe3500000\n.inst 0xe5c45021\n.inst 0x0a000023\n.inst 0xe3a06001\n.inst 0xe3a02003\n.inst 0xe5c46021\n.inst 0xe58d2000\n.inst 0xe1cd00f4\n.inst 0xe59401b8\n.inst 0xe3a03000\n.inst 0xe3e02000\n.inst 0xe3a01003\n.inst 0xeb0060c7\n.inst 0xe59401b8\n.inst 0xebff6a9e\n.inst 0xe59f1064\n.inst 0xee100a10\n.inst 0xe3a02000\n.inst 0xe1500001\n.inst 0xcebd0ac0\n.inst 0xd5c45022\n.inst 0xc5c46022\n.inst 0xe3a01002\n.inst 0xe28400d0\n.inst 0xcd840a05\n.inst 0xeb00fc07\n.inst 0xe28400d0\n.inst 0xeb010134\n.inst 0xe5941014\n.inst 0xe5942008\n.inst 0xe5840018\n.inst 0xe0800001\n.inst 0xe280002a\n.inst 0xe3520003\n.inst 0xe584001c\n.inst 0x03a00002\n.inst 0x05840008\n.inst 0xe3a0001e\n.inst 0xe5840010\n.inst 0xe28dd010\n.inst 0xe8bd8070\n.word 0x0043e128\n.word 0x441d8000\n");
}

// DECOMP_FUNC(0x00282944, 172)
extern "C" __attribute__((naked)) void ui_func_00282944() {
    asm volatile(".arm\n.inst 0xe92d40f0\n.inst 0xe1a05002\n.inst 0xe1a07000\n.inst 0xe59f0090\n.inst 0xe1a06003\n.inst 0xed2d8b02\n.inst 0xe24dd00c\n.inst 0xe28d4028\n.inst 0xec948a02\n.inst 0xe1a04001\n.inst 0xe59f1070\n.inst 0xe1a00000\n.inst 0xe3a01001\n.inst 0xe3a00010\n.inst 0xe1cd00f0\n.inst 0xe3a03068\n.inst 0xe3a02000\n.inst 0xe3a01c01\n.inst 0xe3a00801\n.inst 0xeb0102c3\n.inst 0xe280c00c\n.inst 0xe5807008\n.inst 0xe88c0070\n.inst 0xe2804018\n.inst 0xe59f2040\n.inst 0xe3a01005\n.inst 0xec848a02\n.inst 0xe5801004\n.inst 0xe592300c\n.inst 0xe2821014\n.inst 0xe3530000\n.inst 0x0582000c\n.inst 0x1591200c\n.inst 0x15820000\n.inst 0xe3a02000\n.inst 0xe581000c\n.inst 0xe5802000\n.inst 0xe28dd00c\n.inst 0xecbd8b02\n.inst 0xe8bd80f0\n.word 0x00000281\n.word 0x004100bc\n.word 0x004ea7d4\n");
}

// DECOMP_FUNC(0x002829f0, 160)
extern "C" __attribute__((naked)) void ui_func_002829f0() {
    asm volatile(".arm\n.inst 0xe92d43f0\n.inst 0xe1a04000\n.inst 0xe1a05001\n.inst 0xe24dd00c\n.inst 0xe59f9078\n.inst 0xe59f1078\n.inst 0xe59f0078\n.inst 0xe3a08103\n.inst 0xe1a06002\n.inst 0xe1a07003\n.inst 0xe1a00000\n.inst 0xe3a01001\n.inst 0xe3a00010\n.inst 0xe1cd00f0\n.inst 0xe3a03068\n.inst 0xe3a02000\n.inst 0xe3a01c01\n.inst 0xe3a00801\n.inst 0xeb010299\n.inst 0xe3a0c005\n.inst 0xe280e008\n.inst 0xe580801c\n.inst 0xe59f203c\n.inst 0xe580c004\n.inst 0xe88e02f0\n.inst 0xe2821014\n.inst 0xe592300c\n.inst 0xe3530000\n.inst 0x0582000c\n.inst 0x1591200c\n.inst 0x15820000\n.inst 0xe3a02000\n.inst 0xe581000c\n.inst 0xe5802000\n.inst 0xe28dd00c\n.inst 0xe8bd83f0\n.word 0xffffc040\n.word 0x00000281\n.word 0x004100bc\n.word 0x004ea7d4\n");
}

// DECOMP_FUNC(0x002876d0, 192)
extern "C" __attribute__((naked)) void ui_func_002876d0() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe3a00001\n.inst 0xeb00f855\n.inst 0xe3500000\n.inst 0x1a000025\n.inst 0xe59f0098\n.inst 0xe590101c\n.inst 0xe3510000\n.inst 0x0a00000e\n.inst 0xe3110001\n.inst 0x0a00000c\n.inst 0xe590200c\n.inst 0xe1520005\n.inst 0x1a000006\n.inst 0xe3110030\n.inst 0x1a000019\n.inst 0xe3110002\n.inst 0x0a000005\n.inst 0xe3110008\n.inst 0x1a000003\n.inst 0xea00000f\n.inst 0xe5901010\n.inst 0xe1510005\n.inst 0x0a000011\n.inst 0xe590103c\n.inst 0xe3510000\n.inst 0x13110001\n.inst 0x0a00000e\n.inst 0xe590202c\n.inst 0xe1520005\n.inst 0x1a000007\n.inst 0xe3110030\n.inst 0x1a000008\n.inst 0xe3110002\n.inst 0x0a000007\n.inst 0xe3110008\n.inst 0x1a000005\n.inst 0xe3a04001\n.inst 0xea000003\n.inst 0xe5900030\n.inst 0xe1500005\n.inst 0x1a000000\n.inst 0xe3a04003\n.inst 0xe1a00004\n.inst 0xe8bd8070\n.word 0x004c53c4\n");
}

// DECOMP_FUNC(0x002891e0, 192)
extern "C" __attribute__((naked)) void engine_func_002891e0() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xeb00e64b\n.inst 0xe1a05000\n.inst 0xe2440019\n.inst 0xe3500005\n.inst 0x9a000001\n.inst 0xe3540066\n.inst 0x1a000004\n.inst 0xe3a00f51\n.inst 0xeb00de66\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000019\n.inst 0xe244001f\n.inst 0xe3500004\n.inst 0x9a000001\n.inst 0xe3540067\n.inst 0x1a000004\n.inst 0xe59f0068\n.inst 0xeb00de5c\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a00000f\n.inst 0xe320f000\n.inst 0xeb00e634\n.inst 0xe5d00003\n.inst 0xe3500001\n.inst 0x0a00000c\n.inst 0xe3540018\n.inst 0x03a00002\n.inst 0x0a000006\n.inst 0xe3540040\n.inst 0xaa00000a\n.inst 0xe0850004\n.inst 0xe5d00e14\n.inst 0xe3500003\n.inst 0x0a000006\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe3a00003\n.inst 0xe8bd8070\n.inst 0xe5d50e3d\n.inst 0xe3500003\n.inst 0x1afffff8\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.word 0x0000015a\n");
}

// DECOMP_FUNC(0x0028d4f0, 156)
extern "C" __attribute__((naked)) void camp_func_0028d4f0() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a05000\n.inst 0xe2800b0b\n.inst 0xe2800fcd\n.inst 0xe5906000\n.inst 0xe2460001\n.inst 0xe3500003\n.inst 0x83a06000\n.inst 0x81a04006\n.inst 0x9a000007\n.inst 0xe1a00004\n.inst 0xebff874e\n.inst 0xe1d004b8\n.inst 0xe2844001\n.inst 0xe3500000\n.inst 0x12866001\n.inst 0xe354000c\n.inst 0xbafffff7\n.inst 0xe3560001\n.inst 0xba000010\n.inst 0xe1d50bf4\n.inst 0xe3a04000\n.inst 0xe3500000\n.inst 0xda00000c\n.inst 0xe0850084\n.inst 0xe1d078bc\n.inst 0xe1a00007\n.inst 0xeb0083a3\n.inst 0xe5d0004b\n.inst 0xe1500006\n.inst 0x1a000001\n.inst 0xe1a00007\n.inst 0xe8bd81f0\n.inst 0xe1d50bf4\n.inst 0xe2844001\n.inst 0xe1500004\n.inst 0xcafffff2\n.inst 0xe3a00000\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x00290374, 156)
extern "C" __attribute__((naked)) void script_vm_func_00290374() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xeb009ab8\n.inst 0xe2805c06\n.inst 0xe1a06000\n.inst 0xe1d500b8\n.inst 0xe3a07000\n.inst 0xe3100001\n.inst 0x0a000016\n.inst 0xeb009ab1\n.inst 0xe1a04000\n.inst 0xe2800c06\n.inst 0xe1d000b8\n.inst 0xe3100001\n.inst 0x0a000010\n.inst 0xe1d404b6\n.inst 0xe2401c02\n.inst 0xe25110a3\n.inst 0x1a000003\n.inst 0xe59f0044\n.inst 0xe3a02001\n.inst 0xe3a01000\n.inst 0xebffe57d\n.inst 0xe1d404b6\n.inst 0xe2401c02\n.inst 0xe25110a5\n.inst 0x1a000003\n.inst 0xe59f0028\n.inst 0xe3a02001\n.inst 0xe3a01000\n.inst 0xebffe575\n.inst 0xe1c474b6\n.inst 0xe1d500b8\n.inst 0xe3c00001\n.inst 0xe1c500b8\n.inst 0xe1c674b6\n.inst 0xe1c570b4\n.inst 0xe8bd81f0\n.word 0x00000262\n.word 0x00000263\n");
}

// DECOMP_FUNC(0x002911ec, 192)
extern "C" __attribute__((naked)) void script_vm_func_002911ec() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe3a00001\n.inst 0xeb00d18f\n.inst 0xe3500000\n.inst 0x1a00001f\n.inst 0xe59f0094\n.inst 0xe59f2094\n.inst 0xe3a0301e\n.inst 0xe590101c\n.inst 0xe3110002\n.inst 0x0a00000d\n.inst 0xe3110020\n.inst 0x0a000006\n.inst 0xe3c11020\n.inst 0xe3811040\n.inst 0xe580101c\n.inst 0xe5804004\n.inst 0xe5900000\n.inst 0xe5820004\n.inst 0xea000004\n.inst 0xe3110b01\n.inst 0x1a000002\n.inst 0xe5a03008\n.inst 0xe3811008\n.inst 0xe5801014\n.inst 0xe59f004c\n.inst 0xe590101c\n.inst 0xe3110002\n.inst 0x0a000007\n.inst 0xe3110020\n.inst 0x0a000006\n.inst 0xe3c11020\n.inst 0xe3811040\n.inst 0xe580101c\n.inst 0xe5804004\n.inst 0xe5900000\n.inst 0xe5820004\n.inst 0xe8bd8010\n.inst 0xe3110b01\n.inst 0x1afffffc\n.inst 0xe5a03008\n.inst 0xe3811008\n.inst 0xe5801014\n.inst 0xe8bd8010\n.word 0x004c53c4\n.word 0x0044e098\n.word 0x004c53e4\n");
}

// DECOMP_FUNC(0x002956c0, 160)
extern "C" __attribute__((naked)) void script_vm_func_002956c0() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe2800b0d\n.inst 0xe2800f5d\n.inst 0xe5900000\n.inst 0xeb0047a0\n.inst 0xe59f0074\n.inst 0xe7900004\n.inst 0xeb00bb1e\n.inst 0xebfef3d1\n.inst 0xe59f3068\n.inst 0xe2841b33\n.inst 0xe3a0c000\n.inst 0xe2811fde\n.inst 0xe7c3c004\n.inst 0xe5910000\n.inst 0xe59f2054\n.inst 0xe2800001\n.inst 0xe5810000\n.inst 0xe7921004\n.inst 0xe1510000\n.inst 0x1a000004\n.inst 0xe3a01014\n.inst 0xe1a00004\n.inst 0xeb0004bc\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe3a00001\n.inst 0xeb0024f7\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xeb0024b9\n.inst 0xe3a01009\n.inst 0xe1a00004\n.inst 0xeb0004b2\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.word 0x00003578\n.word 0x0000d640\n.word 0x0000cf74\n");
}

// DECOMP_FUNC(0x00296020, 168)
extern "C" __attribute__((naked)) void script_vm_func_00296020() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1b04000\n.inst 0xe3e06000\n.inst 0x0a00000d\n.inst 0xeb004a74\n.inst 0xe2800090\n.inst 0xe3a05000\n.inst 0xe1500004\n.inst 0x0a000009\n.inst 0xe5d0104a\n.inst 0xe5d4204a\n.inst 0xe1510002\n.inst 0x0a000005\n.inst 0xe2855001\n.inst 0xe2800b01\n.inst 0xe3550018\n.inst 0xe2800f81\n.inst 0xbafffff4\n.inst 0xe1a05006\n.inst 0xe320f000\n.inst 0xeb004a64\n.inst 0xe2800a09\n.inst 0xe2800f42\n.inst 0xe1d010d0\n.inst 0xe3510000\n.inst 0xba000001\n.inst 0xe1510005\n.inst 0x0a000009\n.inst 0xe1d010d1\n.inst 0xe3510000\n.inst 0xba000001\n.inst 0xe1510005\n.inst 0x0a000004\n.inst 0xe1d000d2\n.inst 0xe3500000\n.inst 0xba000003\n.inst 0xe1500005\n.inst 0x1a000001\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe3a00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002971e4, 160)
extern "C" __attribute__((naked)) void script_vm_func_002971e4() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe2515000\n.inst 0xe1a04000\n.inst 0xba000004\n.inst 0xe59400b0\n.inst 0xe5900008\n.inst 0xe1500005\n.inst 0xc3a00000\n.inst 0xca000001\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.inst 0xe59410b4\n.inst 0xe0802285\n.inst 0xe19110d2\n.inst 0xe3510000\n.inst 0xe7c41000\n.inst 0x12800001\n.inst 0x1afffff8\n.inst 0xe59400b4\n.inst 0xe3a01018\n.inst 0xe0811285\n.inst 0xe3a06000\n.inst 0xe7900001\n.inst 0xe584601c\n.inst 0xe5846020\n.inst 0xe5846024\n.inst 0xe5846028\n.inst 0xe584602c\n.inst 0xe5846030\n.inst 0xe5846034\n.inst 0xe5840018\n.inst 0xe3a01070\n.inst 0xe284003c\n.inst 0xe5846038\n.inst 0xeb00b62f\n.inst 0xe28400c8\n.inst 0xe8800060\n.inst 0xe3a00001\n.inst 0xe58460d0\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002994b4, 164)
extern "C" __attribute__((naked)) void engine_func_002994b4() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe1a07000\n.inst 0xe3a09000\n.inst 0xe1a0a001\n.inst 0xe1a08009\n.inst 0xebfde077\n.inst 0xe2506000\n.inst 0xe3a04000\n.inst 0x9a00001d\n.inst 0xe1a00004\n.inst 0xeb01dc90\n.inst 0xe1b05000\n.inst 0xe320f000\n.inst 0x0a000015\n.inst 0xe5d50001\n.inst 0xe1500007\n.inst 0x1a000012\n.inst 0xe1d505b6\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xeb009da7\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a00000b\n.inst 0xe1d505b8\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xebffe729\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000004\n.inst 0xe158000a\n.inst 0x12888001\n.inst 0x1a000001\n.inst 0xe5d59000\n.inst 0xea000002\n.inst 0xe2844001\n.inst 0xe1540006\n.inst 0x3affffe1\n.inst 0xe1a00009\n.inst 0xe8bd87f0\n");
}

// DECOMP_FUNC(0x002998d8, 156)
extern "C" __attribute__((naked)) void ui_func_002998d8() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe59f4088\n.inst 0xe3500000\n.inst 0xe2842000\n.inst 0xe594c004\n.inst 0xe5922004\n.inst 0xe2823d7a\n.inst 0x0a000004\n.inst 0xe3500001\n.inst 0x0a000007\n.inst 0xe3500002\n.inst 0x0a00000b\n.inst 0xea000010\n.inst 0xe5930000\n.inst 0xe1a02001\n.inst 0xe3a03007\n.inst 0xe3a01000\n.inst 0xea000003\n.inst 0xe5930000\n.inst 0xe1a02001\n.inst 0xe3a03007\n.inst 0xe3a01001\n.inst 0xebffebc4\n.inst 0xea000005\n.inst 0xe28ccd7a\n.inst 0xe1a02001\n.inst 0xe59c0000\n.inst 0xe3a03007\n.inst 0xe3a01002\n.inst 0xebffebbd\n.inst 0xe5940004\n.inst 0xe59f3014\n.inst 0xe3a02000\n.inst 0xe3a01006\n.inst 0xe5802010\n.inst 0xe7831000\n.inst 0xe8bd8010\n.word 0x0044e140\n.word 0x000012dc\n");
}

// DECOMP_FUNC(0x0029abc0, 176)
extern "C" __attribute__((naked)) void battle_func_0029abc0() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xeb004e09\n.inst 0xe3500000\n.inst 0x15d05022\n.inst 0x13a04000\n.inst 0x0a000024\n.inst 0xe3a0000c\n.inst 0xebffe17a\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xe3a0000c\n.inst 0xeb004f09\n.inst 0xe5904038\n.inst 0xe3a0000d\n.inst 0xebffe173\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000003\n.inst 0xe3a0000d\n.inst 0xeb004f01\n.inst 0xe5900038\n.inst 0xe0844000\n.inst 0xe3a0000e\n.inst 0xebffe16a\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000003\n.inst 0xe3a0000e\n.inst 0xeb004ef8\n.inst 0xe5900038\n.inst 0xe0844000\n.inst 0xe3a0000f\n.inst 0xebffe161\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000003\n.inst 0xe3a0000f\n.inst 0xeb004eef\n.inst 0xe5900038\n.inst 0xe0844000\n.inst 0xe0450004\n.inst 0xe3500000\n.inst 0xd3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x0029c49c, 156)
extern "C" __attribute__((naked)) void camp_func_0029c49c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xeb003158\n.inst 0xe1a04000\n.inst 0xeb003156\n.inst 0xe1a02000\n.inst 0xe3a01000\n.inst 0xe1a00001\n.inst 0xe0823000\n.inst 0xe2833a09\n.inst 0xe1d33fd0\n.inst 0xe3530000\n.inst 0xba000003\n.inst 0xe2800001\n.inst 0xe3500018\n.inst 0xe2811001\n.inst 0xbafffff6\n.inst 0xe59f0050\n.inst 0xe7d00004\n.inst 0xe1510000\n.inst 0xaa00000d\n.inst 0xeb003145\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe0840384\n.inst 0xe0800404\n.inst 0xe0850100\n.inst 0xe2800090\n.inst 0xeb0481b4\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000004\n.inst 0xe2844001\n.inst 0xe3540018\n.inst 0xbafffff4\n.inst 0xe3e00000\n.inst 0xe8bd8070\n.inst 0xe1a00004\n.inst 0xe8bd8070\n.word 0x0000910b\n");
}

// DECOMP_FUNC(0x0029e19c, 172)
extern "C" __attribute__((naked)) void camp_func_0029e19c() {
    asm volatile(".arm\n.inst 0xe59f209c\n.inst 0xe92d4070\n.inst 0xe3500000\n.inst 0xe24dde61\n.inst 0xe5924004\n.inst 0xe3a05001\n.inst 0xaa000007\n.inst 0xeb00614b\n.inst 0xe1a01000\n.inst 0xe2840c13\n.inst 0xebfebe65\n.inst 0xe2840c1e\n.inst 0xe2800066\n.inst 0xe3a01000\n.inst 0xea00000b\n.inst 0xe3510000\n.inst 0xe1a0600d\n.inst 0xe6ff0070\n.inst 0xe1a01006\n.inst 0x0a000008\n.inst 0xebff3233\n.inst 0xe1a01006\n.inst 0xe2840c13\n.inst 0xebfebdf9\n.inst 0xe2840c1e\n.inst 0xe3a01006\n.inst 0xe2800066\n.inst 0xe5c01000\n.inst 0xea000006\n.inst 0xe320f000\n.inst 0xebffff3e\n.inst 0xe1a01006\n.inst 0xe2840c13\n.inst 0xebfebdef\n.inst 0xe59f0018\n.inst 0xe7c05004\n.inst 0xe2844b07\n.inst 0xe2844fae\n.inst 0xe5c45000\n.inst 0xe28dde61\n.inst 0xe8bd8070\n.word 0x0044e140\n.word 0x00001e66\n");
}

// DECOMP_FUNC(0x0029ec6c, 156)
extern "C" __attribute__((naked)) void ui_func_0029ec6c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe3500c05\n.inst 0xe1a04000\n.inst 0x8a00001f\n.inst 0xeb0046fe\n.inst 0xe1a01000\n.inst 0xe1d001b6\n.inst 0xe2100001\n.inst 0x0a000016\n.inst 0xe59f006c\n.inst 0xe0843104\n.inst 0xe5902004\n.inst 0xe0830184\n.inst 0xe0820100\n.inst 0xe2800903\n.inst 0xe2800f7e\n.inst 0xe5d00016\n.inst 0xe2100002\n.inst 0x1a00000b\n.inst 0xe0813080\n.inst 0xe1d337bc\n.inst 0xe3530000\n.inst 0x0a000009\n.inst 0xe083c103\n.inst 0xe08c3183\n.inst 0xe0823103\n.inst 0xe2833903\n.inst 0xe2833f7e\n.inst 0xe5d33016\n.inst 0xe3130002\n.inst 0x0a000001\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe2800001\n.inst 0xe3500003\n.inst 0x3affffee\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.word 0x0043e2a8\n");
}

// DECOMP_FUNC(0x0029ed44, 184)
extern "C" __attribute__((naked)) void camp_func_0029ed44() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe24dd038\n.inst 0xe1a00001\n.inst 0xeb006983\n.inst 0xe1b04000\n.inst 0x0a000024\n.inst 0xe594002c\n.inst 0xe3100602\n.inst 0x1a000021\n.inst 0xe1d403b6\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xeb00878b\n.inst 0xe3500000\n.inst 0x0a00001b\n.inst 0xe1d403b4\n.inst 0xe3100001\n.inst 0x0a000014\n.inst 0xe3d01001\n.inst 0x0a000009\n.inst 0xe1a000a0\n.inst 0xe1a0100d\n.inst 0xebffa586\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000010\n.inst 0xe1dd02be\n.inst 0xe31000fc\n.inst 0x0a00000d\n.inst 0xea000008\n.inst 0xe1d400b0\n.inst 0xe1a0100d\n.inst 0xebffa57c\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000006\n.inst 0xe1dd02be\n.inst 0xe31000fc\n.inst 0x0a000003\n.inst 0xe1d400b6\n.inst 0xe3100001\n.inst 0x13a00001\n.inst 0x1a000000\n.inst 0xe3a00000\n.inst 0xe28dd038\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002a0de8, 192)
extern "C" __attribute__((naked)) void camp_func_002a0de8() {
    asm volatile(".arm\n.inst 0xe59f00ac\n.inst 0xe92d4030\n.inst 0xe24dd01c\n.inst 0xe5904000\n.inst 0xe3540000\n.inst 0x0a000024\n.inst 0xe2840b01\n.inst 0xe2800f42\n.inst 0xe2845b01\n.inst 0xe8900007\n.inst 0xe28dc010\n.inst 0xeddf0a21\n.inst 0xe28d300c\n.inst 0xe88d0007\n.inst 0xe2840b01\n.inst 0xe2800f45\n.inst 0xed950a4b\n.inst 0xec901a03\n.inst 0xe1a00004\n.inst 0xee211a00\n.inst 0xee611a80\n.inst 0xee220a00\n.inst 0xed9d2a00\n.inst 0xee321a01\n.inst 0xed8d1a00\n.inst 0xee011a10\n.inst 0xe2841b01\n.inst 0xe2811f42\n.inst 0xee311a21\n.inst 0xed8d1a01\n.inst 0xee012a10\n.inst 0xe1a0200d\n.inst 0xee310a00\n.inst 0xed8d0a02\n.inst 0xed9f0a0b\n.inst 0xedcd0a03\n.inst 0xec8c0a02\n.inst 0xeb008489\n.inst 0xe2855e13\n.inst 0xe3a01000\n.inst 0xec950a03\n.inst 0xe1a00004\n.inst 0xebfce8fd\n.inst 0xe28dd01c\n.inst 0xe8bd8030\n.word 0x0044e178\n.word 0x00000000\n.word 0x3f800000\n");
}

// DECOMP_FUNC(0x002a32bc, 192)
extern "C" __attribute__((naked)) void engine_func_002a32bc() {
    asm volatile(".arm\n.inst 0xe59f10b4\n.inst 0xe3a020ff\n.inst 0xe5801000\n.inst 0xe3a01000\n.inst 0xe5801004\n.inst 0xe5c01008\n.inst 0xe580100c\n.inst 0xe5c02010\n.inst 0xe5801014\n.inst 0xe5801018\n.inst 0xe580101c\n.inst 0xe5801020\n.inst 0xe58010b0\n.inst 0xe58010b4\n.inst 0xe5801030\n.inst 0xe5801034\n.inst 0xe5801038\n.inst 0xe580103c\n.inst 0xe5801040\n.inst 0xe5801044\n.inst 0xe5801048\n.inst 0xe580104c\n.inst 0xe5801050\n.inst 0xe5801054\n.inst 0xe5801058\n.inst 0xe580105c\n.inst 0xe5801060\n.inst 0xe5801064\n.inst 0xe5801068\n.inst 0xe580106c\n.inst 0xe5801070\n.inst 0xe5801074\n.inst 0xe5801078\n.inst 0xe580107c\n.inst 0xe5801080\n.inst 0xe5801084\n.inst 0xe5801088\n.inst 0xe580108c\n.inst 0xe5801090\n.inst 0xe5801094\n.inst 0xe5801098\n.inst 0xe580109c\n.inst 0xe58010a0\n.inst 0xe58010a4\n.inst 0xe58010a8\n.inst 0xe58010ac\n.inst 0xe12fff1e\n.word 0x00421e74\n");
}

// DECOMP_FUNC(0x002a3ff8, 164)
extern "C" __attribute__((naked)) void engine_func_002a3ff8() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe3a01080\n.inst 0xeb0082c9\n.inst 0xe3a00000\n.inst 0xe5840000\n.inst 0xe5840004\n.inst 0xed9f0a1d\n.inst 0xe5840008\n.inst 0xe584000c\n.inst 0xed840a03\n.inst 0xe5840010\n.inst 0xe5840014\n.inst 0xe5840018\n.inst 0xe584001c\n.inst 0xed840a07\n.inst 0xe5840040\n.inst 0xe5840044\n.inst 0xe5840048\n.inst 0xeddf0a12\n.inst 0xe584004c\n.inst 0xed840a13\n.inst 0xedc40a11\n.inst 0xe5840050\n.inst 0xe5840054\n.inst 0xe59f2034\n.inst 0xe5840058\n.inst 0xe584005c\n.inst 0xed840a17\n.inst 0xe3e00000\n.inst 0xecd20a04\n.inst 0xe2842020\n.inst 0xe3a01080\n.inst 0xed840a18\n.inst 0xed840a1d\n.inst 0xecc20a04\n.inst 0xe1c406f4\n.inst 0xe8bd8010\n.word 0x3f800000\n.word 0x40a00000\n.word 0x00472520\n");
}

// DECOMP_FUNC(0x002a4e50, 160)
extern "C" __attribute__((naked)) void ui_func_002a4e50() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe1a04000\n.inst 0xe1a08002\n.inst 0xe1a09003\n.inst 0xe59d0024\n.inst 0xe59d5020\n.inst 0xe5840014\n.inst 0xe0810005\n.inst 0xe2400001\n.inst 0xe1a01005\n.inst 0xeb008764\n.inst 0xe0060590\n.inst 0xe0880005\n.inst 0xe2400001\n.inst 0xe1a01005\n.inst 0xe5846018\n.inst 0xeb00875e\n.inst 0xe0070590\n.inst 0xe0880009\n.inst 0xe1a01006\n.inst 0xe0400007\n.inst 0xe584701c\n.inst 0xeb008758\n.inst 0xe0010690\n.inst 0xe3a00000\n.inst 0xe5841020\n.inst 0xe0811007\n.inst 0xe0411006\n.inst 0xe584002c\n.inst 0xe1570001\n.inst 0xe5845028\n.inst 0x8a000005\n.inst 0xe5810000\n.inst 0xe1c421d8\n.inst 0xe1a00001\n.inst 0xe0411002\n.inst 0xe1530001\n.inst 0x9afffff9\n.inst 0xe5840024\n.inst 0xe8bd87f0\n");
}

// DECOMP_FUNC(0x002a6fa0, 172)
extern "C" __attribute__((naked)) void script_vm_func_002a6fa0() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe3710001\n.inst 0xe1a08000\n.inst 0xe1a04001\n.inst 0xe1a06002\n.inst 0x0a000022\n.inst 0xe5980310\n.inst 0xe3a07000\n.inst 0xe3500000\n.inst 0xda00001e\n.inst 0xe5980318\n.inst 0xe0871107\n.inst 0xe0809201\n.inst 0xe1a00009\n.inst 0xeb0014f6\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000012\n.inst 0xe1a00009\n.inst 0xeb0014e4\n.inst 0xe1a05000\n.inst 0xe1a00009\n.inst 0xeb0014d4\n.inst 0xe2501000\n.inst 0xe3a00000\n.inst 0x9a00000a\n.inst 0xe0852300\n.inst 0xe1d230d0\n.inst 0xe1530004\n.inst 0x0592203c\n.inst 0x01520006\n.inst 0x1a000001\n.inst 0xe0850300\n.inst 0xe8bd87f0\n.inst 0xe2800001\n.inst 0xe1500001\n.inst 0x3afffff4\n.inst 0xe5980310\n.inst 0xe2877001\n.inst 0xe1500007\n.inst 0xcaffffe0\n.inst 0xe3a00000\n.inst 0xe8bd87f0\n");
}

// DECOMP_FUNC(0x002a7094, 176)
extern "C" __attribute__((naked)) void func_002a7094() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe3710001\n.inst 0xe1a08000\n.inst 0xe1a04001\n.inst 0xe1a06002\n.inst 0x0a000023\n.inst 0xe5980310\n.inst 0xe3a07000\n.inst 0xe3500000\n.inst 0xda00001f\n.inst 0xe5980318\n.inst 0xe0871107\n.inst 0xe0809201\n.inst 0xe1a00009\n.inst 0xeb0014b9\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000013\n.inst 0xe1a00009\n.inst 0xeb0014a7\n.inst 0xe1a05000\n.inst 0xe1a00009\n.inst 0xeb001497\n.inst 0xe2501000\n.inst 0xe3a00000\n.inst 0x9a00000b\n.inst 0xe0852300\n.inst 0xe1d230d0\n.inst 0xe1530004\n.inst 0x0592203c\n.inst 0x01520006\n.inst 0x1a000002\n.inst 0xe599104c\n.inst 0xe0810200\n.inst 0xe8bd87f0\n.inst 0xe2800001\n.inst 0xe1500001\n.inst 0x3afffff3\n.inst 0xe5980310\n.inst 0xe2877001\n.inst 0xe1500007\n.inst 0xcaffffdf\n.inst 0xe3a00000\n.inst 0xe8bd87f0\n");
}

// DECOMP_FUNC(0x002a7e08, 180)
extern "C" __attribute__((naked)) void engine_func_002a7e08() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe3a00000\n.inst 0xe5840000\n.inst 0xe5840004\n.inst 0xe5840008\n.inst 0xe1b05001\n.inst 0xe1a06002\n.inst 0xe5c4000c\n.inst 0x0a00001e\n.inst 0xe5950000\n.inst 0xe59f1078\n.inst 0xe1500001\n.inst 0x1a00001a\n.inst 0xe5950008\n.inst 0xe3500401\n.inst 0x1a000017\n.inst 0xe1a00005\n.inst 0xe5845000\n.inst 0xebfab626\n.inst 0xe1a01000\n.inst 0xe2811008\n.inst 0xe3a00001\n.inst 0xe5841004\n.inst 0xe3560000\n.inst 0xe5c4000c\n.inst 0x0a00000d\n.inst 0xe3500000\n.inst 0x0a00000b\n.inst 0xe5946000\n.inst 0xe1a00006\n.inst 0xebffffd3\n.inst 0xe59f1028\n.inst 0xe7960000\n.inst 0xe1500001\n.inst 0x1a000004\n.inst 0xe5940000\n.inst 0xebffffcd\n.inst 0xe2800004\n.inst 0xe0800005\n.inst 0xe5840008\n.inst 0xe1a00004\n.inst 0xe8bd8070\n.word 0x52415743\n.word 0x54415743\n");
}

// DECOMP_FUNC(0x002ac614, 188)
extern "C" __attribute__((naked)) void engine_func_002ac614() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe1a04001\n.inst 0xe5900004\n.inst 0xe1a01002\n.inst 0xe1a06003\n.inst 0xebfa8286\n.inst 0xe1a01006\n.inst 0xebfa8291\n.inst 0xe1a06000\n.inst 0xe5950004\n.inst 0xebfa827e\n.inst 0xe5902000\n.inst 0xe5961000\n.inst 0xe1520001\n.inst 0x9a00001c\n.inst 0xe0800181\n.inst 0xe2900004\n.inst 0x0a000019\n.inst 0xe5901000\n.inst 0xe5841000\n.inst 0xe5900004\n.inst 0xe5840004\n.inst 0xe1a00006\n.inst 0xebfa82be\n.inst 0xed840a05\n.inst 0xe1a00006\n.inst 0xebfa828d\n.inst 0xe1a01000\n.inst 0xe2840008\n.inst 0xebffee4c\n.inst 0xe1a00006\n.inst 0xebfa8297\n.inst 0xe5c4000d\n.inst 0xe1a00006\n.inst 0xebfa82a9\n.inst 0xe5c4000e\n.inst 0xe1a00006\n.inst 0xebfa829b\n.inst 0xe5c4000f\n.inst 0xe1a00006\n.inst 0xebfa82ca\n.inst 0xe5c40010\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe3a00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002ad4fc, 164)
extern "C" __attribute__((naked)) void func_002ad4fc() {
    asm volatile(".arm\n.inst 0xed9f3a23\n.inst 0xee715ac1\n.inst 0xee314a81\n.inst 0xee706ac0\n.inst 0xee704a80\n.inst 0xeddf0a21\n.inst 0xee326ac2\n.inst 0xed9f5a1d\n.inst 0xedc00a0e\n.inst 0xee623a82\n.inst 0xed9f0a1b\n.inst 0xee222a05\n.inst 0xed800a01\n.inst 0xed800a03\n.inst 0xeec30a26\n.inst 0xed800a04\n.inst 0xed800a07\n.inst 0xed800a08\n.inst 0xed800a09\n.inst 0xed800a0c\n.inst 0xed800a0d\n.inst 0xed800a0f\n.inst 0xeec31a25\n.inst 0xee240a21\n.inst 0xee621a21\n.inst 0xee831a06\n.inst 0xee223a20\n.inst 0xee640aa0\n.inst 0xee633a81\n.inst 0xee221a81\n.inst 0xed803a00\n.inst 0xedc00a02\n.inst 0xedc01a05\n.inst 0xed800a06\n.inst 0xed801a0a\n.inst 0xedc03a0b\n.inst 0xe12fff1e\n.word 0x3f800000\n.word 0x40000000\n.word 0x00000000\n.word 0xbf800000\n");
}

// DECOMP_FUNC(0x002aea7c, 176)
extern "C" __attribute__((naked)) void engine_func_002aea7c() {
    asm volatile(".arm\n.inst 0xe59f10a4\n.inst 0xe92d41f0\n.inst 0xe0800080\n.inst 0xe3a07000\n.inst 0xe5911000\n.inst 0xe0816180\n.inst 0xe5960004\n.inst 0xe3500000\n.inst 0x0a000012\n.inst 0xe5904004\n.inst 0xe3540000\n.inst 0x0a000008\n.inst 0xe284000c\n.inst 0xe8900021\n.inst 0xeb005629\n.inst 0xe1a00004\n.inst 0xe320f000\n.inst 0xeb005626\n.inst 0xe1b04005\n.inst 0xe320f000\n.inst 0x1afffff6\n.inst 0xe5960004\n.inst 0xe5900000\n.inst 0xeb005620\n.inst 0xe5960004\n.inst 0xe320f000\n.inst 0xeb00561d\n.inst 0xe5867004\n.inst 0xe5964000\n.inst 0xe5940000\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb005617\n.inst 0xe5847000\n.inst 0xe5940008\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb005612\n.inst 0xe5847008\n.inst 0xe1a00004\n.inst 0xeb00560f\n.inst 0xe5867000\n.inst 0xe8bd81f0\n.word 0x0044ea28\n");
}

// DECOMP_FUNC(0x002aeb78, 168)
extern "C" __attribute__((naked)) void engine_func_002aeb78() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a05000\n.inst 0xe24dd080\n.inst 0xe1a07002\n.inst 0xe1a08003\n.inst 0xe1a06001\n.inst 0xe1a00001\n.inst 0xebffe1bc\n.inst 0xe3700001\n.inst 0xe1a04000\n.inst 0x0a00001b\n.inst 0xe3a01080\n.inst 0xe1a0000d\n.inst 0xeb0057df\n.inst 0xe1a0300d\n.inst 0xe1a02007\n.inst 0xe1a01004\n.inst 0xe1a00005\n.inst 0xebffe17e\n.inst 0xe1b05000\n.inst 0x0a000011\n.inst 0xe1a01007\n.inst 0xe1a00006\n.inst 0xeb002ac5\n.inst 0xe1b04000\n.inst 0x0a00000c\n.inst 0xebfa801d\n.inst 0xe1a02005\n.inst 0xe1a01004\n.inst 0xe1a0000d\n.inst 0xebfa77bb\n.inst 0xe1a01008\n.inst 0xe1a00004\n.inst 0xebffe15b\n.inst 0xe1a00004\n.inst 0xebffe14e\n.inst 0xe28dd080\n.inst 0xe1a00004\n.inst 0xe8bd81f0\n.inst 0xe28dd080\n.inst 0xe3a00000\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x002b0908, 176)
extern "C" __attribute__((naked)) void func_002b0908() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a06002\n.inst 0xe1a07000\n.inst 0xe1a00001\n.inst 0xed2d8b02\n.inst 0xe24dd040\n.inst 0xe1a08003\n.inst 0xeddd8a18\n.inst 0xe1cd46d4\n.inst 0xed9d8a1b\n.inst 0xe3540000\n.inst 0x13550000\n.inst 0x03a00000\n.inst 0x0a000019\n.inst 0xe1a01002\n.inst 0xebfffe0f\n.inst 0xe59f1064\n.inst 0xe3e0207c\n.inst 0xe5903004\n.inst 0xe0c1c691\n.inst 0xe5933000\n.inst 0xe58d8004\n.inst 0xe1a0c341\n.inst 0xe04c1fc1\n.inst 0xe387c902\n.inst 0xe0010291\n.inst 0xe58dc000\n.inst 0xedcd8a02\n.inst 0xe28dc010\n.inst 0xe0861181\n.inst 0xed8d8a03\n.inst 0xe0811101\n.inst 0xe3a02001\n.inst 0xe0831101\n.inst 0xe3a03000\n.inst 0xe88c0038\n.inst 0xe1cd22bc\n.inst 0xe1cd22be\n.inst 0xe1a0200d\n.inst 0xebfffbc9\n.inst 0xe28dd040\n.inst 0xecbd8b02\n.inst 0xe8bd81f0\n.word 0x10624dd3\n");
}

// DECOMP_FUNC(0x002b5f90, 160)
extern "C" __attribute__((naked)) void func_002b5f90() {
    asm volatile(".arm\n.inst 0xe92d5ff0\n.inst 0xe3a04000\n.inst 0xe1a06004\n.inst 0xe1a07004\n.inst 0xe1a0b000\n.inst 0xe8905000\n.inst 0xe1a05fc3\n.inst 0xe089a29c\n.inst 0xe1a01fce\n.inst 0xe0209294\n.inst 0xe08a929e\n.inst 0xe020069c\n.inst 0xe022a291\n.inst 0xe0999000\n.inst 0xe022249e\n.inst 0xe0a20004\n.inst 0xe086239c\n.inst 0xe0246394\n.inst 0xe088639e\n.inst 0xe024459c\n.inst 0xe0218391\n.inst 0xe0922009\n.inst 0xe021159e\n.inst 0xe1a05fc0\n.inst 0xe0a42007\n.inst 0xe0900002\n.inst 0xe0a52fc2\n.inst 0xe0900006\n.inst 0xe0a11002\n.inst 0xe3530000\n.inst 0xaa000001\n.inst 0xe090000c\n.inst 0xe0a1100e\n.inst 0xe59d2028\n.inst 0xebfa08b3\n.inst 0xe59b2004\n.inst 0xe1a02fa2\n.inst 0xe0900002\n.inst 0xe2a11000\n.inst 0xe8bd9ff0\n");
}

// DECOMP_FUNC(0x002bb0b4, 188)
extern "C" __attribute__((naked)) void engine_func_002bb0b4() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a04000\n.inst 0xe1a05001\n.inst 0xe590016c\n.inst 0xe3a07000\n.inst 0xe3500000\n.inst 0x0a000009\n.inst 0xe594116c\n.inst 0xe5946174\n.inst 0xee077fba\n.inst 0xe3550000\n.inst 0xe1a00004\n.inst 0x0a000013\n.inst 0xebfa4a76\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xea000014\n.inst 0xe3550000\n.inst 0x03a00000\n.inst 0x0a000019\n.inst 0xe3a01004\n.inst 0xe1a00004\n.inst 0xebffe80d\n.inst 0xe5941184\n.inst 0xe580100c\n.inst 0xe5c07004\n.inst 0xe5941170\n.inst 0xe3510000\n.inst 0x0584016c\n.inst 0x15810000\n.inst 0xe5840170\n.inst 0xe5807000\n.inst 0xeaffffe5\n.inst 0xe320f000\n.inst 0xebfa5cf2\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000007\n.inst 0xe594016c\n.inst 0xe5806008\n.inst 0xe5940174\n.inst 0xe2800001\n.inst 0xe5840174\n.inst 0xe584716c\n.inst 0xe1a00006\n.inst 0xe5847170\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x002bf8d4, 176)
extern "C" __attribute__((naked)) void battle_func_002bf8d4() {
    asm volatile(".arm\n.inst 0xe92d4ff0\n.inst 0xe1a07000\n.inst 0xe1a09001\n.inst 0xe1a0a002\n.inst 0xe59f0094\n.inst 0xe1a0b003\n.inst 0xed2d8b02\n.inst 0xe24dd004\n.inst 0xe5906000\n.inst 0xed9d8a0c\n.inst 0xe3560000\n.inst 0x03a00000\n.inst 0x13a08000\n.inst 0x13a04001\n.inst 0x0a000018\n.inst 0xe0865104\n.inst 0xe5950630\n.inst 0xebfffebf\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a00000e\n.inst 0xe5950630\n.inst 0xebffdee0\n.inst 0xe1500007\n.inst 0xe320f000\n.inst 0x1a000009\n.inst 0xe0860104\n.inst 0xed8d8a00\n.inst 0xe5900630\n.inst 0xe1a0300b\n.inst 0xe1a0200a\n.inst 0xe1a01009\n.inst 0xebffbd04\n.inst 0xe3a08001\n.inst 0xe320f000\n.inst 0xea000002\n.inst 0xe2844001\n.inst 0xe3540004\n.inst 0xbaffffe7\n.inst 0xe1a00008\n.inst 0xe28dd004\n.inst 0xecbd8b02\n.inst 0xe8bd8ff0\n.word 0x0043dfc0\n");
}

// DECOMP_FUNC(0x002c1abc, 168)
extern "C" __attribute__((naked)) void ui_func_002c1abc() {
    asm volatile(".arm\n.inst 0xe59f209c\n.inst 0xe92d4010\n.inst 0xe1a01000\n.inst 0xe2804a01\n.inst 0xe7d20000\n.inst 0xed9f0a21\n.inst 0xe3500000\n.inst 0x1a000013\n.inst 0xeef00a40\n.inst 0xed941a73\n.inst 0xeeb41a60\n.inst 0xeef1fa10\n.inst 0x1a00000e\n.inst 0xeef00a40\n.inst 0xed941a74\n.inst 0xeeb41a60\n.inst 0xeef1fa10\n.inst 0x1a000009\n.inst 0xeef00a40\n.inst 0xed941a75\n.inst 0xeeb41a60\n.inst 0xeef1fa10\n.inst 0x1a000004\n.inst 0xeef00a40\n.inst 0xed941a76\n.inst 0xeeb41a60\n.inst 0xeef1fa10\n.inst 0x0a000008\n.inst 0xeef00a40\n.inst 0xedc40a73\n.inst 0xedc40a74\n.inst 0xedc40a75\n.inst 0xed840a76\n.inst 0xe591052c\n.inst 0xe2811a01\n.inst 0xe2811f73\n.inst 0xebffd2ce\n.inst 0xe3a00000\n.inst 0xe5c401dc\n.inst 0xe8bd8010\n.word 0x3f800000\n.word 0x000011dc\n");
}

// DECOMP_FUNC(0x002c1d3c, 168)
extern "C" __attribute__((naked)) void ui_func_002c1d3c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04001\n.inst 0xe59f1094\n.inst 0xe2805a01\n.inst 0xe24dd010\n.inst 0xe3a06000\n.inst 0xe7d11000\n.inst 0xe3510000\n.inst 0x059501e4\n.inst 0x01500004\n.inst 0x0a00000c\n.inst 0xe3540000\n.inst 0xe58541e4\n.inst 0x05c561e8\n.inst 0x0a000010\n.inst 0xe2840038\n.inst 0xe8900007\n.inst 0xe88d0007\n.inst 0xe5942034\n.inst 0xe5943030\n.inst 0xe1c401d4\n.inst 0xebf9da67\n.inst 0xe3a00003\n.inst 0xe5c501e9\n.inst 0xe3540000\n.inst 0xe5c561e8\n.inst 0x0a000004\n.inst 0xe5d501e9\n.inst 0xe3a04001\n.inst 0xe3500001\n.inst 0x0a000007\n.inst 0xea000003\n.inst 0xe5d501e9\n.inst 0xe3a04000\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xe1a00004\n.inst 0xebfa0e3e\n.inst 0xe5c541e9\n.inst 0xe28dd010\n.inst 0xe8bd8070\n.word 0x000011e8\n");
}

// DECOMP_FUNC(0x002c31e8, 168)
extern "C" __attribute__((naked)) void engine_func_002c31e8() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05001\n.inst 0xe5900000\n.inst 0xe1d031b0\n.inst 0xe590100c\n.inst 0xe0804203\n.inst 0xe5b4300c\n.inst 0xe1510003\n.inst 0x9a000014\n.inst 0xe5941000\n.inst 0xe1a03004\n.inst 0xe1a0c1a1\n.inst 0xe15c0002\n.inst 0xe2011007\n.inst 0x2a000007\n.inst 0xe195c0dc\n.inst 0xe1a0115c\n.inst 0xe3110001\n.inst 0x0a000003\n.inst 0xe1d310b6\n.inst 0xe0801201\n.inst 0xe281400c\n.inst 0xea000002\n.inst 0xe1d310b4\n.inst 0xe0801201\n.inst 0xe281400c\n.inst 0xe5931000\n.inst 0xe5943000\n.inst 0xe1510003\n.inst 0x8affffea\n.inst 0xe5941008\n.inst 0xe3510000\n.inst 0x12840008\n.inst 0x10811000\n.inst 0x0a000004\n.inst 0xe1a00005\n.inst 0xebff9d5d\n.inst 0xe3500000\n.inst 0x01a00004\n.inst 0x0a000000\n.inst 0xe3a00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002c6e04, 172)
extern "C" __attribute__((naked)) void camp_func_002c6e04() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe1d000b0\n.inst 0xe1a05001\n.inst 0xebffc952\n.inst 0xe1a06000\n.inst 0xe1d500b0\n.inst 0xebffc94f\n.inst 0xe5d00003\n.inst 0xe5d61003\n.inst 0xe0500001\n.inst 0x1a000010\n.inst 0xe1d400b0\n.inst 0xebffc949\n.inst 0xe1a04000\n.inst 0xe1d500b0\n.inst 0xebffc946\n.inst 0xe1a01000\n.inst 0xe5d00002\n.inst 0xe5d42002\n.inst 0xe0500002\n.inst 0x1a000006\n.inst 0xe5d40003\n.inst 0xe5d12003\n.inst 0xe0500002\n.inst 0x1a000002\n.inst 0xe1d100b0\n.inst 0xe1d410b0\n.inst 0xe0400001\n.inst 0xe8bd8070\n.inst 0xe1d020b0\n.inst 0xe1d100b0\n.inst 0xe3520000\n.inst 0x0a000003\n.inst 0xe3500000\n.inst 0x03e00000\n.inst 0x0a000004\n.inst 0xea000002\n.inst 0xe3500000\n.inst 0x13a00001\n.inst 0x1a000000\n.inst 0xe0420000\n.inst 0xe12fff1e\n");
}

// DECOMP_FUNC(0x002ca6f4, 180)
extern "C" __attribute__((naked)) void script_vm_func_002ca6f4() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00001\n.inst 0xe59f50a0\n.inst 0xe5954000\n.inst 0xe5c40004\n.inst 0xe3a0003a\n.inst 0xebff689a\n.inst 0xeb01166c\n.inst 0xe594008c\n.inst 0xebfa20f6\n.inst 0xe594008c\n.inst 0xebff74de\n.inst 0xe3a06000\n.inst 0xe584608c\n.inst 0xe5940090\n.inst 0xebfa20f0\n.inst 0xe5940090\n.inst 0xebff74d8\n.inst 0xe5846090\n.inst 0xe5d40085\n.inst 0xe3500000\n.inst 0x0a000004\n.inst 0xe3a00000\n.inst 0xebff73ab\n.inst 0xe5940088\n.inst 0xe3a01000\n.inst 0xebff4782\n.inst 0xe5940088\n.inst 0xebfe6412\n.inst 0xe5846088\n.inst 0xe320f000\n.inst 0xebff6a38\n.inst 0xe3a00000\n.inst 0xe320f000\n.inst 0xebfeadb5\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xebff1cb3\n.inst 0xe5950000\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xebffe6f0\n.inst 0xe5856000\n.inst 0xe8bd8070\n.word 0x0044e300\n");
}

// DECOMP_FUNC(0x002d29f4, 160)
extern "C" __attribute__((naked)) void func_002d29f4() {
    asm volatile(".arm\n.inst 0xe59f0090\n.inst 0xe92d0030\n.inst 0xe3a0c000\n.inst 0xe1a0100c\n.inst 0xe5902000\n.inst 0xe59f0080\n.inst 0xe3a04014\n.inst 0xe3a05016\n.inst 0xe780c002\n.inst 0xe0810081\n.inst 0xe0820380\n.inst 0xe5f03034\n.inst 0xe3530000\n.inst 0x15903174\n.inst 0x13530000\n.inst 0x0a000010\n.inst 0xe353000b\n.inst 0xaa00000e\n.inst 0xe5d0307d\n.inst 0xe3530000\n.inst 0x1a00000b\n.inst 0xe5903084\n.inst 0xe3530000\n.inst 0x0a000006\n.inst 0xe3530002\n.inst 0x02800084\n.inst 0x08801020\n.inst 0x0a000004\n.inst 0xe3530004\n.inst 0x13530005\n.inst 0x1a000001\n.inst 0xe2800084\n.inst 0xe8801010\n.inst 0xe2811001\n.inst 0xe3510020\n.inst 0xbaffffe4\n.inst 0xe8bd0030\n.inst 0xe12fff1e\n.word 0x00447600\n.word 0x00003044\n");
}

// DECOMP_FUNC(0x002d4dac, 156)
extern "C" __attribute__((naked)) void script_vm_func_002d4dac() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xebfea31a\n.inst 0xebfea2ff\n.inst 0xe1d020f4\n.inst 0xe59f107c\n.inst 0xee002a10\n.inst 0xe5911000\n.inst 0xeeb80ac0\n.inst 0xed810a07\n.inst 0xe1d020f6\n.inst 0xee002a10\n.inst 0xeeb80ac0\n.inst 0xed810a08\n.inst 0xe1d020f8\n.inst 0xee002a10\n.inst 0xeeb80ac0\n.inst 0xed810a09\n.inst 0xe591201c\n.inst 0xedd10a08\n.inst 0xe5812028\n.inst 0xedc10a0b\n.inst 0xed810a0c\n.inst 0xe5812034\n.inst 0xedc10a0e\n.inst 0xed810a0f\n.inst 0xe1d020fa\n.inst 0xee002a10\n.inst 0xeeb80ac0\n.inst 0xed810a13\n.inst 0xed810a14\n.inst 0xe1d000fa\n.inst 0xe59f1014\n.inst 0xee000a10\n.inst 0xe5911000\n.inst 0xeeb80ac0\n.inst 0xed810a06\n.inst 0xe8bd8010\n.word 0x00447e88\n.word 0x004474f4\n");
}

// DECOMP_FUNC(0x002d65fc, 160)
extern "C" __attribute__((naked)) void camp_func_002d65fc() {
    asm volatile(".arm\n.inst 0xe59f1094\n.inst 0xe92d41f0\n.inst 0xe3500000\n.inst 0x03a05000\n.inst 0xe5916004\n.inst 0x01a07005\n.inst 0x13a04000\n.inst 0xe5c604c8\n.inst 0x0a000009\n.inst 0xe0640184\n.inst 0xe3a01000\n.inst 0xe0800100\n.inst 0xe0860100\n.inst 0xe2800fdf\n.inst 0xe5c0103c\n.inst 0xe2844001\n.inst 0xe3540002\n.inst 0xbafffff6\n.inst 0xe8bd81f0\n.inst 0xe0650185\n.inst 0xe3a01002\n.inst 0xe0800100\n.inst 0xe0864100\n.inst 0xe2840fdf\n.inst 0xe1c013ba\n.inst 0xe2840fdf\n.inst 0xe3a02000\n.inst 0xe3a01012\n.inst 0xebfefeb8\n.inst 0xe2840fdf\n.inst 0xe3a01001\n.inst 0xe5c0103c\n.inst 0xe5847388\n.inst 0xe2855001\n.inst 0xe584738c\n.inst 0xe3550002\n.inst 0xe5847390\n.inst 0xbaffffec\n.inst 0xe8bd81f0\n.word 0x0043da28\n");
}

// DECOMP_FUNC(0x002de208, 156)
extern "C" __attribute__((naked)) void effGeometry_func_002de208() {
    asm volatile(".arm\n.inst 0xe92d40f0\n.inst 0xe1a06000\n.inst 0xe1a05001\n.inst 0xe59f0080\n.inst 0xe24dd00c\n.inst 0xe3a010dd\n.inst 0xe1a00000\n.inst 0xe3a01001\n.inst 0xe3a00010\n.inst 0xe1cd00f0\n.inst 0xe3a03058\n.inst 0xe3a02000\n.inst 0xe3a01c01\n.inst 0xe3a00801\n.inst 0xebff9497\n.inst 0xe3a01c03\n.inst 0xe3a07000\n.inst 0xe1c010b0\n.inst 0xe1a04000\n.inst 0xe1c070b2\n.inst 0xe1a02007\n.inst 0xe1a01005\n.inst 0xe1a00006\n.inst 0xebfc6191\n.inst 0xe1a01000\n.inst 0xe3150702\n.inst 0xe584100c\n.inst 0x0a000003\n.inst 0xe59fc020\n.inst 0xe2811040\n.inst 0xe89c100d\n.inst 0xe881100d\n.inst 0xe594000c\n.inst 0xe5807060\n.inst 0xe28dd00c\n.inst 0xe1a00004\n.inst 0xe8bd80f0\n.word 0x004145a8\n.word 0x00473808\n");
}

// DECOMP_FUNC(0x002df484, 160)
extern "C" __attribute__((naked)) void ui_func_002df484() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe59f4090\n.inst 0xe24dd048\n.inst 0xe5940004\n.inst 0xe59012b4\n.inst 0xe1a0000d\n.inst 0xebff3b3a\n.inst 0xe28d0010\n.inst 0xed9d0a03\n.inst 0xec901a02\n.inst 0xe5940004\n.inst 0xe2801044\n.inst 0xed800a10\n.inst 0xec811a02\n.inst 0xe280105c\n.inst 0xeddd0a00\n.inst 0xeddd2a01\n.inst 0xed9d2a02\n.inst 0xedc00a0d\n.inst 0xedc02a0e\n.inst 0xed802a0f\n.inst 0xed800a16\n.inst 0xedc00a13\n.inst 0xedc02a14\n.inst 0xed802a15\n.inst 0xec811a02\n.inst 0xe3a01000\n.inst 0xe59002b4\n.inst 0xebfef41c\n.inst 0xe5940004\n.inst 0xe59002b4\n.inst 0xebfe10ab\n.inst 0xe5940004\n.inst 0xe3a01000\n.inst 0xe58012b4\n.inst 0xe5c012b0\n.inst 0xebfe5de4\n.inst 0xe28dd048\n.inst 0xe8bd8010\n.word 0x004474f0\n");
}

// DECOMP_FUNC(0x002dfcf4, 160)
extern "C" __attribute__((naked)) void script_vm_func_002dfcf4() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a01000\n.inst 0xe3a02001\n.inst 0xe59f7088\n.inst 0xe1a04001\n.inst 0xe5970000\n.inst 0xe5c02004\n.inst 0xe5801000\n.inst 0xe1c010ba\n.inst 0xe1c010bc\n.inst 0xe5801010\n.inst 0xe5971000\n.inst 0xe0840104\n.inst 0xe0815180\n.inst 0xe5f5001c\n.inst 0xe3500000\n.inst 0x0a000011\n.inst 0xe1d502f0\n.inst 0xe1d562f2\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xebff8396\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000006\n.inst 0xe3560000\n.inst 0x0a000007\n.inst 0xe1a00006\n.inst 0xebff838f\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000002\n.inst 0xe595001c\n.inst 0xe6bf0070\n.inst 0xebfe9f78\n.inst 0xe2844001\n.inst 0xe3540018\n.inst 0xbaffffe4\n.inst 0xe8bd81f0\n.word 0x00447a48\n");
}

// DECOMP_FUNC(0x002e2750, 184)
extern "C" __attribute__((naked)) void ui_func_002e2750() {
    asm volatile(".arm\n.inst 0xe92d5ff0\n.inst 0xe2516000\n.inst 0xe1a07000\n.inst 0xe1a09002\n.inst 0xe1a0a003\n.inst 0xe3a04000\n.inst 0xc3a0b000\n.inst 0xda000024\n.inst 0xe0875284\n.inst 0xe1d500d6\n.inst 0xe3500000\n.inst 0xba00001d\n.inst 0xe0800180\n.inst 0xe3a01000\n.inst 0xe08a0180\n.inst 0xebfec545\n.inst 0xeebd0ac0\n.inst 0xe3590000\n.inst 0x01c5b0b4\n.inst 0xee108a10\n.inst 0x0a00000e\n.inst 0xe3590001\n.inst 0x0a000002\n.inst 0xe3590002\n.inst 0x1a00000a\n.inst 0xea000005\n.inst 0xe3a01004\n.inst 0xe3a00000\n.inst 0xebfed20f\n.inst 0xe1a00100\n.inst 0xe320f000\n.inst 0xea000002\n.inst 0xe1a01008\n.inst 0xe3a00000\n.inst 0xebfed209\n.inst 0xe1c500b4\n.inst 0xe1d500f4\n.inst 0xe1500008\n.inst 0xba000002\n.inst 0xe1a01008\n.inst 0xebff8e59\n.inst 0xe1c510b4\n.inst 0xe2844001\n.inst 0xe1540006\n.inst 0xbaffffda\n.inst 0xe8bd9ff0\n");
}

// DECOMP_FUNC(0x002eb300, 156)
extern "C" __attribute__((naked)) void ui_func_002eb300() {
    asm volatile(".arm\n.inst 0xe92d4ff0\n.inst 0xe24dd00c\n.inst 0xe3500005\n.inst 0xe1a0a003\n.inst 0xe1a0b001\n.inst 0xe28d1030\n.inst 0xe89103e0\n.inst 0xe59f1074\n.inst 0xe5911000\n.inst 0xaa000019\n.inst 0xe3a0c004\n.inst 0xe5913004\n.inst 0xe08c0200\n.inst 0xe3a01001\n.inst 0xe0834000\n.inst 0xe1a00002\n.inst 0xe5c4100f\n.inst 0xebfece48\n.inst 0xe5c40008\n.inst 0xe5c4a009\n.inst 0xe5c4500a\n.inst 0xe5c4600b\n.inst 0xe5c4700c\n.inst 0xe5c4800d\n.inst 0xe3a00000\n.inst 0xe5c4900e\n.inst 0xebfe4a82\n.inst 0xe89b100a\n.inst 0xe1a02000\n.inst 0xe88d100a\n.inst 0xe1a0300d\n.inst 0xe3a01000\n.inst 0xe1a00003\n.inst 0xebfddfe0\n.inst 0xe1cd00d0\n.inst 0xe1c400f0\n.inst 0xe28dd00c\n.inst 0xe8bd8ff0\n.word 0x00439c60\n");
}

// DECOMP_FUNC(0x002f0204, 180)
extern "C" __attribute__((naked)) void script_vm_func_002f0204() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a00000\n.inst 0xebfe9b53\n.inst 0xe59f709c\n.inst 0xe1a04000\n.inst 0xe5970000\n.inst 0xebfe3a5d\n.inst 0xe5900028\n.inst 0xe3a0100c\n.inst 0xe2800c01\n.inst 0xe1c014bc\n.inst 0xebfe8e98\n.inst 0xe3841801\n.inst 0xe2802a01\n.inst 0xe2822efd\n.inst 0xe1a00fc1\n.inst 0xe5820004\n.inst 0xe3a06001\n.inst 0xe3a05000\n.inst 0xe3a04004\n.inst 0xe5821000\n.inst 0xe320f000\n.inst 0xebfe8e8d\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7900181\n.inst 0xe3100001\n.inst 0x03100040\n.inst 0x1a000007\n.inst 0xe5970000\n.inst 0xebfe3a43\n.inst 0xe2851001\n.inst 0xe0800004\n.inst 0xe6af5071\n.inst 0xe1550006\n.inst 0xe5c04038\n.inst 0xaa000002\n.inst 0xe2844001\n.inst 0xe3540036\n.inst 0xbaffffea\n.inst 0xe3a00001\n.inst 0xe8bd81f0\n.word 0x0043427c\n");
}

// DECOMP_FUNC(0x002f03d0, 168)
extern "C" __attribute__((naked)) void engine_func_002f03d0() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe9ae0\n.inst 0xe1a05000\n.inst 0xe3a00001\n.inst 0xebfe9add\n.inst 0xe1a06000\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe8e27\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000010\n.inst 0xe3110040\n.inst 0x01d01cbe\n.inst 0x01510005\n.inst 0x1a00000c\n.inst 0xe28000cc\n.inst 0xe1d02eb8\n.inst 0xe1d01efa\n.inst 0xe3a00064\n.inst 0xe1600082\n.inst 0xebff5746\n.inst 0xe1500006\n.inst 0xe320f000\n.inst 0xca000003\n.inst 0xe3a00001\n.inst 0xebfe76bf\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe1\n.inst 0xe3a00000\n.inst 0xebfe76b8\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002f0478, 168)
extern "C" __attribute__((naked)) void engine_func_002f0478() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe9ab6\n.inst 0xe1a05000\n.inst 0xe3a00001\n.inst 0xebfe9ab3\n.inst 0xe1a06000\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe8dfd\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000010\n.inst 0xe3110040\n.inst 0x01d01cbe\n.inst 0x01510005\n.inst 0x1a00000c\n.inst 0xe28000cc\n.inst 0xe1d02ebc\n.inst 0xe1d01efe\n.inst 0xe3a00064\n.inst 0xe1600082\n.inst 0xebff571c\n.inst 0xe1500006\n.inst 0xe320f000\n.inst 0xca000003\n.inst 0xe3a00001\n.inst 0xebfe7695\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe1\n.inst 0xe3a00000\n.inst 0xebfe768e\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002f3acc, 172)
extern "C" __attribute__((naked)) void script_vm_func_002f3acc() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a04000\n.inst 0xe59f0094\n.inst 0xe59f7094\n.inst 0xed2d8b04\n.inst 0xeeb08a41\n.inst 0xeef08a60\n.inst 0xeeb09a40\n.inst 0xe5906000\n.inst 0xe3a00065\n.inst 0xe0000094\n.inst 0xe0865100\n.inst 0xe5f501d0\n.inst 0xe3500000\n.inst 0x0a000014\n.inst 0xe5950014\n.inst 0xe350001d\n.inst 0x13500026\n.inst 0x0a000003\n.inst 0xe350001e\n.inst 0x1350001f\n.inst 0x13500025\n.inst 0x1a00000c\n.inst 0xe2850050\n.inst 0xeeb01a48\n.inst 0xeef00a68\n.inst 0xeeb00a49\n.inst 0xecd01a03\n.inst 0xebfe5084\n.inst 0xee100a10\n.inst 0xe1500007\n.inst 0xaa000003\n.inst 0xe3a00012\n.inst 0xe5850004\n.inst 0xecbd8b04\n.inst 0xe8bd81f0\n.inst 0xe2844001\n.inst 0xe3540080\n.inst 0xbaffffe1\n.inst 0xecbd8b04\n.inst 0xe8bd81f0\n.word 0x00447a78\n.word 0x41200000\n");
}

// DECOMP_FUNC(0x002f6e70, 152)
extern "C" __attribute__((naked)) void engine_func_002f6e70() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe8038\n.inst 0xe1a06000\n.inst 0xe3a00001\n.inst 0xebfe8035\n.inst 0xe3a01001\n.inst 0xe1a05011\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe737e\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a00000b\n.inst 0xe3110040\n.inst 0x01d01cbe\n.inst 0x01510006\n.inst 0x1a000007\n.inst 0xe2800c01\n.inst 0xe1d00cb6\n.inst 0xe1100005\n.inst 0x0a000003\n.inst 0xe3a00001\n.inst 0xebfe5c1b\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe6\n.inst 0xe3a00000\n.inst 0xebfe5c14\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002f7694, 160)
extern "C" __attribute__((naked)) void engine_func_002f7694() {
    asm volatile(".arm\n.inst 0xe52de004\n.inst 0xe24dd00c\n.inst 0xe3a00000\n.inst 0xebfe7e2e\n.inst 0xe6ff0070\n.inst 0xebfee473\n.inst 0xe1d025b8\n.inst 0xe3a01000\n.inst 0xe3520000\n.inst 0xe58d2000\n.inst 0xe1d025be\n.inst 0xc3a01001\n.inst 0xe58d2004\n.inst 0xe1d006b4\n.inst 0xe3520000\n.inst 0xc2811001\n.inst 0xe3500000\n.inst 0xc2811001\n.inst 0xe58d0008\n.inst 0xe3510000\n.inst 0xe3e00000\n.inst 0xda000003\n.inst 0xe2410001\n.inst 0xe6ff0070\n.inst 0xebff2534\n.inst 0xe79d0100\n.inst 0xe320f000\n.inst 0xebfe5a13\n.inst 0xe28dd00c\n.inst 0xe3a00001\n.inst 0xe49df004\n.inst 0xe3a00000\n.inst 0xe92d4010\n.inst 0xebfe7e10\n.inst 0xe6ff0070\n.inst 0xebff070f\n.inst 0xe5d00002\n.inst 0xebfe5a09\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002f7d30, 164)
extern "C" __attribute__((naked)) void engine_func_002f7d30() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe7c88\n.inst 0xe1a06000\n.inst 0xe3e05000\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe6fd1\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110001\n.inst 0x0a00000e\n.inst 0xe3110040\n.inst 0x1a00000c\n.inst 0xe3110008\n.inst 0x0a00000a\n.inst 0xe1d010f8\n.inst 0xe3510000\n.inst 0xba000007\n.inst 0xe590127c\n.inst 0xe3510000\n.inst 0x0a000004\n.inst 0xe1d114b6\n.inst 0xe1510006\n.inst 0x1a000001\n.inst 0xe1d050f8\n.inst 0xea000006\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe4\n.inst 0xe6ff0076\n.inst 0xebfe9074\n.inst 0xe3500000\n.inst 0xa280506d\n.inst 0xe1a00005\n.inst 0xebfe5861\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002feda4, 152)
extern "C" __attribute__((naked)) void engine_func_002feda4() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a00000\n.inst 0xebfe606b\n.inst 0xe1a06000\n.inst 0xe3a00001\n.inst 0xebfe6068\n.inst 0xe3a07001\n.inst 0xe1a05017\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe53b1\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a00000b\n.inst 0xe3110040\n.inst 0x01d01cbe\n.inst 0x01510006\n.inst 0x1a000007\n.inst 0xe2800c01\n.inst 0xe1d00cb6\n.inst 0xe1100005\n.inst 0x0a000003\n.inst 0xe3a00001\n.inst 0xebfe3c4e\n.inst 0xe1a00007\n.inst 0xe8bd81f0\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe6\n.inst 0xe3a00000\n.inst 0xebfe3c47\n.inst 0xe1a00007\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x002ff0e4, 156)
extern "C" __attribute__((naked)) void engine_func_002ff0e4() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a00000\n.inst 0xebfe5f9b\n.inst 0xe1a05000\n.inst 0xe3a00001\n.inst 0xebfe5f98\n.inst 0xe1a06000\n.inst 0xe3a04000\n.inst 0xe3a07002\n.inst 0xe320f000\n.inst 0xebfe52e1\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a00000c\n.inst 0xe3110040\n.inst 0x01d01cbe\n.inst 0x01510005\n.inst 0x1a000008\n.inst 0xe0800086\n.inst 0xe2800c01\n.inst 0xe1d00fb2\n.inst 0xe1570520\n.inst 0x1a000003\n.inst 0xe3a00001\n.inst 0xebfe3b7d\n.inst 0xe3a00001\n.inst 0xe8bd81f0\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe5\n.inst 0xe3a00000\n.inst 0xebfe3b76\n.inst 0xe3a00001\n.inst 0xe8bd81f0\n");
}
