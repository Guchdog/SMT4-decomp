#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::camp {

/**
 * Camp Demonica Archive & Resource Streamer Workspace.
 * Original Atlus source path: `c:\SMT4\XRD686\AsdSDK\Source\Sys\File\AsdFile.cpp`
 */
struct CampArchiveWork {
    void* file_handle;              // +0x00: AsdFile streaming handle
    void* decompressed_buffer;      // +0x04: Memory buffer for camp UI assets
    u32 archive_size;               // +0x08: Packed asset byte size
    u32 load_state;                 // +0x0C: 0 = uninit, 1 = reading, 2 = complete
};

/**
 * Streams camp archive files into RAM for Demonica UI rendering.
 *
 * Address: 0x00114374, Size: 6,144 bytes
 */
void Camp_DemonicaArchiveLoad(CampArchiveWork* work, const char* archive_path);

} // namespace smt4::camp
