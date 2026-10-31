#include <cstdint>

typedef uint32_t u32;
typedef uint8_t u8;
typedef uint16_t u16;

struct SaveLoadProcessWork {
    void* task;        // +0x00
    u32 state;         // +0x04
    void* buffer;      // +0x08
    u32 file_size;     // +0x0C
    u32 slot;          // +0x10
    u32 extra;         // +0x14
};

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  Subsystem_Reset_0026b7ec(u32 val);
    void  Subsystem_Reset_002594cc(u32 val);
    void  Subsystem_Reset_002594ac(u32 val);
    u8*   GetContext_002c0b94();
    void* AsdTask_Create(const char* name, u32 priority, u32 arg2, u32 arg3, void* fn, void* arg, void* work, u32 unused);
    void  AsdTask_SetFlags(void* task, u32 flag1, u32 flag2);
    void  SaveLoadProcess_Write(void*);
    extern u8 g_SaveLoadContext_0043e2f0[0x10];
    extern const char g_szSave_00323034[];
}

extern "C" void* h6_saveload_process_close_candidate(u32 slot, u32 difficulty) {
    auto* work = static_cast<SaveLoadProcessWork*>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, sizeof(SaveLoadProcessWork), 1));
    if (!work) return nullptr;

    Subsystem_Reset_0026b7ec(1);
    Subsystem_Reset_002594cc(1);
    Subsystem_Reset_002594ac(1);

    work->buffer = nullptr;
    u8* ctx = GetContext_002c0b94();
    u8 slot_val = ctx ? ctx[3] : 0;
    work->slot = (slot_val != 0) ? slot_val : 1;

    u8* g_ctx = g_SaveLoadContext_0043e2f0;
    g_ctx[3] = 0;
    g_ctx[4] = 0;
    *reinterpret_cast<u16*>(&g_ctx[6]) = 0;
    *reinterpret_cast<u32*>(&g_ctx[8]) = 0;
    g_ctx[0] = 0;
    g_ctx[1] = 0;
    g_ctx[2] = 0;

    work->slot = slot;

    void* task = AsdTask_Create(g_szSave_00323034, 2, 0, 0, reinterpret_cast<void*>(SaveLoadProcess_Write), reinterpret_cast<void*>(0x00324D6C), work, 0);
    work->task = task;
    AsdTask_SetFlags(task, 0x80000, 0);

    work->state = 0;
    work->extra = difficulty;

    return task;
}

extern "C" void* h6_saveload_process_close_mutation(u32 slot, u32 difficulty) {
    return nullptr;
}
