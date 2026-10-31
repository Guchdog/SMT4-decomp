#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;
typedef int8_t s8;
typedef int16_t s16;
typedef float f32;

struct LegionDrawManager {
    s8 ref_count;
    u8 pad[3];
    u8* work;
};

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void  UiSpriteGroup_Init_002c3344(void* obj);
    void  UiSpriteGroup_BindTable_002c32f8(void* obj, u32 t1, u32 s1, u32 t2, u32 s2, u32 a, u32 b, u32 c, u32 d, u32 t3, u32 s3);
    void  camp_func_002bdb2c(void* node, u32 a, u32 b, void* grp, f32 scale, u32 flag);
    void  battle_func_002af854(void* node, u32 a, u32 b);

    extern LegionDrawManager g_BibleLegionDrawManager_0043d9e0;
}

extern "C" void h9_camp_biblelegiondraw_init_candidate() {
    LegionDrawManager* mgr = &g_BibleLegionDrawManager_0043d9e0;
    if (mgr->ref_count <= 0) {
        u8* work = mgr->work;
        if (!work) {
            work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x474, 1));
            mgr->work = work;
            *reinterpret_cast<u32*>(work + 4) = 0;
            *reinterpret_cast<s16*>(work + 8) = -1;
            *reinterpret_cast<u32*>(work + 0xC) = 0;
            *reinterpret_cast<s16*>(work + 0x10) = -1;
            *reinterpret_cast<u32*>(work + 0x14) = 0;
            *reinterpret_cast<s16*>(work + 0x18) = -1;
            work[0x1C] = 0;
            work[0x1D] = 0;
            work[0x1E] = 0;
            work[0x1F] = 0;
            AsdMem_Zero_002c4b30(work + 0x290, 0x1E0);
            *reinterpret_cast<u32*>(work + 0x470) = 0;
        }

        void* calc = AsdTask_Create_002c5978("LegionDrawUp CALC", 2, 0, 0, reinterpret_cast<void*>(0x003AC6A0), 0, 0);
        *reinterpret_cast<void**>(work) = calc;

        UiSpriteGroup_Init_002c3344(work + 0x20);
        UiSpriteGroup_BindTable_002c32f8(work + 0x20, 0x00402414, 0x24, 0x00402438, 0x18, 0, 0, 0, 0, 0x00402450, 0x70);

        for (u32 i = 0; i < 2; ++i) {
            u8* node = work + i * 0x8C;
            camp_func_002bdb2c(node + 0x40, 0x23, 0, work + 0x20, 1.0f, 0x15);
            battle_func_002af854(node + 0x40, 0, 0);
            camp_func_002bdb2c(node + 0x158, 0x23, 0, work + 0x20, 1.0f, 0x15);
            battle_func_002af854(node + 0x158, 1, 0);
        }
    }
    mgr->ref_count++;
}

extern "C" void h9_camp_biblelegiondraw_init_mutation() {
    LegionDrawManager* mgr = &g_BibleLegionDrawManager_0043d9e0;
    mgr->ref_count = -1;
}
