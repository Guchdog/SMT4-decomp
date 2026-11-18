#include "types.h"

using VectorCtor = u32 (*)(void*, void*, u32, u32);

extern "C" u32 h18_003f3454_candidate() {
    *reinterpret_cast<u32*>(0x00471A38u) = 0;
    *reinterpret_cast<u32*>(0x00471A40u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x00471A44u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x00471A48u) = 0;
    *reinterpret_cast<u32*>(0x00471A4Cu) = 0;

    const auto vector_ctor = reinterpret_cast<VectorCtor>(0x002C5F50u);
    return vector_ctor(reinterpret_cast<void*>(0x004E62C0u),
                       reinterpret_cast<void*>(0x00353120u), 8u, 0x40u);
}

extern "C" u32 h18_003f34a0_candidate() {
    *reinterpret_cast<u32*>(0x00472570u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x00472574u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x00472578u) = 0;
    *reinterpret_cast<u32*>(0x0047257Cu) = 0;
    return 0x00472578u;
}

extern "C" u32 h18_003f34cc_candidate() {
    *reinterpret_cast<u32*>(0x00472798u) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x0047279Cu) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(0x004727A0u) = 0;
    *reinterpret_cast<u32*>(0x004727A4u) = 0;
    return 0x004727A0u;
}
