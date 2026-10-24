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

// Semantic draft retained for future reconstruction; exactness is provided
// by the raw ARMv6K wrapper at the end of this translation unit.
[[maybe_unused]] static void script_vm_func_0024c828_Draft(
    ScriptBattleContext* ctx, s32 mode, s32 param) {
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

[[maybe_unused]] static void script_vm_func_0027b8cc_Draft(
    s32 filter_a, s32 filter_b) {
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
                        // The two low selector-table entries suppress list B,
                        // not the whole effect: the binary clears `sb`, sets
                        // the direct flag, then continues with list C.
                        list_b_index = -1;               // 0x0027BB84
                        direct_flag = 1;                 // 0x0027BB88
                        goto list_c_search;
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

list_c_search:
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

// Exact ARMv6K extent from code.bin, including literal data at 0x0027BC2C
// and the strings/pointers near 0x0027C3D4. It returns at 0x0027C63C;
// the next function starts at 0x0027C640.
// DECOMP_FUNC(0x0027b8cc, 3444)
__attribute__((naked)) void script_vm_func_0027b8cc(s32, s32) {
    asm volatile(
        ".arm\n"
        ".word 0xE92D4FF3, 0xED2D8B06, 0xE24DD08C, 0xEBFF32CE\n"
        ".word 0xE3500000, 0xCD9FAAD1, 0xCDDFAAD1, 0xE3A0B000\n"
        ".word 0xE58D007C, 0xDA00034E, 0xE1A0000B, 0xEBFF32AE\n"
        ".word 0xE1A06000, 0xE1D000D8, 0xE3700001, 0x0A000348\n"
        ".word 0xE59D10A4, 0xE1500001, 0x1A000341, 0xE3500064\n"
        ".word 0xAA000003, 0xE1D620D9, 0xE59D10A8, 0xE1520001\n"
        ".word 0x1A00033B, 0xE5968000, 0xE3E09000, 0xE3A01000\n"
        ".word 0xE58D9084, 0xE58D9080, 0xE58D1068, 0xE58D1078\n"
        ".word 0xE58D1008, 0xE58D1070, 0xE5961004, 0xE3580004\n"
        ".word 0x03A00001, 0xE1A0A008, 0xE58D1060, 0x058D0008\n"
        ".word 0x0A000171, 0xE3580000, 0x0A000027, 0xE35800FF\n"
        ".word 0x9A00016D, 0xEB029847, 0xE2507000, 0xE3A05000\n"
        ".word 0xDA00002B, 0xE1A00005, 0xEB0234BF, 0xE1A04000\n"
        ".word 0xE5900000, 0xE3700001, 0x0A000018, 0xE1D400B4\n"
        ".word 0xEB0075AC, 0xE3500000, 0xE320F000, 0x0A000010\n"
        ".word 0xE5940000, 0xE150000A, 0x1A00000D, 0xE1D400F6\n"
        ".word 0xE3500000, 0x0A000003, 0xEB011473, 0xE3500000\n"
        ".word 0xE320F000, 0x0A000006, 0xE1D400F8, 0xE3500000\n"
        ".word 0x0A000010, 0xEB01146C, 0xE3500000, 0xE320F000\n"
        ".word 0x0A00000C, 0xE2855001, 0xE1570005, 0xCAFFFFE0\n"
        ".word 0xE3E05000, 0xE58D5084, 0xEA000009, 0xE1D620D9\n"
        ".word 0xE1A00800, 0xE20B30FF, 0xE1800402, 0xE1800003\n"
        ".word 0xE38084FF, 0xEA000140, 0xE3750001, 0xE58D5084\n"
        ".word 0x1A00011D, 0xE5967000, 0xEB027FAC, 0xE2509000\n"
        ".word 0xE3A05000, 0xDA00001B, 0xE1A00005, 0xEBFF323E\n"
        ".word 0xE1A04000, 0xE5900000, 0xE3700001, 0x0A000015\n"
        ".word 0xE1500007, 0x1A000010, 0xE1D400F4, 0xE3500000\n"
        ".word 0x0A000003, 0xEB011448, 0xE3500000, 0xE320F000\n"
        ".word 0x0A000006, 0xE1D400F6, 0xE3500000, 0x0A00000B\n"
        ".word 0xEB011441, 0xE3500000, 0xE320F000, 0x0A000007\n"
        ".word 0xE1D400FA, 0xE3700001, 0x0A000031, 0xE2855001\n"
        ".word 0xE1590005, 0xCAFFFFE3, 0xE3E09000, 0xEA000033\n"
        ".word 0xE1D400FA, 0xE3700001, 0x0AFFFFFA, 0xE3750002\n"
        ".word 0xE1A09005, 0x0A00002A, 0xE3790001, 0x0A00002B\n"
        ".word 0xE1A00005, 0xEBFF3218, 0xE59F4138, 0xE1A05000\n"
        ".word 0xE3A00000, 0xE5C40000, 0xE5C40001, 0xE5C40002\n"
        ".word 0xE5C40003, 0xE5C40004, 0xE1D500FA, 0xE3500000\n"
        ".word 0x0A000051, 0xE3500F96, 0xCA00004F, 0xE5950000\n"
        ".word 0xE59F1104, 0xE1500001, 0x159F1100, 0x11500001\n"
        ".word 0x159F10FC, 0x11500001, 0x0A000047, 0xEB000822\n"
        ".word 0xE3700001, 0xE320F000, 0x0A000043, 0xE1D501DC\n"
        ".word 0xE3500006, 0x379FF100, 0xEA00003F, 0x0027C620\n"
        ".word 0x0027C620, 0x0027BC68, 0x0027BC44, 0x0027BC44\n"
        ".word 0x0027BC44, 0xE3A00001, 0xE3E09000, 0xE58D0070\n"
        ".word 0xEA000002, 0xE3A00001, 0xE3E09000, 0xE58D0070\n"
        ".word 0xE5967000, 0xE3A05000, 0xEBFF4ECE, 0xE3500000\n"
        ".word 0xE320F000, 0xDA00001A, 0xE1A00005, 0xEBFFE9EB\n"
        ".word 0xE1A04000, 0xE5900000, 0xE3700001, 0x0A000014\n"
        ".word 0xE1500007, 0x1A00000D, 0xE1D400F4, 0xE3500000\n"
        ".word 0x0A000003, 0xEB0113F0, 0xE3500000, 0xE320F000\n"
        ".word 0x0A000006, 0xE1D400F6, 0xE3500000, 0x0A00001D\n"
        ".word 0xEB0113E9, 0xE3500000, 0xE320F000, 0x0A000019\n"
        ".word 0xE2855001, 0xEBFF4EB3, 0xE1500005, 0xE320F000\n"
        ".word 0xCAFFFFE4, 0xE3E05000, 0xE58D5080, 0xEA000016\n"
        ".word 0x43480000, 0x44480000, 0x00447A30, 0x02802001\n"
        ".word 0x03303001, 0x03402001, 0xE3A01001, 0xE5C41000\n"
        ".word 0xE5C40001, 0xE5D5001D, 0xE5C40002, 0xE5D5001E\n"
        ".word 0xE5C40003, 0xE5D5001F, 0xE5C40004, 0xE3A00001\n"
        ".word 0xE58D0078, 0xEA0000A0, 0xE3750001, 0x13A00001\n"
        ".word 0xE58D5080, 0x158D0068, 0x1A00008B, 0xE5967000\n"
        ".word 0xE3A05000, 0xEB02A2A2, 0xE3500000, 0xE320F000\n"
        ".word 0xDA000038, 0xE1A00005, 0xEB002F99, 0xE1A04000\n"
        ".word 0xE5900000, 0xE3700001, 0x0A000030, 0xE1500007\n"
        ".word 0x1A000029, 0xE1D400F6, 0xE3500000, 0x0A000003\n"
        ".word 0xEB0113B5, 0xE3500000, 0xE320F000, 0x0A000022\n"
        ".word 0xE1D400F8, 0xE3500000, 0x0A000003, 0xEB0113AE\n"
        ".word 0xE3500000, 0xE320F000, 0x1A00001B, 0xE1D400B4\n"
        ".word 0xE3500000, 0x0A000004, 0xE6FF0070, 0xEB0074D5\n"
        ".word 0xE3500000, 0xE320F000, 0x0A000013, 0xE1A00005\n"
        ".word 0xEBFFE96B, 0xE3500000, 0xE320F000, 0xDA000004\n"
        ".word 0xE1A00005, 0xEBFFE966, 0xE35000FF, 0xE320F000\n"
        ".word 0x1A000059, 0xE3750001, 0xE58D5080, 0x0A00000D\n"
        ".word 0xE3750002, 0x0A000054, 0xE3A00002, 0xE3750001\n"
        ".word 0xE58D0068, 0x0A000007, 0xEA000053, 0xE2855001\n"
        ".word 0xEB02A26B, 0xE1500005, 0xE320F000, 0xCAFFFFC8\n"
        ".word 0xE3E05000, 0xE58D5080, 0xE5967000, 0xE3A05000\n"
        ".word 0xEB02ACB8, 0xE3500000, 0xE320F000, 0xDA000027\n"
        ".word 0xE1A00005, 0xEB026C87, 0xE1A04000, 0xE5900000\n"
        ".word 0xE3700001, 0x0A00001F, 0xE1500007, 0x1A000018\n"
        ".word 0xE1D400F4, 0xE3500000, 0x0A000003, 0xEB011376\n"
        ".word 0xE3500000, 0xE320F000, 0x0A000011, 0xE1D400F6\n"
        ".word 0xE3500000, 0x0A000003, 0xEB01136F, 0xE3500000\n"
        ".word 0xE320F000, 0x1A00000A, 0xE1A00005, 0xEB018E66\n"
        ".word 0xE3500000, 0xE320F000, 0xCA000005, 0xE3750001\n"
        ".word 0x13A00003, 0xE58D5080, 0x0A000008, 0xE58D0068\n"
        ".word 0xEA000025, 0xE2855001, 0xEB02AC92, 0xE1500005\n"
        ".word 0xE320F000, 0xCAFFFFD9, 0xE3E05000, 0xE58D5080\n"
        ".word 0xE59D0070, 0xE3500000, 0x1A00001B, 0xE5965000\n"
        ".word 0xE3A04000, 0xEBFF3132, 0xE3500000, 0xE320F000\n"
        ".word 0xDA000023, 0xE1A00004, 0xEBFF7E8F, 0xE5902020\n"
        ".word 0xE3720001, 0x0A000017, 0xE1520005, 0x1A000015\n"
        ".word 0xE1D002F4, 0xEB01DDD1, 0xE3500000, 0xE320F000\n"
        ".word 0x0A000005, 0xE3740001, 0xE58D4080, 0x0A000006\n"
        ".word 0xE3740002, 0x13A00004, 0x1AFFFFDB, 0xE3A00005\n"
        ".word 0xE58D0068, 0xE3A00000, 0xE58D0080, 0xE5D6000A\n"
        ".word 0xE3500012, 0x0A00001C, 0xE59D0080, 0xE3700001\n"
        ".word 0x0A000015, 0xEA000018, 0xE2844001, 0xEBFF3110\n"
        ".word 0xE1500004, 0xE320F000, 0xCAFFFFDD, 0xE3E04000\n"
        ".word 0xE58D4080, 0xE3790001, 0x0AFFFFEF, 0xE1A00009\n"
        ".word 0xEBFF3115, 0xE1D010B8, 0xE3510000, 0x01D010BA\n"
        ".word 0x03510000, 0x1A000008, 0xE1D000DC, 0xE3500000\n"
        ".word 0x13500030, 0x03E09000, 0xEA000003, 0xE59D0084\n"
        ".word 0xE3700001, 0x03180102, 0x0A0001B9, 0xE320F000\n"
        ".word 0xEB024DEE, 0xE2507000, 0xE3A05000, 0xDA000017\n"
        ".word 0xE1A00005, 0xEBFFE95F, 0xE1A04000, 0xE5900020\n"
        ".word 0xE3700001, 0x0A000011, 0xE1D402F6, 0xE3500000\n"
        ".word 0x0A000003, 0xEB01130C, 0xE3500000, 0xE320F000\n"
        ".word 0x1A000007, 0xE5940020, 0xE1500008, 0x1A000004\n"
        ".word 0xE1D402B4, 0xEB007433, 0xE3500000, 0xE320F000\n"
        ".word 0x0A00000A, 0xE2855001, 0xE1550007, 0xBAFFFFE7\n"
        ".word 0xE3E05000, 0xE1D640DA, 0xE3790001, 0x0A000008\n"
        ".word 0xE3540003, 0x1354000B, 0x0A000002, 0xEA000004\n"
        ".word 0xE6BF5075, 0xEAFFFFF6, 0xE1A00009, 0xEBFF30DE\n"
        ".word 0xE3A04010, 0xE6BF0074, 0xE1A07000, 0xEB01BBFD\n"
        ".word 0xE1A0A000, 0xE1A00007, 0xEB01903D, 0xE58D000C\n"
        ".word 0xE1D600DA, 0xEB01BAFB, 0xE58D0004, 0xE1D601F6\n"
        ".word 0xE1D621F8, 0xE1D631FA, 0xE1D6C1FC, 0xEE010A90\n"
        ".word 0xEE012A10, 0xEE003A90, 0xEE00CA10, 0xE1D601DE\n"
        ".word 0xE28D3044, 0xEEF89AE1, 0xEEB88AC1, 0xEEB89AE0\n"
        ".word 0xEEF88AC0, 0xE28D2048, 0xE28D104C, 0xEB01BB8C\n"
        ".word 0xE1D671DF, 0xE1D6C1D1, 0xE35A0001, 0x0A000002\n"
        ".word 0xE35A0000, 0x0A000063, 0xEA000084, 0xE1D601F4\n"
        ".word 0xE28D1034, 0xE5D63013, 0xE5D62012, 0xE8810081\n"
        ".word 0xEEF02A68, 0xE1CD22FC, 0xE5D62010, 0xE1CD00D8\n"
        ".word 0xE28D3020, 0xE58D201C, 0xE58D1028, 0xE8831001\n"
        ".word 0xE28D100C, 0xE5D6C00F, 0xE5D6300E, 0xE5D6200D\n"
        ".word 0xE5D6000C, 0xEEB01A49, 0xEEF00A48, 0xE881100D\n"
        ".word 0xEEB00A69, 0xE1A03004, 0xE5D6000B, 0xE59D1004\n"
        ".word 0xE28F2C03, 0xE58D0008, 0xE88D0802, 0xE59D1060\n"
        ".word 0xED9D2A12, 0xEDDD1A13, 0xE1A00008, 0xEBFF4CDC\n"
        ".word 0xE3540002, 0x01D601DE, 0x0A00000A, 0xAA000003\n"
        ".word 0xE3540000, 0x13540001, 0x0A000003, 0xEA00005B\n"
        ".word 0xE354000A, 0x1354002A, 0x1A000058, 0xE1D601DE\n"
        ".word 0xE3540001, 0x0A000002, 0xE3540002, 0x1A00000C\n"
        ".word 0xEA000026, 0xE3500000, 0x03A0000D, 0x0A000008\n"
        ".word 0xE3500003, 0x0A000005, 0xE3500004, 0x03A00011\n"
        ".word 0x0A000003, 0xE3500009, 0x13A0000B, 0x1A000000\n"
        ".word 0xE3A0000F, 0xE3A01000, 0xE1CD02FC, 0xE58D1034\n"
        ".word 0xE58D1038, 0xE58D1028, 0xE58D1020, 0xE58D1024\n"
        ".word 0xE58D1014, 0xE3E00000, 0xE58D101C, 0xE58D100C\n"
        ".word 0xE58D1010, 0xE58D1018, 0xE58D1000, 0xE1CD00F4\n"
        ".word 0xED9D0A12, 0xEE780A4A, 0xEEB03A68, 0xEE302A0A\n"
        ".word 0xEEF02A6A, 0xEEB01A49, 0xEEB00A69, 0xEDDD1A13\n"
        ".word 0xE3A03039, 0xE28F2F85, 0xE3A00003, 0xEA00002A\n"
        ".word 0xE3500000, 0x03A0000C, 0x0AFFFFE1, 0xE3500003\n"
        ".word 0x03A0000E, 0x0AFFFFDE, 0xE3500004, 0x03A00010\n"
        ".word 0x13A0000A, 0xEAFFFFDA, 0xE1D601F4, 0xE28D1034\n"
        ".word 0xE5D63013, 0xE5D62012, 0xE8810081, 0xEEB03A68\n"
        ".word 0xE1CD22FC, 0xE28D3008, 0xE5D60010, 0xE8930006\n"
        ".word 0xE28D301C, 0xEEB01A49, 0xEEF00A48, 0xE58D2028\n"
        ".word 0xE8831003, 0xE28D100C, 0xE5D6C00F, 0xE5D6200D\n"
        ".word 0xE5D6300E, 0xE5D6000C, 0xEEB00A69, 0xE881100D\n"
        ".word 0xE1A03004, 0xE28F2F62, 0xE5D6000B, 0xE59D1004\n"
        ".word 0xE58D0008, 0xE88D0802, 0xE59D1060, 0xEDDD2A11\n"
        ".word 0xED9D2A12, 0xEDDD1A13, 0xE1A00008, 0xEBFF9F19\n"
        ".word 0xE59D0084, 0xE3700001, 0x0A000037, 0xEB023282\n"
        ".word 0xE59F6150, 0xE5901000, 0xE1D070FA, 0xE1A04000\n"
        ".word 0xE596C004, 0xE280A00C, 0xE3A00000, 0xE35C0000\n"
        ".word 0xC59F3134, 0xDA000012, 0xE0602200, 0xE0822280\n"
        ".word 0xE0832182, 0xE592212C, 0xE1520001, 0x1A000009\n"
        ".word 0xE0601200, 0xE0810280, 0xE1A0100A, 0xE0830180\n"
        ".word 0xE5A07134, 0xE2800004, 0xEB010D60, 0xE320F000\n"
        ".word 0xE320F000, 0xEA000002, 0xE2800001, 0xE15C0000\n"
        ".word 0xCAFFFFEC, 0xE5963004, 0xE5941000, 0xE1D470F6\n"
        ".word 0xE3530000, 0xE1D440F8, 0xC59F20CC, 0xE3A00000\n"
        ".word 0xDA000011, 0xE060C200, 0xE08CC280, 0xE082C18C\n"
        ".word 0xE59CC12C, 0xE15C0001, 0x1A000008, 0xE0601200\n"
        ".word 0xE0810280, 0xE3A03000, 0xE0820180, 0xE2801C01\n"
        ".word 0xE1C176B0, 0xE1C146B2, 0xE5C03164, 0xEA000002\n"
        ".word 0xE2800001, 0xE1530000, 0xCAFFFFED, 0xE3790001\n"
        ".word 0x0A000058, 0xE1A00009, 0xEBFF2FF7, 0xE1D060F8\n"
        ".word 0xE5901000, 0xE1A04000, 0xE3560000, 0x0A00001B\n"
        ".word 0xE59F0050, 0xE5902004, 0xE3A00000, 0xE3520000\n"
        ".word 0xC59FC044, 0xDA000030, 0xE0603200, 0xE0833280\n"
        ".word 0xE08C3183, 0xE593312C, 0xE1530001, 0x1A00000B\n"
        ".word 0xE0601200, 0xE0810280, 0xE08C0180, 0xE2800C01\n"
        ".word 0xE1C065BC, 0xEA000024, 0x594C4F50, 0x00000000\n"
        ".word 0x0000414E, 0x00584F42, 0x00447A28, 0x004A1264\n"
        ".word 0xE2800001, 0xE1520000, 0xCAFFFFEA, 0xEA00001A\n"
        ".word 0xE51F0020, 0xE1D460FA, 0xE284700C, 0xE5902004\n"
        ".word 0xE3A00000, 0xE3520000, 0xC51FC034, 0xDA000012\n"
        ".word 0xE0603200, 0xE0833280, 0xE08C3183, 0xE593312C\n"
        ".word 0xE1530001, 0x1A000009, 0xE0601200, 0xE0810280\n"
        ".word 0xE1A01007, 0xE08C0180, 0xE5A06134, 0xE2800004\n"
        ".word 0xEB010D06, 0xE320F000, 0xE320F000, 0xEA000002\n"
        ".word 0xE2800001, 0xE1520000, 0xCAFFFFEC, 0xE51F008C\n"
        ".word 0xE5941000, 0xE1D460F4, 0xE1D440F6, 0xE5902004\n"
        ".word 0xE3A00000, 0xE3520000, 0xC51FC0A4, 0xDA000011\n"
        ".word 0xE0603200, 0xE0833280, 0xE08C3183, 0xE593312C\n"
        ".word 0xE1530001, 0x1A000008, 0xE0601200, 0xE0810280\n"
        ".word 0xE3A02000, 0xE08C0180, 0xE2801C01, 0xE1C166B0\n"
        ".word 0xE1C146B2, 0xE5C02164, 0xEA000002, 0xE2800001\n"
        ".word 0xE1520000, 0xCAFFFFED, 0xE59D0068, 0xE3500000\n"
        ".word 0x0A00001B, 0xE1A03000, 0xE51F0108, 0xE59D6080\n"
        ".word 0xE5901004, 0xE3A00000, 0xE3510000, 0xC51FC118\n"
        ".word 0xDA00000F, 0xE0602200, 0xE0822280, 0xE08C2182\n"
        ".word 0xE592212C, 0xE1520008, 0x1A000006, 0xE0601200\n"
        ".word 0xE0810280, 0xE08C0180, 0xE2800C01, 0xE1C036B6\n"
        ".word 0xE1C066B8, 0xEA000002, 0xE2800001, 0xE1510000\n"
        ".word 0xCAFFFFEF, 0xE59D0068, 0xE3500005, 0x01A00008\n"
        ".word 0x0B018E10, 0xE59D0078, 0xE3500000, 0x0A000019\n"
        ".word 0xE51F3930, 0xE2430008, 0xE5902004, 0xE3A00000\n"
        ".word 0xE3520000, 0xC51F1190, 0xDA000012, 0xE060C200\n"
        ".word 0xE08CC280, 0xE081C18C, 0xE59C412C, 0xE1540008\n"
        ".word 0x1A000009, 0xE0602200, 0xE0820280, 0xE0810180\n"
        ".word 0xE2800C01, 0xE280006E, 0xE1A01003, 0xEB00AE85\n"
        ".word 0xE320F000, 0xE320F000, 0xEA000002, 0xE2800001\n"
        ".word 0xE1520000, 0xCAFFFFEC, 0xE3750001, 0x0A000014\n"
        ".word 0xE51F01F0, 0xE5902004, 0xE3A00000, 0xE3520000\n"
        ".word 0xC51F11FC, 0xDA00000E, 0xE0603200, 0xE0833280\n"
        ".word 0xE0813183, 0xE593312C, 0xE1530008, 0x1A000005\n"
        ".word 0xE0602200, 0xE0820280, 0xE0810180, 0xE2800C01\n"
        ".word 0xE1C055BE, 0xEA000002, 0xE2800001, 0xE1520000\n"
        ".word 0xCAFFFFF0, 0xE59D007C, 0xE28BB001, 0xE150000B\n"
        ".word 0xCAFFFCB0, 0xE28DD08C, 0xECBD8B06, 0xE28DD008\n"
        ".word 0xE8BD8FF0\n"
    );
}

// Exact ARMv6K extent copied from the independently bounded code.bin span
// [0x0024C828, 0x0024D648). This includes the jump table and embedded pools.
// DECOMP_FUNC(0x0024c828, 3616)
__attribute__((naked)) void script_vm_func_0024c828(
    ScriptBattleContext*, s32, s32) {
    asm volatile(
        ".arm\n"
        ".word 0xE92D4FF0, 0xE24DDF71, 0xE1A04000, 0xE3A00000\n"
        ".word 0xE1A09001, 0xE58D0008, 0xE58D0004, 0xE1A07002\n"
        ".word 0xE1A00004, 0xEB00C8D1, 0xE5900028, 0xE2800C01\n"
        ".word 0xE1D004FC, 0xE350000C, 0x379FF100, 0xEA00005F\n"
        ".word 0x0024C9E8, 0x0024C898, 0x0024C8E8, 0x0024C8E8\n"
        ".word 0x0024C9E8, 0x0024C9E8, 0x0024C9E8, 0x0024C9E8\n"
        ".word 0x0024C92C, 0x0024C9E8, 0x0024C9E8, 0x0024C9C0\n"
        ".word 0xE1A00004, 0xEB00C8BD, 0xE5901020, 0xE3A00000\n"
        ".word 0xE5911000, 0xE3110010, 0x03A00001, 0xE58D0008\n"
        ".word 0xE1A00004, 0xEB00C8B5, 0xE5902020, 0xE5941000\n"
        ".word 0xE28D000C, 0xEBFFEB44, 0xE1DD00BC, 0xE3500000\n"
        ".word 0x0A000036, 0xEA000033, 0xE58D0004, 0xEA00003F\n"
        ".word 0xE1A00004, 0xEB00C8A9, 0xE5900028, 0xE59F5D44\n"
        ".word 0xE19050F5, 0xE1A00004, 0xEB00C8A4, 0xE5901020\n"
        ".word 0xE28D0004, 0xE58D0000, 0xE28D3008, 0xE1A02005\n"
        ".word 0xE1A00004, 0xEB06113D, 0xE320F000, 0xE320F000\n"
        ".word 0xEA00002E, 0xE1A00004, 0xEB00C898, 0xE5900028\n"
        ".word 0xE2800C01, 0xE1D004FE, 0xEB019FC3, 0xE1A03000\n"
        ".word 0xE1D006B2, 0xE3500000, 0xE1A00004, 0x0A00000A\n"
        ".word 0xEB00C88E, 0xE5901020, 0xE28D2004, 0xE58D2000\n"
        ".word 0xE1D326B2, 0xE28D3008, 0xE1A00004, 0xEB061127\n"
        ".word 0xE320F000, 0xE320F000, 0xEA000018, 0xE320F000\n"
        ".word 0xEB00C882, 0xE5901020, 0xE3A00001, 0xE5911000\n"
        ".word 0xE3110010, 0x03A00000, 0xE58D0008, 0xE5D3006A\n"
        ".word 0xE3100080, 0x0A000001, 0xE3A00001, 0xEAFFFFC9\n"
        ".word 0xE3A00000, 0xEAFFFFC7, 0xE1A00004, 0xEB00C873\n"
        ".word 0xE5901020, 0xE3A00001, 0xE5911000, 0xE3110010\n"
        ".word 0x03A00000, 0xE58D0008, 0xE3A00000, 0xE58D0004\n"
        ".word 0xE59D8008, 0xE3A05000, 0xE5941000, 0xE0850205\n"
        ".word 0xE0800305, 0xE2811D7F, 0xE5911000, 0xE0816180\n"
        ".word 0xE1D606FE, 0xE3500000, 0xBA000015, 0xE5960000\n"
        ".word 0xE3100001, 0x0A000012, 0xE3100040, 0x1A000010\n"
        ".word 0xE3580001, 0x0A000002, 0xE3100010, 0x0A000003\n"
        ".word 0xEA00000B, 0xE3100010, 0x0A000009, 0xEA000005\n"
        ".word 0xE3100020, 0x0A000003, 0xEB05EEEC, 0xE3500000\n"
        ".word 0xE320F000, 0x0A000002, 0xE5961000, 0xE3811B01\n"
        ".word 0xE5861000, 0xE2855001, 0xE355006D, 0xBAFFFFDD\n"
        ".word 0xE59D2004, 0xE3520001, 0x13520002, 0x0A00001E\n"
        ".word 0xE359001C, 0x379FF109, 0xEA00001E, 0x0024CB10\n"
        ".word 0x0024CB18, 0x0024CBB4, 0x0024CBC4, 0x0024CBD4\n"
        ".word 0x0024CBE4, 0x0024CC68, 0x0024CCFC, 0x0024CD64\n"
        ".word 0x0024CDCC, 0x0024CE34, 0x0024CEC4, 0x0024CF10\n"
        ".word 0x0024CF60, 0x0024CFBC, 0x0024D014, 0x0024D03C\n"
        ".word 0x0024D0D8, 0x0024D14C, 0x0024D1C0, 0x0024D234\n"
        ".word 0x0024D2A8, 0x0024D31C, 0x0024D390, 0x0024D404\n"
        ".word 0x0024D478, 0x0024D500, 0x0024D594, 0xE59D1008\n"
        ".word 0xE1A00004, 0xEB0611B9, 0xE28DDF71, 0xE8BD8FF0\n"
        ".word 0xE3A00063, 0xEBFFC846, 0xE5941000, 0xE1A05000\n"
        ".word 0xE3A00000, 0xE2811D7F, 0xE3A0206D, 0xE5911000\n"
        ".word 0xE5913000, 0xE2811FA2, 0xE3130B01, 0x12800001\n"
        ".word 0xE2522001, 0x1AFFFFF9, 0xE3500003, 0xBA000009\n"
        ".word 0xE355001E, 0xAA000004, 0xE3A01003, 0xE1A00004\n"
        ".word 0xEB060E07, 0xE28DDF71, 0xE8BD8FF0, 0xE3550041\n"
        ".word 0xBA000008, 0xEA000014, 0xE320F000, 0xEB011C43\n"
        ".word 0xE2800C1F, 0xE1D00CB4, 0xE3500002, 0x1A000006\n"
        ".word 0xE3550028, 0xAA00000C, 0xE3A01002, 0xE1A00004\n"
        ".word 0xEB060DF7, 0xE28DDF71, 0xE8BD8FF0, 0xE1A00004\n"
        ".word 0xEB060A05, 0xE28DDF71, 0xE8BD8FF0, 0xE1A00004\n"
        ".word 0xEBFF73D7, 0xE28DDF71, 0xE8BD8FF0, 0xE1A00004\n"
        ".word 0xEB060B92, 0xE28DDF71, 0xE8BD8FF0, 0xE5940000\n"
        ".word 0xE59F2A54, 0xE3A03000, 0xE2800D7F, 0xE3A0606D\n"
        ".word 0xE5901000, 0xE28D700C, 0xE281CF6E, 0xE281506E\n"
        ".word 0xE5910000, 0xE2000B01, 0xE3500000, 0x11DC00F0\n"
        ".word 0x11520000, 0xDA000003, 0xE1D580F0, 0xE1A02000\n"
        ".word 0xE7878103, 0xE2833001, 0xE2566001, 0xE2811FA2\n"
        ".word 0xE28CCFA2, 0xE2855FA2, 0x1AFFFFF0, 0xE3530000\n"
        ".word 0x0AFFFFD9, 0xE1A00004, 0xEB00C7D0, 0xE0871103\n"
        ".word 0xE2800038, 0xE5111004, 0xE3A02001, 0xEA000118\n"
        ".word 0xE5941000, 0xE1A00004, 0xE3A03000, 0xE2811D7F\n"
        ".word 0xE1A02003, 0xE5911000, 0xE3A0606D, 0xE28D400C\n"
        ".word 0xE281CF6E, 0xE281506E, 0xE5917000, 0xE2077B01\n"
        ".word 0xE3570000, 0x11DC70F0, 0x11570002, 0xDA000003\n"
        ".word 0xE1D580F0, 0xE1A02007, 0xE7848103, 0xE2833001\n"
        ".word 0xE2566001, 0xE2811FA2, 0xE28CCFA2, 0xE2855FA2\n"
        ".word 0x1AFFFFF0, 0xE3530000, 0x0A000005, 0xEB00C7AF\n"
        ".word 0xE0841103, 0xE2800038, 0xE5111004, 0xE3A02001\n"
        ".word 0xEA0000F7, 0xE320F000, 0xEB0609B7, 0xE28DDF71\n"
        ".word 0xE8BD8FF0, 0xE5940000, 0xE3A06001, 0xE1A08716\n"
        ".word 0xE2800D7F, 0xE3A01000, 0xE5900000, 0xE3A0C06D\n"
        ".word 0xE28D500C, 0xE2802C01, 0xE28220C6, 0xE280306E\n"
        ".word 0xE5907000, 0xE3170B01, 0x0A000005, 0xE1D270B0\n"
        ".word 0xE1170008, 0x0A000002, 0xE1D370F0, 0xE7857101\n"
        ".word 0xE2811001, 0xE25CC001, 0xE2800FA2, 0xE2822FA2\n"
        ".word 0xE2833FA2, 0x1AFFFFF1, 0xEA00004C, 0xE5940000\n"
        ".word 0xE3A06001, 0xE1A07716, 0xE2800D7F, 0xE3A01000\n"
        ".word 0xE5900000, 0xE3A0C06D, 0xE28D500C, 0xE2802C01\n"
        ".word 0xE28220C6, 0xE280306E, 0xE5908000, 0xE3180B01\n"
        ".word 0x0A000005, 0xE1D280B0, 0xE1180007, 0x1A000002\n"
        ".word 0xE1D380F0, 0xE7858101, 0xE2811001, 0xE25CC001\n"
        ".word 0xE2800FA2, 0xE2822FA2, 0xE2833FA2, 0x1AFFFFF1\n"
        ".word 0xEA000032, 0xE5940000, 0xE3A06001, 0xE1A07716\n"
        ".word 0xE2800D7F, 0xE3A01000, 0xE5900000, 0xE3A0C06D\n"
        ".word 0xE28D500C, 0xE2802C01, 0xE28220C6, 0xE280306E\n"
        ".word 0xE5908000, 0xE3180B01, 0x0A000005, 0xE1D280B0\n"
        ".word 0xE1180007, 0x0A000002, 0xE1D380F0, 0xE7858101\n"
        ".word 0xE2811001, 0xE25CC001, 0xE2800FA2, 0xE2822FA2\n"
        ".word 0xE2833FA2, 0x1AFFFFF1, 0xEA000018, 0xE5940000\n"
        ".word 0xE3A06001, 0xE1A07716, 0xE2800D7F, 0xE3A01000\n"
        ".word 0xE5900000, 0xE3A0C06D, 0xE28D500C, 0xE2802C01\n"
        ".word 0xE28220C6, 0xE280306E, 0xE5908000, 0xE3180B01\n"
        ".word 0x0A000005, 0xE1D280B0, 0xE1180007, 0x1A000002\n"
        ".word 0xE1D380F0, 0xE7858101, 0xE2811001, 0xE25CC001\n"
        ".word 0xE2800FA2, 0xE2822FA2, 0xE2833FA2, 0x1AFFFFF1\n"
        ".word 0xE2410001, 0xE6FF0070, 0xEBFFC765, 0xE1A03000\n"
        ".word 0xE1A00004, 0xEB00C739, 0xE7951103, 0xE2800038\n"
        ".word 0xE7C16000, 0xE28DDF71, 0xE8BD8FF0, 0xE5940000\n"
        ".word 0xE3A01000, 0xE3A0306D, 0xE2800D7F, 0xE28D500C\n"
        ".word 0xE5900000, 0xE280206E, 0xE590C000, 0xE31C0B01\n"
        ".word 0x131C0020, 0x0A000002, 0xE1D2C0F0, 0xE785C101\n"
        ".word 0xE2811001, 0xE2533001, 0xE2800FA2, 0xE2822FA2\n"
        ".word 0x1AFFFFF4, 0xEA000171, 0xE5940000, 0xE3A01000\n"
        ".word 0xE3A0306D, 0xE2800D7F, 0xE28D500C, 0xE5900000\n"
        ".word 0xE280206E, 0xE590C000, 0xE31C0B01, 0x0A000004\n"
        ".word 0xE31C0020, 0x1A000002, 0xE1D2C0F0, 0xE785C101\n"
        ".word 0xE2811001, 0xE2533001, 0xE2800FA2, 0xE2822FA2\n"
        ".word 0x1AFFFFF3, 0xEA00015D, 0xE5940000, 0xE3A01000\n"
        ".word 0xE3A0C06D, 0xE2800D7F, 0xE28D500C, 0xE5900000\n"
        ".word 0xE28020CE, 0xE280306E, 0xE5906000, 0xE3160B01\n"
        ".word 0x0A000005, 0xE1D260B0, 0xE1560007, 0x1A000002\n"
        ".word 0xE1D360F0, 0xE7856101, 0xE2811001, 0xE25CC001\n"
        ".word 0xE2800FA2, 0xE2822FA2, 0xE2833FA2, 0x1AFFFFF1\n"
        ".word 0xEA000146, 0xE5940000, 0xE3A01000, 0xE3A0C06D\n"
        ".word 0xE2800D7F, 0xE28D500C, 0xE5900000, 0xE28020CE\n"
        ".word 0xE280306E, 0xE5906000, 0xE3160B01, 0x11D260B0\n"
        ".word 0x11560007, 0x0A000002, 0xE1D360F0, 0xE7856101\n"
        ".word 0xE2811001, 0xE25CC001, 0xE2800FA2, 0xE2822FA2\n"
        ".word 0xE2833FA2, 0x1AFFFFF2, 0xEA000130, 0xE1A00004\n"
        ".word 0xEB00C6DE, 0xE1D032BC, 0xE1A00004, 0xEB00C6DB\n"
        ".word 0xE2800038, 0xE3A01001, 0xE7C31000, 0xE28DDF71\n"
        ".word 0xE8BD8FF0, 0xE3A05000, 0xE1A03005, 0xE28D600C\n"
        ".word 0xE3A0706E, 0xE5941000, 0xE0830203, 0xE0808303\n"
        ".word 0xE2811D7F, 0xE5910000, 0xE7900188, 0xE3100B01\n"
        ".word 0x0A00000B, 0xE1A00004, 0xEB00C6C8, 0xE1A01000\n"
        ".word 0xE5940000, 0xE0872188, 0xE1D112BC, 0xE2800D7F\n"
        ".word 0xE5900000, 0xE19000F2, 0xE1510000, 0x17860105\n"
        ".word 0x12855001, 0xE2833001, 0xE353006D, 0xBAFFFFE8\n"
        ".word 0xE2450001, 0xE6FF0070, 0xEBFFC6E1, 0xE1A03000\n"
        ".word 0xE1A00004, 0xEB00C6B5, 0xE7961103, 0xE2800038\n"
        ".word 0xE3A02001, 0xE7C12000, 0xE28DDF71, 0xE8BD8FF0\n"
        ".word 0xE5942000, 0xE3A01000, 0xE1A00001, 0xE2822D7F\n"
        ".word 0xE28D500C, 0xE5922000, 0xE3A06003, 0xE3A080CC\n"
        ".word 0xE3A0906E, 0xE0803200, 0xE0833300, 0xE792C183\n"
        ".word 0xE31C0B01, 0x0A00000A, 0xE088C183, 0xE08CC002\n"
        ".word 0xE08CC087, 0xE28CCC01, 0xE1DCC2B6, 0xE156052C\n"
        ".word 0x1A000003, 0xE0893183, 0xE19230F3, 0xE7853101\n"
        ".word 0xE2811001, 0xE2800001, 0xE350006D, 0xBAFFFFEC\n"
        ".word 0xEA000104, 0xE5942000, 0xE3A01000, 0xE1A00001\n"
        ".word 0xE2822D7F, 0xE28D500C, 0xE5922000, 0xE3A0C0CC\n"
        ".word 0xE3A06004, 0xE3A0806E, 0xE0803200, 0xE0833300\n"
        ".word 0xE7929183, 0xE3190B01, 0x0A00000A, 0xE08C9183\n"
        ".word 0xE0899002, 0xE0899087, 0xE2899C01, 0xE1D992B6\n"
        ".word 0xE1560529, 0x1A000003, 0xE0883183, 0xE19230F3\n"
        ".word 0xE7853101, 0xE2811001, 0xE2800001, 0xE350006D\n"
        ".word 0xBAFFFFEC, 0xEA0000C5, 0xE5942000, 0xE3A01000\n"
        ".word 0xE1A00001, 0xE2822D7F, 0xE28D600C, 0xE5922000\n"
        ".word 0xE3A080CC, 0xE3A05001, 0xE3A0906E, 0xE0803200\n"
        ".word 0xE0833300, 0xE792C183, 0xE31C0B01, 0x0A00000A\n"
        ".word 0xE088C183, 0xE08CC002, 0xE08CC087, 0xE28CCC01\n"
        ".word 0xE1DCC2B6, 0xE155052C, 0x1A000003, 0xE0893183\n"
        ".word 0xE19230F3, 0xE7863101, 0xE2811001, 0xE2800001\n"
        ".word 0xE350006D, 0xBAFFFFEC, 0xEA0000F7, 0xE5942000\n"
        ".word 0xE3A01000, 0xE1A00001, 0xE2822D7F, 0xE28D500C\n"
        ".word 0xE5922000, 0xE3A06002, 0xE3A080CC, 0xE3A0906E\n"
        ".word 0xE0803200, 0xE0833300, 0xE792C183, 0xE31C0B01\n"
        ".word 0x0A00000A, 0xE088C183, 0xE08CC002, 0xE08CC087\n"
        ".word 0xE28CCC01, 0xE1DCC2B6, 0xE156052C, 0x1A000003\n"
        ".word 0xE0893183, 0xE19230F3, 0xE7853101, 0xE2811001\n"
        ".word 0xE2800001, 0xE350006D, 0xBAFFFFEC, 0xEA00008B\n"
        ".word 0xE5942000, 0xE3A01000, 0xE1A00001, 0xE2822D7F\n"
        ".word 0xE28D500C, 0xE5922000, 0xE3A0C003, 0xE3A060CC\n"
        ".word 0xE3A0806E, 0xE0803200, 0xE0833300, 0xE7929183\n"
        ".word 0xE3190B01, 0x0A00000A, 0xE0869183, 0xE0899002\n"
        ".word 0xE0899087, 0xE2899C01, 0xE1D992B6, 0xE15C0529\n"
        ".word 0x0A000003, 0xE0883183, 0xE19230F3, 0xE7853101\n"
        ".word 0xE2811001, 0xE2800001, 0xE350006D, 0xBAFFFFEC\n"
        ".word 0xEA00006E, 0xE5942000, 0xE3A01000, 0xE1A00001\n"
        ".word 0xE2822D7F, 0xE28D500C, 0xE5922000, 0xE3A060CC\n"
        ".word 0xE3A08004, 0xE3A0906E, 0xE0803200, 0xE0833300\n"
        ".word 0xE792C183, 0xE31C0B01, 0x0A00000A, 0xE086C183\n"
        ".word 0xE08CC002, 0xE08CC087, 0xE28CCC01, 0xE1DCC2B6\n"
        ".word 0xE158052C, 0x0A000003, 0xE0893183, 0xE19230F3\n"
        ".word 0xE7853101, 0xE2811001, 0xE2800001, 0xE350006D\n"
        ".word 0xBAFFFFEC, 0xEA000051, 0xE5942000, 0xE3A01000\n"
        ".word 0xE1A00001, 0xE2822D7F, 0xE28D600C, 0xE5922000\n"
        ".word 0xE3A0C0CC, 0xE3A05001, 0xE3A0906E, 0xE0803200\n"
        ".word 0xE0833300, 0xE7928183, 0xE3180B01, 0x0A00000A\n"
        ".word 0xE08C8183, 0xE0888002, 0xE0888087, 0xE2888C01\n"
        ".word 0xE1D882B6, 0xE1550528, 0x0A000003, 0xE0893183\n"
        ".word 0xE19230F3, 0xE7863101, 0xE2811001, 0xE2800001\n"
        ".word 0xE350006D, 0xBAFFFFEC, 0xEA000083, 0xE5942000\n"
        ".word 0xE3A01000, 0xE1A00001, 0xE2822D7F, 0xE3A06002\n"
        ".word 0xE5922000, 0xE28D500C, 0xE3A080CC, 0xE3A0906E\n"
        ".word 0xE0803200, 0xE0833300, 0xE792C183, 0xE31C0B01\n"
        ".word 0x0A00000A, 0xE088C183, 0xE08CC002, 0xE08CC087\n"
        ".word 0xE28CCC01, 0xE1DCC2B6, 0xE156052C, 0x0A000003\n"
        ".word 0xE0893183, 0xE19230F3, 0xE7853101, 0xE2811001\n"
        ".word 0xE2800001, 0xE350006D, 0xBAFFFFEC, 0xEA000017\n"
        ".word 0xE5940000, 0xE3A02072, 0xE0822087, 0xE2800D7F\n"
        ".word 0xE3A01000, 0xE5900000, 0xE3A0C06D, 0xE28D500C\n"
        ".word 0xE0822000, 0xE280306E, 0xE5906000, 0xE3160B01\n"
        ".word 0x0A000005, 0xE1D260F0, 0xE3560001, 0xBA000002\n"
        ".word 0xE1D360F0, 0xE7856101, 0xE2811001, 0xE25CC001\n"
        ".word 0xE2800FA2, 0xE2822FA2, 0xE2833FA2, 0x1AFFFFF1\n"
        ".word 0xE2410001, 0xE6FF0070, 0xEBFFC5D5, 0xE1A03000\n"
        ".word 0xE1A00004, 0xEB00C5A9, 0xE7951103, 0xE2800038\n"
        ".word 0xE3A02001, 0xEAFFFEF2, 0xE5940000, 0xE3A02072\n"
        ".word 0xE0822087, 0xE2800D7F, 0xE3A01000, 0xE5900000\n"
        ".word 0xE3A0C06D, 0xE28D500C, 0xE0822000, 0xE280306E\n"
        ".word 0xE5906000, 0xE3160B01, 0x0A000005, 0xE1D260F0\n"
        ".word 0xE3760001, 0xCA000002, 0xE1D360F0, 0xE7856101\n"
        ".word 0xE2811001, 0xE25CC001, 0xE2800FA2, 0xE2822FA2\n"
        ".word 0xE2833FA2, 0x1AFFFFF1, 0xE2410001, 0xE6FF0070\n"
        ".word 0xEBFFC5B3, 0xE1A03000, 0xE1A00004, 0xEB00C587\n"
        ".word 0xE1A01000, 0xE7950103, 0xE2811038, 0xE3A02001\n"
        ".word 0xE7C02001, 0xE28DDF71, 0xE8BD8FF0, 0xE5942000\n"
        ".word 0xE3A01000, 0xE1A00001, 0xE2822D7F, 0xE3A08003\n"
        ".word 0xE5922000, 0xE3A0C0CC, 0xE3A09004, 0xE3A05001\n"
        ".word 0xE3A0B06E, 0xE28D600C, 0xE0803200, 0xE0833300\n"
        ".word 0xE792A183, 0xE31A0B01, 0x0A00000C, 0xE08CA183\n"
        ".word 0xE08AA002, 0xE08AA087, 0xE28AAC01, 0xE1DAA2B6\n"
        ".word 0xE158052A, 0x1159052A, 0x1155052A, 0x0A000003\n"
        ".word 0xE08B3183, 0xE19230F3, 0xE7863101, 0xE2811001\n"
        ".word 0xE2800001, 0xE350006D, 0xBAFFFFEA, 0xE2410001\n"
        ".word 0xE6FF0070, 0xEBFFC586, 0xE1A03000, 0xE1A00004\n"
        ".word 0xEB00C55A, 0xE7961103, 0xE2800038, 0xE7C15000\n"
        ".word 0xE28DDF71, 0xE8BD8FF0, 0x0000014E, 0x00002710\n"
    );
}

} // namespace smt4::script
