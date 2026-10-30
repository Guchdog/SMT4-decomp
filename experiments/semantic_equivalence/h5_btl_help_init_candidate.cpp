#include <cstdint>

typedef uint8_t u8;
typedef uint32_t u32;
typedef int32_t s32;

struct BtlHelpWork {
    void* parent_work;                  // +0x00
    u8 pad_04[0x48];                    // +0x04..+0x4C
    void* calc_task;                    // +0x4C: Task handle ("btlHelp Calc", tag 0x2)
    u8 pad_50[4];                       // +0x50..+0x54
};

extern "C" {
    s32 Task_Destroy_002bf41c(void* task);
    void* Task_Create_002c4c00(const char* name, u32 tag, u32 prio, u32 arg3,
                               void (*func)(void*), void* arg, u32 extra, void* parent);
    void* Mem_Alloc_002c4b84(u32 heap, u32 arg1, u32 arg2, u32 size, u32 align);
    void btlHelp_Calc_001b5398(void*);
    extern void* g_BtlHelpManager_00435d78;
}

extern "C" void h5_btl_help_init_candidate(BtlHelpWork* work) {
    if (!work) return;

    if (Task_Destroy_002bf41c(work->calc_task) != 0) {
        return;
    }

    void* task = Task_Create_002c4c00("btlHelp Calc", 2, 0, 0,
                                     btlHelp_Calc_001b5398, work,
                                     0x0020ee34, work->parent_work);
    work->calc_task = task;

    void* buf = Mem_Alloc_002c4b84(0x100, 0x100, 0, 0x0C, 1);
    g_BtlHelpManager_00435d78 = buf;
    if (buf) {
        ((u32*)buf)[0] = 0;
        ((u32*)buf)[1] = 0;
        ((u32*)buf)[2] = 0;
    }
}

extern "C" void h5_btl_help_init_mutation(BtlHelpWork* work) {
    if (!work) return;
    work->calc_task = nullptr;
}
