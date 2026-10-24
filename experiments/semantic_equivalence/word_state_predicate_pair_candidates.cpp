#include <cstdint>

static uint32_t load_state_field(const uint8_t* object) {
    const uintptr_t address = reinterpret_cast<uintptr_t>(object) + 0x3048u;
    return *reinterpret_cast<const volatile uint32_t*>(address);
}

extern "C" __attribute__((noinline, used)) uint32_t candidate_0028c290(
    const uint8_t* object) {
    return load_state_field(object) == 7;
}

extern "C" __attribute__((noinline, used)) uint32_t candidate_002e42e0(
    const uint8_t* object) {
    return load_state_field(object) == 2;
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_offset_0028c290(
    const uint8_t* object) {
    const uintptr_t address = reinterpret_cast<uintptr_t>(object) + 0x304c;
    return *reinterpret_cast<const volatile uint32_t*>(address) == 7;
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_constant_0028c290(
    const uint8_t* object) {
    return load_state_field(object) == 6;
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_sense_0028c290(
    const uint8_t* object) {
    return load_state_field(object) != 7;
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_offset_002e42e0(
    const uint8_t* object) {
    const uintptr_t address = reinterpret_cast<uintptr_t>(object) + 0x304c;
    return *reinterpret_cast<const volatile uint32_t*>(address) == 2;
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_constant_002e42e0(
    const uint8_t* object) {
    return load_state_field(object) == 3;
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_sense_002e42e0(
    const uint8_t* object) {
    return load_state_field(object) != 2;
}
