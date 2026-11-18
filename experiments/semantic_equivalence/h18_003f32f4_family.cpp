#include "types.h"

// Related startup initializers recovered from the 0x003f31d8 compound span.
// Each entry writes one pair of -1 sentinels and a separate pair of zeros.

extern "C" void candidate_003f32f4() {
    *reinterpret_cast<u32*>(0x00464C68u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x00464C6Cu) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x00464C70u) = 0u;
    *reinterpret_cast<u32*>(0x00464C74u) = 0u;
}

// This entry's first literal is a base; its -1 pair starts at base + 8.
extern "C" void candidate_003f3320() {
    *reinterpret_cast<u32*>(0x00433E20u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x00433E24u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x00433E28u) = 0u;
    *reinterpret_cast<u32*>(0x00433E2Cu) = 0u;
}

extern "C" void candidate_003f334c() {
    *reinterpret_cast<u32*>(0x004719C8u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x004719CCu) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x004719D0u) = 0u;
    *reinterpret_cast<u32*>(0x004719D4u) = 0u;
}

extern "C" void candidate_003f3378() {
    *reinterpret_cast<u32*>(0x00471C30u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x00471C34u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x00471C38u) = 0u;
    *reinterpret_cast<u32*>(0x00471C3Cu) = 0u;
}

extern "C" void candidate_003f33a4() {
    *reinterpret_cast<u32*>(0x00433070u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x00433074u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x00433078u) = 0u;
    *reinterpret_cast<u32*>(0x0043307Cu) = 0u;
}

extern "C" void candidate_003f33d0() {
    *reinterpret_cast<u32*>(0x004330C0u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x004330C4u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x004330C8u) = 0u;
    *reinterpret_cast<u32*>(0x004330CCu) = 0u;
}

extern "C" void candidate_003f33fc() {
    *reinterpret_cast<u32*>(0x00433148u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x0043314Cu) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x00433150u) = 0u;
    *reinterpret_cast<u32*>(0x00433154u) = 0u;
}

// Like 0x003f3320, this entry stores its -1 pair at literal base + 8.
extern "C" void candidate_003f3428() {
    *reinterpret_cast<u32*>(0x0044E5A0u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x0044E5A4u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x0044E5A8u) = 0u;
    *reinterpret_cast<u32*>(0x0044E5ACu) = 0u;
}
