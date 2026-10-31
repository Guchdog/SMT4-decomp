#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    extern void* g_CampWork_0043dd68;
}

extern "C" u32 h10_camp_quest_isidle_candidate() {
    u8* work = static_cast<u8*>(g_CampWork_0043dd68);
    if (!work || work[0x430] == 0) return 1;
    return 0;
}

extern "C" void h10_camp_quest_isidle_mutation() {
    g_CampWork_0043dd68 = reinterpret_cast<void*>(0xDEADBEEF);
}
