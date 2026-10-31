#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct AsdTextCode14 {
    u8 pad[0x14];
    u32 code14;
};

extern "C" {
    extern AsdTextCode14 g_AsdTextCode_00464d48;
}

extern "C" void h14_asdtext_setcodefield14_candidate(u32 val) {
    g_AsdTextCode_00464d48.code14 = val;
}

extern "C" void h14_asdtext_setcodefield14_mutation(u32 val) {
    g_AsdTextCode_00464d48.code14 = val ^ 1;
}
