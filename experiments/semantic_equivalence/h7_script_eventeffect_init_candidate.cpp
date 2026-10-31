#include <cstdint>

typedef uint32_t u32;
typedef uint8_t  u8;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);

    extern void* g_EventEffectWork_0043dee8;
}

struct EventEffectWork {
    void* calc_task;      // 0x00
    void* draw_up_left;   // 0x04
    void* draw_up_right;  // 0x08
    u32   field_0c;       // 0x0C
    u32   field_10;       // 0x10
    float field_14;       // 0x14
    u8    flag_18;        // 0x18
};

extern "C" void h7_script_eventeffect_init_candidate() {
    EventEffectWork* work = static_cast<EventEffectWork*>(g_EventEffectWork_0043dee8);
    if (!work) {
        work = static_cast<EventEffectWork*>(AsdMem_Alloc_002c4b84(0x100, 0x54, 0, sizeof(EventEffectWork), 1));
        g_EventEffectWork_0043dee8 = work;
    }

    u32* words = reinterpret_cast<u32*>(work);
    for (u32 i = 0; i < 7; ++i) {
        words[i] = 0;
    }

    void* calc = AsdTask_Create_002c5978("BlinkFade Calc", 1, 0, 0, reinterpret_cast<void*>(0x00222428), work, 0);
    work->calc_task = calc;

    AsdTask_CreateDraw_002c4c00("BlinkFade DrawUpLeft", 0x81, 0, 0, reinterpret_cast<void*>(0x002221F0), work, reinterpret_cast<u32>(calc));
    AsdTask_CreateDraw_002c4c00("BlinkFade DrawUpRight", 0xDF, 0, 0, reinterpret_cast<void*>(0x002221F0), work, reinterpret_cast<u32>(calc));

    work->field_10 = 0;
    work->draw_up_right = nullptr;
    work->flag_18 = 0;
    work->field_0c = 0x28;
    work->field_14 = 1.0f;
}

extern "C" void h7_script_eventeffect_init_mutation() {
    g_EventEffectWork_0043dee8 = reinterpret_cast<void*>(0xDEADBEEF);
}
