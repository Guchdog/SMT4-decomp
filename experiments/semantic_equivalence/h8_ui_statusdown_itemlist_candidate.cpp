#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;
typedef int16_t s16;

struct ItemEntry {
    u16 item_id;
    u8 pad[4];
    u16 flags;
};

extern "C" {
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    ItemEntry* ItemTable_Get_002b9364(u32 id);
    void  UiPage_Setup_0029fae8(void* page, s16 count, u32 rows, u32 cols, u32 f1, u32 f2);
    void  UiPage_SetScroll_0029edfc(void* page, s16 scroll);
    void  UiPage_SetCursor_0029eb58(void* page, s16 cursor);
    void  StatusDown_SortItemList_0032c4bc();

    extern void* g_StatusDownContext_0044e190;
}

extern "C" void h8_ui_statusdown_itemlist_candidate(const u8* item_counts) {
    u8* work = static_cast<u8*>(g_StatusDownContext_0044e190);
    if (!work) return;

    u8* header = work + 0x2200;
    *reinterpret_cast<u16*>(header + 0x30) = 0;
    *reinterpret_cast<u16*>(header + 0x32) = 0;

    AsdMem_Zero_002c4b30(work + 0xE30, 0x1400);

    for (u32 i = 0; i < 0x500; ++i) {
        ItemEntry* entry = ItemTable_Get_002b9364(i);
        if (entry && (entry->flags & 1)) {
            u16 id = entry->item_id;
            u8 qty = item_counts[id];
            if (qty > 0) {
                s16 count = *reinterpret_cast<s16*>(header + 0x30);
                u8* slot = work + 0xE30 + count * 4;
                *reinterpret_cast<u16*>(slot) = id;
                *reinterpret_cast<u16*>(slot + 2) = qty;
                *reinterpret_cast<u16*>(header + 0x32) += 1;
                *reinterpret_cast<s16*>(header + 0x30) = count + 1;
            }
        }
    }

    s16 total_items = *reinterpret_cast<s16*>(header + 0x30);
    void* page = work + 0x223C;
    UiPage_Setup_0029fae8(page, total_items, 9, 4, 1, 1);

    if (total_items > 0) {
        s16 scroll = *reinterpret_cast<s16*>(header + 0x36);
        s16 cursor = *reinterpret_cast<s16*>(header + 0x34);
        if (total_items <= cursor + scroll * 4) {
            scroll = (total_items - 1) / 4;
            cursor = total_items - 1 - scroll * 4;
            *reinterpret_cast<s16*>(header + 0x36) = scroll;
            *reinterpret_cast<s16*>(header + 0x34) = cursor;
        }
        UiPage_SetScroll_0029edfc(page, scroll);
        UiPage_SetCursor_0029eb58(page, cursor);
    } else {
        UiPage_SetScroll_0029edfc(page, *reinterpret_cast<s16*>(header + 0x36));
        UiPage_SetCursor_0029eb58(page, *reinterpret_cast<s16*>(header + 0x34));
    }

    StatusDown_SortItemList_0032c4bc();
    work[0x410] = 1;
}

extern "C" void h8_ui_statusdown_itemlist_mutation(const u8* item_counts) {
    u8* work = static_cast<u8*>(g_StatusDownContext_0044e190);
    if (work) work[0x410] = 0;
}
