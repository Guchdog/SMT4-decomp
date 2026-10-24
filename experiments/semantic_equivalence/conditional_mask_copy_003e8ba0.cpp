#include <cstdint>

using u32 = std::uint32_t;

// Isolated ordinary-RAM model of 0x003E8BA0. The flag word is deliberately
// re-read before every lane: an earlier destination write may alias it.
extern "C" __attribute__((noinline, used)) u32 candidate_003e8ba0(
    u32, volatile u32* destination, const volatile u32* source) {
    const volatile u32* flags = source + 1;
    const volatile u32* payload = source + 2;
    u32 result = static_cast<u32>(reinterpret_cast<std::uintptr_t>(payload));

    if ((*flags & 1u) != 0) destination[0] = payload[0];
    if ((*flags & 2u) != 0) destination[1] = payload[1];
    if ((*flags & 4u) != 0) destination[2] = payload[2];
    if ((*flags & 8u) != 0) {
        const u32 lane = payload[3];
        destination[3] = lane;
        result = lane;
    }

    return result;
}

extern "C" __attribute__((noinline, used)) u32 negative_wrong_first_lane_003e8ba0(
    u32, volatile u32* destination, const volatile u32* source) {
    const volatile u32* flags = source + 1;
    const volatile u32* payload = source + 2;
    u32 result = static_cast<u32>(reinterpret_cast<std::uintptr_t>(payload));

    if ((*flags & 1u) != 0) destination[0] = payload[0] ^ 1u;
    if ((*flags & 2u) != 0) destination[1] = payload[1];
    if ((*flags & 4u) != 0) destination[2] = payload[2];
    if ((*flags & 8u) != 0) {
        const u32 lane = payload[3];
        destination[3] = lane;
        result = lane;
    }

    return result;
}
