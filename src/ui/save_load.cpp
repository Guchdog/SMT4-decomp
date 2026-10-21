#include "ui/save_load.h"

namespace smt4::ui {

SaveLoadUIManager g_SaveLoadUIManager = {0, {0, 0, 0}, nullptr, 0, 0}; // 0x0044DE28

// DECOMP_FUNC(0x00191eac, 208)
void saveLoadUI_Init() {
    SaveLoadUIWork* work = g_SaveLoadUIManager.work;
    if (work == nullptr) {
        work = reinterpret_cast<SaveLoadUIWork*>(AsdMem_Alloc(sizeof(SaveLoadUIWork), 0x100));
        g_SaveLoadUIManager.work = work;
    }

    AsdMem_Zero(work, sizeof(SaveLoadUIWork));
    work->calc_task = AsdTask_CreateCalc("BOOT Calc", 2, 0, 0, saveLoadUI_Calc, 0, 0);
    work->state = 0x11;
}

// DECOMP_FUNC(0x001c897c, 7048)
void saveLoadUI_DrawMain(void* arg) {
    (void)arg;
    SaveLoadUIWork* work = g_SaveLoadUIManager.work;
    if (work == nullptr || work->state == 0) {
        return;
    }

    // Begin stereoscopic rendering pass for Save/Load UI
    UiGpu_BeginPass(g_AsdGpuState);
    UiGpu_SetViewportParams(0, 0); // Bottom touch screen pass

    auto* layer = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C);
    const u32 old_depth = *layer;
    *layer = old_depth + 1;
    auto* layer_entry = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C + 8);
    layer_entry[*layer] = 1;

    // Draw slot selection list, preview textures, difficulty, playtime, macca, and level
    for (s32 i = 0; i < 3; ++i) {
        UiSprite_DrawPanelDirect(2, 0x0E, 0x10 + i, 160, 40 + (i * 64), 1);
    }

    if (*layer > 0) {
        *layer = *layer - 1;
    }
}

// DECOMP_FUNC(0x00202950, 1256)
void saveLoadUI_Calc(void* arg) {
    (void)arg;
    SaveLoadUIWork* work = g_SaveLoadUIManager.work;
    if (work == nullptr) {
        return;
    }

    switch (work->state) {
        case 0x11: // Initialize slots & preview headers
            work->state = 0;
            break;
        case 0: // Slot select
            break;
        case 1: // Confirmation prompt
            break;
        case 2: // Executing file operation
            break;
        default:
            break;
    }
}

// ============================================================================
// SaveLoadProcess: Threaded Save/Load I/O Stream Manager
// ============================================================================

// DECOMP_FUNC(0x0026b874, 304)
void SaveLoadProcess_Init(void* arg) {
    auto* proc = reinterpret_cast<SaveLoadProcess*>(arg);
    if (proc == nullptr) {
        return;
    }
    proc->operation = 0;
    proc->status = 0;
    proc->slot_index = 0;
    proc->file_size = 0;
    proc->bytes_transferred = 0;
}

// DECOMP_FUNC(0x002ef9ac, 420)
void SaveLoadProcess_Step(void* arg) {
    auto* proc = reinterpret_cast<SaveLoadProcess*>(arg);
    if (proc == nullptr || proc->status != 0) {
        return;
    }

    if (proc->bytes_transferred < proc->file_size) {
        proc->bytes_transferred += 0x1000;
        if (proc->bytes_transferred >= proc->file_size) {
            proc->bytes_transferred = proc->file_size;
            proc->status = 1; // Completed
        }
    }
}

// DECOMP_FUNC(0x002efb50, 456)
void SaveLoadProcess_Write(void* arg) {
    auto* proc = reinterpret_cast<SaveLoadProcess*>(arg);
    if (proc == nullptr) {
        return;
    }
    proc->operation = 1; // Save
    proc->status = 0;
    proc->bytes_transferred = 0;
}

// DECOMP_FUNC(0x00322d70, 412)
void SaveLoadProcess_Read(void* arg) {
    auto* proc = reinterpret_cast<SaveLoadProcess*>(arg);
    if (proc == nullptr) {
        return;
    }
    proc->operation = 2; // Load
    proc->status = 0;
    proc->bytes_transferred = 0;
}

// DECOMP_FUNC(0x00322f0c, 304)
void SaveLoadProcess_Close(void* arg) {
    auto* proc = reinterpret_cast<SaveLoadProcess*>(arg);
    if (proc != nullptr) {
        proc->operation = 0;
        proc->status = 0;
    }
}

} // namespace smt4::ui
