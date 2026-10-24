#include <stdint.h>

extern "C" __attribute__((noinline, used)) void candidate_00140854(
    uint8_t* record) {
    volatile uint32_t* const words = reinterpret_cast<volatile uint32_t*>(record);
    volatile uint16_t* const halves = reinterpret_cast<volatile uint16_t*>(record);
    volatile uint8_t* const bytes = reinterpret_cast<volatile uint8_t*>(record);
    words[1] = 0;
    halves[4] = 0;
    words[3] = 0;
    halves[8] = 0;
    words[5] = 0;
    words[6] = 0;
    words[7] = 0xFFFFFFFF;
    words[11] = 0;
    words[12] = 0;
    words[0xB8 / 4] = 0;
    halves[0xBC / 2] = 0;
    words[0xC0 / 4] = 0;
    halves[0xC4 / 2] = 0;
    words[0xC8 / 4] = 0;
    words[0xCC / 4] = 0;
    words[0xD0 / 4] = 0xFFFFFFFF;
    words[0xE0 / 4] = 0;
    words[0xE4 / 4] = 0;
    bytes[0x18D] = 0;
}

extern "C" __attribute__((noinline, used)) void negative_wrong_record_sentinel(
    uint8_t* record) {
    volatile uint32_t* const words = reinterpret_cast<volatile uint32_t*>(record);
    words[7] = 0;
}

extern "C" __attribute__((noinline, used)) void negative_omit_record_tail(
    uint8_t* record) {
    volatile uint8_t* const bytes = reinterpret_cast<volatile uint8_t*>(record);
    bytes[0x18D] = 0;
}
