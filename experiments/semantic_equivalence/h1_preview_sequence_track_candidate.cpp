#include <stdint.h>

// Experimental reconstruction of the self-contained H1 sequence/track
// selector at 0x002B1C8C. Pointers and indices are unchecked just as in the
// original; the defined fixture domain uses valid, non-aliasing storage.
namespace {
static uint8_t read_u8(const uint8_t* p) { return p[0]; }
static int16_t read_s16(const uint8_t* p) {
    return static_cast<int16_t>(static_cast<uint16_t>(p[0]) |
                                (static_cast<uint16_t>(p[1]) << 8));
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
static uint8_t* at(uint32_t address) {
    return reinterpret_cast<uint8_t*>(static_cast<uintptr_t>(address));
}
static uint32_t indexed_address(uint32_t base, int16_t index,
                                uint32_t stride) {
    return base + static_cast<uint32_t>(static_cast<int32_t>(index)) * stride;
}
} // namespace

extern "C" void* h1_preview_sequence_track_candidate(void* opaque_object) {
    auto* object = static_cast<uint8_t*>(opaque_object);
    if (read_u8(object + 0x89) != 0)
        return opaque_object;

    const uint32_t current_table = read_u32(object + 0x70);
    if (current_table == 0)
        return opaque_object;

    const int16_t current_index = read_s16(object + 0x74);
    const int16_t progress = read_s16(object + 0x76);
    const uint32_t current_entry_address =
        indexed_address(current_table, current_index, 4);
    const uint16_t duration = read_u16(at(current_entry_address) + 2);

    // LDRH duration is nonnegative, so signed ARM GT is duration > s16 progress.
    if (static_cast<int32_t>(duration) > static_cast<int32_t>(progress)) {
        write_u16(object + 0x76,
                  static_cast<uint16_t>(static_cast<int32_t>(progress) + 1));
        return opaque_object;
    }

    const int16_t next_index = static_cast<int16_t>(
        static_cast<uint16_t>(static_cast<int32_t>(current_index) + 1));
    write_u16(object + 0x76, 0);
    write_u16(object + 0x74, static_cast<uint16_t>(next_index));
    const int16_t next_track = read_s16(at(indexed_address(
        current_table, next_index, 4)));

    if (next_track == -1) {
        if (read_u8(object + 0x84) == 0 || read_u32(object + 0x78) == 0) {
            write_u8(object + 0x89, 1);
            return opaque_object;
        }

        const uint32_t sequence = read_u32(object + 0x78);
        const int16_t sequence_index = read_s16(object + 0x82);
        const uint32_t current_sequence_entry =
            indexed_address(sequence, sequence_index, 28) + 8;
        if (static_cast<int32_t>(read_u32(at(current_sequence_entry))) == -1) {
            write_u8(object + 0x89, 1);
            return opaque_object;
        }

        const int16_t next_sequence_index = static_cast<int16_t>(
            static_cast<uint16_t>(static_cast<int32_t>(sequence_index) + 1));
        write_u16(object + 0x82,
                  static_cast<uint16_t>(next_sequence_index));
        const uint32_t next_sequence_word_address =
            indexed_address(sequence, next_sequence_index, 28) + 8;
        const int32_t requested_slot = static_cast<int32_t>(
            read_u32(at(next_sequence_word_address)));
        if (requested_slot == -1 || requested_slot == -3) {
            write_u8(object + 0x89, 1);
            return opaque_object;
        }

        // object+0x48 points to a lookup descriptor: byte length at +6,
        // pointer to 4-byte entries at +0x18. Each entry begins with s16 id.
        const uint32_t descriptor = read_u32(object + 0x48);
        const uint16_t byte_length = read_u16(at(descriptor) + 6);
        const uint32_t slot_count = static_cast<uint32_t>(byte_length) >> 2;
        uint32_t selected_entry = 0;
        const int16_t wanted_ordinal = static_cast<int16_t>(
            static_cast<uint16_t>(requested_slot));
        if (slot_count != 0) {
            const uint32_t lookup = read_u32(at(descriptor) + 0x18);
            uint32_t empty_count = 0;
            for (uint32_t i = 0; i < slot_count; ++i) {
                if (static_cast<int32_t>(empty_count) ==
                    static_cast<int32_t>(wanted_ordinal)) {
                    selected_entry = lookup + i * 4u;
                    break;
                }
                if (read_s16(at(lookup + i * 4u)) == -1)
                    ++empty_count;
            }
        }

        write_u32(object + 0x70, selected_entry);
        if (selected_entry == 0)
            return opaque_object;

        write_u16(object + 0x74, 0);
        write_u16(object + 0x76, 0);
        write_u8(object + 0x89, 0);
        write_u8(object + 0x8A, 0);
        write_u32(object + 4,
                  static_cast<uint32_t>(static_cast<int32_t>(
                      read_s16(at(selected_entry)))));
        write_u32(object + 8, 0xFFFFFFFFu);
        return at(reinterpret_cast<uintptr_t>(opaque_object) + 4);
    }

    if (next_track != -2) {
        write_u32(object + 4,
                  static_cast<uint32_t>(static_cast<int32_t>(next_track)));
        write_u32(object + 8, 0xFFFFFFFFu);
        return object + 4;
    }

    write_u16(object + 0x74, 0);
    const int16_t first_track = read_s16(at(current_table));
    write_u32(object + 4,
              static_cast<uint32_t>(static_cast<int32_t>(first_track)));
    write_u32(object + 8, 0xFFFFFFFFu);
    return object + 4;
}
