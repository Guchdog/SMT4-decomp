#include "types.h"

// Batch 30 B: exact ARM bytes; post-return literal words are preserved as data.

// DECOMP_FUNC(0x00201318, 100)
extern "C" __attribute__((naked)) void engine_func_00201318() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xeb0220c7\n.inst 0xe3500000\n.inst 0x0a000007\n.inst 0xe59f0044\n.inst 0xe5900000\n.inst 0xe5901010\n.inst 0xe5900014\n.inst 0xe1510000\n.inst 0x03a00001\n.inst 0x13a00000\n.inst 0xe8bd8010\n.inst 0xe3a00000\n.inst 0xeb025703\n.inst 0xe3500000\n.inst 0xe3a0100a\n.inst 0x03a000ff\n.inst 0x13e00000\n.inst 0xed9f0a04\n.inst 0xe3a02001\n.inst 0xeb01607b\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.word 0x0043e088\n.word 0x3f800000\n");
}

// DECOMP_FUNC(0x00211824, 124)
extern "C" __attribute__((naked)) void ui_func_00211824() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xeb02091a\n.inst 0xe2800a02\n.inst 0xe3a01006\n.inst 0xe5900234\n.inst 0xe8bd4010\n.inst 0xe1a00000\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe24dd008\n.inst 0xe1a04001\n.inst 0xe3a00000\n.inst 0xeb0215c1\n.inst 0xe1a06000\n.inst 0xeb01df77\n.inst 0xe59f1034\n.inst 0xe1a02000\n.inst 0xe1a00005\n.inst 0xe5911004\n.inst 0xe3510000\n.inst 0x13a03014\n.inst 0x15c13a11\n.inst 0xe3a01000\n.inst 0xe58d1000\n.inst 0xe58d1004\n.inst 0xe1a03004\n.inst 0xe1a01006\n.inst 0xeb01d424\n.inst 0xe28dd008\n.inst 0xe8bd8070\n.word 0x0043e188\n");
}

// DECOMP_FUNC(0x002147e8, 108)
extern "C" __attribute__((naked)) void script_vm_func_002147e8() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe3a07000\n.inst 0xe1a08007\n.inst 0xe59f9054\n.inst 0xe3a04001\n.inst 0xe0896407\n.inst 0xe0865104\n.inst 0xe5950284\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb024ca2\n.inst 0xe5858284\n.inst 0xe2844001\n.inst 0xe3540040\n.inst 0xbafffff6\n.inst 0xe0894107\n.inst 0xe594026c\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xeb024c99\n.inst 0xe584826c\n.inst 0xe5868284\n.inst 0xe2877001\n.inst 0xe3570006\n.inst 0xbaffffea\n.inst 0xe8bd87f0\n.word 0x004bce8c\n");
}

// DECOMP_FUNC(0x00218ae4, 112)
extern "C" __attribute__((naked)) void camp_func_00218ae4() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a06000\n.inst 0xe2862a02\n.inst 0xe3a01000\n.inst 0xe5a2117c\n.inst 0xe3a00004\n.inst 0xe2867c21\n.inst 0xe5820004\n.inst 0xe1c718be\n.inst 0xe1d708fc\n.inst 0xe1a04001\n.inst 0xe3500000\n.inst 0xda00000d\n.inst 0xe0640184\n.inst 0xe3a01008\n.inst 0xe0800100\n.inst 0xe0865100\n.inst 0xe2850020\n.inst 0xeb02993f\n.inst 0xe2850b01\n.inst 0xe2800f66\n.inst 0xe3a01008\n.inst 0xeb02993b\n.inst 0xe1d708fc\n.inst 0xe2844001\n.inst 0xe1500004\n.inst 0xcafffff1\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x002196a4, 116)
extern "C" __attribute__((naked)) void battle_func_002196a4() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe1d000b0\n.inst 0xe1a04001\n.inst 0xe3500000\n.inst 0x0a000013\n.inst 0xe1d410b0\n.inst 0xe3510000\n.inst 0x0a000011\n.inst 0xeb025348\n.inst 0xe1a06000\n.inst 0xe1d400b0\n.inst 0xeb025345\n.inst 0xe3560000\n.inst 0x0a00000b\n.inst 0xe3500000\n.inst 0x0a000008\n.inst 0xe1d500b0\n.inst 0xe3a01001\n.inst 0xeb02055e\n.inst 0xe6bf5070\n.inst 0xe1d400b0\n.inst 0xe3a01001\n.inst 0xeb02055a\n.inst 0xe6bf0070\n.inst 0xe0450000\n.inst 0xe8bd8070\n.inst 0xe3a00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x00226d54, 96)
extern "C" __attribute__((naked)) void func_00226d54() {
    asm volatile(".arm\n.inst 0xe590202c\n.inst 0xe3a01000\n.inst 0xed9f0a13\n.inst 0xe3520004\n.inst 0x03a01001\n.inst 0x0a000001\n.inst 0xe3520005\n.inst 0x03a01002\n.inst 0xe5902008\n.inst 0xe3520000\n.inst 0x0a00000a\n.inst 0xe0800101\n.inst 0xe590100c\n.inst 0xe5900018\n.inst 0xe3510000\n.inst 0x1d910a0e\n.inst 0xe3500000\n.inst 0x1dd00a0e\n.inst 0x1ef40ac0\n.inst 0x1ef1fa10\n.inst 0xceb00a60\n.inst 0xdaffffff\n.inst 0xe12fff1e\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x00227c48, 96)
extern "C" __attribute__((naked)) void ui_func_00227c48() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a04000\n.inst 0xe1a06000\n.inst 0xe1a07001\n.inst 0xe1a08004\n.inst 0xe0840104\n.inst 0xe1a01004\n.inst 0xe0870080\n.inst 0xe2805c09\n.inst 0xe1c58db4\n.inst 0xe5960000\n.inst 0xeb016bc6\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000004\n.inst 0xe2800c01\n.inst 0xe1d01bb4\n.inst 0xe1c51db4\n.inst 0xe1d00bb6\n.inst 0xe1c50db6\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffed\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x00228338, 124)
extern "C" __attribute__((naked)) void ui_func_00228338() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a05000\n.inst 0xeb01ae54\n.inst 0xeb01ac62\n.inst 0xe3500000\n.inst 0x13e00000\n.inst 0x1a000013\n.inst 0xe2856b07\n.inst 0xe3a0701e\n.inst 0xe3a04000\n.inst 0xe3a08058\n.inst 0xe28660fc\n.inst 0xe0840084\n.inst 0xe5961000\n.inst 0xe0800184\n.inst 0xe0880080\n.inst 0xe0815000\n.inst 0xe59f002c\n.inst 0xe1a01005\n.inst 0xeb02091a\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000004\n.inst 0xe2844001\n.inst 0xe3540004\n.inst 0xbafffff1\n.inst 0xe1a00007\n.inst 0xe8bd81f0\n.inst 0xe1d501f0\n.inst 0xe8bd81f0\n.word 0x00400958\n");
}

// DECOMP_FUNC(0x00229a34, 116)
extern "C" __attribute__((naked)) void script_vm_func_00229a34() {
    asm volatile(".arm\n.inst 0xe59f0064\n.inst 0xe92d4010\n.inst 0xe5900000\n.inst 0xe5900000\n.inst 0xe3500000\n.inst 0x0a000012\n.inst 0xe59f1050\n.inst 0xe59042a4\n.inst 0xe19110f0\n.inst 0xe3510000\n.inst 0xba00000b\n.inst 0xe1d010b2\n.inst 0xe3510001\n.inst 0x1a000008\n.inst 0xe1d000b6\n.inst 0xe3100001\n.inst 0x1a000005\n.inst 0xeb0234f1\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000001\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe1b00004\n.inst 0x1affffec\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.word 0x00435d78\n.word 0x000002a2\n");
}

// DECOMP_FUNC(0x0022a2b0, 116)
extern "C" __attribute__((naked)) void script_vm_func_0022a2b0() {
    asm volatile(".arm\n.inst 0xe92d40f0\n.inst 0xe24dd094\n.inst 0xe1a07000\n.inst 0xe1a04001\n.inst 0xe1a05002\n.inst 0xe1a06003\n.inst 0xe3a01080\n.inst 0xe28d0010\n.inst 0xeb026a16\n.inst 0xe28d3010\n.inst 0xe1a02004\n.inst 0xe3a0101f\n.inst 0xe1a00007\n.inst 0xeb01f3b5\n.inst 0xe3500000\n.inst 0x0a000009\n.inst 0xe3a00000\n.inst 0xe3a01004\n.inst 0xe1cd00f0\n.inst 0xe58d0008\n.inst 0xe59f0018\n.inst 0xe1a03005\n.inst 0xe1a02006\n.inst 0xe28d1010\n.inst 0xe5900000\n.inst 0xeb002a8c\n.inst 0xe28dd094\n.inst 0xe8bd80f0\n.word 0x00433130\n");
}

// DECOMP_FUNC(0x00230db0, 100)
extern "C" __attribute__((naked)) void shop_func_00230db0() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe1a04001\n.inst 0xebfff77e\n.inst 0xe1a01004\n.inst 0xeb0254e4\n.inst 0xe3500000\n.inst 0xb3a04000\n.inst 0xba000002\n.inst 0xe3500063\n.inst 0xc3a04063\n.inst 0xd1a04000\n.inst 0xe1a00005\n.inst 0xeb0220c5\n.inst 0xe1a06000\n.inst 0xe1a00005\n.inst 0xeb017bfb\n.inst 0xe3540000\n.inst 0xe0460000\n.inst 0xb3a04000\n.inst 0xba000001\n.inst 0xe1500004\n.inst 0xb1a04000\n.inst 0xe1a00004\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x00232974, 104)
extern "C" __attribute__((naked)) void func_00232974() {
    asm volatile(".arm\n.inst 0xe92d0070\n.inst 0xe3a03000\n.inst 0xe59f4054\n.inst 0xe1a0c003\n.inst 0xe6af207c\n.inst 0xe3520000\n.inst 0xb1a02004\n.inst 0xba000006\n.inst 0xe0802082\n.inst 0xe5d250b0\n.inst 0xe1d26bd1\n.inst 0xe1a02c05\n.inst 0xe1a02822\n.inst 0xe6e22076\n.inst 0xe6bf2072\n.inst 0xe0816003\n.inst 0xe1a05422\n.inst 0xe7c15003\n.inst 0xe28cc001\n.inst 0xe35c0008\n.inst 0xe2833002\n.inst 0xe5c62001\n.inst 0xdaffffec\n.inst 0xe8bd0070\n.inst 0xe12fff1e\n.word 0xffff8140\n");
}

// DECOMP_FUNC(0x00234304, 100)
extern "C" __attribute__((naked)) void script_vm_func_00234304() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a05000\n.inst 0xe1a07001\n.inst 0xe5904000\n.inst 0xe594601c\n.inst 0xe3560000\n.inst 0x9a00000a\n.inst 0xe5940018\n.inst 0xe3a02040\n.inst 0xe1a01007\n.inst 0xe7900185\n.inst 0xeb0200b0\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000004\n.inst 0xe2855001\n.inst 0xe1560005\n.inst 0x8afffff4\n.inst 0xe3a00000\n.inst 0xe8bd81f0\n.inst 0xe5940018\n.inst 0xe3a01004\n.inst 0xe0811185\n.inst 0xe7900001\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x00234608, 100)
extern "C" __attribute__((naked)) void script_vm_func_00234608() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a05000\n.inst 0xe1a07001\n.inst 0xe5904000\n.inst 0xe594601c\n.inst 0xe3560000\n.inst 0x9a00000a\n.inst 0xe5940018\n.inst 0xe3a02040\n.inst 0xe1a01007\n.inst 0xe7900185\n.inst 0xeb01ffef\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000004\n.inst 0xe2855001\n.inst 0xe1560005\n.inst 0x8afffff4\n.inst 0xe3a00000\n.inst 0xe8bd81f0\n.inst 0xe5940018\n.inst 0xe3a01004\n.inst 0xe0811185\n.inst 0xe7900001\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x00234738, 116)
extern "C" __attribute__((naked)) void engine_func_00234738() {
    asm volatile(".arm\n.inst 0xe92d40f0\n.inst 0xe1a04000\n.inst 0xe24dd00c\n.inst 0xe1a06002\n.inst 0xe1a07003\n.inst 0xe1a05001\n.inst 0xe1a00001\n.inst 0xeb00170d\n.inst 0xe1b01fa0\n.inst 0x0a000004\n.inst 0xe1a01000\n.inst 0xe1a00004\n.inst 0xeb021984\n.inst 0xe28dd00c\n.inst 0xe8bd80f0\n.inst 0xe1a02007\n.inst 0xe1a01006\n.inst 0xe1a00005\n.inst 0xeb047b7c\n.inst 0xe1a01000\n.inst 0xe1a0000d\n.inst 0xeb02197b\n.inst 0xe89d0006\n.inst 0xe1a00005\n.inst 0xeb0016ee\n.inst 0xe1cd00d0\n.inst 0xe1c400f0\n.inst 0xe28dd00c\n.inst 0xe8bd80f0\n");
}

// DECOMP_FUNC(0x00237f34, 104)
extern "C" __attribute__((naked)) void func_00237f34() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a07000\n.inst 0xe59f0050\n.inst 0xe0805181\n.inst 0xe1c500d0\n.inst 0xe0811000\n.inst 0xe2414001\n.inst 0xe1500004\n.inst 0xd59f603c\n.inst 0xca00000b\n.inst 0xe0861104\n.inst 0xe1a00007\n.inst 0xe1d120b2\n.inst 0xe1d110b0\n.inst 0xeb000287\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000004\n.inst 0xe5950000\n.inst 0xe2444001\n.inst 0xe1500004\n.inst 0xdafffff3\n.inst 0xe3a00001\n.inst 0xe8bd81f0\n.word 0x004171f8\n.word 0x004149c0\n");
}

// DECOMP_FUNC(0x0023a484, 96)
extern "C" __attribute__((naked)) void func_0023a484() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe5900004\n.inst 0xebffae46\n.inst 0xe3500000\n.inst 0x15906010\n.inst 0x13560000\n.inst 0x03a0000e\n.inst 0x0a00000c\n.inst 0xe5965048\n.inst 0xe3a04000\n.inst 0xe3550000\n.inst 0xda000007\n.inst 0xe1a00006\n.inst 0xeb05d69e\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000004\n.inst 0xe2844001\n.inst 0xe1550004\n.inst 0xcafffff7\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.inst 0xe3a00014\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x0023a620, 112)
extern "C" __attribute__((naked)) void func_0023a620() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3500000\n.inst 0xe3a06000\n.inst 0xe1a04002\n.inst 0x03a00001\n.inst 0x05826000\n.inst 0x0a00000f\n.inst 0xe5900004\n.inst 0xebffadd9\n.inst 0xe5905010\n.inst 0xe3550000\n.inst 0x15950048\n.inst 0x13500000\n.inst 0x0a000006\n.inst 0xe1a00005\n.inst 0xeb06c13e\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xe5d00014\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xe3a0000e\n.inst 0xe5846000\n.inst 0xe8bd8070\n.inst 0xe5950048\n.inst 0xe5840000\n.inst 0xe3a00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x0023ec74, 100)
extern "C" __attribute__((naked)) void camp_func_0023ec74() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe3a01002\n.inst 0xe1a00001\n.inst 0xeb02088e\n.inst 0xe1a06000\n.inst 0xeb020882\n.inst 0xe3540000\n.inst 0xe1a05000\n.inst 0xba000003\n.inst 0xe1a00006\n.inst 0xeb020869\n.inst 0xe1500004\n.inst 0x8a000001\n.inst 0xe1a00005\n.inst 0xe8bd8070\n.inst 0xe59f0018\n.inst 0xe1a01004\n.inst 0xe5900000\n.inst 0xebffb042\n.inst 0xe3500000\n.inst 0x00640184\n.inst 0x00850100\n.inst 0xe8bd8070\n.word 0x00433158\n");
}

// DECOMP_FUNC(0x00240744, 100)
extern "C" __attribute__((naked)) void battle_func_00240744() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a04000\n.inst 0xe1a07000\n.inst 0xe0640184\n.inst 0xe0800100\n.inst 0xe0870100\n.inst 0xe2806d97\n.inst 0xe5965004\n.inst 0xe5d50000\n.inst 0xe3500056\n.inst 0x05d50001\n.inst 0x03500045\n.inst 0x05d50002\n.inst 0x03500052\n.inst 0x1a000005\n.inst 0xe2860008\n.inst 0xeb002820\n.inst 0xe1a01005\n.inst 0xe5c60000\n.inst 0xeb002605\n.inst 0xe5c60000\n.inst 0xe2844001\n.inst 0xe354000b\n.inst 0xbaffffea\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x00240e1c, 112)
extern "C" __attribute__((naked)) void engine_func_00240e1c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe59f4060\n.inst 0xe5941000\n.inst 0xe3510000\n.inst 0x1a000011\n.inst 0xe3500065\n.inst 0xe5840004\n.inst 0x1a000002\n.inst 0xe3a01006\n.inst 0xe3a0001c\n.inst 0xeb02131b\n.inst 0xe5940004\n.inst 0xe3500066\n.inst 0x1a000002\n.inst 0xe3a01007\n.inst 0xe3a0001c\n.inst 0xeb021315\n.inst 0xe5940004\n.inst 0xe3500067\n.inst 0x1a000002\n.inst 0xe3a01008\n.inst 0xe3a0001c\n.inst 0xeb02130f\n.inst 0xe5940000\n.inst 0xe2800001\n.inst 0xe5840000\n.inst 0xe8bd8010\n.word 0x0044cf60\n");
}

// DECOMP_FUNC(0x0024807c, 116)
extern "C" __attribute__((naked)) void ui_func_0024807c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xed2d8b02\n.inst 0xeeb08a40\n.inst 0xeeb00a60\n.inst 0xeddf0a15\n.inst 0xeeb41a60\n.inst 0xeef1fa10\n.inst 0x0a000010\n.inst 0xeef41ae0\n.inst 0xeef1fa10\n.inst 0x9eb00a48\n.inst 0x9a00000c\n.inst 0xeef41ac1\n.inst 0xeef1fa10\n.inst 0xaa000009\n.inst 0xee708a48\n.inst 0xeddf0a0a\n.inst 0xee610aa0\n.inst 0xee800a81\n.inst 0xeebc0ac0\n.inst 0xee100a10\n.inst 0xe6ff0070\n.inst 0xeb01ae96\n.inst 0xee200a28\n.inst 0xee300a08\n.inst 0xecbd8b02\n.inst 0xe8bd8010\n.word 0x00000000\n.word 0x46800000\n");
}

// DECOMP_FUNC(0x00248358, 96)
extern "C" __attribute__((naked)) void script_vm_func_00248358() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe3a01002\n.inst 0xe3a00023\n.inst 0xeb01e2d5\n.inst 0xe1a06000\n.inst 0xeb01e2c9\n.inst 0xe1a05000\n.inst 0xe1a00006\n.inst 0xeb01e2b2\n.inst 0xe1540000\n.inst 0x30850284\n.inst 0x3a000008\n.inst 0xe59f1020\n.inst 0xe5912000\n.inst 0xe2822ffd\n.inst 0xe8920006\n.inst 0xe0811000\n.inst 0xe1540001\n.inst 0x30440000\n.inst 0x30820280\n.inst 0x23a00000\n.inst 0xe8bd8070\n.word 0x00433158\n");
}

// DECOMP_FUNC(0x002483b8, 96)
extern "C" __attribute__((naked)) void camp_func_002483b8() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe3a01000\n.inst 0xe3a00023\n.inst 0xeb01e2bd\n.inst 0xe1a06000\n.inst 0xeb01e2b1\n.inst 0xe1a05000\n.inst 0xe1a00006\n.inst 0xeb01e29a\n.inst 0xe1540000\n.inst 0x30850284\n.inst 0x3a000008\n.inst 0xe59f1020\n.inst 0xe5912000\n.inst 0xe2822ff9\n.inst 0xe8920006\n.inst 0xe0811000\n.inst 0xe1540001\n.inst 0x30440000\n.inst 0x30820280\n.inst 0x23a00000\n.inst 0xe8bd8070\n.word 0x00433158\n");
}

// DECOMP_FUNC(0x0024a964, 112)
extern "C" __attribute__((naked)) void engine_func_0024a964() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe59f6054\n.inst 0xe5960000\n.inst 0xe3500000\n.inst 0xc59f704c\n.inst 0xda00000d\n.inst 0xe20400ff\n.inst 0xe0801180\n.inst 0xe0810280\n.inst 0xe1a01005\n.inst 0xe0870180\n.inst 0xe2800001\n.inst 0xeb017f94\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000005\n.inst 0xe5960000\n.inst 0xe2844001\n.inst 0xe1500004\n.inst 0xcafffff1\n.inst 0xe3a000ff\n.inst 0xe8bd81f0\n.inst 0xe20400ff\n.inst 0xe8bd81f0\n.word 0x00433278\n.word 0x00478000\n");
}

// DECOMP_FUNC(0x0024b9d0, 116)
extern "C" __attribute__((naked)) void func_0024b9d0() {
    asm volatile(".arm\n.inst 0xe52d4004\n.inst 0xe5902020\n.inst 0xe1c22cd0\n.inst 0xe0030392\n.inst 0xe3530000\n.inst 0x0a000013\n.inst 0xe5902018\n.inst 0xe59f404c\n.inst 0xe590c004\n.inst 0xe0410002\n.inst 0xe0801094\n.inst 0xe1a002a0\n.inst 0xe020c390\n.inst 0xe0800100\n.inst 0xe0820180\n.inst 0xda000009\n.inst 0xe2400018\n.inst 0xe3130001\n.inst 0xe3e02000\n.inst 0x15a02028\n.inst 0xe1b010c3\n.inst 0x0a000003\n.inst 0xe5802028\n.inst 0xe2511001\n.inst 0xe5a02050\n.inst 0x1afffffb\n.inst 0xe49d4004\n.inst 0xe12fff1e\n.word 0xcccccccd\n");
}

// DECOMP_FUNC(0x00250960, 120)
extern "C" __attribute__((naked)) void func_00250960() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe3a00001\n.inst 0xebffd52e\n.inst 0xe6bf2070\n.inst 0xed9f0a16\n.inst 0xe2843b07\n.inst 0xe3a00000\n.inst 0xe284cd7f\n.inst 0xe2833fa6\n.inst 0xe59c1000\n.inst 0xe0804200\n.inst 0xe0844300\n.inst 0xe350006d\n.inst 0xe0811184\n.inst 0xe1c127b4\n.inst 0xaa000007\n.inst 0xe5931000\n.inst 0xe0804100\n.inst 0xe0844300\n.inst 0xe0811104\n.inst 0xe2811030\n.inst 0xed810a02\n.inst 0xed810a01\n.inst 0xed810a00\n.inst 0xe2800001\n.inst 0xe350006d\n.inst 0xbaffffed\n.inst 0xe8bd8010\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x00253eb0, 116)
extern "C" __attribute__((naked)) void engine_func_00253eb0() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xeb01bb17\n.inst 0xe59f205c\n.inst 0xe1a01000\n.inst 0xe3a00000\n.inst 0xe19240f4\n.inst 0xe0802100\n.inst 0xe0812102\n.inst 0xe1a03002\n.inst 0xe5f2cf20\n.inst 0xe31c0001\n.inst 0x131c0004\n.inst 0x0a000009\n.inst 0xe2833c0f\n.inst 0xe1d332f6\n.inst 0xe1530004\n.inst 0x1a000005\n.inst 0xe0800100\n.inst 0xe0810100\n.inst 0xe5d00f20\n.inst 0xe3800010\n.inst 0xe5c20000\n.inst 0xe8bd8010\n.inst 0xe2800001\n.inst 0xe3500010\n.inst 0xbaffffeb\n.inst 0xe8bd8010\n.word 0x0000013a\n");
}

// DECOMP_FUNC(0x00254298, 96)
extern "C" __attribute__((naked)) void camp_func_00254298() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe3a01001\n.inst 0xe3a00024\n.inst 0xeb01b305\n.inst 0xe1a06000\n.inst 0xeb01b2f9\n.inst 0xe1a04000\n.inst 0xe1a00006\n.inst 0xeb01b2e2\n.inst 0xe2501000\n.inst 0xe3a00000\n.inst 0x9a000008\n.inst 0xe1d420b0\n.inst 0xe1520005\n.inst 0x1a000001\n.inst 0xe1a00004\n.inst 0xe8bd8070\n.inst 0xe2800001\n.inst 0xe1510000\n.inst 0xe2844040\n.inst 0x8afffff6\n.inst 0xe3a00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x00254a64, 96)
extern "C" __attribute__((naked)) void func_00254a64() {
    asm volatile(".arm\n.inst 0xe2101102\n.inst 0x5a000013\n.inst 0xe2001bff\n.inst 0xe1a00b00\n.inst 0xe1a01521\n.inst 0xe3510011\n.inst 0xe1a00b20\n.inst 0x1a000003\n.inst 0xe3500064\n.inst 0xba000001\n.inst 0xe35000b3\n.inst 0xda000009\n.inst 0xe3510011\n.inst 0x1a000003\n.inst 0xe3500f55\n.inst 0xba000001\n.inst 0xe3500f5a\n.inst 0xba000003\n.inst 0xe3510011\n.inst 0x1a000001\n.inst 0xe3500f5a\n.inst 0xa59f3000\n.inst 0xe12fff1e\n.word 0x00000185\n");
}

// DECOMP_FUNC(0x00256364, 112)
extern "C" __attribute__((naked)) void script_vm_func_00256364() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xeb0182bc\n.inst 0xe1a04000\n.inst 0xe2800c06\n.inst 0xe1d000b8\n.inst 0xe3100001\n.inst 0x0a000011\n.inst 0xe1d404b6\n.inst 0xe2401c02\n.inst 0xe25110a3\n.inst 0x1a000003\n.inst 0xe59f0034\n.inst 0xe3a02001\n.inst 0xe3a01000\n.inst 0xeb00cd88\n.inst 0xe1d404b6\n.inst 0xe2401c02\n.inst 0xe25110a5\n.inst 0x1a000003\n.inst 0xe59f0018\n.inst 0xe3a02001\n.inst 0xe3a01000\n.inst 0xeb00cd80\n.inst 0xe3a00000\n.inst 0xe1c404b6\n.inst 0xe8bd8010\n.word 0x00000262\n.word 0x00000263\n");
}

// DECOMP_FUNC(0x00256b04, 124)
extern "C" __attribute__((naked)) void battle_func_00256b04() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe59f406c\n.inst 0xe1a03001\n.inst 0xe6bf1070\n.inst 0xe3a02000\n.inst 0xe5940000\n.inst 0xebff4002\n.inst 0xe5941000\n.inst 0xe5911008\n.inst 0xe3510000\n.inst 0x0a00000f\n.inst 0xe5d13004\n.inst 0xe591200c\n.inst 0xe3530034\n.inst 0x1a000009\n.inst 0xe1d130f0\n.inst 0xe1d010f0\n.inst 0xe1530001\n.inst 0x1a000005\n.inst 0xe1d010f2\n.inst 0xe3510000\n.inst 0xba000002\n.inst 0xe3e01000\n.inst 0xe1c010b2\n.inst 0xea000001\n.inst 0xe1b01002\n.inst 0x1affffef\n.inst 0xe3a01034\n.inst 0xe5c01004\n.inst 0xe8bd8010\n.word 0x00434290\n");
}

// DECOMP_FUNC(0x00259760, 108)
extern "C" __attribute__((naked)) void engine_func_00259760() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a04000\n.inst 0xe1a07000\n.inst 0xe59f0054\n.inst 0xe1a08004\n.inst 0xe5905000\n.inst 0xe0856104\n.inst 0xe5960034\n.inst 0xeb019725\n.inst 0xe3500000\n.inst 0xe2844001\n.inst 0x05868034\n.inst 0xe354000a\n.inst 0xbafffff7\n.inst 0xe3a00000\n.inst 0xe0851100\n.inst 0xe5911034\n.inst 0xe3510000\n.inst 0x0a000003\n.inst 0xe2800001\n.inst 0xe350000a\n.inst 0xbafffff8\n.inst 0xe8bd81f0\n.inst 0xe0850100\n.inst 0xe5807034\n.inst 0xe8bd81f0\n.word 0x0043ded0\n");
}

// DECOMP_FUNC(0x0025b640, 112)
extern "C" __attribute__((naked)) void script_vm_func_0025b640() {
    asm volatile(".arm\n.inst 0xe59f0064\n.inst 0xe92d4010\n.inst 0xed2d8b02\n.inst 0xeeb08a43\n.inst 0xe5900000\n.inst 0xe3500064\n.inst 0xba000004\n.inst 0xeb00b13a\n.inst 0xeeb40ac8\n.inst 0xeef1fa10\n.inst 0x3a000009\n.inst 0xea00000b\n.inst 0xee303ac2\n.inst 0xeeb04ac3\n.inst 0xeeb44ae3\n.inst 0xeef1fa10\n.inst 0x2a000006\n.inst 0xeb00b1b2\n.inst 0xeeb40ac8\n.inst 0xeef1fa10\n.inst 0x2a000002\n.inst 0xecbd8b02\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xecbd8b02\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.word 0x0049f91c\n");
}

// DECOMP_FUNC(0x00262b60, 108)
extern "C" __attribute__((naked)) void ui_func_00262b60() {
    asm volatile(".arm\n.inst 0xe3100003\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0x03110003\n.inst 0x1a00000a\n.inst 0xe59fe04c\n.inst 0xe2522004\n.inst 0xba000006\n.inst 0xe4913004\n.inst 0xe043c00e\n.inst 0xe1ccc003\n.inst 0xe01cc38e\n.inst 0x04803004\n.inst 0x0afffff7\n.inst 0xe2411004\n.inst 0xe2822004\n.inst 0xe2522001\n.inst 0xba000005\n.inst 0xe4d13001\n.inst 0xe3530000\n.inst 0xe4c03001\n.inst 0x1afffff9\n.inst 0xe1a01002\n.inst 0xeb0183e1\n.inst 0xe1a00004\n.inst 0xe8bd8010\n.word 0x01010101\n");
}

// DECOMP_FUNC(0x00266e10, 120)
extern "C" __attribute__((naked)) void script_vm_func_00266e10() {
    asm volatile(".arm\n.inst 0xe59f2068\n.inst 0xe52d4004\n.inst 0xe3a03000\n.inst 0xe2821b01\n.inst 0xe2822a01\n.inst 0xe2822f61\n.inst 0xe2811fe1\n.inst 0xe5d22048\n.inst 0xe3520000\n.inst 0x0a00000e\n.inst 0xe3500010\n.inst 0x2a00000c\n.inst 0xe0812100\n.inst 0xe3a0c001\n.inst 0xe592487c\n.inst 0xe59f2030\n.inst 0xe1a0001c\n.inst 0xe3540000\n.inst 0x1a000002\n.inst 0xe591ca40\n.inst 0xe1ccc000\n.inst 0xe582c000\n.inst 0xe5911a40\n.inst 0xe1100001\n.inst 0x13a03001\n.inst 0xe49d4004\n.inst 0xe1a00003\n.inst 0xe12fff1e\n.word 0x004e1f68\n.word 0x004e312c\n");
}

// DECOMP_FUNC(0x00269f34, 124)
extern "C" __attribute__((naked)) void camp_func_00269f34() {
    asm volatile(".arm\n.inst 0xe59f0070\n.inst 0xe92d4070\n.inst 0xe3a04000\n.inst 0xe3e06000\n.inst 0xe5905000\n.inst 0xe0840084\n.inst 0xe0851084\n.inst 0xe0850080\n.inst 0xe2811c0e\n.inst 0xe2800c0e\n.inst 0xe1c162b2\n.inst 0xe1c062b8\n.inst 0xe1c062ba\n.inst 0xe1c062bc\n.inst 0xeb013c25\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xeb013c22\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xeb013c1f\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xeb013c1c\n.inst 0xe2844001\n.inst 0xe3540003\n.inst 0xbaffffe9\n.inst 0xe3a00000\n.inst 0xe5c50e3b\n.inst 0xe8bd8070\n.word 0x0043da90\n");
}

// DECOMP_FUNC(0x0026ca24, 104)
extern "C" __attribute__((naked)) void script_vm_func_0026ca24() {
    asm volatile(".arm\n.inst 0xe59f105c\n.inst 0xe92d4070\n.inst 0xe1b04000\n.inst 0xe3a00000\n.inst 0xe5915000\n.inst 0xe5c50010\n.inst 0x0a000009\n.inst 0xe3a01031\n.inst 0xe2850f55\n.inst 0xeb016038\n.inst 0xe3a00000\n.inst 0xe7d41000\n.inst 0xe3510000\n.inst 0x0a000003\n.inst 0xe2800001\n.inst 0xe3500031\n.inst 0xbafffff9\n.inst 0xe8bd8070\n.inst 0xe2802001\n.inst 0xe1a01004\n.inst 0xe2850f55\n.inst 0xeb01655d\n.inst 0xe3a00001\n.inst 0xe5c50010\n.inst 0xe8bd8070\n.word 0x0043e0f8\n");
}

// DECOMP_FUNC(0x0026f3f8, 104)
extern "C" __attribute__((naked)) void script_vm_func_0026f3f8() {
    asm volatile(".arm\n.inst 0xe59f205c\n.inst 0xe52de004\n.inst 0xe24dd00c\n.inst 0xe3a03001\n.inst 0xe5922004\n.inst 0xe3500000\n.inst 0xe5c2355c\n.inst 0xe5c234cb\n.inst 0x0a000009\n.inst 0xe3a03003\n.inst 0xe58d3000\n.inst 0xe1cd00f4\n.inst 0xe5920558\n.inst 0xe3a03000\n.inst 0xe3e02000\n.inst 0xe3a01003\n.inst 0xeb009e53\n.inst 0xe28dd00c\n.inst 0xe49df004\n.inst 0xe3a00000\n.inst 0xe5c204cb\n.inst 0xe5c2055c\n.inst 0xe5820558\n.inst 0xe28dd00c\n.inst 0xe49df004\n.word 0x0043da28\n");
}

// DECOMP_FUNC(0x0026fc24, 124)
extern "C" __attribute__((naked)) void script_vm_func_0026fc24() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a06000\n.inst 0xe3a00001\n.inst 0xeb015701\n.inst 0xe3500000\n.inst 0x1a000015\n.inst 0xe59f8058\n.inst 0xe3a04000\n.inst 0xe1a07004\n.inst 0xe0885284\n.inst 0xe595001c\n.inst 0xe3100002\n.inst 0x13100030\n.inst 0x0a00000a\n.inst 0xe5950000\n.inst 0xe3a01000\n.inst 0xebfe8262\n.inst 0xe585700c\n.inst 0xe5857004\n.inst 0xe5857008\n.inst 0xe5857010\n.inst 0xe5857018\n.inst 0xe5857014\n.inst 0xe3a06001\n.inst 0xe585701c\n.inst 0xe2844001\n.inst 0xe3540002\n.inst 0xbaffffec\n.inst 0xe1a00006\n.inst 0xe8bd81f0\n.word 0x004c53c4\n");
}

// DECOMP_FUNC(0x0027054c, 124)
extern "C" __attribute__((naked)) void script_vm_func_0027054c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a05000\n.inst 0xe59f4068\n.inst 0xe5940018\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb014f7d\n.inst 0xe5845018\n.inst 0xe594001c\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb014f78\n.inst 0xe584501c\n.inst 0xe5940020\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb014f73\n.inst 0xe5845020\n.inst 0xe5940024\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb014f6e\n.inst 0xe5845024\n.inst 0xe5845004\n.inst 0xe5845008\n.inst 0xe584500c\n.inst 0xe5845010\n.inst 0xe5845014\n.inst 0xe5c45000\n.inst 0xe8bd8070\n.word 0x00446fe8\n");
}

// DECOMP_FUNC(0x00275c2c, 116)
extern "C" __attribute__((naked)) void script_vm_func_00275c2c() {
    asm volatile(".arm\n.inst 0xe59f0068\n.inst 0xe92d4070\n.inst 0xe5904000\n.inst 0xe3a00000\n.inst 0xe1a06000\n.inst 0xe2845b03\n.inst 0xe5c40e8c\n.inst 0xe5940fdc\n.inst 0xe2855ff7\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb012b83\n.inst 0xe5856000\n.inst 0xe5940fe8\n.inst 0xe2845b03\n.inst 0xe2855ffa\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb012b7c\n.inst 0xe5856000\n.inst 0xe5940fe4\n.inst 0xe2845b03\n.inst 0xe2855ff9\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb012b75\n.inst 0xe5856000\n.inst 0xe8bd8070\n.word 0x0043e278\n");
}

// DECOMP_FUNC(0x002764d4, 124)
extern "C" __attribute__((naked)) void script_vm_func_002764d4() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe3a01005\n.inst 0xe3a00023\n.inst 0xeb012a76\n.inst 0xe1a06000\n.inst 0xeb012a6a\n.inst 0xe1a05000\n.inst 0xe1a00006\n.inst 0xeb012a53\n.inst 0xe1540000\n.inst 0x2a000003\n.inst 0xe0840084\n.inst 0xe0800184\n.inst 0xe0850100\n.inst 0xe8bd8070\n.inst 0xe59f1030\n.inst 0xe5912000\n.inst 0xe2822b01\n.inst 0xe282200c\n.inst 0xe8920006\n.inst 0xe0811000\n.inst 0xe1510004\n.inst 0x93a00000\n.inst 0x9afffff5\n.inst 0xe0440000\n.inst 0xe0801080\n.inst 0xe0810180\n.inst 0xe0820100\n.inst 0xe8bd8070\n.word 0x00433158\n");
}

// DECOMP_FUNC(0x0027d9b8, 104)
extern "C" __attribute__((naked)) void script_vm_func_0027d9b8() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe3a01001\n.inst 0xe3a00023\n.inst 0xeb010d3d\n.inst 0xe1a06000\n.inst 0xeb010d31\n.inst 0xe1a05000\n.inst 0xe1a00006\n.inst 0xeb010d1a\n.inst 0xe1540000\n.inst 0x30840084\n.inst 0x30850100\n.inst 0x3a000009\n.inst 0xe59f1024\n.inst 0xe5911000\n.inst 0xe59123ec\n.inst 0xe59113f0\n.inst 0xe0822000\n.inst 0xe1540002\n.inst 0x30440000\n.inst 0x30800080\n.inst 0x30810100\n.inst 0x23a00000\n.inst 0xe8bd8070\n.word 0x00433158\n");
}

// DECOMP_FUNC(0x002879c0, 124)
extern "C" __attribute__((naked)) void ui_func_002879c0() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe59f406c\n.inst 0xe5940004\n.inst 0xe3500065\n.inst 0x1a000004\n.inst 0xe3a01006\n.inst 0xe3a0001c\n.inst 0xeb007a85\n.inst 0xe3500000\n.inst 0x0a000012\n.inst 0xe5940004\n.inst 0xe3500066\n.inst 0x1a000005\n.inst 0xe3a01007\n.inst 0xe3a0001c\n.inst 0xeb007a7d\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000009\n.inst 0xe5940004\n.inst 0xe3500067\n.inst 0x1a000005\n.inst 0xe3a01008\n.inst 0xe3a0001c\n.inst 0xeb007a74\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000000\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.word 0x0044cf60\n");
}

// DECOMP_FUNC(0x00287ce0, 116)
extern "C" __attribute__((naked)) void script_vm_func_00287ce0() {
    asm volatile(".arm\n.inst 0xee320a40\n.inst 0xee730a41\n.inst 0xe92d4010\n.inst 0xed2d8b02\n.inst 0xeeb08a61\n.inst 0xebffe8ea\n.inst 0xeef00a40\n.inst 0xed9f1a10\n.inst 0xed9f2a10\n.inst 0xed9f0a10\n.inst 0xe59f1040\n.inst 0xee600a81\n.inst 0xeef40ac2\n.inst 0xeef1fa10\n.inst 0x3e700a80\n.inst 0xee100a90\n.inst 0xe1500001\n.inst 0xce700ac0\n.inst 0xeeb00a48\n.inst 0xeb000010\n.inst 0xeeb40ac2\n.inst 0xeef1fa10\n.inst 0xecbd8b02\n.inst 0x3eb10a40\n.inst 0xe8bd8010\n.word 0x42654ca3\n.word 0x00000000\n.word 0x43b40000\n.word 0x43b40000\n");
}

// DECOMP_FUNC(0x00288990, 104)
extern "C" __attribute__((naked)) void ui_func_00288990() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a04000\n.inst 0xe1a06000\n.inst 0xe1a07004\n.inst 0xe0840104\n.inst 0xe0860200\n.inst 0xe2805010\n.inst 0xe5900018\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb007c38\n.inst 0xe5857008\n.inst 0xe595000c\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb00ee63\n.inst 0xe585700c\n.inst 0xe2844001\n.inst 0xe3540003\n.inst 0xbaffffef\n.inst 0xe5960008\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb007c2b\n.inst 0xe5867008\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x00289fdc, 112)
extern "C" __attribute__((naked)) void script_vm_func_00289fdc() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe24dd090\n.inst 0xe1a05000\n.inst 0xe1a04001\n.inst 0xe1a06002\n.inst 0xe3a01080\n.inst 0xe28d0010\n.inst 0xeb00eacc\n.inst 0xe28d3010\n.inst 0xe1a02004\n.inst 0xe3a01008\n.inst 0xe1a00005\n.inst 0xeb00746b\n.inst 0xe3500000\n.inst 0x0a000009\n.inst 0xe3a03000\n.inst 0xe3a02080\n.inst 0xe3a01001\n.inst 0xe88d000e\n.inst 0xe2803008\n.inst 0xe59f0014\n.inst 0xe1a02006\n.inst 0xe28d1010\n.inst 0xe5900000\n.inst 0xeb0069f9\n.inst 0xe28dd090\n.inst 0xe8bd8070\n.word 0x00433130\n");
}

// DECOMP_FUNC(0x0028a04c, 112)
extern "C" __attribute__((naked)) void script_vm_func_0028a04c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe24dd090\n.inst 0xe1a05000\n.inst 0xe1a04001\n.inst 0xe1a06002\n.inst 0xe3a01080\n.inst 0xe28d0010\n.inst 0xeb00eab0\n.inst 0xe28d3010\n.inst 0xe1a02004\n.inst 0xe3a01007\n.inst 0xe1a00005\n.inst 0xeb00744f\n.inst 0xe3500000\n.inst 0x0a000009\n.inst 0xe3a03000\n.inst 0xe3a02080\n.inst 0xe3a01001\n.inst 0xe88d000e\n.inst 0xe2803008\n.inst 0xe59f0014\n.inst 0xe1a02006\n.inst 0xe28d1010\n.inst 0xe5900000\n.inst 0xeb0069dd\n.inst 0xe28dd090\n.inst 0xe8bd8070\n.word 0x00433130\n");
}

// DECOMP_FUNC(0x0028c194, 112)
extern "C" __attribute__((naked)) void script_vm_func_0028c194() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe59f505c\n.inst 0xe5954000\n.inst 0xe3540000\n.inst 0x0a000013\n.inst 0xe59412f8\n.inst 0xe3510000\n.inst 0xba00000c\n.inst 0xe3a00018\n.inst 0xeb008a5b\n.inst 0xe5950000\n.inst 0xe3a01000\n.inst 0xe3500000\n.inst 0x15c012f4\n.inst 0xe59f002c\n.inst 0xe59422f8\n.inst 0xe3a01018\n.inst 0xe5900000\n.inst 0xeb00688b\n.inst 0xe3e00000\n.inst 0xe58402f8\n.inst 0xe2844fba\n.inst 0xe3a01000\n.inst 0xe3a00003\n.inst 0xe8840003\n.inst 0xe8bd8070\n.word 0x00434210\n.word 0x00433158\n");
}

// DECOMP_FUNC(0x0028ebd8, 108)
extern "C" __attribute__((naked)) void camp_func_0028ebd8() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a06001\n.inst 0xe1a04000\n.inst 0xe1a01000\n.inst 0xe59f0050\n.inst 0xe5900000\n.inst 0xeb00a9c9\n.inst 0xe3500000\n.inst 0x12800002\n.inst 0x1a00000e\n.inst 0xe3a01000\n.inst 0xe3a00001\n.inst 0xeb00c8ad\n.inst 0xe1a07000\n.inst 0xeb00c8a1\n.inst 0xe1a05000\n.inst 0xe1a00007\n.inst 0xeb00c88a\n.inst 0xe1500004\n.inst 0x91a00005\n.inst 0x9a000003\n.inst 0xe0840104\n.inst 0xe3560000\n.inst 0xe0850180\n.inst 0x12800010\n.inst 0xe8bd81f0\n.word 0x00433158\n");
}

// DECOMP_FUNC(0x0029117c, 112)
extern "C" __attribute__((naked)) void script_vm_func_0029117c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe3a00001\n.inst 0xeb00d1ab\n.inst 0xe3500000\n.inst 0x1a000011\n.inst 0xe59f1044\n.inst 0xe3a00000\n.inst 0xe5911004\n.inst 0xe3510000\n.inst 0x059f0038\n.inst 0x0a000001\n.inst 0xe3510001\n.inst 0x059f0030\n.inst 0xe590101c\n.inst 0xe3110002\n.inst 0x0a000006\n.inst 0xe311003c\n.inst 0x1a000004\n.inst 0xe3110040\n.inst 0x13811c02\n.inst 0xe5a04008\n.inst 0x03811010\n.inst 0xe5801014\n.inst 0xe8bd8010\n.word 0x0044e098\n.word 0x004c53c4\n.word 0x004c53e4\n");
}

// DECOMP_FUNC(0x00291c3c, 112)
extern "C" __attribute__((naked)) void script_vm_func_00291c3c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe59f4060\n.inst 0xe5940000\n.inst 0xe2500001\n.inst 0xe5840000\n.inst 0x1a000013\n.inst 0xe5940004\n.inst 0xe3500065\n.inst 0x1a000002\n.inst 0xe3a01006\n.inst 0xe3a0001c\n.inst 0xeb0073af\n.inst 0xe5940004\n.inst 0xe3500066\n.inst 0x1a000002\n.inst 0xe3a01007\n.inst 0xe3a0001c\n.inst 0xeb0073a9\n.inst 0xe5940004\n.inst 0xe3500067\n.inst 0x1a000002\n.inst 0xe3a01008\n.inst 0xe3a0001c\n.inst 0xeb0073a3\n.inst 0xe3a00000\n.inst 0xe5840004\n.inst 0xe8bd8010\n.word 0x0044cf60\n");
}

// DECOMP_FUNC(0x0029350c, 112)
extern "C" __attribute__((naked)) void script_vm_func_0029350c() {
    asm volatile(".arm\n.inst 0xe59f0064\n.inst 0xe92d4070\n.inst 0xe3a02000\n.inst 0xe3a01004\n.inst 0xe5904000\n.inst 0xe594002c\n.inst 0xe2200001\n.inst 0xe584002c\n.inst 0xe2840d06\n.inst 0xeb00a962\n.inst 0xe3a05000\n.inst 0xe594102c\n.inst 0xe0840105\n.inst 0xe59006c8\n.inst 0xeb000139\n.inst 0xe2855001\n.inst 0xe3550004\n.inst 0xbafffff8\n.inst 0xe3a05000\n.inst 0xe594102c\n.inst 0xe0840105\n.inst 0xe59006d8\n.inst 0xeb000131\n.inst 0xe2855001\n.inst 0xe3550018\n.inst 0xbafffff8\n.inst 0xe8bd8070\n.word 0x0043dcf0\n");
}

// DECOMP_FUNC(0x0029357c, 112)
extern "C" __attribute__((naked)) void script_vm_func_0029357c() {
    asm volatile(".arm\n.inst 0xe59f0064\n.inst 0xe92d4070\n.inst 0xe3a02000\n.inst 0xe3a01005\n.inst 0xe5904000\n.inst 0xe594002c\n.inst 0xe2200001\n.inst 0xe584002c\n.inst 0xe2840d06\n.inst 0xeb00a946\n.inst 0xe3a05000\n.inst 0xe594102c\n.inst 0xe0840105\n.inst 0xe59006c8\n.inst 0xeb00011d\n.inst 0xe2855001\n.inst 0xe3550004\n.inst 0xbafffff8\n.inst 0xe3a05000\n.inst 0xe594102c\n.inst 0xe0840105\n.inst 0xe59006d8\n.inst 0xeb000115\n.inst 0xe2855001\n.inst 0xe3550018\n.inst 0xbafffff8\n.inst 0xe8bd8070\n.word 0x0043dcf0\n");
}

// DECOMP_FUNC(0x00293c2c, 108)
extern "C" __attribute__((naked)) void camp_func_00293c2c() {
    asm volatile(".arm\n.inst 0xe59f1060\n.inst 0xe92d4070\n.inst 0xe7911000\n.inst 0xe3110040\n.inst 0x1a000012\n.inst 0xe2800b0b\n.inst 0xe2800fcd\n.inst 0xe5900000\n.inst 0xe2400001\n.inst 0xe3500003\n.inst 0x83a05000\n.inst 0x81a04005\n.inst 0x9a00000a\n.inst 0xe1a00004\n.inst 0xebff6d7c\n.inst 0xe1d004b8\n.inst 0xe2844001\n.inst 0xe3500000\n.inst 0x12855001\n.inst 0xe354000c\n.inst 0xbafffff7\n.inst 0xe3550001\n.inst 0xb3a00000\n.inst 0xba000000\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x000044a8\n");
}

// DECOMP_FUNC(0x002940ac, 112)
extern "C" __attribute__((naked)) void ui_func_002940ac() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe3a01000\n.inst 0xed2d8b04\n.inst 0xeeb08b40\n.inst 0xeeb09a41\n.inst 0xe5900008\n.inst 0xeef00a68\n.inst 0xeeb00a48\n.inst 0xe5900008\n.inst 0xebff2005\n.inst 0xe3a04000\n.inst 0xe0840104\n.inst 0xe0850200\n.inst 0xe5900018\n.inst 0xe3500000\n.inst 0x0a000005\n.inst 0xeeb01a49\n.inst 0xeef00a68\n.inst 0xeeb00a48\n.inst 0xe5900008\n.inst 0xe3a01000\n.inst 0xebff1ff9\n.inst 0xe2844001\n.inst 0xe3540003\n.inst 0xbafffff1\n.inst 0xecbd8b04\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x00296154, 120)
extern "C" __attribute__((naked)) void script_vm_func_00296154() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe1a00001\n.inst 0xe1a01002\n.inst 0xeb00a559\n.inst 0xe590100c\n.inst 0xe3510000\n.inst 0x0a00000a\n.inst 0xe1d020b8\n.inst 0xe1d030ba\n.inst 0xe1d100f0\n.inst 0xe1d110f2\n.inst 0xe0800fa0\n.inst 0xe081cfa1\n.inst 0xe08210c0\n.inst 0xe08300cc\n.inst 0xe1c411b8\n.inst 0xe1c401ba\n.inst 0xe8bd8010\n.inst 0xe1d020b4\n.inst 0xe1d030b6\n.inst 0xe1d010b8\n.inst 0xe1d0c0ba\n.inst 0xe3c20902\n.inst 0xe3c32902\n.inst 0xe08100a0\n.inst 0xe08c10a2\n.inst 0xe1c401b8\n.inst 0xe1c411ba\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x00298a74, 112)
extern "C" __attribute__((naked)) void camp_func_00298a74() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe1a06001\n.inst 0xe3a04000\n.inst 0xe1a00001\n.inst 0xeb005658\n.inst 0xe3550000\n.inst 0xaa000008\n.inst 0xeb007714\n.inst 0xe1a05000\n.inst 0xe3a01001\n.inst 0xe1a00006\n.inst 0xeb000871\n.inst 0xe1d512fc\n.inst 0xe1500001\n.inst 0xca000009\n.inst 0xea000007\n.inst 0xe1a00005\n.inst 0xeb003fc8\n.inst 0xe1a05000\n.inst 0xe1a00006\n.inst 0xeb00083c\n.inst 0xe1d512fc\n.inst 0xe1510000\n.inst 0xba000000\n.inst 0xe3a04001\n.inst 0xe1a00004\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x00299874, 100)
extern "C" __attribute__((naked)) void engine_func_00299874() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xebfeb6b0\n.inst 0xe1a04000\n.inst 0xe1a00005\n.inst 0xeb006bcf\n.inst 0xe3500000\n.inst 0x0a00000d\n.inst 0xe5d00060\n.inst 0xe3100001\n.inst 0x0a000001\n.inst 0xe3540004\n.inst 0x0a000009\n.inst 0xe3100004\n.inst 0x0a000001\n.inst 0xe3540005\n.inst 0x0a000005\n.inst 0xe3100002\n.inst 0x0a000001\n.inst 0xe3540001\n.inst 0x0a000001\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x0029c084, 120)
extern "C" __attribute__((naked)) void camp_func_0029c084() {
    asm volatile(".arm\n.inst 0xe59f106c\n.inst 0xe92d0070\n.inst 0xe3a02000\n.inst 0xe3a04001\n.inst 0xe591c004\n.inst 0xe0801082\n.inst 0xe1d133b4\n.inst 0xe3530000\n.inst 0x11d113f4\n.inst 0x13510000\n.inst 0x0a00000c\n.inst 0xe3510f7d\n.inst 0x8a00000a\n.inst 0xe1a05fc1\n.inst 0xe28c3088\n.inst 0xe0815ea5\n.inst 0xe08331c5\n.inst 0xe2833b92\n.inst 0xe2833fcf\n.inst 0xe3c55007\n.inst 0xe5d36000\n.inst 0xe0411005\n.inst 0xe1861114\n.inst 0xe5c31000\n.inst 0xe2822001\n.inst 0xe3520008\n.inst 0xbaffffe9\n.inst 0xe8bd0070\n.inst 0xe12fff1e\n.word 0x0043e2a8\n");
}

// DECOMP_FUNC(0x002a135c, 116)
extern "C" __attribute__((naked)) void AsdMdlManager_func_002a135c() {
    asm volatile(".arm\n.inst 0xe92d4038\n.inst 0xe3a01065\n.inst 0xe59f0060\n.inst 0xe1a00000\n.inst 0xe3a00001\n.inst 0xe3a01c01\n.inst 0xe58d0000\n.inst 0xe3a0301c\n.inst 0xe3a02000\n.inst 0xe1a00001\n.inst 0xeb009059\n.inst 0xe3a01000\n.inst 0xe5801000\n.inst 0xe5801004\n.inst 0xe5801008\n.inst 0xe580100c\n.inst 0xe5801010\n.inst 0xe5801014\n.inst 0xe1a04000\n.inst 0xe5801018\n.inst 0xebfd742f\n.inst 0xe5942000\n.inst 0xe1a01000\n.inst 0xe5841008\n.inst 0xe3821602\n.inst 0xe1a00004\n.inst 0xe5841000\n.inst 0xe8bd8038\n.word 0x00409454\n");
}

// DECOMP_FUNC(0x002a4588, 120)
extern "C" __attribute__((naked)) void func_002a4588() {
    asm volatile(".arm\n.inst 0xe92d4030\n.inst 0xe24dd00c\n.inst 0xe1d020f6\n.inst 0xe1a03001\n.inst 0xe1904f9f\n.inst 0xe0425003\n.inst 0xe1550004\n.inst 0xe1a01002\n.inst 0xa0841003\n.inst 0xe1805f91\n.inst 0xe3550000\n.inst 0x1afffff7\n.inst 0xe3540000\n.inst 0xda000002\n.inst 0xe1d010f4\n.inst 0xe3510000\n.inst 0xda000008\n.inst 0xe59f1028\n.inst 0xe3a02000\n.inst 0xe1a05002\n.inst 0xe591c000\n.inst 0xe1a01002\n.inst 0xe88d0022\n.inst 0xe1a01000\n.inst 0xe1a0000c\n.inst 0xeb0010a9\n.inst 0xe28dd00c\n.inst 0xe1a00004\n.inst 0xe8bd8030\n.word 0x00471b58\n");
}

// DECOMP_FUNC(0x002a7fd8, 100)
extern "C" __attribute__((naked)) void func_002a7fd8() {
    asm volatile(".arm\n.inst 0xee301a60\n.inst 0xed9f2a15\n.inst 0xeddf1a13\n.inst 0xeeb41ac2\n.inst 0xeef1fa10\n.inst 0xeeb40ac2\n.inst 0x3eb11a41\n.inst 0xeef1fa10\n.inst 0x3eb10a40\n.inst 0xee200a21\n.inst 0xeeb40ac1\n.inst 0xeef1fa10\n.inst 0xaa000007\n.inst 0xeef40ac2\n.inst 0xeef1fa10\n.inst 0x3ef10a60\n.inst 0xee200aa1\n.inst 0xeeb40ac1\n.inst 0xeef1fa10\n.inst 0xb3a00000\n.inst 0xba000000\n.inst 0xe3a00001\n.inst 0xe12fff1e\n.word 0x34000000\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x002a8674, 112)
extern "C" __attribute__((naked)) void func_002a8674() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe1a04001\n.inst 0xed2d8b02\n.inst 0xeeb08a40\n.inst 0xeb004bc9\n.inst 0xe3500000\n.inst 0x0a000010\n.inst 0xe59f0044\n.inst 0xe3540000\n.inst 0xe19000b5\n.inst 0xe0850100\n.inst 0xe2800a01\n.inst 0xe59000a0\n.inst 0xe2801004\n.inst 0xe0811104\n.inst 0xed818a01\n.inst 0x05901000\n.inst 0x03811401\n.inst 0x0a000003\n.inst 0xe3540001\n.inst 0x05901000\n.inst 0x03811402\n.inst 0x1a000000\n.inst 0xe5801000\n.inst 0xecbd8b02\n.inst 0xe8bd8070\n.word 0x0000131e\n");
}

// DECOMP_FUNC(0x002a8cfc, 108)
extern "C" __attribute__((naked)) void func_002a8cfc() {
    asm volatile(".arm\n.inst 0xe92d4030\n.inst 0xe1b04000\n.inst 0xe24dd0c4\n.inst 0x028d4080\n.inst 0xe1a0000d\n.inst 0xebfa96bb\n.inst 0xe59f5048\n.inst 0xe28d0040\n.inst 0xe5951000\n.inst 0xeb005cb4\n.inst 0xe28d0040\n.inst 0xe1a0200d\n.inst 0xec900a08\n.inst 0xe28d0060\n.inst 0xe1a01004\n.inst 0xec840a08\n.inst 0xec900a08\n.inst 0xe2840020\n.inst 0xec800a08\n.inst 0xe1a00002\n.inst 0xeb003929\n.inst 0xe5950000\n.inst 0xe1a0100d\n.inst 0xeb0041b6\n.inst 0xe28dd0c4\n.inst 0xe8bd8030\n.word 0x0044ea00\n");
}

// DECOMP_FUNC(0x002aa48c, 120)
extern "C" __attribute__((naked)) void func_002aa48c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05002\n.inst 0xe59f2064\n.inst 0xe2804a01\n.inst 0xe7d20000\n.inst 0xe3500000\n.inst 0x059401e4\n.inst 0x01500001\n.inst 0x0a00000a\n.inst 0xe3510000\n.inst 0xe58411e4\n.inst 0x0a000007\n.inst 0xe2810014\n.inst 0xe5912034\n.inst 0xe8901001\n.inst 0xe5913030\n.inst 0xe1a0100c\n.inst 0xebfa90a2\n.inst 0xe3a00003\n.inst 0xe5c401e9\n.inst 0xe3a00000\n.inst 0xe5c401e8\n.inst 0xe5d401e9\n.inst 0xe1500005\n.inst 0x0a000002\n.inst 0xe1a00005\n.inst 0xebfa6c75\n.inst 0xe5c451e9\n.inst 0xe8bd8070\n.word 0x000011e8\n");
}

// DECOMP_FUNC(0x002ad714, 112)
extern "C" __attribute__((naked)) void func_002ad714() {
    asm volatile(".arm\n.inst 0xe92d43f0\n.inst 0xe1a07000\n.inst 0xe1a00001\n.inst 0xe1a01002\n.inst 0xe1a02003\n.inst 0xe28d301c\n.inst 0xe59d4028\n.inst 0xe8930120\n.inst 0xe59d6024\n.inst 0xebffebfc\n.inst 0xe1a09000\n.inst 0xe59f0030\n.inst 0xe59f1030\n.inst 0xe3a02ffa\n.inst 0xe1a0cfc4\n.inst 0xe0c03098\n.inst 0xe0ec4195\n.inst 0xe0e03296\n.inst 0xe59f801c\n.inst 0xe0931004\n.inst 0xe0a0000c\n.inst 0xe0e01899\n.inst 0xe5870004\n.inst 0xe5871000\n.inst 0xe8bd83f0\n.word 0x0000ea60\n.word 0x0036ee80\n.word 0x05265c00\n");
}

// DECOMP_FUNC(0x002b2814, 120)
extern "C" __attribute__((naked)) void AsdList_func_002b2814() {
    asm volatile(".arm\n.inst 0xe92d40f8\n.inst 0xe1a04001\n.inst 0xe1a06000\n.inst 0xe59f0060\n.inst 0xe1a05002\n.inst 0xe3a01035\n.inst 0xe1a00000\n.inst 0xe3a00001\n.inst 0xe3a01c01\n.inst 0xe58d0000\n.inst 0xe3a0301c\n.inst 0xe3a02000\n.inst 0xe1a00001\n.inst 0xeb004b28\n.inst 0xe3a01000\n.inst 0xe5801000\n.inst 0xe5801004\n.inst 0xe580100c\n.inst 0xe5801014\n.inst 0xe5801018\n.inst 0xe5804008\n.inst 0xe1a04000\n.inst 0xe1a01000\n.inst 0xe5805010\n.inst 0xe3e02000\n.inst 0xe1a00006\n.inst 0xebfa6f71\n.inst 0xe1a00004\n.inst 0xe8bd80f8\n.word 0x0041037c\n");
}

// DECOMP_FUNC(0x002b4ddc, 104)
extern "C" __attribute__((naked)) void func_002b4ddc() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe5d00014\n.inst 0xe3500000\n.inst 0x0a000013\n.inst 0xe5950008\n.inst 0xe3a06000\n.inst 0xe1a04006\n.inst 0xe3500000\n.inst 0xda000008\n.inst 0xe7950104\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb002202\n.inst 0xe7856104\n.inst 0xe5950008\n.inst 0xe2844001\n.inst 0xe1500004\n.inst 0xcafffff6\n.inst 0xe5856008\n.inst 0xeb00190f\n.inst 0xe1a01005\n.inst 0xe320f000\n.inst 0xebfa9e1f\n.inst 0xe5c56014\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002b8adc, 104)
extern "C" __attribute__((naked)) void ui_func_002b8adc() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe59f5058\n.inst 0xe5954000\n.inst 0xe3540000\n.inst 0x0a00000f\n.inst 0xe5940000\n.inst 0xebffe68d\n.inst 0xe3500000\n.inst 0x1a00000d\n.inst 0xe5d40008\n.inst 0xe3500000\n.inst 0x0a00000a\n.inst 0xe5950000\n.inst 0xe3500000\n.inst 0x0a000005\n.inst 0xe28000ec\n.inst 0xebffdd9f\n.inst 0xe5950000\n.inst 0xeb002e0d\n.inst 0xe3a00000\n.inst 0xe5850000\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x00447060\n");
}

// DECOMP_FUNC(0x002b902c, 104)
extern "C" __attribute__((naked)) void ui_func_002b902c() {
    asm volatile(".arm\n.inst 0xe350001f\n.inst 0xe92d4010\n.inst 0x2a00000d\n.inst 0xe59f104c\n.inst 0xe5912008\n.inst 0xe3120001\n.inst 0x13a00000\n.inst 0x0a00000a\n.inst 0xe591200c\n.inst 0xe1500002\n.inst 0x9a000005\n.inst 0xe5911010\n.inst 0xe0400002\n.inst 0xeb0036ea\n.inst 0xe3510000\n.inst 0x03a00001\n.inst 0x0a000000\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe59f2010\n.inst 0xe7920100\n.inst 0xe3500001\n.inst 0x1afffff0\n.inst 0xe8bd8010\n.word 0x004650a0\n.word 0x004e3c58\n");
}

// DECOMP_FUNC(0x002be4dc, 108)
extern "C" __attribute__((naked)) void func_002be4dc() {
    asm volatile(".arm\n.inst 0xe1a01400\n.inst 0xe1a03800\n.inst 0xe1a01c21\n.inst 0xe1a02c20\n.inst 0xee001a90\n.inst 0xe1a00c23\n.inst 0xee012a10\n.inst 0xee010a90\n.inst 0xe52de004\n.inst 0xe24dd014\n.inst 0xeeb82a60\n.inst 0xed9f0a0c\n.inst 0xeef80a41\n.inst 0xeef81a61\n.inst 0xed8d0a03\n.inst 0xed9f0a09\n.inst 0xe1a0000d\n.inst 0xee221a00\n.inst 0xee600a80\n.inst 0xee210a80\n.inst 0xed8d0a02\n.inst 0xeccd0a02\n.inst 0xebffbf62\n.inst 0xe28dd014\n.inst 0xe49df004\n.word 0x3f800000\n.word 0x3b808081\n");
}

// DECOMP_FUNC(0x002c1570, 104)
extern "C" __attribute__((naked)) void nn_sdk_func_002c1570() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe59f404c\n.inst 0xe1a00004\n.inst 0xeb000949\n.inst 0xe59f1044\n.inst 0xe5910000\n.inst 0xe3500000\n.inst 0xda000006\n.inst 0xe2800001\n.inst 0xe5810000\n.inst 0xe59f5030\n.inst 0xe1a00004\n.inst 0xeb00091f\n.inst 0xe1a00005\n.inst 0xe8bd8070\n.inst 0xe59f0020\n.inst 0xebf96de4\n.inst 0xe1a05000\n.inst 0xe1a00004\n.inst 0xeb000918\n.inst 0xe1a00005\n.inst 0xe8bd8070\n.word 0x004e9ba8\n.word 0x00471b90\n.word 0x082067f9\n.word 0x0040b6e4\n");
}

// DECOMP_FUNC(0x002c8630, 104)
extern "C" __attribute__((naked)) void script_vm_func_002c8630() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xebffe937\n.inst 0xe2440019\n.inst 0xe3500005\n.inst 0x9a000001\n.inst 0xe3540066\n.inst 0x1a000004\n.inst 0xe3a00f51\n.inst 0xebffe153\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a00000a\n.inst 0xe244001f\n.inst 0xe3500004\n.inst 0x9a000001\n.inst 0xe3540067\n.inst 0x1a000004\n.inst 0xe59f0014\n.inst 0xebffe149\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000000\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.word 0x0000015a\n");
}

// DECOMP_FUNC(0x002c9b3c, 104)
extern "C" __attribute__((naked)) void script_vm_func_002c9b3c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe3a01003\n.inst 0xe3a00023\n.inst 0xebffdcdc\n.inst 0xe1a06000\n.inst 0xebffdcd0\n.inst 0xe1a05000\n.inst 0xe1a00006\n.inst 0xebffdcb9\n.inst 0xe1540000\n.inst 0x30840104\n.inst 0x30850100\n.inst 0x3a000009\n.inst 0xe59f1024\n.inst 0xe5911000\n.inst 0xe59123fc\n.inst 0xe5911400\n.inst 0xe0822000\n.inst 0xe1540002\n.inst 0x30440000\n.inst 0x30800100\n.inst 0x30810100\n.inst 0x23a00000\n.inst 0xe8bd8070\n.word 0x00433158\n");
}

// DECOMP_FUNC(0x002cd754, 116)
extern "C" __attribute__((naked)) void ui_func_002cd754() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xebff194e\n.inst 0xe2800a02\n.inst 0xe5900234\n.inst 0xe8bd4010\n.inst 0xe1a00000\n.inst 0xe92d4030\n.inst 0xe1a04000\n.inst 0xe24dd00c\n.inst 0xe3a00000\n.inst 0xebff25f7\n.inst 0xe1a05000\n.inst 0xebfeefad\n.inst 0xe59f1034\n.inst 0xe1a02000\n.inst 0xe1a00004\n.inst 0xe5911004\n.inst 0xe3510000\n.inst 0x13a03014\n.inst 0x15c13a11\n.inst 0xe3a01000\n.inst 0xe58d1000\n.inst 0xe58d1004\n.inst 0xe3a0300b\n.inst 0xe1a01005\n.inst 0xebfee45a\n.inst 0xe28dd00c\n.inst 0xe8bd8030\n.word 0x0043e188\n");
}

// DECOMP_FUNC(0x002cd880, 104)
extern "C" __attribute__((naked)) void engine_func_002cd880() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xebfeef6d\n.inst 0xe3500000\n.inst 0x0a000007\n.inst 0xe59f0048\n.inst 0xe5900000\n.inst 0xe5901010\n.inst 0xe5900014\n.inst 0xe1510000\n.inst 0x03a00001\n.inst 0x13a00000\n.inst 0xe8bd8010\n.inst 0xe3a00000\n.inst 0xebff25a9\n.inst 0xe1a04000\n.inst 0xe3a00001\n.inst 0xebff25a6\n.inst 0xe1a01000\n.inst 0xed9f0a05\n.inst 0xe3a02001\n.inst 0xe1a00004\n.inst 0xebfe2f20\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.word 0x0043e088\n.word 0x3f800000\n");
}

// DECOMP_FUNC(0x002cde1c, 96)
extern "C" __attribute__((naked)) void camp_func_002cde1c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe3a01000\n.inst 0xe3a00025\n.inst 0xebffcc24\n.inst 0xe1a06000\n.inst 0xebffcc18\n.inst 0xe1a04000\n.inst 0xe1a00006\n.inst 0xebffcc01\n.inst 0xe2501000\n.inst 0xe3a00000\n.inst 0x9a000008\n.inst 0xe1d420d0\n.inst 0xe1520005\n.inst 0x1a000001\n.inst 0xe1a00004\n.inst 0xe8bd8070\n.inst 0xe2800001\n.inst 0xe1510000\n.inst 0xe2844020\n.inst 0x8afffff6\n.inst 0xe3a00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002d14d8, 120)
extern "C" __attribute__((naked)) void engine_func_002d14d8() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a08000\n.inst 0xe590009c\n.inst 0xebfe602c\n.inst 0xe598009c\n.inst 0xe5907008\n.inst 0xe3570000\n.inst 0x15901010\n.inst 0x13510000\n.inst 0x0a000012\n.inst 0xe1d810bc\n.inst 0xe5904018\n.inst 0xe59860a0\n.inst 0xe3510003\n.inst 0x1a00000d\n.inst 0xe3570000\n.inst 0xe3a05000\n.inst 0xda00000a\n.inst 0xe5940010\n.inst 0xe3500000\n.inst 0x1a000002\n.inst 0xe1a01006\n.inst 0xe1a00008\n.inst 0xeb00c3d6\n.inst 0xe2855001\n.inst 0xe1550007\n.inst 0xe2844028\n.inst 0xe286601c\n.inst 0xbafffff4\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x002db9d0, 112)
extern "C" __attribute__((naked)) void engine_func_002db9d0() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfeed60\n.inst 0xe1a05000\n.inst 0xe3a00001\n.inst 0xebfeed5d\n.inst 0xe2504000\n.inst 0xaa000003\n.inst 0xe2641000\n.inst 0xe1a00005\n.inst 0xebfdd571\n.inst 0xea000002\n.inst 0xe1a01000\n.inst 0xe1a00005\n.inst 0xebfee8ab\n.inst 0xe320f000\n.inst 0xebffc84e\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000004\n.inst 0xe59f0014\n.inst 0xebff75e6\n.inst 0xe1a00004\n.inst 0xe320f000\n.inst 0xebfcd76c\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x01000174\n");
}

// DECOMP_FUNC(0x002dbad4, 120)
extern "C" __attribute__((naked)) void battle_func_002dbad4() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfeed1f\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfee069\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000007\n.inst 0xe3110040\n.inst 0x01d00cbe\n.inst 0x01500005\n.inst 0x1a000003\n.inst 0xe3a00001\n.inst 0xebfec90a\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffea\n.inst 0xe3a00000\n.inst 0xebfec903\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002dca98, 96)
extern "C" __attribute__((naked)) void func_002dca98() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04001\n.inst 0xe1d010b2\n.inst 0xe3510000\n.inst 0xe1d410b2\n.inst 0x0a000009\n.inst 0xe3510000\n.inst 0x03e00000\n.inst 0x0a000005\n.inst 0xe1d000b0\n.inst 0xebfeae2e\n.inst 0xe1a05000\n.inst 0xe1d400b0\n.inst 0xebfeae2b\n.inst 0xe0400005\n.inst 0xe8bd8070\n.inst 0xe3510000\n.inst 0x03a00000\n.inst 0x13a00001\n.inst 0xe8bd8070\n.inst 0xe5d00000\n.inst 0xe5d11000\n.inst 0xe0400001\n.inst 0xe12fff1e\n");
}

// DECOMP_FUNC(0x002e0c54, 108)
extern "C" __attribute__((naked)) void ui_func_002e0c54() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xebff7fcd\n.inst 0xe3500000\n.inst 0x0a000013\n.inst 0xe59f104c\n.inst 0xe59f204c\n.inst 0xe5d15000\n.inst 0xe182c342\n.inst 0xe1e0300c\n.inst 0xe7c25000\n.inst 0xe5d15001\n.inst 0xe08cc000\n.inst 0xe0404003\n.inst 0xe5cc5000\n.inst 0xe5d1c002\n.inst 0xe04368c2\n.inst 0xe0402006\n.inst 0xe5c4c000\n.inst 0xe5d11003\n.inst 0xe2800909\n.inst 0xe2800d2e\n.inst 0xe3a03001\n.inst 0xe5c21000\n.inst 0xe5c03000\n.inst 0xe8bd8070\n.word 0x0044e0f8\n.word 0x00024b7c\n");
}

// DECOMP_FUNC(0x002e3304, 124)
extern "C" __attribute__((naked)) void camp_func_002e3304() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a06000\n.inst 0xeb010390\n.inst 0xe2505000\n.inst 0xe3a04000\n.inst 0x9a000013\n.inst 0xe6ff0074\n.inst 0xebfd951a\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a00000f\n.inst 0xe1d000b0\n.inst 0xe1500006\n.inst 0x1a00000c\n.inst 0xebfef71a\n.inst 0xe1a01fc4\n.inst 0xe3a03001\n.inst 0xe0841ea1\n.inst 0xe08021c1\n.inst 0xe3c11007\n.inst 0xe0441001\n.inst 0xe5f20035\n.inst 0xe1a01113\n.inst 0xe1100001\n.inst 0x01800001\n.inst 0x05c20000\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe1540005\n.inst 0x3affffe7\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002e3bb0, 120)
extern "C" __attribute__((naked)) void battle_func_002e3bb0() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfec035\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000006\n.inst 0xe3110040\n.inst 0x1a000004\n.inst 0xe1d00cbe\n.inst 0xebff55dc\n.inst 0xe5d00005\n.inst 0xe3500004\n.inst 0x0a000006\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffeb\n.inst 0xe3a00000\n.inst 0xebfea8d0\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe3a00001\n.inst 0xebfea8cc\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002ed404, 120)
extern "C" __attribute__((naked)) void camp_func_002ed404() {
    asm volatile(".arm\n.inst 0xe59f2068\n.inst 0xe92d4038\n.inst 0xe3a01001\n.inst 0xe5924008\n.inst 0xe5c4107e\n.inst 0xe5c4107c\n.inst 0xe5840068\n.inst 0xebfe8a6f\n.inst 0xe584006c\n.inst 0xe5840078\n.inst 0xe3a0100b\n.inst 0xe2840b01\n.inst 0xe28430a4\n.inst 0xe2800fd5\n.inst 0xe58d1000\n.inst 0xed9f0a0c\n.inst 0xe3e02000\n.inst 0xe3a0100e\n.inst 0xe1a04000\n.inst 0xebff41b5\n.inst 0xe3a0100a\n.inst 0xe1a00004\n.inst 0xebff2f1f\n.inst 0xe3a01006\n.inst 0xe1a00004\n.inst 0xebff46f0\n.inst 0xe3a00001\n.inst 0xe8bd8038\n.word 0x0043e188\n.word 0x3f800000\n");
}

// DECOMP_FUNC(0x002f067c, 112)
extern "C" __attribute__((naked)) void engine_func_002f067c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe9a35\n.inst 0xe3500000\n.inst 0xe3a04000\n.inst 0x03a04007\n.inst 0x0a000004\n.inst 0xe3500001\n.inst 0x03a0400a\n.inst 0x0a000001\n.inst 0xe3500002\n.inst 0x03a0400b\n.inst 0xe3a00001\n.inst 0xebfe9a2a\n.inst 0xe1a05000\n.inst 0xe59f0028\n.inst 0xe5900000\n.inst 0xebfe3934\n.inst 0xe5900020\n.inst 0xe0800084\n.inst 0xe1d007f2\n.inst 0xe1500005\n.inst 0x03a00001\n.inst 0x13a00000\n.inst 0xebfe761c\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x0043427c\n");
}

// DECOMP_FUNC(0x002f3b78, 104)
extern "C" __attribute__((naked)) void script_vm_func_002f3b78() {
    asm volatile(".arm\n.inst 0xe59f005c\n.inst 0xe3a01000\n.inst 0xe3a0c006\n.inst 0xe5903000\n.inst 0xe3a00065\n.inst 0xe0000091\n.inst 0xe0830100\n.inst 0xe5f021d0\n.inst 0xe3520000\n.inst 0x0a00000a\n.inst 0xe5902014\n.inst 0xe352001d\n.inst 0x13520026\n.inst 0x0a000003\n.inst 0xe352001e\n.inst 0x1352001f\n.inst 0x13520025\n.inst 0x1a000002\n.inst 0xe5902004\n.inst 0xe3520008\n.inst 0x0580c004\n.inst 0xe2811001\n.inst 0xe3510080\n.inst 0xbaffffeb\n.inst 0xe12fff1e\n.word 0x00447a78\n");
}

// DECOMP_FUNC(0x002f4a2c, 120)
extern "C" __attribute__((naked)) void engine_func_002f4a2c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xebfe5302\n.inst 0xe3500000\n.inst 0x0a000006\n.inst 0xebff3539\n.inst 0xe3500000\n.inst 0xe3a00000\n.inst 0x0a00000e\n.inst 0xebfe4bcf\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe320f000\n.inst 0xebff3531\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x1a00000b\n.inst 0xe3a00000\n.inst 0xebfe893a\n.inst 0xe1a01000\n.inst 0xe3a00000\n.inst 0xebfeaefd\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe320f000\n.inst 0xebff1094\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0affffed\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002f5dc0, 96)
extern "C" __attribute__((naked)) void engine_func_002f5dc0() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe59f6050\n.inst 0xe5965000\n.inst 0xe5950138\n.inst 0xeb00973a\n.inst 0xe3a04000\n.inst 0xe0850104\n.inst 0xe590012c\n.inst 0xeb00501d\n.inst 0xe2844001\n.inst 0xe3540003\n.inst 0xbafffff9\n.inst 0xe5950160\n.inst 0xebff3959\n.inst 0xe5950000\n.inst 0xe3a01000\n.inst 0xebff39ec\n.inst 0xe1a00005\n.inst 0xe320f000\n.inst 0xebff3953\n.inst 0xe3a00000\n.inst 0xe5860000\n.inst 0xe8bd8070\n.word 0x0043db10\n");
}

// DECOMP_FUNC(0x002f6d84, 120)
extern "C" __attribute__((naked)) void battle_func_002f6d84() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe73c0\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000006\n.inst 0xe3110040\n.inst 0x1a000004\n.inst 0xe1d00cbe\n.inst 0xebff0967\n.inst 0xe5d00005\n.inst 0xe3500005\n.inst 0x0a000006\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffeb\n.inst 0xe3a00000\n.inst 0xebfe5c5b\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe3a00001\n.inst 0xebfe5c57\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002f6dfc, 116)
extern "C" __attribute__((naked)) void battle_func_002f6dfc() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe73a2\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000009\n.inst 0xe3110040\n.inst 0x1a000007\n.inst 0xebfd40cd\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000003\n.inst 0xe3a00001\n.inst 0xebfe5c41\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe8\n.inst 0xe3a00000\n.inst 0xebfe5c3a\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002f701c, 96)
extern "C" __attribute__((naked)) void ui_func_002f701c() {
    asm volatile(".arm\n.inst 0xe3a00000\n.inst 0xe92d4010\n.inst 0xebfe7fcd\n.inst 0xe1a04000\n.inst 0xebfe7319\n.inst 0xebfd4ab5\n.inst 0xe3500000\n.inst 0x0a00000b\n.inst 0xe28000cc\n.inst 0xe1d02eb8\n.inst 0xe1d01efa\n.inst 0xe3a00064\n.inst 0xe1600082\n.inst 0xebff3c41\n.inst 0xe1500004\n.inst 0xca000003\n.inst 0xe3a00001\n.inst 0xebfe5bbb\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe3a00000\n.inst 0xebfe5bb7\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002f7108, 96)
extern "C" __attribute__((naked)) void battle_func_002f7108() {
    asm volatile(".arm\n.inst 0xe3a00000\n.inst 0xe92d4010\n.inst 0xebfe7f92\n.inst 0xe1a04000\n.inst 0xe59f0044\n.inst 0xe5900000\n.inst 0xebfe1e9c\n.inst 0xe5901028\n.inst 0xe0810084\n.inst 0xe2800c01\n.inst 0xe1d002b6\n.inst 0xe3100b3f\n.inst 0x13a01002\n.inst 0x11510520\n.inst 0x1a000003\n.inst 0xe3a00001\n.inst 0xebfe5b81\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe3a00000\n.inst 0xebfe5b7d\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.word 0x0043427c\n");
}

// DECOMP_FUNC(0x002fb54c, 124)
extern "C" __attribute__((naked)) void engine_func_002fb54c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xebfe383a\n.inst 0xe3500000\n.inst 0x0a000006\n.inst 0xebff1a71\n.inst 0xe3500000\n.inst 0xe3a00000\n.inst 0x0a00000f\n.inst 0xebfe3107\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe320f000\n.inst 0xebff1a69\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x1a00000c\n.inst 0xe3a00000\n.inst 0xebfe6e72\n.inst 0xe1a01000\n.inst 0xe3e02000\n.inst 0xe3a00000\n.inst 0xebfe842e\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe320f000\n.inst 0xebfef5cb\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0affffec\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002fc9d4, 112)
extern "C" __attribute__((naked)) void camp_func_002fc9d4() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a06001\n.inst 0xe59f405c\n.inst 0xe2845063\n.inst 0xe1a00004\n.inst 0xebfe48a2\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a00000c\n.inst 0xe1a00004\n.inst 0xebfe4cf8\n.inst 0xe1a01000\n.inst 0xe1a00004\n.inst 0xebfd516d\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xebfe9164\n.inst 0xe08001a4\n.inst 0xe2041007\n.inst 0xe5d02044\n.inst 0xe1821116\n.inst 0xe5c01044\n.inst 0xe2844001\n.inst 0xe1540005\n.inst 0x9affffea\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x0000079f\n");
}

// DECOMP_FUNC(0x002febb4, 112)
extern "C" __attribute__((naked)) void engine_func_002febb4() {
    asm volatile(".arm\n.inst 0xe92d4038\n.inst 0xe3a00000\n.inst 0xe1cd00b0\n.inst 0xe1dd00b2\n.inst 0xe1a00520\n.inst 0xe1a00500\n.inst 0xe1cd00b2\n.inst 0xe3a00000\n.inst 0xebfe60e1\n.inst 0xe1a04000\n.inst 0xebfebe9b\n.inst 0xe3500009\n.inst 0x1a000005\n.inst 0xe59f1030\n.inst 0xe3a03000\n.inst 0xe1a00004\n.inst 0xe1a02001\n.inst 0xeb029df4\n.inst 0xe1a04000\n.inst 0xe1a0000d\n.inst 0xe1cd40b0\n.inst 0xebfd1eb3\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xebfe3cce\n.inst 0xe3a00001\n.inst 0xe8bd8038\n.word 0x0000ffff\n");
}

// DECOMP_FUNC(0x002fec44, 124)
extern "C" __attribute__((naked)) void script_vm_func_002fec44() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe59f6064\n.inst 0xe3a00001\n.inst 0xe5964000\n.inst 0xe5c405f2\n.inst 0xe1a00005\n.inst 0xebfe696f\n.inst 0xe59f1050\n.inst 0xe5c405c4\n.inst 0xe18150b4\n.inst 0xebfd4758\n.inst 0xe3a01001\n.inst 0xe1a00005\n.inst 0xebfe450b\n.inst 0xe3a02000\n.inst 0xe1a01002\n.inst 0xe2840034\n.inst 0xebfefb8b\n.inst 0xe5960000\n.inst 0xe3a01001\n.inst 0xe5902004\n.inst 0xe5802008\n.inst 0xe5a01004\n.inst 0xe3a02000\n.inst 0xe580200c\n.inst 0xe3a0001c\n.inst 0xe584000c\n.inst 0xe8bd8070\n.word 0x0043dd50\n.word 0x0000097e\n");
}

// DECOMP_FUNC(0x002fff20, 112)
extern "C" __attribute__((naked)) void battle_func_002fff20() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xebfe4f5b\n.inst 0xe1a04000\n.inst 0xeb00db61\n.inst 0xebfedbca\n.inst 0xe2800c06\n.inst 0xe1d050b6\n.inst 0xebfedbc7\n.inst 0xe2800c06\n.inst 0xe1a01005\n.inst 0xe1d000f4\n.inst 0xebfedb90\n.inst 0xe1d005ba\n.inst 0xe3a01000\n.inst 0xe2800001\n.inst 0xe6bf0070\n.inst 0xebfe5180\n.inst 0xe2841901\n.inst 0xe2811e4a\n.inst 0xe59f0018\n.inst 0xe5912000\n.inst 0xe3822402\n.inst 0xe5812000\n.inst 0xe5900000\n.inst 0xeb02ba2e\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x00439ca8\n");
}
