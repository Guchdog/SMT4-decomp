#pragma once
#include <cstddef>
#include "types.h"

/**
 * Camp CEC (SpotPass / "Cec") editor, main menu, view and settings workspaces.
 *
 * The four functions reconstructed in `src/camp/camp_cec.cpp` come from the
 * three original translation units named by the inline `ADR` strings:
 *
 *   CampCecEdit     c:\SMT4\XRD686\sdds4\program\camp\CampCec\CampCecEdit.cpp
 *   CampCec         c:\SMT4\XRD686\sdds4\program\camp\CampCec\CampCec.cpp
 *   CampCecView     c:\SMT4\XRD686\sdds4\program\camp\CampCec\CampCecView.cpp
 *   CampCecSetting  c:\SMT4\XRD686\sdds4\program\camp\CampCec\CampCecSetting.cpp
 *
 * Every allocation size below is the immediate passed to AsdMem_Alloc in the
 * listing, and every field carries the store/load that proves its offset.
 */

namespace smt4::camp {

/**
 * One 0x14-byte CEC row view.  The loops at 0x002D6A60 (3 entries at +0x3C),
 * 0x002D6A88 (2 entries at +0x14) and 0x002D6AA8 (one at +0x8C) zero the
 * record with `AsdWork_Zero(record, 0x14)` and then set `+0x04 = 0x14A`
 * (`str r7,[r6,#0x40]`, r7 = 0x14A, 0x002D6A7C; also 0x002D6AB4).
 */
struct CecRowView {
    u32 field_00;
    u32 field_04;                       // +0x04: default row id 0x14A
    u32 field_08;
    u32 field_0c;
    u32 field_10;
};
static_assert(sizeof(CecRowView) == 0x14);

/**
 * CampCecEdit workspace (`g_CecEditWork`, 0x0043DAD0).
 * Allocated as exactly 0x160 bytes and zeroed:
 * `mov r3,#0x160` (0x002D67BC), `mov r1,#0x160` (0x002D67D8).
 */
struct CecEditWork {
    void* calc_task;                    // +0x000: `str r0,[r4]` (0x002D6808)
    void* panel_base;                   // +0x004: 0x0024ABFC = g_CecWork + 0xA0
    void* menu_root;                    // +0x008: 0x0025487C = g_CecWork + 0x48
    void* text_block;                   // +0x00C: 0x00309DB8 (0x10-byte text block)
    void* list_block;                   // +0x010: 0x0031B9AC (0x98-byte list block)
    CecRowView grid[2];                 // +0x014..+0x03C: 2 records (loop at 0x002D6A88)
    CecRowView rows[3];                 // +0x03C..+0x078: 3 records (loop at 0x002D6A60)
    u8  pad_078[0x14];                  // +0x078..+0x08C
    CecRowView single;                  // +0x08C..+0x0A0 (0x002D6AA8/0x002D6AB4)
    u8  pad_0a0[4];                     // +0x0A0..+0x0A4
    u32 script_bf;                      // +0x0A4: "camp/CecEdit_scr.bf" (0x002D69F4)
    u32 msg_mbm;                        // +0x0A8: "camp/CecEdit_msg.mbm" (0x002D6A04)
    u32 one_msg_mbm;                    // +0x0AC: "camp/CecEdit_one_msg.mbm" (0x002D6A14)
    void* text_handle;                  // +0x0B0: AsdText_CreateDefault(0) (0x002D6A30)
    u32 handlers[9];                    // +0x0B4..+0x0D8: state callbacks (0x002D6924..0x002D697C)
    u32 field_d8;                       // +0x0D8 = 0
    u32 field_dc;                       // +0x0DC = 1
    u32 field_e0;                       // +0x0E0 = 2
    u32 field_e4;                       // +0x0E4 = 9
    u32 field_e8;                       // +0x0E8 = 4
    u32 field_ec;                       // +0x0EC = 5
    u32 field_f0;                       // +0x0F0 = 6
    u32 field_f4;                       // +0x0F4 = 7
    u32 field_f8;                       // +0x0F8 = 8
    u32 field_fc;                       // +0x0FC = 3
    s32 field_100;                      // +0x100 = -1 (`stm r1,{r0,r8}`, 0x002D68DC)
    u32 field_104;                      // +0x104 = 0
    s32 field_108;                      // +0x108 = -1 (0x002D68D0)
    u32 field_10c;                      // +0x10C = 0
    s32 field_110;                      // +0x110 = -1 (0x002D68CC)
    s32 field_114;                      // +0x114 = -1 (0x002D68D8)
    u32 field_118;                      // +0x118 = 0 (0x002D68E8)
    u32 available_count;                // +0x11C: incremented per available entry (0x002D6CC0)
    u8  pad_120[8];                     // +0x120..+0x128
    u8  flag_128;                       // +0x128 = 1 (`strb r6`, r6 = 1, 0x002D68E4)
    u8  arg_129;                        // +0x129 = init argument low byte (0x002D68EC)
    u8  field_12a;                      // +0x12A = 0
    u8  pad_12b;
    u32 field_12c;                      // +0x12C = 0
    u8  pad_130[4];                     // +0x130..+0x134
    u32 field_134;                      // +0x134 = 0
    u32 field_138;                      // +0x138 = 0x10 (`stm r3,{r1,r8}`, 0x002D6900)
    u32 field_13c;                      // +0x13C = 0
    u8  pad_140;
    u8  flag_141;                       // +0x141 = 0
    u8  pad_142[2];
    s32 field_144;                      // +0x144 = -0x38 (`mvn r2,#0x37`, 0x002D6910)
    u32 field_148;                      // +0x148 = 0
    u8  pad_14c[4];                     // +0x14C..+0x150
    u32 field_150;                      // +0x150 = 0
    u32 field_154;                      // +0x154 = 0
    u32 field_158;                      // +0x158 = 0
    s32 field_15c;                      // +0x15C = -1 (0x002D6920)
};
static_assert(offsetof(CecEditWork, panel_base) == 0x004);
static_assert(offsetof(CecEditWork, text_block) == 0x00C);
static_assert(offsetof(CecEditWork, list_block) == 0x010);
static_assert(offsetof(CecEditWork, grid) == 0x014);
static_assert(offsetof(CecEditWork, rows) == 0x03C);
static_assert(offsetof(CecEditWork, single) == 0x08C);
static_assert(offsetof(CecEditWork, script_bf) == 0x0A4);
static_assert(offsetof(CecEditWork, handlers) == 0x0B4);
static_assert(offsetof(CecEditWork, field_100) == 0x100);
static_assert(offsetof(CecEditWork, available_count) == 0x11C);
static_assert(offsetof(CecEditWork, flag_128) == 0x128);
static_assert(offsetof(CecEditWork, field_144) == 0x144);
static_assert(offsetof(CecEditWork, field_15c) == 0x15C);
static_assert(sizeof(CecEditWork) == 0x160);   // `mov r3,#0x160` (0x002D67BC)

/**
 * CampCec main menu workspace (`g_CecWork`, 0x0043DAA8).
 * Allocated as exactly 0xD7C bytes: `ldr r5,=0xD7C` (0x001FFB04) is passed as
 * both the allocation size (`mov r3,r5`, 0x001FFB24) and the zero size
 * (`mov r1,r5`, 0x001FFB40).
 */
struct CecWork {
    void* calc_task;                    // +0x000: `str r0,[r4]` (0x001FFB70)
    u32 field_04;                       // +0x004 (not written here)
    u32 handlers[14];                   // +0x008..+0x040: state callbacks (0x001FFBD4..0x001FFC40)
    u32 field_40;                       // +0x040 (not written here)
    u32 field_44;                       // +0x044 = 0x00220EAC (0x001FFC44)
    u8  pad_048[0xBDC];                 // +0x048..+0xC24
    s32 field_c24;                      // +0xC24 = -1 (`stm r2,{r1,r6}`, 0x001FFBC4)
    u32 field_c28;                      // +0xC28 = 0
    u8  pad_c2c[0xC8];                  // +0xC2C..+0xCF4
    u32 script_bf;                      // +0xCF4: "camp/CecMain_scr.bf" (0x001FFC7C)
    u32 msg_mbm;                        // +0xCF8: "camp/CecMain_msg.mbm" (0x001FFC90)
    u8  pad_cfc[0x2C];                  // +0xCFC..+0xD28
    u32 state_d28;                      // +0xD28 = 0x0D (0x001FFCA8)
    s32 field_d2c;                      // +0xD2C = -1 (0x001FFBCC)
    s32 field_d30;                      // +0xD30 = -1 (0x001FFBD0)
    u32 field_d34;                      // +0xD34 = 0
    u8  pad_d38[0x24];                  // +0xD38..+0xD5C
    u32 mode;                           // +0xD5C: 0/1/2 (0x001FFC48..0x001FFC68)
    u8  pad_d60;
    u8  flag_d61;                       // +0xD61 = 0 (0x001FFCBC)
    u8  flag_d62;                       // +0xD62 = 1 (0x001FFCC0)
    u8  flag_d63;                       // +0xD63 = 0 (0x001FFCC8)
    u8  flag_d64;                       // +0xD64 = 0 (0x001FFC70)
    u8  flag_d65;                       // +0xD65 = 0 (0x001FFD34)
    u8  pad_d66[2];
    u32 field_d68;                      // +0xD68 = 0 (0x001FFD40)
    void* heap;                         // +0xD6C: AsdMemory_func_002c23f8(0x18) (0x001FFD98)
    u8  thread_result[8];               // +0xD70: AsdThread_Create out block
    void* thread_buffer;                // +0xD78: AsdWork_Alloc(...,0x1000,...) (0x001FFD64)
};
static_assert(offsetof(CecWork, handlers) == 0x008);
static_assert(offsetof(CecWork, field_c24) == 0xC24);
static_assert(offsetof(CecWork, state_d28) == 0xD28);
static_assert(offsetof(CecWork, mode) == 0xD5C);
static_assert(offsetof(CecWork, heap) == 0xD6C);
static_assert(offsetof(CecWork, thread_buffer) == 0xD78);
static_assert(sizeof(CecWork) == 0xD7C);

/**
 * CampCecView workspace (`g_CecViewWork`, 0x0043DB10).
 * Allocated as exactly 0x16C bytes: `mov r3,#0x16C` (0x002D7440),
 * `mov r1,#0x16C` (0x002D7458).
 */
struct CecViewWork {
    void* calc_task;                    // +0x000 (0x002D7484)
    u32 field_04;                       // +0x004
    void* panel_base;                   // +0x008 = 0x0024ABFC (0x002D75BC)
    void* current_row;                  // +0x00C = 0x0026F25C([+0x13C]) (0x002D75CC)
    u8  pad_010[0x90];                  // +0x010..+0x0A0
    CecRowView grid_a[2];               // +0x0A0..+0x0C8 (loop at 0x002D76A4)
    CecRowView grid_b[5];               // +0x0C8..+0x12C (loop at 0x002D76CC)
    void* text_blocks[3];               // +0x12C..+0x138 (loop at 0x002D75D0)
    void* list_block;                   // +0x138: 0x0031B9AC (0x002D75F0)
    s32 field_13c;                      // +0x13C = 0 (0x002D7554)
    u32 field_140;                      // +0x140 = 0 (0x002D7558)
    u32 field_144;                      // +0x144 = 0 (0x002D755C)
    u32 visible_count;                  // +0x148 = 0, +1 per row with [+0x48] != 0 (0x002D7588)
    u32 field_14c;                      // +0x14C = current row (0x002D769C)
    u32 field_150;                      // +0x150 = 0 (0x002D7564)
    u8  pad_154[0xC];                   // +0x154..+0x160
    u32 one_msg_mbm;                    // +0x160: "camp/CecEdit_one_msg.mbm" (0x002D75A0)
    u8  flag_164;                       // +0x164 = 0 (0x002D7568)
    u8  flag_165;                       // +0x165 = 0 (0x002D756C)
    u8  pad_166[2];
    u32 field_168;                      // +0x168 = 0 (0x002D7570)
};
static_assert(offsetof(CecViewWork, grid_a) == 0x0A0);
static_assert(offsetof(CecViewWork, grid_b) == 0x0C8);
static_assert(offsetof(CecViewWork, text_blocks) == 0x12C);
static_assert(offsetof(CecViewWork, list_block) == 0x138);
static_assert(offsetof(CecViewWork, visible_count) == 0x148);
static_assert(offsetof(CecViewWork, one_msg_mbm) == 0x160);
static_assert(sizeof(CecViewWork) == 0x16C);

/**
 * CampCecSetting workspace (`g_CecSettingWork`, 0x0043DAF8).
 * Allocated as exactly 0x44 bytes: `mov r3,#0x44` (0x002F5BEC),
 * `mov r1,#0x44` (0x002F5C08).
 */
struct CecSettingWork {
    void* calc_task;                    // +0x000 (0x002F5C34)
    u32 field_04;                       // +0x004
    u32 script_bf;                      // +0x008: "camp/CecSetting_scr.bf" (0x002F5C8C)
    u32 msg_mbm;                        // +0x00C: "camp/CecSetting_msg.mbm" (0x002F5C9C)
    u32 field_10;                       // +0x010 = 0 (`stm r1,{r5,r6}`, 0x002F5CD4)
    u32 field_14;                       // +0x014 = 1
    u32 table_a[5];                     // +0x018..+0x02C = {2,3,4,5,6} (0x002F5CC8)
    u32 field_2c;                       // +0x02C = 10 (`stm r4,{r7,r8,sb}`, 0x002F5CE4)
    u32 field_30;                       // +0x030 = 7
    u32 field_34;                       // +0x034 = 11
    u32 field_38;                       // +0x038 = 0 (0x002F5CB0)
    u8  field_3c;                       // +0x03C = 2 (`strb r0`, 0x002F5CC4)
    u8  pad_3d[7];                      // +0x03D..+0x044
};
static_assert(offsetof(CecSettingWork, table_a) == 0x018);
static_assert(offsetof(CecSettingWork, field_2c) == 0x02C);
static_assert(offsetof(CecSettingWork, field_38) == 0x038);
static_assert(sizeof(CecSettingWork) == 0x44);

extern CecEditWork* g_CecEditWork;      // 0x0043DAD0
extern CecWork* g_CecWork;              // 0x0043DAA8
extern CecViewWork* g_CecViewWork;      // 0x0043DB10
extern CecSettingWork* g_CecSettingWork;// 0x0043DAF8

/**
 * A CEC message row.  Only +0x48 is read by these functions: the row-count
 * loops test the halfword (`ldrh r0,[r0,#0x48]`, 0x002D757C / 0x002D760C).
 */
struct CecMessageRow {
    u8  pad_00[0x48];
    u16 field_48;                       // +0x48: non-zero selects the row
    u8  pad_4a[2];
};
static_assert(offsetof(CecMessageRow, field_48) == 0x48);

// Camp CEC API (`src/camp/camp_cec.cpp`)
void CampCecEdit_func_002d678c(void* arg);      // 0x002D678C
void CampCec_func_001ffaf4(void* arg);          // 0x001FFAF4
void CampCecView_func_002d7410(void* arg);      // 0x002D7410
void CampCecSetting_func_002f5bc0(void* arg);   // 0x002F5BC0

// Task/draw entry points referenced by the AsdProcess callback words above.
// These are function entries that the linear ledger folds into the preceding
// row (or lists under a generic name); the addresses are the literal values
// stored by the constructors.
void CampCecEdit_Calc(void* arg);               // 0x001C0DFC
void CampCecEdit_DrawBase(void* arg);           // 0x001EBCCC
void CampCecEdit_DrawUp(void* arg);             // 0x001C0D9C
void CampCecEdit_DrawDown(void* arg);           // 0x00210D3C (ledger: ui_func_00210d3c)
void CampCec_Calc(void* arg);                   // 0x0018B10C
void CampCec_DrawUp(void* arg);                 // 0x0018AF6C (ledger: ui_func_0018af6c)
void CampCecView_Calc(void* arg);               // 0x001C0F14 (ledger: ui_func_001c0f14)
void CampCecView_DrawBase(void* arg);           // 0x001EC8C0
void CampCecView_DrawUp(void* arg);             // 0x001C0EB0
void CampCecView_DrawDown(void* arg);           // 0x00211484 (ledger: ui_func_00211484)
void CampCecSetting_Calc(void* arg);            // 0x001FFF64
void CampCecSetting_DrawUp(void* arg);          // 0x001FFF48

} // namespace smt4::camp
