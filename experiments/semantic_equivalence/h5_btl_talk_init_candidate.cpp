#include <cstdint>

typedef uint8_t u8;
typedef int16_t s16;
typedef uint32_t u32;
typedef int32_t s32;

struct BtlTalkWork {
    void* parent_work;                  // +0x00
    u8 pad_04[0x1C];                    // +0x04..+0x20
    void* talk_task;                    // +0x20: Task handle ("btlTalk Calc", tag 0x2)
    u8 pad_24[0x10];                    // +0x24..+0x34
};

extern "C" {
    s32 Task_Destroy_002bf41c(void* task);
    void* Task_Create_002c4c00(const char* name, u32 tag, u32 prio, u32 arg3,
                               void (*func)(void*), void* arg, u32 extra, void* parent);
    void* Mem_Alloc_002c4b84(u32 heap, u32 arg1, u32 arg2, u32 size, u32 align);
    void Talk_Setup_002c4450(void* talk_sub);
    void Talk_Register_00267f68(void* host);
    void btlTalk_Calc_001b71b8(void*);
    extern void* g_pBtlTalkBuffer_00439b58;
    extern void* g_TalkHost_00439ca8;
}

extern "C" void h5_btl_talk_init_candidate(BtlTalkWork* work, void* ctx, s32 arg2, s32 arg3) {
    if (!work) return;

    Task_Destroy_002bf41c(work->talk_task);

    void* buf = Mem_Alloc_002c4b84(0x100, 0x100, 0, 0xCC, 1);
    g_pBtlTalkBuffer_00439b58 = buf;

    void* task = Task_Create_002c4c00("btlTalk Calc", 2, 0, 0,
                                     btlTalk_Calc_001b71b8, work,
                                     0x0020f35c, work->parent_work);
    work->talk_task = task;

    if (buf) {
        char* b = (char*)buf;
        *(void**)(b + 0x00) = work;
        *(void**)(b + 0x04) = ctx;
        *(s32*)(b + 0x1C) = arg2;
        *(s32*)(b + 0x20) = arg3;
        *(u8*)(b + 0xC4) = 0;
        *(u8*)(b + 0xC5) = 0;
        *(s32*)(b + 0xC8) = -1;

        if (ctx) {
            char* sub = *(char**)((char*)ctx + 0x28);
            if (sub) {
                s16 speaker = *(s16*)(sub + 0x14E);
                *(s32*)(b + 0x30) = (s32)speaker;
            }
        }

        Talk_Setup_002c4450(b + 0x34);
        if (g_TalkHost_00439ca8) {
            Talk_Register_00267f68(g_TalkHost_00439ca8);
        }
        *(s32*)(b + 0x18) = 0;
    }
}

extern "C" void h5_btl_talk_init_mutation(BtlTalkWork* work, void* ctx, s32 arg2, s32 arg3) {
    if (!work) return;
    work->talk_task = nullptr;
}
