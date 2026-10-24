// Experimental reconstructions. These do not replace matching source/ledger entries.
#include <stdint.h>

using u8 = uint8_t;
using s8 = int8_t;
using u16 = uint16_t;
using u32 = uint32_t;
using s32 = int32_t;

// Test fixture includes accessible payload, so bounded pointer arithmetic stays
// within the object representation. This does not assert a recovered game size.
struct RelativeRecord { u8 prefix[0x18]; u32 offset; u8 payload[0x800]; };
static_assert(sizeof(void*) == 4);

extern "C" const u8* candidate_00128f34(const RelativeRecord* object) {
    return reinterpret_cast<const u8*>(object) + 8 + object->offset;
}

extern "C" u32 candidate_002ae464(u32 value) {
    return value > 400u;
}

extern "C" u32 candidate_00394614(const u8* byte) {
    return *byte == 0x68;
}

extern "C" u32 candidate_0038143c(u16** cursor) {
    const u16 value = **cursor;
    ++*cursor;
    return value;
}

extern "C" u32 candidate_00381450(u8** cursor) {
    const u8 value = **cursor;
    ++*cursor;
    return value;
}

struct Triple { u32 words[3]; };
struct CopyRecord { Triple destination; Triple source; };

extern "C" CopyRecord* candidate_003d7228(CopyRecord* record) {
    record->destination = record->source;
    return record; // Preserve original r0 even if a caller consumes it.
}

struct StateRecord {
    u8 prefix[0x15];
    u8 enabled;
    u8 reserved;
    u8 reset;
    u8 padding[8];
    u16 flags;
};
static_assert(__builtin_offsetof(StateRecord, flags) == 0x20);

extern "C" StateRecord* candidate_0037c46c(StateRecord* record) {
    const u16 flags = record->flags;
    record->enabled = 1;
    record->reset = 0;
    record->flags = flags | 1u;
    return record;
}

struct SignedByteRecord { u8 prefix[0x330]; s8 value; };
static_assert(__builtin_offsetof(SignedByteRecord, value) == 0x330);

extern "C" s32 candidate_00121d70(const SignedByteRecord* record) {
    return record->value;
}

struct NullablePointerRecord { u8 prefix[0x1c]; void* value; };
static_assert(__builtin_offsetof(NullablePointerRecord, value) == 0x1c);

extern "C" void* candidate_0014ec5c(const NullablePointerRecord* record) {
    return record == nullptr ? nullptr : record->value;
}

struct PairStoreRecord { u32 prefix; u32 first; u32 second; };
static_assert(__builtin_offsetof(PairStoreRecord, first) == 4);

extern "C" PairStoreRecord* candidate_00131414(
    PairStoreRecord* record, u32 first, u32 second) {
    record->first = first;
    record->second = second;
    return reinterpret_cast<PairStoreRecord*>(
        reinterpret_cast<u8*>(record) + 4);
}

// Deliberate bugs: the oracle must reject every control below.
extern "C" u32 wrong_threshold(u32 value) { return value >= 400u; }
extern "C" u32 wrong_byte(const u8* value) { return *value == 0x69; }
extern "C" u32 wrong_cursor(u8** cursor) {
    const u8 value = **cursor;
    *cursor += 2;
    return value;
}
extern "C" u32 wrong_cursor_order(u8** cursor) {
    const u8* previous = *cursor;
    ++*cursor;
    return *previous; // Changes results when previous aliases the pointer cell.
}
extern "C" void wrong_state(StateRecord* record) {
    record->enabled = 1;
    record->reset = 0;
    record->flags |= 2u;
}
extern "C" u32 wrong_abi(u32 value) {
    // Deliberately break a callee-saved register to exercise the ABI checker.
    // This assembly is a negative test, never a proposed reconstruction.
    __asm__ volatile("mov r4, #0");
    return value > 400u;
}

extern "C" u32 wrong_signed_byte(const SignedByteRecord* record) {
    return static_cast<u8>(record->value);
}

extern "C" void* wrong_nullable_pointer(const NullablePointerRecord* record) {
    return const_cast<NullablePointerRecord*>(record);
}

extern "C" PairStoreRecord* wrong_pair_store(
    PairStoreRecord* record, u32 first, u32 second) {
    record->first = first;
    record->second = second ^ 1u;
    return reinterpret_cast<PairStoreRecord*>(
        reinterpret_cast<u8*>(record) + 4);
}
