#include <cstdint>
typedef uint32_t u32;

extern "C" void* h17_aoc_resultcopyvalue_candidate(void** target) {
    void* ptr = *target;
    if (ptr != nullptr) {
        *target = *reinterpret_cast<void**>(ptr);
    }
    return ptr;
}

extern "C" void* h17_aoc_resultcopyvalue_mutation(void** target) {
    *target = nullptr;
    return nullptr;
}
