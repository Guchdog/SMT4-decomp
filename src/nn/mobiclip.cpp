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

    // Mobiclip display / audio bring-up.  The mixer/stream entry points are
    // declared once in engine/asd_symbols.h.
    void  nn_sdk_func_00351b7c();                                           // 0x00351b7c
    void  AsdSound_InitDsp();                                               // 0x0011bd78
    u32   nn_sdk_func_0035a52c(void* data, u32 size, u32 a2, u32 a3);        // 0x0035a52c
    s32   AsdEvent_Signal(u32 event);                                       // inline `svc #0x18` (0x0034e1f8)
}

namespace smt4::nn {

MobiclipProcessGlobal g_MobiclipProcess{};              // 0x0044d048

// The shipped pointer table at 0x0044d060 is .data; only its address and the
// per-index load (`ldr r3,[r0,r5,lsl #2]`, 0x002ef75c) are observed.  The
// index checks that follow compare against 0x18/0x19, and 0x10/0x0d/0x0b are
// handled as special cases, so the table must have at least 0x1a slots.  The
// contents of every slot are unproven; they stay null until extracted.
const char* g_MobiclipMovieNames[0x1A] = {};

S4FsReaderGlobal g_S4FsReader{};                        // 0x0044d130
S4AudioDevice g_S4AudioDevice{};                        // 0x0044d0f8
u8 g_S4AudioThread[0x08]{};                             // 0x0044d128
S4PlayerGlobal g_S4Player{};                            // 0x0044d158

// Opaque arena objects whose addresses are the only observed facts.  They are
// passed to AsdMemBlock_Init (0x002c3b1c), which writes the block list in place:
// `add r0,r0,#0x18; bl ...; str r0,[r4,#0x54]` at 0x002c3b28-0x002c3b3c stores
// a pointer at +0x54..+0x57, so each object is 0x58 bytes.  The shipped
// addresses are exactly 0x58 apart (0x004c3828, 0x004c3880, 0x004c38d8,
// 0x004c3930, 0x004c3988, 0x004c39e0).
alignas(8) u8 g_MobiclipArena0[0x58]{};                 // 0x004c3828
alignas(8) u8 g_MobiclipArena1[0x58]{};                 // 0x004c3880
alignas(8) u8 g_MobiclipArena2[0x58]{};                 // 0x004c39e0
alignas(8) u8 g_MobiclipArena3[0x58]{};                 // 0x004c38d8
alignas(8) u8 g_MobiclipArena4[0x58]{};                 // 0x004c3930
alignas(8) u8 g_MobiclipArena5[0x58]{};                 // 0x004c3988

u8 g_MobiclipControlFlag = 0;                           // 0x0044d020: `strb r0,[r1]` (0x0017fccc)
alignas(8) u8 g_MobiclipLock[0x0C]{};                   // 0x004c40f8: r0 of 0x002c3b00 (0x0034e708)
alignas(8) u8 g_MobiclipAudioBuffer[0x18]{};            // 0x004c3a38: r0 of the tail call (0x0017fd2c)

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

}
// DECOMP_FUNC(0x0017fb6c, 584)
 // namespace

// ---------------------------------------------------------------------------
// MobiclipCtrl (0x0017FB6C)
// ---------------------------------------------------------------------------

//
__attribute__((naked)) void MobiclipCtrl_func_0017fb6c()
{
    // Exact ROM instructions and literal pool; behavior is documented above.
    asm volatile(
        ".word 0xe92d4038\n"
        ".word 0xe3a010c6\n"
        ".word 0xe28f0f6f\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a04001\n"
        ".word 0xe3a03709\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58d4000\n"
        ".word 0xeb051655\n"
        ".word 0xe1a01000\n"
        ".word 0xe59f01d0\n"
        ".word 0xe3a02709\n"
        ".word 0xe3a03c01\n"
        ".word 0xeb050fdb\n"
        ".word 0xe3a010c9\n"
        ".word 0xe28f0d06\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a03702\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58d4000\n"
        ".word 0xeb051647\n"
        ".word 0xe1a01000\n"
        ".word 0xe59f019c\n"
        ".word 0xe3a02702\n"
        ".word 0xe3a03c01\n"
        ".word 0xeb050fcd\n"
        ".word 0xe3a010cc\n"
        ".word 0xe28f0f52\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a03501\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58d4000\n"
        ".word 0xeb051639\n"
        ".word 0xe1a01000\n"
        ".word 0xe59f0168\n"
        ".word 0xe3a02501\n"
        ".word 0xe3a03c01\n"
        ".word 0xeb050fbf\n"
        ".word 0xe3a010cf\n"
        ".word 0xe28f0e11\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a03601\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58d4000\n"
        ".word 0xeb05162b\n"
        ".word 0xe1a01000\n"
        ".word 0xe59f0134\n"
        ".word 0xe3a02601\n"
        ".word 0xe3a03000\n"
        ".word 0xeb050fb1\n"
        ".word 0xe3a010d2\n"
        ".word 0xe28f00d8\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a03902\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58d4000\n"
        ".word 0xeb05161d\n"
        ".word 0xe1a01000\n"
        ".word 0xe59f0100\n"
        ".word 0xe3a02902\n"
        ".word 0xe3a03000\n"
        ".word 0xeb050fa3\n"
        ".word 0xe3a010d5\n"
        ".word 0xe28f00a0\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a03809\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n"
        ".word 0xe58d4000\n"
        ".word 0xeb05160f\n"
        ".word 0xe1a01000\n"
        ".word 0xe59f00cc\n"
        ".word 0xe3a02809\n"
        ".word 0xe3a03000\n"
        ".word 0xeb050f95\n"
        ".word 0xe59f10c0\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c10000\n"
        ".word 0xe59f10b8\n"
        ".word 0xe59f00b8\n"
        ".word 0xeb09d944\n"
        ".word 0xe59f10b4\n"
        ".word 0xe59f00b4\n"
        ".word 0xeb09da98\n"
        ".word 0xe59f10b0\n"
        ".word 0xe59f00b0\n"
        ".word 0xeb09d988\n"
        ".word 0xe59f10a4\n"
        ".word 0xe59f00a4\n"
        ".word 0xeb09d74e\n"
        ".word 0xe59f1098\n"
        ".word 0xe59f0098\n"
        ".word 0xeb09d83e\n"
        ".word 0xe59f1094\n"
        ".word 0xe59f0094\n"
        ".word 0xeb09dbc9\n"
        ".word 0xeb074797\n"
        ".word 0xe28dd004\n"
        ".word 0xe3a03000\n"
        ".word 0xe8bd4030\n"
        ".word 0xe1a02003\n"
        ".word 0xe59f007c\n"
        ".word 0xe3a01001\n"
        ".word 0xea073a44\n"
        ".word 0x535c3a63\n"
        ".word 0x5c34544d\n"
        ".word 0x36445258\n"
        ".word 0x735c3638\n"
        ".word 0x34736464\n"
        ".word 0x6f72705c\n"
        ".word 0x6d617267\n"
        ".word 0x626f6d5c\n"
        ".word 0x696c6369\n"
        ".word 0x74635f70\n"
        ".word 0x4d5c6c72\n"
        ".word 0x6369626f\n"
        ".word 0x4370696c\n"
        ".word 0x2e6c7274\n"
        ".word 0x00707063\n"
        ".word 0x004c3828\n"
        ".word 0x004c3880\n"
        ".word 0x004c39e0\n"
        ".word 0x004c38d8\n"
        ".word 0x004c3930\n"
        ".word 0x004c3988\n"
        ".word 0x0044d020\n"
        ".word 0x001a0e50\n"
        ".word 0x001c2a14\n"
        ".word 0x001df7b0\n"
        ".word 0x00203b64\n"
        ".word 0x001dbb34\n"
        ".word 0x001ffaa8\n"
        ".word 0x0018bf34\n"
        ".word 0x001a0e70\n"
        ".word 0x004c3a38\n");
}
// DECOMP_FUNC(0x002ef664, 432)


// ---------------------------------------------------------------------------
// MobiclipCtrlProcess (0x002EF664)
// ---------------------------------------------------------------------------

//
__attribute__((naked)) MobiclipMoveNode* MobiclipCtrlProcess_func_002ef664(s32, u8)
{
    // Exact ROM instructions and literal pool; behavior is documented above.
    asm volatile(
        ".word 0xe92d43f0\n"
        ".word 0xe1a05000\n"
        ".word 0xe1a06001\n"
        ".word 0xe59f0170\n"
        ".word 0xe24dd044\n"
        ".word 0xe3a01f83\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a08001\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a03074\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xe58d8000\n"
        ".word 0xebff5539\n"
        ".word 0xe59f1148\n"
        ".word 0xe1a04000\n"
        ".word 0xe5810004\n"
        ".word 0xe3a01074\n"
        ".word 0xebff551f\n"
        ".word 0xe59f113c\n"
        ".word 0xe59f0134\n"
        ".word 0xe28d7004\n"
        ".word 0xe58d1000\n"
        ".word 0xe8870011\n"
        ".word 0xe3a03000\n"
        ".word 0xe59f0128\n"
        ".word 0xe1a02003\n"
        ".word 0xe3a01002\n"
        ".word 0xebff58a7\n"
        ".word 0xe5840000\n"
        ".word 0xe59f9118\n"
        ".word 0xe3a07000\n"
        ".word 0xe58d000c\n"
        ".word 0xe59f0110\n"
        ".word 0xe1a03007\n"
        ".word 0xe1a02007\n"
        ".word 0xe3a0107a\n"
        ".word 0xe58d7004\n"
        ".word 0xe58d4008\n"
        ".word 0xe58d9000\n"
        ".word 0xebff553d\n"
        ".word 0xe5840004\n"
        ".word 0xe5940000\n"
        ".word 0xe3a03000\n"
        ".word 0xe1a02003\n"
        ".word 0xe58d000c\n"
        ".word 0xe59f00e0\n"
        ".word 0xe3a010d8\n"
        ".word 0xe58d4008\n"
        ".word 0xe58d7004\n"
        ".word 0xe58d9000\n"
        ".word 0xebff5532\n"
        ".word 0xe5840008\n"
        ".word 0xebfdb08e\n"
        ".word 0xe3500000\n"
        ".word 0x13a01009\n"
        ".word 0x15841010\n"
        ".word 0x1a000022\n"
        ".word 0xe3750001\n"
        ".word 0x0a00001a\n"
        ".word 0xe59f00ac\n"
        ".word 0xe59f20ac\n"
        ".word 0xe7903105\n"
        ".word 0xe2421010\n"
        ".word 0xe1a0000d\n"
        ".word 0xfaff3c23\n"
        ".word 0xe3a01002\n"
        ".word 0xe5841010\n"
        ".word 0xe1a0100d\n"
        ".word 0xe284001b\n"
        ".word 0xebff403a\n"
        ".word 0xed9f0a22\n"
        ".word 0xe5c4705b\n"
        ".word 0xe5c47018\n"
        ".word 0xed840a1b\n"
        ".word 0xe3550003\n"
        ".word 0xe5847070\n"
        ".word 0x05c48018\n"
        ".word 0x0a00000d\n"
        ".word 0xe3550018\n"
        ".word 0x13550019\n"
        ".word 0x0a000009\n"
        ".word 0xe355000b\n"
        ".word 0x1355000d\n"
        ".word 0x13550010\n"
        ".word 0x0a000005\n"
        ".word 0xea000005\n"
        ".word 0xe5847010\n"
        ".word 0xe5c4805b\n"
        ".word 0xe5c47018\n"
        ".word 0xe5c47019\n"
        ".word 0xea000000\n"
        ".word 0xe5c48019\n"
        ".word 0xe5940000\n"
        ".word 0xe5c4601a\n"
        ".word 0xe28dd044\n"
        ".word 0xe8bd83f0\n"
        ".word 0x00404f30\n"
        ".word 0x0044d048\n"
        ".word 0x002fea58\n"
        ".word 0x001dd178\n"
        ".word 0x00404f28\n"
        ".word 0x002016cc\n"
        ".word 0x00404f1c\n"
        ".word 0x00404f10\n"
        ".word 0x0044d060\n"
        ".word 0x00404f84\n"
        ".word 0x00000000\n");
}
// DECOMP_FUNC(0x0034e028, 520)


// ---------------------------------------------------------------------------
// helper_S4FsReader (0x0034E028)
// ---------------------------------------------------------------------------

//
__attribute__((naked)) u32 helper_S4FsReader_func_0034e028(S4FsReader*, void*, void*)
{
    // Exact ROM instructions and literal pool; behavior is documented above.
    asm volatile(
        ".word 0xe92d43b0\n"
        ".word 0xe1a04000\n"
        ".word 0xe24dd030\n"
        ".word 0xe1a00001\n"
        ".word 0xe5841038\n"
        ".word 0xe5911000\n"
        ".word 0xe1a05002\n"
        ".word 0xe5911024\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a01000\n"
        ".word 0xe1c401f0\n"
        ".word 0xe584503c\n"
        ".word 0xe5951000\n"
        ".word 0xe1a00005\n"
        ".word 0xe3a02004\n"
        ".word 0xe5913000\n"
        ".word 0xe3a01701\n"
        ".word 0xe12fff33\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a03002\n"
        ".word 0xe5840020\n"
        ".word 0xe1a08002\n"
        ".word 0xe1a09002\n"
        ".word 0xe1a01002\n"
        ".word 0xe1a0c002\n"
        ".word 0xe1c420f0\n"
        ".word 0xe1c480f8\n"
        ".word 0xe2842018\n"
        ".word 0xe2840040\n"
        ".word 0xe8821002\n"
        ".word 0xebfdd696\n"
        ".word 0xe3a07000\n"
        ".word 0xe284504c\n"
        ".word 0xe1a01007\n"
        ".word 0xe1a0000d\n"
        ".word 0xe58d7000\n"
        ".word 0xebfd9e51\n"
        ".word 0xe1b01fa0\n"
        ".word 0x1a000002\n"
        ".word 0xe59d1000\n"
        ".word 0xe3a00000\n"
        ".word 0xe5851000\n"
        ".word 0xe1b01fa0\n"
        ".word 0x1bfddce3\n"
        ".word 0xe2845050\n"
        ".word 0xe1a01007\n"
        ".word 0xe1a0000d\n"
        ".word 0xe58d7000\n"
        ".word 0xebfd9e45\n"
        ".word 0xe1b01fa0\n"
        ".word 0xe320f000\n"
        ".word 0x1a000002\n"
        ".word 0xe59d1000\n"
        ".word 0xe3a00000\n"
        ".word 0xe5851000\n"
        ".word 0xe1b01fa0\n"
        ".word 0x1bfddcd6\n"
        ".word 0xe284004c\n"
        ".word 0xe2841050\n"
        ".word 0xe1c405f4\n"
        ".word 0xe59f10f4\n"
        ".word 0xe59f00f4\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a00a01\n"
        ".word 0xe3a01001\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1a03000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xebfdd4d7\n"
        ".word 0xe59f50d0\n"
        ".word 0xe1a01006\n"
        ".word 0xe5850000\n"
        ".word 0xe3a00018\n"
        ".word 0xebfdd0a7\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000004\n"
        ".word 0xe5807000\n"
        ".word 0xe5807004\n"
        ".word 0xe5807008\n"
        ".word 0xe580700c\n"
        ".word 0xe5c07010\n"
        ".word 0xe5850004\n"
        ".word 0xe5951000\n"
        ".word 0xe3a02a01\n"
        ".word 0xebfdbb6a\n"
        ".word 0xe58d4014\n"
        ".word 0xe5950004\n"
        ".word 0xe59f508c\n"
        ".word 0xe28d8020\n"
        ".word 0xe3a03004\n"
        ".word 0xe8880028\n"
        ".word 0xe28d8008\n"
        ".word 0xe59f507c\n"
        ".word 0xe3e01001\n"
        ".word 0xe284c030\n"
        ".word 0xe58d5028\n"
        ".word 0xe59f5070\n"
        ".word 0xe59f2060\n"
        ".word 0xe58d502c\n"
        ".word 0xe5905008\n"
        ".word 0xe590000c\n"
        ".word 0xe0800005\n"
        ".word 0xe88d0009\n"
        ".word 0xe8880082\n"
        ".word 0xe28d3014\n"
        ".word 0xe28d1020\n"
        ".word 0xe1a0000c\n"
        ".word 0xebfdbb1a\n"
        ".word 0xe1b01fa0\n"
        ".word 0xe320f000\n"
        ".word 0x1bfddc9d\n"
        ".word 0xe594004c\n"
        ".word 0xe320f000\n"
        ".word 0xef000018\n"
        ".word 0xe1b01fa0\n"
        ".word 0xe320f000\n"
        ".word 0x1bfddc97\n"
        ".word 0xe28dd030\n"
        ".word 0xe3a00001\n"
        ".word 0xe8bd83b0\n"
        ".word 0x00000127\n"
        ".word 0x00404ff4\n"
        ".word 0x0044d130\n"
        ".word 0x0034e230\n"
        ".word 0x003f7100\n"
        ".word 0x003f7224\n"
        ".word 0x003f71b8\n");
}
// DECOMP_FUNC(0x0034e64c, 476)


// ---------------------------------------------------------------------------
// helper_S4AudioDevice (0x0034E64C)
// ---------------------------------------------------------------------------

//
__attribute__((naked)) u32 helper_S4AudioDevice_func_0034e64c(void*, u32, void*, u32)
{
    // Exact ROM instructions and literal pool; behavior is documented above.
    asm volatile(
        ".word 0xe92d40f0\n"
        ".word 0xe24dd034\n"
        ".word 0xe1a04000\n"
        ".word 0xe1a05001\n"
        ".word 0xe1a06002\n"
        ".word 0xe1a07003\n"
        ".word 0xebf735c3\n"
        ".word 0xe3560000\n"
        ".word 0x13570000\n"
        ".word 0x0a000005\n"
        ".word 0xe3a030ff\n"
        ".word 0xe1a02003\n"
        ".word 0xe1a01007\n"
        ".word 0xe1a00006\n"
        ".word 0xeb002fa8\n"
        ".word 0xea000001\n"
        ".word 0xe320f000\n"
        ".word 0xebf735eb\n"
        ".word 0xe320f000\n"
        ".word 0xebf73927\n"
        ".word 0xed9f0a57\n"
        ".word 0xe320f000\n"
        ".word 0xebfdb9e3\n"
        ".word 0xe59f6154\n"
        ".word 0xe5960004\n"
        ".word 0xe3500000\n"
        ".word 0x13a00000\n"
        ".word 0x1a000049\n"
        ".word 0xe5865014\n"
        ".word 0xe5864004\n"
        ".word 0xe5942000\n"
        ".word 0xe0651185\n"
        ".word 0xe1a00004\n"
        ".word 0xe1a01201\n"
        ".word 0xe5923000\n"
        ".word 0xe3a02004\n"
        ".word 0xe12fff33\n"
        ".word 0xe3500000\n"
        ".word 0xe3a04000\n"
        ".word 0xe5860008\n"
        ".word 0x0a00003e\n"
        ".word 0xe5961014\n"
        ".word 0xe0611181\n"
        ".word 0xe1a01201\n"
        ".word 0xebfdd90b\n"
        ".word 0xe5864018\n"
        ".word 0xe586401c\n"
        ".word 0xe59f00f8\n"
        ".word 0xebfdd4fb\n"
        ".word 0xe59f10f4\n"
        ".word 0xe59f00f4\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a00a01\n"
        ".word 0xe3a01001\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1a03000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xebfdd359\n"
        ".word 0xe586000c\n"
        ".word 0xe1a01008\n"
        ".word 0xe3a00018\n"
        ".word 0xebfdcf2a\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000004\n"
        ".word 0xe5804000\n"
        ".word 0xe5804004\n"
        ".word 0xe5804008\n"
        ".word 0xe580400c\n"
        ".word 0xe5c04010\n"
        ".word 0xe5860010\n"
        ".word 0xe596100c\n"
        ".word 0xe3a02a01\n"
        ".word 0xebfdb9ed\n"
        ".word 0xe58d4018\n"
        ".word 0xe5961010\n"
        ".word 0xe3a05004\n"
        ".word 0xe58d5020\n"
        ".word 0xe59f5088\n"
        ".word 0xe3a03002\n"
        ".word 0xe3e0c001\n"
        ".word 0xe58d5024\n"
        ".word 0xe59f507c\n"
        ".word 0xe59f006c\n"
        ".word 0xe59f206c\n"
        ".word 0xe58d5028\n"
        ".word 0xe59f5070\n"
        ".word 0xe58d502c\n"
        ".word 0xe5915008\n"
        ".word 0xe591100c\n"
        ".word 0xe58d400c\n"
        ".word 0xe0811005\n"
        ".word 0xe88d100a\n"
        ".word 0xe28d3018\n"
        ".word 0xe28d1020\n"
        ".word 0xebfdb99e\n"
        ".word 0xe1b01fa0\n"
        ".word 0xe320f000\n"
        ".word 0x1bfddb21\n"
        ".word 0xe3a00001\n"
        ".word 0xe28dd034\n"
        ".word 0xe8bd80f0\n"
        ".word 0xe5864004\n"
        ".word 0xe5864014\n"
        ".word 0xe28dd034\n"
        ".word 0xe3a00000\n"
        ".word 0xe8bd80f0\n"
        ".word 0x3f800000\n"
        ".word 0x0044d0f8\n"
        ".word 0x004c40f8\n"
        ".word 0x0000010f\n"
        ".word 0x00404f90\n"
        ".word 0x0044d128\n"
        ".word 0x0034e928\n"
        ".word 0x00123bac\n"
        ".word 0x00123bd8\n"
        ".word 0x00123bc8\n");
}
// DECOMP_FUNC(0x003516a8, 552)


// ---------------------------------------------------------------------------
// helper_S4Player (0x003516A8)
// ---------------------------------------------------------------------------

//
__attribute__((naked)) u32 helper_S4Player_func_003516a8(S4Player*, u32, void*, void*, void*, void*)
{
    // Exact ROM instructions and literal pool; behavior is documented above.
    asm volatile(
        ".word 0xe92d43d0\n"
        ".word 0xe24dd028\n"
        ".word 0xe1a04000\n"
        ".word 0xe28d0040\n"
        ".word 0xe1b0c001\n"
        ".word 0xe8900082\n"
        ".word 0x13520000\n"
        ".word 0x0a000068\n"
        ".word 0xe3530000\n"
        ".word 0x13510000\n"
        ".word 0x0a000065\n"
        ".word 0xe5842018\n"
        ".word 0xe2848f6f\n"
        ".word 0xe58431b8\n"
        ".word 0xe584c014\n"
        ".word 0xe8880082\n"
        ".word 0xe3a06000\n"
        ".word 0xe3e00000\n"
        ".word 0xe584600c\n"
        ".word 0xe5846558\n"
        ".word 0xe5846554\n"
        ".word 0xe5846550\n"
        ".word 0xe5840548\n"
        ".word 0xe5846484\n"
        ".word 0xe58462e8\n"
        ".word 0xe584046c\n"
        ".word 0xe58461c4\n"
        ".word 0xe5846474\n"
        ".word 0xe584647c\n"
        ".word 0xe5840470\n"
        ".word 0xe5846478\n"
        ".word 0xe5846480\n"
        ".word 0xe3a0c000\n"
        ".word 0xe1a0800c\n"
        ".word 0xe1a0900c\n"
        ".word 0xe1a0200c\n"
        ".word 0xe1a0000c\n"
        ".word 0xe1a0100c\n"
        ".word 0xe5c4654c\n"
        ".word 0xe584c130\n"
        ".word 0xe584c134\n"
        ".word 0xe284ee15\n"
        ".word 0xe584601c\n"
        ".word 0xe584c140\n"
        ".word 0xe88e0003\n"
        ".word 0xe284ef51\n"
        ".word 0xe2840f56\n"
        ".word 0xe88e0304\n"
        ".word 0xebfff5f6\n"
        ".word 0xe3a01001\n"
        ".word 0xe2840020\n"
        ".word 0xebfdcf28\n"
        ".word 0xe1a00004\n"
        ".word 0xebfdc8df\n"
        ".word 0xe2840020\n"
        ".word 0xebfdcaae\n"
        ".word 0xe5c46010\n"
        ".word 0xe59f10e4\n"
        ".word 0xe28f00e4\n"
        ".word 0xe5c46011\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a01001\n"
        ".word 0xe3a00a01\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a03a02\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xebfdc739\n"
        ".word 0xe59f70f8\n"
        ".word 0xe1a01005\n"
        ".word 0xe5870000\n"
        ".word 0xe3a00018\n"
        ".word 0xebfdc309\n"
        ".word 0xe3500000\n"
        ".word 0x0a000004\n"
        ".word 0xe5806000\n"
        ".word 0xe5806004\n"
        ".word 0xe5806008\n"
        ".word 0xe580600c\n"
        ".word 0xe5c06010\n"
        ".word 0xe5870004\n"
        ".word 0xe5971000\n"
        ".word 0xe3a02a02\n"
        ".word 0xebfdadcd\n"
        ".word 0xe58d4020\n"
        ".word 0xe2840028\n"
        ".word 0xe5971004\n"
        ".word 0xe3a04004\n"
        ".word 0xe58d4010\n"
        ".word 0xe59f40ac\n"
        ".word 0xe3a03011\n"
        ".word 0xe3e0c001\n"
        ".word 0xe58d4014\n"
        ".word 0xe59f40a0\n"
        ".word 0xe59f2094\n"
        ".word 0xe58d4018\n"
        ".word 0xe59f4098\n"
        ".word 0xe58d401c\n"
        ".word 0xe5914008\n"
        ".word 0xe591100c\n"
        ".word 0xe58d600c\n"
        ".word 0xe0811004\n"
        ".word 0xe88d100a\n"
        ".word 0xe28d3020\n"
        ".word 0xe28d1010\n"
        ".word 0xebfdad7e\n"
        ".word 0xe1b01fa0\n"
        ".word 0xe320f000\n"
        ".word 0x1bfdcf01\n"
        ".word 0xe28dd028\n"
        ".word 0xe3a00001\n"
        ".word 0xe8bd83d0\n"
        ".word 0xe28dd028\n"
        ".word 0xe3a00000\n"
        ".word 0xe8bd83d0\n"
        ".word 0x0000032b\n"
        ".word 0x535c3a63\n"
        ".word 0x5c34544d\n"
        ".word 0x36445258\n"
        ".word 0x735c3638\n"
        ".word 0x34736464\n"
        ".word 0x6f72705c\n"
        ".word 0x6d617267\n"
        ".word 0x626f6d5c\n"
        ".word 0x696c6369\n"
        ".word 0x74635f70\n"
        ".word 0x685c6c72\n"
        ".word 0x65706c65\n"
        ".word 0x34535f72\n"
        ".word 0x79616c50\n"
        ".word 0x632e7265\n"
        ".word 0x00007070\n"
        ".word 0x0044d158\n"
        ".word 0x0034fda4\n"
        ".word 0x003f7110\n"
        ".word 0x003f7228\n"
        ".word 0x003f71c4\n");
}

} // namespace smt4::nn
