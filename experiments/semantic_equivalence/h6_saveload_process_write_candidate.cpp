#include <cstdint>
#include <cstring>

typedef uint32_t u32;
typedef uint8_t u8;
typedef uint16_t u16;
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
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  AsdMem_Free(void* ptr);
    void  SaveLoad_DispatchWorker_00247c64(u32 op, u32 unk, u32 slot, void* buf, u32 size);
    u32   Worker_IsComplete_001a1bf8();
    u32   Worker_GetError_002ced0c();
    void  SaveHelper_002e0c54();
    void* SaveHelper_0026b844();
    void* SaveHelper_0026b830();
    void  SaveHelper_0026b734();
    void  Data_Serialize_002adb40(void* buf);
    void  Metadata_Copy_002bcf58(void* dst, void* src, u32 size);
    u8*   GetContext_002c0b94();
    extern u8 g_SaveLoadContext_0043e2f0[0x10];
}

extern "C" s32 h6_saveload_process_write_candidate() {
    SaveLoadProcessWork* work = SaveLoadProcess_GetWork_002c0ac8();
    if (!work) return 0;

    u8* g_ctx = g_SaveLoadContext_0043e2f0;

    switch (work->state) {
    case 0: {
        const u32 save_size = 0x24DB0;
        work->file_size = save_size;
        void* buf = AsdMem_Alloc_002c4b84(0x100, 0x100, 0, save_size, 1);
        work->buffer = buf;
        SaveHelper_002e0c54();
        u8* ctx = GetContext_002c0b94();
        if (ctx) ctx[3] = static_cast<u8>(work->slot);
        void* hdr = SaveHelper_0026b844();
        std::memcpy(buf, hdr, 0x80);
        SaveHelper_0026b830();
        u8* u8_buf = static_cast<u8*>(buf);
        Data_Serialize_002adb40(u8_buf + 0x80);
        u8* meta = u8_buf + 0x88;
        ctx = GetContext_002c0b94();
        Metadata_Copy_002bcf58(meta, ctx, 0x24D28);
        *reinterpret_cast<u16*>(meta) = 3;
        meta[2] = static_cast<u8>(work->extra);
        SaveHelper_0026b734();
        SaveLoad_DispatchWorker_00247c64(2, 0, work->slot, buf, save_size);
        work->state = 1;
        return 0;
    }
    case 1: {
        if (Worker_IsComplete_001a1bf8() != 1) {
            return 0;
        }
        u32 err = Worker_GetError_002ced0c();
        if (work->buffer) {
            AsdMem_Free(work->buffer);
            work->buffer = nullptr;
        }
        work->state = (err == 0) ? 2 : 3;
        return 0;
    }
    case 2: {
        g_ctx[1] = 1;
        g_ctx[4] = 1;
        return -1;
    }
    case 3: {
        g_ctx[1] = 1;
        g_ctx[4] = 0;
        return -1;
    }
    default:
        return 0;
    }
}

extern "C" s32 h6_saveload_process_write_mutation() {
    return 0x55;
}
