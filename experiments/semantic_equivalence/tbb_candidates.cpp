// Isolated TBB candidates. This translation unit is not part of the patch batch.
#include <stdint.h>

using u8 = uint8_t;
using u32 = uint32_t;
using u64 = uint64_t;

struct Tbl1Header {
    u32 magic;
    u32 payload_size;
    u32 row_stride;
    u32 reserved;
};

struct TbcrHeader {
    u32 magic;
    u32 header_size;
    u32 table_count;
    u32 table_offsets[1];
};

static constexpr u32 kTbcrMagic = 0x52434254;
static constexpr u32 kTbl1Magic = 0x314C4254;

extern "C" const void* candidate_002c0e9c(const Tbl1Header* table) {
    if (table == nullptr || table->magic != kTbl1Magic) {
        return nullptr;
    }
    return reinterpret_cast<const u8*>(table) + 0x10;
}

// Negative control: deliberately omit the TBL1 magic check.
extern "C" const void* wrong_tbb_payload_magic(const Tbl1Header* table) {
    if (table == nullptr) {
        return nullptr;
    }
    return reinterpret_cast<const u8*>(table) + 0x10;
}

extern "C" u32 candidate_002c0e4c(const Tbl1Header* table) {
    if (table == nullptr || table->magic != kTbl1Magic || table->row_stride == 0) {
        return 0;
    }

    const u32 numerator = table->payload_size;
    const u32 denominator = table->row_stride;
    u32 quotient = 0;
    u64 remainder = 0;
    for (u32 bit = 32; bit-- > 0;) {
        remainder = (remainder << 1) | ((numerator >> bit) & 1);
        if (remainder >= denominator) {
            remainder -= denominator;
            quotient |= 1u << bit;
        }
    }
    return quotient;
}

// Negative control: deliberately return the byte size instead of row count.
extern "C" u32 wrong_tbb_rowcount_divisor(const Tbl1Header* table) {
    if (table == nullptr || table->magic != kTbl1Magic || table->row_stride == 0) {
        return 0;
    }
    return table->payload_size;
}

extern "C" const Tbl1Header* candidate_002ac2f4(
    const TbcrHeader* container, u32 table_index) {
    if (container == nullptr || container->magic != kTbcrMagic ||
        container->table_count <= table_index) {
        return nullptr;
    }
    const u8* bytes = reinterpret_cast<const u8*>(container);
    const u32* offsets = reinterpret_cast<const u32*>(bytes + 0x0C);
    const u32 address = reinterpret_cast<u32>(container) + container->header_size +
                        offsets[table_index];
    if (address == 0) {
        return nullptr;
    }
    const Tbl1Header* table = reinterpret_cast<const Tbl1Header*>(address);
    return table->magic == kTbl1Magic ? table : nullptr;
}

// Negative control: omit the child TBL1 magic check.
extern "C" const Tbl1Header* wrong_tbb_subtable_magic(
    const TbcrHeader* container, u32 table_index) {
    if (container == nullptr || container->magic != kTbcrMagic ||
        container->table_count <= table_index) {
        return nullptr;
    }
    const u8* bytes = reinterpret_cast<const u8*>(container);
    const u32* offsets = reinterpret_cast<const u32*>(bytes + 0x0C);
    const u32 address = reinterpret_cast<u32>(container) + container->header_size +
                        offsets[table_index];
    return reinterpret_cast<const Tbl1Header*>(address);
}
