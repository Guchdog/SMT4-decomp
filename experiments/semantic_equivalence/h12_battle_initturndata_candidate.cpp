#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    extern void* g_BattleStateWork_004655c0;
    void sub_1422F8();
}

extern "C" void h12_battle_initturndata_candidate(u32* p) {
    *p = 0x1C00;
    u8* st = static_cast<u8*>(g_BattleStateWork_004655c0);
    u32* flags = reinterpret_cast<u32*>(st + 0x770);
    *flags = (*flags & ~0x2000u) | 0x11000u;
    sub_1422F8();
}

extern "C" void h12_battle_initturndata_mutation(u32* p) {
    *p = 0;
    sub_1422F8();
}
