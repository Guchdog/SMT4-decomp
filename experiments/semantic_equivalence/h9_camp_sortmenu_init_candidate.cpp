#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;
typedef int8_t s8;
typedef int32_t s32;
typedef float f32;

struct SortMenuManager {
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
    void  UiAnimSprite_SetMode_002bdac0(void* node, u32 a, u32 b);

    extern SortMenuManager g_SortMenuManager_0043dd20;
}

extern "C" void h9_camp_sortmenu_init_candidate(s32 mode) {
    SortMenuManager* mgr = &g_SortMenuManager_0043dd20;
    if (mgr->ref_count <= 0) {
        u8* work = mgr->work;
        if (!work) {
            work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x878, 1));
            mgr->work = work;
        }
        AsdMem_Zero_002c4b30(work, 0x878);

        void* calc = AsdTask_Create_002c5978("SORT CALC", 2, 0, 0, reinterpret_cast<void*>(0x001A1E7C), work, 0);
        *reinterpret_cast<void**>(work) = calc;

        void* draw = AsdTask_CreateDraw_002c4c00("SORT DDRAW", 0xE7, 0, 0, reinterpret_cast<void*>(0x001A25CC), work, 0);
        *reinterpret_cast<void**>(work + 4) = draw;

        UiSpriteGroup_Init_002c3344(work + 0x08);
        UiSpriteGroup_BindTable_002c32f8(work + 0x08, 0x00402DAC, 0x24, 0x00402DAC, 0x18, 0, 0, 0, 0, 0x00402DAC, 0xA8);

        for (u32 i = 0; i < 13; ++i) {
            u8* node = work + 0x28 + i * 0x64;
            UiAnimSprite_SetupEx_002bdb2c(node, 0x1E, 0, work + 0x08, 1.0f, 0);
            UiAnimSprite_SetMode_002bdac0(node, 0, 0);
        }

        *reinterpret_cast<s32*>(work + 0x750) = mode;
    }
    mgr->ref_count++;
}

extern "C" void h9_camp_sortmenu_init_mutation() {
    SortMenuManager* mgr = &g_SortMenuManager_0043dd20;
    mgr->ref_count = -1;
}
