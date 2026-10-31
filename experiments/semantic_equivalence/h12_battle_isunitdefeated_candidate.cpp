#include <cstdint>
typedef uint32_t u32;
typedef int32_t s32;
typedef uint8_t u8;

extern "C" u32 h12_battle_isunitdefeated_candidate(const void* unit) {
    const u8* u = static_cast<const u8*>(unit);
    u32 flags = *reinterpret_cast<const u32*>(u + 0x44A0);
    if (flags & 2) return 0;
    if (flags & 0x02000000) return 1;
    s32 hp = *reinterpret_cast<const s32*>(u + 0xC4);
    return (hp < 0) ? 1 : 0;
}

extern "C" u32 h12_battle_isunitdefeated_mutation(const void* unit) {
    return 0;
}
