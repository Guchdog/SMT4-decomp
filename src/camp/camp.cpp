#include "camp/camp.h"

namespace smt4::camp {

CampWork* g_CampWork = nullptr;                         // 0x0043DA90
GauntletAppMenuWork* g_GauntletAppMenuWork = nullptr;   // 0x0043DC88

// DECOMP_FUNC(0x0028a688, 1284)
void Camp_Init() {
    CampWork* work = g_CampWork;
    if (work == nullptr) {
        work = reinterpret_cast<CampWork*>(ui::AsdMem_Alloc(sizeof(CampWork), 0x100));
        g_CampWork = work;
    }

    ui::AsdMem_Zero(work, sizeof(CampWork));
    work->calc_task = ui::AsdTask_CreateCalc("Camp Calc", 1, 0, 0, Camp_Calc, 0, 0);
    work->state = 1;
}

// DECOMP_FUNC(0x0028ab8c, 3796)
void Camp_Calc(void* arg) {
    (void)arg;
    CampWork* work = g_CampWork;
    if (work == nullptr || work->state == 0) {
        return;
    }

    // Top-level Camp state machine
    switch (work->state) {
        case 1: // Opening Camp menu (fade in Demonica top and bottom screens)
            work->state = 2;
            break;
        case 2: // Main menu navigation: Items, Skills, Demonica Apps, Party, Quest, System
            break;
        case 3: // Sub-menu active (Gauntlet Apps, Status, Config)
            break;
        case 4: // Closing / Exit Camp
            work->state = 0;
            break;
        default:
            break;
    }
}

// DECOMP_FUNC(0x0028ba60, 1608)
void PartyPanel_DrawAndCalc(void* arg) {
    (void)arg;
    CampWork* work = g_CampWork;
    if (work == nullptr || work->state == 0) {
        return;
    }

    // Bottom screen party panel slots & HP/MP gauge rendering pass
    ui::UiGpu_BeginPass(ui::g_AsdGpuState);
    ui::UiGpu_SetViewportParams(0, 0);

    auto* layer = reinterpret_cast<u32*>(ui::g_AsdGpuState + 0x124C);
    const u32 old_depth = *layer;
    *layer = old_depth + 1;
    auto* layer_entry = reinterpret_cast<u32*>(ui::g_AsdGpuState + 0x124C + 8);
    layer_entry[*layer] = 1;

    // Draw active party member slots (Flynn + 3 demons)
    for (s32 i = 0; i < 4; ++i) {
        ui::UiSprite_DrawPanelDirect(2, 0x0E, 0x20 + i, 80 * i, 160, 1);
    }

    if (*layer > 0) {
        *layer = *layer - 1;
    }
}

// DECOMP_FUNC(0x002e2454, 764)
void GauntletAppMenu_Init() {
    GauntletAppMenuWork* work = g_GauntletAppMenuWork;
    if (work == nullptr) {
        work = reinterpret_cast<GauntletAppMenuWork*>(ui::AsdMem_Alloc(sizeof(GauntletAppMenuWork), 0x100));
        g_GauntletAppMenuWork = work;
    }

    ui::AsdMem_Zero(work, sizeof(GauntletAppMenuWork));
    work->state = 1;
}

} // namespace smt4::camp
