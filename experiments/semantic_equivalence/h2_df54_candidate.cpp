#include <stdint.h>

extern "C" __attribute__((minsize)) uint32_t candidate_0028df54(uint32_t value) {
    auto* const state = *reinterpret_cast<uint8_t* volatile*>(0x0044deb8);
    auto* const bytes = reinterpret_cast<volatile uint8_t*>(state);
    bytes[0x3b] = 0;
    *reinterpret_cast<volatile uint32_t*>(bytes + 0xa8) = value;
    return value;
}
