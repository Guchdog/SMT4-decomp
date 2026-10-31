#include <cstdint>
typedef uint32_t u32;

extern "C" void h17_aoc_resultcopyvalue_candidate(u32** target) {
    u32* ptr = *target;
    if (ptr != nullptr) {
        *reinterpret_cast<u32*>(target) = *ptr;
    }
}

extern "C" void h17_aoc_resultcopyvalue_mutation(u32** target) {
    *target = nullptr;
}
