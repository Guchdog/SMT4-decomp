#include <cstdint>

extern "C" void aoc_sub_00253f64(void* self);
extern "C" void aoc_sub_00253f24(void* self);

extern "C" void h17_aoc_resetstate_candidate(void* self) {
    aoc_sub_00253f64(self);
    aoc_sub_00253f24(self);
}

extern "C" void h17_aoc_resetstate_mutation(void* self) {
    aoc_sub_00253f64(self);
}
