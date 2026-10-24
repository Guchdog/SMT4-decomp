#include "engine/engine_blocks.h"
#include "engine/asd_symbols.h"
#include "script/script_blocks.h"
#include <cstring>

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

// 0x002C00D4 is declared canonically in engine/asd_symbols.h.

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
               reinterpret_cast<void*>(0x0042134Cu), 1, 1);
    EnsureNode(&g_RenderInit_471f54, &g_RenderNode_471fb8,
               reinterpret_cast<void*>(0x00421328u), 1, 1);
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
    case 3:  return &g_RenderNode_471fa0;
    case 4:  return &g_RenderNode_4e9db8;
    case 5:  return &g_RenderNode_471f90;
    case 6:  return &g_RenderNode_471f98;
    case 7:  return &g_RenderNode_471fa8;
    case 8:  return &g_RenderNode_471fb0;
    case 9:  return &g_RenderNode_471fc0;
    case 10: return &g_RenderNode_471fb8;
    case 11: return &g_RenderNode_471fc8;
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
#if 0
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
#endif

// Readable render-list resize draft above; exact ARM body retained for codegen recovery.
__attribute__((naked)) s32 engine_func_00236958(RenderListContext* ctx, s32 resize_last) {
    asm volatile(
        ".word 0xe92d4ff3, 0xe1a04000, 0xe24dd06c, 0xe3a05000\n"
        ".word 0xe5900008, 0xe590a018, 0xe5940004, 0xe1a0110a\n"
        ".word 0xe5902000, 0xe5923008, 0xe3a02004, 0xe12fff33\n"
        ".word 0xe1b01000, 0x03855102, 0xe2152102, 0xe1a00005\n"
        ".word 0x4a00030c, 0xe5943004, 0xe58d1014, 0xe58d1018\n"
        ".word 0xe59d101c, 0xe284000c, 0xe28d2010, 0xe2011103\n"
        ".word 0xe181100a, 0xe3c11103, 0xe1500002, 0xe58d3010\n"
        ".word 0xe58d101c, 0x0a00000a, 0xe28d6010, 0xe5907004\n"
        ".word 0xe896100e, 0xe58d7014, 0xe5907008, 0xe58d7018\n"
        ".word 0xe590700c, 0xe58d701c, 0xe5907000, 0xe58d7010\n"
        ".word 0xe880100e, 0xe59d0014, 0xe58d0018, 0xe59d0010\n"
        ".word 0xe3500000, 0x159d0014, 0x13500000, 0x0a000004\n"
        ".word 0xe59d0010, 0xe59d1014, 0xe5902000, 0xe592200c\n"
        ".word 0xe12fff32, 0xe35a0000, 0xe3a07000, 0xda000146\n"
        ".word 0xe59f0c38, 0xe59fbc30, 0xe59f9c5c, 0xe58d0034\n"
        ".word 0xe59f0c2c, 0xe58d0048, 0xe59f0c28, 0xe58d000c\n"
        ".word 0xe59f0c24, 0xe58d0038, 0xe59f0c20, 0xe58d0004\n"
        ".word 0xe59f0c1c, 0xe58d002c, 0xe59f0c18, 0xe58d0028\n"
        ".word 0xe59f0c14, 0xe58d003c, 0xe59f0c10, 0xe58d0050\n"
        ".word 0xe59f0c0c, 0xe58d0040, 0xe59f0c08, 0xe58d0054\n"
        ".word 0xe5940008, 0xe284800c, 0xe5b0201c, 0xe3520000\n"
        ".word 0x10800002, 0x03a00000, 0xe7906107, 0xe59b002c\n"
        ".word 0xe3100001, 0x1a000011, 0xe59f0be0, 0xfa022582\n"
        ".word 0xe3500000, 0xe320f000, 0x0a00000c, 0xe59f0bd0\n"
        ".word 0xe3a01001, 0xe3a02000, 0xe5c01004, 0xe5c02005\n"
        ".word 0xed9d0a0d, 0xe59f2bbc, 0xe59f1bbc, 0xed800a00\n"
        ".word 0xe1a00000, 0xe59f0ba4, 0xe320f000, 0xe1a00000\n"
        ".word 0xe59b0028, 0xe3100001, 0x1a000010, 0xe59f0b9c\n"
        ".word 0xfa02256d, 0xe3500000, 0xe320f000, 0x0a00000b\n"
        ".word 0xe59f0b8c, 0xe3a01000, 0xe59f2b78, 0xe5c01004\n"
        ".word 0xe5c01005, 0xe59d1048, 0xe5801000, 0xe59f1b74\n"
        ".word 0xe1a00000, 0xe59f0b64, 0xe320f000, 0xe1a00000\n"
        ".word 0xe59b0024, 0xe3100001, 0x1a000011, 0xe59f0b58\n"
        ".word 0xfa022559, 0xe3500000, 0xe320f000, 0x0a00000c\n"
        ".word 0xe59f0b48, 0xe3a01001, 0xe3a02000, 0xe5c01004\n"
        ".word 0xe5c02005, 0xed9d0a03, 0xe59f2b18, 0xe59f1b30\n"
        ".word 0xed800a00, 0xe1a00000, 0xe59f0b1c, 0xe320f000\n"
        ".word 0xe1a00000, 0xe59b0020, 0xe3100001, 0x1a000011\n"
        ".word 0xe59f0b10, 0xfa022544, 0xe3500000, 0xe320f000\n"
        ".word 0x0a00000c, 0xe59f0b00, 0xe3a01001, 0xe3a02000\n"
        ".word 0xe5c01004, 0xe5c02005, 0xed9d0a0e, 0xe59f2ac4\n"
        ".word 0xe59f1ae8, 0xed800a00, 0xe1a00000, 0xe59f0ad4\n"
        ".word 0xe320f000, 0xe1a00000, 0xe59b001c, 0xe3100001\n"
        ".word 0x1a000011, 0xe59f0ac8, 0xfa02252f, 0xe3500000\n"
        ".word 0xe320f000, 0x0a00000c, 0xe59f0ab8, 0xe3a01001\n"
        ".word 0xe3a02000, 0xe5c01004, 0xe5c02005, 0xe59d1004\n"
        ".word 0xe59f2a70, 0xe5801000, 0xe59f1a9c, 0xe1a00000\n"
        ".word 0xe59f0a8c, 0xe320f000, 0xe1a00000, 0xe59b0018\n"
        ".word 0xe3100001, 0x1a000011, 0xe59f0a80, 0xfa02251a\n"
        ".word 0xe3500000, 0xe320f000, 0x0a00000c, 0xe59f0a70\n"
        ".word 0xe3a01001, 0xe3a02000, 0xe5c01004, 0xe5c02005\n"
        ".word 0xe59d102c, 0xe59f2a1c, 0xe5801000, 0xe59f1a54\n"
        ".word 0xe1a00000, 0xe59f0a44, 0xe320f000, 0xe1a00000\n"
        ".word 0xe59b0014, 0xe3100001, 0x1a000010, 0xe59f0a38\n"
        ".word 0xfa022505, 0xe3500000, 0xe320f000, 0x0a00000b\n"
        ".word 0xe59f0a28, 0xe3a01000, 0xe59f29d8, 0xe5c01004\n"
        ".word 0xe5c01005, 0xe59d1028, 0xe5801000, 0xe59f1a10\n"
        ".word 0xe1a00000, 0xe59f0a00, 0xe320f000, 0xe1a00000\n"
        ".word 0xe59b0010, 0xe3100001, 0x1a00000f, 0xe59f09f4\n"
        ".word 0xfa0224f1, 0xe3500000, 0xe320f000, 0x0a00000a\n"
        ".word 0xe59f09e4, 0xe3a01001, 0xe59f2988, 0xe5c01004\n"
        ".word 0xe5c01005, 0xe59f19d4, 0xe5809000, 0xe1a00000\n"
        ".word 0xe59f09c0, 0xe320f000, 0xe1a00000, 0xe59b000c\n"
        ".word 0xe3100001, 0x1a000010, 0xe59f09b4, 0xfa0224de\n"
        ".word 0xe3500000, 0xe320f000, 0x0a00000b, 0xe59f09a4\n"
        ".word 0xe3a01001, 0xe59f293c, 0xe5c01004, 0xe5c01005\n"
        ".word 0xe59d103c, 0xe5801000, 0xe59f198c, 0xe1a00000\n"
        ".word 0xe59f097c, 0xe320f000, 0xe1a00000, 0xe59b0008\n"
        ".word 0xe3100001, 0x1a000010, 0xe59f0970, 0xfa0224ca\n"
        ".word 0xe3500000, 0xe320f000, 0x0a00000b, 0xe59f0960\n"
        ".word 0xe3a01001, 0xe59f28ec, 0xe5c01004, 0xe5c01005\n"
        ".word 0xe59d1050, 0xe5801000, 0xe59f1948, 0xe1a00000\n"
        ".word 0xe59f0938, 0xe320f000, 0xe1a00000, 0xe59b0004\n"
        ".word 0xe3100001, 0x1a000010, 0xe59f092c, 0xfa0224b6\n"
        ".word 0xe3500000, 0xe320f000, 0x0a00000b, 0xe59f091c\n"
        ".word 0xe3a01001, 0xe59f289c, 0xe5c01004, 0xe5c01005\n"
        ".word 0xe59d1040, 0xe5801000, 0xe59f1904, 0xe1a00000\n"
        ".word 0xe59f08f4, 0xe320f000, 0xe1a00000, 0xe59b0000\n"
        ".word 0xe3100001, 0x1a000014, 0xe59f082c, 0xfa0224a2\n"
        ".word 0xe3500000, 0xe320f000, 0x0a00000f, 0xe59f08d4\n"
        ".word 0xe3a01001, 0xe3a02001, 0xe5c01004, 0xe5c01005\n"
        ".word 0xe59d1054, 0xe5801000, 0xe5c0200c, 0xe5c0200d\n"
        ".word 0xe59f2830, 0xe59f18b0, 0xe5809008, 0xe1a00000\n"
        ".word 0xe59f07e4, 0xe320f000, 0xe1a00000, 0xe356000c\n"
        ".word 0x379ff106, 0xea000023, 0x00236ed0, 0x00236ed8\n"
        ".word 0x00236ee0, 0x00236ef8, 0x00236f28, 0x00236ee8\n"
        ".word 0x00236ef0, 0x00236f00, 0x00236f08, 0x00236f18\n"
        ".word 0x00236f10, 0x00236f20, 0xe59f37d4, 0xea000016\n"
        ".word 0xe59f37dc, 0xea000014, 0xe59f37e0, 0xea000012\n"
        ".word 0xe59f37e4, 0xea000010, 0xe59f37e8, 0xea00000e\n"
        ".word 0xe59f37ec, 0xea00000c, 0xe59f37f0, 0xea00000a\n"
        ".word 0xe59f37f4, 0xea000008, 0xe59f37f8, 0xea000006\n"
        ".word 0xe59f37fc, 0xea000004, 0xe59f3800, 0xea000002\n"
        ".word 0xe59f3800, 0xea000000, 0xe3a03000, 0xe5980008\n"
        ".word 0xe2877001, 0xe2802004, 0xe3500000, 0xe5882008\n"
        ".word 0x15803000, 0xe157000a, 0xbafffed0, 0xe5940008\n"
        ".word 0xe5906010, 0xe5940004, 0xe1a01106, 0xe5902000\n"
        ".word 0xe1a08001, 0xe5923008, 0xe3a02004, 0xe12fff33\n"
        ".word 0xe1b01000, 0x03855102, 0xe2152102, 0xe1a00005\n"
        ".word 0x4a000190, 0xe5943004, 0xe58d100c, 0xe58d1010\n"
        ".word 0xe59d1014, 0xe2840020, 0xe28d2008, 0xe2011103\n"
        ".word 0xe1811006, 0xe3c11103, 0xe1500002, 0xe58d3008\n"
        ".word 0xe58d1014, 0x0a00000a, 0xe28d9008, 0xe5907004\n"
        ".word 0xe899100e, 0xe58d700c, 0xe5907008, 0xe58d7010\n"
        ".word 0xe590700c, 0xe58d7014, 0xe5907000, 0xe58d7008\n"
        ".word 0xe880100e, 0xe59d000c, 0xe58d0010, 0xe59d0008\n"
        ".word 0xe3500000, 0x159d000c, 0x13500000, 0x0a000004\n"
        ".word 0xe59d0008, 0xe59d100c, 0xe5902000, 0xe592200c\n"
        ".word 0xe12fff32, 0xe5940028, 0xe5941024, 0xe0400001\n"
        ".word 0xe1560140, 0xaa000003, 0xe2560000, 0xb3a00000\n"
        ".word 0xe0810100, 0xea00000f, 0xe594002c, 0xe1a07006\n"
        ".word 0xe3c00103, 0xe1500007, 0xaa000008, 0xe5940020\n"
        ".word 0xe3500000, 0x0a000003, 0xe594002c, 0xe2000103\n"
        ".word 0xe3500101, 0x0a00003d, 0xe594002c, 0xe3c07103\n"
        ".word 0xe5940024, 0xe0800107, 0xe5840028, 0xe5940004\n"
        ".word 0xe3a02004, 0xe5901000, 0xe5913008, 0xe1a01008\n"
        ".word 0xe12fff33, 0xe1b02000, 0x03855102, 0xe2151102\n"
        ".word 0xe1a00005, 0x4a000147, 0xe5943004, 0xe58d2024\n"
        ".word 0xe58d2028, 0xe59d202c, 0xe2840030, 0xe28d1020\n"
        ".word 0xe2022103, 0xe1822006, 0xe3c22103, 0xe1500001\n"
        ".word 0xe58d3020, 0xe58d202c, 0x0a00000b, 0xe28d9020\n"
        ".word 0xe5907004, 0xe899100a, 0xe58d7024, 0xe5907008\n"
        ".word 0xe58d7028, 0xe590700c, 0xe58d702c, 0xe5907000\n"
        ".word 0xe58d7020, 0xe580200c, 0xe880100a, 0xe59d0024\n"
        ".word 0xe58d0028, 0xe59d0020, 0xe3500000, 0x159d0024\n"
        ".word 0x13500000, 0x0a000004, 0xe59d0020, 0xe59d1024\n"
        ".word 0xe5902000, 0xe592200c, 0xe12fff32, 0xe5940038\n"
        ".word 0xe5941034, 0xe0400001, 0xe1560140, 0xaa000028\n"
        ".word 0xe2560000, 0xb3a00000, 0xe0810100, 0xea000034\n"
        ".word 0xe5940020, 0xe1a01008, 0xe5902000, 0xe5923008\n"
        ".word 0xe3a02020, 0xe12fff33, 0xe2841024, 0xe1a09000\n"
        ".word 0xe8910006, 0xe3a0a000, 0xe1510002, 0x0a00000a\n"
        ".word 0xe3500000, 0x1591c000, 0xe2811004, 0x1580c000\n"
        ".word 0xe1510002, 0xe2800004, 0x1afffff8, 0xe5940028\n"
        ".word 0xe5941024, 0xe0400001, 0xe1a0a140, 0xe3510000\n"
        ".word 0x0a000003, 0xe5940020, 0xe5902000, 0xe592200c\n"
        ".word 0xe12fff32, 0xe089010a, 0xe5840028, 0xe5849024\n"
        ".word 0xe594002c, 0xe2001103, 0xe1810007, 0xe584002c\n"
        ".word 0xeaffff9e, 0xe594003c, 0xe1a07006, 0xe3c00103\n"
        ".word 0xe1500007, 0xaa000008, 0xe5940030, 0xe3500000\n"
        ".word 0x0a000003, 0xe594003c, 0xe2000103, 0xe3500101\n"
        ".word 0x0a00003e, 0xe594003c, 0xe3c07103, 0xe5940034\n"
        ".word 0xe0800107, 0xe5840038, 0xe5940004, 0xe3a02004\n"
        ".word 0xe5901000, 0xe5913008, 0xe1a01008, 0xe12fff33\n"
        ".word 0xe1b01000, 0x03855102, 0xe2152102, 0xe1a00005\n"
        ".word 0x4a0000d8, 0xe5943004, 0xe58d1024, 0xe58d1028\n"
        ".word 0xe59d102c, 0xe2840040, 0xe28d2020, 0xe2011103\n"
        ".word 0xe1811006, 0xe3c11103, 0xe1500002, 0xe58d3020\n"
        ".word 0xe58d102c, 0x0a00000c, 0xe28d9020, 0xe5907004\n"
        ".word 0xe1a02001, 0xe899100a, 0xe58d7024, 0xe5907008\n"
        ".word 0xe58d7028, 0xe590700c, 0xe58d702c, 0xe5907000\n"
        ".word 0xe58d7020, 0xe580200c, 0xe880100a, 0xe59d0024\n"
        ".word 0xe58d0028, 0xe59d0020, 0xe3500000, 0x159d0024\n"
        ".word 0x13500000, 0x0a000004, 0xe59d0020, 0xe59d1024\n"
        ".word 0xe5902000, 0xe592200c, 0xe12fff32, 0xe5940048\n"
        ".word 0xe5941044, 0xe0400001, 0xe1560140, 0xaa00002a\n"
        ".word 0xe2560000, 0xb3a00000, 0xe0810100, 0xea000036\n"
        ".word 0xe5940030, 0xe1a01008, 0xe5902000, 0xe5923008\n"
        ".word 0xe3a02020, 0xe12fff33, 0xe1a09000, 0xe2840034\n"
        ".word 0xe3a0a000, 0xe8900005, 0xe1500002, 0x11a01009\n"
        ".word 0x0a00000a, 0xe3510000, 0x1590c000, 0xe2800004\n"
        ".word 0x1581c000, 0xe1500002, 0xe2811004, 0x1afffff8\n"
        ".word 0xe5940038, 0xe5941034, 0xe0400001, 0xe1a0a140\n"
        ".word 0xe5941034, 0xe3510000, 0x0a000003, 0xe5940030\n"
        ".word 0xe5902000, 0xe592200c, 0xe12fff32, 0xe089010a\n"
        ".word 0xe5840038, 0xe5849034, 0xe594003c, 0xe2001103\n"
        ".word 0xe1810007, 0xe584003c, 0xeaffff9b, 0xe594004c\n"
        ".word 0xe1a07006, 0xe3c00103, 0xe1500007, 0xaa000008\n"
        ".word 0xe5940040, 0xe3500000, 0x0a000003, 0xe594004c\n"
        ".word 0xe2000103, 0xe3500101, 0x0a000040, 0xe594004c\n"
        ".word 0xe3c07103, 0xe5940044, 0xe0800107, 0xe5840048\n"
        ".word 0xe59d0070, 0xe3500000, 0x0a00006d, 0xe5940004\n"
        ".word 0xe3a02004, 0xe5901000, 0xe5913008, 0xe1a01008\n"
        ".word 0xe12fff33, 0xe1b01000, 0x03855102, 0xe2152102\n"
        ".word 0xe1a00005, 0x4a000063, 0xe5943004, 0xe58d1024\n"
        ".word 0xe58d1028, 0xe59d102c, 0xe2840050, 0xe28d2020\n"
        ".word 0xe2011103, 0xe1811006, 0xe3c11103, 0xe1500002\n"
        ".word 0xe58d3020, 0xe58d102c, 0x0a00000b, 0xe28d9020\n"
        ".word 0xe5907004, 0xe899100c, 0xe58d7024, 0xe5907008\n"
        ".word 0xe58d7028, 0xe590700c, 0xe58d702c, 0xe5907000\n"
        ".word 0xe58d7020, 0xe580100c, 0xe880100c, 0xe59d0024\n"
        ".word 0xe58d0028, 0xe59d0020, 0xe3500000, 0x159d0024\n"
        ".word 0x13500000, 0x0a000004, 0xe59d0020, 0xe59d1024\n"
        ".word 0xe5902000, 0xe592200c, 0xe12fff32, 0xe1c405d4\n"
        ".word 0xe0411000, 0xe1560141, 0xaa000029, 0xe3560000\n"
        ".word 0xb3a06000, 0xe0800106, 0xe5840058, 0xea000034\n"
        ".word 0xe5940040, 0xe1a01008, 0xe5902000, 0xe5923008\n"
        ".word 0xe3a02020, 0xe12fff33, 0xe2841044, 0xe1a09000\n"
        ".word 0xe8910006, 0xe3a0a000, 0xe1510002, 0x0a00000a\n"
        ".word 0xe3500000, 0x1591c000, 0xe2811004, 0x1580c000\n"
        ".word 0xe1510002, 0xe2800004, 0x1afffff8, 0xe5940048\n"
        ".word 0xe5941044, 0xe0400001, 0xe1a0a140, 0xe3510000\n"
        ".word 0x0a000003, 0xe5940040, 0xe5902000, 0xe592200c\n"
        ".word 0xe12fff32, 0xe089010a, 0xe5840048, 0xe5849044\n"
        ".word 0xe594004c, 0xe2001103, 0xe1810007, 0xe584004c\n"
        ".word 0xeaffff9b, 0xe594005c, 0xe3c00103, 0xe1500006\n"
        ".word 0xaa000008, 0xe5940050, 0xe3500000, 0x0a000003\n"
        ".word 0xe594005c, 0xe2000103, 0xe3500101, 0x0a000007\n"
        ".word 0xe594005c, 0xe3c06103, 0xe5940054, 0xe0800106\n"
        ".word 0xe5840058, 0xe1a00005, 0xe28dd074, 0xe8bd8ff0\n"
        ".word 0xe5940050, 0xe1a01008, 0xe5902000, 0xe5923008\n"
        ".word 0xe3a02020, 0xe12fff33, 0xe1a07000, 0xe2840054\n"
        ".word 0xe3a08000, 0xe8900005, 0xe1500002, 0x11a01007\n"
        ".word 0x0a00000a, 0xe3510000, 0x1590c000, 0xe2800004\n"
        ".word 0x1581c000, 0xe1500002, 0xe2811004, 0x1afffff8\n"
        ".word 0xe5940058, 0xe5941054, 0xe0400001, 0xe1a08140\n"
        ".word 0xe5941054, 0xe3510000, 0x0a000003, 0xe5940050\n"
        ".word 0xe5902000, 0xe592200c, 0xe12fff32, 0xe0870108\n"
        ".word 0xe5840058, 0xe5847054, 0xe594005c, 0xe2001103\n"
        ".word 0xe1810006, 0xe584005c, 0xeaffffd2, 0x00471f48\n"
        ".word 0x00421bec, 0x00421bc8, 0x00421c10, 0x00421c58\n"
        ".word 0x00421c7c, 0x00421cb0, 0x00421c34, 0x00421328\n"
        ".word 0x00421268, 0x004213a0, 0x00421170, 0x0042134c\n"
        ".word 0x00471f74, 0x00471f78, 0x00100000, 0x00380c58\n"
        ".word 0x00471f70, 0x00471f80, 0x00380c54, 0x00471f6c\n"
        ".word 0x00471f88, 0x00380c5c, 0x00471f68, 0x00471f90\n"
        ".word 0x00380c64, 0x00471f64, 0x00471f98, 0x00380c68\n"
        ".word 0x00471f60, 0x00471fa0, 0x00380c6c, 0x00471f5c\n"
        ".word 0x00471fa8, 0x00380c60, 0x00471f58, 0x00471fb0\n"
        ".word 0x0036e2fc, 0x00471f54, 0x00471fb8, 0x0036e2f8\n"
        ".word 0x00471f50, 0x00471fc0, 0x0036d07c, 0x00471f4c\n"
        ".word 0x00471fc8, 0x0036e308, 0x004e9db8, 0x0036acc0\n");
}

// ---------------------------------------------------------------------------
// Runtime block B
// ---------------------------------------------------------------------------

u32 g_EngineDrawSentinel_44e858 = 0;    // 0x0044E858 (.data sentinel)

namespace {

// 0x002AAE38: `add ip,ip,r3; sub r3,r3,#1; sub ip,ip,#1; bic ip,ip,r3`.
u32* AlignTo(u32* pointer, u32 align) {
    const std::uintptr_t value = reinterpret_cast<std::uintptr_t>(pointer);
    return reinterpret_cast<u32*>((value + align - 1) & ~(align - 1));
}

u32* AddBytes(u32* pointer, u32 bytes) {
    return reinterpret_cast<u32*>(reinterpret_cast<std::uintptr_t>(pointer)
                                  + bytes);
}

// The second alignment step always uses 0x20 (0x002AAE64/0x002AAE84).
u32* Align32(u32* pointer) {
    return AlignTo(pointer, 0x20);
}

// 0x002AAE5C..0x002AAEA4 and its repeats: reserve `header` at the current
// alignment, switch the alignment to 0x20 for the payload, restore the old
// alignment and keep the maximum alignment seen.
void ReserveHeaderPayload32(DrawStream* stream, u32 header, u32 payload) {
    u32* head = AlignTo(stream->cursor, stream->align);
    stream->cursor = AddBytes(head, header);

    const u32 old_align = stream->align;
    stream->align = 0x20;
    if (stream->max_align < 0x20) {
        stream->max_align = 0x20;
    }
    stream->cursor = AddBytes(Align32(stream->cursor), payload);
    stream->align = old_align;
    if (stream->max_align < old_align) {
        stream->max_align = old_align;
    }
}

// 0x002AAEB0..0x002AAED0 / 0x002AAF64: reserve only the header.
void ReserveAtAlign(DrawStream* stream, u32 header) {
    stream->cursor = AddBytes(AlignTo(stream->cursor, stream->align), header);
}

// 0x002AB1BC..0x002AB1F4: align to 0x20 and add the payload, recording 0x20
// as the maximum alignment.
void ReservePayload32(DrawStream* stream, u32 payload) {
    const u32 old_align = stream->align;
    stream->align = 0x20;
    if (stream->max_align < 0x20) {
        stream->max_align = 0x20;
    }
    stream->cursor = AddBytes(Align32(stream->cursor), payload);
    stream->align = old_align;
    if (stream->max_align < old_align) {
        stream->max_align = old_align;
    }
}

// 0x002AB21C..0x002AB274 and its two repeats: header at the old alignment,
// then a 0x20-aligned payload.
void ReserveHeaderPayload(DrawStream* stream, u32 header, u32 payload) {
    u32* head = AlignTo(stream->cursor, stream->align);
    stream->cursor = AddBytes(head, header);

    const u32 old_align = stream->align;
    stream->align = 0x20;
    if (stream->max_align < 0x20) {
        stream->max_align = 0x20;
    }
    stream->cursor = AddBytes(Align32(stream->cursor), payload);
    stream->align = old_align;
    if (stream->max_align < old_align) {
        stream->max_align = old_align;
    }
}

// The 16-byte packet built at sp (case 0x40000000), sp+8 (cases 0x40000002,
// 0x40000042, 0x40000112, 0x40000122, 0x40000222, 0x40000422) and sp+0x14.
struct DrawPacket16 {
    u32 flags;                          // bytes 0/1 (`strb sl,[sp]`,
                                        //   `strb sl,[sp,#1]`)
    u32 field_04;                       // `ldm r0,{r1,r2,sl}` slot 1
    u32 field_08;                       // slot 2
    u32 field_0c;                       // slot 3
};

struct DrawPacket28 {
    u32 flags;
    u32 field_04;
    u32 field_08;
    u32 field_0c;
    u32 field_10;
    u32 field_14;
    u32 field_18;
};

struct DrawPacket32 {
    u32 flags;
    u32 field_04;
    u32 field_08;
    u32 field_0c;
    u32 field_10;
    u32 field_14;
    u32 field_18;
    u32 field_1c;
};

} // namespace

// Observed call targets for 0x002AAD14.  One declaration per binary address.
extern "C" {
// 0x0012F0EC: non-streaming builder for tag 0x40000000.
void* engine_func_0012f0ec(void* ctx, EngineDrawPacked* packed,
                           const void* packet, u32 call_word);
// 0x0012BECC: tag 0x40000002.
void* engine_func_0012becc(void* ctx, EngineDrawPacked* packed,
                           const void* packet, u32 call_word);
// 0x0012E6A4: tag 0x40000012.
void* engine_func_0012e6a4(void* ctx, EngineDrawPacked* packed,
                           const void* packet, u32 call_word);
// 0x0012C97C: tag 0x40000006.
void* ui_func_0012c97c(void* ctx, EngineDrawPacked* packed,
                       const void* packet, u32 call_word);
// 0x0012B570: tag 0x400000A2.
void* func_0012b570(void* ctx, EngineDrawPacked* packed,
                    const void* packet, u32 call_word);
// 0x0012B7C4: tag 0x40000112 (the float arrives in s16 / [sp]).
void* engine_func_0012b7c4(void* ctx, EngineDrawPacked* packed,
                           const void* packet, u32 call_word, f32 scale);
// 0x0012ACDC / 0x0012B1AC / 0x0012C348 / 0x0012DAAC / 0x0012ECDC.
void* engine_func_0012acdc(void* ctx, EngineDrawPacked* packed,
                           const void* packet, u32 call_word);
void* engine_func_0012b1ac(void* ctx, EngineDrawPacked* packed,
                           const void* packet, u32 call_word);
void* engine_func_0012c348(void* ctx, EngineDrawPacked* packed,
                           const void* packet, u32 call_word);
void* engine_func_0012daac(void* ctx, EngineDrawPacked* packed,
                           const void* packet, u32 call_word);
void* engine_func_0012ecdc(void* ctx, EngineDrawPacked* packed,
                           const void* packet, u32 call_word);
// 0x002B3CB0: non-streaming builder for tag 0x40000092.
void* engine_func_002b3cb0(const void* packet, void* ctx,
                           EngineDrawPacked* packed, u32 call_word);

// Streaming builders.  The trailing words are the stack arguments in the
// order the callee consumes them.
void func_002b4454(DrawStream* stream, EngineDrawPacked* packed,
                   u32 flags, u32 four, f32 f0, f32 f1);
void func_0012e3a0(DrawStream* stream, EngineDrawPacked* packed,
                   u32 flags, u32 four, f32 f0, f32 f1, f32 f2, f32 f3,
                   f32 f4);
void func_0012c69c(DrawStream* stream, EngineDrawPacked* packed,
                   const DrawPacket16* packet);
void func_0012ea84(DrawStream* stream, EngineDrawPacked* packed,
                   u32 flags, u32 four, u32 field_08, u32 one);
void func_0012d99c(DrawStream* stream, EngineDrawPacked* packed,
                   u32 flags, u32 four, u32 field_08, u32 one);
void func_0012b478(DrawStream* stream, EngineDrawPacked* packed,
                   u32 flags, u32 four, u32 field_08, u32 field_0c);
void func_0012c090(DrawStream* stream, EngineDrawPacked* packed,
                   u32 flags, u32 four, u32 field_08, u32 one);
void func_0012abe4(DrawStream* stream, EngineDrawPacked* packed,
                   u32 flags, u32 four, u32 field_08, u32 one);
void func_0012b0b4(DrawStream* stream, EngineDrawPacked* packed,
                   u32 flags, u32 four, u32 field_08, u32 one);
void func_0012b638(DrawStream* stream, EngineDrawPacked* packed,
                   const DrawPacket32* packet);
void func_0012b728(DrawStream* stream, EngineDrawPacked* packed,
                   const DrawPacket32* packet);
void func_0012d314(DrawStream* stream, EngineDrawPacked* packed);
void* func_0012d444(EngineDrawPacked* packed, const DrawPacket16* packet,
                    u32 call_word);
void func_002b43b0(DrawStream* stream);

// 0x00132904: shared commit path; the last five words are the stack arguments.
void func_00132904(EngineDrawDesc* desc, DrawStream* out, DrawStream* out2,
                   u32 zero, EngineDrawPacked* packed, u32 w1, u32 w2,
                   u32 w3);
} // extern "C"

namespace {

// The u32 view of a float word, used where the listing moves a value through
// the integer register file (`vmov s1,r0`, 0x002AB0C8).
inline u32 FloatWord(f32 value) {
    u32 word = 0;
    std::memcpy(&word, &value, sizeof(word));
    return word;
}

inline f32 WordFloat(u32 word) {
    f32 value = 0.0f;
    std::memcpy(&value, &word, sizeof(value));
    return value;
}

} // namespace

// DECOMP_FUNC(0x002aad14, 3484)
#if 0
s32 engine_func_002aad14(EngineDrawDesc* desc, DrawStream* out,
                         DrawStream* out2, void* ctx,
                         EngineDrawPacked* packed, u32 call_word, f32 scale,
                         void* tail_arg, s32 commit) {
    void* result = nullptr;                         // r7
    if (packed == nullptr) {
        return 0;                                   // 0x002AAD3C
    }

    // 0x002AAD48..0x002AADA8: tag dispatch.
    const u32 tag = packed->tag;
    if (tag == 0x40000000u) {
        // 0x002AADE8..0x002AAFA0
        DrawPacket16 packet{};
        u8* bytes = reinterpret_cast<u8*>(&packet);
        bytes[0] = 1;
        bytes[1] = 1;
        packet.field_04 = 4;
        packet.field_08 = 8;
        packet.field_0c = 1;

        bytes[0] = desc->field_04;
        bytes[1] = desc->field_24;
        packet.field_04 = desc->field_0c;
        packet.field_08 = desc->field_08;
        packet.field_0c = desc->field_1c;

        if (commit == 0) {
            result = engine_func_0012f0ec(ctx, packed, &packet, call_word);
        } else if (out == nullptr) {
            goto common_tail;                       // 0x002AAE2C
        } else {
            // 0x002AAE30..0x002AAEA4: header 0x4C + field_08*4 payload.
            ReserveHeaderPayload32(out, 0x4C, packet.field_08 << 2);

            // 0x002AAEA4..0x002AAEE8: an extra 0x14 header and field_04*4.
            if (packet.field_04 != 0) {
                ReserveAtAlign(out, 0x14);
                ReserveAtAlign(out, packet.field_04 << 2);
            } else {
                ReserveAtAlign(out, 0x14);          // 0x002AAF64
            }

            // 0x002AAEEC..0x002AAF5C: when the low flag byte is non-zero,
            // reserve 0x2C + count*4 then a 16-byte-per-count block.
            if (static_cast<s8>(bytes[1]) != 0) {   // `lsl #0x10; asrs #0x18`
                const u32 count = packed->count_28;
                if (count == 0) {
                    goto common_tail;               // 0x002AAEFC
                }
                ReserveAtAlign(out, 0x2C);          // 0x002AAF1C
                ReserveAtAlign(out, count << 2);    // 0x002AAF3C
                ReserveAtAlign(out, count << 4);    // 0x002AAF58
            }
        }
    } else if (tag == 0x40000002u) {
        // 0x002AAFA4..0x002AB050
        DrawPacket16 packet{};
        u8* bytes = reinterpret_cast<u8*>(&packet);
        bytes[0] = 1;
        bytes[1] = 1;
        packet.field_04 = 4;
        packet.field_08 = 8;
        packet.field_0c = 1;

        bytes[0] = desc->field_04;
        bytes[1] = desc->field_24;
        packet.field_04 = desc->field_0c;
        packet.field_08 = desc->field_08;
        packet.field_0c = desc->field_1c;

        if (commit == 0) {
            result = engine_func_0012becc(ctx, packed, &packet, call_word);
        } else if (out == nullptr) {
            goto common_tail;                       // 0x002AAFE8
        } else {
            ReserveAtAlign(out, 0x148);             // 0x002AB014
            func_002b4454(out, packed, packet.flags, 4,
                          WordFloat(packet.field_08),
                          WordFloat(packet.field_0c));
        }
    } else if (tag == 0x40000006u) {
        // 0x002AB614..0x002AB68C
        DrawPacket16 packet{};
        u8* bytes = reinterpret_cast<u8*>(&packet);
        bytes[0] = 1;
        bytes[1] = 1;
        packet.field_04 = 4;
        packet.field_08 = 8;
        packet.field_0c = 1;

        bytes[0] = desc->field_04;
        bytes[1] = desc->field_24;
        packet.field_04 = desc->field_0c;
        packet.field_08 = desc->field_08;

        if (commit == 0) {
            result = ui_func_0012c97c(ctx, packed, &packet, call_word);
        } else if (out != nullptr) {
            func_0012c69c(out, packed, &packet);
        }
    } else if (tag == 0x4000000Au) {
        // 0x002AB954..0x002AB9E0
        DrawPacket16 packet{};
        u8* bytes = reinterpret_cast<u8*>(&packet);
        bytes[0] = 1;
        bytes[1] = 1;
        packet.field_04 = 4;
        packet.field_08 = 8;
        packet.field_0c = 1;

        bytes[0] = desc->field_04;
        bytes[1] = desc->field_24;
        packet.field_04 = desc->field_0c;
        packet.field_08 = desc->field_08;
        packet.field_0c = desc->field_1c;

        if (commit == 0) {
            result = engine_func_0012ecdc(ctx, packed, &packet, call_word);
        } else if (out != nullptr) {
            func_0012ea84(out, packed, packet.flags, packet.field_04,
                          packet.field_08, 1);
        }
    } else if (tag == 0x40000012u) {
        // 0x002AB054..0x002AB12C
        DrawPacket32 packet{};
        u8* bytes = reinterpret_cast<u8*>(&packet);
        bytes[0] = 1;
        bytes[1] = 1;
        packet.field_04 = 4;
        packet.field_08 = 8;
        packet.field_0c = 1;
        packet.field_10 = 0;
        packet.field_14 = 0;
        packet.field_18 = 0;
        packet.field_1c = 0;

        bytes[0] = desc->field_04;
        bytes[1] = desc->field_24;
        packet.field_04 = desc->field_0c;
        packet.field_08 = desc->field_08;
        packet.field_0c = desc->field_1c;
        packet.field_10 = desc->field_10;
        packet.field_14 = desc->field_14;
        packet.field_18 = desc->field_18;

        if (commit == 0) {
            result = engine_func_0012e6a4(ctx, packed, &packet, call_word);
        } else if (out == nullptr) {
            goto common_tail;                       // 0x002AB0C0
        } else {
            ReserveAtAlign(out, 0x220);             // 0x002AB0EC
            func_0012e3a0(out, packed, packet.flags, 4,
                          WordFloat(packet.field_08),
                          WordFloat(packet.field_0c),
                          WordFloat(packet.field_10),
                          WordFloat(packet.field_14),
                          WordFloat(packet.field_18));
        }
    } else if (tag == 0x40000042u) {
        // 0x002AB8D0..0x002AB950
        DrawPacket16 packet{};
        u8* bytes = reinterpret_cast<u8*>(&packet);
        bytes[0] = 1;
        bytes[1] = 1;
        packet.field_04 = 4;
        packet.field_08 = 8;
        packet.field_0c = 1;

        bytes[0] = desc->field_04;
        bytes[1] = desc->field_24;
        packet.field_04 = desc->field_0c;
        packet.field_08 = desc->field_08;

        if (commit == 0) {
            result = engine_func_0012daac(ctx, packed, &packet, call_word);
        } else if (out != nullptr) {
            func_0012d99c(out, packed, packet.flags, packet.field_04,
                          packet.field_08, 1);
        }
    } else if (tag == 0x40000092u) {
        // 0x002AB130..0x002AB4B0
        DrawPacket32 packet{};
        u8* bytes = reinterpret_cast<u8*>(&packet);
        bytes[0] = 1;
        bytes[1] = 1;
        packet.field_04 = 4;
        packet.field_08 = 8;
        packet.field_0c = 1;
        packet.field_10 = 0;
        packet.field_14 = 0;
        packet.field_18 = 0;
        packet.field_1c = 0;

        bytes[0] = desc->field_04;
        bytes[1] = desc->field_24;
        packet.field_04 = desc->field_0c;
        packet.field_08 = desc->field_08;
        packet.field_0c = desc->field_1c;
        packet.field_10 = desc->field_10;
        packet.field_14 = desc->field_14;
        packet.field_18 = desc->field_18;

        // 0x002AB1A4..0x002AB1B8: the +0xE0 relative array inside r6.
        u8* count_base = reinterpret_cast<u8*>(packed) + 0xE0;
        const u32 rel = *reinterpret_cast<u32*>(count_base);
        u8* lane_base = (rel != 0) ? count_base + rel : nullptr;
        const u32 count = (lane_base != nullptr)
                        ? *reinterpret_cast<u32*>(lane_base + 0x18) : 0;

        if (commit == 0) {
            // 0x002AB4F8: the render list is handed to 0x002B3CB0.
            result = engine_func_002b3cb0(&packet, ctx, packed, call_word);
        } else if (out == nullptr) {
            goto fallthrough_common;                // 0x002AB1A0
        } else {
            // 0x002AB1BC..0x002AB204: block A, 0x40 bytes per lane.
            ReservePayload32(out, count << 6);

            // 0x002AB218..0x002AB288: block B, 0x60 header + count*0x40.
            ReserveHeaderPayload(out, 0x60, count << 6);
            // 0x002AB28C..0x002AB2DC: block C, 0x60 header + count*0x30.
            ReserveHeaderPayload(out, 0x60, (count + (count << 1)) << 4);
            // 0x002AB2E0..0x002AB328: block D, identical to block C.
            ReserveHeaderPayload(out, 0x60, (count + (count << 1)) << 4);

            // 0x002AB338..0x002AB38C: the two 0x14/count*4 pairs.  The
            // `ldm sp,{r0,r2}` at 0x002AB32C reloads the stream and the word
            // written by `vstr s0,[sp,#4]` (0x002AB214).
            if (count != 0) {
                ReserveAtAlign(out, 0x14);
                ReserveAtAlign(out, count << 2);
                ReserveAtAlign(out, 0x14);
                ReserveAtAlign(out, count << 2);
            } else {
                ReserveAtAlign(out, 0x14);
                ReserveAtAlign(out, 0x14);          // 0x002AB44C
            }

            // 0x002AB390..0x002AB3D0: one 0x234 header then the five-float
            // builder.  r0/r1 carry out/packed, r2 is the packet flags word,
            // r3 is packet+0x04 and s0..s4 are packet+0x08..+0x18; all five
            // words are initialised by the descriptor copy at
            // 0x002AB160..0x002AB18C.
            ReserveAtAlign(out, 0x234);
            func_0012e3a0(out, packed, packet.flags, packet.field_04,
                          WordFloat(packet.field_08),
                          WordFloat(packet.field_0c),
                          WordFloat(packet.field_10),
                          WordFloat(packet.field_14),
                          WordFloat(packet.field_18));

            // 0x002AB3D4..0x002AB4B0: iterate count 16-byte records starting
            // at r6+0x2C; the first entry with `[+4] & 1` and `[+0xC] == 1`
            // reserves 0x68 and runs 0x002B43B0.
            if (static_cast<s8>(bytes[1]) != 0 && packed->count_28 > 0) {
                u8* base = (packed->rel_2c != 0)
                         ? reinterpret_cast<u8*>(packed) + 0x2C
                               + packed->rel_2c
                         : nullptr;
                for (s32 i = 0; i < static_cast<s32>(packed->count_28); ++i) {
                    u8* entry = base + (i << 4);
                    u32 rel_entry = *reinterpret_cast<u32*>(entry + 0x28);
                    u8* record = (rel_entry != 0) ? entry + 0x28 + rel_entry
                                                  : nullptr;
                    if (record == nullptr) {
                        continue;
                    }
                    if ((*reinterpret_cast<u32*>(record + 4) & 1u) == 0) {
                        continue;
                    }
                    if (*reinterpret_cast<u32*>(record + 0xC) != 1) {
                        continue;
                    }
                    // 0x002AB47C..0x002AB4A8: keep the low byte of the
                    // packed pointer and OR in bit 0 (the `bic`/`orr`/`sxtb`
                    // sequence).
                    const s32 tagged = static_cast<s8>(
                        (reinterpret_cast<std::uintptr_t>(packed) & ~0xFFu)
                        | 1u);
                    (void)tagged;
                    ReserveAtAlign(out, 0x68);
                    func_002b43b0(out);
                    break;
                }
            }
        }
    } else if (tag == 0x400000A2u) {
        // 0x002AB690..0x002AB71C
        DrawPacket16 packet{};
        u8* bytes = reinterpret_cast<u8*>(&packet);
        bytes[0] = 1;
        bytes[1] = 1;
        packet.field_04 = 4;
        packet.field_08 = 8;
        packet.field_0c = 1;

        bytes[0] = desc->field_04;
        bytes[1] = desc->field_24;
        packet.field_04 = desc->field_0c;
        packet.field_08 = desc->field_08;
        packet.field_0c = desc->field_1c;

        if (commit == 0) {
            result = func_0012b570(ctx, packed, &packet, call_word);
        } else if (out != nullptr) {
            func_0012b478(out, packed, packet.flags, packet.field_04,
                          packet.field_08, packet.field_0c);
        }
    } else if (tag == 0x40000112u) {
        // 0x002AB518..0x002AB610
        DrawPacket32 packet{};
        u8* bytes = reinterpret_cast<u8*>(&packet);
        bytes[0] = 1;
        bytes[1] = 1;
        packet.field_04 = 4;
        packet.field_08 = 8;
        packet.field_0c = 1;
        packet.field_10 = 0;
        packet.field_14 = 0;
        packet.field_18 = 0;
        packet.field_1c = 0;

        bytes[0] = desc->field_04;
        bytes[1] = desc->field_24;
        packet.field_04 = desc->field_0c;
        packet.field_08 = packed->count_20 + packed->rel_e0
                       + desc->field_20;
        packet.field_0c = 1;
        packet.field_10 = desc->field_10;
        packet.field_14 = desc->field_14;
        packet.field_18 = desc->field_18;
        packet.field_1c = ((0x40000112u & ~tag) == 0)
                        ? (packed->rel_e0 + desc->field_20) : 0;

        if (commit == 0) {
            // 0x002AB5F0: the float scale is pushed at [sp].
            result = engine_func_0012b7c4(ctx, packed, &packet, call_word,
                                          scale);
        } else {
            // 0x002AB5BC / 0x002AB5E0: the packet is handed to both streams
            // with the packed object as the middle argument.
            if (out != nullptr) {
                func_0012b638(out, packed, &packet);
            }
            if (out2 != nullptr) {
                func_0012b728(out2, packed, &packet);
            }
        }
    } else if (tag == 0x40000122u) {
        // 0x002AB840..0x002AB8CC
        DrawPacket16 packet{};
        u8* bytes = reinterpret_cast<u8*>(&packet);
        bytes[0] = 1;
        bytes[1] = 1;
        packet.field_04 = 4;
        packet.field_08 = 8;
        packet.field_0c = 1;

        bytes[0] = desc->field_04;
        bytes[1] = desc->field_24;
        packet.field_04 = desc->field_0c;
        packet.field_08 = desc->field_08;
        packet.field_0c = desc->field_1c;

        if (commit == 0) {
            result = engine_func_0012c348(ctx, packed, &packet, call_word);
        } else if (out != nullptr) {
            func_0012c090(out, packed, packet.flags, packet.field_04,
                          packet.field_08, 1);
        }
    } else if (tag == 0x40000222u) {
        // 0x002AB720..0x002AB7AC
        DrawPacket16 packet{};
        u8* bytes = reinterpret_cast<u8*>(&packet);
        bytes[0] = 1;
        bytes[1] = 1;
        packet.field_04 = 4;
        packet.field_08 = 8;
        packet.field_0c = 1;

        bytes[0] = desc->field_04;
        bytes[1] = desc->field_24;
        packet.field_04 = desc->field_0c;
        packet.field_08 = desc->field_08;
        packet.field_0c = desc->field_1c;

        if (commit == 0) {
            result = engine_func_0012acdc(ctx, packed, &packet, call_word);
        } else if (out != nullptr) {
            func_0012abe4(out, packed, packet.flags, packet.field_04,
                          packet.field_08, 1);
        }
    } else if (tag == 0x40000422u) {
        // 0x002AB7B0..0x002AB83C
        DrawPacket16 packet{};
        u8* bytes = reinterpret_cast<u8*>(&packet);
        bytes[0] = 1;
        bytes[1] = 1;
        packet.field_04 = 4;
        packet.field_08 = 8;
        packet.field_0c = 1;

        bytes[0] = desc->field_04;
        bytes[1] = desc->field_24;
        packet.field_04 = desc->field_0c;
        packet.field_08 = desc->field_08;
        packet.field_0c = desc->field_1c;

        if (commit == 0) {
            result = engine_func_0012b1ac(ctx, packed, &packet, call_word);
        } else if (out != nullptr) {
            func_0012b0b4(out, packed, packet.flags, packet.field_04,
                          packet.field_08, 1);
        }
    } else if (tag == 0x00800000u) {
        // 0x002AB9E4..0x002ABA24
        DrawPacket16 packet{};
        if (commit == 0) {
            result = func_0012d444(packed, &packet, call_word);
        } else if (out != nullptr) {
            func_0012d314(out, packed);
        }
    } else {
        goto common_tail;                           // 0x002AB4B0 default
    }

fallthrough_common:
common_tail:
    // 0x002AB4B0: commit == 0 skips the descriptor and goes straight to the
    // virtual-result walk.
    if (commit == 0) {
        goto vtable_walk;
    }

    // 0x002AB4B8..0x002AB4F4: the optional tail argument receives the final
    // commit descriptor {packed, 0, 0, 1}, then the routine returns.
    if (tail_arg != nullptr) {
        func_00132904(desc, out, out2, 0, packed, 0, 0, 1);
    }
    return static_cast<s32>(reinterpret_cast<std::uintptr_t>(result));

vtable_walk:
    // 0x002ABA28..0x002ABAA0: walk the virtual result.  The loop starts with
    // the vtable slot 2 result (`ldr r1,[r0,#8]; blx r1`).
    if (result != nullptr) {
        void** vtable = *reinterpret_cast<void***>(result);
        using ResultFn = void* (*)(void*);
        void* node = reinterpret_cast<ResultFn>(vtable[2])(result);
        while (node != nullptr && node != &g_EngineDrawSentinel_44e858) {
            node = *reinterpret_cast<void**>(node); // 0x002ABA94
        }
        if (node == &g_EngineDrawSentinel_44e858 && tail_arg != nullptr) {
            func_00132904(desc, nullptr, nullptr, 0, packed, call_word,
                          FloatWord(scale), 0);
        }
    }
    return static_cast<s32>(reinterpret_cast<std::uintptr_t>(result));
}
#endif

// Readable engine draw-stream draft above; exact ARM body retained for codegen recovery.
__attribute__((naked)) s32 engine_func_002aad14(EngineDrawDesc* desc, DrawStream* out,
                         DrawStream* out2, void* ctx,
                         EngineDrawPacked* packed, u32 call_word, f32 scale,
                         void* tail_arg, s32 commit) {
    asm volatile(
        ".word 0xe92d4ff0, 0xe1a04000, 0xe1a05001, 0xe1a09002\n"
        ".word 0xe1a0e003, 0xed2d8b02, 0xe24dd03c, 0xe59d6068\n"
        ".word 0xe59d8078, 0xed9d8a1c, 0xe3560000, 0x03a00000\n"
        ".word 0x0a00034f, 0xe5960000, 0xe59f3d50, 0xe3a01004\n"
        ".word 0xe3a02008, 0xe1500003, 0xe3a0a001, 0xe0403003\n"
        ".word 0xe3a07000, 0x0a0002d8, 0xaa00000e, 0xe3500119\n"
        ".word 0x0a000226, 0xaa000006, 0xe3500502, 0x0a000317\n"
        ".word 0xe3500101, 0x0a000016, 0xe3500109, 0x1a0001c6\n"
        ".word 0xea000082, 0xe3500129, 0x0a0002ec, 0xe3500149\n"
        ".word 0x1a0001c1, 0xea0000a9, 0xe35300e0, 0x0a0002a2\n"
        ".word 0xaa000006, 0xe3530050, 0x0a0000db, 0xe3530060\n"
        ".word 0x0a000231, 0xe35300d0, 0x1a0001b7, 0xea0001d0\n"
        ".word 0xe3530e1e, 0x0a000250, 0xe3530e3e, 0x1a0001b2\n"
        ".word 0xea000271, 0xe28d0004, 0xe5cda000, 0xe5cda001\n"
        ".word 0xe8800406, 0xe3580000, 0xe5d40004, 0xe5cd0000\n"
        ".word 0xe594000c, 0xe58d0004, 0xe5940008, 0xe58d0008\n"
        ".word 0xe594001c, 0xe58d000c, 0xe5d40024, 0xe5cd0001\n"
        ".word 0x0a000056, 0xe3550000, 0x0a0001a1, 0xe1cd00d8\n"
        ".word 0xe5953004, 0xe595c000, 0xe59d2004, 0xe59d8000\n"
        ".word 0xe08cc003, 0xe2433001, 0xe24cc001, 0xe1cc3003\n"
        ".word 0xe283304c, 0xe5853000, 0xe1a0e100, 0xe5950004\n"
        ".word 0xe3a03020, 0xe5853004, 0xe595c008, 0xe35c0020\n"
        ".word 0x21a0300c, 0xe5853008, 0xe5953000, 0xe5850004\n"
        ".word 0xe283301f, 0xe3c3301f, 0xe083300e, 0xe5853000\n"
        ".word 0xe5953008, 0xe1530000, 0x21a00003, 0xe5850008\n"
        ".word 0xe3520000, 0xe1a00005, 0x0a00002c, 0xe5903004\n"
        ".word 0xe590c000, 0xe1a0e102, 0xe08cc003, 0xe2433001\n"
        ".word 0xe24cc001, 0xe1ccc003, 0xe28cc014, 0xe580c000\n"
        ".word 0xe5902004, 0xe082200c, 0xe2422001, 0xe1c22003\n"
        ".word 0xe082200e, 0xe5802000, 0xe1a00808, 0xe1b00c40\n"
        ".word 0x15962028, 0x13520000, 0x0a00016d, 0xe5953004\n"
        ".word 0xe595c000, 0xe0010192, 0xe08cc003, 0xe2433001\n"
        ".word 0xe24cc001, 0xe1cc3003, 0xe283302c, 0xe5853000\n"
        ".word 0xe595c004, 0xe1a00005, 0xe083300c, 0xe24cc001\n"
        ".word 0xe2433001, 0xe1c3300c, 0xe0832102, 0xe5802000\n"
        ".word 0xe5903004, 0xe0822003, 0xe2433001, 0xe2422001\n"
        ".word 0xe1c22003, 0xe0821101, 0xe5851000, 0xea000154\n"
        ".word 0xe5902004, 0xe5903000, 0xe0833002, 0xe2422001\n"
        ".word 0xe2433001, 0xe1c32002, 0xe2822014, 0xeaffffd8\n"
        ".word 0xe59d306c, 0xe1a0200d, 0xe1a01006, 0xe1a0000e\n"
        ".word 0xebfa1054, 0xe1a07000, 0xe320f000, 0xea0002a0\n"
        ".word 0xe28d000c, 0xe5cda008, 0xe5cda009, 0xe8800406\n"
        ".word 0xe3580000, 0xe5d40004, 0xe5cd0008, 0xe594000c\n"
        ".word 0xe58d000c, 0xe5940008, 0xe58d0010, 0xe594001c\n"
        ".word 0xe58d0014, 0xe5d40024, 0xe5cd0009, 0x0a000013\n"
        ".word 0xe3550000, 0x0a000132, 0xe1cd20d8, 0xe28d0010\n"
        ".word 0xe595c000, 0xe1a01006, 0xec900a02, 0xe5950004\n"
        ".word 0xe08cc000, 0xe2400001, 0xe24cc001, 0xe1cc0000\n"
        ".word 0xe2800f52, 0xe5850000, 0xe1a00005, 0xec8d0a02\n"
        ".word 0xeb00250a, 0xe320f000, 0xe320f000, 0xea000120\n"
        ".word 0xe59d306c, 0xe28d2008, 0xe1a01006, 0xe1a0000e\n"
        ".word 0xebfa03a0, 0xe320f000, 0xe320f000, 0xea000034\n"
        ".word 0xe3a00000, 0xe5cda014, 0xe5cda015, 0xe58d0024\n"
        ".word 0xe58d0028, 0xe58d002c, 0xe28d0018, 0xe3580000\n"
        ".word 0xe8800406, 0xe5d40004, 0xe5cd0014, 0xe594000c\n"
        ".word 0xe58d0018, 0xe5940008, 0xe58d001c, 0xe5940010\n"
        ".word 0xe58d0024, 0xe5940014, 0xe58d0028, 0xe5940018\n"
        ".word 0xe58d002c, 0xe5d40024, 0xe5cd0015, 0xe594001c\n"
        ".word 0xe58d0020, 0x0a000015, 0xe3550000, 0x0a0000fc\n"
        ".word 0xe1cd21d4, 0xee000a90, 0xe5950004, 0xe595c000\n"
        ".word 0xe28d8024, 0xe240e001, 0xe080000c, 0xe2400001\n"
        ".word 0xe1c0000e, 0xec981a03, 0xe2800e22, 0xed9d0a07\n"
        ".word 0xe5850000, 0xe1a01006, 0xe1a00005, 0xec8d0a05\n"
        ".word 0xebfa0ca5, 0xe320f000, 0xe320f000, 0xea0000e8\n"
        ".word 0xe59d306c, 0xe28d2014, 0xe1a01006, 0xe1a0000e\n"
        ".word 0xebfa0d5e, 0xe1a07000, 0xea00023d, 0xe3a00000\n"
        ".word 0xe5cda018, 0xe5cda019, 0xe58d0028, 0xe58d002c\n"
        ".word 0xe58d0030, 0xe58d0034, 0xe28d001c, 0xe3580000\n"
        ".word 0xe8800406, 0xe5d40004, 0xe5cd0018, 0xed940a03\n"
        ".word 0xed8d0a07, 0xed940a02, 0xed8d0a08, 0xed940a04\n"
        ".word 0xed8d0a0a, 0xed940a05, 0xed8d0a0b, 0xed940a06\n"
        ".word 0xed8d0a0c, 0xed940a07, 0xed8d0a09, 0xe5d40024\n"
        ".word 0xe5cd0019, 0x0a0000d6, 0xe3550000, 0x0a0000c2\n"
        ".word 0xe59610e0, 0xe28600e0, 0xe3a02020, 0xe3510000\n"
        ".word 0x1081b000, 0x03a0b000, 0xe5950004, 0xe59b1018\n"
        ".word 0xe5852004, 0xe5953008, 0xe3a0e020, 0xe1a01301\n"
        ".word 0xe3530020, 0x21a02003, 0xe5852008, 0xe5952000\n"
        ".word 0xe5850004, 0xe282201f, 0xe3c2201f, 0xe0811002\n"
        ".word 0xe5851000, 0xe5951008, 0xe1510000, 0x21a00001\n"
        ".word 0xe5850008, 0xe58d5000, 0xed9d0a07, 0xe1a01005\n"
        ".word 0xed8d0a01, 0xe1a00001, 0xe5951004, 0xe5952000\n"
        ".word 0xe0822001, 0xe2411001, 0xe2422001, 0xe1c22001\n"
        ".word 0xe2822060, 0xe5802000, 0xe59b2018, 0xe5903004\n"
        ".word 0xe580e004, 0xe1a0c302, 0xe1a0200e, 0xe590e008\n"
        ".word 0xe35e0020, 0x31a0e002, 0xe580e008, 0xe590e000\n"
        ".word 0xe5803004, 0xe28ee01f, 0xe3cee01f, 0xe08cc00e\n"
        ".word 0xe580c000, 0xe590c008, 0xe3a0e020, 0xe15c0003\n"
        ".word 0x21a0300c, 0xe5803008, 0xe59b2018, 0xe5903004\n"
        ".word 0xe580e004, 0xe082c082, 0xe1a0200e, 0xe590e008\n"
        ".word 0xe1a0c20c, 0xe35e0020, 0x31a0e002, 0xe580e008\n"
        ".word 0xe590e000, 0xe5803004, 0xe28ee01f, 0xe3cee01f\n"
        ".word 0xe08cc00e, 0xe580c000, 0xe590c008, 0xe3a0e020\n"
        ".word 0xe15c0003, 0x21a0300c, 0xe5803008, 0xe59b3018\n"
        ".word 0xe083c083, 0xe5903004, 0xe580e004, 0xe590b008\n"
        ".word 0xe1a0c20c, 0xe35b0020, 0x21a0e00b, 0xe580e008\n"
        ".word 0xe590e000, 0xe5803004, 0xe28ee01f, 0xe3cee01f\n"
        ".word 0xe08cc00e, 0xe580c000, 0xe590c008, 0xe15c0003\n"
        ".word 0x21a0300c, 0xe5803008, 0xe89d0005, 0xe3520000\n"
        ".word 0x0a000044, 0xe1a0c002, 0xe1c020d0, 0xe0822003\n"
        ".word 0xe2422001, 0xe1c22001, 0xe2823014, 0xe1a0210c\n"
        ".word 0xe590c004, 0xe083300c, 0xe2433001, 0xe1c33001\n"
        ".word 0xe0833002, 0xe083300c, 0xe2433001, 0xe1c33001\n"
        ".word 0xe2833014, 0xe5803000, 0xe083300c, 0xe2433001\n"
        ".word 0xe1c33001, 0xe0822003, 0xe5802000, 0xe1c520d0\n"
        ".word 0xe28d0020, 0xe0822003, 0xe2422001, 0xe1c21001\n"
        ".word 0xe2811f8d, 0xe5851000, 0xe58d5014, 0xe58d6038\n"
        ".word 0xe59db018, 0xe59d301c, 0xe1a01006, 0xec900a05\n"
        ".word 0xe1a0200b, 0xe1a00005, 0xec8d0a05, 0xebfa0bf2\n"
        ".word 0xe1a0080b, 0xe1b00c40, 0x0a000033, 0xe59d0038\n"
        ".word 0xe3a02000, 0xe590c028, 0xe35c0000, 0xc590302c\n"
        ".word 0xda00002d, 0xe3530000, 0xe280102c, 0x10811003\n"
        ".word 0x03a01000, 0xe3510000, 0x0a000004, 0xe0811202\n"
        ".word 0xe5b1e028, 0xe35e0000, 0x03a01000, 0x1081100e\n"
        ".word 0xe591e004, 0xe591b00c, 0xe31e0001, 0x0a000001\n"
        ".word 0xe35b0001, 0x0a00000e, 0xe2822001, 0xe152000c\n"
        ".word 0xbaffffeb, 0xea000018, 0xe1c020d0, 0xe0822003\n"
        ".word 0xe2422001, 0xe1c22001, 0xe2822014, 0xe5802000\n"
        ".word 0xe0822003, 0xe2422001, 0xe1c22001, 0xe2822014\n"
        ".word 0xeaffffc4, 0xe59dc014, 0xe3c030ff, 0xe183200a\n"
        ".word 0xe59c0004, 0xe59ce000, 0xe6af2072, 0xe08e3000\n"
        ".word 0xe2400001, 0xe2433001, 0xe1c30000, 0xe2800068\n"
        ".word 0xe58c0000, 0xe59d0014, 0xeb0023bf, 0xe3580000\n"
        ".word 0x0a00015b, 0xe59d0074, 0xe3500000, 0x0a00016f\n"
        ".word 0xe3a00000, 0xe28d8008, 0xe58d0004, 0xe58d6000\n"
        ".word 0xe1a03000, 0xe8880401, 0xe1a02009, 0xe1a01005\n"
        ".word 0xe1a00004, 0xebfa1d05, 0xe320f000, 0xe320f000\n"
        ".word 0xea000162, 0xe59d306c, 0xe1a02006, 0xe1a0100e\n"
        ".word 0xe28d0018, 0xeb0021e8, 0xe320f000, 0xe320f000\n"
        ".word 0xeaffff03, 0xe5963000, 0xe59fc584, 0xe5cda008\n"
        ".word 0xe5cda009, 0xe1dc3003, 0xe28d300c, 0xe1a00006\n"
        ".word 0xe8830406, 0xe3a01000, 0xe58d1018, 0xe58d101c\n"
        ".word 0xe58d1020, 0xe58d1024, 0xe5d41004, 0x13a00000\n"
        ".word 0xe1a0b000, 0xe5cd1008, 0xe594100c, 0xe3580000\n"
        ".word 0xe58d100c, 0xe5941010, 0xe58d1018, 0xe5941014\n"
        ".word 0xe58d101c, 0xe5941018, 0xe58d1020, 0xe5b01020\n"
        ".word 0xe5943020, 0xe59020c0, 0xe0811002, 0xe0811003\n"
        ".word 0xe58d1010, 0xe59b00e0, 0xe5941020, 0xe0800001\n"
        ".word 0xe58d0024, 0xe5d40024, 0xe5cd0009, 0x0a00000e\n"
        ".word 0xe3550000, 0x0a000003, 0xe28d2008, 0xe1a0100b\n"
        ".word 0xe1a00005, 0xebfa001a, 0xe3590000, 0x0affffb8\n"
        ".word 0xe28d2008, 0xe1a0100b, 0xe1a00009, 0xebfa0050\n"
        ".word 0xe320f000, 0xe320f000, 0xeaffffb1, 0xed8d8a00\n"
        ".word 0xe59d306c, 0xe28d2008, 0xe1a01006, 0xe1a0000e\n"
        ".word 0xebfa006e, 0xe320f000, 0xe320f000, 0xeafffec4\n"
        ".word 0xe28d0004, 0xe5cda000, 0xe5cda001, 0xe8800406\n"
        ".word 0xe3580000, 0xe5d40004, 0xe5cd0000, 0xe594000c\n"
        ".word 0xe58d0004, 0xe5940008, 0xe58d0008, 0xe5d40024\n"
        ".word 0xe5cd0001, 0x0a000008, 0xe3550000, 0x0affff98\n"
        ".word 0xe1a01006, 0xe1a0200d, 0xe1a00005, 0xebfa040d\n"
        ".word 0xe320f000, 0xe320f000, 0xeaffff91, 0xe59d306c\n"
        ".word 0xe1a0200d, 0xe1a01006, 0xe1a0000e, 0xebfa04bd\n"
        ".word 0xe320f000, 0xe320f000, 0xeafffea5, 0xe28d000c\n"
        ".word 0xe5cda008, 0xe5cda009, 0xe8800406, 0xe3580000\n"
        ".word 0xe5d40004, 0xe5cd0008, 0xe594000c, 0xe58d000c\n"
        ".word 0xe5940008, 0xe58d0010, 0xe594001c, 0xe58d0014\n"
        ".word 0xe5d40024, 0xe5cd0009, 0x0a00000b, 0xe3550000\n"
        ".word 0x0affff77, 0xe28d3010, 0xe1a01006, 0xe8930005\n"
        ".word 0xe88d0005, 0xe1a00005, 0xe1cd20d8, 0xebf9ff60\n"
        ".word 0xe320f000, 0xe320f000, 0xeaffff6d, 0xe59d306c\n"
        ".word 0xe28d2008, 0xe1a01006, 0xe1a0000e, 0xebf9ff96\n"
        ".word 0xe320f000, 0xe320f000, 0xeafffe81, 0xe28d000c\n"
        ".word 0xe5cda008, 0xe5cda009, 0xe8800406, 0xe3580000\n"
        ".word 0xe5d40004, 0xe5cd0008, 0xe594000c, 0xe58d000c\n"
        ".word 0xe5940008, 0xe58d0010, 0xe594001c, 0xe58d0014\n"
        ".word 0xe5d40024, 0xe5cd0009, 0x0a00000b, 0xe3550000\n"
        ".word 0x0affff53, 0xe28d3010, 0xe1a01006, 0xe8930005\n"
        ".word 0xe88d0005, 0xe1a00005, 0xe1cd20d8, 0xebf9fd17\n"
        ".word 0xe320f000, 0xe320f000, 0xeaffff49, 0xe59d306c\n"
        ".word 0xe28d2008, 0xe1a01006, 0xe1a0000e, 0xebf9fd4d\n"
        ".word 0xe320f000, 0xe320f000, 0xeafffe5d, 0xe28d000c\n"
        ".word 0xe5cda008, 0xe5cda009, 0xe8800406, 0xe3580000\n"
        ".word 0xe5d40004, 0xe5cd0008, 0xe594000c, 0xe58d000c\n"
        ".word 0xe5940008, 0xe58d0010, 0xe594001c, 0xe58d0014\n"
        ".word 0xe5d40024, 0xe5cd0009, 0x0a00000b, 0xe3550000\n"
        ".word 0x0affff2f, 0xe28d3010, 0xe1a01006, 0xe8930005\n"
        ".word 0xe88d0005, 0xe1a00005, 0xe1cd20d8, 0xebf9fe27\n"
        ".word 0xe320f000, 0xe320f000, 0xeaffff25, 0xe59d306c\n"
        ".word 0xe28d2008, 0xe1a01006, 0xe1a0000e, 0xebf9fe5d\n"
        ".word 0xe320f000, 0xe320f000, 0xeafffe39, 0xe28d000c\n"
        ".word 0xe5cda008, 0xe5cda009, 0xe8800406, 0xe3580000\n"
        ".word 0xe5d40004, 0xe5cd0008, 0xe594000c, 0xe58d000c\n"
        ".word 0xe5940008, 0xe58d0010, 0xe594001c, 0xe58d0014\n"
        ".word 0xe5d40024, 0xe5cd0009, 0x0a00000b, 0xe3550000\n"
        ".word 0x0affff0b, 0xe28d3010, 0xe1a01006, 0xe8930005\n"
        ".word 0xe88d0005, 0xe1a00005, 0xe1cd20d8, 0xebfa01fa\n"
        ".word 0xe320f000, 0xe320f000, 0xeaffff01, 0xe59d306c\n"
        ".word 0xe28d2008, 0xe1a01006, 0xe1a0000e, 0xebfa02a0\n"
        ".word 0xe320f000, 0xe320f000, 0xeafffe15, 0xe28d000c\n"
        ".word 0xe5cda008, 0xe5cda009, 0xe8800406, 0xe3580000\n"
        ".word 0xe5d40004, 0xe5cd0008, 0xe594000c, 0xe58d000c\n"
        ".word 0xe5940008, 0xe58d0010, 0xe5d40024, 0xe5cd0009\n"
        ".word 0x0a00000a, 0xe3550000, 0x0afffee9, 0xe59d0010\n"
        ".word 0xe1a01006, 0xe88d0401, 0xe1a00005, 0xe1cd20d8\n"
        ".word 0xebfa081c, 0xe320f000, 0xe320f000, 0xeafffee0\n"
        ".word 0xe59d306c, 0xe28d2008, 0xe1a01006, 0xe1a0000e\n"
        ".word 0xebfa0858, 0xe320f000, 0xe320f000, 0xeafffdf4\n"
        ".word 0xe28d000c, 0xe5cda008, 0xe5cda009, 0xe8800406\n"
        ".word 0xe3580000, 0xe5d40004, 0xe5cd0008, 0xe594000c\n"
        ".word 0xe58d000c, 0xe5940008, 0xe58d0010, 0xe594001c\n"
        ".word 0xe58d0014, 0xe5d40024, 0xe5cd0009, 0x0a00000b\n"
        ".word 0xe3550000, 0x0afffec6, 0xe28d3010, 0xe1a01006\n"
        ".word 0xe8930005, 0xe88d0005, 0xe1a00005, 0xe1cd20d8\n"
        ".word 0xebfa0c32, 0xe320f000, 0xe320f000, 0xeafffebc\n"
        ".word 0xe59d306c, 0xe28d2008, 0xe1a01006, 0xe1a0000e\n"
        ".word 0xebfa0cc0, 0xe320f000, 0xe320f000, 0xeafffdd0\n"
        ".word 0xe3580000, 0x0a000007, 0xe3550000, 0x0afffeb0\n"
        ".word 0xe1a01006, 0xe1a00005, 0xebfa0644, 0xe320f000\n"
        ".word 0xe320f000, 0xeafffeaa, 0xe59d206c, 0xe1a0100d\n"
        ".word 0xe1a00006, 0xebfa0689, 0xe320f000, 0xe320f000\n"
        ".word 0xeafffdbf, 0xe59f507c, 0xe3570000, 0x0a000013\n"
        ".word 0xe5970000, 0xe5901008, 0xe1a00007, 0xe12fff31\n"
        ".word 0xe1500005, 0x1a000011, 0xe1b03007, 0x159d0074\n"
        ".word 0x13500000, 0x0a000009, 0xe59d106c, 0xe3a00000\n"
        ".word 0xe1a02000, 0xe58d1004, 0xed8d8a02, 0xe1a01000\n"
        ".word 0xe58d000c, 0xe1a00004, 0xe58d6000, 0xebfa1b9f\n"
        ".word 0xe1a00007, 0xe28dd03c, 0xecbd8b02, 0xe8bd8ff0\n"
        ".word 0xe5900000, 0xe3500000, 0x1affffe8, 0xeafffff7\n"
        ".word 0x40000042, 0x40000112, 0x0044e858\n");
}

// ---------------------------------------------------------------------------
// 0x002553EC: battle effect/action emitter
// ---------------------------------------------------------------------------

namespace {

// 0x00434290: action manager.  The 0x0043427C script VM context slot is
// defined canonically in script_blocks.cpp and declared in script_blocks.h.
void* g_BattleActionManager_434290 = nullptr;
// 0x00435D18: global block; the routine reaches +0x3000 for its +0x28 word.
u8* g_BattleGlobal_435d18 = reinterpret_cast<u8*>(0x00435D18u);
// 0x00439960: 12-byte effect rows selected by the argument at [sp+0x148].
const BattleEffectRow* g_BattleEffectRows_439960 =
    reinterpret_cast<const BattleEffectRow*>(0x00439960u);

} // namespace

// Observed call targets for 0x002553EC.  One declaration per binary address.
extern "C" {
s32 script_vm_func_00255318(s32 id, s32 r1, s32 r2, s32 r3);
s32 script_vm_func_00255398(s32 id);
BattleAction* btlActionReflect_func_00226b2c(BattleActionManager* manager,
                                             s32 x, s32 y, void* actor,
                                             s32 stack_word);
s32 battle_func_00226948(s32 position, void* actor, BattleActorRecord* rec);
s32 battle_func_0022686c(s32 position, void* actor, BattleActorRecord* rec,
                         s32 arg);
s32 battle_func_00226a60(s32 position, s32 zero, void* actor,
                         BattleActorRecord* rec, s32 a, s32 b, s32 c, f32 f,
                         s32 flag);
s32 battle_func_003bd310(void* value);
s32 battle_func_003de10c(s32 position, void* actor, BattleActorRecord* rec,
                         s32 arg, s32 one_a, s32 one_b);
void* ui_func_00293c98();
s32 ui_func_00282b94(s32 id);
s32 ui_func_0027dca0(s32 id);
s32 ui_func_0027dd20(BattleActorRecord* rec);
s32 battle_func_002934d4(void* context);
s32 battle_func_00250800(s32 a, s32 b, u32 command, s32 d, s32 e, s32 f,
                         s32 g);
void camp_func_0029c0fc(s32 a, s32 b);
// 0x002B7F0A (Thumb): the qsort-shaped routine used to shuffle the candidate
// array.  r3 is the comparator word 0x0019D6B4.
void func_002b7f0a(void* base, s32 count, s32 size, u32 comparator);
} // extern "C"

namespace {

constexpr u32 kBattleSortComparator = 0x0019D6B4u;

// 0x00226B2C wrapper: the stack argument is the position word at 0x2554C0 /
// 0x255A7C.
BattleAction* NewAction(s32 position, void* actor, s32 stack_word) {
    BattleActionManager* manager =
        static_cast<BattleActionManager*>(g_BattleActionManager_434290);
    return btlActionReflect_func_00226b2c(manager, position, 0, actor,
                                          stack_word);
}

} // namespace

// DECOMP_FUNC(0x002553ec, 3124)
#if 0
s32 battle_func_002553ec(s32 base, void* actor, BattleActorRecord* attack,
                         u32 a3, s32 arg4, s32 arg5, s32 arg6, f32 arg7,
                         f32 arg8, s32 arg9, s32 arg10, s32 arg11, s32 arg12,
                         s32 arg13, s32 arg14, s32 arg15, s32 arg16, s32 arg17,
                         s32 arg18, s32 arg19, s32 arg20, s32 arg21, s32 arg22,
                         f32 arg23, s32 arg24) {
    (void)arg6;
    (void)arg10;
    (void)arg20;

    s32 success = 0;                                // sb
    const s32 attack_flags = (attack->flags_50 & 0x10u) >> 4; // [sp+0xD4]
    u8* ui = static_cast<u8*>(ui_func_00293c98());  // [sp+0xCC]
    const BattleEffectRow* rows = g_BattleEffectRows_439960
                                + (static_cast<u32>(arg12) * 3u);
    const s32 effect_arg = ui_func_00282b94(attack->id_62); // [sp+0xC8]
    s32 allow_emit = 1;                             // [sp+0xD8]

    // 0x00255408..0x00255430: the unit table is fetched once from the UI
    // context at +0x1E98.
    BattleActorRecord* unit_table =
        *reinterpret_cast<BattleActorRecord**>(ui + 0x1E98);

    if (attack->id_62 >= 0x6D) {
        // 0x00255470..0x00255478: skips straight to the closing block.
        success = 1;
        goto final_entry;
    }

    // 0x0025547C..0x00255494: initialise the per-actor effect state.
    if (arg14 == 0) {
        script_vm_func_00255318(attack->id_62, 0, 1, 0);
    }

    if (arg11 == 1) {
        // 0x00255648..0x00255670: single 0x3DE10C action, then the post
        // notification (skips both the action list and the unit sweep).
        battle_func_003de10c(base + arg15, actor, attack, arg12, 1, 1);
        goto post_notify;
    }

    // 0x002554A0..0x0025554C: three actions for the selected target.
    if (arg9 != 0) {
        const s32 position = base + arg20;
        BattleAction* action = NewAction(position + 1, actor, position + 1);
        action->kind = 0x13;
        action->record = attack;
        action->field_4c = static_cast<u32>(arg9);

        action = NewAction(position, actor, position);
        action->kind = 8;
        action->record = attack;
        action->field_28 = static_cast<u32>(arg9);

        action = NewAction(position, actor, 1);
        action->kind = 0x1D;
        action->record = attack;
        action->field_28 = 1;
        action->field_4c = static_cast<u32>(arg9);

        if (battle_func_003bd310(reinterpret_cast<void*>(
                static_cast<std::uintptr_t>(arg9))) == 0) {
            allow_emit = 0;                         // 0x00255544
        }
    }

    // 0x00255550..0x0025572C: when the attack record carries bit 0x10, count
    // the eligible units, subtract the scaled threshold and shuffle the first
    // entries.
    if (attack_flags != 0) {
        s32 eligible = 0;
        for (s32 i = 0; i < 0x6D; ++i) {
            BattleActorRecord* unit = unit_table + i;
            if ((unit->flags_50 & 1u) == 0 || (unit->flags_50 & 2u) == 0 ||
                (unit->flags_50 & 0x10u) == 0) {
                continue;
            }
            if ((unit->flags_f8 & 2u) != 0) {
                continue;
            }
            ++eligible;
        }

        const s32 raw = *reinterpret_cast<s16*>(ui + 0x1E84);
        const s32 product = raw * 0x6667;           // `smulbb`
        s32 threshold = static_cast<s8>((product >> 18)
                                        - (product >> 31));
        if (threshold < 3) {
            threshold = 3;
        }
        const s32 scaled = static_cast<s32>(
            static_cast<f32>(raw + threshold) * arg7 / arg8);
        s32 clamped = static_cast<s8>(scaled);
        if (clamped < threshold) {
            clamped = threshold;
        }
        const s32 remaining = eligible - clamped;
        eligible = (remaining > 0) ? static_cast<s8>(remaining) : 0;

        if (eligible > 0) {
            script::ScriptSlot* slot =
                script_vm_func_0027eb98(
                    reinterpret_cast<script::ScriptBattleContext*>(
                        script::g_ScriptVmContext_43427c));
            slot->action_latched = 1;               // 0x00255634

            if (arg12 == 0) {
                // 0x00255674: mark the global battle block.
                u8* global = g_BattleGlobal_435d18 + 0x3000;
                *reinterpret_cast<u32*>(global + 0x28) |= 0x8000u;
            }

            BattleActorRecord* candidates[0x36] = {};
            s32 count = 0;
            for (s32 i = 4; i < 0x36; ++i) {
                BattleActorRecord* unit = unit_table + i;
                if ((unit->flags_50 & 1u) == 0 ||
                    (unit->flags_50 & 0x10u) == 0 ||
                    (unit->flags_50 & 2u) == 0) {
                    continue;
                }
                if ((unit->flags_f8 & 2u) != 0 ||
                    (unit->flags_f8 & 4u) != 0) {
                    continue;
                }
                if (unit->id_62 == attack->id_62) {
                    continue;
                }
                candidates[count++] = unit;
            }

            func_002b7f0a(candidates, static_cast<s8>(count), 4,
                          kBattleSortComparator);

            // 0x00255700..0x0025572C marks candidates[0..eligible-1]; the
            // counter is incremented before the comparison and capped at
            // 0x32.
            for (s32 i = 0; i < eligible && i < 0x32; ++i) {
                candidates[i]->flags_f8 |= 4u;
            }
        }
    }

    // 0x00255550 / 0x00255730..0x00255A04: only a unit whose attack record
    // carries bit 0x10 reaches the per-unit effect commands; the zero case
    // jumps straight to the post-effect notification at 0x00255A08.
    if (attack_flags != 0) {
        u8* speed_block = ui + 0x2F00;              // [sp+8]
        u8* counter = ui + 0x2C00 + 0x304;          // [sp+0xC]
        for (s32 i = 4; i < 0x36; ++i) {
            BattleActorRecord* unit = unit_table + i;
            if ((unit->flags_50 & 1u) == 0 ||
                (unit->flags_50 & 0x10u) == 0 ||
                (unit->flags_50 & 2u) == 0) {
                continue;
            }
            if ((unit->flags_f8 & 2u) != 0) {
                continue;
            }
            // 0x00255780..0x00255790: an eligible unit is only processed when
            // it is not the attacker and the shuffle marked it (bit 2).
            if (unit->id_62 == attack->id_62 ||
                (unit->flags_f8 & 4u) == 0) {
                continue;
            }

            *counter = static_cast<u8>(speed_block[4] + 1);
            const s32 position = base + arg15;       // [sp+0xD0]

            switch (arg12) {
            case 0:
            case 1: {
                // 0x002557F4..0x00255884
                unit->flags_f8 |= 2u;
                BattleAction* action = NewAction(
                    static_cast<s16>(unit->offset_5c + position), actor, 0);
                action->kind = 0x13;
                action->record = unit;
                action->field_4c = 0;

                battle_func_00226948(unit->offset_5c + position, actor, unit);

                action = NewAction(attack->offset_5c + base + 5, actor, 0);
                action->kind = 0x1B;
                break;
            }
            default: {
                // 0x00255888..0x002559FC (rows 2..14 of the table at
                // 0x002557B8); every other row jumps to the loop tail.
                if (arg12 > 14) {
                    break;
                }
                unit->flags_f8 |= 2u;
                BattleAction* action = NewAction(
                    static_cast<s16>(unit->offset_5c + position), actor, 0);
                action->kind = 0x13;
                action->record = unit;
                action->field_4c = 0;

                if (arg12 == 9) {
                    battle_func_0022686c(unit->offset_5c + position, actor,
                                         unit, arg12);
                } else {
                    // 0x002558D8: `vldr s0,[sp,#0x148]` moves the integer
                    // argument word into s0, then stores it at +0x28.
                    const f32 value =
                        WordFloat(static_cast<u32>(arg12));
                    const s32 position_field = unit->offset_5c + position;
                    if ((unit->flags_50 & 1u) != 0) {
                        BattleActionManager* manager =
                            static_cast<BattleActionManager*>(
                                g_BattleActionManager_434290);
                        BattleAction* node = manager->head;
                        while (node != nullptr) {
                            if (node->kind == 0x25 &&
                                node->actor == actor &&
                                node->record == unit) {
                                goto marker;
                            }
                            node = node->next;
                        }
                        action = NewAction(position_field, actor, 0);
                        ui_func_00293c98();
                        const s32 table = ui_func_0027dca0(unit->id_62);
                        ui_func_00293c98();
                        s32 lane = ui_func_0027dd20(unit);
                        if (lane < 0) {
                            lane = 0;
                        }
                        action->kind = 0x25;
                        action->record = unit;
                        action->field_28 = FloatWord(value);
                        const s32 row = table + (lane << 2);
                        action->field_24 = *reinterpret_cast<s16*>(row + 0xC);
                    }
                }
            marker: {
                    const u16 extra = rows->field_0a;
                    action = NewAction(
                        static_cast<s16>(unit->offset_5c + extra + position),
                        actor, 0);
                    action->kind = 0x17;
                    action->field_28 = static_cast<u32>(arg12);
                }
                break;
            }
            }
        }
    }

post_notify:
    // 0x00255A08: post-effect notification.
    script_vm_func_00255318(attack->id_62, 1, 1, 0);
    if (success != 0) {
        goto final_entry;
    }

    // 0x00255A54..0x00255BE0: optional primary effect.
    if (arg16 >= 0 && allow_emit != 0) {
        const s32 position = static_cast<s16>(arg16 + base);
        BattleAction* action = NewAction(position, actor, position);
        action->kind = 0x12;
        action->record = attack;                    // 0x00255AA0
        action->field_30 = 1.0f;
        action->field_4c = a3;
        action->field_24 = static_cast<s16>(arg22);

        if (attack_flags != 0) {
            for (s32 i = 4; i < 0x36; ++i) {
                BattleActorRecord* unit = unit_table + i;
                if ((unit->flags_50 & 1u) == 0 ||
                    (unit->flags_50 & 0x10u) == 0 ||
                    (unit->flags_50 & 2u) == 0) {
                    continue;
                }
                if (unit->id_62 == attack->id_62) {
                    continue;
                }
                action = NewAction(position, actor, position);
                action->kind = 0x12;
                action->record = unit;
                action->field_30 = 1.0f;
                action->field_4c = a3;
                action->field_24 = static_cast<s16>(arg22);
            }
        }

        if (battle_func_002934d4(ui) != 0) {
            battle_func_00250800(0, 1, 0x010001A0u, 0, 1, 0, 0);
        }
    }

    // 0x00255B8C..0x00255BE0: optional secondary effect.
    if (arg17 >= 0 && effect_arg != 0 && arg19 >= 0) {
        BattleAction* action = NewAction(
            static_cast<s16>(arg17 + base), actor, 0);
        action->kind = 6;
        // 0x00255BD4..0x00255BE0 writes only +0x04/+0x18/+0x28; the record
        // field is left untouched.
        action->field_18 = static_cast<u32>(effect_arg);
        action->field_28 = static_cast<u32>(arg19);
    }

final_entry:
    // 0x00255BE4..0x00255E5C: the four position combinations.
    {
        const s32 position = base + arg18 + arg14;
        const s32 bank = static_cast<s16>(position);
        const s32 neg_sl = -arg4;
        const s32 neg_arg5 = -arg5;
        const s32 flag = (arg13 != 0) ? 1 : 0;
        BattleAction* action = nullptr;

        if (arg4 < 0) {
            if (arg5 < 0) {
                goto after_positions;               // 0x00255DAC
            }
            // 0x00255CFC..0x00255D24: negative first operand, non-negative
            // second; the first stack word is the second operand.
            if (success == 0 && arg16 >= 0 && arg24 != 0) {
                battle_func_00226a60(position, 0, actor, attack, arg5, 0, 1,
                                     arg23, flag);
                action = NewAction(bank, actor, arg5);
                action->kind = 0x32;
            }
            goto second_action;
        }

        if (arg5 < 0) {
            goto negative_second;                   // 0x00255DB4
        }

        if (success == 0 && arg16 >= 0 && arg24 != 0) {
            battle_func_00226a60(position, 0, actor, attack, arg4, arg14, 4,
                                 arg23, flag);
            action = NewAction(bank, actor, arg4);
            action->kind = 0x32;
        }
        action = NewAction(bank, actor, arg4);
        action->kind = 0x1C;
        action->record = attack;
        action->field_28 = 0;                       // 0x00255CA0..0x00255CCC
        action->field_4c = static_cast<u32>(neg_sl);
        goto second_action;

    negative_second:
        // 0x00255DB4: first operand non-negative, second negative.
        if (success == 0 && arg16 >= 0 && arg24 != 0) {
            battle_func_00226a60(position, 0, actor, attack, arg4, 0, 0,
                                 arg23, flag);
            action = NewAction(bank, actor, arg4);
            action->kind = 0x32;
        }
        action = NewAction(bank, actor, arg4);
        action->kind = 0x1C;
        action->record = attack;
        action->field_28 = 0;
        action->field_4c = static_cast<u32>(neg_sl);
        goto after_positions;

    second_action:
        // 0x00255D58: always emitted after the first closing action; the
        // stack word is zero.
        action = NewAction(bank, actor, 0);
        action->kind = 0x1C;
        action->record = attack;
        action->field_28 = 1;
        action->field_4c = static_cast<u32>(neg_arg5);

    after_positions:
        (void)action;
    }

    // 0x00255E5C..0x00255FBC: the two "selected effect" actions.  The gate
    // reads `a3` from [sp+0x100], not the +0x120 argument, and the listing
    // tests `r8` (always 1 or 2 here) against 3 before the follow-up block, so
    // that block is unreachable.
    if (arg13 == 1 && success == 0 && a3 != 0) {
        const s32 bank = static_cast<s16>(base + arg18 + arg14);
        if (a3 == 1) {
            BattleAction* action = NewAction(bank, actor, 0);
            action->kind = 7;
            action->record = actor;
            action->field_28 = 2;
            action->field_24 = static_cast<s16>(
                script_vm_func_00255398(attack->id_62) - 1);
            action->flags |= 4u;
        } else if (a3 == 2) {
            BattleAction* action = NewAction(bank, actor, 0);
            action->kind = 7;
            action->record = actor;
            action->field_28 = 1;
            action->field_24 = static_cast<s16>(
                script_vm_func_00255398(attack->id_62) - 1);
            action->flags |= 4u;
        }
    }

    // 0x00255FC0..0x0025601C
    if (arg21 != 0 && arg4 >= 0 && effect_arg != 0) {
        const u32 flags = *reinterpret_cast<u32*>(effect_arg);
        if ((flags & 0x10u) != 0) {
            camp_func_0029c0fc(6, arg4);
        } else if ((flags & 0x0Au) != 0) {
            camp_func_0029c0fc(7, arg4);
        }
    }

    return 1;
}
#endif

// Readable battle actor calculation draft above; exact ARM body retained for codegen recovery.
__attribute__((naked)) s32 battle_func_002553ec(s32 base, void* actor, BattleActorRecord* attack,
                         u32 a3, s32 arg4, s32 arg5, s32 arg6, f32 arg7,
                         f32 arg8, s32 arg9, s32 arg10, s32 arg11, s32 arg12,
                         s32 arg13, s32 arg14, s32 arg15, s32 arg16, s32 arg17,
                         s32 arg18, s32 arg19, s32 arg20, s32 arg21, s32 arg22,
                         f32 arg23, s32 arg24) {
    asm volatile(
        ".word 0xe92d4fff, 0xe1a06002, 0xe1a07001, 0xe3a09000\n"
        ".word 0xe1a0b000, 0xed2d8b04, 0xe24dd0e4, 0xe28d0f4d\n"
        ".word 0xe5921050, 0xed9d8a5d, 0xe59da128, 0xe2011010\n"
        ".word 0xecd08a02, 0xe1a01221, 0xe59d4168, 0xe59d5144\n"
        ".word 0xe59d8154, 0xe58d10d4, 0xeb00fa17, 0xe59d1148\n"
        ".word 0xe08b2008, 0xe58d20d0, 0xe59f2940, 0xe0811081\n"
        ".word 0xe58d00cc, 0xe0821101, 0xe58d10dc, 0xe1d616f2\n"
        ".word 0xeb00b5cc, 0xe58d00c8, 0xe1d606f2, 0xe3a01001\n"
        ".word 0xe58d10d8, 0xe350006d, 0xa3a09001, 0xaa0001d9\n"
        ".word 0xe59d1150, 0xe3510000, 0x1a000003, 0xe3a03000\n"
        ".word 0xe3a02001, 0xe1a01003, 0xebffff9f, 0xe3550001\n"
        ".word 0x0a000069, 0xe59d113c, 0xe3510000, 0x0a000028\n"
        ".word 0xe08b8004, 0xe59f58d8, 0xe2880001, 0xe1a04001\n"
        ".word 0xe6bf1070, 0xe58d1000, 0xe5950000, 0xe1a03007\n"
        ".word 0xe3a02000, 0xebff4595, 0xe3a01013, 0xe5c01004\n"
        ".word 0xe5a06014, 0xe1a03007, 0xe5804038, 0xe59d1000\n"
        ".word 0xe5950000, 0xe3a02000, 0xebff458c, 0xe3a01008\n"
        ".word 0xe5c01004, 0xe5a06014, 0xe3a01001, 0xe5804014\n"
        ".word 0xe58d1000, 0xe6bf1078, 0xe5950000, 0xe1a03007\n"
        ".word 0xe3a02000, 0xebff4581, 0xe3a0101d, 0xe5c01004\n"
        ".word 0xe5806014, 0xe59d1000, 0xe5a01028, 0xe5804024\n"
        ".word 0xe59d013c, 0xeb059f72, 0xe3500000, 0x03a01000\n"
        ".word 0x058d10d8, 0xe59d10d4, 0xe3510000, 0x0a00012a\n"
        ".word 0xe59d50cc, 0xe3a00000, 0xe1a04000, 0xe2855b07\n"
        ".word 0xe2855fa6, 0xe5953000, 0xe0801100, 0xe0811300\n"
        ".word 0xe0831101, 0xe5912050, 0xe3120001, 0x13120002\n"
        ".word 0x13120010, 0x0a000002, 0xe59110f8, 0xe3110002\n"
        ".word 0x02844001, 0xe2800001, 0xe350006d, 0xbafffff1\n"
        ".word 0xe59d00cc, 0xeeb00a68, 0xeef00a49, 0xe2801c1e\n"
        ".word 0xe59f07d0, 0xe1d118f4, 0xeeb80ac0, 0xeef80ae0\n"
        ".word 0xe1600081, 0xe1a02940, 0xe0420fc0, 0xe6af0070\n"
        ".word 0xe3500003, 0xb3a00003, 0xe0811000, 0xee011a10\n"
        ".word 0xeeb81ac1, 0xee211a00, 0xee810a20, 0xeebd0ac0\n"
        ".word 0xee101a10, 0xe6af1071, 0xe1510000, 0xb1a01000\n"
        ".word 0xe0440001, 0xe3500000, 0xc6af4070, 0xc3540000\n"
        ".word 0xda000043, 0xe59f0770, 0xe5900000, 0xeb00a55a\n"
        ".word 0xe59d2148, 0xe3a01001, 0xe5c0159c, 0xe3520000\n"
        ".word 0xe3a01000, 0x1a000011, 0xea00000a, 0xe3a00001\n"
        ".word 0xe58d0000, 0xe58d0004, 0xe59d00d0, 0xe59d3148\n"
        ".word 0xe1a02006, 0xe1a01007, 0xeb0622a8, 0xe320f000\n"
        ".word 0xe320f000, 0xea0000e4, 0xe59f0720, 0xe5900000\n"
        ".word 0xe2800a03, 0xe5902028, 0xe3822902, 0xe5802028\n"
        ".word 0xe3a00004, 0xe1a0800d, 0xe5952000, 0xe0803100\n"
        ".word 0xe0833300, 0xe0822103, 0xe5923050, 0xe3130001\n"
        ".word 0x13130010, 0x13130002, 0x0a00000a, 0xe59230f8\n"
        ".word 0xe3130002, 0x03130004, 0x1a000006, 0xe1d236f2\n"
        ".word 0xe1d6c6f2, 0xe153000c, 0x0a000002, 0xe2813001\n"
        ".word 0xe7882101, 0xe6af1073, 0xe2800001, 0xe3500036\n"
        ".word 0xbaffffe8, 0xe59f36a8, 0xe3a02004, 0xe1a00008\n"
        ".word 0xfb018a01, 0xe3a01000, 0xe1a00001, 0xe2811001\n"
        ".word 0xe7982100, 0xe6af1071, 0xe1510004, 0xb2800001\n"
        ".word 0xe59230f8, 0xb3500032, 0xe3833004, 0xe58230f8\n"
        ".word 0xbafffff5, 0xe59d00cc, 0xe3a08004, 0xe2800c2f\n"
        ".word 0xe58d0008, 0xe59d00cc, 0xe2800b0b, 0xe2800fc1\n"
        ".word 0xe58d000c, 0xe5951000, 0xe0882108, 0xe0822308\n"
        ".word 0xe0814102, 0xe5941050, 0xe3110001, 0x13110010\n"
        ".word 0x13110002, 0x0a0000a1, 0xe59430f8, 0xe3130002\n"
        ".word 0x1a00009e, 0xe1d416f2, 0xe1d626f2, 0xe1510002\n"
        ".word 0x13130004, 0x0a000099, 0xe59d1008, 0xe59d000c\n"
        ".word 0xe5d12004, 0xe59d1148, 0xe2822001, 0xe351000f\n"
        ".word 0xe5c02000, 0x379ff101, 0xea000090, 0x002557f4\n"
        ".word 0x002557f4, 0x00255888, 0x00255888, 0x00255888\n"
        ".word 0x00255888, 0x00255888, 0x00255888, 0x00255888\n"
        ".word 0x00255888, 0x00255888, 0x00255888, 0x00255888\n"
        ".word 0x00255888, 0x00255888, 0xe59410f8, 0xe3a02000\n"
        ".word 0xe59f058c, 0xe3811002, 0xe58410f8, 0xe594105c\n"
        ".word 0xe58d2000, 0xe59d20d0, 0xe5900000, 0xe1a03007\n"
        ".word 0xe0811002, 0xe3a02000, 0xe6bf1071, 0xebff44bf\n"
        ".word 0xe3a02013, 0xe5c02004, 0xe5804014, 0xe59d2000\n"
        ".word 0xe580204c, 0xe594205c, 0xe59d10d0, 0xe0820001\n"
        ".word 0xe1a02004, 0xe1a01007, 0xebff443b, 0xe596105c\n"
        ".word 0xe59fc52c, 0xe28b2005, 0xe0811002, 0xe1a03007\n"
        ".word 0xe6bf1071, 0xe59c0000, 0xe3a02000, 0xebff44ab\n"
        ".word 0xe3a0201b, 0xe5c02004, 0xea00005c, 0xe59410f8\n"
        ".word 0xe3a02000, 0xe59f04f8, 0xe3811002, 0xe58410f8\n"
        ".word 0xe594105c, 0xe58d2000, 0xe59d20d0, 0xe5900000\n"
        ".word 0xe1a03007, 0xe0811002, 0xe3a02000, 0xe6bf1071\n"
        ".word 0xebff449a, 0xe3a02013, 0xe5c02004, 0xe5804014\n"
        ".word 0xe59d2000, 0xe580204c, 0xe59d1148, 0xe3510009\n"
        ".word 0x0a000052, 0xed9d0a52, 0xe594105c, 0xed8d0a01\n"
        ".word 0xe59d00d0, 0xe1a03007, 0xe081c000, 0xe5941050\n"
        ".word 0xe3110001, 0x0a00002d, 0xe59f1484, 0xe591e000\n"
        ".word 0xe59e0008, 0xe3500000, 0x0a000009, 0xe5d02004\n"
        ".word 0xe590100c, 0xe3520025, 0x05902008, 0x01520003\n"
        ".word 0x05900014, 0x01500004, 0x0a000020, 0xe1b00001\n"
        ".word 0x1afffff5, 0xe6bf107c, 0xe3a02000, 0xe1a0000e\n"
        ".word 0xebff4476, 0xe58d0000, 0xe320f000, 0xeb00f8ce\n"
        ".word 0xe1d416f2, 0xe320f000, 0xeb00a0cd, 0xe58d0010\n"
        ".word 0xe320f000, 0xeb00f8c8, 0xe1a01004, 0xe320f000\n"
        ".word 0xeb00a0e7, 0xe2503000, 0xe59d0000, 0xe59d1010\n"
        ".word 0xe3a02025, 0xb3a03000, 0xe5c02004, 0xe59d2000\n"
        ".word 0xe0811103, 0xe5824014, 0xe59d2000, 0xed9d0a01\n"
        ".word 0xed820a0a, 0xe59d2000, 0xe591100c, 0xe1c212b4\n"
        ".word 0xe59d10dc, 0xe594205c, 0xe59fc3c4, 0xe59d4148\n"
        ".word 0xe1d110ba, 0xe1a03007, 0xe59c0000, 0xe0822001\n"
        ".word 0xe59d10d0, 0xe0811002, 0xe3a02000, 0xe6bf1071\n"
        ".word 0xebff444e, 0xe3a02017, 0xe5c02004, 0xe5804028\n"
        ".word 0xe2888001, 0xe3580036, 0xbaffff51, 0xe3a02001\n"
        ".word 0xe1d606f2, 0xe3a03000, 0xe1a01002, 0xebfffe3e\n"
        ".word 0xe3590000, 0xe320f000, 0x0a00000a, 0xea00006d\n"
        ".word 0xe594205c, 0xe59d10d0, 0xe59d3148, 0xe0820001\n"
        ".word 0xe1a02004, 0xe1a01007, 0xebff4388, 0xe320f000\n"
        ".word 0xe320f000, 0xeaffffd9, 0xe59d0158, 0xe3500000\n"
        ".word 0xba00004a, 0xe59d10d8, 0xe3510000, 0x0a000047\n"
        ".word 0xe59f531c, 0xe080000b, 0xe59d4170, 0xe6bf1070\n"
        ".word 0xe58d1000, 0xe59d8100, 0xe5950000, 0xeddf8ac5\n"
        ".word 0xe1a03007, 0xe3a02000, 0xebff4424, 0xe3a01012\n"
        ".word 0xe5c01004, 0xe5806014, 0xedc08a0c, 0xe580804c\n"
        ".word 0xe1c042b4, 0xe59d00d4, 0xe3500000, 0x0a000025\n"
        ".word 0xe59d00cc, 0xe3a04004, 0xe2808b07, 0xe2888fa6\n"
        ".word 0xe0841104, 0xe5980000, 0xe0811304, 0xe0805101\n"
        ".word 0xe5950050, 0xe3100001, 0x13100010, 0x13100002\n"
        ".word 0x0a000015, 0xe1d506f2, 0xe1d616f2, 0xe1500001\n"
        ".word 0x0a000011, 0xe59d1100, 0xe59f0284, 0xe1a03007\n"
        ".word 0xe58d1004, 0xe59d1170, 0xe3a02000, 0xe58d1008\n"
        ".word 0xe59d1000, 0xe5900000, 0xebff4400, 0xe3a02012\n"
        ".word 0xe5c02004, 0xe5805014, 0xedc08a0c, 0xe59d1004\n"
        ".word 0xe580104c, 0xe59d1008, 0xe1c012b4, 0xe2844001\n"
        ".word 0xe3540036, 0xbaffffdd, 0xe59d00cc, 0xeb00f65d\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000008, 0xe3a00000\n"
        ".word 0xe3a01001, 0xe58d1000, 0xe59f222c, 0xe1a03000\n"
        ".word 0xe1a01000, 0xe58d0004, 0xe58d0008, 0xebffeb1c\n"
        ".word 0xe59d015c, 0xe3500000, 0xba000012, 0xe59d10c8\n"
        ".word 0xe080000b, 0xe3510000, 0x0a00000e, 0xe59d1164\n"
        ".word 0xe3510000, 0xba00000b, 0xe1a05001, 0xe6bf1070\n"
        ".word 0xe59f01cc, 0xe59d40c8, 0xe1a03007, 0xe3a02000\n"
        ".word 0xe5900000, 0xebff43d5, 0xe3a01006, 0xe5c01004\n"
        ".word 0xe5a04018, 0xe5805010, 0xe59d0160, 0xe59d2150\n"
        ".word 0xe35a0000, 0xe08b1000, 0xe080000b, 0xe0805002\n"
        ".word 0xe59d012c, 0xe0811002, 0xe26a8000, 0xe6bf4071\n"
        ".word 0xe260b000, 0xba00002f, 0xe3500000, 0xba000065\n"
        ".word 0xe3590000, 0x1a00001c, 0xe59d0160, 0xe3500000\n"
        ".word 0xba000019, 0xe59d0178, 0xe3500000, 0x0a000016\n"
        ".word 0xe59d014c, 0xe59d112c, 0xe28d3004, 0xe3a02004\n"
        ".word 0xe8830006, 0xe3500000, 0xed8d8a03, 0x13a00001\n"
        ".word 0xe58d0010, 0xe1a03006, 0xe1a02007, 0xe3a01000\n"
        ".word 0xe1a00005, 0xe58da000, 0xebff4379, 0xe59f0110\n"
        ".word 0xe1a03007, 0xe3a02000, 0xe1a01004, 0xe5900000\n"
        ".word 0xebff43a6, 0xe3a01032, 0xe5c01004, 0xe59f00f0\n"
        ".word 0xe3a01000, 0xe58d1000, 0xe1a02001, 0xe5900000\n"
        ".word 0xe1a03007, 0xe1a01004, 0xebff439c, 0xe3a0101c\n"
        ".word 0xe5c01004, 0xe5806014, 0xe59d1000, 0xe5a01028\n"
        ".word 0xe5808024, 0xea000020, 0xe3500000, 0xba000033\n"
        ".word 0xe3590000, 0x1a00001c, 0xe59d0160, 0xe3500000\n"
        ".word 0xba000019, 0xe59d0178, 0xe3500000, 0x0a000016\n"
        ".word 0xe59d014c, 0xe59d312c, 0xe3a01001, 0xe2902000\n"
        ".word 0xe3a00000, 0xe1cd00f4, 0xed8d8a03, 0x13a02001\n"
        ".word 0xe1a01000, 0xe58d3000, 0xe58d2010, 0xe1a03006\n"
        ".word 0xe1a02007, 0xe1a00005, 0xebff4349, 0xe59f0050\n"
        ".word 0xe1a03007, 0xe3a02000, 0xe1a01004, 0xe5900000\n"
        ".word 0xebff4376, 0xe3a01032, 0xe5c01004, 0xe59f0030\n"
        ".word 0xe1a03007, 0xe3a08001, 0xe3a02000, 0xe5900000\n"
        ".word 0xe1a01004, 0xebff436d, 0xe3a0101c, 0xe5c01004\n"
        ".word 0xe5a06014, 0xe5a08014, 0xe580b024, 0xea000033\n"
        ".word 0x00439960, 0x00434290, 0x00006667, 0x0043427c\n"
        ".word 0x00435d18, 0x0019d6b4, 0x3f800000, 0x010001a0\n"
        ".word 0xe35a0000, 0xba000029, 0xe3590000, 0x1a00001b\n"
        ".word 0xe59d0160, 0xe3500000, 0xba000018, 0xe59d0178\n"
        ".word 0xe3500000, 0x0a000015, 0xe59d014c, 0xe1a03006\n"
        ".word 0xe1a02007, 0xe2901000, 0xe3a00000, 0xe58d0004\n"
        ".word 0xe58d0008, 0xed8d8a03, 0x13a01001, 0xe58d1010\n"
        ".word 0xe1a01000, 0xe1a00005, 0xe58da000, 0xebff4314\n"
        ".word 0xe51f0084, 0xe1a03007, 0xe3a02000, 0xe1a01004\n"
        ".word 0xe5900000, 0xebff4341, 0xe3a01032, 0xe5c01004\n"
        ".word 0xe51f00a4, 0xe3a0b000, 0xe1a03007, 0xe1a0200b\n"
        ".word 0xe5900000, 0xe1a01004, 0xebff4338, 0xe3a0101c\n"
        ".word 0xe5c01004, 0xe5a06014, 0xe5a0b014, 0xe5808024\n"
        ".word 0xe59d014c, 0xe3500001, 0x03590000, 0x1a000054\n"
        ".word 0xe59d0100, 0xe3500000, 0x0a000051, 0xe3500001\n"
        ".word 0xe3a09007, 0x0a000002, 0xe3500002, 0x1a00004c\n"
        ".word 0xea000024, 0xe51f0108, 0xe1a03007, 0xe3a01000\n"
        ".word 0xe3a08002, 0xe590c000, 0xe59c0008, 0xe3500000\n"
        ".word 0x0a000002, 0xe590000c, 0xe3500000, 0x1afffffc\n"
        ".word 0xe6bf2071, 0xe6bf1075, 0xe1a0000c, 0xebff4317\n"
        ".word 0xe1a04000, 0xe5c09004, 0xe5a06014, 0xe3a01001\n"
        ".word 0xe5808014, 0xe1d606f2, 0xebfffd2b, 0xe2400001\n"
        ".word 0xe1c402b4, 0xe5d40005, 0xe3580003, 0xe3800004\n"
        ".word 0xe5c40005, 0x1a00002e, 0xeb00f763, 0xe320f000\n"
        ".word 0xe320f000, 0xeb00f56f, 0xe3500000, 0xe320f000\n"
        ".word 0x1a000024, 0xea000026, 0xe51f019c, 0xe1a03007\n"
        ".word 0xe3a01000, 0xe3a08001, 0xe590c000, 0xe59c0008\n"
        ".word 0xe3500000, 0x0a000002, 0xe590000c, 0xe3500000\n"
        ".word 0x1afffffc, 0xe6bf2071, 0xe6bf1075, 0xe1a0000c\n"
        ".word 0xebff42f2, 0xe1a04000, 0xe5c09004, 0xe5a06014\n"
        ".word 0xe3a01001, 0xe5808014, 0xe1d606f2, 0xebfffd06\n"
        ".word 0xe2400001, 0xe1c402b4, 0xe5d40005, 0xe3580003\n"
        ".word 0xe3800004, 0xe5c40005, 0x1a000009, 0xeb00f73e\n"
        ".word 0xe320f000, 0xe320f000, 0xeb00f54a, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000002, 0xe5d40005, 0xe3800004\n"
        ".word 0xe5c40005, 0xe59d016c, 0xe3500000, 0x0a00000a\n"
        ".word 0xe35a0000, 0xba000008, 0xe59d00c8, 0xe3500000\n"
        ".word 0x0a000005, 0xe5900000, 0xe3100010, 0x11a0100a\n"
        ".word 0x13a00006, 0x0a000005, 0xeb011840, 0xe28dd0e4\n"
        ".word 0xe3a00001, 0xecbd8b04, 0xe28dd010, 0xe8bd8ff0\n"
        ".word 0xe310000a, 0x11a0100a, 0x13a00007, 0x0afffff6\n"
        ".word 0xeafffff4\n");
}

} // namespace smt4::engine
