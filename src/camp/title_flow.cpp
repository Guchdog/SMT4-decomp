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
// DECOMP_FUNC(0x002f4ca0, 572)


// ---------------------------------------------------------------------------
// titleConfig.cpp (0x002F4CA0), 572 B
// ---------------------------------------------------------------------------

//
__attribute__((naked)) void titleConfig_func_002f4ca0(void*) {
    asm volatile(
        ".arm\n"
        "push {r4, r5, r6, lr}\n"
        "sub sp, sp, #0x20\n"
        "ldr r1, [pc, #0x190]\n"
        "add r0, pc, #0x190\n"
        "mov r0, r0\n"
        "mov r6, #1\n"
        "mov r1, #0x100\n"
        "mov r3, #0x158\n"
        "mov r2, #0\n"
        "mov r0, r1\n"
        "str r6, [sp]\n"
        ".word 0xebff3fac\n" // bl 0x002c4b84
        "ldr r1, [pc, #0x1a0]\n"
        "ldr r3, [pc, #0x1a4]\n"
        "ldr r2, [pc, #0x19c]\n"
        "mov r4, r0\n"
        "str r0, [r1]\n"
        "add r0, sp, #4\n"
        "str r3, [sp]\n"
        "stm r0, {r2, r4}\n"
        "mov r3, #0\n"
        "mov r2, r3\n"
        "mov r1, #2\n"
        "add r0, pc, #0x180\n"
        ".word 0xebff431c\n" // bl 0x002c5978: AsdTask_CreateCalc
        "mov r1, r0\n"
        "ldr r0, [pc, #0x188]\n"
        "mov r5, #0\n"
        "str r1, [r4]\n"
        "stm sp, {r0, r5}\n"
        "str r1, [sp, #0xc]\n"
        "mov r3, r5\n"
        "mov r2, r5\n"
        "mov r1, #0xe6\n"
        "add r0, pc, #0x16c\n"
        "str r5, [sp, #8]\n"
        ".word 0xebff3fb2\n" // bl 0x002c4c00: AsdTask_CreateDraw
        "add r0, r4, #0x3c\n"
        ".word 0xebff3981\n" // bl 0x002c3344: UiSpriteGroup_Init
        "str r5, [sp, #0x14]\n"
        "str r5, [sp, #0x18]\n"
        "ldr r1, [pc, #0x160]\n"
        "mov r3, #0\n"
        "mov r2, #0x18\n"
        "add r0, r4, #0x3c\n"
        "str r5, [sp, #0xc]\n"
        "str r5, [sp, #0x10]\n"
        "str r5, [sp]\n"
        "str r5, [sp, #4]\n"
        "str r5, [sp, #8]\n"
        ".word 0xebff3962\n" // bl 0x002c32f8: UiSpriteGroup_BindTable
        "mov r0, #0xc9\n"
        "str r0, [sp]\n"
        "vldr s0, [pc, #0x134]\n"
        "add r3, r4, #0x3c\n"
        "mov r2, #0\n"
        "mov r1, #0x2f\n"
        "add r0, r4, #0x5c\n"
        ".word 0xebff2367\n" // bl 0x002bdb2c: UiAnimSprite_Setup
        "mov r2, #0\n"
        "mov r1, r2\n"
        "add r0, r4, #0x5c\n"
        ".word 0xebff2348\n" // bl 0x002bdac0: UiAnimSprite_SetAnim
        "mov r2, #3\n"
        "mov r3, #1\n"
        "mov r1, r2\n"
        "add r0, r4, #0xe8\n"
        "stm sp, {r5, r6}\n"
        ".word 0xebfeab4c\n" // bl 0x0029fae8: UiListCursor_Setup
        "str r5, [r4, #8]\n"
        "mvn r1, #0\n"
        "add r0, r4, #0x1c\n"
        "strh r5, [r4, #0x1a]\n"
        ".word 0xebfe280b\n" // bl 0x0027edf8: UiConfig_FillPair
        "mov r2, #0\n"
        "add r1, r4, #0x14c\n"
        "add r0, pc, #0xdc\n"
        "strh r5, [r4, #0x24]\n"
        ".word 0xebfe8a49\n" // bl 0x00297704: ScriptVm_LoadTable
        "mov r2, #0\n"
        "add r1, r4, #0x150\n"
        "add r0, pc, #0xd8\n"
        ".word 0xebfe8a45\n" // bl 0x00297704: ScriptVm_LoadTable
        "mov r0, #0x99\n"
        ".word 0xebff0f60\n" // bl 0x002b8b78: Sound_PlaySE
        "ldr r1, [pc, #0xd8]\n"
        "mov r0, #0\n"
        ".word 0xebfea8c2\n" // bl 0x0029f10c: Camp_SetFadeColor
        "ldr r5, [pc, #0xd0]\n"
        "ldrb r0, [r5]\n"
        ".word 0xebff5758\n" // bl 0x002cab70: Config_MapByteToIndexA
        "str r0, [r4, #0x28]\n"
        "ldrb r0, [r5, #1]\n"
        ".word 0xebfca960\n" // bl 0x0021f39c: Config_MapByteToIndexB
        "str r0, [r4, #0x2c]\n"
        "ldrb r0, [r5, #2]\n"
        ".word 0xebffaf33\n" // bl 0x002e0af4: Config_MapByteToIndexC
        "str r0, [r4, #0x30]\n"
        "add sp, sp, #0x20\n"
        "mov r1, r5\n"
        "add r2, r4, #0x34\n"
        "pop {r4, r5, r6, lr}\n"
        "mov r0, r2\n"
        ".word 0xeafee33f\n" // b 0x002adb40: UiConfig_CopyPair
        ".word 0x0000033d\n"
        ".asciz \"c:\\\\SMT4\\\\XRD686\\\\sdds4\\\\program\\\\title\\\\titleConfig.cpp\"\n"
        ".balign 4, 0\n"
        ".word 0x0044e2d0\n"
        ".word 0x002caef0\n"
        ".word 0x001ea928\n"
        ".asciz \"TITLE_CONFIG_MAIN\"\n"
        ".balign 4, 0\n"
        ".word 0x002cafd0\n"
        ".asciz \"TITLE_CONFIG D\"\n"
        ".balign 4, 0\n"
        ".word 0x00407ec6\n"
        ".word 0x3f800000\n"
        ".asciz \"camp/config.bf\"\n"
        ".balign 4, 0\n"
        ".asciz \"camp/config.mbm\"\n"
        ".balign 4, 0\n"
        ".word 0x323232ff\n"
        ".word 0x0044e0f8\n"
    );
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
// DECOMP_FUNC(0x001eb02c, 524)


// ---------------------------------------------------------------------------
// titleMain.cpp (0x001EB02C), 524 B
// ---------------------------------------------------------------------------

//
__attribute__((naked)) void titleMain_func_001eb02c(const u8*) {
    asm volatile(
        ".arm\n"
        "push {r4, r5, r6, r7, lr}\n"
        "mov r5, r0\n"
        "sub sp, sp, #0x14\n"
        "ldr r1, [pc, #0x170]\n"
        "add r0, pc, #0x170\n"
        "mov r0, r0\n"
        "mov r7, #1\n"
        "mov r3, #0xa0\n"
        "mov r2, #0\n"
        "mov r1, #0x100\n"
        "mov r0, #0x10000\n"
        "str r7, [sp]\n"
        ".word 0xeb036923\n" // bl 0x002c54f0: AsdMem_AllocAlign
        "ldr r1, [pc, #0x180]\n"
        "mov r6, #0\n"
        "vldr s0, [pc, #0x17c]\n"
        "mov r4, r0\n"
        "str r0, [r1]\n"
        "str r6, [r0, #8]\n"
        "str r6, [r0, #0xc]\n"
        "strb r7, [r0, #0x10]\n"
        "strb r7, [r0, #0x60]\n"
        "vstr s0, [r0, #0x40]\n"
        "vstr s0, [r0, #0x44]\n"
        "vstr s0, [r0, #0x48]\n"
        "vstr s0, [r0, #0x4c]\n"
        "vstr s0, [r0, #0x50]\n"
        "vstr s0, [r0, #0x54]\n"
        "vstr s0, [r0, #0x58]\n"
        "vstr s0, [r0, #0x5c]\n"
        "strb r6, [r0, #0x63]\n"
        "strb r6, [r0, #0x61]\n"
        "mov r1, #2\n"
        "strb r6, [r0, #0x62]\n"
        "str r1, [r0, #0x80]\n"
        "strh r6, [r0, #0x70]\n"
        "strh r6, [r0, #0x72]\n"
        "str r6, [r0, #0x74]\n"
        "str r6, [r0, #0x78]\n"
        "vstr s0, [r0, #0x64]\n"
        "vstr s0, [r0, #0x68]\n"
        "strb r6, [r0, #0x7c]\n"
        "strb r7, [r0, #0x84]\n"
        "strb r6, [r0, #0x86]\n"
        "strb r7, [r0, #0x85]\n"
        "strb r6, [r0, #0x96]\n"
        "strb r6, [r0, #0x94]\n"
        "vstr s0, [r0, #0x98]\n"
        "strb r6, [r0, #0x95]\n"
        "cmp r5, #0\n"
        "strb r6, [r4, #4]\n"
        "beq .Ltitle_main_after_arg\n"
        "ldrb r0, [r5]\n"
        "strb r0, [r4, #0x95]\n"
        "strb r6, [r4, #0x10]\n"
        ".Ltitle_main_after_arg:\n"
        "ldr r1, [pc, #0xe4]\n"
        "ldr r0, [pc, #0xdc]\n"
        "add r5, sp, #4\n"
        "str r1, [sp]\n"
        "mov r3, #0\n"
        "stm r5, {r0, r6}\n"
        "mov r2, r3\n"
        "mov r1, #2\n"
        "add r0, pc, #0xc8\n"
        ".word 0xeb036a11\n" // bl 0x002c5978: AsdTask_CreateCalc
        "ldr r1, [pc, #0xc8]\n"
        "str r0, [r4]\n"
        "mov r3, #0\n"
        "stm sp, {r1, r6}\n"
        "str r0, [sp, #0xc]\n"
        "mov r2, r3\n"
        "mov r1, #0x76\n"
        "add r0, pc, #0xb0\n"
        "str r6, [sp, #8]\n"
        ".word 0xeb0366a9\n" // bl 0x002c4c00: AsdTask_CreateDraw
        "ldr r1, [pc, #0xb4]\n"
        "ldr r0, [r4]\n"
        "mov r3, #0\n"
        "stm sp, {r1, r6}\n"
        "str r0, [sp, #0xc]\n"
        "mov r2, r3\n"
        "mov r1, #0xd4\n"
        "add r0, pc, #0x9c\n"
        "str r6, [sp, #8]\n"
        ".word 0xeb03669f\n" // bl 0x002c4c00: AsdTask_CreateDraw
        "ldr r1, [pc, #0xa4]\n"
        "ldr r0, [r4]\n"
        "mov r3, #0\n"
        "stm sp, {r1, r6}\n"
        "str r0, [sp, #0xc]\n"
        "mov r2, r3\n"
        "mov r1, #0xe7\n"
        "add r0, pc, #0x8c\n"
        "str r6, [sp, #8]\n"
        ".word 0xeb036695\n" // bl 0x002c4c00: AsdTask_CreateDraw
        "add sp, sp, #0x14\n"
        "pop {r4, r5, r6, r7, pc}\n"
        ".word 0x00000105\n"
        ".asciz \"c:\\\\SMT4\\\\XRD686\\\\sdds4\\\\program\\\\title\\\\titleMain.cpp\"\n"
        ".balign 4, 0\n"
        ".word 0x0044e300\n"
        ".word 0x00000000\n"
        ".word 0x002ca6f4\n"
        ".word 0x001e989c\n"
        ".asciz \"TITLE C\"\n"
        ".balign 4, 0\n"
        ".word 0x0020fd5c\n"
        ".asciz \"TITLE UDrawLeft\"\n"
        ".balign 4, 0\n"
        ".word 0x0021f36c\n"
        ".asciz \"TITLE UDrawRight\"\n"
        ".balign 4, 0\n"
        ".word 0x002ca7a8\n"
        ".asciz \"TITLE D\"\n"
        ".balign 4, 0\n"
    );
}
// DECOMP_FUNC(0x001dafbc, 668)


// ---------------------------------------------------------------------------
// tmnlMain.cpp (0x001DAFBC), 668 B
// ---------------------------------------------------------------------------

//
__attribute__((naked)) void tmnlMain_func_001dafbc(const u32*) {
    asm volatile(
        ".arm\n"
        "push {r4, r5, r6, r7, lr}\n"
        "mov r5, r0\n"
        "sub sp, sp, #0x14\n"
        "mov r1, #0xf9\n"
        "add r0, pc, #0x214\n"
        "mov r0, r0\n"
        "mov r7, #1\n"
        "mov r1, #0x100\n"
        "ldr r3, [pc, #0x238]\n"
        "mov r2, #0\n"
        "mov r0, r1\n"
        "str r7, [sp]\n"
        ".word 0xeb03a6e4\n" // bl 0x002c4b84: AsdMem_Alloc
        "ldr r1, [pc, #0x228]\n"
        "mov r4, r0\n"
        "str r0, [r1]\n"
        "mov r0, #0xa\n"
        ".word 0xeb0221dc\n" // bl 0x00263778: UiInput_TestFlag
        "cmp r0, #0\n"
        "bne .Ltmnl_after_flag_a\n"
        "mov r0, #0xa\n"
        "mov r1, #1\n"
        ".word 0xeb0221c6\n" // bl 0x00263734: UiInput_SetFlag
        ".Ltmnl_after_flag_a:\n"
        "mov r0, #0xc\n"
        ".word 0xeb0221d5\n" // bl 0x00263778: UiInput_TestFlag
        "cmp r0, #0\n"
        "nop\n"
        "bne .Ltmnl_after_flag_c\n"
        "mov r0, #0xc\n"
        "mov r1, #1\n"
        ".word 0xeb0221be\n" // bl 0x00263734: UiInput_SetFlag
        ".Ltmnl_after_flag_c:\n"
        "mov r0, #0xb\n"
        ".word 0xeb0221cd\n" // bl 0x00263778: UiInput_TestFlag
        "cmp r0, #0\n"
        "nop\n"
        "bne .Ltmnl_after_flag_b\n"
        "ldr r0, [pc, #0x1d0]\n"
        ".word 0xeb0396d4\n" // bl 0x002c0ba8: Flag_CheckEventBit
        "cmp r0, #0\n"
        "nop\n"
        "beq .Ltmnl_after_flag_b\n"
        "mov r0, #0xb\n"
        "mov r1, #1\n"
        ".word 0xeb0221b1\n" // bl 0x00263734: UiInput_SetFlag
        ".Ltmnl_after_flag_b:\n"
        "ldr r0, [pc, #0x1b4]\n"
        "mov r2, #1\n"
        "mov r1, #0\n"
        ".word 0xeb02ba51\n" // bl 0x002899c4: ScriptVm_SetFlag
        "mov r6, #0\n"
        "strb r7, [r4, #5]\n"
        "str r6, [r4, #0x10]\n"
        "str r6, [r4, #0x14]\n"
        "strb r6, [r4, #9]\n"
        "str r6, [r4, #0xc]\n"
        "str r6, [r4, #0x20]\n"
        "str r6, [r4, #0x24]\n"
        "str r6, [r4, #0x28]\n"
        "str r6, [r4, #0x2c]\n"
        "str r6, [r4, #0x30]\n"
        "str r6, [r4, #0x34]\n"
        "str r6, [r4, #0x38]\n"
        "str r6, [r4, #0x3c]\n"
        "str r6, [r4, #0x40]\n"
        "str r6, [r4, #0x44]\n"
        "str r6, [r4, #0x550]\n"
        "strb r6, [r4, #0x554]\n"
        "str r6, [r4, #0x558]\n"
        "str r6, [r4, #0x568]\n"
        "str r6, [r4, #0x564]\n"
        "str r6, [r4, #0x574]\n"
        "str r6, [r4, #0x570]\n"
        "str r6, [r4, #0x580]\n"
        "str r6, [r4, #0x57c]\n"
        "str r6, [r4, #0x58c]\n"
        "mov r0, #0\n"
        "str r6, [r4, #0x588]\n"
        ".word 0xeb033113\n" // bl 0x002a7540: Ui_SetEntryLock
        "cmp r5, #0\n"
        "strb r6, [r4, #4]\n"
        "beq .Ltmnl_no_boot_arg\n"
        "ldr r0, [r5]\n"
        "mov r1, #1\n"
        "and r0, r0, #0xff\n"
        "strb r0, [r4, #9]\n"
        "strb r6, [r4, #5]\n"
        ".word 0xeb022187\n" // bl 0x00263734: UiInput_SetFlag
        "mov r1, #1\n"
        "mov r0, #0x1c\n"
        ".word 0xeb0303f6\n" // bl 0x0029c0fc: Camp_AddProgressValue
        "str r6, [r4, #0x10]\n"
        "str r6, [r4, #0x14]\n"
        "b .Ltmnl_setup_tasks\n"
        ".Ltmnl_no_boot_arg:\n"
        "str r6, [r4, #0x14]\n"
        "mov r1, #0xff\n"
        "mov r0, #0\n"
        "str r7, [r4, #0x10]\n"
        ".word 0xeb029f4a\n" // bl 0x00282e6c: UiAnimSlot_SetState
        ".Ltmnl_setup_tasks:\n"
        "ldr r1, [pc, #0xe8]\n"
        "ldr r0, [pc, #0xe0]\n"
        "add r5, sp, #4\n"
        "str r1, [sp]\n"
        "mov r3, #0\n"
        "stm r5, {r0, r6}\n"
        "mov r2, r3\n"
        "mov r1, #2\n"
        "add r0, pc, #0xcc\n"
        ".word 0xeb03aa03\n" // bl 0x002c5978: AsdTask_CreateCalc
        "ldr r1, [pc, #0xcc]\n"
        "str r0, [r4]\n"
        "mov r3, #0\n"
        "stm sp, {r1, r6}\n"
        "str r0, [sp, #0xc]\n"
        "mov r2, r3\n"
        "mov r1, #0x75\n"
        "add r0, pc, #0xb4\n"
        "str r6, [sp, #8]\n"
        ".word 0xeb03a69b\n" // bl 0x002c4c00: AsdTask_CreateDraw
        "ldr r1, [pc, #0xb0]\n"
        "ldr r0, [r4]\n"
        "mov r3, #0\n"
        "stm sp, {r1, r6}\n"
        "str r0, [sp, #0xc]\n"
        "mov r2, r3\n"
        "mov r1, #0xd3\n"
        "add r0, pc, #0x8c\n"
        "str r6, [sp, #8]\n"
        ".word 0xeb03a691\n" // bl 0x002c4c00: AsdTask_CreateDraw
        "ldr r1, [pc, #0x8c]\n"
        "ldr r0, [r4]\n"
        "mov r3, #0\n"
        "stm sp, {r1, r6}\n"
        "str r0, [sp, #0xc]\n"
        "mov r2, r3\n"
        "mov r1, #0xe7\n"
        "add r0, pc, #0x74\n"
        "str r6, [sp, #8]\n"
        ".word 0xeb03a687\n" // bl 0x002c4c00: AsdTask_CreateDraw
        "add sp, sp, #0x14\n"
        "pop {r4, r5, r6, r7, pc}\n"
        ".asciz \"c:\\\\SMT4\\\\XRD686\\\\sdds4\\\\program\\\\Terminal\\\\tmnlMain.cpp\"\n"
        ".balign 4, 0\n"
        ".word 0x000005e8\n"
        ".word 0x00432ce0\n"
        ".word 0x00000277\n"
        ".word 0x00000465\n"
        ".word 0x0021f240\n"
        ".word 0x001d98c4\n"
        ".asciz \"TMNL C\"\n"
        ".balign 4, 0\n"
        ".word 0x001fe198\n"
        ".asciz \"TMNL UD\"\n"
        ".balign 4, 0\n"
        ".word 0x002e08d4\n"
        ".word 0x0021f258\n"
        ".asciz \"TMNL DD\"\n"
        ".balign 4, 0\n"
    );
}

} // namespace smt4::camp
