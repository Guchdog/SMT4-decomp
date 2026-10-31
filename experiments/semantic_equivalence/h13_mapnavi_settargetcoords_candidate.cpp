#include <cstdint>
typedef uint16_t u16;
typedef uint8_t u8;

struct MapNaviTarget {
    u8 pad[4];
    u16 target_x;
    u16 target_y;
    u16 angle;
    u8 active;
};

extern "C" {
    extern MapNaviTarget* g_MapNaviTarget_004474d8;
}

extern "C" void h13_mapnavi_settargetcoords_candidate(u16 x, u16 y) {
    MapNaviTarget* navi = g_MapNaviTarget_004474d8;
    navi->angle = 0;
    navi->target_x = x;
    navi->target_y = y;
    navi->active = 1;
}

extern "C" void h13_mapnavi_settargetcoords_mutation(u16 x, u16 y) {
    MapNaviTarget* navi = g_MapNaviTarget_004474d8;
    navi->target_x = 0;
    navi->target_y = 0;
    navi->active = 0;
}
