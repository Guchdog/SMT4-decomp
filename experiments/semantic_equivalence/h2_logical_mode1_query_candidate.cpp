#include "types.h"

extern "C" s32 candidate_002bffbc(u32 id) {
    if (id >= 0x1fu) {
        return 0;
    }

    const u32 input_flags = *reinterpret_cast<const u32*>(0x004650A8);
    if ((input_flags & 1u) != 0) {
        return 0;
    }

    const u32 counter = *reinterpret_cast<const u32*>(0x004E3C58u + id * 4u);
    return counter == 1u ? 1 : 0;
}

// Negative controls: one checks the wrong flag bit; the other reads ID+1.
extern "C" s32 candidate_002bffbc_bad_flag(u32 id) {
    if (id >= 0x1fu) {
        return 0;
    }

    const u32 input_flags = *reinterpret_cast<const u32*>(0x004650A8);
    if ((input_flags & 2u) != 0) {
        return 0;
    }

    const u32 counter = *reinterpret_cast<const u32*>(0x004E3C58u + id * 4u);
    return counter == 1u ? 1 : 0;
}

extern "C" s32 candidate_002bffbc_bad_counter(u32 id) {
    if (id >= 0x1fu) {
        return 0;
    }

    const u32 input_flags = *reinterpret_cast<const u32*>(0x004650A8);
    if ((input_flags & 1u) != 0) {
        return 0;
    }

    const u32 counter = *reinterpret_cast<const u32*>(0x004E3C58u + (id + 1u) * 4u);
    return counter == 1u ? 1 : 0;
}

extern "C" s32 candidate_002bffbc_bad_bound(u32 id) {
    if (id > 0x1fu) {
        return 0;
    }

    const u32 input_flags = *reinterpret_cast<const u32*>(0x004650A8);
    if ((input_flags & 1u) != 0) {
        return 0;
    }

    const u32 counter = *reinterpret_cast<const u32*>(0x004E3C58u + id * 4u);
    return counter == 1u ? 1 : 0;
}
