#include <cstdint>

typedef uint8_t u8;
typedef uint32_t u32;
typedef int32_t s32;

extern "C" {
    void* TargetSelect_GetWork_002c0ac8();
    void TargetSelect_UpdateAnim_002bf9f0(void*);
    void TargetSelect_Mode1Calc_003428a4(void*);
}

extern "C" s32 h5_btl_target_select_calc_candidate(void) {
    void* work = TargetSelect_GetWork_002c0ac8();
    if (!work) return 0;

    TargetSelect_UpdateAnim_002bf9f0((char*)work + 0x2C);

    u32 state = *(u32*)((char*)work + 0x30);
    u32 flag = (state != 0x71) ? 1 : 0;

    void* obj0 = *(void**)work;
    if (obj0) {
        *(u32*)((char*)obj0 + 0x120) = flag;
    }

    void* obj1 = *(void**)((char*)work + 4);
    if (obj1) {
        *(u32*)((char*)obj1 + 0x54) = flag;
    }

    u8 mode = *(u8*)((char*)work + 8);
    if (mode == 1) {
        if (obj0) {
            TargetSelect_Mode1Calc_003428a4(obj0);
        }
    } else if (mode == 2) {
        if (obj1) {
            float* f58 = (float*)((char*)obj1 + 0x58);
            float* f5c = (float*)((char*)obj1 + 0x5C);

            *f58 += 1.0f;
            if (*f58 >= 30.0f) {
                *f58 -= 30.0f;
            }

            *f5c += 12.0f;
            if (*f5c > 360.0f) {
                *f5c -= 360.0f;
            }
        }
    }
    return 0;
}

extern "C" s32 h5_btl_target_select_calc_mutation(void) {
    // Deliberate mutation: adds 2.0f instead of 1.0f
    void* work = TargetSelect_GetWork_002c0ac8();
    if (!work) return 0;
    void* obj1 = *(void**)((char*)work + 4);
    if (obj1) {
        float* f58 = (float*)((char*)obj1 + 0x58);
        *f58 += 2.0f;
    }
    return 0;
}
