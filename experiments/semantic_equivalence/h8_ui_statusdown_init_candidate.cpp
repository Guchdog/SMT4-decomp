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
    void  UiAnimSprite_SetupEx_002bdb2c(void* sprite, u32 id, int param, u32 index, void* group, u32 flag, float scale);
    void  UiAnimSprite_SetMode_002bdac0(void* sprite, u32 mode);
    void  UiAnimSprite_SetMode_002bf030(void* sprite, u32 mode);
    void* engine_func_002bda1c(void* sprite);
    void  engine_func_002bda10(void* ptr, u32 alpha);
    void  engine_func_002bda00(void* ptr, u32 a, u32 b, float scale);
    void  engine_func_002c4450(void* ptr, u32 a, int b);

    extern void* g_StatusDownContext_0044e190;
    extern u8    g_StatusDownSpriteTable_00407d58[];
}

extern "C" void h8_ui_statusdown_init_candidate() {
    u8* work = static_cast<u8*>(g_StatusDownContext_0044e190);
    if (!work) {
        work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x2394, 1));
        g_StatusDownContext_0044e190 = work;
    }
    AsdMem_Zero_002c4b30(work, 0x2394);

    void* calc_task = AsdTask_Create_002c5978("TMD CALC", 2, 0, 0, reinterpret_cast<void*>(0x001CA648), work, 0);
    *reinterpret_cast<void**>(work) = calc_task;

    AsdTask_CreateDraw_002c4c00("TMD DDRAW", 0x57, 0, 0, reinterpret_cast<void*>(0x001CC914), work, reinterpret_cast<u32>(calc_task));

    u8* group = work + 0x28;
    UiSpriteGroup_Init_002c3344(group);

    u8* table = g_StatusDownSpriteTable_00407d58;
    UiSpriteGroup_BindTable_002c32f8(group, 0, 0x50, table - 0xA0, 0x50, table - 0x50, 0, 0, table, 0x150);

    UiAnimSprite_SetupEx_002bdb2c(work + 0x48, 0x20, -1, 0, group, 1, 1.0f);
    UiAnimSprite_SetMode_002bdac0(work + 0x48, 0);

    UiAnimSprite_SetupEx_002bdb2c(work + 0xD4, 0x20, -1, 1, group, 1, 1.0f);
    UiAnimSprite_SetMode_002bf030(work + 0xD4, 0);

    void* spr = engine_func_002bda1c(work + 0x160);
    *reinterpret_cast<void**>(work + 0x22A0) = spr;
    engine_func_002bda10(spr, 0xFF);
    engine_func_002bda00(spr, 0, 0, 1.0f);

    engine_func_002c4450(work + 0x42C, 0x29, -1);
    work[0x2392] = 1;
}

extern "C" void h8_ui_statusdown_init_mutation() {
    g_StatusDownContext_0044e190 = reinterpret_cast<void*>(0xDEADBEEF);
}
