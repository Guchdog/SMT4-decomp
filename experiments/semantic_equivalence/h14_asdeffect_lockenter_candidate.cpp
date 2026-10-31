#include <cstdint>
typedef uint16_t u16;
typedef uint8_t u8;

struct AsdEffectInner {
    u8 pad[0x38];
    u16 effect_id;
};

struct AsdEffectLockWork {
    u16 saved_id;
    u16 depth;
    u8 pad[4];
    AsdEffectInner* inner;
};

extern "C" {
    extern AsdEffectLockWork g_AsdEffectLockWork_00465120;
}

extern "C" void h14_asdeffect_lockenter_candidate(u16 id) {
    AsdEffectLockWork* lock = &g_AsdEffectLockWork_00465120;
    AsdEffectInner* inner = lock->inner;
    u16 d = lock->depth;
    if (d == 0) {
        lock->saved_id = inner->effect_id;
    }
    lock->depth = d + 1;
    inner->effect_id = id;
}

extern "C" void h14_asdeffect_lockenter_mutation(u16 id) {
    AsdEffectLockWork* lock = &g_AsdEffectLockWork_00465120;
    lock->depth++;
}
