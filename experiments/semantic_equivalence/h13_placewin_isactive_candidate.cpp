#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct PlaceWinTimer {
    u8 pad[0x38];
    float duration;
    u8 pad2[0xC];
    float elapsed;
};

struct PlaceWinHolder {
    u8 pad[4];
    PlaceWinTimer* timer;
};

extern "C" u32 h13_placewin_isactive_candidate(PlaceWinHolder* holder) {
    PlaceWinTimer* t = holder->timer;
    if (!t) return 1;
    return (t->elapsed > t->duration) ? 0 : 1;
}

extern "C" u32 h13_placewin_isactive_mutation(PlaceWinHolder* holder) {
    return 0;
}
