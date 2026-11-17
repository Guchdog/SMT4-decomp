#include <cstdint>

extern "C" __attribute__((target("thumb"), noinline))
std::uint32_t candidate_002b5c2c(const std::uint16_t* input) {
    std::uint32_t count = 0;
    while (*input != 0) {
        ++count;
        ++input;
    }
    __asm__ volatile("cmp %0, #0" : : "r"(count) : "cc");
    return count;
}
