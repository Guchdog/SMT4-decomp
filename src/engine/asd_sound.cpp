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
AsdSoundFloat3 g_AsdSoundMixLevels{};                   // 0x004EFD2C

// ---------------------------------------------------------------------------
// soundEffect (c:\SMT4\XRD686\sdds4\program\sound\soundEffect.cpp)
// ---------------------------------------------------------------------------

// 0x0010368c (184 B): build the first effect unit, then chain into 0x00109524.
// DECOMP_FUNC(0x0010368c, 184)
void soundEffect_func_0010368c()
{
    // 0x00103690: `mov r0,#1` / `bl 0x2c583c`; the table slot doubles as the
    // "already built" flag, so a non-null entry skips the whole block.
    if (AsdSound_GetTableEntry(1) == nullptr) {
        AsdSoundEffectConfigA& config = g_AsdSoundEffectConfigA;

        config.field_00 = 0x96;             // 0x001036b0
        config.field_04 = 0.1f;             // 0x3DCCCCCD (0x001036bc)
        config.field_08 = 0.7f;             // 0x3F333333 (0x001036bc)
        config.field_0c = 1;                // 0x001036c4

        // 0x001036c8: unit = config - 0x60 (0x004C5484).
        AsdSoundEffect_Configure(&g_AsdSoundEffectUnitA, &config);      // 0x001036cc

        // 0x001036d4: buffer size from the unit's sample rate/channel count.
        u32 size = AsdSoundEffect_GetBufferSize(&g_AsdSoundEffectUnitA);

        // 0x001036fc: AsdMem_AllocAlign(0x10000, 0x100, 0, size, 1).
        void* buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, size, 1);

        g_AsdSoundEffectBuffers[0] = buffer;                            // 0x00103708
        AsdSoundEffect_SetBuffer(&g_AsdSoundEffectUnitA, buffer, size); // 0x00103714

        AsdSound_Dispatch(0, &g_AsdSoundEffectUnitA);                   // 0x00103720
    }

    // 0x00103728: `pop {r3,r4,r5,lr}` + `b 0x109524` (tail call).
    soundEffect_func_00109524();
}

// 0x00109524 (240 B): build the second effect unit and register it.
// DECOMP_FUNC(0x00109524, 240)
void soundEffect_func_00109524()
{
    if (AsdSound_GetTableEntry(1) != nullptr) {
        return;                             // 0x00109534
    }

    AsdSoundEffectConfigB& config = g_AsdSoundEffectConfigB;

    config.field_00 = 0x5A;                 // 0x00109548
    config.field_04 = 0x4B0;                // 0x00109548
    config.field_08 = 0x1E;                 // 0x00109548
    config.field_0c = 0.5f;                 // 0x3F000000 (0x0010955c)
    config.field_10 = 0.8f;                 // 0x3F4CCCCD (0x0010955c)
    config.field_14 = static_cast<u32>(reinterpret_cast<std::uintptr_t>(&config))
                      + 0x24;               // 0x00109578 (block+0x24)
    config.field_18 = 0.4f;                 // 0x3ECCCCCD (0x0010957c)
    config.field_1c = 0.4f;                 // 0x3ECCCCCD (0x00109580)
    config.field_20 = 0;                    // 0x00109590
    config.field_21 = 1;                    // 0x00109588
    config.field_24 = 0xBE0;                // 0x0010956c
    config.field_28 = 0xE60;                // 0x0010956c
    config.field_2c = 0x820;                // 0x0010956c

    // 0x00109594: unit = config - 0x110 (0x004C54F4).
    AsdSoundEffect2_Configure(&g_AsdSoundEffectUnitB, &config);         // 0x00109598

    u32 size = AsdSoundEffect2_GetBufferSize(&g_AsdSoundEffectUnitB);    // 0x001095a0

    // 0x001095c8: AsdMem_AllocAlign(0x10000, 0x100, 0, size, 1).
    void* buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, size, 1);

    g_AsdSoundEffectBuffers[1] = buffer;                                // 0x001095d4
    AsdSoundEffect2_SetBuffer(&g_AsdSoundEffectUnitB, buffer, size);    // 0x001095e0

    // 0x001095e8: `mov r0,#1` / `b 0x120ce4` (tail call).
    AsdSound_Dispatch(1, &g_AsdSoundEffectUnitB);
}

// ---------------------------------------------------------------------------
// AsdSoundSystem (c:\SMT4\XRD686\AsdSDK\Source\Snd\AsdSoundSystem.cpp)
// ---------------------------------------------------------------------------

// 0x00109690 (1,040 B): load the sound archive and initialise its voices.
// DECOMP_FUNC(0x00109690, 1040)
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

// 0x0010b974 (176 B): lazily load the extra archive buffer.
// DECOMP_FUNC(0x0010b974, 176)
void* AsdSoundSystem_func_0010b974()
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

// 0x0010c078 (380 B): build a streamed-sound object from a data block.
// DECOMP_FUNC(0x0010c078, 380)
void* AsdSoundSystem_func_0010c078(void* data, u32 size, u32 extra)
{
    // 0x0010c098: the whole construction runs under the 0x004E315C lock.
    AsdMemLock_Acquire(&g_AsdSoundLock);

    // 0x0010c0c0: AsdMem_Alloc(0x100, 0x100, 0, 0x98, 1) (zero-filled).
    AsdSoundStreamObject* object =
        static_cast<AsdSoundStreamObject*>(AsdMem_Alloc(0x100, 0x100, 0, 0x98, 1));

    object->field_7c = 0xFFFFFFFF;                                      // 0x0010c0cc
    object->field_8c = extra;                                           // 0x0010c0d4
    object->field_90 = 1;                                               // 0x0010c0d4

    object->field_00 = static_cast<u32>(
        reinterpret_cast<std::uintptr_t>(AsdData_GetBase(data)));       // 0x0010c0dc
    AsdData_GetCount(data);                                             // 0x0010c0e4 (result unused)

    // 0x0010c0f0: entry 0 minus the block base is the header length.
    u32 header = AsdData_GetEntry(data, 0) -
                 static_cast<u32>(reinterpret_cast<std::uintptr_t>(data));
    object->field_88 = size - header;                                   // 0x0010c0f8
    object->field_80 = header;                                          // 0x0010c100

    // 0x0010c128: AsdWork_Alloc2(0x10000, 0x100, 0, size, 0x20, 1).
    void* buffer = AsdWork_Alloc2(0x10000, 0x100, 0, size, 0x20, 1);
    object->field_6c = buffer;                                          // 0x0010c130
    AsdMem_CopyFrom(data, buffer, size);                                // 0x0010c13c

    // 0x0010c148: (1 << 15) - 1 through AsdSoundVoice_Create.
    void* voice = AsdSoundVoice_Create(0x7FFF, 0, 0);
    object->field_38 = voice;                                           // 0x0010c154
    object->field_3c = 0.707f;                                          // 0x3F34FDF4 (0x0010c158)
    object->field_40 = 0.707f;                                          // 0x3F34FDF4 (0x0010c15c)

    AsdSoundVoice_SetParams(voice, &object->field_3c);                  // 0x0010c164
    AsdSoundVoice_SetVolume(voice, 1.0f);                               // 0x0010c174
    AsdSoundVoice_SetSpeed(voice, 1.0f);                                // 0x0010c180

    // 0x0010c188: two 0x18-byte blocks at object+0x08 and object+0x20.
    for (u32 i = 0; i < 2; ++i) {
        AsdSoundVoice_Clear(reinterpret_cast<u8*>(object) + 0x08 + i * 0x18);
    }

    // 0x0010c1bc: (voice, buffer, object+0x08, object+0x20, 0).
    AsdSoundVoice_Attach(voice, object->field_6c,
                         reinterpret_cast<u8*>(object) + 0x08,
                         reinterpret_cast<u8*>(object) + 0x20, 0);

    AsdMemLock_Release(&g_AsdSoundLock);                                   // 0x0010c1c8

    return object;                                                      // 0x0010c1d0
}

// 0x0010c5d4 (480 B): open sequence slot `index` and publish the active one.
// DECOMP_FUNC(0x0010c5d4, 480)
u32 AsdSoundSystem_func_0010c5d4(u32 index, u32 size)
{
    AsdSoundSystem& system = g_AsdSoundSystem;

    if (index >= 4) {                                                   // 0x0010c5d8
        return 0;                                                       // 0x0010c608
    }

    AsdSoundSequenceSlot& slot = system.sequences[index];               // 0x0010c5ec
    if (slot.field_3a != 0) {                                           // 0x0010c5f8
        return 0;
    }

    if (size != 0) {                                                    // 0x0010c610
        void* buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, size, 1);   // 0x0010c63c
        slot.field_30 = buffer;                                         // 0x0010c644
        AsdSoundSlot_Attach(&slot, buffer, size);                       // 0x0010c650
        slot.field_34 = AsdSoundSlot_GetHandle(&slot);                  // 0x0010c660
        slot.field_3b = 1;                                              // 0x0010c664
    }

    slot.field_3a = 1;                                                  // 0x0010c66c
    slot.field_39 = static_cast<u8>(index);                             // 0x0010c674
    slot.field_38 = 0x40;                                               // 0x0010c678

    const u8 previous_flags = g_AsdSoundStream.field_18;                // 0x0010c67c
    g_AsdSoundStream.field_00 = 0.5f;                                   // 0x3F000000 (0x0010c68c)
    g_AsdSoundStream.field_04 = 0x1E;                                   // 0x0010c6a4
    g_AsdSoundStream.field_08 = 0x1E;                                   // 0x0010c6a4
    g_AsdSoundStream.field_0c = 0x0F;                                   // 0x0010c6a4
    g_AsdSoundStream.field_10 = 0x0F;                                   // 0x0010c6a4
    g_AsdSoundStream.field_18 = previous_flags | 1;                     // 0x0010c6a0
    if (g_AsdSoundStream.field_33 != 0) {                               // 0x0010c6ac
        g_AsdSoundStream.field_1a = 1;                                  // 0x0010c6b4
    }

    for (u32 i = 0; i < 4; ++i) {                                       // 0x0010c6b8
        if (system.sequences[i].field_3a == 0) {                        // 0x0010c6c4
            continue;                                                   // 0x0010c760
        }

        // 0x0010c6d4: `cmn r0,#1` can never be taken (index is 0..3); the
        // listing still clears the published slot on that path.
        if (i == 0xFFFFFFFF) {
            system.field_1218 = nullptr;
            break;
        }
        if (i >= 4) {                                                   // 0x0010c6e4
            break;
        }

        AsdSoundSequenceSlot& active = system.sequences[i];             // 0x0010c6f0
        if (active.field_3a == 0) {                                     // 0x0010c6f4
            break;
        }

        // 0x0010c700: r5 holds the flags just written above, so bit 0 is always
        // set and the `cmp r5,#0` / `beq 0x0010c750` skip is never taken; the
        // teardown of the published slot therefore runs unconditionally.
        for (u32 j = 0; j < 4; ++j) {                                   // 0x0010c714
            if (active.field_20[j] != nullptr) {
                AsdSoundVoice_Stop(active.field_20[j], 0);              // 0x0010c724
            }
        }
        // 0x0010c734: the stream byte is read first, then the published slot's
        // level byte is forced to 0x40 (r8) before the conditional stop.
        const u8 streaming = active.field_3b;
        active.field_38 = 0x40;                                         // 0x0010c738
        if (streaming != 0) {
            AsdSoundSlot_Stop(&active, active.field_34);                // 0x0010c74c
        }

        system.field_1218 = &active;                                    // 0x0010c758
        break;
    }

    return 1;                                                           // 0x0010c76c
}

// 0x0010d40c (516 B): start the DSP/mixer and reset the sound-system state.
// DECOMP_FUNC(0x0010d40c, 516)
void AsdSoundSystem_func_0010d40c(s32 duration)
{
    AsdSoundSystem& system = g_AsdSoundSystem;

    // 0x0010d418, 0x0010d424, 0x0010d430: each initialiser returns a negative
    // error code, which is handed to the abort path (0x002bce48).
    if (AsdSound_InitDsp() < 0) {                                       // 0x0010d41c
        AsdFile_NotifyClose();
    }
    if (AsdSound_InitMixer() < 0) {                                     // 0x0010d428
        AsdFile_NotifyClose();
    }
    if (AsdSound_InitStream() < 0) {                                    // 0x0010d434
        AsdFile_NotifyClose();
    }

    AsdSound_SetMasterVolume(1.0f);                                     // 0x3F800000 (0x0010d43c)

    if (duration > 0) {                                                 // 0x0010d44c
        AsdSound_SetPhase(0x1E);                                        // 0x0010d454
        AsdSound_RequestMode(3);                                        // 0x0010d45c
    }

    // The descriptor is built in place; +0x1F is never written by the listing,
    // so the object is deliberately not zero-initialised.
    AsdSoundInitConfig config;
    config.field_08 = 0x4000;                                           // sp+0x0C (0x0010d470)
    config.field_0c = 0x20000;                                          // sp+0x10 (0x0010d470)
    config.field_10 = 3;                                                // sp+0x14 (0x0010d470)
    config.field_14 = 0x4000;                                           // sp+0x18 (0x0010d47c)
    config.field_18 = 0x2000;                                           // sp+0x1C (0x0010d47c)
    config.field_00 = 4;                                                // sp+0x04 (0x0010d48c)
    config.field_04 = 0;                                                // sp+0x08 (0x0010d48c)
    config.field_1c = 1;                                                // sp+0x20 (0x0010d494)
    config.field_1d = 0;                                                // sp+0x21 (0x0010d4a0)
    config.field_1e = 1;                                                // sp+0x22 (0x0010d4a8)
    config.field_20 = 0xFFFFFFFF;                                       // sp+0x24 (0x0010d4ac)
    if (duration > 0) {                                                 // 0x0010d4b0
        config.field_04 = 1;
    }

    u32 size = AsdSound_CreateEngine(&config);                          // 0x0010d4b4
    void* buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, size, 1);       // 0x0010d4dc
    system.field_464 = buffer;                                          // 0x0010d4e4
    AsdSound_InitEngine(&config, buffer, size);                         // 0x0010d4f0

    // 0x0010d4f4: the 0x48 word of all four stream records.
    system.streams[0].field_48 = 0x40;                                  // 0x0010d4f8
    system.streams[1].field_48 = 0x40;                                  // 0x0010d4fc
    system.streams[2].field_48 = 0x40;                                  // 0x0010d500
    system.streams[3].field_48 = 0x40;                                  // 0x0010d504

    system.field_630 = 0;                                               // 0x0010d508
    system.field_634 = 0;                                               // 0x0010d50c
    system.field_635 = 0x40;                                            // 0x0010d510
    system.field_66c = 0;                                               // 0x0010d514
    system.field_670 = 0;                                               // 0x0010d518
    system.field_671 = 0x40;                                            // 0x0010d51c
    system.field_67c = 0;                                               // 0x0010d520
    system.field_680 = 0;                                               // 0x0010d524
    system.field_681 = 0x40;                                            // 0x0010d528
    system.field_682 = 0;                                               // 0x0010d52c
    system.field_68c = 0;                                               // 0x0010d530
    system.field_690 = 0;                                               // 0x0010d534
    system.field_691 = 0x40;                                            // 0x0010d538
    system.field_692 = 0;                                               // 0x0010d53c

    // 0x0010d540: sequence state bytes; +0x39 is intentionally left alone.
    system.sequences[0].field_38 = 0x40;                                // 0x0010d540
    system.sequences[0].field_3a = 0;                                   // 0x0010d544
    system.sequences[0].field_3b = 0;                                   // 0x0010d548
    system.sequences[1].field_38 = 0x40;                                // 0x0010d54c
    system.sequences[1].field_3a = 0;                                   // 0x0010d550
    system.sequences[1].field_3b = 0;                                   // 0x0010d554
    system.sequences[2].field_38 = 0x40;                                // 0x0010d558
    system.sequences[2].field_3a = 0;                                   // 0x0010d55c
    system.sequences[2].field_3b = 0;                                   // 0x0010d560
    system.sequences[3].field_38 = 0x40;                                // 0x0010d564
    system.sequences[3].field_3a = 0;                                   // 0x0010d56c
    system.sequences[3].field_3b = 0;                                   // 0x0010d570

    system.field_11cc = 0;                                              // 0x0010d574
    system.field_11cd = 0x40;                                           // 0x0010d578

    g_AsdSoundStream.field_04 = 0;                                      // 0x0010d584
    g_AsdSoundStream.field_00 = 0.0f;                                   // 0x0010d588
    g_AsdSoundStream.field_0c = 0;                                      // 0x0010d58c
    g_AsdSoundStream.field_10 = 0;                                      // 0x0010d590
    g_AsdSoundStream.field_08 = 0;                                      // 0x0010d594
    g_AsdSoundStream.field_14 = 0;                                      // 0x0010d598
    g_AsdSoundStream.field_19 = 0;                                      // 0x0010d59c
    g_AsdSoundStream.field_18 = 0;                                      // 0x0010d5a0
    g_AsdSoundStream.field_1a = 0;                                      // 0x0010d5a4
    g_AsdSoundStream.field_31 = 0;                                      // 0x0010d5ac
    g_AsdSoundStream.field_33 = 0;                                      // 0x0010d5b0
    g_AsdSoundStream.field_1c = 0;                                      // 0x0010d5b4
    g_AsdSoundStream.field_20 = 0;                                      // 0x0010d5b8

    system.field_121c = 0;                                              // 0x0010d5bc
}

// 0x002c1df4 (308 B): open stream slot `index` and publish the active one.
// DECOMP_FUNC(0x002c1df4, 308)
u32 AsdSoundSystem_func_002c1df4(u32 index, u32 size)
{
    AsdSoundSystem& system = g_AsdSoundSystem;

    if (index >= 4) {                                                   // 0x002c1df8
        return 0;                                                       // 0x002c1e24
    }

    AsdSoundStream& stream = system.streams[index];                     // 0x002c1e08
    if (stream.field_10 != 0) {                                         // 0x002c1e14
        return 0;
    }

    void* buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, size, 1);       // 0x002c1e50
    stream.field_40 = buffer;                                           // 0x002c1e58
    AsdSoundSlot_Attach(&stream, buffer, size);                         // 0x002c1e64
    stream.field_48 = 0x40;                                             // 0x002c1e6c
    stream.field_44 = AsdSoundSlot_GetHandle(&stream);                  // 0x002c1e78

    for (u32 i = 0; i < 4; ++i) {                                       // 0x002c1e7c
        if (system.streams[i].field_10 == 0) {                          // 0x002c1e88
            continue;
        }

        // 0x002c1e98: `cmn r0,#1` can never be taken (index is 0..3); the
        // listing still clears the published slot on that path.
        if (i == 0xFFFFFFFF) {
            system.field_1204 = nullptr;
            break;
        }
        if (i >= 4) {                                                   // 0x002c1eac
            break;
        }
        if (system.streams[i].field_10 == 0) {                          // 0x002c1ebc
            break;
        }

        system.field_1204 = &system.streams[i];                         // 0x002c1ed0
        system.streams[i].field_4c = static_cast<u8>(i);                // 0x002c1ed4
        break;
    }

    return 1;                                                           // 0x002c1ee8
}

// ---------------------------------------------------------------------------
// soundTest (c:\SMT4\XRD686\sdds4\program\sound\soundTest.cpp)
// ---------------------------------------------------------------------------

// 0x001ea808 (264 B): create the two sound-test UI widgets.
// DECOMP_FUNC(0x001ea808, 264)
void soundTest_func_001ea808()
{
    // 0x001ea814/0x001ea820: the source path and line 0x31 only feed the
    // logging macro; r1/r0 are overwritten before the call.
    AsdSoundTestObject* object =
        static_cast<AsdSoundTestObject*>(AsdMem_Alloc(0x100, 0x100, 0, 0x14, 1));

    g_SoundTestObject = object;                                         // 0x001ea848
    object->field_08 = 0;                                               // 0x001ea84c
    object->field_0c = 0;                                               // 0x001ea850
    object->field_10 = 0;                                               // 0x001ea854
    object->field_04 = 0;                                               // 0x001ea858

    // 0x001ea87c: kind "ST C", id 2, callbacks 0x001E9518 / 0x002CA68C.
    object->ui = AsdUi_Create("ST C", 2, 0, 0, 0x001E9518u, 0x002CA68Cu,
                              nullptr);

    // 0x001ea8ac: kind "ST D", id 0xE6, callbacks 0x002CA6A4 / 0x002F4AEC and
    // the widget created above as the last argument.
    AsdUi_CreateLabel("ST D", 0xE6, 0, 0, 0x002CA6A4u, 0x002F4AECu,
                      nullptr, static_cast<u32>(
                          reinterpret_cast<std::uintptr_t>(object->ui)));
}

} // namespace smt4::engine
