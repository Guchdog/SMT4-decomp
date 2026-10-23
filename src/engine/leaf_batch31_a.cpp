#include "types.h"

// Batch 31 A: raw ARM encodings with explicit bounded return/data tails.

// DECOMP_FUNC(0x0034afe4, 8)
extern "C" __attribute__((naked)) void func_0034afe4() {
    asm volatile(
        ".arm\n"
        ".inst 0xeafd9d4d\n"
        ".inst 0xe12fff1e\n"
    );
}
// DECOMP_FUNC(0x0035311c, 8)
extern "C" __attribute__((naked)) void engine_func_0035311c() {
    asm volatile(
        ".arm\n"
        ".inst 0xeafb9c8c\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00394ee0, 12)
extern "C" __attribute__((naked)) void script_vm_func_00394ee0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00001\n"
        ".inst 0xeafcc254\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x003968c0, 20)
extern "C" __attribute__((naked)) void script_vm_func_003968c0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5901000\n"
        ".inst 0xe3110001\n"
        ".inst 0x1a000000\n"
        ".inst 0xea000000\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x003eafac, 20)
extern "C" __attribute__((naked)) void func_003eafac() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3510000\n"
        ".inst 0xe2800004\n"
        ".inst 0x0a000000\n"
        ".inst 0xeafae11a\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0033858c, 24)
extern "C" __attribute__((naked)) void engine_func_0033858c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe2800901\n"
        ".inst 0xe5900394\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000000\n"
        ".inst 0xeafd7cdf\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00349740, 24)
extern "C" __attribute__((naked)) void func_00349740() {
    asm volatile(
        ".arm\n"
        ".inst 0xeafda376\n"
        ".inst 0xe12fff1e\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe5802000\n"
        ".inst 0xe5802004\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00351e98, 24)
extern "C" __attribute__((naked)) void func_00351e98() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000\n"
        ".inst 0x059f0008\n"
        ".inst 0x0a000000\n"
        ".inst 0xea0000a9\n"
        ".inst 0xe12fff1e\n"
        ".word 0xe0409fff @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00351ee0, 24)
extern "C" __attribute__((naked)) void func_00351ee0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000\n"
        ".inst 0x059f0008\n"
        ".inst 0x0a000000\n"
        ".inst 0xea0000b5\n"
        ".inst 0xe12fff1e\n"
        ".word 0xe0409fff @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003c0a90, 24)
extern "C" __attribute__((naked)) void func_003c0a90() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5900008\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xe3a01000\n"
        ".inst 0xeafbae13\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x003d6634, 24)
extern "C" __attribute__((naked)) void func_003d6634() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5900730\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xe3a01000\n"
        ".inst 0xeafb2824\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00308c7c, 28)
extern "C" __attribute__((naked)) void script_vm_func_00308c7c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000000\n"
        ".inst 0xea00001b\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00447e28 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0030f518, 28)
extern "C" __attribute__((naked)) void script_vm_func_0030f518() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000000\n"
        ".inst 0xeaffe5f4\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00447060 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0031074c, 28)
extern "C" __attribute__((naked)) void script_vm_func_0031074c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfde4bc\n"
        ".inst 0xe3500000\n"
        ".inst 0x13a00001\n"
        ".inst 0x1bfde4ad\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0034b3a0, 28)
extern "C" __attribute__((naked)) void func_0034b3a0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1b00001\n"
        ".inst 0x0a000002\n"
        ".inst 0xe59f1008\n"
        ".inst 0xe5911004\n"
        ".inst 0xe12fff11\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0044e990 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003604a4, 28)
extern "C" __attribute__((naked)) void func_003604a4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb0000d2\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafd7262\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x003605ec, 28)
extern "C" __attribute__((naked)) void func_003605ec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb0000eb\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafd7210\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x003606b0, 28)
extern "C" __attribute__((naked)) void func_003606b0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb0000d5\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafd71df\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x003606cc, 28)
extern "C" __attribute__((naked)) void func_003606cc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb0000dd\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafd71d8\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x003606e8, 28)
extern "C" __attribute__((naked)) void func_003606e8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb0000e2\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafd71d1\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0036072c, 28)
extern "C" __attribute__((naked)) void engine_func_0036072c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4008\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xeb0000f7\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x1bfd71c1\n"
        ".inst 0xe1dd00d0\n"
        ".inst 0xe8bd8008\n"
    );
}

// DECOMP_FUNC(0x00360748, 28)
extern "C" __attribute__((naked)) void func_00360748() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb000100\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafd71b9\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00360764, 28)
extern "C" __attribute__((naked)) void func_00360764() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb000108\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafd71b2\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x003607c0, 28)
extern "C" __attribute__((naked)) void func_003607c0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb00010f\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafd719b\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x003607dc, 28)
extern "C" __attribute__((naked)) void nn_sdk_func_003607dc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb000117\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafd7194\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00360cbc, 28)
extern "C" __attribute__((naked)) void func_00360cbc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebffffee\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafd705c\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0037e7b0, 28)
extern "C" __attribute__((naked)) void func_0037e7b0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe3510002\n"
        ".inst 0xe1a04002\n"
        ".inst 0x0bfadd86\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840098\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0030f904, 32)
extern "C" __attribute__((naked)) void script_vm_func_0030f904() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0014\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xe2800040\n"
        ".inst 0xea023499\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0044cdf0 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00338638, 32)
extern "C" __attribute__((naked)) void func_00338638() {
    asm volatile(
        ".arm\n"
        ".inst 0xe2800901\n"
        ".inst 0xe5900394\n"
        ".inst 0xe3500000\n"
        ".inst 0x0d9f0a02\n"
        ".inst 0x0a000000\n"
        ".inst 0xeafd1d5a\n"
        ".inst 0xe12fff1e\n"
        ".word 0xbf800000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00355fc0, 32)
extern "C" __attribute__((naked)) void func_00355fc0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000\n"
        ".inst 0x059f0010\n"
        ".inst 0x0a000002\n"
        ".inst 0xe5901000\n"
        ".inst 0xe591100c\n"
        ".inst 0xe12fff11\n"
        ".inst 0xe12fff1e\n"
        ".word 0xe0e046bc @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003560bc, 32)
extern "C" __attribute__((naked)) void func_003560bc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500000\n"
        ".inst 0x059f0010\n"
        ".inst 0x0a000002\n"
        ".inst 0xe5902000\n"
        ".inst 0xe5922014\n"
        ".inst 0xe12fff12\n"
        ".inst 0xe12fff1e\n"
        ".word 0xe0e046bc @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0035b084, 32)
extern "C" __attribute__((naked)) void func_0035b084() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500004\n"
        ".inst 0x259f0010\n"
        ".inst 0x2a000002\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe1a00011\n"
        ".inst 0xeaffffca\n"
        ".inst 0xe12fff1e\n"
        ".word 0xd8e06bed @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0035b0a4, 32)
extern "C" __attribute__((naked)) void func_0035b0a4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3500004\n"
        ".inst 0x259f0010\n"
        ".inst 0x2a000002\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe1a00011\n"
        ".inst 0xeaf736e2\n"
        ".inst 0xe12fff1e\n"
        ".word 0xd8e06bed @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0038b618, 32)
extern "C" __attribute__((naked)) void func_0038b618() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebff5752\n"
        ".inst 0xebff576b\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a000001\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeaff576b\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0030ab70, 36)
extern "C" __attribute__((naked)) void camp_func_0030ab70() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0018\n"
        ".inst 0xe5900000\n"
        ".inst 0xe5d005c4\n"
        ".inst 0xe3500000\n"
        ".inst 0x13a00000\n"
        ".inst 0x1a000000\n"
        ".inst 0xeafe16c1\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043dd50 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0030f5ec, 36)
extern "C" __attribute__((naked)) void camp_func_0030f5ec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1018\n"
        ".inst 0xe5911000\n"
        ".inst 0xe3510000\n"
        ".inst 0x15d1103c\n"
        ".inst 0x13510000\n"
        ".inst 0x0a000000\n"
        ".inst 0xeafef270\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00447e28 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00357698, 36)
extern "C" __attribute__((naked)) void func_00357698() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5901008\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe59f0004\n"
        ".inst 0xeaf7f949\n"
        ".inst 0xe12fff1e\n"
        ".inst 0x004e6ef0\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00359184, 36)
extern "C" __attribute__((naked)) void func_00359184() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0014\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3500000\n"
        ".inst 0x059f000c\n"
        ".inst 0x0a000000\n"
        ".inst 0xeaf81968\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00473848 @ bounded tail data\n"
        ".word 0xe0810bf8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0035bb24, 36)
extern "C" __attribute__((naked)) void func_0035bb24() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1c021d0\n"
        ".inst 0xe2822001\n"
        ".inst 0xe1520003\n"
        ".inst 0xe5802010\n"
        ".inst 0x03a00006\n"
        ".inst 0x0a000001\n"
        ".inst 0xe3a02004\n"
        ".inst 0xea000140\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0035bb74, 36)
extern "C" __attribute__((naked)) void func_0035bb74() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1c021d0\n"
        ".inst 0xe2822001\n"
        ".inst 0xe1520003\n"
        ".inst 0xe5802010\n"
        ".inst 0x03a00006\n"
        ".inst 0x0a000001\n"
        ".inst 0xe3a02002\n"
        ".inst 0xea00012c\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0037a3fc, 36)
extern "C" __attribute__((naked)) void func_0037a3fc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04001\n"
        ".inst 0xeb000005\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a000002\n"
        ".inst 0xe284000c\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafd2482\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0039f834, 36)
extern "C" __attribute__((naked)) void script_vm_func_0039f834() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00b01\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfc84d9\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xe3a00076\n"
        ".inst 0xeafbce5d\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x003af184, 36)
extern "C" __attribute__((naked)) void func_003af184() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0018\n"
        ".inst 0xe5900020\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe2800a02\n"
        ".inst 0xe2800e46\n"
        ".inst 0xeafcb486\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00439c88 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e7038, 36)
extern "C" __attribute__((naked)) void func_003e7038() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5902004\n"
        ".inst 0xe3520000\n"
        ".inst 0x03a00000\n"
        ".inst 0x012fff1e\n"
        ".inst 0xe2800004\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb000028\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x003e7080, 36)
extern "C" __attribute__((naked)) void func_003e7080() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5903004\n"
        ".inst 0xe3530000\n"
        ".inst 0x03a00000\n"
        ".inst 0x012fff1e\n"
        ".inst 0xe2800004\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb000022\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x003e70a4, 36)
extern "C" __attribute__((naked)) void func_003e70a4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe590c004\n"
        ".inst 0xe35c0000\n"
        ".inst 0x03a00000\n"
        ".inst 0x012fff1e\n"
        ".inst 0xe2800004\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb000040\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00302674, 40)
extern "C" __attribute__((naked)) void engine_func_00302674() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900044\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe3500000\n"
        ".inst 0x1bfd5340\n"
        ".inst 0xe1a00005\n"
        ".inst 0xebfd1b23\n"
        ".inst 0xe5840044\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x003408c4, 40)
extern "C" __attribute__((naked)) void ui_func_003408c4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb01009f\n"
        ".inst 0xe59f1014\n"
        ".inst 0xe3a03008\n"
        ".inst 0xe3a02004\n"
        ".inst 0xe2800020\n"
        ".inst 0xfafe159d\n"
        ".inst 0xe2400020\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00376b78 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0034752c, 40)
extern "C" __attribute__((naked)) void ui_func_0034752c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb00e585\n"
        ".inst 0xe3a03004\n"
        ".inst 0xe59f1010\n"
        ".inst 0xe1a02003\n"
        ".inst 0xe2800020\n"
        ".inst 0xfafdfa83\n"
        ".inst 0xe2400020\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00376b78 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0034a1f0, 40)
extern "C" __attribute__((naked)) void func_0034a1f0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1018\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5801000\n"
        ".inst 0xebffffcc\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafda0c3\n"
        ".inst 0x00420514\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00357b2c, 40)
extern "C" __attribute__((naked)) void engine_func_00357b2c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe590c004\n"
        ".inst 0xe35c0000\n"
        ".inst 0x059f009c\n"
        ".inst 0x012fff1e\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000001\n"
        ".inst 0xe3520070\n"
        ".inst 0x2a000001\n"
        ".inst 0xe59f0088\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00360704, 40)
extern "C" __attribute__((naked)) void engine_func_00360704() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb0000ea\n"
        ".inst 0xe59f1014\n"
        ".inst 0xe1500001\n"
        ".inst 0x0a000002\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x1bfd71c9\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8010\n"
        ".word 0xc9405001 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0037024c, 40)
extern "C" __attribute__((naked)) void func_0037024c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4008\n"
        ".inst 0xe5b01008\n"
        ".inst 0xe3510000\n"
        ".inst 0x10800001\n"
        ".inst 0x03a00000\n"
        ".inst 0xe3500000\n"
        ".inst 0xe58d0000\n"
        ".inst 0x11a0000d\n"
        ".inst 0x1bfd4cbd\n"
        ".inst 0xe8bd8008\n"
    );
}

// DECOMP_FUNC(0x0037e3f8, 40)
extern "C" __attribute__((naked)) void func_0037e3f8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f1014\n"
        ".inst 0xe3a03002\n"
        ".inst 0xe3a0200c\n"
        ".inst 0xe2800064\n"
        ".inst 0xfafd2129\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00361c60 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003ade5c, 40)
extern "C" __attribute__((naked)) void func_003ade5c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe5900020\n"
        ".inst 0xe3500000\n"
        ".inst 0x03a00001\n"
        ".inst 0x0a000002\n"
        ".inst 0xe2800a02\n"
        ".inst 0xe2800e46\n"
        ".inst 0xeafb7a7a\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00439c88 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003d7200, 40)
extern "C" __attribute__((naked)) void engine_func_003d7200() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5902730\n"
        ".inst 0xe1a03001\n"
        ".inst 0xe3520000\n"
        ".inst 0x1a000004\n"
        ".inst 0xe2801b01\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe2811fcd\n"
        ".inst 0xe1a00003\n"
        ".inst 0xeafb0137\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x003d9fa0, 40)
extern "C" __attribute__((naked)) void engine_func_003d9fa0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00044\n"
        ".inst 0xebfba111\n"
        ".inst 0xe3500000\n"
        ".inst 0x1bfdc122\n"
        ".inst 0xe2844b07\n"
        ".inst 0xe28440f8\n"
        ".inst 0xe5840000\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x003e72fc, 40)
extern "C" __attribute__((naked)) void func_003e72fc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5900004\n"
        ".inst 0xe1a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe590003c\n"
        ".inst 0xebfafe91\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafffe01\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0033534c, 44)
extern "C" __attribute__((naked)) void ui_func_0033534c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5900008\n"
        ".inst 0xe5900008\n"
        ".inst 0xeafb6ac8\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a02007\n"
        ".inst 0xe5801000\n"
        ".inst 0xe1c020b4\n"
        ".inst 0xe5801008\n"
        ".inst 0xe580100c\n"
        ".inst 0xe5c01010\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x003489e8, 44)
extern "C" __attribute__((naked)) void func_003489e8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe59f2014\n"
        ".inst 0xe59f1014\n"
        ".inst 0xe3a03002\n"
        ".inst 0xe2800004\n"
        ".inst 0xfafdf7ad\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00000544 @ bounded tail data\n"
        ".word 0x0033b7f0 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0034f61c, 44)
extern "C" __attribute__((naked)) void func_0034f61c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe0800101\n"
        ".inst 0xe5900010\n"
        ".inst 0xe12fff1e\n"
        ".inst 0xe0802101\n"
        ".inst 0xe5922010\n"
        ".inst 0xe3520000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe0800281\n"
        ".inst 0xe2800040\n"
        ".inst 0xeafffa54\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00354ef0, 44)
extern "C" __attribute__((naked)) void engine_func_00354ef0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4008\n"
        ".inst 0xe1a03002\n"
        ".inst 0xe1a02001\n"
        ".inst 0xe2800004\n"
        ".inst 0xe1a0100d\n"
        ".inst 0xebfd9a3e\n"
        ".inst 0xe1a0100f\n"
        ".inst 0xe1b02fa0\n"
        ".inst 0x1bfd9b7e\n"
        ".inst 0xe59d0000\n"
        ".inst 0xe8bd8008\n"
    );
}

// DECOMP_FUNC(0x00354f1c, 44)
extern "C" __attribute__((naked)) void func_00354f1c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4008\n"
        ".inst 0xe2800004\n"
        ".inst 0xe59d1008\n"
        ".inst 0xe58d1000\n"
        ".inst 0xebfd5eb8\n"
        ".inst 0xe1a0100f\n"
        ".inst 0xe1b02fa0\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4008\n"
        ".inst 0xeafd9b72\n"
        ".inst 0xe8bd8008\n"
    );
}

// DECOMP_FUNC(0x0035f9ec, 44)
extern "C" __attribute__((naked)) void func_0035f9ec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfb6036\n"
        ".inst 0xe3500000\n"
        ".inst 0x059f0010\n"
        ".inst 0x0a000002\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xea000079\n"
        ".inst 0xe8bd8010\n"
        ".word 0xc8a0d018 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0035fa18, 44)
extern "C" __attribute__((naked)) void func_0035fa18() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfb602b\n"
        ".inst 0xe3500000\n"
        ".inst 0x059f0010\n"
        ".inst 0x0a000002\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xea00013c\n"
        ".inst 0xe8bd8010\n"
        ".word 0xc8a0d018 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00370220, 44)
extern "C" __attribute__((naked)) void func_00370220() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe92d4008\n"
        ".inst 0xe580102c\n"
        ".inst 0xe5b02008\n"
        ".inst 0xe3520000\n"
        ".inst 0x10821000\n"
        ".inst 0xe3510000\n"
        ".inst 0x11a0000d\n"
        ".inst 0xe58d1000\n"
        ".inst 0x1bfd4cc7\n"
        ".inst 0xe8bd8008\n"
    );
}

// DECOMP_FUNC(0x00376b20, 44)
extern "C" __attribute__((naked)) void func_00376b20() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5801000\n"
        ".inst 0xe1a00001\n"
        ".inst 0xeb000c27\n"
        ".inst 0xe3500000\n"
        ".inst 0x15940000\n"
        ".inst 0x1bfd1c20\n"
        ".inst 0xe5940000\n"
        ".inst 0xe5804008\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0037bc48, 44)
extern "C" __attribute__((naked)) void func_0037bc48() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5d01261\n"
        ".inst 0xe3510000\n"
        ".inst 0x1a000006\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe5c02260\n"
        ".inst 0xe5c01261\n"
        ".inst 0xe1a01002\n"
        ".inst 0xe280000c\n"
        ".inst 0xeafffeec\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0039493c, 44)
extern "C" __attribute__((naked)) void engine_func_0039493c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfcc3bc\n"
        ".inst 0xe3500000\n"
        ".inst 0x13a00001\n"
        ".inst 0x1a000002\n"
        ".inst 0xe59f0008\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafd0596\n"
        ".inst 0xe8bd8010\n"
        ".word 0x06000001 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003a6614, 44)
extern "C" __attribute__((naked)) void engine_func_003a6614() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f2020\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe5921004\n"
        ".inst 0xe2411001\n"
        ".inst 0xe3510000\n"
        ".inst 0xe5821004\n"
        ".inst 0xca000001\n"
        ".inst 0xe3a00017\n"
        ".inst 0xeafbf8d0\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0044e068 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e0dbc, 44)
extern "C" __attribute__((naked)) void engine_func_003e0dbc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a03000\n"
        ".inst 0xe1b00001\n"
        ".inst 0xe92d4010\n"
        ".inst 0x0a000005\n"
        ".inst 0xe3a02008\n"
        ".inst 0xe1a01003\n"
        ".inst 0xfafb831b\n"
        ".inst 0xe3500000\n"
        ".inst 0x03a00001\n"
        ".inst 0x13a00000\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x003619cc, 48)
extern "C" __attribute__((naked)) void func_003619cc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f0020\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfd19ed\n"
        ".inst 0xe1b01fa0\n"
        ".inst 0x159f1014\n"
        ".inst 0x11500001\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafd6d15\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00000401 @ bounded tail data\n"
        ".word 0xc8a0cffc @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00361b7c, 48)
extern "C" __attribute__((naked)) void script_vm_func_00361b7c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfd7de4\n"
        ".inst 0xe1b01fa0\n"
        ".inst 0x159f1010\n"
        ".inst 0x11500001\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafd6ca8\n"
        ".inst 0xe8bd8010\n"
        ".word 0xc8a0cffc @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00384dc8, 48)
extern "C" __attribute__((naked)) void ui_func_00384dc8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5900004\n"
        ".inst 0xe3500002\n"
        ".inst 0xda000005\n"
        ".inst 0xe59f4014\n"
        ".inst 0xe5940000\n"
        ".inst 0xebfcf35f\n"
        ".inst 0xe5940000\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafcf332\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0044ea00 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00394c6c, 48)
extern "C" __attribute__((naked)) void battle_func_00394c6c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfcc2f0\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a000005\n"
        ".inst 0xe3a00002\n"
        ".inst 0xebfcb4c6\n"
        ".inst 0xe3a00002\n"
        ".inst 0xebfd31f7\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeaf9ab72\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x003a65e4, 48)
extern "C" __attribute__((naked)) void camp_func_003a65e4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f4020\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe5941004\n"
        ".inst 0xe3510000\n"
        ".inst 0xd3a00017\n"
        ".inst 0xdbfbc42a\n"
        ".inst 0xe5941004\n"
        ".inst 0xe2811001\n"
        ".inst 0xe5841004\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0044e068 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003ca154, 48)
extern "C" __attribute__((naked)) void engine_func_003ca154() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe3a04000\n"
        ".inst 0xe0850104\n"
        ".inst 0xe5900038\n"
        ".inst 0xe3500000\n"
        ".inst 0x1bfbe87b\n"
        ".inst 0xe2844001\n"
        ".inst 0xe3540038\n"
        ".inst 0xbafffff8\n"
        ".inst 0xe1a00005\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x003df0d8, 48)
extern "C" __attribute__((naked)) void func_003df0d8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5900010\n"
        ".inst 0xe3500000\n"
        ".inst 0x0d9f0a06\n"
        ".inst 0x0a000004\n"
        ".inst 0xe1d001b0\n"
        ".inst 0xe59f1010\n"
        ".inst 0xe7d10000\n"
        ".inst 0xee000a10\n"
        ".inst 0xeeb80a40\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000 @ bounded tail data\n"
        ".word 0x003ff7c8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0031124c, 52)
extern "C" __attribute__((naked)) void func_0031124c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1028\n"
        ".inst 0xe5911000\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000006\n"
        ".inst 0xe3500000\n"
        ".inst 0xe3a01001\n"
        ".inst 0x0a000001\n"
        ".inst 0xe3a00008\n"
        ".inst 0xeafe08de\n"
        ".inst 0xe3a00016\n"
        ".inst 0xeafe08dc\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0043dcf0 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003a07d0, 52)
extern "C" __attribute__((naked)) void func_003a07d0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfa5006\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafc474f\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe1d000b0\n"
        ".inst 0xe1d130b0\n"
        ".inst 0xe0500003\n"
        ".inst 0x1a000002\n"
        ".inst 0xe1d200b2\n"
        ".inst 0xe1d110b2\n"
        ".inst 0xe0400001\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00339a5c, 56)
extern "C" __attribute__((naked)) void script_vm_func_00339a5c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe2804901\n"
        ".inst 0xe5940398\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe5901008\n"
        ".inst 0xe591100c\n"
        ".inst 0xe3510000\n"
        ".inst 0xabf8641d\n"
        ".inst 0xe5940398\n"
        ".inst 0xebfdb805\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840398\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0035a238, 56)
extern "C" __attribute__((naked)) void camp_func_0035a238() {
    asm volatile(
        ".arm\n"
        ".inst 0xe52de004\n"
        ".inst 0xe24dd0c4\n"
        ".inst 0xe3a02703\n"
        ".inst 0xe3a010c0\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xebf77e23\n"
        ".inst 0xe1a0100f\n"
        ".inst 0xe1b02fa0\n"
        ".inst 0x1bfd86ac\n"
        ".inst 0xe59d0000\n"
        ".inst 0xe28dd0c4\n"
        ".inst 0xe2000020\n"
        ".inst 0xe1a002a0\n"
        ".inst 0xe49df004\n"
    );
}

// DECOMP_FUNC(0x00368cc0, 56)
extern "C" __attribute__((naked)) void func_00368cc0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3a02004\n"
        ".inst 0xe3a01008\n"
        ".inst 0xe5903008\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe12fff33\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xe59f1004\n"
        ".inst 0xe8800012\n"
        ".inst 0xe8bd8010\n"
        ".word 0x004210ec @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0036c070, 56)
extern "C" __attribute__((naked)) void func_0036c070() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3a02004\n"
        ".inst 0xe3a01008\n"
        ".inst 0xe5903008\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe12fff33\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xe59f1004\n"
        ".inst 0xe8800012\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0042122c @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00376b4c, 56)
extern "C" __attribute__((naked)) void func_00376b4c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5801000\n"
        ".inst 0xe1a00001\n"
        ".inst 0xeb000c2c\n"
        ".inst 0xe3500000\n"
        ".inst 0x15940000\n"
        ".inst 0x1b000c17\n"
        ".inst 0xe5940000\n"
        ".inst 0xe580400c\n"
        ".inst 0xe8bd8010\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5801000\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00337558, 60)
extern "C" __attribute__((naked)) void func_00337558() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1030\n"
        ".inst 0xe7911000\n"
        ".inst 0xe3110040\n"
        ".inst 0x13a00000\n"
        ".inst 0x1a000007\n"
        ".inst 0xe2800b11\n"
        ".inst 0xe28000a8\n"
        ".inst 0xe5900000\n"
        ".inst 0xe3100802\n"
        ".inst 0x13a00001\n"
        ".inst 0x1a000001\n"
        ".inst 0xe3a00010\n"
        ".inst 0xeafd6f0f\n"
        ".inst 0xe12fff1e\n"
        ".word 0x000044a0 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00338988, 60)
extern "C" __attribute__((naked)) void ui_func_00338988() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe2804901\n"
        ".inst 0xe5940394\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000008\n"
        ".inst 0xebfd3ffb\n"
        ".inst 0xe5940394\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe5901000\n"
        ".inst 0xe5911004\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840394\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00359088, 60)
extern "C" __attribute__((naked)) void func_00359088() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1028\n"
        ".inst 0xe5911000\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000000\n"
        ".inst 0xea0001c7\n"
        ".inst 0xe59f1018\n"
        ".inst 0xe5911000\n"
        ".inst 0xe3510000\n"
        ".inst 0x059f0010\n"
        ".inst 0x0a000000\n"
        ".inst 0xea0000a3\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0047384c @ bounded tail data\n"
        ".word 0x00473848 @ bounded tail data\n"
        ".word 0xe0810bf8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003591e4, 60)
extern "C" __attribute__((naked)) void nn_sdk_func_003591e4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfda0e0\n"
        ".inst 0xe1b01fa0\n"
        ".inst 0x1a000007\n"
        ".inst 0xe59f001c\n"
        ".inst 0xebfda824\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe59f1010\n"
        ".inst 0xe59f0010\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xe3a03000\n"
        ".inst 0xeafda0c9\n"
        ".inst 0xe8bd8010\n"
        ".word 0x004103aa @ bounded tail data\n"
        ".word 0x00473848 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00359288, 60)
extern "C" __attribute__((naked)) void func_00359288() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1028\n"
        ".inst 0xe5911000\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000000\n"
        ".inst 0xea0001a8\n"
        ".inst 0xe59f1018\n"
        ".inst 0xe5911000\n"
        ".inst 0xe3510000\n"
        ".inst 0x059f0010\n"
        ".inst 0x0a000000\n"
        ".inst 0xea000084\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0047384c @ bounded tail data\n"
        ".word 0x00473848 @ bounded tail data\n"
        ".word 0xe0810bf8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003596c4, 60)
extern "C" __attribute__((naked)) void func_003596c4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59fc028\n"
        ".inst 0xe59cc000\n"
        ".inst 0xe35c0000\n"
        ".inst 0x0a000000\n"
        ".inst 0xea0000a8\n"
        ".inst 0xe59fc018\n"
        ".inst 0xe59cc000\n"
        ".inst 0xe35c0000\n"
        ".inst 0x059f0010\n"
        ".inst 0x0a000000\n"
        ".inst 0xeaffff84\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0047384c @ bounded tail data\n"
        ".word 0x00473848 @ bounded tail data\n"
        ".word 0xe0810bf8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00359700, 60)
extern "C" __attribute__((naked)) void func_00359700() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1028\n"
        ".inst 0xe5911000\n"
        ".inst 0xe3510000\n"
        ".inst 0x0a000000\n"
        ".inst 0xea0000bb\n"
        ".inst 0xe59f1018\n"
        ".inst 0xe5911000\n"
        ".inst 0xe3510000\n"
        ".inst 0x059f0010\n"
        ".inst 0x0a000000\n"
        ".inst 0xeaffff97\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0047384c @ bounded tail data\n"
        ".word 0x00473848 @ bounded tail data\n"
        ".word 0xe0810bf8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00359b94, 60)
extern "C" __attribute__((naked)) void func_00359b94() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59fc028\n"
        ".inst 0xe59cc000\n"
        ".inst 0xe35c0000\n"
        ".inst 0x0a000000\n"
        ".inst 0xeaffffbb\n"
        ".inst 0xe59fc018\n"
        ".inst 0xe59cc000\n"
        ".inst 0xe35c0000\n"
        ".inst 0x059f0010\n"
        ".inst 0x0a000000\n"
        ".inst 0xeafffe97\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0047384c @ bounded tail data\n"
        ".word 0x00473848 @ bounded tail data\n"
        ".word 0xe0810bf8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003604c0, 60)
extern "C" __attribute__((naked)) void func_003604c0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a0c000\n"
        ".inst 0xe59f002c\n"
        ".inst 0xe92d4008\n"
        ".inst 0xe5900000\n"
        ".inst 0xe58d3000\n"
        ".inst 0xe1a03002\n"
        ".inst 0xe1a02001\n"
        ".inst 0xe1a0100c\n"
        ".inst 0xeb0000d3\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4008\n"
        ".inst 0xeafd7254\n"
        ".inst 0xe8bd8008\n"
        ".word 0x0040b6f0 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003604fc, 60)
extern "C" __attribute__((naked)) void func_003604fc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a0c000\n"
        ".inst 0xe59f002c\n"
        ".inst 0xe92d4008\n"
        ".inst 0xe5900000\n"
        ".inst 0xe58d3000\n"
        ".inst 0xe1a03002\n"
        ".inst 0xe1a02001\n"
        ".inst 0xe1a0100c\n"
        ".inst 0xeb0000db\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4008\n"
        ".inst 0xeafd7245\n"
        ".inst 0xe8bd8008\n"
        ".word 0x0040b6f0 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00360538, 60)
extern "C" __attribute__((naked)) void func_00360538() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a0c000\n"
        ".inst 0xe59f002c\n"
        ".inst 0xe92d4008\n"
        ".inst 0xe5900000\n"
        ".inst 0xe58d3000\n"
        ".inst 0xe1a03002\n"
        ".inst 0xe1a02001\n"
        ".inst 0xe1a0100c\n"
        ".inst 0xeb0000e3\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4008\n"
        ".inst 0xeafd7236\n"
        ".inst 0xe8bd8008\n"
        ".word 0x0040b6f0 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00360574, 60)
extern "C" __attribute__((naked)) void engine_func_00360574() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe59f4028\n"
        ".inst 0xe5d40000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000006\n"
        ".inst 0xeb000113\n"
        ".inst 0xe5950000\n"
        ".inst 0xef000023\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x1bfd7229\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5c40000\n"
        ".inst 0xe8bd8070\n"
        ".word 0x00471ba8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003605b0, 60)
extern "C" __attribute__((naked)) void func_003605b0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe1a0c000\n"
        ".inst 0xe59f002c\n"
        ".inst 0xe92d4008\n"
        ".inst 0xe5900000\n"
        ".inst 0xe58d3000\n"
        ".inst 0xe1a03002\n"
        ".inst 0xe1a02001\n"
        ".inst 0xe1a0100c\n"
        ".inst 0xeb0000dc\n"
        ".inst 0xe1b00fa0\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4008\n"
        ".inst 0xeafd7218\n"
        ".inst 0xe8bd8008\n"
        ".word 0x0040b6f0 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0037e7f8, 60)
extern "C" __attribute__((naked)) void func_0037e7f8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5c0100e\n"
        ".inst 0xe5900098\n"
        ".inst 0xe3500000\n"
        ".inst 0x15d020c6\n"
        ".inst 0x13520000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe5d020c5\n"
        ".inst 0xe3520000\n"
        ".inst 0x13a02001\n"
        ".inst 0xe1520001\n"
        ".inst 0x0a000002\n"
        ".inst 0xe5c010c5\n"
        ".inst 0xe5900134\n"
        ".inst 0xeafadd62\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x0037fc8c, 60)
extern "C" __attribute__((naked)) void func_0037fc8c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe1b04001\n"
        ".inst 0xe2805008\n"
        ".inst 0xe58120c0\n"
        ".inst 0x0a000007\n"
        ".inst 0xe5940000\n"
        ".inst 0xe5901000\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe1a01004\n"
        ".inst 0xe1a00005\n"
        ".inst 0xe8bd4070\n"
        ".inst 0xeafc8dd8\n"
        ".inst 0xe8bd8070\n"
    );
}
