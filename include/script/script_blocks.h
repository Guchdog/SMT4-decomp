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
    u8  pad_0a5[0x4F7];
    u8  action_latched;                 // +0x59C: `strb r1,[r0,#0x59c]`
                                        //   (0x00255634)
};
static_assert(offsetof(ScriptSlot, action_latched) == 0x59C);

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
// 0x0027B8CC: effect/particle emission
//
// The routine walks five registered effect lists, resolves the entry whose id
// matches the record at 0x002483B8(index), then emits its POLY/BOX draw
// command and updates the slot at 0x004A1264.
// ---------------------------------------------------------------------------

/**
 * One effect definition at r6 (`camp_func_002483B8(index)`).
 * `filter_a`/`filter_b` are signed bytes compared with the two arguments
 * (0x0027B900/0x0027B920); `kind` is the byte used by all the render branches
 * (0x0027BEB8).
 */
struct ScriptEffectEntry {
    u32 id;                             // +0x00: `ldr r8,[r6]` (0x0027B930)
    u32 field_04;                       // +0x04: `ldr r1,[r6,#4]` (0x0027B954)
    s8  filter_a;                       // +0x08: `ldrsb r0,[r0,#8]` (0x0027B900)
    s8  filter_b;                       // +0x09: `ldrsb r2,[r6,#9]` (0x0027B920)
    u8  kind;                           // +0x0A: `ldrb r0,[r6,#0xa]` (0x0027BEB8)
    u8  field_0b;                       // +0x0B: `ldrb r0,[r6,#0xb]` (0x0027C0C4)
    u8  field_0c;                       // +0x0C: `ldrb r0,[r6,#0xc]` (0x0027C0AC)
    u8  field_0d;                       // +0x0D
    u8  field_0e;                       // +0x0E
    u8  field_0f;                       // +0x0F
    u8  field_10;                       // +0x10: `ldrb r2,[r6,#0x10]`
                                        //   (0x0027C084)
    u8  field_11;                       // +0x11: `ldrsb ip,[r6,#0x11]`
                                        //   (0x0027C050)
    u8  field_12;                       // +0x12: `ldrb r2,[r6,#0x12]`
                                        //   (0x0027C074)
    u8  field_13;                       // +0x13: `ldrb r3,[r6,#0x13]`
                                        //   (0x0027C070)
    s16 field_14;                       // +0x14: `ldrsh r0,[r6,#0x14]`
                                        //   (0x0027C068)
    s16 field_16;                       // +0x16: `ldrsh r0,[r6,#0x16]`
                                        //   (0x0027C008)
    s16 field_18;                       // +0x18: `ldrsh r2,[r6,#0x18]`
                                        //   (0x0027C00C)
    s16 field_1a;                       // +0x1A: `ldrsh r3,[r6,#0x1a]`
                                        //   (0x0027C010)
    s16 field_1c;                       // +0x1C: `ldrsh ip,[r6,#0x1c]`
                                        //   (0x0027C014); its low byte is the
                                        //   `ldrsb r0,[r6,#0x1c]` switch value
                                        //   (0x0027BB58)
    s8  field_1e;                       // +0x1E: `ldrsb r0,[r6,#0x1e]`
                                        //   (0x0027C028)
    s8  field_1f;                       // +0x1F: `ldrsb r7,[r6,#0x1f]`
                                        //   (0x0027C04C)
};
static_assert(offsetof(ScriptEffectEntry, id) == 0x00);
static_assert(offsetof(ScriptEffectEntry, field_04) == 0x04);
static_assert(offsetof(ScriptEffectEntry, filter_a) == 0x08);
static_assert(offsetof(ScriptEffectEntry, filter_b) == 0x09);
static_assert(offsetof(ScriptEffectEntry, kind) == 0x0A);
static_assert(offsetof(ScriptEffectEntry, field_14) == 0x14);
static_assert(offsetof(ScriptEffectEntry, field_1c) == 0x1C);
static_assert(offsetof(ScriptEffectEntry, field_1e) == 0x1E);
static_assert(offsetof(ScriptEffectEntry, field_1f) == 0x1F);

/** Row returned by 0x00308C98: `ldr r0,[r0]`, `ldrh r0,[r4,#4]`, +6/+8/+A. */
struct ScriptEffectRowA {
    s32 id;                             // +0x00
    u16 field_04;                       // +0x04: `ldrh r0,[r4,#4]`
                                        //   (0x0027B9A8)
    s16 field_06;                       // +0x06: `ldrsh r0,[r4,#6]`
                                        //   (0x0027B9C8)
    s16 field_08;                       // +0x08: `ldrsh r0,[r4,#8]`
                                        //   (0x0027B9E4)
    s16 field_0a;                       // +0x0A: `ldrsh r7,[r0,#0xa]`
                                        //   (0x0027C294)
    u8  pad_00c[4];
    char text[1];                       // +0x0C: `add sl,r0,#0xc`
                                        //   (0x0027C2A0)
};

/** Row returned by 0x00248358: +0/+4/+6/+8/+A and the +0xC byte. */
struct ScriptEffectRowB {
    s32 id;                             // +0x00
    s16 field_04;                       // +0x04: `ldrsh r0,[r4,#4]`
                                        //   (0x0027BA74)
    s16 field_06;                       // +0x06: `ldrsh r0,[r4,#6]`
                                        //   (0x0027BA90)
    u16 field_08;                       // +0x08: `ldrh r1,[r0,#8]`
                                        //   (0x0027BF00)
    s16 field_0a;                       // +0x0A: `ldrsh r0,[r4,#0xa]`
                                        //   (0x0027BAAC)
    u8  field_0c;                       // +0x0C: `ldrsb r0,[r0,#0xc]`
                                        //   (0x0027BF14)
    u8  pad_00d[0x10];
    u8  field_1d;                       // +0x1D: `ldrb r0,[r5,#0x1d]`
                                        //   (0x0027BC50)
    u8  field_1e;                       // +0x1E: `ldrb r0,[r5,#0x1e]`
                                        //   (0x0027BC58)
    u8  field_1f;                       // +0x1F: `ldrb r0,[r5,#0x1f]`
                                        //   (0x0027BC60)
};

/** Row returned by 0x002764D4: +0x20 id, +0x24 u16, +0x26 s16. */
struct ScriptEffectRowC {
    u8  pad_000[0x20];
    s32 id;                             // +0x20: `ldr r0,[r0,#0x20]`
                                        //   (0x0027BF58)
    u16 field_24;                       // +0x24: `ldrh r0,[r4,#0x24]`
                                        //   (0x0027BF8C)
    s16 field_26;                       // +0x26: `ldrsh r0,[r4,#0x26]`
                                        //   (0x0027BF64)
};
static_assert(offsetof(ScriptEffectRowC, id) == 0x20);

/** Row returned by 0x0025B8A8: +0x20 id and +0x24 s16. */
struct ScriptEffectRowD {
    u8  pad_000[0x20];
    s32 id;                             // +0x20: `ldr r2,[r0,#0x20]`
                                        //   (0x0027BE68)
    s16 field_24;                       // +0x24: `ldrsh r0,[r0,#0x24]`
                                        //   (0x0027BE7C)
};

/** Row returned by 0x00287B10: +0/+4/+6/+8. */
struct ScriptEffectRowE {
    s32 id;                             // +0x00: `ldr r0,[r0]`
                                        //   (0x0027BCAC)
    u16 field_04;                       // +0x04: `ldrh r0,[r4,#4]`
                                        //   (0x0027BCF8)
    s16 field_06;                       // +0x06: `ldrsh r0,[r4,#6]`
                                        //   (0x0027BCC0)
    s16 field_08;                       // +0x08: `ldrsh r0,[r4,#8]`
                                        //   (0x0027BCDC)
};

/** Row returned by 0x00316FC4: +0/+4/+6. */
struct ScriptEffectRowF {
    s32 id;                             // +0x00: `ldr r0,[r0]`
                                        //   (0x0027BDA8)
    s16 field_04;                       // +0x04: `ldrsh r0,[r4,#4]`
                                        //   (0x0027BDBC)
    s16 field_06;                       // +0x06: `ldrsh r0,[r4,#6]`
                                        //   (0x0027BDD8)
};

/** One 0x178-byte slot in the table at 0x004A1264. */
struct ScriptEffectSlot {
    u8  pad_000[0x12C];
    s32 id;                             // +0x12C: `ldr r2,[r2,#0x12c]`
                                        //   (0x0027C2C0)
    u8  pad_130[4];
    s16 field_134;                      // +0x134: `str r7,[r0,#0x134]!`
                                        //   (0x0027C2DC)
    u8  pad_136[0x26];
    s16 field_15c;                      // +0x15C: `strh r6,[r0,#0x5c]`
                                        //   (0x0027C3CC)
    s16 field_15e;                      // +0x15E: `strh r5,[r0,#0x5e]`
                                        //   (0x0027C60C)
    s16 field_160;                      // +0x160: `strh r7,[r1,#0x60]`
                                        //   (0x0027C34C)
    s16 field_162;                      // +0x162: `strh r4,[r1,#0x62]`
                                        //   (0x0027C350)
    u8  field_164;                      // +0x164: `strb r3,[r0,#0x164]`
                                        //   (0x0027C354)
    u8  pad_165[1];
    s16 field_166;                      // +0x166: `strh r3,[r0,#0x66]`
                                        //   (0x0027C528)
    s16 field_168;                      // +0x168: `strh r6,[r0,#0x68]`
                                        //   (0x0027C52C)
    u8  pad_16a[4];
    char text_16e[0x0A];                // +0x16E: `add r0,r0,#0x6e`
                                        //   (0x0027C5A0)
};
static_assert(offsetof(ScriptEffectSlot, id) == 0x12C);
static_assert(offsetof(ScriptEffectSlot, field_134) == 0x134);
static_assert(offsetof(ScriptEffectSlot, field_15c) == 0x15C);
static_assert(offsetof(ScriptEffectSlot, field_160) == 0x160);
static_assert(offsetof(ScriptEffectSlot, field_166) == 0x166);
static_assert(offsetof(ScriptEffectSlot, text_16e) == 0x16E);
static_assert(sizeof(ScriptEffectSlot) == 0x178);

/** 0x00447A28: slot count at +0x04 and the five-byte colour at +0x08. */
struct ScriptEffectTable {
    u32 reserved;                       // +0x00
    s32 count;                          // +0x04: `ldr ip,[r6,#4]`
                                        //   (0x0027C29C)
    u8  color[5];                       // +0x08: `ldr r3,[pc,#-0x930]`
                                        //   =0x00447A30 (0x0027C55C)
};
static_assert(offsetof(ScriptEffectTable, count) == 0x04);
static_assert(offsetof(ScriptEffectTable, color) == 0x08);

// ---------------------------------------------------------------------------
// Reconstructed entry points (ledger names)
// ---------------------------------------------------------------------------

/**
 * 0x0027EB98, 76 B: resolves the active per-slot script work.  Shared by
 * 0x0024C828 and the battle emitter 0x002553EC (0x00255628).
 */
ScriptSlot* script_vm_func_0027eb98(ScriptBattleContext* ctx);

/**
 * 0x0024C828, 3,616 B: battle target-selection helper.
 *
 * `ctx`  (r0) is the script VM context, `mode` (r1) selects the candidate
 * selection rule (0..0x1B), and `param` (r2) is the rule operand used by
 * modes 13/14 (target id) and 17..27 (party lane index).
 */
void script_vm_func_0024c828(ScriptBattleContext* ctx, s32 mode, s32 param);

/**
 * 0x0027B8CC, 3,444 B: effect/particle emission.
 *
 * `unused` is the never-read r0; `filter_a` (r1) and `filter_b` (r2) select the
 * effect entries by their +0x08/+0x09 bytes.  The routine has no defined
 * return value.
 */
void script_vm_func_0027b8cc(u32 unused, s32 filter_a, s32 filter_b);

} // namespace smt4::script
