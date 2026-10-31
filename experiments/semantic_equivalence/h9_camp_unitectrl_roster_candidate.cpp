#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" {
    void* ui_Tbb_GetGlobalSubTable_001b9a90(u32 a, u32 b);
    u32   ui_Tbb_GetRowCount_001b9aa4(void* tbl);
    void* Battle_GetTalkEntry_00215fa8(u16 id);
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  qsort_002b7f0a(void* base, u32 num, u32 size, void* cmp);

    extern void* g_UniteCtrlRoster_0043dd40;
}

struct UniteBibleRow {
    u16 id;
    u8 race;
    u8 field_03;
    u16 flags;
};

struct UniteCtrlEntry {
    u16 demon_id;
    u8 field_02;
    u8 pad;
};

struct UniteCtrlRoster {
    u8 counts[0x38];
    UniteCtrlEntry* buckets[0x38];
    u16 field_118;
    u16 field_11a;
    u16 field_11c;
    u16 field_11e;
    u8  field_120;
    u8  field_121;
    u8  field_122[4];
    u8  field_126[4];
    u8  field_12a[4];
    u8  field_12e[4];
    u8  field_132;
    u8  pad_133;
    u16 field_134;
    u8  field_136;
    u8  pad_137;
    u16 field_138;
    u16 field_13a;
    u8  pad_13c[6];
    u8  field_142;
    u8  field_143;
    u8  pad_144[0x38];
    u8  field_17c;
};

extern "C" void h9_camp_unitectrl_roster_candidate(UniteCtrlRoster* roster) {
    void* tbl = ui_Tbb_GetGlobalSubTable_001b9a90(0, 0);
    u32 row_count = ui_Tbb_GetRowCount_001b9aa4(tbl);

    u8 local_counts[0x38];
    for (u32 i = 0; i < 0x38; ++i) {
        local_counts[i] = 0;
        roster->counts[i] = 0;
        roster->buckets[i] = nullptr;
    }

    for (u32 i = 0; i < row_count; ++i) {
        UniteBibleRow* row = static_cast<UniteBibleRow*>(Battle_GetTalkEntry_00215fa8(static_cast<u16>(i)));
        if (!row) continue;
        u32 race = row->race;
        if (race < 0x38 && (row->flags & 1)) {
            roster->counts[race]++;
        }
    }

    for (u32 i = 0; i < 0x38; ++i) {
        u8 count = roster->counts[i];
        if (count > 0) {
            roster->buckets[i] = static_cast<UniteCtrlEntry*>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, count * sizeof(UniteCtrlEntry), 1));
        }
    }

    for (u32 i = 0; i < row_count; ++i) {
        UniteBibleRow* row = static_cast<UniteBibleRow*>(Battle_GetTalkEntry_00215fa8(static_cast<u16>(i)));
        if (!row) continue;
        u32 race = row->race;
        if (race < 0x38 && (row->flags & 1)) {
            u8 idx = local_counts[race]++;
            UniteCtrlEntry* ent = roster->buckets[race];
            if (ent) {
                ent[idx].demon_id = row->id;
                ent[idx].field_02 = row->field_03;
            }
        }
    }

    for (u32 i = 0; i < 0x38; ++i) {
        if (roster->buckets[i]) {
            qsort_002b7f0a(roster->buckets[i], roster->counts[i], sizeof(UniteCtrlEntry), reinterpret_cast<void*>(0x00219600));
        }
    }

    roster->field_11c = 0;
    roster->field_11e = 0;
    roster->field_118 = 0;
    roster->field_11a = 0;
    roster->field_143 = 0;
    roster->field_120 = 0;
    roster->field_121 = 0;
    for (u32 i = 0; i < 4; ++i) roster->field_122[i] = 0;
    for (u32 i = 0; i < 4; ++i) roster->field_126[i] = 0;
    for (u32 i = 0; i < 4; ++i) roster->field_12a[i] = 0;
    for (u32 i = 0; i < 4; ++i) roster->field_12e[i] = 0;
    roster->field_132 = 0;
    roster->field_134 = static_cast<u16>(roster->field_134 & 0x03FF);
    roster->field_136 = 0;
    roster->field_138 = 0xFFFF;
    roster->field_13a = 0xFFFF;
    roster->field_17c = 0;
}

extern "C" void h9_camp_unitectrl_roster_mutation(UniteCtrlRoster* roster) {
    roster->counts[0] = 0xFF;
}
