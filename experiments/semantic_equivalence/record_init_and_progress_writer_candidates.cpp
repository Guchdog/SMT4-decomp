#include <stdint.h>

extern "C" __attribute__((noinline, used)) void candidate_00296f18(
    volatile uint32_t* record, int32_t value, uint32_t type) {
    record[7] = type;
    record[0] = 0;
    record[1] = 0;
    record[2] = 0;
    record[3] = 0;
    record[8] = 0;
    record[4] = static_cast<uint32_t>(value);
    record[5] = 2;
    record[9] = 0;
    record[6] = static_cast<uint32_t>(value);
    if (value <= 0) record[6] = 0;
    else record[6] = static_cast<uint32_t>(value);
    record[0] = 6;
}

extern "C" __attribute__((noinline, used)) void negative_wrong_value_threshold(
    volatile uint32_t* record, int32_t value, uint32_t type) {
    record[7] = type;
    record[0] = 0;
    record[1] = 0;
    record[2] = 0;
    record[3] = 0;
    record[8] = 0;
    record[4] = static_cast<uint32_t>(value);
    record[5] = 2;
    record[9] = 0;
    record[6] = static_cast<uint32_t>(value);
    if (value <= 1) record[6] = 0;
    else record[6] = static_cast<uint32_t>(value);
    record[0] = 6;
}

extern "C" __attribute__((noinline, used)) void negative_omit_status_write(
    volatile uint32_t* record, int32_t value, uint32_t type) {
    record[7] = type;
    record[0] = 0;
    record[1] = 0;
    record[2] = 0;
    record[3] = 0;
    record[8] = 0;
    record[4] = static_cast<uint32_t>(value);
    record[5] = 2;
    record[9] = 0;
    record[6] = static_cast<uint32_t>(value);
    if (value <= 0) record[6] = 0;
    else record[6] = static_cast<uint32_t>(value);
}

static void write_progress(volatile uint32_t* destination,
                           volatile const uint32_t* source,
                           uint32_t initial_clear_mask,
                           bool omit_last_copy) {
    uint32_t state = destination[1];
    state = (state & ~initial_clear_mask) | 1;
    destination[1] = state;
    destination[2] = source[0];
    destination[1] = destination[1] | 2;
    destination[3] = source[1];
    destination[1] = destination[1] | 4;
    destination[4] = source[2];
    destination[1] = destination[1] | 8;
    if (!omit_last_copy) destination[5] = source[3];
}

extern "C" __attribute__((noinline, used)) void candidate_003e8b44(
    uint32_t, volatile uint32_t* destination,
    volatile const uint32_t* source) {
    write_progress(destination, source, 0xF, false);
}

extern "C" __attribute__((noinline, used)) void negative_wrong_state_clear_mask(
    uint32_t, volatile uint32_t* destination,
    volatile const uint32_t* source) {
    write_progress(destination, source, 0x1F, false);
}

extern "C" __attribute__((noinline, used)) void negative_omit_progress_copy(
    uint32_t, volatile uint32_t* destination,
    volatile const uint32_t* source) {
    write_progress(destination, source, 0xF, true);
}
