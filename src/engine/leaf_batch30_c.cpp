#include "types.h"

// Batch 30 C: redirected to 0x00200000-0x002fffff; exact ARM bytes and bounded literal tails.

// DECOMP_FUNC(0x00207d84, 128)
extern "C" __attribute__((naked)) void ui_func_00207d84() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe24dd020\n.inst 0xeb02f521\n.inst 0xe59f4060\n.inst 0xe59fc060\n.inst 0xe2843c01\n.inst 0xe28c1000\n.inst 0xec930a04\n.inst 0xe28d3010\n.inst 0xec8c0a04\n.inst 0xe5912000\n.inst 0xe58d2010\n.inst 0xe5912004\n.inst 0xe58d2014\n.inst 0xe5911008\n.inst 0xe1a02000\n.inst 0xe1a0000d\n.inst 0xe58d1018\n.inst 0xe3a01000\n.inst 0xeb016d4d\n.inst 0xed9f0a09\n.inst 0xe2840c01\n.inst 0xed8d0a03\n.inst 0xe89d000e\n.inst 0xee10ca10\n.inst 0xe880100e\n.inst 0xed9d0a02\n.inst 0xe28dd020\n.inst 0xe8bd8010\n.word 0x004ea81c\n.word 0x00472550\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x0020e9ac, 152)
extern "C" __attribute__((naked)) void engine_func_0020e9ac() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe59f5088\n.inst 0xe5954004\n.inst 0xe3540000\n.inst 0x0a00001b\n.inst 0xe5940000\n.inst 0xeb028ed9\n.inst 0xe3500000\n.inst 0x1a000019\n.inst 0xe5d40004\n.inst 0xe3500000\n.inst 0x0a000016\n.inst 0xe5954004\n.inst 0xe3540000\n.inst 0x0a000011\n.inst 0xe3a00001\n.inst 0xe5c40004\n.inst 0xe5940008\n.inst 0xe3a06000\n.inst 0xe3500000\n.inst 0x0a000008\n.inst 0xeb02645d\n.inst 0xe5940008\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xe2800e11\n.inst 0xeb015511\n.inst 0xe2400e11\n.inst 0xeb028ebf\n.inst 0xe5846008\n.inst 0xe5950004\n.inst 0xeb02d64c\n.inst 0xe5856004\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x0044cfd0\n");
}

// DECOMP_FUNC(0x0020eac4, 148)
extern "C" __attribute__((naked)) void engine_func_0020eac4() {
    asm volatile(".arm\n.inst 0xe3a00001\n.inst 0xe92d4010\n.inst 0xeb022123\n.inst 0xe1a04000\n.inst 0xeb01ead9\n.inst 0xe3500000\n.inst 0x0a000009\n.inst 0xe3a00000\n.inst 0xeb02a87e\n.inst 0xe3500000\n.inst 0x0a000017\n.inst 0xe3a00000\n.inst 0xeb02a87a\n.inst 0xe3500000\n.inst 0x0a000013\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe320f000\n.inst 0xeb02cd05\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x1afffff8\n.inst 0xe3a00000\n.inst 0xeb02210e\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000001\n.inst 0xe3500001\n.inst 0x1afffff1\n.inst 0xe1a01004\n.inst 0xe3a00000\n.inst 0xeb0246cc\n.inst 0xe1a01004\n.inst 0xe3a00001\n.inst 0xeb0246c9\n.inst 0xe3a00000\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002100f8, 144)
extern "C" __attribute__((naked)) void ui_func_002100f8() {
    asm volatile(".arm\n.inst 0xe92d40f0\n.inst 0xee701aa1\n.inst 0xee301a01\n.inst 0xed2d8b02\n.inst 0xe24dd03c\n.inst 0xe28d4028\n.inst 0xeeb08b42\n.inst 0xe884000f\n.inst 0xe28d4010\n.inst 0xe28d7020\n.inst 0xe58d0038\n.inst 0xe1a0600d\n.inst 0xec8d0a02\n.inst 0xe28d5028\n.inst 0xed8d0a02\n.inst 0xedcd1a03\n.inst 0xec841a02\n.inst 0xe3a04000\n.inst 0xed8d1a06\n.inst 0xedcd0a07\n.inst 0xec870a02\n.inst 0xe3a07004\n.inst 0xe0860184\n.inst 0xe0851104\n.inst 0xec900a04\n.inst 0xeef02a68\n.inst 0xeeb02a48\n.inst 0xe5911004\n.inst 0xe7950104\n.inst 0xeb014c38\n.inst 0xe2844001\n.inst 0xe1540007\n.inst 0xbafffff4\n.inst 0xe28dd03c\n.inst 0xecbd8b02\n.inst 0xe8bd80f0\n");
}

// DECOMP_FUNC(0x002118a0, 148)
extern "C" __attribute__((naked)) void engine_func_002118a0() {
    asm volatile(".arm\n.inst 0xe92d40f0\n.inst 0xe24dd00c\n.inst 0xe3a00000\n.inst 0xeb01f1a2\n.inst 0xeb01df62\n.inst 0xe3500000\n.inst 0x1a000005\n.inst 0xe59f006c\n.inst 0xe3a01001\n.inst 0xe5900008\n.inst 0xe3500000\n.inst 0x15c01030\n.inst 0xe5c01031\n.inst 0xe320f000\n.inst 0xeb01d3e8\n.inst 0xe3500014\n.inst 0x03a00005\n.inst 0xe1a05000\n.inst 0xe3a04001\n.inst 0xeb01d3de\n.inst 0xe1a07000\n.inst 0xe3a00000\n.inst 0xeb021598\n.inst 0xe1a06000\n.inst 0xe320f000\n.inst 0xeb01df4d\n.inst 0xe3a01000\n.inst 0xe1a02000\n.inst 0xe58d1004\n.inst 0xe1a03005\n.inst 0xe1a01006\n.inst 0xe1a00007\n.inst 0xe58d4000\n.inst 0xeb01d3ff\n.inst 0xe28dd00c\n.inst 0xe8bd80f0\n.word 0x0043e188\n");
}

// DECOMP_FUNC(0x00211c50, 148)
extern "C" __attribute__((naked)) void battle_func_00211c50() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xeb042858\n.inst 0xe1a05000\n.inst 0xeb02b5ee\n.inst 0xe3500000\n.inst 0x0a00001a\n.inst 0xe1a00005\n.inst 0xeb02bb95\n.inst 0xe1a04000\n.inst 0xe590000c\n.inst 0xe3500001\n.inst 0x0a000007\n.inst 0xe5d40064\n.inst 0xe3a05001\n.inst 0xe3500000\n.inst 0x0a00000d\n.inst 0xeb01de6a\n.inst 0xe3500000\n.inst 0x0a000005\n.inst 0xea000007\n.inst 0xe3a01000\n.inst 0xe1a00005\n.inst 0xeb02ca42\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xed9f0a08\n.inst 0xe5c45030\n.inst 0xed840a0a\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.inst 0xed9f0a04\n.inst 0xe5c45030\n.inst 0xed840a0a\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0xbdcccccd\n.word 0xbe800000\n");
}

// DECOMP_FUNC(0x00211f8c, 152)
extern "C" __attribute__((naked)) void camp_func_00211f8c() {
    asm volatile(".arm\n.inst 0xe59f008c\n.inst 0xe92d4070\n.inst 0xe3a04000\n.inst 0xe5900004\n.inst 0xe2805090\n.inst 0xeb01634e\n.inst 0xe2401001\n.inst 0xe3510000\n.inst 0xe1a0c000\n.inst 0xda000012\n.inst 0xe31c0001\n.inst 0xe2850076\n.inst 0x1a000002\n.inst 0xe1f020b2\n.inst 0xe3520000\n.inst 0x13a04001\n.inst 0xe1d030b2\n.inst 0xe1b010c1\n.inst 0xe3a02000\n.inst 0x0a000007\n.inst 0xe3530000\n.inst 0xe1f030b4\n.inst 0x12844001\n.inst 0xe3530000\n.inst 0xe1d030b2\n.inst 0x12822001\n.inst 0xe2511001\n.inst 0x1afffff7\n.inst 0xe0844002\n.inst 0xe25c0001\n.inst 0x4a000003\n.inst 0xe0850080\n.inst 0xe1d007b8\n.inst 0xe3500000\n.inst 0x12844001\n.inst 0xe1a00004\n.inst 0xe8bd8070\n.word 0x0043e2a8\n");
}

// DECOMP_FUNC(0x00215bd8, 148)
extern "C" __attribute__((naked)) void script_vm_func_00215bd8() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a06001\n.inst 0xe1a05000\n.inst 0xe59f7078\n.inst 0xe5974000\n.inst 0xe5c465f2\n.inst 0xeb020d8b\n.inst 0xe59f106c\n.inst 0xe5c405c4\n.inst 0xe18150b4\n.inst 0xeb00eb74\n.inst 0xe3a01001\n.inst 0xe1a00005\n.inst 0xeb01e927\n.inst 0xe3a02000\n.inst 0xe1a01002\n.inst 0xe2840034\n.inst 0xeb029fa7\n.inst 0xe5970000\n.inst 0xe3a01001\n.inst 0xe5902004\n.inst 0xe5802008\n.inst 0xe5a01004\n.inst 0xe3a02000\n.inst 0xe580200c\n.inst 0xe3a0001d\n.inst 0xe584000c\n.inst 0xe1a00005\n.inst 0xeb0282ac\n.inst 0xe5d00007\n.inst 0xe3100040\n.inst 0x13a00002\n.inst 0x158405c8\n.inst 0x058465c8\n.inst 0xe8bd81f0\n.word 0x0043dd50\n.word 0x0000097e\n");
}

// DECOMP_FUNC(0x00219624, 128)
extern "C" __attribute__((naked)) void camp_func_00219624() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe1d000b0\n.inst 0xe1a05001\n.inst 0xeb0215b3\n.inst 0xe1a06000\n.inst 0xe1d500b0\n.inst 0xeb0215b0\n.inst 0xe1d01006\n.inst 0x13e00000\n.inst 0x1a000013\n.inst 0xe1d60000\n.inst 0x13a00001\n.inst 0x1a000010\n.inst 0xe1d400b0\n.inst 0xeb027f3f\n.inst 0xe1a04000\n.inst 0xe1d500b0\n.inst 0xeb027f3c\n.inst 0xe1a01000\n.inst 0xe5d42002\n.inst 0xe5d00002\n.inst 0xe0520000\n.inst 0x1a000006\n.inst 0xe5d10003\n.inst 0xe5d42003\n.inst 0xe0500002\n.inst 0x1a000002\n.inst 0xe1d400b0\n.inst 0xe1d110b0\n.inst 0xe0400001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x00221168, 148)
extern "C" __attribute__((naked)) void engine_func_00221168() {
    asm volatile(".arm\n.inst 0xe92d40f0\n.inst 0xe24dd00c\n.inst 0xe3a00000\n.inst 0xeb01b370\n.inst 0xeb01a130\n.inst 0xe3500000\n.inst 0xe59f0070\n.inst 0x1a000004\n.inst 0xe3a02001\n.inst 0xe5901008\n.inst 0xe3510000\n.inst 0x15c12030\n.inst 0xe5c12031\n.inst 0xe5900004\n.inst 0xe3a05006\n.inst 0xe3a04001\n.inst 0xe3500000\n.inst 0x13a01014\n.inst 0x15c01a11\n.inst 0xeb0195ac\n.inst 0xe1a07000\n.inst 0xe3a00000\n.inst 0xeb01d766\n.inst 0xe1a06000\n.inst 0xe320f000\n.inst 0xeb01a11b\n.inst 0xe3a01000\n.inst 0xe1a02000\n.inst 0xe58d1004\n.inst 0xe1a03005\n.inst 0xe1a01006\n.inst 0xe1a00007\n.inst 0xe58d4000\n.inst 0xeb0195cd\n.inst 0xe28dd00c\n.inst 0xe8bd80f0\n.word 0x0043e188\n");
}

// DECOMP_FUNC(0x00221fb4, 128)
extern "C" __attribute__((naked)) void engine_func_00221fb4() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a00000\n.inst 0xeb00dd53\n.inst 0xe1a07000\n.inst 0xe3a00001\n.inst 0xeb01d3e4\n.inst 0xe1a04000\n.inst 0xe3a00002\n.inst 0xeb01d3e1\n.inst 0xe1a05000\n.inst 0xe3a00003\n.inst 0xeb01d3de\n.inst 0xe1a06000\n.inst 0xeb019d94\n.inst 0xe59f803c\n.inst 0xe3500000\n.inst 0x0a000005\n.inst 0xe5980000\n.inst 0xeb027506\n.inst 0xe3500000\n.inst 0x03a00001\n.inst 0x0a000007\n.inst 0xea000005\n.inst 0xe1a03006\n.inst 0xe1a02005\n.inst 0xe1a01004\n.inst 0xe1a00007\n.inst 0xeb03a099\n.inst 0xe5880000\n.inst 0xe3a00000\n.inst 0xe8bd81f0\n.word 0x0043df58\n");
}

// DECOMP_FUNC(0x002220a8, 140)
extern "C" __attribute__((naked)) void ui_func_002220a8() {
    asm volatile(".arm\n.inst 0xe92d4030\n.inst 0xe24dd00c\n.inst 0xe3a00000\n.inst 0xeb01d3a9\n.inst 0xe1a04000\n.inst 0xe3a00001\n.inst 0xeb01d3a6\n.inst 0xe59f2060\n.inst 0xee000a10\n.inst 0xe59f505c\n.inst 0xe8920007\n.inst 0xeef80ac0\n.inst 0xe88d0007\n.inst 0xe1a0000d\n.inst 0xe0800104\n.inst 0xed900a00\n.inst 0xe5950000\n.inst 0xe2801b01\n.inst 0xe2800b01\n.inst 0xe2811fcf\n.inst 0xe2800fce\n.inst 0xeb032743\n.inst 0xe1a04000\n.inst 0xeb0274c4\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xe5950000\n.inst 0xe1a01004\n.inst 0xe5900000\n.inst 0xeb0288cf\n.inst 0xe28dd00c\n.inst 0xe3a00001\n.inst 0xe8bd8030\n.word 0x00403788\n.word 0x0043dfc0\n");
}

// DECOMP_FUNC(0x00224730, 152)
extern "C" __attribute__((naked)) void engine_func_00224730() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xeb0270e3\n.inst 0xe1a04000\n.inst 0xe5900004\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xe3500001\n.inst 0x1a00001a\n.inst 0xea000011\n.inst 0xe5940008\n.inst 0xe3500000\n.inst 0x0a000016\n.inst 0xe3a05001\n.inst 0xe5845004\n.inst 0xeb02029b\n.inst 0xe284101c\n.inst 0xe584000c\n.inst 0xeb01fd75\n.inst 0xe594000c\n.inst 0xed9f0a10\n.inst 0xeb01fc85\n.inst 0xe594000c\n.inst 0xe320f000\n.inst 0xebffd6f6\n.inst 0xe5840018\n.inst 0xe5c45010\n.inst 0xea000007\n.inst 0xe594000c\n.inst 0xeb01759e\n.inst 0xe594000c\n.inst 0xe320f000\n.inst 0xeb033a1e\n.inst 0xe3500000\n.inst 0x13e00000\n.inst 0x1a000000\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.word 0x3f000000\n");
}

// DECOMP_FUNC(0x002277fc, 144)
extern "C" __attribute__((naked)) void ui_func_002277fc() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe2804b07\n.inst 0xe28440fc\n.inst 0xe5940000\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xeb01b11f\n.inst 0xeb01af2d\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xe3e00000\n.inst 0xe8bd8010\n.inst 0xe5943000\n.inst 0xe3a00000\n.inst 0xe59f104c\n.inst 0xe1d326f8\n.inst 0xe1d31afa\n.inst 0xe3520000\n.inst 0xa3520000\n.inst 0xc1a00002\n.inst 0xe1d327fe\n.inst 0xe3520000\n.inst 0xa1520000\n.inst 0xc1a00002\n.inst 0xe1d329f4\n.inst 0xe3520000\n.inst 0xa1520000\n.inst 0xc1a00002\n.inst 0xe3510000\n.inst 0xa1510000\n.inst 0xc1a00001\n.inst 0xe3500000\n.inst 0xd3a00e19\n.inst 0xd19000f3\n.inst 0xe8bd8010\n.word 0x0000270f\n");
}

// DECOMP_FUNC(0x00227f50, 144)
extern "C" __attribute__((naked)) void engine_func_00227f50() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe2806b07\n.inst 0xe28660fc\n.inst 0xe5960000\n.inst 0xe3500000\n.inst 0x0a000018\n.inst 0xeb01af4a\n.inst 0xeb01ad58\n.inst 0xe3500000\n.inst 0x1a000014\n.inst 0xe59f705c\n.inst 0xe3a04000\n.inst 0xe3a08058\n.inst 0xe0840084\n.inst 0xe5961000\n.inst 0xe0800184\n.inst 0xe0880080\n.inst 0xe0915000\n.inst 0x0a000008\n.inst 0xe597000c\n.inst 0xeb026cba\n.inst 0xe1a02000\n.inst 0xe597100c\n.inst 0xe1a00005\n.inst 0xeb023190\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000004\n.inst 0xe2844001\n.inst 0xe3540004\n.inst 0xbaffffed\n.inst 0xe3e00000\n.inst 0xe8bd81f0\n.inst 0xe1d501f0\n.inst 0xe8bd81f0\n.word 0x00435d00\n");
}

// DECOMP_FUNC(0x00227fe0, 128)
extern "C" __attribute__((naked)) void engine_func_00227fe0() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe2806b07\n.inst 0xe28660fc\n.inst 0xe5960000\n.inst 0xe3500000\n.inst 0x0a000014\n.inst 0xe59f705c\n.inst 0xe3a04000\n.inst 0xe3a08058\n.inst 0xe0840084\n.inst 0xe5961000\n.inst 0xe0800184\n.inst 0xe0880080\n.inst 0xe0915000\n.inst 0x0a000008\n.inst 0xe597000c\n.inst 0xeb026c9a\n.inst 0xe1a02000\n.inst 0xe597100c\n.inst 0xe1a00005\n.inst 0xeb023170\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000004\n.inst 0xe2844001\n.inst 0xe3540004\n.inst 0xbaffffed\n.inst 0xe3e00000\n.inst 0xe8bd81f0\n.inst 0xe1d501b2\n.inst 0xe8bd81f0\n.word 0x00435d00\n");
}

// DECOMP_FUNC(0x002282a0, 152)
extern "C" __attribute__((naked)) void ui_func_002282a0() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe2804b07\n.inst 0xe28440fc\n.inst 0xe1a05001\n.inst 0xe5940000\n.inst 0xe3500000\n.inst 0x0a000018\n.inst 0xe2800c01\n.inst 0xe1d009f0\n.inst 0xe3500000\n.inst 0xba000014\n.inst 0xeb01ae71\n.inst 0xeb01ac7f\n.inst 0xe3500000\n.inst 0x0a000007\n.inst 0xeb01ae6d\n.inst 0xe2800b11\n.inst 0xe28000ac\n.inst 0xe5900000\n.inst 0xe2000002\n.inst 0xe1b00000\n.inst 0x13a00000\n.inst 0x1a000009\n.inst 0xe3550000\n.inst 0x0a000008\n.inst 0xeb01ae63\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xeb01ac6f\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000001\n.inst 0xe3e00000\n.inst 0xe8bd8070\n.inst 0xe5940000\n.inst 0xe2800c01\n.inst 0xe1d009f0\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x0022922c, 128)
extern "C" __attribute__((naked)) void func_0022922c() {
    asm volatile(".arm\n.inst 0xe52d4004\n.inst 0xe5903000\n.inst 0xe3a02001\n.inst 0xe1a01002\n.inst 0xe2833d7f\n.inst 0xe5933000\n.inst 0xe5934000\n.inst 0xe3c44b01\n.inst 0xe5834000\n.inst 0xe0823202\n.inst 0xe083c302\n.inst 0xe5903000\n.inst 0xe2822001\n.inst 0xe2811002\n.inst 0xe2833d7f\n.inst 0xe351006d\n.inst 0xe5933000\n.inst 0xe7b3c18c\n.inst 0xe3cccb01\n.inst 0xe583c000\n.inst 0xe5903000\n.inst 0xe082c202\n.inst 0xe08cc302\n.inst 0xe2833d7f\n.inst 0xe2822001\n.inst 0xe5933000\n.inst 0xe7b3c18c\n.inst 0xe3cccb01\n.inst 0xe583c000\n.inst 0xbaffffea\n.inst 0xe49d4004\n.inst 0xe12fff1e\n");
}

// DECOMP_FUNC(0x00229aa8, 132)
extern "C" __attribute__((naked)) void ui_func_00229aa8() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe1a06001\n.inst 0xe5900000\n.inst 0xe1a01002\n.inst 0xe1a04002\n.inst 0xeb016433\n.inst 0xe3500000\n.inst 0x11d046fe\n.inst 0xe0840104\n.inst 0xe0860080\n.inst 0xe2800c09\n.inst 0xe1d00db4\n.inst 0xe3500000\n.inst 0x1a00000f\n.inst 0xe5951000\n.inst 0xe0840204\n.inst 0xe0800304\n.inst 0xe2811d7f\n.inst 0xe5911000\n.inst 0xe7912180\n.inst 0xe3120001\n.inst 0x0a000007\n.inst 0xe3120501\n.inst 0x1a000005\n.inst 0xe3a020c8\n.inst 0xe0820180\n.inst 0xe7910000\n.inst 0xe3500000\n.inst 0xd3a00001\n.inst 0xda000000\n.inst 0xe3a00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x00229b2c, 140)
extern "C" __attribute__((naked)) void script_vm_func_00229b2c() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe24ddf6d\n.inst 0xe3a03000\n.inst 0xe5901000\n.inst 0xe59f2070\n.inst 0xe3a0506d\n.inst 0xe2811d7f\n.inst 0xe1a0600d\n.inst 0xe5911000\n.inst 0xe281cf6d\n.inst 0xe281406e\n.inst 0xe5917000\n.inst 0xe3170b01\n.inst 0x0a000006\n.inst 0xe1dc70f0\n.inst 0xe1570002\n.inst 0xca000003\n.inst 0xe1d480f0\n.inst 0xe1a02007\n.inst 0xe7868103\n.inst 0xe2833001\n.inst 0xe2555001\n.inst 0xe2811fa2\n.inst 0xe28ccfa2\n.inst 0xe2844fa2\n.inst 0x1afffff0\n.inst 0xeb0153ff\n.inst 0xe0861103\n.inst 0xe2800038\n.inst 0xe5111004\n.inst 0xe3a02001\n.inst 0xe7c12000\n.inst 0xe28ddf6d\n.inst 0xe8bd81f0\n.word 0x000186a0\n");
}

// DECOMP_FUNC(0x00229bd0, 152)
extern "C" __attribute__((naked)) void battle_func_00229bd0() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a04003\n.inst 0xe1a03001\n.inst 0xe59f7080\n.inst 0xe6bf1070\n.inst 0xe1a06002\n.inst 0xe59d5018\n.inst 0xe5970000\n.inst 0xe3a02000\n.inst 0xebfff3cc\n.inst 0xe3550000\n.inst 0x0a000013\n.inst 0xe5971000\n.inst 0xe5911008\n.inst 0xe3510000\n.inst 0x0a00000f\n.inst 0xe5d13004\n.inst 0xe591200c\n.inst 0xe353000e\n.inst 0x05913028\n.inst 0x03530000\n.inst 0x0591104c\n.inst 0x01510004\n.inst 0x1a000005\n.inst 0xe1d010f2\n.inst 0xe3510000\n.inst 0xba000002\n.inst 0xe3e01000\n.inst 0xe1c010b2\n.inst 0xea000001\n.inst 0xe1b01002\n.inst 0x1affffef\n.inst 0xe3a0100e\n.inst 0xe5806028\n.inst 0xe5c01004\n.inst 0xe580404c\n.inst 0xe8bd81f0\n.word 0x00434290\n");
}

// DECOMP_FUNC(0x0022b9d0, 132)
extern "C" __attribute__((naked)) void engine_func_0022b9d0() {
    asm volatile(".arm\n.inst 0xe2800050\n.inst 0xeddf2a1b\n.inst 0xed9f2a1b\n.inst 0xeddf1a1b\n.inst 0xed910a00\n.inst 0xecd00a02\n.inst 0xeeb40ae1\n.inst 0xee700ae2\n.inst 0xee311a42\n.inst 0xeefd0ae0\n.inst 0xeebd1ac1\n.inst 0xeef1fa10\n.inst 0xed912a01\n.inst 0xdeb00a61\n.inst 0xeeb42ae1\n.inst 0xed810a00\n.inst 0xeef1fa10\n.inst 0xcef01a42\n.inst 0xeeb82ae0\n.inst 0xedc11a01\n.inst 0xeeb40ac2\n.inst 0xeef1fa10\n.inst 0xceb80ae0\n.inst 0xed810a00\n.inst 0xeeb80ac1\n.inst 0xeef41ac0\n.inst 0xeef1fa10\n.inst 0xcef81ac1\n.inst 0xedc11a01\n.inst 0xe12fff1e\n.word 0x43c80000\n.word 0x43700000\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x0022df7c, 140)
extern "C" __attribute__((naked)) void unite_func_0022df7c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe1a05001\n.inst 0xe1a00001\n.inst 0xeb022cf4\n.inst 0xe3500000\n.inst 0x0a000015\n.inst 0xe1d009b0\n.inst 0xe3500e16\n.inst 0x33a00000\n.inst 0x33a02001\n.inst 0x2a000010\n.inst 0xe0841080\n.inst 0xe1d110f0\n.inst 0xe1510005\n.inst 0x1a000001\n.inst 0xe0800004\n.inst 0xea00000e\n.inst 0xe2800001\n.inst 0xe3500010\n.inst 0xbafffff6\n.inst 0xe3a00000\n.inst 0xe0841080\n.inst 0xe1d110f0\n.inst 0xe3710001\n.inst 0x0a000003\n.inst 0xe2800001\n.inst 0xe3500010\n.inst 0xbafffff8\n.inst 0xe8bd8070\n.inst 0xe0841080\n.inst 0xe0800004\n.inst 0xe1c150b0\n.inst 0xe5c02020\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002306ec, 144)
extern "C" __attribute__((naked)) void engine_func_002306ec() {
    asm volatile(".arm\n.inst 0xe3500000\n.inst 0xe59f0080\n.inst 0xe92d4038\n.inst 0xe3a0100b\n.inst 0xed9f0a1c\n.inst 0xe5904008\n.inst 0x0a00000c\n.inst 0xe3a00001\n.inst 0xe5c40082\n.inst 0xe58d1000\n.inst 0xe28430a4\n.inst 0xe3a02000\n.inst 0xe3a0100e\n.inst 0xe2840e7e\n.inst 0xeb023500\n.inst 0xe3a02000\n.inst 0xe3a01008\n.inst 0xe2840e7e\n.inst 0xeb0234e1\n.inst 0xea00000b\n.inst 0xe3a00002\n.inst 0xe5c40082\n.inst 0xe58d1000\n.inst 0xe28430a4\n.inst 0xe3a02000\n.inst 0xe3a0100e\n.inst 0xe2840e7e\n.inst 0xeb0234f3\n.inst 0xe3a02000\n.inst 0xe3a01009\n.inst 0xe2840e7e\n.inst 0xeb0234d4\n.inst 0xe3a00001\n.inst 0xe8bd8038\n.word 0x3f800000\n.word 0x0043e188\n");
}

// DECOMP_FUNC(0x0023d230, 132)
extern "C" __attribute__((naked)) void func_0023d230() {
    asm volatile(".arm\n.inst 0xe20128ff\n.inst 0xe2013cff\n.inst 0xe1a0c822\n.inst 0xe1a02c21\n.inst 0xee002a90\n.inst 0xee01ca10\n.inst 0xe1a03423\n.inst 0xe20110ff\n.inst 0xee023a10\n.inst 0xee001a10\n.inst 0xeef82a60\n.inst 0xeef80a41\n.inst 0xeddf1a10\n.inst 0xe59f1040\n.inst 0xeeb81a42\n.inst 0xeeb82a40\n.inst 0xe5d12000\n.inst 0xe59f1034\n.inst 0xee220aa1\n.inst 0xee600aa1\n.inst 0xe3822102\n.inst 0xe4802004\n.inst 0xee211a21\n.inst 0xee621a21\n.inst 0xe4801004\n.inst 0xece01a01\n.inst 0xeca01a01\n.inst 0xece00a01\n.inst 0xeca00a01\n.inst 0xe12fff1e\n.word 0x3b808081\n.word 0x00490e46\n.word 0x804f02c0\n");
}

// DECOMP_FUNC(0x0024095c, 128)
extern "C" __attribute__((naked)) void func_0024095c() {
    asm volatile(".arm\n.inst 0xe3a02000\n.inst 0xe580172c\n.inst 0xe5802728\n.inst 0xe5902634\n.inst 0xe280300c\n.inst 0xe2801b01\n.inst 0xe3822702\n.inst 0xe5802634\n.inst 0xedd02a06\n.inst 0xed902a07\n.inst 0xed900a05\n.inst 0xedd01a08\n.inst 0xe2811f8d\n.inst 0xecd30a02\n.inst 0xee300a61\n.inst 0xe59f3038\n.inst 0xee700ae2\n.inst 0xee311a42\n.inst 0xee600aa0\n.inst 0xee410a01\n.inst 0xee400a00\n.inst 0xeeb10ae0\n.inst 0xee100a10\n.inst 0xe1500003\n.inst 0x8a000004\n.inst 0xee100a10\n.inst 0xe2833102\n.inst 0xe1500003\n.inst 0xd3c20702\n.inst 0xd5810000\n.inst 0xe12fff1e\n.word 0xbc23d70a\n");
}

// DECOMP_FUNC(0x00247d64, 128)
extern "C" __attribute__((naked)) void engine_func_00247d64() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04001\n.inst 0xe1a05002\n.inst 0xeb01e354\n.inst 0xed9f0a17\n.inst 0xeddf0a17\n.inst 0xe3550000\n.inst 0x0a000009\n.inst 0xe3540000\n.inst 0x0d800a09\n.inst 0x0a00000f\n.inst 0xee004a10\n.inst 0xed9f1a11\n.inst 0xedc00a09\n.inst 0xeeb80ac0\n.inst 0xeec10a00\n.inst 0xedc00a0a\n.inst 0xe8bd8070\n.inst 0xe3540000\n.inst 0x0dc00a09\n.inst 0x0a000005\n.inst 0xee014a10\n.inst 0xed800a09\n.inst 0xeeb81ac1\n.inst 0xee800a81\n.inst 0xed800a0a\n.inst 0xe8bd8070\n.inst 0xed800a0a\n.inst 0xe8bd8070\n.word 0x00000000\n.word 0x3f800000\n.word 0xbf800000\n");
}

// DECOMP_FUNC(0x0024baf4, 140)
extern "C" __attribute__((naked)) void ui_func_0024baf4() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xeb012066\n.inst 0xe2800a02\n.inst 0xe5904234\n.inst 0xeb00001d\n.inst 0xe1a01000\n.inst 0xe1a00004\n.inst 0xe8bd4010\n.inst 0xe1a00000\n.inst 0xe92d4030\n.inst 0xe1b04000\n.inst 0xe24dd00c\n.inst 0xe1a05001\n.inst 0x1a000001\n.inst 0xeb00eb4e\n.inst 0xe1a04000\n.inst 0xe59f0040\n.inst 0xe590000c\n.inst 0xe5805024\n.inst 0xe3a00000\n.inst 0xeb012d05\n.inst 0xe1a05000\n.inst 0xe320f000\n.inst 0xeb00f6ba\n.inst 0xe3a01000\n.inst 0xe1a02000\n.inst 0xe58d1000\n.inst 0xe58d1004\n.inst 0xe3a0300c\n.inst 0xe1a01005\n.inst 0xe1a00004\n.inst 0xeb00eb6c\n.inst 0xe28dd00c\n.inst 0xe8bd8030\n.word 0x0043e188\n");
}

// DECOMP_FUNC(0x0024c3f8, 148)
extern "C" __attribute__((naked)) void engine_func_0024c3f8() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a06001\n.inst 0xe1a04002\n.inst 0xe1a05003\n.inst 0xeb018f5e\n.inst 0xe59f2074\n.inst 0xe5903004\n.inst 0xe3e0107c\n.inst 0xe0c02692\n.inst 0xe5932000\n.inst 0xe1a03340\n.inst 0xe0430fc0\n.inst 0xe0000190\n.inst 0xe0860180\n.inst 0xe0800100\n.inst 0xe0820100\n.inst 0xe1d010b4\n.inst 0xe1d020b6\n.inst 0xe590000c\n.inst 0xe3c11902\n.inst 0xe3c22902\n.inst 0xe3500000\n.inst 0x0a000007\n.inst 0xe1d030b4\n.inst 0xe3530001\n.inst 0x0a000002\n.inst 0xe5d0300c\n.inst 0xe3130001\n.inst 0x0a000001\n.inst 0xe1d010f0\n.inst 0xe1d020f2\n.inst 0xe3540000\n.inst 0x15841000\n.inst 0xe3550000\n.inst 0x15852000\n.inst 0xe8bd8070\n.word 0x10624dd3\n");
}

// DECOMP_FUNC(0x0024de78, 136)
extern "C" __attribute__((naked)) void engine_func_0024de78() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a06000\n.inst 0xe1a04006\n.inst 0xe59f706c\n.inst 0xe5970000\n.inst 0xe3500000\n.inst 0xc59f8064\n.inst 0xda000012\n.inst 0xe0840184\n.inst 0xe0800284\n.inst 0xe0885180\n.inst 0xe595013c\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xeb01d92a\n.inst 0xe585613c\n.inst 0xe5856028\n.inst 0xe5950024\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xeb01d924\n.inst 0xe5856024\n.inst 0xe5856020\n.inst 0xe5970000\n.inst 0xe2844001\n.inst 0xe1540000\n.inst 0xbaffffec\n.inst 0xe59f0010\n.inst 0xe3a01c52\n.inst 0xeb01db0f\n.inst 0xe5876000\n.inst 0xe8bd81f0\n.word 0x00433278\n.word 0x00478000\n");
}

// DECOMP_FUNC(0x0024fd10, 148)
extern "C" __attribute__((naked)) void engine_func_0024fd10() {
    asm volatile(".arm\n.inst 0xe92d40f0\n.inst 0xe24dd00c\n.inst 0xe3a06038\n.inst 0xe5902020\n.inst 0xe5901024\n.inst 0xe3520000\n.inst 0x059000b8\n.inst 0x10050192\n.inst 0x00050190\n.inst 0xe59f105c\n.inst 0xe59f005c\n.inst 0xe3550064\n.inst 0x83a05064\n.inst 0xe1a00000\n.inst 0xe3a07001\n.inst 0xe3a00010\n.inst 0xe88d0081\n.inst 0xe1a03006\n.inst 0xe3a02000\n.inst 0xe3a01c01\n.inst 0xe3a00801\n.inst 0xeb01cdce\n.inst 0xe1a04000\n.inst 0xe1a01006\n.inst 0xeb01cf74\n.inst 0xe3e01000\n.inst 0xed9f0a08\n.inst 0xe5841004\n.inst 0xe5845000\n.inst 0xed840a02\n.inst 0xe1c473b4\n.inst 0xe28dd00c\n.inst 0xe1a00004\n.inst 0xe8bd80f0\n.word 0x000001c2\n.word 0x004102c4\n.word 0x3f800000\n");
}

// DECOMP_FUNC(0x002502e8, 128)
extern "C" __attribute__((naked)) void engine_func_002502e8() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05001\n.inst 0xe1a04000\n.inst 0xeb001a50\n.inst 0xe59f6060\n.inst 0xe895100e\n.inst 0xe2860c01\n.inst 0xe880100e\n.inst 0xeb069ae6\n.inst 0xeb014b02\n.inst 0xe2865d05\n.inst 0xe2843010\n.inst 0xe8950007\n.inst 0xed9f0a10\n.inst 0xe8840007\n.inst 0xe2861e15\n.inst 0xe5960158\n.inst 0xe8910006\n.inst 0xe5840018\n.inst 0xe8830006\n.inst 0xe2861e16\n.inst 0xe5960168\n.inst 0xe8910006\n.inst 0xe2843020\n.inst 0xe5840028\n.inst 0xe8830006\n.inst 0xed840a0c\n.inst 0xed840a0d\n.inst 0xed840a0e\n.inst 0xe8bd8070\n.word 0x004ea81c\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x00252630, 140)
extern "C" __attribute__((naked)) void script_vm_func_00252630() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe59f6078\n.inst 0xe5965000\n.inst 0xe1b04005\n.inst 0x0a00001a\n.inst 0xe59512f8\n.inst 0xe3a07000\n.inst 0xe3510000\n.inst 0xba00000f\n.inst 0xe3a00018\n.inst 0xeb017133\n.inst 0xe5960000\n.inst 0xe3a01000\n.inst 0xe3500000\n.inst 0x15c012f4\n.inst 0xe59f0044\n.inst 0xe59422f8\n.inst 0xe3a01018\n.inst 0xe5900000\n.inst 0xeb014f63\n.inst 0xe3e00000\n.inst 0xe58402f8\n.inst 0xe2844fba\n.inst 0xe3a00003\n.inst 0xe8840081\n.inst 0xe3a01000\n.inst 0xe59502e4\n.inst 0xeb01c7c5\n.inst 0xe1a00005\n.inst 0xe320f000\n.inst 0xeb01c72c\n.inst 0xe5867000\n.inst 0xe8bd81f0\n.word 0x00434210\n.word 0x00433158\n");
}

// DECOMP_FUNC(0x00256524, 140)
extern "C" __attribute__((naked)) void func_00256524() {
    asm volatile(".arm\n.inst 0xe59f2078\n.inst 0xe3510000\n.inst 0x03a00000\n.inst 0xe5922000\n.inst 0xe2822903\n.inst 0xe2822d33\n.inst 0x05c20000\n.inst 0x0a000016\n.inst 0xe3a03001\n.inst 0xe5c23000\n.inst 0xe59f2050\n.inst 0xe3500000\n.inst 0x03e00000\n.inst 0xed9f0a13\n.inst 0xe5922000\n.inst 0xe2822b33\n.inst 0xe1c20cb2\n.inst 0xe0810101\n.inst 0xe59f1034\n.inst 0xe1a00080\n.inst 0xe6bf0070\n.inst 0xe1c20cb6\n.inst 0xe1a03100\n.inst 0xed820a33\n.inst 0xe0c01391\n.inst 0xed820a34\n.inst 0xed820a35\n.inst 0xe1a01140\n.inst 0xe0410fc0\n.inst 0xe1c20cb4\n.inst 0xe1c20cb8\n.inst 0xe12fff1e\n.word 0x00447a78\n.word 0x66666667\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x00262664, 140)
extern "C" __attribute__((naked)) void func_00262664() {
    asm volatile(".arm\n.inst 0xe59f107c\n.inst 0xe92d0030\n.inst 0xe1d041fc\n.inst 0xe5912000\n.inst 0xe3520000\n.inst 0x15921064\n.inst 0x13510015\n.inst 0x0a000015\n.inst 0xe2822d7f\n.inst 0xe3a01000\n.inst 0xe592c000\n.inst 0xe0812201\n.inst 0xe0822301\n.inst 0xe08c2182\n.inst 0xe5923000\n.inst 0xe3130001\n.inst 0x0a000009\n.inst 0xe3130040\n.inst 0x1a000007\n.inst 0xe3130002\n.inst 0x0a000005\n.inst 0xe5923278\n.inst 0xe1530000\n.inst 0x1a000002\n.inst 0xe59f0020\n.inst 0xe19040f2\n.inst 0xea000002\n.inst 0xe2811001\n.inst 0xe351006d\n.inst 0xbaffffec\n.inst 0xe1a00004\n.inst 0xe8bd0030\n.inst 0xe12fff1e\n.word 0x00435d90\n.word 0x000001b6\n");
}

// DECOMP_FUNC(0x00262edc, 144)
extern "C" __attribute__((naked)) void camp_func_00262edc() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe59f007c\n.inst 0xe5900004\n.inst 0xe2805090\n.inst 0xeb001f7a\n.inst 0xe2502000\n.inst 0xd3a00000\n.inst 0xda00000a\n.inst 0xe2020001\n.inst 0xe3500000\n.inst 0xe3a01000\n.inst 0xda000006\n.inst 0xe0853081\n.inst 0xe1d337b8\n.inst 0xe1530004\n.inst 0x0a00000a\n.inst 0xe2811001\n.inst 0xe1500001\n.inst 0xcafffff8\n.inst 0xe1500002\n.inst 0xaa00000a\n.inst 0xe0851080\n.inst 0xe1d137b8\n.inst 0xe1530004\n.inst 0x11d117ba\n.inst 0x11510004\n.inst 0x1a000001\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2800002\n.inst 0xe1520000\n.inst 0xcafffff4\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.word 0x0043e2a8\n");
}

// DECOMP_FUNC(0x002642d0, 152)
extern "C" __attribute__((naked)) void script_vm_func_002642d0() {
    asm volatile(".arm\n.inst 0xe92d4038\n.inst 0xe5900000\n.inst 0xe7900101\n.inst 0xe590400c\n.inst 0xe3540000\n.inst 0x0a000019\n.inst 0xe58d0000\n.inst 0xe594101c\n.inst 0xe5942018\n.inst 0xe1a0300d\n.inst 0xe1520001\n.inst 0x0a000004\n.inst 0xe5920000\n.inst 0xe59dc000\n.inst 0xe150000c\n.inst 0x12822004\n.inst 0x1afffff8\n.inst 0xe1520001\n.inst 0x0a000002\n.inst 0xe2820004\n.inst 0xeb014d39\n.inst 0xe1a02000\n.inst 0xe594001c\n.inst 0xe584201c\n.inst 0xe1500002\n.inst 0x13a00001\n.inst 0x03a00000\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xe59d0000\n.inst 0xe3a01000\n.inst 0xe580100c\n.inst 0xe59f000c\n.inst 0xe5901000\n.inst 0xe2411001\n.inst 0xe5801000\n.inst 0xe8bd8038\n.word 0x004dad80\n");
}

// DECOMP_FUNC(0x002649c0, 136)
extern "C" __attribute__((naked)) void script_vm_func_002649c0() {
    asm volatile(".arm\n.inst 0xe59f107c\n.inst 0xe59f0070\n.inst 0xe3a03001\n.inst 0xe59f206c\n.inst 0xe5911000\n.inst 0xe5c032f8\n.inst 0xe5913040\n.inst 0xe58032fc\n.inst 0xe5913048\n.inst 0xe5803300\n.inst 0xe5903008\n.inst 0xe5803304\n.inst 0xe5922000\n.inst 0xe282301c\n.inst 0xec930a03\n.inst 0xe2803fc2\n.inst 0xec830a03\n.inst 0xe592304c\n.inst 0xe5803314\n.inst 0xe5913040\n.inst 0xe580331c\n.inst 0xe5911048\n.inst 0xe5801320\n.inst 0xe282101c\n.inst 0xe891100a\n.inst 0xe5801324\n.inst 0xe2801fca\n.inst 0xe8811008\n.inst 0xe592104c\n.inst 0xe5801330\n.inst 0xe12fff1e\n.word 0x0049f91c\n.word 0x00447e88\n.word 0x00447060\n");
}

// DECOMP_FUNC(0x00269e54, 140)
extern "C" __attribute__((naked)) void func_00269e54() {
    asm volatile(".arm\n.inst 0xe59f107c\n.inst 0xe92d0030\n.inst 0xe1d040fe\n.inst 0xe5912000\n.inst 0xe3520000\n.inst 0x15921064\n.inst 0x13510015\n.inst 0x0a000015\n.inst 0xe2822d7f\n.inst 0xe3a01000\n.inst 0xe592c000\n.inst 0xe0812201\n.inst 0xe0822301\n.inst 0xe08c2182\n.inst 0xe5923000\n.inst 0xe3130001\n.inst 0x0a000009\n.inst 0xe3130040\n.inst 0x1a000007\n.inst 0xe3130008\n.inst 0x0a000005\n.inst 0xe592327c\n.inst 0xe1530000\n.inst 0x1a000002\n.inst 0xe59f0020\n.inst 0xe19040f2\n.inst 0xea000002\n.inst 0xe2811001\n.inst 0xe351006d\n.inst 0xbaffffec\n.inst 0xe1a00004\n.inst 0xe8bd0030\n.inst 0xe12fff1e\n.word 0x00435d90\n.word 0x000001b6\n");
}

// DECOMP_FUNC(0x0026b734, 152)
extern "C" __attribute__((naked)) void ui_func_0026b734() {
    asm volatile(".arm\n.inst 0xe92d4030\n.inst 0xe24dd014\n.inst 0xe1a0000d\n.inst 0xeb016849\n.inst 0xe1cd00d0\n.inst 0xe1cd00f8\n.inst 0xe28d0008\n.inst 0xebffa3b1\n.inst 0xe1a05000\n.inst 0xe28d0008\n.inst 0xebffa398\n.inst 0xe1a04000\n.inst 0xe28d0008\n.inst 0xebffa37f\n.inst 0xe1a02005\n.inst 0xe1a01004\n.inst 0xeb00f3ed\n.inst 0xe0800080\n.inst 0xe1a04180\n.inst 0xe28d0008\n.inst 0xeb05d5c8\n.inst 0xe0800004\n.inst 0xe0600200\n.inst 0xe1a04100\n.inst 0xe28d0008\n.inst 0xeb05d5dd\n.inst 0xe0800004\n.inst 0xe0600200\n.inst 0xe1a04100\n.inst 0xe28d0008\n.inst 0xeb05d5f3\n.inst 0xe59f1010\n.inst 0xe0800004\n.inst 0xe591100c\n.inst 0xe5810004\n.inst 0xe28dd014\n.inst 0xe8bd8030\n.word 0x0043e2a8\n");
}

// DECOMP_FUNC(0x0026ea7c, 152)
extern "C" __attribute__((naked)) void engine_func_0026ea7c() {
    asm volatile(".arm\n.inst 0xee700a82\n.inst 0xee311a22\n.inst 0xee332a85\n.inst 0xee742a25\n.inst 0xed2d8b02\n.inst 0xe3500000\n.inst 0xed9f8a1c\n.inst 0xeddf7a1c\n.inst 0xee700a82\n.inst 0xee311a22\n.inst 0xee600a88\n.inst 0xee211a08\n.inst 0x0a000009\n.inst 0xee300a21\n.inst 0xee731a24\n.inst 0xed9f2a13\n.inst 0xe3500001\n.inst 0xee300a21\n.inst 0xee200a02\n.inst 0x0a000006\n.inst 0xe3500002\n.inst 0x0a000008\n.inst 0xea000009\n.inst 0xeef06a60\n.inst 0xeeb07a41\n.inst 0xeeb06a67\n.inst 0xea000005\n.inst 0xeeb06a40\n.inst 0xeeb07a41\n.inst 0xeef06a67\n.inst 0xea000001\n.inst 0xeeb06b40\n.inst 0xeeb07a67\n.inst 0xec816a03\n.inst 0xecbd8b02\n.inst 0xe12fff1e\n.word 0x3e800000\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x0026f370, 136)
extern "C" __attribute__((naked)) void func_0026f370() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a05000\n.inst 0xe1a07001\n.inst 0xe1a06002\n.inst 0xed2d8b02\n.inst 0xeef08a40\n.inst 0xeeb08a60\n.inst 0xe3a04000\n.inst 0xe1a01002\n.inst 0xe1a00007\n.inst 0xeb015891\n.inst 0xee381a68\n.inst 0xeddf0a13\n.inst 0xe1560007\n.inst 0x03a04001\n.inst 0xed850a00\n.inst 0xeeb41ae0\n.inst 0xeef1fa10\n.inst 0xda000003\n.inst 0xeeb40ac8\n.inst 0xeef1fa10\n.inst 0xaa000006\n.inst 0xea000002\n.inst 0xeeb40ac8\n.inst 0xeef1fa10\n.inst 0x9a000002\n.inst 0xe3540000\n.inst 0x03a00000\n.inst 0x0a000001\n.inst 0xed858a00\n.inst 0xe3a00001\n.inst 0xecbd8b02\n.inst 0xe8bd81f0\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x002701c4, 140)
extern "C" __attribute__((naked)) void script_vm_func_002701c4() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe59f4074\n.inst 0xe5940010\n.inst 0xe3500000\n.inst 0x0a000019\n.inst 0xebffed99\n.inst 0xe5941010\n.inst 0xe3a02080\n.inst 0xeb01335b\n.inst 0xebffed90\n.inst 0xe5941014\n.inst 0xeb00f652\n.inst 0xeb014266\n.inst 0xe59f2048\n.inst 0xe5941018\n.inst 0xeb013354\n.inst 0xeb01c251\n.inst 0xeb015617\n.inst 0xe59f0038\n.inst 0xe5900000\n.inst 0xebfff8de\n.inst 0xe5940010\n.inst 0xeb01504f\n.inst 0xe5940014\n.inst 0xeb01504d\n.inst 0xe5940018\n.inst 0xeb01504b\n.inst 0xe3a00000\n.inst 0xe5840010\n.inst 0xe5840014\n.inst 0xe5840018\n.inst 0xe8bd8010\n.word 0x0044de28\n.word 0x00024d28\n.word 0x00433158\n");
}

// DECOMP_FUNC(0x002706e4, 140)
extern "C" __attribute__((naked)) void script_vm_func_002706e4() {
    asm volatile(".arm\n.inst 0xe59f0080\n.inst 0xe92d4070\n.inst 0xe59f5074\n.inst 0xe5904000\n.inst 0xe2850094\n.inst 0xeb0002b8\n.inst 0xe3a00001\n.inst 0xe5c502f8\n.inst 0xe594002c\n.inst 0xe2852fc3\n.inst 0xe58502fc\n.inst 0xe5940030\n.inst 0xe5850300\n.inst 0xe5950008\n.inst 0xe5850304\n.inst 0xed950a25\n.inst 0xe1c509d8\n.inst 0xed850ac2\n.inst 0xe8820003\n.inst 0xedd50a28\n.inst 0xedc50ac5\n.inst 0xedc50ac6\n.inst 0xe594202c\n.inst 0xe585231c\n.inst 0xe5942030\n.inst 0xe5852320\n.inst 0xe2852fca\n.inst 0xed850ac9\n.inst 0xe8820003\n.inst 0xe5950090\n.inst 0xe5850330\n.inst 0xe5850334\n.inst 0xe8bd8070\n.word 0x0049f91c\n.word 0x00447e28\n");
}

// DECOMP_FUNC(0x00275984, 148)
extern "C" __attribute__((naked)) void script_vm_func_00275984() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe59f6084\n.inst 0xe5960000\n.inst 0xe5d01009\n.inst 0xe3510000\n.inst 0x15d01008\n.inst 0x13510000\n.inst 0x0a00001a\n.inst 0xe5902004\n.inst 0xe3a01000\n.inst 0xe1a04001\n.inst 0xe3520000\n.inst 0xe5c01008\n.inst 0xda000014\n.inst 0xe5960000\n.inst 0xe0805284\n.inst 0xe5f5000c\n.inst 0xe3500000\n.inst 0x0a00000a\n.inst 0xe1d501b0\n.inst 0xe3500000\n.inst 0x1a000007\n.inst 0xe5950008\n.inst 0xe3500000\n.inst 0x1a000004\n.inst 0xe2851014\n.inst 0xe5950004\n.inst 0xec910a03\n.inst 0xeb0071ba\n.inst 0xe5850008\n.inst 0xe5960000\n.inst 0xe2844001\n.inst 0xe5900004\n.inst 0xe1500004\n.inst 0xcaffffea\n.inst 0xe8bd8070\n.word 0x00448c20\n");
}

// DECOMP_FUNC(0x002762e8, 132)
extern "C" __attribute__((naked)) void script_vm_func_002762e8() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a07000\n.inst 0xeb013209\n.inst 0xe2806c0d\n.inst 0xe1a05000\n.inst 0xe1d60ed3\n.inst 0xe3a04000\n.inst 0xe3500000\n.inst 0xc3a08000\n.inst 0xda000014\n.inst 0xe0850004\n.inst 0xe5d01de4\n.inst 0xe3510000\n.inst 0x0a00000c\n.inst 0xe59f2040\n.inst 0xe0851084\n.inst 0xe19220f1\n.inst 0xe1520007\n.inst 0x1a000007\n.inst 0xe2811c0d\n.inst 0xe5c08de4\n.inst 0xe1d10ff4\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xe3a02001\n.inst 0xe1a01002\n.inst 0xeb004d9b\n.inst 0xe1d60ed3\n.inst 0xe2844001\n.inst 0xe1500004\n.inst 0xcaffffea\n.inst 0xe8bd81f0\n.word 0x00000e04\n");
}

// DECOMP_FUNC(0x00276c24, 136)
extern "C" __attribute__((naked)) void script_vm_func_00276c24() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3720001\n.inst 0xe1a05000\n.inst 0xe59f8070\n.inst 0xe1a06001\n.inst 0xe1a07002\n.inst 0xe8880007\n.inst 0x0a000015\n.inst 0xe3a04000\n.inst 0xebff563a\n.inst 0xe3500000\n.inst 0xda000011\n.inst 0xe1a00004\n.inst 0xeb001b56\n.inst 0xe1d010d0\n.inst 0xe1510005\n.inst 0x01d010d1\n.inst 0x01510006\n.inst 0x05d01002\n.inst 0x01510007\n.inst 0x1a000003\n.inst 0xe5d00003\n.inst 0xe35000ff\n.inst 0x1a000006\n.inst 0xea000004\n.inst 0xe2844001\n.inst 0xebff5629\n.inst 0xe1500004\n.inst 0xe320f000\n.inst 0xcaffffed\n.inst 0xe3e00000\n.inst 0xe588000c\n.inst 0xe8bd81f0\n.word 0x0049fd14\n");
}

// DECOMP_FUNC(0x00277dcc, 128)
extern "C" __attribute__((naked)) void script_vm_func_00277dcc() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3500024\n.inst 0xe1a04000\n.inst 0xe59f0068\n.inst 0xe1a06001\n.inst 0xe5905000\n.inst 0x0a000016\n.inst 0xeb00367d\n.inst 0xe3500001\n.inst 0x1a000003\n.inst 0xe3a00029\n.inst 0xebff7494\n.inst 0xe3500001\n.inst 0x0a00000f\n.inst 0xe3540018\n.inst 0x0a000006\n.inst 0xe3540064\n.inst 0xaa000004\n.inst 0xe1a00004\n.inst 0xebff748c\n.inst 0xe3500001\n.inst 0xe320f000\n.inst 0x0a000006\n.inst 0xe2850b33\n.inst 0xe3a02001\n.inst 0xe3a01000\n.inst 0xe1c02bb8\n.inst 0xe1c01bba\n.inst 0xe1c04bbc\n.inst 0xe1c06bbe\n.inst 0xe8bd8070\n.word 0x00447a78\n");
}

// DECOMP_FUNC(0x00289044, 140)
extern "C" __attribute__((naked)) void camp_func_00289044() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe2516000\n.inst 0xe1a07000\n.inst 0xaa000004\n.inst 0xeb00b5a4\n.inst 0xe1d001fc\n.inst 0xe1500007\n.inst 0xba000013\n.inst 0xea000017\n.inst 0xe320f000\n.inst 0xeb007e65\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe0850004\n.inst 0xe2800a09\n.inst 0xe1d00fd0\n.inst 0xe3500000\n.inst 0xba00000b\n.inst 0xeb007e54\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000007\n.inst 0xe1d014b6\n.inst 0xe1510006\n.inst 0x1a000004\n.inst 0xe1d000fe\n.inst 0xe1500007\n.inst 0xaa000001\n.inst 0xe3a00001\n.inst 0xe8bd81f0\n.inst 0xe2844001\n.inst 0xe3540018\n.inst 0xbaffffeb\n.inst 0xe3a00000\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x0028de84, 136)
extern "C" __attribute__((naked)) void script_vm_func_0028de84() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe5d00023\n.inst 0xe3e05000\n.inst 0xe3500000\n.inst 0x1a000019\n.inst 0xe5940034\n.inst 0xe3500000\n.inst 0xaa000002\n.inst 0xeb00a20f\n.inst 0xe1d027b2\n.inst 0xea000002\n.inst 0xe320f000\n.inst 0xeb006ac9\n.inst 0xe1d024b4\n.inst 0xe3a00001\n.inst 0xe3a01000\n.inst 0xe1a03000\n.inst 0xe1120013\n.inst 0x0a000008\n.inst 0xe594c01c\n.inst 0xe15c0001\n.inst 0x12811001\n.inst 0x1a000004\n.inst 0xe6bf0070\n.inst 0xeb008a26\n.inst 0xe1a05000\n.inst 0xe320f000\n.inst 0xea000002\n.inst 0xe2800001\n.inst 0xe350000b\n.inst 0xbafffff1\n.inst 0xe1a00005\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002918c4, 140)
extern "C" __attribute__((naked)) void ui_func_002918c4() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3500000\n.inst 0xed9f0a1e\n.inst 0xe1a05001\n.inst 0xe1a04002\n.inst 0x0a00000a\n.inst 0xe3500001\n.inst 0x0a000010\n.inst 0xe3500002\n.inst 0x1a00000d\n.inst 0xe3a01001\n.inst 0xe3a00000\n.inst 0xeb0015c2\n.inst 0xe6af0070\n.inst 0xe3500000\n.inst 0xe1a01005\n.inst 0x0a000007\n.inst 0xe3a00000\n.inst 0xeb0015bc\n.inst 0xee000a10\n.inst 0xee004a90\n.inst 0xeeb81ac0\n.inst 0xeef80a60\n.inst 0xee810a20\n.inst 0xe8bd8070\n.inst 0xe3a00000\n.inst 0xeb0015b4\n.inst 0xee000a10\n.inst 0xee004a90\n.inst 0xeeb80ac0\n.inst 0xeef80a60\n.inst 0xee801a20\n.inst 0xeeb10a41\n.inst 0xe8bd8070\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x00295300, 140)
extern "C" __attribute__((naked)) void ui_func_00295300() {
    asm volatile(".arm\n.inst 0xe5901028\n.inst 0xe3510000\n.inst 0x03a00000\n.inst 0x0a00001c\n.inst 0xe5d0203c\n.inst 0xe3520000\n.inst 0x1a000018\n.inst 0xe3a02001\n.inst 0xe5c0203c\n.inst 0xe5801010\n.inst 0xe59f2058\n.inst 0xe5913000\n.inst 0xe1530002\n.inst 0x13a01000\n.inst 0x15801010\n.inst 0x1a00000f\n.inst 0xe2812028\n.inst 0xe5802014\n.inst 0xe1d130b4\n.inst 0xe0822283\n.inst 0xe5802018\n.inst 0xe5913008\n.inst 0xe0833103\n.inst 0xe0822183\n.inst 0xe580201c\n.inst 0xe1d130b6\n.inst 0xe0822103\n.inst 0xe5802020\n.inst 0xe1d110bc\n.inst 0xe0811081\n.inst 0xe0821181\n.inst 0xe5801024\n.inst 0xe3a00001\n.inst 0xe12fff1e\n.word 0x57444b4e\n");
}

// DECOMP_FUNC(0x00295f04, 140)
extern "C" __attribute__((naked)) void script_vm_func_00295f04() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3510063\n.inst 0xe1a06000\n.inst 0xe1a04001\n.inst 0xa3a00000\n.inst 0xaa00001a\n.inst 0xe1a05004\n.inst 0xe3a01001\n.inst 0xe3a00009\n.inst 0xeb00abe5\n.inst 0xeb00abda\n.inst 0xe0800105\n.inst 0xe5105004\n.inst 0xe1a00006\n.inst 0xeb008d08\n.inst 0xe5d00003\n.inst 0xe0440000\n.inst 0xe2804001\n.inst 0xe3540000\n.inst 0xd3a00064\n.inst 0xda000007\n.inst 0xe354000a\n.inst 0xc3a0400a\n.inst 0xe3a01002\n.inst 0xe3a00009\n.inst 0xeb00abd5\n.inst 0xeb00abca\n.inst 0xe0800084\n.inst 0xe15000b2\n.inst 0xe59f100c\n.inst 0xe0000095\n.inst 0xe0801091\n.inst 0xe1a002a0\n.inst 0xe8bd8070\n.word 0x51eb851f\n");
}

// DECOMP_FUNC(0x002960d4, 128)
extern "C" __attribute__((naked)) void camp_func_002960d4() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a04001\n.inst 0xe1a07000\n.inst 0xe1a05002\n.inst 0xe3a01001\n.inst 0xe3a00009\n.inst 0xeb00ab74\n.inst 0xeb00ab69\n.inst 0xe0800104\n.inst 0xe5106004\n.inst 0xe1a00007\n.inst 0xeb008c97\n.inst 0xe5d00003\n.inst 0xe0450000\n.inst 0xe2804001\n.inst 0xe3540000\n.inst 0xd3a00064\n.inst 0xda000007\n.inst 0xe354000a\n.inst 0xc3a0400a\n.inst 0xe3a01002\n.inst 0xe3a00009\n.inst 0xeb00ab64\n.inst 0xeb00ab59\n.inst 0xe0800084\n.inst 0xe15000b2\n.inst 0xe59f100c\n.inst 0xe0000096\n.inst 0xe0801091\n.inst 0xe1a002a0\n.inst 0xe8bd81f0\n.word 0x51eb851f\n");
}

// DECOMP_FUNC(0x0029933c, 152)
extern "C" __attribute__((naked)) void camp_func_0029933c() {
    asm volatile(".arm\n.inst 0xe59f0088\n.inst 0xe92d4038\n.inst 0xe5904008\n.inst 0xeb009e11\n.inst 0xe2800b7d\n.inst 0xe2800054\n.inst 0xe5900000\n.inst 0xe3500000\n.inst 0x03a00001\n.inst 0x0a000018\n.inst 0xeb009e0a\n.inst 0xe2800b7d\n.inst 0xe2800054\n.inst 0xe3a01001\n.inst 0xe5900000\n.inst 0xe3a0200b\n.inst 0xe28430a4\n.inst 0xe584009c\n.inst 0xe5c410a1\n.inst 0xe5c410a0\n.inst 0xe2840b02\n.inst 0xe280006c\n.inst 0xe58d2000\n.inst 0xed9f0a0c\n.inst 0xe3e02000\n.inst 0xe3a0100e\n.inst 0xe1a04000\n.inst 0xeb0091df\n.inst 0xe3a01016\n.inst 0xe1a00004\n.inst 0xeb007f49\n.inst 0xe3a01006\n.inst 0xe1a00004\n.inst 0xeb00971a\n.inst 0xe3a00001\n.inst 0xe8bd8038\n.word 0x0043e188\n.word 0x3f800000\n");
}

// DECOMP_FUNC(0x0029957c, 144)
extern "C" __attribute__((naked)) void engine_func_0029957c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe59f407c\n.inst 0xe3500000\n.inst 0xe2841000\n.inst 0xe5942004\n.inst 0xe5911004\n.inst 0xe2811d7a\n.inst 0x0a000004\n.inst 0xe3500001\n.inst 0x0a000006\n.inst 0xe3500002\n.inst 0x0a000009\n.inst 0xea00000d\n.inst 0xe5910000\n.inst 0xe3a02007\n.inst 0xe3a01000\n.inst 0xea000002\n.inst 0xe5910000\n.inst 0xe3a02007\n.inst 0xe3a01001\n.inst 0xebffec48\n.inst 0xea000004\n.inst 0xe2822d7a\n.inst 0xe3a01002\n.inst 0xe5920000\n.inst 0xe3a02007\n.inst 0xebffec42\n.inst 0xe5940004\n.inst 0xe59f3014\n.inst 0xe3a02000\n.inst 0xe3a01006\n.inst 0xe5802010\n.inst 0xe7831000\n.inst 0xe8bd8010\n.word 0x0044e140\n.word 0x000012dc\n");
}

// DECOMP_FUNC(0x0029bddc, 140)
extern "C" __attribute__((naked)) void engine_func_0029bddc() {
    asm volatile(".arm\n.inst 0xe92d40f8\n.inst 0xe1a05001\n.inst 0xe1a06000\n.inst 0xeb00155b\n.inst 0xe1a04000\n.inst 0xe5900008\n.inst 0xe3a01000\n.inst 0xe5805008\n.inst 0xe1a00006\n.inst 0xeb00518b\n.inst 0xe3a01001\n.inst 0xe5840004\n.inst 0xeb005181\n.inst 0xe5940004\n.inst 0xebf9f0e5\n.inst 0xe5940004\n.inst 0xe1a0100d\n.inst 0xebfa7142\n.inst 0xe59d1000\n.inst 0xeb005b52\n.inst 0xe1a01000\n.inst 0xe5940008\n.inst 0xe5801004\n.inst 0xe5940008\n.inst 0xe1a01005\n.inst 0xeb003594\n.inst 0xe1a00004\n.inst 0xeb005ab6\n.inst 0xe59f0010\n.inst 0xe3a02000\n.inst 0xe1a01004\n.inst 0xeb005a6d\n.inst 0xe1a00004\n.inst 0xe8bd80f8\n.word 0x004dad60\n");
}

// DECOMP_FUNC(0x002a140c, 148)
extern "C" __attribute__((naked)) void engine_func_002a140c() {
    asm volatile(".arm\n.inst 0xe52de004\n.inst 0xeb000058\n.inst 0xe2001bff\n.inst 0xe3510b4e\n.inst 0x1a00001a\n.inst 0xe59f106c\n.inst 0xe1500001\n.inst 0xe0402001\n.inst 0x0a00000e\n.inst 0xca00000f\n.inst 0xe282160a\n.inst 0xe2911007\n.inst 0x0a00000a\n.inst 0xe59f2050\n.inst 0xe0911002\n.inst 0x12411502\n.inst 0x12511088\n.inst 0x0a000005\n.inst 0xe1a00b00\n.inst 0xe1a00b20\n.inst 0xe3500060\n.inst 0xba000009\n.inst 0xe3500080\n.inst 0xaa000007\n.inst 0xe3a00001\n.inst 0xe49df004\n.inst 0xe59f1020\n.inst 0xe0911000\n.inst 0x12411602\n.inst 0x12511008\n.inst 0x0afffff8\n.inst 0xeafffff1\n.inst 0xe3a00000\n.inst 0xe49df004\n.word 0xc9413910\n.word 0xffe00084\n.word 0x36bec6ee\n");
}

// DECOMP_FUNC(0x002a515c, 128)
extern "C" __attribute__((naked)) void engine_func_002a515c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe59f0068\n.inst 0xe1a06001\n.inst 0xe5904000\n.inst 0xe3540000\n.inst 0x03a00000\n.inst 0x0a000012\n.inst 0xe59405e4\n.inst 0xe3500000\n.inst 0x0a000010\n.inst 0xeb0023f7\n.inst 0xe3500000\n.inst 0x0a00000d\n.inst 0xe59405e4\n.inst 0xe59f1038\n.inst 0xe1a02005\n.inst 0xe5900008\n.inst 0xe7911106\n.inst 0xeb0023b1\n.inst 0xe3560000\n.inst 0x1a000004\n.inst 0xe2841b01\n.inst 0xed950a02\n.inst 0xedd10a90\n.inst 0xee300a20\n.inst 0xed850a02\n.inst 0xe8bd8070\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x0043dfc0\n.word 0x0043e048\n");
}

// DECOMP_FUNC(0x002a9414, 132)
extern "C" __attribute__((naked)) void func_002a9414() {
    asm volatile(".arm\n.inst 0xe59f3078\n.inst 0xe52de004\n.inst 0xe24dd034\n.inst 0xe283ce13\n.inst 0xe2833e15\n.inst 0xec9c0a08\n.inst 0xec8d0a08\n.inst 0xec930a04\n.inst 0xe28d3020\n.inst 0xec830a04\n.inst 0xe5903008\n.inst 0xe58d3000\n.inst 0xe5903004\n.inst 0xe58d3008\n.inst 0xe5900000\n.inst 0xe58d000c\n.inst 0xe5910008\n.inst 0xe58d0010\n.inst 0xe5910004\n.inst 0xe58d0018\n.inst 0xe5910000\n.inst 0xe3a01030\n.inst 0xe58d001c\n.inst 0xe5920004\n.inst 0xe58d0028\n.inst 0xe5920000\n.inst 0xe3a02001\n.inst 0xe58d002c\n.inst 0xe1a0000d\n.inst 0xeb001269\n.inst 0xe28dd034\n.inst 0xe49df004\n.word 0x00409780\n");
}

// DECOMP_FUNC(0x002b0614, 140)
extern "C" __attribute__((naked)) void engine_func_002b0614() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xeb004b1b\n.inst 0xe3500008\n.inst 0xc3a00008\n.inst 0xca000002\n.inst 0xe3500000\n.inst 0xd3a01000\n.inst 0xda000009\n.inst 0xe2001001\n.inst 0xe3510000\n.inst 0xe3a02000\n.inst 0xda000005\n.inst 0xe7d43002\n.inst 0xe353003a\n.inst 0x0a000010\n.inst 0xe2822001\n.inst 0xe1510002\n.inst 0xcafffff9\n.inst 0xe1510000\n.inst 0xaa000009\n.inst 0xe7d42001\n.inst 0xe352003a\n.inst 0x0a000008\n.inst 0xe0842001\n.inst 0xe5d22001\n.inst 0xe352003a\n.inst 0x0a000004\n.inst 0xe2811002\n.inst 0xe1500001\n.inst 0xcafffff5\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002b32e0, 144)
extern "C" __attribute__((naked)) void func_002b32e0() {
    asm volatile(".arm\n.inst 0xe59f1084\n.inst 0xe92d0030\n.inst 0xe281201c\n.inst 0xe5914028\n.inst 0xe892100c\n.inst 0xe1520000\n.inst 0x8a000003\n.inst 0xe591502c\n.inst 0xe0822005\n.inst 0xe1500002\n.inst 0x9a000014\n.inst 0xe1530000\n.inst 0x8a000004\n.inst 0xe5912030\n.inst 0xe0822003\n.inst 0xe1500002\n.inst 0x93a00001\n.inst 0x9a00000e\n.inst 0xe15c0000\n.inst 0x8a000004\n.inst 0xe5912034\n.inst 0xe082200c\n.inst 0xe1500002\n.inst 0x93a00002\n.inst 0x9a000007\n.inst 0xe1540000\n.inst 0x8a000004\n.inst 0xe5911038\n.inst 0xe0811004\n.inst 0xe1510000\n.inst 0x23a00003\n.inst 0x2a000000\n.inst 0xe3a00000\n.inst 0xe8bd0030\n.inst 0xe12fff1e\n.word 0x00465120\n");
}

// DECOMP_FUNC(0x002b7584, 152)
extern "C" __attribute__((naked)) void func_002b7584() {
    asm volatile(".arm\n.inst 0xe2812028\n.inst 0xed9f0a22\n.inst 0xec921a02\n.inst 0xeec10a81\n.inst 0xedc00a04\n.inst 0xed911a0a\n.inst 0xedd10a0b\n.inst 0xee311a40\n.inst 0xeec01a81\n.inst 0xedc01a05\n.inst 0xedd11a00\n.inst 0xed912a0a\n.inst 0xedd10a02\n.inst 0xed911a0b\n.inst 0xee611a82\n.inst 0xee302ac0\n.inst 0xeec10a21\n.inst 0xee221a20\n.inst 0xed801a00\n.inst 0xed911a02\n.inst 0xee311a00\n.inst 0xee610a20\n.inst 0xedc00a01\n.inst 0xedd11a05\n.inst 0xed912a0a\n.inst 0xedd10a06\n.inst 0xed911a0b\n.inst 0xee611a82\n.inst 0xee302a80\n.inst 0xeec10a21\n.inst 0xee221a20\n.inst 0xed801a03\n.inst 0xed911a06\n.inst 0xee310a40\n.inst 0xee200a20\n.inst 0xed800a02\n.inst 0xe12fff1e\n.word 0x3f800000\n");
}

// DECOMP_FUNC(0x002b8070, 148)
extern "C" __attribute__((naked)) void ui_func_002b8070() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xed2d8b0a\n.inst 0xeeb08b40\n.inst 0xeeb09b41\n.inst 0xeeb0ab42\n.inst 0xeeb0bb43\n.inst 0xeeb0ca44\n.inst 0xeb000124\n.inst 0xe3e03000\n.inst 0xeeb04a4c\n.inst 0xeef03a6b\n.inst 0xeeb03a4b\n.inst 0xeef02a6a\n.inst 0xeeb02a4a\n.inst 0xeef01a69\n.inst 0xeeb01a49\n.inst 0xeef00a68\n.inst 0xeeb00a48\n.inst 0xe1a02003\n.inst 0xe1a01003\n.inst 0xe1a00003\n.inst 0xeb00000e\n.inst 0xecbd8b0a\n.inst 0xe8bd4010\n.inst 0xe1a00000\n.inst 0xe59f0024\n.inst 0xe52de004\n.inst 0xe24dd01c\n.inst 0xe3a02001\n.inst 0xec900a06\n.inst 0xe3a01018\n.inst 0xe1a0000d\n.inst 0xec8d0a06\n.inst 0xebffd74e\n.inst 0xe28dd01c\n.inst 0xe49df004\n.word 0x00409898\n");
}

// DECOMP_FUNC(0x002b89fc, 132)
extern "C" __attribute__((naked)) void battle_func_002b89fc() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe59f5074\n.inst 0xe5954004\n.inst 0xe3540000\n.inst 0x0a000016\n.inst 0xe5940000\n.inst 0xebffe6c5\n.inst 0xe3500000\n.inst 0x1a000014\n.inst 0xe5d40018\n.inst 0xe3500000\n.inst 0x0a000011\n.inst 0xe5954004\n.inst 0xe3540000\n.inst 0x0a00000c\n.inst 0xe3a00001\n.inst 0xe5c40018\n.inst 0xe594001c\n.inst 0xe3a06000\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xebffba29\n.inst 0xe594001c\n.inst 0xebffe6b0\n.inst 0xe584601c\n.inst 0xe5950004\n.inst 0xeb002e3d\n.inst 0xe5856004\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x0044db88\n");
}

// DECOMP_FUNC(0x002baacc, 144)
extern "C" __attribute__((naked)) void engine_func_002baacc() {
    asm volatile(".arm\n.inst 0xe92d4030\n.inst 0xe24dd01c\n.inst 0xe3a05000\n.inst 0xe1a04000\n.inst 0xe5805000\n.inst 0xe5845004\n.inst 0xe5845008\n.inst 0xe584500c\n.inst 0xe3a00001\n.inst 0xe5845010\n.inst 0xe5c40414\n.inst 0xe5c40415\n.inst 0xe584541c\n.inst 0xe2840e42\n.inst 0xe5845418\n.inst 0xeb00220d\n.inst 0xe59f1044\n.inst 0xe3a00e31\n.inst 0xe3a02054\n.inst 0xe2413054\n.inst 0xe58d3004\n.inst 0xe58d1014\n.inst 0xe3a0c048\n.inst 0xe2433048\n.inst 0xe58d2008\n.inst 0xe58d0018\n.inst 0xe3a02078\n.inst 0xe2431078\n.inst 0xe2840e42\n.inst 0xe58d500c\n.inst 0xe58d5010\n.inst 0xe58dc000\n.inst 0xeb0021e9\n.inst 0xe28dd01c\n.inst 0xe8bd8030\n.word 0x003ff3f4\n");
}

// DECOMP_FUNC(0x002bc170, 144)
extern "C" __attribute__((naked)) void engine_func_002bc170() {
    asm volatile(".arm\n.inst 0xed9f3a1f\n.inst 0xee306ac0\n.inst 0xee304a80\n.inst 0xee715ac1\n.inst 0xee724ac2\n.inst 0xeddf2a1c\n.inst 0xee315a81\n.inst 0xedc02a01\n.inst 0xedc02a02\n.inst 0xedc02a04\n.inst 0xedc02a06\n.inst 0xeec30a06\n.inst 0xedc02a08\n.inst 0xedc02a09\n.inst 0xedc02a0c\n.inst 0xeddf3a11\n.inst 0xedc02a0d\n.inst 0xe2801038\n.inst 0xecc12a02\n.inst 0xee831a25\n.inst 0xee612a23\n.inst 0xee251a41\n.inst 0xee830a24\n.inst 0xee203aa3\n.inst 0xee640a60\n.inst 0xed800a0a\n.inst 0xee621a00\n.inst 0xed803a00\n.inst 0xedc00a03\n.inst 0xedc02a05\n.inst 0xed801a07\n.inst 0xedc01a0b\n.inst 0xe12fff1e\n.word 0x3f800000\n.word 0x40000000\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x002bdb2c, 152)
extern "C" __attribute__((naked)) void camp_func_002bdb2c() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe1a06001\n.inst 0xe1a04000\n.inst 0xe1a07002\n.inst 0xe1a05003\n.inst 0xed2d8b02\n.inst 0xeeb08a40\n.inst 0xe59d8028\n.inst 0xe3e09000\n.inst 0xe3a0108c\n.inst 0xeb001bf5\n.inst 0xe88402c0\n.inst 0xe3a01001\n.inst 0xeddf0a16\n.inst 0xed848a08\n.inst 0xe1c483b8\n.inst 0xedc40a09\n.inst 0xedc40a0a\n.inst 0xedc40a0b\n.inst 0xe5845048\n.inst 0xe595200c\n.inst 0xe584204c\n.inst 0xe5952010\n.inst 0xe5842058\n.inst 0xe5952014\n.inst 0xe5842064\n.inst 0xe5952018\n.inst 0xe5842070\n.inst 0xe595201c\n.inst 0xe5842078\n.inst 0xe5c41086\n.inst 0xe5c41087\n.inst 0xe5c41088\n.inst 0xe5c41089\n.inst 0xe5c4108a\n.inst 0xecbd8b02\n.inst 0xe8bd87f0\n.word 0x3f800000\n");
}

// DECOMP_FUNC(0x002bf0a8, 152)
extern "C" __attribute__((naked)) void ui_func_002bf0a8() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe1a04000\n.inst 0xe1a07001\n.inst 0xe1a08002\n.inst 0xe1a09003\n.inst 0xed2d8b02\n.inst 0xe28d1028\n.inst 0xeeb08a40\n.inst 0xe8910060\n.inst 0xe3a0108c\n.inst 0xeb001696\n.inst 0xe8840380\n.inst 0xe3a00001\n.inst 0xeddf0a16\n.inst 0xed848a08\n.inst 0xe1c463b8\n.inst 0xedc40a09\n.inst 0xedc40a0a\n.inst 0xedc40a0b\n.inst 0xe5845048\n.inst 0xe595100c\n.inst 0xe584104c\n.inst 0xe5951010\n.inst 0xe5841058\n.inst 0xe5951014\n.inst 0xe5841064\n.inst 0xe5951018\n.inst 0xe5841070\n.inst 0xe595101c\n.inst 0xe5841078\n.inst 0xe5c40086\n.inst 0xe5c40087\n.inst 0xe5c40088\n.inst 0xe5c40089\n.inst 0xe5c4008a\n.inst 0xecbd8b02\n.inst 0xe8bd87f0\n.word 0x3f800000\n");
}

// DECOMP_FUNC(0x002c25f4, 144)
extern "C" __attribute__((naked)) void engine_func_002c25f4() {
    asm volatile(".arm\n.inst 0xe59f007c\n.inst 0xe92d4010\n.inst 0xe590409c\n.inst 0xe3540000\n.inst 0x0a00001a\n.inst 0xe5940004\n.inst 0xe3500000\n.inst 0x1a000002\n.inst 0xe5940018\n.inst 0xe3500000\n.inst 0x0a000014\n.inst 0xe5941020\n.inst 0xe5940018\n.inst 0xe0611181\n.inst 0xe1a01101\n.inst 0xeb00093e\n.inst 0xe3a00000\n.inst 0xe584000c\n.inst 0xe5840010\n.inst 0xe5840020\n.inst 0xe5840028\n.inst 0xe5840014\n.inst 0xe5840024\n.inst 0xe5840034\n.inst 0xe59f1020\n.inst 0xe5840030\n.inst 0xe5940004\n.inst 0xe5810000\n.inst 0xe5941008\n.inst 0xe0800001\n.inst 0xe59f100c\n.inst 0xe5810000\n.inst 0xe8bd8010\n.word 0x004c6290\n.word 0x004652a0\n.word 0x004652a4\n");
}

// DECOMP_FUNC(0x002c3734, 128)
extern "C" __attribute__((naked)) void engine_func_002c3734() {
    asm volatile(".arm\n.inst 0xe59f2074\n.inst 0xe1b0c000\n.inst 0xe3a00000\n.inst 0xe92d4008\n.inst 0x03a03000\n.inst 0x02820088\n.inst 0x0a000005\n.inst 0xe35c0001\n.inst 0x03a03000\n.inst 0x028200c4\n.inst 0x0a000001\n.inst 0xe35c0002\n.inst 0x0a00000b\n.inst 0xe58d1000\n.inst 0xe0821203\n.inst 0xe082c103\n.inst 0xedd11a60\n.inst 0xe2811f5d\n.inst 0xe59c21b0\n.inst 0xed9c2a69\n.inst 0xe3a03007\n.inst 0xec910a03\n.inst 0xe2801018\n.inst 0xebf957b6\n.inst 0xe8bd8008\n.inst 0xe5920084\n.inst 0xe3500001\n.inst 0x13a03001\n.inst 0x12820c01\n.inst 0x1affffee\n.inst 0xe8bd8008\n.word 0x004e39e0\n");
}

// DECOMP_FUNC(0x002c854c, 136)
extern "C" __attribute__((naked)) void battle_func_002c854c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe5900008\n.inst 0xebffdbb0\n.inst 0xe3500000\n.inst 0x0a000016\n.inst 0xe59f005c\n.inst 0xe5900000\n.inst 0xe3500000\n.inst 0x0a000012\n.inst 0xe59f1050\n.inst 0xe5911000\n.inst 0xe3510000\n.inst 0x0a00000e\n.inst 0xe59f1044\n.inst 0xe5911000\n.inst 0xe3510000\n.inst 0x0a00000a\n.inst 0xe59f1038\n.inst 0xe5911000\n.inst 0xe3510000\n.inst 0x0a000006\n.inst 0xe5911634\n.inst 0xe3110702\n.inst 0x13a00000\n.inst 0x1a000003\n.inst 0xe590000c\n.inst 0xe2100004\n.inst 0x0a000000\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.word 0x00435d30\n.word 0x00434290\n.word 0x00435d18\n.word 0x004342c8\n");
}

// DECOMP_FUNC(0x002c8750, 128)
extern "C" __attribute__((naked)) void script_vm_func_002c8750() {
    asm volatile(".arm\n.inst 0xe59f0074\n.inst 0xe52d4004\n.inst 0xe3a01000\n.inst 0xe1a0c001\n.inst 0xe5902000\n.inst 0xe3a04001\n.inst 0xe0810081\n.inst 0xe0820380\n.inst 0xe5f03034\n.inst 0xe3530000\n.inst 0x15903174\n.inst 0x13530000\n.inst 0x0a00000c\n.inst 0xe353000b\n.inst 0xaa00000a\n.inst 0xe5d0307d\n.inst 0xe3530000\n.inst 0x1a000007\n.inst 0xe5903084\n.inst 0xe3530000\n.inst 0x0a000002\n.inst 0xe3530004\n.inst 0x13530005\n.inst 0x1a000001\n.inst 0xe2800084\n.inst 0xe8801010\n.inst 0xe2811001\n.inst 0xe3510020\n.inst 0xbaffffe8\n.inst 0xe49d4004\n.inst 0xe12fff1e\n.word 0x00447600\n");
}

// DECOMP_FUNC(0x002c8a78, 148)
extern "C" __attribute__((naked)) void script_vm_func_002c8a78() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a04008\n.inst 0xe3a07000\n.inst 0xe59f607c\n.inst 0xe0841084\n.inst 0xe0811184\n.inst 0xe5960000\n.inst 0xe0805101\n.inst 0xe2855a01\n.inst 0xe2855f45\n.inst 0xe5d50000\n.inst 0xe3500000\n.inst 0x15950020\n.inst 0x13500000\n.inst 0x0a000001\n.inst 0xebfa280f\n.inst 0xe5c57024\n.inst 0xe2544001\n.inst 0x5afffff0\n.inst 0xe3a04002\n.inst 0xe5960000\n.inst 0xe0841084\n.inst 0xe0811184\n.inst 0xe0805101\n.inst 0xe2855a01\n.inst 0xe2855e2a\n.inst 0xe5d50000\n.inst 0xe3500000\n.inst 0x15950020\n.inst 0x13500000\n.inst 0x0a000001\n.inst 0xebfa27ff\n.inst 0xe5c57024\n.inst 0xe2544001\n.inst 0x5afffff0\n.inst 0xe8bd81f0\n.word 0x00447e10\n");
}

// DECOMP_FUNC(0x002cf6d4, 128)
extern "C" __attribute__((naked)) void script_vm_func_002cf6d4() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a00001\n.inst 0xe59f606c\n.inst 0xe5964000\n.inst 0xe5c405c4\n.inst 0xebfe04ba\n.inst 0xe2840b01\n.inst 0xe2800f7f\n.inst 0xe1a05000\n.inst 0xebff3ed8\n.inst 0xe1a07000\n.inst 0xe1a00005\n.inst 0xebff3ecf\n.inst 0xe0800007\n.inst 0xe3a01001\n.inst 0xe0840080\n.inst 0xe2800c06\n.inst 0xe1d00cb4\n.inst 0xebff0263\n.inst 0xe3a02000\n.inst 0xe1a01002\n.inst 0xe2840034\n.inst 0xebffb8e3\n.inst 0xe5960000\n.inst 0xe3a01001\n.inst 0xe5902004\n.inst 0xe5802008\n.inst 0xe5a01004\n.inst 0xe3a02000\n.inst 0xe580200c\n.inst 0xe8bd81f0\n.word 0x0043dd50\n");
}

// DECOMP_FUNC(0x002cfc60, 128)
extern "C" __attribute__((naked)) void engine_func_002cfc60() {
    asm volatile(".arm\n.inst 0xe52de004\n.inst 0xe24dd044\n.inst 0xe3a00000\n.inst 0xebfe2627\n.inst 0xe3a02000\n.inst 0xe58d2000\n.inst 0xe58d2004\n.inst 0xe58d2008\n.inst 0xe58d200c\n.inst 0xe58d2010\n.inst 0xe58d2014\n.inst 0xe1a01000\n.inst 0xe58d2018\n.inst 0xe58d201c\n.inst 0xe58d2020\n.inst 0xe58d2024\n.inst 0xe58d2028\n.inst 0xe1a0000d\n.inst 0xe58d202c\n.inst 0xe58d2030\n.inst 0xe58d2034\n.inst 0xe58d2038\n.inst 0xe58d203c\n.inst 0xebffbeea\n.inst 0xe59f0014\n.inst 0xe1a0100d\n.inst 0xe5900000\n.inst 0xeb042dec\n.inst 0xe28dd044\n.inst 0xe3a00001\n.inst 0xe49df004\n.word 0x00435d18\n");
}

// DECOMP_FUNC(0x002d0400, 152)
extern "C" __attribute__((naked)) void script_vm_func_002d0400() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a05000\n.inst 0xe1a06001\n.inst 0xe1d000b0\n.inst 0xebff2321\n.inst 0xe1a07000\n.inst 0xe1d600b0\n.inst 0xe3a04000\n.inst 0xebff231d\n.inst 0xe1d71000\n.inst 0x13a04001\n.inst 0xe1d00007\n.inst 0x13e04000\n.inst 0x03540000\n.inst 0x1a00000b\n.inst 0xe1d500b0\n.inst 0xebff98ae\n.inst 0xe1a05000\n.inst 0xe1d600b0\n.inst 0xebff98ab\n.inst 0xe3550000\n.inst 0x13500000\n.inst 0xe3a04000\n.inst 0x0a000002\n.inst 0xe1d000b4\n.inst 0xe1d510b4\n.inst 0xe0404001\n.inst 0xe1a00004\n.inst 0xe8bd81f0\n.inst 0xe1a02000\n.inst 0xe5d00000\n.inst 0xe5d13000\n.inst 0xe0500003\n.inst 0x1a000002\n.inst 0xe5d20001\n.inst 0xe5d11001\n.inst 0xe0400001\n.inst 0xe12fff1e\n");
}

// DECOMP_FUNC(0x002d54c4, 128)
extern "C" __attribute__((naked)) void func_002d54c4() {
    asm volatile(".arm\n.inst 0xe59f0038\n.inst 0xe92d4010\n.inst 0xe5904000\n.inst 0xe3540000\n.inst 0x0a000006\n.inst 0xe5940000\n.inst 0xebff7413\n.inst 0xe3500000\n.inst 0x1a000004\n.inst 0xe5d40005\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0x00432cc8\n.inst 0xe1a01000\n.inst 0xe59f002c\n.inst 0xe92d4010\n.inst 0xe3a04000\n.inst 0xe5900004\n.inst 0xe3500000\n.inst 0x0a000004\n.inst 0xe5900018\n.inst 0xeb020c7e\n.inst 0xe2000102\n.inst 0xe3500000\n.inst 0xa3a04001\n.inst 0xe1a00004\n.inst 0xe8bd8010\n.word 0x00464fa8\n");
}

// DECOMP_FUNC(0x002d5780, 136)
extern "C" __attribute__((naked)) void script_vm_func_002d5780() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xed2d8b02\n.inst 0xeeb08a40\n.inst 0xe5900008\n.inst 0xebff1986\n.inst 0xeeb00a48\n.inst 0xe5940008\n.inst 0xebfedc4a\n.inst 0xe5940008\n.inst 0xeeb00a48\n.inst 0xecbd8b02\n.inst 0xe8bd4010\n.inst 0xe1a00000\n.inst 0xe5901068\n.inst 0xe3510000\n.inst 0xda00000f\n.inst 0xed800a20\n.inst 0xedd00a1d\n.inst 0xe590002c\n.inst 0xe3a01000\n.inst 0xee200a80\n.inst 0xe5902150\n.inst 0xe3520000\n.inst 0x0a000007\n.inst 0xe5902028\n.inst 0xe5900154\n.inst 0xe5923028\n.inst 0xe592201c\n.inst 0xe0201390\n.inst 0xe7920100\n.inst 0xe3500000\n.inst 0x1d800a10\n.inst 0xe12fff1e\n");
}

// DECOMP_FUNC(0x002d782c, 144)
extern "C" __attribute__((naked)) void func_002d782c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe59f007c\n.inst 0xe1a06002\n.inst 0xe5902000\n.inst 0xe1a00a21\n.inst 0xe1a01601\n.inst 0xe7920180\n.inst 0xe1a01621\n.inst 0xe3500000\n.inst 0x0a000005\n.inst 0xe5902024\n.inst 0xe1520001\n.inst 0x0a000003\n.inst 0xe590004c\n.inst 0xe3500000\n.inst 0x1afffff9\n.inst 0xe3a00000\n.inst 0xe3550000\n.inst 0xe590201c\n.inst 0xe3c612ff\n.inst 0x11811002\n.inst 0x01c21001\n.inst 0xe580101c\n.inst 0xe5904058\n.inst 0xe3540000\n.inst 0x0a000006\n.inst 0xe5941028\n.inst 0xe1a02006\n.inst 0xe1a00005\n.inst 0xebffffe0\n.inst 0xe594405c\n.inst 0xe3540000\n.inst 0x1afffff8\n.inst 0xe8bd8070\n.word 0x004e3cf4\n");
}

// DECOMP_FUNC(0x002dba40, 148)
extern "C" __attribute__((naked)) void ui_func_002dba40() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfeed44\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfee08e\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a00000e\n.inst 0xe3110040\n.inst 0x1a00000c\n.inst 0xe28000cc\n.inst 0xe1d02eb8\n.inst 0xe1d01efa\n.inst 0xe3a00064\n.inst 0xe1600082\n.inst 0xebffa9af\n.inst 0xe1500005\n.inst 0xe320f000\n.inst 0xca000003\n.inst 0xe3a00001\n.inst 0xebfec928\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe3\n.inst 0xe3a00000\n.inst 0xebfec921\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002e11bc, 148)
extern "C" __attribute__((naked)) void script_vm_func_002e11bc() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe5900008\n.inst 0xe1a05001\n.inst 0xebfdcea6\n.inst 0xe5940008\n.inst 0xe1a01005\n.inst 0xebffffe8\n.inst 0xe5940008\n.inst 0xe1a01005\n.inst 0xe8bd4070\n.inst 0xe1a00000\n.inst 0xe5902068\n.inst 0xe3520000\n.inst 0xda000012\n.inst 0xe590002c\n.inst 0xe3a02000\n.inst 0xe5903150\n.inst 0xe3530000\n.inst 0x0a00000d\n.inst 0xe5903028\n.inst 0xe5900154\n.inst 0xe593c028\n.inst 0xe593301c\n.inst 0xe0202c90\n.inst 0xe7930100\n.inst 0xe3500000\n.inst 0x0a000005\n.inst 0xe3510000\n.inst 0x059f1010\n.inst 0x159f1010\n.inst 0xe3a02001\n.inst 0xe5c02058\n.inst 0xe580104c\n.inst 0xe12fff1e\n.word 0x0015555c\n.word 0x00151404\n");
}

// DECOMP_FUNC(0x002e3af8, 132)
extern "C" __attribute__((naked)) void battle_func_002e3af8() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfecd16\n.inst 0xe3a01001\n.inst 0xe1a05011\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfec05f\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000009\n.inst 0xe3110040\n.inst 0x1a000007\n.inst 0xe2800c01\n.inst 0xe1d00cb6\n.inst 0xe1100005\n.inst 0x0a000003\n.inst 0xe3a00001\n.inst 0xebfea8fe\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe8\n.inst 0xe3a00000\n.inst 0xebfea8f7\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002eb59c, 152)
extern "C" __attribute__((naked)) void script_vm_func_002eb59c() {
    asm volatile(".arm\n.inst 0xe59f0088\n.inst 0xe92d4070\n.inst 0xe59f1084\n.inst 0xe5d00284\n.inst 0xe59f5078\n.inst 0xe5914000\n.inst 0xe3500000\n.inst 0x13a00000\n.inst 0x15c50284\n.inst 0x1a000018\n.inst 0xe2850094\n.inst 0xebfe1704\n.inst 0xe3a00001\n.inst 0xe5c502f8\n.inst 0xe594002c\n.inst 0xe58502fc\n.inst 0xe5940030\n.inst 0xe5850300\n.inst 0xe5950008\n.inst 0xe5850304\n.inst 0xe2850094\n.inst 0xecd00a03\n.inst 0xe2850fc2\n.inst 0xecc00a03\n.inst 0xed950a24\n.inst 0xed850ac5\n.inst 0xed850ac6\n.inst 0xed942a0b\n.inst 0xed852ac7\n.inst 0xed942a0c\n.inst 0xed852ac8\n.inst 0xed850acc\n.inst 0xed850acd\n.inst 0xe2855fc9\n.inst 0xecc50a03\n.inst 0xe8bd8070\n.word 0x0049f91c\n.word 0x00447e28\n");
}

// DECOMP_FUNC(0x002ed47c, 144)
extern "C" __attribute__((naked)) void engine_func_002ed47c() {
    asm volatile(".arm\n.inst 0xe59f0084\n.inst 0xe92d41f0\n.inst 0xe24dd008\n.inst 0xe5904004\n.inst 0xebfe64fb\n.inst 0xe3500014\n.inst 0x03a00005\n.inst 0xe1a05000\n.inst 0xebfe64f2\n.inst 0xe1a07000\n.inst 0xe3a00000\n.inst 0xebfea6ac\n.inst 0xe1a06000\n.inst 0xebfe7062\n.inst 0xe3a08000\n.inst 0xe1a02000\n.inst 0xe1a03005\n.inst 0xe1a01006\n.inst 0xe1a00007\n.inst 0xe58d8000\n.inst 0xe58d8004\n.inst 0xebfe6514\n.inst 0xe1a05000\n.inst 0xebfe7058\n.inst 0xe3500000\n.inst 0x1a000005\n.inst 0xe5940004\n.inst 0xebff2c21\n.inst 0xe594000c\n.inst 0xe5c48a10\n.inst 0xe3800020\n.inst 0xe584000c\n.inst 0xe28dd008\n.inst 0xe1a00005\n.inst 0xe8bd81f0\n.word 0x0043e188\n");
}

// DECOMP_FUNC(0x002f02b8, 132)
extern "C" __attribute__((naked)) void battle_func_002f02b8() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe9b26\n.inst 0xe3a06001\n.inst 0xe1a05016\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe8e6f\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000009\n.inst 0xe3110040\n.inst 0x1a000007\n.inst 0xe2800c01\n.inst 0xe1d00cb6\n.inst 0xe1100005\n.inst 0x0a000003\n.inst 0xe3a00001\n.inst 0xebfe770e\n.inst 0xe1a00006\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe8\n.inst 0xe3a00000\n.inst 0xebfe7707\n.inst 0xe1a00006\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002f033c, 148)
extern "C" __attribute__((naked)) void ui_func_002f033c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe9b05\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe8e4f\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a00000e\n.inst 0xe3110040\n.inst 0x1a00000c\n.inst 0xe28000cc\n.inst 0xe1d02eb8\n.inst 0xe1d01efa\n.inst 0xe3a00064\n.inst 0xe1600082\n.inst 0xebff5770\n.inst 0xe1500005\n.inst 0xe320f000\n.inst 0xba000003\n.inst 0xe3a00001\n.inst 0xebfe76e9\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe3\n.inst 0xe3a00000\n.inst 0xebfe76e2\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002f0520, 140)
extern "C" __attribute__((naked)) void ui_func_002f0520() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a00000\n.inst 0xebfe9a8c\n.inst 0xe3a05000\n.inst 0xe1a07000\n.inst 0xe1a06005\n.inst 0xe1a04005\n.inst 0xe320f000\n.inst 0xebfe8dd4\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000005\n.inst 0xe3110040\n.inst 0x1a000003\n.inst 0xe2800c01\n.inst 0xe2866001\n.inst 0xe1d00cbc\n.inst 0xe0855000\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffec\n.inst 0xe1a01006\n.inst 0xe1a00005\n.inst 0xebff56f1\n.inst 0xe1570000\n.inst 0xd3a00001\n.inst 0xc3a00000\n.inst 0xebfe766b\n.inst 0xe3a00001\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x002f05ac, 136)
extern "C" __attribute__((naked)) void battle_func_002f05ac() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe9a69\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe3a06002\n.inst 0xe320f000\n.inst 0xebfe8db2\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a00000a\n.inst 0xe3110040\n.inst 0x1a000008\n.inst 0xe0800085\n.inst 0xe2800c01\n.inst 0xe1d00fb2\n.inst 0xe1560520\n.inst 0x1a000003\n.inst 0xe3a00001\n.inst 0xebfe7650\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe7\n.inst 0xe3a00000\n.inst 0xebfe7649\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002f10dc, 132)
extern "C" __attribute__((naked)) void engine_func_002f10dc() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xebfe8aec\n.inst 0xe1a04000\n.inst 0xe3a00000\n.inst 0xebfe979b\n.inst 0xe1a05000\n.inst 0xe3a00001\n.inst 0xebfe9798\n.inst 0xe1a06000\n.inst 0xebfe614e\n.inst 0xe59f7050\n.inst 0xe3500000\n.inst 0x0a000005\n.inst 0xe5970000\n.inst 0xe5900080\n.inst 0xe3500004\n.inst 0x03a00001\n.inst 0x13a00000\n.inst 0xe8bd81f0\n.inst 0xe5970000\n.inst 0xe1a01004\n.inst 0xeb035c04\n.inst 0xe2840f4f\n.inst 0xe1a01004\n.inst 0xe8800060\n.inst 0xe5970000\n.inst 0xeb035b58\n.inst 0xe5970000\n.inst 0xe320f000\n.inst 0xebfe361e\n.inst 0xe3a00000\n.inst 0xe8bd81f0\n.word 0x004398d4\n");
}

// DECOMP_FUNC(0x002f2878, 128)
extern "C" __attribute__((naked)) void camp_func_002f2878() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe1d000b0\n.inst 0xe1a05001\n.inst 0xebfeb11e\n.inst 0xe1a06000\n.inst 0xe1d500b0\n.inst 0xebfeb11b\n.inst 0xe1d01006\n.inst 0x13a00001\n.inst 0x1a000013\n.inst 0xe1d60000\n.inst 0x13e00000\n.inst 0x1a000010\n.inst 0xe1d400b0\n.inst 0xebff1aaa\n.inst 0xe1a04000\n.inst 0xe1d500b0\n.inst 0xebff1aa7\n.inst 0xe1a01000\n.inst 0xe5d00002\n.inst 0xe5d42002\n.inst 0xe0500002\n.inst 0x1a000006\n.inst 0xe5d40003\n.inst 0xe5d12003\n.inst 0xe0500002\n.inst 0x1a000002\n.inst 0xe1d100b0\n.inst 0xe1d410b0\n.inst 0xe0400001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002f6cf0, 148)
extern "C" __attribute__((naked)) void ui_func_002f6cf0() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a00000\n.inst 0xebfe8098\n.inst 0xe3a05000\n.inst 0xe1a07000\n.inst 0xe1a06005\n.inst 0xe1a04005\n.inst 0xe320f000\n.inst 0xebfe73e0\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000006\n.inst 0xe3110040\n.inst 0x1a000004\n.inst 0xe2800c01\n.inst 0xe1d01bf6\n.inst 0xe1d00bf4\n.inst 0xe0855001\n.inst 0xe0866000\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffeb\n.inst 0xe3a00064\n.inst 0xe1a01005\n.inst 0xe0000096\n.inst 0xebff3cfb\n.inst 0xe1500007\n.inst 0xd3a00001\n.inst 0xc3a00000\n.inst 0xebfe5c75\n.inst 0xe3a00001\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x002f6f08, 136)
extern "C" __attribute__((naked)) void battle_func_002f6f08() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe8012\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe3a06001\n.inst 0xe320f000\n.inst 0xebfe735b\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a00000a\n.inst 0xe3110040\n.inst 0x1a000008\n.inst 0xe0800085\n.inst 0xe2800c01\n.inst 0xe1d00fb2\n.inst 0xe1560520\n.inst 0x1a000003\n.inst 0xe3a00001\n.inst 0xebfe5bf9\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe7\n.inst 0xe3a00000\n.inst 0xebfe5bf2\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002f6f90, 140)
extern "C" __attribute__((naked)) void battle_func_002f6f90() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe7ff0\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe3a06002\n.inst 0xe320f000\n.inst 0xebfe7339\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000001\n.inst 0xe3110040\n.inst 0x0a000006\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbafffff0\n.inst 0xe3a00000\n.inst 0xebfe5bd9\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe0800085\n.inst 0xe2800c01\n.inst 0xe1d00fb2\n.inst 0xe3100b3f\n.inst 0x11560520\n.inst 0x1afffff2\n.inst 0xe3a00001\n.inst 0xebfe5bcf\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002fb4c0, 140)
extern "C" __attribute__((naked)) void script_vm_func_002fb4c0() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xebfe385d\n.inst 0xe3500000\n.inst 0x0a00000c\n.inst 0xebfe385a\n.inst 0xe3500001\n.inst 0x0a000013\n.inst 0xebfe3857\n.inst 0xe3500003\n.inst 0xb3a00000\n.inst 0xba000004\n.inst 0xe3e00000\n.inst 0xebfe4a91\n.inst 0xe3a00000\n.inst 0xebfe4a83\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe3a00001\n.inst 0xebfe4a8b\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xebfdead0\n.inst 0xe3a00003\n.inst 0xe320f000\n.inst 0xebfdd35c\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe59f0014\n.inst 0xebfef723\n.inst 0xe3a00001\n.inst 0xe320f000\n.inst 0xebfdd355\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.word 0x01000184\n");
}

// DECOMP_FUNC(0x002fe924, 132)
extern "C" __attribute__((naked)) void script_vm_func_002fe924() {
    asm volatile(".arm\n.inst 0xe3a00000\n.inst 0xe92d4010\n.inst 0xebfe618b\n.inst 0xe59f106c\n.inst 0xe3500000\n.inst 0xe5d10251\n.inst 0x0a000002\n.inst 0xe3500000\n.inst 0x0a00000b\n.inst 0xea000013\n.inst 0xe3500000\n.inst 0x0a000011\n.inst 0xe3a00000\n.inst 0xe5c10251\n.inst 0xebfd6e6d\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xebfddc2a\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xea000008\n.inst 0xe3a00001\n.inst 0xe5c10251\n.inst 0xebfddd2c\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xebfe2c55\n.inst 0xe3a00090\n.inst 0xe320f000\n.inst 0xebfee876\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.word 0x0049f91c\n");
}

// DECOMP_FUNC(0x002fed1c, 136)
extern "C" __attribute__((naked)) void battle_func_002fed1c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe608d\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe3a06003\n.inst 0xe320f000\n.inst 0xebfe53d6\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a00000a\n.inst 0xe3110040\n.inst 0x1a000008\n.inst 0xe0800085\n.inst 0xe2800c01\n.inst 0xe1d00fb2\n.inst 0xe1560520\n.inst 0x1a000003\n.inst 0xe3a00001\n.inst 0xebfe3c74\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe7\n.inst 0xe3a00000\n.inst 0xebfe3c6d\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002ff050, 148)
extern "C" __attribute__((naked)) void engine_func_002ff050() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe5fc0\n.inst 0xe1a05000\n.inst 0xe3a00001\n.inst 0xebfe5fbd\n.inst 0xe1a06000\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe5307\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a00000b\n.inst 0xe3110040\n.inst 0x01d01cbe\n.inst 0x01510005\n.inst 0x1a000007\n.inst 0xe2800c01\n.inst 0xe1d00cbc\n.inst 0xe1500006\n.inst 0xba000003\n.inst 0xe3a00001\n.inst 0xebfe3ba4\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe6\n.inst 0xe3a00000\n.inst 0xebfe3b9d\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002ff180, 136)
extern "C" __attribute__((naked)) void battle_func_002ff180() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe5f74\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe3a06004\n.inst 0xe320f000\n.inst 0xebfe52bd\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a00000a\n.inst 0xe3110040\n.inst 0x1a000008\n.inst 0xe0800085\n.inst 0xe2800c01\n.inst 0xe1d00fb2\n.inst 0xe1560520\n.inst 0x1a000003\n.inst 0xe3a00001\n.inst 0xebfe3b5b\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe7\n.inst 0xe3a00000\n.inst 0xebfe3b54\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002ff208, 132)
extern "C" __attribute__((naked)) void battle_func_002ff208() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe5f52\n.inst 0xe3a01001\n.inst 0xe1a05011\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe529b\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000005\n.inst 0xe3110040\n.inst 0x1a000003\n.inst 0xe2800c01\n.inst 0xe1d00cb6\n.inst 0xe1100005\n.inst 0x0a000006\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffec\n.inst 0xe3a00000\n.inst 0xebfe3b37\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe3a00001\n.inst 0xebfe3b33\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}
