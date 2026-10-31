#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct alignas(4) SmirkSubWork {
    u8 pad[0x10];
    u32 slots[7];
};

struct alignas(4) BattleSmirkWork {
    u8 pad[0xC];
    void* actor;
    u8 pad2[0xC];
    SmirkSubWork* sub;
};

extern "C" {
    extern BattleSmirkWork g_BattleSmirkWork_00471a70;
    void sub_2C3AA8(void*);
    void sub_2C3A24(void*);
}

extern "C" u32 h12_battle_exchangesmirkslot_candidate(u32 val, u32 slot) {
    if (slot >= 7) return 0;
    SmirkSubWork* sub = g_BattleSmirkWork_00471a70.sub;
    sub_2C3AA8(sub);
    u32 old_val = sub->slots[slot];
    sub->slots[slot] = val;
    sub_2C3A24(sub);
    return old_val;
}

extern "C" u32 h12_battle_exchangesmirkslot_mutation(u32 val, u32 slot) {
    return 0xDEADBEEF;
}
