#include "engine/asd_sound.h"
#include "engine/asd_symbols.h"
#include <cstdint>

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

extern "C" {
    // Shared helpers (AsdString_Strcpy, AsdMem_CopyFrom) come from
    // engine/asd_symbols.h.

    // Allocators / locks
    void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);         // 0x002c4b84
    void* AsdMem_AllocAlign(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);    // 0x002c54f0
    void* AsdWork_Alloc2(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 flag);// 0x002bf798

    // soundEffect
    u32   AsdSoundEffect_Configure(void* unit, const void* config);         // 0x00110c60
    u32   AsdSoundEffect_GetBufferSize(const void* unit);                   // 0x00110c44
    u32   AsdSoundEffect_SetBuffer(void* unit, void* buffer, u32 size);     // 0x00110c2c
    u32   AsdSoundEffect2_Configure(void* unit, const void* config);        // 0x00121208
    u32   AsdSoundEffect2_GetBufferSize(const void* unit);                  // 0x00121168
    u32   AsdSoundEffect2_SetBuffer(void* unit, void* buffer, u32 size);    // 0x00121150
    u32   AsdSound_Dispatch(u32 mode, void* unit);                          // 0x00120ce4

    // AsdSoundSystem
    u32   AsdSound_HasState(const void* state);                             // 0x002bf85c
    void  AsdSound_Shutdown();                                              // 0x001176e0
    u32   AsdSound_OpenArchive(void* system, const char* path);             // 0x00121744
    u32   AsdSound_GetBlockSize(const void* container);                     // 0x00132a20 (0x2001 tag)
    u32   AsdSound_GetStreamBlockSize(const void* container);               // 0x00132aa0 (0x2000 tag)
    // 0x00121F20 / 0x00121F40 / 0x00122094 ignore r0 and derive the size from
    // r1, so the owner pointer is the meaningful argument (r0 still carries the
    // container at every call site).
    u32   AsdSound_GetDataSize(const void* container, const void* owner);    // 0x00121f20
    u32   AsdSound_GetContainerSize(const void* container, const void* owner);// 0x00121f40
    u32   AsdSound_GetSampleBytes(const void* container, const void* owner); // 0x00122094
    u32   AsdSound_LoadData(void* system, const void* data, u32 size);      // 0x001215ec
    u32   AsdSound_LoadDataPersistent(void* system, const void* data, u32 size); // 0x00121694
    u32   AsdSound_ParseContainer(void* container, void* owner, void* buffer,
                                  u32 size);                                // 0x00120f50
    u32   AsdSound_SetupContainer(void* container, void* owner, void* source,
                                  void* block, u32 block_size, void* buffer,
                                  u32 buffer_size);                         // 0x0012105c
    s32   AsdSound_InitDsp();                                               // 0x0011bd78
    void  AsdSound_SetPhase(s32 phase);                                     // 0x0012a664
    void  AsdSound_RequestMode(u32 mode);                                   // 0x0011cc34
    u32   AsdSound_CreateEngine(const smt4::engine::AsdSoundInitConfig* config); // 0x00120d44
    void  AsdSound_InitEngine(const smt4::engine::AsdSoundInitConfig* config,
                              void* buffer, u32 size);                      // 0x00120ac8

    // Voice helpers
    void  AsdSoundVoice_InitSlot(void* slot, void* container, void* voice);// 0x00120dd4
    void  AsdSoundVoice_SetTarget(void* slot, const f32* mix);              // 0x00120e14
    u32   AsdSoundVoice_AttachBuffer(void* voice, void* container, void* buffer,
                                     u32 size);                             // 0x00120e68
    u32   AsdSoundVoice_GetBufferSize(const void* voice);                   // 0x00120ef4
    u32   AsdSoundVoice_Stop(void* voice, u32 release);                     // 0x002bdc08
    void  AsdSoundSlot_Stop(void* slot, u32 handle);                        // 0x002bd3fc
    void* AsdSoundSlot_Attach(void* slot, void* buffer, u32 size);          // 0x00121a98
    u32   AsdSoundSlot_GetHandle(void* slot);                               // 0x00121b50
    void* AsdSoundVoice_Create(u32 a0, u32 a1, u32 a2);                     // 0x002bd48c
    void  AsdSoundVoice_SetParams(void* voice, const f32* params);          // 0x001537c4
    void  AsdSoundVoice_SetVolume(void* voice, f32 volume);                 // 0x00147288
    void  AsdSoundVoice_SetSpeed(void* voice, f32 speed);                   // 0x002bd46c
    void  AsdSoundVoice_Clear(void* voice);                                 // 0x002bd448
    u32   AsdSoundVoice_Attach(void* voice, void* data, void* a, void* b,
                               u32 index);                                  // 0x00128ff0
    void  AsdSound_UpdateListener(const f32* position, f32 scale);          // 0x00119b48
    s32   AsdFlag_TestAndSet(u32* flag);                                    // 0x002c00d4 (Thumb)
    u32   AsdList_Append(u32* head, u32* tail, u32* node);                  // 0x002bf774
    void* AsdData_GetBase(const void* data);                                // 0x00128f34
    u32   AsdData_GetCount(const void* data);                               // 0x00128f44
    u32   AsdData_GetEntry(const void* data, s32 index);                    // 0x00128f58

}

namespace smt4::engine {

AsdSoundSystem g_AsdSoundSystem{};                      // 0x004E1F68
AsdSoundStreamSettings g_AsdSoundStream{};              // 0x004E3138
AsdSoundSettings g_AsdSoundSettings{};                  // 0x004E30EC
AsdSoundLock g_AsdSoundLock{};                          // 0x004E315C

u8 g_AsdSoundEffectUnitA;                               // 0x004C5484
AsdSoundEffectConfigA g_AsdSoundEffectConfigA{};        // 0x004C54E4
u8 g_AsdSoundEffectUnitB;                               // 0x004C54F4
AsdSoundEffectConfigB g_AsdSoundEffectConfigB{};        // 0x004C5604

void* g_AsdSoundEffectBuffers[2]{};                     // 0x0044E0E0
void* g_SoundTestObject;                                // 0x0044E110
void* g_AsdSoundSystemHandle;                           // 0x004E23E0
u32   g_AsdSoundFlag;                                   // 0x00476628
AsdSoundFloat3 g_AsdSoundMixLevels{};
// DECOMP_FUNC(0x0010368c, 184)
                   // 0x004EFD2C

// ---------------------------------------------------------------------------
// soundEffect (c:\SMT4\XRD686\sdds4\program\sound\soundEffect.cpp)
// ---------------------------------------------------------------------------

// 0x0010368c (184 B): build the first effect unit, then chain into 0x00109524.
//
__attribute__((naked)) void soundEffect_func_0010368c()
{
    asm volatile(
        ".word 0xe92d4038\n" // push {r3, r4, r5, lr}
        ".word 0xe3a00001\n"
        ".word 0xeb070868\n" // AsdSound_GetTableEntry (0x002c583c)
        ".word 0xe3500000\n"
        ".word 0x1a000020\n" // existing table entry skips setup
        ".word 0xe59f0084\n" // config A
        ".word 0xe3a01096\n"
        ".word 0xed9f0a20\n" // 0.1f
        ".word 0xeddf0a20\n" // 0.7f
        ".word 0xe5801000\n"
        ".word 0xe2801004\n"
        ".word 0xe3a05001\n"
        ".word 0xec810a02\n"
        ".word 0xe2801000\n"
        ".word 0xe5c0500c\n"
        ".word 0xe2410060\n" // unit A = config A - 0x60
        ".word 0xeb003563\n" // AsdSoundEffect_Configure (0x00110c60)
        ".word 0xe59f0060\n" // unit A
        ".word 0xeb00355a\n" // AsdSoundEffect_GetBufferSize (0x00110c44)
        ".word 0xe1a04000\n" // preserve size
        ".word 0xe59f0058\n" // source path/line metadata
        ".word 0xe3a01047\n"
        ".word 0xe1a00000\n"
        ".word 0xe1a03004\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n" // allocation region 0x10000
        ".word 0xe58d5000\n" // allocation flag = 1
        ".word 0xeb07077b\n" // AsdMem_AllocAlign (0x002c54f0)
        ".word 0xe59f1038\n" // g_AsdSoundEffectBuffers
        ".word 0xe1a02004\n"
        ".word 0xe5810000\n"
        ".word 0xe1a01000\n"
        ".word 0xe59f0020\n" // unit A
        ".word 0xeb003544\n" // AsdSoundEffect_SetBuffer (0x00110c2c)
        ".word 0xe59f1018\n"
        ".word 0xe3a00000\n"
        ".word 0xeb00756f\n" // AsdSound_Dispatch (0x00120ce4)
        ".word 0xe8bd4038\n"
        ".word 0xea00177d\n" // tail branch to soundEffect_func_00109524
        ".word 0x004c54e4\n"
        ".word 0x3dcccccd\n"
        ".word 0x3f333333\n"
        ".word 0x004c5484\n"
        ".word 0x004077b8\n"
        ".word 0x0044e0e0\n");
}
// DECOMP_FUNC(0x00109524, 240)


// 0x00109524 (240 B): build the second effect unit and register it.
//
__attribute__((naked)) void soundEffect_func_00109524()
{
    asm volatile(
        ".word 0xe92d43f8\n" // push {r3, r4, r5, r6, r7, r8, sb, lr}
        ".word 0xe3a00001\n"
        ".word 0xeb06f0c2\n" // AsdSound_GetTableEntry (0x002c583c)
        ".word 0xe3500000\n"
        ".word 0x1a00002e\n" // existing table entry exits
        ".word 0xe59f00bc\n" // config B
        ".word 0xe3a0605a\n"
        ".word 0xe3a07e4b\n"
        ".word 0xe3a0801e\n"
        ".word 0xe88001c0\n" // config fields +0/+4/+8
        ".word 0xe280600c\n"
        ".word 0xeddf0a2a\n" // 0.4f
        ".word 0xed9f1a2a\n" // 0.5f / 0.8f
        ".word 0xe2801024\n"
        ".word 0xecc60a02\n"
        ".word 0xe3a03ebe\n"
        ".word 0xe3a04ee6\n"
        ".word 0xe3a0ce82\n"
        ".word 0xe8811018\n" // config trailing scalar fields
        ".word 0xe3a05001\n"
        ".word 0xed9f0a1f\n"
        ".word 0xe5801014\n" // config +0x14 points to config +0x24
        ".word 0xed800a06\n"
        ".word 0xed800a07\n"
        ".word 0xe3a02000\n"
        ".word 0xe5c05021\n"
        ".word 0xe2801000\n"
        ".word 0xe5c02020\n"
        ".word 0xe2410e11\n" // unit B = config B - 0x110
        ".word 0xeb005f1a\n" // AsdSoundEffect2_Configure (0x00121208)
        ".word 0xe59f0064\n" // unit B
        ".word 0xeb005ef0\n" // AsdSoundEffect2_GetBufferSize (0x00121168)
        ".word 0xe1a04000\n" // preserve buffer size
        ".word 0xe59f005c\n" // source metadata
        ".word 0xe3a0106c\n"
        ".word 0xe1a00000\n"
        ".word 0xe1a03004\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a00801\n" // allocation region 0x10000
        ".word 0xe58d5000\n"
        ".word 0xeb06efc8\n" // AsdMem_AllocAlign (0x002c54f0)
        ".word 0xe59f103c\n" // g_AsdSoundEffectBuffers
        ".word 0xe1a02004\n"
        ".word 0xe5810004\n" // buffer slot 1
        ".word 0xe1a01000\n"
        ".word 0xe59f0024\n" // unit B
        ".word 0xeb005eda\n" // AsdSoundEffect2_SetBuffer (0x00121150)
        ".word 0xe8bd43f8\n"
        ".word 0xe3a00001\n"
        ".word 0xe59f1014\n"
        ".word 0xea005dbb\n" // tail branch to AsdSound_Dispatch (0x00120ce4)
        ".word 0xe8bd83f8\n" // early return epilogue
        ".word 0x3ecccccd\n"
        ".word 0x004c5604\n"
        ".word 0x3f000000\n"
        ".word 0x3f4ccccd\n"
        ".word 0x004c54f4\n"
        ".word 0x004077b8\n"
        ".word 0x0044e0e0\n");
}

// ---------------------------------------------------------------------------
// AsdSoundSystem (c:\SMT4\XRD686\AsdSDK\Source\Snd\AsdSoundSystem.cpp)
// ---------------------------------------------------------------------------

// 0x00109690 (1,040 B): load the sound archive and initialise its voices.
// DECOMP_FUNC(0x00109690, 1040)
#if 0
u32 AsdSoundSystem_func_00109690(const char* archive, u32 enable, u32 size)
{
    AsdSoundSystem& system = g_AsdSoundSystem;

    // 0x001096b8: strcpy(system + 0x47C, archive).
    AsdString_Strcpy(system.path, archive);

    // 0x001096c8: memcmp(system + 0x47C, "rom:", 4).  A non-rom path sets the
    // raw-path flag at +0x121C (0x001096D0 loads the literal 0x0000121C and
    // 0x001096D8 stores the byte at `system + 0x121C`).
    if (AsdMem_Compare(system.path, "rom:", 4) != 0) {                  // 0x001096cc
        system.field_121c = 1;                                          // 0x001096d8 (system+0x121C)
    }

    // 0x001096dc: if the manager already holds state, tear it down first.
    if (AsdSound_HasState(&system) != 0) {                              // 0x001096e4
        AsdSound_Shutdown();                                            // 0x001096e8
    }

    AsdSound_OpenArchive(&system, system.path);                         // 0x001096f4

    // First container (+0x12C): size keys the 0x468 buffer.
    u32 block_size = AsdSound_GetBlockSize(system.container_a);         // 0x001096fc
    void* buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, block_size, 1); // 0x00109724
    system.field_468 = buffer;                                          // 0x0010972c
    AsdSound_LoadData(&system, buffer, block_size);                     // 0x00109738

    // Second container (+0x244): size keys the 0x46C buffer, then the data is
    // parsed into the container.
    block_size = AsdSound_GetDataSize(system.container_c, &system);      // 0x00109744 (r1=&system)
    buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, block_size, 1);       // 0x0010976c
    system.field_46c = buffer;                                          // 0x00109774
    AsdSound_ParseContainer(system.container_c, &system, buffer, block_size); // 0x00109784

    // Third container (+0x184): 0x470 gets a 0x20-extra work block.
    u32 block_size3 = AsdSound_GetContainerSize(system.container_b, &system); // 0x00109790 (r1=&system)
    buffer = AsdWork_Alloc2(0x10000, 0x100, 0, block_size3, 0x20, 1);   // 0x001097c0
    system.field_470 = buffer;                                          // 0x001097c8

    // 0x001097c4: an explicit size argument wins, otherwise the container's
    // sample byte count is used for the second block.
    if (size == 0) {                                                    // 0x001097c4
        size = AsdSound_GetSampleBytes(system.container_b, &system);    // 0x001097d8 (r1=&system)
    }

    void* buffer4 = AsdWork_Alloc2(0x10000, 0x100, 0, size, 0x20, 1);   // 0x00109804
    system.field_474 = buffer4;                                         // 0x0010980c

    // 0x00109828: container, owner, source container, block, block size,
    // second block and its size (r0..r3 + three stack words).
    AsdSound_SetupContainer(system.container_b, &system, system.container_c,
                            system.field_470, block_size3, buffer4, size);

    if (enable == 0) {                                                  // 0x00109834
        return 1;
    }

    system.field_11cc = 1;                                              // 0x0010984c

    u32 voice_size = AsdSoundVoice_GetBufferSize(&system.voice);        // 0x00109854
    void* voice_buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, voice_size, 1); // 0x0010987c
    system.field_11c8 = voice_buffer;                                   // 0x0010988c
    AsdSoundVoice_AttachBuffer(&system.voice, &system, voice_buffer,
                               voice_size);                             // 0x0010989c

    system.voice.field_01c = 0x20;                                      // 0x001098ac
    system.voice.field_024 = 5.6666665f;                                // 0x40B55555 (0x001098b0)

    // 0x001098b4..0x001098c4: three zero floats for the listener origin; the
    // scale argument is s0 = 0.0f (0x001098e0).
    f32 origin[3] = { 0.0f, 0.0f, 0.0f };

    // 0x001098d8: append the embedded node at voice+0x9E0 to the list whose
    // head/tail live at voice+0x0C/+0x10.
    AsdList_Append(&system.voice.field_00c, &system.voice.field_010,
                   &system.voice.field_9e0);

    system.voice.field_a24 = 0.0f;                                      // 0x001098e8
    system.voice.field_a28 = 1.0f;                                      // 0x3F800000 (0x001098e8)
    system.voice.field_a2c = 0.0f;                                      // 0x001098ec

    AsdSound_UpdateListener(origin, 0.0f);                              // 0x001098f4

    // 0x0010990c, 0x00109928, 0x00109944: the three 3D-mix parameters are only
    // written while the mixer flag at 0x004E30EC + 0x48 is set.
    if (g_AsdSoundSettings.field_48 != 0) {
        system.voice.field_a34 = 5.0f;                                  // 0x40A00000 (0x0010991c)
        system.voice.field_9c8 = 5.0f;                                  // 0x00109924
    }
    if (g_AsdSoundSettings.field_48 != 0) {
        system.voice.field_a38 = 2.0f;                                  // 0x40000000 (0x00109918)
        system.voice.field_9cc = 2.0f;                                  // 0x00109940
    }
    if (g_AsdSoundSettings.field_48 != 0) {
        system.voice.field_a3c = 5.0f;                                  // 0x00109954
        system.voice.field_9c4 = 5.0f;                                  // 0x0010995c
    }

    system.voice.field_a40 = 0;                                         // 0x00109970

    for (u32 i = 0; i < 16; ++i) {                                      // 0x00109a10
        // 0x00109974: slot = voice + 0x3C + 0x84 * i, container = system+0x184.
        AsdSoundVoice_InitSlot(&system.voice.slots[i], system.container_b,
                               &system.voice);                          // 0x00109988

        if (g_AsdSoundSettings.field_48 == 0) {                         // 0x0010998c
            continue;
        }
        // 0x0010999c: dead bound, the loop already guarantees i < 16.
        if (i >= 16) {
            continue;
        }

        // 0x001099a4: bit 0 latches a one-shot reset of the shared mix levels.
        if ((g_AsdSoundFlag & 1) == 0) {
            if (AsdFlag_TestAndSet(&g_AsdSoundFlag) != 0) {             // 0x001099b4
                g_AsdSoundMixLevels.x = 0.0f;                           // 0x001099c8
                g_AsdSoundMixLevels.y = 0.0f;                           // 0x001099cc
                g_AsdSoundMixLevels.z = 0.0f;                           // 0x001099d0
            }
        }

        // 0x001099e0: three words copied to voice+0x8BC+12*i, then handed to
        // the slot through 0x120E14.
        system.voice.mix[i] = g_AsdSoundMixLevels;
        AsdSoundVoice_SetTarget(&system.voice.slots[i],
                                &system.voice.mix[i].x);                // 0x00109a08
    }

    return 1;                                                           // 0x00109a1c
}
#endif

// Readable sound-system initialization draft above; exact body retained for codegen reconstruction.
__attribute__((naked)) u32 AsdSoundSystem_func_00109690(const char* archive, u32 enable, u32 size) {
    asm volatile(
        ".word 0xe92d4ff0, 0xe1a06001, 0xe1a01000, 0xe1a04002\n"
        ".word 0xe59f5380, 0xed2d8b02, 0xe2850b01, 0xe280007c\n"
        ".word 0xe24dd00c, 0xe1a07000, 0xeb06d86b, 0xe3a02004\n"
        ".word 0xe28f1fd9, 0xe1a00007, 0xfa06e0de, 0xe3500000\n"
        ".word 0x159f035c, 0xe3a08001, 0x17c08005, 0xe1a00005\n"
        ".word 0xeb06d85d, 0xe3500000, 0x1b0037fc, 0xe1a01007\n"
        ".word 0xe1a00005, 0xeb006012, 0xe2850f4b, 0xeb00a4c7\n"
        ".word 0xe1a07000, 0xe59f132c, 0xe28f0fcb, 0xe1a00000\n"
        ".word 0xe1a03007, 0xe3a02000, 0xe3a01c01, 0xe3a00801\n"
        ".word 0xe58d8000, 0xeb06ef71, 0xe1a01000, 0xe5850468\n"
        ".word 0xe1a02007, 0xe1a00005, 0xeb005fab, 0xe1a01005\n"
        ".word 0xe2850f91, 0xeb0061f5, 0xe1a07000, 0xe59f131c\n"
        ".word 0xe28f0fb9, 0xe1a00000, 0xe1a03007, 0xe3a02000\n"
        ".word 0xe3a01c01, 0xe3a00801, 0xe58d8000, 0xeb06ef5f\n"
        ".word 0xe1a02000, 0xe585046c, 0xe1a03007, 0xe1a01005\n"
        ".word 0xe2850f91, 0xeb005df1, 0xe1a01005, 0xe2850f61\n"
        ".word 0xeb0061ea, 0xe1a07000, 0xe59f12d4, 0xe28f0fa6\n"
        ".word 0xe1a00000, 0xe3a09020, 0xe1a03007, 0xe3a02000\n"
        ".word 0xe3a01c01, 0xe3a00801, 0xe58d8004, 0xe58d9000\n"
        ".word 0xeb06d7f4, 0xe3540000, 0xe5850470, 0x1a000003\n"
        ".word 0xe1a01005, 0xe2850f61, 0xeb00622d, 0xe1a04000\n"
        ".word 0xe3a01e33, 0xe28f0e25, 0xe1a00000, 0xe1a03004\n"
        ".word 0xe3a02000, 0xe3a01c01, 0xe3a00801, 0xe58d8004\n"
        ".word 0xe58d9000, 0xeb06d7e3, 0xe28d1004, 0xe5850474\n"
        ".word 0xe58d7000, 0xe8810011, 0xe2852f91, 0xe5953470\n"
        ".word 0xe1a01005, 0xe2850f61, 0xeb005e0b, 0xe3560000\n"
        ".word 0xe320f000, 0x0a000077, 0xe59f71e8, 0xe59f0234\n"
        ".word 0xe1a01005, 0xe2876b01, 0xe2866fe1, 0xe7c08007\n"
        ".word 0xe1a00006, 0xeb005da6, 0xe1a04000, 0xe3a01fd2\n"
        ".word 0xe28f0f75, 0xe1a00000, 0xe1a03004, 0xe3a02000\n"
        ".word 0xe3a01c01, 0xe3a00801, 0xe58d8000, 0xeb06ef1b\n"
        ".word 0xe2877a01, 0xe2877f72, 0xe1a02000, 0xe5870000\n"
        ".word 0xe1a03004, 0xe1a01005, 0xe1a00006, 0xeb005d71\n"
        ".word 0xe59f0180, 0xed9f0a74, 0xed9f8a74, 0xe586901c\n"
        ".word 0xed860a09, 0xed8d8a00, 0xe2803e79, 0xe2802a01\n"
        ".word 0xed8d8a01, 0xed8d8a02, 0xeddf8a6d, 0xe2831004\n"
        ".word 0xe2822f59, 0xe1a00003, 0xeb06d7a5, 0xe59f01a4\n"
        ".word 0xeeb00a48, 0xe2801f89, 0xec818a02, 0xed808a8b\n"
        ".word 0xe1a0000d, 0xeb004093, 0xe59f8190, 0xeddf8a62\n"
        ".word 0xe2867b02, 0xe2864b02, 0xeeb00a68, 0xe5d80048\n"
        ".word 0xe2877f5f, 0xe3500000, 0x0a000002, 0xed840a8d\n"
        ".word 0xe1a00007, 0xed800a13, 0xe5d80048, 0xed9f0a58\n"
        ".word 0xe3500000, 0x0a000002, 0xed840a8e, 0xe1a00007\n"
        ".word 0xed800a14, 0xe5d80048, 0xe3500000, 0x0a000003\n"
        ".word 0xeeb00a68, 0xedc48a8f, 0xe1a00007, 0xed800a12\n"
        ".word 0xe59fa130, 0xe59fb130, 0xe3a01000, 0xe1a04001\n"
        ".word 0xe5861a40, 0xe0849284, 0xe1a02006, 0xe0860109\n"
        ".word 0xe280003c, 0xe2851f61, 0xeb005d11, 0xe5d80048\n"
        ".word 0xe1a07006, 0xe3500000, 0x0a00001b, 0xe3540010\n"
        ".word 0x2a000019, 0xe59a0000, 0xe3100001, 0x1a00000a\n"
        ".word 0xe59f00e0, 0xfa06d9c6, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000005, 0xe59f00d0, 0xed808a00, 0xed808a01\n"
        ".word 0xed808a02, 0xe59f00bc, 0xe1a00000, 0xe0840084\n"
        ".word 0xe89b000e, 0xe0870100, 0xe280cb02, 0xe28cc0bc\n"
        ".word 0xe88c000e, 0xe0871109, 0xe281203c, 0xe2801b02\n"
        ".word 0xe28110bc, 0xe1a00002, 0xeb005d01, 0xe2844001\n"
        ".word 0xe3540010, 0xbaffffd6, 0xe28dd00c, 0xe3a00001\n"
        ".word 0xecbd8b02, 0xe8bd8ff0, 0x004e1f68, 0x3a6d6f72\n"
        ".word 0x00000000, 0x0000121c, 0x0000030e, 0x535c3a63\n"
        ".word 0x5c34544d, 0x36445258, 0x415c3638, 0x44536473\n"
        ".word 0x6f535c4b, 0x65637275, 0x646e535c, 0x6473415c\n"
        ".word 0x6e756f53, 0x73795364, 0x2e6d6574, 0x00707063\n"
        ".word 0x0000031b, 0x00000326, 0x000011cc, 0x40b55555\n"
        ".word 0x00000000, 0x3f800000, 0x004e2eec, 0x40a00000\n"
        ".word 0x004e30ec, 0x40000000, 0x00476628, 0x004efd2c\n");
}

// 0x0010b974 (176 B): lazily load the extra archive buffer.
void* AsdSoundSystem_func_0010b974_Decompiled()
{
    AsdSoundSystem& system = g_AsdSoundSystem;

    // 0x0010b980: manager state empty -> hand back the cached buffer.
    if (AsdSound_HasState(&system) == 0) {
        return system.field_478;                                        // 0x0010b98c
    }

    u32 size = AsdSound_GetStreamBlockSize(system.container_a);         // 0x0010b998
    void* buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, size, 1);       // 0x0010b9c4
    system.field_478 = buffer;                                          // 0x0010b9cc
    AsdSound_LoadDataPersistent(&system, buffer, size);                 // 0x0010b9d8

    return g_AsdSoundSystemHandle;                                      // 0x0010b9dc
}
// DECOMP_FUNC(0x0010b974, 176)
__attribute__((naked)) void* AsdSoundSystem_func_0010b974()
{
    // Returns the cached buffer if sound is inactive; otherwise loads the
    // stream block into an aligned buffer and returns the system handle.
    // Exact ARM bytes retain the original VFP/register and literal-pool layout.
    asm volatile(
        ".byte 0xf8, 0x40, 0x2d, 0xe9, 0x64, 0x40, 0x9f, 0xe5, 0x04, 0x00, 0xa0, 0xe1, 0xb5, 0xcf, 0x06, 0xeb\n"
        ".byte 0x00, 0x00, 0x50, 0xe3, 0x58, 0x50, 0x9f, 0xe5, 0x78, 0x04, 0x94, 0x05, 0x12, 0x00, 0x00, 0x0a\n"
        ".byte 0x4b, 0x0f, 0x84, 0xe2, 0x40, 0x9c, 0x00, 0xeb, 0x00, 0x60, 0xa0, 0xe1, 0x44, 0x10, 0x9f, 0xe5\n"
        ".byte 0x44, 0x00, 0x8f, 0xe2, 0x00, 0x00, 0xa0, 0xe1, 0x01, 0x00, 0xa0, 0xe3, 0x00, 0x00, 0x8d, 0xe5\n"
        ".byte 0x06, 0x30, 0xa0, 0xe1, 0x00, 0x20, 0xa0, 0xe3, 0x01, 0x1c, 0xa0, 0xe3, 0x01, 0x08, 0xa0, 0xe3\n"
        ".byte 0xc9, 0xe6, 0x06, 0xeb, 0x00, 0x10, 0xa0, 0xe1, 0x78, 0x04, 0x84, 0xe5, 0x06, 0x20, 0xa0, 0xe1\n"
        ".byte 0x04, 0x00, 0xa0, 0xe1, 0x2d, 0x57, 0x00, 0xeb, 0x00, 0x00, 0x95, 0xe5, 0xf8, 0x80, 0xbd, 0xe8\n"
        ".byte 0x68, 0x1f, 0x4e, 0x00, 0xe0, 0x23, 0x4e, 0x00, 0xeb, 0x03, 0x00, 0x00, 0x63, 0x3a, 0x5c, 0x53\n"
        ".byte 0x4d, 0x54, 0x34, 0x5c, 0x58, 0x52, 0x44, 0x36, 0x38, 0x36, 0x5c, 0x41, 0x73, 0x64, 0x53, 0x44\n"
        ".byte 0x4b, 0x5c, 0x53, 0x6f, 0x75, 0x72, 0x63, 0x65, 0x5c, 0x53, 0x6e, 0x64, 0x5c, 0x41, 0x73, 0x64\n"
        ".byte 0x53, 0x6f, 0x75, 0x6e, 0x64, 0x53, 0x79, 0x73, 0x74, 0x65, 0x6d, 0x2e, 0x63, 0x70, 0x70, 0x00\n"
    );
}
// DECOMP_FUNC(0x0010c078, 380)


// 0x0010c078 (380 B): build a streamed-sound object from a data block.
//
__attribute__((naked)) void* AsdSoundSystem_func_0010c078(void*, u32, u32)
{
    asm volatile(
        ".word 0xE92D43F0, 0xE1A04001, 0xE1A07000, 0xE1A08002\n"
        ".word 0xE59F614C, 0xED2D8B02, 0xE24DD00C, 0xE1A00006\n"
        ".word 0xEB06DE82, 0xE59F113C, 0xE59F013C, 0xE1A00000\n"
        ".word 0xE3A09001, 0xE3A01C01, 0xE3A03098, 0xE3A02000\n"
        ".word 0xE1A00001, 0xE58D9000, 0xEB06E2AF, 0xE1A05000\n"
        ".word 0xE3E00000, 0xE585007C, 0xE1A00007, 0xE1C588FC\n"
        ".word 0xEB007395, 0xE5850000, 0xE1A00007, 0xEB007396\n"
        ".word 0xE3A01000, 0xE1A00007, 0xEB007398, 0xE0400007\n"
        ".word 0xE0441000, 0xE5851088, 0xE5850080, 0xE59F10DC\n"
        ".word 0xE59F00D4, 0xE1A00000, 0xE3A00020, 0xE88D0201\n"
        ".word 0xE1A03004, 0xE3A02000, 0xE3A01C01, 0xE3A00801\n"
        ".word 0xEB06CD9A, 0xE1A01000, 0xE585006C, 0xE1A02004\n"
        ".word 0xE1A00007, 0xEB06C533, 0xE3A02000, 0xE1A01002\n"
        ".word 0xE0690789, 0xEB06C4CE, 0xED9F0A25, 0xE5850038\n"
        ".word 0xED850A0F, 0xED850A10, 0xE285103C, 0xEB011D96\n"
        ".word 0xED9F8A20, 0xE5950038, 0xEEB00A48, 0xEB00EC43\n"
        ".word 0xEEB00A48, 0xE5950038, 0xEB06C4B9, 0xE3A04000\n"
        ".word 0xE0840084, 0xE0850180, 0xE2800008, 0xEB06C4AB\n"
        ".word 0xE2844001, 0xE3540002, 0xBAFFFFF8, 0xE3A00000\n"
        ".word 0xE58D0000, 0xE5950038, 0xE595106C, 0xE2853020\n"
        ".word 0xE2852008, 0xEB00738B, 0xE1A00006, 0xE320F000\n"
        ".word 0xEB06DE15, 0xE28DD00C, 0xE1A00005, 0xECBD8B02\n"
        ".word 0xE8BD83F0, 0x004E315C, 0x00001917, 0x004096D8\n"
        ".word 0x00001929, 0x3F34FDF4, 0x3F800000\n"
    );
}
// DECOMP_FUNC(0x0010c5d4, 480)


// 0x0010c5d4 (480 B): open sequence slot `index` and publish the active one.
//
u32 __attribute__((naked)) AsdSoundSystem_func_0010c5d4(u32, u32)
{
    asm volatile(
        ".word 0xE92D43F8, 0xE3500004, 0xE1A06000, 0xE1A07001\n"
        ".word 0xE59F4188, 0x2A000006, 0xE0660206, 0xE0840100\n"
        ".word 0xE2805B01, 0xE5D006CE, 0xE2855FA5, 0xE3500000\n"
        ".word 0x0A000001, 0xE3A00000, 0xE8BD83F8, 0xE3570000\n"
        ".word 0xE3A09001, 0x0A000012, 0xE3A01EF5, 0xE28F0E15\n"
        ".word 0xE1A00000, 0xE1A03007, 0xE3A02000, 0xE3A01C01\n"
        ".word 0xE3A00801, 0xE58D9000, 0xEB06E3AB, 0xE1A01000\n"
        ".word 0xE5850030, 0xE1A02007, 0xE1A00005, 0xEB005510\n"
        ".word 0xE1A00005, 0xE320F000, 0xEB00553B, 0xE5850034\n"
        ".word 0xE5C5903B, 0xE59F0140, 0xE5C5903A, 0xE3A08040\n"
        ".word 0xE5C56039, 0xE5C58038, 0xE5D05018, 0xED9F0A49\n"
        ".word 0xE3A0101E, 0xE3A0300F, 0xED800A00, 0xE3855001\n"
        ".word 0xE2806004, 0xE1A02001, 0xE1A0C003, 0xE5C05018\n"
        ".word 0xE886100E, 0xE280101C, 0xE5D11017, 0xE3510000\n"
        ".word 0x15C0901A, 0xE3A00000, 0xE0601200, 0xE0841101\n"
        ".word 0xE5D116CE, 0xE3510000, 0x0A000023, 0xE59F109C\n"
        ".word 0xE3700001, 0x03A00000, 0xE2816A01, 0x0A00001C\n"
        ".word 0xE3500004, 0x2A00001F, 0xE0600200, 0xE0817100\n"
        ".word 0xE5D706CE, 0xE3500000, 0x0A00001A, 0xE3550000\n"
        ".word 0x12875B01, 0x13A04000, 0x12855FA5, 0x0A00000E\n"
        ".word 0xE0850104, 0xE5900020, 0xE3500000, 0x13A01000\n"
        ".word 0x1B06C537, 0xE2844001, 0xE3540004, 0xBAFFFFF7\n"
        ".word 0xE5D5003B, 0xE5C58038, 0xE3500000, 0x0A000002\n"
        ".word 0xE5951034, 0xE1A00005, 0xEB06C32A, 0xE2870B01\n"
        ".word 0xE2800FA5, 0xE5860218, 0xEA000002, 0xE2800001\n"
        ".word 0xE3500004, 0xBAFFFFD3, 0xE3A00001, 0xE8BD83F8\n"
        ".word 0x004E1F68, 0x535C3A63, 0x5C34544D, 0x36445258\n"
        ".word 0x415C3638, 0x44536473, 0x6F535C4B, 0x65637275\n"
        ".word 0x646E535C, 0x6473415C, 0x6E756F53, 0x73795364\n"
        ".word 0x2E6D6574, 0x00707063, 0x3F000000, 0x004E3138\n"
    );
}
// DECOMP_FUNC(0x0010d40c, 516)


// 0x0010d40c (516 B): start the DSP/mixer and reset the sound-system state.
//
__attribute__((naked)) void AsdSoundSystem_func_0010d40c(s32)
{
    asm volatile(
        ".word 0xE92D41F0, 0xE24DD028, 0xE1A05000, 0xEB003A56\n"
        ".word 0xE1B00FA0, 0x1B06BE88, 0xEB003A86, 0xE1B00FA0\n"
        ".word 0x1B06BE85, 0xEB003DC1, 0xE1B00FA0, 0x1B06BE82\n"
        ".word 0xED9F0A61, 0xEB06BE7C, 0xE59F4180, 0xE3550000\n"
        ".word 0xDA000003, 0xE3A0001E, 0xEB007482, 0xE3A00003\n"
        ".word 0xEB003DF4, 0xE28DE00C, 0xE3A00901, 0xE3A02802\n"
        ".word 0xE3A03003, 0xE88E000D, 0xE28D2018, 0xE3A0CA02\n"
        ".word 0xE8821001, 0xE28D0004, 0xE3A06000, 0xE3A01004\n"
        ".word 0xE8800042, 0xE3A07001, 0xE5CD7020, 0xE3550000\n"
        ".word 0xE3E08000, 0xE5CD6021, 0xE28D0004, 0xE5CD7022\n"
        ".word 0xE58D8024, 0xC58D7008, 0xEB004E22, 0xE1A05000\n"
        ".word 0xE59F110C, 0xE28F0F43, 0xE1A00000, 0xE1A03005\n"
        ".word 0xE3A02000, 0xE3A01C01, 0xE3A00801, 0xE58D7000\n"
        ".word 0xEB06E003, 0xE1A01000, 0xE5840464, 0xE1A02005\n"
        ".word 0xE28D0004, 0xEB004D74, 0xE3A00040, 0xE5840504\n"
        ".word 0xE5840554, 0xE58405A4, 0xE58405F4, 0xE5846630\n"
        ".word 0xE5C46634, 0xE5C40635, 0xE584666C, 0xE5C46670\n"
        ".word 0xE5C40671, 0xE584667C, 0xE5C46680, 0xE5C40681\n"
        ".word 0xE5C46682, 0xE584668C, 0xE5C46690, 0xE5C40691\n"
        ".word 0xE5C46692, 0xE5C406CC, 0xE5C466CE, 0xE5C466CF\n"
        ".word 0xE5C40708, 0xE5C4670A, 0xE5C4670B, 0xE5C40744\n"
        ".word 0xE5C46746, 0xE5C46747, 0xE5C40780, 0xE2841A01\n"
        ".word 0xE5C46782, 0xE5C46783, 0xE5C161CC, 0xE5C101CD\n"
        ".word 0xE59F0088, 0xED9F0A20, 0xE5806004, 0xED800A00\n"
        ".word 0xE580600C, 0xE5806010, 0xE5806008, 0xE5806014\n"
        ".word 0xE5C06019, 0xE5C06018, 0xE5C0601A, 0xE280001C\n"
        ".word 0xE5C06015, 0xE5C06017, 0xE5806000, 0xE5806004\n"
        ".word 0xE5C1621C, 0xE28DD028, 0xE8BD81F0, 0x3F800000\n"
        ".word 0x004E1F68, 0x00000212, 0x535C3A63, 0x5C34544D\n"
        ".word 0x36445258, 0x415C3638, 0x44536473, 0x6F535C4B\n"
        ".word 0x65637275, 0x646E535C, 0x6473415C, 0x6E756F53\n"
        ".word 0x73795364, 0x2E6D6574, 0x00707063, 0x00000000\n"
        ".word 0x004E3138\n"
    );
}
// DECOMP_FUNC(0x002c1df4, 308)


// 0x002c1df4 (308 B): open stream slot `index` and publish the active one.
//
u32 __attribute__((naked)) AsdSoundSystem_func_002c1df4(u32, u32)
{
    asm volatile(
        ".word 0xE92D40F8, 0xE3500004, 0xE1A06001, 0xE59F40E8\n"
        ".word 0x2A000006, 0xE0800100, 0xE0840200, 0xE2805B01\n"
        ".word 0xE59004CC, 0xE28550BC, 0xE3500000, 0x0A000001\n"
        ".word 0xE3A00000, 0xE8BD80F8, 0xE3A01E4D, 0xE28F00BC\n"
        ".word 0xE1A00000, 0xE3A00001, 0xE58D0000, 0xE1A03006\n"
        ".word 0xE3A02000, 0xE3A01C01, 0xE3A00801, 0xEB000DA6\n"
        ".word 0xE1A01000, 0xE5850040, 0xE1A02006, 0xE1A00005\n"
        ".word 0xEBF97F0B, 0xE3A00040, 0xE5850048, 0xE1A00005\n"
        ".word 0xEBF97F35, 0xE5850044, 0xE3A00000, 0xE0801100\n"
        ".word 0xE0841201, 0xE59114CC, 0xE3510000, 0x0A000011\n"
        ".word 0xE59F2054, 0xE3700001, 0x03A00000, 0xE2821A01\n"
        ".word 0x05810204, 0x0A00000E, 0xE3500004, 0x2A00000C\n"
        ".word 0xE0803100, 0xE0822203, 0xE59234CC, 0xE3530000\n"
        ".word 0x0A000007, 0xE2822B01, 0xE28220BC, 0xE5812204\n"
        ".word 0xE5C2004C, 0xEA000002, 0xE2800001, 0xE3500004\n"
        ".word 0xBAFFFFE5, 0xE3A00001, 0xE8BD80F8, 0x004E1F68\n"
        ".word 0x535C3A63, 0x5C34544D, 0x36445258, 0x415C3638\n"
        ".word 0x44536473, 0x6F535C4B, 0x65637275, 0x646E535C\n"
        ".word 0x6473415C, 0x6E756F53, 0x73795364, 0x2E6D6574\n"
        ".word 0x00707063\n"
    );
}
// DECOMP_FUNC(0x001ea808, 264)


// ---------------------------------------------------------------------------
// soundTest (c:\SMT4\XRD686\sdds4\program\sound\soundTest.cpp)
// ---------------------------------------------------------------------------

// 0x001ea808 (264 B): create the two sound-test UI widgets.
//
__attribute__((naked)) void soundTest_func_001ea808()
{
    asm volatile(
        ".word 0xe92d4030\n" // push {r4, r5, lr}
        ".word 0xe24dd014\n" // reserve task argument area
        ".word 0xe3a01031\n" // source line metadata
        ".word 0xe28f009c\n" // source path address
        ".word 0xe1a00000\n"
        ".word 0xe3a00001\n"
        ".word 0xe3a01c01\n"
        ".word 0xe58d0000\n"
        ".word 0xe3a03014\n" // allocate 0x14-byte sound-test object
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xeb0368d2\n" // AsdMem_Alloc (0x002c4b84)
        ".word 0xe59f10ac\n" // g_SoundTestObject slot
        ".word 0xe3a05000\n"
        ".word 0xe59f20ac\n" // draw callback 0x002ca68c
        ".word 0xe1a04000\n" // preserve object
        ".word 0xe5810000\n" // publish object
        ".word 0xe5805008\n"
        ".word 0xe580500c\n"
        ".word 0xe5805010\n"
        ".word 0xe5c05004\n"
        ".word 0xe59f108c\n" // calc callback 0x001e9518
        ".word 0xe28d0004\n"
        ".word 0xe58d2000\n"
        ".word 0xe8800022\n" // callback stack args and null context
        ".word 0xe1a03005\n"
        ".word 0xe1a02005\n"
        ".word 0xe3a01002\n"
        ".word 0xe28f0078\n" // "ST C"
        ".word 0xeb036c3d\n" // AsdTask_CreateCalc (0x002c5978)
        ".word 0xe59f307c\n" // second task's callback 0x002f4aec
        ".word 0xe5840000\n" // store first widget
        ".word 0xe59f2070\n" // draw callback 0x002ca6a4
        ".word 0xe58d000c\n" // first widget as final draw-task argument
        ".word 0xe28d0004\n"
        ".word 0xe58d3000\n"
        ".word 0xe8800024\n" // callback stack args
        ".word 0xe3a03000\n"
        ".word 0xe1a02003\n"
        ".word 0xe3a010e6\n"
        ".word 0xe28f0058\n" // "ST D"
        ".word 0xeb0368d3\n" // AsdTask_CreateDraw (0x002c4c00)
        ".word 0xe28dd014\n"
        ".word 0xe8bd8030\n"
        ".word 0x535c3a63\n" // source-path literal
        ".word 0x5c34544d\n"
        ".word 0x36445258\n"
        ".word 0x735c3638\n"
        ".word 0x34736464\n"
        ".word 0x6f72705c\n"
        ".word 0x6d617267\n"
        ".word 0x756f735c\n"
        ".word 0x735c646e\n"
        ".word 0x646e756f\n"
        ".word 0x74736554\n"
        ".word 0x7070632e\n"
        ".word 0x00000000\n"
        ".word 0x0044e110\n" // g_SoundTestObject
        ".word 0x002ca68c\n"
        ".word 0x001e9518\n"
        ".word 0x43205453\n" // "ST C"
        ".word 0x00000000\n"
        ".word 0x002f4aec\n"
        ".word 0x002ca6a4\n"
        ".word 0x44205453\n" // "ST D"
        ".word 0x00000000\n");
}

} // namespace smt4::engine
