#include "camp/bible.h"
#include "ui/status_down.h"

namespace smt4::camp {

BibleMainManager g_BibleMainManager = {nullptr};

// DECOMP_FUNC(0x00269cc8, 352)
void bibleMain_Init() {
    BibleMainWork* work = reinterpret_cast<BibleMainWork*>(ui::AsdMem_Alloc(sizeof(BibleMainWork), 0x100));
    g_BibleMainManager.work = work;

    if (work == nullptr) {
        return;
    }

    work->flag_0c = 0;
    work->flag_0d = 0;
    work->state = 1;
    work->flag_14 = 1;

    // Register BibleMainProc calculation task (tag 2)
    work->proc_task = ui::AsdTask_CreateCalc("BibleMainProc", 2, 0, 0, nullptr, work, 0);

    // Register BibleDrawUp stereoscopic 3D compendium display pass (tag 0x6F)
    work->draw_up_task = ui::AsdTask_CreateDraw("BibleDrawUp", 0x6F, 1, 0, nullptr, work, 0);

    // Register BibleDrawDown touchscreen compendium list & summon pass (tag 0xE6)
    work->draw_down_task = ui::AsdTask_CreateDraw("BibleDrawDown", 0xE6, 1, 0, nullptr, work, 0);
}

// DECOMP_FUNC(0x003a9200, 948)
void bibleAnalyze_Init(BibleAnalyzeWork* work) {
    if (work == nullptr) {
        return;
    }
    // Compendium demon analyzer setup:
    // Unpacks demon affinities, skill heritage, macca summon cost,
    // and lore descriptions.
    work->state_flag = 0;
}

} // namespace smt4::camp
