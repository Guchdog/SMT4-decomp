#include "types.h"

extern "C" s32 ui_func_002b902c(u32 id);
extern "C" s32 ui_func_002bffbc(u32 id);
extern "C" u32 ui_func_002c17d4(u32 id);

using H2LogicalFallback = u32 (*)(u32);

extern "C" u32 candidate_002c1830(u32 id, u32 mode) {
    u32 value = 0;
    if (mode == 0) {
        value = static_cast<u32>(ui_func_002b902c(id));
    } else if (mode == 1) {
        value = static_cast<u32>(ui_func_002bffbc(id));
    } else if (mode == 2) {
        value = ui_func_002c17d4(id);
    } else {
        return 0;
    }
    if (value != 0) {
        return value;
    }

    const u32 fallback_code = static_cast<u32>(id == 0)
                            + (static_cast<u32>(id == 1) << 1)
                            + static_cast<u32>(id == 7) * 6u
                            + static_cast<u32>(id == 8) * 5u
                            + static_cast<u32>(id == 9) * 3u
                            + static_cast<u32>(id == 10) * 4u;
    const u32 secondary_id = id >= 3 && id <= 6 ? id + 9u : 0u;

    if (secondary_id != 0) {
        if (mode == 0) {
            value = static_cast<u32>(ui_func_002b902c(secondary_id));
        } else if (mode == 1) {
            value = static_cast<u32>(ui_func_002bffbc(secondary_id));
        } else {
            value = ui_func_002c17d4(secondary_id);
        }
        if (value != 0) {
            return value;
        }
    }
    if (fallback_code == 0) {
        return 0;
    }

    const u32 fallback_address = mode == 0 ? 0x00125C10u
                              : mode == 1 ? 0x00124FA8u
                                          : 0x00124F0Cu;
    return reinterpret_cast<H2LogicalFallback>(fallback_address)(fallback_code);
}
