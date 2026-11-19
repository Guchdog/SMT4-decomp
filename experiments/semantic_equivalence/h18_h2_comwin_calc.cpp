#include <cstdint>

extern "C" uint32_t h18_h2_comwin_calc_candidate(void*) {
    auto* const work = *reinterpret_cast<volatile uint8_t* const*>(0x0043e0f8u);
    const uint32_t state = *reinterpret_cast<volatile uint32_t*>(work + 8u);
    using WidgetCalc = int32_t (*)(void*);
    const auto widget_calc = reinterpret_cast<WidgetCalc>(0x002bf9f0u);

    switch (state) {
    case 1:
        if (widget_calc(const_cast<uint8_t*>(work + 0x3cu)) != 0) {
            *reinterpret_cast<volatile uint32_t*>(work + 8u) = 2;
            *reinterpret_cast<volatile uint32_t*>(work + 0x0cu) = 0;
        }
        break;
    case 2:
        (void)widget_calc(const_cast<uint8_t*>(work + 0xc8u));
        break;
    case 4:
        if (widget_calc(const_cast<uint8_t*>(work + 0x3cu)) != 0) {
            *reinterpret_cast<volatile uint32_t*>(work + 8u) = 0;
        }
        break;
    default:
        break;
    }

    *reinterpret_cast<volatile uint32_t*>(work + 0x0cu) += 1u;
    return 0;
}
