#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct ShopContext {
    u8 pad0[0x4C];
    u32 selected_item; // 0x4C
    u8 pad1[0x11];     // 0x50..0x60
    u8 dirty_flag;     // 0x61
    u8 is_locked;      // 0x62
};

extern "C" void h11_shop_setselecteditem_candidate(ShopContext* ctx, u32 item_id) {
    if (ctx->is_locked == 0) {
        if (ctx->selected_item != item_id) {
            ctx->dirty_flag = 1;
        }
        ctx->selected_item = item_id;
    }
}

extern "C" void h11_shop_setselecteditem_mutation(ShopContext* ctx, u32 item_id) {
    ctx->dirty_flag = 0xFF;
}
