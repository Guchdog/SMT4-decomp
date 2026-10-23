#include "types.h"

// Batch 35 A: byte-exact ARM/Thumb encodings with complete decode, explicit terminal returns, and bounded tails.

// DECOMP_FUNC(0x002b4d6c, 12)
extern "C" __attribute__((naked)) void func_002b4d6c() {
    asm volatile(
        ".thumb\n"
        ".hword 0xb510\n"
        ".hword 0xf64b\n"
        ".hword 0xfc35\n"
        ".hword 0xf011\n"
        ".hword 0xef46\n"
        ".hword 0xbd10\n"
    );
}

// DECOMP_FUNC(0x002b9424, 20)
extern "C" __attribute__((naked)) void engine_func_002b9424() {
    asm volatile(
        ".thumb\n"
        ".hword 0xbd70\n"
        ".hword 0x2800\n"
        ".hword 0xd004\n"
        ".hword 0x6800\n"
        ".hword 0x2800\n"
        ".hword 0xd001\n"
        ".hword 0x2000\n"
        ".hword 0x4770\n"
        ".hword 0x2001\n"
        ".hword 0x4770\n"
    );
}

// DECOMP_FUNC(0x00252520, 24)
extern "C" __attribute__((naked)) void engine_func_00252520() {
    asm volatile(
        ".thumb\n"
        ".hword 0x060b\n"
        ".hword 0x2200\n"
        ".hword 0x0e1b\n"
        ".hword 0x7801\n"
        ".hword 0x1c40\n"
        ".hword 0x4299\n"
        ".hword 0xd100\n"
        ".hword 0x1e42\n"
        ".hword 0x2900\n"
        ".hword 0xd1f8\n"
        ".hword 0x0010\n"
        ".hword 0x4770\n"
    );
}

// DECOMP_FUNC(0x002b67e0, 24)
extern "C" __attribute__((naked)) void engine_func_002b67e0() {
    asm volatile(
        ".thumb\n"
        ".hword 0x1e42\n"
        ".hword 0x1c52\n"
        ".hword 0x7813\n"
        ".hword 0x2b00\n"
        ".hword 0xd1fb\n"
        ".hword 0x780b\n"
        ".hword 0x1c49\n"
        ".hword 0x7013\n"
        ".hword 0x1c52\n"
        ".hword 0x2b00\n"
        ".hword 0xd1f9\n"
        ".hword 0x4770\n"
    );
}

// DECOMP_FUNC(0x002adb14, 32)
extern "C" __attribute__((naked)) void engine_func_002adb14() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f4010\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0b003cc7\n"
        ".inst 0xe5940000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00471a68 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002a23d8, 36)
extern "C" __attribute__((naked)) void func_002a23d8() {
    asm volatile(
        ".thumb\n"
        ".hword 0xb510\n"
        ".hword 0x1e43\n"
        ".hword 0x1c5b\n"
        ".hword 0x781c\n"
        ".hword 0x2c00\n"
        ".hword 0xd1fb\n"
        ".hword 0xe005\n"
        ".hword 0x780c\n"
        ".hword 0x1c49\n"
        ".hword 0x701c\n"
        ".hword 0x1c5b\n"
        ".hword 0x2c00\n"
        ".hword 0xd003\n"
        ".hword 0x1e52\n"
        ".hword 0xd2f7\n"
        ".hword 0x2100\n"
        ".hword 0x7019\n"
        ".hword 0xbd10\n"
    );
}

// DECOMP_FUNC(0x0023a308, 40)
extern "C" __attribute__((naked)) void func_0023a308() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000\n"
        ".inst 0x059f0018\n"
        ".inst 0xe92d4010\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5901000\n"
        ".inst 0xe5911030\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8010\n"
        ".word 0xc8804465 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0028cba8, 40)
extern "C" __attribute__((naked)) void engine_func_0028cba8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a02004\n"
        ".inst 0xe28f1014\n"
        ".inst 0xe92d4010\n"
        ".inst 0xfa00d3a3\n"
        ".inst 0xe3500000\n"
        ".inst 0x03a00001\n"
        ".inst 0x13a00000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x58455453 @ bounded tail data\n"
        ".word 0x00000000\n"
    );
}

// DECOMP_FUNC(0x0021a5ac, 48)
extern "C" __attribute__((naked)) void func_0021a5ac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900038\n"
        ".inst 0xe59f1018\n"
        ".inst 0xe0800080\n"
        ".inst 0xe7911180\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840034\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00472718 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0021ad14, 48)
extern "C" __attribute__((naked)) void func_0021ad14() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900038\n"
        ".inst 0xe59f1018\n"
        ".inst 0xe0600180\n"
        ".inst 0xe7911100\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840034\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00472840 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002adb54, 48)
extern "C" __attribute__((naked)) void func_002adb54() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xee1d4f70\n"
        ".inst 0xe59f101c\n"
        ".inst 0xe2844080\n"
        ".inst 0xe884000e\n"
        ".inst 0xe5900000\n"
        ".inst 0xef000032\n"
        ".inst 0xe2001102\n"
        ".inst 0xe3510000\n"
        ".inst 0xa5940004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x080e0080 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002c7a14, 48)
extern "C" __attribute__((naked)) void func_002c7a14() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900038\n"
        ".inst 0xe59f1018\n"
        ".inst 0xe0600180\n"
        ".inst 0xe7911100\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840034\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00472608 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002df410, 48)
extern "C" __attribute__((naked)) void func_002df410() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe590002c\n"
        ".inst 0xe59f1018\n"
        ".inst 0xe0800080\n"
        ".inst 0xe7911180\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840028\n"
        ".inst 0xe8bd8010\n"
        ".word 0x004727a8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002390a8, 52)
extern "C" __attribute__((naked)) void func_002390a8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe52de004\n"
        ".inst 0xe24dd00c\n"
        ".inst 0xe3a02014\n"
        ".inst 0xe3a01002\n"
        ".inst 0xe88d0006\n"
        ".inst 0xe5901000\n"
        ".inst 0xe3a02060\n"
        ".inst 0xe591c030\n"
        ".inst 0xe2801f67\n"
        ".inst 0xe12fff3c\n"
        ".inst 0xe28dd00c\n"
        ".inst 0xe49df004\n"
        ".word 0xc8810bea @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002aa234, 52)
extern "C" __attribute__((naked)) void func_002aa234() {
    asm volatile(
        ".arm\n"
        ".inst 0xe52de004\n"
        ".inst 0xe24dd044\n"
        ".inst 0xe59f2020\n"
        ".inst 0xe1cd12b4\n"
        ".inst 0xe3a0303c\n"
        ".inst 0xe58d2000\n"
        ".inst 0xe5b0243c\n"
        ".inst 0xe5901004\n"
        ".inst 0xe28d0004\n"
        ".inst 0xfa00299f\n"
        ".inst 0xe28dd044\n"
        ".inst 0xe49df004\n"
        ".word 0x00151a7c @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00207c0c, 56)
extern "C" __attribute__((naked)) void func_00207c0c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900038\n"
        ".inst 0xe59f1020\n"
        ".inst 0xe0600180\n"
        ".inst 0xe0810100\n"
        ".inst 0xe5901010\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe5940034\n"
        ".inst 0xe2800001\n"
        ".inst 0xe5840034\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00472840 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0021a40c, 56)
extern "C" __attribute__((naked)) void func_0021a40c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900038\n"
        ".inst 0xe59f1020\n"
        ".inst 0xe0600180\n"
        ".inst 0xe0810100\n"
        ".inst 0xe5901010\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe5940034\n"
        ".inst 0xe2800001\n"
        ".inst 0xe5840034\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00472608 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00270514, 56)
extern "C" __attribute__((naked)) void script_vm_func_00270514() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a0403f\n"
        ".inst 0xe59f5024\n"
        ".inst 0xe0640184\n"
        ".inst 0xe5951000\n"
        ".inst 0xe0810180\n"
        ".inst 0xe590003c\n"
        ".inst 0xe3500000\n"
        ".inst 0x1bfb896f\n"
        ".inst 0xe2544001\n"
        ".inst 0xe320f000\n"
        ".inst 0x5afffff6\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00447e58 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0027b4ec, 56)
extern "C" __attribute__((naked)) void script_vm_func_0027b4ec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a04000\n"
        ".inst 0xe59f5024\n"
        ".inst 0xe0641204\n"
        ".inst 0xe5950000\n"
        ".inst 0xe0800101\n"
        ".inst 0xe5f01024\n"
        ".inst 0xe3510000\n"
        ".inst 0x1b015e4f\n"
        ".inst 0xe2844001\n"
        ".inst 0xe3540010\n"
        ".inst 0xbafffff6\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00447a60 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00207b98, 60)
extern "C" __attribute__((naked)) void func_00207b98() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900038\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe0800080\n"
        ".inst 0xe0810180\n"
        ".inst 0xe590100c\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe12fff31\n"
        ".inst 0xeb01883d\n"
        ".inst 0xe5941034\n"
        ".inst 0xe0800001\n"
        ".inst 0xe5840034\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00472718 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0023a2b0, 60)
extern "C" __attribute__((naked)) void nn_sdk_func_0023a2b0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f002c\n"
        ".inst 0xe92d4008\n"
        ".inst 0xe59f2028\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe5d00000\n"
        ".inst 0xe5cd0000\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xebfbfe03\n"
        ".inst 0xe1a0100f\n"
        ".inst 0xe1b02fa0\n"
        ".inst 0x1b02068c\n"
        ".inst 0xe5dd0000\n"
        ".inst 0xe8bd8008\n"
        ".word 0x0040b59c @ bounded tail data\n"
        ".word 0x000a0002\n"
    );
}

// DECOMP_FUNC(0x002d1804, 60)
extern "C" __attribute__((naked)) void func_002d1804() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe590002c\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe0800080\n"
        ".inst 0xe0810180\n"
        ".inst 0xe590100c\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe12fff31\n"
        ".inst 0xebfe6122\n"
        ".inst 0xe5941028\n"
        ".inst 0xe0800001\n"
        ".inst 0xe5840028\n"
        ".inst 0xe8bd8010\n"
        ".word 0x004727a8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00210600, 64)
extern "C" __attribute__((naked)) void engine_func_00210600() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f2030\n"
        ".inst 0xe0820100\n"
        ".inst 0xe2800a01\n"
        ".inst 0xe5904210\n"
        ".inst 0xe3540000\n"
        ".inst 0x0a000006\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x1b02b577\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5c4100c\n"
        ".inst 0xe5840008\n"
        ".inst 0xe8bd8010\n"
        ".word 0x004e1f68 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00294a98, 64)
extern "C" __attribute__((naked)) void ui_func_00294a98() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1030\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe3a03003\n"
        ".inst 0xe4801010\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe3a02050\n"
        ".inst 0xfa00c528\n"
        ".inst 0xe2400010\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe2803008\n"
        ".inst 0xe3a02001\n"
        ".inst 0xe5801004\n"
        ".inst 0xe8830006\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00420338 @ bounded tail data\n"
        ".word 0x00335358\n"
    );
}

// DECOMP_FUNC(0x00235f4c, 68)
extern "C" __attribute__((naked)) void func_00235f4c() {
    asm volatile(
        ".arm\n"
        ".inst 0xeef40a41\n"
        ".inst 0xeef1fa10\n"
        ".inst 0x1a000003\n"
        ".inst 0xee710a82\n"
        ".inst 0xed9f0a0a\n"
        ".inst 0xee200a80\n"
        ".inst 0xe12fff1e\n"
        ".inst 0xee602a82\n"
        ".inst 0xee312ac2\n"
        ".inst 0xee700ac1\n"
        ".inst 0xee412a61\n"
        ".inst 0xee220a00\n"
        ".inst 0xee801a20\n"
        ".inst 0xee820aa0\n"
        ".inst 0xee310a00\n"
        ".inst 0xe12fff1e\n"
        ".word 0x3f000000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002563d4, 68)
extern "C" __attribute__((naked)) void script_vm_func_002563d4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb0182a0\n"
        ".inst 0xe2804c06\n"
        ".inst 0xe1d410b8\n"
        ".inst 0xe3110001\n"
        ".inst 0x1a000008\n"
        ".inst 0xe1d014b6\n"
        ".inst 0xe2412b01\n"
        ".inst 0xe25220b1\n"
        ".inst 0x059f1014\n"
        ".inst 0x0b01b9cb\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe1c400ba\n"
        ".inst 0xe1c400bc\n"
        ".inst 0xe1c400be\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00000604 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002a05fc, 68)
extern "C" __attribute__((naked)) void camp_func_002a05fc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f4034\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000009\n"
        ".inst 0xe5d00430\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000002\n"
        ".inst 0xeb000259\n"
        ".inst 0xe3500000\n"
        ".inst 0x0bffdabf\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x13e01000\n"
        ".inst 0x15801478\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043dd68 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0026e97c, 72)
extern "C" __attribute__((naked)) void ui_func_0026e97c() {
    asm volatile(
        ".arm\n"
        ".inst 0xed9f2a0f\n"
        ".inst 0xeeb41a42\n"
        ".inst 0xeef1fa10\n"
        ".inst 0x0a000005\n"
        ".inst 0xeef41ac2\n"
        ".inst 0xeef1fa10\n"
        ".inst 0x9a000003\n"
        ".inst 0xeef41ac1\n"
        ".inst 0xeef1fa10\n"
        ".inst 0xba000001\n"
        ".inst 0xeeb00a60\n"
        ".inst 0xe12fff1e\n"
        ".inst 0xee700ac0\n"
        ".inst 0xee601aa1\n"
        ".inst 0xeec10a81\n"
        ".inst 0xee300a80\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002f9e94, 72)
extern "C" __attribute__((naked)) void func_002f9e94() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1038\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe590003c\n"
        ".inst 0xe5912000\n"
        ".inst 0xe5901008\n"
        ".inst 0xe5812050\n"
        ".inst 0xe5904004\n"
        ".inst 0xe59f1020\n"
        ".inst 0xe5940038\n"
        ".inst 0xe0800080\n"
        ".inst 0xe7911180\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840034\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00472560 @ bounded tail data\n"
        ".word 0x00472718\n"
    );
}

// DECOMP_FUNC(0x00273640, 76)
extern "C" __attribute__((naked)) void script_vm_func_00273640() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0040\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a04000\n"
        ".inst 0xe5905000\n"
        ".inst 0xe3a00065\n"
        ".inst 0xe0000094\n"
        ".inst 0xe0850100\n"
        ".inst 0xe5f011d0\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5901004\n"
        ".inst 0xe3510003\n"
        ".inst 0x05900024\n"
        ".inst 0x0bfe5521\n"
        ".inst 0xe2844001\n"
        ".inst 0xe3540080\n"
        ".inst 0xbafffff2\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00447a78 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002b52c8, 80)
extern "C" __attribute__((naked)) void func_002b52c8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5900000\n"
        ".inst 0xe59f103c\n"
        ".inst 0xe3a04000\n"
        ".inst 0xe5902000\n"
        ".inst 0xe3520102\n"
        ".inst 0x0a000002\n"
        ".inst 0xe3520101\n"
        ".inst 0x1a000007\n"
        ".inst 0xea000003\n"
        ".inst 0xe5911000\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe1844000\n"
        ".inst 0xea000002\n"
        ".inst 0xe5911004\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe1844000\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x004734c0 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002b2cec, 84)
extern "C" __attribute__((naked)) void ui_func_002b2cec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe590408c\n"
        ".inst 0xe3540000\n"
        ".inst 0x159f6038\n"
        ".inst 0x0a00000a\n"
        ".inst 0xe5940090\n"
        ".inst 0xe1d010b4\n"
        ".inst 0xe0811201\n"
        ".inst 0xe0861101\n"
        ".inst 0xe591101c\n"
        ".inst 0xe3510000\n"
        ".inst 0x15900008\n"
        ".inst 0x112fff31\n"
        ".inst 0xe59440ac\n"
        ".inst 0xe3540000\n"
        ".inst 0x1afffff4\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5850084\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00464110 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00233354, 88)
extern "C" __attribute__((naked)) void func_00233354() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f004c\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5900000\n"
        ".inst 0xe2804a01\n"
        ".inst 0xe2844fab\n"
        ".inst 0xe5940000\n"
        ".inst 0xe0841100\n"
        ".inst 0xe2400001\n"
        ".inst 0xe5911008\n"
        ".inst 0xe5840000\n"
        ".inst 0xe0840100\n"
        ".inst 0xe5d42018\n"
        ".inst 0xe5900008\n"
        ".inst 0xe3520000\n"
        ".inst 0x01510000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe594101c\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5c40018\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0044ea00 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0023c7e8, 88)
extern "C" __attribute__((naked)) void camp_func_0023c7e8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe24dd010\n"
        ".inst 0xe3a01002\n"
        ".inst 0xe3a00011\n"
        ".inst 0xeb0211b0\n"
        ".inst 0xe1a05000\n"
        ".inst 0xeb0211a4\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb02118d\n"
        ".inst 0xe59f1020\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe3a0300c\n"
        ".inst 0xe58d1000\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe28d0004\n"
        ".inst 0xe1cd40b4\n"
        ".inst 0xfa01e029\n"
        ".inst 0xe28dd010\n"
        ".inst 0xe8bd8070\n"
        ".word 0x001b1710 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00248fa4, 88)
extern "C" __attribute__((naked)) void script_vm_func_00248fa4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f104c\n"
        ".inst 0xe5913000\n"
        ".inst 0xe3530000\n"
        ".inst 0x13a01000\n"
        ".inst 0x11a0c001\n"
        ".inst 0x012fff1e\n"
        ".inst 0xe52d4004\n"
        ".inst 0xe3a02065\n"
        ".inst 0xe0020291\n"
        ".inst 0xe0832102\n"
        ".inst 0xe5f241d0\n"
        ".inst 0xe3540000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe5924018\n"
        ".inst 0xe1540000\n"
        ".inst 0x0582c004\n"
        ".inst 0xe2811001\n"
        ".inst 0xe3510080\n"
        ".inst 0xbafffff3\n"
        ".inst 0xe49d4004\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00447a78 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00257744, 88)
extern "C" __attribute__((naked)) void camp_func_00257744() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe24dd078\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a0000c\n"
        ".inst 0xeb01a5d9\n"
        ".inst 0xe1a05000\n"
        ".inst 0xeb01a5cd\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb01a5b6\n"
        ".inst 0xe59f1020\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe3a03074\n"
        ".inst 0xe58d1000\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe28d0004\n"
        ".inst 0xe1cd42b4\n"
        ".inst 0xfa017452\n"
        ".inst 0xe28dd078\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00206bc8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0026ad50, 88)
extern "C" __attribute__((naked)) void camp_func_0026ad50() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe24dd078\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a0000c\n"
        ".inst 0xeb015856\n"
        ".inst 0xe1a05000\n"
        ".inst 0xeb01584a\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb015833\n"
        ".inst 0xe59f1020\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe3a03074\n"
        ".inst 0xe58d1000\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe28d0004\n"
        ".inst 0xe1cd42b4\n"
        ".inst 0xfa0126cf\n"
        ".inst 0xe28dd078\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00206bc8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0029ec14, 88)
extern "C" __attribute__((naked)) void camp_func_0029ec14() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe24dd008\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe3a00006\n"
        ".inst 0xeb0088a5\n"
        ".inst 0xe1a05000\n"
        ".inst 0xeb008899\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb008882\n"
        ".inst 0xe59f1020\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe3a03004\n"
        ".inst 0xe58d1000\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe28d0004\n"
        ".inst 0xe1cd40b4\n"
        ".inst 0xfa00571e\n"
        ".inst 0xe28dd008\n"
        ".inst 0xe8bd8070\n"
        ".word 0x002dca30 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002bacec, 88)
extern "C" __attribute__((naked)) void camp_func_002bacec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900318\n"
        ".inst 0xe3a05000\n"
        ".inst 0xe5845310\n"
        ".inst 0xe5845314\n"
        ".inst 0xe3500000\n"
        ".inst 0xe5845350\n"
        ".inst 0x0a000002\n"
        ".inst 0xe59f1024\n"
        ".inst 0xfaffe814\n"
        ".inst 0xe5845318\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebffe74a\n"
        ".inst 0xe59f0014\n"
        ".inst 0xe5900000\n"
        ".inst 0xe5901754\n"
        ".inst 0xe3c11801\n"
        ".inst 0xe5801754\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0013188c @ bounded tail data\n"
        ".word 0x00432fc8\n"
    );
}

// DECOMP_FUNC(0x002cc19c, 88)
extern "C" __attribute__((naked)) void func_002cc19c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f104c\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5911000\n"
        ".inst 0xe2814a01\n"
        ".inst 0xe2844fab\n"
        ".inst 0xe5941000\n"
        ".inst 0xe2812001\n"
        ".inst 0xe0843101\n"
        ".inst 0xe5931008\n"
        ".inst 0xe0843102\n"
        ".inst 0xe5842000\n"
        ".inst 0xe5830008\n"
        ".inst 0xe5d42018\n"
        ".inst 0xe3520000\n"
        ".inst 0x01510000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe594101c\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5c40018\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0044ea00 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002235e8, 92)
extern "C" __attribute__((naked)) void script_vm_func_002235e8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d41f0\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe59f7044\n"
        ".inst 0xe5c70250\n"
        ".inst 0xe3a04001\n"
        ".inst 0xe0875406\n"
        ".inst 0xe0850104\n"
        ".inst 0xe5900284\n"
        ".inst 0xe3500000\n"
        ".inst 0x1bfcbd38\n"
        ".inst 0xe2844001\n"
        ".inst 0xe3540040\n"
        ".inst 0xbafffff8\n"
        ".inst 0xe0870106\n"
        ".inst 0xe590026c\n"
        ".inst 0xe3500000\n"
        ".inst 0x1bfcbd31\n"
        ".inst 0xe2866001\n"
        ".inst 0xe3560006\n"
        ".inst 0xbaffffef\n"
        ".inst 0xe8bd81f0\n"
        ".word 0x004bce8c @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0022e290, 92)
extern "C" __attribute__((naked)) void unite_func_0022e290() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe2800a0a\n"
        ".inst 0xe24dd088\n"
        ".inst 0xe1d020d4\n"
        ".inst 0xe1520001\n"
        ".inst 0x11d460f0\n"
        ".inst 0x13560001\n"
        ".inst 0xda00000a\n"
        ".inst 0xe5c01004\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe3a02088\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xeb023b22\n"
        ".inst 0xe79d3105\n"
        ".inst 0xe3a02020\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe2840004\n"
        ".inst 0xfb022709\n"
        ".inst 0xe28dd088\n"
        ".inst 0xe8bd8070\n"
        ".word 0x004022d4 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002ae818, 92)
extern "C" __attribute__((naked)) void camp_func_002ae818() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe24dd048\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a0000b\n"
        ".inst 0xeb0049a4\n"
        ".inst 0xe1b05000\n"
        ".inst 0x0a00000b\n"
        ".inst 0xeb004997\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb004980\n"
        ".inst 0xe59f1020\n"
        ".inst 0xe1cd42b8\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe58d1000\n"
        ".inst 0xe3a03040\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe28d0008\n"
        ".inst 0xfa00181c\n"
        ".inst 0xe28dd048\n"
        ".inst 0xe8bd8070\n"
        ".word 0x001455dc @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002aece4, 92)
extern "C" __attribute__((naked)) void func_002aece4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d41f0\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe5911000\n"
        ".inst 0xe3a07000\n"
        ".inst 0xe1a04007\n"
        ".inst 0xe1a05007\n"
        ".inst 0xe5911048\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe3500001\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe59f0024\n"
        ".inst 0x01c040d0\n"
        ".inst 0x0a000004\n"
        ".inst 0xe3510002\n"
        ".inst 0x01c040d8\n"
        ".inst 0x0a000001\n"
        ".inst 0xe3510003\n"
        ".inst 0x01c041d0\n"
        ".inst 0xe5867000\n"
        ".inst 0xe1c640f4\n"
        ".inst 0xe8bd81f0\n"
        ".word 0x004091d4 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002af060, 92)
extern "C" __attribute__((naked)) void func_002af060() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1050\n"
        ".inst 0xe5911004\n"
        ".inst 0xe2812c06\n"
        ".inst 0xe1d234fe\n"
        ".inst 0xe1530000\n"
        ".inst 0x1a00000b\n"
        ".inst 0xe5d10008\n"
        ".inst 0xe3500001\n"
        ".inst 0x13500002\n"
        ".inst 0x1a000007\n"
        ".inst 0xe1d205f0\n"
        ".inst 0xe3500001\n"
        ".inst 0xba000006\n"
        ".inst 0xe350000f\n"
        ".inst 0xba000002\n"
        ".inst 0xe240000f\n"
        ".inst 0xe3100003\n"
        ".inst 0x0a000001\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043dcb0 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002a4528, 96)
extern "C" __attribute__((naked)) void engine_func_002a4528() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe590100c\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0048\n"
        ".inst 0xe3510000\n"
        ".inst 0xe5840000\n"
        ".inst 0x1b006240\n"
        ".inst 0xe5940010\n"
        ".inst 0xe3500000\n"
        ".inst 0x1b00623d\n"
        ".inst 0xe5b41010\n"
        ".inst 0xe3510000\n"
        ".inst 0x13a00000\n"
        ".inst 0x0a000006\n"
        ".inst 0xe1a02001\n"
        ".inst 0xe5911004\n"
        ".inst 0xe5820004\n"
        ".inst 0xe5820000\n"
        ".inst 0xe3510000\n"
        ".inst 0x1afffff9\n"
        ".inst 0xe5840000\n"
        ".inst 0xe2440010\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00420bc0 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002a49fc, 96)
extern "C" __attribute__((naked)) void engine_func_002a49fc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d41f0\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe280502c\n"
        ".inst 0xe1a06001\n"
        ".inst 0xe1a07002\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb007c23\n"
        ".inst 0xe0860086\n"
        ".inst 0xe7941100\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000008\n"
        ".inst 0xe0840100\n"
        ".inst 0xe3570000\n"
        ".inst 0xe5901004\n"
        ".inst 0xe2414004\n"
        ".inst 0x1b0059cc\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb007bf7\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd81f0\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb007bf3\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd81f0\n"
    );
}

// DECOMP_FUNC(0x002a4df0, 96)
extern "C" __attribute__((naked)) void ui_func_002a4df0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d43f0\n"
        ".inst 0xe24dd00c\n"
        ".inst 0xe1a08000\n"
        ".inst 0xe28d0028\n"
        ".inst 0xe1b04001\n"
        ".inst 0xe8900220\n"
        ".inst 0xe1a06002\n"
        ".inst 0xe1a07003\n"
        ".inst 0x13550000\n"
        ".inst 0x059f0030\n"
        ".inst 0x0a000009\n"
        ".inst 0xe3a00001\n"
        ".inst 0xeb00236f\n"
        ".inst 0xe88d0220\n"
        ".inst 0xe5940000\n"
        ".inst 0xe1a02006\n"
        ".inst 0xe1a03007\n"
        ".inst 0xe1a01008\n"
        ".inst 0xe590c000\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe12fff3c\n"
        ".inst 0xe28dd00c\n"
        ".inst 0xe8bd83f0\n"
        ".word 0xe0e046bc @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002adb84, 96)
extern "C" __attribute__((naked)) void func_002adb84() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d41f0\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe59d101c\n"
        ".inst 0xe59dc018\n"
        ".inst 0xee1d4f70\n"
        ".inst 0xe59f7040\n"
        ".inst 0xe3a06000\n"
        ".inst 0xe5a47080\n"
        ".inst 0xe584100c\n"
        ".inst 0xe1861701\n"
        ".inst 0xe2846010\n"
        ".inst 0xe3811002\n"
        ".inst 0xe8861002\n"
        ".inst 0xe1c420f4\n"
        ".inst 0xe5900000\n"
        ".inst 0xef000032\n"
        ".inst 0xe2101102\n"
        ".inst 0x4a000003\n"
        ".inst 0xe2841008\n"
        ".inst 0xe1c100d0\n"
        ".inst 0xe1c500f0\n"
        ".inst 0xe5940004\n"
        ".inst 0xe8bd81f0\n"
        ".word 0x080c00c2 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002b5bcc, 96)
extern "C" __attribute__((naked)) void engine_func_002b5bcc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d407f\n"
        ".inst 0xe59d5024\n"
        ".inst 0xee1d4f70\n"
        ".inst 0xe59f3048\n"
        ".inst 0xe5a43080\n"
        ".inst 0xe5842004\n"
        ".inst 0xe1dd30bc\n"
        ".inst 0xe1c430b8\n"
        ".inst 0xe1dd32b0\n"
        ".inst 0xe1c430bc\n"
        ".inst 0xe3a0300a\n"
        ".inst 0xe1832202\n"
        ".inst 0xe5841014\n"
        ".inst 0xe5842010\n"
        ".inst 0xe5900000\n"
        ".inst 0xef000032\n"
        ".inst 0xe2101102\n"
        ".inst 0x4a000002\n"
        ".inst 0xe5d40008\n"
        ".inst 0xe5c50000\n"
        ".inst 0xe5940004\n"
        ".inst 0xe28dd010\n"
        ".inst 0xe8bd8070\n"
        ".word 0x001100c2 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002bf984, 96)
extern "C" __attribute__((naked)) void func_002bf984() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5910000\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe3a02004\n"
        ".inst 0xe3a01f52\n"
        ".inst 0xe5903008\n"
        ".inst 0xe1a00005\n"
        ".inst 0xe12fff33\n"
        ".inst 0xe3500000\n"
        ".inst 0x03a04000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe1a03004\n"
        ".inst 0xe1a01005\n"
        ".inst 0xebffd6b4\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a01005\n"
        ".inst 0xe5940000\n"
        ".inst 0xe5902024\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe12fff32\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002c3290, 96)
extern "C" __attribute__((naked)) void engine_func_002c3290() {
    asm volatile(
        ".arm\n"
        ".inst 0xe2803001\n"
        ".inst 0xea000003\n"
        ".inst 0xe4d01001\n"
        ".inst 0xe3510000\n"
        ".inst 0x00400003\n"
        ".inst 0x012fff1e\n"
        ".inst 0xe3100003\n"
        ".inst 0x059f2038\n"
        ".inst 0x1afffff8\n"
        ".inst 0xe4901004\n"
        ".inst 0xe6621ff1\n"
        ".inst 0xe3510000\n"
        ".inst 0x0afffffb\n"
        ".inst 0xe1b02c01\n"
        ".inst 0xe0400003\n"
        ".inst 0x12400003\n"
        ".inst 0x112fff1e\n"
        ".inst 0xe1b02801\n"
        ".inst 0x12400002\n"
        ".inst 0x112fff1e\n"
        ".inst 0xe1b01401\n"
        ".inst 0x12400001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x01010101 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002f30c0, 96)
extern "C" __attribute__((naked)) void engine_func_002f30c0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe590408c\n"
        ".inst 0xe3540000\n"
        ".inst 0x159f5048\n"
        ".inst 0x0a00000f\n"
        ".inst 0xe5940090\n"
        ".inst 0xe1d010b4\n"
        ".inst 0xe0811201\n"
        ".inst 0xe0851101\n"
        ".inst 0xe5911038\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000005\n"
        ".inst 0xe5900008\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8070\n"
        ".inst 0xe59440ac\n"
        ".inst 0xe3540000\n"
        ".inst 0x1affffef\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00464110 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002f9ee4, 96)
extern "C" __attribute__((naked)) void engine_func_002f9ee4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe59100d0\n"
        ".inst 0xe1a04001\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000006\n"
        ".inst 0xe59500d0\n"
        ".inst 0xe3500000\n"
        ".inst 0x1bfd7521\n"
        ".inst 0xe59400d0\n"
        ".inst 0xebfd74c6\n"
        ".inst 0xe58500d0\n"
        ".inst 0xe8bd8070\n"
        ".inst 0xe59400cc\n"
        ".inst 0xe3500000\n"
        ".inst 0x0afffffb\n"
        ".inst 0xe59500cc\n"
        ".inst 0xe3500000\n"
        ".inst 0x1bfd7502\n"
        ".inst 0xe59400cc\n"
        ".inst 0xe320f000\n"
        ".inst 0xebfd74b7\n"
        ".inst 0xe58500cc\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002fe2b8, 96)
extern "C" __attribute__((naked)) void engine_func_002fe2b8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe5904014\n"
        ".inst 0xe590c010\n"
        ".inst 0xe1c021d8\n"
        ".inst 0xe05cc002\n"
        ".inst 0xe0c44003\n"
        ".inst 0xe05cc001\n"
        ".inst 0xe2d4c000\n"
        ".inst 0xb3a00000\n"
        ".inst 0xba00000c\n"
        ".inst 0xe0922001\n"
        ".inst 0xe3a0c000\n"
        ".inst 0xe0a3300c\n"
        ".inst 0xe1c021f8\n"
        ".inst 0xe1c020d0\n"
        ".inst 0xe0924001\n"
        ".inst 0xe0a3500c\n"
        ".inst 0xe1c040f0\n"
        ".inst 0xe590004c\n"
        ".inst 0xef000018\n"
        ".inst 0xe1b01fa0\n"
        ".inst 0x1bff1c55\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00235938, 100)
extern "C" __attribute__((naked)) void func_00235938() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xeb00005f\n"
        ".inst 0xe59540c4\n"
        ".inst 0xe3540000\n"
        ".inst 0x0a000006\n"
        ".inst 0xe5d400c6\n"
        ".inst 0xe3500000\n"
        ".inst 0x11a00004\n"
        ".inst 0x1b000029\n"
        ".inst 0xe5944138\n"
        ".inst 0xe3540000\n"
        ".inst 0x1afffff8\n"
        ".inst 0xe59540c4\n"
        ".inst 0xe3540000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb000116\n"
        ".inst 0xe5944138\n"
        ".inst 0xe3540000\n"
        ".inst 0x1afffffa\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe58500c4\n"
        ".inst 0xe5c50005\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002b4fe4, 100)
extern "C" __attribute__((naked)) void engine_func_002b4fe4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4038\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5d0001c\n"
        ".inst 0xe1a05003\n"
        ".inst 0xe1a03002\n"
        ".inst 0xe3500000\n"
        ".inst 0xe1a02001\n"
        ".inst 0x0a000006\n"
        ".inst 0xe1a01005\n"
        ".inst 0xe2840004\n"
        ".inst 0xeb0019fc\n"
        ".inst 0xe5840018\n"
        ".inst 0xe1a00fc0\n"
        ".inst 0xe2800001\n"
        ".inst 0xe8bd8038\n"
        ".inst 0xe2840004\n"
        ".inst 0xe1a0100d\n"
        ".inst 0xeb0019f5\n"
        ".inst 0xe1a0100f\n"
        ".inst 0xe1b02fa0\n"
        ".inst 0x1b001b35\n"
        ".inst 0xe59d0000\n"
        ".inst 0xe5850000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8038\n"
    );
}

// DECOMP_FUNC(0x002215e8, 104)
extern "C" __attribute__((naked)) void battle_func_002215e8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfeed5a\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a000012\n"
        ".inst 0xe59f404c\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5940004\n"
        ".inst 0xeb028beb\n"
        ".inst 0xe5940008\n"
        ".inst 0xe3a01000\n"
        ".inst 0xeb028be8\n"
        ".inst 0xe594000c\n"
        ".inst 0xe3a01000\n"
        ".inst 0xeb028be5\n"
        ".inst 0xe5940010\n"
        ".inst 0xe3a01000\n"
        ".inst 0xeb028be2\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3a01002\n"
        ".inst 0xeb028bdf\n"
        ".inst 0xe5940014\n"
        ".inst 0xe3500000\n"
        ".inst 0x112fff30\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043dea8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002263d4, 104)
extern "C" __attribute__((naked)) void func_002263d4() {
    asm volatile(
        ".arm\n"
        ".inst 0xecf11a01\n"
        ".inst 0xed9f2a15\n"
        ".inst 0xecd10a02\n"
        ".inst 0xee210aa1\n"
        ".inst 0xee000aa0\n"
        ".inst 0xee010a01\n"
        ".inst 0xeeb40a42\n"
        ".inst 0xeef1fa10\n"
        ".inst 0x1a000004\n"
        ".inst 0xe892000a\n"
        ".inst 0xe5922008\n"
        ".inst 0xe5802008\n"
        ".inst 0xe880000a\n"
        ".inst 0xe12fff1e\n"
        ".inst 0xeef12ac0\n"
        ".inst 0xed9f2a08\n"
        ".inst 0xee820a22\n"
        ".inst 0xee611a80\n"
        ".inst 0xee600a80\n"
        ".inst 0xee210a00\n"
        ".inst 0xedc01a00\n"
        ".inst 0xedc00a01\n"
        ".inst 0xed800a02\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000 @ bounded tail data\n"
        ".word 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x002420c8, 104)
extern "C" __attribute__((naked)) void camp_func_002420c8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe24dd048\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a0000b\n"
        ".inst 0xeb01fb78\n"
        ".inst 0xe1b05000\n"
        ".inst 0x0a00000d\n"
        ".inst 0xeb01fb6b\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb01fb54\n"
        ".inst 0xe59f102c\n"
        ".inst 0xe1cd42b8\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe58d1000\n"
        ".inst 0xe3a03040\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe28d0008\n"
        ".inst 0xfa01c9f0\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a000000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe28dd048\n"
        ".inst 0xe8bd8070\n"
        ".word 0x001455dc @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0024c74c, 104)
extern "C" __attribute__((naked)) void battle_func_0024c74c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb018726\n"
        ".inst 0xe5d01023\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe351000b\n"
        ".inst 0x379ff101\n"
        ".inst 0xe8bd8010\n"
        ".inst 0x0024c764\n"
        ".inst 0x0024c764\n"
        ".inst 0x0024c764\n"
        ".inst 0x0024c794\n"
        ".inst 0x0024c79c\n"
        ".inst 0x0024c7ac\n"
        ".inst 0x0024c7ac\n"
        ".inst 0x0024c7a4\n"
        ".inst 0x0024c7a4\n"
        ".inst 0x0024c7a4\n"
        ".inst 0x0024c7ac\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".inst 0xe3a00002\n"
        ".inst 0xe8bd8010\n"
        ".inst 0xe3a00003\n"
        ".inst 0xe8bd8010\n"
        ".inst 0xe3a00004\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0026a904, 104)
extern "C" __attribute__((naked)) void camp_func_0026a904() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe24dd008\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe3a00006\n"
        ".inst 0xeb015969\n"
        ".inst 0xe1a05000\n"
        ".inst 0xeb01595d\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb015946\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe59f0028\n"
        ".inst 0xe3a03004\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe58d0000\n"
        ".inst 0xe28d0004\n"
        ".inst 0xe1cd40b4\n"
        ".inst 0xfa0127e2\n"
        ".inst 0xe5d00002\n"
        ".inst 0xe59f100c\n"
        ".inst 0xe7d10000\n"
        ".inst 0xe28dd008\n"
        ".inst 0xe8bd8070\n"
        ".word 0x002dca30 @ bounded tail data\n"
        ".word 0x0040442e\n"
    );
}

// DECOMP_FUNC(0x00280cc8, 104)
extern "C" __attribute__((naked)) void func_00280cc8() {
    asm volatile(
        ".arm\n"
        ".inst 0xee704a42\n"
        ".inst 0xee314a43\n"
        ".inst 0xeddf5a14\n"
        ".inst 0xee245aa4\n"
        ".inst 0xee045a04\n"
        ".inst 0xeef12ac5\n"
        ".inst 0xeef42a65\n"
        ".inst 0xeef1fa10\n"
        ".inst 0xee711aa3\n"
        ".inst 0x0ddf2a0e\n"
        ".inst 0xeef41ae2\n"
        ".inst 0xeef1fa10\n"
        ".inst 0xbc800a03\n"
        ".inst 0xb3a00000\n"
        ".inst 0xba000007\n"
        ".inst 0xee841aa2\n"
        ".inst 0xee012a21\n"
        ".inst 0xee840a22\n"
        ".inst 0xed802a00\n"
        ".inst 0xedc00a01\n"
        ".inst 0xee003a21\n"
        ".inst 0xed803a02\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000 @ bounded tail data\n"
        ".word 0x3c23d70a\n"
    );
}

// DECOMP_FUNC(0x00289a58, 104)
extern "C" __attribute__((naked)) void script_vm_func_00289a58() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5912000\n"
        ".inst 0xe24dd018\n"
        ".inst 0xe3a04000\n"
        ".inst 0xe58d2008\n"
        ".inst 0xe5912004\n"
        ".inst 0xe3a03010\n"
        ".inst 0xe58d200c\n"
        ".inst 0xe5911008\n"
        ".inst 0xe1cd01b4\n"
        ".inst 0xe59f2030\n"
        ".inst 0xe59f0030\n"
        ".inst 0xe58d1010\n"
        ".inst 0xe58d2000\n"
        ".inst 0xe2801018\n"
        ".inst 0xe5902000\n"
        ".inst 0xe28d0008\n"
        ".inst 0xfa00ab8e\n"
        ".inst 0xe3500000\n"
        ".inst 0x11d000be\n"
        ".inst 0xe28dd018\n"
        ".inst 0x12804e82\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x001e15cc @ bounded tail data\n"
        ".word 0x0043e3b0\n"
    );
}

// DECOMP_FUNC(0x002bb54c, 104)
extern "C" __attribute__((naked)) void func_002bb54c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe59f6054\n"
        ".inst 0xe1d600d1\n"
        ".inst 0xe1d610d2\n"
        ".inst 0xe1d00001\n"
        ".inst 0x159f5048\n"
        ".inst 0x13a04000\n"
        ".inst 0x0a00000e\n"
        ".inst 0xe7950104\n"
        ".inst 0xe3500000\n"
        ".inst 0x112fff30\n"
        ".inst 0xe2844001\n"
        ".inst 0xe3540008\n"
        ".inst 0xbafffff9\n"
        ".inst 0xe5d60001\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5960008\n"
        ".inst 0xebf9f9c0\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5c60001\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe5c60002\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0044e458 @ bounded tail data\n"
        ".word 0x004c6464\n"
    );
}

// DECOMP_FUNC(0x002bf86c, 104)
extern "C" __attribute__((naked)) void engine_func_002bf86c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1803001\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe3130003\n"
        ".inst 0x059fc050\n"
        ".inst 0xe52de004\n"
        ".inst 0x1a000009\n"
        ".inst 0xe4913004\n"
        ".inst 0xe66ceff3\n"
        ".inst 0xe35e0000\n"
        ".inst 0x04823004\n"
        ".inst 0x0afffffa\n"
        ".inst 0xe21310ff\n"
        ".inst 0x11a03423\n"
        ".inst 0xe4c21001\n"
        ".inst 0x1afffffb\n"
        ".inst 0xe49df004\n"
        ".inst 0xe4d13001\n"
        ".inst 0xe3530000\n"
        ".inst 0xe4c23001\n"
        ".inst 0x049df004\n"
        ".inst 0xe4d13001\n"
        ".inst 0xe3530000\n"
        ".inst 0xe4c23001\n"
        ".inst 0x1afffff7\n"
        ".inst 0xe49df004\n"
        ".word 0x01010101 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0022a028, 108)
extern "C" __attribute__((naked)) void camp_func_0022a028() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d40f0\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe24dd00c\n"
        ".inst 0xe3a01003\n"
        ".inst 0xe3a00005\n"
        ".inst 0xeb025b9f\n"
        ".inst 0xe1a06000\n"
        ".inst 0xeb025b93\n"
        ".inst 0xe1a07000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xeb025b7c\n"
        ".inst 0xe5cd4004\n"
        ".inst 0xe59d3004\n"
        ".inst 0xe59f1028\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe3c338ff\n"
        ".inst 0xe3c33cff\n"
        ".inst 0xe1833405\n"
        ".inst 0xe88d000a\n"
        ".inst 0xe3a03004\n"
        ".inst 0xe1a01007\n"
        ".inst 0xe28d0004\n"
        ".inst 0xfa022a14\n"
        ".inst 0xe28dd00c\n"
        ".inst 0xe8bd80f0\n"
        ".word 0x002d0630 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0024205c, 108)
extern "C" __attribute__((naked)) void camp_func_0024205c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe24dd048\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a0000b\n"
        ".inst 0xeb01fb93\n"
        ".inst 0xe1b05000\n"
        ".inst 0x0a00000e\n"
        ".inst 0xeb01fb86\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb01fb6f\n"
        ".inst 0xe59f1030\n"
        ".inst 0xe1cd42b8\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe58d1000\n"
        ".inst 0xe3a03040\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe28d0008\n"
        ".inst 0xfa01ca0b\n"
        ".inst 0xe3500000\n"
        ".inst 0x11d002b6\n"
        ".inst 0x1a000000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe28dd048\n"
        ".inst 0xe8bd8070\n"
        ".word 0x001455dc @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002a882c, 108)
extern "C" __attribute__((naked)) void ui_func_002a882c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe24dd010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xeb003500\n"
        ".inst 0xe3500000\n"
        ".inst 0x059f004c\n"
        ".inst 0x11a05000\n"
        ".inst 0x11a0600d\n"
        ".inst 0x0a00000e\n"
        ".inst 0xe0d400b2\n"
        ".inst 0xe350003a\n"
        ".inst 0x1afffffc\n"
        ".inst 0xe3a01004\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe88d0012\n"
        ".inst 0xfa0034ef\n"
        ".inst 0xe2800001\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe1a00080\n"
        ".inst 0xe58d0008\n"
        ".inst 0xe5950000\n"
        ".inst 0xe5902008\n"
        ".inst 0xe1a00005\n"
        ".inst 0xe12fff32\n"
        ".inst 0xe28dd010\n"
        ".inst 0xe8bd8070\n"
        ".word 0xc8804465 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002c4b84, 108)
extern "C" __attribute__((naked)) void engine_func_002c4b84() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d41f0\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a06001\n"
        ".inst 0xe59f8054\n"
        ".inst 0xe1a07002\n"
        ".inst 0xed2d8b02\n"
        ".inst 0xe24dd008\n"
        ".inst 0xe5980004\n"
        ".inst 0xe1a05003\n"
        ".inst 0xed9d8a0a\n"
        ".inst 0xebfffbbd\n"
        ".inst 0xed8d8a00\n"
        ".inst 0xe1a03005\n"
        ".inst 0xe1a02007\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb000249\n"
        ".inst 0xe1b04000\n"
        ".inst 0x11a01005\n"
        ".inst 0x1bfffbdc\n"
        ".inst 0xe5980004\n"
        ".inst 0xebfffb91\n"
        ".inst 0xe28dd008\n"
        ".inst 0xe1a00004\n"
        ".inst 0xecbd8b02\n"
        ".inst 0xe8bd81f0\n"
        ".word 0x00465120 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002ef824, 108)
extern "C" __attribute__((naked)) void func_002ef824() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe59f4058\n"
        ".inst 0xe5d00001\n"
        ".inst 0xe3500001\n"
        ".inst 0xe5c41001\n"
        ".inst 0x1a000011\n"
        ".inst 0xebf8524f\n"
        ".inst 0xe3500000\n"
        ".inst 0x1bf8511f\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe1a01002\n"
        ".inst 0xe3a00006\n"
        ".inst 0xebfbeeec\n"
        ".inst 0xe2100102\n"
        ".inst 0xe3a05000\n"
        ".inst 0x4a000006\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe1a01002\n"
        ".inst 0xe3a00006\n"
        ".inst 0xebfc827f\n"
        ".inst 0xe3500001\n"
        ".inst 0x13500002\n"
        ".inst 0x0a000000\n"
        ".inst 0xe5c45001\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0043e310 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0021ddac, 112)
extern "C" __attribute__((naked)) void script_vm_func_0021ddac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f3060\n"
        ".inst 0xe92d0030\n"
        ".inst 0xe5934004\n"
        ".inst 0xe3a03000\n"
        ".inst 0xe3540000\n"
        ".inst 0xc59fc050\n"
        ".inst 0xda00000b\n"
        ".inst 0xe0635203\n"
        ".inst 0xe0855283\n"
        ".inst 0xe08c5185\n"
        ".inst 0xe595512c\n"
        ".inst 0xe1550000\n"
        ".inst 0x1a000007\n"
        ".inst 0xe0630203\n"
        ".inst 0xe0800283\n"
        ".inst 0xe08c0180\n"
        ".inst 0xe2800c01\n"
        ".inst 0xe1c016b6\n"
        ".inst 0xe1c026b8\n"
        ".inst 0xe8bd0030\n"
        ".inst 0xe12fff1e\n"
        ".inst 0xe2833001\n"
        ".inst 0xe1540003\n"
        ".inst 0xcaffffee\n"
        ".inst 0xe8bd0030\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00447a28 @ bounded tail data\n"
        ".word 0x004a1264\n"
    );
}

// DECOMP_FUNC(0x0024b804, 112)
extern "C" __attribute__((naked)) void func_0024b804() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5902020\n"
        ".inst 0xe1c22cd0\n"
        ".inst 0xe0020392\n"
        ".inst 0xe3520000\n"
        ".inst 0x012fff1e\n"
        ".inst 0xe52d4004\n"
        ".inst 0xe5903018\n"
        ".inst 0xe59fc048\n"
        ".inst 0xe5904004\n"
        ".inst 0xe0410003\n"
        ".inst 0xec910a03\n"
        ".inst 0xe080c09c\n"
        ".inst 0xe3e0c000\n"
        ".inst 0xe1a002a0\n"
        ".inst 0xe0204290\n"
        ".inst 0xe0800100\n"
        ".inst 0xe0830180\n"
        ".inst 0xe281300c\n"
        ".inst 0xecd31a05\n"
        ".inst 0xec800a08\n"
        ".inst 0xe5912024\n"
        ".inst 0xe5911020\n"
        ".inst 0xe5a0c010\n"
        ".inst 0xe5801010\n"
        ".inst 0xe5802014\n"
        ".inst 0xe49d4004\n"
        ".inst 0xe12fff1e\n"
        ".word 0xcccccccd @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002ebd80, 112)
extern "C" __attribute__((naked)) void engine_func_002ebd80() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f005c\n"
        ".inst 0xe1a06001\n"
        ".inst 0xe2805b01\n"
        ".inst 0xe2800a01\n"
        ".inst 0xe2800f61\n"
        ".inst 0xe2855fe1\n"
        ".inst 0xe5d00048\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a00000e\n"
        ".inst 0xe3540010\n"
        ".inst 0x2a00000c\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfdec14\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000008\n"
        ".inst 0xe0850104\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe590087c\n"
        ".inst 0xe3500000\n"
        ".inst 0x1bff478b\n"
        ".inst 0xe5952a40\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe1c21411\n"
        ".inst 0xe5851a40\n"
        ".inst 0xe8bd8070\n"
        ".word 0x004e1f68 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002f46e4, 112)
extern "C" __attribute__((naked)) void func_002f46e4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d0030\n"
        ".inst 0xe59f305c\n"
        ".inst 0xe59f505c\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe062c182\n"
        ".inst 0xe08cc202\n"
        ".inst 0xe793410c\n"
        ".inst 0xe3740001\n"
        ".inst 0x0a00000d\n"
        ".inst 0xe1540000\n"
        ".inst 0x1a000008\n"
        ".inst 0xe083c10c\n"
        ".inst 0xe59cc004\n"
        ".inst 0xe15c0001\n"
        ".inst 0x1a000004\n"
        ".inst 0xe0620182\n"
        ".inst 0xe0800202\n"
        ".inst 0xe8bd0030\n"
        ".inst 0xe0830100\n"
        ".inst 0xe12fff1e\n"
        ".inst 0xe2822001\n"
        ".inst 0xe1520005\n"
        ".inst 0xbaffffec\n"
        ".inst 0xe8bd0030\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00448e18 @ bounded tail data\n"
        ".word 0x000003e7\n"
    );
}

// DECOMP_FUNC(0x0021a36c, 116)
extern "C" __attribute__((naked)) void engine_func_0021a36c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d41f0\n"
        ".inst 0xe3e05000\n"
        ".inst 0xe590408c\n"
        ".inst 0xe3540000\n"
        ".inst 0x159f6058\n"
        ".inst 0x13e07000\n"
        ".inst 0x0a000012\n"
        ".inst 0xe5940090\n"
        ".inst 0xe1d010b4\n"
        ".inst 0xe0811201\n"
        ".inst 0xe0861101\n"
        ".inst 0xe5911040\n"
        ".inst 0xe3510000\n"
        ".inst 0x01a00007\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5900008\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe5941080\n"
        ".inst 0xe59440ac\n"
        ".inst 0xe0800001\n"
        ".inst 0xe1550000\n"
        ".inst 0xb1a05000\n"
        ".inst 0xe3540000\n"
        ".inst 0x1affffec\n"
        ".inst 0xe1a00005\n"
        ".inst 0xe8bd81f0\n"
        ".word 0x00464110 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00245b44, 116)
extern "C" __attribute__((naked)) void engine_func_00245b44() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe59f0058\n"
        ".inst 0xe24dd030\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfbae3c\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a00000f\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a00019\n"
        ".inst 0xeb01ecd3\n"
        ".inst 0xe1a05000\n"
        ".inst 0xeb01ecc7\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb01ecb0\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe3a0302c\n"
        ".inst 0xe58d1000\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe28d0004\n"
        ".inst 0xe1cd42b4\n"
        ".inst 0xfa01bb4c\n"
        ".inst 0xe28dd030\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00433158 @ bounded tail data\n"
        ".word 0x00124704\n"
    );
}

// DECOMP_FUNC(0x0027e094, 116)
extern "C" __attribute__((naked)) void script_vm_func_0027e094() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d41f0\n"
        ".inst 0xe3a04000\n"
        ".inst 0xe1a07000\n"
        ".inst 0xe1a08004\n"
        ".inst 0xe0875204\n"
        ".inst 0xe5950968\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5901000\n"
        ".inst 0xe5911004\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe5858968\n"
        ".inst 0xe5950960\n"
        ".inst 0xe2856e96\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe5901008\n"
        ".inst 0xe591100c\n"
        ".inst 0xe3510000\n"
        ".inst 0xabfb5284\n"
        ".inst 0xe5950960\n"
        ".inst 0xe320f000\n"
        ".inst 0xeb00a66b\n"
        ".inst 0xe5868000\n"
        ".inst 0xe2844001\n"
        ".inst 0xe354006d\n"
        ".inst 0xe585896c\n"
        ".inst 0x3affffe7\n"
        ".inst 0xe8bd81f0\n"
    );
}

// DECOMP_FUNC(0x002840b8, 116)
extern "C" __attribute__((naked)) void camp_func_002840b8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe59f0058\n"
        ".inst 0xe24dd040\n"
        ".inst 0xe5900000\n"
        ".inst 0xeb009853\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a00000f\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe3a00004\n"
        ".inst 0xeb00f376\n"
        ".inst 0xe1a05000\n"
        ".inst 0xeb00f36a\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb00f353\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe3a0303c\n"
        ".inst 0xe58d1000\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe28d0004\n"
        ".inst 0xe1cd42b4\n"
        ".inst 0xfa00c1ef\n"
        ".inst 0xe28dd040\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00433158 @ bounded tail data\n"
        ".word 0x001453fc\n"
    );
}

// DECOMP_FUNC(0x0029e5c8, 116)
extern "C" __attribute__((naked)) void engine_func_0029e5c8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1068\n"
        ".inst 0xe591c004\n"
        ".inst 0xe28c2b01\n"
        ".inst 0xe59c1754\n"
        ".inst 0xe2822fd5\n"
        ".inst 0xe3510014\n"
        ".inst 0xa12fff1e\n"
        ".inst 0xe28c3b01\n"
        ".inst 0xe2833fd6\n"
        ".inst 0xe52de004\n"
        ".inst 0xe24dd00c\n"
        ".inst 0xe7c10003\n"
        ".inst 0xe5920000\n"
        ".inst 0xe2801001\n"
        ".inst 0xe5821000\n"
        ".inst 0xe5dc074e\n"
        ".inst 0xe3500002\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe1a03000\n"
        ".inst 0xe58d0000\n"
        ".inst 0xe58d0004\n"
        ".inst 0xe28c0b01\n"
        ".inst 0x03a0200a\n"
        ".inst 0x13a02009\n"
        ".inst 0xe2800fe2\n"
        ".inst 0xeb00052d\n"
        ".inst 0xe28dd00c\n"
        ".inst 0xe49df004\n"
        ".word 0x0043dd20 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0029fa74, 116)
extern "C" __attribute__((naked)) void camp_func_0029fa74() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe59f0058\n"
        ".inst 0xe24dd020\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a00000f\n"
        ".inst 0xe3a01004\n"
        ".inst 0xe3a00005\n"
        ".inst 0xeb008507\n"
        ".inst 0xe1a05000\n"
        ".inst 0xeb0084fb\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb0084e4\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe3a0301c\n"
        ".inst 0xe58d1000\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe28d0004\n"
        ".inst 0xe1cd40b4\n"
        ".inst 0xfa005380\n"
        ".inst 0xe28dd020\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00433158 @ bounded tail data\n"
        ".word 0x001f64c4\n"
    );
}

// DECOMP_FUNC(0x002ae3f0, 116)
extern "C" __attribute__((naked)) void battle_func_002ae3f0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe59f0058\n"
        ".inst 0xe24dd070\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfa795a\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a00000f\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a00004\n"
        ".inst 0xeb004aa8\n"
        ".inst 0xe1a05000\n"
        ".inst 0xeb004a9c\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb004a85\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe1cd42b8\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe58d1000\n"
        ".inst 0xe3a03068\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe28d0008\n"
        ".inst 0xfa001921\n"
        ".inst 0xe28dd070\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00433158 @ bounded tail data\n"
        ".word 0x0014514c\n"
    );
}

// DECOMP_FUNC(0x002b492c, 116)
extern "C" __attribute__((naked)) void camp_func_002b492c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f2068\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe0813081\n"
        ".inst 0xe792c103\n"
        ".inst 0xe15c0000\n"
        ".inst 0x8a000006\n"
        ".inst 0xe082c103\n"
        ".inst 0xe59cc004\n"
        ".inst 0xe150000c\n"
        ".inst 0x8a000002\n"
        ".inst 0xe0810081\n"
        ".inst 0xe0820100\n"
        ".inst 0xe12fff1e\n"
        ".inst 0xe0823103\n"
        ".inst 0xe593c00c\n"
        ".inst 0xe15c0000\n"
        ".inst 0x95933010\n"
        ".inst 0x91500003\n"
        ".inst 0x8a000003\n"
        ".inst 0xe0810081\n"
        ".inst 0xe0820100\n"
        ".inst 0xe280000c\n"
        ".inst 0xe12fff1e\n"
        ".inst 0xe2811002\n"
        ".inst 0xe351000c\n"
        ".inst 0xbaffffe7\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00404378 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002bac34, 116)
extern "C" __attribute__((naked)) void engine_func_002bac34() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900000\n"
        ".inst 0xe24dd010\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000014\n"
        ".inst 0xe3e02000\n"
        ".inst 0xe58d0008\n"
        ".inst 0xe58d2000\n"
        ".inst 0xe58d2004\n"
        ".inst 0xe3a03000\n"
        ".inst 0xe3a02001\n"
        ".inst 0xe28d1008\n"
        ".inst 0xe28d000c\n"
        ".inst 0xeb0025a2\n"
        ".inst 0xe1b01fa0\n"
        ".inst 0x1b0029fb\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe5c40004\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb002557\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000002\n"
        ".inst 0xef000023\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840000\n"
        ".inst 0xe28dd010\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002bd13c, 116)
extern "C" __attribute__((naked)) void camp_func_002bd13c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe59f0058\n"
        ".inst 0xe24dd030\n"
        ".inst 0xe5900000\n"
        ".inst 0xebf9d0be\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a00000f\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a00019\n"
        ".inst 0xeb000f55\n"
        ".inst 0xe1a05000\n"
        ".inst 0xeb000f49\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb000f32\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe3a0302c\n"
        ".inst 0xe58d1000\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe28d0004\n"
        ".inst 0xe1cd42b4\n"
        ".inst 0xfaffddce\n"
        ".inst 0xe28dd030\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00433158 @ bounded tail data\n"
        ".word 0x00124704\n"
    );
}

// DECOMP_FUNC(0x002c1a48, 116)
extern "C" __attribute__((naked)) void engine_func_002c1a48() {
    asm volatile(
        ".thumb\n"
        ".hword 0x0003\n"
        ".hword 0x430b\n"
        ".hword 0xb510\n"
        ".hword 0x079b\n"
        ".hword 0xd11c\n"
        ".hword 0x2a04\n"
        ".hword 0xd31a\n"
        ".hword 0xc808\n"
        ".hword 0xc910\n"
        ".hword 0x1f12\n"
        ".hword 0x42a3\n"
        ".hword 0xd0f8\n"
        ".hword 0x0618\n"
        ".hword 0x0621\n"
        ".hword 0x0e00\n"
        ".hword 0x0e09\n"
        ".hword 0x1a40\n"
        ".hword 0xd10e\n"
        ".hword 0x0418\n"
        ".hword 0x0421\n"
        ".hword 0x0c00\n"
        ".hword 0x0c09\n"
        ".hword 0x1a40\n"
        ".hword 0xd108\n"
        ".hword 0x0218\n"
        ".hword 0x0221\n"
        ".hword 0x0a00\n"
        ".hword 0x0a09\n"
        ".hword 0x1a40\n"
        ".hword 0xd102\n"
        ".hword 0x0e18\n"
        ".hword 0x0e21\n"
        ".hword 0x1a40\n"
        ".hword 0xbd10\n"
        ".hword 0x2a00\n"
        ".hword 0xd003\n"
        ".hword 0x07d3\n"
        ".hword 0xd003\n"
        ".hword 0x1c52\n"
        ".hword 0xe007\n"
        ".hword 0x2000\n"
        ".hword 0xbd10\n"
        ".hword 0x7803\n"
        ".hword 0x780c\n"
        ".hword 0x1c40\n"
        ".hword 0x1c49\n"
        ".hword 0x1b1b\n"
        ".hword 0xd107\n"
        ".hword 0x7803\n"
        ".hword 0x780c\n"
        ".hword 0x1c40\n"
        ".hword 0x1c49\n"
        ".hword 0x1b1b\n"
        ".hword 0xd101\n"
        ".hword 0x1e92\n"
        ".hword 0xd1f1\n"
        ".hword 0x0018\n"
        ".hword 0xbd10\n"
    );
}

// DECOMP_FUNC(0x00201234, 120)
extern "C" __attribute__((naked)) void battle_func_00201234() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb025747\n"
        ".inst 0xe1a04000\n"
        ".inst 0xeb0220fd\n"
        ".inst 0xe3500000\n"
        ".inst 0xe1a00004\n"
        ".inst 0x0a000003\n"
        ".inst 0xeb02f870\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000010\n"
        ".inst 0xea00000d\n"
        ".inst 0xe320f000\n"
        ".inst 0xeb02f86b\n"
        ".inst 0xe3500000\n"
        ".inst 0xe320f000\n"
        ".inst 0x0a00000a\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb02fe11\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900018\n"
        ".inst 0xe3500000\n"
        ".inst 0x1bfd4619\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a00003\n"
        ".inst 0xe1c400f8\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8010\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002543f8, 120)
extern "C" __attribute__((naked)) void engine_func_002543f8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f3068\n"
        ".inst 0xe92d0030\n"
        ".inst 0xe5934004\n"
        ".inst 0xe3a03000\n"
        ".inst 0xe3540000\n"
        ".inst 0xc59fc058\n"
        ".inst 0xda00000d\n"
        ".inst 0xe0635203\n"
        ".inst 0xe0855283\n"
        ".inst 0xe08c5185\n"
        ".inst 0xe595512c\n"
        ".inst 0xe1550000\n"
        ".inst 0x1a000009\n"
        ".inst 0xe0630203\n"
        ".inst 0xe0800283\n"
        ".inst 0xe3a04000\n"
        ".inst 0xe08c0180\n"
        ".inst 0xe2803c01\n"
        ".inst 0xe1c316b0\n"
        ".inst 0xe1c326b2\n"
        ".inst 0xe5c04164\n"
        ".inst 0xe8bd0030\n"
        ".inst 0xe12fff1e\n"
        ".inst 0xe2833001\n"
        ".inst 0xe1540003\n"
        ".inst 0xcaffffec\n"
        ".inst 0xe8bd0030\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00447a28 @ bounded tail data\n"
        ".word 0x004a1264\n"
    );
}

// DECOMP_FUNC(0x0026959c, 120)
extern "C" __attribute__((naked)) void func_0026959c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900010\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a00000d\n"
        ".inst 0xe5942008\n"
        ".inst 0xe5940018\n"
        ".inst 0xe3520000\n"
        ".inst 0x0a000009\n"
        ".inst 0xe2400018\n"
        ".inst 0xe3120001\n"
        ".inst 0xe3e01000\n"
        ".inst 0x15a01028\n"
        ".inst 0xe1b020a2\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5801028\n"
        ".inst 0xe2522001\n"
        ".inst 0xe5a01050\n"
        ".inst 0x1afffffb\n"
        ".inst 0xe1d400b0\n"
        ".inst 0xe59f101c\n"
        ".inst 0xe0800100\n"
        ".inst 0xe7911100\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe5940010\n"
        ".inst 0xe2800001\n"
        ".inst 0xe5840010\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00473590 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00292c04, 120)
extern "C" __attribute__((naked)) void camp_func_00292c04() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3510000\n"
        ".inst 0xe24dd068\n"
        ".inst 0xe1a04000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a00016\n"
        ".inst 0xeb00b8a7\n"
        ".inst 0xe1a05000\n"
        ".inst 0xea000003\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe3a00016\n"
        ".inst 0xeb00b8a2\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe320f000\n"
        ".inst 0xeb00b895\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb00b87e\n"
        ".inst 0xe59f1020\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe3a03060\n"
        ".inst 0xe58d1000\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe28d0008\n"
        ".inst 0xe5cd4008\n"
        ".inst 0xfa00871a\n"
        ".inst 0xe28dd068\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0032c8fc @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002a803c, 120)
extern "C" __attribute__((naked)) void func_002a803c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe2801004\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe8910006\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f305c\n"
        ".inst 0xe0420001\n"
        ".inst 0xe1520001\n"
        ".inst 0xe0c02093\n"
        ".inst 0xe1a021c0\n"
        ".inst 0xe0422fc0\n"
        ".inst 0x82020001\n"
        ".inst 0x93a00000\n"
        ".inst 0xe2800001\n"
        ".inst 0xe2822001\n"
        ".inst 0xe1520000\n"
        ".inst 0xda000002\n"
        ".inst 0xe2800002\n"
        ".inst 0xe1520000\n"
        ".inst 0xcafffffc\n"
        ".inst 0xe5841008\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x13510000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe5902000\n"
        ".inst 0xe592200c\n"
        ".inst 0xe12fff32\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x2aaaaaab @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x002f11c4, 120)
extern "C" __attribute__((naked)) void engine_func_002f11c4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe9763\n"
        ".inst 0xe59f4060\n"
        ".inst 0xe3500000\n"
        ".inst 0xe5940000\n"
        ".inst 0x0a000009\n"
        ".inst 0xeb02f5cd\n"
        ".inst 0xe3500000\n"
        ".inst 0x15940000\n"
        ".inst 0x1b02f41a\n"
        ".inst 0xe5940000\n"
        ".inst 0xeb02f505\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".inst 0xe320f000\n"
        ".inst 0xeb02f4ff\n"
        ".inst 0xe3500000\n"
        ".inst 0x15940000\n"
        ".inst 0x1b02f4ac\n"
        ".inst 0xe5940000\n"
        ".inst 0xe320f000\n"
        ".inst 0xeb02f5bc\n"
        ".inst 0xe3500000\n"
        ".inst 0xe320f000\n"
        ".inst 0x1afffff2\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00439ca8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00208a84, 124)
extern "C" __attribute__((naked)) void engine_func_00208a84() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb02e823\n"
        ".inst 0xe5d01790\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe3a04000\n"
        ".inst 0xe5c04790\n"
        ".inst 0xeb01d455\n"
        ".inst 0xe3500006\n"
        ".inst 0x379ff100\n"
        ".inst 0xe8bd8010\n"
        ".inst 0x00208ac8\n"
        ".inst 0x00208ac8\n"
        ".inst 0x00208aac\n"
        ".inst 0x00208ac8\n"
        ".inst 0x00208aac\n"
        ".inst 0x00208ac8\n"
        ".inst 0xe320f000\n"
        ".inst 0xeb01fbe5\n"
        ".inst 0xe3500000\n"
        ".inst 0xe320f000\n"
        ".inst 0x1afffff3\n"
        ".inst 0xe1a00000\n"
        ".inst 0xe320f000\n"
        ".inst 0xe320f000\n"
        ".inst 0xeb02e80b\n"
        ".inst 0xe5c04003\n"
        ".inst 0xe320f000\n"
        ".inst 0xeb02e808\n"
        ".inst 0xe5c0401c\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0021e8f0, 124)
extern "C" __attribute__((naked)) void engine_func_0021e8f0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb01e198\n"
        ".inst 0xe1a04000\n"
        ".inst 0xeb01ab4e\n"
        ".inst 0xe3500000\n"
        ".inst 0xe3a00000\n"
        ".inst 0x0a000004\n"
        ".inst 0xeb0268f3\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a00000c\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
        ".inst 0xe320f000\n"
        ".inst 0xeb01e18c\n"
        ".inst 0xe3500000\n"
        ".inst 0x13500001\n"
        ".inst 0x1afffff8\n"
        ".inst 0xe1a01004\n"
        ".inst 0xe3a00000\n"
        ".inst 0xeb02074c\n"
        ".inst 0xe320f000\n"
        ".inst 0xe320f000\n"
        ".inst 0xea000004\n"
        ".inst 0xe320f000\n"
        ".inst 0xeb028d73\n"
        ".inst 0xe3500000\n"
        ".inst 0x13a00000\n"
        ".inst 0x1b01a40a\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00295208, 124)
extern "C" __attribute__((naked)) void ui_func_00295208() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5901040\n"
        ".inst 0xe59f2068\n"
        ".inst 0xe3510001\n"
        ".inst 0x05903004\n"
        ".inst 0x12411001\n"
        ".inst 0x03a01000\n"
        ".inst 0x15801040\n"
        ".inst 0x1a00000f\n"
        ".inst 0xe0824101\n"
        ".inst 0xe5940004\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a00000c\n"
        ".inst 0xe590c004\n"
        ".inst 0xe15c0003\n"
        ".inst 0x1a000009\n"
        ".inst 0xebfea378\n"
        ".inst 0xe5940004\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe5901000\n"
        ".inst 0xe5911004\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840004\n"
        ".inst 0xe8bd8010\n"
        ".inst 0xe2811001\n"
        ".inst 0xe3510010\n"
        ".inst 0xbaffffeb\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0047e508 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00295284, 124)
extern "C" __attribute__((naked)) void ui_func_00295284() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1c400d8\n"
        ".inst 0xeb009116\n"
        ".inst 0xe1a05000\n"
        ".inst 0xebfea48d\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000015\n"
        ".inst 0xe5d4003d\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a000011\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb02a83c\n"
        ".inst 0xe3500000\n"
        ".inst 0x11a00004\n"
        ".inst 0x1b02a866\n"
        ".inst 0xe5952008\n"
        ".inst 0xe594100c\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe5c4003d\n"
        ".inst 0xe5940010\n"
        ".inst 0xe1d000b4\n"
        ".inst 0xe3500000\n"
        ".inst 0xda000002\n"
        ".inst 0xe5940014\n"
        ".inst 0xe5a02018\n"
        ".inst 0xe5801004\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb02a5f8\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002ada98, 124)
extern "C" __attribute__((naked)) void ui_func_002ada98() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d41f0\n"
        ".inst 0xe24dd010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a07002\n"
        ".inst 0xe1a08003\n"
        ".inst 0xeb002063\n"
        ".inst 0xe3500000\n"
        ".inst 0x059f0054\n"
        ".inst 0x11a05000\n"
        ".inst 0x11a0600d\n"
        ".inst 0x0a000010\n"
        ".inst 0xe0d400b2\n"
        ".inst 0xe350003a\n"
        ".inst 0x1afffffc\n"
        ".inst 0xe3a01004\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe88d0012\n"
        ".inst 0xfa002052\n"
        ".inst 0xe2800001\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe1a00080\n"
        ".inst 0xe58d0008\n"
        ".inst 0xe5950000\n"
        ".inst 0xe1a02007\n"
        ".inst 0xe1a03008\n"
        ".inst 0xe590c018\n"
        ".inst 0xe1a00005\n"
        ".inst 0xe12fff3c\n"
        ".inst 0xe28dd010\n"
        ".inst 0xe8bd81f0\n"
        ".word 0xc8804465 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00211f0c, 128)
extern "C" __attribute__((naked)) void engine_func_00211f0c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d40f8\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a05002\n"
        ".inst 0xe1c401d0\n"
        ".inst 0xe1a06003\n"
        ".inst 0xe0500005\n"
        ".inst 0xe0d10006\n"
        ".inst 0xb3a00000\n"
        ".inst 0xba000015\n"
        ".inst 0xe2840040\n"
        ".inst 0xeb02c6db\n"
        ".inst 0xe1a00005\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe1c401f8\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe1c400f0\n"
        ".inst 0xe1c400f8\n"
        ".inst 0xe58d2000\n"
        ".inst 0xe5940038\n"
        ".inst 0xe1a02005\n"
        ".inst 0xe1a03006\n"
        ".inst 0xe5901000\n"
        ".inst 0xe591100c\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe2840040\n"
        ".inst 0xeb02c6ab\n"
        ".inst 0xe594004c\n"
        ".inst 0xef000018\n"
        ".inst 0xe1b01fa0\n"
        ".inst 0x1b02cd38\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd80f8\n"
    );
}

// DECOMP_FUNC(0x00249508, 128)
extern "C" __attribute__((naked)) void engine_func_00249508() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900050\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe1a06002\n"
        ".inst 0xe3500000\n"
        ".inst 0x1b00376d\n"
        ".inst 0xe356000a\n"
        ".inst 0x379ff106\n"
        ".inst 0xe8bd8070\n"
        ".inst 0x0024952c\n"
        ".inst 0x00249558\n"
        ".inst 0x0024956c\n"
        ".inst 0x0024952c\n"
        ".inst 0x00249558\n"
        ".inst 0x0024952c\n"
        ".inst 0x0024952c\n"
        ".inst 0x0024952c\n"
        ".inst 0x0024952c\n"
        ".inst 0x00249558\n"
        ".inst 0xe6ff0075\n"
        ".inst 0xe59f101c\n"
        ".inst 0xeb025328\n"
        ".inst 0xe5840050\n"
        ".inst 0xe8bd8070\n"
        ".inst 0xe6ff0075\n"
        ".inst 0xe59f100c\n"
        ".inst 0xeb025323\n"
        ".inst 0xe5840050\n"
        ".inst 0xe8bd8070\n"
        ".word 0x20080027 @ bounded tail data\n"
        ".word 0x200000a7\n"
    );
}

// DECOMP_FUNC(0x002b9438, 128)
extern "C" __attribute__((naked)) void engine_func_002b9438() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5d005b0\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a000005\n"
        ".inst 0xe3a02040\n"
        ".inst 0xe2841e53\n"
        ".inst 0xe1a00005\n"
        ".inst 0xfa002179\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000012\n"
        ".inst 0xe1a01005\n"
        ".inst 0xe2840e53\n"
        ".inst 0xeb001ae2\n"
        ".inst 0xe2841e53\n"
        ".inst 0xe2840e57\n"
        ".inst 0xebfff989\n"
        ".inst 0xe2842a01\n"
        ".inst 0xe2841a01\n"
        ".inst 0xe2843e53\n"
        ".inst 0xe2822f43\n"
        ".inst 0xe2811f53\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb000a43\n"
        ".inst 0xe2841a01\n"
        ".inst 0xe594052c\n"
        ".inst 0xe2811f63\n"
        ".inst 0xeb000a2a\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5c405b0\n"
        ".inst 0xe8bd8070\n"
    );
}
