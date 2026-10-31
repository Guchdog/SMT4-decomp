#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct UiTextCode28 {
    u8 pad[0x28];
    u32 code28;
};

extern "C" {
    extern UiTextCode28 g_UiTextCode_00464d48;
}

extern "C" void h15_uitext_setcodefield28_candidate(u32 val) {
    g_UiTextCode_00464d48.code28 = val;
}

extern "C" void h15_uitext_setcodefield28_mutation(u32 val) {
    g_UiTextCode_00464d48.code28 = val ^ 1;
}
