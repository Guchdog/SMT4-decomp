#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct AsdTextCode30 {
    u8 pad[0x30];
    u32 code30;
};

extern "C" {
    extern AsdTextCode30 g_AsdTextCode_00464d48;
}

extern "C" void h14_asdtext_setcodefield30_candidate(u32 val) {
    g_AsdTextCode_00464d48.code30 = val;
}

extern "C" void h14_asdtext_setcodefield30_mutation(u32 val) {
    g_AsdTextCode_00464d48.code30 = val ^ 1;
}
