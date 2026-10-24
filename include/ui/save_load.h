#pragma once
#include <cstddef>
#include "types.h"
#include "ui/status_down.h"

namespace smt4::ui {

/**
 * One of the two 0x80-byte slot pages in `SaveLoadUIWork` (base +0x24C).
 * 0x00214964 walks the pages with `add fp,r6,sl,lsl #7` (0x00214B38) and
 * `add r2,fp,#0x24c` (0x00214B44/0x00214B5C), so every offset below is
 * page-relative.
 */
struct SaveSlotPage {
    char text[0x4C];                    // +0x00: UiFont_DrawText text (`add r2,fp,#0x24c`)
    u8   digit_4C;                      // +0x4C: `ldrb r0,[fp,#0x298]` (0x00214B68)
    u8   flags_4D;                      // +0x4D: `ldrb r3,[r3,#0x4d]` (0x00214C24)
    u8   pad_4E[0x02];
    u32  timer_50;                      // +0x50: `ldr r2,[r8,#0x50]` (0x00214EE0)
    u8   pad_54[0x04];
    u16  clamp_58;                      // +0x58: `ldrh r0,[r4,#0x58]` (0x00214E04)
    u16  frame_5A;                      // +0x5A: `ldrh r1,[r4,#0x5a]` (0x00214E2C)
    u16  icon_5C[3];                    // +0x5C..+0x61: `ldrh r0,[r8,#0x5c]` (0x0021513C)
    u16  pad_62;
    u16  pad_64;
    u16  counter_66;                    // +0x66: `ldrh r2,[r4,#0x66]` (0x002151DC)
    u8   pad_68[0x18];
};
static_assert(offsetof(SaveSlotPage, digit_4C) == 0x4C);
static_assert(offsetof(SaveSlotPage, flags_4D) == 0x4D);
static_assert(offsetof(SaveSlotPage, timer_50) == 0x50);
static_assert(offsetof(SaveSlotPage, clamp_58) == 0x58);
static_assert(offsetof(SaveSlotPage, frame_5A) == 0x5A);
static_assert(offsetof(SaveSlotPage, icon_5C) == 0x5C);
static_assert(offsetof(SaveSlotPage, counter_66) == 0x66);
static_assert(sizeof(SaveSlotPage) == 0x80);

/**
 * Save / Load UI Workspace (0x388 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\saveLoadUI\saveLoadUI.cpp`
 * Global manager: `g_SaveLoadUIManager` at `0x0044DE28`.
 *
 * The detailed fields below are the ones read by 0x00214964 (the two-page
 * slot renderer); each carries the proving instruction.  Fields that routine
 * does not touch stay unnamed.
 */
struct SaveLoadUIWork {
    void* calc_task;                    // +0x000: "BOOT Calc" task handle
    u8 pad_04[4];                       // +0x04
    u32 state;                          // +0x08: Menu state (0: slot select, 1: confirm, 2: save, 3: load)
    u32 sub_state;                      // +0x0C
    u32 selected_slot;                  // +0x010: Selected slot index (0..N)
    u8 pad_014[0x08];                   // +0x014..+0x01C
    f32 field_01C;                      // +0x01C: `vldr s0,[r0,#0x1c]` (0x00215520)
    u8 pad_020[0x0C];                   // +0x020..+0x02C
    f32 slot_scale_02C[2];              // +0x02C: `vldr s0,[r4,#0x2c]`, r4=work+slot*4 (0x00214AD4)
    u32 panel_034;                      // +0x034: `ldr r2,[r0,#0x34]!` (0x00214A20)
    u8 pad_038[0x11];                   // +0x038..+0x049
    s8  index_049;                      // +0x049: `ldrsb r4,[r0,#0x49]` (0x002149D8)
    u8 pad_04A[0x06];                   // +0x04A..+0x050
    u32 panel_050;                      // +0x050: `ldr r1,[r5,#0x50]` (0x00215744)
    u8 pad_054;                         // +0x054
    u8 flag_055;                        // +0x055: `ldrb r0,[r0,#0x55]` (0x002155A8)
    u8 pad_056[0x02];
    u32 field_058;                      // +0x058: `ldr r0,[r5,#0x58]` (0x002157D0)
    u8 pad_05C[0x04];
    u32 field_060;                      // +0x060: `ldr r0,[r5,#0x60]` (0x002157C0)
    u32 field_064;                      // +0x064: `ldr r3,[r0,#0x30]`, r0=work+0x34 (0x00214A24)
    s32 slot_pos_068[2];                // +0x068: `ldr r3,[r4,#0x68]`, r4=work+slot*4 (0x00214AFC)
    u8 flag_070;                        // +0x070: `ldrb r0,[r0,#0x70]` (0x0021547C)
    u8 flag_071;                        // +0x071: `ldrb r0,[r0,#0x71]` (0x0021548C)
    u8 flag_072;                        // +0x072: `ldrb r0,[r0,#0x72]` (0x002155B8)
    u8 pad_073[0x24C - 0x073];
    SaveSlotPage slots[2];              // +0x24C: two pages, stride 0x80
    u8 active_34C[2];                   // +0x34C: `ldrb r0,[r0,#0x34c]`, r0=work+slot (0x00214A48)
    u8 pad_34E[0x354 - 0x34E];
    u8 flag_354;                        // +0x354: `ldrb r0,[r0,#0x54]`, r0=work+0x300 (0x0021549C)
    u8 pad_355[0x374 - 0x355];
    f32 field_374;                      // +0x374: `vldr s0,[r0,#0x374]` (0x00215620)
    u8 busy_378;                        // +0x378: `ldrb r0,[r0,#0x78]`, r0=work+0x300 (0x00214984)
    u8 pad_379[0x388 - 0x379];
};

static_assert(offsetof(SaveLoadUIWork, calc_task) == 0x000);
static_assert(offsetof(SaveLoadUIWork, state) == 0x008);
static_assert(offsetof(SaveLoadUIWork, selected_slot) == 0x010);
static_assert(offsetof(SaveLoadUIWork, field_01C) == 0x01C);
static_assert(offsetof(SaveLoadUIWork, slot_scale_02C) == 0x02C);
static_assert(offsetof(SaveLoadUIWork, panel_034) == 0x034);
static_assert(offsetof(SaveLoadUIWork, index_049) == 0x049);
static_assert(offsetof(SaveLoadUIWork, panel_050) == 0x050);
static_assert(offsetof(SaveLoadUIWork, flag_055) == 0x055);
static_assert(offsetof(SaveLoadUIWork, field_058) == 0x058);
static_assert(offsetof(SaveLoadUIWork, field_060) == 0x060);
static_assert(offsetof(SaveLoadUIWork, field_064) == 0x064);
static_assert(offsetof(SaveLoadUIWork, slot_pos_068) == 0x068);
static_assert(offsetof(SaveLoadUIWork, flag_070) == 0x070);
static_assert(offsetof(SaveLoadUIWork, flag_071) == 0x071);
static_assert(offsetof(SaveLoadUIWork, flag_072) == 0x072);
static_assert(offsetof(SaveLoadUIWork, slots) == 0x24C);
static_assert(offsetof(SaveLoadUIWork, active_34C) == 0x34C);
static_assert(offsetof(SaveLoadUIWork, flag_354) == 0x354);
static_assert(offsetof(SaveLoadUIWork, field_374) == 0x374);
static_assert(offsetof(SaveLoadUIWork, busy_378) == 0x378);
static_assert(sizeof(SaveLoadUIWork) == 0x388);

struct SaveLoadUIManager {
    u8 flags;                           // +0x00: `ldrsb r0,[r0]` (0x0021591C)
    u8 pad_01[3];                       // +0x01..+0x04
    SaveLoadUIWork* work;               // +0x04: `ldr r0,[r0,#4]` (0x00214974)
    u32 selected;                       // +0x08: `ldr r0,[sb,#8]` (0x00214AE8)
    u32 pad_0c;
};

extern SaveLoadUIManager g_SaveLoadUIManager; // 0x0044DE28

// saveLoadUI API
void saveLoadUI_Init();                                                             // 0x00191eac
void saveLoadUI_DrawMain(void* arg);                                                // 0x001c897c
void func_001c8d28(void* arg);                                                      // 0x001c8d28
void saveLoadUI_Calc(void* arg);                                                    // 0x00202950

/**
 * Save / Load Thread Process Workspace (0x18 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\gamedata\SaveLoadProcess.cpp`
 */
struct SaveLoadProcess {
    void* thread_handle;                // +0x00
    u32 operation;                      // +0x04: 0: None, 1: Save, 2: Load
    u32 status;                         // +0x08: 0: Busy, 1: Done, -1: Error
    u32 slot_index;                     // +0x0C: Target file slot
    u32 file_size;                      // +0x10: Target payload size
    u32 bytes_transferred;              // +0x14: Progress counter
};

static_assert(sizeof(SaveLoadProcess) == 0x18);

// SaveLoadProcess API
void SaveLoadProcess_Init(void* arg);                                               // 0x0026b874
void SaveLoadProcess_Step(void* arg);                                               // 0x002ef9ac
void SaveLoadProcess_Write(void* arg);                                              // 0x002efb50
void SaveLoadProcess_Read(void* arg);                                               // 0x00322d70
void SaveLoadProcess_Close(void* arg);                                              // 0x00322f0c

} // namespace smt4::ui
