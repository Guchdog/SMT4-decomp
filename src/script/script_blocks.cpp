#include "script/script_blocks.h"

namespace smt4::script {

// ---------------------------------------------------------------------------
// Observed call targets.  One declaration per binary address; none of these
// addresses is declared in engine/asd_symbols.h or another reconstructed TU.
// ---------------------------------------------------------------------------

extern "C" {
    // 0x0027EB98 (76 B): resolves the active per-slot script work.  It reads
    // `*ctx`, then battle_work+0x84, validates [0,4), scales by 0xF1C and adds
    // the table pointer at 0x00434278+4 plus 4.
    ScriptSlot* script_vm_func_0027eb98(ScriptBattleContext* ctx);

    // 0x002475E4 (1,664 B): writes a 16-bit selection result to `out`
    // (`ldrh r0,[sp,#0xc]` at 0x0024C8D0).
    u16 camp_func_002475e4(u16* out, ScriptBattleWork* work,
                           ScriptCommandInput* input);

    // 0x003D0E18 (304 B): battle command flag reducer.
    void battle_func_003d0e18(ScriptBattleContext* ctx,
                              ScriptCommandInput* input, s32 value,
                              s32* out_flag, s32* out_result);

    // 0x002B4854 (136 B): row lookup by unit id.
    ScriptCommandRow* camp_func_002b4854(s32 unit_id);

    // 0x003C8608 (72 B): "can this actor be targeted" predicate; the routine
    // ignores the incoming register state and returns 0/1.
    s32 script_vm_func_003c8608();

    // 0x003D038C (192 B), 0x003CF3D4 (128 B), 0x00229B2C (140 B),
    // 0x003CFA28 (136 B): the four random-target helpers reused by mode 1.
    void script_vm_func_003d038c(ScriptBattleContext* ctx, s32 mode);
    void script_vm_func_003cf3d4(ScriptBattleContext* ctx);
    void script_vm_func_00229b2c(ScriptBattleContext* ctx);
    void script_vm_func_003cfa28(ScriptBattleContext* ctx);

    // 0x003D11F8 (212 B): command-result dispatch.
    void script_vm_func_003d11f8(ScriptBattleContext* ctx, s32 flag);

    // 0x0023EC3C (56 B): LCG draw.  The argument is `count - 1`; the routine
    // computes `(rand16 * (arg + 1)) >> 16`, i.e. an index in [0,count).
    s32 script_vm_func_0023ec3c(u32 count_minus_one);

    // 0x00293C98 (16 B): returns the UI context pointer stored at 0x00435D90.
    void* ui_func_00293c98();
}

namespace {

constexpr s32 kActorCount = 0x6D;          // `cmp r5,#0x6d` (0x0024CA70)
constexpr u32 kActorSelected = 0x400;      // `orr r1,r1,#0x400` (0x0024CA64)

// `sub r0,r1,#1; uxth r0,r0; bl 0x23ec3c` (0x0024CE98..0x0024CEA0 and
// repeats): uniform index in [0,count).
inline s32 RandomIndex(s32 count) {
    return script_vm_func_0023ec3c(static_cast<u32>(count - 1) & 0xFFFFu);
}

} // namespace

// ---------------------------------------------------------------------------
// 0x0024C828: battle target-selection helper.
//
// The routine runs once per script-battle command.  It:
//   1. reads the current command id from slot->actor+0x14C and folds a
//      three-way command-input result through battle_func_003D0E18;
//   2. scans the 0x6D battle actors and clears/sets their 0x400 "selected"
//      flag according to the command's target polarity;
//   3. when the command input reports 1 or 2, forwards the polarity to
//      0x003D11F8 and returns;
//   4. otherwise applies the `mode` (r1) candidate rule to the selected
//      actors and marks one of them through slot->selected[].
//
// Every literal below (0x6D, 0x288 stride, 0x400, 0x2710, the 1/10/100/... 
// ladder is absent here, the 0x1E/0x28/0x41 roll bounds) is read directly
// from the listing.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0024c828, 3616)
void script_vm_func_0024c828(ScriptBattleContext* ctx, s32 mode, s32 param) {
    s32 out_flag = 0;                   // [sp+0x08] (`str r0,[sp,#8]`)
    s32 out_result = 0;                 // [sp+0x04] (`str r0,[sp,#4]`)

    ScriptSlot* slot = script_vm_func_0027eb98(ctx);        // 0x0024C84C
    ScriptActorState* state = slot->actor;                  // 0x0024C850

    // 0x0024C858..0x0024C860: 13-entry jump table at 0x0024C868 indexed by
    // state->command_id; 0, 4..7, 9, 10 and 12 land on the common scan.
    switch (state->command_id) {
    case 1: {
        // 0x0024C898..0x0024C8B4: re-resolve the slot for the input flags;
        // polarity is the inverse of input bit 0x10.
        const u32 flags = script_vm_func_0027eb98(ctx)->input->flags;
        out_flag = (flags & 0x10u) == 0 ? 1 : 0;

        // 0x0024C8B8..0x0024C8DC: re-resolve the slot and read the 16-bit
        // command result.
        ScriptSlot* current = script_vm_func_0027eb98(ctx);
        u16 result = 0;
        camp_func_002475e4(&result, ctx->work, current->input);
        out_result = result != 0 ? 1 : 0;
        break;
    }
    case 2:
    case 3: {
        // 0x0024C8E8..0x0024C924: re-resolve the slot for the unit id, then
        // re-resolve it again for the command input.
        const s16 unit_id = script_vm_func_0027eb98(ctx)->actor->unit_id;
        ScriptSlot* current = script_vm_func_0027eb98(ctx);
        battle_func_003d0e18(ctx, current->input, unit_id,
                             &out_flag, &out_result);
        break;
    }
    case 8: {
        // 0x0024C92C..0x0024C980: look up the command row for the unit.
        const s16 unit_id = script_vm_func_0027eb98(ctx)->actor->unit_id;
        ScriptCommandRow* row = camp_func_002b4854(unit_id);
        if (row->target_count != 0) {
            ScriptSlot* current = script_vm_func_0027eb98(ctx);
            battle_func_003d0e18(ctx, current->input, row->target_count,
                                 &out_flag, &out_result);
        } else {
            // 0x0024C984..0x0024C9AC: input bit 0x10 and row bit 0x80.
            ScriptSlot* current = script_vm_func_0027eb98(ctx);
            const u32 flags = current->input->flags;
            out_flag = (flags & 0x10u) != 0 ? 1 : 0;
            out_result = (row->flags & 0x80u) != 0 ? 1 : 0;
        }
        break;
    }
    case 11: {
        // 0x0024C9C0..0x0024C9E4: direct polarity, zero command result.
        ScriptSlot* current = script_vm_func_0027eb98(ctx);
        out_flag = (current->input->flags & 0x10u) != 0 ? 1 : 0;
        out_result = 0;
        break;
    }
    default:
        break;
    }

    // ---- 0x0024C9E8..0x0024CA74: actor flag sweep -------------------------
    // r8 = out_flag.  Each actor is 0x288 bytes; +0x6E is the actor slot id,
    // +0 flags, +0x1B8 the rank key used by modes 5/6.
    const s32 polarity = out_flag;
    ScriptActor* actors = ctx->work->actors;
    for (s32 i = 0; i < kActorCount; ++i) {
        ScriptActor& actor = actors[i];
        const s32 slot_id = actor.slot;
        if (slot_id < 0) {
            continue;                                       // 0x0024CA10 blt
        }
        const u32 flags = actor.flags;
        if ((flags & 1u) == 0) {
            continue;                                       // 0x0024CA1C
        }
        if ((flags & 0x40u) != 0) {
            continue;                                       // 0x0024CA24
        }
        if (polarity == 1) {
            // 0x0024CA3C: keep actors that already carry 0x10.
            if ((flags & 0x10u) != 0) {
                actor.flags = flags | kActorSelected;
            }
        } else if ((flags & 0x10u) == 0) {
            // 0x0024CA48..0x0024CA5C: without 0x10 the actor is eligible
            // immediately when 0x20 is clear; otherwise 0x003C8608 decides.
            if ((flags & 0x20u) == 0 || script_vm_func_003c8608() != 0) {
                actor.flags = flags | kActorSelected;
            }
        }
    }

    // 0x0024CA78..0x0024CA84: command results 1 and 2 go straight to
    // 0x003D11F8 with the polarity.
    if (out_result == 1 || out_result == 2) {
        script_vm_func_003d11f8(ctx, out_flag);
        return;
    }

    // 0x0024CA88..0x0024CA90: 28-entry jump table at 0x0024CA94 indexed by
    // `mode`; entries 0..0x1B are valid (the compare is against 0x1C).
    s32 candidates[kActorCount];
    s32 count = 0;

    switch (mode) {
    case 0:
        // 0x0024CB10: no target selected.
        return;

    case 1: {
        // 0x0024CB18..0x0024CBB0: roll against the number of selected
        // actors.  The three roll bounds are 0x1E, 0x28 and 0x41.
        const s32 roll = script_vm_func_0023ec3c(0x63); // 0x0024CB18
        s32 selected = 0;
        for (s32 i = 0; i < kActorCount; ++i) {
            if ((actors[i].flags & kActorSelected) != 0) {
                ++selected;                             // 0x0024CB40
            }
        }
        if (selected >= 3) {                            // 0x0024CB50
            if (roll < 0x1E) {
                script_vm_func_003d038c(ctx, 3);        // 0x0024CB60..68
            } else if (roll < 0x41) {
                script_vm_func_003d038c(ctx, 2);        // 0x0024CBA8
            } else {
                script_vm_func_003cfa28(ctx);           // 0x0024CBD4
            }
        } else {
            // 0x0024CB80: the UI context carries a 16-bit panel id at
            // +0x1F00+0xC4; value 2 selects the short roll bound.
            u8* ui = static_cast<u8*>(ui_func_00293c98());
            const u16 panel = *reinterpret_cast<u16*>(ui + 0x1F00 + 0xC4);
            if (panel != 2) {
                script_vm_func_003cf3d4(ctx);           // 0x0024CBB4
            } else if (roll < 0x28) {
                script_vm_func_003d038c(ctx, 2);        // 0x0024CBA8
            } else {
                script_vm_func_003cfa28(ctx);           // 0x0024CBD4
            }
        }
        return;
    }

    case 2:
        script_vm_func_003cf3d4(ctx);                   // 0x0024CBB4
        return;

    case 3:
        script_vm_func_00229b2c(ctx);                   // 0x0024CBC4
        return;

    case 4:
        script_vm_func_003cfa28(ctx);                   // 0x0024CBD4
        return;

    case 5: {
        // 0x0024CBE4..0x0024CC64: pick the selected actor with the smallest
        // +0x1B8 rank key (initial sentinel 0x2710).
        s32 best = 0x2710;
        for (s32 i = 0; i < kActorCount; ++i) {
            ScriptActor& actor = actors[i];
            if ((actor.flags & kActorSelected) == 0) {
                continue;
            }
            const s32 key = actor.rank_key;
            if (key < best) {
                best = key;
                candidates[count++] = actor.slot;
            }
        }
        if (count == 0) {
            script_vm_func_003cf3d4(ctx);               // 0x0024CCF0
            return;
        }
        // 0x0024CC4C..0x0024CC64: the candidate list is not randomized here;
        // index `count-1` (the last, minimum key) is marked directly.
        slot = script_vm_func_0027eb98(ctx);
        slot->selected[candidates[count - 1]] = 1;
        return;
    }

    case 6: {
        // 0x0024CC68..0x0024CCE8: pick the selected actor with the largest
        // +0x1B8 rank key (initial sentinel 0).  Note the listing parks the
        // candidate base in r4 after setting r0 = ctx.
        s32 best = 0;
        for (s32 i = 0; i < kActorCount; ++i) {
            ScriptActor& actor = actors[i];
            if ((actor.flags & kActorSelected) == 0) {
                continue;
            }
            const s32 key = actor.rank_key;
            if (key > best) {
                best = key;
                candidates[count++] = actor.slot;
            }
        }
        if (count == 0) {
            script_vm_func_003cf3d4(ctx);               // 0x0024CCF0
            return;
        }
        // 0x0024CCD4..0x0024CCE8: index `count-1` (the last, maximum key) is
        // marked directly, matching the minimum path.
        slot = script_vm_func_0027eb98(ctx);
        slot->selected[candidates[count - 1]] = 1;
        return;
    }

    case 7:
    case 9: {
        // 0x0024CCFC / 0x0024CDCC: party mask bit `param` set.
        const u16 mask = static_cast<u16>(1u << param);
        for (s32 i = 0; i < kActorCount; ++i) {
            ScriptActor& actor = actors[i];
            if ((actor.flags & kActorSelected) != 0 &&
                (actor.party_mask & mask) != 0) {
                candidates[count++] = actor.slot;
            }
        }
        break;
    }

    case 8:
    case 10: {
        // 0x0024CD64 / 0x0024CE34: party mask bit `param` clear.
        const u16 mask = static_cast<u16>(1u << param);
        for (s32 i = 0; i < kActorCount; ++i) {
            ScriptActor& actor = actors[i];
            if ((actor.flags & kActorSelected) != 0 &&
                (actor.party_mask & mask) == 0) {
                candidates[count++] = actor.slot;
            }
        }
        break;
    }

    case 11:
        // 0x0024CEC4: flags 0x400 and 0x20 both set.
        for (s32 i = 0; i < kActorCount; ++i) {
            ScriptActor& actor = actors[i];
            if ((actor.flags & kActorSelected) != 0 &&
                (actor.flags & 0x20u) != 0) {
                candidates[count++] = actor.slot;
            }
        }
        break;

    case 12:
        // 0x0024CF10: 0x400 set, 0x20 clear.
        for (s32 i = 0; i < kActorCount; ++i) {
            ScriptActor& actor = actors[i];
            if ((actor.flags & kActorSelected) != 0 &&
                (actor.flags & 0x20u) == 0) {
                candidates[count++] = actor.slot;
            }
        }
        break;

    case 13:
        // 0x0024CF60: selected and +0xCE equals `param`.
        for (s32 i = 0; i < kActorCount; ++i) {
            ScriptActor& actor = actors[i];
            if ((actor.flags & kActorSelected) != 0 &&
                actor.target_id == static_cast<u16>(param)) {
                candidates[count++] = actor.slot;
            }
        }
        break;

    case 14:
        // 0x0024CFBC: selected and +0xCE differs from `param`.
        for (s32 i = 0; i < kActorCount; ++i) {
            ScriptActor& actor = actors[i];
            if ((actor.flags & kActorSelected) != 0 &&
                actor.target_id != static_cast<u16>(param)) {
                candidates[count++] = actor.slot;
            }
        }
        break;

    case 15: {
        // 0x0024D014..0x0024D034: the index is read from a first slot
        // resolution and the byte is stored through a second one.
        const u16 index = script_vm_func_0027eb98(ctx)->actor_index;
        ScriptSlot* target = script_vm_func_0027eb98(ctx);
        target->selected[index] = 1;
        return;
    }

    case 16: {
        // 0x0024D03C..0x0024D0A4: every selected actor whose slot id differs
        // from slot+0x2C.  The listing re-resolves 0x0027EB98 per actor.
        for (s32 i = 0; i < kActorCount; ++i) {
            ScriptActor& actor = actors[i];
            if ((actor.flags & kActorSelected) == 0) {
                continue;
            }
            const u16 exclude = script_vm_func_0027eb98(ctx)->actor_index;
            const s16 id = actor.slot;
            if (id != static_cast<s16>(exclude)) {
                candidates[count++] = id;
            }
        }
        break;
    }

    case 17:
    case 18:
    case 19:
    case 20: {
        // 0x0024D0D8 / 0x0024D14C / 0x0024D1C0 / 0x0024D234: lane field
        // (+0x1F2 + param*2) >> 10 equals 3, 4, 1 or 2 respectively.
        const u16 wanted = mode == 17 ? 3
                         : mode == 18 ? 4
                         : mode == 19 ? 1 : 2;
        for (s32 i = 0; i < kActorCount; ++i) {
            ScriptActor& actor = actors[i];
            if ((actor.flags & kActorSelected) != 0 &&
                static_cast<u16>(actor.lane[param] >> 10) == wanted) {
                candidates[count++] = actor.slot;
            }
        }
        break;
    }

    case 21:
    case 22:
    case 23:
    case 24: {
        // 0x0024D2A8 / 0x0024D31C / 0x0024D390 / 0x0024D404: lane field
        // differs from 3, 4, 1 or 2.
        const u16 unwanted = mode == 21 ? 3
                           : mode == 22 ? 4
                           : mode == 23 ? 1 : 2;
        for (s32 i = 0; i < kActorCount; ++i) {
            ScriptActor& actor = actors[i];
            if ((actor.flags & kActorSelected) != 0 &&
                static_cast<u16>(actor.lane[param] >> 10) != unwanted) {
                candidates[count++] = actor.slot;
            }
        }
        break;
    }

    case 25:
        // 0x0024D478: group[param] >= 1.
        for (s32 i = 0; i < kActorCount; ++i) {
            ScriptActor& actor = actors[i];
            if ((actor.flags & kActorSelected) != 0 &&
                actor.group[param] >= 1) {
                candidates[count++] = actor.slot;
            }
        }
        break;

    case 26:
        // 0x0024D500: group[param] <= -1.
        for (s32 i = 0; i < kActorCount; ++i) {
            ScriptActor& actor = actors[i];
            if ((actor.flags & kActorSelected) != 0 &&
                actor.group[param] <= -1) {
                candidates[count++] = actor.slot;
            }
        }
        break;

    case 27:
        // 0x0024D594..0x0024D638: lane field is not 1, 3 or 4.
        for (s32 i = 0; i < kActorCount; ++i) {
            ScriptActor& actor = actors[i];
            if ((actor.flags & kActorSelected) == 0) {
                continue;
            }
            const u16 lane = static_cast<u16>(actor.lane[param] >> 10);
            if (lane != 1 && lane != 3 && lane != 4) {
                candidates[count++] = actor.slot;
            }
        }
        break;

    default:
        return;
    }

    // 0x0024CE98 / 0x0024D4D8 / 0x0024D560 / 0x0024D614: every collecting
    // mode ends with a uniform pick over the candidate list and stores byte 1
    // at slot+0x38+candidate.
    const s32 index = RandomIndex(count);
    slot = script_vm_func_0027eb98(ctx);
    slot->selected[candidates[index]] = 1;
}

} // namespace smt4::script
