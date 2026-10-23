#include "types.h"

// Batch 31 B: raw ARM/Thumb encodings with explicit bounded return/data tails.

// DECOMP_FUNC(0x003e4eb0, 12)
extern "C" __attribute__((naked)) void func_003e4eb0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0044e870 @ bounded tail data\n"
    );
}
// DECOMP_FUNC(0x003e5194, 12)
extern "C" __attribute__((naked)) void func_003e5194() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00472140 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e51a8, 12)
extern "C" __attribute__((naked)) void func_003e51a8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00472238 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e5224, 12)
extern "C" __attribute__((naked)) void func_003e5224() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004722a0 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e6024, 12)
extern "C" __attribute__((naked)) void func_003e6024() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00472030 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e6030, 12)
extern "C" __attribute__((naked)) void func_003e6030() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004732d8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e603c, 12)
extern "C" __attribute__((naked)) void func_003e603c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00472180 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e6048, 12)
extern "C" __attribute__((naked)) void func_003e6048() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0044e820 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e611c, 12)
extern "C" __attribute__((naked)) void func_003e611c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00472158 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e6128, 12)
extern "C" __attribute__((naked)) void func_003e6128() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004765b0 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e6134, 12)
extern "C" __attribute__((naked)) void func_003e6134() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0044e858 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003bcfc8, 16)
extern "C" __attribute__((naked)) void func_003bcfc8() {
    asm volatile(
        ".arm\n"
        ".inst 0xeddf0a01\n"
        ".inst 0xee200a20\n"
        ".inst 0xe12fff1e\n"
        ".word 0x3fa00000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003409d4, 24)
extern "C" __attribute__((naked)) void func_003409d4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a01000\n"
        ".inst 0xed9f0a02\n"
        ".inst 0xe5801004\n"
        ".inst 0xed800a02\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00348ac0, 24)
extern "C" __attribute__((naked)) void func_00348ac0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a01000\n"
        ".inst 0xed9f0a02\n"
        ".inst 0xe5801004\n"
        ".inst 0xed800a02\n"
        ".inst 0xe12fff1e\n"
        ".word 0x3f800000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0035a220, 24)
extern "C" __attribute__((naked)) void script_vm_func_0035a220() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500007\n"
        ".inst 0x359f1008\n"
        ".inst 0x37910100\n"
        ".inst 0x23a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00465768 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0035a270, 24)
extern "C" __attribute__((naked)) void script_vm_func_0035a270() {
    asm volatile(
        ".arm\n"
        ".inst 0xe350000c\n"
        ".inst 0x359f1008\n"
        ".inst 0x37910100\n"
        ".inst 0x23a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00465728 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00380420, 24)
extern "C" __attribute__((naked)) void func_00380420() {
    asm volatile(
        ".arm\n"
        ".inst 0xed9f0a03\n"
        ".inst 0xe3a01000\n"
        ".inst 0xed800a05\n"
        ".inst 0xe5801010\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003f59f0, 24)
extern "C" __attribute__((naked)) void func_003f59f0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f000c\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5801000\n"
        ".inst 0xe5801004\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0044e918 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003f5dc8, 24)
extern "C" __attribute__((naked)) void func_003f5dc8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f000c\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5801000\n"
        ".inst 0xe5801004\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0044e930 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003f61d8, 24)
extern "C" __attribute__((naked)) void func_003f61d8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f000c\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5801000\n"
        ".inst 0xe5801004\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0044e948 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003f6b2c, 24)
extern "C" __attribute__((naked)) void func_003f6b2c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f000c\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5801000\n"
        ".inst 0xe5801004\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0044e990 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00379b14, 28)
extern "C" __attribute__((naked)) void func_00379b14() {
    asm volatile(
        ".arm\n"
        ".inst 0xeddf0a04\n"
        ".inst 0xeeb40ae0\n"
        ".inst 0xeef1fa10\n"
        ".inst 0x3eb00a60\n"
        ".inst 0xed800a2c\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003f62d0, 32)
extern "C" __attribute__((naked)) void func_003f62d0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe59f000c\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5801000\n"
        ".inst 0xe5801004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0044e960 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0033c908, 36)
extern "C" __attribute__((naked)) void camp_func_0033c908() {
    asm volatile(
        ".arm\n"
        ".inst 0xed9f0a06\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5801390\n"
        ".inst 0xed800ae6\n"
        ".inst 0xed800ae7\n"
        ".inst 0xed800ae8\n"
        ".inst 0xed800ae5\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003954a4, 36)
extern "C" __attribute__((naked)) void func_003954a4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5901070\n"
        ".inst 0xed9f0a05\n"
        ".inst 0xe3c11001\n"
        ".inst 0xe5801070\n"
        ".inst 0xed800a1d\n"
        ".inst 0xed800a1e\n"
        ".inst 0xed800a1f\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003d6610, 36)
extern "C" __attribute__((naked)) void engine_func_003d6610() {
    asm volatile(
        ".arm\n"
        ".inst 0xed9f0a06\n"
        ".inst 0xed800a05\n"
        ".inst 0xed800a04\n"
        ".inst 0xed800a03\n"
        ".inst 0xed800a08\n"
        ".inst 0xed800a07\n"
        ".inst 0xed800a06\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00302770, 40)
extern "C" __attribute__((naked)) void func_00302770() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5912000\n"
        ".inst 0xed9f0a06\n"
        ".inst 0xe5802020\n"
        ".inst 0xe5912004\n"
        ".inst 0xe5802024\n"
        ".inst 0xe5911008\n"
        ".inst 0xe5801028\n"
        ".inst 0xed800a0b\n"
        ".inst 0xe12fff1e\n"
        ".word 0x3f800000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003f65e8, 40)
extern "C" __attribute__((naked)) void func_003f65e8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0018\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3e02000\n"
        ".inst 0xe5801000\n"
        ".inst 0xe5801004\n"
        ".inst 0xe59f0008\n"
        ".inst 0xe5802008\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0044e978 @ bounded tail data\n"
        ".word 0x004d4674 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00376fb4, 44)
extern "C" __attribute__((naked)) void func_00376fb4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5801018\n"
        ".inst 0xed9f0a06\n"
        ".inst 0xe580101c\n"
        ".inst 0xe5801020\n"
        ".inst 0xe3a02001\n"
        ".inst 0xed800a09\n"
        ".inst 0xe5c02028\n"
        ".inst 0xe5c01029\n"
        ".inst 0xe12fff1e\n"
        ".word 0x3f000000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0037f7e0, 44)
extern "C" __attribute__((naked)) void func_0037f7e0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3510010\n"
        ".inst 0xb0800081\n"
        ".inst 0xb28000cc\n"
        ".inst 0xba000004\n"
        ".inst 0xe3510020\n"
        ".inst 0xb59f000c\n"
        ".inst 0xb0800081\n"
        ".inst 0xb2400020\n"
        ".inst 0xa3a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004ea494 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003f5a3c, 44)
extern "C" __attribute__((naked)) void nn_sdk_func_003f5a3c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe59f1010\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe1a00000\n"
        ".inst 0xe59f0008\n"
        ".inst 0xe1c040f0\n"
        ".inst 0xe8bd8070\n"
        ".word 0x04000047 @ bounded tail data\n"
        ".word 0x0044e918 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003f5e08, 44)
extern "C" __attribute__((naked)) void nn_sdk_func_003f5e08() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe59f1010\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe1a00000\n"
        ".inst 0xe59f0008\n"
        ".inst 0xe1c040f0\n"
        ".inst 0xe8bd8070\n"
        ".word 0x04000068 @ bounded tail data\n"
        ".word 0x0044e930 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003f6c40, 44)
extern "C" __attribute__((naked)) void nn_sdk_func_003f6c40() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe59f1010\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe1a00000\n"
        ".inst 0xe59f0008\n"
        ".inst 0xe1c040f0\n"
        ".inst 0xe8bd8070\n"
        ".word 0x040000eb @ bounded tail data\n"
        ".word 0x0044e990 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e0df8, 48)
extern "C" __attribute__((naked)) void func_003e0df8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5902004\n"
        ".inst 0xe5903000\n"
        ".inst 0xe0422003\n"
        ".inst 0xe1a020c2\n"
        ".inst 0xe3520c01\n"
        ".inst 0x95812000\n"
        ".inst 0x95900000\n"
        ".inst 0x859f0008\n"
        ".inst 0x95810004\n"
        ".inst 0x93a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0xe0e046c7 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e0e7c, 48)
extern "C" __attribute__((naked)) void func_003e0e7c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5902004\n"
        ".inst 0xe5903000\n"
        ".inst 0xe0422003\n"
        ".inst 0xe1a020c2\n"
        ".inst 0xe3520c01\n"
        ".inst 0x95812000\n"
        ".inst 0x95900000\n"
        ".inst 0x859f0008\n"
        ".inst 0x95810004\n"
        ".inst 0x93a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0xe0e046c8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e70c8, 48)
extern "C" __attribute__((naked)) void func_003e70c8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5910000\n"
        ".inst 0xe59f2020\n"
        ".inst 0xe1500002\n"
        ".inst 0x13a00000\n"
        ".inst 0x1a000004\n"
        ".inst 0xe5911008\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe28114fe\n"
        ".inst 0xe3510801\n"
        ".inst 0x93a00001\n"
        ".inst 0xe12fff1e\n"
        ".word 0x4d545343 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003f6708, 48)
extern "C" __attribute__((naked)) void engine_func_003f6708() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe1a05001\n"
        ".inst 0xebfb34e2\n"
        ".inst 0xe5940038\n"
        ".inst 0xe5850000\n"
        ".inst 0xe59f0008\n"
        ".inst 0xebfb34bd\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8070\n"
        ".word 0x004d4674 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00338658, 52)
extern "C" __attribute__((naked)) void func_00338658() {
    asm volatile(
        ".arm\n"
        ".inst 0xe2800b07\n"
        ".inst 0xe2800fa9\n"
        ".inst 0xed9f0a08\n"
        ".inst 0xe3a01000\n"
        ".inst 0xed800a00\n"
        ".inst 0xed800a01\n"
        ".inst 0xed800a02\n"
        ".inst 0xed800a03\n"
        ".inst 0xed800a04\n"
        ".inst 0xed800a05\n"
        ".inst 0xe5801018\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e69dc, 52)
extern "C" __attribute__((naked)) void func_003e69dc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5902000\n"
        ".inst 0xe1520001\n"
        ".inst 0xe59f2020\n"
        ".inst 0x9a000005\n"
        ".inst 0xe0801181\n"
        ".inst 0xe1d130b4\n"
        ".inst 0xe1530002\n"
        ".inst 0x05911008\n"
        ".inst 0x00800001\n"
        ".inst 0x0a000000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00004101 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e6a10, 52)
extern "C" __attribute__((naked)) void func_003e6a10() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5902000\n"
        ".inst 0xe1520001\n"
        ".inst 0xe59f2020\n"
        ".inst 0x9a000005\n"
        ".inst 0xe0801181\n"
        ".inst 0xe1d130b4\n"
        ".inst 0xe1530002\n"
        ".inst 0x05911008\n"
        ".inst 0x00800001\n"
        ".inst 0x0a000000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00004102 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e6af4, 52)
extern "C" __attribute__((naked)) void func_003e6af4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4008\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe1a0100d\n"
        ".inst 0xe2800004\n"
        ".inst 0xebfb00a2\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe59d0000\n"
        ".inst 0xe1a00800\n"
        ".inst 0xe1a00c20\n"
        ".inst 0xe3500001\n"
        ".inst 0x13a00000\n"
        ".inst 0xe8bd8008\n"
    );
}

// DECOMP_FUNC(0x003f9044, 52)
extern "C" __attribute__((naked)) void func_003f9044() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfffe69\n"
        ".inst 0xe5d01002\n"
        ".inst 0xe5d00001\n"
        ".inst 0xed940a03\n"
        ".inst 0xe201100f\n"
        ".inst 0xed941a02\n"
        ".inst 0xe0800401\n"
        ".inst 0xee000a90\n"
        ".inst 0xeef80a60\n"
        ".inst 0xee000a81\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x003e646c, 56)
extern "C" __attribute__((naked)) void func_003e646c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4038\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a02009\n"
        ".inst 0xe1a0100d\n"
        ".inst 0xebfb0244\n"
        ".inst 0xe3500000\n"
        ".inst 0x059f0014\n"
        ".inst 0x0a000003\n"
        ".inst 0xe59d0000\n"
        ".inst 0xe0800004\n"
        ".inst 0xe5901004\n"
        ".inst 0xe0800001\n"
        ".inst 0xe8bd8038\n"
        ".word 0x004765dd @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003ea4f8, 56)
extern "C" __attribute__((naked)) void camp_func_003ea4f8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04002\n"
        ".inst 0xe1a01081\n"
        ".inst 0xe3a00026\n"
        ".inst 0xebfb5a6d\n"
        ".inst 0xe1a06000\n"
        ".inst 0xebfb5a61\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xebfb5a4a\n"
        ".inst 0xe1540000\n"
        ".inst 0x23a00000\n"
        ".inst 0x30850284\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x003d71c4, 60)
extern "C" __attribute__((naked)) void func_003d71c4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe2801b01\n"
        ".inst 0xed9f0a0b\n"
        ".inst 0xe2811fce\n"
        ".inst 0xed810a02\n"
        ".inst 0xed810a01\n"
        ".inst 0xed810a00\n"
        ".inst 0xe5902634\n"
        ".inst 0xe3c22502\n"
        ".inst 0xe5a02634\n"
        ".inst 0xe2800e13\n"
        ".inst 0xed800a02\n"
        ".inst 0xed800a01\n"
        ".inst 0xed800a00\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003d8acc, 60)
extern "C" __attribute__((naked)) void battle_func_003d8acc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe2801b01\n"
        ".inst 0xed9f0a0b\n"
        ".inst 0xe2811fa2\n"
        ".inst 0xed810a02\n"
        ".inst 0xed810a01\n"
        ".inst 0xed810a00\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5801694\n"
        ".inst 0xe2801b01\n"
        ".inst 0xe5900634\n"
        ".inst 0xe2811f8d\n"
        ".inst 0xe3800020\n"
        ".inst 0xe5810000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e84f0, 60)
extern "C" __attribute__((naked)) void func_003e84f0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4038\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a02009\n"
        ".inst 0xe1a0100d\n"
        ".inst 0xe2800004\n"
        ".inst 0xebfafa22\n"
        ".inst 0xe3500000\n"
        ".inst 0x059f0014\n"
        ".inst 0x0a000003\n"
        ".inst 0xe59d0000\n"
        ".inst 0xe0800004\n"
        ".inst 0xe5901004\n"
        ".inst 0xe0800001\n"
        ".inst 0xe8bd8038\n"
        ".word 0x004765d8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00300150, 64)
extern "C" __attribute__((naked)) void ui_func_00300150() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a00000\n"
        ".inst 0xebfe5b80\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe3a04000\n"
        ".inst 0xebfe4ecb\n"
        ".inst 0xe1a01005\n"
        ".inst 0xebfe0a88\n"
        ".inst 0xe3500000\n"
        ".inst 0x159f4010\n"
        ".inst 0x119040f4\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfe3773\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8070\n"
        ".word 0x000001b6 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0031b960, 64)
extern "C" __attribute__((naked)) void camp_func_0031b960() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f000c\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x13a00001\n"
        ".inst 0xe12fff1e\n"
        ".inst 0x0044cdf0\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe5900000\n"
        ".inst 0xe5901760\n"
        ".inst 0xe2411001\n"
        ".inst 0xe3510000\n"
        ".inst 0xe5801760\n"
        ".inst 0xb3a01003\n"
        ".inst 0xb580114c\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00432cc8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0031bfcc, 64)
extern "C" __attribute__((naked)) void script_vm_func_0031bfcc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f4030\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000008\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfe8d0c\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000004\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5900000\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafea16c\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043e088 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00324b68, 64)
extern "C" __attribute__((naked)) void func_00324b68() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1030\n"
        ".inst 0xe3a02008\n"
        ".inst 0xe3a00000\n"
        ".inst 0xed9f0a0a\n"
        ".inst 0xe5c12088\n"
        ".inst 0xe5c10089\n"
        ".inst 0xe5c1008a\n"
        ".inst 0xe2811d1d\n"
        ".inst 0xe5810000\n"
        ".inst 0xe5810004\n"
        ".inst 0xe5810008\n"
        ".inst 0xe581000c\n"
        ".inst 0xed810a03\n"
        ".inst 0xe12fff1e\n"
        ".word 0x004d8b40 @ bounded tail data\n"
        ".word 0x3f800000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00327b18, 64)
extern "C" __attribute__((naked)) void func_00327b18() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0034\n"
        ".inst 0xed9f0a0b\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe2401e73\n"
        ".inst 0xed800a00\n"
        ".inst 0xed800a01\n"
        ".inst 0xed800a02\n"
        ".inst 0xed800a03\n"
        ".inst 0xe3a03008\n"
        ".inst 0xe5c13088\n"
        ".inst 0xe5c12089\n"
        ".inst 0xe1a00002\n"
        ".inst 0xe5c1208a\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000 @ bounded tail data\n"
        ".word 0x004d9270 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00340918, 64)
extern "C" __attribute__((naked)) void func_00340918() {
    asm volatile(
        ".arm\n"
        ".inst 0xee001a10\n"
        ".inst 0xeddf0a0c\n"
        ".inst 0xee013a10\n"
        ".inst 0xe0822001\n"
        ".inst 0xe580100c\n"
        ".inst 0xe0821003\n"
        ".inst 0xeeb80ac0\n"
        ".inst 0xe5801014\n"
        ".inst 0xeeb81ac1\n"
        ".inst 0xe5802010\n"
        ".inst 0xeec01a80\n"
        ".inst 0xedc01a06\n"
        ".inst 0xee800a81\n"
        ".inst 0xed800a07\n"
        ".inst 0xe12fff1e\n"
        ".word 0x3f800000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00360354, 64)
extern "C" __attribute__((naked)) void func_00360354() {
    asm volatile(
        ".arm\n"
        ".inst 0xed9f0a0d\n"
        ".inst 0xe5801000\n"
        ".inst 0xed800a15\n"
        ".inst 0xed800a11\n"
        ".inst 0xed800a0d\n"
        ".inst 0xed800a16\n"
        ".inst 0xed800a12\n"
        ".inst 0xed800a0e\n"
        ".inst 0xed800a17\n"
        ".inst 0xed800a13\n"
        ".inst 0xed800a0f\n"
        ".inst 0xed800a18\n"
        ".inst 0xed800a14\n"
        ".inst 0xed800a10\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00360780, 64)
extern "C" __attribute__((naked)) void engine_func_00360780() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4038\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a05000\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xe58d5000\n"
        ".inst 0xeb00010c\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x1bfd71a9\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xef000023\n"
        ".inst 0xe5845000\n"
        ".inst 0xe59d0000\n"
        ".inst 0xe5840000\n"
        ".inst 0xe8bd8038\n"
    );
}

// DECOMP_FUNC(0x00368820, 64)
extern "C" __attribute__((naked)) void func_00368820() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xedd00a0e\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe2841044\n"
        ".inst 0xee301a80\n"
        ".inst 0xec910a02\n"
        ".inst 0xe594104c\n"
        ".inst 0xe5900050\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe5940038\n"
        ".inst 0xed840a0e\n"
        ".inst 0xe584003c\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe5c40058\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00000000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0036a25c, 64)
extern "C" __attribute__((naked)) void func_0036a25c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5d01008\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0028\n"
        ".inst 0xe3510000\n"
        ".inst 0xe5840000\n"
        ".inst 0x1594100c\n"
        ".inst 0x13510000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5940004\n"
        ".inst 0xe5902000\n"
        ".inst 0xe592200c\n"
        ".inst 0xe12fff32\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00421104 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0036ac80, 64)
extern "C" __attribute__((naked)) void func_0036ac80() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5d01008\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0028\n"
        ".inst 0xe3510000\n"
        ".inst 0xe5840000\n"
        ".inst 0x1594100c\n"
        ".inst 0x13510000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5940004\n"
        ".inst 0xe5902000\n"
        ".inst 0xe592200c\n"
        ".inst 0xe12fff32\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0042114c @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0036aed4, 64)
extern "C" __attribute__((naked)) void func_0036aed4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5d01009\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0028\n"
        ".inst 0xe3510000\n"
        ".inst 0xe5840000\n"
        ".inst 0x1594101c\n"
        ".inst 0x13510000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5940004\n"
        ".inst 0xe5902000\n"
        ".inst 0xe592200c\n"
        ".inst 0xe12fff32\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00421194 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0036b570, 64)
extern "C" __attribute__((naked)) void func_0036b570() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5d01008\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0028\n"
        ".inst 0xe3510000\n"
        ".inst 0xe5840000\n"
        ".inst 0x1594100c\n"
        ".inst 0x13510000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5940004\n"
        ".inst 0xe5902000\n"
        ".inst 0xe592200c\n"
        ".inst 0xe12fff32\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x004211f4 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0036d03c, 64)
extern "C" __attribute__((naked)) void func_0036d03c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5d01009\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0028\n"
        ".inst 0xe3510000\n"
        ".inst 0xe5840000\n"
        ".inst 0x1594101c\n"
        ".inst 0x13510000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5940004\n"
        ".inst 0xe5902000\n"
        ".inst 0xe592200c\n"
        ".inst 0xe12fff32\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00421244 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0036e2b8, 64)
extern "C" __attribute__((naked)) void func_0036e2b8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5d01009\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f0028\n"
        ".inst 0xe3510000\n"
        ".inst 0xe5840000\n"
        ".inst 0x1594101c\n"
        ".inst 0x13510000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5940004\n"
        ".inst 0xe5902000\n"
        ".inst 0xe592200c\n"
        ".inst 0xe12fff32\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00421304 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0036f338, 64)
extern "C" __attribute__((naked)) void func_0036f338() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5900000\n"
        ".inst 0xe5901004\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000009\n"
        ".inst 0xe5903000\n"
        ".inst 0xe59f2020\n"
        ".inst 0xe3530102\n"
        ".inst 0x0a000003\n"
        ".inst 0xe3530101\n"
        ".inst 0x1a000003\n"
        ".inst 0xe5922004\n"
        ".inst 0xe12fff12\n"
        ".inst 0xe5922000\n"
        ".inst 0xe12fff12\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0044e8f0 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0037f880, 64)
extern "C" __attribute__((naked)) void func_0037f880() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a06001\n"
        ".inst 0xe3a04000\n"
        ".inst 0xe5c0100e\n"
        ".inst 0xe354000f\n"
        ".inst 0xca000004\n"
        ".inst 0xe0850104\n"
        ".inst 0xe590008c\n"
        ".inst 0xe3500000\n"
        ".inst 0x11a01006\n"
        ".inst 0x1bfff86f\n"
        ".inst 0xe2844001\n"
        ".inst 0xe3540010\n"
        ".inst 0xbafffff5\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00380c70, 64)
extern "C" __attribute__((naked)) void func_00380c70() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfad317\n"
        ".inst 0xe594000c\n"
        ".inst 0xe3100001\n"
        ".inst 0x15940010\n"
        ".inst 0x1a000006\n"
        ".inst 0xe59f1018\n"
        ".inst 0xe2000038\n"
        ".inst 0xe1a001a0\n"
        ".inst 0xe7911100\n"
        ".inst 0xe2840010\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xe12fff11\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00471c20 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003aaef0, 64)
extern "C" __attribute__((naked)) void camp_func_003aaef0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f000c\n"
        ".inst 0xe3a01004\n"
        ".inst 0xe5900004\n"
        ".inst 0xe5c0101d\n"
        ".inst 0xe12fff1e\n"
        ".inst 0x0043d9e0\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5900000\n"
        ".inst 0xe5900000\n"
        ".inst 0xe5901000\n"
        ".inst 0xe591100c\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043d9c8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003bbed4, 64)
extern "C" __attribute__((naked)) void ui_func_003bbed4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f402c\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfe6ed0\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe5911000\n"
        ".inst 0xebf9bc0f\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfe6ec9\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafc657f\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00000e5c @ bounded tail data\n"
        ".word 0x0043ddb8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e68bc, 64)
extern "C" __attribute__((naked)) void func_003e68bc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1034\n"
        ".inst 0xe1d021b4\n"
        ".inst 0xe1520001\n"
        ".inst 0x02800014\n"
        ".inst 0x0a000007\n"
        ".inst 0xe1d022b0\n"
        ".inst 0xe1520001\n"
        ".inst 0x02800020\n"
        ".inst 0x0a000003\n"
        ".inst 0xe1d022bc\n"
        ".inst 0xe1520001\n"
        ".inst 0x0280002c\n"
        ".inst 0x13a00000\n"
        ".inst 0xe5900004\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00004002 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e6934, 64)
extern "C" __attribute__((naked)) void func_003e6934() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1034\n"
        ".inst 0xe1d021b4\n"
        ".inst 0xe1520001\n"
        ".inst 0x02800014\n"
        ".inst 0x0a000007\n"
        ".inst 0xe1d022b0\n"
        ".inst 0xe1520001\n"
        ".inst 0x02800020\n"
        ".inst 0x0a000003\n"
        ".inst 0xe1d022bc\n"
        ".inst 0xe1520001\n"
        ".inst 0x0280002c\n"
        ".inst 0x13a00000\n"
        ".inst 0xe5900004\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00004001 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003f6228, 64)
extern "C" __attribute__((naked)) void func_003f6228() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe59f5030\n"
        ".inst 0xe5951004\n"
        ".inst 0xe3510000\n"
        ".inst 0x13500000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900004\n"
        ".inst 0xe3500000\n"
        ".inst 0x112fff31\n"
        ".inst 0xe5951004\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd4070\n"
        ".inst 0xe12fff11\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0044e948 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003f6368, 64)
extern "C" __attribute__((naked)) void func_003f6368() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe59f5030\n"
        ".inst 0xe5951004\n"
        ".inst 0xe3510000\n"
        ".inst 0x13500000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900010\n"
        ".inst 0xe3500000\n"
        ".inst 0x112fff31\n"
        ".inst 0xe5951004\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd4070\n"
        ".inst 0xe12fff11\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0044e960 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00341c04, 68)
extern "C" __attribute__((naked)) void engine_func_00341c04() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe24dd080\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a02001\n"
        ".inst 0xe28f1024\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xfafdf2f6\n"
        ".inst 0xe3a01007\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xebfd686b\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe5840028\n"
        ".inst 0xebfd7aa3\n"
        ".inst 0xe28dd080\n"
        ".inst 0xe8bd8010\n"
        ".word 0x622e7325 @ bounded tail data\n"
        ".word 0x00006d61 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00351e24, 68)
extern "C" __attribute__((naked)) void engine_func_00351e24() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a04001\n"
        ".inst 0xebfdd061\n"
        ".inst 0xeb0020d9\n"
        ".inst 0xe1a05000\n"
        ".inst 0xebf7d21e\n"
        ".inst 0xe3550000\n"
        ".inst 0x059f0018\n"
        ".inst 0x0a000003\n"
        ".inst 0xe1a01004\n"
        ".inst 0xe1a00006\n"
        ".inst 0xe8bd4070\n"
        ".inst 0xea000026\n"
        ".inst 0xe8bd8070\n"
        ".word 0xe0409fff @ bounded tail data\n"
        ".word 0xc9209f84 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00362374, 68)
extern "C" __attribute__((naked)) void func_00362374() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1038\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe2804010\n"
        ".inst 0xe5801000\n"
        ".inst 0xe5900014\n"
        ".inst 0xe5840008\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x15941004\n"
        ".inst 0x13510000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe5902000\n"
        ".inst 0xe592200c\n"
        ".inst 0xe12fff32\n"
        ".inst 0xe2440010\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00420c4c @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00376c88, 68)
extern "C" __attribute__((naked)) void func_00376c88() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe5914004\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe3540000\n"
        ".inst 0x0a000009\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb000c8a\n"
        ".inst 0xe1a01004\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb000b91\n"
        ".inst 0xe2860018\n"
        ".inst 0xe286101c\n"
        ".inst 0xe2842018\n"
        ".inst 0xe8bd4070\n"
        ".inst 0xeafd22aa\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00377924, 68)
extern "C" __attribute__((naked)) void func_00377924() {
    asm volatile(
        ".arm\n"
        ".inst 0xedd11a13\n"
        ".inst 0xeddf0a0d\n"
        ".inst 0xed911a17\n"
        ".inst 0xeeb40ae1\n"
        ".inst 0xeef1fa10\n"
        ".inst 0xda000007\n"
        ".inst 0xee300a61\n"
        ".inst 0xedd10a14\n"
        ".inst 0xed912a16\n"
        ".inst 0xeec01a20\n"
        ".inst 0xee610a82\n"
        ".inst 0xeef40ac1\n"
        ".inst 0xeef1fa10\n"
        ".inst 0xcef00a41\n"
        ".inst 0xedc30a00\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0038e480, 68)
extern "C" __attribute__((naked)) void func_0038e480() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5801000\n"
        ".inst 0xe59f0018\n"
        ".inst 0xe5900000\n"
        ".inst 0xe2800088\n"
        ".inst 0xebfcb1e4\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafc901c\n"
        ".inst 0x00421ee0\n"
        ".inst 0x00432fc8\n"
        ".inst 0xe1d000b0\n"
        ".inst 0xe1d110b0\n"
        ".inst 0xe0400001\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x003bbd74, 68)
extern "C" __attribute__((naked)) void engine_func_003bbd74() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a05001\n"
        ".inst 0xebf98dad\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000009\n"
        ".inst 0xe284000c\n"
        ".inst 0xebfce4a2\n"
        ".inst 0xe1a01005\n"
        ".inst 0xebfcbee1\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a000003\n"
        ".inst 0xe1a01005\n"
        ".inst 0xe8bd4070\n"
        ".inst 0xe3a00000\n"
        ".inst 0xeafcbedb\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x003e46a4, 68)
extern "C" __attribute__((naked)) void func_003e46a4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe2814030\n"
        ".inst 0xed910a0c\n"
        ".inst 0xebfb1e82\n"
        ".inst 0xed840a00\n"
        ".inst 0xed940a01\n"
        ".inst 0xebfb1e7f\n"
        ".inst 0xed840a01\n"
        ".inst 0xed940a02\n"
        ".inst 0xebfb1e7c\n"
        ".inst 0xed840a02\n"
        ".inst 0xe595003c\n"
        ".inst 0xe3800b02\n"
        ".inst 0xe585003c\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x003f6318, 68)
extern "C" __attribute__((naked)) void nn_sdk_func_003f6318() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4030\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe59f1028\n"
        ".inst 0xe24dd00c\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe1a00000\n"
        ".inst 0xe28d2008\n"
        ".inst 0xe28d1004\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xebf6256b\n"
        ".inst 0xe59f000c\n"
        ".inst 0xe1c040f0\n"
        ".inst 0xe28dd00c\n"
        ".inst 0xe8bd8030\n"
        ".word 0x040000a9 @ bounded tail data\n"
        ".word 0x0044e960 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003f752c, 68)
extern "C" __attribute__((naked)) void func_003f752c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5900010\n"
        ".inst 0xeafb3343\n"
        ".inst 0xe2801020\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe5801004\n"
        ".inst 0xe5802000\n"
        ".inst 0xe5801008\n"
        ".inst 0xe590100c\n"
        ".inst 0xe3a01106\n"
        ".inst 0xe580100c\n"
        ".inst 0xe12fff1e\n"
        ".inst 0xe2801004\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe5801004\n"
        ".inst 0xe5802000\n"
        ".inst 0xe5801008\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00355f78, 72)
extern "C" __attribute__((naked)) void ui_func_00355f78() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4038\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1b00001\n"
        ".inst 0xe1a02003\n"
        ".inst 0xe59d3010\n"
        ".inst 0x059f0028\n"
        ".inst 0x0a000008\n"
        ".inst 0xe5901000\n"
        ".inst 0xe591c000\n"
        ".inst 0xe1a0100d\n"
        ".inst 0xe12fff3c\n"
        ".inst 0xe1b01fa0\n"
        ".inst 0x1a000002\n"
        ".inst 0xe59d0000\n"
        ".inst 0xe5840000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8038\n"
        ".word 0xc8804465 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0037c424, 72)
extern "C" __attribute__((naked)) void func_0037c424() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe5900040\n"
        ".inst 0xe3500001\n"
        ".inst 0x0a00000b\n"
        ".inst 0xe5950008\n"
        ".inst 0xe3a04000\n"
        ".inst 0xe3500000\n"
        ".inst 0xda000007\n"
        ".inst 0xe7950104\n"
        ".inst 0xe3500000\n"
        ".inst 0x15951040\n"
        ".inst 0x1bff8fb1\n"
        ".inst 0xe5950008\n"
        ".inst 0xe2844001\n"
        ".inst 0xe1500004\n"
        ".inst 0xcafffff7\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00324010, 76)
extern "C" __attribute__((naked)) void engine_func_00324010() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfdcbd0\n"
        ".inst 0xe1b04000\n"
        ".inst 0x03a00001\n"
        ".inst 0x0a000007\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000005\n"
        ".inst 0xebfe77bb\n"
        ".inst 0xe3500000\n"
        ".inst 0x15940004\n"
        ".inst 0x1bfbf6cc\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8010\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfe80c2\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00351b7c, 76)
extern "C" __attribute__((naked)) void nn_sdk_func_00351b7c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1038\n"
        ".inst 0xe59f0038\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb003a9e\n"
        ".inst 0xe3a00001\n"
        ".inst 0xeb003b11\n"
        ".inst 0xe59f0028\n"
        ".inst 0xeb003af8\n"
        ".inst 0xe59f0020\n"
        ".inst 0xe5900000\n"
        ".inst 0xef000019\n"
        ".inst 0xe1b01fa0\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafdce2b\n"
        ".inst 0xe8bd8010\n"
        ".word 0x004092a0 @ bounded tail data\n"
        ".word 0x00471bac @ bounded tail data\n"
        ".word 0x0044e9e8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00353160, 76)
extern "C" __attribute__((naked)) void func_00353160() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4008\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe1a03001\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xebfffc97\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe1500001\n"
        ".inst 0x03a00000\n"
        ".inst 0x0a000005\n"
        ".inst 0xe1b01fa0\n"
        ".inst 0x1a000003\n"
        ".inst 0xe5dd0000\n"
        ".inst 0xe3500000\n"
        ".inst 0x159f0008\n"
        ".inst 0x0affffff\n"
        ".inst 0xe8bd8008\n"
        ".word 0xd8a083fa @ bounded tail data\n"
        ".word 0xe0a13899 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0035f454, 76)
extern "C" __attribute__((naked)) void func_0035f454() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3520000\n"
        ".inst 0xc59fc03c\n"
        ".inst 0xe3a00000\n"
        ".inst 0xda00000b\n"
        ".inst 0xe0813080\n"
        ".inst 0xe1d330b0\n"
        ".inst 0xe3530000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe3530040\n"
        ".inst 0x1153000c\n"
        ".inst 0x1a000001\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe12fff1e\n"
        ".inst 0xe2800001\n"
        ".inst 0xe1520000\n"
        ".inst 0xcafffff3\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0000ff20 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00379a28, 76)
extern "C" __attribute__((naked)) void engine_func_00379a28() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe5910008\n"
        ".inst 0xe1a04001\n"
        ".inst 0xe5911010\n"
        ".inst 0xe5902000\n"
        ".inst 0xe5922008\n"
        ".inst 0xe12fff32\n"
        ".inst 0xe1b06000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe284100c\n"
        ".inst 0xe8910006\n"
        ".inst 0xebfd3165\n"
        ".inst 0xe5943010\n"
        ".inst 0xe8940007\n"
        ".inst 0xe585302c\n"
        ".inst 0xe285501c\n"
        ".inst 0xe8850047\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x003972c8, 76)
extern "C" __attribute__((naked)) void func_003972c8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe2800008\n"
        ".inst 0xe1510000\n"
        ".inst 0xe1a04001\n"
        ".inst 0x0a00000b\n"
        ".inst 0xe5941000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xebfffff6\n"
        ".inst 0xe5941004\n"
        ".inst 0xe1a00005\n"
        ".inst 0xebfffff3\n"
        ".inst 0xe5950000\n"
        ".inst 0xe1a01004\n"
        ".inst 0xe5902000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xe8bd4070\n"
        ".inst 0xe12fff12\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x003eb014, 76)
extern "C" __attribute__((naked)) void func_003eb014() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe2404044\n"
        ".inst 0xe5500038\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a00000c\n"
        ".inst 0xe5940064\n"
        ".inst 0xe1510000\n"
        ".inst 0x8a000009\n"
        ".inst 0xe1500002\n"
        ".inst 0x8a000007\n"
        ".inst 0xe5d4000d\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000004\n"
        ".inst 0xebfb4978\n"
        ".inst 0xe2841050\n"
        ".inst 0xebfb31c6\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5c4000d\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x003f5e40, 76)
extern "C" __attribute__((naked)) void func_003f5e40() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe59f503c\n"
        ".inst 0xe5951004\n"
        ".inst 0xe3510000\n"
        ".inst 0x13500000\n"
        ".inst 0x0a00000a\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900004\n"
        ".inst 0xe3500000\n"
        ".inst 0x112fff31\n"
        ".inst 0xe5951004\n"
        ".inst 0xe5940000\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe5951004\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd4070\n"
        ".inst 0xe12fff11\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0044e930 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00311d20, 80)
extern "C" __attribute__((naked)) void camp_func_00311d20() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4030\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe24dd014\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe3a0001f\n"
        ".inst 0xebfe8b27\n"
        ".inst 0xe4902004\n"
        ".inst 0xe59f3028\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe2420004\n"
        ".inst 0xe1cd40ba\n"
        ".inst 0xe1a021a0\n"
        ".inst 0xe58d3000\n"
        ".inst 0xe3a03008\n"
        ".inst 0xe28d0008\n"
        ".inst 0xe1cd50b8\n"
        ".inst 0xfafe8add\n"
        ".inst 0xe28dd014\n"
        ".inst 0xe8bd8030\n"
        ".word 0x001e15bc @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0034f648, 80)
extern "C" __attribute__((naked)) void ui_func_0034f648() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f1038\n"
        ".inst 0xe3a04000\n"
        ".inst 0xe5804004\n"
        ".inst 0xe5804008\n"
        ".inst 0xe480100c\n"
        ".inst 0xe59f1028\n"
        ".inst 0xe3a03003\n"
        ".inst 0xe3a02020\n"
        ".inst 0xe4804034\n"
        ".inst 0xfafdda38\n"
        ".inst 0xe2400040\n"
        ".inst 0xe5804010\n"
        ".inst 0xe5804014\n"
        ".inst 0xe5804018\n"
        ".inst 0xe58040a0\n"
        ".inst 0xe8bd8010\n"
        ".inst 0x0042067c\n"
        ".inst 0x0034e01c\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00357be4, 80)
extern "C" __attribute__((naked)) void engine_func_00357be4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d40f8\n"
        ".inst 0xe1a0c000\n"
        ".inst 0xe1a05002\n"
        ".inst 0xe59d001c\n"
        ".inst 0xe1a06003\n"
        ".inst 0xe1a04001\n"
        ".inst 0xe58d0000\n"
        ".inst 0xe59d3018\n"
        ".inst 0xe1a02006\n"
        ".inst 0xe1a01005\n"
        ".inst 0xe1a0000c\n"
        ".inst 0xebffffc5\n"
        ".inst 0xe2101102\n"
        ".inst 0x4a000004\n"
        ".inst 0xe1a02006\n"
        ".inst 0xe1a01005\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd40f8\n"
        ".inst 0xea000856\n"
        ".inst 0xe8bd80f8\n"
    );
}

// DECOMP_FUNC(0x0038007c, 80)
extern "C" __attribute__((naked)) void func_0038007c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5d000ca\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a00000d\n"
        ".inst 0xe5d40090\n"
        ".inst 0xe3500004\n"
        ".inst 0x0a000008\n"
        ".inst 0xe5940134\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5d410c9\n"
        ".inst 0xe3510000\n"
        ".inst 0x03a01001\n"
        ".inst 0x0bfff096\n"
        ".inst 0xe3a00004\n"
        ".inst 0xe5c40090\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5c400c5\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0038b334, 80)
extern "C" __attribute__((naked)) void func_0038b334() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5801000\n"
        ".inst 0xe59f0018\n"
        ".inst 0xe5900000\n"
        ".inst 0xe2800088\n"
        ".inst 0xebfcbe37\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafc9c6f\n"
        ".inst 0x00421e0c\n"
        ".inst 0x00432fc8\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5801000\n"
        ".inst 0xe5801004\n"
        ".inst 0xe5801008\n"
        ".inst 0xe5c0100c\n"
        ".inst 0xe5c0100d\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x003ac930, 80)
extern "C" __attribute__((naked)) void engine_func_003ac930() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f4018\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000002\n"
        ".inst 0xebfc5e85\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840000\n"
        ".inst 0xe8bd8010\n"
        ".inst 0x0043d990\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5900000\n"
        ".inst 0xe5900000\n"
        ".inst 0xe5901000\n"
        ".inst 0xe5911014\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043d9c8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003beaf0, 80)
extern "C" __attribute__((naked)) void ui_func_003beaf0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe24dd028\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfb5465\n"
        ".inst 0xe1a01004\n"
        ".inst 0xebfb1022\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfb5461\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe1a02004\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xebfa22b0\n"
        ".inst 0xe5dd001d\n"
        ".inst 0xeddf0a04\n"
        ".inst 0xe28dd028\n"
        ".inst 0xee000a10\n"
        ".inst 0xeeb80a40\n"
        ".inst 0xee200a20\n"
        ".inst 0xe8bd8010\n"
        ".word 0x3c23d70a @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003bed80, 80)
extern "C" __attribute__((naked)) void ui_func_003bed80() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe24dd028\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfb53c1\n"
        ".inst 0xe1a01004\n"
        ".inst 0xebfb0f7e\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfb53bd\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe1a02004\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xebfa220c\n"
        ".inst 0xe5dd001e\n"
        ".inst 0xeddf0a04\n"
        ".inst 0xe28dd028\n"
        ".inst 0xee000a10\n"
        ".inst 0xeeb80a40\n"
        ".inst 0xee200a20\n"
        ".inst 0xe8bd8010\n"
        ".word 0x3c23d70a @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e51c4, 80)
extern "C" __attribute__((naked)) void func_003e51c4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d41f0\n"
        ".inst 0xe1a06001\n"
        ".inst 0xe1a07000\n"
        ".inst 0xe59d4018\n"
        ".inst 0xe1a05003\n"
        ".inst 0xe1a02003\n"
        ".inst 0xed940a00\n"
        ".inst 0xebfffc9a\n"
        ".inst 0xed940a01\n"
        ".inst 0xe1a02005\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe1a00007\n"
        ".inst 0xebfffcc3\n"
        ".inst 0xed940a02\n"
        ".inst 0xe1a02005\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe1a00007\n"
        ".inst 0xebf90364\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd81f0\n"
    );
}
