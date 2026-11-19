#include "types.h"

// Recovered static initialization at 0x003f3274.
extern "C" void candidate_003f3274() {
    u32* const first_pair = reinterpret_cast<u32*>(0x00465080u);
    first_pair[0] = 0xFFFFFFFFu;
    first_pair[1] = 0xFFFFFFFFu;

    u32* const second_pair = reinterpret_cast<u32*>(0x00465088u);
    second_pair[0] = 0u;
    second_pair[1] = 0u;

    u8* const config = reinterpret_cast<u8*>(0x004E39E0u);
    *reinterpret_cast<u32*>(config + 0x1D4u) = 0x00100000u;
    *reinterpret_cast<u32*>(config + 0x1D8u) = 0x00000800u;
    *reinterpret_cast<u32*>(config + 0x1DCu) = 0x00080000u;
    *reinterpret_cast<u32*>(config + 0x1E0u) = 0x00000080u;
    *reinterpret_cast<u32*>(config + 0x1E4u) = 0x00080000u;
    *reinterpret_cast<u32*>(config + 0x1E8u) = 0u;
    *reinterpret_cast<u32*>(config + 0x1ECu) = 0x00000500u;
    *reinterpret_cast<u32*>(config + 0x1F0u) = 0u;
    *reinterpret_cast<u32*>(config + 0x1F4u) = 0u;
    *reinterpret_cast<u32*>(config + 0x1F8u) = 0x00008058u;
    *reinterpret_cast<u32*>(config + 0x1FCu) = 0x00008051u;
}
