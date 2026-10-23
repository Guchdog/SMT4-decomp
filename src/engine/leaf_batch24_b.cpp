#include "types.h"

// Batch 24 B exact ARM encodings; each complete ledger extent is emitted as raw words.

// DECOMP_FUNC(0x0023a2ec, 28)
extern "C" __attribute__((naked)) void ui_func_0023a2ec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d000f\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe28d3014\n"
        ".inst 0xe59d2010\n"
        ".inst 0xeb06ff56\n"
        ".inst 0xe49d4004\n"
        ".inst 0xe49df014\n"
    );
}
// DECOMP_FUNC(0x0023a330, 32)
extern "C" __attribute__((naked)) void script_vm_func_0023a330() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d000f\n"
        ".inst 0xe3e01102\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe28d3010\n"
        ".inst 0xe59d200c\n"
        ".inst 0xeb06ff44\n"
        ".inst 0xe49d4004\n"
        ".inst 0xe49df014\n"
    );
}

// DECOMP_FUNC(0x00258040, 52)
extern "C" __attribute__((naked)) void script_vm_func_00258040() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe24dd028\n"
        ".inst 0xe1a04000\n"
        ".inst 0xeb0179a6\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xebffefd0\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xe0800084\n"
        ".inst 0xe1d000b0\n"
        ".inst 0xe28dd028\n"
        ".inst 0xe3c00b3f\n"
        ".inst 0xe8bd8010\n"
    );
}
// DECOMP_FUNC(0x002f14d8, 52)
extern "C" __attribute__((naked)) void engine_func_002f14d8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe969e\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfe89ea\n"
        ".inst 0xe2800b12\n"
        ".inst 0xe2800f6f\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe5902000\n"
        ".inst 0xe1c21411\n"
        ".inst 0xe5801000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}
// DECOMP_FUNC(0x002277c4, 56)
extern "C" __attribute__((naked)) void ui_func_002277c4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe2804b07\n"
        ".inst 0xe28440fc\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000006\n"
        ".inst 0xeb01b12d\n"
        ".inst 0xeb01af3b\n"
        ".inst 0xe3500000\n"
        ".inst 0x05940000\n"
        ".inst 0x02800c01\n"
        ".inst 0x01d009f6\n"
        ".inst 0x13a00000\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0022ebcc, 56)
extern "C" __attribute__((naked)) void shop_func_0022ebcc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04001\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a00017\n"
        ".inst 0xeb0248b8\n"
        ".inst 0xe1a06000\n"
        ".inst 0xeb0248ac\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xeb024895\n"
        ".inst 0xe1540000\n"
        ".inst 0x23a00000\n"
        ".inst 0x30850384\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00237a5c, 56)
extern "C" __attribute__((naked)) void func_00237a5c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a06001\n"
        ".inst 0xe3a04000\n"
        ".inst 0xeb04f87f\n"
        ".inst 0xe1800004\n"
        ".inst 0xe2101102\n"
        ".inst 0xe1a04000\n"
        ".inst 0x4a000003\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb04b978\n"
        ".inst 0xe1800004\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x0023a358, 56)
extern "C" __attribute__((naked)) void engine_func_0023a358() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4037\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe28d0004\n"
        ".inst 0xeb019c4d\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a000003\n"
        ".inst 0xe28d0004\n"
        ".inst 0xeb019c24\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfbb2d4\n"
        ".inst 0xe28dd00c\n"
        ".inst 0xe8bd8030\n"
    );
}

// DECOMP_FUNC(0x0024c500, 56)
extern "C" __attribute__((naked)) void func_0024c500() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a04001\n"
        ".inst 0xebffc3cd\n"
        ".inst 0xe0800185\n"
        ".inst 0xe2800ecf\n"
        ".inst 0xe7d011a4\n"
        ".inst 0xe2043007\n"
        ".inst 0xe3a02001\n"
        ".inst 0xe1a00312\n"
        ".inst 0xe20000ff\n"
        ".inst 0xe0100001\n"
        ".inst 0x13a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x0024ddf8, 56)
extern "C" __attribute__((naked)) void ui_func_0024ddf8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d41f0\n"
        ".inst 0xe1a04003\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a07001\n"
        ".inst 0xe0000490\n"
        ".inst 0xe1a05002\n"
        ".inst 0xe1a01002\n"
        ".inst 0xeb01e0d0\n"
        ".inst 0xe0466000\n"
        ".inst 0xe0000497\n"
        ".inst 0xe1a01005\n"
        ".inst 0xeb01e0cc\n"
        ".inst 0xe0800006\n"
        ".inst 0xe8bd81f0\n"
    );
}

// DECOMP_FUNC(0x0024df5c, 56)
extern "C" __attribute__((naked)) void ui_func_0024df5c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a01001\n"
        ".inst 0xebfd8ec6\n"
        ".inst 0xe5944034\n"
        ".inst 0xe3540000\n"
        ".inst 0x0a000005\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfd8ec0\n"
        ".inst 0xe5944034\n"
        ".inst 0xe3540000\n"
        ".inst 0x1afffff9\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00253394, 56)
extern "C" __attribute__((naked)) void engine_func_00253394() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xeb01bdde\n"
        ".inst 0xe1a01fc4\n"
        ".inst 0xe0842da1\n"
        ".inst 0xe1a012c2\n"
        ".inst 0xe3c2201f\n"
        ".inst 0xe0800101\n"
        ".inst 0xe0442002\n"
        ".inst 0xe5900750\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe0100211\n"
        ".inst 0x13a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0025b6b0, 56)
extern "C" __attribute__((naked)) void script_vm_func_0025b6b0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xeb019d17\n"
        ".inst 0xe1a01fc4\n"
        ".inst 0xe0842da1\n"
        ".inst 0xe1a012c2\n"
        ".inst 0xe3c2201f\n"
        ".inst 0xe0800101\n"
        ".inst 0xe0442002\n"
        ".inst 0xe59007d4\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe0100211\n"
        ".inst 0x13a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0025c4d0, 56)
extern "C" __attribute__((naked)) void script_vm_func_0025c4d0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe3a00001\n"
        ".inst 0xed2d0b04\n"
        ".inst 0xed2d8b02\n"
        ".inst 0xeeb08a61\n"
        ".inst 0xeb01a4d4\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a000002\n"
        ".inst 0xeeb00a48\n"
        ".inst 0xe28d0008\n"
        ".inst 0xebfaf592\n"
        ".inst 0xecbd8b02\n"
        ".inst 0xe28dd010\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0025ce8c, 56)
extern "C" __attribute__((naked)) void script_vm_func_0025ce8c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00e41\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb018f43\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000006\n"
        ".inst 0xeb016611\n"
        ".inst 0xe1d010b2\n"
        ".inst 0xe3510000\n"
        ".inst 0x11d000b4\n"
        ".inst 0x13500000\n"
        ".inst 0x13a00001\n"
        ".inst 0x1a000000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00282c0c, 56)
extern "C" __attribute__((naked)) void ui_func_00282c0c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe2804b07\n"
        ".inst 0xe28440fc\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000006\n"
        ".inst 0xeb00441b\n"
        ".inst 0xeb004229\n"
        ".inst 0xe3500000\n"
        ".inst 0x05940000\n"
        ".inst 0x02800c01\n"
        ".inst 0x01d009f4\n"
        ".inst 0x13a00000\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002aea28, 56)
extern "C" __attribute__((naked)) void camp_func_002aea28() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a0000e\n"
        ".inst 0xeb004921\n"
        ".inst 0xe1a06000\n"
        ".inst 0xeb004915\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xeb0048fe\n"
        ".inst 0xe1540000\n"
        ".inst 0x23a00000\n"
        ".inst 0x30850204\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002b5b94, 56)
extern "C" __attribute__((naked)) void script_vm_func_002b5b94() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe24dd018\n"
        ".inst 0xe28de028\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe89e1061\n"
        ".inst 0xe88d1061\n"
        ".inst 0xe28d0010\n"
        ".inst 0xebffded7\n"
        ".inst 0xe28de010\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe89e0006\n"
        ".inst 0xe8840006\n"
        ".inst 0xe28dd018\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002c3aa8, 56)
extern "C" __attribute__((naked)) void engine_func_002c3aa8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xee1d0f70\n"
        ".inst 0xe5941004\n"
        ".inst 0xe1500001\n"
        ".inst 0x0a000003\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfa0a8b\n"
        ".inst 0xee1d0f70\n"
        ".inst 0xe5840004\n"
        ".inst 0xe5940008\n"
        ".inst 0xe2800001\n"
        ".inst 0xe5840008\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002d2954, 56)
extern "C" __attribute__((naked)) void engine_func_002d2954() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebffc06e\n"
        ".inst 0xe1a01fc4\n"
        ".inst 0xe0842da1\n"
        ".inst 0xe1a012c2\n"
        ".inst 0xe3c2201f\n"
        ".inst 0xe0800101\n"
        ".inst 0xe0442002\n"
        ".inst 0xe5900d18\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe0100211\n"
        ".inst 0x13a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002d4e48, 56)
extern "C" __attribute__((naked)) void camp_func_002d4e48() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe3a0002e\n"
        ".inst 0xebffb019\n"
        ".inst 0xe1a06000\n"
        ".inst 0xebffb00d\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xebffaff6\n"
        ".inst 0xe1540000\n"
        ".inst 0x23a00000\n"
        ".inst 0x30850104\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002d4e80, 56)
extern "C" __attribute__((naked)) void camp_func_002d4e80() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a0002e\n"
        ".inst 0xebffb00b\n"
        ".inst 0xe1a06000\n"
        ".inst 0xebffafff\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xebffafe8\n"
        ".inst 0xe1540000\n"
        ".inst 0x23a00000\n"
        ".inst 0x30850104\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002d87e0, 56)
extern "C" __attribute__((naked)) void ui_func_002d87e0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfef9dc\n"
        ".inst 0xeb007475\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfdc5c8\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe1a01002\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfdc566\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfed5d0\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002df760, 56)
extern "C" __attribute__((naked)) void script_vm_func_002df760() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebff8ceb\n"
        ".inst 0xe1a01fc4\n"
        ".inst 0xe0842da1\n"
        ".inst 0xe1a012c2\n"
        ".inst 0xe3c2201f\n"
        ".inst 0xe0800101\n"
        ".inst 0xe0442002\n"
        ".inst 0xe5900744\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe0100211\n"
        ".inst 0x13a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002f0fe0, 56)
extern "C" __attribute__((naked)) void engine_func_002f0fe0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe97dc\n"
        ".inst 0xe3500010\n"
        ".inst 0xe1a04000\n"
        ".inst 0x2a000005\n"
        ".inst 0xebfe8b26\n"
        ".inst 0xe0800104\n"
        ".inst 0xe2800b12\n"
        ".inst 0xe2800f5f\n"
        ".inst 0xe5900000\n"
        ".inst 0xebfe73d0\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002f14a0, 56)
extern "C" __attribute__((naked)) void engine_func_002f14a0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe96ac\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfe89f8\n"
        ".inst 0xe2801b12\n"
        ".inst 0xe2811f6f\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe5911000\n"
        ".inst 0xe0110410\n"
        ".inst 0x13a00001\n"
        ".inst 0xebfe72a0\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002f35cc, 56)
extern "C" __attribute__((naked)) void engine_func_002f35cc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebff3d50\n"
        ".inst 0xe1a01fc4\n"
        ".inst 0xe0842da1\n"
        ".inst 0xe1a012c2\n"
        ".inst 0xe3c2201f\n"
        ".inst 0xe0800101\n"
        ".inst 0xe0442002\n"
        ".inst 0xe5900c98\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe0100211\n"
        ".inst 0x13a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002fb058, 56)
extern "C" __attribute__((naked)) void engine_func_002fb058() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebff1ead\n"
        ".inst 0xe1a01fc4\n"
        ".inst 0xe0842da1\n"
        ".inst 0xe1a012c2\n"
        ".inst 0xe3c2201f\n"
        ".inst 0xe0800101\n"
        ".inst 0xe0442002\n"
        ".inst 0xe5900e58\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe0100211\n"
        ".inst 0x13a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00211e54, 60)
extern "C" __attribute__((naked)) void engine_func_00211e54() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a00000\n"
        ".inst 0xeb02143f\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe3a00002\n"
        ".inst 0xeb02143c\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xeb021439\n"
        ".inst 0xe1a01004\n"
        ".inst 0xeb011db0\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb017751\n"
        ".inst 0xe3a00002\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00231628, 60)
extern "C" __attribute__((naked)) void camp_func_00231628() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04001\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe3a0002b\n"
        ".inst 0xeb023e21\n"
        ".inst 0xe1a06000\n"
        ".inst 0xeb023e15\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xeb023dfe\n"
        ".inst 0xe1540000\n"
        ".inst 0x30840104\n"
        ".inst 0x23a00000\n"
        ".inst 0x30850100\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00235510, 60)
extern "C" __attribute__((naked)) void script_vm_func_00235510() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04001\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a00027\n"
        ".inst 0xeb022e67\n"
        ".inst 0xe1a06000\n"
        ".inst 0xeb022e5b\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xeb022e44\n"
        ".inst 0xe1540000\n"
        ".inst 0x30840204\n"
        ".inst 0x23a00000\n"
        ".inst 0x30850180\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00235758, 60)
extern "C" __attribute__((naked)) void camp_func_00235758() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe0801081\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04002\n"
        ".inst 0xe3a00026\n"
        ".inst 0xeb022dd4\n"
        ".inst 0xe1a06000\n"
        ".inst 0xeb022dc8\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xeb022db1\n"
        ".inst 0xe1540000\n"
        ".inst 0x23a00000\n"
        ".inst 0x30850284\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002473d8, 60)
extern "C" __attribute__((naked)) void camp_func_002473d8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04001\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a0002b\n"
        ".inst 0xeb01e6b5\n"
        ".inst 0xe1a06000\n"
        ".inst 0xeb01e6a9\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xeb01e692\n"
        ".inst 0xe1540000\n"
        ".inst 0x30840104\n"
        ".inst 0x23a00000\n"
        ".inst 0x30850100\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00253f64, 60)
extern "C" __attribute__((naked)) void engine_func_00253f64() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5d00000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000008\n"
        ".inst 0xe594002c\n"
        ".inst 0xeb01c0f7\n"
        ".inst 0xe5940048\n"
        ".inst 0xe3a05000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xeb01c0f2\n"
        ".inst 0xe5845048\n"
        ".inst 0xe5c45000\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00259454, 60)
extern "C" __attribute__((naked)) void func_00259454() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4030\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe24dd00c\n"
        ".inst 0xe1a04001\n"
        ".inst 0xe3a00000\n"
        ".inst 0xeb00d2b3\n"
        ".inst 0xeb00c073\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe3a0300f\n"
        ".inst 0xe1a00005\n"
        ".inst 0xe88d0012\n"
        ".inst 0xeb00b527\n"
        ".inst 0xe28dd00c\n"
        ".inst 0xe8bd8030\n"
    );
}

// DECOMP_FUNC(0x00269ee0, 60)
extern "C" __attribute__((naked)) void camp_func_00269ee0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe24dd008\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5841038\n"
        ".inst 0xe58d0000\n"
        ".inst 0xe58d0004\n"
        ".inst 0xe28d2004\n"
        ".inst 0xe1a0100d\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebff51a0\n"
        ".inst 0xe1cd00d0\n"
        ".inst 0xe1c402fc\n"
        ".inst 0xe28dd008\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0027636c, 60)
extern "C" __attribute__((naked)) void script_vm_func_0027636c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a0002f\n"
        ".inst 0xeb012ad0\n"
        ".inst 0xe1a06000\n"
        ".inst 0xeb012ac4\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xeb012aad\n"
        ".inst 0xe1540000\n"
        ".inst 0x30840184\n"
        ".inst 0x23a00000\n"
        ".inst 0x30850100\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00287b10, 60)
extern "C" __attribute__((naked)) void script_vm_func_00287b10() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe3a0002f\n"
        ".inst 0xeb00e4e7\n"
        ".inst 0xe1a06000\n"
        ".inst 0xeb00e4db\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xeb00e4c4\n"
        ".inst 0xe1540000\n"
        ".inst 0x30840084\n"
        ".inst 0x23a00000\n"
        ".inst 0x30850180\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00288380, 60)
extern "C" __attribute__((naked)) void camp_func_00288380() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a01002\n"
        ".inst 0xe3a00001\n"
        ".inst 0xeb00e2cb\n"
        ".inst 0xe1a06000\n"
        ".inst 0xeb00e2bf\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xeb00e2a8\n"
        ".inst 0xe1500004\n"
        ".inst 0x80850104\n"
        ".inst 0x81d000b0\n"
        ".inst 0x91d500b0\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002888dc, 60)
extern "C" __attribute__((naked)) void camp_func_002888dc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a00024\n"
        ".inst 0xeb00e174\n"
        ".inst 0xe1a06000\n"
        ".inst 0xeb00e168\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xeb00e151\n"
        ".inst 0xe1540000\n"
        ".inst 0x30840184\n"
        ".inst 0x23e00000\n"
        ".inst 0x37d50200\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00293a30, 60)
extern "C" __attribute__((naked)) void script_vm_func_00293a30() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe24dd008\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe584103c\n"
        ".inst 0xe58d0000\n"
        ".inst 0xe58d0004\n"
        ".inst 0xe28d2004\n"
        ".inst 0xe1a0100d\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfeaacc\n"
        ".inst 0xe1cd00d0\n"
        ".inst 0xe1c402fc\n"
        ".inst 0xe28dd008\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002a13d0, 60)
extern "C" __attribute__((naked)) void engine_func_002a13d0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe24dd008\n"
        ".inst 0xe4c01004\n"
        ".inst 0xeb00672e\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5801008\n"
        ".inst 0xe2404004\n"
        ".inst 0xe580100c\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xeb006661\n"
        ".inst 0xe1c000d0\n"
        ".inst 0xe1c400f4\n"
        ".inst 0xe28dd008\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002cd6e4, 60)
extern "C" __attribute__((naked)) void script_vm_func_002cd6e4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe2f87\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfdf994\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe3a02012\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebff9bbb\n"
        ".inst 0xe3500000\n"
        ".inst 0x03a00001\n"
        ".inst 0x13a00000\n"
        ".inst 0xebff020e\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002cdce0, 60)
extern "C" __attribute__((naked)) void engine_func_002cdce0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a00000\n"
        ".inst 0xebff249c\n"
        ".inst 0xe6ff4070\n"
        ".inst 0xe3a00001\n"
        ".inst 0xebff2499\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebffa27e\n"
        ".inst 0xe0800085\n"
        ".inst 0xe2800c01\n"
        ".inst 0xe1d004b8\n"
        ".inst 0xebff008f\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002d03c4, 60)
extern "C" __attribute__((naked)) void script_vm_func_002d03c4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe1d000b0\n"
        ".inst 0xebff98ca\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1d500b0\n"
        ".inst 0xebff98c7\n"
        ".inst 0xe3540000\n"
        ".inst 0x03a00000\n"
        ".inst 0x13500000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe1d000b4\n"
        ".inst 0xe1d410b4\n"
        ".inst 0xe0400001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002d4eb8, 60)
extern "C" __attribute__((naked)) void camp_func_002d4eb8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a0002c\n"
        ".inst 0xebffaffd\n"
        ".inst 0xe1a06000\n"
        ".inst 0xebffaff1\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xebffafda\n"
        ".inst 0xe1540000\n"
        ".inst 0x30840104\n"
        ".inst 0x23a00000\n"
        ".inst 0x30850100\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002d8818, 60)
extern "C" __attribute__((naked)) void engine_func_002d8818() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a00000\n"
        ".inst 0xebfef9ce\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xebfef9cb\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00002\n"
        ".inst 0xebfef9c8\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe1a01004\n"
        ".inst 0xe1a00005\n"
        ".inst 0xebfd1f16\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002dbe50, 60)
extern "C" __attribute__((naked)) void engine_func_002dbe50() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfeec40\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfedf8c\n"
        ".inst 0xe2800b11\n"
        ".inst 0xe28000b4\n"
        ".inst 0xe5d00000\n"
        ".inst 0xe2800001\n"
        ".inst 0xe1500004\n"
        ".inst 0xd3a00001\n"
        ".inst 0xc3a00000\n"
        ".inst 0xebfec833\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002e4058, 60)
extern "C" __attribute__((naked)) void ui_func_002e4058() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a00000\n"
        ".inst 0xebfecbbe\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe3a04000\n"
        ".inst 0xebfebf09\n"
        ".inst 0xe1a01005\n"
        ".inst 0xebfe7ac6\n"
        ".inst 0xe3500000\n"
        ".inst 0x13a04f6d\n"
        ".inst 0x119040f4\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfea7b1\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002ebf28, 60)
extern "C" __attribute__((naked)) void camp_func_002ebf28() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe3a0000e\n"
        ".inst 0xebff53e1\n"
        ".inst 0xe1a06000\n"
        ".inst 0xebff53d5\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xebff53be\n"
        ".inst 0xe1540000\n"
        ".inst 0x30850104\n"
        ".inst 0x23a00000\n"
        ".inst 0x31d000b0\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002f0fa4, 60)
extern "C" __attribute__((naked)) void engine_func_002f0fa4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe97eb\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfe8b37\n"
        ".inst 0xe2800b11\n"
        ".inst 0xe28000b4\n"
        ".inst 0xe5d00000\n"
        ".inst 0xe2800001\n"
        ".inst 0xe1500004\n"
        ".inst 0xa3a00001\n"
        ".inst 0xb3a00000\n"
        ".inst 0xebfe73de\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002f6294, 60)
extern "C" __attribute__((naked)) void engine_func_002f6294() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4008\n"
        ".inst 0xebff3d66\n"
        ".inst 0xe3a00000\n"
        ".inst 0xebfe832d\n"
        ".inst 0xe1cd00b0\n"
        ".inst 0xe3a00001\n"
        ".inst 0xebfe832a\n"
        ".inst 0xe1cd00b2\n"
        ".inst 0xe3a02004\n"
        ".inst 0xe1a0100d\n"
        ".inst 0xe3a0000e\n"
        ".inst 0xebff3dbb\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8008\n"
    );
}

// DECOMP_FUNC(0x002f73a0, 60)
extern "C" __attribute__((naked)) void engine_func_002f73a0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe7eec\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xebfe7ee9\n"
        ".inst 0xebfd49fb\n"
        ".inst 0xebfec591\n"
        ".inst 0xe5900000\n"
        ".inst 0xe1500004\n"
        ".inst 0xd3a00001\n"
        ".inst 0xc3a00000\n"
        ".inst 0xebfe5adf\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002fb3f0, 60)
extern "C" __attribute__((naked)) void camp_func_002fb3f0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a01003\n"
        ".inst 0xe3a0002c\n"
        ".inst 0xebff16af\n"
        ".inst 0xe1a06000\n"
        ".inst 0xebff16a3\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xebff168c\n"
        ".inst 0xe1540000\n"
        ".inst 0x30840104\n"
        ".inst 0x23a00000\n"
        ".inst 0x30850100\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002fb42c, 60)
extern "C" __attribute__((naked)) void engine_func_002fb42c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe3a0002c\n"
        ".inst 0xebff16a0\n"
        ".inst 0xe1a06000\n"
        ".inst 0xebff1694\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xebff167d\n"
        ".inst 0xe1540000\n"
        ".inst 0x30840104\n"
        ".inst 0x23a00000\n"
        ".inst 0x30850100\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002ff2e0, 60)
extern "C" __attribute__((naked)) void engine_func_002ff2e0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a00000\n"
        ".inst 0xebfe5f1c\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe3a04000\n"
        ".inst 0xebfe5267\n"
        ".inst 0xebfd2a03\n"
        ".inst 0xe3500000\n"
        ".inst 0x13a04001\n"
        ".inst 0xe1540005\n"
        ".inst 0xd3a00001\n"
        ".inst 0xc3a00000\n"
        ".inst 0xebfe3b0f\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002ffdc4, 60)
extern "C" __attribute__((naked)) void ui_func_002ffdc4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe5c63\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfe4faf\n"
        ".inst 0xe2800b11\n"
        ".inst 0xe28000b4\n"
        ".inst 0xe1a01004\n"
        ".inst 0xe5d00000\n"
        ".inst 0xe2800001\n"
        ".inst 0xebff18da\n"
        ".inst 0xe1a00001\n"
        ".inst 0xebfe3856\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002fff90, 60)
extern "C" __attribute__((naked)) void camp_func_002fff90() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a00000\n"
        ".inst 0xebfe5bf0\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfea298\n"
        ".inst 0xe2800a09\n"
        ".inst 0xe5d0510b\n"
        ".inst 0xebfea29a\n"
        ".inst 0xe0450000\n"
        ".inst 0xe1500004\n"
        ".inst 0xa3a00001\n"
        ".inst 0xb3a00000\n"
        ".inst 0xebfe37e3\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00206d8c, 64)
extern "C" __attribute__((naked)) void engine_func_00206d8c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe1d000b0\n"
        ".inst 0xeb02b68b\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1d500b0\n"
        ".inst 0xeb02b688\n"
        ".inst 0xe1d016d4\n"
        ".inst 0xe1d426d4\n"
        ".inst 0xe0511002\n"
        ".inst 0x1a000002\n"
        ".inst 0xe1d415b0\n"
        ".inst 0xe1d005b0\n"
        ".inst 0xe0411000\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00206e30, 64)
extern "C" __attribute__((naked)) void engine_func_00206e30() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe1d000b0\n"
        ".inst 0xeb02b662\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1d500b0\n"
        ".inst 0xeb02b65f\n"
        ".inst 0xe1d016d2\n"
        ".inst 0xe1d426d2\n"
        ".inst 0xe0511002\n"
        ".inst 0x1a000002\n"
        ".inst 0xe1d415b0\n"
        ".inst 0xe1d005b0\n"
        ".inst 0xe0411000\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00206e70, 64)
extern "C" __attribute__((naked)) void engine_func_00206e70() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe1d000b0\n"
        ".inst 0xeb02b652\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1d500b0\n"
        ".inst 0xeb02b64f\n"
        ".inst 0xe1d016d5\n"
        ".inst 0xe1d426d5\n"
        ".inst 0xe0511002\n"
        ".inst 0x1a000002\n"
        ".inst 0xe1d415b0\n"
        ".inst 0xe1d005b0\n"
        ".inst 0xe0411000\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00206eb0, 64)
extern "C" __attribute__((naked)) void engine_func_00206eb0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe1d000b0\n"
        ".inst 0xeb02b642\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1d500b0\n"
        ".inst 0xeb02b63f\n"
        ".inst 0xe1d016d3\n"
        ".inst 0xe1d426d3\n"
        ".inst 0xe0511002\n"
        ".inst 0x1a000002\n"
        ".inst 0xe1d415b0\n"
        ".inst 0xe1d005b0\n"
        ".inst 0xe0411000\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00206ef0, 64)
extern "C" __attribute__((naked)) void engine_func_00206ef0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe1d000b0\n"
        ".inst 0xeb02b632\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1d500b0\n"
        ".inst 0xeb02b62f\n"
        ".inst 0xe1d016d1\n"
        ".inst 0xe1d426d1\n"
        ".inst 0xe0511002\n"
        ".inst 0x1a000002\n"
        ".inst 0xe1d415b0\n"
        ".inst 0xe1d005b0\n"
        ".inst 0xe0411000\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00230aa8, 64)
extern "C" __attribute__((naked)) void camp_func_00230aa8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04001\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe3a00017\n"
        ".inst 0xeb024101\n"
        ".inst 0xe1a06000\n"
        ".inst 0xeb0240f5\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xeb0240de\n"
        ".inst 0xe1540000\n"
        ".inst 0x30840104\n"
        ".inst 0x30800184\n"
        ".inst 0x23a00000\n"
        ".inst 0x30850180\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00234278, 64)
extern "C" __attribute__((naked)) void engine_func_00234278() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe24dd008\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe4c01004\n"
        ".inst 0xeb021b83\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5801008\n"
        ".inst 0xe2404004\n"
        ".inst 0xe580100c\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xeb021ab6\n"
        ".inst 0xe1c000d0\n"
        ".inst 0xe1c400f4\n"
        ".inst 0xe28dd008\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002348a0, 64)
extern "C" __attribute__((naked)) void camp_func_002348a0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe1a01002\n"
        ".inst 0xe1a02003\n"
        ".inst 0xe59d3008\n"
        ".inst 0xe6bf2072\n"
        ".inst 0xe6bf1071\n"
        ".inst 0xe6bf0070\n"
        ".inst 0xe6bf3073\n"
        ".inst 0xeb01a689\n"
        ".inst 0xe1d415ba\n"
        ".inst 0xe1c405b6\n"
        ".inst 0xe2810001\n"
        ".inst 0xe1c405ba\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002348e0, 64)
extern "C" __attribute__((naked)) void camp_func_002348e0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe1a01002\n"
        ".inst 0xe1a02003\n"
        ".inst 0xe59d3008\n"
        ".inst 0xe6bf2072\n"
        ".inst 0xe6bf1071\n"
        ".inst 0xe6bf0070\n"
        ".inst 0xe6bf3073\n"
        ".inst 0xeb01a679\n"
        ".inst 0xe1d415ba\n"
        ".inst 0xe1c405b4\n"
        ".inst 0xe2810001\n"
        ".inst 0xe1c405ba\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0023de18, 64)
extern "C" __attribute__((naked)) void script_vm_func_0023de18() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe3a04000\n"
        ".inst 0xeb01e414\n"
        ".inst 0xe3500000\n"
        ".inst 0x13500001\n"
        ".inst 0x0a000007\n"
        ".inst 0xe3500002\n"
        ".inst 0x1a000005\n"
        ".inst 0xeb01e408\n"
        ".inst 0xe1d004b6\n"
        ".inst 0xebffb09f\n"
        ".inst 0xe1d000b4\n"
        ".inst 0xe3100001\n"
        ".inst 0x13a04001\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0024f7a8, 64)
extern "C" __attribute__((naked)) void camp_func_0024f7a8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a01002\n"
        ".inst 0xe3a0002e\n"
        ".inst 0xeb01c5c1\n"
        ".inst 0xe1a06000\n"
        ".inst 0xeb01c5b5\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xeb01c59e\n"
        ".inst 0xe1540000\n"
        ".inst 0x30840084\n"
        ".inst 0x30800184\n"
        ".inst 0x23a00000\n"
        ".inst 0x30850100\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00253f24, 64)
extern "C" __attribute__((naked)) void engine_func_00253f24() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5d00000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000008\n"
        ".inst 0xe594002c\n"
        ".inst 0xeb01c107\n"
        ".inst 0xe5940048\n"
        ".inst 0xe3a05000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xeb01c102\n"
        ".inst 0xe5845048\n"
        ".inst 0xe5c45000\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00262a04, 64)
extern "C" __attribute__((naked)) void camp_func_00262a04() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a00024\n"
        ".inst 0xeb01792a\n"
        ".inst 0xe1a06000\n"
        ".inst 0xeb01791e\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xeb017907\n"
        ".inst 0xe1540000\n"
        ".inst 0x30840184\n"
        ".inst 0x23e00000\n"
        ".inst 0x30850200\n"
        ".inst 0x35d00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x0027db78, 64)
extern "C" __attribute__((naked)) void script_vm_func_0027db78() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb0113e6\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe3a03010\n"
        ".inst 0xe1a01002\n"
        ".inst 0xe082c102\n"
        ".inst 0xe2533001\n"
        ".inst 0xe080c10c\n"
        ".inst 0xe28c4c0f\n"
        ".inst 0xe5cc1f20\n"
        ".inst 0xe1c412b4\n"
        ".inst 0xe5cc1f23\n"
        ".inst 0xe2822001\n"
        ".inst 0xe1c412b8\n"
        ".inst 0x1afffff5\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0028889c, 64)
extern "C" __attribute__((naked)) void camp_func_0028889c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe3a00024\n"
        ".inst 0xeb00e184\n"
        ".inst 0xe1a06000\n"
        ".inst 0xeb00e178\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xeb00e161\n"
        ".inst 0xe1540000\n"
        ".inst 0x30840184\n"
        ".inst 0x23a00000\n"
        ".inst 0x30850200\n"
        ".inst 0x32800004\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x0028ca7c, 64)
extern "C" __attribute__((naked)) void engine_func_0028ca7c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xeb00c3ac\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe580103c\n"
        ".inst 0xe5801040\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a03803\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe1a01005\n"
        ".inst 0xebfc4c27\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb00c31e\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002a2268, 64)
extern "C" __attribute__((naked)) void ui_func_002a2268() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900000\n"
        ".inst 0xe0410000\n"
        ".inst 0xe5941008\n"
        ".inst 0xeb009263\n"
        ".inst 0xe08411a0\n"
        ".inst 0xe2000007\n"
        ".inst 0xe5d13014\n"
        ".inst 0xe3a02001\n"
        ".inst 0xe1c30012\n"
        ".inst 0xe5c10014\n"
        ".inst 0xe5940010\n"
        ".inst 0xe2400001\n"
        ".inst 0xe5840010\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002dbfa8, 64)
extern "C" __attribute__((naked)) void engine_func_002dbfa8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a00000\n"
        ".inst 0xebfeebea\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xebfeebe7\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe3a00002\n"
        ".inst 0xebfeebe4\n"
        ".inst 0xe1550004\n"
        ".inst 0xd1540000\n"
        ".inst 0xc3a00000\n"
        ".inst 0xd3a00001\n"
        ".inst 0xebfec7dc\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002e4724, 64)
extern "C" __attribute__((naked)) void engine_func_002e4724() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe1d000b0\n"
        ".inst 0xebff4025\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1d500b0\n"
        ".inst 0xebff4022\n"
        ".inst 0xe1d416d4\n"
        ".inst 0xe1d026d4\n"
        ".inst 0xe0511002\n"
        ".inst 0x1a000002\n"
        ".inst 0xe1d005b0\n"
        ".inst 0xe1d415b0\n"
        ".inst 0xe0401001\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002e481c, 64)
extern "C" __attribute__((naked)) void engine_func_002e481c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe1d000b0\n"
        ".inst 0xebff3fe7\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1d500b0\n"
        ".inst 0xebff3fe4\n"
        ".inst 0xe1d416d2\n"
        ".inst 0xe1d026d2\n"
        ".inst 0xe0511002\n"
        ".inst 0x1a000002\n"
        ".inst 0xe1d005b0\n"
        ".inst 0xe1d415b0\n"
        ".inst 0xe0401001\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002e485c, 64)
extern "C" __attribute__((naked)) void engine_func_002e485c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe1d000b0\n"
        ".inst 0xebff3fd7\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1d500b0\n"
        ".inst 0xebff3fd4\n"
        ".inst 0xe1d416d5\n"
        ".inst 0xe1d026d5\n"
        ".inst 0xe0511002\n"
        ".inst 0x1a000002\n"
        ".inst 0xe1d005b0\n"
        ".inst 0xe1d415b0\n"
        ".inst 0xe0401001\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002e489c, 64)
extern "C" __attribute__((naked)) void engine_func_002e489c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe1d000b0\n"
        ".inst 0xebff3fc7\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1d500b0\n"
        ".inst 0xebff3fc4\n"
        ".inst 0xe1d416d3\n"
        ".inst 0xe1d026d3\n"
        ".inst 0xe0511002\n"
        ".inst 0x1a000002\n"
        ".inst 0xe1d005b0\n"
        ".inst 0xe1d415b0\n"
        ".inst 0xe0401001\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002e48dc, 64)
extern "C" __attribute__((naked)) void engine_func_002e48dc() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe1d000b0\n"
        ".inst 0xebff3fb7\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1d500b0\n"
        ".inst 0xebff3fb4\n"
        ".inst 0xe1d416d1\n"
        ".inst 0xe1d026d1\n"
        ".inst 0xe0511002\n"
        ".inst 0x1a000002\n"
        ".inst 0xe1d005b0\n"
        ".inst 0xe1d415b0\n"
        ".inst 0xe0401001\n"
        ".inst 0xe1a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002f1018, 64)
extern "C" __attribute__((naked)) void engine_func_002f1018() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a00000\n"
        ".inst 0xebfe97ce\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xebfe97cb\n"
        ".inst 0xe3540010\n"
        ".inst 0xe1a05000\n"
        ".inst 0x2a000004\n"
        ".inst 0xebfe8b15\n"
        ".inst 0xe0800104\n"
        ".inst 0xe2800b12\n"
        ".inst 0xe2800f5f\n"
        ".inst 0xe5805000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002f123c, 64)
extern "C" __attribute__((naked)) void engine_func_002f123c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe9745\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfe8a91\n"
        ".inst 0xe2801901\n"
        ".inst 0xe3a02001\n"
        ".inst 0xe2811e9d\n"
        ".inst 0xe1a00412\n"
        ".inst 0xe1c120d0\n"
        ".inst 0xe1a0cfc0\n"
        ".inst 0xe1800002\n"
        ".inst 0xe183200c\n"
        ".inst 0xe8810005\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002f78e8, 64)
extern "C" __attribute__((naked)) void engine_func_002f78e8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe7d9a\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfe70e6\n"
        ".inst 0xe2800901\n"
        ".inst 0xe2800e9d\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe1e01411\n"
        ".inst 0xe1c020d0\n"
        ".inst 0xe1a0cfc1\n"
        ".inst 0xe0011002\n"
        ".inst 0xe003200c\n"
        ".inst 0xe8800006\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002176a8, 68)
extern "C" __attribute__((naked)) void camp_func_002176a8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a01002\n"
        ".inst 0xe3a00016\n"
        ".inst 0xeb02a601\n"
        ".inst 0xe1a06000\n"
        ".inst 0xeb02a5f5\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xeb02a5de\n"
        ".inst 0xe1540000\n"
        ".inst 0x30840184\n"
        ".inst 0x30800204\n"
        ".inst 0x30850100\n"
        ".inst 0x32800013\n"
        ".inst 0x23a00000\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x0023d190, 68)
extern "C" __attribute__((naked)) void engine_func_0023d190() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe590000c\n"
        ".inst 0xe3a05000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xeb021c6c\n"
        ".inst 0xe584500c\n"
        ".inst 0xe5940008\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000001\n"
        ".inst 0xeb020e2a\n"
        ".inst 0xe5845008\n"
        ".inst 0xe5a45010\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe584000c\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x0025cdf8, 68)
extern "C" __attribute__((naked)) void camp_func_0025cdf8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a01002\n"
        ".inst 0xe3a00016\n"
        ".inst 0xeb01902d\n"
        ".inst 0xe1a06000\n"
        ".inst 0xeb019021\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe1a00006\n"
        ".inst 0xeb01900a\n"
        ".inst 0xe1540000\n"
        ".inst 0x30840184\n"
        ".inst 0x30800204\n"
        ".inst 0x30850100\n"
        ".inst 0x32800001\n"
        ".inst 0x23a00000\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002623ec, 68)
extern "C" __attribute__((naked)) void battle_func_002623ec() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d40f8\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5830000\n"
        ".inst 0xe1a06001\n"
        ".inst 0xe1a04003\n"
        ".inst 0xe1a00002\n"
        ".inst 0xeb012ff8\n"
        ".inst 0xe1b02000\n"
        ".inst 0x03a00001\n"
        ".inst 0x0a000004\n"
        ".inst 0xe3a03001\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe1a00005\n"
        ".inst 0xe58d4000\n"
        ".inst 0xebffdafa\n"
        ".inst 0xe8bd80f8\n"
    );
}

// DECOMP_FUNC(0x002b4a0c, 68)
extern "C" __attribute__((naked)) void func_002b4a0c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe24ddef9\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a0500d\n"
        ".inst 0xe1a00005\n"
        ".inst 0xebfa1d33\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe58d4004\n"
        ".inst 0xe5cd0ee4\n"
        ".inst 0xebfa4a1c\n"
        ".inst 0xebfa1d6e\n"
        ".inst 0xebfa1d79\n"
        ".inst 0xe1a01005\n"
        ".inst 0xe28d0d3e\n"
        ".inst 0xebfa1d46\n"
        ".inst 0xe28ddef9\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002c35d4, 68)
extern "C" __attribute__((naked)) void camp_func_002c35d4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xee1d0f70\n"
        ".inst 0xe5941004\n"
        ".inst 0xe1500001\n"
        ".inst 0x0a000005\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebf96195\n"
        ".inst 0xe3500000\n"
        ".inst 0x1e1d0f70\n"
        ".inst 0x15840004\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5940008\n"
        ".inst 0xe2800001\n"
        ".inst 0xe5840008\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002cddd8, 68)
extern "C" __attribute__((naked)) void engine_func_002cddd8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a00000\n"
        ".inst 0xebff245e\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xebff245b\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe20560ff\n"
        ".inst 0xebfe19b9\n"
        ".inst 0xe7900106\n"
        ".inst 0xe1500004\n"
        ".inst 0x2a000002\n"
        ".inst 0xe20550ff\n"
        ".inst 0xebfe19b4\n"
        ".inst 0xe7804105\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002cfce0, 68)
extern "C" __attribute__((naked)) void ui_func_002cfce0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebff1c9c\n"
        ".inst 0xe350006d\n"
        ".inst 0xe1a04000\n"
        ".inst 0xaa000004\n"
        ".inst 0xebff0fe6\n"
        ".inst 0xe1a01004\n"
        ".inst 0xebfecba3\n"
        ".inst 0xe590027c\n"
        ".inst 0xea000001\n"
        ".inst 0xe240006d\n"
        ".inst 0xebff6333\n"
        ".inst 0xe1d004b6\n"
        ".inst 0xebfef88d\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002ef230, 68)
extern "C" __attribute__((naked)) void engine_func_002ef230() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe3a00000\n"
        ".inst 0xebfe9f48\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xebfe9f45\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00002\n"
        ".inst 0xebfe9f42\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfda8b8\n"
        ".inst 0xe1a00005\n"
        ".inst 0xebfe3a2e\n"
        ".inst 0xebfff0f1\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00221f28, 72)
extern "C" __attribute__((naked)) void engine_func_00221f28() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb01d40a\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xeb01d407\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb00c11f\n"
        ".inst 0xe1a04000\n"
        ".inst 0xeb019db3\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb019d4e\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb01affa\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00245de4, 72)
extern "C" __attribute__((naked)) void script_vm_func_00245de4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe3a04000\n"
        ".inst 0xeb01c421\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a00000a\n"
        ".inst 0xe3500001\n"
        ".inst 0x0a000007\n"
        ".inst 0xe3500002\n"
        ".inst 0x1a000006\n"
        ".inst 0xeb01c414\n"
        ".inst 0xe1d004b6\n"
        ".inst 0xebff90ab\n"
        ".inst 0xe5d00003\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a000000\n"
        ".inst 0xe3a04001\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0028cd9c, 72)
extern "C" __attribute__((naked)) void camp_func_0028cd9c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d40f8\n"
        ".inst 0xe1a05002\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5820000\n"
        ".inst 0xe5830000\n"
        ".inst 0xe1a04003\n"
        ".inst 0xe1a00001\n"
        ".inst 0xeb009ea4\n"
        ".inst 0xe1b01000\n"
        ".inst 0x03a00001\n"
        ".inst 0x0a000004\n"
        ".inst 0xe1a03005\n"
        ".inst 0xe3a02001\n"
        ".inst 0xe1a00006\n"
        ".inst 0xe58d4000\n"
        ".inst 0xebfe97c6\n"
        ".inst 0xe8bd80f8\n"
    );
}

// DECOMP_FUNC(0x002cdd90, 72)
extern "C" __attribute__((naked)) void script_vm_func_002cdd90() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d40f8\n"
        ".inst 0xe3a00000\n"
        ".inst 0xebff2470\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe3a0001e\n"
        ".inst 0xebff9b0b\n"
        ".inst 0xe1a05000\n"
        ".inst 0xebfeee23\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebffc8db\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe58d0000\n"
        ".inst 0xe3a03006\n"
        ".inst 0xe1a02004\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe1a00005\n"
        ".inst 0xebfe1ca5\n"
        ".inst 0xe8bd80f8\n"
    );
}

// DECOMP_FUNC(0x002e1e60, 72)
extern "C" __attribute__((naked)) void func_002e1e60() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe24dd008\n"
        ".inst 0xe1a06001\n"
        ".inst 0xe1a04002\n"
        ".inst 0xe1a05003\n"
        ".inst 0xebfdd632\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe1d002f2\n"
        ".inst 0xebff31b0\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe1a03006\n"
        ".inst 0xe3a01013\n"
        ".inst 0xe3a00002\n"
        ".inst 0xe1cd40f0\n"
        ".inst 0xebff3377\n"
        ".inst 0xe28dd008\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x002e2808, 72)
extern "C" __attribute__((naked)) void engine_func_002e2808() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe24dd008\n"
        ".inst 0xe3a00000\n"
        ".inst 0xebfed1d1\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe3a00001\n"
        ".inst 0xebfed1ce\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe58d1000\n"
        ".inst 0xe58d1004\n"
        ".inst 0xe20010ff\n"
        ".inst 0xe3a03000\n"
        ".inst 0xe20400ff\n"
        ".inst 0xe1a02003\n"
        ".inst 0xebfe8b31\n"
        ".inst 0xe28dd008\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x002f78a0, 72)
extern "C" __attribute__((naked)) void engine_func_002f78a0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfe7dac\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfe70f8\n"
        ".inst 0xe2800901\n"
        ".inst 0xe2800e9d\n"
        ".inst 0xe3a03001\n"
        ".inst 0xe8900006\n"
        ".inst 0xe1a00413\n"
        ".inst 0xe0011000\n"
        ".inst 0xe0020fc0\n"
        ".inst 0xe1900001\n"
        ".inst 0x13a00001\n"
        ".inst 0x03a00000\n"
        ".inst 0xebfe599c\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}
