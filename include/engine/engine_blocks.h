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

// ---------------------------------------------------------------------------
// Reconstructed entry point (ledger name)
// ---------------------------------------------------------------------------

/**
 * 0x00236958, 3,552 B: builds the render command list and the four per-kind
 * pointer lists from the descriptor.  `resize_last` (r1) gates the final
 * 0x50 list (checked at 0x00237408).  Returns 0 or 0x80000000 when an
 * allocator call fails.
 */
s32 engine_func_00236958(RenderListContext* ctx, s32 resize_last);

} // namespace smt4::engine
