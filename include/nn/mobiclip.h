#pragma once
#include <cstddef>
#include "types.h"

/**
 * Mobiclip video playback runtime.
 *
 * The five reconstructed functions come from three original translation units:
 *
 *   MobiclipCtrl          c:\SMT4\XRD686\sdds4\program\mobiclip_ctrl\MobiclipCtrl.cpp
 *   MobiclipCtrlProcess   c:\SMT4\XRD686\sdds4\program\mobiclip_ctrl\MobiclipCtrlProcess.cpp
 *   helper_S4FsReader     c:\SMT4\XRD686\sdds4\program\mobiclip_ctrl\helper_S4FsReader.cpp
 *   helper_S4AudioDevice  c:\SMT4\XRD686\sdds4\program\mobiclip_ctrl\helper_S4AudioDevice.cpp
 *   helper_S4Player       c:\SMT4\XRD686\sdds4\program\mobiclip_ctrl\helper_S4Player.cpp
 *
 * Only the offsets actually touched by those functions are named.  Fields that
 * the listings never prove remain `pad_NN` arrays.
 */

namespace smt4::nn {

// ---------------------------------------------------------------------------
// MobiclipCtrlProcess (0x0044D048)
// ---------------------------------------------------------------------------

/**
 * Something created by the `Move*` scene-node factory at 0x002C5978 / 0x002C4C00.
 * Only the pointer identity is observed, so the payload stays opaque.
 */
struct MobiclipMoveNode;

/**
 * Playback control block allocated by `MobiclipCtrlProcess_func_002ef664`
 * (0x74 bytes, `AsdMem_Alloc(...,0x74,1)` at 0x002ef698).
 */
struct MobiclipCtrlProcess {
    MobiclipMoveNode* move;             // +0x00: `str r0,[r4]` (0x002ef6d8)
    MobiclipMoveNode* move_ncl;         // +0x04: `str r0,[r4,#4]` (0x002ef708)
    MobiclipMoveNode* move_ncr;         // +0x08: `str r0,[r4,#8]` (0x002ef734)
    u32 field_0c;                       // +0x0C: not touched by this function
    s32 state;                          // +0x10: `str r1,[r4,#0x10]` 9/2/0 (0x002ef744..0x002ef770)
    u8  flag_14;                        // +0x14: not touched by this function
    u8  pad_15[0x03];                   // +0x15..+0x18
    u8  flag_18;                        // +0x18: `strb r7,[r4,#0x18]` then `strbeq r8` (0x002ef788)
    u8  flag_19;                        // +0x19: `strb r8,[r4,#0x19]` (0x002ef7d4)
    u8  flag_1a;                        // +0x1A: `strb r6,[r4,#0x1a]` (0x002ef7dc)
    char path[0x40];                    // +0x1B: `add r0,r4,#0x1b` / strcpy (0x002ef778)
    u8  flag_5b;                        // +0x5B: `strb r7,[r4,#0x5b]` (0x002ef784)
    u8  pad_5c[0x10];                   // +0x5C..+0x6C
    f32 field_6c;                       // +0x6C: `vstr s0,[r4,#0x6c]`, s0 = 0.0 (0x002ef78c)
    u32 field_70;                       // +0x70: `str r7,[r4,#0x70]` (0x002ef794)
};
static_assert(offsetof(MobiclipCtrlProcess, move) == 0x00);
static_assert(offsetof(MobiclipCtrlProcess, move_ncl) == 0x04);
static_assert(offsetof(MobiclipCtrlProcess, move_ncr) == 0x08);
static_assert(offsetof(MobiclipCtrlProcess, state) == 0x10);
static_assert(offsetof(MobiclipCtrlProcess, flag_18) == 0x18);
static_assert(offsetof(MobiclipCtrlProcess, flag_19) == 0x19);
static_assert(offsetof(MobiclipCtrlProcess, flag_1a) == 0x1A);
static_assert(offsetof(MobiclipCtrlProcess, path) == 0x1B);
static_assert(offsetof(MobiclipCtrlProcess, flag_5b) == 0x5B);
static_assert(offsetof(MobiclipCtrlProcess, field_6c) == 0x6C);
static_assert(offsetof(MobiclipCtrlProcess, field_70) == 0x70);
static_assert(sizeof(MobiclipCtrlProcess) == 0x74);

/** Global at 0x0044D048: `[+0x04]` is the live control block (0x002ef6a4). */
struct MobiclipProcessGlobal {
    u32 field_00;                       // +0x00: not touched by this function
    MobiclipCtrlProcess* process;       // +0x04: `str r0,[r1,#4]` (0x002ef6a4)
};
static_assert(offsetof(MobiclipProcessGlobal, process) == 0x04);

extern MobiclipProcessGlobal g_MobiclipProcess;         // 0x0044D048
extern const char* g_MobiclipMovieNames[];              // 0x0044D060, `ldr r3,[r0,r5,lsl #2]` (0x002ef75c)

// ---------------------------------------------------------------------------
// helper_S4FsReader (0x0044D130)
// ---------------------------------------------------------------------------

/**
 * Asynchronous file reader owned by the Mobiclip player.
 *
 * `helper_S4FsReader_func_0034e028` receives the file object in r1, the sink
 * in r2 and leaves two 0x1000-byte heap regions in `g_S4FsReader`.
 */
struct S4FsReader {
    u32 field_00;                       // +0x00: first word of `strd r2,r3,[r4]` (0x0034e08c)
    u32 field_04;                       // +0x04: second word of that `strd`
    u32 field_08;                       // +0x08: first word of `strd r8,sb,[r4,#8]` (0x0034e090)
    u32 field_0c;                       // +0x0C: second word of that `strd`
    u64 file_size;                      // +0x10: `strd r0,r1,[r4,#0x10]` (0x0034e050)
    u32 field_18;                       // +0x18: `stm r2,{r1,ip}` with r2=r4+0x18 (0x0034e09c)
    u32 field_1c;                       // +0x1C: second word of that `stm`
    void* buffer;                       // +0x20: `str r0,[r4,#0x20]` (0x0034e078)
    u8  pad_24[0x0c];                   // +0x24..+0x30
    u8  thread[0x08];                   // +0x30: out pointer of 0x002B5A04 setup, passed as r0 (0x0034e1dc)
    void* file;                         // +0x38: `str r1,[r4,#0x38]` (0x0034e038)
    void* sink;                         // +0x3C: `str r5,[r4,#0x3c]` (0x0034e054)
    u32 lock;                           // +0x40: `add r0,r4,#0x40` to 0x002C3B00 (0x0034e098)
    u8  pad_44[0x08];                   // +0x44..+0x4C
    u32 event_a;                        // +0x4C: `str r1,[r5]` with r5=r4+0x4c (0x0034e0cc)
    u32 event_b;                        // +0x50: `str r1,[r5]` with r5=r4+0x50 (0x0034e100)
    u32* event_a_ptr;                   // +0x54: `add r0,r4,#0x4c` first word of `strd` (0x0034e114)
    u32* event_b_ptr;                   // +0x58: `add r1,r4,#0x50` second word of `strd` (0x0034e114)
};
static_assert(offsetof(S4FsReader, file_size) == 0x10);
static_assert(offsetof(S4FsReader, field_18) == 0x18);
static_assert(offsetof(S4FsReader, buffer) == 0x20);
static_assert(offsetof(S4FsReader, thread) == 0x30);
static_assert(offsetof(S4FsReader, file) == 0x38);
static_assert(offsetof(S4FsReader, sink) == 0x3C);
static_assert(offsetof(S4FsReader, lock) == 0x40);
static_assert(offsetof(S4FsReader, event_a) == 0x4C);
static_assert(offsetof(S4FsReader, event_b) == 0x50);
static_assert(offsetof(S4FsReader, event_a_ptr) == 0x54);
static_assert(offsetof(S4FsReader, event_b_ptr) == 0x58);

/** Global at 0x0044D130: work buffer and 0x18-byte heap header (0x0034e14c/0x0034e178). */
struct S4FsReaderGlobal {
    void* work_buffer;                  // +0x00: `str r0,[r5]` (0x0034e14c)
    void* heap;                         // +0x04: `str r0,[r5,#4]` (0x0034e178)
};
static_assert(offsetof(S4FsReaderGlobal, work_buffer) == 0x00);
static_assert(offsetof(S4FsReaderGlobal, heap) == 0x04);

extern S4FsReaderGlobal g_S4FsReader;                   // 0x0044D130

// ---------------------------------------------------------------------------
// helper_S4AudioDevice (0x0044D0F8)
// ---------------------------------------------------------------------------

/** Audio-device slot table; every field below is written by 0x0034E64C. */
struct S4AudioDevice {
    u32 field_00;                       // +0x00: not touched by this function
    void* device;                       // +0x04: `str r4,[r6,#4]` (0x0034e6c0)
    void* buffer;                       // +0x08: `str r0,[r6,#8]` (0x0034e6e8)
    void* heap_buffer;                  // +0x0C: `str r0,[r6,#0xc]` (0x0034e73c)
    void* heap;                         // +0x10: `str r0,[r6,#0x10]` (0x0034e76c)
    u32 count;                          // +0x14: `str r5,[r6,#0x14]` (0x0034e6bc)
    u32 field_18;                       // +0x18: `str r4,[r6,#0x18]` (0x0034e700)
    u32 field_1c;                       // +0x1C: `str r4,[r6,#0x1c]` (0x0034e704)
};
static_assert(offsetof(S4AudioDevice, device) == 0x04);
static_assert(offsetof(S4AudioDevice, buffer) == 0x08);
static_assert(offsetof(S4AudioDevice, heap_buffer) == 0x0C);
static_assert(offsetof(S4AudioDevice, heap) == 0x10);
static_assert(offsetof(S4AudioDevice, count) == 0x14);
static_assert(offsetof(S4AudioDevice, field_18) == 0x18);
static_assert(offsetof(S4AudioDevice, field_1c) == 0x1C);

extern S4AudioDevice g_S4AudioDevice;                   // 0x0044D0F8
extern u8 g_S4AudioThread[0x08];                        // 0x0044D128, r0 of 0x002BCE50 (0x0034e7d0)

// ---------------------------------------------------------------------------
// helper_S4Player (0x0044D158)
// ---------------------------------------------------------------------------

/**
 * Mobiclip player state.  `helper_S4Player_func_003516a8` only resets and
 * publishes the fields below; everything else is left as proven padding.
 */
struct S4Player {
    u32 lock;                           // +0x000: `mov r0,r4` to 0x002C3B00 (0x00351778)
    u32 field_04;                       // +0x004: not touched by this function
    u32 field_08;                       // +0x008: not touched by this function
    u32 field_0c;                       // +0x00C: `str r6,[r4,#0xc]` (0x003516f0)
    u8  flag_10;                        // +0x010: `strb r6,[r4,#0x10]` (0x00351788)
    u8  flag_11;                        // +0x011: `strb r6,[r4,#0x11]` (0x00351794)
    u8  pad_12[0x02];                   // +0x012..+0x14
    u32 source;                         // +0x014: `str ip,[r4,#0x14]` (0x003516e0)
    void* data;                         // +0x018: `str r2,[r4,#0x18]` (0x003516d4)
    u32 field_1c;                       // +0x01C: `str r6,[r4,#0x1c]` (0x00351750)
    u8  sync[0x110];                    // +0x020: 0x002C541C / 0x002C4244 operate here
    u32 field_130;                      // +0x130: `str ip,[r4,#0x130]` (0x00351744)
    u32 field_134;                      // +0x134: `str ip,[r4,#0x134]` (0x00351748)
    u32 field_138;                      // +0x138: not touched by this function
    u32 field_13c;                      // +0x13C: not touched by this function
    u32 field_140;                      // +0x140: `str ip,[r4,#0x140]` (0x00351754)
    u32 field_144;                      // +0x144: `stm lr,{r2,r8,sb}` with lr=r4+0x144 (0x00351764)
    u32 field_148;                      // +0x148: second word of that `stm`
    u32 field_14c;                      // +0x14C: third word of that `stm`
    u32 field_150;                      // +0x150: `stm lr,{r0,r1}` with lr=r4+0x150 (0x00351758)
    u32 field_154;                      // +0x154: second word of that `stm`
    u8  decoder[0x60];                  // +0x158: r0 of 0x0034EF48 (0x00351768)
    void* frame;                        // +0x1B8: `str r3,[r4,#0x1b8]` (0x003516dc)
    void* frame_arg;                    // +0x1BC: `stm r8,{r1,r7}` with r8=r4+0x1bc (0x003516e4)
    void* frame_arg2;                   // +0x1C0: second word of that `stm`
    u32 field_1c4;                      // +0x1C4: `str r6,[r4,#0x1c4]` (0x00351710)
    u8  pad_1c8[0x120];                 // +0x1C8..+0x2E8
    u32 field_2e8;                      // +0x2E8: `str r6,[r4,#0x2e8]` (0x00351708)
    u8  pad_2ec[0x180];                 // +0x2EC..+0x46C
    u32 field_46c;                      // +0x46C: `str r0,[r4,#0x46c]` r0=-1 (0x0035170c)
    u32 field_470;                      // +0x470: `str r0,[r4,#0x470]` r0=-1 (0x0035171c)
    u32 field_474;                      // +0x474: `str r6,[r4,#0x474]` (0x00351714)
    u32 field_478;                      // +0x478: `str r6,[r4,#0x478]` (0x00351720)
    u32 field_47c;                      // +0x47C: `str r6,[r4,#0x47c]` (0x00351718)
    u32 field_480;                      // +0x480: `str r6,[r4,#0x480]` (0x00351724)
    u32 field_484;                      // +0x484: `str r6,[r4,#0x484]` (0x00351704)
    u8  pad_488[0xc0];                  // +0x488..+0x548
    u32 field_548;                      // +0x548: `str r0,[r4,#0x548]` r0=-1 (0x00351700)
    u8  flag_54c;                       // +0x54C: `strb r6,[r4,#0x54c]` (0x00351740)
    u8  pad_54d[0x03];                  // +0x54D..+0x550
    u32 field_550;                      // +0x550: `str r6,[r4,#0x550]` (0x003516fc)
    u32 field_554;                      // +0x554: `str r6,[r4,#0x554]` (0x003516f8)
    u32 field_558;                      // +0x558: `str r6,[r4,#0x558]` (0x003516f4)
};
static_assert(offsetof(S4Player, lock) == 0x000);
static_assert(offsetof(S4Player, field_0c) == 0x00C);
static_assert(offsetof(S4Player, flag_10) == 0x010);
static_assert(offsetof(S4Player, source) == 0x014);
static_assert(offsetof(S4Player, data) == 0x018);
static_assert(offsetof(S4Player, sync) == 0x020);
static_assert(offsetof(S4Player, field_130) == 0x130);
static_assert(offsetof(S4Player, field_140) == 0x140);
static_assert(offsetof(S4Player, field_144) == 0x144);
static_assert(offsetof(S4Player, field_150) == 0x150);
static_assert(offsetof(S4Player, decoder) == 0x158);
static_assert(offsetof(S4Player, frame) == 0x1B8);
static_assert(offsetof(S4Player, frame_arg) == 0x1BC);
static_assert(offsetof(S4Player, frame_arg2) == 0x1C0);
static_assert(offsetof(S4Player, field_1c4) == 0x1C4);
static_assert(offsetof(S4Player, field_2e8) == 0x2E8);
static_assert(offsetof(S4Player, field_46c) == 0x46C);
static_assert(offsetof(S4Player, field_470) == 0x470);
static_assert(offsetof(S4Player, field_480) == 0x480);
static_assert(offsetof(S4Player, field_484) == 0x484);
static_assert(offsetof(S4Player, field_548) == 0x548);
static_assert(offsetof(S4Player, flag_54c) == 0x54C);
static_assert(offsetof(S4Player, field_550) == 0x550);
static_assert(offsetof(S4Player, field_558) == 0x558);
static_assert(sizeof(S4Player) == 0x55C);

/** Global at 0x0044D158: 0x2000-byte work buffer and heap header (0x003517c4/0x003517ec). */
struct S4PlayerGlobal {
    void* work_buffer;                  // +0x00: `str r0,[r7]` (0x003517c4)
    void* heap;                         // +0x04: `str r0,[r7,#4]` (0x003517ec)
};
static_assert(offsetof(S4PlayerGlobal, work_buffer) == 0x00);
static_assert(offsetof(S4PlayerGlobal, heap) == 0x04);

extern S4PlayerGlobal g_S4Player;                       // 0x0044D158

// ---------------------------------------------------------------------------
// Functions
// ---------------------------------------------------------------------------

// 0x0017FB6C (584 B): carve the six Mobiclip arenas, publish the nn callbacks
// and start the audio device.
void MobiclipCtrl_func_0017fb6c();

// 0x002EF664 (432 B): allocate and initialise one Mobiclip playback block.
MobiclipMoveNode* MobiclipCtrlProcess_func_002ef664(s32 movie_index, u8 flag);

// 0x0034E028 (520 B): initialise the asynchronous file-reader state.
u32 helper_S4FsReader_func_0034e028(S4FsReader* reader, void* file, void* sink);

// 0x0034E64C (476 B): initialise the audio device and its worker thread.
u32 helper_S4AudioDevice_func_0034e64c(void* device, u32 count,
                                       void* data, u32 size);

// 0x003516A8 (552 B): initialise a Mobiclip player instance.
u32 helper_S4Player_func_003516a8(S4Player* player, u32 source, void* data,
                                  void* frame, void* arg4, void* arg5);

} // namespace smt4::nn
