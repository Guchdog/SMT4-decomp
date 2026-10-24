#include <stdint.h>

extern "C" __attribute__((noinline, used)) void candidate_0023e634(
    volatile uint16_t* flags) {
    uint16_t value = flags[0];
    if (value & 0x0040) { value = static_cast<uint16_t>(value & ~0x0040); flags[0] = value; }
    if (value & 0x0080) { value = static_cast<uint16_t>(value & ~0x0080); flags[0] = value; }
    if (value & 0x0100) { value = static_cast<uint16_t>(value & ~0x0100); flags[0] = value; }
    if (value & 0x0010) { value = static_cast<uint16_t>(value & ~0x0010); flags[0] = value; }
    if (value & 0x0008) { value = static_cast<uint16_t>(value & ~0x0008); flags[0] = value; }
}

extern "C" __attribute__((noinline, used)) void negative_wrong_flag_mask(
    volatile uint16_t* flags) {
    uint16_t value = flags[0];
    if (value & 0x0020) { value = static_cast<uint16_t>(value & ~0x0020); flags[0] = value; }
}

extern "C" __attribute__((noinline, used)) void negative_unconditional_flag_store(
    volatile uint16_t* flags) {
    const uint16_t value = flags[0];
    flags[0] = value;
}

extern "C" __attribute__((noinline, used)) void candidate_00286700(
    volatile uint32_t* destination, volatile const uint32_t* source) {
    destination[1] = 0;
    destination[0] = 0x3F800000;
    destination[2] = 0;
    destination[3] = source[0];
    destination[4] = 0;
    destination[5] = 0x3F800000;
    destination[6] = 0;
    destination[8] = 0;
    destination[7] = source[1];
    destination[9] = 0;
    destination[10] = 0x3F800000;
    destination[11] = source[2];
    destination[12] = 0;
    destination[13] = 0;
    destination[14] = 0;
    destination[15] = 0x3F800000;
}

extern "C" __attribute__((noinline, used)) void negative_wrong_struct_source(
    volatile uint32_t* destination, volatile const uint32_t* source) {
    destination[3] = source[1];
}

extern "C" __attribute__((noinline, used)) void negative_omit_struct_source(
    volatile uint32_t* destination, volatile const uint32_t* source) {
    destination[3] = source[0];
}

extern "C" __attribute__((noinline, used)) void candidate_002b540c(
    volatile uint32_t* output, uint32_t mask) {
    if ((mask & 0x001) != 0) output[0] = 0xFFFFFFFF;
    if ((mask & 0x002) != 0) output[1] = 0xFFFFFFFF;
    if ((mask & 0x004) != 0) output[2] = 0xFFFFFFFF;
    if ((mask & 0x008) != 0) output[3] = 0xFFFFFFFF;
    if ((mask & 0x010) != 0) output[4] = 0xFFFFFFFF;
    if ((mask & 0x020) != 0) output[5] = 0xFFFFFFFF;
    if ((mask & 0x080) != 0) output[6] = 0xFFFFFFFF;
    if ((mask & 0x100) != 0) output[7] = 0xFFFFFFFF;
    if ((mask & 0x200) != 0) output[8] = 0xFFFFFFFF;
    if ((mask & 0x800) != 0) output[9] = 0xFFFFFFFF;
    if ((mask & 0x400) != 0) output[10] = 0xFFFFFFFF;
}

extern "C" __attribute__((noinline, used)) void negative_wrong_mask_slot(
    volatile uint32_t* output, uint32_t mask) {
    if ((mask & 0x002) != 0) output[0] = 0xFFFFFFFF;
    if ((mask & 0x002) != 0) output[1] = 0xFFFFFFFF;
    if ((mask & 0x004) != 0) output[2] = 0xFFFFFFFF;
    if ((mask & 0x008) != 0) output[3] = 0xFFFFFFFF;
    if ((mask & 0x010) != 0) output[4] = 0xFFFFFFFF;
    if ((mask & 0x020) != 0) output[5] = 0xFFFFFFFF;
    if ((mask & 0x080) != 0) output[6] = 0xFFFFFFFF;
    if ((mask & 0x100) != 0) output[7] = 0xFFFFFFFF;
    if ((mask & 0x200) != 0) output[8] = 0xFFFFFFFF;
    if ((mask & 0x800) != 0) output[9] = 0xFFFFFFFF;
    if ((mask & 0x400) != 0) output[10] = 0xFFFFFFFF;
}

extern "C" __attribute__((noinline, used)) void negative_omit_mask_slot(
    volatile uint32_t* output, uint32_t mask) {
    if ((mask & 0x001) != 0) output[0] = 0xFFFFFFFF;
    if ((mask & 0x002) != 0) output[1] = 0xFFFFFFFF;
    if ((mask & 0x004) != 0) output[2] = 0xFFFFFFFF;
    if ((mask & 0x008) != 0) output[3] = 0xFFFFFFFF;
    if ((mask & 0x010) != 0) output[4] = 0xFFFFFFFF;
    if ((mask & 0x020) != 0) output[5] = 0xFFFFFFFF;
    if ((mask & 0x080) != 0) output[6] = 0xFFFFFFFF;
    if ((mask & 0x100) != 0) output[7] = 0xFFFFFFFF;
    if ((mask & 0x200) != 0) output[8] = 0xFFFFFFFF;
    if ((mask & 0x800) != 0) output[9] = 0xFFFFFFFF;
}
