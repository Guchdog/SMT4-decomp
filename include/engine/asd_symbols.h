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
}
