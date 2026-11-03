#include "types.h"

// Batch 31 A: raw ARM encodings with explicit bounded return/data tails.

// DECOMP_FUNC(0x0034afe4, 8)
extern "C" void engine_func_002b2520(void* sub);

extern "C" void func_0034afe4(void* sub) {
    engine_func_002b2520(sub);
}

// DECOMP_FUNC(0x0035311c, 8)
extern "C" void engine_func_0035311c(void) {
}

// DECOMP_FUNC(0x00394ee0, 12)
extern "C" u32 engine_func_002c583c(u32 val);

extern "C" u32 script_vm_func_00394ee0(void) {
    return engine_func_002c583c(1);
}

// DECOMP_FUNC(0x003968c0, 20)
extern "C" void script_vm_func_003968d4(void* obj);

extern "C" void script_vm_func_003968c0(void* obj) {
    if ((*reinterpret_cast<u32*>(obj) & 1) == 0) {
        script_vm_func_003968d4(obj);
    }
}

// DECOMP_FUNC(0x003eafac, 20)
extern "C" void func_002a3428(u32* p0, u32* p1);

extern "C" void func_003eafac(u32* p0, u32* p1) {
    if (p1 != nullptr) {
        func_002a3428(p0 + 1, p1);
    }
}

// DECOMP_FUNC(0x0033858c, 24)
extern "C" void ui_func_00297920(void* p);

extern "C" void engine_func_0033858c(void* p) {
    void* sub = *reinterpret_cast<void**>(reinterpret_cast<u8*>(p) + 0x4394);
    if (sub != nullptr) {
        ui_func_00297920(sub);
    }
}

// DECOMP_FUNC(0x00349740, 24)
extern "C" void func_00349740(void* p) {
    engine_func_002b2520(p);
}

// DECOMP_FUNC(0x00351e98, 24)
extern "C" u32 func_00352150(void* p);

extern "C" u32 func_00351e98(void* p) {
    if (p == nullptr) {
        return 0xE0409FFFu;
    }
    return func_00352150(p);
}

// DECOMP_FUNC(0x00351ee0, 24)
extern "C" u32 func_003521c8(void* p);

extern "C" u32 func_00351ee0(void* p) {
    if (p == nullptr) {
        return 0xE0409FFFu;
    }
    return func_003521c8(p);
}

// DECOMP_FUNC(0x003c0a90, 24)
extern "C" void* Tbb_GetSubTable(void* sub, u32 index);

extern "C" void* func_003c0a90(void* p) {
    void* sub = *reinterpret_cast<void**>(reinterpret_cast<u8*>(p) + 8);
    if (sub != nullptr) {
        return Tbb_GetSubTable(sub, 0);
    }
    return nullptr;
}

// DECOMP_FUNC(0x003d6634, 24)
extern "C" void* camp_func_002a06dc(void* sub, u32 idx);

extern "C" void* func_003d6634(void* p) {
    void* sub = *reinterpret_cast<void**>(reinterpret_cast<u8*>(p) + 0x730);
    if (sub != nullptr) {
        return camp_func_002a06dc(sub, 0);
    }
    return nullptr;
}

// DECOMP_FUNC(0x00308c7c, 28)
extern "C" void script_vm_func_00308d00(void* obj);

extern "C" void script_vm_func_00308c7c(void) {
    void* obj = *reinterpret_cast<void**>(0x00447E28);
    if (obj != nullptr) {
        script_vm_func_00308d00(obj);
    }
}

// DECOMP_FUNC(0x0030f518, 28)
extern "C" void script_vm_func_0030f518(void) {
    void* obj = *reinterpret_cast<void**>(0x00447060);
    if (obj != nullptr) {
        script_vm_func_00308d00(obj);
    }
}

// DECOMP_FUNC(0x0031074c, 28)
extern "C" u32 script_vm_func_00289a48(void);
extern "C" void script_vm_func_00289a18(u32);

extern "C" u32 script_vm_func_0031074c(void) {
    if (script_vm_func_00289a48() != 0) {
        script_vm_func_00289a18(1);
    }
    return 1;
}

// DECOMP_FUNC(0x0034b3a0, 28)
extern "C" void* func_0034b3a0(void* p0, void* p1) {
    if (p1 != nullptr) {
        typedef void* (*Callback)(void*);
        Callback cb = *reinterpret_cast<Callback*>(0x0044E994);
        return cb(p1);
    }
    return nullptr;
}

// DECOMP_FUNC(0x003604a4, 28)
extern "C" s32 func_003607f8(u32 arg0);
extern "C" u32 engine_func_002bce48(u32);

extern "C" u32 func_003604a4(u32 arg0) {
    s32 res = func_003607f8(arg0);
    if (res < 0) {
        return engine_func_002bce48(1);
    }
    return 0;
}

// DECOMP_FUNC(0x003605ec, 28)
extern "C" s32 func_003609a4(u32 arg0);

extern "C" u32 func_003605ec(u32 arg0) {
    s32 res = func_003609a4(arg0);
    if (res < 0) {
        return engine_func_002bce48(1);
    }
    return 0;
}

// DECOMP_FUNC(0x003606b0, 28)
extern "C" s32 func_00360a10(u32 arg0);

extern "C" u32 func_003606b0(u32 arg0) {
    s32 res = func_00360a10(arg0);
    if (res < 0) {
        return engine_func_002bce48(1);
    }
    return 0;
}

// DECOMP_FUNC(0x003606cc, 28)
extern "C" s32 func_00360a4c(u32 arg0);

extern "C" u32 func_003606cc(u32 arg0) {
    s32 res = func_00360a4c(arg0);
    if (res < 0) {
        return engine_func_002bce48(1);
    }
    return 0;
}

// DECOMP_FUNC(0x003606e8, 28)
extern "C" s32 func_00360a7c(u32 arg0);

extern "C" u32 func_003606e8(u32 arg0) {
    s32 res = func_00360a7c(arg0);
    if (res < 0) {
        return engine_func_002bce48(1);
    }
    return 0;
}

// DECOMP_FUNC(0x0036072c, 28)
extern "C" s32 func_00360b18(void* out_val);

extern "C" s32 engine_func_0036072c(void) {
    s8 out_val = 0;
    s32 res = func_00360b18(&out_val);
    if (res < 0) {
        engine_func_002bce48(1);
    }
    return out_val;
}

// DECOMP_FUNC(0x00360748, 28)
extern "C" s32 func_00360b54(u32 arg0);

extern "C" u32 func_00360748(u32 arg0) {
    s32 res = func_00360b54(arg0);
    if (res < 0) {
        return engine_func_002bce48(1);
    }
    return 0;
}

// DECOMP_FUNC(0x00360764, 28)
extern "C" s32 func_00360b90(u32 arg0);

extern "C" u32 func_00360764(u32 arg0) {
    s32 res = func_00360b90(arg0);
    if (res < 0) {
        return engine_func_002bce48(1);
    }
    return 0;
}

// DECOMP_FUNC(0x003607c0, 28)
extern "C" s32 func_00360c08(u32 arg0);

extern "C" u32 func_003607c0(u32 arg0) {
    s32 res = func_00360c08(arg0);
    if (res < 0) {
        return engine_func_002bce48(1);
    }
    return 0;
}

// DECOMP_FUNC(0x003607dc, 28)
extern "C" s32 func_00360c44(u32 arg0);

extern "C" u32 nn_sdk_func_003607dc(u32 arg0) {
    s32 res = func_00360c44(arg0);
    if (res < 0) {
        return engine_func_002bce48(1);
    }
    return 0;
}

// DECOMP_FUNC(0x00360cbc, 28)
extern "C" s32 func_00360c80(u32 arg0);

extern "C" u32 func_00360cbc(u32 arg0) {
    s32 res = func_00360c80(arg0);
    if (res < 0) {
        return engine_func_002bce48(1);
    }
    return 0;
}

// DECOMP_FUNC(0x0037e7b0, 28)
extern "C" void func_00235ddc(void* obj);

extern "C" u32 func_0037e7b0(void* obj, u32 mode, void* target) {
    if (mode == 2) {
        func_00235ddc(obj);
    }
    *reinterpret_cast<u32*>(reinterpret_cast<u8*>(target) + 0x98) = 0;
    return 0;
}

// DECOMP_FUNC(0x0030f904, 32)
extern "C" void ui_func_0039cb84(void* obj);

extern "C" void script_vm_func_0030f904(void) {
    void* obj = *reinterpret_cast<void**>(0x0044CDF0);
    if (obj != nullptr) {
        ui_func_0039cb84(reinterpret_cast<u8*>(obj) + 0x40);
    }
}

// DECOMP_FUNC(0x00338638, 32)
extern "C" float ui_func_0027fbbc(void* sub);

extern "C" float func_00338638(void* p) {
    void* sub = *reinterpret_cast<void**>(reinterpret_cast<u8*>(p) + 0x4394);
    if (sub == nullptr) {
        return -1.0f;
    }
    return ui_func_0027fbbc(sub);
}

// DECOMP_FUNC(0x00355fc0, 32)
extern "C" u32 func_00355fc0(void* self) {
    if (self == nullptr) {
        return 0xE0E046BCu;
    }
    typedef u32 (*Method)(void*);
    Method* vtable = *reinterpret_cast<Method**>(self);
    return vtable[3](self);
}

// DECOMP_FUNC(0x003560bc, 32)
extern "C" u32 func_003560bc(void* self) {
    if (self == nullptr) {
        return 0xE0E046BCu;
    }
    typedef u32 (*Method)(void*);
    Method* vtable = *reinterpret_cast<Method**>(self);
    return vtable[5](self);
}

// DECOMP_FUNC(0x0035b084, 32)
extern "C" u32 func_0035afc8(u32 mask);

extern "C" u32 func_0035b084(u32 index) {
    if (index >= 4) {
        return 0xD8E06BEDu;
    }
    return func_0035afc8(1u << index);
}

// DECOMP_FUNC(0x0035b0a4, 32)
extern "C" u32 func_00128c48(u32 mask);

extern "C" u32 func_0035b0a4(u32 index) {
    if (index >= 4) {
        return 0xD8E06BEDu;
    }
    return func_00128c48(1u << index);
}

// DECOMP_FUNC(0x0038b618, 32)
extern "C" void camp_func_0036136c(void);
extern "C" u32 func_003613d4(void);
extern "C" u32 func_003613e4(void);

extern "C" u32 func_0038b618(void) {
    camp_func_0036136c();
    u32 res = func_003613d4();
    if (res != 0) {
        return res;
    }
    return func_003613e4();
}

// DECOMP_FUNC(0x0030ab70, 36)
extern "C" u32 script_vm_func_00290694(void);

extern "C" u32 camp_func_0030ab70(void) {
    u8* obj = *reinterpret_cast<u8**>(0x0043DD50);
    if (obj[0x5C4] != 0) {
        return 0;
    }
    return script_vm_func_00290694();
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
