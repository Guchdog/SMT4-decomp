#include <cstdint>

typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    void engine_func_002bdc08(void* obj, u32 flag);
    void engine_func_002bdbcc(void* slot);

    extern u32 g_ComWinContext_004e2f68[];
}

extern "C" void h7_ui_comwin_reset_candidate() {
    u8* work = reinterpret_cast<u8*>(g_ComWinContext_004e2f68[0x204 / 4]);
    if (work) {
        u8* slot = work + 0x20;
        int i = 8;
        #pragma clang loop unroll(disable)
        do {
            void* obj = *reinterpret_cast<void**>(slot);
            if (obj) {
                engine_func_002bdc08(obj, 0);
                engine_func_002bdbcc(slot);
            }
            slot += 4;
        } while (--i);
    }
}

extern "C" void h7_ui_comwin_reset_mutation() {
    g_ComWinContext_004e2f68[0x204 / 4] = 0;
}
