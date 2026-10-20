#include "engine/asd_model.h"

namespace smt4::engine {

// ---------------------------------------------------------------------------
// Global manager / editor singletons
// ---------------------------------------------------------------------------

AsdModelManager g_AsdModelManager{};        // 0x00464AF0
EffectEditorState g_EffectEditor{};         // 0x0044EA80

// Slots written by the shadow-model initializer (0x0010495c).
extern void* g_AsdShadowModelEntry;         // 0x00472950
extern void* g_AsdShadowModelNode;          // 0x00472954
extern void* g_AsdShadowModelDraw;          // 0x00472958

// Two-word owner consulted while building the shadow draw node.
struct AsdShadowModelOwner {
    u32 field_00;
    void* field_04;
};
extern AsdShadowModelOwner g_AsdShadowModelOwner;   // 0x004DAE60

// Engine helpers called by the reconstructed functions.
extern "C" {
    // Memory (AsdMemory)
    void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);        // 0x002c4b84
    void* AsdMem_AllocAlign(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);   // 0x002c54f0
    void  AsdMem_Zero(void* ptr, u32 size);                                // 0x002c4b30
    void  AsdMem_Free(void* ptr);                                          // 0x002c4360
    void  AsdMem_FreeSmall(void* ptr);                                     // 0x002c2430

    // Resource / name database
    void* AsdRes_Load(const char* name, u32 a1, u32 a2);                   // 0x002c32f0
    u32   AsdRes_Hash(const char* name);                                   // 0x002c3290
    void* AsdRes_Find(void* out, const char* name, u32 hash);              // 0x002c31e8
    void* AsdRes_Create(void* desc, void* a1, void* a2, void* a3);         // 0x002c3188
    void* AsdRes_GetContext();                                             // 0x002c31bc
    void* AsdRes_GetDevice();                                              // 0x002c31d8
    void  AsdRes_Register(void* out, void* a1, void* a2);                  // 0x001208b8
    void* AsdRes_Bind(void* obj, void* a1, void* a2);                      // 0x002c2cf0
    u32   AsdRes_BuildKey(void* out);                                      // 0x002c2be8
    int   AsdTag_Compare(const void* a, const void* b, u32 len);           // 0x002c1a48
    void  AsdRaw_ReadHeader(const void* src, void* dst, u32 size);         // 0x002bd610

    // Effect parts / animation
    void* EffParts_Create(const void* entry);                              // 0x002a51dc
    void* AsdAnim_CreateController(void* model);                           // 0x00151470
    void* AsdAnim_BindController(void* data, void* first, s32 max);        // 0x0014ef80
    void* AsdAnim_CreateTrack(void* resource, void* ctx);                  // 0x002a6108
    void  AsdAnim_SetupTrack(void* track, void* desc, void* a2, void* a3, s32 flag); // 0x002a5ca4
    void  AsdAnim_SetNode(void* model, s32 index, f32 value);              // 0x002a5a54
    void  AsdAnim_Finalize(void* model, s32 index);                        // 0x002a5930
    void  AsdParts_AddFlag8(void* view, u32 flag);                         // 0x002a691c
    void  AsdParts_AddFlag20(void* view, u32 flag);                        // 0x002a671c
    void  AsdParts_AddFlag10(void* view, u32 flag);                        // 0x002a65a8
    int   AsdParts_HasParts(void* obj);                                    // 0x0014e9f4
    void* AsdGfx_CreateResource(const void* desc, u32 a1, void* a2, void* a3); // 0x002b3cb0
    void  AsdGfx_ReleaseResource(void* resource);                          // 0x002fb5c8

    // Containers / render helpers
    int   AsdPtrVector_Grow(void* vec, u32 capacity);                      // 0x002af528
    void  AsdRenderWork_Init(void* work, s32 index);                       // 0x001524d0
    void  AsdPool_Add(void* a, void* b);                                   // 0x00150158
    int   AsdPool_Contains(void* a, void* b);                              // 0x002af604
    void* AsdRenderNode_Bind(void* desc, void* ctx);                       // 0x00153f8c
    int   AsdRenderNode_IsActive(void* node);                              // 0x00155854
    void  AsdRenderNode_SetFlag(void* model, s32 flag);                    // 0x00158c18
    int   AsdName_Equal(const char* a, const char* b, u32 hash);           // 0x002b45f8
    void  AsdList_Insert(void* list, void* item, u32 mode);                // 0x002b2814
    void  AsdList_Init();                                                  // 0x0010bb08

    // EffectEditor UI plumbing
    void* AsdPartsManager_Create();                                        // 0x001d2460
    u32   AsdParts_Count(void* parts);                                     // 0x00246a74
    void* AsdParts_Get(void* parts, u32 index);                            // 0x00246a4c
    void* AsdParts_Current();                                              // 0x002469c0
    int   UiInput_Trigger(u32 id);                                         // 0x002b902c
    int   UiInput_Trigger2(u32 id);                                        // 0x002bffbc
    int   UiInput_Trigger3(u32 id);                                        // 0x002c17d4
    void  UiInput_Reset(u32 id);                                           // 0x0024df94
    void  UiText_Draw(u32 a0, u32 a1, u32 a2, const char* fmt, ...);       // 0x0024df14
    void  UiText_Format(char* buf, const char* fmt, ...);                  // 0x002be7fc
    void  UiDraw_Bind(void* a0, void* a1, u32 size);                       // 0x002bcf58
    void* AsdWork_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 a5); // 0x002c34a4
    void  AsdWork_Zero(void* ptr, u32 size);                               // 0x002c3b48
    void* AsdUiObject_CreateAndReset();                                    // 0x0024dfa4
    void  AsdUiObject_Update(void* obj);                                   // 0x0024df5c
    void  AsdPart_Close(void* part, s32 mode);                             // 0x00262bd4
    void  AsdPart_Release(void* part, s32 mode);                           // 0x00262c1c
    void* AsdPart_Wrap(void* element);                                     // 0x0024fe64
    void  AsdPart_Play(void* part);                                        // 0x00281e20
    void  AsdPart_Update(void* part);                                      // 0x002c7938
    int   AsdPart_Update2(void* part);                                     // 0x002f30c0
    void  AsdPart_Update3(void* part);                                     // 0x00250440
    void  AsdPart_Stop(void* part);                                        // 0x00250420
    int   AsdPart_GetCount(void* part);                                    // 0x0021a36c
    void  AsdPart_Setup1(void* part, void* arg);                           // 0x002a3bf8
    void  AsdPart_Setup2(void* part, void* arg);                           // 0x002a3d50
    void  AsdPart_SetScale(void* part, f32 scale);                         // 0x002a399c
    void  AsdPart_SetValue(void* part, void* value);                       // 0x002a37dc
}

// Name tables used by the node resolution passes.
extern void* g_AsdNodeNameTables[];         // 0x00464B8C (array of table pointers)
extern const char* g_AsdNodeNames[3];       // 0x00464BD8
extern void* g_AsdEditorDrawTable[13];      // 0x0044F4D4
extern u8 g_AsdEditorDefaultEntry;          // 0x0044EB38
extern u8 g_AsdModelList;                   // 0x004DAE48
extern u8 g_AsdAnimTableList;               // 0x004DAE3C

// 0x0014ECE0 is emitted as the continuation of 0x0014EC68 (tail call without
// a branch); it is also reached directly from 0x002A5C6C.
void AsdModel_ReloadEffectParts(AsdModel* model, const void* atbc, s32 filter);

namespace {

// Addresses compared against the virtual type-id chain.
constexpr u32 kTypeInfo_44E858 = 0x0044E858;
constexpr u32 kTypeInfo_472180 = 0x00472180;
constexpr u32 kTypeInfo_472288 = 0x00472288;

// Data blocks referenced by the editor draw list / menu descriptors.
constexpr u32 kEditorDrawDesc = 0x004D8C20;
constexpr u32 kEditorDrawDescAlt = 0x004D8CA0;
constexpr u32 kEditorLampA = 0x0044F740;
constexpr u32 kEditorLampB = 0x0044F7B0;
constexpr u32 kEditorLampC = 0x0044F778;
constexpr u32 kEditorMenuPose = 0x0044F890;
constexpr u32 kEditorMenuExit = 0x0044F5B0;
constexpr u32 kEditorMenuNewPartsData = 0x0044F7E8;
constexpr u32 kEditorMenuNewPartsName = 0x0044FE68;
constexpr u32 kEditorMenuNewPartsAlt = 0x0044EAFC;
constexpr u32 kEditorMenuNewPartsAltData = 0x0044F508;
constexpr u32 kEditorSaveCallback = 0x002E6F34;
constexpr u32 kEditorLoadCallback = 0x00313768;
constexpr u32 kEditorLoadCallback2 = 0x00324854;
constexpr u32 kEditorNewPartsCallbackA = 0x00323AC8;
constexpr u32 kEditorNewPartsCallbackB = 0x002FCCE4;

// Reads a virtual type identifier: `ldr r0,[obj]; ldr r1,[r0,#8]; blx r1`.
void* AsdVtableType(void* obj) {
    void** vtable = *reinterpret_cast<void***>(obj);
    using GetTypeFn = void* (*)(void*);
    return reinterpret_cast<GetTypeFn>(vtable[2])(obj);
}

// Walks the type-id chain exactly like the loops at 0x00104a84 / 0x002a9d78.
void* AsdTypeMatch(void* obj, u32 type) {
    if (obj == nullptr) {
        return nullptr;
    }
    void* current = AsdVtableType(obj);
    while (current != reinterpret_cast<void*>(type)) {
        current = *reinterpret_cast<void**>(current);
        if (current == nullptr) {
            return nullptr;
        }
    }
    return obj;
}

// Mirrors `ldr rN, [base, #offset]!; addne base, base, rN` relative pointers.
u8* AsdRelPtr(u8* base, u32 offset) {
    if (base == nullptr) {
        return nullptr;
    }
    u32 rel = *reinterpret_cast<const u32*>(base + offset);
    return rel != 0 ? base + offset + rel : nullptr;
}

// Mirrors the grid store shared by 0x00192594 / 0x002a94e8 / 0x002a9acc.
// `ldr r1,[data,#0x28]; ldm r5,{begin,end}; ldr ip,[r1,#0x28]; ldr r1,[r1,#0x1c]`.
void AsdGridStore(AsdModelData* data, s32 index, void* value) {
    u8* grid = reinterpret_cast<u8*>(data->node_grid);
    if (grid == nullptr || index < 0) {
        return;
    }
    u32 count = (*reinterpret_cast<u32*>(grid + 0x10) -
                 *reinterpret_cast<u32*>(grid + 0x0C)) >> 2;
    if (static_cast<u32>(index) >= count) {
        return;
    }
    s32 rows = *reinterpret_cast<s32*>(grid + 0x28);
    if (rows <= 0) {
        return;
    }
    void** cells = *reinterpret_cast<void***>(grid + 0x1C);
    cells[static_cast<u32>(index) * static_cast<u32>(rows)] = value;
}

// `cmp capacity,count; bgt skip` grow-then-push sequence (0x002a9dd0 / 0x0031ddd8).
bool AsdPtrVector_Push(AsdPtrVector* vec, void* value) {
    u32 capacity = vec->capacity & ~0xC0000000u;
    u32 count = static_cast<u32>(vec->end - vec->begin);
    bool grown = true;
    if (capacity <= count) {
        u32 next = capacity == 0 ? 1 : capacity * 2;
        grown = AsdPtrVector_Grow(vec, next) != 0;
    }
    if (!grown) {
        return false;
    }
    if (vec->end != nullptr) {
        *vec->end = value;
    }
    ++vec->end;
    return true;
}

// `ldr r0,[ctx]; ldr r2,[r0,#0xc]; blx r2` with (ctx, begin).
void AsdPtrVector_Destroy(AsdPtrVector* vec) {
    if (vec->ctx != nullptr && vec->begin != nullptr) {
        void** vtable = *reinterpret_cast<void***>(vec->ctx);
        using DestroyFn = void (*)(void*, void**);
        reinterpret_cast<DestroyFn>(vtable[3])(vec->ctx, vec->begin);
    }
}

// Editor input helpers: `bl trigger; bne taken; bl reset; bl trigger`.
int Ui_PressedA(u32 id) {
    if (UiInput_Trigger(id) != 0) {
        return 1;
    }
    UiInput_Reset(id);
    return UiInput_Trigger(id) != 0 ? 1 : 0;
}

int Ui_PressedB(u32 id) {
    if (UiInput_Trigger2(id) != 0) {
        return 1;
    }
    UiInput_Reset(id);
    return UiInput_Trigger2(id) != 0 ? 1 : 0;
}

// Shared EPLSIGN walk: returns the entry header (`r7 = r4 + 0x10`) for the
// `outer_index`-th chunk, or nullptr when a tag check fails.
const u8* AsdFindEplEntry(const void* atbc, s32 outer_index, s32* out_chunk_count) {
    const u8* chunk = reinterpret_cast<const u8*>(atbc);
    if (AsdTag_Compare(chunk, "ATBC", 4) != 0) {
        return nullptr;
    }
    s32 count = *reinterpret_cast<const s32*>(chunk + 8);
    *out_chunk_count = count;
    if (count <= 0 || count <= outer_index) {
        return nullptr;
    }
    chunk += *reinterpret_cast<const u32*>(chunk + 0x10);

    s32 walk = 0;
    for (;;) {
        if (AsdTag_Compare(chunk, "EPLSIGN", 7) != 0) {
            return nullptr;
        }
        u8 header[0x10];
        AsdRaw_ReadHeader(chunk, header, 0x10);
        const u8* entry = chunk + 0x10;
        if (outer_index == walk) {
            return entry;
        }
        u32 next = *reinterpret_cast<u32*>(&header[8]);
        ++walk;
        chunk += next;
        if (count == 0) {
            return nullptr;
        }
    }
}

} // namespace

// ---------------------------------------------------------------------------
// 0x0010495c -- AsdModel shadow-model / shadow-shader initializer
//
// Strings: "ShadowModel.bcmdl", "ShadowModel", "nwgfx_ShadowShader.bcsdr".
// Atlus source: c:\SMT4\XRD686\AsdSDK\Source\Gfx\Model\AsdModel.cpp
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0010495c, 1108)
void AsdModel_func_0010495c() {
    AsdModelManager& manager = g_AsdModelManager;
    manager.flag_01 = 1;

    AsdList_Init();
    manager.shadow_model_resource = AsdRes_Load("ShadowModel.bcmdl", 0, 1);

    // `ldr r1,[r0,#0x20]!` on the loaded resource.
    u8* resource = reinterpret_cast<u8*>(manager.shadow_model_resource);
    void* node = AsdRelPtr(resource, 0x20);

    if (node != nullptr) {
        void* found = AsdRes_Find(&node, "ShadowModel", AsdRes_Hash("ShadowModel"));
        if (found != nullptr) {
            u8* base = reinterpret_cast<u8*>(found);
            u32 rel = *reinterpret_cast<u32*>(base + 0x0C);
            node = rel != 0 ? base + 0x0C + rel : nullptr;
        } else {
            node = nullptr;
        }
    } else {
        node = nullptr;
    }

    void* shadow_node = node;   // [sp+0x30]
    AsdRes_Register(&shadow_node, AsdRes_GetDevice(), manager.shadow_model_resource);

    // 0x00104a14 .. 0x00104a64: request the model resource by name.
    void* context = AsdRes_GetContext();
    void* device = AsdRes_GetDevice();
    struct {
        void* object;           // +0x00
        u8    flag_04;          // +0x04
        u8    pad_05[0x03];
        u32   field_08;         // +0x08
        u32   field_0c;         // +0x0C
        u32   field_10;         // +0x10
        u32   field_14;         // +0x14
        u32   field_18;         // +0x18
        u32   field_1c;         // +0x1C
        u32   field_20;         // +0x20
        u8    flag_24;          // +0x24
    } desc{};
    desc.object = shadow_node;
    desc.flag_04 = 1;
    desc.field_08 = 8;
    desc.field_0c = 4;
    desc.field_10 = 0;
    desc.field_14 = 0;
    desc.field_18 = 0;
    desc.field_1c = 4;
    desc.field_20 = 0;
    desc.flag_24 = 1;
    void* created = AsdRes_Create(&desc, context, device, shadow_node);

    created = AsdTypeMatch(created, kTypeInfo_44E858);
    manager.shadow_model = AsdTypeMatch(created, kTypeInfo_472180);

    // 0x00104adc: load and bind the shadow shader.
    void* shader = AsdRes_Load("nwgfx_ShadowShader.bcsdr", 0, 1);
    AsdRes_Bind(&shader, AsdRes_GetContext(), shader);

    void* shader_node = reinterpret_cast<u8*>(shader);
    shader_node = AsdRelPtr(reinterpret_cast<u8*>(shader), 0x40);
    shader_node = AsdRelPtr(reinterpret_cast<u8*>(shader_node), 0x28);
    shader_node = AsdRelPtr(reinterpret_cast<u8*>(shader_node), 0x2C);
    if (shader_node != nullptr) {
        u32 rel = *reinterpret_cast<u32*>(shader_node);
        if (rel != 0) {
            shader_node = reinterpret_cast<u8*>(shader_node) + rel;
        } else {
            shader_node = nullptr;
        }
    }

    u8* shadow_model = reinterpret_cast<u8*>(manager.shadow_model);
    u8* shadow_resource = *reinterpret_cast<u8**>(shadow_model + 0x164);
    u8* shadow_draw = *reinterpret_cast<u8**>(shadow_resource);
    *reinterpret_cast<void**>(shadow_draw + 0x20) = shader_node;
    u8* draw_state = *reinterpret_cast<u8**>(shadow_draw + 8);
    *reinterpret_cast<void**>(draw_state + 0x2A4) = nullptr;

    created = AsdTypeMatch(created, kTypeInfo_472180);
    if (created != nullptr) {
        u8* model_base = reinterpret_cast<u8*>(created);
        const f32 zero = 0.0f;

        u8* node0 = *reinterpret_cast<u8**>(model_base + 0x164);
        u8* node0_data = *reinterpret_cast<u8**>(node0);
        u8* flags_owner = *reinterpret_cast<u8**>(node0_data + 8);
        u32 flags = *reinterpret_cast<u32*>(flags_owner + 0x140);
        *reinterpret_cast<u32*>(flags_owner + 0x140) = flags | 3;

        u8* render = *reinterpret_cast<u8**>(model_base + 0x164);
        render = *reinterpret_cast<u8**>(render);
        render = *reinterpret_cast<u8**>(render + 8);
        u8* matrix = render + 0x24;
        *reinterpret_cast<f32*>(render + 0x44) = zero;
        *reinterpret_cast<f32*>(render + 0x48) = zero;
        *reinterpret_cast<f32*>(render + 0x4C) = zero;
        *reinterpret_cast<f32*>(render + 0x50) = zero;
        u32 key = AsdRes_BuildKey(render + 0x44);
        *reinterpret_cast<u32*>(matrix + 0xB8) = key;
    }

    u8* shadow_first = reinterpret_cast<u8*>(manager.shadow_model);
    u8* shadow_first_res = *reinterpret_cast<u8**>(shadow_first + 0x164);
    f32 shadow_scale = *reinterpret_cast<f32*>(shadow_first_res);

    // 0x00104bfc .. 0x00104c48: allocate the 0x18-byte shadow draw entry.
    void* entry = AsdMem_AllocAlign(0x10000, 0x100, 0, 0x18, 1);
    if (entry != nullptr) {
        u8* owner = reinterpret_cast<u8*>(&g_AsdShadowModelOwner);
        u32 owner_word = *reinterpret_cast<u32*>(owner + 4);
        owner_word = *reinterpret_cast<u32*>(owner_word);
        u8* out = reinterpret_cast<u8*>(entry);
        *reinterpret_cast<u32*>(out + 8) = 2;
        *reinterpret_cast<u32*>(out + 0) = 0x004205C8;
        *reinterpret_cast<u32*>(out + 4) = owner_word;
        *reinterpret_cast<f32*>(out + 0x0C) = shadow_scale;
        *reinterpret_cast<u32*>(out + 0x10) = 0;
        *reinterpret_cast<u32*>(out + 0x14) = 0;
    }
    g_AsdShadowModelEntry = entry;

    // 0x00104c4c .. 0x00104c98: 0x0C-byte node wrapper.
    void* node_wrapper = AsdMem_AllocAlign(0x10000, 0x100, 0, 0x0C, 1);
    if (node_wrapper != nullptr) {
        u8* out = reinterpret_cast<u8*>(node_wrapper);
        *reinterpret_cast<u32*>(out + 0) = 0x00420558;
        *reinterpret_cast<void**>(out + 4) = g_AsdShadowModelEntry;
        *reinterpret_cast<u32*>(out + 8) = 0;
    }
    g_AsdShadowModelNode = node_wrapper;

    // 0x00104ca0 .. 0x00104cf0: 0x10-byte draw wrapper.
    void* draw_wrapper = AsdMem_AllocAlign(0x10000, 0x100, 0, 0x10, 1);
    if (draw_wrapper != nullptr) {
        u8* owner = reinterpret_cast<u8*>(&g_AsdShadowModelOwner);
        u32 owner_word = *reinterpret_cast<u32*>(owner + 4);
        owner_word = *reinterpret_cast<u32*>(owner_word);
        u32 table_word = *reinterpret_cast<u32*>(0x00464BBC);
        u8* out = reinterpret_cast<u8*>(draw_wrapper);
        *reinterpret_cast<u32*>(out + 0) = 0x004204F0;
        *reinterpret_cast<u32*>(out + 4) = owner_word;
        *reinterpret_cast<u32*>(out + 8) = table_word;
        *reinterpret_cast<u32*>(out + 0x0C) = 0;
    }
    g_AsdShadowModelDraw = draw_wrapper;
}

// ---------------------------------------------------------------------------
// 0x0014515c -- parse the "ATBC" chunk table and build the EPLSIGN key array.
//
// Atlus source: c:\SMT4\XRD686\AsdSDK\Source\Gfx\Model\AsdModel.cpp
// Tags: "ATBC" (4 bytes), "EPLSIGN" (7 bytes).
// For every chunk whose EPLSIGN entry has bit 0 set, one key is emitted for
// each value in [u16@+0x00, u16@+0x02]; each key is 12 bytes:
//   +0x00 flags (entry+0x0C), +0x04 key, +0x08 EffParts handle.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0014515c, 688)
void AsdModel_func_0014515c(AsdModel* model, const void* atbc) {
    s32 chunk_count = 0;
    if (atbc != nullptr && AsdTag_Compare(atbc, "ATBC", 4) == 0) {
        chunk_count = *reinterpret_cast<const s32*>(reinterpret_cast<const u8*>(atbc) + 8);
    }

    model->atbc_chunk_count = chunk_count;
    model->atbc_key_count = 0;

    s32 key_count = 0;
    for (s32 i = 0; i < chunk_count; ++i) {
        s32 table_count = 0;
        const u8* entry = AsdFindEplEntry(atbc, i, &table_count);
        if (entry == nullptr) {
            continue;
        }
        if ((*reinterpret_cast<const u32*>(entry + 0x0C) & 1u) == 0) {
            continue;
        }
        u16 begin = *reinterpret_cast<const u16*>(entry + 0x00);
        u16 end = *reinterpret_cast<const u16*>(entry + 0x02);
        s32 span = static_cast<s32>(end) - static_cast<s32>(begin);
        key_count = span + key_count + 1;
    }

    model->atbc_key_count = key_count;
    if (key_count == 0) {
        model->atbc_keys = nullptr;
        return;
    }

    u8* keys = reinterpret_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, static_cast<u32>(key_count) * 12u, 1));
    model->atbc_keys = keys;

    s32 out = 0;
    for (s32 i = 0; i < model->atbc_chunk_count; ++i) {
        s32 table_count = 0;
        const u8* entry = AsdFindEplEntry(atbc, i, &table_count);
        if (entry == nullptr) {
            continue;
        }
        void* payload = const_cast<u8*>(entry) + 0x14;
        if ((*reinterpret_cast<const u32*>(entry + 0x0C) & 1u) == 0) {
            continue;
        }
        u16 begin = *reinterpret_cast<const u16*>(entry + 0x00);
        u16 end = *reinterpret_cast<const u16*>(entry + 0x02);
        if (begin > end) {
            continue;
        }
        do {
            u8* slot = keys + static_cast<u32>(out) * 12u;
            void* part = EffParts_Create(payload);
            *reinterpret_cast<u16*>(slot + 4) = begin;
            *reinterpret_cast<void**>(slot + 8) = part;
            *reinterpret_cast<u32*>(slot + 0) =
                *reinterpret_cast<const u32*>(entry + 0x0C);
            ++begin;
            ++out;
        } while (begin <= end);
    }
}

// ---------------------------------------------------------------------------
// 0x0014ec68 -- release the effect-part key array, then rebuild it.
//
// Atlus source: c:\SMT4\XRD686\AsdSDK\Source\Gfx\Model\AsdModel.cpp
// The 792-byte ledger entry contains two compiler-emitted halves:
//   0x0014ec68: destroy pass (effect_parts / effect_part_count)
//   0x0014ece0: rebuild pass, reached by a tail call that pops the frame and
//               immediately re-pushes it for the callee
//               (same target also called directly from 0x002a5c6c).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0014ec68, 792)
void AsdModel_func_0014ec68(AsdModel* model, s32 index) {
    for (s32 i = 0; i < model->effect_part_count; ++i) {
        u8* entry = reinterpret_cast<u8*>(model->effect_parts) + static_cast<u32>(i) * 12u;
        AsdMem_FreeSmall(*reinterpret_cast<void**>(entry + 8));
        *reinterpret_cast<void**>(entry + 8) = nullptr;
    }

    if (model->effect_parts != nullptr) {
        AsdMem_Free(model->effect_parts);
        model->effect_parts = nullptr;
    }
    model->effect_part_count = 0;

    u8* source = reinterpret_cast<u8*>(model->source);
    void* atbc = *reinterpret_cast<void**>(source + 0x0C);
    AsdModel_ReloadEffectParts(model, atbc, index);
}

void AsdModel_ReloadEffectParts(AsdModel* model, const void* atbc, s32 filter) {
    model->effect_part_count = 0;

    // 0x0014ecfc / 0x0014edc4: the outer walk length is the count cached on the
    // model (+0x94), not the header count read inside AsdFindEplEntry.
    s32 chunk_count = model->atbc_chunk_count;

    s32 key_count = 0;
    for (s32 i = 0; i < chunk_count; ++i) {
        s32 table_count = 0;
        const u8* entry = AsdFindEplEntry(atbc, i, &table_count);
        if (entry == nullptr) {
            continue;
        }
        if ((*reinterpret_cast<const u32*>(entry + 0x0C) & 1u) != 0) {
            continue;
        }
        if (*reinterpret_cast<const s32*>(entry + 0x10) != filter) {
            continue;
        }
        u16 begin = *reinterpret_cast<const u16*>(entry + 0x00);
        u16 end = *reinterpret_cast<const u16*>(entry + 0x02);
        s32 span = static_cast<s32>(end) - static_cast<s32>(begin);
        key_count = span + key_count + 1;
    }

    model->effect_part_count = key_count;
    if (key_count == 0) {
        model->effect_parts = nullptr;
        return;
    }

    u8* keys = reinterpret_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, static_cast<u32>(key_count) * 12u, 1));
    model->effect_parts = keys;

    s32 out = 0;
    for (s32 i = 0; i < chunk_count; ++i) {
        s32 table_count = 0;
        const u8* entry = AsdFindEplEntry(atbc, i, &table_count);
        if (entry == nullptr) {
            continue;
        }
        void* payload = const_cast<u8*>(entry) + 0x14;
        if ((*reinterpret_cast<const u32*>(entry + 0x0C) & 1u) != 0) {
            continue;
        }
        if (*reinterpret_cast<const s32*>(entry + 0x10) != filter) {
            continue;
        }
        u16 begin = *reinterpret_cast<const u16*>(entry + 0x00);
        u16 end = *reinterpret_cast<const u16*>(entry + 0x02);
        if (begin > end) {
            continue;
        }
        do {
            u8* slot = keys + static_cast<u32>(out) * 12u;
            void* part = EffParts_Create(payload);
            *reinterpret_cast<u16*>(slot + 4) = begin;
            *reinterpret_cast<void**>(slot + 8) = part;
            *reinterpret_cast<u32*>(slot + 0) =
                *reinterpret_cast<const u32*>(entry + 0x0C);
            ++begin;
            ++out;
        } while (begin <= end);
    }
}

// ---------------------------------------------------------------------------
// 0x00192594 -- attach a model source and build the runtime model data.
//
// Atlus source: c:\SMT4\XRD686\AsdSDK\Source\Gfx\Model\AsdModel.cpp
// mode == 1: create a resource whose descriptor points at the source's
//            model-data block and at the block at model_data+0x220.
// mode == 0: create the default (0x834) resource descriptor.
// Both modes then bump the source refcount, install the node-handle array,
// optionally run the 0x002a94e8 build pass and finally parse the "ATBC"
// chunk table through AsdModel_func_0014515c.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00192594, 484)
void AsdModel_func_00192594(AsdModel* model, AsdModel* source, s32 mode) {
    struct CreateDesc {
        u8  flag_00;                    // +0x00
        u8  flag_01;                    // +0x01
        u8  pad_02[0x02];               // +0x02..+0x04
        u32 field_04;                   // +0x04
        u32 field_08;                   // +0x08
        u32 field_0c;                   // +0x0C
        u32 field_10;                   // +0x10
        void* field_14;                 // +0x14
        void* field_18;                 // +0x18
        void* field_1c;                 // +0x1C
    };

    void* handle = nullptr;
    void* device = nullptr;
    u8* source_data = reinterpret_cast<u8*>(source->model_data);

    if (mode == 1) {
        u8* render = *reinterpret_cast<u8**>(source_data + 0x220);
        u8* flags_owner = *reinterpret_cast<u8**>(render + 8);
        u32 flags = *reinterpret_cast<u32*>(flags_owner + 0x28);
        *reinterpret_cast<u32*>(flags_owner + 0x28) = flags | 1;

        device = AsdRes_GetDevice();
        CreateDesc desc{};
        desc.flag_00 = 1;
        desc.flag_01 = 1;
        desc.field_04 = 4;
        desc.field_08 = 8;
        desc.field_0c = 1;
        desc.field_10 = 0;
        desc.field_14 = source_data;
        desc.field_18 = source_data;
        desc.field_1c = render;
        handle = AsdGfx_CreateResource(&desc, 0,
                                       *reinterpret_cast<void**>(source_data + 8),
                                       device);
    } else if (mode == 0) {
        device = AsdRes_GetDevice();
        CreateDesc desc{};
        desc.flag_00 = 1;
        desc.flag_01 = 1;
        desc.field_04 = 4;
        desc.field_08 = 8;
        desc.field_0c = 1;
        desc.field_10 = 0x834;
        desc.field_14 = nullptr;
        desc.field_18 = nullptr;
        desc.field_1c = nullptr;
        handle = AsdGfx_CreateResource(&desc, 0,
                                       *reinterpret_cast<void**>(source_data + 8),
                                       device);
    }

    model->model_data = handle;

    if ((source->flags & 2u) != 0) {
        AsdGfx_ReleaseResource(model->model_data);
        model->flags |= 2u;
        ++g_AsdModelManager.ref_count_40;
    }

    model->source = source->source;
    ++*reinterpret_cast<u32*>(model->source);

    model->node_handle_count = 1;
    model->node_handles = reinterpret_cast<void**>(
        AsdMem_AllocAlign(0x100, 0x100, 0, static_cast<u32>(model->node_handle_count) * 4u, 1));
    model->node_handles[0] = model->model_data;

    if (mode == 0) {
        AsdModel_func_002a94e8(model);
    }

    u8* model_source = reinterpret_cast<u8*>(model->source);
    AsdModel_func_0014515c(model, *reinterpret_cast<void**>(model_source + 0x0C));
}

// ---------------------------------------------------------------------------
// 0x001fe470 -- AsdModel constructor.
//
// Atlus source: c:\SMT4\XRD686\AsdSDK\Source\Gfx\Model\AsdModel.cpp
// Allocates 0xA8 bytes, zeroes them, seeds -1 at +0x0C/+0x10, 7 at +0x08,
// unit scale at +0x74..+0x80, then links the model into the global list at
// 0x004DAE48 and bumps g_AsdModelManager.ref_count_3c.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001fe470, 288)
AsdModel* AsdModel_func_001fe470() {
    AsdModel* model = reinterpret_cast<AsdModel*>(AsdMem_AllocAlign(0x100, 0x100, 0, 0xA8, 1));
    AsdMem_Zero(model, 0xA8);

    model->field_0c = -1;
    model->field_10 = -1;

    model->source = nullptr;
    model->field_08 = 7;

    model->node_handles = nullptr;
    model->node_handle_count = 0;
    model->model_data = nullptr;
    model->node_ptrs = nullptr;
    model->node_count = 0;
    model->current_node = 0;
    model->max_node_index = 0;

    model->mesh_ptrs = nullptr;
    model->mesh_count = 0;
    model->field_5c = 0;

    model->controller_ptrs = nullptr;
    model->controller_count = 0;
    // +0x6C is zeroed by AsdMem_Zero (0x001fe4f8 stores to padding).

    model->field_74 = 1.0f;
    model->field_78 = 1.0f;
    model->field_7c = 1.0f;
    model->field_80 = 1.0f;

    model->field_90 = 0;

    model->field_84 = 0.0f;
    model->field_88 = 0.0f;
    model->field_8c = 0.0f;

    AsdList_Insert(&g_AsdModelList, model, 0);
    ++g_AsdModelManager.ref_count_3c;

    return model;
}

// ---------------------------------------------------------------------------
// 0x002a94e8 -- resolve node/mesh/controller tables from the model source.
//
// Atlus source: c:\SMT4\XRD686\AsdSDK\Source\Gfx\Model\AsdModel.cpp
// Literal pool: 0x3F800000 (1.0f) for the scale fields.
// Source object layout: model->source+0x18 -> block, then
//   +0x64 node count,  +0x68 relative node-list pointer
//   +0x6C mesh count,  +0x70 relative mesh-list pointer
//   +0x74 draw count,  +0x78 relative draw-list pointer
// Each list entry is 16 bytes; the actual node starts at entry+0x28+rel32.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002a94e8, 1508)
AsdModel* AsdModel_func_002a94e8(AsdModel* model) {
    s32 max_index = -1;

    if (model->model_data == nullptr) {
        AsdAnim_SetNode(model, 0, 0.0f);
        model->field_7c = 1.0f;
        if (model->mesh_count > 0 && model->mesh_controller != nullptr) {
            void** vtable = *reinterpret_cast<void***>(model->mesh_controller);
            using CallFn = void (*)(void*, void*);
            reinterpret_cast<CallFn>(vtable[9])(model->mesh_controller, model->mesh_ptrs[0]);
            model->field_5c = 0;
        }
        AsdAnim_Finalize(model, 0);
        return model;
    }

    u8* source = reinterpret_cast<u8*>(model->source);
    u8* source_data = *reinterpret_cast<u8**>(source + 0x18);

    // --- node table --------------------------------------------------------
    s32 count = *reinterpret_cast<s32*>(source_data + 0x64);
    model->node_count = count;
    if (count <= 0) {
        model->node_ptrs = nullptr;
        model->anim_controller_alt = nullptr;
    } else {
        model->node_ptrs = reinterpret_cast<void**>(
            AsdMem_AllocAlign(0x100, 0x100, 0, static_cast<u32>(count) * 4u, 1));
        for (s32 i = 0; i < count; ++i) {
            u8* list = AsdRelPtr(source_data, 0x68);
            u8* entry = list != nullptr ? list + static_cast<u32>(i) * 16u : nullptr;
            u8* node = AsdRelPtr(entry, 0x28);
            model->node_ptrs[i] = node;
            s32 node_max = *reinterpret_cast<s32*>(node + 0x18);
            if (max_index < node_max) {
                max_index = node_max;
            }
        }

        model->max_node_index = max_index;
        model->anim_controller = AsdAnim_CreateController(model);
        model->anim_controller_alt = AsdAnim_BindController(
            model->model_data, model->node_ptrs[0], max_index);

        u8* anim = reinterpret_cast<u8*>(model->anim_controller);
        u8* value0 = *reinterpret_cast<u8**>(anim + 0x14);
        *reinterpret_cast<void**>(value0) = model->anim_controller_alt;
        u8* value1 = *reinterpret_cast<u8**>(anim + 0x24);
        *reinterpret_cast<f32*>(value1) = 1.0f;
        u8* value2 = *reinterpret_cast<u8**>(anim + 0x34);
        *reinterpret_cast<f32*>(value2) = 1.0f;
        *reinterpret_cast<u8*>(anim + 0x41) = 1;

        AsdModelData* data = reinterpret_cast<AsdModelData*>(model->model_data);
        void* selected = data->field_231 != 0 ? model->anim_controller_alt
                                              : model->anim_controller;
        if (data->field_228 != 0) {
            AsdGridStore(data, data->field_22c, selected);
        }
    }

    // --- mesh table --------------------------------------------------------
    count = *reinterpret_cast<s32*>(source_data + 0x6C);
    model->mesh_count = count;
    if (count <= 0) {
        model->mesh_ptrs = nullptr;
    } else {
        model->mesh_ptrs = reinterpret_cast<void**>(
            AsdMem_AllocAlign(0x100, 0x100, 0, static_cast<u32>(count) * 4u, 1));
        for (s32 i = 0; i < count; ++i) {
            u8* list = AsdRelPtr(source_data, 0x70);
            u8* entry = list != nullptr ? list + static_cast<u32>(i) * 16u : nullptr;
            model->mesh_ptrs[i] = AsdRelPtr(entry, 0x28);
        }

        {
            AsdModelData* data = reinterpret_cast<AsdModelData*>(model->model_data);
            void* list_obj = data->field_148;
            void* first = model->mesh_ptrs[0];
            void* controller = nullptr;

            if (list_obj != nullptr && first != nullptr) {
                u8* info = reinterpret_cast<u8*>(list_obj);
                u8* info_data = *reinterpret_cast<u8**>(info + 8);
                u32 value = *reinterpret_cast<u32*>(info_data + 0x10);

                void* context = AsdRes_GetContext();
                void** vtable = *reinterpret_cast<void***>(context);
                using CreateFn = void* (*)(void*, u32, u32);
                void* resource = reinterpret_cast<CreateFn>(vtable[2])(context, 0x74, 4);
                if (resource != nullptr) {
                    void* track = AsdAnim_CreateTrack(resource, context);
                    struct TrackDesc {
                        void* name;         // +0x00
                        u32 field_04;       // +0x04
                        u32 field_08;       // +0x08
                        u8  flag_0c;        // +0x0C
                    } desc{};
                    desc.name = first;
                    desc.field_04 = value;
                    desc.field_08 = value;
                    desc.flag_0c = 1;
                    AsdAnim_SetupTrack(track, &desc,
                                       reinterpret_cast<void*>(static_cast<uintptr_t>(value)),
                                       reinterpret_cast<void*>(static_cast<uintptr_t>(value)),
                                       1);
                    if (track != nullptr) {
                        void** track_vtable = *reinterpret_cast<void***>(track);
                        using BindFn = void (*)(void*, void*);
                        reinterpret_cast<BindFn>(track_vtable[3])(track, list_obj);
                        if (data->field_148 != nullptr) {
                            AsdGridStore(data, data->field_124, track);
                        }
                    }
                    controller = track;
                }
            }
            model->mesh_controller = controller;
        }
    }

    // --- draw table --------------------------------------------------------
    count = *reinterpret_cast<s32*>(source_data + 0x74);
    model->controller_count = count;
    if (count <= 0) {
        model->controller_ptrs = nullptr;
    } else {
        model->controller_ptrs = reinterpret_cast<void**>(
            AsdMem_AllocAlign(0x100, 0x100, 0, static_cast<u32>(count) * 4u, 1));
        for (s32 i = 0; i < count; ++i) {
            u8* list = AsdRelPtr(source_data, 0x78);
            u8* entry = list != nullptr ? list + static_cast<u32>(i) * 16u : nullptr;
            model->controller_ptrs[i] = AsdRelPtr(entry, 0x28);
        }

        {
            AsdModelData* data = reinterpret_cast<AsdModelData*>(model->model_data);
            void* list_obj = data->field_150;
            void* first = model->controller_ptrs[0];
            void* controller = nullptr;

            if (list_obj != nullptr && first != nullptr) {
                u8* info = reinterpret_cast<u8*>(list_obj);
                u8* info_data = *reinterpret_cast<u8**>(info + 8);
                u32 value = *reinterpret_cast<u32*>(info_data + 0x10);

                void* context = AsdRes_GetContext();
                void** vtable = *reinterpret_cast<void***>(context);
                using CreateFn = void* (*)(void*, u32, u32);
                void* resource = reinterpret_cast<CreateFn>(vtable[2])(context, 0x74, 4);
                if (resource != nullptr) {
                    void* track = AsdAnim_CreateTrack(resource, context);
                    struct TrackDesc {
                        void* name;         // +0x00
                        u32 field_04;       // +0x04
                        u32 field_08;       // +0x08
                        u8  flag_0c;        // +0x0C
                    } desc{};
                    desc.name = first;
                    desc.field_04 = value;
                    desc.field_08 = value;
                    desc.flag_0c = 1;
                    AsdAnim_SetupTrack(track, &desc,
                                       reinterpret_cast<void*>(static_cast<uintptr_t>(value)),
                                       reinterpret_cast<void*>(static_cast<uintptr_t>(value)),
                                       1);
                    if (track != nullptr) {
                        void** track_vtable = *reinterpret_cast<void***>(track);
                        using BindFn = void (*)(void*, void*);
                        reinterpret_cast<BindFn>(track_vtable[3])(track, list_obj);
                        if (data->field_150 != nullptr) {
                            AsdGridStore(data, data->field_12c, track);
                        }
                    }
                    controller = track;
                }
            }
            model->draw_controller = controller;
        }
    }

    AsdAnim_SetNode(model, 0, 0.0f);
    model->field_7c = 1.0f;

    if (model->mesh_count > 0 && model->mesh_controller != nullptr) {
        void** vtable = *reinterpret_cast<void***>(model->mesh_controller);
        using CallFn = void (*)(void*, void*);
        reinterpret_cast<CallFn>(vtable[9])(model->mesh_controller, model->mesh_ptrs[0]);
        model->field_5c = 0;
    }

    AsdAnim_Finalize(model, 0);
    return model;
}

// ---------------------------------------------------------------------------
// 0x002a9acc -- resolve and register the node/render handles.
//
// Atlus source: c:\SMT4\XRD686\AsdSDK\Source\Gfx\Model\AsdModel.cpp
// Type ids: 0x0044E858, 0x00472288.  Draw-context mask: 0x40000092.
// flags bit meaning (observed branches):
//   0x008 -> AsdParts_AddFlag8  (0x02020000)   else 0x040 -> 0x02030000
//   0x020 -> AsdParts_AddFlag20 (0x02020000)   else 0x100 -> 0x02030000
//   0x010 -> AsdParts_AddFlag10 (0x02020000)   else 0x080 -> 0x02030000
// A non-null `source` selects the source-descriptor create path; otherwise
// the name descriptor is created and RTTI-checked against 0x0044E858.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002a9acc, 1880)
void AsdModel_func_002a9acc(AsdModelView* view, AsdModel* model,
                            u32 flags, AsdModel* source) {
    if ((flags & 0x008u) != 0) {
        AsdParts_AddFlag8(view, 0x02020000);
    } else if ((flags & 0x040u) != 0) {
        AsdParts_AddFlag8(view, 0x02030000);
    }

    if ((flags & 0x020u) != 0) {
        AsdParts_AddFlag20(view, 0x02020000);
    } else if ((flags & 0x100u) != 0) {
        AsdParts_AddFlag20(view, 0x02030000);
    }

    if ((flags & 0x010u) != 0) {
        AsdParts_AddFlag10(view, 0x02020000);
    } else if ((flags & 0x080u) != 0) {
        AsdParts_AddFlag10(view, 0x02030000);
    }

    void* bind_result = nullptr;
    {
        void* context = AsdRes_GetContext();
        bind_result = AsdRes_Bind(view, context, view->data);
    }
    // `ands r1,r0,#0x80000000; bpl` -- r0 is the bind return value.
    u32 bind_bits = static_cast<u32>(reinterpret_cast<uintptr_t>(bind_result));
    if ((bind_bits & 0x80000000u) != 0 && (bind_bits & 2u) != 0) {
        void* draw = g_AsdModelManager.field_7c;
        void* context = AsdRes_GetContext();
        AsdRes_Bind(view, context, draw);
    }

    AsdPtrVector resolved{};
    resolved.ctx = AsdRes_GetContext();
    resolved.begin = nullptr;
    resolved.end = nullptr;
    resolved.capacity = 0x40000000u;

    bool modified = false;

    u32 node_count = view->data->node_count;
    model->node_handle_count = static_cast<s32>(node_count);
    model->node_handles = reinterpret_cast<void**>(
        AsdMem_AllocAlign(0x100, 0x100, 0, node_count * 4u, 1));

    u8* list = AsdRelPtr(reinterpret_cast<u8*>(view->data), 0x20);
    u8* entry = list != nullptr ? list + 0x1C : nullptr;
    u8* end = entry != nullptr ? entry + node_count * 16u : nullptr;

    bool loop_ran = false;
    s32 out = 0;
    while (entry != nullptr && entry != end) {
        u8* name = AsdRelPtr(entry, 0x0C);
        void* created = nullptr;

        if (source != nullptr) {
            u8* sub = *reinterpret_cast<u8**>(reinterpret_cast<u8*>(source) + 0x2C);
            void* device = AsdRes_GetDevice();

            struct CreateDesc {
                const char* name;       // +0x00
                u8  flag_04;            // +0x04
                u8  flag_05;            // +0x05
                u8  pad_06[0x02];
                u32 field_08;           // +0x08
                u32 field_0c;           // +0x0C
                u32 field_10;           // +0x10
                u32 field_14;           // +0x14
                u32 field_18;           // +0x18
                void* field_1c;         // +0x1C
            } desc{};
            desc.name = reinterpret_cast<const char*>(name);
            desc.flag_04 = 1;
            desc.flag_05 = 1;
            desc.field_08 = 4;
            desc.field_0c = 8;
            desc.field_10 = 1;
            desc.field_14 = 0;
            desc.field_18 = 0;
            desc.field_1c = *reinterpret_cast<void**>(sub + 0x220);
            created = AsdGfx_CreateResource(&desc, 0, name, device);
        } else {
            void* context = AsdRes_GetContext();
            void* device = AsdRes_GetDevice();

            struct NameDesc {
                const char* name;       // +0x00
                u8  flag_04;            // +0x04
                u8  pad_05[0x03];
                u32 field_08;           // +0x08
                u32 field_0c;           // +0x0C
                u32 field_10;           // +0x10
                u32 field_14;           // +0x14
                u32 field_18;           // +0x18
                u32 field_1c;           // +0x1C
                u32 field_20;           // +0x20
                u8  flag_24;            // +0x24
            } desc{};
            desc.name = reinterpret_cast<const char*>(name);
            desc.flag_04 = 1;
            desc.field_08 = 8;
            desc.field_0c = 4;
            desc.field_10 = 4;
            desc.field_14 = 0;
            desc.field_18 = 0;
            desc.field_1c = 4;
            desc.field_20 = 0;
            desc.flag_24 = 1;
            created = AsdRes_Create(&desc, context, device,
                                    reinterpret_cast<void*>(1));
            created = AsdTypeMatch(created, kTypeInfo_44E858);
        }

        if (AsdParts_HasParts(created) != 0) {
            modified = true;
            model->flags |= 2u;
        }

        AsdPtrVector_Push(&resolved, created);
        created = AsdTypeMatch(created, kTypeInfo_472288);
        model->node_handles[out] = created;

        ++out;
        entry += 0x10;
        loop_ran = true;
    }

    if (modified) {
        ++g_AsdModelManager.ref_count_40;
    }

    model->model_data = model->node_handles[0];

    if (loop_ran) {
        u8* first = reinterpret_cast<u8*>(model->model_data);
        u32* type = *reinterpret_cast<u32**>(first + 8);
        if (type != nullptr) {
            if ((0x40000092u & ~(*type)) != 0) {
                type = nullptr;
            }
        }
        u8* sub = AsdRelPtr(reinterpret_cast<u8*>(type), 0xE0);

        AsdRenderWork_Init(reinterpret_cast<u8*>(model) + 0x1C, -1);

        s32 node_count2 = *reinterpret_cast<s32*>(sub + 0x18);
        for (s32 i = 0; i < node_count2; ++i) {
            u8* node_list = AsdRelPtr(sub, 0x1C);
            u8* node_entry = node_list != nullptr
                                 ? node_list + static_cast<u32>(i) * 16u
                                 : nullptr;
            u8* node = AsdRelPtr(node_entry, 0x28);
            u8* names = nullptr;
            if (node != nullptr) {
                u32 rel = *reinterpret_cast<u32*>(node);
                names = rel != 0 ? node + rel : nullptr;
            }

            for (s32 j = 0; j < 3; ++j) {
                const char* target = g_AsdNodeNames[j];
                u32 hash = AsdRes_Hash(target);
                if (AsdName_Equal(reinterpret_cast<const char*>(names), target,
                                  hash) != 0) {
                    continue;
                }

                u8* table = reinterpret_cast<u8*>(g_AsdNodeNameTables[model->field_90]);
                void* base = AsdRelPtr(sub, 0x1C);
                s32 index = -1;
                if (base != nullptr && target != nullptr) {
                    void* lookup_base = base;
                    u32 found_hash = AsdRes_Hash(target);
                    u8* found = reinterpret_cast<u8*>(
                        AsdRes_Find(&lookup_base, target, found_hash));
                    if (found != nullptr) {
                        index = static_cast<s32>(
                            (found - reinterpret_cast<u8*>(lookup_base) - 0x1C) >> 4);
                    }
                }
                model->field_1c[j] = static_cast<u16>(index);
                break;
            }
        }

        // 0x002aa054: pairwise pool insertion over the resolved vector.
        void** begin = resolved.begin;
        void** finish = resolved.end;
        for (void** a = begin; a != finish; ++a) {
            for (void** b = begin; b != finish; ++b) {
                AsdPool_Add(*a, *b);
            }
        }

        // 0x002aa098: attach each untagged entry to the table's vector.
        AsdNodeNameTableEntry* table = reinterpret_cast<AsdNodeNameTableEntry*>(
            g_AsdNodeNameTables[model->field_90]);
        for (void** it = resolved.begin; it != resolved.end; ++it) {
            u8* object = reinterpret_cast<u8*>(*it);
            if (*reinterpret_cast<u32*>(object + 0x0C) != 0) {
                continue;
            }
            u8* owner = reinterpret_cast<u8*>(table->field_0c);
            if (owner != nullptr) {
                if (owner == object) {
                    continue;
                }
                if (AsdPool_Contains(owner, object) != 0) {
                    continue;
                }
            }
            if (!AsdPtrVector_Push(&table->vec, object)) {
                continue;
            }
            *reinterpret_cast<void**>(object + 0x0C) = table->owner;
        }
    }

    if (g_AsdModelManager.flag_03 != 0) {
        u8* first = reinterpret_cast<u8*>(model->model_data);
        u32 draw_count = (*reinterpret_cast<u32*>(first + 0x168) -
                          *reinterpret_cast<u32*>(first + 0x164)) >> 2;

        u8* p = AsdRelPtr(reinterpret_cast<u8*>(g_AsdModelManager.field_7c), 0x40);
        if (p != nullptr) {
            p = AsdRelPtr(p, 0x28);
            p = AsdRelPtr(p, 0x2C);
        }
        void* draw_node = nullptr;
        if (p != nullptr) {
            u32 rel = *reinterpret_cast<u32*>(p);
            if (rel != 0) {
                draw_node = p + rel;
            }
        }

        for (u32 i = 0; i < draw_count; ++i) {
            u8* list2 = *reinterpret_cast<u8**>(first + 0x164);
            u8* draw = *reinterpret_cast<u8**>(list2 + i * 4u);
            *reinterpret_cast<void**>(draw + 0x20) = draw_node;
            u8* state = *reinterpret_cast<u8**>(draw + 8);
            *reinterpret_cast<void**>(state + 0x2A4) = nullptr;
        }
    }

    resolved.end = resolved.begin;
    AsdPtrVector_Destroy(&resolved);
}

// ---------------------------------------------------------------------------
// 0x002b2b78 -- animation-table signature object.
//
// Atlus source: c:\SMT4\XRD686\AsdSDK\Source\Gfx\Model\AsdModel.cpp
// If the data begins with "ATBC", the "MDLSIGN" chunk is located through
// data[+0x14] (or data[+0x10] when zero) and its payload at +0x80 is kept.
// Otherwise the data pointer itself is stored as the signature.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002b2b78, 340)
AsdAnimTable* AsdModel_func_002b2b78(void* data, void* owner) {
    AsdAnimTable* table = reinterpret_cast<AsdAnimTable*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, 0x1C, 1));

    u8* bytes = reinterpret_cast<u8*>(data);
    table->field_00 = 1;
    table->field_04 = 1;
    table->signature = nullptr;
    table->atbc = data;
    table->chunk = nullptr;
    table->owner = nullptr;
    table->field_18 = 0;

    void* signature = nullptr;
    void* owner_copy = nullptr;

    if (AsdTag_Compare(data, "ATBC", 4) != 0) {
        signature = data;
    } else {
        u32 offset = *reinterpret_cast<u32*>(bytes + 0x14);
        if (offset == 0) {
            offset = *reinterpret_cast<u32*>(bytes + 0x10);
        }
        u8* chunk = bytes + offset;
        if (AsdTag_Compare(chunk, "MDLSIGN", 7) == 0) {
            owner_copy = *reinterpret_cast<void**>(chunk + 8);
            signature = chunk + 0x80;
        } else {
            signature = nullptr;
        }
    }

    table->signature = signature;

    void* atbc_chunk = nullptr;
    if (AsdTag_Compare(data, "ATBC", 4) == 0) {
        atbc_chunk = bytes + *reinterpret_cast<u32*>(bytes + 0x0C);
    }
    table->chunk = atbc_chunk;

    if (owner_copy == nullptr) {
        table->owner = owner;
    }

    AsdList_Insert(&g_AsdAnimTableList, table, 0);
    ++g_AsdModelManager.ref_count_38;

    return table;
}

// ---------------------------------------------------------------------------
// 0x0031dc4c -- build the node/mesh/controller handle set for a model view.
//
// Atlus source: c:\SMT4\XRD686\AsdSDK\Source\Gfx\Model\AsdModel.cpp
// Type ids: 0x0044E858, 0x00472288.  Draw-context mask: 0x40000092.
// Node list   : view->data+0x1C (count), +0x20 (relative list)
// Mesh list   : view->data+0x64 (count), +0x68 (relative list)
// Draw list   : view->data+0x74 (count), +0x78 (relative list)
// Same 16-byte list entries and +0x28 relative node pointers as 0x002a94e8.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0031dc4c, 2028)
AsdModelNodeSet* AsdModel_func_0031dc4c(AsdModelView* view) {
    AsdModelNodeSet* set = reinterpret_cast<AsdModelNodeSet*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x28, 1));

    AsdPtrVector resolved{};
    resolved.ctx = AsdRes_GetContext();
    resolved.begin = nullptr;
    resolved.end = nullptr;
    resolved.capacity = 0x40000000u;

    u32 node_count = view->data->node_count;
    set->node_count = node_count;
    set->node_handles = reinterpret_cast<void**>(
        AsdMem_AllocAlign(0x100, 0x100, 0, node_count * 4u, 1));

    u8* list = AsdRelPtr(reinterpret_cast<u8*>(view->data), 0x20);
    u8* entry = list != nullptr ? list + 0x1C : nullptr;
    u8* end = entry != nullptr ? entry + node_count * 16u : nullptr;

    s32 out = 0;
    while (entry != nullptr && entry != end) {
        u8* name = AsdRelPtr(entry, 0x0C);
        void* context = AsdRes_GetContext();
        void* device = AsdRes_GetDevice();

        struct NameDesc {
            const char* name;           // +0x00
            u8  flag_04;                // +0x04
            u8  pad_05[0x03];
            u32 field_08;               // +0x08
            u32 field_0c;               // +0x0C
            u32 field_10;               // +0x10
            u32 field_14;               // +0x14
            u32 field_18;               // +0x18
            u32 field_1c;               // +0x1C
            u32 field_20;               // +0x20
            u8  flag_24;                // +0x24
        } desc{};
        desc.name = reinterpret_cast<const char*>(name);
        desc.flag_04 = 1;
        desc.field_08 = 8;
        desc.field_0c = 4;
        desc.field_10 = 4;
        desc.field_14 = 0;
        desc.field_18 = 0;
        desc.field_1c = 4;
        desc.field_20 = 0;
        desc.flag_24 = 1;

        void* created = AsdRes_Create(&desc, context, device,
                                      reinterpret_cast<void*>(1));
        created = AsdTypeMatch(created, kTypeInfo_44E858);
        AsdPtrVector_Push(&resolved, created);
        created = AsdTypeMatch(created, kTypeInfo_472288);
        set->node_handles[out] = created;

        ++out;
        entry += 0x10;
    }

    // 0x0031de64: pairwise pool insertion.
    for (void** a = resolved.begin; a != resolved.end; ++a) {
        for (void** b = resolved.begin; b != resolved.end; ++b) {
            AsdPool_Add(*a, *b);
        }
    }

    // --- mesh handles ------------------------------------------------------
    s32 mesh_count = static_cast<s32>(view->data->mesh_count);
    set->mesh_count = static_cast<u32>(mesh_count);
    if (mesh_count <= 0) {
        set->mesh_handles = nullptr;
    } else {
        set->mesh_handles = reinterpret_cast<void**>(
            AsdMem_AllocAlign(0x100, 0x100, 0, mesh_count * 4u, 1));
        set->mesh_handles_alt = reinterpret_cast<void**>(
            AsdMem_Alloc(0x100, 0x100, 0, mesh_count * 4u, 1));

        for (s32 i = 0; i < mesh_count; ++i) {
            u8* mesh_list = AsdRelPtr(reinterpret_cast<u8*>(view->data), 0x68);
            u8* mesh_entry = mesh_list != nullptr
                                 ? mesh_list + i * 16u
                                 : nullptr;
            set->mesh_handles[i] = AsdRelPtr(mesh_entry, 0x28);
        }

        for (s32 i = 0; i < mesh_count; ++i) {
            u8* first = reinterpret_cast<u8*>(set->mesh_handles[i]);
            u8* sub = AsdRelPtr(first, 8);
            u32 hash = AsdRes_Hash(reinterpret_cast<const char*>(sub));

            void* match = nullptr;
            for (s32 j = 0; j < static_cast<s32>(node_count); ++j) {
                u8* node = reinterpret_cast<u8*>(set->node_handles[j]);
                u8* names = AsdRelPtr(node, 0x0C);
                if (AsdRes_Hash(reinterpret_cast<const char*>(names)) != hash) {
                    continue;
                }
                if (AsdName_Equal(reinterpret_cast<const char*>(names),
                                  reinterpret_cast<const char*>(sub), hash) == 0) {
                    match = node;
                    break;
                }
            }

            if (match != nullptr) {
                u8* node = reinterpret_cast<u8*>(match);
                void* first_value = set->mesh_handles[i];
                u8* node_data = *reinterpret_cast<u8**>(node + 8);
                if (node_data != nullptr) {
                    if ((0x40000092u & ~(*reinterpret_cast<u32*>(node_data))) != 0) {
                        node_data = nullptr;
                    }
                }

                if (AsdRenderNode_IsActive(&first_value) != 0) {
                    AsdRenderNode_SetFlag(node, 1);
                }

                f32 value = *reinterpret_cast<f32*>(
                    reinterpret_cast<u8*>(first_value) + 0x18);
                void* node_228 = *reinterpret_cast<void**>(node + 0x228);
                void* link = nullptr;
                if (node_228 != nullptr) {
                    u8* info = *reinterpret_cast<u8**>(
                        reinterpret_cast<u8*>(node_228) + 8);
                    link = *reinterpret_cast<void**>(info + 0x10);
                }

                u8* sub2 = AsdRelPtr(node_data, 0xE0);
                u32 sub_flags = *reinterpret_cast<u32*>(sub2 + 0x28);
                s32 flag = (sub_flags & 2u) == 0 ? 1 : 0;

                void* render = nullptr;
                if (first_value != nullptr) {
                    struct RenderDesc {
                        void* object;       // +0x00
                        void* link;         // +0x04
                        f32   value;        // +0x08
                        u8    flag;         // +0x0C
                    } desc{};
                    desc.object = first_value;
                    desc.link = link;
                    desc.value = value;
                    desc.flag = 1;
                    render = AsdRenderNode_Bind(&desc, AsdRes_GetContext());
                    *reinterpret_cast<u8*>(reinterpret_cast<u8*>(render) + 0x5D) =
                        static_cast<u8>(flag ^ 1);
                }

                void** render_vtable = *reinterpret_cast<void***>(render);
                using BindFn = void (*)(void*, void*);
                reinterpret_cast<BindFn>(render_vtable[3])(render, node_228);

                set->mesh_handles_alt[i] = render;

                if (*reinterpret_cast<void**>(node + 0x228) != nullptr) {
                    u8* grid = *reinterpret_cast<u8**>(node + 0x28);
                    u32 index = *reinterpret_cast<u32*>(node + 0x204);
                    s32 rows = *reinterpret_cast<s32*>(grid + 0x28);
                    u32 count = (*reinterpret_cast<u32*>(grid + 0x10) -
                                 *reinterpret_cast<u32*>(grid + 0x0C)) >> 2;
                    if (index < count && rows > 0) {
                        void** cells = *reinterpret_cast<void***>(grid + 0x1C);
                        cells[index * static_cast<u32>(rows)] = render;
                    }
                }
            }
        }
    }

    // --- draw/controller handles ------------------------------------------
    s32 draw_count = static_cast<s32>(view->data->draw_count);
    set->draw_count = static_cast<u32>(draw_count);
    if (draw_count <= 0) {
        set->draw_handles = nullptr;
    } else {
        set->draw_handles = reinterpret_cast<void**>(
            AsdMem_AllocAlign(0x100, 0x100, 0, draw_count * 4u, 1));
        set->draw_handles_alt = reinterpret_cast<void**>(
            AsdMem_Alloc(0x100, 0x100, 0, draw_count * 4u, 1));

        for (s32 i = 0; i < draw_count; ++i) {
            u8* draw_list = AsdRelPtr(reinterpret_cast<u8*>(view->data), 0x78);
            u8* draw_entry = draw_list != nullptr
                                 ? draw_list + i * 16u
                                 : nullptr;
            set->draw_handles[i] = AsdRelPtr(draw_entry, 0x28);
        }

        for (s32 i = 0; i < draw_count; ++i) {
            u8* first = reinterpret_cast<u8*>(set->draw_handles[i]);
            u8* sub = AsdRelPtr(first, 8);
            u32 hash = AsdRes_Hash(reinterpret_cast<const char*>(sub));

            void* match = nullptr;
            for (s32 j = 0; j < static_cast<s32>(node_count); ++j) {
                u8* node = reinterpret_cast<u8*>(set->node_handles[j]);
                u8* names = AsdRelPtr(node, 0x0C);
                if (AsdRes_Hash(reinterpret_cast<const char*>(names)) != hash) {
                    continue;
                }
                if (AsdName_Equal(reinterpret_cast<const char*>(names),
                                  reinterpret_cast<const char*>(sub), hash) == 0) {
                    match = node;
                    break;
                }
            }

            if (match != nullptr) {
                u8* node = reinterpret_cast<u8*>(match);
                void* list_obj = *reinterpret_cast<void**>(node + 0x148);
                void* track = nullptr;

                if (list_obj != nullptr) {
                    u8* info = *reinterpret_cast<u8**>(
                        reinterpret_cast<u8*>(list_obj) + 8);
                    void* value = *reinterpret_cast<void**>(info + 0x10);

                    void* context = AsdRes_GetContext();
                    void** vtable = *reinterpret_cast<void***>(context);
                    using CreateFn = void* (*)(void*, u32, u32);
                    void* resource = reinterpret_cast<CreateFn>(vtable[2])(
                        context, 0x74, 4);
                    if (resource != nullptr) {
                        track = AsdAnim_CreateTrack(resource, context);
                        struct TrackDesc {
                            void* object;       // +0x00
                            void* link;         // +0x04
                            u32   value;        // +0x08
                            u8    flag;         // +0x0C
                        } desc{};
                        desc.object = set->draw_handles[i];
                        desc.link = value;
                        desc.value = static_cast<u32>(
                            reinterpret_cast<uintptr_t>(value));
                        desc.flag = 1;
                        AsdAnim_SetupTrack(track, &desc, value, value, 1);
                        if (track != nullptr) {
                            void** track_vtable = *reinterpret_cast<void***>(track);
                            using BindFn = void (*)(void*, void*);
                            reinterpret_cast<BindFn>(track_vtable[3])(track, list_obj);
                            if (*reinterpret_cast<void**>(node + 0x148) != nullptr) {
                                u8* grid = *reinterpret_cast<u8**>(node + 0x28);
                                u32 index = *reinterpret_cast<u32*>(node + 0x124);
                                s32 rows = *reinterpret_cast<s32*>(grid + 0x28);
                                u32 count = (*reinterpret_cast<u32*>(grid + 0x10) -
                                             *reinterpret_cast<u32*>(grid + 0x0C)) >> 2;
                                if (index < count && rows > 0) {
                                    void** cells = *reinterpret_cast<void***>(grid + 0x1C);
                                    cells[index * static_cast<u32>(rows)] = track;
                                }
                            }
                        }
                    }
                }
                set->draw_handles_alt[i] = track;
            }
        }
    }

    resolved.end = resolved.begin;
    AsdPtrVector_Destroy(&resolved);

    return set;
}

// ---------------------------------------------------------------------------
// 0x002fcd20 -- EffectEditor authoring/update entry point.
//
// Atlus source: c:\SMT4\XRD686\AsdSDK\Source\Gfx\EffectEditor\EffectEditor.cpp
// Strings: " %-10s%3d", "%-11s%3d", "%-10s*%3d", " %-9s*%3d", "POSETURE",
//          "NEW  PARTS", "SAVE(EPL)", "LOAD(EPL)", "EXIT", "STOP", "SLOW",
//          "2D", "ALL:%d NOW:%d", "RL BUTTON RELEASE KEYWAIT",
//          "%s(TMX)", "%s(P2A)", "%s(PB)", "%s", "%s(EP)", "%s(EPL)", "%s(TLP)"
//
// Returns 0x00800001 on the first frame (g_EffectEditor.flag_07 == 0) and 0
// afterwards; the sign bit tells the caller that the editor just started.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002fcd20, 4160)
void* EffectEditor_func_002fcd20() {
    EffectEditorState& ed = g_EffectEditor;
    u8* widget = reinterpret_cast<u8*>(0x0044F858);

    s32 menu_changed = 0;       // [sp+0x10]
    s32 list_changed = 0;       // [sp+0x14]
    s32 rebuild_part = 0;       // r14/sl

    if (ed.menu_current == widget) {
        u32 flags = *reinterpret_cast<u32*>(widget + 0x10);
        *reinterpret_cast<u32*>(widget + 0x10) = flags & ~1u;
    }

    if (ed.parts == nullptr) {
        ed.parts = AsdPartsManager_Create();
    }
    u32 part_count = AsdParts_Count(ed.parts);      // [sp+8]

    if (ed.menu_current == widget) {
        u32 mode = *reinterpret_cast<u32*>(widget + 0x0C);
        if (mode == 0) {
            if (Ui_PressedA(5) != 0) {
                if (ed.list_offset != 0) {
                    menu_changed = 1;
                    list_changed = 1;
                    --ed.list_offset;
                }
            }
        } else if (mode == 0x14) {
            if (Ui_PressedA(6) != 0) {
                u32 next = static_cast<u32>(ed.list_offset) + 1u + mode;
                if (part_count > next) {
                    menu_changed = 1;
                    list_changed = 1;
                    ++ed.list_offset;
                }
            }
        }

        u32 index = mode + static_cast<u32>(ed.list_offset);
        if (index < part_count) {
            EffectEditorPart* part = reinterpret_cast<EffectEditorPart*>(
                AsdParts_Get(ed.parts, index));
            s32 value = part->list_index;

            if (Ui_PressedA(4) != 0 && value != 0) {
                rebuild_part = 1;
                if (UiInput_Trigger3(7) != 0 || UiInput_Trigger3(0x18) != 0) {
                    if (value >= 10) {
                        value -= 10;
                    } else {
                        value = 0;
                    }
                } else if (UiInput_Trigger3(8) != 0) {
                    if (UiInput_Trigger3(0x1C) == 0) {
                        value -= 1;
                    } else if (value >= 0x64) {
                        value -= 0x64;
                    } else {
                        value = 0;
                    }
                } else {
                    if (value >= 0x64) {
                        value -= 0x64;
                    } else {
                        value = 0;
                    }
                }
                part->list_index = value;
            } else if (Ui_PressedA(3) != 0) {
                rebuild_part = 1;
                if (UiInput_Trigger3(7) != 0 || UiInput_Trigger3(0x18) != 0) {
                    value += 10;
                } else if (UiInput_Trigger3(8) != 0) {
                    if (UiInput_Trigger3(0x1C) == 0) {
                        value += 1;
                    } else {
                        value += 0x64;
                    }
                } else {
                    value += 0x64;
                }
                part->list_index = value;
            }
        }

        if (Ui_PressedB(0x0A) != 0 && part_count > index) {
            EffectEditorPart* part = reinterpret_cast<EffectEditorPart*>(
                AsdParts_Get(ed.parts, index));
            part->flags ^= 2u;
        }
    }

    u32 draw_count = part_count > 0x15u ? 0x15u : part_count;    // sb
    u32 slot_count = draw_count + 0x0A;                          // [sp+0xc]
    u32 work_size = slot_count * 0x2C;

    u8* work = reinterpret_cast<u8*>(AsdWork_Alloc(0x10000, 0x100, 0, work_size, 0x10, 1));
    AsdWork_Zero(work, work_size);

    u8* text = work + slot_count * 0x18;
    UiDraw_Bind(reinterpret_cast<void*>(kEditorDrawDesc), ed.parts, 0x80);

    for (u32 i = 0; i < draw_count; ++i) {
        EffectEditorPart* part = reinterpret_cast<EffectEditorPart*>(
            AsdParts_Get(ed.parts, static_cast<u32>(ed.list_offset) + i));
        u8* element = reinterpret_cast<u8*>(part->element_table);
        u16 key_a = *reinterpret_cast<u16*>(element + 4);
        u16 key_b = *reinterpret_cast<u16*>(element + 0x0C);

        u8* found = nullptr;
        for (u32 k = 0; k < 13; ++k) {
            u8* table = reinterpret_cast<u8*>(g_AsdEditorDrawTable[k]);
            if (table == nullptr) {
                continue;
            }
            u8* cursor = table;
            u8* node = *reinterpret_cast<u8**>(cursor);
            u8* hit = nullptr;
            while (node != nullptr) {
                u16 type = *reinterpret_cast<u16*>(node + 4);
                if (type != 0x1B && type == key_a &&
                    *reinterpret_cast<u16*>(node + 8) == key_b) {
                    hit = node;
                    break;
                }
                cursor += 0x1C;
                node = *reinterpret_cast<u8**>(cursor);
            }
            if (hit != nullptr) {
                found = hit;
                break;
            }
        }
        if (found == nullptr) {
            found = &g_AsdEditorDefaultEntry;
        }

        s32 value = part->list_index;
        u32 color = part->flags & 2u;
        u16 type = *reinterpret_cast<u16*>(found + 4);
        u8* name = part->name;
        u8* item = work + i * 0x18;

        if ((part->field_98 & 1u) != 0) {
            if (type == 0x14) {
                UiText_Format(reinterpret_cast<char*>(text), " %-9s*%3d", name, value);
            } else {
                UiText_Format(reinterpret_cast<char*>(text), " %-10s%3d", name, value);
            }
            *reinterpret_cast<void**>(item + 8) =
                reinterpret_cast<void*>(kEditorLampC);
            *reinterpret_cast<u32*>(item + 0x0C) =
                color != 0 ? 0x00FFFFFEu : 0x00FFFFFFu;
        } else {
            if (type == 0x14) {
                UiText_Format(reinterpret_cast<char*>(text), "%-10s*%3d", name, value);
            } else {
                UiText_Format(reinterpret_cast<char*>(text), "%-11s%3d", name, value);
            }
            *reinterpret_cast<void**>(item + 8) =
                reinterpret_cast<void*>(type != 0 ? kEditorLampA : kEditorLampB);
            *reinterpret_cast<u32*>(item + 0x0C) =
                color != 0 ? 0x00FFFFFEu : 0x00FFFFFFu;
        }

        *reinterpret_cast<u8**>(item) = text;
        *reinterpret_cast<u8*>(item + 4) = 0x1A;
        *reinterpret_cast<u32*>(item + 0x10) = 0;
        *reinterpret_cast<f32*>(item + 0x14) = 0.0f;
        text += 0x14;
    }

    // 0x002fd25c: menu descriptor entries share the same scratch buffer.
    EffectEditorMenuEntry* menu =
        reinterpret_cast<EffectEditorMenuEntry*>(work);
    u32 index = draw_count;

    if (draw_count != 0) {
        menu[index].name = nullptr;
        menu[index].type = 0x19;
        menu[index].callback_a = nullptr;
        menu[index].callback_b = nullptr;
        menu[index].payload = nullptr;
        menu[index].value = 0.0f;
        ++index;

        menu[index].name = "POSETURE";
        menu[index].type = 0x1A;
        menu[index].callback_a = reinterpret_cast<void*>(kEditorMenuPose);
        menu[index].callback_b = nullptr;
        menu[index].payload = nullptr;
        menu[index].value = 0.0f;
        ++index;
    }

    menu[index].name = "NEW  PARTS";
    menu[index].type = 0x1C;
    menu[index].callback_a = reinterpret_cast<void*>(kEditorMenuNewPartsData);
    menu[index].callback_b = nullptr;
    menu[index].payload = nullptr;
    menu[index].value = 0.0f;
    ++index;

    menu[index].name = reinterpret_cast<const char*>(
        static_cast<uintptr_t>(kEditorMenuNewPartsName));
    menu[index].type = 0x1E;
    menu[index].callback_a = reinterpret_cast<void*>(kEditorNewPartsCallbackA);
    menu[index].callback_b = reinterpret_cast<void*>(kEditorNewPartsCallbackB);
    menu[index].payload = nullptr;
    menu[index].value = 0.0f;
    ++index;

    // Separator: only the type byte is written (0x002fd33c).  The `beq` at
    // 0x002fd340 reuses the flags of `sub ip,r6,#0x680` (always non-zero), so
    // the following entries are emitted unconditionally.
    menu[index].type = 0x18;
    ++index;

    menu[index].name = "SAVE(EPL)";
    menu[index].type = 0x1E;
    menu[index].callback_a = reinterpret_cast<void*>(kEditorSaveCallback);
    menu[index].callback_b = reinterpret_cast<void*>(kEditorLoadCallback);
    menu[index].payload = nullptr;
    menu[index].value = 0.0f;
    ++index;

    menu[index].name = "LOAD(EPL)";
    menu[index].type = 0x1E;
    menu[index].callback_a = reinterpret_cast<void*>(kEditorLoadCallback2);
    menu[index].callback_b = reinterpret_cast<void*>(kEditorNewPartsCallbackB);
    menu[index].payload = nullptr;
    menu[index].value = 0.0f;
    ++index;

    // The `beq` at 0x002fd3a0 also reuses the stale (non-zero) `sub` flags.
    menu[index].name = reinterpret_cast<const char*>(
        static_cast<uintptr_t>(kEditorMenuNewPartsAlt));
    menu[index].type = 0x1A;
    menu[index].callback_a = reinterpret_cast<void*>(kEditorMenuNewPartsAltData);
    menu[index].callback_b = nullptr;
    menu[index].payload = nullptr;
    menu[index].value = 0.0f;
    ++index;

    menu[index].name = "EXIT";
    menu[index].type = 0x1A;
    menu[index].callback_a = reinterpret_cast<void*>(kEditorMenuExit);
    menu[index].callback_b = nullptr;
    menu[index].payload = nullptr;
    menu[index].value = 0.0f;
    ++index;

    *reinterpret_cast<u32*>(widget + 0x18) = index;
    *reinterpret_cast<u32*>(widget + 0x14) = static_cast<u32>(reinterpret_cast<uintptr_t>(work));

    u32 mode = *reinterpret_cast<u32*>(widget + 0x0C);
    if (mode >= slot_count) {
        --slot_count;
        *reinterpret_cast<u32*>(widget + 0x0C) = slot_count;
    }

    u32 old_selection = *reinterpret_cast<u32*>(widget + 0x0C);
    f32 old_time = *reinterpret_cast<f32*>(reinterpret_cast<u8*>(ed.parts) + 0x74);

    void* current = ed.menu_current;
    if (ed.speed_mode == 0) {
        current = AsdUiObject_CreateAndReset();
        ed.menu_current = current;
    }
    if (current == reinterpret_cast<void*>(kEditorMenuPose)) {
        if ((*reinterpret_cast<u32*>(reinterpret_cast<u8*>(current) + 0x10) & 8u) != 0) {
            rebuild_part = 1;
        }
    }

    if (menu_changed != 0) {
        u32 last = *reinterpret_cast<u32*>(widget + 0x18) - 1u;
        u32 selected = *reinterpret_cast<u32*>(widget + 0x0C);
        if (selected == last) {
            *reinterpret_cast<u32*>(widget + 0x0C) = 0;
        } else if (selected == 0x16 &&
                   part_count >= static_cast<u32>(ed.list_offset) + 0x15u) {
            *reinterpret_cast<u32*>(widget + 0x0C) = 0x14;
        }
    }

    if ((*reinterpret_cast<u32*>(widget + 0x18) - 1u) == old_selection &&
        *reinterpret_cast<u32*>(widget + 0x0C) == 0) {
        ed.list_offset = 0;
    }

    AsdUiObject_Update(ed.menu_current);

    f32 new_time = *reinterpret_cast<f32*>(reinterpret_cast<u8*>(ed.parts) + 0x74);
    if (new_time != old_time) {
        rebuild_part = 1;
    }
    if (ed.menu_pending != nullptr) {
        ed.menu_current = ed.menu_pending;
        ed.menu_pending = nullptr;
    }

    AsdMem_Free(work);

    u32 result;
    if (ed.flag_07 == 0) {
        result = 0x00800001u;
    } else {
        ed.flag_07 = 0;
        ed.flag_08 = 1;
        ed.list_offset = 0;
        result = 0;
        *reinterpret_cast<u32*>(widget + 0x0C) = 0;
    }

    UiDraw_Bind(ed.parts, reinterpret_cast<void*>(kEditorDrawDesc), 0x80);

    if (UiInput_Trigger2(0x19) != 0) {
        ed.speed_mode = ed.speed_mode == 1 ? 0 : 1;
    } else if (Ui_PressedB(0) != 0) {
        if (ed.speed_mode == 1) {
            ed.speed_mode = 2;
        }
    }

    if (ed.speed_mode == 1) {
        UiText_Draw(0x1C4, 0x17, 5, "STOP");
    } else if (ed.speed_mode == 2) {
        UiText_Draw(0x1C4, 0x17, 5, "SLOW");
    }

    if (ed.menu_current != widget) {
        if (Ui_PressedB(0x0A) != 0) {
            ed.flag_06 = 1;
        }
    }

    u32 list_index = static_cast<u32>(ed.list_offset) +
                     *reinterpret_cast<u32*>(widget + 0x0C);

    if (ed.flag_06 != 0 ||
        (ed.menu_current == widget &&
         (*reinterpret_cast<u32*>(widget + 0x0C) != old_selection || list_changed != 0))) {
        if (ed.work_part != nullptr) {
            AsdPart_Close(ed.work_part, 3);
            ed.work_part = nullptr;
        }
        if (AsdParts_Count(ed.parts) > list_index) {
            if (ed.selected_part != nullptr) {
                AsdPart_Release(ed.selected_part, 3);
                ed.selected_part = nullptr;
            }
            u8* part = reinterpret_cast<u8*>(AsdParts_Get(ed.parts, list_index));
            ed.work_part = AsdPart_Wrap(*reinterpret_cast<void**>(part + 0x90));
            UiDraw_Bind(reinterpret_cast<void*>(kEditorDrawDescAlt), part, 0x80);
        }
        ed.flag_06 = 0;
    } else {
        s32 pressed = Ui_PressedB(9);
        if ((pressed | rebuild_part) != 0) {
            if (ed.selected_part != nullptr) {
                AsdPart_Release(ed.selected_part, 3);
                ed.selected_part = nullptr;
                if (rebuild_part == 0) {
                    goto after_rebuild;
                }
            }
            ed.selected_part = EffParts_Create(ed.parts);
            AsdPart_Setup1(ed.selected_part, reinterpret_cast<void*>(0x004D8C70));
            AsdPart_Setup2(ed.selected_part, reinterpret_cast<void*>(0x004D8C10));
            AsdPart_SetScale(ed.selected_part, 1.0f);
            AsdPart_SetValue(ed.selected_part,
                             *reinterpret_cast<void**>(0x004D8C20 + 0x64));
        }
    }

after_rebuild:
    if (ed.flag_00 != 0) {
        UiText_Draw(0xAA, 0, 6, "2D");
    }

    if (ed.selected_part != nullptr) {
        u32 now = static_cast<u32>(AsdPart_GetCount(ed.selected_part));
        u32 all = *reinterpret_cast<u32*>(reinterpret_cast<u8*>(ed.selected_part) + 0x84);
        UiText_Draw(0xAA, 0x0C, 6, "ALL:%d NOW:%d", now, all);

        if (ed.speed_mode == 0) {
            AsdPart_Play(ed.selected_part);
        } else if (ed.speed_mode == 1) {
            if (Ui_PressedB(1) != 0) {
                AsdPart_Play(ed.selected_part);
            }
        } else if (ed.speed_mode == 2) {
            if (ed.frame_counter == 0) {
                AsdPart_Play(ed.selected_part);
            }
        }

        AsdPart_Update(ed.selected_part);
        if (AsdPart_Update2(ed.selected_part) != 0) {
            ++ed.timer;
            if (ed.timer < 0x18) {
                UiText_Draw(0x0A, 0xF0, 0, "RL BUTTON RELEASE KEYWAIT");
            } else if (ed.timer >= 0x30) {
                ed.timer = 0;
            }
        }
    } else {
        if (ed.work_part != nullptr) {
            AsdPart_Update3(ed.work_part);
            if (ed.speed_mode == 0) {
                AsdPart_Stop(ed.work_part);
            } else if (ed.speed_mode == 2) {
                if (ed.frame_counter != 0) {
                    u8 previous = ed.frame_counter;
                    u8 next = static_cast<u8>(previous + 1u);
                    ed.frame_counter = next;
                    if ((previous & 8u) != 0) {
                        ed.frame_counter = 0;
                    }
                } else {
                    AsdPart_Stop(ed.work_part);
                }
            }
        }
    }

    // 0x002fda3c: hovering element lookup and draw-command reprofiling.
    if (AsdParts_Count(ed.parts) > list_index) {
        u8* part = reinterpret_cast<u8*>(AsdParts_Get(ed.parts, list_index));
        u8* current_part = reinterpret_cast<u8*>(AsdParts_Current());
        if (*reinterpret_cast<u16*>(current_part + 4) == 1) {
            u8* element = *reinterpret_cast<u8**>(part + 0x90);
            u8* table = *reinterpret_cast<u8**>(current_part + 0x0C);
            u16 key_a = *reinterpret_cast<u16*>(element + 4);
            u16 key_b = *reinterpret_cast<u16*>(element + 0x0C);

            u8* found = nullptr;
            for (u32 k = 0; k < 13; ++k) {
                u8* entry_table = reinterpret_cast<u8*>(g_AsdEditorDrawTable[k]);
                if (entry_table == nullptr) {
                    continue;
                }
                u8* cursor = entry_table;
                u8* node = *reinterpret_cast<u8**>(cursor);
                u8* hit = nullptr;
                while (node != nullptr) {
                    if (*reinterpret_cast<u16*>(node + 4) == key_a &&
                        *reinterpret_cast<u16*>(node + 8) == key_b) {
                        hit = node;
                        break;
                    }
                    cursor += 0x1C;
                    node = *reinterpret_cast<u8**>(cursor);
                }
                if (hit != nullptr) {
                    found = *reinterpret_cast<u8**>(cursor + 4);
                    break;
                }
            }

            u16 element_type = *reinterpret_cast<u16*>(element + 0x1C);
            s32 marker;
            if (element_type == 5 || element_type == 6) {
                marker = -1;
                *reinterpret_cast<u32*>(table + 0xC0) = 0;
                *reinterpret_cast<u32*>(table + 0xC4) = 1;
            } else {
                marker = 0;
            }

            if (found != nullptr && *reinterpret_cast<u32*>(found + 0x18) != 0) {
                u32 count = *reinterpret_cast<u32*>(found + 0x18);
                u8* array = *reinterpret_cast<u8**>(found + 0x14);
                for (u32 i = 0; i < count; ++i) {
                    if (array[4 + i * 0x18] == 0x1A &&
                        *reinterpret_cast<u32*>(array + 0x14 + i * 0x18) == 0xC7F12000u) {
                        *reinterpret_cast<u32*>(array + 0x10 + i * 0x18) = static_cast<u32>(marker);
                        u8* second = *reinterpret_cast<u8**>(found + 0x14);
                        *reinterpret_cast<u32*>(second + 0x0C + i * 0x18) = static_cast<u32>(marker);
                    }
                }
            }
        }
    }

    // 0x002fdb8c: draw the element type label for the current part.
    if (ed.selected_part == nullptr && AsdParts_Count(ed.parts) > list_index) {
        u8* part = reinterpret_cast<u8*>(AsdParts_Get(ed.parts, list_index));
        u8* current_part = reinterpret_cast<u8*>(AsdParts_Current());
        u8* element = *reinterpret_cast<u8**>(part + 0x90);
        u16 element_type = *reinterpret_cast<u16*>(element + 0x1C);
        const char* label = nullptr;
        switch (element_type) {
        case 0:
        case 4:
            label = "%s";
            break;
        case 1:
            label = "%s(TMX)";
            break;
        case 2:
            label = "%s(P2A)";
            break;
        case 3:
            label = "%s(PB)";
            break;
        case 5:
            label = "%s(EP)";
            break;
        case 6:
            label = "%s(EPL)";
            break;
        case 7:
            label = "%s(TLP)";
            break;
        default:
            break;
        }
        if (label != nullptr) {
            UiText_Draw(0xF0, 0, 0, label, *reinterpret_cast<void**>(current_part));
        }
    }

    return reinterpret_cast<void*>(static_cast<uintptr_t>(result));
}

} // namespace smt4::engine
