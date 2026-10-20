#pragma once
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

    // 0x00433158: camp / NPC row-bundle pointer.  The listing loads the value
    // stored here (`ldr r0,[r5]`, 0x002FE088) before calling the row helpers,
    // so the slot itself is a non-const pointer.
    extern void* g_CampMessageBundle;
}
