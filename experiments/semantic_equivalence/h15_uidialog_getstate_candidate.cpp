#include <cstdint>
typedef int8_t s8;

extern "C" {
    void* sub_2C0AC8();
}

extern "C" s8 h15_uidialog_getstate_candidate() {
    s8* p = (s8*)sub_2C0AC8();
    return p[0x8C];
}

extern "C" s8 h15_uidialog_getstate_mutation() {
    s8* p = (s8*)sub_2C0AC8();
    return (s8)(p[0x8C] ^ 1);
}
