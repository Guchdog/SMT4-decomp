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
// DECOMP_FUNC(0x001b0b00, 408)


// ---------------------------------------------------------------------------
// aocMain (0x001B0B00)
// ---------------------------------------------------------------------------

//
__attribute__((naked)) void* aocMain_func_001b0b00(u32)
{
    asm volatile(
        ".word 0xE92D41F0\n"
        ".word 0xE1A05000\n"
        ".word 0xE24DD010\n"
        ".word 0xE3A01095\n"
        ".word 0xE28F0F43\n"
        ".word 0xE1A00000\n"
        ".word 0xE3A08001\n"
        ".word 0xE3A01C01\n"
        ".word 0xE3A03020\n"
        ".word 0xE3A02000\n"
        ".word 0xE1A00001\n"
        ".word 0xE58D8000\n"
        ".word 0xEB045013\n" // AsdMem_Alloc (0x002C4B84)
        ".word 0xE59F7118\n"
        ".word 0xE3A06000\n"
        ".word 0xE3550000\n"
        ".word 0xE1A04000\n"
        ".word 0xE5870000\n"
        ".word 0xE5C06018\n"
        ".word 0xE5C06019\n"
        ".word 0xE580601C\n"
        ".word 0xE5C0601A\n"
        ".word 0x1A000006\n"
        ".word 0xE3A010FF\n"
        ".word 0xE3A00000\n"
        ".word 0xE5C48019\n"
        ".word 0xEB0348BF\n" // AocMode_Set (0x00282E6C)
        ".word 0xE3A010FF\n"
        ".word 0xE3A00001\n"
        ".word 0xEB0348BC\n" // AocMode_Set (0x00282E6C)
        ".word 0xE59F10D8\n"
        ".word 0xE59F00D8\n"
        ".word 0xE5972000\n"
        ".word 0xE3A03000\n"
        ".word 0xE88D0007\n"
        ".word 0xE1A02003\n"
        ".word 0xE3A01002\n"
        ".word 0xE28F00C4\n"
        ".word 0xEB045376\n" // AsdTask_CreateCalc (0x002C5978)
        ".word 0xE5840000\n"
        ".word 0xE5971000\n"
        ".word 0xE59F50C0\n"
        ".word 0xE58D000C\n"
        ".word 0xE58D1008\n"
        ".word 0xE3A03000\n"
        ".word 0xE3A02001\n"
        ".word 0xE3A0107D\n"
        ".word 0xE28F00AC\n"
        ".word 0xE88D0060\n"
        ".word 0xEB04500D\n" // AsdTask_CreateDraw (0x002C4C00)
        ".word 0xE5940000\n"
        ".word 0xE5971000\n"
        ".word 0xE3A03000\n"
        ".word 0xE58D000C\n"
        ".word 0xE58D1008\n"
        ".word 0xE3A02001\n"
        ".word 0xE3A010DB\n"
        ".word 0xE28F0090\n"
        ".word 0xE88D0060\n"
        ".word 0xEB045003\n" // AsdTask_CreateDraw (0x002C4C00)
        ".word 0xE59F2090\n"
        ".word 0xE5941000\n"
        ".word 0xE5970000\n"
        ".word 0xE88D0044\n"
        ".word 0xE3A03000\n"
        ".word 0xE1CD00F8\n"
        ".word 0xE3A02001\n"
        ".word 0xE3A010E7\n"
        ".word 0xE28F0074\n"
        ".word 0xEB044FF9\n" // AsdTask_CreateDraw (0x002C4C00)
        ".word 0xE584000C\n"
        ".word 0xE28DD010\n"
        ".word 0xE8BD81F0\n"
        ".word 0x535C3A63\n"
        ".word 0x5C34544D\n"
        ".word 0x36445258\n"
        ".word 0x735C3638\n"
        ".word 0x34736464\n"
        ".word 0x6F72705C\n"
        ".word 0x6D617267\n"
        ".word 0x6464615C\n"
        ".word 0x615C6E6F\n"
        ".word 0x614D636F\n"
        ".word 0x632E6E69\n"
        ".word 0x00007070\n"
        ".word 0x00433048\n"
        ".word 0x0020EB80\n"
        ".word 0x001B4EE8\n"
        ".word 0x4D434F41\n"
        ".word 0x506E6961\n"
        ".word 0x00636F72\n"
        ".word 0x001E4618\n"
        ".word 0x44434F41\n"
        ".word 0x55776172\n"
        ".word 0x004C2070\n"
        ".word 0x44434F41\n"
        ".word 0x55776172\n"
        ".word 0x00522070\n"
        ".word 0x0020EBC8\n"
        ".word 0x44434F41\n"
        ".word 0x44776172\n"
        ".word 0x006E776F\n");
}
// DECOMP_FUNC(0x00224ae0, 276)


// ---------------------------------------------------------------------------
// aocBootProcess (0x00224AE0)
// ---------------------------------------------------------------------------

//
__attribute__((naked)) void* aocBootProcess_func_00224ae0()
{
    asm volatile(
        ".word 0xE92D4070\n"
        ".word 0xE24DD010\n"
        ".word 0xE59F60A4\n"
        ".word 0xE5960000\n"
        ".word 0xE3500000\n"
        ".word 0x1A00000A\n"
        ".word 0xE59F1098\n"
        ".word 0xE28F0098\n"
        ".word 0xE1A00000\n"
        ".word 0xE3A00001\n"
        ".word 0xE3A01C01\n"
        ".word 0xE58D0000\n"
        ".word 0xE59F30BC\n"
        ".word 0xE3A02000\n"
        ".word 0xE1A00001\n"
        ".word 0xEB028018\n" // AsdMem_Alloc (0x002C4B84)
        ".word 0xE5860000\n"
        ".word 0xE3A05000\n"
        ".word 0xE5865004\n"
        ".word 0xE5C05008\n"
        ".word 0xE1A04000\n"
        ".word 0xE5C05009\n"
        ".word 0xE280000C\n"
        ".word 0xEB0257E2\n" // AocBoot_InitCalc (0x002BAACC)
        ".word 0xE59F1094\n"
        ".word 0xE58455F0\n"
        ".word 0xE59F0088\n"
        ".word 0xE28D4004\n"
        ".word 0xE58D1000\n"
        ".word 0xE3A03000\n"
        ".word 0xE8840021\n"
        ".word 0xE1A02003\n"
        ".word 0xE3A01002\n"
        ".word 0xE28F0074\n"
        ".word 0xEB028382\n" // AsdTask_CreateCalc.
        ".word 0xE5961000\n"
        ".word 0xE5810000\n"
        ".word 0xE59F0074\n"
        ".word 0xE5900000\n"
        ".word 0xE5902754\n"
        ".word 0xE3C22070\n"
        ".word 0xE5802754\n"
        ".word 0xE5910000\n"
        ".word 0xE28DD010\n"
        ".word 0xE8BD8070\n"
        ".word 0x00432FE0\n" // g_AocBootProcess (process/global state).
        ".word 0x0000011E\n" // Original line marker.
        ".word 0x535C3A63\n"
        ".word 0x5C34544D\n"
        ".word 0x36445258\n"
        ".word 0x735C3638\n"
        ".word 0x34736464\n"
        ".word 0x6F72705C\n"
        ".word 0x6D617267\n"
        ".word 0x6464615C\n"
        ".word 0x615C6E6F\n"
        ".word 0x6F42636F\n"
        ".word 0x7250746F\n"
        ".word 0x7365636F\n"
        ".word 0x70632E73\n"
        ".word 0x00000070\n"
        ".word 0x000005F4\n"
        ".word 0x0020EB58\n"
        ".word 0x001B4BBC\n"
        ".word 0x42636F61\n"
        ".word 0x20746F6F\n"
        ".word 0x434C4143\n"
        ".word 0x00000000\n"
        ".word 0x00432FC8\n"); // g_AocAppletState literal.
}
// DECOMP_FUNC(0x0038b384, 236)


// ---------------------------------------------------------------------------
// aocApplication (0x0038B384 / 0x0038B510)
// ---------------------------------------------------------------------------

//
__attribute__((naked)) void aocApplication_func_0038b384(AocApplication*)
{
    asm volatile(
        ".word 0xE92D40F8\n"
        ".word 0xE1A04000\n"
        ".word 0xE3A06000\n"
        ".word 0xE59005A8\n"
        ".word 0xE3500000\n"
        ".word 0x0A000002\n"
        ".word 0xEBFF1F5E\n" // AocTexture_Destroy (0x0035311C)
        ".word 0xEBFC9C5E\n" // Aoc_ReleaseGlobal (0x002B2520)
        ".word 0xE58465A8\n"
        ".word 0xE59405AC\n"
        ".word 0xE2845B01\n"
        ".word 0xE2855F6B\n"
        ".word 0xE3500000\n"
        ".word 0x0A000001\n"
        ".word 0xEBFCE3E7\n" // AsdMem_Free (0x002C4360)
        ".word 0xE5856000\n"
        ".word 0xE3A01F5A\n"
        ".word 0xE28F0068\n"
        ".word 0xE1A00000\n"
        ".word 0xE3A00001\n"
        ".word 0xE58D0000\n"
        ".word 0xE3A03802\n"
        ".word 0xE3A02000\n"
        ".word 0xE3A01C01\n"
        ".word 0xE3A00801\n"
        ".word 0xEBFCE840\n" // AsdMem_AllocAlign (0x002C54F0)
        ".word 0xE3A01802\n"
        ".word 0xE58405AC\n"
        ".word 0xEBFCE1D3\n" // AsdWork_Zero.
        ".word 0xE5950000\n"
        ".word 0xE3500000\n"
        ".word 0x0A00000A\n"
        ".word 0xE3A00010\n"
        ".word 0xEBFCDBFA\n" // AsdMemory_func_002c23f8.
        ".word 0xE3500000\n"
        ".word 0xE320F000\n"
        ".word 0x0A000003\n"
        ".word 0xE5941080\n"
        ".word 0xE59425AC\n"
        ".word 0xE3A03802\n"
        ".word 0xEBFF1F33\n" // AocTexture_Create (0x003530F8)
        ".word 0xE58405A8\n"
        ".word 0xE8BD80F8\n"
        ".word 0xE8BD40F8\n"
        ".word 0xEAFCC683\n" // AsdFile_NotifyClose.
        ".word 0x535C3A63\n"
        ".word 0x5C34544D\n"
        ".word 0x36445258\n"
        ".word 0x735C3638\n"
        ".word 0x34736464\n"
        ".word 0x6F72705C\n"
        ".word 0x6D617267\n"
        ".word 0x6464615C\n"
        ".word 0x615C6E6F\n"
        ".word 0x7041636F\n"
        ".word 0x63696C70\n"
        ".word 0x6F697461\n"
        ".word 0x70632E6E\n"
        ".word 0x00000070\n"); // Original source-path literal.
}
// DECOMP_FUNC(0x0038b510, 240)


//
__attribute__((naked)) void aocApplication_func_0038b510(AocApplication*)
{
    asm volatile(
        ".word 0xE92D40F8\n"
        ".word 0xE1A04000\n"
        ".word 0xE3A06000\n"
        ".word 0xE59005B0\n"
        ".word 0xE3500000\n"
        ".word 0x0A000002\n"
        ".word 0xEBFABB88\n" // AocArchive_Destroy (0x0023A350)
        ".word 0xEBFC9BFB\n" // Aoc_ReleaseGlobal (0x002B2520)
        ".word 0xE58465B0\n"
        ".word 0xE59405B4\n"
        ".word 0xE2845B01\n"
        ".word 0xE2855F6D\n"
        ".word 0xE3500000\n"
        ".word 0x0A000001\n"
        ".word 0xEBFCE384\n" // AsdMem_Free (0x002C4360)
        ".word 0xE5856000\n"
        ".word 0xE59F106C\n"
        ".word 0xE28F006C\n"
        ".word 0xE1A00000\n"
        ".word 0xE3A00001\n"
        ".word 0xE58D0000\n"
        ".word 0xE3A03802\n"
        ".word 0xE3A02000\n"
        ".word 0xE3A01C01\n"
        ".word 0xE3A00801\n"
        ".word 0xEBFCE7DD\n" // AsdMem_AllocAlign (0x002C54F0)
        ".word 0xE3A01802\n"
        ".word 0xE58405B4\n"
        ".word 0xEBFCE170\n" // AsdWork_Zero.
        ".word 0xE5950000\n"
        ".word 0xE3500000\n"
        ".word 0x0A00000A\n"
        ".word 0xE3A00010\n"
        ".word 0xEBFCDB97\n" // AsdMemory_func_002c23f8.
        ".word 0xE3500000\n"
        ".word 0xE320F000\n"
        ".word 0x0A000003\n"
        ".word 0xE5941080\n"
        ".word 0xE59425B4\n"
        ".word 0xE3A03802\n"
        ".word 0xEBFF1CE6\n" // AocArchive_Create (0x00352950)
        ".word 0xE58405B0\n"
        ".word 0xE8BD80F8\n"
        ".word 0xE8BD40F8\n"
        ".word 0xEAFCC620\n" // AsdFile_NotifyClose.
        ".word 0x00000187\n" // Original line marker.
        ".word 0x535C3A63\n"
        ".word 0x5C34544D\n"
        ".word 0x36445258\n"
        ".word 0x735C3638\n"
        ".word 0x34736464\n"
        ".word 0x6F72705C\n"
        ".word 0x6D617267\n"
        ".word 0x6464615C\n"
        ".word 0x615C6E6F\n"
        ".word 0x7041636F\n"
        ".word 0x63696C70\n"
        ".word 0x6F697461\n"
        ".word 0x70632E6E\n"
        ".word 0x00000070\n"); // Original source-path literal.
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
// DECOMP_FUNC(0x00234ca8, 164)


// ---------------------------------------------------------------------------
// aocTexCtrl (0x00234CA8 / 0x002A465C / 0x003936E8 / 0x00393838)
// ---------------------------------------------------------------------------

//
__attribute__((naked)) void aocTexCtrl_func_00234ca8(AocTexCtrl*)
{
    asm volatile(
        ".word 0xE92D4038\n"
        ".word 0xE1A04000\n"
        ".word 0xE5900004\n"
        ".word 0xE3500000\n"
        ".word 0x1A000014\n"
        ".word 0xE3A01FDB\n"
        ".word 0xE28F004C\n"
        ".word 0xE1A00000\n"
        ".word 0xE3A00001\n"
        ".word 0xE3A01C01\n"
        ".word 0xE58D0000\n"
        ".word 0xE3A03018\n"
        ".word 0xE3A02000\n"
        ".word 0xE1A00001\n"
        ".word 0xEB023FA7\n" // AsdMem_Alloc (0x002C4B84)
        ".word 0xE3A01000\n"
        ".word 0xE5840004\n"
        ".word 0xE5801000\n"
        ".word 0xE5801004\n"
        ".word 0xE5801008\n"
        ".word 0xE580100C\n"
        ".word 0xE5801010\n"
        ".word 0xE5801014\n" // Explicit six-word clear of the 0x18-byte state.
        ".word 0xE1A00004\n"
        ".word 0xE8BD4038\n"
        ".word 0xEA057A75\n" // Tail branch to aocTexCtrl_func_003936e8 (0x003936E8).
        ".word 0xE8BD8038\n"
        ".word 0x535C3A63\n"
        ".word 0x5C34544D\n"
        ".word 0x36445258\n"
        ".word 0x735C3638\n"
        ".word 0x34736464\n"
        ".word 0x6F72705C\n"
        ".word 0x6D617267\n"
        ".word 0x6464615C\n"
        ".word 0x735C6E6F\n"
        ".word 0x615C7379\n"
        ".word 0x6554636F\n"
        ".word 0x72744378\n"
        ".word 0x70632E6C\n"
        ".word 0x00000070\n"); // Original source-path literal, including terminator.
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


//
__attribute__((naked)) u32 aocTexCtrl_func_003936e8(AocTexCtrl*)
{
    asm volatile(
        ".word 0xE92D41F0\n"
        ".word 0xE1A07000\n"
        ".word 0xE5904000\n"
        ".word 0xE3A08000\n"
        ".word 0xE1A01008\n"
        ".word 0xE284201C\n"
        ".word 0xE5940014\n"
        ".word 0xE8921004\n"
        ".word 0xE594302C\n"
        ".word 0xE5946024\n"
        ".word 0xE0822004\n"
        ".word 0xE0805004\n"
        ".word 0xE35C0000\n"
        ".word 0xE1A00002\n"
        ".word 0xE0866004\n"
        ".word 0xE0833004\n"
        ".word 0xDA00000B\n"
        ".word 0xE590C00C\n"
        ".word 0xE37C0001\n"
        ".word 0x0580800C\n"
        ".word 0x0A000002\n"
        ".word 0xE08CC10C\n"
        ".word 0xE085C20C\n"
        ".word 0xE580C00C\n"
        ".word 0xE594C020\n"
        ".word 0xE2811001\n"
        ".word 0xE2800014\n"
        ".word 0xE15C0001\n"
        ".word 0xCAFFFFF3\n"
        ".word 0xE594C028\n"
        ".word 0xE1A01006\n"
        ".word 0xE3A00000\n"
        ".word 0xE35C0000\n"
        ".word 0xDA00000B\n"
        ".word 0xE591C000\n"
        ".word 0xE2800001\n"
        ".word 0xE08CC10C\n"
        ".word 0xE082C10C\n"
        ".word 0xE581C000\n"
        ".word 0xE591C008\n"
        ".word 0xE08CC003\n"
        ".word 0xE5A1C008\n"
        ".word 0xE594C028\n"
        ".word 0xE2811008\n"
        ".word 0xE15C0000\n"
        ".word 0xCAFFFFF3\n"
        ".word 0xE59F008C\n"
        ".word 0xE3A0103E\n"
        ".word 0xE1A00000\n"
        ".word 0xE3A01000\n"
        ".word 0xE3A0002C\n"
        ".word 0xEBFC8FCB\n" // AsdMem_AllocFlags (0x002B76E8)
        ".word 0xE1A05000\n"
        ".word 0xE5940028\n"
        ".word 0xE3500000\n"
        ".word 0xD5858000\n"
        ".word 0xDA000007\n"
        ".word 0xE59F0060\n"
        ".word 0xE3A01041\n"
        ".word 0xE1A00000\n"
        ".word 0xE5940028\n"
        ".word 0xE3A01000\n"
        ".word 0xE1A00280\n"
        ".word 0xEBFC8FBF\n" // AsdMem_AllocFlags (0x002B76E8)
        ".word 0xE5850000\n"
        ".word 0xE5942028\n"
        ".word 0xE5950000\n"
        ".word 0xE3A01000\n"
        ".word 0xE3520000\n"
        ".word 0xDA000006\n"
        ".word 0xE8800060\n"
        ".word 0xE2811001\n"
        ".word 0xE5942028\n"
        ".word 0xE2800020\n"
        ".word 0xE2866010\n"
        ".word 0xE1520001\n"
        ".word 0xCAFFFFF8\n"
        ".word 0xE5854004\n"
        ".word 0xE5854008\n"
        ".word 0xE5970004\n"
        ".word 0xE5805000\n"
        ".word 0xE3A00001\n"
        ".word 0xE8BD81F0\n"
        ".word 0x003FF78C\n");
}
// DECOMP_FUNC(0x00393838, 456)


//
__attribute__((naked)) void aocTexCtrl_func_00393838(AocTexCtrl*, void**)
{
    asm volatile(
        ".word 0xE92D4FF8\n"
        ".word 0xE1A04001\n"
        ".word 0xE1A0B000\n"
        ".word 0xE5900004\n"
        ".word 0xE3500000\n"
        ".word 0x1A00005A\n"
        ".word 0xE5945000\n"
        ".word 0xE59F1164\n"
        ".word 0xE28F0F59\n"
        ".word 0xE1A00000\n"
        ".word 0xE3A0A001\n"
        ".word 0xE3A01C01\n"
        ".word 0xE3A03008\n"
        ".word 0xE3A02000\n"
        ".word 0xE1A00001\n"
        ".word 0xE58DA000\n"
        ".word 0xEBFCC4C1\n" // AsdMem_Alloc (0x002C4B84)
        ".word 0xE58B0004\n"
        ".word 0xE3A01FE2\n"
        ".word 0xE28F0F4E\n"
        ".word 0xE1A00000\n"
        ".word 0xE3A01C01\n"
        ".word 0xE3A03040\n"
        ".word 0xE3A02000\n"
        ".word 0xE1A00001\n"
        ".word 0xE58DA000\n"
        ".word 0xEBFCC4B7\n" // AsdMem_Alloc (0x002C4B84)
        ".word 0xE59B1004\n"
        ".word 0xE3A07000\n"
        ".word 0xE1A06007\n"
        ".word 0xE5810000\n"
        ".word 0xEC950A08\n"
        ".word 0xE2855020\n"
        ".word 0xEC800A08\n"
        ".word 0xE2800020\n"
        ".word 0xEC950A08\n"
        ".word 0xEC800A08\n"
        ".word 0xE59B1004\n"
        ".word 0xE5940000\n"
        ".word 0xE5919000\n"
        ".word 0xE2805040\n"
        ".word 0xE5991020\n"
        ".word 0xE3510000\n"
        ".word 0xDA000034\n"
        ".word 0xE59F010C\n"
        ".word 0xE3A01061\n"
        ".word 0xE1A00000\n"
        ".word 0xE3A01C01\n"
        ".word 0xE3A03014\n"
        ".word 0xE3A02000\n"
        ".word 0xE1A00001\n"
        ".word 0xE58DA000\n"
        ".word 0xEBFCC49D\n" // AsdMem_Alloc (0x002C4B84)
        ".word 0xE5D51000\n"
        ".word 0xE1A04000\n"
        ".word 0xE3A0800C\n"
        ".word 0xE5801000\n"
        ".word 0xE5D51004\n"
        ".word 0xE3510000\n"
        ".word 0xE5801004\n"
        ".word 0xE5D51008\n"
        ".word 0xE5C01008\n"
        ".word 0xD3A00000\n"
        ".word 0xDA00000A\n"
        ".word 0xE59F00BC\n"
        ".word 0xE3A0106F\n"
        ".word 0xE1A00000\n"
        ".word 0xE58DA000\n"
        ".word 0xE5940004\n"
        ".word 0xE3A01C01\n"
        ".word 0xE3A02000\n"
        ".word 0xE0800100\n"
        ".word 0xE1A03100\n"
        ".word 0xE1A00001\n"
        ".word 0xEBFCC487\n" // AsdMem_Alloc (0x002C4B84)
        ".word 0xE584000C\n"
        ".word 0xE5940004\n"
        ".word 0xE285100C\n"
        ".word 0xE3500000\n"
        ".word 0xDA000003\n"
        ".word 0xE0802100\n"
        ".word 0xE594000C\n"
        ".word 0xE1A02102\n"
        ".word 0xEBFCA573\n" // AsdMem_CopyLarge (0x002BCF58)
        ".word 0xE5940004\n"
        ".word 0xE3570000\n"
        ".word 0x059B1004\n"
        ".word 0xE2866001\n"
        ".word 0xE0800100\n"
        ".word 0xE0880100\n"
        ".word 0x05814004\n"
        ".word 0xE0855000\n"
        ".word 0x15874010\n"
        ".word 0xE5990020\n"
        ".word 0xE1A07004\n"
        ".word 0xE1500006\n"
        ".word 0xCAFFFFCA\n"
        ".word 0xE8BD8FF8\n"
        ".word 0x00000386\n"
        ".word 0x535C3A63\n"
        ".word 0x5C34544D\n"
        ".word 0x36445258\n"
        ".word 0x735C3638\n"
        ".word 0x34736464\n"
        ".word 0x6F72705C\n"
        ".word 0x6D617267\n"
        ".word 0x6464615C\n"
        ".word 0x735C6E6F\n"
        ".word 0x615C7379\n"
        ".word 0x6554636F\n"
        ".word 0x72744378\n"
        ".word 0x70632E6C\n"
        ".word 0x00000070\n"
        ".word 0x003FF78C\n");
}

} // namespace smt4::engine
