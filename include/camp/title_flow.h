#pragma once
#include <cstddef>
#include "types.h"
#include "ui/status_down.h"

/**
 * Title / config / play-log / terminal flows reconstructed in
 * `src/camp/title_flow.cpp`.
 *
 * The original translation units are named by the inline `ADR` strings:
 *
 *   PlayLog      c:\SMT4\XRD686\sdds4\program\camp\PlayLog\PlayLog.cpp
 *   titleConfig  c:\SMT4\XRD686\sdds4\program\title\titleConfig.cpp
 *   Config       c:\SMT4\XRD686\sdds4\program\camp\Config\Config.cpp
 *   titleMain    c:\SMT4\XRD686\sdds4\program\title\titleMain.cpp
 *   tmnlMain     c:\SMT4\XRD686\sdds4\program\Terminal\tmnlMain.cpp
 *
 * Allocation sizes are the immediates passed to AsdMem_Alloc/AllocAlign and
 * every field carries the instruction that proves its offset.
 */

namespace smt4::camp {

/**
 * 0x20-byte sprite group cleared by 0x002C3344 (`UiSpriteGroup_Init`) and
 * filled by 0x002C32F8 (`UiSpriteGroup_BindTable`).
 */
struct FlowSpriteGroup {
    u8 raw[0x20];
};
static_assert(sizeof(FlowSpriteGroup) == 0x20);

/**
 * PlayLog workspace (`g_PlayLogWork`, 0x0043DD08).
 * Allocated as exactly 0x488 bytes: `ldr r6,=0x488` (0x00194DC8),
 * `mov r1,r6` (0x00194E0C).
 */
struct PlayLogWork {
    FlowSpriteGroup sprite_group;       // +0x000: UiSpriteGroup_Init(work) (0x00194E44)
    ui::UiAnimSprite sprites[5];        // +0x020..+0x2DC: 5 * 0x8C (loop 0x00194E80)
    ui::UiListCursor list_cursor;       // +0x2DC..+0x340: UiListCursor_Setup(work+0x2DC) (0x00194FA8)
    u8  pad_340[4];                     // +0x340..+0x344
    u32 field_344;                      // +0x344 = 0 (0x00194E1C)
    u8  pad_348[0x14];                  // +0x348..+0x35C
    // The two arrays fill the gap to the end of the 0x488 allocation exactly:
    // 0x424-0x35C = 0xC8 = 50 words and 0x488-0x424 = 0x64 = 50 halfwords.
    u32 entry_values[50];               // +0x35C..+0x424 (indexed by `str r0,[r1,#0x35c]`)
    u16 visible_indices[50];            // +0x424..+0x488 (`strh r4,[r0,#0x24]`, base work+0x400)
};
static_assert(offsetof(PlayLogWork, sprites) == 0x020);
static_assert(offsetof(PlayLogWork, list_cursor) == 0x2DC);
static_assert(offsetof(PlayLogWork, field_344) == 0x344);
static_assert(offsetof(PlayLogWork, entry_values) == 0x35C);
static_assert(offsetof(PlayLogWork, visible_indices) == 0x424);
static_assert(sizeof(PlayLogWork) == 0x488);   // `ldr r6,=0x488` (0x00194DC8)

/**
 * titleConfig workspace (`g_TitleConfigWork`, 0x0044E2D0).
 * Allocated as exactly 0x158 bytes: `mov r3,#0x158` (0x002F4CBC).
 */
struct TitleConfigWork {
    void* calc_task;                    // +0x000 (0x002F4D10)
    u32 field_04;                       // +0x004
    u32 field_08;                       // +0x008 = 0 (0x002F4DB4)
    u32 field_0c;                       // +0x00C
    u32 field_10;                       // +0x010
    u16 field_14;                       // +0x014
    u16 field_16;                       // +0x016
    u16 field_18;                       // +0x018
    u16 field_1a;                       // +0x01A = 0 (`strh r5`, 0x002F4DC0)
    s32 field_1c;                       // +0x01C = -1 (0xFF byte fill, 0x002F4DC4)
    s32 field_20;                       // +0x020 = -1
    u16 field_24;                       // +0x024 = 0 (`strh r5`, 0x002F4DD4)
    u16 pad_26;
    u32 field_28;                       // +0x028 = map(config[0]) (0x002F4E0C)
    u32 field_2c;                       // +0x02C = map(config[1]) (0x002F4E18)
    u32 field_30;                       // +0x030 = map(config[2]) (0x002F4E24)
    u32 field_34;                       // +0x034 = config word 0 (0x002F4E3C)
    u32 field_38;                       // +0x038 = config word 1
    FlowSpriteGroup sprite_group;       // +0x03C..+0x05C (0x002F4D34)
    ui::UiAnimSprite sprite;            // +0x05C..+0x0E8 (0x002F4D88)
    ui::UiListCursor list_cursor;       // +0x0E8..+0x14C (0x002F4DAC)
    u32 script_bf;                      // +0x14C: "camp/config.bf" (0x002F4DD8)
    u32 msg_mbm;                        // +0x150: "camp/config.mbm" (0x002F4DE8)
    u8  pad_154[4];                     // +0x154..+0x158
};
static_assert(offsetof(TitleConfigWork, field_1a) == 0x01A);
static_assert(offsetof(TitleConfigWork, field_1c) == 0x01C);
static_assert(offsetof(TitleConfigWork, field_28) == 0x028);
static_assert(offsetof(TitleConfigWork, sprite_group) == 0x03C);
static_assert(offsetof(TitleConfigWork, sprite) == 0x05C);
static_assert(offsetof(TitleConfigWork, list_cursor) == 0x0E8);
static_assert(offsetof(TitleConfigWork, script_bf) == 0x14C);
static_assert(sizeof(TitleConfigWork) == 0x158);

/**
 * Config workspace (`g_ConfigWork`, 0x0043DC58).
 * Allocated as exactly 0xBC bytes: `mov r3,#0xbc` (0x0018B68C),
 * `mov r1,#0xbc` (0x0018B6A8).
 */
struct ConfigWork {
    ui::UiListCursor list_cursor;       // +0x000..+0x064: UiListCursor_Setup(work,...) (0x0018B738)
    u32 field_64;                       // +0x064 = 0 (0x0018B6B4)
    u8  pad_68[0x18];                   // +0x068..+0x080
    u32 field_80;                       // +0x080: 0/1/2 selection (0x0018B7E4)
    u8  pad_84[0x24];                   // +0x084..+0x0A8
    u8  field_a8;                       // +0x0A8: both event bits set (0x0018B804)
    u8  pad_a9[3];                      // +0x0A9..+0x0AC
    u32 script_bf;                      // +0x0AC: "camp/config.bf" (0x0018B6DC)
    u32 msg_mbm;                        // +0x0B0: "camp/config.mbm" (0x0018B6EC)
    u8  pad_b4[8];                      // +0x0B4..+0x0BC
};
static_assert(offsetof(ConfigWork, field_64) == 0x064);
static_assert(offsetof(ConfigWork, field_80) == 0x080);
static_assert(offsetof(ConfigWork, field_a8) == 0x0A8);
static_assert(offsetof(ConfigWork, script_bf) == 0x0AC);
static_assert(sizeof(ConfigWork) == 0xBC);

/**
 * titleMain workspace (`g_TitleMainWork`, 0x0044E300).
 * Allocated as exactly 0xA0 bytes with 0x10000 alignment:
 * `mov r3,#0xa0` / `mov r0,#0x10000` (0x001EB048/0x001EB054).
 */
struct TitleMainWork {
    void* calc_task;                    // +0x000 (0x001EB070)
    u8  flag_04;                        // +0x004 = 0 (0x001EB0F4)
    u8  pad_05[3];
    u32 field_08;                       // +0x008 = 0 (0x001EB074)
    u32 field_0c;                       // +0x00C = 0 (0x001EB078)
    u8  flag_10;                        // +0x010 = 1, or 0 when an argument is supplied
    u8  pad_11[0x2F];                   // +0x011..+0x040
    f32 field_40[8];                    // +0x040..+0x060: eight zero floats (0x001EB084..)
    u8  flag_60;                        // +0x060 = 1 (0x001EB080)
    u8  flag_61;                        // +0x061 = 0 (0x001EB0A8)
    u8  flag_62;                        // +0x062 = 0 (0x001EB0B0)
    u8  flag_63;                        // +0x063 = 0 (0x001EB0A4)
    f32 field_64;                       // +0x064 = 0 (0x001EB0C8)
    f32 field_68;                       // +0x068 = 0 (0x001EB0CC)
    f32 field_6c;                       // +0x06C: `vldr s0,[r0,#0x6c]` (0x001EA778)
    u16 field_70;                       // +0x070 = 0 (0x001EB0B8)
    u16 field_72;                       // +0x072 = 0 (0x001EB0BC)
    u32 field_74;                       // +0x074 = 0 (0x001EB0C0)
    u32 field_78;                       // +0x078 = 0 (0x001EB0C4)
    u8  flag_7c;                        // +0x07C = 0 (0x001EB0D0)
    u8  pad_7d[3];
    u32 field_80;                       // +0x080 = 2 (0x001EB0B4)
    u8  flag_84;                        // +0x084 = 1 (0x001EB0D4)
    u8  flag_85;                        // +0x085 = 1 (0x001EB0DC)
    u8  flag_86;                        // +0x086 = 0 (0x001EB0D8)
    u8  pad_87;                         // +0x087
    u32 resource_88;                    // +0x088: `str r0,[r4,#0x88]` (0x001E9B38)
    u32 resource_8c;                    // +0x08C: `str r0,[r4,#0x8c]` (0x001E9B48)
    u32 resource_90;                    // +0x090: `str r0,[r4,#0x90]` (0x001E9B58)
    u8  flag_94;                        // +0x094 = 0 (0x001EB0E4)
    u8  flag_95;                        // +0x095 = 0, or argument byte (0x001EB0FC)
    u8  flag_96;                        // +0x096 = 0 (0x001EB0E0)
    u8  pad_97;
    f32 field_98;                       // +0x098 = 0 (0x001EB0E8)
    s32 state_9C;                       // +0x09C: `ldr r0,[r5,#0x9c]` (0x001E98B4)
};
static_assert(offsetof(TitleMainWork, flag_04) == 0x004);
static_assert(offsetof(TitleMainWork, field_40) == 0x040);
static_assert(offsetof(TitleMainWork, field_64) == 0x064);
static_assert(offsetof(TitleMainWork, field_70) == 0x070);
static_assert(offsetof(TitleMainWork, field_80) == 0x080);
static_assert(offsetof(TitleMainWork, flag_95) == 0x095);
static_assert(offsetof(TitleMainWork, field_98) == 0x098);
static_assert(offsetof(TitleMainWork, resource_88) == 0x088);
static_assert(offsetof(TitleMainWork, resource_8c) == 0x08C);
static_assert(offsetof(TitleMainWork, resource_90) == 0x090);
static_assert(offsetof(TitleMainWork, state_9C) == 0x09C);
static_assert(sizeof(TitleMainWork) == 0xA0);

/**
 * Terminal main workspace (`g_TerminalMainWork`, 0x00432CE0).
 * Allocated as exactly 0x5E8 bytes: `ldr r3,=0x5e8` (0x001DAFDC).
 */
struct TerminalMainWork {
    void* calc_task;                    // +0x000 (0x001DB16C)
    u8  flag_04;                        // +0x004 = 0 (0x001DB0F4)
    u8  flag_05;                        // +0x005 = 1, or 0 when an argument is supplied
    u8  pad_06[2];
    u8  field_08;                       // +0x008
    u8  flag_09;                        // +0x009 = 0, or argument byte (0x001DB108)
    u8  pad_0a[2];
    u32 field_0c;                       // +0x00C = 0 (0x001DB090)
    u32 field_10;                       // +0x010 = 0 or 1 (0x001DB084/0x001DB138)
    u32 field_14;                       // +0x014 = 0 (0x001DB088)
    u8  pad_18[8];                      // +0x018..+0x020
    u32 field_20[10];                   // +0x020..+0x048: ten zero words (0x001DB094..0x001DB0B8)
    u8  pad_48[0x508];                  // +0x048..+0x550
    u32 field_550;                      // +0x550 = 0 (0x001DB0BC)
    u8  flag_554;                       // +0x554 = 0 (0x001DB0C0)
    u8  pad_555[3];
    u32 field_558;                      // +0x558 = 0 (0x001DB0C4)
    u8  pad_55c[8];                     // +0x55C..+0x564
    u32 field_564;                      // +0x564 = 0 (0x001DB0CC)
    u32 field_568;                      // +0x568 = 0 (0x001DB0C8)
    u8  pad_56c[4];                     // +0x56C..+0x570
    u32 field_570;                      // +0x570 = 0 (0x001DB0D4)
    u32 field_574;                      // +0x574 = 0 (0x001DB0D0)
    u8  pad_578[4];                     // +0x578..+0x57C
    u32 field_57c;                      // +0x57C = 0 (0x001DB0DC)
    u32 field_580;                      // +0x580 = 0 (0x001DB0D8)
    u8  pad_584[4];                     // +0x584..+0x588
    u32 field_588;                      // +0x588 = 0 (0x001DB0E8)
    u32 field_58c;                      // +0x58C = 0 (0x001DB0E0)
    u8  pad_590[0x58];                  // +0x590..+0x5E8
};
static_assert(offsetof(TerminalMainWork, flag_05) == 0x005);
static_assert(offsetof(TerminalMainWork, flag_09) == 0x009);
static_assert(offsetof(TerminalMainWork, field_20) == 0x020);
static_assert(offsetof(TerminalMainWork, field_550) == 0x550);
static_assert(offsetof(TerminalMainWork, flag_554) == 0x554);
static_assert(offsetof(TerminalMainWork, field_588) == 0x588);
static_assert(sizeof(TerminalMainWork) == 0x5E8);

extern PlayLogWork* g_PlayLogWork;              // 0x0043DD08
extern TitleConfigWork* g_TitleConfigWork;      // 0x0044E2D0
extern ConfigWork* g_ConfigWork;                // 0x0043DC58
extern TitleMainWork* g_TitleMainWork;          // 0x0044E300
extern TerminalMainWork* g_TerminalMainWork;    // 0x00432CE0

/**
 * 8-byte persisted option block at 0x0044E0F8.  titleConfig only reads it:
 * bytes 0/1/2 are mapped through three table lookups and then the two words
 * are copied to +0x34.  Its initialiser is written by the save/config loader.
 */
extern u8 g_ConfigBytes[];

// Title/config/play-log/terminal API (`src/camp/title_flow.cpp`)
void PlayLog_func_00194dbc(void* arg);          // 0x00194DBC
void tmnlMain_func_001dafbc(const u32* arg);    // 0x001DAFBC
void titleConfig_func_002f4ca0(void* arg);      // 0x002F4CA0
void Config_func_0018b660(void* arg);           // 0x0018B660
void titleMain_func_001eb02c(const u8* arg);    // 0x001EB02C

// Task/draw entry points stored by the constructors above.  Entries outside
// the ledger are named after the task they service.
void TitleConfig_Calc(void* arg);               // 0x001EA928
void TitleConfig_Secondary();                   // 0x002CAEF0 (CreateCalc a5)
void TitleConfig_Draw(void* arg);               // 0x002CAFD0
void TitleMain_Calc(void* arg);                 // 0x001E989C
extern "C" u32 H1_TitleMain_UpdateNavigationSlice(TitleMainWork** captured_work_out);
extern "C" u32 H1_TitleMain_ProcessConfirmationSlice(TitleMainWork* work);
void TitleMain_Secondary();                     // 0x002CA6F4 (CreateCalc a5)
void TitleMain_DrawLeft(void* arg);             // 0x0020FD5C
void TitleMain_DrawRight(void* arg);            // 0x0021F36C
void TitleMain_DrawDown(void* arg);             // 0x002CA7A8
void Terminal_DrawUp(void* arg);                // 0x001FE198
void Terminal_DrawUpAlt(void* arg);             // 0x002E08D4
void Terminal_DrawDown(void* arg);              // 0x0021F258

} // namespace smt4::camp
