#include <cstdint>
typedef uint8_t u8;

struct alignas(4) BattleSmirkWork {
    u8 pad[0xC];
    void* actor;
    u8 pad2[0xC];
    void* sub;
};

extern "C" {
    extern BattleSmirkWork g_BattleSmirkWork_00471a70;
}

extern "C" void* h12_battle_getsmirkactor_candidate() {
    return g_BattleSmirkWork_00471a70.actor;
}

extern "C" void* h12_battle_getsmirkactor_mutation() {
    return reinterpret_cast<void*>(0xDEADBEEF);
}
