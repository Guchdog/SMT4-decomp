#include <cstdint>

// Isolated reconstructions of two signedness-sensitive byte predicates.
// Both return exactly 0 or 1 and do not write memory.
extern "C" __attribute__((noinline, used)) uint32_t candidate_00126430(
    const uint8_t* object) {
    return object[0x44] == 2;
}

extern "C" __attribute__((noinline, used)) uint32_t candidate_0027ec84(
    const uint8_t* object) {
    return object[0] == 0;
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_offset_00126430(
    const uint8_t* object) {
    return object[0x45] == 2;
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_constant_00126430(
    const uint8_t* object) {
    return object[0x44] == 3;
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_sense_00126430(
    const uint8_t* object) {
    return object[0x44] != 2;
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_offset_0027ec84(
    const uint8_t* object) {
    return object[1] == 0;
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_constant_0027ec84(
    const uint8_t* object) {
    return object[0] == 1;
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_sense_0027ec84(
    const uint8_t* object) {
    return object[0] != 0;
}
