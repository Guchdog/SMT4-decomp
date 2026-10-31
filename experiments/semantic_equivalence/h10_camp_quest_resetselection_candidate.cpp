#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    extern void* g_CampWork_0043dd68;
}

extern "C" void h10_camp_quest_resetselection_candidate(u32 cat) {
    u8* work = static_cast<u8*>(g_CampWork_0043dd68);
    if (!work) return;
    work[0x420] = static_cast<u8>(cat);
    *reinterpret_cast<u32*>(work + 0x400) = 0;
    *reinterpret_cast<u32*>(work + 0x3fc) = 0;
}

extern "C" void h10_camp_quest_resetselection_mutation(u32 cat) {
    g_CampWork_0043dd68 = reinterpret_cast<void*>(0xDEADBEEF);
}
