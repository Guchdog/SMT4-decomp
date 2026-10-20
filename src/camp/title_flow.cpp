#include "camp/title_flow.h"
#include "engine/asd_symbols.h"
#include "engine/asd_texture.h"
#include "ui/tbb_table.h"
#include "ui/terminal_ui.h"

namespace smt4::camp {

PlayLogWork* g_PlayLogWork = nullptr;              // 0x0043DD08
TitleConfigWork* g_TitleConfigWork = nullptr;      // 0x0044E2D0
ConfigWork* g_ConfigWork = nullptr;                // 0x0043DC58
TitleMainWork* g_TitleMainWork = nullptr;          // 0x0044E300
TerminalMainWork* g_TerminalMainWork = nullptr;    // 0x00432CE0

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

extern "C" {
    // AsdMemory
    void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);         // 0x002C4B84
    void* AsdMem_AllocAlign(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);    // 0x002C54F0
    void  AsdMem_Zero(void* ptr, u32 size);                                 // 0x002C4B30

    // Resource request / script tables
    void  AsdRes_Request(u32 key, u32 sub);                                 // 0x002A6214
    void  ScriptVm_LoadTable(const char* name, void* out, u32 value);       // 0x00297704
    u32   Tbb_EnsureSlotLoaded(u32 slot_id);                                // 0x002976AC

    // AsdText / sprites / cursor widgets
    void  UiSpriteGroup_Init(void* group);                                  // 0x002C3344
    void  UiSpriteGroup_BindTable(void* group, const void* t0, u32 s0,
                                  u32 s1, const void* t1, u32 s2,
                                  u32 a6, u32 a7, const void* t2, u32 s3);  // 0x002C32F8
    void  UiAnimSprite_Setup(ui::UiAnimSprite* sprite, u32 res_group_id,
                             s32 idx, void* sprite_group, u32 panel_id,
                             f32 scale);                                    // 0x002BDB2C
    void  UiAnimSprite_SetAnim(ui::UiAnimSprite* sprite, s32 anim_idx,
                               s32 mode);                                   // 0x002BDAC0
    void  UiListCursor_Setup(ui::UiListCursor* cursor, s32 total_items,
                             s32 visible_rows, s32 cols, s32 wrap_row,
                             s32 repeat);                                   // 0x0029FAE8

    void  Sound_PlaySE(s32 se_id);                                          // 0x002B8B78

    // Save / option persistence helpers
    s32   SaveData_GetEntryValue(u32 id);                                   // 0x00290A38
    s32   SaveData_GetPlayLogCount();                                       // 0x00290A4C
    u8    SaveData_GetSettingMode();                                        // 0x00297688
    void  Camp_AddProgressValue(u32 index, s32 delta);                      // 0x0029C0FC
    void  ScriptVm_SetFlag(u32 flag_id, u32 value, u32 notify);             // 0x002899C4
    void  UiAnimSlot_SetState(u32 index, u32 value);                        // 0x00282E6C
    void  Ui_SetEntryLock(u32 mode);                                        // 0x002A7540

    // Input / audio / UI boot helpers
    u32   UiInput_TestFlag(u32 id);                                         // 0x00263778 (falls into 0x00263784)
    void  UiInput_SetFlag(u32 id, u32 value);                               // 0x00263734 (falls into 0x0026373C)
    u32   Flag_CheckEventBit(u32 flag_id);                                  // 0x002C0BA8
    void  Sound_SetBgmSequence(u32 id);                                     // 0x001A7F30
    void  Sound_RequestBgm(u32 id, u32 volume, u32 frames);                 // 0x002A0640
    void  RunWin_OpenDefault();                                             // 0x0032FEF4
    void  Camp_SetFadeColor(u32 screen, u32 rgba);                          // 0x0029F10C
    void  UiConfig_FillPair(void* dst, u32 byte_value);                     // 0x0027EDF8
    void  UiConfig_CopyPair(void* dst, const void* src);                    // 0x002ADB40
    u32   Config_MapByteToIndexA(u8 value);                                 // 0x002CAB70
    u32   Config_MapByteToIndexB(u8 value);                                 // 0x0021F39C
    u32   Config_MapByteToIndexC(u8 value);                                 // 0x002E0AF4
}

namespace {
// 0x00402D58 / 0x00407EC6: sprite tables bound by UiSpriteGroup_BindTable.
constexpr std::uintptr_t kPlayLogSpriteTable = 0x00402D58;
constexpr std::uintptr_t kTitleConfigSpriteTable = 0x00407EC6;
} // namespace

// ---------------------------------------------------------------------------
// PlayLog.cpp (0x00194DBC), 648 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00194dbc, 648)
void PlayLog_func_00194dbc(void* arg) {
    (void)arg;
    PlayLogWork* work = g_PlayLogWork;
    if (work == nullptr) {
        // 0x00194DC8/0x00194DF0: AsdMem_Alloc(0x100,0x100,0,0x488,1).
        work = static_cast<PlayLogWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(PlayLogWork), 1));
        g_PlayLogWork = work;
    }
    AsdMem_Zero(work, sizeof(PlayLogWork));                 // 0x00194E10

    // 0x00194E1C..0x00194E44: option counter, texture group request, table
    // load and sprite-group reset.
    work->field_344 = 0;
    engine::AsdTMTexTable_func_002c4e28(0x30);              // 0x002C4E28
    AsdRes_Request(0x30, 0);                                // 0x002A6214
    Tbb_EnsureSlotLoaded(0x37);                             // 0x002976AC
    UiSpriteGroup_Init(&work->sprite_group);                // 0x002C3344
    UiSpriteGroup_BindTable(&work->sprite_group,
                            reinterpret_cast<const void*>(kPlayLogSpriteTable),
                            0x18, 0, nullptr, 0, 0, 0, nullptr, 0);

    // 0x00194E78..0x00194EC0: five 0x8C-byte animation sprites.  The record
    // stride is 140 (`rsb r0,r4,r4,lsl #3` then `add r0,r0,r0,lsl #2`,
    // 0x00194E84/0x00194E8C) and the first one starts at +0x20.
    for (s32 i = 0; i < 5; ++i) {
        UiAnimSprite_Setup(&work->sprites[i], 0x30, 0, work, 1, 1.0f);
        UiAnimSprite_SetAnim(&work->sprites[i], 0, 0);
    }

    // 0x00194EC4..0x00194FA0: scan the 0x37 TBB sub-table.  Rows are 0x40
    // bytes (`adds r6,r6,r4,lsl #6`, 0x00194F2C).  A negative first halfword
    // uses the global play-log counter (0x00290A4C); otherwise the low byte is
    // an id looked up in the save array (0x00290A38).  Id 0x29 is stored as
    // count-1 (`subne r0,r0,#1`, 0x00194FF0).
    u32 visible = 0;
    auto row_count = []() -> u32 {
        const ui::Tbl1Header* table = ui::Tbb_GetGlobalSubTable(0x37, 0);
        ui::Tbb_GetPayloadData(table);
        return ui::Tbb_GetRowCount(table);
    };

    if (row_count() != 0) {
        u32 index = 0;
        do {
            const ui::Tbl1Header* table = ui::Tbb_GetGlobalSubTable(0x37, 0);
            const u8* payload =
                static_cast<const u8*>(ui::Tbb_GetPayloadData(table));
            const u32 rows = ui::Tbb_GetRowCount(table);
            const u8* row =
                (index < rows) ? payload + static_cast<std::size_t>(index) * 0x40
                               : nullptr;

            bool keep = false;
            if (row != nullptr) {
                const s16 key = *reinterpret_cast<const s16*>(row);
                s32 value;
                if (key < 0) {
                    value = SaveData_GetPlayLogCount();     // 0x00290A4C
                    work->entry_values[index] = static_cast<u32>(value);
                    keep = value != 0;
                } else {
                    const u32 id = static_cast<u16>(key) & 0xFF;
                    value = SaveData_GetEntryValue(id);     // 0x00290A38
                    work->entry_values[index] = static_cast<u32>(value);
                    if (id == 0x29) {
                        if (value == 0) {
                            keep = false;
                        } else {
                            --value;
                            work->entry_values[index] = static_cast<u32>(value);
                            keep = value != 0;
                        }
                    } else {
                        keep = value != 0;
                    }
                }
            }

            if (keep) {
                // `add r0,r6,r5,lsl #2` / `strh r4,[r0,#0x24]` with
                // r0 = work + 0x400: the visible list starts at +0x424.
                work->visible_indices[visible++] = static_cast<u16>(index);
            }
            ++index;
        } while (row_count() > index);
    }

    // 0x00194FA0..0x00194FB8: UiListCursor_Setup(work+0x2DC, visible, 5, 1, 0, 1).
    UiListCursor_Setup(&work->list_cursor, static_cast<s32>(visible), 5, 1, 0, 1);
}

// ---------------------------------------------------------------------------
// titleConfig.cpp (0x002F4CA0), 572 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002f4ca0, 572)
void titleConfig_func_002f4ca0(void* arg) {
    (void)arg;
    // 0x002F4CA8..0x002F4CE0: this constructor has no null check and never
    // calls AsdMem_Zero -- every allocation replaces the global outright.
    TitleConfigWork* work = static_cast<TitleConfigWork*>(
        AsdMem_Alloc(0x100, 0x100, 0, sizeof(TitleConfigWork), 1));
    g_TitleConfigWork = work;

    // 0x002F4CE4..0x002F4D00: CreateCalc("TITLE_CONFIG_MAIN", 2, 0, 0,
    // calc = 0x001EA928, a5 = 0x002CAEF0, a6 = work).
    work->calc_task = AsdTask_CreateCalc(
        "TITLE_CONFIG_MAIN", 2, 0, 0, TitleConfig_Calc,
        static_cast<u32>(
            reinterpret_cast<std::uintptr_t>(&TitleConfig_Secondary)),
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(work)));

    // 0x002F4D04..0x002F4D30: CreateDraw("TITLE_CONFIG D", 0xE6, ...).
    AsdTask_CreateDraw("TITLE_CONFIG D", 0xE6, 0, 0, TitleConfig_Draw, 0, 0,
                       work->calc_task);

    // 0x002F4D34..0x002F4D98: sprite group, one 0x8C sprite (resource group
    // 0x2F, panel id 0xC9), animation 0.
    UiSpriteGroup_Init(&work->sprite_group);                // 0x002C3344
    UiSpriteGroup_BindTable(
        &work->sprite_group,
        reinterpret_cast<const void*>(kTitleConfigSpriteTable),
        0x18, 0, nullptr, 0, 0, 0, nullptr, 0);
    UiAnimSprite_Setup(&work->sprite, 0x2F, 0, &work->sprite_group, 0xC9, 1.0f);
    UiAnimSprite_SetAnim(&work->sprite, 0, 0);

    // 0x002F4D9C..0x002F4DB4: cursor with three rows, then field_08 = 0.
    UiListCursor_Setup(&work->list_cursor, 3, 3, 1, 0, 1);
    work->field_08 = 0;

    // 0x002F4DB8..0x002F4DD4: fill +0x1C..+0x24 with the byte 0xFF
    // (`mvn r1,#0` is the byte fill argument) and clear the halfword at +0x1A.
    UiConfig_FillPair(&work->field_1c, 0xFF);               // 0x0027EDF8
    work->field_1a = 0;

    // 0x002F4DC8..0x002F4DE8: config script/message tables.
    ScriptVm_LoadTable("camp/config.bf", &work->script_bf, 0);
    ScriptVm_LoadTable("camp/config.mbm", &work->msg_mbm, 0);

    // 0x002F4DEC..0x002F4E00: SE 0x99 and a 0x32 grey fade.
    Sound_PlaySE(0x99);
    Camp_SetFadeColor(0, 0x323232FF);

    // 0x002F4E00..0x002F4E24: persisted configuration bytes 0/1/2 are mapped
    // through three 12-entry lookup tables; the results land at +0x28..+0x30.
    work->field_28 = Config_MapByteToIndexA(g_ConfigBytes[0]);
    work->field_2c = Config_MapByteToIndexB(g_ConfigBytes[1]);
    work->field_30 = Config_MapByteToIndexC(g_ConfigBytes[2]);

    // 0x002F4E28..0x002F4E3C: tail-call UiConfig_CopyPair(work+0x34,
    // g_ConfigBytes), copying the first two configuration words.
    UiConfig_CopyPair(&work->field_34, g_ConfigBytes);
}

// ---------------------------------------------------------------------------
// Config.cpp (0x0018B660), 536 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0018b660, 536)
void Config_func_0018b660(void* arg) {
    (void)arg;
    ConfigWork* work = g_ConfigWork;
    if (work == nullptr) {
        // 0x0018B67C..0x0018B6A0: AsdMem_Alloc(0x100,0x100,0,0xBC,1).
        work = static_cast<ConfigWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(ConfigWork), 1));
        g_ConfigWork = work;
    }
    AsdMem_Zero(work, sizeof(ConfigWork));                  // 0x0018B6AC

    // 0x0018B6B4..0x0018B6EC: option field, texture group and tables.
    work->field_64 = 0;
    work->field_a8 = 0;
    engine::AsdTMTexTable_func_002c4e28(0x2F);              // 0x002C4E28
    AsdRes_Request(0x2F, 0);                                // 0x002A6214
    ScriptVm_LoadTable("camp/config.bf", &work->script_bf, 0);
    ScriptVm_LoadTable("camp/config.mbm", &work->msg_mbm, 0);

    // 0x0018B6F0..0x0018B738: load TBB slot 0x36 and seed the cursor with its
    // row count.
    Tbb_EnsureSlotLoaded(0x36);                             // 0x002976AC
    const ui::Tbl1Header* table = ui::Tbb_GetGlobalSubTable(0x36, 0);
    ui::Tbb_GetPayloadData(table);
    const u32 rows = ui::Tbb_GetRowCount(table);
    UiListCursor_Setup(&work->list_cursor, static_cast<s32>(rows), 1, 1, 0, 1);

    // 0x0018B73C..0x0018B7E4: two event bits and the saved setting mode
    // (0x00297688 reads the byte at g+0x24BB0) select 0, 1 or 2.
    const u8 mode = SaveData_GetSettingMode();
    u32 value = 1;
    const bool flag_555 = Flag_CheckEventBit(0x555) != 0;
    const bool flag_557 = Flag_CheckEventBit(0x557) != 0;

    if (flag_555 && flag_557) {
        if (mode == 1) {
            value = 0;
        } else if (mode == 2) {
            value = 2;
        }
    } else if (flag_557) {
        if (mode == 1) {
            value = 0;
        }
    } else if (flag_555) {
        if (mode == 0) {
            value = 0;
        }
    }
    work->field_80 = value;

    // 0x0018B7E0..0x0018B810: the lock byte is raised only when both event
    // bits are set; the listing re-tests 0x555 and 0x557 here.
    work->field_a8 = (flag_555 && flag_557) ? 1 : 0;
}

// ---------------------------------------------------------------------------
// titleMain.cpp (0x001EB02C), 524 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001eb02c, 524)
void titleMain_func_001eb02c(const u8* arg) {
    // 0x001EB038..0x001EB060: aligned 0xA0 allocation, stored unconditionally
    // (no null check, no AsdMem_Zero).
    TitleMainWork* work = static_cast<TitleMainWork*>(
        AsdMem_AllocAlign(0x10000, 0x100, 0, sizeof(TitleMainWork), 1));
    g_TitleMainWork = work;

    // 0x001EB068..0x001EB0F4: field reset.  The eight floats at +0x40 are
    // written from s0 = 0.0 (`vstr s0`), followed by the byte flags.
    work->field_08 = 0;
    work->field_0c = 0;
    work->flag_10 = 1;
    work->flag_60 = 1;
    for (s32 i = 0; i < 8; ++i) {
        work->field_40[i] = 0.0f;
    }
    work->flag_63 = 0;
    work->flag_61 = 0;
    work->flag_62 = 0;
    work->field_80 = 2;
    work->field_70 = 0;
    work->field_72 = 0;
    work->field_74 = 0;
    work->field_78 = 0;
    work->field_64 = 0.0f;
    work->field_68 = 0.0f;
    work->flag_7c = 0;
    work->flag_84 = 1;
    work->flag_86 = 0;
    work->flag_85 = 1;
    work->flag_96 = 0;
    work->flag_94 = 0;
    work->field_98 = 0.0f;
    work->flag_95 = 0;
    work->flag_04 = 0;

    // 0x001EB0F0..0x001EB104: when a boot argument is present its first byte
    // becomes flag_95 and the default state byte is cleared.
    if (arg != nullptr) {
        work->flag_95 = *arg;
        work->flag_10 = 0;
    }

    // 0x001EB108..0x001EB12C: CreateCalc("TITLE C", 2, 0, 0, calc =
    // 0x001E989C, a5 = 0x002CA6F4, a6 = 0).
    work->calc_task = AsdTask_CreateCalc(
        "TITLE C", 2, 0, 0, TitleMain_Calc,
        static_cast<u32>(
            reinterpret_cast<std::uintptr_t>(&TitleMain_Secondary)),
        0);

    // 0x001EB130..0x001EB1A4: three draw tasks.
    AsdTask_CreateDraw("TITLE UDrawLeft", 0x76, 0, 0, TitleMain_DrawLeft,
                       0, 0, work->calc_task);
    AsdTask_CreateDraw("TITLE UDrawRight", 0xD4, 0, 0, TitleMain_DrawRight,
                       0, 0, work->calc_task);
    AsdTask_CreateDraw("TITLE D", 0xE7, 0, 0, TitleMain_DrawDown,
                       0, 0, work->calc_task);
}

// ---------------------------------------------------------------------------
// tmnlMain.cpp (0x001DAFBC), 668 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001dafbc, 668)
void tmnlMain_func_001dafbc(const u32* arg) {
    // 0x001DAFC8..0x001DAFF8: AsdMem_Alloc(0x100,0x100,0,0x5E8,1) with the
    // result stored to g_TerminalMainWork immediately.
    TerminalMainWork* work = static_cast<TerminalMainWork*>(
        AsdMem_Alloc(0x100, 0x100, 0, sizeof(TerminalMainWork), 1));
    g_TerminalMainWork = work;

    // 0x001DAFFC..0x001DB06C: three input/event flags.  0xA and 0xC are
    // enabled unconditionally; 0xB additionally requires event bit 0x277.
    if (UiInput_TestFlag(0xA) == 0) {                       // 0x00263778
        UiInput_SetFlag(0xA, 1);                            // 0x00263734
    }
    if (UiInput_TestFlag(0xC) == 0) {
        UiInput_SetFlag(0xC, 1);
    }
    if (UiInput_TestFlag(0xB) == 0) {
        if (Flag_CheckEventBit(0x277) != 0) {               // 0x002C0BA8
            UiInput_SetFlag(0xB, 1);
        }
    }

    // 0x001DB06C..0x001DB0E8: script flag 0x465, the main field reset and the
    // zeroed option words at +0x20..+0x44.
    ScriptVm_SetFlag(0x465, 0, 1);                          // 0x002899C4
    work->flag_05 = 1;
    work->field_10 = 0;
    work->field_14 = 0;
    work->flag_09 = 0;
    work->field_0c = 0;
    for (s32 i = 0; i < 10; ++i) {
        work->field_20[i] = 0;
    }
    work->field_550 = 0;
    work->flag_554 = 0;
    work->field_558 = 0;
    work->field_568 = 0;
    work->field_564 = 0;
    work->field_574 = 0;
    work->field_570 = 0;
    work->field_580 = 0;
    work->field_57c = 0;
    work->field_58c = 0;
    work->field_588 = 0;

    // 0x001DB0E4..0x001DB0F8: per-frame entry lock and flag_04.
    Ui_SetEntryLock(0);                                     // 0x002A7540
    work->flag_04 = 0;

    // 0x001DB0F0..0x001DB13C: boot argument handling.  `ldr r0,[r5]` reads a
    // 32-bit value and only its low byte is used.
    if (arg != nullptr) {
        work->flag_09 = static_cast<u8>(*arg);
        work->flag_05 = 0;
        UiInput_SetFlag(static_cast<u32>(work->flag_09), 1);
        Camp_AddProgressValue(0x1C, 1);                     // 0x0029C0FC
        work->field_10 = 0;
        work->field_14 = 0;
    } else {
        work->field_14 = 0;
        work->field_10 = 1;
        UiAnimSlot_SetState(0, 0xFF);                       // 0x00282E6C
    }

    // 0x001DB140..0x001DB1E4: calc task (callback 0x001D98C4, the terminal
    // scene renderer) and three draw tasks.
    work->calc_task = AsdTask_CreateCalc(
        "TMNL C", 2, 0, 0,
        reinterpret_cast<void (*)(void*)>(&ui::Ui_TerminalSceneRender),
        static_cast<u32>(0x0021F240), 0);

    AsdTask_CreateDraw("TMNL UD", 0x75, 0, 0, Terminal_DrawUp,
                       0, 0, work->calc_task);
    AsdTask_CreateDraw("TMNL UD", 0xD3, 0, 0, Terminal_DrawUpAlt,
                       0, 0, work->calc_task);
    AsdTask_CreateDraw("TMNL DD", 0xE7, 0, 0, Terminal_DrawDown,
                       0, 0, work->calc_task);
}

} // namespace smt4::camp
