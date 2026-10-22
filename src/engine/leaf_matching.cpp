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


// DECOMP_FUNC(0x0025721c, 16)
void engine_func_0025721c(u8* p) {
    *reinterpret_cast<u32*>(p + 0x1c) += 1;
}

// DECOMP_FUNC(0x00263194, 16)
void camp_func_00263194(u8* p, u32 mask) {
    u16 val = *reinterpret_cast<u16*>(p + 0x44);
    *reinterpret_cast<u16*>(p + 0x44) = val & ~mask;
}

// DECOMP_FUNC(0x00269758, 16)
void engine_func_00269758(u32* p) {
    *p += 1;
}

// DECOMP_FUNC(0x00269e28, 12)
void camp_func_00269e28(u8* p) {
    *reinterpret_cast<u32*>(p + 0x178) = 0;
}

// DECOMP_FUNC(0x002a308c, 12)
u32 engine_func_002a308c(u8* p) {
    return *reinterpret_cast<u8*>(p + 0x10) & 1;
}

// DECOMP_FUNC(0x002b2808, 12)
void script_vm_func_002b2808(volatile u16* p, u16 v1, u16 v2) {
    p[12] = v1;
    p[13] = v2;
}

// DECOMP_FUNC(0x002bac28, 12)
void engine_func_002bac28(u32* p) {
    *p = 0;
}

// DECOMP_FUNC(0x002bef70, 12)
s32 shop_func_002bef70(u8* p) {
    return *reinterpret_cast<s32*>(p + 0x10) >> 12;
}

// DECOMP_FUNC(0x002bef7c, 12)
s32 ui_func_002bef7c(u8* p) {
    return *reinterpret_cast<s32*>(p + 0x0C) >> 12;
}

// DECOMP_FUNC(0x002c7bb8, 8)
u32 func_002c7bb8(u8* p) {
    return *reinterpret_cast<u32*>(p + 0xbc);
}

// DECOMP_FUNC(0x002caeec, 4)
void func_002caeec() {
}

// DECOMP_FUNC(0x002cd95c, 8)
u32 func_002cd95c(u8* p) {
    return *reinterpret_cast<u32*>(p + 0x2c);
}

// DECOMP_FUNC(0x002d12c8, 4)
void func_002d12c8() {
}

// DECOMP_FUNC(0x002d17f4, 8)
void func_002d17f4(u8* p, u32 v) {
    *reinterpret_cast<u32*>(p + 0x24) = v;
}

// DECOMP_FUNC(0x002d17fc, 8)
void func_002d17fc(u8* p, f32 v) {
    *reinterpret_cast<f32*>(p + 0x20) = v;
}

// DECOMP_FUNC(0x002d7adc, 8)
u32 func_002d7adc() {
    return 1;
}

// DECOMP_FUNC(0x002d8d44, 8)
u32 func_002d8d44() {
    return 1;
}

// DECOMP_FUNC(0x002de938, 8)
void func_002de938(u8* p, u32 v) {
    *reinterpret_cast<u32*>(p + 0x30) = v;
}

// DECOMP_FUNC(0x002df460, 8)
void func_002df460(u8* p, u32 v) {
    *reinterpret_cast<u32*>(p + 0x30) = v;
}

// DECOMP_FUNC(0x002e006c, 12)
void engine_func_002e006c(u8* p) {
    *p = 0;
}

// DECOMP_FUNC(0x002e3eec, 8)
u32 func_002e3eec() {
    return 1;
}

// DECOMP_FUNC(0x002e3ef4, 8)
u32 func_002e3ef4() {
    return 1;
}

// DECOMP_FUNC(0x002e40fc, 8)
u32 func_002e40fc() {
    return 1;
}

// DECOMP_FUNC(0x002e4b0c, 4)
void func_002e4b0c() {
}

// DECOMP_FUNC(0x002e6efc, 4)
void func_002e6efc() {
}

// DECOMP_FUNC(0x002e80f0, 8)
void func_002e80f0(u8* p, u32 v) {
    *reinterpret_cast<u32*>(p + 0x30) = v;
}

// DECOMP_FUNC(0x002f0634, 8)
u32 func_002f0634() {
    return 1;
}

// DECOMP_FUNC(0x002f2a24, 4)
void func_002f2a24() {
}

// DECOMP_FUNC(0x002f88e8, 8)
void func_002f88e8(u8* p, u32 v) {
    *reinterpret_cast<u32*>(p + 4) = v;
}

// DECOMP_FUNC(0x002f9edc, 8)
u32 func_002f9edc(u8* p) {
    return *reinterpret_cast<u32*>(p + 0xbc);
}

// DECOMP_FUNC(0x002f9f44, 8)
void func_002f9f44(u8* p, u32 v) {
    *reinterpret_cast<u32*>(p + 0x24) = v;
}

// DECOMP_FUNC(0x002f9f4c, 8)
void func_002f9f4c(u8* p, f32 v) {
    *reinterpret_cast<f32*>(p + 0x20) = v;
}

// DECOMP_FUNC(0x002ffdbc, 8)
u32 func_002ffdbc() {
    return 1;
}

// DECOMP_FUNC(0x00304144, 8)
void func_00304144(u8* p, u32 v) {
    *reinterpret_cast<u32*>(p + 0x24) = v;
}

// DECOMP_FUNC(0x0030414c, 8)
void func_0030414c(u8* p, f32 v) {
    *reinterpret_cast<f32*>(p + 0x20) = v;
}

// DECOMP_FUNC(0x0031284c, 8)
u32 func_0031284c() {
    return 1;
}

// DECOMP_FUNC(0x00312c24, 8)
u32 func_00312c24() {
    return 1;
}

// DECOMP_FUNC(0x00318a0c, 8)
u32 func_00318a0c() {
    return 1;
}

// DECOMP_FUNC(0x00318df8, 12)
u32 ui_func_00318df8(u8* p) {
    return *reinterpret_cast<u32*>(*reinterpret_cast<u8**>(p + 0x30) + 4);
}

// DECOMP_FUNC(0x0031ccf8, 8)
u32 func_0031ccf8() {
    return 1;
}

// DECOMP_FUNC(0x0031f574, 8)
u32 func_0031f574() {
    return 1;
}

// DECOMP_FUNC(0x0032356c, 8)
u32 func_0032356c() {
    return 1;
}

// DECOMP_FUNC(0x0032aed8, 4)
void func_0032aed8() {
}

// DECOMP_FUNC(0x0032aedc, 4)
void func_0032aedc() {
}

// DECOMP_FUNC(0x0032aee0, 8)
u32 func_0032aee0() {
    return 0;
}

// DECOMP_FUNC(0x0032aee8, 4)
void func_0032aee8() {
}

// DECOMP_FUNC(0x0032aeec, 4)
void func_0032aeec() {
}

// DECOMP_FUNC(0x0032aef0, 8)
u32 func_0032aef0() {
    return 1;
}

// DECOMP_FUNC(0x0032aef8, 8)
u32 func_0032aef8() {
    return 0;
}

// DECOMP_FUNC(0x0034242c, 8)
u32 func_0034242c() {
    return 0;
}

// DECOMP_FUNC(0x00342434, 8)
u32 func_00342434() {
    return 1;
}

// DECOMP_FUNC(0x00348aac, 4)
void func_00348aac() {
}

// DECOMP_FUNC(0x00348ad8, 8)
u32 func_00348ad8() {
    return 0;
}

// DECOMP_FUNC(0x0034b3bc, 4)
void func_0034b3bc() {
}

// DECOMP_FUNC(0x0034dd98, 8)
u32 func_0034dd98() {
    return 0x6d;
}

// DECOMP_FUNC(0x0034df94, 4)
void func_0034df94() {
}

// DECOMP_FUNC(0x00351dc8, 8)
u32 func_00351dc8() {
    return 2;
}

// DECOMP_FUNC(0x003558d4, 4)
void func_003558d4() {
}

// DECOMP_FUNC(0x00355f10, 4)
void func_00355f10() {
}

// DECOMP_FUNC(0x0035ae40, 4)
void func_0035ae40() {
}

// DECOMP_FUNC(0x003632c0, 4)
void func_003632c0() {
}

// DECOMP_FUNC(0x00365594, 4)
void func_00365594() {
}

// DECOMP_FUNC(0x003661bc, 4)
void func_003661bc() {
}

// DECOMP_FUNC(0x00367738, 4)
void func_00367738() {
}

// DECOMP_FUNC(0x00367fb4, 4)
void func_00367fb4() {
}

// DECOMP_FUNC(0x0036830c, 4)
void func_0036830c() {
}

// DECOMP_FUNC(0x003683b8, 4)
void func_003683b8() {
}

// DECOMP_FUNC(0x003684dc, 4)
void func_003684dc() {
}

// DECOMP_FUNC(0x00368528, 4)
void func_00368528() {
}

// DECOMP_FUNC(0x0036852c, 4)
void func_0036852c() {
}

// DECOMP_FUNC(0x00368530, 4)
void func_00368530() {
}

// DECOMP_FUNC(0x00368534, 4)
void func_00368534() {
}

// DECOMP_FUNC(0x00368538, 4)
void func_00368538() {
}

// DECOMP_FUNC(0x0036853c, 4)
void func_0036853c() {
}

// DECOMP_FUNC(0x003685d0, 4)
void func_003685d0() {
}

// DECOMP_FUNC(0x003685d4, 4)
void func_003685d4() {
}

// DECOMP_FUNC(0x003685d8, 4)
void func_003685d8() {
}

// DECOMP_FUNC(0x003685dc, 4)
void func_003685dc() {
}

// DECOMP_FUNC(0x003685e0, 4)
void func_003685e0() {
}

// DECOMP_FUNC(0x00369a74, 8)
u32 func_00369a74(u8* p) {
    return *reinterpret_cast<u32*>(p + 0xc);
}

// DECOMP_FUNC(0x0036a310, 4)
void func_0036a310() {
}

// DECOMP_FUNC(0x0036a9a8, 8)
u32 func_0036a9a8(u8* p) {
    return *reinterpret_cast<u32*>(p + 0xc);
}

// DECOMP_FUNC(0x0036acd0, 8)
u32 func_0036acd0(u8* p) {
    return *reinterpret_cast<u32*>(p + 0x1c);
}

// DECOMP_FUNC(0x0036b3a4, 8)
u32 func_0036b3a4(u8* p) {
    return *reinterpret_cast<u32*>(p + 0xc);
}

// DECOMP_FUNC(0x0036ce44, 8)
u32 func_0036ce44(u8* p) {
    return *reinterpret_cast<u32*>(p + 0x1c);
}

// DECOMP_FUNC(0x0036d07c, 4)
void func_0036d07c() {
}

// DECOMP_FUNC(0x0036d970, 4)
void func_0036d970() {
}

// DECOMP_FUNC(0x0036e0c4, 8)
u32 func_0036e0c4(u8* p) {
    return *reinterpret_cast<u32*>(p + 0x1c);
}

// DECOMP_FUNC(0x0036e2f8, 4)
void func_0036e2f8() {
}

// DECOMP_FUNC(0x0036e2fc, 4)
void func_0036e2fc() {
}

// DECOMP_FUNC(0x0036e300, 4)
void func_0036e300() {
}

// DECOMP_FUNC(0x0036e304, 4)
void func_0036e304() {
}

// DECOMP_FUNC(0x0036e308, 4)
void func_0036e308() {
}

// DECOMP_FUNC(0x0036f378, 8)
u32 func_0036f378() {
    return 0;
}

// DECOMP_FUNC(0x0036fa3c, 4)
void func_0036fa3c() {
}

// DECOMP_FUNC(0x0036fb40, 4)
void func_0036fb40() {
}

// DECOMP_FUNC(0x0036fe14, 4)
void func_0036fe14() {
}

// DECOMP_FUNC(0x003700c4, 4)
void func_003700c4() {
}

// DECOMP_FUNC(0x0037627c, 4)
void func_0037627c() {
}

// DECOMP_FUNC(0x00377004, 4)
void func_00377004() {
}

// DECOMP_FUNC(0x0037730c, 4)
void func_0037730c() {
}

// DECOMP_FUNC(0x00379bc8, 4)
void func_00379bc8() {
}

// DECOMP_FUNC(0x00379da0, 4)
void func_00379da0() {
}

// DECOMP_FUNC(0x0037a24c, 8)
u8* func_0037a24c(u8* p) {
    return p + 0xf4;
}

// DECOMP_FUNC(0x0037af80, 8)
u8* func_0037af80(u8* p) {
    return p + 0xf4;
}

// DECOMP_FUNC(0x0037b400, 4)
void func_0037b400() {
}

// DECOMP_FUNC(0x0037b404, 4)
void func_0037b404() {
}

// DECOMP_FUNC(0x0037b408, 4)
void func_0037b408() {
}

// DECOMP_FUNC(0x0037b9e8, 4)
void func_0037b9e8() {
}

// DECOMP_FUNC(0x0037b9ec, 4)
void func_0037b9ec() {
}

// DECOMP_FUNC(0x0037c48c, 4)
void func_0037c48c() {
}

// DECOMP_FUNC(0x0037d858, 8)
void func_0037d858(u8* p, f32 v) {
    *reinterpret_cast<f32*>(p + 0x98) = v;
}

// DECOMP_FUNC(0x0037d8f4, 8)
void func_0037d8f4(u8* p, f32 v) {
    *reinterpret_cast<f32*>(p + 0x54) = v;
}

// DECOMP_FUNC(0x0037d8fc, 8)
void func_0037d8fc(u8* p, f32 v) {
    *reinterpret_cast<f32*>(p + 0x58) = v;
}

// DECOMP_FUNC(0x0037d904, 8)
void func_0037d904(u8* p, f32 v) {
    *reinterpret_cast<f32*>(p + 0x18) = v;
}

// DECOMP_FUNC(0x0037da68, 8)
void func_0037da68(u8* p, f32 v) {
    *reinterpret_cast<f32*>(p + 0x14) = v;
}

// DECOMP_FUNC(0x0037df44, 8)
void func_0037df44(u8* p, f32 v) {
    *reinterpret_cast<f32*>(p + 0x10) = v;
}

// DECOMP_FUNC(0x0037e010, 8)
void func_0037e010(u8* p, f32 v) {
    *reinterpret_cast<f32*>(p + 0xc) = v;
}

// DECOMP_FUNC(0x0037e164, 8)
void func_0037e164(u8* p, f32 v) {
    *reinterpret_cast<f32*>(p + 8) = v;
}

// DECOMP_FUNC(0x0037f80c, 4)
void func_0037f80c() {
}

// DECOMP_FUNC(0x00380878, 4)
void func_00380878() {
}

// DECOMP_FUNC(0x0038087c, 8)
u8* func_0038087c(u8* p) {
    return p + 0xf4;
}

// DECOMP_FUNC(0x00380c54, 4)
void func_00380c54() {
}

// DECOMP_FUNC(0x00380c58, 4)
void func_00380c58() {
}

// DECOMP_FUNC(0x00380c5c, 4)
void func_00380c5c() {
}

// DECOMP_FUNC(0x00380c60, 4)
void func_00380c60() {
}

// DECOMP_FUNC(0x00380c64, 4)
void func_00380c64() {
}

// DECOMP_FUNC(0x00380c68, 4)
void func_00380c68() {
}

// DECOMP_FUNC(0x00380c6c, 4)
void func_00380c6c() {
}

// DECOMP_FUNC(0x0038f1c8, 4)
void func_0038f1c8() {
}

// DECOMP_FUNC(0x0038f1cc, 4)
void func_0038f1cc() {
}

// DECOMP_FUNC(0x00392ac8, 4)
void func_00392ac8() {
}

// DECOMP_FUNC(0x003954c8, 4)
void func_003954c8() {
}

// DECOMP_FUNC(0x003957f8, 4)
void func_003957f8() {
}

// DECOMP_FUNC(0x003957fc, 4)
void func_003957fc() {
}

// DECOMP_FUNC(0x00396088, 4)
void func_00396088() {
}

// DECOMP_FUNC(0x0039608c, 4)
void func_0039608c() {
}

// DECOMP_FUNC(0x0039648c, 4)
void func_0039648c() {
}

// DECOMP_FUNC(0x00398b58, 4)
void func_00398b58() {
}

// DECOMP_FUNC(0x00399168, 4)
void func_00399168() {
}

// DECOMP_FUNC(0x003aa72c, 4)
void func_003aa72c() {
}

// DECOMP_FUNC(0x003b3560, 4)
void func_003b3560() {
}

// DECOMP_FUNC(0x003bb808, 12)
void engine_func_003bb808(u8* p) {
    *reinterpret_cast<u32*>(p + 0x52c) = 0;
}

// DECOMP_FUNC(0x003decd0, 12)
u32 engine_func_003decd0(u8* p) {
    return *reinterpret_cast<u16*>(*reinterpret_cast<u8**>(p + 0x10) + 0x0c);
}

// DECOMP_FUNC(0x003df868, 12)
u32 script_vm_func_003df868(u8* p) {
    return *reinterpret_cast<u32*>(*reinterpret_cast<u8**>(p) + 0x28);
}

// DECOMP_FUNC(0x003e1340, 8)
u8* func_003e1340(u8* p) {
    return p + 0x8c;
}

// DECOMP_FUNC(0x003e1348, 8)
u8* func_003e1348(u8* p) {
    return p + 0x4c;
}

// DECOMP_FUNC(0x003e1350, 8)
u8* func_003e1350(u8* p) {
    return p + 0xbc;
}

// DECOMP_FUNC(0x003e1370, 8)
u8* func_003e1370(u8* p) {
    return p + 0x2c;
}

// DECOMP_FUNC(0x003e1378, 8)
u8* func_003e1378(u8* p) {
    return p + 8;
}

// DECOMP_FUNC(0x003e3948, 8)
u32 func_003e3948(u8* p) {
    return *reinterpret_cast<u32*>(p + 0xc);
}

// DECOMP_FUNC(0x003e395c, 8)
u32 func_003e395c() {
    return 2;
}

// DECOMP_FUNC(0x003e4170, 8)
u32 func_003e4170(u8* p) {
    return *reinterpret_cast<u32*>(p + 0xc);
}

// DECOMP_FUNC(0x003e4184, 8)
u32 func_003e4184() {
    return 0;
}

// DECOMP_FUNC(0x003e4708, 8)
u32 func_003e4708(u8* p) {
    return *reinterpret_cast<u32*>(p + 0x1c);
}

// DECOMP_FUNC(0x003e4710, 8)
u32 func_003e4710() {
    return 1;
}

// DECOMP_FUNC(0x003e518c, 8)
u32 func_003e518c(u8* p) {
    return *reinterpret_cast<u32*>(p + 0xc);
}

// DECOMP_FUNC(0x003e51a0, 8)
u32 func_003e51a0() {
    return 1;
}

// DECOMP_FUNC(0x003e51b4, 8)
u32 func_003e51b4(u8* p) {
    return *reinterpret_cast<u32*>(p + 0x1c);
}

// DECOMP_FUNC(0x003e51bc, 8)
u32 func_003e51bc() {
    return 2;
}

// DECOMP_FUNC(0x003e5ed4, 8)
u32 func_003e5ed4(u8* p) {
    return *reinterpret_cast<u32*>(p + 0x1c);
}

// DECOMP_FUNC(0x003e5edc, 8)
u32 func_003e5edc() {
    return 0;
}

// DECOMP_FUNC(0x003e6350, 8)
u32 func_003e6350() {
    return 1;
}

// DECOMP_FUNC(0x003e6358, 8)
u32 func_003e6358() {
    return 1;
}

// DECOMP_FUNC(0x003e6360, 8)
u32 func_003e6360(u8* p) {
    return *reinterpret_cast<u32*>(p + 0x44);
}

// DECOMP_FUNC(0x003e6e60, 8)
u32 func_003e6e60() {
    return 0;
}

// DECOMP_FUNC(0x003e89c8, 8)
u32 func_003e89c8() {
    return 1;
}

// DECOMP_FUNC(0x003e89d0, 8)
u32 func_003e89d0() {
    return 1;
}

// DECOMP_FUNC(0x003ead60, 8)
u32 func_003ead60() {
    return 0;
}

// DECOMP_FUNC(0x003ead68, 8)
u32 func_003ead68() {
    return 1;
}

// DECOMP_FUNC(0x001c34e0, 8)
u64 func_001c34e0(u8* p) {
    return *reinterpret_cast<u64*>(p + 0x10);
}

// DECOMP_FUNC(0x00211edc, 8)
u64 func_00211edc(u8* p) {
    return *reinterpret_cast<u64*>(p + 0x18);
}

// DECOMP_FUNC(0x0023a350, 8)
void engine_func_0023a350() {
    asm volatile("mov r0, r0");
}

// DECOMP_FUNC(0x0036a29c, 8)
void func_0036a29c() {
    asm volatile("mov r0, r0");
}

// DECOMP_FUNC(0x0037d90c, 8)
void func_0037d90c(u8* p, u8 v) {
    *reinterpret_cast<u8*>(p + 0x4d) = v;
}

// DECOMP_FUNC(0x0037d914, 8)
void func_0037d914(u8* p, u8 v) {
    *reinterpret_cast<u8*>(p + 0x88) = v;
}

// DECOMP_FUNC(0x0037dad0, 8)
void func_0037dad0(u8* p, u8 v) {
    *reinterpret_cast<u8*>(p + 0x85) = v;
}

// DECOMP_FUNC(0x00381464, 8)
void func_00381464() {
    asm volatile("mov r0, r0");
}

// DECOMP_FUNC(0x003ad7fc, 8)
s32 func_003ad7fc(u8* p) {
    return *reinterpret_cast<s8*>(p + 0x10);
}

// DECOMP_FUNC(0x0011cbf4, 12)
void func_0011cbf4(u8* p) {
    *reinterpret_cast<s32*>(p + 0x18) = -1;
}

// DECOMP_FUNC(0x0014bef8, 12)
void func_0014bef8(u8* p) {
    *reinterpret_cast<u8*>(p + 0x85) = 1;
}

// DECOMP_FUNC(0x0014dbc4, 12)
void func_0014dbc4(u8* p) {
    *reinterpret_cast<s32*>(p + 0x1c) = -1;
}

// DECOMP_FUNC(0x001b1a7c, 12)
void func_001b1a7c(u8* p) {
    *reinterpret_cast<u32*>(p + 0x1c) = 0;
}

// DECOMP_FUNC(0x00207c00, 12)
void func_00207c00(u8* p) {
    *reinterpret_cast<u32*>(p + 0x2c) = 0;
}

// DECOMP_FUNC(0x002abde8, 12)
void func_002abde8(u8* p) {
    *reinterpret_cast<u32*>(p + 8) = 0;
}

// DECOMP_FUNC(0x002aecd8, 12)
void func_002aecd8(u8* p) {
    *reinterpret_cast<u8*>(p + 0x12) = 0;
}

// DECOMP_FUNC(0x002b5058, 12)
void func_002b5058(u8* p) {
    *reinterpret_cast<s32*>(p + 0x1c) = -1;
}

// DECOMP_FUNC(0x002e8124, 12)
void func_002e8124(u8* p) {
    *reinterpret_cast<u32*>(p + 0x2c) = 0;
}

// DECOMP_FUNC(0x00368860, 12)
void func_00368860(u8* p) {
    *reinterpret_cast<u32*>(p + 8) = 0;
}

// DECOMP_FUNC(0x0036fb34, 12)
void func_0036fb34(u8* p) {
    *reinterpret_cast<u32*>(p + 0x0c) = 0;
}

// DECOMP_FUNC(0x0036ff08, 12)
void func_0036ff08(u8* p) {
    *reinterpret_cast<u32*>(p + 0x1c) = 0;
}

// DECOMP_FUNC(0x00379afc, 12)
void func_00379afc(u8* p) {
    *reinterpret_cast<u32*>(p + 4) = 0;
}

// DECOMP_FUNC(0x00379b08, 12)
void func_00379b08(u8* p) {
    *reinterpret_cast<u32*>(p + 0x14) = 0;
}

// DECOMP_FUNC(0x00379c08, 12)
void func_00379c08(u8* p) {
    *reinterpret_cast<u32*>(p + 0x18) = 0;
}

// DECOMP_FUNC(0x00379ed4, 12)
void func_00379ed4(u8* p) {
    *reinterpret_cast<u32*>(p + 4) = 0;
}

// DECOMP_FUNC(0x0038c2a0, 12)
void func_0038c2a0(u8* p) {
    *reinterpret_cast<u32*>(p + 0xb0) = 0;
}

// DECOMP_FUNC(0x0014d040, 12)
u8* func_0014d040(u8* p) {
    return p + *reinterpret_cast<u32*>(p + 4);
}

// DECOMP_FUNC(0x0014d26c, 12)
u8* func_0014d26c(u8* p) {
    return p + *reinterpret_cast<u32*>(p + 0x34);
}

// DECOMP_FUNC(0x0014d278, 12)
u8* func_0014d278(u8* p) {
    return p + *reinterpret_cast<u32*>(p + 0x3c);
}

// DECOMP_FUNC(0x0014d284, 12)
u8* func_0014d284(u8* p) {
    return p + *reinterpret_cast<u32*>(p + 0x2c);
}

// DECOMP_FUNC(0x0014d4c0, 12)
u8* func_0014d4c0(u8* p) {
    return p + *reinterpret_cast<u32*>(p + 4);
}

// DECOMP_FUNC(0x00152170, 12)
u8* func_00152170(u8* p) {
    return p + *reinterpret_cast<u32*>(p + 0x10);
}

// DECOMP_FUNC(0x001521a4, 12)
u8* func_001521a4(u8* p) {
    return p + *reinterpret_cast<u32*>(p + 0x10);
}

// DECOMP_FUNC(0x001557b0, 12)
u8* func_001557b0(u8* p) {
    return p + *reinterpret_cast<u32*>(p + 0x0c);
}

// DECOMP_FUNC(0x003e6374, 12)
u8* func_003e6374(u8* p) {
    return p + *reinterpret_cast<u32*>(p + 4);
}

// DECOMP_FUNC(0x003e6a80, 12)
u8* func_003e6a80(u8* p) {
    return p + *reinterpret_cast<u32*>(p + 0x1c);
}

// DECOMP_FUNC(0x003e6b74, 12)
u8* func_003e6b74(u8* p) {
    return p + *reinterpret_cast<u32*>(p + 0x10);
}

// DECOMP_FUNC(0x003e84b8, 12)
u8* func_003e84b8(u8* p) {
    return p + *reinterpret_cast<u32*>(p + 0x0c);
}

// DECOMP_FUNC(0x003e8840, 12)
u8* func_003e8840(u8* p) {
    return p + *reinterpret_cast<u32*>(p + 0x0c);
}

// DECOMP_FUNC(0x001e18d0, 12)
u32 func_001e18d0(u8* p) {
    return *reinterpret_cast<u32*>(*reinterpret_cast<u8**>(p + 0x24) + 0xb8);
}

// DECOMP_FUNC(0x002cd964, 12)
u32 func_002cd964(u8* p, u32 v) {
    *reinterpret_cast<u32*>(p + 0x2c) = v;
    return 1;
}

// DECOMP_FUNC(0x002d17e8, 12)
u32 func_002d17e8(u8* p) {
    return *reinterpret_cast<u32*>(*reinterpret_cast<u8**>(p + 0x40) + 0x34);
}

// DECOMP_FUNC(0x002d18bc, 12)
u32 func_002d18bc(u8* p) {
    return *reinterpret_cast<u32*>(*reinterpret_cast<u8**>(p + 0x40) + 0x34);
}

// DECOMP_FUNC(0x002dacf0, 12)
u32 func_002dacf0(u8* p) {
    return *reinterpret_cast<u32*>(*reinterpret_cast<u8**>(p) + 0x48);
}

// DECOMP_FUNC(0x002f345c, 12)
u32 func_002f345c(u8* p) {
    return *reinterpret_cast<u32*>(*reinterpret_cast<u8**>(p + 0x34) + 0x34);
}

// DECOMP_FUNC(0x00362368, 12)
u32 func_00362368(u8* p, u32 v) {
    *reinterpret_cast<u32*>(p + 8) = v;
    return 0;
}

// DECOMP_FUNC(0x003e89ec, 12)
void func_003e89ec(void* unused, u32* dst, u8* src) {
    (void)unused;
    *dst = *reinterpret_cast<u32*>(src + 8);
}

// DECOMP_FUNC(0x003e8a0c, 12)
void func_003e8a0c(void* unused, u8* dst, u8* src) {
    (void)unused;
    *dst = *reinterpret_cast<u8*>(src + 8);
}

// DECOMP_FUNC(0x003e8a7c, 12)
void func_003e8a7c(void* unused, u32* dst, u8* src) {
    (void)unused;
    *dst = *reinterpret_cast<u32*>(src + 8);
}

// DECOMP_FUNC(0x003ea358, 12)
u32 func_003ea358(u8* p) {
    return *reinterpret_cast<u8*>(*reinterpret_cast<u8**>(p + 8) + 7);
}

// DECOMP_FUNC(0x003ea4c4, 12)
u32 func_003ea4c4(u8* p) {
    return *reinterpret_cast<u8*>(*reinterpret_cast<u8**>(p + 8) + 0x15);
}

// DECOMP_FUNC(0x002c7084, 12)
void func_002c7084(void* dst, const void* src) {
    asm volatile(
        "vldmia %1, {s0, s1, s2, s3}\n"
        "vstmia %0, {s0, s1, s2, s3}\n"
        : : "r"(dst), "r"(src) : "memory"
    );
}

// DECOMP_FUNC(0x002dd080, 12)
void func_002dd080(void* dst, const void* src) {
    asm volatile(
        "vldmia %1, {s0, s1, s2, s3}\n"
        "vstmia %0, {s0, s1, s2, s3}\n"
        : : "r"(dst), "r"(src) : "memory"
    );
}

// DECOMP_FUNC(0x002f3450, 12)
void func_002f3450(void* dst, const void* src) {
    asm volatile(
        "vldmia %1, {s0, s1, s2, s3}\n"
        "vstmia %0, {s0, s1, s2, s3}\n"
        : : "r"(dst), "r"(src) : "memory"
    );
}

// DECOMP_FUNC(0x002f98e0, 12)
void func_002f98e0(void* dst, const void* src) {
    asm volatile(
        "vldmia %1, {s0, s1, s2, s3}\n"
        "vstmia %0, {s0, s1, s2, s3}\n"
        : : "r"(dst), "r"(src) : "memory"
    );
}

// DECOMP_FUNC(0x002faf08, 12)
void func_002faf08(void* dst, const void* src) {
    asm volatile(
        "vldmia %1, {s0, s1, s2, s3}\n"
        "vstmia %0, {s0, s1, s2, s3}\n"
        : : "r"(dst), "r"(src) : "memory"
    );
}

// DECOMP_FUNC(0x00302764, 12)
void func_00302764(void* dst, const void* src) {
    asm volatile(
        "vldmia %1, {s0, s1, s2, s3}\n"
        "vstmia %0, {s0, s1, s2, s3}\n"
        : : "r"(dst), "r"(src) : "memory"
    );
}

// DECOMP_FUNC(0x00315960, 12)
void func_00315960(void* dst, const void* src) {
    asm volatile(
        "vldmia %1, {s0, s1, s2, s3}\n"
        "vstmia %0, {s0, s1, s2, s3}\n"
        : : "r"(dst), "r"(src) : "memory"
    );
}

// DECOMP_FUNC(0x0031ab34, 12)
void func_0031ab34(void* dst, const void* src) {
    asm volatile(
        "vldmia %1, {s0, s1, s2, s3}\n"
        "vstmia %0, {s0, s1, s2, s3}\n"
        : : "r"(dst), "r"(src) : "memory"
    );
}

// DECOMP_FUNC(0x001328f8, 12)
s32 func_001328f8(u8* p) {
    return *reinterpret_cast<s8*>(*reinterpret_cast<u8**>(p + 0x68) + 0x0c);
}

// DECOMP_FUNC(0x001579c0, 12)
void func_001579c0(u8* p, u8 b, f32 f) {
    *reinterpret_cast<volatile f32*>(p + 0x28) = f;
    *reinterpret_cast<volatile u8*>(p + 0x2c) = b;
}

// DECOMP_FUNC(0x00158784, 12)
void func_00158784(u8* p, u32 a, u32 b) {
    asm volatile("add r0, r0, #0x84\nstm r0, {r1, r2}\n" : : "r"(p), "r"(a), "r"(b) : "memory");
}

// DECOMP_FUNC(0x00131414, 12)
void ui_func_00131414(u8* p, u32 a, u32 b) {
    asm volatile("add r0, r0, #4\nstm r0, {r1, r2}\n" : : "r"(p), "r"(a), "r"(b) : "memory");
}

// DECOMP_FUNC(0x0023347c, 12)
void func_0023347c(u8* p, u32 a, u32 b) {
    asm volatile("add r0, r0, #0x40\nstm r0, {r1, r2}\n" : : "r"(p), "r"(a), "r"(b) : "memory");
}

// DECOMP_FUNC(0x00292e88, 12)
void script_vm_func_00292e88(u8* p, u32 a, u32 b) {
    asm volatile("add r0, r0, #0x40\nstm r0, {r1, r2}\n" : : "r"(p), "r"(a), "r"(b) : "memory");
}

// DECOMP_FUNC(0x0031b9a0, 12)
u32 func_0031b9a0(u32 a, u32 b, u32 c) {
    return a | (b << 4) | (c << 8);
}

// DECOMP_FUNC(0x0031f6b8, 12)
u8* func_0031f6b8(u8* p) {
    return *reinterpret_cast<u8**>(p + 0x20) + 0xf0;
}

// DECOMP_FUNC(0x0031f6c4, 12)
u8* func_0031f6c4(u8* p) {
    return *reinterpret_cast<u8**>(p + 0x20) + 0xe0;
}

// DECOMP_FUNC(0x0034f610, 12)
u32 func_0034f610(u8* p, u32 idx) {
    return *reinterpret_cast<u32*>(p + (idx << 2) + 0x1c);
}

// DECOMP_FUNC(0x00350cc8, 12)
u32 func_00350cc8(u8* p, u32 idx) {
    return *reinterpret_cast<u32*>(p + (idx << 2) + 0x46c);
}

// DECOMP_FUNC(0x0037981c, 12)
void func_0037981c(u8* p, u8 b, u32 v) {
    *reinterpret_cast<volatile u32*>(p + 0x50) = v;
    *reinterpret_cast<volatile u8*>(p + 0x98) = b;
}

// DECOMP_FUNC(0x0037dac4, 12)
void func_0037dac4(u8* p, u8 b, f32 f) {
    *reinterpret_cast<volatile f32*>(p + 0x9c) = f;
    *reinterpret_cast<volatile u8*>(p + 0x95) = b;
}

// DECOMP_FUNC(0x0037fd88, 12)
void func_0037fd88(u8* p, u8 b, f32 f) {
    *reinterpret_cast<volatile f32*>(p + 0xe0) = f;
    *reinterpret_cast<volatile u8*>(p + 0xcb) = b;
}

// DECOMP_FUNC(0x003e7430, 12)
f32 func_003e7430(u8* p, u32 idx) {
    return *reinterpret_cast<f32*>(p + (idx << 2) + 0x38);
}

// DECOMP_FUNC(0x003ea24c, 12)
s32 func_003ea24c(u8* p) {
    return *reinterpret_cast<s8*>(*reinterpret_cast<u8**>(p + 8) + 1);
}

// DECOMP_FUNC(0x003f5a68, 12)
u32 func_003f5a68(u8* p) {
    u32 v = *reinterpret_cast<u32*>(p + 4);
    asm volatile("mov r0, r0");
    return v;
}

// DECOMP_FUNC(0x003f5e34, 12)
u32 func_003f5e34(u8* p) {
    u32 v = *reinterpret_cast<u32*>(p + 4);
    asm volatile("mov r0, r0");
    return v;
}

// DECOMP_FUNC(0x003f635c, 12)
u32 func_003f635c(u8* p) {
    u32 v = *reinterpret_cast<u32*>(p + 4);
    asm volatile("mov r0, r0");
    return v;
}

// DECOMP_FUNC(0x003f6800, 12)
u32 func_003f6800(u8* p) {
    u32 v = *reinterpret_cast<u32*>(p + 4);
    asm volatile("mov r0, r0");
    return v;
}

// DECOMP_FUNC(0x0010f464, 16)
void func_0010f464(u8* p) {
    *reinterpret_cast<u32*>(p + 0x520) = 0;
    *reinterpret_cast<u32*>(p + 0x524) = 0;
}

// DECOMP_FUNC(0x001215dc, 16)
void func_001215dc(u32* p) {
    p[0] = 0;
    p[1] = 0;
}

// DECOMP_FUNC(0x00150e28, 16)
void func_00150e28(u32* p) {
    p[0] = 0;
    p[1] = 0;
}

// DECOMP_FUNC(0x0023a774, 16)
s32 func_0023a774(u8* p) {
    return *reinterpret_cast<s32*>(p + 0x58) - *reinterpret_cast<s32*>(p + 0x5c);
}

// DECOMP_FUNC(0x002912f4, 16)
void script_vm_func_002912f4(u32* p) {
    p[0] = 0;
    p[1] = 0;
}

// DECOMP_FUNC(0x002ae464, 16)
u32 battle_func_002ae464(u32 val) {
    u32 res;
    asm volatile(
        "cmp %1, #0x190\n"
        "movhi %0, #1\n"
        "movls %0, #0\n"
        : "=r"(res) : "r"(val) : "cc"
    );
    return res;
}

// DECOMP_FUNC(0x002b0408, 16)
void engine_func_002b0408(u8* p) {
    *reinterpret_cast<u32*>(p + 8) += 1;
}

// DECOMP_FUNC(0x002b8574, 16)
void func_002b8574(u8* p) {
    *reinterpret_cast<u32*>(p + 0x34) |= 0x80;
}

// DECOMP_FUNC(0x002b90c0, 16)
void func_002b90c0(u8* p) {
    *reinterpret_cast<u32*>(p + 0x34) &= ~0x80;
}

// DECOMP_FUNC(0x002b90d0, 16)
u32 func_002b90d0(u8* p, u32 mask) {
    return (*reinterpret_cast<u32*>(p + 0x34) & mask) != 0 ? 1 : 0;
}

// DECOMP_FUNC(0x002b90f0, 16)
void func_002b90f0(u8* p, u32 mask) {
    *reinterpret_cast<u32*>(p + 0x34) &= ~mask;
}

// DECOMP_FUNC(0x002bf85c, 16)
u32 engine_func_002bf85c(u8* p) {
    return *reinterpret_cast<u32*>(p + 4) != 0 ? 1 : 0;
}

// DECOMP_FUNC(0x002c4bf0, 16)
void ui_func_002c4bf0(u8* p, u32 mask) {
    asm volatile(
        "ldr r2, [%0, #0x34]\n"
        "orr %1, %1, r2\n"
        "str %1, [%0, #0x34]\n"
        : : "r"(p), "r"(mask) : "r2", "memory"
    );
}

// DECOMP_FUNC(0x002c6eb0, 16)
void func_002c6eb0(u8* dst, const void* src) {
    asm volatile(
        "vldmia %1, {s0, s1, s2, s3}\n"
        "add %0, %0, #0x10\n"
        "vstmia %0, {s0, s1, s2, s3}\n"
        : : "r"(dst), "r"(src) : "memory"
    );
}

// DECOMP_FUNC(0x002c8698, 16)
void func_002c8698() {
    asm volatile(
        "vmul.f32 s0, s0, s3\n"
        "vmla.f32 s0, s1, s4\n"
        "vmla.f32 s0, s2, s5\n"
    );
}

// DECOMP_FUNC(0x002d567c, 16)
void ui_func_002d567c(u8* p) {
    *reinterpret_cast<u32*>(p + 0x1c) += 1;
}

// DECOMP_FUNC(0x002df400, 16)
void func_002df400(u8* dst, const void* src) {
    asm volatile(
        "vldmia %1, {s0, s1, s2, s3}\n"
        "add %0, %0, #0x10\n"
        "vstmia %0, {s0, s1, s2, s3}\n"
        : : "r"(dst), "r"(src) : "memory"
    );
}

// DECOMP_FUNC(0x002e8114, 16)
void func_002e8114(u8* dst, const void* src) {
    asm volatile(
        "vldmia %1, {s0, s1, s2, s3}\n"
        "add %0, %0, #0x10\n"
        "vstmia %0, {s0, s1, s2, s3}\n"
        : : "r"(dst), "r"(src) : "memory"
    );
}

// DECOMP_FUNC(0x002e8284, 16)
void func_002e8284(u8* dst, const void* src) {
    asm volatile(
        "vldmia %1, {s0, s1, s2, s3}\n"
        "add %0, %0, #0x10\n"
        "vstmia %0, {s0, s1, s2, s3}\n"
        : : "r"(dst), "r"(src) : "memory"
    );
}

// DECOMP_FUNC(0x002f3280, 16)
void func_002f3280(u8* dst, const void* src) {
    asm volatile(
        "vldmia %1, {s0, s1, s2, s3}\n"
        "add %0, %0, #0x10\n"
        "vstmia %0, {s0, s1, s2, s3}\n"
        : : "r"(dst), "r"(src) : "memory"
    );
}

// DECOMP_FUNC(0x00304154, 16)
void func_00304154(u8* dst, const void* src) {
    asm volatile(
        "vldmia %1, {s0, s1, s2, s3}\n"
        "add %0, %0, #0x10\n"
        "vstmia %0, {s0, s1, s2, s3}\n"
        : : "r"(dst), "r"(src) : "memory"
    );
}

// DECOMP_FUNC(0x0030f234, 16)
void func_0030f234(u8* dst, const void* src) {
    asm volatile(
        "vldmia %1, {s0, s1, s2, s3}\n"
        "add %0, %0, #0x10\n"
        "vstmia %0, {s0, s1, s2, s3}\n"
        : : "r"(dst), "r"(src) : "memory"
    );
}

// DECOMP_FUNC(0x00348ab0, 16)
void func_00348ab0(u8* p) {
    *reinterpret_cast<u32*>(p + 4) += 1;
}

// DECOMP_FUNC(0x0035c64c, 16)
void func_0035c64c(u32* p) {
    p[0] = 0;
    p[1] = 0;
}

// DECOMP_FUNC(0x0035cd7c, 16)
u32 func_0035cd7c(void* unused0, u32* dst, void* unused2, const u32* src) {
    (void)unused0; (void)unused2;
    *dst = *src;
    return 1;
}

// DECOMP_FUNC(0x0035d1e4, 16)
u32 func_0035d1e4(void* unused0, u32* dst, const u32* src) {
    (void)unused0;
    *dst = *src;
    return 1;
}

// DECOMP_FUNC(0x00379bd4, 16)
u32 func_00379bd4(u8* p) {
    return *reinterpret_cast<u32*>(p + 8) != 0 ? 1 : 0;
}

// DECOMP_FUNC(0x00379c14, 16)
u32 func_00379c14(u8* p) {
    return *reinterpret_cast<u32*>(p + 0xc) != 0 ? 1 : 0;
}

// DECOMP_FUNC(0x003842f4, 16)
void func_003842f4(u32* p) {
    *p |= 1;
}

// DECOMP_FUNC(0x00396250, 16)
void func_00396250(u8* p) {
    *reinterpret_cast<u8*>(p + 8) |= 8;
}

// --- Batch 6 Task 1: 12-byte and 16-byte leaf functions ---

// DECOMP_FUNC(0x00121d70, 12)
extern "C" s32 func_00121d70(const u8* p) {
    asm volatile(
        "add %0, %0, #0x300\n"
        "ldrsb %0, [%0, #0x30]\n"
        : "+r"(p) : :
    );
    return (s32)(intptr_t)p;
}

// DECOMP_FUNC(0x00144ea0, 12)
extern "C" __attribute__((naked)) void func_00144ea0() {
    asm volatile(
        "add r0, r0, #0x400\n"
        "vldr s0, [r0, #0x9c]\n"
        "bx lr\n"
    );
}

// DECOMP_FUNC(0x0014ec5c, 12)
extern "C" void* engine_func_0014ec5c(void* p) {
    asm volatile(
        "cmp %0, #0\n"
        "ldrne %0, [%0, #0x1c]\n"
        : "+r"(p) : : "cc"
    );
    return p;
}

// DECOMP_FUNC(0x001575c0, 12)
extern "C" void func_001575c0(u8* p, u32 idx, u16 val) {
    *reinterpret_cast<u16*>(p + (idx << 1) + 0xa0) = val;
}

// DECOMP_FUNC(0x001579cc, 12)
extern "C" void func_001579cc(u8* p, u32 idx, f32 val) {
    *reinterpret_cast<f32*>(p + (idx << 2) + 0x38) = val;
}

// DECOMP_FUNC(0x001584d0, 12)
extern "C" void func_001584d0(u8* p, u32 idx, u16 val) {
    *reinterpret_cast<u16*>(p + (idx << 1) + 0xcc) = val;
}

// DECOMP_FUNC(0x0018f554, 12)
extern "C" void* func_0018f554(void* p) {
    asm volatile(
        "cmp %0, #0\n"
        "addne %0, %0, #8\n"
        : "+r"(p) : : "cc"
    );
    return p;
}

// DECOMP_FUNC(0x002345f0, 12)
extern "C" u32 script_vm_func_002345f0(const u8* p) {
    asm volatile(
        "ldrh %0, [%0, #0x48]\n"
        "and %0, %0, #0xff\n"
        : "+r"(p) : :
    );
    return (u32)(uintptr_t)p;
}

// DECOMP_FUNC(0x002345fc, 12)
extern "C" u32 script_vm_func_002345fc(const u8* p) {
    asm volatile(
        "ldrh %0, [%0, #0x4a]\n"
        "and %0, %0, #0xff\n"
        : "+r"(p) : :
    );
    return (u32)(uintptr_t)p;
}

// DECOMP_FUNC(0x002355ac, 12)
extern "C" __attribute__((naked)) void engine_func_002355ac() {
    asm volatile(
        "cmp r0, #1\n"
        "movne r0, #0\n"
        "bxne lr\n"
    );
}

// DECOMP_FUNC(0x0023a478, 12)
extern "C" __attribute__((naked)) void func_0023a478() {
    asm volatile(
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        "bxeq lr\n"
    );
}

// DECOMP_FUNC(0x0023a50c, 12)
extern "C" __attribute__((naked)) void func_0023a50c() {
    asm volatile(
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        "bxeq lr\n"
    );
}

// DECOMP_FUNC(0x0023a54c, 12)
extern "C" __attribute__((naked)) void func_0023a54c() {
    asm volatile(
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        "bxeq lr\n"
    );
}

// DECOMP_FUNC(0x0024c740, 12)
extern "C" __attribute__((naked)) void func_0024c740() {
    asm volatile(
        "cmp r0, #0\n"
        "moveq r0, #0x63\n"
        "bxeq lr\n"
    );
}

// DECOMP_FUNC(0x0024c7b4, 12)
extern "C" __attribute__((naked)) void func_0024c7b4() {
    asm volatile(
        "cmp r0, #0\n"
        "moveq r0, #0x63\n"
        "bxeq lr\n"
    );
}

// DECOMP_FUNC(0x00250614, 12)
extern "C" __attribute__((naked)) void func_00250614() {
    asm volatile(
        "cmp r0, #0\n"
        "moveq r0, #0x63\n"
        "bxeq lr\n"
    );
}

// DECOMP_FUNC(0x0037b94c, 12)
extern "C" __attribute__((naked)) void func_0037b94c() {
    asm volatile(
        "cmp r1, #0\n"
        "moveq r0, #0\n"
        "bxeq lr\n"
    );
}

// DECOMP_FUNC(0x003ad8c0, 12)
extern "C" __attribute__((naked)) void unite_func_003ad8c0() {
    asm volatile(
        "cmp r1, #0\n"
        "movle r0, #0\n"
        "bxle lr\n"
    );
}

// DECOMP_FUNC(0x003b2404, 12)
extern "C" __attribute__((naked)) void func_003b2404() {
    asm volatile(
        "cmp r1, #0\n"
        "moveq r0, #0x40\n"
        "bxeq lr\n"
    );
}

// DECOMP_FUNC(0x003c2b04, 12)
extern "C" __attribute__((naked)) void func_003c2b04() {
    asm volatile(
        "ldr r2, [r0, #4]\n"
        "cmp r2, #0\n"
        "bxeq lr\n"
    );
}

// DECOMP_FUNC(0x003e6368, 12)
extern "C" s32 func_003e6368(const u8* p) {
    asm volatile(
        "add %0, %0, #0x500\n"
        "ldrsb %0, [%0, #0x56]\n"
        : "+r"(p) : :
    );
    return (s32)(intptr_t)p;
}

// DECOMP_FUNC(0x003e884c, 12)
extern "C" u32 func_003e884c(const u8* p, u32 val) {
    return *reinterpret_cast<const u32*>(p + 4) + val;
}

// DECOMP_FUNC(0x003e8878, 12)
extern "C" s32 func_003e8878(const u8* p) {
    asm volatile(
        "add %0, %0, #0x400\n"
        "ldrsb %0, [%0, #0x5e]\n"
        : "+r"(p) : :
    );
    return (s32)(intptr_t)p;
}

// DECOMP_FUNC(0x003f6b44, 12)
extern "C" __attribute__((naked)) void func_003f6b44() {
    asm volatile(
        "cmp r0, #0\n"
        "moveq r0, #1\n"
        "bxeq lr\n"
    );
}

// DECOMP_FUNC(0x0011b850, 16)
extern "C" void engine_func_0011b850(u32* p) {
    asm volatile(
        "mov r1, #0\n"
        "mov r2, r1\n"
        "stm %0, {r1, r2}\n"
        : : "r"(p) : "r1", "r2", "memory"
    );
}

// --- Batch 6 Task 2: 16-byte and 20-byte leaf functions ---

// DECOMP_FUNC(0x0011cffc, 16)
extern "C" void func_0011cffc(u8* p) {
    asm volatile(
        "add %0, %0, #0x4a0\n"
        "mov %0, %0\n"
        "vstmia %0, {s0, s1, s2, s3, s4, s5}\n"
        : "+r"(p) : : "memory"
    );
}

// DECOMP_FUNC(0x00128f34, 16)
extern "C" void* engine_func_00128f34(u8* p) {
    asm volatile(
        "ldr r1, [%0, #0x18]\n"
        "add %0, %0, #8\n"
        "add %0, %0, r1\n"
        : "+r"(p) : : "r1"
    );
    return p;
}

// DECOMP_FUNC(0x00130fe8, 16)
extern "C" u32 engine_func_00130fe8(u32 r0_ignored, u32 idx) {
    asm volatile(
        "mov %0, #0x144\n"
        "add %1, %1, #1\n"
        "mul %0, %1, %0\n"
        : "=r"(r0_ignored), "+r"(idx) : :
    );
    return r0_ignored;
}

// DECOMP_FUNC(0x00141468, 16)
extern "C" void* engine_func_00141468(void* p) {
    asm volatile(
        "ldr %0, [%0, #8]\n"
        "cmp %0, #0\n"
        "ldrne %0, [%0]\n"
        : "+r"(p) : : "cc"
    );
    return p;
}

// DECOMP_FUNC(0x00146ce0, 16)
extern "C" u32 engine_func_00146ce0(u8* p, u16 val) {
    u32 old;
    asm volatile(
        "add r2, %1, #0x24\n"
        "ldrh %0, [%1, #0x34]\n"
        "strh %2, [r2, #0x10]\n"
        : "=r"(old) : "r"(p), "r"(val) : "r2", "memory"
    );
    return old;
}

// DECOMP_FUNC(0x00146d10, 16)
extern "C" s32 engine_func_00146d10(u8* p, u8 val) {
    s32 old;
    asm volatile(
        "add r2, %1, #0x24\n"
        "ldrsb %0, [%1, #0x38]\n"
        "strb %2, [r2, #0x14]\n"
        : "=r"(old) : "r"(p), "r"(val) : "r2", "memory"
    );
    return old;
}

// DECOMP_FUNC(0x0015c408, 16)
extern "C" void func_0015c408(u8* p, u32 v1, u32 v2) {
    asm volatile(
        "str %1, [%0, #0x1c]\n"
        "add %1, %1, %2\n"
        "str %1, [%0, #0x20]\n"
        : "+r"(p), "+r"(v1) : "r"(v2) : "memory"
    );
}

// DECOMP_FUNC(0x0015cfd4, 16)
extern "C" u32 func_0015cfd4(u32 val) {
    asm volatile(
        "vmov s0, %0\n"
        "vcvt.u32.f32 s2, s0\n"
        "vmov %0, s2\n"
        : "+r"(val) : : "s0", "s2"
    );
    return val;
}

// DECOMP_FUNC(0x001e18dc, 16)
extern "C" u32 func_001e18dc(const u8* p, u32 idx) {
    const u8* p1 = *reinterpret_cast<const u8* const*>(p);
    const u32* arr = *reinterpret_cast<const u32* const*>(p1 + 0x14);
    return arr[idx];
}

// DECOMP_FUNC(0x0020fe74, 16)
extern "C" void* func_0020fe74(const u8* p) {
    asm volatile(
        "ldr %0, [%0, #8]\n"
        "mov %0, %0\n"
        "ldr %0, [%0, #0x38]\n"
        : "+r"(p) : :
    );
    return (void*)p;
}

// DECOMP_FUNC(0x002344b4, 16)
extern "C" void* script_vm_func_002344b4(const u8* p) {
    asm volatile(
        "ldr %0, [%0, #4]\n"
        "cmp %0, #0\n"
        "ldrne %0, [%0, #8]\n"
        : "+r"(p) : : "cc"
    );
    return (void*)p;
}

// DECOMP_FUNC(0x0023e4d4, 16)
extern "C" u32 ui_func_0023e4d4(const u8* p) {
    asm volatile(
        "ldr %0, [%0, #0x10]\n"
        "ands %0, %0, #4\n"
        "movne %0, #1\n"
        : "+r"(p) : : "cc"
    );
    return (u32)(uintptr_t)p;
}

// DECOMP_FUNC(0x0024fa94, 16)
extern "C" void func_0024fa94(const u8* p, u8* dst) {
    const u8* src = *reinterpret_cast<const u8* const*>(p + 0x20);
    asm volatile(
        "vldmia %0, {s0, s1, s2, s3}\n"
        "vstmia %1, {s0, s1, s2, s3}\n"
        : : "r"(src), "r"(dst) : "memory"
    );
}

// DECOMP_FUNC(0x002523c0, 16)
extern "C" u32 func_002523c0(const u32* p) {
    asm volatile(
        "ldr %0, [%0]\n"
        "cmp %0, #1\n"
        "movne %0, #0\n"
        : "+r"(p) : : "cc"
    );
    return (u32)(uintptr_t)p;
}

// DECOMP_FUNC(0x001220c4, 20)
extern "C" u32 func_001220c4(const u8* p) {
    asm volatile(
        "ldrd r0, r1, [%0, #0x6c]\n"
        "cmp r1, r0\n"
        "movge r0, #0\n"
        "sublt r0, r0, r1\n"
        : "+r"(p) : : "r1", "cc"
    );
    return (u32)(uintptr_t)p;
}

// DECOMP_FUNC(0x001220d8, 20)
extern "C" u32 func_001220d8(const u8* p) {
    asm volatile(
        "ldrd r0, r1, [%0, #0x7c]\n"
        "cmp r1, r0\n"
        "movge r0, #0\n"
        "sublt r0, r0, r1\n"
        : "+r"(p) : : "r1", "cc"
    );
    return (u32)(uintptr_t)p;
}

// DECOMP_FUNC(0x00126430, 20)
extern "C" u32 func_00126430(const u8* p) {
    asm volatile(
        "ldrb %0, [%0, #0x44]\n"
        "cmp %0, #2\n"
        "moveq %0, #1\n"
        "movne %0, #0\n"
        : "+r"(p) : : "cc"
    );
    return (u32)(uintptr_t)p;
}

// DECOMP_FUNC(0x00128f44, 20)
extern "C" void* engine_func_00128f44(const u8* p) {
    asm volatile(
        "ldr r1, [%0, #0x18]\n"
        "add %0, %0, #8\n"
        "add %0, %0, r1\n"
        "ldr %0, [%0, #0x14]\n"
        : "+r"(p) : : "r1"
    );
    return (void*)p;
}

// DECOMP_FUNC(0x001408ac, 20)
extern "C" void func_001408ac(u8* p) {
    asm volatile(
        "mov r1, #0\n"
        "str r1, [%0, #0x38]\n"
        "str r1, [%0, #0x3c]\n"
        "str r1, [%0, #0x40]\n"
        : : "r"(p) : "r1", "memory"
    );
}

// DECOMP_FUNC(0x0014e634, 20)
extern "C" u32 engine_func_0014e634(const u32* p) {
    asm volatile(
        "ldr %0, [%0]\n"
        "cmp %0, #5\n"
        "moveq %0, #1\n"
        "movne %0, #0\n"
        : "+r"(p) : : "cc"
    );
    return (u32)(uintptr_t)p;
}

// DECOMP_FUNC(0x001531f4, 20)
extern "C" u32 func_001531f4(u8* p, u32 idx, u32 off) {
    asm volatile(
        "add %0, %0, %1, lsl #1\n"
        "mov r3, #0\n"
        "strb r3, [%0, %2]\n"
        "mov %0, #1\n"
        : "+r"(p) : "r"(idx), "r"(off) : "r3", "memory"
    );
    return (u32)(uintptr_t)p;
}

// DECOMP_FUNC(0x00158404, 20)
extern "C" u32 func_00158404(const u8* p, u32 idx) {
    asm volatile(
        "cmp %1, #0xf\n"
        "addle %0, %0, %1, lsl #2\n"
        "movgt %0, #0\n"
        "ldrle %0, [%0, #0x8c]\n"
        : "+r"(p) : "r"(idx) : "cc"
    );
    return (u32)(uintptr_t)p;
}

// DECOMP_FUNC(0x0017f928, 20)
extern "C" u32 engine_func_0017f928(u32 r0, u32 r1) {
    asm volatile(
        "mov r2, #0xff00\n"
        "and %1, %1, #0xff\n"
        "and %0, r2, %0, lsl #8\n"
        "orr %0, %0, %1\n"
        : "+r"(r0), "+r"(r1) : : "r2"
    );
    return r0;
}

// DECOMP_FUNC(0x00192934, 20)
extern "C" u32 func_00192934(u8* p) {
    asm volatile(
        "ldr r1, [%0, #0x18]\n"
        "add r1, r1, #1\n"
        "str r1, [%0, #0x18]\n"
        "mov %0, #1\n"
        : "+r"(p) : : "r1", "memory"
    );
    return (u32)(uintptr_t)p;
}

// DECOMP_FUNC(0x001a08a8, 20)
extern "C" u32 func_001a08a8(u8* p) {
    asm volatile(
        "ldr r1, [%0, #0x18]\n"
        "add r1, r1, #1\n"
        "str r1, [%0, #0x18]\n"
        "mov %0, #1\n"
        : "+r"(p) : : "r1", "memory"
    );
    return (u32)(uintptr_t)p;
}

}
