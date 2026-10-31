#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct UiTextCode10 {
    u8 pad[0x10];
    u32 code10;
};

extern "C" {
    extern UiTextCode10 g_UiTextCode_00464d48;
}

extern "C" void h15_uitext_setcodefield10_candidate(u32 val) {
    g_UiTextCode_00464d48.code10 = val;
}

extern "C" void h15_uitext_setcodefield10_mutation(u32 val) {
    g_UiTextCode_00464d48.code10 = val ^ 1;
}
