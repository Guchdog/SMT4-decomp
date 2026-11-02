#include <stdint.h>
static inline bool signed_less(uint32_t a, uint32_t b) {
    return static_cast<int32_t>(a) < static_cast<int32_t>(b);
}
extern "C" __attribute__((minsize)) uint32_t candidate_002892c0(void* object, uint32_t index) {
    auto words = static_cast<uint32_t*>(object);
    auto out = static_cast<volatile uint32_t*>(object);
    const uint32_t count = words[7];
    if (count == 0) {
        out[9] = 0;
        out[8] = 0;
        return 1;
    }
    if (!signed_less(0, index)) index = 0;
    else if (signed_less(count, index)) index = count - 1u;
    const uint32_t delta = index - words[8];
    if (signed_less(delta, 0)) {
        out[8] = index;
        out[9] = 0;
    } else {
        uint32_t visible = words[4];
        out[9] = delta;
        if (signed_less(count, visible)) visible = count;
        const uint32_t limit = count - visible;
        if (signed_less(limit, delta)) {
            out[9] = limit;
            out[8] = index - limit;
        }
    }
    return 1;
}
