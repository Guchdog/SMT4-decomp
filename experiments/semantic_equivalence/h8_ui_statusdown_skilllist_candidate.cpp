#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;
typedef int16_t s16;

struct SkillEntry {
    u16 skill_id;
    u8 pad[4];
    u16 flags;
    u8 pad2[0x30];
    u16 cost;
};

typedef int (*CompareFn)(const void*, const void*);

extern "C" {
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    SkillEntry* SkillTable_Get_002b9364(u32 id);
    void  UiPage_Setup_0029fae8(void* page, s16 count, u32 rows, u32 cols, u32 f1, u32 f2);
    u8*   UiMenu_GetSortOptions_002a0fac(void* work);
    void  qsort_002b7f0a(void* base, u32 num, u32 size, CompareFn cmp);

    extern void* g_StatusDownContext_0044e190;
    extern int StatusDown_SkillSortByIdAsc(const void*, const void*);
    extern int StatusDown_SkillSortByIdDesc(const void*, const void*);
    extern int StatusDown_SkillSortByCostAsc(const void*, const void*);
    extern int StatusDown_SkillSortByCostDesc(const void*, const void*);
    extern int StatusDown_SkillSortByNameAsc(const void*, const void*);
    extern int StatusDown_SkillSortByNameDesc(const void*, const void*);
}

extern "C" void h8_ui_statusdown_skilllist_candidate(const u8* skill_bitfield) {
    u8* work = static_cast<u8*>(g_StatusDownContext_0044e190);
    if (!work) return;

    u8* header = work + 0xDC0;
    *reinterpret_cast<u16*>(header + 0x8) = 0;
    *reinterpret_cast<u16*>(header + 0xA) = 0;

    AsdMem_Zero_002c4b30(work + 0x5C8, 0x800);

    for (u32 i = 0; i < 0x500; ++i) {
        SkillEntry* entry = SkillTable_Get_002b9364(i);
        if (entry && (entry->flags & 1) && entry->cost != 0) {
            u16 sid = entry->cost; // cost/id index
            if (skill_bitfield[sid >> 3] & (1 << (sid & 7))) {
                s16 count = *reinterpret_cast<s16*>(header + 0x8);
                u8* slot = work + 0x5C8 + count * 4;
                *reinterpret_cast<u16*>(slot) = entry->skill_id;
                *reinterpret_cast<u16*>(slot + 2) = entry->cost;
                *reinterpret_cast<s16*>(header + 0x8) = count + 1;
            }
            *reinterpret_cast<u16*>(header + 0xA) += 1;
        }
    }

    s16 total = *reinterpret_cast<s16*>(header + 0x8);
    void* page = work + 0xDCC;
    UiPage_Setup_0029fae8(page, total, 11, 1, 0, 1);

    u8* opt = UiMenu_GetSortOptions_002a0fac(work);
    u8 mode_byte = opt[0x15];
    u32 crit = mode_byte & 0x7F;
    bool desc = (mode_byte >> 7) != 0;

    void* base = work + 0x5C8;
    s16 count = *reinterpret_cast<s16*>(work + 0xDC8);

    if (crit == 1) {
        CompareFn cmp = desc ? StatusDown_SkillSortByIdDesc : StatusDown_SkillSortByIdAsc;
        qsort_002b7f0a(base, count, 4, cmp);
    } else if (crit == 0x21) {
        CompareFn cmp = desc ? StatusDown_SkillSortByNameDesc : StatusDown_SkillSortByNameAsc;
        qsort_002b7f0a(base, count, 4, cmp);
    } else if (crit == 3) {
        CompareFn cmp = desc ? StatusDown_SkillSortByCostDesc : StatusDown_SkillSortByCostAsc;
        qsort_002b7f0a(base, count, 4, cmp);
    }

    work[0x410] = 1;
}

extern "C" void h8_ui_statusdown_skilllist_mutation(const u8* skill_bitfield) {
    u8* work = static_cast<u8*>(g_StatusDownContext_0044e190);
    if (work) work[0x410] = 0;
}
