#pragma once

#include "types.h"

namespace smt4::ui {

constexpr u32 kTbcrMagic = 0x52434254; // 'TBCR'
constexpr u32 kTbl1Magic = 0x314C4254; // 'TBL1'
constexpr u32 kMaxGlobalTbbSlots = 0x43;

struct Tbl1Header {
    u32 magic;        // +0x00: 'TBL1' (0x314C4254)
    u32 payload_size; // +0x04: Total byte size of payload rows
    u32 row_stride;   // +0x08: Byte stride per row (0 if single struct)
    u32 reserved;     // +0x0C: Alignment / flags (typically 0x10)
};

struct TbcrHeader {
    u32 magic;            // +0x00: 'TBCR' (0x52434254)
    u32 header_size;      // +0x04: Offset to first table base
    u32 table_count;      // +0x08: Number of TBL1 sub-tables
    u32 table_offsets[1]; // +0x0C: Sub-table offsets relative to header_size
};

struct GlobalTbbSlot {
    u32 flags;                   // +0x00
    const TbcrHeader* container; // +0x04
    u32 reserved0;               // +0x08
    u32 reserved1;               // +0x0C
};

// Decompiled UI / TBB functions from code.bin
const Tbl1Header* Tbb_GetSubTable(const TbcrHeader* container, u32 table_index);
const Tbl1Header* Tbb_GetGlobalSubTable(u32 slot_id, u32 table_index);
const void* Tbb_GetPayloadData(const Tbl1Header* tbl);
const void* Tbb_GetDefaultTable18Payload();
u32 Tbb_GetRowCount(const Tbl1Header* tbl);

// Camp / Bottom-Screen Touch Input Controller (c:\SMT4\XRD686\sdds4\program\camp\IfTouch.cpp)
struct IfTouchWork {
    void* calc_task_handle; // +0x000
    u8 pad_004[0x646];      // +0x004
    u16 touch_timer;        // +0x64A
    u16 touch_state;        // +0x64C
    u16 active_panel_id;    // +0x64E
    u8 pad_650[0x30];       // +0x650..0x680
};

struct IfTouchGlobal {
    s8 ref_count;          // +0x00
    u8 pad[3];             // +0x01
    IfTouchWork* work_ptr; // +0x04
};

void IfTouch_Init();

} // namespace smt4::ui
