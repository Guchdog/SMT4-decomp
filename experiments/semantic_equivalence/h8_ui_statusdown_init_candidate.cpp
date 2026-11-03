#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, void* parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, u32 u1, void* work, void* parent);
    void  UiSpriteGroup_Init_002c3344(void* group);
    void  UiSpriteGroup_BindTable_002c32f8(void* group, u8* t1, u32 s1, u8* t2, u32 s2, u8* t3, u32 s3, u32 f1, u32 f2, u8* t4, u32 s4);
    void  UiAnimSprite_SetupEx_002bdb2c(void* sprite, u32 id, u32 param, void* group, u32 flag, float scale);
    void  UiAnimSprite_SetMode_002bdac0(void* sprite, u32 mode, u32 flags);
    void  UiAnimSprite_SetAnim_002bf030(void* sprite, u32 anim);
    void  UiAnimSprite_Setup_002bf0a8(void* sprite, u32 id, int param, u32 index, void* group, u32 flag, float scale);
    void* engine_func_002bda1c(u32 arg0);
    void  engine_func_002bda10(void* ptr, u32 alpha);
    void  engine_func_002bda00(void* ptr, u32 a, u32 color, float scale);
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

    void* calc_task = AsdTask_Create_002c5978("TMD CALC", 2, 0, 0, reinterpret_cast<void*>(0x001CA648), nullptr, nullptr);
    *reinterpret_cast<void**>(work) = calc_task;

    void* draw_task = AsdTask_CreateDraw_002c4c00("TMD DDRAW", 0xE7, 0, 0, reinterpret_cast<void*>(0x001CC914), 0, nullptr, calc_task);
    *reinterpret_cast<void**>(work + 4) = draw_task;

    u8* group = work + 8;
    UiSpriteGroup_Init_002c3344(group);

    u8* table = g_StatusDownSpriteTable_00407d58;
    UiSpriteGroup_BindTable_002c32f8(group, table - 0xA8, 0x48, table - 0x60, 0x48, table - 0x18, 0x18, 0, 0, table, 0x134);

    UiAnimSprite_SetupEx_002bdb2c(work + 0x28, 0x1A, 0x3E8, group, 1, 1.0f);
    UiAnimSprite_SetMode_002bdac0(work + 0x28, 0, 0);

    UiAnimSprite_SetupEx_002bdb2c(work + 0xB4, 0x1A, 0x3E8, group, 1, 1.0f);
    UiAnimSprite_SetAnim_002bf030(work + 0xB4, 0);

    UiAnimSprite_SetupEx_002bdb2c(work + 0x140, 0x1A, 0x3E8, group, 1, 1.0f);
    UiAnimSprite_SetAnim_002bf030(work + 0x140, 1);

    UiAnimSprite_SetupEx_002bdb2c(work + 0x1CC, 0x1A, 0x3E8, group, 1, 1.0f);
    UiAnimSprite_SetMode_002bdac0(work + 0x1CC, 4, 0);

    UiAnimSprite_SetupEx_002bdb2c(work + 0x258, 0x1A, 0x3E8, group, 1, 1.0f);
    UiAnimSprite_SetMode_002bdac0(work + 0x258, 5, 0);

    UiAnimSprite_SetupEx_002bdb2c(work + 0x2E4, 0x1A, 0x3E8, group, 1, 1.0f);
    UiAnimSprite_SetMode_002bdac0(work + 0x2E4, 0, 0);

    UiAnimSprite_Setup_002bf0a8(work + 0x370, 0x1A, -1, 0x1C, group, 0xC9, 1.0f);
    UiAnimSprite_SetAnim_002bf030(work + 0x370, 2);
    *reinterpret_cast<u16*>(work + 0x370 + 0x3A) = 2;

    void* spr = engine_func_002bda1c(0);
    *reinterpret_cast<void**>(work + 0x22A0) = spr;
    engine_func_002bda10(spr, 0xFF);
    engine_func_002bda00(spr, 0, 0x646464FF, 0.0f);

    engine_func_002c4450(work + 0x42C, 0x29, -1);
    work[0x2392] = 1;
}

extern "C" void h8_ui_statusdown_init_mutation() {
    g_StatusDownContext_0044e190 = reinterpret_cast<void*>(0xDEADBEEF);
}
