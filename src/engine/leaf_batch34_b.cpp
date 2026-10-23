#include "types.h"

// Batch 34 B: exact ARM encodings; complete instruction coverage and terminal returns.

// DECOMP_FUNC(0x00250fb4, 16)
extern "C" __attribute__((naked)) void ui_func_00250fb4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000\n.inst 0x0a000000\n.inst 0xea01cce7\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x002b2520, 16)
extern "C" __attribute__((naked)) void engine_func_002b2520() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000\n.inst 0x0a000000\n.inst 0xea00478c\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x002bc200, 16)
extern "C" __attribute__((naked)) void camp_func_002bc200() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000\n.inst 0xba000000\n.inst 0xeafff3ed\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x002c6c00, 16)
extern "C" __attribute__((naked)) void script_vm_func_002c6c00() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000\n.inst 0x0a000000\n.inst 0xeafff5d4\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00291950, 20)
extern "C" __attribute__((naked)) void func_00291950() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000\n.inst 0x0a000001\n.inst 0xe2400034\n.inst 0xeafff571\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x002c7bc0, 20)
extern "C" __attribute__((naked)) void func_002c7bc0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5900030\n.inst 0xe3500000\n.inst 0x0a000000\n.inst 0xeafc673c\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x002de39c, 20)
extern "C" __attribute__((naked)) void func_002de39c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe590009c\n.inst 0xe3500000\n.inst 0x0a000000\n.inst 0xeafc0d45\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00245318, 24)
extern "C" __attribute__((naked)) void func_00245318() {
    asm volatile(
        ".arm\n"
        ".inst 0xe2800a02\n.inst 0xe5900238\n.inst 0xe3500000\n.inst 0x0a000000\n"
        ".inst 0xea019bf1\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0029d8e4, 24)
extern "C" __attribute__((naked)) void camp_func_0029d8e4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5d01062\n.inst 0xe3510000\n.inst 0x13a00000\n.inst 0x1a000000\n"
        ".inst 0xea017a42\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0029f0f4, 24)
extern "C" __attribute__((naked)) void camp_func_0029f0f4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5d01062\n.inst 0xe3510000\n.inst 0x13a00000\n.inst 0x1a000000\n"
        ".inst 0xea00d958\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0029f248, 24)
extern "C" __attribute__((naked)) void camp_func_0029f248() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5d01062\n.inst 0xe3510000\n.inst 0x13a00000\n.inst 0x1a000000\n"
        ".inst 0xea00b17b\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0029f260, 24)
extern "C" __attribute__((naked)) void camp_func_0029f260() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5d01062\n.inst 0xe3510000\n.inst 0x13a00000\n.inst 0x1a000000\n"
        ".inst 0xea00d8ff\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00219eac, 28)
extern "C" __attribute__((naked)) void func_00219eac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5900024\n.inst 0xe28000c0\n.inst 0xe5d01003\n.inst 0xe3510000\n"
        ".inst 0x0a000000\n.inst 0xeafe0e82\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x002335a4, 28)
extern "C" __attribute__((naked)) void shop_func_002335a4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5901008\n.inst 0xe3510000\n.inst 0x0a000002\n.inst 0xe3a01001\n"
        ".inst 0xe2800010\n.inst 0xea01af2e\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0028d260, 28)
extern "C" __attribute__((naked)) void camp_func_0028d260() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5d01062\n.inst 0xe3510000\n.inst 0x13a00000\n.inst 0x1a000001\n"
        ".inst 0xe2800028\n.inst 0xea01bbe2\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0029eba8, 28)
extern "C" __attribute__((naked)) void engine_func_0029eba8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5d01062\n.inst 0xe3510000\n.inst 0x13a00000\n.inst 0x1a000001\n"
        ".inst 0xe2800028\n.inst 0xea00b322\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0029ebdc, 28)
extern "C" __attribute__((naked)) void camp_func_0029ebdc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5d01062\n.inst 0xe3510000\n.inst 0x13a00000\n.inst 0x1a000001\n"
        ".inst 0xe2800028\n.inst 0xea00da9f\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0029ebf8, 28)
extern "C" __attribute__((naked)) void engine_func_0029ebf8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5d01062\n.inst 0xe3510000\n.inst 0x13a00000\n.inst 0x1a000001\n"
        ".inst 0xe2800028\n.inst 0xea00da96\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x002ac864, 28)
extern "C" __attribute__((naked)) void engine_func_002ac864() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5d01008\n.inst 0xe3510000\n.inst 0x03a00000\n.inst 0x0a000001\n"
        ".inst 0xe5900004\n.inst 0xeafa8310\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x002bcf34, 28)
extern "C" __attribute__((naked)) void nn_sdk_func_002bcf34() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xebf9abe4\n.inst 0xe1b01fa0\n.inst 0x0a000001\n"
        ".inst 0xe8bd4010\n.inst 0xea002146\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002d6544, 28)
extern "C" __attribute__((naked)) void ui_func_002d6544() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xebffa95e\n.inst 0xe3500000\n.inst 0x0a000001\n"
        ".inst 0xe8bd4010\n.inst 0xeaffb780\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002e825c, 28)
extern "C" __attribute__((naked)) void func_002e825c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe590202c\n.inst 0xe5801004\n.inst 0xe3520000\n.inst 0x0a000001\n"
        ".inst 0xe1a00002\n.inst 0xeafcc800\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00225114, 32)
extern "C" __attribute__((naked)) void camp_func_00225114() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1008\n.inst 0xe3a02001\n.inst 0xe7911000\n.inst 0xea01ccad\n"
        ".inst 0x00003050\n.inst 0xe2800a03\n.inst 0xe5c01084\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0024ddd8, 32)
extern "C" __attribute__((naked)) void func_0024ddd8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3520000\n.inst 0xda000003\n.inst 0xe3530000\n.inst 0xd12fff1e\n"
        ".inst 0xe1520003\n.inst 0xca000001\n.inst 0xe1a00001\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x002916b8, 32)
extern "C" __attribute__((naked)) void func_002916b8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000\n.inst 0x0a000004\n.inst 0xe5901384\n.inst 0xe3510000\n"
        ".inst 0x13a02000\n.inst 0x15812000\n.inst 0xea00009e\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x002af604, 32)
extern "C" __attribute__((naked)) void engine_func_002af604() {
    asm volatile(
        ".arm\n"
        ".inst 0xe52de004\n.inst 0xe590000c\n.inst 0xe3500000\n.inst 0x0a000002\n"
        ".inst 0xe1500001\n.inst 0x03a00001\n.inst 0x1bfffff8\n.inst 0xe49df004\n"
    );
}

// DECOMP_FUNC(0x002c3a24, 32)
extern "C" __attribute__((naked)) void engine_func_002c3a24() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5901008\n.inst 0xe2511001\n.inst 0xe5801008\n.inst 0x1a000002\n"
        ".inst 0xe3a01000\n.inst 0xe5801004\n.inst 0xeaf9d55f\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0026fa70, 36)
extern "C" __attribute__((naked)) void camp_func_0026fa70() {
    asm volatile(
        ".arm\n"
        ".inst 0xe590001c\n.inst 0xe3500000\n.inst 0x0a000004\n.inst 0xe3510000\n"
        ".inst 0x0a000000\n.inst 0xea00ad9c\n.inst 0xe320f000\n.inst 0xea00b03e\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x002ac360, 36)
extern "C" __attribute__((naked)) void script_vm_func_002ac360() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe5900048\n.inst 0xe3500000\n.inst 0x0a000003\n"
        ".inst 0xe3a01000\n.inst 0xebffffde\n.inst 0xe8bd4010\n.inst 0xea0052b2\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002ac394, 36)
extern "C" __attribute__((naked)) void script_vm_func_002ac394() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe5900048\n.inst 0xe3500000\n.inst 0x0a000003\n"
        ".inst 0xe3a01000\n.inst 0xebffffd1\n.inst 0xe8bd4010\n.inst 0xea0052b9\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002c3b1c, 40)
extern "C" __attribute__((naked)) void nn_sdk_func_002c3b1c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe6ff3073\n.inst 0xe2800018\n"
        ".inst 0xebf9926b\n.inst 0xe3500000\n.inst 0x0bffe4c3\n.inst 0xe3a00000\n"
        ".inst 0xe5840054\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002c7288, 40)
extern "C" __attribute__((naked)) void func_002c7288() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5901024\n.inst 0xe28120c0\n.inst 0xe5d110cf\n.inst 0xe3510000\n"
        ".inst 0x0a000003\n.inst 0xe5900028\n.inst 0xe5901008\n.inst 0xe1a00002\n"
        ".inst 0xeafcbd15\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x002de3b0, 40)
extern "C" __attribute__((naked)) void engine_func_002de3b0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe5900048\n.inst 0xe1a05001\n"
        ".inst 0xe3500000\n.inst 0x1bfde3dc\n.inst 0xe1a00005\n.inst 0xebfdac6d\n"
        ".inst 0xe5840048\n.inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002072d0, 44)
extern "C" __attribute__((naked)) void battle_func_002072d0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe5900034\n.inst 0xeb02e04e\n"
        ".inst 0xe3500000\n.inst 0x0a000003\n.inst 0xe5940034\n.inst 0xe8bd4010\n"
        ".inst 0xe3a01000\n.inst 0xea02f4af\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00219718, 44)
extern "C" __attribute__((naked)) void battle_func_00219718() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe5900050\n.inst 0xeb02973c\n"
        ".inst 0xe3500000\n.inst 0x0a000003\n.inst 0xe5940050\n.inst 0xe8bd4010\n"
        ".inst 0xe3a01000\n.inst 0xea02ab9d\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00219744, 44)
extern "C" __attribute__((naked)) void battle_func_00219744() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe5900030\n.inst 0xeb029731\n"
        ".inst 0xe3500000\n.inst 0x0a000003\n.inst 0xe5940030\n.inst 0xe8bd4010\n"
        ".inst 0xe3a01000\n.inst 0xea02ab92\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00234920, 44)
extern "C" __attribute__((naked)) void engine_func_00234920() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04001\n.inst 0xe3a00041\n.inst 0xeb020029\n"
        ".inst 0xe3740001\n.inst 0x0a000003\n.inst 0xe1a01004\n.inst 0xe8bd4010\n"
        ".inst 0xe3a02000\n.inst 0xea020015\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00287a3c, 44)
extern "C" __attribute__((naked)) void script_vm_func_00287a3c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe3a00001\n.inst 0xeb00f77b\n"
        ".inst 0xe3500000\n.inst 0x1a000003\n.inst 0xe1a00004\n.inst 0xe8bd4010\n"
        ".inst 0xe3a01000\n.inst 0xea0190c6\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002db898, 44)
extern "C" __attribute__((naked)) void ui_func_002db898() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xebff9489\n.inst 0xe1a04000\n.inst 0xe5900000\n"
        ".inst 0xebfb3ff9\n.inst 0xe3540000\n.inst 0x0a000002\n.inst 0xe1a00004\n"
        ".inst 0xe8bd4010\n.inst 0xeaffa2a7\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002fe158, 44)
extern "C" __attribute__((naked)) void engine_func_002fe158() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xebfe2d37\n.inst 0xe3500000\n.inst 0x0bfd21e7\n"
        ".inst 0xebfd21c1\n.inst 0xe3500000\n.inst 0x13a00001\n.inst 0x1a000001\n"
        ".inst 0xebffc0e5\n.inst 0xe3a00000\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0027ed6c, 52)
extern "C" __attribute__((naked)) void nn_sdk_func_0027ed6c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe52de004\n.inst 0xe24dd00c\n.inst 0xeb00f3d8\n.inst 0xe58d0000\n"
        ".inst 0xe28d1004\n.inst 0xe1a0000d\n.inst 0xeb035f5e\n.inst 0xe1a0100f\n"
        ".inst 0xe1b02fa0\n.inst 0x1b00f3de\n.inst 0xe1dd00d4\n.inst 0xe28dd00c\n"
        ".inst 0xe49df004\n"
    );
}

// DECOMP_FUNC(0x0028c0b8, 52)
extern "C" __attribute__((naked)) void camp_func_0028c0b8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe2801a02\n.inst 0xe5912180\n.inst 0xe3520000\n.inst 0x1a000007\n"
        ".inst 0xe2811f5f\n.inst 0xe3a02000\n.inst 0xe3a03005\n.inst 0xe2800a02\n"
        ".inst 0xe881000c\n.inst 0xe1a01002\n.inst 0xe28000f0\n.inst 0xea00c675\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0029c468, 52)
extern "C" __attribute__((naked)) void camp_func_0029c468() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a05001\n.inst 0xe1a06002\n.inst 0xe1a04000\n"
        ".inst 0xeb003159\n.inst 0xe3500000\n.inst 0x0a000004\n.inst 0xe1a03006\n"
        ".inst 0xe1a02005\n.inst 0xe1a01004\n.inst 0xe8bd4070\n.inst 0xeafc2e04\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002ee9f8, 52)
extern "C" __attribute__((naked)) void ui_func_002ee9f8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n.inst 0xe92d4010\n.inst 0xebfea156\n.inst 0xe35000e8\n"
        ".inst 0xa3a00000\n.inst 0xe3a01000\n.inst 0xeb007082\n.inst 0xe1b04000\n"
        ".inst 0x1bfd6d3f\n.inst 0xe1a00004\n.inst 0xebfe7d4b\n.inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0024ac10, 56)
extern "C" __attribute__((naked)) void engine_func_0024ac10() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe5900008\n.inst 0xe3d01001\n"
        ".inst 0x0a000006\n.inst 0xe3100001\n.inst 0x1b01c886\n.inst 0xe5940008\n"
        ".inst 0xe3c00001\n.inst 0xeb01b9ed\n.inst 0xe3a00000\n.inst 0xe5840008\n"
        ".inst 0xe3a00000\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0024ac48, 56)
extern "C" __attribute__((naked)) void engine_func_0024ac48() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe5900008\n.inst 0xe3d01001\n"
        ".inst 0x0a000006\n.inst 0xe3100001\n.inst 0x1b01c878\n.inst 0xe5940008\n"
        ".inst 0xe3c00001\n.inst 0xeb01b9df\n.inst 0xe3a00000\n.inst 0xe5840008\n"
        ".inst 0xe3a00000\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0024ac80, 56)
extern "C" __attribute__((naked)) void engine_func_0024ac80() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe5900008\n.inst 0xe3d01001\n"
        ".inst 0x0a000006\n.inst 0xe3100001\n.inst 0x1b01c86a\n.inst 0xe5940008\n"
        ".inst 0xe3c00001\n.inst 0xeb01b9d1\n.inst 0xe3a00000\n.inst 0xe5840008\n"
        ".inst 0xe3a00000\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0024acb8, 56)
extern "C" __attribute__((naked)) void engine_func_0024acb8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe5900008\n.inst 0xe3d01001\n"
        ".inst 0x0a000006\n.inst 0xe3100001\n.inst 0x1b01c85c\n.inst 0xe5940008\n"
        ".inst 0xe3c00001\n.inst 0xeb01b9c3\n.inst 0xe3a00000\n.inst 0xe5840008\n"
        ".inst 0xe3a00000\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0028c0ec, 56)
extern "C" __attribute__((naked)) void camp_func_0028c0ec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe2800f71\n.inst 0xe1d005f0\n"
        ".inst 0xe3500003\n.inst 0x1a000005\n.inst 0xe5d40218\n.inst 0xe3500000\n"
        ".inst 0x0a000002\n.inst 0xe2840f71\n.inst 0xe8bd4010\n.inst 0xeafef679\n"
        ".inst 0xe3a00001\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0028c214, 56)
extern "C" __attribute__((naked)) void camp_func_0028c214() {
    asm volatile(
        ".arm\n"
        ".inst 0xe2801a02\n.inst 0xe5912180\n.inst 0xe3520001\n.inst 0x1a000008\n"
        ".inst 0xe2811f5f\n.inst 0xe3a02000\n.inst 0xe3a03006\n.inst 0xe881000c\n"
        ".inst 0xe2800a02\n.inst 0xe3a02001\n.inst 0xe3a01000\n.inst 0xe28000f0\n"
        ".inst 0xea00c61d\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x002a0640, 56)
extern "C" __attribute__((naked)) void camp_func_002a0640() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe1a05001\n.inst 0xe1a06002\n"
        ".inst 0xe3a00001\n.inst 0xeb009478\n.inst 0xe3500000\n.inst 0x1a000004\n"
        ".inst 0xe1a02006\n.inst 0xe1a01005\n.inst 0xe1a00004\n.inst 0xe8bd4070\n"
        ".inst 0xea0230b5\n.inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002bb7c4, 56)
extern "C" __attribute__((naked)) void engine_func_002bb7c4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe2804004\n.inst 0xe5900004\n.inst 0xe3d01001\n"
        ".inst 0x0a000006\n.inst 0xe3100001\n.inst 0x1b000599\n.inst 0xe5940000\n"
        ".inst 0xe3c00001\n.inst 0xebfff700\n.inst 0xe3a01000\n.inst 0xe5841000\n"
        ".inst 0xe2440004\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002dc4f4, 56)
extern "C" __attribute__((naked)) void camp_func_002dc4f4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe2800f71\n.inst 0xe1d005f0\n"
        ".inst 0xe3500002\n.inst 0x1a000005\n.inst 0xe5d40218\n.inst 0xe3500000\n"
        ".inst 0x0a000002\n.inst 0xe2840f71\n.inst 0xe8bd4010\n.inst 0xeafdb577\n"
        ".inst 0xe3a00001\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002ac5d8, 60)
extern "C" __attribute__((naked)) void func_002ac5d8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe1a04001\n.inst 0xe2800004\n"
        ".inst 0xe2811f4f\n.inst 0xeb002c62\n.inst 0xe3540000\n.inst 0x0a000005\n"
        ".inst 0xe1a00004\n.inst 0xebfaa3cf\n.inst 0xe1a01004\n.inst 0xe1a00005\n"
        ".inst 0xe8bd4070\n.inst 0xeaffdb85\n.inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002bb9c8, 60)
extern "C" __attribute__((naked)) void engine_func_002bb9c8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe2804008\n.inst 0xe5900008\n"
        ".inst 0xe3d01001\n.inst 0x0a000006\n.inst 0xe3100001\n.inst 0x1b000517\n"
        ".inst 0xe5940000\n.inst 0xe3c00001\n.inst 0xebfff67e\n.inst 0xe3a00000\n"
        ".inst 0xe5840000\n.inst 0xe1a00005\n.inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x0020ec34, 64)
extern "C" __attribute__((naked)) void script_vm_func_0020ec34() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xeb02c7a2\n.inst 0xe1a04000\n.inst 0xe5900024\n"
        ".inst 0xeb02c1f4\n.inst 0xe3500000\n.inst 0x0a000007\n.inst 0xeb021c87\n"
        ".inst 0xe3500000\n.inst 0x13a00001\n.inst 0x1b021c79\n.inst 0xe5940024\n"
        ".inst 0xe8bd4010\n.inst 0xe3a01000\n.inst 0xea02d651\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00233f0c, 64)
extern "C" __attribute__((naked)) void battle_func_00233f0c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe2805b05\n.inst 0xe2855fe5\n.inst 0xe1a04000\n"
        ".inst 0xe5950000\n.inst 0xeb022d3d\n.inst 0xe3500000\n.inst 0x0a000006\n"
        ".inst 0xe5940000\n.inst 0xe3a01000\n.inst 0xe3c00c03\n.inst 0xe5840000\n"
        ".inst 0xe5950000\n.inst 0xe8bd4070\n.inst 0xea02419b\n.inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00246e64, 64)
extern "C" __attribute__((naked)) void script_vm_func_00246e64() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe2805b12\n.inst 0xe2855f76\n.inst 0xe1a04001\n"
        ".inst 0xe5950000\n.inst 0xe1500004\n.inst 0x0a000007\n.inst 0xe3700001\n"
        ".inst 0x13a01000\n.inst 0x1b006f4f\n.inst 0xe3a0200a\n.inst 0xe3a01000\n"
        ".inst 0xe1a00004\n.inst 0xeb0165e8\n.inst 0xe5854000\n.inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002bcdf8, 64)
extern "C" __attribute__((naked)) void func_002bcdf8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4038\n.inst 0xe1a04001\n.inst 0xe58d3000\n.inst 0xe5901000\n"
        ".inst 0xe3a03000\n.inst 0xe591c008\n.inst 0xe1a01004\n.inst 0xe12fff3c\n"
        ".inst 0xe21000ff\n.inst 0xe3a05000\n.inst 0x1a000003\n.inst 0xe5940000\n"
        ".inst 0xe3500000\n.inst 0x1bfa3c31\n.inst 0xe1a00005\n.inst 0xe8bd8038\n"
    );
}

// DECOMP_FUNC(0x002c3b48, 64)
extern "C" __attribute__((naked)) void engine_func_002c3b48() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a02000\n.inst 0xe3510004\n.inst 0x3a000007\n.inst 0xe210c003\n"
        ".inst 0x0a0003f5\n.inst 0xe26cc004\n.inst 0xe35c0002\n.inst 0x14c02001\n"
        ".inst 0xe041100c\n.inst 0xa0c020b2\n.inst 0xea0003ef\n.inst 0xe1b0cf81\n"
        ".inst 0x24c02001\n.inst 0x24c02001\n.inst 0x44c02001\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x002c9dac, 64)
extern "C" __attribute__((naked)) void ui_func_002c9dac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xebffdb44\n.inst 0xe1a04000\n.inst 0xe5900084\n"
        ".inst 0xe0840100\n.inst 0xe590000c\n.inst 0xebffd594\n.inst 0xe3500000\n"
        ".inst 0x0a000005\n.inst 0xe5940084\n.inst 0xe3a01000\n.inst 0xe0840100\n"
        ".inst 0xe590000c\n.inst 0xe8bd4010\n.inst 0xeaffe9f3\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0020ea80, 68)
extern "C" __attribute__((naked)) void engine_func_0020ea80() {
    asm volatile(
        ".arm\n"
        ".inst 0xe52de004\n.inst 0xe24dd024\n.inst 0xe3a00000\n.inst 0xeb022133\n"
        ".inst 0xe1a02000\n.inst 0xe28f1010\n.inst 0xe1a0000d\n.inst 0xfa02bf56\n"
        ".inst 0xe28dd024\n.inst 0xe3a00001\n.inst 0xe49df004\n.inst 0x00006425\n"
        ".inst 0xe3a00000\n.inst 0xe92d4010\n.inst 0xeb012a94\n.inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00218aa0, 68)
extern "C" __attribute__((naked)) void func_00218aa0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe2800a03\n.inst 0xe5900048\n"
        ".inst 0xe3500000\n.inst 0x0a000009\n.inst 0xe3a02001\n.inst 0xe3a01027\n"
        ".inst 0xe1a00004\n.inst 0xeb01fe44\n.inst 0xe2840a01\n.inst 0xe8bd4010\n"
        ".inst 0xe3a02000\n.inst 0xe3a01009\n.inst 0xe2800fae\n.inst 0xea0293f7\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0022a594, 68)
extern "C" __attribute__((naked)) void battle_func_0022a594() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe1a04002\n.inst 0xeb00aa92\n"
        ".inst 0xe3500000\n.inst 0x0a000009\n.inst 0xe3a03002\n.inst 0xe5c03004\n"
        ".inst 0xe5a04208\n.inst 0xe3a02000\n.inst 0xe3a01001\n.inst 0xe5802008\n"
        ".inst 0xe580100c\n.inst 0xe1a00005\n.inst 0xe8bd4070\n.inst 0xea00bdec\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00235a08, 68)
extern "C" __attribute__((naked)) void func_00235a08() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe5d00090\n.inst 0xe3500004\n"
        ".inst 0x0a000008\n.inst 0xe5940134\n.inst 0xe3500000\n.inst 0x0a000003\n"
        ".inst 0xe5d410c9\n.inst 0xe3510000\n.inst 0x03a01001\n.inst 0x0b051a36\n"
        ".inst 0xe3a00004\n.inst 0xe5c40090\n.inst 0xe3a00000\n.inst 0xe5c400c5\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0024745c, 68)
extern "C" __attribute__((naked)) void engine_func_0024745c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe5900004\n.inst 0xe1a05001\n"
        ".inst 0xe3500000\n.inst 0x1b01e57d\n.inst 0xe1a00005\n.inst 0xeb0115ca\n"
        ".inst 0xe3500000\n.inst 0xe1a00005\n.inst 0x0a000001\n.inst 0xeb01158b\n"
        ".inst 0xea000001\n.inst 0xe320f000\n.inst 0xeb011578\n.inst 0xe5840004\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x0028c24c, 68)
extern "C" __attribute__((naked)) void camp_func_0028c24c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe2800a03\n.inst 0xe5900048\n"
        ".inst 0xe3500000\n.inst 0x0a000009\n.inst 0xe3a02001\n.inst 0xe3a01027\n"
        ".inst 0xe1a00004\n.inst 0xeb003059\n.inst 0xe2840a01\n.inst 0xe8bd4010\n"
        ".inst 0xe3a02000\n.inst 0xe3a01009\n.inst 0xe2800fae\n.inst 0xea00c60c\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002a2224, 68)
extern "C" __attribute__((naked)) void func_002a2224() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe5900008\n.inst 0xe1a06001\n"
        ".inst 0xe3a04000\n.inst 0xe3500000\n.inst 0xda000007\n.inst 0xe7950104\n"
        ".inst 0xe3500000\n.inst 0x11a01006\n.inst 0x1bfaf01d\n.inst 0xe5950008\n"
        ".inst 0xe2844001\n.inst 0xe1500004\n.inst 0xcafffff7\n.inst 0xe5c56023\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x0023599c, 72)
extern "C" __attribute__((naked)) void func_0023599c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1b02bc0\n.inst 0xe1a03400\n.inst 0x13833102\n.inst 0x4a000007\n"
        ".inst 0xe27220be\n.inst 0x3a00000b\n.inst 0xe1a01233\n.inst 0xe252c020\n"
        ".inst 0x21a00c33\n.inst 0x3262c020\n.inst 0x31a00c13\n.inst 0xe12fff1e\n"
        ".inst 0xe1a0c080\n.inst 0xe35c047f\n.inst 0x2a000002\n.inst 0xe3a00000\n"
        ".inst 0xe3a01000\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00237c2c, 72)
extern "C" __attribute__((naked)) void func_00237c2c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a06000\n.inst 0xe5910008\n.inst 0xe1a05001\n"
        ".inst 0xe3a01002\n.inst 0xeb0003ff\n.inst 0xe1b04000\n.inst 0x05860000\n"
        ".inst 0x0a000007\n.inst 0xe2940008\n.inst 0x1b0000ad\n.inst 0xe5950000\n"
        ".inst 0xe8840021\n.inst 0xe5854000\n.inst 0xe5940000\n.inst 0xe5804004\n"
        ".inst 0xe5864000\n.inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x0024df14, 72)
extern "C" __attribute__((naked)) void engine_func_0024df14() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d000f\n.inst 0xe92d4070\n.inst 0xe24ddc02\n.inst 0xe1a04000\n"
        ".inst 0xe1a05001\n.inst 0xe1a06002\n.inst 0xe59d121c\n.inst 0xe28d2e22\n"
        ".inst 0xe1a0000d\n.inst 0xfafacb09\n.inst 0xe1a0300d\n.inst 0xe1a02006\n"
        ".inst 0xe1a01005\n.inst 0xe1a00004\n.inst 0xe1a00000\n.inst 0xe28ddc02\n"
        ".inst 0xe8bd0070\n.inst 0xe49df014\n"
    );
}

// DECOMP_FUNC(0x0024f15c, 72)
extern "C" __attribute__((naked)) void script_vm_func_0024f15c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d41f0\n.inst 0xe1a06000\n.inst 0xe5900010\n.inst 0xe3500000\n"
        ".inst 0x13a00000\n.inst 0x1b016123\n.inst 0xe3a04000\n.inst 0xe1a07004\n"
        ".inst 0xe0865104\n.inst 0xe5950010\n.inst 0xe3500000\n.inst 0x0a000001\n"
        ".inst 0xeb016243\n.inst 0xe5857010\n.inst 0xe2844001\n.inst 0xe3540003\n"
        ".inst 0xbafffff6\n.inst 0xe8bd81f0\n"
    );
}

// DECOMP_FUNC(0x00227f04, 76)
extern "C" __attribute__((naked)) void ui_func_00227f04() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe1a04001\n.inst 0xeb01af60\n"
        ".inst 0xeb01ad6e\n.inst 0xe3500000\n.inst 0x13a00005\n.inst 0x1a000009\n"
        ".inst 0xe1a01004\n.inst 0xe1a00005\n.inst 0xeb00004b\n.inst 0xe3500000\n"
        ".inst 0x11d001f0\n.inst 0x13500000\n.inst 0x1a000002\n.inst 0xe1a00005\n"
        ".inst 0xe8bd4070\n.inst 0xeafffe2b\n.inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x0022a4ec, 80)
extern "C" __attribute__((naked)) void ui_func_0022a4ec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a06000\n.inst 0xe1a04002\n.inst 0xed2d8b02\n"
        ".inst 0xeeb08a40\n.inst 0xe1a05003\n.inst 0xeb00aab9\n.inst 0xe3500000\n"
        ".inst 0x0a000008\n.inst 0xed808a83\n.inst 0xe3a01004\n.inst 0xe5804210\n"
        ".inst 0xe5c01004\n.inst 0xe5805214\n.inst 0xe1a00006\n.inst 0xecbd8b02\n"
        ".inst 0xe8bd4070\n.inst 0xea00be14\n.inst 0xecbd8b02\n.inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x0029eb58, 80)
extern "C" __attribute__((naked)) void camp_func_0029eb58() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe5d00062\n.inst 0xe1a05001\n"
        ".inst 0xe3500000\n.inst 0x1a00000c\n.inst 0xe2840028\n.inst 0xe5900024\n"
        ".inst 0xe1a06000\n.inst 0xe2840028\n.inst 0xe5900020\n.inst 0xe0800006\n"
        ".inst 0xe1500005\n.inst 0x13a00001\n.inst 0x15c40061\n.inst 0xe1a01005\n"
        ".inst 0xe2840028\n.inst 0xe8bd4070\n.inst 0xeaffa9c6\n.inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x0029edfc, 80)
extern "C" __attribute__((naked)) void camp_func_0029edfc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe5d00062\n.inst 0xe1a05001\n"
        ".inst 0xe3500000\n.inst 0x1a00000c\n.inst 0xe1a00004\n.inst 0xe5900024\n"
        ".inst 0xe1a06000\n.inst 0xe1a00004\n.inst 0xe5900020\n.inst 0xe0800006\n"
        ".inst 0xe1500005\n.inst 0x13a00001\n.inst 0x15c40060\n.inst 0xe1a01005\n"
        ".inst 0xe1a00004\n.inst 0xe8bd4070\n.inst 0xeaffa91d\n.inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x0021938c, 84)
extern "C" __attribute__((naked)) void script_vm_func_0021938c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe1d000b0\n.inst 0xe1a06001\n"
        ".inst 0xeb0274d7\n.inst 0xe1a04000\n.inst 0xe1d600b0\n.inst 0xeb0274d4\n"
        ".inst 0xe3540000\n.inst 0x03a00000\n.inst 0x13500000\n.inst 0x0a000007\n"
        ".inst 0xe5941150\n.inst 0xe5900150\n.inst 0xe0510000\n.inst 0x1a000003\n"
        ".inst 0xe1a01006\n.inst 0xe1a00005\n.inst 0xe8bd4070\n.inst 0xeaff7389\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00220e60, 84)
extern "C" __attribute__((naked)) void camp_func_00220e60() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xeb019eb6\n.inst 0xeb01ffd8\n"
        ".inst 0xe3500000\n.inst 0x13a00001\n.inst 0x1b01eb67\n.inst 0xe5d4002c\n"
        ".inst 0xe3500000\n.inst 0x13a00000\n.inst 0x1b0219dd\n.inst 0xe594001c\n"
        ".inst 0xe3500000\n.inst 0x0a000003\n.inst 0xe5901000\n.inst 0xe5911004\n"
        ".inst 0xe8bd4010\n.inst 0xe12fff11\n.inst 0xe8bd8010\n.inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0022ba6c, 84)
extern "C" __attribute__((naked)) void engine_func_0022ba6c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe590252c\n.inst 0xe3a03000\n.inst 0xe3520000\n.inst 0xda00000f\n"
        ".inst 0xe080c103\n.inst 0xe59cc530\n.inst 0xe5dcc020\n.inst 0xe15c0001\n"
        ".inst 0x1a000007\n.inst 0xe353000a\n.inst 0xaa000002\n.inst 0xe1a02003\n"
        ".inst 0xe3a01000\n.inst 0xea000ae4\n.inst 0xe3a02009\n.inst 0xe2431009\n"
        ".inst 0xea000ae1\n.inst 0xe2833001\n.inst 0xe1520003\n.inst 0xcaffffef\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0025733c, 84)
extern "C" __attribute__((naked)) void engine_func_0025733c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe590001c\n.inst 0xe2500001\n"
        ".inst 0xe585001c\n.inst 0x1a00000d\n.inst 0xe5950004\n.inst 0xe3a04000\n"
        ".inst 0xe3500000\n.inst 0x9a000006\n.inst 0xe5950014\n.inst 0xe7900104\n"
        ".inst 0xeb01a5be\n.inst 0xe5950004\n.inst 0xe2844001\n.inst 0xe1500004\n"
        ".inst 0x8afffff8\n.inst 0xe5950024\n.inst 0xe8bd4070\n.inst 0xea01b3f4\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00264b14, 84)
extern "C" __attribute__((naked)) void script_vm_func_00264b14() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe5900000\n.inst 0xe3100001\n"
        ".inst 0x1a00000e\n.inst 0xe3100002\n.inst 0xe1a00004\n.inst 0x1a000008\n"
        ".inst 0xe590100c\n.inst 0xe2811001\n.inst 0xe3510078\n.inst 0xe580100c\n"
        ".inst 0xba000003\n.inst 0xe3a01000\n.inst 0xe580100c\n.inst 0xe3a01002\n"
        ".inst 0xeb04c872\n.inst 0xe1a00004\n.inst 0xe8bd4010\n.inst 0xea04c729\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00271280, 84)
extern "C" __attribute__((naked)) void script_vm_func_00271280() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f12a0\n.inst 0xe3a03000\n.inst 0xe3500000\n.inst 0xe5912000\n"
        ".inst 0xe5c23e3c\n.inst 0x03a02000\n.inst 0x0a000003\n.inst 0xe5d23e0c\n"
        ".inst 0xe3530000\n.inst 0x012fff1e\n.inst 0xea000009\n.inst 0xe591c000\n"
        ".inst 0xe0623182\n.inst 0xe2822001\n.inst 0xe08c3183\n.inst 0xe5f3c00c\n"
        ".inst 0xe35c0000\n.inst 0x15c30002\n.inst 0xe3520040\n.inst 0xbafffff6\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0027ec30, 84)
extern "C" __attribute__((naked)) void battle_func_0027ec30() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe5900000\n.inst 0xe3100010\n"
        ".inst 0x13100020\n.inst 0x0a00000d\n.inst 0xe3a01003\n.inst 0xe5841008\n"
        ".inst 0xe3c00020\n.inst 0xe5840000\n.inst 0xe3a02000\n.inst 0xe3a01002\n"
        ".inst 0xe2840d11\n.inst 0xeb00c2fa\n.inst 0xe2840b01\n.inst 0xe8bd4010\n"
        ".inst 0xe3a02000\n.inst 0xe3a01002\n.inst 0xe2800f56\n.inst 0xea00c2f4\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00291430, 84)
extern "C" __attribute__((naked)) void func_00291430() {
    asm volatile(
        ".arm\n"
        ".inst 0xed9f0a27\n.inst 0xe3500000\n.inst 0x0a000004\n.inst 0xe3500001\n"
        ".inst 0x0a000008\n.inst 0xe3500002\n.inst 0x112fff1e\n.inst 0xea00000c\n"
        ".inst 0xee001a10\n.inst 0xee002a90\n.inst 0xeeb81a40\n.inst 0xeef80a60\n"
        ".inst 0xee810a20\n.inst 0xe12fff1e\n.inst 0xee001a10\n.inst 0xee002a90\n"
        ".inst 0xeeb80a40\n.inst 0xeef80a60\n.inst 0xee801a20\n.inst 0xeeb10a41\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x002c41e8, 84)
extern "C" __attribute__((naked)) void engine_func_002c41e8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe5d00004\n.inst 0xe24dd010\n"
        ".inst 0xe3500000\n.inst 0x1a00000c\n.inst 0xe5942000\n.inst 0xe3e00000\n"
        ".inst 0xe1a01000\n.inst 0xe88d0007\n.inst 0xe3a03000\n.inst 0xe3a02001\n"
        ".inst 0xe28d1008\n.inst 0xe28d000c\n.inst 0xeb000035\n.inst 0xe1b01fa0\n"
        ".inst 0x1b00048e\n.inst 0xe3a00001\n.inst 0xe5c40004\n.inst 0xe28dd010\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002f274c, 84)
extern "C" __attribute__((naked)) void script_vm_func_002f274c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe1d000b0\n.inst 0xe1a06001\n"
        ".inst 0xebff0fe7\n.inst 0xe1a04000\n.inst 0xe1d600b0\n.inst 0xebff0fe4\n"
        ".inst 0xe3540000\n.inst 0x03a00000\n.inst 0x13500000\n.inst 0x0a000007\n"
        ".inst 0xe5900150\n.inst 0xe5941150\n.inst 0xe0500001\n.inst 0x1a000003\n"
        ".inst 0xe1a01006\n.inst 0xe1a00005\n.inst 0xe8bd4070\n.inst 0xeaffa8d6\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x0021910c, 88)
extern "C" __attribute__((naked)) void camp_func_0021910c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe5900004\n.inst 0xe1a06001\n"
        ".inst 0xe3500000\n.inst 0xb3a04000\n.inst 0xba000001\n.inst 0xeb023e2d\n"
        ".inst 0xe1d044b6\n.inst 0xe5960004\n.inst 0xe3500000\n.inst 0xb3a00000\n"
        ".inst 0xba000001\n.inst 0xeb023e27\n.inst 0xe1d004b6\n.inst 0xe0540000\n"
        ".inst 0x1a000003\n.inst 0xe1a01006\n.inst 0xe1a00005\n.inst 0xe8bd4070\n"
        ".inst 0xea00f98e\n.inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00227eac, 88)
extern "C" __attribute__((naked)) void ui_func_00227eac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xeb01af77\n.inst 0xe1a01004\n"
        ".inst 0xeb016b34\n.inst 0xe1a04000\n.inst 0xe5900000\n.inst 0xe3100a02\n"
        ".inst 0x0a000003\n.inst 0xeb01af70\n.inst 0xe3a02001\n.inst 0xe1a01004\n"
        ".inst 0xeb043f14\n.inst 0xe5940000\n.inst 0xe3100901\n.inst 0x0a000004\n"
        ".inst 0xeb01af69\n.inst 0xe1a01004\n.inst 0xe8bd4010\n.inst 0xe3a02002\n"
        ".inst 0xea043f0c\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0022a53c, 88)
extern "C" __attribute__((naked)) void battle_func_0022a53c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d41f0\n.inst 0xe1a05002\n.inst 0xe1a07000\n.inst 0xe1a06003\n"
        ".inst 0xed2d8b02\n.inst 0xe59d4024\n.inst 0xed9d8a08\n.inst 0xeb00aaa4\n"
        ".inst 0xe3500000\n.inst 0x0a000009\n.inst 0xe3a01003\n.inst 0xe5805208\n"
        ".inst 0xe5c01004\n.inst 0xe5806210\n.inst 0xed808a85\n.inst 0xe5c04005\n"
        ".inst 0xe1a00007\n.inst 0xecbd8b02\n.inst 0xe8bd41f0\n.inst 0xea00bdfe\n"
        ".inst 0xecbd8b02\n.inst 0xe8bd81f0\n"
    );
}

// DECOMP_FUNC(0x0027eda0, 88)
extern "C" __attribute__((naked)) void camp_func_0027eda0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe5900004\n.inst 0xeb01019a\n"
        ".inst 0xe3500000\n.inst 0x0a00000e\n.inst 0xe594041c\n.inst 0xe2845b01\n"
        ".inst 0xe285501c\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xeb00a35f\n"
        ".inst 0xe3a00000\n.inst 0xe5850000\n.inst 0xe5940000\n.inst 0xe3a01000\n"
        ".inst 0xe3c00030\n.inst 0xe5840000\n.inst 0xe5940004\n.inst 0xe8bd4070\n"
        ".inst 0xea0115f0\n.inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002a7d80, 88)
extern "C" __attribute__((naked)) void engine_func_002a7d80() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5d0200c\n.inst 0xe3520000\n.inst 0x0a000003\n.inst 0xe5902004\n"
        ".inst 0xe5923000\n.inst 0xe1530001\n.inst 0x8a000001\n.inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n.inst 0xe5903008\n.inst 0xe3530000\n.inst 0x17930101\n"
        ".inst 0x112fff1e\n.inst 0xe0811081\n.inst 0xe92d4010\n.inst 0xe0821101\n"
        ".inst 0xe5900000\n.inst 0xe5914008\n.inst 0xebfaa7e4\n.inst 0xe2800008\n"
        ".inst 0xe0800004\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002d4f88, 88)
extern "C" __attribute__((naked)) void engine_func_002d4f88() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d41f0\n.inst 0xebffaecd\n.inst 0xe59f6040\n.inst 0xe1a05000\n"
        ".inst 0xe5964000\n.inst 0xe3540000\n.inst 0x0a000008\n.inst 0xe5940004\n"
        ".inst 0xe3a07000\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xebffbce9\n"
        ".inst 0xe5847004\n.inst 0xe5960000\n.inst 0xebffbce6\n.inst 0xe5867000\n"
        ".inst 0xe5950008\n.inst 0xe8bd41f0\n.inst 0xe3a01000\n.inst 0xeaffbd77\n"
        ".inst 0x00435d30\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x002f26f4, 88)
extern "C" __attribute__((naked)) void camp_func_002f26f4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe5900004\n.inst 0xe1a06001\n"
        ".inst 0xe3500000\n.inst 0xb3a04000\n.inst 0xba000001\n.inst 0xebfed8b3\n"
        ".inst 0xe1d044b6\n.inst 0xe5960004\n.inst 0xe3500000\n.inst 0xb3a00000\n"
        ".inst 0xba000001\n.inst 0xebfed8ad\n.inst 0xe1d004b6\n.inst 0xe0500004\n"
        ".inst 0x1a000003\n.inst 0xe1a01006\n.inst 0xe1a00005\n.inst 0xe8bd4070\n"
        ".inst 0xeafd5c81\n.inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x0022ad74, 92)
extern "C" __attribute__((naked)) void func_0022ad74() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a03001\n.inst 0xe5901278\n.inst 0xe3510000\n.inst 0x0a000002\n"
        ".inst 0xe3a01001\n.inst 0xe1a00003\n.inst 0xea016503\n.inst 0xe590227c\n"
        ".inst 0xe3520000\n.inst 0x05902280\n.inst 0x03520000\n.inst 0x0a000002\n"
        ".inst 0xe1a01003\n.inst 0xe1a00002\n.inst 0xea007664\n.inst 0xe5901284\n"
        ".inst 0xe3510000\n.inst 0x0a000003\n.inst 0xe1d00cbe\n.inst 0xe3a02008\n"
        ".inst 0xe1a01003\n.inst 0xea02dc36\n.inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0022e638, 92)
extern "C" __attribute__((naked)) void shop_func_0022e638() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe5d00000\n.inst 0xe1a05002\n"
        ".inst 0xe1a06001\n.inst 0xe3500000\n.inst 0x1a000004\n.inst 0xe2840010\n"
        ".inst 0xeb01aa68\n.inst 0xe1a01005\n.inst 0xe2840010\n.inst 0xeb01bc95\n"
        ".inst 0xe5d40000\n.inst 0xe3500001\n.inst 0x1a000006\n.inst 0xe1a01006\n"
        ".inst 0xe2840010\n.inst 0xebffefe2\n.inst 0xe1a01005\n.inst 0xe2840010\n"
        ".inst 0xe8bd4070\n.inst 0xea01abb1\n.inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00250620, 92)
extern "C" __attribute__((naked)) void battle_func_00250620() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n.inst 0xeb017771\n.inst 0xe5901028\n.inst 0xe3a00000\n"
        ".inst 0xe1a01b81\n.inst 0xe1a01e21\n.inst 0xe3510008\n.inst 0x379ff101\n"
        ".inst 0xe8bd8010\n.inst 0x00250664\n.inst 0x00250640\n.inst 0x00250664\n"
        ".inst 0x00250640\n.inst 0x00250674\n.inst 0x00250640\n.inst 0x0025066c\n"
        ".inst 0x00250664\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe3a00002\n"
        ".inst 0xe8bd8010\n.inst 0xe3a00003\n.inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002b4e44, 92)
extern "C" __attribute__((naked)) void func_002b4e44() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe5d00016\n.inst 0xe3a06000\n"
        ".inst 0xe3500000\n.inst 0x0a00000c\n.inst 0xe5950008\n.inst 0xe3a04000\n"
        ".inst 0xe3500000\n.inst 0xda000007\n.inst 0xe7950104\n.inst 0xe3500000\n"
        ".inst 0x13a01001\n.inst 0x1bfa955d\n.inst 0xe5950008\n.inst 0xe2844001\n"
        ".inst 0xe1500004\n.inst 0xcafffff7\n.inst 0xe5c56016\n.inst 0xe5c56018\n"
        ".inst 0xe5c56017\n.inst 0xe5c56015\n.inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002c43f4, 92)
extern "C" __attribute__((naked)) void func_002c43f4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4030\n.inst 0xe1a05000\n.inst 0xe5900058\n.inst 0xe3500000\n"
        ".inst 0x0a000006\n.inst 0xe1d513b6\n.inst 0xe590405c\n.inst 0xe1c013b6\n"
        ".inst 0xebfffff6\n.inst 0xe1b00004\n.inst 0xe320f000\n.inst 0x1afffff8\n"
        ".inst 0xe5d50098\n.inst 0xe3500004\n.inst 0x379ff100\n.inst 0xe8bd8030\n"
        ".inst 0x002c4430\n.inst 0x002c4444\n.inst 0x002c4444\n.inst 0x002c4444\n"
        ".inst 0xe3a00004\n.inst 0xe5c50098\n.inst 0xe8bd8030\n"
    );
}

// DECOMP_FUNC(0x0021abe4, 96)
extern "C" __attribute__((naked)) void engine_func_0021abe4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe5900030\n.inst 0xe5906024\n"
        ".inst 0xe1a00006\n.inst 0xeb00d444\n.inst 0xe1a05000\n.inst 0xe5940030\n"
        ".inst 0xe284200c\n.inst 0xe1d010b0\n.inst 0xe1a00005\n.inst 0xeb00d3a8\n"
        ".inst 0xe5941030\n.inst 0xe5950030\n.inst 0xe1d140b0\n.inst 0xe3500000\n"
        ".inst 0x1b013a5a\n.inst 0xe6ff0074\n.inst 0xe5951000\n.inst 0xe1a02006\n"
        ".inst 0xeb0139f2\n.inst 0xe5850030\n.inst 0xe1a00005\n.inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002736fc, 96)
extern "C" __attribute__((naked)) void script_vm_func_002736fc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe590000c\n.inst 0xe3a05000\n"
        ".inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb014311\n.inst 0xe584500c\n"
        ".inst 0xe5940010\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb01430c\n"
        ".inst 0xe5845010\n.inst 0xe5940014\n.inst 0xe3500000\n.inst 0x0a000001\n"
        ".inst 0xeb00cf86\n.inst 0xe5845014\n.inst 0xe5d40008\n.inst 0xe3500000\n"
        ".inst 0x0a000001\n.inst 0xe8bd4070\n.inst 0xea0078c0\n.inst 0xe8bd8070\n"
    );
}
