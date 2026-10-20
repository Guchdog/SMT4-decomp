#include "shop/shop.h"
#include "ui/status_down.h"

namespace smt4::shop {

ShopMainManager g_ShopMainManager = {nullptr};

// DECOMP_FUNC(0x001d3b10, 364)
void shopMain_Init(void* arg0, s32 arg1) {
    ShopMainWork* work = reinterpret_cast<ShopMainWork*>(ui::AsdMem_Alloc(sizeof(ShopMainWork), 0x100));
    g_ShopMainManager.work = work;

    if (work == nullptr) {
        return;
    }

    work->flag_04 = 0;
    work->flag_05 = 0;
    work->shop_type = 0;
    work->shop_data = nullptr;
    work->flag_14 = 0;
    work->flag_0c = 0;

    if (arg0 != nullptr) {
        if (arg1 == 8) {
            work->shop_type = *reinterpret_cast<u8*>(arg0);
            work->shop_mode = reinterpret_cast<s32*>(arg0)[1];
        } else if (arg1 == 4) {
            work->shop_mode = *reinterpret_cast<s32*>(arg0);
        }
    } else {
        work->shop_mode = 1;
    }

    // Register ShopMainProc calculation task (tag 2)
    work->proc_task = ui::AsdTask_CreateCalc("ShopMainProc", 2, 0, 0, nullptr, work, 0);

    // Register ShopMainDrawUp stereoscopic 3D passes (tag 0x65 Upper Left, tag 0xCC Upper Right)
    ui::AsdTask_CreateDraw("ShopMainDrawUp", 0x65, 1, 0, nullptr, work, 0);
    ui::AsdTask_CreateDraw("ShopMainDrawUp", 0xCC, 1, 0, nullptr, work, 0);

    // Register ShopMainDrawDown touch screen shopping interface (tag 0xE7)
    ui::AsdTask_CreateDraw("ShopMainDrawDown", 0xE7, 1, 0, nullptr, work, 0);
}

// DECOMP_FUNC(0x001d9538, 908)
void shopMain_Proc(void* task_ctx) {
    (void)task_ctx;
    // Shop logic processor: handles Macca transaction verification,
    // item/relic count limits, equipment preview stat comparison,
    // and prompt confirmations.
}

// DECOMP_FUNC(0x001fdf4c, 1132)
void shopMain_DrawUp(void* task_ctx) {
    (void)task_ctx;
    // Upper screen 3D shopkeeper bustup, shop banner, item description window,
    // and party stat delta preview.
}

// DECOMP_FUNC(0x0021ee14, 1416)
void shopMain_DrawDown(void* task_ctx) {
    (void)task_ctx;
    // Lower touch screen inventory listbox, Buy/Sell/Appraise category tabs,
    // Macca balance display, and quantity selector.
}

} // namespace smt4::shop
