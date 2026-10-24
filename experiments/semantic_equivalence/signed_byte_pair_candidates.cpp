#include <stdint.h>

// Isolated signed-byte field getters. These preserve byte-width volatile reads
// and ARM signed extension; they are experimental, not production code.
extern "C" __attribute__((noinline, used)) int32_t candidate_003e6368(
    const uint8_t* object) {
    return *reinterpret_cast<volatile const int8_t*>(object + 0x556);
}

extern "C" __attribute__((noinline, used)) int32_t candidate_003e8878(
    const uint8_t* object) {
    return *reinterpret_cast<volatile const int8_t*>(object + 0x45E);
}

// Deliberately incorrect controls used to prove the tests discriminate offset,
// access width, and signedness errors.
extern "C" __attribute__((noinline, used)) int32_t wrong_offset_003e6368(
    const uint8_t* object) {
    return *reinterpret_cast<volatile const int8_t*>(object + 0x557);
}

extern "C" __attribute__((noinline, used)) int32_t wrong_offset_003e8878(
    const uint8_t* object) {
    return *reinterpret_cast<volatile const int8_t*>(object + 0x45F);
}

extern "C" __attribute__((noinline, used)) int32_t wrong_width_003e6368(
    const uint8_t* object) {
    return *reinterpret_cast<volatile const int16_t*>(object + 0x556);
}

extern "C" __attribute__((noinline, used)) int32_t wrong_width_003e8878(
    const uint8_t* object) {
    return *reinterpret_cast<volatile const int16_t*>(object + 0x45E);
}

extern "C" __attribute__((noinline, used)) int32_t wrong_sign_003e6368(
    const uint8_t* object) {
    return *reinterpret_cast<volatile const uint8_t*>(object + 0x556);
}

extern "C" __attribute__((noinline, used)) int32_t wrong_sign_003e8878(
    const uint8_t* object) {
    return *reinterpret_cast<volatile const uint8_t*>(object + 0x45E);
}
