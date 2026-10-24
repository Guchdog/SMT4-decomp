#include <cstdint>

using u32 = uint32_t;

// Isolated semantic reconstruction for 0x0035D270. The ordinary C++ ABI
// returns the selector value in r0; this is not integrated into production.
extern "C" __attribute__((noinline, used)) u32 candidate_0035d270(
    const uint8_t* object) {
    const u32 value = *reinterpret_cast<const u32*>(object + 0x18);
    return value == 0 ? 3u : 1u;
}

// Negative control: same field load but an intentionally incorrect zero case.
extern "C" __attribute__((noinline, used)) u32 wrong_zero_result_0035d270(
    const uint8_t* object) {
    const u32 value = *reinterpret_cast<const u32*>(object + 0x18);
    return value == 0 ? 2u : 1u;
}
