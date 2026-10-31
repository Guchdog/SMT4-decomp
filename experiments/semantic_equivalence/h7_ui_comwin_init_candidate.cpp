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
    void  UiAnimSprite_Setup_002bf0a8(void* sprite, u32 id, int param, u32 index, void* group, u32 flag, float scale);
    void  UiAnimSprite_SetMode_002bf030(void* sprite, u32 mode);

    extern void* g_ComWinWork_0043e0f8;
    extern u8    g_ComWinSpriteTable_004038f0[];
}

extern "C" void h7_ui_comwin_init_candidate() {
    u8* work = static_cast<u8*>(g_ComWinWork_0043e0f8);
    if (!work) {
        work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0x122, 0, 0x188, 1));
        g_ComWinWork_0043e0f8 = work;
    }
    AsdMem_Zero_002c4b30(work, 0x188);

    void* calc_task = AsdTask_Create_002c5978("ComWin Calc", 1, 0, 0, reinterpret_cast<void*>(0x0011B094), work, 0);
    *reinterpret_cast<void**>(work) = calc_task;

    AsdTask_CreateDraw_002c4c00("ComWin DrawUpLeft", 0x81, 0, 0, reinterpret_cast<void*>(0x0011A354), work, reinterpret_cast<u32>(calc_task));
    AsdTask_CreateDraw_002c4c00("ComWin DrawUpRight", 0xDF, 0, 0, reinterpret_cast<void*>(0x0011A354), work, reinterpret_cast<u32>(calc_task));

    u8* group = work + 0x1C;
    UiSpriteGroup_Init_002c3344(group);

    u8* table = g_ComWinSpriteTable_004038f0;
    UiSpriteGroup_BindTable_002c32f8(group, 0, 0x30, table - 0x60, 0x30, table - 0x30, 0, 0, table, 0x118);

    UiAnimSprite_Setup_002bf0a8(work + 0x3C, 0x0E, -1, 2, group, 1, 1.0f);
    UiAnimSprite_SetMode_002bf030(work + 0x3C, 0);

    UiAnimSprite_Setup_002bf0a8(work + 0xC8, 0x0E, -1, 3, group, 1, 1.0f);
    UiAnimSprite_SetMode_002bf030(work + 0xC8, 2);
}

extern "C" void h7_ui_comwin_init_mutation() {
    g_ComWinWork_0043e0f8 = reinterpret_cast<void*>(0xDEADBEEF);
}
