#include "types.h"

extern "C" u32 candidate_002c17d4(u32 id) {
    if (id >= 31u) {
        return 0;
    }

    auto* const row = reinterpret_cast<const u32*>(0x004099C0u + id * 8u);
    if (row[0] != 0u) {
        return 0;
    }

    const u32 mask = row[1];
    const u32 mode = *reinterpret_cast<const u32*>(0x004650A8u);
    const u32 state_address = (mode & 1u) != 0u ? 0x004E3C48u : 0x004E3C28u;
    const u32 state = *reinterpret_cast<const u32*>(state_address);
    return (state & mask) != 0u ? 1u : 0u;
}
