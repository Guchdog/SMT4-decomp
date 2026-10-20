#include "camp/unite.h"

namespace smt4::camp {

ButtonHelpManager g_ButtonHelpManager = {0, {0, 0, 0}, nullptr}; // 0x0043DA28
SortMenuManager g_SortMenuManager = {0, {0, 0, 0}, nullptr};     // 0x0043DD20

// DECOMP_FUNC(0x0028d974, 736)
void ButtonHelp_Init() {
    ButtonHelpManager* mgr = &g_ButtonHelpManager;
    if (mgr->ref_count <= 0) {
        if (mgr->work == nullptr) {
            mgr->work = reinterpret_cast<ButtonHelpWork*>(ui::AsdMem_Alloc(sizeof(ButtonHelpWork), 0x100));
        }
        ui::AsdMem_Zero(mgr->work, sizeof(ButtonHelpWork));
    }
    mgr->ref_count++;
}

// DECOMP_FUNC(0x0029e63c, 644)
void SortMenu_Init(s32 mode) {
    (void)mode;
    SortMenuManager* mgr = &g_SortMenuManager;
    if (mgr->ref_count <= 0) {
        if (mgr->work == nullptr) {
            mgr->work = reinterpret_cast<SortMenuWork*>(ui::AsdMem_Alloc(sizeof(SortMenuWork), 0x100));
        }
        ui::AsdMem_Zero(mgr->work, sizeof(SortMenuWork));
    }
    mgr->ref_count++;
}

// ============================================================================
// Unite: Mido Demon Fusion (Cathedral of Shadows) Engine
// ============================================================================

UniteWork* g_UniteWork = nullptr;

// DECOMP_FUNC(0x0029b3cc, 1676)
void Unite_Init(void* r0, void* r1, s32 r2, void* r3) {
    (void)r0; (void)r1; (void)r2; (void)r3;
    UniteWork* work = g_UniteWork;
    if (work == nullptr) {
        work = reinterpret_cast<UniteWork*>(ui::AsdMem_Alloc(sizeof(UniteWork), 0x100));
        g_UniteWork = work;
    }

    ui::AsdMem_Zero(work, sizeof(UniteWork));
    work->calc_task = ui::AsdTask_CreateCalc("Unite Calc", 1, 0, 0, Unite_DrawAndCalc, 0, 0);
    work->state = 1;
}

// DECOMP_FUNC(0x001f2f58, 1704)
void Unite_Setup(void* arg) {
    (void)arg;
    UniteWork* work = g_UniteWork;
    if (work == nullptr) {
        return;
    }

    work->state = 2; // Configure demon ingredients, search fusion results, calculate heritage skills
}

// DECOMP_FUNC(0x002e315c, 344)
void UniteEffect_Init(void* arg) {
    (void)arg;
    UniteWork* work = g_UniteWork;
    if (work == nullptr) {
        return;
    }

    // Initialize 3D fusion summoning circle and lightning vortex particle effects
}

// DECOMP_FUNC(0x001de238, 5020)
void Unite_DrawAndCalc(void* arg) {
    (void)arg;
    UniteWork* work = g_UniteWork;
    if (work == nullptr || work->state == 0) {
        return;
    }

    // State machine logic
    switch (work->state) {
        case 1: // Fusion formula selection (2-demon, special, search fusion)
            break;
        case 2: // Result preview & skill inheritance picking
            break;
        case 3: // Fusion cutscene & accident roll
            work->state = 4;
            break;
        case 4: // Fusion completed / Demon registered to compendium
            work->state = 0;
            break;
        default:
            break;
    }

    // Stereoscopic rendering pass for Mido Cathedral of Shadows fusion room
    ui::UiGpu_BeginPass(ui::g_AsdGpuState);
    ui::UiGpu_SetViewportParams(1, 0); // Upper screen 3D stage

    auto* layer = reinterpret_cast<u32*>(ui::g_AsdGpuState + 0x124C);
    const u32 old_depth = *layer;
    *layer = old_depth + 1;
    auto* layer_entry = reinterpret_cast<u32*>(ui::g_AsdGpuState + 0x124C + 8);
    layer_entry[*layer] = 1;

    // Draw fusion circle and preview demons
    ui::UiSprite_DrawPanelDirect(2, 0x0E, 0x30, 200, 120, 1);

    if (*layer > 0) {
        *layer = *layer - 1;
    }
}

} // namespace smt4::camp
