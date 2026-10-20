#include "camp/camp_main.h"
#include "ui/status_down.h"

namespace smt4::camp {

// DECOMP_FUNC(0x0017fe9c, 27308)
void Camp_MainProc(void* task_ctx) {
    (void)task_ctx;
    // Master Demonica Camp menu state machine:
    // 1. Manages Demonica visor OS animations and tab switches:
    //    - Items (Healing, Attack, Incense, Key Items, Relics)
    //    - Skills (Flynn & Demon skill inspection, affinity icons)
    //    - Gauntlet Apps (Stat bonuses, fusion enhancements, scout perks)
    //    - Party (Stock order, summoning/returning demons, whispering)
    //    - Quests (Main Quests, Challenge Quests, delivery checklists)
    //    - System (Save, Load, Game Settings, Difficulty)
    // 2. Polls Nintendo 3DS touch coordinates, Circle Pad / D-Pad navigation,
    //    and L/R trigger page flips.
    // 3. Dispatches transitions into Cathedral of Shadows (Unite) and Compendium (Bible).
}

// DECOMP_FUNC(0x0019a3ec, 12900)
void Camp_DrawStereoViews(void* task_ctx) {
    (void)task_ctx;
    // Dual-screen stereoscopic Demonica UI rendering pipeline:
    // 1. Upper stereoscopic 3D LCD (800x240, 400px per eye):
    //    - Left-eye & Right-eye holographic HUD passes with parallax offset
    //    - Real-time 3D demon portrait models and idle breathing animations
    //    - HP / MP status gauges and elemental affinity resistance grids
    // 2. Lower touchscreen LCD (320x240):
    //    - Interactive tab buttons with press states
    //    - Scrolling inventory item lists with description panes
    //    - Party formation quick-summon demon slots
}

} // namespace smt4::camp
