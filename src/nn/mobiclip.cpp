#include "nn/mobiclip.h"
#include "engine/asd_symbols.h"
#include <cstdint>

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

extern "C" {
    // Allocators / heap helpers
    void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);         // 0x002c4b84
    void* AsdMem_AllocAlign(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);    // 0x002c54f0
    void  AsdMem_Zero(void* ptr, u32 size);                                 // 0x002c4b30
    void  AsdMem_Free(void* ptr);                                           // 0x002c4360
    void* AsdWork_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 flag); // 0x002c34a4
    void  AsdMemBlock_Init(void* heap, u32 start, u32 size, u32 align);     // 0x002c3b1c
    void  AsdMemBlock_InitLock(void* lock);                                 // 0x002c3b00
    void  AsdHeap_Init(void* heap, void* buffer, u32 size);                 // 0x002bcf34
    void* AsdMem_AllocFlags(u32 size, u32 flags);                           // 0x002b76e8

    // Kernel helpers
    s32   AsdThread_Create(void* out, const void* desc, void* entry, void* arg,
                           u32 stack_size, u32 priority, s32 processor);    // 0x002bce50
    void  AsdKernel_AbortOnFailure(s32 result);                             // 0x002c5468
    s32   AsdEvent_Create(void* out, u32 flag);                             // 0x002b5a04

    // Synchronisation / object helpers
    void  AsdSync_Set(void* sync, u32 value);                               // 0x002c541c
    void  AsdSync_Reset(void* sync);                                        // 0x002c4244
    void  AsdDecoder_Reset(void* decoder);                                  // 0x0034ef48

    // Scene-node state check (the factories live in engine/asd_symbols.h).
    u32   AsdNode_HasState();                                               // 0x0025b978

    // String / format helpers
    void  UiText_Format(char* dst, const char* fmt, ...);                   // 0x002be7fc

    // nn SDK callback publication.  Each stores the (r0,r1) pair in a
    // dedicated global table slot.
    void  nn_sdk_func_003f61f0(void* fn0, void* fn1);                        // 0x003f61f0
    void  nn_sdk_func_003f674c(void* fn0, void* fn1);                        // 0x003f674c
    void  nn_sdk_func_003f6318(void* fn0, void* fn1);                        // 0x003f6318
    void  nn_sdk_func_003f5a3c(void* fn0, void* fn1);                        // 0x003f5a3c
    void  nn_sdk_func_003f5e08(void* fn0, void* fn1);                        // 0x003f5e08
    void  nn_sdk_func_003f6c40(void* fn0, void* fn1);                        // 0x003f6c40

    // Mobiclip display / audio bring-up
    void  nn_sdk_func_00351b7c();                                           // 0x00351b7c
    void  AsdSound_InitDsp();                                               // 0x0011bd78
    void  AsdSound_OpenDefault();                                           // 0x0011be44
    void  AsdSound_InitOutput();                                            // 0x0011cb3c
    u32   nn_sdk_func_0035a52c(void* data, u32 size, u32 a2, u32 a3);        // 0x0035a52c
    s32   AsdEvent_Signal(u32 event);                                       // inline `svc #0x18` (0x0034e1f8)
}

namespace smt4::nn {

// Opaque arena objects whose addresses are the only observed facts.  They are
// passed to AsdMemBlock_Init, which writes the block list in place.
extern u8 g_MobiclipArena0;             // 0x004c3828
extern u8 g_MobiclipArena1;             // 0x004c3880
extern u8 g_MobiclipArena2;             // 0x004c39e0
extern u8 g_MobiclipArena3;             // 0x004c38d8
extern u8 g_MobiclipArena4;             // 0x004c3930
extern u8 g_MobiclipArena5;             // 0x004c3988

extern u8 g_MobiclipControlFlag;        // 0x0044d020: `strb r0,[r1]` (0x0017fccc)
extern u8 g_MobiclipLock;               // 0x004c40f8: r0 of 0x002c3b00 (0x0034e708)
extern u8 g_MobiclipAudioBuffer[];      // 0x004c3a38: r0 of the tail call (0x0017fd2c)

namespace {

// Thread entry points / descriptor callbacks copied verbatim.
constexpr u32 kS4FsReaderEntry = 0x0034e230;
constexpr u32 kS4FsReaderDesc0 = 0x003f7100;
constexpr u32 kS4FsReaderDesc1 = 0x003f7224;
constexpr u32 kS4FsReaderDesc2 = 0x003f71b8;
constexpr u32 kS4AudioDeviceEntry = 0x0034e928;
constexpr u32 kS4AudioDeviceDesc0 = 0x00123bac;
constexpr u32 kS4AudioDeviceDesc1 = 0x00123bd8;
constexpr u32 kS4AudioDeviceDesc2 = 0x00123bc8;
constexpr u32 kS4PlayerEntry = 0x0034fda4;
constexpr u32 kS4PlayerDesc0 = 0x003f7110;
constexpr u32 kS4PlayerDesc1 = 0x003f7228;
constexpr u32 kS4PlayerDesc2 = 0x003f71c4;

// Register pairs published by MobiclipCtrl_func_0017fb6c.
struct CallbackPair {
    u32 first;
    u32 second;
};

CallbackPair MobiclipCtrl_Callbacks[] = {
    {0x001c2a14, 0x001a0e50},           // 0x0017fcd4/0x0017fcd0
    {0x00203b64, 0x001df7b0},           // 0x0017fce0/0x0017fcdc
    {0x001ffaa8, 0x001dbb34},           // 0x0017fcec/0x0017fce8
    {0x001ffaa8, 0x001dbb34},           // 0x0017fcf8/0x0017fcf4
    {0x001ffaa8, 0x001dbb34},           // 0x0017fd04/0x0017fd00
    {0x001a0e70, 0x0018bf34},           // 0x0017fd10/0x0017fd0c
};

} // namespace

// ---------------------------------------------------------------------------
// MobiclipCtrl (0x0017FB6C)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0017fb6c, 584)
void MobiclipCtrl_func_0017fb6c()
{
    // 0x0017fb70..0x0017fba8: 0x240000 bytes from the 0x10000 arena.
    void* buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, 0x240000, 1);
    AsdMemBlock_Init(&g_MobiclipArena0, static_cast<u32>(reinterpret_cast<std::uintptr_t>(buffer)),
                     0x240000, 0x100);  // 0x0017fba8

    // 0x0017fbac..0x0017fbe0: 0x80000 bytes.
    buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, 0x80000, 1);
    AsdMemBlock_Init(&g_MobiclipArena1, static_cast<u32>(reinterpret_cast<std::uintptr_t>(buffer)),
                     0x80000, 0x100);   // 0x0017fbe0

    // 0x0017fbe4..0x0017fc18: 0x400000 bytes.
    buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, 0x400000, 1);
    AsdMemBlock_Init(&g_MobiclipArena2, static_cast<u32>(reinterpret_cast<std::uintptr_t>(buffer)),
                     0x400000, 0x100);  // 0x0017fc18

    // 0x0017fc1c..0x0017fc50: 0x100000 bytes, alignment 0.
    buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, 0x100000, 1);
    AsdMemBlock_Init(&g_MobiclipArena3, static_cast<u32>(reinterpret_cast<std::uintptr_t>(buffer)),
                     0x100000, 0);      // 0x0017fc50

    // 0x0017fc54..0x0017fc88: 0x8000 bytes, alignment 0.
    buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, 0x8000, 1);
    AsdMemBlock_Init(&g_MobiclipArena4, static_cast<u32>(reinterpret_cast<std::uintptr_t>(buffer)),
                     0x8000, 0);        // 0x0017fc88

    // 0x0017fc8c..0x0017fcc0: 0x90000 bytes, alignment 0.
    buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, 0x90000, 1);
    AsdMemBlock_Init(&g_MobiclipArena5, static_cast<u32>(reinterpret_cast<std::uintptr_t>(buffer)),
                     0x90000, 0);       // 0x0017fcc0

    // 0x0017fcc4..0x0017fccc: clear the one-byte playback gate.
    g_MobiclipControlFlag = 0;

    // 0x0017fcd0..0x0017fd14: publish the six callback pairs.  The listing
    // loads the first word into r0 and the second into r1 for every call.
    nn_sdk_func_003f61f0(reinterpret_cast<void*>(MobiclipCtrl_Callbacks[0].first),
                         reinterpret_cast<void*>(MobiclipCtrl_Callbacks[0].second));
    nn_sdk_func_003f674c(reinterpret_cast<void*>(MobiclipCtrl_Callbacks[1].first),
                         reinterpret_cast<void*>(MobiclipCtrl_Callbacks[1].second));
    nn_sdk_func_003f6318(reinterpret_cast<void*>(MobiclipCtrl_Callbacks[2].first),
                         reinterpret_cast<void*>(MobiclipCtrl_Callbacks[2].second));
    nn_sdk_func_003f5a3c(reinterpret_cast<void*>(MobiclipCtrl_Callbacks[3].first),
                         reinterpret_cast<void*>(MobiclipCtrl_Callbacks[3].second));
    nn_sdk_func_003f5e08(reinterpret_cast<void*>(MobiclipCtrl_Callbacks[4].first),
                         reinterpret_cast<void*>(MobiclipCtrl_Callbacks[4].second));
    nn_sdk_func_003f6c40(reinterpret_cast<void*>(MobiclipCtrl_Callbacks[5].first),
                         reinterpret_cast<void*>(MobiclipCtrl_Callbacks[5].second));

    // 0x0017fd18: bring up the Y2R conversion unit.
    nn_sdk_func_00351b7c();

    // 0x0017fd1c..0x0017fd34: tail call
    // helper_S4AudioDevice_func_0034e64c(&g_MobiclipAudioBuffer, 1, 0, 0).
    helper_S4AudioDevice_func_0034e64c(g_MobiclipAudioBuffer, 1, nullptr, 0);
}

// ---------------------------------------------------------------------------
// MobiclipCtrlProcess (0x002EF664)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002ef664, 432)
MobiclipMoveNode* MobiclipCtrlProcess_func_002ef664(s32 movie_index, u8 flag)
{
    // 0x002ef680..0x002ef6ac: allocate and clear the 0x74-byte control block.
    MobiclipCtrlProcess* process = static_cast<MobiclipCtrlProcess*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x74, 1));
    g_MobiclipProcess.process = process;                 // 0x002ef6a4
    AsdMem_Zero(process, 0x74);                          // 0x002ef6ac

    // 0x002ef6b0..0x002ef6d8: "Move" node, two callbacks plus the process.
    // The listing pushes [sp]=0x001DD178 and [sp+4]=0x002FEA58.
    process->move = static_cast<MobiclipMoveNode*>(AsdTask_CreateCalc(
        "Move", 2, 0, 0,
        reinterpret_cast<void (*)(void*)>(0x001dd178),
        0x002fea58u,
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(process))));

    // 0x002ef6e8..0x002ef708: "Move NCL" child, strings at 0x00404f1c.
    process->move_ncl = static_cast<MobiclipMoveNode*>(AsdTask_CreateDraw(
        "Move NCL", 0x7a, 0, 0,
        reinterpret_cast<void (*)(void*)>(0x002016cc), 0,
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(process)),
        process->move));

    // 0x002ef71c..0x002ef734: "Move NCR" child, strings at 0x00404f10.
    process->move_ncr = static_cast<MobiclipMoveNode*>(AsdTask_CreateDraw(
        "Move NCR", 0xd8, 0, 0,
        reinterpret_cast<void (*)(void*)>(0x002016cc), 0,
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(process)),
        process->move));

    // 0x002ef738..0x002ef748: a non-zero global check forces state 9.
    if (AsdNode_HasState() != 0) {
        process->state = 9;
        process->flag_1a = flag;
        return process->move;
    }

    if (movie_index == -1) {
        // 0x002ef7c0..0x002ef7d0: no movie selected.
        process->state = 0;
        process->flag_5b = 1;
        process->flag_18 = 0;
        process->flag_19 = 0;
        process->flag_1a = flag;
        return process->move;
    }

    // 0x002ef754..0x002ef76c: "%s/%s.moflex" with "rom:/moflex" and the
    // per-index name at 0x0044d060.
    char path[0x40];
    UiText_Format(path, "%s/%s.moflex", "rom:/moflex", g_MobiclipMovieNames[movie_index]);

    process->state = 2;                                  // 0x002ef770
    AsdString_Strcpy(process->path, path);               // 0x002ef77c
    process->flag_5b = 0;                                // 0x002ef784
    process->flag_18 = 0;                                // 0x002ef788
    process->field_6c = 0.0f;                            // 0x002ef78c
    process->field_70 = 0;                               // 0x002ef794

    if (movie_index == 3) {
        // 0x002ef798..0x002ef79c
        process->flag_18 = 1;
        process->flag_1a = flag;
        return process->move;
    }

    // 0x002ef7a0..0x002ef7b8: 0x18/0x19 and 0x0b/0x0d/0x10 share the
    // "alternate frame" marker.
    if (movie_index == 0x18 || movie_index == 0x19 ||
        movie_index == 0x0b || movie_index == 0x0d || movie_index == 0x10) {
        process->flag_19 = 1;                            // 0x002ef7d4
    }

    process->flag_1a = flag;                             // 0x002ef7dc
    return process->move;                                // 0x002ef7d8/0x002ef7d8
}

// ---------------------------------------------------------------------------
// helper_S4FsReader (0x0034E028)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0034e028, 520)
u32 helper_S4FsReader_func_0034e028(S4FsReader* reader, void* file, void* sink)
{
    reader->file = file;                                 // 0x0034e038

    // 0x0034e03c..0x0034e048: virtual call through vtable+0x24 returns the
    // stream length.
    void** vtable = *static_cast<void***>(file);
    using SizeFn = u32 (*)(void*);
    const u64 stream_size = static_cast<u32>(
        reinterpret_cast<SizeFn>(vtable[0x24 / 4])(file));
    reader->file_size = stream_size;                     // 0x0034e050
    reader->sink = sink;                                 // 0x0034e054

    // 0x0034e058..0x0034e06c: vtable[0](sink, 0x40000, 4) returns the
    // 0x40000-element transfer buffer.
    void** sink_vtable = *static_cast<void***>(sink);
    using AllocFn = void* (*)(void*, u32, u32);
    reader->buffer = reinterpret_cast<AllocFn>(sink_vtable[0])(sink, 0x40000, 4); // 0x0034e078

    reader->field_00 = 0;                                // 0x0034e08c
    reader->field_04 = 0;
    reader->field_08 = 0;                                // 0x0034e090
    reader->field_0c = 0;
    reader->field_18 = 0;                                // 0x0034e09c
    reader->field_1c = 0;

    AsdMemBlock_InitLock(&reader->lock);                 // 0x0034e0a0

    // 0x0034e0a4..0x0034e108: two event objects; failure is reported through
    // 0x002C5468 rather than propagated.
    u32 event = 0;
    s32 result = AsdEvent_Create(&event, 0);
    if (result >= 0) {
        reader->event_a = event;                         // 0x0034e0cc
    } else {
        AsdKernel_AbortOnFailure(result);                // 0x0034e0d4
    }

    event = 0;
    result = AsdEvent_Create(&event, 0);
    if (result >= 0) {
        reader->event_b = event;                         // 0x0034e100
    } else {
        AsdKernel_AbortOnFailure(result);                // 0x0034e108
    }

    reader->event_a_ptr = &reader->event_a;              // 0x0034e114
    reader->event_b_ptr = &reader->event_b;

    // 0x0034e118..0x0034e140: 0x1000-byte work area from the 0x10000 arena.
    g_S4FsReader.work_buffer = AsdWork_Alloc(0x100, 0x100, 0, 0x1000, 0x1000, 1);
    g_S4FsReader.heap = smt4::engine::AsdMemory_func_002c23f8(0x18);   // 0x0034e154
    if (g_S4FsReader.heap != nullptr) {
        // 0x0034e164..0x0034e174
        *static_cast<u32*>(g_S4FsReader.heap) = 0;
        *reinterpret_cast<u32*>(static_cast<u8*>(g_S4FsReader.heap) + 4) = 0;
        *reinterpret_cast<u32*>(static_cast<u8*>(g_S4FsReader.heap) + 8) = 0;
        *reinterpret_cast<u32*>(static_cast<u8*>(g_S4FsReader.heap) + 0xc) = 0;
        *reinterpret_cast<u8*>(static_cast<u8*>(g_S4FsReader.heap) + 0x10) = 0;
    }

    AsdHeap_Init(g_S4FsReader.heap, g_S4FsReader.work_buffer, 0x1000); // 0x0034e184

    // 0x0034e188..0x0034e1e0: thread descriptor {4, 0x003F7100,
    // 0x003F7224, 0x003F71B8}; the context argument is `reader` itself.
    struct ThreadDesc {
        u32 a;
        u32 b;
        u32 c;
        u32 d;
    } desc = {4, kS4FsReaderDesc0, kS4FsReaderDesc1, kS4FsReaderDesc2};
    void* thread_arg = reader;
    const u8* heap = static_cast<const u8*>(g_S4FsReader.heap);
    const u32 stack_size = *reinterpret_cast<const u32*>(heap + 0x08) +
                           *reinterpret_cast<const u32*>(heap + 0x0c); // 0x0034e1c8
    result = AsdThread_Create(reader->thread, &desc,
                              reinterpret_cast<void*>(kS4FsReaderEntry),
                              static_cast<void*>(&thread_arg), stack_size, 4, -1); // 0x0034e1e0
    if (result < 0) {
        AsdKernel_AbortOnFailure(result);                // 0x0034e1ec
    }

    // 0x0034e1f0..0x0034e204: `svc #0x18` on reader->event_a
    // (signal-event); a negative result aborts.
    result = AsdEvent_Signal(reader->event_a);
    if (result < 0) {
        AsdKernel_AbortOnFailure(result);
    }

    return 1;                                            // 0x0034e20c
}

// ---------------------------------------------------------------------------
// helper_S4AudioDevice (0x0034E64C)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0034e64c, 476)
u32 helper_S4AudioDevice_func_0034e64c(void* device, u32 count,
                                       void* data, u32 size)
{
    AsdSound_InitDsp();                                  // 0x0034e664

    // 0x0034e668..0x0034e690: a provided wave buffer is installed, otherwise
    // the default output is opened.
    if (data != nullptr && size != 0) {
        nn_sdk_func_0035a52c(data, size, 0xff, 0xff);    // 0x0034e684
    } else {
        AsdSound_OpenDefault();                          // 0x0034e690
    }

    AsdSound_InitOutput();                               // 0x0034e698
    AsdSound_SetMasterVolume(1.0f);                            // 0x0034e69c/0x0034e6a4

    if (g_S4AudioDevice.device != nullptr) {
        return 0;                                        // 0x0034e6b4
    }

    // 0x0034e6bc..0x0034e6e4: publish the owner/count and allocate
    // count*0x70 bytes through vtable[0].
    g_S4AudioDevice.count = count;
    g_S4AudioDevice.device = device;
    void** vtable = *static_cast<void***>(device);
    using AllocFn = void* (*)(void*, u32, u32);
    const u32 buffer_size = count * 0x70;                // `rsb`/`lsl #4` at 0x0034e6c8..0x0034e6d0
    g_S4AudioDevice.buffer = reinterpret_cast<AllocFn>(vtable[0])(device, buffer_size, 4);

    if (g_S4AudioDevice.buffer == nullptr) {
        // 0x0034e7ec..0x0034e7fc
        g_S4AudioDevice.device = nullptr;
        g_S4AudioDevice.count = 0;
        return 0;
    }

    AsdMem_Zero(g_S4AudioDevice.buffer, buffer_size);     // 0x0034e6fc
    g_S4AudioDevice.field_18 = 0;                        // 0x0034e700
    g_S4AudioDevice.field_1c = 0;                        // 0x0034e704

    AsdMemBlock_InitLock(&g_MobiclipLock);               // 0x0034e70c

    // 0x0034e710..0x0034e738: 0x1000-byte work area and 0x18-byte heap header.
    g_S4AudioDevice.heap_buffer = AsdWork_Alloc(0x100, 0x100, 0, 0x1000, 0x1000, 1);
    g_S4AudioDevice.heap = smt4::engine::AsdMemory_func_002c23f8(0x18); // 0x0034e748
    if (g_S4AudioDevice.heap != nullptr) {
        // 0x0034e758..0x0034e768
        *static_cast<u32*>(g_S4AudioDevice.heap) = 0;
        *reinterpret_cast<u32*>(static_cast<u8*>(g_S4AudioDevice.heap) + 4) = 0;
        *reinterpret_cast<u32*>(static_cast<u8*>(g_S4AudioDevice.heap) + 8) = 0;
        *reinterpret_cast<u32*>(static_cast<u8*>(g_S4AudioDevice.heap) + 0xc) = 0;
        *reinterpret_cast<u8*>(static_cast<u8*>(g_S4AudioDevice.heap) + 0x10) = 0;
    }

    AsdHeap_Init(g_S4AudioDevice.heap, g_S4AudioDevice.heap_buffer, 0x1000); // 0x0034e778

    // 0x0034e77c..0x0034e7d0: thread descriptor {4, 0x00123BAC,
    // 0x00123BD8, 0x00123BC8}; the context argument is the zero word at
    // sp+0x18 (`str r4,[sp,#0x18]` with r4=0 at 0x0034e77c).
    struct ThreadDesc {
        u32 a;
        u32 b;
        u32 c;
        u32 d;
    } desc = {4, kS4AudioDeviceDesc0, kS4AudioDeviceDesc1, kS4AudioDeviceDesc2};
    void* thread_arg = nullptr;
    const u8* heap = static_cast<const u8*>(g_S4AudioDevice.heap);
    const u32 stack_size = *reinterpret_cast<const u32*>(heap + 0x08) +
                           *reinterpret_cast<const u32*>(heap + 0x0c); // 0x0034e7c8
    s32 result = AsdThread_Create(g_S4AudioThread, &desc,
                                  reinterpret_cast<void*>(kS4AudioDeviceEntry),
                                  static_cast<void*>(&thread_arg),
                                  stack_size, 2, -1);    // 0x0034e7d0
    if (result < 0) {
        AsdKernel_AbortOnFailure(result);                // 0x0034e7dc
    }

    return 1;                                            // 0x0034e7e0
}

// ---------------------------------------------------------------------------
// helper_S4Player (0x003516A8)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x003516a8, 552)
u32 helper_S4Player_func_003516a8(S4Player* player, u32 source, void* data,
                                  void* frame, void* arg4, void* arg5)
{
    // 0x003516bc..0x003516d0: reject a null source/data/frame/arg4.
    if (source == 0 || data == nullptr || frame == nullptr || arg4 == nullptr) {
        return 0;
    }

    // 0x003516d4..0x003516e8: publish the five inputs.
    player->data = data;
    player->frame = frame;
    player->frame_arg = arg4;
    player->frame_arg2 = arg5;
    player->source = source;

    // 0x003516f0..0x0035175c: clear the player state.
    player->field_0c = 0;
    player->field_558 = 0;
    player->field_554 = 0;
    player->field_550 = 0;
    player->field_548 = 0xffffffff;
    player->field_484 = 0;
    player->field_2e8 = 0;
    player->field_46c = 0xffffffff;
    player->field_1c4 = 0;
    player->field_474 = 0;
    player->field_47c = 0;
    player->field_470 = 0xffffffff;
    player->field_478 = 0;
    player->field_480 = 0;
    player->flag_54c = 0;
    player->field_130 = 0;
    player->field_134 = 0;
    player->field_1c = 0;
    player->field_140 = 0;
    player->field_150 = 0;
    player->field_154 = 0;
    player->field_144 = 0;
    player->field_148 = 0;
    player->field_14c = 0;

    AsdDecoder_Reset(player->decoder);                   // 0x00351768

    // 0x0035176c..0x00351784: reset the synchronisation object and lock.
    AsdSync_Set(&player->sync, 1);                       // 0x00351774
    AsdMemBlock_InitLock(&player->lock);                 // 0x0035177c
    AsdSync_Reset(&player->sync);                        // 0x00351784

    player->flag_10 = 0;                                 // 0x00351788
    player->flag_11 = 0;                                 // 0x00351794

    // 0x0035179c..0x003517b8: 0x2000-byte work area.
    g_S4Player.work_buffer = AsdWork_Alloc(0x100, 0x100, 0, 0x2000, 0x1000, 1);
    g_S4Player.heap = smt4::engine::AsdMemory_func_002c23f8(0x18);     // 0x003517cc
    if (g_S4Player.heap != nullptr) {
        // 0x003517d8..0x003517e8
        *static_cast<u32*>(g_S4Player.heap) = 0;
        *reinterpret_cast<u32*>(static_cast<u8*>(g_S4Player.heap) + 4) = 0;
        *reinterpret_cast<u32*>(static_cast<u8*>(g_S4Player.heap) + 8) = 0;
        *reinterpret_cast<u32*>(static_cast<u8*>(g_S4Player.heap) + 0xc) = 0;
        *reinterpret_cast<u8*>(static_cast<u8*>(g_S4Player.heap) + 0x10) = 0;
    }

    AsdHeap_Init(g_S4Player.heap, g_S4Player.work_buffer, 0x2000); // 0x003517f8

    // 0x003517fc..0x00351850: thread descriptor {4, 0x003F7110,
    // 0x003F7228, 0x003F71C4} and context argument `player`.
    struct ThreadDesc {
        u32 a;
        u32 b;
        u32 c;
        u32 d;
    } desc = {4, kS4PlayerDesc0, kS4PlayerDesc1, kS4PlayerDesc2};
    void* thread_arg = player;
    const u8* heap = static_cast<const u8*>(g_S4Player.heap);
    const u32 stack_size = *reinterpret_cast<const u32*>(heap + 0x08) +
                           *reinterpret_cast<const u32*>(heap + 0x0c); // 0x00351840
    s32 result = AsdThread_Create(player->thread, &desc,
                                  reinterpret_cast<void*>(kS4PlayerEntry),
                                  static_cast<void*>(&thread_arg),
                                  stack_size, 0x11, -1); // 0x00351850
    if (result < 0) {
        AsdKernel_AbortOnFailure(result);                // 0x0035185c
    }

    return 1;                                            // 0x00351864
}

} // namespace smt4::nn
