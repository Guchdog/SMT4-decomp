#include "camp/camp_cec.h"
#include "engine/asd_symbols.h"

namespace smt4::ui {
// Shared ComWin/RunWin constructor (src/ui/window.cpp); declared directly
// rather than pulling in the whole window header.
void RunWin_Init();                                                     // 0x002027DC
} // namespace smt4::ui

namespace smt4::camp {

CecEditWork* g_CecEditWork = nullptr;       // 0x0043DAD0
CecWork* g_CecWork = nullptr;               // 0x0043DAA8
CecViewWork* g_CecViewWork = nullptr;       // 0x0043DB10
CecSettingWork* g_CecSettingWork = nullptr; // 0x0043DAF8

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

extern "C" {
    // AsdMemory (c:\SMT4\XRD686\AsdSDK\Source\Sys\Mem\AsdMemory.cpp)
    void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);         // 0x002C4B84
    void  AsdMem_Zero(void* ptr, u32 size);                                 // 0x002C4B30

    // AsdProcess task factories beyond the shared declarations in
    // engine/asd_symbols.h (0x002C5978 / 0x002C4C00).
    void* AsdWork_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 flag); // 0x002C34A4
    void  AsdWork_Zero(void* ptr, u32 size);                                // 0x002C3B48

    // nn::os thread/heap helpers -- same spellings as src/engine/asd_file.cpp.
    void  AsdHeap_Init(void* heap, void* buffer, u32 size);                 // 0x002BCF34
    s32   AsdThread_Create(void* out, const void* desc, void (*entry)(void*),
                           void* context, u32 stack_size, u32 priority,
                           s32 processor);                                  // 0x002BCE50
    void  AsdKernel_AbortOnFailure(s32 result);                             // 0x002C5468

    // Script/resource loading
    void  ScriptVm_LoadTable(const char* name, void* out, u32 value);       // 0x00297704

    // AsdText (c:\SMT4\XRD686\AsdSDK\Source\Gfx\Text\AsdText.cpp)
    void* AsdText_CreateDefault(u32 arg0);                                  // 0x002BDA1C
    void  AsdText_SetAlpha(void* text_handle, u32 alpha);                   // 0x002BDA10
    void  AsdText_SetColorAndScale(void* text_handle, u32 a1, u32 rgba,
                                   f32 scale);                              // 0x002BDA00

    void  Sound_PlaySE(s32 se_id);                                          // 0x002B8B78

    // CampCec shared accessors (CampCec.cpp / CampCecDraw.cpp)
    void* CampCec_GetPanelBase();                                           // 0x0024ABFC
    void* CampCec_GetMenuRoot();                                            // 0x0025487C
    void* CampCec_GetFieldMenu();                                           // 0x002B66EC
    void  CampCecFieldMenu_Init(void* menu, void* source);                  // 0x0026F084
    void  CampCecFieldMenu_Reset(void* menu);                               // 0x0026F018

    void* CampCecDraw_CreateTextBlock();                                    // 0x00309DB8
    void* CampCecDraw_CreateListBlock();                                    // 0x0031B9AC
    void  CampCecDraw_SetTextRow(void* block, const CecMessageRow* row);    // 0x0026F174
    void  CampCecDraw_SetEntryText(void* block, const CecMessageRow* row,
                                   u32 msg);                                // 0x0026F474
    int   CampCecDraw_CreateSprite(void* block);                            // 0x0026F9F4
    void  CampCecDraw_FinishSprite(void* block, u32 mode);                  // 0x0026FA70
    void  CampCecRow_ApplyTemplate(CecMessageRow* row, void* scratch);      // 0x0030A818
    CecMessageRow* CampCecMessage_GetRow(u32 index);                        // 0x0026F25C

    // CEC save-block accessors
    void* CampCec_GetSaveHeader();                                          // 0x002A8A08
    u8*   CampCec_GetSaveEntry(u32 index);                                  // 0x002A89E4
    u32   CampCec_EntryTestFlag(const u8* entry, u32 bit);                  // 0x0029EE4C

    // CampCec boot helpers
    u32   CampCec_IsModeOne();                                              // 0x0035A238
    u32   CampCec_IsModeZero();                                             // 0x0035A1A0
    void  CampCec_SetupInput(u32 enable);                                   // 0x00257BF0
    void  Status_InitEnvironment(void* env);                                // 0x002D72C4
    void  UiInput_SetMode(u32 mode);                                        // 0x0026B7EC
    void  UiInput_SetModeB(u32 mode);                                       // 0x002594CC
    void  CampCec_ThreadEntry(void* arg);                                   // 0x001EC5F4
}

// ---------------------------------------------------------------------------
// CampCecEdit.cpp (0x002D678C), 1,356 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002d678c, 1356)
void CampCecEdit_func_002d678c(void* arg) {
    CecEditWork* work = g_CecEditWork;
    if (work == nullptr) {
        // 0x002D67AC..0x002D67D0: AsdMem_Alloc(0x100,0x100,0,0x160,1).
        work = static_cast<CecEditWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(CecEditWork), 1));
        g_CecEditWork = work;
    }
    AsdMem_Zero(work, sizeof(CecEditWork));                 // 0x002D67DC

    // 0x002D67E0..0x002D6808: calc task, callback 0x001C0DFC.
    work->calc_task = AsdTask_CreateCalc("CampCecEdit Calc", 1, 0, 0,
                                         CampCecEdit_Calc, 0, 0);
    void* parent = work->calc_task;

    // 0x002D6810..0x002D68C0: five draw tasks.  The constructors return the
    // new task, but the listing never stores it: the results stay in r0 and
    // are overwritten by the next factory call.
    AsdTask_CreateDraw("CampCecEdit DrawUpLeft_b", 0x65, 0, 0,
                       CampCecEdit_DrawBase, 0, 0, parent);
    AsdTask_CreateDraw("CampCecEdit DrawUpRight_b", 0xCC, 0, 0,
                       CampCecEdit_DrawBase, 0, 0, parent);
    AsdTask_CreateDraw("CampCecEdit DrawUpLeft", 0x7D, 0, 0,
                       CampCecEdit_DrawUp, 0, 0, parent);
    AsdTask_CreateDraw("CampCecEdit DrawUpRight", 0xDB, 0, 0,
                       CampCecEdit_DrawUp, 0, 0, parent);
    AsdTask_CreateDraw("CampCecEdit DrawDown", 0xE6, 0, 0,
                       CampCecEdit_DrawDown, 0, 0, parent);

    // 0x002D68C4..0x002D6920: `mvn r0,#0` seeds every "-1" slot; the pairs
    // are written with `stm r1,{r0,r8}` (r8 = 0) at +0x100/+0x108.
    work->field_100 = -1;
    work->field_104 = 0;
    work->field_108 = -1;
    work->field_10c = 0;
    work->field_110 = -1;
    work->field_114 = -1;
    work->field_118 = 0;
    work->flag_128 = 1;                                     // `strb r6` (r6 = 1)
    work->arg_129 = static_cast<u8>(reinterpret_cast<std::uintptr_t>(arg));
    work->field_12a = 0;                                    // `strb r8`
    work->field_12c = 0;
    work->field_134 = 0;
    work->field_138 = 0x10;                                 // `stm r3,{r1,r8}`
    work->field_13c = 0;
    work->flag_141 = 0;
    work->field_144 = -0x38;                                // `mvn r2,#0x37`
    work->field_148 = 0;
    work->field_150 = 0;
    work->field_154 = 0;
    work->field_158 = 0;
    work->field_15c = -1;

    // 0x002D6924..0x002D697C: state-handler table at +0xB4.  +0xB4 is filled
    // first, then +0xB8.. and finally +0xC0..+0xD4 (the compiler scheduled
    // the stores); the values are the literal-pool words 0x002D6C40..0x002D6C60.
    work->handlers[0] = 0x002E16D0;
    work->handlers[2] = 0x002D6CD8;
    work->handlers[1] = 0x00220C5C;
    work->handlers[3] = 0x002FC864;
    work->handlers[4] = 0x002FC728;
    work->handlers[5] = 0x002EC4BC;
    work->handlers[7] = 0x00321CE0;
    work->handlers[8] = 0x00220C3C;
    work->handlers[6] = 0x00317428;

    // 0x002D6984..0x002D69A8: small integer table (+0xD8..+0xFC).  Entry 3
    // and entry 9 are swapped (3 -> 9, 9 -> 3).
    work->field_d8 = 0;
    work->field_dc = 1;
    work->field_e0 = 2;
    work->field_e4 = 9;
    work->field_e8 = 4;
    work->field_ec = 5;
    work->field_f0 = 6;
    work->field_f4 = 7;
    work->field_f8 = 8;
    work->field_fc = 3;

    // 0x002D69AC..0x002D69F0: two camp accessors, the two draw objects and
    // their initial row bindings.  `+0xAC` is still zero here because its
    // script table is loaded later (0x002D6A14).
    work->panel_base = CampCec_GetPanelBase();              // 0x0024ABFC
    work->menu_root = CampCec_GetMenuRoot();                // 0x0025487C
    work->text_block = CampCecDraw_CreateTextBlock();       // 0x00309DB8
    CampCecDraw_SetTextRow(work->text_block,
                           static_cast<const CecMessageRow*>(work->menu_root));
    work->list_block = CampCecDraw_CreateListBlock();       // 0x0031B9AC
    CampCecDraw_SetEntryText(work->list_block,
                             static_cast<const CecMessageRow*>(work->menu_root),
                             work->one_msg_mbm);

    // 0x002D69F4..0x002D6A1C: three table loads into +0xA4/+0xA8/+0xAC.
    ScriptVm_LoadTable("camp/CecEdit_scr.bf", &work->script_bf, 0);
    ScriptVm_LoadTable("camp/CecEdit_msg.mbm", &work->msg_mbm, 0);
    ScriptVm_LoadTable("camp/CecEdit_one_msg.mbm", &work->one_msg_mbm, 0);

    // 0x002D6A20..0x002D6A54: text object, full alpha, 0x64 grey colour and
    // a zero scale, then SE 0xB1.
    work->text_handle = AsdText_CreateDefault(0);
    AsdText_SetAlpha(work->text_handle, 0xFF);
    AsdText_SetColorAndScale(work->text_handle, 0, 0x646464FF, 0.0f);
    Sound_PlaySE(0xB1);

    // 0x002D6A60: three 0x14-byte rows at +0x3C with default row 0x14A.
    for (s32 i = 0; i < 3; ++i) {
        CecRowView& row = work->rows[i];
        AsdWork_Zero(&row, sizeof(row));
        row.field_04 = 0x14A;                               // `str r7,[r6,#0x40]`
    }

    // 0x002D6A88: two 0x14-byte rows at +0x14; no default row.
    for (s32 i = 0; i < 2; ++i) {
        CecRowView& row = work->grid[i];
        AsdWork_Zero(&row, sizeof(row));
    }

    // 0x002D6AA8..0x002D6AB4: one 0x14-byte row at +0x8C, default row 0x14A
    // (`str r7,[r4,#0x90]`).
    AsdWork_Zero(&work->single, sizeof(work->single));
    work->single.field_04 = 0x14A;

    // 0x002D6ABC..0x002D6AF8: bind the field menu widget returned by
    // 0x002B66EC to the CampCec panel base, reset it, then fetch the CEC
    // save header.
    void* field_menu = CampCec_GetFieldMenu();
    CampCecFieldMenu_Init(CampCec_GetPanelBase(), field_menu);
    CampCecFieldMenu_Reset(CampCec_GetPanelBase());
    const u8* save_header = static_cast<const u8*>(CampCec_GetSaveHeader());

    // 0x002D6B00..0x002D6CD0: count the available CEC entries.  The signed
    // byte array lives at save_header + 0x90F0 (`add r6,r0,#0x9000` plus
    // `ldrsb r0,[r6,#0xf0]`, 0x002D6B0C/0x002D6B10).  An entry counts when
    // source byte >= 0 and neither flag bit 0xA nor bit 1 is set; the flags
    // are read from the halfword at entry + 0x44 (0x0029EE4C).
    work->available_count = 0;
    for (s32 i = 0; i < 0x18; ++i) {
        const s8 source = reinterpret_cast<const s8*>(save_header)[0x90F0 + i];
        if (source < 0) {
            continue;
        }

        const u8* entry = CampCec_GetSaveEntry(static_cast<u32>(source));
        if (CampCec_EntryTestFlag(entry, 0xA) != 0) {
            continue;
        }
        if (CampCec_EntryTestFlag(entry, 1) != 0) {
            continue;
        }
        ++work->available_count;                            // 0x002D6CC0
    }
}

// ---------------------------------------------------------------------------
// CampCec.cpp (0x001FFAF4), 1,068 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001ffaf4, 1068)
void CampCec_func_001ffaf4(void* arg) {
    (void)arg;
    CecWork* work = g_CecWork;
    if (work == nullptr) {
        // 0x001FFB04/0x001FFB24: size 0xD7C; 0x001FFB30..0x001FFB38 store it.
        work = static_cast<CecWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(CecWork), 1));
        g_CecWork = work;
    }
    AsdMem_Zero(work, sizeof(CecWork));                     // 0x001FFB44

    // 0x001FFB48..0x001FFBAC: calc task plus two draw tasks.
    work->calc_task = AsdTask_CreateCalc("CampCec Calc", 1, 0, 0,
                                         CampCec_Calc, 0, 0);
    AsdTask_CreateDraw("CampCec DrawUpLeft", 0x7D, 0, 0, CampCec_DrawUp, 0, 0,
                       work->calc_task);
    AsdTask_CreateDraw("CampCec DrawUpRight", 0xDB, 0, 0, CampCec_DrawUp, 0, 0,
                       work->calc_task);

    // 0x001FFBB8..0x001FFBD0: the first pair is at work + 0xC00 + 0x124 =
    // +0xD24 (not +0xC24); the second pair is at +0xD30, with the lone -1 at
    // +0xD2C (`stm r2,{r1,r6}`, r1 = -1, r6 = 0).
    work->field_d24 = -1;
    work->state_d28 = 0;
    work->field_d2c = -1;
    work->field_d30 = -1;
    work->field_d34 = 0;

    // 0x001FFBD4..0x001FFC44: state-handler table.  +0x30 and +0x34 share
    // the same target (0x001EBD24); +0x40 is not written by this function.
    work->handlers[0] = 0x002112C4;
    work->handlers[1] = 0x002EC530;
    work->handlers[2] = 0x002CCACC;
    work->handlers[3] = 0x001EBDF0;
    work->handlers[4] = 0x001DBE2C;
    work->handlers[5] = 0x00210FB0;
    work->handlers[6] = 0x002E1824;
    work->handlers[7] = 0x001DBDB0;
    work->handlers[8] = 0x001DC500;
    work->handlers[9] = 0x00211400;
    work->handlers[10] = 0x001EBD24;
    work->handlers[11] = 0x001EBD24;
    work->handlers[12] = 0x00310658;
    work->handlers[13] = 0x002ECE08;
    work->field_44 = 0x00220EAC;

    // 0x001FFC48..0x001FFC68: boot mode selection.  0x0035A238 -> 1;
    // otherwise 0x0035A1A0 returning 0 selects 2, non-zero stays 0.
    work->mode = 0;
    if (CampCec_IsModeOne() != 0) {
        work->mode = 1;
    } else if (CampCec_IsModeZero() == 0) {
        work->mode = 2;
    }

    // 0x001FFC70/0x001FFC74: clear the "mode 0 started" byte before the
    // branch so both paths observe it.
    work->flag_d64 = 0;
    if (work->mode != 0) {
        // 0x001FFC7C..0x001FFCAC: script/message tables and state 0x0D.
        ScriptVm_LoadTable("camp/CecMain_scr.bf", &work->script_bf, 0);
        ScriptVm_LoadTable("camp/CecMain_msg.mbm", &work->msg_mbm, 0);
        work->state_d28 = 0x0D;
        return;
    }

    // 0x001FFCB4..0x001FFD34: interactive CEC boot path.
    Sound_PlaySE(0x03);
    work->flag_d61 = 0;
    work->flag_d62 = 1;
    work->flag_d63 = 0;
    Sound_PlaySE(0xB9);
    CampCec_SetupInput(0);                                  // 0x00257BF0
    Status_InitEnvironment(reinterpret_cast<u8*>(g_CecWork) + 0xA0); // 0x002D72C4
    Sound_SetSequenceState(0);                              // 0x001A7F30
    Sound_RequestBgm(0x01000062, 0, 0x3C);            // 0x002A0640
    ui::RunWin_Init();                                      // 0x002027DC
    RunWin_OpenDefault();                                 // 0x0032FEF4
    UiInput_SetMode(2);                                     // 0x0026B7EC
    UiInput_SetModeB(2);                                    // 0x002594CC
    work->flag_d65 = 0;
    work->field_d68 = 0;

    // 0x001FFD38..0x001FFD64: a 0x1000-byte work buffer
    // (AsdWork_Alloc(0x100,0x100,0,0x1000,0x1000,1)).
    work->thread_buffer = AsdWork_Alloc(0x100, 0x100, 0, 0x1000, 0x1000, 1);

    // 0x001FFD68..0x001FFDA8: 0x18-byte heap block, cleared by hand, then
    // AsdHeap_Init(heap, thread_buffer, 0x1000).
    work->heap = engine::AsdMemory_func_002c23f8(0x18);
    if (work->heap != nullptr) {
        auto* words = static_cast<u32*>(work->heap);
        words[0] = 0;
        words[1] = 0;
        words[2] = 0;
        words[3] = 0;
        static_cast<u8*>(work->heap)[0x10] = 0;             // `strb r6,[r0,#0x10]`
    }
    AsdHeap_Init(work->heap, work->thread_buffer, 0x1000);

    // 0x001FFDAC..0x001FFE24: spawn the CEC worker thread.  The descriptor is
    // the four-word block at sp+0x10; the stack size is heap[+0x08] plus
    // heap[+0x0C]; priority 0x11, processor -1.  As in src/nn/mobiclip.cpp the
    // context argument is the address of a local holding the work pointer.
    struct ThreadDesc {
        u32 a;
        u32 b;
        u32 c;
        u32 d;
    } desc = {
        4,
        static_cast<u32>(0x003F70E0),
        static_cast<u32>(0x003F721C),
        static_cast<u32>(0x003F71A0),
    };

    const u32* heap_words = static_cast<const u32*>(work->heap);
    const u32 stack_size = heap_words[2] + heap_words[3];   // +0x08 + +0x0C
    void* thread_arg = work;

    const s32 result = AsdThread_Create(&work->thread_result, &desc,
                                        CampCec_ThreadEntry, &thread_arg,
                                        stack_size, 0x11, -1);
    if ((result & 0x7E00000) != 0x600000 && result < 0) {
        AsdKernel_AbortOnFailure(result);                   // 0x001FFE18
    }
}

// ---------------------------------------------------------------------------
// CampCecView.cpp (0x002D7410), 1,012 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002d7410, 1012)
void CampCecView_func_002d7410(void* arg) {
    (void)arg;
    CecViewWork* work = g_CecViewWork;
    if (work == nullptr) {
        // 0x002D7428..0x002D7450: AsdMem_Alloc(0x100,0x100,0,0x16C,1).
        work = static_cast<CecViewWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(CecViewWork), 1));
        g_CecViewWork = work;
    }
    AsdMem_Zero(work, sizeof(CecViewWork));                 // 0x002D745C

    // 0x002D7460..0x002D7550: calc task and five draw tasks.
    work->calc_task = AsdTask_CreateCalc("CampCecView Calc", 1, 0, 0,
                                         CampCecView_Calc, 0, 0);
    AsdTask_CreateDraw("CampCecView DrawUpLeft_b", 0x65, 0, 0,
                       CampCecView_DrawBase, 0, 0, work->calc_task);
    AsdTask_CreateDraw("CampCecView DrawUpRight_b", 0xCC, 0, 0,
                       CampCecView_DrawBase, 0, 0, work->calc_task);
    AsdTask_CreateDraw("CampCecView DrawUpLeft", 0x81, 0, 0,
                       CampCecView_DrawUp, 0, 0, work->calc_task);
    AsdTask_CreateDraw("CampCecView DrawUpRight", 0xDF, 0, 0,
                       CampCecView_DrawUp, 0, 0, work->calc_task);
    AsdTask_CreateDraw("CampCecView DrawDown", 0xE6, 0, 0,
                       CampCecView_DrawDown, 0, 0, work->calc_task);

    // 0x002D7554..0x002D7570: cleared counters/flags.
    work->field_13c = 0;
    work->field_140 = 0;
    work->field_144 = 0;
    work->visible_count = 0;
    work->field_150 = 0;
    work->flag_164 = 0;
    work->flag_165 = 0;
    work->field_168 = 0;

    // 0x002D7574..0x002D759C: walk the twelve CEC message rows and count the
    // ones whose +0x48 halfword is non-zero (0x0026F25C clamps index >= 0xC
    // to a null row).
    for (s32 i = 0; i < 0xC; ++i) {
        const CecMessageRow* row = CampCecMessage_GetRow(static_cast<u32>(i));
        if (row->field_48 != 0) {
            ++work->visible_count;
        }
    }

    // 0x002D75A0..0x002D75CC: message table and the two camp accessors.
    ScriptVm_LoadTable("camp/CecEdit_one_msg.mbm", &work->one_msg_mbm, 0);
    work->panel_base = CampCec_GetPanelBase();              // 0x0024ABFC
    work->current_row = CampCecMessage_GetRow(static_cast<u32>(work->field_13c));

    // 0x002D75D0..0x002D75E8: three text blocks at +0x12C.
    for (s32 i = 0; i < 3; ++i) {
        work->text_blocks[i] = CampCecDraw_CreateTextBlock(); // 0x00309DB8
    }
    work->list_block = CampCecDraw_CreateListBlock();       // 0x0031B9AC

    // 0x002D75F4..0x002D762C: bind rows [field_140 + i] to text block i when
    // the row's +0x48 halfword is set.
    for (s32 i = 0; i < 3; ++i) {
        const CecMessageRow* row =
            CampCecMessage_GetRow(work->field_140 + static_cast<u32>(i));
        if (row->field_48 != 0) {
            CampCecDraw_SetTextRow(work->text_blocks[i], row);
        }
    }

    // 0x002D7630..0x002D764C: refresh the current row and bind the list block
    // to it plus the one-message table.
    work->current_row = CampCecMessage_GetRow(static_cast<u32>(work->field_13c));
    CampCecDraw_SetEntryText(work->list_block,
                             static_cast<const CecMessageRow*>(work->current_row),
                             work->one_msg_mbm);

    // 0x002D7650..0x002D769C: clear the current row's display ranges and, if
    // the panel base owns a live widget, install the zeroed template, reset
    // the widget and remember the current row.
    u8 row_template[0x8C];
    CampCecRow_ApplyTemplate(
        static_cast<CecMessageRow*>(work->current_row), row_template);
    if (CampCecDraw_CreateSprite(work->panel_base) != 0) {
        CampCecFieldMenu_Init(work->panel_base, row_template);
        CampCecFieldMenu_Reset(work->panel_base);
        CampCecDraw_FinishSprite(work->panel_base, 0);
        work->field_14c = static_cast<u32>(work->field_13c);
    }

    // 0x002D76A0..0x002D76EC: two clear rows at +0xA0 and five at +0xC8;
    // every +0xC8 row receives default row 0x14A at record +0x04.
    for (s32 i = 0; i < 2; ++i) {
        AsdWork_Zero(&work->grid_a[i], sizeof(CecRowView));
    }
    for (s32 i = 0; i < 5; ++i) {
        CecRowView& row = work->grid_b[i];
        AsdWork_Zero(&row, sizeof(row));
        row.field_04 = 0x14A;                               // `str r7,[r6,#0xcc]`
    }

    // 0x002D76F0..0x002D76FC: epilogue tail-calls SE 0xB2.
    Sound_PlaySE(0xB2);
}

// ---------------------------------------------------------------------------
// CampCecSetting.cpp (0x002F5BC0), 512 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002f5bc0, 512)
void CampCecSetting_func_002f5bc0(void* arg) {
    (void)arg;
    CecSettingWork* work = g_CecSettingWork;
    if (work == nullptr) {
        // 0x002F5BDC..0x002F5C00: AsdMem_Alloc(0x100,0x100,0,0x44,1).
        work = static_cast<CecSettingWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(CecSettingWork), 1));
        g_CecSettingWork = work;
    }
    AsdMem_Zero(work, sizeof(CecSettingWork));              // 0x002F5C0C

    // 0x002F5C10..0x002F5C84: calc task and two draw tasks.
    work->calc_task = AsdTask_CreateCalc("CampCecSetting Calc", 1, 0, 0,
                                         CampCecSetting_Calc, 0, 0);
    AsdTask_CreateDraw("CampCecSetting DrawUpLeft", 0x81, 0, 0,
                       CampCecSetting_DrawUp, 0, 0, work->calc_task);
    AsdTask_CreateDraw("CampCecSetting DrawUpRight", 0xDF, 0, 0,
                       CampCecSetting_DrawUp, 0, 0, work->calc_task);

    // 0x002F5C88..0x002F5CA4: tables.
    ScriptVm_LoadTable("camp/CecSetting_scr.bf", &work->script_bf, 0);
    ScriptVm_LoadTable("camp/CecSetting_msg.mbm", &work->msg_mbm, 0);

    // 0x002F5CA8..0x002F5CE8: the visible option table.  The five words at
    // +0x18 are written by one `stm lr,{r0,r1,r2,r3,ip}` (2,3,4,5,6); the
    // three at +0x2C by `stm r4,{r7,r8,sb}` (10,7,11).
    work->field_38 = 0;
    work->field_3c = 2;                                     // `strb r0,#0x3c`
    work->table_a[0] = 2;
    work->table_a[1] = 3;
    work->table_a[2] = 4;
    work->table_a[3] = 5;
    work->table_a[4] = 6;
    work->field_10 = 0;                                     // `stm r1,{r5,r6}`
    work->field_14 = 1;
    work->field_2c = 10;
    work->field_30 = 7;
    work->field_34 = 11;

    // 0x002F5CEC..0x002F5CF4: epilogue tail-calls SE 0xE2.
    Sound_PlaySE(0xE2);
}

} // namespace smt4::camp
