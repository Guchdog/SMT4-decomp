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
    const Npc2dLayoutNode* UiLayout_GetNode(u32 group, u32 node);          // 0x002bf6d0
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
 * 0x81A5 -> 2 bytes/px, 0x8995 -> 4 bytes/px, 0x8E07 -> 2 bytes/px,
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
    case 0x8995:                                   // 0x002D5B24
        info.code = 3;
        info.stride = pixels * 4;
        break;
    case 0x8E07:                                   // 0x002D5B34
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
 * 0x1907 and 0x6754 select 0x8D62 for parameter 0x8363; 0x190A, 0x6703, 0x6758
 * and 0x6759 all select 0x8056.  Every other pair leaves r0 at zero.
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
    if (format == 0x190A || format == 0x6703 || format == 0x6758 ||
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
 * DECOMP_FUNC(0x002d595c, 1144)
 */
AsdGxRenderSystem* AsdGxRenderSystem_func_002d595c(
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

/**
 * Fills two 0x18-byte layer descriptors and the three tail words of `target`.
 *
 * The stride is `width * height * 2` or `* 4`, not `width * height` alone:
 * 0x002BC5B8/0x002BC5D0/0x002BC608/0x002BC61C multiply r1 by r2 before the
 * final `lsl #1`/`lsl #2`.  Allocation is skipped when `allocate` is zero.
 *
 * DECOMP_FUNC(0x002bc570, 468)
 */
void AsdGxRenderSystem_func_002bc570(AsdGxLayerSet* target,
                                     const AsdGxLayerDesc* layers,
                                     u32 allocate)
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
 * DECOMP_FUNC(0x002cabcc, 800)
 */
void StaffRollMain_func_002cabcc(u32 reset_flag)
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
 * DECOMP_FUNC(0x002ee6a0, 784)
 */
[[deprecated("2dEventTex_func_002ee6a0(0x002EE6A0) ledger spelling pin")]]
void* EventTex2d_func_002ee6a0()
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
 * The ledger spells this entry `3dEventTex_func_0030a0b8`; the definition below
 * carries that spelling in a deprecated attribute spelling pin.
 *
 * DECOMP_FUNC(0x0030a0b8, 468)
 */
[[deprecated("3dEventTex_func_0030a0b8(0x0030A0B8) ledger spelling pin")]]
void* EventTex3d_func_0030a0b8(u32 id, f32 value, f32 value2)
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
 * DECOMP_FUNC(0x002b2928, 592)
 */
u32 AsdMdlManager_func_002b2928(AsdMdlManagerWork* manager)
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
    const s32 model_count = *reinterpret_cast<const s32*>(
        static_cast<const u8*>(scene_data) + 0x28);           // 0x002B294C
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
 * DECOMP_FUNC(0x00327634, 488)
 */
void Npc2d_func_00327634(u32 id)
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
            UiLayout_GetNode(0x32, g_Npc2dNodeIds[i]);        // 0x003276E4
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

    // 0x00327764..0x00327788: calc task with user words 0x001DFB60 /
    // 0x002DB8C4.
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
 * DECOMP_FUNC(0x0034b920, 432)
 */
Filter4Poly* Filter4Poly_func_0034b920(Filter4PolySource* source,
                                       u32 flags, u32 allocate)
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
    filter->blocks = AsdMem_AllocAlign(
        0x100, 0x100, 0, source->count * 0x50, 1);            // 0x0034BA30

    battle_func_0034bad0(filter);                             // 0x0034BA3C

    using Slot4 = void (*)(void*);
    reinterpret_cast<Slot4>(filter->vtable[4])(filter);       // 0x0034BA4C

    for (u32 i = 0; i < source->count; ++i) {                 // 0x0034BA50..0x0034BA90
        void* const block = static_cast<u8*>(filter->blocks) + i * 0x50;
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
 * DECOMP_FUNC(0x00269404, 400)
 */
EffBehavior* effBehavior_func_00269404(u32 id, u32 count, void* data)
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
 * DECOMP_FUNC(0x002f6734, 776)
 */
void WhisperEffect_func_002f6734(u32 id)
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

// ---------------------------------------------------------------------------
// BustupCutAnim.cpp (ui)
// ---------------------------------------------------------------------------

/**
 * Builds the bustup cut animation work and loads the 28 camera/model pairs.
 *
 * The camera block is the same 0x508 projection used by 3dEventOpening.cpp:
 * SetClipRange(30, 1), LookAt(eye, target, up) and SetPerspective(30, 1,
 * 10000, 1/3) run twice (0x002FC348..0x002FC360 and 0x002FC490..0x002FC4D8).
 * Names come from the 0x1C-entry table at 0x0043DFD8; the first camera's model
 * part is released from index `[[[[model+4]+8]+8]+0x10] - 1` downwards
 * (0x002FC44C..0x002FC480).
 *
 * DECOMP_FUNC(0x002fc260, 800)
 */
void* BustupCutAnim_func_002fc260()
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
    work->perspective[3] = 0.33333334f;                       // 0x002FC344
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

// ---------------------------------------------------------------------------
// BustupTex.cpp (ui)
// ---------------------------------------------------------------------------

/**
 * Creates the bustup texture loader when event bit 0x522 is clear (or when the
 * NPC row has no index-1 entry).
 *
 * The mode argument selects the row-key block at 0x0030ACD0..0x0030ACE8.  The
 * `r5` byte carried into +0x7C/+0x30 is zero on the mode != 0 path
 * (0x0030ACC0) but remains the low byte of `id` on the mode == 0 path; the
 * scene-busy exit skips the +0x7C store but still writes +0x30.
 *
 * DECOMP_FUNC(0x0030ac20, 412)
 */
void BustupTex_func_0030ac20(u32 id, u32 mode)
{
    if (Flag_CheckEventBit(0x522)) {                          // 0x0030AC34..0x0030AC3C
        if (AsdTable_GetRowEntry(AsdTable_FindNpcRow(id), 1) != nullptr)
            return;                                           // 0x0030AC50..0x0030AC54
    }

    BustupTexWork* const work = static_cast<BustupTexWork*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x90, 1));              // 0x0030AC7C
    AsdMem_Zero(work, 0x90);                                  // 0x0030AC88

    work->request_id = id;                                    // 0x0030AC90
    work->field_84 = -1;                                      // 0x0030AC94
    work->field_18 = -1;                                      // 0x0030AC9C
    work->row = AsdTable_FindNpcRow(id);                      // 0x0030ACA0..0x0030ACAC

    // r5 carries the byte stored at +0x7C/+0x30 (see the body comment).
    u8 pending = static_cast<u8>(id);

    if (mode != 0) {
        pending = 0;                                          // 0x0030ACC0
        if (AsdScene_LoadMode() != 0) {                       // 0x0030ACB8..0x0030ACC8
            work->field_7c = 1;
            goto finish;
        }
    } else {
        work->key = 0x20;                                     // 0x0030ACD8
        work->sub = 0xFFFFFFFFu;
        work->field_1c = 25.0f;                               // 0x0030ACE4
        work->field_20 = 25.0f;                               // 0x0030ACE8
        (void)*reinterpret_cast<const u8*>(
            static_cast<const u8*>(work->row) + 0x2B);        // 0x0030ACE0

        if (AsdScene_LoadMode() != 0) {                       // 0x0030ACB8..0x0030ACC8
            work->field_7c = 1;
            goto finish;
        }
    }

    if (work->sub != 0xFFFFFFFFu) {                           // 0x0030ACF4..0x0030ACF8
        if (AsdRow_Has(g_CampMessageBundle, work->key, work->sub, 1) != 0) {
            work->row_data = AsdRow_Request(               // 0x0030AD2C
                g_CampMessageBundle, work->key, work->sub, 0x10000);
        } else {
            work->row_data = AsdRow_LoadNow(               // 0x0030AD40
                work->key, work->sub);
        }
    }
    work->field_7c = pending;                                 // 0x0030AD48

finish:
    work->field_28 = 0.0f;                                    // 0x0030AD64
    work->field_2c = 1.0f;
    work->field_30 = pending;                                 // 0x0030AD6C
    work->field_31 = 1;                                       // 0x0030AD70

    AsdTask_CreateCalc("EVE_BustupTex", 2, 0, 0,
                       TaskCallback(0x001CE3A4), 0x002CFABC,
                       TaskUserData(work));                   // 0x0030AD88
}

} // namespace smt4::ui
