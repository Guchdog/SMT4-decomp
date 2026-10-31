#include <cstdint>
typedef uint32_t u32;

extern "C" {
    void* sub_2C0AC8();
}

extern "C" u32 h15_uitext_getdrawcoordx_candidate() {
    u32* p = (u32*)sub_2C0AC8();
    return p[0x38 / 4];
}

extern "C" u32 h15_uitext_getdrawcoordx_mutation() {
    u32* p = (u32*)sub_2C0AC8();
    return p[0x38 / 4] + 1;
}
