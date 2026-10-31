#include <cstdint>
typedef uint8_t u8;

struct GameWork {
    void* field_0;
    u8* save_data;
};

extern "C" {
    extern GameWork g_GameWork_0043e2a8;
}

extern "C" void* h10_camp_burroughs_getsavedata_promoted() {
    return g_GameWork_0043e2a8.save_data + 0x1ec18;
}

extern "C" void h10_camp_burroughs_getsavedata_mutation() {
    g_GameWork_0043e2a8.save_data = reinterpret_cast<u8*>(0xDEADBEEF);
}
