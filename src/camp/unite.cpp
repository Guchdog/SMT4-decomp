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

} // namespace smt4::camp
