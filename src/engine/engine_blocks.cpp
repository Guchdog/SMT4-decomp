#include "engine/engine_blocks.h"

namespace smt4::engine {

// ---------------------------------------------------------------------------
// .bss singletons (all zero in code.bin; filled by the lazy blocks below).
// ---------------------------------------------------------------------------

u32 g_RenderInit_471f74 = 0;
u32 g_RenderInit_471f70 = 0;
u32 g_RenderInit_471f6c = 0;
u32 g_RenderInit_471f68 = 0;
u32 g_RenderInit_471f64 = 0;
u32 g_RenderInit_471f60 = 0;
u32 g_RenderInit_471f5c = 0;
u32 g_RenderInit_471f58 = 0;
u32 g_RenderInit_471f54 = 0;
u32 g_RenderInit_471f50 = 0;
u32 g_RenderInit_471f4c = 0;
u32 g_RenderInit_471f48 = 0;

AsdRenderNode8  g_RenderNode_471f78 = {};
AsdRenderNode8  g_RenderNode_471f80 = {};
AsdRenderNode8  g_RenderNode_471f88 = {};
AsdRenderNode8  g_RenderNode_471f90 = {};
AsdRenderNode8  g_RenderNode_471f98 = {};
AsdRenderNode8  g_RenderNode_471fa0 = {};
AsdRenderNode8  g_RenderNode_471fa8 = {};
AsdRenderNode8  g_RenderNode_471fb0 = {};
AsdRenderNode8  g_RenderNode_471fb8 = {};
AsdRenderNode8  g_RenderNode_471fc0 = {};
AsdRenderNode8  g_RenderNode_471fc8 = {};
AsdRenderNode16 g_RenderNode_4e9db8 = {};

// 0x002C00D4: Thumb test-and-set.  Sets the word to 1 and returns 1 only when
// it was zero; returns 0 otherwise.  The canonical declaration also appears in
// asd_sound.cpp / asd_effect2.cpp; it is not part of asd_symbols.h.
extern "C" s32 AsdFlag_TestAndSet(u32* flag);

namespace {

using AsdAllocFn = void* (*)(void* owner, u32 size, u32 align);
using AsdReleaseFn = void (*)(void* owner, void* block);

// `ldr r2,[owner]; ldr r3,[r2,#8]; blx r3` with (owner,size,align).
void* Allocate(void* owner, u32 size, u32 align) {
    void** vtable = *reinterpret_cast<void***>(owner);
    return reinterpret_cast<AsdAllocFn>(vtable[2])(owner, size, align);
}

// `ldr r0,[ctx]; ldr r2,[r0,#0xc]; blx r2` with (ctx, begin).
void Release(void* owner, void* block) {
    if (owner == nullptr || block == nullptr) {
        return;
    }
    void** vtable = *reinterpret_cast<void***>(owner);
    reinterpret_cast<AsdReleaseFn>(vtable[3])(owner, block);
}

// 0x00236A04..0x00236A28 and the four phase-2 copies: swap in the temporary
// vector and release the previous storage.
void ReplaceVector(AsdPtrVector* target, const AsdPtrVector& temp) {
    const AsdPtrVector old = *target;
    *target = temp;
    if (old.begin != nullptr) {
        Release(old.ctx, old.begin);
    }
}

// 0x00237168..0x002371F8 / 0x00237328..0x002373C0 / 0x002374F8..:
// "inline capacity" growth.  Allocates a fixed 0x20-byte block, copies the
// current contents, releases the old block and keeps the two capacity tag
// bits.  This path is reached only for vectors carrying tag 0x40000000; the
// lists built by this routine are reset with tag 0 first, so it is retained
// for completeness of the listing.
void GrowInlineEight(AsdPtrVector* vec, s32 requested) {
    void** block = static_cast<void**>(Allocate(vec->ctx, 0x20, 8));
    if (block == nullptr) {
        return;
    }
    s32 count = 0;
    for (void** it = vec->begin; it != vec->end; ++it) {
        block[count++] = *it;
    }
    void* old = vec->begin;
    if (old != nullptr) {
        Release(vec->ctx, old);
    }
    const u32 tag = vec->capacity & 0xC0000000u;
    vec->begin = block;
    vec->end = block + count;
    vec->capacity = tag | static_cast<u32>(requested);
}

// 0x00237030..0x00237080 and its three repeats.
void ResizeVector(AsdPtrVector* vec, s32 requested) {
    const u32 capacity = vec->capacity & 0xC0000000u;
    const s32 count = static_cast<s32>(vec->end - vec->begin);
    if (requested < count) {
        vec->end = vec->begin + (requested < 0 ? 0 : requested);
        return;
    }
    if ((vec->capacity & 0x3FFFFFFFu) < static_cast<u32>(requested)) {
        if (vec->ctx != nullptr && capacity == 0x40000000u) {
            GrowInlineEight(vec, requested);
            return;
        }
        vec->end = vec->begin + static_cast<s32>(vec->capacity & 0x3FFFFFFFu);
        return;
    }
    vec->end = vec->begin + requested;
}

template <typename Node>
void EnsureNode(u32* flag, Node* node, void* vtable, u8 visible, u8 enabled) {
    if ((*flag & 1u) == 0 && AsdFlag_TestAndSet(flag) != 0) {
        node->vtable = vtable;
        node->visible = visible;
        node->enabled = enabled;
    }
}

// 0x00236AB4..0x00236E90: the twelve lazy registrations.  The vtable pointers
// are the .rodata words referenced by the listing; the object and flag
// addresses are the ones in the switch table at 0x00236EA0.
void EnsureRenderNodes() {
    EnsureNode(&g_RenderInit_471f74, &g_RenderNode_471f78,
               reinterpret_cast<void*>(0x00421BECu), 1, 0);
    EnsureNode(&g_RenderInit_471f70, &g_RenderNode_471f80,
               reinterpret_cast<void*>(0x00421BC8u), 0, 0);
    EnsureNode(&g_RenderInit_471f6c, &g_RenderNode_471f88,
               reinterpret_cast<void*>(0x00421C10u), 1, 0);
    EnsureNode(&g_RenderInit_471f68, &g_RenderNode_471f90,
               reinterpret_cast<void*>(0x00421C58u), 1, 0);
    EnsureNode(&g_RenderInit_471f64, &g_RenderNode_471f98,
               reinterpret_cast<void*>(0x00421C7Cu), 1, 0);
    EnsureNode(&g_RenderInit_471f60, &g_RenderNode_471fa0,
               reinterpret_cast<void*>(0x00421CB0u), 1, 0);
    EnsureNode(&g_RenderInit_471f5c, &g_RenderNode_471fa8,
               reinterpret_cast<void*>(0x00421C34u), 0, 0);
    EnsureNode(&g_RenderInit_471f58, &g_RenderNode_471fb0,
               reinterpret_cast<void*>(0x00421328u), 1, 1);
    EnsureNode(&g_RenderInit_471f54, &g_RenderNode_471fb8,
               reinterpret_cast<void*>(0x0042134Cu), 1, 1);
    EnsureNode(&g_RenderInit_471f50, &g_RenderNode_471fc0,
               reinterpret_cast<void*>(0x00421268u), 1, 1);
    EnsureNode(&g_RenderInit_471f4c, &g_RenderNode_471fc8,
               reinterpret_cast<void*>(0x004213A0u), 1, 1);

    // 0x00236E54..0x00236E90: the last node lives at 0x004E9DB8 and also
    // stores 0x0042134C at +0x08 plus two 1-bytes at +0x0C/+0x0D.
    if ((g_RenderInit_471f48 & 1u) == 0 &&
        AsdFlag_TestAndSet(&g_RenderInit_471f48) != 0) {
        g_RenderNode_4e9db8.vtable = reinterpret_cast<void*>(0x00421170u);
        g_RenderNode_4e9db8.visible = 1;
        g_RenderNode_4e9db8.enabled = 1;
        g_RenderNode_4e9db8.extra = reinterpret_cast<void*>(0x0042134Cu);
        g_RenderNode_4e9db8.flag_0c = 1;
        g_RenderNode_4e9db8.flag_0d = 1;
    }
}

// 0x00236E94..0x00236F30: jump table at 0x00236EA0 over ids 0..0x0B.  The
// default returns null.
void* SelectRenderNode(u32 id) {
    switch (id) {
    case 0:  return &g_RenderNode_471f78;
    case 1:  return &g_RenderNode_471f80;
    case 2:  return &g_RenderNode_471f88;
    case 3:  return &g_RenderNode_471f90;
    case 4:  return &g_RenderNode_471f98;
    case 5:  return &g_RenderNode_471fa0;
    case 6:  return &g_RenderNode_471fa8;
    case 7:  return &g_RenderNode_471fb0;
    case 8:  return &g_RenderNode_471fb8;
    case 9:  return &g_RenderNode_471fc0;
    case 10: return &g_RenderNode_471fc8;
    case 11: return &g_RenderNode_4e9db8;
    default: return nullptr;
    }
}

// Builds the temporary `{owner, block, block, count}` vector used by every
// reset site (0x002369B4..0x002369C8, 0x00236F98..0x00236FB8, ...).
AsdPtrVector MakeVector(void* owner, void** block, u32 count) {
    AsdPtrVector vec{};
    vec.ctx = owner;
    vec.begin = block;
    vec.end = block;
    vec.capacity = count;
    return vec;
}

inline u32* IdArray(RenderListSource* source) {
    return reinterpret_cast<u32*>(
        reinterpret_cast<u8*>(source) + 0x1C + source->rel_1c);
}

} // namespace

// ---------------------------------------------------------------------------
// 0x00236958: render-list builder.
//
// Phase 1 (0x00236968..0x00236F50) allocates a `count_18`-entry command vector
// and fills it with the render-node singleton selected by each id in the
// relative id array at source+0x1C.  Each iteration first runs the twelve
// lazy registrations.
//
// Phase 2 (0x00236F54..0x002375D0) allocates four `count_10`-entry pointer
// lists at +0x20/+0x30/+0x40/+0x50 and sizes each one through the tagged
// vector protocol.  The final list is only built when r1 (resize_last) is
// non-zero (0x00237408).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00236958, 3552)
s32 engine_func_00236958(RenderListContext* ctx, s32 resize_last) {
    u32 status = 0;                            // r5
    RenderListSource* source = ctx->source;    // r0/r4+8
    const s32 command_count = source->count_18;

    // 0x00236970..0x00236998.
    void** command_block = static_cast<void**>(
        Allocate(ctx->allocator,
                 static_cast<u32>(command_count) << 2, 4));
    if (command_block == nullptr) {
        status |= 0x80000000u;
        return static_cast<s32>(status);
    }

    // 0x0023699C..0x00236A28: swap the new command vector into +0x0C.
    const AsdPtrVector command_temp =
        MakeVector(ctx->allocator, command_block,
                   static_cast<u32>(command_count));
    ReplaceVector(&ctx->commands, command_temp);

    // 0x00236A2C..0x00236F50: id -> render node.
    if (command_count > 0) {
        for (s32 i = 0; i < command_count; ++i) {
            EnsureRenderNodes();               // 0x00236AB4..0x00236E90

            const u32 id = IdArray(source)[i]; // 0x00236AA0..0x00236AB0
            void* node = SelectRenderNode(id); // 0x00236E94..0x00236F30

            // 0x00236F34..0x00236F48: push through end, then advance.
            void** end = ctx->commands.end;
            ctx->commands.end = end + 1;
            if (end != nullptr) {
                *end = node;
            }
        }
    }

    // ---- Phase 2: the four pointer lists ---------------------------------
    const s32 list_count = source->count_10;   // r6
    const u32 list_bytes = static_cast<u32>(list_count) << 2;

    // +0x20 (0x00236F8C..0x00237080)
    void** block = static_cast<void**>(Allocate(ctx->allocator, list_bytes, 4));
    if (block == nullptr) {
        status |= 0x80000000u;
        return static_cast<s32>(status);
    }
    ReplaceVector(&ctx->list_a,
                  MakeVector(ctx->allocator, block,
                             static_cast<u32>(list_count)));
    ResizeVector(&ctx->list_a, list_count);

    // +0x30 (0x00237084..0x0023723C)
    block = static_cast<void**>(Allocate(ctx->allocator, list_bytes, 4));
    if (block == nullptr) {
        status |= 0x80000000u;
        return static_cast<s32>(status);
    }
    ReplaceVector(&ctx->list_b,
                  MakeVector(ctx->allocator, block,
                             static_cast<u32>(list_count)));
    ResizeVector(&ctx->list_b, list_count);

    // +0x40 (0x00237240..0x00237404)
    block = static_cast<void**>(Allocate(ctx->allocator, list_bytes, 4));
    if (block == nullptr) {
        status |= 0x80000000u;
        return static_cast<s32>(status);
    }
    ReplaceVector(&ctx->list_c,
                  MakeVector(ctx->allocator, block,
                             static_cast<u32>(list_count)));
    ResizeVector(&ctx->list_c, list_count);

    // +0x50 (0x00237408..0x002375CC), gated by the r1 argument.
    if (resize_last != 0) {
        block = static_cast<void**>(Allocate(ctx->allocator, list_bytes, 4));
        if (block == nullptr) {
            status |= 0x80000000u;
            return static_cast<s32>(status);
        }
        ReplaceVector(&ctx->list_d,
                      MakeVector(ctx->allocator, block,
                                 static_cast<u32>(list_count)));
        ResizeVector(&ctx->list_d, list_count);
    }

    return static_cast<s32>(status);
}

} // namespace smt4::engine
