#include "types.h"

extern "C" u32 candidate_00297674() {
    auto* const object = *reinterpret_cast<u32**>(0x0043E190u);
    return *reinterpret_cast<u32*>(reinterpret_cast<u8*>(object) + 0x1Cu);
}
