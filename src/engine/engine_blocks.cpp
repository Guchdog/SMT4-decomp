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

} // namespace smt4::engine
