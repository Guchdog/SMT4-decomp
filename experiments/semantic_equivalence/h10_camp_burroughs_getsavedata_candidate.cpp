#include <cstdint>
struct GameWork {
    void* field_0;
    uint8_t* save_data;
};
extern "C" {
    extern GameWork g_GameWork_0043e2a8;
}

extern "C" void* h10_camp_burroughs_getsavedata_candidate() {
    return g_GameWork_0043e2a8.save_data + 0x1ec18;
}

extern "C" void h10_camp_burroughs_getsavedata_mutation() {
    g_GameWork_0043e2a8.save_data = reinterpret_cast<uint8_t*>(0xDEADBEEF);
}
