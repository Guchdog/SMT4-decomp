#include "camp/camp_inventory.h"
#include "ui/status_down.h"

namespace smt4::camp {

// DECOMP_FUNC(0x002d966c, 5336)
void Camp_ItemInventorySort(ItemInventoryWork* work, u32 sort_mode) {
    if (work == nullptr || work->total_items == 0) {
        return;
    }

    // Demonica Item Pocket Sorter:
    // Sorts player consumable items and relics across categories.
    work->sort_order = sort_mode;
}

} // namespace smt4::camp
