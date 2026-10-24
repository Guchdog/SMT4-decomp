#include <cstdint>

using u8 = std::uint8_t;
using u16 = std::uint16_t;
using u32 = std::uint32_t;
using u64 = std::uint64_t;

// The binary takes r0=record and r1=address of a pointer slot. Keep the
// pointer-slot reload and each field access sequenced: the initial byte clear
// and the halfword store can alias later inputs. Volatile is used to prevent
// those accesses from being folded/reordered in this bounded RAM experiment.
// The +0xc/+0x10 snapshot is deliberately one volatile 64-bit load, matching
// the original LDRD footprint/instruction where the compiler supports it.
template <u32 Address>
static u32 indexed_halfword_writer(u8* record, void* target_slot_address) {
    auto* slot = reinterpret_cast<volatile u32* volatile*>(target_slot_address);
    volatile u32* first_target = *slot;
    *reinterpret_cast<volatile u8*>(first_target + 2) = 0;

    const u64 pair = *reinterpret_cast<volatile u64*>(record + 0x0c);
    const u32 base = static_cast<u32>(pair);
    const u32 index = static_cast<u32>(pair >> 32);

    volatile u32* second_target = *slot;
    const u32 source_address = base + (index << 1);
    const u16 value = *reinterpret_cast<volatile u16*>(
        static_cast<std::uintptr_t>(source_address));
    *reinterpret_cast<volatile u16*>(
        reinterpret_cast<volatile u8*>(second_target) + 0x0a) = value;

    auto* index_field = reinterpret_cast<volatile u32*>(record + 0x10);
    const u32 next_index = *index_field + 1;
    *index_field = next_index;
    return 0;
}

extern "C" __attribute__((noinline, used)) u32 candidate_0035bbc4(
    u8* record, void* target_slot_address) {
    return indexed_halfword_writer<0x0035bbc4>(record, target_slot_address);
}

extern "C" __attribute__((noinline, used)) u32 candidate_0035c00c(
    u8* record, void* target_slot_address) {
    return indexed_halfword_writer<0x0035c00c>(record, target_slot_address);
}

// Negative controls: wrong source stride; wrong output-store width; and
// incrementing the cursor before writing the halfword (caught by alias cases).
extern "C" __attribute__((noinline, used)) u32 negative_wrong_stride(
    u8* record, void* target_slot_address) {
    auto* slot = reinterpret_cast<volatile u32* volatile*>(target_slot_address);
    volatile u32* target = *slot;
    *reinterpret_cast<volatile u8*>(target + 2) = 0;
    const u64 pair = *reinterpret_cast<volatile u64*>(record + 0x0c);
    const u32 source = static_cast<u32>(pair) +
                       (static_cast<u32>(pair >> 32) << 2);
    target = *slot;
    const u16 value = *reinterpret_cast<volatile u16*>(
        static_cast<std::uintptr_t>(source));
    *reinterpret_cast<volatile u16*>(
        reinterpret_cast<volatile u8*>(target) + 0x0a) = value;
    auto* cursor = reinterpret_cast<volatile u32*>(record + 0x10);
    *cursor = *cursor + 1;
    return 0;
}

extern "C" __attribute__((noinline, used)) u32 negative_byte_store(
    u8* record, void* target_slot_address) {
    auto* slot = reinterpret_cast<volatile u32* volatile*>(target_slot_address);
    volatile u32* target = *slot;
    *reinterpret_cast<volatile u8*>(target + 2) = 0;
    const u64 pair = *reinterpret_cast<volatile u64*>(record + 0x0c);
    const u32 source = static_cast<u32>(pair) +
                       (static_cast<u32>(pair >> 32) << 1);
    target = *slot;
    const u16 value = *reinterpret_cast<volatile u16*>(
        static_cast<std::uintptr_t>(source));
    *reinterpret_cast<volatile u8*>(
        reinterpret_cast<volatile u8*>(target) + 0x0a) = static_cast<u8>(value);
    auto* cursor = reinterpret_cast<volatile u32*>(record + 0x10);
    *cursor = *cursor + 1;
    return 0;
}

extern "C" __attribute__((naked, noinline, used)) u32 negative_increment_before_store(
    u8*, void*) {
    // Deliberately place STRH after the cursor increment. Keep this control
    // leaf-shaped so the same fail-closed harness validates its code blob.
    __asm__ volatile(
        "ldr r3, [r1]\n"
        "mov r2, #0\n"
        "strb r2, [r3, #8]\n"
        "ldrd r2, r3, [r0, #0xc]\n"
        "add r2, r2, r3, lsl #1\n"
        "ldr r1, [r1]\n"
        "ldrh r2, [r2]\n"
        "ldr r3, [r0, #0x10]\n"
        "add r3, r3, #1\n"
        "str r3, [r0, #0x10]\n"
        "strh r2, [r1, #0xa]\n"
        "mov r0, #0\n"
        "bx lr\n");
}
