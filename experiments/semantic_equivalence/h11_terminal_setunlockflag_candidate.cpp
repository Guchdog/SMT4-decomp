#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" void* sub_2BBD40();

extern "C" void h11_terminal_setunlockflag_candidate(u32 terminal_id, u32 state) {
    if (terminal_id >= 32) return;
    u8* work = static_cast<u8*>(sub_2BBD40());
    u8* bitset = work + 8;
    u32 byte_idx = terminal_id >> 3;
    u8 mask = static_cast<u8>(1u << (terminal_id & 7));
    if (state != 0) {
        bitset[byte_idx] |= mask;
    } else {
        bitset[byte_idx] &= ~mask;
    }
}

extern "C" void h11_terminal_setunlockflag_mutation(u32 terminal_id, u32 state) {
    u8* work = static_cast<u8*>(sub_2BBD40());
    if (work) work[0] = 0xFF;
}
