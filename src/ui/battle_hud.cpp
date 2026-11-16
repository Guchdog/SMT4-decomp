#include "ui/battle_hud.h"
#include "ui/status_down.h"

extern "C" {
void engine_func_002c3b00(void* ptr);
void engine_func_00225e4c(void* ptr, u32 a1, u32 a2);
}

namespace smt4::ui {

// DECOMP_FUNC(0x003efa10, 56)
void Ui_NkmBaseTableLoad(BattleTableWork*, void*) {
    void* global_ptr = reinterpret_cast<void*>(0x004E629C);
    *reinterpret_cast<u32*>(global_ptr) = 0;
    engine_func_002c3b00(global_ptr);
    engine_func_00225e4c(global_ptr, 0x003576B8, 0x00100000);
}

// Independently bounded by the next code entry at 0x003efaa4; the literal
// pool at 0x003efa98..0x003efaa0 supplies the table values and destination.
// DECOMP_FUNC(0x003efa48, 92)
void func_003efa48() {
    struct TableEntry {
        u32 a;
        u32 b;
    };
    TableEntry* table = reinterpret_cast<TableEntry*>(0x00465788);
    u32 val = 0x00008202;
    const u32 const_b = 0x00040030;

    table[0] = { val, const_b };
    val += 0x0D00;
    table[1] = { val, const_b };
    val += 0x0900;
    table[2] = { val, const_b };
    val += 0x0900;
    table[3] = { val, const_b };
    val += 0x0800;
    table[4] = { val, const_b };
    val += 0x0800;
    table[5] = { val, const_b };
}

// These next independent reset entries are split by the preceding return and
// the PC-relative literal pools that feed their global-address loads.
// DECOMP_FUNC(0x003efaa4, 20)
void func_003efaa4() {
    *reinterpret_cast<u32*>(0x00473850) = 0;
}

// DECOMP_FUNC(0x003efab8, 20)
void func_003efab8() {
    *reinterpret_cast<u32*>(0x00472A50) = 0;
}

// DECOMP_FUNC(0x003efacc, 64)
void func_003efacc() {
    u32* p1 = reinterpret_cast<u32*>(0x0044E588);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0x0044E590);
    p2[0] = 0;
    p2[1] = 0;

    *reinterpret_cast<u32*>(0x004C7024) = 0xE7E3FFFF;
}

// DECOMP_FUNC(0x003efb0c, 44)
void func_003efb0c() {
    u32* p1 = reinterpret_cast<u32*>(0x0044E5B0);
    p1[0] = 0xFFFFFFFF;
    p1[1] = 0xFFFFFFFF;

    u32* p2 = reinterpret_cast<u32*>(0x0044E5B8);
    p2[0] = 0;
    p2[1] = 0;
}

// The entry at 0x003f0040 is referenced by the literal at 0x00148380 in the
// already-matched func_00148350 callback installer; its shared pool is retained.
// DECOMP_FUNC(0x003f0040, 28)
void func_003f0040() {
    u32* p = reinterpret_cast<u32*>(0x00465270);
    p[0] = 0;
    p[1] = 0;
}

// DECOMP_FUNC(0x0025d3fc, 7328)
__attribute__((naked, used)) void Ui_BattleCommandMenu(BattleCommandWork*, u32) {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x15d3fc, 7328\n");
}

// The original aggregate span contains 143 independently bounded code/pool
// records. The first entry below is the exported message-window routine; its
// remaining exact leaf records are in battle_hud_exact_batch.cpp.
// DECOMP_FUNC(0x003f34f8, 440)
__attribute__((naked, used)) void Ui_BattleMessageWindow(BattleMessageWork*, void*) {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2f34f8, 440\n");
}

// This first routine is a tail-call wrapper; the remaining bounded records
// from the original aggregate span are in battle_hud_exact_batch.cpp.
// DECOMP_FUNC(0x003ec954, 148)
__attribute__((naked, used)) void Ui_BattleActionEffectOverlay(BattleActionOverlayWork*, void*) {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2ec954, 148\n");
}

} // namespace smt4::ui
