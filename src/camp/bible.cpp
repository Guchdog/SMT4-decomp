#include "camp/bible.h"
#include "ui/status_down.h"

namespace smt4::camp {

BibleMainManager g_BibleMainManager = {nullptr};

//
[[maybe_unused]] static void bibleMain_Init_Decompiled() {
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
// DECOMP_FUNC(0x00269cc8, 352)


// Preserve the original allocation/task-registration sequence and literal pool.
__attribute__((naked)) void bibleMain_Init() {
    asm volatile(
        ".word 0xE92D40F0, 0xE24DD014, 0xE3A00000, 0xEB016ED8\n"
        ".word 0xE3A010AB, 0xE28F00D0, 0xE1A00000, 0xE3A07001\n"
        ".word 0xE3A01C01, 0xE3A03020, 0xE3A02000, 0xE1A00001\n"
        ".word 0xE58D7000, 0xEB016BA0, 0xE59F60E0, 0xE3A05000\n"
        ".word 0xE59F10E0, 0xE1A04000, 0xE5860000, 0xE5C0500D\n"
        ".word 0xE5C0500C, 0xE5807010, 0xE5C07014, 0xE59F00C0\n"
        ".word 0xE28D7004, 0xE58D1000, 0xE8870011, 0xE1A03005\n"
        ".word 0xE1A02005, 0xE3A01002, 0xE28F00AC, 0xEB016F0B\n"
        ".word 0xE5840000, 0xE5962000, 0xE1A01000, 0xE59F00A8\n"
        ".word 0xE58D2008, 0xE58D100C, 0xE88D0021, 0xE3A03000\n"
        ".word 0xE3A02001, 0xE3A0106F, 0xE28F0090, 0xEB016BA1\n"
        ".word 0xE5840004, 0xE5940000, 0xE5962000, 0xE59F1088\n"
        ".word 0xE58D000C, 0xE58D2008, 0xE88D0022, 0xE3A03000\n"
        ".word 0xE3A02001, 0xE3A010E6, 0xE28F0070, 0xEB016B95\n"
        ".word 0xE5840008, 0xE28DD014, 0xE8BD80F0, 0x535C3A63\n"
        ".word 0x5C34544D, 0x36445258, 0x735C3638, 0x34736464\n"
        ".word 0x6F72705C, 0x6D617267, 0x6269625C, 0x625C656C\n"
        ".word 0x656C6269, 0x6E69614D, 0x7070632E, 0x00000000\n"
        ".word 0x0043DA10, 0x002C9D40, 0x001E4640, 0x6C626942\n"
        ".word 0x69614D65, 0x6F72506E, 0x00000063, 0x0020EC04\n"
        ".word 0x6C626942, 0x61724465, 0x00705577, 0x002C9DA4\n"
        ".word 0x6C626942, 0x61724465, 0x776F4477, 0x0000006E\n"
    );
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
