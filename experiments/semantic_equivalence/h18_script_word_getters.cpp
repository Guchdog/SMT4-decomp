#include <cstdint>

extern "C" std::uint32_t candidate_002345f0(const std::uint8_t* p) {
    const auto value = *reinterpret_cast<const std::uint16_t*>(p + 0x48);
    return static_cast<std::uint32_t>(value & 0xffu);
}

extern "C" std::uint32_t candidate_002345fc(const std::uint8_t* p) {
    const auto value = *reinterpret_cast<const std::uint16_t*>(p + 0x4a);
    return static_cast<std::uint32_t>(value & 0xffu);
}

extern "C" std::uint32_t control_wrong_offset(const std::uint8_t* p) {
    return static_cast<std::uint32_t>(*reinterpret_cast<const std::uint16_t*>(p + 0x4a) & 0xffu);
}

extern "C" std::uint32_t control_signed_extension(const std::uint8_t* p) {
    return static_cast<std::uint32_t>(static_cast<std::int32_t>(static_cast<std::int8_t>(p[0x48])));
}

extern "C" std::uint32_t control_omitted_mask(const std::uint8_t* p) {
    return *reinterpret_cast<const std::uint16_t*>(p + 0x48);
}

extern "C" std::uint32_t control_memory_write(const std::uint8_t* p) {
    auto* writable = const_cast<std::uint8_t*>(p);
    writable[0] ^= 1;
    return static_cast<std::uint32_t>(*reinterpret_cast<const std::uint16_t*>(p + 0x48) & 0xffu);
}
