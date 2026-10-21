#pragma once
#include <cstddef>
#include "types.h"
#include "ui/save_load.h"

namespace smt4::ui {

/**
 * Views required by the last four large unnamed `ui` routines of the 21%
 * milestone.  Ledger names are kept unchanged:
 *
 *   0x00214964  save/load two-page slot renderer   (SaveLoadUIWork view)
 *   0x001F1FC8  fusion-candidate list (3 rows + detail)
 *   0x001E989C  titleMain state machine (title/title_top.*)
 *   0x003EB4F4  fixed-point log2 + CRT static-init block
 *
 * The save/load workspace view lives in `ui/save_load.h` (the global at
 * 0x0044DE28 already had an owner); the title workspace view lives in
 * `camp/title_flow.h` (0x0044E300).  Both were extended with the offsets the
 * new listings prove instead of being redeclared here.
 */

// ---------------------------------------------------------------------------
// 0x001F1FC8: fusion-candidate list
// ---------------------------------------------------------------------------

/**
 * One 0x94-byte row returned by Battle_GetTalkEntry (0x002B9364).  0x001F1FC8
 * reads the id at +0x00 (`ldrh r0,[fp]`, 0x001F2BC8 / 0x001F2C3C / 0x001F2D18)
 * and the small counter at +0x03 (`ldrb ip,[ip,#3]`, 0x001F2610).  The
 * descriptor words are not part of this row: they live at
 * `CampFusionView::candidate_pairs_9438` (+0x9438, four 8-byte pairs).  The
 * rest of the 0x94-byte stride is kept as padding.
 */
struct FusionCandidateEntry {
    u16 id;                         // +0x00: `ldrh r0,[fp]` (0x001F2BC8)
    u8  pad_02;
    u8  field_03;                   // +0x03: `ldrb ip,[ip,#3]` (0x001F2610)
    u8  pad_04[0x90];
};
static_assert(offsetof(FusionCandidateEntry, id) == 0x00);
static_assert(offsetof(FusionCandidateEntry, field_03) == 0x03);
static_assert(sizeof(FusionCandidateEntry) == 0x94);

/**
 * 0x001F1FC8: draws the three "FUSION POSSIBLE" rows (group 0x24, nodes
 * 0x4A/0x5C..0x62/0x73) and the selected-row detail (nodes 0x76..0x87).
 *
 * r0 = horizontal offset (`abs(r0) >= 0x140` early-out, 0x001F1FEC),
 * r1 = vertical offset, r2 = selected row (0..2), r3 = detail column used to
 * pick node 0x81/0x7F/0x80 (`ldr r0,[sp,#0x70]`, 0x001F2D9C; the saved-r3
 * slot), 5th argument = touch region handle (`ldr r0,[sp,#0x98]`,
 * 0x001F2854).  Returns nothing.
 */
void ui_func_001f1fc8(s32 x, s32 y, s32 selected, s32 column, s16 touch_handle);

// ---------------------------------------------------------------------------
// 0x00214964: save/load slot renderer
// ---------------------------------------------------------------------------

/**
 * 0x00214964: renders the two save-slot pages of `g_SaveLoadUIManager.work`
 * (0x0044DE28).  Per page it pushes the 0x24C GPU ring
 * (`UiGpu_SetViewportParams(1,0)` + cursor increment, 0x00214A54..0x00214A88),
 * draws the page panel (2/3 for active, 4/5 for empty), the slot name from
 * Tbb group 0x3D (stride 0x54, string at +0x00), the status string at +0x14
 * (only for states 2 and 10: `sub r1,r0,#2; cmp r1,#9; bhs`, 0x0021499C),
 * the play clock (digits drawn from group 0x0D nodes 0xBB8+digit), the four
 * flag icons, and for the selected page the timer value split into thousands
 * /hundreds/tens/units (nodes 0x72/0x71/0x70/0x6F).  It ends with the
 * 0x374-faded model pass (`UiDraw_ModelPass(0,0,0x140,0xF0,0xD3)`) and the
 * nine-position animated digit strip (nodes 0x5F/0x60/0x61).
 */
void ui_func_00214964();

// ---------------------------------------------------------------------------
// 0x001E989C: titleMain state machine
// ---------------------------------------------------------------------------

/**
 * 0x001E989C: the `titleMain.cpp` Calc callback registered by 0x001EB02C.
 * The state word is `TitleMainWork::state_9C`; the 13-way jump table at
 * 0x001E98C4 dispatches states 0..12:
 *
 *   0 -> 0x001E98F8 (load Tbb 0x3A, cache layout nodes 0x12/0x13/0x16/0x17)
 *   1 -> 0x001E9A10 (poll 0x003BCBF8 on work+0x14)
 *   2 -> 0x001E9A3C (create the title 0x3C anim, "title/title_top.*")
 *   3 -> 0x001E9B90 (wait for both .bam loads and the .bccam handle)
 *   4 -> 0x001E9BC0 (build the 3D title camera, bind projection)
 *   5 -> 0x001E9D08 (cursor / blend / four touch regions / fade handoff)
 *   6 -> 0x001EA48C (wait 0x00289924 then state 12)
 *   7 -> 0x001EA32C (0x0030A9A4 hand-off, state 8)
 *   8 -> 0x001EA358 (wait, then reset or state 12)
 *   9 -> 0x001EA398 (0x002F4CA0, state 10)
 *  10 -> 0x001EA3C4 (wait 0x002FC0EC, reset, state 5)
 *  11 -> 0x001EA478 (wait 0x00289924, state 12)
 *  12 -> 0x001EA494 (destroy the task pair, per-state 0/1/2/3 exit)
 *
 * The r0 argument is not read; the callback ABI is `void (*)(void*)`.
 */
void ui_func_001e989c(void* arg);

// ---------------------------------------------------------------------------
// 0x003EB4F4: fixed-point log2 + CRT static-init block
// ---------------------------------------------------------------------------

/**
 * 0x003EB4F4: splits `value_bits` (an IEEE-754 single in an integer register;
 * the routine never reads s0) into an integer exponent and a fractional
 * mantissa.  The exponent byte is `(value_bits << 1) >> 24`, the table at
 * 0x0042027C supplies the Q32 mantissa seed, and the polynomial constants
 * 0x36000000 / 0x2C800000 / 0x29FDAA22 / 0x2FC90FDB / 0x2FC90000 finish the
 * interpolation.  `*out_integer` receives the exponent (`r4`); a negative
 * input negates the result and stores `0x10000000 - exponent`
 * (0x003EB60C..0x003EB61C).  Values whose exponent field is 0xFF — i.e.
 * `(bits << 1) >= 0xFF000000`, which covers NaN/Inf — store 0xFFFFFFFF and
 * return without touching s0 (0x003EB4FC..0x003EB50C).
 */
f32 ui_func_003eb4f4(u32* out_integer, u32 value_bits);

} // namespace smt4::ui
