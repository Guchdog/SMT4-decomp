#include <cstdint>

typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void  UiSpriteGroup_Init_002c3344(void* group);
    void  UiSpriteGroup_BindTable_002c32f8(void* group, u32 a, u32 b, void* c, u32 d, void* e, u32 f, u32 g, void* h, u32 i);
    void  UiAnimSprite_SetupEx_002bdb2c(void* sprite, u32 id, u32 param, u32 unused, void* group, u32 flag, float scale);
    void  UiAnimSprite_SetMode_002bdac0(void* sprite, u32 mode, u32 flags);

    extern void* g_InfoWinWork_0043e128;
    extern u8    g_InfoWinSpriteTable_00403aa8[];
}

extern "C" void h7_ui_infowin_init_candidate() {
    u8* work = static_cast<u8*>(g_InfoWinWork_0043e128);
    if (!work) {
        work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0xFF, 0, 0x1BC, 1));
        g_InfoWinWork_0043e128 = work;
    }
    AsdMem_Zero_002c4b30(work, 0x1BC);

    void* calc_task = AsdTask_Create_002c5978("InfoWin Calc", 1, 0, 0, reinterpret_cast<void*>(0x0011B1BC), work, 0);
    *reinterpret_cast<void**>(work) = calc_task;

    AsdTask_CreateDraw_002c4c00("InfoWin DrawUpLeft", 0x81, 0, 0, reinterpret_cast<void*>(0x0011AE10), work, reinterpret_cast<u32>(calc_task));
    AsdTask_CreateDraw_002c4c00("InfoWin DrawUpRight", 0xDF, 0, 0, reinterpret_cast<void*>(0x0011AE10), work, reinterpret_cast<u32>(calc_task));

    u8* group = work + 0x24;
    UiSpriteGroup_Init_002c3344(group);

    u8* table = g_InfoWinSpriteTable_00403aa8;
    UiSpriteGroup_BindTable_002c32f8(group, 0, 0x24, table, 0, 0, 0, 0, 0, 0);

    UiAnimSprite_SetupEx_002bdb2c(work + 0x44, 0x0E, 0x87, 0, group, 1, 1.0f);
    UiAnimSprite_SetMode_002bdac0(work + 0x44, 0, 0);

    UiAnimSprite_SetupEx_002bdb2c(work + 0xD0, 0x0E, 0x87, 0, group, 1, 1.0f);
    UiAnimSprite_SetMode_002bdac0(work + 0xD0, 0, 0);

    *reinterpret_cast<u32*>(work + 0x10) = 0x1E;
}

extern "C" void h7_ui_infowin_init_mutation() {
    g_InfoWinWork_0043e128 = reinterpret_cast<void*>(0xDEADBEEF);
}
