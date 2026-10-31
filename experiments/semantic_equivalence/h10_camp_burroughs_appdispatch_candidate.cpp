#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;
typedef int32_t s32;

extern "C" {
    u32 camp_func_002971e4(u32 arg0, u32 app_id);
    void camp_func_002a0f68(u32 flag);
    void sound_func_002b8b78(u32 se_id);
    extern void* g_CampWork_0043dd68;
}

extern "C" u32 h10_camp_burroughs_appdispatch_candidate(u32 app_id) {
    u8* work = static_cast<u8*>(g_CampWork_0043dd68);
    if (!work) return 0;

    if (work[0x430] != 0) {
        *reinterpret_cast<u32*>(work + 0x478) = app_id;
        return 0;
    }

    u32 f42c = *reinterpret_cast<u32*>(work + 0x42c);
    if (camp_func_002971e4(f42c, app_id) == 0) {
        return 0;
    }

    if (app_id == 7 || app_id == 8 || app_id == 9 || app_id == 10 || app_id == 11 || app_id == 13) {
        camp_func_002a0f68(1);
        sound_func_002b8b78(0x9e);
    } else if (app_id == 12) {
        camp_func_002a0f68(1);
    }

    *reinterpret_cast<s32*>(work + 0x478) = -1;
    *reinterpret_cast<u32*>(work + 0x434) = app_id;
    work[0x430] = 1;
    return 1;
}

extern "C" void h10_camp_burroughs_appdispatch_mutation(u32 app_id) {
    g_CampWork_0043dd68 = reinterpret_cast<void*>(0xDEADBEEF);
}
