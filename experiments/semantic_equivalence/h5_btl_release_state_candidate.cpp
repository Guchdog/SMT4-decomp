#include <cstdint>

typedef uint8_t u8;
typedef int32_t s32;

extern "C" {
    s32 SubObject_CheckState_002b2530(void* sub_obj);
    void Free_002c4360(void* ptr);
    extern void* g_CombatSubWork_00447e28;
}

extern "C" s32 h5_btl_release_state_candidate(void) {
    void* work = g_CombatSubWork_00447e28;
    if (!work) return 0;

    if (SubObject_CheckState_002b2530(*(void**)work) != 0) {
        return 1;
    }

    if (*(u8*)((char*)work + 0x0C) == 0) {
        return 1;
    }

    Free_002c4360(work);
    g_CombatSubWork_00447e28 = nullptr;
    return 0;
}

extern "C" s32 h5_btl_release_state_mutation(void) {
    return 1;
}
