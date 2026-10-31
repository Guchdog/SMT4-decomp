#include <cstdint>
typedef uint32_t u32;

extern "C" {
    u32 shop_func_0026f0d8(u32 type);
    u32 shop_func_002b902c(u32 flag);
}

extern "C" u32 h11_shop_checkhasnew_promoted(void* ctx) {
    u32 res = 0;
    if (shop_func_0026f0d8(6) != 0) {
        res = 1;
    }
    if (shop_func_002b902c(7) != 0) {
        res = 1;
    }
    return res;
}

extern "C" u32 h11_shop_checkhasnew_mutation(void* ctx) {
    return 0xDEADBEEF;
}
