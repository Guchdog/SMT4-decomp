#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::ui {

/**
 * Ally Demon (Nakama) Base Table & Encounter Metadata Workspace.
 * Original Atlus source paths:
 *   - `battle/NKMBaseTable.tbb`
 *   - `battle/NKMSortIndex.tbb`
 *   - `battle/EncountData.tbb`
 *   - `battle/EventEncountData.tbb`
 */
struct BattleTableWork {
    void* nkm_table_buf;            // +0x00: Loaded NKMBaseTable pointer
    u32 nkm_table_size;             // +0x04: Size of ally demon definitions
    void* encount_table_buf;        // +0x08: Loaded EncountData pointer
    u32 total_encounters;           // +0x0C: Total indexed encounter packs
    u32 load_status;                // +0x10: 1 when tables are mounted
};

/**
 * Real-time Combat Command Selector Menu (Flynn Attack/Shoot/Skill/Item/Negotiate).
 */
struct BattleCommandWork {
    u32 active_cursor_slot;         // +0x00: Currently focused menu command index
    u32 selection_state;            // +0x04: 0 = idle, 1 = confirm, 2 = cancel
    u32 can_use_gun;                // +0x08: 1 if Flynn has gun & bullets equipped
    u32 can_negotiate;              // +0x0C: 1 if demon talk is enabled
    f32 cursor_anim_timer;          // +0x10: Cursor highlight pulse timer
};

/**
 * Battle Message and Dialogue Window.
 */
struct BattleMessageWork {
    char message_text[256];         // +0x00: Displayed combat dialogue text
    u32 window_state;               // +0x100: 0 = hidden, 1 = scrolling, 2 = awaiting prompt
    f32 type_delay_timer;           // +0x104: Text typing animation clock
};

/**
 * Battle Action Effect & Critical/Smirk Cut-in Overlay.
 */
struct BattleActionOverlayWork {
    u32 effect_type;                // +0x00: 0 = normal, 1 = weakness hit, 2 = critical, 3 = smirk
    f32 screen_shake_intensity;     // +0x04: Screen shake amplitude
    f32 flash_alpha;                // +0x08: Fullscreen color flash transparency
    u32 target_actor_index;         // +0x0C: Targeted demon slot index
};

/**
 * Loads ally demon (Nakama) base tables, sort indices, and encounter data files
 * from the RomFS battle partition.
 *
 * Address: 0x003efa10, Size: 12,708 bytes
 */
void Ui_NkmBaseTableLoad(BattleTableWork* work, void* file_ctx);

/**
 * Handles lower screen battle command selection (Attack, Shoot, Skills, Items, Talk).
 *
 * Address: 0x0025d3fc, Size: 7,328 bytes
 */
void Ui_BattleCommandMenu(BattleCommandWork* work, u32 pad_input);

/**
 * Renders combat dialogue, turn announcements, and demon encounter chatter.
 *
 * Address: 0x003f34f8, Size: 7,984 bytes
 */
void Ui_BattleMessageWindow(BattleMessageWork* work, void* render_ctx);

/**
 * Computes and renders weakness exploitation, critical cut-ins, and smirk banner overlays.
 *
 * Address: 0x003ec954, Size: 6,616 bytes
 */
void Ui_BattleActionEffectOverlay(BattleActionOverlayWork* work, void* render_ctx);

} // namespace smt4::ui
