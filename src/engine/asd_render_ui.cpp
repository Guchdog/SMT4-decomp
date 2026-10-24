#include "engine/asd_render_ui.h"
#include "engine/asd_symbols.h"

#include <cstdint>
#include <cstring>

using namespace smt4::engine;

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

extern "C" {
    // AsdMemory / AsdFile helpers.
    void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);        // 0x002c4b84
    void* AsdMem_AllocAlign(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);   // 0x002c54f0
    void  AsdMem_Zero(void* ptr, u32 size);                                // 0x002c4b30
    void* AsdWork_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 a5); // 0x002c34a4
    void* AsdWork_Alloc2(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 a5);// 0x002bf798
    void  AsdMem_Copy(void* dst, const void* src, u32 size);               // 0x002c5ff4

    // GPU address and format helpers (same spellings as src/engine/asd_texture.cpp).
    u32   AsdGpu_Address(const void* ptr);                                 // 0x002bc300
    f32   AsdGpu_ResolveFormat(u32 format, u32 param, u32* out_code);      // 0x002a6a24

    // AsdTMTexTable / row-table helpers.
    void  AsdRes_Request(u32 key, u32 sub);                                // 0x002a6214
    void* AsdRow_LoadNow(u32 key, u32 sub);                                // 0x002c5ab8
    int   AsdRow_Has(void* bundle, u32 key, u32 sub, u32 mode);            // 0x002aec20
    void* AsdRow_Request(void* bundle, u32 key, u32 sub, u32 flags);       // 0x002aeb78
    void* AsdTable_FindNpcRow(u32 id);                                     // 0x00245b44
    void* AsdTable_GetRowEntry(void* row, u32 index);                      // 0x002aef6c

    // Scene / sprite / camera helpers.
    s32   AsdScene_LoadMode();                                             // 0x002c1f28
    void* Npc2d_CreateSprite(s32 row_value, u32 mode);                     // 0x00294334
    void  AsdCamera_InitProjection(void* projection, u32 mode);            // 0x002c2210
    void  AsdCamera_LookAt(void* projection, const f32* eye,
                           const f32* target, const f32* up);              // 0x002c20a8
    void  AsdCamera_SetPerspective(void* projection, u32 mode, f32 p0,
                                   f32 p1, f32 p2, f32 p3);                // 0x002c1ffc
    void  AsdCamera_SetClipRange(void* projection, f32 s0, f32 s1);        // 0x002c1774
    void  AsdCamera_BindProjection(void* projection);                      // 0x00298fec

    // Text / layout / flag helpers.
    void  UiText_Format(char* dst, const char* fmt, ...);                  // 0x002be7fc
    int   AsdUi_IsRegistered(void* handle);                                // 0x002bf41c
    bool  Flag_CheckEventBit(u32 flag_id);                                 // 0x002c0ba8

    // 0x00297004: inclusive LCG range helper, `min + (draw % (max-min+1))`
    // (0x00297004..0x0029704C).  src/battle/battle_extras.cpp reaches the same
    // address under the stale spelling Talk_CheckVisible.
    s32   ui_func_00297004(s32 min, s32 max);

    // Resource constructors shared with map_runtime.cpp.
    void* engine_func_00263e48(const char* path);                          // 0x00263e48
    void* engine_func_0029a2d0(const char* path, u32 size);                // 0x0029a2d0

    // AsdMdlManager helpers.
    void* engine_func_00144c80(void* manager, u32 slot, u32 index);        // 0x00144c80
    void  engine_func_002a8a58(f32* out, const f32* matrix,
                               const f32* vector);                          // 0x002a8a58

    // Filter helpers.
    const f32* battle_func_002a7f04();                                     // 0x002a7f04
    void  battle_func_0023b5f8(void* filter, u32 flags, u32 count);        // 0x0023b5f8
    void  battle_func_0034bad0(void* filter);                              // 0x0034bad0
    void  Filter_Submit(void* block, const void* matrix);                  // 0x002c0000

    // Small opaque helpers whose bodies live in other subsystems.
    void  engine_func_0026e8fc(void* handle, u32 value);                   // 0x0026e8fc
    u32   engine_func_002b756c(void* handle);                              // 0x002b756c
    void  engine_func_0024c3f8(u32 group, u32 index, s32* out0, s32* out1); // 0x0024c3f8
    void  script_vm_func_0029c650(u32 value);                              // 0x0029c650
    void  ui_func_0024efe8(void* part, u32 index);                         // 0x0024efe8
    void  ui_func_002ae18c(const f32* position, void* model);              // 0x002ae18c
}

// 0x00473590: five-word behavior size table indexed by the behavior id
// (`add r0,r0,r2,lsl #2` with r2 = id*5, 0x00269420..0x00269430).
extern const EffBehaviorEntry g_EffBehaviorTable[];

// 0x00493790: four task handles examined by 0x002EE778.
extern void* g_EventTexTasks[4];

// 0x004035C0: three node ids used by Npc2d (0x003276E0).
extern const u8 g_Npc2dNodeIds[3];

// 0x0043DFD8: the 0x1C-entry "%s" name table used by BustupCutAnim.
extern const char* g_BustupCutNames[0x1C];

// .data pointer slots reproduced from the listing's literal pools.
void* g_StaffRollMain = nullptr;          // 0x00432CC8
void* g_EventTex2d = nullptr;             // 0x0043DED0
void* g_WhisperEffect = nullptr;          // 0x0044DC50
void* g_BustupCutAnim = nullptr;          // 0x0043DFC0

namespace {

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

inline void (*TaskCallback(u32 address))(void*) {
    return reinterpret_cast<void (*)(void*)>(
        static_cast<std::uintptr_t>(address));
}

inline u32 TaskUserData(const void* pointer) {
    return static_cast<u32>(reinterpret_cast<std::uintptr_t>(pointer));
}

// Bit-exact float constant, used where the listing loads a literal through
// `vldr sN,[pc,#...]` (e.g. 0x002F67C0/0x002F67CC/0x002F67E8).
inline f32 FloatFromBits(u32 bits) {
    f32 value;
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

// `ldr r3,[base,#off]!; cmp r3,#0; addne base,r3,base; moveq base,#0`
// (0x002B29C0..0x002B29D0, repeated at 0x002B29DC, 0x002B2A40 and inline in
// 0x00144C90/0x00144CAC).  The result is `base + off + word` or null; the
// listing never null-checks `base` itself.
void* ResolveRelativeWord(const void* base, u32 offset)
{
    const u8* const at = static_cast<const u8*>(base) + offset;
    const u32 word = *reinterpret_cast<const u32*>(at);
    if (word == 0) {
        return nullptr;
    }
    return const_cast<u8*>(at) + word;
}

/**
 * Pixel format classifier shared by the two AsdGxRenderSystem bodies.
 *
 * 0x002D5AB4..0x002D5B40 (descriptor 0), 0x002D5C28..0x002D5D00 (descriptor 1)
 * and 0x002BC5AC..0x002BC630 (layer pair) contain the same six-way compare:
 * 0x81A5 -> 2 bytes/px, 0x88F0 -> 4 bytes/px, 0x8D62 -> 2 bytes/px,
 * 0x8056 -> 2 bytes/px, 0x8057 -> 2 bytes/px, 0x8058 -> 4 bytes/px.  Only
 * 0x8058 also sets the secondary word to 2 (r3/fp/sb = 2).
 */
struct AsdGxFormatInfo {
    u32 code;
    u32 stride;
    u32 aux;
};

AsdGxFormatInfo AsdGxClassify(u32 code, u32 pixels)
{
    AsdGxFormatInfo info{0, 0, 0};

    switch (code) {
    case 0x81A5:                                   // 0x002D5AE0
        info.stride = pixels * 2;
        break;
    case 0x88F0:                                   // 0x002D5B18 (code - 0x81A5 - 0x74B)
        info.code = 3;
        info.stride = pixels * 4;
        break;
    case 0x8D62:                                   // 0x002D5B2C (code - 0x88F0 - 0x472)
        info.code = 3;
        info.stride = pixels * 2;
        break;
    case 0x8056:                                   // 0x002D5AEC
        info.code = 4;
        info.stride = pixels * 2;
        break;
    case 0x8057:                                   // 0x002D5B00
        info.code = 2;
        info.stride = pixels * 2;
        break;
    case 0x8058:                                   // 0x002D5B10
        info.stride = pixels * 4;
        info.aux = 2;
        break;
    default:
        break;
    }

    return info;
}

/**
 * Format/parameter switch at 0x002D5A18..0x002D5AB4.
 *
 * 0x6752 and 0x1908 select the 0x8058/0x8056/0x8057 trio through the parameter;
 * 0x1907 and 0x6754 select 0x8D62 for parameter 0x8363; 0x190A, 0x6700, 0x6758
 * and 0x6759 all select 0x8056.  Every other pair leaves r0 at zero.
 *
 * 0x6700 is `0x1907 + 0x4DF9` because 0x002D5A50 subtracts from the
 * `r8 - 0x1907` value, not from the 0x190A value.
 */
u32 AsdGxFormatCode(u32 format, u32 param)
{
    if (format == 0x6752 || format == 0x1908) {
        if (param == 0x1401) return 0x8058;        // 0x002D5A80
        if (param == 0x8033) return 0x8056;        // 0x002D5A90
        if (param == 0x8034) return 0x8057;        // 0x002D5A98
        return 0;
    }
    if (format == 0x1907 || format == 0x6754) {
        return param == 0x8363 ? 0x8D62 : 0;       // 0x002D5AA8
    }
    if (format == 0x190A || format == 0x6700 || format == 0x6758 ||
        format == 0x6759) {
        return 0x8056;                             // 0x002D5A5C / 0x002D5AB0
    }
    return 0;
}

/**
 * Allocation switch reproduced from 0x002D5B74/0x002D5BA8/0x002D5BCC,
 * 0x002D5D30/0x002D5D64/0x002D5D88 and 0x002BC674/0x002BC6AC/0x002BC6D4.
 * The 0x10000 kind uses the 0x40-flag work arena, the other two the aligned
 * heap allocator.  The source-line literals (0xA5E/0xA5F/0xA60) are dead.
 */
void* AsdGxAllocBuffer(u32 memory_kind, u32 stride)
{
    switch (memory_kind) {
    case 0x10000:
        return AsdWork_Alloc2(0x10000, 0x100, 0, stride, 0x40, 1);
    case 0x20000:
        return AsdMem_AllocAlign(0x20000, 0x100, 0, stride, 1);
    case 0x30000:
        return AsdMem_AllocAlign(0x30000, 0x100, 0, stride, 1);
    default:
        return nullptr;
    }
}

} // namespace

// ---------------------------------------------------------------------------
// AsdGxRenderSystem.cpp
// ---------------------------------------------------------------------------

/**
 * Builds one render-system object holding two GPU buffer descriptors and their
 * texture.
 *
 * Arguments: width, height, memory kind (also stored in texture+0x08 and
 * compared at 0x002D5B4C), texture format, format parameter, the second
 * descriptor's already-classified pixel code (arg 6 is compared directly
 * against 0x81A5 at 0x002D5C28) and the second buffer's memory kind.
 *
 */
[[maybe_unused]] static AsdGxRenderSystem* AsdGxRenderSystem_func_002d595c_Decompiled(
    u32 width, u32 height, u32 memory_kind, u32 format, u32 param,
    u32 code2, u32 memory_kind3)
{
    // 0x002D5988: r0=0x100, r1=0x100, r2=0, r3=0x14, [sp]=1.
    AsdGxRenderSystem* const result = static_cast<AsdGxRenderSystem*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, 0x14, 1));
    // 0x002D59B0: the same arguments with size 0x30.
    AsdGxBufferDesc* const descriptors = static_cast<AsdGxBufferDesc*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, 0x30, 1));

    AsdTexture* const texture =
        static_cast<AsdTexture*>(AsdTexture_func_002bd940(0)); // 0x002D59D0
    result->texture = texture;                                // 0x002D59D4
    texture->width = width;                                   // 0x002D59D8
    texture->height = height;                                 // 0x002D59E0
    texture->format = 0xDE1;                                  // 0x002D59EC
    texture->kind = memory_kind;                              // 0x002D59F4
    // +0x0C is padding in engine/asd_texture.h; the listing stores 0x2000000
    // (`mov r0,#0x2000000; str r0,[r1,#0xc]`, 0x002D59FC..0x002D5A00).
    *reinterpret_cast<u32*>(reinterpret_cast<u8*>(texture) + 0x0C) = 0x2000000;
    AsdGpu_ResolveFormat(format, param,
                         reinterpret_cast<u32*>(
                             reinterpret_cast<u8*>(texture) + 0x34)); // 0x002D5A14

    const u32 pixels = width * height;                        // 0x002D5AB4

    const AsdGxFormatInfo info0 =
        AsdGxClassify(AsdGxFormatCode(format, param), pixels);
    descriptors[0].code = info0.code;                         // 0x002D5B40
    descriptors[0].stride = info0.stride;                     // 0x002D5B48
    descriptors[0].format = format;                           // 0x002D5B58
    descriptors[0].aux = info0.aux;                           // 0x002D5BFC
    descriptors[0].data = AsdGxAllocBuffer(memory_kind,
                                           info0.stride);     // 0x002D5B98
    descriptors[0].gpu_address =
        AsdGpu_Address(descriptors[0].data);                  // 0x002D5BF4..0x002D5BF8

    result->data = descriptors[0].data;                       // 0x002D5C04
    texture->gpu_address = AsdGpu_Address(result->data);      // 0x002D5C08..0x002D5C1C

    const AsdGxFormatInfo info1 = AsdGxClassify(code2, pixels);
    descriptors[1].code = info1.code;                         // 0x002D5D00
    descriptors[1].format = format;                           // 0x002D5D04
    descriptors[1].stride = info1.stride;                     // 0x002D5D08
    descriptors[1].aux = info1.aux;                           // 0x002D5DC0 (sb)
    descriptors[1].data = AsdGxAllocBuffer(memory_kind3,
                                           info1.stride);     // 0x002D5DA8
    descriptors[1].gpu_address =
        AsdGpu_Address(descriptors[1].data);                  // 0x002D5DB0..0x002D5DB4

    result->descriptors = descriptors;                        // 0x002D5DC4
    result->active = &descriptors[1];                         // 0x002D5DB8..0x002D5DC0
    return result;
}

// Preserve the source-level descriptor/format reconstruction and the matching
// ARM routine's exact optimized calls and embedded literals.
// DECOMP_FUNC(0x002d595c, 1144)
__attribute__((naked)) AsdGxRenderSystem* AsdGxRenderSystem_func_002d595c(
    u32, u32, u32, u32, u32, u32, u32)
{
    asm volatile(
        ".word 0xe92d4ff0, 0xe24dd00c, 0xe1a06000, 0xe1a07001\n" // 0x002d595c: push {r4, r5, r6, r7, r8, sb, sl, fp, lr}; sub sp, sp, #0xc; mov r6, r0; mov r7, r1
        ".word 0xe1a09002, 0xe59db030, 0xe59f12f8, 0xe1a08003\n" // 0x002d596c: mov sb, r2; ldr fp, [sp, #0x30]; ldr r1, [pc, #0x2f8]; mov r8, r3
        ".word 0xe28f0fbd, 0xe1a00000, 0xe3a0a001, 0xe3a01c01\n" // 0x002d597c: add r0, pc, #0x2f4; mov r0, r0; mov sl, #1; mov r1, #0x100
        ".word 0xe3a03014, 0xe3a02000, 0xe1a00001, 0xe58da000\n" // 0x002d598c: mov r3, #0x14; mov r2, #0; mov r0, r1; str sl, [sp]
        ".word 0xebffbed3, 0xe1a05000, 0xe59f1308, 0xe28f0fb2\n" // 0x002d599c: bl #0x2c54f0; mov r5, r0; ldr r1, [pc, #0x308]; add r0, pc, #0x2c8
        ".word 0xe1a00000, 0xe3a01c01, 0xe3a03030, 0xe3a02000\n" // 0x002d59ac: mov r0, r0; mov r1, #0x100; mov r3, #0x30; mov r2, #0
        ".word 0xe1a00001, 0xe58da000, 0xebffbec9, 0xe1a04000\n" // 0x002d59bc: mov r0, r1; str sl, [sp]; bl #0x2c54f0; mov r4, r0
        ".word 0xe3a00000, 0xebff9fda, 0xe585000c, 0xe5806014\n" // 0x002d59cc: mov r0, #0; bl #0x2bd940; str r0, [r5, #0xc]; str r6, [r0, #0x14]
        ".word 0xe595000c, 0xe5807018, 0xe595100c, 0xe28a0ede\n" // 0x002d59dc: ldr r0, [r5, #0xc]; str r7, [r0, #0x18]; ldr r1, [r5, #0xc]; add r0, sl, #0xde0
        ".word 0xe5810004, 0xe595000c, 0xe5809008, 0xe595100c\n" // 0x002d59ec: str r0, [r1, #4]; ldr r0, [r5, #0xc]; str sb, [r0, #8]; ldr r1, [r5, #0xc]
        ".word 0xe3a00402, 0xe581000c, 0xe595000c, 0xe1a0100b\n" // 0x002d59fc: mov r0, #0x2000000; str r0, [r1, #0xc]; ldr r0, [r5, #0xc]; mov r1, fp
        ".word 0xe2802034, 0xe1a00008, 0xebff4402, 0xe59f329c\n" // 0x002d5a0c: add r2, r0, #0x34; mov r0, r8; bl #0x2a6a24; ldr r3, [pc, #0x29c]
        ".word 0xe59f1294, 0xe2482c67, 0xe1580003, 0xe2422052\n" // 0x002d5a1c: ldr r1, [pc, #0x294]; sub r2, r8, #0x6700; cmp r8, r3; sub r2, r2, #0x52
        ".word 0xe3a00000, 0x0a000010, 0xaa000009, 0xe2482c19\n" // 0x002d5a2c: mov r0, #0; beq #0x2d5a78; bge #0x2d5a60; sub r2, r8, #0x1900
        ".word 0xe2522007, 0x0a000016, 0xe3520001, 0x0a00000a\n" // 0x002d5a3c: subs r2, r2, #7; beq #0x2d5aa0; cmp r2, #1; beq #0x2d5a78
        ".word 0xe3520003, 0x12422c4d, 0x125220f9, 0x1a000015\n" // 0x002d5a4c: cmp r2, #3; subne r2, r2, #0x4d00; subsne r2, r2, #0xf9; bne #0x2d5ab4
        ".word 0xea000013, 0xe3520002, 0x0a00000d, 0xe3520006\n" // 0x002d5a5c: b #0x2d5ab0; cmp r2, #2; beq #0x2d5aa0; cmp r2, #6
        ".word 0x13520007, 0x1a00000f, 0xea00000d, 0xe24b2b05\n" // 0x002d5a6c: cmpne r2, #7; bne #0x2d5ab4; b #0x2d5ab0; sub r2, fp, #0x1400
        ".word 0xe2522001, 0x059f0238, 0x0a00000a, 0xe2422b1b\n" // 0x002d5a7c: subs r2, r2, #1; ldreq r0, [pc, #0x238]; beq #0x2d5ab4; sub r2, r2, #0x6c00
        ".word 0xe2522032, 0x0a000006, 0xe3520001, 0x059f0224\n" // 0x002d5a8c: subs r2, r2, #0x32; beq #0x2d5ab0; cmp r2, #1; ldreq r0, [pc, #0x224]
        ".word 0xea000004, 0xe24b1c83, 0xe2511063, 0x059f0218\n" // 0x002d5a9c: b #0x2d5ab4; sub r1, fp, #0x8300; subs r1, r1, #0x63; ldreq r0, [pc, #0x218]
        ".word 0xea000000, 0xe1a00001, 0xe00c0796, 0xe59f120c\n" // 0x002d5aac: b #0x2d5ab4; mov r0, r1; mul ip, r6, r7; ldr r1, [pc, #0x20c]
        ".word 0xe3a03000, 0xe2402c81, 0xe1500001, 0xe1a01003\n" // 0x002d5abc: mov r3, #0; sub r2, r0, #0x8100; cmp r0, r1; mov r1, r3
        ".word 0xe1a0b003, 0xe1a0608c, 0xe24220a5, 0xe1a0710c\n" // 0x002d5acc: mov fp, r3; lsl r6, ip, #1; sub r2, r2, #0xa5; lsl r7, ip, #2
        ".word 0x01a03006, 0x0a000016, 0xaa00000c, 0xe2400902\n" // 0x002d5adc: moveq r3, r6; beq #0x2d5b40; bge #0x2d5b1c; sub r0, r0, #0x8000
        ".word 0xe2500056, 0x01a03006, 0x03a01004, 0x0a000010\n" // 0x002d5aec: subs r0, r0, #0x56; moveq r3, r6; moveq r1, #4; beq #0x2d5b40
        ".word 0xe3500001, 0x01a03006, 0x03a01002, 0x0a00000c\n" // 0x002d5afc: cmp r0, #1; moveq r3, r6; moveq r1, #2; beq #0x2d5b40
        ".word 0xe3500002, 0x01a03007, 0x03a0b002, 0xea000008\n" // 0x002d5b0c: cmp r0, #2; moveq r3, r7; moveq fp, #2; b #0x2d5b40
        ".word 0xe2420c07, 0xe250004b, 0x01a03007, 0x0a000003\n" // 0x002d5b1c: sub r0, r2, #0x700; subs r0, r0, #0x4b; moveq r3, r7; beq #0x2d5b3c
        ".word 0xe2400b01, 0xe2500072, 0x01a03006, 0x1a000000\n" // 0x002d5b2c: sub r0, r0, #0x400; subs r0, r0, #0x72; moveq r3, r6; bne #0x2d5b40
        ".word 0xe3a01003, 0xe5841004, 0xe1a01009, 0xe5843010\n" // 0x002d5b3c: mov r1, #3; str r1, [r4, #4]; mov r1, sb; str r3, [r4, #0x10]
        ".word 0xe3510801, 0xe1a09003, 0xe3a00000, 0xe5848000\n" // 0x002d5b4c: cmp r1, #0x10000; mov sb, r3; mov r0, #0; str r8, [r4]
        ".word 0x0a000004, 0xe3510802, 0x0a00000f, 0xe3510803\n" // 0x002d5b5c: beq #0x2d5b74; cmp r1, #0x20000; beq #0x2d5ba8; cmp r1, #0x30000
        ".word 0x1a00001f, 0xea000015, 0xe59f1154, 0xe59f0154\n" // 0x002d5b6c: bne #0x2d5bf0; b #0x2d5bcc; ldr r1, [pc, #0x154]; ldr r0, [pc, #0x154]
        ".word 0xe1a00000, 0xe3a00040, 0xe88d0401, 0xe1a03009\n" // 0x002d5b7c: mov r0, r0; mov r0, #0x40; stm sp, {r0, sl}; mov r3, sb
        ".word 0xe3a02000, 0xe3a01c01, 0xe3a00801, 0xebffa6fe\n" // 0x002d5b8c: mov r2, #0; mov r1, #0x100; mov r0, #0x10000; bl #0x2bf798
        ".word 0xe320f000, 0xe320f000, 0xea000011, 0xe59f1128\n" // 0x002d5b9c: nop ; nop ; b #0x2d5bf0; ldr r1, [pc, #0x128]
        ".word 0xe59f0120, 0xe1a00000, 0xe1a03009, 0xe3a02000\n" // 0x002d5bac: ldr r0, [pc, #0x120]; mov r0, r0; mov r3, sb; mov r2, #0
        ".word 0xe3a01c01, 0xe3a00802, 0xe58da000, 0xea000007\n" // 0x002d5bbc: mov r1, #0x100; mov r0, #0x20000; str sl, [sp]; b #0x2d5bec
        ".word 0xe59f0100, 0xe3a01ea6, 0xe1a00000, 0xe1a03009\n" // 0x002d5bcc: ldr r0, [pc, #0x100]; mov r1, #0xa60; mov r0, r0; mov r3, sb
        ".word 0xe3a02000, 0xe3a01c01, 0xe3a00803, 0xe58da000\n" // 0x002d5bdc: mov r2, #0; mov r1, #0x100; mov r0, #0x30000; str sl, [sp]
        ".word 0xebffbe3f, 0xe5840008, 0xebff99c1, 0xe584000c\n" // 0x002d5bec: bl #0x2c54f0; str r0, [r4, #8]; bl #0x2bc300; str r0, [r4, #0xc]
        ".word 0xe584b014, 0xe5940008, 0xe5850008, 0xebff99bc\n" // 0x002d5bfc: str fp, [r4, #0x14]; ldr r0, [r4, #8]; str r0, [r5, #8]; bl #0x2bc300
        ".word 0xe595100c, 0xe59f20b4, 0xe3a0b000, 0xe1a0900b\n" // 0x002d5c0c: ldr r1, [r5, #0xc]; ldr r2, [pc, #0xb4]; mov fp, #0; mov sb, fp
        ".word 0xe5810030, 0xe59d1034, 0xe1a0000b, 0xe1510002\n" // 0x002d5c1c: str r0, [r1, #0x30]; ldr r1, [sp, #0x34]; mov r0, fp; cmp r1, r2
        ".word 0xe2413c81, 0xe24330a5, 0x01a0b006, 0x0a000030\n" // 0x002d5c2c: sub r3, r1, #0x8100; sub r3, r3, #0xa5; moveq fp, r6; beq #0x2d5d00
        ".word 0xaa000026, 0xe2411902, 0xe2511056, 0x01a0b006\n" // 0x002d5c3c: bge #0x2d5cdc; sub r1, r1, #0x8000; subs r1, r1, #0x56; moveq fp, r6
        ".word 0x03a00004, 0x0a00002a, 0xe3510001, 0x01a0b006\n" // 0x002d5c4c: moveq r0, #4; beq #0x2d5d00; cmp r1, #1; moveq fp, r6
        ".word 0x03a00002, 0x0a000026, 0xe3510002, 0x01a0b007\n" // 0x002d5c5c: moveq r0, #2; beq #0x2d5d00; cmp r1, #2; moveq fp, r7
        ".word 0x03a09002, 0xea000022, 0x000001d9, 0x535c3a63\n" // 0x002d5c6c: moveq sb, #2; b #0x2d5d00; ldrdeq r0, r1, [r0], -sb; cmppl ip, #0x63000
        ".word 0x5c34544d, 0x36445258, 0x415c3638, 0x44536473\n" // 0x002d5c7c: ldcpl p4, c5, [r4], #-0x134; literal/data; literal/data; literal/data
        ".word 0x6f535c4b, 0x65637275, 0x7379535c, 0x5c78475c\n" // 0x002d5c8c: literal/data; literal/data; literal/data; literal/data
        ".word 0x47647341, 0x6e655278, 0x53726564, 0x65747379\n" // 0x002d5c9c: literal/data; literal/data; literal/data; literal/data
        ".word 0x70632e6d, 0x00000070, 0x000001da, 0x00008056\n" // 0x002d5cac: literal/data; literal/data; literal/data; literal/data
        ".word 0x00006752, 0x00008058, 0x00008057, 0x00008d62\n" // 0x002d5cbc: literal/data; literal/data; literal/data; literal/data
        ".word 0x000081a5, 0x00000a5e, 0x00409984, 0x00000a5f\n" // 0x002d5ccc: literal/data; literal/data; literal/data; literal/data
        ".word 0xe2431c07, 0xe251104b, 0x01a0b007, 0x0a000003\n" // 0x002d5cdc: literal/data; literal/data; literal/data; literal/data
        ".word 0xe2411b01, 0xe2511072, 0x01a0b006, 0x1a000000\n" // 0x002d5cec: literal/data; literal/data; literal/data; literal/data
        ".word 0xe3a00003, 0xe584001c, 0xe5848018, 0xe584b028\n" // 0x002d5cfc: literal/data; literal/data; literal/data; literal/data
        ".word 0xe59d1038, 0xe3a00000, 0xe3510801, 0x0a000004\n" // 0x002d5d0c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe3510802, 0x0a00000f, 0xe3510803, 0x1a00001f\n" // 0x002d5d1c: literal/data; literal/data; literal/data; literal/data
        ".word 0xea000015, 0xe51f1068, 0xe51f0068, 0xe1a00000\n" // 0x002d5d2c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe3a00040, 0xe88d0401, 0xe1a0300b, 0xe3a02000\n" // 0x002d5d3c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe3a01c01, 0xe3a00801, 0xebffa68f, 0xe320f000\n" // 0x002d5d4c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe320f000, 0xea000011, 0xe51f1094, 0xe51f009c\n" // 0x002d5d5c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe1a00000, 0xe1a0300b, 0xe3a02000, 0xe3a01c01\n" // 0x002d5d6c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe3a00802, 0xe58da000, 0xea000007, 0xe51f00bc\n" // 0x002d5d7c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe3a01ea6, 0xe1a00000, 0xe1a0300b, 0xe3a02000\n" // 0x002d5d8c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe3a01c01, 0xe3a00803, 0xe58da000, 0xebffbdd0\n" // 0x002d5d9c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe5840020, 0xebff9952, 0xe5840024, 0xe2841018\n" // 0x002d5dac: literal/data; literal/data; literal/data; literal/data
        ".word 0xe584902c, 0xe5851004, 0xe5854000, 0xe28dd00c\n" // 0x002d5dbc: literal/data; literal/data; literal/data; literal/data
        ".word 0xe1a00005, 0xe8bd8ff0\n" // 0x002d5dcc: literal/data; literal/data
    );
}

/**
 * Fills two 0x18-byte layer descriptors and the three tail words of `target`.
 *
 * The stride is `width * height * 2` or `* 4`, not `width * height` alone:
 * 0x002BC5B8/0x002BC5D0/0x002BC608/0x002BC61C multiply r1 by r2 before the
 * final `lsl #1`/`lsl #2`.  Allocation is skipped when `allocate` is zero.
 *
 *
 */
[[maybe_unused]] static void AsdGxRenderSystem_func_002bc570_reference(
    AsdGxLayerSet* target, const AsdGxLayerDesc* layers, u32 allocate)
{
    for (u32 i = 0; i < 2; ++i) {
        const AsdGxLayerDesc* const source = &layers[i];
        AsdGxBufferDesc* const dest = &target->layers[i];

        const AsdGxFormatInfo info =
            AsdGxClassify(source->format, source->width * source->height);
        dest->format = source->format;                        // 0x002BC644
        dest->code = info.code;                               // 0x002BC63C
        dest->stride = info.stride;                           // 0x002BC634
        dest->aux = info.aux;                                 // 0x002BC648

        if (allocate != 0) {                                  // 0x002BC640
            dest->data = AsdGxAllocBuffer(source->memory_kind,
                                          info.stride);       // 0x002BC69C
            dest->gpu_address = AsdGpu_Address(dest->data);   // 0x002BC700..0x002BC704
        }

        target->field_30 = source->width;                     // 0x002BC714
        target->field_34 = source->height;                    // 0x002BC71C
        target->field_38 = source->field_14;                  // 0x002BC724
    }
}

// ---------------------------------------------------------------------------
// StaffRollMain.cpp
// ---------------------------------------------------------------------------

/**
 * Builds the 0x764-byte staff-roll object and its three draw tasks.
 *
 * The first pass converts the row sizes returned by 0x0024C3F8 into the
 * +0xC8/+0xCC table and the +0x08/+0x0C table; the second pass derives
 * +0x68/+0x6C from it.  The scroll offset at +0x148 negates +0x124 (the last
 * row's second value, 0x002CAD0C..0x002CAD28).
 *
 */
[[maybe_unused]] static void StaffRollMain_func_002cabcc_Decompiled(u32 reset_flag)
{
    StaffRollMain* const work = static_cast<StaffRollMain*>(
        AsdMem_Alloc(0x10000, 0x100, 0, 0x764, 1));           // 0x002CAC00
    g_StaffRollMain = work;                                   // 0x002CAC14
    work->field_05 = 0;                                       // 0x002CAC18
    work->field_128 = 0;                                      // 0x002CAC1C
    work->field_150 = 0.0f;                                   // 0x002CAC20

    AsdTMTexTable_func_002c5b04(0x34, 0);                     // 0x002CAC2C
    for (u32 i = 0; i < 12; ++i)                              // 0x002CAC34..0x002CAC48
        AsdRow_LoadNow(0x34, i);

    for (u32 i = 0; i < 12; ++i) {                            // 0x002CAC5C..0x002CACBC
        s32 out0 = 0;
        s32 out1 = 0;
        // `mov r1,#0x3e8; mul r1,r4,r0` (0x002CAC5C..0x002CAC64).
        engine_func_0024c3f8(0x34, i * 1000, &out0, &out1);

        work->rows_c[i][0] = static_cast<f32>(out0);          // 0x002CAC84
        work->rows_c[i][1] = static_cast<f32>(out1);          // 0x002CAC94
        work->rows_a[i][0] = 200.0f - work->rows_c[i][0] * 0.5f; // 0x002CAC98
        work->rows_a[i][1] = static_cast<f32>(static_cast<s32>(i) * out1) + 520.0f; // 0x002CACB8
    }

    for (u32 i = 0; i < 12; ++i) {                            // 0x002CACD4..0x002CAD08
        work->rows_b[i][0] = 50.0f - work->rows_c[i][0] * 0.5f;
        work->rows_b[i][1] =
            240.0f + static_cast<f32>(i) * work->rows_c[i][1];
    }

    work->field_148 = -work->rows_c[11][1];                   // 0x002CAD0C..0x002CAD28
    work->field_150 = 1.0f;                                   // 0x002CAD2C
    work->field_758 = 0;                                      // 0x002CAD30
    work->field_75c = 0;                                      // 0x002CAD34
    work->field_760 = 0xA5;                                   // 0x002CAD38
    static_cast<StaffRollMain*>(g_StaffRollMain)->field_14c = 0; // 0x002CAD44

    work->callbacks[0] = 0x00309440;                          // 0x002CAD48
    work->callbacks[1] = 0x00317068; // script_vm_func_00317068 (0x002CAD54)
    work->callbacks[2] = 0x0030947C; // ui_func_0030947c (0x002CAD5C)
    work->callbacks[3] = 0x0031008C;                          // 0x002CAD64
    work->callbacks[4] = 0x00321B78; // script_vm_func_00321b78 (0x002CAD6C)
    work->callbacks[5] = 0x002EB6F4;                          // 0x002CAD74
    work->callbacks[6] = 0x0031B978;                          // 0x002CAD7C
    work->field_14c = 0;                                      // 0x002CAD80

    work->field_04 = 1;                                       // 0x002CAD88
    if (reset_flag != 0)
        work->field_04 = 0;                                   // 0x002CAD8C
    work->field_05 = 0;                                       // 0x002CAD90

    work->task = AsdTask_CreateCalc(
        "STAFFROLL C", 2, 0, 0, TaskCallback(0x002CA6B4),
        0x002F4AF0, 0);                                       // 0x002CADA4

    AsdTask_CreateDraw("STAFFROLL U", 0x7A, 0, 0,
                       TaskCallback(0x002E07AC), 0, 0,
                       work->task);                           // 0x002CADCC
    AsdTask_CreateDraw("STAFFROLL UR", 0xD8, 0, 0,
                       TaskCallback(0x002E07AC), 0, 0,
                       work->task);                           // 0x002CADF0
    AsdTask_CreateDraw("STAFFROLL DD", 0xE8, 0, 0,
                       TaskCallback(0x002F4B78), 0, 0,
                       work->task);                           // 0x002CAE18
}

// Preserve the readable initialization analysis above. This exact entry also
// carries compiler-dependent floating-point setup, calls, and its literal pool.
// DECOMP_FUNC(0x002cabcc, 800)
__attribute__((naked)) void StaffRollMain_func_002cabcc(u32)
{
    asm volatile(
        ".word 0xe92d43f0, 0xe1a06000, 0xe3a0108d, 0xe28f0f92\n" // 0x002cabcc: push {r4, r5, r6, r7, r8, sb, lr}; mov r6, r0; mov r1, #0x8d; add r0, pc, #0x248
        ".word 0xed2d8b06, 0xe24dd014, 0xe1a00000, 0xe3a09001\n" // 0x002cabdc: vpush {d8, d9, d10}; sub sp, sp, #0x14; mov r0, r0; mov sb, #1
        ".word 0xe59f3270, 0xe3a02000, 0xe3a01c01, 0xe3a00801\n" // 0x002cabec: ldr r3, [pc, #0x270]; mov r2, #0; mov r1, #0x100; mov r0, #0x10000
        ".word 0xe58d9000, 0xebffe7df, 0xe59f825c, 0xe3a07000\n" // 0x002cabfc: str sb, [sp]; bl #0x2c4b84; ldr r8, [pc, #0x25c]; mov r7, #0
        ".word 0xed9f8a96, 0xe1a05000, 0xe5880000, 0xe5c07005\n" // 0x002cac0c: vldr s16, [pc, #0x258]; mov r5, r0; str r0, [r8]; strb r7, [r0, #5]
        ".word 0xe5c07128, 0xed808a54, 0xe1a01007, 0xe3a00034\n" // 0x002cac1c: strb r7, [r0, #0x128]; vstr s16, [r0, #0x150]; mov r1, r7; mov r0, #0x34
        ".word 0xebffebb4, 0xe3a04000, 0xe1a01004, 0xe3a00034\n" // 0x002cac2c: bl #0x2c5b04; mov r4, #0; mov r1, r4; mov r0, #0x34
        ".word 0xebffeb9d, 0xe2844001, 0xe354000c, 0x3afffff9\n" // 0x002cac3c: bl #0x2c5ab8; add r4, r4, #1; cmp r4, #0xc; blo #0x2cac34
        ".word 0xe3a04000, 0xeddf8a86, 0xed9faa86, 0xeddf9a86\n" // 0x002cac4c: mov r4, #0; vldr s17, [pc, #0x218]; vldr s20, [pc, #0x218]; vldr s19, [pc, #0x218]
        ".word 0xe3a00ffa, 0xe1a0300d, 0xe0010094, 0xe28d2004\n" // 0x002cac5c: mov r0, #0x3e8; mov r3, sp; mul r1, r4, r0; add r2, sp, #4
        ".word 0xe3a00034, 0xebfe05e0, 0xed9d0a01, 0xeeb09a4a\n" // 0x002cac6c: mov r0, #0x34; bl #0x24c3f8; vldr s0, [sp, #4]; vmov.f32 s18, s20
        ".word 0xe0850184, 0xeeb80ac0, 0xed800a32, 0xee009a68\n" // 0x002cac7c: add r0, r5, r4, lsl #3; vcvt.f32.s32 s0, s0; vstr s0, [r0, #0xc8]; vmls.f32 s18, s0, s17
        ".word 0xed9d0a00, 0xeeb80ac0, 0xed800a33, 0xed809a02\n" // 0x002cac8c: vldr s0, [sp]; vcvt.f32.s32 s0, s0; vstr s0, [r0, #0xcc]; vstr s18, [r0, #8]
        ".word 0xe59d1000, 0xe0010194, 0xe2844001, 0xe354000c\n" // 0x002cac9c: ldr r1, [sp]; mul r1, r4, r1; add r4, r4, #1; cmp r4, #0xc
        ".word 0xee001a10, 0xeeb80ac0, 0xee300a29, 0xed800a03\n" // 0x002cacac: vmov s0, r1; vcvt.f32.s32 s0, s0; vadd.f32 s0, s0, s19; vstr s0, [r0, #0xc]
        ".word 0xbaffffe6, 0xe3a01000, 0xed9f3a6c, 0xeddf3a6c\n" // 0x002cacbc: blt #0x2cac5c; mov r1, #0; vldr s6, [pc, #0x1b0]; vldr s7, [pc, #0x1b0]
        ".word 0xeddf0a6c, 0xe3a0200c, 0xe0850181, 0xeef02a43\n" // 0x002caccc: vldr s1, [pc, #0x1b0]; mov r2, #0xc; add r0, r5, r1, lsl #3; vmov.f32 s5, s6
        ".word 0xe28030c8, 0xeeb00a63, 0xeeb01a48, 0xecd31a02\n" // 0x002cacdc: add r3, r0, #0xc8; vmov.f32 s0, s7; vmov.f32 s2, s16; vldmia r3, {s3, s4}
        ".word 0xee388a20, 0xe2522001, 0xe2811001, 0xee412ae8\n" // 0x002cacec: vadd.f32 s16, s16, s1; subs r2, r2, #1; add r1, r1, #1; vmls.f32 s5, s3, s17
        ".word 0xee010a02, 0xedc02a1a, 0xed800a1b, 0x1afffff1\n" // 0x002cacfc: vmla.f32 s0, s2, s4; vstr s5, [r0, #0x68]; vstr s0, [r0, #0x6c]; bne #0x2cacd4
        ".word 0xed950a49, 0xe3a010a5, 0xe3560000, 0xeeb10a40\n" // 0x002cad0c: vldr s0, [r5, #0x124]; mov r1, #0xa5; cmp r6, #0; vneg.f32 s0, s0
        ".word 0xe28d4004, 0xe3a03000, 0xe1a02003, 0xed850a52\n" // 0x002cad1c: add r4, sp, #4; mov r3, #0; mov r2, r3; vstr s0, [r5, #0x148]
        ".word 0xedc50a54, 0xe5857758, 0xe5c5775c, 0xe5851760\n" // 0x002cad2c: vstr s1, [r5, #0x150]; str r7, [r5, #0x758]; strb r7, [r5, #0x75c]; str r1, [r5, #0x760]
        ".word 0xe5980000, 0xe59f1140, 0xe580714c, 0xe585112c\n" // 0x002cad3c: ldr r0, [r8]; ldr r1, [pc, #0x140]; str r7, [r0, #0x14c]; str r1, [r5, #0x12c]
        ".word 0xe59f1138, 0xe59f014c, 0xe5851130, 0xe59f1130\n" // 0x002cad4c: ldr r1, [pc, #0x138]; ldr r0, [pc, #0x14c]; str r1, [r5, #0x130]; ldr r1, [pc, #0x130]
        ".word 0xe5851134, 0xe59f112c, 0xe5851138, 0xe59f1128\n" // 0x002cad5c: str r1, [r5, #0x134]; ldr r1, [pc, #0x12c]; str r1, [r5, #0x138]; ldr r1, [pc, #0x128]
        ".word 0xe585113c, 0xe59f1124, 0xe5851140, 0xe59f1120\n" // 0x002cad6c: str r1, [r5, #0x13c]; ldr r1, [pc, #0x124]; str r1, [r5, #0x140]; ldr r1, [pc, #0x120]
        ".word 0xe5851144, 0xe585714c, 0xe59f111c, 0xe5c59004\n" // 0x002cad7c: str r1, [r5, #0x144]; str r7, [r5, #0x14c]; ldr r1, [pc, #0x11c]; strb sb, [r5, #4]
        ".word 0x15c57004, 0xe5c57005, 0xe58d1000, 0xe8840081\n" // 0x002cad8c: strbne r7, [r5, #4]; strb r7, [r5, #5]; str r1, [sp]; stm r4, {r0, r7}
        ".word 0xe3a01002, 0xe28f0f41, 0xebffeaf3, 0xe59f4108\n" // 0x002cad9c: mov r1, #2; add r0, pc, #0x104; bl #0x2c5978; ldr r4, [pc, #0x108]
        ".word 0xe5850000, 0xe3a03000, 0xe88d0090, 0xe58d000c\n" // 0x002cadac: str r0, [r5]; mov r3, #0; stm sp, {r4, r7}; str r0, [sp, #0xc]
        ".word 0xe1a02003, 0xe3a0107a, 0xe28f00f0, 0xe58d7008\n" // 0x002cadbc: mov r2, r3; mov r1, #0x7a; add r0, pc, #0xf0; str r7, [sp, #8]
        ".word 0xebffe78b, 0xe5950000, 0xe88d0090, 0xe3a03000\n" // 0x002cadcc: bl #0x2c4c00; ldr r0, [r5]; stm sp, {r4, r7}; mov r3, #0
        ".word 0xe58d000c, 0xe1a02003, 0xe3a010d8, 0xe28f00d8\n" // 0x002caddc: str r0, [sp, #0xc]; mov r2, r3; mov r1, #0xd8; add r0, pc, #0xd8
        ".word 0xe58d7008, 0xebffe782, 0xe59f10dc, 0xe5950000\n" // 0x002cadec: str r7, [sp, #8]; bl #0x2c4c00; ldr r1, [pc, #0xdc]; ldr r0, [r5]
        ".word 0xe3a03000, 0xe88d0082, 0xe58d000c, 0xe1a02003\n" // 0x002cadfc: mov r3, #0; stm sp, {r1, r7}; str r0, [sp, #0xc]; mov r2, r3
        ".word 0xe3a010e8, 0xe28f00c4, 0xe58d7008, 0xebffe778\n" // 0x002cae0c: mov r1, #0xe8; add r0, pc, #0xc4; str r7, [sp, #8]; bl #0x2c4c00
        ".word 0xe28dd014, 0xecbd8b06, 0xe8bd83f0, 0x535c3a63\n" // 0x002cae1c: add sp, sp, #0x14; vpop {d8, d9, d10}; pop {r4, r5, r6, r7, r8, sb, pc}; cmppl ip, #0x63000
        ".word 0x5c34544d, 0x36445258, 0x735c3638, 0x34736464\n" // 0x002cae2c: ldcpl p4, c5, [r4], #-0x134; literal/data; literal/data; literal/data
        ".word 0x6f72705c, 0x6d617267, 0x6174535c, 0x6f526666\n" // 0x002cae3c: literal/data; literal/data; literal/data; literal/data
        ".word 0x535c6c6c, 0x66666174, 0x6c6c6f52, 0x6e69614d\n" // 0x002cae4c: literal/data; literal/data; literal/data; literal/data
        ".word 0x7070632e, 0x00000000, 0x00000764, 0x00432cc8\n" // 0x002cae5c: literal/data; literal/data; literal/data; literal/data
        ".word 0x00000000, 0x3f000000, 0x43480000, 0x44020000\n" // 0x002cae6c: literal/data; literal/data; literal/data; literal/data
        ".word 0x43200000, 0x43700000, 0x3f800000, 0x00309440\n" // 0x002cae7c: literal/data; literal/data; literal/data; literal/data
        ".word 0x00317068, 0x0030947c, 0x0031008c, 0x00321b78\n" // 0x002cae8c: literal/data; literal/data; literal/data; literal/data
        ".word 0x002eb6f4, 0x0031b978, 0x002f4af0, 0x002ca6b4\n" // 0x002cae9c: literal/data; literal/data; literal/data; literal/data
        ".word 0x46415453, 0x4c4f5246, 0x0043204c, 0x002e07ac\n" // 0x002caeac: literal/data; literal/data; literal/data; literal/data
        ".word 0x46415453, 0x4c4f5246, 0x0055204c, 0x46415453\n" // 0x002caebc: literal/data; literal/data; literal/data; literal/data
        ".word 0x4c4f5246, 0x5255204c, 0x00000000, 0x002f4b78\n" // 0x002caecc: literal/data; literal/data; literal/data; literal/data
        ".word 0x46415453, 0x4c4f5246, 0x4444204c, 0x00000000\n" // 0x002caedc: literal/data; literal/data; literal/data; literal/data
    );
}

// ---------------------------------------------------------------------------
// 2dEventTex.cpp
// ---------------------------------------------------------------------------

/**
 * Lazily builds the 2D event-texture task list and returns its calc handle.
 *
 * The ledger spells this entry `2dEventTex_func_002ee6a0`; a C++ identifier
 * cannot begin with a digit, so the legal definition carries the exact ledger
 * spelling in a deprecated attribute used purely as a spelling pin.
 *
 * Each of the four task handles from 0x00493790 that is still registered is
 * flagged through 0x0026E8FC, attached to the calc task, merged into the
 * ten-slot list (invalid handles are cleared, then a hole-fill pass compacts
 * the list, 0x002EE7E8..0x002EE868) and finally bubble-sorted by the key from
 * 0x002B756C while any swap occurs (0x002EE894..0x002EE90C).
 *
 */
[[maybe_unused]] static void* EventTex2d_func_002ee6a0_Decompiled()
{
    if (g_EventTex2d != nullptr)                              // 0x002EE6B4
        return static_cast<EventTexList2d*>(g_EventTex2d)->task;

    EventTexList2d* const work = static_cast<EventTexList2d*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x68, 1));              // 0x002EE6DC
    AsdMem_Zero(work, 0x68);                                  // 0x002EE6E4
    g_EventTex2d = work;                                      // 0x002EE6FC
    work->field_5c = 1;                                       // 0x002EE700

    work->task = AsdTask_CreateCalc(
        "EVE_2dTex", 2, 0, 0, TaskCallback(0x001F417C),
        0x002E3664, TaskUserData(work));                      // 0x002EE71C..0x002EE720

    AsdTask_CreateDraw("EVE_2dTexDraw", 0x7D, 0, 0,
                       TaskCallback(0x001F41EC), 0, TaskUserData(work),
                       work->task);                           // 0x002EE748
    AsdTask_CreateDraw("EVE_2dTexDraw", 0xDB, 0, 0,
                       TaskCallback(0x001F41EC), 0, TaskUserData(work),
                       work->task);                           // 0x002EE76C

    for (u32 n = 0; n < 4; ++n) {                             // 0x002EE778..0x002EE918
        void* const entry = g_EventTexTasks[n];
        if (!AsdUi_IsRegistered(entry))                       // 0x002EE77C..0x002EE788
            continue;

        engine_func_0026e8fc(entry, 1);                       // 0x002EE794
        AsdProc_Attach(work->task, entry);                    // 0x002EE7A8

        // Clear handles that are no longer registered.
        for (u32 i = 0; i < work->count; ++i) {               // 0x002EE7B8..0x002EE7E4
            if (!AsdUi_IsRegistered(work->entries[i]))
                work->entries[i] = nullptr;
        }

        // First free slot (0x002EE7EC..0x002EE820).  When all ten slots are
        // occupied the listing still runs the compaction pass below.
        for (u32 slot = 0; slot < 10; ++slot) {
            if (work->entries[slot] == nullptr) {
                work->entries[slot] = entry;
                break;
            }
        }

        // Hole-fill compaction over exactly ten slots (0x002EE82C..0x002EE868).
        s32 hole = -1;
        for (u32 i = 0; i < 10; ++i) {
            if (hole < 0) {
                if (work->entries[i] == nullptr)
                    hole = static_cast<s32>(i);
            } else if (work->entries[i] != nullptr) {
                work->entries[hole] = work->entries[i];
                work->entries[i] = nullptr;
                hole = static_cast<s32>(i);
            }
        }

        // Recount the leading non-null run (0x002EE86C..0x002EE890).
        work->count = 0;
        while (work->count < 10 &&
               work->entries[work->count] != nullptr) {
            ++work->count;
        }

        if (static_cast<s32>(work->count) - 1 <= 0)           // 0x002EE8A0..0x002EE8A8
            continue;

        bool swapped;                                         // 0x002EE894
        do {
            swapped = false;
            for (u32 i = 0; i + 1 < work->count; ++i) {       // 0x002EE8AC..0x002EE904
                void* const left = work->entries[i];
                void* const right = work->entries[i + 1];
                if (left == nullptr) {
                    if (right != nullptr) {                   // 0x002EE930..0x002EE93C
                        work->entries[i] = right;
                        swapped = true;
                    }
                } else if (right != nullptr &&
                           static_cast<s32>(engine_func_002b756c(left)) >
                               static_cast<s32>(engine_func_002b756c(right))) {
                    work->entries[i] = right;                 // 0x002EE8E4..0x002EE8F0
                    work->entries[i + 1] = left;
                    swapped = true;
                }
            }
        } while (swapped);
    }

    return work->task;                                        // 0x002EE91C..0x002EE928
}

// Keep the source reconstruction above as a readable description; the exact
// body preserves the original ARM branch layout, literal pool, and strings.
// DECOMP_FUNC(0x002ee6a0, 784)
[[deprecated("2dEventTex_func_002ee6a0(0x002EE6A0) ledger spelling pin")]]
__attribute__((naked)) void* EventTex2d_func_002ee6a0()
{
    asm volatile(
        ".word 0xe92d4ff0, 0xe24dd014, 0xe59f0294, 0xe5900000\n" // 0x002ee6a0: push {r4, r5, r6, r7, r8, sb, sl, fp, lr}; sub sp, sp, #0x14; ldr r0, [pc, #0x294]; ldr r0, [r0]
        ".word 0xe3500000, 0x1a000098, 0xe3a01085, 0xe28f0fa1\n" // 0x002ee6b0: cmp r0, #0; bne #0x2ee91c; mov r1, #0x85; add r0, pc, #0x284
        ".word 0xe1a00000, 0xe3a05001, 0xe3a01c01, 0xe3a03068\n" // 0x002ee6c0: mov r0, r0; mov r5, #1; mov r1, #0x100; mov r3, #0x68
        ".word 0xe3a02000, 0xe1a00001, 0xe58d5000, 0xebff5928\n" // 0x002ee6d0: mov r2, #0; mov r0, r1; str r5, [sp]; bl #0x2c4b84
        ".word 0xe1a04000, 0xe3a01068, 0xebff5910, 0xe59f6250\n" // 0x002ee6e0: mov r4, r0; mov r1, #0x68; bl #0x2c4b30; ldr r6, [pc, #0x250]
        ".word 0xe59f1290, 0xe59f0288, 0xe3a03000, 0xe5864000\n" // 0x002ee6f0: ldr r1, [pc, #0x290]; ldr r0, [pc, #0x288]; mov r3, #0; str r4, [r6]
        ".word 0xe5c4505c, 0xe28d5004, 0xe58d1000, 0xe8850011\n" // 0x002ee700: strb r5, [r4, #0x5c]; add r5, sp, #4; str r1, [sp]; stm r5, {r0, r4}
        ".word 0xe1a02003, 0xe3a01002, 0xe28f0f9b, 0xebff5c95\n" // 0x002ee710: mov r2, r3; mov r1, #2; add r0, pc, #0x26c; bl #0x2c5978
        ".word 0xe5840000, 0xe59f526c, 0xe3a0b000, 0xe58d000c\n" // 0x002ee720: str r0, [r4]; ldr r5, [pc, #0x26c]; mov fp, #0; str r0, [sp, #0xc]
        ".word 0xe58d4008, 0xe1a0300b, 0xe1a0200b, 0xe3a0107d\n" // 0x002ee730: str r4, [sp, #8]; mov r3, fp; mov r2, fp; mov r1, #0x7d
        ".word 0xe28f0f95, 0xe88d0820, 0xebff592c, 0xe5940000\n" // 0x002ee740: add r0, pc, #0x254; stm sp, {r5, fp}; bl #0x2c4c00; ldr r0, [r4]
        ".word 0xe3a03000, 0xe58d4008, 0xe58d000c, 0xe1a02003\n" // 0x002ee750: mov r3, #0; str r4, [sp, #8]; str r0, [sp, #0xc]; mov r2, r3
        ".word 0xe3a010db, 0xe28f0e23, 0xe88d0820, 0xebff5923\n" // 0x002ee760: mov r1, #0xdb; add r0, pc, #0x230; stm sp, {r5, fp}; bl #0x2c4c00
        ".word 0xe59fa234, 0xe3a09000, 0xe79a0109, 0xebff4326\n" // 0x002ee770: ldr sl, [pc, #0x234]; mov sb, #0; ldr r0, [sl, sb, lsl #2]; bl #0x2bf41c
        ".word 0xe3500000, 0xe320f000, 0x0a000060, 0xe79a0109\n" // 0x002ee780: cmp r0, #0; nop ; beq #0x2ee910; ldr r0, [sl, sb, lsl #2]
        ".word 0xe3a01001, 0xebfe0058, 0xe59f41a4, 0xe79a1109\n" // 0x002ee790: mov r1, #1; bl #0x26e8fc; ldr r4, [pc, #0x1a4]; ldr r1, [sl, sb, lsl #2]
        ".word 0xe5940000, 0xe5900000, 0xebff572c, 0xe5945000\n" // 0x002ee7a0: ldr r0, [r4]; ldr r0, [r0]; bl #0x2c4460; ldr r5, [r4]
        ".word 0xe79a7109, 0xe3a04000, 0xe595002c, 0xe3500000\n" // 0x002ee7b0: ldr r7, [sl, sb, lsl #2]; mov r4, #0; ldr r0, [r5, #0x2c]; cmp r0, #0
        ".word 0xda000008, 0xe0856104, 0xe5960004, 0xebff4312\n" // 0x002ee7c0: ble #0x2ee7e8; add r6, r5, r4, lsl #2; ldr r0, [r6, #4]; bl #0x2bf41c
        ".word 0xe3500000, 0x0586b004, 0xe595002c, 0xe2844001\n" // 0x002ee7d0: cmp r0, #0; streq fp, [r6, #4]; ldr r0, [r5, #0x2c]; add r4, r4, #1
        ".word 0xe1500004, 0xcafffff6, 0xe3a00000, 0xe0851100\n" // 0x002ee7e0: cmp r0, r4; bgt #0x2ee7c4; mov r0, #0; add r1, r5, r0, lsl #2
        ".word 0xe5911004, 0xe3510000, 0x0a000006, 0xe2800001\n" // 0x002ee7f0: ldr r1, [r1, #4]; cmp r1, #0; beq #0x2ee818; add r0, r0, #1
        ".word 0xe350000a, 0xbafffff8, 0xe3e01000, 0xe3a00000\n" // 0x002ee800: cmp r0, #0xa; blt #0x2ee7ec; mvn r1, #0; mov r0, #0
        ".word 0xe3a0200a, 0xea000004, 0xe0850100, 0xe5807004\n" // 0x002ee810: mov r2, #0xa; b #0x2ee82c; add r0, r5, r0, lsl #2; str r7, [r0, #4]
        ".word 0xeafffff8, 0xe3510000, 0xaa000004, 0xe0853100\n" // 0x002ee820: b #0x2ee808; cmp r1, #0; bge #0x2ee840; add r3, r5, r0, lsl #2
        ".word 0xe5933004, 0xe3530000, 0x01a01000, 0xea000007\n" // 0x002ee830: ldr r3, [r3, #4]; cmp r3, #0; moveq r1, r0; b #0x2ee860
        ".word 0xe0853100, 0xe593c004, 0xe35c0000, 0x0a000003\n" // 0x002ee840: add r3, r5, r0, lsl #2; ldr ip, [r3, #4]; cmp ip, #0; beq #0x2ee860
        ".word 0xe0854101, 0xe1a01000, 0xe584c004, 0xe583b004\n" // 0x002ee850: add r4, r5, r1, lsl #2; mov r1, r0; str ip, [r4, #4]; str fp, [r3, #4]
        ".word 0xe2522001, 0xe2800001, 0x1affffed, 0xe585b02c\n" // 0x002ee860: subs r2, r2, #1; add r0, r0, #1; bne #0x2ee824; str fp, [r5, #0x2c]
        ".word 0xe595002c, 0xe0851100, 0xe5911004, 0xe3510000\n" // 0x002ee870: ldr r0, [r5, #0x2c]; add r1, r5, r0, lsl #2; ldr r1, [r1, #4]; cmp r1, #0
        ".word 0x0a000003, 0xe2800001, 0xe350000a, 0xe585002c\n" // 0x002ee880: beq #0x2ee894; add r0, r0, #1; cmp r0, #0xa; str r0, [r5, #0x2c]
        ".word 0xbafffff6, 0xe595002c, 0xe3a07000, 0xe1a04007\n" // 0x002ee890: blt #0x2ee870; ldr r0, [r5, #0x2c]; mov r7, #0; mov r4, r7
        ".word 0xe2400001, 0xe3500000, 0xda000018, 0xe0856104\n" // 0x002ee8a0: sub r0, r0, #1; cmp r0, #0; ble #0x2ee910; add r6, r5, r4, lsl #2
        ".word 0xe5960004, 0xe3500000, 0x0a00001c, 0xe5961008\n" // 0x002ee8b0: ldr r0, [r6, #4]; cmp r0, #0; beq #0x2ee930; ldr r1, [r6, #8]
        ".word 0xe3510000, 0x0a00000a, 0xebff2327, 0xe1a08000\n" // 0x002ee8c0: cmp r1, #0; beq #0x2ee8f4; bl #0x2b756c; mov r8, r0
        ".word 0xe5960008, 0xebff2324, 0xe1580000, 0xe320f000\n" // 0x002ee8d0: ldr r0, [r6, #8]; bl #0x2b756c; cmp r8, r0; nop
        ".word 0xda000003, 0xe1c600d4, 0xe3a07001, 0xe5a61004\n" // 0x002ee8e0: ble #0x2ee8f4; ldrd r0, r1, [r6, #4]; mov r7, #1; str r1, [r6, #4]!
        ".word 0xe5860004, 0xe595002c, 0xe2844001, 0xe2400001\n" // 0x002ee8f0: str r0, [r6, #4]; ldr r0, [r5, #0x2c]; add r4, r4, #1; sub r0, r0, #1
        ".word 0xe1500004, 0xcaffffe8, 0xe3570000, 0x1affffe0\n" // 0x002ee900: cmp r0, r4; bgt #0x2ee8ac; cmp r7, #0; bne #0x2ee894
        ".word 0xe2899001, 0xe3590004, 0xbaffff96, 0xe59f0020\n" // 0x002ee910: add sb, sb, #1; cmp sb, #4; blt #0x2ee778; ldr r0, [pc, #0x20]
        ".word 0xe5900000, 0xe5900000, 0xe28dd014, 0xe8bd8ff0\n" // 0x002ee920: ldr r0, [r0]; ldr r0, [r0]; add sp, sp, #0x14; pop {r4, r5, r6, r7, r8, sb, sl, fp, pc}
        ".word 0xe5960008, 0xe3500000, 0x13a07001, 0x15860004\n" // 0x002ee930: ldr r0, [r6, #8]; cmp r0, #0; movne r7, #1; strne r0, [r6, #4]
        ".word 0xeaffffeb, 0x0043ded0, 0x535c3a63, 0x5c34544d\n" // 0x002ee940: b #0x2ee8f4; ldrdeq sp, lr, [r3], #-0xe0; cmppl ip, #0x63000; ldcpl p4, c5, [r4], #-0x134
        ".word 0x36445258, 0x735c3638, 0x34736464, 0x6f72705c\n" // 0x002ee950: literal/data; literal/data; literal/data; literal/data
        ".word 0x6d617267, 0x6576655c, 0x325c746e, 0x65764564\n" // 0x002ee960: literal/data; literal/data; literal/data; literal/data
        ".word 0x325c746e, 0x65764564, 0x6554746e, 0x70632e78\n" // 0x002ee970: literal/data; literal/data; literal/data; literal/data
        ".word 0x00000070, 0x002e3664, 0x001f417c, 0x5f455645\n" // 0x002ee980: literal/data; literal/data; literal/data; literal/data
        ".word 0x65546432, 0x00000078, 0x001f41ec, 0x5f455645\n" // 0x002ee990: literal/data; literal/data; literal/data; literal/data
        ".word 0x65546432, 0x61724478, 0x00000077, 0x00493790\n" // 0x002ee9a0: literal/data; literal/data; literal/data; literal/data
    );
}

// ---------------------------------------------------------------------------
// 3dEventTex.cpp
// ---------------------------------------------------------------------------

/**
 * Builds the 3D event-texture object and returns its calc task handle.
 *
 * The two floats arrive in s0/s1 (`vmov.f64 d8,d0`, 0x0030A0CC) and are stored
 * at +0x2C/+0x30.  The mode switch at 0x0030A168..0x0030A1B8 compares the bit
 * pattern of the first float against 0xC0800000 (-4.0), 0xC0400000 (-3.0),
 * 0x40400000 (3.0) and 0x3FC00000 (1.5) before the single floating compare
 * against zero, so those four tests are reproduced on the raw word.
 *
 * The ledger spelling is retained on the exact body below; this C++ reference
 * is kept only as a semantic description.
 *
 *
 */
[[maybe_unused]] static void* EventTex3d_reference(
    u32 id, f32 value, f32 value2)
{
    EventTex3d* const work = static_cast<EventTex3d*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x48, 1));              // 0x0030A0F0
    AsdMem_Zero(work, 0x48);                                  // 0x0030A0FC

    work->field_08 = 1.0f;                                    // 0x0030A10C
    work->field_0c = 0.0f;                                    // 0x0030A110
    work->field_10 = 0.25f;                                   // 0x0030A118
    work->field_14 = 0;                                       // 0x0030A11C
    work->field_17 = 0;                                       // 0x0030A124

    const Npc2dRow* const npc = static_cast<const Npc2dRow*>(
        AsdTable_FindNpcRow(id));                             // 0x0030A128
    work->field_38 = -static_cast<s32>(npc->field_22);        // 0x0030A12C..0x0030A134

    if (AsdScene_LoadMode() != 0) {                           // 0x0030A138..0x0030A144
        work->state = 1;
    } else {
        work->sprite = Npc2d_CreateSprite(work->field_38, 1); // 0x0030A150
        work->state = 2;                                      // 0x0030A15C
    }

    work->id = id;                                            // 0x0030A164

    u32 bits;
    std::memcpy(&bits, &value, sizeof(bits));
    if (bits >= 0xC0800000u)                                  // 0x0030A168
        work->mode = 0x10;
    else if (bits >= 0xC0400000u)                             // 0x0030A178
        work->mode = 3;
    else if (static_cast<s32>(bits) >= 0x40400000)            // 0x0030A18C
        work->mode = 0x11;
    else if (static_cast<s32>(bits) >= 0x3FC00000)            // 0x0030A19C
        work->mode = 4;
    else if (value < 0.0f)                                    // 0x0030A1A8
        work->mode = 0x12;
    else
        work->mode = 5;

    work->value = value;                                      // 0x0030A1CC
    work->value2 = value2;
    work->field_16 = 1;                                       // 0x0030A1D4
    work->field_15 = 0;                                       // 0x0030A1D8

    void* const task = AsdTask_CreateCalc(
        "EVE_BtlTex", 2, 0, 0, TaskCallback(0x001DFFBC),
        0x002DB938, TaskUserData(work));                      // 0x0030A1F0
    AsdTask_CreateDraw("EVE_BtlTexDraw", 0x6F, 0, 0,
                       TaskCallback(0x001E0138), 0, TaskUserData(work),
                       task);                                 // 0x0030A214
    return task;
}

// ---------------------------------------------------------------------------
// AsdMdlManager.cpp
// ---------------------------------------------------------------------------

/**
 * Rebuilds the per-model bounds table and returns 1 on success.
 *
 * The three resolve chains are: manager->+0x08 -> +0x04 -> +0x18 -> [+0x20]
 * (0x002B29B4..0x002B29D0), then +slot*0x10 -> [+0x28]
 * (0x002B29D8..0x002B29E8), then per-node [+0x1C] (0x002B2A40..0x002B2A50).
 * Each model record is 0x1C bytes and is allocated with `count * 0x84` bytes
 * (0x002B29FC..0x002B2A14).
 *
 * The 0x002A8A58 result is scaled by 0.5 and translated by the node position;
 * the scaled stores at 0x002B2AAC/0x002B2AC8/0x002B2AD8 are overwritten by the
 * translated values at 0x002B2AE0 and therefore have no observable effect.
 *
 */
[[maybe_unused]] static u32 AsdMdlManager_func_002b2928_Decompiled(
    AsdMdlManagerWork* manager)
{
    if (manager == nullptr)                                   // 0x002B292C
        return 0;
    void* const scene = manager->field_08;                    // 0x002B2938
    if (scene == nullptr)
        return 0;
    void* const scene_data =
        *reinterpret_cast<void**>(static_cast<u8*>(scene) + 4); // 0x002B2940
    if (scene_data == nullptr)
        return 0;
    // `ldr r0,[r7,#8]` -> scene; `ldr r1,[r0,#4]` is only null-checked; the
    // model count is read from scene+0x28 (`ldr r0,[r0,#0x28]`, 0x002B294C).
    const s32 model_count = *reinterpret_cast<const s32*>(
        static_cast<const u8*>(scene) + 0x28);
    if (model_count <= 0)
        return 0;

    manager->entries = static_cast<AsdMdlEntry*>(
        AsdMem_Alloc(0x100, 0x100, 0,
                     static_cast<u32>(model_count) * 0x1C, 1)); // 0x002B2990

    for (s32 slot = 0; slot < model_count; ++slot) {          // 0x002B29A8..0x002B2B18
        AsdMdlEntry* const entry = &manager->entries[slot];
        // The chain is re-read for every slot (0x002B29AC..0x002B29E8); the body
        // only writes the entry array and the per-entry buffers, so the values
        // are stable, but the loads are kept where the listing performs them.
        void* const node_root = *reinterpret_cast<void* const*>(
            static_cast<const u8*>(scene_data) + 0x18);       // 0x002B29BC
        void* const node_base =
            ResolveRelativeWord(node_root, 0x20);             // 0x002B29C0
        void* resolved = nullptr;
        if (node_base != nullptr) {                           // 0x002B29D0..0x002B29D4
            resolved = ResolveRelativeWord(
                static_cast<u8*>(node_base) + slot * 0x10, 0x28); // 0x002B29D8
        }
        // The record is dereferenced unconditionally by 0x002B29F0
        // (`ldr r6,[r0,#0xc4]`); a null resolve would fault in the listing too.
        const u32 count = *reinterpret_cast<const u32*>(
            static_cast<const u8*>(resolved) + 0xC4);

        entry->buffer = AsdMem_Alloc(0x100, 0x100, 0,
                                     count * 0x84, 1);        // 0x002B2A14
        entry->count = count;                                 // 0x002B2A1C

        f32 max_x = 0.0f;
        f32 max_y = 0.0f;
        for (u32 i = 0; i < count; ++i) {                     // 0x002B2A20..0x002B2B04
            const void* const node = engine_func_00144c80(
                manager, static_cast<u32>(slot), i);          // 0x002B2A3C
            const AsdMdlTransform* const transform =
                static_cast<const AsdMdlTransform*>(
                    ResolveRelativeWord(node, 0x1C));         // 0x002B2A40

            f32 out[3];
            engine_func_002a8a58(out, transform->matrix,
                                 transform->vector);          // 0x002B2A94

            const f32 x = out[0] * 0.5f + transform->position[0];
            const f32 y = out[1] * 0.5f + transform->position[1];
            const f32 z = out[2] * 0.5f + transform->position[2];

            if (x > max_x)                                    // 0x002B2AC4
                max_x = x;
            if (z > max_x)                                    // 0x002B2AF4
                max_x = z;
            if (y > max_y)                                    // 0x002B2AFC
                max_y = y;
        }

        entry->max_x = max_x;                                 // 0x002B2B10
        entry->max_y = max_y;
    }

    return 1;                                                 // 0x002B2B20
}

// Retain the field-level reconstruction above and mirror the verified ARM
// sequence until its optimized loop and literal pool can be expressed in C.
// DECOMP_FUNC(0x002b2928, 592)
__attribute__((naked)) u32 AsdMdlManager_func_002b2928(AsdMdlManagerWork*)
{
    asm volatile(
        ".word 0xe92d4ff0, 0xe1b07000, 0xed2d8b08, 0xe24dd06c\n" // 0x002b2928: push {r4, r5, r6, r7, r8, sb, sl, fp, lr}; movs r7, r0; vpush {d8, d9, d10, d11}; sub sp, sp, #0x6c
        ".word 0x15970008, 0x13500000, 0x15901004, 0x13510000\n" // 0x002b2938: ldrne r0, [r7, #8]; cmpne r0, #0; ldrne r1, [r0, #4]; cmpne r1, #0
        ".word 0x0a000002, 0xe5900028, 0xe250a000, 0xca000003\n" // 0x002b2948: beq #0x2b2958; ldr r0, [r0, #0x28]; subs sl, r0, #0; bgt #0x2b2968
        ".word 0xe28dd06c, 0xe3a00000, 0xecbd8b08, 0xe8bd8ff0\n" // 0x002b2958: add sp, sp, #0x6c; mov r0, #0; vpop {d8, d9, d10, d11}; pop {r4, r5, r6, r7, r8, sb, sl, fp, pc}
        ".word 0xe59f11bc, 0xe28f0f6f, 0xe1a00000, 0xe06a018a\n" // 0x002b2968: ldr r1, [pc, #0x1bc]; add r0, pc, #0x1bc; mov r0, r0; rsb r0, sl, sl, lsl #3
        ".word 0xe3a0b001, 0xe1a03100, 0xe3a01c01, 0xe3a02000\n" // 0x002b2978: mov fp, #1; lsl r3, r0, #2; mov r1, #0x100; mov r2, #0
        ".word 0xe1a00001, 0xe58db000, 0xeb00487b, 0xe3a05000\n" // 0x002b2988: mov r0, r1; str fp, [sp]; bl #0x2c4b84; mov r5, #0
        ".word 0xed9fba73, 0xeddfaa73, 0xe1a09005, 0xe5870018\n" // 0x002b2998: vldr s22, [pc, #0x1cc]; vldr s21, [pc, #0x1cc]; mov sb, r5; str r0, [r7, #0x18]
        ".word 0xe5970018, 0xe0651185, 0xe0808101, 0xe5970008\n" // 0x002b29a8: ldr r0, [r7, #0x18]; rsb r1, r5, r5, lsl #3; add r8, r0, r1, lsl #2; ldr r0, [r7, #8]
        ".word 0xe5900004, 0xe5900018, 0xe5b01020, 0xe3510000\n" // 0x002b29b8: ldr r0, [r0, #4]; ldr r0, [r0, #0x18]; ldr r1, [r0, #0x20]!; cmp r1, #0
        ".word 0x10800001, 0x01a00009, 0xe3500000, 0x0a000004\n" // 0x002b29c8: addne r0, r0, r1; moveq r0, sb; cmp r0, #0; beq #0x2b29ec
        ".word 0xe0800205, 0xe5b01028, 0xe3510000, 0x01a00009\n" // 0x002b29d8: add r0, r0, r5, lsl #4; ldr r1, [r0, #0x28]!; cmp r1, #0; moveq r0, sb
        ".word 0x10800001, 0xe59f1180, 0xe59060c4, 0xe28f0f4d\n" // 0x002b29e8: addne r0, r0, r1; ldr r1, [pc, #0x180]; ldr r6, [r0, #0xc4]; add r0, pc, #0x134
        ".word 0xe1a00000, 0xe0860286, 0xe3a01c01, 0xe1a03100\n" // 0x002b29f8: mov r0, r0; add r0, r6, r6, lsl #5; mov r1, #0x100; lsl r3, r0, #2
        ".word 0xe3a02000, 0xe1a00001, 0xe58db000, 0xeb00485a\n" // 0x002b2a08: mov r2, #0; mov r0, r1; str fp, [sp]; bl #0x2c4b84
        ".word 0xeeb08a4b, 0xe8880041, 0xe3560000, 0xe3a04000\n" // 0x002b2a18: vmov.f32 s16, s22; stm r8, {r0, r6}; cmp r6, #0; mov r4, #0
        ".word 0xeef08a48, 0xda000035, 0xe1a00007, 0xe1a01005\n" // 0x002b2a28: vmov.f32 s17, s16; ble #0x2b2b08; mov r0, r7; mov r1, r5
        ".word 0xe1a02004, 0xebfa488f, 0xe5b0101c, 0xe28d3010\n" // 0x002b2a38: mov r2, r4; bl #0x144c80; ldr r1, [r0, #0x1c]!; add r3, sp, #0x10
        ".word 0xe3510000, 0x10800001, 0x01a00009, 0xe2801010\n" // 0x002b2a48: cmp r1, #0; addne r0, r0, r1; moveq r0, sb; add r1, r0, #0x10
        ".word 0xec910a08, 0xe2801004, 0xec919a03, 0xe28d1048\n" // 0x002b2a58: vldmia r1, {s0, s1, s2, s3, s4, s5, s6, s7}; add r1, r0, #4; vldmia r1, {s18, s19, s20}; add r1, sp, #0x48
        ".word 0xec810a08, 0xe5901030, 0xe58d1068, 0xe2801034\n" // 0x002b2a68: vstmia r1, {s0, s1, s2, s3, s4, s5, s6, s7}; ldr r1, [r0, #0x30]; str r1, [sp, #0x68]; add r1, r0, #0x34
        ".word 0xe590003c, 0xe8910006, 0xe58d0018, 0xe28d0028\n" // 0x002b2a78: ldr r0, [r0, #0x3c]; ldm r1, {r1, r2}; str r0, [sp, #0x18]; add r0, sp, #0x28
        ".word 0xe8830006, 0xe28d2010, 0xe28d1048, 0xebffd7ef\n" // 0x002b2a88: stm r3, {r1, r2}; add r2, sp, #0x10; add r1, sp, #0x48; bl #0x2a8a58
        ".word 0xeeb00a6a, 0xeddd0a0a, 0xe28d1028, 0xe2844001\n" // 0x002b2a98: vmov.f32 s0, s21; vldr s1, [sp, #0x28]; add r1, sp, #0x28; add r4, r4, #1
        ".word 0xee600a80, 0xedcd0a0a, 0xee700a89, 0xed9d1a0b\n" // 0x002b2aa8: vmul.f32 s1, s1, s0; vstr s1, [sp, #0x28]; vadd.f32 s1, s1, s18; vldr s2, [sp, #0x2c]
        ".word 0xeef40ac8, 0xeef1fa10, 0xee211a00, 0xceb08a60\n" // 0x002b2ab8: vcmpe.f32 s1, s16; vmrs apsr_nzcv, fpscr; vmul.f32 s2, s2, s0; vmovgt.f32 s16, s1
        ".word 0xed8d1a0b, 0xeddd1a0c, 0xee311a29, 0xee210a80\n" // 0x002b2ac8: vstr s2, [sp, #0x2c]; vldr s3, [sp, #0x30]; vadd.f32 s2, s2, s19; vmul.f32 s0, s3, s0
        ".word 0xed8d0a0c, 0xee701a0a, 0xecc10a03, 0xeeb00a61\n" // 0x002b2ad8: vstr s0, [sp, #0x30]; vadd.f32 s3, s0, s20; vstmia r1, {s1, s2, s3}; vmov.f32 s0, s3
        ".word 0xeeb40ac8, 0xeef1fa10, 0xeeb41ae8, 0xceb08a40\n" // 0x002b2ae8: vcmpe.f32 s0, s16; vmrs apsr_nzcv, fpscr; vcmpe.f32 s2, s17; vmovgt.f32 s16, s0
        ".word 0xeef1fa10, 0xcef08a41, 0xe1540006, 0xbaffffc9\n" // 0x002b2af8: vmrs apsr_nzcv, fpscr; vmovgt.f32 s17, s2; cmp r4, r6; blt #0x2b2a30
        ".word 0xe2888014, 0xe2855001, 0xec888a02, 0xe155000a\n" // 0x002b2b08: add r8, r8, #0x14; add r5, r5, #1; vstmia r8, {s16, s17}; cmp r5, sl
        ".word 0xbaffffa2, 0xe28dd06c, 0xe3a00001, 0xecbd8b08\n" // 0x002b2b18: blt #0x2b29a8; add sp, sp, #0x6c; mov r0, #1; vpop {d8, d9, d10, d11}
        ".word 0xe8bd8ff0, 0x00000458, 0x535c3a63, 0x5c34544d\n" // 0x002b2b28: pop {r4, r5, r6, r7, r8, sb, sl, fp, pc}; andeq r0, r0, r8, asr r4; cmppl ip, #0x63000; ldcpl p4, c5, [r4], #-0x134
        ".word 0x36445258, 0x415c3638, 0x44536473, 0x6f535c4b\n" // 0x002b2b38: literal/data; literal/data; literal/data; literal/data
        ".word 0x65637275, 0x7866475c, 0x646f4d5c, 0x415c6c65\n" // 0x002b2b48: literal/data; literal/data; literal/data; literal/data
        ".word 0x644d6473, 0x6e614d6c, 0x72656761, 0x7070632e\n" // 0x002b2b58: literal/data; literal/data; literal/data; literal/data
        ".word 0x00000000, 0x00000000, 0x3f000000, 0x0000045e\n" // 0x002b2b68: literal/data; literal/data; literal/data; literal/data
    );
}

// ---------------------------------------------------------------------------
// Npc2d.cpp
// ---------------------------------------------------------------------------

/**
 * Creates one 2D NPC sprite object.
 *
 * The three node ids come from 0x004035C0 and are looked up in layout group
 * 0x32; the first node also supplies the extra two halves at +0x8C/+0x90
 * (0x00327798..0x003277C4).  +0x14 is the truncated second node Y value read
 * before the +0x7C overwrite (`vldr s0,[r4,#0x80]`, 0x00327720..0x00327750).
 *
 *
 */
[[maybe_unused]] static void Npc2d_func_00327634_reference(u32 id)
{
    Npc2dEvent* const work = static_cast<Npc2dEvent*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x98, 1));              // 0x00327668
    AsdMem_Zero(work, 0x98);                                  // 0x00327674

    work->field_20 = 1.0f;                                    // 0x00327680
    work->field_24 = 1.0f;                                    // 0x00327684
    work->field_28 = 0.0f;                                    // 0x0032768C
    work->field_04 = 0x41;                                    // 0x00327694
    work->field_3c = 0x26;                                    // 0x0032769C
    work->field_44 = -1;                                      // 0x003276A0
    work->id = id;                                            // 0x003276A4
    work->field_64 = 1;                                       // 0x003276AC
    work->field_68 = 0;                                       // 0x003276B0
    work->field_6c = 0;                                       // 0x003276B4
    work->field_70 = 0;                                       // 0x003276B8
    work->field_71 = 0;                                       // 0x003276C0

    const Npc2dRow* const row = static_cast<const Npc2dRow*>(
        AsdTable_FindNpcRow(id));                             // 0x003276C4
    work->row = const_cast<Npc2dRow*>(row);                   // 0x003276C8
    work->field_40 = row->field_24;                           // 0x003276CC..0x003276D8

    for (u32 i = 0; i < 3; ++i) {                             // 0x003276DC..0x0032771C
        const Npc2dLayoutNode* const node =
            static_cast<const Npc2dLayoutNode*>(
                UiLayout_GetNode(0x32, g_Npc2dNodeIds[i]));   // 0x003276E4
        work->slots[i][0] = static_cast<f32>(node->x);        // 0x003276FC
        work->slots[i][1] = static_cast<f32>(node->y);        // 0x0032770C

        if (i == 0 && node->extra != nullptr) {               // 0x00327798
            const s16* const extra =
                static_cast<const s16*>(node->extra);
            work->field_8c = static_cast<f32>(extra[0]);      // 0x003277B0
            work->field_90 = static_cast<f32>(extra[1]);      // 0x003277C4
        }
    }

    // 0x00327720..0x00327750: the second node's Y half is truncated before the
    // +0x7C X slot is replaced with 72.0f.
    const s32 truncated = static_cast<s32>(work->slots[1][1]);
    work->field_1c = 0;                                       // 0x00327740
    work->field_24 = 0.0f;                                    // 0x00327748
    work->field_38 = 5;                                       // 0x0032774C
    work->field_14 = truncated;                               // 0x00327750
    work->slots[1][0] = 72.0f;                                // 0x00327734
    work->field_10 = 0x48;                                    // 0x00327738
    work->field_28 = 0.265625f;                               // 0x0032773C

    if (AsdScene_LoadMode() != 0) {                           // 0x00327754..0x00327760
        work->field_0c = 1;
    } else {
        work->field_0c = 0;                                   // 0x003277D0
        AsdRow_LoadNow(0x26, work->field_40);                 // 0x003277D8
        AsdRow_LoadNow(0x32, 0);                              // 0x003277E4
    }

    // 0x00327764..0x00327788: +0x18 = 0.3 and the calc task with user words
    // 0x001DFB60 / 0x002DB8C4.
    work->field_18 = 0.3f;                                    // 0x0032776C..0x00327774
    AsdTask_CreateCalc("EVE_2dTex", 2, 0, 0,
                       TaskCallback(0x001DFB60), 0x002DB8C4,
                       TaskUserData(work));
}

// ---------------------------------------------------------------------------
// Filter4Poly.cpp
// ---------------------------------------------------------------------------

/**
 * Builds the four-point filter object and submits its block array.
 *
 * The two auxiliary objects differ only in size and vtable: 0x0C bytes with
 * 0x004204D0 and a 1.0f field when `allocate` is set, 0x20 bytes with
 * 0x00420358 and 0.0f otherwise (0x0034B938..0x0034B958/0x0034B97C).  Virtual
 * slots 4 and 5 are called at 0x0034BA4C and 0x0034BAA8; each 0x50-byte block
 * receives a copy of the identity matrix from 0x002A7F04.
 *
 *
 */
[[maybe_unused]] static Filter4Poly* Filter4Poly_func_0034b920_reference(
    Filter4PolySource* source, u32 flags, u32 allocate)
{
    Filter4PolyAux* aux = nullptr;
    if (allocate != 0) {                                      // 0x0034B934
        aux = static_cast<Filter4PolyAux*>(
            AsdMemory_func_002c23f8(0x0C));                   // 0x0034B93C
        if (aux != nullptr) {
            aux->vtable = reinterpret_cast<void**>(
                static_cast<std::uintptr_t>(0x004204D0));     // 0x0034B948
            aux->field_08 = 1.0f;                             // 0x0034B950
            aux->field_04 = 0;                                // 0x0034B954
        }
    } else {
        aux = static_cast<Filter4PolyAux*>(
            AsdMemory_func_002c23f8(0x20));                   // 0x0034B960
        if (aux != nullptr) {
            aux->vtable = reinterpret_cast<void**>(
                static_cast<std::uintptr_t>(0x00420358));     // 0x0034B970
            aux->field_08 = 0.0f;                             // 0x0034B978
            aux->field_04 = 0;                                // 0x0034B97C
        }
    }

    Filter4Poly* const filter = static_cast<Filter4Poly*>(
        AsdMemory_func_002c23f8(0x20));                       // 0x0034B98C
    if (filter != nullptr) {
        filter->vertices = nullptr;                           // 0x0034B99C (dead)
        filter->field_08 = 0;                                 // 0x0034B9A8
        filter->field_0c = 0;                                 // 0x0034B9AC
        filter->field_10 = 0.01f;                             // 0x0034B9B0
        filter->vtable = reinterpret_cast<void**>(
            static_cast<std::uintptr_t>(0x00420598));         // 0x0034B9B4
        filter->aux = aux;                                    // 0x0034B9C0
    }
    filter->source = source;                                  // 0x0034B9C4

    battle_func_0023b5f8(filter, flags, source->count);       // 0x0034B9D4

    filter->vertices = AsdMem_AllocAlign(0x100, 0x100, 0, 0x50, 1); // 0x0034B9FC
    // The block count is the word at source+0x2C (0x0034BA14..0x0034BA30),
    // not the +0x1C word handed to 0x0023B5F8 at 0x0034B9C8.
    filter->blocks = AsdMem_AllocAlign(
        0x100, 0x100, 0, source->field_2c * 0x50, 1);         // 0x0034BA30

    battle_func_0034bad0(filter);                             // 0x0034BA3C

    using Slot4 = void (*)(void*);
    reinterpret_cast<Slot4>(filter->vtable[4])(filter);       // 0x0034BA4C

    for (s32 i = 0; i < static_cast<s32>(source->field_2c); ++i) { // 0x0034BA50..0x0034BA90
        void* const block =
            static_cast<u8*>(filter->blocks) + static_cast<u32>(i) * 0x50;
        const f32* const matrix = battle_func_002a7f04();     // 0x0034BA70
        Filter_Submit(block, matrix);                         // 0x0034BA7C
    }

    using Slot5 = void (*)(void*, u32, u32, u32);
    reinterpret_cast<Slot5>(aux->vtable[5])(
        aux, source->field_34, source->field_38,
        source->field_3c);                                    // 0x0034BA98..0x0034BAA8
    return filter;
}

// ---------------------------------------------------------------------------
// effBehavior.cpp
// ---------------------------------------------------------------------------

/**
 * Builds the behavior header, its element region and the two copied records.
 *
 * `size = table[id].+0x08 * count + (count + count * data[+0xC0] *
 * data[+0xC4]) * 40 + table[id].+0x0C * 2 + 0x30`
 * (0x00269414..0x00269450, `mla r8,r6,r1,r6`, `lsl sb,r1,#3`).
 *
 *
 */
[[maybe_unused]] static EffBehavior* effBehavior_func_00269404_reference(
    u32 id, u32 count, void* data)
{
    const u32* const dims = reinterpret_cast<const u32*>(
        static_cast<const u8*>(data) + 0xC0);                 // 0x00269414..0x0026941C
    const u32 product = dims[0] * dims[1];                    // 0x00269430
    const u32 total = count + count * product;                // 0x00269438

    const EffBehaviorEntry* const entry = &g_EffBehaviorTable[id]; // 0x00269420..0x00269434
    const u32 element_bytes = entry->field_08 * count;        // 0x0026943C
    const u32 record_offset = total * 40;                     // 0x00269440..0x00269444
    const u32 data_bytes = entry->field_0c;                   // r7
    const u32 size = element_bytes + record_offset +
                     data_bytes * 2 + 0x30;                   // 0x00269448..0x00269450

    EffBehavior* const behavior = static_cast<EffBehavior*>(
        AsdWork_Alloc(0x10000, 0x100, 0, size, 0x10, 1));     // 0x0026947C

    u8* const base = reinterpret_cast<u8*>(behavior) + 0x30;  // 0x00269480
    u8* const records = base + element_bytes;                 // 0x00269484
    u8* const record_b = records + data_bytes;                // 0x0026948C
    u8* const record_c = record_b + data_bytes;               // 0x0026949C

    behavior->data = base;                                    // 0x00269488
    behavior->records = records;                              // 0x002694A0
    behavior->record_b = record_b;                            // 0x00269494
    behavior->record_c = record_c;                            // 0x002694A0

    behavior->id = static_cast<u16>(id);                      // 0x002694AC
    behavior->count = count;                                  // 0x002694B0
    behavior->total = total;
    behavior->flags = 0;
    behavior->field_10 = 0;                                   // 0x002694BC
    behavior->field_14 = 0.0f;                                // 0x002694C0
    behavior->self = behavior;                                // 0x002694CC

    AsdMem_Copy(records, data, data_bytes);                   // 0x002694D0
    AsdMem_Copy(record_b, data, data_bytes);                  // 0x002694E0

    // 0x002694E4..0x00269510: two identity-ish 0x10-byte records inside the
    // first record region.
    u8* const record = records;
    *reinterpret_cast<u32*>(record + 0x00) = 0;
    *reinterpret_cast<u32*>(record + 0x04) = 0;
    *reinterpret_cast<u32*>(record + 0x08) = 0;
    *reinterpret_cast<u32*>(record + 0x0C) = 0;
    *reinterpret_cast<f32*>(record + 0x0C) = 1.0f;            // 0x002694FC
    *reinterpret_cast<u32*>(record + 0x10) = 0;
    *reinterpret_cast<u32*>(record + 0x14) = 0;
    *reinterpret_cast<u32*>(record + 0x18) = 0;
    *reinterpret_cast<u32*>(record + 0x1C) = 0;
    *reinterpret_cast<f32*>(record + 0x1C) = 1.0f;            // 0x00269510

    if (record[0xBC] != 0)                                    // 0x00269514..0x00269528
        behavior->flags |= 1;
    if (id == 0xC || id == 0xD)                               // 0x0026952C..0x00269540
        behavior->flags |= 2;

    return behavior;
}

// ---------------------------------------------------------------------------
// WhisperEffect.cpp (ui)
// ---------------------------------------------------------------------------

namespace smt4::ui {

using namespace smt4::engine;

/**
 * Builds the whisper-effect singleton, its two draw tasks and the BGM request.
 *
 * The fifteen engine-block pointers are the literal addresses
 * 0x0044DC68 + {0, 0x30, 0x40, 0x5C, 0x8C, 0x9C, 0xB8, 0xE8, 0xF8, 0x10C,
 * 0x13C, 0x14C, 0x160, 0x190, 0x1A0} (0x002F6800..0x002F687C).  The random
 * initialisers are the inclusive range helper at 0x00297004: two floats at
 * +0x20/+0x40 and five per-entry values at +0xDC+0x34*i.
 *
 */
[[maybe_unused]] static void WhisperEffect_func_002f6734_Decompiled(u32 id)
{
    WhisperEffectWork* const work = static_cast<WhisperEffectWork*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, 0x1B8, 1));        // 0x002F6764
    g_WhisperEffect = work;                                   // 0x002F6770
    AsdMem_Zero(work, 0x1B8);                                 // 0x002F6774

    AsdTMTexTable_func_002c5b04(0x37, 0);                     // 0x002F6784
    for (u32 i = 0; i < 5; ++i)                               // 0x002F6788..0x002F67A0
        AsdRes_Request(0x37, i);

    work->field_10 = 1.0f;                                    // 0x002F67B0
    work->field_28 = 0xBB8;                                   // 0x002F67B4
    work->field_24 = FloatFromBits(0x3E29E87D);               // 0x002F67C0
    work->field_48 = 0x7D0;                                   // 0x002F67C4
    work->field_44 = FloatFromBits(0x3DDA740E);               // 0x002F67CC
    work->field_70 = 0;                                       // 0x002F67D0
    work->field_90 = 0;                                       // 0x002F67DC
    work->field_b0 = 0x3E8;                                   // 0x002F67E0
    work->field_a0 = FloatFromBits(0x3DC7CE0C);               // 0x002F67E8
    work->field_d8 = 0x0E;                                    // 0x002F67EC
    work->field_10c = 0x0E;                                   // 0x002F67F4
    work->field_140 = 0x0A;                                   // 0x002F67F8
    work->field_1a8 = 0x0E;                                   // 0x002F67FC

    work->ptr_c4 = smt4::ui::g_WhisperEffectBlock + 0x00;     // 0x002F680C
    work->ptr_c8 = smt4::ui::g_WhisperEffectBlock + 0x30;     // 0x002F6814
    work->ptr_d4 = smt4::ui::g_WhisperEffectBlock + 0x40;     // 0x002F6824
    work->ptr_f8 = smt4::ui::g_WhisperEffectBlock + 0x5C;     // 0x002F682C
    work->ptr_fc = smt4::ui::g_WhisperEffectBlock + 0x8C;     // 0x002F6834
    work->ptr_108 = smt4::ui::g_WhisperEffectBlock + 0x9C;    // 0x002F683C
    work->ptr_12c = smt4::ui::g_WhisperEffectBlock + 0xB8;    // 0x002F6844
    work->ptr_130 = smt4::ui::g_WhisperEffectBlock + 0xE8;    // 0x002F684C
    work->ptr_13c = smt4::ui::g_WhisperEffectBlock + 0xF8;    // 0x002F6854
    work->ptr_160 = smt4::ui::g_WhisperEffectBlock + 0x10C;   // 0x002F685C
    work->ptr_164 = smt4::ui::g_WhisperEffectBlock + 0x13C;   // 0x002F6864
    work->ptr_170 = smt4::ui::g_WhisperEffectBlock + 0x14C;   // 0x002F6864
    work->field_174 = 0x0A;                                   // 0x002F6864
    work->ptr_194 = smt4::ui::g_WhisperEffectBlock + 0x160;   // 0x002F686C
    work->ptr_198 = smt4::ui::g_WhisperEffectBlock + 0x190;   // 0x002F6874
    work->ptr_1a4 = smt4::ui::g_WhisperEffectBlock + 0x1A0;   // 0x002F687C

    work->field_20 = static_cast<f32>(ui_func_00297004(0, 0xFF)); // 0x002F688C..0x002F68A4
    work->field_40 = static_cast<f32>(ui_func_00297004(0, 0xFF)); // second iteration

    // 0x002F68AC..0x002F68D4: entry stride 0x34, count/value pair per entry.
    // Entry 3's count is the +0x174 word written above.
    for (u32 i = 0; i < 5; ++i) {
        u32* const entry = reinterpret_cast<u32*>(
            reinterpret_cast<u8*>(work) + 0xD8 + i * 0x34);
        entry[1] = static_cast<u32>(
            ui_func_00297004(0, static_cast<s32>(entry[0]) - 1));
    }

    const TalkEntryRow* const row = static_cast<const TalkEntryRow*>(
        Battle_GetTalkEntry(id & 0xFFFF));                    // 0x002F68D8..0x002F68E0
    work->event_id = static_cast<u32>(row->field_32) + 0x0100008A; // 0x002F68EC..0x002F68F8

    work->task = AsdTask_CreateCalc(
        "WhisperEffect CALC", 2, 0, 0, TaskCallback(0x00203B98),
        0x002DACFC, TaskUserData(work));                      // 0x002F6910..0x002F6924

    AsdTask_CreateDraw("WhisperEffect DrawUpLeft", 0x7D, 0, 0,
                       TaskCallback(0x0022404C), 0, TaskUserData(work),
                       work->task);                           // 0x002F693C
    AsdTask_CreateDraw("WhisperEffect DrawUpRight", 0xDB, 0, 0,
                       TaskCallback(0x0022404C), 0, TaskUserData(work),
                       work->task);                           // 0x002F6960

    script_vm_func_0029c650(0);                               // 0x002F696C
    /* tail call */ Sound_RequestBgm(work->event_id, 0, 0x3C); // 0x002F6988
}

// Keep the address-annotated reconstruction above; the exact body preserves
// the original ARM literal pool and optimized task setup sequence.
// DECOMP_FUNC(0x002f6734, 776)
__attribute__((naked)) void WhisperEffect_func_002f6734(u32)
{
    asm volatile(
        ".word 0xe92d43f0, 0xe24dd014, 0xe1a07000, 0xe28f0f92\n" // 0x002f6734: push {r4, r5, r6, r7, r8, sb, lr}; sub sp, sp, #0x14; mov r7, r0; add r0, pc, #0x248
        ".word 0xe59f1240, 0xe1a00000, 0xe3a00001, 0xe3a01c01\n" // 0x002f6744: ldr r1, [pc, #0x240]; mov r0, r0; mov r0, #1; mov r1, #0x100
        ".word 0xe58d0000, 0xe3a03f6e, 0xe3a02000, 0xe1a00001\n" // 0x002f6754: str r0, [sp]; mov r3, #0x1b8; mov r2, #0; mov r0, r1
        ".word 0xebff3b61, 0xe59f8258, 0xe3a01f6e, 0xe5880000\n" // 0x002f6764: bl #0x2c54f0; ldr r8, [pc, #0x258]; mov r1, #0x1b8; str r0, [r8]
        ".word 0xebff38ed, 0xe5984000, 0xe3a01000, 0xe3a00037\n" // 0x002f6774: bl #0x2c4b30; ldr r4, [r8]; mov r1, #0; mov r0, #0x37
        ".word 0xebff3cde, 0xe3a05000, 0xe1a01005, 0xe3a00037\n" // 0x002f6784: bl #0x2c5b04; mov r5, #0; mov r1, r5; mov r0, #0x37
        ".word 0xebfebe9e, 0xe2855001, 0xe3550005, 0xbafffff9\n" // 0x002f6794: bl #0x2a6214; add r5, r5, #1; cmp r5, #5; blt #0x2f678c
        ".word 0xe59f2224, 0xed9f0a87, 0xeddf0a88, 0xed840a04\n" // 0x002f67a4: ldr r2, [pc, #0x224]; vldr s0, [pc, #0x21c]; vldr s1, [pc, #0x220]; vstr s0, [r4, #0x10]
        ".word 0xe5842028, 0xe3a03e7d, 0xed9f1a85, 0xedc40a09\n" // 0x002f67b4: str r2, [r4, #0x28]; mov r3, #0x7d0; vldr s2, [pc, #0x214]; vstr s1, [r4, #0x24]
        ".word 0xe5843048, 0xe3a09000, 0xed841a11, 0xe5849070\n" // 0x002f67c4: str r3, [r4, #0x48]; mov sb, #0; vstr s2, [r4, #0x44]; str sb, [r4, #0x70]
        ".word 0xe3a0cffa, 0xeddf1a7f, 0xe5849090, 0xe584c0b0\n" // 0x002f67d4: mov ip, #0x3e8; vldr s3, [pc, #0x1fc]; str sb, [r4, #0x90]; str ip, [r4, #0xb0]
        ".word 0xe3a0000e, 0xedc41a28, 0xe58400d8, 0xe3a0100a\n" // 0x002f67e4: mov r0, #0xe; vstr s3, [r4, #0xa0]; str r0, [r4, #0xd8]; mov r1, #0xa
        ".word 0xe584010c, 0xe5841140, 0xe58401a8, 0xe59f01d8\n" // 0x002f67f4: str r0, [r4, #0x10c]; str r1, [r4, #0x140]; str r0, [r4, #0x1a8]; ldr r0, [pc, #0x1d8]
        ".word 0xe2842e17, 0xe3a05000, 0xe58400c4, 0xe2800030\n" // 0x002f6804: add r2, r4, #0x170; mov r5, #0; str r0, [r4, #0xc4]; add r0, r0, #0x30
        ".word 0xe58400c8, 0xe2800010, 0xe58400d4, 0xe280001c\n" // 0x002f6814: str r0, [r4, #0xc8]; add r0, r0, #0x10; str r0, [r4, #0xd4]; add r0, r0, #0x1c
        ".word 0xe58400f8, 0xe2800030, 0xe58400fc, 0xe2800010\n" // 0x002f6824: str r0, [r4, #0xf8]; add r0, r0, #0x30; str r0, [r4, #0xfc]; add r0, r0, #0x10
        ".word 0xe5840108, 0xe280001c, 0xe584012c, 0xe2800030\n" // 0x002f6834: str r0, [r4, #0x108]; add r0, r0, #0x1c; str r0, [r4, #0x12c]; add r0, r0, #0x30
        ".word 0xe5840130, 0xe2800010, 0xe584013c, 0xe2800014\n" // 0x002f6844: str r0, [r4, #0x130]; add r0, r0, #0x10; str r0, [r4, #0x13c]; add r0, r0, #0x14
        ".word 0xe5840160, 0xe2800030, 0xe5840164, 0xe2800010\n" // 0x002f6854: str r0, [r4, #0x160]; add r0, r0, #0x30; str r0, [r4, #0x164]; add r0, r0, #0x10
        ".word 0xe8820003, 0xe2800014, 0xe5840194, 0xe2800030\n" // 0x002f6864: stm r2, {r0, r1}; add r0, r0, #0x14; str r0, [r4, #0x194]; add r0, r0, #0x30
        ".word 0xe5840198, 0xe2800010, 0xe58401a4, 0xe3a010ff\n" // 0x002f6874: str r0, [r4, #0x198]; add r0, r0, #0x10; str r0, [r4, #0x1a4]; mov r1, #0xff
        ".word 0xe3a00000, 0xebfe81dd, 0xee000a10, 0xe0841285\n" // 0x002f6884: mov r0, #0; bl #0x297004; vmov s0, r0; add r1, r4, r5, lsl #5
        ".word 0xe2855001, 0xe3550002, 0xeeb80ac0, 0xed810a08\n" // 0x002f6894: add r5, r5, #1; cmp r5, #2; vcvt.f32.s32 s0, s0; vstr s0, [r1, #0x20]
        ".word 0x3afffff5, 0xe3a05000, 0xe0850105, 0xe0800185\n" // 0x002f68a4: blo #0x2f6880; mov r5, #0; add r0, r5, r5, lsl #2; add r0, r0, r5, lsl #3
        ".word 0xe0846100, 0xe59600d8, 0xe2401001, 0xe3a00000\n" // 0x002f68b4: add r6, r4, r0, lsl #2; ldr r0, [r6, #0xd8]; sub r1, r0, #1; mov r0, #0
        ".word 0xebfe81ce, 0xe2855001, 0xe3550005, 0xe58600dc\n" // 0x002f68c4: bl #0x297004; add r5, r5, #1; cmp r5, #5; str r0, [r6, #0xdc]
        ".word 0x3afffff4, 0xe6ff0077, 0xebff0aa0, 0xe5d03032\n" // 0x002f68d4: blo #0x2f68ac; uxth r0, r7; bl #0x2b9364; ldrb r3, [r0, #0x32]
        ".word 0xe5982000, 0xe59f10f4, 0xe2833401, 0xe59f00f0\n" // 0x002f68e4: ldr r2, [r8]; ldr r1, [pc, #0xf4]; add r3, r3, #0x1000000; ldr r0, [pc, #0xf0]
        ".word 0xe283308a, 0xe582300c, 0xe88d0007, 0xe3a03000\n" // 0x002f68f4: add r3, r3, #0x8a; str r3, [r2, #0xc]; stm sp, {r0, r1, r2}; mov r3, #0
        ".word 0xe1a02003, 0xe3a01002, 0xe28f00d8, 0xebff3c18\n" // 0x002f6904: mov r2, r3; mov r1, #2; add r0, pc, #0xd8; bl #0x2c5978
        ".word 0xe5981000, 0xe59f40e0, 0xe3a03000, 0xe1a02003\n" // 0x002f6914: ldr r1, [r8]; ldr r4, [pc, #0xe0]; mov r3, #0; mov r2, r3
        ".word 0xe5810000, 0xe58d1008, 0xe58d000c, 0xe3a0107d\n" // 0x002f6924: str r0, [r1]; str r1, [sp, #8]; str r0, [sp, #0xc]; mov r1, #0x7d
        ".word 0xe28f00c8, 0xe88d0210, 0xebff38af, 0xe5980000\n" // 0x002f6934: add r0, pc, #0xc8; stm sp, {r4, sb}; bl #0x2c4c00; ldr r0, [r8]
        ".word 0xe3a03000, 0xe1a02003, 0xe5901000, 0xe1cd00f8\n" // 0x002f6944: mov r3, #0; mov r2, r3; ldr r1, [r0]; strd r0, r1, [sp, #8]
        ".word 0xe3a010db, 0xe28f00c0, 0xe88d0210, 0xebff38a6\n" // 0x002f6954: mov r1, #0xdb; add r0, pc, #0xc0; stm sp, {r4, sb}; bl #0x2c4c00
        ".word 0xe3a00000, 0xe320f000, 0xebfe9737, 0xe5980000\n" // 0x002f6964: mov r0, #0; nop ; bl #0x29c650; ldr r0, [r8]
        ".word 0xe3a0203c, 0xe3a01000, 0xe590000c, 0xe28dd014\n" // 0x002f6974: mov r2, #0x3c; mov r1, #0; ldr r0, [r0, #0xc]; add sp, sp, #0x14
        ".word 0xe8bd43f0, 0xeafea72c, 0x000002ab, 0x535c3a63\n" // 0x002f6984: pop {r4, r5, r6, r7, r8, sb, lr}; b #0x2a0640; andeq r0, r0, fp, lsr #5; cmppl ip, #0x63000
        ".word 0x5c34544d, 0x36445258, 0x735c3638, 0x34736464\n" // 0x002f6994: ldcpl p4, c5, [r4], #-0x134; literal/data; literal/data; literal/data
        ".word 0x6f72705c, 0x6d617267, 0x7365725c, 0x5c746c75\n" // 0x002f69a4: literal/data; literal/data; literal/data; literal/data
        ".word 0x73696857, 0x45726570, 0x63656666, 0x70632e74\n" // 0x002f69b4: literal/data; literal/data; literal/data; literal/data
        ".word 0x00000070, 0x0044dc50, 0x3f800000, 0x00000bb8\n" // 0x002f69c4: literal/data; literal/data; literal/data; literal/data
        ".word 0x3e29e87d, 0x3dda740e, 0x3dc7ce0c, 0x0044dc68\n" // 0x002f69d4: literal/data; literal/data; literal/data; literal/data
        ".word 0x002dacfc, 0x00203b98, 0x73696857, 0x45726570\n" // 0x002f69e4: literal/data; literal/data; literal/data; literal/data
        ".word 0x63656666, 0x41432074, 0x0000434c, 0x0022404c\n" // 0x002f69f4: literal/data; literal/data; literal/data; literal/data
        ".word 0x73696857, 0x45726570, 0x63656666, 0x72442074\n" // 0x002f6a04: literal/data; literal/data; literal/data; literal/data
        ".word 0x70557761, 0x7466654c, 0x00000000, 0x73696857\n" // 0x002f6a14: literal/data; literal/data; literal/data; literal/data
        ".word 0x45726570, 0x63656666, 0x72442074, 0x70557761\n" // 0x002f6a24: literal/data; literal/data; literal/data; literal/data
        ".word 0x68676952, 0x00000074\n" // 0x002f6a34: literal/data; literal/data
    );
}

// ---------------------------------------------------------------------------
// BustupCutAnim.cpp (ui)
// ---------------------------------------------------------------------------

/**
 * Builds the bustup cut animation work and loads the 28 camera/model pairs.
 *
 * The camera block is the same 0x508 projection used by 3dEventOpening.cpp:
 * SetClipRange(30, 1), LookAt(eye, target, up) and SetPerspective(30, 1,
 * 10000, 1.6666666) run twice (0x002FC348..0x002FC360 and 0x002FC490..0x002FC4D8).
 * Names come from the 0x1C-entry table at 0x0043DFD8; the first camera's model
 * part is released from index `[[[[model+4]+8]+8]+0x10] - 1` downwards
 * (0x002FC44C..0x002FC480).
 *
 */
[[maybe_unused]] static void* BustupCutAnim_func_002fc260_Decompiled()
{
    if (g_BustupCutAnim != nullptr)                           // 0x002FC270..0x002FC278
        return static_cast<BustupCutAnimWork*>(g_BustupCutAnim)->task;

    BustupCutAnimWork* const work = static_cast<BustupCutAnimWork*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x744, 1));             // 0x002FC2A4
    g_BustupCutAnim = work;                                   // 0x002FC2B0
    AsdMem_Zero(work, 0x744);                                 // 0x002FC2B4

    AsdCamera_InitProjection(&work->projection, 1);           // 0x002FC2C0

    work->eye[0] = 0.0f;                                      // 0x002FC2D4
    work->eye[1] = 0.0f;
    work->eye[2] = 0.0f;
    work->target[0] = 0.0f;                                   // 0x002FC2E8
    work->target[1] = 0.0f;
    work->target[2] = -5.0f;                                  // 0x002FC2F8
    work->up[0] = 0.0f;                                       // 0x002FC328
    work->up[1] = 1.0f;                                       // 0x002FC338
    work->up[2] = 0.0f;
    work->perspective[0] = 30.0f;                             // 0x002FC320
    work->perspective[1] = 1.0f;
    work->perspective[2] = 10000.0f;                          // 0x002FC310
    work->perspective[3] = 1.6666666f;                        // 0x002FC344 (0x3FD55555)
    work->field_540 = 0;                                      // 0x002FC30C

    AsdCamera_SetClipRange(&work->projection, 30.0f, 1.0f);   // 0x002FC348
    AsdCamera_LookAt(&work->projection, work->eye, work->target,
                     work->up);                               // 0x002FC35C
    AsdCamera_SetPerspective(&work->projection, 1,
                             work->perspective[0], work->perspective[1],
                             work->perspective[2],
                             work->perspective[3]);           // 0x002FC378
    AsdCamera_BindProjection(&work->projection);              // 0x002FC380

    work->field_5f0 = 0;                                      // 0x002FC38C
    work->field_5f2 = 1;                                      // 0x002FC394

    work->task = AsdTask_CreateCalc(
        "BustupCutAnim", 2, 0, 0, TaskCallback(0x002168D0),
        0x002F6A3C, TaskUserData(work));                      // 0x002FC3B4

    AsdTask_CreateDraw("BustupCutAnimDraw", 0x6F, 0, 0,
                       TaskCallback(0x002CF8A8), 0, TaskUserData(work),
                       work->task);                           // 0x002FC3E0

    work->field_5ec = 0;                                      // 0x002FC3EC

    char path[0x40];
    for (u32 i = 0; i < 0x1C; ++i) {                          // 0x002FC3F0..0x002FC43C
        UiText_Format(path, "event/BustUpEvent/%s.bccam",
                      g_BustupCutNames[i]);                   // 0x002FC3FC
        work->cameras[i] = engine_func_00263e48(path);        // 0x002FC408..0x002FC414

        UiText_Format(path, "event/BustUpEvent/%s.bam",
                      g_BustupCutNames[i]);                   // 0x002FC420
        work->models[i] = engine_func_0029a2d0(path, 7);      // 0x002FC42C..0x002FC438
    }

    work->model = work->cameras[0];                           // 0x002FC440..0x002FC444
    work->field_5f1 = 0;                                      // 0x002FC448

    void* const part = *reinterpret_cast<void**>(
        static_cast<u8*>(work->model) + 4);                   // 0x002FC44C..0x002FC450
    if (part != nullptr) {
        const u8* const object = *reinterpret_cast<u8* const*>(
            static_cast<u8*>(part) + 8);                      // 0x002FC458..0x002FC45C
        const u8* const state = *reinterpret_cast<u8* const*>(
            object + 8);                                      // 0x002FC460
        s32 index = static_cast<s32>(
            *reinterpret_cast<const u32*>(state + 0x10)) - 1; // 0x002FC464
        for (; index >= 0; --index)                           // 0x002FC468..0x002FC480
            ui_func_0024efe8(part, static_cast<u32>(index));
    }

    ui_func_002ae18c(work->eye, work->model);                 // 0x002FC48C

    AsdCamera_SetClipRange(&work->projection, 30.0f, 1.0f);   // 0x002FC4A4
    AsdCamera_LookAt(&work->projection, work->eye, work->target,
                     work->up);                               // 0x002FC4B8
    AsdCamera_SetPerspective(&work->projection, 1,
                             work->perspective[0], work->perspective[1],
                             work->perspective[2],
                             work->perspective[3]);           // 0x002FC4CC
    AsdCamera_BindProjection(&work->projection);              // 0x002FC4D8

    return work->task;                                        // 0x002FC4DC..0x002FC4E4
}

// Keep the camera/model reconstruction above and the original optimized
// ARM sequence below, including its in-function literal pool.
// DECOMP_FUNC(0x002fc260, 800)
__attribute__((naked)) void* BustupCutAnim_func_002fc260()
{
    asm volatile(
        ".word 0xe92d47f0, 0xe59f8284, 0xed2d8b02, 0xe24dd050\n" // 0x002fc260: push {r4, r5, r6, r7, r8, sb, sl, lr}; ldr r8, [pc, #0x284]; vpush {d8}; sub sp, sp, #0x50
        ".word 0xe5980000, 0xe3500000, 0x1a000097, 0xe59f1270\n" // 0x002fc270: ldr r0, [r8]; cmp r0, #0; bne #0x2fc4dc; ldr r1, [pc, #0x270]
        ".word 0xe59f0270, 0xe1a00000, 0xe59f426c, 0xe3a09001\n" // 0x002fc280: ldr r0, [pc, #0x270]; mov r0, r0; ldr r4, [pc, #0x26c]; mov sb, #1
        ".word 0xe3a01c01, 0xe1a03004, 0xe3a02000, 0xe1a00001\n" // 0x002fc290: mov r1, #0x100; mov r3, r4; mov r2, #0; mov r0, r1
        ".word 0xe58d9000, 0xebff2236, 0xe1a05000, 0xe1a01004\n" // 0x002fc2a0: str sb, [sp]; bl #0x2c4b84; mov r5, r0; mov r1, r4
        ".word 0xe5880000, 0xebff221d, 0xe3a01001, 0xe2850004\n" // 0x002fc2b0: str r0, [r8]; bl #0x2c4b30; mov r1, #1; add r0, r5, #4
        ".word 0xebff17d2, 0xe2857b01, 0xe2877f43, 0xed9f1a8b\n" // 0x002fc2c0: bl #0x2c2210; add r7, r5, #0x400; add r7, r7, #0x10c; vldr s2, [pc, #0x22c]
        ".word 0xe2850b01, 0xed871a00, 0xed871a01, 0xe2800f46\n" // 0x002fc2d0: add r0, r5, #0x400; vstr s2, [r7]; vstr s2, [r7, #4]; add r0, r0, #0x118
        ".word 0xed871a02, 0xed9f0a86, 0xed801a00, 0xed9f8a86\n" // 0x002fc2e0: vstr s2, [r7, #8]; vldr s0, [pc, #0x218]; vstr s2, [r0]; vldr s16, [pc, #0x218]
        ".word 0xed801a01, 0xeddf8a83, 0xed800a02, 0xeef00a48\n" // 0x002fc2f0: vstr s2, [r0, #4]; vldr s17, [pc, #0x20c]; vstr s0, [r0, #8]; vmov.f32 s1, s16
        ".word 0xe2851b01, 0xeddf1a81, 0xeeb00a68, 0xed811a50\n" // 0x002fc300: add r1, r5, #0x400; vldr s3, [pc, #0x204]; vmov.f32 s0, s17; vstr s2, [r1, #0x140]
        ".word 0xedc11a4e, 0xe2852e53, 0xe2850b01, 0xe2800f49\n" // 0x002fc310: vstr s3, [r1, #0x138]; add r2, r5, #0x530; add r0, r5, #0x400; add r0, r0, #0x124
        ".word 0xec820a02, 0xe2856004, 0xed801a00, 0xe2850b01\n" // 0x002fc320: vstmia r2, {s0, s1}; add r6, r5, #4; vstr s2, [r0]; add r0, r5, #0x400
        ".word 0xe2800f4a, 0xe1a04007, 0xecc00a02, 0xe1a00006\n" // 0x002fc330: add r0, r0, #0x128; mov r4, r7; vstmia r0, {s1, s2}; mov r0, r6
        ".word 0xed9f1a73, 0xed811a4f, 0xebff1509, 0xe2843018\n" // 0x002fc340: vldr s2, [pc, #0x1cc]; vstr s2, [r1, #0x13c]; bl #0x2c1774; add r3, r4, #0x18
        ".word 0xe284200c, 0xe1a01004, 0xe1a00006, 0xebff1751\n" // 0x002fc350: add r2, r4, #0xc; mov r1, r4; mov r0, r6; bl #0x2c20a8
        ".word 0xe1a07004, 0xe2844028, 0xed970a09, 0xe3a01001\n" // 0x002fc360: mov r7, r4; add r4, r4, #0x28; vldr s0, [r7, #0x24]; mov r1, #1
        ".word 0xecd40a03, 0xe1a00006, 0xebff171f, 0xe1a00006\n" // 0x002fc370: vldmia r4, {s1, s2, s3}; mov r0, r6; bl #0x2c1ffc; mov r0, r6
        ".word 0xebfe7319, 0xe3a0a000, 0xe59f118c, 0xe5c5a5f0\n" // 0x002fc380: bl #0x298fec; mov sl, #0; ldr r1, [pc, #0x18c]; strb sl, [r5, #0x5f0]
        ".word 0xe59f0180, 0xe5c595f2, 0xe28d4004, 0xe58d1000\n" // 0x002fc390: ldr r0, [pc, #0x180]; strb sb, [r5, #0x5f2]; add r4, sp, #4; str r1, [sp]
        ".word 0xe8840021, 0xe1a0300a, 0xe1a0200a, 0xe3a01002\n" // 0x002fc3a0: stm r4, {r0, r5}; mov r3, sl; mov r2, sl; mov r1, #2
        ".word 0xe28f0f5a, 0xebff256f, 0xe1a01000, 0xe5851000\n" // 0x002fc3b0: add r0, pc, #0x168; bl #0x2c5978; mov r1, r0; str r1, [r5]
        ".word 0xe59f0168, 0xe58d100c, 0xe58d5008, 0xe3a03000\n" // 0x002fc3c0: ldr r0, [pc, #0x168]; str r1, [sp, #0xc]; str r5, [sp, #8]; mov r3, #0
        ".word 0xe88d0401, 0xe1a02003, 0xe3a0106f, 0xe28f0e15\n" // 0x002fc3d0: stm sp, {r0, sl}; mov r2, r3; mov r1, #0x6f; add r0, pc, #0x150
        ".word 0xebff2206, 0xe3a04000, 0xe2889018, 0xe585a5ec\n" // 0x002fc3e0: bl #0x2c4c00; mov r4, #0; add sb, r8, #0x18; str sl, [r5, #0x5ec]
        ".word 0xe7992104, 0xe28f1f53, 0xe28d0010, 0xfaff08fe\n" // 0x002fc3f0: ldr r2, [sb, r4, lsl #2]; add r1, pc, #0x14c; add r0, sp, #0x10; blx #0x2be7fc
        ".word 0xe28d0010, 0xe320f000, 0xebfd9e8e, 0xe0856104\n" // 0x002fc400: add r0, sp, #0x10; nop ; bl #0x263e48; add r6, r5, r4, lsl #2
        ".word 0xe28f1f53, 0xe58606c8, 0xe7992104, 0xe28d0010\n" // 0x002fc410: add r1, pc, #0x14c; str r0, [r6, #0x6c8]; ldr r2, [sb, r4, lsl #2]; add r0, sp, #0x10
        ".word 0xfaff08f5, 0xe3a01007, 0xe28d0010, 0xebfe77a7\n" // 0x002fc420: blx #0x2be7fc; mov r1, #7; add r0, sp, #0x10; bl #0x29a2d0
        ".word 0xe2844001, 0xe354001c, 0xe5860658, 0x3affffeb\n" // 0x002fc430: add r4, r4, #1; cmp r4, #0x1c; str r0, [r6, #0x658]; blo #0x2fc3f0
        ".word 0xe59506c8, 0xe58505e8, 0xe5c5a5f1, 0xe5906004\n" // 0x002fc440: ldr r0, [r5, #0x6c8]; str r0, [r5, #0x5e8]; strb sl, [r5, #0x5f1]; ldr r6, [r0, #4]
        ".word 0xe3560000, 0x0a00000a, 0xe5960008, 0xe5900008\n" // 0x002fc450: cmp r6, #0; beq #0x2fc484; ldr r0, [r6, #8]; ldr r0, [r0, #8]
        ".word 0xe5900010, 0xe2504001, 0x4a000005, 0xe1a01004\n" // 0x002fc460: ldr r0, [r0, #0x10]; subs r4, r0, #1; bmi #0x2fc484; mov r1, r4
        ".word 0xe1a00006, 0xebfd4adb, 0xe2544001, 0xe320f000\n" // 0x002fc470: mov r0, r6; bl #0x24efe8; subs r4, r4, #1; nop
        ".word 0x5afffff9, 0xe59515e8, 0xe1a00007, 0xebfec73e\n" // 0x002fc480: bpl #0x2fc46c; ldr r1, [r5, #0x5e8]; mov r0, r7; bl #0x2ae18c
        ".word 0xeef00a48, 0xeeb00a68, 0xe2855004, 0xe1a04007\n" // 0x002fc490: vmov.f32 s1, s16; vmov.f32 s0, s17; add r5, r5, #4; mov r4, r7
        ".word 0xe1a00005, 0xebff14b2, 0xe2843018, 0xe284200c\n" // 0x002fc4a0: mov r0, r5; bl #0x2c1774; add r3, r4, #0x18; add r2, r4, #0xc
        ".word 0xe1a01004, 0xe1a00005, 0xebff16fa, 0xe2844024\n" // 0x002fc4b0: mov r1, r4; mov r0, r5; bl #0x2c20a8; add r4, r4, #0x24
        ".word 0xe3a01001, 0xec940a04, 0xe1a00005, 0xebff16ca\n" // 0x002fc4c0: mov r1, #1; vldmia r4, {s0, s1, s2, s3}; mov r0, r5; bl #0x2c1ffc
        ".word 0xe1a00005, 0xe320f000, 0xebfe72c3, 0xe5980000\n" // 0x002fc4d0: mov r0, r5; nop ; bl #0x298fec; ldr r0, [r8]
        ".word 0xe5900000, 0xe28dd050, 0xecbd8b02, 0xe8bd87f0\n" // 0x002fc4e0: ldr r0, [r0]; add sp, sp, #0x50; vpop {d8}; pop {r4, r5, r6, r7, r8, sb, sl, pc}
        ".word 0x0043dfc0, 0x00000201, 0x00403794, 0x00000744\n" // 0x002fc4f0: subeq sp, r3, r0, asr #31; andeq r0, r0, r1, lsl #4; umaaleq r3, r0, r4, r7; andeq r0, r0, r4, asr #14
        ".word 0x00000000, 0xc0a00000, 0x41f00000, 0x3f800000\n" // 0x002fc500: andeq r0, r0, r0; adcgt r0, r0, r0; mvnsmi r0, r0; svclo #0x800000
        ".word 0x461c4000, 0x3fd55555, 0x002f6a3c, 0x002168d0\n" // 0x002fc510: ldrmi r4, [ip], -r0; svclo #0xd55555; eoreq r6, pc, ip, lsr sl; literal/data
        ".word 0x74737542, 0x75437075, 0x696e4174, 0x0000006d\n" // 0x002fc520: literal/data; literal/data; literal/data; literal/data
        ".word 0x002cf8a8, 0x74737542, 0x75437075, 0x696e4174\n" // 0x002fc530: literal/data; literal/data; literal/data; literal/data
        ".word 0x6172446d, 0x00000077, 0x6e657665, 0x75422f74\n" // 0x002fc540: literal/data; literal/data; literal/data; literal/data
        ".word 0x70557473, 0x6e657645, 0x73252f74, 0x6363622e\n" // 0x002fc550: literal/data; literal/data; literal/data; literal/data
        ".word 0x00006d61, 0x6e657665, 0x75422f74, 0x70557473\n" // 0x002fc560: literal/data; literal/data; literal/data; literal/data
        ".word 0x6e657645, 0x73252f74, 0x6d61622e, 0x00000000\n" // 0x002fc570: literal/data; literal/data; literal/data; literal/data
    );
}

// DECOMP_FUNC(0x0030ac20, 412)


// ---------------------------------------------------------------------------
// BustupTex.cpp (ui)
// ---------------------------------------------------------------------------

/**
 * Creates the bustup texture loader when event bit 0x522 is clear (or when the
 * NPC row has an index-1 entry).
 *
 * The mode argument selects the row-key block at 0x0030ACD0..0x0030ACE8.  Both
 * paths reach `mov r5,#0` at 0x0030ACC0, so the byte stored at +0x7C/+0x30 is
 * always zero; the scene-busy exit skips the +0x7C store but still writes +0x30.
 *
 *
 */
__attribute__((naked)) void BustupTex_func_0030ac20(u32, u32)
{
    asm volatile(
        ".word 0xe92d41f0\n" // push {r4, r5, r6, r7, r8, lr}
        ".word 0xe1a05000\n" // preserve request id
        ".word 0xe24dd010\n" // reserve task stack arguments
        ".word 0xe59f0160\n" // event id literal 0x522
        ".word 0xe1a06001\n" // preserve mode
        ".word 0xebfed7db\n" // Flag_CheckEventBit (0x002c0ba8)
        ".word 0xe3500000\n"
        ".word 0x0a000005\n" // skip row gate when event bit is clear
        ".word 0xe1a00005\n"
        ".word 0xebfcebbe\n" // AsdTable_FindNpcRow (0x00245b44)
        ".word 0xe3a01001\n"
        ".word 0xebfe90c6\n" // AsdTable_GetRowEntry (0x002aef6c)
        ".word 0xe3500000\n"
        ".word 0x0a00004c\n" // null index-1 row exits
        ".word 0xe59f1138\n"
        ".word 0xe59f0138\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a07001\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a03090\n" // allocate 0x90-byte work record
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xe58d7000\n"
        ".word 0xebfee7c0\n" // AsdMem_Alloc (0x002c4b84)
        ".word 0xe1a04000\n" // preserve work record
        ".word 0xe3a01090\n"
        ".word 0xebfee7a8\n" // AsdMem_Zero (0x002c4b30)
        ".word 0xe3e08000\n" // -1 sentinel
        ".word 0xe5845000\n" // request_id
        ".word 0xe5848084\n" // field_84 = -1
        ".word 0xe1a00005\n"
        ".word 0xe5848018\n" // field_18 = -1
        ".word 0xebfceba7\n" // AsdTable_FindNpcRow (0x00245b44)
        ".word 0xe3560000\n" // choose mode path
        ".word 0xe1a01000\n"
        ".word 0xe5840004\n" // row pointer
        ".word 0x0a000006\n" // mode zero: initialize default row key
        ".word 0xe320f000\n"
        ".word 0xebfedc9a\n" // AsdScene_LoadMode (0x002c1f28)
        ".word 0xe3500000\n"
        ".word 0xe3a05000\n"
        ".word 0x15c4707c\n" // busy path sets field_7c = 1
        ".word 0x1a00001f\n" // busy path joins the task setup
        ".word 0xea000007\n" // otherwise continue with default-row path
        ".word 0xe2842010\n"
        ".word 0xe3a00020\n" // key = 0x20
        ".word 0xe8820101\n" // key = 0x20, sub = -1
        ".word 0xed9f0a2f\n" // 25.0f literal
        ".word 0xe5d1002b\n" // preserve ROM's row[0x2b] read
        ".word 0xed840a07\n" // field_1c = 25.0f
        ".word 0xed840a08\n" // field_20 = 25.0f
        ".word 0xeafffff0\n" // recheck scene-load mode
        ".word 0xe5942014\n"
        ".word 0xe3720001\n" // skip load when sub is -1
        ".word 0x0a000012\n"
        ".word 0xe59f60a0\n" // g_CampMessageBundle slot
        ".word 0xe5941010\n" // key
        ".word 0xe3a03001\n" // row-exists mode
        ".word 0xe5960000\n" // dereference bundle slot
        ".word 0xebfe8fc3\n" // AsdRow_Has (0x002aec20)
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000007\n" // miss: use synchronous row load
        ".word 0xe2841010\n"
        ".word 0xe5960000\n"
        ".word 0xe8910006\n" // key and sub
        ".word 0xe3a03801\n" // request flags 0x10000
        ".word 0xebfe8f91\n" // AsdRow_Request (0x002aeb78)
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000001\n"
        ".word 0xe1c401d0\n" // key/sub pair for AsdRow_LoadNow
        ".word 0xebfeeb5c\n" // AsdRow_LoadNow (0x002c5ab8)
        ".word 0xe584000c\n" // row_data
        ".word 0xe5c4507c\n" // pending byte = 0 on normal path
        ".word 0xed9f0a15\n" // 0.0f literal
        ".word 0xeddf0a15\n" // 1.0f literal
        ".word 0xe2842028\n"
        ".word 0xe59f1054\n" // callback user data 0x002cfabc
        ".word 0xe59f004c\n" // "EVE_BustupTex"
        ".word 0xe28d6004\n"
        ".word 0xec820a02\n" // fields +0x28/+0x2c = 0.0f/1.0f
        ".word 0xe3a03000\n"
        ".word 0xe5c45030\n" // field_30 = 0
        ".word 0xe5c47031\n" // field_31 = 1
        ".word 0xe58d1000\n"
        ".word 0xe8860011\n" // callback and work pointer stack args
        ".word 0xe1a02003\n"
        ".word 0xe59f0030\n"
        ".word 0xe3a01002\n"
        ".word 0xebfeeafa\n" // AsdTask_CreateCalc (0x002c5978)
        ".word 0xe28dd010\n"
        ".word 0xe8bd81f0\n"
        ".word 0x00000522\n"
        ".word 0x00000484\n"
        ".word 0x00403850\n"
        ".word 0x41c80000\n" // 25.0f
        ".word 0x00433158\n" // g_CampMessageBundle
        ".word 0x00000000\n" // 0.0f
        ".word 0x3f800000\n" // 1.0f
        ".word 0x002cfabc\n"
        ".word 0x001ce3a4\n"
        ".word 0x00403840\n"); // task name
}

}
// DECOMP_FUNC(0x00269404, 400)
 // namespace smt4::ui

// Exact ROM bodies with their inline literal pools retained verbatim.
__attribute__((naked)) EffBehavior* effBehavior_func_00269404(u32, u32, void*)
{
    asm volatile(
        ".word 0xE92D4FF0, 0xE1A06001, 0xE1A05000, 0xE1A0A002\n"
        ".word 0xE28A10C0, 0xE59F0130, 0xE891000A, 0xE0852105\n"
        ".word 0xE24DD00C, 0xE0800102, 0xE2800008, 0xE0010391\n"
        ".word 0xE8900084, 0xE0286196, 0xE0000692, 0xE0881108\n"
        ".word 0xE1A09181, 0xE0800009, 0xE0800087, 0xE2804030\n"
        ".word 0xE3A01D3F, 0xE28F00F4, 0xE1A00000, 0xE3A01001\n"
        ".word 0xE3A00010, 0xE1CD00F0, 0xE1A03004, 0xE3A02000\n"
        ".word 0xE3A01C01, 0xE3A00801, 0xEB016808, 0xE2801030\n"
        ".word 0xE0813009, 0xE5801018, 0xE0831007, 0xE1A04000\n"
        ".word 0xE5801024, 0xE280001C, 0xE0811007, 0xE880000A\n"
        ".word 0xE2840004, 0xE3A0B000, 0xE1C450B0, 0xE8800940\n"
        ".word 0xE1A02007, 0xED9F0A33, 0xE584B010, 0xED840A05\n"
        ".word 0xE1A0100A, 0xE1A00003, 0xE5844028, 0xEB0172C7\n"
        ".word 0xE5940024, 0xE1A02007, 0xE1A0100A, 0xEB0172C3\n"
        ".word 0xE5940020, 0xED9F0A28, 0xE580B000, 0xE580B004\n"
        ".word 0xE580B008, 0xE580B00C, 0xED800A03, 0xE580B010\n"
        ".word 0xE580B014, 0xE580B018, 0xE580B01C, 0xED800A07\n"
        ".word 0xE5D000BC, 0xE3500000, 0x0A000002, 0xE594000C\n"
        ".word 0xE3800001, 0xE584000C, 0xE355000C, 0x1355000D\n"
        ".word 0x1A000002, 0xE594000C, 0xE3800002, 0xE584000C\n"
        ".word 0xE28DD00C, 0xE1A00004, 0xE8BD8FF0, 0x00473590\n"
        ".word 0x535C3A63, 0x5C34544D, 0x36445258, 0x415C3638\n"
        ".word 0x44536473, 0x6F535C4B, 0x65637275, 0x7866475C\n"
        ".word 0x6666455C, 0x5C746365, 0x42666665, 0x76616865\n"
        ".word 0x2E726F69, 0x00707063, 0x00000000, 0x3F800000\n");
}
// DECOMP_FUNC(0x002bc570, 468)


__attribute__((naked)) void AsdGxRenderSystem_func_002bc570(
    AsdGxLayerSet*, const AsdGxLayerDesc*, u32)
{
    asm volatile(
        ".word 0xE92D4FF0, 0xE24DD00C, 0xE1A06000, 0xE1A08001\n"
        ".word 0xE1A09002, 0xE59FB1A8, 0xE3A07000, 0xE3A0A000\n"
        ".word 0xE0870087, 0xE1A0300A, 0xE0884180, 0xE2841004\n"
        ".word 0xE594C000, 0xE8910006, 0xE0865180, 0xE15C000B\n"
        ".word 0xE24CEC81, 0xE1A0000A, 0x00010291, 0xE24EE0A5\n"
        ".word 0x0A000018, 0xCA00000D, 0xE24CC902, 0xE25CC056\n"
        ".word 0x00010291, 0x03A00004, 0x0A000012, 0xE35C0001\n"
        ".word 0x00010291, 0x03A00002, 0x0A00000E, 0xE35C0002\n"
        ".word 0x00010291, 0x03A03002, 0x0A00000C, 0xEA00000C\n"
        ".word 0xE24ECC07, 0xE25CC04B, 0x00010291, 0x03A00003\n"
        ".word 0x0A000006, 0xE24CCB01, 0xE25CC072, 0x00010291\n"
        ".word 0x03A00003, 0x1A000002, 0xE1A0A081, 0xEA000000\n"
        ".word 0xE1A0A101, 0xE585A010, 0xE5941000, 0xE5850004\n"
        ".word 0xE3590000, 0xE5851000, 0xE5853014, 0x0A00002D\n"
        ".word 0xE594100C, 0xE3A00000, 0xE3510801, 0x0A000004\n"
        ".word 0xE3510802, 0x0A000010, 0xE3510803, 0x1A000022\n"
        ".word 0xEA000017, 0xE59F10BC, 0xE59F00BC, 0xE1A00000\n"
        ".word 0xE3A01001, 0xE3A00040, 0xE1CD00F0, 0xE1A0300A\n"
        ".word 0xE3A02000, 0xE3A01C01, 0xE3A00801, 0xEB000C3D\n"
        ".word 0xE320F000, 0xE320F000, 0xEA000013, 0xE59F108C\n"
        ".word 0xE59F0084, 0xE1A00000, 0xE3A00001, 0xE58D0000\n"
        ".word 0xE1A0300A, 0xE3A02000, 0xE3A01C01, 0xE3A00802\n"
        ".word 0xEA000008, 0xE59F0060, 0xE3A01EA6, 0xE1A00000\n"
        ".word 0xE3A00001, 0xE58D0000, 0xE1A0300A, 0xE3A02000\n"
        ".word 0xE3A01C01, 0xE3A00803, 0xEB00237C, 0xE5850008\n"
        ".word 0xEBFFFEFE, 0xE585000C, 0xE5940004, 0xE2877001\n"
        ".word 0xE3570002, 0xE5860030, 0xE5940008, 0xE5860034\n"
        ".word 0xE5940014, 0xE5860038, 0x3AFFFF97, 0xE28DD00C\n"
        ".word 0xE8BD8FF0, 0x000081A5, 0x00000A5E, 0x00409984\n"
        ".word 0x00000A5F\n");
}
// DECOMP_FUNC(0x0030a0b8, 468)


[[deprecated("3dEventTex_func_0030a0b8(0x0030A0B8) ledger spelling pin")]]
__attribute__((naked)) void* EventTex3d_func_0030a0b8(u32, f32, f32)
{
    asm volatile(
        ".word 0xE92D40F0, 0xE1A05000, 0xE28F0F59, 0xE59F115C\n"
        ".word 0xED2D8B04, 0xEEB08B40, 0xE24DD014, 0xE1A00000\n"
        ".word 0xE3A07001, 0xE3A01C01, 0xE3A03048, 0xE3A02000\n"
        ".word 0xE1A00001, 0xE58D7000, 0xEBFEEAA3, 0xE1A04000\n"
        ".word 0xE3A01048, 0xEBFEEA8B, 0xED9F0A59, 0xED9F9A57\n"
        ".word 0xEDDF0A58, 0xED840A02, 0xED849A03, 0xE3A06000\n"
        ".word 0xEDC40A04, 0xE5C46014, 0xE1A00005, 0xE5C46017\n"
        ".word 0xEBFCEE85, 0xE1D002B2, 0xE2600000, 0xE5840038\n"
        ".word 0xEBFEDF7A, 0xE3500000, 0x15847004, 0x1A000005\n"
        ".word 0xE5940038, 0xE3A01001, 0xEBFE2877, 0xE3A01002\n"
        ".word 0xE5840034, 0xE5841004, 0xEE180A10, 0xE5845000\n"
        ".word 0xE37005FE, 0x23A00010, 0x2A000010, 0xEE180A10\n"
        ".word 0xE37005FF, 0x23A00003, 0x2A00000C, 0xE59F10E8\n"
        ".word 0xEE180A10, 0xE1500001, 0xA3A00011, 0xAA000007\n"
        ".word 0xEE180A10, 0xE35005FF, 0xA3A00004, 0xAA000003\n"
        ".word 0xEEB48AC9, 0xEEF1FA10, 0x33A00012, 0x23A00005\n"
        ".word 0xE584003C, 0xE284202C, 0xE59F10B4, 0xE59F00AC\n"
        ".word 0xE28D5004, 0xEC828A02, 0xE3A03000, 0xE5C47016\n"
        ".word 0xE5C46015, 0xE58D1000, 0xE8850011, 0xE1A02003\n"
        ".word 0xE59F0090, 0xE3A01002, 0xEBFEEDE0, 0xE59F1088\n"
        ".word 0xE1A05000, 0xE3A03000, 0xE88D0042, 0xE59F007C\n"
        ".word 0xE1A02003, 0xE3A0106F, 0xE1CD40F8, 0xEBFEEA79\n"
        ".word 0xE28DD014, 0xE1A00005, 0xECBD8B04, 0xE8BD80F0\n"
        ".word 0x0000018D, 0x535C3A63, 0x5C34544D, 0x36445258\n"
        ".word 0x735C3638, 0x34736464, 0x6F72705C, 0x6D617267\n"
        ".word 0x6576655C, 0x335C746E, 0x65764564, 0x335C746E\n"
        ".word 0x65764564, 0x6554746E, 0x70632E78, 0x00000070\n"
        ".word 0x00000000, 0x3F800000, 0x3E800000, 0x40400000\n"
        ".word 0x002DB938, 0x001DFFBC, 0x0040377C, 0x001E0138\n"
        ".word 0x0040376C\n");
}
// DECOMP_FUNC(0x00327634, 488)


__attribute__((naked)) void Npc2d_func_00327634(u32)
{
    asm volatile(
        ".word 0xE92D41F0, 0xE1A05000, 0xE3A01FE1, 0xE59F01AC\n"
        ".word 0xED2D8B02, 0xE24DD010, 0xE1A00000, 0xE3A07001\n"
        ".word 0xE3A01C01, 0xE3A03098, 0xE3A02000, 0xE1A00001\n"
        ".word 0xE58D7000, 0xEBFE7545, 0xE1A04000, 0xE3A01098\n"
        ".word 0xEBFE752D, 0xED9F0A5E, 0xED9F8A5E, 0xED840A08\n"
        ".word 0xED840A09, 0xE3A01041, 0xED848A0A, 0xE3A02026\n"
        ".word 0xE5841004, 0xE3E03000, 0xE584203C, 0xE5843044\n"
        ".word 0xE5845000, 0xE3A06000, 0xE5C47064, 0xE5846068\n"
        ".word 0xE584606C, 0xE5C46070, 0xE1A00005, 0xE5C46071\n"
        ".word 0xEBFC791E, 0xE5840054, 0xE1D002B4, 0xE59F8128\n"
        ".word 0xE3A05000, 0xE5840040, 0xE3A00032, 0xE7D81005\n"
        ".word 0xEBFE5FF9, 0xE1D020F8, 0xE0841185, 0xE3550000\n"
        ".word 0xEE002A10, 0xEEB80AC0, 0xED810A1D, 0xE1D020FA\n"
        ".word 0xEE002A10, 0xEEB80AC0, 0xED810A1E, 0x0A000020\n"
        ".word 0xE2855001, 0xE3550003, 0x3AFFFFEE, 0xED940A20\n"
        ".word 0xEDDF0A36, 0xE3A01048, 0xEEBD0AC0, 0xED9F1A34\n"
        ".word 0xEDC40A1F, 0xE5841010, 0xED841A0A, 0xED848A07\n"
        ".word 0xE3A00005, 0xED848A09, 0xE5840038, 0xED840A05\n"
        ".word 0xEBFE69F3, 0xE3500000, 0x1584700C, 0x0A00001A\n"
        ".word 0xE59F00A4, 0xE59F10A4, 0xED9F0A26, 0xE3A03000\n"
        ".word 0xED840A06, 0xE88D0013, 0xE1A02003, 0xE59F0090\n"
        ".word 0xE3A01002, 0xEBFE787A, 0xE28DD010, 0xECBD8B02\n"
        ".word 0xE8BD81F0, 0xE590100C, 0xE3510000, 0x0A000008\n"
        ".word 0xE1D110F0, 0xEE001A10, 0xEEB80AC0, 0xED840A23\n"
        ".word 0xE590000C, 0xE1D000F2, 0xEE000A10, 0xEEB80AC0\n"
        ".word 0xED840A24, 0xE3A05001, 0xEAFFFFC2, 0xE584600C\n"
        ".word 0xE1C403DC, 0xEBFE78B6, 0xE3A01000, 0xE3A00032\n"
        ".word 0xEBFE78B3, 0xE320F000, 0xE320F000, 0xEAFFFFDB\n"
        ".word 0x004035D0, 0x3F800000, 0x00000000, 0x004035C0\n"
        ".word 0x42900000, 0x3E87AE14, 0x3E99999A, 0x001DFB60\n"
        ".word 0x002DB8C4, 0x004035C4\n");
}
// DECOMP_FUNC(0x0034b920, 432)


__attribute__((naked)) Filter4Poly* Filter4Poly_func_0034b920(
    Filter4PolySource*, u32, u32)
{
    asm volatile(
        ".word 0xE92D43F8, 0xE3520000, 0xE1A07000, 0xE1A04001\n"
        ".word 0xE3A06000, 0x0A000008, 0xE3A0000C, 0xEBFDDAAD\n"
        ".word 0xE3500000, 0x0A00000D, 0xE59F1168, 0xED9F0A58\n"
        ".word 0xED800A02, 0xE8800042, 0xEA000008, 0xE3A00020\n"
        ".word 0xEBFDDAA4, 0xE3500000, 0xE320F000, 0x0A000003\n"
        ".word 0xE59F1148, 0xED9F0A50, 0xED800A02, 0xE8800042\n"
        ".word 0xE1A08000, 0xE1A01004, 0xE3A00020, 0xEBFDDA99\n"
        ".word 0xE3500000, 0x03A05000, 0x0A000009, 0xE5806004\n"
        ".word 0xE59F1120, 0xED9F0A46, 0xE5806008, 0xE580600C\n"
        ".word 0xED800A04, 0xE5801000, 0xE580601C, 0xE1A05000\n"
        ".word 0xE5808014, 0xE585701C, 0xE597201C, 0xE1A01004\n"
        ".word 0xE1A00005, 0xEBFBBF07, 0xE59F00EC, 0xE3A01F4A\n"
        ".word 0xE1A00000, 0xE3A04001, 0xE3A01C01, 0xE3A03050\n"
        ".word 0xE3A02000, 0xE1A00001, 0xE58D4000, 0xEBFDE6BB\n"
        ".word 0xE5850004, 0xE59F00C0, 0xE2841F4A, 0xE1A00000\n"
        ".word 0xE58D4000, 0xE595001C, 0xE3A01C01, 0xE3A02000\n"
        ".word 0xE590002C, 0xE0800100, 0xE1A03200, 0xE1A00001\n"
        ".word 0xEBFDE6AE, 0xE5850018, 0xE1A00005, 0xEB000023\n"
        ".word 0xE5950000, 0xE5901010, 0xE1A00005, 0xE12FFF31\n"
        ".word 0xE595001C, 0xE3A04000, 0xE590002C, 0xE3500000\n"
        ".word 0xDA00000B, 0xE5951018, 0xE0840104, 0xE0816200\n"
        ".word 0xEBFD7123, 0xE1A01000, 0xE1A00006, 0xEBFDD15F\n"
        ".word 0xE595001C, 0xE2844001, 0xE590002C, 0xE1500004\n"
        ".word 0xCAFFFFF3, 0xE5980000, 0xE2877034, 0xE897000E\n"
        ".word 0xE590C014, 0xE1A00008, 0xE12FFF3C, 0xE1A00005\n"
        ".word 0xE8BD83F8, 0x3F800000, 0x004204D0, 0x00000000\n"
        ".word 0x00420358, 0x3C23D70A, 0x00420598, 0x003FF848\n");
}
