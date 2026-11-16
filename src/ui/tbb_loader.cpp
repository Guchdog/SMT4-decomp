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
s32 ui_func_002c6c10(s32 value, s32 divisor);

extern IfTouchGlobal g_IfTouchGlobal; // 0x0043DCB0
}

static u32 ReadU32LEAt(u32 address) {
    const auto* bytes = reinterpret_cast<const u8*>(address);
    return static_cast<u32>(bytes[0]) |
           (static_cast<u32>(bytes[1]) << 8) |
           (static_cast<u32>(bytes[2]) << 16) |
           (static_cast<u32>(bytes[3]) << 24);
}

// DECOMP_FUNC(0x002ac2f4, 92)
const Tbl1Header* Tbb_GetSubTable(const TbcrHeader* container, u32 table_index) {
    if (container == nullptr || container->magic != kTbcrMagic ||
        table_index >= container->table_count) {
        return nullptr;
    }

    // Keep address arithmetic in ARM's 32-bit domain. The original API has no
    // allocation length, so it cannot validate the trailing array or child.
    const u32 container_address = reinterpret_cast<u32>(container);
    const u32 offset_address = container_address + kTbcrOffsetsOffset +
                               (table_index << 2);
    const u32 child_address = container_address + container->header_size +
                              ReadU32LEAt(offset_address);
    if (child_address == 0 || ReadU32LEAt(child_address) != kTbl1Magic) {
        return nullptr;
    }
    return reinterpret_cast<const Tbl1Header*>(child_address);
}
// DECOMP_FUNC(0x002c0ec4, 28)
__attribute__((minsize)) const Tbl1Header* Tbb_GetGlobalSubTable(u32 slot_id, u32 table_index) {
    const TbcrHeader* container = nullptr;
    if (__builtin_expect(slot_id < 0x43u, 1)) {
        container = *reinterpret_cast<const TbcrHeader* const*>(0x00493830u + slot_id * 16);
    }
    return Tbb_GetSubTable(container, table_index);
}

// DECOMP_FUNC(0x002c0e9c, 40)
const void* Tbb_GetPayloadData(const Tbl1Header* table) {
    if (table == nullptr || table->magic != kTbl1Magic) {
        return nullptr;
    }
    const u32 payload_address = reinterpret_cast<u32>(table) + 0x10;
    return reinterpret_cast<const void*>(payload_address);
}
// DECOMP_FUNC(0x002c0e84, 24)
const void* Tbb_GetDefaultTable18Payload() {
    const Tbl1Header* table = Tbb_GetGlobalSubTable(0x18, 0);
    return Tbb_GetPayloadData(table);
}

// DECOMP_FUNC(0x002c0e4c, 56)
__attribute__((minsize)) u32 Tbb_GetRowCount(const Tbl1Header* table) {
    if (table == nullptr || table->magic != kTbl1Magic || table->row_stride == 0) {
        return 0;
    }
    return static_cast<u32>(ui_func_002c6c10(
        static_cast<s32>(table->payload_size), static_cast<s32>(table->row_stride)));
}
// DECOMP_FUNC(0x0010299c, 260)


// Original Atlus source: c:\SMT4\XRD686\sdds4\program\camp\IfTouch.cpp (line 364)
void IfTouch_Init() {
    auto* const global = reinterpret_cast<IfTouchGlobal*>(0x0043DCB0);
    if (global->ref_count <= 0) {
        IfTouchWork* work = global->work_ptr;
        if (work == nullptr) {
            work = reinterpret_cast<IfTouchWork*>(
                engine_func_002c4b84(0x100, 0x100, 0, sizeof(IfTouchWork), 1)
            );
            global->work_ptr = work;
        }
        engine_func_002c4b30(work, sizeof(IfTouchWork));

        void* const task = engine_func_002c5978(
            "TOUCH CALC",
            1,
            0,
            0,
            reinterpret_cast<void*>(IfTouch_CalcCallback_00107ccc),
            reinterpret_cast<void*>(IfTouch_ExitCallback_0010a28c),
            nullptr
        );
        work->calc_task_handle = task;
        work->active_panel_id = 0xFFFF;
        work->touch_timer = 10;
        work->touch_state = 0;
    }
    global->ref_count++;
}

} // namespace smt4::ui
