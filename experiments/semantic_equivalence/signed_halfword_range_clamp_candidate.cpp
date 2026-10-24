#include <stdint.h>

extern "C" __attribute__((noinline, used)) void candidate_001285c4(
    volatile int16_t* fields) {
    const int16_t first = fields[0];
    if (first < 40) fields[0] = 40;
    const int16_t second = fields[1];
    if (second < 36) fields[1] = 36;
    const int16_t third = fields[3];
    if (third > 145) fields[3] = 145;
    const int16_t fourth = fields[4];
    if (fourth > 145) fields[4] = 145;
    const int16_t fifth = fields[5];
    if (fifth > 145) fields[5] = 145;
}

extern "C" __attribute__((noinline, used)) void negative_wrong_upper_clamp(
    volatile int16_t* fields) {
    const int16_t value = fields[3];
    if (value > 144) fields[3] = 144;
}

extern "C" __attribute__((noinline, used)) void negative_omit_lower_clamp(
    volatile int16_t* fields) {
    const int16_t value = fields[0];
    if (value < 40) fields[0] = value;
}
