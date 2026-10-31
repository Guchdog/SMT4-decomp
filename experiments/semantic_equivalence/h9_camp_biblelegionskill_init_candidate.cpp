#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void  unite_func_00232800(void* ptr, u32 a, u32 b, u32 c);
    void  unite_func_00233600(void* ptr);
    void  shop_func_002333d4(void* ptr, u32 flag);
    void* engine_func_002c23f8(u32 size);
    void  unite_func_002333bc(void* ptr);
    void  unite_func_003ab0d0(void* ptr);
    void  unite_func_00233804(void* ptr, u32 a, u32 b, u32 c);
    void  camp_func_0029f10c(u32 a, u32 color);
    void  bibleLegionDraw_func_003ad300();

    extern void* g_BibleLegionSkillHandle_0043d9f8;
}

extern "C" void h9_camp_biblelegionskill_init_candidate(u8* work) {
    *reinterpret_cast<u32*>(work + 0x14) = 0;
    *reinterpret_cast<u32*>(work + 0x18) = 0;
    work[0x94] = 0;
    *reinterpret_cast<u16*>(work + 0xA5B0) = 0;

    void** vtbl = *reinterpret_cast<void***>(work);
    reinterpret_cast<void(*)(void*)>(vtbl[8])(work);

    void** handle = static_cast<void**>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 4, 1));
    g_BibleLegionSkillHandle_0043d9f8 = handle;
    handle[0] = work;

    void* calc = AsdTask_Create_002c5978("BIBLE LEGIONSKILL CALC", 2, 0, 0, reinterpret_cast<void*>(0x003AD034), handle, 0);
    *reinterpret_cast<void**>(work + 4) = calc;

    AsdTask_CreateDraw_002c4c00("BIBLE LEGIONSKILL UP", 0x6F, 1, 0, reinterpret_cast<void*>(0x003AD288), handle, reinterpret_cast<u32>(calc));
    AsdTask_CreateDraw_002c4c00("BIBLE LEGIONSKILL DOWN", 0xE6, 1, 0, reinterpret_cast<void*>(0x003AD588), handle, reinterpret_cast<u32>(calc));

    unite_func_00232800(work + 0xC8, 0x140, 0, 0x1D);
    unite_func_00233600(work + 0xDC);
    shop_func_002333d4(work + 0xDC, 0);
    shop_func_002333d4(work + 0xDC, 1);

    void* ui = engine_func_002c23f8(0x68);
    if (ui) {
        unite_func_002333bc(ui);
        *static_cast<void**>(ui) = reinterpret_cast<void*>(0x0042207C);
    }
    *reinterpret_cast<void**>(work + 0x590) = ui;
    *reinterpret_cast<void**>(static_cast<u8*>(ui) + 0x64) = work + 0xC8;

    unite_func_003ab0d0(work);
    unite_func_00233804(work + 0x56C, 0x1D, 0x40E, 0xA);
    work[0x56C] = 1;
    camp_func_0029f10c(0, 0x323232FF);
    bibleLegionDraw_func_003ad300();
    *reinterpret_cast<u32*>(work + 0x14) = 1;
    *reinterpret_cast<u32*>(work + 0x18) = 0;
}

extern "C" void h9_camp_biblelegionskill_init_mutation() {
    g_BibleLegionSkillHandle_0043d9f8 = reinterpret_cast<void*>(0xDEADBEEF);
}
