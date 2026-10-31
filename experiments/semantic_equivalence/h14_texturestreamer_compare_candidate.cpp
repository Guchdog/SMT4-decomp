#include <cstdint>
typedef uint16_t u16;

extern "C" int h14_texturestreamer_compare_candidate(const u16* a, const u16* b) {
    return (int)*a - (int)*b;
}

extern "C" int h14_texturestreamer_compare_mutation(const u16* a, const u16* b) {
    return (int)*b - (int)*a;
}
