#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::camp {

/**
 * Camp Item Pocket Inventory Sorting & Category Filter Workspace.
 * Handles item categorization:
 * - Recovery items (Medicine, Bead, Chakra Drop)
 * - Attack items (Agilao Stone, Bufudyne Stone)
 * - Support items (Smoke Ball, Repel Glass)
 * - Key/Relic items
 */
struct ItemInventoryWork {
    u16 item_ids[256];              // +0x00: Packed item inventory slots
    u8 item_quantities[256];        // +0x200: Quantity per slot
    u32 total_items;                // +0x300: Total unique items held
    u32 current_category;           // +0x304: Active tab filter
    u32 sort_order;                 // +0x308: 0 = ID, 1 = Type, 2 = Quantity
};

/**
 * Sorts and filters item inventory based on active pocket category and sort mode.
 *
 * Address: 0x002d966c, Size: 5,336 bytes
 */
void Camp_ItemInventorySort(ItemInventoryWork* work, u32 sort_mode);

} // namespace smt4::camp
