#include <cstdint>
typedef uint32_t u32;
typedef int32_t s32;
typedef uint8_t u8;

extern "C" {
    void* sub_22EBBC();
    s32 sub_2C615C(void* p, u32 item_id);
    s32 sub_2B9100(void* ctx);
    s32 sub_28FDE4(void* ctx);
}

extern "C" s32 h11_shop_calcpurchasableqty_candidate(void* ctx, u32 item_id) {
    void* p = sub_22EBBC();
    s32 qty = sub_2C615C(p, item_id);
    if (qty < 0) {
        qty = 0;
    } else if (qty > 99) {
        qty = 99;
    }
    s32 max_bag = sub_2B9100(ctx);
    s32 current_bag = sub_28FDE4(ctx);
    s32 remaining = max_bag - current_bag;
    if (qty < 0) {
        qty = 0;
    }
    if (remaining < qty) {
        qty = remaining;
    }
    return qty;
}

extern "C" s32 h11_shop_calcpurchasableqty_mutation(void* ctx, u32 item_id) {
    return -999;
}
