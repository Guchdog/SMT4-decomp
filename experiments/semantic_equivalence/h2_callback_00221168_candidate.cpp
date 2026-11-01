#include <stdint.h>
extern "C" uint32_t h2_set_global(uint32_t);
extern "C" uint32_t h2_get_state(uint32_t);
extern "C" uint32_t h2_get_context(uint32_t);
extern "C" uint32_t h2_select_value(uint32_t);
extern "C" uint32_t h2_final_helper(uint32_t, uint32_t, uint32_t, uint32_t, uint32_t, uint32_t);
extern "C" uint32_t candidate_00221168() {
    auto slots = reinterpret_cast<uint32_t*>(0x0043e188);
    uint32_t state = h2_get_state(h2_set_global(0));
    if (state == 0) {
        auto object = reinterpret_cast<uint8_t*>(slots[2]);
        if (object != nullptr) object[0x30] = 1;
        object[0x31] = 1;
    }
    auto object = reinterpret_cast<uint8_t*>(slots[1]);
    if (object != nullptr) object[0xa11] = 0x14;
    uint32_t context = h2_get_context(reinterpret_cast<uint32_t>(object));
    uint32_t value = h2_select_value(0);
    uint32_t current = h2_get_state(value);
    return h2_final_helper(context, value, current, 6, 1, 0);
}
