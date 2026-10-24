#include <cstdint>

// Isolated modular pointer arithmetic candidates. The halfword gate controls
// whether the 32-bit displacement is read at all.
extern "C" __attribute__((noinline, used)) uint32_t candidate_003e698c(
    const uint8_t* object) {
    const uint16_t tag = *reinterpret_cast<const volatile uint16_t*>(object + 8);
    if (tag != 0x101) return 0;
    const uint32_t displacement =
        *reinterpret_cast<const volatile uint32_t*>(object + 0x0c);
    return static_cast<uint32_t>(reinterpret_cast<uintptr_t>(object)) + displacement;
}

extern "C" __attribute__((noinline, used)) uint32_t candidate_003e69c0(
    const uint8_t* object) {
    const uint16_t tag = *reinterpret_cast<const volatile uint16_t*>(object + 0x10);
    if (tag != 0x101) return 0;
    const uint32_t displacement =
        *reinterpret_cast<const volatile uint32_t*>(object + 0x14);
    return static_cast<uint32_t>(reinterpret_cast<uintptr_t>(object)) + displacement;
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_tag_offset_003e698c(
    const uint8_t* object) {
    const uint16_t tag = *reinterpret_cast<const volatile uint16_t*>(object + 0x0a);
    if (tag != 0x101) return 0;
    return static_cast<uint32_t>(reinterpret_cast<uintptr_t>(object)) +
           *reinterpret_cast<const volatile uint32_t*>(object + 0x0c);
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_disp_offset_003e698c(
    const uint8_t* object) {
    const uint16_t tag = *reinterpret_cast<const volatile uint16_t*>(object + 8);
    if (tag != 0x101) return 0;
    return static_cast<uint32_t>(reinterpret_cast<uintptr_t>(object)) +
           *reinterpret_cast<const volatile uint32_t*>(object + 0x10);
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_add_003e698c(
    const uint8_t* object) {
    const uint16_t tag = *reinterpret_cast<const volatile uint16_t*>(object + 8);
    if (tag != 0x101) return 0;
    return *reinterpret_cast<const volatile uint32_t*>(object + 0x0c);
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_tag_offset_003e69c0(
    const uint8_t* object) {
    const uint16_t tag = *reinterpret_cast<const volatile uint16_t*>(object + 0x12);
    if (tag != 0x101) return 0;
    return static_cast<uint32_t>(reinterpret_cast<uintptr_t>(object)) +
           *reinterpret_cast<const volatile uint32_t*>(object + 0x14);
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_disp_offset_003e69c0(
    const uint8_t* object) {
    const uint16_t tag = *reinterpret_cast<const volatile uint16_t*>(object + 0x10);
    if (tag != 0x101) return 0;
    return static_cast<uint32_t>(reinterpret_cast<uintptr_t>(object)) +
           *reinterpret_cast<const volatile uint32_t*>(object + 0x18);
}

extern "C" __attribute__((noinline, used)) uint32_t wrong_add_003e69c0(
    const uint8_t* object) {
    const uint16_t tag = *reinterpret_cast<const volatile uint16_t*>(object + 0x10);
    if (tag != 0x101) return 0;
    return *reinterpret_cast<const volatile uint32_t*>(object + 0x14);
}
