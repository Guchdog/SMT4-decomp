#include "engine/aoc.h"
#include "engine/asd_symbols.h"
#include <cstdint>

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

extern "C" {
    // Allocators / memory helpers
    void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);         // 0x002c4b84
    void* AsdMem_AllocAlign(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);    // 0x002c54f0
    void  AsdMem_Free(void* ptr);                                           // 0x002c4360
    void* AsdWork_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 flag); // 0x002c34a4
    void* AsdWork_Alloc2(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 flag);// 0x002bf798
    void* AsdMem_AllocFlags(u32 size, u32 flags);                           // 0x002b76e8

    // nn result objects.  0x002BAD80 stores the code and resolves the module
    // description; 0x002A1578 returns the normalised value.
    void* Result_Construct(void* out, u32 code);                            // 0x002bad80
    u32   Result_Value(const void* result);                                 // 0x002a1578
    u32   Result_IsReady(const void* path_object);                          // 0x002a17c0
    u32   Result_IsClassA(const void* result);                              // 0x002a14a0
    u32   Result_IsClassB(const void* result);                              // 0x002a140c

    // Application helpers
    u32   AocApplet_Check98(void* applet);                                  // 0x002ad46c
    u32   AocApplet_IsFlag10000(void* applet);                              // 0x002a17d4

    // Path construction / dispatch
    void* AocPath_Build(void* out, void* path_root, const char* name);      // 0x0015db38
    void  AocPath_BuildLocal(void* out, void* path_root);                   // 0x002a150c
    u32   AocPath_Dispatch(void* applet, void* path_object,
                           u32 word2, u32 word3);                           // 0x0015dc64
    void  AocPath_Commit(void* applet, const void* path_object,
                         u32 code, u32 zero);                               // 0x002baca8

    // AsdFile / stream helpers
    void  AsdFile_Pair_Init(void* pair);                                    // 0x002bb09c
    s32   AsdFile_Open(void* out, const void* path, u32 mode);              // 0x002bb8e4
    s32   AsdFile_GetSize(void* file, u64* out_size);                       // 0x002bb88c
    s32   AsdFile_Read(void* file, u32* out_read, void* buffer, u32 size);  // 0x002bb804
    u32   AsdLoadFile_func_002ae6c8(const char* name, u32* out_status,
                                    u32 flags, void* callback,
                                    u32 callback_arg, u32 user);            // 0x002ae6c8
    u32   AsdLoadFile_Immediate(const char* name, u32* out_status,
                                u32 flags, u32 user);                       // 0x002a14e8
    void* AsdFile_LoadSync(const char* name, u32* out_size,
                           u32 flags, u32 user);                            // 0x002c5e3c
    void  AsdFile_ReleaseHandle(void* handle);                              // 0x002b93f0

    // String conversion / formatting
    void  UiText_Format(char* dst, const char* fmt, ...);                   // 0x002be7fc
    int   MbsInit(void* state);                                             // 0x002b9426
    u32   MbrLen(const char* s, u32 n, void* state);                        // 0x002b9408
    u32   MbrToWc(u16* out, const char* s, u32 n, void* state);             // 0x002c6388

    // AOC tasks / mount helpers
    void  AocMode_Set(u32 mode, u32 value);                                 // 0x00282e6c
    void  AocBoot_InitCalc(void* calc);                                     // 0x002baacc
    u32   AocContent_GetSize(u32* out_size, u32 id, u32 index,
                             u32 a3, u32 a4, u32 a5);                       // 0x00355304
    void  AocTexture_Destroy(void* handle);                                 // 0x0035311c
    void* AocTexture_Create(void* object, void* source,
                            void* buffer, u32 size);                        // 0x003530f8
    void  Aoc_ReleaseGlobal();                                              // 0x002b2520
    void  AocArchive_Destroy(void* handle);                                 // 0x0023a350
    void* AocArchive_Create(void* object, void* source,
                            void* buffer, u32 size);                        // 0x00352950

    // TMSprite upload helpers
    u32   UiTMSpr_func_0014f3fc(void* sprite);                              // 0x0014f3fc
    void  UiTMSpr_func_0014f070(void* sprite, void* buffer);                // 0x0014f070
    void  UiTMSpr_func_0014f30c(void* sprite, void* buffer);                // 0x0014f30c
    void  UiTMSpr_func_0014f1cc(void* sprite, void* buffer);                // 0x0014f1cc
}

// 0x00433158: the slot is shared with the camp/NPC row path (see
// engine/asd_symbols.h); aocFileLoad reads it as its path root, so the
// canonical name is g_CampMessageBundle and `g_AocPathRoot` was a duplicate.
extern "C" void* g_CampMessageBundle = nullptr;

namespace smt4::engine {

AocMain* g_AocMain = nullptr;                   // 0x00433048
AocBootProcessGlobal g_AocBootProcess{};        // 0x00432FE0
AocAppletState* g_AocAppletState = nullptr;     // 0x00432FC8

namespace {

// 0x0015C880: `ldr r2,[r0]` after loading the 0x00420870 table pointer.
constexpr u32 kAocFileVTableTable = 0x00420870;

/** Two-word nn::Result representation (`ldrd r0,r1,[...]`). */
struct SdkResult {
    u32 words[2];
};
static_assert(sizeof(SdkResult) == 0x08);

/** 20-byte path object returned by 0x0015DB38 / 0x002A150C. */
struct AocPathObject {
    u8 status;                          // +0x00: `ldrb r0,[r0]` (0x002a17c0)
    u8 pad_01[0x13];                    // +0x01..+0x14
};
static_assert(sizeof(AocPathObject) == 0x14);

// 0x0015CD08..0x0015CD24: `ldr r0,[r4,#0x24]!` is a pre-indexed write-back
// load.  The effective offsets are +0x24 (size) and, after r4 += 0x24, +0x90
// -> the original +0xB4 (notify), whose +0x08 receives the size.

u32 AocNormaliseResultCode(u32 code)
{
    // 0x0015CF4C..0x0015CF5C: sign ? 0xFFFFFFE0 + (code >> 27) : code >> 27.
    if ((code & 0x80000000u) != 0) {
        return 0xFFFFFFE0u + (code >> 27);
    }
    return code >> 27;
}

void AocFile_Close(void* file)
{
    // 0x0015C944..0x0015C968 / 0x0015C96C..0x0015C994: bit 0 marks
    // "notified", so the close helper runs on (word & ~1) first.
    u32 handle = *static_cast<u32*>(file);
    if ((handle & ~1u) != 0) {
        if ((handle & 1u) != 0) {
            AsdFile_NotifyClose();                       // 0x0015c958/0x0015c988
        }
        AsdFile_ReleaseHandle(reinterpret_cast<void*>(handle & ~1u)); // 0x0015c964
        // 0x0015C944 / 0x0015C96C: the clearing store is inside the branch;
        // an empty handle leaves the word untouched.
        *static_cast<u32*>(file) = 0;
    }
}

} // namespace

// ---------------------------------------------------------------------------
// aocFileLoad (0x0015C728)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0015c728, 2220)
void aocFileLoad_func_0015c728(AocLoadContext* context, AocFileLoadJob* job)
{
    // 0x0015C730..0x0015C78C: path object at sp+0x20 starts at status 0x64;
    // the result pair at sp+0x24 is zeroed through 0x002BAD80.
    AocPathObject path_object{};
    path_object.status = 0x64;
    SdkResult result{};

    // 0x0015C740..0x0015C75C: initialise the 0x18-byte file object head.
    AocFileObject file{};
    file.vtable = nullptr;
    file.handle = 0;

    AocPathObject built{};
    bool did_reinit = false;

    if (job->state == 1) {
        // 0x0015CDB4..0x0015CE54: asynchronous / deferred phase.
        if ((job->flags & 2) == 0) {
            job->state = 3;                          // 0x0015CE00
            g_AocAppletState->flags_754 |= 0x40;     // 0x0015CE08
            return;
        }

        if ((job->flags & 1) == 0) {
            // 0x0015CE18..0x0015CE2C: synchronous load straight into a buffer.
            job->buffer = AsdFile_LoadSync(job->name, &job->size, job->mode, job->user);
            job->state = 3;
            return;
        }

        if (job->callback != nullptr) {
            // 0x0015CDD4..0x0015CDF8: callback-driven asynchronous load.
            AsdLoadFile_func_002ae6c8(job->name, job->out, job->mode,
                                      reinterpret_cast<void*>(job->callback),
                                      job->callback_arg0, job->user);
            job->state = 2;                          // 0x0015CE48
            return;
        }

        // 0x0015CE38..0x0015CE48: load through the immediate helper.
        AsdLoadFile_Immediate(job->name, job->out, job->mode, job->user);
        job->state = 2;
        return;
    }

    if (job->state == 2) {
        // 0x0015C7A8..0x0015C7B4: cancellation completes immediately.
        job->state = 3;
        return;
    }

    if (job->state != 0) {
        // 0x0015C7B0: any other state simply returns.
        return;
    }

    // -----------------------------------------------------------------------
    // State 0: start.
    // -----------------------------------------------------------------------

    // 0x0015C7B8..0x0015C7C8: wait while the applet still owns the GPU.
    if (AocApplet_IsFlag10000(g_AocAppletState) != 0) {
        if (AocApplet_Check98(&g_AocAppletState->field_98) != 0) {
            // 0x0015C7E8..0x0015C804
            g_AocAppletState->flags_754 &= ~0x10000u;
            path_object.status = 0xC8;
            goto cleanup_result;
        }

        // 0x0015C828..0x0015C860: build the path object for job->path.
        AocPath_Build(&built, g_CampMessageBundle, job->path);
        path_object = built;

        // 0x0015C84C..0x0015C860: status >= 0x64 means "not ready".
        if (Result_IsReady(&path_object) != 0) {
            goto cleanup_result;
        }

        // 0x0015C864..0x0015C890: build the 0x18-byte file object through
        // the 0x00420870 vtable table.
        const AocFileVTableSlot* slot =
            reinterpret_cast<const AocFileVTableSlot*>(kAocFileVTableTable);
        void** vtable = slot->vtable;                   // 0x0015C878
        file.vtable = vtable;                           // 0x0015C884
        const u32 base_offset =
            *reinterpret_cast<u32*>(reinterpret_cast<u8*>(vtable) - 0x30);
        *reinterpret_cast<void**>(reinterpret_cast<u8*>(&file) + base_offset) =
            slot->self;                                 // 0x0015C890

        // 0x0015C8A4..0x0015C8F4: convert job->path (UTF-8) to UTF-16.
        u8 mbs_state[8] = {0, 0, 0, 0, 0, 0, 0, 0};
        u16 wide_path[0x108];
        MbsInit(mbs_state);                             // 0x0015C8B0
        const char* scan = job->path;
        u16* write = wide_path;
        for (;;) {
            const u32 length = MbrLen(scan, 0x105, mbs_state); // 0x0015C8C0
            if (length == 0) {
                break;
            }
            if (MbrToWc(write, scan, length, mbs_state) == 0) { // 0x0015C8E0
                break;
            }
            write += 1;
            scan += length;
        }
        *write = 0;                                     // 0x0015C8F4

        // 0x0015C8F8..0x0015C920: AsdFile_Open(&file.handle, wide_path, 1).
        file.vtable = vtable;
        file.handle = 0;
        const s32 open_result = AsdFile_Open(&file.handle, wide_path, 1);
        Result_Construct(&result, static_cast<u32>(open_result));
        if (static_cast<s32>(Result_Value(&result)) < 0) {
            AocFile_Close(&file.handle);
            goto cleanup_result;
        }

        // 0x0015C998..0x0015CA24: query the stream size.
        u64 stream_size = 0;
        const s32 size_result = AsdFile_GetSize(&file.handle, &stream_size);
        Result_Construct(&result, static_cast<u32>(size_result));
        if (static_cast<s32>(Result_Value(&result)) < 0) {
            AocFile_Close(&file.handle);
            goto cleanup_result;
        }

        job->size = static_cast<u32>(stream_size);      // 0x0015CA2C

        if (job->buffer == nullptr) {
            // 0x0015CA38..0x0015CA7C: mode selects the arena and flag word.
            if (job->mode == 0x10) {
                job->buffer = AsdWork_Alloc2(0x100, 0x100, 0, job->size, job->user, 0);
            } else if (job->mode == 1) {
                job->buffer = AsdWork_Alloc2(0x10000, 0x100, 0, job->size, job->user, 1);
            } else if (job->mode == 0x11) {
                job->buffer = AsdWork_Alloc2(0x10000, 0x100, 0, job->size, job->user, 0);
            } else {
                job->buffer = AsdWork_Alloc2(0x100, 0x100, 0, job->size, job->user, 1);
            }
        }

        // 0x0015CA80..0x0015CAB4: read the whole stream.
        u32 read_count = 0;
        const s32 read_result = AsdFile_Read(&file.handle, &read_count,
                                             job->buffer, job->size);
        Result_Construct(&result, static_cast<u32>(read_result));
        if (read_count == 0) {
            // 0x0015CB54..0x0015CB64: empty read is reported as 0xD9004586.
            Result_Construct(&result, 0xD9004586u);
        }

        if (static_cast<s32>(Result_Value(&result)) < 0) {
            AocFile_Close(&file.handle);
            goto cleanup_result;
        }

        // 0x0015CBC0..0x0015CBE0: release the file object before committing.
        AocFile_Close(&file.handle);

        if (context->initialized == 1) {
            goto success;
        }

        // 0x0015CBFC..0x0015CC2C: resolve the final path object; non-zero
        // status means success, zero means the load failed.
        AocPath_BuildLocal(&built, g_CampMessageBundle);
        path_object = built;
        if (Result_IsReady(&path_object) == 0) {
            goto success;
        }
        goto cleanup_result;
    }

    // 0x0015C808..0x0015CE14: applet is idle.
    if ((job->flags & 2) == 0) {
        job->state = 3;                                  // 0x0015CDFC
        g_AocAppletState->flags_754 |= 0x40;             // 0x0015CE08
        return;
    }

    job->state = 1;                                      // 0x0015C814
    g_AocAppletState->flags_754 |= 0x20;                 // 0x0015C820
    return;

// ---------------------------------------------------------------------------
// Shared error / retry paths
// ---------------------------------------------------------------------------

cleanup_result:
    // 0x0015CC58..0x0015CCD0
    AsdSound_GetTableEntry(0);
    AocPath_BuildLocal(&built, g_CampMessageBundle);           // 0x0015CC6C
    g_AocAppletState->flags_754 =
        (g_AocAppletState->flags_754 & ~0x10000u) | 0x10u; // 0x0015CC7C..0x0015CC84

    if (job->buffer != nullptr) {
        AsdMem_Free(job->buffer);                        // 0x0015CC94
        job->buffer = nullptr;
    }
    if (job->out != nullptr) {
        *job->out = 0;                                   // 0x0015CCAC
    }

    if (Result_Value(&result) != 0xC9413891u) {          // 0x0015CCBC
        goto retry_dispatch;
    }
    AsdSound_GetTableEntry(0);                                     // 0x0015CCC8
    return;

retry_dispatch:
    // 0x0015CE58..0x0015CED4
    if (AocApplet_Check98(&g_AocAppletState->field_98) != 0) {
        g_AocAppletState->flags_754 &= ~0x10000u;        // 0x0015CE78
    } else if (path_object.status != 0xC8) {
        goto retry_commit;
    } else {
        goto retry_reinit;
    }

retry_reinit:
    // 0x0015CE90..0x0015CED4
    AsdSound_GetTableEntry(0);
    path_object.status = 0xC8;
    job->state = 1;
    {
        const u32 code = (g_AocAppletState->flags_754 & 0x100u) != 0
                             ? 0x66u : 0x65u;
        AocPath_Commit(g_AocAppletState, &path_object, code, 0);
    }
    did_reinit = true;
    // r5 = 1 in the listing: retry_commit always runs next.

retry_commit:
    // 0x0015CED8..0x0015CF10
    built = path_object;
    {
        const u32 ret = AocPath_Dispatch(g_AocAppletState, &built,
                                         result.words[0], result.words[1]);
        if (ret != 0) {
            path_object.status = 0x64;
            job->state = 1;
        } else if (!did_reinit) {
            AsdSound_GetTableEntry(0);
        }
    }

    // 0x0015CF14..0x0015CFC8: classify the open result.  -4 and -5 are the
    // retryable classes; everything else returns through the common exit.
    if (Result_IsClassA(&file.handle) != 0 ||
        Result_IsClassB(&file.handle) != 0) {
        path_object.status = 0x64;
        job->state = 1;
        const u32 code = Result_Value(&file.handle);
        const u32 normalised = AocNormaliseResultCode(code);
        if (normalised != static_cast<u32>(-4)) {
            if (normalised != static_cast<u32>(-5)) {
                return;
            }
        }
        if (static_cast<s32>(Result_Value(&file.handle)) < 0) {
            AsdFile_NotifyClose();                       // 0x0015CF98 / 0x0015CFC8
        }
        return;
    }

    // 0x0015CF68..0x0015CF84
    AsdSound_GetTableEntry(0);
    path_object.status = 0x64;
    job->state = 1;
    Result_Value(&file.handle);
    return;

success:
    // 0x0015CCD4..0x0015CD54
    if ((job->flags & 1) != 0 && job->out != nullptr) {
        *job->out = static_cast<u32>(reinterpret_cast<std::uintptr_t>(job->buffer));
    }
    if (job->callback != nullptr) {
        job->callback(job->buffer, job->callback_arg0, job->size);
    }
    job->state = 3;

    if (job->notify != nullptr) {
        // 0x0015CD18 and 0x0015CD24: the listing writes ready first, then
        // loads [r4+0x24]! (write-back) and stores it at [r4+0x90], i.e. at
        // the original +0xB4 notify object's +0x08 field.
        job->notify->ready = 1;
        job->notify->size = job->size;
    }

    AocFile_Close(&file.handle);
    return;
}

// ---------------------------------------------------------------------------
// aocMain (0x001B0B00)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001b0b00, 408)
void* aocMain_func_001b0b00(u32 mode)
{
    // 0x001B0B0C..0x001B0B50: allocate and clear the 0x20-byte state.
    AocMain* state = static_cast<AocMain*>(AsdMem_Alloc(0x100, 0x100, 0, 0x20, 1));
    g_AocMain = state;
    state->flag_18 = 0;
    state->flag_19 = 0;
    state->field_1c = 0;
    state->flag_1a = 0;

    if (mode == 0) {
        // 0x001B0B5C..0x001B0B74: enable both display latches.
        state->flag_19 = 1;
        AocMode_Set(0, 0xff);
        AocMode_Set(1, 0xff);
    }

    // 0x001B0B78..0x001B0BA0: "AOCMainProc" node with three stack arguments.
    // The listing pushes [sp]=0x001B4EE8 and [sp+4]=0x0020EB80.
    state->main_task = AsdTask_CreateCalc("AOCMainProc", 2, 0, 0,
                                      reinterpret_cast<void (*)(void*)>(0x001b4ee8),
                                      0x0020eb80u,
                                      static_cast<u32>(reinterpret_cast<std::uintptr_t>(state)));

    // 0x001B0BA0..0x001B0BC4: top-left and top-right draw tasks.
    AsdTask_CreateDraw("AOCDrawUp L", 0x7d, 1, 0,
                       reinterpret_cast<void (*)(void*)>(0x001e4618), 0,
                       static_cast<u32>(reinterpret_cast<std::uintptr_t>(state)),
                       state->main_task);
    AsdTask_CreateDraw("AOCDrawUp R", 0xdb, 1, 0,
                       reinterpret_cast<void (*)(void*)>(0x001e4618), 0,
                       static_cast<u32>(reinterpret_cast<std::uintptr_t>(state)),
                       state->main_task);

    // 0x001B0BF0..0x001B0C18: bottom draw task, this one is retained and is
    // the return value (`r0` at 0x001B0C18..0x001B0C20).
    state->draw_task = AsdTask_CreateDraw("AOCDrawDown", 0xe7, 1, 0,
                                          reinterpret_cast<void (*)(void*)>(0x0020ebc8), 0,
                                          static_cast<u32>(reinterpret_cast<std::uintptr_t>(state)),
                                          state->main_task);
    return state->draw_task;
}

// ---------------------------------------------------------------------------
// aocBootProcess (0x00224AE0)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00224ae0, 276)
void* aocBootProcess_func_00224ae0()
{
    // 0x00224AE8..0x00224AF4: one-time 0x5F4-byte state.
    if (g_AocBootProcess.process == nullptr) {
        g_AocBootProcess.process = static_cast<AocBootProcess*>(
            AsdMem_Alloc(0x100, 0x100, 0, 0x5f4, 1));
    }

    AocBootProcess* process = g_AocBootProcess.process;
    g_AocBootProcess.handle = 0;                         // 0x00224B28
    process->flag_08 = 0;                                // 0x00224B2C
    process->flag_09 = 0;                                // 0x00224B34
    AocBoot_InitCalc(process->calc);                     // 0x00224B3C
    process->field_5f0 = 0;                              // 0x00224B44

    // 0x00224B40..0x00224B70: "aocBoot CALC" node.  The listing's stack
    // arguments are [sp]=0x001B4BBC and [sp+4]=0x0020EB58.
    process->task = AsdTask_CreateCalc("aocBoot CALC", 2, 0, 0,
                                   reinterpret_cast<void (*)(void*)>(0x001b4bbc),
                                   0x0020eb58u, 0);

    // 0x00224B74..0x00224B84: clear the low GPU bits.  The listing returns
    // `*(g_AocBootProcess.process)`, i.e. the task pointer.
    g_AocAppletState->flags_754 &= ~0x70u;
    return process->task;
}

// ---------------------------------------------------------------------------
// aocApplication (0x0038B384 / 0x0038B510)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0038b384, 236)
void aocApplication_func_0038b384(AocApplication* app)
{
    // 0x0038B390..0x0038B3A4: tear down the previous texture handle.
    if (app->texture_handle != nullptr) {
        AocTexture_Destroy(app->texture_handle);
        Aoc_ReleaseGlobal();
        app->texture_handle = nullptr;
    }

    // 0x0038B3A8..0x0038B3C0: free the previous 0x20000-byte buffer.
    if (app->texture_buffer != nullptr) {
        AsdMem_Free(app->texture_buffer);
        app->texture_buffer = nullptr;
    }

    // 0x0038B3C4..0x0038B3F4: allocate and clear the new buffer.
    app->texture_buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, 0x20000, 1);
    AsdWork_Zero(app->texture_buffer, 0x20000);

    if (app->texture_buffer == nullptr) {
        AsdFile_NotifyClose();                                // 0x0038B434
        return;
    }

    // 0x0038B404..0x0038B428: create the texture object.  The listing keeps
    // the new 0x10 object in r0 and passes it as the first argument.
    void* texture = AsdMemory_func_002c23f8(0x10);
    if (texture != nullptr) {
        texture = AocTexture_Create(texture, app->source_handle,
                                    app->texture_buffer, 0x20000);
    }
    app->texture_handle = texture;                       // 0x0038B428
}

// DECOMP_FUNC(0x0038b510, 240)
void aocApplication_func_0038b510(AocApplication* app)
{
    // 0x0038B51C..0x0038B530: tear down the previous archive handle.
    if (app->archive_handle != nullptr) {
        AocArchive_Destroy(app->archive_handle);
        Aoc_ReleaseGlobal();
        app->archive_handle = nullptr;
    }

    // 0x0038B534..0x0038B54C: free the previous 0x20000-byte buffer.
    if (app->archive_buffer != nullptr) {
        AsdMem_Free(app->archive_buffer);
        app->archive_buffer = nullptr;
    }

    // 0x0038B550..0x0038B580: allocate and clear the new buffer.
    app->archive_buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, 0x20000, 1);
    AsdWork_Zero(app->archive_buffer, 0x20000);

    if (app->archive_buffer == nullptr) {
        AsdFile_NotifyClose();                                // 0x0038B5C0
        return;
    }

    // 0x0038B590..0x0038B5B4: create the archive object with the new 0x10
    // object as the first argument.
    void* archive = AsdMemory_func_002c23f8(0x10);
    if (archive != nullptr) {
        archive = AocArchive_Create(archive, app->source_handle,
                                    app->archive_buffer, 0x20000);
    }
    app->archive_handle = archive;                       // 0x0038B5B4
}

// ---------------------------------------------------------------------------
// aocFileContent (0x0038BD00)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0038bd00, 408)
void aocFileContent_func_0038bd00(AocFileContentState* state,
                                  AocFileContent* content, u32 index)
{
    // 0x0038BD08..0x0038BD28: drop the previous mount buffer.
    if (content->buffer != nullptr) {
        AsdMem_Free(content->buffer);
        content->buffer = nullptr;
    }

    // 0x0038BD2C..0x0038BD44: reset the status and the four-word object at
    // state+4 (0x002BB09C writes its magic/zero head).
    state->status = 0;
    AsdFile_Pair_Init(&state->result[0]);                // 0x0038BD38
    state->field_0c = 0;                                 // 0x0038BD3C
    state->field_10 = 0;                                 // 0x0038BD44

    // 0x0038BD48..0x0038BD60: zero the local result object.
    SdkResult init_result{};
    Result_Construct(&init_result, 0);                   // 0x0038BD50
    state->result[0] = init_result.words[0];
    state->result[1] = init_result.words[1];

    // 0x0038BD68..0x0038BD74: query the archive size into content->size.
    const u32 size_result = AocContent_GetSize(&content->size, 0x0e5c, index,
                                               2, 2, 0);
    SdkResult size_status{};
    Result_Construct(&size_status, size_result);         // 0x0038BD80
    if (static_cast<s32>(Result_Value(&size_status)) < 0) {
        // 0x0038BD9C..0x0038BDF8: failure path.
        AsdSound_GetTableEntry(0);
        state->result[0] = size_status.words[0];
        state->result[1] = size_status.words[1];
        state->status = 0x64;

        if (Result_Value(&size_status) != 0xC9413891u) {
            if (AocApplet_Check98(&g_AocAppletState->field_98) != 0) {
                g_AocAppletState->flags_754 &= ~0x10000u;
                state->status = 0xC8;
            }
        }
        return;
    }

    // 0x0038BE04..0x0038BE48: allocate the mount buffer and format "aoc%d:".
    content->buffer = AsdMem_AllocAlign(0x100, 0x100, 0, content->size, 1);
    AsdWork_Zero(content->buffer, content->size);
    UiText_Format(content->mount, "aoc%d:", index);
}

// ---------------------------------------------------------------------------
// aocTexCtrl (0x00234CA8 / 0x002A465C / 0x003936E8 / 0x00393838)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00234ca8, 164)
void aocTexCtrl_func_00234ca8(AocTexCtrl* ctrl)
{
    // 0x00234CB0..0x00234CB8: already initialised.
    if (ctrl->state != nullptr) {
        return;
    }

    // 0x00234CBC..0x00234D00: allocate and clear the 0x18-byte state.
    AocTexCtrlState* state = static_cast<AocTexCtrlState*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x18, 1));
    ctrl->state = state;
    u8* raw = reinterpret_cast<u8*>(state);
    for (u32 offset = 0; offset < 0x18; offset += 4) {
        *reinterpret_cast<u32*>(raw + offset) = 0;
    }

    // 0x00234D04..0x00234D0C: tail call aocTexCtrl_func_003936e8(ctrl).
    aocTexCtrl_func_003936e8(ctrl);
}

// DECOMP_FUNC(0x002a465c, 460)
void* aocTexCtrl_func_002a465c(AocTMSpr* sprite, u32 flags, u32 size)
{
    // 0x002A466C..0x002A4688: only the 0x10/0x20/0x30 high nibbles are handled.
    const u32 type = sprite->type & 0xf0;
    if (type != 0x10 && type != 0x20 && type != 0x30) {
        return sprite;
    }

    // 0x002A468C..0x002A4698: vtable[?] returns the required work size.
    const u32 work_size = UiTMSpr_func_0014f3fc(sprite);
    if (work_size == 0) {
        return sprite;
    }

    void* buffer;
    if ((flags & 1) != 0) {
        if ((flags & 2) != 0) {
            // 0x002A46B8..0x002A46E0
            buffer = AsdWork_Alloc2(0x10000, 0x100, 0, work_size, size, 0);
        } else {
            // 0x002A46E8..0x002A470C
            buffer = AsdWork_Alloc2(0x10000, 0x100, 0, work_size, size, 1);
        }
    } else {
        if ((flags & 2) != 0) {
            // 0x002A4720..0x002A4748
            buffer = AsdWork_Alloc2(0x100, 0x100, 0, work_size, size, 0);
        } else {
            // 0x002A4754..0x002A4778
            buffer = AsdWork_Alloc2(0x100, 0x100, 0, work_size, size, 1);
        }
    }

    // 0x002A477C..0x002A47D0: pick the upload routine from the type nibble.
    switch (type) {
    case 0x10:
        UiTMSpr_func_0014f070(sprite, buffer);
        break;
    case 0x20:
        UiTMSpr_func_0014f30c(sprite, buffer);
        break;
    case 0x30:
        UiTMSpr_func_0014f1cc(sprite, buffer);
        break;
    default:
        break;
    }

    AsdMem_Free(sprite);                                 // 0x002A47D8
    return buffer;
}

// DECOMP_FUNC(0x003936e8, 336)
u32 aocTexCtrl_func_003936e8(AocTexCtrl* ctrl)
{
    u8* block = ctrl->source;                            // 0x003936F0
    AocTexBlock* header = reinterpret_cast<AocTexBlock*>(block);

    // 0x003936F4..0x00393724: resolve the four bases.
    u8* entry_base = block + header->entry_offset;       // r2
    u8* object_base = block + header->base_offset;       // r5
    u8* stream_base = block + header->stream_offset;     // r6
    u8* stream_data = block + header->stream_data_offset;// r3

    // 0x0039372C..0x00393758: turn each +0x0C index into a 0x50-byte pointer.
    if (header->entry_count > 0) {
        u8* entry = entry_base;
        for (s32 i = 0; i < header->entry_count; ++i) {
            u32 value = *reinterpret_cast<u32*>(entry + 0x0c);
            if (value == 0xffffffffu) {
                *reinterpret_cast<u32*>(entry + 0x0c) = 0;
            } else {
                u8* target = object_base + (value * 5) * 0x10;
                *reinterpret_cast<void**>(entry + 0x0c) = target;
            }
            entry += 0x14;
        }
    }

    // 0x0039375C..0x0039379C: second array; each record is 0x10 bytes
    // (`str ip,[r1,#8]!` then `add r1,r1,#8`) and grows into the 0x14-byte
    // table and the stream data base.
    if (header->stream_count > 0) {
        u8* stream = stream_base;
        for (s32 i = 0; i < header->stream_count; ++i) {
            u32 index = *reinterpret_cast<u32*>(stream);
            *reinterpret_cast<u8**>(stream) = entry_base + (index * 5) * 4;
            u32 offset = *reinterpret_cast<u32*>(stream + 8);
            *reinterpret_cast<u8**>(stream + 8) = stream_data + offset;
            stream += 0x10;
        }
    }

    // 0x003937A0..0x003937E8: 0x2C-byte output descriptor + node array.
    AocTexOutput* output = static_cast<AocTexOutput*>(AsdMem_AllocFlags(0x2c, 0));
    if (header->stream_count <= 0) {
        output->nodes = nullptr;
    } else {
        output->nodes = AsdMem_AllocFlags(
            static_cast<u32>(header->stream_count) * 0x20, 0);
    }

    // 0x003937EC..0x00393818: seed each 0x20-byte node with owner/source.
    if (header->stream_count > 0) {
        AocTexOutputNode* node = static_cast<AocTexOutputNode*>(output->nodes);
        u8* stream = stream_base;
        for (s32 i = 0; i < header->stream_count; ++i) {
            node->owner = output;
            node->source = stream;
            node += 1;
            stream += 0x10;
        }
    }

    output->header = block;                              // 0x0039381C
    output->header_dup = block;                          // 0x00393820
    ctrl->state->block = output;                         // 0x00393828
    return 1;                                            // 0x0039382C
}

// DECOMP_FUNC(0x00393838, 456)
void aocTexCtrl_func_00393838(AocTexCtrl* ctrl, void** source)
{
    // 0x00393844..0x0039384C: already initialised.
    if (ctrl->state != nullptr) {
        return;
    }

    // 0x00393850..0x0039387C: replace the state with an 8-byte owner object.
    u8* src = static_cast<u8*>(*source);
    void** owner = static_cast<void**>(AsdMem_Alloc(0x100, 0x100, 0, 8, 1));
    ctrl->state = reinterpret_cast<AocTexCtrlState*>(owner);

    // 0x00393880..0x003938CC: copy the 0x40-byte header block; owner[0]
    // points at that copy.
    u8* header = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, 0x40, 1));
    owner[0] = header;
    for (u32 i = 0; i < 0x40; i += 4) {
        *reinterpret_cast<u32*>(header + i) =
            *reinterpret_cast<const u32*>(src + i);
    }
    src += 0x40;

    // 0x003938D4..0x003938E4: header[0x20] is the entry count.
    const s32 count = *reinterpret_cast<s32*>(header + 0x20);
    if (count <= 0) {
        return;
    }

    // 0x003938E8..0x00393964: build one 0x14-byte entry per descriptor.
    AocTexListEntry* previous = nullptr;
    s32 built = 0;
    while (built < count) {
        AocTexListEntry* entry = static_cast<AocTexListEntry*>(
            AsdMem_Alloc(0x100, 0x100, 0, 0x14, 1));
        entry->value = src[0];                          // 0x00393918
        entry->count = src[4];                          // 0x00393924
        entry->type = src[8];                           // 0x0039392C

        if (entry->count <= 0) {
            entry->data = nullptr;
        } else {
            // 0x00393938..0x00393960: count * 0x14 bytes.
            entry->data = AsdMem_Alloc(0x100, 0x100, 0,
                                       entry->count * 0x14, 1);
        }

        if (entry->count > 0) {
            AsdMem_CopyLarge(entry->data, src + 0x0c,
                             entry->count * 0x14);      // 0x00393984
        }

        // 0x00393988..0x003939B8: link and advance by the variable record.
        if (previous == nullptr) {
            owner[1] = entry;                           // 0x003939A0
        } else {
            previous->next = entry;                     // 0x003939A8
        }
        previous = entry;
        ++built;
        src += 0x0c + entry->count * 0x14;
    }
}

} // namespace smt4::engine
