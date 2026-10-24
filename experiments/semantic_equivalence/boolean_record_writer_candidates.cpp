#include <stdint.h>

using u8 = uint8_t;
using u32 = uint32_t;

// Faithful only to the bounded ordinary-RAM contract pinned by the runner.
// Each volatile access remains a separate operation so partial commits and
// observable access order are not folded into a higher-level struct update.
#define DEFINE_BOOLEAN_RECORD_WRITER(name, byte_value, final_cursor_bump)       \
    extern "C" __attribute__((noinline, used)) u32 name(u8* base) {           \
        const uintptr_t b = reinterpret_cast<uintptr_t>(base);                 \
        volatile u32* cursor = reinterpret_cast<volatile u32*>(b + 0x18);     \
        u32 next = *cursor + 1;                                                \
        *cursor = next;                                                        \
        u32* volatile* table_cell = reinterpret_cast<u32* volatile*>(          \
            b + 0xBC);                                                         \
        u32* table = *table_cell;                                              \
        volatile u32* index_cell = reinterpret_cast<volatile u32*>(            \
            b + 0x1C);                                                         \
        u32 first_index = *index_cell;                                         \
        const uintptr_t table_address = reinterpret_cast<uintptr_t>(table);     \
        u32 value = *reinterpret_cast<volatile u32*>(                           \
            table_address + static_cast<uintptr_t>(next) * 4);                  \
        *reinterpret_cast<volatile u8*>(b + 0x20 + first_index) =              \
            static_cast<u8>(byte_value);                                       \
        u32 second_index = *index_cell;                                        \
        *reinterpret_cast<volatile u32*>(b + second_index * 4 + 0x3C) =        \
            value;                                                             \
        u32 third_index = *index_cell;                                         \
        *index_cell = third_index + 1;                                         \
        if (final_cursor_bump) {                                               \
            u32 last_cursor = *cursor;                                         \
            *cursor = last_cursor + 1;                                         \
        }                                                                      \
        return 1;                                                              \
    }

DEFINE_BOOLEAN_RECORD_WRITER(candidate_001aa094, 1, 1)
DEFINE_BOOLEAN_RECORD_WRITER(candidate_001aa0ec, 0, 1)

// Negative controls intentionally alter one pinned effect each.
DEFINE_BOOLEAN_RECORD_WRITER(negative_wrong_boolean_value, 1, 1)
DEFINE_BOOLEAN_RECORD_WRITER(negative_missing_final_cursor_bump, 0, 0)
