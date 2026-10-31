#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;
typedef int32_t s32;
typedef int16_t s16;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void  unite_func_00232800(void* ptr, u32 a, u32 b, u32 c);
    void* engine_func_002c23f8(u32 size);
    void  unite_func_002333bc(void* ptr);
    void  unite_func_0022d5c8(void* ptr);
    void  unite_func_003aad60(void* ptr);
    void  unite_func_0022df7c(void* ptr, u32 val);
    s32   unite_func_002338ac(void* ptr);
    void  unite_func_00233600(void* ptr);
    void  unite_func_00233804(void* ptr, u32 a, u32 b, u32 c);
    void  camp_func_0029f10c(u32 a, u32 color);
    void  unite_func_002e32c8();
    void  camp_func_0022d33c(void* ptr);

    extern void* g_BibleDevilHandle_0043d9c8;
}

extern "C" void h9_camp_bibledevil_init_candidate(u8* work) {
    work[0x5A5] = 1;
    work[0x94] = 0;
    *reinterpret_cast<u16*>(work + 0xA5B0) = 0;
    *reinterpret_cast<s16*>(work + 0xA5B2) = -1;

    void** vtbl = *reinterpret_cast<void***>(work);
    reinterpret_cast<void(*)(void*)>(vtbl[8])(work);

    void** handle = static_cast<void**>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 4, 1));
    g_BibleDevilHandle_0043d9c8 = handle;
    handle[0] = work;

    void* calc = AsdTask_Create_002c5978("BIBLE DEVIL CALC", 2, 0, 0, reinterpret_cast<void*>(0x003AAF08), handle, 0);
    *reinterpret_cast<void**>(work + 4) = calc;

    AsdTask_CreateDraw_002c4c00("BIBLE DEVIL UP", 0x6F, 1, 0, reinterpret_cast<void*>(0x003AC958), handle, reinterpret_cast<u32>(calc));
    AsdTask_CreateDraw_002c4c00("BIBLE DEVIL DOWN", 0xE6, 1, 0, reinterpret_cast<void*>(0x003ACC74), handle, reinterpret_cast<u32>(calc));

    unite_func_00232800(work + 0xC8, 0x140, 0, 0x1D);

    void* ui = engine_func_002c23f8(0x68);
    if (ui) {
        unite_func_002333bc(ui);
        *static_cast<void**>(ui) = reinterpret_cast<void*>(0x0042207C);
    }
    *reinterpret_cast<void**>(work + 0x590) = ui;
    *reinterpret_cast<void**>(static_cast<u8*>(ui) + 0x64) = work + 0xC8;

    unite_func_0022d5c8(work);
    unite_func_003aad60(work + 0x5A8);
    unite_func_0022df7c(work + 0x5A8, 0);

    s32 vis = unite_func_002338ac(work + 0x20);
    for (s32 i = 0; i < vis; ++i) {
        s16 did = *reinterpret_cast<s16*>(work + 0x5A8 + 4 + i * 0x20);
        if (did != 0) {
            unite_func_0022df7c(work + 0x5A8, static_cast<u16>(did));
        }
    }

    unite_func_00233600(work + 0xDC);

    s32 rows = *reinterpret_cast<s32*>(work + 0x568);
    if (rows > 10) rows = 10;
    unite_func_00233804(work + 0x56C, 0x1D, 0x40E, rows);
    work[0x56C] = 1;
    camp_func_0029f10c(0, 0x323232FF);
    *reinterpret_cast<u32*>(work + 0x14) = 0;
    *reinterpret_cast<u32*>(work + 0x18) = 0;
    unite_func_002e32c8();
    camp_func_0022d33c(work);
}

extern "C" void h9_camp_bibledevil_init_mutation() {
    g_BibleDevilHandle_0043d9c8 = reinterpret_cast<void*>(0xDEADBEEF);
}
