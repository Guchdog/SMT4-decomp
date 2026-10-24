#include <stdint.h>

using u32 = uint32_t;

#define DEFINE_ZERO_PAIR(name)                                      \
    extern "C" __attribute__((noinline, used)) volatile u32* name(  \
        volatile u32* destination) {                                  \
        destination[0] = 0;                                          \
        destination[1] = 0;                                          \
        return destination;                                          \
    }

DEFINE_ZERO_PAIR(candidate_0011b850)
DEFINE_ZERO_PAIR(candidate_0017f5e8)
DEFINE_ZERO_PAIR(candidate_0017f5f8)

extern "C" __attribute__((noinline, used)) volatile u32* negative_second_offset(
    volatile u32* destination) {
    destination[0] = 0;
    destination[2] = 0;
    return destination;
}

extern "C" __attribute__((noinline, used)) volatile u32* negative_missing_store(
    volatile u32* destination) {
    destination[0] = 0;
    return destination;
}

extern "C" __attribute__((noinline, used)) volatile u32* negative_wrong_return(
    volatile u32* destination) {
    destination[0] = 0;
    destination[1] = 0;
    return destination + 1;
}
