#include <cstdint>
typedef uint8_t u8;
typedef uint32_t u32;

extern "C" u32 h17_aoc_resultisready_candidate(const u8* path_obj) {
    return (*path_obj >= 0x64) ? 1 : 0;
}

extern "C" u32 h17_aoc_resultisready_mutation(const u8* path_obj) {
    return (*path_obj < 0x64) ? 1 : 0;
}
