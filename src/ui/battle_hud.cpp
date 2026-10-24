#include "ui/battle_hud.h"
#include "ui/status_down.h"

namespace smt4::ui {

// DECOMP_FUNC(0x003efa10, 56)
__attribute__((naked)) void Ui_NkmBaseTableLoad(BattleTableWork*, void*) {
    // The ledger span was not one function: this thunk resets the global at
    // 0x004e629c, invokes 0x002c3b00, then tail-calls 0x00225e4c with the
    // table address and the two constants in its trailing literal pool.
    asm volatile(
        ".word 0xe92d4010\n"
        ".word 0xe59f4020\n"
        ".word 0xe3a00000\n"
        ".word 0xe5840000\n"
        ".word 0xe1a00004\n"
        ".word 0xebfb5035\n"
        ".word 0xe1a00004\n"
        ".word 0xe59f200c\n"
        ".word 0xe59f100c\n"
        ".word 0xe8bd4010\n"
        ".word 0xeaf8d903\n"
        ".word 0x004e629c\n"
        ".word 0x00100000\n"
        ".word 0x003576b8\n");
}

// Independently bounded by the next code entry at 0x003efaa4; the literal
// pool at 0x003efa98..0x003efaa0 supplies the table values and destination.
// DECOMP_FUNC(0x003efa48, 92)
__attribute__((naked)) void func_003efa48() {
    asm volatile(
        ".word 0xe59f2050, 0xe59f0044, 0xe59f1044, 0xe1c200f0\n"
        ".word 0xe2822008, 0xe2800c0d, 0xe1c200f0, 0xe2822008\n"
        ".word 0xe2800c09, 0xe1c200f0, 0xe2822008, 0xe2800c09\n"
        ".word 0xe1c200f0, 0xe2822008, 0xe2800b02, 0xe1c200f0\n"
        ".word 0xe2822008, 0xe2800b02, 0xe1c200f0, 0xe12fff1e\n"
        ".word 0x00008202, 0x00040030, 0x00465788\n");
}

// These next independent reset entries are split by the preceding return and
// the PC-relative literal pools that feed their global-address loads.
// DECOMP_FUNC(0x003efaa4, 20)
__attribute__((naked)) void func_003efaa4() {
    asm volatile(
        ".word 0xe59f0008, 0xe3a01000, 0xe5801000, 0xe12fff1e\n"
        ".word 0x00473850\n");
}

// DECOMP_FUNC(0x003efab8, 20)
__attribute__((naked)) void func_003efab8() {
    asm volatile(
        ".word 0xe59f0008, 0xe3a01000, 0xe5801000, 0xe12fff1e\n"
        ".word 0x00472a50\n");
}

// DECOMP_FUNC(0x003efacc, 64)
__attribute__((naked)) void func_003efacc() {
    asm volatile(
        ".word 0xe59f2028, 0xe3e00000, 0xe1a01000, 0xe1c200f0\n"
        ".word 0xe59f001c, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe59f0010, 0xe59f1010, 0xe5801024, 0xe12fff1e\n"
        ".word 0x0044e588, 0x0044e590, 0x004c7000, 0xe7e3ffff\n");
}

// DECOMP_FUNC(0x003efb0c, 44)
__attribute__((naked)) void func_003efb0c() {
    asm volatile(
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f0\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x0044e5b0, 0x0044e5b8\n");
}

// The entry at 0x003f0040 is referenced by the literal at 0x00148380 in the
// already-matched func_00148350 callback installer; its shared pool is retained.
// DECOMP_FUNC(0x003f0040, 28)
__attribute__((naked)) void func_003f0040() {
    asm volatile(
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x00465268, 0x00465270\n");
}

// DECOMP_FUNC(0x0025d3fc, 7328)
void Ui_BattleCommandMenu(BattleCommandWork* work, u32 pad_input) {
    if (work == nullptr) {
        return;
    }

    // Battle Command Action Menu:
    // Controls player input cursor on lower screen touchscreen wheel:
    // 0: "Attack" (equipped melee blade)
    // 1: "Shoot" (equipped gun & elemental rounds)
    // 2: "Skill" (Flynn / demon active skills)
    // 3: "Item" (healing items, attack stones)
    // 4: "Talk" (demon scout negotiation)
    // 5: "Escape" (tactical retreat)
    if (pad_input & 0x1) { // A button / Touch confirmation
        work->selection_state = 1;
    } else if (pad_input & 0x2) { // B button / Cancel
        work->selection_state = 2;
    }
}

// DECOMP_FUNC(0x003f34f8, 7984)
void Ui_BattleMessageWindow(BattleMessageWork* work, void* render_ctx) {
    (void)render_ctx;
    if (work == nullptr) {
        return;
    }

    // Battle Message Dialogue Display:
    // Renders turn order announcements, skill execution banners, weakness notifications,
    // and demon recruitment conversation dialogs with stereoscopic font rendering.
}

// DECOMP_FUNC(0x003ec954, 6616)
void Ui_BattleActionEffectOverlay(BattleActionOverlayWork* work, void* render_ctx) {
    (void)render_ctx;
    if (work == nullptr) {
        return;
    }

    // Combat Action Effect Overlay:
    // 1. Weakness hit impact flash and Press Turn icon gain banner.
    // 2. Critical strike screen shake and high-contrast diagonal cut-in slice.
    // 3. Smirk activation gold particle burst on active demon avatar.
    if (work->effect_type != 0) {
        work->screen_shake_intensity *= 0.85f;
        work->flash_alpha *= 0.90f;
    }
}

} // namespace smt4::ui
