#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    extern void* g_BattleTurnWork_0044e32c;
    void sub_136FA4(void*);
    void sub_132FB8(void*);
    void sub_1423C0(void*);
    void sub_13348C(void*);
}

extern "C" u32 h12_battle_initturnsubsystems_candidate(void* arg) {
    g_BattleTurnWork_0044e32c = arg;
    u8* p = static_cast<u8*>(arg);
    sub_136FA4(p);
    sub_132FB8(p + 4);
    sub_1423C0(p + 8);
    sub_13348C(p + 0xC);
    return 0;
}

extern "C" u32 h12_battle_initturnsubsystems_mutation(void* arg) {
    return 0xDEADBEEF;
}
