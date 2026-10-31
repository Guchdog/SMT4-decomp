#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct AsdTextCode {
    u8 pad[0x1C];
    u32 code1c;
};

extern "C" {
    extern AsdTextCode g_AsdTextCode_00464d48;
}

extern "C" void h14_asdtext_setcodefield1c_candidate(u32 val) {
    g_AsdTextCode_00464d48.code1c = val;
}

extern "C" void h14_asdtext_setcodefield1c_mutation(u32 val) {
    g_AsdTextCode_00464d48.code1c = val ^ 1;
}
