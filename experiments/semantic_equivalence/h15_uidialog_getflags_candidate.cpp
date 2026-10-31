#include <cstdint>
typedef uint32_t u32;

extern "C" {
    void* sub_2C0AC8();
}

extern "C" u32 h15_uidialog_getflags_candidate() {
    u32* p = (u32*)sub_2C0AC8();
    return *p;
}

extern "C" u32 h15_uidialog_getflags_mutation() {
    u32* p = (u32*)sub_2C0AC8();
    return *p ^ 1;
}
