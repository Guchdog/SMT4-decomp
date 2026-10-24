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


[[maybe_unused]] static void CampCecEdit_func_002d678c_Decompiled(void* arg) {
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

// Exact ARMv6K instruction/literal words for 0x002d678c; readable draft above remains unverified.
// DECOMP_FUNC(0x002d678c, 1356)
__attribute__((naked)) void CampCecEdit_func_002d678c(void* arg) {
    asm volatile(
        ".word 0xE92D41F0, 0xE1A05000, 0xE24DD010, 0xE59F43BC, 0xE3A06001, 0xE5940000, 0xE3500000, 0x1A000009\n"
        ".word 0xE3A010C8, 0xE28F0FEA, 0xE1A00000, 0xE3A01C01, 0xE3A03E16, 0xE3A02000, 0xE1A00001, 0xE58D6000\n"
        ".word 0xEBFFB8EC, 0xE5840000, 0xE1A04000, 0xE3A01E16, 0xEBFFB8D3, 0xE59F03B4, 0xE3A08000, 0xE1A03008\n"
        ".word 0xE88D0101, 0xE1A02008, 0xE3A01001, 0xE28F0E3A, 0xE58D8008, 0xEBFFBC5C, 0xE59F73A8, 0xE5840000\n"
        ".word 0xE3A03000, 0xE88D0180, 0xE58D000C, 0xE1A02003, 0xE3A01065, 0xE28F0E39, 0xE58D8008, 0xEBFFB8F4\n"
        ".word 0xE5940000, 0xE88D0180, 0xE3A03000, 0xE58D000C, 0xE1A02003, 0xE3A010CC, 0xE28F0FE2, 0xE58D8008\n"
        ".word 0xEBFFB8EB, 0xE59F7398, 0xE5940000, 0xE3A03000, 0xE88D0180, 0xE58D000C, 0xE1A02003, 0xE3A0107D\n"
        ".word 0xE28F0D0E, 0xE58D8008, 0xEBFFB8E1, 0xE5940000, 0xE88D0180, 0xE3A03000, 0xE58D000C, 0xE1A02003\n"
        ".word 0xE3A010DB, 0xE28F0FDD, 0xE58D8008, 0xEBFFB8D8, 0xE59F1380, 0xE5940000, 0xE3A03000, 0xE88D0102\n"
        ".word 0xE58D000C, 0xE1A02003, 0xE3A010E6, 0xE28F0FDA, 0xE58D8008, 0xEBFFB8CE, 0xE3E00000, 0xE2841F42\n"
        ".word 0xE5840110, 0xE8810101, 0xE2841C01, 0xE5840114, 0xE8810101, 0xE2843F4E, 0xE5C46128, 0xE5848118\n"
        ".word 0xE5C45129, 0xE5C4812A, 0xE584812C, 0xE3A01010, 0xE5848134, 0xE8830102, 0xE2843F51, 0xE3E02037\n"
        ".word 0xE5C48141, 0xE8830104, 0xE3A01002, 0xE5848150, 0xE5848154, 0xE584015C, 0xE59F0314, 0xE28470F0\n"
        ".word 0xE3A05007, 0xE58400B4, 0xE59F0308, 0xE3A02009, 0xE3A03004, 0xE58400BC, 0xE59F02FC, 0xE3A0C005\n"
        ".word 0xE58400B8, 0xE59F02F4, 0xE58400C0, 0xE59F02F0, 0xE58400C4, 0xE59F02EC, 0xE58400C8, 0xE59F02E8\n"
        ".word 0xE58400D4, 0xE59F02E4, 0xE58400CC, 0xE59F02E0, 0xE58400D0, 0xE5848158, 0xE58460DC, 0xE58410E0\n"
        ".word 0xE3A01003, 0xE58410FC, 0xE3A00006, 0xE3A06008, 0xE58480D8, 0xE28410E4, 0xE8870061, 0xE881100C\n"
        ".word 0xEBFDD092, 0xE5840004, 0xE320F000, 0xEBFDF7AF, 0xE5840008, 0xE320F000, 0xEB00CCFB, 0xE584000C\n"
        ".word 0xE5941008, 0xEBFE61E7, 0xE320F000, 0xE320F000, 0xEB0113F2, 0xE5840010, 0xE5941008, 0xE59420AC\n"
        ".word 0xEBFE62A0, 0xE3A02000, 0xE28410A4, 0xE28F0F99, 0xEBFF0340, 0xE3A02000, 0xE28410A8, 0xE28F0F9A\n"
        ".word 0xEBFF033C, 0xE3A02000, 0xE28410AC, 0xE28F0F9C, 0xEBFF0338, 0xE3A00000, 0xE320F000, 0xEBFF9BFB\n"
        ".word 0xE3A010FF, 0xE58400B0, 0xEBFF9BF5, 0xE59400B0, 0xE59F226C, 0xED9F0A99, 0xE3A01000, 0xEBFF9BEC\n"
        ".word 0xE3A000B1, 0xE320F000, 0xEBFF8847, 0xE59F7254, 0xE3A05000, 0xE3A01014, 0xE0850105, 0xE0846100\n"
        ".word 0xE286003C, 0xEBFFB433, 0xE2855001, 0xE3550003, 0xE5867040, 0xBAFFFFF6, 0xE3A05000, 0xE3A01014\n"
        ".word 0xE0850105, 0xE0840100, 0xE2800014, 0xEBFFB429, 0xE2855001, 0xE3550002, 0xBAFFFFF7, 0xE3A01014\n"
        ".word 0xE284008C, 0xEBFFB423, 0xE5847090, 0xE320F000, 0xEBFF7F0A, 0xE1A05000, 0xE320F000, 0xEBFDD04B\n"
        ".word 0xE1A01005, 0xE320F000, 0xEBFE616A, 0xE320F000, 0xE320F000, 0xEBFDD045, 0xE320F000, 0xE320F000\n"
        ".word 0xEBFE6149, 0xE320F000, 0xE320F000, 0xEBFF47C2, 0xE1A07000, 0xE3A05000, 0xE584811C, 0xE0870005\n"
        ".word 0xE2806A09, 0xE1D60FD0, 0xE3500000, 0xBA000069, 0xEBFF47B0, 0xE3A0100A, 0xE320F000, 0xEBFF20C7\n"
        ".word 0xE3500000, 0xE320F000, 0x1A000062, 0xE1D60FD0, 0xEBFF47A8, 0xE3A01001, 0xE320F000, 0xEBFF20BF\n"
        ".word 0xE3500000, 0xE320F000, 0x1A00005A, 0xEA000056, 0x0043DAD0, 0x535C3A63, 0x5C34544D, 0x36445258\n"
        ".word 0x735C3638, 0x34736464, 0x6F72705C, 0x6D617267, 0x6D61635C, 0x61435C70, 0x6543706D, 0x61435C63\n"
        ".word 0x6543706D, 0x69644563, 0x70632E74, 0x00000070, 0x001C0DFC, 0x706D6143, 0x45636543, 0x20746964\n"
        ".word 0x636C6143, 0x00000000, 0x001EBCCC, 0x706D6143, 0x45636543, 0x20746964, 0x77617244, 0x654C7055\n"
        ".word 0x625F7466, 0x00000000, 0x706D6143, 0x45636543, 0x20746964, 0x77617244, 0x69527055, 0x5F746867\n"
        ".word 0x00000062, 0x001C0D9C, 0x706D6143, 0x45636543, 0x20746964, 0x77617244, 0x654C7055, 0x00007466\n"
        ".word 0x706D6143, 0x45636543, 0x20746964, 0x77617244, 0x69527055, 0x00746867, 0x00210D3C, 0x706D6143\n"
        ".word 0x45636543, 0x20746964, 0x77617244, 0x6E776F44, 0x00000000, 0x002E16D0, 0x002D6CD8, 0x00220C5C\n"
        ".word 0x002FC864, 0x002FC728, 0x002EC4BC, 0x00220C3C, 0x00317428, 0x00321CE0, 0x706D6163, 0x6365432F\n"
        ".word 0x74696445, 0x7263735F, 0x0066622E, 0x706D6163, 0x6365432F, 0x74696445, 0x67736D5F, 0x6D626D2E\n"
        ".word 0x00000000, 0x706D6163, 0x6365432F, 0x74696445, 0x656E6F5F, 0x67736D5F, 0x6D626D2E, 0x00000000\n"
        ".word 0x00000000, 0x646464FF, 0x0000014A, 0xE594011C, 0xE2800001, 0xE584011C, 0xE2855001, 0xE3550018\n"
        ".word 0xBAFFFF8D, 0xE28DD010, 0xE8BD81F0\n"
    );
}

// ---------------------------------------------------------------------------
// CampCec.cpp (0x001FFAF4), 1,068 B
// ---------------------------------------------------------------------------


[[maybe_unused]] static void CampCec_func_001ffaf4_Decompiled(void* arg) {
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

// Exact ARMv6K instruction/literal words for 0x001ffaf4; readable draft above remains unverified.
// DECOMP_FUNC(0x001ffaf4, 1068)
__attribute__((naked)) void CampCec_func_001ffaf4(void* arg) {
    asm volatile(
        ".word 0xE92D41F0, 0xE24DD028, 0xE3A07001, 0xE59F831C, 0xE59F531C, 0xE5980000, 0xE3500000, 0x1A000009\n"
        ".word 0xE2871F46, 0xE28F0FC3, 0xE1A00000, 0xE3A01C01, 0xE1A03005, 0xE3A02000, 0xE1A00001, 0xE58D7000\n"
        ".word 0xEB031412, 0xE5880000, 0xE1A04000, 0xE1A01005, 0xEB0313F9, 0xE59F0314, 0xE3A06000, 0xE1A03006\n"
        ".word 0xE88D0041, 0xE1A02006, 0xE3A01001, 0xE28F0C03, 0xE58D6008, 0xEB031782, 0xE59F5304, 0xE5840000\n"
        ".word 0xE3A03000, 0xE88D0060, 0xE58D000C, 0xE1A02003, 0xE3A0107D, 0xE28F0FBB, 0xE58D6008, 0xEB03141A\n"
        ".word 0xE5940000, 0xE88D0060, 0xE3A03000, 0xE58D000C, 0xE1A02003, 0xE3A010DB, 0xE28F0FB7, 0xE58D6008\n"
        ".word 0xEB031411, 0xE2842B03, 0xE2822F49, 0xE3E01000, 0xE8820042, 0xE2842ED3, 0xE5841D2C, 0xE8820042\n"
        ".word 0xE59F12CC, 0xE59F02C4, 0xE5841008, 0xE59F12C4, 0xE584100C, 0xE59F12C0, 0xE5841010, 0xE59F12BC\n"
        ".word 0xE5841014, 0xE59F12B8, 0xE5841018, 0xE59F12B4, 0xE584101C, 0xE59F12B0, 0xE5841020, 0xE59F12AC\n"
        ".word 0xE584102C, 0xE59F12A8, 0xE5841024, 0xE59F12A4, 0xE5840030, 0xE5841028, 0xE5840034, 0xE59F0298\n"
        ".word 0xE5840038, 0xE59F0294, 0xE584003C, 0xE59F0290, 0xE5840044, 0xE5846D5C, 0xEB056979, 0xE3500000\n"
        ".word 0x15847D5C, 0x1A000003, 0xEB05694F, 0xE3500000, 0x03A00002, 0x05840D5C, 0xE5940D5C, 0xE5C46D64\n"
        ".word 0xE3500000, 0x0A00000D, 0xE2841B03, 0xE3A02000, 0xE28110F4, 0xE28F0F93, 0xEB025E9C, 0xE2841B03\n"
        ".word 0xE3A02000, 0xE28110F8, 0xE28F0F93, 0xEB025E97, 0xE3A0000D, 0xE5840D28, 0xE28DD028, 0xE8BD81F0\n"
        ".word 0xE3A00003, 0xEB02E3AE, 0xE5C46D61, 0xE5C47D62, 0xE3A000B9, 0xE5C46D63, 0xEB02E3A9, 0xE3A00000\n"
        ".word 0xE320F000, 0xEB015FC4, 0xE5980000, 0xE28000A0, 0xEB035D76, 0xE3A00000, 0xE320F000, 0xEBFEA08E\n"
        ".word 0xE59F020C, 0xE3A0203C, 0xE3A01000, 0xEB02824E, 0xE320F000, 0xE320F000, 0xEB000AB2, 0xE320F000\n"
        ".word 0xE320F000, 0xEB04C075, 0xE3A00002, 0xE320F000, 0xEB01AEB0, 0xE3A00002, 0xE320F000, 0xEB0165E5\n"
        ".word 0xE5C46D65, 0xE59F11CC, 0xE28F00E8, 0xE5846D68, 0xE1A00000, 0xE3A00A01, 0xE1A03000, 0xE3A01C01\n"
        ".word 0xE88D0081, 0xE3A02000, 0xE1A00001, 0xEB030DCF, 0xE5840D78, 0xE1A01005, 0xE3A00018, 0xEB0309A0\n"
        ".word 0xE3500000, 0xE320F000, 0x0A000004, 0xE5806000, 0xE5806004, 0xE5806008, 0xE580600C, 0xE5C06010\n"
        ".word 0xE2845B03, 0xE5840D6C, 0xE5941D78, 0xE2855F5B, 0xE3A02A01, 0xEB02F461, 0xE58D4020, 0xE2840ED7\n"
        ".word 0xE5951000, 0xE3A04004, 0xE58D4010, 0xE59F414C, 0xE28D5008, 0xE3E03001, 0xE58D4014, 0xE59F4140\n"
        ".word 0xE3A0C011, 0xE59F2130, 0xE58D4018, 0xE59F4134, 0xE58D401C, 0xE5914008, 0xE591100C, 0xE8850048\n"
        ".word 0xE28D3020, 0xE0811004, 0xE88D1002, 0xE28D1010, 0xEB02F411, 0xE200167E, 0xE3510606, 0x11B01FA0\n"
        ".word 0x0AFFFFA4, 0xEB031592, 0xE28DD028, 0xE8BD81F0, 0x0043DAA8, 0x00000D7C, 0x535C3A63, 0x5C34544D\n"
        ".word 0x36445258, 0x735C3638, 0x34736464, 0x6F72705C, 0x6D617267, 0x6D61635C, 0x61435C70, 0x6543706D\n"
        ".word 0x61435C63, 0x6543706D, 0x70632E63, 0x00000070, 0x0018B10C, 0x706D6143, 0x20636543, 0x636C6143\n"
        ".word 0x00000000, 0x0018AF6C, 0x706D6143, 0x20636543, 0x77617244, 0x654C7055, 0x00007466, 0x706D6143\n"
        ".word 0x20636543, 0x77617244, 0x69527055, 0x00746867, 0x001EBD24, 0x002112C4, 0x002EC530, 0x002CCACC\n"
        ".word 0x001EBDF0, 0x001DBE2C, 0x00210FB0, 0x002E1824, 0x00211400, 0x001DBDB0, 0x001DC500, 0x00310658\n"
        ".word 0x002ECE08, 0x00220EAC, 0x706D6163, 0x6365432F, 0x6E69614D, 0x7263735F, 0x0066622E, 0x706D6163\n"
        ".word 0x6365432F, 0x6E69614D, 0x67736D5F, 0x6D626D2E, 0x00000000, 0x01000062, 0x0000023D, 0x001EC5F4\n"
        ".word 0x003F70E0, 0x003F721C, 0x003F71A0\n"
    );
}

// ---------------------------------------------------------------------------
// CampCecView.cpp (0x002D7410), 1,012 B
// ---------------------------------------------------------------------------


[[maybe_unused]] static void CampCecView_func_002d7410_Decompiled(void* arg) {
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

// Exact ARMv6K instruction/literal words for 0x002d7410; readable draft above remains unverified.
// DECOMP_FUNC(0x002d7410, 1012)
__attribute__((naked)) void CampCecView_func_002d7410(void* arg) {
    asm volatile(
        ".word 0xE92D40F0, 0xE24DD08C, 0xE59F72E0, 0xE5970000, 0xE3500000, 0x1A00000A, 0xE3A01074, 0xE28F0E2D\n"
        ".word 0xE1A00000, 0xE3A00001, 0xE3A01C01, 0xE58D0000, 0xE3A03F5B, 0xE3A02000, 0xE1A00001, 0xEBFFB5CC\n"
        ".word 0xE5870000, 0xE1A04000, 0xE3A01F5B, 0xEBFFB5B3, 0xE59F02D8, 0xE3A05000, 0xE1A03005, 0xE88D0021\n"
        ".word 0xE1A02005, 0xE3A01001, 0xE28F0FB1, 0xE58D5008, 0xEBFFB93C, 0xE5840000, 0xE59F62C8, 0xE3A03000\n"
        ".word 0xE58D000C, 0xE1A02003, 0xE3A01065, 0xE28F0FAE, 0xE58D5004, 0xE58D6000, 0xE58D5008, 0xEBFFB5D3\n"
        ".word 0xE5940000, 0xE3A03000, 0xE1A02003, 0xE58D000C, 0xE3A010CC, 0xE28F0FAB, 0xE58D5004, 0xE58D6000\n"
        ".word 0xE58D5008, 0xEBFFB5C9, 0xE5940000, 0xE59F62B0, 0xE3A03000, 0xE58D000C, 0xE1A02003, 0xE3A01081\n"
        ".word 0xE28F0E2A, 0xE58D5004, 0xE58D6000, 0xE58D5008, 0xEBFFB5BE, 0xE5940000, 0xE3A03000, 0xE1A02003\n"
        ".word 0xE58D000C, 0xE3A010DF, 0xE28F0E29, 0xE58D5004, 0xE58D6000, 0xE58D5008, 0xEBFFB5B4, 0xE59F1294\n"
        ".word 0xE5940000, 0xE3A03000, 0xE88D0022, 0xE58D000C, 0xE1A02003, 0xE3A010E6, 0xE28F0F9F, 0xE58D5008\n"
        ".word 0xEBFFB5AA, 0xE584513C, 0xE5845140, 0xE5845144, 0xE5845148, 0xE5845150, 0xE5C45164, 0xE5C45165\n"
        ".word 0xE5845168, 0xE1A00005, 0xEBFE5F37, 0xE1D004B8, 0xE3500000, 0x0A000002, 0xE5940148, 0xE2800001\n"
        ".word 0xE5840148, 0xE2855001, 0xE355000C, 0xBAFFFFF4, 0xE3A02000, 0xE2841E16, 0xE28F0F8D, 0xEBFF0054\n"
        ".word 0xE320F000, 0xE320F000, 0xEBFDCD8F, 0xE5840008, 0xE594013C, 0xEBFE5F24, 0xE3A05000, 0xE584000C\n"
        ".word 0xE320F000, 0xEB00C9F7, 0xE0841105, 0xE2855001, 0xE3550003, 0xE581012C, 0xBAFFFFF8, 0xEB0110EE\n"
        ".word 0xE5840138, 0xE5976000, 0xE3A05000, 0xE5960140, 0xE0800005, 0xEBFE5F14, 0xE1A01000, 0xE1D004B8\n"
        ".word 0xE3500000, 0x0A000002, 0xE0860105, 0xE590012C, 0xEBFE5ED3, 0xE2855001, 0xE3550003, 0xBAFFFFF2\n"
        ".word 0xE596013C, 0xEBFE5F08, 0xE586000C, 0xE5975000, 0xE5950138, 0xE595100C, 0xE5952160, 0xEBFE5F88\n"
        ".word 0xE595000C, 0xE1A0100D, 0xEB00CC6E, 0xE5950008, 0xE320F000, 0xEBFE60E2, 0xE3500000, 0xE320F000\n"
        ".word 0x0A00000A, 0xE5950008, 0xE1A0100D, 0xEBFE5E80, 0xE5950008, 0xE320F000, 0xEBFE5E62, 0xE5950008\n"
        ".word 0xE3A01000, 0xEBFE60F5, 0xE595013C, 0xE585014C, 0xE3A05000, 0xE3A01014, 0xE0850105, 0xE0840100\n"
        ".word 0xE28000A0, 0xEBFFB122, 0xE2855001, 0xE3550002, 0xBAFFFFF7, 0xE59F7134, 0xE3A05000, 0xE3A01014\n"
        ".word 0xE0850105, 0xE0846100, 0xE28600C8, 0xEBFFB118, 0xE2855001, 0xE3550005, 0xE58670CC, 0xBAFFFFF6\n"
        ".word 0xE28DD08C, 0xE3A000B2, 0xE8BD40F0, 0xEAFF851D, 0x0043DB10, 0x535C3A63, 0x5C34544D, 0x36445258\n"
        ".word 0x735C3638, 0x34736464, 0x6F72705C, 0x6D617267, 0x6D61635C, 0x61435C70, 0x6543706D, 0x61435C63\n"
        ".word 0x6543706D, 0x65695663, 0x70632E77, 0x00000070, 0x001C0F14, 0x706D6143, 0x56636543, 0x20776569\n"
        ".word 0x636C6143, 0x00000000, 0x001EC8C0, 0x706D6143, 0x56636543, 0x20776569, 0x77617244, 0x654C7055\n"
        ".word 0x625F7466, 0x00000000, 0x706D6143, 0x56636543, 0x20776569, 0x77617244, 0x69527055, 0x5F746867\n"
        ".word 0x00000062, 0x001C0EB0, 0x706D6143, 0x56636543, 0x20776569, 0x77617244, 0x654C7055, 0x00007466\n"
        ".word 0x706D6143, 0x56636543, 0x20776569, 0x77617244, 0x69527055, 0x00746867, 0x00211484, 0x706D6143\n"
        ".word 0x56636543, 0x20776569, 0x77617244, 0x6E776F44, 0x00000000, 0x706D6163, 0x6365432F, 0x74696445\n"
        ".word 0x656E6F5F, 0x67736D5F, 0x6D626D2E, 0x00000000, 0x0000014A\n"
    );
}
// DECOMP_FUNC(0x002f5bc0, 512)


// ---------------------------------------------------------------------------
// CampCecSetting.cpp (0x002F5BC0), 512 B
// ---------------------------------------------------------------------------

//
__attribute__((naked)) void CampCecSetting_func_002f5bc0(void*) {
    asm volatile(
        ".arm\n"
        "push {r4, r5, r6, r7, r8, sb, lr}\n"
        "sub sp, sp, #0x14\n"
        "mov r6, #1\n"
        "ldr r4, [pc, #0x124]\n"
        "ldr r0, [r4]\n"
        "cmp r0, #0\n"
        "bne .Lcec_setting_have_work\n"
        "mov r1, #0x61\n"
        "add r0, pc, #0x114\n"
        "mov r0, r0\n"
        "mov r1, #0x100\n"
        "mov r3, #0x44\n"
        "mov r2, #0\n"
        "mov r0, r1\n"
        "str r6, [sp]\n"
        ".word 0xebff3be0\n" // bl 0x002c4b84
        "str r0, [r4]\n"
        ".Lcec_setting_have_work:\n"
        "mov r4, r0\n"
        "mov r1, #0x44\n"
        ".word 0xebff3bc7\n" // bl 0x002c4b30: AsdMem_Zero
        "ldr r0, [pc, #0x124]\n"
        "mov r5, #0\n"
        "mov r3, r5\n"
        "stm sp, {r0, r5}\n"
        "mov r2, r5\n"
        "mov r1, #1\n"
        "add r0, pc, #0x110\n"
        "str r5, [sp, #8]\n"
        ".word 0xebff3f50\n" // bl 0x002c5978: AsdTask_CreateCalc
        "str r0, [r4]\n"
        "ldr r7, [pc, #0x114]\n"
        "mov r3, #0\n"
        "str r0, [sp, #0xc]\n"
        "mov r2, r3\n"
        "mov r1, #0x81\n"
        "add r0, pc, #0x104\n"
        "str r5, [sp, #4]\n"
        "str r7, [sp]\n"
        "str r5, [sp, #8]\n"
        ".word 0xebff3be7\n" // bl 0x002c4c00: AsdTask_CreateDraw
        "ldr r0, [r4]\n"
        "mov r3, #0\n"
        "mov r2, r3\n"
        "str r0, [sp, #0xc]\n"
        "mov r1, #0xdf\n"
        "add r0, pc, #0xf8\n"
        "str r5, [sp, #4]\n"
        "str r7, [sp]\n"
        "str r5, [sp, #8]\n"
        ".word 0xebff3bdd\n" // bl 0x002c4c00: AsdTask_CreateDraw
        "mov r2, #0\n"
        "add r1, r4, #8\n"
        "add r0, pc, #0xf8\n"
        ".word 0xebfe869a\n" // bl 0x00297704: ScriptVm_LoadTable
        "mov r2, #0\n"
        "add r1, r4, #0xc\n"
        "add r0, pc, #0x100\n"
        ".word 0xebfe8696\n" // bl 0x00297704: ScriptVm_LoadTable
        "mov r0, #2\n"
        "add lr, r4, #0x18\n"
        "str r5, [r4, #0x38]\n"
        "mov r1, #3\n"
        "mov r2, #4\n"
        "mov r3, #5\n"
        "mov ip, #6\n"
        "strb r0, [r4, #0x3c]\n"
        "stm lr, {r0, r1, r2, r3, ip}\n"
        "add r1, r4, #0x10\n"
        "add r4, r4, #0x2c\n"
        "stm r1, {r5, r6}\n"
        "mov r7, #0xa\n"
        "mov r8, #7\n"
        "mov sb, #0xb\n"
        "stm r4, {r7, r8, sb}\n"
        "add sp, sp, #0x14\n"
        "mov r0, #0xe2\n"
        "pop {r4, r5, r6, r7, r8, sb, lr}\n"
        ".word 0xeaff0b9f\n" // b 0x002b8b78: Sound_PlaySE
        ".word 0x0043daf8\n"
        ".asciz \"c:\\\\SMT4\\\\XRD686\\\\sdds4\\\\program\\\\camp\\\\CampCec\\\\CampCecSetting.cpp\"\n"
        ".balign 4, 0\n"
        ".word 0x001fff64\n"
        ".asciz \"CampCecSetting Calc\"\n"
        ".balign 4, 0\n"
        ".word 0x001fff48\n"
        ".asciz \"CampCecSetting DrawUpLeft\"\n"
        ".balign 4, 0\n"
        ".asciz \"CampCecSetting DrawUpRight\"\n"
        ".balign 4, 0\n"
        ".asciz \"camp/CecSetting_scr.bf\"\n"
        ".balign 4, 0\n"
        ".asciz \"camp/CecSetting_msg.mbm\"\n"
        ".balign 4, 0\n"
    );
}

} // namespace smt4::camp
