#include "engine/event_runtime.h"

namespace smt4::engine {
namespace {

// Literal pool word at 0x0011F500: the table installed at output +0x00.
constexpr u32 kEventResourceTableAddress = 0x00420D30u;

// Empty inline capacity marker.  The empty vectors built by the prologue use
// `capacity = 0x40000000` (`orr r1,r1,#0x40000000`, 0x0011DA34 and repeats);
// moving a vector out keeps only these two tag bits
// (`and r2,r2,#0xc0000000`, 0x0011EAC8..0x0011EAD8 and repeats).
constexpr u32 kVectorInlineCapacity = 0x40000000u;
constexpr u32 kVectorCapacityMask = 0xC0000000u;

using EventAllocFn = void* (*)(void* owner, u32 size, u32 align);
using EventReleaseFn = void (*)(void* owner, void* block);

// `ldr r2,[owner]; ldr r3,[r2,#8]; blx r3` with (r0,r1,r2) =
// (owner, size, align): the allocator slot proved by AsdPtrVector_Grow
// (0x002AF568..0x002AF578) and by 0x0011DC50..0x0011DC64 here.
void* OwnerAllocate(void* owner, u32 size, u32 align) {
    void** vtable = *reinterpret_cast<void***>(owner);
    return reinterpret_cast<EventAllocFn>(vtable[2])(owner, size, align);
}

// `ldr r2,[owner]; ldr r2,[r2,#0xc]; blx r2` with (r0,r1) =
// (owner, block): the release slot also used by AsdPtrVector_Destroy
// (0x002AF5D0..0x002AF5DC).
void OwnerRelease(void* owner, void* block) {
    if (owner == nullptr || block == nullptr) {
        return;
    }
    void** vtable = *reinterpret_cast<void***>(owner);
    reinterpret_cast<EventReleaseFn>(vtable[3])(owner, block);
}

// One inlined member construction (0x0011DC28..0x0011DD14 and its fourteen
// repeats).  The temporary starts as `{owner, 0, 0, count}`; when the count
// is non-zero a `count * 4` block at alignment 0x20 is attached to both
// begin and end, and the capacity word is `count & 0x3FFFFFFF`
// (`and`/`orr`/`bic` at 0x0011DC88..0x0011DC94 and repeats).  The temporary
// is then swapped into the member and the previous (always empty) storage is
// released, which performs no call because its begin is null.
AsdPtrVector CreateArray(void* owner, u32 count) {
    AsdPtrVector vec{};
    vec.ctx = owner;
    vec.capacity = count & ~kVectorCapacityMask;
    if (count != 0) {
        void** block = static_cast<void**>(OwnerAllocate(owner, count * 4, 0x20));
        vec.begin = block;
        vec.end = block;
    }
    return vec;
}

// Teardown at 0x0011EF88..0x0011F4F0.  The earlier 0x0011EF88 pass guards on
// the "moved" words at sp+0x26C..0x27C and on ip; the build clears all of
// them to zero (0x0011EDE4..0x0011EF5C) and the failed-allocation path enters
// with ip already zero (0x0011EA68), so that pass never calls.  In the
// successful path every member has already been moved out
// (`begin = end = 0`), so the 0x0011F21C pass also performs no call; on the
// failed 0xF8-byte allocation it releases the fifteen live blocks.
void ReleaseArrays(AsdPtrVector* arrays) {
    for (s32 i = 14; i >= 0; --i) {
        if (arrays[i].ctx != nullptr && arrays[i].begin != nullptr) {
            OwnerRelease(arrays[i].ctx, arrays[i].begin);
        }
    }
}

} // namespace

// ---------------------------------------------------------------------------
// 0x0011D9FC -- event/resource table constructor.
//
// Reads a count snapshot (`EventResourceCounts`) and produces a 0xF8-byte
// table whose +0x00 word is the 0x00420D30 class/table pointer and whose
// +0x08..+0xF8 range holds fifteen pointer arrays.  Every array is allocated
// from the task/allocator context passed in r1 and keeps that context in its
// `ctx` slot, so the table owns the arrays through the task that created it.
//
// Inputs are byte `[r0]` (allocation gate) plus the fifteen word counts at
// r0+0x04..r0+0x3C; see EventResourceCounts for the per-field mapping.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0011d9fc, 6920)
EventResourceTable* func_0011d9fc(const EventResourceCounts* counts, void* owner) {
    // 0x0011DA14..0x0011DC18: fifteen empty inline vectors
    // `{owner, 0, 0, 0x40000000}`.
    AsdPtrVector arrays[15];
    for (u32 i = 0; i < 15; ++i) {
        arrays[i].ctx = owner;
        arrays[i].begin = nullptr;
        arrays[i].end = nullptr;
        arrays[i].capacity = kVectorInlineCapacity;
    }

    // 0x0011DC1C..0x0011DC24: byte 0 gates all fifteen constructions.
    if (counts->active != 0) {
        // Construction order follows the listing, not the output layout:
        // array 4 and array 5 are fed by +0x14 and +0x2C before +0x18.
        arrays[0] = CreateArray(owner, counts->count_04);    // 0x0011DC28
        arrays[1] = CreateArray(owner, counts->count_08);    // 0x0011DD18
        arrays[2] = CreateArray(owner, counts->count_0c);    // 0x0011DE0C
        arrays[3] = CreateArray(owner, counts->count_10);    // 0x0011DF00
        arrays[4] = CreateArray(owner, counts->count_14);    // 0x0011E4AC
        arrays[5] = CreateArray(owner, counts->count_2c);    // 0x0011E59C
        arrays[6] = CreateArray(owner, counts->count_18);    // 0x0011DFF0
        arrays[7] = CreateArray(owner, counts->count_1c);    // 0x0011E0E0
        arrays[8] = CreateArray(owner, counts->count_20);    // 0x0011E1D0
        arrays[9] = CreateArray(owner, counts->count_24);    // 0x0011E2C4
        arrays[10] = CreateArray(owner, counts->count_28);   // 0x0011E3BC
        arrays[11] = CreateArray(owner, counts->count_30);   // 0x0011E690
        arrays[12] = CreateArray(owner, counts->count_34);   // 0x0011E77C
        arrays[13] = CreateArray(owner, counts->count_38);   // 0x0011E870
        arrays[14] = CreateArray(owner, counts->count_3c);   // 0x0011E964
    }

    // 0x0011EA50..0x0011EA70: allocator->vtable[2](owner, 0xF8, 4).
    void* storage = OwnerAllocate(owner, 0xF8, 4);
    if (storage == nullptr) {
        // 0x0011EF88..0x0011F4F0: release every array that was built.
        ReleaseArrays(arrays);
        return nullptr;
    }

    EventResourceTable* table = static_cast<EventResourceTable*>(storage);
    table->vtable = reinterpret_cast<const void*>(
        static_cast<std::uintptr_t>(kEventResourceTableAddress)); // 0x0011EDC8
    table->owner = owner;                                        // 0x0011EDC4

    // 0x0011EAB0..0x0011EF80: move all fifteen members into the result.
    // The source slots keep `ctx` and the tag bits of `capacity`, but begin
    // and end are cleared (`str r1,[sp,#...]` with r1 = 0, then
    // `and r2,r2,#0xc0000000` and `stm`/`str`).
    for (u32 i = 0; i < 15; ++i) {
        table->arrays[i] = arrays[i];
        arrays[i].begin = nullptr;
        arrays[i].end = nullptr;
        arrays[i].capacity &= kVectorCapacityMask;
    }

    return table;
}

} // namespace smt4::engine
