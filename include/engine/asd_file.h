#pragma once
#include <cstddef>
#include "types.h"
#include "engine/asd_symbols.h"

/**
 * Atlus AsdSDK file system, memory pool and save-file common plumbing.
 *
 * The fourteen functions reconstructed in `src/engine/asd_file.cpp` come from
 * four original translation units:
 *
 *   AsdFile        c:\SMT4\XRD686\AsdSDK\Source\Sys\File\AsdFile.cpp
 *   AsdLoadFile    c:\SMT4\XRD686\AsdSDK\Source\Sys\File\AsdLoadFile.cpp
 *   AsdMemory      c:\SMT4\XRD686\AsdSDK\Source\Sys\Mem\AsdMemory.cpp
 *   AsdSaveCommon  c:\SMT4\XRD686\AsdSDK\Source\Sys\Save\AsdSaveCommon.cpp
 *
 * Only the offsets actually touched by those fourteen functions are named.
 * Every field carries the instruction that proves it; unproven ranges stay
 * `pad_NN`.
 */

namespace smt4::engine {

// ---------------------------------------------------------------------------
// AsdFile (0x00465000)
// ---------------------------------------------------------------------------

/**
 * Two-word synchronisation object at `0x00465024`.
 *
 * `AsdFile_func_00113d58` passes it to `engine_func_002c3628` (wait) and
 * `engine_func_002c541c` (state store), which touch +0x00 and +0x04;
 * `engine_func_00138f5c` (lock) only touches +0x00.
 */
struct AsdFileSync {
    s32 state;                          // +0x00: `ldr r0,[r4]` (0x00138f64)
    u32 lock;                           // +0x04: `add r5,r4,#4` (0x00138f94)
};
static_assert(offsetof(AsdFileSync, lock) == 0x04);

/**
 * Queued asynchronous file request (exactly 0x144 bytes).
 *
 * `AsdFile_func_002b0434` allocates it, zeroes it and fills the head of the
 * object; `AsdFile_func_00113d58` drives it through its state machine.
 */
struct AsdFileRequest {
    s32 state;                          // +0x000: `str sb,[r5]` (0x002b0564); switch at 0x00113e60
    s32 pending;                        // +0x004: `stm r0,{r2,sb}` r2=1 (0x002b0590)
    s32 completed;                      // +0x008: second word of the same `stm` (0x002b0590)
    void* buffer;                       // +0x00C: `str r0,[r7,#0xc]` (0x00113fe0)
    u32 field_10;                       // +0x010: `ldr r0,[r7,#0x10]` (0x00114204)
    u32 field_14;                       // +0x014: zeroed by `str r5,[r5,#0x14]` (0x002b0574)
    s32 file_size;                      // +0x018: `str r0,[r7,#0x18]` (0x00113f70)
    u32 field_1c;                       // +0x01C: zeroed by the 0x144-byte memset
    u8  mode;                           // +0x020: `strb r6,[r5,#0x20]` (0x002b0568)
    u8  pad_21[0x03];                   // +0x021..+0x024
    u32 read_mode;                      // +0x024: `ldr r0,[r7,#0x24]` (0x00113f9c)
    u32 request_size;                   // +0x028: `ldr r0,[r7,#0x28]` (0x00113fc4)
    char path[0x100];                   // +0x02C: `add r6,r7,#0x2c` (0x00113edc)
    void* file;                         // +0x12C: `str r0,[r7,#0x12c]` (0x00113ec0)
    void* callback;                     // +0x130: `ldr r0,[r7,#0x130]` (0x00114134)
    void* callback_arg;                 // +0x134: `ldr r0,[r7,#0x134]` (0x00114170)
    void* cancel_callback;              // +0x138: `ldr r0,[r7,#0x138]` (0x00113df8)
    AsdFileRequest* next;               // +0x13C: `ldr r7,[r7,#0x13c]` (0x001142b4)
    AsdFileRequest* prev;               // +0x140: `str r0,[r5,#0x140]` (0x002b04d0)
};
static_assert(offsetof(AsdFileRequest, pending) == 0x004);
static_assert(offsetof(AsdFileRequest, completed) == 0x008);
static_assert(offsetof(AsdFileRequest, buffer) == 0x00C);
static_assert(offsetof(AsdFileRequest, file_size) == 0x018);
static_assert(offsetof(AsdFileRequest, mode) == 0x020);
static_assert(offsetof(AsdFileRequest, read_mode) == 0x024);
static_assert(offsetof(AsdFileRequest, path) == 0x02C);
static_assert(offsetof(AsdFileRequest, file) == 0x12C);
static_assert(offsetof(AsdFileRequest, callback) == 0x130);
static_assert(offsetof(AsdFileRequest, cancel_callback) == 0x138);
static_assert(offsetof(AsdFileRequest, next) == 0x13C);
static_assert(offsetof(AsdFileRequest, prev) == 0x140);
static_assert(sizeof(AsdFileRequest) == 0x144);

/**
 * Global AsdFile manager at `0x00465000`.
 *
 * `AsdFile_func_0010250c` creates the mutex at +0x10 and the synchronisation
 * object at +0x24; `AsdFile_func_0010d070` fills +0x14/+0x18 and spawns the
 * worker thread whose descriptor lives at +0x1C.
 */
struct AsdFileGlobal {
    u8  field_00;                       // +0x000: `strb r5,[r6]` (0x0010d088)
    u8  pad_01[0x03];                   // +0x001..+0x004
    u32 field_04;                       // +0x004: `str fp,[sb,#4]` fp=1 (0x00113ff0)
    void* rom_buffer;                   // +0x008: `str r0,[r6,#8]` (0x0010255c)
    AsdFileRequest* head;               // +0x00C: `ldr r7,[sb,#0xc]` (0x00113db4)
    u32 mutex;                          // +0x010: `str r1,[r4]` r4=r6+0x10 (0x001025a0)
    void* work_buffer;                  // +0x014: `str r0,[r6,#0x14]` (0x0010d0b0)
    void* heap;                         // +0x018: `str r0,[r6,#0x18]` (0x0010d0dc)
    u8  thread_desc[0x08];              // +0x01C: out pointer of 0x002bce50 (0x0010d110)
    AsdFileSync sync;                   // +0x024: `ldr r0,=0x00465024` (0x0010d158)
};
static_assert(offsetof(AsdFileGlobal, field_04) == 0x004);
static_assert(offsetof(AsdFileGlobal, rom_buffer) == 0x008);
static_assert(offsetof(AsdFileGlobal, head) == 0x00C);
static_assert(offsetof(AsdFileGlobal, mutex) == 0x010);
static_assert(offsetof(AsdFileGlobal, work_buffer) == 0x014);
static_assert(offsetof(AsdFileGlobal, heap) == 0x018);
static_assert(offsetof(AsdFileGlobal, thread_desc) == 0x01C);
static_assert(offsetof(AsdFileGlobal, sync) == 0x024);

extern AsdFileGlobal g_AsdFile;         // 0x00465000

// +0x00465040: when non-zero, `AsdLoadFile_func_002ae6c8` passes the name
// through unchanged instead of prefixing it with "rom:/".
extern u8 g_AsdLoadFileRawPath;         // 0x00465040

// ---------------------------------------------------------------------------
// AsdMemory (0x00465170)
// ---------------------------------------------------------------------------

/**
 * Heap block node used by the AsdMemory block lists (0x10 bytes).
 *
 * `AsdMemory_func_00144978` allocates these with `AsdMem_AllocAlign(...,0x10,1)`
 * and links them through +0x08/+0x0C; `engine_func_002c38d4` inserts them into
 * the ordered tree using +0x00 as the key.
 */
struct AsdMemoryBlock {
    u32 start;                          // +0x00: `stm r7,{r0,r6}` (0x00144a10)
    u32 size;                           // +0x04: second word of that `stm` (0x00144a10)
    AsdMemoryBlock* prev;               // +0x08: `ldrd r0,r1,[r4,#8]` (0x00144a5c)
    AsdMemoryBlock* next;               // +0x0C: second word of that `ldrd` (0x00144a5c)
};
static_assert(offsetof(AsdMemoryBlock, size) == 0x04);
static_assert(offsetof(AsdMemoryBlock, prev) == 0x08);
static_assert(offsetof(AsdMemoryBlock, next) == 0x0C);
static_assert(sizeof(AsdMemoryBlock) == 0x10);

/**
 * Ordered block tree (root/tail/count) used by `engine_func_002c38d4`.
 *
 * The tree header is embedded at +0x0C of the 0x20000/0x30000 region
 * descriptors built by `AsdMemory_func_0010376c` (0x00103930 / 0x001039a0).
 */
struct AsdMemoryBlockTree {
    void* root;                         // +0x00: `ldr r1,[r0]` (0x002c3938)
    void* tail;                         // +0x04: `streq r1,[r0,#4]` (0x002c3930)
    u32 count;                          // +0x08: `ldr r1,[r0,#8]` (0x002c3938)
};
static_assert(offsetof(AsdMemoryBlockTree, tail) == 0x04);
static_assert(offsetof(AsdMemoryBlockTree, count) == 0x08);
static_assert(sizeof(AsdMemoryBlockTree) == 0x0C);

/**
 * Region descriptor written at `0x004E4100` (+0x1C for the second region).
 *
 * `AsdMemory_func_0010376c` zeroes +0x00..+0x14, stores the region byte size at
 * +0x18 and inserts the free node through the tree header at +0x0C.
 */
struct AsdMemoryRegion {
    u32 field_00;                       // +0x00: `str r6,[r4]` (0x001038e4)
    u32 field_04;                       // +0x04: `str r6,[r4,#4]` (0x001038e8)
    u32 field_08;                       // +0x08: `str r6,[r4,#8]` (0x001038ec)
    AsdMemoryBlockTree tree;            // +0x0C: `add r0,r4,#0xc` (0x00103930)
    u32 size;                           // +0x18: `stm r2,{r6,sl}` (0x00103900)
};
static_assert(offsetof(AsdMemoryRegion, field_04) == 0x04);
static_assert(offsetof(AsdMemoryRegion, field_08) == 0x08);
static_assert(offsetof(AsdMemoryRegion, tree) == 0x0C);
static_assert(offsetof(AsdMemoryRegion, size) == 0x18);
static_assert(sizeof(AsdMemoryRegion) == 0x1C);

/**
 * Heap book-keeping object at `0x004E4100` is a plain array of the above;
 * the allocator state itself starts with the 0x18-byte block tree.
 */
struct AsdMemBlockHeap {
    AsdMemoryBlockTree tree;            // +0x00: `bl 0x002c38d4` with r0=heap (0x00144a44)
    AsdMemoryBlock* free_head;          // +0x0C: `ldr r4,[r0,#0xc]` (0x0014497c)
    AsdMemoryBlock* free_tail;          // +0x10: `streq r0,[r5,#0x10]` (0x00144a74)
    s32 free_count;                     // +0x14: `sub r0,r0,#1` (0x00144a88)
    u32 free_bytes;                     // +0x18: `sub r0,r0,r1` (0x00144a34)
};
static_assert(offsetof(AsdMemBlockHeap, free_head) == 0x0C);
static_assert(offsetof(AsdMemBlockHeap, free_tail) == 0x10);
static_assert(offsetof(AsdMemBlockHeap, free_count) == 0x14);
static_assert(offsetof(AsdMemBlockHeap, free_bytes) == 0x18);
static_assert(sizeof(AsdMemBlockHeap) == 0x1C);

/** Lock triple touched by `engine_func_002c3aa8` / `engine_func_002c3a24`. */
struct AsdMemoryLock {
    u32 field_00;                       // +0x00: `bl 0x00138f44` stores 1 (0x002c3b08)
    u32 owner;                          // +0x04: `ldr r1,[r4,#4]` (0x002c3ab4)
    u32 count;                          // +0x08: `ldr r0,[r4,#8]` (0x002c3ad0)
};
static_assert(offsetof(AsdMemoryLock, owner) == 0x04);
static_assert(offsetof(AsdMemoryLock, count) == 0x08);
static_assert(sizeof(AsdMemoryLock) == 0x0C);

/**
 * Primary AsdMemory heap descriptor reached through `g_AsdMemory.heap`.
 *
 * `AsdMemory_func_0010376c` fills +0x80..+0x100; the block pool at +0x88 is
 * initialised through `engine_func_002c3b1c` and guarded by the lock at +0xE0.
 */
struct AsdMemoryHeap {
    u8  pad_00[0x80];                   // +0x000..+0x080
    u32 heap_start;                     // +0x080: `str r0,[r1,#0x80]` (0x00103784)
    u32 heap_size;                      // +0x084: `str r0,[r2,#0x84]` (0x00103794)
    u8  block_pool[0x58];               // +0x088: `add r4,r0,#0x88` (0x001037ac)
    AsdMemoryLock lock;                 // +0x0E0: `add r4,r0,#0xe0` (0x001037e4)
    u32 region2_start;                  // +0x0EC: `str r0,[r1,#0xec]` (0x00103864)
    u32 region2_size;                   // +0x0F0: `stm r1,{r0,r2}` (0x00103880)
    u8  pad_f4[0x04];                   // +0x0F4..+0x0F8
    u32 region3_start;                  // +0x0F8: `str r0,[r1,#0xf8]` (0x00103890)
    u32 region3_size;                   // +0x0FC: `strd r0,r1,[ip,#0xfc]` (0x001038a8)
    u32 field_100;                      // +0x100: second word of that `strd` (0x001038a8)
};
static_assert(offsetof(AsdMemoryHeap, heap_start) == 0x080);
static_assert(offsetof(AsdMemoryHeap, heap_size) == 0x084);
static_assert(offsetof(AsdMemoryHeap, block_pool) == 0x088);
static_assert(offsetof(AsdMemoryHeap, lock) == 0x0E0);
static_assert(offsetof(AsdMemoryHeap, region2_start) == 0x0EC);
static_assert(offsetof(AsdMemoryHeap, region2_size) == 0x0F0);
static_assert(offsetof(AsdMemoryHeap, region3_start) == 0x0F8);
static_assert(offsetof(AsdMemoryHeap, region3_size) == 0x0FC);
static_assert(offsetof(AsdMemoryHeap, field_100) == 0x100);

/** Global AsdMemory manager at `0x00465170`. */
struct AsdMemoryGlobal {
    u8  field_00;                       // +0x00: `strb r0,[r7]` (0x00103a2c)
    u8  pad_01[0x03];                   // +0x01..+0x04
    AsdMemoryHeap* heap;                // +0x04: `ldr r1,[r7,#4]` (0x00103780)
    void* pool_100;                     // +0x08: `str r0,[r7,#8]` (0x001039e4)
    void* pool_20000;                   // +0x0C: `str r0,[r7,#0xc]` (0x00103a24)
    void* pool_30000;                   // +0x10: `str r0,[r7,#0x10]` (0x00103a6c)
    u32 block_handle;                   // +0x14: `str r5,[r7,#0x14]` (0x00103824)
    u32 block_handle_hi;                // +0x18: read by `ldrd r0,r1,[ip,#0x14]` (0x001038bc)
};
static_assert(offsetof(AsdMemoryGlobal, heap) == 0x04);
static_assert(offsetof(AsdMemoryGlobal, pool_100) == 0x08);
static_assert(offsetof(AsdMemoryGlobal, pool_20000) == 0x0C);
static_assert(offsetof(AsdMemoryGlobal, pool_30000) == 0x10);
static_assert(offsetof(AsdMemoryGlobal, block_handle) == 0x14);
static_assert(offsetof(AsdMemoryGlobal, block_handle_hi) == 0x18);

extern AsdMemoryGlobal g_AsdMemory;     // 0x00465170

// ---------------------------------------------------------------------------
// AsdFile functions
// ---------------------------------------------------------------------------

// 0x0010250c (296 B): one-time AsdFile start-up.
void AsdFile_func_0010250c();

// 0x0010d070 (272 B): allocate the worker heap and spawn the worker thread.
void AsdFile_func_0010d070();

// 0x00113d58 (1,564 B): asynchronous request worker loop.
void AsdFile_func_00113d58();

// 0x002b0434 (480 B): enqueue and initialise a request for `name`.
AsdFileRequest* AsdFile_func_002b0434(const char* name, u8 mode);

// ---------------------------------------------------------------------------
// AsdLoadFile functions
// ---------------------------------------------------------------------------

// 0x002ae6c8 (336 B): build a "rom:/"-qualified path and queue a load.
u32 AsdLoadFile_func_002ae6c8(const char* name, u32* out_status, u32 flags,
                              void* owner, f32 scale, u32 size);

// ---------------------------------------------------------------------------
// AsdMemory functions
// ---------------------------------------------------------------------------

// 0x0010376c (820 B): initialise the AsdMemory heap + region descriptors.
void AsdMemory_func_0010376c();

// 0x00144978 (320 B): carve `size` bytes out of the heap free list.
void* AsdMemory_func_00144978(AsdMemBlockHeap* heap, u32 size);

// 0x002c684c (112 B): operator-new style allocator from the 0x100 arena.
void* AsdMemory_func_002c684c(u32 size);

// 0x00262ac0 (104 B): operator-new style allocator from the 0x100 arena.
void* AsdMemory_func_00262ac0(u32 size);

// 0x00346d38 (120 B): pool allocator with an extra per-element count.
void* AsdMemory_func_00346d38(u32 size, u32 extra);

// 0x00348a1c (120 B): pool allocator with an extra per-element count.
void* AsdMemory_func_00348a1c(u32 size, u32 extra);

// 0x0034b3dc (120 B): 0x10000-arena variant of the pool allocator.
void* AsdMemory_func_0034b3dc(u32 size, u32 extra);

// ---------------------------------------------------------------------------
// AsdSaveCommon functions
// ---------------------------------------------------------------------------

// 0x0021041c (204 B): read a 0x80-byte header plus payload via 0x002f5348.
u32 AsdSaveCommon_func_0021041c(u32 device, u32 file, void* header,
                                void* payload, u32 payload_size);

// 0x002104e8 (268 B): write a 0x80-byte header plus payload via 0x002f5584.
u32 AsdSaveCommon_func_002104e8(u32 device, u32 file, const void* header,
                                const void* payload, u32 payload_size);

} // namespace smt4::engine
