#include <stdint.h>

// Bit-preserving 4x4 word transpose. The original reads every source lane
// before writing, so this snapshot also preserves aligned overlap behavior.
extern "C" __attribute__((noinline, used)) void candidate_002b7aa8(
    uint32_t* destination, const uint32_t* source) {
    uint32_t lanes[16];
    for (unsigned row = 0; row != 4; ++row)
        for (unsigned column = 0; column != 4; ++column)
            lanes[row * 4 + column] = source[column * 4 + row];
    for (unsigned i = 0; i != 16; ++i)
        destination[i] = lanes[i];
}

extern "C" __attribute__((noinline, used)) void wrong_ui_transpose_002b7aa8(
    uint32_t* destination, const uint32_t* source) {
    for (unsigned i = 0; i != 16; ++i)
        destination[i] = source[i];
}
