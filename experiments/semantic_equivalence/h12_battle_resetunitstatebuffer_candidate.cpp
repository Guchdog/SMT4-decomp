#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    extern u8 g_BattleUnitTable_00478000[];
    void* sub_2BCF58(void* dest, const void* src, u32 n);
}

extern "C" void* h12_battle_resetunitstatebuffer_candidate(u32 idx, const void* src) {
    u8* unit = g_BattleUnitTable_00478000 + idx * 328;
    return sub_2BCF58(unit + 0x2C, src, 0x90);
}

extern "C" void* h12_battle_resetunitstatebuffer_mutation(u32 idx, const void* src) {
    u8* unit = g_BattleUnitTable_00478000 + idx * 328;
    return sub_2BCF58(unit + 0x2C, src, 0);
}
