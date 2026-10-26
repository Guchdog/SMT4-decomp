// Experimental readable reconstruction of pinned helper 0x002B1DFC.
// This is one translation-track update entry, not a merged animation helper.
#include <stdint.h>

namespace {
static int16_t read_s16(const uint8_t* p) {
    const uint16_t bits = static_cast<uint16_t>(p[0]) |
                          (static_cast<uint16_t>(p[1]) << 8);
    const int32_t signed_value = (bits & 0x8000u) != 0
        ? static_cast<int32_t>(bits) - 0x10000
        : static_cast<int32_t>(bits);
    return static_cast<int16_t>(signed_value);
}

static int8_t read_s8(const uint8_t* p) {
    const int32_t signed_value = (p[0] & 0x80u) != 0
        ? static_cast<int32_t>(p[0]) - 0x100
        : static_cast<int32_t>(p[0]);
    return static_cast<int8_t>(signed_value);
}

static uint16_t read_u16(const uint8_t* p) {
    return static_cast<uint16_t>(p[0]) |
           (static_cast<uint16_t>(p[1]) << 8);
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

static float read_f32(const uint8_t* p) {
    return __builtin_bit_cast(float, read_u32(p));
}

static uint32_t float_bits(float value) {
    return __builtin_bit_cast(uint32_t, value);
}

static uint32_t row_address(uint32_t table, int16_t index) {
    return table + static_cast<uint32_t>(static_cast<int32_t>(index)) * 12u;
}

static uint32_t sequence_entry_address(uint32_t sequence, int16_t index) {
    return sequence + 0x14u + static_cast<uint32_t>(static_cast<int32_t>(index)) * 0x1Cu;
}

static void install_sequence_row(uint8_t* object, uint32_t table,
                                 int16_t animation, int8_t direction) {
    write_u16(object + 0x68, static_cast<uint16_t>(animation));
    write_u16(object + 0x6A, 0);
    write_u8(object + 0x6C, static_cast<uint8_t>(direction));
    write_u8(object + 0x8A, 0);
    const uint32_t address = row_address(table, animation);
    const auto* row = reinterpret_cast<const uint8_t*>(static_cast<uintptr_t>(address));
    const uint32_t value = read_u32(row + (direction != 0 ? 4 : 0));
    write_u32(object + 0x24, value);
    write_u32(object + 0x28, value);
    write_u32(object + 0x2C, value);
}

static void update_sequence(uint8_t* object, uint32_t table) {
    const uint8_t enabled = object[0x84];
    if (enabled == 0) {
        write_u8(object + 0x88, 1);
        return;
    }
    const uint32_t sequence = read_u32(object + 0x78);
    if (sequence == 0) {
        write_u8(object + 0x88, 1);
        return;
    }

    const int16_t index = read_s16(object + 0x80);
    const uint32_t entry_address = sequence_entry_address(sequence, index);
    const auto* entry = reinterpret_cast<const uint8_t*>(static_cast<uintptr_t>(entry_address));
    const uint32_t current_word = read_u32(entry);
    if (current_word == 0xFFFFFFFFu) {
        write_u8(object + 0x88, 1);
        return;
    }

    const int16_t next_index = static_cast<int16_t>(static_cast<uint16_t>(index + 1));
    write_u16(object + 0x80, static_cast<uint16_t>(next_index));
    const uint32_t next_address = sequence_entry_address(sequence, next_index);
    const auto* next = reinterpret_cast<const uint8_t*>(static_cast<uintptr_t>(next_address));
    const uint32_t next_word = read_u32(next);
    if (next_word == 0xFFFFFFFFu || next_word == 0xFFFFFFFDu) {
        write_u8(object + 0x88, 1);
        return;
    }

    if (next_word == 0xFFFFFFFEu) {
        write_u16(object + 0x80, 0);
        const auto* first = reinterpret_cast<const uint8_t*>(
            static_cast<uintptr_t>(sequence_entry_address(sequence, 0)));
        const uint16_t animation_bits = static_cast<uint16_t>(read_u32(first));
        const int16_t animation = (animation_bits & 0x8000u) != 0
            ? static_cast<int16_t>(static_cast<int32_t>(animation_bits) - 0x10000)
            : static_cast<int16_t>(animation_bits);
        const int8_t direction = read_s8(first + 4);
        install_sequence_row(object, table, animation, direction);
        return;
    }

    const uint16_t animation_bits = static_cast<uint16_t>(next_word);
    const int16_t animation = (animation_bits & 0x8000u) != 0
        ? static_cast<int16_t>(static_cast<int32_t>(animation_bits) - 0x10000)
        : static_cast<int16_t>(animation_bits);
    const int8_t direction = read_s8(next + 4);
    install_sequence_row(object, table, animation, direction);
}
} // namespace

extern "C" void h1_preview_translation_track_candidate(void* opaque_object) {
    auto* object = static_cast<uint8_t*>(opaque_object);
    if (object[0x88] != 0) return;
    const uint32_t table = read_u32(object + 0x64);
    if (table == 0) return;

    const int16_t animation = read_s16(object + 0x68);
    const int16_t progress = read_s16(object + 0x6A);
    const uint32_t initial_row_address = row_address(table, animation);
    const auto* row = reinterpret_cast<const uint8_t*>(
        static_cast<uintptr_t>(initial_row_address));
    const uint16_t duration = read_u16(row + 8);

    if (static_cast<int32_t>(duration) > static_cast<int32_t>(progress)) {
        const uint8_t direction = object[0x6C];
        const float first = read_f32(row + (direction != 0 ? 0 : 4));
        const float second = read_f32(row + (direction != 0 ? 4 : 0));
        volatile float numerator = first - second;
        volatile float denominator = static_cast<float>(duration);
        volatile float delta = numerator / denominator;
        volatile float current = read_f32(object + 0x24);
        volatile float updated = current + delta;
        write_u32(object + 0x24, float_bits(updated));
        write_u16(object + 0x6A, static_cast<uint16_t>(progress + 1));
    } else {
        const uint8_t row_mode = row[0x0A];
        const int8_t direction = read_s8(object + 0x6C);
        const unsigned value_offset = row_mode != 0
            ? (direction != 0 ? 4u : 0u)
            : (direction != 0 ? 0u : 4u);
        write_u32(object + 0x24, read_u32(row + value_offset));
        if (row_mode != 0) {
            write_u16(object + 0x6A, 0);
        } else {
            // The mode-zero endpoint path does not clear progress unless a
            // sequence entry is actually installed by update_sequence.
            update_sequence(object, table);
        }
    }

    const uint32_t current_value = read_u32(object + 0x24);
    write_u32(object + 0x28, current_value);
    write_u32(object + 0x2C, current_value);
}
