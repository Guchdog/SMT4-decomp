#include <cstdint>
typedef uint32_t u32;

extern "C" {
    u32 sub_2C3290();
    u32 sub_20FDE0(u32);
}

extern "C" u32 h13_mapepl_calcscale_candidate() {
    u32 a = sub_2C3290();
    u32 b = sub_20FDE0(0);
    return a * b;
}

extern "C" u32 h13_mapepl_calcscale_mutation() {
    u32 a = sub_2C3290();
    u32 b = sub_20FDE0(0);
    return a + b;
}
