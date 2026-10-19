#pragma once

#include "types.h"

namespace smt4::script {

constexpr u32 kFlw0Magic = 0x30574C46; // 'FLW0'
constexpr u32 kMsg1Magic = 0x3147534D; // 'MSG1'

struct BfSectionEntry {
    u32 section_type; // 0 = Procedure labels, 1 = Branch labels, 2 = Bytecode, 3 = MSG1, 4 = Strings
    u32 element_size;
    u32 count;
    u32 offset;
};

struct BfHeader {
    u8 file_type;
    u8 compressed;
    u16 user_id;
    u32 file_size;
    u32 magic; // 'FLW0'
    u32 reserved;
    u32 section_count;
    u16 local_int_count;
    u16 local_float_count;
    u8 padding[8];
};

} // namespace smt4::script
