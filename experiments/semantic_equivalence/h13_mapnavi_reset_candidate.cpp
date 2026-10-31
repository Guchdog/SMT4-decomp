#include <cstdint>
typedef uint32_t u32;

extern "C" {
    extern void** g_MapRuntimeWork_00447060;
    void sub_2C45B8(void* work, u32 flag);
}

extern "C" void h13_mapnavi_reset_candidate() {
    void* w = *g_MapRuntimeWork_00447060;
    sub_2C45B8(w, 0);
}

extern "C" void h13_mapnavi_reset_mutation() {
    void* w = *g_MapRuntimeWork_00447060;
    sub_2C45B8(w, 1);
}
