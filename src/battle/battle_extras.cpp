#include "battle/battle_extras.h"
#include "engine/asd_frame.h"
#include "engine/asd_symbols.h"
#include "engine/asd_texture.h"

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

    // Matrix helpers used by both EnemyDraw and titleDbgBg.
    s32  Gpu_CheckDrawFlag(const void* flag);                               // 0x002C00D4
    void Battle_LoadMatrix(void* dst, const void* src);                     // 0x002C00B4
    void Matrix_Translate(void* matrix, const f32* vec);                    // 0x0023E4E4
    void Matrix_FromEuler(void* dst, u32 mode, f32 x, f32 y, f32 z);        // 0x00292C7C
    void Matrix_Multiply(void* dst, const void* rhs);                       // 0x002A5078
    void Matrix_AddTranslation(void* matrix, const f32* a, const f32* b);   // 0x0015F6D4
    void Matrix_TransformPoint(const void* matrix, const f32* in, f32* out); // 0x002AD6D8

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
    void Title_DrawQuad(void* object, void* a, void* b,
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
    void* Battle_GetTalkEntry(u32 id);                                      // 0x002B9364
    void* ScriptVm_GetTalkState();                                          // 0x002B66EC
    s32  Talk_CheckUnit(u32 id);                                            // 0x0024EC64
    void Talk_CommitChoice(s32 value);                                      // 0x0028DF54
    s32  Talk_CheckVisible(s32 value);                                      // 0x00297004
    void Talk_SelectUnit(u16 id);                                           // 0x002BD25C
    s32  Talk_ChooseIndex(u16 count);                                       // 0x002C0BCC

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

    // Shared UI sprite/layout helpers (same addresses as the UI TUs).
    void UiSpriteGroup_Init(void* group);                                   // 0x002C3344
    void UiSpriteGroup_BindTable(void* group, const void* a1, u32 a2,
                                 const void* a3, u32 a4, const void* a5,
                                 u32 a6, u32 a7, u32 a8, const void* a9,
                                 u32 a10);                                  // 0x002C32F8
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
                Matrix_Translate(matrix, offset);           // 0x0033EFEC

                const f32 angle =
                    static_cast<f32>(unit->field_20) * 256.0f *
                    0.0027777778f;                          // 0x3B360B61
                f32 rotation[16];
                Matrix_FromEuler(rotation, 1, 0.0f, 0.0f, angle);
                Matrix_Multiply(matrix, rotation);          // 0x0033F02C

                offset[0] = -offset[0];
                offset[1] = -offset[1];
                offset[2] = -offset[2];
                Matrix_Translate(matrix, offset);           // 0x0033F05C
            }

            // 0x0033F060..0x0033F148: sprite-facing billboard pass.
            if (unit->flag_25 != 0) {
                f32 offset[3];
                offset[0] = 0.5f * unit->width - unit->x;
                offset[1] = -(unit->y + unit->height);
                offset[2] = 0.0f;
                Matrix_Translate(matrix, offset);           // 0x0033F0A4

                f32 rotation[16];
                Matrix_FromEuler(rotation, 1, 64.0f, 0.0f, 0.0f); // 0x0033F0B4
                Matrix_Multiply(matrix, rotation);          // 0x0033F0CC

                f32 view[3] = {1.0f, 1.0f, g_EnemyDrawGlobal.field_04};
                Matrix_AddTranslation(matrix, view, view + 1); // 0x0033F0F0

                f32 forward[3] = {0.0f, 0.0f, unit->height * 0.5f};
                Matrix_Translate(matrix, forward);          // 0x0033F118

                offset[0] = -offset[0];
                offset[1] = -offset[1];
                offset[2] = -offset[2];
                Matrix_Translate(matrix, offset);           // 0x0033F148
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
                Matrix_TransformPoint(matrix, vertex, vertex);   // 0x0033F1A4
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
            render->primitive = nullptr;

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

// ---------------------------------------------------------------------------
// EftLoadFile.c
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00249fac, 2144)
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
                u32* wide = reinterpret_cast<u32*>(
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
                    *wide = static_cast<u32>(value);
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
                if (name[3] >= 0x1F) {
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

// ---------------------------------------------------------------------------
// titleDbgBg.cpp
// ---------------------------------------------------------------------------

// Documented view over the existing `g_FrameTex` singleton (0x0043E278).
// titleDbgBg reaches the fields below through the same pointer loaded from
// 0x0043E278 (`ldr r0,[pc,...]` / `ldr r4,[r0]`, 0x00117CB0..0x00117CCC).
// The +0x13DC slot lies past the 0xFEC-byte FrameTexScene reconstructed in
// engine/asd_frame.cpp, so it is modelled here without introducing a second
// global for the address.
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
    u8  pad_fe0[0x3FC];                 // +0x0FE0..+0x13DC
    engine::AsdTexture* field_13dc;     // +0x13DC: `ldr r2,[r5]` (0x00117CF8)
};
static_assert(offsetof(TitleDbgBgView, field_ee4) == 0xEE4);
static_assert(offsetof(TitleDbgBgView, field_f10) == 0xF10);
static_assert(offsetof(TitleDbgBgView, field_f18) == 0xF18);
static_assert(offsetof(TitleDbgBgView, overlay_textures) == 0xF20);
static_assert(offsetof(TitleDbgBgView, field_fdc) == 0xFDC);
static_assert(offsetof(TitleDbgBgView, field_13dc) == 0x13DC);

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
        Title_UpdateTextureSize(texture, work->field_13dc); // 0x00117D0C
        // 0x00117D10..0x00117D2C reloads `[r5]` (work+0x13DC) and halves
        // that texture, not the 0xF20/0xF24 overlay.
        work->field_13dc->width >>= 1;
        work->field_13dc->height >>= 1;
    }

    engine::AsdTexture* const target = work->field_fdc;
    f32 width_scale = 240.0f;                           // 0x43700000
    const f32 height_scale = 400.0f;                    // 0x43C80000
    if (work->field_ee4 == 0 && mode != 0) {
        width_scale = 480.0f;                           // 0x43F00000
    }

    const f32 ratio = Camp_GetAspectScale(2.0f, 1.0f);  // 0x00117DB8
    const f32 inv_w = (height_scale / ratio) /
                      static_cast<f32>(target->width);  // 0x00117E08
    const f32 inv_h = (width_scale / ratio) /
                      static_cast<f32>(target->height); // 0x00117E04

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
                   work->field_ee8, work->field_ef8, work->field_f14,
                   work->field_eec, work->field_efc, work->field_f14,
                   work->field_ef0, work->field_f00, work->field_f14,
                   work->field_ef4, work->field_f04, work->field_f14,
                   inv_w, inv_w, inv_w, inv_h,
                   0.0f, 0.0f, 0.0f, inv_h);           // 0x00117FA8

    if (work->field_f18 != 0) {
        void* pop_primitive = UiGpu_SetRenderMode(6, 7, 0);  // 0x00117FC8
        AsdGpuList_Push(g_AsdGpuState, 0x12AC, pop_primitive);
    }
    AsdGpuList_Pop(g_AsdGpuState, 0x124C);               // 0x00118000
}

// ---------------------------------------------------------------------------
// FilterXPoly.cpp
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00348548, 1032)
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

// ---------------------------------------------------------------------------
// EffectProcess.cpp
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002217d8, 648)
void* EffectProcess_func_002217d8(u8 mode) {
    // 0x002217F0..0x00221824: 0x534-byte singleton.
    EffectProcessWork* work = static_cast<EffectProcessWork*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x534, 1));
    g_EffectProcessWork = work;
    AsdMem_Zero(work, 0x534);
    work->mode = mode;                                  // 0x00221828

    Effect_InitA();                                     // 0x0022182C
    Effect_InitB(0);                                    // 0x00221834
    if (work->mode == 0) {
        Effect_InitC();                                 // 0x00221844
    }
    Effect_InitD();                                     // 0x00221848

    // 0x0022184C..0x00221894: default vectors, 5.0/60.0 distances.
    work->field_508 = 0.0f;
    work->field_50C = 0.0f;
    work->field_510 = 5.0f;
    work->field_514 = 0.0f;
    work->field_518 = 0.0f;
    work->field_51C = 0.0f;
    work->field_520 = 60.0f;

    Effect_Setup(work, 1);                              // 0x002218A0
    Effect_SetScale(work, 5.0f, 1.0f);                  // 0x002218B0
    const f32 up[3] = {0.0f, 1.0f, 0.0f};               // [sp+0x10..0x18]
    Effect_SetVectors(work, &work->field_508, &work->field_514,
                      up);                              // 0x002218C4
    Effect_SetDrawParams(work, 1, work->field_520, 0.1f, 25600.0f,
                         0.33333334f);                  // 0x46C80000 / 0x3FD55555

    // 0x002218E4..0x0022190C: "EffectProc" calculation task.
    // 0x002218E4..0x00221908: stack word [0] = 0x0017FAE4 (5th argument,
    // callback), [4] = 0x001DC8C8 (6th), [8] = work (7th).
    work->task = AsdTask_CreateCalc("EffectProc", 2, 0, 0,
                                    TaskCallback(0x0017FAE4),
                                    0x001DC8C8, TaskUserData(work));

    // 0x00221910..0x002219A4: 2D-only or 3D+2D draw tasks.
    if (work->mode != 0) {
        work->draw_down = AsdTask_CreateDraw(
            "EffectDrawDown2D", 0x84, 0, 0, TaskCallback(0x001AA19C), 0,
            TaskUserData(work), work->task);
        work->draw_up = nullptr;
    } else {
        work->draw_up = AsdTask_CreateDraw(
            "EffectDrawUp3D", 0x70, 0, 0, TaskCallback(0x001AA3A4), 0,
            TaskUserData(work), work->task);
        work->draw_down = AsdTask_CreateDraw(
            "EffectDrawDown2D", 0xE8, 0, 0, TaskCallback(0x001DC954), 0,
            TaskUserData(work), work->task);
    }

    return work->task;                                  // 0x002219A8
}

// ---------------------------------------------------------------------------
// btlTalkCommand.cpp
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00318770, 516)
s32 btlTalkCommand_func_00318770() {
    // 0x00318774..0x0031879C: selected index -> unit -> talk entry.
    const u16 selected = Talk_GetSelectedIndex();
    BtlTalkUnitRecord* unit =
        static_cast<BtlTalkUnitRecord*>(Battle_GetTalkUnit(selected));
    const u16 linked = unit->linked_id;
    BtlTalkUnitRecord* entry =
        static_cast<BtlTalkUnitRecord*>(Battle_GetTalkUnit(linked));
    Battle_GetTalkEntry(linked);

    // 0x003187A0..0x003187D8: direct branch when the linked entry is not a
    // talk candidate (0x0400) or the command availability test succeeds.
    if (linked != 0 && entry != nullptr && (entry->flags & 0x0400) != 0) {
        const u8 max = reinterpret_cast<const u8*>(ScriptVm_GetTalkState())[0x76];
        if (entry->field_02 <= max && Talk_CheckUnit(linked) == 0) {
            Talk_CommitChoice(linked);                  // 0x0031886C
            return 1;
        }
    }

    // 0x003187DC..0x00318800: 0x962-byte candidate index buffer.
    u16* candidates = static_cast<u16*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x962, 1));
    u32 candidate_count = 0;

    // 0x0031880C..0x00318844: the `bhi` at 0x0031881C only skips a redundant
    // reload of the same ScriptVm byte; the threshold block itself is always
    // executed.  r6 = talk_max - max(10, talk_max/2).
    const u8 talk_max = reinterpret_cast<const u8*>(
        ScriptVm_GetTalkState())[0x76];
    s32 lower = static_cast<s32>(talk_max);
    const s32 half = lower / 2;
    const s32 margin = (half < 10) ? 10 : half;
    lower = static_cast<s16>(lower - margin);
    if (Talk_CheckVisible(lower) <= 0) {                // 0x00318848
        Talk_CommitChoice(-1);                          // 0x0031885C
        AsdMem_Free(candidates);                        // 0x00318920
        return 1;
    }
    // 0x00318880: clamp the scan's lower bound to 1.
    if (lower <= 0) {
        lower = 1;
    }

    // 0x00318888..0x003188F4: scan ids 1..0x4B0; the record's field_03 is
    // compared against r6 (lower) and r7 (talk_max), not the unit limit.
    for (u32 id = 1; id <= 0x4B0; ++id) {
        const u16 narrow = static_cast<u16>(id);
        BtlTalkUnitRecord* row =
            static_cast<BtlTalkUnitRecord*>(Battle_GetTalkEntry(narrow));
        BtlTalkUnitRecord* unit_row =
            static_cast<BtlTalkUnitRecord*>(Battle_GetTalkUnit(narrow));
        if (row->field_03 >= lower &&
            talk_max >= row->field_03 &&
            (unit_row->flags & 0x0400) != 0 &&
            Talk_CheckUnit(row->id) == 0) {
            Talk_SelectUnit(row->id);                   // 0x003188D4
            candidates[candidate_count++] = row->id;    // 0x003188E8
        }
    }

    s32 result;
    if (candidate_count == 0) {
        result = -1;                                    // 0x003188FC
    } else {
        const s32 index = Talk_ChooseIndex(
            static_cast<u16>(candidate_count - 1));     // 0x0031890C
        result = static_cast<s16>(candidates[index]);   // 0x00318918
    }
    Talk_CommitChoice(result);                          // 0x0031891C
    AsdMem_Free(candidates);                            // 0x00318924
    return 1;
}

// ---------------------------------------------------------------------------
// btlDebug.cpp
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001e1f4c, 504)
void btlDebug_func_001e1f4c(BtlDebugWork* work, void* arg) {
    work->flags |= 1;                                   // 0x001E1F6C

    // 0x001E1F74..0x001E1FCC: "btlDebug Calc" and the two draw tasks.
    work->calc_task = AsdTask_CreateDraw(
        "btlDebug Calc", 2, 0, 0, TaskCallback(0x001D3CA4), 0x0021EB38,
        TaskUserData(work), work->parent);              // 0x001E1FA4
    AsdTask_CreateDraw("btlDebug DrawUp", 0x73, 0, 0,
                       TaskCallback(0x001FC51C), 0, TaskUserData(work),
                       work->calc_task);                // 0x001E1FCC
    AsdTask_CreateDraw("btlDebug DrawDown", 0xE6, 0, 0,
                       TaskCallback(0x0021EBE0), 0, TaskUserData(work),
                       work->calc_task);                // 0x001E1FF4

    // 0x001E2008..0x001E2038: r3 = 0x20, so the allocation is 0x20 bytes
    // (0xE5C is the source-line immediate).  +0x00 = 0, +0x04 = arg; the
    // global only receives +0x08 (pointer) and +0x02 (zero).
    void* menu_state = AsdMem_Alloc(0x100, 0x100, 0, 0x20, 1);
    *reinterpret_cast<u32*>(menu_state) = 0;            // 0x001E2034
    *reinterpret_cast<void**>(static_cast<u8*>(menu_state) + 4) = arg; // 0x001E2030
    g_BtlDebugState.work = menu_state;                  // 0x001E202C
    g_BtlDebugState.field_02 = 0;                       // 0x001E2038

    if (arg == nullptr) {
        Battle_DebugReset();                            // 0x001E20A0
    } else {
        // 0x001E2044..0x001E2078: "btl Debug Menu" list box.
        void* list = AsdList_Create(work->calc_task, 0x73, 0, 0);
        *reinterpret_cast<void**>(static_cast<u8*>(menu_state) + 0x10) = list;
        AsdListBox_Setup(list, reinterpret_cast<const void*>(
            static_cast<std::uintptr_t>(0x00434588)), 0xB);
        AsdListBox_SetMode(list, 1);
        AsdListBox_SetTitle(list, "btl Debug Menu");
    }

    // 0x001E207C..0x001E20B4: optional global menu teardown.
    void* global_menu = *reinterpret_cast<void**>(
        static_cast<std::uintptr_t>(0x00439CA8));
    if (global_menu != nullptr) {
        AsdProc_Destroy(global_menu, 1);                // 0x001E2098 tail
    }
}

// ---------------------------------------------------------------------------
// btlTalkBustUp.cpp
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002959c4, 472)
void btlTalkBustUp_func_002959c4() {
    if (g_BtlTalkBustUpWork != nullptr) {               // 0x002959D4
        return;
    }

    // 0x002959DC..0x00295A10: 0x30C-byte singleton, zeroed.
    BtlTalkBustUpWork* work = static_cast<BtlTalkBustUpWork*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x30C, 1));
    g_BtlTalkBustUpWork = work;
    AsdMem_Zero(work, 0x30C);

    work->field_2f8 = -1;                               // 0x00295A1C
    work->field_308 = 0;                                // 0x00295A24
    work->field_2fc = 1.0f;                             // 0x00295A2C
    work->field_300 = 1.0f;                             // 0x00295A30
    work->field_304 = 0.0f;                             // 0x00295A38
    work->field_2e8 = 0;                                // 0x00295A44
    work->field_2ec = 0;                                // 0x00295A48

    // 0x00295A40..0x00295A60: "TMD CALC" calculation task.
    work->calc_task = AsdTask_CreateCalc("TMD CALC", 2, 0, 0,
                                         TaskCallback(0x002063C4), 0, 0);

    // 0x00295A64..0x00295AB0: left/right bust-up draw tasks.
    AsdTask_CreateDraw("TalkBustUp DrawLeft", 0x7D, 0, 0,
                       TaskCallback(0x00225270), 0, 0,
                       work->calc_task);
    AsdTask_CreateDraw("TalkBustUp DrawRight", 0xDB, 0, 0,
                       TaskCallback(0x00225270), 0, 0,
                       work->calc_task);                // 0x00295AA4

    // 0x00295AB4..0x00295AFC: sprite group and five sprite-table slices.
    UiSpriteGroup_Init(work);
    UiSpriteGroup_BindTable(
        work,
        reinterpret_cast<const void*>(static_cast<std::uintptr_t>(0x003FF884)),
        0x60,
        reinterpret_cast<const void*>(static_cast<std::uintptr_t>(0x003FF8E4)),
        0x144,
        reinterpret_cast<const void*>(static_cast<std::uintptr_t>(0x003FFA28)),
        0x90, 0, 0,
        reinterpret_cast<const void*>(static_cast<std::uintptr_t>(0x003FFAB8)),
        0x9BC);
}

// ---------------------------------------------------------------------------
// btlEditor.cpp
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001f7f00, 432)
void btlEditor_func_001f7f00(BtlEditorWork* work) {
    // 0x001F7F0C..0x001F7F64: "btlEditor Calc" + "btlEditor DrawUp".
    work->calc_task = AsdTask_CreateDraw(
        "btlEditor Calc", 2, 0, 0, TaskCallback(0x001E495C), 0x002C9E88,
        TaskUserData(work), work->parent);
    AsdTask_CreateDraw("btlEditor DrawUp", 0x73, 0, 0,
                       TaskCallback(0x0020EC74), 0, TaskUserData(work),
                       work->calc_task);

    // 0x001F7F74..0x001F7F9C: 0x18-byte editor state.
    BtlEditorState* state = static_cast<BtlEditorState*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x18, 1));
    g_BtlEditorState = state;
    state->field_00 = 0;                                // 0x001F7FA0
    // 0x001F7FA4 loads the byte at the literal 0x001E9D plus the incoming
    // work pointer; the addition is preserved as written by the listing.
    state->field_04 = *reinterpret_cast<const u8*>(
        static_cast<std::uintptr_t>(0x001E9D) +
        reinterpret_cast<std::uintptr_t>(work));
    state->field_10 = 0xFFFF;                           // `mvn r1,#0` (0x001F7FB0)
    state->field_12 = 0xFF;                             // 0x001F7FB4
    state->field_13 = 0xFF;                             // 0x001F7FB8

    // 0x001F7FBC..0x001F7FFC: optional editor manager hand-off.
    void** manager_slot = reinterpret_cast<void**>(
        static_cast<std::uintptr_t>(0x004342C8));
    if (*manager_slot != nullptr) {
        void* manager = *manager_slot;
        if (*reinterpret_cast<s32*>(static_cast<u8*>(manager) + 0x760) >= 0) {
            if (Battle_EditorCheck(manager, work, 1) != 0) {   // 0x001F7FDC
                Battle_EditorStart(nullptr, nullptr);         // 0x001F7FF0
            }
        }
        Battle_EditorSetMode(1, 0);                     // 0x001F7FFC
    }

    // 0x001F8000..0x001F8014: mark the 0x80000 editor flag.
    work->flags |= 0x00080000;

    // 0x001F8008..0x001F8038: optional global menu teardown.
    void* global_menu = *reinterpret_cast<void**>(
        static_cast<std::uintptr_t>(0x00439CA8));
    if (global_menu != nullptr) {
        AsdProc_Destroy(global_menu, 1);                // 0x001F8030 tail
    }
}

// ---------------------------------------------------------------------------
// btlGameOver.cpp
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0021ae48, 428)
void btlGameOver_func_0021ae48(BtlGameOverWork* work) {
    // 0x0021AE54..0x0021AED8: calc + stereo draw tasks.
    work->calc_task = AsdTask_CreateDraw(
        "btlGameOver Calc", 2, 0, 0, TaskCallback(0x0020EDB0), 0x002E0640,
        TaskUserData(work), work->parent);
    AsdTask_CreateDraw("btlGameOver DrawUpLeft", 0x7A, 0, 0,
                       TaskCallback(0x002C9FDC), 0, TaskUserData(work),
                       work->calc_task);                // 0x0021AEB0
    AsdTask_CreateDraw("btlGameOver DrawUpRight", 0xD8, 0, 0,
                       TaskCallback(0x002C9FDC), 0, TaskUserData(work),
                       work->calc_task);                // 0x0021AED8

    // 0x0021AEE4..0x0021AF0C: 0x40-byte game-over state.
    BtlGameOverState* state = static_cast<BtlGameOverState*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x40, 1));
    g_BtlGameOverState = state;

    // 0x0021AF10..0x0021AF54: only arm the game-over flag when the save
    // state byte and event bit 0x557 leave the run active.
    const u32 state_index = Save_GetGameOverStateIndex(); // 0x0021AF10
    const u8 flag = *reinterpret_cast<const u8*>(
        static_cast<std::uintptr_t>(state_index) + 0x00024B29u);
    if (flag != 0) {
        if (!Flag_CheckEventBit(0x557)) {               // 0x0021AF2C
            state->field_04 |= 1;                       // 0x0021AF48
            work->flags |= 0x80000000u;                 // 0x0021AF50
        }
    }
}

} // namespace smt4::battle
