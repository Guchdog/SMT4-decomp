#include <stdint.h>

using u8 = uint8_t;
using u16 = uint16_t;
using u32 = uint32_t;

namespace {

const u8* tagged_payload(const u8* base, u16 expected_tag) {
    // Volatile pins the target's observable load order: the tag is always read,
    // while the relative offset is read only for the matching tag.
    const volatile u16* tag = reinterpret_cast<const volatile u16*>(base);
    if (*tag != expected_tag) {
        return nullptr;
    }
    const volatile u32* relative_offset =
        reinterpret_cast<const volatile u32*>(base + 4);
    const u32 result = static_cast<u32>(reinterpret_cast<uintptr_t>(base)) +
                       *relative_offset;
    return reinterpret_cast<const u8*>(static_cast<uintptr_t>(result));
}

const u8* tagged_payload_wrong_tag(const u8* base, u16 expected_tag) {
    const volatile u16* tag = reinterpret_cast<const volatile u16*>(base);
    if (*tag != static_cast<u16>(expected_tag + 1)) {
        return nullptr;
    }
    const volatile u32* relative_offset =
        reinterpret_cast<const volatile u32*>(base + 4);
    const u32 result = static_cast<u32>(reinterpret_cast<uintptr_t>(base)) +
                       *relative_offset;
    return reinterpret_cast<const u8*>(static_cast<uintptr_t>(result));
}

const u8* tagged_payload_wrong_offset(const u8* base, u16 expected_tag) {
    const volatile u16* tag = reinterpret_cast<const volatile u16*>(base);
    if (*tag != expected_tag) {
        return nullptr;
    }
    const volatile u32* wrong_relative_offset =
        reinterpret_cast<const volatile u32*>(base + 8);
    const u32 result = static_cast<u32>(reinterpret_cast<uintptr_t>(base)) +
                       *wrong_relative_offset;
    return reinterpret_cast<const u8*>(static_cast<uintptr_t>(result));
}

}  // namespace

extern "C" __attribute__((noinline, used)) const u8* candidate_003e6974(
    const u8* base) {
    return tagged_payload(base, 0x0300);
}

extern "C" __attribute__((noinline, used)) const u8* candidate_003e69a8(
    const u8* base) {
    return tagged_payload(base, 0x4100);
}

extern "C" __attribute__((noinline, used)) const u8* wrong_tag_003e6974(
    const u8* base) {
    return tagged_payload_wrong_tag(base, 0x0300);
}

extern "C" __attribute__((noinline, used)) const u8* wrong_tag_003e69a8(
    const u8* base) {
    return tagged_payload_wrong_tag(base, 0x4100);
}

extern "C" __attribute__((noinline, used)) const u8* wrong_offset_003e6974(
    const u8* base) {
    return tagged_payload_wrong_offset(base, 0x0300);
}

extern "C" __attribute__((noinline, used)) const u8* wrong_offset_003e69a8(
    const u8* base) {
    return tagged_payload_wrong_offset(base, 0x4100);
}
