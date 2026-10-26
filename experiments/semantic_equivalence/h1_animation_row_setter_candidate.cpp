// Readable experimental model of pinned ARM entry 0x002BDAC0.
// Its evidence supports a row-driven object initializer; it does not identify
// a stronger engine-level type for the opaque object or table.
#include <stdint.h>

namespace {
static int16_t read_s16(const uint8_t* p) {
    const uint16_t bits = static_cast<uint16_t>(p[0]) |
                          (static_cast<uint16_t>(p[1]) << 8);
    return static_cast<int16_t>(bits);
}

static uint32_t read_u32(const uint8_t* p) {
    return static_cast<uint32_t>(p[0]) |
           (static_cast<uint32_t>(p[1]) << 8) |
           (static_cast<uint32_t>(p[2]) << 16) |
           (static_cast<uint32_t>(p[3]) << 24);
}

static void write_u16(uint8_t* p, uint16_t value) {
    p[0] = static_cast<uint8_t>(value);
    p[1] = static_cast<uint8_t>(value >> 8);
}

static void write_u32(uint8_t* p, uint32_t value) {
    p[0] = static_cast<uint8_t>(value);
    p[1] = static_cast<uint8_t>(value >> 8);
    p[2] = static_cast<uint8_t>(value >> 16);
    p[3] = static_cast<uint8_t>(value >> 24);
}

static uint32_t coordinate_12_12(int16_t coordinate) {
    // Convert to unsigned before shifting to model ARM's modulo-2^32 LSL.
    return static_cast<uint32_t>(static_cast<int32_t>(coordinate)) << 12;
}
} // namespace

extern "C" void h1_animation_row_setter_candidate(void* opaque_object,
                                                   int32_t row_index,
                                                   int32_t mode) {
    auto* object = static_cast<uint8_t*>(opaque_object);
    const uint32_t table_address = read_u32(object + 0x4C);
    if (table_address == 0) {
        return;
    }

    // ARM stores the low halfword but scales the full r1 argument for the row
    // address. Use unsigned arithmetic to preserve its 32-bit wrap semantics.
    write_u16(object + 0x50, static_cast<uint16_t>(row_index));
    write_u16(object + 0x52, 0);
    object[0x86] = 0;
    object[0x8A] = 0;
    object[0x54] = static_cast<uint8_t>(mode);

    const uint32_t row_offset = static_cast<uint32_t>(row_index) * 12u;
    const uint32_t row_address = table_address + row_offset;
    const auto* row = reinterpret_cast<const uint8_t*>(static_cast<uintptr_t>(row_address));
    const unsigned x_offset = mode != 0 ? 4u : 0u;
    const unsigned y_offset = mode != 0 ? 6u : 2u;
    write_u32(object + 0x0C, coordinate_12_12(read_s16(row + x_offset)));
    write_u32(object + 0x10, coordinate_12_12(read_s16(row + y_offset)));
}
