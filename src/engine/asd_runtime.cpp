#include "engine/asd_runtime.h"
#include "engine/asd_symbols.h"
#include "engine/map_runtime.h"
#include "camp/camp.h"
#include "ui/ui_runtime.h"
#include <cmath>
#include <cstring>

namespace smt4::engine {

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

// 0x0049F91C (BSS): shared map/script word block.  The canonical declaration
// (u8[0x3E4]) lives in engine/map_runtime.h; only the dword at +0x08 is
// written here (0x001ABC54).

extern "C" {
    // 0x002C2B1C: engine context singleton (same spelling as window.cpp).
    void* UiEngine_GetContext();

    // 0x002E294C (1,364 B): maze visibility classifier.  r0 is dead (the
    // callee's first act is to reload the engine context at 0x002E2960); the
    // four vector arguments arrive in s0..s3.
    void  engine_func_002e294c(u32 unused, f32 x, f32 y, f32 angle, f32 col);

    // 0x002C0BCC is declared canonically in engine/asd_symbols.h as
    // Random_Range(u32 max); the implementation returns a value in [0, max].

    // 0x002857E4 (16 B): `ldrb r0,[engine,#3]` - the active map id.
    s32   script_vm_func_002857e4();

    // 0x00316E2C (24 B): 1 when engine+0x1C is 1, else 0.
    s32   engine_func_00316e2c();

    // 0x00285560 (644 B): reset the maze grid.  A zero argument also restores
    // the default 11x11 size and the (5,5) cursor.
    void  engine_func_00285560(u32 reset_size);

    // 0x0028550C (84 B): map-script notification.  The two float arguments
    // arrive on the stack (`vldmia r4,{s0,s1}` at 0x0028551C); both call sites
    // pass zero.
    // The two trailing words are consumed by `add r4,sp,#0x10;
    // vldmia r4,{s0,s1}` (0x0028551C), so they are raw stack words that the
    // callee reinterprets as floats.  Both call sites pass zero.
    void  script_vm_func_0028550c(u32 mode, u32 a1, u32 a2, u32 w0, u32 w1);

    // 0x002854EC (32 B): stores `flag != 0` into engine+0x1C.
    void  script_vm_func_002854ec(u32 flag);

    // 0x002BE7FC (44 B): sprintf-style formatter (the canonical spelling used
    // by the other engine TUs).
    void  UiText_Format(char* dst, const char* fmt, ...);

    // 0x0029BDDC (140 B): instantiate one ".bam" model; the second argument is
    // the model kind word.  Returns the model handle.
    void* engine_func_0029bddc(const char* path, u32 kind);

    // 0x002A06C8 (20 B): clear bit 0x200000 in the handle flags and forward
    // the model's +8 object to 0x001DB890.
    void  engine_func_002a06c8(void* model, u32 mode);

    // 0x0028549C (80 B): clone a model instance for the trail arrays.
    void* engine_func_0028549c(void* model, u32 mode);

    // 0x002CE434 (2,152 B): flush/publish the maze scene.
    void  engine_func_002ce434();

    // 0x00284C14 (2,184 B): map-scene frame step; the single argument is zero
    // at 0x001AC9AC.
    void  engine_func_00284c14(u32 mode);

    // 0x002E0200 (296 B): submit one effect/particle at (s0,s1,s2); r0 is the
    // id word loaded from engine+0xDB0.
    void  engine_func_002e0200(u32 id, f32 x, f32 y, f32 z);

    // 0x00284AA8 (364 B): map-scene completion notification.
    void  script_vm_func_00284aa8();

    // 0x002C2B1C is the context getter above; 0x002C0BA8 is Flag_CheckEventBit
    // in engine/asd_symbols.h.

    // 0x002B66EC (0x00188460): returns the six-id interaction table (the code
    // reads u16 fields at +0, +2, +4, +6, +8, +0xA, +0xC).
    void* script_vm_func_002b66ec();

    // Camp slot command helpers.
    s32   camp_func_0029e248();                             // 0x0029E248
    s32   script_vm_func_0029e398();                        // 0x0029E398
    void  script_vm_func_0029a3c4(u32 mode);                // 0x0029A3C4
    void  script_vm_func_0029c768(u32 mode);                // 0x0029C768
    void  script_vm_func_0029ccf8();                        // 0x0029CCF8
    void  engine_func_0029a384(void* table);                // 0x0029A384
    void  engine_func_0029a368(void* table);                // 0x0029A368
    void  camp_func_0029d924(u32 mode);                     // 0x0029D924
    s32   camp_func_0029f260(void* slot);                    // 0x0029F260
    s32   camp_func_0029f248(void* slot);                    // 0x0029F248
    void  engine_func_0029a320(u32 index, u32 id);          // 0x0029A320
    void* engine_func_0029a2d0(const char* path, u32 kind); // 0x0029A2D0
    s32   engine_func_002ae16c(void* model);                // 0x002AE16C
    void  engine_func_0029a2b0(void* part, u32 mode, f32 x, f32 y,
                               f32 z);                      // 0x0029A2B0
    s32   ui_func_0029a25c();                               // 0x0029A25C
    void  engine_func_0029a03c(u32 command);                // 0x0029A03C
    void  engine_func_0029a020(u32 index);                  // 0x0029A020
    void  engine_func_00299e60(void* slot, u32 mode);       // 0x00299E60
    void  engine_func_00299b9c(u32 command);                // 0x00299B9C
    void  engine_func_002999e8(u32 command);                // 0x002999E8
    void  ui_func_00299974(u32 mode);                       // 0x00299974
    void* camp_func_002bf6d0(u32 group, u32 node);          // 0x002BF6D0
    s32   camp_func_0029f878(void* work, void* node, void* extra,
                             s32 a3, s32 a4, s32 a5, u8* out,
                             s32 a7, s32 a8);                // 0x0029F878
    s32   camp_func_0029f278(void* slot, u32 mode);          // 0x0029F278
    s32   camp_func_002c1830(u32 a, u32 b);                  // 0x002C1830
    s32   engine_func_00299874(u32 id);                      // 0x00299874
    void  engine_func_0029960c(u32 mode);                    // 0x0029960C
    void  camp_func_002bc200(u32 id);                        // 0x002BC200
    void  script_vm_func_002bf9e8(u32 id);                   // 0x002BF9E8
    void  engine_func_0029957c(u32 mode);                    // 0x0029957C
    s32   ui_func_0029d8fc(s16 handle);                      // 0x0029D8FC
    void  engine_func_00299558(void* list, s32 index);       // 0x00299558
    s32   engine_func_0029eba8(void* list);                  // 0x0029EBA8
    s32   engine_func_0029ebf8(void* list);                  // 0x0029EBF8
    s32   engine_func_002994b4(s32 a, s32 b);                // 0x002994B4
    void  script_vm_func_002b8b78(u32 index);               // 0x002B8B78
    void  SortMenu_Init(u32 index, u32 mode);                // 0x0029E63C
    void  engine_func_0029e5c8(u32 index);                   // 0x0029E5C8
    void  camp_func_0029f10c(u32 index, u32 color);          // 0x0029F10C
    u8    camp_func_002b8ccc();                              // 0x002B8CCC
    void  camp_func_002bdac0(void* object, u32 mode, u32 a2); // 0x002BDAC0
    void  script_vm_func_002a7aa0(void* model);              // 0x002A7AA0
    void  engine_func_00299410(void* slot, u32 mode);        // 0x00299410
    void  engine_func_002993d4();                            // 0x002993D4
    void  camp_func_0029e8e8(u32 a, u32 b);                  // 0x0029E8E8
    void  camp_func_0029933c();                              // 0x0029933C
    void  ui_func_002998d8(u32 index, u32 id);               // 0x002998D8
    void  engine_func_0029a400(s32 index);                   // 0x0029A400

    // UI part / trail update helpers (0x002E4B10).
    void  UiPart_GetSceneMatrix(void* out);                  // 0x002A2F1C
    f32   engine_func_0024ba44(u32 mode);                    // 0x0024BA44
    void  func_0024b9d0(void* owner);                        // 0x0024B9D0
    // 0x002486EC (60 B): build the two rotation matrices at 0x004EA95C/
    // 0x004EA97C from `axis` (r0) and `angle` (s0), forwarded to
    // 0x0030F924.  Both arguments are live.
    void  func_002486ec(const f32* axis, f32 angle);         // 0x002486EC
    void  ui_func_0024b874(UiPartInstance* instance,
                           UiPartSource* source, s32 life,
                           const f32* vector);               // 0x0024B874
    void  func_0024afec(void* owner, void* instance);        // 0x0024AFEC
    u32   ui_func_00269cb8();                                // 0x00269CB8
    f32   ui_func_002b73a4(f32 angle);                       // 0x002B73A4 (sin)
    f32   ui_func_002b740c(f32 angle);                       // 0x002B740C (cos)
    u32   engine_func_0024b990(u32 mode);                    // 0x0024B990
    s32   ui_func_002c6c10(s32 value, s32 limit);            // 0x002C6C10
    void  func_0024b804(void* owner, void* instance);        // 0x0024B804

    // Trail/ribbon builder (0x00304164).
    void  func_0019d9d4(f32* out);                           // 0x0019D9D4
    f32   func_002460b4(f32 value);                          // 0x002460B4 (acos)
    void  ui_func_00248650(f32 angle);                       // 0x00248650
    void  ui_func_002485f0(f32 angle);                       // 0x002485F0
    void  func_00248444();                                   // 0x00248444
    void  func_0024603c();                                   // 0x0024603C
    f32   func_00361074(f32 value);                          // 0x00361074
}

// ---------------------------------------------------------------------------
// Data tables (addresses are the storage locations used by the listing)
// ---------------------------------------------------------------------------

// 0x00447EC0 (96 B): the 24 permutations of 1..4.  The generator draws
// Random_Range(0x17) and skips a draw whose first byte repeats the previous
// first byte (0x001ABCD0..0x001ABCFC).
const u8 g_MazeDirectionOrders[24][4] = {
    {1, 2, 3, 4},
    {1, 2, 4, 3},
    {1, 3, 2, 4},
    {1, 3, 4, 2},
    {1, 4, 2, 3},
    {1, 4, 3, 2},
    {2, 1, 3, 4},
    {2, 1, 4, 3},
    {2, 3, 1, 4},
    {2, 3, 4, 1},
    {2, 4, 1, 3},
    {2, 4, 3, 1},
    {3, 1, 2, 4},
    {3, 1, 4, 2},
    {3, 2, 1, 4},
    {3, 2, 4, 1},
    {3, 4, 1, 2},
    {3, 4, 2, 1},
    {4, 1, 2, 3},
    {4, 1, 3, 2},
    {4, 2, 1, 3},
    {4, 2, 3, 1},
    {4, 3, 1, 2},
    {4, 3, 2, 1},
};

// 0x00447F20 (16 B): wall-kind byte indexed by the four-neighbour mask.
// The high nibble is the model type counted by the placement pass.
const u8 g_MazeWallKinds[16] = {
    0x00, 0x13, 0x11, 0x21, 0x10, 0x30, 0x31, 0x40, 0x12, 0x33, 0x32, 0x42, 0x20, 0x43, 0x41, 0x00,
};

// 0x00447F30 (16 B): wall-style byte written to cell+0x04.  The first table is
// written to cell+0x05 and the second to cell+0x04 (0x001AC728).
const u8 g_MazeWallStyles[16] = {
    0x00, 0x01, 0x02, 0x01, 0x03, 0x03, 0x02, 0x03, 0x04, 0x04, 0x04, 0x04, 0x04, 0x01, 0x02, 0x00,
};

// 0x00448270 onward: eleven distinct 15x15 layout byte blocks.  Values:
// 0 = open, 1 = wall, 2/3 = corridor with direction 1/2 (counted into
// engine+0xDD4 by 0x001ABC84/0x001ABC9C).
// 0x00448270
const u8 g_MazeLayout00[15 * 15] = {
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 3, 0, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

// 0x00448351
const u8 g_MazeLayout02[15 * 15] = {
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1,
    1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1,
    1, 2, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1,
    1, 0, 1, 0, 1, 0, 1, 2, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

// 0x00448432
const u8 g_MazeLayout03[15 * 15] = {
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 1,
    1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

// 0x00448513
const u8 g_MazeLayout04[15 * 15] = {
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1,
    1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1,
    1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1,
    1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

// 0x004485F4
const u8 g_MazeLayout05[15 * 15] = {
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

// 0x004486D5
const u8 g_MazeLayout06[15 * 15] = {
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1,
    1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1,
    1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1,
    1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1,
    1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1,
    1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1,
    1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 1,
    1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1,
    1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1,
    1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1,
    1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1,
    1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1,
    1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

// 0x004487B6
const u8 g_MazeLayout07[15 * 15] = {
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1,
    1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1,
    1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1,
    1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1,
    1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1,
    1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1,
    1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1,
    1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1,
    1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1,
    1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1,
    1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1,
    1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

// 0x00448897
const u8 g_MazeLayout08[15 * 15] = {
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1,
    1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1,
    1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1,
    1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1,
    1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1,
    1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1,
    1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1,
    1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1,
    1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1,
    1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1,
    1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

// 0x00448978
const u8 g_MazeLayout09[15 * 15] = {
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1,
    1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1,
    1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1,
    1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1,
    1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1,
    1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1,
    1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1,
    1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1,
    1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1,
    1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1,
    1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1,
    1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1,
    1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

// 0x00448A59
const u8 g_MazeLayout10[15 * 15] = {
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1,
    1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1,
    1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1,
    1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1,
    1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1,
    1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1,
    1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1,
    1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1,
    1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1,
    1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1,
    1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1,
    1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

// 0x00448B3A
const u8 g_MazeLayout11[15 * 15] = {
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1,
    1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1,
    1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1,
    1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

// 0x00447F40 (0x44 bytes per entry): the twelve predefined map layouts.
const MazeLayoutEntry g_MazeLayoutTable[12] = {
    { g_MazeLayout00,  0x0000, 11, 11, {0},   9,   1,  1,  7, 0x0000, 0x0000, {0} },  // 0
    { g_MazeLayout00,  0x004F, 11, 11, {0},   9,   1,  1,  8, 0x0000, 0x0000, {0} },  // 1
    { g_MazeLayout02,  0x002D, 11, 11, {0},   3,   9,  3,  3, 0x0000, 0x0000, {0} },  // 2
    { g_MazeLayout03,  0x0011, 11, 11, {0},   9,   9,  9,  1, 0x0000, 0x0000, {0} },  // 3
    { g_MazeLayout04,  0x002E, 11, 11, {0},   3,   4,  9,  5, 0x0000, 0x0000, {0} },  // 4
    { g_MazeLayout05,  0x0067, 11, 11, {0},   5,   1,  5,  9, 0x0018, 0x000A, {0} },  // 5
    { g_MazeLayout06,  0x0089, 15, 15, {0},   1,  11,  7,  4, 0x0000, 0x0000, {0} },  // 6
    { g_MazeLayout07,  0x008C, 15, 15, {0},  12,  13,  1,  1, 0x0000, 0x0000, {0} },  // 7
    { g_MazeLayout08,  0x009D, 14, 13, {0},   1,   6, 11,  1, 0x0000, 0x0000, {0} },  // 8
    { g_MazeLayout09,  0x00A1, 15, 15, {0},  13,   1,  7, 13, 0x0000, 0x0000, {0} },  // 9
    { g_MazeLayout10,  0x00A4, 15, 15, {0},  13,  13,  7, 13, 0x0000, 0x0000, {0} },  // 10
    { g_MazeLayout11,  0x0058, 15,  9, {0},  13,   3,  1,  3, 0x0011, 0x0006, {0} },  // 11
};

MazeGenWork g_MazeGenWork{};                 // 0x004BCE8C

f32 g_TrailScratchA[4] = {0.0f, 1.0f, 0.0f, 1.0f};   // 0x00472530
f32 g_TrailScratchB[4] = {0.0f, 0.0f, 0.0f, 1.0f};   // 0x00472550

// ---------------------------------------------------------------------------
// engine_func_001aba94 (0x001ABA94), 4,672 B
// ---------------------------------------------------------------------------
//
// Recovered role: the "mr01/mr02" maze runtime.  The routine either loads one
// of twelve predefined 15x15 layouts (map id != 0) or carves a random maze
// (map id 0) with the standard 2-cell-step backtracking walk, then classifies
// every corridor cell from its four neighbours, builds the five wall-piece
// models ("map/mr01/mr01_%02d.bam" or "map/mr02/mr02_%02d.bam"), places the
// start/goal markers and finally samples up to sixteen candidate model
// markers.  It is the only place that touches engine+0xDCC..+0xDD7.

namespace {

constexpr s32 kMazeStride = 15;              // `rsb rX,rY,rY,lsl #4`

inline MazeCell* MazeCellAt(MazeEngineState* engine, s32 row, s32 col) {
    return &engine->cells[row * kMazeStride + col];
}

inline const MazeCell* MazeCellAt(const MazeEngineState* engine, s32 row,
                                  s32 col) {
    return &engine->cells[row * kMazeStride + col];
}

// Two cells ahead in `direction` are still untouched.  The four blocks at
// 0x001ABD58, 0x001ABD7C, 0x001ABDA0 and 0x001ABDC4 read:
//   dir 1: (x-1,y), (x-2,y)     dir 2: (x+1,y), (x+2,y)
//   dir 3: (x,y-1), (x,y-2)     dir 4: (x,y+1), (x,y+2)
bool MazeDirectionOpen(const MazeEngineState* engine, s32 x, s32 y, u8 dir) {
    switch (dir) {
    case 1:
        return MazeCellAt(engine, y, x - 1)->state == 0 &&
               MazeCellAt(engine, y, x - 2)->state == 0;
    case 2:
        return MazeCellAt(engine, y, x + 1)->state == 0 &&
               MazeCellAt(engine, y, x + 2)->state == 0;
    case 3:
        return MazeCellAt(engine, y - 1, x)->state == 0 &&
               MazeCellAt(engine, y - 2, x)->state == 0;
    default:
        return MazeCellAt(engine, y + 1, x)->state == 0 &&
               MazeCellAt(engine, y + 2, x)->state == 0;
    }
}

// Carve the current cell, the wall between, and the destination.  Every
// direction block stores state 2 at the three cells before publishing the new
// cursor (0x001ABF50..0x001ABF60, 0x001ABF7C..0x001ABF8C,
// 0x001ABFA8..0x001ABFB8, 0x001ABFD4..0x001ABFE4).
void MazeCarve(MazeEngineState* engine, u8 dir) {
    const s32 x = engine->cursor_x;
    const s32 y = engine->cursor_y;

    MazeCellAt(engine, y, x)->state = 2;
    switch (dir) {
    case 1:
        MazeCellAt(engine, y, x - 1)->state = 2;
        MazeCellAt(engine, y, x - 2)->state = 2;
        engine->cursor_x = static_cast<s8>(x - 2);
        break;
    case 2:
        MazeCellAt(engine, y, x + 1)->state = 2;
        MazeCellAt(engine, y, x + 2)->state = 2;
        engine->cursor_x = static_cast<s8>(x + 2);
        break;
    case 3:
        MazeCellAt(engine, y - 1, x)->state = 2;
        MazeCellAt(engine, y - 2, x)->state = 2;
        engine->cursor_y = static_cast<s8>(y - 2);
        break;
    default:
        MazeCellAt(engine, y + 1, x)->state = 2;
        MazeCellAt(engine, y + 2, x)->state = 2;
        engine->cursor_y = static_cast<s8>(y + 2);
        break;
    }
    // The cursor bytes are stored with strb from the same registers
    // (0x001ABF5C..0x001ABF60 and the three sibling blocks).
}

} // namespace

// DECOMP_FUNC(0x001aba94, 4672)
#if 0
void engine_func_001aba94() {
    MazeEngineState* const engine =
        static_cast<MazeEngineState*>(UiEngine_GetContext());
    MazeGenWork* const work = &g_MazeGenWork;

    // 0x001ABAA8..0x001ABAD0: retry flag [sp+0x24] = 1, previous first
    // direction byte [sp+0x10] = (Random_Range(4) + 1) & 0xFF, remaining-step
    // budget [sp+0x20] = 0 and accepted-step flag [sp+0x14] = 0.
    s32 retry = 1;
    u8 previous_direction =
        static_cast<u8>((Random_Range(4) + 1) & 0xFF);
    s32 extra_steps = 0;
    s32 accepted = 0;

    const s32 map_id = script_vm_func_002857e4();   // 0x001ABAD4
    const bool ready = engine_func_00316e2c() == 1; // 0x001ABADC..0x001ABAE8

    // 0x001ABAE8: map 0 is regenerated only while engine+0x1C is clear.
    if (map_id == 0 && ready) {
        goto place_models;
    }

    engine_func_00285560(0);                    // 0x001ABAF0
    work->path_count = 0;                       // 0x001ABB04 `str r0,[fp,#0x24c]`

    if (map_id != 0) {
        // 0x001ABB0C..0x001ABB28: 0x44-byte layout entry selection and the
        // two size bytes.
        const MazeLayoutEntry* const layout = &g_MazeLayoutTable[map_id];
        engine->width = static_cast<s8>(layout->width);
        engine->height = static_cast<s8>(layout->height);
        engine_func_00285560(1);                // 0x001ABB30
        (void)previous_direction;

        // 0x001ABB34..0x001ABB48: a pending size override is cancelled.
        if (engine->requested_size != -1) {
            engine->requested_size = -1;
        }

        // 0x001ABB4C..0x001ABBC8: copy the layout pattern and assign the
        // corridor direction/counter.
        const u8* const pattern = layout->layout;
        for (s32 row = 0; row < engine->height; ++row) {
            const s32 pattern_row = row * kMazeStride;
            const s32 cell_row = row * kMazeStride;
            for (s32 col = 0; col < engine->width; ++col) {
                const u8 value = pattern[pattern_row + col];
                MazeCell* const cell = &engine->cells[cell_row + col];
                if (value == 1) {
                    cell->state = 1;            // `strbeq r6,[fp,#0x3c]`
                    cell->direction = 0;
                } else {
                    cell->state = 2;            // `strbne r7,[fp,#0x3c]`
                    if (value == 2) {
                        cell->direction = 1;    // 0x001ABC80
                        ++engine->carved;       // 0x001ABC88
                    } else if (value == 3) {
                        cell->direction = 2;    // 0x001ABC94
                        ++engine->carved;       // 0x001ABC9C
                    } else {
                        cell->direction = 0;    // 0x001ABBA8
                    }
                }
            }
        }

        // 0x001ABBD0..0x001ABC0C: start marker.
        engine->start_x = layout->start_x;
        engine->start_y = layout->start_y;
        engine->goal_x = layout->goal_x;
        engine->goal_y = layout->goal_y;
        if (engine->start_x > 0 && engine->start_y > 0) {
            MazeCellAt(engine, engine->start_y, engine->start_x)->field_02 = 1;
        }

        // 0x001ABC10..0x001ABC28: goal marker.
        MazeCellAt(engine, engine->goal_y, engine->goal_x)->field_03 = 1;

        // 0x001ABC2C..0x001ABC40: optional byte pair.
        if (layout->field_10 != 0) {
            engine->field_03a = static_cast<u8>(layout->field_10);
            engine->field_03b = static_cast<u8>(layout->field_12);
        }

        // 0x001ABC44..0x001ABC6C: publish the layout id word and notify the
        // map script.  The two stack words at [sp]/[sp+4] are zero.
        *reinterpret_cast<s32*>(g_MapRuntimeState + 8) = layout->field_04;
        script_vm_func_0028550c(
            static_cast<u32>(layout->field_04 & 0xFF), 0, 0, 0u, 0u);

        goto reset_wall_types;                  // 0x001ABC78
    }

    // ------------------------------------------------------------------
    // Random maze (map id 0), 0x001ABCA8..0x001AC150
    // ------------------------------------------------------------------

    // 0x001ABCA8..0x001ABCC4: a positive size request re-initialises the
    // grid, then the slot is consumed.
    if (engine->requested_size > 0) {
        engine->width = engine->requested_size;
        engine->height = engine->requested_size;
        engine_func_00285560(1);                // 0x001ABCC4
    }
    engine->requested_size = -1;                // 0x001ABCCC

    do {
        // 0x001ABCD0..0x001ABD18: draw a direction permutation that does not
        // start with the previous first direction, then copy its four bytes to
        // work+0x248.
        u32 order = Random_Range(0x17);         // 0x001ABCD0
        if (g_MazeDirectionOrders[order][0] == previous_direction) {
            // 0x001ABCE8..0x001ABCF0: exactly one redraw, not a loop.
            order = Random_Range(0x17);
        }

        for (s32 i = 0; i < 4; ++i) {
            work->direction[i] = g_MazeDirectionOrders[order][i];
        }

        // 0x001ABD1C..0x001ABDF0: count the passable directions.
        s32 passable = 0;
        for (s32 i = 0; i < 4; ++i) {
            const u8 dir = work->direction[i];
            if (MazeDirectionOpen(engine, engine->cursor_x, engine->cursor_y,
                                  dir)) {
                ++passable;
            }
        }

        // 0x001ABDF4..0x001ABE10: two or more openings bias the walk to one
        // or two extra steps (60%).
        if (passable >= 2) {
            extra_steps = (Random_Range(0x63) < 0x3C) ? 1 : 2;
        }

        // 0x001ABE14..0x001AC048: carve every passable direction.
        s32 carved_this_pass = 0;               // [sp+4]
        for (s32 i = 0; i < 4; ++i) {
            const u8 dir = work->direction[i];
            const s32 x = engine->cursor_x;
            const s32 y = engine->cursor_y;
            if (!MazeDirectionOpen(engine, x, y, dir)) {
                continue;
            }

            // 0x001ABEF8..0x001ABF18: append the old cursor to the frontier
            // list (count at +0x244).
            const s32 index = work->cell_count;
            work->cell_list[index * 2] = static_cast<u8>(x);
            work->cell_list[index * 2 + 1] = static_cast<u8>(y);
            work->cell_count = index + 1;

            MazeCarve(engine, dir);

            // 0x001ABFE8..0x001AC010
            --extra_steps;
            carved_this_pass = 1;
            accepted = 1;
            previous_direction = work->direction[i];  // 0x001AC00C
            if (extra_steps <= 0) {
                goto next_pass;                 // 0x001AC144
            }

            // 0x001AC018..0x001AC038: replace the last frontier entry with
            // the new cursor.
            work->cell_list[(work->cell_count - 1) * 2] =
                static_cast<u8>(engine->cursor_x);
            work->cell_list[(work->cell_count - 1) * 2 + 1] =
                static_cast<u8>(engine->cursor_y);

            // 0x001AC038..0x001AC03C: put the pre-carve cursor back so the
            // remaining directions start from the same cell.
            engine->cursor_x = static_cast<s8>(x);
            engine->cursor_y = static_cast<s8>(y);
        }

        // 0x001AC04C..0x001AC060: a pass that carved nothing backtracks.
        if (carved_this_pass != 0) {
            goto next_pass;
        }

        if (accepted != 0) {
            // 0x001AC064..0x001AC0B4: record the dead end (only while the
            // 16-entry point array has room).
            if (work->path_count < 0x10) {
                MazePoint* const point = &work->points[work->path_count];
                point->x = engine->cursor_x;
                point->y = engine->cursor_y;
                point->distance = 0;
                ++work->path_count;
            }
            accepted = 0;
        }

        // 0x001AC0BC..0x001AC0C8: an empty frontier branches to the finish
        // stage at 0x001AC150 (not directly to the wall-type reset).
        if (work->cell_count == 0) {
            goto finish_maze;
        }

        // 0x001AC0CC..0x001AC114: pop one frontier cell at random.
        {
            const s32 pick = static_cast<s32>(
                Random_Range(static_cast<u32>(work->cell_count - 1)));
            engine->cursor_x =
                static_cast<s8>(work->cell_list[pick * 2]);
            engine->cursor_y =
                static_cast<s8>(work->cell_list[pick * 2 + 1]);
            --work->cell_count;

            // Compact the list, skipping `pick` (0x001AC118..0x001AC140).
            if (work->cell_count > 0) {
                for (s32 src = 0, dst = 0; dst < work->cell_count;
                     ++dst, ++src) {
                    if (src == pick) {
                        ++src;
                    }
                    work->cell_list[dst * 2] = work->cell_list[src * 2];
                    work->cell_list[dst * 2 + 1] =
                        work->cell_list[src * 2 + 1];
                }
            }
        }

    next_pass:
        // 0x001AC144..0x001AC14C: `[sp+0x24]` is written once at entry
        // (0x001ABAAC) and never modified again, so this test is always true
        // and the walk continues until the frontier empties or it finishes.
        continue;
    } while (retry != 0);

finish_maze:
    // ------------------------------------------------------------------
    // 0x001AC150..0x001AC474: close the random maze.
    // ------------------------------------------------------------------
    {
        // 0x001AC150..0x001AC1B0: every untouched cell becomes a wall and
        // every direction byte is cleared.
        for (s32 row = 0; row < engine->height; ++row) {
            for (s32 col = 0; col < engine->width; ++col) {
                MazeCell* const cell = MazeCellAt(engine, row, col);
                cell->direction = 0;                 // 0x001AC18C
                if (cell->state == 0) {
                    cell->state = 1;                 // 0x001AC194
                }
            }
        }

        // 0x001AC1B4..0x001AC1C8: no marker until the goal pass selects one.
        engine->field_dd5 = 0;
        engine->field_dd6 = 0;
        engine->field_dd7 = 0;

        const s32 point_count = work->path_count;
        if (point_count >= 2) {
            // 0x001AC1E8..0x001AC240: Manhattan distance from point 0 for
            // every later dead end.
            const s32 origin_x = work->points[0].x;
            const s32 origin_y = work->points[0].y;
            for (s32 i = 1; i < point_count; ++i) {
                s32 dx = origin_x - work->points[i].x;
                s32 dy = origin_y - work->points[i].y;
                if (dx < 0) {
                    dx = -dx;
                }
                if (dy < 0) {
                    dy = -dy;
                }
                work->points[i].distance = dx + dy;  // 0x001AC23C
            }

            // 0x001AC244..0x001AC2D0: sort points 1.. by distance (the
            // listing's nested swap loop).
            for (s32 i = 1; i < point_count - 1; ++i) {
                for (s32 j = i + 1; j < point_count; ++j) {
                    if (work->points[i].distance >
                        work->points[j].distance) {
                        const MazePoint tmp = work->points[i];
                        work->points[i] = work->points[j];
                        work->points[j] = tmp;
                    }
                }
            }

            // 0x001AC2D4..0x001AC318: pick the goal from the far half.
            s32 goal_index;
            const s32 half = point_count / 2;
            if (half >= 2) {
                const s32 pick = static_cast<s32>(
                    Random_Range(static_cast<u32>(half - 1)));
                goal_index = point_count - pick - 1;
                if (work->points[goal_index].distance < 5) {
                    goal_index = point_count - 1;
                }
            } else {
                goal_index = point_count - 1;
            }

            // 0x001AC318..0x001AC358: start = point 0, goal = selected point.
            const s32 goal_x = work->points[goal_index].x;
            const s32 goal_y = work->points[goal_index].y;
            engine->start_x = static_cast<s8>(origin_x);
            engine->start_y = static_cast<s8>(origin_y);
            engine->goal_x = static_cast<u8>(goal_x);
            engine->goal_y = static_cast<u8>(goal_y);
            MazeCellAt(engine, origin_y, origin_x)->field_02 = 1;
            MazeCellAt(engine, goal_y, goal_x)->field_03 = 1;

            // 0x001AC35C..0x001AC474: pick a third point (neither start nor
            // goal) and publish the marker cell / effect id.
            if (point_count >= 3) {
                const s32 pick = static_cast<s32>(
                    Random_Range(static_cast<u32>(point_count - 3)));
                s32 seen = 0;
                for (s32 i = 0; i < point_count; ++i) {
                    if (work->points[i].x == origin_x &&
                        work->points[i].y == origin_y) {
                        continue;
                    }
                    if (work->points[i].x == goal_x &&
                        work->points[i].y == goal_y) {
                        continue;
                    }
                    if (seen != pick) {
                        ++seen;
                        continue;
                    }

                    engine->field_dd5 = 1;           // 0x001AC3D8
                    engine->field_dd6 =
                        static_cast<s8>(work->points[i].x);
                    engine->field_dd7 =
                        static_cast<s8>(work->points[i].y);

                    // 0x001AC3EC..0x001AC470
                    if (Flag_CheckEventBit(0x648)) {
                        engine->field_db0 = static_cast<u16>(
                            Random_Range(4) + 0x1C2);
                    } else if (Flag_CheckEventBit(0x6D2)) {
                        engine->field_db0 = static_cast<u16>(
                            Random_Range(3) + 0x1C2);
                    } else {
                        engine->field_db0 = static_cast<u16>(
                            Random_Range(2) + 0x1C2);
                    }
                    break;
                }
            }
        }
    }

reset_wall_types:
    // 0x001AC474..0x001AC4F4: classify every interior corridor cell from its
    // four orthogonal neighbours.  Non-corridor cells clear cell+0x41 only.
    for (s32 row = 1; row < engine->height - 1; ++row) {
        for (s32 col = 1; col < engine->width - 1; ++col) {
            MazeCell* const cell = MazeCellAt(engine, row, col);
            if (cell->state != 2) {
                cell->wall_kind = 0;
                continue;
            }
            u32 mask = 0;
            if (MazeCellAt(engine, row, col - 1)->state == 1) mask |= 1;
            if (MazeCellAt(engine, row, col + 1)->state == 1) mask |= 2;
            if (MazeCellAt(engine, row - 1, col)->state == 1) mask |= 4;
            if (MazeCellAt(engine, row + 1, col)->state == 1) mask |= 8;
            cell->wall_kind = g_MazeWallKinds[mask];    // 0x001AC71C
            cell->wall_style = g_MazeWallStyles[mask];  // 0x001AC724
        }
    }

    // 0x001AC4F8: publish the ready flag to the map script.
    script_vm_func_002854ec(1);

place_models:
    // ------------------------------------------------------------------
    // 0x001AC500..0x001AC9A0: count wall kinds over eight view angles and
    // build one model (plus clones) per non-empty kind.
    // ------------------------------------------------------------------
    {
        // 0x001AC518..0x001AC590: five per-kind maxima.
        for (s32 type = 0; type < 5; ++type) {
            s32 count = 0;
            for (s32 row = 1; row < engine->height - 1; ++row) {
                for (s32 col = 1; col < engine->width - 1; ++col) {
                    const MazeCell* const cell = MazeCellAt(engine, row, col);
                    if ((cell->wall_kind >> 4) == type) {
                        ++count;                // 0x001AC738
                    }
                }
            }
            work->type_count[type] = count;
        }

        // 0x001AC594..0x001AC7FC: eight 45-degree sweeps.  The helper at
        // 0x002E294C classifies the cells for one world origin/angle; the
        // maxima are kept in [sp+0x28..0x30] and r6/r7.
        s32 best_kind0 = 0;
        s32 best_kind1 = 0;
        s32 best_kind2 = 0;
        s32 best_kind3 = 0;
        s32 best_kind4 = 0;
        for (s32 row = 1; row < engine->height - 1; ++row) {
            for (s32 col = 1; col < engine->width - 1; ++col) {
                for (s32 angle_index = 0; angle_index < 8; ++angle_index) {
                    s32 counts[6] = {0, 0, 0, 0, 0, 0};
                    const f32 x = 250.0f + static_cast<f32>(col) * 500.0f;
                    const f32 y = 250.0f + static_cast<f32>(row) * 500.0f;
                    const f32 angle = 45.0f * static_cast<f32>(angle_index);

                    // 0x001AC684: the listing leaves r0 from the preceding
                    // call (engine width - 1) and passes (s0=x, s1=y,
                    // s2=angle, s3=col); the callee ignores r0.
                    engine_func_002e294c(
                        static_cast<u32>(engine->width - 1), x, y, angle,
                        static_cast<f32>(col));

                    // 0x001AC688..0x001AC750: count the cells flagged at
                    // cell+0x06, bucketed by the high nibble of +0x05.
                    for (s32 r = 0; r < engine->height; ++r) {
                        for (s32 c = 0; c < engine->width; ++c) {
                            const MazeCell* const cell = MazeCellAt(engine, r, c);
                            if (cell->field_06 == 1) {
                                const u32 type = cell->wall_kind >> 4;
                                if (type < 6) {
                                    ++counts[type];
                                }
                            }
                        }
                    }

                    // 0x001AC760..0x001AC7B8
                    if (counts[0] > best_kind0) best_kind0 = counts[0];
                    if (counts[1] > best_kind1) best_kind1 = counts[1];
                    if (counts[2] > best_kind2) best_kind2 = counts[2];
                    if (counts[3] > best_kind3) best_kind3 = counts[3];
                    if (counts[4] > best_kind4) best_kind4 = counts[4];
                }
            }
        }

        // 0x001AC800..0x001AC838
        work->type_count[0] = best_kind0;
        work->type_count[1] = best_kind1;
        work->type_count[2] = best_kind2;
        work->type_count[3] = best_kind3;
        work->type_count[4] = best_kind4;
        work->type_count[5] = 2;                 // 0x001AC80C
        if (engine->carved > 0) {
            work->type_count[5] = engine->carved + 2;  // 0x001AC838
        }

        // 0x001AC83C..0x001AC99C: one model per non-empty kind.
        char path[0x80];
        for (s32 type = 0; type < 6; ++type) {
            if (work->type_count[type] <= 0) {
                continue;
            }
            if (script_vm_func_002857e4() == 0) {
                UiText_Format(path, "map/mr01/mr01_%02d.bam", type + 1);
            } else {
                UiText_Format(path, "map/mr02/mr02_%02d.bam", type + 1);
            }

            u32 kind;
            if (type >= 1 && type <= 3) {
                kind = 0x38;                    // 0x001AC934
            } else {
                kind = 7;                       // 0x001AC878 / 0x001AC94C
            }
            void* const model = engine_func_0029bddc(path, kind);
            work->model[type] = static_cast<u32>(
                reinterpret_cast<std::uintptr_t>(model));

            engine_func_002a06c8(model, 1);     // 0x001AC898

            const s32 count = work->type_count[type];
            if (count > 0) {
                work->instances[type][0] = model;   // 0x001AC8B4
                for (s32 i = 1; i < count; ++i) {
                    void* const clone = engine_func_0028549c(model, 1);
                    work->instances[type][i] = clone;   // 0x001AC978
                    engine_func_002a06c8(clone, 1);
                }
            }
        }
    }

    // 0x001AC9A0..0x001AC9B4
    engine_func_002ce434();
    engine_func_00284c14(0);

    // 0x001AC9B8..0x001ACA14: optional effect at the stored marker cell.
    if (engine->field_dd5 != 0) {
        const s32 x = engine->field_dd6;
        const s32 y = engine->field_dd7;
        const f32 fx = 250.0f + static_cast<f32>(x * 125) * 4.0f;
        const f32 fy = 250.0f + static_cast<f32>(y * 125) * 4.0f;
        engine_func_002e0200(engine->field_db0, fx, 0.0f, fy);
        script_vm_func_00284aa8();              // 0x001ACA14
    }

    // ------------------------------------------------------------------
    // 0x001ACA1C..0x001ACCA8: sample candidate cells.  Map id 8 uses the
    // even columns only; every other map uses odd rows/columns.
    // ------------------------------------------------------------------
    {
        const bool special = script_vm_func_002857e4() == 8;
        work->marker_count = 0;

        s32 attempts;
        s32 col_start;
        if (special) {
            attempts = retry;                   // [sp+0x24] keeps its entry value
            col_start = 2;
        } else {
            attempts = 0;
            col_start = 1;
        }

        do {
            for (s32 row = 1; row < engine->height - 1; row += 2) {
                for (s32 col = col_start; col < engine->width - 1; col += 2) {
                    const MazeCell* const cell = MazeCellAt(engine, row, col);
                    // 0x001ACA88..0x001ACAA4: skip start/goal and non-corridor.
                    if (cell->field_02 == 1 || cell->field_03 == 1) {
                        continue;
                    }
                    if (cell->state != 2) {
                        continue;
                    }
                    // 0x001ACBB0: 40% acceptance.
                    if (Random_Range(0x64) >= 0x28) {
                        continue;
                    }

                    // 0x001ACBE4..0x001ACC14: {0x18, 0, x, 0, y} is written
                    // at the current count slot first.
                    MazeMarker* const marker =
                        &work->markers[work->marker_count];
                    marker->kind = 0x18;
                    marker->pad_01 = 0;
                    marker->x = static_cast<s16>(
                        250.0f + static_cast<f32>(col) * 500.0f);
                    marker->pad_04 = 0;
                    marker->y = static_cast<s16>(
                        250.0f + static_cast<f32>(row) * 500.0f);

                    // 0x001ACC18..0x001ACC4C: reject duplicates.
                    bool duplicate = false;
                    for (s32 i = 0; i < work->marker_count; ++i) {
                        if (work->markers[i].x == marker->x &&
                            work->markers[i].y == marker->y) {
                            duplicate = true;
                            break;
                        }
                    }
                    if (duplicate) {
                        continue;
                    }

                    ++work->marker_count;       // 0x001ACC58
                    if (work->marker_count >= 0x10) {
                        goto markers_done;
                    }
                }
            }

            // 0x001ACC88..0x001ACCA4: retry up to three times when fewer
            // than five markers were found.
            if (work->marker_count >= 5) {
                break;
            }
            ++attempts;
        } while (attempts < 3);
    }

markers_done:
    work->ready = 1;                            // 0x001ACCA8
}
#endif

// Readable Maze Engine transition draft above; exact ARM body retained pending codegen recovery.
__attribute__((naked)) void engine_func_001aba94() {
    asm volatile(
        ".word 0xe92d4ff0, 0xed2d8b0a, 0xe24dd09c, 0xeb045c1d\n"
        ".word 0xe1a0a000, 0xe3a00001, 0xe58d0024, 0xe3a00004\n"
        ".word 0xeb045444, 0xe2801001, 0xe3a00000, 0xe58d0020\n"
        ".word 0xe20100ff, 0xe58d0010, 0xe3a00000, 0xe58d0014\n"
        ".word 0xeb036742, 0xe1a04000, 0xeb05acd2, 0xe2400001\n"
        ".word 0xe1900004, 0x0a000284, 0xe3a00000, 0xeb03669a\n"
        ".word 0xe59fbdc0, 0xe3a00000, 0xe3540000, 0xe3e06000\n"
        ".word 0xe58b024c, 0x0a000066, 0xe59f0dac, 0xe0841204\n"
        ".word 0xe0805101, 0xe7904101, 0xe5d50006, 0xe5ca0dd0\n"
        ".word 0xe5d50007, 0xe5ca0dd1, 0xe3a00001, 0xeb03668a\n"
        ".word 0xe59f0d88, 0xe28a1c0d, 0xe3a0c000, 0xe19000da\n"
        ".word 0xe3700001, 0x15ca6791, 0xe1d10dd1, 0xe3500000\n"
        ".word 0xda00001d, 0xe3a07002, 0xe3a06001, 0xe3a09000\n"
        ".word 0xe1d12dd0, 0xe3a00000, 0xe3520000, 0xc06c820c\n"
        ".word 0xc08a2188, 0xda000010, 0xe0883000, 0xe7d4b003\n"
        ".word 0xe35b0001, 0xe082b180, 0x15cb703c, 0x05cb603c\n"
        ".word 0xe7d43003, 0xe3530002, 0x0a000036, 0xe3530003\n"
        ".word 0xe0823180, 0x15c39043, 0x0a000038, 0xe1d13dd0\n"
        ".word 0xe2800001, 0xe1530000, 0xcaffffee, 0xe1d10dd1\n"
        ".word 0xe28cc001, 0xe150000c, 0xcaffffe4, 0xe1d500dc\n"
        ".word 0xe5ca0dcc, 0xe1d520dd, 0xe3500000, 0xe5ca2dcd\n"
        ".word 0xe5d5300e, 0xc3520000, 0xe5ca3dce, 0xe5d5300f\n"
        ".word 0xe5ca3dcf, 0xda000004, 0xe0623202, 0xe3a02001\n"
        ".word 0xe08a3183, 0xe0830180, 0xe5c0203e, 0xe1d12cdf\n"
        ".word 0xe1d11cde, 0xe3a00001, 0xe0622202, 0xe08a2182\n"
        ".word 0xe0821181, 0xe5c1003f, 0xe1d501f0, 0xe3500000\n"
        ".word 0x0a000002, 0xe5ca003a, 0xe1d501b2, 0xe5ca003b\n"
        ".word 0xe59f2c7c, 0xe1d510f4, 0xe3a00000, 0xe3a03000\n"
        ".word 0xe5821008, 0xe58d0000, 0xe58d0004, 0xe20100ff\n"
        ".word 0xe1a02003, 0xe1a01003, 0xeb036626, 0xe320f000\n"
        ".word 0xe320f000, 0xea0001fd, 0xe0823180, 0xe5c36043\n"
        ".word 0xe5d130d4, 0xe2833001, 0xe5ca3dd4, 0xeaffffc6\n"
        ".word 0xe5c37043, 0xe5d130d4, 0xe2833001, 0xe5ca3dd4\n"
        ".word 0xeaffffc1, 0xe59f0c14, 0xe19000da, 0xe3500000\n"
        ".word 0xda000003, 0xe5ca0dd0, 0xe5ca0dd1, 0xe3a00001\n"
        ".word 0xeb036625, 0xe28a4c0d, 0xe5ca6791, 0xe3a00017\n"
        ".word 0xeb0453bc, 0xe59f6bec, 0xe59d1010, 0xe7d62100\n"
        ".word 0xe1520001, 0x03a00017, 0x0b0453b6, 0xe7d61100\n"
        ".word 0xe0860100, 0xe3a05000, 0xe5cb1248, 0xe5d01001\n"
        ".word 0xe1a09005, 0xe5cb1249, 0xe5d01002, 0xe5cb124a\n"
        ".word 0xe5d00003, 0xe5cb024b, 0xe08b0005, 0xe1d47dd2\n"
        ".word 0xe5d06248, 0xe1d48dd3, 0xeb045b7a, 0xe3560001\n"
        ".word 0xe320f000, 0x0a000006, 0xe3560002, 0x0a00000d\n"
        ".word 0xe3560003, 0x0a000014, 0xe3560004, 0x1a000024\n"
        ".word 0xea00001a, 0xe0681208, 0xe0800181, 0xe0800187\n"
        ".word 0xe5d01034, 0xe3510000, 0x05d0002c, 0x03500000\n"
        ".word 0x1a00001b, 0xea000019, 0xe0681208, 0xe0800181\n"
        ".word 0xe0800187, 0xe5d01044, 0xe3510000, 0x05d0004c\n"
        ".word 0x03500000, 0x1a000012, 0xea000010, 0xe0681208\n"
        ".word 0xe0800181, 0xe0800187, 0xe550103c, 0xe3510000\n"
        ".word 0x055000b4, 0x03500000, 0x1a000009, 0xea000007\n"
        ".word 0xe0681208, 0xe0800181, 0xe0800187, 0xe5d010b4\n"
        ".word 0xe3510000, 0x05d0012c, 0x03500000, 0x1a000000\n"
        ".word 0xe2899001, 0xe2855001, 0xe3550004, 0xbaffffc9\n"
        ".word 0xe3590002, 0xba000005, 0xe3a00063, 0xeb045371\n"
        ".word 0xe350003c, 0x33a00001, 0x23a00002, 0xe58d0020\n"
        ".word 0xe3a00000, 0xe1a05000, 0xe58d0004, 0xe08b9005\n"
        ".word 0xe1d47dd2, 0xe5d96248, 0xe1d48dd3, 0xeb045b39\n"
        ".word 0xe3560001, 0xe320f000, 0x0a000006, 0xe3560002\n"
        ".word 0x0a00000d, 0xe3560003, 0x0a000014, 0xe3560004\n"
        ".word 0x1a000079, 0xea00001a, 0xe0681208, 0xe0800181\n"
        ".word 0xe0800187, 0xe5d01034, 0xe3510000, 0x05d0002c\n"
        ".word 0x03500000, 0x1a000070, 0xea000019, 0xe0681208\n"
        ".word 0xe0800181, 0xe0800187, 0xe5d01044, 0xe3510000\n"
        ".word 0x05d0004c, 0x03500000, 0x1a000067, 0xea000010\n"
        ".word 0xe0681208, 0xe0800181, 0xe0800187, 0xe550103c\n"
        ".word 0xe3510000, 0x055000b4, 0x03500000, 0x1a00005e\n"
        ".word 0xea000007, 0xe0681208, 0xe0800181, 0xe0800187\n"
        ".word 0xe5d010b4, 0xe3510000, 0x05d0012c, 0x03500000\n"
        ".word 0x1a000055, 0xe1d46dd2, 0xe1d47dd3, 0xe5d98248\n"
        ".word 0xeb045b08, 0xe59b1244, 0xe3580001, 0xe7cb6081\n"
        ".word 0xe59b1244, 0xe08b1081, 0xe5c17001, 0xe59b1244\n"
        ".word 0xe2811001, 0xe58b1244, 0x0a000006, 0xe3580002\n"
        ".word 0x0a00000f, 0xe3580003, 0x0a000018, 0xe3580004\n"
        ".word 0x1a00002b, 0xea000020, 0xe0672207, 0xe3a01002\n"
        ".word 0xe0803182, 0xe0833186, 0xe2462002, 0xe5c3103c\n"
        ".word 0xe5c31034, 0xe5c3102c, 0xe5c02dd2, 0xe5c07dd3\n"
        ".word 0xea00001f, 0xe0672207, 0xe3a01002, 0xe0803182\n"
        ".word 0xe0833186, 0xe2862002, 0xe5c3103c, 0xe5c31044\n"
        ".word 0xe5c3104c, 0xe5c02dd2, 0xe5c07dd3, 0xea000014\n"
        ".word 0xe0672207, 0xe3a01002, 0xe0802182, 0xe0822186\n"
        ".word 0xe2473002, 0xe5c2103c, 0xe542103c, 0xe54210b4\n"
        ".word 0xe5c06dd2, 0xe5c03dd3, 0xea000009, 0xe0672207\n"
        ".word 0xe3a01002, 0xe0802182, 0xe0822186, 0xe2873002\n"
        ".word 0xe5c2103c, 0xe5c210b4, 0xe5c2112c, 0xe5c06dd2\n"
        ".word 0xe5c03dd3, 0xe59d0020, 0xe2400001, 0xe58d0020\n"
        ".word 0xe3a00001, 0xe58d0004, 0xe59d0020, 0xe3500000\n"
        ".word 0xe3a00001, 0xe58d0014, 0xe5d90248, 0xe58d0010\n"
        ".word 0xda00004a, 0xe59b1244, 0xe5d400d2, 0xe08b1081\n"
        ".word 0xe5410002, 0xe59b1244, 0xe5d400d3, 0xe08b1081\n"
        ".word 0xe5410001, 0xe5ca6dd2, 0xe5ca7dd3, 0xe2855001\n"
        ".word 0xe3550004, 0xbaffff74, 0xe59d0004, 0xe3500000\n"
        ".word 0x1a00003a, 0xe59d0014, 0xe3500000, 0x0a000015\n"
        ".word 0xe59b124c, 0xe1d42dd2, 0xe1d40dd3, 0xe3510010\n"
        ".word 0xaa00000e, 0xe0813081, 0xe3a01000, 0xe08b3103\n"
        ".word 0xe5832100, 0xe59b224c, 0xe0822082, 0xe08b2102\n"
        ".word 0xe5820104, 0xe59b024c, 0xe0800080, 0xe08b0100\n"
        ".word 0xe5801108, 0xe59b024c, 0xe2800001, 0xe58b024c\n"
        ".word 0xe3a00000, 0xe58d0014, 0xe59b0244, 0xe1a0600b\n"
        ".word 0xe3500000, 0x0a000020, 0xeb045a92, 0xe1a05000\n"
        ".word 0xe5960244, 0xe2400001, 0xe6ff0070, 0xeb0452b9\n"
        ".word 0xe5963244, 0xe1a02000, 0xe3a01000, 0xe2433001\n"
        ".word 0xe086c082, 0xe3530000, 0xe5863244, 0xe5dc3000\n"
        ".word 0xe1a00001, 0xe5c53dd2, 0xe5dc3001, 0xe5c53dd3\n"
        ".word 0xda00000a, 0xe1500002, 0x02811001, 0xe0863080\n"
        ".word 0xe086c081, 0xe2800001, 0xe1dcc0b0, 0xe2811001\n"
        ".word 0xe1c3c0b0, 0xe5963244, 0xe1530000, 0xcafffff4\n"
        ".word 0xe59d0024, 0xe3500000, 0x1afffedf, 0xe1d40dd1\n"
        ".word 0xe3a05000, 0xe3500000, 0xc3a06001, 0xc3a0c000\n"
        ".word 0xda000011, 0xe1d41dd0, 0xe3510000, 0xda00000a\n"
        ".word 0xe0652205, 0xe3a00000, 0xe08a3182, 0xe0832180\n"
        ".word 0xe2800001, 0xe5d2703c, 0xe5c2c043, 0xe3570000\n"
        ".word 0x05c2603c, 0xe2511001, 0x1afffff7, 0xe1d40dd1\n"
        ".word 0xe2855001, 0xe1500005, 0xcaffffed, 0xe320f000\n"
        ".word 0xeb045a58, 0xe3a01000, 0xe5c01dd5, 0xe5c01dd6\n"
        ".word 0xe1a06000, 0xe5c01dd7, 0xe59b024c, 0xe1a04001\n"
        ".word 0xe1a05001, 0xe3500002, 0xe1a07001, 0xe1a08001\n"
        ".word 0xba00005c, 0xe28b4c01, 0xe2401001, 0xe8940030\n"
        ".word 0xe3510000, 0xe1a0900b, 0xda000010, 0xe2897f43\n"
        ".word 0xe2892e11, 0xe289cf45, 0xe5970000, 0xe5923000\n"
        ".word 0xe287700c, 0xe0440000, 0xe3500000, 0xe0453003\n"
        ".word 0xb2600000, 0xe3530000, 0xb2633000, 0xe0800003\n"
        ".word 0xe2511001, 0xe282200c, 0xe48c000c, 0x1afffff1\n"
        ".word 0xe599024c, 0xe3a01001, 0xe2400001, 0xe3500001\n"
        ".word 0xda00001e, 0xe599224c, 0xe2810001, 0xe1520000\n"
        ".word 0xc0812081, 0xc0892102, 0xda000013, 0xe080c080\n"
        ".word 0xe5923108, 0xe089c10c, 0xe59c7108, 0xe1530007\n"
        ".word 0xda000009, 0xe28c8c01, 0xed920a40, 0xe282ac01\n"
        ".word 0xecd80a02, 0xe5928104, 0xecca0a02, 0xe5827108\n"
        ".word 0xed8c0a40, 0xe5ac8104, 0xe58c3004, 0xe599324c\n"
        ".word 0xe2800001, 0xe1530000, 0xcaffffeb, 0xe599024c\n"
        ".word 0xe2811001, 0xe2400001, 0xe1500001, 0xcaffffe0\n"
        ".word 0xe599124c, 0xe0810fa1, 0xe1a000c0, 0xe3500002\n"
        ".word 0xba00000a, 0xe2400001, 0xe6ff0070, 0xeb045235\n"
        ".word 0xe599124c, 0xe0410000, 0xe2400001, 0xe0802080\n"
        ".word 0xe0892102, 0xe5922108, 0xe3520005, 0xaa000000\n"
        ".word 0xe2410001, 0xe0652205, 0xe0800080, 0xe0891100\n"
        ".word 0xe2811c01, 0xe3a00001, 0xe8910180, 0xe0861182\n"
        ".word 0xe5c64dcc, 0xe5c65dcd, 0xe0811184, 0xe0682208\n"
        ".word 0xe5c67dce, 0xe0862182, 0xe0822187, 0xe5c68dcf\n"
        ".word 0xe5c1003e, 0xe5c2003f, 0xe59b024c, 0xe3500003\n"
        ".word 0xba000042, 0xe2400003, 0xe6ff0070, 0xeb045215\n"
        ".word 0xe59b924c, 0xe1a0c000, 0xe3a03000, 0xe3590000\n"
        ".word 0xe1a00003, 0xda000039, 0xe0801080, 0xe08b1101\n"
        ".word 0xe5912100, 0xe1520004, 0x0591a104, 0x015a0005\n"
        ".word 0x0a00001c, 0xe1520007, 0x05911104, 0x01510008\n"
        ".word 0x0a000018, 0xe15c0003, 0x12833001, 0x1a000015\n"
        ".word 0xe3700001, 0x0a000029, 0xe0800080, 0xe3a01001\n"
        ".word 0xe08b0100, 0xe5c61dd5, 0xe5901100, 0xe5c61dd6\n"
        ".word 0xe5900104, 0xe5c60dd7, 0xe59f04dc, 0xeb0451ec\n"
        ".word 0xe3500000, 0xe320f000, 0x0a00000a, 0xe3a00004\n"
        ".word 0xeb0451f0, 0xe2800c01, 0xe3a01edb, 0xe28000c2\n"
        ".word 0xe18100b6, 0xea000015, 0xe2800001, 0xe1590000\n"
        ".word 0xcaffffd8, 0xea000011, 0xe59f04a0, 0xeb0451dc\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000006, 0xe3a00003\n"
        ".word 0xeb0451e0, 0xe2800c01, 0xe3a01edb, 0xe28000c2\n"
        ".word 0xe18100b6, 0xea000005, 0xe3a00002, 0xeb0451d9\n"
        ".word 0xe2800c01, 0xe3a01edb, 0xe28000c2, 0xe18100b6\n"
        ".word 0xe320f000, 0xeb0459a7, 0xe2804c0d, 0xe3a0c001\n"
        ".word 0xe1d41dd1, 0xe2411001, 0xe3510001, 0xda000018\n"
        ".word 0xe59f743c, 0xe3a08000, 0xe2876010, 0xe1d41dd0\n"
        ".word 0xe3a03001, 0xe2411001, 0xe3510001, 0xc06c120c\n"
        ".word 0xc0805181, 0xda000009, 0xe0852183, 0xe5d2103c\n"
        ".word 0xe3510002, 0x15c28041, 0x0a000085, 0xe1d41dd0\n"
        ".word 0xe2833001, 0xe2411001, 0xe1510003, 0xcafffff5\n"
        ".word 0xe1d41dd1, 0xe28cc001, 0xe2411001, 0xe151000c\n"
        ".word 0xcaffffe9, 0xe3a00001, 0xeb0363fa, 0xe320f000\n"
        ".word 0xeb045984, 0xe1a05000, 0xe2800c0d, 0xe3a01000\n"
        ".word 0xe58d0078, 0xe1d00dd1, 0xe3a02000, 0xe3a0c001\n"
        ".word 0xe2404001, 0xe3540001, 0xda000011, 0xe59d0078\n"
        ".word 0xe1d07dd0, 0xe2476002, 0xe3560000, 0xda000009\n"
        ".word 0xe06c020c, 0xe1a03006, 0xe0850180, 0xe2800049\n"
        ".word 0xe5d08000, 0xe2800008, 0xe1510228, 0x02822001\n"
        ".word 0xe2533001, 0x1afffff9, 0xe28cc001, 0xe154000c\n"
        ".word 0xcafffff0, 0xe59f033c, 0xe0800101, 0xe2811001\n"
        ".word 0xe5802254, 0xe59d0078, 0xe3510005, 0xbaffffe0\n"
        ".word 0xe1d01dd1, 0xe3a06000, 0xe3a00001, 0xe58d0088\n"
        ".word 0xed9f9acc, 0xeddf8acc, 0xed9f8acc, 0xe2410001\n"
        ".word 0xe3500001, 0xe1a07006, 0xe58d6028, 0xe58d602c\n"
        ".word 0xe58d6030, 0xda00008c, 0xe28d8008, 0xeddf9ac4\n"
        ".word 0xed9faac4, 0xeddfaac4, 0xed9fbac4, 0xeddfbac4\n"
        ".word 0xed9fcac4, 0xeddfcac4, 0xe59d0078, 0xe1d01dd0\n"
        ".word 0xe3a00001, 0xe58d0084, 0xe2410001, 0xe3500001\n"
        ".word 0xda000075, 0xe3a04000, 0xed9d1a21, 0xeddd0a22\n"
        ".word 0xeeb00a48, 0xeef81ac1, 0xeeb81ae0, 0xe3540000\n"
        ".word 0xeef00a40, 0xee010aa8, 0xee410a28, 0x0eb01a49\n"
        ".word 0x0a000011, 0xe3540001, 0x0eb01a69, 0x0a00000e\n"
        ".word 0xe3540002, 0x0eb01a4a, 0x0a00000b, 0xe3540003\n"
        ".word 0x0eb01a6a, 0x0a000008, 0xe3540004, 0x0eb01a4b\n"
        ".word 0x0a000005, 0xe3540005, 0x0eb01a6b, 0x0a000002\n"
        ".word 0xe3540006, 0x0eb01a4c, 0x1eb01a6c, 0xe320f000\n"
        ".word 0xeb04d8b0, 0xe3a00000, 0xe58d0008, 0xe1a03000\n"
        ".word 0xe58d000c, 0xe58d0010, 0xe58d0014, 0xe58d0018\n"
        ".word 0xe58d001c, 0xe59d0078, 0xe1d0add1, 0xe35a0000\n"
        ".word 0xc1d09dd0, 0xda000028, 0xe3590000, 0xda000023\n"
        ".word 0xe0631203, 0xe1a00009, 0xe0852181, 0xe2821042\n"
        ".word 0xe2822041, 0xe5d1c000, 0xe35c0001, 0x1a000017\n"
        ".word 0xea000011, 0xe5d29034, 0xe3a01000, 0xe3590001\n"
        ".word 0xe5d29044, 0x03a01001, 0xe3590001, 0xe552903c\n"
        ".word 0x03811002, 0xe3590001, 0xe5d290b4, 0x03811004\n"
        ".word 0xe3590001, 0x03811008, 0xe7d79001, 0xe5c29041\n"
        ".word 0xe7d61001, 0xe5c21040, 0xeaffff67, 0xe5d2c000\n"
        ".word 0xe1a0c22c, 0xe798b10c, 0xe28bb001, 0xe788b10c\n"
        ".word 0xe2500001, 0xe2811008, 0xe2822008, 0x1affffe0\n"
        ".word 0xe2833001, 0xe15a0003, 0xcaffffd6, 0xe59d0008\n"
        ".word 0xe59d1028, 0xe2844001, 0xe1560000, 0xd1a06000\n"
        ".word 0xe59d000c, 0xe1570000, 0xd1a07000, 0xe59d0010\n"
        ".word 0xe1510000, 0xc1a00001, 0xe59d1014, 0xe58d0028\n"
        ".word 0xe59d002c, 0xe1500001, 0xd1a00001, 0xe59d1018\n"
        ".word 0xe58d002c, 0xe59d0030, 0xe1500001, 0xd1a00001\n"
        ".word 0xe3540008, 0xe58d0030, 0xbaffff92, 0xe59d0078\n"
        ".word 0xe1d01dd0, 0xe59d0084, 0xe2411001, 0xe2800001\n"
        ".word 0xe1500001, 0xe58d0084, 0xbaffff89, 0xe59d0078\n"
        ".word 0xe1d01dd1, 0xe59d0088, 0xe2411001, 0xe2800001\n"
        ".word 0xe1500001, 0xe58d0088, 0xbaffff7a, 0xe28d4028\n"
        ".word 0xe59f90b0, 0xe894000d, 0xe3a01002, 0xe2894f97\n"
        ".word 0xe5891268, 0xe884000d, 0xe2890f95, 0xe88000c0\n"
        ".word 0xe3a07000, 0xe59d0078, 0xe1d00dd4, 0xe3500000\n"
        ".word 0xc2800002, 0xc5890268, 0xe0895107, 0xe5950254\n"
        ".word 0xe3500000, 0xda000051, 0xeb0363e4, 0xe3500000\n"
        ".word 0xe2872001, 0x0a00002f, 0xe28f10a0, 0xe28d0038\n"
        ".word 0xfa0447e4, 0xe3570001, 0x13570002, 0x13570003\n"
        ".word 0x0a00002e, 0xe3570004, 0xe3a01007, 0xe28d0038\n"
        ".word 0x0a000030, 0xeb03bd53, 0xe585026c, 0xe595026c\n"
        ".word 0xe3a01001, 0xeb03cf8a, 0xe5950254, 0xe3a04000\n"
        ".word 0xe3500000, 0xc0896407, 0xda000038, 0xe595026c\n"
        ".word 0xe5860284, 0xea000031, 0x004bce8c, 0x00447f40\n"
        ".word 0x00000791, 0x0049f91c, 0x00447ec0, 0x00000648\n"
        ".word 0x000006d2, 0x00447f20, 0x00000000, 0x43fa0000\n"
        ".word 0x437a0000, 0x42340000, 0x42b40000, 0x43070000\n"
        ".word 0x43340000, 0x43610000, 0x43870000, 0x439d8000\n"
        ".word 0x2f70616d, 0x3230726d, 0x30726d2f, 0x30255f32\n"
        ".word 0x622e6432, 0x00006d61, 0xe28f1fe6, 0xe28d0038\n"
        ".word 0xfa0447b4, 0xe320f000, 0xe320f000, 0xeaffffcc\n"
        ".word 0xe3a01038, 0xe28d0038, 0xeb03bd26, 0xe585026c\n"
        ".word 0xe320f000, 0xeaffffd0, 0xe320f000, 0xeb03bd21\n"
        ".word 0xe51f10a0, 0xe581027c, 0xeaffffcb, 0xe3540000\n"
        ".word 0x0affffd1, 0xe595026c, 0xe3a01001, 0xeb0362c9\n"
        ".word 0xe0861104, 0xe5810284, 0xe3a01001, 0xeb03cf50\n"
        ".word 0xe5950254, 0xe2844001, 0xe1500004, 0xcafffff2\n"
        ".word 0xe2877001, 0xe3570005, 0xdaffffa6, 0xeb0486a3\n"
        ".word 0xe3a00000, 0xe320f000, 0xeb036098, 0xe320f000\n"
        ".word 0xe320f000, 0xeb045857, 0xe2800c0d, 0xe5d010d5\n"
        ".word 0xe3510000, 0x0a000012, 0xe1d02dd7, 0xe1d03dd6\n"
        ".word 0xe3a010fa, 0xe1d00bf0, 0xe082c082, 0xe06c2382\n"
        ".word 0xe0834083, 0xe0643383, 0xe0812102, 0xe0811103\n"
        ".word 0xee002a90, 0xee001a10, 0xeeb81ae0, 0xeeb80ac0\n"
        ".word 0xeef00a49, 0xeb04cdfc, 0xe320f000, 0xe320f000\n"
        ".word 0xeb036023, 0xe320f000, 0xeb04583e, 0xe58d0004\n"
        ".word 0xe320f000, 0xeb03636d, 0xe3500008, 0xe3a08018\n"
        ".word 0xe3a0a000, 0x0a00001b, 0xe3a00000, 0xe589a240\n"
        ".word 0xe58d0024, 0xe59d0004, 0xe2805c0d, 0xe3a07001\n"
        ".word 0xe1d50dd1, 0xe2400001, 0xe3500001, 0xda000088\n"
        ".word 0xe1d50dd0, 0xe3a04001, 0xe2400001, 0xe3500001\n"
        ".word 0xda00007e, 0xe59d1004, 0xe0670207, 0xe0816180\n"
        ".word 0xe0860184, 0xe5d0103e, 0xe3510001, 0x15d0103f\n"
        ".word 0x13510001, 0x0a000070, 0xe5d0003c, 0xe3500002\n"
        ".word 0x0a000041, 0xea00006c, 0xe59d0004, 0xe589a240\n"
        ".word 0xe3a07001, 0xe2805c0d, 0xe1d50dd1, 0xe2400001\n"
        ".word 0xe3500001, 0xda000076, 0xe1d50dd0, 0xe3a04002\n"
        ".word 0xe2400001, 0xe3500002, 0xda00002d, 0xe59d1004\n"
        ".word 0xe0670207, 0xe0816180, 0xe0860184, 0xe5d0103e\n"
        ".word 0xe3510001, 0x15d0103f, 0x13510001, 0x0a00001f\n"
        ".word 0xe5d0003c, 0xe3500002, 0x1a00001c, 0xe3a00064\n"
        ".word 0xeb04502c, 0xe3500028, 0xe320f000, 0x2a000017\n"
        ".word 0xee004a90, 0xee007a10, 0xe5990240, 0xeeb81ae0\n"
        ".word 0xeef81ac0, 0xeef00a48, 0xeeb00a48, 0xe0890180\n"
        ".word 0xe5e081c0, 0xe5c0a001, 0xee410a28, 0xee010aa8\n"
        ".word 0xeefd0ae0, 0xeebd0ac0, 0xee101a90, 0xee102a10\n"
        ".word 0xe1c010b2, 0xe1c0a0b4, 0xe1c020b6, 0xe5990240\n"
        ".word 0xe2800001, 0xe3500010, 0xe5890240, 0xaa000048\n"
        ".word 0xe1d50dd0, 0xe2844002, 0xe2400001, 0xe1500004\n"
        ".word 0xcaffffd4, 0xe1d50dd1, 0xe2877002, 0xe2400001\n"
        ".word 0xe1500007, 0xcaffffc7, 0xea00003d, 0xe3a00064\n"
        ".word 0xeb045004, 0xe3500028, 0xe320f000, 0x2a000026\n"
        ".word 0xee014a10, 0xee007a10, 0xeef00a48, 0xe5990240\n"
        ".word 0xeeb81ac1, 0xeef81ac0, 0xeeb00a60, 0xe0891180\n"
        ".word 0xe5e181c0, 0xe5c1a001, 0xee010a28, 0xee410aa8\n"
        ".word 0xeebd0ac0, 0xeefd0ae0, 0xee102a10, 0xee103a90\n"
        ".word 0xe6bf2072, 0xe1c120b2, 0xe6bfc073, 0xe1c1a0b4\n"
        ".word 0xe1c1c0b6, 0xe599b240, 0xe3a01000, 0xe35b0000\n"
        ".word 0xda000009, 0xe0893181, 0xe2833d07, 0xe1d3e0f2\n"
        ".word 0xe15e0002, 0x01d330f6, 0x0153000c, 0x0a000006\n"
        ".word 0xe2811001, 0xe15b0001, 0xcafffff5, 0xe28b0001\n"
        ".word 0xe3500010, 0xe5890240, 0xaa000011, 0xe1d50dd0\n"
        ".word 0xe2844002, 0xe2400001, 0xe1500004, 0xcaffff83\n"
        ".word 0xe1d50dd1, 0xe2877002, 0xe2400001, 0xe1500007\n"
        ".word 0xcaffff76, 0xe5990240, 0xe3500005, 0xaa000004\n"
        ".word 0xe59d0024, 0xe2800001, 0xe3500003, 0xe58d0024\n"
        ".word 0xbaffff69, 0xe3a00001, 0xe5c90250, 0xe28dd09c\n"
        ".word 0xecbd8b0a, 0xe8bd8ff0, 0x2f70616d, 0x3130726d\n"
        ".word 0x30726d2f, 0x30255f31, 0x622e6432, 0x00006d61\n");
}

// ---------------------------------------------------------------------------
// engine_func_0018844c (0x0018844C), 4,016 B
// ---------------------------------------------------------------------------
//
// Recovered role: the camp equipment/slot command state machine.  Commands
// 0x11..0x17 each select a 0x64-byte slot record (work+0x2A4 + index*0x64)
// and a parallel u16 id array; the routine then drives the five-state UI
// sequence at work+0x1C:
//   0: build the "player/pl_dammy.bam" model and fill slots 0..2
//   1: wait for the model and hide it below the screen
//   2: open the selected slot page
//   3: run the interaction (A/B/touch), rewrite the six-id table on confirm
//   4: close the page, destroy the model and hand control back to 0x0029933C
//
// All large-object offsets are the raw displacements in the listing; the
// header only asserts the small prefix.

// 0x0043DA90 (.data) is `smt4::camp::g_CampWork`, allocated by
// Camp_Init (0x0028A688) and shared with the camp menu.  The command
// routine only needs the prefix view `CampSlotCommandWork`, so it reuses the
// canonical pointer instead of declaring a second, producer-less global.

namespace {

inline u8* WorkBytes(CampSlotCommandWork* work) {
    return reinterpret_cast<u8*>(work);
}

template <typename T>
inline T& WorkField(CampSlotCommandWork* work, u32 offset) {
    return *reinterpret_cast<T*>(WorkBytes(work) + offset);
}

} // namespace

// DECOMP_FUNC(0x0018844c, 4016)
#if 0
void engine_func_0018844c(u32 command) {
    CampSlotCommandWork* const work =
        reinterpret_cast<CampSlotCommandWork*>(camp::g_CampWork);
    u16* const table =
        static_cast<u16*>(script_vm_func_002b66ec());  // 0x00188460

    // 0x00188468..0x00188564: command -> slot record and id-array base.
    u8* slot = nullptr;
    const u16* ids = nullptr;
    s32 uses_slot = 0;                          // r8
    switch (command) {
    case 0x11:
        slot = WorkBytes(work) + 0x2A4;
        ids = reinterpret_cast<const u16*>(WorkBytes(work) + 0x1E7C);
        break;
    case 0x12:
        slot = WorkBytes(work) + 0x308;
        ids = reinterpret_cast<const u16*>(WorkBytes(work) + 0x1F6C);
        break;
    case 0x13:
        slot = WorkBytes(work) + 0x36C;
        ids = reinterpret_cast<const u16*>(WorkBytes(work) + 0x205C);
        break;
    case 0x14:
        slot = WorkBytes(work) + 0x3D0;
        ids = reinterpret_cast<const u16*>(WorkBytes(work) + 0x20C0);
        uses_slot = 1;
        break;
    case 0x15:
        slot = WorkBytes(work) + 0x434;
        ids = reinterpret_cast<const u16*>(WorkBytes(work) + 0x21B0);
        uses_slot = 1;
        break;
    case 0x16:
        slot = WorkBytes(work) + 0x498;
        ids = reinterpret_cast<const u16*>(WorkBytes(work) + 0x22A0);
        uses_slot = 1;
        break;
    case 0x17:
        slot = WorkBytes(work) + 0x4FC;
        ids = reinterpret_cast<const u16*>(WorkBytes(work) + 0x2390);
        uses_slot = 1;
        break;
    default:
        break;
    }

    engine_func_0029a400(static_cast<s32>(command) - 0x11);  // 0x00188564

    switch (work->state) {                     // 0x00188568..0x00188574
    case 0: {
        // 0x00188590..0x00188664
        if (camp_func_0029e248() != 0) {
            return;
        }
        if (script_vm_func_0029e398() == 0) {
            return;
        }
        script_vm_func_0029a3c4(3);
        script_vm_func_0029c768(1);
        engine_func_0029a384(const_cast<u16*>(table));
        engine_func_0029a368(const_cast<u16*>(table));
        camp_func_0029d924(1);

        const s32 index =
            camp_func_0029f260(slot) + camp_func_0029f248(slot);
        const u32 selected = ids[index];

        // 0x00188608..0x001886AC: three ids, then the player model.
        u32 slot_id[3];
        if (command == 0x14) {
            slot_id[1] = table[4];
            slot_id[2] = table[5];
            slot_id[0] = selected;
        } else if (command == 0x15) {
            slot_id[0] = table[3];
            slot_id[2] = table[5];
            slot_id[1] = selected;
        } else if (command == 0x16) {
            slot_id[0] = table[3];
            slot_id[1] = table[4];
            slot_id[2] = selected;
        } else {
            slot_id[0] = table[3];
            slot_id[1] = table[4];
            slot_id[2] = table[5];
        }

        engine_func_0029a320(0, slot_id[0]);
        engine_func_0029a320(1, slot_id[1]);
        engine_func_0029a320(2, slot_id[2]);

        void* const model = engine_func_0029a2d0("player/pl_dammy.bam", 7);
        WorkField<void*>(work, 0x25C0) = model;      // 0x00188658

        ++work->state;                          // 0x00188854
        return;
    }

    case 1: {
        // 0x001886CC..0x00188750
        void* const model = WorkField<void*>(work, 0x25C0);
        if (engine_func_002ae16c(model) != 0) {
            u8* const part =
                *reinterpret_cast<u8**>(static_cast<u8*>(model) + 8);
            if (*reinterpret_cast<s32*>(part + 0x0C) < 0) {
                engine_func_002a06c8(model, 1);
                engine_func_0029a2b0(part, 0, 0.0f, -10000.0f, 0.0f);
            }
        }
        if (ui_func_0029a25c() == 0) {
            return;
        }
        if (engine_func_002ae16c(model) == 0) {
            return;
        }
        if (uses_slot != 0) {
            work->field_032 = 1;                // 0x0018874C
        }
        ++work->state;
        return;
    }

    case 2: {
        // 0x00188754..0x00188850: one page-selection notification per
        // command, then the common list update.
        switch (command) {
        case 0x11:
            engine_func_0029a03c(0x11);
            engine_func_0029a020(0);
            break;
        case 0x12:
            engine_func_0029a03c(0x12);
            engine_func_0029a020(0);
            break;
        case 0x13:
            engine_func_0029a03c(0x13);
            engine_func_0029a020(0);
            break;
        case 0x14:
            engine_func_0029a03c(0x14);
            engine_func_0029a020(1);
            break;
        case 0x15:
            engine_func_0029a03c(0x15);
            engine_func_0029a020(0);
            break;
        case 0x16:
            engine_func_0029a03c(0x16);
            engine_func_0029a020(2);
            break;
        case 0x17:
            engine_func_0029a03c(0x17);
            engine_func_0029a020(0);
            break;
        default:
            break;
        }

        work->field_033 = 0;                    // 0x00188834
        engine_func_00299e60(slot, 0);
        engine_func_00299b9c(command);
        if (uses_slot == 0) {
            engine_func_002999e8(command);      // 0x00188850
        }
        ++work->state;
        return;
    }

    case 3: {
        // 0x00188868..0x00189318
        const s8 slot_61 = reinterpret_cast<const s8*>(slot)[0x61];
        const s8 slot_60 = reinterpret_cast<const s8*>(slot)[0x60];

        if (work->field_024 == 0x29) {
            work->field_024 = 0x1A;             // 0x0018887C
            if (uses_slot == 0) {
                engine_func_002999e8(command);
                goto state3_buttons;
            }
            ui_func_00299974(0);
            work->field_032 = 1;
            goto state3_buttons;
        }

    state3_buttons:
        // 0x001888A0..0x001888E0
        if (slot_61 != 0 || slot_60 != 0) {
            if (uses_slot == 0) {
                goto state3_active;
            }
            ui_func_00299974(0);
            work->field_032 = 1;
            goto state3_active;
        }

        if (work->field_032 != 0) {
            // 0x001888F0..0x00188990: commit the row under the cursor.
            const s32 index =
                camp_func_0029f260(slot) + camp_func_0029f248(slot);
            const u32 id = ids[index];
            if (command == 0x14) {
                ui_func_002998d8(0, id);
            } else if (command == 0x15) {
                ui_func_002998d8(1, id);
            } else if (command == 0x16) {
                ui_func_002998d8(2, id);
            }
            if (uses_slot != 0) {
                engine_func_002999e8(command);
            }
            work->field_032 = 0;
        } else {
            // 0x00188994..0x001889A4
            if (ui_func_0029a25c() != 0) {
                ui_func_00299974(1);
            }
        }

    state3_active:
        // 0x001889A8..0x00188A44
        if (ui_func_0029a25c() == 0) {
            return;
        }

        {
            void* const node = camp_func_002bf6d0(0x1D, 0x572);
            u8 flag14 = 0;                      // [sp+0x14]
            const s32 a3 = *reinterpret_cast<const s16*>(
                WorkBytes(work) + 0xE02);
            const s32 a4 = *reinterpret_cast<const s16*>(
                WorkBytes(work) + 0xE04);
            const s32 a5 = *reinterpret_cast<const s16*>(
                WorkBytes(work) + 0xE06);

            if (camp_func_0029f878(slot, node, WorkBytes(work) + 0xE0C,
                                   a3, a4, a5, &flag14, 0, 1) != 0 ||
                camp_func_0029f278(slot, 1) != 0) {
                engine_func_00299b9c(command);
                engine_func_002999e8(command);
                return;
            }

            // 0x00188A50..0x00188A58: A/confirm unless the B byte is set.
            if (camp_func_002c1830(0, 1) != 0 || flag14 != 0) {
                // 0x00188A5C..0x00188BB4: confirm the row into the table.
                const s32 index =
                    camp_func_0029f260(slot) + camp_func_0029f248(slot);
                const u32 id = ids[index];
                if (engine_func_00299874(id) == 0) {
                    camp_func_002bc200(0x0100016E);  // 0x00188BB8
                    return;
                }

                s32 changed = 1;
                switch (command) {
                case 0x11: {
                    const u16 old = table[0];
                    table[0] = static_cast<u16>(id);
                    if (old == static_cast<u16>(id)) changed = 0;
                    break;
                }
                case 0x12: {
                    const u16 old = table[1];
                    table[1] = static_cast<u16>(id);
                    if (old == static_cast<u16>(id)) changed = 0;
                    break;
                }
                case 0x13: {
                    const u16 old = table[2];
                    table[2] = static_cast<u16>(id);
                    if (old == static_cast<u16>(id)) changed = 0;
                    break;
                }
                case 0x14: {
                    const u16 old = table[3];
                    table[3] = static_cast<u16>(id);
                    if (old == static_cast<u16>(id)) changed = 0;
                    break;
                }
                case 0x15: {
                    const u16 old = table[4];
                    table[4] = static_cast<u16>(id);
                    if (old == static_cast<u16>(id)) changed = 0;
                    break;
                }
                case 0x16: {
                    const u16 old = table[5];
                    table[5] = static_cast<u16>(id);
                    if (old == static_cast<u16>(id)) changed = 0;
                    break;
                }
                case 0x17: {
                    const u16 old = table[6];
                    table[6] = static_cast<u16>(id);
                    if (old == static_cast<u16>(id)) changed = 0;
                    break;
                }
                default:
                    break;
                }

                engine_func_0029960c(0);        // 0x00188B70
                if (changed == 0) {
                    return;
                }
                engine_func_0029a384(const_cast<u16*>(table));
                engine_func_0029a368(const_cast<u16*>(table));
                camp_func_002bc200(0x0100016D);
                script_vm_func_002bf9e8(0x0100025F);
                return;
            }

            // 0x00188BC8..0x00188C20: B/cancel path.
            if (camp_func_002c1830(1, 1) != 0) {
                ui_func_00299974(0);
                engine_func_0029957c(0);
                engine_func_0029957c(1);
                engine_func_0029957c(2);
                ++work->state;                  // 0x00188C0C
                camp_func_002bc200(0x0100016E);
                return;
            }

            const s8 touch_a = *reinterpret_cast<const s8*>(
                WorkBytes(work) + 0xE08);
            const s8 touch_b = *reinterpret_cast<const s8*>(
                WorkBytes(work) + 0xE0A);
            if (camp_func_002c1830(8, 0) != 0 ||
                ui_func_0029d8fc(touch_a) == 6) {
                // 0x00188C68: scan records downward.
                const s32 index =
                    camp_func_0029f260(slot) + camp_func_0029f248(slot);
                const u32 id = ids[index];

                if (command == 0x14) {
                    if (table[3] != static_cast<u16>(id)) {
                        engine_func_0029957c(0);
                        ui_func_00299974(0);
                        work->field_032 = 1;
                    }
                } else if (command == 0x15) {
                    if (table[4] != static_cast<u16>(id)) {
                        engine_func_0029957c(1);
                        ui_func_00299974(0);
                        work->field_032 = 1;
                    }
                } else if (command == 0x16) {
                    if (table[5] != static_cast<u16>(id)) {
                        ui_func_00299974(0);
                        work->field_032 = 1;
                    }
                }

                // 0x00188D1C..0x00188DF4: find the previous non-empty
                // record and select it.
                s32 row = engine_func_0029eba8(WorkBytes(work) + 0x34);
                s32 i = 0;
                const s32 count =
                    engine_func_0029ebf8(WorkBytes(work) + 0x34);
                if (count > 0) {
                    for (;;) {
                        if (--row < 0) {
                            row = engine_func_0029ebf8(
                                      WorkBytes(work) + 0x34) - 1;
                        }
                        u8* const record = WorkBytes(work) + row * 0x64;
                        s32 sub = engine_func_0029ebf8(record + 0x2A4);
                        if (!Flag_CheckEventBit(0x410) && row > 0) {
                            sub = engine_func_0029ebf8(record + 0x36C);
                        }
                        if (sub > 0) {
                            engine_func_00299558(WorkBytes(work) + 0x34, row);
                            const s32 current = engine_func_0029eba8(
                                WorkBytes(work) + 0x34);
                            engine_func_002994b4(work->field_098, current);
                            engine_func_00299b9c(command);
                            break;
                        }
                        ++i;
                        if (engine_func_0029ebf8(
                                WorkBytes(work) + 0x34) <= i) {
                            break;
                        }
                    }
                }

                engine_func_00299410(slot, 0);
                work->state = 2;
                switch (command) {
                case 0x11:
                    script_vm_func_002b8b78(
                        Flag_CheckEventBit(0x410) ? 14 : 21);
                    break;
                case 0x12:
                    script_vm_func_002b8b78(15);
                    break;
                case 0x13:
                    script_vm_func_002b8b78(16);
                    break;
                case 0x14:
                    script_vm_func_002b8b78(
                        Flag_CheckEventBit(0x410) ? 17 : 22);
                    break;
                case 0x15:
                    script_vm_func_002b8b78(18);
                    break;
                case 0x16:
                    script_vm_func_002b8b78(19);
                    break;
                case 0x17:
                    script_vm_func_002b8b78(20);
                    break;
                default:
                    break;
                }
                camp_func_002bc200(0x0100016F);
                return;
            }

            // 0x00188F04: scan records upward.  Both the "7" button and
            // the +0xE0A touch branch jump to this block (0x00188EAC).
            auto scan_up = [&]() {
                s32 row = engine_func_0029eba8(WorkBytes(work) + 0x34) + 1;
                const s32 count =
                    engine_func_0029ebf8(WorkBytes(work) + 0x34);
                if (row >= count) {
                    row = 0;
                }

                const s32 index =
                    camp_func_0029f260(slot) + camp_func_0029f248(slot);
                const u32 id = ids[index];

                if (command == 0x14) {
                    if (table[3] != static_cast<u16>(id)) {
                        engine_func_0029957c(0);
                        ui_func_00299974(0);
                        work->field_032 = 1;
                    }
                } else if (command == 0x15) {
                    if (table[4] != static_cast<u16>(id)) {
                        engine_func_0029957c(1);
                        ui_func_00299974(0);
                        work->field_032 = 1;
                    }
                } else if (command == 0x16) {
                    if (table[5] != static_cast<u16>(id)) {
                        engine_func_0029957c(2);
                        ui_func_00299974(0);
                        work->field_032 = 1;
                    }
                }

                s32 i = 0;
                if (count > 0) {
                    for (;;) {
                        u8* const record = WorkBytes(work) + row * 0x64;
                        s32 sub = engine_func_0029ebf8(record + 0x2A4);
                        if (!Flag_CheckEventBit(0x410) && row > 0) {
                            sub = engine_func_0029ebf8(record + 0x36C);
                        }
                        if (sub > 0) {
                            engine_func_00299558(WorkBytes(work) + 0x34, row);
                            const s32 current = engine_func_0029eba8(
                                WorkBytes(work) + 0x34);
                            engine_func_002994b4(work->field_098, current);
                            engine_func_00299b9c(command);
                            break;
                        }
                        ++row;
                        if (row >= engine_func_0029ebf8(
                                       WorkBytes(work) + 0x34)) {
                            row = 0;
                        }
                        ++i;
                        if (i >= count) {
                            break;
                        }
                    }
                }

                engine_func_00299410(slot, 0);
                work->state = 2;
                switch (command) {
                case 0x11:
                    script_vm_func_002b8b78(
                        Flag_CheckEventBit(0x410) ? 14 : 21);
                    break;
                case 0x12:
                    script_vm_func_002b8b78(15);
                    break;
                case 0x13:
                    script_vm_func_002b8b78(16);
                    break;
                case 0x14:
                    script_vm_func_002b8b78(
                        Flag_CheckEventBit(0x410) ? 17 : 22);
                    break;
                case 0x15:
                    script_vm_func_002b8b78(18);
                    break;
                case 0x16:
                    script_vm_func_002b8b78(19);
                    break;
                case 0x17:
                    script_vm_func_002b8b78(20);
                    break;
                default:
                    break;
                }
                camp_func_002bc200(0x0100016F);
            };

            if (camp_func_002c1830(7, 0) != 0) {
                scan_up();
                return;
            }

            // 0x00188E9C..0x00189318: third touch/button case.
            if (ui_func_0029d8fc(touch_b) == 6) {
                scan_up();                       // 0x00188EAC -> 0x00188F04
                return;
            }
            if (camp_func_002c1830(9, 1) == 0) {
                return;
            }

            switch (command) {
            case 0x11:
                SortMenu_Init(5, 0);
                engine_func_0029e5c8(6);
                engine_func_0029e5c8(0x11);
                engine_func_0029e5c8(0x12);
                engine_func_0029e5c8(3);
                break;
            case 0x12:
                SortMenu_Init(6, 0);
                engine_func_0029e5c8(6);
                engine_func_0029e5c8(0x11);
                engine_func_0029e5c8(0x12);
                engine_func_0029e5c8(3);
                break;
            case 0x13:
                SortMenu_Init(7, 0);
                engine_func_0029e5c8(6);
                engine_func_0029e5c8(0x1F);
                engine_func_0029e5c8(0x13);
                engine_func_0029e5c8(3);
                break;
            case 0x14:
                SortMenu_Init(8, 0);
                engine_func_0029e5c8(4);
                engine_func_0029e5c8(0x24);
                engine_func_0029e5c8(0x25);
                engine_func_0029e5c8(0x26);
                engine_func_0029e5c8(0x27);
                engine_func_0029e5c8(0x28);
                engine_func_0029e5c8(3);
                break;
            case 0x16:
                SortMenu_Init(0xA, 0);
                engine_func_0029e5c8(4);
                engine_func_0029e5c8(0x24);
                engine_func_0029e5c8(0x25);
                engine_func_0029e5c8(0x26);
                engine_func_0029e5c8(0x27);
                engine_func_0029e5c8(0x28);
                engine_func_0029e5c8(3);
                break;
            case 0x15:
                SortMenu_Init(9, 0);
                engine_func_0029e5c8(4);
                engine_func_0029e5c8(0x32);
                engine_func_0029e5c8(3);
                break;
            case 0x17:
                SortMenu_Init(0xB, 0);
                engine_func_0029e5c8(0x33);
                engine_func_0029e5c8(3);
                break;
            default:
                break;
            }

            // 0x001892D4..0x00189314
            camp_func_0029f10c(0, 0x323232FF);
            work->field_033 = 1;
            work->field_031 = camp_func_002b8ccc();
            WorkField<u32>(work, 0x24) = WorkField<u32>(work, 0x18);
            WorkField<u32>(work, 0x18) = 0x28;
            WorkField<u32>(work, 0x1C) = 0;
            WorkField<u32>(work, 0x14) = 0;
            camp_func_002bc200(0x0100016D);
            return;
        }
    }

    case 4: {
        // 0x0018931C..0x001893E0
        if (ui_func_0029a25c() == 0) {
            return;
        }
        engine_func_0029a400(-1);
        script_vm_func_0029c768(0);
        script_vm_func_0029ccf8();
        script_vm_func_0029a3c4(0);
        engine_func_00299b9c(0);
        camp_func_002bdac0(WorkBytes(work) + 0x6D4, 3, 0);
        work->field_020 = 6;                    // 0x00189380

        // 0x00189384..0x001893A4: republish the command state before the
        // model is destroyed: +0x24 <- +0x18, +0x18 <- 5, +0x1C <- 0,
        // +0x14 <- 0.
        WorkField<u32>(work, 0x24) = WorkField<u32>(work, 0x18);
        WorkField<u32>(work, 0x18) = 5;
        WorkField<u32>(work, 0x1C) = 0;
        WorkField<u32>(work, 0x14) = 0;

        void* const model = WorkField<void*>(work, 0x25C0);
        script_vm_func_002a7aa0(model);          // 0x001893AC
        WorkField<void*>(work, 0x25C0) = nullptr;
        engine_func_00299410(slot, 0);
        engine_func_002993d4();
        camp_func_0029e8e8(1, 0);
        camp_func_0029933c();                   // 0x001893E0 tail call
        return;
    }

    default:
        return;                                 // 0x00188578 -> 0x00188860
    }
}
#endif

// Readable camp event runtime draft above; exact ARM body retained pending codegen recovery.
__attribute__((naked)) void engine_func_0018844c(u32 command) {
    asm volatile(
        ".word 0xe92d4ff0, 0xe1a05000, 0xe24dd01c, 0xe59f04dc\n"
        ".word 0xe5904000, 0xeb04b8a1, 0xe3a08000, 0xe3550011\n"
        ".word 0xe1a06000, 0xe1a09008, 0xe1a07008, 0x0a00000c\n"
        ".word 0xe3550012, 0x0a00000f, 0xe3550013, 0x0a000012\n"
        ".word 0xe3550014, 0x0a000015, 0xe3550015, 0x0a00001a\n"
        ".word 0xe3550016, 0x0a000021, 0xe3550017, 0x0a000028\n"
        ".word 0xea00002d, 0xe2847b07, 0xe2849fa9, 0xe2877f9f\n"
        ".word 0xe3a00000, 0xea000027, 0xe2847b07, 0xe2849fc2\n"
        ".word 0xe2877fdb, 0xe3a00001, 0xea000022, 0xe2847a02\n"
        ".word 0xe2849fdb, 0xe287705c, 0xe3a00002, 0xea00001d\n"
        ".word 0xe2849e3d, 0xe2847d83, 0xe3a00003, 0xeb0447c0\n"
        ".word 0xe3a08001, 0xe320f000, 0xea000017, 0xe2849b01\n"
        ".word 0xe2847a02, 0xe2899034, 0xe2877e1b, 0xe3a00004\n"
        ".word 0xeb0447b7, 0xe3a08001, 0xe320f000, 0xea00000e\n"
        ".word 0xe2849b01, 0xe2847a02, 0xe2899098, 0xe2877e2a\n"
        ".word 0xe3a00005, 0xeb0447ae, 0xe3a08001, 0xe320f000\n"
        ".word 0xea000005, 0xe2849b01, 0xe2847a02, 0xe28990fc\n"
        ".word 0xe2877e39, 0xe3a00006, 0xeb0447a5, 0xe594001c\n"
        ".word 0xe3a0a000, 0xe3500005, 0x379ff100, 0xea0000b8\n"
        ".word 0x00188590, 0x001886cc, 0x00188754, 0x00188868\n"
        ".word 0x0018931c, 0xe320f000, 0xeb04572b, 0xe3500000\n"
        ".word 0xe320f000, 0x1a0000ae, 0xeb04577b, 0xe3500000\n"
        ".word 0xe320f000, 0x0a0000aa, 0xe3a00003, 0xeb044781\n"
        ".word 0xe3a00001, 0xe320f000, 0xeb045067, 0xe1a00006\n"
        ".word 0xe320f000, 0xeb04476b, 0xe1a00006, 0xe320f000\n"
        ".word 0xeb044761, 0xe3a00001, 0xe320f000, 0xeb0454cd\n"
        ".word 0xe1a00009, 0xe320f000, 0xeb045b19, 0xe1a08000\n"
        ".word 0xe1a00009, 0xeb045b10, 0xe0800008, 0xe3550014\n"
        ".word 0xe0870080, 0xe1d070b0, 0x0a000012, 0xe3550015\n"
        ".word 0x0a000019, 0xe1d610b6, 0xe3550016, 0xe3a00000\n"
        ".word 0x0a00001e, 0xeb04473a, 0xe1d610b8, 0xe3a00001\n"
        ".word 0xeb044737, 0xe1d610ba, 0xe3a00002, 0xeb044734\n"
        ".word 0xe3a01007, 0xe28f0fba, 0xeb04471d, 0xe3a01d97\n"
        ".word 0xe7810004, 0xea00007b, 0xe1d610b8, 0xe3a00001\n"
        ".word 0xeb04472b, 0xe1d610ba, 0xe3a00002, 0xeb044728\n"
        ".word 0xe6ff1077, 0xe3a00000, 0xeaffffef, 0xe1d610b6\n"
        ".word 0xe3a00000, 0xeb044722, 0xe1d610ba, 0xe3a00002\n"
        ".word 0xeb04471f, 0xe6ff1077, 0xe3a00001, 0xeaffffe6\n"
        ".word 0xe320f000, 0xeb04471a, 0xe1d610b8, 0xe3a00001\n"
        ".word 0xeb044717, 0xe6ff1077, 0xe320f000, 0xeaffffdd\n"
        ".word 0xe2845d97, 0xe5950000, 0xeb0496a4, 0xe3500000\n"
        ".word 0xe320f000, 0x0a00000d, 0xe5950000, 0xe5901008\n"
        ".word 0xe591100c, 0xe3510000, 0xaa000008, 0xe3a01001\n"
        ".word 0xeb045ff1, 0xed9f0a93, 0xe5950000, 0xeddf0a92\n"
        ".word 0xeeb01a40, 0xe3a01000, 0xe5900008, 0xeb0446e4\n"
        ".word 0xe320f000, 0xeb0446cd, 0xe3500000, 0xe320f000\n"
        ".word 0x0a00004b, 0xe5950000, 0xeb04968c, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000046, 0xe3580000, 0x13a00001\n"
        ".word 0x15c40032, 0xea00003f, 0xe2450011, 0xe3500007\n"
        ".word 0x379ff100, 0xea000031, 0x00188780, 0x00188794\n"
        ".word 0x001887a8, 0x00188808, 0x001887c8, 0x0018881c\n"
        ".word 0x001887e8, 0xe3a00011, 0xeb04462c, 0xe3a00000\n"
        ".word 0xe320f000, 0xea000024, 0xe3a00012, 0xeb044627\n"
        ".word 0xe3a00000, 0xe320f000, 0xea00001f, 0xe3a00013\n"
        ".word 0xeb044622, 0xe3a00000, 0xe320f000, 0xeb044618\n"
        ".word 0xe320f000, 0xe320f000, 0xea000018, 0xe3a00015\n"
        ".word 0xeb04461a, 0xe3a00000, 0xe320f000, 0xeb044610\n"
        ".word 0xe320f000, 0xe320f000, 0xea000010, 0xe3a00017\n"
        ".word 0xeb044612, 0xe3a00000, 0xe320f000, 0xeb044608\n"
        ".word 0xe320f000, 0xe320f000, 0xea000008, 0xe3a00014\n"
        ".word 0xeb04460a, 0xe3a00001, 0xe320f000, 0xea000002\n"
        ".word 0xe3a00016, 0xeb044605, 0xe3a00002, 0xeb0445fc\n"
        ".word 0xe3a01000, 0xe1a00009, 0xe5c4a033, 0xeb044588\n"
        ".word 0xe1a00005, 0xe320f000, 0xeb0444d4, 0xe3580000\n"
        ".word 0x01a00005, 0x0b044464, 0xe594001c, 0xe2800001\n"
        ".word 0xe584001c, 0xe28dd01c, 0xe8bd8ff0, 0xe5940024\n"
        ".word 0xe3500029, 0x1a00000a, 0xe3a0001a, 0xe3580000\n"
        ".word 0xe5840024, 0x0a000004, 0xe3a00000, 0xeb044439\n"
        ".word 0xe3a00001, 0xe5c40032, 0xea000001, 0xe1a00005\n"
        ".word 0xeb044451, 0xe1a00009, 0xe1d006d1, 0xe3500000\n"
        ".word 0xe320f000, 0x1a000004, 0xe1a00009, 0xe1d006d0\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000006, 0xe3580000\n"
        ".word 0x0a000035, 0xe3a00000, 0xeb044426, 0xe3a00001\n"
        ".word 0xe5c40032, 0xea000030, 0xe5d40032, 0xe3500000\n"
        ".word 0x0a000028, 0xe1a00009, 0xeb045a59, 0xe1a0b000\n"
        ".word 0xe1a00009, 0xeb045a50, 0xe080000b, 0xe3550014\n"
        ".word 0xe0870080, 0xe1d000b0, 0x0a000010, 0xe3550015\n"
        ".word 0x06ff1070, 0x03a00001, 0x0a000012, 0xe3550016\n"
        ".word 0x06ff1070, 0x03a00002, 0x0a00000e, 0xea00000e\n"
        ".word 0x0043da90, 0x79616c70, 0x702f7265, 0x61645f6c\n"
        ".word 0x2e796d6d, 0x006d6162, 0x00000000, 0xc61c4000\n"
        ".word 0xe6ff1070, 0xe3a00000, 0xeb0443db, 0xe320f000\n"
        ".word 0xe320f000, 0xea000000, 0xeb0443d7, 0xe3580000\n"
        ".word 0x11a00005, 0xe5c4a032, 0x1b044417, 0xe320f000\n"
        ".word 0xe320f000, 0xea000004, 0xe320f000, 0xeb04462f\n"
        ".word 0xe3500000, 0x13a00001, 0x1b0443f2, 0xe320f000\n"
        ".word 0xeb04462a, 0xe3500000, 0xe320f000, 0x0affffa8\n"
        ".word 0xe59f1a20, 0xe3a0001d, 0xe5cda014, 0xeb04db40\n"
        ".word 0xe2848c0e, 0xe1a01000, 0xe1d800f6, 0xe28d3004\n"
        ".word 0xe3a0b001, 0xe28d2014, 0xe8830c05, 0xe2842b03\n"
        ".word 0xe2822f83, 0xe1d800f4, 0xe58d0000, 0xe1d830f2\n"
        ".word 0xe1a00009, 0xeb045b9c, 0xe3500000, 0xe320f000\n"
        ".word 0x1a000005, 0xe3a01001, 0xe1a00009, 0xeb045a16\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000006, 0xe1a00005\n"
        ".word 0xeb04445a, 0xe1a00005, 0xe320f000, 0xeb0443ea\n"
        ".word 0xe28dd01c, 0xe8bd8ff0, 0xe3a01001, 0xe3a00000\n"
        ".word 0xeb04e377, 0xe1dd11d4, 0xe1900001, 0x0a00005a\n"
        ".word 0xe1a00009, 0xeb0459fe, 0xe1a04000, 0xe1a00009\n"
        ".word 0xeb0459f5, 0xe0800004, 0xe0877080, 0xe1d700b0\n"
        ".word 0xeb04437c, 0xe3500000, 0xe320f000, 0x0a00004a\n"
        ".word 0xe3550011, 0xe3a04001, 0x0a00000c, 0xe3550012\n"
        ".word 0x0a000010, 0xe3550013, 0x0a000014, 0xe3550014\n"
        ".word 0x0a000018, 0xe3550015, 0x0a00001c, 0xe3550016\n"
        ".word 0x0a000020, 0xe3550017, 0x0a000024, 0xea000028\n"
        ".word 0xe1d700b0, 0xe1d610b0, 0xe1c600b0, 0xe1510000\n"
        ".word 0x03a04000, 0xea000022, 0xe1d700b0, 0xe1d610b2\n"
        ".word 0xe1c600b2, 0xe1510000, 0x03a04000, 0xea00001c\n"
        ".word 0xe1d700b0, 0xe1d610b4, 0xe1c600b4, 0xe1510000\n"
        ".word 0x03a04000, 0xea000016, 0xe1d700b0, 0xe1d610b6\n"
        ".word 0xe1c600b6, 0xe1510000, 0x03a04000, 0xea000010\n"
        ".word 0xe1d700b0, 0xe1d610b8, 0xe1c600b8, 0xe1510000\n"
        ".word 0x03a04000, 0xea00000a, 0xe1d700b0, 0xe1d610ba\n"
        ".word 0xe1c600ba, 0xe1510000, 0x03a04000, 0xea000004\n"
        ".word 0xe1d700b0, 0xe1d610bc, 0xe1c600bc, 0xe1510000\n"
        ".word 0x03a04000, 0xe3a00000, 0xeb0442a4, 0xe3540000\n"
        ".word 0xe320f000, 0x0affff36, 0xe1a00006, 0xeb0445fd\n"
        ".word 0xe1a00006, 0xe320f000, 0xeb0445f3, 0xe59f0848\n"
        ".word 0xe320f000, 0xeb04cd96, 0xe59f0840, 0xe320f000\n"
        ".word 0xeb04db8d, 0xe28dd01c, 0xe8bd8ff0, 0xe59f0830\n"
        ".word 0xeb04cd8f, 0xe28dd01c, 0xe8bd8ff0, 0xe3a01001\n"
        ".word 0xe1a00001, 0xeb04e316, 0xe3500000, 0xe320f000\n"
        ".word 0x0a00000f, 0xe3a00000, 0xeb044362, 0xe3a00000\n"
        ".word 0xe320f000, 0xeb044261, 0xe3a00001, 0xe320f000\n"
        ".word 0xeb04425e, 0xe3a00002, 0xe320f000, 0xeb04425b\n"
        ".word 0xe594001c, 0xe2800001, 0xe584001c, 0xe59f07d0\n"
        ".word 0xea00009b, 0xe3a01000, 0xe3a00008, 0xeb04e300\n"
        ".word 0xe3500000, 0xe320f000, 0x1a00000b, 0xe1d800f8\n"
        ".word 0xeb04532e, 0xe3500006, 0xe320f000, 0x0a000006\n"
        ".word 0xe3a01000, 0xe3a00007, 0xeb04e2f5, 0xe3500000\n"
        ".word 0xe320f000, 0x1a0000a7, 0xea00008c, 0xe1a00009\n"
        ".word 0xeb04597b, 0xe1a08000, 0xe1a00009, 0xeb045972\n"
        ".word 0xe3550014, 0xe0800008, 0xe3a01000, 0x0a000004\n"
        ".word 0xe3550015, 0x0a000008, 0xe3550016, 0x0a00000c\n"
        ".word 0xea000010, 0xe0870080, 0xe1d610b6, 0xe1d000b0\n"
        ".word 0xe1510000, 0x1a000012, 0xea000018, 0xe0870080\n"
        ".word 0xe1d610b8, 0xe1d000b0, 0xe1510000, 0x1a00000e\n"
        ".word 0xea000012, 0xe0870080, 0xe1d620ba, 0xe1d000b0\n"
        ".word 0xe1520000, 0x1a00000a, 0xe3510000, 0x0a00000b\n"
        ".word 0xe3550014, 0x0a000002, 0xe3550015, 0x0a000002\n"
        ".word 0xea000003, 0xe3a00000, 0xea000000, 0xe3a00001\n"
        ".word 0xeb04421a, 0xe3a00000, 0xeb044316, 0xe5c4b032\n"
        ".word 0xe2840034, 0xeb0457a0, 0xe1a06000, 0xe3a07000\n"
        ".word 0xe2840034, 0xeb0457b0, 0xe3500000, 0xe320f000\n"
        ".word 0xda00002c, 0xe2566001, 0x5a000002, 0xe2840034\n"
        ".word 0xeb0457a9, 0xe2406001, 0xe0860186, 0xe0800206\n"
        ".word 0xe0848100, 0xe2880fa9, 0xeb0457a3, 0xe1a0a000\n"
        ".word 0xe3a00e41, 0xeb04df8c, 0xe3500000, 0xe320f000\n"
        ".word 0x1a000004, 0xe3560000, 0xda000002, 0xe2880fdb\n"
        ".word 0xeb045799, 0xe1a0a000, 0xe35a0000, 0xda00000f\n"
        ".word 0xe1a01006, 0xe2840034, 0xeb0441eb, 0xe2840034\n"
        ".word 0xe320f000, 0xeb04577c, 0xe1d429d8, 0xe1a01000\n"
        ".word 0xe1a00002, 0xeb0441bb, 0xe1a05000, 0xe320f000\n"
        ".word 0xeb044372, 0xe320f000, 0xe320f000, 0xea000005\n"
        ".word 0xe2877001, 0xe2840034, 0xeb045783, 0xe1500007\n"
        ".word 0xe320f000, 0xcaffffd2, 0xe3a01000, 0xe1a00009\n"
        ".word 0xeb044183, 0xe3a00002, 0xe3550011, 0xe584001c\n"
        ".word 0x0a00000c, 0xe3550012, 0x0a0000bb, 0xe3550013\n"
        ".word 0x0a0000bb, 0xe3550014, 0x0a00000e, 0xe3550015\n"
        ".word 0x0a0000c2, 0xe3550016, 0x0a0000c2, 0xe3550017\n"
        ".word 0x0a00000e, 0xea0000a5, 0xe3a00e41, 0xeb04df56\n"
        ".word 0xe3500000, 0xe320f000, 0x0a0000a9, 0xea0000a6\n"
        ".word 0xeb04bf45, 0xea00009d, 0xe3a00e41, 0xeb04df4e\n"
        ".word 0xe3500000, 0xe320f000, 0x0a0000ae, 0xea0000ab\n"
        ".word 0xe3a00014, 0xeb04bf3c, 0xe320f000, 0xe320f000\n"
        ".word 0xea000092, 0xeb04ccda, 0xe28dd01c, 0xe8bd8ff0\n"
        ".word 0xe1d800fa, 0xeb045295, 0xe3500006, 0xe320f000\n"
        ".word 0x0a000014, 0xe3a01001, 0xe3a00009, 0xeb04e25c\n"
        ".word 0xe3500000, 0xe320f000, 0x0afffe65, 0xe3550011\n"
        ".word 0x0a00009e, 0xe3550012, 0x0a0000ae, 0xe3550013\n"
        ".word 0x0a0000be, 0xe3550014, 0x03a01000, 0x03a00008\n"
        ".word 0x0a0000cc, 0xe3550016, 0x03a01000, 0x03a0000a\n"
        ".word 0x0a0000c8, 0xea0000d6, 0xe1a00009, 0xeb0458d4\n"
        ".word 0xe1a08000, 0xe1a00009, 0xeb0458cb, 0xe3550014\n"
        ".word 0xe0800008, 0xe3a01000, 0x0a000004, 0xe3550015\n"
        ".word 0x0a000008, 0xe3550016, 0x0a00000c, 0xea000010\n"
        ".word 0xe0870080, 0xe1d610b6, 0xe1d000b0, 0xe1510000\n"
        ".word 0x0a000019, 0xea000015, 0xe0870080, 0xe1d610b8\n"
        ".word 0xe1d000b0, 0xe1510000, 0x1a00000e, 0xea000012\n"
        ".word 0xe0870080, 0xe1d620ba, 0xe1d000b0, 0xe1520000\n"
        ".word 0x1a000006, 0xe3510000, 0x0a00000b, 0xe3550016\n"
        ".word 0x0a000002, 0xe3550015, 0x0a000002, 0xea000003\n"
        ".word 0xe3a00002, 0xea000000, 0xe3a00001, 0xeb044173\n"
        ".word 0xe3a00000, 0xeb04426f, 0xe5c4b032, 0xe2840034\n"
        ".word 0xeb0456f9, 0xe1a06000, 0xe3a07000, 0xe2840034\n"
        ".word 0xeb045709, 0xe3500000, 0xe320f000, 0xda00002c\n"
        ".word 0xe2866001, 0xe2840034, 0xeb045703, 0xe1500006\n"
        ".word 0xd3a06000, 0xe0860186, 0xe0800206, 0xe0848100\n"
        ".word 0xe2880fa9, 0xeb0456fc, 0xe1a0a000, 0xe3a00e41\n"
        ".word 0xeb04dee5, 0xe3500000, 0xe320f000, 0x1a000004\n"
        ".word 0xe3560000, 0xda000002, 0xe2880fdb, 0xeb0456f2\n"
        ".word 0xe1a0a000, 0xe35a0000, 0xda00000f, 0xe1a01006\n"
        ".word 0xe2840034, 0xeb044144, 0xe2840034, 0xe320f000\n"
        ".word 0xeb0456d5, 0xe1d429d8, 0xe1a01000, 0xe1a00002\n"
        ".word 0xeb044114, 0xe1a05000, 0xe320f000, 0xeb0442cb\n"
        ".word 0xe320f000, 0xe320f000, 0xea000005, 0xe2877001\n"
        ".word 0xe2840034, 0xeb0456dc, 0xe1500007, 0xe320f000\n"
        ".word 0xcaffffd2, 0xe3a01000, 0xe1a00009, 0xeb0440dc\n"
        ".word 0xe3a00002, 0xe3550011, 0xe584001c, 0x0a00000d\n"
        ".word 0xe3550012, 0x0a000014, 0xe3550013, 0x0a000014\n"
        ".word 0xe3550014, 0x0a000014, 0xe3550015, 0x0a00001b\n"
        ".word 0xe3550016, 0x0a00001b, 0xe3550017, 0x0affff67\n"
        ".word 0xe59f0310, 0xeaffff6a, 0xe3a00e41, 0xeb04deae\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000001, 0xe3a0000e\n"
        ".word 0xeaffff56, 0xe3a00015, 0xeaffff54, 0xe3a0000f\n"
        ".word 0xeaffff52, 0xe3a00010, 0xeaffff50, 0xe3a00e41\n"
        ".word 0xeb04dea1, 0xe3500000, 0xe320f000, 0x0a000001\n"
        ".word 0xe3a00011, 0xeaffff49, 0xe3a00016, 0xeaffff47\n"
        ".word 0xe3a00012, 0xeaffff45, 0xe3a00013, 0xeaffff43\n"
        ".word 0xe3a01000, 0xe3a00005, 0xeb045538, 0xe3a00006\n"
        ".word 0xe320f000, 0xeb045518, 0xe3a00011, 0xe320f000\n"
        ".word 0xeb045515, 0xe3a00012, 0xe320f000, 0xeb045512\n"
        ".word 0xe3a00003, 0xe320f000, 0xeb04550f, 0xe320f000\n"
        ".word 0xe320f000, 0xea00004f, 0xe3a01000, 0xe3a00006\n"
        ".word 0xeb045526, 0xe3a00006, 0xe320f000, 0xeb045506\n"
        ".word 0xe3a00011, 0xe320f000, 0xeb045503, 0xe3a00012\n"
        ".word 0xe320f000, 0xeb045500, 0xe3a00003, 0xe320f000\n"
        ".word 0xeb0454fd, 0xe320f000, 0xe320f000, 0xea00003d\n"
        ".word 0xe3a01000, 0xe3a00007, 0xeb045514, 0xe3a00006\n"
        ".word 0xe320f000, 0xeb0454f4, 0xe3a0001f, 0xe320f000\n"
        ".word 0xeb0454f1, 0xe3a00013, 0xe320f000, 0xeb0454ee\n"
        ".word 0xe3a00003, 0xe320f000, 0xeb0454eb, 0xe320f000\n"
        ".word 0xe320f000, 0xea00002b, 0xeb045504, 0xe3a00004\n"
        ".word 0xeb0454e5, 0xe3a00024, 0xeb0454e3, 0xe3a00025\n"
        ".word 0xeb0454e1, 0xe3a00026, 0xeb0454df, 0xe3a00027\n"
        ".word 0xeb0454dd, 0xe3a00028, 0xeb0454db, 0xe3a00003\n"
        ".word 0xeb0454d9, 0xe3550015, 0x0a000002, 0xe3550017\n"
        ".word 0x0a00000f, 0xea000017, 0xe3a01000, 0xe3a00009\n"
        ".word 0xeb0454ee, 0xe3a00004, 0xe320f000, 0xeb0454ce\n"
        ".word 0xe3a00032, 0xe320f000, 0xeb0454cb, 0xe3a00003\n"
        ".word 0xe320f000, 0xeb0454c8, 0xe320f000, 0xe320f000\n"
        ".word 0xea000008, 0xe3a01000, 0xe3a0000b, 0xeb0454df\n"
        ".word 0xe3a00033, 0xe320f000, 0xeb0454bf, 0xe3a00003\n"
        ".word 0xe320f000, 0xeb0454bc, 0xe59f111c, 0xe3a00000\n"
        ".word 0xe5c4b033, 0xeb045789, 0xe320f000, 0xe320f000\n"
        ".word 0xeb04be76, 0xe5c40031, 0xe51f09c0, 0xe3a01028\n"
        ".word 0xe5900000, 0xe2803018, 0xe5902018, 0xe5802024\n"
        ".word 0xe8830402, 0xe580a014, 0xe59f00cc, 0xeafffedc\n"
        ".word 0xe320f000, 0xeb0443cd, 0xe3500000, 0xe320f000\n"
        ".word 0x0afffd4b, 0xe3e00000, 0xeb044431, 0xe3a00000\n"
        ".word 0xe320f000, 0xeb044d08, 0xe320f000, 0xe320f000\n"
        ".word 0xeb044e69, 0xe3a00000, 0xe320f000, 0xeb044419\n"
        ".word 0xe3a00000, 0xe320f000, 0xeb04420c, 0xe2840b01\n"
        ".word 0xe3a02000, 0xe3a01003, 0xe2800fb5, 0xeb04d1d0\n"
        ".word 0xe3a00006, 0xe5840020, 0xe51f0a50, 0xe3a01005\n"
        ".word 0xe2844d97, 0xe5900000, 0xe2803018, 0xe5902018\n"
        ".word 0xe5802024, 0xe8830402, 0xe580a014, 0xe5940000\n"
        ".word 0xeb0479bb, 0xe3a01000, 0xe1a00009, 0xe584a000\n"
        ".word 0xeb044013, 0xe320f000, 0xe320f000, 0xeb044001\n"
        ".word 0xe3a01000, 0xe3a00001, 0xeb045543, 0xe28dd01c\n"
        ".word 0xe8bd4ff0, 0xea043fd5, 0x00000572, 0x0100016d\n"
        ".word 0x0100025f, 0x0100016e, 0x0100016f, 0x323232ff\n");
}

// ---------------------------------------------------------------------------
// engine_func_002e4b10 (0x002E4B10), 4,116 B
// ---------------------------------------------------------------------------
//
// Recovered role: advance the UI part instances owned by `owner`.  Every pair
// of a 0x28-byte instance and a 0x4C-byte descriptor is driven from one shared
// 0x120-byte source descriptor:
//   - the instance life selects the cubic Bezier span between the source
//     control points and the descriptor anchors (0x002E4D54..0x002E4DF4),
//   - the orientation quaternion at source+0x10 is copied to 0x004EA91C and
//     expanded to the scene matrix by 0x002A2F1C (0x002E4B44..0x002E4B70),
//   - a second matrix is built from the descriptor/curve tangent by
//     0x002486EC and used to rotate the curve point (0x002E4E0C..0x002E5048),
//   - the expired life (-1) runs the randomized spawn transform at
//     0x002E50E4..0x002E5A80 and optionally pushes a trail sample through
//     0x0024B804.
// The two stack slots [sp+0x1C]/[sp+0x20] are read at 0x002E4E18 and
// 0x002E5748 but never written anywhere in the function; they are modelled as
// zero here.

namespace {

/** View of the 0x004EA81C block including the +0x120 scratch quad that
 *  `ui_runtime.h` leaves as padding. */
struct UiPartRenderStateView {
    u8  pad_000[0x100];
    f32 vector[4];                      // +0x100 (also 0x004EA91C)
    f32 color[4];                       // +0x110 (also 0x004EA92C)
    f32 scratch[4];                     // +0x120: `vstmia r1,{s17,s18,s19}`
                                        //   + `vstr s4,[g+0x12c]` (0x002E5198)
    u8  pad_130[0x10];                  // +0x130..+0x140
    f32 matrix[16];                     // +0x140: `add r1,r0,#0x140`
};
static_assert(offsetof(UiPartRenderStateView, vector) == 0x100);
static_assert(offsetof(UiPartRenderStateView, color) == 0x110);
static_assert(offsetof(UiPartRenderStateView, scratch) == 0x120);
static_assert(offsetof(UiPartRenderStateView, matrix) == 0x140);

inline UiPartRenderStateView& RenderState() {
    return *reinterpret_cast<UiPartRenderStateView*>(&ui::g_UiPartRenderState);
}

// Cubic Bezier evaluation used at 0x002E4DE0..0x002E4DF4.
inline void Bezier3(const f32 p0[3], const f32 p1[3], const f32 p2[3],
                    const f32 p3[3], f32 t, f32 out[3]) {
    const f32 u = 1.0f - t;
    const f32 b0 = u * u * u;
    const f32 b1 = 3.0f * (u * u) * t;
    const f32 b2 = 3.0f * u * (t * t);
    const f32 b3 = t * t * t;
    for (s32 i = 0; i < 3; ++i) {
        out[i] = p0[i] * b0 + p1[i] * b1 + p2[i] * b2 + p3[i] * b3;
    }
}

// Normalization blocks at 0x002E4E94..0x002E4EC0, 0x002E5348..0x002E5390 and
// 0x002E45F4..0x002E4520.
inline void Normalize3(f32 v[3]) {
    const f32 length = std::sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
    if (length > 0.0f) {
        v[0] /= length;
        v[1] /= length;
        v[2] /= length;
    }
}

// 4x4 transform at 0x002E4FE0..0x002E5018 (column-major layout).
inline void Transform4(const f32 m[16], const f32 in[4], f32 out[4]) {
    f32 r[4];
    for (s32 i = 0; i < 4; ++i) {
        r[i] = in[0] * m[i] + in[1] * m[4 + i] +
               in[2] * m[8 + i] + in[3] * m[12 + i];
    }
    for (s32 i = 0; i < 4; ++i) {
        out[i] = r[i];
    }
}

} // namespace

// DECOMP_FUNC(0x002e4b10, 4116)
#if 0
void engine_func_002e4b10(UiPartUpdateOwner* owner) {
    UiPartSource* const source = owner->source;
    UiPartInstance* instance = owner->instances;
    UiPartDescriptor* part = owner->parts;
    const s32 count = owner->count;             // 0x002E4B2C

    if (source->field_b8 == 0) {                // 0x002E4B30..0x002E4B38
        return;
    }

    // 0x002E4B3C..0x002E4B70: copy the source quaternion to 0x004EA91C and
    // build the scene matrix.  r0 of 0x002A2F1C is dead (the callee reloads
    // 0x004EA81C), exactly as at 0x002E4B70.
    f32 orientation[4] = {
        source->orientation[0], source->orientation[1],
        source->orientation[2], source->orientation[3],
    };
    std::memcpy(RenderState().vector, orientation, sizeof(orientation));
    UiPart_GetSceneMatrix(RenderState().vector);

    const f32 curve_a = source->field_ec;       // s28
    const f32 curve_b = source->field_f8;       // s27
    const f32 p0[3] = {
        source->bezier[0], source->bezier[1], source->bezier[2],
    };

    // 0x002E4B74..0x002E4C74: frame/time accumulator.  [sp+0x6C] is the
    // "interpolating" flag.
    s32 frame = 0;
    bool interpolate = false;
    if (source->field_20 == 0 ||
        static_cast<s32>(source->field_20) > owner->limit) {
        if (owner->limit == 0 && source->field_bd != 0) {
            interpolate = true;
            if (source->field_28 <= 0.0f) {
                frame = count;                  // `ldrle fp,[sb,#4]`
            } else {
                const f32 random = engine_func_0024ba44(0);
                frame = static_cast<s32>(
                    random * (1.1f - source->field_28) *
                    static_cast<f32>(count));
            }
        } else {
            if (source->field_28 <= 0.0f) {
                owner->time += static_cast<f32>(source->field_24);
            } else {
                const f32 random = engine_func_0024ba44(0);
                owner->time += static_cast<f32>(source->field_24) *
                               (random * (1.1f - source->field_28));
            }
            frame = static_cast<s32>(std::fabs(owner->time));
            owner->time -= static_cast<f32>(frame);
        }
    } else {
        frame = 0;
        interpolate = false;
    }

    for (s32 index = 0; index < count; ++index, ++instance, ++part) {
        // 0x002E4C88..0x002E4CB4: expire the instance when its life reaches
        // the source threshold.
        if (instance->life >= source->field_b8) {
            instance->life = (source->field_20 != 0) ? -1 : 0;
            func_0024b9d0(owner);
        }

        const s32 life = instance->life;        // r8
        if (life == -2) {                       // 0x002E4CBC
            continue;
        }

        // [sp+0x88] keeps the entering instance vector for the tail call.
        f32 saved[4] = {
            instance->vector[0], instance->vector[1],
            instance->vector[2], instance->vector[3],
        };

        if (life == -1) {                       // 0x002E50E4 spawn path
            if (frame == 0) {                   // 0x002E50E8
                continue;
            }

            // 0x002E50F0..0x002E5148: random phase and the three descriptor
            // offsets.
            const f32 random = engine_func_0024ba44(0);
            const f32 angle =
                (random - 0.5f) * 2.0f * 3.14159265f * 40.743665f;
            part->offset[0] = ui_func_002b73a4(angle) * source->field_11c;
            part->offset[1] = -source->field_120;
            part->offset[2] = ui_func_002b740c(angle) * source->field_11c;

            const f32 p3[3] = {
                source->field_108 + part->offset[0],   // 0x002E516C
                source->field_10c + part->offset[1],   // 0x002E517C
                source->field_110 + part->offset[2],   // 0x002E518C
            };

            // 0x002E516C..0x002E5210: the listing seeds +0x100 with the
            // source triple, +0x110 with the endpoint and +0x120 with the
            // same source triple (w from the uninitialized [sp+0x1C]).
            UiPartRenderStateView& rs = RenderState();
            const f32 stack_1c = 0.0f;
            const f32 stack_20 = 0.0f;
            for (s32 i = 0; i < 3; ++i) {
                rs.vector[i] = p0[i];
                rs.scratch[i] = p0[i];
                rs.color[i] = p3[i];
            }
            rs.vector[3] = stack_1c;
            rs.scratch[3] = stack_1c;
            rs.color[3] = stack_20;

            // 0x002E51B8..0x002E5224: first interpolation, weight
            // `source+0xC8 * 0.01` (0x3C23D70A at 0x002E5158/0x002E51D4).
            {
                const f32 w = static_cast<f32>(source->field_c8) * 0.01f;
                const f32 inv = 1.0f - w;
                for (s32 i = 0; i < 4; ++i) {
                    rs.vector[i] = rs.vector[i] * inv + rs.color[i] * w;
                }
            }

            // 0x002E5228..0x002E524C: the first-interpolated quad is saved
            // (sp+0x98 / s21 / s25 / s20) before the scratch restore and the
            // second interpolation.
            f32 saved_quad[4] = {
                rs.vector[0], rs.vector[1], rs.vector[2], rs.vector[3],
            };
            for (s32 i = 0; i < 4; ++i) {
                rs.vector[i] = rs.scratch[i];
            }

            // 0x002E5254..0x002E52BC: second interpolation, weight
            // `source+0xD4 * 0.01` (same 0x3C23D70A constant, 0x002E5264).
            {
                const f32 w = static_cast<f32>(source->field_d4) * 0.01f;
                const f32 inv = 1.0f - w;
                for (s32 i = 0; i < 4; ++i) {
                    rs.vector[i] = rs.vector[i] * inv + rs.color[i] * w;
                }
            }

            // 0x002E52C0..0x002E5348: the second-interpolated quad is held in
            // sp+0x30/s31/sp+0x60/s29; the working vector then becomes the
            // scratch quad (p0) and subtracts the color quad (p3), including
            // the W component.
            f32 second_quad[4] = {
                rs.vector[0], rs.vector[1], rs.vector[2], rs.vector[3],
            };
            for (s32 i = 0; i < 4; ++i) {
                rs.vector[i] = rs.scratch[i];
            }
            f32 delta[4] = {
                rs.vector[0] - rs.color[0],
                rs.vector[1] - rs.color[1],
                rs.vector[2] - rs.color[2],
                rs.vector[3] - rs.color[3],
            };
            // 0x002E5348..0x002E534C: descriptor scale is the norm of the
            // delta before it is normalized into the working vector.
            part->scale = std::sqrt(delta[0] * delta[0] +
                                    delta[1] * delta[1] +
                                    delta[2] * delta[2]);
            Normalize3(delta);                  // 0x002E5350..0x002E5390
            for (s32 i = 0; i < 3; ++i) {
                rs.vector[i] = delta[i];
            }

            // 0x002E5394..0x002E5448: orthonormal basis built from the
            // interpolated quad and the first trail scratch block.
            f32 basis[3] = {
                saved_quad[1] * rs.vector[2] - saved_quad[2] * rs.vector[1],
                saved_quad[2] * rs.vector[0] - saved_quad[0] * rs.vector[2],
                saved_quad[0] * rs.vector[1] - saved_quad[1] * rs.vector[0],
            };
            Normalize3(basis);
            for (s32 i = 0; i < 3; ++i) {
                rs.vector[i] = basis[i];
                rs.color[i] = g_TrailScratchA[i];
            }
            rs.color[3] = g_TrailScratchA[3];

            // 0x002E5458..0x002E5494: random spawn rotation and quaternion
            // matrix.  s0 = (rand-0.5)*2*field_e0*0.5*(pi/180).
            const f32 spin = (engine_func_0024ba44(0) - 0.5f) * 2.0f *
                             static_cast<f32>(source->field_e0) *
                             0.5f * 0.017453292f;
            // 0x002E548C: axis sp+0x50 holds the normalized delta quad and
            // the angle arrives in s0.
            func_002486ec(delta, spin);

            // 0x002E5498..0x002E54D0: radial scale from source+0xCC/+0xD0.
            const f32 random2 = engine_func_0024ba44(0);
            const f32 radial =
                ((1.0f - source->field_d0) +
                 random2 * source->field_d0) * source->field_cc;
            (void)spin;

            // 0x002E54D4..0x002E55D4: restore the saved quad and apply the
            // spawn rotation to +0x110.
            for (s32 i = 0; i < 4; ++i) {
                rs.vector[i] = saved_quad[i];
                rs.color[i] = g_TrailScratchA[i];
            }
            for (s32 i = 0; i < 3; ++i) {
                rs.color[i] *= radial;
            }

            // 0x002E55E0..0x002E5708: the second interpolated quad parked at
            // sp+0x30/s31/sp+0x60/s29 (0x002E52C0..0x002E52E4) is the base
            // for the life curve, not the saved first-interpolated quad.
            const f32 random3 = engine_func_0024ba44(0);
            const f32 life_scale =
                ((1.0f - source->field_dc) +
                 random3 * source->field_dc) * source->field_d8;
            for (s32 i = 0; i < 4; ++i) {
                rs.vector[i] = second_quad[i];
            }
            for (s32 i = 0; i < 4; ++i) {
                rs.vector[i] *= life_scale;
            }

            // 0x002E571C..0x002E5738: descriptor speed from +0xF0/+0xF4.
            const f32 random4 = engine_func_0024ba44(0);
            part->speed_b =
                ((1.0f - source->field_f4) +
                 random4 * source->field_f4) * source->field_f0;

            // 0x002E573C..0x002E575C: descriptor speed from +0xE4/+0xE8.
            const f32 random5 = engine_func_0024ba44(0);
            part->speed_a =
                ((1.0f - source->field_e8) +
                 random5 * source->field_e8) * source->field_e4;

            // 0x002E5770..0x002E5788: descriptor angle from source+0x6C.
            const f32 random6 = engine_func_0024ba44(0);
            part->angle =
                (1.0f - source->field_6c) + random6 * source->field_6c;

            // 0x002E579C..0x002E57F0: the two descriptor angles.  Mode 2
            // uses a random angle, mode 1 the source+0x98 angle, mode 0
            // zero; the odd tick at 0x002E57D8 negates +0x48.
            if (source->field_9c == 2) {
                part->angle_offset = 0.0f;      // 0x002E578C
                part->angle_scale = 0.0f;       // 0x002E5790
            } else {
                const f32 random7 = engine_func_0024ba44(0);
                part->angle_scale =
                    (1.0f - source->field_98) + random7 * source->field_98;
                if (source->field_9c == 1) {
                    const f32 random8 = engine_func_0024ba44(0);
                    part->angle_offset = random8 * 6.2831855f;
                    if ((engine_func_0024b990(0) & 1) != 0) {
                        part->angle_scale = -part->angle_scale;
                    }
                } else {
                    part->angle_offset = 0.0f;
                }
            }

            // 0x002E5760..0x002E5768: clear the progress, seed the instance
            // vector from the source control point, then let 0x002E57F4 copy
            // that vector into the shared [sp+0x88] buffer.
            part->progress = 0.0f;
            instance->vector[0] = p0[0];
            instance->vector[1] = p0[1];
            instance->vector[2] = p0[2];
            instance->vector[3] = stack_1c;

            // 0x002E57F4..0x002E5810: the spawn instance starts at life 0.
            instance->life = 0;
            std::memcpy(saved, instance->vector, sizeof(saved));

            if (interpolate) {
                // 0x002E5814..0x002E5A80: clamp the frame count, then use
                // the 0x002C6C10 interpolator for the two scale fields.
                engine_func_0024b990(0);
                const s32 clamped =
                    ui_func_002c6c10(frame, source->field_b8);
                const f32 tf = static_cast<f32>(static_cast<u32>(clamped));
                // 0x002E583C..0x002E5848: the position curve uses s27
                // (source+0xF8, `curve_b`), not curve_a.
                const f32 a =
                    (part->speed_b * tf + 0.5f * curve_b * tf * tf) *
                    0.001f;
                const f32 t = std::fmin(std::fmax(a, part->progress), 1.0f);
                part->progress = t;

                // 0x002E5854..0x002E5880: the rotation angle is the second
                // curve, speed_a*tf + 0.5*curve_a*tf^2, clamped at zero.
                const f32 angle_raw =
                    part->speed_a * tf + 0.5f * curve_a * tf * tf;
                const f32 spawn_angle =
                    angle_raw < 0.0f ? 0.0f : angle_raw;

                // 0x002E5950..0x002E59F0: rebuild the orientation matrix
                // from +0x100, then apply it to +0x110.
                // 0x002E5950: axis sp+0x50, angle s0 = `spawn_angle`.
                func_002486ec(rs.vector, spawn_angle);
                for (s32 i = 0; i < 4; ++i) {
                    rs.color[i] = rs.vector[i];
                }
                f32 point[3] = {
                    p0[0] + (p3[0] - p0[0]) * t,
                    p0[1] + (p3[1] - p0[1]) * t,
                    p0[2] + (p3[2] - p0[2]) * t,
                };
                for (s32 i = 0; i < 3; ++i) {
                    rs.vector[i] = point[i];
                }
                // 0x002E58EC / 0x002E59A4 store s21, the Y component saved
                // from the first-interpolated quad at 0x002E523C.
                rs.vector[3] = saved_quad[1];
                for (s32 i = 0; i < 4; ++i) {
                    rs.vector[i] -= rs.color[i];
                }
                Transform4(rs.matrix, rs.vector, rs.vector);
                for (s32 i = 0; i < 4; ++i) {
                    rs.vector[i] += rs.color[i];
                }

                // 0x002E5A84..0x002E5A9C: commit the spawn position and the
                // integer life.
                f32 commit[4] = {
                    rs.vector[0], rs.vector[1], rs.vector[2], rs.vector[3],
                };
                instance->vector[0] = commit[0];
                instance->vector[1] = commit[1];
                instance->vector[2] = commit[2];
                instance->vector[3] = commit[3];
                instance->life = static_cast<s32>(tf);
            }

            // 0x002E5AA0..0x002E5B14: shared spawn tail.
            ui_func_0024b874(instance, source, instance->life, saved);
            instance->scale_x *= part->angle;
            instance->scale_y *= part->angle_scale;
            instance->scale_y += part->angle_offset;
            if (interpolate) {
                func_0024b804(owner, instance);
                instance->life =
                    static_cast<s32>(ui_func_00269cb8()) + instance->life;
            }
            continue;
        }

        // ------------------------------------------------------------------
        // 0x002E4CCC..0x002E50C4: live instance.
        // ------------------------------------------------------------------
        const f32 life_f = static_cast<f32>(life);
        f32 a = part->speed_b * life_f +
                0.5f * curve_b * life_f * life_f;
        if (a < 0.0f) {
            a = 0.0f;
        }
        f32 b = part->speed_a * life_f +
                0.5f * curve_a * life_f * life_f;
        if (b < 0.0f) {
            b = 0.0f;
        }

        // 0x002E4D2C..0x002E4D54: 0.001 scale, clamp, and monotonic
        // progress.
        f32 t = a * 0.001f;
        if (t > 1.0f) {
            t = 1.0f;
        }
        if (part->progress <= t) {
            part->progress = t;
        } else {
            t = part->progress;
        }

        // 0x002E4D54..0x002E4DF4: cubic Bezier.
        const f32 p3[3] = {
            source->field_108 + part->offset[0],
            source->field_10c + part->offset[1],
            source->field_110 + part->offset[2],
        };
        const f32 p1[3] = {
            part->anchor[0], part->anchor[1], part->anchor[2],
        };
        const f32 p2[3] = {
            part->anchor[3], part->anchor[4], part->anchor[5],
        };
        f32 point[3];
        Bezier3(p0, p1, p2, p3, t, point);

        // 0x002E4DF8..0x002E4E08: publish the curve point first; the
        // orientation block is skipped when the distance is zero.
        UiPartRenderStateView& rs = RenderState();
        rs.vector[0] = point[0];
        rs.vector[1] = point[1];
        rs.vector[2] = point[2];
        rs.vector[3] = 1.1f;

        if (b != 0.0f) {
            // 0x002E4E0C..0x002E4EC0: the listing copies the source triple
            // to +0x100 and +0x110 and therefore normalizes a zero delta.
            const f32 stack_1c = 0.0f;
            f32 quat[4] = {p0[0], p0[1], p0[2], stack_1c};
            for (s32 i = 0; i < 3; ++i) {
                rs.color[i] = p0[i];
            }
            rs.color[3] = 0.0f;
            f32 delta[3] = {
                quat[0] - rs.color[0],
                quat[1] - rs.color[1],
                quat[2] - rs.color[2],
            };
            Normalize3(delta);                  // no-op in the listing
            // 0x002E4EE4: axis sp+0x50, angle s0 = the second curve value.
            func_002486ec(quat, b);

            // 0x002E4EE8..0x002E4F2C: +0x110 receives the quaternion and is
            // scaled by `part->scale * t`.
            for (s32 i = 0; i < 4; ++i) {
                rs.color[i] = quat[i];
            }
            const f32 scale = part->scale * t;
            for (s32 i = 0; i < 4; ++i) {
                rs.color[i] *= scale;
            }

            // 0x002E4F30..0x002E5048: point - scaled quaternion, matrix
            // transform, then translation.
            rs.vector[0] = point[0];
            rs.vector[1] = point[1];
            rs.vector[2] = point[2];
            rs.vector[3] = 1.1f;
            for (s32 i = 0; i < 4; ++i) {
                rs.vector[i] -= rs.color[i];
            }
            Transform4(rs.matrix, rs.vector, rs.vector);
            for (s32 i = 0; i < 4; ++i) {
                rs.vector[i] += rs.color[i];
            }
        }

        // 0x002E504C..0x002E5064: commit to the instance.
        instance->vector[0] = rs.vector[0];
        instance->vector[1] = rs.vector[1];
        instance->vector[2] = rs.vector[2];
        instance->vector[3] = rs.vector[3];

        // 0x002E5068..0x002E50A8: shared live tail.
        ui_func_0024b874(instance, source, life, saved);
        instance->scale_x *= part->angle;
        instance->scale_y *= part->angle_scale;
        instance->scale_y += part->angle_offset;

        // 0x002E50AC..0x002E50C0
        func_0024afec(owner, instance);
        instance->life =
            static_cast<s32>(ui_func_00269cb8()) + life;
    }
}
#endif

// Readable UI part-update loop draft above; exact ARM body retained pending codegen recovery.
__attribute__((naked)) void engine_func_002e4b10(UiPartUpdateOwner* owner) {
    asm volatile(
        ".word 0xe92d4ff0, 0xe280401c, 0xe1a09000, 0xed2d8b10\n"
        ".word 0xe24dd0b4, 0xe8940050, 0xe5905018, 0xe590a004\n"
        ".word 0xe59610b8, 0xe3510000, 0x0a000166, 0xe2863010\n"
        ".word 0xe5d6009c, 0xe8931888, 0xe28620fc, 0xe58d00a4\n"
        ".word 0xe59f03fc, 0xed96ea3b, 0xedd6da3e, 0xecd28a03\n"
        ".word 0xe5962020, 0xe58d107c, 0xe58d20a0, 0xe8801888\n"
        ".word 0xebfef8e9, 0xe59d20a0, 0xed9f8af6, 0xe3520000\n"
        ".word 0x0a000006, 0xe5990010, 0xe1520000, 0xca000003\n"
        ".word 0xe3a00000, 0xe1a0b000, 0xe58d006c, 0xea000035\n"
        ".word 0xe5990010, 0xed9faaec, 0xe3500000, 0x1a000014\n"
        ".word 0xe5d600bd, 0xe3500000, 0x0a000011, 0xed960a0a\n"
        ".word 0xe3a00001, 0xe58d006c, 0xeeb40ac8, 0xeef1fa10\n"
        ".word 0xd599b004, 0xda000027, 0xe3a00000, 0xebfd9b98\n"
        ".word 0xed961a0a, 0xedd90a01, 0xee3a1a41, 0xeef80a60\n"
        ".word 0xee200a01, 0xee200a20, 0xeebd0ac0, 0xee10ba10\n"
        ".word 0xea00001c, 0xed960a0a, 0xe3a00000, 0xe58d006c\n"
        ".word 0xeeb40ac8, 0xeef1fa10, 0xda00000a, 0xebfd9b88\n"
        ".word 0xedd61a0a, 0xedd60a09, 0xed991a05, 0xee7a1a61\n"
        ".word 0xeef80a60, 0xee200a21, 0xee001a80, 0xed891a05\n"
        ".word 0xeeb00a41, 0xea000004, 0xed960a09, 0xedd90a05\n"
        ".word 0xeeb80a40, 0xee300a80, 0xed890a05, 0xeef00ac0\n"
        ".word 0xeefd0ae0, 0xee10ba90, 0xee00ba90, 0xeef80ae0\n"
        ".word 0xee300a60, 0xed890a05, 0xe35a0000, 0x8d9ffab7\n"
        ".word 0xe3a07000, 0x9a000113, 0xe5950010, 0xe59d107c\n"
        ".word 0xe1500001, 0xba000007, 0xe59d00a0, 0xe1a01005\n"
        ".word 0xe3500000, 0x13e00001, 0x03e00000, 0xe5850010\n"
        ".word 0xe1a00009, 0xebfd9b45, 0xe5958010, 0xe3780002\n"
        ".word 0x0a0000ff, 0xe3780001, 0x0a000105, 0xee008a10\n"
        ".word 0xe895000f, 0xe28dc088, 0xed9f1aa1, 0xed9fda9d\n"
        ".word 0xe88c000f, 0xeeb80ac0, 0xedd40a0d, 0xee6d1a80\n"
        ".word 0xee600a80, 0xee611a80, 0xee410a81, 0xeeb4dae0\n"
        ".word 0xeef1fa10, 0xee2e2a00, 0xedd41a0c, 0xcef00a4d\n"
        ".word 0xee222a00, 0xee210a80, 0xee020a01, 0xeeb40acd\n"
        ".word 0xeef1fa10, 0xed9f1a8f, 0x3eb00a4d, 0xee208a81\n"
        ".word 0xedd40a0f, 0xee180a10, 0xe35005fe, 0xceb08a4f\n"
        ".word 0xe59f020c, 0xeef40ac8, 0xeef1fa10, 0xdd848a0f\n"
        ".word 0xceb08a60, 0xed961a42, 0xedd40a09, 0xed962a44\n"
        ".word 0xedd41a0b, 0xee717a20, 0xeef00a4f, 0xee72ca21\n"
        ".word 0xedd62a43, 0xed943a0a, 0xeddf1a7b, 0xedd64a40\n"
        ".word 0xee700ac8, 0xee32ca83, 0xee682a08, 0xed963a3f\n"
        ".word 0xed966a41, 0xedd43a00, 0xed945a01, 0xedd46a02\n"
        ".word 0xed944a03, 0xedd45a04, 0xee202aa0, 0xed947a05\n"
        ".word 0xee221a20, 0xee222a08, 0xee620aa0, 0xee622a88\n"
        ".word 0xee63aa01, 0xee222a21, 0xee24ba81, 0xee66ba01\n"
        ".word 0xee600aa1, 0xee43aa82, 0xee05ba02, 0xee46ba82\n"
        ".word 0xee44aa20, 0xee05baa0, 0xee47ba20, 0xee47aaa2\n"
        ".word 0xee0cba22, 0xee4cbaa2, 0xeeb40a4d, 0xed80aa03\n"
        ".word 0xeef1fa10, 0xecc0aa03, 0x0a00008f, 0xe2402c01\n"
        ".word 0xe28d001c, 0xe28630fc, 0xec902a02, 0xe2821c01\n"
        ".word 0xe2820e11, 0xecd30a03, 0xed822a43, 0xecc18a03\n"
        ".word 0xedc22a47, 0xecc00a03, 0xe2820c01, 0xed921a44\n"
        ".word 0xedd20a40, 0xee700ac1, 0xedc20a40, 0xedd20a41\n"
        ".word 0xed921a45, 0xee700ac1, 0xedc20a41, 0xedd20a42\n"
        ".word 0xed921a46, 0xee700ac1, 0xedc20a42, 0xed921a47\n"
        ".word 0xedd20a43, 0xee700ac1, 0xedc20a43, 0xedd21a40\n"
        ".word 0xedd20a41, 0xed922a42, 0xee211aa1, 0xee001aa0\n"
        ".word 0xee021a02, 0xeef10ac1, 0xeef40acd, 0xeef1fa10\n"
        ".word 0xda000007, 0xeef02a42, 0xee812aa0, 0xed901a01\n"
        ".word 0xed802a00, 0xeec11a20, 0xedc01a01, 0xee821aa0\n"
        ".word 0xed801a02, 0xe59f00a4, 0xe28dc050, 0xe2801c01\n"
        ".word 0xe590010c, 0xe891000e, 0xe58d005c, 0xe28d0050\n"
        ".word 0xe88c000e, 0xebfd8e00, 0xe28de050, 0xe59f0080\n"
        ".word 0xe89e100e, 0xe880100e, 0xed940a0e, 0xedd00a00\n"
        ".word 0xee200a08, 0xee600a80, 0xedc00a00, 0xedd00a01\n"
        ".word 0xee600a80, 0xedc00a01, 0xedd00a02, 0xee600a80\n"
        ".word 0xedc00a02, 0xedd00a03, 0xee200a80, 0xed800a03\n"
        ".word 0xe2400010, 0xe2801010, 0xed80aa03, 0xecc0aa03\n"
        ".word 0xedd10a00, 0xed900a00, 0xee300a60, 0xed800a00\n"
        ".word 0xea000008, 0x004ea91c, 0x00000000, 0x3f8ccccd\n"
        ".word 0x3f800000, 0x3f000000, 0x3a83126f, 0x40400000\n"
        ".word 0x004ea81c, 0x004ea92c, 0xed900a01, 0xedd10a01\n"
        ".word 0xee300a60, 0xed800a01, 0xed900a02, 0xedd10a02\n"
        ".word 0xee300a60, 0xed800a02, 0xedd10a03, 0xed900a03\n"
        ".word 0xe2801000, 0xee300a60, 0xed800a03, 0xe2810040\n"
        ".word 0xedd11a00, 0xed907a03, 0xed912a01, 0xed906a07\n"
        ".word 0xed903a04, 0xed904a05, 0xed905a06, 0xedd12a02\n"
        ".word 0xedd06a0b, 0xedd03a08, 0xedd04a09, 0xedd05a0a\n"
        ".word 0xec900a03, 0xe2810010, 0xee210a80, 0xee610aa0\n"
        ".word 0xee211a81, 0xee611a87, 0xee020a03, 0xee420a04\n"
        ".word 0xee021a05, 0xee421a06, 0xee020aa3, 0xee420aa4\n"
        ".word 0xee021aa5, 0xee421aa6, 0xec810a04, 0xed902a00\n"
        ".word 0xee300a02, 0xed810a00, 0xed900a01, 0xee300a80\n"
        ".word 0xed810a01, 0xed900a02, 0xee310a00, 0xed810a02\n"
        ".word 0xed900a03, 0xee310a80, 0xed810a03, 0xe51f00e4\n"
        ".word 0xe2801c01, 0xe590010c, 0xe891000e, 0xe585000c\n"
        ".word 0xe1a00005, 0xe885000e, 0xe28d3088, 0xe1a02008\n"
        ".word 0xe1a01006, 0xebfd99fe, 0xed950a06, 0xedd40a10\n"
        ".word 0xe1a01005, 0xe1a00009, 0xee200a20, 0xed850a06\n"
        ".word 0xed950a07, 0xedd40a12, 0xee200a20, 0xed850a07\n"
        ".word 0xedd40a11, 0xee300a20, 0xed850a07, 0xebfd97ce\n"
        ".word 0xe320f000, 0xe320f000, 0xebfe12fe, 0xe0800008\n"
        ".word 0xe5850010, 0xe2877001, 0xe157000a, 0xe284404c\n"
        ".word 0xe2855028, 0x3afffeeb, 0xe28dd0b4, 0xecbd8b10\n"
        ".word 0xe8bd8ff0, 0xe35b0000, 0x0afffff5, 0xe3a00000\n"
        ".word 0xebfd9a53, 0xed1f1a66, 0xeddf1aee, 0xeddf0aec\n"
        ".word 0xee300a41, 0xee200a21, 0xee200a20, 0xeddf0aea\n"
        ".word 0xee208a20, 0xeeb00a48, 0xebff48a1, 0xedd60a47\n"
        ".word 0xee200a20, 0xed840a09, 0xed960a48, 0xeeb10a40\n"
        ".word 0xed840a0a, 0xeeb00a48, 0xebff48b3, 0xedd60a47\n"
        ".word 0xe28d101c, 0xe51f01dc, 0xee200a20, 0xec912a02\n"
        ".word 0xe2801e12, 0xe2802c01, 0xed9f1ad8, 0xeeb0da4f\n"
        ".word 0xe2808f49, 0xe2803e12, 0xed840a0b, 0xedd60a42\n"
        ".word 0xedd41a09, 0xee700aa1, 0xedcd0a27, 0xedd61a43\n"
        ".word 0xed943a0a, 0xee711a83, 0xedcd1a0d, 0xed963a44\n"
        ".word 0xed802a4b, 0xee330a00, 0xecc18a03, 0xed802a43\n"
        ".word 0xecc28a03, 0xedc00a44, 0xedc01a45, 0xed800a46\n"
        ".word 0xedc02a47, 0xed8d0a2a, 0xe1d61cf8, 0xed902a44\n"
        ".word 0xee001a10, 0xe1a01002, 0xe2802e11, 0xedd11a00\n"
        ".word 0xeeb80ac0, 0xee200a01, 0xee7d0a40, 0xee611aa0\n"
        ".word 0xee421a00, 0xedc11a00, 0xedd11a01, 0xed902a45\n"
        ".word 0xee611aa0, 0xee421a00, 0xedc11a01, 0xedd11a02\n"
        ".word 0xed902a46, 0xee611aa0, 0xee421a00, 0xedc11a02\n"
        ".word 0xed912a03, 0xedd21a03, 0xe1a02001, 0xee620a20\n"
        ".word 0xee410a80, 0xedc10a03, 0xed910a00, 0xedd00a48\n"
        ".word 0xecd81a03, 0xe2818004, 0xed8d0a26, 0xedd1aa01\n"
        ".word 0xedd1ca02, 0xed91aa03, 0xedc10a00, 0xecc81a02\n"
        ".word 0xedc12a03, 0xe1d61df4, 0xee001a10, 0xe1a01002\n"
        ".word 0xeeb80ac0, 0xee200a01, 0xed911a00, 0xedd01a44\n"
        ".word 0xe2802e11, 0xee7d0a40, 0xee211a20, 0xee011a80\n"
        ".word 0xed811a00, 0xed911a01, 0xedd01a45, 0xee211a20\n"
        ".word 0xee011a80, 0xed811a01, 0xed911a02, 0xedd01a46\n"
        ".word 0xee211a20, 0xee011a80, 0xed811a02, 0xed911a03\n"
        ".word 0xedd21a03, 0xee610a20, 0xee410a80, 0xedc10a03\n"
        ".word 0xed910a00, 0xecd30a04, 0xed8d0a0c, 0xed910a01\n"
        ".word 0xeef0fa40, 0xed910a02, 0xed8d0a18, 0xed910a03\n"
        ".word 0xecc10a03, 0xeef0ea40, 0xed812a03, 0xedd00a44\n"
        ".word 0xed910a00, 0xed9f2a72, 0xee300a60, 0xed810a00\n"
        ".word 0xed910a01, 0xedd00a45, 0xee300a60, 0xed810a01\n"
        ".word 0xed910a02, 0xedd00a46, 0xee300a60, 0xed810a02\n"
        ".word 0xed900a47, 0xedd10a03, 0xe2810004, 0xee300ac0\n"
        ".word 0xed810a03, 0xed910a00, 0xecd00a02, 0xee200a00\n"
        ".word 0xee000aa0, 0xee010a01, 0xeef10ac0, 0xedc40a0e\n"
        ".word 0xed910a02, 0xec911a02, 0xee610a01, 0xee410aa1\n"
        ".word 0xee400a00, 0xeeb10ae0, 0xeeb40ac2, 0xeef1fa10\n"
        ".word 0xda000007, 0xeef00a61, 0xeec11a00, 0xed912a02\n"
        ".word 0xedc11a00, 0xee801a80, 0xed811a01, 0xeec20a00\n"
        ".word 0xedc10a02, 0xe51f842c, 0xe28d1050, 0xe2880c01\n"
        ".word 0xec900a04, 0xe2880e12, 0xec810a04, 0xe59f1114\n"
        ".word 0xec800a04, 0xe2880e11, 0xe891100c, 0xe591100c\n"
        ".word 0xe588111c, 0xe880100c, 0xe2880e12, 0xedd81a41\n"
        ".word 0xed981a46, 0xed980a42, 0xed982a45, 0xee610a81\n"
        ".word 0xedd82a44, 0xed983a40, 0xee400a42, 0xee200a22\n"
        ".word 0xedc80a40, 0xee030a41, 0xee231a02, 0xed880a41\n"
        ".word 0xee011ae2, 0xed881a42, 0xe890100e, 0xe2880e11\n"
        ".word 0xe880100e, 0xe1a01000, 0xe2880f41, 0xedd11a02\n"
        ".word 0xedd12a01, 0xed913a00, 0xee202a21, 0xee012a62\n"
        ".word 0xee211a03, 0xed882a40, 0xee202aa2, 0xee001ae1\n"
        ".word 0xee002a43, 0xed881a41, 0xed882a42, 0xed988a40\n"
        ".word 0xec90ba03, 0xe3a00000, 0xebfd9979, 0xeddf0a1a\n"
        ".word 0xeddf1a14, 0xe1d60ef0, 0xee300a60, 0xed9f1a17\n"
        ".word 0xee601a21, 0xee000a10, 0xe28d0050, 0xeeb80ac0\n"
        ".word 0xee210a80, 0xee200a20, 0xee200a01, 0xebfd8c96\n"
        ".word 0xe3a00000, 0xe320f000, 0xebfd9969, 0xedd60a34\n"
        ".word 0xed961a33, 0xee7d1a60, 0xee401a20, 0xee210a81\n"
        ".word 0xea000007, 0x40490fdb, 0x40000000, 0x4222f983\n"
        ".word 0x3c23d70a, 0x00000000, 0x00472530, 0x3f000000\n"
        ".word 0x3c8efa35, 0xe59d1098, 0xe2880f49, 0xe5881100\n"
        ".word 0xedc8aa41, 0xedc8ca42, 0xed88aa43, 0xed888a48\n"
        ".word 0xe2881e11, 0xec80ba03, 0xe2880f45, 0xed888a44\n"
        ".word 0xec80ba03, 0xe2880d05, 0xedd80a44, 0xee600a80\n"
        ".word 0xedc80a44, 0xedd80a45, 0xee600a80, 0xedc80a45\n"
        ".word 0xedd80a46, 0xee600a80, 0xedc80a46, 0xedd80a47\n"
        ".word 0xee200a80, 0xed880a47, 0xedd81a44, 0xed987a53\n"
        ".word 0xedd82a45, 0xedd85a57, 0xed986a54, 0xedd83a55\n"
        ".word 0xedd84a56, 0xed982a46, 0xedd86a5b, 0xed983a58\n"
        ".word 0xed984a59, 0xed985a5a, 0xec900a03, 0xe2880c01\n"
        ".word 0xee210a80, 0xee610aa0, 0xee211a81, 0xee611a87\n"
        ".word 0xee020a86, 0xee420aa3, 0xee021aa4, 0xee421aa5\n"
        ".word 0xee020a03, 0xee420a04, 0xee021a05, 0xee421a26\n"
        ".word 0xec810a04, 0xed982a40, 0xee320a00, 0xed880a40\n"
        ".word 0xed980a41, 0xee300a20, 0xed880a41, 0xed980a42\n"
        ".word 0xee300a01, 0xed880a42, 0xed980a43, 0xee300a21\n"
        ".word 0xed880a43, 0xec900a03, 0xe3a00000, 0xec840a03\n"
        ".word 0xebfd9917, 0xeef02a6f, 0xedd60a37, 0xed963a36\n"
        ".word 0xe2882c01, 0xed9d1a18, 0xed9d2a0c, 0xeef01a6e\n"
        ".word 0xec822a02, 0xee3d2a60, 0xe2882f42, 0xe2881e12\n"
        ".word 0xec821a02, 0xe2880e11, 0xe2888e11, 0xe51f26b4\n"
        ".word 0xee002a20, 0xee220a03, 0xecd10a04, 0xe2821e11\n"
        ".word 0xecc00a04, 0xe2820c01, 0xedd80a00, 0xee600a80\n"
        ".word 0xedc80a00, 0xedd80a01, 0xee600a80, 0xedc80a01\n"
        ".word 0xedd80a02, 0xee600a80, 0xedc80a02, 0xedd80a03\n"
        ".word 0xee200a80, 0xed880a03, 0xedd22a50, 0xed920a51\n"
        ".word 0xed922a52, 0xed927a53, 0xed923a54, 0xed924a55\n"
        ".word 0xed925a56, 0xed926a57, 0xedd23a58, 0xedd24a59\n"
        ".word 0xedd25a5a, 0xedd26a5b, 0xecd10a03, 0xee602aa2\n"
        ".word 0xee200a80, 0xee202a82, 0xee600a87, 0xee412a03\n"
        ".word 0xee010a04, 0xee012a05, 0xee410a06, 0xee412aa3\n"
        ".word 0xee010aa4, 0xee012aa5, 0xee410aa6, 0xedc12a00\n"
        ".word 0xed810a01, 0xed812a02, 0xedc10a03, 0xed921a40\n"
        ".word 0xee311a22, 0xed821a40, 0xed921a41, 0xee310a00\n"
        ".word 0xed820a41, 0xed920a42, 0xee300a02, 0xed820a42\n"
        ".word 0xed920a43, 0xee300a20, 0xed820a43, 0xec900a03\n"
        ".word 0xe284100c, 0xe3a00000, 0xec810a03, 0xebfd98c8\n"
        ".word 0xedd60a3d, 0xed961a3c, 0xe3a00000, 0xee7d1a60\n"
        ".word 0xee401a20, 0xee210a81, 0xed840a0d, 0xebfd98c0\n"
        ".word 0xedd60a3a, 0xedd61a39, 0xe59d001c, 0xee3d1a60\n"
        ".word 0xed1faaa5, 0xee001a20, 0xee210a21, 0xed840a0c\n"
        ".word 0xed84aa0f, 0xecc58a03, 0xe585000c, 0xe3a00000\n"
        ".word 0xebfd98b3, 0xedd60a1b, 0xe59d00a4, 0xee3d1a60\n"
        ".word 0xe3500002, 0xee001a20, 0xed841a10, 0x0d84aa11\n"
        ".word 0x0d84da12, 0x0a000016, 0xe3a00000, 0xebfd98a8\n"
        ".word 0xedd60a26, 0xe59d00a4, 0xee3d1a60, 0xe3500001\n"
        ".word 0xee001a20, 0xed841a12, 0x1d84aa11, 0x1a00000c\n"
        ".word 0xe3a00000, 0xebfd989e, 0xeddf0ad2, 0xe3a00000\n"
        ".word 0xee200a20, 0xed840a11, 0xebfd986c, 0xe3100001\n"
        ".word 0xe320f000, 0x0a000002, 0xed940a12, 0xeeb10a40\n"
        ".word 0xed840a12, 0xe895110c, 0xe3a00000, 0xe59d106c\n"
        ".word 0xe5850010, 0xe28d0088, 0xe3510000, 0xe880110c\n"
        ".word 0x0a0000a2, 0xe3a00000, 0xebfd985c, 0xe59d107c\n"
        ".word 0xe320f000, 0xebff84f9, 0xee001a10, 0xedd40a0d\n"
        ".word 0xed1f1adb, 0xe51f88cc, 0xeeb88a40, 0xee2d0a88\n"
        ".word 0xee600a88, 0xee200a08, 0xee400a01, 0xeef40aca\n"
        ".word 0xeef1fa10, 0xee6e1a08, 0xed940a0c, 0xeef0fa4a\n"
        ".word 0x3ef00a4a, 0xee200a08, 0xeeb02a6f, 0xee611a88\n"
        ".word 0xee010a81, 0xeeb40ac2, 0xeef1fa10, 0xed9f1aa6\n"
        ".word 0x3eb00a6f, 0xee20aa81, 0xedd40a0f, 0xee1a0a10\n"
        ".word 0xe35005fe, 0xceb0aa4d, 0xe2880c01, 0xeef40aca\n"
        ".word 0xeef1fa10, 0xed9f1a9d, 0xceb0aa60, 0xdd84aa0f\n"
        ".word 0xee7d0a4a, 0xee6a1a0a, 0xedd62a3f, 0xed964a40\n"
        ".word 0xedd65a41, 0xed943a00, 0xedd44a01, 0xed946a02\n"
        ".word 0xedd43a03, 0xed945a04, 0xee202aa0, 0xedd46a05\n"
        ".word 0xeddd7a27, 0xedddca0d, 0xedddea2a, 0xedc0aa03\n"
        ".word 0xee227a20, 0xee222a0a, 0xee610aa0, 0xee611a8a\n"
        ".word 0xee22ba87, 0xee222a01, 0xee64ba07, 0xee25ca87\n"
        ".word 0xee600a81, 0xee03ba02, 0xee44ba82, 0xee06ca02\n"
        ".word 0xee03baa0, 0xee45ba20, 0xee06caa0, 0xeef00a6f\n"
        ".word 0xeeb40a60, 0xee07baa1, 0xee4cbaa1, 0xee0ecaa1\n"
        ".word 0xeef1fa10, 0xec80ba03, 0x0a00004d, 0xe28d0050\n"
        ".word 0xebfd8b65, 0xe28de050, 0xe2880e11, 0xe89e100e\n"
        ".word 0xe880100e, 0xe2880c01, 0xe2881c01, 0xed940a0e\n"
        ".word 0xedd80a44, 0xee200a0a, 0xee600a80, 0xedc80a44\n"
        ".word 0xedd80a45, 0xee600a80, 0xedc80a45, 0xedd80a46\n"
        ".word 0xee600a80, 0xedc80a46, 0xedd80a47, 0xee200a80\n"
        ".word 0xed880a47, 0xedc8aa43, 0xec80ba03, 0xe2880d05\n"
        ".word 0xed980a40, 0xedd80a44, 0xee300a60, 0xed880a40\n"
        ".word 0xed980a41, 0xedd80a45, 0xee300a60, 0xed880a41\n"
        ".word 0xed980a42, 0xedd80a46, 0xee300a60, 0xed880a42\n"
        ".word 0xedd80a47, 0xed980a43, 0xee300a60, 0xed880a43\n"
        ".word 0xed987a40, 0xed986a57, 0xed983a54, 0xed984a55\n"
        ".word 0xed985a56, 0xedd86a5b, 0xedd83a58, 0xedd84a59\n"
        ".word 0xedd85a5a, 0xec900a04, 0xe2880f41, 0xec902a02\n"
        ".word 0xee270a00, 0xee671a21, 0xee670a20, 0xee271a01\n"
        ".word 0xee020a03, 0xee421a06, 0xee420a04, 0xee021a05\n"
        ".word 0xee020aa3, 0xee421aa6, 0xee420aa4, 0xee021aa5\n"
        ".word 0xec810a04, 0xed982a44, 0xee300a02, 0xed880a40\n"
        ".word 0xed980a45, 0xee300a80, 0xed880a41, 0xed980a46\n"
        ".word 0xee310a00, 0xed880a42, 0xed980a47, 0xee310a80\n"
        ".word 0xed880a43, 0xe2880c01, 0xeebd0ac8, 0xe890000e\n"
        ".word 0xe598010c, 0xe585000c, 0xe885000e, 0xed850a04\n"
        ".word 0xe5952010, 0xe28d3088, 0xe1a01006, 0xe1a00005\n"
        ".word 0xebfd976f, 0xed950a06, 0xedd40a10, 0xe59d006c\n"
        ".word 0xee200a20, 0xe3500000, 0xed850a06, 0xed950a07\n"
        ".word 0xedd40a12, 0xee200a20, 0xed850a07, 0xedd40a11\n"
        ".word 0xee300a20, 0xed850a07, 0x0a000008, 0xe1a01005\n"
        ".word 0xe1a00009, 0xebfd9742, 0xe320f000, 0xe320f000\n"
        ".word 0xebfe106c, 0xe5951010, 0xe0800001, 0xe5850010\n"
        ".word 0xe24bb001, 0xeafffd6a, 0x40c90fdb, 0x3a83126f\n"
        ".word 0x40400000\n");
}

// ---------------------------------------------------------------------------
// engine_func_00304164 (0x00304164), 3,684 B
// ---------------------------------------------------------------------------
//
// Recovered role: rebuild one owner's ribbon/trail geometry.  `owner->buffer`
// holds the entry array and the fractional time; `owner->config` supplies the
// segment length, angular step and the radial/fade curves.  For every 0x30-byte
// entry the routine either initializes the random phase (life == -1), fades
// the colour by 0x40000000 per call, or rebuilds the five-vec3 cross-section
// at track+0x30 and the 0x3C-byte history records that follow it.  The
// orientation matrices are built through 0x00248650 / 0x002485F0 / 0x00248444 /
// 0x002486EC and applied to the shared 0x004EA81C block.

// DECOMP_FUNC(0x00304164, 3684)
#if 0
void engine_func_00304164(TrailOwner* owner) {
    TrailBuffer* const buffer = owner->buffer;      // 0x0030417C
    TrailConfig* const config = owner->config;      // 0x00304170
    TrailEntry* const entries =
        static_cast<TrailEntry*>(buffer->entries);  // 0x00304184

    // 0x00304188..0x00304198
    if (owner->limit > config->active_count && config->active_count != 0) {
        return;
    }

    // 0x0030419C..0x00304204: per-frame segment/angle increments.
    const f32 span =
        config->segment_length / static_cast<f32>(config->frame_span);
    const f32 angle_step =
        3.14159265f * static_cast<f32>(config->angle_count) /
        static_cast<f32>(config->frame_span);
    if (span <= 0.0f) {
        return;
    }

    // 0x00304208: camera translation vec4 into sp+0xD8.
    f32 camera[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    func_0019d9d4(camera);

    // 0x00304210..0x0030426C: cumulative cross-section widths parked at
    // sp+0x08..sp+0x18 and reused as the per-ring offsets by the history
    // loop.  sp+0xEC holds the common spread/slope step.
    const f32 width_80 = config->field_80;
    const f32 width_7c = config->field_7c;
    const f32 stack_width0 = width_80 + width_7c;       // sp+0x10
    const f32 stack_width1 = stack_width0 + width_7c;   // sp+0x14
    const f32 stack_width2 = stack_width1 + width_80;   // sp+0x18
    const f32 spread_factor = span * 0.1f * -0.0872665f; // sp+0xEC

    // 0x003041CC/0x00304220: the local radius copy and the jitter base live
    // across the whole entry loop, not per entry.
    f32 radius = config->radius;                        // sp+0x74
    f32 radial_base = 0.34906587f;                      // sp+0xBC

    // 0x00304260..0x0030427C: buffer time accumulator.  The old value is the
    // sample time used by the spawn phase.
    const f32 sample_time = buffer->time;
    buffer->time += buffer->step;

    if (config->entry_count <= 0) {                 // 0x00304280
        return;
    }

    for (s32 index = 0; index < config->entry_count; ++index) {
        TrailEntry* const entry = &entries[index];

        // ------------------------------------------------------------------
        // 0x00304DE8..0x00304F3C: initialise the entry (life == -1).
        // ------------------------------------------------------------------
        if (entry->life == -1) {
            const f32 random0 = engine_func_0024ba44(0);
            entry->offset_a =
                ((1.0f - config->field_a4) +
                 random0 * config->field_a4) * config->field_a0;
            entry->offset_b = 0.0f;

            if (config->field_88 == 0) {
                const f32 random1 = engine_func_0024ba44(0);
                entry->offset_c = 0.0f;
                entry->angle_a = (random1 - 0.5f) * 2.0f * 3.14159265f;
                const f32 random2 = engine_func_0024ba44(0);
                entry->angle_b = (random2 - 0.5f) * 2.0f * 3.14159265f;
            } else {
                const f32 random1 = engine_func_0024ba44(0);
                entry->angle_a =
                    (random1 - 0.5f) * 2.0f * 0.78539816f;
                const f32 random2 = engine_func_0024ba44(0);
                entry->offset_c = random2 * config->fade_speed;
                const f32 random3 = engine_func_0024ba44(0);
                entry->angle_b = (random3 - 0.5f) * 2.0f * 3.14159265f;
            }

            // 0x00304E98..0x00304F04
            ui_func_00248650(entry->angle_a);
            ui_func_002485f0(entry->angle_b);
            func_00248444();

            UiPartRenderStateView& rs = RenderState();
            const f32 spin = entry->offset_b * 40.743665f;
            rs.vector[0] = ui_func_002b73a4(spin) * sample_time;
            rs.vector[1] = 0.0f;
            rs.vector[2] = ui_func_002b740c(spin) * sample_time;
            func_0024603c();                        // 0x00304F04

            // 0x00304F0C..0x00304F3C
            entry->vector[0] = rs.vector[0];
            entry->vector[1] = rs.vector[1];
            entry->vector[2] = rs.vector[2];
            entry->color = 0xFFFFFFFFu;
            continue;
        }

        // ------------------------------------------------------------------
        // 0x00304294..0x003042FC: colour fade; 0x00304F74 handles the final
        // decrement when the alpha byte has reached 0x40.
        // ------------------------------------------------------------------
        if ((entry->color & 0xFF000000u) > 0x40000000u) {
            entry->color -= 0x40000000u;            // 0x003042A8..B0
        } else {
            entry->life = -1;                       // 0x00304F84
            if (config->field_40 > 0) {
                const s32 random = static_cast<s32>(engine_func_0024b990(0));
                entry->life -= ui_func_002c6c10(random, config->field_40);
            }
            continue;
        }

        // 0x003042DC..0x00304304: mirror the local radius copy; the listing
        // negates sp+0x74, never config+0x50.
        if ((engine_func_0024b990(0) & 1) != 0) {
            radius = -radius;
        }
        const f32 random0 = engine_func_0024ba44(0);
        const f32 radial = (0.05f + random0 * 0.95f) * radius;
        const f32 phase = engine_func_0024ba44(0) * 3.14159265f;

        // 0x00304330..0x00304370: the two neighbouring ring samples and the
        // resulting tangent angle.
        const f32 ring0 =
            ui_func_002b740c(phase * 40.743665f) * radial;
        const f32 ring1 =
            ui_func_002b740c((phase + angle_step) * 40.743665f) * radial;
        const f32 dx = ring1 - ring0;
        const f32 tangent =
            func_002460b4(dx / std::sqrt(dx * dx + span * span));

        const f32 random1 = engine_func_0024ba44(0);
        const f32 spread = 0.3f + random1 * 0.7f;

        // 0x00304394..0x003043DC: the live path only reads the spawn
        // offsets +0x24/+0x28 to derive the ring angle; it never writes
        // +0x24/+0x28/+0x2C, so offset_c keeps its spawned value.
        const f32 life_plus_one = static_cast<f32>(entry->life + 1);
        const f32 ring_angle =
            (entry->offset_b +
             (entry->offset_a +
              0.5f * config->time_step * life_plus_one) * life_plus_one) *
            40.743665f;
        const f32 spread_b = spread * spread_factor;    // sp+0xF8

        // 0x003043E0..0x00304438: two rotation matrices and the combined
        // basis.
        ui_func_00248650(entry->angle_a);
        ui_func_002485f0(entry->angle_b);
        func_00248444();

        UiPartRenderStateView& rs = RenderState();
        rs.vector[0] = ui_func_002b73a4(ring_angle) * sample_time;
        rs.vector[1] = 0.0f;
        rs.vector[2] = ui_func_002b740c(ring_angle) * sample_time;
        rs.vector[3] = 0.0f;
        func_0024603c();                            // 0x0030443C

        // 0x00304440..0x003044AC: keep the transformed direction D for the
        // cross-section/translate, then normalize it into the quaternion
        // copy at sp+0xC0 (used as the first rotation axis).
        const f32 dir[3] = {rs.vector[0], rs.vector[1], rs.vector[2]};
        Normalize3(rs.vector);
        f32 quat[4] = {
            rs.vector[0], rs.vector[1], rs.vector[2], rs.vector[3],
        };
        f32 tangent_dir[3] = {
            dir[0] - entry->vector[0],
            dir[1] - entry->vector[1],
            dir[2] - entry->vector[2],
        };
        Normalize3(tangent_dir);                    // 0x003044DC..0x00304520
        rs.scratch[0] = tangent_dir[0];             // g+0x120
        rs.scratch[1] = tangent_dir[1];
        rs.scratch[2] = tangent_dir[2];
        rs.scratch[3] = 0.0f;
        // 0x00304594..0x003045C8: first cross product, tangent x normalized
        // direction (the quaternion copy at +0x110).
        f32 cross[3] = {
            tangent_dir[1] * quat[2] - tangent_dir[2] * quat[1],
            tangent_dir[2] * quat[0] - tangent_dir[0] * quat[2],
            tangent_dir[0] * quat[1] - tangent_dir[1] * quat[0],
        };
        Normalize3(cross);
        // 0x003045D0..0x003045D8: this normalized tangent cross is parked at
        // sp+0x50 and later consumed by the second 0x002486EC call.
        f32 saved_cross_quad[4] = {cross[0], cross[1], cross[2], 0.0f};

        // 0x003045DC..0x003045E4: the camera quad is copied into +0x110.
        rs.color[0] = camera[0];
        rs.color[1] = camera[1];
        rs.color[2] = camera[2];
        rs.color[3] = camera[3];

        // 0x003045E8..0x003045F4: the normalized tangent becomes +0x100.
        for (s32 i = 0; i < 3; ++i) {
            rs.vector[i] = tangent_dir[i];
        }
        rs.vector[3] = 0.0f;

        // 0x003045F8..0x0030466C: second cross, (tangent x direction) x camera,
        // normalized.  This is the basis used for the ribbon.
        f32 basis[3] = {
            tangent_dir[1] * camera[2] - tangent_dir[2] * camera[1],
            tangent_dir[2] * camera[0] - tangent_dir[0] * camera[2],
            tangent_dir[0] * camera[1] - tangent_dir[1] * camera[0],
        };
        Normalize3(basis);

        // 0x00304670..0x00304684: mirror the basis into +0x120 and +0x110.
        for (s32 i = 0; i < 3; ++i) {
            rs.scratch[i] = basis[i];
            rs.color[i] = basis[i];
        }
        rs.scratch[3] = 0.0f;
        rs.color[3] = 0.0f;

        // 0x00304688..0x0030468C: the basis vector is scaled by
        // config+0x80 + config+0x7C and parked in g_TrailScratchB.
        const f32 width0 = stack_width0;
        const f32 width1 = width_7c;
        g_TrailScratchB[0] = basis[0] * width0;
        g_TrailScratchB[1] = basis[1] * width0;
        g_TrailScratchB[2] = basis[2] * width0;
        g_TrailScratchB[3] = 0.0f;

        // 0x0030445C..0x00304544: five cross-section points.  The listing
        // fills +0x00 = +basis*w0, +0x0C = +basis*w1, +0x18 = 0,
        // +0x24 = -basis*w1 and +0x30 = -basis*w0.
        TrailFrame* const frame = entry->frame;      // 0x003042B4
        TrailTrack* const track =
            static_cast<TrailTrack*>(frame->track);  // 0x003042C4
        f32* const points = track->points;           // r8
        points[0] = g_TrailScratchB[0];
        points[1] = g_TrailScratchB[1];
        points[2] = g_TrailScratchB[2];
        points[12] = -g_TrailScratchB[0];            // +0x30
        points[13] = -g_TrailScratchB[1];
        points[14] = -g_TrailScratchB[2];
        // 0x0030472C..0x00304780: the same second-cross basis is scaled by
        // config+0x7C and stored at +0x0C / +0x24.
        points[3] = basis[0] * width1;               // +0x0C
        points[4] = basis[1] * width1;
        points[5] = basis[2] * width1;
        points[9] = -basis[0] * width1;              // +0x24
        points[10] = -basis[1] * width1;
        points[11] = -basis[2] * width1;
        points[6] = 0.0f;                            // +0x18
        points[7] = 0.0f;
        points[8] = 0.0f;

        // 0x003047F0..0x00304808: translation = direction with offset_c on Y.
        const f32 translate[3] = {
            dir[0], dir[1] + entry->offset_c, dir[2],
        };
        for (s32 k = 0; k < 5; ++k) {
            points[k * 3 + 0] += translate[0];
            points[k * 3 + 1] += translate[1];
            points[k * 3 + 2] += translate[2];
        }
        entry->vector[0] = dir[0];                   // 0x003048CC
        entry->vector[1] = dir[1];
        entry->vector[2] = dir[2];

        // 0x003048BC: the first 0x3C block is the live cross-section; the
        // history records follow it.  `segments` is frame->count / 5
        // (0x003042B8..0x003042D8: smulbb 0x6667, asr 17).
        const s32 segments = static_cast<s32>(frame->count) / 5;
        f32 offsets[5] = {0.0f, 0.0f, 0.0f, 0.0f, 0.0f};   // sp+0xA0
        // 0x00304240..0x0030426C: sp+0x08 already holds the five cumulative
        // ring widths used to scale each per-ring step.
        f32 accum[5] = {
            0.0f, width_80, stack_width0, stack_width1, stack_width2,
        };
        if (segments > 1) {
            u8* history = reinterpret_cast<u8*>(points) + 0x3C;
            f32 phase_accum = phase + angle_step;    // s17 at 0x00304344
            f32 section_radial = radial;             // sp+0xF4
            f32 spread_b_hist = spread_b;            // sp+0xF8
            f32 ring_prev = ring1;                   // s28 at 0x00304354
            f32 prev_twist = tangent;                // s29 at 0x00304374

            for (s32 seg = 1; seg < segments; ++seg, history += 0x3C) {
                // 0x003048F0..0x0030490C
                const f32 jitter_random = engine_func_0024ba44(0);
                const f32 jitter =
                    (0.25f + jitter_random * 0.75f) * radial_base;

                // 0x00304910: third engine_func_0024B990 tick.
                if ((engine_func_0024b990(0) & 1) != 0) {
                    radial_base = -radial_base;
                }

                // 0x0030492C..0x00304998: the first iteration starts at
                // phase + 2*angle_step because s17 already held
                // phase + angle_step before the loop.
                phase_accum += angle_step;
                if (phase_accum >= 3.14159265f) {
                    const f32 old_radius = radius;
                    radius = -radius;
                    phase_accum -= 3.14159265f;
                    const f32 random_a = engine_func_0024ba44(0);
                    section_radial =
                        -(old_radius * (0.05f + random_a * 0.95f));
                    const f32 random_b = engine_func_0024ba44(0);
                    spread_b_hist =
                        (0.3f + random_b * 0.7f) * spread_factor;
                }

                // 0x0030499C..0x003049C8: second 0x002460B4 call.
                const f32 ring =
                    ui_func_002b740c(phase_accum * 40.743665f) *
                    section_radial;
                const f32 slope = ring - ring_prev;
                const f32 twist =
                    func_002460b4(slope / std::sqrt(slope * slope +
                                                    span * span)) + jitter;

                // 0x003049D0..0x00304A6C: first orientation matrix from the
                // saved quaternion and the previous twist, then transform the
                // tangent into dir2.
                func_002486ec(quat, prev_twist);
                f32 dir2[4] = {
                    tangent_dir[0], tangent_dir[1], tangent_dir[2], 0.0f,
                };
                Transform4(rs.matrix, dir2, dir2);

                // 0x00304A74..0x00304AFC: second orientation matrix from the
                // cross-section quad (sp+0x50) and the spread angle.
                func_002486ec(saved_cross_quad, spread_b_hist);

                // 0x00304B00..0x00304BA4: transform the unnormalized spawn
                // direction D through the second matrix.
                f32 delta_dir[4] = {dir[0], dir[1], dir[2], 0.0f};
                Transform4(rs.matrix, delta_dir, delta_dir);

                // 0x00304BA4..0x00304C10: the per-sample length is the norm
                // of the D2 - D delta (0x00304BF0..0x00304C08), not the
                // transformed direction.
                f32 sample_delta[3] = {
                    delta_dir[0] - dir[0],
                    delta_dir[1] - dir[1],
                    delta_dir[2] - dir[2],
                };
                const f32 length = std::sqrt(
                    sample_delta[0] * sample_delta[0] +
                    sample_delta[1] * sample_delta[1] +
                    sample_delta[2] * sample_delta[2]);
                // 0x00304BC4/0x00304C10: (twist - previous_twist) * 0.5,
                // then func_00361074(...) * pi/128.
                const f32 twist_delta = (twist - prev_twist) * 0.5f;
                const f32 sample_step =
                    func_00361074(twist_delta) * 0.024543693f;  // pi/128

                // 0x00304C18..0x00304C1C: refresh s28/s29 for the next ring.
                ring_prev = ring;
                prev_twist = twist;

                // 0x00304C14..0x00304D74: five transformed history points.
                // r6-0x3C is the previous 0x3C-byte record; r4 advances by
                // 0x3C at 0x00304D7C.
                TrailSample* const sample =
                    reinterpret_cast<TrailSample*>(history);
                const TrailSample* const prev_sample = sample - 1;
                for (s32 k = 0; k < 5; ++k) {
                    const f32 step = accum[k] * sample_step;
                    // 0x00304C70..C78: the ring offset accumulates the step
                    // and `length` is added to the updated offset.
                    offsets[k] += step;
                    const f32 scale = offsets[k] + length;

                    sample->points[k][0] = prev_sample->points[k][0] +
                                           dir2[0] * scale;
                    sample->points[k][1] = prev_sample->points[k][1] +
                                           dir2[1] * scale;
                    sample->points[k][2] = prev_sample->points[k][2] +
                                           dir2[2] * scale;
                }
            }
        }

        // 0x00304D9C..0x00304DB0: advance the entry lifetime by the global
        // frame timer.
        entry->life += static_cast<s32>(ui_func_00269cb8());
    }
}
#endif

// Readable trail buffer update draft above; exact ARM body retained pending codegen recovery.
__attribute__((naked)) void engine_func_00304164(TrailOwner* owner) {
    asm volatile(
        ".word 0xe92d4ff0, 0xed2d8b10, 0xe24ddf43, 0xe5901034\n"
        ".word 0xe5902028, 0xe58d104c, 0xe5904030, 0xe5910034\n"
        ".word 0xe5941000, 0xe1520000, 0xe58d1000, 0xda000001\n"
        ".word 0xe3500000, 0x1a00030f, 0xe59d004c, 0xed9f8ae8\n"
        ".word 0xed9f9ae8, 0xedd00a0f, 0xedd01a21, 0xed901a13\n"
        ".word 0xe5900038, 0xe58d0094, 0xe59d004c, 0xe5900040\n"
        ".word 0xe58d007c, 0xe59d004c, 0xed900a14, 0xed8d0a1d\n"
        ".word 0xed900a2a, 0xed8d0a1b, 0xeeb80a60, 0xeef80a41\n"
        ".word 0xe5d00088, 0xe58d00e8, 0xee81ca80, 0xee201a88\n"
        ".word 0xeeb4cac9, 0xeef1fa10, 0xeec10a00, 0xedcd0a22\n"
        ".word 0x9a0002f4, 0xe28d00d8, 0xebfa65f0, 0xe59d0094\n"
        ".word 0xed9f0acf, 0xeddf0acc, 0xe3500000, 0xed8d0a2f\n"
        ".word 0xe3a00000, 0xe58d0084, 0xed8d9a11, 0xed8d9a02\n"
        ".word 0xe59d004c, 0xee2c2a20, 0xed9f1ac4, 0xed900a20\n"
        ".word 0xed8d0a03, 0xedd00a1f, 0xe2840004, 0xee701a20\n"
        ".word 0xee221a01, 0xee710aa0, 0xed8d1a3b, 0xedcd1a04\n"
        ".word 0xedcd0a05, 0xee300a80, 0xed8d0a06, 0xec900a02\n"
        ".word 0xed8d0a3c, 0xee700a20, 0xedc40a01, 0xda0002d5\n"
        ".word 0xe59d0000, 0xe5900014, 0xe3700001, 0x0a0002d4\n"
        ".word 0xe59d0000, 0xe5900018, 0xe20014ff, 0xe3510101\n"
        ".word 0x9a000332, 0xe2801103, 0xe59d0000, 0xe5801018\n"
        ".word 0xe59d0000, 0xe59f129c, 0xe5900000, 0xe1d020b2\n"
        ".word 0xe5903008, 0xe1600182, 0xe5938030, 0xe1a018c0\n"
        ".word 0xe0410fc0, 0xe58d0080, 0xe3a00000, 0xebfd1daa\n"
        ".word 0xe3100001, 0xe320f000, 0x0a000002, 0xed9d0a1d\n"
        ".word 0xeeb10a40, 0xed8d0a1d, 0xe3a00000, 0xebfd1dcf\n"
        ".word 0xeddf0a8f, 0xe3a00000, 0xee208a20, 0xebfd1dcb\n"
        ".word 0xeddffa91, 0xeddf0a91, 0xed9faa91, 0xee400a2f\n"
        ".word 0xed9d0a1d, 0xee600a80, 0xee280a0a, 0xedcd0a3d\n"
        ".word 0xebfecc34, 0xeddd0a3d, 0xee609a20, 0xed9d0a22\n"
        ".word 0xee788a00, 0xee280a8a, 0xebfecc2e, 0xeddd0a3d\n"
        ".word 0xee20ea20, 0xee7e0a69, 0xee200aa0, 0xee0c0a0c\n"
        ".word 0xeeb11ac0, 0xee800a81, 0xebfd0750, 0xe59d004c\n"
        ".word 0xeef0ea40, 0xedd00a20, 0xed908a1f, 0xe3a00000\n"
        ".word 0xee30ba88, 0xebfd1dad, 0xe59d0000, 0xeeb02a40\n"
        ".word 0xed9f0a75, 0xeddf0a75, 0xe5901014, 0xedd01a09\n"
        ".word 0xed903a0a, 0xe2810001, 0xee010a10, 0xee420a00\n"
        ".word 0xeddf2a6c, 0xeeb80ac1, 0xed9d1a1b, 0xee211a00\n"
        ".word 0xee411a22, 0xed9d1a3b, 0xee600a81, 0xee210a80\n"
        ".word 0xedcd0a3e, 0xe59d0000, 0xee739a00, 0xed900a07\n"
        ".word 0xebfd1099, 0xe59d0000, 0xed900a08, 0xebfd107e\n"
        ".word 0xe320f000, 0xe320f000, 0xebfd1010, 0xee29aa8a\n"
        ".word 0xeeb00a4a, 0xebfecbe5, 0xeddd0a3c, 0xeddfba4d\n"
        ".word 0xee609a20, 0xeeb00a4a, 0xebfecbfa, 0xeddd0a3c\n"
        ".word 0xe59fb14c, 0xee200a20, 0xedcb9a40, 0xedcbba41\n"
        ".word 0xed8b0a42, 0xedcbba43, 0xebfd06fe, 0xe28b0c01\n"
        ".word 0xed9bfa43, 0xecd0ca03, 0xed8dfa11, 0xeddb0a42\n"
        ".word 0xec901a02, 0xee210a01, 0xee010aa1, 0xee000aa0\n"
        ".word 0xeef10ac0, 0xeef40aeb, 0xeef1fa10, 0xda000007\n"
        ".word 0xeeb02a61, 0xeec11a20, 0xed900a02, 0xedc01a00\n"
        ".word 0xee821a20, 0xed801a01, 0xee802a20, 0xed802a02\n"
        ".word 0xe890100c, 0xe1a01000, 0xe590000c, 0xe28d40c0\n"
        ".word 0xeeb01a6d, 0xe58d00cc, 0xe884100c, 0xeeb00a6c\n"
        ".word 0xe59d0000, 0xeef00a4d, 0xe2800004, 0xecd01a03\n"
        ".word 0xe1a00001, 0xed819a03, 0xee701a61, 0xee712a62\n"
        ".word 0xee302ac2, 0xecc11a03, 0xedd12a00, 0xedd11a01\n"
        ".word 0xed913a02, 0xee222aa2, 0xee012aa1, 0xee032a03\n"
        ".word 0xeef11ac2, 0xeef41aeb, 0xeef1fa10, 0xda000007\n"
        ".word 0xeeb02a43, 0xee823aa1, 0xedd03a01, 0xed803a00\n"
        ".word 0xeec32aa1, 0xedc02a01, 0xeec23a21, 0xedc13a02\n"
        ".word 0xe590200c, 0xedd09a00, 0xe2800004, 0xe28b1e12\n"
        ".word 0xec90aa02, 0xe28b0e11, 0xe28d40c0, 0xecc19a03\n"
        ".word 0xea00000c, 0x40490fdb, 0x00000000, 0x3dcccccd\n"
        ".word 0xbdb2b8c2, 0x3eb2b8c2, 0x00006667, 0x3f733333\n"
        ".word 0x3d4cccd0, 0x4222f983, 0x3f000000, 0x3f333333\n"
        ".word 0x3e99999a, 0x004ea81c, 0xe58b212c, 0xe894100e\n"
        ".word 0xe28d6050, 0xe880100e, 0xe28b1c01, 0xe1a00001\n"
        ".word 0xeddb2a45, 0xeddb3a40, 0xeddb1a46, 0xed9b4a41\n"
        ".word 0xed9b2a42, 0xed9b3a44, 0xee635aa2, 0xee644a21\n"
        ".word 0xee225a03, 0xe28b2e11, 0xee445a43, 0xee424a62\n"
        ".word 0xee035ae1, 0xecc14a03, 0xe28b1e12, 0xe8901038\n"
        ".word 0xe28b0c01, 0xe8861038, 0xe28d60d8, 0xe8961038\n"
        ".word 0xe8821038, 0xe1c120d0, 0xe59b1128, 0xe58b1108\n"
        ".word 0xe1c020f0, 0xed9b4a41, 0xeddb1a46, 0xed9b2a42\n"
        ".word 0xed9b3a44, 0xee644a21, 0xeddb2a45, 0xee225a03\n"
        ".word 0xeddb3a40, 0xe28b1c01, 0xe1a00001, 0xee635aa2\n"
        ".word 0xee424a62, 0xee035ae1, 0xee445a43, 0xee641aa4\n"
        ".word 0xecc14a03, 0xee451a05, 0xee451aa5, 0xeeb12ae1\n"
        ".word 0xeeb42aeb, 0xeef1fa10, 0xda000007, 0xed903a01\n"
        ".word 0xedd01a02, 0xeec42a82, 0xedc02a00, 0xeec33a02\n"
        ".word 0xedc03a01, 0xee813a82, 0xed813a02, 0xe28b1e12\n"
        ".word 0xecd01a04, 0xe28b0e11, 0xecc11a03, 0xe28b1c01\n"
        ".word 0xecc01a04, 0xeddb1a40, 0xe59f063c, 0xee611a8b\n"
        ".word 0xedcb1a40, 0xeddb1a41, 0xee611a8b, 0xedcb1a41\n"
        ".word 0xeddb1a42, 0xee611a8b, 0xedcb1a42, 0xeddb1a43\n"
        ".word 0xee611a8b, 0xedcb1a43, 0xe891100c, 0xe59b110c\n"
        ".word 0xe580100c, 0xe880100c, 0xe5882000, 0xe5901004\n"
        ".word 0xe5881004, 0xe5901008, 0xe5881008, 0xeddb1a40\n"
        ".word 0xe28b1c01, 0xeef11a61, 0xedcb1a40, 0xeddb1a41\n"
        ".word 0xeef11a61, 0xedcb1a41, 0xeddb1a42, 0xeef11a61\n"
        ".word 0xedcb1a42, 0xe891100c, 0xe59b110c, 0xe580100c\n"
        ".word 0xe880100c, 0xe5882030, 0xe5901004, 0xe5881034\n"
        ".word 0xe5901008, 0xe5881038, 0xeddb1a44, 0xe28b1e11\n"
        ".word 0xee611a88, 0xedcb1a44, 0xeddb1a45, 0xee611a88\n"
        ".word 0xedcb1a45, 0xeddb1a46, 0xee611a88, 0xedcb1a46\n"
        ".word 0xeddb1a47, 0xee611a88, 0xedcb1a47, 0xe891100c\n"
        ".word 0xe59b111c, 0xe580100c, 0xe880100c, 0xe588200c\n"
        ".word 0xe5901004, 0xe5881010, 0xe5901008, 0xe5881014\n"
        ".word 0xeddb1a44, 0xeef11a61, 0xedcb1a44, 0xeddb1a45\n"
        ".word 0xeef11a61, 0xedcb1a45, 0xeddb1a46, 0xe28b2e11\n"
        ".word 0xeef02a4d, 0xeef11a61, 0xe28b1e11, 0xe3a03000\n"
        ".word 0xe28d70a0, 0xe1a05000, 0xedcb1a46, 0xed9d2a11\n"
        ".word 0xeef01a6d, 0xec923a04, 0xec803a04, 0xed883a09\n"
        ".word 0xed903a01, 0xed883a0a, 0xed903a02, 0xed883a0b\n"
        ".word 0xedc8ba06, 0xedc8ba07, 0xedc8ba08, 0xe59d2000\n"
        ".word 0xeeb03a6c, 0xedd23a0b, 0xe2812008, 0xed8b3a44\n"
        ".word 0xee722aa3, 0xedcb2a45, 0xecc21a02, 0xe0831083\n"
        ".word 0xe28bcc01, 0xe0882101, 0xe28b0c01, 0xedd21a00\n"
        ".word 0xe28b1e11, 0xedc51a00, 0xedd21a01, 0xe1a0600c\n"
        ".word 0xedc51a01, 0xedd21a02, 0xe0874103, 0xedc51a02\n"
        ".word 0xe2833001, 0xecd51a04, 0xe3530005, 0xeccc1a04\n"
        ".word 0xeddb1a40, 0xed9b2a44, 0xee711a82, 0xedcb1a40\n"
        ".word 0xeddb1a41, 0xed9b2a45, 0xee711a82, 0xedc01a01\n"
        ".word 0xedd01a02, 0xed912a02, 0xee711a82, 0xedc01a02\n"
        ".word 0xed912a03, 0xedd01a03, 0xee711a82, 0xedc01a03\n"
        ".word 0xed9c3a03, 0xecd61a03, 0xecc51a04, 0xedc21a00\n"
        ".word 0xe5950004, 0xe5820004, 0xe5950008, 0xe5820008\n"
        ".word 0xedc4ba00, 0xbaffffd4, 0xe59d0080, 0xe288403c\n"
        ".word 0xe3500001, 0xe59d0000, 0xed800a01, 0xe59d0000\n"
        ".word 0xedc00a02, 0xe59d0000, 0xed801a03, 0xe3a00001\n"
        ".word 0xe58d00b4, 0xda00012a, 0xe3a00000, 0xebfd1c53\n"
        ".word 0xeef00a40, 0xed9f1af5, 0xed9f0af5, 0xe3a00000\n"
        ".word 0xee000a81, 0xeddd0a2f, 0xee208a20, 0xebfd1c1e\n"
        ".word 0xe3100001, 0xe320f000, 0x0a000002, 0xed9d0a2f\n"
        ".word 0xeeb10a40, 0xed8d0a2f, 0xed9d0a22, 0xe59f03a4\n"
        ".word 0xee788a80, 0xee181a90, 0xe1510000, 0xba000015\n"
        ".word 0xed9dba1d, 0xed9f0ae4, 0xe3a00000, 0xeef10a4b\n"
        ".word 0xee788ac0, 0xedcd0a1d, 0xebfd1c38, 0xeef00a40\n"
        ".word 0xed9f1ade, 0xed9f0ade, 0xe3a00000, 0xee000a81\n"
        ".word 0xee2b0a40, 0xed8d0a3d, 0xebfd1c30, 0xeef00a40\n"
        ".word 0xed9f1ad8, 0xed9f0ad8, 0xee000a81, 0xeddd0a3b\n"
        ".word 0xee200a20, 0xed8d0a3e, 0xed9f0ad4, 0xee280a80\n"
        ".word 0xebfeca98, 0xeddd0a3d, 0xee20ba20, 0xee3b0a4e\n"
        ".word 0xee600a00, 0xee4c0a0c, 0xeeb11ae0, 0xeec00a01\n"
        ".word 0xeeb00a60, 0xebfd05b9, 0xee70ba08, 0xeeb00a6e\n"
        ".word 0xe28d00c0, 0xebfd0f43, 0xe28b0c01, 0xed8b9a43\n"
        ".word 0xe28b1c01, 0xecc09a03, 0xe28b3f51, 0xeddb2a50\n"
        ".word 0xed9b7a53, 0xed9b3a54, 0xed9b6a57, 0xed9b5a56\n"
        ".word 0xed9b4a55, 0xeddb3a58, 0xeddb6a5b, 0xeddb5a5a\n"
        ".word 0xeddb4a59, 0xe28b2c01, 0xec910a03, 0xe28d0050\n"
        ".word 0xecd31a02, 0xee602a22, 0xee601a21, 0xee202a02\n"
        ".word 0xee200a07, 0xee402a83, 0xee401a84, 0xee002a85\n"
        ".word 0xee000a86, 0xee412a23, 0xee411a24, 0xee012a25\n"
        ".word 0xee010a26, 0xedc12a00, 0xed810a03, 0xe2811004\n"
        ".word 0xecc11a02, 0xe89201c0, 0xedd2fa03, 0xed9d0a3e\n"
        ".word 0xebfd0f1c, 0xe28b0c01, 0xed8b9a43, 0xe28b1c01\n"
        ".word 0xecc09a03, 0xe28b0d05, 0xed9b2a40, 0xeddb7a57\n"
        ".word 0xeddb5a55, 0xeddb6a56, 0xed9b8a5b, 0xed9b5a58\n"
        ".word 0xed9b6a59, 0xed9b7a5a, 0xeeb01a4f, 0xecd02a05\n"
        ".word 0xe28b0c01, 0xeeb00b4d, 0xe28b3c01, 0xee622a22\n"
        ".word 0xee223a03, 0xee224a04, 0xee623a23, 0xed9b2a41\n"
        ".word 0xeddf1a87, 0xee422a24, 0xee023a25, 0xee024a27\n"
        ".word 0xee423a26, 0xed912a02, 0xee422a05, 0xee023a06\n"
        ".word 0xee024a08, 0xee423a07, 0xecc12a04, 0xe28b1d05\n"
        ".word 0xed9b9a43, 0xecd09a03, 0xe28b0f41, 0xedcbca40\n"
        ".word 0xec800a03, 0xe28b0f45, 0xedcbca44, 0xec800a03\n"
        ".word 0xe28b0e11, 0xed9b1a40, 0xed9b0a50, 0xeddb0a51\n"
        ".word 0xeddb3a53, 0xee210a00, 0xee212a20, 0xeddb0a52\n"
        ".word 0xed9b3a41, 0xeddb2a42, 0xee610a20, 0xee211a23\n"
        ".word 0xeddb3a54, 0xee030a23, 0xeddb3a55, 0xee032a23\n"
        ".word 0xedd13a06, 0xee430a23, 0xedd13a07, 0xee031a23\n"
        ".word 0xed913a08, 0xee020a83, 0xed913a09, 0xee022a83\n"
        ".word 0xed913a0a, 0xee420a83, 0xed913a0b, 0xed830a00\n"
        ".word 0xee021a83, 0xed832a01, 0xe2833008, 0xecc30a02\n"
        ".word 0xee3b3aee, 0xedd02a00, 0xe28b2f41, 0xeddbca40\n"
        ".word 0xee702a62, 0xec92da02, 0xe28b1c01, 0xed9bfa43\n"
        ".word 0xee230a21, 0xedcb2a40, 0xedd01a01, 0xee721a61\n"
        ".word 0xedcb1a41, 0xedd01a02, 0xee700ae1, 0xedcb0a42\n"
        ".word 0xedd00a03, 0xee710a60, 0xedc10a03, 0xeddb0a40\n"
        ".word 0xeddb1a41, 0xed9b1a42, 0xee600aa0, 0xee410aa1\n"
        ".word 0xee410a01, 0xeeb18ae0, 0xeb017118, 0xeddf0a39\n"
        ".word 0xe28b0e12, 0xeeb0eb4b, 0xee600a20, 0xe88001c0\n"
        ".word 0xe3a03000, 0xedcbfa4b, 0xe28de0a0, 0xe28d0008\n"
        ".word 0xe0802103, 0xe08e7103, 0xed920a00, 0xed971a00\n"
        ".word 0xe28bae12, 0xee200a20, 0xe28b8e11, 0xe0831083\n"
        ".word 0xe28b9c01, 0xe0846101, 0xe1a01008, 0xe1a02009\n"
        ".word 0xe2833001, 0xe3530005, 0xe1a0c001, 0xee311a00\n"
        ".word 0xed871a00, 0xee311a08, 0xecda1a04, 0xecc81a04\n"
        ".word 0xe1a08002, 0xed561a0f, 0xedc51a00, 0xed561a0e\n"
        ".word 0xedc51a01, 0xed561a0d, 0xedc51a02, 0xecd51a04\n"
        ".word 0xecc91a04, 0xedd11a00, 0xee611a81, 0xedc11a00\n"
        ".word 0xedd11a01, 0xee611a81, 0xedc11a01, 0xedd11a02\n"
        ".word 0xee611a81, 0xedc11a02, 0xea00000b, 0x00472550\n"
        ".word 0x3f400000, 0x3e800000, 0x40490fdb, 0x40490fdb\n"
        ".word 0x3f733333, 0x3d4cccd0, 0x3f333333, 0x3e99999a\n"
        ".word 0x4222f983, 0x3f000000, 0x3cc90fdb, 0xedd11a03\n"
        ".word 0xee211a81, 0xed811a03, 0xedd21a00, 0xed9c1a00\n"
        ".word 0xee311a81, 0xed821a00, 0xed921a01, 0xeddc1a01\n"
        ".word 0xee311a21, 0xed821a01, 0xed921a02, 0xeddc1a02\n"
        ".word 0xee311a21, 0xed821a02, 0xed911a03, 0xedd21a03\n"
        ".word 0xee311a81, 0xed891a03, 0xed921a03, 0xecd81a03\n"
        ".word 0xed851a03, 0xecc51a03, 0xedc61a00, 0xed951a01\n"
        ".word 0xed861a01, 0xed951a02, 0xed861a02, 0xed870a00\n"
        ".word 0xbaffffad, 0xe59d00b4, 0xe284403c, 0xe2800001\n"
        ".word 0xe1a01000, 0xe58d00b4, 0xe59d0080, 0xe1510000\n"
        ".word 0xbafffed4, 0xe320f000, 0xebfd93c5, 0xe59d1000\n"
        ".word 0xe5911014, 0xe0811000, 0xe59d0000, 0xe5801014\n"
        ".word 0xe59d0084, 0xe59d1094, 0xe2800001, 0xe58d0084\n"
        ".word 0xe59d0000, 0xe2800030, 0xe58d0000, 0xe59d0084\n"
        ".word 0xe1500001, 0xbafffd29, 0xe28ddf43, 0xecbd8b10\n"
        ".word 0xe8bd8ff0, 0xe3a00000, 0xebfd1b14, 0xe59d004c\n"
        ".word 0xed9f1a6f, 0xeddf8a6f, 0xedd00a29, 0xedd01a28\n"
        ".word 0xe59d00e8, 0xee311a60, 0xe3500000, 0xe59d0000\n"
        ".word 0xee001a20, 0xee210a21, 0xed800a09, 0xe59d0000\n"
        ".word 0xedc08a0a, 0xe3a00000, 0x0a000043, 0xebfd1b03\n"
        ".word 0xed1f1a51, 0xeddf1a60, 0xeddf0a60, 0xee300a41\n"
        ".word 0xe59d0000, 0xee200a21, 0xee200a20, 0xed800a07\n"
        ".word 0xe3a00000, 0xebfd1af9, 0xe59d004c, 0xedd00a27\n"
        ".word 0xe59d0000, 0xee200a20, 0xed800a0b, 0xe3a00000\n"
        ".word 0xebfd1af2, 0xed5f0a62, 0xed9f1a4f, 0xe59d0000\n"
        ".word 0xee700a60, 0xed1f0a6c, 0xee600a81, 0xee200a80\n"
        ".word 0xed800a08, 0xe59d0000, 0xed900a07, 0xebfd0dea\n"
        ".word 0xe59d0000, 0xed900a08, 0xebfd0dcf, 0xe320f000\n"
        ".word 0xe320f000, 0xebfd0d61, 0xe59d0000, 0xed5f0a75\n"
        ".word 0xed900a0a, 0xee609a20, 0xeeb00a69, 0xebfec933\n"
        ".word 0xeddd0a3c, 0xee208a20, 0xeeb00a69, 0xebfec949\n"
        ".word 0xeddd0a3c, 0xe51f4978, 0xee200a20, 0xeddd0a11\n"
        ".word 0xe2841f42, 0xe2840c01, 0xec810a02, 0xec808a02\n"
        ".word 0xebfd044c, 0xe2840c01, 0xed940a43, 0xe890000e\n"
        ".word 0xe3e0c000, 0xed8d0a11, 0xe59d0000, 0xe5801004\n"
        ".word 0xe59d0000, 0xe5802008, 0xe59d0000, 0xe580300c\n"
        ".word 0xe59d0000, 0xe580c018, 0xeaffff95, 0xe320f000\n"
        ".word 0xebfd1abe, 0xed5f1a96, 0xeddf0a1b, 0xed1f1a9e\n"
        ".word 0xee300a61, 0xe59d0000, 0xedc08a0b, 0xe59d0000\n"
        ".word 0xee200a20, 0xee200a01, 0xed800a07, 0xeaffffbe\n"
        ".word 0xe59d107c, 0xe3e00000, 0xe3510000, 0xe59d1000\n"
        ".word 0xe5810014, 0xdaffff89, 0xe3a00000, 0xebfd1a7e\n"
        ".word 0xe59d107c, 0xe320f000, 0xebff071b, 0xe59d0000\n"
        ".word 0xe5900014, 0xe0401001, 0xe59d0000, 0xe5801014\n"
        ".word 0xeaffff7e, 0x3f800000, 0x00000000, 0x40000000\n"
        ".word 0x3f490fdb\n");
}

} // namespace smt4::engine
