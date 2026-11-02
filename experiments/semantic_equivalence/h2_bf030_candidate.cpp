#include <cstdint>

extern "C" uint32_t candidate_002bf030(uint8_t* object, uint32_t selector) {
    auto manager = *reinterpret_cast<uint8_t**>(object + 0x48);
    auto n = *reinterpret_cast<const uint16_t*>(manager + 8);
    auto count = (static_cast<uint32_t>(n) * 0x9249u + 0x9249u) >> 20;
    uint8_t* selected = nullptr;
    if (count != 0) {
        auto table = *reinterpret_cast<uint8_t**>(manager + 0x1c);
        uint32_t markers = 0;
        for (uint32_t i = 0; i < count; ++i) {
            auto entry = table + i * 28u;
            if (markers == selector) { selected = entry; break; }
            if (*reinterpret_cast<const uint32_t*>(entry) == 0xffffffffu) ++markers;
        }
    }
    using service_fn = uint32_t (*)(uint8_t*, uint8_t*);
    auto service = reinterpret_cast<service_fn>(0x00138934);
    return service(object, selected);
}
