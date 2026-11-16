# func_003ecdac (0x003ecdac)

## Summary
- **Address:** 0x003ecdac
- **Size:** 468 bytes
- **Domain:** UI / Battle HUD Channel & State Reset
- **Status:** Semantically verified (non_matching in ledger)
- **Source File:** src/ui/battle_hud_exact_batch.cpp
- **Differential Suite:** tools/battle_hud_exact_experiment.py

## Role and Behavior
- **Role:** Battle HUD channel state reset and resource layout descriptor initializer routine.
- **Details:**
  - Implements state clear and layout descriptor setup operations:
`cpp
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

`
- **Differential Coverage:** Verified in Unicorn emulator against original ARM binary with exact post-execution memory image and call trace comparison.
