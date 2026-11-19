#include "types.h"

// Typed callable reconstruction of only the first body at 0x002e0dd0.
// All helper addresses and meanings remain unresolved interfaces.
extern "C" u32 h18_002e0dd0_candidate(u32 arg0, u32 arg1, const u16* arg2,
                                       u32 arg3, u32 arg4) {
    using Gate = u32 (*)(u32, u32, u32, u32);
    using Count = u32 (*)(const u16*);
    using Value = void (*)(u32, u32, const u16*, u32);
    using Cleanup = void (*)(u32);

    const u32 global_context = *reinterpret_cast<volatile const u32*>(0x00464fac);
    const u32 object = *reinterpret_cast<volatile const u32*>(global_context + 0x18);
    const auto gate = reinterpret_cast<Gate>(0x00263534u);
    const u32 status = gate(object, arg0, arg1, arg3);
    if ((status & 0x80000000u) != 0) return 5;

    const auto count_nonzero = reinterpret_cast<Count>(0x002b5c2du);
    const auto apply_value = reinterpret_cast<Value>(0x00248e58u);
    const u32 count = count_nonzero(arg2);
    apply_value(object, 0x6eu, arg2, count << 1);
    apply_value(object, 0x65u, reinterpret_cast<const u16*>(arg3), arg4);

    const auto cleanup = reinterpret_cast<Cleanup>(0x002390dcu);
    cleanup(object);
    return 0;
}
