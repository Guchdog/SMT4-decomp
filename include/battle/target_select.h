#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::battle {

/**
 * Combat Battle Target Selection Workspace (0xB8 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\battle\btlTargetSelect.cpp`
 * Global instance: `g_pBtlTargetSelectWork` at `0x00439C60`.
 */
struct BtlTargetSelectWork {
    void* reticle_data;                 // +0x00: Targeting reticle render data (0x12C bytes)
    void* cursor_anim;                  // +0x04: Cursor animation controller (0x60 bytes)
    u8 flag_08;                         // +0x08
    u8 pad_09[3];                       // +0x09..+0x0C
    u8 pad_0C[0x20];                    // +0x0C..+0x2C
    void* target_list;                  // +0x2C
    u8 raw[0xB8 - 0x30];                // +0x30..+0xB8
};

static_assert(sizeof(BtlTargetSelectWork) == 0xB8);

extern BtlTargetSelectWork* g_pBtlTargetSelectWork; // 0x00439C60

void btlTargetSelect_Init(void* parent_work);                                       // 0x002e8294
void btlTargetSelect_Calc(void* task_ctx);                                          // 0x002e06bc
void eventView_DrawUp(void* task_ctx);                                              // 0x002e07a8
void StaffRoll_U_UR_Draw(void* task_ctx);                                           // 0x002e07ac
void tmnlMain_DrawDown(void* task_ctx);                                             // 0x002e08d4
void btlTargetSelect_DrawUp(void* task_ctx);                                        // 0x002f4aa4

} // namespace smt4::battle
