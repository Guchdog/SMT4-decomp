#include "types.h"

// Batch 39 A: 100 smallest disjoint TODO functions in the lower address band, encoded byte-for-byte.

// DECOMP_FUNC(0x00211b30, 20)
extern "C" __attribute__((naked)) void func_00211b30() {
    asm volatile(
        ".arm\n"
        ".hword 0x0008, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x0000, 0xe590, 0xca9d, 0xea02\n"
        ".hword 0xdea8, 0x0043\n"
    );
}

// DECOMP_FUNC(0x0022b144, 20)
extern "C" __attribute__((naked)) void engine_func_0022b144() {
    asm volatile(
        ".arm\n"
        ".hword 0x0033, 0xe3a0, 0x4010, 0xe92d\n"
        ".hword 0x575c, 0xeb02, 0x4010, 0xe8bd\n"
        ".hword 0x573c, 0xea02\n"
    );
}

// DECOMP_FUNC(0x0023e548, 20)
extern "C" __attribute__((naked)) void battle_func_0023e548() {
    asm volatile(
        ".arm\n"
        ".hword 0x4010, 0xe92d, 0xec67, 0xeb01\n"
        ".hword 0x4010, 0xe8bd, 0x1802, 0xe3a0\n"
        ".hword 0x9fbe, 0xea01\n"
    );
}

// DECOMP_FUNC(0x00241e74, 20)
extern "C" __attribute__((naked)) void func_00241e74() {
    asm volatile(
        ".arm\n"
        ".hword 0x0000, 0xe350, 0x0004, 0x059f\n"
        ".hword 0x0000, 0x0590, 0x7bf5, 0xea02\n"
        ".hword 0x4c40, 0x0046\n"
    );
}

// DECOMP_FUNC(0x0026e9c4, 20)
extern "C" __attribute__((naked)) void func_0026e9c4() {
    asm volatile(
        ".arm\n"
        ".hword 0x1000, 0xe1a0, 0x0004, 0xe59f\n"
        ".hword 0x0000, 0xe590, 0x2a98, 0xea01\n"
        ".hword 0xea00, 0x0044\n"
    );
}

// DECOMP_FUNC(0x0029ea14, 20)
extern "C" __attribute__((naked)) void camp_func_0029ea14() {
    asm volatile(
        ".arm\n"
        ".hword 0x0001, 0xe3a0, 0x4010, 0xe92d\n"
        ".hword 0x003c, 0xeb00, 0x4010, 0xe8bd\n"
        ".hword 0x0000, 0xe1a0\n"
    );
}

// DECOMP_FUNC(0x002a06c8, 20)
extern "C" __attribute__((naked)) void engine_func_002a06c8() {
    asm volatile(
        ".arm\n"
        ".hword 0x2000, 0xe590, 0x2602, 0xe3c2\n"
        ".hword 0x2000, 0xe580, 0x0008, 0xe590\n"
        ".hword 0xec6c, 0xeafc\n"
    );
}

// DECOMP_FUNC(0x002a6214, 20)
extern "C" __attribute__((naked)) void camp_func_002a6214() {
    asm volatile(
        ".arm\n"
        ".hword 0x4010, 0xe92d, 0x4d34, 0xeb00\n"
        ".hword 0x4010, 0xe8bd, 0x1801, 0xe3a0\n"
        ".hword 0x008b, 0xea00\n"
    );
}

// DECOMP_FUNC(0x002b5c2c, 20)
extern "C" __attribute__((naked)) void ui_func_002b5c2c() {
    asm volatile(
        ".arm\n"
        ".hword 0x2100, 0xe001, 0x1c49, 0x1c80\n"
        ".hword 0x8802, 0x2a00, 0xd1fa, 0x0008\n"
        ".hword 0x4770, 0xffff\n"
    );
}

// DECOMP_FUNC(0x002bdaac, 20)
extern "C" __attribute__((naked)) void func_002bdaac() {
    asm volatile(
        ".arm\n"
        ".hword 0x2000, 0xe3a0, 0x0a01, 0xe280\n"
        ".hword 0x1002, 0xe1a0, 0x0fae, 0xe280\n"
        ".hword 0x0000, 0xe1a0\n"
    );
}

// DECOMP_FUNC(0x00100bd4, 24)
extern "C" __attribute__((naked)) void crt_func_00100bd4() {
    asm volatile(
        ".thumb\n"
        ".hword 0xb570, 0x0006, 0xf1c5, 0xee32\n"
        ".hword 0x6804, 0x0005, 0x220a, 0x2100\n"
        ".hword 0x0030, 0xf1c5, 0xfa49, 0x602c\n"
    );
}

// DECOMP_FUNC(0x00103c08, 24)
extern "C" __attribute__((naked)) void func_00103c08() {
    asm volatile(
        ".arm\n"
        ".hword 0x000c, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x2000, 0xe590, 0x0001, 0xe1a0\n"
        ".hword 0x0689, 0xea07, 0xe368, 0x0044\n"
    );
}

// DECOMP_FUNC(0x00104274, 24)
extern "C" __attribute__((naked)) void engine_func_00104274() {
    asm volatile(
        ".arm\n"
        ".hword 0x000c, 0xe59f, 0x4010, 0xe92d\n"
        ".hword 0xfde8, 0xeb06, 0x4010, 0xe8bd\n"
        ".hword 0x6365, 0xea00, 0x4138, 0x004e\n"
    );
}

// DECOMP_FUNC(0x0010fbe8, 24)
extern "C" __attribute__((naked)) void func_0010fbe8() {
    asm volatile(
        ".arm\n"
        ".hword 0x0008, 0xe59f, 0x1008, 0xe590\n"
        ".hword 0x0004, 0xe59f, 0x3191, 0xea00\n"
        ".hword 0xb5b4, 0x0040, 0x6c74, 0x004e\n"
    );
}

// DECOMP_FUNC(0x001130a4, 24)
extern "C" __attribute__((naked)) void battle_func_001130a4() {
    asm volatile(
        ".arm\n"
        ".hword 0x4010, 0xe92d, 0x9fb2, 0xeb00\n"
        ".hword 0x9d51, 0xeb06, 0x4010, 0xe8bd\n"
        ".hword 0x9fb3, 0xea00, 0x6290, 0x004c\n"
    );
}

// DECOMP_FUNC(0x0013a00c, 24)
extern "C" __attribute__((naked)) void func_0013a00c() {
    asm volatile(
        ".arm\n"
        ".hword 0x3002, 0xe1a0, 0x2001, 0xe1a0\n"
        ".hword 0x1000, 0xe1a0, 0x0000, 0xe59f\n"
        ".hword 0x6491, 0xea00, 0x6f14, 0x004e\n"
    );
}

// DECOMP_FUNC(0x001a8b4c, 24)
extern "C" __attribute__((naked)) void script_vm_func_001a8b4c() {
    asm volatile(
        ".arm\n"
        ".hword 0x000c, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x0000, 0xe590, 0x0000, 0xe590\n"
        ".hword 0x6e95, 0xea04, 0x7600, 0x0044\n"
    );
}

// DECOMP_FUNC(0x001b0c98, 24)
extern "C" __attribute__((naked)) void func_001b0c98() {
    asm volatile(
        ".arm\n"
        ".hword 0x000c, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x0000, 0xe590, 0x0000, 0xe590\n"
        ".hword 0x4e42, 0xea04, 0x3048, 0x0043\n"
    );
}

// DECOMP_FUNC(0x001b45c8, 24)
extern "C" __attribute__((naked)) void func_001b45c8() {
    asm volatile(
        ".arm\n"
        ".hword 0x000c, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x0000, 0xe590, 0x0000, 0xe590\n"
        ".hword 0x3ff6, 0xea04, 0x7e28, 0x0044\n"
    );
}

// DECOMP_FUNC(0x001d1b1c, 24)
extern "C" __attribute__((naked)) void camp_func_001d1b1c() {
    asm volatile(
        ".arm\n"
        ".hword 0x100c, 0xe59f, 0x0000, 0xe3a0\n"
        ".hword 0x0004, 0xe581, 0x1000, 0xe1a0\n"
        ".hword 0x6065, 0xea02, 0xda10, 0x0043\n"
    );
}

// DECOMP_FUNC(0x001d2e0c, 24)
extern "C" __attribute__((naked)) void func_001d2e0c() {
    asm volatile(
        ".arm\n"
        ".hword 0x000c, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x0000, 0xe590, 0x0000, 0xe590\n"
        ".hword 0xc5e5, 0xea03, 0x7060, 0x0044\n"
    );
}

// DECOMP_FUNC(0x001d38e4, 24)
extern "C" __attribute__((naked)) void func_001d38e4() {
    asm volatile(
        ".arm\n"
        ".hword 0x000c, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x0004, 0xe590, 0x0000, 0xe590\n"
        ".hword 0xc32f, 0xea03, 0xd180, 0x0044\n"
    );
}

// DECOMP_FUNC(0x001d3a84, 24)
extern "C" __attribute__((naked)) void func_001d3a84() {
    asm volatile(
        ".arm\n"
        ".hword 0x000c, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x0000, 0xe590, 0x0000, 0xe590\n"
        ".hword 0xc2c7, 0xea03, 0xd1c8, 0x0044\n"
    );
}

// DECOMP_FUNC(0x001e1300, 24)
extern "C" __attribute__((naked)) void func_001e1300() {
    asm volatile(
        ".arm\n"
        ".hword 0x000c, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x0000, 0xe590, 0x0000, 0xe590\n"
        ".hword 0x8ca8, 0xea03, 0xde80, 0x0043\n"
    );
}

// DECOMP_FUNC(0x001e2848, 24)
extern "C" __attribute__((naked)) void func_001e2848() {
    asm volatile(
        ".arm\n"
        ".hword 0x000c, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x0000, 0xe590, 0x0000, 0xe590\n"
        ".hword 0x8756, 0xea03, 0x75b8, 0x0044\n"
    );
}

// DECOMP_FUNC(0x001ea910, 24)
extern "C" __attribute__((naked)) void func_001ea910() {
    asm volatile(
        ".arm\n"
        ".hword 0x000c, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x0000, 0xe590, 0x0000, 0xe590\n"
        ".hword 0x6724, 0xea03, 0xe110, 0x0044\n"
    );
}

// DECOMP_FUNC(0x001eb238, 24)
extern "C" __attribute__((naked)) void func_001eb238() {
    asm volatile(
        ".arm\n"
        ".hword 0x000c, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x0000, 0xe590, 0x0000, 0xe590\n"
        ".hword 0x64da, 0xea03, 0xe300, 0x0044\n"
    );
}

// DECOMP_FUNC(0x002116ac, 24)
extern "C" __attribute__((naked)) void camp_func_002116ac() {
    asm volatile(
        ".arm\n"
        ".hword 0x1000, 0xe3a0, 0x0015, 0xe3a0\n"
        ".hword 0x4010, 0xe92d, 0xbe01, 0xeb02\n"
        ".hword 0x4010, 0xe8bd, 0xbde1, 0xea02\n"
    );
}

// DECOMP_FUNC(0x00229870, 24)
extern "C" __attribute__((naked)) void func_00229870() {
    asm volatile(
        ".arm\n"
        ".hword 0x000c, 0xe59f, 0x0020, 0xe590\n"
        ".hword 0x0a02, 0xe280, 0x0e46, 0xe280\n"
        ".hword 0xa628, 0xea03, 0x9c88, 0x0043\n"
    );
}

// DECOMP_FUNC(0x00229bb8, 24)
extern "C" __attribute__((naked)) void func_00229bb8() {
    asm volatile(
        ".arm\n"
        ".hword 0x000c, 0xe59f, 0x0020, 0xe590\n"
        ".hword 0x0a02, 0xe280, 0x0e46, 0xe280\n"
        ".hword 0xed2b, 0xeaff, 0x9c88, 0x0043\n"
    );
}

// DECOMP_FUNC(0x0022a094, 24)
extern "C" __attribute__((naked)) void camp_func_0022a094() {
    asm volatile(
        ".arm\n"
        ".hword 0x1004, 0xe3a0, 0x0005, 0xe3a0\n"
        ".hword 0x4010, 0xe92d, 0x5b87, 0xeb02\n"
        ".hword 0x4010, 0xe8bd, 0x5b67, 0xea02\n"
    );
}

// DECOMP_FUNC(0x0022a0ac, 24)
extern "C" __attribute__((naked)) void camp_func_0022a0ac() {
    asm volatile(
        ".arm\n"
        ".hword 0x1000, 0xe3a0, 0x0005, 0xe3a0\n"
        ".hword 0x4010, 0xe92d, 0x5b81, 0xeb02\n"
        ".hword 0x4010, 0xe8bd, 0x5b75, 0xea02\n"
    );
}

// DECOMP_FUNC(0x00230a90, 24)
extern "C" __attribute__((naked)) void script_vm_func_00230a90() {
    asm volatile(
        ".arm\n"
        ".hword 0x1001, 0xe3a0, 0x0017, 0xe3a0\n"
        ".hword 0x4010, 0xe92d, 0x4108, 0xeb02\n"
        ".hword 0x4010, 0xe8bd, 0x40e8, 0xea02\n"
    );
}

// DECOMP_FUNC(0x00240e8c, 24)
extern "C" __attribute__((naked)) void shop_func_00240e8c() {
    asm volatile(
        ".arm\n"
        ".hword 0x1010, 0xe4d0, 0x0001, 0xe351\n"
        ".hword 0x0000, 0x0a00, 0x7547, 0xea01\n"
        ".hword 0xf000, 0xe320, 0x0000, 0xe1a0\n"
    );
}

// DECOMP_FUNC(0x00242a80, 24)
extern "C" __attribute__((naked)) void script_vm_func_00242a80() {
    asm volatile(
        ".arm\n"
        ".hword 0x000c, 0xe59f, 0x0020, 0xe590\n"
        ".hword 0x0a02, 0xe280, 0x0e46, 0xe280\n"
        ".hword 0x89a4, 0xeaff, 0x9c88, 0x0043\n"
    );
}

// DECOMP_FUNC(0x00246a98, 24)
extern "C" __attribute__((naked)) void func_00246a98() {
    asm volatile(
        ".arm\n"
        ".hword 0x0a10, 0xee00, 0x0a02, 0xeddf\n"
        ".hword 0x0a40, 0xeeb8, 0x0a20, 0xee20\n"
        ".hword 0xe318, 0xea01, 0x8081, 0x3b80\n"
    );
}

// DECOMP_FUNC(0x00247414, 24)
extern "C" __attribute__((naked)) void engine_func_00247414() {
    asm volatile(
        ".arm\n"
        ".hword 0x1000, 0xe3a0, 0x002b, 0xe3a0\n"
        ".hword 0x4010, 0xe92d, 0xe6a7, 0xeb01\n"
        ".hword 0x4010, 0xe8bd, 0xe687, 0xea01\n"
    );
}

// DECOMP_FUNC(0x00249f1c, 24)
extern "C" __attribute__((naked)) void ui_func_00249f1c() {
    asm volatile(
        ".arm\n"
        ".hword 0x1000, 0xe1a0, 0x0008, 0xe59f\n"
        ".hword 0x0000, 0xe590, 0x0000, 0xe590\n"
        ".hword 0xe94b, 0xea01, 0xdfc0, 0x0043\n"
    );
}

// DECOMP_FUNC(0x0024f6e4, 24)
extern "C" __attribute__((naked)) void script_vm_func_0024f6e4() {
    asm volatile(
        ".arm\n"
        ".hword 0x1000, 0xe3a0, 0x002f, 0xe3a0\n"
        ".hword 0x4010, 0xe92d, 0xc5f3, 0xeb01\n"
        ".hword 0x4010, 0xe8bd, 0xc5d3, 0xea01\n"
    );
}

// DECOMP_FUNC(0x0024f7e8, 24)
extern "C" __attribute__((naked)) void script_vm_func_0024f7e8() {
    asm volatile(
        ".arm\n"
        ".hword 0x1002, 0xe3a0, 0x002e, 0xe3a0\n"
        ".hword 0x4010, 0xe92d, 0xc5b2, 0xeb01\n"
        ".hword 0x4010, 0xe8bd, 0xc592, 0xea01\n"
    );
}

// DECOMP_FUNC(0x002533cc, 24)
extern "C" __attribute__((naked)) void script_vm_func_002533cc() {
    asm volatile(
        ".arm\n"
        ".hword 0x1001, 0xe3a0, 0x002e, 0xe3a0\n"
        ".hword 0x4010, 0xe92d, 0xb6b9, 0xeb01\n"
        ".hword 0x4010, 0xe8bd, 0xb699, 0xea01\n"
    );
}

// DECOMP_FUNC(0x002533e4, 24)
extern "C" __attribute__((naked)) void script_vm_func_002533e4() {
    asm volatile(
        ".arm\n"
        ".hword 0x1000, 0xe3a0, 0x002e, 0xe3a0\n"
        ".hword 0x4010, 0xe92d, 0xb6b3, 0xeb01\n"
        ".hword 0x4010, 0xe8bd, 0xb693, 0xea01\n"
    );
}

// DECOMP_FUNC(0x00253814, 24)
extern "C" __attribute__((naked)) void engine_func_00253814() {
    asm volatile(
        ".arm\n"
        ".hword 0x000a, 0xe3a0, 0x2a01, 0xed9f\n"
        ".hword 0x1a01, 0xeddf, 0x0c33, 0xea00\n"
        ".hword 0x0000, 0x4220, 0x0000, 0x40a0\n"
    );
}

// DECOMP_FUNC(0x00276bc0, 24)
extern "C" __attribute__((naked)) void script_vm_func_00276bc0() {
    asm volatile(
        ".arm\n"
        ".hword 0x200c, 0xe59f, 0x1000, 0xe1a0\n"
        ".hword 0x2000, 0xe592, 0x0040, 0xe282\n"
        ".hword 0x988b, 0xea04, 0xcdf0, 0x0044\n"
    );
}

// DECOMP_FUNC(0x00288700, 24)
extern "C" __attribute__((naked)) void camp_func_00288700() {
    asm volatile(
        ".arm\n"
        ".hword 0x0068, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0c23, 0xe280, 0x0092, 0xe5d0\n"
        ".hword 0x0000, 0xe350, 0xff1e, 0x012f\n"
    );
}

// DECOMP_FUNC(0x00289628, 24)
extern "C" __attribute__((naked)) void engine_func_00289628() {
    asm volatile(
        ".arm\n"
        ".hword 0x1000, 0xe1a0, 0x0008, 0xe59f\n"
        ".hword 0x0000, 0xe590, 0x0000, 0xe590\n"
        ".hword 0xeb88, 0xea00, 0xded0, 0x0043\n"
    );
}

// DECOMP_FUNC(0x002920cc, 24)
extern "C" __attribute__((naked)) void script_vm_func_002920cc() {
    asm volatile(
        ".arm\n"
        ".hword 0x1000, 0xe3a0, 0x002c, 0xe3a0\n"
        ".hword 0x4010, 0xe92d, 0xbb79, 0xeb00\n"
        ".hword 0x4010, 0xe8bd, 0xbb59, 0xea00\n"
    );
}

// DECOMP_FUNC(0x0029ebc4, 24)
extern "C" __attribute__((naked)) void shop_func_0029ebc4() {
    asm volatile(
        ".arm\n"
        ".hword 0x1010, 0xe4d0, 0x0001, 0xe351\n"
        ".hword 0x0000, 0x0a00, 0x01a2, 0xea00\n"
        ".hword 0xf000, 0xe320, 0x0000, 0xe1a0\n"
    );
}

// DECOMP_FUNC(0x002b0188, 24)
extern "C" __attribute__((naked)) void ui_func_002b0188() {
    asm volatile(
        ".arm\n"
        ".hword 0x200c, 0xe59f, 0x0080, 0xe080\n"
        ".hword 0x2000, 0xe592, 0x0180, 0xe792\n"
        ".hword 0x227c, 0xeafa, 0xea28, 0x0044\n"
    );
}

// DECOMP_FUNC(0x002b49f4, 24)
extern "C" __attribute__((naked)) void func_002b49f4() {
    asm volatile(
        ".arm\n"
        ".hword 0x4010, 0xe92d, 0x4001, 0xe1a0\n"
        ".hword 0xbb95, 0xebf9, 0x0004, 0xe1a0\n"
        ".hword 0x4010, 0xe8bd, 0x0000, 0xe1a0\n"
    );
}

// DECOMP_FUNC(0x002b4ea0, 24)
extern "C" __attribute__((naked)) void func_002b4ea0() {
    asm volatile(
        ".arm\n"
        ".hword 0x3002, 0xe1a0, 0x2001, 0xe1a0\n"
        ".hword 0x1000, 0xe1a0, 0x0000, 0xe59f\n"
        ".hword 0x47a2, 0xeafa, 0x6f14, 0x004e\n"
    );
}

// DECOMP_FUNC(0x002b96f0, 24)
extern "C" __attribute__((naked)) void engine_func_002b96f0() {
    asm volatile(
        ".arm\n"
        ".hword 0x200c, 0xe59f, 0x0080, 0xe080\n"
        ".hword 0x2000, 0xe592, 0x0180, 0xe792\n"
        ".hword 0x3024, 0xeafa, 0xea28, 0x0044\n"
    );
}

// DECOMP_FUNC(0x002bd48c, 24)
extern "C" __attribute__((naked)) void engine_func_002bd48c() {
    asm volatile(
        ".arm\n"
        ".hword 0x3002, 0xe1a0, 0x2001, 0xe1a0\n"
        ".hword 0x1000, 0xe1a0, 0x0000, 0xe59f\n"
        ".hword 0x622f, 0xeafa, 0x8568, 0x004e\n"
    );
}

// DECOMP_FUNC(0x002bf75c, 24)
extern "C" __attribute__((naked)) void func_002bf75c() {
    asm volatile(
        ".arm\n"
        ".hword 0x2001, 0xe1a0, 0x0008, 0xe581\n"
        ".hword 0x0018, 0xe280, 0x1004, 0xe280\n"
        ".hword 0x2018, 0xe282, 0x0000, 0xe1a0\n"
    );
}

// DECOMP_FUNC(0x00103c54, 28)
extern "C" __attribute__((naked)) void func_00103c54() {
    asm volatile(
        ".arm\n"
        ".hword 0x0001, 0xe3a0, 0x4010, 0xe92d\n"
        ".hword 0x30dd, 0xeb00, 0x0004, 0xe59f\n"
        ".hword 0x4010, 0xe8bd, 0xfe6e, 0xea06\n"
        ".hword 0x519c, 0x0046\n"
    );
}

// DECOMP_FUNC(0x0010fc44, 28)
extern "C" __attribute__((naked)) void engine_func_0010fc44() {
    asm volatile(
        ".arm\n"
        ".hword 0x0000, 0xe351, 0x0048, 0x059f\n"
        ".hword 0xff1e, 0x012f, 0x2018, 0xe5d0\n"
        ".hword 0x0000, 0xe352, 0x003c, 0x159f\n"
        ".hword 0xff1e, 0x112f\n"
    );
}

// DECOMP_FUNC(0x001596c0, 28)
extern "C" __attribute__((naked)) void func_001596c0() {
    asm volatile(
        ".arm\n"
        ".hword 0xc000, 0xe1a0, 0x2001, 0xe1a0\n"
        ".hword 0x0008, 0xe59f, 0x3a01, 0xe3a0\n"
        ".hword 0x100c, 0xe1a0, 0x8914, 0xea05\n"
        ".hword 0xac5c, 0x004e\n"
    );
}

// DECOMP_FUNC(0x001e0578, 28)
extern "C" __attribute__((naked)) void camp_func_001e0578() {
    asm volatile(
        ".arm\n"
        ".hword 0x1010, 0xe59f, 0x0001, 0xe3a0\n"
        ".hword 0x0004, 0xe581, 0x1000, 0xe3a0\n"
        ".hword 0x0001, 0xe1a0, 0x25cd, 0xea02\n"
        ".hword 0xda10, 0x0043\n"
    );
}

// DECOMP_FUNC(0x001f4aa8, 28)
extern "C" __attribute__((naked)) void camp_func_001f4aa8() {
    asm volatile(
        ".arm\n"
        ".hword 0x1010, 0xe59f, 0x0002, 0xe3a0\n"
        ".hword 0x0004, 0xe581, 0x1000, 0xe3a0\n"
        ".hword 0x0001, 0xe1a0, 0xd481, 0xea01\n"
        ".hword 0xda10, 0x0043\n"
    );
}

// DECOMP_FUNC(0x001ff3a8, 28)
extern "C" __attribute__((naked)) void ui_func_001ff3a8() {
    asm volatile(
        ".arm\n"
        ".hword 0x4010, 0xe92d, 0x05c5, 0xeb03\n"
        ".hword 0x4000, 0xe1a0, 0x59b1, 0xebfd\n"
        ".hword 0x0004, 0xe1a0, 0x4010, 0xe8bd\n"
        ".hword 0x13e6, 0xea03\n"
    );
}

// DECOMP_FUNC(0x0020d530, 28)
extern "C" __attribute__((naked)) void script_vm_func_0020d530() {
    asm volatile(
        ".arm\n"
        ".hword 0x0010, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0903, 0xe280, 0x0ebd, 0xe280\n"
        ".hword 0x001c, 0xe590, 0x156b, 0xeafd\n"
        ".hword 0x7a78, 0x0044\n"
    );
}

// DECOMP_FUNC(0x0021df5c, 28)
extern "C" __attribute__((naked)) void engine_func_0021df5c() {
    asm volatile(
        ".arm\n"
        ".hword 0x0010, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0903, 0xe280, 0x0ec1, 0xe280\n"
        ".hword 0x001c, 0xe590, 0xd2e0, 0xeafc\n"
        ".hword 0x7a78, 0x0044\n"
    );
}

// DECOMP_FUNC(0x0021e054, 28)
extern "C" __attribute__((naked)) void camp_func_0021e054() {
    asm volatile(
        ".arm\n"
        ".hword 0x0010, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x0000, 0x0a00\n"
        ".hword 0x7cbc, 0xea01, 0xff1e, 0xe12f\n"
        ".hword 0x7e28, 0x0044\n"
    );
}

// DECOMP_FUNC(0x0023c840, 28)
extern "C" __attribute__((naked)) void engine_func_0023c840() {
    asm volatile(
        ".arm\n"
        ".hword 0x0010, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x0000, 0x0a00\n"
        ".hword 0x2e36, 0xea06, 0xff1e, 0xe12f\n"
        ".hword 0x98d4, 0x0043\n"
    );
}

// DECOMP_FUNC(0x0023f640, 28)
extern "C" __attribute__((naked)) void func_0023f640() {
    asm volatile(
        ".arm\n"
        ".hword 0x0010, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x0000, 0x0a00\n"
        ".hword 0x6a97, 0xea06, 0xff1e, 0xe12f\n"
        ".hword 0x5d18, 0x0043\n"
    );
}

// DECOMP_FUNC(0x00244f04, 28)
extern "C" __attribute__((naked)) void func_00244f04() {
    asm volatile(
        ".arm\n"
        ".hword 0x100c, 0xe59f, 0x200c, 0xe59f\n"
        ".hword 0x1100, 0xe791, 0x0100, 0xe792\n"
        ".hword 0xf706, 0xea01, 0x4b84, 0x0046\n"
        ".hword 0x4b7c, 0x0046\n"
    );
}

// DECOMP_FUNC(0x00248268, 28)
extern "C" __attribute__((naked)) void engine_func_00248268() {
    asm volatile(
        ".arm\n"
        ".hword 0x0010, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0903, 0xe280, 0x0ec3, 0xe280\n"
        ".hword 0x001c, 0xe590, 0x2a1d, 0xeafc\n"
        ".hword 0x7a78, 0x0044\n"
    );
}

// DECOMP_FUNC(0x0024aed4, 28)
extern "C" __attribute__((naked)) void engine_func_0024aed4() {
    asm volatile(
        ".arm\n"
        ".hword 0x0010, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0903, 0xe280, 0x0ec5, 0xe280\n"
        ".hword 0x001c, 0xe590, 0x1f02, 0xeafc\n"
        ".hword 0x7a78, 0x0044\n"
    );
}

// DECOMP_FUNC(0x00298fa8, 28)
extern "C" __attribute__((naked)) void camp_func_00298fa8() {
    asm volatile(
        ".arm\n"
        ".hword 0x1010, 0xe59f, 0x1004, 0xe591\n"
        ".hword 0x1a01, 0xe281, 0x02f1, 0xe5c1\n"
        ".hword 0x0001, 0xe220, 0x523f, 0xeaff\n"
        ".hword 0xe140, 0x0044\n"
    );
}

// DECOMP_FUNC(0x0029a368, 28)
extern "C" __attribute__((naked)) void engine_func_0029a368() {
    asm volatile(
        ".arm\n"
        ".hword 0x2010, 0xe59f, 0x1000, 0xe1a0\n"
        ".hword 0x2004, 0xe592, 0x0a01, 0xe282\n"
        ".hword 0x0e8b, 0xe280, 0xcdf7, 0xeafe\n"
        ".hword 0xe140, 0x0044\n"
    );
}

// DECOMP_FUNC(0x0029a504, 28)
extern "C" __attribute__((naked)) void func_0029a504() {
    asm volatile(
        ".arm\n"
        ".hword 0x1085, 0xe5d0, 0x0000, 0xe351\n"
        ".hword 0x0001, 0x0a00, 0x0a01, 0xed9f\n"
        ".hword 0x7c7b, 0xea00, 0xff1e, 0xe12f\n"
        ".hword 0x0000, 0x0000\n"
    );
}

// DECOMP_FUNC(0x002a2d34, 28)
extern "C" __attribute__((naked)) void func_002a2d34() {
    asm volatile(
        ".arm\n"
        ".hword 0x0000, 0xe5d0, 0x0000, 0xe350\n"
        ".hword 0x0001, 0x0a00, 0x0004, 0xe59f\n"
        ".hword 0xeccc, 0xeafa, 0xff1e, 0xe12f\n"
        ".hword 0xad10, 0x004e\n"
    );
}

// DECOMP_FUNC(0x002a61f8, 28)
extern "C" __attribute__((naked)) void engine_func_002a61f8() {
    asm volatile(
        ".arm\n"
        ".hword 0x002f, 0xe3a0, 0x4010, 0xe92d\n"
        ".hword 0x7b08, 0xeb00, 0x4010, 0xe8bd\n"
        ".hword 0x1000, 0xe3a0, 0x002f, 0xe3a0\n"
        ".hword 0x0000, 0xe1a0\n"
    );
}

// DECOMP_FUNC(0x002aea60, 28)
extern "C" __attribute__((naked)) void script_vm_func_002aea60() {
    asm volatile(
        ".arm\n"
        ".hword 0x1000, 0xe3a0, 0x0024, 0xe3a0\n"
        ".hword 0x4010, 0xe92d, 0x002e, 0xeb00\n"
        ".hword 0x4010, 0xe8bd, 0x0024, 0xe3a0\n"
        ".hword 0x0000, 0xe1a0\n"
    );
}

// DECOMP_FUNC(0x002b2504, 28)
extern "C" __attribute__((naked)) void func_002b2504() {
    asm volatile(
        ".arm\n"
        ".hword 0x4010, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x8694, 0xebfe, 0x0004, 0xe1a0\n"
        ".hword 0x8682, 0xebfe, 0x4010, 0xe8bd\n"
        ".hword 0x0000, 0xe1a0\n"
    );
}

// DECOMP_FUNC(0x002b9408, 28)
extern "C" __attribute__((naked)) void engine_func_002b9408() {
    asm volatile(
        ".arm\n"
        ".hword 0xb570, 0x0004, 0x000d, 0x0010\n"
        ".hword 0xd102, 0x2104, 0xf00d, 0xfa65\n"
        ".hword 0x0003, 0x002a, 0x0021, 0x2000\n"
        ".hword 0xf00c, 0xffb2\n"
    );
}

// DECOMP_FUNC(0x00100b44, 32)
extern "C" __attribute__((naked)) void crt_func_00100b44() {
    asm volatile(
        ".thumb\n"
        ".hword 0xb510, 0x0004, 0xf1c6, 0xe87a\n"
        ".hword 0x6800, 0x5d00, 0x0700, 0xd504\n"
        ".hword 0x2cdf, 0xd002, 0x0020, 0x3820\n"
        ".hword 0xbd10, 0x0020, 0xbd10, 0xffff\n"
    );
}

// DECOMP_FUNC(0x00106d58, 32)
extern "C" __attribute__((naked)) void func_00106d58() {
    asm volatile(
        ".arm\n"
        ".hword 0x0000, 0xe1a0, 0x4010, 0xe92d\n"
        ".hword 0x22b5, 0xeb00, 0x233d, 0xeb00\n"
        ".hword 0x2328, 0xeb00, 0x2322, 0xeb00\n"
        ".hword 0x4010, 0xe8bd, 0xc53e, 0xea00\n"
    );
}

// DECOMP_FUNC(0x0010decc, 32)
extern "C" __attribute__((naked)) void engine_func_0010decc() {
    asm volatile(
        ".arm\n"
        ".hword 0x4010, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x0014, 0xe590, 0x0000, 0xe350\n"
        ".hword 0xd91f, 0x1b06, 0x0004, 0xe1a0\n"
        ".hword 0x4010, 0xe8bd, 0xd91c, 0xea06\n"
    );
}

// DECOMP_FUNC(0x00126754, 32)
extern "C" __attribute__((naked)) void func_00126754() {
    asm volatile(
        ".arm\n"
        ".hword 0x0a05, 0xed9f, 0x2001, 0xe1a0\n"
        ".hword 0x1012, 0xe3a0, 0x1a40, 0xeef0\n"
        ".hword 0x1a40, 0xeeb0, 0x0a40, 0xeef0\n"
        ".hword 0x2894, 0xea06, 0x0000, 0x0000\n"
    );
}

// DECOMP_FUNC(0x0014dbd0, 32)
extern "C" __attribute__((naked)) void func_0014dbd0() {
    asm volatile(
        ".arm\n"
        ".hword 0x1014, 0xe59f, 0x1000, 0xe580\n"
        ".hword 0x1024, 0xe590, 0x0000, 0xe351\n"
        ".hword 0x1000, 0x13a0, 0x1024, 0x1580\n"
        ".hword 0x5a4e, 0xea05, 0x0b00, 0x0042\n"
    );
}

// DECOMP_FUNC(0x0015630c, 32)
extern "C" __attribute__((naked)) void func_0015630c() {
    asm volatile(
        ".arm\n"
        ".hword 0x0000, 0xe351, 0x1007, 0xe5d0\n"
        ".hword 0x1002, 0x1381, 0x1002, 0x03c1\n"
        ".hword 0x1007, 0xe5c0, 0x0068, 0xe590\n"
        ".hword 0x10ff, 0xe201, 0x0ff7, 0xea00\n"
    );
}

// DECOMP_FUNC(0x0017fac4, 32)
extern "C" __attribute__((naked)) void camp_func_0017fac4() {
    asm volatile(
        ".arm\n"
        ".hword 0x0014, 0xe59f, 0x1004, 0xe3a0\n"
        ".hword 0x0000, 0xe590, 0x1008, 0xe580\n"
        ".hword 0x1001, 0xe3a0, 0x003c, 0xe280\n"
        ".hword 0xfd53, 0xea04, 0xe0f8, 0x0043\n"
    );
}

// DECOMP_FUNC(0x0019fe8c, 32)
extern "C" __attribute__((naked)) void camp_func_0019fe8c() {
    asm volatile(
        ".arm\n"
        ".hword 0x0000, 0xe350, 0x0000, 0x1351\n"
        ".hword 0xff1e, 0x012f, 0x0a00, 0xed91\n"
        ".hword 0x0a59, 0xeddf, 0x0a60, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0xff1e, 0x012f\n"
    );
}

// DECOMP_FUNC(0x00215938, 32)
extern "C" __attribute__((naked)) void battle_func_00215938() {
    asm volatile(
        ".arm\n"
        ".hword 0x2180, 0xe080, 0x0280, 0xe082\n"
        ".hword 0x200c, 0xe59f, 0x0180, 0xe082\n"
        ".hword 0x002c, 0xe280, 0x2090, 0xe3a0\n"
        ".hword 0x9d80, 0xea02, 0x8000, 0x0047\n"
    );
}

// DECOMP_FUNC(0x0021e8b0, 32)
extern "C" __attribute__((naked)) void script_vm_func_0021e8b0() {
    asm volatile(
        ".arm\n"
        ".hword 0x2014, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x2000, 0xe592, 0x02f8, 0xe1c2\n"
        ".hword 0x1000, 0xe1a0, 0x0040, 0xe282\n"
        ".hword 0x4b6b, 0xea00, 0xcdf0, 0x0044\n"
    );
}

// DECOMP_FUNC(0x0021e8d0, 32)
extern "C" __attribute__((naked)) void script_vm_func_0021e8d0() {
    asm volatile(
        ".arm\n"
        ".hword 0x0014, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x0001, 0x0a00\n"
        ".hword 0x0040, 0xe280, 0xebd4, 0xea05\n"
        ".hword 0xff1e, 0xe12f, 0xcdf0, 0x0044\n"
    );
}

// DECOMP_FUNC(0x00220f00, 32)
extern "C" __attribute__((naked)) void camp_func_00220f00() {
    asm volatile(
        ".arm\n"
        ".hword 0x0014, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x0001, 0x0a00\n"
        ".hword 0x0004, 0xe590, 0xff87, 0xea02\n"
        ".hword 0xff1e, 0xe12f, 0xde68, 0x0043\n"
    );
}

// DECOMP_FUNC(0x0024c564, 32)
extern "C" __attribute__((naked)) void func_0024c564() {
    asm volatile(
        ".arm\n"
        ".hword 0x10b4, 0xe1d0, 0x2010, 0xe59f\n"
        ".hword 0x0008, 0xe590, 0x1201, 0xe081\n"
        ".hword 0x1101, 0xe082, 0x100c, 0xe591\n"
        ".hword 0xff11, 0xe12f, 0x4110, 0x0046\n"
    );
}

// DECOMP_FUNC(0x00250420, 32)
extern "C" __attribute__((naked)) void engine_func_00250420() {
    asm volatile(
        ".arm\n"
        ".hword 0x10b4, 0xe1d0, 0x2010, 0xe59f\n"
        ".hword 0x0008, 0xe590, 0x1201, 0xe081\n"
        ".hword 0x1101, 0xe082, 0x1008, 0xe591\n"
        ".hword 0xff11, 0xe12f, 0x4110, 0x0046\n"
    );
}

// DECOMP_FUNC(0x0025485c, 32)
extern "C" __attribute__((naked)) void camp_func_0025485c() {
    asm volatile(
        ".arm\n"
        ".hword 0x0014, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x0001, 0x0a00\n"
        ".hword 0x0004, 0xe590, 0x9d97, 0xea05\n"
        ".hword 0xff1e, 0xe12f, 0xde68, 0x0043\n"
    );
}

// DECOMP_FUNC(0x002594f0, 32)
extern "C" __attribute__((naked)) void script_vm_func_002594f0() {
    asm volatile(
        ".arm\n"
        ".hword 0x0a05, 0xed9f, 0x2000, 0xe3e0\n"
        ".hword 0x1010, 0xe3a0, 0x1a40, 0xeef0\n"
        ".hword 0x1a40, 0xeeb0, 0x0a40, 0xeef0\n"
        ".hword 0x5d2d, 0xea01, 0x0000, 0x0000\n"
    );
}

// DECOMP_FUNC(0x002599f8, 32)
extern "C" __attribute__((naked)) void camp_func_002599f8() {
    asm volatile(
        ".arm\n"
        ".hword 0x0014, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x0001, 0x0a00\n"
        ".hword 0x0004, 0xe590, 0x1cdc, 0xea02\n"
        ".hword 0xff1e, 0xe12f, 0xde68, 0x0043\n"
    );
}

// DECOMP_FUNC(0x0025ce6c, 32)
extern "C" __attribute__((naked)) void script_vm_func_0025ce6c() {
    asm volatile(
        ".arm\n"
        ".hword 0x4010, 0xe92d, 0x661d, 0xeb01\n"
        ".hword 0x00b4, 0xe1d0, 0x5e53, 0xeb01\n"
        ".hword 0x0054, 0xe590, 0x4010, 0xe8bd\n"
        ".hword 0x0a20, 0xe1a0, 0xa074, 0xeaff\n"
    );
}

// DECOMP_FUNC(0x0025cec4, 32)
extern "C" __attribute__((naked)) void script_vm_func_0025cec4() {
    asm volatile(
        ".arm\n"
        ".hword 0x4010, 0xe92d, 0x6607, 0xeb01\n"
        ".hword 0x00b0, 0xe1d0, 0x5e3d, 0xeb01\n"
        ".hword 0x0054, 0xe590, 0x4010, 0xe8bd\n"
        ".hword 0x0a20, 0xe1a0, 0xa05e, 0xeaff\n"
    );
}

// DECOMP_FUNC(0x00262b40, 32)
extern "C" __attribute__((naked)) void battle_func_00262b40() {
    asm volatile(
        ".arm\n"
        ".hword 0x4010, 0xe92d, 0x4001, 0xe1a0\n"
        ".hword 0x77de, 0xeb01, 0x1004, 0xe1a0\n"
        ".hword 0x4010, 0xe8bd, 0x2c01, 0xe3a0\n"
        ".hword 0x008c, 0xe280, 0x0000, 0xe1a0\n"
    );
}

// DECOMP_FUNC(0x00275a18, 32)
extern "C" __attribute__((naked)) void script_vm_func_00275a18() {
    asm volatile(
        ".arm\n"
        ".hword 0x0014, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x0001, 0x0a00\n"
        ".hword 0x0040, 0xe280, 0x9a0e, 0xea04\n"
        ".hword 0xff1e, 0xe12f, 0xcdf0, 0x0044\n"
    );
}

// DECOMP_FUNC(0x00275e38, 32)
extern "C" __attribute__((naked)) void script_vm_func_00275e38() {
    asm volatile(
        ".arm\n"
        ".hword 0x0014, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x0001, 0x0a00\n"
        ".hword 0x0040, 0xe280, 0x99a2, 0xea04\n"
        ".hword 0xff1e, 0xe12f, 0xcdf0, 0x0044\n"
    );
}

// DECOMP_FUNC(0x00276488, 32)
extern "C" __attribute__((naked)) void script_vm_func_00276488() {
    asm volatile(
        ".arm\n"
        ".hword 0x0010, 0xe59f, 0x2010, 0xe59f\n"
        ".hword 0x1004, 0xe590, 0x0008, 0xe590\n"
        ".hword 0x1088, 0xe281, 0x1aad, 0xea01\n"
        ".hword 0xe2a8, 0x0043, 0x4d28, 0x0002\n"
    );
}

// DECOMP_FUNC(0x0027dbb8, 32)
extern "C" __attribute__((naked)) void script_vm_func_0027dbb8() {
    asm volatile(
        ".arm\n"
        ".hword 0x0014, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x0001, 0x0a00\n"
        ".hword 0x0040, 0xe280, 0x78d0, 0xea04\n"
        ".hword 0xff1e, 0xe12f, 0xcdf0, 0x0044\n"
    );
}

// End of Batch 39 A.
