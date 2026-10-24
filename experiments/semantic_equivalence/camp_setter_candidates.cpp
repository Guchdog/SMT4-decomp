// Isolated semantic-experiment candidates for two CAMP leaves.
// Evidence establishes only ordered byte/halfword writes at fixed offsets.
#include <cstdint>

extern "C" volatile std::uint8_t* candidate_003c8fc8(volatile std::uint8_t* base,
                                                      std::uint32_t byte_value,
                                                      std::uint32_t halfword_0,
                                                      std::uint32_t halfword_1) {
    base[0x136] = static_cast<std::uint8_t>(byte_value);
    *reinterpret_cast<volatile std::uint16_t*>(base + 0x138) =
        static_cast<std::uint16_t>(halfword_0);
    *reinterpret_cast<volatile std::uint16_t*>(base + 0x13a) =
        static_cast<std::uint16_t>(halfword_1);
    return base;
}

extern "C" volatile std::uint8_t* candidate_003c9314(volatile std::uint8_t* base,
                                                      std::uint32_t byte_value,
                                                      std::uint32_t halfword_0,
                                                      std::uint32_t halfword_1) {
    base[0x13c] = static_cast<std::uint8_t>(byte_value);
    *reinterpret_cast<volatile std::uint16_t*>(base + 0x13e) =
        static_cast<std::uint16_t>(halfword_0);
    *reinterpret_cast<volatile std::uint16_t*>(base + 0x140) =
        static_cast<std::uint16_t>(halfword_1);
    return base;
}

// Negative controls prove the fixtures detect a width/offset mistake and a
// halfword-value/order mistake. Neither is an alternative implementation.
extern "C" volatile std::uint8_t* negative_camp_wrong_byte_offset(volatile std::uint8_t* base,
                                                                  std::uint32_t byte_value,
                                                                  std::uint32_t halfword_0,
                                                                  std::uint32_t halfword_1) {
    base[0x137] = static_cast<std::uint8_t>(byte_value);
    *reinterpret_cast<volatile std::uint16_t*>(base + 0x138) =
        static_cast<std::uint16_t>(halfword_0);
    *reinterpret_cast<volatile std::uint16_t*>(base + 0x13a) =
        static_cast<std::uint16_t>(halfword_1);
    return base;
}

extern "C" volatile std::uint8_t* negative_camp_swapped_halfwords(volatile std::uint8_t* base,
                                                                  std::uint32_t byte_value,
                                                                  std::uint32_t halfword_0,
                                                                  std::uint32_t halfword_1) {
    base[0x136] = static_cast<std::uint8_t>(byte_value);
    *reinterpret_cast<volatile std::uint16_t*>(base + 0x138) =
        static_cast<std::uint16_t>(halfword_1);
    *reinterpret_cast<volatile std::uint16_t*>(base + 0x13a) =
        static_cast<std::uint16_t>(halfword_0);
    return base;
}
