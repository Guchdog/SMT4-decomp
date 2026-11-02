#include "types.h"

extern "C" uint32_t engine_func_002ae6b0(uint32_t code);
extern "C" uint32_t func_002ae664(uint32_t code);

// Bounded C++ reconstruction of the 32-byte text-record scan used by H2.
// The control-code predicate and code-to-index table lookup stay at their
// original ARM entry points until their own contracts are reconstructed.
extern "C" __attribute__((minsize)) uint32_t candidate_002b787c(
    uint32_t raw_handle) {
    const auto* handle = reinterpret_cast<const uint8_t*>(
        static_cast<uintptr_t>(raw_handle));
    if (*reinterpret_cast<const uint32_t*>(handle + 0x14) == 0) return 0;

    const uint32_t start = *reinterpret_cast<const uint32_t*>(handle + 0x0c);
    const int32_t signed_limit = static_cast<int32_t>(start + 0x3e7);
    uint32_t index = start;
    uint32_t count = 0;
    for (;;) {
        const uint32_t table_base = *reinterpret_cast<const uint32_t*>(handle);
        const uint32_t record_address = table_base + (index << 5);
        const uint32_t code = *reinterpret_cast<const uint16_t*>(
            static_cast<uintptr_t>(record_address));
        if (code == 0xffff) return count;

        if (engine_func_002ae6b0(code) != 0) {
            // The retained predicate has already constrained this to F801..F88F,
            // so its low byte uniquely selects the three special values.
            const uint8_t control_code = static_cast<uint8_t>(code);
            if (control_code == 1) {
                count += 1;
            } else if (control_code == 2) {
                return count;
            } else if (control_code == 0x1a) {
                index += 1;
                const uint32_t payload_table =
                    *reinterpret_cast<const uint32_t*>(handle);
                const uint32_t payload_address = payload_table + (index << 5);
                count = *reinterpret_cast<const uint16_t*>(
                    static_cast<uintptr_t>(payload_address));
            } else {
                index += func_002ae664(code);
            }
        }

        index += 1;
        if (static_cast<int32_t>(index) >= signed_limit)
            return count;
    }
}
