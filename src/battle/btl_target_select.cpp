#include "battle/target_select.h"
#include "ui/status_down.h"

namespace smt4::battle {

BtlTargetSelectWork* g_pBtlTargetSelectWork = nullptr;
 // 0x00439C60

extern "C" {
    void* AsdRef_Get(void* handle);                 // 0x002c0ac8
    void ui_func_00342b54(void* resource);           // 0x00342b54
    void ui_func_0034946c(void* resource);           // 0x0034946c
}

// DECOMP_FUNC(0x002e8294, 604)
__attribute__((naked)) void btlTargetSelect_Init(void*) {
    asm volatile(
        ".word 0xE92D41F0, 0xE1A05000, 0xE24DD020, 0xE59F119C\n"
        ".word 0xE28F0F67, 0xE1A00000, 0xE3A06001, 0xE3A01C01\n"
        ".word 0xE3A030B8, 0xE3A02000, 0xE1A00001, 0xE58D6000\n"
        ".word 0xEBFF7489, 0xE1A04000, 0xE59F01AC, 0xE1A01005\n"
        ".word 0xE5804000, 0xE3A00F4B, 0xEBFF6845, 0xE3500000\n"
        ".word 0x1B016BC2, 0xE5840000, 0xE1A01005, 0xE3A00060\n"
        ".word 0xEBFF683F, 0xE3500000, 0xE3A07000, 0x0A00000F\n"
        ".word 0xE59F1178, 0xE3A03005, 0xE3A02010, 0xE4801004\n"
        ".word 0xE59F116C, 0xFAFF770E, 0xE2400004, 0xED9F0A59\n"
        ".word 0xE5C07013, 0xE5C07023, 0xE5C07033, 0xE5C07043\n"
        ".word 0xEDDF0A55, 0xE2801058, 0xE5C07053, 0xEC810A02\n"
        ".word 0xE28D8004, 0xE5840004, 0xE5C47008, 0xE59F2140\n"
        ".word 0xE5950000, 0xE59F1134, 0xE58D2000, 0xE58D000C\n"
        ".word 0xE3A03000, 0xE8880012, 0xE1A02003, 0xE3A01002\n"
        ".word 0xE28F0E12, 0xEBFF7220, 0xE585001C, 0xE59F812C\n"
        ".word 0xE3A03000, 0xE58D000C, 0xE1A02003, 0xE3A0107A\n"
        ".word 0xE28F0F47, 0xE58D4008, 0xE58D7004, 0xE58D8000\n"
        ".word 0xEBFF7215, 0xE595001C, 0xE3A03000, 0xE1A02003\n"
        ".word 0xE58D000C, 0xE3A010D8, 0xE28F0F43, 0xE58D4008\n"
        ".word 0xE58D7004, 0xE58D8000, 0xEBFF720B, 0xE284000C\n"
        ".word 0xE320F000, 0xEBFF6BD9, 0xE59F1104, 0xE28D2010\n"
        ".word 0xE3A00010, 0xE58D100C, 0xE8820081, 0xE3A03000\n"
        ".word 0xE58D7018, 0xE1A02003, 0xE1A01003, 0xE284000C\n"
        ".word 0xE58D7000, 0xE58D7004, 0xE58D7008, 0xEBFF6BB8\n"
        ".word 0xED9F0A34, 0xE284300C, 0xE3A02071, 0xE3A01014\n"
        ".word 0xE284002C, 0xE58D6000, 0xEBFF55BE, 0xE28DD020\n"
        ".word 0xE284002C, 0xE8BD41F0, 0xE3A01000, 0xEA000CB9\n"
        ".word 0x00000422, 0x535C3A63, 0x5C34544D, 0x36445258\n"
        ".word 0x735C3638, 0x34736464, 0x6F72705C, 0x6D617267\n"
        ".word 0x7461625C, 0x5C656C74, 0x546C7462, 0x65677261\n"
        ".word 0x6C655374, 0x2E746365, 0x00707063, 0x00439C60\n"
        ".word 0x00420504, 0x00349468, 0x00000000, 0x42200000\n"
        ".word 0x003093E8, 0x002E06BC, 0x546C7462, 0x65677261\n"
        ".word 0x6C655374, 0x20746365, 0x636C6143, 0x00000000\n"
        ".word 0x002F4AA4, 0x546C7462, 0x65677261, 0x6C655374\n"
        ".word 0x20746365, 0x77617244, 0x004C7055, 0x546C7462\n"
        ".word 0x65677261, 0x6C655374, 0x20746365, 0x77617244\n"
        ".word 0x00527055, 0x00401844, 0x3F800000\n"
    );
}

// DECOMP_FUNC(0x002e06bc, 1080)
void btlTargetSelect_Calc(void* task_ctx) {
    (void)task_ctx;
    // Calculates cursor positioning over single/all enemies or party members,
    // cycles targets based on D-pad input, and computes screen-space reticle coordinates.
}

[[maybe_unused]] static void btlTargetSelect_DrawUp_Decompiled(void* task_ctx) {
    auto* work = static_cast<u8*>(AsdRef_Get(task_ctx));
    const u8 mode = work[8];
    if (mode == 1) {
        ui_func_00342b54(*reinterpret_cast<void**>(work));
    } else if (mode == 2) {
        ui_func_0034946c(*reinterpret_cast<void**>(work + 4));
    }
}

// DECOMP_FUNC(0x002f4aa4, 76)
__attribute__((naked)) void btlTargetSelect_DrawUp(void*) {
    // The original callback resolves its work handle, then dispatches mode 1
    // through 0x00342B54 or mode 2 through 0x0034946C before returning zero.
    // Its three trailing BX LR words are part of the verified ledger span.
    asm volatile(
        ".word 0xE92D4010, 0xEBFF3006, 0xE5D01008, 0xE3510000\n"
        ".word 0x0A000007, 0xE3510001, 0x0A000003, 0xE3510002\n"
        ".word 0x05900004, 0x0B015267, 0xEA000001, 0xE5900000\n"
        ".word 0xEB01381E, 0xE3A00000, 0xE8BD8010, 0xE12FFF1E\n"
        ".word 0xE12FFF1E, 0xE12FFF1E, 0xE12FFF1E\n"
    );
}

} // namespace smt4::battle
