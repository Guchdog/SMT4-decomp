#include <stdint.h>

// AAPCS arguments are destination/source/raw slot-1 word in r0/r1/r2. The
// reference loads all source words before any destination write, so snapshot
// the lanes explicitly to preserve aligned overlap behavior.
extern "C" __attribute__((noinline, used)) void candidate_0023aff0(
    uint32_t* destination, const uint32_t* source, uint32_t slot1) {
    uint32_t x[16];
    for (unsigned i = 0; i != 16; ++i) x[i] = source[i];
    destination[0] = x[3]; destination[1] = slot1;
    destination[2] = x[2]; destination[3] = x[1]; destination[4] = x[0];
    destination[5] = x[7]; destination[6] = x[6]; destination[7] = x[5]; destination[8] = x[4];
    destination[9] = x[11]; destination[10] = x[10]; destination[11] = x[9]; destination[12] = x[8];
    destination[13] = x[15]; destination[14] = x[14]; destination[15] = x[13]; destination[16] = x[12];
}

extern "C" __attribute__((noinline, used)) void candidate_002a1b4c(
    uint32_t* destination, const uint32_t* source, uint32_t slot1) {
    uint32_t x[16];
    for (unsigned i = 0; i != 16; ++i) x[i] = source[i];
    destination[0] = x[3]; destination[1] = slot1;
    destination[2] = x[2]; destination[3] = x[1]; destination[4] = x[0];
    destination[5] = x[7]; destination[6] = x[6]; destination[7] = x[5]; destination[8] = x[4];
    destination[9] = x[11]; destination[10] = x[10]; destination[11] = x[9]; destination[12] = x[8];
    destination[13] = x[15]; destination[14] = x[14]; destination[15] = x[13]; destination[16] = x[12];
}

extern "C" __attribute__((noinline, used)) void wrong_transpose_0023aff0(
    uint32_t* destination, const uint32_t* source, uint32_t slot1) {
    uint32_t x[16];
    for (unsigned i = 0; i != 16; ++i) x[i] = source[i];
    destination[0] = x[0]; destination[1] = slot1;
    destination[2] = x[1]; destination[3] = x[2]; destination[4] = x[3];
    destination[5] = x[4]; destination[6] = x[5]; destination[7] = x[6]; destination[8] = x[7];
    destination[9] = x[8]; destination[10] = x[9]; destination[11] = x[10]; destination[12] = x[11];
    destination[13] = x[12]; destination[14] = x[13]; destination[15] = x[14]; destination[16] = x[15];
}

extern "C" __attribute__((noinline, used)) void wrong_slot_002a1b4c(
    uint32_t* destination, const uint32_t* source, uint32_t slot1) {
    uint32_t x[16];
    for (unsigned i = 0; i != 16; ++i) x[i] = source[i];
    destination[0] = x[3]; destination[1] = x[2]; destination[2] = slot1;
    destination[3] = x[1]; destination[4] = x[0];
    destination[5] = x[7]; destination[6] = x[6]; destination[7] = x[5]; destination[8] = x[4];
    destination[9] = x[11]; destination[10] = x[10]; destination[11] = x[9]; destination[12] = x[8];
    destination[13] = x[15]; destination[14] = x[14]; destination[15] = x[13]; destination[16] = x[12];
}
