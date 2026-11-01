#include <cstdint>

extern "C" int32_t candidate_002b89a0() {
    auto manager_slot = reinterpret_cast<const uint8_t* const*>(0x0044dc20);
    auto manager = *manager_slot;
    if (manager == nullptr) {
        return 1;
    }
    auto mode = *reinterpret_cast<const uint32_t*>(manager + 0x352c);
    return mode == 0x14 ? 1 : 0;
}
