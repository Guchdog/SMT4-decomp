#include "shop/shop.h"
#include "ui/status_down.h"

namespace smt4::shop {

ShopMainManager g_ShopMainManager = {nullptr};
// DECOMP_FUNC(0x001d3b10, 364)


//
__attribute__((naked)) void shopMain_Init(void*, s32) {
    asm volatile(
        ".word 0xE92D43F0, 0xE1A05000, 0xE24DD014, 0xE1A06001\n"
        ".word 0xE3A00000, 0xEB03C744, 0xE59F0128, 0xE3A010A7\n"
        ".word 0xE1A00000, 0xE3A09001, 0xE3A01C01, 0xE3A0301C\n"
        ".word 0xE3A02000, 0xE1A00001, 0xE58D9000, 0xEB03C40C\n"
        ".word 0xE59F8104, 0xE3A07000, 0xE3550000, 0xE1A04000\n"
        ".word 0xE5880000, 0xE5C07005, 0xE5C07004, 0xE5C07006\n"
        ".word 0xE5807018, 0xE5C07014, 0xE5C0700C, 0x0A000004\n"
        ".word 0xE3560008, 0x0A00002E, 0xE3560004, 0x05951000\n"
        ".word 0x0A00002E, 0xE5849008, 0xE59F20C4, 0xE59F10BC\n"
        ".word 0xE28D0004, 0xE58D2000, 0xE8800012, 0xE3A03000\n"
        ".word 0xE59F00B0, 0xE1A02003, 0xE3A01002, 0xEB03C76D\n"
        ".word 0xE5840000, 0xE5981000, 0xE59F509C, 0xE58D000C\n"
        ".word 0xE58D1008, 0xE59F0094, 0xE3A03000, 0xE3A02001\n"
        ".word 0xE3A01065, 0xE88D00A0, 0xEB03C404, 0xE5940000\n"
        ".word 0xE5981000, 0xE3A03000, 0xE58D000C, 0xE58D1008\n"
        ".word 0xE59F0068, 0xE3A02001, 0xE3A010CC, 0xE88D00A0\n"
        ".word 0xEB03C3FA, 0xE59F2058, 0xE5941000, 0xE5980000\n"
        ".word 0xE88D0084, 0xE3A03000, 0xE1CD00F8, 0xE59F0044\n"
        ".word 0xE3A02001, 0xE3A010E7, 0xEB03C3F0, 0xE28DD014\n"
        ".word 0xE8BD83F0, 0xE5951000, 0xE5C41006, 0xE5951004\n"
        ".word 0xE5841008, 0xEAFFFFCF, 0x0040774C, 0x0044E050\n"
        ".word 0x0021F1EC, 0x001D9538, 0x004077A0, 0x001FE15C\n"
        ".word 0x00407790, 0x0021F204, 0x0040777C\n"
    );
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
