#include <cstdint>
typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" {
    void* sub_2B66EC(void* unit);
    u32 sub_2AE64C(u32 slot_id);
}

extern "C" u32 h11_shop_isequipslotmatch_candidate(void* unit, u32 slot_id) {
    u8* equip_table = static_cast<u8*>(sub_2B66EC(unit));
    u32 cat = sub_2AE64C(slot_id);
    u32 offset = 0;
    if (cat == 2) offset = 0;
    else if (cat == 3) offset = 2;
    else if (cat == 4) offset = 6;
    else if (cat == 5) offset = 8;
    else if (cat == 6) offset = 10;
    else if (cat == 7) offset = 12;
    else if (cat == 8) offset = 4;
    else return 0;
    u16 equipped_id = *reinterpret_cast<u16*>(equip_table + offset);
    return (slot_id == equipped_id) ? 1 : 0;
}

extern "C" u32 h11_shop_isequipslotmatch_mutation(void* unit, u32 slot_id) {
    return 0xDEADBEEF;
}
