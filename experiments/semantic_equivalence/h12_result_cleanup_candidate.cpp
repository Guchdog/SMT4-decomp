#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    extern void* g_ResultWork_0044dc20;
    void sub_2A755C(void*);
    void sub_2C4360(void*);
    void sub_2C0128();
    void sub_2A497C(u32);
    void sub_2AEB2C(u32, u32);
}

extern "C" void h12_result_cleanup_candidate() {
    u8* work = static_cast<u8*>(g_ResultWork_0044dc20);
    if (!work) return;
    sub_2A755C(*reinterpret_cast<void**>(work + 0x3568));
    sub_2C4360(*reinterpret_cast<void**>(work + 0x3564));
    sub_2C4360(*reinterpret_cast<void**>(work + 0x356c));
    sub_2C0128();
    sub_2C4360(*reinterpret_cast<void**>(work + 0x3570));
    sub_2A497C(0x14);
    sub_2A497C(0x25);
    for (u32 i = 0; i < 2; ++i) {
        sub_2AEB2C(0x28, i);
    }
    sub_2C4360(work);
    g_ResultWork_0044dc20 = nullptr;
}

extern "C" void h12_result_cleanup_mutation() {
    g_ResultWork_0044dc20 = reinterpret_cast<void*>(0xDEADBEEF);
}
