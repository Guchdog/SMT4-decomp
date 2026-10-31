#include <cstdint>

typedef uint32_t u32;
typedef int32_t  s32;
typedef uint8_t  u8;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);

    extern void* g_EventFadeWork_0043e088;
}

struct EventFadeWork {
    void* proc_task;  // 0x00
    u32   mode;       // 0x04
    float alpha;      // 0x08
    float step;       // 0x0C
    u32   flag;       // 0x10
    s32   frames;     // 0x14
};

extern "C" void h7_script_eventcmd_fade_candidate(u32 mode, s32 frames, u32 flag, float alpha) {
    EventFadeWork* work = static_cast<EventFadeWork*>(g_EventFadeWork_0043e088);
    if (!work) {
        work = static_cast<EventFadeWork*>(AsdMem_Alloc_002c4b84(0x100, 0x1CD, 0, sizeof(EventFadeWork), 1));
        g_EventFadeWork_0043e088 = work;

        work->alpha = 0.0f;
        work->step = 0.0f;
        work->frames = 0;
        work->flag = 0;

        void* proc = AsdTask_Create_002c5978("EventMessUnderFade_Proc", 2, 0, 0, reinterpret_cast<void*>(0x00317EB8), work, 0);
        work->proc_task = proc;

        AsdTask_CreateDraw_002c4c00("EventMessUnderFade_Draw", 0x80, 0, 0, reinterpret_cast<void*>(0x002E21DC), work, 0);
        AsdTask_CreateDraw_002c4c00("EventMessUnderFade_Draw", 0xDE, 0, 0, reinterpret_cast<void*>(0x002E21DC), work, 0);
    }

    work->frames = frames;
    work->flag = 0;

    if (flag) {
        work->mode = mode;
        if (frames) {
            work->alpha = 0.0f;
            work->step = alpha / static_cast<float>(frames);
        } else {
            work->alpha = alpha;
            work->step = 0.0f;
        }
    } else {
        if (frames) {
            if (work->alpha == 0.0f) {
                work->mode = mode;
            }
            work->alpha = alpha;
            work->step = -(alpha / static_cast<float>(frames));
        } else {
            work->mode = mode;
            work->alpha = 0.0f;
            work->step = 0.0f;
        }
    }
}

extern "C" void h7_script_eventcmd_fade_mutation(u32 mode, s32 frames, u32 flag, float alpha) {
    g_EventFadeWork_0043e088 = reinterpret_cast<void*>(0xDEADBEEF);
}
