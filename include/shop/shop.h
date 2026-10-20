#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::shop {

/**
 * Mikado Blacksmith & Tokyo Underground Shop Manager Workspace (0x1C bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\shop\shopMain.cpp`
 * Global manager: `g_ShopMainManager` at `0x0044E050`.
 */
struct ShopMainWork {
    void* proc_task;                    // +0x00: Task handle ("ShopMainProc", tag 2)
    u8 flag_04;                         // +0x04
    u8 flag_05;                         // +0x05
    u8 shop_type;                       // +0x06: Mikado weapon, Tokyo weapon, item, relic
    u8 pad_07;                          // +0x07
    s32 shop_mode;                      // +0x08: Buy, Sell, Appraise, Talk
    u8 flag_0c;                         // +0x0C
    u8 pad_0d[7];                       // +0x0D..+0x14
    u8 flag_14;                         // +0x14
    u8 pad_15[3];                       // +0x15..+0x18
    void* shop_data;                    // +0x18: Loaded ShopTable.tbb / ShopSale.tbb reference
};

static_assert(sizeof(ShopMainWork) == 0x1C);

struct ShopMainManager {
    ShopMainWork* work;                 // +0x00
};

extern ShopMainManager g_ShopMainManager; // 0x0044E050

void shopMain_Init(void* arg0, s32 arg1);                                           // 0x001d3b10
void shopMain_Proc(void* task_ctx);                                                 // 0x001d9538
void shopMain_DrawUp(void* task_ctx);                                               // 0x001fdf4c
void shopMain_DrawDown(void* task_ctx);                                             // 0x0021ee14

} // namespace smt4::shop
