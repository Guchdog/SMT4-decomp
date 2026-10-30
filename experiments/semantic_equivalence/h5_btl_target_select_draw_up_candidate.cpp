#include <cstdint>

typedef uint8_t u8;
typedef int32_t s32;

extern "C" {
    void* TargetSelect_GetWork_002c0ac8();
    void TargetSelect_DrawMode1_00342b54(void*);
    void TargetSelect_DrawMode2_0034946c(void*);
}

extern "C" s32 h5_btl_target_select_draw_up_candidate(void) {
    void* work = TargetSelect_GetWork_002c0ac8();
    if (!work) return 0;

    u8 mode = *(u8*)((char*)work + 8);
    if (mode == 1) {
        void* obj = *(void**)work;
        TargetSelect_DrawMode1_00342b54(obj);
    } else if (mode == 2) {
        void* obj = *(void**)((char*)work + 4);
        TargetSelect_DrawMode2_0034946c(obj);
    }
    return 0;
}

extern "C" s32 h5_btl_target_select_draw_up_mutation(void) {
    // Deliberate mutation: swaps mode 1 and mode 2
    void* work = TargetSelect_GetWork_002c0ac8();
    if (!work) return 0;

    u8 mode = *(u8*)((char*)work + 8);
    if (mode == 2) {
        void* obj = *(void**)work;
        TargetSelect_DrawMode1_00342b54(obj);
    } else if (mode == 1) {
        void* obj = *(void**)((char*)work + 4);
        TargetSelect_DrawMode2_0034946c(obj);
    }
    return 0;
}
