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
const void* Tbb_GetPayloadData(const Tbl1Header* table) {
    if (table == nullptr || table->magic != kTbl1Magic) {
        return nullptr;
    }
    const u32 payload_address = reinterpret_cast<u32>(table) + 0x10;
    return reinterpret_cast<const void*>(payload_address);
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


//
// Original Atlus source: c:\SMT4\XRD686\sdds4\program\camp\IfTouch.cpp (line 364)
__attribute__((naked)) void IfTouch_Init() {
    asm volatile(
        ".arm\n"
        "push {r4, r5, r6, lr}\n"
        "sub sp, sp, #0x10\n"
        "ldr r5, [pc, #0xac]\n"
        "ldrsb r0, [r5]\n"
        "cmp r0, #0\n"
        "bgt .L_if_touch_count_done\n"
        "ldr r0, [r5, #4]\n"
        "cmp r0, #0\n"
        "bne .L_if_touch_work_ready\n"
        "mov r1, #0x16c\n"
        "add r0, pc, #0x90\n"
        "mov r0, r0\n"
        "mov r0, #1\n"
        "mov r1, #0x100\n"
        "str r0, [sp]\n"
        "mov r3, #0x680\n"
        "mov r2, #0\n"
        "mov r0, r1\n"
        ".word 0xeb070866\n"
        "str r0, [r5, #4]\n"
        ".L_if_touch_work_ready:\n"
        "mov r4, r0\n"
        "mov r1, #0x680\n"
        ".word 0xeb07084d\n"
        "ldr r1, [pc, #0x90]\n"
        "ldr r0, [pc, #0x88]\n"
        "mov r6, #0\n"
        "add ip, sp, #4\n"
        "str r1, [sp]\n"
        "stm ip, {r0, r6}\n"
        "mov r3, r6\n"
        "mov r2, r6\n"
        "mov r1, #1\n"
        "add r0, pc, #0x70\n"
        ".word 0xeb070bd4\n"
        "mov r1, r0\n"
        "add r0, r4, #0x600\n"
        "mvn r3, #0\n"
        "str r1, [r4]\n"
        "mov r2, #0xa\n"
        "strh r3, [r0, #0x4e]\n"
        "strh r2, [r0, #0x4a]\n"
        "strh r6, [r0, #0x4c]\n"
        ".L_if_touch_count_done:\n"
        "ldrb r0, [r5]\n"
        "add r0, r0, #1\n"
        "strb r0, [r5]\n"
        "add sp, sp, #0x10\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x0043dcb0\n"
        ".byte 0x63, 0x3a, 0x5c, 0x53, 0x4d, 0x54, 0x34, 0x5c\n"
        ".byte 0x58, 0x52, 0x44, 0x36, 0x38, 0x36, 0x5c, 0x73\n"
        ".byte 0x64, 0x64, 0x73, 0x34, 0x5c, 0x70, 0x72, 0x6f\n"
        ".byte 0x67, 0x72, 0x61, 0x6d, 0x5c, 0x63, 0x61, 0x6d\n"
        ".byte 0x70, 0x5c, 0x49, 0x66, 0x54, 0x6f, 0x75, 0x63\n"
        ".byte 0x68, 0x2e, 0x63, 0x70, 0x70, 0x00, 0x00, 0x00\n"
        ".word 0x0010a28c\n"
        ".word 0x00107ccc\n"
        ".asciz \"TOUCH CALC\"\n"
        ".balign 4\n");
}

} // namespace smt4::ui
