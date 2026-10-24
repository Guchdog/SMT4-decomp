#include <cstdint>

// Isolated model of the title callback's two touch scans only.
// `touch_state[i]` is assumed stable across the two original helper calls.
// No claim is made about the helper's physical input or timing semantics.
extern "C" std::uint32_t title_touch_reduce(
    std::uint8_t* work, const std::int32_t* touch_state) {
    for (std::uint32_t i = 0; i < 4; ++i) {
        const std::int32_t state = touch_state[i];
        if (state == 1 || state == 2) {
            *reinterpret_cast<std::uint32_t*>(work + 8) = i;
            break;
        }
    }

    for (std::uint32_t i = 0; i < 4; ++i) {
        if (touch_state[i] == 6) {
            *reinterpret_cast<std::uint32_t*>(work + 8) = i;
            work[0x63] = 1;
        }
    }

    return *reinterpret_cast<std::uint32_t*>(work + 8);
}
