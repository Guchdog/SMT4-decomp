#include <stdint.h>

// Experimental readable reconstruction of 0x002B1FC0. All pointers below
// must refer to valid, ordinary memory with the layouts described in the
// function record; the original performs no bounds checks.
namespace {
static uint8_t read_u8(const uint8_t* p) { return p[0]; }

static int8_t read_s8(const uint8_t* p) {
    return static_cast<int8_t>(p[0]);
}

static uint16_t read_u16(const uint8_t* p) {
    return static_cast<uint16_t>(p[0]) |
           (static_cast<uint16_t>(p[1]) << 8);
}

static int16_t read_s16(const uint8_t* p) {
    return static_cast<int16_t>(read_u16(p));
}

static uint32_t read_u32(const uint8_t* p) {
    return static_cast<uint32_t>(p[0]) |
           (static_cast<uint32_t>(p[1]) << 8) |
           (static_cast<uint32_t>(p[2]) << 16) |
           (static_cast<uint32_t>(p[3]) << 24);
}

static void write_u8(uint8_t* p, uint8_t value) { p[0] = value; }

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

static float float_from_bits(uint32_t bits) {
    return __builtin_bit_cast(float, bits);
}

static uint32_t float_to_bits(float value) {
    return __builtin_bit_cast(uint32_t, value);
}

static uint32_t row_address(uint32_t table, int16_t index) {
    return table + static_cast<uint32_t>(static_cast<int32_t>(index)) * 12u;
}

static void store_endpoint(uint8_t* object, uint32_t address, bool second) {
    const auto* row = reinterpret_cast<const uint8_t*>(static_cast<uintptr_t>(address));
    write_u32(object + 0x20, read_u32(row + (second ? 4u : 0u)));
}

static void interpolate(uint8_t* object, const uint8_t* row,
                        uint32_t duration, bool direction_nonzero) {
    const float first = float_from_bits(read_u32(row));
    const float second = float_from_bits(read_u32(row + 4));
    const float delta = direction_nonzero ? first - second : second - first;
    const float divisor = static_cast<float>(duration);
    const float step = delta / divisor;
    const float current = float_from_bits(read_u32(object + 0x20));
    const float next = step + current;
    write_u32(object + 0x20, float_to_bits(next));
}
} // namespace

extern "C" void* h1_preview_scale_track_candidate(void* opaque_object) {
    auto* object = static_cast<uint8_t*>(opaque_object);
    if (read_u8(object + 0x87) != 0)
        return opaque_object;

    const uint32_t table = read_u32(object + 0x58);
    if (table == 0)
        return opaque_object;

    const int16_t row_index = read_s16(object + 0x5C);
    const int16_t progress = read_s16(object + 0x5E);
    const uint32_t current_row_address = row_address(table, row_index);
    const auto* current_row = reinterpret_cast<const uint8_t*>(
        static_cast<uintptr_t>(current_row_address));
    const uint32_t duration = read_u16(current_row + 8);

    // ARM CMP compares the zero-extended duration against signed LDRSH r3.
    if (static_cast<int32_t>(duration) > static_cast<int32_t>(progress)) {
        interpolate(object, current_row, duration, read_u8(object + 0x60) != 0);
        write_u16(object + 0x5E,
                  static_cast<uint16_t>(static_cast<int32_t>(progress) + 1));
        return opaque_object;
    }

    const bool row_mode = read_u8(current_row + 0x0A) != 0;
    const bool direction_nonzero = read_s8(object + 0x60) != 0;
    if (row_mode) {
        store_endpoint(object, current_row_address, direction_nonzero);
        write_u16(object + 0x5E, 0);
        return opaque_object;
    }

    // The row-mode-zero path chooses the opposite current endpoint before
    // examining the optional sequence, matching the pinned store order.
    store_endpoint(object, current_row_address, !direction_nonzero);
    if (read_u8(object + 0x84) == 0) {
        write_u8(object + 0x87, 1);
        return opaque_object;
    }

    const uint32_t sequence = read_u32(object + 0x78);
    if (sequence == 0) {
        write_u8(object + 0x87, 1);
        return opaque_object;
    }

    const int16_t sequence_index = read_s16(object + 0x7E);
    const uint32_t sequence_entry_address = sequence + 0x0Cu +
        static_cast<uint32_t>(static_cast<int32_t>(sequence_index)) * 28u;
    const auto* sequence_entry = reinterpret_cast<const uint8_t*>(
        static_cast<uintptr_t>(sequence_entry_address));
    if (static_cast<int32_t>(read_u32(sequence_entry)) == -1) {
        write_u8(object + 0x87, 1);
        return opaque_object;
    }

    const uint16_t incremented_bits = static_cast<uint16_t>(
        static_cast<int32_t>(sequence_index) + 1);
    write_u16(object + 0x7E, incremented_bits);
    const int16_t next_index = read_s16(object + 0x7E);
    const uint32_t next_entry_address = sequence +
        static_cast<uint32_t>(static_cast<int32_t>(next_index)) * 28u;
    const auto* next_entry = reinterpret_cast<const uint8_t*>(
        static_cast<uintptr_t>(next_entry_address));
    const int32_t next_word = static_cast<int32_t>(read_u32(next_entry + 0x0C));
    if (next_word == -1 || next_word == -3) {
        write_u8(object + 0x87, 1);
        return opaque_object;
    }

    int32_t next_row_index;
    int8_t next_direction;
    if (next_word == -2) {
        write_u16(object + 0x7E, 0);
        next_row_index = static_cast<int16_t>(read_u16(
            reinterpret_cast<const uint8_t*>(static_cast<uintptr_t>(sequence)) + 0x0C));
        next_direction = read_s8(
            reinterpret_cast<const uint8_t*>(static_cast<uintptr_t>(sequence)) + 0x10);
    } else {
        next_row_index = static_cast<int16_t>(static_cast<uint16_t>(next_word));
        next_direction = read_s8(next_entry + 0x10);
    }

    write_u16(object + 0x5C, static_cast<uint16_t>(next_row_index));
    write_u16(object + 0x5E, 0);
    write_u8(object + 0x60, static_cast<uint8_t>(next_direction));
    write_u8(object + 0x8A, 0);
    const uint32_t next_row_address = row_address(table,
                                                  static_cast<int16_t>(next_row_index));
    store_endpoint(object, next_row_address, next_direction != 0);
    return opaque_object;
}
