#include <cstdint>

typedef uint32_t u32;
typedef uint8_t u8;
typedef int32_t s32;

struct SaveLoadProcessWork {
    void* task;        // +0x00
    u32 state;         // +0x04
    void* buffer;      // +0x08
    u32 file_size;     // +0x0C
    u32 slot;          // +0x10
    u32 extra;         // +0x14
};

extern "C" {
    SaveLoadProcessWork* SaveLoadProcess_GetWork_002c0ac8();
    void* AsdMem_Alloc_002c54f0(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  SaveLoad_DispatchWorker_00247c64(u32 op, u32 unk, u32 slot, void* buf, u32 size);
    u32   Worker_IsComplete_001a1bf8();
    u32   Worker_GetError_002ced0c();
    void* SaveHelper_0026b844();
    void* SaveHelper_0026b830();
    void  SaveHelper_0026b734();
    void* Metadata_Copy_002bcf58(void* dst, const void* src, u32 size);
    void  Data_Deserialize_002adb40(void* dst, void* payload);
    u8*   GetContext_002c0b94();
    extern u8 g_SaveLoadContext_0043e2f0[0x10];
}

extern "C" s32 h6_saveload_process_step_candidate() {
    SaveLoadProcessWork* work = SaveLoadProcess_GetWork_002c0ac8();
    if (!work) return 0;

    u8* g_ctx = g_SaveLoadContext_0043e2f0;

    switch (work->state) {
    case 4: {
        const u32 save_size = 0x24DB0;
        work->file_size = save_size;
        void* buf = AsdMem_Alloc_002c54f0(0x100, 0x100, 0, save_size, 1);
        work->buffer = buf;
        SaveLoad_DispatchWorker_00247c64(3, 0, work->slot, buf, save_size);
        work->state = 5;
        return 0;
    }
    case 5: {
        if (Worker_IsComplete_001a1bf8() != 1) {
            return 0;
        }
        if (Worker_GetError_002ced0c() != 0) {
            work->state = 7;
            return 0;
        }
        u8* buf = static_cast<u8*>(work->buffer);
        u8* payload = buf + 0x80;
        u8* meta = buf + 0x88;

        void* hdr = SaveHelper_0026b844();
        Metadata_Copy_002bcf58(hdr, buf, 0x80);

        void* dst = SaveHelper_0026b830();
        Data_Deserialize_002adb40(dst, payload);

        u8* ctx = GetContext_002c0b94();
        Metadata_Copy_002bcf58(ctx, meta, 0x24D28);

        u8* ctx2 = GetContext_002c0b94();
        if (ctx2) ctx2[3] = static_cast<u8>(work->slot);
        SaveHelper_0026b734();
        work->state = 6;
        return 0;
    }
    case 6: {
        g_ctx[3] = 1;
        g_ctx[0] = 1;
        return -1;
    }
    case 7: {
        g_ctx[3] = 0;
        g_ctx[0] = 1;
        return -1;
    }
    default:
        return 0;
    }
}

extern "C" s32 h6_saveload_process_step_mutation() {
    return 0x55;
}
