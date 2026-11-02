#include <cstdint>

extern "C" int32_t candidate_002c1f28() {
    auto globals = reinterpret_cast<const uint8_t*>(0x0043e0b8);
    auto enabled = *reinterpret_cast<const int32_t*>(globals + 4);
    if (enabled < 0) {
        return *reinterpret_cast<const int8_t*>(globals);
    }
    return 0;
}
