#pragma once
#include <cstddef>
#include "types.h"

/**
 * Script-VM runtime blocks A: the battle target-selection helper at
 * 0x0024C828.
 *
 * The routine runs in the script VM's battle context.  Every structure below
 * is an opaque view: only fields proven by an access in the ARM listing of
 * 0x0024C828 are named, and each offset cites the proving instruction.
 */

namespace smt4::script {

// ---------------------------------------------------------------------------
// 0x00434278+4 -> per-slot script work, stride 0xF1C
//
// 0x0027EB98 reads the slot index from battle_work+0x84, validates it against
// [0,4), then scales it by 0xF1C (`mul r0,r0,#0x3c7; lsl #2`) and adds the
// table pointer stored at 0x00434278+4 before adding 4.  These are the only
// slot fields this routine touches.
// ---------------------------------------------------------------------------

struct ScriptActorState;

/** The command-input object reached through ScriptSlot::input. */
struct ScriptCommandInput {
    u32 flags;                          // +0x00: `ldr r1,[r1]` (0x0024C8A8)
};

/**
 * The per-slot script work returned by 0x0027EB98.  `selected` is a byte
 * array indexed by the actor slot id at ScriptActor::slot.
 */
struct ScriptSlot {
    u8  pad_000[0x20];
    ScriptCommandInput* input;          // +0x20: `ldr r1,[r0,#0x20]` (0x0024C8A0)
    u8  pad_024[4];
    ScriptActorState* actor;            // +0x28: `ldr r0,[r0,#0x28]` (0x0024C850)
    u16 actor_index;                    // +0x2C: `ldrh r3,[r0,#0x2c]` (0x0024D01C)
    u8  pad_02e[0x0A];
    u8  selected[0x6D];                 // +0x38: `strb r1,[r3,r0]` (0x0024D030)
};

/**
 * Command state block hung off ScriptSlot::actor.
 * +0x14C is the switch value at 0x0024C858; +0x14E is the id passed to
 * camp_func_002B4854 (0x0024C93C) and to battle_func_003D0E18
 * (0x0024C8F8).
 */
struct ScriptActorState {
    u8  pad_000[0x14C];
    s16 command_id;                     // +0x14C: `ldrsh r0,[r0,#0x4c]` with
                                        //   r0 = state+0x100 (0x0024C858)
    s16 unit_id;                        // +0x14E: `ldrsh r5,[r0,#0x14e]`
                                        //   (0x0024C8F8)
};

/**
 * One 0x288-byte battle actor record.  The table is reached from
 * battle_work+0x1FC0 (`add r1,r1,#0x1fc0; ldr r1,[r1]`, 0x0024C9FC) and
 * holds 0x6D entries (`cmp r5,#0x6d`, 0x0024CA70).
 */
struct ScriptActor {
    u32 flags;                          // +0x000: `ldr r0,[r6]` (0x0024CA14)
    u8  pad_004[0x6A];
    s16 slot;                           // +0x06E: `ldrsh r0,[r6,#0x6e]`
                                        //   (0x0024CA08)
    u8  pad_070[2];
    s16 group[0x2E];                    // +0x072: `add r2,r2,r7,lsl #1` with
                                        //   r2 = actor+0x72 (0x0024D47C)
    u16 target_id;                      // +0x0CE: `add r2,r0,#0xce`
                                        //   (0x0024CF78)
    u8  pad_0d0[0xE8];
    s16 rank_key;                       // +0x1B8: `add ip,r1,#0x1b8`
                                        //   (0x0024CC00)
    u8  pad_1ba[0x0C];
    u16 party_mask;                     // +0x1C6: `add r2,r0,#0x100;
                                        //   add r2,r2,#0xc6` (0x0024CD1C)
    u8  pad_1c8[0x2A];
    u16 lane[0x20];                     // +0x1F2: `add ip,r8,r3,lsl #3`
                                        //   + `add ip,ip,#0x100` (0x0024D110)
    u8  pad_232[0x56];                  // +0x232..+0x288 (table stride)
};
static_assert(sizeof(ScriptActor) == 0x288);
static_assert(offsetof(ScriptActor, flags) == 0x000);
static_assert(offsetof(ScriptActor, slot) == 0x06E);
static_assert(offsetof(ScriptActor, group) == 0x072);
static_assert(offsetof(ScriptActor, target_id) == 0x0CE);
static_assert(offsetof(ScriptActor, rank_key) == 0x1B8);
static_assert(offsetof(ScriptActor, party_mask) == 0x1C6);
static_assert(offsetof(ScriptActor, lane) == 0x1F2);

/** Head of the battle work block (`ldr r1,[r4]` at 0x0024C9F0). */
struct ScriptBattleWork {
    u8  pad_000[0x1FC0];
    ScriptActor* actors;                // +0x1FC0: `add r1,r1,#0x1fc0;
                                        //   ldr r1,[r1]` (0x0024C9FC)
};

/** Script VM / battle context passed in r0. */
struct ScriptBattleContext {
    ScriptBattleWork* work;             // +0x00: `ldr r1,[r4]` (0x0024C9F0)
};
static_assert(offsetof(ScriptBattleContext, work) == 0x00);

/** One row returned by camp_func_002B4854 (`ldrsh r0,[r0,#0x4e]` id). */
struct ScriptCommandRow {
    u8  pad_000[0x62];
    u16 target_count;                   // +0x62: `ldrh r0,[r0,#0x62]`
                                        //   (0x0024C948)
    u8  pad_064[6];
    u8  flags;                          // +0x6A: `ldrb r0,[r3,#0x6a]`
                                        //   (0x0024C9A4)
};
static_assert(offsetof(ScriptCommandRow, target_count) == 0x62);
static_assert(offsetof(ScriptCommandRow, flags) == 0x6A);

// ---------------------------------------------------------------------------
// Reconstructed entry point (ledger name)
// ---------------------------------------------------------------------------

/**
 * 0x0024C828, 3,616 B: battle target-selection helper.
 *
 * `ctx`  (r0) is the script VM context, `mode` (r1) selects the candidate
 * selection rule (0..0x1B), and `param` (r2) is the rule operand used by
 * modes 13/14 (target id) and 17..27 (party lane index).
 */
void script_vm_func_0024c828(ScriptBattleContext* ctx, s32 mode, s32 param);

} // namespace smt4::script
