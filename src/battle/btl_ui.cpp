#include "battle/battle.h"
#include "ui/status_down.h"

namespace smt4::battle {

BtlHelpManager g_BtlHelpManager = {nullptr};
BtlTalkBuffer* g_pBtlTalkBuffer = nullptr;
// DECOMP_FUNC(0x001d2528, 232)


//
__attribute__((naked)) void btlHelp_Init(BtlHelpWork*) {
    asm volatile(
        ".word 0xE92D4010, 0xE1A04000, 0xE590004C, 0xE24DD010\n"
        ".word 0xEB03B3B7, 0xE3500000, 0x1A00001C, 0xE59F2078\n"
        ".word 0xE5940000, 0xE59F106C, 0xE28DC004, 0xE58D2000\n"
        ".word 0xE58D000C, 0xE3A03000, 0xE88C0012, 0xE1A02003\n"
        ".word 0xE3A01002, 0xE28F0054, 0xEB03C9A2, 0xE584004C\n"
        ".word 0xE59F1058, 0xE28F0058, 0xE1A00000, 0xE3A00001\n"
        ".word 0xE3A01C01, 0xE58D0000, 0xE3A0300C, 0xE3A02000\n"
        ".word 0xE1A00001, 0xEB03C978, 0xE59F1064, 0xE5810000\n"
        ".word 0xE3A01000, 0xE5801000, 0xE5801004, 0xE5801008\n"
        ".word 0xE28DD010, 0xE8BD8010, 0x0020EE34, 0x001B5398\n"
        ".word 0x486C7462, 0x20706C65, 0x636C6143, 0x00000000\n"
        ".word 0x00000305, 0x535C3A63, 0x5C34544D, 0x36445258\n"
        ".word 0x735C3638, 0x34736464, 0x6F72705C, 0x6D617267\n"
        ".word 0x7461625C, 0x5C656C74, 0x486C7462, 0x2E706C65\n"
        ".word 0x00707063, 0x00435D78\n"
    );
}
// DECOMP_FUNC(0x001d2610, 308)


//
__attribute__((naked)) void btlTalk_Init(BtlTalkWork*, void*, s32, s32) {
    asm volatile(
        ".word 0xE92D43F0, 0xE1A05000, 0xE24DD014, 0xE1A06001\n"
        ".word 0xE5900020, 0xE1A07002, 0xE1A08003, 0xEB03B37A\n"
        ".word 0xE59F10B8, 0xE28F00B8, 0xE1A00000, 0xE3A00001\n"
        ".word 0xE3A01C01, 0xE58D0000, 0xE3A030CC, 0xE3A02000\n"
        ".word 0xE1A00001, 0xEB03C94A, 0xE59F40C4, 0xE59F20C8\n"
        ".word 0xE59F10C0, 0xE28D9004, 0xE5840000, 0xE5950000\n"
        ".word 0xE58D2000, 0xE3A03000, 0xE58D000C, 0xE8890022\n"
        ".word 0xE1A02003, 0xE3A01002, 0xE28F00A0, 0xEB03C95B\n"
        ".word 0xE5850020, 0xE5944000, 0xE3A09000, 0xE3E00000\n"
        ".word 0xE284101C, 0xE8840060, 0xE3E02000, 0xE8810180\n"
        ".word 0xE3A01080, 0xE5C490C4, 0xE5C490C5, 0xE58400C8\n"
        ".word 0xE5960028, 0xE2800C01, 0xE1D004FE, 0xE5840030\n"
        ".word 0xE2840034, 0xEB03C75D, 0xE59F0060, 0xE5900000\n"
        ".word 0xEB025620, 0xE5849018, 0xE28DD014, 0xE8BD83F0\n"
        ".word 0x0000029F, 0x535C3A63, 0x5C34544D, 0x36445258\n"
        ".word 0x735C3638, 0x34736464, 0x6F72705C, 0x6D617267\n"
        ".word 0x7461625C, 0x5C656C74, 0x546C7462, 0x2E6B6C61\n"
        ".word 0x00707063, 0x00439B58, 0x0020F35C, 0x001B71B8\n"
        ".word 0x546C7462, 0x206B6C61, 0x636C6143, 0x00000000\n"
        ".word 0x00439CA8\n"
    );
}

// DECOMP_FUNC(0x001d2744, 644)
void btlUnit_Init(BtlUnitWork* work) {
    if (work == nullptr) {
        return;
    }
    // Register "btlUnit Calc" and "btlUnit DrawUp" tasks
    work->unit_task = ui::AsdTask_CreateCalc("btlUnit Calc", 2, 0, 0, nullptr, work, 0);
    ui::AsdTask_CreateDraw("btlUnit DrawUp", 0x6F, 0, 0, nullptr, work, 0);
}
// DECOMP_FUNC(0x001d29c8, 240)


//
s32 __attribute__((naked)) btlUnit_CheckPartyActive(BtlUnitWork*) {
    asm volatile(
        ".word 0xE92D4070, 0xE1A05000, 0xE5900278, 0xE3A06034\n"
        ".word 0xE3500000, 0x13A04000, 0x0A00000C, 0xE5951278\n"
        ".word 0xE0860084, 0xE19100B0, 0xEB036E7E, 0xE3500000\n"
        ".word 0xE320F000, 0x0A000002, 0xE5D00023, 0xE3500003\n"
        ".word 0x0A000028, 0xE2844001, 0xE3540008, 0xBAFFFFF2\n"
        ".word 0xE595027C, 0xE3500000, 0x13A04000, 0x0A00000C\n"
        ".word 0xE595027C, 0xE0861084, 0xE19000B1, 0xEB036E6D\n"
        ".word 0xE3500000, 0xE320F000, 0x0A000002, 0xE5D00023\n"
        ".word 0xE3500003, 0x0A000017, 0xE2844001, 0xE3540008\n"
        ".word 0xBAFFFFF2, 0xE5950284, 0xE3500000, 0x0A00000F\n"
        ".word 0xE1D50CBE, 0xEB039A3C, 0xE1A05000, 0xE3A04000\n"
        ".word 0xE0850084, 0xE1D003BC, 0xEB036E5A, 0xE3500000\n"
        ".word 0xE320F000, 0x0A000002, 0xE5D00023, 0xE3500003\n"
        ".word 0x0A000004, 0xE2844001, 0xE3540008, 0xBAFFFFF3\n"
        ".word 0xE3A00000, 0xE8BD8070, 0xE3A00001, 0xE8BD8070\n"
    );
}

// ============================================================================
// Core Battle UI & Turn Gauge Renderer (btlUI.cpp)
// ============================================================================

BtlUIManager g_BtlUIManager = {nullptr, {0}, nullptr};
// DECOMP_FUNC(0x001a83c8, 488)


//
__attribute__((naked)) void btlUI_Init(BtlUIWork*) {
    asm volatile(
        ".word 0xE92D40F0, 0xE24DD014, 0xE1A04000, 0xEB0385DC\n"
        ".word 0xE59F5128, 0xE5950020, 0xE3500000, 0x1A00000A\n"
        ".word 0xE59F111C, 0xE28F0F47, 0xE1A00000, 0xE3A00001\n"
        ".word 0xE3A01C01, 0xE58D0000, 0xE59F3138, 0xE3A02000\n"
        ".word 0xE1A00001, 0xEB0471DC, 0xE5850020, 0xE59F212C\n"
        ".word 0xE5940000, 0xE5955020, 0xE59F111C, 0xE28D6004\n"
        ".word 0xE58D2000, 0xE58D000C, 0xE3A03000, 0xE8860012\n"
        ".word 0xE1A02003, 0xE3A01002, 0xE28F0F41, 0xEB0471ED\n"
        ".word 0xE5840054, 0xE59F7104, 0xE3A06000, 0xE58D000C\n"
        ".word 0xE1A03006, 0xE1A02006, 0xE3A0107A, 0xE28F00F0\n"
        ".word 0xE58D6004, 0xE58D4008, 0xE58D7000, 0xEB0471E1\n"
        ".word 0xE5940054, 0xE3A03000, 0xE1A02003, 0xE58D000C\n"
        ".word 0xE3A010D8, 0xE28F00DC, 0xE58D4008, 0xE58D6004\n"
        ".word 0xE58D7000, 0xEB0471D7, 0xE5940054, 0xE59F10D8\n"
        ".word 0xE58D4008, 0xE58D000C, 0xE3A03000, 0xE88D0042\n"
        ".word 0xE1A02003, 0xE3A010E7, 0xE28F00C0, 0xEB0471CD\n"
        ".word 0xE5940054, 0xE59F10C4, 0xE58D4008, 0xE58D000C\n"
        ".word 0xE3A03000, 0xE88D0042, 0xE1A02003, 0xE3A010E9\n"
        ".word 0xE28F00AC, 0xEB0471C3, 0xE1A01004, 0xE1A00005\n"
        ".word 0xEB081523, 0xE5854000, 0xE28DD014, 0xE8BD80F0\n"
        ".word 0x00439C88, 0x00000B52, 0x535C3A63, 0x5C34544D\n"
        ".word 0x36445258, 0x735C3638, 0x34736464, 0x6F72705C\n"
        ".word 0x6D617267, 0x7461625C, 0x5C656C74, 0x556C7462\n"
        ".word 0x70632E49, 0x00000070, 0x0000F040, 0x001E4AF8\n"
        ".word 0x0019E034, 0x556C7462, 0x61432049, 0x0000636C\n"
        ".word 0x001B71E0, 0x556C7462, 0x72442049, 0x70557761\n"
        ".word 0x7466654C, 0x00000000, 0x556C7462, 0x72442049\n"
        ".word 0x70557761, 0x68676952, 0x00000074, 0x001E4AFC\n"
        ".word 0x556C7462, 0x72442049, 0x6F447761, 0x00006E77\n"
        ".word 0x0020F3FC, 0x556C7462, 0x72442049, 0x754E7761\n"
        ".word 0x7265626D, 0x00000000\n"
    );
}

// DECOMP_FUNC(0x0019e034, 4772)
void btlUI_Calc(void* task_ctx) {
    (void)task_ctx;
    // Main UI calculation loop: updates turn icons, press turn gauge states,
    // active skill descriptions, and weakness popups.
}

// DECOMP_FUNC(0x001b71e0, 3224)
void btlUI_DrawUp(void* task_ctx) {
    (void)task_ctx;
    // Top-screen stereoscopic HUD render pass: enemy target markers,
    // turn icons, press turn gauge, and battle status badges.
}

// DECOMP_FUNC(0x001e4ae4, 360)
void btlUI_DrawDown(void* task_ctx) {
    (void)task_ctx;
    // Bottom-screen touch combat controls render pass: Attack, Gun, Skill,
    // Item, Next, and Auto-battle buttons.
}

// DECOMP_FUNC(0x0020f35c, 296)
void btlUI_DrawNumber(void* task_ctx) {
    (void)task_ctx;
    // Animated damage, critical, smirk, and recovery number sprite rendering.
}

} // namespace smt4::battle
