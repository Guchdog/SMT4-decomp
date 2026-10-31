#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    u8* Quest_GetMainEntry_002ae3f0(u32 id);
    u8* Quest_GetSubTable_002aa224(void*);
    u8* engine_func_002c0ec4(u32, u32);
    u8* engine_func_002c0e9c();
    u8* engine_func_002c0e4c(u8*);
    u8* Quest_FindEntry_002b48dc(void* params);
    extern void* g_QuestTableMgr_00433158;
}

extern "C" u32 h10_camp_quest_getavailability_candidate(u32 quest_id) {
    if (quest_id <= 0x190) {
        u8* entry = Quest_GetMainEntry_002ae3f0(quest_id);
        if (!entry) return 0;
        u32 f38 = *reinterpret_cast<u32*>(entry + 0x38);
        return (static_cast<int32_t>(f38) >= 0) ? 1 : 0;
    }

    u8* sub = Quest_GetSubTable_002aa224(g_QuestTableMgr_00433158);
    u8* entry = nullptr;
    if (sub) {
        entry = sub;
    } else {
        u8* p1 = engine_func_002c0ec4(4, 1);
        u8* p2 = engine_func_002c0e9c();
        u8* p3 = engine_func_002c0e4c(p1);
        u32 search_buf[16];
        search_buf[9] = quest_id;
        entry = Quest_FindEntry_002b48dc(search_buf);
    }

    if (!entry) return 0;
    u32 f38 = *reinterpret_cast<u32*>(entry + 0x38);
    return !(f38 & 0x40000000);
}

extern "C" u32 h10_camp_quest_getavailability_mutation(u32 quest_id) {
    return 0xDEADBEEF;
}
