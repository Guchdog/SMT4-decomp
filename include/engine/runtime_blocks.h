#pragma once
#include <cstddef>
#include "types.h"

/**
 * Four large runtime blocks recovered from the shipped 3DS image.
 *
 * ---------------------------------------------------------------------------
 * 0x003B11A8 (4,548 B) -- event/command dispatch
 * ---------------------------------------------------------------------------
 * The routine consumes two unsigned LEB128 values from the byte stream at
 * `cursor->position` (`func_003b03b0` at 0x003B11CC and 0x003B121C), then
 * either advances the stream or dispatches a command:
 *
 *   - key 0 (`[sp+0x1c]`): `cursor->position += value` and return 0x100
 *     (0x003B1444..0x003B1464).
 *   - otherwise the key selects a 0x24-byte tree node whose +0x18 word is a
 *     polymorphic payload.  The payload compares its +0x08 word with the
 *     decoded value (0x003B1530..0x003B1538), calls its virtual slot 3 with
 *     `(payload, stream_base + index)` (0x003B1548..0x003B1554), then slot 4
 *     (0x003B1560..0x003B156C).  Slot 4 == 0 appends a 16-byte element to the
 *     vector at state+0x1434 (0x003B1B08); slot 4 != 0 walks the tree at
 *     state+0x1414 and creates a 0x74-byte child (0x003B15FC..0x003B1690).
 *
 * Failure paths write the 64/0x40 and 0x10000 words at state+0x1478 and
 * state+0x147C, clear the two bytes at state+0x1487 / state+0x1489 and return
 * 0x43 (0x003B2318..0x003B2360) or 0x45 (0x003B17CC..0x003B1814).  A partial
 * allocation failure returns 0x44 (0x003B2048..0x003B2050).  The success path
 * adds the decoded value to the stream cursor and returns 0 unless the cursor
 * has passed `end`, in which case the 0x43 reset path runs
 * (0x003B22F0..0x003B2318).
 *
 * ---------------------------------------------------------------------------
 * 0x00101308 (4,144 B) -- nnMain / application main loop
 * ---------------------------------------------------------------------------
 * `__start` calls this routine directly (src/crt/start.cpp).  It performs the
 * engine bring-up (graphics, memory, files, sound, texture tables), creates
 * the twenty-three AsdProcess draw tasks, then enters the frame loop whose
 * per-frame state is the 0x00446DB0 block: byte +0x00 (render-ready),
 * byte +0x01 (stereo enabled), byte +0x02 (mode latch), byte +0x03
 * (shutdown), byte +0x04 (timer enabled), word +0x10 (timer), word +0x14
 * (fade timer), word +0x18 (frame load), word +0x1C (stereo counter) and the
 * 64-bit system-tick snapshots at +0x20 and +0x28.
 *
 * ---------------------------------------------------------------------------
 * 0x00142BF0 (4,008 B) -- LCD framebuffer register programming
 * ---------------------------------------------------------------------------
 * `r0` is a render config and `r1` is a screen index (0/1/2).  The routine
 * reads the per-screen availability byte at 0x004655C0->0x104+index and the
 * register block at 0x004655C0->0x770.  Screen 0 uses register words
 * +0x00..+0x14 plus the per-screen control word at +0x38; screens 1 and 2 use
 * +0x44..+0x58 and +0x64..+0x78.  The packed RGBA word (255-scaled floats at
 * config +0x18..+0x24) is stored at channel+0x04.  The framebuffer address is
 * translated by `func_00147994` and the register write is submitted with
 * `func_002aa938(0x81/0x91/0x99, 0x0A/0x06/0x06)`.  Invalid screen indices
 * return 0x501; a missing config returns 0x502.
 *
 * ---------------------------------------------------------------------------
 * 0x002831F0 (3,784 B) -- camp layout byte-stream interpreter
 * ---------------------------------------------------------------------------
 * `r0` is a layout opcode in [9, 24].  The jump table at 0x00283224 selects
 * one of ten handlers; each handler reads a stream of bytes whose low seven
 * bits are a field opcode and whose bit 7 picks one of two copy routines.
 * `camp_func_0029f0f4` resolves the source slot, then the two variants are
 * invoked through the Thumb veneer at 0x002B7F0A with
 * `(destination, resolved_index, 2 or 8)`.  The first eight bytes of every
 * handler are copied with size 8 and the remaining ones with size 2.
 */

namespace smt4::engine {

// ---------------------------------------------------------------------------
// 0x003B11A8 support types
// ---------------------------------------------------------------------------

// 16-byte element of the vector at 0x003B11A8 state+0x1434.  The four words
// are the intrusive left/right/parent/link slots copied at
// 0x003B1B88..0x003B1BA8 and released by func_0022c1cc.
struct ScriptNode16 {
    u32 link_00;    // +0x00
    u32 link_04;    // +0x04
    u32 link_08;    // +0x08
    u32 link_0c;    // +0x0C
};
static_assert(offsetof(ScriptNode16, link_00) == 0x00);
static_assert(offsetof(ScriptNode16, link_04) == 0x04);
static_assert(offsetof(ScriptNode16, link_08) == 0x08);
static_assert(offsetof(ScriptNode16, link_0c) == 0x0C);
static_assert(sizeof(ScriptNode16) == 0x10);

// Vector header at state+0x1434.  `begin` is read at 0x003B1B18, `capacity`
// at 0x003B1B38, and `size` at 0x003B1B14; `owner` is the allocation context
// consumed by func_0022c198/func_0022c6f8.
struct ScriptNodeVector {
    void* owner;            // +0x00
    ScriptNode16* begin;    // +0x04
    u32 capacity;           // +0x08
    u32 size;               // +0x0C
};
static_assert(offsetof(ScriptNodeVector, owner) == 0x00);
static_assert(offsetof(ScriptNodeVector, begin) == 0x04);
static_assert(offsetof(ScriptNodeVector, capacity) == 0x08);
static_assert(offsetof(ScriptNodeVector, size) == 0x0C);
static_assert(sizeof(ScriptNodeVector) == 0x10);

// Byte cursor passed in r2.  `func_003b03b0` increments the word at +0x00
// (`ldr r4,[r2]` / `str r4,[r2]`, 0x003B03B4..0x003B03C8) and returns 0 when
// the cursor reaches the `end` argument (r3).
struct ScriptCursor {
    u32 position;           // +0x00
};
static_assert(offsetof(ScriptCursor, position) == 0x00);

// The large event state rooted in r0.  Only offsets touched by this routine
// are named; every gap is an explicit byte pad.
struct ScriptRuntimeState {
    u32 output_words[4];                // +0x0000 (stm sb, 0x003B17DC)
    u8  channel_table[0x1404];          // +0x0010 (func_003af524 input)
    u8  command_tree[0x0020];           // +0x1414
    ScriptNodeVector nodes;             // +0x1434
    u8  key_tree[0x0028];               // +0x1444
    void* allocator;                    // +0x146C (`ldr r0,[r6]`, 0x003B1240)
    u8  pad_1470[0x0008];               // +0x1470..+0x1477
    u32 output_1478;                    // +0x1478 (`str r4,[r1]`)
    u32 output_147c;                    // +0x147C (`str r5,[r1]`)
    void (*callback_1480)(u32, u32);    // +0x1480 (`ldr r2,[sb,#0x1480]`)
    u8  pad_1484[0x0003];               // +0x1484..+0x1486
    u8  output_1487;                    // +0x1487 (`strb r0,[r1]`)
    u8  pad_1488;                       // +0x1488
    u8  output_1489;                    // +0x1489 (`strb r0,[r1]`)
    u8  pad_148a[0x0002];               // +0x148A..+0x148B
};
static_assert(offsetof(ScriptRuntimeState, output_words) == 0x0000);
static_assert(offsetof(ScriptRuntimeState, channel_table) == 0x0010);
static_assert(offsetof(ScriptRuntimeState, command_tree) == 0x1414);
static_assert(offsetof(ScriptRuntimeState, nodes) == 0x1434);
static_assert(offsetof(ScriptRuntimeState, key_tree) == 0x1444);
static_assert(offsetof(ScriptRuntimeState, allocator) == 0x146C);
static_assert(offsetof(ScriptRuntimeState, output_1478) == 0x1478);
static_assert(offsetof(ScriptRuntimeState, output_147c) == 0x147C);
static_assert(offsetof(ScriptRuntimeState, callback_1480) == 0x1480);
static_assert(offsetof(ScriptRuntimeState, output_1487) == 0x1487);
static_assert(offsetof(ScriptRuntimeState, output_1489) == 0x1489);
static_assert(sizeof(ScriptRuntimeState) == 0x148C);

// ---------------------------------------------------------------------------
// 0x00101308 support types
// ---------------------------------------------------------------------------

// Frame state at 0x00446DB0.  The two 64-bit words are written with `strd`
// at 0x00101B88 (+0x20) and 0x00101F14 (+0x28); the remaining fields are the
// byte/word accesses listed above.
struct CrtMainState {
    u8  render_ready;       // +0x00 (`strb r0,[r5]`, 0x00101BA8)
    u8  stereo_enabled;     // +0x01 (`strb r0,[r5,#1]`, 0x00101390)
    u8  mode_latch;         // +0x02 (`strb r0,[r5,#2]`, 0x00102170)
    u8  shutdown;           // +0x03 (`strb r0,[r5,#3]`, 0x00101B4C)
    u8  timer_enabled;      // +0x04 (`ldrb r0,[r5,#4]`, 0x00101E10)
    u8  pad_05[0x0003];     // +0x05..+0x07
    void* gx_08;            // +0x08 (`str r0,[r6,#8]`, 0x001015D0)
    void* gx_0c;            // +0x0C (`str r0,[r6,#0xc]`, 0x001015DC)
    u32 timer_10;           // +0x10 (`ldr r0,[r5,#0x10]`, 0x00101E2C)
    u32 fade_14;            // +0x14 (`str r0,[r5,#0x14]`, 0x00102168)
    u32 frame_load_18;      // +0x18 (`str r0,[r5,#0x18]`, 0x00102004)
    u32 stereo_counter_1c;  // +0x1C (`str r0,[r5,#0x1c]`, 0x00101DF8)
    u64 tick_20;            // +0x20 (`strd r0,r1,[r5,#0x20]`)
    u64 tick_28;            // +0x28 (`strd r0,r1,[r2,#0x28]`)
};
static_assert(offsetof(CrtMainState, render_ready) == 0x00);
static_assert(offsetof(CrtMainState, stereo_enabled) == 0x01);
static_assert(offsetof(CrtMainState, mode_latch) == 0x02);
static_assert(offsetof(CrtMainState, shutdown) == 0x03);
static_assert(offsetof(CrtMainState, timer_enabled) == 0x04);
static_assert(offsetof(CrtMainState, gx_08) == 0x08);
static_assert(offsetof(CrtMainState, gx_0c) == 0x0C);
static_assert(offsetof(CrtMainState, timer_10) == 0x10);
static_assert(offsetof(CrtMainState, fade_14) == 0x14);
static_assert(offsetof(CrtMainState, frame_load_18) == 0x18);
static_assert(offsetof(CrtMainState, stereo_counter_1c) == 0x1C);
static_assert(offsetof(CrtMainState, tick_20) == 0x20);
static_assert(offsetof(CrtMainState, tick_28) == 0x28);
static_assert(sizeof(CrtMainState) == 0x30);

// Passed by pointer to battle_func_00105460 (0x001013B0) after the six-word
// initialiser at 0x00101360..0x001013AC: words +0x00..+0x0C and +0x14..+0x1C.
struct CrtInitBlock {
    u32 words[8];           // +0x00..+0x1C
};
static_assert(sizeof(CrtInitBlock) == 0x20);

// ---------------------------------------------------------------------------
// 0x00142BF0 support types
// ---------------------------------------------------------------------------

// Render configuration consumed by func_00142bf0.  The float quartet at
// +0x18..+0x24 is scaled by 255.0f (0x437F0000) and packed R/G/B/A; the
// +0x28 float supplies the size field; +0x34 is the address; +0x40/+0x44
// are the two pixel-format selectors; +0x48 is the operating mode checked
// against 0x1906..0x190A / 0x1FCA / 0x2025; +0x50 supplies the four-bit
// control nibble; +0x68 supplies the size divisor.
struct LcdRenderConfig {
    u32 mode_00;            // +0x00 (0x2600/0x2601 -> control bit 1)
    u32 mode_04;            // +0x04 (0x2600/0x2601/0x2700..0x2703)
    u32 format_08;          // +0x08 (0x2901/0x812D/0x812F/0x8130)
    u32 format_0c;          // +0x0C (same selector set)
    u8  pad_10[0x0008];     // +0x10..+0x17
    f32 color_18;           // +0x18 (`vldr s8`, 0x00142C84)
    f32 color_1c;           // +0x1C (`vldr s7`, 0x00142C80)
    f32 color_20;           // +0x20 (`vldr s1`, 0x00142C88)
    f32 color_24;           // +0x24 (`vldr s6`, 0x00142C8C)
    f32 alpha_28;           // +0x28 (`vldr s0`, 0x00142D60)
    u8  pad_2c[0x0008];     // +0x2C..+0x33
    u32 address_34;         // +0x34 (`ldr r0,[r5]`, 0x00143228)
    u8  pad_38[0x0008];     // +0x38..+0x3F
    u32 field_40;           // +0x40 (`ldr r1,[r5,#0xc]`, 0x00142D2C)
    u32 field_44;           // +0x44 (`ldr r7,[r5,#0x10]`, 0x00142D44)
    u32 mode_48;            // +0x48 (`ldr r1,[r5,#0x14]`, 0x00142E38)
    u8  pad_4c[0x0004];     // +0x4C
    u32 field_50;           // +0x50 (`ldr r1,[r5,#0x1c]`, 0x00142E20)
    u8  pad_54[0x0014];     // +0x54..+0x67
    u32 count_68;           // +0x68 (`ldr ip,[r5,#0x34]`, 0x00143050)
};
static_assert(offsetof(LcdRenderConfig, mode_00) == 0x00);
static_assert(offsetof(LcdRenderConfig, mode_04) == 0x04);
static_assert(offsetof(LcdRenderConfig, format_08) == 0x08);
static_assert(offsetof(LcdRenderConfig, format_0c) == 0x0C);
static_assert(offsetof(LcdRenderConfig, color_18) == 0x18);
static_assert(offsetof(LcdRenderConfig, alpha_28) == 0x28);
static_assert(offsetof(LcdRenderConfig, address_34) == 0x34);
static_assert(offsetof(LcdRenderConfig, field_40) == 0x40);
static_assert(offsetof(LcdRenderConfig, field_44) == 0x44);
static_assert(offsetof(LcdRenderConfig, mode_48) == 0x48);
static_assert(offsetof(LcdRenderConfig, field_50) == 0x50);
static_assert(offsetof(LcdRenderConfig, count_68) == 0x68);
static_assert(sizeof(LcdRenderConfig) == 0x6C);

// Register block at 0x004655C0->0x770.  Channel 0 is the non-contiguous set
// +0x00/+0x04/+0x08/+0x0C/+0x10/+0x14/+0x38; channels 1 and 2 are the
// contiguous six-word groups starting at +0x44 and +0x64.
struct LcdRegisterBlock {
    u32 flags_00;           // +0x00 (orr/bic bit 1/2/4)
    u32 color0_04;          // +0x04 (`str r7,[r4,#4]`, 0x00142D1C)
    u32 format0_08;         // +0x08
    u32 control0_0c;        // +0x0C
    u32 size0_10;           // +0x10
    u32 address0_14;        // +0x14
    u8  pad_18[0x0020];     // +0x18..+0x37
    u32 extra0_38;          // +0x38 (`str r1,[r4,#0x38]`, 0x00142E34)
    u8  pad_3c[0x0008];     // +0x3C..+0x43
    u32 color1_44;          // +0x44 (`str r7,[r4,#0x44]`, 0x001435A8)
    u32 format1_48;         // +0x48
    u32 control1_4c;        // +0x4C
    u32 size1_50;           // +0x50
    u32 address1_54;        // +0x54
    u32 extra1_58;          // +0x58
    u8  pad_5c[0x0008];     // +0x5C..+0x63
    u32 color2_64;          // +0x64 (`str r7,[r4,#0x64]`, 0x00143A20)
    u32 format2_68;         // +0x68
    u32 control2_6c;        // +0x6C
    u32 size2_70;           // +0x70
    u32 address2_74;        // +0x74
    u32 extra2_78;          // +0x78
};
static_assert(offsetof(LcdRegisterBlock, flags_00) == 0x00);
static_assert(offsetof(LcdRegisterBlock, color0_04) == 0x04);
static_assert(offsetof(LcdRegisterBlock, format0_08) == 0x08);
static_assert(offsetof(LcdRegisterBlock, control0_0c) == 0x0C);
static_assert(offsetof(LcdRegisterBlock, size0_10) == 0x10);
static_assert(offsetof(LcdRegisterBlock, address0_14) == 0x14);
static_assert(offsetof(LcdRegisterBlock, extra0_38) == 0x38);
static_assert(offsetof(LcdRegisterBlock, color1_44) == 0x44);
static_assert(offsetof(LcdRegisterBlock, format1_48) == 0x48);
static_assert(offsetof(LcdRegisterBlock, control1_4c) == 0x4C);
static_assert(offsetof(LcdRegisterBlock, size1_50) == 0x50);
static_assert(offsetof(LcdRegisterBlock, address1_54) == 0x54);
static_assert(offsetof(LcdRegisterBlock, extra1_58) == 0x58);
static_assert(offsetof(LcdRegisterBlock, color2_64) == 0x64);
static_assert(offsetof(LcdRegisterBlock, format2_68) == 0x68);
static_assert(offsetof(LcdRegisterBlock, control2_6c) == 0x6C);
static_assert(offsetof(LcdRegisterBlock, size2_70) == 0x70);
static_assert(offsetof(LcdRegisterBlock, address2_74) == 0x74);
static_assert(offsetof(LcdRegisterBlock, extra2_78) == 0x78);

// ---------------------------------------------------------------------------
// 0x002831F0 support type
// ---------------------------------------------------------------------------

// Camp layout state rooted at 0x0043DA90.  The fields are the byte/word
// slots touched by the ten jump-table handlers; the large explicit gaps keep
// the proven offsets exact.
struct CampLayoutState {
    u8  pad_0000[0x00B0];       // +0x0000
    u8  slot_00b0[0x00C8];      // +0x00B0 (case 11 source)
    u8  slot_0178[0x0064];      // +0x0178 (case 13 source)
    u8  slot_01dc[0x0064];      // +0x01DC (case 9 source)
    u8  slot_0240[0x0064];      // +0x0240 (case 10 count)
    u8  slot_02a4[0x0064];      // +0x02A4 (case 18 source)
    u8  slot_0308[0x0064];      // +0x0308 (case 19 source)
    u8  slot_036c[0x0064];      // +0x036C (case 20 source)
    u8  slot_03d0[0x0064];      // +0x03D0 (case 21 source)
    u8  slot_0434[0x0064];      // +0x0434 (case 22 source)
    u8  slot_0498[0x0064];      // +0x0498 (case 23 source)
    u8  slot_04fc[0x0F80];      // +0x04FC (case 24 source)
    u8  slot_147c[0x0848];      // +0x147C (case 11 destination)
    u8  slot_1cc4[0x00F0];      // +0x1CC4 (case 13 destination)
    u8  slot_1db4[0x02A8];      // +0x1DB4 (case 10 counters)
    u8  slot_205c[0x0064];      // +0x205C (case 20 destination)
    u8  slot_20c0[0x00F0];      // +0x20C0 (case 21 destination)
    u8  slot_21b0[0x00F0];      // +0x21B0 (case 22 destination)
    u8  slot_22a0[0x00F0];      // +0x22A0 (case 23 destination)
    u8  slot_2390[0x9EAC];      // +0x2390..+0xC23B
    u8  slot_c23c[0x10040];     // +0xC23C (case 9 destination)
    u8  slot_1c27c[0x00F0];     // +0x1C27C (case 18 destination)
    u8  slot_1c36c[0x3CF0];     // +0x1C36C (case 19 destination)
};
static_assert(offsetof(CampLayoutState, slot_00b0) == 0x00B0);
static_assert(offsetof(CampLayoutState, slot_0178) == 0x0178);
static_assert(offsetof(CampLayoutState, slot_01dc) == 0x01DC);
static_assert(offsetof(CampLayoutState, slot_0240) == 0x0240);
static_assert(offsetof(CampLayoutState, slot_02a4) == 0x02A4);
static_assert(offsetof(CampLayoutState, slot_0308) == 0x0308);
static_assert(offsetof(CampLayoutState, slot_036c) == 0x036C);
static_assert(offsetof(CampLayoutState, slot_03d0) == 0x03D0);
static_assert(offsetof(CampLayoutState, slot_0434) == 0x0434);
static_assert(offsetof(CampLayoutState, slot_0498) == 0x0498);
static_assert(offsetof(CampLayoutState, slot_04fc) == 0x04FC);
static_assert(offsetof(CampLayoutState, slot_c23c) == 0xC23C);
static_assert(offsetof(CampLayoutState, slot_147c) == 0x147C);
static_assert(offsetof(CampLayoutState, slot_1cc4) == 0x1CC4);
static_assert(offsetof(CampLayoutState, slot_1db4) == 0x1DB4);
static_assert(offsetof(CampLayoutState, slot_1c27c) == 0x1C27C);
static_assert(offsetof(CampLayoutState, slot_1c36c) == 0x1C36C);
static_assert(offsetof(CampLayoutState, slot_205c) == 0x205C);
static_assert(offsetof(CampLayoutState, slot_20c0) == 0x20C0);
static_assert(offsetof(CampLayoutState, slot_21b0) == 0x21B0);
static_assert(offsetof(CampLayoutState, slot_22a0) == 0x22A0);
static_assert(offsetof(CampLayoutState, slot_2390) == 0x2390);

// ---------------------------------------------------------------------------
// Globals reproduced from .data
// ---------------------------------------------------------------------------

extern void* g_RenderRegisterBase;   // 0x0044EA00
extern u8    g_CrtOverlayFlag;       // 0x0044D048
extern void* g_CrtModeContext;       // 0x0044E368
extern CrtMainState g_CrtMainState; // 0x00446DB0 (the block itself)
extern void* g_LcdGpuState;          // 0x004655C0
extern u32*  g_GpuCommandCursor;     // 0x004652A0
extern u32*  g_GpuCommandEnd;        // 0x004652A4
extern void* g_CampLayoutRoot;       // 0x0043DA90

// ---------------------------------------------------------------------------
// Reconstructed entry points
// ---------------------------------------------------------------------------

// 0x003B11A8: two-LEB128 event command dispatcher.
u32 func_003b11a8(ScriptRuntimeState* state, u32 index, ScriptCursor* cursor,
                  u32 end);

// 0x00101308: application bring-up and frame loop (called by __start).
void crt_func_00101308(void);

// 0x00142BF0: programs one LCD framebuffer register group.  Returns 0 on
// success, 0x501 for an invalid screen index and 0x502 for an invalid config.
u32 func_00142bf0(LcdRenderConfig* config, u32 screen);

// 0x002831F0: camp layout byte-stream interpreter for opcodes 9..24.
void camp_func_002831f0(u32 layout_opcode);

} // namespace smt4::engine
