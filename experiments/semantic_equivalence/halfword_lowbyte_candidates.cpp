#include <cstdint>

// Isolated candidates for two adjacent record-field getters. These preserve
// the original halfword load footprint, then return only its low byte.
extern "C" __attribute__((noinline, used)) uint32_t candidate_002345f0(
    const uint8_t* object) {
    const auto value = *reinterpret_cast<const volatile uint16_t*>(object + 0x48);
    return value & 0xffu;
}

extern "C" __attribute__((noinline, used)) uint32_t candidate_002345fc(
    const uint8_t* object) {
    const auto value = *reinterpret_cast<const volatile uint16_t*>(object + 0x4a);
    return value & 0xffu;
}

// Negative controls intentionally either shift the field by one byte or
// return the full halfword instead of masking away its high byte.
extern "C" __attribute__((noinline, used)) uint32_t wrong_offset_002345f0(
    const uint8_t* object) {
    const auto value = *reinterpret_cast<const uint16_t*>(object + 0x49);
    return value & 0xffu;
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_mask_002345f0(
    const uint8_t* object) {
    return *reinterpret_cast<const uint16_t*>(object + 0x48);
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_offset_002345fc(
    const uint8_t* object) {
    const auto value = *reinterpret_cast<const uint16_t*>(object + 0x4b);
    return value & 0xffu;
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_mask_002345fc(
    const uint8_t* object) {
    return *reinterpret_cast<const uint16_t*>(object + 0x4a);
}
