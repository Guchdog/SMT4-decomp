#include "script/flowscript.h"
#include "camp/unite.h"
#include "ui/status_down.h"

namespace smt4::script {

NameMainManager g_NameMainManager = {nullptr, nullptr};
OnesRoomManager g_OnesRoomManager = {nullptr};

// DECOMP_FUNC(0x001d374c, 408)
void nameMain_Init(void* arg0, s32 arg1) {
    NameMainWork* work = reinterpret_cast<NameMainWork*>(ui::AsdMem_Alloc(sizeof(NameMainWork), 0x100));
    g_NameMainManager.work = work;

    if (work == nullptr) {
        return;
    }

    ui::AsdMem_Zero(work, sizeof(NameMainWork));

    // Register calculation task ("NameMainProc", priority 2)
    work->proc_task = ui::AsdTask_CreateCalc("NameMainProc", 2, 0, 0, nullptr, work, 0);

    // Register 3D stereo naming display passes (tags 0x7A, 0xD8 or 0x80, 0xDE depending on mode)
    if (arg0 != nullptr && arg1 == 1) {
        ui::AsdTask_CreateDraw("NameDrawUp", 0x80, 1, 0, nullptr, work, 0);
        ui::AsdTask_CreateDraw("NameDrawUp", 0xDE, 1, 0, nullptr, work, 0);
    } else {
        ui::AsdTask_CreateDraw("NameDrawUp", 0x7A, 1, 0, nullptr, work, 0);
        ui::AsdTask_CreateDraw("NameDrawUp", 0xD8, 1, 0, nullptr, work, 0);
    }

    // Register bottom touchscreen virtual keyboard interface (tag 0xE6)
    ui::AsdTask_CreateDraw("NameDrawDown", 0xE6, 1, 0, nullptr, work, 0);
}

// DECOMP_FUNC(0x001d38fc, 392)
void onesRoom_Init(void* arg0, s32 arg1) {
    (void)arg0; (void)arg1;
    OnesRoomWork* work = reinterpret_cast<OnesRoomWork*>(ui::AsdMem_Alloc(sizeof(OnesRoomWork), 0x100));
    g_OnesRoomManager.work = work;

    if (work == nullptr) {
        return;
    }

    ui::AsdMem_Zero(work, sizeof(OnesRoomWork));

    // Initialize button prompt HUD
    camp::ButtonHelp_Init();

    // Register barracks background & event task ("onesRoom C", priority 2)
    work->calc_task = ui::AsdTask_CreateCalc("onesRoom C", 2, 0, 0, nullptr, work, 0);
}

} // namespace smt4::script
