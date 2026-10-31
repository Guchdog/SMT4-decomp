#include <cstdint>
typedef int32_t s32;
typedef int8_t s8;
typedef uint8_t u8;

struct alignas(4) SmirkWork {
    u8 pad[0x1C];
    u8* sub;
};

extern "C" {
    extern SmirkWork g_BattleSmirkWork_00471a70;
}

extern "C" s32 h12_battle_getunitsmirkstate_promoted() {
    return *reinterpret_cast<s8*>(g_BattleSmirkWork_00471a70.sub + 0x75);
}

extern "C" s32 h12_battle_getunitsmirkstate_mutation() {
    return 0xDEADBEEF;
}
