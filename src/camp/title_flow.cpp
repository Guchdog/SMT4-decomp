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

    // AsdText / sprites / cursor widgets.  Tbb_EnsureSlotLoaded,
    // UiSpriteGroup_Init and UiSpriteGroup_BindTable are declared canonically
    // in engine/asd_symbols.h.
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
                            static_cast<u32>(kPlayLogSpriteTable),
                            0x18, 0, 0, 0, 0, 0, 0, 0, 0);

    // 0x00194E78..0x00194EC0: five 0x8C-byte animation sprites.
    for (s32 i = 0; i < 5; ++i) {
        UiAnimSprite_Setup(&work->sprites[i], 0x30, 0, work, 1, 1.0f);
        UiAnimSprite_SetAnim(&work->sprites[i], 0, 0);
    }

    // 0x00194EC4..0x00194FA0: scan the 0x37 TBB sub-table.
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
                work->visible_indices[visible++] = static_cast<u16>(index);
            }
            ++index;
        } while (row_count() > index);
    }

    UiListCursor_Setup(&work->list_cursor, static_cast<s32>(visible), 5, 1, 0, 1);
}

// DECOMP_FUNC(0x002f4ca0, 572)


// ---------------------------------------------------------------------------
// titleConfig.cpp (0x002F4CA0), 572 B
// ---------------------------------------------------------------------------

//
void titleConfig_func_002f4ca0(void*) {
    using Calc = void (*)(void*);
    using Alloc = void* (*)(u32, u32, u32, u32, u32);
    using CreateCalc = void* (*)(const char*, u32, u32, u32, Calc, Calc, void*);
    using CreateDraw = void* (*)(const char*, u32, u32, u32, Calc, u32, u32, void*);
    using GroupInit = void (*)(void*);
    using GroupBind = void (*)(void*, u32, u32, u32, u32, u32, u32, u32,
                               u32, u32, u32);
    using SpriteSetup = void (*)(void*, u32, s32, void*, u32, f32);
    using SpriteSetAnim = void (*)(void*, s32, s32);
    using CursorSetup = void (*)(void*, s32, s32, s32, s32, s32);
    using LoadTable = u32 (*)(const char*, void*, u32);
    using SoundPlay = void (*)(s32);
    using ResetUi = void (*)(u32, u32);
    using FillPair = void (*)(void*, u32);
    using Mapper = u32 (*)(u8);
    using CopyPair = u32 (*)(void*, const void*);

    constexpr std::uintptr_t kWorkGlobal = 0x0044E2D0;
    constexpr std::uintptr_t kConfigGlobal = 0x0044E0F8;
    constexpr std::uintptr_t kSpriteTable = 0x00407EC6;
    constexpr std::uintptr_t kCalcTaskName = 0x0042AB78;
    constexpr std::uintptr_t kDrawTaskName = 0x0042AB8C;
    constexpr std::uintptr_t kConfigScriptName = 0x0042AB9C;
    constexpr std::uintptr_t kConfigMessageName = 0x0042ABAC;

    auto** const work_global = reinterpret_cast<TitleConfigWork**>(kWorkGlobal);
    auto* const work = static_cast<TitleConfigWork*>(
        reinterpret_cast<Alloc>(0x002C4B84)(0x100, 0x100, 0, 0x158, 1));
    *work_global = work;

    auto* const calc_task = reinterpret_cast<CreateCalc>(0x002C5978)(
        reinterpret_cast<const char*>(kCalcTaskName), 2, 0, 0,
        reinterpret_cast<Calc>(0x001EA928),
        reinterpret_cast<Calc>(0x002CAEF0), work);
    work->calc_task = calc_task;
    (void)reinterpret_cast<CreateDraw>(0x002C4C00)(
        reinterpret_cast<const char*>(kDrawTaskName), 0xE6, 0, 0,
        reinterpret_cast<Calc>(0x002CAFD0), 0, 0, calc_task);

    auto* const group = &work->sprite_group;
    reinterpret_cast<GroupInit>(0x002C3344)(group);
    reinterpret_cast<GroupBind>(0x002C32F8)(group, kSpriteTable, 0x18,
                                            0, 0, 0, 0, 0, 0, 0, 0);
    auto* const sprite = &work->sprite;
    reinterpret_cast<SpriteSetup>(0x002BDB2C)(sprite, 0x2F, 0, group, 0xC9, 1.0f);
    reinterpret_cast<SpriteSetAnim>(0x002BDAC0)(sprite, 0, 0);
    reinterpret_cast<CursorSetup>(0x0029FAE8)(&work->list_cursor, 3, 3, 1, 0, 1);

    work->field_08 = 0;
    work->field_1a = 0;
    reinterpret_cast<FillPair>(0x0027EDF8)(&work->field_1c, 0xFFFFFFFF);
    work->field_24 = 0;
    (void)reinterpret_cast<LoadTable>(0x00297704)(
        reinterpret_cast<const char*>(kConfigScriptName), &work->script_bf, 0);
    (void)reinterpret_cast<LoadTable>(0x00297704)(
        reinterpret_cast<const char*>(kConfigMessageName), &work->msg_mbm, 0);
    reinterpret_cast<SoundPlay>(0x002B8B78)(0x99);
    reinterpret_cast<ResetUi>(0x0029F10C)(0, 0x323232FF);

    auto* const config = reinterpret_cast<const u8*>(kConfigGlobal);
    work->field_28 = reinterpret_cast<Mapper>(0x002CAB70)(config[0]);
    work->field_2c = reinterpret_cast<Mapper>(0x0021F39C)(config[1]);
    work->field_30 = reinterpret_cast<Mapper>(0x002E0AF4)(config[2]);

    // The header's frozen declaration is void, but the original tail-branch
    // exposes this helper's result in r0. Preserve that ABI-visible value.
    const u32 copy_result =
        reinterpret_cast<CopyPair>(0x002ADB40)(&work->field_34, config);
    asm volatile("mov r0, %0" : : "r"(copy_result) : "r0");
    // Keep this replacement within the original 572-byte in-place slot.
    asm volatile("nop\n\tnop\n\tnop");
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
    // bits are set.
    work->field_a8 = (Flag_CheckEventBit(0x555) != 0 && Flag_CheckEventBit(0x557) != 0) ? 1 : 0;
}

// ---------------------------------------------------------------------------
// titleMain.cpp (0x001EB02C), 524 B
// ---------------------------------------------------------------------------

//
// DECOMP_FUNC(0x001eb02c, 524)
void titleMain_func_001eb02c(const u8* arg) {
    TitleMainWork* work = reinterpret_cast<TitleMainWork*>(
        AsdMem_AllocAlign(0x10000, 0x100, 0, sizeof(TitleMainWork), 1)
    );
    g_TitleMainWork = work;

    work->field_08 = 0;
    work->field_0c = 0;
    work->flag_10 = 1;
    work->flag_60 = 1;
    for (int i = 0; i < 8; ++i) {
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

    if (arg != nullptr) {
        work->flag_95 = *arg;
        work->flag_10 = 0;
    }

    void* calc_task = AsdTask_CreateCalc(
        "TITLE C",
        2,
        0,
        0,
        reinterpret_cast<void(*)(void*)>(0x001e989c),
        0x002ca6f4,
        0
    );
    work->calc_task = calc_task;

    AsdTask_CreateDraw(
        "TITLE UDrawLeft",
        0x76,
        0,
        0,
        reinterpret_cast<void(*)(void*)>(0x0020fd5c),
        0,
        0,
        calc_task
    );

    AsdTask_CreateDraw(
        "TITLE UDrawRight",
        0xd4,
        0,
        0,
        reinterpret_cast<void(*)(void*)>(0x0021f36c),
        0,
        0,
        calc_task
    );

    AsdTask_CreateDraw(
        "TITLE D",
        0xe7,
        0,
        0,
        reinterpret_cast<void(*)(void*)>(0x002ca7a8),
        0,
        0,
        calc_task
    );
}

// DECOMP_FUNC(0x001dafbc, 668)
void tmnlMain_func_001dafbc(const u32* arg) {
    TerminalMainWork* work = reinterpret_cast<TerminalMainWork*>(
        AsdMem_Alloc(0x100, 0x100, 0, sizeof(TerminalMainWork), 1)
    );
    g_TerminalMainWork = work;

    if (UiInput_TestFlag(10) == 0) {
        UiInput_SetFlag(10, 1);
    }
    if (UiInput_TestFlag(12) == 0) {
        UiInput_SetFlag(12, 1);
    }
    if (UiInput_TestFlag(11) == 0) {
        if (Flag_CheckEventBit(0x277) != 0) {
            UiInput_SetFlag(11, 1);
        }
    }
    ScriptVm_SetFlag(0x465, 0, 1);

    work->flag_05 = 1;
    work->field_10 = 0;
    work->field_14 = 0;
    work->flag_09 = 0;
    work->field_0c = 0;
    for (int i = 0; i < 10; ++i) {
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
    Ui_SetEntryLock(0);
    work->flag_04 = 0;

    if (arg != nullptr) {
        work->flag_09 = static_cast<u8>(*arg & 0xFF);
        work->flag_05 = 0;
        UiInput_SetFlag(*arg & 0xFF, 1);
        Camp_AddProgressValue(0x1c, 1);
        work->field_10 = 0;
        work->field_14 = 0;
    } else {
        work->field_14 = 0;
        work->field_10 = 1;
        UiAnimSlot_SetState(0, 0xFF);
    }

    void* calc_task = AsdTask_CreateCalc(
        "TMNL C",
        2,
        0,
        0,
        reinterpret_cast<void(*)(void*)>(0x0021f240),
        0x001d98c4,
        0
    );
    work->calc_task = calc_task;

    AsdTask_CreateDraw(
        "TMNL UD",
        0x75,
        0,
        0,
        reinterpret_cast<void(*)(void*)>(0x001fe198),
        0,
        0,
        calc_task
    );

    AsdTask_CreateDraw(
        "TMNL UD",
        0xd3,
        0,
        0,
        reinterpret_cast<void(*)(void*)>(0x002e08d4),
        0,
        0,
        calc_task
    );

    AsdTask_CreateDraw(
        "TMNL DD",
        0xe7,
        0,
        0,
        reinterpret_cast<void(*)(void*)>(0x0021f258),
        0,
        0,
        calc_task
    );
}

} // namespace smt4::camp
