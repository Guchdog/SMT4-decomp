#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::ui {

/**
 * Combat & Quest Result Subsystem Workspace (0xD658 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\result\Result.cpp`
 * Global instance: `g_pResultWork` at `0x0044DC20`.
 */
struct ResultWork {
    u8 pad_00[0x3560];                  // +0x0000..+0x3560
    u8 result_mode;                     // +0x3560: 0 = battle victory, 1 = quest complete
    u8 pad_3561[0xD644 - 0x3561];       // +0x3561..+0xD644
    void* calc_task;                    // +0xD644: Task handle ("Result CALC", tag 2)
    u8 pad_D648[4];                     // +0xD648..+0xD64C
    void* draw_down_task;               // +0xD64C: Task handle ("Result DDRAW", tag 0xE6)
    u8 raw[0xD658 - 0xD650];            // +0xD650..+0xD658
};

static_assert(sizeof(ResultWork) == 0xD658);

struct ResultManager {
    ResultWork* work;                   // +0x00
};

extern ResultManager g_ResultManager;   // 0x0044DC20

void Result_Init(s32 mode);                                                         // 0x0029bc38
void Result_Calc(void* task_ctx);                                                   // 0x0018bfec
void Result_DrawUp(void* task_ctx);                                                 // 0x001a15b0
void Result_DrawDown(void* task_ctx);                                               // 0x001c87d8
void func_001c8874(void* task_ctx);                                                 // 0x001c8874

} // namespace smt4::ui
