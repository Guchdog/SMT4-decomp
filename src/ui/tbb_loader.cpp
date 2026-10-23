#include "ui/tbb_table.h"

namespace smt4::ui {

extern "C" {
// BSS table of 67 (0x43) global TBB table slots at 0x0049382C
extern GlobalTbbSlot g_GlobalTbbSlots[kMaxGlobalTbbSlots]; // 0x0049382C

// Engine memory and task creation functions (AsdSDK)
void* engine_func_002c4b84(
    u32 align, u32 heap_id, u32 zero_flag, u32 size, u32 flags);
void engine_func_002c4b30(void* ptr, u32 size);
void* engine_func_002c5978(
    const char* name,
    u32 prio,
    u32 arg2,
    u32 arg3,
    void* calc_cb,
    void* draw_cb,
    void* user_data
);
void IfTouch_CalcCallback_00107ccc();
void IfTouch_ExitCallback_0010a28c();

extern IfTouchGlobal g_IfTouchGlobal; // 0x0043DCB0
}

// DECOMP_FUNC(0x002ac2f4, 92)
const Tbl1Header* Tbb_GetSubTable(const TbcrHeader* container, u32 table_index) {
    if (container == nullptr || container->magic != kTbcrMagic) {
        return nullptr;
    }
    if (table_index >= container->table_count) {
        return nullptr;
    }

    const u32 rel_offset = container->table_offsets[table_index] + container->header_size;
    // The original adds this relative offset to the base address, then rejects
    // a null result (including 32-bit address wraparound), not a zero offset.
    const u32 sub_tbl_addr = reinterpret_cast<u32>(container) + rel_offset;
    if (sub_tbl_addr == 0) {
        return nullptr;
    }

    const auto* sub_tbl = reinterpret_cast<const Tbl1Header*>(sub_tbl_addr);
    if (sub_tbl->magic != kTbl1Magic) {
        return nullptr;
    }
    return sub_tbl;
}

// DECOMP_FUNC(0x002c0ec4, 28)
const Tbl1Header* Tbb_GetGlobalSubTable(u32 slot_id, u32 table_index) {
    const TbcrHeader* container = nullptr;
    if (slot_id < kMaxGlobalTbbSlots) {
        container = g_GlobalTbbSlots[slot_id].container;
    }
    return Tbb_GetSubTable(container, table_index);
}

// DECOMP_FUNC(0x002c0e9c, 40)
const void* Tbb_GetPayloadData(const Tbl1Header* tbl) {
    if (tbl != nullptr && tbl->magic == kTbl1Magic) {
        return reinterpret_cast<const u8*>(tbl) + sizeof(Tbl1Header);
    }
    return nullptr;
}

// DECOMP_FUNC(0x002c0e84, 24)
const void* Tbb_GetDefaultTable18Payload() {
    const Tbl1Header* tbl = Tbb_GetGlobalSubTable(0x18, 0);
    return Tbb_GetPayloadData(tbl);
}

// DECOMP_FUNC(0x002c0e4c, 56)
u32 Tbb_GetRowCount(const Tbl1Header* tbl) {
    if (tbl == nullptr || tbl->magic != kTbl1Magic || tbl->row_stride == 0) {
        return 0;
    }
    return tbl->payload_size / tbl->row_stride;
}

// DECOMP_FUNC(0x0010299c, 260)
// Original Atlus source: c:\SMT4\XRD686\sdds4\program\camp\IfTouch.cpp (line 364)
void IfTouch_Init() {
    if (g_IfTouchGlobal.ref_count <= 0) {
        IfTouchWork* work = g_IfTouchGlobal.work_ptr;
        if (work == nullptr) {
            work = static_cast<IfTouchWork*>(
                engine_func_002c4b84(0x100, 0x100, 0, sizeof(IfTouchWork), 1)
            );
            g_IfTouchGlobal.work_ptr = work;
        }
        engine_func_002c4b30(work, sizeof(IfTouchWork));
        work->calc_task_handle = engine_func_002c5978(
            "TOUCH CALC",
            1,
            0,
            0,
            reinterpret_cast<void*>(&IfTouch_CalcCallback_00107ccc),
            reinterpret_cast<void*>(&IfTouch_ExitCallback_0010a28c),
            nullptr
        );
        work->touch_timer = 10;
        work->touch_state = 0;
        work->active_panel_id = 0xFFFF;
    }
    g_IfTouchGlobal.ref_count++;
}

} // namespace smt4::ui
