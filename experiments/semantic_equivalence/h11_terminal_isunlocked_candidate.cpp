#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" void* sub_2BBD40();

extern "C" u32 h11_terminal_isunlocked_candidate(u32 terminal_id) {
    if (terminal_id >= 32) return 0;
    u8* work = static_cast<u8*>(sub_2BBD40());
    u8* bitset = work + 8;
    u32 byte_idx = terminal_id >> 3;
    u8 mask = static_cast<u8>(1u << (terminal_id & 7));
    return (bitset[byte_idx] & mask) ? 1 : 0;
}

extern "C" u32 h11_terminal_isunlocked_mutation(u32 terminal_id) {
    return 0xDEADBEEF;
}
