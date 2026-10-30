#include <cstdint>

typedef uint32_t u32;
typedef uint8_t u8;

struct SaveLoadUIManager {
    u32 flags;
    void* work; // +0x04
};

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void* AsdTask_Create(const char* name, u32 priority, u32 arg2, u32 arg3, void* fn, void* arg, void* work, u32 unused);
    void  BootCalc_001c8d28(void*);
    extern SaveLoadUIManager g_SaveLoadUIManager_0044de28;
    extern const char g_szBootC_00191f74[];
}

extern "C" void h6_saveload_ui_init_candidate() {
    u8* work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x10000, 0x100, 0, 0x388, 1));
    if (!work) return;

    g_SaveLoadUIManager_0044de28.work = work;
    work[4] = 0;

    void* task = AsdTask_Create(g_szBootC_00191f74, 2, 0, 0, reinterpret_cast<void*>(BootCalc_001c8d28), reinterpret_cast<void*>(0x00214960), nullptr, 0);
    *reinterpret_cast<void**>(&work[0]) = task;
    *reinterpret_cast<u32*>(&work[8]) = 0x11;
    *reinterpret_cast<u32*>(&work[0xC]) = 0;
}

extern "C" void h6_saveload_ui_init_mutation() {
    // Mutation: does not allocate or initialize
    return;
}
