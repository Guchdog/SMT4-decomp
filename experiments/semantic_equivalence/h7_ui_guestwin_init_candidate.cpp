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
    void  UiAnimSprite_SetAnim_002bf030(void* sprite, u32 anim, u32 flags);

    extern void* g_GuestWinWork_0043e110;
    extern u8    g_GuestWinSpriteTable_00403a38[];
}

extern "C" void h7_ui_guestwin_init_candidate() {
    u8* work = static_cast<u8*>(g_GuestWinWork_0043e110);
    if (!work) {
        work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0xF5, 0, 0xBC, 1));
        g_GuestWinWork_0043e110 = work;
    }
    AsdMem_Zero_002c4b30(work, 0xBC);

    void* calc_task = AsdTask_Create_002c5978("GuestWin Calc", 1, 0, 0, reinterpret_cast<void*>(0x0011B128), work, 0);
    *reinterpret_cast<void**>(work) = calc_task;

    AsdTask_CreateDraw_002c4c00("GuestWin DrawUpLeft", 0x81, 0, 0, reinterpret_cast<void*>(0x0011A9B4), work, reinterpret_cast<u32>(calc_task));
    AsdTask_CreateDraw_002c4c00("GuestWin DrawUpRight", 0xDF, 0, 0, reinterpret_cast<void*>(0x0011A9B4), work, reinterpret_cast<u32>(calc_task));

    u8* group = work + 0x10;
    UiSpriteGroup_Init_002c3344(group);

    u8* table = g_GuestWinSpriteTable_00403a38;
    UiSpriteGroup_BindTable_002c32f8(group, 0, 0x18, table - 0x30, 0x18, table - 0x18, 0, 0, table, 0x70);

    UiAnimSprite_SetupEx_002bdb2c(work + 0x30, 0x0E, 0x87, 0, group, 1, 1.0f);
    UiAnimSprite_SetAnim_002bf030(work + 0x30, 0, 0);
}

extern "C" void h7_ui_guestwin_init_mutation() {
    g_GuestWinWork_0043e110 = reinterpret_cast<void*>(0xDEADBEEF);
}
