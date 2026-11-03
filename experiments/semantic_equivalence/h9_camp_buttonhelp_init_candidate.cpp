#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;
typedef int8_t s8;
typedef float f32;

struct ButtonHelpManager {
    s8 ref_count;      // +0x00
    u8 pad[3];         // +0x01
    u8* work;          // +0x04
    u32 script_id;     // +0x08
    u32 script_arg;    // +0x0c
};

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, void* parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, u32 u1, void* work, void* parent);
    void  UiSpriteGroup_Init_002c3344(void* obj);
    void  UiSpriteGroup_BindTable_002c32f8(void* obj, u32 t1, u32 s1, u32 t2, u32 s2, u32 a, u32 b, u32 c, u32 d, u32 t3, u32 s3);
    void  UiAnimSprite_SetupEx_002bdb2c(void* node, u32 a, u32 b, void* grp, f32 scale, u32 flag);
    void  QuestUi_SetTextPair_00262448(void* node, u32 a, u32 b, u32 c);
    void  UiAnimSprite_SetText_00296154(void* node, u32 a, u32 b);
    void* AsdText_CreateDefault_002bda1c(u32 a0);
    void  AsdText_SetAlpha_002bda10(void* handle, u32 alpha);
    void  AsdText_SetColorAndScale_002bda00(void* handle, u32 a1, u32 color, f32 scale);
    void* scrScriptProcess_func_002972f8(u32 a0, u32 a1);

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

        void* calc = AsdTask_Create_002c5978("ButtonHelp CALC", 1, 0, 0, reinterpret_cast<void*>(0x001C0B38), reinterpret_cast<void*>(0x002108CC), nullptr);
        *reinterpret_cast<void**>(work) = calc;

        void* draw = AsdTask_CreateDraw_002c4c00("ButtonHelp DDRAW", 0xE6, 0, 0, reinterpret_cast<void*>(0x002108D0), 0, nullptr, calc);
        *reinterpret_cast<void**>(work + 8) = draw;

        UiSpriteGroup_Init_002c3344(work + 0x14);
        UiSpriteGroup_BindTable_002c32f8(
            work + 0x14,
            0x00402556, 0x30,
            0x00402588, 0x0C,
            0x00402594, 0x0C,
            0, 0,
            0x004025A0, 0xA8
        );

        for (u32 i = 0; i < 6; ++i) {
            u8* node = work + 0x34 + i * 0x8C;
            UiAnimSprite_SetupEx_002bdb2c(node, 0x12, 3, work + 0x14, 1.0f, 0x10);
            QuestUi_SetTextPair_00262448(node, 0x12, i + 0x11, 3);
        }

        UiAnimSprite_SetupEx_002bdb2c(work + 0x37C, 0x12, 0, work + 0x14, 1.0f, 0x10);
        UiAnimSprite_SetupEx_002bdb2c(work + 0x408, 0x12, 1, work + 0x14, 1.0f, 0x10);

        work[0x4C8] = 0;
        for (u32 i = 0; i < 2; ++i) {
            u8* node = work + 0x37C + i * 0x8C;
            *reinterpret_cast<u16*>(node + 0x3A) = 2;
            UiAnimSprite_SetText_00296154(node, 0x12, 0);
            node[0x3C] = 1;
            *reinterpret_cast<u32*>(node + 0x0C) = 0;
            *reinterpret_cast<u32*>(node + 0x10) = 0;
            *reinterpret_cast<u32*>(node + 0x14) = 0;
        }

        work[0x4C5] = 0;
        work[0x4C6] = 1;
        work[0x4C4] = 1;
        work[0x4C7] = 0;

        void* text = AsdText_CreateDefault_002bda1c(0);
        *reinterpret_cast<void**>(work + 0x558) = text;
        AsdText_SetAlpha_002bda10(text, 0x323232FF);
        AsdText_SetColorAndScale_002bda00(text, 0, 0x646464FF, 0.0f);

        void* proc = scrScriptProcess_func_002972f8(mgr->script_arg, mgr->script_id);
        *reinterpret_cast<void**>(work + 0x560) = proc;
    }
    mgr->ref_count++;
}

extern "C" void h9_camp_buttonhelp_init_mutation() {
    ButtonHelpManager* mgr = &g_ButtonHelpManager_0043da28;
    mgr->ref_count = -1;
}
