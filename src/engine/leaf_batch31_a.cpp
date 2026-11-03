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
extern "C" u32 func_002cbfcc(u32 arg0);

extern "C" u32 camp_func_0030f5ec(u32 arg0) {
    u8* obj = *reinterpret_cast<u8**>(0x00447E28);
    if (obj != nullptr && obj[0x3C] != 0) {
        return func_002cbfcc(arg0);
    }
    return arg0;
}

// DECOMP_FUNC(0x00357698, 36)
extern "C" u32 engine_func_00155bd8(void* ctx, void* obj);

extern "C" u32 func_00357698(void* obj) {
    if (*reinterpret_cast<void**>(reinterpret_cast<u8*>(obj) + 8) != nullptr) {
        return engine_func_00155bd8(reinterpret_cast<void*>(0x004E6EF0), obj);
    }
    return reinterpret_cast<uintptr_t>(obj);
}

// DECOMP_FUNC(0x00359184, 36)
extern "C" u32 func_0015f740(void* obj);

extern "C" u32 func_00359184(void) {
    void* obj = *reinterpret_cast<void**>(0x00473848);
    if (obj == nullptr) {
        return 0xE0810BF8u;
    }
    return func_0015f740(obj);
}

// DECOMP_FUNC(0x0035bb24, 36)
extern "C" u32 func_0035c048(void* self, u32 arg1, u32 arg2);

extern "C" u32 func_0035bb24(void* self, u32 arg1) {
    u32* fields = reinterpret_cast<u32*>(reinterpret_cast<u8*>(self) + 0x10);
    u32 cur = fields[0] + 1;
    u32 max = fields[1];
    fields[0] = cur;
    if (cur == max) {
        return 6;
    }
    return func_0035c048(self, arg1, 4);
}

// DECOMP_FUNC(0x0035bb74, 36)
extern "C" u32 func_0035bb74(void* self, u32 arg1) {
    u32* fields = reinterpret_cast<u32*>(reinterpret_cast<u8*>(self) + 0x10);
    u32 cur = fields[0] + 1;
    u32 max = fields[1];
    fields[0] = cur;
    if (cur == max) {
        return 6;
    }
    return func_0035c048(self, arg1, 2);
}

// DECOMP_FUNC(0x0037a3fc, 36)
extern "C" u32 engine_func_0037a420(void* arg0);
extern "C" u32 engine_func_002c3628(void* arg);

extern "C" u32 func_0037a3fc(void* arg0, void* arg1) {
    u32 res = engine_func_0037a420(arg0);
    if (res != 0) {
        return res;
    }
    return engine_func_002c3628(reinterpret_cast<u8*>(arg1) + 0xC);
}

// DECOMP_FUNC(0x0039f834, 36)
extern "C" u32 script_vm_func_002c0ba8(u32 arg0);
extern "C" u32 battle_func_002931cc(u32 arg0);

extern "C" u32 script_vm_func_0039f834(void) {
    u32 res = script_vm_func_002c0ba8(0x400);
    if (res == 0) {
        return 0;
    }
    return battle_func_002931cc(0x76);
}

// DECOMP_FUNC(0x003af184, 36)
extern "C" u32 func_002dc3bc(void* obj);

extern "C" u32 func_003af184(void) {
    u8* obj = *reinterpret_cast<u8**>(0x00439CA8);
    if (obj != nullptr) {
        return func_002dc3bc(obj + 0x2460);
    }
    return 0;
}

// DECOMP_FUNC(0x003e7038, 36)
extern "C" void func_003e70f8(void* sub);

extern "C" u32 func_003e7038(void* self) {
    if (*reinterpret_cast<void**>(reinterpret_cast<u8*>(self) + 4) == nullptr) {
        return 0;
    }
    func_003e70f8(reinterpret_cast<u8*>(self) + 4);
    return 1;
}

// DECOMP_FUNC(0x003e7080, 36)
extern "C" void func_003e7128(void* sub);

extern "C" u32 func_003e7080(void* self) {
    if (*reinterpret_cast<void**>(reinterpret_cast<u8*>(self) + 4) == nullptr) {
        return 0;
    }
    func_003e7128(reinterpret_cast<u8*>(self) + 4);
    return 1;
}

// DECOMP_FUNC(0x003e70a4, 36)
extern "C" void engine_func_003e71c4(void* sub);

extern "C" u32 func_003e70a4(void* self) {
    if (*reinterpret_cast<void**>(reinterpret_cast<u8*>(self) + 4) == nullptr) {
        return 0;
    }
    engine_func_003e71c4(reinterpret_cast<u8*>(self) + 4);
    return 1;
}

// DECOMP_FUNC(0x00302674, 40)
extern "C" void ui_func_00257390(void* old_obj);
extern "C" void* effP2A_func_00249324(void* arg);

extern "C" void engine_func_00302674(void* self, void* new_arg) {
    void** slot = reinterpret_cast<void**>(reinterpret_cast<u8*>(self) + 0x44);
    if (*slot != nullptr) {
        ui_func_00257390(*slot);
    }
    *slot = effP2A_func_00249324(new_arg);
}

// DECOMP_FUNC(0x003408c4, 40)
extern "C" void* ui_func_00380b4c(void* arg0);
extern "C" void* ui_func_002c5f58(void* p, const void* desc, u32 arg2, u32 arg3);

extern "C" void* ui_func_003408c4(void* arg0) {
    void* base = ui_func_00380b4c(arg0);
    u8* res = reinterpret_cast<u8*>(ui_func_002c5f58(
        reinterpret_cast<u8*>(base) + 0x20,
        reinterpret_cast<const void*>(0x00376B78),
        4,
        8
    ));
    return res - 0x20;
}

// DECOMP_FUNC(0x0034752c, 40)
extern "C" void* ui_func_0034752c(void* arg0) {
    void* base = ui_func_00380b4c(arg0);
    u8* res = reinterpret_cast<u8*>(ui_func_002c5f58(
        reinterpret_cast<u8*>(base) + 0x20,
        reinterpret_cast<const void*>(0x00376B78),
        4,
        4
    ));
    return res - 0x20;
}

// DECOMP_FUNC(0x0034a1f0, 40)
extern "C" void func_0034a138(void* self);

extern "C" void func_0034a1f0(void* self) {
    *reinterpret_cast<void**>(self) = reinterpret_cast<void*>(0x00420514);
    func_0034a138(self);
    engine_func_002b2520(self);
}

// DECOMP_FUNC(0x00357b2c, 40)
extern "C" u32 func_00357b54(void* self, u32 arg1, u32 arg2);

extern "C" u32 engine_func_00357b2c(void* self, u32 arg1, u32 arg2) {
    if (*reinterpret_cast<void**>(reinterpret_cast<u8*>(self) + 4) == nullptr) {
        return 0xC8810BEAu;
    }
    if (arg1 != 0 && arg2 >= 0x70) {
        return func_00357b54(self, arg1, arg2);
    }
    return 0xE0E10BFDu;
}

// DECOMP_FUNC(0x00360704, 40)
extern "C" s32 func_00360ab8(u32 arg0);

extern "C" u32 engine_func_00360704(u32 arg0) {
    s32 res = func_00360ab8(arg0);
    if (static_cast<u32>(res) == 0xC9405001u) {
        return 0xC9405001u;
    }
    if (res < 0) {
        engine_func_002bce48(1);
    }
    return 0;
}

// DECOMP_FUNC(0x0037024c, 40)
extern "C" u32 script_vm_func_002c3568(void** p_target);

extern "C" u32 func_0037024c(void* base) {
    u8* ptr = reinterpret_cast<u8*>(base) + 8;
    s32 rel = *reinterpret_cast<s32*>(ptr);
    void* target = (rel != 0) ? (ptr + rel) : nullptr;
    if (target != nullptr) {
        return script_vm_func_002c3568(&target);
    }
    return 0;
}

// DECOMP_FUNC(0x0037e3f8, 40)
extern "C" void func_002c68bc(void* p, const void* desc, u32 arg2, u32 arg3);

extern "C" void* func_0037e3f8(void* self) {
    func_002c68bc(
        reinterpret_cast<u8*>(self) + 0x64,
        reinterpret_cast<const void*>(0x00361C60),
        12,
        2
    );
    return self;
}

// DECOMP_FUNC(0x003ade5c, 40)
extern "C" u32 camp_func_0028c868(void* obj);

extern "C" u32 func_003ade5c(void) {
    u8* obj = *reinterpret_cast<u8**>(0x00439CA8);
    if (obj == nullptr) {
        return 1;
    }
    return camp_func_0028c868(obj + 0x2460);
}

// DECOMP_FUNC(0x003d7200, 40)
extern "C" u32 script_vm_func_00297704(u32 arg0, void* arg1, u32 arg2);

extern "C" u32 engine_func_003d7200(void* arg0, u32 arg1) {
    if (*reinterpret_cast<void**>(reinterpret_cast<u8*>(arg0) + 0x730) == nullptr) {
        return script_vm_func_00297704(arg1, reinterpret_cast<u8*>(arg0) + 0x734, 0);
    }
    return reinterpret_cast<uintptr_t>(arg0);
}

// DECOMP_FUNC(0x003d9fa0, 40)
extern "C" void* AsdMemory_func_002c23f8(u32 size);
extern "C" void* engine_func_0034a444(void* obj);

extern "C" void engine_func_003d9fa0(void* self) {
    void* obj = AsdMemory_func_002c23f8(0x44);
    if (obj != nullptr) {
        obj = engine_func_0034a444(obj);
    }
    *reinterpret_cast<void**>(reinterpret_cast<u8*>(self) + 0x1CF8) = obj;
}

// DECOMP_FUNC(0x003e72fc, 40)
extern "C" u32 func_002a6d58(void* target);
extern "C" u32 func_003e6b28(void);

extern "C" u32 func_003e72fc(void* arg0) {
    void* sub = *reinterpret_cast<void**>(reinterpret_cast<u8*>(arg0) + 4);
    void* target = *reinterpret_cast<void**>(reinterpret_cast<u8*>(sub) + 0x3C);
    if (func_002a6d58(target) != 0) {
        return func_003e6b28();
    }
    return 0;
}

// DECOMP_FUNC(0x0033534c, 44)
extern "C" u32 func_0020fe7c(void* sub2);

extern "C" u32 ui_func_0033534c(void* arg0) {
    void* sub1 = *reinterpret_cast<void**>(reinterpret_cast<u8*>(arg0) + 8);
    void* sub2 = *reinterpret_cast<void**>(reinterpret_cast<u8*>(sub1) + 8);
    return func_0020fe7c(sub2);
}

// DECOMP_FUNC(0x003489e8, 44)
extern "C" void* func_003489e8(void* self) {
    func_002c68bc(
        reinterpret_cast<u8*>(self) + 4,
        reinterpret_cast<const void*>(0x0033B7F0),
        0x544,
        2
    );
    return self;
}

// DECOMP_FUNC(0x0034f61c, 44)
extern "C" void* func_0034f61c(void* self, u32 index) {
    return *reinterpret_cast<void**>(reinterpret_cast<u8*>(self) + 0x10 + index * 4);
}

// DECOMP_FUNC(0x00354ef0, 44)
extern "C" s32 engine_func_002bb804(void* sub, u32* out_val, u32 arg1, u32 arg2);
extern "C" u32 nn_sdk_func_002bbd10(s32 res, ...);

extern "C" u32 engine_func_00354ef0(void* self, u32 arg1, u32 arg2) {
    u32 out_val = 0;
    s32 res = engine_func_002bb804(reinterpret_cast<u8*>(self) + 4, &out_val, arg1, arg2);
    if (res < 0) {
        nn_sdk_func_002bbd10(res);
    }
    return out_val;
}

// DECOMP_FUNC(0x00354f1c, 44)
extern "C" s32 func_002aca14(void* sub, u32 arg1, u32 arg2, u32 arg3, u32 arg4);

extern "C" u32 func_00354f1c(void* self, u32 arg1, u32 arg2, u32 arg3, u32 arg4) {
    s32 res = func_002aca14(reinterpret_cast<u8*>(self) + 4, arg1, arg2, arg3, arg4);
    if (res < 0) {
        return nn_sdk_func_002bbd10(res);
    }
    return res;
}

// DECOMP_FUNC(0x0035f9ec, 44)
extern "C" u32 engine_func_00237ad4(void* self);
extern "C" u32 engine_func_0035fbf8(void* self);

extern "C" u32 func_0035f9ec(void* self) {
    if (engine_func_00237ad4(self) == 0) {
        return 0xC8A0D018u;
    }
    return engine_func_0035fbf8(self);
}

// DECOMP_FUNC(0x0035fa18, 44)
extern "C" u32 func_0035ff30(void* self);

extern "C" u32 func_0035fa18(void* self) {
    if (engine_func_00237ad4(self) == 0) {
        return 0xC8A0D018u;
    }
    return func_0035ff30(self);
}

// DECOMP_FUNC(0x00370220, 44)
extern "C" u32 func_00370220(void* base) {
    *reinterpret_cast<u32*>(reinterpret_cast<u8*>(base) + 0x2C) = 0;
    u8* ptr = reinterpret_cast<u8*>(base) + 8;
    s32 rel = *reinterpret_cast<s32*>(ptr);
    if (rel != 0) {
        void* target = ptr + rel;
        return script_vm_func_002c3568(&target);
    }
    return reinterpret_cast<uintptr_t>(ptr);
}

// DECOMP_FUNC(0x00376b20, 44)
extern "C" u32 func_00379bd4(void* obj);
extern "C" void func_002bdbc4(void* obj);

extern "C" void func_00376b20(void* self, void* arg1) {
    *reinterpret_cast<void**>(self) = arg1;
    if (func_00379bd4(arg1) != 0) {
        func_002bdbc4(*reinterpret_cast<void**>(self));
    }
    void* inner = *reinterpret_cast<void**>(self);
    *reinterpret_cast<void**>(reinterpret_cast<u8*>(inner) + 8) = self;
}

// DECOMP_FUNC(0x0037bc48, 44)
extern "C" u32 func_0037b824(void* sub, u32 arg1);

extern "C" u32 func_0037bc48(void* self) {
    u8* p = reinterpret_cast<u8*>(self);
    if (p[0x261] == 0) {
        p[0x260] = 0;
        p[0x261] = 1;
        return func_0037b824(p + 0xC, 0);
    }
    return reinterpret_cast<uintptr_t>(self);
}

// DECOMP_FUNC(0x0039493c, 44)
extern "C" u32 func_002d5fbc(u32 token);

extern "C" u32 engine_func_0039493c(void) {
    if (engine_func_002c583c(1) != 0) {
        return 1;
    }
    return func_002d5fbc(0x06000001);
}

// DECOMP_FUNC(0x003a6614, 44)
extern "C" u32 script_vm_func_002a497c(u32 id);

extern "C" u32 engine_func_003a6614(void) {
    s32* p_count = reinterpret_cast<s32*>(0x0044E06C);
    s32 count = *p_count - 1;
    *p_count = count;
    if (count > 0) {
        return 1;
    }
    return script_vm_func_002a497c(0x17);
}

// DECOMP_FUNC(0x003e0dbc, 44)
extern "C" u32 func_002c1a48(void* arg0, void* arg1, u32 arg2);

extern "C" u32 engine_func_003e0dbc(void* arg0, void* arg1) {
    if (arg1 == nullptr) {
        return 0;
    }
    return (func_002c1a48(arg1, arg0, 8) == 0) ? 1 : 0;
}

// DECOMP_FUNC(0x003619cc, 48)
extern "C" s32 func_002a8190(u32 id);

extern "C" u32 func_003619cc(void) {
    s32 res = func_002a8190(0x401);
    if (res < 0 && static_cast<u32>(res) != 0xC8A0CFFCu) {
        return engine_func_002bce48(static_cast<u32>(res));
    }
    return static_cast<u32>(res);
}

// DECOMP_FUNC(0x00361b7c, 48)
extern "C" s32 func_002c1320(u32 a0, u32 a1);

extern "C" u32 script_vm_func_00361b7c(void) {
    s32 res = func_002c1320(0, 0);
    if (res < 0 && static_cast<u32>(res) != 0xC8A0CFFCu) {
        return engine_func_002bce48(static_cast<u32>(res));
    }
    return static_cast<u32>(res);
}

// DECOMP_FUNC(0x00384dc8, 48)
extern "C" void func_002c1b64(void* obj);
extern "C" u32 func_002c1abc(void* obj);

extern "C" u32 ui_func_00384dc8(void* arg0) {
    u32 val = *reinterpret_cast<u32*>(reinterpret_cast<u8*>(arg0) + 4);
    if (static_cast<s32>(val) > 2) {
        void* global_obj = *reinterpret_cast<void**>(0x0044EA00);
        func_002c1b64(global_obj);
        return func_002c1abc(global_obj);
    }
    return val;
}

// DECOMP_FUNC(0x00394c6c, 48)
extern "C" void func_002c1fa4(u32 id);
extern "C" void func_002e1470(u32 id);
extern "C" u32 func_001ffa64(void);

extern "C" u32 battle_func_00394c6c(void) {
    u32 res = engine_func_002c583c(1);
    if (res != 0) {
        return res;
    }
    func_002c1fa4(2);
    func_002e1470(2);
    return func_001ffa64();
}

// DECOMP_FUNC(0x003a65e4, 48)
extern "C" u32 camp_func_002976ac(u32 id);

extern "C" u32 camp_func_003a65e4(void) {
    s32* counter = reinterpret_cast<s32*>(0x0044E06C);
    u32 ret = 1;
    if (*counter <= 0) {
        ret = camp_func_002976ac(0x17);
    }
    *counter += 1;
    return ret;
}

// DECOMP_FUNC(0x003ca154, 48)
extern "C" void engine_func_002c4360(void* obj);

extern "C" void* engine_func_003ca154(void* self) {
    void** slots = reinterpret_cast<void**>(reinterpret_cast<u8*>(self) + 0x38);
    for (u32 i = 0; i < 0x38; ++i) {
        if (slots[i] != nullptr) {
            engine_func_002c4360(slots[i]);
        }
    }
    return self;
}

// DECOMP_FUNC(0x003df0d8, 48)
extern "C" float func_003df0d8(void* arg0) {
    void* sub = *reinterpret_cast<void**>(reinterpret_cast<u8*>(arg0) + 0x10);
    if (sub == nullptr) {
        return 0.0f;
    }
    u16 idx = *reinterpret_cast<u16*>(reinterpret_cast<u8*>(sub) + 0x10);
    const u8* table = reinterpret_cast<const u8*>(0x003FF7C8);
    return static_cast<float>(table[idx]);
}

// DECOMP_FUNC(0x0031124c, 52)
extern "C" u32 script_vm_func_002935ec(u32 id, u32 flag);

extern "C" u32 func_0031124c(u32 arg0) {
    void* global_obj = *reinterpret_cast<void**>(0x0043DCF0);
    if (global_obj == nullptr) {
        return arg0;
    }
    u32 id = (arg0 == 0) ? 0x16 : 8;
    return script_vm_func_002935ec(id, 1);
}

// DECOMP_FUNC(0x003a07d0, 52)
extern "C" void func_002347f4(void* obj);

extern "C" void func_003a07d0(void* obj) {
    func_002347f4(obj);
    engine_func_002b2520(obj);
}

extern "C" s32 func_003a07e0(const u16* a, const u16* b) {
    s32 diff = static_cast<s32>(a[0]) - static_cast<s32>(b[0]);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(a[1]) - static_cast<s32>(b[1]);
}

// DECOMP_FUNC(0x00339a5c, 56)
extern "C" void script_vm_func_00152af8(void* sub);
extern "C" void script_vm_func_002a7aa0(void* sub);

extern "C" u32 script_vm_func_00339a5c(void* obj) {
    void** slot = reinterpret_cast<void**>(reinterpret_cast<u8*>(obj) + 0x4398);
    void* sub = *slot;
    if (sub == nullptr) {
        return 0;
    }
    void* p = *reinterpret_cast<void**>(reinterpret_cast<u8*>(sub) + 8);
    s32 flag = *reinterpret_cast<s32*>(reinterpret_cast<u8*>(p) + 0xC);
    if (flag >= 0) {
        script_vm_func_00152af8(sub);
    }
    script_vm_func_002a7aa0(*slot);
    *slot = nullptr;
    return 0;
}

// DECOMP_FUNC(0x0035a238, 56)
extern "C" s32 camp_func_00139ae0(void* buf, u32 size, u32 flags);

extern "C" u32 camp_func_0035a238(void) {
    u8 buf[0xC4];
    s32 res = camp_func_00139ae0(buf, 0xC0, 0xC0000);
    if (res < 0) {
        nn_sdk_func_002bbd10(res);
    }
    u32 val = *reinterpret_cast<u32*>(buf);
    return (val >> 5) & 1;
}

// DECOMP_FUNC(0x00368cc0, 56)
extern "C" void* func_00368cc0(void* self) {
    using VTableFn = void* (*)(void*, u32, u32);
    VTableFn* vtable = *reinterpret_cast<VTableFn**>(self);
    void* res = vtable[2](self, 8, 4);
    if (res != nullptr) {
        void** out = reinterpret_cast<void**>(res);
        out[0] = reinterpret_cast<void*>(0x004210EC);
        out[1] = self;
    }
    return res;
}

// DECOMP_FUNC(0x0036c070, 56)
extern "C" void* func_0036c070(void* self) {
    using VTableFn = void* (*)(void*, u32, u32);
    VTableFn* vtable = *reinterpret_cast<VTableFn**>(self);
    void* res = vtable[2](self, 8, 4);
    if (res != nullptr) {
        void** out = reinterpret_cast<void**>(res);
        out[0] = reinterpret_cast<void*>(0x0042122C);
        out[1] = self;
    }
    return res;
}

// DECOMP_FUNC(0x00376b4c, 56)
extern "C" u32 func_00379c14(void* obj);
extern "C" void func_00379bcc(void* obj);

extern "C" void* func_00376b4c(void* self, void* arg1) {
    *reinterpret_cast<void**>(self) = arg1;
    if (func_00379c14(arg1) != 0) {
        func_00379bcc(*reinterpret_cast<void**>(self));
    }
    void* inner = *reinterpret_cast<void**>(self);
    *reinterpret_cast<void**>(reinterpret_cast<u8*>(inner) + 0xC) = self;
    return inner;
}

extern "C" void func_00376b78(void* obj) {
    *reinterpret_cast<void**>(obj) = nullptr;
}

// DECOMP_FUNC(0x00337558, 60)
extern "C" u32 battle_func_002931cc(u32 id);

extern "C" u32 func_00337558(void* obj) {
    u8* base = reinterpret_cast<u8*>(obj);
    u32 flag_a0 = *reinterpret_cast<u32*>(base + 0x44A0);
    if ((flag_a0 & 0x40) != 0) {
        return 0;
    }
    u32 flag_a8 = *reinterpret_cast<u32*>(base + 0x44A8);
    if ((flag_a8 & 0x20000) != 0) {
        return 1;
    }
    return battle_func_002931cc(0x10);
}

// DECOMP_FUNC(0x00338988, 60)
extern "C" void ui_func_00288990(void* sub);

extern "C" u32 ui_func_00338988(void* obj) {
    void** slot = reinterpret_cast<void**>(reinterpret_cast<u8*>(obj) + 0x4394);
    void* sub = *slot;
    if (sub == nullptr) {
        return 0;
    }
    ui_func_00288990(sub);
    sub = *slot;
    if (sub != nullptr) {
        using DtorFn = void (*)(void*);
        DtorFn* vtable = *reinterpret_cast<DtorFn**>(sub);
        vtable[1](sub);
    }
    *slot = nullptr;
    return 0;
}

// DECOMP_FUNC(0x00359088, 60)
extern "C" u32 func_003597bc(u32 arg0);
extern "C" u32 func_00359344(u32 arg0);

extern "C" u32 func_00359088(u32 arg0) {
    if (*reinterpret_cast<void**>(0x0047384C) != nullptr) {
        return func_003597bc(arg0);
    }
    if (*reinterpret_cast<void**>(0x00473848) != nullptr) {
        return func_00359344(arg0);
    }
    return 0xE0810BF8u;
}

// DECOMP_FUNC(0x003591e4, 60)
extern "C" s32 nn_sdk_func_002c1570(void);
extern "C" u32 engine_func_002c3290(u32 str_ptr);
extern "C" u32 nn_sdk_func_002c153c(void* target, u32 key, u32 val, u32 extra);

extern "C" u32 nn_sdk_func_003591e4(void) {
    s32 res = nn_sdk_func_002c1570();
    if (res < 0) {
        return static_cast<u32>(res);
    }
    u32 len = engine_func_002c3290(0x004103AA);
    return nn_sdk_func_002c153c(reinterpret_cast<void*>(0x00473848), 0x004103AA, len, 0);
}

// DECOMP_FUNC(0x00359288, 60)
extern "C" u32 func_00359940(u32 arg0);
extern "C" u32 func_003594c8(u32 arg0);

extern "C" u32 func_00359288(u32 arg0) {
    if (*reinterpret_cast<void**>(0x0047384C) != nullptr) {
        return func_00359940(arg0);
    }
    if (*reinterpret_cast<void**>(0x00473848) != nullptr) {
        return func_003594c8(arg0);
    }
    return 0xE0810BF8u;
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
