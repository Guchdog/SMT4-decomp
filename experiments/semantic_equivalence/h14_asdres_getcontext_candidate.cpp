#include <cstdint>
typedef uint8_t u8;

struct AsdResManager {
    u8 flag;
    u8 pad[7];
    void* active_ctx;
    void* default_ctx;
};

extern "C" {
    extern AsdResManager g_AsdResManager_00465170;
}

extern "C" void* h14_asdres_getcontext_candidate() {
    void* res;
    asm(
        "ldrb r1, [%1]\n\t"
        "cmp r1, #0\n\t"
        "ldrne %0, [%1, #8]\n\t"
        "ldreq %0, [%1, #12]"
        : "=r"(res) : "r"(&g_AsdResManager_00465170) : "r1", "cc"
    );
    return res;
}

extern "C" void* h14_asdres_getcontext_mutation() {
    return nullptr;
}
