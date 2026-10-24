#include <cstdint>

using u8 = std::uint8_t;
using u16 = std::uint16_t;
using u32 = std::uint32_t;

template <u32 DispatchOffset, u32 FlagValue = 1>
static u32 dispatch_halfword_entry(volatile u8* record) {
    // The original saves this callee-saved pair before any data access. Keep
    // that visible even on a fault in this exception-sensitive experiment.
    __asm__ volatile("push {r4, r5}" ::: "memory");
    // Preserve the binary's two independent cursors and the order of reads
    // before writes. The selected halfword indexes a pointer table.
    auto* cursor_pair = reinterpret_cast<volatile u32*>(record + 0x18);
    const u32 source_cursor = cursor_pair[0];
    const u32 output_cursor = cursor_pair[1];

    const u32 source_address = *reinterpret_cast<volatile u32*>(record + 0xbc);
    const u32 table_address = *reinterpret_cast<volatile u32*>(record + DispatchOffset);
    const u32 item_address = source_address + 2u + source_cursor * 4u;
    const u16 key = *reinterpret_cast<volatile u16*>(
        static_cast<std::uintptr_t>(item_address));
    const u32 value = *reinterpret_cast<volatile u32*>(
        static_cast<std::uintptr_t>(table_address + key * 4u));

    const u32 flags_address = static_cast<u32>(
        reinterpret_cast<std::uintptr_t>(record) + 0x20u + output_cursor);
    *reinterpret_cast<volatile u8*>(static_cast<std::uintptr_t>(flags_address)) =
        static_cast<u8>(FlagValue);

    // ARM STR uses 32-bit address arithmetic; express that explicitly so
    // wraparound aliases remain testable without C++ pointer arithmetic UB.
    const u32 pointer_cursor = *reinterpret_cast<volatile u32*>(record + 0x1c);
    const u32 pointer_slot_address = static_cast<u32>(
        reinterpret_cast<std::uintptr_t>(record) + 0x3cu + pointer_cursor * 4u);
    *reinterpret_cast<volatile u32*>(
        static_cast<std::uintptr_t>(pointer_slot_address)) = value;

    // The original reloads both cursor fields after its output store, so a
    // deliberately overlapping output slot must affect these increments.
    volatile u32* output_field = reinterpret_cast<volatile u32*>(record + 0x1c);
    *output_field = *output_field + 1u;
    volatile u32* source_field = reinterpret_cast<volatile u32*>(record + 0x18);
    *source_field = *source_field + 1u;
    __asm__ volatile("pop {r4, r5}" ::: "memory");
    return 1;
}

extern "C" __attribute__((noinline, used)) u32 candidate_001dc648(volatile u8* record) {
    return dispatch_halfword_entry<0xec, 1>(record);
}

extern "C" __attribute__((noinline, used)) u32 candidate_001dc6a8(volatile u8* record) {
    return dispatch_halfword_entry<0xe8, 0>(record);
}

extern "C" __attribute__((noinline, used)) u32 negative_wrong_dispatch_001dc648(volatile u8* record) {
    return dispatch_halfword_entry<0xe8>(record);
}

extern "C" __attribute__((noinline, used)) u32 negative_wrong_dispatch_001dc6a8(volatile u8* record) {
    return dispatch_halfword_entry<0xec>(record);
}

extern "C" __attribute__((noinline, used)) u32 negative_wrong_flag_value_001dc648(volatile u8* record) {
    return dispatch_halfword_entry<0xec, 0>(record);
}

extern "C" __attribute__((noinline, used)) u32 negative_wrong_flag_value_001dc6a8(volatile u8* record) {
    return dispatch_halfword_entry<0xe8, 1>(record);
}
