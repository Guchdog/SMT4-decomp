#include "types.h"

extern "C" u32 camp_func_002892c0(void* object, u32 index);

extern "C" u32 candidate_0029edfc(void* object, u32 index) {
    auto* const bytes = static_cast<u8*>(object);
    const u8 disabled = bytes[0x62];
    if (disabled != 0) {
        return disabled;
    }

    const u32 end = *reinterpret_cast<const u32*>(bytes + 0x24);
    const u32 start = *reinterpret_cast<const u32*>(bytes + 0x20);
    if (end + start != index) {
        bytes[0x60] = 1;
    }
    return camp_func_002892c0(object, index);
}
