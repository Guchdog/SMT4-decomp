#pragma once
#include <cstddef>
#include "types.h"
#include "engine/asd_model.h"

/**
 * Event/resource runtime container built by `func_0011d9fc`.
 *
 * The routine takes a resource-count snapshot plus the task/allocator context
 * that owns every allocation ("task ownership"): each array is a
 * `count * 4`-byte block requested from `owner->vtable[2](owner, size, 0x20)`
 * and is released through `owner->vtable[3](owner, begin)` (see the inlined
 * per-member construction and the teardown at 0x0011EF88).
 *
 * The destination object is allocated from the same context with
 * `vtable[2](owner, 0xF8, 4)` (0x0011EA50..0x0011EA70), so every embedded
 * vector keeps `owner` in its `ctx` slot.
 *
 * Original position in the binary: the routine occupies 0x0011D9FC..0x0011F504
 * and ends with its own literal-pool word at 0x0011F500 (the class-table
 * pointer 0x00420D30), not with the start of the next routine.  The texture
 * converter blocks are later, at 0x00170D70 and above.
 */

namespace smt4::engine {

/**
 * Input snapshot read by `func_0011d9fc`.
 *
 * `active` gates only the fifteen array allocations: when it is zero the
 * output table is still allocated, but every embedded vector stays in its
 * empty inline form (`begin = end = 0`, `capacity = 0x40000000`).
 *
 * Each count is scaled by four at the allocation site (`lsl r1,r1,#2`,
 * 0x0011DC54 and every repeat).  The fields are declared in ascending offset
 * order; the comments record which output vector each count feeds, because
 * the construction order in the listing is not the declaration order of the
 * output object.
 */
struct EventResourceCounts {
    u8  active;                         // +0x00: `ldrb r0,[r5]` (0x0011DC1C)
    u8  pad_01[0x03];                   // +0x01..+0x04
    u32 count_04;                       // +0x04: `ldr r1,[r5,#4]`  (0x0011DC30) -> array 0
    u32 count_08;                       // +0x08: `ldr r1,[r5,#8]`  (0x0011DD20) -> array 1
    u32 count_0c;                       // +0x0C: `ldr r1,[r5,#0xc]` (0x0011DE14) -> array 2
    u32 count_10;                       // +0x10: `ldr r1,[r5,#0x10]` (0x0011DF08) -> array 3
    u32 count_14;                       // +0x14: `ldr r1,[r5,#0x14]` (0x0011E4B4) -> array 4
    u32 count_18;                       // +0x18: `ldr r1,[r5,#0x18]` (0x0011DFF8) -> array 6
    u32 count_1c;                       // +0x1C: `ldr r1,[r5,#0x1c]` (0x0011E0E8) -> array 7
    u32 count_20;                       // +0x20: `ldr r1,[r5,#0x20]` (0x0011E1D8) -> array 8
    u32 count_24;                       // +0x24: `ldr r1,[r5,#0x24]` (0x0011E2CC) -> array 9
    u32 count_28;                       // +0x28: `ldr r1,[r5,#0x28]` (0x0011E3C4) -> array 10
    u32 count_2c;                       // +0x2C: `ldr r1,[r5,#0x2c]` (0x0011E5A4) -> array 5
    u32 count_30;                       // +0x30: `ldr r1,[r5,#0x30]` (0x0011E698) -> array 11
    u32 count_34;                       // +0x34: `ldr r1,[r5,#0x34]` (0x0011E784) -> array 12
    u32 count_38;                       // +0x38: `ldr r1,[r5,#0x38]` (0x0011E878) -> array 13
    u32 count_3c;                       // +0x3C: `ldr r1,[r5,#0x3c]` (0x0011E96C) -> array 14
};
static_assert(offsetof(EventResourceCounts, active) == 0x00);
static_assert(offsetof(EventResourceCounts, count_04) == 0x04);
static_assert(offsetof(EventResourceCounts, count_14) == 0x14);
static_assert(offsetof(EventResourceCounts, count_2c) == 0x2C);
static_assert(offsetof(EventResourceCounts, count_3c) == 0x3C);
static_assert(sizeof(EventResourceCounts) == 0x40);

/**
 * 0xF8-byte resource table returned by `func_0011d9fc`.
 *
 * +0x00 is the class/table address 0x00420D30 (`ldr r3,[pc,#0x730]`,
 * 0x0011EDC8; literal pool entry 0x0011F500).  +0x04 is the owning
 * task/allocator context (`str r3,[r0,#4]`, 0x0011EDC4, where r3 was copied
 * from the incoming r1 at 0x0011EB18).
 *
 * The remaining 0xF0 bytes are fifteen `AsdPtrVector` members written one
 * after another: array 0 at +0x08, array 14 at +0xE8.  The final stores are
 * 0x0011EF60..0x0011EF80 for array 14, ending exactly at +0xF8.
 */
struct EventResourceTable {
    const void* vtable;                 // +0x00: 0x00420D30 (0x0011EDC8/0x0011EDCC)
    void* owner;                        // +0x04: `str r3,[r0,#4]` (0x0011EDC4)
    AsdPtrVector arrays[15];            // +0x08: 0x0011EDD0..0x0011EF80
};
static_assert(offsetof(EventResourceTable, vtable) == 0x00);
static_assert(offsetof(EventResourceTable, owner) == 0x04);
static_assert(offsetof(EventResourceTable, arrays) == 0x08);
static_assert(sizeof(EventResourceTable) == 0xF8);

/**
 * Event/resource runtime constructor (0x0011D9FC, 6,920 B).
 *
 * `func_0011d9fc` returns the new table, or null when the 0xF8-byte
 * allocation fails; in that case the fifteen already-built arrays are
 * released through their owning context before returning.
 */
EventResourceTable* func_0011d9fc(const EventResourceCounts* counts, void* owner);

} // namespace smt4::engine
