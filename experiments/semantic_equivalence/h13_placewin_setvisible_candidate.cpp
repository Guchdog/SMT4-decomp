#include <cstdint>
typedef uint8_t u8;

struct PlaceWinWork {
    u8 pad[0x4C5];
    u8 visible;
};

extern "C" {
    extern PlaceWinWork* g_PlaceWinWork_0043da28[];
}

extern "C" void h13_placewin_setvisible_candidate(u8 visible) {
    PlaceWinWork* w = g_PlaceWinWork_0043da28[1];
    w->visible = visible;
}

extern "C" void h13_placewin_setvisible_mutation(u8 visible) {
    PlaceWinWork* w = g_PlaceWinWork_0043da28[1];
    w->visible = visible ^ 1;
}
