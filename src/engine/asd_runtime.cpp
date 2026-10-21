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
                const f32 a =
                    (part->speed_b * tf + 0.5f * curve_a * tf * tf) *
                    0.001f;
                const f32 t = std::fmin(std::fmax(a, part->progress), 1.0f);
                part->progress = t;

                // 0x002E5950..0x002E59F0: rebuild the orientation matrix
                // from +0x100, then apply it to +0x110.
                // 0x002E5950: axis sp+0x50, angle s0 = the curve value `a`.
                func_002486ec(rs.vector, a);
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
                    const f32 scale = offsets[k] + step + length;
                    offsets[k] = step;

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

} // namespace smt4::engine
