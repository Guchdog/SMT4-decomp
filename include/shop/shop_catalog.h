#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::shop {

/**
 * Shop Goods Catalog & Pricing Workspace.
 * Manages merchandise listing, Flynn discount apps (Expert / Master Haggler),
 * weapon/armor previews, and purchase confirmations.
 */
struct ShopCatalogWork {
    u32 shopkeeper_id;              // +0x00: Shop NPC merchant index (Q, Bito, Ginza luxury, etc.)
    u32 selected_item_id;           // +0x04: Currently highlighted merchandise
    u32 base_price;                 // +0x08: Default retail price
    u32 discounted_price;           // +0x0C: Price after Burroughs discount perks
    u32 player_macca;               // +0x10: Flynn's current funds
    u32 quantity_to_buy;            // +0x14: Batch purchase count
};

/**
 * Calculates shop prices, discounts, and item transaction feasibility.
 *
 * Address: 0x003b35a8, Size: 5,656 bytes
 */
s32 Ui_ShopInventoryCatalog(ShopCatalogWork* work, u32 confirm_buy);

} // namespace smt4::shop
