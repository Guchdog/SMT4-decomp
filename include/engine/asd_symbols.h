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
    // 0x00262B60 (108 B): strncpy(dst, src, size); returns dst.
    char* AsdString_Copy(char* dst, const char* src, u32 size);

    // 0x002BF86C (104 B): strcpy(dst, src); returns dst.
    char* AsdString_Strcpy(char* dst, const char* src);

    // 0x002C3290 (96 B): strlen(s).
    u32   AsdString_Length(const char* s);

    // 0x002BCF58 (116 B): aligned fast path reached from memcpy 0x002C5FF4.
    void  AsdMem_CopyLarge(void* dst, const void* src, u32 size);
}
