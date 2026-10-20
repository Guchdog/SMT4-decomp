#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::battle {

/**
 * Combat Battle Help Modal Workspace.
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\battle\btlHelp.cpp`
 */
struct BtlHelpWork {
    void* parent_work;                  // +0x00
    u8 pad_04[0x48];                    // +0x04..+0x4C
    void* calc_task;                    // +0x4C: Task handle ("btlHelp Calc", tag 0x2)
    u8 pad_50[4];                       // +0x50..+0x54
};

static_assert(sizeof(BtlHelpWork) == 0x54);

struct BtlHelpManager {
    void* buffer;                       // +0x00
};

extern BtlHelpManager g_BtlHelpManager; // 0x00435D78

void btlHelp_Init(BtlHelpWork* work);                                               // 0x001d2528

/**
 * Combat Demon Talk Modal Workspace.
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\battle\btlTalk.cpp`
 */
struct BtlTalkWork {
    void* parent_work;                  // +0x00
    u8 pad_04[0x1C];                    // +0x04..+0x20
    void* talk_task;                    // +0x20: Task handle ("btlTalk Calc", tag 0x2)
    u8 pad_24[0x10];                    // +0x24..+0x34
};

static_assert(sizeof(BtlTalkWork) == 0x34);

struct BtlTalkBuffer {
    void* parent;                       // +0x00
    void* ctx;                          // +0x04
    u8 pad_08[0x10];                    // +0x08..+0x18
    s32 state;                          // +0x18
    s32 arg2;                           // +0x1C
    s32 arg3;                           // +0x20
    u8 pad_24[0xC];                     // +0x24..+0x30
    s32 speaker_id;                     // +0x30
    u8 raw[0xCC - 0x34];                // +0x34..+0xCC
};

static_assert(sizeof(BtlTalkBuffer) == 0xCC);

extern BtlTalkBuffer* g_pBtlTalkBuffer; // 0x00439B58

void btlTalk_Init(BtlTalkWork* work, void* ctx, s32 arg2, s32 arg3);                // 0x001d2610

/**
 * Combat Battle Unit Manager Workspace.
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\battle\btlUnit.cpp`
 */
struct BtlUnitWork {
    void* parent_work;                  // +0x00
    u8 pad_04[0x30];                    // +0x04..+0x34
    void* unit_task;                    // +0x34: Task handle ("btlUnit Calc", tag 0x2)
    u8 pad_38[0x96];                    // +0x38..+0xCE
    u16 sub_party_id;                   // +0xCE
    u8 pad_D0[0x1A8];                   // +0xD0..+0x278
    u16* party_slots;                   // +0x278: Active party slots (array of 8 unit IDs)
    u16* reserve_slots;                 // +0x27C: Reserve slots (array of 8 unit IDs)
    u8 pad_280[4];                      // +0x280..+0x284
    void* guest_unit;                   // +0x284: Guest unit pointer
};

static_assert(sizeof(BtlUnitWork) == 0x288);

void btlUnit_Init(BtlUnitWork* work);                                               // 0x001d2744
s32  btlUnit_CheckPartyActive(BtlUnitWork* work);                                   // 0x001d29c8

/**
 * Combat Battle UI & Turn Gauge HUD Workspace (0x120 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\battle\btlUI.cpp`
 */
struct BtlUIWork {
    void* parent_work;                  // +0x00
    u8 pad_04[0x50];                    // +0x04..+0x54
    void* calc_task;                    // +0x54: Task handle ("btlUI Calc", tag 0x2)
    u8 pad_58[0x24];                    // +0x58..+0x7C
    u32 flags;                          // +0x7C
    u8 raw[0x120 - 0x80];               // +0x80..+0x120
};

static_assert(sizeof(BtlUIWork) == 0x120);

struct BtlUIManager {
    BtlUIWork* ui_work;                 // +0x00
    u8 pad_04[0x1C];                    // +0x04..+0x20
    void* buffer;                       // +0x20: Dynamic UI buffer (0xF040 bytes)
};

extern BtlUIManager g_BtlUIManager;     // 0x00439C88

void btlUI_Init(BtlUIWork* work);                                                   // 0x001a83c8
void btlUI_Calc(void* task_ctx);                                                    // 0x0019e034
void btlUI_DrawUp(void* task_ctx);                                                  // 0x001b71e0
void btlUI_DrawDown(void* task_ctx);                                                // 0x001e4ae4
void btlUI_DrawNumber(void* task_ctx);                                              // 0x0020f35c

} // namespace smt4::battle
