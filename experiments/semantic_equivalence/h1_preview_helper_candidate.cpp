// Readable experimental reconstruction of ARM function 0x002BF9F0.
// The pointed-to bytes are an opaque helper object; the nested row and sequence
// arrays are caller-owned and have no length checks in the original body.
#include <stdint.h>

extern "C" void camp_func_002bdac0(void* object, int32_t animation, int32_t frame);
extern "C" int32_t ui_func_002c615c(int32_t delta_12_12, uint32_t duration);
extern "C" void ui_func_002b1fc0(void* object);
extern "C" void ui_func_002b1dfc(void* object);
extern "C" void ui_func_002b1c8c(void* object);

namespace {
static int16_t read_s16(const uint8_t* p) {
    uint16_t value = static_cast<uint16_t>(p[0]) |
                     (static_cast<uint16_t>(p[1]) << 8);
    return static_cast<int16_t>(value);
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
static uint32_t fixed12(int16_t value) {
    return static_cast<uint32_t>(static_cast<int32_t>(value)) << 12;
}
static void set_endpoint(uint8_t* object, const uint8_t* row,
                         unsigned x_offset, unsigned y_offset) {
    write_u32(object + 0x0C, fixed12(read_s16(row + x_offset)));
    write_u32(object + 0x10, fixed12(read_s16(row + y_offset)));
}
static void interpolate(uint8_t* object, const uint8_t* row,
                        unsigned from_x, unsigned to_x,
                        unsigned from_y, unsigned to_y) {
    const uint32_t duration = read_u16(row + 8);
    const int32_t dx = static_cast<int32_t>(read_s16(row + from_x)) -
                       static_cast<int32_t>(read_s16(row + to_x));
    const int32_t dy = static_cast<int32_t>(read_s16(row + from_y)) -
                       static_cast<int32_t>(read_s16(row + to_y));
    const int32_t step_x = ui_func_002c615c(static_cast<int32_t>(static_cast<uint32_t>(dx) << 12), duration);
    write_u32(object + 0x0C, read_u32(object + 0x0C) + static_cast<uint32_t>(step_x));
    const int32_t step_y = ui_func_002c615c(static_cast<int32_t>(static_cast<uint32_t>(dy) << 12), duration);
    write_u32(object + 0x10, read_u32(object + 0x10) + static_cast<uint32_t>(step_y));
}
} // namespace

extern "C" int32_t h1_preview_helper_candidate(void* opaque) {
    if (!opaque) return 1;
    auto* object = static_cast<uint8_t*>(opaque);

    if (static_cast<int32_t>(read_u32(object + 4)) < 0 &&
        static_cast<int32_t>(read_u32(object + 8)) < 0) return 1;

    if (object[0x86] == 0) {
        const uint32_t table_address = read_u32(object + 0x4C);
        if (table_address != 0) {
            auto* table = reinterpret_cast<const uint8_t*>(static_cast<uintptr_t>(table_address));
            const int32_t row_index = read_s16(object + 0x50);
            const auto row_delta = static_cast<intptr_t>(row_index) * 12;
            const uint8_t* row = table + row_delta;
            const int16_t progress = read_s16(object + 0x52);
            const uint16_t duration = read_u16(row + 8);

            if (static_cast<int32_t>(duration) > progress) {
                if (object[0x54] != 0) interpolate(object, row, 0, 4, 2, 6);
                else interpolate(object, row, 4, 0, 6, 2);
                write_u16(object + 0x52, static_cast<uint16_t>(read_u16(object + 0x52) + 1));
            } else {
                const uint8_t row_mode = row[0x0A];
                const uint8_t direction = object[0x54];
                if (row_mode != 0) {
                    if (direction != 0) set_endpoint(object, row, 4, 6);
                    else set_endpoint(object, row, 0, 2);
                } else {
                    if (direction != 0) set_endpoint(object, row, 0, 2);
                    else set_endpoint(object, row, 4, 6);
                }
                write_u16(object + 0x52, 0);

                if (row_mode == 0 && object[0x84] != 0) {
                    const uint32_t sequence_address = read_u32(object + 0x78);
                    if (sequence_address != 0) {
                        auto* sequence = reinterpret_cast<const uint8_t*>(static_cast<uintptr_t>(sequence_address));
                        const int32_t index = read_s16(object + 0x7C);
                        const uint8_t* entry = sequence + static_cast<intptr_t>(index) * 0x1C;
                        const int32_t first = static_cast<int32_t>(read_u32(entry));
                        if (first == -1) {
                            object[0x86] = 1;
                        } else {
                            write_u16(object + 0x7C, static_cast<uint16_t>(index + 1));
                            const int32_t next_index = static_cast<int16_t>(read_u16(object + 0x7C));
                            const uint8_t* next = sequence + static_cast<intptr_t>(next_index) * 0x1C;
                            const int32_t next_word = static_cast<int32_t>(read_u32(next));
                            if (next_word == -1 || next_word == -3) {
                                object[0x86] = 1;
                            } else if (next_word == -2) {
                                write_u16(object + 0x7C, 0);
                                const int32_t animation = static_cast<int16_t>(read_u32(sequence));
                                const int32_t frame = static_cast<int8_t>(sequence[4]);
                                camp_func_002bdac0(object, animation, frame);
                            } else {
                                const int32_t animation = static_cast<int16_t>(next_word);
                                const int32_t frame = static_cast<int8_t>(next[4]);
                                camp_func_002bdac0(object, animation, frame);
                            }
                        }
                    } else {
                        object[0x86] = 1;
                    }
        } else if (row_mode == 0) {
                    // The original conditional-load chain branches to the
                    // same completion path when the sequence feature is off.
                    object[0x86] = 1;
                }
            }
        }
    }

    ui_func_002b1fc0(object);
    ui_func_002b1dfc(object);
    ui_func_002b1c8c(object);
    object[0x8A] = (object[0x86] && object[0x87] && object[0x88] && object[0x89]) ? 1 : 0;
    const int32_t result = static_cast<int8_t>(object[0x8A]);
    object[0x85] = 1;
    return result;
}
