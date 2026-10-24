#include <cstdint>

using u32 = std::uint32_t;

// Isolated semantic reconstruction of ARM leaf 0x00151ff4. The binary
// reloads the active count before each lane, so count and source reads must
// remain volatile and ordered with the corresponding destination write.
extern "C" __attribute__((noinline, used)) u32 candidate_00151ff4(
    void* descriptor, void* destination) {
    auto* const descriptor_words = static_cast<volatile u32*>(descriptor);
    const u32 offset = descriptor_words[1];
    auto* const source = reinterpret_cast<volatile u32*>(
        reinterpret_cast<std::uintptr_t>(descriptor) + offset);
    auto* const output = static_cast<volatile u32*>(destination);
    const u32 base = static_cast<u32>(reinterpret_cast<std::uintptr_t>(source));
    u32 result = base;

    for (u32 lane = 0; lane != 4; ++lane) {
        const u32 active_count = source[0];
        const u32 value = active_count > lane ? source[lane + 1] : 0xffffffffu;
        output[lane] = value;
        if (lane == 3 && active_count > 3)
            result = value;
    }
    return result;
}

// Negative controls. The first snapshots the count once (wrong under aliasing);
// the second uses >= instead of the binary's strict unsigned comparison.
extern "C" __attribute__((noinline, used)) u32 negative_cached_count_00151ff4(
    void* descriptor, void* destination) {
    auto* const bytes = static_cast<std::uint8_t*>(descriptor);
    const u32 offset = *reinterpret_cast<volatile u32*>(bytes + 4);
    auto* const source = reinterpret_cast<volatile u32*>(
        reinterpret_cast<std::uintptr_t>(descriptor) + offset);
    auto* const output = static_cast<volatile u32*>(destination);
    const u32 count = source[0];
    output[0] = count > 0 ? source[1] : 0xffffffffu;
    output[1] = count > 1 ? source[2] : 0xffffffffu;
    output[2] = count > 2 ? source[3] : 0xffffffffu;
    output[3] = count > 3 ? source[4] : 0xffffffffu;
    return count > 3 ? source[4] : static_cast<u32>(reinterpret_cast<std::uintptr_t>(source));
}

extern "C" __attribute__((noinline, used)) u32 negative_inclusive_count_00151ff4(
    void* descriptor, void* destination) {
    auto* const bytes = static_cast<std::uint8_t*>(descriptor);
    const u32 offset = *reinterpret_cast<volatile u32*>(bytes + 4);
    auto* const source = reinterpret_cast<volatile u32*>(
        reinterpret_cast<std::uintptr_t>(descriptor) + offset);
    auto* const output = static_cast<volatile u32*>(destination);
    u32 result = static_cast<u32>(reinterpret_cast<std::uintptr_t>(source));
    u32 count = source[0];
    output[0] = count >= 0 ? source[1] : 0xffffffffu;
    count = source[0];
    output[1] = count >= 1 ? source[2] : 0xffffffffu;
    count = source[0];
    output[2] = count >= 2 ? source[3] : 0xffffffffu;
    count = source[0];
    const u32 value = count >= 3 ? source[4] : 0xffffffffu;
    output[3] = value;
    if (count >= 3)
        result = value;
    return result;
}
