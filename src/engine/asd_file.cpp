#include "engine/asd_file.h"
#include "engine/asd_symbols.h"
#include <cstdint>

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

extern "C" {
    // AsdMemory (c:\SMT4\XRD686\AsdSDK\Source\Sys\Mem\AsdMemory.cpp)
    void  AsdMem_Zero(void* ptr, u32 size);                                 // 0x002c4b30
    void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);          // 0x002c4b84
    void* AsdMem_AllocAlign(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);     // 0x002c54f0
    void  AsdMem_Free(void* ptr);                                           // 0x002c4360

    // Ordered block tree (key = node->start) and heap block allocator.
    void  AsdMemBlockTree_Insert(void* tree, void* node);                   // 0x002c38d4
    void  AsdMemBlock_Init(void* heap, u32 start, u32 size, u32 align);     // 0x002c3b1c
    void  AsdMemBlock_InitLock(void* lock);                                 // 0x002c3b00
    void* AsdMemBlock_Alloc(void* heap, u32 size, s32 align,
                            u32 a3, u32 a4, u32 a5);                        // 0x002c3a44
    void* AsdMemBlock_Release(void* heap, void* block, u32 size);           // 0x0011bf0c
    void  AsdMemLock_Acquire(void* lock);                                   // 0x002c3aa8
    void  AsdMemLock_Release(void* lock);                                   // 0x002c3a24

    // GPU heap / VRAM bank helpers
    u32   AsdGpu_HeapStart();                                               // 0x002c3b98
    u32   AsdGpu_HeapSize();                                                // 0x002c3b88
    u32   AsdGpu_BankStart(u32 kind);                                       // 0x002c39a4
    u32   AsdGpu_BankEnd(u32 kind);                                         // 0x002c3968
    // The last four arguments are loaded with `vldmia sp,{s0,s1,s2,s3}` at
    // 0x0010a110 and stored verbatim, so they are passed as raw 32-bit words.
    void  AsdGpu_SetRegions(u32 a0, u32 a1, u32 a2, u32 a3,
                            u32 s0, u32 s1, u32 s2, u32 s3);                // 0x0010a10c

    // Work-arena allocators.  0x002c34a4 and 0x002bf798 are byte-identical
    // bodies that differ only in the arena literal their callers select.
    void* AsdWork_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 flag); // 0x002c34a4
    void* AsdWork_Alloc2(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 flag);// 0x002bf798

    // Kernel trampolines.  Each wrapper executes one `svc` and stores the
    // register left in r1 at *out (0x002c42fc / 0x002c5450 / 0x002c54d8).
    s32   AsdKernel_WaitProcessWideKey(void* out, const void* key, u32 value,
                                       u32 address, s32 timeout_lo, s32 timeout_hi); // 0x002c42fc
    s32   AsdKernel_ReleaseMutex(void* out, u32 mutex, u32 flags);          // 0x002c5450
    s32   AsdKernel_CreateMutex(void* out, u32 initially_locked, u32 flags); // 0x002c54d8
    void  AsdKernel_AbortOnFailure(s32 result);                             // 0x002c5468

    // Synchronisation primitives around 0x00465024.
    void  AsdSync_Wait(void* sync);                                         // 0x002c3628
    void  AsdSync_Set(void* sync, u32 value);                               // 0x002c541c
    void  AsdSync_Lock(void* lock);                                         // 0x00138f5c
    void  AsdThread_Sleep(u32 lo, u32 hi);                                  // 0x002bb490

    // AsdFile / nn::fs glue
    void  AsdFs_Init();                                                     // 0x0010f5b8
    u32   AsdFs_RomHeapSize(u32 a0, u32 a1, u32 a2);                        // 0x0010f674
    void  AsdFs_MountRom(u32 a0, u32 a1, void* buffer, u32 size, u32 flag); // 0x0010f6f0
    void  AsdFs_ThreadStart();                                              // 0x0010f69c
    void  AsdHeap_Init(void* heap, void* buffer, u32 size);                 // 0x002bcf34
    s32   AsdThread_Create(void* out, const void* desc, void (*entry)(),
                           void* context, u32 stack_size, u32 priority,
                           s32 processor);                                  // 0x002bce50
    s32   AsdFile_Open(void* out, const u16* path, u32 flags);              // 0x002bb8e4
    void  AsdFile_ReleaseHandle(void* handle);                              // 0x002b93f0

    // Request helpers
    int   AsdFile_HasScheme(const char* path);                              // 0x002b0614
    void* AsdFile_CreateRequestWithCallback(const char* path, u32 mode,
                                            void* callback, void* arg);     // 0x00155bbc
    u32   AsdFile_SetReadMode(smt4::engine::AsdFileRequest* req, u32 mode); // 0x002b0418
    u32   AsdFile_SetRequestSize(smt4::engine::AsdFileRequest* req, u32 size); // 0x0014e744

    // String formatting / multibyte conversion
    void  UiText_Format(char* dst, const char* fmt, ...);                   // 0x002be7fc
    int   MbsInit(void* state);                                             // 0x002b9426
    u32   MbrLen(const char* s, u32 n, void* state);                        // 0x002b9408
    u32   MbrToWc(u16* out, const char* s, u32 n, void* state);             // 0x002c6388

    // Storage back-ends (dispatch on `device`)
    u32   AsdSave_Read(u32 device, u32 file, void* buffer, u32 size);       // 0x002f5348
    u32   AsdSave_Write(u32 device, u32 file, const void* buffer, u32 size);// 0x002f5584
}

namespace {

using namespace smt4::engine;

// 0x00465010 (AsdFileGlobal::mutex) is the mutex every AsdFile critical
// section uses; the trampolines take it through a stack copy.
s32 AsdFile_AcquireMutex(u32* out_word)
{
    u32 key = g_AsdFile.mutex;
    // 0x00113d84: r0=&out, r1=&key, r2=1, r3=0, [sp]=-1, [sp+4]=-1.
    return AsdKernel_WaitProcessWideKey(out_word, &key, 1, 0, -1, -1);
}

s32 AsdFile_ReleaseMutex(u32* out_word)
{
    // 0x00113dc4: r0=sp, r1=[0x00465010], r2=1.
    return AsdKernel_ReleaseMutex(out_word, g_AsdFile.mutex, 1);
}

void AsdFile_AcquireChecked(u32* out_word)
{
    s32 result = AsdFile_AcquireMutex(out_word);
    if (result < 0) {
        AsdKernel_AbortOnFailure(result);
    }
}

void AsdFile_ReleaseChecked(u32* out_word)
{
    s32 result = AsdFile_ReleaseMutex(out_word);
    if (result < 0) {
        AsdKernel_AbortOnFailure(result);
    }
}

// The 0x18-byte file object allocated at 0x00113e80.  Only the vtable word and
// the five words that the constructor writes are named.
struct AsdFileObject {
    void** vtable;                      // +0x00: `str r1,[r0]` (0x00113eb0)
    u32 field_04;                       // +0x04: file handle, bit0 = owned (0x00114038)
    u32 field_08;                       // +0x08: `str sl,[r0,#8]` (0x00113e9c)
    u32 field_0c;                       // +0x0C: `str sl,[r0,#0xc]` (0x00113ea0)
    u32 field_10;                       // +0x10: `str sl,[r0,#0x10]` (0x00113ea4)
    u32 field_14;                       // +0x14: `str sl,[r0,#0x14]` (0x00113ea8)
};
static_assert(offsetof(AsdFileObject, field_04) == 0x04);
static_assert(offsetof(AsdFileObject, field_14) == 0x14);
static_assert(sizeof(AsdFileObject) == 0x18);

// 0x00420870: {vtable = 0x004208B0, 0x003FF29C, 0x003FF29C, self = 0x004208B0}.
// 0x00420880 (vtable - 0x30) holds 0, so the MSVC virtual-base store at
// 0x00113ebc rewrites the vtable word at offset 0 with the same pointer.
struct AsdFileVTableSlot {
    void** vtable;                      // +0x00: `ldr r1,[r3]` (0x00113eac)
    u32 field_04;                       // +0x04
    u32 field_08;                       // +0x08
    void* self;                         // +0x0C: `ldr r2,[r3,#0xc]` (0x00113eb8)
};
constexpr u32 kAsdFileObjectVTableTable = 0x00420870;

// Thread-descriptor callbacks copied verbatim into the descriptor at
// 0x0010d0f8..0x0010d120.
constexpr u32 kAsdFileThreadEntry0 = 0x00123BAC;
constexpr u32 kAsdFileThreadEntry1 = 0x00123BD8;
constexpr u32 kAsdFileThreadEntry2 = 0x00123BC8;

// 0x00465124 holds the lock used around the synchronous read (0x00113fe8).
constexpr u32 kAsdFileReadLock = 0x00465124;

// 0x004E4100 / 0x004E411C: the two AsdMemory region descriptors.
constexpr u32 kAsdMemoryRegion2 = 0x004E4100;
constexpr u32 kAsdMemoryRegion3 = 0x004E411C;

// Allocator vtables selected at 0x001039dc / 0x00103a1c / 0x00103a64.
constexpr u32 kAsdMemoryPool100VTable = 0x00420580;
constexpr u32 kAsdMemoryPool20000VTable = 0x00420440;
constexpr u32 kAsdMemoryPool30000VTable = 0x004204B8;

} // namespace

namespace smt4::engine {

// ---------------------------------------------------------------------------
// Globals
// ---------------------------------------------------------------------------

AsdFileGlobal g_AsdFile{};                  // 0x00465000
u8 g_AsdLoadFileRawPath;                    // 0x00465040
AsdMemoryGlobal g_AsdMemory{};              // 0x00465170

// ---------------------------------------------------------------------------
// AsdFile (c:\SMT4\XRD686\AsdSDK\Source\Sys\File\AsdFile.cpp)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0010250c, 296)
void AsdFile_func_0010250c()
{
    // 0x00102518: `str r5,[r6,#0xc]` with r5 = 0.
    g_AsdFile.head = nullptr;

    // 0x0010251c: mount "fs:USER" once (0x0010f5b8 returns early when the
    // 0x0044e644 state word is already set and otherwise falls through into
    // 0x0010f5c8).
    AsdFs_Init();

    // 0x00102520..0x0010252c: AsdFs_RomHeapSize(0x10, 0x10, 1) = 0x380.
    const u32 heap_size = AsdFs_RomHeapSize(0x10, 0x10, 1);

    // 0x00102534..0x0010255c: line 0x115,
    // AsdMem_AllocAlign(0x100, 0x100, 0, 0x380, 1).
    g_AsdFile.rom_buffer = AsdMem_AllocAlign(0x100, 0x100, 0, heap_size, 1);

    // 0x00102564..0x00102574: AsdFs_MountRom(0x10, 0x10, buffer, 0x380, 1).
    AsdFs_MountRom(0x10, 0x10, g_AsdFile.rom_buffer, heap_size, 1);

    // 0x00102584..0x0010258c: create the mutex (initial state 0, flags 2).
    u32 mutex = 0;
    s32 result = AsdKernel_CreateMutex(&mutex, 0, 2);
    if (result >= 0) {
        g_AsdFile.mutex = mutex;            // 0x001025a0
        result = 0;                         // 0x0010259c: `mov r0,#0`
    }
    if (result < 0) {
        AsdKernel_AbortOnFailure(result);   // 0x001025a8
    }

    // 0x001025ac..0x001025bc: release the fresh mutex once.
    u32 release_slot = 0;
    result = AsdKernel_ReleaseMutex(&release_slot, g_AsdFile.mutex, 1);
    if (result < 0) {
        AsdKernel_AbortOnFailure(result);   // 0x001025c8
    }

    // 0x001025cc..0x001025d4: publish state 0 on the 0x00465024 object.
    AsdSync_Set(&g_AsdFile.sync, 0);

    // 0x001025e0: create the worker heap and spawn the worker thread.
    AsdFile_func_0010d070();

    // 0x001025ec: `b 0x0010f69c` (tail call).
    AsdFs_ThreadStart();
}

// DECOMP_FUNC(0x0010d070, 272)
void AsdFile_func_0010d070()
{
    // 0x0010d088: clear the shutdown flag.
    g_AsdFile.field_00 = 0;

    // 0x0010d090..0x0010d0ac: line 0x317,
    // AsdWork_Alloc(0x100, 0x100, 0, 0x1000, 0x1000, 1).
    g_AsdFile.work_buffer = AsdWork_Alloc(0x100, 0x100, 0, 0x1000, 0x1000, 1);

    // 0x0010d0b8: allocate the 0x18-byte heap object.  r1 is the caller's r4
    // and 0x002c23f8 only consumes r0.
    u8* heap = static_cast<u8*>(AsdMemory_func_002c23f8(0x18));
    if (heap != nullptr) {
        *reinterpret_cast<u32*>(heap + 0x00) = 0;   // 0x0010d0c8
        *reinterpret_cast<u32*>(heap + 0x04) = 0;   // 0x0010d0cc
        *reinterpret_cast<u32*>(heap + 0x08) = 0;   // 0x0010d0d0
        *reinterpret_cast<u32*>(heap + 0x0C) = 0;   // 0x0010d0d4
        *reinterpret_cast<u8*>(heap + 0x10) = 0;    // 0x0010d0d8
    }
    g_AsdFile.heap = heap;                          // 0x0010d0dc

    // 0x0010d0e0..0x0010d0e8: AsdHeap_Init(heap, work_buffer, 0x1000).
    AsdHeap_Init(heap, g_AsdFile.work_buffer, 0x1000);

    // 0x0010d0b4 / 0x0010d0ec read r4 before this frame ever writes it.  The
    // sole caller (0x0010250c) leaves r4 = &g_AsdFile.mutex, set by its
    // `add r4,r6,#0x10` at 0x00102578, and that word is what lands in the
    // worker-context slot at [sp,#0x20].
    void* worker_context = &g_AsdFile.mutex;

    struct ThreadDesc {
        u32 word_00;                    // [sp+0x10]
        u32 word_04;                    // [sp+0x14]
        u32 word_08;                    // [sp+0x18]
        u32 word_0c;                    // [sp+0x1c]
        void* context;                  // [sp+0x20]
    } desc;

    desc.word_00 = 4;                               // 0x0010d0f8
    desc.word_04 = kAsdFileThreadEntry0;            // 0x0010d0fc
    desc.word_08 = kAsdFileThreadEntry1;            // 0x0010d10c
    desc.word_0c = kAsdFileThreadEntry2;            // 0x0010d11c
    desc.context = worker_context;                  // 0x0010d0ec

    // 0x0010d124 / 0x0010d128: stack size = object[+0x0C] + object[+0x08].
    u8* object = static_cast<u8*>(g_AsdFile.heap);
    const u32 stack_size = *reinterpret_cast<u32*>(object + 0x08) +
                           *reinterpret_cast<u32*>(object + 0x0C);

    // 0x0010d140: out = &g_AsdFile.thread_desc, desc, entry =
    // AsdFile_func_00113d58, context = &desc.context, stack size, priority
    // 0x12, processor -2.
    s32 result = AsdThread_Create(&g_AsdFile.thread_desc, &desc,
                                  &AsdFile_func_00113d58, &desc.context,
                                  stack_size, 0x12, -2);
    // 0x0010d144: status class 0x00600000 is accepted; otherwise a negative
    // result is fatal.
    if ((result & 0x07E00000) != 0x00600000 && result < 0) {
        AsdKernel_AbortOnFailure(result);           // 0x0010d154
    }
}

// DECOMP_FUNC(0x00113d58, 1564)
void AsdFile_func_00113d58()
{
    u16 wide_path[0x100];                           // [sp+0x000..0x200]
    u32 lock_key;                                   // [sp+0x008]
    u32 lock_out;                                   // [sp+0x00C]
    u32 open_out;                                   // [sp+0x214]
    u32 convert_state[2];                           // [sp+0x218]

    struct OpenDesc {
        void* handle_slot;                          // [sp+0x20C]
        u32 mode;                                   // [sp+0x210]
    } open_desc;

    // 0x00113d70: wait on the 0x00465024 state object.
    AsdSync_Wait(&g_AsdFile.sync);
    if (g_AsdFile.field_00 != 0) {                  // 0x00113d78
        return;
    }

    for (;;) {
        // ---- snapshot the request head under the mutex ---------------------
        lock_key = g_AsdFile.mutex;                 // 0x00113d90
        s32 result = AsdKernel_WaitProcessWideKey(&lock_out, &lock_key, 1, 0, -1, -1);
        if (result < 0) {
            AsdKernel_AbortOnFailure(result);       // 0x00113db0
        }

        AsdFileRequest* request = g_AsdFile.head;   // 0x00113db4

        // The listing passes `sp`, the head of the wide-path buffer, as the
        // out pointer (0x00113dc0); the trampoline's store is dead because the
        // path is rewritten before it is read.
        AsdFile_ReleaseChecked(reinterpret_cast<u32*>(wide_path));

        for (;;) {
            // ---- idle: nothing queued --------------------------------------
            if (request == nullptr) {               // 0x00113dd8
                if (g_AsdFile.field_00 != 0) {      // 0x00114340
                    return;
                }
                AsdSync_Lock(&g_AsdFile.sync);      // 0x0011434c
                AsdThread_Sleep(0x002DC6C0, 0);     // 0x00114358
                break;                              // 0x00114364 -> 0x00113d70
            }

            if (g_AsdFile.field_00 != 0) {          // 0x00113de0
                return;
            }

            // ---- completed requests ----------------------------------------
            // 0x00113de8: state 4 or 5 jumps straight to the completion path.
            if (request->state == 4 || request->state == 5) {
                lock_key = g_AsdFile.mutex;
                result = AsdKernel_WaitProcessWideKey(&lock_out, &lock_key, 1, 0, -1, -1);
                if (result < 0) {
                    AsdKernel_AbortOnFailure(result);       // 0x001141d0
                }

                // 0x001141d4: `ldrd r0,r1,[r7,#4]; sub r0,r0,r1; str r0,[r7,#4]`
                request->pending -= request->completed;

                if (request->pending > 0) {                 // 0x001141e4
                    // 0x00114260: release, then re-acquire at 0x00114284.
                    AsdFile_ReleaseChecked(reinterpret_cast<u32*>(wide_path));
                    AsdFile_AcquireChecked(&lock_out);      // 0x001142a4
                    request = request->next;                // 0x001142b4
                    AsdFile_ReleaseChecked(reinterpret_cast<u32*>(wide_path));
                    continue;
                }

                // 0x001141e8: unlink and destroy the finished request.
                AsdFileRequest* prev = request->prev;
                AsdFileRequest* next = request->next;
                if (prev != nullptr) {
                    prev->next = next;                      // 0x001141fc
                    if (next != nullptr) {
                        next->prev = prev;                  // 0x00114200
                    }
                } else {
                    g_AsdFile.head = next;                  // 0x00114218
                    if (next != nullptr) {
                        next->prev = nullptr;               // 0x0011421c
                    }
                }

                if (request->field_10 == 0) {               // 0x00114204
                    if (request->buffer != nullptr) {
                        AsdMem_Free(request->buffer);       // 0x0011422c
                    }
                }
                request->buffer = nullptr;                  // 0x00114234
                AsdMem_Free(request);                       // 0x00114238

                request = next;
                AsdFile_ReleaseChecked(reinterpret_cast<u32*>(wide_path));
                continue;                                   // 0x00114258
            }

            // ---- cancellation callback -------------------------------------
            if (request->cancel_callback != nullptr) {      // 0x00113df8
                AsdFile_AcquireChecked(&lock_out);          // 0x00113e24
                using CancelFn = void (*)(char*);
                reinterpret_cast<CancelFn>(request->cancel_callback)(request->path);
                request->cancel_callback = nullptr;         // 0x00113e40
                AsdFile_ReleaseChecked(reinterpret_cast<u32*>(wide_path));
            }

            // ---- state machine ---------------------------------------------
            // 0x00113e68: jump table over states 0..3.
            const u32 state = static_cast<u32>(request->state);

            if (state == 0) {
                // 0x00113e80: construct the 0x18-byte AsdFileObject.
                AsdFileObject* file = static_cast<AsdFileObject*>(
                    AsdMemory_func_002c23f8(0x18));

                if (file != nullptr) {
                    file->field_04 = 0;                 // 0x00113e94
                    const AsdFileVTableSlot* slot =
                        reinterpret_cast<const AsdFileVTableSlot*>(kAsdFileObjectVTableTable);
                    void** vtable = slot->vtable;       // 0x00113eac
                    file->vtable = vtable;              // 0x00113eb0
                    file->field_08 = 0;                 // 0x00113e9c
                    file->field_0c = 0;                 // 0x00113ea0
                    file->field_10 = 0;                 // 0x00113ea4
                    file->field_14 = 0;                 // 0x00113ea8

                    // 0x00113eb4..0x00113ebc: virtual-base store; vtable-0x30
                    // reads 0x00420880, which holds 0.
                    const u32 base_offset =
                        *reinterpret_cast<u32*>(reinterpret_cast<u8*>(vtable) - 0x30);
                    *reinterpret_cast<void**>(reinterpret_cast<u8*>(file) + base_offset) =
                        slot->self;
                }
                request->file = file;                   // 0x00113ec0

                // 0x00113ec4..0x00113ed8: open descriptor
                // {&file->field_04, 1}.
                open_desc.handle_slot = &file->field_04;
                open_desc.mode = 1;

                // 0x00113ed0..0x00113ee8: reset the conversion state.
                convert_state[0] = 0;
                convert_state[1] = 0;
                MbsInit(convert_state);

                // 0x00113eec..0x00113f28: path -> UTF-16.
                u16* out = wide_path;
                const char* cursor = request->path;
                u32 length;
                while ((length = MbrLen(cursor, 0x105, convert_state)) != 0) {
                    if (MbrToWc(out, cursor, length, convert_state) == 0) {
                        break;
                    }
                    ++out;                              // 0x00113f20
                    cursor += length;                   // 0x00113f24
                }
                *out = 0;                               // 0x00113f30

                // 0x00113f3c..0x00113f48: clear the handle words again.
                file->field_10 = 0;                     // 0x00113f3c
                file->field_14 = 0;                     // 0x00113f40
                file->field_08 = 0;                     // 0x00113f44
                file->field_0c = 0;                     // 0x00113f48

                // 0x00113f4c: AsdFile_Open(&file->field_04, wide_path, 1).
                const s32 open_result = AsdFile_Open(open_desc.handle_slot,
                                                    wide_path, open_desc.mode);
                if ((open_result & static_cast<s32>(0x80000000u)) != 0) {
                    request->state = 5;                 // 0x00113f5c
                }

                // 0x00113f60..0x00113f70: vtable[0x24] = file size.
                using SizeFn = u32 (*)(void*);
                request->file_size = reinterpret_cast<SizeFn>(file->vtable[0x24 / 4])(file);

                // 0x00113f74..0x00113f8c: vtable[0x0C](file, ...) with r2=r3=0
                // and a zero fifth word.  r1 still holds the slot pointer.
                using SeekFn = void (*)(void*, u32, u32, u32, u32);
                SeekFn seek = reinterpret_cast<SeekFn>(file->vtable[0x0C / 4]);
                seek(file, static_cast<u32>(reinterpret_cast<std::uintptr_t>(seek)), 0, 0, 0);

                if (request->buffer == nullptr) {       // 0x00113f90
                    switch (request->read_mode) {       // 0x00113f9c
                    case 0x10:                          // 0x00114098, line 0x26F
                        request->buffer = AsdWork_Alloc2(0x100, 0x100, 0, request->file_size,
                                                         request->request_size, 0);
                        break;
                    case 1:                             // 0x001140CC, line 0x271
                        request->buffer = AsdWork_Alloc2(0x10000, 0x100, 0, request->file_size,
                                                         request->request_size, 1);
                        break;
                    case 0x11:                          // 0x00114100, line 0x273
                        request->buffer = AsdWork_Alloc2(0x10000, 0x100, 0, request->file_size,
                                                         request->request_size, 0);
                        break;
                    default:                            // 0x00113FB8, line 0x275
                        request->buffer = AsdWork_Alloc2(0x100, 0x100, 0, request->file_size,
                                                         request->request_size, 1);
                        break;
                    }
                }

                // 0x00113fe4..0x0011400c: read under 0x00465124.
                void* read_lock = *reinterpret_cast<void**>(kAsdFileReadLock);
                AsdMemLock_Acquire(read_lock);
                g_AsdFile.field_04 = 1;             // 0x00113ff0

                using ReadFn = s32 (*)(void*, u32*, void*, u32);
                ReadFn read = reinterpret_cast<ReadFn>(file->vtable[0x28 / 4]);
                const s32 read_result = read(file, &open_out, request->buffer,
                                             request->file_size);

                g_AsdFile.field_04 = 0;             // 0x00114014
                AsdMemLock_Release(read_lock);      // 0x0011401c
                if ((read_result & static_cast<s32>(0x80000000u)) != 0) {
                    request->state = 5;             // 0x0011402c
                }

                // 0x00114030..0x00114054: close the handle.
                AsdFileObject* object = static_cast<AsdFileObject*>(request->file);
                const u32 handle = object->field_04;
                if ((handle & ~1u) != 0) {          // 0x00114038
                    if ((handle & 1u) != 0) {
                        AsdFile_NotifyClose();      // 0x00114044
                    }
                    AsdFile_ReleaseHandle(reinterpret_cast<void*>(handle & ~1u));
                    object->field_04 = 0;           // 0x00114054
                }

                // 0x00114058..0x0011406c: virtual destructor.
                if (request->file != nullptr) {
                    using DtorFn = void (*)(void*);
                    reinterpret_cast<DtorFn>(file->vtable[1])(file);
                }

                request->state = 3;                 // 0x00114074
                request->file = nullptr;            // 0x00114078
                request->state = 4;                 // 0x00114080
            } else if (state == 3) {
                // 0x0011407C: state 3 promotes itself to 4.
                request->state = 4;
            }

            // 0x00114084: only 4/5 run the completion callback.
            if (request->state == 4 || request->state == 5) {
                if (request->callback != nullptr) {         // 0x00114134
                    AsdFile_AcquireChecked(&lock_out);      // 0x00114160
                    void* arg = request->callback_arg;      // 0x00114170
                    if (arg == nullptr) {
                        arg = request;                      // 0x0011417c
                    }
                    using CallbackFn = void (*)(void*);
                    reinterpret_cast<CallbackFn>(request->callback)(arg);
                    AsdFile_ReleaseChecked(reinterpret_cast<u32*>(wide_path));
                }
            }

            // 0x00114284: advance to the next request.
            AsdFile_AcquireChecked(&lock_out);
            request = request->next;                        // 0x001142b4
            AsdFile_ReleaseChecked(reinterpret_cast<u32*>(wide_path));
        }
    }
}

// DECOMP_FUNC(0x002b0434, 480)
AsdFileRequest* AsdFile_func_002b0434(const char* name, u8 mode)
{
    // 0x002b0448..0x002b0468: acquire the AsdFile mutex.
    u32 lock_key = g_AsdFile.mutex;
    u32 lock_out;
    s32 result = AsdKernel_WaitProcessWideKey(&lock_out, &lock_key, 1, 0, -1, -1);
    if (result < 0) {
        AsdKernel_AbortOnFailure(result);       // 0x002b0470
    }

    // 0x002b0498: line 0xC2, AsdMem_Alloc(0x100, 0x100, 0, 0x144, 1).
    AsdFileRequest* request = static_cast<AsdFileRequest*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x144, 1));
    AsdMem_Zero(request, 0x144);                // 0x002b04a4

    // 0x002b04a8..0x002b04d0: append at the tail of the request list.
    if (g_AsdFile.head == nullptr) {
        g_AsdFile.head = request;               // 0x002b04b4
    } else {
        AsdFileRequest* node = g_AsdFile.head;
        while (node->next != nullptr) {         // 0x002b04bc
            node = node->next;
        }
        node->next = request;                   // 0x002b04cc
        request->prev = node;                   // 0x002b04d0
    }

    // 0x002b04d4..0x002b0550: scan the first min(strlen, 8) bytes for ':'.
    u32 length = AsdString_Length(name);        // 0x002b04d8
    if (length > 8) {
        length = 8;                             // 0x002b04e8
    }
    bool has_scheme = false;
    for (u32 i = 0; i < length; ++i) {
        if (name[i] == ':') {
            has_scheme = true;
            break;
        }
    }

    if (has_scheme) {
        AsdString_Strcpy(request->path, name);  // 0x002b05c0
    } else {
        // 0x002b0560: sprintf(path, "rom:/%s", name).
        UiText_Format(request->path, "rom:/%s", name);
    }

    request->state = 0;                         // 0x002b0564
    request->mode = mode;                       // 0x002b0568
    request->buffer = nullptr;                  // 0x002b056c
    request->field_10 = 0;                      // 0x002b0570
    request->field_14 = 0;                      // 0x002b0574
    request->file_size = 0;                     // 0x002b057c
    request->request_size = 0x80;               // 0x002b0580
    request->file = nullptr;                    // 0x002b058c
    request->pending = 1;                       // 0x002b0590
    request->completed = 0;                     // 0x002b0590

    // 0x002b0594..0x002b059c: release the mutex (out pointer is the frame base).
    u32 release_slot = 0;
    result = AsdKernel_ReleaseMutex(&release_slot, g_AsdFile.mutex, 1);
    if (result < 0) {
        AsdKernel_AbortOnFailure(result);       // 0x002b05a8
    }

    return request;                             // 0x002b05b0
}

// ---------------------------------------------------------------------------
// AsdLoadFile (c:\SMT4\XRD686\AsdSDK\Source\Sys\File\AsdLoadFile.cpp)
// ---------------------------------------------------------------------------

namespace {

// 0x18-byte context allocated at 0x002ae768 and handed to the 0x00155B30
// completion callback through request->callback_arg.
struct AsdLoadFileContext {
    void* request;                      // +0x00: `str r0,[r4]` (0x002ae7b0)
    void* field_04;                     // +0x04: `str r8,[r0,#4]` (0x002ae770)
    f32   scale;                        // +0x08: `vstr s16,[r0,#8]` (0x002ae778)
    u32   field_0c;                     // +0x0C: `strd r6,r7,[r4,#0xc]` (0x002ae780)
    u32   field_10;                     // +0x10: second word of that `strd`
    void* field_14;                     // +0x14: `str r5,[r0,#0x14]` (0x002ae76c)
};
static_assert(offsetof(AsdLoadFileContext, scale) == 0x08);
static_assert(offsetof(AsdLoadFileContext, field_14) == 0x14);
static_assert(sizeof(AsdLoadFileContext) == 0x18);

constexpr u32 kAsdLoadFileCallback = 0x00155B30;

} // namespace

// DECOMP_FUNC(0x002ae6c8, 336)
u32 AsdLoadFile_func_002ae6c8(const char* name, u32* out_status, u32 flags,
                              void* owner, f32 scale, u32 size)
{
    char path[0x100];
    AsdMem_Zero(path, 0x100);                   // 0x002ae6f4

    // 0x002ae6f8..0x002ae71c: an already-qualified name (or the raw-path flag)
    // is copied as-is, everything else is prefixed with "rom:/".
    if (g_AsdLoadFileRawPath != 0 || AsdFile_HasScheme(name) != 0) {
        // The listing passes the name itself as the format string (r1 = r4,
        // no varargs), which is a plain copy for names without '%'.
        UiText_Format(path, name);              // 0x002ae724
    } else {
        UiText_Format(path, "rom:/%s", name);   // 0x002ae740
    }

    // 0x002ae768: line 0x15B, AsdMem_Alloc(0x100, 0x100, 0, 0x18, 0).
    AsdLoadFileContext* context = static_cast<AsdLoadFileContext*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x18, 0));

    context->field_14 = out_status;             // 0x002ae76c: `str r5,[r0,#0x14]`
    context->field_04 = owner;                  // 0x002ae770: `str r8,[r0,#4]`
    context->scale = scale;                     // 0x002ae778: `vstr s16,[r0,#8]`
    // 0x002ae780: `strd r6,r7,[r4,#0xc]` stores a2 at +0x0C and a5 at +0x10.
    context->field_0c = flags;
    context->field_10 = size;

    if (out_status != nullptr) {
        *out_status = 0;                        // 0x002ae794: `strne sb,[r5]`
    }

    // 0x002ae798: enqueue the request with the 0x00155B30 completion callback
    // and this context as its argument.
    context->request = AsdFile_CreateRequestWithCallback(
        path, 0, reinterpret_cast<void*>(kAsdLoadFileCallback), context);

    // 0x002ae79c..0x002ae7b4: translate the flag bits into a read mode.
    u32 read_mode = 0;
    if ((flags & 1) != 0) {
        read_mode |= 1;
    }
    if ((flags & 2) != 0) {
        read_mode |= 0x10;
    }
    AsdFile_SetReadMode(static_cast<AsdFileRequest*>(context->request), read_mode);

    // 0x002ae7c0: store the requested size and return its status.
    return AsdFile_SetRequestSize(static_cast<AsdFileRequest*>(context->request), size);
}

// ---------------------------------------------------------------------------
// AsdMemory (c:\SMT4\XRD686\AsdSDK\Source\Sys\Mem\AsdMemory.cpp)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0010376c, 820)
void AsdMemory_func_0010376c()
{
    // 0x00103778..0x0010379c: publish and clear the GPU heap window.
    const u32 heap_start = AsdGpu_HeapStart();
    g_AsdMemory.heap->heap_start = heap_start;              // 0x00103784
    const u32 heap_size = AsdGpu_HeapSize();
    g_AsdMemory.heap->heap_size = heap_size;                // 0x00103794
    AsdWork_Zero(reinterpret_cast<void*>(heap_start), heap_size);   // 0x0010379c

    // 0x001037a0..0x001037c0: initialise the block pool and its lock.
    AsdMemBlock_Init(&g_AsdMemory.heap->block_pool, heap_start, heap_size, 0x100);
    AsdMemBlock_InitLock(&g_AsdMemory.heap->lock);

    // 0x001037c4..0x001037d4: only reserve the high block when the heap is
    // larger than 0x02000100 bytes.
    if (heap_size > 0x02000100u) {
        // 0x001037e8: size = heap_size + 0xFE000080.
        const u32 reserve = heap_size + 0xFE000080u;

        AsdMemLock_Acquire(&g_AsdMemory.heap->lock);        // 0x001037fc
        // 0x00103814: block alloc(reserve, -0x80, 0, 0, 0).
        void* block = AsdMemBlock_Alloc(&g_AsdMemory.heap->block_pool, reserve,
                                        -0x80, 0, 0, 0);
        AsdMemLock_Release(&g_AsdMemory.heap->lock);        // 0x00103820
        g_AsdMemory.block_handle = static_cast<u32>(
            reinterpret_cast<std::uintptr_t>(block));       // 0x00103824

        // 0x00103838..0x00103850: carve 0x100 bytes back out of the block.
        AsdMemLock_Acquire(&g_AsdMemory.heap->lock);
        AsdMemBlock_Release(&g_AsdMemory.heap->block_pool, block, 0x100);
        AsdMemLock_Release(&g_AsdMemory.heap->lock);
    }

    // 0x00103858..0x001038a8: 0x20000 and 0x30000 VRAM bank windows.
    g_AsdMemory.heap->region2_start = AsdGpu_BankStart(0x20000);
    g_AsdMemory.heap->region2_size =
        AsdGpu_BankEnd(0x20000) - g_AsdMemory.heap->region2_start;
    g_AsdMemory.heap->region3_start = AsdGpu_BankStart(0x30000);
    g_AsdMemory.heap->region3_size =
        AsdGpu_BankEnd(0x30000) - g_AsdMemory.heap->region3_start;
    g_AsdMemory.heap->field_100 = g_AsdMemory.heap->region3_start;

    // 0x001038ac..0x001038c4: publish the region table.
    AsdGpu_SetRegions(g_AsdMemory.block_handle, g_AsdMemory.block_handle_hi,
                      heap_start, heap_size,
                      g_AsdMemory.heap->region2_start,
                      g_AsdMemory.heap->region2_size,
                      g_AsdMemory.heap->region3_start,
                      g_AsdMemory.heap->region3_size);

    // 0x001038c8..0x00103938: first region descriptor (0x20000 window).
    AsdMemoryRegion* region2 = reinterpret_cast<AsdMemoryRegion*>(kAsdMemoryRegion2);
    region2->field_00 = 0;
    region2->field_04 = 0;
    region2->field_08 = 0;
    region2->tree.root = nullptr;
    region2->tree.tail = nullptr;
    region2->tree.count = 0;
    region2->size = g_AsdMemory.heap->region2_size;         // 0x00103900

    // 0x00103910..0x00103938: line 0x255,
    // AsdMem_AllocAlign(0x100, 0x100, 0, 0x10, 1).
    AsdMemoryBlock* node2 = static_cast<AsdMemoryBlock*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, 0x10, 1));
    node2->prev = nullptr;                                  // 0x00103924
    node2->next = nullptr;                                  // 0x0010392c
    node2->start = g_AsdMemory.heap->region2_start;         // 0x00103934
    node2->size = g_AsdMemory.heap->region2_size;
    AsdMemBlockTree_Insert(&region2->tree, node2);          // 0x00103938

    // 0x0010393c..0x001039a4: second region descriptor (0x30000 window).
    // 0x0010394c loads [heap+0xFC] through s16 and 0x0010396c / 0x00103998
    // store it back unchanged, so the word is copied bit-for-bit.
    AsdMemoryRegion* region3 = reinterpret_cast<AsdMemoryRegion*>(kAsdMemoryRegion3);
    region3->field_00 = 0;
    region3->field_04 = 0;
    region3->field_08 = 0;
    region3->tree.root = nullptr;
    region3->tree.tail = nullptr;
    region3->tree.count = 0;
    region3->size = g_AsdMemory.heap->region3_size;         // 0x0010396c

    AsdMemoryBlock* node3 = static_cast<AsdMemoryBlock*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, 0x10, 1));       // 0x00103988
    node3->prev = nullptr;                                  // 0x0010398c
    node3->next = nullptr;                                  // 0x00103990
    node3->start = g_AsdMemory.heap->region3_start;         // 0x00103994
    node3->size = g_AsdMemory.heap->region3_size;           // 0x00103998
    AsdMemBlockTree_Insert(&region3->tree, node3);          // 0x001039a4

    // 0x001039a8..0x001039e4: allocator bound to the 0x100 arena.
    void* pool = AsdMem_AllocAlign(0x100, 0x100, 0, 4, 1);
    if (pool != nullptr) {
        *static_cast<u32*>(pool) = kAsdMemoryPool100VTable;  // 0x001039e0
    }
    g_AsdMemory.pool_100 = pool;                            // 0x001039e4

    // 0x001039e8..0x00103a24: allocator bound to the 0x20000 arena.
    pool = AsdMem_AllocAlign(0x100, 0x100, 0, 4, 1);
    if (pool != nullptr) {
        *static_cast<u32*>(pool) = kAsdMemoryPool20000VTable; // 0x00103a20
    }
    g_AsdMemory.pool_20000 = pool;                          // 0x00103a24

    // 0x00103a28..0x00103a6c: allocator bound to the 0x30000 arena.
    pool = AsdMem_AllocAlign(0x100, 0x100, 0, 4, 1);
    if (pool != nullptr) {
        *static_cast<u32*>(pool) = kAsdMemoryPool30000VTable; // 0x00103a68
    }
    g_AsdMemory.pool_30000 = pool;                          // 0x00103a6c

    g_AsdMemory.field_00 = 0;                               // 0x00103a2c
}

// DECOMP_FUNC(0x00144978, 320)
void* AsdMemory_func_00144978(AsdMemBlockHeap* heap, u32 size)
{
    // 0x0014497c..0x00144990: first-fit scan of the free list.
    AsdMemoryBlock* block = heap->free_head;
    while (block != nullptr && block->size < size) {
        block = block->next;                                // 0x00144aa0
    }
    if (block == nullptr) {
        return nullptr;                                     // 0x00144aac
    }

    // 0x00144994..0x001449a8: round the request up to 0x80.
    if ((size & 0x7F) != 0) {
        size += 0x80 - (size & 0x7F);
    }

    // 0x001449b8: re-tests the already-aligned value, so the branch at
    // 0x001449c0 is never taken.
    u32 block_size = size;
    if ((block_size & 0x7F) != 0) {
        block_size += 0x80 - (block_size & 0x7F);
    }

    if (block->size == size) {                              // 0x001449ac
        // ---- exact fit: unlink the node and publish it in the tree --------
        heap->free_bytes -= block->size;                    // 0x00144a58

        AsdMemoryBlock* prev = block->prev;
        AsdMemoryBlock* next = block->next;
        if (prev != nullptr) {
            prev->next = next;                              // 0x00144a64
        } else {
            heap->free_head = next;                         // 0x00144a68
        }
        if (next != nullptr) {
            next->prev = prev;                              // 0x00144a70
        } else {
            heap->free_tail = prev;                         // 0x00144a74
        }
        block->prev = nullptr;                              // 0x00144a78
        block->next = nullptr;                              // 0x00144a7c

        heap->free_count -= 1;                              // 0x00144a8c
        AsdMemBlockTree_Insert(heap, block);                // 0x00144a94
        return reinterpret_cast<void*>(block->start);       // 0x00144a98
    }

    // ---- split: carve the front of the free block -------------------------
    // 0x001449f4: line 0x180, AsdMem_AllocAlign(0x100, 0x100, 0, 0x10, 1).
    AsdMemoryBlock* node = static_cast<AsdMemoryBlock*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, 0x10, 1));
    node->prev = nullptr;                                   // 0x001449f8
    node->next = nullptr;                                   // 0x001449fc
    node->start = block->start;                             // 0x00144a10
    node->size = block_size;                                // 0x00144a10

    block->start += block_size;                             // 0x00144a1c
    block->size -= block_size;                              // 0x00144a28
    heap->free_bytes -= node->size;                         // 0x00144a34

    AsdMemBlockTree_Insert(heap, node);                     // 0x00144a44
    return reinterpret_cast<void*>(node->start);            // 0x00144a48
}

// DECOMP_FUNC(0x002c684c, 112)
void* AsdMemory_func_002c684c(u32 size)
{
    // 0x002c6854..0x002c6878: line 0x78,
    // AsdMem_AllocAlign(0x100, 0x100, 0, size, 1).
    return AsdMem_AllocAlign(0x100, 0x100, 0, size, 1);
}

// DECOMP_FUNC(0x00262ac0, 104)
void* AsdMemory_func_00262ac0(u32 size)
{
    // 0x00262ac8..0x00262aec: line 0xBD,
    // AsdMem_AllocAlign(0x100, 0x100, 0, size, 1).
    return AsdMem_AllocAlign(0x100, 0x100, 0, size, 1);
}

// DECOMP_FUNC(0x00346d38, 120)
void* AsdMemory_func_00346d38(u32 size, u32 extra)
{
    // 0x00346d48..0x00346d70: line 0x4F.  r3 = size, [sp] = extra,
    // [sp+4] = 1.
    return AsdWork_Alloc2(0x100, 0x100, 0, size, extra, 1);
}

// DECOMP_FUNC(0x00348a1c, 120)
void* AsdMemory_func_00348a1c(u32 size, u32 extra)
{
    // 0x00348a2c..0x00348a54: line 0x67, same argument layout.
    return AsdWork_Alloc2(0x100, 0x100, 0, size, extra, 1);
}

// DECOMP_FUNC(0x0034b3dc, 120)
void* AsdMemory_func_0034b3dc(u32 size, u32 extra)
{
    // 0x0034b3f8..0x0034b414: line 0x3F, but the arena class is 0x10000
    // instead of 0x100 (r0 = 0x10000 at 0x0034b40c).
    return AsdWork_Alloc2(0x10000, 0x100, 0, size, extra, 1);
}

// ---------------------------------------------------------------------------
// AsdSaveCommon (c:\SMT4\XRD686\AsdSDK\Source\Sys\Save\AsdSaveCommon.cpp)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0021041c, 204)
u32 AsdSaveCommon_func_0021041c(u32 device, u32 file, void* header,
                                void* payload, u32 payload_size)
{
    // 0x00210438: total = payload_size + 0x80.
    const u32 total = payload_size + 0x80;

    // 0x00210430..0x0021045c: line 0x206,
    // AsdMem_AllocAlign(0x100, 0x100, 0, total, 1).
    u8* buffer = static_cast<u8*>(AsdMem_AllocAlign(0x100, 0x100, 0, total, 1));

    // 0x00210474: read header+payload in one transfer.
    const u32 result = AsdSave_Read(device, file, buffer, total);

    // 0x00210488: memcpy(header, buffer, 0x80) via the swapped helper.
    AsdMem_CopyFrom(buffer, header, 0x80);
    // 0x00210498: memcpy(payload, buffer + 0x80, payload_size).
    AsdMem_CopyFrom(buffer + 0x80, payload, payload_size);

    AsdMem_Free(buffer);                        // 0x002104a0
    return result;                              // 0x002104a4
}

// DECOMP_FUNC(0x002104e8, 268)
u32 AsdSaveCommon_func_002104e8(u32 device, u32 file, const void* header,
                                const void* payload, u32 payload_size)
{
    // 0x00210504: total = payload_size + 0x80.
    const u32 total = payload_size + 0x80;

    // 0x00210500..0x00210528: line 0x1D4,
    // AsdMem_AllocAlign(0x100, 0x100, 0, total, 1).
    u8* buffer = static_cast<u8*>(AsdMem_AllocAlign(0x100, 0x100, 0, total, 1));

    // 0x0021053c: memcpy(buffer, header, 0x80).
    AsdMem_CopyFrom(header, buffer, 0x80);
    // 0x0021054c: memcpy(buffer + 0x80, payload, payload_size).
    AsdMem_CopyFrom(payload, buffer + 0x80, payload_size);

    // 0x00210560: write header+payload in one transfer.
    const u32 result = AsdSave_Write(device, file, buffer, total);

    AsdMem_Free(buffer);                        // 0x0021056c
    return result;                              // 0x00210570
}

} // namespace smt4::engine
