#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    void app_func_00242a80(void* work, u32 flag);
    u8* app_func_00293c98();
    extern void* g_AppStoreWork_00439ca8;
}

extern "C" u32 h10_camp_appstore_setflag_candidate() {
    void* work = g_AppStoreWork_00439ca8;
    app_func_00242a80(work, 1);
    u8* base = app_func_00293c98();
    u32* flag_ptr = reinterpret_cast<u32*>(base + 0x44a0);
    *flag_ptr |= 0x20000000;
    return 1;
}

extern "C" void h10_camp_appstore_setflag_mutation() {
    g_AppStoreWork_00439ca8 = reinterpret_cast<void*>(0xDEADBEEF);
}
