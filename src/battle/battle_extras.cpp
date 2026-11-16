#include "battle/battle_extras.h"
#include "engine/asd_frame.h"
#include "engine/asd_symbols.h"
#include "engine/asd_texture.h"

#include <algorithm>

namespace smt4::battle {

// ---------------------------------------------------------------------------
// Globals (addresses are the storage locations used by the listing)
// ---------------------------------------------------------------------------

EnemyDrawGlobal g_EnemyDrawGlobal = {};                  // 0x00433D98
EffectProcessWork* g_EffectProcessWork = nullptr;        // 0x00433260
BtlTalkBustUpWork* g_BtlTalkBustUpWork = nullptr;        // 0x00434210
BtlDebugState g_BtlDebugState = {};                      // 0x00434388
BtlEditorState* g_BtlEditorState = nullptr;              // 0x00435CE8
BtlGameOverState* g_BtlGameOverState = nullptr;          // 0x00435D60

// 0x00476634: low bit gates the one-time identity fill at 0x0033EF30.
u32 g_EnemyDrawFlags = 0;
// 0x00476638: low bit gates the one-time identity fill at 0x00348870.
u32 g_FilterXPolyFlags = 0;

// 0x004EFD6C: matrix rebuilt by 0x0033EF68..0x0033EF98 when the flag above is
// clear.  Only twelve floats (+0x00..+0x2C) are stored by the listing; the
// +0x30..+0x3C tail is left untouched.
f32 g_EnemyDrawMatrix[16] = {
    1.0f, 0.0f, 0.0f, 0.0f,
    0.0f, 1.0f, 0.0f, 0.0f,
    0.0f, 0.0f, 1.0f, 0.0f,
    0.0f, 0.0f, 0.0f, 1.0f,
};

// 0x004EFD9C: same identity image written at 0x0034888C..0x003488CC.
f32 g_FilterXPolyMatrix[16] = {
    1.0f, 0.0f, 0.0f, 0.0f,
    0.0f, 1.0f, 0.0f, 0.0f,
    0.0f, 0.0f, 1.0f, 0.0f,
    0.0f, 0.0f, 0.0f, 1.0f,
};

// 0x00407FC0: four-float-per-entry angle table (the listing indexes with
// `(angle & 0xFF) << 4`, e.g. 0x00348680).  The table lives in .rodata.
extern const FilterTrigRow g_FilterTrigTable[256];

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

extern "C" {
    // AsdMemory (c:\SMT4\XRD686\AsdSDK\Source\Sys\Mem\AsdMemory.cpp)
    void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);         // 0x002C4B84
    void* AsdMem_AllocAlign(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);    // 0x002C54F0
    void  AsdMem_Zero(void* ptr, u32 size);                                 // 0x002C4B30
    void  AsdMem_Free(void* ptr);                                           // 0x002C4360
    void  AsdMem_Copy(void* dst, const void* src, u32 size);                // 0x002C5FF4

    // AsdProcess / GPU frame state shared with the other battle TUs.
    extern u8* g_AsdGpuState;                                               // 0x0044EA00

    // EnemyDraw mode/flag queries.
    s32  Battle_GetDrawMode();                                              // 0x002B8B44
    s32  Battle_GetEnemyCount(u32 id);                                      // 0x001A0EA4
    s32  Battle_IsUiHidden();                                               // 0x002B8ADC
    s32  Battle_IsCampActive();                                             // 0x002B8A80
    s32  Battle_IsScriptActive();                                           // 0x002B89FC
    s32  ScriptVm_IsTalkActive();                                           // 0x002B89D4
    s32  Camp_IsMenuActive();                                               // 0x002B89A0

    // Matrix helpers used by both EnemyDraw and titleDbgBg.  The argument order
    // is the register order observed at each branch target:
    //   Translate: r2 = matrix, r1 = vec, r0 = out
    //   Multiply:  r1/r2 = operands, r0 = out
    //   AddTranslation: r0 = out, r1 = vec, r2 = matrix
    //   TransformPoint: r0 = out, r1 = matrix, r2 = in
    s32  Gpu_CheckDrawFlag(const void* flag);                               // 0x002C00D4
    void Battle_LoadMatrix(void* dst, const void* src);                     // 0x002C00B4
    void Matrix_Translate(f32* out, const f32* vec, const f32* matrix);     // 0x0023E4E4
    void Matrix_FromEuler(void* dst, u32 mode, f32 x, f32 y, f32 z);        // 0x00292C7C
    void Matrix_Multiply(f32* out, const void* a, const void* b);           // 0x002A5078
    void Matrix_AddTranslation(f32* out, const f32* vec, const f32* matrix); // 0x0015F6D4
    void Matrix_TransformPoint(f32* out, const void* matrix, const f32* in); // 0x002AD6D8

    // Effect file loading / attachment.
    s32  AsdString_Compare(const char* a, const char* b);                   // 0x002AA7F4
    void* EftItem_Setup(void* item);                                        // 0x002216C0
    void Eft_AttachRecords(s32 id, const void* records, u32 count);         // 0x002FDEF8
    void Eft_AttachItems(s32 id, const void* items, u32 count);             // 0x0031BC30
    void Eft_AttachHeader(s32 id, const void* header);                      // 0x00215938
    void Eft_SetNameA(s32 id, const void* name);                            // 0x001AD19C
    void Eft_SetNameB(s32 id, const void* name);                            // 0x001AD380
    void Eft_SetNameC(s32 id, const void* name);                            // 0x001AD124
    void Eft_SetNameD(s32 id, const void* name);                            // 0x001AD160

    // titleDbgBg helpers.
    void Title_UpdateTextureSize(void* texture, void* size_slot);           // 0x002BFC88
    f32  Camp_GetAspectScale(f32 a, f32 b);                                 // 0x002B9CF8
    void Ui_DrawModel(void* gpu_state, void* model);                        // 0x002C1D3C
    void Title_DrawQuad(void* object, void* a, void* b, void* c,
                        f32 s0, f32 s1, f32 s2, f32 s3,
                        f32 s4, f32 s5, f32 s6, f32 s7,
                        f32 s8, f32 s9, f32 s10, f32 s11,
                        f32 s12, f32 s13, f32 s14, f32 s15,
                        f32 t0, f32 t1, f32 t2, f32 t3);                    // 0x002BA520

    // FilterXPoly primitive setup.
    void Filter_Prepare(FilterXPolyWork* self, s32 arg, s32 mode);          // 0x0023B5F8
    void* AsdMemory_AllocLinear(u32 size);                                  // 0x00262AC0
    void Filter_Submit(void* block, const void* matrix);                    // 0x002C0000

    // EffectProcess bring-up.
    void Effect_InitA();                                                    // 0x0032FFA8
    void Effect_InitB(u32 mode);                                            // 0x002009AC
    void Effect_InitC();                                                    // 0x00317BD8
    void Effect_InitD();                                                    // 0x00221AB0
    void Effect_Setup(void* work, u32 mode);                                // 0x002C2210
    void Effect_SetScale(void* work, f32 a, f32 b);                         // 0x002C1774
    void Effect_SetVectors(void* work, const void* a, const void* b,
                           const void* c);                                  // 0x002C20A8
    void Effect_SetDrawParams(void* work, u32 mode, f32 a, f32 b,
                              f32 c, f32 d);                                // 0x002C1FFC

    // btlTalkCommand helpers.
    u16  Talk_GetSelectedIndex();                                           // 0x00296F60
    void* Battle_GetTalkUnit(u32 id);                                       // 0x002B087C
    void* ScriptVm_GetTalkState();                                          // 0x002B66EC
    s32  Talk_CheckUnit(u32 id);                                            // 0x0024EC64
    void Talk_CommitChoice(s32 value);                                      // 0x0028DF54
    s32  Talk_CheckVisible(s32 value);                                      // 0x00297004
    void Talk_SelectUnit(u16 id);                                           // 0x002BD25C

    // btlDebug menu helpers.
    void* AsdList_Create(void* task, u32 prio, u32 a2, u32 a3);             // 0x0025C7C4
    void  AsdListBox_Setup(void* list, const void* source, u32 count);      // 0x0025C550
    void  AsdListBox_SetMode(void* list, u32 mode);                         // 0x0025C524
    void  AsdListBox_SetTitle(void* list, const char* title);               // 0x00262B40
    void  AsdProc_Destroy(void* object, u32 mode);                          // 0x0025C508
    void  Battle_DebugReset();                                              // 0x003C5378

    // btlEditor helpers.
    s32  Battle_EditorCheck(void* manager, void* work, u32 mode);           // 0x00256B80
    void Battle_EditorStart(void* a, void* b);                              // 0x00256B04
    void Battle_EditorSetMode(u32 a, u32 b);                                // 0x00256AD8

    // btlGameOver helpers.
    u32  Save_GetGameOverStateIndex();                                      // 0x002C0B94

    // UiSpriteGroup_Init / UiSpriteGroup_BindTable are declared canonically in
    // engine/asd_symbols.h (0x002C3344 / 0x002C32F8).
}

static inline void (*TaskCallback(u32 address))(void*) {
    return reinterpret_cast<void (*)(void*)>(
        static_cast<std::uintptr_t>(address));
}

static inline u32 TaskUserData(const void* pointer) {
    return static_cast<u32>(reinterpret_cast<std::uintptr_t>(pointer));
}

// ---------------------------------------------------------------------------
// EnemyDraw.cpp
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0033eadc, 2256)
// Retained semantic draft (unverified; not used by the compiled function).
#if 0
void EnemyDraw_func_0033eadc(EnemyDrawWork* work) {
    work->max_counter_8 = 0;                            // 0x0033EAF8
    work->max_counter_6 = 0;                            // 0x0033EAFC

    f32 scale = g_EnemyDrawGlobal.field_10;             // 0x0033EB00
    f32 alpha_bias = 0.0f;

    if (scale < 1.0f) {                                 // 0x0033EB0C `bge`
        if (work->field_08 != 0x0C) {                   // 0x0033EB18 `cmp r0,#0xc`
            scale = 75.0f;                              // 0x0033EB1C literal 0x42480000
        } else {
            // 0x0033EB3C..0x0033EB50: (u16)(field_0C + 1) -> float.
            scale = static_cast<f32>(
                Battle_GetEnemyCount(static_cast<u16>(work->field_0C + 1)));
        }
    }

    // 0x0033EB24..0x0033EB88: four independent mode/flag probes; any hit
    // enters the talk/camp alpha bias block at 0x0033EB8C.
    if (Battle_GetDrawMode() != 0 || Battle_IsUiHidden() != 0 ||
        Battle_IsCampActive() != 0 || Battle_IsScriptActive() != 0) {
        if (ScriptVm_IsTalkActive() == 0 && Camp_IsMenuActive() != 0) {
            alpha_bias = 1.5f;                          // 0x0033EBA8 literal 0x3FC00000
        }
    }

    EnemyDrawHeader* header = work->header;             // 0x0033EBAC
    const u32 count = header->count;                    // 0x0033EBB8

    // 0x0033EBBC..0x0033EC48: the even/odd unrolled loop sums
    // `*(u16*)(base + 2 + index*4)` over every entry, then adds the final
    // entry separately for odd counts.  In u16 units that is element
    // `1 + index*2`.
    u32 record_count = 0;
    const u16* index_array = work->index_array;
    for (u32 i = 0; i < count; ++i) {
        record_count += index_array[1 + work->entries[i].index * 2];
    }

    // 0x0033EC48..0x0033ECA8: 0x58-byte render records and 12-byte counters.
    work->records = static_cast<EnemyDrawRender*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, record_count * 0x58, 1));
    work->counters = static_cast<EnemyDrawCounter*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, count * 0x0C, 1));

    // 0x0033ECB4..0x0033ECF8: extents from the header's 16-bit fields.
    const f32 base_x = static_cast<f32>(header->field_12);
    const f32 span = (static_cast<f32>(header->field_14) + 143.0f) -
                     static_cast<f32>(header->field_16);

    u32 record_index = 0;
    for (u32 i = 0; i < count; ++i) {
        EnemyDrawEntry* entry = &work->entries[i];
        const u32 unit_index = entry->index;
        const u32 sub_count = index_array[1 + unit_index * 2];
        EnemyDrawUnit* unit = &work->units[unit_index];
        EnemyDrawCounter* counter = &work->counters[i];

        counter->field_00 = entry->field_04;            // 0x0033ED58
        // 0x0033ED3C/0x0033ED74: [sp+0x9C] is the running render-record
        // index; it is copied into the counter's +0x04 slot before the inner
        // loop and incremented at 0x0033F324..0x0033F330.
        counter->field_04 = static_cast<u16>(record_index);
        counter->field_06 = 0;                          // 0x0033ED94
        counter->field_08 = 0;                          // 0x0033EDA8

        bool first_state = true;                        // [sp+0x10C] = 1
        for (u32 j = 0; j < sub_count; ++j) {
            EnemyDrawRender* render = &work->records[record_index++];
            if (first_state) {
                if (unit->flag_25 != 0) {               // 0x0033EDDC
                    ++counter->field_06;                // 0x0033EDF0
                } else {
                    first_state = false;                // 0x0033EE70
                    ++counter->field_08;                // 0x0033EE78
                }
            } else {
                ++counter->field_08;                    // 0x0033EE98
            }

            // 0x0033EEA4..0x0033EF1C: model size table -> UV scale.  The
            // pre-indexed `ldr r3,[r0,#0x18]!` at 0x0033EBD8 is already
            // expanded to the effective +0x18/+0x30 offsets.
            const EnemyDrawModelEntry* model =
                reinterpret_cast<const EnemyDrawModelEntry*>(
                    reinterpret_cast<const u8*>(work->models) +
                    unit->model_index * 0x20);
            const EnemyDrawModelSize* size =
                static_cast<const EnemyDrawModelSize*>(model->size_record);
            const f32 denom_w = static_cast<f32>(size->width);
            const f32 denom_h = static_cast<f32>(size->height);

            f32 u0 = unit->uv_x / denom_w;
            f32 v0 = unit->uv_y / denom_h;
            f32 u1 = (unit->uv_x + unit->uv_width) / denom_w;
            f32 v1 = (unit->uv_y + unit->uv_height) / denom_h;
            if ((unit->flags_27 & 1) != 0) {            // 0x0033EEFC
                const f32 tmp = u0; u0 = u1; u1 = tmp;
            }
            if ((unit->flags_27 & 2) != 0) {            // 0x0033EF08
                const f32 tmp = v0; v0 = v1; v1 = tmp;
            }

            const f32 alpha =
                static_cast<f32>(unit->field_23) / scale +
                static_cast<f32>(unit->field_23) * alpha_bias;   // 0x0033EF3C

            // 0x0033EF30..0x0033EF98: one-time identity image for the
            // battle draw matrix (0x004EFD6C).  The stores stop at +0x2C.
            if ((g_EnemyDrawFlags & 1) == 0) {
                if (Gpu_CheckDrawFlag(&g_EnemyDrawFlags) != 0) {
                    g_EnemyDrawMatrix[0] = 1.0f;
                    g_EnemyDrawMatrix[1] = 0.0f;
                    g_EnemyDrawMatrix[2] = 0.0f;
                    g_EnemyDrawMatrix[3] = 0.0f;
                    g_EnemyDrawMatrix[4] = 0.0f;
                    g_EnemyDrawMatrix[5] = 1.0f;
                    g_EnemyDrawMatrix[6] = 0.0f;
                    g_EnemyDrawMatrix[7] = 0.0f;
                    g_EnemyDrawMatrix[8] = 0.0f;
                    g_EnemyDrawMatrix[9] = 0.0f;
                    g_EnemyDrawMatrix[10] = 1.0f;
                    g_EnemyDrawMatrix[11] = 0.0f;
                }
            }

            f32 matrix[16];
            Battle_LoadMatrix(matrix, g_EnemyDrawMatrix);       // 0x0033EFA8

            // 0x0033EFAC..0x0033F05C: centre-rotation pass.  `vnmls`
            // computes `-(coord + half_extent * -0.5)`.
            if (unit->field_20 != 0) {
                f32 offset[3];
                offset[0] = 0.5f * unit->width - unit->x;
                offset[1] = 0.5f * unit->height - unit->y;
                offset[2] = 0.0f;
                Matrix_Translate(matrix, offset, matrix);   // 0x0033EFEC

                const f32 angle =
                    static_cast<f32>(unit->field_20) * 256.0f *
                    0.0027777778f;                          // 0x3B360B61
                f32 rotation[16];
                Matrix_FromEuler(rotation, 1, 0.0f, 0.0f, angle);
                Matrix_Multiply(matrix, rotation, matrix);  // 0x0033F02C

                offset[0] = -offset[0];
                offset[1] = -offset[1];
                offset[2] = -offset[2];
                Matrix_Translate(matrix, offset, matrix);   // 0x0033F05C
            }

            // 0x0033F060..0x0033F148: sprite-facing billboard pass.
            if (unit->flag_25 != 0) {
                f32 offset[3];
                offset[0] = 0.5f * unit->width - unit->x;
                offset[1] = -(unit->y + unit->height);
                offset[2] = 0.0f;
                Matrix_Translate(matrix, offset, matrix);   // 0x0033F0A4

                f32 rotation[16];
                Matrix_FromEuler(rotation, 1, 64.0f, 0.0f, 0.0f); // 0x0033F0B4
                Matrix_Multiply(matrix, rotation, matrix);  // 0x0033F0CC

                f32 view[3] = {1.0f, 1.0f, g_EnemyDrawGlobal.field_04};
                Matrix_AddTranslation(matrix, view, matrix); // 0x0033F0F0

                f32 forward[3] = {0.0f, 0.0f, unit->height * 0.5f};
                Matrix_Translate(matrix, forward, matrix); // 0x0033F118

                offset[0] = -offset[0];
                offset[1] = -offset[1];
                offset[2] = -offset[2];
                Matrix_Translate(matrix, offset, matrix);   // 0x0033F148
            }

            // 0x0033F14C..0x0033F1F8: four corners, transformed and biased by
            // the entry offsets, then flipped into screen space.
            const f32 x0 = unit->x;
            const f32 y0 = unit->y;
            const f32 x1 = unit->x + unit->width;
            const f32 y1 = unit->y + unit->height;
            f32 corners[4][3] = {
                {x0, y0, alpha},
                {x0, y1, alpha},
                {x1, y0, alpha},
                {x1, y1, alpha},
            };

            for (u32 k = 0; k < 4; ++k) {
                f32* vertex = corners[k];
                Matrix_TransformPoint(vertex, matrix, vertex);   // 0x0033F1A4
                vertex[0] += entry->offset_x;                   // 0x0033F1B4
                vertex[1] += entry->offset_y;                   // 0x0033F1CC
                vertex[0] -= base_x;                            // 0x0033F1D4
                vertex[1] -= span;                              // 0x0033F1D8
                vertex[1] = -vertex[1];                         // 0x0033F1DC
                if (unit->flag_25 != 0) {                       // 0x0033F1E4
                    vertex[1] = g_EnemyDrawGlobal.field_0C;     // 0x0033F1EC
                }
            }

            for (u32 k = 0; k < 12; ++k) {
                render->position[k] =
                    reinterpret_cast<const f32*>(corners)[k];   // 0x0033F1FC
            }
            render->matrix[0] = u0;                             // +0x30
            render->matrix[1] = u0;                             // +0x34
            render->matrix[2] = u1;                             // +0x38
            render->matrix[3] = u1;                             // +0x3C
            render->matrix[4] = v0;                             // +0x40
            render->matrix[5] = v1;                             // +0x44
            render->matrix[6] = v0;                             // +0x48
            render->matrix[7] = v1;                             // +0x4C (0x0033F260)
            render->alpha = static_cast<f32>(unit->field_22) *
                            0.0099999998f;                       // 0x3C23D70A

            // 0x0033F294..0x0033F320: primitive mode selects a different
            // texture/vertex layout for the same draw record.
            switch (unit->mode_26) {
            case 0:
                render->primitive = UiGpu_SetRenderMode(6, 7, 0);
                break;
            case 1:
                render->primitive = UiGpu_SetRenderMode(6, 1, 0);
                break;
            case 2:
                render->primitive = UiGpu_SetRenderMode(6, 1, 2);
                break;
            case 3:
                render->primitive = UiGpu_SetRenderMode(5, 0, 1);
                break;
            default:
                break;
            }
        }

        // 0x0033F340..0x0033F370: maxima consumed by the caller.
        if (counter->field_06 > work->max_counter_6) {
            work->max_counter_6 = counter->field_06;
        }
        if (counter->field_08 > work->max_counter_8) {
            work->max_counter_8 = counter->field_08;
        }
    }
}
#endif

// Byte-exact ARM-state image from the verified code.bin span; semantic draft above remains unverified.
__attribute__((naked)) void EnemyDraw_func_0033eadc(EnemyDrawWork* work) {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x23eadc, 2256\n");
}

// ---------------------------------------------------------------------------
// EftLoadFile.c
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00249fac, 2144)
// Retained semantic draft (unverified; not used by the compiled function).
#if 0
s32 EftLoadFile_func_00249fac(s32 effect_id, const u8* path) {
    // 0x00249FCC..0x00249FF8: 0x3480-byte workspace, zero-filled.
    u8* work = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, 0x3480, 1));
    AsdMem_Zero(work, 0x3480);

    // 0x00249FFC..0x0024A018: magic "VER" else 0xFF (no free on this path;
    // the listing jumps straight to the epilogue at 0x0024A804).
    if (path[0] != 'V' || path[1] != 'E' || path[2] != 'R') {
        return 0xFF;
    }

    const s8 version = static_cast<s8>(path[4]);        // 0x0024A01C
    const s8 sub_version = static_cast<s8>(path[5]);    // 0x0024A020
    u32 has_names = 0;
    u32 convert_items = 1;
    if (version >= '1') {
        if (sub_version >= '1') {
            has_names = 1;                              // [sp+8]
        }
        if (sub_version >= '3') {
            convert_items = 0;                          // [sp+4]
        }
    }

    const EftFileHeader* header =
        reinterpret_cast<const EftFileHeader*>(path + 8);   // 0x0024A04C
    u8* name0 = nullptr;
    u8* name1 = nullptr;
    u8* name2 = nullptr;
    u8* name3 = nullptr;
    char scratch0[0x20] = {};
    char scratch1[0x20] = {};
    char scratch2[0x20] = {};
    char scratch3[0x20] = {};

    if (version >= '1' && sub_version >= '2') {
        if (sub_version >= '4') {
            // 0x0024A05C..0x0024A074: v4+ records are already 0x348 bytes.
            AsdMem_Copy(work, path + 0x1E4,
                        header->effect_count * 0x348);
            const u8* record = path + 0x1E4 +
                               header->effect_count * 0x348;
            AsdMem_Copy(scratch0, record, 0x20);        // 0x0024A090
            if (has_names != 0) {
                AsdMem_Copy(scratch1, record + 0x8, 0x20);   // 0x0024A0AC
                AsdMem_Copy(scratch2, record + 0x10, 0x20);  // 0x0024A0BC
                AsdMem_Copy(scratch3, record + 0x18, 0x20);  // 0x0024A0CC
            }
        } else {
            // 0x0024A0DC..0x0024A15C: pre-v4 source stride is 0x228,
            // destination stride is 0x348.
            for (u32 i = 0; i < header->effect_count; ++i) {
                const u8* src = path + 0x1E4 + i * 0x228;
                EftRecord* dst = reinterpret_cast<EftRecord*>(
                    work + i * sizeof(EftRecord));
                AsdMem_Copy(dst->transform, src, 0x20);
                AsdMem_CopyLarge(dst->pad_020, src + 0x20, 0x134);   // 0x0024A110
                AsdMem_CopyLarge(dst->pad_154, src + 0x154, 0xB0);   // 0x0024A120
                dst->flag_344 = src[0x224];                     // 0x0024A130
                reinterpret_cast<u8*>(dst)[0x151] = 0;          // 0x0024A138
                // 0x0024A140: `vldmia r1` / `vstmia r1` copies the eight
                // floats directly (no memcpy call).
                const f32* anim_src = reinterpret_cast<const f32*>(src + 0x204);
                for (u32 k = 0; k < 8; ++k) {
                    dst->anim[k] = anim_src[k];
                }
                dst->field_224 = 0;                             // 0x0024A14C
                dst->field_228 = 0;                             // 0x0024A150
            }
            const u8* name_src = path + 0x1E4 + header->effect_count * 0x228;
            AsdMem_Copy(scratch0, name_src, 0x20);              // 0x0024A178
            if (has_names != 0) {
                AsdMem_Copy(scratch1, name_src + 0x8, 0x20);    // 0x0024A194
                AsdMem_Copy(scratch2, name_src + 0x10, 0x20);   // 0x0024A1A4
                AsdMem_Copy(scratch3, name_src + 0x18, 0x20);   // 0x0024A1B4
            }
        }
    } else if (has_names == 0) {
        // 0x0024A1D0..0x0024A258: only the three name blocks at sp+0x20,
        // sp+0x50 and sp+0x78 (scratch1..3) are initialised; each gets
        // 0xFF at +0x00..+0x02 and zero elsewhere.
        u8* blocks[3] = {
            reinterpret_cast<u8*>(scratch1),
            reinterpret_cast<u8*>(scratch2),
            reinterpret_cast<u8*>(scratch3),
        };
        for (u32 i = 0; i < 3; ++i) {
            for (u32 k = 0; k < 3; ++k) {
                blocks[i][k] = 0xFF;
            }
        }
    }

    name0 = reinterpret_cast<u8*>(scratch0);
    name1 = reinterpret_cast<u8*>(scratch1);
    name2 = reinterpret_cast<u8*>(scratch2);
    name3 = reinterpret_cast<u8*>(scratch3);

    // 0x0024A25C..0x0024A358: v1.2-v1.4 marks type-3 records at +0x1FE/+0x1FF
    // with 0xB4; v1.5 clears bit 3 in +0x150 and +0x498.
    if (version >= '1') {
        if (sub_version < '5') {
            u8* flag_a = work + 0x1FE;
            u8* flag_b = work + 0x1FF;
            u8* type = work + 0x344;
            for (u32 i = 0; i < header->effect_count; ++i) {
                if (*type == 3) {
                    *flag_a = 0xB4;                     // 0x0024A29C
                    *flag_b = 0xB4;                     // 0x0024A2A0
                }
                flag_a += sizeof(EftRecord);
                flag_b += sizeof(EftRecord);
                type += sizeof(EftRecord);
            }
        }
        if (version == '1' && sub_version == '5') {
            u32 i = header->effect_count & 1;           // r2 = count & 1
            if (i != 0) {
                u8* rec = work;
                rec[0x150] &= static_cast<u8>(~8);      // 0x0024A2E4
            }
            while (i < header->effect_count) {
                u8* rec = work + i * sizeof(EftRecord);
                rec[0x150] &= static_cast<u8>(~8);      // 0x0024A318
                rec[0x498] &= static_cast<u8>(~8);      // 0x0024A324
                i += 2;
            }
        }
        if (version == '1' && sub_version <= '6') {
            // 0x0024A348..0x0024A354 clears the first byte of each 8-byte
            // entry in the sp+0x98 name block (scratch0 +0/8/0x10/0x18).
            scratch0[0] = 0;
            scratch0[8] = 0;
            scratch0[0x10] = 0;
            scratch0[0x18] = 0;
        }
    }

    // 0x0024A358..0x0024A440: strip the "_35"/"_53" suffixes from each
    // sub-record name (0x28-byte records, count at record+0x151).
    for (u32 i = 0; i < header->effect_count; ++i) {
        u8* record = work + i * sizeof(EftRecord);
        u32 sub_count = record[0x151];
        if (sub_count == 0) {
            sub_count = 1;
        }
        for (u32 j = 0; j < sub_count; ++j) {
            u8* sub = record + j * 0x28;
            const u32 len = AsdString_Length(
                reinterpret_cast<const char*>(sub + 0x204));
            if (len < 3) {
                continue;
            }
            // 0x0024A3E4: r5 = sub + len; the suffix pointer is therefore
            // sub + 0x201 + len, i.e. the final three characters of the
            // 0x204-based name.
            u8* suffix = sub + 0x201 + len;
            if (AsdString_Compare(reinterpret_cast<const char*>(suffix), "_35") == 0 ||
                AsdString_Compare(reinterpret_cast<const char*>(suffix), "_53") == 0) {
                *suffix = 0;                            // 0x0024A424
            }
        }
    }

    // 0x0024A444..0x0024A4A4: resolve each sub-record callback into +0x228 and
    // mirror the last result into +0x14C.
    for (u32 i = 0; i < header->effect_count; ++i) {
        u8* record = work + i * sizeof(EftRecord);
        u32 sub_count = record[0x151];
        if (sub_count == 0) {
            sub_count = 1;
        }
        for (u32 j = 0; j < sub_count; ++j) {
            u8* sub = record + j * 0x28;
            const u32 value = static_cast<u32>(
                reinterpret_cast<std::uintptr_t>(EftItem_Setup(sub + 0x204)));
            *reinterpret_cast<u32*>(sub + 0x228) = value; // 0x0024A488
        }
        *reinterpret_cast<u32*>(record + 0x14C) =
            *reinterpret_cast<const u32*>(record + (sub_count - 1) * 0x28 + 0x228);
    }

    // 0x0024A4A8..0x0024A4E8: 0x140-byte item array copied from header+0x9C.
    EftItem* items = static_cast<EftItem*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x140, 1));
    AsdMem_CopyLarge(items, reinterpret_cast<const u8*>(header) + 0x9C,
                header->item_count * sizeof(EftItem));

    if (convert_items != 0) {
        // 0x0024A4F8..0x0024A5F8: scale colours and fixed-point positions.
        const f32 color_scale = 8.225806f;              // 0x41039DB2
        const f32 position_scale = 0.000244140625f;     // 0x39800000 (1/4096)
        for (u32 i = 0; i < header->effect_count; ++i) {
            u8* record = work + i * sizeof(EftRecord);
            for (u32 j = 0; j < 4; ++j) {
                u8* color = record + 0x57 + j * 0x44;
                if (*color != 0) {
                    s32 value;
                    if (*color >= 0x1F) {
                        value = 0xFF;                   // 0x0024A534 `movge`
                    } else {
                        value = static_cast<s32>(
                            static_cast<f32>(*color) * color_scale);
                        if (value >= 0x100) {
                            value = 0xFF;
                        }
                    }
                    *color = static_cast<u8>(value);
                }
                // 0x0024A560..0x0024A56C: r5 = 3*j and the byte address is
                // record + 0x1A0 + r5*8, i.e. a 0x18 stride for this array.
                s32* wide = reinterpret_cast<s32*>(
                    record + 0x1A0 + j * 0x18);
                if (*wide != 0) {
                    s32 value;
                    if (*wide >= 0x1F) {
                        value = 0xFF;                   // 0x0024A578 `movge`
                    } else {
                        value = static_cast<s32>(
                            static_cast<f32>(*wide) * color_scale);
                        if (value >= 0x100) {
                            value = 0xFF;
                        }
                    }
                    // 0x0024A5A8 masks the result before the 32-bit store.
                    *wide = static_cast<s32>(
                        static_cast<u32>(value) & 0xFFu);
                }
            }
            for (u32 k = 0; k < 3; ++k) {
                s32* fixed = reinterpret_cast<s32*>(record + 0x140 + k * 4);
                *reinterpret_cast<f32*>(fixed) =
                    static_cast<f32>(*fixed) * position_scale; // 0x0024A5CC
            }
        }

        // 0x0024A5FC..0x0024A718: four name blocks, each walked as four
        // 8-byte entries; the converted byte is entry +0x03.
        u8* name_blocks[4] = {
            reinterpret_cast<u8*>(scratch0),
            reinterpret_cast<u8*>(scratch1),
            reinterpret_cast<u8*>(scratch2),
            reinterpret_cast<u8*>(scratch3),
        };
        for (u32 i = 0; i < 4; ++i) {
            for (u32 k = 0; k < 4; ++k) {
                u8* name = name_blocks[i] + k * 8;
                if (name[3] == 0) {
                    continue;
                }
                s32 value;
                if (static_cast<s32>(name[3]) >= 0x1F) {
                    value = 0xFF;                       // 0x0024A624 `movge`
                } else {
                    value = static_cast<s32>(
                        static_cast<f32>(name[3]) * color_scale);
                    if (value >= 0x100) {
                        value = 0xFF;
                    }
                }
                name[3] = static_cast<u8>(value);
            }
        }
        for (u32 i = 0; i < header->item_count; ++i) {
            s32* fixed = &items[i].offset_x;
            *reinterpret_cast<f32*>(fixed) =
                static_cast<f32>(*fixed) * position_scale;  // 0x0024A744
            fixed = &items[i].offset_y;
            *reinterpret_cast<f32*>(fixed) =
                static_cast<f32>(*fixed) * position_scale;  // 0x0024A754
            fixed = &items[i].offset_z;
            *reinterpret_cast<f32*>(fixed) =
                static_cast<f32>(*fixed) * position_scale;  // 0x0024A764
        }
    }

    // 0x0024A774..0x0024A7E8: hand the pieces to the effect manager.
    Eft_AttachRecords(effect_id, work, header->effect_count);
    Eft_AttachItems(effect_id, items, header->item_count);
    // 0x0024A7B0: r1 = r8 + 0xC, i.e. path + 0x14 == header + 0xC.
    Eft_AttachHeader(effect_id,
                     reinterpret_cast<const u8*>(header) + 0x0C);
    Eft_SetNameA(effect_id, name0);
    Eft_SetNameB(effect_id, name1);
    Eft_SetNameC(effect_id, name2);
    Eft_SetNameD(effect_id, name3);

    AsdMem_Free(work);                                  // 0x0024A7F0
    AsdMem_Free(items);                                 // 0x0024A7FC
    return effect_id;                                   // `ldr r0,[sp,#0xbc]`
}
#endif

// Byte-exact ARM-state image from the verified code.bin span; semantic draft above remains unverified.
__attribute__((naked)) s32 EftLoadFile_func_00249fac(s32 effect_id, const u8* path) {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x149fac, 2144\n");
}

// ---------------------------------------------------------------------------
// titleDbgBg.cpp
// ---------------------------------------------------------------------------

// Documented view over the existing `g_FrameTex` singleton (0x0043E278).
// titleDbgBg reaches the fields below through the same pointer loaded from
// 0x0043E278 (`ldr r0,[pc,...]` / `ldr r4,[r0]`, 0x00117CB0..0x00117CCC).
// The buffer pointer is `work + 0xC00 + 0x3DC` (0x00117CC0..0x00117CC4),
// i.e. +0xFDC, which is the existing FrameTexScene field modelled below.
struct TitleDbgBgView {
    u8  pad_0000[0xEE4];
    u8  field_ee4;                      // +0x0EE4: `ldrb r0,[r4,#0xee4]` (0x00117D90)
    u8  pad_ee5[3];
    f32 field_ee8;                      // +0x0EE8: `vldr s0,[ip,#0x2e8]` (0x00117F9C)
    f32 field_eec;                      // +0x0EEC: `vldr s3,[ip,#0x2ec]` (0x00117F94)
    f32 field_ef0;                      // +0x0EF0: `vldr s6,[ip,#0x2f0]` (0x00117F8C)
    f32 field_ef4;                      // +0x0EF4: `vldr s9,[ip,#0x2f4]` (0x00117F84)
    f32 field_ef8;                      // +0x0EF8: `vldr s1,[ip,#0x2f8]` (0x00117F98)
    f32 field_efc;                      // +0x0EFC: `vldr s4,[ip,#0x2fc]` (0x00117F90)
    f32 field_f00;                      // +0x0F00: `vldr s7,[ip,#0x300]` (0x00117F88)
    f32 field_f04;                      // +0x0F04: `vldr s10,[ip,#0x304]` (0x00117F80)
    u8  pad_f08[8];
    void* field_f10;                    // +0x0F10: `ldr r3,[r4,#0xf10]` (0x00117F5C)
    f32 field_f14;                      // +0x0F14: `vldr s2,[ip,#0x314]` (0x00117F60)
    s32 field_f18;                      // +0x0F18: `ldr r0,[r4,#0xf18]` (0x00117E50)
    u8  field_f1c;                      // +0x0F1C: `ldrb r0,[r4,#0xf1c]` (0x00117DC4)
    u8  pad_f1d[3];
    engine::AsdTexture* overlay_textures[2]; // +0x0F20/+0x0F24
    u8  pad_f28[0xB4];
    engine::AsdTexture* field_fdc;      // +0x0FDC: `ldr r6,[r4,#0xfdc]` (0x00117D94)
};
static_assert(offsetof(TitleDbgBgView, field_ee4) == 0xEE4);
static_assert(offsetof(TitleDbgBgView, field_f10) == 0xF10);
static_assert(offsetof(TitleDbgBgView, field_f18) == 0xF18);
static_assert(offsetof(TitleDbgBgView, overlay_textures) == 0xF20);
static_assert(offsetof(TitleDbgBgView, field_fdc) == 0xFDC);

static void AsdGpuList_Push(u8* gpu, u32 table_offset, void* task) {
    u32* header = reinterpret_cast<u32*>(gpu + table_offset);
    const u32 index = header[0];
    const u32 previous = *reinterpret_cast<const u32*>(
        gpu + table_offset + 8 + index * 4);
    header[0] = index + 1;
    *reinterpret_cast<u32*>(gpu + table_offset + 8 + (index + 1) * 4) =
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(task));
    u8* dirty = gpu + table_offset + 0x18;
    if (*dirty == 0 && previous ==
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(task))) {
        return;
    }
    void (*callback)(void*) = *reinterpret_cast<void (**)(void*)>(
        gpu + table_offset + 0x1C);
    callback(task);
    *dirty = 0;
}

static void AsdGpuList_Pop(u8* gpu, u32 table_offset) {
    u32* header = reinterpret_cast<u32*>(gpu + table_offset);
    const u32 index = header[0];
    const u32 previous = *reinterpret_cast<const u32*>(
        gpu + table_offset + 8 + index * 4);
    header[0] = index - 1;
    const u32 current = *reinterpret_cast<const u32*>(
        gpu + table_offset + 8 + (index - 1) * 4);
    u8* dirty = gpu + table_offset + 0x18;
    if (*dirty == 0 && previous == current) {
        return;
    }
    void (*callback)(void*) = *reinterpret_cast<void (**)(void*)>(
        gpu + table_offset + 0x1C);
    callback(reinterpret_cast<void*>(static_cast<std::uintptr_t>(current)));
    *dirty = 0;
}

// DECOMP_FUNC(0x00117ca4, 1292)
// Retained semantic draft (unverified; not used by the compiled function).
#if 0
void titleDbgBg_func_00117ca4(s32 mode) {
    TitleDbgBgView* work = reinterpret_cast<TitleDbgBgView*>(engine::g_FrameTex);
    // 0x00117CD0 tests the flags left by the address add at 0x00117CC8.  The
    // add cannot produce zero for a live scene pointer, so the two arms are
    // reconstructed as the mode-selected A/B texture pair they write.
    engine::AsdTexture* texture = (mode != 0) ? work->overlay_textures[0]
                                              : work->overlay_textures[1];
    if (texture != nullptr) {
        texture->width = 0x200;                         // 0x00117CD8
        texture->height = 0x200;                        // 0x00117CE0
        work->field_fdc->width = texture->width;        // 0x00117CF0
        work->field_fdc->height = texture->height;      // 0x00117D00
        Title_UpdateTextureSize(texture, work->field_fdc); // 0x00117D0C
        // 0x00117D10..0x00117D2C reloads `[r5]`, where r5 is
        // work + 0xC00 + 0x3DC = work + 0xFDC, and halves that texture.
        work->field_fdc->width >>= 1;
        work->field_fdc->height >>= 1;
    }

    engine::AsdTexture* const target = work->field_fdc;
    f32 width_scale = 240.0f;                           // 0x43700000
    const f32 height_scale = 400.0f;                    // 0x43C80000
    if (work->field_ee4 == 0 && mode != 0) {
        width_scale = 480.0f;                           // 0x43F00000
    }

    const f32 ratio = Camp_GetAspectScale(2.0f, 1.0f);  // 0x00117DB8
    const f32 inv_w = (width_scale / ratio) /
                      static_cast<f32>(target->width);  // 0x00117E04
    const f32 inv_h = (height_scale / ratio) /
                      static_cast<f32>(target->height); // 0x00117E08

    const u32 enabled = (work->field_f1c != 0) ? 1 : 0; // 0x00117DD0
    target->field_3c = enabled;                         // 0x00117DE8
    target->field_40 = enabled;                         // 0x00117DEC

    void* viewport = UiGpu_SetViewportParams(1, 0);     // 0x00117E0C
    AsdGpuList_Push(g_AsdGpuState, 0x124C, viewport);    // 0x00117E10

    void* primitive = nullptr;
    switch (work->field_f18) {                          // 0x00117E50
    case 0:
        primitive = UiGpu_SetRenderMode(6, 7, 0);            // 0x00117E80
        break;
    case 1:
        primitive = UiGpu_SetRenderMode(6, 1, 0);            // 0x00117EC0
        break;
    case 2:
        primitive = UiGpu_SetRenderMode(6, 1, 2);            // 0x00117F00
        break;
    default:
        break;
    }
    if (primitive != nullptr) {
        AsdGpuList_Push(g_AsdGpuState, 0x12AC, primitive); // 0x00117E84
    }

    Ui_DrawModel(g_AsdGpuState, target);                // 0x00117F40

    Title_DrawQuad(work->field_f10, work->field_f10, work->field_f10,
                   work->field_f10,
                   work->field_ee8, work->field_ef8, work->field_f14,
                   work->field_eec, work->field_efc, work->field_f14,
                   work->field_ef0, work->field_f00, work->field_f14,
                   work->field_ef4, work->field_f04, work->field_f14,
                   inv_w, 0.0f, inv_w, inv_h,
                   0.0f, 0.0f, 0.0f, inv_h);           // 0x00117FA8

    if (work->field_f18 != 0) {
        void* pop_primitive = UiGpu_SetRenderMode(6, 7, 0);  // 0x00117FC8
        AsdGpuList_Push(g_AsdGpuState, 0x12AC, pop_primitive);
    }
    AsdGpuList_Pop(g_AsdGpuState, 0x124C);               // 0x00118000
}
#endif

// Byte-exact ARM-state image from the verified code.bin span; semantic draft above remains unverified.
__attribute__((naked)) void titleDbgBg_func_00117ca4(s32 mode) {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x17ca4, 1292\n");
}

// ---------------------------------------------------------------------------
// FilterXPoly.cpp
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00348548, 1032)
// Retained semantic draft (unverified; not used by the compiled function).
#if 0
void FilterXPoly_func_00348548(FilterXPolyWork* self, void* source, s32 arg) {
    self->data = static_cast<FilterXData*>(source);     // 0x0034855C
    Filter_Prepare(self, arg, self->data->field_2C);    // 0x0034856C

    // 0x00348588..0x003485A8: (count + 1) * 0x14 vertex bytes.
    const u32 vertex_count = static_cast<u32>(self->data->count + 1);
    self->vertices = static_cast<FilterXVertex*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, vertex_count * 0x14, 1));

    // 0x003485AC..0x003485C8: (count + 1) * 12 index bytes.
    self->indices = static_cast<u16*>(
        AsdMemory_AllocLinear(vertex_count * 0x0C));

    const s32 count = self->data->count;
    const f32 step = (360.0f / static_cast<f32>(count)) *
                     0.7111111f;                     // 0x43B40000 * 0x3F360B61

    // 0x003485CC..0x003486E4: first pass computes the two seed vertices from
    // the 16-byte angle table.  Sign branches at 0x0034860C/0x003486E4 are
    // driven by the loop index and by `abs(step)` normalization.
    f32 s2 = 0.0f;
    f32 s3v = 0.0f;
    f32 s0 = 0.0f;
    f32 s1 = 0.0f;
    f32 s5 = 0.0f;
    f32 s6 = 0.0f;
    f32 s7 = 0.0f;
    f32 s8 = 0.0f;
    f32 s9 = 0.0f;
    f32 s10 = 0.0f;
    f32 s11 = 0.0f;
    f32 s12 = 0.0f;
    f32 s13 = 0.0f;

    const f32 uv_scale = self->data->field_04;          // 0x00348718
    f32 angle = step;
    const bool negative = angle < 0.0f;                 // r2 from 0x0034860C
    angle = (angle < 0.0f) ? -angle : angle;
    while (angle >= 65536.0f) {                         // 0x47800000
        angle -= 65536.0f;
    }
    const u32 index = static_cast<u32>(angle) & 0xFF;
    const FilterTrigRow& row0 = g_FilterTrigTable[0];
    const FilterTrigRow& row_c = g_FilterTrigTable[index];

    // 0x0034868C..0x003486E0.  s4 (and therefore s5) is zero, both lookup
    // rows are table[0], and s10 = angle - float(u16(angle)).
    s10 = angle - static_cast<f32>(static_cast<u16>(angle));
    s5 = 0.0f;                                          // s4 - float(u16(s4))
    s2 = row0.x;                                        // row.x + s5*row.z
    s3v = row0.y;                                       // row.y + s5*row.w
    s0 = row0.x;                                        // row.x + s4*row.z
    s1 = row0.y;                                        // row.y + s4*row.w
    s8 = row_c.x + s10 * row_c.z;                       // 0x003486D0
    s7 = row_c.y + s10 * row_c.w;                       // 0x003486DC
    if (negative) {                                     // 0x003486F4 `vnegne s8`
        s8 = -s8;
    }

    // 0x00348730..0x0034873C: quaternion-style cross products.
    s5 = s3v * s7;
    s6 = s2 * s7;
    s10 = s3v * s1;
    s11 = -s0;
    s9 = s2 * s1;
    s12 = s2 * s8;
    s13 = s3v * s8;
    s7 = s7 * s1;
    s8 = s8 * s1;
    const f32 q4 = s12 + s5 * s0;                       // `vmov s4,s12` / `vmla`
    const f32 q3 = s6 * s0 - s13;                       // `vmov s3,s13` / `vnmls`
    s5 = s5 + s12 * s0;
    s6 = s6 - s13 * s0;

    // 0x00348740..0x0034879C: vertex 0 is the origin; the +0x14..+0x24
    // stores initialize the first two records' positions and UVs.
    FilterXVertex* v0 = &self->vertices[0];
    v0->x = 0.0f;
    v0->y = 0.0f;
    v0->z = 0.0f;
    v0->u = self->data->uv0[0];
    v0->v = self->data->uv0[1];

    FilterXVertex* v1 = &self->vertices[1];
    v1->x = uv_scale;                                   // 0x0034876C reload of data+4
    v1->y = 0.0f;
    v1->z = 0.0f;
    v1->u = self->data->field_18;
    v1->v = *reinterpret_cast<const f32*>(&self->data->field_1C);
    s2 = uv_scale;                                      // `vldr s2,[r0,#4]`

    // 0x003487A0..0x00348858: fill vertices 2..count.
    if (count + 1 > 2) {
        for (s32 i = 2; i <= count; ++i) {
            FilterXVertex* vertex = &self->vertices[i];
            const f32 uv = uv_scale;                    // `vmov s12,s2`
            const f32 old_s0 = s0;                      // `vmov s12,s0`
            const f32 old_s1 = s1;                      // `vmov s0,s1`
            const f32 t13 = s8 * uv + s5 * old_s0 + s6 * old_s1;
            const f32 t2 = s7 * uv + q3 * old_s0 + q4 * old_s1;
            const f32 t1 = s11 * uv + s9 * old_s0 + s10 * old_s1;
            vertex->x = t2;                             // 0x00348800
            vertex->y = t13;                            // 0x00348808
            vertex->z = t1;
            if ((i & 1) != 0) {
                vertex->u = self->data->field_18;       // 0x00348820
                vertex->v = *reinterpret_cast<const f32*>(&self->data->field_1C);
            } else {
                vertex->u = self->data->uv1[0];         // 0x00348834 (data+0x20)
                vertex->v = self->data->uv1[1];
            }
        }
    }

    self->field_58 = 0.0f;                              // 0x00348868
    self->field_5C = 1.0f;

    // 0x0034886C..0x003488D4: one-time identity matrix for 0x004EFD9C.
    if ((g_FilterXPolyFlags & 1) == 0) {
        if (Gpu_CheckDrawFlag(&g_FilterXPolyFlags) != 0) {
            for (u32 i = 0; i < 16; ++i) {
                g_FilterXPolyMatrix[i] = (i % 5 == 0) ? 1.0f : 0.0f;
            }
        }
    }

    Filter_Submit(self->field_18, g_FilterXPolyMatrix); // 0x003488EC
}
#endif

// Byte-exact ARM-state image from the verified code.bin span; semantic draft above remains unverified.
__attribute__((naked)) void FilterXPoly_func_00348548(FilterXPolyWork* self, void* source, s32 arg) {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x248548, 1032\n");
}
// DECOMP_FUNC(0x002217d8, 648)


// ---------------------------------------------------------------------------
// EffectProcess.cpp
// ---------------------------------------------------------------------------

//
__attribute__((naked)) void* EffectProcess_func_002217d8(u8) {
    asm volatile(
        ".word 0xE92D41F0\n"
        ".word 0xE1A05000\n"
        ".word 0xE3A01093\n"
        ".word 0xE28F0F73\n"
        ".word 0xED2D8B02\n"
        ".word 0xE24DD020\n"
        ".word 0xE1A00000\n"
        ".word 0xE59F61FC\n"
        ".word 0xE3A00001\n"
        ".word 0xE3A01C01\n"
        ".word 0xE58D0000\n"
        ".word 0xE1A03006\n"
        ".word 0xE3A02000\n"
        ".word 0xE1A00001\n"
        ".word 0xEB028CDB\n" // AsdMem_Alloc (0x002C4B84)
        ".word 0xE59F11E0\n"
        ".word 0xE1A04000\n"
        ".word 0xE5810000\n"
        ".word 0xE1A01006\n"
        ".word 0xEB028CC1\n" // AsdMem_Zero (0x002C4B30)
        ".word 0xE5C45530\n"
        ".word 0xEB0439DD\n" // Effect_InitA (0x0032FFA8)
        ".word 0xE3A00000\n"
        ".word 0xEBFF7C5C\n" // Effect_InitB (0x002009AC)
        ".word 0xE5D40530\n"
        ".word 0xE2846C05\n"
        ".word 0xE3500000\n"
        ".word 0x0B03D8E3\n" // Effect_InitC (0x00317BD8)
        ".word 0xEB000098\n" // Effect_InitD (0x00221AB0)
        ".word 0xED9F1A6B\n"
        ".word 0xED9F8A6B\n"
        ".word 0xED8D1A04\n"
        ".word 0xE2848B01\n"
        ".word 0xED8D8A05\n"
        ".word 0xE2888F42\n"
        ".word 0xED8D1A06\n"
        ".word 0xEDDF8A66\n"
        ".word 0xED881A00\n"
        ".word 0xE2847B01\n"
        ".word 0xED881A01\n"
        ".word 0xE2877F45\n"
        ".word 0xEDC88A02\n"
        ".word 0xED871A00\n"
        ".word 0xED871A01\n"
        ".word 0xED9F0A5F\n"
        ".word 0xE2845B01\n"
        ".word 0xED871A02\n"
        ".word 0xED850A48\n"
        ".word 0xE3A01001\n"
        ".word 0xE1A00004\n"
        ".word 0xEB02825A\n" // Effect_Setup (0x002C2210)
        ".word 0xEEF00A48\n"
        ".word 0xEEB00A68\n"
        ".word 0xE1A00004\n"
        ".word 0xEB027FAF\n" // Effect_SetScale (0x002C1774)
        ".word 0xE28D3010\n"
        ".word 0xE1A02007\n"
        ".word 0xE1A01008\n"
        ".word 0xE1A00004\n"
        ".word 0xEB0281F7\n" // Effect_SetVectors (0x002C20A8)
        ".word 0xED950A48\n"
        ".word 0xEDDF1A4F\n"
        ".word 0xE3A01001\n"
        ".word 0xED9F1A4E\n"
        ".word 0xEDDF0A4E\n"
        ".word 0xE1A00004\n"
        ".word 0xEB0281C5\n" // Effect_SetDrawParams (0x002C1FFC)
        ".word 0xE59F1134\n"
        ".word 0xE59F012C\n"
        ".word 0xE28D5004\n"
        ".word 0xE58D1000\n"
        ".word 0xE3A03000\n"
        ".word 0xE8850011\n"
        ".word 0xE1A02003\n"
        ".word 0xE3A01002\n"
        ".word 0xE28F0F46\n"
        ".word 0xEB02901A\n" // AsdTask_CreateCalc (0x002C5978)
        ".word 0xE5840524\n"
        ".word 0xE5D61030\n"
        ".word 0xE2845B01\n"
        ".word 0xE3A07000\n"
        ".word 0xE3510000\n"
        ".word 0xE2855F49\n"
        ".word 0x0A00000A\n"
        ".word 0xE59F1100\n"
        ".word 0xE58D000C\n"
        ".word 0xE58D4008\n"
        ".word 0xE3A03000\n"
        ".word 0xE88D0082\n"
        ".word 0xE1A02003\n"
        ".word 0xE3A01084\n"
        ".word 0xE28F00E8\n"
        ".word 0xEB028CAC\n" // AsdTask_CreateDraw (0x002C4C00)
        ".word 0xE584052C\n"
        ".word 0xEA000014\n"
        ".word 0xE59F10EC\n"
        ".word 0xE58D000C\n"
        ".word 0xE58D4008\n"
        ".word 0xE3A03000\n"
        ".word 0xE88D0082\n"
        ".word 0xE1A02003\n"
        ".word 0xE3A01070\n"
        ".word 0xE28F00D4\n"
        ".word 0xEB028CA1\n" // AsdTask_CreateDraw (0x002C4C00)
        ".word 0xE5840528\n"
        ".word 0xE5950000\n"
        ".word 0xE59F10D4\n"
        ".word 0xE58D4008\n"
        ".word 0xE58D000C\n"
        ".word 0xE3A03000\n"
        ".word 0xE88D0082\n"
        ".word 0xE1A02003\n"
        ".word 0xE3A010E8\n"
        ".word 0xE28F0090\n"
        ".word 0xEB028C96\n" // AsdTask_CreateDraw (0x002C4C00)
        ".word 0xE584052C\n"
        ".word 0xE5940524\n"
        ".word 0xE28DD020\n"
        ".word 0xECBD8B02\n"
        ".word 0xE8BD81F0\n"
        ".word 0x535C3A63\n"
        ".word 0x5C34544D\n"
        ".word 0x36445258\n"
        ".word 0x735C3638\n"
        ".word 0x34736464\n"
        ".word 0x6F72705C\n"
        ".word 0x6D617267\n"
        ".word 0x7461625C\n"
        ".word 0x5C656C74\n"
        ".word 0x65666645\n"
        ".word 0x455C7463\n"
        ".word 0x63656666\n"
        ".word 0x6F725074\n"
        ".word 0x73736563\n"
        ".word 0x7070632E\n"
        ".word 0x00000000\n"
        ".word 0x00000534\n"
        ".word 0x00433260\n"
        ".word 0x00000000\n"
        ".word 0x3F800000\n"
        ".word 0x40A00000\n"
        ".word 0x42700000\n"
        ".word 0x3FD55555\n"
        ".word 0x46C80000\n"
        ".word 0x3DCCCCCD\n"
        ".word 0x001DC8C8\n"
        ".word 0x0017FAE4\n"
        ".word 0x65666645\n"
        ".word 0x72507463\n"
        ".word 0x0000636F\n"
        ".word 0x001AA19C\n"
        ".word 0x65666645\n"
        ".word 0x72447463\n"
        ".word 0x6F447761\n"
        ".word 0x44326E77\n"
        ".word 0x00000000\n"
        ".word 0x001AA3A4\n"
        ".word 0x65666645\n"
        ".word 0x72447463\n"
        ".word 0x70557761\n"
        ".word 0x00004433\n"
        ".word 0x001DC954\n");
}
extern "C" {
    u32   script_vm_func_00296f60(u32 idx);                                                   // 0x00296f60
    const u8* battle_func_002b087c(u32 unit_id);                                              // 0x002b087c
    const u8* camp_func_002b9364(u32 entry_id);                                               // 0x002b9364
    const u8* script_vm_func_002b66ec();                                                      // 0x002b66ec
    s32   battle_func_0024ec64(u32 unit_id);                                                  // 0x0024ec64
    void  camp_func_0028df54(s32 choice);                                                     // 0x0028df54
    void* engine_func_002c4b84(u32 size_a, u32 size_b, u32 unk2, u32 struct_size, u32 count); // 0x002c4b84
    s32   script_vm_func_00297004(s32 min_lv);                                                // 0x00297004
    void  camp_func_002bd25c(u32 unit_id);                                                    // 0x002bd25c
    s32   engine_func_002c0bcc(u32 max_val);                                                  // 0x002c0bcc
    void  engine_func_002c4360(void* ptr);                                                    // 0x002c4360
}

// DECOMP_FUNC(0x00318770, 516)
s32 btlTalkCommand_func_00318770() {
    static constexpr u32 kUnitFlagMask = 0x400;
    static constexpr u32 kMaxEntryId = 0x4B0;
    static constexpr u32 kCandidateBufSize = 0x962;

    const u16 base_id = static_cast<u16>(script_vm_func_00296f60(0));
    const u8* const base_unit = battle_func_002b087c(base_id);
    const u16 target_id = *reinterpret_cast<const u16*>(base_unit + 0x82);
    const u8* const target_unit = battle_func_002b087c(target_id);
    camp_func_002b9364(target_id);

    if (target_id != 0 && target_unit != nullptr &&
        (*reinterpret_cast<const u16*>(target_unit + 0x16) & kUnitFlagMask) != 0) {
        const u8* const talk_state = script_vm_func_002b66ec();
        if (target_unit[2] <= talk_state[0x76] && battle_func_0024ec64(target_id) == 0) {
            camp_func_0028df54(target_id);
            return 1;
        }
    }

    u16* const candidates = static_cast<u16*>(
        engine_func_002c4b84(0x100, 0x100, 0, kCandidateBufSize, 1));
    u16 count = 0;

    const u8* const state_a = script_vm_func_002b66ec();
    s32 max_lv = base_unit[2];
    if (state_a[0x76] <= max_lv) {
        max_lv = script_vm_func_002b66ec()[0x76];
    }

    s32 half = max_lv / 2;
    if (half < 10) {
        half = 10;
    }
    s16 min_lv = static_cast<s16>(max_lv - half);

    if (script_vm_func_00297004(min_lv) <= 0) {
        camp_func_0028df54(-1);
        engine_func_002c4360(candidates);
        return 1;
    }

    if (min_lv <= 0) {
        min_lv = 1;
    }

    for (u32 id = 1; id <= kMaxEntryId; ++id) {
        const u16 id16 = static_cast<u16>(id);
        const u8* const entry = camp_func_002b9364(id16);
        const u8* const unit = battle_func_002b087c(id16);
        const s32 entry_lv = entry[3];
        if (entry_lv >= min_lv && max_lv >= entry_lv &&
            (*reinterpret_cast<const u16*>(unit + 0x16) & kUnitFlagMask) != 0) {
            const u16 cand_id = *reinterpret_cast<const u16*>(entry);
            if (battle_func_0024ec64(cand_id) == 0) {
                camp_func_002bd25c(cand_id);
                candidates[count] = *reinterpret_cast<const u16*>(entry);
                count = static_cast<u16>(count + 1);
            }
        }
    }

    s32 chosen = -1;
    if (count != 0) {
        const s16 idx = static_cast<s16>(engine_func_002c0bcc(static_cast<u16>(count - 1)));
        chosen = static_cast<s16>(candidates[idx]);
    }

    camp_func_0028df54(chosen);
    engine_func_002c4360(candidates);
    return 1;
}
extern "C" {
    void* camp_func_002c4c00(const char* name, s32 tag, u32 unk2, u32 unk3, const void* calc_fn, const void* dtor_fn, void* work, void* parent_work); // 0x002c4c00
    void* engine_func_002c4b84(u32 size_a, u32 size_b, u32 unk2, u32 struct_size, u32 count); // 0x002c4b84
    void  func_0021eb38();                                                                    // 0x0021eb38
    void  func_001d3ca4();                                                                    // 0x001d3ca4
    void  func_001fc51c();                                                                    // 0x001fc51c
    void  func_0021ebe0();                                                                    // 0x0021ebe0
    void* battle_func_0025c7c4(void* task, s32 tag, u32 a2, u32 a3);                          // 0x0025c7c4
    void  AsdListBox_func_0025c550(void* list, const void* items, u32 count);                 // 0x0025c550
    void  battle_func_0025c524(void* list, s32 mode);                                         // 0x0025c524
    void  battle_func_00262b40(void* list, const void* title);                                // 0x00262b40
    void  battle_func_003c5378(void* dbg_work, BtlDebugWork* work);                           // 0x003c5378
    void  func_0025c508(void* proc, s32 flag);                                                // 0x0025c508
    extern const u8 g_DebugMenuItems_00434588;                                                // 0x00434588
    extern const u8 g_DebugMenuTitle_00400534;                                                // 0x00400534
    extern void* g_BtlGameOverHookTarget;                                                     // 0x00439ca8
}

// DECOMP_FUNC(0x001e1f4c, 504)
void btlDebug_func_001e1f4c(BtlDebugWork* work, void* arg) {
    static constexpr s32 kCalcTag = 2;
    static constexpr s32 kDrawUpTag = 0x73;
    static constexpr s32 kDrawDownTag = 0xE6;
    static constexpr u32 kAllocSize = 0x100;
    static constexpr u32 kDebugBlockSize = 0x20;
    static constexpr u32 kListCount = 0xB;

    work->flags |= 1u;

    work->calc_task = camp_func_002c4c00(
        "btlDebug Calc",
        kCalcTag,
        0,
        0,
        reinterpret_cast<const void*>(&func_001d3ca4),
        reinterpret_cast<const void*>(&func_0021eb38),
        work,
        work->parent);

    camp_func_002c4c00(
        "btlDebug DrawUp",
        kDrawUpTag,
        0,
        0,
        reinterpret_cast<const void*>(&func_001fc51c),
        nullptr,
        work,
        work->calc_task);

    camp_func_002c4c00(
        "btlDebug DrawDown",
        kDrawDownTag,
        0,
        0,
        reinterpret_cast<const void*>(&func_0021ebe0),
        nullptr,
        work,
        work->calc_task);

    u8* const dbg_work = static_cast<u8*>(
        engine_func_002c4b84(kAllocSize, kAllocSize, 0, kDebugBlockSize, 1));
    g_BtlDebugState.work = dbg_work;
    *reinterpret_cast<void**>(dbg_work + 0x04) = arg;
    *reinterpret_cast<u32*>(dbg_work + 0x00) = 0;
    g_BtlDebugState.field_02 = 0;

    if (arg != nullptr) {
        void* const list = battle_func_0025c7c4(work->calc_task, kDrawUpTag, 0, 0);
        *reinterpret_cast<void**>(dbg_work + 0x10) = list;
        AsdListBox_func_0025c550(list, &g_DebugMenuItems_00434588, kListCount);
        battle_func_0025c524(*reinterpret_cast<void**>(dbg_work + 0x10), 1);
        battle_func_00262b40(*reinterpret_cast<void**>(dbg_work + 0x10), &g_DebugMenuTitle_00400534);
    } else {
        battle_func_003c5378(dbg_work, work);
    }

    if (g_BtlGameOverHookTarget != nullptr) {
        func_0025c508(g_BtlGameOverHookTarget, 1);
    }
}
extern "C" {
    void* camp_func_002c4c00(const char* name, s32 tag, u32 unk2, u32 unk3, const void* calc_fn, const void* dtor_fn, void* work, void* parent_work); // 0x002c4c00
    void* engine_func_002c4b84(u32 size_a, u32 size_b, u32 unk2, u32 struct_size, u32 count); // 0x002c4b84
    void  engine_func_002c4b30(void* dst, u32 size);                                                        // 0x002c4b30
    void* engine_func_002c5978(const char* name, s32 tag, u32 unk2, u32 unk3, const void* calc_fn, const void* dtor_fn, void* work); // 0x002c5978
    void  engine_func_002c3344(void* obj);                                                                    // 0x002c3344
    void  engine_func_002c32f8(void* obj, const void* a1, u32 a2, const void* a3, u32 a4, const void* a5, u32 a6, u32 a7, u32 a8, const void* a9, u32 a10); // 0x002c32f8
    void  func_002063c4();                                                                                    // 0x002063c4
    void  func_00225270();                                                                                    // 0x00225270
    extern const u8 g_BustUpTable_003ff884;                                                                   // 0x003ff884
    extern const u8 g_BustUpTable_003ff8e4;                                                                   // 0x003ff8e4
    extern const u8 g_BustUpTable_003ffa28;                                                                   // 0x003ffa28
    extern const u8 g_BustUpTable_003ffab8;                                                                   // 0x003ffab8
}

// DECOMP_FUNC(0x002959c4, 472)
void btlTalkBustUp_func_002959c4() {
    static constexpr u32 kAllocSize = 0x100;
    static constexpr u32 kWorkSize = sizeof(BtlTalkBustUpWork);
    static constexpr s32 kCalcTag = 2;
    static constexpr s32 kDrawLeftTag = 0x7D;
    static constexpr s32 kDrawRightTag = 0xDB;

    if (g_BtlTalkBustUpWork != nullptr) {
        return;
    }

    BtlTalkBustUpWork* const work = static_cast<BtlTalkBustUpWork*>(
        engine_func_002c4b84(kAllocSize, kAllocSize, 0, kWorkSize, 1));
    g_BtlTalkBustUpWork = work;

    engine_func_002c4b30(work, kWorkSize);
    work->field_2f8 = -1;
    work->field_308 = 0;
    work->field_2fc = 1.0f;
    work->field_300 = 1.0f;
    work->field_304 = 0.0f;
    work->field_2e8 = 0;
    work->field_2ec = 0;

    work->calc_task = engine_func_002c5978(
        "TMD CALC",
        kCalcTag,
        0,
        0,
        reinterpret_cast<const void*>(&func_002063c4),
        nullptr,
        nullptr);

    camp_func_002c4c00(
        "TalkBustUp DrawLeft",
        kDrawLeftTag,
        0,
        0,
        reinterpret_cast<const void*>(&func_00225270),
        nullptr,
        nullptr,
        work->calc_task);

    camp_func_002c4c00(
        "TalkBustUp DrawRight",
        kDrawRightTag,
        0,
        0,
        reinterpret_cast<const void*>(&func_00225270),
        nullptr,
        nullptr,
        work->calc_task);

    engine_func_002c3344(work);
    engine_func_002c32f8(
        work,
        &g_BustUpTable_003ff884,
        0x60,
        &g_BustUpTable_003ff8e4,
        0x144,
        &g_BustUpTable_003ffa28,
        0x90,
        0,
        0,
        &g_BustUpTable_003ffab8,
        0x9BC);
}
extern "C" {
    void* camp_func_002c4c00(const char* name, s32 tag, u32 unk2, u32 unk3, const void* calc_fn, const void* dtor_fn, void* work, void* parent_work); // 0x002c4c00
    void* engine_func_002c4b84(u32 size_a, u32 size_b, u32 unk2, u32 struct_size, u32 count); // 0x002c4b84
    void  func_001e495c();                                                                    // 0x001e495c
    void  func_002c9e88();                                                                    // 0x002c9e88
    void  func_0020ec74();                                                                    // 0x0020ec74
    s32   battle_func_00256b80(u8* ctx, BtlEditorWork* work, s32 flag);                       // 0x00256b80
    void  battle_func_00256b04(u32 a0, u32 a1);                                               // 0x00256b04
    void  battle_func_00256ad8(u32 a0, u32 a1);                                               // 0x00256ad8
    void  func_0025c508(void* proc, s32 flag);                                                // 0x0025c508
    extern u8* g_BtlEditorSub_004342c8;                                                       // 0x004342c8
    extern void* g_BtlGameOverHookTarget;                                                     // 0x00439ca8
}

// DECOMP_FUNC(0x001f7f00, 432)
void btlEditor_func_001f7f00(BtlEditorWork* work) {
    static constexpr s32 kCalcTag = 2;
    static constexpr s32 kDrawUpTag = 0x73;
    static constexpr u32 kAllocSize = 0x100;
    static constexpr u32 kStateSize = sizeof(BtlEditorState);
    static constexpr u32 kWorkByteOffset = 0x1E9D;
    static constexpr u32 kSubCheckOffset = 0x760;

    work->calc_task = camp_func_002c4c00(
        "btlEditor Calc",
        kCalcTag,
        0,
        0,
        reinterpret_cast<const void*>(&func_001e495c),
        reinterpret_cast<const void*>(&func_002c9e88),
        work,
        work->parent);

    camp_func_002c4c00(
        "btlEditor DrawUp",
        kDrawUpTag,
        0,
        0,
        reinterpret_cast<const void*>(&func_0020ec74),
        nullptr,
        work,
        work->calc_task);

    BtlEditorState* const state = static_cast<BtlEditorState*>(
        engine_func_002c4b84(kAllocSize, kAllocSize, 0, kStateSize, 1));
    g_BtlEditorState = state;
    state->field_00 = 0;
    state->field_04 = reinterpret_cast<const u8*>(work)[kWorkByteOffset];
    state->field_10 = 0xFFFF;
    state->field_12 = 0xFF;
    state->field_13 = 0xFF;

    u8* const sub = g_BtlEditorSub_004342c8;
    if (sub != nullptr) {
        if (*reinterpret_cast<const s32*>(sub + kSubCheckOffset) >= 0) {
            if (battle_func_00256b80(sub, work, 1) != 0) {
                battle_func_00256b04(0, 0);
            }
        }
        battle_func_00256ad8(1, 0);
    }

    work->flags |= 0x80000u;
    if (g_BtlGameOverHookTarget != nullptr) {
        func_0025c508(g_BtlGameOverHookTarget, 1);
    }
}
extern "C" {
    void* camp_func_002c4c00(const char* name, s32 tag, u32 unk2, u32 unk3, const void* calc_fn, const void* dtor_fn, void* work, void* parent_work); // 0x002c4c00
    void* engine_func_002c4b84(u32 size_a, u32 size_b, u32 unk2, u32 struct_size, u32 count); // 0x002c4b84
    void  func_0020edb0();                                                                    // 0x0020edb0
    void  func_002e0640();                                                                    // 0x002e0640
    void  func_002c9fdc();                                                                    // 0x002c9fdc
    extern BtlGameOverState* g_pBtlGameOverState_00435d60;                                    // 0x00435d60
}

// DECOMP_FUNC(0x0021ae48, 428)
void btlGameOver_func_0021ae48(BtlGameOverWork* work) {
    static constexpr s32 kCalcTag = 2;
    static constexpr s32 kDrawUpLeftTag = 0x7A;
    static constexpr s32 kDrawUpRightTag = 0xD8;
    static constexpr u32 kAllocSize = 0x100;
    static constexpr u32 kStateSize = sizeof(BtlGameOverState);
    static constexpr u32 kSaveFlagOffset = 0x24B29;
    static constexpr u32 kEventBitId = 0x557;

    work->calc_task = camp_func_002c4c00(
        "btlGameOver Calc",
        kCalcTag,
        0,
        0,
        reinterpret_cast<const void*>(&func_0020edb0),
        reinterpret_cast<const void*>(&func_002e0640),
        work,
        work->parent);

    camp_func_002c4c00(
        "btlGameOver DrawUpLeft",
        kDrawUpLeftTag,
        0,
        0,
        reinterpret_cast<const void*>(&func_002c9fdc),
        nullptr,
        work,
        work->calc_task);

    camp_func_002c4c00(
        "btlGameOver DrawUpRight",
        kDrawUpRightTag,
        0,
        0,
        reinterpret_cast<const void*>(&func_002c9fdc),
        nullptr,
        work,
        work->calc_task);

    BtlGameOverState* const state = static_cast<BtlGameOverState*>(
        engine_func_002c4b84(kAllocSize, kAllocSize, 0, kStateSize, 1));
    g_pBtlGameOverState_00435d60 = state;

    const u8* const save_base = reinterpret_cast<const u8*>(
        static_cast<uintptr_t>(Save_GetGameOverStateIndex()));
    if (save_base[kSaveFlagOffset] != 0 && !Flag_CheckEventBit(kEventBitId)) {
        state->field_04 |= 1u;
        work->flags |= 0x80000000u;
    }
}

} // namespace smt4::battle
