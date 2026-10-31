#include <cstdint>

extern "C" void AsdMem_Free(void* ptr);

extern "C" void h17_aoc_releaseglobal_candidate(void* ptr) {
    if (ptr != nullptr) {
        AsdMem_Free(ptr);
    }
}

extern "C" void h17_aoc_releaseglobal_mutation(void* ptr) {
}
