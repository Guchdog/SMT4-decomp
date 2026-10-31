#include <cstdint>
typedef uint8_t u8;

struct alignas(4) MapFieldState {
    u8 pad[0x2F8];
    u8 active_flag;
};

extern "C" {
    extern MapFieldState g_MapFieldState_0049f91c;
}

extern "C" void h13_mapfield_clearactiveflag_candidate() {
    g_MapFieldState_0049f91c.active_flag = 0;
}

extern "C" void h13_mapfield_clearactiveflag_mutation() {
    g_MapFieldState_0049f91c.active_flag = 1;
}
