#include "types.h"

// Batch 41 C: Capstone-validated ARM encodings preserved as exact raw words; semantics are not reconstructed.

// DECOMP_FUNC(0x0025a004, 160)
// 34 ARM instructions through unconditional bx; 24 trailing data bytes.
extern "C" __attribute__((naked)) void script_vm_func_0025a004() {
    asm volatile(
        ".arm\n"
        ".word 0xe3500000, 0x13500001, 0x1a00001d, 0xe59f3074\n"
        ".word 0xe0830100, 0xe2800a01, 0xe5900210, 0xe3500000\n"
        ".word 0x0a000017, 0xe351007f, 0xe5c0100d, 0x83a0107f\n"
        ".word 0x85c0100d, 0x8a000002, 0xe3510000, 0x0d9f0a12\n"
        ".word 0x0a00000a, 0xe20110ff, 0xee001a90, 0xeddf1a0f\n"
        ".word 0xed9f1a0f, 0xed9f0a0f, 0xeef80a60, 0xee700ae1\n"
        ".word 0xee000a81, 0xee101a10, 0xe3510101, 0xcd9f0a0a\n"
        ".word 0xe5900000, 0xe1a01002, 0xe3500000, 0x0a000000\n"
        ".word 0xea018b42, 0xe12fff1e, 0x004e1f68, 0x00000000\n"
        ".word 0x42800000, 0x3c810204, 0x3f800000, 0x40000000\n"
    );
}

// DECOMP_FUNC(0x0026f17c, 224)
// 49 ARM instructions through unconditional pop; 28 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_0026f17c() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d40f0, 0xe24dd04c, 0xe1a04000, 0xe3a07000\n"
        ".word 0xe281000e, 0xe1a05001, 0xe58d0004, 0xe58d7000\n"
        ".word 0xe5940000, 0xe1a03007, 0xe3e02000, 0xe3a01002\n"
        ".word 0xeb009f0b, 0xe1d504b8, 0xe28d6008, 0xe3500000\n"
        ".word 0x0a000003, 0xeb013825, 0xe28d1008, 0xeb0137f8\n"
        ".word 0xea000002, 0xe1a00006, 0xe28f1064, 0xebff7fa0\n"
        ".word 0xe58d6004, 0xe58d7000, 0xe5940004, 0xe3a03000\n"
        ".word 0xe3e02000, 0xe3a01002, 0xeb009ef9, 0xe5d50020\n"
        ".word 0xe3100002, 0x0a00000a, 0xe3a02013, 0xe28f1038\n"
        ".word 0xe28d0008, 0xeb013750, 0xe58d6004, 0xe58d7000\n"
        ".word 0xe5940008, 0xe3a03000, 0xe3e02000, 0xe3a01002\n"
        ".word 0xeb009eeb, 0xe3a00001, 0xe5c4000c, 0xe28dd04c\n"
        ".word 0xe8bd80f0, 0x7c817c81, 0x00007c81, 0x85826382\n"
        ".word 0x85829682, 0x8f828c82, 0x85829082, 0x00009282\n"
    );
}

// DECOMP_FUNC(0x002819f8, 228)
// 53 ARM instructions through unconditional bx; 16 trailing data bytes.
extern "C" __attribute__((naked)) void script_vm_func_002819f8() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d00f0, 0xe3a04000, 0xe59f60c4, 0xe59f50c8\n"
        ".word 0xed9f0a30, 0xe1a0c004, 0xe5864000, 0xe06c020c\n"
        ".word 0xe080028c, 0xe3a01000, 0xe3a02008, 0xe0850180\n"
        ".word 0xe0813081, 0xe2522001, 0xe0803103, 0xe2811001\n"
        ".word 0xed830a00, 0xed830a01, 0xed830a02, 0x1afffff7\n"
        ".word 0xed800a1b, 0xed800a1c, 0xe3a01000, 0xe3a02006\n"
        ".word 0xed800a1d, 0xe0813081, 0xe0807101, 0xe0803103\n"
        ".word 0xe2522001, 0xed830a1f, 0xed830a20, 0xed830a21\n"
        ".word 0xe2811001, 0xed870a31, 0x1afffff5, 0xe2801c01\n"
        ".word 0xe28cc001, 0xe1c147b4, 0xe1c147b6, 0xe1c145bc\n"
        ".word 0xe1c146b6, 0xe1c146b8, 0xe1c146ba, 0xe5c0416c\n"
        ".word 0xe35c00a0, 0xe5c0416d, 0xbaffffd7, 0xe59f101c\n"
        ".word 0xe3e00000, 0xe5864004, 0xe5810038, 0xe8bd00f0\n"
        ".word 0xe12fff1e, 0x00447a28, 0x00000000, 0x004a1264\n"
        ".word 0x0049f91c\n"
    );
}

// DECOMP_FUNC(0x002b67f8, 228)
// 56 ARM instructions through unconditional pop; 4 trailing data bytes.
extern "C" __attribute__((naked)) void func_002b67f8() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4070, 0xe3a06000, 0xe59f50d0, 0xe5950000\n"
        ".word 0xe2804a01, 0xe2844fc3, 0xe5940000, 0xe0841100\n"
        ".word 0xe2400001, 0xe5911008, 0xe5840000, 0xe0840100\n"
        ".word 0xe5d42018, 0xe5900008, 0xe3520000, 0x01510000\n"
        ".word 0x0a000002, 0xe594101c, 0xe12fff31, 0xe5c46018\n"
        ".word 0xe5950000, 0xe2804a01, 0xe2844fd3, 0xe5940000\n"
        ".word 0xe0841100, 0xe2400001, 0xe5911008, 0xe5840000\n"
        ".word 0xe0840100, 0xe5d42018, 0xe5900008, 0xe3520000\n"
        ".word 0x01510000, 0x0a000002, 0xe594101c, 0xe12fff31\n"
        ".word 0xe5c46018, 0xe5950000, 0xe2804a01, 0xe2844fcb\n"
        ".word 0xe5940000, 0xe0841100, 0xe2400001, 0xe5911008\n"
        ".word 0xe5840000, 0xe0840100, 0xe5d42018, 0xe5900008\n"
        ".word 0xe3520000, 0x01510000, 0x0a000002, 0xe594101c\n"
        ".word 0xe12fff31, 0xe5c46018, 0xe3a00001, 0xe8bd8070\n"
        ".word 0x0044ea00\n"
    );
}

// DECOMP_FUNC(0x0028674c, 232)
// 57 ARM instructions through unconditional pop; 4 trailing data bytes.
extern "C" __attribute__((naked)) void func_0028674c() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d41f0, 0xe1a06000, 0xe3a05000, 0xe59f70d0\n"
        ".word 0xe20500ff, 0xe3560000, 0xe7974200, 0x0a000006\n"
        ".word 0xe3560001, 0x0a000011, 0xe3560002, 0x0a000028\n"
        ".word 0xe3560003, 0x0a00001a, 0xea000025, 0xe3540000\n"
        ".word 0x0a000023, 0xe5d40002, 0xe3500000, 0x1a000003\n"
        ".word 0xe594100c, 0xe3510000, 0x12840034, 0x112fff31\n"
        ".word 0xe5944020, 0xe3540000, 0x1afffff5, 0xea000018\n"
        ".word 0xe3540000, 0x0a000016, 0xe5d40002, 0xe3500000\n"
        ".word 0x1a000003, 0xe5941010, 0xe3510000, 0x12840034\n"
        ".word 0x112fff31, 0xe5944020, 0xe3540000, 0x1afffff5\n"
        ".word 0xea00000b, 0xe3540000, 0x0a000009, 0xe5d40002\n"
        ".word 0xe3500000, 0x1a000003, 0xe5941014, 0xe3510000\n"
        ".word 0x12840034, 0x112fff31, 0xe5944020, 0xe3540000\n"
        ".word 0x1afffff5, 0xe2855001, 0xe3550005, 0xbaffffcb\n"
        ".word 0xe8bd81f0, 0x004c5830\n"
    );
}

// DECOMP_FUNC(0x0029423c, 248)
// 61 ARM instructions through unconditional pop; 4 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_0029423c() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4070, 0xe1a04000, 0xe5900010, 0xe3500000\n"
        ".word 0x0a000036, 0xe59f50d8, 0xe3110008, 0xe5950000\n"
        ".word 0x0a00000e, 0xe2841008, 0xe3a03001, 0xe8910006\n"
        ".word 0xeb006a6b, 0xe3500000, 0x0a000005, 0xe2844008\n"
        ".word 0xe5950000, 0xe8940006, 0xe3a03802, 0xe8bd4070\n"
        ".word 0xea0047e5, 0xe1c400d8, 0xe8bd4070, 0xeafea8aa\n"
        ".word 0xe3110040, 0x0a00000f, 0xe2841008, 0xe3a03001\n"
        ".word 0xe8910006, 0xeb006a5a, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000005, 0xe2844008, 0xe5950000, 0xe8940006\n"
        ".word 0xe3a03803, 0xe8bd4070, 0xea0047d3, 0xe1c400d8\n"
        ".word 0xe8bd4070, 0xea004857, 0xe3110001, 0x0a00000f\n"
        ".word 0xe2841008, 0xe3a03001, 0xe8910006, 0xeb006a48\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000005, 0xe2844008\n"
        ".word 0xe5950000, 0xe8940006, 0xe3a03801, 0xe8bd4070\n"
        ".word 0xea0047c1, 0xe1c400d8, 0xe8bd4070, 0xea0047b9\n"
        ".word 0xe8bd8070, 0x00433158\n"
    );
}

// DECOMP_FUNC(0x00286604, 252)
// 61 ARM instructions through unconditional bx; 8 trailing data bytes.
extern "C" __attribute__((naked)) void func_00286604() {
    asm volatile(
        ".arm\n"
        ".word 0xec910a03, 0xe2811010, 0xecd11a03, 0xe2811010\n"
        ".word 0xec913a03, 0xee205a02, 0xee605aa2, 0xee216a21\n"
        ".word 0xee636a02, 0xee217aa0, 0xee607a23, 0xee255a04\n"
        ".word 0xee655a83, 0xee266a23, 0xee065ac1, 0xee475a44\n"
        ".word 0xee076ae2, 0xee355a25, 0xeddf7a29, 0xee355a06\n"
        ".word 0xee152a10, 0xe3520102, 0x13520000, 0x03a00000\n"
        ".word 0x012fff1e, 0xed2d8b0a, 0xeec77a85, 0xee228a04\n"
        ".word 0xee618a84, 0xee219aa3, 0xee609a84, 0xee20aa04\n"
        ".word 0xee60aa23, 0xee20baa2, 0xee60ba22, 0xee20ca02\n"
        ".word 0xee038ae2, 0xee438a62, 0xee039a42, 0xee439ac1\n"
        ".word 0xee03aa41, 0xee43aa60, 0xee02ba41, 0xee41bac1\n"
        ".word 0xee01cae0, 0xee280a27, 0xee680ae7, 0xee291a27\n"
        ".word 0xee292ae7, 0xee6a2a27, 0xee2a3ae7, 0xee2b4a27\n"
        ".word 0xee6b4ae7, 0xee2c5a27, 0xeddf1a06, 0xeddf3a05\n"
        ".word 0xeddf5a04, 0xecbd8b0a, 0xec800a0c, 0xe3a00001\n"
        ".word 0xe12fff1e, 0x3f800000, 0x00000000\n"
    );
}

// DECOMP_FUNC(0x002a4cb4, 252)
// 60 ARM instructions through unconditional pop; 12 trailing data bytes.
extern "C" __attribute__((naked)) void func_002a4cb4() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d47f0, 0xe5902000, 0xe3520000, 0x059f00dc\n"
        ".word 0x0a000035, 0xe5d23001, 0xe353000f, 0x259f00d0\n"
        ".word 0x2a000031, 0xe1923f9f, 0xe1a02803, 0xe59fe0c4\n"
        ".word 0xe203c0ff, 0xe1a02c22, 0xe08cc002, 0xe3a08020\n"
        ".word 0xe08e4c9e, 0xe5919018, 0xe1a0e1ae, 0xe04ee20e\n"
        ".word 0xe08cc00e, 0xe590e000, 0xe088c28c, 0xe08cc00e\n"
        ".word 0xe89141f0, 0xe591101c, 0xe58c101c, 0xe58c9018\n"
        ".word 0xe88c41f0, 0xe3a01000, 0xee071f9a, 0xe2821001\n"
        ".word 0xe3c32cff, 0xe1a01401, 0xe2011cff, 0xe1811002\n"
        ".word 0xe5903000, 0xe1832f91, 0xe3520000, 0x0a000009\n"
        ".word 0xe5901000, 0xe1911f9f, 0xe1a03801, 0xe3c12cff\n"
        ".word 0xe1a01c23, 0xe2811001, 0xe1a01401, 0xe2011cff\n"
        ".word 0xe1811002, 0xeafffff1, 0xe1a00801, 0xe1a00c20\n"
        ".word 0xe3500001, 0x1a000003, 0xeb0021d7, 0xe320f000\n"
        ".word 0xe320f000, 0xebfabade, 0xe3a00000, 0xe8bd87f0\n"
        ".word 0xd8a02bf8, 0xd8a02a02, 0x88888889\n"
    );
}

// DECOMP_FUNC(0x0020fe98, 264)
// 64 ARM instructions through unconditional pop; 8 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_0020fe98() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4070, 0xe1a04000, 0xe1a05001, 0xed2d8b04\n"
        ".word 0xeeb08b40, 0xe5900034, 0xe3500000, 0xc1500005\n"
        ".word 0xda000034, 0xe5940000, 0xe3100001, 0x15946050\n"
        ".word 0x13560000, 0x0a00000a, 0xe5960000, 0xe5901000\n"
        ".word 0xe1a00006, 0xe12fff31, 0xe5960004, 0xe5901000\n"
        ".word 0xe591200c, 0xe1a01006, 0xe12fff32, 0xe3a00000\n"
        ".word 0xe5840050, 0xe5940000, 0xed9f9a24, 0xe3800001\n"
        ".word 0xe5840000, 0xe5845038, 0xed849a10, 0xedc48a11\n"
        ".word 0xe594203c, 0xe1c402dc, 0xe7911105, 0xebfcfc15\n"
        ".word 0xe1a01000, 0xe5840050, 0xe5940048, 0xed9f0a18\n"
        ".word 0xeeb48a49, 0xe3a05001, 0xe5902014, 0xeef1fa10\n"
        ".word 0xe5821004, 0xe5901024, 0xed810a00, 0xe5901034\n"
        ".word 0xed810a00, 0xe5c05041, 0x0a00000a, 0xe5944050\n"
        ".word 0xeeb01a48, 0xe2841044, 0xe5940050, 0xec910a02\n"
        ".word 0xe594104c, 0xe12fff31, 0xe5940038, 0xe584003c\n"
        ".word 0xed840a0e, 0xe5c45058, 0xecbd8b04, 0xe8bd8070\n"
        ".word 0x00000000, 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x002a4828, 332)
// 82 ARM instructions through unconditional pop; 4 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_002a4828() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d40f0, 0xe1b06002, 0xe1a07000, 0xe1a04001\n"
        ".word 0xed2d8b04, 0xe24ddf5f, 0xe1a05003, 0xeddd8a68\n"
        ".word 0xed9d8a69, 0xed9d9a6a, 0x0a000023, 0xe1a00001\n"
        ".word 0xeb007a8c, 0xe1a00006, 0xeb007a8a, 0xe28d00b8\n"
        ".word 0xebfffa93, 0xe1a01004, 0xe3a02040, 0xe28d40b8\n"
        ".word 0xe28d00e8, 0xeb0058b6, 0xe3a02040, 0xe1a01006\n"
        ".word 0xe2840070, 0xeb0058b2, 0xedcd8a38, 0xed8d8a39\n"
        ".word 0xed8d9a5b, 0xe59d00bc, 0xe28d10b8, 0xe3800002\n"
        ".word 0xe58d00bc, 0xe1a00007, 0xebfffa3c, 0xe1a04000\n"
        ".word 0xe1a00007, 0xebfff9f9, 0xe5d40008, 0xe3500003\n"
        ".word 0x0a000022, 0xe59f009c, 0xe3a01000, 0xeb005aed\n"
        ".word 0xe320f000, 0xe320f000, 0xeafffff6, 0xe1a06001\n"
        ".word 0xe3a04000, 0xe1a00001, 0xeb007a66, 0xe1a0000d\n"
        ".word 0xe320f000, 0xebfffa6e, 0xe3a02040, 0xe1a01006\n"
        ".word 0xe28d0030, 0xeb005892, 0xedcd8a0a, 0xed8d8a0b\n"
        ".word 0xe1a0100d, 0xe1a00007, 0xe58d40b4, 0xebfffa1f\n"
        ".word 0xe1a04000, 0xe1a00007, 0xebfff9dc, 0xe5d40008\n"
        ".word 0xe3500003, 0x0a000005, 0xe59f0028, 0xe3a01000\n"
        ".word 0xeb005ad0, 0xe320f000, 0xe320f000, 0xeafffff6\n"
        ".word 0xe5940024, 0xe5850000, 0xe5940014, 0xe28ddf5f\n"
        ".word 0xecbd8b04, 0xe8bd80f0, 0x002dc6c0\n"
    );
}

// DECOMP_FUNC(0x00118fd8, 356)
// 84 ARM instructions through unconditional pop; 20 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_00118fd8() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d41f0, 0xe1a05000, 0xe1a07001, 0xe59f213c\n"
        ".word 0xe3a08000, 0xed2d8b02, 0xeef08a40, 0xeeb08a60\n"
        ".word 0xe5901090, 0xe59f0128, 0xe24dd008, 0xe1120001\n"
        ".word 0x0a000029, 0xe3110c02, 0x0a000041, 0xe2806008\n"
        ".word 0xe1a00006, 0xeb06aaa1, 0xe5950038, 0xeb06917d\n"
        ".word 0xe3a02000, 0xe59f00fc, 0xe1a01002, 0xeb069114\n"
        ".word 0xe285103c, 0xe5850038, 0xeb00e9df, 0xe5950038\n"
        ".word 0xed9f0a39, 0xeb069106, 0xe3a04000, 0xe5858090\n"
        ".word 0xe0840084, 0xe0850180, 0xe2800008, 0xeb0690f7\n"
        ".word 0xe2844001, 0xe3540002, 0xbafffff8, 0xe58d8000\n"
        ".word 0xe5950038, 0xe595106c, 0xe2853020, 0xe2852008\n"
        ".word 0xeb003fd8, 0xeef00a48, 0xed950a25, 0xe1a01007\n"
        ".word 0xe1a00005, 0xebffffcb, 0xe28dd008, 0xe1a00006\n"
        ".word 0xecbd8b02, 0xe8bd41f0, 0xea06aa5b, 0xe2804008\n"
        ".word 0xe1a00004, 0xeb06aa79, 0xeeb00a68, 0xe5857078\n"
        ".word 0xe5858084, 0xe3570000, 0xed850a25, 0xe5950038\n"
        ".word 0xcd9f0a16, 0xeb00b869, 0xe5950038, 0xe3a01000\n"
        ".word 0xeb0104c1, 0xe5950090, 0xe5951078, 0xe3800040\n"
        ".word 0xe3510000, 0xe5850090, 0xc3800020, 0xc5850090\n"
        ".word 0xe28dd008, 0xe1a00004, 0xecbd8b02, 0xe8bd41f0\n"
        ".word 0xea06aa41, 0xe28dd008, 0xecbd8b02, 0xe8bd81f0\n"
        ".word 0x00000202, 0x004e3154, 0x00007fff, 0x3f800000\n"
        ".word 0x00000000\n"
    );
}

// DECOMP_FUNC(0x0019feac, 368)
// 87 ARM instructions through unconditional pop; 20 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_0019feac() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d41f0, 0xe1a05000, 0xe24dd018, 0xe59f714c\n"
        ".word 0xe1a06001, 0xe5970000, 0xeb048f37, 0xeb047c11\n"
        ".word 0xe5974000, 0xe3a01000, 0xe3a00001, 0xeb049827\n"
        ".word 0xe2844a01, 0xe2844f93, 0xe3a08000, 0xe5941000\n"
        ".word 0xe2812001, 0xe0843101, 0xe5931008, 0xe0843102\n"
        ".word 0xe5842000, 0xe5830008, 0xe5d42018, 0xe3520000\n"
        ".word 0x01510000, 0x0a000002, 0xe594101c, 0xe12fff31\n"
        ".word 0xe5c48018, 0xed960a00, 0xeb047df9, 0xe59f30e0\n"
        ".word 0xe28d4008, 0xed9f0a37, 0xe893000f, 0xe884000f\n"
        ".word 0xe5970000, 0xeb046949, 0xeebd0ac0, 0xe3a0000b\n"
        ".word 0xe58d0004, 0xe58d8000, 0xe5d50037, 0xe28d4008\n"
        ".word 0xe3a01039, 0xe7942180, 0xee103a10, 0xe3a00002\n"
        ".word 0xeb047d79, 0xe5970000, 0xed9f0a27, 0xeb04693b\n"
        ".word 0xeebd0ac0, 0xe3a0000c, 0xe58d0004, 0xe58d8000\n"
        ".word 0xe5d50037, 0xe3a01039, 0xe0840180, 0xee103a10\n"
        ".word 0xe5902004, 0xe3a00002, 0xeb047d2d, 0xe5970000\n"
        ".word 0xe2804a01, 0xe2844f93, 0xe5940000, 0xe0841100\n"
        ".word 0xe2400001, 0xe5911008, 0xe5840000, 0xe0840100\n"
        ".word 0xe5d42018, 0xe5900008, 0xe3520000, 0x01510000\n"
        ".word 0x0a000002, 0xe594101c, 0xe12fff31, 0xe5c48018\n"
        ".word 0xe5970000, 0xeb0486db, 0xe5970000, 0xe320f000\n"
        ".word 0xeb0486ae, 0xe28dd018, 0xe8bd81f0, 0x00000000\n"
        ".word 0x0044ea00, 0x004028d4, 0x3eb33333, 0x3ea8f5c3\n"
    );
}

// DECOMP_FUNC(0x001e9728, 372)
// 86 ARM instructions through unconditional pop; 28 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_001e9728() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d40f0, 0xe59f014c, 0xed2d8b02, 0xe24dd00c\n"
        ".word 0xe5905000, 0xe5950008, 0xe3500064, 0xa3a00000\n"
        ".word 0xaa000049, 0xe59f6130, 0xe5960000, 0xeb036913\n"
        ".word 0xe5964000, 0xe3a01000, 0xe3a00001, 0xeb037204\n"
        ".word 0xe2844a01, 0xe2844f93, 0xe3a07000, 0xe5941000\n"
        ".word 0xe2812001, 0xe0843101, 0xe5931008, 0xe0843102\n"
        ".word 0xe5842000, 0xe5830008, 0xe5d42018, 0xe3520000\n"
        ".word 0x01510000, 0x0a000002, 0xe594101c, 0xe12fff31\n"
        ".word 0xe5c47018, 0xed9f8a35, 0xeeb00a48, 0xeb0357d5\n"
        ".word 0xe320f000, 0xe320f000, 0xeb0355d3, 0xe5960000\n"
        ".word 0xe3a01000, 0xeb03615a, 0xed9f0a2d, 0xe3a030ff\n"
        ".word 0xe1a02003, 0xeeb02a40, 0xeef00a40, 0xe1a01003\n"
        ".word 0xe1a00003, 0xeddf1a27, 0xed9f1a27, 0xeb035cc8\n"
        ".word 0xe5950008, 0xe3500064, 0xaa000007, 0xe3a0000b\n"
        ".word 0xe58d0004, 0xe59f2084, 0xe3a03000, 0xe3a0100e\n"
        ".word 0xe3a00002, 0xe58d7000, 0xeb03570e, 0xe5960000\n"
        ".word 0xe2804a01, 0xe2844f93, 0xe5940000, 0xe0841100\n"
        ".word 0xe2400001, 0xe5911008, 0xe5840000, 0xe0840100\n"
        ".word 0xe5d42018, 0xe5900008, 0xe3520000, 0x01510000\n"
        ".word 0x0a000002, 0xe594101c, 0xe12fff31, 0xe5c47018\n"
        ".word 0xeeb00a48, 0xeb0357a7, 0xe3a00000, 0xe28dd00c\n"
        ".word 0xecbd8b02, 0xe8bd80f0, 0x00446d78, 0x0044ea00\n"
        ".word 0x3f800000, 0x00000000, 0x43700000, 0x43c80000\n"
        ".word 0x0000018a\n"
    );
}

// DECOMP_FUNC(0x002b6f74, 380)
// 87 ARM instructions through unconditional pop; 32 trailing data bytes.
extern "C" __attribute__((naked)) void camp_func_002b6f74() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d43f0, 0xe24dd014, 0xe1a05001, 0xe28d1030\n"
        ".word 0xe3700001, 0xe1a07000, 0xe8910210, 0xe1a06002\n"
        ".word 0x059f0134, 0xe1a08003, 0x0a000011, 0xe3770002\n"
        ".word 0x03a00e3f, 0x0a00000e, 0xe3770003, 0x059f011c\n"
        ".word 0x0a00000b, 0xebffdd29, 0xe3500000, 0x159f0110\n"
        ".word 0x1a000007, 0xe1a00007, 0xebffdd07, 0xe3500000\n"
        ".word 0x03a00ffa, 0x0a000002, 0xe5900028, 0xe200001f\n"
        ".word 0xebffdd58, 0xe1a02000, 0xe1a03005, 0xe3a01013\n"
        ".word 0xe3a00002, 0xe88d0140, 0xebffdf1f, 0xe3540000\n"
        ".word 0xe320f000, 0x0a00002e, 0xe1a00007, 0xebffdcdf\n"
        ".word 0xe0800009, 0xe20040ff, 0xe1a00007, 0xebfa057d\n"
        ".word 0xe1540000, 0xc20040ff, 0xe3540001, 0x9a000024\n"
        ".word 0xe1540000, 0xa59f009c, 0xb59f009c, 0xeb001d25\n"
        ".word 0xe59f1098, 0xe3a00013, 0xeb00219f, 0xe28f1090\n"
        ".word 0xe3a07001, 0xe2889001, 0xe58d1008, 0xe88d0280\n"
        ".word 0xe1d010fa, 0xe1d000f8, 0xe3a03000, 0xe0812006\n"
        ".word 0xe0801005, 0xe3a00002, 0xeb001c3a, 0xe1871507\n"
        ".word 0xe3a00013, 0xeb002190, 0xe28d3008, 0xe28f1054\n"
        ".word 0xe2442001, 0xe8830006, 0xe3a03000, 0xe88d0280\n"
        ".word 0xe1d010fa, 0xe1d000f8, 0xe0812006, 0xe0801005\n"
        ".word 0xe3a00002, 0xeb001c2b, 0xe28dd014, 0xe8bd43f0\n"
        ".word 0xea001f92, 0xe28dd014, 0xe8bd83f0, 0x000003ef\n"
        ".word 0x000003f6, 0x00000419, 0xfbeb39ff, 0x72e027ff\n"
        ".word 0x00000402, 0x0000002b, 0x00006425\n"
    );
}

// DECOMP_FUNC(0x002b8e8c, 380)
// 93 ARM instructions through unconditional pop; 8 trailing data bytes.
extern "C" __attribute__((naked)) void camp_func_002b8e8c() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d40f0, 0xe1a04000, 0xe3a06000, 0xe5d00009\n"
        ".word 0xe24dd02c, 0xe1a05006, 0xe350000b, 0x0a00000b\n"
        ".word 0xe3500013, 0x0a000050, 0xe1d620fa, 0xe1d610f8\n"
        ".word 0xe2840f9a, 0xebffe650, 0xe1d520fa, 0xe1d510f8\n"
        ".word 0xe28dd02c, 0xe2840d0e, 0xe8bd40f0, 0xeaffe64a\n"
        ".word 0xe5940020, 0xe3500002, 0x0a00001a, 0xe59f7110\n"
        ".word 0xe3500003, 0x0a00002a, 0xe3500004, 0x1affffed\n"
        ".word 0xe2870070, 0xe28d5018, 0xe890000f, 0xe885000f\n"
        ".word 0xe28d1018, 0xe5940018, 0xe7911100, 0xe3a0000e\n"
        ".word 0xeb0019eb, 0xe2877080, 0xe1a06000, 0xe897000f\n"
        ".word 0xe28d5008, 0xe885000f, 0xe28d1008, 0xe5940018\n"
        ".word 0xe7911100, 0xe3a0000e, 0xeb0019e1, 0xe1a05000\n"
        ".word 0xe320f000, 0xeaffffd7, 0xe59f50a8, 0xe1c500d0\n"
        ".word 0xe1cd01f0, 0xe5940018, 0xe28d1010, 0xe7911100\n"
        ".word 0xe3a0000e, 0xeb0019d6, 0xe1a06000, 0xe1c500d8\n"
        ".word 0xe1cd00f8, 0xe5940018, 0xe28d1008, 0xe7911100\n"
        ".word 0xe3a0000e, 0xeb0019ce, 0xe1a05000, 0xe320f000\n"
        ".word 0xeaffffc4, 0xe2870058, 0xe28d3014, 0xe8900007\n"
        ".word 0xe8830007, 0xe28d1014, 0xe5940018, 0xe7911100\n"
        ".word 0xe3a0000e, 0xeb0019c2, 0xe2877064, 0xe1a06000\n"
        ".word 0xe8970007, 0xe28d3008, 0xe8830007, 0xe28d1008\n"
        ".word 0xe5940018, 0xe7911100, 0xe3a0000e, 0xeb0019b8\n"
        ".word 0xe1a05000, 0xe320f000, 0xeaffffae, 0xe28dd02c\n"
        ".word 0xe8bd80f0, 0x0040417c, 0x00403d7c\n"
    );
}

// DECOMP_FUNC(0x0011d31c, 384)
// 88 ARM instructions through unconditional pop; 32 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_0011d31c() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d43f0, 0xe24dd024, 0xe3a04000, 0xe1a07000\n"
        ".word 0xe59f6148, 0xe1a09001, 0xe1a08002, 0xe2865004\n"
        ".word 0xe1a01004, 0xe1a0000d, 0xe58d4000, 0xeb0661ad\n"
        ".word 0xe1b01fa0, 0x1a000002, 0xe59d1000, 0xe3a00000\n"
        ".word 0xe5851000, 0xe1b01fa0, 0x1b06a03f, 0xe5960004\n"
        ".word 0xe2865004, 0xe3500000, 0x0a000001, 0xef000023\n"
        ".word 0xe5854000, 0xe5869004, 0xe1a01004, 0xe1a0000d\n"
        ".word 0xe58d4000, 0xeb06619b, 0xe1b01fa0, 0xe320f000\n"
        ".word 0x1a000002, 0xe59d1000, 0xe3a00000, 0xe5861000\n"
        ".word 0xe1b01fa0, 0x1b06a02c, 0xe59f50c0, 0xe5950000\n"
        ".word 0xe3500000, 0x0a000001, 0xef000023, 0xe5854000\n"
        ".word 0xe59f00a8, 0xe2865008, 0xe1a01004, 0xe5808000\n"
        ".word 0xe1a0000d, 0xe58d4000, 0xeb066186, 0xe1b01fa0\n"
        ".word 0xe320f000, 0x1a000002, 0xe59d1000, 0xe3a00000\n"
        ".word 0xe5851000, 0xe1b01fa0, 0x1b06a017, 0xe59f0070\n"
        ".word 0xe3a01001, 0xeb06a001, 0xe59f0068, 0xe3a0c004\n"
        ".word 0xe28d5008, 0xe3e03001, 0xe5c04000, 0xe58dc010\n"
        ".word 0xe59fc05c, 0xe58d4020, 0xe59f1050, 0xe58dc014\n"
        ".word 0xe59fc050, 0xe59f2040, 0xe280000c, 0xe58dc018\n"
        ".word 0xe59fc044, 0xe58dc01c, 0xe8850018, 0xe28d3020\n"
        ".word 0xe88d0082, 0xe28d1010, 0xeb067e79, 0xe1b01fa0\n"
        ".word 0xe320f000, 0x1b069ffc, 0xe28dd024, 0xe8bd83f0\n"
        ".word 0x004e5290, 0x00465644, 0x00465630, 0x0012a2a0\n"
        ".word 0x0042c000, 0x00138254, 0x00138270, 0x00138264\n"
    );
}

// DECOMP_FUNC(0x00231178, 392)
// 97 ARM instructions through unconditional pop; 4 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_00231178() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d43f0, 0xe1a06001, 0xe1a08000, 0xe1a07002\n"
        ".word 0xe1a09003, 0xed2d8b06, 0xe24dd08c, 0xe28d00c0\n"
        ".word 0xe59d50d0, 0xecd08a04, 0xeb000881, 0xeeb08a40\n"
        ".word 0xe1a01007, 0xe1a00006, 0xeb023946, 0xe1a04000\n"
        ".word 0xe590000c, 0xe3500000, 0x0a000002, 0xe1d010b4\n"
        ".word 0xe3510001, 0x0a000041, 0xe3550000, 0x13500000\n"
        ".word 0x0a000031, 0xe59f1118, 0xe3a03004, 0xe3a02010\n"
        ".word 0xe28d0008, 0xfa025359, 0xe594000c, 0xe28d1038\n"
        ".word 0xe28d5028, 0xe2800010, 0xec900a04, 0xe28d0008\n"
        ".word 0xec800a04, 0xe594000c, 0xe2800020, 0xec900a04\n"
        ".word 0xe28d0018, 0xec800a04, 0xe594000c, 0xe2800030\n"
        ".word 0xec900a04, 0xe28d0028, 0xec800a04, 0xe594000c\n"
        ".word 0xe2800040, 0xec900a04, 0xe3a00000, 0xec810a04\n"
        ".word 0xe28d1048, 0xec810a04, 0xe895100e, 0xe28d5058\n"
        ".word 0xe885100e, 0xe28d5018, 0xe895100e, 0xe28d5068\n"
        ".word 0xe885100e, 0xe28d5008, 0xe895100e, 0xe28d5078\n"
        ".word 0xe58d0000, 0xe58d0004, 0xe885100e, 0xe28d3048\n"
        ".word 0xe28d2058, 0xe28d1068, 0xe28d0078, 0xeb0203b8\n"
        ".word 0xe594000c, 0xed900a02, 0xeb02391a, 0xe1a03009\n"
        ".word 0xe1a02007, 0xe1a01006, 0xe1a00008, 0xeccd8a04\n"
        ".word 0xebff7d26, 0xeeb00a48, 0xe320f000, 0xeb023911\n"
        ".word 0xe28dd08c, 0xecbd8b06, 0xe8bd43f0, 0xea02370e\n"
        ".word 0xe1a03009, 0xe1a02007, 0xe1a01006, 0xe1a00008\n"
        ".word 0xeccd8a04, 0xeb01fd85, 0xe28dd08c, 0xecbd8b06\n"
        ".word 0xe8bd83f0, 0x0014144c\n"
    );
}

// DECOMP_FUNC(0x002805d4, 392)
// 95 ARM instructions through unconditional pop; 12 trailing data bytes.
extern "C" __attribute__((naked)) void script_vm_func_002805d4() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d41f0, 0xe3e00000, 0xe3a06000, 0xe59f8168\n"
        ".word 0xe59f7168, 0xed2d8b08, 0xe24dd010, 0xeeb0ab40\n"
        ".word 0xe5c8002f, 0xe5c80031, 0xe5970f80, 0xe3500000\n"
        ".word 0xcddf9a53, 0xda00004d, 0xeeb0ba69, 0xe0660286\n"
        ".word 0xe3a04000, 0xe0875100, 0xe3540000, 0x0a000006\n"
        ".word 0xe3540001, 0x0a000010, 0xe3540002, 0x0a00001a\n"
        ".word 0xe3540003, 0x1a00002d, 0xea000023, 0xe285101c\n"
        ".word 0xeef02a6a, 0xec910a03, 0xe2851028, 0xeeb02a69\n"
        ".word 0xeef01a4a, 0xec918a03, 0xe1a0000d, 0xebff4815\n"
        ".word 0xe320f000, 0xe320f000, 0xea000020, 0xe2851034\n"
        ".word 0xeef02a6a, 0xec910a03, 0xe2851040, 0xeeb02a69\n"
        ".word 0xeef01a4a, 0xec918a03, 0xe1a0000d, 0xebff4809\n"
        ".word 0xe320f000, 0xe320f000, 0xea000014, 0xe285104c\n"
        ".word 0xeef02a6a, 0xec910a03, 0xe2851058, 0xeeb02a69\n"
        ".word 0xeef01a4a, 0xec918a03, 0xe1a0000d, 0xebff47fd\n"
        ".word 0xe320f000, 0xe320f000, 0xea000008, 0xe2851064\n"
        ".word 0xeef02a6a, 0xec910a03, 0xe2851070, 0xeeb02a69\n"
        ".word 0xeef01a4a, 0xec918a03, 0xe1a0000d, 0xebff47f1\n"
        ".word 0xeeb01a49, 0xeef00a68, 0xeeb00a48, 0xecdd1a03\n"
        ".word 0xeb011fe3, 0xeeb40acb, 0xeef1fa10, 0x3a000007\n"
        ".word 0xe2844001, 0xe3540004, 0xbaffffbe, 0xe1d501b8\n"
        ".word 0xe3500000, 0xe1d501ba, 0x05c8002f, 0x15c80031\n"
        ".word 0xe5970f80, 0xe2866001, 0xe1500006, 0xcaffffb1\n"
        ".word 0xe28dd010, 0xecbd8b08, 0xe8bd81f0, 0x0049f91c\n"
        ".word 0x004c14a0, 0x00000000\n"
    );
}

// DECOMP_FUNC(0x00156594, 396)
// 93 ARM instructions through unconditional pop; 24 trailing data bytes.
extern "C" __attribute__((naked)) void func_00156594() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d47f0, 0xe1a05000, 0xe5901014, 0xe3a00004\n"
        ".word 0xe1d00001, 0x0a000055, 0xe5950020, 0xe5907054\n"
        ".word 0xe2850040, 0xe5971298, 0xeb00135e, 0xe5d510e8\n"
        ".word 0xe3a00000, 0xe3510000, 0x0a000020, 0xe59f213c\n"
        ".word 0xe59f812c, 0xe59f912c, 0xe59fa12c, 0xe3a010ff\n"
        ".word 0xe5820000, 0xe5881000, 0xe5891000, 0xe58a1000\n"
        ".word 0xe59560e4, 0xe3a04000, 0xe3560000, 0xda000007\n"
        ".word 0xe5950064, 0xe1a01004, 0xe7902104, 0xe1a00005\n"
        ".word 0xeb00111d, 0xe2844001, 0xe1560004, 0xcafffff7\n"
        ".word 0xe5992000, 0xe5981000, 0xe59a3000, 0xe59f00e0\n"
        ".word 0xe1811402, 0xe59f20dc, 0xe1811c03, 0xe5923000\n"
        ".word 0xe283c008, 0xe5830004, 0xe5831000, 0xe582c000\n"
        ".word 0xe5d500eb, 0xe3500000, 0x11a00005, 0x1b0012cf\n"
        ".word 0xe5d500ea, 0xe3a08001, 0xe3500000, 0x159560e0\n"
        ".word 0x13560000, 0xda000014, 0xe5950008, 0xe5901008\n"
        ".word 0xe5911068, 0xe3510000, 0xda000006, 0xe2462001\n"
        ".word 0xe3520000, 0xe3a01000, 0xa1a01002, 0xe20110ff\n"
        ".word 0xe3811801, 0xe580101c, 0xe3a04000, 0xe595004c\n"
        ".word 0xe1a01004, 0xe7902104, 0xe1a00005, 0xeb00103e\n"
        ".word 0xe2844001, 0xe1540006, 0xbafffff7, 0xe597029c\n"
        ".word 0xe59520c0, 0xe59510a0, 0xe7920100, 0xe1510000\n"
        ".word 0x158500a0, 0x15c580ec, 0xe5d500ec, 0xe3500000\n"
        ".word 0x0a000002, 0xe1a00005, 0xe8bd47f0, 0xea000fc6\n"
        ".word 0xe8bd87f0, 0x00472104, 0x00472108, 0x0047210c\n"
        ".word 0x00472100, 0x000b01c4, 0x004652a0\n"
    );
}

// DECOMP_FUNC(0x0024f460, 396)
// 95 ARM instructions through unconditional pop; 16 trailing data bytes.
extern "C" __attribute__((naked)) void script_vm_func_0024f460() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d5fff, 0xe59f9170, 0xe59fb170, 0xe3a0e001\n"
        ".word 0xed2d0b06, 0xed2d8b04, 0xe28d4068, 0xeef08a40\n"
        ".word 0xe8941001, 0xe28d4070, 0xeeb08a62, 0xe89405e0\n"
        ".word 0xe28d408c, 0xeef09a41, 0xed9f0a51, 0xeeb09a60\n"
        ".word 0xec943a03, 0xe5994004, 0xe0641184, 0xe0811101\n"
        ".word 0xe08bb101, 0xe28b1018, 0xe58be018, 0xedcb1a08\n"
        ".word 0xed8b2a07, 0xe58b3028, 0xe58be024, 0xed8b3a0b\n"
        ".word 0xedcb3a0c, 0xed8b4a0d, 0xe5cb0038, 0xe5cbc039\n"
        ".word 0xe5cb503a, 0xe5cb603b, 0xe5cb703c, 0xe5cb803d\n"
        ".word 0xe1cbe3be, 0xe28b2024, 0xe58b1040, 0xe28b0044\n"
        ".word 0xe58b2070, 0xe58b0068, 0xedcb8a11, 0xed8b0a14\n"
        ".word 0xed8b8a15, 0xed8b0a16, 0xe28b0048, 0xec809a02\n"
        ".word 0xe59d0030, 0xe58b0064, 0xe28b005c, 0xebff3419\n"
        ".word 0xe28db060, 0xeef01a48, 0xeeb01a69, 0xeef00a49\n"
        ".word 0xeeb00a68, 0xe1a05000, 0xe89b0006, 0xe59d0028\n"
        ".word 0xe59d3098, 0xeb000c68, 0xe0642204, 0xe59f3084\n"
        ".word 0xe0824284, 0xe0651205, 0xe0815285, 0xe0834184\n"
        ".word 0xe0833185, 0xe59d6084, 0xe5830124, 0xe5c3a16c\n"
        ".word 0xe5c4616d, 0xe59d0028, 0xe2834e13, 0xe3e0c000\n"
        ".word 0xe583012c, 0xe59d102c, 0xe2830c01, 0xe3a02000\n"
        ".word 0xe8841002, 0xe1c025bc, 0xe1c0c5be, 0xe5c32164\n"
        ".word 0xe59d1088, 0xe5c31128, 0xe5c3216e, 0xe1c026b0\n"
        ".word 0xe1c026b2, 0xe5990004, 0xe2800001, 0xe5890004\n"
        ".word 0xecbd8b04, 0xe28dd028, 0xe8bd9ff0, 0x00447a28\n"
        ".word 0x004afd64, 0x00000000, 0x004a1264\n"
    );
}

// DECOMP_FUNC(0x0033b3e0, 400)
//
// Inserts one battle unit into the twelve-slot, key-ordered unit list of the
// UI context and then forwards the shared UI buffer to 0x0025508c.
//
// Recovered contract (ARM 0x0033B3E0..0x0033B564):
//   * `context` is the UI object, `id` a battle-unit index (s32).
//   * The unit flag word lives in the 0x114-byte record table whose base
//     pointer sits at context+0x1E98, at record offset +0x50.  Bits 0x01 and
//     0x80 must both be set; otherwise the flag word is returned unchanged
//     (the caller at 0x003BD2EC raises exactly 0x81 in that word first).
//   * The value to insert is the s16 at +0x6E of the 0x288-byte actor record
//     that 0x00282b94(context, id) finds.  The helper result is dereferenced
//     without a null check, exactly like `ldrsh r0,[r0,#0x6e]` (0x0033B420).
//   * The slot array is twelve s16 at context+0x2F06; context+0x2F1E holds the
//     cursor (read signed).  Insertion starts at cursor+1, is skipped entirely
//     when that index is >= 12, and otherwise lands in the first slot whose
//     value is negative (the scan only advances over slots >= 0).
//   * When the start index is <= 10 the window [start, 11] is re-ordered by an
//     exchange pass: for j < i, when both slots are non-negative, slot j and
//     slot i swap if the primary key of slot j is smaller than the primary key
//     of slot i; on equal primary keys they swap if the secondary key of slot j
//     is greater.  The primary key is the s16 truncation of the sum of the two
//     zero-extended u16 fields at actor+0x1C2 and actor+0x254; the secondary
//     key is the s16 at actor+0x008.
//   * Return: the flag word on the early exit, otherwise the value returned by
//     the tail call 0x0025508c(*0x00439CA8).
//
// The sort starts at cursor+1 rather than at the slot the value was written to;
// both indices are kept separately below because an occupied prefix makes them
// differ (original `mov r2,r1` at 0x0033B430 versus the scan on r1).
namespace ui_b3e0 {

// UI context fields (offsets from the r0/`context` register).
constexpr u32 kFlagTablePointer = 0x1E98;    // 0x0033B3E4..0x0033B3F4
constexpr u32 kFlagFieldOffset = 0x50;       // 0x0033B3FC..0x0033B404
constexpr u32 kFlagRecordStride = 0x114;     // 0x0033B3EC/0x0033B3F8/0x0033B400
constexpr u32 kFlagBit0 = 0x00000001;        // `tst r0,#1` (0x0033B408)
constexpr u32 kFlagBit7 = 0x00000080;        // `tstne r0,#0x80` (0x0033B40C)

constexpr u32 kActorTablePointer = 0x1FC0;   // 0x0033B45C..0x0033B4B4
constexpr u32 kSlotArrayOffset = 0x2F06;     // ctx+0x2F00, `ldrsh [.,#6]`
constexpr u32 kCursorOffset = 0x2F1E;        // literal 0x2F1E + r4 (0x0033B41C)
constexpr s32 kSlotCount = 12;               // `cmp #0xc` (0x0033B42C/0x0033B530)
constexpr s32 kSortOuterLimit = 11;          // `cmp r2,#0xb` (0x0033B454/0x0033B53C)

// 0x288-byte actor record reached through context+0x1FC0.
constexpr u32 kActorStride = 0x288;          // ip*17 + ip*64, then lsl #3
constexpr u32 kInsertValueOffset = 0x6E;     // 0x0033B420
constexpr u32 kSecondaryKeyOffset = 0x008;   // `mov r5,#8` (0x0033B510)
constexpr u32 kPrimaryKeyLowOffset = 0x1C2;  // 0xCC+0xF6 (0x0033B4DC)
constexpr u32 kPrimaryKeyHighOffset = 0x254; // 0xCC+0x188 (0x0033B4D8)

constexpr u32 kSharedUiBuffer = 0x00439CA8;  // literal 0x00439CA8 (0x0033B554)

}  // namespace ui_b3e0

extern "C" u8* ui_func_00282b94(void* context, s32 id);
extern "C" u32 script_vm_func_0025508c(void* buffer);

namespace {

// s16 slot accessor; a negative index addresses the words just before the
// array, which is what the original `add r3,r4,r1,lsl #1` also does.
s16* SlotAt(u8* ui, s32 index) {
    return reinterpret_cast<s16*>(ui + ui_b3e0::kSlotArrayOffset) + index;
}

const u8* ActorAt(const u8* actors, s32 index) {
    return actors + static_cast<u32>(index) * ui_b3e0::kActorStride;
}

// `ldrh`/`ldrh`/`add`/`sxth` (0x0033B4D4..0x0033B4F0): both u16 fields are
// zero-extended, summed modulo 2^32 and truncated to s16.
s32 PrimaryKey(const u8* actors, s32 index) {
    const u8* const record = ActorAt(actors, index);
    const u32 low =
        *reinterpret_cast<const u16*>(record + ui_b3e0::kPrimaryKeyLowOffset);
    const u32 high =
        *reinterpret_cast<const u16*>(record + ui_b3e0::kPrimaryKeyHighOffset);
    return static_cast<s16>(static_cast<u16>(low + high));
}

s32 SecondaryKey(const u8* actors, s32 index) {
    return *reinterpret_cast<const s16*>(
        ActorAt(actors, index) + ui_b3e0::kSecondaryKeyOffset);
}

}  // namespace

extern "C" u32 ui_func_0033b3e0(void* context, s32 id) {
    u8* const ui = static_cast<u8*>(context);

    // 0x0033B3E4..0x0033B410: unit flag gate.
    const u8* const flag_table =
        *reinterpret_cast<u8* const*>(ui + ui_b3e0::kFlagTablePointer);
    const u32 flags = *reinterpret_cast<const u32*>(
        flag_table + ui_b3e0::kFlagFieldOffset +
        static_cast<u32>(id) * ui_b3e0::kFlagRecordStride);
    if ((flags & ui_b3e0::kFlagBit0) == 0 ||
        (flags & ui_b3e0::kFlagBit7) == 0) {
        return flags;
    }

    // 0x0033B414..0x0033B42C: helper result and cursor, in this order.  The
    // +0x6E read is volatile so it stays on every path after the call, as in
    // the original: when the cursor already saturates the slot list the value
    // is still loaded (and a bad helper pointer still faults there).
    const s32 value = *reinterpret_cast<const volatile s16*>(
        reinterpret_cast<const u8*>(ui_func_00282b94(context, id)) +
        ui_b3e0::kInsertValueOffset);
    const s32 start =
        static_cast<s32>(*reinterpret_cast<const s16*>(
            ui + ui_b3e0::kCursorOffset)) + 1;

    // 0x0033B42C..0x0033B460: find the first free (negative) slot.
    s32 free_index = start;
    while (free_index < ui_b3e0::kSlotCount &&
           *SlotAt(ui, free_index) >= 0) {
        ++free_index;
    }

    if (free_index < ui_b3e0::kSlotCount) {
        *SlotAt(ui, free_index) = static_cast<s16>(value);

        // 0x0033B464..0x0033B544: exchange pass over [start, 11].
        if (start < ui_b3e0::kSortOuterLimit) {
            const u8* const actors = *reinterpret_cast<u8* const*>(
                ui + ui_b3e0::kActorTablePointer);
            for (s32 j = start; j < ui_b3e0::kSortOuterLimit; ++j) {
                if (*SlotAt(ui, j) < 0) {
                    continue;
                }
                for (s32 i = j + 1; i < ui_b3e0::kSlotCount; ++i) {
                    const s32 slot_i = *SlotAt(ui, i);
                    if (slot_i < 0) {
                        continue;
                    }
                    const s32 slot_j = *SlotAt(ui, j);
                    const s32 key_j = PrimaryKey(actors, slot_j);
                    const s32 key_i = PrimaryKey(actors, slot_i);
                    const bool swap =
                        key_j != key_i
                            ? key_j < key_i
                            : SecondaryKey(actors, slot_j) >
                                  SecondaryKey(actors, slot_i);
                    if (swap) {
                        *SlotAt(ui, j) = static_cast<s16>(slot_i);
                        *SlotAt(ui, i) = static_cast<s16>(slot_j);
                    }
                }
            }
        }
    }

    // 0x0033B554..0x0033B560: return 0x0025508c(*0x00439CA8).
    return script_vm_func_0025508c(
        *reinterpret_cast<void* const*>(ui_b3e0::kSharedUiBuffer));
}

// DECOMP_FUNC(0x003d9e10, 400)
//
// Teardown of the script-VM context object.  It clears two scalar words,
// drains three fixed arrays of owned subobjects, releases the optional
// reference-counted subobject at +0x1CF8, drops one global graphics flag and
// then runs three global cleanup helpers.
//
// Recovered contract (ARM 0x003D9E10..0x003D9FA0):
//   * `object = r0`; r1-r3 and the stack are not read.  The 97 return-path
//     instructions end in `pop {r4,r5,r6,r7,r8,pc}`; the last 12 bytes are the
//     literal pool 0x00003048, 0x00002F98, 0x004342C8.
//   * 0x003D9E10..0x003D9E2C: `*(u32*)(object+0x3048) = 0`, then
//     0x00227220(object) and 0x003DAABC(object), in that order.
//   * 0x003D9E30..0x003D9E78: 11 entries of 0x8C bytes at object+0x25C0.
//     Per entry: byte +0x00 = 0xFF; 0x002C4B30(entry+0x08, 0x80) zeroes the
//     0x80-byte block; a non-null pointer at +0x04 is passed to 0x002C4360 and
//     cleared; byte +0x88 = 0.  The bound is signed `cmp r5,#0xb` / `blt`.
//   * 0x003D9E7C..0x003D9E9C: if object+0x1CF8 is non-null, call its virtual
//     slot 1 (`*[obj]` is the vtable, `[vtable+4]` the target, receiver = obj)
//     and clear the slot.  The concrete target is unresolved; the call is
//     reproduced through the observed vtable offset.
//   * 0x003D9EA0..0x003D9EE0: 0x0022788C(object),
//     `*(u32*)(object+0x2F98) = 0`, 0x0024DE78(), 0x00262C64(), then if the
//     global pointer at 0x004342C8 is non-null clear bit 27 (0x08000000) of
//     its u32 at +0x634, and finally 0x0027E094(object).
//     The two no-argument helpers ignore r0: at their call sites r0 still
//     holds 0x2F98 (0x003D9EAC) and the return of 0x0024DE78 respectively.
//   * 0x003D9EE4..0x003D9F58: 50 entries of 40 bytes at object+0x190.
//     Load +0x20 first (virtual object), then store +0x04 = -1,
//     +0x24 = 0, +0x08 = -1, +0x1C = 0.  If +0x20 is non-null call its
//     virtual slot 1 and then set +0x20 = 0.  Re-load +0x00 (the virtual call
//     may have rewritten it); when non-null, read `[[ptr+8]+0x0C]` as a signed
//     word and, when it is >= 0, call 0x00152AF8(ptr), then re-load +0x00 again
//     and call 0x002A7AA0(ptr), and finally set +0x00 = 0.
//   * 0x003D9F5C..0x003D9F90: 50 entries of 48 bytes at object+0x1398.
//     Store +0x00 = -1, +0x04 = 0, call 0x00241E88(entry+0x08), then store
//     +0x2C = 0 (the original increments the index before that store, but the
//     entry base register is unchanged).  Bound 0x32.
//
// Return value: none.  The caller (e.g. 0x002C9F7C) frees `object` itself after
// this body returns, so this is the destructor/clear body, not a deallocator.
namespace func_3d9e10 {

// Scalar words cleared at the start and in the middle of the teardown.
constexpr u32 kTopZeroWord = 0x3048;    // literal 0x00003048 (0x003D9F94)
constexpr u32 kLowZeroWord = 0x2F98;    // literal 0x00002F98 (0x003D9F98)

// First owned array: 11 entries of 0x8C bytes at +0x25C0 (0x003D9E38..E78).
constexpr u32 kPoolOffset = 0x25C0;     // `add r4,r6,#0x25c0`
constexpr u32 kPoolStride = 0x8C;       // 7*i + 28*i = 35*i, then lsl #2
constexpr s32 kPoolCount = 11;          // `cmp r5,#0xb`
constexpr u32 kPoolStateByte = 0x00;    // `strb r8,[r4]`
constexpr u8 kPoolStateDead = 0xFF;     // r8 = 0xFF at 0x003D9E34
constexpr u32 kPoolPointerOffset = 0x04;  // `ldr/str [r4,#4]`
constexpr u32 kPoolBlockOffset = 0x08;    // `add r0,r4,#8`
constexpr u32 kPoolBlockSize = 0x80;      // r1 = 0x80 at 0x003D9E3C
constexpr u32 kPoolTailByte = 0x88;       // `strb r7,[r4,#0x88]`

// Optional reference-counted subobject released through its vtable.
constexpr u32 kMidSubobjectSlot = 0x1CF8;  // `add r4,r6,#0x1c00; add #0xf8`

// Global graphics pointer and the controlled flag at +0x634 (0x003D9EC0).
constexpr u32 kGlobalPointer = 0x004342C8;  // literal 0x004342C8 (0x003D9F9C)
constexpr u32 kGlobalFlagsOffset = 0x634;   // `ldr r1,[r0,#0x634]`
constexpr u32 kGlobalClearBit = 0x08000000; // `bic r1,r1,#0x8000000`

// Second owned array: 50 entries of 40 bytes at +0x190 (0x003D9EEC..F58).
constexpr u32 kObjectOffset = 0x190;
constexpr u32 kObjectStride = 40;        // 5*i, then lsl #3
constexpr s32 kObjectCount = 50;         // `cmp r5,#0x32`
constexpr u32 kObjectPrimaryOffset = 0x00;
constexpr u32 kObjectMinusOneA = 0x04;
constexpr u32 kObjectMinusOneB = 0x08;
constexpr u32 kObjectZeroA = 0x1C;
constexpr u32 kObjectSecondaryOffset = 0x20;  // `ldr r0,[r0,#0x1b0]`
constexpr u32 kObjectZeroB = 0x24;
constexpr u32 kObjectLinkOffset = 0x08;       // `ldr r1,[r0,#8]`
constexpr u32 kObjectLinkStateOffset = 0x0C;  // `ldr r1,[r1,#0xc]`
constexpr u32 kAllOnes = 0xFFFFFFFF;     // `mvn r8,#0` at 0x003D9EE8

// Third owned array: 50 entries of 48 bytes at +0x1398 (0x003D9F60..F8C).
constexpr u32 kTailOffset = 0x1398;      // `add r0,r6,#0x1000; add #0x3a0`
constexpr u32 kTailStride = 48;          // 3*i, then lsl #4
constexpr s32 kTailCount = 50;           // `cmp r4,#0x32`
constexpr u32 kTailMinusOne = 0x00;
constexpr u32 kTailZeroA = 0x04;
constexpr u32 kTailSubobject = 0x08;     // r0 = entry + 0x13A0 - 0x1398
constexpr u32 kTailZeroB = 0x2C;         // entry + 0x13C4 - 0x1398

}  // namespace func_3d9e10

// Direct callees.  Every one is an existing raw-ARM body in this repository.
extern "C" void script_vm_func_00227220(void* object);
extern "C" void engine_func_003daabc(void* object);
extern "C" void engine_func_002c4b30(void* destination, u32 size);
extern "C" void engine_func_002c4360(void* block);
extern "C" void engine_func_0022788c(void* object);
extern "C" void engine_func_0024de78(void);
extern "C" void ui_func_00262c64(void);
extern "C" void script_vm_func_0027e094(void* object);
extern "C" void script_vm_func_00152af8(void* object);
extern "C" void script_vm_func_002a7aa0(void* object);
extern "C" void camp_func_00241e88(void* object);

namespace {

// `ldr r1,[r0]; ldr r1,[r1,#4]; blx r1` (0x003D9E90 and 0x003D9F14): virtual
// slot 1.  The concrete target lives in the object's vtable and is not
// resolvable statically; the test installs a deterministic slot.
void CallVirtualSlot1(void* object) {
    using VirtualFn = void (*)(void*);
    VirtualFn* const vtable = *reinterpret_cast<VirtualFn**>(object);
    vtable[1](object);
}

// `ldr r1,[r0,#8]; ldr r1,[r1,#0xc]; cmp r1,#0` (0x003D9F30..F3C): the
// second-level word is compared as signed.  A null link word faults exactly
// like the original.
bool ReleaseStateIsNonNegative(void* object) {
    const u32* const link = *reinterpret_cast<u32* const*>(
        static_cast<u8*>(object) + func_3d9e10::kObjectLinkOffset);
    const s32 state = *reinterpret_cast<const s32*>(
        reinterpret_cast<const u8*>(link) +
        func_3d9e10::kObjectLinkStateOffset);
    return state >= 0;
}

}  // namespace

extern "C" void script_vm_func_003d9e10(void* object) {
    u8* const base = static_cast<u8*>(object);

    // 0x003D9E10..0x003D9E2C: top-level word and two context resets.
    *reinterpret_cast<u32*>(base + func_3d9e10::kTopZeroWord) = 0;
    script_vm_func_00227220(base);
    engine_func_003daabc(base);

    // 0x003D9E30..0x003D9E78: 11-entry owned-block array at +0x25C0.
    for (u32 i = 0; i < static_cast<u32>(func_3d9e10::kPoolCount); ++i) {
        u8* const entry =
            base + func_3d9e10::kPoolOffset + i * func_3d9e10::kPoolStride;
        entry[func_3d9e10::kPoolStateByte] = func_3d9e10::kPoolStateDead;
        engine_func_002c4b30(entry + func_3d9e10::kPoolBlockOffset,
                            func_3d9e10::kPoolBlockSize);

        void* const block = *reinterpret_cast<void**>(
            entry + func_3d9e10::kPoolPointerOffset);
        if (block != nullptr) {
            engine_func_002c4360(block);
            *reinterpret_cast<void**>(
                entry + func_3d9e10::kPoolPointerOffset) = nullptr;
        }
        entry[func_3d9e10::kPoolTailByte] = 0;
    }

    // 0x003D9E7C..0x003D9E9C: optional virtual subobject at +0x1CF8.
    u8* const mid_slot = base + func_3d9e10::kMidSubobjectSlot;
    void* const mid = *reinterpret_cast<void**>(mid_slot);
    if (mid != nullptr) {
        CallVirtualSlot1(mid);
        *reinterpret_cast<void**>(mid_slot) = nullptr;
    }

    // 0x003D9EA0..0x003D9EE0: context reset, global cleanups, global flag.
    engine_func_0022788c(base);
    *reinterpret_cast<u32*>(base + func_3d9e10::kLowZeroWord) = 0;
    engine_func_0024de78();
    ui_func_00262c64();

    void* const global =
        *reinterpret_cast<void* const*>(func_3d9e10::kGlobalPointer);
    if (global != nullptr) {
        u32* const flags = reinterpret_cast<u32*>(
            static_cast<u8*>(global) + func_3d9e10::kGlobalFlagsOffset);
        *flags &= ~func_3d9e10::kGlobalClearBit;
    }
    script_vm_func_0027e094(base);

    // 0x003D9EE4..0x003D9F58: 50-entry 40-byte array at +0x190.  The +0x20
    // pointer is loaded before the field stores; the +0x00 pointer is loaded
    // only after the +0x20 virtual call, and re-loaded again after the
    // conditional 0x00152AF8 call.
    for (u32 i = 0; i < static_cast<u32>(func_3d9e10::kObjectCount); ++i) {
        u8* const entry =
            base + func_3d9e10::kObjectOffset + i * func_3d9e10::kObjectStride;
        void* const secondary = *reinterpret_cast<void**>(
            entry + func_3d9e10::kObjectSecondaryOffset);

        *reinterpret_cast<u32*>(entry + func_3d9e10::kObjectMinusOneA) =
            func_3d9e10::kAllOnes;
        *reinterpret_cast<u32*>(entry + func_3d9e10::kObjectZeroB) = 0;
        *reinterpret_cast<u32*>(entry + func_3d9e10::kObjectMinusOneB) =
            func_3d9e10::kAllOnes;
        *reinterpret_cast<u32*>(entry + func_3d9e10::kObjectZeroA) = 0;

        if (secondary != nullptr) {
            CallVirtualSlot1(secondary);
            *reinterpret_cast<void**>(
                entry + func_3d9e10::kObjectSecondaryOffset) = nullptr;
        }

        void* const primary = *reinterpret_cast<void**>(
            entry + func_3d9e10::kObjectPrimaryOffset);
        if (primary != nullptr) {
            if (ReleaseStateIsNonNegative(primary)) {
                script_vm_func_00152af8(primary);
            }
            void* const reloaded = *reinterpret_cast<void**>(
                entry + func_3d9e10::kObjectPrimaryOffset);
            script_vm_func_002a7aa0(reloaded);
            *reinterpret_cast<void**>(
                entry + func_3d9e10::kObjectPrimaryOffset) = nullptr;
        }
    }

    // 0x003D9F5C..0x003D9F90: 50-entry 48-byte array at +0x1398.
    for (u32 i = 0; i < static_cast<u32>(func_3d9e10::kTailCount); ++i) {
        u8* const entry =
            base + func_3d9e10::kTailOffset + i * func_3d9e10::kTailStride;
        *reinterpret_cast<u32*>(entry + func_3d9e10::kTailMinusOne) =
            func_3d9e10::kAllOnes;
        *reinterpret_cast<u32*>(entry + func_3d9e10::kTailZeroA) = 0;
        camp_func_00241e88(entry + func_3d9e10::kTailSubobject);
        *reinterpret_cast<u32*>(entry + func_3d9e10::kTailZeroB) = 0;
    }
}

// DECOMP_FUNC(0x003dff3c, 400)
//
// Emits a ten- or fourteen-word rendering record from a small source structure
// and optionally hands it to the shared continuation at 0x0022673C.
//
// Recovered contract (ARM 0x003DFF3C..0x003E00AB, literal pool 0x003E00AC):
//   * `object` is the source structure (kept in r12 for the whole body),
//     `out` is the word cursor, `submit` (r2) selects the tail call and
//     `extra` (r3) selects four additional leading words.
//   * `object[0]` gates the complete packing block: when zero no word is
//     written, but the tail call still happens.
//   * The fixed leading words are 0x00E40103 then 0x00010100.  When
//     `extra != 0` four more words follow: 0, 0x00200080, 0, 0.
//   * `object+0x04` is converted to a 24-bit truncating fixed-point value
//     (see ToFixed24): the original tests `v > 0.0f` with VCMPE, rejects
//     float exponents of 0xFF (infinity/NaN), scales by 2^24 with VMUL,
//     saturates to 0x00FFFFFF when the scaled bit pattern is >= 0x4B800000
//     and otherwise uses VCVT.U32.F32 (round towards zero).  Every rejected
//     input yields 0.  Bit 0 of the value is then replaced by
//     `object[1] == 0 ? 1 : 0`; the word 0x000F008B follows.
//   * The word after that packs two IEEE binary16 halves produced by the
//     truncating conversion in ToHalf: bits 0..15 hold
//     `object+0x0C + object+0x10`, bits 16..31 hold `-(object+0x0C)`.
//     The final word is 0x000F0130.
//   * `submit == 0` returns the advanced cursor; otherwise the routine tail
//     calls 0x0022673C with (*(u32*)(object+0x14) + 0x7C, cursor, 1) and
//     forwards its return value.
//
// 0x0022673C is a separate entry point that the ledger folds into
// func_00226690 (its prologue/`bx lr` pair at 0x22673C/0x22679C is distinct
// from 0x00226690's own return at 0x226730); it is declared below.
namespace record_dff3c {

// Source-structure offsets (all reached through the r12 copy of `object`).
constexpr u32 kGateByte = 0x00;              // ldrb [ip] (0x003DFF44)
constexpr u32 kHalfFlagByte = 0x01;          // ldrb [ip,#1] (0x003DFFC4)
constexpr u32 kFixedValue = 0x04;            // vldr s0,[ip,#4] (0x003DFF7C)
constexpr u32 kSecondValue = 0x0C;           // vldr s1,[ip,#0xc] (0x003DFFEC)
constexpr u32 kThirdValue = 0x10;            // vldr s0,[ip,#0x10] (0x003DFFE8)
constexpr u32 kObjectPointer = 0x14;         // ldr r0,[ip,#0x14] (0x003E0094)
constexpr u32 kTailBias = 0x7C;              // add r0,r0,#0x7c (0x003E00A0)

// Fixed output words (literal pool 0x003E00AC..0x003E00C8).
constexpr u32 kHeaderWord0 = 0x00E40103;     // 0x003E00AC
constexpr u32 kHeaderWord1 = 0x00010100;     // 0x003E00B0
constexpr u32 kExtraWord = 0x00200080;       // 0x003E00B4
constexpr u32 kFixedWord0 = 0x000F008B;      // 0x003E00C4
constexpr u32 kFixedWord1 = 0x000F0130;      // 0x003E00C8

// 0x003DFF80/0x003E00B8 compare against +0.0f; 0x003DFFA8/0x003E00BC
// multiply by 2^24; 0x003DFFA4/0x003E00C0 is the raw bit pattern of 2^24.
constexpr f32 kPositiveZero = 0.0f;
constexpr f32 kFixedScale = 16777216.0f;
constexpr u32 kFixedScaleBits = 0x4B800000u;

// `mvnle r0,#0xff000000` (0x003DFFBC) saturates to the 24-bit maximum.
constexpr u32 kFixedSaturated = 0x00FFFFFFu;

// ToHalf exponent rebase/bias: `sub r3,r3,#0x70` (0x003E0008/0x003E004C).
constexpr u32 kHalfBias = 0x70;

// The parenthesised low bit is the only rounding the original performs.
constexpr u32 kFixedMask = ~1u;
constexpr u32 kHalfMantissaMask = 0x3FFu;

}  // namespace record_dff3c

// Tail continuation at 0x0022673C (see the comment above).
extern "C" u32 func_0022673c(u32 object, u32* out, u32 mode);

namespace {

inline u32 FloatBits(f32 value) {
    u32 bits;
    __builtin_memcpy(&bits, &value, sizeof(bits));
    return bits;
}

inline f32 ReadF32(const u8* base, u32 offset) {
    f32 value;
    __builtin_memcpy(&value, base + offset, sizeof(value));
    return value;
}

inline u32 ReadU32(const u8* base, u32 offset) {
    u32 value;
    __builtin_memcpy(&value, base + offset, sizeof(value));
    return value;
}

// 0x003DFF7C..0x003DFFC0: VCMPE/VMUL/VCVT.U32.F32 24-bit conversion.
u32 ToFixed24(f32 value) {
    const u32 bits = FloatBits(value);

    // `vcmpe.f32 s0,#0.0` + `bls`: false for every value <= 0 and for NaN,
    // while the unordered case is caught by the exponent test below.
    if (!(value > record_dff3c::kPositiveZero)) {
        return 0;
    }
    if (((bits << 1) >> 24) == 0xFFu) {  // `cmp #0xff,r3,lsr #24`
        return 0;
    }

    const f32 scaled = value * record_dff3c::kFixedScale;
    // `cmp r3,r0` is a signed compare of the two raw bit patterns; both
    // operands are non-negative here, so the ordering is the same.
    if (!(FloatBits(scaled) < record_dff3c::kFixedScaleBits)) {
        return record_dff3c::kFixedSaturated;
    }
    return static_cast<u32>(scaled);  // VCVT.U32.F32 (round towards zero)
}

// 0x003DFFDC..0x003E0030 and 0x003E0034..0x003E0074: the shared, unrounded
// binary16 conversion.  `+/-0` and every value whose biased exponent is below
// 0x70 collapse to a signed zero; larger values keep the top 10 mantissa bits
// and lose the excess exponent bits through the final `uxth`.
u16 ToHalf(f32 value) {
    const u32 bits = FloatBits(value);
    const u32 sign = (bits >> 31) << 15;
    if ((bits & 0x7FFFFFFFu) == 0) {  // `bics r3,r0,#0x80000000`
        return static_cast<u16>(sign);
    }
    const u32 exponent = (bits << 1) >> 24;
    const s32 rebased = static_cast<s32>(exponent) -
                        static_cast<s32>(record_dff3c::kHalfBias);
    if (rebased < 0) {  // `cmp r3,#0` + `blt`
        return static_cast<u16>(sign);
    }
    return static_cast<u16>(
        (static_cast<u32>(rebased) << 10) |
        ((bits >> 13) & record_dff3c::kHalfMantissaMask) | sign);
}

}  // namespace

extern "C" u32 func_003dff3c(const u8* object, u32* out, u32 submit, u32 extra) {
    u32* cursor = out;

    // 0x003DFF3C..0x003DFF4C: byte-0 gate.
    if (object[record_dff3c::kGateByte] != 0) {
        // 0x003DFF50..0x003DFF60: fixed header words.
        *cursor++ = record_dff3c::kHeaderWord0;
        *cursor++ = record_dff3c::kHeaderWord1;

        // 0x003DFF64..0x003DFF78: optional four-word extension.
        if (extra != 0) {
            *cursor++ = 0;
            *cursor++ = record_dff3c::kExtraWord;
            *cursor++ = 0;
            *cursor++ = 0;
        }

        // 0x003DFF7C..0x003DFFDC: 24-bit value, flag bit, fixed word.
        const u32 fixed = ToFixed24(ReadF32(object, record_dff3c::kFixedValue));
        const u32 low_bit = (object[record_dff3c::kHalfFlagByte] == 0) ? 1u : 0u;
        *cursor++ = (fixed & record_dff3c::kFixedMask) | low_bit;
        *cursor++ = record_dff3c::kFixedWord0;

        // 0x003DFFE8..0x003E0084: packed half pair and closing word.  The
        // two VFP loads happen before the add, exactly as in the original.
        const f32 second = ReadF32(object, record_dff3c::kSecondValue);
        const f32 third = ReadF32(object, record_dff3c::kThirdValue);
        const u32 sum_half = ToHalf(second + third);
        const u32 negated_half = ToHalf(-second);
        *cursor++ = sum_half | (negated_half << 16);
        *cursor++ = record_dff3c::kFixedWord1;
    }

    // 0x003E0088..0x003E00A8: return the cursor or forward to 0x0022673C.
    if (submit == 0) {
        return reinterpret_cast<u32>(cursor);
    }
    const u32 continuation =
        ReadU32(object, record_dff3c::kObjectPointer) + record_dff3c::kTailBias;
    return func_0022673c(continuation, cursor, 1);
}

// ---------------------------------------------------------------------------
// 0x00297C9C -- preset the map-interface record block owned by the object
// published through 0x00447A78 (`g_MapIfWork` in include/engine/map_runtime.h).
//
// ARM 0x00297C9C..0x00297E2F: 92 instructions, 36 trailing constant-pool bytes.
// No calls, no indirect branches, no stack arguments.
//
// Record contract recovered from the addressing (`add r0, r2, r0, lsl #2` after
// `mul r0, r0, #0x65`, then `strb r1, [r0, #0x1d0]!`):
//   * 0x00447A78 holds a pointer.  The routine dereferences it once and never
//     reads the incoming r0, so the caller's argument is dead.
//   * A record is 0x194 (404) bytes.  Record i of the sweep lives at
//     base + i*404 + 0x1D0; the `cmp r3,#0x80` / `blt` loop runs i = 0..0x7F,
//     covering +0x1D0..+0xCBD0.
//   * The element at +0x03C is also exactly 0x194 bytes long (+0x3C + 0x194 =
//     +0x1D0) and receives the same field offsets with different values, so the
//     region is 129 contiguous records whose first element is a distinct preset.
//   * Widths: +0x00, +0x40, +0x41, +0x42 and +0x4C are byte stores, +0x0C,
//     +0x28, +0x2A and +0x2C are halfword stores, +0x30/+0x34/+0x38/+0x3C,
//     +0x48, +0x5C..+0x80 and +0x8C..+0xBC are VFP singles, everything else is
//     a 32-bit word store.
//   * The 128 swept records receive 700/300/2500 at +0x34/+0x38/+0x3C,
//     1150 at +0x5C and +0x68, 150 at +0x60 and +0x6C, 25 at +0x78/+0x7C,
//     0xFFFFFFFF at +0x18 and +0x80, and 0 everywhere else it touches.
//   * The +0x3C element instead receives 50 at +0x78/+0x7C, 0 at +0x5C..+0x74
//     and +0x30, 0xFFFFFFFF at +0x18 and +0x80, and leaves the remaining record
//     fields at their previous contents (only the listed fields are written).
//   * The `stm` at 0x00297E00 copies the just-stored zero bits of +0x5C/+0x60
//     (and a VFP zero) into +0x68/+0x6C/+0x70; the three stores are plain zero.
//   * Only r4 is callee-saved (`str r4, [sp, #-4]!` / `pop {r4}`).  The final
//     `ldm r0, {r0, r3}` reloads the zeroed +0x5C word, so the register image
//     returns r0 = 0; no reconstructed caller consumes that value.
// ---------------------------------------------------------------------------
namespace func_297c9c {

constexpr u32 kMapIfWork = 0x00447A78;  // pointer to the host block (0x00297C9C)
constexpr u32 kRecordCount = 0x80;      // `mov r4,#0x65`, `cmp r3,#0x80`
constexpr u32 kRecordSize = 0x194;      // 0x65 words; +0x3C + 0x194 = +0x1D0
constexpr u32 kRecordBase = 0x1D0;      // `strb r1, [r0, #0x1d0]!`
constexpr u32 kPresetBase = 0x03C;      // `strb r1, [r2, #0x3c]!`

constexpr f32 kZero = 0.0f;             // literal 0x00000000 (0x00297E1C)
constexpr f32 kValue25 = 25.0f;         // literal 0x41C80000 (0x00297E20)
constexpr f32 kValue50 = 50.0f;         // literal 0x42480000 (0x00297E2C)
constexpr f32 kValue150 = 150.0f;       // literal 0x43160000 (0x00297E28)
constexpr f32 kValue300 = 300.0f;       // literal 0x43960000 (0x00297E14)
constexpr f32 kValue700 = 700.0f;       // literal 0x442F0000 (0x00297E10)
constexpr f32 kValue1150 = 1150.0f;     // literal 0x448FC000 (0x00297E24)
constexpr f32 kValue2500 = 2500.0f;     // literal 0x451C4000 (0x00297E18)
constexpr u32 kUnset = 0xFFFFFFFFu;     // `mvn ip, #0` (0x00297CCC)

// 0x194-byte record.  Only the offsets the init code proves are named.
struct MapIfRecord {
    u8  field_000;           // +0x000: strb 0 (sweep and preset)
    u8  pad_001[0x03];
    u32 field_004;           // +0x004: str 0 (sweep only)
    u32 field_008;           // +0x008: str 0 (sweep only)
    u16 field_00c;           // +0x00C: strh 0 (sweep only)
    u8  pad_00e[0x02];
    u32 field_010;           // +0x010: str 0 (sweep and preset)
    u32 field_014;           // +0x014: str 0 (sweep and preset)
    u32 field_018;           // +0x018: str 0xFFFFFFFF (sweep and preset)
    u32 field_01c;           // +0x01C: str 0 (sweep and preset)
    u8  pad_020[0x08];
    u16 field_028;           // +0x028: strh 0 (sweep only)
    u16 field_02a;           // +0x02A: strh 0 (sweep only)
    u16 field_02c;           // +0x02C: strh 0 (sweep only)
    u8  pad_02e[0x02];
    f32 field_030;           // +0x030: 0 (sweep and preset)
    f32 field_034;           // +0x034: 700 (sweep only)
    f32 field_038;           // +0x038: 300 (sweep only)
    f32 field_03c;           // +0x03C: 2500 (sweep only)
    u8  field_040;           // +0x040: strb 0 (sweep and preset)
    u8  field_041;           // +0x041: strb 0 (sweep and preset)
    u8  field_042;           // +0x042: strb 0 (sweep only)
    u8  pad_043[0x01];
    u32 field_044;           // +0x044: str 0 (sweep only)
    f32 field_048;           // +0x048: 0 (sweep only)
    u8  field_04c;           // +0x04C: strb 0 (sweep only)
    u8  pad_04d[0x0f];
    f32 field_05c;           // +0x05C: 1150 sweep, 0 preset
    f32 field_060;           // +0x060: 150 sweep, 0 preset
    f32 field_064;           // +0x064: 0 (sweep and preset)
    f32 field_068;           // +0x068: 1150 sweep, 0 preset
    f32 field_06c;           // +0x06C: 150 sweep, 0 preset
    f32 field_070;           // +0x070: 0 (sweep and preset)
    f32 field_074;           // +0x074: 0 (sweep and preset)
    f32 field_078;           // +0x078: 25 sweep, 50 preset
    f32 field_07c;           // +0x07C: 25 sweep, 50 preset
    u32 field_080;           // +0x080: 0xFFFFFFFF (sweep and preset)
    u8  pad_084[0x08];
    f32 field_08c;           // +0x08C: 0 (sweep only)
    f32 field_090;           // +0x090: 0 (sweep only)
    f32 field_094;           // +0x094: 0 (sweep only)
    f32 field_098;           // +0x098: 0 (sweep only)
    f32 field_09c;           // +0x09C: 0 (sweep only)
    f32 field_0a0;           // +0x0A0: 0 (sweep only)
    f32 field_0a4;           // +0x0A4: 0 (sweep only)
    f32 field_0a8;           // +0x0A8: 0 (sweep only)
    f32 field_0ac;           // +0x0AC: 0 (sweep only)
    f32 field_0b0;           // +0x0B0: 0 (sweep only)
    f32 field_0b4;           // +0x0B4: 0 (sweep only)
    f32 field_0b8;           // +0x0B8: 0 (sweep only)
    f32 field_0bc;           // +0x0BC: 0 (sweep only)
    u8  pad_0c0[0xc4];
    u32 field_184;           // +0x184: str 0 (sweep only)
    u32 field_188;           // +0x188: str 0 (sweep only)
    u32 field_18c;           // +0x18C: str 0 (sweep only)
    u32 field_190;           // +0x190: str 0 (sweep and preset)
};
static_assert(offsetof(MapIfRecord, field_004) == 0x004);
static_assert(offsetof(MapIfRecord, field_00c) == 0x00C);
static_assert(offsetof(MapIfRecord, field_010) == 0x010);
static_assert(offsetof(MapIfRecord, field_018) == 0x018);
static_assert(offsetof(MapIfRecord, field_028) == 0x028);
static_assert(offsetof(MapIfRecord, field_030) == 0x030);
static_assert(offsetof(MapIfRecord, field_034) == 0x034);
static_assert(offsetof(MapIfRecord, field_040) == 0x040);
static_assert(offsetof(MapIfRecord, field_042) == 0x042);
static_assert(offsetof(MapIfRecord, field_044) == 0x044);
static_assert(offsetof(MapIfRecord, field_048) == 0x048);
static_assert(offsetof(MapIfRecord, field_04c) == 0x04C);
static_assert(offsetof(MapIfRecord, field_05c) == 0x05C);
static_assert(offsetof(MapIfRecord, field_080) == 0x080);
static_assert(offsetof(MapIfRecord, field_08c) == 0x08C);
static_assert(offsetof(MapIfRecord, field_0bc) == 0x0BC);
static_assert(offsetof(MapIfRecord, field_184) == 0x184);
static_assert(offsetof(MapIfRecord, field_190) == 0x190);
static_assert(sizeof(MapIfRecord) == kRecordSize);

// Observed prefix of the host object: one 0x194-byte preset element at +0x3C
// followed by the 0x80 swept elements at +0x1D0 (ending at +0xCBD0, the
// `field_cbd0` marker in include/engine/map_runtime.h).
struct MapIfRecordBlock {
    u8 pad_000[kPresetBase];
    MapIfRecord preset;
    MapIfRecord records[kRecordCount];
};
static_assert(offsetof(MapIfRecordBlock, preset) == kPresetBase);
static_assert(offsetof(MapIfRecordBlock, records) == kRecordBase);
static_assert(sizeof(MapIfRecordBlock) == 0xCBD0);

}  // namespace func_297c9c

// DECOMP_FUNC(0x00297c9c, 404)
extern "C" u32 script_vm_func_00297c9c() {
    using namespace func_297c9c;

    MapIfRecordBlock* const host =
        *reinterpret_cast<MapIfRecordBlock**>(kMapIfWork);

    // 0x00297CD0..0x00297DA8: the 0x80 swept records.  Store order follows the
    // listing; the fields of one record never overlap, so the final image is
    // independent of that order.
    for (s32 index = 0; index < static_cast<s32>(kRecordCount); ++index) {
        MapIfRecord& record = host->records[index];
        record.field_000 = 0;                    // 0x00297CE8
        record.field_004 = 0;                    // 0x00297CF0
        record.field_008 = 0;                    // 0x00297CF4
        record.field_00c = 0;                    // 0x00297CF8
        record.field_028 = 0;                    // 0x00297CFC
        record.field_02a = 0;                    // 0x00297D00
        record.field_02c = 0;                    // 0x00297D04
        record.field_034 = kValue700;             // 0x00297D08
        record.field_038 = kValue300;             // 0x00297D0C
        record.field_03c = kValue2500;            // 0x00297D10
        record.field_040 = 0;                    // 0x00297D14
        record.field_010 = 0;                    // 0x00297D18
        record.field_190 = 0;                    // 0x00297D1C
        record.field_014 = 0;                    // 0x00297D20
        record.field_018 = kUnset;               // 0x00297D20
        record.field_01c = 0;                    // 0x00297D24
        record.field_030 = kZero;                // 0x00297D28
        record.field_078 = kValue25;              // 0x00297D2C
        record.field_07c = kValue25;              // 0x00297D30
        record.field_080 = kUnset;               // 0x00297D34
        record.field_08c = kZero;                // 0x00297D38
        record.field_041 = 0;                    // 0x00297D3C
        record.field_05c = kValue1150;            // 0x00297D40
        record.field_042 = 0;                    // 0x00297D44
        record.field_044 = 0;                    // 0x00297D48
        record.field_048 = kZero;                // 0x00297D4C
        record.field_060 = kValue150;             // 0x00297D50
        record.field_064 = kZero;                // 0x00297D54
        record.field_04c = 0;                    // 0x00297D58
        record.field_074 = kZero;                // 0x00297D5C
        record.field_090 = kZero;                // 0x00297D60
        record.field_094 = kZero;                // 0x00297D64
        record.field_098 = kZero;                // 0x00297D68
        record.field_09c = kZero;                // 0x00297D6C
        record.field_0a0 = kZero;                // 0x00297D70
        record.field_0a4 = kZero;                // 0x00297D74
        record.field_0a8 = kZero;                // 0x00297D78
        record.field_0ac = kZero;                // 0x00297D7C
        record.field_0b0 = kZero;                // 0x00297D80
        record.field_0b4 = kZero;                // 0x00297D84
        record.field_0b8 = kZero;                // 0x00297D88
        record.field_0bc = kZero;                // 0x00297D8C
        record.field_184 = 0;                    // 0x00297D94
        record.field_188 = 0;                    // 0x00297D98
        record.field_18c = 0;                    // 0x00297D9C
        record.field_068 = kValue1150;            // 0x00297DA4
        record.field_06c = kValue150;             // 0x00297DA4
        record.field_070 = kZero;                // 0x00297DA4
    }

    // 0x00297DAC..0x00297E00: the single +0x3C element.  Only the fields named
    // here are touched; the rest of the element keeps its prior contents.
    MapIfRecord& preset = host->preset;
    preset.field_000 = 0;                        // 0x00297DAC
    preset.field_040 = 0;                        // 0x00297DB4
    preset.field_018 = kUnset;                   // 0x00297DB8
    preset.field_05c = kZero;                    // 0x00297DBC
    preset.field_010 = 0;                        // 0x00297DC0
    preset.field_190 = 0;                        // 0x00297DC4
    preset.field_060 = kZero;                    // 0x00297DC8
    preset.field_064 = kZero;                    // 0x00297DCC
    preset.field_01c = 0;                        // 0x00297DD8
    preset.field_014 = 0;                        // 0x00297DE0
    preset.field_030 = kZero;                    // 0x00297DE4
    preset.field_078 = kValue50;                 // 0x00297DE8
    preset.field_07c = kValue50;                 // 0x00297DEC
    preset.field_080 = kUnset;                   // 0x00297DF0
    preset.field_041 = 0;                        // 0x00297DF4
    preset.field_074 = kZero;                    // 0x00297DF8
    preset.field_068 = kZero;                    // 0x00297E00
    preset.field_06c = kZero;                    // 0x00297E00
    preset.field_070 = kZero;                    // 0x00297E00

    return 0;
}

// DECOMP_FUNC(0x0032bc14, 404)
//
// Engine wait/step loop over the two global engine objects at 0x004C3AF8 and
// 0x004C3B20.  Each iteration probes the context object, compares the 64-bit
// value returned by 0x00351208 with the baseline stored at 0x0044D020+0x08
// (and with six times that baseline), runs the matching transition helpers,
// sleeps through 0x00351698 and exits when the accumulated flags are set or
// the context state is 1 or 7.
//
// Recovered contract (ARM 0x0032BC14..0x0032BDA7):
//   * r0 is caller-supplied and never read: the original overwrites it with
//     0x004C3AF8 before the first call.  The only caller (0x001DD5A8) passes
//     an unrelated per-frame counter in r0.
//   * r4 means "the byte at 0x0044D020 was nonzero in some iteration"; r5
//     means "the six-times-baseline check took its overdue (non-negative
//     high-word) path".  Both flags persist across loop iterations, and the
//     loop ends when either is set or the state word is 1 or 7.
//   * Return 1 only when r5 is set.  Otherwise 0x00350530 is called and 0 is
//     returned; r4 alone still forces the 0x00350530 call.
//   * All callee-saved registers are preserved; there are no stack arguments
//     and no indirect calls.
//
// The 12 trailing bytes at 0x0032BD9C are the literal pool read by `ldr`
// (0x0044D020, 0x004C3AF8, 0x004C3B20).

namespace engine_0032bc14 {

// Literal-pool constants (0x0032BD9C..0x0032BDA4).
constexpr u32 kStatusAddress = 0x0044D020;    // `ldrb r0, [r6]`
constexpr u32 kTaskObjectAddress = 0x004C3AF8;  // first/second stage object
constexpr u32 kContextAddress = 0x004C3B20;   // engine task context
constexpr u32 kBaselineOffset = 0x08;         // `ldrd r2, r3, [r6, #8]`
constexpr u32 kStateOffset = 0x0C;            // `ldr r0, [r0, #0xc]`
constexpr u32 kBaselineScale = 6;             // `mov r7, #6`

// The two globals are instruction literals, not parameters.
inline u8* Global(u32 address) {
    return reinterpret_cast<u8*>(static_cast<std::uintptr_t>(address));
}

// 64-bit baseline owned by the status block.  The original re-reads it with
// `ldrd` for each comparison; volatile keeps both loads distinct.
inline u64 LoadBaseline() {
    return *reinterpret_cast<const volatile u64*>(
        Global(kStatusAddress + kBaselineOffset));
}

// Context state word read after the per-iteration sleep call.
inline u32 LoadContextState() {
    return *reinterpret_cast<const volatile u32*>(
        Global(kContextAddress + kStateOffset));
}

}  // namespace engine_0032bc14

// Direct calls.  Return types record what the callees produce when the
// contract is known; results this caller ignores are left as void.
// 0x0034F878: nonzero when the task object's phase/timestamp state is ready.
// 0x00351028: nonzero when the context probe says the clock is suspended.
// 0x00351208: u64 remaining-time value, 0xFFFFFFFFFFFFFFFF when inactive.
// 0x00350EA8 / 0x00350A64: step-state predicates returning 0 or 1.
// 0x00351698: 16-byte sleeper wrapper; ignores r0, loads 0x0007A120 and
//             tail-calls 0x002BB490 with r1 = 0.
extern "C" s32 func_0034f878(void* object);
extern "C" void func_0011b558(void* object);
extern "C" s32 engine_func_0011b5e8(void* object);
extern "C" s32 engine_func_0011b6a8(void* object);
extern "C" void func_0011b590(void* object);
extern "C" s32 func_00351028(void* object);
extern "C" u64 func_00351208(void* object);
extern "C" void func_0034fe60(void* object);
extern "C" s32 func_00350ea8(void* object);
extern "C" s32 func_00350024(void* object);
extern "C" s32 func_00350a64(void* object);
extern "C" void func_0034f808(void* object);
extern "C" u32 engine_func_0034fc14(void* object);
extern "C" void engine_func_0034fdd8(void* object);
extern "C" void camp_func_00351040(void* object);
extern "C" void func_0034f840(void* object);
extern "C" void nn_sdk_func_00351698(void* object);
extern "C" void func_00350530(void* object);

extern "C" s32 engine_func_0032bc14(void) {
    namespace detail = engine_0032bc14;

    u8* const task_object = detail::Global(detail::kTaskObjectAddress);
    u8* const context = detail::Global(detail::kContextAddress);
    volatile u8* const status_byte = reinterpret_cast<volatile u8*>(
        detail::Global(detail::kStatusAddress));

    // r4 and r5; both survive loop iterations.
    bool status_seen = false;
    bool overdue = false;

    for (;;) {
        // 0x0032BC24..0x0032BC60: one-shot or repeated task-object start.
        if (func_0034f878(task_object) != 0) {
            func_0011b558(task_object);
            engine_func_0011b5e8(context);
            engine_func_0011b6a8(context);
            func_0011b590(task_object);
        }

        // 0x0032BC64..0x0032BCB4: suspended-context handling.  A nonzero
        // probe result skips the whole clock block.
        if (func_00351028(context) == 0) {
            const u64 now = func_00351208(context);
            const u64 baseline = detail::LoadBaseline();

            // Signed 64-bit `now < baseline` (subs/sbcs + blt).
            if (static_cast<s64>(now) < static_cast<s64>(baseline)) {
                if (func_00350ea8(context) != 0) {
                    func_00350024(context);
                }
            } else {
                func_0034fe60(context);
            }
        }

        // 0x0032BCC0..0x0032BD40: overdue check against baseline * 6.
        if (func_00350a64(context) != 0) {
            const u64 now = func_00351208(context);
            const u64 scaled =
                detail::LoadBaseline() * detail::kBaselineScale;

            // `umull`/`mla` build (baseline * 6) modulo 2^64 and the
            // following subs/sbcs/blt is a signed 64-bit comparison.
            if (static_cast<s64>(now) < static_cast<s64>(scaled)) {
                // 0x0032BD24 still tests r1, the high word of the time
                // value returned by 0x00351208: `sbcs r0, r1, r2` wrote the
                // difference into r0, so r1 keeps now's high word.
                if (static_cast<s32>(static_cast<u32>(now >> 32)) >= 0) {
                    overdue = true;
                    camp_func_00351040(context);
                    func_0034f840(task_object);
                }
            } else {
                func_0034f808(task_object);
                engine_func_0034fc14(context);
                engine_func_0034fdd8(context);
            }
        }

        // 0x0032BD44..0x0032BD60: latch the status byte, then sleep.
        if (*status_byte != 0) {
            status_seen = true;
        }
        nn_sdk_func_00351698(context);

        // 0x0032BD60..0x0032BD7C: state read after the sleep.
        const u32 state = detail::LoadContextState();
        if (overdue || status_seen || state == 7 || state == 1) {
            break;
        }
    }

    if (overdue) {
        return 1;
    }
    func_00350530(context);
    return 0;
}

// DECOMP_FUNC(0x00239dec, 408)
//
// Hashes a halfword-keyed record and submits the hash with the record to two
// UI lookup helpers.  The record at r3 holds {u32 seed; u32 count;
// const u16* values}: the hash starts at `seed ^ 0x075BCD15` and then mixes
// every halfword in ascending order with `hash = value ^ ror(hash, 5)`.
//
// Recovered contract (ARM 0x00239DEC..0x00239F77):
//   * r0-r2 are forwarded unchanged to 0x003FC300; r3 is the record pointer.
//   * The element count is materialised as `(s32)(count << 1) >> 1`: the
//     original computes `values + count*2 - values` at 0x00239E0C..0x00239E18
//     and then keeps that doubled value in r11/fp.  A non-positive derived
//     count mixes no elements; a positive count c mixes values[0..c-1].
//   * Each element is a zero-extended `ldrh`.  The halfword buffer and
//     `count*2` (the byte length) are passed in stack arguments 5 and 6, the
//     hash in stack argument 7 (r0-r3 stay context, arg1, arg2, record).
//   * A first-call result whose bit 31 is clear is returned unchanged.  A
//     negative result is returned unchanged unless its bits 10..17 equal 0x11
//     and its bits 0..9 equal 0x6F (the 0xC880446F status: level bit 31,
//     module 0x11, description 0x6F).
//   * Only for that distinguished status is the record hashed again (the
//     fields are re-read after the first call) and 0x003FC46C called with
//     context+0x28, a u32 scratch output, a 0x14-byte scratch output, the
//     record, and the same three stack arguments.
//   * Second-call result bit 31 clear => return 0xE0C04702.  Otherwise the
//     distinguished status => return 0xC8804471, and any other result is
//     returned unchanged.
namespace func_239dec {

constexpr u32 kSeedXor = 0x075BCD15;          // literal at 0x00239F78
constexpr u32 kContextOffset = 0x28;          // `add r0, sl, #0x28`
constexpr u32 kResultAfterSecondSuccess = 0xE0C04702;  // 0x00239F7C
constexpr u32 kResultAfterSecondFailure = 0xC8804471;  // 0x00239F80

// Status layout tested at 0x00239E98..0x00239EB0 and 0x00239F50..0x00239F68.
constexpr u32 kFailureLevel = 0x80000000;     // `ands r1, r0, #0x80000000`
constexpr u32 kModuleMask = 0x0003FC00;       // `and r1, r0, #0x3FC00`
constexpr u32 kModule11 = 0x00004400;         // `cmp r1, #0x11` after `lsr #0xA`
constexpr u32 kDescriptionMask = 0x000003FF;  // lsl #22 / lsr #22
constexpr u32 kDescription6F = 0x0000006F;    // `cmp r1, #0x6F`

// 12-byte record reached through r3 (0x00239E00..0x00239E0C).
struct Record {
    u32 seed;          // +0x00 (r3 from `ldm r3, {r3, lr}`)
    u32 count;         // +0x04 (lr / r5 on the second pass)
    const u16* values; // +0x08 (`ldr r6, [r3, #8]`)
};

}  // namespace func_239dec

// Direct calls; the callees are existing raw-ARM leaf bodies
// (src/engine/leaf_batch38_b.cpp).  Both take seven arguments: the three stack
// words are the hash, the halfword buffer and the byte length.
extern "C" u32 ui_func_003fc300(u32 context, u32 arg1, u32 arg2,
                                func_239dec::Record* record, u32 hash,
                                const u16* values, u32 byte_length);
extern "C" u32 ui_func_003fc46c(u32 context, u32* out_word, void* out_block,
                                func_239dec::Record* record, u32 hash,
                                const u16* values, u32 byte_length);

namespace {

// `add r0, r6, lr, lsl #1; sub fp, r0, r6; add/asr r0, r8, fp, asr #1`
// (0x00239E0C..0x00239E20 and 0x00239E5C): the doubled count is kept modulo
// 2^32 and then sign-shifted back, so only the low 31 bits of `count` decide
// how many elements are mixed.
s32 ElementCount(u32 count) {
    return static_cast<s32>(count << 1) >> 1;
}

// `lsl r0, lr, #1` / `lsl r1, r5, #1` (0x00239E70 and 0x00239F20).
u32 RecordByteLength(const func_239dec::Record& record) {
    return record.count << 1;
}

// Mix loop at 0x00239E24..0x00239E6C (first pass) and
// 0x00239ED4..0x00239F1C (second pass).  `ror #5` is `hash >> 5 | hash << 27`.
u32 HashRecord(const func_239dec::Record& record) {
    u32 hash = record.seed ^ func_239dec::kSeedXor;
    const s32 count = ElementCount(record.count);
    for (s32 i = 0; i < count; ++i) {
        const u32 value = record.values[i];  // zero-extended ldrh
        hash = value ^ ((hash >> 5) | (hash << 27));
    }
    return hash;
}

// Status test: `(r0 >> 10) & 0xFF == 0x11` followed by
// `(r0 << 22) >> 22 == 0x6F`, reached only when bit 31 is set.
bool IsDistinguishedFailure(u32 status) {
    return (status & func_239dec::kFailureLevel) != 0 &&
           (status & func_239dec::kModuleMask) == func_239dec::kModule11 &&
           (status & func_239dec::kDescriptionMask) ==
               func_239dec::kDescription6F;
}

}  // namespace

extern "C" u32 func_00239dec(u32 context, u32 arg1, u32 arg2,
                             func_239dec::Record* record) {
    // 0x00239E00..0x00239E8C: hash, then report context/arg1/arg2 plus the
    // record and the three stack arguments.
    const u32 first_hash = HashRecord(*record);
    const u32 first = ui_func_003fc300(
        context, arg1, arg2, record, first_hash, record->values,
        RecordByteLength(*record));

    // 0x00239E8C..0x00239EB0: success and every non-distinguished failure
    // return the helper result unchanged.
    if ((first & func_239dec::kFailureLevel) == 0) {
        return first;
    }
    if (!IsDistinguishedFailure(first)) {
        return first;
    }

    // 0x00239EB4..0x00239F3C: re-read the record, hash it again and call the
    // second helper with context+0x28 and two stack scratch outputs.
    const u32 second_hash = HashRecord(*record);
    u32 scratch_word;
    u32 scratch_block[5];
    const u32 second = ui_func_003fc46c(
        context + func_239dec::kContextOffset, &scratch_word, scratch_block,
        record, second_hash, record->values, RecordByteLength(*record));

    // 0x00239F40..0x00239F6C.
    if ((second & func_239dec::kFailureLevel) == 0) {
        return func_239dec::kResultAfterSecondSuccess;
    }
    if (!IsDistinguishedFailure(second)) {
        return second;
    }
    return func_239dec::kResultAfterSecondFailure;
}

// DECOMP_FUNC(0x00263ee4, 408)
//
// Builds one script-effect work record and registers its table slot.  Reached
// from the battle effect emitter 0x0027B8CC on the "BOX" path (0x0027C1F4)
// and on the remapped-type "NA" path (0x0027C0EC), and from several battle
// effect helpers.
//
// Recovered contract (ARM 0x00263EE4..0x00264068; the four literal words
// 0x00447A28, 0x004AFD64, +0.0f and 0x004A1264 follow at 0x0026406C):
//   * ABI: r0 = id, r1 = handle, r2 = kind pointer, r3 = type, then fifteen
//     stack words and seven VFP arguments s0..s6.  The prologue spills
//     r0-r3 and d0-d3, then re-reads r0/r1/r2 from the register save area
//     (0x00263FAC..0x00263FD8) while r3 is used directly.  Stack word n is
//     read at the entry value of r13 + 4*n; word 14 is at 0x002640A0.
//   * The work-record index is the pre-call value of the global count at
//     0x00447A2C.  Records are 0x8C bytes at 0x004AFD64 (140*index).
//   * 0x0021C598 (Btl_StatusEffectCalc) receives work+0x5C in r0 and, in the
//     original register image, work+0x08 in r1 and work+0x24 in r2.  Its body
//     overwrites r1-r3 before any read, so only r0 is an argument.  Its return
//     value indexes the 0x178-byte slot array at 0x004A1264 (47*index*8).
//   * The init order into the work record is exactly the store order below:
//     +0x08 = 2; +0x10/+0x0C/+0x14 = s3/s4/s5; +0x28 = type; +0x24 = 1;
//     +0x2C/+0x30/+0x34 = stack words 11/12/13 (raw s7/s8/s9 bits);
//     +0x38..+0x3D = bytes of stack words 2..7; +0x3E = u16 1;
//     +0x40 = work+0x08; +0x70 = work+0x24; +0x68 = work+0x44;
//     +0x44/+0x48/+0x4C = s0/s1/s2; +0x50/+0x58 = +0.0f; +0x54 = s6;
//     +0x64 = kind.
//   * 0x002526FC (slot allocator) receives r0 = id, r1 = stack word 0,
//     r2 = stack word 1, r3 = stack word 14 and s0..s3 = s0,s1,s2,s6.
//     The original leaves s4..s7 untouched; the callee reads only s0..s3.
//   * Slot stores, in original order: +0x124 = allocator return;
//     +0x16C = byte of stack word 8; the *previous* slot's +0x16D = byte of
//     stack word 9; +0x12C = id; +0x130 = handle; +0x134 = -1 (u32);
//     +0x15C = u16 0; +0x15E = u16 0xFFFF; +0x164 = 0;
//     +0x128 = byte of stack word 10; +0x16E = 0; +0x160 = u16 0;
//     +0x162 = u16 0.
//   * The global count is re-read after both calls, incremented by one and
//     stored back (0x00264050..0x00264058).
//   * Return: the first helper's result, both success and failure (r7).
namespace func_263ee4 {

constexpr u32 kEffectTable = 0x00447A28;  // literal 0x00447A28 (0x0026406C)
constexpr u32 kEffectCount = 0x00447A2C;  // `ldr/str [sb,#4]`
constexpr u32 kWorkBase = 0x004AFD64;     // literal 0x004AFD64 (0x00264070)
constexpr u32 kSlotBase = 0x004A1264;     // literal 0x004A1264 (0x00264078)
constexpr u32 kWorkStride = 0x8C;         // 7*index + 28*index, lsl #2
constexpr u32 kSlotStride = 0x178;        // 15*index + 32*index, lsl #3
constexpr f32 kZero = 0.0f;               // literal 0x00000000 (0x00264074)
constexpr u32 kSlotUnset = 0xFFFFFFFFu;   // `mvn ip,#0` (0x00264004)

// 0x8C-byte work record at 0x004AFD64 + 140*index.  Offsets are the only
// names the ARM evidence supports.
struct WorkRecord {
    u8 pad_000[0x08];
    u32 field_08;        // +0x08: constant 2
    f32 field_0C;        // +0x0C: s4
    f32 field_10;        // +0x10: s3
    f32 field_14;        // +0x14: s5
    u8 pad_018[0x0C];
    u32 field_24;        // +0x24: constant 1
    u32 field_28;        // +0x28: type (r3)
    f32 field_2C;        // +0x2C: stack word 11 bits
    f32 field_30;        // +0x30: stack word 12 bits
    f32 field_34;        // +0x34: stack word 13 bits
    u8 field_38;         // +0x38..+0x3D: stack words 2..7, one byte each
    u8 field_39;
    u8 field_3A;
    u8 field_3B;
    u8 field_3C;
    u8 field_3D;
    u16 field_3E;        // +0x3E: constant 1
    u32 field_40;        // +0x40: address of +0x08
    f32 field_44;        // +0x44: s0
    f32 field_48;        // +0x48: s1
    f32 field_4C;        // +0x4C: s2
    f32 field_50;        // +0x50: +0.0f
    f32 field_54;        // +0x54: s6
    f32 field_58;        // +0x58: +0.0f
    u8 pad_05C[0x08];
    u32 field_64;        // +0x64: kind (r2)
    u32 field_68;        // +0x68: address of +0x44
    u8 pad_06C[0x04];
    u32 field_70;        // +0x70: address of +0x24
    u8 pad_074[0x18];
};
static_assert(offsetof(WorkRecord, field_08) == 0x08);
static_assert(offsetof(WorkRecord, field_0C) == 0x0C);
static_assert(offsetof(WorkRecord, field_10) == 0x10);
static_assert(offsetof(WorkRecord, field_14) == 0x14);
static_assert(offsetof(WorkRecord, field_24) == 0x24);
static_assert(offsetof(WorkRecord, field_2C) == 0x2C);
static_assert(offsetof(WorkRecord, field_38) == 0x38);
static_assert(offsetof(WorkRecord, field_3E) == 0x3E);
static_assert(offsetof(WorkRecord, field_40) == 0x40);
static_assert(offsetof(WorkRecord, field_44) == 0x44);
static_assert(offsetof(WorkRecord, field_64) == 0x64);
static_assert(offsetof(WorkRecord, field_68) == 0x68);
static_assert(offsetof(WorkRecord, field_70) == 0x70);
static_assert(sizeof(WorkRecord) == 0x8C);

// 0x178-byte slot at 0x004A1264 + 376*index.
struct SlotRecord {
    u8 pad_000[0x124];
    u32 field_124;       // +0x124: allocator result
    u8 field_128;        // +0x128: stack word 10, low byte
    u8 pad_129[0x03];
    u32 field_12C;       // +0x12C: id
    u32 field_130;       // +0x130: handle
    u32 field_134;       // +0x134: 0xFFFFFFFF
    u8 pad_138[0x24];
    u16 field_15C;       // +0x15C: 0
    u16 field_15E;       // +0x15E: 0xFFFF
    u16 field_160;       // +0x160: 0
    u16 field_162;       // +0x162: 0
    u8 field_164;        // +0x164: 0
    u8 pad_165[0x07];
    u8 field_16C;        // +0x16C: stack word 8, low byte
    u8 field_16D;        // +0x16D: stack word 9, low byte (previous slot)
    u8 field_16E;        // +0x16E: 0
    u8 pad_16F[0x09];
};
static_assert(offsetof(SlotRecord, field_124) == 0x124);
static_assert(offsetof(SlotRecord, field_128) == 0x128);
static_assert(offsetof(SlotRecord, field_12C) == 0x12C);
static_assert(offsetof(SlotRecord, field_134) == 0x134);
static_assert(offsetof(SlotRecord, field_15C) == 0x15C);
static_assert(offsetof(SlotRecord, field_164) == 0x164);
static_assert(offsetof(SlotRecord, field_16C) == 0x16C);
static_assert(sizeof(SlotRecord) == 0x178);

// 0x00447A28: only the +0x04 count is touched here.
struct EffectTable {
    u32 reserved_00;
    u32 count_04;
};
static_assert(offsetof(EffectTable, count_04) == 0x04);

inline WorkRecord* WorkAt(u32 index) {
    return reinterpret_cast<WorkRecord*>(kWorkBase + index * kWorkStride);
}

inline SlotRecord* SlotAt(u32 index) {
    return reinterpret_cast<SlotRecord*>(kSlotBase + index * kSlotStride);
}

inline EffectTable* Table() {
    return reinterpret_cast<EffectTable*>(kEffectTable);
}

inline u32 AddressOf(const void* pointer) {
    return static_cast<u32>(reinterpret_cast<std::uintptr_t>(pointer));
}

}  // namespace func_263ee4

// 0x0021C598 = smt4::battle::Btl_StatusEffectCalc.  The established 3-argument
// declaration is kept so the reference resolves to the reconstructed body in
// src/battle/battle_ailment.cpp; its ARM body overwrites r1 and r2 before any
// read, so the two pointer values are register-image fidelity only.
namespace smt4::battle {
struct StatusAilmentWork;
s32 Btl_StatusEffectCalc(StatusAilmentWork* work, u32 incoming_ailment,
                         u32 luck_stat);
}  // namespace smt4::battle

// 0x002526FC: slot allocator; four core-register and four VFP arguments.
extern "C" s32 script_vm_func_002526fc(u32 arg0, u32 arg1, u32 arg2, u32 arg3,
                                       f32 f0, f32 f1, f32 f2, f32 f3);

extern "C" u32 script_vm_func_00263ee4(
    u32 id, u32 handle, u32 kind, u32 type,
    u32 stack0, u32 stack1, u32 stack2, u32 stack3, u32 stack4,
    u32 stack5, u32 stack6, u32 stack7, u32 stack8, u32 stack9,
    u32 stack10, u32 stack11, u32 stack12, u32 stack13, u32 stack14,
    f32 f0, f32 f1, f32 f2, f32 f3, f32 f4, f32 f5, f32 f6) {
    using namespace func_263ee4;

    // 0x00263F2C..0x00263F38: index the new work record with the count that
    // was live before either helper ran.
    const u32 old_count = Table()->count_04;
    WorkRecord* const work = WorkAt(old_count);

    // 0x00263F3C..0x00263FB0: field initialization, in store order.
    work->field_08 = 2;
    work->field_10 = f3;
    work->field_0C = f4;
    work->field_14 = f5;
    work->field_28 = type;
    work->field_24 = 1;
    work->field_2C = __builtin_bit_cast(f32, stack11);
    work->field_30 = __builtin_bit_cast(f32, stack12);
    work->field_34 = __builtin_bit_cast(f32, stack13);
    work->field_38 = static_cast<u8>(stack2);
    work->field_39 = static_cast<u8>(stack3);
    work->field_3A = static_cast<u8>(stack4);
    work->field_3B = static_cast<u8>(stack5);
    work->field_3C = static_cast<u8>(stack6);
    work->field_3D = static_cast<u8>(stack7);
    work->field_3E = 1;
    work->field_40 = AddressOf(&work->field_08);
    work->field_70 = AddressOf(&work->field_24);
    work->field_68 = AddressOf(&work->field_44);
    work->field_44 = f0;
    work->field_50 = kZero;
    work->field_54 = f6;
    work->field_58 = kZero;
    work->field_48 = f1;
    work->field_4C = f2;
    work->field_64 = kind;

    // 0x00263FB4..0x00263FE0: status-effect calculation on work+0x5C.  r1 and
    // r2 receive work+0x08 and work+0x24 exactly as the original leaves them.
    u8* const work_bytes = reinterpret_cast<u8*>(work);
    const s32 slot_index = smt4::battle::Btl_StatusEffectCalc(
        reinterpret_cast<smt4::battle::StatusAilmentWork*>(work_bytes + 0x5C),
        AddressOf(work_bytes + 0x08), AddressOf(work_bytes + 0x24));

    // 0x00263FE4..0x00264000: index the new and previous slot records.
    SlotRecord* const slot = SlotAt(static_cast<u32>(slot_index));
    SlotRecord* const previous = SlotAt(old_count);

    // 0x00263FD0..0x00263FE0: r0 = id, r1 = stack0, r2 = stack1,
    // r3 = stack14, s0..s3 = s0,s1,s2,s6.
    const s32 allocated = script_vm_func_002526fc(
        id, stack0, stack1, stack14, f0, f1, f2, f6);

    // 0x00264008..0x0026404C: slot stores, in original order.
    slot->field_124 = static_cast<u32>(allocated);
    slot->field_16C = static_cast<u8>(stack8);
    previous->field_16D = static_cast<u8>(stack9);
    slot->field_12C = id;
    slot->field_130 = handle;
    slot->field_134 = kSlotUnset;
    slot->field_15C = 0;
    slot->field_15E = 0xFFFFu;
    slot->field_164 = 0;
    slot->field_128 = static_cast<u8>(stack10);
    slot->field_16E = 0;
    slot->field_160 = 0;
    slot->field_162 = 0;

    // 0x00264050..0x00264058: re-read the count (a helper may have changed it)
    // and advance it modulo 2^32.
    ++Table()->count_04;
    return static_cast<u32>(slot_index);
}

// DECOMP_FUNC(0x0026a62c, 408)
//
// Rebuilds one of the three camp identifier lists selected by `mode` and hands
// the halfword count to the shared page/cursor setup helper.
//
// Recovered contract (ARM 0x0026A62C..0x0026A7AC):
//   * r0 is `mode`.  Only 0xB, 0xC and 0xD select a list; every other value
//     jumps to the epilogue at 0x0026A7A4.  r0 then still holds the work
//     pointer loaded at 0x0026A640, because that epilogue restores only
//     r4-r8/sb/pc.
//   * The work pointer is `*(void**)0x0043DA90`, the canonical
//     smt4::camp::g_CampWork.  The table/page bases are:
//       0xB: table = work + 0x147C, page = work + 0x00B0
//       0xC: table = work + 0x14F4, page = work + 0x0114
//       0xD: table = work + 0x1CC4, page = work + 0x0178
//   * 0x0026A66C..0x0026A674 rejects the derived pair when either 32-bit
//     address wrapped to zero (`cmp r6,#0` / `cmpne r8,#0`).
//   * Entries are zero-extended `strh` stores of the enumerated id at
//     table[count++], performed only after the mode-specific predicate passes.
//   * 0xB: ids 1..0x3C inclusive, predicate 0x0028EC78(id) != 0.  The bound is
//     the signed `ble` at 0x0026A6AC.
//   * 0xC: ids 0x3B7..0x47E inclusive, then 0x47F..0x79E inclusive.  Both
//     passes test 0x0028EC78(id) != 0; the first loop uses the signed `ble`
//     at 0x0026A6AC, the second the unsigned `bls` at 0x0026A72C.
//   * 0xD: ids 0x33F..0x3B6 inclusive, then 0x79F..0x802 inclusive.  The first
//     pass tests 0x0028EC78(id) != 0.  The second pass first calls 0x0028EC78
//     and, only when its result is non-zero, calls 0x0028FDE4(id) and stores
//     the id when that signed result is > 0 (`ble` at 0x0026A758).  The extra
//     call is kept even though 0x0028EC78 is normally its >0 normalization.
//   * A selected list always calls
//     0x0029FAE8(page, count, 0xB, 1, 1, 1): four register arguments and the
//     two stack words 1, 1 (0x0026A774..0x0026A790).
//   * The original then loads r0 = mode and tail-branches to 0x002831F0
//     (0x0026A798..0x0026A7A0).  We return that callee's r0 so the register
//     passthrough stays observable; callers of this routine ignore it.
namespace func_26a62c {

constexpr u32 kModeB = 0x0B;              // `cmp r0,#0xb` (0x0026A630)
constexpr u32 kModeC = 0x0C;              // `cmp sb,#0xc` (0x0026A648)
constexpr u32 kModeD = 0x0D;              // `cmp sb,#0xd` (0x0026A650)

constexpr u32 kTableB = 0x147C;           // 0x1400 + 0x7C (0x0026A6D4..E0)
constexpr u32 kPageB = 0x00B0;            // 0x0026A6E4
constexpr s32 kFirstB = 0x01;             // `mov r5,#1` (0x0026A6D8)
constexpr s32 kLastB = 0x3C;              // `mov r7,#0x3c` (0x0026A6DC)

constexpr u32 kTableC = 0x14F4;           // 0x1400 + 0xF4 (0x0026A6F0..F4)
constexpr u32 kPageC = 0x0114;            // 0x0026A6FC
constexpr u32 kFirstC = 0x3B7;            // literal 0x3B7 (0x0026A6EC)
constexpr u32 kLastCFirstPass = 0x47E;    // firstC + 0xC7 (0x0026A6F8)
constexpr u32 kFirstCSecondPass = 0x47F;  // literal 0x47F (0x0026A6B4)
constexpr u32 kLastCSecondPass = 0x79E;   // literal 0x79E (0x0026A6B8)

constexpr u32 kTableD = 0x1CC4;           // 0x1C00 + 0xC4 (0x0026A65C..60)
constexpr u32 kPageD = 0x0178;            // 0x178 (0x0026A668)
constexpr u32 kFirstD = 0x33F;            // literal 0x33F (0x0026A658)
constexpr u32 kLastDFirstPass = 0x3B6;    // firstD + 0x77 (0x0026A664)
constexpr u32 kFirstDSecondPass = 0x79F;  // literal 0x79F (0x0026A6C4)
constexpr u32 kLastDSecondPass = 0x802;   // firstD + 0x63 (0x0026A6C8)

constexpr s32 kPageRows = 0x0B;           // `mov r2,#0xb` (0x0026A784)
constexpr s32 kPageColumns = 1;           // `mov r3,#1` / r0=1 (0x0026A774..778)
constexpr s32 kPageWrapRow = 1;           // `str r0,[sp]` (0x0026A77C)
constexpr s32 kPageRepeat = 1;            // `str r0,[sp,#4]` (0x0026A780)

}  // namespace func_26a62c

// The canonical work object (defined in src/camp/camp.cpp); only its address
// is used here.  The forward declaration keeps this translation unit free of
// the camp header's heavier UI dependencies.
namespace smt4 {
namespace camp {
struct CampWork;
extern CampWork* g_CampWork;
}  // namespace camp
}  // namespace smt4

// Direct calls.  0x0028EC78 returns a normalized non-zero result, 0x0028FDE4
// is its signed predicate, 0x0029FAE8 is the shared page/cursor setup and
// 0x002831F0 is the camp layout interpreter (canonically void; its r0 is
// forwarded by the original tail branch).
extern "C" u32 battle_func_0028ec78(u32 id);
extern "C" s32 camp_func_0028fde4(u32 id);
extern "C" u32 camp_func_0029fae8(volatile u8* cursor, s32 total_items,
                                  s32 visible_rows, s32 columns,
                                  s32 wrap_row, s32 repeat);
extern "C" u32 camp_func_002831f0(u32 layout_opcode);

extern "C" u32 camp_func_0026a62c(u32 mode) {
    const u32 work_address = reinterpret_cast<u32>(
        reinterpret_cast<uintptr_t>(smt4::camp::g_CampWork));
    u8* const work = reinterpret_cast<u8*>(work_address);

    // 0x0026A630..0x0026A654: dispatch.  The derived addresses are compared
    // before any table access, exactly like the r6/r8 zero test.
    u32 table_offset;
    u32 page_offset;
    switch (mode) {
    case func_26a62c::kModeB:
        table_offset = func_26a62c::kTableB;
        page_offset = func_26a62c::kPageB;
        break;
    case func_26a62c::kModeC:
        table_offset = func_26a62c::kTableC;
        page_offset = func_26a62c::kPageC;
        break;
    case func_26a62c::kModeD:
        table_offset = func_26a62c::kTableD;
        page_offset = func_26a62c::kPageD;
        break;
    default:
        return work_address;
    }

    const u32 table_address = work_address + table_offset;
    const u32 page_address = work_address + page_offset;
    if (table_address == 0 || page_address == 0) {
        return work_address;
    }

    u16* const table = reinterpret_cast<u16*>(work + table_offset);
    s32 count = 0;

    // 0x0026A678..0x0026A6AC: first pass.  Signed `ble` bound.
    if (mode == func_26a62c::kModeB) {
        for (s32 id = func_26a62c::kFirstB;
             id <= func_26a62c::kLastB; ++id) {
            if (battle_func_0028ec78(static_cast<u32>(id)) != 0) {
                table[count++] = static_cast<u16>(id);
            }
        }
    } else {
        const s32 first = static_cast<s32>(
            mode == func_26a62c::kModeC ? func_26a62c::kFirstC
                                        : func_26a62c::kFirstD);
        const s32 last = static_cast<s32>(
            mode == func_26a62c::kModeC ? func_26a62c::kLastCFirstPass
                                        : func_26a62c::kLastDFirstPass);
        for (s32 id = first; id <= last; ++id) {
            if (battle_func_0028ec78(static_cast<u32>(id)) != 0) {
                table[count++] = static_cast<u16>(id);
            }
        }
    }

    // 0x0026A6B0..0x0026A6D0: select the optional second pass.  0xB has none.
    if (mode == func_26a62c::kModeC) {
        // 0x0026A704..0x0026A72C: unsigned `bls` bound.
        for (u32 id = func_26a62c::kFirstCSecondPass;
             id <= func_26a62c::kLastCSecondPass; ++id) {
            if (battle_func_0028ec78(id) != 0) {
                table[count++] = static_cast<u16>(id);
            }
        }
    } else if (mode == func_26a62c::kModeD) {
        // 0x0026A734..0x0026A770: second predicate is gated by the first.
        for (u32 id = func_26a62c::kFirstDSecondPass;
             id <= func_26a62c::kLastDSecondPass; ++id) {
            if (battle_func_0028ec78(id) != 0 &&
                camp_func_0028fde4(id) > 0) {
                table[count++] = static_cast<u16>(id);
            }
        }
    }

    // 0x0026A774..0x0026A790: page/cursor setup with six arguments.
    camp_func_0029fae8(reinterpret_cast<volatile u8*>(page_address), count,
                       func_26a62c::kPageRows, func_26a62c::kPageColumns,
                       func_26a62c::kPageWrapRow, func_26a62c::kPageRepeat);

    // 0x0026A798..0x0026A7A0: r0 = mode, then tail branch to 0x002831F0.
    return camp_func_002831f0(mode);
}

// DECOMP_FUNC(0x00275ca0, 408)
//
// Applies the map-navi/player target's active flag to its two model slots and
// forwards the matching volume scale to both audio helpers.
//
// Recovered contract (ARM 0x00275CA0..0x00275E2B; the 12 literal bytes
// 0x004474D8, 1.0f, 0.0f follow at 0x00275E2C):
//   * `work = *(void**)0x004474D8`.  The global, the model pointer and the
//     model backend are re-read after every helper call, so a helper that
//     rewrites the chain is observed by the following accesses.
//   * For `work->model_0c` (+0x0C) and then `work->model_10` (+0x10):
//       - null model: nothing happens.
//       - `work->active` (+0x0A) != 0 and `model->flags` (+0x00) bit 1 set:
//         clear bit 1, store `model->backend->visual_node->visible` (+0x1F6)
//         = 1 and call 0x0029BDB4(backend, 1.0f), 0x0028C8D0(backend, 1.0f).
//       - `work->active` == 0 and bit 1 clear: set bit 1, store visible = 0
//         and call both helpers with 0.0f.
//       - a model already in the requested state is skipped without any store
//         or call (`cmp r2,#0` plus a conditional skip).
//   * The second model's final helper call is reached after `vpop {d8}` and
//     `pop {r4,r5,r6,lr}`, i.e. the original tail-branches to 0x0028C8D0.
//   * No arguments, `void` result.  r0 on return is incidental: all four static
//     callers overwrite it immediately, so it is not part of the contract.
namespace func_275ca0 {

constexpr u32 kRootPointerAddress = 0x004474D8;  // literal at 0x00275E2C
constexpr u32 kActiveOffset = 0x0A;              // `ldrb r1, [r1, #0xa]`
constexpr u32 kModelAOffset = 0x0C;              // `ldr r0, [r1, #0xc]`
constexpr u32 kModelBOffset = 0x10;              // `ldr r0, [r1, #0x10]`
constexpr u32 kModelFlagsOffset = 0x00;          // `ldr r1, [r0]`
constexpr u32 kModelBackendOffset = 0x08;        // `ldr r0, [r0, #8]`
constexpr u32 kBackendVisualNodeOffset = 0x2C;   // `ldr r0, [r0, #0x2c]`
constexpr u32 kVisualNodeVisibleOffset = 0x1F6;  // `strb r5, [r0, #0x1f6]`
constexpr u32 kHiddenFlag = 2;                   // `and r2, r1, #2`
constexpr float kShownVolume = 1.0f;             // s16, literal at 0x00275E30
constexpr float kHiddenVolume = 0.0f;            // s17, literal at 0x00275E34

struct VisualNode {
    u8 pad_000[kVisualNodeVisibleOffset];
    u8 visible_1f6;                              // +0x1F6: 1 shown, 0 hidden
};

struct ModelBackend {
    u8 pad_000[kBackendVisualNodeOffset];
    VisualNode* visual_node;                     // +0x2C
};

struct Model {
    u32 flags;                                   // +0x00, bit 1 = hidden
    u8 pad_004[4];
    ModelBackend* backend;                       // +0x08
};

struct Work {
    u8 pad_000[kActiveOffset];
    u8 active;                                   // +0x0A
    Model* model_0c;                             // +0x0C
    Model* model_10;                             // +0x10
};

inline Work* current_work() {
    return *reinterpret_cast<Work* const*>(kRootPointerAddress);
}

}  // namespace func_275ca0

// Direct calls: r0 = model backend, s0 = 1.0f/0.0f; both return void.
extern "C" void ui_func_0029bdb4(func_275ca0::ModelBackend* backend,
                                 float volume);
extern "C" void script_vm_func_0028c8d0(func_275ca0::ModelBackend* backend,
                                        float volume);

extern "C" void script_vm_func_00275ca0() {
    using namespace func_275ca0;

    // 0x00275CB8..0x00275D64: first model.
    {
        Work* const work = current_work();
        Model* const model = work->model_0c;
        if (model != nullptr) {
            const u8 active = work->active;
            const u32 flags = model->flags;
            if (active != 0) {
                if ((flags & kHiddenFlag) != 0) {
                    model->flags = flags & ~kHiddenFlag;
                    model->backend->visual_node->visible_1f6 = 1;
                    ui_func_0029bdb4(current_work()->model_0c->backend,
                                     kShownVolume);
                    script_vm_func_0028c8d0(current_work()->model_0c->backend,
                                            kShownVolume);
                }
            } else if ((flags & kHiddenFlag) == 0) {
                model->flags = flags | kHiddenFlag;
                model->backend->visual_node->visible_1f6 = 0;
                ui_func_0029bdb4(current_work()->model_0c->backend,
                                 kHiddenVolume);
                script_vm_func_0028c8d0(current_work()->model_0c->backend,
                                        kHiddenVolume);
            }
        }
    }

    // 0x00275D68..0x00275E20: second model; its last helper call is a tail
    // branch in the original.
    {
        Work* const work = current_work();
        Model* const model = work->model_10;
        if (model != nullptr) {
            const u8 active = work->active;
            const u32 flags = model->flags;
            if (active != 0) {
                if ((flags & kHiddenFlag) != 0) {
                    model->flags = flags & ~kHiddenFlag;
                    model->backend->visual_node->visible_1f6 = 1;
                    ui_func_0029bdb4(current_work()->model_10->backend,
                                     kShownVolume);
                    script_vm_func_0028c8d0(current_work()->model_10->backend,
                                            kShownVolume);
                    return;
                }
            } else if ((flags & kHiddenFlag) == 0) {
                model->flags = flags | kHiddenFlag;
                model->backend->visual_node->visible_1f6 = 0;
                ui_func_0029bdb4(current_work()->model_10->backend,
                                 kHiddenVolume);
                script_vm_func_0028c8d0(current_work()->model_10->backend,
                                        kHiddenVolume);
                return;
            }
        }
    }
}

// DECOMP_FUNC(0x003d58c4, 408)
//
// Recovered contract (ARM 0x003D58C4..0x003D5A50; the two literal words
// 0x00493524 and 0x0049353C follow at 0x003D5A54):
//   * `flags = self->field_634`; bit 20 (0x100000) gates the whole update.
//     When set the routine returns immediately: no store, no helper call and
//     no tail call.
//   * `t = ui_func_00227414(0, self->field_680, value)` (0x003D58E0).
//     0x00227414 mode 0 returns `(f32)value / (f32)denominator`, or +0.0f
//     when denominator == 0; the divide is signed 32-bit.  `field_680` is
//     re-read immediately before every one of the five calls.
//   * Every write is `base + (target - base) * t`, i.e. VFP `vsub.f32`
//     followed by `vmla.f32` (non-fused, two roundings), in this order:
//       0x00493518 -> 0x00493524                    -> self+0x658
//       self+0x5AC..0x5B4 <- self+0x5F0..0x5F8      -> self+0x6CC..0x6D4
//       0x00493530..0x00493538 -> 0x0049353C..0x00493544
//                                                   -> self+0x6E4..0x6EC
//     then, with a fresh `t` for each triple:
//       self+0x5E8 <- self+0x62C (base re-read after the call) -> +0x5A4
//       self+0x5EC <- self+0x630 (base re-read after the call) -> +0x6A8
//       self+0x5DC <- self+0x620 (base re-read after the call) -> +0x698
//   * The fifth 0x00227414 result (0x003D5A30) is discarded.
//   * Epilogue: `vpop {d8}`, `pop {r4,r5,r6,r7,r8,lr}` and an unconditional
//     tail branch to 0x003D74C4(self, value).  `r8` is saved but unused.
namespace func_3d58c4 {

constexpr u32 kFlagsOffset = 0x634;        // `ldr r0, [r0, #0x634]`
constexpr u32 kUpdateBlockedFlag = 0x100000;  // `tst r0, #0x100000`
constexpr u32 kDenominatorOffset = 0x680;  // `ldr r1, [r5, #0x680]`

// Literal-pool addresses of the four BSS tracks.  The pool words at
// 0x003D5A54/0x003D5A58 hold 0x00493524 and 0x0049353C; the "from" values
// are the same pointers minus 0xC.
constexpr u32 kTrackAScalarFrom = 0x00493518;
constexpr u32 kTrackAScalarTo = 0x00493524;
constexpr u32 kTrackBVectorFrom = 0x00493530;
constexpr u32 kTrackBVectorTo = 0x0049353C;

struct SceneState {
    u8 pad_000[0x5A4];
    f32 out_5a4;                 // interpolated from 0x5E8 toward 0x62C
    u8 pad_5a8[4];
    f32 from_5ac[3];             // three-lane target of the first vector lerp
    u8 pad_5b8[0x24];
    f32 to_5dc;                  // scalar target for +0x698
    u8 pad_5e0[8];
    f32 to_5e8;                  // scalar target for +0x5A4
    f32 to_5ec;                  // scalar target for +0x6A8
    f32 base_5f0[3];             // base of the first vector lerp
    u8 pad_5fc[0x24];
    f32 base_620;                // scalar base for +0x698
    u8 pad_624[8];
    f32 base_62c;                // scalar base for +0x5A4
    f32 base_630;                // scalar base for +0x6A8
    u32 flags_634;
    u8 pad_638[0x20];
    f32 out_658;                 // BSS scalar lerp result
    u8 pad_65c[0x24];
    s32 denominator_680;
    u8 pad_684[0x14];
    f32 out_698;
    u8 pad_69c[0xC];
    f32 out_6a8;
    u8 pad_6ac[0x20];
    f32 out_6cc;
    f32 out_6d0;
    f32 out_6d4;
    u8 pad_6d8[0xC];
    f32 out_6e4;                 // BSS three-lane lerp result
    f32 out_6e8;
    f32 out_6ec;
};

inline f32 read_global_f32(u32 address) {
    return *reinterpret_cast<const f32*>(address);
}

// The original uses the non-fused `vmla.f32` (multiply, round, add, round).
// Clang expands `base + delta * fraction` into `vmul` + `vadd`, which agrees
// for finite inputs but can select a different NaN payload when a signalling
// NaN is involved.  Emitting the instruction explicitly keeps the candidate
// bit-identical for every input, including NaNs.
__attribute__((always_inline)) inline f32 vmla_f32(f32 base, f32 addend,
                                                   f32 factor) {
    __asm__("vmla.f32 %0, %1, %2" : "+t"(base) : "t"(addend), "t"(factor));
    return base;
}

}  // namespace func_3d58c4

// 0x00227414: mode 0 computes (f32)value / (f32)denominator as a single
// precision quotient; a zero denominator yields +0.0f.  The routine also has
// modes 1 and 2, which this caller never selects.
extern "C" f32 ui_func_00227414(s32 mode, s32 denominator, s32 value);

// 0x003D74C4: tail continuation of the update.  Its result is not part of the
// caller-visible contract; the original reaches it with `b` after restoring
// every callee-saved register.
extern "C" void func_003d74c4(func_3d58c4::SceneState* self, s32 value);

extern "C" void func_003d58c4(func_3d58c4::SceneState* self, s32 value) {
    using namespace func_3d58c4;

    // 0x003D58D4..0x003D58DC: blocked updates perform no work at all.
    if ((self->flags_634 & kUpdateBlockedFlag) != 0) {
        return;
    }

    // 0x003D58E0..0x003D5920: BSS scalar track A, single lane.
    const f32 t0 = ui_func_00227414(0, self->denominator_680, value);
    const f32 track_a_from = read_global_f32(kTrackAScalarFrom);
    const f32 track_a_to = read_global_f32(kTrackAScalarTo);
    self->out_658 = vmla_f32(track_a_from, track_a_to - track_a_from, t0);

    // 0x003D5924..0x003D5970: three-lane lerp from +0x5AC toward +0x5F0.
    self->out_6cc =
        vmla_f32(self->base_5f0[0], self->from_5ac[0] - self->base_5f0[0], t0);
    self->out_6d0 =
        vmla_f32(self->base_5f0[1], self->from_5ac[1] - self->base_5f0[1], t0);
    self->out_6d4 =
        vmla_f32(self->base_5f0[2], self->from_5ac[2] - self->base_5f0[2], t0);

    // 0x003D5974..0x003D59B4: three-lane BSS track B.
    const f32 track_b_from_x = read_global_f32(kTrackBVectorFrom + 0x0);
    const f32 track_b_from_y = read_global_f32(kTrackBVectorFrom + 0x4);
    const f32 track_b_from_z = read_global_f32(kTrackBVectorFrom + 0x8);
    const f32 track_b_to_x = read_global_f32(kTrackBVectorTo + 0x0);
    const f32 track_b_to_y = read_global_f32(kTrackBVectorTo + 0x4);
    const f32 track_b_to_z = read_global_f32(kTrackBVectorTo + 0x8);
    self->out_6e4 = vmla_f32(track_b_from_x, track_b_to_x - track_b_from_x, t0);
    self->out_6e8 = vmla_f32(track_b_from_y, track_b_to_y - track_b_from_y, t0);
    self->out_6ec = vmla_f32(track_b_from_z, track_b_to_z - track_b_from_z, t0);

    // 0x003D59B8..0x003D59DC: the base at +0x62C is loaded after the call.
    {
        const f32 delta = self->to_5e8 - self->base_62c;
        const f32 t = ui_func_00227414(0, self->denominator_680, value);
        self->out_5a4 = vmla_f32(self->base_62c, delta, t);
    }

    // 0x003D59E0..0x003D5A04: the base at +0x630 is loaded after the call.
    {
        const f32 delta = self->to_5ec - self->base_630;
        const f32 t = ui_func_00227414(0, self->denominator_680, value);
        self->out_6a8 = vmla_f32(self->base_630, delta, t);
    }

    // 0x003D5A08..0x003D5A2C: the base at +0x620 is loaded after the call.
    {
        const f32 delta = self->to_5dc - self->base_620;
        const f32 t = ui_func_00227414(0, self->denominator_680, value);
        self->out_698 = vmla_f32(self->base_620, delta, t);
    }

    // 0x003D5A30..0x003D5A34: fifth fraction; the result is discarded.
    ui_func_00227414(0, self->denominator_680, value);

    // 0x003D5A38..0x003D5A48: restore and tail-branch to 0x003D74C4.
    func_003d74c4(self, value);
}

// DECOMP_FUNC(0x0015a620, 416)
//
// Recovered contract (ARM 0x0015A620..0x0015A79C plus seven literal words at
// 0x0015A7A4..0x0015A7BC: 1.0f, 0.0f, 255.0f, 0.5f, 0x000400E0, 0x000F00E1
// and the address of g_GpuCommandCursor):
//   * `state = *(GpuState**)(self + 0xA0)`; a null state returns immediately
//     without reading the entry, writing memory or calling anything.
//   * `entry = *(Entry**)(state + 0x08)`.  One 16-byte GPU command record is
//     appended at `g_GpuCommandCursor` (0x004652A0):
//         +0x0 = (entry->flags_18 & 2) ? 0x00010000 : 0
//         +0x4 = 0x000400E0
//         +0x8 = R | G << 8 | B << 16
//         +0xC = 0x000F00E1
//     The original stores +0xC first (`str r2, [ip, #0xc]`), then +0x0/+0x4/
//     +0x8 with one `stm ip, {r1, r3, lr}`, and finally stores cursor+0x10
//     back to 0x004652A0.  Every source word is loaded before the first store,
//     so a cursor aliasing the entry still observes the original values.
//   * The channels at `entry+0xB4/+0xB8/+0xBC/+0xC0` are each clamped to
//     [0.0f, 1.0f] with NaN passing through unchanged (`vcmpe`, `vmovgt`,
//     `vmovlo`) and converted by `vcvt.u32.f32` of
//     `vmla.f32(0.5f, channel, 255.0f)`, i.e. truncation of
//     `0.5 + 255 * channel`, then masked to a byte.  The fourth channel is
//     converted the same way but its byte is cleared again
//     (`bic lr, ip, #0xff000000`), so the record carries only the RGB bytes.
//     Its conversion is dead apart from VFP status-flag side effects.
//   * `ui_func_002a20a8(list, 0x17)` is a tail call: the original restores
//     r4-r6/lr and branches with r0 = `list` and r1 = 0x17.  `list` is the
//     self-relative pointer held at `entry+0xC4`,
//     `(u8*)&entry->rel_c4 + entry->rel_c4`, or null when that offset is zero.
//     0x002A20A8 records the pointer for slot 0x17 in the table at 0x004E9DC8
//     and appends a call-list command to the same command stream.
namespace func_15a620 {

constexpr u32 kStateOffset = 0xA0;  // `ldr r0, [r0, #0xa0]`
constexpr u32 kEntryOffset = 0x08;  // `ldr r1, [r0, #8]`

// Literal pool 0x0015A7A4..0x0015A7B0.
constexpr f32 kChannelMax = 1.0f;    // 0x3F800000
constexpr f32 kChannelMin = 0.0f;    // 0x00000000
constexpr f32 kChannelSpan = 255.0f; // 0x437F0000
constexpr f32 kRoundBias = 0.5f;     // 0x3F000000

// Literal pool 0x0015A7B4/0x0015A7B8 and the `ands`/`movne` pair at
// 0x0015A764..0x0015A768.
constexpr u32 kCommandHeaderRgb = 0x000400E0;
constexpr u32 kCommandHeaderEnd = 0x000F00E1;
constexpr u32 kEntryFlagBit = 2;
constexpr u32 kFlaggedLeadWord = 0x00010000;

// `mov r1, #0x17` before the tail branch.
constexpr u32 kCommandSlot = 0x17;

// `add r5, ip, #0x10`, stored back to 0x004652A0.
constexpr u32 kCommandWords = 4;

// `[self+0xA0]` points at a state object whose `+0x08` word is the entry.
struct GpuState {
    u8 pad_000[0x08];
    u8* entry_08;
};

// The entry fields read by this routine (all other bytes are untouched).
struct Entry {
    u8 pad_000[0x18];
    u32 flags_18;
    u8 pad_01c[0xB4 - 0x1C];
    f32 channel_b4;
    f32 channel_b8;
    f32 channel_bc;
    f32 channel_c0;
    u32 rel_c4;  // self-relative pointer, zero means null
};

// The object this routine is invoked with; only `+0xA0` is read.
struct Object {
    u8 pad_000[0xA0];
    GpuState* state_a0;
};

static_assert(offsetof(Object, state_a0) == kStateOffset);
static_assert(offsetof(GpuState, entry_08) == kEntryOffset);
static_assert(offsetof(Entry, flags_18) == 0x18);
static_assert(offsetof(Entry, channel_b4) == 0xB4);
static_assert(offsetof(Entry, rel_c4) == 0xC4);

// The original converts `0.5f + clamp(entry->channel) * 255.0f` with a single
// VMLA and `vcvt.u32.f32`.  Clang expands the plain expression into `vmul` +
// `vadd` (two roundings).  The intermediate value differs in the low bit for
// some inputs, but an enumeration of every float in the reachable [0, 1]
// clamp domain (plus the differential boundary cases in the test) shows the
// truncated byte is identical, so no inline assembly is needed.
inline u32 channel_to_byte(f32 value) {
    f32 clamped = value;
    if (clamped > kChannelMax) {
        clamped = kChannelMax;
    } else if (clamped < kChannelMin) {
        clamped = kChannelMin;
    }
    // NaN survives the clamp and converts to zero, exactly like VCVT.
    return static_cast<u8>(
        static_cast<u32>(kRoundBias + clamped * kChannelSpan));
}

}  // namespace func_15a620

// 0x004652A0: bump-allocated GPU command-stream cursor shared with
// 0x0015B1A4 and 0x002A20A8.
extern u32* g_GpuCommandCursor;

// 0x002A20A8: registers the command list for a slot and appends the call-list
// command.  Reached by a tail branch after every callee-saved register has
// been restored.
extern "C" void ui_func_002a20a8(void* list, u32 slot);

extern "C" void func_0015a620(void* self) {
    using namespace func_15a620;

    GpuState* const state = static_cast<Object*>(self)->state_a0;
    if (state == nullptr) {
        return;
    }

    Entry* const entry = reinterpret_cast<Entry*>(state->entry_08);

    // All loads precede the record stores in the original.
    const u32 lead =
        (entry->flags_18 & kEntryFlagBit) != 0 ? kFlaggedLeadWord : 0;
    const u32 red = channel_to_byte(entry->channel_b4);
    const u32 green = channel_to_byte(entry->channel_b8);
    const u32 blue = channel_to_byte(entry->channel_bc);
    const u32 alpha = channel_to_byte(entry->channel_c0);
    const u32 rgba = red | (green << 8) | (blue << 16) | (alpha << 24);
    const u32 offset = entry->rel_c4;
    void* const list =
        offset != 0
            ? reinterpret_cast<u8*>(&entry->rel_c4) + offset
            : nullptr;

    u32* const cursor = g_GpuCommandCursor;
    cursor[3] = kCommandHeaderEnd;
    cursor[0] = lead;
    cursor[1] = kCommandHeaderRgb;
    cursor[2] = rgba & 0x00FFFFFFu;
    g_GpuCommandCursor = cursor + kCommandWords;

    ui_func_002a20a8(list, kCommandSlot);
}

// DECOMP_FUNC(0x002f4804, 416)
//
// Recovered contract (ARM 0x002F4804..0x002F498C plus the five literal words
// at 0x002F4990..0x002F49A0: record base 0x004BE698, the twelve-entry color
// table 0x004049B4, the render-register global 0x0044EA00, 100.0f and the
// divide-by-twelve magic 0x2AAAAAAB):
//   * `count = *(s32*)0x004BF898` (base + 0x1200, the producer at 0x00277F9C
//     appends 0x20-byte records at 0x004BE698 and increments this counter).
//     A zero count returns without touching the render stack or calling
//     anything.
//   * Push a viewport command onto the render stack node at
//     `*0x0044EA00 + 0x124C`: `slot[count]` is the previous top, `count` is
//     incremented and `slot[count]` receives `ui_func_002c5f7c(5, 1)`
//     (0x1F51).  If the node's dirty byte is non-zero, or the previous top
//     differs from the new value, the node's flush callback at `+0x1C` is
//     invoked with the new value in r0 and the dirty byte is cleared.
//   * `ui_func_002c1d3c(*0x0044EA00, 0)` selects the render mode.
//   * For every record `i` while `i < *(s32*)0x004BF898` (signed bound,
//     re-read every iteration) draw one element with `func_0029705c`:
//       - the color word is `kColorTable[i % 12] | 0x70`, passed in r0..r3;
//       - the four vec3 arguments are
//         (rec+0x00, s16, rec+0x08), (rec+0x00, s16, rec+0x14),
//         (rec+0x0C, s16, rec+0x08), (rec+0x0C, s16, rec+0x14)
//         with `s16 = incoming_s0 + 100.0f`.
//   * Pop the render stack node: the same callback rule applies, and the
//     function leaves the popped value (or the callback result) in r0.
// Only the incoming float register s0 is live; r0..r3 are overwritten before
// they are read.  The single caller at 0x001FDD98 reaches this routine from a
// dispatcher with `s0 = *(f32*)(*r6 + 0x20)`.
namespace func_2f4804 {

// Absolute addresses in the pinned image.
constexpr u32 kRecordBaseAddress = 0x004BE698;   // 0x20-byte draw records
constexpr u32 kRecordCountAddress = 0x004BF898;  // kRecordBaseAddress + 0x1200
constexpr u32 kRecordStride = 0x20;

// 0x0044EA00 points at the render-register block; the viewport stack node
// starts at +0x124C.
constexpr u32 kRenderStackOffset = 0x124C;

// Literal pool 0x002F499C/0x002F49A0 and the `orr r0, r0, #0x70`.
constexpr f32 kVerticalStep = 100.0f;  // 0x42C80000
constexpr u32 kColorCommandBits = 0x70;

// 0x004049B4..0x004049E0: one color/format word per draw slot.
constexpr u32 kColorCount = 12;
constexpr u32 kColorTable[kColorCount] = {
    0xFF000000, 0x00FF0000, 0xFFFF0000, 0x0000FF00,
    0xFF00FF00, 0x00FFFF00, 0x80000000, 0x00800000,
    0xFF800000, 0x00008000, 0xFF008000, 0x00FF8000,
};

// `mov r0, #5` / `mov r1, #1` before the 0x002C5F7C call.
constexpr u32 kViewportCommand = 5;
constexpr u32 kViewportEnabled = 1;

// `mov r1, #0` before the 0x002C1D3C call.
constexpr u32 kRenderMode = 0;

// Render-stack node at render_base + 0x124C.  `slots` is addressed as a flat
// word array (`node + 8 + count*4`); the original has no bounds check, so the
// reconstruction indexes past the four visible slots exactly like the ARM code.
struct RenderStackNode {
    u32 count;          // +0x00
    u32 pad_004;        // +0x04
    u32 slots[4];       // +0x08..+0x17
    u8 dirty;           // +0x18
    u8 pad_019[3];
    u32 flush_cb;       // +0x1C, `blx r1` with the new value in r0
};

static_assert(offsetof(RenderStackNode, count) == 0x00);
static_assert(offsetof(RenderStackNode, slots) == 0x08);
static_assert(offsetof(RenderStackNode, dirty) == 0x18);
static_assert(offsetof(RenderStackNode, flush_cb) == 0x1C);

// `blx r1` with no null check: the original requires a non-null callback.
using FlushCallback = u32 (*)(u32 value);

inline RenderStackNode* render_stack(void* base) {
    return reinterpret_cast<RenderStackNode*>(
        static_cast<u8*>(base) + kRenderStackOffset);
}

inline s32 load_record_count() {
    return *reinterpret_cast<const s32*>(kRecordCountAddress);
}

}  // namespace func_2f4804

namespace smt4::engine {
extern void* g_RenderRegisterBase;  // 0x0044EA00
}

// 0x002C5F7C: builds the 0x1F51 viewport command word for (5, 1).
extern "C" u32 ui_func_002c5f7c(u32 kind, u32 enabled);

// 0x002C1D3C: selects the render mode on the render-register block.
extern "C" void ui_func_002c1d3c(void* base, u32 mode);

// 0x0029705C: submits one four-corner element.  r0..r3 carry the same color
// word; s0..s11 carry four vec3 corners.
extern "C" void func_0029705c(u32 color_a, u32 color_b, u32 color_c,
                              u32 color_d, f32 x0, f32 y0, f32 z0, f32 x1,
                              f32 y1, f32 z1, f32 x2, f32 y2, f32 z2, f32 x3,
                              f32 y3, f32 z3);

extern "C" u32 ui_func_002f4804(f32 vertical_offset) {
    using namespace func_2f4804;

    if (load_record_count() == 0) {
        return 0;
    }

    // The original captures the base before the viewport-command helper runs,
    // then re-reads the global for the render-mode call and again for the pop.
    void* const push_base = smt4::engine::g_RenderRegisterBase;
    const u32 pushed = ui_func_002c5f7c(kViewportCommand, kViewportEnabled);
    RenderStackNode* const push_node = render_stack(push_base);
    u32* const push_slots = push_node->slots;
    const u32 push_previous = push_slots[push_node->count];
    push_node->count = push_node->count + 1;
    push_slots[push_node->count] = pushed;
    if (push_node->dirty != 0 || push_previous != pushed) {
        reinterpret_cast<FlushCallback>(push_node->flush_cb)(pushed);
        push_node->dirty = 0;
    }

    ui_func_002c1d3c(smt4::engine::g_RenderRegisterBase, kRenderMode);

    const f32 draw_y = vertical_offset + kVerticalStep;

    // The count is re-read from 0x004BF898 every iteration, exactly like the
    // `ldr r0, [r6, #0x200]` in the loop tail, so a helper that grows the
    // record list extends the loop.
    for (s32 index = 0; index < load_record_count(); ++index) {
        const u8* const record = reinterpret_cast<const u8*>(
            kRecordBaseAddress + static_cast<u32>(index) * kRecordStride);
        const f32 x_lo = *reinterpret_cast<const f32*>(record + 0x00);
        const f32 z_lo = *reinterpret_cast<const f32*>(record + 0x08);
        const f32 z_hi = *reinterpret_cast<const f32*>(record + 0x0C);
        const f32 x_hi = *reinterpret_cast<const f32*>(record + 0x14);
        const u32 color =
            kColorTable[static_cast<u32>(index) % kColorCount] |
            kColorCommandBits;

        func_0029705c(color, color, color, color,
                      x_lo, draw_y, z_lo,
                      x_lo, draw_y, x_hi,
                      z_hi, draw_y, z_lo,
                      z_hi, draw_y, x_hi);
    }

    RenderStackNode* const pop_node =
        render_stack(smt4::engine::g_RenderRegisterBase);
    u32* const pop_slots = pop_node->slots;
    const u32 pop_count = pop_node->count;
    const u32 pop_previous = pop_slots[pop_count];
    pop_node->count = pop_count - 1;
    const u32 new_top = pop_slots[pop_count - 1];
    if (pop_node->dirty != 0 || pop_previous != new_top) {
        const u32 result =
            reinterpret_cast<FlushCallback>(pop_node->flush_cb)(new_top);
        pop_node->dirty = 0;
        return result;
    }
    return new_top;
}

// DECOMP_FUNC(0x001e2af0, 420)
//
// Recovered contract (ARM 0x001E2AF0..0x001E2C74 plus the seven literal words
// at 0x001E2C78..0x001E2C90: 0x0049F91C, 0x00447A98, 0x00000D5B, 0x00000708,
// 0x00001C20, 0x00447AB0 and 0.707f = 0x3F34FDF4):
//   * `context = engine_func_002c2b1c()` is the engine context; this routine
//     owns exactly one field of it, the signed advice index at `+0xD5B`.
//   * `script_vm_func_002bffac()` returns a profile byte.  Its value `| 4` is
//     forwarded to the final `script_vm_func_002bfdfc` call; the unmodified
//     byte is what the early-exit path leaves in r0.
//   * Three gates suppress the update entirely: the byte at
//     `0x0049F91C + 0x18` must be zero, the word reached through
//     `*(u32*)0x00447A98` must be zero, and event flag 0x16 must be set.
//     The first two checks happen before the flag lookup; the second one
//     re-reads `0x00447A98` later for the command writes, so a helper that
//     rewrites that global is observed.
//   * The nine 0x60-byte entries at 0x00447AB0 are `{u32 message_id,
//     Shift-JIS text[0x5C]}`; `entry[0]` is forwarded as the message id and
//     `entry+4` is stored into the pending command array.  The selected index
//     is never bounds-checked, exactly like the original's flat `index*0x60`.
//   * The index state machine advances one step per invocation, wrapping to 0
//     after entry 8.  Index 1 stays put while `camp_func_002a8a1c()` (a
//     populated-entry count) is non-zero.  Indices 5, 6 and 7 are gated by
//     `func_0025c1dc()` (elapsed seconds) around 1800 s, 3600 s and 7200 s;
//     the comparisons are unsigned, so a value below a gate wraps and falls
//     through to the next stage.  Index 8 compares two signed 16-bit record
//     fields and resets to 0 when the second is at least half the first.
//   * The pending command array receives `[0] = 2`, `[1] = 0`,
//     `[5] = entry+4`; words `[2..4]` are left untouched.
//   * No stack arguments, no indirect calls, no floating-point input.  The
//     epilogue is `pop {r4, r5, r6, r7, r8, pc}`.
//
// Callers ignore r0, but the original leaves a defined value there on every
// path (the 0x2BFFAC byte, the non-zero pending word, 0, or the next index).
// The reconstruction returns it so register-level differential tests are
// exact.
namespace func_1e2af0 {

// 0x0049F91C: shared map/script word block.  Only `+0x18` is read here.
constexpr u32 kUiBlockAddress = 0x0049F91C;
constexpr u32 kUiBlockHoldOffset = 0x18;

// 0x00447A98: pointer to the pending command word array.
constexpr u32 kCommandArrayPointerAddress = 0x00447A98;

// `str r2, [r0]`; `str r1, [r0, #4]`; `str r3, [r0, #0x14]`.
constexpr u32 kCommandKindIndex = 0;
constexpr u32 kCommandKind = 2;
constexpr u32 kCommandArgumentIndex = 1;
constexpr u32 kCommandDataIndex = 5;

// 0x00447AB0: nine advice entries, each a u32 message id followed by 0x5C
// bytes of Shift-JIS text.
constexpr u32 kAdviceTableAddress = 0x00447AB0;
constexpr u32 kAdviceEntryStride = 0x60;
constexpr u32 kAdviceEntryCount = 9;
constexpr u32 kAdviceTextOffset = 4;

// Engine context field owned by this routine (`ldrsb r4, [context, #0xD5B]`).
constexpr u32 kAdviceIndexOffset = 0xD5B;

// Elapsed-second gates: `ldr r1, =0x708` + `sub r0, r0, r1` + `cmp r0, r1`
// (state 5), `sub r0, r0, #0xE10` + `cmp r0, #0xE10` (state 6) and
// `ldr r1, =0x1C20` + `cmp r1, r0` (state 7).
constexpr u32 kSaveGateWindow = 0x0708;   // 1800 s
constexpr u32 kSaveGateSecond = 0x0E10;   // 3600 s
constexpr u32 kSaveGateThird = 0x1C20;    // 7200 s

// `mov r0, #0x20` before each camp_func_00290a38 call.
constexpr u32 kSaveDataEntryId = 0x20;

// `mov r0, #0x16` before the event-flag test.
constexpr u32 kAdviceEventFlag = 0x16;

// `mov r0, #1` before the 0x2BFDFC call.
constexpr u32 kAdviceMessageKind = 1;

// `orr r7, r0, #4`.
constexpr u32 kAdviceFlagsOr = 4;

// 0x3F34FDF4, loaded into s0 and copied to s1 for the 0x2BFDFC call.
constexpr f32 kAdviceCoefficient = 0.707f;

}  // namespace func_1e2af0

// 0x002C2B1C: engine context singleton (`*(*(0x0043E2A8 + 4)) + 0xAC8C`).
extern "C" u8* engine_func_002c2b1c(void);

// 0x002BFFAC: profile byte at `0x004C5634 + 0x1E4`.
extern "C" u32 script_vm_func_002bffac(void);

// 0x002BFF9C: profile byte at `0x004C5634 + 0x1E5`.
extern "C" u32 script_vm_func_002bff9c(void);

// 0x002C0BA8: event-flag test, non-zero when the flag bit is set.
extern "C" u32 script_vm_func_002c0ba8(u32 flag_id);

// 0x002A8A1C: count of leading non-negative s8 entries in a 24-entry table.
extern "C" u32 camp_func_002a8a1c(void);

// 0x00290A38: save-data entry word for `id`.
extern "C" u32 camp_func_00290a38(u32 id);

// 0x0025C1DC: elapsed seconds since the save timestamp (0 when in the future,
// -1 when no timestamp is armed).
extern "C" s32 func_0025c1dc(void);

// 0x0033426C: signed 16-bit field at `+0x1C` of the shared record.
extern "C" s32 script_vm_func_0033426c(void);

// 0x0028D5B4: signed 16-bit field at `+0x2A` of the shared record.
extern "C" s32 camp_func_0028d5b4(void);

// 0x002BFDFC: queues one script message record (kind, message id, byte, flags,
// two floats).
extern "C" u32 script_vm_func_002bfdfc(u32 kind, u32 message_id,
                                       u32 byte_argument, u32 flags,
                                       f32 coefficient_a, f32 coefficient_b);

extern "C" u32 script_vm_func_001e2af0(void) {
    using namespace func_1e2af0;

    u8* const context = engine_func_002c2b1c();

    // The profile byte is read before the suppression checks and its `| 4`
    // form is kept live across the whole body for the final message call.
    const u32 profile_byte = script_vm_func_002bffac();
    const u32 profile_flags = profile_byte | kAdviceFlagsOr;

    if (*reinterpret_cast<const u8*>(kUiBlockAddress + kUiBlockHoldOffset) !=
        0) {
        return profile_byte;
    }

    const u32 command_array_address =
        *reinterpret_cast<const u32*>(kCommandArrayPointerAddress);
    const u32 pending_command =
        *reinterpret_cast<const u32*>(command_array_address);
    if (pending_command != 0) {
        return pending_command;
    }

    if (script_vm_func_002c0ba8(kAdviceEventFlag) == 0) {
        return 0;
    }

    s32 index = *reinterpret_cast<const s8*>(context + kAdviceIndexOffset);

    switch (index) {
    case 1: {
        // `cmp r0, #1` / `movlt r4, #2`: an empty roster advances to entry 2,
        // otherwise entry 1 is shown and the state simply moves on.
        const s32 populated = static_cast<s32>(camp_func_002a8a1c());
        if (populated < 1) {
            index = 2;
        }
        break;
    }
    case 5:
        // The unsigned window `elapsed - 1800 <= 1800` keeps entry 5.
        if (camp_func_00290a38(kSaveDataEntryId) != 0) {
            const u32 elapsed = static_cast<u32>(func_0025c1dc());
            if (elapsed - kSaveGateWindow <= kSaveGateWindow) {
                break;
            }
        }
        index = 6;
        [[fallthrough]];
    case 6:
        // The unsigned window `elapsed - 3600 <= 3600` keeps entry 6.
        if (camp_func_00290a38(kSaveDataEntryId) != 0) {
            const u32 elapsed = static_cast<u32>(func_0025c1dc());
            if (elapsed - kSaveGateSecond <= kSaveGateSecond) {
                break;
            }
        }
        index = 7;
        [[fallthrough]];
    case 7:
        // `cmp r1, r0` with r1 = 0x1C20: entry 7 stays while elapsed >= 7200 s.
        if (camp_func_00290a38(kSaveDataEntryId) != 0) {
            const u32 elapsed = static_cast<u32>(func_0025c1dc());
            if (kSaveGateThird <= elapsed) {
                break;
            }
        }
        index = 8;
        [[fallthrough]];
    case 8: {
        // `add r2, r6, r6, lsr #31` / `cmp r0, r2, asr #1` is a signed
        // division of the first field by two, truncated toward zero.
        const s32 half_value = script_vm_func_0033426c();
        const s32 current_value = camp_func_0028d5b4();
        if (current_value >= half_value / 2) {
            index = 0;
        }
        break;
    }
    default:
        // Entries 0, 2, 3, 4 and out-of-range indices are emitted as-is.
        break;
    }

    // The pointer is re-read here; the earlier suppression check used a
    // separate load, so helper side effects on 0x00447A98 are observed.
    u32* const command_array = reinterpret_cast<u32*>(
        *reinterpret_cast<const u32*>(kCommandArrayPointerAddress));
    const u32 entry_address =
        kAdviceTableAddress + static_cast<u32>(index) * kAdviceEntryStride;
    const u32* const entry = reinterpret_cast<const u32*>(entry_address);

    command_array[kCommandKindIndex] = kCommandKind;
    command_array[kCommandArgumentIndex] = 0;
    command_array[kCommandDataIndex] = entry_address + kAdviceTextOffset;

    const u32 coefficient_argument = script_vm_func_002bff9c();
    script_vm_func_002bfdfc(kAdviceMessageKind, entry[0], coefficient_argument,
                            profile_flags, kAdviceCoefficient,
                            kAdviceCoefficient);

    s32 next_index = index + 1;
    if (next_index >= static_cast<s32>(kAdviceEntryCount)) {
        next_index = 0;
    }
    context[kAdviceIndexOffset] = static_cast<u8>(next_index);
    return static_cast<u32>(next_index);
}

// DECOMP_FUNC(0x001f6704, 420)
//
// Recovered contract (ARM 0x001F6704..0x001F688F plus the six literal words at
// 0x001F6890..0x001F68A7: 0.0f, 0x0044EA00, 0.5f, 2*pi = 0x40C90FDB,
// 1/18 = 0x3D638E39 and 128/pi = 0x4222F983):
//   * `object` is the sub-object selected by the only caller (0x002C7288):
//     `r0 = *(u32*)(parent + 0x24) + 0xC0` when the byte at `+0xCF` is set.
//     Only five fields are read:
//       - `+0x0C..+0x0F` is a four-byte RGBA quad.  The word is read with
//         `ldr`, byte-swapped with `rev`, its low byte cleared and the fourth
//         byte `l`d`r`b`'d from `+0x0F` OR'd back in.  After `rev` that byte
//         already *is* the low byte, so the value is `bswap32(word)` =
//         `R << 24 | G << 16 | B << 8 | A`.  The `bic`+`orr` pair is kept
//         verbatim below because it is what the caller's producer
//         (0x002C7090) and this reader agree on.
//       - `+0x14`/`+0x18` and `+0x1C`/`+0x20` are the two xy endpoints.
//     The ring uses the same colour with the alpha byte (the low byte of the
//     byte-swapped value) masked off.
//   * Three separate reads of the render-register global 0x0044EA00: the value
//     forwarded to `ui_func_002c1d3c(base, 0)`, the base used for the
//     render-stack *push* (read after that call and before the
//     `ui_func_002c5f7c(1, 0)` call) and the base used for the *pop* (read at
//     the end of the body).
//   * The push mirrors 0x002F4804: `slots[count]` is captured, `count` is
//     incremented, `slots[count]` receives the `ui_func_002c5f7c(1, 0)` word,
//     and when the node's dirty byte is set *or* the captured value differs
//     from the new one, the node's `+0x1C` callback runs with the new value in
//     r0 and the dirty byte is cleared.  The callback result is dead here
//     (r0 is overwritten by the next instruction).
//   * `dx = to_x - from_x`, `dy = to_y - from_y`, `mid = from + d * 0.5`,
//     `radius = dx * 0.5` (VSUB/VMLA/VMUL, each rounded separately).
//   * `func_0025760c()` flushes the queued sprite batch (`mov r0, #2` then a
//     tail branch to 0x002B03B8); it has no live arguments and its result is
//     not used.
//   * `ui_func_002575fc(rgba, x, y, z)` draws one point sprite: r0 carries the
//     colour and s0..s2 the position (the wrapper supplies s3 = s4 = 0.0f
//     before its tail branch to 0x002B0208).  The centre point is drawn with
//     the full colour at the midpoint, then a closed 19-vertex ring
//     (`i = 0..18`, signed bound 0x13) is drawn with the alpha-cleared colour:
//     `angle = i * 2*pi * (1/18) * (128/pi)`, x = `mid_x + radius*sin(angle)`,
//     y = `mid_y + radius*cos(angle)`, z = 0.  `ui_func_002b73a4` is the table
//     sine and `ui_func_002b740c` the table cosine; both take the angle in
//     units of one 256-entry table step, which is why the caller multiplies by
//     128/pi before the call.  The product chain is kept in the original order
//     (multiply, not a single combined constant) so every intermediate rounds
//     exactly like the ARM code.
//   * `ui_func_0025b988()` flushes the batch again (four-byte tail branch to
//     0x002B80D4 inside ui_func_002b8070); it also takes no arguments and its
//     result is discarded.
//   * Pop: `previous = slots[count]`, `count` is decremented, the new top is
//     `slots[count - 1]` (flat, unchecked like the ARM), and the same callback
//     rule applies.  The callback result, or the new top when no callback ran,
//     is left in r0 and returned.
//
// No stack arguments, no preserved-register surprises: the prologue saves
// r4-r8 plus s16-s23 (d8-d11) and the epilogue restores them, so `SP` at the
// pop is the entry `SP`.  The indirect calls are the render-stack callback
// (`blx r1`) only; it is never null-checked by the original.
namespace func_1f6704 {

// Literal pool 0x001F6890..0x001F68A7.
constexpr f32 kHalf = 0.5f;                 // 0x3F000000
constexpr f32 kZero = 0.0f;                 // 0x00000000
constexpr f32 kFullTurn = 6.2831855f;       // 0x40C90FDB, 2*pi
constexpr f32 kRingFraction = 0.055555556f; // 0x3D638E39, 1/18
constexpr f32 kTableScale = 40.743664f;     // 0x4222F983, 128/pi

// `cmp r4, #0x13` / `blt`: i = 0..18 closes the 18-segment ring.
constexpr s32 kRingSegments = 19;

// `add r4, r4, #0x1000` + `add r4, r4, #0x24C`: render-stack node offset.
constexpr u32 kRenderStackOffset = 0x124C;

// `bic r7, r6, #0xff`: the ring colour drops the alpha byte.
constexpr u32 kAlphaByteMask = 0xFFFFFF00u;

// `mov r0, #1` / `mov r1, #0` before the 0x002C5F7C call.
constexpr u32 kPushKind = 1;
constexpr u32 kPushEnabled = 0;

// `mov r1, #0` before the 0x002C1D3C call.
constexpr u32 kRenderMode = 0;

// The sub-object handed to this routine by 0x002C7288 (`parent + 0x24`, then
// `+0xC0`).  Only the fields read below are named.
struct BillboardParams {
    u8 pad_000[0x0C];
    u32 rgba_word_0c;  // `ldr r0, [r0, #0xc]`
    u8 pad_010[0x04];
    f32 from_x_14;  // `vldmia r5, {s16, s17}` with r5 = object + 0x14
    f32 from_y_18;
    f32 to_x_1c;  // `vldmia r0, {s1, s2}` with r0 = object + 0x1C
    f32 to_y_20;
};

static_assert(offsetof(BillboardParams, rgba_word_0c) == 0x0C);
static_assert(offsetof(BillboardParams, from_x_14) == 0x14);
static_assert(offsetof(BillboardParams, from_y_18) == 0x18);
static_assert(offsetof(BillboardParams, to_x_1c) == 0x1C);
static_assert(offsetof(BillboardParams, to_y_20) == 0x20);

// Render-stack node at 0x0044EA00 + 0x124C, same layout as the node consumed
// by 0x002F4804.  `slots` is a flat word array (`node + 8 + count*4`); the
// original has no bounds check, so the reconstruction indexes past the four
// visible slots exactly like the ARM code.
struct RenderStackNode {
    u32 count;       // +0x00
    u32 pad_004;     // +0x04
    u32 slots[4];    // +0x08..+0x17
    u8 dirty;        // +0x18
    u8 pad_019[3];
    u32 flush_cb;    // +0x1C, `blx r1` with the new value in r0
};

static_assert(offsetof(RenderStackNode, count) == 0x00);
static_assert(offsetof(RenderStackNode, slots) == 0x08);
static_assert(offsetof(RenderStackNode, dirty) == 0x18);
static_assert(offsetof(RenderStackNode, flush_cb) == 0x1C);

// `blx r1` with no null check: the original requires a non-null callback.
using FlushCallback = u32 (*)(u32 value);

inline RenderStackNode* render_stack(void* base) {
    return reinterpret_cast<RenderStackNode*>(
        static_cast<u8*>(base) + kRenderStackOffset);
}

// The closure of the ring in table steps: i * 2*pi * (1/18) * (128/pi).  The
// three multiplications happen in this order in the original (they appear
// twice, once before the sine call and once before the cosine call); one
// variable is enough because the sequence and its rounding are identical.
inline f32 ring_angle(s32 index) {
    return ((static_cast<f32>(index) * kFullTurn) * kRingFraction) *
           kTableScale;
}

}  // namespace func_1f6704

// 0x002C1D3C: selects the render mode (declared with 0x002F4804 above as
// `void ui_func_002c1d3c(void* base, u32 mode)`).
// 0x002C5F7C: builds the render-stack command word (declared above as
// `u32 ui_func_002c5f7c(u32 kind, u32 enabled)`).

// 0x0025760C: `mov r0, #2` then a tail branch to 0x002B03B8, which builds a
// 0x34-byte packet (first word = 2 << 8) and submits it through 0x002ADE34.
// It reads no caller register: r0 is set inside the wrapper and r1 = r0 << 8
// is derived from that constant, so the prototype takes no arguments.
extern "C" void func_0025760c(void);

// 0x002575FC: loads s3 = s4 = 0.0f and tail-branches to 0x002B0208 with the
// caller's r0 and s0..s2.  r0 is the colour, s0..s2 the position.
extern "C" void ui_func_002575fc(u32 rgba, f32 x, f32 y, f32 z);

// 0x002B73A4: table sine over 256 entries per turn; the argument is the turn
// angle scaled by 128/pi (one unit per table step).  Returns s0.
extern "C" f32 ui_func_002b73a4(f32 table_angle);

// 0x002B740C: table cosine with the same argument convention.  Returns s0.
extern "C" f32 ui_func_002b740c(f32 table_angle);

// 0x0025B988: four-byte tail branch to 0x002B80D4, a no-argument batch
// submit/flush path inside ui_func_002b8070.
extern "C" void ui_func_0025b988(void);

extern "C" u32 ui_func_001f6704(void* object) {
    using namespace func_1f6704;

    BillboardParams* const params =
        static_cast<BillboardParams*>(object);

    // The colour and the two endpoints are read before any helper runs.  The
    // byte at +0x0F is fetched separately (`ldrb r1, [r5, #3]`, r5 = object +
    // 0xC) and merged into the byte-swapped word.
    const u32 rgba_word = params->rgba_word_0c;
    const u32 rgba_byte_0f = static_cast<const u8*>(object)[0x0F];
    const u32 color = (__builtin_bswap32(rgba_word) & kAlphaByteMask) |
                      rgba_byte_0f;
    const u32 ring_color = color & kAlphaByteMask;

    ui_func_002c1d3c(smt4::engine::g_RenderRegisterBase, kRenderMode);

    // The push base is captured here, after the render-mode call and before
    // the command-word helper, which may itself rewrite 0x0044EA00.
    void* const push_base = smt4::engine::g_RenderRegisterBase;
    const u32 pushed = ui_func_002c5f7c(kPushKind, kPushEnabled);

    RenderStackNode* const push_node = render_stack(push_base);
    u32* const push_slots = push_node->slots;
    const u32 push_previous = push_slots[push_node->count];
    push_node->count = push_node->count + 1;
    push_slots[push_node->count] = pushed;
    if (push_node->dirty != 0 || push_previous != pushed) {
        reinterpret_cast<FlushCallback>(push_node->flush_cb)(pushed);
        push_node->dirty = 0;
    }

    // The two endpoints are only loaded here, after the push callback: a
    // helper that rewrites the object is observed, exactly like the ARM loads
    // at 0x001F6798 (`object + 0x1C`) and 0x001F67A0 (`object + 0x14`).
    const f32 to_x = params->to_x_1c;
    const f32 to_y = params->to_y_20;
    const f32 from_x = params->from_x_14;
    const f32 from_y = params->from_y_18;

    const f32 delta_x = to_x - from_x;
    const f32 delta_y = to_y - from_y;
    const f32 mid_x = from_x + delta_x * kHalf;
    const f32 mid_y = from_y + delta_y * kHalf;
    const f32 radius = delta_x * kHalf;

    func_0025760c();

    ui_func_002575fc(color, mid_x, mid_y, kZero);

    for (s32 index = 0; index < kRingSegments; ++index) {
        const f32 angle = ring_angle(index);
        const f32 sine = ui_func_002b73a4(angle);
        const f32 cosine = ui_func_002b740c(angle);
        ui_func_002575fc(ring_color, mid_x + radius * sine,
                         mid_y + radius * cosine, kZero);
    }

    ui_func_0025b988();

    // The pop re-reads 0x0044EA00; the node captured for the callback is the
    // one addressed by *this* read even if the callback switches the global.
    RenderStackNode* const pop_node =
        render_stack(smt4::engine::g_RenderRegisterBase);
    u32* const pop_slots = pop_node->slots;
    const u32 pop_count = pop_node->count;
    const u32 pop_previous = pop_slots[pop_count];
    pop_node->count = pop_count - 1;
    const u32 new_top = pop_slots[pop_count - 1];
    if (pop_node->dirty != 0 || pop_previous != new_top) {
        const u32 result =
            reinterpret_cast<FlushCallback>(pop_node->flush_cb)(new_top);
        pop_node->dirty = 0;
        return result;
    }
    return new_top;
}

// DECOMP_FUNC(0x002d8fac, 420)
// 104 ARM instructions through unconditional pop; 4 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_002d8fac() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d41f0, 0xe59f7194, 0xe5974004, 0xe5970008\n"
        ".word 0xe5941018, 0xe1510000, 0x0a00005f, 0xe5d41028\n"
        ".word 0xe3510000, 0x1a00005c, 0xe5d41355, 0xe3510000\n"
        ".word 0x1a000059, 0xe5840018, 0xe0800004, 0xe5d0034c\n"
        ".word 0xe3500000, 0x0a00004c, 0xe3a00001, 0xe5c40355\n"
        ".word 0xebff1497, 0xe3a00001, 0xebff16c2, 0xe3a00000\n"
        ".word 0xebff0258, 0xe5970008, 0xe5945350, 0xe3a0200e\n"
        ".word 0xe0840380, 0xe2806f93, 0xe590025e, 0xe2861030\n"
        ".word 0xe5850000, 0xe5960016, 0xe5850004, 0xe596001a\n"
        ".word 0xe5850008, 0xe1d601be, 0xe1c500bc, 0xe596003e\n"
        ".word 0xe585000e, 0xe5960042, 0xe5850012, 0xe5960046\n"
        ".word 0xe5850016, 0xe1d604ba, 0xe1c501ba, 0xe285001c\n"
        ".word 0xebff8fb9, 0xe1d602b4, 0xe1a01006, 0xe1c502ba\n"
        ".word 0xe1d602b6, 0xe1c502bc, 0xe5960020, 0xe5850030\n"
        ".word 0xe285004c, 0xebff99f5, 0xe5d6004c, 0xe5c50076\n"
        ".word 0xebff9ebc, 0xe2800054, 0xe1a01006, 0xebff99ef\n"
        ".word 0xe5940350, 0xebff04b3, 0xe5970008, 0xe0840380\n"
        ".word 0xe2900f93, 0x0a000003, 0xe5d00064, 0xe3500000\n"
        ".word 0x13a00001, 0xebfe49ce, 0xe3a00000, 0xebff0da2\n"
        ".word 0xe320f000, 0xe320f000, 0xebff7580, 0xe5941350\n"
        ".word 0xe3a0200e, 0xebff8f98, 0xe5940350, 0xe1d010b8\n"
        ".word 0xe3a00001, 0xebff01f4, 0xe5940350, 0xe1d010ba\n"
        ".word 0xe3a00002, 0xebff01f0, 0xe5940350, 0xe1d010b6\n"
        ".word 0xe8bd41f0, 0xe3a00000, 0xeaff01eb, 0xe3a00000\n"
        ".word 0xebff144b, 0xe3a00001, 0xe320f000, 0xebff1675\n"
        ".word 0xe8bd41f0, 0xe3a00000, 0xeaff020a, 0xe8bd81f0\n"
        ".word 0x0044de28\n"
    );
}

// DECOMP_FUNC(0x0030f760, 420)
// 100 ARM instructions through unconditional pop; 20 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_0030f760() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d43f0, 0xe59f0188, 0xe59f5180, 0xe2801090\n"
        ".word 0xed2d8b02, 0xe24dd034, 0xe89111de, 0xeeb08a40\n"
        ".word 0xe88d11de, 0xe28010b0, 0xe59000bc, 0xe891000e\n"
        ".word 0xe58d002c, 0xe28d0020, 0xe880000e, 0xe5950e00\n"
        ".word 0xe3500000, 0x0a00004e, 0xe59f6148, 0xe3a01001\n"
        ".word 0xe3a00005, 0xe5964000, 0xebfed9ef, 0xe2844a01\n"
        ".word 0xe2844f93, 0xe3a07000, 0xe5941000, 0xe2812001\n"
        ".word 0xe0843101, 0xe5931008, 0xe0843102, 0xe5842000\n"
        ".word 0xe5830008, 0xe5d42018, 0xe3520000, 0x01510000\n"
        ".word 0x0a000002, 0xe594101c, 0xe12fff31, 0xe5c47018\n"
        ".word 0xe5960000, 0xe3a01000, 0xebfec94b, 0xe5950e00\n"
        ".word 0xe3a04000, 0xe3500000, 0xda000020, 0xe59f90dc\n"
        ".word 0xed9f0a35, 0xe1a0800d, 0xee388a00, 0xe0640184\n"
        ".word 0xe0850100, 0xed900a00, 0xed901a02, 0xedd02a05\n"
        ".word 0xed903a03, 0xe0c01499, 0xeef05a62, 0xeeb05a48\n"
        ".word 0xeef04a43, 0xe1a010c0, 0xe0410fc0, 0xeeb04a41\n"
        ".word 0xe0400100, 0xeef03a48, 0xe0840100, 0xeeb02a48\n"
        ".word 0xe7980100, 0xeef01a40, 0xeef00a48, 0xe3800070\n"
        ".word 0xe1a03000, 0xe1a02003, 0xe1a01002, 0xebfe1df2\n"
        ".word 0xe5950e00, 0xe2844001, 0xe1500004, 0xcaffffe2\n"
        ".word 0xe5960000, 0xe2804a01, 0xe2844f93, 0xe5940000\n"
        ".word 0xe0841100, 0xe2400001, 0xe5911008, 0xe5840000\n"
        ".word 0xe0840100, 0xe5d42018, 0xe5900008, 0xe3520000\n"
        ".word 0x01510000, 0x0a000002, 0xe594101c, 0xe12fff31\n"
        ".word 0xe5c47018, 0xe28dd034, 0xecbd8b02, 0xe8bd83f0\n"
        ".word 0x004c2424, 0x004049b4, 0x0044ea00, 0x42c80000\n"
        ".word 0x2aaaaaab\n"
    );
}

// DECOMP_FUNC(0x00126480, 424)
// 100 ARM instructions through unconditional pop; 24 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_00126480() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d47f0, 0xe3e05000, 0xe1a08000, 0xe1a09002\n"
        ".word 0xe59f7178, 0xe1a06001, 0xed2d8b06, 0xe2870a01\n"
        ".word 0xeef08a40, 0xeeb08a60, 0xe5900204, 0xe1b04000\n"
        ".word 0x13e02000, 0x13a05000, 0x0a000051, 0xe0801105\n"
        ".word 0xe5911020, 0xe3510000, 0x0a000004, 0xe2855001\n"
        ".word 0xe3550008, 0xbafffff8, 0xe1a05002, 0xea000048\n"
        ".word 0xe3750001, 0x0a000046, 0xe59fa120, 0xe1a0000a\n"
        ".word 0xeb0664d9, 0xe3500000, 0xe320f000, 0x0a000040\n"
        ".word 0xe1a01008, 0xe1a0000a, 0xeb006d0c, 0xe3500000\n"
        ".word 0xe320f000, 0x0a00003a, 0xe1a00008, 0xeb066e88\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000034, 0xe0844105\n"
        ".word 0xe2841020, 0xe3a03000, 0xe1a02008, 0xe2870f61\n"
        ".word 0xeb065a2c, 0xe31000ff, 0xeddf9a32, 0x03a07001\n"
        ".word 0x13a07000, 0xe3560000, 0x0eb09a69, 0xed9faa2c\n"
        ".word 0x0a000009, 0xee006a10, 0xed9f1a2b, 0xeeb09a4a\n"
        ".word 0xeddf0a2a, 0xeeb80a40, 0xee300a41, 0xee009a20\n"
        ".word 0xee190a10, 0xe3500101, 0xcd9f9a25, 0xeeb00a69\n"
        ".word 0xe5940020, 0xe3a01000, 0xe3500000, 0x1b0659fc\n"
        ".word 0xeeb00a4a, 0xe5940020, 0xe3500000, 0x1d800a2e\n"
        ".word 0xeeb00a69, 0xe5940020, 0xe3500000, 0x1d800a2d\n"
        ".word 0xe5940020, 0xeeb00a49, 0xe3500000, 0x11a01009\n"
        ".word 0x1b0659ef, 0xeeb00a68, 0xe5940020, 0xe3500000\n"
        ".word 0x1d800a2e, 0xeeb00a48, 0xe5940020, 0xe3500000\n"
        ".word 0x1d800a2d, 0xe3570000, 0xe320f000, 0x1a000000\n"
        ".word 0xe3e05000, 0xecbd8b06, 0xe1a00005, 0xe8bd87f0\n"
        ".word 0x004e1f68, 0x3f800000, 0x00000000, 0x42800000\n"
        ".word 0x3c810204, 0x40000000\n"
    );
}

// DECOMP_FUNC(0x002bc3c8, 424)
// 98 ARM instructions through unconditional pop; 32 trailing data bytes.
extern "C" __attribute__((naked)) void battle_func_002bc3c8() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d41f0, 0xe59f617c, 0xe59f017c, 0xe596409c\n"
        ".word 0xe5901000, 0xe5942004, 0xe0412002, 0xe584200c\n"
        ".word 0xe5943014, 0xe1530002, 0x0a000055, 0xe59f315c\n"
        ".word 0xe3120008, 0x12821018, 0x1584100c, 0x1a00000a\n"
        ".word 0xe2822020, 0xe584200c, 0xe5932000, 0xe1510002\n"
        ".word 0x2a000005, 0xe59f5138, 0xe3a0c000, 0xe2817008\n"
        ".word 0xe5815004, 0xe581c000, 0xe5807000, 0xe5931000\n"
        ".word 0xe5902000, 0xe3a07001, 0xe1520001, 0x2a000003\n"
        ".word 0xe59fc110, 0xe2825008, 0xe8821080, 0xe5805000\n"
        ".word 0xe5902000, 0xe5931000, 0xe1520001, 0x2a000003\n"
        ".word 0xe59fc0f4, 0xe2825008, 0xe8821080, 0xe5805000\n"
        ".word 0xe5931000, 0xe5902000, 0xe1520001, 0x2a000004\n"
        ".word 0xe59f30d8, 0xe59fc0d8, 0xe2825008, 0xe8821008\n"
        ".word 0xe5805000, 0xe5941020, 0xe5940018, 0xe0611181\n"
        ".word 0xe0805101, 0xe5c57000, 0xe5940004, 0xe5941014\n"
        ".word 0xe0800001, 0xe5850004, 0xe594000c, 0xe5941014\n"
        ".word 0xe0400001, 0xe5850008, 0xe5940034, 0xe3500000\n"
        ".word 0x0a000002, 0xe1a01005, 0xe1a00004, 0xebffb8f1\n"
        ".word 0xe595000c, 0xe3c00002, 0xe585000c, 0xe5d4103d\n"
        ".word 0xe3510000, 0x13800001, 0x1585000c, 0xe594000c\n"
        ".word 0xe5840014, 0xebf9fa99, 0xe5940020, 0xe2800001\n"
        ".word 0xe5840020, 0xe59600a0, 0xe1500004, 0x1a000006\n"
        ".word 0xe5d60012, 0xe3500000, 0x0a000003, 0xe5d60011\n"
        ".word 0xe3500000, 0x05c67011, 0x0bfff82c, 0xe8bd41f0\n"
        ".word 0xeaf9fa8e, 0xe8bd81f0, 0x004c6290, 0x004652a0\n"
        ".word 0x004652a4, 0x0008025e, 0x000f0111, 0x000f0110\n"
        ".word 0x12345678, 0x000f0010\n"
    );
}

// DECOMP_FUNC(0x002e03ec, 424)
// 101 ARM instructions through unconditional pop; 20 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_002e03ec() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d47f0, 0xe59f018c, 0xe59f6184, 0xe2801030\n"
        ".word 0xed2d8b02, 0xe24dd030, 0xe891139e, 0xe2865b07\n"
        ".word 0xeeb08a40, 0xe88d139e, 0xe2801050, 0xe590005c\n"
        ".word 0xe891000e, 0xe58d002c, 0xe28d0020, 0xe880000e\n"
        ".word 0xe5950000, 0xe3500000, 0x0a00004e, 0xe59f7148\n"
        ".word 0xe3a01001, 0xe3a00005, 0xe5974000, 0xebff96cb\n"
        ".word 0xe2844a01, 0xe2844f93, 0xe3a08000, 0xe5941000\n"
        ".word 0xe2812001, 0xe0843101, 0xe5931008, 0xe0843102\n"
        ".word 0xe5842000, 0xe5830008, 0xe5d42018, 0xe3520000\n"
        ".word 0x01510000, 0x0a000002, 0xe594101c, 0xe12fff31\n"
        ".word 0xe5c48018, 0xe5970000, 0xe3a01000, 0xebff8627\n"
        ".word 0xe5950000, 0xe3a04000, 0xe3500000, 0xda000020\n"
        ".word 0xe59fa0dc, 0xed9f0a35, 0xe1a0900d, 0xee388a00\n"
        ".word 0xe0640184, 0xe0860100, 0xed900a00, 0xed901a02\n"
        ".word 0xedd02a05, 0xed903a03, 0xe0c0149a, 0xeef05a62\n"
        ".word 0xeeb05a48, 0xeef04a43, 0xe1a010c0, 0xe0410fc0\n"
        ".word 0xeeb04a41, 0xe0400100, 0xeef03a48, 0xe0840100\n"
        ".word 0xeeb02a48, 0xe7990100, 0xeef01a40, 0xeef00a48\n"
        ".word 0xe3800070, 0xe1a03000, 0xe1a02003, 0xe1a01002\n"
        ".word 0xebfedace, 0xe5950000, 0xe2844001, 0xe1500004\n"
        ".word 0xcaffffe2, 0xe5970000, 0xe2804a01, 0xe2844f93\n"
        ".word 0xe5940000, 0xe0841100, 0xe2400001, 0xe5911008\n"
        ".word 0xe5840000, 0xe0840100, 0xe5d42018, 0xe5900008\n"
        ".word 0xe3520000, 0x01510000, 0x0a000002, 0xe594101c\n"
        ".word 0xe12fff31, 0xe5c48018, 0xe28dd030, 0xecbd8b02\n"
        ".word 0xe8bd87f0, 0x004bf89c, 0x004049b4, 0x0044ea00\n"
        ".word 0x42c80000, 0x2aaaaaab\n"
    );
}

// DECOMP_FUNC(0x001182dc, 428)
// 102 ARM instructions through unconditional pop; 20 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_001182dc() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe24dd00c, 0xe59f7188, 0xe5d70000\n"
        ".word 0xe3500000, 0x0a00005d, 0xe59f517c, 0xe3a04001\n"
        ".word 0xe5b50018, 0xe3500000, 0xca000003, 0xe2870084\n"
        ".word 0xe5900004, 0xe3100001, 0x0a000054, 0xe59fa15c\n"
        ".word 0xe1a03004, 0xe24a9038, 0xe59a0004, 0xe5901004\n"
        ".word 0xe58d1004, 0xe5991004, 0xe597202c, 0xeb00686a\n"
        ".word 0xe5d50004, 0xe24ab028, 0xe24b8008, 0xe3500000\n"
        ".word 0x0a000020, 0xe5d50005, 0xe3500000, 0x1a00001d\n"
        ".word 0xe59b0004, 0xe5986004, 0xe1a0300d, 0xe58d0000\n"
        ".word 0xe1c601d8, 0xe1500001, 0x0a000004, 0xe5902000\n"
        ".word 0xe59dc000, 0xe152000c, 0x12800004, 0x1afffff8\n"
        ".word 0xe1500001, 0x0a000002, 0xe1a02000, 0xe2800004\n"
        ".word 0xeb067d1a, 0xe596101c, 0xe586001c, 0xe1510000\n"
        ".word 0x13a01001, 0x03a01000, 0xe3510000, 0x0a000002\n"
        ".word 0xe59d0000, 0xe3a01000, 0xe580100c, 0xe7981104\n"
        ".word 0xe7990104, 0xeb064e76, 0xe5d50014, 0xe3500000\n"
        ".word 0x1a000003, 0xe7991104, 0xe79a0104, 0xe1a02004\n"
        ".word 0xeb0065f2, 0xe5d50004, 0xe3500000, 0x0a000008\n"
        ".word 0xe5d50005, 0xe3500000, 0x1a000005, 0xe79b1104\n"
        ".word 0xe7980104, 0xeb069f9d, 0xe7981104, 0xe7990104\n"
        ".word 0xeb064e63, 0xe79a0104, 0xe597102c, 0xe3a03000\n"
        ".word 0xe3a02002, 0xeb006782, 0xe59d0004, 0xe320f000\n"
        ".word 0xeb067cdd, 0xe320f000, 0xe320f000, 0xe3a00000\n"
        ".word 0xe3500000, 0x159f0028, 0x1b069b9c, 0xe59f0024\n"
        ".word 0xe5900000, 0xeb06adec, 0xe3a00000, 0xe5870018\n"
        ".word 0xe28dd00c, 0xe8bd8ff0, 0x00464af0, 0x004dad80\n"
        ".word 0x00464bb4, 0x00003fff, 0x0044ea00\n"
    );
}

// DECOMP_FUNC(0x00126774, 428)
// 101 ARM instructions through unconditional pop; 24 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_00126774() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d47f0, 0xe1a05001, 0xe1a08000, 0xe1a09002\n"
        ".word 0xe59f717c, 0xed2d8b02, 0xe2870a01, 0xe5900218\n"
        ".word 0xe1b06000, 0x03e00000, 0x0a000057, 0xe5901020\n"
        ".word 0xe3e04000, 0xe3510000, 0x03a04000, 0x0a00000b\n"
        ".word 0xe5901024, 0xe3510000, 0x03a04001, 0x0a000007\n"
        ".word 0xe5901028, 0xe3510000, 0x03a04002, 0x0a000003\n"
        ".word 0xe596002c, 0xe3500000, 0x03a04003, 0x1a000045\n"
        ".word 0xe59fa11c, 0xe1a0000a, 0xeb06641a, 0xe3500000\n"
        ".word 0xe320f000, 0x0a00003f, 0xe1a01008, 0xe1a0000a\n"
        ".word 0xeb006c4d, 0xe3500000, 0xe320f000, 0x0a000039\n"
        ".word 0xe1a01008, 0xe1a00007, 0xeb006c47, 0xe5d6103b\n"
        ".word 0xe3510000, 0x0a00000a, 0xe3500003, 0x0a000002\n"
        ".word 0xe3500002, 0x0a00000a, 0xea00002e, 0xe1a00008\n"
        ".word 0xeb0047ed, 0xe3500000, 0xe320f000, 0x1a000004\n"
        ".word 0xea000028, 0xe3500003, 0x0a000026, 0xe3500002\n"
        ".word 0x1a000024, 0xe0866104, 0xe2861020, 0xe3a03000\n"
        ".word 0xe1a02008, 0xe2870f61, 0xeb06595d, 0xe31000ff\n"
        ".word 0x03a07001, 0x13a07000, 0xe355007f, 0xed9f0a1d\n"
        ".word 0x83a0507f, 0x8a000002, 0xe3550000, 0x0eb08a40\n"
        ".word 0x0a000009, 0xee005a90, 0xeddf1a17, 0xed9f1a17\n"
        ".word 0xed9f8a17, 0xeef80a60, 0xee700ae1, 0xee008a81\n"
        ".word 0xee180a10, 0xe3500101, 0xcd9f8a12, 0xe5960020\n"
        ".word 0xe3a01000, 0xe3500000, 0x1b06592c, 0xeeb00a48\n"
        ".word 0xe5960020, 0xe1a01009, 0xe3500000, 0x1b065927\n"
        ".word 0xe3570000, 0x03e04000, 0xe1a00004, 0xecbd8b02\n"
        ".word 0xe8bd87f0, 0x004e1f68, 0x00000000, 0x42800000\n"
        ".word 0x3c810204, 0x3f800000, 0x40000000\n"
    );
}

// DECOMP_FUNC(0x003a8b14, 428)
// 100 ARM instructions through unconditional pop; 28 trailing data bytes.
extern "C" __attribute__((naked)) void shop_func_003a8b14() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d40f0, 0xe2805ca5, 0xe1a04000, 0xe1d51bf2\n"
        ".word 0xe24dd044, 0xe28000dc, 0xebfa2a69, 0xe1a06000\n"
        ".word 0xe1d50bf2, 0xe0600180, 0xe0800100, 0xe0840100\n"
        ".word 0xe28050fc, 0xe1a00005, 0xebfc5907, 0xe1a07000\n"
        ".word 0xe1a00005, 0xebfc5907, 0xe1a01000, 0xe1a02007\n"
        ".word 0xe28400c8, 0xebfa2219, 0xe3560000, 0x0a000049\n"
        ".word 0xe5d405a4, 0xe2845c05, 0xe3500000, 0x03a0002e\n"
        ".word 0x13a00046, 0xebfc3ffa, 0xe5d500a4, 0xe3500000\n"
        ".word 0x0a00000f, 0xe59f0108, 0xe59f6100, 0xe7901004\n"
        ".word 0xe28d0040, 0xebfa1022, 0xe1b02000, 0xe59f00f4\n"
        ".word 0xe59f10f4, 0x01a02006, 0xe5903008, 0xe1a0000d\n"
        ".word 0xfafc570c, 0xe59f10e4, 0xe1a0000d, 0xebfbd94d\n"
        ".word 0xea00000a, 0xe2846b01, 0xe2866f6a, 0xe2840020\n"
        ".word 0xebfa2aed, 0xe0860280, 0xe3a03000, 0xe1d000b4\n"
        ".word 0xe3a01001, 0xe6ff2070, 0xe1a00003, 0xebfbd433\n"
        ".word 0xe3a00000, 0xebfbe0d6, 0xe3a01000, 0xe3a00002\n"
        ".word 0xe1c401f4, 0xe1a02001, 0xe28400c8, 0xebfa21eb\n"
        ".word 0xe5940590, 0xe2846e59, 0xe5901000, 0xe5912008\n"
        ".word 0xe2841020, 0xe12fff32, 0xe5960000, 0xe1f010b4\n"
        ".word 0xe3811a01, 0xe1c010b0, 0xe5d500a4, 0xe5943028\n"
        ".word 0xe3500000, 0xe2840b01, 0xe2800f57, 0x0a000006\n"
        ".word 0xe28dd044, 0xe353000a, 0xe8bd40f0, 0xa3a0300a\n"
        ".word 0xe3a0101c, 0xe59f2038, 0xeafa2ae0, 0xe28dd044\n"
        ".word 0xe353000a, 0xe8bd40f0, 0xa3a0300a, 0xe3a0101d\n"
        ".word 0xe59f2020, 0xeafa2ad9, 0xe28dd044, 0xe8bd80f0\n"
        ".word 0x004022bc, 0x0000a5b4, 0x0043d990, 0x004022c4\n"
        ".word 0x323232ff, 0x00001030, 0x0000040e\n"
    );
}

// DECOMP_FUNC(0x0019f99c, 432)
// 94 ARM instructions through unconditional pop; 56 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_0019f99c() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d5ff0, 0xe3a06000, 0xe1a08000, 0xe1a09006\n"
        ".word 0xe59f7160, 0xe59fb188, 0xed2d8b0c, 0xeeb08a40\n"
        ".word 0xe247a024, 0xed9f0a54, 0xed9f9a54, 0xed9fba54\n"
        ".word 0xee688a00, 0xeddfba53, 0xed9fca53, 0xeddf9a53\n"
        ".word 0xeddfca53, 0xed9fda53, 0xed9faa53, 0xeddfaa53\n"
        ".word 0xe5c71000, 0xe59f014c, 0xe0000096, 0xe0875100\n"
        ".word 0xe2855004, 0xe2852008, 0xe1c580f0, 0xed859a06\n"
        ".word 0xed859a05, 0xe2850034, 0xec828a02, 0xe285301c\n"
        ".word 0xed859a04, 0xed859a0c, 0xed859a0b, 0xed85ba0a\n"
        ".word 0xecc0ba02, 0xe89a0007, 0xe8830007, 0xe3a01001\n"
        ".word 0xe285003c, 0xeb0489f2, 0xe59f30fc, 0xe2852010\n"
        ".word 0xe285101c, 0xe285003c, 0xeb048993, 0xe2850034\n"
        ".word 0xe285403c, 0xec900a02, 0xe2850068, 0xedc59a19\n"
        ".word 0xe31600ff, 0xec800a02, 0xeeb01a40, 0x0dc4ca0d\n"
        ".word 0x1d84da0d, 0xeeb00a6a, 0xedd40a0d, 0xedd41a0c\n"
        ".word 0xe28400a8, 0xeb045ee1, 0xe3a01001, 0xe28400a8\n"
        ".word 0xeb047184, 0xe28410a8, 0xe2840f56, 0xeb045ffe\n"
        ".word 0xed940a0a, 0xe284102c, 0xedd40a0d, 0xee200a0a\n"
        ".word 0xec911a02, 0xe28400e8, 0xeb045ed4, 0xe3a01000\n"
        ".word 0xe28400e8, 0xeb047177, 0xe5d40000, 0xe3500000\n"
        ".word 0x0a000002, 0xe28410e8, 0xe2840e4a, 0xeb045ea5\n"
        ".word 0xe59b1004, 0xe31600ff, 0xe285003c, 0xe2866001\n"
        ".word 0x05810080, 0x15810084, 0xe3560002, 0xbaffffb8\n"
        ".word 0xecbd8b0c, 0xe8bd9ff0, 0x004d4948, 0x45610000\n"
        ".word 0x00000000, 0xbdb2b8c2, 0x41a00000, 0x46c80000\n"
        ".word 0x419222d1, 0x3fd55555, 0x3faaaaab, 0x3c8efa35\n"
        ".word 0x3ea33c48, 0x0044ea58, 0x00000151, 0x004d493c\n"
    );
}

// DECOMP_FUNC(0x00262498, 432)
// 105 ARM instructions through unconditional pop; 12 trailing data bytes.
extern "C" __attribute__((naked)) void camp_func_00262498() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff7, 0xe24dd018, 0xe1a05000, 0xe1a00002\n"
        ".word 0xe1d513b6, 0xe1b01a01, 0x05d51043, 0x03510000\n"
        ".word 0x03a00000, 0x0a00005c, 0xe3a08000, 0xe3500000\n"
        ".word 0xe1a07008, 0xe1a06008, 0xe58d8000, 0xe58d8004\n"
        ".word 0xe58d8008, 0xe58d800c, 0xe58d8010, 0xaa00000c\n"
        ".word 0xeb01507f, 0xe1d092f4, 0xe3a01001, 0xe1a0000d\n"
        ".word 0xeb008728, 0xe1d502b0, 0xeb012fa3, 0xe1a01000\n"
        ".word 0xe3a02002, 0xe1a00005, 0xeb008705, 0xe1a08000\n"
        ".word 0xea000008, 0xe320f000, 0xeb01192f, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000040, 0xe2801034, 0xe1d091f6\n"
        ".word 0xe891100e, 0xe88d100e, 0xe3a04000, 0xe1a0a00d\n"
        ".word 0xe3a0b014, 0xe08a0084, 0xe1d000b0, 0xe3500000\n"
        ".word 0x0a00000e, 0xeb0086d5, 0xe3500000, 0xe320f000\n"
        ".word 0x0a00000a, 0xe5900038, 0xe1a01800, 0xe15b0da1\n"
        ".word 0x1a000006, 0xe1a00600, 0xe1a00e20, 0xe3500005\n"
        ".word 0x02866001, 0x0a000001, 0xe3500006, 0x02866002\n"
        ".word 0xe2844001, 0xe3540009, 0xbaffffe9, 0xe1d503b6\n"
        ".word 0xe3a024fa, 0xe3a01000, 0xe1520a00, 0x059d101c\n"
        ".word 0x0a00001c, 0xe1b02a00, 0x0a00000e, 0xe3c00a0f\n"
        ".word 0xee000a10, 0xe59f1068, 0xeddf0a1a, 0xe6ff2077\n"
        ".word 0xe0811106, 0xeeb01a60, 0xeeb80a40, 0xedd11a00\n"
        ".word 0xe1a01008, 0xe1a00009, 0xeb05745b, 0xe320f000\n"
        ".word 0xe320f000, 0xea00000a, 0xe5d50043, 0xe3500000\n"
        ".word 0x0a000008, 0xee000a10, 0xeddf0a0b, 0xe6ff2077\n"
        ".word 0xe59d001c, 0xe1a01008, 0xeeb80a40, 0xee200a20\n"
        ".word 0xeb05745f, 0xe1a01000, 0xe1a00001, 0xe28dd024\n"
        ".word 0xe8bd8ff0, 0x00446d30, 0x3f800000, 0x3c23d70a\n"
    );
}

// DECOMP_FUNC(0x002f7f18, 432)
// 105 ARM instructions through unconditional pop; 12 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_002f7f18() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe24dd034, 0xe3a00000, 0xebfe7c0d\n"
        ".word 0xe58d0028, 0xe3a00001, 0xebfe7c0a, 0xe58d002c\n"
        ".word 0xe3a00002, 0xebfe7c07, 0xe1a04000, 0xe59f0170\n"
        ".word 0xe5900000, 0xebfe1b11, 0xe59fa168, 0xe3540000\n"
        ".word 0xe3a06000, 0xe3a09000, 0xc3a09e3e, 0xe1a04006\n"
        ".word 0xe1a0b006, 0xe58d0024, 0xe320f000, 0xebfe6f47\n"
        ".word 0xe2800d7f, 0xe0841204, 0xe5900000, 0xe0811304\n"
        ".word 0xe0805181, 0xe5950000, 0xe3100001, 0x0a000042\n"
        ".word 0xe3100040, 0x1a000040, 0xe1d500f8, 0xe3500000\n"
        ".word 0xba00003d, 0xe2850c01, 0xe59dc028, 0xe1d03bf6\n"
        ".word 0xe1d02cb6, 0xe0030c93, 0xe2021008, 0xe3510000\n"
        ".word 0xe0c3c39a, 0xe1a012c3, 0xe0417fc3, 0x13570001\n"
        ".word 0xc3a07001, 0xca000001, 0xe3570000, 0x03e07000\n"
        ".word 0xe1d00bfa, 0xe59d102c, 0xe2022008, 0xe3520000\n"
        ".word 0xe0000190, 0xe0c0109a, 0xe1a012c0, 0xe0418fc0\n"
        ".word 0x13580001, 0xc3a08001, 0xca000001, 0xe3580000\n"
        ".word 0x03e08000, 0xe320f000, 0xebfe6f1c, 0xe1a01000\n"
        ".word 0xe1d500f8, 0xe2811b07, 0xe2811fa6, 0xe0865106\n"
        ".word 0xe5912000, 0xe0803100, 0xe0833300, 0xe28d1018\n"
        ".word 0xe3a00009, 0xe58d5014, 0xe8810801, 0xe0822103\n"
        ".word 0xe28d0008, 0xe3e03000, 0xe58d5010, 0xe58db020\n"
        ".word 0xe8800208, 0xe3a03000, 0xe88d0180, 0xe59d1024\n"
        ".word 0xe1a00003, 0xebfe1847, 0xe59f203c, 0xe59d1024\n"
        ".word 0xe3a03000, 0xe1a00005, 0xe58db000, 0xe58db004\n"
        ".word 0xe58db008, 0xebfd61d7, 0xe2866001, 0xe2844001\n"
        ".word 0xe3540004, 0xbaffffaf, 0xe28dd034, 0xe3a00001\n"
        ".word 0xe8bd8ff0, 0x0043427c, 0x51eb851f, 0x010001c1\n"
    );
}

// DECOMP_FUNC(0x0036ff14, 432)
// 107 ARM instructions through unconditional pop; 4 trailing data bytes.
extern "C" __attribute__((naked)) void func_0036ff14() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe1a05000, 0xe1b08001, 0xe3a09000\n"
        ".word 0xe24dd00c, 0x059f0190, 0xe1a0a009, 0xe1a04009\n"
        ".word 0x05908000, 0xe5950000, 0xe5907014, 0xe3570000\n"
        ".word 0xc3a0b001, 0xda000036, 0xe5951000, 0xe5b10018\n"
        ".word 0xe3500000, 0x10800001, 0x01a0000a, 0xe7b01104\n"
        ".word 0xe3510000, 0x10816000, 0x01a0600a, 0xe5960008\n"
        ".word 0xe3700001, 0x1a000027, 0xe5961000, 0xe5950000\n"
        ".word 0xe3510000, 0x10813006, 0xe5902084, 0x03a03000\n"
        ".word 0xe2801084, 0xe3520000, 0x10811002, 0x01a0100a\n"
        ".word 0xe590200c, 0xe5911040, 0xe1a0000d, 0xeb01c977\n"
        ".word 0xe59d0000, 0xe3500000, 0xa5c6a005, 0xaa000014\n"
        ".word 0xe5960000, 0xe3500000, 0x10803006, 0xe5950000\n"
        ".word 0x03a03000, 0xe2801084, 0xe5902084, 0xe3520000\n"
        ".word 0x10811002, 0x01a0100a, 0xe5902010, 0xe5911040\n"
        ".word 0xe1a0000d, 0xeb01c965, 0xe59d1000, 0xe3510000\n"
        ".word 0xa5c6b005, 0xb3e00000, 0xb3899010, 0xa5861008\n"
        ".word 0xaa000000, 0xe5860008, 0xe2844001, 0xe1540007\n"
        ".word 0xbaffffc8, 0xe5950000, 0xe590107c, 0xe3510000\n"
        ".word 0x11a00009, 0x1a00001e, 0xe5b01084, 0xe3510000\n"
        ".word 0x1081a000, 0xe5950000, 0xe59ab040, 0xe280000c\n"
        ".word 0xe8900480, 0xe1a0000b, 0xe1a01007, 0xe1a0200a\n"
        ".word 0xeb01cba0, 0xe1a06000, 0xe5980000, 0xe3a02004\n"
        ".word 0xe1a01006, 0xe5903008, 0xe1a00008, 0xe12fff33\n"
        ".word 0xe1a04000, 0xe1a03000, 0xe1a0200a, 0xe1a01007\n"
        ".word 0xe1a0000b, 0xe58d6000, 0xeb01cb67, 0xe1a01000\n"
        ".word 0xe5950000, 0xe580407c, 0xe5950000, 0xe5801080\n"
        ".word 0xe1a00009, 0xe28dd00c, 0xe8bd8ff0, 0x00471c40\n"
    );
}

// DECOMP_FUNC(0x002421b0, 436)
// 103 ARM instructions through unconditional pop; 24 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_002421b0() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d41f0, 0xe59f7194, 0xe24ddd05, 0xe3a08000\n"
        ".word 0xe1a04000, 0xe58d80d0, 0xe597003c, 0xe59f6178\n"
        ".word 0xe28d5004, 0xe3500000, 0x0a00000f, 0xe5970040\n"
        ".word 0xeb02d822, 0xe5970040, 0xe5900008, 0xe58d00d0\n"
        ".word 0xe5970040, 0xe1a01005, 0xeb038518, 0xe58d00cc\n"
        ".word 0xe5970040, 0xeb035afb, 0xe58d00d4, 0xe59d00d0\n"
        ".word 0xe3500001, 0x0a000020, 0xea000025, 0xe1a01004\n"
        ".word 0xe3a00000, 0xe3a00000, 0xe3140008, 0xe587003c\n"
        ".word 0x0a000010, 0xe3a00016, 0xe2505000, 0xe3a04000\n"
        ".word 0x9a00000c, 0xe1a02004, 0xe28f1f41, 0xe28d00d8\n"
        ".word 0xfa01f169, 0xe58d8000, 0xe597003c, 0xe1a03004\n"
        ".word 0xe3a02008, 0xe28d10d8, 0xeb02700d, 0xe2844001\n"
        ".word 0xe1550004, 0x8afffff2, 0xe597003c, 0xeb0332b5\n"
        ".word 0xe3a0201c, 0xe3a010ba, 0xe5870040, 0xe8800006\n"
        ".word 0xe320f000, 0xe320f000, 0xea000005, 0xe5970040\n"
        ".word 0xeb001441, 0xe5878040, 0xe597003c, 0xeb00142e\n"
        ".word 0xe587803c, 0xe59d00d0, 0xe3500002, 0x03a06501\n"
        ".word 0x0a00001e, 0xe3500001, 0x1a00001c, 0xe59d00cc\n"
        ".word 0xe3500008, 0x0a000010, 0xe59d00d4, 0xe2601000\n"
        ".word 0xe5970014, 0xeb0011d8, 0xe5971024, 0xe1a04000\n"
        ".word 0xe1510004, 0x0a000010, 0xe5970014, 0xeb000198\n"
        ".word 0xe5b70014, 0xe1a02004, 0xe5971010, 0xeb00695d\n"
        ".word 0xe320f000, 0xe320f000, 0xea000007, 0xe5970014\n"
        ".word 0xe5971024, 0xeb00018e, 0xe3a03004, 0xe597001c\n"
        ".word 0xe1a02003, 0xe28d10d4, 0xeb006a35, 0xe59f601c\n"
        ".word 0xe28ddd05, 0xe1a00006, 0xe8bd81f0, 0x00600001\n"
        ".word 0x0044ea80, 0x454e4547, 0x204c4152, 0x00006425\n"
        ".word 0x00400002\n"
    );
}

// DECOMP_FUNC(0x0025f538, 436)
// 107 ARM instructions through unconditional pop; 8 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_0025f538() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d43f0, 0xe2805a03, 0xe1a04000, 0xe24dd00c\n"
        ".word 0xe5d50084, 0xe3500000, 0x1a000061, 0xe595005c\n"
        ".word 0xe3500003, 0xca00005e, 0xe2840a01, 0xe2800fae\n"
        ".word 0xe1a07000, 0xeb017e82, 0xe1a06000, 0xe1a00007\n"
        ".word 0xeb017e7c, 0xe1a07000, 0xe28400ac, 0xed900a08\n"
        ".word 0xeb018060, 0xe595005c, 0xe2801052, 0xe3a00015\n"
        ".word 0xeb01804c, 0xe59f9140, 0xe1a04000, 0xe3a02000\n"
        ".word 0xe3a01001, 0xe5995000, 0xe3a00006, 0xeb019a7a\n"
        ".word 0xe2855a01, 0xe2855fab, 0xe3a08000, 0xe5951000\n"
        ".word 0xe0852101, 0xe5921008, 0xe5820008, 0xe5d52018\n"
        ".word 0xe3520000, 0x01510000, 0x0a000002, 0xe595101c\n"
        ".word 0xe12fff31, 0xe5c58018, 0xe1d400fa, 0xe3a05029\n"
        ".word 0xe3a0204b, 0xe0800007, 0xe88d0021, 0xe1d400f8\n"
        ".word 0xe3a01015, 0xe0803006, 0xe3a00002, 0xeb017f91\n"
        ".word 0xe1d400fa, 0xe3a0204a, 0xe3a01015, 0xe0800007\n"
        ".word 0xe88d0021, 0xe1d400f8, 0xe0803006, 0xe3a00002\n"
        ".word 0xeb017f88, 0xe1d400fa, 0xe3a0204c, 0xe3a01015\n"
        ".word 0xe0800007, 0xe88d0021, 0xe1d400f8, 0xe0803006\n"
        ".word 0xe3a00002, 0xeb017f7f, 0xe1d400fa, 0xe3a0204d\n"
        ".word 0xe3a01015, 0xe0800007, 0xe88d0021, 0xe1d400f8\n"
        ".word 0xe0803006, 0xe3a00002, 0xeb017f76, 0xe5994000\n"
        ".word 0xe3a02000, 0xe3a01007, 0xe3a00006, 0xeb019a42\n"
        ".word 0xe2844a01, 0xe2844fab, 0xe5941000, 0xe0842101\n"
        ".word 0xe5921008, 0xe5820008, 0xe5d42018, 0xe3520000\n"
        ".word 0x01510000, 0x0a000002, 0xe594101c, 0xe12fff31\n"
        ".word 0xe5c48018, 0xe28dd00c, 0xed9f0a04, 0xe8bd43f0\n"
        ".word 0xea01800c, 0xe28dd00c, 0xe8bd83f0, 0x0044ea00\n"
        ".word 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x003a18b8, 436)
// 102 ARM instructions through unconditional pop; 28 trailing data bytes.
extern "C" __attribute__((naked)) void shop_func_003a18b8() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4070, 0xe1a04000, 0xebfba0a1, 0xebfba087\n"
        ".word 0xebfbb0e1, 0xebfbb028, 0xe59f0178, 0xe3a02000\n"
        ".word 0xe2841e16, 0xebfbd788, 0xe3a0002b, 0xebfc8d4f\n"
        ".word 0xe3a01000, 0xe3a0002b, 0xebfc9070, 0xe5d40014\n"
        ".word 0xe3a05000, 0xe1a06005, 0xe3500000, 0x0a000002\n"
        ".word 0xe3500001, 0x1a000019, 0xea00002f, 0xe5940018\n"
        ".word 0xe3500008, 0x0a000009, 0xe3500006, 0x13500007\n"
        ".word 0x0a00000c, 0xe3500009, 0x0a000021, 0xe59f0118\n"
        ".word 0xe3a0505a, 0xe3a02000, 0xe2841f59, 0xea00000a\n"
        ".word 0xe59f0108, 0xe3a05058, 0xe3a06019, 0xe3a02000\n"
        ".word 0xe2841f59, 0xea000004, 0xe59f00f4, 0xe3a0508b\n"
        ".word 0xe3a06050, 0xe3a02000, 0xe2841f59, 0xebfbd762\n"
        ".word 0xe1a00005, 0xebfd718d, 0xe59f10d8, 0xe3560000\n"
        ".word 0xe7810004, 0x0a00002e, 0xe3a02000, 0xe1a01002\n"
        ".word 0xe1a00006, 0xebfb91c4, 0xe2844b57, 0xe2844f51\n"
        ".word 0xe3a02000, 0xe5840000, 0xe8bd4070, 0xe1a01002\n"
        ".word 0xeafa98e9, 0xe59f0090, 0xe3a05088, 0xe3a060a2\n"
        ".word 0xe3a02000, 0xe2841f59, 0xeaffffe7, 0xe5940018\n"
        ".word 0xe3500009, 0x0a000008, 0xe3500005, 0x0a00000c\n"
        ".word 0xe350000a, 0x0a000010, 0xe59f006c, 0xe3a0505b\n"
        ".word 0xe3a02000, 0xe2841f59, 0xeaffffdb, 0xe59f005c\n"
        ".word 0xe3a05059, 0xe3a0601a, 0xe3a02000, 0xe2841f59\n"
        ".word 0xeaffffd5, 0xe59f0040, 0xe3a0508b, 0xe3a06050\n"
        ".word 0xe3a02000, 0xe2841f59, 0xeaffffcf, 0xe59f0028\n"
        ".word 0xe3a05089, 0xe3a060a3, 0xe3a02000, 0xe2841f59\n"
        ".word 0xeaffffc9, 0xe8bd8070, 0x004076b0, 0x004076f0\n"
        ".word 0x004076c0, 0x004076d8, 0x00015d40, 0x00407720\n"
        ".word 0x00407708\n"
    );
}

// DECOMP_FUNC(0x00150654, 440)
// 105 ARM instructions through unconditional pop; 20 trailing data bytes.
extern "C" __attribute__((naked)) void func_00150654() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d5ff0, 0xe1a05000, 0xe1b07002, 0xe1a08001\n"
        ".word 0xe1a09003, 0x0a000061, 0xe59fb188, 0xe59f3180\n"
        ".word 0xe3a0211a, 0xe2871020, 0xe59b0000, 0xe3a0a000\n"
        ".word 0xe0c020f8, 0xeb054542, 0xe59b0000, 0xe59f4168\n"
        ".word 0xe1b06008, 0xe2800018, 0xe58b0000, 0x0a000008\n"
        ".word 0xe5960000, 0xe5901008, 0xe1a00008, 0xe12fff31\n"
        ".word 0xe1500004, 0x0a000003, 0xe5900000, 0xe3500000\n"
        ".word 0x1afffffa, 0xe1a0600a, 0xe5950008, 0xe590101c\n"
        ".word 0xe1510008, 0x0a000008, 0xe3560000, 0x0a000004\n"
        ".word 0xe1a01006, 0xeb000dd8, 0xe320f000, 0xe320f000\n"
        ".word 0xea000001, 0xe1a01008, 0xeb000d98, 0xe5971030\n"
        ".word 0xe2870030, 0xe3510000, 0x10814000, 0xe597002c\n"
        ".word 0x01a0400a, 0xe0847100, 0xe1540007, 0x0a000033\n"
        ".word 0xe5940000, 0xe3500000, 0x10800004, 0x01a0000a\n"
        ".word 0xe3560000, 0xe5903000, 0x13530000, 0x0a000009\n"
        ".word 0xe5941000, 0xe1a00005, 0xe3510000, 0x10812004\n"
        ".word 0x01a0200a, 0xe1a01006, 0xeb000cbd, 0xe320f000\n"
        ".word 0xe320f000, 0xea00000f, 0xe5950008, 0xe59f308c\n"
        ".word 0xe3a02166, 0xe288108c, 0xe5900008, 0xe590c014\n"
        ".word 0xe3ccc006, 0xe580c014, 0xe59b0000, 0xe1c020f0\n"
        ".word 0xe59f206c, 0xe2800008, 0xeb0544c9, 0xe59b0000\n"
        ".word 0xe2800040, 0xe58b0000, 0xe5940000, 0xe3500000\n"
        ".word 0x10800004, 0x01a0000a, 0xe5b01010, 0xe3510000\n"
        ".word 0x10800001, 0x01a0000a, 0xe0801109, 0xe5910000\n"
        ".word 0xe3500000, 0x10811000, 0xe5950008, 0x01a0100a\n"
        ".word 0xeb000d22, 0xe2844004, 0xe1540007, 0x1affffcb\n"
        ".word 0xe8bd9ff0, 0x804f02c0, 0x004652a0, 0x00472288\n"
        ".word 0x000f02c0, 0x00bf02c1\n"
    );
}

// DECOMP_FUNC(0x002f2e54, 440)
// 106 ARM instructions through unconditional pop; 16 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_002f2e54() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d47f0, 0xee000a10, 0xee001a90, 0xe1a07002\n"
        ".word 0xe59f9194, 0xe3a01001, 0xed2d8b04, 0xe28d2030\n"
        ".word 0xeeb80ac0, 0xe8920060, 0xeef80ae0, 0xe59f2174\n"
        ".word 0xe5994000, 0xe1a08003, 0xe1a00001, 0xec921a02\n"
        ".word 0xee300a01, 0xee700aa1, 0xeebd8ac0, 0xeefd8ae0\n"
        ".word 0xebff4c34, 0xe2844a01, 0xe2844f93, 0xe3a0a000\n"
        ".word 0xe5941000, 0xe2812001, 0xe0843101, 0xe5931008\n"
        ".word 0xe0843102, 0xe5842000, 0xe5830008, 0xe5d42018\n"
        ".word 0xe3520000, 0x01510000, 0x0a000002, 0xe594101c\n"
        ".word 0xe12fff31, 0xe5c4a018, 0xe5990000, 0xe3a01000\n"
        ".word 0xebff3b90, 0xe1a01406, 0xe1a02806, 0xed9f9a3f\n"
        ".word 0xe1b00c26, 0xe1a01c21, 0xe1a02c22, 0xe20630ff\n"
        ".word 0x0a00000e, 0xee008a10, 0xe1a03c03, 0xeef80ae8\n"
        ".word 0xe1832802, 0xe1821401, 0xe1800001, 0xeef81ac0\n"
        ".word 0xee007a10, 0xeeb02a49, 0xe1a03000, 0xe1a02003\n"
        ".word 0xe1a01002, 0xeeb81ac0, 0xeeb80ac8, 0xebff36f1\n"
        ".word 0xe1a02405, 0xe1a01805, 0xe1b00c25, 0xe1a02c22\n"
        ".word 0xe1a01c21, 0xe20530ff, 0x0a00000f, 0xee008a10\n"
        ".word 0xe1a03c03, 0xeef80ae8, 0xe1831801, 0xe1811402\n"
        ".word 0xe1800001, 0xeef81ac0, 0xee007a10, 0xeeb02a49\n"
        ".word 0xe1a03000, 0xe1a02003, 0xeddf2a19, 0xe1a01002\n"
        ".word 0xeeb81ac0, 0xeeb80ac8, 0xebfc7451, 0xe5990000\n"
        ".word 0xe2804a01, 0xe2844f93, 0xe5940000, 0xe0841100\n"
        ".word 0xe2400001, 0xe5911008, 0xe5840000, 0xe0840100\n"
        ".word 0xe5d42018, 0xe5900008, 0xe3520000, 0x01510000\n"
        ".word 0x0a000002, 0xe594101c, 0xe12fff31, 0xe5c4a018\n"
        ".word 0xecbd8b04, 0xe8bd87f0, 0x004724cc, 0x0044ea00\n"
        ".word 0x00000000, 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x003518d0, 440)
// 109 ARM instructions through unconditional pop; 4 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_003518d0() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d40f0, 0xe1a04000, 0xe24dd014, 0xe5900014\n"
        ".word 0xe3500000, 0x0a000064, 0xe3a05001, 0xe5c45010\n"
        ".word 0xe2840020, 0xebfdca52, 0xe5942028, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe88d0007, 0xe3a03000, 0xe3a02001\n"
        ".word 0xe28d1008, 0xe28d000c, 0xebfdca77, 0xe1b01fa0\n"
        ".word 0x1bfdced0, 0xe2840028, 0xe5c4502c, 0xebfdca2d\n"
        ".word 0xe5940028, 0xe3a07000, 0xe2845028, 0xe3500000\n"
        ".word 0x0a000001, 0xef000023, 0xe5857000, 0xe59f6130\n"
        ".word 0xe5960004, 0xebfdca01, 0xe5960004, 0xe3500000\n"
        ".word 0x0a000004, 0xe1a05000, 0xebfdc9fc, 0xe1a00005\n"
        ".word 0xe320f000, 0xebfd82e9, 0xe5867004, 0xe5960000\n"
        ".word 0xebfdca76, 0xe3e00000, 0xe5867000, 0xe5840008\n"
        ".word 0xe1a00004, 0xebfffb6c, 0xe59402e8, 0xe3a05000\n"
        ".word 0xe3500000, 0xda00000b, 0xe59401b8, 0xe0846105\n"
        ".word 0xe5941014, 0xe59622ec, 0xe5903000, 0xe5933004\n"
        ".word 0xe12fff33, 0xe58672ec, 0xe59402e8, 0xe2855001\n"
        ".word 0xe1500005, 0xcafffff3, 0xe5940484, 0xe3a05000\n"
        ".word 0xe3500000, 0xda00000b, 0xe59401b8, 0xe0846105\n"
        ".word 0xe5941014, 0xe5962488, 0xe5903000, 0xe593300c\n"
        ".word 0xe12fff33, 0xe5867488, 0xe5940484, 0xe2855001\n"
        ".word 0xe1500005, 0xcafffff3, 0xe59401c4, 0xe3a05000\n"
        ".word 0xe3500000, 0xda00000d, 0xe0850085, 0xe0846180\n"
        ".word 0xe59611d8, 0xe3510000, 0x0a000004, 0xe5940014\n"
        ".word 0xe5902000, 0xe5922004, 0xe12fff32, 0xe58671d8\n"
        ".word 0xe59401c4, 0xe2855001, 0xe1500005, 0xcafffff1\n"
        ".word 0xe2840f56, 0xebfff5fd, 0xe5847014, 0xe5847018\n"
        ".word 0xe58471b8, 0xe58471bc, 0xe58471c0, 0xe28dd014\n"
        ".word 0xe8bd80f0, 0x0044d158\n"
    );
}

// DECOMP_FUNC(0x001204a4, 444)
// 106 ARM instructions through unconditional pop; 20 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_001204a4() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d47f0, 0xe1a05000, 0xe1a07001, 0xe3a02004\n"
        ".word 0xe5910000, 0xe3a01048, 0xe5903008, 0xe1a00007\n"
        ".word 0xe12fff33, 0xe1b04000, 0x13a01048, 0x1b069196\n"
        ".word 0xe59f0170, 0xe59f1170, 0xe3a02405, 0xe3a09000\n"
        ".word 0xe8840007, 0xe2843024, 0xe584900c, 0xe5849010\n"
        ".word 0xe5849014, 0xe5950000, 0xe59f1150, 0xe5840018\n"
        ".word 0xe5952004, 0xe59f0148, 0xe5841020, 0xe584201c\n"
        ".word 0xe8830201, 0xe2841030, 0xe584902c, 0xe5950008\n"
        ".word 0xe3a02004, 0xe8810201, 0xe3a01020, 0xe5970000\n"
        ".word 0xe5903008, 0xe1a00007, 0xe12fff33, 0xe1b06000\n"
        ".word 0x0a000007, 0xe5869000, 0xe5869004, 0xe5869008\n"
        ".word 0xe586900c, 0xe5869010, 0xe5869014, 0xe5869018\n"
        ".word 0xe586901c, 0xe5867010, 0xe5951000, 0xe3a00020\n"
        ".word 0xed9f1a38, 0xe5861000, 0xe5951004, 0xe5861004\n"
        ".word 0xe595100c, 0xe1c601f4, 0xedd50a00, 0xed950a01\n"
        ".word 0xe5d50018, 0xeef80ae0, 0xeeb80ac0, 0xe3500000\n"
        ".word 0x0286000c, 0x05869008, 0xee610a20, 0xee200a80\n"
        ".word 0xeebc0ac0, 0xee108a10, 0x0a000016, 0xe5970000\n"
        ".word 0xe3a02080, 0xe1a01008, 0xe5903008, 0xe1a00007\n"
        ".word 0xe12fff33, 0xe5d51010, 0xe1a03000, 0xe3510000\n"
        ".word 0x0a000006, 0xe1b01008, 0xe3a02000, 0x120220ff\n"
        ".word 0x0a000002, 0xe2511001, 0xe4c02001, 0x1afffffc\n"
        ".word 0xe3530000, 0xe286000c, 0x10431000, 0xe5868008\n"
        ".word 0x15801000, 0x1a000000, 0xe5809000, 0xe3560000\n"
        ".word 0xe2840038, 0x10461000, 0x05809000, 0x15801000\n"
        ".word 0xe5d50011, 0xe5c4003c, 0xe5950014, 0xe5840040\n"
        ".word 0xe1a00004, 0xe8bd87f0, 0x20000021, 0x48535854\n"
        ".word 0x00006040, 0x00001405, 0x40800000\n"
    );
}

// DECOMP_FUNC(0x002d110c, 444)
// 103 ARM instructions through unconditional pop; 32 trailing data bytes.
extern "C" __attribute__((naked)) void func_002d110c() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d47f0, 0xe1a07000, 0xe5905024, 0xe28540c0\n"
        ".word 0xe59580b8, 0xe2986000, 0x1597601c, 0x13560000\n"
        ".word 0x1a00000c, 0xe2840010, 0xed9f0a5b, 0xeddf0a5b\n"
        ".word 0xed840a06, 0xed9f1a5a, 0xed840a07, 0xeddf1a59\n"
        ".word 0xed9f2a59, 0xecc00a02, 0xe2840020, 0xecc01a02\n"
        ".word 0xe5950028, 0xe5840004, 0xe1580006, 0xb3a00000\n"
        ".word 0xb5c40003, 0xba00004b, 0xe1a03008, 0xe1a02006\n"
        ".word 0xe2851024, 0xe1a00005, 0xebfe61da, 0xe1a09000\n"
        ".word 0xe5970010, 0xebfe191f, 0xe59f7120, 0xe2871c01\n"
        ".word 0xe2870e11, 0xec910a04, 0xec800a04, 0xe1a00009\n"
        ".word 0xebfe1918, 0xed970a40, 0xedd70a44, 0xe2870c01\n"
        ".word 0xee200a20, 0xed870a40, 0xed970a41, 0xedd70a45\n"
        ".word 0xee200a20, 0xed870a41, 0xed970a42, 0xedd70a46\n"
        ".word 0xee200a20, 0xed870a42, 0xedd70a47, 0xed970a43\n"
        ".word 0xee200a20, 0xed870a43, 0xed9f0a31, 0xecd00a04\n"
        ".word 0xee600a80, 0xee211a00, 0xee611a80, 0xee222a00\n"
        ".word 0xeefc0ae0, 0xeebc0ac1, 0xee100a90, 0xeefc0ae1\n"
        ".word 0xee101a10, 0xeebc0ac2, 0xe1a00c00, 0xe20130ff\n"
        ".word 0xe1800803, 0xee102a90, 0xee101a10, 0xe20220ff\n"
        ".word 0xe20110ff, 0xe1800402, 0xe1800001, 0xe6bf1f30\n"
        ".word 0xe6bf3f30, 0xe1a02821, 0xe1a01423, 0xe6bf3f30\n"
        ".word 0xe6bf0f30, 0xe1a03c23, 0xe5c43000, 0xe5c42001\n"
        ".word 0xe5c41002, 0xe5c40003, 0xe1a02008, 0xe1a01006\n"
        ".word 0xe2850034, 0xebfe6138, 0xeddf0a0e, 0xe1a02008\n"
        ".word 0xe1a01006, 0xee300a20, 0xe2850060, 0xed840a03\n"
        ".word 0xebfe6131, 0xed840a02, 0xe8bd87f0, 0x00000000\n"
        ".word 0x43480000, 0x42f00000, 0x43c80000, 0x43700000\n"
        ".word 0x004ea81c, 0x437f0000, 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x00336e20, 444)
// 107 ARM instructions through unconditional pop; 16 trailing data bytes.
extern "C" __attribute__((naked)) void battle_func_00336e20() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff1, 0xe24dd0d8, 0xe59f019c, 0xe5900000\n"
        ".word 0xe5901634, 0xe3811901, 0xe5801634, 0xe59f018c\n"
        ".word 0xe5900000, 0xebfc263e, 0xe59d10d8, 0xe3a06000\n"
        ".word 0xe3a00004, 0xe2812b07, 0xe28db008, 0xe2822fa6\n"
        ".word 0xe0801100, 0xe5923000, 0xe0811300, 0xe2800001\n"
        ".word 0xe0831101, 0xe5913050, 0xe3130001, 0x13130002\n"
        ".word 0x178b1106, 0x12866001, 0xe3500036, 0xbafffff3\n"
        ".word 0xe59f313c, 0xe3a02004, 0xe1a01006, 0xe1a0000b\n"
        ".word 0xfbfe0418, 0xe3a0a000, 0xe3560000, 0xe1a0700a\n"
        ".word 0xe1a0400a, 0xda00003e, 0xe79b5104, 0xe5950050\n"
        ".word 0xe3100001, 0x13100002, 0x0a000036, 0xe1d505b8\n"
        ".word 0xe3100b02, 0x1a000033, 0xe5951050, 0xe3800b02\n"
        ".word 0xe1c505b8, 0xe59f00ec, 0xe3110010, 0x0a000007\n"
        ".word 0xe280000c, 0xe890100e, 0xe6bf9071, 0xe6bf0072\n"
        ".word 0xe58d00d0, 0xe6bf807c, 0xe6bf0073, 0xea000008\n"
        ".word 0xe4903004, 0xe4902004, 0xe4901010, 0xe6bf9073\n"
        ".word 0xe590c000, 0xe6bf0072, 0xe58d00d0, 0xe6bf0071\n"
        ".word 0xe6bf807c, 0xe3a03000, 0xe58d0000, 0xe59d00d8\n"
        ".word 0xe1a02003, 0xe1a01005, 0xebfc25d7, 0xe3a00000\n"
        ".word 0xe58d0004, 0xe59d00d0, 0xe3a030ff, 0xe1a02005\n"
        ".word 0xe0800008, 0xe1000987, 0xe3a01000, 0xebfc38ef\n"
        ".word 0xe5950050, 0xe3a03006, 0xe1a02005, 0xe3100010\n"
        ".word 0xe3a0000d, 0xe58d0000, 0x13a03007, 0xe1008987\n"
        ".word 0xe3a01000, 0xebfc25b1, 0xe2870001, 0xe35a0000\n"
        ".word 0xe6bf7070, 0x03a0a001, 0xe2844001, 0xe1540006\n"
        ".word 0xbaffffc0, 0xe59f0010, 0xe3a01078, 0xe5900000\n"
        ".word 0xebfc2665, 0xe28dd0dc, 0xe8bd8ff0, 0x004342c8\n"
        ".word 0x00435d18, 0x0019d76c, 0x00439a20\n"
    );
}

// DECOMP_FUNC(0x003635f0, 444)
// 110 ARM instructions through unconditional pop; 4 trailing data bytes.
extern "C" __attribute__((naked)) void func_003635f0() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d5ff0, 0xe3a06000, 0xe1a09001, 0xe1a0b000\n"
        ".word 0xe1c94edc, 0xe1540005, 0x0a000006, 0xe5940000\n"
        ".word 0xe1a01006, 0xe5900028, 0xebfff991, 0xe2844004\n"
        ".word 0xe1540005, 0x1afffff8, 0xe289800c, 0xe1a06009\n"
        ".word 0xe8980500, 0xe158000a, 0x0a00001a, 0xe5987000\n"
        ".word 0xe5970034, 0xe1c040d8, 0xe1540005, 0x0a000008\n"
        ".word 0xe5940000, 0xe1a02006, 0xe1a01007, 0xe5903000\n"
        ".word 0xe5933000, 0xe12fff33, 0xe2844004, 0xe1540005\n"
        ".word 0x1afffff6, 0xe5980000, 0xe5901000, 0xe5911020\n"
        ".word 0xe12fff31, 0xe5980000, 0xe59b1010, 0xe5902000\n"
        ".word 0xe592300c, 0xe1a02006, 0xe12fff33, 0xe2888004\n"
        ".word 0xe158000a, 0x1affffe4, 0xe1c94edc, 0xe3a06001\n"
        ".word 0xe1540005, 0x0a000006, 0xe5940000, 0xe1a01006\n"
        ".word 0xe5900028, 0xebfff966, 0xe2844004, 0xe1540005\n"
        ".word 0x1afffff8, 0xe599003c, 0xe5995040, 0xe3a07001\n"
        ".word 0xe1a01007, 0xe0452000, 0xe0873142, 0xe3530001\n"
        ".word 0xc3a0c000, 0xc0873142, 0xda000005, 0xe4902004\n"
        ".word 0xe2811001, 0xe1530001, 0xe5922220, 0xe5c2c018\n"
        ".word 0xcafffff9, 0xe599403c, 0xe1540005, 0x0a00000f\n"
        ".word 0xe5940000, 0xe5d01231, 0xe3510000, 0x1a000008\n"
        ".word 0xe5906220, 0xe5d60018, 0xe3500000, 0x1a000004\n"
        ".word 0xe59b0008, 0xe59b2010, 0xe1a01006, 0xeb01f70e\n"
        ".word 0xe5c67018, 0xe2844004, 0xe1540005, 0x1affffef\n"
        ".word 0xe59f0040, 0xe28990ec, 0xe8990050, 0xe5905004\n"
        ".word 0xe5907000, 0xe1540006, 0x0a000009, 0xe5940000\n"
        ".word 0xe3150001, 0x01a01007, 0xe08000c5, 0x15901000\n"
        ".word 0x17911007, 0xe12fff31, 0xe2844004, 0xe1540006\n"
        ".word 0x1afffff5, 0xe8bd9ff0, 0x004105ac\n"
    );
}

// DECOMP_FUNC(0x0012aef4, 448)
// 105 ARM instructions through unconditional pop; 28 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_0012aef4() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d47f0, 0xe3a060d0, 0xe1a07000, 0xe1a09001\n"
        ".word 0xe3a05000, 0xed2d8b02, 0xe3a02004, 0xe5901000\n"
        ".word 0xe5913008, 0xe1a01006, 0xe12fff33, 0xe1a04000\n"
        ".word 0xe2566001, 0xe4c05001, 0x1afffffc, 0xe59f0164\n"
        ".word 0xe59f1164, 0xe59f2158, 0xe5840008, 0xe5841004\n"
        ".word 0xe5842000, 0xe1a08007, 0xe5845010, 0xe3590000\n"
        ".word 0xe284600c, 0xe3a07c01, 0xe5845014, 0x0a000026\n"
        ".word 0xe1a00009, 0xeb0660c8, 0xe3500c01, 0x31a07000\n"
        ".word 0xe5980000, 0xe2871001, 0xe3a02004, 0xe5903008\n"
        ".word 0xe1a00008, 0xe12fff33, 0xe1a08000, 0xe1a02007\n"
        ".word 0xe1a01009, 0xeb066c15, 0xe3580000, 0x10480006\n"
        ".word 0xe7c85007, 0x15860000, 0x0a000013, 0xe5845020\n"
        ".word 0xe5845024, 0xeddf8a39, 0xe5845028, 0xe584502c\n"
        ".word 0xedc48a0c, 0xed9f8a36, 0xedc48a0d, 0xedc48a0e\n"
        ".word 0xed848a0f, 0xed848a10, 0xe59f00c8, 0xed848a11\n"
        ".word 0xed848a12, 0xed848a13, 0xed848a14, 0xe5900000\n"
        ".word 0xe3100001, 0x1a000016, 0xea000001, 0xe5865000\n"
        ".word 0xeaffffe9, 0xe59f009c, 0xfa065430, 0xe3500000\n"
        ".word 0xe320f000, 0x0a00000e, 0xe59f008c, 0xe2801010\n"
        ".word 0xedc08a00, 0xed808a01, 0xed808a02, 0xed808a03\n"
        ".word 0xec818a02, 0xe2801024, 0xed808a06, 0xed808a07\n"
        ".word 0xed808a08, 0xec818a02, 0xed808a0b, 0xe59f0054\n"
        ".word 0xe1a00000, 0xe59f0050, 0xe2849084, 0xe89011ee\n"
        ".word 0xe88911ee, 0xe2801020, 0xe590002c, 0xe891000e\n"
        ".word 0xe58400b0, 0xe28400a4, 0xe880000e, 0xe1a00004\n"
        ".word 0xe5941018, 0xe3811001, 0xe5841018, 0xecbd8b02\n"
        ".word 0xe8bd87f0, 0x40000422, 0x07010000, 0x4e465443\n"
        ".word 0x3f800000, 0x00000000, 0x00476634, 0x004efd6c\n"
    );
}

// DECOMP_FUNC(0x0012c188, 448)
// 105 ARM instructions through unconditional pop; 28 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_0012c188() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d47f0, 0xe3a060e8, 0xe1a07000, 0xe1a09001\n"
        ".word 0xe3a05000, 0xed2d8b02, 0xe3a02004, 0xe5901000\n"
        ".word 0xe5913008, 0xe1a01006, 0xe12fff33, 0xe1a04000\n"
        ".word 0xe2566001, 0xe4c05001, 0x1afffffc, 0xe59f0164\n"
        ".word 0xe59f1164, 0xe59f2158, 0xe5840008, 0xe5841004\n"
        ".word 0xe5842000, 0xe1a08007, 0xe5845010, 0xe3590000\n"
        ".word 0xe284600c, 0xe3a07c01, 0xe5845014, 0x0a000026\n"
        ".word 0xe1a00009, 0xeb065c23, 0xe3500c01, 0x31a07000\n"
        ".word 0xe5980000, 0xe2871001, 0xe3a02004, 0xe5903008\n"
        ".word 0xe1a00008, 0xe12fff33, 0xe1a08000, 0xe1a02007\n"
        ".word 0xe1a01009, 0xeb066770, 0xe3580000, 0x10480006\n"
        ".word 0xe7c85007, 0x15860000, 0x0a000013, 0xe5845020\n"
        ".word 0xe5845024, 0xeddf8a39, 0xe5845028, 0xe584502c\n"
        ".word 0xedc48a0c, 0xed9f8a36, 0xedc48a0d, 0xedc48a0e\n"
        ".word 0xed848a0f, 0xed848a10, 0xe59f00c8, 0xed848a11\n"
        ".word 0xed848a12, 0xed848a13, 0xed848a14, 0xe5900000\n"
        ".word 0xe3100001, 0x1a000016, 0xea000001, 0xe5865000\n"
        ".word 0xeaffffe9, 0xe59f009c, 0xfa064f8b, 0xe3500000\n"
        ".word 0xe320f000, 0x0a00000e, 0xe59f008c, 0xe2801010\n"
        ".word 0xedc08a00, 0xed808a01, 0xed808a02, 0xed808a03\n"
        ".word 0xec818a02, 0xe2801024, 0xed808a06, 0xed808a07\n"
        ".word 0xed808a08, 0xec818a02, 0xed808a0b, 0xe59f0054\n"
        ".word 0xe1a00000, 0xe59f0050, 0xe2849084, 0xe89011ee\n"
        ".word 0xe88911ee, 0xe2801020, 0xe590002c, 0xe891000e\n"
        ".word 0xe58400b0, 0xe28400a4, 0xe880000e, 0xe1a00004\n"
        ".word 0xe5941018, 0xe3811001, 0xe5841018, 0xecbd8b02\n"
        ".word 0xe8bd87f0, 0x40000122, 0x07010000, 0x4e465443\n"
        ".word 0x3f800000, 0x00000000, 0x00476634, 0x004efd6c\n"
    );
}

// DECOMP_FUNC(0x0013cf50, 448)
// 105 ARM instructions through unconditional pop; 28 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_0013cf50() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d47f0, 0xe3a06c01, 0xe1a07000, 0xe1a09001\n"
        ".word 0xe3a05000, 0xed2d8b02, 0xe3a02004, 0xe5901000\n"
        ".word 0xe5913008, 0xe1a01006, 0xe12fff33, 0xe1a04000\n"
        ".word 0xe2566001, 0xe4c05001, 0x1afffffc, 0xe59f0164\n"
        ".word 0xe59f1164, 0xe59f2158, 0xe5840008, 0xe5841004\n"
        ".word 0xe5842000, 0xe1a08007, 0xe5845010, 0xe3590000\n"
        ".word 0xe284600c, 0xe3a07c01, 0xe5845014, 0x0a000026\n"
        ".word 0xe1a00009, 0xeb0618b1, 0xe3500c01, 0x31a07000\n"
        ".word 0xe5980000, 0xe2871001, 0xe3a02004, 0xe5903008\n"
        ".word 0xe1a00008, 0xe12fff33, 0xe1a08000, 0xe1a02007\n"
        ".word 0xe1a01009, 0xeb0623fe, 0xe3580000, 0x10480006\n"
        ".word 0xe7c85007, 0x15860000, 0x0a000013, 0xe5845020\n"
        ".word 0xe5845024, 0xeddf8a39, 0xe5845028, 0xe584502c\n"
        ".word 0xedc48a0c, 0xed9f8a36, 0xedc48a0d, 0xedc48a0e\n"
        ".word 0xed848a0f, 0xed848a10, 0xe59f00c8, 0xed848a11\n"
        ".word 0xed848a12, 0xed848a13, 0xed848a14, 0xe5900000\n"
        ".word 0xe3100001, 0x1a000016, 0xea000001, 0xe5865000\n"
        ".word 0xeaffffe9, 0xe59f009c, 0xfa060c19, 0xe3500000\n"
        ".word 0xe320f000, 0x0a00000e, 0xe59f008c, 0xe2801010\n"
        ".word 0xedc08a00, 0xed808a01, 0xed808a02, 0xed808a03\n"
        ".word 0xec818a02, 0xe2801024, 0xed808a06, 0xed808a07\n"
        ".word 0xed808a08, 0xec818a02, 0xed808a0b, 0xe59f0054\n"
        ".word 0xe1a00000, 0xe59f0050, 0xe2849084, 0xe89011ee\n"
        ".word 0xe88911ee, 0xe2801020, 0xe590002c, 0xe891000e\n"
        ".word 0xe58400b0, 0xe28400a4, 0xe880000e, 0xe1a00004\n"
        ".word 0xe5941018, 0xe3811001, 0xe5841018, 0xecbd8b02\n"
        ".word 0xe8bd87f0, 0x40000222, 0x07010000, 0x4e465443\n"
        ".word 0x3f800000, 0x00000000, 0x00476634, 0x004efd6c\n"
    );
}

// DECOMP_FUNC(0x00296a18, 448)
// 110 ARM instructions through unconditional pop; 8 trailing data bytes.
extern "C" __attribute__((naked)) void script_vm_func_00296a18() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d41f0, 0xe1a06000, 0xe2867b0d, 0xe2877f4b\n"
        ".word 0xe59f21a0, 0xe5974000, 0xe2800a03, 0xe2800e53\n"
        ".word 0xe3a08000, 0xe5804000, 0xe2823008, 0xe5871000\n"
        ".word 0xe282c010, 0xe7828006, 0xe2865c35, 0xe7838006\n"
        ".word 0xe78c8006, 0xe1d507fc, 0xe1a04008, 0xe3500000\n"
        ".word 0xda000005, 0xe320f000, 0xeb008964, 0xe1d507fc\n"
        ".word 0xe2844001, 0xe1500004, 0xcafffff9, 0xe1c587bc\n"
        ".word 0xe5970000, 0xe350000e, 0x03a040df, 0x0a000019\n"
        ".word 0xca00000c, 0xe3500001, 0x03a04062, 0x0a000015\n"
        ".word 0xe350000a, 0x03a0409e, 0x0a000012, 0xe350000b\n"
        ".word 0x03a04065, 0x0a00000f, 0xe350000d, 0x03a04066\n"
        ".word 0x0a00000c, 0xea000011, 0xe350000f, 0x03a04068\n"
        ".word 0x0a000008, 0xe3500010, 0x03a0406a, 0x0a000005\n"
        ".word 0xe3500011, 0x03a040e1, 0x0a000002, 0xe3500012\n"
        ".word 0x03a04064, 0x1a000005, 0xe59f10cc, 0xe3a00000\n"
        ".word 0xeb00217f, 0xe20400ff, 0xe320f000, 0xeb008817\n"
        ".word 0xe5970000, 0xe3500014, 0x1a000029, 0xe3a00000\n"
        ".word 0xeb000e25, 0xe3a00000, 0xe320f000, 0xebfff102\n"
        ".word 0xe3a00000, 0xe320f000, 0xeb001dc6, 0xe3a00000\n"
        ".word 0xe320f000, 0xeb001ff0, 0xe3a00000, 0xe320f000\n"
        ".word 0xeb001702, 0xe320f000, 0xe320f000, 0xebfff0d1\n"
        ".word 0xe320f000, 0xe320f000, 0xebfff0c7, 0xe1b04000\n"
        ".word 0xe320f000, 0x0a00000d, 0xeb0047a0, 0xe5900000\n"
        ".word 0xe1540000, 0x8a000009, 0xe3a00013, 0xe5870000\n"
        ".word 0xe3a00090, 0xeb0087f5, 0xe2866b0d, 0xe2866f5a\n"
        ".word 0xe3a01005, 0xe5960000, 0xe8bd41f0, 0xea00018a\n"
        ".word 0xe3a00000, 0xebfffa3d, 0xe8bd41f0, 0xe3a00003\n"
        ".word 0xea00867b, 0xe8bd81f0, 0x00003534, 0x323232ff\n"
    );
}

// DECOMP_FUNC(0x002a043c, 448)
// 107 ARM instructions through unconditional pop; 20 trailing data bytes.
extern "C" __attribute__((naked)) void camp_func_002a043c() {
    asm volatile(
        ".arm\n"
        ".word 0xe59f01a4, 0xe92d47f0, 0xe5905000, 0xeb0002d7\n"
        ".word 0xe280901c, 0xe59f1194, 0xe2850d17, 0xeb0091b4\n"
        ".word 0xe2850c0f, 0xe2800022, 0xe3a01070, 0xe1a0a000\n"
        ".word 0xeb008db5, 0xe2850c0f, 0xe59f1174, 0xe2800092\n"
        ".word 0xeb008db1, 0xe3a07000, 0xe1a08007, 0xe1a04007\n"
        ".word 0xe5950000, 0xe1a01004, 0xebfffa2a, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000022, 0xe1a00004, 0xeb0063ad\n"
        ".word 0xe1a06000, 0xe1d000b0, 0xebfffa13, 0xe3500000\n"
        ".word 0xe320f000, 0x1a000004, 0xe1d600b0, 0xebfff9e7\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000015, 0xe1d900f8\n"
        ".word 0xe3500000, 0x15d61002, 0x11500001, 0x1a000004\n"
        ".word 0xe1d600b0, 0xe0851087, 0xe2811c05, 0xe2877001\n"
        ".word 0xe1c10cb0, 0xe5d62002, 0xe1a01008, 0xe1a0000a\n"
        ".word 0xebfff2db, 0xe3500000, 0xe320f000, 0x1a000004\n"
        ".word 0xe5d60002, 0xe0851088, 0xe2811c0f, 0xe2888001\n"
        ".word 0xe1c102b2, 0xe2840001, 0xe6ff4070, 0xe3540e4b\n"
        ".word 0x9affffd2, 0xe59f30ac, 0xe3a02002, 0xe1a01007\n"
        ".word 0xe2850d17, 0xfb005e6c, 0xe59fa09c, 0xe3a06000\n"
        ".word 0xe1a04006, 0xe1a00004, 0xebfff9aa, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000012, 0xe5d01003, 0xe3110020\n"
        ".word 0x0a00000f, 0xe1d911d5, 0xe3510000, 0xba000003\n"
        ".word 0xe79a1101, 0xe5d00002, 0xe1510000, 0x1a000008\n"
        ".word 0xe6bf0074, 0xebfc03cf, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000003, 0xe0850086, 0xe2800c0f, 0xe2866001\n"
        ".word 0xe1c049b2, 0xe2840001, 0xe6ff4070, 0xe3540f7d\n"
        ".word 0x9affffe3, 0xe2850a01, 0xe5806384, 0xe2850a01\n"
        ".word 0xe2800fdf, 0xe8800180, 0xe8bd87f0, 0x0043dd68\n"
        ".word 0x00000962, 0x000003ea, 0x001f643c, 0x0040333c\n"
    );
}

// DECOMP_FUNC(0x002a37dc, 448)
// 108 ARM instructions through unconditional pop; 16 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_002a37dc() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d41f0, 0xe1a02401, 0xe1a04801, 0xe1a03c21\n"
        ".word 0xed2d8b06, 0xe1a0cc22, 0xe1a02c24, 0xee013a90\n"
        ".word 0xe5801064, 0xe20110ff, 0xee002a10, 0xee001a90\n"
        ".word 0xee01ca10, 0xeeb82a61, 0xed9faa5c, 0xe59f6170\n"
        ".word 0xeef81a40, 0xeeb80a60, 0xeeb81a41, 0xe2861c01\n"
        ".word 0xee228a0a, 0xee219a8a, 0xee609a0a, 0xee618a0a\n"
        ".word 0xec818a04, 0xe590408c, 0xe3540000, 0x159f5148\n"
        ".word 0x1ddfaa50, 0x0a00004b, 0xe5943064, 0xe286cc01\n"
        ".word 0xe1a0100c, 0xe2867e11, 0xe1a08403, 0xe1a02007\n"
        ".word 0xe1a08c28, 0xee008a10, 0xe1a08803, 0xe2860c01\n"
        ".word 0xe1a08c28, 0xee008a90, 0xe1a08c23, 0xeef81a40\n"
        ".word 0xee008a10, 0xe20330ff, 0xeeb82a60, 0xeeb81a40\n"
        ".word 0xee210a8a, 0xee013a90, 0xeef81a61, 0xee610a0a\n"
        ".word 0xee221a0a, 0xee611a8a, 0xedcc0a00, 0xed8c0a01\n"
        ".word 0xe28cc008, 0xec8c1a02, 0xec878a04, 0xed910a00\n"
        ".word 0xedd20a00, 0xee200a20, 0xed810a00, 0xed910a01\n"
        ".word 0xedd20a01, 0xee200a20, 0xed810a01, 0xed910a02\n"
        ".word 0xedd20a02, 0xee200a20, 0xed810a02, 0xed920a03\n"
        ".word 0xedd10a03, 0xee200a80, 0xed810a03, 0xec900a04\n"
        ".word 0xee200a2a, 0xee211a2a, 0xee600aaa, 0xee611aaa\n"
        ".word 0xeebc0ac0, 0xeefc0ae0, 0xee100a10, 0xeebc0ac1\n"
        ".word 0xee101a90, 0xe1a00c00, 0xe20110ff, 0xe1800801\n"
        ".word 0xee102a10, 0xeebc0ae1, 0xe20220ff, 0xe1800402\n"
        ".word 0xee103a10, 0xe20310ff, 0xe1811000, 0xe5940090\n"
        ".word 0xe1d020b4, 0xe0822202, 0xe0852102, 0xe5922030\n"
        ".word 0xe3520000, 0x15900008, 0x112fff32, 0xe59440ac\n"
        ".word 0xe3540000, 0x1affffb3, 0xecbd8b06, 0xe8bd81f0\n"
        ".word 0x3b808081, 0x004ea81c, 0x437f0000, 0x00464110\n"
    );
}

// DECOMP_FUNC(0x002adc74, 448)
// 107 ARM instructions through unconditional pop; 20 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_002adc74() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4fff, 0xe24dd074, 0xe3a04000, 0xe1a06002\n"
        ".word 0xe1a07003, 0xe1a0b001, 0xe28d10a8, 0xe8910700\n"
        ".word 0xebfa617a, 0xe1b05000, 0x0a000030, 0xe3a01e13\n"
        ".word 0xeb005ba1, 0xe1a00005, 0xebfa61ae, 0xe1b05000\n"
        ".word 0x0a00002a, 0xe58d4040, 0xe58d6028, 0xe58d7024\n"
        ".word 0xe59b0008, 0xe3ccc0ff, 0xe28de068, 0xe20000ff\n"
        ".word 0xe89b000a, 0xe180000c, 0xe88e0041, 0xe28d0060\n"
        ".word 0xe28de04c, 0xe880000a, 0xe1a02004, 0xe59b100c\n"
        ".word 0xe58d4048, 0xe59f6120, 0xe88e0006, 0xe3a03002\n"
        ".word 0xe58d2054, 0xe58d2058, 0xe5966010, 0xe3a07001\n"
        ".word 0xe28de010, 0xe58d300c, 0xe58d3000, 0xe28d1048\n"
        ".word 0xe3a0b014, 0xe58d7018, 0xe88e0802, 0xe28de004\n"
        ".word 0xe3a0c010, 0xe88e1001, 0xe28de01c, 0xe59f30dc\n"
        ".word 0xe28d1040, 0xe28d0020, 0xe88e0044, 0xeb002006\n"
        ".word 0xe1a06000, 0xe1b00fa0, 0x0a000002, 0xea00001d\n"
        ".word 0xe59f60bc, 0xea000024, 0xe59f00b8, 0xe59d6040\n"
        ".word 0xeb001fe4, 0xe3500000, 0xe320f000, 0x0a000012\n"
        ".word 0xe59f10a4, 0xe8800042, 0xe1a06000, 0xe88d0700\n"
        ".word 0xe1a01000, 0xe59d2028, 0xe59d3024, 0xe1a00005\n"
        ".word 0xebfa603c, 0xe1a07000, 0xe1b00fa0, 0x03a06000\n"
        ".word 0x0a000008, 0xe5960000, 0xe590102c, 0xe1a00006\n"
        ".word 0xe12fff31, 0xe1a06007, 0xea000002, 0xe59d0040\n"
        ".word 0xef000023, 0xe59f6048, 0xe2060102, 0xe3500000\n"
        ".word 0xa1a04005, 0xa3a06000, 0xaa000003, 0xe5950000\n"
        ".word 0xe5901030, 0xe1a00005, 0xe12fff31, 0xe1b01fa6\n"
        ".word 0xe1a00006, 0x1a000002, 0xe59d0074, 0xe5804000\n"
        ".word 0xe3a00000, 0xe28dd084, 0xe8bd8ff0, 0x0044e650\n"
        ".word 0x2345678a, 0xd8604659, 0x004d4358, 0x00420998\n"
    );
}

// DECOMP_FUNC(0x0033d164, 448)
// 110 ARM instructions through unconditional pop; 8 trailing data bytes.
extern "C" __attribute__((naked)) void camp_func_0033d164() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4070, 0xe1a05000, 0xe3a04000, 0xe2841059\n"
        ".word 0xe3a00014, 0xebfe0954, 0xe1d010f8, 0xe0856204\n"
        ".word 0xee001a10, 0xe284105d, 0xeeb80ac0, 0xed860aca\n"
        ".word 0xe1d000fa, 0xee000a10, 0xe3a00014, 0xeeb80ac0\n"
        ".word 0xed860acb, 0xebfe0948, 0xe1d010f8, 0xe2844001\n"
        ".word 0xe3540004, 0xee001a10, 0xeeb80ac0, 0xed860acc\n"
        ".word 0xe1d000fa, 0xee000a10, 0xeeb80ac0, 0xed860acd\n"
        ".word 0xbaffffe5, 0xe3a01061, 0xe3a00014, 0xebfe093a\n"
        ".word 0xe1d010f8, 0xe3a04000, 0xee001a10, 0xeeb80ac0\n"
        ".word 0xed850ac0, 0xe1d000fa, 0xee000a10, 0xeeb80ac0\n"
        ".word 0xed850ac1, 0xe2641064, 0xe3a00014, 0xebfe092e\n"
        ".word 0xe1d010f8, 0xee001a10, 0xe0851184, 0xe2844001\n"
        ".word 0xe3540003, 0xeeb80ac0, 0xed810ac2, 0xe1d000fa\n"
        ".word 0xee000a10, 0xeeb80ac0, 0xed810ac3, 0xbafffff0\n"
        ".word 0xedd50ac4, 0xed950ac6, 0xe595031c, 0xe3a04000\n"
        ".word 0xee700a60, 0xe5850324, 0xee300a80, 0xed850ac8\n"
        ".word 0xe2841065, 0xe3a00014, 0xebfe0917, 0xe1d020f8\n"
        ".word 0xe0851184, 0xe2844001, 0xee002a10, 0xe3540004\n"
        ".word 0xeeb80ac0, 0xed810ada, 0xe1d000fa, 0xee000a10\n"
        ".word 0xeeb80ac0, 0xed810adb, 0xbafffff0, 0xe3a0106a\n"
        ".word 0xe3a00014, 0xebfe0908, 0xe1d000fa, 0xe3a01069\n"
        ".word 0xee000a10, 0xe3a00014, 0xeeb80ac0, 0xed850ae3\n"
        ".word 0xebfe0901, 0xe1d000fa, 0xe3a01fbd, 0xee000a10\n"
        ".word 0xe1a00005, 0xeeb80ac0, 0xed850ae2, 0xebfe1e12\n"
        ".word 0xe3e00000, 0xe3a01000, 0xe58502f8, 0xed9f0a09\n"
        ".word 0xe58512f4, 0xe58502fc, 0xed850ae6, 0xed850ae7\n"
        ".word 0xed850ae8, 0xed9f0a04, 0xe3a00004, 0xed850ae5\n"
        ".word 0xe5850390, 0xe8bd8070, 0x00000000, 0x40800000\n"
    );
}

// DECOMP_FUNC(0x00290874, 452)
// 112 ARM instructions through unconditional pop; 4 trailing data bytes.
extern "C" __attribute__((naked)) void script_vm_func_00290874() {
    asm volatile(
        ".arm\n"
        ".word 0xe59f01b8, 0xe92d4070, 0xe5904000, 0xe5900000\n"
        ".word 0xe2845c05, 0xe5d415c4, 0xe59005d0, 0xe3510000\n"
        ".word 0x0a00000f, 0xe3500001, 0x03a0006c, 0x0b00a0b4\n"
        ".word 0xe59405d0, 0xe3500002, 0x1a00005f, 0xe59405c8\n"
        ".word 0xe3500000, 0x03a0006d, 0x0b00a0ad, 0xe59405c8\n"
        ".word 0xe3500001, 0x1a000058, 0xe8bd4070, 0xe3a0006e\n"
        ".word 0xea00a0a7, 0xe3500001, 0x03a0006f, 0x0b00a0a4\n"
        ".word 0xe59405d0, 0xe3500002, 0x1a000007, 0xe59405c8\n"
        ".word 0xe3500000, 0x03a00070, 0x0b00a09d, 0xe59405c8\n"
        ".word 0xe3500001, 0x03a00071, 0x0b00a099, 0xe59405d0\n"
        ".word 0xe3500003, 0x1a00000b, 0xe59405c8, 0xe3500000\n"
        ".word 0x03a00072, 0x0b00a092, 0xe59405c8, 0xe3500001\n"
        ".word 0x03a00073, 0x0b00a08e, 0xe59405c8, 0xe3500002\n"
        ".word 0x03a00074, 0x0b00a08a, 0xe5d500f1, 0xe3500000\n"
        ".word 0x0a000009, 0xe3a03001, 0xe3a02032, 0xe1a01003\n"
        ".word 0xe3a00005, 0xeb009f89, 0xe3a03001, 0xe3a02000\n"
        ".word 0xe3a01012, 0xe3a00002, 0xeb009f84, 0xe2840e66\n"
        ".word 0xeb003a35, 0xe1a06000, 0xe2840e66, 0xeb003a2c\n"
        ".word 0xe0800006, 0xe0840080, 0xe2800c07, 0xe1d048ba\n"
        ".word 0xebffff3a, 0xe1500004, 0xe320f000, 0x1a000007\n"
        ".word 0xe3a03001, 0xe3a02033, 0xe1a01003, 0xe3a00005\n"
        ".word 0xeb009f72, 0xe320f000, 0xe320f000, 0xea000007\n"
        ".word 0xe5d500f1, 0xe3500000, 0x1a000004, 0xe3a03001\n"
        ".word 0xe3a02031, 0xe1a01003, 0xe3a00005, 0xeb009f67\n"
        ".word 0xe320f000, 0xebfffeb4, 0xe3500000, 0xe3a03001\n"
        ".word 0x0a000004, 0xe8bd4070, 0xe3a02033, 0xe3a01004\n"
        ".word 0xe3a00002, 0xea009f5d, 0xe8bd4070, 0xe3a02000\n"
        ".word 0xe3a01012, 0xe3a00002, 0xea009f58, 0xe8bd8070\n"
        ".word 0x0043dd50\n"
    );
}

// DECOMP_FUNC(0x0038ba94, 452)
// 110 ARM instructions through unconditional pop; 12 trailing data bytes.
extern "C" __attribute__((naked)) void script_vm_func_0038ba94() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d40f0, 0xe1a05000, 0xe5900048, 0xe24dd08c\n"
        ".word 0xe3500000, 0x1595104c, 0x13510000, 0x0a000063\n"
        ".word 0xe5d51045, 0xe3a06000, 0xe3510000, 0x0a000003\n"
        ".word 0xe3a01000, 0xebfc8209, 0xebfcd4f2, 0xe1a06000\n"
        ".word 0xe5d50045, 0xe3500000, 0x15950048, 0x13500000\n"
        ".word 0x0a000056, 0xe3a01000, 0xebfc8200, 0xe320f000\n"
        ".word 0xe320f000, 0xebfcd4d3, 0xe2507000, 0xe3a04000\n"
        ".word 0x9a00004e, 0xe0860304, 0xe1d000d0, 0xe3500030\n"
        ".word 0x379ff100, 0xea000046, 0x0038bbdc, 0x0038bbdc\n"
        ".word 0x0038bbdc, 0x0038bbdc, 0x0038bbdc, 0x0038bbdc\n"
        ".word 0x0038bbdc, 0x0038bc38, 0x0038bc38, 0x0038bc38\n"
        ".word 0x0038bc38, 0x0038bbdc, 0x0038bc38, 0x0038bc38\n"
        ".word 0x0038bc38, 0x0038bc38, 0x0038bc38, 0x0038bc38\n"
        ".word 0x0038bbdc, 0x0038bbdc, 0x0038bc38, 0x0038bbdc\n"
        ".word 0x0038bc38, 0x0038bbdc, 0x0038bbdc, 0x0038bbdc\n"
        ".word 0x0038bbdc, 0x0038bbdc, 0x0038bbdc, 0x0038bc38\n"
        ".word 0x0038bc38, 0x0038bc38, 0x0038bc38, 0x0038bbdc\n"
        ".word 0x0038bbdc, 0x0038bbdc, 0x0038bbdc, 0x0038bbdc\n"
        ".word 0x0038bbdc, 0x0038bbdc, 0x0038bbdc, 0x0038bbdc\n"
        ".word 0x0038bbdc, 0x0038bbdc, 0x0038bbdc, 0x0038bbdc\n"
        ".word 0x0038bbdc, 0x0038bbdc, 0xe3a01080, 0xe28d0008\n"
        ".word 0xebfce3d1, 0xe0860304, 0xe2803001, 0xe2852024\n"
        ".word 0xe28f1050, 0xe28d0008, 0xfafccafe, 0xe595104c\n"
        ".word 0xe3a00080, 0xe3a03001, 0xe0812204, 0xe88d0005\n"
        ".word 0xe59f0038, 0xe28d1008, 0xe5900000, 0xebfff9cf\n"
        ".word 0xe595104c, 0xe3a0200c, 0xe0822204, 0xe3a00001\n"
        ".word 0xe7c10002, 0xe2844001, 0xe1540007, 0x3affffb0\n"
        ".word 0xe28dd08c, 0xe8bd80f0, 0x252f7325, 0x00000073\n"
        ".word 0x00433130\n"
    );
}

// DECOMP_FUNC(0x0022d994, 456)
// 106 ARM instructions through unconditional pop; 32 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_0022d994() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe1a04000, 0xe2811b01, 0xe24dd00c\n"
        ".word 0xe1a05002, 0xe1a08003, 0xe281102f, 0xe28000c8\n"
        ".word 0xeb024743, 0xe1d060f8, 0xe1d070fa, 0xe2841f85\n"
        ".word 0xe1a00001, 0xed900a08, 0xeb02474f, 0xe59f1164\n"
        ".word 0xe1a03007, 0xe1a02006, 0xe28400c8, 0xe58d5000\n"
        ".word 0xeb000d4b, 0xe59f1150, 0xe1a03007, 0xe1a02006\n"
        ".word 0xe28400c8, 0xe58d5000, 0xeb000d45, 0xe59f113c\n"
        ".word 0xe1a03007, 0xe1a02006, 0xe28400c8, 0xe58d5000\n"
        ".word 0xeb000d3f, 0xed9f0a4a, 0xeb02473b, 0xe3a09001\n"
        ".word 0xe59f1120, 0xe1a03007, 0xe1a02006, 0xe28400c8\n"
        ".word 0xe88d0220, 0xeb0010c8, 0xe3580000, 0xe59f8108\n"
        ".word 0xe1a03007, 0xe1a02006, 0x0a000004, 0xe18812c8\n"
        ".word 0xe28400c8, 0xe88d0220, 0xeb0010bf, 0xea000003\n"
        ".word 0xe1a01008, 0xe28400c8, 0xe88d0220, 0xeb0010ba\n"
        ".word 0xe1a01008, 0xe28400c8, 0xeb024711, 0xe590100c\n"
        ".word 0xe1d0c0f8, 0xe1d080fa, 0xe1d120f0, 0xe1d130f2\n"
        ".word 0xe08c0006, 0xe0881007, 0xeb000e52, 0xe59fb0ac\n"
        ".word 0xe28400c8, 0xe1a0100b, 0xeb024705, 0xe1a08000\n"
        ".word 0xe284ae2a, 0xe1a0000a, 0xeb02452e, 0xe1d810b4\n"
        ".word 0xe0800006, 0xe3c11902, 0xe0406001, 0xe1a0000a\n"
        ".word 0xeb024525, 0xe0803007, 0xe1a02006, 0xe1a0100b\n"
        ".word 0xe28400c8, 0xe88d0220, 0xeb00109b, 0xe59f0060\n"
        ".word 0xe5901000, 0xe3a00000, 0xe2814a01, 0xe2844fc3\n"
        ".word 0xe5941000, 0xe0842101, 0xe5921008, 0xe5820008\n"
        ".word 0xe5d42018, 0xe3520000, 0x03510000, 0x0a000003\n"
        ".word 0xe594101c, 0xe12fff31, 0xe3a00000, 0xe5c40018\n"
        ".word 0xe28dd00c, 0xe8bd8ff0, 0x00000426, 0x00000427\n"
        ".word 0x00000428, 0x3f800000, 0x00000429, 0x0000042a\n"
        ".word 0x0000042c, 0x0044ea00\n"
    );
}

// DECOMP_FUNC(0x002313ec, 456)
// 111 ARM instructions through unconditional pop; 12 trailing data bytes.
extern "C" __attribute__((naked)) void func_002313ec() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d47f0, 0xe1a04002, 0xe0802004, 0xe3520000\n"
        ".word 0xed9f0a69, 0xb3a00000, 0xe1a05003, 0xb1a04000\n"
        ".word 0xba000007, 0xe3500000, 0xb0844000, 0xb3a00000\n"
        ".word 0xba000003, 0xe3500d05, 0xc3a00000, 0xc1a04000\n"
        ".word 0xca000007, 0xe0802004, 0xe3520d05, 0xda000004\n"
        ".word 0xee000a90, 0xeef80ae0, 0xee700a60, 0xeefd0ae0\n"
        ".word 0xee104a90, 0xe0812005, 0xe3520000, 0xeddf0a53\n"
        ".word 0xb3a05000, 0xba000002, 0xe3510000, 0xb0835001\n"
        ".word 0xaa000001, 0xe3a01000, 0xea000003, 0xe35100f0\n"
        ".word 0xc3a01000, 0xc1a05001, 0xca000007, 0xe0812005\n"
        ".word 0xe35200f0, 0xda000004, 0xee011a10, 0xeeb81ac1\n"
        ".word 0xee301ac1, 0xeebd1ac1, 0xee115a10, 0xe0800004\n"
        ".word 0xee010a10, 0xe0811005, 0xee011a90, 0xe59fa0f0\n"
        ".word 0xe3a00003, 0xe3a07000, 0xeeb81ac1, 0xe59a1000\n"
        ".word 0xeef81ae1, 0xe2816a01, 0xe2866fc3, 0xe5961000\n"
        ".word 0xee300a41, 0xe0862101, 0xee301ae1, 0xe5921008\n"
        ".word 0xe5820008, 0xe5d62018, 0xe3520000, 0x03510003\n"
        ".word 0xeefd0ac0, 0xeebd0ac1, 0xee109a90, 0xee108a10\n"
        ".word 0x0a000002, 0xe596101c, 0xe12fff31, 0xe5c67018\n"
        ".word 0xe59a6000, 0xe1a01008, 0xe1a00009, 0xe1800801\n"
        ".word 0xe2866a01, 0xe2866fcb, 0xe5961000, 0xe0862101\n"
        ".word 0xe5921008, 0xe5820008, 0xe5d62018, 0xe3520000\n"
        ".word 0x01510000, 0x0a000002, 0xe596101c, 0xe12fff31\n"
        ".word 0xe5c67018, 0xe59a6000, 0xe1a01005, 0xe1a00004\n"
        ".word 0xe1800801, 0xe2864a01, 0xe2844fd3, 0xe5941000\n"
        ".word 0xe0842101, 0xe5921008, 0xe5820008, 0xe5d42018\n"
        ".word 0xe3520000, 0x01510000, 0x0a000002, 0xe594101c\n"
        ".word 0xe12fff31, 0xe5c47018, 0xe8bd87f0, 0x43a00000\n"
        ".word 0x43700000, 0x0044ea00\n"
    );
}

// DECOMP_FUNC(0x0023adc4, 456)
// 109 ARM instructions through unconditional bx; 20 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_0023adc4() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d0030, 0xe5d0201c, 0xe5903004, 0xe59fc1a8\n"
        ".word 0xe3520000, 0xeddf3a66, 0xe5932010, 0xed9c2a00\n"
        ".word 0xeddf1a64, 0xe1d241f4, 0xe1d251f6, 0xe1d232f2\n"
        ".word 0xee004a90, 0xee015a10, 0xe1d2c2b6, 0xeef80ae0\n"
        ".word 0xeeb81ac1, 0xee700a82, 0xee303ac1, 0x0a000013\n"
        ".word 0xe5904008, 0xee003a90, 0xe1d051fa, 0xe594400c\n"
        ".word 0xee015a10, 0xeeb84ae0, 0xedd40a06, 0xedd42a05\n"
        ".word 0xee103a90, 0xeef84ac1, 0xeeb81ae0, 0xe04c3003\n"
        ".word 0xee023a10, 0xeef80ae2, 0xeeb82ac2, 0xee222a23\n"
        ".word 0xee342a82, 0xee342a02, 0xee322a01, 0xea00000d\n"
        ".word 0xee00ca90, 0xe1d242b4, 0xed904a04, 0xedd02a05\n"
        ".word 0xe083300c, 0xee023a10, 0xeeb81a60, 0xee004a90\n"
        ".word 0xeeb04ac4, 0xeef02ae2, 0xeeb82ac2, 0xeef80a60\n"
        ".word 0xee021aa1, 0xee440a21, 0xe3a03000, 0xeef40ac1\n"
        ".word 0xeef1fa10, 0xda000003, 0xee700ac1, 0xee600aa3\n"
        ".word 0xeefd0ae0, 0xee103a90, 0xee332a42, 0xeddf0a2f\n"
        ".word 0xee013a10, 0xeeb81ac1, 0xee321a41, 0xee301a81\n"
        ".word 0xed811a01, 0xe5d0301c, 0xe3530000, 0x05d0301d\n"
        ".word 0x03530000, 0x1a000002, 0xed902a05, 0xee021a21\n"
        ".word 0xed811a01, 0xee211a00, 0xe59f3084, 0xedd31a00\n"
        ".word 0xee311a21, 0xecc10a02, 0xe5d0301c, 0xe1d2c2b4\n"
        ".word 0xe3530000, 0xe1d232f0, 0xe1d221f2, 0xe08330ac\n"
        ".word 0xe0422003, 0xee012a10, 0xeef81ac1, 0xeeb01a60\n"
        ".word 0xee311a61, 0xed811a00, 0x0a000005, 0xe1d001f8\n"
        ".word 0xee010a90, 0xeef81ae1, 0xee311a21, 0xed811a00\n"
        ".word 0xea000002, 0xedd01a04, 0xee311a21, 0xed811a00\n"
        ".word 0xee210a00, 0xedc10a02, 0xed810a00, 0xe8bd0030\n"
        ".word 0xe12fff1e, 0x3f000000, 0x40000000, 0x003ff7c4\n"
        ".word 0x00000000, 0x00433d98\n"
    );
}

// DECOMP_FUNC(0x003cf20c, 456)
// 113 ARM instructions through unconditional pop; 4 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_003cf20c() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff7, 0xe24dd008, 0xe1a06000, 0xe5900000\n"
        ".word 0xe2800901, 0xe2800e4a, 0xe5900000, 0xe3100004\n"
        ".word 0x1a000065, 0xe3a0a001, 0xe3a07004, 0xe3a04000\n"
        ".word 0xe1a0900a, 0xe3a00010, 0xebfbdd80, 0xe1a0b000\n"
        ".word 0xe3a08000, 0xe5960000, 0xe0841204, 0xe0811304\n"
        ".word 0xe2800d7f, 0xe5900000, 0xe0805181, 0xe5950000\n"
        ".word 0xe3100001, 0x0a000009, 0xe3100040, 0x1a000007\n"
        ".word 0xe59f014c, 0xe19000b5, 0xe3100b01, 0x03100004\n"
        ".word 0x1a000002, 0xe3100c02, 0x13a09000, 0x0a000006\n"
        ".word 0xe2844001, 0xe1570004, 0xcaffffe9, 0xe35a0000\n"
        ".word 0x03590000, 0x1a000040, 0xea000013, 0xe1d500f8\n"
        ".word 0xe3e03000, 0xe3a02002, 0xe3a0100f, 0xebf9dbf4\n"
        ".word 0xe58d0000, 0xe1d500f8, 0xe3a0100f, 0xebf96df3\n"
        ".word 0xe1a01000, 0xe59d0000, 0xe1800001, 0xe3100817\n"
        ".word 0x1affffea, 0xe1d500f8, 0xe2881001, 0xe3a0a000\n"
        ".word 0xe78b0108, 0xe6af8071, 0xeaffffe4, 0xe3580000\n"
        ".word 0x0a000029, 0xe3a00063, 0xebf9be48, 0xe350000f\n"
        ".word 0xe320f000, 0xba000005, 0xe5960000, 0xe2800b11\n"
        ".word 0xe28000a8, 0xe5900000, 0xe3100401, 0x0a00001e\n"
        ".word 0xe2480001, 0xe6ff0070, 0xebf9be3c, 0xe5961000\n"
        ".word 0xe79b2100, 0xe3a00001, 0xe2811b07, 0xe2811fa6\n"
        ".word 0xe0823102, 0xe5911000, 0xe0832302, 0xe58d0000\n"
        ".word 0xe0814102, 0xe59d0010, 0xe59d100c, 0xe3a03c02\n"
        ".word 0xe1a02004, 0xebf9df02, 0xe1d416f2, 0xe5960000\n"
        ".word 0xebface00, 0xe1a01000, 0xe2800c01, 0xe3a02000\n"
        ".word 0xe1c02cb8, 0xe1d02cba, 0xe3822010, 0xe1c02cba\n"
        ".word 0xe3a02001, 0xe3a0001c, 0xebf96cec, 0xe28dd014\n"
        ".word 0xe1a0000b, 0xe8bd4ff0, 0xeafa06fa, 0xe28dd014\n"
        ".word 0xe8bd8ff0, 0x000001c6\n"
    );
}

// DECOMP_FUNC(0x00256ffc, 460)
// 114 ARM instructions through unconditional bx; 4 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_00256ffc() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d0070, 0xe5902010, 0xe590c000, 0xe592300c\n"
        ".word 0xe5934010, 0xe3140201, 0x1a000068, 0xe5924008\n"
        ".word 0xe3540000, 0xc2440001, 0xca000014, 0xe5924004\n"
        ".word 0xe2844001, 0xe5824004, 0xe593500c, 0xe1550004\n"
        ".word 0x8a000008, 0xe5935010, 0xe3a04000, 0xe3150010\n"
        ".word 0x05824004, 0x0a000003, 0xe1c041b4, 0xe593000c\n"
        ".word 0xe2400001, 0xe5820004, 0xe5920004, 0xe5924010\n"
        ".word 0xe3a05012, 0xe0800080, 0xe0850180, 0xe19400f0\n"
        ".word 0xe5820008, 0xe5924004, 0xe5930010, 0xe5922010\n"
        ".word 0xe0845084, 0xe3100001, 0xe0820185, 0x03e02000\n"
        ".word 0x0a000003, 0xe59c2000, 0xe5935004, 0xe0822005\n"
        ".word 0xe7922104, 0xe581202c, 0xe59c2014, 0xe1d0c1f0\n"
        ".word 0xe5933010, 0xe792210c, 0xe3130002, 0x13a03002\n"
        ".word 0xe2824014, 0xec940a02, 0x11c132b8, 0xeeb80ac0\n"
        ".word 0xeef80ae0, 0x1a000003, 0xe3130004, 0x13a03003\n"
        ".word 0x03a03001, 0xe1c132b8, 0xe5903014, 0xed9f3a31\n"
        ".word 0xe5813010, 0xe1d060f8, 0xe1d040f0, 0xe1d050f2\n"
        ".word 0xe1d030f4, 0xe1a06246, 0xee016a10, 0xee015a90\n"
        ".word 0xe1d0c0f6, 0xee023a10, 0xee02ca90, 0xeef83ac1\n"
        ".word 0xee014a10, 0xeef81ae1, 0xeeb82ac2, 0xeef82ae2\n"
        ".word 0xeeb81ac1, 0xee834a80, 0xee611a83, 0xed814a06\n"
        ".word 0xe1d030fa, 0xee211a03, 0xe1a03243, 0xee033a10\n"
        ".word 0xee712ae2, 0xeeb83ac3, 0xeec33a20, 0xee313a42\n"
        ".word 0xedc13a07, 0xe1d030fc, 0xe1a03243, 0xee023a10\n"
        ".word 0xe2813030, 0xeeb82ac2, 0xeec23a00, 0xedc13a08\n"
        ".word 0xe1d000fe, 0xe1a00240, 0xee020a10, 0xeeb82ac2\n"
        ".word 0xeec23a20, 0xedc13a09, 0xed813a00, 0xedc12a01\n"
        ".word 0xec830a02, 0xe2813008, 0xec831a02, 0xe5812014\n"
        ".word 0xe8bd0070, 0xe12fff1e, 0x3f000000\n"
    );
}

// DECOMP_FUNC(0x001f6528, 464)
// 107 ARM instructions through unconditional pop; 36 trailing data bytes.
extern "C" __attribute__((naked)) void func_001f6528() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d47f0, 0xe1a07000, 0xed2d8b02, 0xe5905024\n"
        ".word 0xe28540c0, 0xe59580b8, 0xe2986000, 0x1597601c\n"
        ".word 0x13560000, 0x1a00000c, 0xe2840010, 0xed9f0a5e\n"
        ".word 0xeddf0a5e, 0xed840a06, 0xed9f1a5d, 0xed840a07\n"
        ".word 0xeddf1a5c, 0xed9f2a5c, 0xecc00a02, 0xe2840020\n"
        ".word 0xecc01a02, 0xe5950028, 0xe5840004, 0xe1580006\n"
        ".word 0xb3a00000, 0xb5c40003, 0xba00004d, 0xe1a03008\n"
        ".word 0xe1a02006, 0xe2851024, 0xe1a00005, 0xeb01ccd2\n"
        ".word 0xe1a09000, 0xe5970010, 0xeb018417, 0xe59f712c\n"
        ".word 0xe2871c01, 0xe2870e11, 0xec910a04, 0xec800a04\n"
        ".word 0xe1a00009, 0xeb018410, 0xed970a40, 0xedd70a44\n"
        ".word 0xe2870c01, 0xee200a20, 0xed870a40, 0xed970a41\n"
        ".word 0xedd70a45, 0xee200a20, 0xed870a41, 0xed970a42\n"
        ".word 0xedd70a46, 0xee200a20, 0xed870a42, 0xedd70a47\n"
        ".word 0xed970a43, 0xee200a20, 0xed870a43, 0xed9f0a34\n"
        ".word 0xecd00a04, 0xee600a80, 0xee211a00, 0xee611a80\n"
        ".word 0xee222a00, 0xeefc0ae0, 0xeebc0ac1, 0xee100a90\n"
        ".word 0xeefc0ae1, 0xee101a10, 0xeebc0ac2, 0xe1a00c00\n"
        ".word 0xe20130ff, 0xe1800803, 0xee102a90, 0xee101a10\n"
        ".word 0xe20220ff, 0xe20110ff, 0xe1800402, 0xe1800001\n"
        ".word 0xe6bf1f30, 0xe6bf3f30, 0xe1a02821, 0xe1a01423\n"
        ".word 0xe6bf3f30, 0xe6bf0f30, 0xe1a03c23, 0xe5c43000\n"
        ".word 0xe5c42001, 0xe5c41002, 0xe5c40003, 0xe1a02008\n"
        ".word 0xe1a01006, 0xe2850034, 0xeb01cc30, 0xed9f8a11\n"
        ".word 0xeddf0a11, 0xe1a02008, 0xe1a01006, 0xee400a08\n"
        ".word 0xe2850060, 0xedc40a03, 0xeb01cc28, 0xee200a08\n"
        ".word 0xed840a02, 0xecbd8b02, 0xe8bd87f0, 0x00000000\n"
        ".word 0x43480000, 0x42f00000, 0x43c80000, 0x43700000\n"
        ".word 0x004ea81c, 0x437f0000, 0x3c23d70a, 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x00290a68, 464)
// 104 ARM instructions through unconditional pop; 48 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_00290a68() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d47f0, 0xe1b08001, 0x159f4190, 0x159fa190\n"
        ".word 0xe1a09000, 0xe1a07001, 0xe3a05000, 0x0a00001a\n"
        ".word 0xe1540007, 0xca000057, 0xe1a01004, 0xe1a00008\n"
        ".word 0xeb00d5af, 0xe1b06000, 0xe320f000, 0x0a000015\n"
        ".word 0xe3560001, 0x0a000019, 0xe3560002, 0x0a00001d\n"
        ".word 0xe3560003, 0x0a000021, 0xe3560004, 0x0a000025\n"
        ".word 0xe3560005, 0x0a000029, 0xe3560006, 0x0a00002d\n"
        ".word 0xe3560007, 0x0a000031, 0xe3560008, 0x0a000035\n"
        ".word 0xe3560009, 0x0a000039, 0xea00003c, 0xe8bd47f0\n"
        ".word 0xe28f1e11, 0xea00b73c, 0xe0890005, 0xe28f1f41\n"
        ".word 0xfa00b73b, 0xe0855000, 0xe320f000, 0xea000033\n"
        ".word 0xe0890005, 0xe28f10f0, 0xfa00b735, 0xe0855000\n"
        ".word 0xe320f000, 0xea00002d, 0xe0890005, 0xe28f10dc\n"
        ".word 0xfa00b72f, 0xe0855000, 0xe320f000, 0xea000027\n"
        ".word 0xe0890005, 0xe28f10c8, 0xfa00b729, 0xe0855000\n"
        ".word 0xe320f000, 0xea000021, 0xe0890005, 0xe28f10b4\n"
        ".word 0xfa00b723, 0xe0855000, 0xe320f000, 0xea00001b\n"
        ".word 0xe0890005, 0xe28f10a0, 0xfa00b71d, 0xe0855000\n"
        ".word 0xe320f000, 0xea000015, 0xe0890005, 0xe28f108c\n"
        ".word 0xfa00b717, 0xe0855000, 0xe320f000, 0xea00000f\n"
        ".word 0xe0890005, 0xe28f1078, 0xfa00b711, 0xe0855000\n"
        ".word 0xe320f000, 0xea000009, 0xe0890005, 0xe28f1064\n"
        ".word 0xfa00b70b, 0xe0855000, 0xe320f000, 0xea000003\n"
        ".word 0xe0890005, 0xe28f1050, 0xfa00b705, 0xe0855000\n"
        ".word 0xe0000694, 0xe0488000, 0xe0c1049a, 0xe1a00141\n"
        ".word 0xe0404fc1, 0xe3540000, 0xcaffffa0, 0xe8bd87f0\n"
        ".word 0x05f5e100, 0x66666667, 0x00004f82, 0x00005082\n"
        ".word 0x00005182, 0x00005282, 0x00005382, 0x00005482\n"
        ".word 0x00005582, 0x00005682, 0x00005782, 0x00005882\n"
    );
}

// DECOMP_FUNC(0x002c2210, 468)
// 109 ARM instructions through unconditional pop; 32 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_002c2210() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4070, 0xe1a06001, 0xe59f11a4, 0xe1a04000\n"
        ".word 0xed2d8b02, 0xeb000a41, 0xe3a00000, 0xe5c40001\n"
        ".word 0xe59f0198, 0xed9f8a63, 0xeddf8a63, 0xe5900000\n"
        ".word 0xe3100001, 0x1a000012, 0xe59f0180, 0xfafff7a0\n"
        ".word 0xe3500000, 0x0a00000e, 0xe59f0174, 0xe2801010\n"
        ".word 0xedc08a00, 0xed808a01, 0xed808a02, 0xed808a03\n"
        ".word 0xec818a02, 0xe2801024, 0xed808a06, 0xed808a07\n"
        ".word 0xed808a08, 0xec818a02, 0xed808a0b, 0xe59f013c\n"
        ".word 0xe1a00000, 0xe59f1138, 0xe2840038, 0xebfff784\n"
        ".word 0xe59f5130, 0xe5950000, 0xe3100001, 0x1a000017\n"
        ".word 0xe2850000, 0xfafff786, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000012, 0xe59f0110, 0xe2801010, 0xedc08a00\n"
        ".word 0xed808a01, 0xed808a02, 0xed808a03, 0xec818a02\n"
        ".word 0xe2801024, 0xed808a06, 0xed808a07, 0xed808a08\n"
        ".word 0xec818a02, 0xed808a0b, 0xed808a0c, 0xed808a0d\n"
        ".word 0xe2800038, 0xec808a02, 0xe2850000, 0xe1a00000\n"
        ".word 0xe59f10c4, 0xe28400a8, 0xebfff738, 0xe5950000\n"
        ".word 0xe3100001, 0x1a000017, 0xe59f00a8, 0xfafff768\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000012, 0xe59f0098\n"
        ".word 0xe2801010, 0xedc08a00, 0xed808a01, 0xed808a02\n"
        ".word 0xed808a03, 0xec818a02, 0xe2801024, 0xed808a06\n"
        ".word 0xed808a07, 0xed808a08, 0xec818a02, 0xed808a0b\n"
        ".word 0xed808a0c, 0xed808a0d, 0xe2800038, 0xec808a02\n"
        ".word 0xe59f0050, 0xe1a00000, 0xe59f104c, 0xe28400e8\n"
        ".word 0xebfff71a, 0xed9f8a11, 0xe2845b01, 0xe3560000\n"
        ".word 0xed858a26, 0xe5c46000, 0x0a000003, 0xe2840e4a\n"
        ".word 0xebf96ac7, 0xed858a41, 0xedc58a40, 0xecbd8b02\n"
        ".word 0xe8bd8070, 0x00000508, 0x00000000, 0x3f800000\n"
        ".word 0x00476634, 0x004efd6c, 0x00476638, 0x004efd9c\n"
        ".word 0x40a00000\n"
    );
}

// DECOMP_FUNC(0x0034ebc8, 468)
// 114 ARM instructions through unconditional pop; 12 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_0034ebc8() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d40f0, 0xe24dd014, 0xe59f61b8, 0xe5960004\n"
        ".word 0xe3500000, 0x0a000069, 0xe59f01ac, 0xebfdd3af\n"
        ".word 0xe5960014, 0xe3a04000, 0xe3500000, 0x9a000009\n"
        ".word 0xe5960008, 0xe0641184, 0xe7900201, 0xe3500000\n"
        ".word 0x13a01001, 0x1bf82df8, 0xe5960014, 0xe2844001\n"
        ".word 0xe1540000, 0x3afffff5, 0xe59f016c, 0xebfdd37e\n"
        ".word 0xe3a07000, 0xe5c67000, 0xe59f5160, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1a03007, 0xe5952000, 0xe88d0007\n"
        ".word 0xe3a02001, 0xe28d1008, 0xe28d000c, 0xebfdd5a8\n"
        ".word 0xe1b01fa0, 0xe320f000, 0x1bfdda00, 0xe3a00001\n"
        ".word 0xe5c50004, 0xe59f0124, 0xebfdd55c, 0xe5950000\n"
        ".word 0xe59f4118, 0xe3500000, 0x0a000001, 0xef000023\n"
        ".word 0xe5847000, 0xe5960010, 0xebfdd532, 0xe5964010\n"
        ".word 0xe3540000, 0x0a000004, 0xe1a00004, 0xebfdd52d\n"
        ".word 0xe1a00004, 0xe320f000, 0xebfd8e1a, 0xe5867010\n"
        ".word 0xe596000c, 0xebfdd5a7, 0xe586700c, 0xe5960014\n"
        ".word 0xe3a04000, 0xe3500000, 0x8a000002, 0xea00001b\n"
        ".word 0xe3540000, 0xba000016, 0xe1540000, 0x2a000013\n"
        ".word 0xe59f00a4, 0xebfdd36d, 0xe5961008, 0xe0640184\n"
        ".word 0xe0815200, 0xe5950000, 0xe3500000, 0x0a000001\n"
        ".word 0xebfdba44, 0xe5857000, 0xe5951004, 0xe3510000\n"
        ".word 0x0a000004, 0xe5960004, 0xe5902000, 0xe5922004\n"
        ".word 0xe12fff32, 0xe5857004, 0xe59f005c, 0xebfdd33a\n"
        ".word 0xe5960014, 0xe2844001, 0xe1540000, 0x3affffe3\n"
        ".word 0xe59f1044, 0xe3e00000, 0xe5810008, 0xe5960004\n"
        ".word 0xe5901000, 0xe5912004, 0xe5961008, 0xe12fff32\n"
        ".word 0xe5867004, 0xebf70439, 0xe320f000, 0xe320f000\n"
        ".word 0xebf7037b, 0xe28dd014, 0xe8bd40f0, 0xeaf70384\n"
        ".word 0xe28dd014, 0xe8bd80f0, 0x0044d0f8, 0x004c40f8\n"
        ".word 0x0044d128\n"
    );
}

// DECOMP_FUNC(0x002eb39c, 472)
// 115 ARM instructions through unconditional pop; 12 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_002eb39c() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4fff, 0xe24dd00c, 0xe1a06000, 0xe28d0040\n"
        ".word 0xe1a0b002, 0xe8900780, 0xe59f01ac, 0xe5904000\n"
        ".word 0xe59d0010, 0xebff152d, 0xe1a05000, 0xe59d0010\n"
        ".word 0xebff47a2, 0xe5941000, 0xe1a02000, 0xe2813004\n"
        ".word 0xe28f1f62, 0xe1a00003, 0xfaff4d04, 0xe59d0010\n"
        ".word 0xe3a01000, 0xebff470a, 0xe5941000, 0xe1a02000\n"
        ".word 0xe281302c, 0xe28f1f59, 0xe1a00003, 0xfaff4cfb\n"
        ".word 0xe59d0010, 0xebfece15, 0xe5942000, 0xe59d1018\n"
        ".word 0xe5c20024, 0xe5942000, 0xe5d50002, 0xe5820028\n"
        ".word 0xe1d502b4, 0xe5942000, 0xe1a00520, 0xe5c2004c\n"
        ".word 0xe1d502b6, 0xe5942000, 0xe1a00520, 0xe5c2004d\n"
        ".word 0xe1d502b8, 0xe5942000, 0xe1a00520, 0xe5c2004e\n"
        ".word 0xe1d502ba, 0xe5942000, 0xe1a00520, 0xe5c2004f\n"
        ".word 0xe1d502bc, 0xe5942000, 0xe1a00520, 0xe5c20050\n"
        ".word 0xe1d502be, 0xe5942000, 0xe1a00520, 0xe5c20051\n"
        ".word 0xe1d503b0, 0xe5942000, 0xe1a00520, 0xe5c20052\n"
        ".word 0xe1d503b2, 0xe5942000, 0xe1a00520, 0xe5c20053\n"
        ".word 0xe5940000, 0xe5c0b054, 0xe5940000, 0xe5c01055\n"
        ".word 0xe5940000, 0xe5c07056, 0xe5940000, 0xe5c08057\n"
        ".word 0xe5940000, 0xe5c09058, 0xe5940000, 0xe5c0a059\n"
        ".word 0xe5944000, 0xe5960000, 0xe584005c, 0xe5960004\n"
        ".word 0xe5840060, 0xe5960008, 0xe5840064, 0xe3a00000\n"
        ".word 0xebfe4a1d, 0xe1a02000, 0xe284305c, 0xe3a01000\n"
        ".word 0xe1a0000d, 0xebfddf7d, 0xe1cd00d0, 0xe59f2050\n"
        ".word 0xe1c406f8, 0xe1500002, 0xda000005, 0xee000a10\n"
        ".word 0xedd40a1e, 0xe3a00000, 0xe5c400e4, 0xee300a60\n"
        ".word 0xea000006, 0xed940a1c, 0xedd40a36, 0xe3a01001\n"
        ".word 0xe5c410e4, 0xee700a20, 0xee000a10, 0xee300ac0\n"
        ".word 0xed840a3d, 0xe28dd01c, 0xe8bd8ff0, 0x00439c60\n"
        ".word 0x00007325, 0x43520000\n"
    );
}

// DECOMP_FUNC(0x002fb5c8, 472)
// 113 ARM instructions through unconditional pop; 20 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_002fb5c8() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe24dd024, 0xe1a0a000, 0xe59f61b0\n"
        ".word 0xe5d60001, 0xe3500000, 0x0a000067, 0xe2860080\n"
        ".word 0xe5900000, 0xe3500000, 0x0a000063, 0xe59f4194\n"
        ".word 0xe1b0500a, 0xe3a0b000, 0x0a000008, 0xe5950000\n"
        ".word 0xe5901008, 0xe1a0000a, 0xe12fff31, 0xe1500004\n"
        ".word 0x0a000003, 0xe5900000, 0xe3500000, 0x1afffffa\n"
        ".word 0xe1a0500b, 0xe3a04000, 0xe5950168, 0xe5951164\n"
        ".word 0xe28f8f55, 0xe0400001, 0xe1540140, 0xaa00004d\n"
        ".word 0xe5950164, 0xe1a07008, 0xe28d9004, 0xe7906104\n"
        ".word 0xe5960008, 0xe5b01014, 0xe3510000, 0x10800001\n"
        ".word 0x01a0000b, 0xe3500000, 0x13570000, 0xe58d0004\n"
        ".word 0x0a00000d, 0xe1a00008, 0xebff1f02, 0xe1a02000\n"
        ".word 0xe1a01007, 0xe1a00009, 0xebff1ed4, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000004, 0xe5b0100c, 0xe3510000\n"
        ".word 0x01a0000b, 0x10800001, 0xea000000, 0xe3a00000\n"
        ".word 0xe3500000, 0x0a000029, 0xe5901000, 0xe3110202\n"
        ".word 0x03a00000, 0xe5900010, 0xe3500000, 0xda00001b\n"
        ".word 0xe3500002, 0x1a000007, 0xe59f00a4, 0xe3a01001\n"
        ".word 0xe5d02001, 0xe3520000, 0x0a000002, 0xed900a19\n"
        ".word 0xe1a00006, 0xebfe9f68, 0xe59f7094, 0xe1b0600a\n"
        ".word 0x0a000008, 0xe5960000, 0xe5901008, 0xe1a0000a\n"
        ".word 0xe12fff31, 0xe1500007, 0x0a000003, 0xe5900000\n"
        ".word 0xe3500000, 0x1afffffa, 0xe1a0600b, 0xe3a00001\n"
        ".word 0xe5cd0000, 0xe59d0000, 0xe586021c, 0xea000007\n"
        ".word 0xe59f003c, 0xe3a01001, 0xe5d02001, 0xe3520000\n"
        ".word 0x0a000002, 0xed900a18, 0xe1a00006, 0xebfe9f4e\n"
        ".word 0xe5950168, 0xe5951164, 0xe2844001, 0xe0400001\n"
        ".word 0xe1540140, 0xbaffffb1, 0xe3a00001, 0xe28dd024\n"
        ".word 0xe8bd8ff0, 0x00464af0, 0x00472180, 0x64616873\n"
        ".word 0x0000776f, 0x00472288\n"
    );
}

// DECOMP_FUNC(0x0036f49c, 472)
// 115 ARM instructions through unconditional pop; 12 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_0036f49c() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe24dd00c, 0xe1b07000, 0x0a000003\n"
        ".word 0xe5971000, 0xe3a02292, 0xe1d21001, 0x0a000000\n"
        ".word 0xe3a07000, 0xe597102c, 0xe3510000, 0x1a000064\n"
        ".word 0xe587002c, 0xe5978030, 0xe3a04000, 0xe1a09000\n"
        ".word 0xe3a0b038, 0xe1a0a004, 0xe20400ff, 0xe08b0100\n"
        ".word 0xe0800007, 0xe5901000, 0xe3510000, 0x10815000\n"
        ".word 0x01a0500a, 0xe1a00008, 0xe5951018, 0xe3510000\n"
        ".word 0x1585a01c, 0x1a00004f, 0xe3500000, 0x059f0148\n"
        ".word 0xe5956008, 0xe1a00820, 0xe3560000, 0xe1a00800\n"
        ".word 0x1a000005, 0xe5951004, 0xe5952000, 0xe0020291\n"
        ".word 0xe5951014, 0xe0010192, 0xe1a061a1, 0xe59f1118\n"
        ".word 0xe1500001, 0xe0402001, 0x0a000008, 0xaa000003\n"
        ".word 0xe28004ff, 0xe2500801, 0x1a00003a, 0xea000021\n"
        ".word 0xe3520801, 0x13520802, 0x0a000009, 0xea000035\n"
        ".word 0xe5b5000c, 0xe1a01006, 0xe3500000, 0x10800005\n"
        ".word 0x01a0000a, 0xebfd4c16, 0xe320f000, 0xe320f000\n"
        ".word 0xea00002c, 0xe59fc0c8, 0xe2000803, 0xe58d0000\n"
        ".word 0xe59f10b8, 0xe59cc000, 0xe1a03006, 0xe1a02009\n"
        ".word 0xe12fff3c, 0xe58d0004, 0xe595100c, 0xe285000c\n"
        ".word 0xe3510000, 0x10900001, 0x0a000002, 0xe59d1004\n"
        ".word 0xe1a02006, 0xebfcdcf2, 0xe59d0004, 0xe5850018\n"
        ".word 0xe59d0000, 0xea000016, 0xe59fc074, 0xe59f106c\n"
        ".word 0xe1a03006, 0xe1a02009, 0xe59cc000, 0xe3a00801\n"
        ".word 0xe12fff3c, 0xe58d0000, 0xe595100c, 0xe285000c\n"
        ".word 0xe3510000, 0x0a000007, 0xe0911000, 0x159d0000\n"
        ".word 0x0a000004, 0xe1a02006, 0xebfcf5bf, 0xe59d0000\n"
        ".word 0xe1a01006, 0xebfd4bea, 0xe59d0000, 0xe5850018\n"
        ".word 0xe3a00801, 0xe585001c, 0xe2844001, 0xe3540006\n"
        ".word 0xbaffffa0, 0xe28dd00c, 0xe8bd8ff0, 0x02010000\n"
        ".word 0x00000101, 0x0044e330\n"
    );
}

// DECOMP_FUNC(0x003f5ad4, 472)
// 117 ARM instructions through unconditional pop; 4 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_003f5ad4() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe1a05000, 0xe24dd00c, 0xe1a06001\n"
        ".word 0xe5904018, 0xe3a00000, 0xe5850008, 0xe1a01004\n"
        ".word 0xe1a00002, 0xebfb4444, 0xe1a0b000, 0xe2400026\n"
        ".word 0xe3a02001, 0xe3a01002, 0xebfda9d7, 0xe1b08000\n"
        ".word 0x0a000060, 0xe3540001, 0x85950010, 0xe59fa180\n"
        ".word 0x81580000, 0x9a00000c, 0xe595000c, 0xe3500000\n"
        ".word 0x159a1004, 0x112fff31, 0xe3a00000, 0xe5850010\n"
        ".word 0xe59a1000, 0xe1a00088, 0xe12fff31, 0xe3500000\n"
        ".word 0xe585000c, 0x15858010, 0x0a00004f, 0xe2480020\n"
        ".word 0xe3540001, 0xe0000490, 0x01a07088, 0xe1a09080\n"
        ".word 0xe5950004, 0x11a07009, 0xe1500007, 0x2a00000c\n"
        ".word 0xe5950000, 0xe3500000, 0x159a1004, 0x112fff31\n"
        ".word 0xe3a00000, 0xe5850004, 0xe59a1000, 0xe1a00007\n"
        ".word 0xe12fff31, 0xe3500000, 0xe5850000, 0x15857004\n"
        ".word 0x0a000039, 0xe3540001, 0xe5859008, 0x0a000018\n"
        ".word 0xe3540000, 0xe3a07000, 0x82489021, 0x8248a020\n"
        ".word 0x9a000030, 0xe2861020, 0xe28d0004, 0xebfb1f81\n"
        ".word 0xe58d8000, 0xe595100c, 0xe2860026, 0xe28d3004\n"
        ".word 0xe1a02006, 0xebfda953, 0xe595000c, 0xe5951000\n"
        ".word 0xe35a0000, 0xe2800020, 0xe0811087, 0xda00001d\n"
        ".word 0xe3190001, 0xe2400002, 0xe0411084, 0x1a00000f\n"
        ".word 0xea00000b, 0xe2861020, 0xe28d0004, 0xebfb1f6d\n"
        ".word 0xe58d8000, 0xe5951000, 0xe2860026, 0xe28d3004\n"
        ".word 0xe1a02006, 0xebfda93f, 0xe320f000, 0xe320f000\n"
        ".word 0xea000010, 0xe1f020b2, 0xe0811084, 0xe1c120b0\n"
        ".word 0xe1b020ca, 0x0a000007, 0xe1d030b2, 0xe081c084\n"
        ".word 0xe0811104, 0xe1cc30b0, 0xe1f030b4, 0xe2522001\n"
        ".word 0xe1c130b0, 0x1afffff7, 0xe2877001, 0xe1570004\n"
        ".word 0xe086600b, 0x3affffce, 0xe3a00001, 0xe28dd00c\n"
        ".word 0xe8bd8ff0, 0x0044e918\n"
    );
}

// DECOMP_FUNC(0x0037c808, 476)
// 118 ARM instructions through unconditional pop; 4 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_0037c808() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe1a06000, 0xe24dd024, 0xe1a04001\n"
        ".word 0xe59f01c0, 0xe5900004, 0xe3500000, 0x0a00006b\n"
        ".word 0xe5901000, 0xe28d2014, 0xe5913008, 0xe5961014\n"
        ".word 0xe12fff33, 0xe3500000, 0x0a000064, 0xe5962010\n"
        ".word 0xe3a01001, 0xe3a00b02, 0xe5842010, 0xe1d623b0\n"
        ".word 0xe3a0b000, 0xe1c428b0, 0xe59d5014, 0xe5841040\n"
        ".word 0xe584503c, 0xe5c41018, 0xe59d1018, 0xe3550000\n"
        ".word 0xe584101c, 0xe5d61024, 0xe5c41020, 0xe5961028\n"
        ".word 0xe5841024, 0xe596102c, 0xe5841028, 0xe59d101c\n"
        ".word 0xe5840030, 0xe584102c, 0xe5840034, 0x0a00000f\n"
        ".word 0xe2050001, 0xe3500001, 0xe3a01000, 0x03a01001\n"
        ".word 0x0584b060, 0xe1500005, 0x2a000008, 0xe0842101\n"
        ".word 0xe2811001, 0xe2800002, 0xe0843101, 0xe582b060\n"
        ".word 0xe1500005, 0xe2811001, 0xe583b060, 0x3afffff6\n"
        ".word 0xe594702c, 0xe5949024, 0xe1a01007, 0xe1a00009\n"
        ".word 0xebfd28c4, 0xe1a08000, 0xe594a028, 0xe0000897\n"
        ".word 0xe1a01007, 0xe0499000, 0xe24a0001, 0xebfd28bd\n"
        ".word 0xe1a02000, 0xe5d40020, 0xe3a01040, 0xe3a03003\n"
        ".word 0xe3500000, 0x10000297, 0x104a0000, 0x03a00b01\n"
        ".word 0xe5840038, 0xe3a0007f, 0xe5c40044, 0xe5c41045\n"
        ".word 0xe5c4b046, 0xe5c43047, 0xe3550000, 0xe3a00000\n"
        ".word 0xe5c45048, 0x9a000005, 0xe1a01000, 0xe0843000\n"
        ".word 0xe2800001, 0xe1550000, 0xe5c31049, 0x8afffff9\n"
        ".word 0xe2860038, 0xe5869048, 0xe8800104, 0xe5962c24\n"
        ".word 0xe3520000, 0x0a00000c, 0xe58db000, 0xe5961c28\n"
        ".word 0xe1a0000d, 0xe12fff32, 0xe3500000, 0x0a00000b\n"
        ".word 0xe59d0000, 0xe5860050, 0xe5960018, 0xe5900010\n"
        ".word 0xe586005c, 0xe586b058, 0xea000002, 0xe596002c\n"
        ".word 0xe586005c, 0xe586b058, 0xe3a00001, 0xe586b054\n"
        ".word 0xe28dd024, 0xe8bd8ff0, 0x00473540\n"
    );
}

// DECOMP_FUNC(0x003a0bb8, 476)
// 109 ARM instructions through unconditional pop; 40 trailing data bytes.
extern "C" __attribute__((naked)) void shop_func_003a0bb8() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4070, 0xe1a04000, 0xe5900008, 0xe3500000\n"
        ".word 0x0a000002, 0xe3500001, 0x1a00004c, 0xea000007\n"
        ".word 0xe3a00001, 0xebfa40e8, 0xe3a01000, 0xe2840fea\n"
        ".word 0xebfa49f9, 0xe3a00001, 0xe5840008, 0xea000043\n"
        ".word 0xe2845ff2, 0xe3a01000, 0xe1a00005, 0xebfc6185\n"
        ".word 0xe1a00005, 0xe320f000, 0xebfc78d6, 0xe1a06000\n"
        ".word 0xe1a00005, 0xebfc78d6, 0xe1a01000, 0xe1a02006\n"
        ".word 0xe2840d0e, 0xebfa41e8, 0xe1a00005, 0xe320f000\n"
        ".word 0xe1d008da, 0xe3500000, 0xe320f000, 0x0a00002f\n"
        ".word 0xe5940860, 0xe3a05000, 0xe3500009, 0x379ff100\n"
        ".word 0xea00002a, 0x003a0c80, 0x003a0c80, 0x003a0c80\n"
        ".word 0x003a0c80, 0x003a0c80, 0x003a0c80, 0x003a0c80\n"
        ".word 0x003a0ca4, 0x003a0cd8, 0xe320f000, 0xebfbf5c3\n"
        ".word 0xe3500000, 0xe320f000, 0x0a00001c, 0xe2841004\n"
        ".word 0xe3a00005, 0xe8810021, 0xea000018, 0xe2842004\n"
        ".word 0xe3a00006, 0xe8820021, 0xe28f10b4, 0xe5940160\n"
        ".word 0xebfbc0d6, 0xe5942168, 0xe1a01000, 0xe1a00002\n"
        ".word 0xebfbd945, 0xe320f000, 0xe320f000, 0xea000009\n"
        ".word 0xe2842004, 0xe3a00007, 0xe8820021, 0xe28f1090\n"
        ".word 0xe5940160, 0xebfbc0c9, 0xe5942168, 0xe1a01000\n"
        ".word 0xe1a00002, 0xebfbd938, 0xe5940168, 0xebf7f4ac\n"
        ".word 0xe2844b57, 0xe2844f52, 0xe5940000, 0xe3500000\n"
        ".word 0x0a000012, 0xebfc3512, 0xe3500000, 0xe320f000\n"
        ".word 0x0a00000e, 0xe5940000, 0xe5901008, 0xe591100c\n"
        ".word 0xe3510000, 0xaa000009, 0xe3a01001, 0xebfbfe5f\n"
        ".word 0xe5940000, 0xed9f0a0e, 0xeddf0a0e, 0xe3a01000\n"
        ".word 0xe5900008, 0xeeb01a40, 0xe8bd4070, 0xeafbe551\n"
        ".word 0xe8bd8070, 0x706f6873, 0x6574695f, 0x7975626d\n"
        ".word 0x00000000, 0x706f6873, 0x6c65735f, 0x66666f6c\n"
        ".word 0x00000000, 0x00000000, 0xc6fa0000\n"
    );
}

// DECOMP_FUNC(0x003b87a0, 476)
// 117 ARM instructions through unconditional pop; 8 trailing data bytes.
extern "C" __attribute__((naked)) void script_vm_func_003b87a0() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4070, 0xe1a04000, 0xe59f01c4, 0xe3a05000\n"
        ".word 0xe1d017ba, 0xe3510000, 0x0a000004, 0xe2842028\n"
        ".word 0xe3a0100d, 0xe8820022, 0xe1c057ba, 0xea00005c\n"
        ".word 0xe1d017b8, 0xe3510000, 0x0a000004, 0xe2842028\n"
        ".word 0xe3a0100c, 0xe8820022, 0xe1c057b8, 0xea000054\n"
        ".word 0xe59f0180, 0xe5900000, 0xebfaf7c6, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000003, 0xe2841028, 0xe3a0000e\n"
        ".word 0xe8810021, 0xea00004a, 0xe5940020, 0xe3a06010\n"
        ".word 0xe3100501, 0x0a000006, 0xe3a020ff, 0xe3a0101e\n"
        ".word 0xe3a00000, 0xebfb8f89, 0xe584502c, 0xe5846028\n"
        ".word 0xea00003f, 0xe3100010, 0x03100602, 0x1a000009\n"
        ".word 0xe3100701, 0x03100502, 0x1a000006, 0xe3100301\n"
        ".word 0x03100401, 0x1a000003, 0xe3100402, 0x03100302\n"
        ".word 0x03100202, 0x0a000002, 0xe3100c01, 0x1a000015\n"
        ".word 0xea000010, 0xe3100a02, 0x0a00002b, 0xe3100040\n"
        ".word 0x0a000002, 0xe3c00040, 0xe5840020, 0xebfb7a21\n"
        ".word 0xe2841028, 0xe3a00006, 0xe8810021, 0xe284009c\n"
        ".word 0xebf9cc67, 0xe5840d60, 0xe5940020, 0xe3c00a02\n"
        ".word 0xe5840020, 0xea00001e, 0xe3a020ff, 0xe3a0100a\n"
        ".word 0xe3a00000, 0xebfb8f61, 0xe5940020, 0xe3100502\n"
        ".word 0x03100401, 0x1a00000b, 0xe3100402, 0x03100302\n"
        ".word 0x1a000008, 0xe3100601, 0x03100702, 0x1a000005\n"
        ".word 0xe3100602, 0x03100701, 0x1a000002, 0xe3100301\n"
        ".word 0x03100202, 0x0a000005, 0xe3100c01, 0x1a000003\n"
        ".word 0xe3a020ff, 0xe3a0100a, 0xe3a00001, 0xebfb8f4b\n"
        ".word 0xe584502c, 0xe5846028, 0xea000001, 0xe1a00004\n"
        ".word 0xeb00000d, 0xe1a00004, 0xebf9cbef, 0xe2841058\n"
        ".word 0xe1a00004, 0xebf9cc1d, 0xe5d40e58, 0xe3500000\n"
        ".word 0x0a000002, 0xe5940e5c, 0xe8bd4070, 0xeafe24c0\n"
        ".word 0xe8bd8070, 0x0049fa1c, 0x00433158\n"
    );
}

// DECOMP_FUNC(0x001103bc, 480)
// 114 ARM instructions through unconditional pop; 24 trailing data bytes.
extern "C" __attribute__((naked)) void camp_func_001103bc() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d5fff, 0xe1a06003, 0xe1a0a001, 0xe1a0b002\n"
        ".word 0xeb06ac8d, 0xe3500000, 0x1a000003, 0xeb06ac10\n"
        ".word 0xe3500000, 0x059f019c, 0x0a000064, 0xe320f000\n"
        ".word 0xeb06ac0b, 0xe3500000, 0xe3a04001, 0x0a000004\n"
        ".word 0xe3a00000, 0xeb06ac33, 0xe320f000, 0xe320f000\n"
        ".word 0xea000014, 0xe320f000, 0xeb06ac7b, 0xe3500000\n"
        ".word 0xe320f000, 0x0a00000f, 0xe59f515c, 0xe5c54001\n"
        ".word 0xeb0065b0, 0xe320f000, 0xe320f000, 0xeb06ac5d\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000001, 0xeb06ac3f\n"
        ".word 0xe5c54004, 0xe3a00000, 0xeb06ac1e, 0xe320f000\n"
        ".word 0xe320f000, 0xeb0068a1, 0xe320f000, 0xeb06abe8\n"
        ".word 0xe1b05000, 0x13a00001, 0x1b06d4d2, 0xe59f710c\n"
        ".word 0xe59f810c, 0xe59f910c, 0xe320f000, 0xeb06ac8a\n"
        ".word 0xe59d0000, 0xe1a03006, 0xe1a0200b, 0xe1a0100a\n"
        ".word 0xeb0034a1, 0xe1a04000, 0xe320f000, 0xeb06ac66\n"
        ".word 0xe1540007, 0xe1a00004, 0x11500008, 0x11540009\n"
        ".word 0x0a000008, 0xe3550000, 0x0a000011, 0xeb06abd0\n"
        ".word 0xe3500000, 0x03a00001, 0x0b06d452, 0xe320f000\n"
        ".word 0xe320f000, 0xea00000f, 0xe59fc0ac, 0xe3a0100a\n"
        ".word 0xe3a03000, 0xe1a02fc1, 0xe0840c91, 0xe0224c92\n"
        ".word 0xe0212391, 0xeb06abe2, 0xe320f000, 0xe320f000\n"
        ".word 0xeaffffdc, 0xe320f000, 0xeb06abbd, 0xe3500000\n"
        ".word 0x13a00001, 0x1b06d4a7, 0xe1a00004, 0xe1a0100f\n"
        ".word 0xe1b02fa4, 0x1b06adf6, 0xe320f000, 0xe320f000\n"
        ".word 0xeb06abdf, 0xe320f000, 0xe320f000, 0xeb06ac2e\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000002, 0xe59d0000\n"
        ".word 0xeb0033d2, 0xe1a04000, 0xe320f000, 0xeb06abac\n"
        ".word 0xe3500000, 0xe320f000, 0x1f000003, 0xe1a00004\n"
        ".word 0xe28dd010, 0xe8bd9ff0, 0xc8a0cc04, 0x0044e360\n"
        ".word 0xc8a0cff0, 0xe0a0cc08, 0xc8a0cc02, 0x000f4240\n"
    );
}

// DECOMP_FUNC(0x0014c5c0, 480)
// 115 ARM instructions through unconditional pop; 20 trailing data bytes.
extern "C" __attribute__((naked)) void func_0014c5c0() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d47f0, 0xe1a04000, 0xe2806c01, 0xe1a05001\n"
        ".word 0xed2d8b02, 0xe5d001f6, 0xe3500001, 0x1a000068\n"
        ".word 0xe5950004, 0xe5951000, 0xe1c420d0, 0xe0911002\n"
        ".word 0xe0a00003, 0xe5840004, 0xe5841000, 0xe5940008\n"
        ".word 0xe2800001, 0xe5840008, 0xeb000ce1, 0xe594100c\n"
        ".word 0xe0800001, 0xe584000c, 0xe5d600b4, 0xe3500001\n"
        ".word 0x1a000057, 0xe59f2160, 0xe5956000, 0xe3a07000\n"
        ".word 0xe5955004, 0xe59f1154, 0xe1a03fc2, 0xe1a00007\n"
        ".word 0xeb05a53f, 0xe0823096, 0xe0cc3195, 0xe08ac095\n"
        ".word 0xe1a09fc5, 0xe3a08000, 0xe020a099, 0xe08a9691\n"
        ".word 0xe0200895, 0xe1a08fc1, 0xe3a05000, 0xe026a698\n"
        ".word 0xe09cc009, 0xe0216591, 0xe0a11000, 0xe0922007\n"
        ".word 0xe0a33005, 0xe09c0002, 0xe0a11003, 0xe3a02ffa\n"
        ".word 0xe1a03005, 0xeb05a52a, 0xeb04da02, 0xee000a10\n"
        ".word 0xeddf0a3b, 0xe2840010, 0xee208a20, 0xeddf0a39\n"
        ".word 0xeeb00a48, 0xeeb40ae0, 0xeef1fa10, 0x3a000003\n"
        ".word 0xe59f20d4, 0xee181a10, 0xe1510002, 0xda000002\n"
        ".word 0xe59011a0, 0xe2811001, 0xe58011a0, 0xeef00a48\n"
        ".word 0xed900a00, 0xeeb40ae0, 0xeef1fa10, 0xeef00a48\n"
        ".word 0x3eb00a48, 0xeefd0ae0, 0xed800a00, 0xee101a90\n"
        ".word 0xe3510065, 0xaa000003, 0xe0801101, 0xe5912008\n"
        ".word 0xe2822001, 0xe5812008, 0xe590119c, 0xeeb00a48\n"
        ".word 0xe2811001, 0xe580119c, 0xedd00a01, 0xee300a80\n"
        ".word 0xed800a01, 0xe59401f8, 0xe3500000, 0x0a00000f\n"
        ".word 0xe5941204, 0xe5942200, 0xe1520001, 0xda00000b\n"
        ".word 0xe0805181, 0xeb05bac5, 0xe320f000, 0xe320f000\n"
        ".word 0xeb00171c, 0xe5c50004, 0xe59401fc, 0xe5c50005\n"
        ".word 0xed858a00, 0xe5940204, 0xe2800001, 0xe5840204\n"
        ".word 0xe58471fc, 0xecbd8b02, 0xe8bd87f0, 0x0ffb0ff0\n"
        ".word 0x3b9aca00, 0x3ca78f51, 0x00000000, 0x42c80000\n"
    );
}

// DECOMP_FUNC(0x00258c58, 480)
// 116 ARM instructions through unconditional pop; 16 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_00258c58() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d43f0, 0xe24dd01c, 0xe1b07000, 0xe3a06008\n"
        ".word 0xe59f91b8, 0xe5994004, 0xe2848c13, 0xe2845c13\n"
        ".word 0xe1d800f0, 0x12845a01, 0x12855e8b, 0xe3500000\n"
        ".word 0xaa000001, 0xeb010841, 0xea000007, 0xe320f000\n"
        ".word 0xda000006, 0xe59f0188, 0xe7d00004, 0xe3500006\n"
        ".word 0x0a000002, 0xe3a00000, 0xeb010fb7, 0xe1a06000\n"
        ".word 0xe2840a01, 0xe20610ff, 0xe2800fd2, 0xebfef365\n"
        ".word 0xe3570000, 0xe320f000, 0x0a000003, 0xe2840b06\n"
        ".word 0xe20610ff, 0xe28000f8, 0xeb022895, 0xe3a07000\n"
        ".word 0xe58d7008, 0xe58d700c, 0xe58d7010, 0xe58d7014\n"
        ".word 0xe1d500f0, 0xe3500000, 0xda00001c, 0xe59f0120\n"
        ".word 0xe7d00004, 0xe3500006, 0x0a000018, 0xe3500002\n"
        ".word 0x13500003, 0x1a000006, 0xe1d800b0, 0xeb015ebe\n"
        ".word 0xe3500000, 0x15d0004b, 0x13500000, 0x13a00001\n"
        ".word 0x1a000000, 0xe3a00000, 0xe58d0000, 0xe1d510b2\n"
        ".word 0xe1d500b0, 0xe28d3008, 0xe2852048, 0xeb0047b6\n"
        ".word 0xe6af1070, 0xe28d0008, 0xeb00479e, 0xe59f00c4\n"
        ".word 0xe7d00004, 0xe3500006, 0x1a00000a, 0xea000002\n"
        ".word 0xe3e01000, 0xe3a00000, 0xeafffff6, 0xe5996004\n"
        ".word 0xe59f00a4, 0xe7807006, 0xeb00ec2d, 0xe2866c1e\n"
        ".word 0xe2866063, 0xe5c67000, 0xe1d500f0, 0xe3a06001\n"
        ".word 0xe3500000, 0xaa000006, 0xe285003a, 0xebfef2f5\n"
        ".word 0xe2840a01, 0xe59012e4, 0xe3510001, 0xc58062e4\n"
        ".word 0xcb00ec1f, 0xe1d500f0, 0xe3500000, 0xda00000f\n"
        ".word 0xeb01d9c0, 0xe2850058, 0xe320f000, 0xebfe55ee\n"
        ".word 0xe2850098, 0xe320f000, 0xebfe5674, 0xe320f000\n"
        ".word 0xe320f000, 0xeb00ebd3, 0xe3500002, 0xe320f000\n"
        ".word 0x1a000002, 0xe59f0020, 0xe7806004, 0xeb00ec0c\n"
        ".word 0xe320f000, 0xeb0048aa, 0xe28dd01c, 0xe8bd83f0\n"
        ".word 0x0044e140, 0x00001e66, 0x00001e67, 0x000012e4\n"
    );
}

// DECOMP_FUNC(0x0033504c, 480)
// 119 ARM instructions through unconditional pop; 4 trailing data bytes.
extern "C" __attribute__((naked)) void camp_func_0033504c() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe24dd04c, 0xebfc293e, 0xe59f91c8\n"
        ".word 0xe3a07001, 0xe3a0b000, 0xe1a0a007, 0xe58d0004\n"
        ".word 0xe3a01000, 0xe3a0000b, 0xebfe2f92, 0xe1b04000\n"
        ".word 0xe320f000, 0x0a000063, 0xebfe2f84, 0xe1a05000\n"
        ".word 0xe1a00004, 0xebfe2f6d, 0xe6ff8077, 0xe1a02000\n"
        ".word 0xe1cd82b8, 0xe3a03040, 0xe1a01005, 0xe28d0008\n"
        ".word 0xe58d9000, 0xfafdfe09, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000054, 0xe1d002b6, 0xe3500000, 0x1a000051\n"
        ".word 0xe3a01000, 0xe3a0000b, 0xebfe2f7a, 0xe1b04000\n"
        ".word 0xe320f000, 0x0a00004b, 0xebfe2f6c, 0xe1a05000\n"
        ".word 0xe1a00004, 0xebfe2f55, 0xe1a02000, 0xe1cd82b8\n"
        ".word 0xe3a03040, 0xe1a01005, 0xe28d0008, 0xe58d9000\n"
        ".word 0xfafdfdf2, 0xe1b05000, 0xe320f000, 0x0a00003d\n"
        ".word 0xebfe0572, 0xe5d5102b, 0xe5d00076, 0xe1510000\n"
        ".word 0x93a04000, 0x8a000037, 0xe0850084, 0xe1d002bc\n"
        ".word 0xe3500000, 0x0a000003, 0xebfe2e97, 0xe3500000\n"
        ".word 0xe320f000, 0x0a00002f, 0xe2844001, 0xe3540003\n"
        ".word 0xbafffff4, 0xe3a04000, 0xe0850084, 0xe1d063b2\n"
        ".word 0xe3560000, 0x0a000004, 0xebfc28f6, 0xe7d001a6\n"
        ".word 0xe2062007, 0xe110021a, 0x0a000022, 0xe2844001\n"
        ".word 0xe3540003, 0xbafffff3, 0xe3a01000, 0xe3a0000b\n"
        ".word 0xebfe2f48, 0xe1b04000, 0xe320f000, 0x0a00000a\n"
        ".word 0xebfe2f3a, 0xe1a05000, 0xe1a00004, 0xebfe2f23\n"
        ".word 0xe1a02000, 0xe1cd82b8, 0xe3a03040, 0xe1a01005\n"
        ".word 0xe28d0008, 0xe58d9000, 0xfafdfdc0, 0xe320f000\n"
        ".word 0xebfd836b, 0xe1a01fc7, 0xe59d0004, 0xe0872ea1\n"
        ".word 0xe1a011c2, 0xe3c22007, 0xe0472002, 0xe7f03001\n"
        ".word 0xe1a0121a, 0xe1832001, 0xe5c02000, 0xe5d02012\n"
        ".word 0xe1811002, 0xe5c01012, 0xe2877001, 0xe357008d\n"
        ".word 0x3affff92, 0xe28dd04c, 0xe8bd8ff0, 0x001455dc\n"
    );
}

// DECOMP_FUNC(0x0013a29c, 484)
// 120 ARM instructions through unconditional bx; 4 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_0013a29c() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d41f0, 0xe1a04000, 0xed2d8b02, 0xe5d00000\n"
        ".word 0xed9f8a67, 0xe3500000, 0x0a000005, 0xeeb00a48\n"
        ".word 0xe59f0190, 0xed840a01, 0xedd40a02, 0xee200a20\n"
        ".word 0xeb05b904, 0xe5d40000, 0xe3500000, 0x0a000005\n"
        ".word 0xeeb00a48, 0xe59f016c, 0xed840a02, 0xedd40a01\n"
        ".word 0xee200a80, 0xeb05b8fb, 0xeeb00a48, 0xe5d40000\n"
        ".word 0xe3a01000, 0xe3500000, 0x0a000002, 0xe59f0144\n"
        ".word 0xed840a03, 0xeb05b8d7, 0xeeb00a48, 0xe5d40000\n"
        ".word 0xe3a01001, 0xe3500000, 0x0a000002, 0xe59f0124\n"
        ".word 0xed840a04, 0xeb05b8cf, 0xe3a06000, 0xe2840034\n"
        ".word 0xe1a07006, 0xe1a08006, 0xe1a05000, 0xeb0625d6\n"
        ".word 0xe5847014, 0xe584801c, 0xe1d423d0, 0xe59f00f4\n"
        ".word 0xe1a01006, 0xeb05b8a8, 0xe1a00005, 0xe320f000\n"
        ".word 0xeb0625ac, 0xe3a07000, 0xe2845034, 0xe3a06001\n"
        ".word 0xe1a08007, 0xe1a00005, 0xeb0625c7, 0xe5847018\n"
        ".word 0xe5848020, 0xe1d423d1, 0xe59f00b8, 0xe1a01006\n"
        ".word 0xeb05b899, 0xe1a00005, 0xe320f000, 0xeb06259d\n"
        ".word 0xe3a02000, 0xe59f009c, 0xe1a01002, 0xe5c42024\n"
        ".word 0xeb00332c, 0xe3a02000, 0xe59f0088, 0xe3a01001\n"
        ".word 0xe5c42025, 0xeb003327, 0xe3a01902, 0xe59f0074\n"
        ".word 0xe1c412ba, 0xeb0032e8, 0xe0661786, 0xe59f0064\n"
        ".word 0xe1c412b8, 0xeb00330a, 0xe3a05001, 0xe320f000\n"
        ".word 0xeb06046c, 0xe3500000, 0xe320f000, 0x0a000003\n"
        ".word 0xe59f0040, 0xe1a01005, 0xe5c45001, 0xeb0032ee\n"
        ".word 0xe3a00000, 0xe5c40030, 0xe5c40031, 0xe3a01002\n"
        ".word 0xe59f0020, 0xe1c413b2, 0xeb00333b, 0xe3a01000\n"
        ".word 0xe5c41003, 0xe59f000c, 0xecbd8b02, 0xe8bd41f0\n"
        ".word 0xea0032bc, 0x3f800000, 0x004e6f64, 0xe5d01000\n"
        ".word 0xe3510000, 0x0a000004, 0xed800a01, 0xedd00a02\n"
        ".word 0xe59f0008, 0xee200a20, 0xea05b89a, 0xe12fff1e\n"
        ".word 0x004e6f64\n"
    );
}

// DECOMP_FUNC(0x0029ccf8, 484)
// 117 ARM instructions through unconditional pop; 16 trailing data bytes.
extern "C" __attribute__((naked)) void script_vm_func_0029ccf8() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d40f0, 0xe24dd00c, 0xe59f71c4, 0xe59f01c4\n"
        ".word 0xe5975004, 0xe7900005, 0xe3500003, 0x0a00006a\n"
        ".word 0xe59f01b4, 0xe7d00005, 0xe3500003, 0x13500009\n"
        ".word 0x1a00002d, 0xeb001028, 0xe3500000, 0x0a000012\n"
        ".word 0xe2851d7a, 0xe5910000, 0xe3500000, 0x0a000026\n"
        ".word 0xe2850b07, 0xed9f1a61, 0xed900aa2, 0xe5902284\n"
        ".word 0xedd00aa3, 0xee300a01, 0xe28d0004, 0xe58d2000\n"
        ".word 0xec800a02, 0xe5910000, 0xe1a0100d, 0xebffdce8\n"
        ".word 0xe3a00001, 0xebfffba6, 0xea000013, 0xe2854d7a\n"
        ".word 0xe5940000, 0xe3500000, 0x0a000013, 0xebffaefd\n"
        ".word 0xe320f000, 0xe320f000, 0xeb006f4d, 0xe3500000\n"
        ".word 0x03a00000, 0x0b002a14, 0xe5d70002, 0xe3500000\n"
        ".word 0x0a000005, 0xe5940000, 0xe3500000, 0x0a000006\n"
        ".word 0xe5901000, 0xe5911004, 0xe12fff31, 0xe3a00d7a\n"
        ".word 0xe7900005, 0xe3500000, 0x1bffaed8, 0xe3a02000\n"
        ".word 0xe3a01005, 0xe2850fe3, 0xeb008332, 0xe2850b01\n"
        ".word 0xe3a01003, 0xe2800018, 0xeb00888a, 0xe2850b01\n"
        ".word 0xe3a01003, 0xe28000a4, 0xeb008886, 0xe3a01003\n"
        ".word 0xe2850e53, 0xeb008883, 0xe2850b01, 0xe3a02000\n"
        ".word 0xe3a01005, 0xe2800f6f, 0xeb008322, 0xe2850b01\n"
        ".word 0xe3a02000, 0xe3a01005, 0xe2800f92, 0xeb00831d\n"
        ".word 0xe2850b01, 0xe3a02000, 0xe3a01005, 0xe2800fb5\n"
        ".word 0xeb008318, 0xe3a01003, 0xe2850e76, 0xeb008871\n"
        ".word 0xe3a04000, 0xe3a02000, 0xe0640184, 0xe3a01005\n"
        ".word 0xe0800100, 0xe0856100, 0xe2860b01, 0xe2800ffb\n"
        ".word 0xeb00830c, 0xe2860b03, 0xe2800f59, 0xe3a02000\n"
        ".word 0xe3a01005, 0xeb008307, 0xe2844001, 0xe354000a\n"
        ".word 0xbaffffef, 0xe5971004, 0xe59f3018, 0xe3a02000\n"
        ".word 0xe3a00002, 0xe5812010, 0xe7830001, 0xe28dd00c\n"
        ".word 0xe8bd80f0, 0x0044e140, 0x000012dc, 0x00001e67\n"
        ".word 0x447a0000\n"
    );
}

// DECOMP_FUNC(0x002b5820, 484)
// 116 ARM instructions through unconditional pop; 20 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_002b5820() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4fff, 0xe24dd01c, 0xe1a06001, 0xe1a07000\n"
        ".word 0xe1a08003, 0xe59f41b4, 0xe1cd05d8, 0xe59d9050\n"
        ".word 0xe2445008, 0xe1cd00f8, 0xe1c420d0, 0xe0222000\n"
        ".word 0xe0233001, 0xe1922003, 0x0a000009, 0xe1c520d0\n"
        ".word 0xe0200002, 0xe0211003, 0xe1900001, 0x0a000004\n"
        ".word 0xef000028, 0xe1cd01f0, 0xe2060801, 0xe1a0a820\n"
        ".word 0xea000002, 0xe3a00000, 0xe1a01000, 0xeafffff8\n"
        ".word 0xe59d5024, 0xe3580a01, 0xe1a04008, 0x8b001d69\n"
        ".word 0xe3550000, 0x13540000, 0x03a05000, 0x01a04005\n"
        ".word 0xeb001780, 0xe320f000, 0xe320f000, 0xeb0016df\n"
        ".word 0xe1a03005, 0xe1a02006, 0xe1a01007, 0xe88d0210\n"
        ".word 0xebfa4a4e, 0xe1a04000, 0xe2100102, 0x4a000001\n"
        ".word 0xe35a0000, 0x1bfa49bd, 0xe320f000, 0xeb001755\n"
        ".word 0xe2140102, 0xe58d4000, 0x5a000039, 0xe59f00f0\n"
        ".word 0xe1540000, 0x1a000036, 0xe59f00e0, 0xe1c020d0\n"
        ".word 0xe1cd00d8, 0xe0222000, 0xe0233001, 0xe1922003\n"
        ".word 0x0a00002f, 0xe59f20cc, 0xe5923000, 0xe5922004\n"
        ".word 0xe0233000, 0xe0210002, 0xe1900003, 0x0a00001d\n"
        ".word 0xef000028, 0xe1a02000, 0xe28d4010, 0xe1a00001\n"
        ".word 0xe894000a, 0xe3a0b000, 0xe58db004, 0xe0521001\n"
        ".word 0xe0c00003, 0xe59f3090, 0xe3a02003, 0xe58db018\n"
        ".word 0xe1a0400b, 0xe08c5391, 0xe08e5290, 0xe59de018\n"
        ".word 0xe09cc004, 0xe1a0bfc0, 0xe0a5500e, 0xe08e4390\n"
        ".word 0xe023e39b, 0xe59db004, 0xe0203b90, 0xe0a04192\n"
        ".word 0xe1cd20d8, 0xe094100c, 0xe0a00005, 0xe0521001\n"
        ".word 0xe0d30000, 0xba00000a, 0xe59fc040, 0xe3a0100a\n"
        ".word 0xe3a03000, 0xe1a02fc1, 0xe0840c91, 0xe0224c92\n"
        ".word 0xe0212391, 0xeb0016ad, 0xe320f000, 0xe320f000\n"
        ".word 0xeaffffaa, 0xe59d0000, 0xe28dd02c, 0xe8bd8ff0\n"
        ".word 0x0044e378, 0xc8a0cc02, 0x0044e370, 0xbad34aee\n"
        ".word 0x000f4240\n"
    );
}

// DECOMP_FUNC(0x003821e4, 484)
// 120 ARM instructions through unconditional pop; 4 trailing data bytes.
extern "C" __attribute__((naked)) void script_vm_func_003821e4() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4070, 0xe1a04000, 0xe59005a0, 0xe3500000\n"
        ".word 0x159405a4, 0x13500000, 0x0a00006f, 0xe59405ac\n"
        ".word 0xe3500000, 0x159405b0, 0x13500000, 0x13a01000\n"
        ".word 0x0a000069, 0xe3a00031, 0xebfc9075, 0xe3500000\n"
        ".word 0x159f6198, 0x13a05000, 0x0a000063, 0xe7d61005\n"
        ".word 0xe3a00031, 0xebfcf524, 0xe1d020f8, 0xe1a01000\n"
        ".word 0xe0840185, 0xee002a10, 0xe2802b01, 0xeeb80ac0\n"
        ".word 0xed800aa7, 0xed820a27, 0xe1d130fa, 0xee003a10\n"
        ".word 0xeeb80ac0, 0xed800aa8, 0xed820a28, 0xe591200c\n"
        ".word 0xe3520000, 0x0a000008, 0xe1d220f0, 0xee002a10\n"
        ".word 0xeeb80ac0, 0xed800ae7, 0xe591100c, 0xe1d110f2\n"
        ".word 0xee001a10, 0xeeb80ac0, 0xed800ae8, 0xe2855001\n"
        ".word 0xe3550017, 0x3affffe0, 0xe3a00000, 0xe3a02007\n"
        ".word 0xe0841180, 0xe2811b01, 0xedd40ad1, 0xed910a2f\n"
        ".word 0xe2522001, 0xe2800001, 0xee300a20, 0xed810a2f\n"
        ".word 0xed940ad2, 0xedd10a30, 0xee300a80, 0xed810a30\n"
        ".word 0x1afffff2, 0xe3a00000, 0xe3a0200a, 0xe0841180\n"
        ".word 0xe2811b01, 0xedd40ad3, 0xed910a3d, 0xe2522001\n"
        ".word 0xe2800001, 0xee300a20, 0xed810a3d, 0xedd40ad4\n"
        ".word 0xed910a3e, 0xee300a20, 0xed810a3e, 0x1afffff2\n"
        ".word 0xe2840e5a, 0xe8900003, 0xebfc53f1, 0xe3a01002\n"
        ".word 0xe58405a8, 0xe5801108, 0xe2840b01, 0xe2800f6b\n"
        ".word 0xe8900003, 0xebfc53ea, 0xe3a01002, 0xe58405b4\n"
        ".word 0xe5801108, 0xe5d41021, 0xe3a00000, 0xe3510001\n"
        ".word 0x13510002, 0x03a0100e, 0x13a01003, 0xe5a41004\n"
        ".word 0xe5840004, 0x0a000010, 0xe3a00000, 0xebfd0212\n"
        ".word 0xe3500003, 0xe320f000, 0x1a000002, 0xe3a0100a\n"
        ".word 0xe3a00000, 0xebfc78b6, 0xe3a00001, 0xebfd020a\n"
        ".word 0xe3500003, 0xe320f000, 0x1a000003, 0xe8bd4070\n"
        ".word 0xe3a0100a, 0xe3a00001, 0xeafc78ad, 0xe8bd8070\n"
        ".word 0x00405968\n"
    );
}

// DECOMP_FUNC(0x0022c780, 488)
// 121 ARM instructions through unconditional pop; 4 trailing data bytes.
extern "C" __attribute__((naked)) void func_0022c780() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d47f0, 0xe1a07000, 0xe59f01d4, 0xe5978010\n"
        ".word 0xe5870000, 0xe3580000, 0x0a00006f, 0xe5980068\n"
        ".word 0xe5981060, 0xe288405c, 0xe0800001, 0xe0400001\n"
        ".word 0xe3500000, 0xda000003, 0xe1b000c0, 0x0a000001\n"
        ".word 0xe2500001, 0x1afffffd, 0xe5940000, 0xe5902000\n"
        ".word 0xe5922004, 0xe12fff32, 0xe3a0a000, 0xe584a004\n"
        ".word 0xe288004c, 0xe584a008, 0xebfffe92, 0xe598003c\n"
        ".word 0xe5985034, 0xe2889030, 0xe0856200, 0xe1550006\n"
        ".word 0x2a000016, 0xe1a04005, 0xe2855010, 0xe5940008\n"
        ".word 0xe3500000, 0x11500004, 0x1a000007, 0xe5941004\n"
        ".word 0xe3510000, 0x0a00000a, 0xe5940000, 0xe5902000\n"
        ".word 0xe5922004, 0xe12fff32, 0xea000005, 0xe594100c\n"
        ".word 0xe580100c, 0xe1c400d8, 0xe5810008, 0xe584a008\n"
        ".word 0xe584a00c, 0xe1550006, 0xe584a004, 0x3affffe8\n"
        ".word 0xe1c900d0, 0xe5902000, 0xe5922004, 0xe12fff32\n"
        ".word 0xe589a004, 0xe589a008, 0xe598002c, 0xe5985024\n"
        ".word 0xe2889020, 0xe0856200, 0xe1550006, 0x2a000016\n"
        ".word 0xe1a04005, 0xe2855010, 0xe5940008, 0xe3500000\n"
        ".word 0x11500004, 0x1a000007, 0xe5941004, 0xe3510000\n"
        ".word 0x0a00000a, 0xe5940000, 0xe5902000, 0xe5922004\n"
        ".word 0xe12fff32, 0xea000005, 0xe594100c, 0xe580100c\n"
        ".word 0xe1c400d8, 0xe5810008, 0xe584a008, 0xe584a00c\n"
        ".word 0xe1550006, 0xe584a004, 0x3affffe8, 0xe1c900d0\n"
        ".word 0xe5902000, 0xe5922004, 0xe12fff32, 0xe589a004\n"
        ".word 0xe2884004, 0xe589a008, 0xe5b81008, 0xe5980008\n"
        ".word 0xe0800001, 0xe0400001, 0xe3500000, 0xda000003\n"
        ".word 0xe1b000c0, 0x0a000001, 0xe2500001, 0x1afffffd\n"
        ".word 0xe5940000, 0xe5902000, 0xe5922004, 0xe12fff32\n"
        ".word 0xe584a004, 0xe584a008, 0xe1c700dc, 0xe5902000\n"
        ".word 0xe5922004, 0xe12fff32, 0xe587a010, 0xe1a00007\n"
        ".word 0xe8bd87f0, 0x00422190\n"
    );
}

// DECOMP_FUNC(0x0024f800, 488)
// 119 ARM instructions through unconditional pop; 12 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_0024f800() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d40f0, 0xe1a04001, 0xe1a05000, 0xe59f71c8\n"
        ".word 0xe5901014, 0xe24dd044, 0xe5970000, 0xeb01c946\n"
        ".word 0xe2850018, 0xeddf4a6e, 0xe1a0100d, 0xec900a08\n"
        ".word 0xe2850038, 0xec8d0a08, 0xed9f0a68, 0xecd00a08\n"
        ".word 0xe28d001c, 0xed8d0a03, 0xec800a09, 0xed8d0a0b\n"
        ".word 0xedcd4a0f, 0xe5970000, 0xeb03cf1c, 0xe1a00004\n"
        ".word 0xeb001eed, 0xe1d501b2, 0xe5974000, 0xe3a06000\n"
        ".word 0xe3100c01, 0xe1a01006, 0x0a000010, 0xe3a00005\n"
        ".word 0xeb01d9bd, 0xe2844a01, 0xe2844f93, 0xe1a01000\n"
        ".word 0xe5940000, 0xe2802001, 0xe0843100, 0xe5930008\n"
        ".word 0xe0843102, 0xe5842000, 0xe5831008, 0xe5d42018\n"
        ".word 0xe3520000, 0x01500001, 0x0a000014, 0xea00000f\n"
        ".word 0xe3a00001, 0xeb01d9ac, 0xe2844a01, 0xe2844f93\n"
        ".word 0xe1a01000, 0xe5940000, 0xe0842100, 0xe2800001\n"
        ".word 0xe5922008, 0xe0843100, 0xe5840000, 0xe5831008\n"
        ".word 0xe5d40018, 0xe3500000, 0x01520001, 0x0a000003\n"
        ".word 0xe594201c, 0xe1a00001, 0xe12fff32, 0xe5c46018\n"
        ".word 0xe5951058, 0xe3510000, 0x0a000002, 0xe5950000\n"
        ".word 0xeb03deb5, 0xe5856058, 0xe5950000, 0xeb03de17\n"
        ".word 0xe1d500f8, 0xe3a04000, 0xe3500000, 0xda00000e\n"
        ".word 0xe5950004, 0xe0801204, 0xe5970000, 0xeb03d017\n"
        ".word 0xe1d510fc, 0xe0842084, 0xe5950000, 0xe0020291\n"
        ".word 0xe0813081, 0xe3a01000, 0xebffafc4, 0xe1d500f8\n"
        ".word 0xe2844001, 0xe1500004, 0xcafffff0, 0xe5970000\n"
        ".word 0xeb01c84d, 0xe5970000, 0xe320f000, 0xeb01c874\n"
        ".word 0xe5970000, 0xe2804a01, 0xe2844f93, 0xe5940000\n"
        ".word 0xe0841100, 0xe2400001, 0xe5911008, 0xe5840000\n"
        ".word 0xe0840100, 0xe5d42018, 0xe5900008, 0xe3520000\n"
        ".word 0x01510000, 0x0a000002, 0xe594101c, 0xe12fff31\n"
        ".word 0xe5c46018, 0xe28dd044, 0xe8bd80f0, 0x0044ea00\n"
        ".word 0x00000000, 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x0035edd4, 488)
// 121 ARM instructions through unconditional pop; 4 trailing data bytes.
extern "C" __attribute__((naked)) void func_0035edd4() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4fff, 0xe24dd024, 0xe1a06000, 0xe1a05001\n"
        ".word 0xe1a08002, 0xe28d000c, 0xe59d705c, 0xe59da058\n"
        ".word 0xebffffaf, 0xe5961020, 0xe28d000c, 0xebffffa4\n"
        ".word 0xe3a01002, 0xe28d000c, 0xebfb678c, 0xe3500000\n"
        ".word 0x1bfff508, 0xe58d0000, 0xe3a01001, 0xe28d000c\n"
        ".word 0xebfb6786, 0xe3500000, 0x1bfff606, 0xe58d0004\n"
        ".word 0xe3a01002, 0xe28d000c, 0xebfb6780, 0xe3500000\n"
        ".word 0x1bfffae1, 0xe1a04000, 0xe3a01002, 0xe28d000c\n"
        ".word 0xebfb677a, 0xe3500000, 0x1bfffe4c, 0xe1a09000\n"
        ".word 0xe3a01001, 0xe28d000c, 0xebfb6774, 0xe3500000\n"
        ".word 0x13a01000, 0x15801000, 0xe1a0b000, 0xe59d3030\n"
        ".word 0xe59d0000, 0xe1a02008, 0xe28d100c, 0xebfff133\n"
        ".word 0xe3500000, 0x1a000042, 0xe59d0004, 0xe59d1000\n"
        ".word 0xe28f2f43, 0xebfff51f, 0xe3500000, 0xe3a08001\n"
        ".word 0x0a000015, 0xe3570000, 0xe3a04000, 0x9a000038\n"
        ".word 0xe5d6001b, 0xe7951104, 0xe1110018, 0x1a00000a\n"
        ".word 0xe79a2104, 0xe59d0004, 0xe59d1000, 0xebfff511\n"
        ".word 0xe3500001, 0xe320f000, 0x1a000003, 0xe5d6001b\n"
        ".word 0xe7951104, 0xe1810018, 0xe7850104, 0xe2844001\n"
        ".word 0xe1540007, 0x3affffed, 0xea000025, 0xe59d2000\n"
        ".word 0xe28d100c, 0xe1a00004, 0xebfffa7c, 0xe3500000\n"
        ".word 0xe320f000, 0x1a00001e, 0xe5940010, 0xe28d3020\n"
        ".word 0xe2842004, 0xe58d0020, 0xe28d100c, 0xe1a00009\n"
        ".word 0xebfffd7f, 0xe3500000, 0xe320f000, 0x0a000014\n"
        ".word 0xe3570000, 0xe3a04000, 0x9a000011, 0xe5d6101b\n"
        ".word 0xe7950104, 0xe1100118, 0x1a00000a, 0xe79a2104\n"
        ".word 0xe2891004, 0xe1a0000b, 0xebfff050, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000003, 0xe5d6001b, 0xe7951104\n"
        ".word 0xe1810018, 0xe7850104, 0xe2844001, 0xe1540007\n"
        ".word 0x3affffed, 0xe28d000c, 0xe1a00000, 0xe28dd034\n"
        ".word 0xe8bd8ff0, 0x00000000\n"
    );
}

// DECOMP_FUNC(0x003912d0, 488)
// 115 ARM instructions through unconditional pop; 28 trailing data bytes.
extern "C" __attribute__((naked)) void ui_func_003912d0() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d5ff0, 0xed2d8b04, 0xe24dde41, 0xebfcbdf9\n"
        ".word 0xe59f21b4, 0xe5901000, 0xe5925000, 0xe3110a01\n"
        ".word 0x0a000065, 0xe59f11a4, 0xe7911000, 0xe3510000\n"
        ".word 0x13510001, 0x02804a01, 0x02844e7d, 0x0a000003\n"
        ".word 0xe3510002, 0x02804b06, 0x0284405c, 0x1a00005a\n"
        ".word 0xe1a00004, 0xebfcb714, 0xe1a07000, 0xe1a00004\n"
        ".word 0xebfcb70e, 0xe59f9168, 0xe1a06000, 0xe5990000\n"
        ".word 0xebfcca18, 0xe5994000, 0xe3a01000, 0xe3a00001\n"
        ".word 0xebfcd309, 0xe2844a01, 0xe2844f93, 0xe3a0a000\n"
        ".word 0xe5941000, 0xe2812001, 0xe0843101, 0xe5931008\n"
        ".word 0xe0843102, 0xe5842000, 0xe5830008, 0xe5d42018\n"
        ".word 0xe3520000, 0x01510000, 0x0a000002, 0xe594101c\n"
        ".word 0xe12fff31, 0xe5c4a018, 0xe3a00081, 0xe58d0004\n"
        ".word 0xe1a03007, 0xe3a02006, 0xe3a0103a, 0xe3a00002\n"
        ".word 0xe58d6000, 0xebfcb867, 0xe59fb0e8, 0xe3a01065\n"
        ".word 0xe1a00005, 0xebfa8d55, 0xe28d8008, 0xe1a01000\n"
        ".word 0xe1a02008, 0xe1a00005, 0xebfa8d5b, 0xe2505000\n"
        ".word 0xe3a04000, 0xda000017, 0xed9f8a2f, 0xeddf8a2f\n"
        ".word 0xed9f9a2f, 0xe2841043, 0xe3a0003a, 0xebfcb8b3\n"
        ".word 0xe1d010f8, 0xe1d000fa, 0xeeb02a48, 0xe0813007\n"
        ".word 0xe080c006, 0xee00ca10, 0xeef01a68, 0xeeb01a49\n"
        ".word 0xe0882384, 0xe1a0100b, 0xe3a00003, 0xeef80ac0\n"
        ".word 0xee003a10, 0xeeb80ac0, 0xebfcb4cf, 0xe2844001\n"
        ".word 0xe1540005, 0xbaffffea, 0xe5990000, 0xe2804a01\n"
        ".word 0xe2844f93, 0xe5940000, 0xe0841100, 0xe2400001\n"
        ".word 0xe5911008, 0xe5840000, 0xe0840100, 0xe5d42018\n"
        ".word 0xe5900008, 0xe3520000, 0x01510000, 0x0a000002\n"
        ".word 0xe594101c, 0xe12fff31, 0xe5c4a018, 0xe28dde41\n"
        ".word 0xe3a00000, 0xecbd8b04, 0xe8bd9ff0, 0x00432fc8\n"
        ".word 0x000017a4, 0x0044ea00, 0xfc4f46ff, 0x3f800000\n"
        ".word 0x00000000, 0x3f000000\n"
    );
}

// DECOMP_FUNC(0x002916d8, 492)
// 120 ARM instructions through unconditional pop; 12 trailing data bytes.
extern "C" __attribute__((naked)) void battle_func_002916d8() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d40f0, 0xe1a04000, 0xe1a05001, 0xe1a06002\n"
        ".word 0xed2d8b0a, 0xe24ddf41, 0xe1a07003, 0xedd09a00\n"
        ".word 0xed90ba01, 0xed90aa02, 0xeddfaa6c, 0xeb0059fe\n"
        ".word 0xe1a01000, 0xe1a0000d, 0xeb00ba3a, 0xee005a10\n"
        ".word 0xeddfba67, 0xed9fca67, 0xe28d0040, 0xeeb01a4c\n"
        ".word 0xeeb80ac0, 0xeef00a4c, 0xee200a2b, 0xeb0082f0\n"
        ".word 0xe1a0100d, 0xe28d2040, 0xe1a00001, 0xeb0096ab\n"
        ".word 0xec9d0a10, 0xee208a29, 0xee628a29, 0xee249a29\n"
        ".word 0xee669a29, 0xee008a8b, 0xee428a8b, 0xee049a8b\n"
        ".word 0xee469a8b, 0xee018a0a, 0xee438a0a, 0xee059a0a\n"
        ".word 0xee479a0a, 0xee018aaa, 0xee438aaa, 0xee059aaa\n"
        ".word 0xee479aaa, 0xeb0059dc, 0xe1a01000, 0xe1a0000d\n"
        ".word 0xeb00ba18, 0xee006a10, 0xeeb01a4c, 0xe28d0080\n"
        ".word 0xeeb80ac0, 0xee600a2b, 0xeeb00a4c, 0xeb0082d0\n"
        ".word 0xe1a0100d, 0xe28d2080, 0xe1a00001, 0xeb00968b\n"
        ".word 0xec9d0a10, 0xee20aa08, 0xee62aa08, 0xee24ba08\n"
        ".word 0xee268a08, 0xee00aaa8, 0xee42aaa8, 0xee04baa8\n"
        ".word 0xee068aa8, 0xee01aa09, 0xee43aa09, 0xee05ba09\n"
        ".word 0xee078a09, 0xee01aaa9, 0xee43aaa9, 0xee05baa9\n"
        ".word 0xee078aa9, 0xeb0059bc, 0xe1a01000, 0xe1a0000d\n"
        ".word 0xeb00b9f8, 0xee007a10, 0xeef00a4c, 0xe28d00c0\n"
        ".word 0xeeb80ac0, 0xee201a2b, 0xeeb00a4c, 0xeb0082b0\n"
        ".word 0xe1a0100d, 0xe28d20c0, 0xe1a00001, 0xeb00966b\n"
        ".word 0xed9d1a08, 0xed9d0a00, 0xeddd0a04, 0xee211a0a\n"
        ".word 0xee200a0a, 0xee600a8a, 0xeddd4a09, 0xeddd5a01\n"
        ".word 0xed9d5a05, 0xed9d3a0a, 0xed9d4a02, 0xeddd3a06\n"
        ".word 0xeddd1a0b, 0xee041aaa, 0xee050aaa, 0xee450a2a\n"
        ".word 0xeddd2a03, 0xed9d2a07, 0xee031a0b, 0xee040a0b\n"
        ".word 0xee430a8b, 0xee011a88, 0xee020a88, 0xee420a08\n"
        ".word 0xec840a03, 0xe28ddf41, 0xecbd8b0a, 0xe8bd80f0\n"
        ".word 0x3f800000, 0x3f360b61, 0x00000000\n"
    );
}

// DECOMP_FUNC(0x0014e804, 496)
// 119 ARM instructions through unconditional pop; 20 trailing data bytes.
extern "C" __attribute__((naked)) void func_0014e804() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4070, 0xe24dd018, 0xeddf1a73, 0xe1a04000\n"
        ".word 0xedcd1a02, 0xe28d000c, 0xeeb12a60, 0xecc00a03\n"
        ".word 0xeef12a41, 0xeddf0a6d, 0xeeb01a61, 0xe59f01b0\n"
        ".word 0xee300ac0, 0xe3a02000, 0xec8d2a02, 0xe1a03002\n"
        ".word 0xe3a0e000, 0xeeb40ae1, 0xeef1fa10, 0xeeb00ac0\n"
        ".word 0x33a0c001, 0x23a0c000, 0xee101a10, 0xe1510000\n"
        ".word 0xaddf0a60, 0xba000003, 0xee300a60, 0xee101a10\n"
        ".word 0xe1510000, 0xaafffffb, 0xeefc0ac1, 0xe3520000\n"
        ".word 0xee100a90, 0xeefc0ae1, 0xe6ff0070, 0xee101a90\n"
        ".word 0xeefc0ac0, 0xe6ff5071, 0xee101a90, 0xee000a90\n"
        ".word 0xe20000ff, 0xe6ff1071, 0xe20160ff, 0xeeb82a60\n"
        ".word 0xee005a90, 0xe20550ff, 0xeef82a60, 0xee001a90\n"
        ".word 0xe59f1124, 0xee311a42, 0xe0815205, 0xe0810200\n"
        ".word 0xeef80a60, 0xe0811206, 0xed953a01, 0xee711ae2\n"
        ".word 0xecf02a01, 0xedd13a01, 0xec904a03, 0xe3a005fe\n"
        ".word 0xee302a60, 0xed950a00, 0xe2855008, 0xedd10a00\n"
        ".word 0xe2811008, 0xecd55a02, 0xee412a24, 0xee014a05\n"
        ".word 0xecd16a02, 0xee010aa5, 0xee013a86, 0xe584e00c\n"
        ".word 0xee420a26, 0xee423a07, 0xe584e01c, 0xe1a01004\n"
        ".word 0x1ef12a62, 0xe3530000, 0x1eb10a40, 0xe35c0000\n"
        ".word 0x1ef10a60, 0xee222aa3, 0xeeb11a40, 0xee621aa0\n"
        ".word 0xee644a20, 0xed841a08, 0xee241a23, 0xee205a83\n"
        ".word 0xee633a83, 0xee622a83, 0xee243a03, 0xe584e02c\n"
        ".word 0xe584e030, 0xeef00a61, 0xe584e034, 0xe584003c\n"
        ".word 0xe584e038, 0xedc43a00, 0xed845a04, 0xee410a00\n"
        ".word 0xee011a80, 0xeef01a64, 0xee521a00, 0xee142a80\n"
        ".word 0xedc41a01, 0xed842a06, 0xedc40a02, 0xed841a05\n"
        ".word 0xe2843024, 0xe1a0200d, 0xe1a00001, 0xecc32a02\n"
        ".word 0xeb055376, 0xe1a02004, 0xe28d100c, 0xe1a00002\n"
        ".word 0xeb05536b, 0xe28dd018, 0xe8bd8070, 0x00000000\n"
        ".word 0x43800000, 0x47800000, 0x47800000, 0x00407fc0\n"
    );
}

// DECOMP_FUNC(0x0020d7b8, 500)
// 121 ARM instructions through unconditional pop; 16 trailing data bytes.
extern "C" __attribute__((naked)) void script_vm_func_0020d7b8() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d5ff0, 0xe59f81d8, 0xed2d8b02, 0xe5980000\n"
        ".word 0xe1d000bc, 0xe3500016, 0x1a00006f, 0xebff552e\n"
        ".word 0xe3a06000, 0xe59fb1c0, 0xe3a0a001, 0xed9f8a6d\n"
        ".word 0xe1a09006, 0xeddf8a6d, 0xea000003, 0xe3560000\n"
        ".word 0x13a07003, 0x13a04000, 0x1a000004, 0xe3a07009\n"
        ".word 0xe3a04000, 0xea000012, 0xe3560000, 0x0a000010\n"
        ".word 0xe5980000, 0xe0841084, 0xe0811184, 0xe0800101\n"
        ".word 0xe2805a01, 0xe2855e2a, 0xe5d50000, 0xe3500000\n"
        ".word 0x0a00004f, 0xe5db0022, 0xe3500000, 0x0a000016\n"
        ".word 0xe5950020, 0xe5901000, 0xe3110002, 0x0a000007\n"
        ".word 0xea00000f, 0xe5980000, 0xe0841084, 0xe0811184\n"
        ".word 0xe0800101, 0xe2805a01, 0xe2855f45, 0xeaffffed\n"
        ".word 0xe3811002, 0xe5801000, 0xe5900008, 0xeeb00a48\n"
        ".word 0xe590002c, 0xe5c091f6, 0xe5950020, 0xe5900008\n"
        ".word 0xeb023945, 0xe5c5a001, 0xea000035, 0xe5d50001\n"
        ".word 0xe3500000, 0x0a000032, 0xe5d50002, 0xe3500000\n"
        ".word 0xe5950020, 0xe5901000, 0xe2012002, 0x0a00000a\n"
        ".word 0xe3520000, 0x0a000013, 0xe3c11002, 0xe5801000\n"
        ".word 0xe5900008, 0xeeb00a68, 0xe590002c, 0xe5c0a1f6\n"
        ".word 0xe5950020, 0xe5900008, 0xea000009, 0xe3520000\n"
        ".word 0x1a000008, 0xe3811002, 0xe5801000, 0xe5900008\n"
        ".word 0xeeb00a48, 0xe590002c, 0xe5c091f6, 0xe5950020\n"
        ".word 0xe5900008, 0xeb023924, 0xe5950020, 0xe2852004\n"
        ".word 0xe3a01000, 0xe5900008, 0xeb01fbdc, 0xeeb00a48\n"
        ".word 0xe5950020, 0xedd50a04, 0xe3a01000, 0xe5900008\n"
        ".word 0xeeb01a40, 0xeb01fbcb, 0xe5950020, 0xe5900008\n"
        ".word 0xe5900038, 0xe5951014, 0xe1500001, 0x0a000003\n"
        ".word 0xe5950020, 0xeeb00a48, 0xe5900008, 0xeb026036\n"
        ".word 0xe5c59001, 0xe2844001, 0xe1540007, 0xbaffffa1\n"
        ".word 0xe2866001, 0xe3560002, 0xbaffff97, 0xecbd8b02\n"
        ".word 0xe8bd9ff0, 0x00447e10, 0x00000000, 0x0049f91c\n"
        ".word 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x00292c7c, 500)
// 121 ARM instructions through unconditional bx; 16 trailing data bytes.
extern "C" __attribute__((naked)) void battle_func_00292c7c() {
    asm volatile(
        ".arm\n"
        ".word 0xeddf1a77, 0xe92d03f0, 0xeeb40ae1, 0xe59f21d4\n"
        ".word 0xeef1fa10, 0xeeb00ac0, 0xeef40ae1, 0x33a03001\n"
        ".word 0x23a03000, 0xee105a10, 0xeef1fa10, 0xeef00ae0\n"
        ".word 0xeeb41ae1, 0x33a0c001, 0x23a0c000, 0xeef1fa10\n"
        ".word 0xeeb01ac1, 0xeddf1a68, 0x33a04001, 0x23a04000\n"
        ".word 0xe1550002, 0xba000003, 0xee300a61, 0xee105a10\n"
        ".word 0xe1550002, 0xaafffffb, 0xee105a90, 0xe1550002\n"
        ".word 0xba000003, 0xee700ae1, 0xee105a90, 0xe1550002\n"
        ".word 0xaafffffb, 0xee115a10, 0xe1550002, 0xba000003\n"
        ".word 0xee311a61, 0xee115a10, 0xe1550002, 0xaafffffb\n"
        ".word 0xeefc1ac0, 0xe3530000, 0xee112a90, 0xeefc1ae0\n"
        ".word 0xe6ff2072, 0xe20270ff, 0xee115a90, 0xeefc1ac1\n"
        ".word 0xe6ff5075, 0xe20580ff, 0xee116a90, 0xee012a90\n"
        ".word 0xe59f2118, 0xe6ff6076, 0xe20690ff, 0xeeb82a61\n"
        ".word 0xee015a90, 0xe0825207, 0xedd53a01, 0xeef82a61\n"
        ".word 0xee016a90, 0xe0826208, 0xee302a42, 0xe0822209\n"
        ".word 0xed960a00, 0xed924a01, 0xeef81a61, 0xee702ae2\n"
        ".word 0xedd20a00, 0xe2822008, 0xecd26a02, 0xe2802024\n"
        ".word 0xee313a61, 0xed951a00, 0xe2855008, 0xedd61a01\n"
        ".word 0xe2866008, 0xecd54a02, 0xecd65a02, 0xee021a24\n"
        ".word 0xee430a26, 0xee423a05, 0xee020aa5, 0xee034a07\n"
        ".word 0xee421a86, 0x1eb11a41, 0xe35c0000, 0x1eb10a40\n"
        ".word 0xe3540000, 0x1ef10a60, 0xee213a04, 0xee232a84\n"
        ".word 0xee244a21, 0xeef12a40, 0xe3510000, 0xee635aa0\n"
        ".word 0xee215a20, 0xee600aa1, 0xedc02a08, 0xee211a21\n"
        ".word 0xee631aa1, 0xed804a00, 0xeef02a65, 0xeef04a45\n"
        ".word 0xedc00a04, 0xee532a00, 0xee153a80, 0xee424a00\n"
        ".word 0xee052a00, 0xedc02a01, 0xed803a06, 0xedc04a02\n"
        ".word 0xed802a05, 0xec821a02, 0x0a000003, 0xe3a01000\n"
        ".word 0xe580100c, 0xe580101c, 0xe580102c, 0xe8bd03f0\n"
        ".word 0xe12fff1e, 0x00000000, 0x47800000, 0x47800000\n"
        ".word 0x00407fc0\n"
    );
}

// DECOMP_FUNC(0x0036eaf4, 500)
// 121 ARM instructions through unconditional pop; 16 trailing data bytes.
extern "C" __attribute__((naked)) void engine_func_0036eaf4() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe24dd00c, 0xe1b07001, 0xe1a08000\n"
        ".word 0xe3a0b000, 0x059f01c8, 0xe3a04000, 0x05907000\n"
        ".word 0xe5980000, 0xe5807014, 0xe5980000, 0xe490900c\n"
        ".word 0xe5901000, 0xe3510000, 0x10816000, 0x01a0600b\n"
        ".word 0xe3590000, 0x9a000064, 0xe5980000, 0xe5b01004\n"
        ".word 0xe3510000, 0x10800001, 0x01a0000b, 0xe7b01104\n"
        ".word 0xe3510000, 0x10815000, 0x01a0500b, 0xe1a00005\n"
        ".word 0xe7865104, 0xe3a00070, 0xe1a0a000, 0xe5970000\n"
        ".word 0xe3a02004, 0xe1a0100a, 0xe5903008, 0xe1a00007\n"
        ".word 0xe12fff33, 0xe2851018, 0xe8810401, 0xe5950020\n"
        ".word 0xe3500000, 0x1585b024, 0x1a000048, 0xe5950014\n"
        ".word 0xe59f3130, 0xe595100c, 0xe3500000, 0x059f0124\n"
        ".word 0xe595a008, 0xe7962104, 0xe1a00820, 0xe1a00800\n"
        ".word 0xe1500003, 0xe040c003, 0x0a000008, 0xaa000003\n"
        ".word 0xe28004ff, 0xe2500801, 0x1a000038, 0xea000020\n"
        ".word 0xe35c0801, 0x135c0802, 0x0a000009, 0xea000033\n"
        ".word 0xe3510000, 0xe285000c, 0x10800001, 0x01a0000b\n"
        ".word 0xe1a0100a, 0xebfd4e78, 0xe320f000, 0xe320f000\n"
        ".word 0xea00002a, 0xe59fc0c4, 0xe2000803, 0xe58d0000\n"
        ".word 0xe59f10b4, 0xe59cc000, 0xe1a0300a, 0xe12fff3c\n"
        ".word 0xe58d0004, 0xe595100c, 0xe285000c, 0xe1a0200a\n"
        ".word 0xe3510000, 0x10800001, 0xe59d1004, 0x01a0000b\n"
        ".word 0xebfcdf55, 0xe59d0004, 0xe5850020, 0xe59d0000\n"
        ".word 0xea000015, 0xe59fc074, 0xe59f106c, 0xe1a0300a\n"
        ".word 0xe3a00801, 0xe59cc000, 0xe12fff3c, 0xe58d0000\n"
        ".word 0xe595100c, 0xe1a03000, 0xe285000c, 0xe3510000\n"
        ".word 0x10811000, 0x01a0100b, 0xe1a0200a, 0xe1a00003\n"
        ".word 0xebfcf823, 0xe59d0000, 0xe1a0100a, 0xebfd4e4e\n"
        ".word 0xe59d0000, 0xe5850020, 0xe3a00801, 0xe5850024\n"
        ".word 0xe2844001, 0xe1540009, 0x3affff9a, 0xe28dd00c\n"
        ".word 0xe8bd8ff0, 0x00471c40, 0x02010000, 0x00000102\n"
        ".word 0x0044e330\n"
    );
}

// DECOMP_FUNC(0x003a0080, 500)
// 113 ARM instructions through unconditional pop; 48 trailing data bytes.
extern "C" __attribute__((naked)) void shop_func_003a0080() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d41f0, 0xe1a04000, 0xe3a00000, 0xe5c40010\n"
        ".word 0xe5c40011, 0xe5947000, 0xe1d401f2, 0xebfbf616\n"
        ".word 0xe1a05000, 0xe1d401f4, 0xebfbf613, 0xe3550000\n"
        ".word 0xe3a01001, 0xe1a06000, 0x15c41010, 0xe3560000\n"
        ".word 0x15c41011, 0xe1d401f2, 0xebfc3df1, 0xe3500000\n"
        ".word 0x0a000003, 0xe1c400d0, 0xe1500001, 0x0a000022\n"
        ".word 0xea000004, 0xe3550002, 0x1a000005, 0xe1c400d0\n"
        ".word 0xe1500001, 0xaa000002, 0xe2800001, 0xe5840000\n"
        ".word 0xea000042, 0xe1d401f4, 0xebfc3de1, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000007, 0xe5940000, 0xe5941008\n"
        ".word 0xe1500001, 0x1a000001, 0xe5940004, 0xeafffff2\n"
        ".word 0xe2400001, 0xeafffff0, 0xe3560002, 0x1a000002\n"
        ".word 0xe5940000, 0xe3500000, 0xcafffff8, 0xe3a00000\n"
        ".word 0xeb008ad5, 0xe3500000, 0xe320f000, 0x0a000004\n"
        ".word 0xe1c400d0, 0xe1500001, 0x1a000001, 0xe5940008\n"
        ".word 0xeaffffe1, 0xe3a00000, 0xeb008afb, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000003, 0xe5940000, 0xe5941008\n"
        ".word 0xe1500001, 0x0affffe3, 0xe3a00000, 0xeb008ae6\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000002, 0xe5940000\n"
        ".word 0xe280000a, 0xe5840000, 0xe3a00000, 0xeb008ad2\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000002, 0xe5940000\n"
        ".word 0xe240000a, 0xe5840000, 0xe3a00000, 0xeb008aa6\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000002, 0xe5940000\n"
        ".word 0xe2800001, 0xe5840000, 0xe3a00000, 0xeb008ab6\n"
        ".word 0xe3500000, 0xe5940000, 0x12400001, 0x1affffba\n"
        ".word 0xe5941008, 0xe1500001, 0xd1a00001, 0xe5941004\n"
        ".word 0xe5840000, 0xe1500001, 0xc1a00001, 0xe1500007\n"
        ".word 0xe5840000, 0x0a000001, 0xe8bd41f0, 0xeafa4cd5\n"
        ".word 0xe8bd81f0, 0xe1d020b2, 0xe1d130b2, 0xe2022001\n"
        ".word 0xe2033001, 0xe1120003, 0x1a000005, 0xe3530000\n"
        ".word 0x13a00001, 0x112fff1e, 0xe3520000, 0x13e00000\n"
        ".word 0x112fff1e\n"
    );
}
