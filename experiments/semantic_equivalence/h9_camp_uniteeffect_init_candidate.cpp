#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, void* parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, u32 u1, void* work, void* parent);
    void  engine_func_002976ac(u32 id);

    extern void* g_UniteEffectWork_0043dd90;
}

extern "C" void h9_camp_uniteeffect_init_candidate() {
    u8* work = static_cast<u8*>(g_UniteEffectWork_0043dd90);
    if (!work) {
        work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x958, 1));
        g_UniteEffectWork_0043dd90 = work;
    }
    AsdMem_Zero_002c4b30(work, 0x958);

    void* calc = AsdTask_Create_002c5978("TMD CALC", 2, 0, 0, reinterpret_cast<void*>(0x002F6420), nullptr, nullptr);
    *reinterpret_cast<void**>(work) = calc;

    AsdTask_CreateDraw_002c4c00("TMD DDRAW", 0xE7, 0, 0, reinterpret_cast<void*>(0x002C9DA4), 0, nullptr, calc);
    AsdTask_CreateDraw_002c4c00("TMD DDRAW", 0x6F, 0, 0, reinterpret_cast<void*>(0x002C9DA4), 0, nullptr, calc);

    engine_func_002976ac(0x25);
}

extern "C" void h9_camp_uniteeffect_init_mutation() {
    g_UniteEffectWork_0043dd90 = reinterpret_cast<void*>(0xDEADBEEF);
}
