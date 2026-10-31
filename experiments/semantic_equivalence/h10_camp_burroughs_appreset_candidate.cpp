#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;
typedef int32_t s32;

extern "C" {
    u32 camp_func_002a0f88();
    void camp_func_00297128();
    extern void* g_CampWork_0043dd68;
}

extern "C" void h10_camp_burroughs_appreset_candidate() {
    u8* work = static_cast<u8*>(g_CampWork_0043dd68);
    if (!work) return;

    if (work[0x430] != 0) {
        if (camp_func_002a0f88() == 0) {
            camp_func_00297128();
        }
    }

    u8* cur = static_cast<u8*>(g_CampWork_0043dd68);
    if (cur) {
        *reinterpret_cast<s32*>(cur + 0x478) = -1;
    }
}

extern "C" void h10_camp_burroughs_appreset_mutation() {
    g_CampWork_0043dd68 = reinterpret_cast<void*>(0xDEADBEEF);
}
