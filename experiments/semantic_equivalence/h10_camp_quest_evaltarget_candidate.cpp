#include <cstdint>
typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" u32 h10_camp_quest_evaltarget_candidate(const u8* entry, const u8* cond) {
    u32 f38 = *reinterpret_cast<const u32*>(entry + 0x38);
    u32 type = (f38 >> 16) & 0xF;
    if (type != 5 && type != 6) return 0;

    u8 cond_type = cond[0x23];
    if (cond_type == 0 || cond_type == 1) {
        u32 c28 = *reinterpret_cast<const u32*>(cond + 0x28);
        u32 target_val = (c28 >> 12) & 0x1F;
        u32 entry_val = (f38 >> 11) & 0x1F;
        return target_val == entry_val;
    }

    if (cond_type == 3) {
        if ((f38 & 0xF800) != 0xA000) return 0;
        u16 c36 = *reinterpret_cast<const u16*>(cond + 0x36);
        u32 shifted = (static_cast<u32>(c36) << 20);
        if (shifted == 0) {
            return cond[0x43] != 0;
        }
        return shifted != 0xFA000000;
    }

    return 0;
}

extern "C" u32 h10_camp_quest_evaltarget_mutation(const u8* entry, const u8* cond) {
    return 0xDEADBEEF;
}
