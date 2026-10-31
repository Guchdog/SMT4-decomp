#include <cstdint>

typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    void StatusDown_SetDisplayMode_00292f44(u32 mode);

    extern u32 g_StatusContext_0044e140[];
}

extern "C" void h8_ui_status_affinity_candidate() {
    u32* ctx = g_StatusContext_0044e140;
    u32 r4_val = ctx[1];
    if (!r4_val) return;
    u8* r4 = reinterpret_cast<u8*>(r4_val);

    *reinterpret_cast<u32*>(r4 + 0x14) = 0;
    r4[0x1E63] = 1;
    u8 r0 = r4[0x1E63 + 3];

    u32* r5 = reinterpret_cast<u32*>(r4_val + 0x1000);
    u32 state_2e4 = r5[0x2E4 / 4];

    if (r0 == 0) {
        if (state_2e4 == 0) StatusDown_SetDisplayMode_00292f44(0);
        else if (state_2e4 == 1) StatusDown_SetDisplayMode_00292f44(1);
        else if (r4[0x1E63] == 0 && state_2e4 == 2) StatusDown_SetDisplayMode_00292f44(2);
    } else if (r0 == 6) {
        if (state_2e4 == 0) StatusDown_SetDisplayMode_00292f44(0);
        else if (state_2e4 == 1) StatusDown_SetDisplayMode_00292f44(1);
        else if (state_2e4 == 2) StatusDown_SetDisplayMode_00292f44(5);
    } else if (r0 == 8 || r0 == 9 || r0 == 10 || r0 == 11 || r0 == 7) {
        if (state_2e4 == 0) StatusDown_SetDisplayMode_00292f44(1);
        else if (state_2e4 == 1) StatusDown_SetDisplayMode_00292f44(4);
        else if (state_2e4 == 2) StatusDown_SetDisplayMode_00292f44(5);
    } else if (r0 == 14) {
        if (state_2e4 == 0) StatusDown_SetDisplayMode_00292f44(0);
    } else if (r0 == 13) {
        if (state_2e4 == 0) StatusDown_SetDisplayMode_00292f44(0);
        else if (state_2e4 == 1) StatusDown_SetDisplayMode_00292f44(1);
        else if (r4[0x1E63] == 0) {
            if (state_2e4 == 2) StatusDown_SetDisplayMode_00292f44(4);
            else if (state_2e4 == 3) StatusDown_SetDisplayMode_00292f44(5);
        }
    } else {
        if (r4[0x12F1] == 6) {
            if (state_2e4 == 0) StatusDown_SetDisplayMode_00292f44(1);
        } else {
            if (state_2e4 == 0) StatusDown_SetDisplayMode_00292f44(0);
            else if (state_2e4 == 1) StatusDown_SetDisplayMode_00292f44(1);
            if (r4[0x1E63] == 0) {
                if (state_2e4 == 2) StatusDown_SetDisplayMode_00292f44(4);
                else if (state_2e4 == 3) StatusDown_SetDisplayMode_00292f44(5);
            }
        }
    }
}

extern "C" void h8_ui_status_affinity_mutation() {
    StatusDown_SetDisplayMode_00292f44(0xDEADBEEF);
}
