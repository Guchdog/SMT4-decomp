#include <cstdint>

using u32 = uint32_t;

// Isolated C++ candidates only; these are not production implementations.
extern "C" __attribute__((noinline, used)) u32 candidate_00146ce0(
    volatile uint8_t* object, u32 value) {
    volatile uint16_t* field = reinterpret_cast<volatile uint16_t*>(object + 0x34);
    const u32 previous = *field;
    *field = static_cast<uint16_t>(value);
    return previous;
}

extern "C" __attribute__((noinline, used)) int32_t candidate_00146d10(
    volatile uint8_t* object, u32 value) {
    volatile int8_t* field = reinterpret_cast<volatile int8_t*>(object + 0x38);
    const int32_t previous = *field;
    *field = static_cast<int8_t>(value);
    return previous;
}

extern "C" __attribute__((noinline, used)) u32 candidate_002523c0(
    const volatile u32* field) {
    return *field == 1u ? 1u : 0u;
}

extern "C" __attribute__((noinline, used)) u32 wrong_offset_00146ce0(
    volatile uint8_t* object, u32 value) {
    volatile uint16_t* field = reinterpret_cast<volatile uint16_t*>(object + 0x38);
    const u32 previous = *field;
    *field = static_cast<uint16_t>(value);
    return previous;
}

extern "C" __attribute__((noinline, used)) u32 wrong_unsigned_return_00146d10(
    volatile uint8_t* object, u32 value) {
    volatile uint8_t* field = object + 0x38;
    const u32 previous = *field;
    *field = static_cast<uint8_t>(value);
    return previous;
}

extern "C" __attribute__((noinline, used)) u32 wrong_comparison_002523c0(
    const volatile u32* field) {
    return *field == 2u ? 1u : 0u;
}
