#include "engine/leaf_matching.h"

extern "C" {

// DECOMP_FUNC(0x0011b838, 24)
void engine_func_0011b838(u8* p) {
    *reinterpret_cast<volatile u32*>(p + 0x00) = 0;
    *reinterpret_cast<volatile u32*>(p + 0x04) = 0;
    *reinterpret_cast<volatile u16*>(p + 0x48) = 0;
    *reinterpret_cast<volatile u16*>(p + 0x4A) = 0;
}

// DECOMP_FUNC(0x00121ec4, 20)
void engine_func_00121ec4(u8* p) {
    *reinterpret_cast<volatile u32*>(p + 0x00) = 0;
    *reinterpret_cast<volatile u8*>(p + 0x04) = 1;
}

// DECOMP_FUNC(0x00130dcc, 12)
void engine_func_00130dcc(u8* p, u32 v) {
    *reinterpret_cast<u32*>(p + 0x3C) = v + 8;
}

// DECOMP_FUNC(0x00130dd8, 12)
void engine_func_00130dd8(u8* p, u32 v) {
    *reinterpret_cast<u32*>(p + 0x38) = v + 8;
}

// DECOMP_FUNC(0x001311a0, 12)
u32 engine_func_001311a0(void* self, u32 idx) {
    (void)self;
    return (idx * 3u) << 5;
}

// DECOMP_FUNC(0x00132fb8, 12)
void battle_func_00132fb8(u32* p) {
    *p = 1;
}

// DECOMP_FUNC(0x0015e7c0, 16)
u32 engine_func_0015e7c0(void** p) {
    void* v = p[1];
    if (v != nullptr) {
        v = reinterpret_cast<void*>(1);
    }
    return static_cast<u32>(reinterpret_cast<uintptr_t>(v));
}

// DECOMP_FUNC(0x0019de0c, 12)
u32 ui_func_0019de0c(u32** p) {
    return **(p - 1);
}

// DECOMP_FUNC(0x0022b3cc, 12)
u32 engine_func_0022b3cc(u8* p, u32 idx) {
    return *reinterpret_cast<u32*>(p + (idx << 2) + 0x530);
}

// DECOMP_FUNC(0x002347ac, 12)
u32 engine_func_002347ac(u32** p) {
    return (*p)[10];
}

// DECOMP_FUNC(0x0023abc0, 20)
void engine_func_0023abc0(volatile u32* src, u32* dst1, u32* dst2) {
    *dst1 = src[2];
    *dst2 = src[3];
}

// DECOMP_FUNC(0x0025503c, 20)
void engine_func_0025503c(volatile u16* p) {
    p[0] = 0;
    p[1] = 0;
    p[2] = 0;
}

// The original bodies of the next six ledger-defined leaf functions each
// consist of the single ARM return instruction `bx lr`.

// DECOMP_FUNC(0x001b0fdc, 4)
void func_001b0fdc() {}

// DECOMP_FUNC(0x001d2054, 4)
void func_001d2054() {}

// DECOMP_FUNC(0x001f66f8, 4)
void func_001f66f8() {}

// DECOMP_FUNC(0x00207304, 4)
void func_00207304() {}

// DECOMP_FUNC(0x00207308, 4)
void func_00207308() {}

// DECOMP_FUNC(0x002197d4, 4)
void func_002197d4() {}

// DECOMP_FUNC(0x001f66fc, 8)
void func_001f66fc(u8* p, u32 value) {
    *reinterpret_cast<u32*>(p + 0x10) = value;
}

// DECOMP_FUNC(0x001f68a8, 8)
void func_001f68a8(u8* p, f32 value) {
    *reinterpret_cast<f32*>(p + 0x14) = value;
}

// DECOMP_FUNC(0x002072fc, 8)
u32 func_002072fc(u8* p) {
    return *reinterpret_cast<u32*>(p + 0xBC);
}

// DECOMP_FUNC(0x00219770, 8)
void func_00219770(u8* p, u32 value) {
    *reinterpret_cast<u32*>(p + 0x24) = value;
}

// DECOMP_FUNC(0x00219778, 8)
void func_00219778(u8* p, f32 value) {
    *reinterpret_cast<f32*>(p + 0x20) = value;
}

// DECOMP_FUNC(0x0021a278, 8)
void func_0021a278(u8* p, u32 value) {
    *reinterpret_cast<u32*>(p + 0x04) = value;
}

// DECOMP_FUNC(0x0035d1f4, 8)
u32 func_0035d1f4() {
    return 8;
}

// DECOMP_FUNC(0x0035d268, 8)
u32 func_0035d268() {
    return 5;
}

// DECOMP_FUNC(0x0035d718, 8)
u32 func_0035d718() {
    return 4;
}

// DECOMP_FUNC(0x003686e8, 8)
u8* func_003686e8(u8* p) {
    return p + 0x3C;
}

// DECOMP_FUNC(0x003686f0, 8)
u8* func_003686f0(u8* p) {
    return p + 0x5C;
}

// DECOMP_FUNC(0x003686f8, 8)
u8* func_003686f8(u8* p) {
    return p + 0x4C;
}

// DECOMP_FUNC(0x00368700, 8)
u8* func_00368700(u8* p) {
    return p + 0x1C;
}

// DECOMP_FUNC(0x00368708, 8)
u8* func_00368708(u8* p) {
    return p + 0x2C;
}

}
