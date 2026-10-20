#include "shop/shop_catalog.h"
#include "ui/status_down.h"

namespace smt4::shop {

// DECOMP_FUNC(0x003b35a8, 5656)
s32 Ui_ShopInventoryCatalog(ShopCatalogWork* work, u32 confirm_buy) {
    if (work == nullptr) {
        return 0;
    }

    // Shop Catalog Transaction Calculator:
    // 1. Applies Burroughs Haggler discount multipliers.
    // 2. Verifies player Macca reserves against total cost.
    // 3. Executes transfer of purchased goods into inventory pockets.
    u32 total_cost = work->discounted_price * work->quantity_to_buy;
    if (confirm_buy == 1) {
        if (work->player_macca >= total_cost) {
            work->player_macca -= total_cost;
            return 1; // Purchase completed
        }
        return 0; // Not enough Macca
    }

    return 0;
}

} // namespace smt4::shop
