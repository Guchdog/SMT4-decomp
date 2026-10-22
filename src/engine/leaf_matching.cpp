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

}
