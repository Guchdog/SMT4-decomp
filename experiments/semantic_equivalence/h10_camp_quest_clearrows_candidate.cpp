#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    void UiAnimSprite_SetMode_002bdac0(void* sprite, u32 mode, u32 param);
    extern void* g_QuestManagerWork_0043da90;
}

extern "C" void h10_camp_quest_clearrows_candidate() {
    u8* mgr = static_cast<u8*>(g_QuestManagerWork_0043da90);
    if (!mgr) return;

    UiAnimSprite_SetMode_002bdac0(mgr + 0x648, 3, 0);

    for (u32 i = 0; i < 8; ++i) {
        UiAnimSprite_SetMode_002bdac0(mgr + 0x904 + (i * 0x8C), 3, 0);
    }

    UiAnimSprite_SetMode_002bdac0(mgr + 0x878, 3, 0);
}

extern "C" void h10_camp_quest_clearrows_mutation() {
    g_QuestManagerWork_0043da90 = reinterpret_cast<void*>(0xDEADBEEF);
}
