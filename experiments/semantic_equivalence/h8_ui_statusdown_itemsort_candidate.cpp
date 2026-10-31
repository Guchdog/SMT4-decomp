#include <cstdint>

typedef uint32_t u32;
typedef uint8_t u8;
typedef int16_t s16;

typedef int (*CompareFn)(const void*, const void*);

extern "C" {
    u8* UiMenu_GetSortOptions_002a0fac(void* work);
    void qsort_002b7f0a(void* base, u32 num, u32 size, CompareFn cmp);
    void qsort_tail_0027f3d4(void* base, u32 num, u32 size, CompareFn cmp);

    extern void* g_StatusDownContext_0044e190;
    extern int StatusDown_ItemSortByIdAsc(const void*, const void*);
    extern int StatusDown_ItemSortByIdDesc(const void*, const void*);
    extern int StatusDown_ItemSortByTypeAsc(const void*, const void*);
    extern int StatusDown_ItemSortByTypeDesc(const void*, const void*);
    extern int engine_func_002dca98(const void*, const void*);
    extern int engine_func_002c6d30(const void*, const void*);
    extern int engine_func_001f61a4(const void*, const void*);
    extern int engine_func_001d1bb8(const void*, const void*);
}

extern "C" void h8_ui_statusdown_itemsort_candidate() {
    u8* work = static_cast<u8*>(g_StatusDownContext_0044e190);
    if (!work) return;

    u8* opt = UiMenu_GetSortOptions_002a0fac(work);
    u8 mode_byte = opt[0x16];
    u32 crit = mode_byte & 0x7F;
    bool desc = (mode_byte >> 7) != 0;

    void* base = work + 0xE30;
    s16 count = *reinterpret_cast<s16*>(work + 0x2230);

    if (crit == 1) {
        CompareFn cmp = desc ? StatusDown_ItemSortByIdDesc : StatusDown_ItemSortByIdAsc;
        qsort_002b7f0a(base, count, 4, cmp);
    } else if (crit == 8) {
        CompareFn cmp = desc ? engine_func_002c6d30 : engine_func_002dca98;
        qsort_002b7f0a(base, count, 4, cmp);
    } else if (crit == 2) {
        CompareFn cmp = desc ? StatusDown_ItemSortByTypeDesc : StatusDown_ItemSortByTypeAsc;
        qsort_002b7f0a(base, count, 4, cmp);
    } else if (crit == 3) {
        CompareFn cmp = desc ? engine_func_001d1bb8 : engine_func_001f61a4;
        qsort_002b7f0a(base, count, 4, cmp);
    }
}

extern "C" void h8_ui_statusdown_itemsort_mutation() {
    u8* work = static_cast<u8*>(g_StatusDownContext_0044e190);
    if (work) work[0x410] = 0xFF;
}
