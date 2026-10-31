#include <cstdint>
typedef uint32_t u32;

extern "C" {
    float sub_266D70(u32 arg);
    void sub_2E05BC(float dist);
}

extern "C" u32 h13_mapcalc_distancetoentity_candidate() {
    float dist_sq = sub_266D70(0);
    float dist;
    asm("vsqrt.f32 %0, %1" : "=t"(dist) : "t"(dist_sq));
    sub_2E05BC(dist);
    return 1;
}

extern "C" u32 h13_mapcalc_distancetoentity_mutation() {
    return 0;
}
