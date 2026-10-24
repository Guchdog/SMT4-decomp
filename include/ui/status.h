#pragma once
#include <cstddef>
#include "types.h"
#include "ui/status_down.h"

namespace smt4::ui {

/**
 * Top-Screen Status HUD & Status Manager workspace (`0x1EBC` bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\status\Status.cpp`
 * Global manager: `g_StatusManager` at `0x0044E140`.
 */
struct StatusWork {
    void* calc_task;                    // +0x0000: "Status Calc" task handle (0x0018f560, prio 2)
    void* draw_back_up_left;            // +0x0004: "Status DrawBackUpLeft" (0x001cddf8, prio 0x65)
    void* draw_back_up_right;           // +0x0008: "Status DrawBackUpRight" (0x001cddf8, prio 0xCC)
    void* draw_up_left;                 // +0x000C: "Status DrawUpLeft" (0x001a310c, prio 0x7D)
    void* draw_up_right;                // +0x0010: "Status DrawUpRight" (0x001a310c, prio 0xDB)
    u32 field_14;                       // +0x0014
    u8 raw_panels[0x12EC - 0x18];       // +0x0018..+0x12EC: UI animation sprites & panel nodes
    s8 sub_state_ec;                    // +0x12EC: Sub-state query (0x0029b0e0)
    u8 pad_12ed[0x12FC - 0x12ED];       // +0x12ED..+0x12FC
    u16 field_12fc;                     // +0x12FC
    u16 field_12fe;                     // +0x12FE
    u8 unk_1300[0x1E61 - 0x1300];       // +0x1300: Actor pointer buffer & affinity layout
    u8 flag_1e61;                       // +0x1E61: Upper screen draw enable flag
    u8 unk_1e62;                        // +0x1E62
    s8 flag_1e63;                       // +0x1E63: Status flag (queried by 0x0026c8a8)
    s8 field_1e64;                      // +0x1E64: Queried by 0x001ddaf8
    u8 flag_1e65;                       // +0x1E65: Set by 0x0022e694
    u8 main_menu_id;                    // +0x1E66: Queried by Status_GetMainMenuId (0x0029af30)
    u8 sub_menu_state;                  // +0x1E67: Queried by Status_GetSubMenuState (0x00288408)
    u8 unk_1e68[0x1E71 - 0x1e68];       // +0x1E68..+0x1E71
    u8 mode_1e71;                       // +0x1E71: Set by 0x0026abc0
    u8 unk_1e72[0x1EA0 - 0x1E72];       // +0x1E72..+0x1EA0
    s32 scale_calc_val;                 // +0x1EA0: Queried by Status_GetCalculatedScale (0x00295010)
    u8 unk_1ea4[0x1EB6 - 0x1ea4];       // +0x1EA4..+0x1EB6
    u16 active_demon_id;                // +0x1EB6: Active demon ID (set by 0x00203338)
    u8 mode_1eb8;                       // +0x1EB8
    u8 mode_1eb9;                       // +0x1EB9: Set by 0x0026b810
    u8 pad_1eba[2];                     // +0x1EBA..+0x1EBC
};

static_assert(offsetof(StatusWork, calc_task) == 0x0000);
static_assert(offsetof(StatusWork, sub_state_ec) == 0x12EC);
static_assert(offsetof(StatusWork, flag_1e61) == 0x1E61);
static_assert(offsetof(StatusWork, flag_1e63) == 0x1E63);
static_assert(offsetof(StatusWork, field_1e64) == 0x1E64);
static_assert(offsetof(StatusWork, flag_1e65) == 0x1E65);
static_assert(offsetof(StatusWork, main_menu_id) == 0x1E66);
static_assert(offsetof(StatusWork, sub_menu_state) == 0x1E67);
static_assert(offsetof(StatusWork, mode_1e71) == 0x1E71);
static_assert(offsetof(StatusWork, scale_calc_val) == 0x1EA0);
static_assert(offsetof(StatusWork, active_demon_id) == 0x1EB6);
static_assert(offsetof(StatusWork, mode_1eb9) == 0x1EB9);
static_assert(sizeof(StatusWork) == 0x1EBC);

struct StatusManager {
    s8 ref_count;                       // +0x00
    u8 pad_01[3];                       // +0x01..+0x04
    StatusWork* work;                   // +0x04
};

extern StatusManager g_StatusManager;   // 0x0044E140

// Lifecycle & mode control
void Status_Init();                                                                 // 0x0028c2a8
void Status_Destroy(s32* out_x, s32* out_y, s32 panel_idx, f32 scale);              // 0x00289158

// Stereoscopic draw callbacks
void Status_DrawBackUp(void* arg);                                                  // 0x001cddf8
void Status_DrawUp(void* arg);                                                      // 0x001a310c

// Status calculations & state callbacks
void Status_CalcTaskCallback(void* arg);                                            // 0x0018f560

// Queries & state getters/setters
s8   Status_GetField1E64();                                                         // 0x001ddaf8
bool Status_IsState8();                                                             // 0x001ddb1c
void Status_SetActiveDemonId(u16 demon_id);                                         // 0x00203338
void Status_SetFlag1E65(u8 flag);                                                   // 0x0022e694
bool Status_IsActive();                                                             // 0x0022e6b4
void Status_SetMode1E71(u8 mode);                                                   // 0x0026abc0
void Status_SetMode1EB9(u8 mode);                                                   // 0x0026b810
s8   Status_GetFlag1E63();                                                          // 0x0026c8a8
void Status_ResetAffinityView();                                                    // 0x0026d8dc
u8   Status_GetSubMenuState();                                                      // 0x00288408
s32  Status_HandleLRPrompt();                                                       // 0x00293d64
void Status_UpdateAffinityTable();                                                  // 0x00293e4c
f32  Status_GetCalculatedScale();                                                   // 0x00295010
u8   Status_GetMainMenuId();                                                        // 0x0029af30
const u16* Status_GetSelectedActorPtr();                                            // 0x0029af4c
s8   Status_GetSubState();                                                          // 0x0029b0e0

/**
 * Character / Demon BustUp Renderer Workspace.
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\status\StatusBustUp.cpp`
 * Global manager: `g_StatusBustUpManager` at `0x0044E158`.
 */
struct StatusBustUpManager {
    s8 ref_count;                       // +0x00
    u8 pad_01[3];                       // +0x01..+0x04
    void* buffer1;                      // +0x04
    void* buffer2;                      // +0x08
};

extern StatusBustUpManager g_StatusBustUpManager; // 0x0044E158

void StatusBustUp_Init();                                                           // 0x00223a90

/**
 * Upper Screen Stereoscopic Camera Workspace (0x53C bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\status\StatusCamera.cpp`
 * Global pointer: `g_StatusCamera` at `0x0044E178`.
 */
struct StatusCameraWork {
    u8 raw[0x53C];
};

static_assert(sizeof(StatusCameraWork) == 0x53C);

extern StatusCameraWork* g_StatusCamera;                                            // 0x0044E178

void StatusCamera_Init(const f32* pos, const f32* target, const f32* up, f32 fov, f32 aspect, f32 near_z, f32 far_z, f32 scale); // 0x00258e38

} // namespace smt4::ui
