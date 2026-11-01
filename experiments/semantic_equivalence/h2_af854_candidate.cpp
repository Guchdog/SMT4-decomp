#include <cstdint>

extern "C" uint8_t* candidate_002af854(uint8_t* object, uint32_t index, uint32_t mode) {
    auto list = *reinterpret_cast<const uint32_t* const*>(object + 0x58);
    if (list == nullptr) {
        return object;
    }

    *reinterpret_cast<volatile uint16_t*>(object + 0x5c) = static_cast<uint16_t>(index);
    *reinterpret_cast<volatile uint16_t*>(object + 0x5e) = 0;
    *reinterpret_cast<volatile uint8_t*>(object + 0x87) = 0;
    *reinterpret_cast<volatile uint8_t*>(object + 0x8a) = 0;
    *reinterpret_cast<volatile uint8_t*>(object + 0x60) = static_cast<uint8_t>(mode);

    auto entry = reinterpret_cast<const uint8_t*>(list) + index * 12u;
    auto selected = *reinterpret_cast<const volatile uint32_t*>(entry + (mode != 0 ? 4 : 0));
    *reinterpret_cast<uint32_t*>(object + 0x20) = selected;
    return object;
}
