#include "types.h"

extern "C" {
void engine_func_00225e4c(void* ptr, u32 a1, u32 a2);
void ui_func_002c5f58(void* base, void* func, u32 elem_size, u32 count);
void func_003772d4(void* ptr);
void ui_func_0037e2b4(void* ptr);
void func_003613f4(void* ptr);
}

// Verified ARM-state BattleMessageWindow tail entries. Each span includes its
// adjacent PC-relative literal pool; every emitted byte is checked against code.bin.
// DECOMP_FUNC(0x003f3960, 44)
void func_003f3960() {
    u32* p1 = reinterpret_cast<u32*>(0X44D0D8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44D0E0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f398c, 44)
void func_003f398c() {
    u32* p1 = reinterpret_cast<u32*>(0X44D138);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44D140);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f39b8, 44)
void func_003f39b8() {
    u32* p1 = reinterpret_cast<u32*>(0X4764C8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X4764D0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f39e4, 44)
void func_003f39e4() {
    u32* p1 = reinterpret_cast<u32*>(0X472960);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X472968);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f3a10, 20)
void func_003f3a10() {
    *reinterpret_cast<u32*>(0X471B6C) = 0;
}
// DECOMP_FUNC(0x003f3a24, 20)
void func_003f3a24() {
    *reinterpret_cast<u32*>(0X471B74) = 0;
}
// DECOMP_FUNC(0x003f3a38, 56)
void func_003f3a38() {
    *reinterpret_cast<u8*>(0X4E6F14) = 0X0;
    *reinterpret_cast<u32*>(0X4E6F58) = 0X0;
    *reinterpret_cast<u32*>(0X4E6F5C) = 0X0;
    *reinterpret_cast<u32*>(0X4E6F60) = 0XFFFFFFFF;
    engine_func_00225e4c(reinterpret_cast<void*>(0X4E6F14), 0X360148, 0X100000);
}
// DECOMP_FUNC(0x003f3a70, 24)
void func_003f3a70() {
    *reinterpret_cast<u32*>(0X473538) = 0X472338;
}
// DECOMP_FUNC(0x003f3a88, 44)
void func_003f3a88() {
    u32* p1 = reinterpret_cast<u32*>(0X471B80);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X471B88);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f3ab4, 44)
void func_003f3ab4() {
    *reinterpret_cast<u32*>(0X1000EEFC) = 0X0;
    *reinterpret_cast<u8*>(0X4765DD) = 0X7F;
    *reinterpret_cast<u8*>(0X4765DE) = 0X7F;
    *reinterpret_cast<u8*>(0X4765DF) = 0X7F;
    *reinterpret_cast<u8*>(0X4765E0) = 0X7F;
    *reinterpret_cast<u8*>(0X4765E1) = 0X7F;
}
// DECOMP_FUNC(0x003f3ae0, 44)
void func_003f3ae0() {
    u32* p1 = reinterpret_cast<u32*>(0X4729E8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X4729F0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f3b0c, 44)
void func_003f3b0c() {
    u32* p1 = reinterpret_cast<u32*>(0X4330D0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X4330D8);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f3b38, 44)
void func_003f3b38() {
    u32* p1 = reinterpret_cast<u32*>(0X472788);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X472790);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f3b64, 120)
void func_003f3b64() {
    *reinterpret_cast<u32*>(0x4720A0) = 0xBF0000;
    *reinterpret_cast<u32*>(0x4720A8) = 0xFFFFFFFF;
    *reinterpret_cast<u32*>(0x4720AC) = 0xFFFFFFFF;
    *reinterpret_cast<u32*>(0x4720B0) = 0;
    *reinterpret_cast<u32*>(0x4720B4) = 0;
    ui_func_002c5f58(reinterpret_cast<void*>(0x4E9DC8), reinterpret_cast<void*>(0x17F5C0), 4, 0x18);
    *reinterpret_cast<u32*>(0x4720BC) = 0x000F0111;
    *reinterpret_cast<u32*>(0x4720C4) = 0x000F0110;
    *reinterpret_cast<u32*>(0x4720CC) = 0x803F0112;
}
// DECOMP_FUNC(0x003f3bdc, 60)
void func_003f3bdc() {
    *reinterpret_cast<u32*>(0X473360) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X473364) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X473368) = 0X0;
    *reinterpret_cast<u32*>(0X47336C) = 0X0;
    *reinterpret_cast<u32*>(0X473358) = 0X472128;
}
// DECOMP_FUNC(0x003f3c18, 44)
void func_003f3c18() {
    u32* p1 = reinterpret_cast<u32*>(0X473370);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X473378);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f3c44, 44)
void func_003f3c44() {
    u32* p1 = reinterpret_cast<u32*>(0X4734D0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X4734D8);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f3c70, 60)
void func_003f3c70() {
    *reinterpret_cast<u32*>(0X473400) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X473404) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X473408) = 0X0;
    *reinterpret_cast<u32*>(0X47340C) = 0X0;
    *reinterpret_cast<u32*>(0X4733F8) = 0X476560;
}
// DECOMP_FUNC(0x003f3cac, 60)
void func_003f3cac() {
    *reinterpret_cast<u32*>(0X44E890) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X44E894) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X44E898) = 0X0;
    *reinterpret_cast<u32*>(0X44E89C) = 0X0;
    *reinterpret_cast<u32*>(0X44E888) = 0X4722B8;
}
// DECOMP_FUNC(0x003f3ce8, 44)
void func_003f3ce8() {
    u32* p1 = reinterpret_cast<u32*>(0X472AB8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X472AC0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f3d14, 44)
void func_003f3d14() {
    u32* p1 = reinterpret_cast<u32*>(0X472B10);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X472B18);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f3d40, 44)
void func_003f3d40() {
    u32* p1 = reinterpret_cast<u32*>(0X472B30);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X472B38);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f3d6c, 44)
void func_003f3d6c() {
    u32* p1 = reinterpret_cast<u32*>(0X476518);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X476520);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f3d98, 40)
void func_003f3d98() {
    func_003772d4(reinterpret_cast<void*>(0x4EA4B4));
    engine_func_00225e4c(reinterpret_cast<void*>(0x4EA4B4), 0x37730C, 0x100000);
}
// DECOMP_FUNC(0x003f3dc0, 44)
void func_003f3dc0() {
    u32* p1 = reinterpret_cast<u32*>(0X472980);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X472988);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f3dec, 44)
void func_003f3dec() {
    u32* p1 = reinterpret_cast<u32*>(0X43DEC0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X43DEC8);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f3e18, 44)
void func_003f3e18() {
    u32* p1 = reinterpret_cast<u32*>(0X44D050);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44D058);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f3e44, 44)
void func_003f3e44() {
    u32* p1 = reinterpret_cast<u32*>(0X465620);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X465628);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f3e70, 172)
void func_003f3e70() {
    *reinterpret_cast<u32*>(0x465650) = 0xFFFFFFFF;
    *reinterpret_cast<u32*>(0x465654) = 0xFFFFFFFF;
    *reinterpret_cast<u32*>(0x465658) = 0;
    *reinterpret_cast<u32*>(0x46565C) = 0;
    ui_func_002c5f58(reinterpret_cast<void*>(0x4E5290), reinterpret_cast<void*>(0x3578DC), 4, 3);
    *reinterpret_cast<u32*>(0x46563C) = 0;
    *reinterpret_cast<u8*>(0x465640) = 1;
    *reinterpret_cast<u32*>(0x465644) = 0;
    *reinterpret_cast<u32*>(0x465648) = 0;
    engine_func_00225e4c(reinterpret_cast<void*>(0x465644), 0x3575B0, 0x100000);
}
// DECOMP_FUNC(0x003f3f1c, 208)
void func_003f3f1c() {
    *reinterpret_cast<u32*>(0X471C48) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X471C4C) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X471C50) = 0X0;
    *reinterpret_cast<u32*>(0X471C54) = 0X0;
    *reinterpret_cast<u32*>(0X471C5C) = 0XF0202;
    *reinterpret_cast<u32*>(0X471C64) = 0XF0205;
    *reinterpret_cast<u32*>(0X471C6C) = 0XF0208;
    *reinterpret_cast<u32*>(0X471C74) = 0XF020B;
    *reinterpret_cast<u32*>(0X471C7C) = 0XF020E;
    *reinterpret_cast<u32*>(0X471C84) = 0XF0211;
    *reinterpret_cast<u32*>(0X471C8C) = 0XF0214;
    *reinterpret_cast<u32*>(0X471C94) = 0XF0217;
    *reinterpret_cast<u32*>(0X471C9C) = 0XF021A;
    *reinterpret_cast<u32*>(0X471CA4) = 0XF021D;
    *reinterpret_cast<u32*>(0X471CAC) = 0XF0220;
    *reinterpret_cast<u32*>(0X471CB4) = 0XF0223;
    *reinterpret_cast<u32*>(0X471CBC) = 0XF0226;
    *reinterpret_cast<u32*>(0X471CC4) = 0X803F0232;
    *reinterpret_cast<u32*>(0X471CDC) = 0X803F0232;
    *reinterpret_cast<u32*>(0X471CF4) = 0X803F0232;
    *reinterpret_cast<u32*>(0X471D0C) = 0X803F0232;
    *reinterpret_cast<u32*>(0X471D24) = 0X803F0232;
    *reinterpret_cast<u32*>(0X471D3C) = 0X803F0232;
    *reinterpret_cast<u32*>(0X471D54) = 0X803F0232;
    *reinterpret_cast<u32*>(0X471D6C) = 0X803F0232;
    *reinterpret_cast<u32*>(0X471D84) = 0X803F0232;
    *reinterpret_cast<u32*>(0X471D9C) = 0X803F0232;
    *reinterpret_cast<u32*>(0X471DB4) = 0X803F0232;
}
// DECOMP_FUNC(0x003f3fec, 60)
void func_003f3fec() {
    *reinterpret_cast<u32*>(0X472118) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X47211C) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X472120) = 0X0;
    *reinterpret_cast<u32*>(0X472124) = 0X0;
    *reinterpret_cast<u32*>(0X472110) = 0X4732D8;
}
// DECOMP_FUNC(0x003f4028, 60)
void func_003f4028() {
    *reinterpret_cast<u32*>(0X473348) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X47334C) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X473350) = 0X0;
    *reinterpret_cast<u32*>(0X473354) = 0X0;
    *reinterpret_cast<u32*>(0X473340) = 0X472128;
}
// DECOMP_FUNC(0x003f4064, 60)
void func_003f4064() {
    *reinterpret_cast<u32*>(0X4721B8) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4721BC) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4721C0) = 0X0;
    *reinterpret_cast<u32*>(0X4721C4) = 0X0;
    *reinterpret_cast<u32*>(0X4721B0) = 0X4722B8;
}
// DECOMP_FUNC(0x003f40a0, 44)
void func_003f40a0() {
    u32* p1 = reinterpret_cast<u32*>(0X4722E8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X4722F0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f40cc, 44)
void func_003f40cc() {
    u32* p1 = reinterpret_cast<u32*>(0X473440);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X473448);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f40f8, 44)
void func_003f40f8() {
    u32* p1 = reinterpret_cast<u32*>(0X473868);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X473870);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4124, 44)
void func_003f4124() {
    u32* p1 = reinterpret_cast<u32*>(0X471B28);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X471B30);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4150, 268)
void func_003f4150() {
    ui_func_002c5f58(reinterpret_cast<void*>(0x4EA428), reinterpret_cast<void*>(0x17F5E8), 8, 7);
    *reinterpret_cast<u32*>(0x4EA460) = 0;
    *reinterpret_cast<u32*>(0x4EA464) = 0;
    *reinterpret_cast<u32*>(0x4EA468) = 0;
    *reinterpret_cast<u32*>(0x472348) = 0x00421838;
    *reinterpret_cast<u32*>(0x47234C) = 0x00421824;
    *reinterpret_cast<u32*>(0x472350) = 0x0042184C;
    *reinterpret_cast<u32*>(0x472354) = 0x004218FC;
    *reinterpret_cast<u32*>(0x472358) = 0x00421910;
    ui_func_0037e2b4(reinterpret_cast<void*>(0x4EA168));
    engine_func_00225e4c(reinterpret_cast<void*>(0x4EA168), 0x37E3F8, 0x100000);
}
// DECOMP_FUNC(0x003f425c, 44)
void func_003f425c() {
    u32* p1 = reinterpret_cast<u32*>(0X4330F0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X4330F8);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4288, 44)
void func_003f4288() {
    u32* p1 = reinterpret_cast<u32*>(0X44E498);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44E4A0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f42b4, 60)
void func_003f42b4() {
    *reinterpret_cast<u32*>(0X471FE8) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X471FEC) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X471FF0) = 0X0;
    *reinterpret_cast<u32*>(0X471FF4) = 0X0;
    *reinterpret_cast<u32*>(0X471FE0) = 0X471F30;
}
// DECOMP_FUNC(0x003f42f0, 44)
void func_003f42f0() {
    u32* p1 = reinterpret_cast<u32*>(0X476538);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X476540);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f431c, 44)
void func_003f431c() {
    u32* p1 = reinterpret_cast<u32*>(0X44E8F8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44E900);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4348, 44)
void func_003f4348() {
    u32* p1 = reinterpret_cast<u32*>(0X472228);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X472230);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4374, 60)
void func_003f4374() {
    *reinterpret_cast<u32*>(0X4733E8) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4733EC) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4733F0) = 0X0;
    *reinterpret_cast<u32*>(0X4733F4) = 0X0;
    *reinterpret_cast<u32*>(0X4733E0) = 0X476560;
}
// DECOMP_FUNC(0x003f43b0, 44)
void func_003f43b0() {
    u32* p1 = reinterpret_cast<u32*>(0X4765A0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X4765A8);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f43dc, 60)
void func_003f43dc() {
    *reinterpret_cast<u32*>(0X473470) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X473474) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X473478) = 0X0;
    *reinterpret_cast<u32*>(0X47347C) = 0X0;
    *reinterpret_cast<u32*>(0X473468) = 0X4765B0;
}
// DECOMP_FUNC(0x003f4418, 128)
void func_003f4418() {
    *reinterpret_cast<u32*>(0X1000EEF8) = 0X0;
    *reinterpret_cast<u32*>(0X1000EEFC) = 0X0;
    *reinterpret_cast<u32*>(0X44D118) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X44D11C) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X44D120) = 0X0;
    *reinterpret_cast<u32*>(0X44D124) = 0X0;
    *reinterpret_cast<u32*>(0X44D128) = 0X0;
    *reinterpret_cast<u8*>(0X44D12C) = 0X1;
    *reinterpret_cast<u32*>(0X4C40F8) = 0X0;
    *reinterpret_cast<u32*>(0X4C4100) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4C40FC) = 0X0;
    engine_func_00225e4c(reinterpret_cast<void*>(0X4C40F8), 0X3576B8, 0X100000);
}
// DECOMP_FUNC(0x003f4498, 44)
void func_003f4498() {
    u32* p1 = reinterpret_cast<u32*>(0X471AF0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X471AF8);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f44c4, 44)
void func_003f44c4() {
    u32* p1 = reinterpret_cast<u32*>(0X4765F0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X4765F8);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f44f0, 20)
void func_003f44f0() {
    *reinterpret_cast<u32*>(0X471B70) = 0;
}
// DECOMP_FUNC(0x003f4504, 44)
void func_003f4504() {
    u32* p1 = reinterpret_cast<u32*>(0X433D88);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X433D90);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4530, 44)
void func_003f4530() {
    *reinterpret_cast<u32*>(0X472A60) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X472A64) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X472A68) = 0X0;
    *reinterpret_cast<u32*>(0X472A6C) = 0X0;
    *reinterpret_cast<u32*>(0X472A58) = 0X0;
}
// DECOMP_FUNC(0x003f455c, 44)
void func_003f455c() {
    u32* p1 = reinterpret_cast<u32*>(0X433090);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X433098);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4588, 60)
void func_003f4588() {
    *reinterpret_cast<u32*>(0X44E810) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X44E814) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X44E818) = 0X0;
    *reinterpret_cast<u32*>(0X44E81C) = 0X0;
    *reinterpret_cast<u32*>(0X44E808) = 0X471FF8;
}
// DECOMP_FUNC(0x003f45c4, 124)
void func_003f45c4() {
    *reinterpret_cast<u32*>(0X4732B0) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4732B4) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4732B8) = 0X0;
    *reinterpret_cast<u32*>(0X4732BC) = 0X0;
    *reinterpret_cast<u32*>(0X4732A8) = 0X0;
    *reinterpret_cast<u32*>(0X4EAD50) = 0X0;
    *reinterpret_cast<u32*>(0X4EAD54) = 0X0;
    *reinterpret_cast<u32*>(0X4EAD58) = 0XBF800000;
    *reinterpret_cast<u32*>(0X4EAD5C) = 0X0;
    *reinterpret_cast<u32*>(0X4EAD60) = 0X3F800000;
    *reinterpret_cast<u32*>(0X4EAD64) = 0X0;
    *reinterpret_cast<u32*>(0X4EAD68) = 0X0;
    *reinterpret_cast<u32*>(0X4EAD6C) = 0X0;
    *reinterpret_cast<u32*>(0X4EAD70) = 0X0;
}
// DECOMP_FUNC(0x003f4640, 60)
void func_003f4640() {
    *reinterpret_cast<u32*>(0X473310) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X473314) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X473318) = 0X0;
    *reinterpret_cast<u32*>(0X47331C) = 0X0;
    *reinterpret_cast<u32*>(0X473308) = 0X4732C0;
}
// DECOMP_FUNC(0x003f467c, 44)
void func_003f467c() {
    u32* p1 = reinterpret_cast<u32*>(0X4765C8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X4765D0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f46a8, 60)
void func_003f46a8() {
    *reinterpret_cast<u32*>(0X472218) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X47221C) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X472220) = 0X0;
    *reinterpret_cast<u32*>(0X472224) = 0X0;
    *reinterpret_cast<u32*>(0X472210) = 0X4732A8;
}
// DECOMP_FUNC(0x003f46e4, 12)
void func_003f46e4() {
    func_003613f4(reinterpret_cast<void*>(0x4EF9CC));
}
// DECOMP_FUNC(0x003f46f0, 44)
void func_003f46f0() {
    u32* p1 = reinterpret_cast<u32*>(0X472B00);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X472B08);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f471c, 44)
void func_003f471c() {
    u32* p1 = reinterpret_cast<u32*>(0X476508);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X476510);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4748, 20)
void func_003f4748() {
    *reinterpret_cast<u32*>(0X471B68) = 0;
}
// DECOMP_FUNC(0x003f475c, 56)
void func_003f475c() {
    *reinterpret_cast<u8*>(0X4EAD10) = 0X0;
    *reinterpret_cast<u32*>(0X4EAD44) = 0X0;
    *reinterpret_cast<u32*>(0X4EAD48) = 0X0;
    *reinterpret_cast<u32*>(0X4EAD4C) = 0XFFFFFFFF;
    engine_func_00225e4c(reinterpret_cast<void*>(0X4EAD10), 0X3602DC, 0X100000);
}
// DECOMP_FUNC(0x003f4794, 44)
void func_003f4794() {
    u32* p1 = reinterpret_cast<u32*>(0X4640F0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X4640F8);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f47c0, 44)
void func_003f47c0() {
    u32* p1 = reinterpret_cast<u32*>(0X4330E0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X4330E8);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f47ec, 44)
void func_003f47ec() {
    u32* p1 = reinterpret_cast<u32*>(0X433100);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X433108);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4818, 52)
void func_003f4818() {
    *reinterpret_cast<u32*>(0X4732C8) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4732CC) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4732D0) = 0X0;
    *reinterpret_cast<u32*>(0X4732D4) = 0X0;
    *reinterpret_cast<u32*>(0X4732C0) = 0X0;
}
// DECOMP_FUNC(0x003f484c, 60)
void func_003f484c() {
    *reinterpret_cast<u32*>(0X476590) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X476594) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X476598) = 0X0;
    *reinterpret_cast<u32*>(0X47659C) = 0X0;
    *reinterpret_cast<u32*>(0X476588) = 0X472260;
}
// DECOMP_FUNC(0x003f4888, 44)
void func_003f4888() {
    u32* p1 = reinterpret_cast<u32*>(0X473490);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X473498);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f48b4, 44)
void func_003f48b4() {
    u32* p1 = reinterpret_cast<u32*>(0X44E9C8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44E9D0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f48e0, 44)
void func_003f48e0() {
    u32* p1 = reinterpret_cast<u32*>(0X44E998);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44E9A0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f490c, 44)
void func_003f490c() {
    u32* p1 = reinterpret_cast<u32*>(0X4764B8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X4764C0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4938, 44)
void func_003f4938() {
    u32* p1 = reinterpret_cast<u32*>(0X472010);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X472018);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4964, 44)
void func_003f4964() {
    u32* p1 = reinterpret_cast<u32*>(0X472A78);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X472A80);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4990, 44)
void func_003f4990() {
    u32* p1 = reinterpret_cast<u32*>(0X472AA0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X472AA8);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f49bc, 44)
void func_003f49bc() {
    u32* p1 = reinterpret_cast<u32*>(0X472AE0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X472AE8);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f49e8, 44)
void func_003f49e8() {
    u32* p1 = reinterpret_cast<u32*>(0X476610);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X476618);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4a14, 44)
void func_003f4a14() {
    u32* p1 = reinterpret_cast<u32*>(0X4656A0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X4656A8);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4a40, 60)
void func_003f4a40() {
    *reinterpret_cast<u32*>(0X471F08) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X471F0C) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X471F10) = 0X0;
    *reinterpret_cast<u32*>(0X471F14) = 0X0;
    *reinterpret_cast<u32*>(0X471F00) = 0X4732A8;
}
// DECOMP_FUNC(0x003f4a7c, 44)
void func_003f4a7c() {
    u32* p1 = reinterpret_cast<u32*>(0X473480);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X473488);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4aa8, 44)
void func_003f4aa8() {
    u32* p1 = reinterpret_cast<u32*>(0X4330A0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X4330A8);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4ad4, 44)
void func_003f4ad4() {
    u32* p1 = reinterpret_cast<u32*>(0X472AC8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X472AD0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4b00, 44)
void func_003f4b00() {
    u32* p1 = reinterpret_cast<u32*>(0X44E938);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44E940);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4b2c, 44)
void func_003f4b2c() {
    u32* p1 = reinterpret_cast<u32*>(0X4764D8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X4764E0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4b58, 60)
void func_003f4b58() {
    *reinterpret_cast<u32*>(0X4721A0) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4721A4) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4721A8) = 0X0;
    *reinterpret_cast<u32*>(0X4721AC) = 0X0;
    *reinterpret_cast<u32*>(0X472198) = 0X473288;
}
// DECOMP_FUNC(0x003f4b94, 60)
void func_003f4b94() {
    *reinterpret_cast<u32*>(0X44E878) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X44E87C) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X44E880) = 0X0;
    *reinterpret_cast<u32*>(0X44E884) = 0X0;
    *reinterpret_cast<u32*>(0X44E870) = 0X44E808;
}
// DECOMP_FUNC(0x003f4bd0, 44)
void func_003f4bd0() {
    u32* p1 = reinterpret_cast<u32*>(0X44D0E8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44D0F0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4bfc, 44)
void func_003f4bfc() {
    u32* p1 = reinterpret_cast<u32*>(0X4764F8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X476500);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4c28, 44)
void func_003f4c28() {
    u32* p1 = reinterpret_cast<u32*>(0X471A58);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X471A60);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4c54, 72)
void func_003f4c54() {
    *reinterpret_cast<u32*>(0X473298) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X47329C) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4732A0) = 0X0;
    *reinterpret_cast<u32*>(0X4732A4) = 0X0;
    *reinterpret_cast<u32*>(0X473288) = 0X0;
    *reinterpret_cast<u32*>(0X47328C) = 0X0;
    *reinterpret_cast<u32*>(0X473290) = 0X0;
}
// DECOMP_FUNC(0x003f4c9c, 60)
void func_003f4c9c() {
    *reinterpret_cast<u32*>(0X472148) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X47214C) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X472150) = 0X0;
    *reinterpret_cast<u32*>(0X472154) = 0X0;
    *reinterpret_cast<u32*>(0X472140) = 0X4732A8;
}
// DECOMP_FUNC(0x003f4cd8, 44)
void func_003f4cd8() {
    u32* p1 = reinterpret_cast<u32*>(0X476578);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X476580);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4d04, 60)
void func_003f4d04() {
    *reinterpret_cast<u32*>(0X472240) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X472244) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X472248) = 0X0;
    *reinterpret_cast<u32*>(0X47224C) = 0X0;
    *reinterpret_cast<u32*>(0X472238) = 0X472260;
}
// DECOMP_FUNC(0x003f4d40, 60)
void func_003f4d40() {
    *reinterpret_cast<u32*>(0X473430) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X473434) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X473438) = 0X0;
    *reinterpret_cast<u32*>(0X47343C) = 0X0;
    *reinterpret_cast<u32*>(0X473428) = 0X4732C0;
}
// DECOMP_FUNC(0x003f4d7c, 60)
void func_003f4d7c() {
    *reinterpret_cast<u32*>(0X472078) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X47207C) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X472080) = 0X0;
    *reinterpret_cast<u32*>(0X472084) = 0X0;
    *reinterpret_cast<u32*>(0X472070) = 0X473288;
}
// DECOMP_FUNC(0x003f4db8, 44)
void func_003f4db8() {
    u32* p1 = reinterpret_cast<u32*>(0X473878);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X473880);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4de4, 44)
void func_003f4de4() {
    u32* p1 = reinterpret_cast<u32*>(0X476600);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X476608);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4e10, 44)
void func_003f4e10() {
    u32* p1 = reinterpret_cast<u32*>(0X4764E8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X4764F0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4e3c, 60)
void func_003f4e3c() {
    *reinterpret_cast<u32*>(0X4721D0) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4721D4) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4721D8) = 0X0;
    *reinterpret_cast<u32*>(0X4721DC) = 0X0;
    *reinterpret_cast<u32*>(0X4721C8) = 0X4732C0;
}
// DECOMP_FUNC(0x003f4e78, 60)
void func_003f4e78() {
    *reinterpret_cast<u32*>(0X4722A8) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4722AC) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4722B0) = 0X0;
    *reinterpret_cast<u32*>(0X4722B4) = 0X0;
    *reinterpret_cast<u32*>(0X4722A0) = 0X471FE0;
}
// DECOMP_FUNC(0x003f4eb4, 44)
void func_003f4eb4() {
    u32* p1 = reinterpret_cast<u32*>(0X44D148);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44D150);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4ee0, 44)
void func_003f4ee0() {
    u32* p1 = reinterpret_cast<u32*>(0X44E920);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44E928);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4f0c, 44)
void func_003f4f0c() {
    u32* p1 = reinterpret_cast<u32*>(0X44E968);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44E970);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4f38, 84)
void func_003f4f38() {
    *reinterpret_cast<u32*>(0X44E980) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X44E984) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X44E988) = 0X0;
    *reinterpret_cast<u32*>(0X44E98C) = 0X0;
    *reinterpret_cast<u32*>(0X4D4674) = 0X0;
    *reinterpret_cast<u32*>(0X4D4678) = 0X0;
    *reinterpret_cast<u32*>(0X4D467C) = 0XFFFFFFFF;
    engine_func_00225e4c(reinterpret_cast<void*>(0X4D4674), 0X3576B8, 0X100000);
}
// DECOMP_FUNC(0x003f4f8c, 52)
void func_003f4f8c() {
    *reinterpret_cast<u32*>(0X473458) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X47345C) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X473460) = 0X0;
    *reinterpret_cast<u32*>(0X473464) = 0X0;
    *reinterpret_cast<u32*>(0X473450) = 0X0;
}
// DECOMP_FUNC(0x003f4fc0, 44)
void func_003f4fc0() {
    u32* p1 = reinterpret_cast<u32*>(0X44E9A8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44E9B0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f4fec, 44)
void func_003f4fec() {
    u32* p1 = reinterpret_cast<u32*>(0X44E9D8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44E9E0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f5018, 60)
void func_003f5018() {
    *reinterpret_cast<u32*>(0X472200) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X472204) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X472208) = 0X0;
    *reinterpret_cast<u32*>(0X47220C) = 0X0;
    *reinterpret_cast<u32*>(0X4721F8) = 0X473288;
}
// DECOMP_FUNC(0x003f5054, 44)
void func_003f5054() {
    u32* p1 = reinterpret_cast<u32*>(0X472AF0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X472AF8);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f5080, 44)
void func_003f5080() {
    u32* p1 = reinterpret_cast<u32*>(0X44E9B8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44E9C0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f50ac, 44)
void func_003f50ac() {
    u32* p1 = reinterpret_cast<u32*>(0X44E1C0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44E1C8);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f50d8, 44)
void func_003f50d8() {
    u32* p1 = reinterpret_cast<u32*>(0X44E0B8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44E0C0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f5104, 44)
void func_003f5104() {
    u32* p1 = reinterpret_cast<u32*>(0X433218);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X433220);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f5130, 44)
void func_003f5130() {
    u32* p1 = reinterpret_cast<u32*>(0X433D58);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X433D60);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f515c, 44)
void func_003f515c() {
    u32* p1 = reinterpret_cast<u32*>(0X433D68);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X433D70);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f5188, 44)
void func_003f5188() {
    u32* p1 = reinterpret_cast<u32*>(0X433D78);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X433D80);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f51b4, 44)
void func_003f51b4() {
    u32* p1 = reinterpret_cast<u32*>(0X44E0A0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44E0A8);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f51e0, 44)
void func_003f51e0() {
    u32* p1 = reinterpret_cast<u32*>(0X43DA98);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X43DAA0);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f520c, 44)
void func_003f520c() {
    u32* p1 = reinterpret_cast<u32*>(0X433250);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X433258);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f5238, 68)
void func_003f5238() {
    *reinterpret_cast<u32*>(0X446DE0) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X446DE4) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X446DE8) = 0X0;
    *reinterpret_cast<u32*>(0X446DEC) = 0X0;
    *reinterpret_cast<u32*>(0X446DD0) = 0X0;
    *reinterpret_cast<u32*>(0X446DD4) = 0X0;
    *reinterpret_cast<u32*>(0X446DD8) = 0X0;
    *reinterpret_cast<u32*>(0X446DDC) = 0X0;
}
// DECOMP_FUNC(0x003f527c, 44)
void func_003f527c() {
    u32* p1 = reinterpret_cast<u32*>(0X472378);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X472380);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f52a8, 44)
void func_003f52a8() {
    u32* p1 = reinterpret_cast<u32*>(0X43DF18);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X43DF20);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f52d4, 44)
void func_003f52d4() {
    u32* p1 = reinterpret_cast<u32*>(0X446538);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X446540);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f5300, 44)
void func_003f5300() {
    u32* p1 = reinterpret_cast<u32*>(0X43DD70);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X43DD78);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f532c, 20)
void func_003f532c() {
    *reinterpret_cast<u32*>(0X4655F8) = 0;
}
// DECOMP_FUNC(0x003f5340, 44)
void func_003f5340() {
    u32* p1 = reinterpret_cast<u32*>(0X439CB0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X439CB8);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f536c, 100)
void func_003f536c() {
    *reinterpret_cast<u32*>(0X4474E0) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4474E4) = 0XFFFFFFFF;
    *reinterpret_cast<u32*>(0X4474E8) = 0X0;
    *reinterpret_cast<u32*>(0X4474EC) = 0X0;
    *reinterpret_cast<u32*>(0X49F114) = 0X0;
    *reinterpret_cast<u8*>(0X49F118) = 0X1;
    *reinterpret_cast<u32*>(0X49F124) = 0X0;
    *reinterpret_cast<u32*>(0X49F128) = 0X0;
    *reinterpret_cast<u32*>(0X49F12C) = 0XFFFFFFFF;
    engine_func_00225e4c(reinterpret_cast<void*>(0X49F0DC), 0X33B80C, 0X100000);
}
// DECOMP_FUNC(0x003f53d0, 44)
void func_003f53d0() {
    u32* p1 = reinterpret_cast<u32*>(0X447A88);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X447A90);
    p2[0] = 0;
    p2[1] = 0;
}
// DECOMP_FUNC(0x003f53fc, 44)
void func_003f53fc() {
    u32* p1 = reinterpret_cast<u32*>(0X44E130);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0X44E138);
    p2[0] = 0;
    p2[1] = 0;
}
