#pragma once
#include <cstddef>
#include "types.h"

/**
 * Add-on content (AOC) runtime.
 *
 * The ten reconstructed functions come from seven original translation units:
 *
 *   aocFileLoad      c:\SMT4\XRD686\sdds4\program\addon\sys\aocFileLoad.cpp
 *   aocMain          c:\SMT4\XRD686\sdds4\program\addon\aocMain.cpp
 *   aocBootProcess   c:\SMT4\XRD686\sdds4\program\addon\aocBootProcess.cpp
 *   aocApplication   c:\SMT4\XRD686\sdds4\program\addon\aocApplication.cpp
 *   aocFileContent   c:\SMT4\XRD686\sdds4\program\addon\sys\aocFileContent.cpp
 *   aocTexCtrl       c:\SMT4\XRD686\sdds4\program\addon\sys\aocTexCtrl.cpp
 *
 * Only the offsets actually touched by those functions are named.  Every
 * field carries the instruction that proves it; unproven ranges stay `pad_NN`.
 */

namespace smt4::engine {

// ---------------------------------------------------------------------------
// aocFileLoad (0x0015C728)
// ---------------------------------------------------------------------------

/**
 * Notification object reached through `AocFileLoadJob::notify`.
 *
 * `+0x08` receives the loaded size and `+0x0D` is set to 1 on completion
 * (0x0015CD18..0x0015CD24).
 */
struct AocFileLoadNotify {
    u8  pad_00[0x08];                   // +0x00..+0x08
    u32 size;                           // +0x08: `str r0,[r1,#8]` (0x0015cd24)
    u8  pad_0c[0x01];                   // +0x0C
    u8  ready;                          // +0x0D: `strb sb,[r0,#0xd]` (0x0015cd18)
};
static_assert(offsetof(AocFileLoadNotify, size) == 0x08);
static_assert(offsetof(AocFileLoadNotify, ready) == 0x0D);

/**
 * Load request consumed by `aocFileLoad_func_0015c728`.
 *
 * `state` selects the start / asynchronous / cancelled phases; `flags`
 * mirrors the AsdLoadFile flag word and decides whether the result goes to a
 * caller pointer or a callback.
 */
struct AocFileLoadJob {
    u32 field_00;                       // +0x00: not touched by this function
    u32 flags;                          // +0x04: `tst r0,#2` (0x0015c80c)
    u8  state;                          // +0x08: switch at 0x0015c790, stores at 0x0015c814
    u8  pad_09[0x0b];                   // +0x09..+0x14
    void* buffer;                       // +0x14: `str r0,[r4,#0x14]` (0x0015ca7c)
    u32* out;                           // +0x18: `ldr r1,[r4,#0x18]` (0x0015cde0)
    void (*callback)(void*, u32, u32);  // +0x1C: `ldr r3,[r4,#0x1c]` then `blx r3` (0x0015cd00)
    u32 callback_arg0;                  // +0x20: `ldr r0,[r4,#0x20]` (0x0015cdd4)
    u32 size;                           // +0x24: `str r0,[r4,#0x24]` (0x0015ca2c)
    u32 mode;                           // +0x28: compare with 0x10/1/0x11 (0x0015ca38..0x0015ca4c)
    u32 user;                           // +0x2C: `ldr r0,[r4,#0x2c]` (0x0015ca60)
    char path[0x40];                    // +0x30: r7 of MbrLen loop (0x0015c87c)
    char name[0x40];                    // +0x70: `add r0,r4,#0x70` (0x0015cde8)
    u32 field_b0;                       // +0xB0: not touched by this function
    AocFileLoadNotify* notify;          // +0xB4: `ldr r0,[r4,#0xb4]` (0x0015cd08)
};
static_assert(offsetof(AocFileLoadJob, flags) == 0x04);
static_assert(offsetof(AocFileLoadJob, state) == 0x08);
static_assert(offsetof(AocFileLoadJob, buffer) == 0x14);
static_assert(offsetof(AocFileLoadJob, out) == 0x18);
static_assert(offsetof(AocFileLoadJob, callback) == 0x1C);
static_assert(offsetof(AocFileLoadJob, callback_arg0) == 0x20);
static_assert(offsetof(AocFileLoadJob, size) == 0x24);
static_assert(offsetof(AocFileLoadJob, mode) == 0x28);
static_assert(offsetof(AocFileLoadJob, user) == 0x2C);
static_assert(offsetof(AocFileLoadJob, path) == 0x30);
static_assert(offsetof(AocFileLoadJob, name) == 0x70);
static_assert(offsetof(AocFileLoadJob, notify) == 0xB4);
// 0x00158B44..0x00158B54: the per-job stride is
// `(7*i + (i << 4)) << 3` = i * 0xB8.
static_assert(sizeof(AocFileLoadJob) == 0xB8);

/**
 * Caller context.  `aocFileLoad` reads one byte at `+0x450C`
 * (`add r0,r0,#0x4400; add r0,r0,#0x10c; ldrb`, 0x0015cbe4).
 */
struct AocLoadContext {
    u8  pad_00[0x450C];                 // +0x0000..+0x450C
    u8  initialized;                    // +0x450C: `ldrb r0,[r0]` (0x0015cbf0)
};
static_assert(offsetof(AocLoadContext, initialized) == 0x450C);

/** File object built on the stack; same layout as AsdFileObject (0x0015C87C..0x0015C890). */
struct AocFileObject {
    void** vtable;                      // +0x00: `str r2,[sp,#8]` (0x0015c884)
    u32 handle;                         // +0x04: `str r0,[sp,#0xc]` region (0x0015c8f8)
    u32 field_08;                       // +0x08: zeroed (0x0015c90c)
    u32 field_0c;                       // +0x0C: zeroed (0x0015c904)
    u32 field_10;                       // +0x10: zeroed (0x0015c908)
    u32 field_14;                       // +0x14: zeroed by the 0x18-byte clear
};
static_assert(offsetof(AocFileObject, handle) == 0x04);
static_assert(sizeof(AocFileObject) == 0x18);

/** 0x00420870 vtable table entry; the MSVC virtual-base store uses `vtable[-0x30]`. */
struct AocFileVTableSlot {
    void** vtable;                      // +0x00: `ldr r2,[r0]` (0x0015c878)
    u32 field_04;                       // +0x04
    u32 field_08;                       // +0x08
    void* self;                         // +0x0C: `ldr r0,[r0,#0xc]` (0x0015c88c)
};
static_assert(offsetof(AocFileVTableSlot, self) == 0x0C);

// 0x0015C728 (2,220 B): start / advance / cancel one add-on file load.
void aocFileLoad_func_0015c728(AocLoadContext* context, AocFileLoadJob* job);

// ---------------------------------------------------------------------------
// aocMain (0x00433048) and aocBootProcess (0x00432FE0)
// ---------------------------------------------------------------------------

/** Global aocMain state allocated by 0x001B0B00 (0x20 bytes). */
struct AocMain {
    void* main_task;                    // +0x00: `str r0,[r4]` (0x001b0b9c)
    u8  pad_04[0x08];                   // +0x04..+0x0C
    void* draw_task;                    // +0x0C: `str r0,[r4,#0xc]` (0x001b0c18)
    u8  pad_10[0x08];                   // +0x10..+0x18
    u8  flag_18;                        // +0x18: `strb r6,[r0,#0x18]` (0x001b0b48)
    u8  flag_19;                        // +0x19: `strb r6,[r0,#0x19]` / `strb r8` (0x001b0b4c)
    u8  flag_1a;                        // +0x1A: `strb r6,[r0,#0x1a]` (0x001b0b54)
    u8  pad_1b[0x01];                   // +0x1B
    u32 field_1c;                       // +0x1C: `str r6,[r0,#0x1c]` (0x001b0b50)
};
static_assert(offsetof(AocMain, main_task) == 0x00);
static_assert(offsetof(AocMain, draw_task) == 0x0C);
static_assert(offsetof(AocMain, flag_18) == 0x18);
static_assert(offsetof(AocMain, flag_19) == 0x19);
static_assert(offsetof(AocMain, flag_1a) == 0x1A);
static_assert(offsetof(AocMain, field_1c) == 0x1C);
static_assert(sizeof(AocMain) == 0x20);

extern AocMain* g_AocMain;              // 0x00433048: `str r0,[r7]` (0x001b0b44)

/** Global aocBootProcess state allocated by 0x00224AE0 (0x5F4 bytes). */
struct AocBootProcess {
    void* task;                         // +0x000: `str r0,[r1]` (0x00224b70)
    u32 field_04;                       // +0x004: `str r5,[r6,#4]` (0x00224b28)
    u8  flag_08;                        // +0x008: `strb r5,[r0,#8]` (0x00224b2c)
    u8  flag_09;                        // +0x009: `strb r5,[r0,#9]` (0x00224b34)
    u8  pad_0a[0x02];                   // +0x00A..+0x00C
    u8  calc[0x5e4];                    // +0x00C: r0 of 0x002BAACC (0x00224b38)
    u32 field_5f0;                      // +0x5F0: `str r5,[r4,#0x5f0]` (0x00224b44)
};
static_assert(offsetof(AocBootProcess, task) == 0x000);
static_assert(offsetof(AocBootProcess, field_04) == 0x004);
static_assert(offsetof(AocBootProcess, flag_08) == 0x008);
static_assert(offsetof(AocBootProcess, flag_09) == 0x009);
static_assert(offsetof(AocBootProcess, calc) == 0x00C);
static_assert(offsetof(AocBootProcess, field_5f0) == 0x5F0);
static_assert(sizeof(AocBootProcess) == 0x5F4);

/** Global at 0x00432FE0: live process pointer and a handle word. */
struct AocBootProcessGlobal {
    AocBootProcess* process;            // +0x00: `ldr r0,[r6]` (0x00224aec)
    u32 handle;                         // +0x04: `str r5,[r6,#4]` (0x00224b28)
};
static_assert(offsetof(AocBootProcessGlobal, process) == 0x00);
static_assert(offsetof(AocBootProcessGlobal, handle) == 0x04);

extern AocBootProcessGlobal g_AocBootProcess;   // 0x00432FE0

/** Shared application object at 0x00432FC8; only +0x98 and +0x754 are observed. */
struct AocAppletState {
    u8  pad_00[0x98];                   // +0x000..+0x098
    u8  field_98;                       // +0x098: `add r0,r0,#0x98` (0x0015c7d4)
    u8  pad_99[0x754 - 0x99];           // +0x099..+0x754
    u32 flags_754;                      // +0x754: `ldr r1,[r0,#0x754]` (0x0015c7f0)
};
static_assert(offsetof(AocAppletState, field_98) == 0x098);
static_assert(offsetof(AocAppletState, flags_754) == 0x754);

extern AocAppletState* g_AocAppletState;        // 0x00432FC8: `ldr r0,[r0]` (0x0015c7ec)

// 0x001B0B00 (408 B): create the AOC main/draw tasks; returns the retained
// `AOCDrawDown` child (`r0` at 0x001B0C18).
void* aocMain_func_001b0b00(u32 mode);

// 0x00224AE0 (276 B): create the boot-time AOC calculation task; returns the
// task pointer loaded from `g_AocBootProcess.process` (0x00224B88).
void* aocBootProcess_func_00224ae0();

// ---------------------------------------------------------------------------
// aocApplication (0x0038B384 / 0x0038B510)
// ---------------------------------------------------------------------------

/**
 * Add-on application object.  The two functions only touch the source handle
 * at +0x80 and the texture/archive pairs at +0x5A8..+0x5B4.
 */
struct AocApplication {
    u8  pad_00[0x80];                   // +0x000..+0x080
    void* source_handle;                // +0x080: `ldr r1,[r4,#0x80]` (0x0038b418)
    u8  pad_84[0x5a8 - 0x84];           // +0x084..+0x5A8
    void* texture_handle;               // +0x5A8: `ldr r0,[r0,#0x5a8]` (0x0038b390)
    void* texture_buffer;               // +0x5AC: `str r0,[r4,#0x5ac]` (0x0038b3f0)
    void* archive_handle;               // +0x5B0: `ldr r0,[r0,#0x5b0]` (0x0038b51c)
    void* archive_buffer;               // +0x5B4: `str r0,[r4,#0x5b4]` (0x0038b57c)
};
static_assert(offsetof(AocApplication, source_handle) == 0x080);
static_assert(offsetof(AocApplication, texture_handle) == 0x5A8);
static_assert(offsetof(AocApplication, texture_buffer) == 0x5AC);
static_assert(offsetof(AocApplication, archive_handle) == 0x5B0);
static_assert(offsetof(AocApplication, archive_buffer) == 0x5B4);

// 0x0038B384 (236 B): rebuild the texture archive buffer and handle.
void aocApplication_func_0038b384(AocApplication* app);

// 0x0038B510 (240 B): rebuild the sound archive buffer and handle.
void aocApplication_func_0038b510(AocApplication* app);

// ---------------------------------------------------------------------------
// aocFileContent (0x0038BD00)
// ---------------------------------------------------------------------------

/**
 * Mount request for one add-on file archive.
 *
 * `+0x20` is the read buffer, `+0x24` the "aoc%d:" mount name and `+0x34`
 * the buffer size.
 */
struct AocFileContent {
    u8  pad_00[0x20];                   // +0x000..+0x020
    void* buffer;                       // +0x020: `str r0,[r4,#0x20]` (0x0038be2c)
    char mount[0x10];                   // +0x024: `add r0,r4,#0x24` to UiText_Format (0x0038be40)
    u32 size;                           // +0x034: `ldr r3,[r4,#0x34]` (0x0038be1c)
};
static_assert(offsetof(AocFileContent, buffer) == 0x20);
static_assert(offsetof(AocFileContent, mount) == 0x24);
static_assert(offsetof(AocFileContent, size) == 0x34);

/** Status/result pair filled by `aocFileContent_func_0038bd00` (0x2BB09C object - 4). */
struct AocFileContentState {
    u8  status;                         // +0x00: `strb r0,[r5]` (0x0038bd30)
    u8  pad_01[0x03];                   // +0x01..+0x04
    u32 result[2];                      // +0x04: `strd r0,r1,[r5,#4]` (0x0038bd5c)
    u32 field_0c;                       // +0x0C: `str r7,[r0,#8]` with r0=state+4 (0x0038bd3c)
    u32 field_10;                       // +0x10: `str r7,[r0,#0xc]` with r0=state+4 (0x0038bd44)
};
static_assert(offsetof(AocFileContentState, result) == 0x04);
static_assert(offsetof(AocFileContentState, field_0c) == 0x0C);
static_assert(offsetof(AocFileContentState, field_10) == 0x10);
static_assert(sizeof(AocFileContentState) == 0x14);

// 0x0038BD00 (408 B): mount add-on archive `index` and report its state.
void aocFileContent_func_0038bd00(AocFileContentState* state,
                                  AocFileContent* content, u32 index);

// ---------------------------------------------------------------------------
// aocTexCtrl (0x00234CA8 / 0x002A465C / 0x003936E8 / 0x00393838)
// ---------------------------------------------------------------------------

/**
 * Texture-control context.  `source` points at the on-disk block table and
 * `state` at the 0x18-byte runtime object allocated by 0x00234CA8.
 */
struct AocTexCtrlState;
struct AocTexListEntry;

struct AocTexCtrl {
    u8* source;                         // +0x00: `ldr r4,[r0]` (0x003936f0)
    AocTexCtrlState* state;             // +0x04: `ldr r0,[r0,#4]` then `str r5,[r0]` (0x00393824)
};
static_assert(offsetof(AocTexCtrl, source) == 0x00);
static_assert(offsetof(AocTexCtrl, state) == 0x04);

/**
 * Runtime texture-control state.
 *
 * 0x00234CA8 allocates 0x18 bytes and zeroes all six words, but only the
 * first two are ever used: `block` (the 0x2C output descriptor built by
 * 0x003936E8) and `list` (the 0x14-byte list built by 0x00393838).
 */
struct AocTexCtrlState {
    void* block;                        // +0x00: `str r5,[r0]` (0x00393828)
    AocTexListEntry* list;              // +0x04: `streq r4,[r1,#4]` (0x003939a0)
};
static_assert(offsetof(AocTexCtrlState, block) == 0x00);
static_assert(offsetof(AocTexCtrlState, list) == 0x04);
static_assert(sizeof(AocTexCtrlState) == 0x08);

/** 0x2C output descriptor allocated by 0x003936E8 via 0x002B76E8. */
struct AocTexOutput {
    void* nodes;                        // +0x00: `str r0,[r5]` (0x003937e8)
    void* header;                       // +0x04: `str r4,[r5,#4]` (0x0039381c)
    void* header_dup;                   // +0x08: `str r4,[r5,#8]` (0x00393820)
    u8  pad_0c[0x20];                   // +0x0C..+0x2C
};
static_assert(offsetof(AocTexOutput, nodes) == 0x00);
static_assert(offsetof(AocTexOutput, header) == 0x04);
static_assert(offsetof(AocTexOutput, header_dup) == 0x08);
static_assert(sizeof(AocTexOutput) == 0x2C);

/** 0x20-byte render node allocated per entry by 0x003936E8. */
struct AocTexOutputNode {
    void* owner;                        // +0x00: `stm r0,{r5,r6}` (0x00393800)
    void* source;                       // +0x04: second word of that `stm`
    u8  pad_08[0x18];                   // +0x08..+0x20
};
static_assert(offsetof(AocTexOutputNode, source) == 0x04);
static_assert(sizeof(AocTexOutputNode) == 0x20);

/** 0x14-byte texture-control list entry built by 0x00393838. */
struct AocTexListEntry {
    u32 value;                          // +0x00: `ldrb r1,[r5]` then `str r1,[r0]` (0x00393918)
    u32 count;                          // +0x04: `ldrb r1,[r5,#4]` then `str r1,[r0,#4]` (0x00393924)
    u8  type;                           // +0x08: `ldrb r1,[r5,#8]` / `strb r1,[r0,#8]` (0x0039392c)
    u8  pad_09[0x03];                   // +0x09..+0x0C
    void* data;                         // +0x0C: `str r0,[r4,#0xc]` (0x00393964)
    AocTexListEntry* next;              // +0x10: `strne r4,[r7,#0x10]` (0x003939a8)
};
static_assert(offsetof(AocTexListEntry, count) == 0x04);
static_assert(offsetof(AocTexListEntry, type) == 0x08);
static_assert(offsetof(AocTexListEntry, data) == 0x0C);
static_assert(offsetof(AocTexListEntry, next) == 0x10);
static_assert(sizeof(AocTexListEntry) == 0x14);

/** Header block read by 0x003936E8; four parallel arrays described by DWORD offsets. */
struct AocTexBlock {
    u8  pad_00[0x14];                   // +0x00..+0x14
    u32 base_offset;                    // +0x14: `ldr r0,[r4,#0x14]` (0x00393700)
    u8  pad_18[0x04];                   // +0x18..+0x1C
    u32 entry_offset;                   // +0x1C: `ldr r2,[r4,#0x1c]` (0x00393704)
    s32 entry_count;                    // +0x20: `ldr ip,[r4,#0x20]` / `cmp` (0x00393718)
    u32 stream_offset;                  // +0x24: `ldr r6,[r4,#0x24]` (0x0039370c)
    s32 stream_count;                   // +0x28: `ldr ip,[r4,#0x28]` (0x0039375c)
    u32 stream_data_offset;             // +0x2C: `ldr r3,[r4,#0x2c]` (0x00393708)
};
static_assert(offsetof(AocTexBlock, base_offset) == 0x14);
static_assert(offsetof(AocTexBlock, entry_offset) == 0x1C);
static_assert(offsetof(AocTexBlock, entry_count) == 0x20);
static_assert(offsetof(AocTexBlock, stream_offset) == 0x24);
static_assert(offsetof(AocTexBlock, stream_count) == 0x28);
static_assert(offsetof(AocTexBlock, stream_data_offset) == 0x2C);

/** TMSprite header: high nibble 0x10/0x20/0x30 selects the upload routine. */
struct AocTMSpr {
    u8 type;                            // +0x00: `ldrb r0,[r0]`; `and r4,r0,#0xf0` (0x002a466c)
};
static_assert(offsetof(AocTMSpr, type) == 0x00);

// 0x00234CA8 (164 B): lazily allocate the 0x18-byte texture-control state.
void aocTexCtrl_func_00234ca8(AocTexCtrl* ctrl);

// 0x002A465C (460 B): upload a TMSprite into a work buffer and free it.
void* aocTexCtrl_func_002a465c(AocTMSpr* sprite, u32 flags, u32 size);

// 0x003936E8 (336 B): build the output descriptor from the on-disk table.
u32 aocTexCtrl_func_003936e8(AocTexCtrl* ctrl);

// 0x00393838 (456 B): build the texture-control list from a source block.
void aocTexCtrl_func_00393838(AocTexCtrl* ctrl, void** source);

} // namespace smt4::engine
