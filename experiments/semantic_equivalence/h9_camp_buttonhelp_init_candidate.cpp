#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;
typedef int8_t s8;
typedef float f32;

struct ButtonHelpManager {
    s8 ref_count;
    u8 pad[3];
    u8* work;
};

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void  UiSpriteGroup_Init_002c3344(void* obj);
    void  UiSpriteGroup_BindTable_002c32f8(void* obj, u32 t1, u32 s1, u32 t2, u32 s2, u32 a, u32 b, u32 c, u32 d, u32 t3, u32 s3);
    void  UiAnimSprite_SetupEx_002bdb2c(void* node, u32 a, u32 b, void* grp, f32 scale, u32 flag);
    void  UiAnimSprite_SetMode_002bf030(void* node, u32 a, u32 b, u32 c);

    extern ButtonHelpManager g_ButtonHelpManager_0043da28;
}

extern "C" void h9_camp_buttonhelp_init_candidate() {
    ButtonHelpManager* mgr = &g_ButtonHelpManager_0043da28;
    if (mgr->ref_count <= 0) {
        u8* work = mgr->work;
        if (!work) {
            work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x564, 1));
            mgr->work = work;
        }
        AsdMem_Zero_002c4b30(work, 0x564);

        void* calc = AsdTask_Create_002c5978("ButtonHelp CALC", 1, 0, 0, reinterpret_cast<void*>(0x002108CC), work, 0);
        *reinterpret_cast<void**>(work) = calc;

        void* draw = AsdTask_CreateDraw_002c4c00("ButtonHelp DDRAW", 0xE6, 0, 0, reinterpret_cast<void*>(0x002108D0), work, 0);
        *reinterpret_cast<void**>(work + 8) = draw;

        UiSpriteGroup_Init_002c3344(work + 0x14);
        UiSpriteGroup_BindTable_002c32f8(work + 0x14, 0x004025A0, 0x0C, 0x004025A0, 0x30, 0, 0, 0, 0, 0x004025A0, 0xA8);

        for (u32 i = 0; i < 6; ++i) {
            u8* node = work + 0x34 + i * 0x64;
            UiAnimSprite_SetupEx_002bdb2c(node, 0x12, 3, work + 0x14, 1.0f, 0x10);
            UiAnimSprite_SetMode_002bf030(node, 0x12, i + 0x11, 3);
        }
    }
    mgr->ref_count++;
}

extern "C" void h9_camp_buttonhelp_init_mutation() {
    ButtonHelpManager* mgr = &g_ButtonHelpManager_0043da28;
    mgr->ref_count = -1;
}
