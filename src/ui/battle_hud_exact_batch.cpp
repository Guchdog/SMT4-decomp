#include "types.h"

extern "C" {
void engine_func_00225e4c(void* ptr, u32 a1, u32 a2);
}

// Exact-address ARMv6K wrappers for bounded battle HUD records.
// Code ends at a return or external tail branch; attached literal pools are
// included in each exact span. Direct/static external references were not
// established for every leaf, so names remain address-based.

// DECOMP_FUNC(0x003ec9e8, 44)
void func_003ec9e8() {
    u32* p1 = reinterpret_cast<u32*>(0x00446FD8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003eca14, 44)
void func_003eca14() {
    u32* p1 = reinterpret_cast<u32*>(0x0043E1A8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003eca40, 44)
void func_003eca40() {
    u32* p1 = reinterpret_cast<u32*>(0x0044E2C0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003eca6c, 20)
void func_003eca6c() {
    *reinterpret_cast<u32*>(0x00471BAC) = 0;
}


// DECOMP_FUNC(0x003eca80, 268)
__attribute__((naked, used)) void func_003eca80() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2eca80, 268\n");
}

// DECOMP_FUNC(0x003ecb8c, 44)
void func_003ecb8c() {
    u32* p1 = reinterpret_cast<u32*>(0x00464C08);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ecbb8, 192)
__attribute__((naked, used)) void func_003ecbb8() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2ecbb8, 192\n");
}

// DECOMP_FUNC(0x003ecc78, 44)
void func_003ecc78() {
    u32* p1 = reinterpret_cast<u32*>(0x004650D0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ecca4, 44)
void func_003ecca4() {
    u32* p1 = reinterpret_cast<u32*>(0x00473568);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003eccd0, 44)
void func_003eccd0() {
    u32* p1 = reinterpret_cast<u32*>(0x0043DB48);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003eccfc, 44)
void func_003eccfc() {
    u32* p1 = reinterpret_cast<u32*>(0x004463D0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ecd28, 44)
void func_003ecd28() {
    u32* p1 = reinterpret_cast<u32*>(0x0043DC10);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ecd54, 44)
void func_003ecd54() {
    u32* p1 = reinterpret_cast<u32*>(0x0043DC38);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ecd80, 44)
void func_003ecd80() {
    u32* p1 = reinterpret_cast<u32*>(0x00433280);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ecdac, 468)
void func_003ecdac() {
    u32* p1 = reinterpret_cast<u32*>(0x00433A60);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;

    u32* p2 = reinterpret_cast<u32*>(0x00433A90);
    p2[0] = 0x3F000000;
    p2[1] = 0x3F000000;
    p2[2] = 0x3F000000;
    p2[3] = 0x3F800000;

    *reinterpret_cast<u32*>(0x00433AC0) = 0x3EEB851F;
    *reinterpret_cast<u32*>(0x00433ACC) = 0x3F800000;
    u32* p3 = reinterpret_cast<u32*>(0x00433AC4);
    p3[0] = 0x3EA8F5C3;
    p3[1] = 0x3EC7AE14;

    u32* p4 = reinterpret_cast<u32*>(0x00433AF0);
    p4[0] = 0x3E3851EC;
    p4[1] = 0x3ED1EB85;
    p4[2] = 0x3EF5C28F;
    p4[3] = 0x3F800000;

    u32* p5 = reinterpret_cast<u32*>(0x00433B20);
    p5[0] = 0x3DE147AE;
    p5[1] = 0x3E6147AE;
    p5[2] = 0x3EDC28F6;
    p5[3] = 0x3F800000;

    u32* p6 = reinterpret_cast<u32*>(0x00433B50);
    p6[0] = 0x3E6147AE;
    p6[1] = 0x3EB851EC;
    p6[2] = 0x3E051EB8;
    p6[3] = 0x3F800000;

    u32* p7 = reinterpret_cast<u32*>(0x00433B80);
    p7[0] = 0x3EF5C28F;
    p7[1] = 0x3EB851EC;
    p7[2] = 0x3EF0A3D7;
    p7[3] = 0x3F800000;

    *reinterpret_cast<u32*>(0x00433BBC) = 0x3F800000;
    u32* p8 = reinterpret_cast<u32*>(0x00433BB0);
    p8[0] = 0x3EB851EC;
    p8[1] = 0x3E8F5C29;
    p8[2] = 0x3E851EB8;

    u32* p9 = reinterpret_cast<u32*>(0x00433BE0);
    p9[0] = 0x3F1EB852;
    p9[1] = 0x3F23D70A;
    p9[2] = 0x3F0A3D71;
    p9[3] = 0x3F800000;

    u32* p10 = reinterpret_cast<u32*>(0x00433C18);
    p10[0] = 0x3E99999A;
    p10[1] = 0x3F800000;

    u32* p11 = reinterpret_cast<u32*>(0x00433C10);
    p11[0] = 0x3F0A3D71;
    p11[1] = 0x3ECCCCCD;

    u32* p12 = reinterpret_cast<u32*>(0x00433C40);
    p12[0] = 0x3F19999A;
    p12[1] = 0x3EE66666;
    p12[2] = 0x3E99999A;
    p12[3] = 0x3F800000;

    u32* p13 = reinterpret_cast<u32*>(0x00433C70);
    p13[0] = 0x3F000000;
    p13[1] = 0x3F23D70A;
    p13[2] = 0x3F000000;
    p13[3] = 0x3F800000;

    *reinterpret_cast<u32*>(0x00433CAC) = 0x3F800000;
    u32* p14 = reinterpret_cast<u32*>(0x00433CA0);
    p14[0] = 0x3ECCCCCD;
    p14[1] = 0x3F0CCCCD;
    p14[2] = 0x3EE66666;

    u32* p15 = reinterpret_cast<u32*>(0x00433CD0);
    p15[0] = 0x3E800000;
    p15[1] = 0x3F19999A;
    p15[2] = 0x3F000000;
    p15[3] = 0x3F800000;

    u32* p16 = reinterpret_cast<u32*>(0x00433D00);
    p16[0] = 0x3F19999A;
    p16[1] = 0x3E99999A;
    p16[2] = 0x3F000000;
    p16[3] = 0x3F800000;
}


// DECOMP_FUNC(0x003ecf80, 44)
void func_003ecf80() {
    u32* p1 = reinterpret_cast<u32*>(0x00433D38);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ecfac, 44)
void func_003ecfac() {
    u32* p1 = reinterpret_cast<u32*>(0x0044E1A8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ecfd8, 44)
void func_003ecfd8() {
    u32* p1 = reinterpret_cast<u32*>(0x0043E298);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed004, 44)
void func_003ed004() {
    u32* p1 = reinterpret_cast<u32*>(0x0043E2C8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed030, 44)
void func_003ed030() {
    u32* p1 = reinterpret_cast<u32*>(0x00446D40);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed05c, 44)
void func_003ed05c() {
    u32* p1 = reinterpret_cast<u32*>(0x0043E118);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed088, 44)
void func_003ed088() {
    u32* p1 = reinterpret_cast<u32*>(0x004463B0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed0b4, 44)
void func_003ed0b4() {
    u32* p1 = reinterpret_cast<u32*>(0x00446400);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed0e0, 44)
void func_003ed0e0() {
    u32* p1 = reinterpret_cast<u32*>(0x0043E148);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed10c, 44)
void func_003ed10c() {
    u32* p1 = reinterpret_cast<u32*>(0x0043DD28);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed138, 44)
void func_003ed138() {
    u32* p1 = reinterpret_cast<u32*>(0x00433028);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed164, 44)
void func_003ed164() {
    u32* p1 = reinterpret_cast<u32*>(0x00434398);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed190, 44)
void func_003ed190() {
    u32* p1 = reinterpret_cast<u32*>(0x00435D50);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed1bc, 44)
void func_003ed1bc() {
    u32* p1 = reinterpret_cast<u32*>(0x00435E90);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed1e8, 44)
void func_003ed1e8() {
    u32* p1 = reinterpret_cast<u32*>(0x004398D8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed214, 80)
void func_003ed214() {
    u32* p1 = reinterpret_cast<u32*>(0x00439AD8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;

    u32* p2 = reinterpret_cast<u32*>(0x00493560);
    p2[0] = 0xBFD9999A;
    p2[1] = 0x40000000;
    p2[2] = 0;
}


// DECOMP_FUNC(0x003ed264, 44)
void func_003ed264() {
    u32* p1 = reinterpret_cast<u32*>(0x00464100);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed290, 44)
void func_003ed290() {
    u32* p1 = reinterpret_cast<u32*>(0x0043E0A8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed2bc, 20)
void func_003ed2bc() {
    *reinterpret_cast<u32*>(0x00476620) = 0;
}


// DECOMP_FUNC(0x003ed2d0, 624)
void func_003ed2d0() {
    u32* p1 = reinterpret_cast<u32*>(0x00447068);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;

    u32* p2 = reinterpret_cast<u32*>(0x0049EBAC);
    p2[0] = 0xC40A8000;
    p2[1] = 0x3C23D70A;
    p2[2] = 0xC5956000;
    p2[3] = 0xC40A8000;
    p2[4] = 0x3C23D70A;
    p2[5] = 0xC5956000;
    p2[6] = 0;
    p2[7] = 0xC3C80000;
    p2[8] = 0x42C80000;
    p2[9] = 0xC40A8000;
    p2[10] = 0x3C23D70A;
    p2[11] = 0xC5956000;

    u32* p3 = reinterpret_cast<u32*>(0x00447358);
    p3[0] = 0x44D0C000;
    p3[1] = 0;
    p3[2] = 0xC5B18000;

    u32* p4 = reinterpret_cast<u32*>(0x00447370);
    p4[0] = 0xC6179000;
    p4[1] = 0x42DC0000;
    p4[2] = 0xC5B86000;

    u32* p5 = reinterpret_cast<u32*>(0x00447388);
    p5[0] = 0xC6872800;
    p5[1] = 0x42B40000;
    p5[2] = 0xC6241000;

    u32* p6 = reinterpret_cast<u32*>(0x004473A0);
    p6[0] = 0xC6309000;
    p6[1] = 0x42480000;
    p6[2] = 0xC6147000;

    u32* p7 = reinterpret_cast<u32*>(0x004473B8);
    p7[0] = 0xC6A98800;
    p7[1] = 0x42E20000;
    p7[2] = 0x45960000;

    u32* p8 = reinterpret_cast<u32*>(0x004473D0);
    p8[0] = 0xC687F000;
    p8[1] = 0x42B40000;
    p8[2] = 0x46354000;

    u32* p9 = reinterpret_cast<u32*>(0x004473E8);
    p9[0] = 0xC60DE000;
    p9[1] = 0x42700000;
    p9[2] = 0x45674000;

    u32* p10 = reinterpret_cast<u32*>(0x00447400);
    p10[0] = 0xC63D1000;
    p10[1] = 0x42B40000;
    p10[2] = 0x466D8000;

    u32* p11 = reinterpret_cast<u32*>(0x00447418);
    p11[0] = 0x43E10000;
    p11[1] = 0;
    p11[2] = 0x45020000;

    u32* p12 = reinterpret_cast<u32*>(0x00447430);
    p12[0] = 0xC5898000;
    p12[1] = 0x41200000;
    p12[2] = 0xC3BE0000;

    u32* p13 = reinterpret_cast<u32*>(0x00447448);
    p13[0] = 0x44C80000;
    p13[1] = 0;
    p13[2] = 0xC4938000;

    u32* p14 = reinterpret_cast<u32*>(0x00447460);
    p14[0] = 0xC581B000;
    p14[1] = 0x41200000;
    p14[2] = 0xC63DD800;

    u32* p15 = reinterpret_cast<u32*>(0x00447478);
    p15[0] = 0xC5084000;
    p15[1] = 0x41200000;
    p15[2] = 0xC633B000;

    u32* p16 = reinterpret_cast<u32*>(0x00447490);
    p16[0] = 0xC604D000;
    p16[1] = 0x42B40000;
    p16[2] = 0xC6066000;

    u32* p17 = reinterpret_cast<u32*>(0x004474A8);
    p17[0] = 0xC5E74000;
    p17[1] = 0;
    p17[2] = 0x46548000;

    u32* p18 = reinterpret_cast<u32*>(0x004474C0);
    p18[0] = 0xC48D4000;
    p18[1] = 0;
    p18[2] = 0x464FD000;
}


// DECOMP_FUNC(0x003ed540, 44)
void func_003ed540() {
    u32* p1 = reinterpret_cast<u32*>(0x00447610);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed56c, 68)
__attribute__((naked, used)) void func_003ed56c() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2ed56c, 68\n");
}

// DECOMP_FUNC(0x003ed5b0, 68)
__attribute__((naked, used)) void func_003ed5b0() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2ed5b0, 68\n");
}

// DECOMP_FUNC(0x003ed5f4, 44)
void func_003ed5f4() {
    u32* p1 = reinterpret_cast<u32*>(0x00447EA0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed620, 68)
__attribute__((naked, used)) void func_003ed620() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2ed620, 68\n");
}

// DECOMP_FUNC(0x003ed664, 44)
void func_003ed664() {
    u32* p1 = reinterpret_cast<u32*>(0x00448E08);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed690, 44)
void func_003ed690() {
    u32* p1 = reinterpret_cast<u32*>(0x004719D8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed6bc, 44)
void func_003ed6bc() {
    u32* p1 = reinterpret_cast<u32*>(0x0044D188);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed6e8, 44)
void func_003ed6e8() {
    u32* p1 = reinterpret_cast<u32*>(0x0044CDF8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed714, 44)
void func_003ed714() {
    u32* p1 = reinterpret_cast<u32*>(0x0044CEE8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed740, 44)
void func_003ed740() {
    u32* p1 = reinterpret_cast<u32*>(0x0044D1D0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed76c, 44)
void func_003ed76c() {
    u32* p1 = reinterpret_cast<u32*>(0x0044E298);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed798, 44)
void func_003ed798() {
    u32* p1 = reinterpret_cast<u32*>(0x0044DF88);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed7c4, 44)
void func_003ed7c4() {
    u32* p1 = reinterpret_cast<u32*>(0x0044E058);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed7f0, 56)
__attribute__((naked, used)) void func_003ed7f0() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2ed7f0, 56\n");
}

// DECOMP_FUNC(0x003ed828, 44)
void func_003ed828() {
    u32* p1 = reinterpret_cast<u32*>(0x00432CE8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed854, 152)
void func_003ed854() {
    u32* p1 = reinterpret_cast<u32*>(0x1000EEF8);
    p1[0] = 0;
    p1[1] = 0;

    u32* p2 = reinterpret_cast<u32*>(0x004651B0);
    p2[0] = 0xFFFFFFFF;
    p2[1] = 0xFFFFFFFF;
    p2[2] = 0;
    p2[3] = 0;

    u32* p3 = reinterpret_cast<u32*>(0x0046519C);
    p3[0] = 0;
    p3[1] = 0;
    p3[2] = 0;
    p3[3] = 0;

    *reinterpret_cast<u32*>(0x004E4138) = 0;
    *reinterpret_cast<u32*>(0x004E4140) = 0xFFFFFFFF;
    *reinterpret_cast<u32*>(0x004E413C) = 0;
    engine_func_00225e4c(reinterpret_cast<void*>(0x004E4138), 0x003576B8, 0x00100000);
}


// DECOMP_FUNC(0x003ed8ec, 172)
__attribute__((naked, used)) void func_003ed8ec() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2ed8ec, 172\n");
}

// DECOMP_FUNC(0x003ed998, 44)
void func_003ed998() {
    u32* p1 = reinterpret_cast<u32*>(0x00465160);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed9c4, 44)
void func_003ed9c4() {
    u32* p1 = reinterpret_cast<u32*>(0x00464AC8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ed9f0, 44)
void func_003ed9f0() {
    u32* p1 = reinterpret_cast<u32*>(0x00465188);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003eda1c, 44)
void func_003eda1c() {
    u32* p1 = reinterpret_cast<u32*>(0x00464D00);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003eda48, 44)
void func_003eda48() {
    u32* p1 = reinterpret_cast<u32*>(0x00464D10);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003eda74, 44)
void func_003eda74() {
    u32* p1 = reinterpret_cast<u32*>(0x00464D20);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edaa0, 44)
void func_003edaa0() {
    u32* p1 = reinterpret_cast<u32*>(0x0043E078);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edacc, 44)
void func_003edacc() {
    u32* p1 = reinterpret_cast<u32*>(0x0043DB38);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edaf8, 44)
void func_003edaf8() {
    u32* p1 = reinterpret_cast<u32*>(0x00433228);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edb24, 44)
void func_003edb24() {
    u32* p1 = reinterpret_cast<u32*>(0x00433D28);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edb50, 44)
void func_003edb50() {
    u32* p1 = reinterpret_cast<u32*>(0x0043E350);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edb7c, 136)
void func_003edb7c() {
    u32* p1 = reinterpret_cast<u32*>(0x1000EEF8);
    p1[0] = 0;
    p1[1] = 0;

    u32* p2 = reinterpret_cast<u32*>(0x00433DB0);
    p2[0] = 0xFFFFFFFF;
    p2[1] = 0xFFFFFFFF;
    p2[2] = 0;
    p2[3] = 0;

    u32* p3 = reinterpret_cast<u32*>(0x0047E508);
    p3[0] = 0x00420410;
    p3[1] = 0;
    p3[2] = 0;
    p3[3] = 0;
    p3[4] = 0;
    p3[5] = 0;
    p3[6] = 0;
    p3[7] = 0;
    p3[8] = 0;
    p3[9] = 0;
    p3[10] = 0;
    p3[11] = 0;
    p3[12] = 0;
    p3[13] = 0;
    p3[14] = 0;
    p3[15] = 0;
    p3[16] = 0;

    engine_func_00225e4c(reinterpret_cast<void*>(0x0047E508), 0x00343B84, 0x00100000);
}


// DECOMP_FUNC(0x003edc04, 44)
void func_003edc04() {
    u32* p1 = reinterpret_cast<u32*>(0x0043DCD0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edc30, 44)
void func_003edc30() {
    u32* p1 = reinterpret_cast<u32*>(0x00446450);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edc5c, 44)
void func_003edc5c() {
    u32* p1 = reinterpret_cast<u32*>(0x0043E178);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edc88, 44)
void func_003edc88() {
    u32* p1 = reinterpret_cast<u32*>(0x0043DF30);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edcb4, 44)
void func_003edcb4() {
    u32* p1 = reinterpret_cast<u32*>(0x00446528);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edce0, 44)
void func_003edce0() {
    u32* p1 = reinterpret_cast<u32*>(0x00446D50);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edd0c, 44)
void func_003edd0c() {
    u32* p1 = reinterpret_cast<u32*>(0x0043DD80);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edd38, 44)
void func_003edd38() {
    u32* p1 = reinterpret_cast<u32*>(0x00433198);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edd64, 44)
void func_003edd64() {
    u32* p1 = reinterpret_cast<u32*>(0x004331A8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edd90, 44)
void func_003edd90() {
    u32* p1 = reinterpret_cast<u32*>(0x004331C8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003eddbc, 44)
void func_003eddbc() {
    u32* p1 = reinterpret_cast<u32*>(0x0043D9B8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edde8, 44)
void func_003edde8() {
    u32* p1 = reinterpret_cast<u32*>(0x0043DA18);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ede14, 44)
void func_003ede14() {
    u32* p1 = reinterpret_cast<u32*>(0x00434280);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ede40, 76)
void func_003ede40() {
    u32* p1 = reinterpret_cast<u32*>(0x00434300);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;

    u32* p2 = reinterpret_cast<u32*>(0x00493554);
    p2[0] = 0;
    p2[1] = 0;
    p2[2] = 0xC0A00000;
}


// DECOMP_FUNC(0x003ede8c, 44)
void func_003ede8c() {
    u32* p1 = reinterpret_cast<u32*>(0x00435CF0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edeb8, 44)
void func_003edeb8() {
    u32* p1 = reinterpret_cast<u32*>(0x00435D20);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edee4, 44)
void func_003edee4() {
    u32* p1 = reinterpret_cast<u32*>(0x00435E28);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edf10, 44)
void func_003edf10() {
    u32* p1 = reinterpret_cast<u32*>(0x00435E70);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edf3c, 44)
void func_003edf3c() {
    u32* p1 = reinterpret_cast<u32*>(0x0043DE88);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edf68, 68)
__attribute__((naked, used)) void func_003edf68() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2edf68, 68\n");
}

// DECOMP_FUNC(0x003edfac, 44)
void func_003edfac() {
    u32* p1 = reinterpret_cast<u32*>(0x0044E5D0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003edfd8, 44)
void func_003edfd8() {
    u32* p1 = reinterpret_cast<u32*>(0x0044E228);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ee004, 44)
void func_003ee004() {
    u32* p1 = reinterpret_cast<u32*>(0x0043E0C0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ee030, 44)
void func_003ee030() {
    u32* p1 = reinterpret_cast<u32*>(0x0043E0D8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ee05c, 60)
void func_003ee05c() {
    u32* p1 = reinterpret_cast<u32*>(0x004732E0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;

    *reinterpret_cast<u32*>(0x004732D8) = 0x004722B8;
}


// DECOMP_FUNC(0x003ee098, 60)
void func_003ee098() {
    u32* p1 = reinterpret_cast<u32*>(0x00472188);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;

    *reinterpret_cast<u32*>(0x00472180) = 0x004722B8;
}


// DECOMP_FUNC(0x003ee0d4, 36)
__attribute__((naked, used)) void func_003ee0d4() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2ee0d4, 36\n");
}

// DECOMP_FUNC(0x003ee0f8, 44)
void func_003ee0f8() {
    u32* p1 = reinterpret_cast<u32*>(0x0044E240);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ee124, 44)
void func_003ee124() {
    u32* p1 = reinterpret_cast<u32*>(0x00447030);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ee150, 120)
__attribute__((naked, used)) void func_003ee150() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2ee150, 120\n");
}

// DECOMP_FUNC(0x003ee1c8, 44)
void func_003ee1c8() {
    u32* p1 = reinterpret_cast<u32*>(0x00447540);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ee1f4, 44)
void func_003ee1f4() {
    u32* p1 = reinterpret_cast<u32*>(0x004475C0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ee220, 104)
__attribute__((naked, used)) void func_003ee220() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2ee220, 104\n");
}

// DECOMP_FUNC(0x003ee288, 44)
void func_003ee288() {
    u32* p1 = reinterpret_cast<u32*>(0x00447E90);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003ee2b4, 96)
__attribute__((naked, used)) void func_003ee2b4() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2ee2b4, 96\n");
}

// DECOMP_FUNC(0x003f36b0, 60)
void func_003f36b0() {
    u32* p1 = reinterpret_cast<u32*>(0x0044E7F8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;

    *reinterpret_cast<u32*>(0x0044E7F0) = 0x0044E808;
}


// DECOMP_FUNC(0x003f36ec, 60)
void func_003f36ec() {
    u32* p1 = reinterpret_cast<u32*>(0x00472050);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;

    *reinterpret_cast<u32*>(0x00472048) = 0x004732D8;
}


// DECOMP_FUNC(0x003f3728, 52)
void func_003f3728() {
    u32* p1 = reinterpret_cast<u32*>(0x00472130);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;

    *reinterpret_cast<u32*>(0x00472128) = 0;
}


// DECOMP_FUNC(0x003f375c, 52)
void func_003f375c() {
    u32* p1 = reinterpret_cast<u32*>(0x00476550);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;

    *reinterpret_cast<u32*>(0x00476548) = 0;
}


// DECOMP_FUNC(0x003f3790, 52)
void func_003f3790() {
    u32* p1 = reinterpret_cast<u32*>(0x00476568);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;

    *reinterpret_cast<u32*>(0x00476560) = 0;
}


// DECOMP_FUNC(0x003f37c4, 44)
void func_003f37c4() {
    u32* p1 = reinterpret_cast<u32*>(0x00473320);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003f37f0, 60)
void func_003f37f0() {
    u32* p1 = reinterpret_cast<u32*>(0x004721E8);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;

    *reinterpret_cast<u32*>(0x004721E0) = 0x00472180;
}


// DECOMP_FUNC(0x003f382c, 60)
void func_003f382c() {
    u32* p1 = reinterpret_cast<u32*>(0x004733A0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;

    *reinterpret_cast<u32*>(0x00473398) = 0x00472260;
}


// DECOMP_FUNC(0x003f3868, 84)
void func_003f3868() {
    u32* p1 = reinterpret_cast<u32*>(0x0044E838);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;

    u32* p2 = reinterpret_cast<u32*>(0x004D4658);
    p2[0] = 0;
    p2[1] = 0;
    p2[2] = 0;
    p2[3] = 0x3F800000;
}


// DECOMP_FUNC(0x003f38bc, 44)
void func_003f38bc() {
    u32* p1 = reinterpret_cast<u32*>(0x00472278);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;
}


// DECOMP_FUNC(0x003f38e8, 60)
void func_003f38e8() {
    u32* p1 = reinterpret_cast<u32*>(0x00472290);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;

    *reinterpret_cast<u32*>(0x00472288) = 0x00472180;
}


// DECOMP_FUNC(0x003f3924, 60)
void func_003f3924() {
    u32* p1 = reinterpret_cast<u32*>(0x004722C0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;
    p1[2] = 0;
    p1[3] = 0;

    *reinterpret_cast<u32*>(0x004722B8) = 0x0044E858;
}

