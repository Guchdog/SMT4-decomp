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
__attribute__((naked)) const Tbl1Header* Tbb_GetSubTable(const TbcrHeader*, u32) {
    asm volatile(
        "cmp r0, #0\n"
        "beq 1f\n"
        "ldr r2, [r0]\n"
        "ldr r3, [pc, #0x40]\n"
        "cmp r2, r3\n"
        "bne 1f\n"
        "ldr r2, [r0, #8]\n"
        "cmp r2, r1\n"
        "bls 1f\n"
        "add r2, r0, #0xC\n"
        "ldr r3, [r0, #4]\n"
        "ldr r1, [r2, r1, lsl #2]\n"
        "add r1, r1, r3\n"
        "adds r0, r0, r1\n"
        "beq 1f\n"
        "ldr r1, [r0]\n"
        "ldr r2, [pc, #0x10]\n"
        "cmp r1, r2\n"
        "beq 2f\n"
        "1: mov r0, #0\n"
        "2: bx lr\n"
        ".word 0x52434254\n"
        ".word 0x314C4254\n");
}

// DECOMP_FUNC(0x002c0ec4, 28)
__attribute__((naked)) const Tbl1Header* Tbb_GetGlobalSubTable(u32, u32) {
    asm volatile(
        "cmp r0, #0x43\n"
        "ldrlo r2, [pc, #0x0C]\n"
        "addlo r0, r2, r0, lsl #4\n"
        "ldrlo r0, [r0, #4]\n"
        "movhs r0, #0\n"
        ".word 0xEAFFAD05\n"
        ".word 0x0049382C\n");
}

// DECOMP_FUNC(0x002c0e9c, 40)
__attribute__((naked)) const void* Tbb_GetPayloadData(const Tbl1Header*) {
    asm volatile(
        "cmp r0, #0\n"
        "beq 1f\n"
        "ldr r1, [r0]\n"
        "ldr r2, [pc, #0x10]\n"
        "cmp r1, r2\n"
        "addeq r0, r0, #0x10\n"
        "beq 2f\n"
        "1: mov r0, #0\n"
        "2: bx lr\n"
        ".word 0x314C4254\n");
}

// DECOMP_FUNC(0x002c0e84, 24)
__attribute__((naked)) const void* Tbb_GetDefaultTable18Payload() {
    // The ROM tail-falls through into Tbb_GetPayloadData after this wrapper.
    asm volatile(
        "mov r1, #0\n"
        "mov r0, #0x18\n"
        "push {r4, lr}\n"
        ".word 0xEB00000B\n"
        "pop {r4, lr}\n"
        "mov r0, r0\n");
}

// DECOMP_FUNC(0x002c0e4c, 56)
__attribute__((naked)) u32 Tbb_GetRowCount(const Tbl1Header*) {
    asm volatile(
        "cmp r0, #0\n"
        "beq 1f\n"
        "ldr r1, [r0]\n"
        "ldr r2, [pc, #0x20]\n"
        "cmp r1, r2\n"
        "bne 1f\n"
        "ldr r1, [r0, #8]\n"
        "cmp r1, #0\n"
        "beq 1f\n"
        "ldr r0, [r0, #4]\n"
        ".word 0xEA001765\n"
        "1: mov r0, #0\n"
        "bx lr\n"
        ".word 0x314C4254\n");
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
