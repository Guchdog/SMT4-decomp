#pragma once
#include <cstddef>
#include "types.h"
#include "engine/asd_model.h"

/**
 * Engine runtime block A: the render-list / command-list builder at
 * 0x00236958.
 *
 * The routine consumes a small descriptor (source + five growable pointer
 * vectors) and lazily constructs the twelve static render-node singletons at
 * 0x00471F78..0x00471FC8 and 0x004E9DB8.  Only offsets proven by the listing
 * are named.
 */

namespace smt4::engine {

/**
 * Input descriptor at context+0x08.
 *   +0x10  count for the four output lists    (`ldr r6,[r0,#0x10]`, 0x00236F58)
 *   +0x18  count for the command list         (`ldr sl,[r0,#0x18]`, 0x0023696C)
 *   +0x1C  relative offset to a u32 id array  (`ldr r2,[r0,#0x1c]!`, 0x00236AA0)
 * The id array base is source + 0x1C + rel_1c (0x00236AA8).
 */
struct RenderListSource {
    u8  pad_000[0x10];
    s32 count_10;                       // +0x10: `ldr r6,[r0,#0x10]`
    u8  pad_014[4];
    s32 count_18;                       // +0x18: `ldr sl,[r0,#0x18]`
    s32 rel_1c;                         // +0x1C: `ldr r2,[r0,#0x1c]!`
};
static_assert(offsetof(RenderListSource, count_10) == 0x10);
static_assert(offsetof(RenderListSource, count_18) == 0x18);
static_assert(offsetof(RenderListSource, rel_1c) == 0x1C);

/**
 * The context passed in r0.  `commands` is at +0x0C (the routine swaps a
 * temporary `{allocator, begin, begin, count}` into it at 0x002369D0) and the
 * four output lists follow at +0x20/+0x30/+0x40/+0x50.
 */
struct RenderListContext {
    u8  pad_000[4];
    void* allocator;                    // +0x04: `ldr r0,[r4,#4]`
                                        //   (0x00236970)
    RenderListSource* source;           // +0x08: `ldr r0,[r4,#8]`
                                        //   (0x00236968)
    AsdPtrVector commands;              // +0x0C: `add r0,r4,#0xc`
                                        //   (0x002369AC)
    u8  pad_01c[4];
    AsdPtrVector list_a;                // +0x20: `add r0,r4,#0x20`
                                        //   (0x00236F9C)
    AsdPtrVector list_b;                // +0x30: `add r0,r4,#0x30`
                                        //   (0x002370C0)
    AsdPtrVector list_c;                // +0x40: `add r0,r4,#0x40`
                                        //   (0x0023727C)
    AsdPtrVector list_d;                // +0x50: `add r0,r4,#0x50`
                                        //   (0x00237450)
};
static_assert(offsetof(RenderListContext, allocator) == 0x04);
static_assert(offsetof(RenderListContext, source) == 0x08);
static_assert(offsetof(RenderListContext, commands) == 0x0C);
static_assert(offsetof(RenderListContext, list_a) == 0x20);
static_assert(offsetof(RenderListContext, list_b) == 0x30);
static_assert(offsetof(RenderListContext, list_c) == 0x40);
static_assert(offsetof(RenderListContext, list_d) == 0x50);

/**
 * One lazily constructed render node.  The first word is the .rodata vtable
 * (0x00421BEC etc.); +0x04/+0x05 are set from the immediate byte pair in each
 * construction block; the two pad bytes are never read.
 */
struct AsdRenderNode8 {
    void* vtable;                       // +0x00: `vstr s0,[r0]` where s0
                                        //   holds the 0x00421xxx word
                                        //   (0x00236AE8..0x00236AF4)
    u8  visible;                        // +0x04: `strb r1,[r0,#4]`
                                        //   (0x00236AE0)
    u8  enabled;                        // +0x05: `strb r2,[r0,#5]`
                                        //   (0x00236AE4)
    u8  pad_006[2];
};
static_assert(sizeof(AsdRenderNode8) == 0x08);
static_assert(offsetof(AsdRenderNode8, visible) == 0x04);
static_assert(offsetof(AsdRenderNode8, enabled) == 0x05);

/**
 * The twelfth node (0x004E9DB8) additionally carries a second .rodata pointer
 * at +0x08 and the byte pair at +0x0C/+0x0D (`str sb,[r0,#8]`,
 * `strb r2,[r0,#0xc]`, `strb r2,[r0,#0xd]`, 0x00236E80..0x00236E74).
 */
struct AsdRenderNode16 {
    void* vtable;                       // +0x00: `str r1,[r0]`
    u8  visible;                        // +0x04: `strb r1,[r0,#4]`
    u8  enabled;                        // +0x05: `strb r1,[r0,#5]`
    u8  pad_006[2];
    void* extra;                        // +0x08: `str sb,[r0,#8]`
    u8  flag_0c;                        // +0x0C: `strb r2,[r0,#0xc]`
    u8  flag_0d;                        // +0x0D: `strb r2,[r0,#0xd]`
    u8  pad_00e[2];
};
static_assert(sizeof(AsdRenderNode16) == 0x10);
static_assert(offsetof(AsdRenderNode16, extra) == 0x08);
static_assert(offsetof(AsdRenderNode16, flag_0c) == 0x0C);

// ---------------------------------------------------------------------------
// Lazily initialised singletons (all .bss in code.bin).
// The flag words live immediately before each object except the last one.
// ---------------------------------------------------------------------------

extern u32 g_RenderInit_471f74;             // -> g_RenderNode_471f78
extern u32 g_RenderInit_471f70;             // -> g_RenderNode_471f80
extern u32 g_RenderInit_471f6c;             // -> g_RenderNode_471f88
extern u32 g_RenderInit_471f68;             // -> g_RenderNode_471f90
extern u32 g_RenderInit_471f64;             // -> g_RenderNode_471f98
extern u32 g_RenderInit_471f60;             // -> g_RenderNode_471fa0
extern u32 g_RenderInit_471f5c;             // -> g_RenderNode_471fa8
extern u32 g_RenderInit_471f58;             // -> g_RenderNode_471fb0
extern u32 g_RenderInit_471f54;             // -> g_RenderNode_471fb8
extern u32 g_RenderInit_471f50;             // -> g_RenderNode_471fc0
extern u32 g_RenderInit_471f4c;             // -> g_RenderNode_471fc8
extern u32 g_RenderInit_471f48;             // -> g_RenderNode_4e9db8

extern AsdRenderNode8  g_RenderNode_471f78;
extern AsdRenderNode8  g_RenderNode_471f80;
extern AsdRenderNode8  g_RenderNode_471f88;
extern AsdRenderNode8  g_RenderNode_471f90;
extern AsdRenderNode8  g_RenderNode_471f98;
extern AsdRenderNode8  g_RenderNode_471fa0;
extern AsdRenderNode8  g_RenderNode_471fa8;
extern AsdRenderNode8  g_RenderNode_471fb0;
extern AsdRenderNode8  g_RenderNode_471fb8;
extern AsdRenderNode8  g_RenderNode_471fc0;
extern AsdRenderNode8  g_RenderNode_471fc8;
extern AsdRenderNode16 g_RenderNode_4e9db8;

/**
 * 0x0044E858: sentinel compared against the object returned by the virtual
 * `[r7]+8` call in the tail of 0x002AAD14 (0x002ABA44).  The listing walks the
 * result as a linked list through its first word until it either reaches this
 * slot or a null link (0x002ABA94).
 */
extern u32 g_EngineDrawSentinel_44e858;

// ---------------------------------------------------------------------------
// Runtime block B: draw-command dispatcher 0x002AAD14
//
// The routine receives a tagged descriptor (r6), a primary and an optional
// secondary draw stream (r1/r2), an owner context (r3) and four stack words.
// It selects one of 15 construction paths from the descriptor tag.
// ---------------------------------------------------------------------------

/**
 * Growable command stream at r5.
 *   +0x00 write cursor        (`ldr ip,[r5]`, 0x002AAE38)
 *   +0x04 current alignment   (`ldr r3,[r5,#4]`, 0x002AAE34)
 *   +0x08 maximum alignment   (`ldr ip,[r5,#8]`, 0x002AAE6C)
 */
struct DrawStream {
    u32* cursor;                        // +0x00
    u32  align;                         // +0x04
    u32  max_align;                     // +0x08
};
static_assert(offsetof(DrawStream, cursor) == 0x00);
static_assert(offsetof(DrawStream, align) == 0x04);
static_assert(offsetof(DrawStream, max_align) == 0x08);

/**
 * Source descriptor at r4.  Only the fields read by the tag paths are named.
 * `field_24` and `field_04` are byte members (`ldrb r0,[r4,#0x24]`,
 * 0x002AAE1C / `ldrb r0,[r4,#4]`, 0x002AADFC).
 */
struct EngineDrawDesc {
    u8  pad_000[4];
    u8  field_04;                       // +0x04
    u32 field_08;                       // +0x08
    u32 field_0c;                       // +0x0C
    u32 field_10;                       // +0x10
    u32 field_14;                       // +0x14
    u32 field_18;                       // +0x18
    u32 field_1c;                       // +0x1C
    u32 field_20;                       // +0x20
    u8  field_24;                       // +0x24
};
static_assert(offsetof(EngineDrawDesc, field_04) == 0x04);
static_assert(offsetof(EngineDrawDesc, field_08) == 0x08);
static_assert(offsetof(EngineDrawDesc, field_0c) == 0x0C);
static_assert(offsetof(EngineDrawDesc, field_10) == 0x10);
static_assert(offsetof(EngineDrawDesc, field_14) == 0x14);
static_assert(offsetof(EngineDrawDesc, field_18) == 0x18);
static_assert(offsetof(EngineDrawDesc, field_1c) == 0x1C);
static_assert(offsetof(EngineDrawDesc, field_20) == 0x20);
static_assert(offsetof(EngineDrawDesc, field_24) == 0x24);

/**
 * Tagged record at r6.  The tag is the first word; +0x20/+0x28/+0x2C/+0xE0 are
 * the only other members the dispatcher reads.
 */
struct EngineDrawPacked {
    u32 tag;                            // +0x00: `ldr r0,[r6]` (0x002AAD48)
    u8  pad_004[0x1C];
    u32 count_20;                       // +0x20: `ldr r1,[r0,#0x20]!`
                                        //   (0x002AB580)
    u8  pad_024[4];
    u32 count_28;                       // +0x28: `ldr r2,[r6,#0x28]`
                                        //   (0x002AAEF4)
    u32 rel_2c;                         // +0x2C: `ldr r3,[r0,#0x2c]`
                                        //   (0x002AB3F0)
    u8  pad_030[0xB0];
    u32 rel_e0;                         // +0xE0: `ldr r2,[r0,#0xc0]` with
                                        //   r0 = r6+0x20 (0x002AB588)
};
static_assert(offsetof(EngineDrawPacked, tag) == 0x00);
static_assert(offsetof(EngineDrawPacked, count_20) == 0x20);
static_assert(offsetof(EngineDrawPacked, count_28) == 0x28);
static_assert(offsetof(EngineDrawPacked, rel_2c) == 0x2C);
static_assert(offsetof(EngineDrawPacked, rel_e0) == 0xE0);

/**
 * One action-list entry allocated by 0x00226B2C and linked through +0x0C.
 * The dispatcher only touches the fields below.
 */
struct BattleAction {
    u8  pad_000[4];
    u8  kind;                           // +0x04: `strb r1,[r0,#4]`
                                        //   (0x002554D8)
    u8  flags;                          // +0x05: `ldrb r0,[r4,#5]`
                                        //   (0x00255EF0)
    u8  pad_006[2];
    void* actor;                        // +0x08: `ldr r2,[r0,#8]`
                                        //   (0x00255924)
    BattleAction* next;                 // +0x0C: `ldr r1,[r0,#0xc]`
                                        //   (0x0025591C)
    u8  pad_010[4];
    void* record;                       // +0x14: `str r6,[r0,#0x14]!`
                                        //   (0x002554DC)
    u32 field_18;                       // +0x18: `str r4,[r0,#0x18]!`
                                        //   (0x00255BDC)
    u8  pad_01c[8];
    s16 field_24;                       // +0x24: `strh r1,[r2,#0x24]`
                                        //   (0x002559B8)
    u32 field_28;                       // +0x28: `str r1,[r0,#0x28]`
                                        //   (0x002559F8)
    u8  pad_02c[4];
    f32 field_30;                       // +0x30: `vstr s17,[r0,#0x30]`
                                        //   (0x00255AA4)
    u8  pad_034[0x18];
    u32 field_4c;                       // +0x4C: `str r4,[r0,#0x4c]`
                                        //   (0x00255538)
};
static_assert(offsetof(BattleAction, kind) == 0x04);
static_assert(offsetof(BattleAction, flags) == 0x05);
static_assert(offsetof(BattleAction, actor) == 0x08);
static_assert(offsetof(BattleAction, next) == 0x0C);
static_assert(offsetof(BattleAction, record) == 0x14);
static_assert(offsetof(BattleAction, field_24) == 0x24);
static_assert(offsetof(BattleAction, field_28) == 0x28);
static_assert(offsetof(BattleAction, field_30) == 0x30);
static_assert(offsetof(BattleAction, field_4c) == 0x4C);

/** Action manager at 0x00434290; +0x08 is the head of the action list. */
struct BattleActionManager {
    u8  pad_000[8];
    BattleAction* head;                 // +0x08: `ldr r0,[lr,#8]`
                                        //   (0x0025590C)
};
static_assert(offsetof(BattleActionManager, head) == 0x08);

/**
 * One 0x114-byte battle unit record iterated by 0x002553EC (index * 0x114 is
 * formed by `add r1,r0,r0,lsl #2; add r1,r1,r0,lsl #6; ... lsl #2`,
 * 0x00255574..0x0025557C).
 */
struct BattleActorRecord {
    u8  pad_000[0x50];
    u32 flags_50;                       // +0x50: `ldr r2,[r1,#0x50]`
                                        //   (0x00255580)
    u8  pad_054[8];
    s32 offset_5c;                      // +0x5C: `ldr r2,[r4,#0x5c]`
                                        //   (0x00255840)
    u8  pad_060[2];
    s16 id_62;                          // +0x62: `ldrsh r1,[r4,#0x62]`
                                        //   (0x00255780)
    u8  pad_064[0x94];
    u32 flags_f8;                       // +0xF8: `ldr r3,[r4,#0xf8]`
                                        //   (0x00255774)
    u8  pad_fc[0x18];                   // +0xFC..+0x114 (table stride)
};
static_assert(offsetof(BattleActorRecord, flags_50) == 0x50);
static_assert(offsetof(BattleActorRecord, offset_5c) == 0x5C);
static_assert(offsetof(BattleActorRecord, id_62) == 0x62);
static_assert(offsetof(BattleActorRecord, flags_f8) == 0xF8);
static_assert(sizeof(BattleActorRecord) == 0x114);

/** 0x00439960: 12-byte effect row; only +0x0A is read (0x002559CC). */
struct BattleEffectRow {
    u8  pad_000[0x0A];
    u16 field_0a;                       // +0x0A: `ldrh r1,[r1,#0xa]`
                                        //   (0x002559CC)
};
static_assert(sizeof(BattleEffectRow) == 0x0C);
static_assert(offsetof(BattleEffectRow, field_0a) == 0x0A);

// ---------------------------------------------------------------------------
// Reconstructed entry points (ledger names)
// ---------------------------------------------------------------------------

/**
 * 0x00236958, 3,552 B: builds the render command list and the four per-kind
 * pointer lists from the descriptor.  `resize_last` (r1) gates the final
 * 0x50 list (checked at 0x00237408).  Returns 0 or 0x80000000 when an
 * allocator call fails.
 */
s32 engine_func_00236958(RenderListContext* ctx, s32 resize_last);

/**
 * 0x002AAD14, 3,484 B: tagged draw-command dispatcher.
 *
 * `desc` (r0) is the source descriptor, `out` (r1) the primary stream,
 * `out2` (r2) the optional secondary stream and `ctx` (r3) the owner passed as
 * r0 to the non-streaming builders.  `packed` (5th argument, r6) carries the
 * tag; `call_word` is the stack word at [sp+0x6C], `scale` the word at
 * [sp+0x70], `tail_arg` the pointer at [sp+0x74] and `commit` the r8 flag.
 */
s32 engine_func_002aad14(EngineDrawDesc* desc, DrawStream* out,
                         DrawStream* out2, void* ctx,
                         EngineDrawPacked* packed, u32 call_word, f32 scale,
                         void* tail_arg, s32 commit);

/**
 * 0x002553EC, 3,124 B: battle effect/action emitter.
 *
 * `base` (r0) is added to the unit-table offsets, `actor` (r1) is the acting
 * record, `attack` (r2) is the 0x114-byte unit record, `a3` is the r3 word and
 * `arg4`..`arg24` are the stack words at [sp+0x128]..[sp+0x178].  `arg7` and
 * `arg8` are the two floats loaded by `vldmia sp+0x134` (0x0025541C) and
 * `arg23` is the float read from [sp+0x174] (0x00255410).
 */
s32 battle_func_002553ec(s32 base, void* actor, BattleActorRecord* attack,
                         u32 a3, s32 arg4, s32 arg5, s32 arg6, f32 arg7,
                         f32 arg8, s32 arg9, s32 arg10, s32 arg11, s32 arg12,
                         s32 arg13, s32 arg14, s32 arg15, s32 arg16, s32 arg17,
                         s32 arg18, s32 arg19, s32 arg20, s32 arg21, s32 arg22,
                         f32 arg23, s32 arg24);

} // namespace smt4::engine
