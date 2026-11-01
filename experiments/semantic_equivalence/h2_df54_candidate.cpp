#include <stdint.h>

extern "C" uint32_t candidate_0028df54(uint32_t value) {
    auto base = reinterpret_cast<uint8_t*>(0x0044de98);
    auto state = *reinterpret_cast<uint8_t**>(base + 0x20);
    state[0x3b] = 0;
    *reinterpret_cast<uint32_t*>(state + 0xa8) = value;
    return value;
}
