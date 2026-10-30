#include <cstdint>

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int32_t s32;

struct BtlUnitWork {
    void* parent_work;                  // +0x00
    u8 pad_04[0x30];                    // +0x04..+0x34
    void* unit_task;                    // +0x34: Task handle ("btlUnit Calc", tag 0x2)
    u8 pad_38[0x96];                    // +0x38..+0xCE
    u16 sub_party_id;                   // +0xCE
    u8 pad_D0[0x1A8];                   // +0xD0..+0x278
    u16* party_slots;                   // +0x278: Active party slots
    u16* reserve_slots;                 // +0x27C: Reserve slots
    u8 pad_280[4];                      // +0x280..+0x284
    void* guest_unit;                   // +0x284: Guest unit pointer
};

extern "C" {
    void* Unit_Lookup_002ae3f0(u16 unit_id);
    void* SubParty_Lookup_002b9364(u16 sub_party_id);
}

extern "C" s32 h5_btl_unit_check_party_active_candidate(BtlUnitWork* work) {
    if (!work) return 0;

    const char* groups[3];
    groups[0] = (const char*)work->party_slots;
    groups[1] = (const char*)work->reserve_slots;
    groups[2] = nullptr;

    if (work->guest_unit != nullptr) {
        groups[2] = (const char*)SubParty_Lookup_002b9364(work->sub_party_id);
    }

    #pragma clang loop unroll(disable)
    for (int g = 0; g < 3; ++g) {
        const char* grp = groups[g];
        if (grp == nullptr) continue;
        int off = (g == 2) ? 0x3C : 0x34;
        #pragma clang loop unroll(disable)
        for (int i = 0; i < 8; ++i) {
            u16 id = *(const u16*)(grp + off + i * 2);
            void* unit = Unit_Lookup_002ae3f0(id);
            if (unit != nullptr && *(const u8*)((const char*)unit + 0x23) == 3) {
                return 1;
            }
        }
    }

    return 0;
}

extern "C" s32 h5_btl_unit_check_party_active_mutation(BtlUnitWork* work) {
    if (!work) return 0;
    return 0;
}
