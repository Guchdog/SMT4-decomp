#pragma once
#include <cstdint>
#include "types.h"

/**
 * Shared engine call targets referenced from more than one reconstructed
 * translation unit.
 *
 * Keeping one declaration per binary address/linkage prevents the AsdText,
 * AsdModel and AsdTexture TUs from disagreeing about a helper's name,
 * argument count or language linkage.
 */

namespace smt4::engine {

// 0x002C23F8 (56 B, AsdMemory.cpp): aligned 0x100/0x100 allocation.
// Defined in src/engine/asd_texture.cpp with C++ linkage (ledger entry).
void* AsdMemory_func_002c23f8(u32 size);

} // namespace smt4::engine

extern "C" {
    // 0x002BCE48 (8 B): tail-calls 0x002AD8A8 with 0.  Shared by the file,
    // sound and Mobiclip paths as a "close/yield" notification.
    void AsdFile_NotifyClose();

    // 0x002C583C (16 B): global table slot lookup (`ldr r0,[table+index*4]`).
    void* AsdSound_GetTableEntry(u32 index);

    // 0x002C5F7C / 0x002C5FA4: GPU viewport selection and primitive/render
    // mode selection.  These are the canonical spellings used by the UI TUs;
    // the battle title/enemy-draw paths reach the same routines.
    void* UiGpu_SetViewportParams(s32 a0, s32 a1);
    void* UiGpu_SetRenderMode(s32 a0, s32 a1, s32 a2);

    // 0x002BCE38 (12 B): master-volume update; the value arrives in s0.
    void AsdSound_SetMasterVolume(f32 volume);

    // 0x002C5978 (48 B) / 0x002C4C00 (44 B): AsdProcess task factories.
    // The final three/four arguments are the stack words observed at every
    // call site: calculation callback, draw callback and user context.
    void* AsdTask_CreateCalc(const char* name, u32 prio, u32 a2, u32 a3,
                             void (*calc_cb)(void*), u32 a5, u32 a6);
    void* AsdTask_CreateDraw(const char* name, u32 prio, u32 a2, u32 a3,
                             void (*calc_cb)(void*), u32 a5, u32 a6,
                             void* parent);

    // 0x002C3AA8 (56 B) / 0x002C3A24 (32 B): AsdMemory heap lock
    // acquisition/release.  AsdFile and AsdSound both reach these routines;
    // the AsdMemLock_* spelling is canonical.
    void  AsdMemLock_Acquire(void* lock);
    void  AsdMemLock_Release(void* lock);

    // 0x002C1A48 (116 B): Thumb memcmp shared by AsdModel (tag checks) and
    // AsdSound (path prefix checks).
    s32   AsdMem_Compare(const void* a, const void* b, u32 size);

    // 0x0011BE44 (120 B) / 0x0011CB3C (184 B): mixer and stream bring-up used
    // by AsdSoundSystem and the Mobiclip audio helper.
    s32   AsdSound_InitMixer();
    s32   AsdSound_InitStream();

    // 0x002C4460 (320 B): links `child` into the child list of `parent`
    // (AsdProcess pool at 0x004E3CF4).  AsdText reaches the same routine for
    // widget attachment, so the declaration lives here for both TUs.
    void AsdProc_Attach(void* parent, void* child);

    // 0x002C4450 (16 B): broadcasts the low byte of `value` and tail-calls
    // the byte fill at 0x002C3B4C; `size` is therefore a byte count.
    void AsdMem_FillBytes(void* dst, u32 size, u32 value);

    // 0x00262B60 (108 B): strncpy(dst, src, size); returns dst.
    char* AsdString_Copy(char* dst, const char* src, u32 size);

    // 0x002BF86C (104 B): strcpy(dst, src); returns dst.
    char* AsdString_Strcpy(char* dst, const char* src);

    // 0x002C3290 (96 B): strlen(s).
    u32   AsdString_Length(const char* s);

    // 0x002BCF58 (116 B): aligned fast path reached from memcpy 0x002C5FF4.
    void  AsdMem_CopyLarge(void* dst, const void* src, u32 size);

    // 0x002BD610 (16 B): swaps r0/r1 and tail-calls memcpy 0x002C5FF4, so the
    // first argument is the source and the second the destination.
    // Used by AsdModel (EPLSIGN header reads) and AsdSaveCommon (record split).
    void  AsdMem_CopyFrom(const void* src, void* dst, u32 size);

    // 0x002C3B48 (64 B): zero-fill of a whole number of words.  Reached from
    // AsdModel (work-buffer clear) and AsdFile/AsdMemory (heap windows).
    void  AsdWork_Zero(void* ptr, u32 size);

    // 0x0024DFA4 (184 B): resets `object` (r0 is consumed: `movs r5,r0` at
    // 0x0024DFA8, null check at 0x0024DFB0) and returns it.  Reached from
    // AsdModel (0x002FD520) and EffectEditor (0x00242588).
    void* AsdUiObject_CreateAndReset(void* object);

    // 0x002C0BA8 (12 B): event-flag query, returning the 0/1 bit result.  The
    // CampCec, title and status TUs all reach this routine.
    bool  Flag_CheckEventBit(u32 flag_id);

    // 0x001A7F30 (116 B) / 0x002A0640 (56 B): BGM sequence helpers shared by
    // the CampCec boot path and the title/play-log flows.  0x002A0640 only
    // forwards when sound-table slot 1 is still empty.
    void  Sound_SetSequenceState(u32 mode);
    void  Sound_RequestBgm(u32 id, u32 volume, u32 frames);

    // 0x0032FEF4 (88 B): resets the 0x0043E158 RunWin panel (formats its title
    // at +0xC4, sets +0x14/+0x08 and requests 0x010001FD).  Reached from the
    // CampCec main-menu boot path.
    void  RunWin_OpenDefault();

    // 0x00433158: camp / NPC row-bundle pointer.  The listing loads the value
    // stored here (`ldr r0,[r5]`, 0x002FE088) before calling the row helpers,
    // so the slot itself is a non-const pointer.  aocFileLoad reads the same
    // slot as its path root (0x0015C830), so this is the one canonical name
    // for the address; `g_AocPathRoot` was a duplicate alias.
    extern void* g_CampMessageBundle;
}

// 0x002C5978 / 0x002C4C00 are the AsdProcess task factories declared above.
// The AsdFrame / AsdScene / AsdSound / AsdText TUs historically called them
// through the AsdUi_* spelling (the widget-like name is the shipped source's
// vocabulary); these global adapters keep that call shape without introducing
// a second declaration for either address.
static inline void* AsdUi_Create(const char* kind, std::uintptr_t name, u32 a2,
                          u32 a3, u32 cb0, u32 cb1, void* obj)
{
    return AsdTask_CreateCalc(
        kind, static_cast<u32>(name), a2, a3,
        reinterpret_cast<void (*)(void*)>(static_cast<std::uintptr_t>(cb0)),
        cb1, static_cast<u32>(reinterpret_cast<std::uintptr_t>(obj)));
}

static inline void* AsdUi_CreateLabel(const char* name, u32 id, u32 a1, u32 a2,
                               u32 p0, u32 p1, void* p2, u32 p3)
{
    return AsdTask_CreateDraw(
        name, id, a1, a2,
        reinterpret_cast<void (*)(void*)>(static_cast<std::uintptr_t>(p0)),
        p1, static_cast<u32>(reinterpret_cast<std::uintptr_t>(p2)),
        reinterpret_cast<void*>(static_cast<std::uintptr_t>(p3)));
}
