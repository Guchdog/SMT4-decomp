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

    volatile u8* opt = UiMenu_GetSortOptions_002a0fac(work);
    void* base = work + 0xE30;
    s16 count = *reinterpret_cast<volatile s16*>(work + 0x2230);

    u8 m1 = opt[0x16];
    if ((m1 & 0x7F) == 1) {
        CompareFn cmp = (m1 >> 7) ? StatusDown_ItemSortByIdDesc : StatusDown_ItemSortByIdAsc;
        qsort_002b7f0a(base, count, 4, cmp);
    }
    u8 m8 = opt[0x16];
    if ((m8 & 0x7F) == 8) {
        CompareFn cmp = (m8 >> 7) ? StatusDown_ItemSortByTypeDesc : StatusDown_ItemSortByTypeAsc;
        qsort_002b7f0a(base, count, 4, cmp);
    }
    u8 m2 = opt[0x16];
    if ((m2 & 0x7F) == 2) {
        CompareFn cmp = (m2 >> 7) ? engine_func_002c6d30 : engine_func_001d1bb8;
        qsort_002b7f0a(base, count, 4, cmp);
    }
    u8 m3 = opt[0x16];
    if ((m3 & 0x7F) == 3) {
        CompareFn cmp = (m3 >> 7) ? engine_func_002dca98 : engine_func_001f61a4;
        qsort_002b7f0a(base, count, 4, cmp);
    }
}

extern "C" void h8_ui_statusdown_itemsort_mutation() {
    u8* work = static_cast<u8*>(g_StatusDownContext_0044e190);
    if (work) work[0x410] = 0xFF;
}
