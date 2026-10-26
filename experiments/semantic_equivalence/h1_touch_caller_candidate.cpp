#include "types.h"

namespace {
using TouchQuery = s32 (*)(s16);

inline s32 query_region(s16 handle) {
    const auto query = reinterpret_cast<TouchQuery>(
        static_cast<std::uintptr_t>(0x0029D8FCu));
    return query(handle);
}

u32 scan_title_touch(void* work, bool reverse_selection, bool ignore_state_one) {
    auto* bytes = static_cast<u8*>(work);
    auto* handles = reinterpret_cast<const s16*>(bytes + 0x74);
    auto* cursor = reinterpret_cast<u32*>(bytes + 8);

    for (s32 step = 0; step < 4; ++step) {
        const s32 index = reverse_selection ? 3 - step : step;
        const s32 first_state = query_region(handles[index]);
        if (!ignore_state_one && first_state == 1) {
            *cursor = static_cast<u32>(index);
            break;
        }
        // The original calls the helper again for every non-state-1 result,
        // then compares only that second response with state 2.
        const s32 second_state = query_region(handles[index]);
        if (second_state == 2) {
            *cursor = static_cast<u32>(index);
            break;
        }
    }

    for (u32 index = 0; index < 4; ++index) {
        if (query_region(handles[index]) == 6) {
            *cursor = index;
            bytes[0x63] = 1;
        }
    }

    return *cursor;
}
} // namespace

extern "C" u32 h1_touch_caller_candidate(void* work) {
    return scan_title_touch(work, false, false);
}

extern "C" u32 negative_touch_reversed_priority(void* work) {
    return scan_title_touch(work, true, false);
}

extern "C" u32 negative_touch_ignores_state_one(void* work) {
    return scan_title_touch(work, false, true);
}
