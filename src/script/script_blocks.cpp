#include "script/script_blocks.h"
#include "engine/asd_symbols.h"

namespace smt4::script {

// ---------------------------------------------------------------------------
// Observed call targets.  One declaration per binary address; none of these
// addresses is declared in engine/asd_symbols.h or another reconstructed TU.
// ---------------------------------------------------------------------------

extern "C" {
    // 0x0027EB98 (76 B) is declared canonically in script/script_blocks.h.

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

// ---------------------------------------------------------------------------
// 0x0027B8CC: effect/particle emission
// ---------------------------------------------------------------------------

ScriptEffectTable g_ScriptEffectTable_447a28{};   // 0x00447A28
ScriptEffectSlot* g_ScriptEffectSlots_4a1264 =
    reinterpret_cast<ScriptEffectSlot*>(0x004A1264u); // 0x004A1264
void* g_ScriptVmContext_43427c = nullptr;          // 0x0043427C

namespace {

// Observed call targets.  One declaration per binary address.
extern "C" {
s32 camp_func_00248418();
ScriptEffectEntry* camp_func_002483b8(s32 index);
s32 camp_func_00321aa4();
ScriptEffectRowA* camp_func_00308c98(s32 index);
s32 script_vm_func_00299064(u32 id);
s32 camp_func_0031b8fc();
ScriptEffectRowB* script_vm_func_00248358(s32 index);
s32 script_vm_func_0027dbd8();
s32 script_vm_func_0024f6e4();
ScriptEffectRowB* script_vm_func_0027636c(s32 index);
s32 script_vm_func_00324720();
ScriptEffectRowE* script_vm_func_00287b10(s32 index);
s32 script_vm_func_002762d0(s32 index);
s32 script_vm_func_00327074();
ScriptEffectRowF* camp_func_00316fc4(s32 index);
s32 engine_func_002df798(s32 index);
s32 script_vm_func_00248320();
ScriptEffectRowD* script_vm_func_0025b8a8(s32 index);
s32 engine_func_002f35cc(s16 id);
s32 camp_func_0030f6fc();
ScriptEffectRowC* script_vm_func_002764d4(s32 index);
s32 script_vm_func_002eafe4(s32 type);
s32 script_vm_func_002e00f0(s32 type);
s32 script_vm_func_002eabf4(s32 kind);
s32 script_vm_func_002eae80(s32 value, f32* out_a, f32* out_b, f32* out_c);
// The four register arguments are followed by fifteen stack words and six
// VFP s0..s5 arguments.
void script_vm_func_0024f460(u32 id, u32 handle, const char* kind, s32 type,
                             u32 s0, u32 s1, u32 s2, u32 s3, u32 s4,
                             u32 s5, u32 s6, u32 s7, u32 s8, u32 s9,
                             u32 s10, u32 s11, u32 s12, u32 s13,
                             u32 s14, f32 f0, f32 f1, f32 f2, f32 f3,
                             f32 f4, f32 f5);
void script_vm_func_00263ee4(u32 id, u32 handle, const char* kind, s32 type,
                             u32 s0, u32 s1, u32 s2, u32 s3, u32 s4,
                             u32 s5, u32 s6, u32 s7, u32 s8, u32 s9,
                             u32 s10, u32 s11, u32 s12, u32 s13,
                             u32 s14, f32 f0, f32 f1, f32 f2, f32 f3,
                             f32 f4, f32 f5);
void engine_func_002a7fc4(char* dst, const char* src);
void script_vm_func_002dfd94(u32 id);
} // extern "C"

inline f32 S16ToF32(s16 value) {
    return static_cast<f32>(value);
}

// 0x0027C2B4..0x0027C368: slot lookup by id.
ScriptEffectSlot* FindEffectSlot(u32 id) {
    const s32 count = g_ScriptEffectTable_447a28.count;
    for (s32 i = 0; i < count; ++i) {
        ScriptEffectSlot* slot = g_ScriptEffectSlots_4a1264 + i;
        if (static_cast<u32>(slot->id) == id) {
            return slot;
        }
    }
    return nullptr;
}

// 0x0027CC..: the six-entry selector table at 0x0027BB68.
enum class EffectSelector : s32 {
    kSkip = 0,
    kSkip2 = 1,
    kString = 2,
    kColor = 3,
};

EffectSelector SelectorFor(s8 value) {
    switch (value) {
    case 0:
    case 1:
        return EffectSelector::kSkip;
    case 2:
        return EffectSelector::kString;
    case 3:
    case 4:
    case 5:
        return EffectSelector::kColor;
    default:
        return EffectSelector::kString;
    }
}

} // namespace

// DECOMP_FUNC(0x0027b8cc, 3444)
void script_vm_func_0027b8cc(s32 filter_a, s32 filter_b) {
    // 0x0027B8D8..0x0027B8F0
    const s32 count = camp_func_00248418();
    if (count <= 0) {
        return;
    }

    for (s32 index = 0; index < count; ++index) {
        ScriptEffectEntry* entry = camp_func_002483b8(index);

        // 0x0027B8FC..0x0027B92C
        if (entry->filter_a == -1) {
            break;
        }
        if (entry->filter_a != filter_a) {
            continue;
        }
        if (entry->filter_a < 0x64 && entry->filter_b != filter_b) {
            continue;
        }

        // 0x0027B930..0x0027B964
        u32 id_word = entry->id;                    // r8
        s32 found_a = -1;                           // [sp+0x84]
        s32 found_b = -1;                           // [sp+0x80]
        s32 list_b_index = -1;                      // sb
        s32 kind_sel = 0;                           // [sp+0x68]
        s32 string_flag = 0;                        // [sp+0x78]
        s32 direct_flag = 0;                        // [sp+0x70]
        const u32 handle = entry->field_04;         // [sp+0x60]
        s32 flag8 = 0;                              // [sp+8]
        bool do_render = false;

        if (entry->id == 4) {
            flag8 = 1;
            do_render = true;
            goto after_search;                      // 0x0027B96C
        }
        if (entry->id == 0) {
            // 0x0027BA18..0x0027BA30
            id_word = 0xFF000000u
                    | (static_cast<u32>(entry->filter_a) << 16)
                    | (static_cast<u32>(entry->filter_b) << 8)
                    | (static_cast<u32>(index) & 0xFFu);
            do_render = true;
            goto after_search;
        }
        if (entry->id <= 0xFFu) {
            do_render = true;
            goto after_search;                      // 0x0027B97C
        }

        // 0x0027B980..0x0027BA40: list A (0x00321AA4 / 0x00308C98).
        {
            const s32 n = camp_func_00321aa4();
            if (n > 0) {
                for (s32 i = 0; i < n; ++i) {
                    ScriptEffectRowA* row = camp_func_00308c98(i);
                    if (row->id == -1) {
                        break;
                    }
                    if (script_vm_func_00299064(row->field_04) == 0) {
                        continue;
                    }
                    if (static_cast<u32>(row->id) != entry->id) {
                        continue;
                    }
                    if (row->field_06 != 0 &&
                        Flag_CheckEventBit(
                            static_cast<u32>(row->field_06)) == 0) {
                        continue;
                    }
                    if (row->field_08 == 0 ||
                        Flag_CheckEventBit(
                            static_cast<u32>(row->field_08)) != 0) {
                        found_a = i;
                        break;
                    }
                }
            }
            if (found_a != -1) {
                goto after_search;
            }
        }

        // 0x0027BA40..0x0027BB9C: list B (0x0031B8FC / 0x00248358).
        {
            const s32 n = camp_func_0031b8fc();
            s32 found_index = -1;
            if (n > 0) {
                for (s32 i = 0; i < n; ++i) {
                    ScriptEffectRowB* row = script_vm_func_00248358(i);
                    if (row->id == -1) {
                        break;
                    }
                    if (static_cast<u32>(row->id) != entry->id) {
                        continue;
                    }
                    if (row->field_04 != 0 &&
                        Flag_CheckEventBit(
                            static_cast<u32>(row->field_04)) == 0) {
                        continue;
                    }
                    // 0x0027BA90..0x0027BAA8: accept when field_06 is zero
                    // or the flag check succeeds; reject only both nonzero.
                    if (row->field_06 != 0 &&
                        Flag_CheckEventBit(
                            static_cast<u32>(row->field_06)) != 0) {
                        continue;
                    }
                    if (row->field_0a == -1) {
                        break;
                    }
                    found_index = i;
                    break;
                }
            }
            if (found_index != -1) {
                list_b_index = found_index;
                ScriptEffectRowB* row =
                    script_vm_func_00248358(found_index);
                // 0x0027BAEC..0x0027BB18
                for (s32 i = 0; i < 5; ++i) {
                    g_ScriptEffectTable_447a28.color[i] = 0;
                }
                // 0x0027BB14: the range check uses the row's +0x0A word;
                // the +0x1C byte only selects the colour/string branch.
                const s32 selector = row->field_0a;
                const bool valid_id =
                    selector != 0 && selector <= 0x258 &&
                    row->id != 0x02802001 &&
                    row->id != 0x03303001 &&
                    row->id != 0x03402001;
                if (valid_id && script_vm_func_0027dbd8() != -1) {
                    // 0x0027BB58: the selector byte is entry +0x1C.
                    switch (SelectorFor(
                        static_cast<s8>(row->field_1c))) {
                    case EffectSelector::kSkip:
                    case EffectSelector::kSkip2:
                        continue;                       // 0x0027C620
                    case EffectSelector::kColor:
                        // 0x0027BC44..0x0027BC64
                        g_ScriptEffectTable_447a28.color[0] = 1;
                        g_ScriptEffectTable_447a28.color[1] =
                            row->field_1c;
                        g_ScriptEffectTable_447a28.color[2] =
                            row->field_1d;
                        g_ScriptEffectTable_447a28.color[3] =
                            row->field_1e;
                        g_ScriptEffectTable_447a28.color[4] =
                            row->field_1f;
                        break;
                    case EffectSelector::kString:
                        break;
                    }
                }
                string_flag = 1;                        // 0x0027BC68

                // 0x0027BEF8: the surviving list-B index is cleared when the
                // row has no +0x08/+0x0A value and its +0x0C byte is 0/0x30.
                if (list_b_index != -1) {
                    ScriptEffectRowB* check =
                        script_vm_func_00248358(list_b_index);
                    const u16 field_08 = check->field_08;
                    if (field_08 == 0 && check->field_0a == 0) {
                        const s8 field_0c =
                            static_cast<s8>(check->field_0c);
                        if (field_0c == 0 || field_0c == 0x30) {
                            list_b_index = -1;
                        }
                    }
                }
                goto render_effect;
            }
        }

        // 0x0027BB9C..0x0027BC88: list C (0x0024F6E4 / 0x0027636C).
        {
            const s32 n = script_vm_func_0024f6e4();
            s32 found_index = -1;
            if (n > 0) {
                for (s32 i = 0; i < n; ++i) {
                    ScriptEffectRowB* row = script_vm_func_0027636c(i);
                    if (row->id == -1) {
                        break;
                    }
                    if (static_cast<u32>(row->id) != entry->id) {
                        continue;
                    }
                    if (row->field_04 != 0 &&
                        Flag_CheckEventBit(
                            static_cast<u32>(row->field_04)) == 0) {
                        continue;
                    }
                    // 0x0027BBF0..0x0027BC08: same gate as list B -- reject
                    // only when field_06 and the flag check are both nonzero.
                    if (row->field_06 != 0 &&
                        Flag_CheckEventBit(
                            static_cast<u32>(row->field_06)) != 0) {
                        continue;
                    }
                    found_index = i;
                    break;
                }
            }
            if (found_index == -1) {
                found_b = -1;
            } else {
                found_b = found_index;
                kind_sel = 1;
                goto after_search;
            }
        }

        // 0x0027BC88..0x0027BD84: list D (0x00324720 / 0x00287B10).
        {
            const s32 n = script_vm_func_00324720();
            s32 found_index = -1;
            if (n > 0) {
                for (s32 i = 0; i < n; ++i) {
                    ScriptEffectRowE* row = script_vm_func_00287b10(i);
                    if (row->id == -1) {
                        break;
                    }
                    if (static_cast<u32>(row->id) != entry->id) {
                        continue;
                    }
                    if (row->field_06 != 0 &&
                        Flag_CheckEventBit(
                            static_cast<u32>(row->field_06)) == 0) {
                        continue;
                    }
                    if (row->field_08 != 0 &&
                        Flag_CheckEventBit(
                            static_cast<u32>(row->field_08)) != 0) {
                        continue;
                    }
                    if (row->field_04 != 0 &&
                        script_vm_func_00299064(row->field_04) == 0) {
                        continue;
                    }
                    const s32 q = script_vm_func_002762d0(i);
                    if (q > 0 && q != 0xFF) {
                        kind_sel = 5;
                        found_b = 0;
                        goto after_search;
                    }
                    if (i == -1) {
                        break;
                    }
                    if (i == -2) {
                        kind_sel = 5;
                        found_b = 0;
                        goto after_search;
                    }
                    found_index = i;
                    kind_sel = 2;
                    break;
                }
            }
            if (found_index == -1) {
                found_b = -1;
            } else {
                found_b = found_index;
                goto after_search;
            }
        }

        // 0x0027BD84..0x0027BE3C: list E (0x00327074 / 0x00316FC4).
        {
            const s32 n = script_vm_func_00327074();
            s32 found_index = -1;
            if (n > 0) {
                for (s32 i = 0; i < n; ++i) {
                    ScriptEffectRowF* row = camp_func_00316fc4(i);
                    if (row->id == -1) {
                        break;
                    }
                    if (static_cast<u32>(row->id) != entry->id) {
                        continue;
                    }
                    if (row->field_04 != 0 &&
                        Flag_CheckEventBit(
                            static_cast<u32>(row->field_04)) == 0) {
                        continue;
                    }
                    if (row->field_06 != 0 &&
                        Flag_CheckEventBit(
                            static_cast<u32>(row->field_06)) != 0) {
                        continue;
                    }
                    if (engine_func_002df798(i) <= 0) {
                        if (i != -1 && i != -2) {
                            found_index = i;
                            kind_sel = 3;
                        } else if (i == -2) {
                            kind_sel = 5;
                            found_b = 0;
                            goto after_search;
                        }
                        break;
                    }
                }
            }
            if (found_index == -1) {
                found_b = -1;
            } else {
                found_b = found_index;
                goto after_search;
            }
        }

        // 0x0027BE3C..0x0027BEF4: list F (0x00248320 / 0x0025B8A8).
        if (direct_flag != 0) {
            goto after_search;
        } else {
            const s32 n = script_vm_func_00248320();
            s32 found_index = -1;
            if (n > 0) {
                for (s32 i = 0; i < n; ++i) {
                    ScriptEffectRowD* row = script_vm_func_0025b8a8(i);
                    if (row->id == -1) {
                        break;
                    }
                    if (static_cast<u32>(row->id) != entry->id) {
                        continue;
                    }
                    if (engine_func_002f35cc(row->field_24) == 0) {
                        kind_sel = 5;
                        found_b = 0;
                        goto after_search;
                    }
                    if (i == -1) {
                        break;
                    }
                    if (i == -2) {
                        break;
                    }
                    found_index = i;
                    kind_sel = 4;
                    break;
                }
            }
            found_b = (found_index == -1) ? -1 : found_index;
        }

after_search:
        // 0x0027BEB8..0x0027BF34
        if (entry->kind == 0x12) {
            do_render = true;
        } else if (found_b == -1 && found_a == -1 &&
                   (id_word & 0x80000000u) == 0) {
            continue;
        } else {
            do_render = true;
        }
        if (!do_render) {
            continue;
        }

render_effect:
        {
            // 0x0027BF38..0x0027BFB0: list G search.
            const s32 n = camp_func_0030f6fc();
            s32 selected = -1;
            if (n > 0) {
                for (s32 i = 0; i < n; ++i) {
                    ScriptEffectRowC* row = script_vm_func_002764d4(i);
                    if (row->id == -1) {
                        break;
                    }
                    if (row->field_26 != 0 &&
                        Flag_CheckEventBit(
                            static_cast<u32>(row->field_26)) != 0) {
                        continue;
                    }
                    if (static_cast<u32>(row->id) != id_word) {
                        continue;
                    }
                    if (script_vm_func_00299064(row->field_24) == 0) {
                        selected = i;
                        break;
                    }
                }
            }

            // 0x0027BFB0..0x0027BFE4: gate on the surviving list-B index.
            s32 type = entry->kind;
            if (list_b_index != -1 &&
                (type == 3 || type == 0x0B)) {
                type = 0x10;
            }
            const s32 type_arg = type;
            const s32 sprite_mode = script_vm_func_002eafe4(type_arg);
            const s32 handle_arg = script_vm_func_002e00f0(type_arg);
            const s32 kind_arg = script_vm_func_002eabf4(entry->kind);

            const f32 c16 = S16ToF32(entry->field_16);
            const f32 c18 = S16ToF32(entry->field_18);
            const f32 c1a = S16ToF32(entry->field_1a);
            const f32 c1c = S16ToF32(entry->field_1c);

            f32 out_c = 0.0f;
            f32 out_b = 0.0f;
            f32 out_a = 0.0f;
            script_vm_func_002eae80(entry->field_1e, &out_a, &out_b, &out_c);

            const s32 flag_11 = static_cast<s8>(entry->field_11);
            const u32 field_1f =
                static_cast<u32>(static_cast<s32>(
                    static_cast<s8>(entry->field_1f)));

            if (sprite_mode == 1) {
                // 0x0027C068..0x0027C0EC: POLY draw.  The fifteen stack
                // words are kind_arg, index, field_0b..field_10, flag8,
                // field_11, handle_arg, field_12..field_14, field_1f;
                // s0..s5 hold field_16, field_18, field_1a, out_a, out_b,
                // field_1C.
                script_vm_func_0024f460(
                    id_word, handle, "POLY", type_arg,
                    static_cast<u32>(kind_arg), static_cast<u32>(index),
                    entry->field_0b, entry->field_0c, entry->field_0d,
                    entry->field_0e, entry->field_0f, entry->field_10,
                    static_cast<u32>(flag8), static_cast<u32>(flag_11),
                    static_cast<u32>(handle_arg), entry->field_12,
                    entry->field_13, entry->field_14, field_1f,
                    c16, c18, c1a, out_a, out_b, c1c);

                // 0x0027C0EC..0x0027C1F0: remapped POLY types get a second
                // 0x00263EE4 pass tagged "NA" (0x0027C3DC).
                s32 na_type = static_cast<s8>(entry->field_1e);
                if (type_arg == 1) {
                    switch (na_type) {
                    case 0:  na_type = 0x0D; break;
                    case 3:  na_type = 0x0F; break;
                    case 4:  na_type = 0x11; break;
                    default: na_type = 0x0B; break;
                    }
                } else if (type_arg == 2) {
                    switch (na_type) {
                    case 0:  na_type = 0x0C; break;
                    case 3:  na_type = 0x0E; break;
                    case 4:  na_type = 0x10; break;
                    default: na_type = 0x0A; break;
                    }
                }
                if (type_arg == 0 || type_arg == 1 || type_arg == 2 ||
                    type_arg == 0x0A || type_arg == 0x2A) {
                    script_vm_func_00263ee4(
                        3, 0, "NA", 0x39,
                        0, 0xFFFFFFFFu, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        static_cast<u32>(na_type), 0, 0, 0,
                        out_b, c18 - 200.0f, c1a, out_a, out_b + 200.0f,
                        800.0f);
                }
            } else if (sprite_mode == 0) {
                // 0x0027C1F4..0x0027C278: BOX draw; same fifteen stack words,
                // with s0..s5 = field_16, field_18, field_1a, out_a, out_b,
                // out_c.
                script_vm_func_00263ee4(
                    id_word, handle, "BOX", type_arg,
                    static_cast<u32>(kind_arg), static_cast<u32>(index),
                    entry->field_0b, entry->field_0c, entry->field_0d,
                    entry->field_0e, entry->field_0f, entry->field_10,
                    static_cast<u32>(flag8), static_cast<u32>(flag_11),
                    static_cast<u32>(handle_arg), entry->field_12,
                    entry->field_13, entry->field_14, field_1f,
                    c16, c18, c1a, out_a, out_b, out_c);
            }

            // 0x0027C27C..0x0027C368: list A slot update.
            if (found_a != -1) {
                ScriptEffectRowA* row = camp_func_00308c98(found_a);
                ScriptEffectSlot* slot =
                    FindEffectSlot(static_cast<u32>(row->id));
                if (slot != nullptr) {
                    slot->field_134 = row->field_0a;
                    AsdString_Strcpy(
                        reinterpret_cast<char*>(slot) + 0x138,
                        reinterpret_cast<const char*>(row) + 0x0C);
                }
            }

            // 0x0027C300..0x0027C368: list A flags.
            if (found_a != -1) {
                ScriptEffectRowA* row = camp_func_00308c98(found_a);
                ScriptEffectSlot* slot =
                    FindEffectSlot(static_cast<u32>(row->id));
                if (slot != nullptr) {
                    slot->field_160 = row->field_06;
                    slot->field_162 = row->field_08;
                    slot->field_164 = 0;
                }
            }

            // 0x0027C368..0x0027C4D4: list B slot update, keyed by the
            // surviving list-B index.
            if (list_b_index != -1) {
                ScriptEffectRowB* row =
                    script_vm_func_00248358(list_b_index);
                ScriptEffectSlot* slot =
                    FindEffectSlot(static_cast<u32>(row->id));
                if (slot != nullptr) {
                    if (row->field_08 != 0) {
                        slot->field_15c = row->field_08;
                    } else {
                        AsdString_Strcpy(
                            reinterpret_cast<char*>(slot) + 0x138,
                            reinterpret_cast<const char*>(row) + 0x0C);
                        slot->field_160 = row->field_04;
                        slot->field_162 = row->field_06;
                        slot->field_164 = 0;
                    }
                }
            }

            // 0x0027C4D4..0x0027C54C: selector/kind record.
            if (kind_sel != 0) {
                ScriptEffectSlot* slot = FindEffectSlot(id_word);
                if (slot != nullptr) {
                    slot->field_166 = static_cast<s16>(kind_sel);
                    slot->field_168 = static_cast<s16>(found_b);
                }
                if (kind_sel == 5) {
                    script_vm_func_002dfd94(id_word);
                }
            }

            // 0x0027C550..0x0027C5C4: colour copy.
            if (string_flag != 0) {
                ScriptEffectSlot* slot = FindEffectSlot(id_word);
                if (slot != nullptr) {
                    engine_func_002a7fc4(
                        reinterpret_cast<char*>(slot) + 0x16E,
                        reinterpret_cast<const char*>(
                            g_ScriptEffectTable_447a28.color));
                }
            }

            // 0x0027C5C4..0x0027C620: selected-list index.
            if (selected != -1) {
                ScriptEffectSlot* slot = FindEffectSlot(id_word);
                if (slot != nullptr) {
                    slot->field_15e = static_cast<s16>(selected);
                }
            }
        }
    }
}

} // namespace smt4::script
