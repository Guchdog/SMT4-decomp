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

    // AsdTask helpers
    void* AsdTask_CreateCalc(const char* name, u32 prio, u32 a2, u32 a3,
                             void (*cb)(void*), u32 a5, u32 a6);
    void* AsdTask_CreateDraw(const char* name, u32 prio, u32 a2, u32 a3,
                             void (*cb)(void*), u32 a5, u32 a6, void* parent);

    // Lock helpers
    void  engine_func_002c3aa8(void* lock);                               // 0x002c3aa8
    void  engine_func_002c3a24(void* lock);                               // 0x002c3a24

    // DSP check helpers
    s32   engine_func_0011be44();                                         // 0x0011be44
    s32   engine_func_0011cb3c();                                         // 0x0011cb3c
    void  engine_func_002bce48();                                         // 0x002bce48
    void  engine_func_002bce38(f32 volume);                               // 0x002bce38

    // Memory copy
    void  engine_func_002bd610(void* dst, const void* src, u32 size);     // 0x002bd610

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
void soundEffect_func_0010368c()
{
    if (AsdSound_GetTableEntry(1) == nullptr) {
        g_AsdSoundEffectConfigA.field_00 = 0x96;
        g_AsdSoundEffectConfigA.field_04 = 0.1f;
        g_AsdSoundEffectConfigA.field_08 = 0.7f;
        g_AsdSoundEffectConfigA.field_0c = 1;

        void* unitA = &g_AsdSoundEffectUnitA;
        AsdSoundEffect_Configure(unitA, &g_AsdSoundEffectConfigA);
        u32 size = AsdSoundEffect_GetBufferSize(unitA);
        void* buf = AsdMem_AllocAlign(0x10000, 0x100, 0, size, 1);
        g_AsdSoundEffectBuffers[0] = buf;
        AsdSoundEffect_SetBuffer(unitA, buf, size);
        AsdSound_Dispatch(0, unitA);
    }

    soundEffect_func_00109524();
}
// DECOMP_FUNC(0x00109524, 240)


// 0x00109524 (240 B): build the second effect unit and register it.
//
void soundEffect_func_00109524()
{
    if (AsdSound_GetTableEntry(1) != nullptr) {
        return;
    }

    g_AsdSoundEffectConfigB.field_00 = 0x5a;
    g_AsdSoundEffectConfigB.field_04 = 0x4b0;
    g_AsdSoundEffectConfigB.field_08 = 0x1e;
    g_AsdSoundEffectConfigB.field_0c = 0.5f;
    g_AsdSoundEffectConfigB.field_10 = 0.8f;
    g_AsdSoundEffectConfigB.field_24 = 0xbe0;
    g_AsdSoundEffectConfigB.field_28 = 0xe60;
    g_AsdSoundEffectConfigB.field_2c = 0x820;
    g_AsdSoundEffectConfigB.field_14 = reinterpret_cast<uintptr_t>(&g_AsdSoundEffectConfigB.field_24);
    g_AsdSoundEffectConfigB.field_18 = 0.4f;
    g_AsdSoundEffectConfigB.field_1c = 0.4f;
    g_AsdSoundEffectConfigB.field_20 = 0;
    g_AsdSoundEffectConfigB.field_21 = 1;

    void* unitB = &g_AsdSoundEffectUnitB;
    AsdSoundEffect2_Configure(unitB, &g_AsdSoundEffectConfigB);
    u32 size = AsdSoundEffect2_GetBufferSize(unitB);
    void* buf = AsdMem_AllocAlign(0x10000, 0x100, 0, size, 1);
    g_AsdSoundEffectBuffers[1] = buf;
    AsdSoundEffect2_SetBuffer(unitB, buf, size);
    AsdSound_Dispatch(1, unitB);
}

// ---------------------------------------------------------------------------
// AsdSoundSystem (c:\SMT4\XRD686\AsdSDK\Source\Snd\AsdSoundSystem.cpp)
// ---------------------------------------------------------------------------

// 0x00109690 (1,040 B): load the sound archive and initialise its voices.
// DECOMP_FUNC(0x00109690, 1040)
// 0x00109690 (1,040 B): load the sound archive and initialise its voices.
u32 AsdSoundSystem_func_00109690(const char* archive, u32 enable, u32 size)
{
    AsdSoundSystem& system = g_AsdSoundSystem;

    AsdString_Strcpy(system.path, archive);

    if (AsdMem_Compare(system.path, "rom:", 4) != 0) {
        system.field_121c = 1;
    }

    if (AsdSound_HasState(&system) != 0) {
        AsdSound_Shutdown();
    }

    AsdSound_OpenArchive(&system, system.path);

    u32 block_size = AsdSound_GetBlockSize(system.container_a);
    void* buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, block_size, 1);
    system.field_468 = buffer;
    AsdSound_LoadData(&system, buffer, block_size);

    block_size = AsdSound_GetDataSize(system.container_c, &system);
    buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, block_size, 1);
    system.field_46c = buffer;
    AsdSound_ParseContainer(system.container_c, &system, buffer, block_size);

    u32 block_size3 = AsdSound_GetContainerSize(system.container_b, &system);
    buffer = AsdWork_Alloc2(0x10000, 0x100, 0, block_size3, 0x20, 1);
    system.field_470 = buffer;

    if (size == 0) {
        size = AsdSound_GetSampleBytes(system.container_b, &system);
    }

    void* buffer4 = AsdWork_Alloc2(0x10000, 0x100, 0, size, 0x20, 1);
    system.field_474 = buffer4;

    AsdSound_SetupContainer(system.container_b, &system, system.container_c,
                            system.field_470, block_size3, buffer4, size);

    if (enable == 0) {
        return 1;
    }

    system.field_11cc = 1;

    u32 voice_size = AsdSoundVoice_GetBufferSize(&system.voice);
    void* voice_buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, voice_size, 1);
    system.field_11c8 = voice_buffer;
    AsdSoundVoice_AttachBuffer(&system.voice, &system, voice_buffer, voice_size);

    system.voice.field_01c = 0x20;
    system.voice.field_024 = 5.6666665f;

    f32 origin[3] = { 0.0f, 0.0f, 0.0f };

    AsdList_Append(&system.voice.field_00c, &system.voice.field_010,
                   &system.voice.field_9e0);

    system.voice.field_a24 = 0.0f;
    system.voice.field_a28 = 1.0f;
    system.voice.field_a2c = 0.0f;

    AsdSound_UpdateListener(origin, 0.0f);

    if (g_AsdSoundSettings.field_48 != 0) {
        system.voice.field_a34 = 5.0f;
        system.voice.field_9c8 = 5.0f;
    }
    if (g_AsdSoundSettings.field_48 != 0) {
        system.voice.field_a38 = 2.0f;
        system.voice.field_9cc = 2.0f;
    }
    if (g_AsdSoundSettings.field_48 != 0) {
        system.voice.field_a3c = 5.0f;
        system.voice.field_9c4 = 5.0f;
    }

    system.voice.field_a40 = 0;

    for (u32 i = 0; i < 16; ++i) {
        AsdSoundVoice_InitSlot(&system.voice.slots[i], system.container_b,
                               &system.voice);

        if (g_AsdSoundSettings.field_48 == 0) {
            continue;
        }
        if (i >= 16) {
            continue;
        }

        if ((g_AsdSoundFlag & 1) == 0) {
            if (AsdFlag_TestAndSet(&g_AsdSoundFlag) != 0) {
                g_AsdSoundMixLevels.x = 0.0f;
                g_AsdSoundMixLevels.y = 0.0f;
                g_AsdSoundMixLevels.z = 0.0f;
            }
        }

        system.voice.mix[i] = g_AsdSoundMixLevels;
        AsdSoundVoice_SetTarget(&system.voice.slots[i],
                                &system.voice.mix[i].x);
    }

    return 1;
}

// 0x0010b974 (176 B): lazily load the extra archive buffer.
void* AsdSoundSystem_func_0010b974()
{
    AsdSoundSystem& system = g_AsdSoundSystem;

    if (AsdSound_HasState(&system) == 0) {
        return system.field_478;
    }

    u32 size = AsdSound_GetStreamBlockSize(system.container_a);
    void* buffer = AsdMem_AllocAlign(0x10000, 0x100, 0, size, 1);
    system.field_478 = buffer;
    AsdSound_LoadDataPersistent(&system, buffer, size);

    return g_AsdSoundSystemHandle;
}
// DECOMP_FUNC(0x0010c078, 380)


// 0x0010c078 (380 B): build a streamed-sound object from a data block.
//
void* AsdSoundSystem_func_0010c078(void* data, u32 size, u32 extra)
{
    engine_func_002c3aa8(&g_AsdSoundLock);

    AsdSoundStreamObject* obj = reinterpret_cast<AsdSoundStreamObject*>(
        AsdMem_Alloc(0x100, 0x100, 0, sizeof(AsdSoundStreamObject), 1)
    );

    obj->field_7c = 0xFFFFFFFF;
    obj->field_8c = extra;
    obj->field_90 = 1;

    obj->field_00 = reinterpret_cast<uintptr_t>(AsdData_GetBase(data));
    (void)AsdData_GetCount(data);

    uintptr_t entry = AsdData_GetEntry(data, 0);
    u32 offset = static_cast<u32>(entry - reinterpret_cast<uintptr_t>(data));
    obj->field_88 = size - offset;
    obj->field_80 = offset;

    void* copy_buf = AsdWork_Alloc2(0x10000, 0x100, 0, size, 0x20, 1);
    obj->field_6c = copy_buf;
    engine_func_002bd610(data, copy_buf, size);

    void* player = AsdSoundVoice_Create(0x7FFF, 0, 0);
    obj->field_38 = player;
    obj->field_3c = 0.707f;
    obj->field_40 = 0.707f;

    AsdSoundVoice_SetParams(player, &obj->field_3c);
    AsdSoundVoice_SetVolume(player, 1.0f);
    AsdSoundVoice_SetSpeed(player, 1.0f);

    uintptr_t obj_addr = reinterpret_cast<uintptr_t>(obj);
    for (u32 i = 0; i < 2; ++i) {
        void* slot_ptr = reinterpret_cast<void*>(obj_addr + 8 + i * 24);
        AsdSoundVoice_Clear(slot_ptr);
    }

    AsdSoundVoice_Attach(
        player,
        copy_buf,
        reinterpret_cast<void*>(obj_addr + 8),
        reinterpret_cast<void*>(obj_addr + 0x20),
        0
    );

    engine_func_002c3a24(&g_AsdSoundLock);

    return obj;
}
// DECOMP_FUNC(0x0010c5d4, 480)


// 0x0010c5d4 (480 B): open sequence slot `index` and publish the active one.
//
u32 AsdSoundSystem_func_0010c5d4(u32 index, u32 size)
{
    if (index >= 4) {
        return 0;
    }

    AsdSoundSystem& system = g_AsdSoundSystem;
    AsdSoundSequenceSlot& slot = system.sequences[index];

    if (slot.field_3a != 0) {
        return 0;
    }

    if (size != 0) {
        void* buf = AsdMem_AllocAlign(0x10000, 0x100, 0, size, 1);
        slot.field_30 = buf;
        AsdSoundSlot_Attach(&slot, buf, size);
        slot.field_34 = AsdSoundSlot_GetHandle(&slot);
        slot.field_3b = 1;
    }

    slot.field_3a = 1;
    slot.field_39 = static_cast<u8>(index);
    slot.field_38 = 0x40;

    g_AsdSoundStream.field_00 = 0.5f;
    g_AsdSoundStream.field_18 |= 1;
    g_AsdSoundStream.field_04 = 0x1e;
    g_AsdSoundStream.field_08 = 0x1e;
    g_AsdSoundStream.field_0c = 0x0f;
    g_AsdSoundStream.field_10 = 0x0f;

    if (g_AsdSoundStream.field_33 != 0) {
        g_AsdSoundStream.field_1a = 1;
    }

    for (s32 i = 0; i < 4; ++i) {
        if (system.sequences[i].field_3a != 0) {
            if (i == -1) {
                system.field_1218 = nullptr;
            } else if (static_cast<u32>(i) < 4) {
                if (system.sequences[i].field_3a != 0) {
                    for (u32 ch = 0; ch < 4; ++ch) {
                        if (system.sequences[i].field_20[ch] != nullptr) {
                            AsdSoundVoice_Stop(system.sequences[i].field_20[ch], 0);
                        }
                    }
                    system.sequences[i].field_38 = 0x40;
                    if (system.sequences[i].field_3b != 0) {
                        AsdSoundSlot_Stop(&system.sequences[i], system.sequences[i].field_34);
                    }
                    system.field_1218 = &system.sequences[i];
                }
            }
            break;
        }
    }

    return 1;
}
// DECOMP_FUNC(0x0010d40c, 516)


// 0x0010d40c (516 B): start the DSP/mixer and reset the sound-system state.
//
void AsdSoundSystem_func_0010d40c(s32 duration)
{
    if (AsdSound_InitDsp() < 0) {
        engine_func_002bce48();
    }
    if (engine_func_0011be44() < 0) {
        engine_func_002bce48();
    }
    if (engine_func_0011cb3c() < 0) {
        engine_func_002bce48();
    }

    engine_func_002bce38(1.0f);

    if (duration > 0) {
        AsdSound_SetPhase(0x1e);
        AsdSound_RequestMode(3);
    }

    AsdSoundInitConfig config;
    config.field_00 = 4;
    config.field_04 = (duration > 0) ? 1 : 0;
    config.field_08 = 0x4000;
    config.field_0c = 0x20000;
    config.field_10 = 3;
    config.field_14 = 0x4000;
    config.field_18 = 0x2000;
    config.field_1c = 1;
    config.field_1d = 0;
    config.field_1e = 1;
    config.field_20 = 0xFFFFFFFF;

    u32 engine_size = AsdSound_CreateEngine(&config);
    void* engine_buf = AsdMem_AllocAlign(0x10000, 0x100, 0, engine_size, 1);

    AsdSoundSystem& system = g_AsdSoundSystem;
    system.field_464 = engine_buf;

    AsdSound_InitEngine(&config, engine_buf, engine_size);

    system.streams[0].field_48 = 0x40;
    system.streams[1].field_48 = 0x40;
    system.streams[2].field_48 = 0x40;
    system.streams[3].field_48 = 0x40;

    system.field_630 = 0;
    system.field_634 = 0;
    system.field_635 = 0x40;

    system.field_66c = 0;
    system.field_670 = 0;
    system.field_671 = 0x40;

    system.field_67c = 0;
    system.field_680 = 0;
    system.field_681 = 0x40;
    system.field_682 = 0;

    system.field_68c = 0;
    system.field_690 = 0;
    system.field_691 = 0x40;
    system.field_692 = 0;

    system.sequences[0].field_38 = 0x40;
    system.sequences[0].field_3a = 0;
    system.sequences[0].field_3b = 0;

    system.sequences[1].field_38 = 0x40;
    system.sequences[1].field_3a = 0;
    system.sequences[1].field_3b = 0;

    system.sequences[2].field_38 = 0x40;
    system.sequences[2].field_3a = 0;
    system.sequences[2].field_3b = 0;

    system.sequences[3].field_38 = 0x40;
    system.sequences[3].field_3a = 0;
    system.sequences[3].field_3b = 0;

    system.field_11cc = 0;
    system.field_11cd = 0x40;

    g_AsdSoundStream.field_00 = 0.0f;
    g_AsdSoundStream.field_04 = 0;
    g_AsdSoundStream.field_08 = 0;
    g_AsdSoundStream.field_0c = 0;
    g_AsdSoundStream.field_10 = 0;
    g_AsdSoundStream.field_14 = 0;
    g_AsdSoundStream.field_18 = 0;
    g_AsdSoundStream.field_19 = 0;
    g_AsdSoundStream.field_1a = 0;
    g_AsdSoundStream.field_1c = 0;
    g_AsdSoundStream.field_20 = 0;
    g_AsdSoundStream.field_31 = 0;
    g_AsdSoundStream.field_33 = 0;

    system.field_121c = 0;
}
// DECOMP_FUNC(0x002c1df4, 308)


static void AsdSoundSystem_SetActiveStream(s32 index)
{
    AsdSoundSystem& system = g_AsdSoundSystem;
    if (index == -1) {
        system.field_1204 = nullptr;
    } else if (static_cast<u32>(index) < 4) {
        if (system.streams[index].field_10 != 0) {
            system.field_1204 = &system.streams[index];
            system.streams[index].field_4c = static_cast<u8>(index);
        }
    }
}

// 0x002c1df4 (308 B): open stream slot `index` and publish the active one.
//
u32 AsdSoundSystem_func_002c1df4(u32 index, u32 size)
{
    if (index >= 4) {
        return 0;
    }

    AsdSoundSystem& system = g_AsdSoundSystem;
    AsdSoundStream& slot = system.streams[index];

    if (slot.field_10 != 0) {
        return 0;
    }

    void* buf = AsdMem_AllocAlign(0x10000, 0x100, 0, size, 1);
    slot.field_40 = buf;
    AsdSoundSlot_Attach(&slot, buf, size);
    slot.field_48 = 0x40;
    slot.field_44 = AsdSoundSlot_GetHandle(&slot);

    for (s32 i = 0; i < 4; ++i) {
        if (system.streams[i].field_10 != 0) {
            AsdSoundSystem_SetActiveStream(i);
            break;
        }
    }

    return 1;
}
// DECOMP_FUNC(0x001ea808, 264)


// ---------------------------------------------------------------------------
// soundTest (c:\SMT4\XRD686\sdds4\program\sound\soundTest.cpp)
// ---------------------------------------------------------------------------

// 0x001ea808 (264 B): create the two sound-test UI widgets.
//
void soundTest_func_001ea808()
{
    AsdSoundTestObject* obj = reinterpret_cast<AsdSoundTestObject*>(
        AsdMem_Alloc(0x100, 0x100, 0, sizeof(AsdSoundTestObject), 1)
    );
    g_SoundTestObject = obj;

    obj->field_08 = 0;
    obj->field_0c = 0;
    obj->field_10 = 0;
    obj->field_04 = 0;

    void* calc_task = AsdTask_CreateCalc(
        "ST C",
        2,
        0,
        0,
        reinterpret_cast<void(*)(void*)>(0x001e9518),
        0x002ca68c,
        0
    );
    obj->ui = calc_task;

    AsdTask_CreateDraw(
        "ST D",
        0xe6,
        0,
        0,
        reinterpret_cast<void(*)(void*)>(0x002ca6a4),
        0x002f4aec,
        0,
        calc_task
    );
}

} // namespace smt4::engine
