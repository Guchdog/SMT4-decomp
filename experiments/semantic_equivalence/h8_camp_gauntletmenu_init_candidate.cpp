#include <cstdint>

typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void  engine_func_002c0ba8(void* ptr, u32 id);
    void  engine_func_002488a8(void* ptr);
    void  engine_func_002976ac(void* ptr, const char* mbm, const char* bf);

    extern void* g_GauntletAppWork_0044e1a0;
}

extern "C" void h8_camp_gauntletmenu_init_candidate() {
    u8* work = static_cast<u8*>(g_GauntletAppWork_0044e1a0);
    if (!work) {
        work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0x122, 0, 0x1B8, 1));
        g_GauntletAppWork_0044e1a0 = work;
    }
    AsdMem_Zero_002c4b30(work, 0x1B8);

    void* calc_task = AsdTask_Create_002c5978("Gauntlet App CALC", 2, 0, 0, reinterpret_cast<void*>(0x00329410), work, 0);
    *reinterpret_cast<void**>(work) = calc_task;

    AsdTask_CreateDraw_002c4c00("Gauntlet App DDRAW", 0x57, 0, 0, reinterpret_cast<void*>(0x0032B070), work, reinterpret_cast<u32>(calc_task));

    engine_func_002c0ba8(work + 0x18, 0x521);
    engine_func_002c0ba8(work + 0x48, 0x526);
    engine_func_002c0ba8(work + 0x78, 0x527);
    engine_func_002c0ba8(work + 0xA8, 0x59F);

    engine_func_002488a8(work + 0xD8);
    engine_func_002976ac(work, "camp/gauntletApp.mbm", "camp/gauntletApp.bf");
}

extern "C" void h8_camp_gauntletmenu_init_mutation() {
    g_GauntletAppWork_0044e1a0 = reinterpret_cast<void*>(0xDEADBEEF);
}
