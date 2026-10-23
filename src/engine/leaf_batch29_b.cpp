#include "types.h"

// Batch 29 B: exact ARM bytes; post-return literal words are preserved as data.

// DECOMP_FUNC(0x0020087c, 56)
extern "C" __attribute__((naked)) void engine_func_0020087c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xeb02236e\n.inst 0xe3500000\n.inst 0x0a000005\n.inst 0xeb033428\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb046e65\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe320f000\n.inst 0xeb042713\n.inst 0xe3a00000\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x00205b14, 80)
extern "C" __attribute__((naked)) void engine_func_00205b14() {
    asm volatile(".arm\n.inst 0xe3a00000\n.inst 0xe92d4010\n.inst 0xeb02450f\n.inst 0xe1a04000\n.inst 0xe3a00001\n.inst 0xeb02450c\n.inst 0xe1540000\n.inst 0xba000003\n.inst 0xe3a00001\n.inst 0xeb022105\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe6ff0070\n.inst 0xeb02ec1f\n.inst 0xe1500004\n.inst 0xa3a00000\n.inst 0xb3a00001\n.inst 0xeb0220fd\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x00208b00, 68)
extern "C" __attribute__((naked)) void script_vm_func_00208b00() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xeb02e803\n.inst 0xe3540000\n.inst 0xba00000a\n.inst 0xe1a01fc4\n.inst 0xe3a03001\n.inst 0xe0842da1\n.inst 0xe1a012c2\n.inst 0xe3c2201f\n.inst 0xe0442002\n.inst 0xe0800101\n.inst 0xe1a01213\n.inst 0xe59027d4\n.inst 0xe1811002\n.inst 0xe58017d4\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x00211c04, 76)
extern "C" __attribute__((naked)) void engine_func_00211c04() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe59f503c\n.inst 0xe1d500d0\n.inst 0xe3500000\n.inst 0xca000008\n.inst 0xe3a00013\n.inst 0xeb02cc81\n.inst 0xe3a04000\n.inst 0xe1a01004\n.inst 0xe3a00013\n.inst 0xeb02cfa1\n.inst 0xe2844001\n.inst 0xe3540008\n.inst 0xbafffff9\n.inst 0xe5d50000\n.inst 0xe2800001\n.inst 0xe5c50000\n.inst 0xe8bd8070\n.word 0x0043dc70\n");
}

// DECOMP_FUNC(0x00211df4, 96)
extern "C" __attribute__((naked)) void battle_func_00211df4() {
    asm volatile(".arm\n.inst 0xe3a00000\n.inst 0xe92d4010\n.inst 0xeb021457\n.inst 0xe1a04000\n.inst 0xeb02b584\n.inst 0xe3500000\n.inst 0x0a000008\n.inst 0xe1a00004\n.inst 0xeb02bb2b\n.inst 0xe5901004\n.inst 0xe3510001\n.inst 0x0a000005\n.inst 0xe3a01001\n.inst 0xed9f0a08\n.inst 0xed800a04\n.inst 0xe5c01014\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe3a01000\n.inst 0xe1a00004\n.inst 0xeb02c9db\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.word 0xbe800000\n");
}

// DECOMP_FUNC(0x00217538, 88)
extern "C" __attribute__((naked)) void func_00217538() {
    asm volatile(".arm\n.inst 0xe59f004c\n.inst 0xed9f2a11\n.inst 0xec901a02\n.inst 0xed900a02\n.inst 0xee610a01\n.inst 0xee410aa1\n.inst 0xee400a00\n.inst 0xeeb10ae0\n.inst 0xeeb40ac2\n.inst 0xeef1fa10\n.inst 0xda000007\n.inst 0xeeb02a61\n.inst 0xeec11a00\n.inst 0xedd00a02\n.inst 0xedc01a00\n.inst 0xee821a00\n.inst 0xed801a01\n.inst 0xee802a80\n.inst 0xed802a02\n.inst 0xe12fff1e\n.word 0x00000000\n.word 0x004ea91c\n");
}

// DECOMP_FUNC(0x0021f43c, 68)
extern "C" __attribute__((naked)) void engine_func_0021f43c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe59f4034\n.inst 0xe5940004\n.inst 0xe8900006\n.inst 0xe5900018\n.inst 0xeb011037\n.inst 0xe2000102\n.inst 0xe3500000\n.inst 0xa5940004\n.inst 0xb3a00000\n.inst 0xa5900018\n.inst 0xa59043c0\n.inst 0xba000001\n.inst 0xeb006719\n.inst 0xe1a00004\n.inst 0xe8bd8010\n.word 0x00464fa8\n");
}

// DECOMP_FUNC(0x0021f5bc, 44)
extern "C" __attribute__((naked)) void func_0021f5bc() {
    asm volatile(".arm\n.inst 0xe3500000\n.inst 0xb3a00000\n.inst 0xba000005\n.inst 0xe0812281\n.inst 0xe0821381\n.inst 0xe59f200c\n.inst 0xe0821101\n.inst 0xe0810100\n.inst 0xe5900264\n.inst 0xe12fff1e\n.word 0x004d9880\n");
}

// DECOMP_FUNC(0x0022033c, 88)
extern "C" __attribute__((naked)) void engine_func_0022033c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe24dde1f\n.inst 0xe3a02001\n.inst 0xe1a0100d\n.inst 0xeb00d1dc\n.inst 0xe3500000\n.inst 0x0a000007\n.inst 0xeb0235ed\n.inst 0xe1a0000d\n.inst 0xeb022131\n.inst 0xe1a04000\n.inst 0xeb028ce9\n.inst 0xe28dde1f\n.inst 0xe1a00004\n.inst 0xe8bd8010\n.inst 0xe59f0010\n.inst 0xe1a04000\n.inst 0xeb028ce3\n.inst 0xe28dde1f\n.inst 0xe1a00004\n.inst 0xe8bd8010\n.word 0xe0e046bc\n");
}

// DECOMP_FUNC(0x00220458, 80)
extern "C" __attribute__((naked)) void battle_func_00220458() {
    asm volatile(".arm\n.inst 0xe59f0044\n.inst 0xe92d4070\n.inst 0xe5906000\n.inst 0xe3560000\n.inst 0x13a04001\n.inst 0x0a00000b\n.inst 0xe0865104\n.inst 0xe5950630\n.inst 0xeb027be7\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000002\n.inst 0xe5950630\n.inst 0xe3a01001\n.inst 0xeb025c02\n.inst 0xe2844001\n.inst 0xe3540004\n.inst 0xbafffff3\n.inst 0xe8bd8070\n.word 0x0043dfc0\n");
}

// DECOMP_FUNC(0x00226138, 80)
extern "C" __attribute__((naked)) void ui_func_00226138() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe2524000\n.inst 0xe1a05000\n.inst 0xda00000d\n.inst 0xe2850004\n.inst 0xe8900005\n.inst 0xe0803004\n.inst 0xe1530002\n.inst 0x83a00001\n.inst 0x85c5000c\n.inst 0x8a000006\n.inst 0xe1a02004\n.inst 0xeb021af2\n.inst 0xe5950004\n.inst 0xe0800004\n.inst 0xe5850004\n.inst 0xe1a00004\n.inst 0xe8bd8070\n.inst 0xe3e00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x00228244, 92)
extern "C" __attribute__((naked)) void ui_func_00228244() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe2804b07\n.inst 0xe28440fc\n.inst 0xe5940000\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xe2800c01\n.inst 0xe1d009f2\n.inst 0xe3500000\n.inst 0xaa000001\n.inst 0xe3e00000\n.inst 0xe8bd8010\n.inst 0xe320f000\n.inst 0xeb01ae86\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xeb01ac92\n.inst 0xe3500000\n.inst 0x05940000\n.inst 0x13a00000\n.inst 0x02800c01\n.inst 0x01d009f2\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x00228ac4, 80)
extern "C" __attribute__((naked)) void script_vm_func_00228ac4() {
    asm volatile(".arm\n.inst 0xe92d4030\n.inst 0xe1a04001\n.inst 0xe1a05002\n.inst 0xeb015830\n.inst 0xe3a03000\n.inst 0xe080c183\n.inst 0xe59c15a8\n.inst 0xe3510000\n.inst 0xaa000002\n.inst 0xe59c15ac\n.inst 0xe3510000\n.inst 0x0a000003\n.inst 0xe2833001\n.inst 0xe3530085\n.inst 0xbafffff5\n.inst 0xe8bd8030\n.inst 0xe0800183\n.inst 0xe58045a8\n.inst 0xe58c55ac\n.inst 0xe8bd8030\n");
}

// DECOMP_FUNC(0x0022af30, 72)
extern "C" __attribute__((naked)) void engine_func_0022af30() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe59f4038\n.inst 0xe1a03000\n.inst 0xe1a02001\n.inst 0xe1a01003\n.inst 0xe5940004\n.inst 0xe5900018\n.inst 0xeb00e178\n.inst 0xe2000102\n.inst 0xe3500000\n.inst 0xb3a00000\n.inst 0xba000003\n.inst 0xe5940004\n.inst 0xe5900018\n.inst 0xeb00385b\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.word 0x00464fa8\n");
}

// DECOMP_FUNC(0x0022e244, 76)
extern "C" __attribute__((naked)) void unite_func_0022e244() {
    asm volatile(".arm\n.inst 0xe59f1040\n.inst 0xe92d4010\n.inst 0xe1d040f0\n.inst 0xe19110f0\n.inst 0xe3510000\n.inst 0xd3a00000\n.inst 0xda000006\n.inst 0xe3a00064\n.inst 0xe0000094\n.inst 0xeb025fbb\n.inst 0xe21000ff\n.inst 0x0a000002\n.inst 0xe3500064\n.inst 0x83a00064\n.inst 0xe8bd8010\n.inst 0xe3540000\n.inst 0xc3a00001\n.inst 0xe8bd8010\n.word 0x0000a006\n");
}

// DECOMP_FUNC(0x002339ac, 60)
extern "C" __attribute__((naked)) void shop_func_002339ac() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe1d003f0\n.inst 0xe3a04000\n.inst 0xe3500000\n.inst 0xda000005\n.inst 0xe320f000\n.inst 0xeb02158e\n.inst 0xe1d503f0\n.inst 0xe2844001\n.inst 0xe1500004\n.inst 0xcafffff9\n.inst 0xe3a00000\n.inst 0xe1c503b0\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002339e8, 60)
extern "C" __attribute__((naked)) void shop_func_002339e8() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe1d005fa\n.inst 0xe3a04000\n.inst 0xe3500000\n.inst 0xda000005\n.inst 0xe320f000\n.inst 0xeb02157f\n.inst 0xe1d505fa\n.inst 0xe2844001\n.inst 0xe1500004\n.inst 0xcafffff9\n.inst 0xe3a00000\n.inst 0xe1c505ba\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002347f4, 76)
extern "C" __attribute__((naked)) void camp_func_002347f4() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe59f0038\n.inst 0xe3a04000\n.inst 0xe5850000\n.inst 0xe1d505fa\n.inst 0xe3500000\n.inst 0xda000005\n.inst 0xe320f000\n.inst 0xeb0211fa\n.inst 0xe1d505fa\n.inst 0xe2844001\n.inst 0xe1500004\n.inst 0xcafffff9\n.inst 0xe3a00000\n.inst 0xe1c505ba\n.inst 0xe1a00005\n.inst 0xe8bd8070\n.word 0x004221e4\n");
}

// DECOMP_FUNC(0x00236454, 92)
extern "C" __attribute__((naked)) void func_00236454() {
    asm volatile(".arm\n.inst 0xe590103c\n.inst 0xe3a02004\n.inst 0xe1d22001\n.inst 0x0a000010\n.inst 0xedd00a03\n.inst 0xed9f0a0f\n.inst 0xeef40a40\n.inst 0xeef1fa10\n.inst 0x1a000009\n.inst 0xedd00a07\n.inst 0xe1a02000\n.inst 0xeef40a40\n.inst 0xeef1fa10\n.inst 0x0dd00a0b\n.inst 0x0ef40a40\n.inst 0x0ef1fa10\n.inst 0x03811c01\n.inst 0x0582103c\n.inst 0x0a000001\n.inst 0xe3c11c01\n.inst 0xe580103c\n.inst 0xe12fff1e\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x0023a11c, 64)
extern "C" __attribute__((naked)) void func_0023a11c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xeb049bf9\n.inst 0xe2001bff\n.inst 0xe1a01521\n.inst 0xe3510011\n.inst 0x1a000006\n.inst 0xe1a00b00\n.inst 0xe1a00b20\n.inst 0xe3500064\n.inst 0xba000002\n.inst 0xe35000b3\n.inst 0xd59f0008\n.inst 0xda000000\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.word 0xc961391a\n");
}

// DECOMP_FUNC(0x0023b5f8, 88)
extern "C" __attribute__((naked)) void battle_func_0023b5f8() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe3110008\n.inst 0xe1a04000\n.inst 0x0a000003\n.inst 0xe1a01002\n.inst 0xe3a00016\n.inst 0xeb000bcc\n.inst 0xea000004\n.inst 0xe3110040\n.inst 0x0a000004\n.inst 0xe1a01002\n.inst 0xe3a00016\n.inst 0xeb01ab85\n.inst 0xe5840008\n.inst 0xe8bd8010\n.inst 0xe3110001\n.inst 0x0afffffc\n.inst 0xe1a01002\n.inst 0xe3a00016\n.inst 0xeb01aaf2\n.inst 0xe5840008\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x0023ecd8, 76)
extern "C" __attribute__((naked)) void camp_func_0023ecd8() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1b04000\n.inst 0x0a00000d\n.inst 0xeb01a747\n.inst 0xe2801090\n.inst 0xe3a00000\n.inst 0xe1510004\n.inst 0x0a000009\n.inst 0xe5d1204a\n.inst 0xe5d4304a\n.inst 0xe1520003\n.inst 0x0a000005\n.inst 0xe2800001\n.inst 0xe2811b01\n.inst 0xe3500018\n.inst 0xe2811f81\n.inst 0xbafffff4\n.inst 0xe3e00000\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x0024c4bc, 68)
extern "C" __attribute__((naked)) void func_0024c4bc() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a06000\n.inst 0xe1a04001\n.inst 0xe1a05002\n.inst 0xebffc3dd\n.inst 0xe2042007\n.inst 0xe3550000\n.inst 0xe3a01001\n.inst 0xe0800186\n.inst 0xe1a01211\n.inst 0xe2800ecf\n.inst 0xe7f021a4\n.inst 0xe20110ff\n.inst 0x11811002\n.inst 0x01c21001\n.inst 0xe5c01000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x0024de30, 72)
extern "C" __attribute__((naked)) void script_vm_func_0024de30() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xeb01a22b\n.inst 0xe3540004\n.inst 0x0a000005\n.inst 0xe3540005\n.inst 0x1a000008\n.inst 0xe1d007f4\n.inst 0xe3700e32\n.inst 0xca000005\n.inst 0xea000002\n.inst 0xe1d007f4\n.inst 0xe3500e32\n.inst 0xba000001\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe3a00000\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x0024ec64, 92)
extern "C" __attribute__((naked)) void camp_func_0024ec64() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xeb016765\n.inst 0xe1a01000\n.inst 0xe3a00000\n.inst 0xe0812000\n.inst 0xe2822a09\n.inst 0xe1d22fd0\n.inst 0xe3520000\n.inst 0xba000007\n.inst 0xe0823382\n.inst 0xe0832402\n.inst 0xe0812102\n.inst 0xe1d22db6\n.inst 0xe1520004\n.inst 0x1a000001\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe2800001\n.inst 0xe3500018\n.inst 0xbaffffef\n.inst 0xe3a00000\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x0025382c, 80)
extern "C" __attribute__((naked)) void engine_func_0025382c() {
    asm volatile(".arm\n.inst 0xeef02a40\n.inst 0xeeb03a60\n.inst 0xeeb02a41\n.inst 0xe52de004\n.inst 0xeb00d14c\n.inst 0xeddf0a0c\n.inst 0xeef01a40\n.inst 0xeeb40ae0\n.inst 0xeef1fa10\n.inst 0x3eb10a40\n.inst 0xeeb40ac2\n.inst 0xeef1fa10\n.inst 0x9eb00a43\n.inst 0x9a000003\n.inst 0xeef41ae0\n.inst 0xeef1fa10\n.inst 0x3e320ac2\n.inst 0x2e320a82\n.inst 0xe49df004\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x0025452c, 64)
extern "C" __attribute__((naked)) void script_vm_func_0025452c() {
    asm volatile(".arm\n.inst 0xe1a02000\n.inst 0xe59f0030\n.inst 0xe5901004\n.inst 0xe3a00000\n.inst 0xe281108c\n.inst 0xe0822001\n.inst 0xe2822c91\n.inst 0xe1d220d8\n.inst 0xe3520000\n.inst 0xba000003\n.inst 0xe0820382\n.inst 0xe0800402\n.inst 0xe0810100\n.inst 0xe2800090\n.inst 0xe12fff1e\n.word 0x0043e2a8\n");
}

// DECOMP_FUNC(0x002547cc, 68)
extern "C" __attribute__((naked)) void func_002547cc() {
    asm volatile(".arm\n.inst 0xeddf1a0e\n.inst 0xed901a00\n.inst 0xeeb40ae1\n.inst 0xeef1fa10\n.inst 0xee311a00\n.inst 0xba000003\n.inst 0xeeb41ae0\n.inst 0xeef1fa10\n.inst 0xda000004\n.inst 0xea000002\n.inst 0xeeb41ae0\n.inst 0xeef1fa10\n.inst 0x2a000000\n.inst 0xeeb01a60\n.inst 0xed801a00\n.inst 0xe12fff1e\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x00256020, 88)
extern "C" __attribute__((naked)) void script_vm_func_00256020() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1500001\n.inst 0xe1a04000\n.inst 0xda000002\n.inst 0xe1a00001\n.inst 0xe1a01004\n.inst 0xe1a04000\n.inst 0xe0410004\n.inst 0xe2801001\n.inst 0xe59f0024\n.inst 0xe59f2024\n.inst 0xe5903000\n.inst 0xe0020293\n.inst 0xe2822a03\n.inst 0xe2822039\n.inst 0xe5802000\n.inst 0xe1a00822\n.inst 0xeb01c03c\n.inst 0xe0810004\n.inst 0xe8bd8010\n.word 0x00435e48\n.word 0x41c64e6d\n");
}

// DECOMP_FUNC(0x002564cc, 88)
extern "C" __attribute__((naked)) void battle_func_002564cc() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xeb01a97b\n.inst 0xe5901060\n.inst 0xe5900064\n.inst 0xe0814000\n.inst 0xe1a00005\n.inst 0xeb01a976\n.inst 0xe5900000\n.inst 0xe3500000\n.inst 0x0a000008\n.inst 0xe5902000\n.inst 0xe5901008\n.inst 0xe1520004\n.inst 0x1a000001\n.inst 0xe5910000\n.inst 0xe8bd8070\n.inst 0xe5900018\n.inst 0xe3500000\n.inst 0x1afffff6\n.inst 0xe3e00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002571c8, 84)
extern "C" __attribute__((naked)) void ui_func_002571c8() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe3a04000\n.inst 0xe1a07000\n.inst 0xe1a08001\n.inst 0xe590600c\n.inst 0xe3560000\n.inst 0xc3a09001\n.inst 0xda00000b\n.inst 0xe5970010\n.inst 0xe0841104\n.inst 0xe0805101\n.inst 0xe595000c\n.inst 0xe590100c\n.inst 0xe1a00008\n.inst 0xeb01be82\n.inst 0xe2855004\n.inst 0xe2844001\n.inst 0xe8850202\n.inst 0xe1540006\n.inst 0xbafffff3\n.inst 0xe8bd87f0\n");
}

// DECOMP_FUNC(0x0025a2bc, 92)
extern "C" __attribute__((naked)) void ui_func_0025a2bc() {
    asm volatile(".arm\n.inst 0xe59f0050\n.inst 0xe92d4010\n.inst 0xe5904000\n.inst 0xe5d40f2b\n.inst 0xe3500000\n.inst 0x15d4001c\n.inst 0x13500000\n.inst 0x0a000009\n.inst 0xe2840b03\n.inst 0xe28000e8\n.inst 0xe1d008d5\n.inst 0xe3500000\n.inst 0x1a000006\n.inst 0xe2840b03\n.inst 0xe2800f5d\n.inst 0xeb0195bc\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.word 0x0043e278\n");
}

// DECOMP_FUNC(0x0025b920, 72)
extern "C" __attribute__((naked)) void script_vm_func_0025b920() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xeb009d49\n.inst 0xe1a01000\n.inst 0xe2440001\n.inst 0xe3a02c01\n.inst 0xe15201c0\n.inst 0x33a00000\n.inst 0x3a000007\n.inst 0xe08111c0\n.inst 0xe2000007\n.inst 0xe3a02001\n.inst 0xe5d11f49\n.inst 0xe1a00012\n.inst 0xe20000ff\n.inst 0xe0100001\n.inst 0x13a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x0025ccb8, 64)
extern "C" __attribute__((naked)) void ui_func_0025ccb8() {
    asm volatile(".arm\n.inst 0xe3500000\n.inst 0xba00000b\n.inst 0xe0812281\n.inst 0xe0821381\n.inst 0xe59f2024\n.inst 0xe0821101\n.inst 0xe0810100\n.inst 0xe5900264\n.inst 0xed800a16\n.inst 0xedc00a1a\n.inst 0xed801a1e\n.inst 0xe5901088\n.inst 0xe3811b02\n.inst 0xe5801088\n.inst 0xe12fff1e\n.word 0x004d9d88\n");
}

// DECOMP_FUNC(0x00262c64, 84)
extern "C" __attribute__((naked)) void ui_func_00262c64() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a07000\n.inst 0xe59f4040\n.inst 0xe1a05007\n.inst 0xe2846a01\n.inst 0xe5960300\n.inst 0xe3500000\n.inst 0xda000009\n.inst 0xe5940000\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb017775\n.inst 0xe5847000\n.inst 0xe5960300\n.inst 0xe2855001\n.inst 0xe284404c\n.inst 0xe1500005\n.inst 0xcafffff5\n.inst 0xe5867300\n.inst 0xe8bd81f0\n.word 0x0047d200\n");
}

// DECOMP_FUNC(0x0026373c, 60)
extern "C" __attribute__((naked)) void func_0026373c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe1a05001\n.inst 0xeb01617c\n.inst 0xe2042007\n.inst 0xe3550000\n.inst 0xe3a01001\n.inst 0xe1a01211\n.inst 0xe2800008\n.inst 0xe7f021a4\n.inst 0xe20110ff\n.inst 0x11811002\n.inst 0x01c21001\n.inst 0xe5c01000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x00263e60, 76)
extern "C" __attribute__((naked)) void engine_func_00263e60() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe59f0038\n.inst 0xe3a04000\n.inst 0xe5850000\n.inst 0xe1d503f0\n.inst 0xe3500000\n.inst 0xda000005\n.inst 0xe320f000\n.inst 0xeb01545f\n.inst 0xe1d503f0\n.inst 0xe2844001\n.inst 0xe1500004\n.inst 0xcafffff9\n.inst 0xe3a00000\n.inst 0xe1c503b0\n.inst 0xe1a00005\n.inst 0xe8bd8070\n.word 0x004221d8\n");
}

// DECOMP_FUNC(0x00269fb0, 84)
extern "C" __attribute__((naked)) void camp_func_00269fb0() {
    asm volatile(".arm\n.inst 0xe59f0044\n.inst 0xe92d4010\n.inst 0xe5900000\n.inst 0xe3500000\n.inst 0x0a00000a\n.inst 0xe59f1034\n.inst 0xe7911000\n.inst 0xe3510000\n.inst 0x0a000005\n.inst 0xe5d00430\n.inst 0xe3500000\n.inst 0x0a000004\n.inst 0xeb00dbe8\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.word 0x0043dd68\n.word 0x000095d8\n");
}

// DECOMP_FUNC(0x0026b9a4, 72)
extern "C" __attribute__((naked)) void ui_func_0026b9a4() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xeb012b4e\n.inst 0xe1a01000\n.inst 0xe3a00000\n.inst 0xe0812080\n.inst 0xe1d233b4\n.inst 0xe1530004\n.inst 0x11d223b6\n.inst 0x11520004\n.inst 0x1a000001\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe2800002\n.inst 0xe3500008\n.inst 0xbafffff4\n.inst 0xe3a00000\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x0026fcb4, 96)
extern "C" __attribute__((naked)) void script_vm_func_0026fcb4() {
    asm volatile(".arm\n.inst 0xe92d0030\n.inst 0xe59f204c\n.inst 0xe59f504c\n.inst 0xe1a03000\n.inst 0xe3a00000\n.inst 0xe060c180\n.inst 0xe08c4200\n.inst 0xe792c104\n.inst 0xe37c0001\n.inst 0x0a000008\n.inst 0xe15c0003\n.inst 0x1a000003\n.inst 0xe082c104\n.inst 0xe59cc004\n.inst 0xe15c0001\n.inst 0x0a000003\n.inst 0xe2800001\n.inst 0xe1500005\n.inst 0xbafffff1\n.inst 0xe3e00000\n.inst 0xe8bd0030\n.inst 0xe12fff1e\n.word 0x00448e18\n.word 0x000003e7\n");
}

// DECOMP_FUNC(0x0027dd20, 88)
extern "C" __attribute__((naked)) void ui_func_0027dd20() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04001\n.inst 0xe1d116f2\n.inst 0xeb001398\n.inst 0xe1b02000\n.inst 0x11d416f2\n.inst 0x13a00000\n.inst 0x0a00000b\n.inst 0xe0823080\n.inst 0xe1d3c0f8\n.inst 0xe151000c\n.inst 0x0a000003\n.inst 0xe1d330fa\n.inst 0xe1510003\n.inst 0x1a000001\n.inst 0xe2800001\n.inst 0xe8bd8010\n.inst 0xe2800002\n.inst 0xe3500032\n.inst 0xbafffff3\n.inst 0xe3e00000\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x0027ee10, 92)
extern "C" __attribute__((naked)) void script_vm_func_0027ee10() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe59f504c\n.inst 0xe5954000\n.inst 0xe3540000\n.inst 0x0a00000c\n.inst 0xe5940000\n.inst 0xeb00cdc0\n.inst 0xe3500000\n.inst 0x1a00000a\n.inst 0xe5d40008\n.inst 0xe3500000\n.inst 0x0a000007\n.inst 0xe5950000\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xeb011543\n.inst 0xe3a00000\n.inst 0xe5850000\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x004475b8\n");
}

// DECOMP_FUNC(0x00282df8, 92)
extern "C" __attribute__((naked)) void ui_func_00282df8() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe59f504c\n.inst 0xe5954004\n.inst 0xe3540000\n.inst 0x0a00000c\n.inst 0xe5940000\n.inst 0xeb00bdc6\n.inst 0xe3500000\n.inst 0x1a00000a\n.inst 0xe5d40004\n.inst 0xe3500000\n.inst 0x0a000007\n.inst 0xe5950004\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xeb010549\n.inst 0xe3a00000\n.inst 0xe5850004\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x0044de28\n");
}

// DECOMP_FUNC(0x00287a68, 76)
extern "C" __attribute__((naked)) void script_vm_func_00287a68() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xeb00bd01\n.inst 0xe3500000\n.inst 0x0a00000b\n.inst 0xe3500001\n.inst 0x0a000008\n.inst 0xe3500002\n.inst 0x1a000006\n.inst 0xeb00bcf4\n.inst 0xe1d014b4\n.inst 0xe3110002\n.inst 0x1a000004\n.inst 0xe1d002ba\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002899c4, 84)
extern "C" __attribute__((naked)) void script_vm_func_002899c4() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a04000\n.inst 0xe1a05001\n.inst 0xe1a06002\n.inst 0xeb00914e\n.inst 0xe3560000\n.inst 0xe1a07000\n.inst 0x0a000002\n.inst 0xe1a01005\n.inst 0xe1a00004\n.inst 0xebfed149\n.inst 0xe2041007\n.inst 0xe3550000\n.inst 0xe3a00001\n.inst 0xe1a00110\n.inst 0xe1a011a4\n.inst 0xe7d72001\n.inst 0x11800002\n.inst 0x01c20000\n.inst 0xe7c70001\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x0028c13c, 88)
extern "C" __attribute__((naked)) void camp_func_0028c13c() {
    asm volatile(".arm\n.inst 0xe59f004c\n.inst 0xe92d4070\n.inst 0xe5905000\n.inst 0xe3550000\n.inst 0x13a04000\n.inst 0x0a00000d\n.inst 0xe0640184\n.inst 0xe0800100\n.inst 0xe0850100\n.inst 0xe5901068\n.inst 0xe3510000\n.inst 0x0a000002\n.inst 0xe2800020\n.inst 0xe3a01001\n.inst 0xeb00cbad\n.inst 0xe2844001\n.inst 0xe3540005\n.inst 0xbafffff3\n.inst 0xe3a00000\n.inst 0xe5c502f5\n.inst 0xe8bd8070\n.word 0x00434210\n");
}

// DECOMP_FUNC(0x0028ccb0, 84)
extern "C" __attribute__((naked)) void camp_func_0028ccb0() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe59f0040\n.inst 0xe5900004\n.inst 0xe2804090\n.inst 0xebff7805\n.inst 0xe2501000\n.inst 0xe3a00000\n.inst 0xda000006\n.inst 0xe0842080\n.inst 0xe1d227b8\n.inst 0xe3520000\n.inst 0x0a000003\n.inst 0xe2800001\n.inst 0xe1510000\n.inst 0xcafffff8\n.inst 0xe8bd8070\n.inst 0xe0840080\n.inst 0xe1c057b8\n.inst 0xe8bd8070\n.word 0x0043e2a8\n");
}

// DECOMP_FUNC(0x0028cd04, 88)
extern "C" __attribute__((naked)) void camp_func_0028cd04() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe59f0044\n.inst 0xe5900004\n.inst 0xe2804090\n.inst 0xebff77f0\n.inst 0xe2501000\n.inst 0xe3a00000\n.inst 0xda000006\n.inst 0xe0842080\n.inst 0xe1d227b8\n.inst 0xe1520005\n.inst 0x1a000003\n.inst 0xe0841080\n.inst 0xe3a00000\n.inst 0xe1c107b8\n.inst 0xe8bd8070\n.inst 0xe2800001\n.inst 0xe1510000\n.inst 0xcafffff4\n.inst 0xe8bd8070\n.word 0x0043e2a8\n");
}

// DECOMP_FUNC(0x00292bb8, 76)
extern "C" __attribute__((naked)) void camp_func_00292bb8() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe0850084\n.inst 0xe1d003b4\n.inst 0xe3500000\n.inst 0x0a000006\n.inst 0xebffc537\n.inst 0xe3500000\n.inst 0x15d00035\n.inst 0x13500000\n.inst 0x0a000001\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe3540008\n.inst 0xbafffff1\n.inst 0xe3a00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x00293ca8, 92)
extern "C" __attribute__((naked)) void ui_func_00293ca8() {
    asm volatile(".arm\n.inst 0xe5902010\n.inst 0xed9f0a13\n.inst 0xe3520000\n.inst 0x11d220be\n.inst 0x11520001\n.inst 0xda00000e\n.inst 0xe5902020\n.inst 0xe5900024\n.inst 0xe3a03002\n.inst 0xe083c101\n.inst 0xe0801101\n.inst 0xe19000bc\n.inst 0xe1d110b0\n.inst 0xe3a03004\n.inst 0xe0800001\n.inst 0xe2400001\n.inst 0xe0800080\n.inst 0xe0830180\n.inst 0xe7920000\n.inst 0xee000a10\n.inst 0xeeb80ac0\n.inst 0xe12fff1e\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x00294054, 88)
extern "C" __attribute__((naked)) void ui_func_00294054() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe5900008\n.inst 0xe1a06001\n.inst 0xe1a02001\n.inst 0xe3a01000\n.inst 0xe5900008\n.inst 0xebfead28\n.inst 0xe3a04000\n.inst 0xe0840104\n.inst 0xe0850200\n.inst 0xe5900018\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xe5900008\n.inst 0xe1a02006\n.inst 0xe3a01000\n.inst 0xebfead1e\n.inst 0xe2844001\n.inst 0xe3540003\n.inst 0xbafffff3\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x0029411c, 88)
extern "C" __attribute__((naked)) void ui_func_0029411c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe5900008\n.inst 0xe1a06001\n.inst 0xe1a02001\n.inst 0xe3a01000\n.inst 0xe5900008\n.inst 0xebffe1da\n.inst 0xe3a04000\n.inst 0xe0840104\n.inst 0xe0850200\n.inst 0xe5900018\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xe5900008\n.inst 0xe1a02006\n.inst 0xe3a01000\n.inst 0xebffe1d0\n.inst 0xe2844001\n.inst 0xe3540003\n.inst 0xbafffff3\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x00295eac, 88)
extern "C" __attribute__((naked)) void script_vm_func_00295eac() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xeb004ad3\n.inst 0xe1a04000\n.inst 0xe5900000\n.inst 0xe3550000\n.inst 0xe0801005\n.inst 0xe5841000\n.inst 0xda000002\n.inst 0xe1a01005\n.inst 0xe3a00000\n.inst 0xeb001887\n.inst 0xe5940000\n.inst 0xe59f1018\n.inst 0xe3500000\n.inst 0xd3a00000\n.inst 0xe1500001\n.inst 0xe5840000\n.inst 0xc1a00001\n.inst 0xe5840000\n.inst 0xe8bd8070\n.word 0x3b9ac9ff\n");
}

// DECOMP_FUNC(0x00297004, 88)
extern "C" __attribute__((naked)) void ui_func_00297004() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1500001\n.inst 0xe1a04000\n.inst 0xda000002\n.inst 0xe1a00001\n.inst 0xe1a01004\n.inst 0xe1a04000\n.inst 0xe0410004\n.inst 0xe2801001\n.inst 0xe59f0024\n.inst 0xe59f2024\n.inst 0xe5903000\n.inst 0xe0020293\n.inst 0xe2822a03\n.inst 0xe2822039\n.inst 0xe5802000\n.inst 0xe1a00822\n.inst 0xeb00bc43\n.inst 0xe0810004\n.inst 0xe8bd8010\n.word 0x004651c0\n.word 0x41c64e6d\n");
}

// DECOMP_FUNC(0x002976ac, 88)
extern "C" __attribute__((naked)) void camp_func_002976ac() {
    asm volatile(".arm\n.inst 0xe3500043\n.inst 0xe92d4010\n.inst 0x2a000008\n.inst 0xe59f1040\n.inst 0xe0814200\n.inst 0xe5940004\n.inst 0xe3500000\n.inst 0x13a00001\n.inst 0x1a000003\n.inst 0xe5d4000c\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe5940000\n.inst 0xe3a02000\n.inst 0xe2841008\n.inst 0xeb00aefe\n.inst 0xe5840004\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.word 0x0049382c\n");
}

// DECOMP_FUNC(0x0029bf90, 92)
extern "C" __attribute__((naked)) void camp_func_0029bf90() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xeb00329a\n.inst 0xe1a01000\n.inst 0xe3a00000\n.inst 0xe0812000\n.inst 0xe2822a09\n.inst 0xe1d22fd0\n.inst 0xe3520000\n.inst 0xba000007\n.inst 0xe0823382\n.inst 0xe0833402\n.inst 0xe0813103\n.inst 0xe1d33db6\n.inst 0xe1530004\n.inst 0x1a000001\n.inst 0xe1a00002\n.inst 0xe8bd8010\n.inst 0xe2800001\n.inst 0xe3500018\n.inst 0xbaffffef\n.inst 0xe3e00000\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002a14a0, 72)
extern "C" __attribute__((naked)) void engine_func_002a14a0() {
    asm volatile(".arm\n.inst 0xe52de004\n.inst 0xeb000033\n.inst 0xe2001bff\n.inst 0xe3510b4e\n.inst 0x0a000001\n.inst 0xe3a00000\n.inst 0xe49df004\n.inst 0xe1a00b00\n.inst 0xe1a00b20\n.inst 0xe24010c0\n.inst 0xe3510040\n.inst 0x22401d05\n.inst 0x23510040\n.inst 0x22400040\n.inst 0x23500020\n.inst 0x33a00001\n.inst 0x2afffff3\n.inst 0xe49df004\n");
}

// DECOMP_FUNC(0x002a497c, 84)
extern "C" __attribute__((naked)) void script_vm_func_002a497c() {
    asm volatile(".arm\n.inst 0xe3500043\n.inst 0xe92d4010\n.inst 0x2a000008\n.inst 0xe59f103c\n.inst 0xe0814200\n.inst 0xe5940004\n.inst 0xe3500000\n.inst 0x03a00001\n.inst 0x0a000003\n.inst 0xe5d4100c\n.inst 0xe3510000\n.inst 0x0a000001\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe320f000\n.inst 0xeb007e68\n.inst 0xe3a00000\n.inst 0xe5840004\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.word 0x0049382c\n");
}

// DECOMP_FUNC(0x002a8a1c, 60)
extern "C" __attribute__((naked)) void camp_func_002a8a1c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xebfffff8\n.inst 0xe1a02000\n.inst 0xe3a00000\n.inst 0xe1a01000\n.inst 0xe0823001\n.inst 0xe2833a09\n.inst 0xe1d33fd0\n.inst 0xe3530000\n.inst 0xba000003\n.inst 0xe2811001\n.inst 0xe3510018\n.inst 0xe2800001\n.inst 0xbafffff6\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002ac6d0, 92)
extern "C" __attribute__((naked)) void engine_func_002ac6d0() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe3a00000\n.inst 0xe5840000\n.inst 0xe5840004\n.inst 0xe59f003c\n.inst 0xe5912000\n.inst 0xe1520000\n.inst 0x05910008\n.inst 0x03500401\n.inst 0x1a000008\n.inst 0xe1a00001\n.inst 0xe5841000\n.inst 0xebfa8232\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xe2800008\n.inst 0xe5840004\n.inst 0xe1a00004\n.inst 0xe8bd8010\n.inst 0xe1a00004\n.inst 0xe8bd8010\n.word 0x44535743\n");
}

// DECOMP_FUNC(0x002acc58, 64)
extern "C" __attribute__((naked)) void func_002acc58() {
    asm volatile(".arm\n.inst 0xe92d4008\n.inst 0xe5900000\n.inst 0xe5901000\n.inst 0xe3510106\n.inst 0x0a000002\n.inst 0xe351010a\n.inst 0x13a00000\n.inst 0xe8bd8008\n.inst 0xe5b0101c\n.inst 0xe3510000\n.inst 0x10800001\n.inst 0x03a00000\n.inst 0xe58d0000\n.inst 0xe1a0000d\n.inst 0xebfffff0\n.inst 0xe8bd8008\n");
}

// DECOMP_FUNC(0x002ae394, 92)
extern "C" __attribute__((naked)) void script_vm_func_002ae394() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xeb0020d2\n.inst 0xe1a01000\n.inst 0xe3a00000\n.inst 0xe0812080\n.inst 0xe1d233b4\n.inst 0xe1530004\n.inst 0x1a000002\n.inst 0xe0800001\n.inst 0xe5d00044\n.inst 0xe8bd8010\n.inst 0xe1d223b6\n.inst 0xe1520004\n.inst 0x1a000002\n.inst 0xe0800001\n.inst 0xe5d00045\n.inst 0xe8bd8010\n.inst 0xe2800002\n.inst 0xe3500008\n.inst 0xbaffffef\n.inst 0xe3a00000\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002af894, 60)
extern "C" __attribute__((naked)) void engine_func_002af894() {
    asm volatile(".arm\n.inst 0xe59f1030\n.inst 0xe5911004\n.inst 0xe2812c06\n.inst 0xe1d234fe\n.inst 0xe1530000\n.inst 0x05d10008\n.inst 0x03500001\n.inst 0x1a000003\n.inst 0xe1d205f0\n.inst 0xe3500001\n.inst 0xb3a00001\n.inst 0xba000000\n.inst 0xe3a00000\n.inst 0xe12fff1e\n.word 0x0043dcb0\n");
}

// DECOMP_FUNC(0x002b0824, 88)
extern "C" __attribute__((naked)) void camp_func_002b0824() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xebffe079\n.inst 0xe3500000\n.inst 0xda00000d\n.inst 0xe320f000\n.inst 0xebffe070\n.inst 0xe0800004\n.inst 0xe2800a09\n.inst 0xe1d00fd0\n.inst 0xebffe063\n.inst 0xe1d014b6\n.inst 0xe1510005\n.inst 0x0a000005\n.inst 0xe2844001\n.inst 0xebffe06c\n.inst 0xe1500004\n.inst 0xe320f000\n.inst 0xcafffff1\n.inst 0xe3a00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002b2d48, 36)
extern "C" __attribute__((naked)) void engine_func_002b2d48() {
    asm volatile(".arm\n.inst 0xe5901034\n.inst 0xed9f0a05\n.inst 0xe3510000\n.inst 0xda000002\n.inst 0xe590004c\n.inst 0xe3500000\n.inst 0x1d900a0e\n.inst 0xe12fff1e\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x002b5070, 88)
extern "C" __attribute__((naked)) void ui_func_002b5070() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe2810003\n.inst 0xe3c04003\n.inst 0xe2830003\n.inst 0xe3c06003\n.inst 0xe0440001\n.inst 0xe0420000\n.inst 0xe1a01006\n.inst 0xeb0046dd\n.inst 0xe2501000\n.inst 0xe3a00000\n.inst 0x9a000006\n.inst 0xe5952000\n.inst 0xe2800001\n.inst 0xe1510000\n.inst 0xe5842000\n.inst 0xe5854000\n.inst 0xe0844006\n.inst 0x8afffff8\n.inst 0xe1a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002b6e78, 84)
extern "C" __attribute__((naked)) void script_vm_func_002b6e78() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xebfffff7\n.inst 0xe2801c06\n.inst 0xe1d120b8\n.inst 0xe3120001\n.inst 0x0a000005\n.inst 0xe1d004b6\n.inst 0xe3500000\n.inst 0x13a00002\n.inst 0x1a000000\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe1d100ba\n.inst 0xe3500000\n.inst 0x01d100bc\n.inst 0x03500000\n.inst 0x01d100be\n.inst 0x03500000\n.inst 0x13a00001\n.inst 0x0afffff5\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002b8a80, 92)
extern "C" __attribute__((naked)) void battle_func_002b8a80() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe59f504c\n.inst 0xe5954000\n.inst 0xe3540000\n.inst 0x0a00000c\n.inst 0xe5940000\n.inst 0xebffe6a4\n.inst 0xe3500000\n.inst 0x1a00000a\n.inst 0xe5d4000c\n.inst 0xe3500000\n.inst 0x0a000007\n.inst 0xe5950000\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xeb002e27\n.inst 0xe3a00000\n.inst 0xe5850000\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x00447e28\n");
}

// DECOMP_FUNC(0x002bc210, 92)
extern "C" __attribute__((naked)) void script_vm_func_002bc210() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a04000\n.inst 0xe1a07004\n.inst 0xe59f6044\n.inst 0xe3540004\n.inst 0x30640204\n.inst 0x23a05000\n.inst 0x30865180\n.inst 0xe5950048\n.inst 0xeb0015fb\n.inst 0xe3500000\n.inst 0x15950050\n.inst 0x13500004\n.inst 0x0a000003\n.inst 0xe5950068\n.inst 0xe3800004\n.inst 0xe5a50068\n.inst 0xe5857008\n.inst 0xe2844001\n.inst 0xe3540004\n.inst 0xbaffffee\n.inst 0xe8bd81f0\n.word 0x004c5634\n");
}

// DECOMP_FUNC(0x002bc26c, 88)
extern "C" __attribute__((naked)) void camp_func_002bc26c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a04000\n.inst 0xe59f6044\n.inst 0xe3540004\n.inst 0x30640204\n.inst 0x23a05000\n.inst 0x30865180\n.inst 0xe5950048\n.inst 0xeb0015e5\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000003\n.inst 0xe3550000\n.inst 0x13a00001\n.inst 0x1a000004\n.inst 0xea000002\n.inst 0xe2844001\n.inst 0xe3540004\n.inst 0xbaffffef\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.word 0x004c5634\n");
}

// DECOMP_FUNC(0x002c0c04, 88)
extern "C" __attribute__((naked)) void engine_func_002c0c04() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a06000\n.inst 0xe1a04001\n.inst 0xe1a05002\n.inst 0xebffec49\n.inst 0xe3560000\n.inst 0x0a000008\n.inst 0xe3560001\n.inst 0x13a00000\n.inst 0x1a000004\n.inst 0xe1a01084\n.inst 0xe2411002\n.inst 0xe0811005\n.inst 0xe0800101\n.inst 0xe2800f5b\n.inst 0xe8bd8070\n.inst 0xe2441001\n.inst 0xe0611181\n.inst 0xe0811005\n.inst 0xe0800101\n.inst 0xe280001c\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002c3968, 60)
extern "C" __attribute__((naked)) void engine_func_002c3968() {
    asm volatile(".arm\n.inst 0xe3500802\n.inst 0xe92d4010\n.inst 0x0a000005\n.inst 0xe3500803\n.inst 0x13a00000\n.inst 0x1a000001\n.inst 0xebffc0c6\n.inst 0xe59f0010\n.inst 0xe8bd8010\n.inst 0xe320f000\n.inst 0xebffc0c2\n.inst 0xe59f0004\n.inst 0xe8bd8010\n.word 0x1f5fffff\n.word 0x1f2fffff\n");
}

// DECOMP_FUNC(0x002c39a4, 80)
extern "C" __attribute__((naked)) void engine_func_002c39a4() {
    asm volatile(".arm\n.inst 0xe3500802\n.inst 0xe92d4010\n.inst 0x0a000007\n.inst 0xe3500803\n.inst 0x13a00000\n.inst 0x1a000003\n.inst 0xebffc0b7\n.inst 0xe3500000\n.inst 0x159f001c\n.inst 0x059f001c\n.inst 0xe8bd8010\n.inst 0xe320f000\n.inst 0xebffc0b1\n.inst 0xe3500000\n.inst 0x159f000c\n.inst 0x03a0041f\n.inst 0xe8bd8010\n.word 0x1f380000\n.word 0x1f300000\n.word 0x1f180000\n");
}

// DECOMP_FUNC(0x002c46e0, 48)
extern "C" __attribute__((naked)) void ui_func_002c46e0() {
    asm volatile(".arm\n.inst 0xe59f1024\n.inst 0xe5912000\n.inst 0xe3520000\n.inst 0x15911004\n.inst 0x11510000\n.inst 0x9a000003\n.inst 0xe0801080\n.inst 0xe0810180\n.inst 0xe0920100\n.inst 0x1d800a0a\n.inst 0xe12fff1e\n.word 0x00464a70\n");
}

// DECOMP_FUNC(0x002cb75c, 44)
extern "C" __attribute__((naked)) void func_002cb75c() {
    asm volatile(".arm\n.inst 0xe3500000\n.inst 0xb3a00000\n.inst 0xba000005\n.inst 0xe0812281\n.inst 0xe0821381\n.inst 0xe59f200c\n.inst 0xe0821101\n.inst 0xe0810100\n.inst 0xe5900264\n.inst 0xe12fff1e\n.word 0x004d9d88\n");
}

// DECOMP_FUNC(0x002cbee0, 88)
extern "C" __attribute__((naked)) void engine_func_002cbee0() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe24dde1f\n.inst 0xe3a02000\n.inst 0xe1a0100d\n.inst 0xebfe22f3\n.inst 0xe3500000\n.inst 0x0a000007\n.inst 0xebff8704\n.inst 0xe1a0000d\n.inst 0xebff7248\n.inst 0xe1a04000\n.inst 0xebffde00\n.inst 0xe28dde1f\n.inst 0xe1a00004\n.inst 0xe8bd8010\n.inst 0xe59f0010\n.inst 0xe1a04000\n.inst 0xebffddfa\n.inst 0xe28dde1f\n.inst 0xe1a00004\n.inst 0xe8bd8010\n.word 0xe0e046bc\n");
}

// DECOMP_FUNC(0x002d29ac, 72)
extern "C" __attribute__((naked)) void engine_func_002d29ac() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe1a05001\n.inst 0xebffc057\n.inst 0xe1a01fc4\n.inst 0xe3550000\n.inst 0xe0842da1\n.inst 0xe3a03001\n.inst 0xe1a012c2\n.inst 0xe3c2201f\n.inst 0xe0800101\n.inst 0xe0442002\n.inst 0xe5901d18\n.inst 0xe1a02213\n.inst 0x11811002\n.inst 0x01c11002\n.inst 0xe5801d18\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002d575c, 36)
extern "C" __attribute__((naked)) void func_002d575c() {
    asm volatile(".arm\n.inst 0xe5901034\n.inst 0xed9f0a05\n.inst 0xe3510000\n.inst 0xda000002\n.inst 0xe590004c\n.inst 0xe3500000\n.inst 0x1d900a10\n.inst 0xe12fff1e\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x002d6560, 76)
extern "C" __attribute__((naked)) void engine_func_002d6560() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a04001\n.inst 0xe3a06000\n.inst 0xe1a00004\n.inst 0xeb002bf8\n.inst 0xe3700001\n.inst 0xe1a05000\n.inst 0x0a000006\n.inst 0xebffa3a5\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000002\n.inst 0xe1a00005\n.inst 0xebffa94b\n.inst 0xe5c0608c\n.inst 0xe2844001\n.inst 0xe3540004\n.inst 0xbafffff0\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002d9150, 80)
extern "C" __attribute__((naked)) void func_002d9150() {
    asm volatile(".arm\n.inst 0xe3500048\n.inst 0xaa00000f\n.inst 0xe3500000\n.inst 0xba00000d\n.inst 0xe59f1034\n.inst 0xe3500040\n.inst 0xe5912004\n.inst 0xe2821088\n.inst 0xe0800001\n.inst 0xa2800b92\n.inst 0xa2800fd7\n.inst 0xb2800a1e\n.inst 0xb2800ec1\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xe5d01000\n.inst 0xe3811004\n.inst 0xe5c01000\n.inst 0xe12fff1e\n.word 0x0043e2a8\n");
}

// DECOMP_FUNC(0x002dacfc, 64)
extern "C" __attribute__((naked)) void ui_func_002dacfc() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xebff9770\n.inst 0xe3a04000\n.inst 0xe1a01004\n.inst 0xe3a00037\n.inst 0xebff4f85\n.inst 0xe2844001\n.inst 0xe3540005\n.inst 0xbafffff9\n.inst 0xe3a00037\n.inst 0xebff4f54\n.inst 0xe59f1008\n.inst 0xe3a00000\n.inst 0xe5810000\n.inst 0xe8bd8010\n.word 0x0044dc50\n");
}

// DECOMP_FUNC(0x002dca04, 60)
extern "C" __attribute__((naked)) void func_002dca04() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04001\n.inst 0xe1d000b2\n.inst 0xebfdeb4b\n.inst 0xe1a05000\n.inst 0xe1d400b2\n.inst 0xebfdeb48\n.inst 0xe1d003b2\n.inst 0xe1d513b2\n.inst 0xe0400001\n.inst 0xe8bd8070\n.inst 0xe1d000b0\n.inst 0xe1d110b0\n.inst 0xe0400001\n.inst 0xe12fff1e\n");
}

// DECOMP_FUNC(0x002df7b0, 72)
extern "C" __attribute__((naked)) void engine_func_002df7b0() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe1a05001\n.inst 0xebff8cd6\n.inst 0xe1a01fc4\n.inst 0xe3550000\n.inst 0xe0842da1\n.inst 0xe3a03001\n.inst 0xe1a012c2\n.inst 0xe3c2201f\n.inst 0xe0800101\n.inst 0xe0442002\n.inst 0xe5901744\n.inst 0xe1a02213\n.inst 0x11811002\n.inst 0x01c11002\n.inst 0xe5801744\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002e0020, 76)
extern "C" __attribute__((naked)) void script_vm_func_002e0020() {
    asm volatile(".arm\n.inst 0xe59f1040\n.inst 0xe3a00000\n.inst 0xe1a03000\n.inst 0xe080c080\n.inst 0xe5912000\n.inst 0xe2800002\n.inst 0xe3500020\n.inst 0xe082220c\n.inst 0xe2822b0a\n.inst 0xe2822044\n.inst 0xe5c23000\n.inst 0xe5912000\n.inst 0xe082220c\n.inst 0xe2822b0a\n.inst 0xe2822074\n.inst 0xe5c23000\n.inst 0xbafffff1\n.inst 0xe12fff1e\n.word 0x00447e40\n");
}

// DECOMP_FUNC(0x002e1180, 60)
extern "C" __attribute__((naked)) void script_vm_func_002e1180() {
    asm volatile(".arm\n.inst 0xe5902058\n.inst 0xe3520000\n.inst 0xda000008\n.inst 0xe5900060\n.inst 0xe3500000\n.inst 0x0a000005\n.inst 0xe3510000\n.inst 0x059f1010\n.inst 0x159f1010\n.inst 0xe3a02001\n.inst 0xe5c02058\n.inst 0xe580104c\n.inst 0xe12fff1e\n.word 0x0015555c\n.word 0x00151404\n");
}

// DECOMP_FUNC(0x002e13e4, 88)
extern "C" __attribute__((naked)) void engine_func_002e13e4() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe24dde1f\n.inst 0xe3a02002\n.inst 0xe1a0100d\n.inst 0xebfdcdb2\n.inst 0xe3500000\n.inst 0x0a000007\n.inst 0xebff31c3\n.inst 0xe1a0000d\n.inst 0xebff1d07\n.inst 0xe1a04000\n.inst 0xebff88bf\n.inst 0xe28dde1f\n.inst 0xe1a00004\n.inst 0xe8bd8010\n.inst 0xe59f0010\n.inst 0xe1a04000\n.inst 0xebff88b9\n.inst 0xe28dde1f\n.inst 0xe1a00004\n.inst 0xe8bd8010\n.word 0xe0e046bc\n");
}

// DECOMP_FUNC(0x002e708c, 52)
extern "C" __attribute__((naked)) void engine_func_002e708c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe1a05001\n.inst 0xe2800021\n.inst 0xebff61f2\n.inst 0xe1a00005\n.inst 0xebff7079\n.inst 0xe5840010\n.inst 0xe8bd8070\n.inst 0xe59f0004\n.inst 0xec800a02\n.inst 0xe12fff1e\n.word 0x004724cc\n");
}

// DECOMP_FUNC(0x002e8510, 72)
extern "C" __attribute__((naked)) void engine_func_002e8510() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe1a05001\n.inst 0xebff697e\n.inst 0xe1a01fc4\n.inst 0xe3550000\n.inst 0xe0842da1\n.inst 0xe3a03001\n.inst 0xe1a012c2\n.inst 0xe3c2201f\n.inst 0xe0800101\n.inst 0xe0442002\n.inst 0xe5901750\n.inst 0xe1a02213\n.inst 0x11811002\n.inst 0x01c11002\n.inst 0xe5801750\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002eeeec, 88)
extern "C" __attribute__((naked)) void engine_func_002eeeec() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a05000\n.inst 0xe59f4044\n.inst 0xe5940248\n.inst 0xe3500000\n.inst 0x0a000005\n.inst 0xe3500002\n.inst 0x05845248\n.inst 0x03a00001\n.inst 0x13a00000\n.inst 0x05c4524c\n.inst 0xe8bd8070\n.inst 0xe3a00000\n.inst 0xebfea00e\n.inst 0xe3500001\n.inst 0xe3a00001\n.inst 0x05c4024c\n.inst 0x15c4524c\n.inst 0xe5840248\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.word 0x0049f91c\n");
}

// DECOMP_FUNC(0x002f1160, 64)
extern "C" __attribute__((naked)) void battle_func_002f1160() {
    asm volatile(".arm\n.inst 0xe59f0034\n.inst 0xe92d4010\n.inst 0xe5900000\n.inst 0xe2800a03\n.inst 0xe5d00040\n.inst 0xe350000d\n.inst 0x0a000003\n.inst 0xe3a00000\n.inst 0xebfe7373\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe3a00001\n.inst 0xebfe736f\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.word 0x00435d18\n");
}

// DECOMP_FUNC(0x002f12a8, 68)
extern "C" __attribute__((naked)) void ui_func_002f12a8() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xebfe8a79\n.inst 0xe1a04000\n.inst 0xe3a01001\n.inst 0xebfe35a9\n.inst 0xe3500000\n.inst 0xb3a00000\n.inst 0xba000005\n.inst 0xe2844d7f\n.inst 0xe0802200\n.inst 0xe5941000\n.inst 0xe0820300\n.inst 0xe0810180\n.inst 0xe1d00cbe\n.inst 0xebfe731b\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002f3604, 72)
extern "C" __attribute__((naked)) void script_vm_func_002f3604() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe1a05001\n.inst 0xebff3d41\n.inst 0xe1a01fc4\n.inst 0xe3550000\n.inst 0xe0842da1\n.inst 0xe3a03001\n.inst 0xe1a012c2\n.inst 0xe3c2201f\n.inst 0xe0800101\n.inst 0xe0442002\n.inst 0xe5901c98\n.inst 0xe1a02213\n.inst 0x11811002\n.inst 0x01c11002\n.inst 0xe5801c98\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002f5070, 36)
extern "C" __attribute__((naked)) void engine_func_002f5070() {
    asm volatile(".arm\n.inst 0xe5901034\n.inst 0xed9f0a05\n.inst 0xe3510000\n.inst 0xda000002\n.inst 0xe590004c\n.inst 0xe3500000\n.inst 0x1d900a12\n.inst 0xe12fff1e\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x002f5b2c, 44)
extern "C" __attribute__((naked)) void func_002f5b2c() {
    asm volatile(".arm\n.inst 0xe59f1020\n.inst 0xe5911004\n.inst 0xe3510000\n.inst 0x0a000003\n.inst 0xe3500006\n.inst 0x30810100\n.inst 0x35d00494\n.inst 0x3a000000\n.inst 0xe3a00000\n.inst 0xe12fff1e\n.word 0x0043da28\n");
}

// DECOMP_FUNC(0x002f5e20, 72)
extern "C" __attribute__((naked)) void battle_func_002f5e20() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a05000\n.inst 0xe59f4034\n.inst 0xe2846063\n.inst 0xe1a00004\n.inst 0xebfe638f\n.inst 0xe3500000\n.inst 0x13a05001\n.inst 0xe2844001\n.inst 0xe1540006\n.inst 0x9afffff8\n.inst 0xe3550000\n.inst 0x13a00001\n.inst 0x03a00000\n.inst 0xebfe603d\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x0000079f\n");
}

// DECOMP_FUNC(0x002f5e68, 56)
extern "C" __attribute__((naked)) void camp_func_002f5e68() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe1a05001\n.inst 0xebfeac4c\n.inst 0xe2041007\n.inst 0xe3550000\n.inst 0xe3a02001\n.inst 0xe1a01112\n.inst 0xe08001a4\n.inst 0xe5d02044\n.inst 0x11811002\n.inst 0x01c21001\n.inst 0xe5c01044\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002f707c, 68)
extern "C" __attribute__((naked)) void battle_func_002f707c() {
    asm volatile(".arm\n.inst 0xe59f0038\n.inst 0xe92d4010\n.inst 0xe5900000\n.inst 0xebfe1ec2\n.inst 0xe5900020\n.inst 0xebfd4036\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xe3a00001\n.inst 0xebfe5bab\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe3a00000\n.inst 0xebfe5ba7\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.word 0x0043427c\n");
}

// DECOMP_FUNC(0x002fb090, 72)
extern "C" __attribute__((naked)) void script_vm_func_002fb090() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe1a05001\n.inst 0xebff1e9e\n.inst 0xe1a01fc4\n.inst 0xe3550000\n.inst 0xe0842da1\n.inst 0xe3a03001\n.inst 0xe1a012c2\n.inst 0xe3c2201f\n.inst 0xe0800101\n.inst 0xe0442002\n.inst 0xe5901e58\n.inst 0xe1a02213\n.inst 0x11811002\n.inst 0x01c11002\n.inst 0xe5801e58\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002fdebc, 60)
extern "C" __attribute__((naked)) void func_002fdebc() {
    asm volatile(".arm\n.inst 0xe59f102c\n.inst 0xe5911000\n.inst 0xe0411000\n.inst 0xe2411001\n.inst 0xe3510000\n.inst 0xb3a00000\n.inst 0xba000004\n.inst 0xe0801180\n.inst 0xe0810280\n.inst 0xe59f100c\n.inst 0xe0810180\n.inst 0xe5900024\n.inst 0xe12fff1e\n.word 0x00433278\n.word 0x00478000\n");
}

// DECOMP_FUNC(0x002ff28c, 84)
extern "C" __attribute__((naked)) void battle_func_002ff28c() {
    asm volatile(".arm\n.inst 0xe3a00000\n.inst 0xe92d4010\n.inst 0xebfe5f31\n.inst 0xe1a04000\n.inst 0xebfe527d\n.inst 0xebfd2a19\n.inst 0xe3500000\n.inst 0x0a000008\n.inst 0xe2800c01\n.inst 0xe3a01001\n.inst 0xe1d00cb6\n.inst 0xe1100411\n.inst 0x0a000003\n.inst 0xe3a00001\n.inst 0xebfe3b22\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe3a00000\n.inst 0xebfe3b1e\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}
