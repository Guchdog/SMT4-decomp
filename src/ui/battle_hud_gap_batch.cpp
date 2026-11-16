#include "types.h"

extern "C" {
void engine_func_002c3b00(void* ptr);
void engine_func_00225e4c(void* ptr, u32 a1, u32 a2);
}

// Independently bounded ARM reset callbacks split from opaque HUD spans.
// Each naked wrapper preserves its code.bin bytes, including literal pools.
namespace smt4::ui {

// DECOMP_FUNC(0x003f142c, 44)
void func_003f142c() {
    u32* p = reinterpret_cast<u32*>(0x0044E630);
    p[2] = 0x07898BFF;
    p[3] = 0x00000574;
    p[0] = 0x43323000;
    p[1] = 0xFFFFFD21;
}

// DECOMP_FUNC(0x003f1464, 52)
void func_003f1464() {
    u32* p1 = reinterpret_cast<u32*>(0x004732F8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0x00473300);
    p2[0] = 0;
    p2[1] = 0;

    *reinterpret_cast<u32*>(0x004732F0) = 0;
}

// DECOMP_FUNC(0x003f1498, 60)
void func_003f1498() {
    u32* p1 = reinterpret_cast<u32*>(0x00472160);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0x00472168);
    p2[0] = 0;
    p2[1] = 0;

    *reinterpret_cast<u32*>(0x00472158) = 0x00472260;
}

// DECOMP_FUNC(0x003f1558, 60)
void func_003f1558() {
    u32* p1 = reinterpret_cast<u32*>(0x004765B8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0x004765C0);
    p2[0] = 0;
    p2[1] = 0;

    *reinterpret_cast<u32*>(0x004765B0) = 0x00472260;
}

// DECOMP_FUNC(0x003f1594, 48)
void func_003f1594() {
    u32* p = reinterpret_cast<u32*>(0x004EAC50);
    p[0] = 0;
    p[1] = 0;
    p[2] = 0xFFFFFFFF;
    engine_func_00225e4c(p, 0x003576B8, 0x00100000);
}

// DECOMP_FUNC(0x003f15c4, 56)
void func_003f15c4() {
    u32* p = reinterpret_cast<u32*>(0x004E6CC0);
    p[1] = 0;
    p[2] = 0;
    p[3] = 0;
    p[0] = 0x0040B5C8;
    engine_func_00225e4c(p, 0x00394EE8, 0x00100000);
}

// DECOMP_FUNC(0x003f1730, 44)
void func_003f1730() {
    u8* p = reinterpret_cast<u8*>(0x004765D8);
    p[0] = 0x7F;
    p[1] = 0x7F;
    p[2] = 0x7F;
    p[3] = 0x7F;
    p[4] = 0x7F;
}

// DECOMP_FUNC(0x003f175c, 28)
void func_003f175c() {
    u32* p = reinterpret_cast<u32*>(0x004D4668);
    p[0] = 0xBE0;
    p[1] = 0xE60;
    p[2] = 0x820;
}

// DECOMP_FUNC(0x003f1778, 28)
void func_003f1778() {
    u32* p = reinterpret_cast<u32*>(0x004EAD04);
    p[0] = 0xBE0;
    p[1] = 0xE60;
    p[2] = 0x820;
}

// DECOMP_FUNC(0x003f1818, 56)
void func_003f1818() {
    u32* p1 = reinterpret_cast<u32*>(0x00465200);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0x00465208);
    p2[0] = 0;
    p2[1] = 0;

    *reinterpret_cast<u32*>(0x004651F8) = 0;
}

// DECOMP_FUNC(0x003f1a34, 180)
__attribute__((naked)) void func_003f1a34() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2f1a34, 180\n");
}

// DECOMP_FUNC(0x003f1b98, 20)
void func_003f1b98() {
    *reinterpret_cast<u32*>(0x00472A34) = 0;
}

// DECOMP_FUNC(0x003f1cb4, 60)
void func_003f1cb4() {
    u32* p1 = reinterpret_cast<u32*>(0x0044E860);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0x0044E868);
    p2[0] = 0;
    p2[1] = 0;

    *reinterpret_cast<u32*>(0x0044E858) = 0x00472260;
}

// DECOMP_FUNC(0x003f1cf0, 20)
void func_003f1cf0() {
    *reinterpret_cast<u32*>(0x00472AB0) = 0;
}

// DECOMP_FUNC(0x003f1d30, 24)
void func_003f1d30() {
    *reinterpret_cast<u32*>(0x00473528) = 0x0047352C;
}

// DECOMP_FUNC(0x003f1df8, 20)
void func_003f1df8() {
    *reinterpret_cast<u32*>(0x00472AD8) = 0;
}

// DECOMP_FUNC(0x003f1e38, 24)
void func_003f1e38() {
    *reinterpret_cast<u32*>(0x00473564) = 0x00472338;
}

// DECOMP_FUNC(0x003f1e7c, 104)
__attribute__((naked)) void func_003f1e7c() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2f1e7c, 104\n");
}

// DECOMP_FUNC(0x003f1ee4, 284)
__attribute__((naked)) void func_003f1ee4() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2f1ee4, 284\n");
}

// DECOMP_FUNC(0x003f22dc, 132)
__attribute__((naked)) void func_003f22dc() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2f22dc, 132\n");
}

// DECOMP_FUNC(0x003f2360, 128)
__attribute__((naked)) void func_003f2360() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2f2360, 128\n");
}

// DECOMP_FUNC(0x003f24e8, 52)
void func_003f24e8() {
    u32* p1 = reinterpret_cast<u32*>(0x00472000);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0x00472008);
    p2[0] = 0;
    p2[1] = 0;

    *reinterpret_cast<u32*>(0x00471FF8) = 0;
}

// DECOMP_FUNC(0x003f25a0, 20)
void func_003f25a0() {
    *reinterpret_cast<u32*>(0x00472338) = 0;
}

// DECOMP_FUNC(0x003f2690, 168)
__attribute__((naked)) void func_003f2690() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2f2690, 168\n");
}

// DECOMP_FUNC(0x003f28f0, 60)
void func_003f28f0() {
    u32* p1 = reinterpret_cast<u32*>(0x00471F38);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0x00471F40);
    p2[0] = 0;
    p2[1] = 0;

    *reinterpret_cast<u32*>(0x00471F30) = 0x00471FF8;
}

// DECOMP_FUNC(0x003f2984, 60)
void func_003f2984() {
    u32* p1 = reinterpret_cast<u32*>(0x00473388);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0x00473390);
    p2[0] = 0;
    p2[1] = 0;

    *reinterpret_cast<u32*>(0x00473380) = 0x0044E858;
}

// DECOMP_FUNC(0x003f29c0, 56)
void func_003f29c0() {
    u32* p1 = reinterpret_cast<u32*>(0x004733C0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0x004733C8);
    p2[0] = 0;
    p2[1] = 0;

    *reinterpret_cast<u32*>(0x00476624) = 0;
}

// DECOMP_FUNC(0x003f2a50, 52)
void func_003f2a50() {
    u32* p1 = reinterpret_cast<u32*>(0x00472268);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0x00472270);
    p2[0] = 0;
    p2[1] = 0;

    *reinterpret_cast<u32*>(0x00472260) = 0;
}

// DECOMP_FUNC(0x003f2a84, 60)
void func_003f2a84() {
    u32* p1 = reinterpret_cast<u32*>(0x004722D8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0x004722E0);
    p2[0] = 0;
    p2[1] = 0;

    *reinterpret_cast<u32*>(0x004722D0) = 0x004732D8;
}

// DECOMP_FUNC(0x003f2b44, 68)
void func_003f2b44() {
    u32* p1 = reinterpret_cast<u32*>(0x0044E9F0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0x0044E9F8);
    p2[0] = 0;
    p2[1] = 0;

    void* target = reinterpret_cast<void*>(0x0044E9E8);
    *reinterpret_cast<u32*>(target) = 0;
    engine_func_00225e4c(target, 0x003578E8, 0x00100000);
}

// DECOMP_FUNC(0x003efc80, 92)
__attribute__((naked)) void func_003efc80() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2efc80, 92\n");
}

// DECOMP_FUNC(0x003efd08, 120)
__attribute__((naked)) void func_003efd08() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2efd08, 120\n");
}

// DECOMP_FUNC(0x003efeb4, 248)
__attribute__((naked)) void func_003efeb4() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2efeb4, 248\n");
}

// DECOMP_FUNC(0x003f0000, 48)
void func_003f0000() {
    u32* p = reinterpret_cast<u32*>(0x004EF9C0);
    u32 p_plus_4 = reinterpret_cast<u32>(p + 1);
    p[1] = p_plus_4;
    p[0] = 0;
    p[2] = p_plus_4;
    engine_func_00225e4c(p, 0x00361C5C, 0x00100000);
}

// DECOMP_FUNC(0x003f0138, 84)
__attribute__((naked)) void func_003f0138() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2f0138, 84\n");
}

// DECOMP_FUNC(0x003f018c, 836)
__attribute__((naked)) void func_003f018c() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2f018c, 836\n");
}

// DECOMP_FUNC(0x003f0580, 3272)
__attribute__((naked)) void func_003f0580() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2f0580, 3272\n");
}

// DECOMP_FUNC(0x003f2210, 68)
void func_003f2210() {
    u32* p1 = reinterpret_cast<u32*>(0x00465670);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0x00465678);
    p2[0] = 0;
    p2[1] = 0;

    void* target = reinterpret_cast<void*>(0x00465668);
    *reinterpret_cast<u32*>(target) = 0;
    engine_func_00225e4c(target, 0x00357910, 0x00100000);
}

// DECOMP_FUNC(0x003f2254, 92)
void func_003f2254() {
    u32* p1 = reinterpret_cast<u32*>(0x0044E440);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0x0044E448);
    p2[0] = 0;
    p2[1] = 0;

    void* target = reinterpret_cast<void*>(0x004C644C);
    *reinterpret_cast<u32*>(target) = 0;
    engine_func_002c3b00(target);
    engine_func_00225e4c(target, 0x003576B8, 0x00100000);
}

}  // namespace smt4::ui
