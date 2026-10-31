#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct PlaceWinContext {
    u8 pad[8];
    u32 state;
    u8 pad2[0x28];
    u8 sub[4];
};

extern "C" {
    extern PlaceWinContext* g_PlaceWinContext_0043e140;
    void sub_2BF030(void* sub, u32 flag);
}

extern "C" void h13_placewin_dismiss_candidate() {
    PlaceWinContext* ctx = g_PlaceWinContext_0043e140;
    ctx->state = 3;
    sub_2BF030(ctx->sub, 1);
}

extern "C" void h13_placewin_dismiss_mutation() {
    PlaceWinContext* ctx = g_PlaceWinContext_0043e140;
    ctx->state = 0;
    sub_2BF030(ctx->sub, 0);
}
