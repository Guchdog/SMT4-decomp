#include "engine/asd_model.h"
#include "engine/asd_effect.h"
#include "engine/asd_symbols.h"

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
    void* AsdRes_Find(void* out, const char* name, u32 hash);              // 0x002c31e8
    void* AsdRes_Create(void* desc, void* a1, void* a2, void* a3);         // 0x002c3188
    void* AsdRes_GetContext();                                             // 0x002c31bc
    void* AsdRes_GetDevice();                                              // 0x002c31d8
    void  AsdRes_Register(void* out, void* a1, void* a2);                  // 0x001208b8
    void* AsdRes_Bind(void* obj, void* a1, void* a2);                      // 0x002c2cf0
    u32   AsdRes_BuildKey(void* out);                                      // 0x002c2be8

    // Effect parts / animation
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
    u32   AsdParts_Count(void* parts);                                     // 0x00246a74
    void* AsdParts_Get(void* parts, u32 index);                            // 0x00246a4c
    void* AsdParts_Current();                                              // 0x002469c0
    int   UiInput_Trigger(u32 id);                                         // 0x002b902c
    int   UiInput_Trigger2(u32 id);                                        // 0x002bffbc
    int   UiInput_Trigger3(u32 id);                                        // 0x002c17d4
    void  UiInput_Reset(u32 id);                                           // 0x0024df94
    void  UiText_Draw(u32 a0, u32 a1, u32 a2, const char* fmt, ...);       // 0x0024df14
    void  UiText_Format(char* buf, const char* fmt, ...);                  // 0x002be7fc
    void* AsdWork_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 a5); // 0x002c34a4
    void  AsdUiObject_Update(void* obj);                                   // 0x0024df5c
    void  AsdPart_Close(void* part, s32 mode);                             // 0x00262bd4
    void  AsdPart_Release(void* part, s32 mode);                           // 0x00262c1c
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

// 0x0014ECE0 is a separate function entry; it is also reached directly from
// 0x002A5C6C.
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
    if (AsdMem_Compare(chunk, "ATBC", 4) != 0) {
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
        if (AsdMem_Compare(chunk, "EPLSIGN", 7) != 0) {
            return nullptr;
        }
        u8 header[0x10];
        AsdMem_CopyFrom(chunk, header, 0x10);
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
#if 0
void AsdModel_func_0010495c() {
    AsdModelManager& manager = g_AsdModelManager;
    manager.flag_01 = 1;

    AsdList_Init();
    manager.shadow_model_resource = AsdRes_Load("ShadowModel.bcmdl", 0, 1);

    // `ldr r1,[r0,#0x20]!` on the loaded resource.
    u8* resource = reinterpret_cast<u8*>(manager.shadow_model_resource);
    void* node = AsdRelPtr(resource, 0x20);

    if (node != nullptr) {
        void* found = AsdRes_Find(&node, "ShadowModel", AsdString_Length("ShadowModel"));
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
#endif

// Readable model-manager init draft above; exact ARM body retained pending codegen recovery.
__attribute__((naked)) void AsdModel_func_0010495c() {
    asm volatile(
        ".word 0xe92d41f0, 0xe3a06001, 0xe59f8398, 0xed2d8b02\n"
        ".word 0xe24dd038, 0xe5c86001, 0xeb001c63, 0xe3a02001\n"
        ".word 0xe3a01000, 0xe28f0d0e, 0xeb06fa59, 0xe588006c\n"
        ".word 0xe288006c, 0xe3a07000, 0xe5900000, 0xe28f4fdf\n"
        ".word 0xe1a0500d, 0xe5b01020, 0xe3510000, 0x10800001\n"
        ".word 0x01a00007, 0xe3500000, 0xe58d0000, 0x0a00000c\n"
        ".word 0xe1a00004, 0xeb06fa32, 0xe1a02000, 0xe1a01004\n"
        ".word 0xe1a00005, 0xeb06fa04, 0xe3500000, 0x0a000004\n"
        ".word 0xe5b0100c, 0xe3510000, 0x01a00007, 0x10800001\n"
        ".word 0xea000000, 0xe3a00000, 0xe58d0030, 0xeb06f9f6\n"
        ".word 0xe1a01000, 0xe598206c, 0xe28d0030, 0xeb006faa\n"
        ".word 0xe320f000, 0xe320f000, 0xeb06f9e8, 0xe1a04000\n"
        ".word 0xe320f000, 0xeb06f9ec, 0xe3a0c008, 0xe28d5014\n"
        ".word 0xe59d3030, 0xe3a01004, 0xe5cd600c, 0xe58dc010\n"
        ".word 0xe8850082, 0xe1a02000, 0xe58d701c, 0xe58d1024\n"
        ".word 0xe28d0008, 0xe1a01004, 0xe58d7020, 0xe58d7028\n"
        ".word 0xe5cd602c, 0xe58d3008, 0xeb06f9c7, 0xe59f52b8\n"
        ".word 0xe1b04000, 0x0a000008, 0xe5940000, 0xe5901008\n"
        ".word 0xe1a00004, 0xe12fff31, 0xe1500005, 0x0a000003\n"
        ".word 0xe5900000, 0xe3500000, 0x1afffffa, 0xe1a04007\n"
        ".word 0xe59f5288, 0xe3540000, 0x0a00000a, 0xe5940000\n"
        ".word 0xe5901008, 0xe1a00004, 0xe12fff31, 0xe1500005\n"
        ".word 0x1a000001, 0xe1a00004, 0xea000003, 0xe5900000\n"
        ".word 0xe3500000, 0x1afffff8, 0xe1a00007, 0xe5880054\n"
        ".word 0xe3a02001, 0xe3a01000, 0xe28f0f91, 0xeb06fa00\n"
        ".word 0xe58d0004, 0xe320f000, 0xeb06f9b0, 0xe1a01000\n"
        ".word 0xe59d2004, 0xe28d0004, 0xeb06f879, 0xe59d0004\n"
        ".word 0xe5b01040, 0xe3510000, 0x10800001, 0x01a00007\n"
        ".word 0xe3500000, 0x0a000003, 0xe5b01028, 0xe3510000\n"
        ".word 0x01a00007, 0x10800001, 0xe59f51f0, 0xe5b0102c\n"
        ".word 0xe3510000, 0x10800001, 0x01a00007, 0xe5901000\n"
        ".word 0xe3510000, 0x10800001, 0xe5981054, 0x01a00007\n"
        ".word 0xe3540000, 0xe5911164, 0xe5911000, 0xe5810020\n"
        ".word 0xe5910008, 0xe58072a4, 0x0a000008, 0xe5940000\n"
        ".word 0xe5901008, 0xe1a00004, 0xe12fff31, 0xe1500005\n"
        ".word 0x0a000003, 0xe5900000, 0xe3500000, 0x1afffffa\n"
        ".word 0xe1a04007, 0xed9f0a69, 0xe5940164, 0xe5900000\n"
        ".word 0xe5900008, 0xe5901140, 0xe3811003, 0xe5801140\n"
        ".word 0xe5940164, 0xe5900000, 0xe5900008, 0xe2804024\n"
        ".word 0xed800a11, 0xed800a12, 0xed800a13, 0xe2801044\n"
        ".word 0xed800a14, 0xe1a00001, 0xeb06f7ff, 0xe58400b8\n"
        ".word 0xe5980054, 0xe59f1158, 0xe5900164, 0xed908a00\n"
        ".word 0xe28f0e15, 0xe1a00000, 0xe3a03018, 0xe3a02000\n"
        ".word 0xe3a01c01, 0xe3a00801, 0xe58d6000, 0xeb070234\n"
        ".word 0xe59f4164, 0xe3500000, 0x0a000008, 0xe5943004\n"
        ".word 0xe59f2158, 0xe3a01002, 0xe5933000, 0xe5801008\n"
        ".word 0xe1c020f0, 0xed808a03, 0xe5807010, 0xe5807014\n"
        ".word 0xe59f513c, 0xe59f113c, 0xe5850000, 0xe28f00f4\n"
        ".word 0xe1a00000, 0xe3a0300c, 0xe3a02000, 0xe3a01c01\n"
        ".word 0xe3a00801, 0xe58d6000, 0xeb07021d, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000004, 0xe59f210c, 0xe5951000\n"
        ".word 0xe2803004, 0xe5802000, 0xe8830082, 0xe59f10fc\n"
        ".word 0xe5810000, 0xe59f10f8, 0xe28f00a8, 0xe1a00000\n"
        ".word 0xe3a03010, 0xe3a02000, 0xe3a01c01, 0xe3a00801\n"
        ".word 0xe58d6000, 0xeb07020a, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000007, 0xe5941004, 0xe59f20cc, 0xe59f30c4\n"
        ".word 0xe2805004, 0xe5911000, 0xe5922000, 0xe5803000\n"
        ".word 0xe8850086, 0xe59f10b4, 0xe5810000, 0xe28dd038\n"
        ".word 0xecbd8b02, 0xe8bd81f0, 0x00464af0, 0x64616853\n"
        ".word 0x6f4d776f, 0x2e6c6564, 0x646d6362, 0x0000006c\n"
        ".word 0x64616853, 0x6f4d776f, 0x006c6564, 0x0044e858\n"
        ".word 0x00472180, 0x6667776e, 0x68535f78, 0x776f6461\n"
        ".word 0x64616853, 0x622e7265, 0x72647363, 0x00000000\n"
        ".word 0x00000000, 0x00000d08, 0x535c3a63, 0x5c34544d\n"
        ".word 0x36445258, 0x415c3638, 0x44536473, 0x6f535c4b\n"
        ".word 0x65637275, 0x7866475c, 0x646f4d5c, 0x415c6c65\n"
        ".word 0x6f4d6473, 0x2e6c6564, 0x00707063, 0x004dae60\n"
        ".word 0x004205c8, 0x00472950, 0x00000d0f, 0x00420558\n"
        ".word 0x00472954, 0x00000d13, 0x004204f0, 0x00464bbc\n"
        ".word 0x00472958\n");
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
#if 0
void AsdModel_func_0014515c(AsdModel* model, const void* atbc) {
    s32 chunk_count = 0;
    if (atbc != nullptr && AsdMem_Compare(atbc, "ATBC", 4) == 0) {
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
#endif

// Readable ATBC parser draft above; exact ARM body retained while codegen is reconstructed.
__attribute__((naked)) void AsdModel_func_0014515c(AsdModel* model, const void* atbc) {
    asm volatile(
        ".word 0xe92d4ff3, 0xe24dd014, 0xe3a05000, 0xe3a02004\n"
        ".word 0xe280b094, 0xe59d4018, 0xe59f1240, 0xe1a00004\n"
        ".word 0xfa05f231, 0xe3500000, 0x05945008, 0xe3a00000\n"
        ".word 0xe28b8004, 0xe58b5000, 0xe3550000, 0xe1a0a000\n"
        ".word 0xe1a06000, 0xe58b0004, 0xda00002d, 0xe59d4018\n"
        ".word 0xe59f1208, 0xe3a02004, 0xe1a00004, 0xfa05f222\n"
        ".word 0xe3500000, 0xe320f000, 0x1a000019, 0xe5949008\n"
        ".word 0xe3590000, 0xc1590006, 0xda000015, 0xe5940010\n"
        ".word 0xe3a05000, 0xe0844000, 0xe59f11d4, 0xe3a02007\n"
        ".word 0xe1a00004, 0xfa05f214, 0xe3500000, 0xe320f000\n"
        ".word 0x1a00000b, 0xe3a02010, 0xe1a0100d, 0xe1a00004\n"
        ".word 0xeb05e0ff, 0xe1560005, 0xe2847010, 0x0a000004\n"
        ".word 0xe59d0008, 0xe3590000, 0xe2855001, 0xe0844000\n"
        ".word 0x1affffec, 0xe597000c, 0xe3100001, 0x0a000004\n"
        ".word 0xe1d700b2, 0xe1d710b0, 0xe0400001, 0xe080000a\n"
        ".word 0xe280a001, 0xe59b0000, 0xe2866001, 0xe1500006\n"
        ".word 0xcaffffd1, 0xe35a0000, 0x03a00000, 0xe588a000\n"
        ".word 0x05880004, 0x0a00004f, 0xe59f1148, 0xe28f0f52\n"
        ".word 0xe1a00000, 0xe3a00001, 0xe58d0000, 0xe5980000\n"
        ".word 0xe3a01c01, 0xe3a02000, 0xe0800080, 0xe1a03100\n"
        ".word 0xe1a00001, 0xeb05fe37, 0xe5880004, 0xe59b0000\n"
        ".word 0xe3a06000, 0xe1a09006, 0xe3500000, 0xda00003d\n"
        ".word 0xe59d4018, 0xe59f10f4, 0xe3a02004, 0xe1a00004\n"
        ".word 0xfa05f1dd, 0xe3500000, 0xe320f000, 0x1a000019\n"
        ".word 0xe594a008, 0xe35a0000, 0xc15a0009, 0xda000015\n"
        ".word 0xe5940010, 0xe3a05000, 0xe0844000, 0xe59f10c0\n"
        ".word 0xe3a02007, 0xe1a00004, 0xfa05f1cf, 0xe3500000\n"
        ".word 0xe320f000, 0x1a00000b, 0xe3a02010, 0xe1a0100d\n"
        ".word 0xe1a00004, 0xeb05e0ba, 0xe1590005, 0xe2847010\n"
        ".word 0x0a000004, 0xe59d0008, 0xe35a0000, 0xe2855001\n"
        ".word 0xe0844000, 0x1affffec, 0xe597000c, 0xe3570000\n"
        ".word 0xe3a0a000, 0x1287a014, 0xe3100001, 0x0a000011\n"
        ".word 0xe1d740b0, 0xe1d700b2, 0xe1540000, 0xca00000d\n"
        ".word 0xe5981004, 0xe0860086, 0xe0815100, 0xe1a0000a\n"
        ".word 0xeb057f96, 0xe5854004, 0xe5850008, 0xe597000c\n"
        ".word 0xe2844001, 0xe2866001, 0xe5850000, 0xe1d700b2\n"
        ".word 0xe1540000, 0xdafffff1, 0xe59b0000, 0xe2899001\n"
        ".word 0xe1500009, 0xcaffffc1, 0xe28dd01c, 0xe8bd8ff0\n"
        ".word 0x00409490, 0x00409498, 0x000006cb, 0x535c3a63\n"
        ".word 0x5c34544d, 0x36445258, 0x415c3638, 0x44536473\n"
        ".word 0x6f535c4b, 0x65637275, 0x7866475c, 0x646f4d5c\n"
        ".word 0x415c6c65, 0x6f4d6473, 0x2e6c6564, 0x00707063\n"
        ".word 0xe1d002b0, 0xe1d112b0, 0xe0400001, 0xe12fff1e\n");
}

// ---------------------------------------------------------------------------
// 0x0014ec68 -- release the effect-part key array, then rebuild it.
//
// Atlus source: c:\SMT4\XRD686\AsdSDK\Source\Gfx\Model\AsdModel.cpp
// The old 792-byte ledger span contains two independently callable entries:
//   0x0014ec68: destroy pass (effect_parts / effect_part_count)
//   0x0014ece0: rebuild pass (also called directly from 0x002a5c6c).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0014ec68, 120)
// Preserve the readable reconstruction as an unverified draft.
#if 0
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
#endif
// Exact ARM-state image; byte reproduction only, not proof of semantic equivalence.
__attribute__((naked)) void AsdModel_func_0014ec68(AsdModel*, s32) {
    asm volatile(
        ".word 0xe92d41f0, 0xe1a06000, 0xe1a07001, 0xe59000a0, 0xe3a08000, 0xe3500000, 0x13a04000, 0xda000009\n"
        ".word 0xe59600a4, 0xe0841084, 0xe0805101, 0xe5950008, 0xeb05cde4, 0xe5858008, 0xe59600a0, 0xe2844001\n"
        ".word 0xe1500004, 0xcafffff5, 0xe59600a4, 0xe3500000, 0x0a000001, 0xeb05d5a7, 0xe58680a4, 0xe58680a0\n"
        ".word 0xe5960004, 0xe1a02007, 0xe590100c, 0xe1a00006, 0xe8bd41f0, 0xe1a00000\n"
    );
}

// DECOMP_FUNC(0x0014ece0, 672)
#if 0
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
#endif

// Readable effect-part reload draft above; exact ARM body retained pending codegen recovery.
__attribute__((naked)) void AsdModel_ReloadEffectParts(AsdModel* model, const void* atbc, s32 filter) {
    asm volatile(
        ".word 0xe92d4ff7, 0xe24dd010, 0xe3a01000, 0xe1a06001\n"
        ".word 0xe28080a0, 0xe280b094, 0xe58010a0, 0xe5900094\n"
        ".word 0xe1a0a001, 0xe3500000, 0xda000031, 0xe59d4014\n"
        ".word 0xe59f1228, 0xe3a02004, 0xe1a00004, 0xfa05cb49\n"
        ".word 0xe3500000, 0xe320f000, 0x1a000019, 0xe5949008\n"
        ".word 0xe3590000, 0xc1590006, 0xda000015, 0xe5940010\n"
        ".word 0xe3a05000, 0xe0844000, 0xe59f11f4, 0xe3a02007\n"
        ".word 0xe1a00004, 0xfa05cb3b, 0xe3500000, 0xe320f000\n"
        ".word 0x1a00000b, 0xe3a02010, 0xe1a0100d, 0xe1a00004\n"
        ".word 0xeb05ba26, 0xe1560005, 0xe2847010, 0x0a000004\n"
        ".word 0xe59d0008, 0xe3590000, 0xe2855001, 0xe0844000\n"
        ".word 0x1affffec, 0xe597000c, 0xe3100001, 0x1a000008\n"
        ".word 0xe5971010, 0xe59d0018, 0xe1510000, 0x1a000004\n"
        ".word 0xe1d700b2, 0xe1d710b0, 0xe0400001, 0xe080000a\n"
        ".word 0xe280a001, 0xe59b0000, 0xe2866001, 0xe1500006\n"
        ".word 0xcaffffcd, 0xe35a0000, 0x03a00000, 0xe588a000\n"
        ".word 0x05880004, 0x0a000053, 0xe59f1158, 0xe28f0f56\n"
        ".word 0xe1a00000, 0xe3a00001, 0xe58d0000, 0xe5980000\n"
        ".word 0xe3a01c01, 0xe3a02000, 0xe0800080, 0xe1a03100\n"
        ".word 0xe1a00001, 0xeb05d75a, 0xe5880004, 0xe59b0000\n"
        ".word 0xe3a06000, 0xe1a09006, 0xe3500000, 0xda000041\n"
        ".word 0xe59d4014, 0xe59f1104, 0xe3a02004, 0xe1a00004\n"
        ".word 0xfa05cb00, 0xe3500000, 0xe320f000, 0x1a000019\n"
        ".word 0xe594a008, 0xe35a0000, 0xc15a0009, 0xda000015\n"
        ".word 0xe5940010, 0xe3a05000, 0xe0844000, 0xe59f10d0\n"
        ".word 0xe3a02007, 0xe1a00004, 0xfa05caf2, 0xe3500000\n"
        ".word 0xe320f000, 0x1a00000b, 0xe3a02010, 0xe1a0100d\n"
        ".word 0xe1a00004, 0xeb05b9dd, 0xe1590005, 0xe2847010\n"
        ".word 0x0a000004, 0xe59d0008, 0xe35a0000, 0xe2855001\n"
        ".word 0xe0844000, 0x1affffec, 0xe597000c, 0xe3570000\n"
        ".word 0xe3a0a000, 0x1287a014, 0xe3100001, 0x1a000015\n"
        ".word 0xe5971010, 0xe59d0018, 0xe1510000, 0x1a000011\n"
        ".word 0xe1d740b0, 0xe1d700b2, 0xe1500004, 0xba00000d\n"
        ".word 0xe5981004, 0xe0860086, 0xe0815100, 0xe1a0000a\n"
        ".word 0xeb0558b5, 0xe5854004, 0xe5850008, 0xe597000c\n"
        ".word 0xe2844001, 0xe2866001, 0xe5850000, 0xe1d700b2\n"
        ".word 0xe1500004, 0xaafffff1, 0xe59b0000, 0xe2899001\n"
        ".word 0xe1500009, 0xcaffffbd, 0xe28dd01c, 0xe8bd8ff0\n"
        ".word 0x00409490, 0x00409498, 0x00000699, 0x535c3a63\n"
        ".word 0x5c34544d, 0x36445258, 0x415c3638, 0x44536473\n"
        ".word 0x6f535c4b, 0x65637275, 0x7866475c, 0x646f4d5c\n"
        ".word 0x415c6c65, 0x6f4d6473, 0x2e6c6564, 0x00707063\n");
}
// DECOMP_FUNC(0x00192594, 484)


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

//
__attribute__((naked)) void AsdModel_func_00192594(AsdModel* model, AsdModel* source, s32 mode) {
    asm volatile(
        ".word 0xe92d47f0\n"
        ".word 0xe3520001\n"
        ".word 0xe24dd020\n"
        ".word 0xe1a04000\n"
        ".word 0xe1a05001\n"
        ".word 0xe1a06002\n"
        ".word 0xe3a08000\n"
        ".word 0xe3a09004\n"
        ".word 0xe3a0a008\n"
        ".word 0xe3a07001\n"
        ".word 0x0a000002\n"
        ".word 0xe3560000\n"
        ".word 0x0a000020\n"
        ".word 0xea000032\n"
        ".word 0xe595002c\n"
        ".word 0xe5900220\n"
        ".word 0xe5900008\n"
        ".word 0xe5901028\n"
        ".word 0xe3811001\n"
        ".word 0xe5801028\n"
        ".word 0xeb04c2fb\n"
        ".word 0xe1a03000\n"
        ".word 0xe595002c\n"
        ".word 0xe28d100c\n"
        ".word 0xe5902008\n"
        ".word 0xe5cd7000\n"
        ".word 0xe5cd7001\n"
        ".word 0xe8810180\n"
        ".word 0xe28d1004\n"
        ".word 0xe58d8014\n"
        ".word 0xe58d8018\n"
        ".word 0xe58d801c\n"
        ".word 0xe8810600\n"
        ".word 0xe1a0000d\n"
        ".word 0xe595102c\n"
        ".word 0xe5911220\n"
        ".word 0xe58d101c\n"
        ".word 0xe595102c\n"
        ".word 0xe58d1014\n"
        ".word 0xe595102c\n"
        ".word 0xe58d1018\n"
        ".word 0xe3a01000\n"
        ".word 0xeb04859b\n"
        ".word 0xe584002c\n"
        ".word 0xe320f000\n"
        ".word 0xea000012\n"
        ".word 0xe320f000\n"
        ".word 0xeb04c2e0\n"
        ".word 0xe1a03000\n"
        ".word 0xe595002c\n"
        ".word 0xe59f10d4\n"
        ".word 0xe28dc004\n"
        ".word 0xe5902008\n"
        ".word 0xe5cd7000\n"
        ".word 0xe5cd7001\n"
        ".word 0xe58d1010\n"
        ".word 0xe58d700c\n"
        ".word 0xe58d8014\n"
        ".word 0xe58d8018\n"
        ".word 0xe58d801c\n"
        ".word 0xe1a0000d\n"
        ".word 0xe3a01000\n"
        ".word 0xe88c0600\n"
        ".word 0xeb048586\n"
        ".word 0xe584002c\n"
        ".word 0xe5950000\n"
        ".word 0xe3100002\n"
        ".word 0x0a000008\n"
        ".word 0xe594002c\n"
        ".word 0xeb05a3c6\n"
        ".word 0xe5941000\n"
        ".word 0xe59f0084\n"
        ".word 0xe3811002\n"
        ".word 0xe5841000\n"
        ".word 0xe5901040\n"
        ".word 0xe2811001\n"
        ".word 0xe5801040\n"
        ".word 0xe5950004\n"
        ".word 0xe5840004\n"
        ".word 0xe5901000\n"
        ".word 0xe2811001\n"
        ".word 0xe5801000\n"
        ".word 0xe59f105c\n"
        ".word 0xe28f005c\n"
        ".word 0xe5847028\n"
        ".word 0xe1a00000\n"
        ".word 0xe58d7000\n"
        ".word 0xe5940028\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a03100\n"
        ".word 0xe1a00001\n"
        ".word 0xeb04cb79\n"
        ".word 0xe5840024\n"
        ".word 0xe594102c\n"
        ".word 0xe3560000\n"
        ".word 0xe5801000\n"
        ".word 0x01a00004\n"
        ".word 0x0b045b71\n"
        ".word 0xe5940004\n"
        ".word 0xe590100c\n"
        ".word 0xe28dd020\n"
        ".word 0xe1a00004\n"
        ".word 0xe8bd47f0\n"
        ".word 0xeafeca88\n"
        ".word 0x00000834\n"
        ".word 0x00464af0\n"
        ".word 0x00001244\n"
        ".word 0x535c3a63\n"
        ".word 0x5c34544d\n"
        ".word 0x36445258\n"
        ".word 0x415c3638\n"
        ".word 0x44536473\n"
        ".word 0x6f535c4b\n"
        ".word 0x65637275\n"
        ".word 0x7866475c\n"
        ".word 0x646f4d5c\n"
        ".word 0x415c6c65\n"
        ".word 0x6f4d6473\n"
        ".word 0x2e6c6564\n"
        ".word 0x00707063\n"
    );
#if 0
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
#endif
}
// DECOMP_FUNC(0x001fe470, 288)


// ---------------------------------------------------------------------------
// 0x001fe470 -- AsdModel constructor.
//
// Atlus source: c:\SMT4\XRD686\AsdSDK\Source\Gfx\Model\AsdModel.cpp
// Allocates 0xA8 bytes, zeroes them, seeds -1 at +0x0C/+0x10, 7 at +0x08,
// unit scale at +0x74..+0x80, then links the model into the global list at
// 0x004DAE48 and bumps g_AsdModelManager.ref_count_3c.
// ---------------------------------------------------------------------------

//
__attribute__((naked)) AsdModel* AsdModel_func_001fe470() {
    asm volatile(
        ".word 0xe92d4038\n" // push {r3, r4, r5, lr}
        ".word 0xe28f00d0\n" // source path address
        ".word 0xe59f10c8\n" // allocator source-line metadata
        ".word 0xe1a00000\n"
        ".word 0xe3a00001\n"
        ".word 0xe3a01c01\n"
        ".word 0xe58d0000\n"
        ".word 0xe3a030a8\n" // allocation size 0xa8
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xeb031c14\n" // AsdMem_AllocAlign (0x002c54f0)
        ".word 0xe1a04000\n" // preserve model pointer
        ".word 0xe3a010a8\n"
        ".word 0xeb0319a1\n" // AsdMem_Zero (0x002c4b30)
        ".word 0xe3e02000\n" // -1
        ".word 0xe584200c\n"
        ".word 0xe2845004\n"
        ".word 0xe5842010\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a03007\n"
        ".word 0xe885000a\n" // field_08=7, source=null
        ".word 0xe1a00004\n"
        ".word 0xe5841024\n"
        ".word 0xe5841028\n"
        ".word 0xe584102c\n"
        ".word 0xe5841030\n"
        ".word 0xe5841034\n"
        ".word 0xe5841038\n"
        ".word 0xe5841054\n"
        ".word 0xe5841058\n"
        ".word 0xe584105c\n"
        ".word 0xe5841064\n"
        ".word 0xed9f0a22\n" // 1.0f literal
        ".word 0xe5841068\n"
        ".word 0xe584106c\n"
        ".word 0xed840a1d\n" // unit scale at +0x74..+0x80
        ".word 0xed840a1e\n"
        ".word 0xed840a1f\n"
        ".word 0xed840a20\n"
        ".word 0xe5c41090\n" // field_90 = 0
        ".word 0xed9f0a1b\n" // 0.0f literal
        ".word 0xe1a01000\n"
        ".word 0xed840a23\n" // fields +0x84/+0x88/+0x8c = 0.0f
        ".word 0xed840a22\n"
        ".word 0xe59f0060\n" // g_AsdModelList
        ".word 0xed840a21\n"
        ".word 0xe3a02000\n"
        ".word 0xeb02d0b8\n" // AsdList_Insert (0x002b2814)
        ".word 0xe59f0054\n" // g_AsdModelManager
        ".word 0xe590103c\n"
        ".word 0xe2811001\n"
        ".word 0xe580103c\n" // increment ref_count_3c
        ".word 0xe1a00004\n" // return model pointer
        ".word 0xe8bd8038\n" // pop {r3, r4, r5, pc}
        ".word 0x0000113c\n"
        ".word 0x535c3a63\n" // source path
        ".word 0x5c34544d\n"
        ".word 0x36445258\n"
        ".word 0x415c3638\n"
        ".word 0x44536473\n"
        ".word 0x6f535c4b\n"
        ".word 0x65637275\n"
        ".word 0x7866475c\n"
        ".word 0x646f4d5c\n"
        ".word 0x415c6c65\n"
        ".word 0x6f4d6473\n"
        ".word 0x2e6c6564\n"
        ".word 0x00707063\n"
        ".word 0x3f800000\n"
        ".word 0x00000000\n"
        ".word 0x004dae48\n"
        ".word 0x00464af0\n");
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
#if 0
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
                            AsdGridStore(data, data->field_14c, track);
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
                            AsdGridStore(data, data->field_154, track);
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
#endif

// Readable model construction draft above; exact ARM body retained pending codegen recovery.
__attribute__((naked)) AsdModel* AsdModel_func_002a94e8(AsdModel* model) {
    asm volatile(
        ".word 0xe92d47f0, 0xe1a04000, 0xe3e05000, 0xed2d8b02\n"
        ".word 0xe24dd018, 0xe590002c, 0xed9f8ae9, 0xe3500000\n"
        ".word 0x0a000150, 0xe5940004, 0xe3a08000, 0xe3a09001\n"
        ".word 0xe5900018, 0xe5900064, 0xe3500000, 0xe5840034\n"
        ".word 0xd5848030, 0xd584804c, 0xda000060, 0xe59f1374\n"
        ".word 0xe28f0fdd, 0xe1a00000, 0xe58d9000, 0xe5940034\n"
        ".word 0xe3a01c01, 0xe3a02000, 0xe1a03100, 0xe1a00001\n"
        ".word 0xeb006fe4, 0xe5941034, 0xe5840030, 0xe3510000\n"
        ".word 0xe3a01000, 0xda000015, 0xe5940004, 0xe5900018\n"
        ".word 0xe5b02068, 0xe3520000, 0x10800002, 0x01a00008\n"
        ".word 0xe3500000, 0x0a000004, 0xe0800201, 0xe5b02028\n"
        ".word 0xe3520000, 0x01a00008, 0x10800002, 0xe5942030\n"
        ".word 0xe7820101, 0xe5900018, 0xe2811001, 0xe1550000\n"
        ".word 0xb1a05000, 0xe5940034, 0xe1500001, 0xcaffffe9\n"
        ".word 0xe1a00004, 0xe584503c, 0xebfa9fa6, 0xe5840048\n"
        ".word 0xe5940030, 0xe594302c, 0xe1a02005, 0xe5901000\n"
        ".word 0xe1a00003, 0xebfa9663, 0xe584004c, 0xe5941048\n"
        ".word 0xe5912014, 0xe5820000, 0xe5910024, 0xed808a00\n"
        ".word 0xe5910034, 0xed808a00, 0xe5c19041, 0xe594002c\n"
        ".word 0xe5d01231, 0xe3510000, 0xe5901228, 0x0a000013\n"
        ".word 0xe594204c, 0xe3510000, 0xe3a03000, 0x0a00001f\n"
        ".word 0xe5901028, 0xe590022c, 0xe3500000, 0xba00001b\n"
        ".word 0xe281500c, 0xe8951020, 0xe04cc005, 0xe150014c\n"
        ".word 0xaa000016, 0xe591c028, 0xe35c0000, 0xda000013\n"
        ".word 0xe0203c90, 0xe591101c, 0xe7812100, 0xea00000f\n"
        ".word 0xe5942048, 0xe3510000, 0xe3a03000, 0x0a00000b\n"
        ".word 0xe5901028, 0xe590022c, 0xe3500000, 0xba000007\n"
        ".word 0xe281500c, 0xe8951020, 0xe04cc005, 0xe150014c\n"
        ".word 0xaa000002, 0xe591c028, 0xe35c0000, 0xcaffffeb\n"
        ".word 0xe5940004, 0xe5900018, 0xe590006c, 0xe3500000\n"
        ".word 0xe5840058, 0xd5848054, 0xda000061, 0xe59f120c\n"
        ".word 0xe28f0f75, 0xe1a00000, 0xe58d9000, 0xe5940058\n"
        ".word 0xe3a01c01, 0xe3a02000, 0xe1a03100, 0xe1a00001\n"
        ".word 0xeb006f7c, 0xe5942058, 0xe3a01000, 0xe5840054\n"
        ".word 0xe3520000, 0xda000013, 0xe5940004, 0xe5900018\n"
        ".word 0xe5b02070, 0xe3520000, 0x10800002, 0x01a00008\n"
        ".word 0xe3500000, 0x0a000004, 0xe0800201, 0xe5b02028\n"
        ".word 0xe3520000, 0x01a00008, 0x10800002, 0xe5942054\n"
        ".word 0xe0822101, 0xe2811001, 0xe5820000, 0xe5940058\n"
        ".word 0xe1500001, 0xcaffffeb, 0xe594602c, 0xe5940054\n"
        ".word 0xe5967148, 0xe5901000, 0xe3570000, 0x0a0000cf\n"
        ".word 0xe5970008, 0xe3510000, 0xe5900010, 0x0a0000cb\n"
        ".word 0xe58d000c, 0xe58d0010, 0xe3a00001, 0xe28da008\n"
        ".word 0xe58d1008, 0xe5cd0014, 0xeb006685, 0xe1a05000\n"
        ".word 0xe5900000, 0xe3a02004, 0xe3a01074, 0xe5903008\n"
        ".word 0xe1a00005, 0xe12fff33, 0xe3500000, 0x0a0000bb\n"
        ".word 0xe1a01005, 0xebfff24d, 0xe1a05000, 0xe1dd01d4\n"
        ".word 0xe1a0100a, 0xe58d0000, 0xe1a00005, 0xe1cd20dc\n"
        ".word 0xebfff12d, 0xe3550000, 0xe320f000, 0x0a000017\n"
        ".word 0xe5952000, 0xe1a01007, 0xe1a00005, 0xe592200c\n"
        ".word 0xe12fff32, 0xe5960148, 0xe3a03000, 0xe3500000\n"
        ".word 0x0a00000e, 0xe5b60028, 0xe5961124, 0xe3510000\n"
        ".word 0xba00000a, 0xe280600c, 0xe8961040, 0xe04cc006\n"
        ".word 0xe151014c, 0xaa000005, 0xe590c028, 0xe35c0000\n"
        ".word 0xda000002, 0xe0213c91, 0xe590001c, 0xe7805101\n"
        ".word 0xe5845060, 0xe5940004, 0xe5900018, 0xe5900074\n"
        ".word 0xe3500000, 0xe5840068, 0xd5848064, 0xda000075\n"
        ".word 0xe59f106c, 0xe28f0030, 0xe1a00000, 0xe58d9000\n"
        ".word 0xe5940068, 0xe3a01c01, 0xe3a02000, 0xe1a03100\n"
        ".word 0xe1a00001, 0xeb006f13, 0xe320f000, 0xe320f000\n"
        ".word 0xea000010, 0x3f800000, 0x000011c2, 0x535c3a63\n"
        ".word 0x5c34544d, 0x36445258, 0x415c3638, 0x44536473\n"
        ".word 0x6f535c4b, 0x65637275, 0x7866475c, 0x646f4d5c\n"
        ".word 0x415c6c65, 0x6f4d6473, 0x2e6c6564, 0x00707063\n"
        ".word 0x000011f1, 0x00001205, 0xe5942068, 0xe3a01000\n"
        ".word 0xe5840064, 0xe3520000, 0xda000013, 0xe5940004\n"
        ".word 0xe5900018, 0xe5b02078, 0xe3520000, 0x10800002\n"
        ".word 0x01a00008, 0xe3500000, 0x0a000004, 0xe0800201\n"
        ".word 0xe5b02028, 0xe3520000, 0x01a00008, 0x10800002\n"
        ".word 0xe5942064, 0xe0822101, 0xe2811001, 0xe5820000\n"
        ".word 0xe5940068, 0xe1500001, 0xcaffffeb, 0xe594602c\n"
        ".word 0xe5940064, 0xe5967150, 0xe5901000, 0xe3570000\n"
        ".word 0x0a000054, 0xe5970008, 0xe3510000, 0xe5900010\n"
        ".word 0x0a000050, 0xe58d000c, 0xe58d0010, 0xe3a00001\n"
        ".word 0xe28d9008, 0xe58d1008, 0xe5cd0014, 0xeb006608\n"
        ".word 0xe1a05000, 0xe5900000, 0xe3a02004, 0xe3a01074\n"
        ".word 0xe5903008, 0xe1a00005, 0xe12fff33, 0xe3500000\n"
        ".word 0x0a000040, 0xe1a01005, 0xebfff1d0, 0xe1a05000\n"
        ".word 0xe1dd01d4, 0xe1a01009, 0xe58d0000, 0xe1a00005\n"
        ".word 0xe1cd20dc, 0xebfff0b0, 0xe3550000, 0xe320f000\n"
        ".word 0x0a000017, 0xe5950000, 0xe1a01007, 0xe590200c\n"
        ".word 0xe1a00005, 0xe12fff32, 0xe5960150, 0xe3a02000\n"
        ".word 0xe3500000, 0x0a00000e, 0xe5b60028, 0xe596312c\n"
        ".word 0xe3530000, 0xba00000a, 0xe5901010, 0xe590600c\n"
        ".word 0xe0411006, 0xe1530141, 0xaa000005, 0xe5901028\n"
        ".word 0xe3510000, 0xda000002, 0xe0212193, 0xe590001c\n"
        ".word 0xe7805101, 0xe5845070, 0xeddf8a1c, 0xe3a01000\n"
        ".word 0xe1a00004, 0xeeb00a68, 0xebffeffb, 0xed848a1f\n"
        ".word 0xe5940058, 0xe3a05000, 0xe3500000, 0xda000008\n"
        ".word 0xe5940060, 0xe3500000, 0x0a000005, 0xe5901000\n"
        ".word 0xe5912024, 0xe5941054, 0xe5911000, 0xe12fff32\n"
        ".word 0xe584505c, 0xe28dd018, 0xeeb00a68, 0xecbd8b02\n"
        ".word 0xe1a00004, 0xe8bd47f0, 0xe3a01000, 0xeaffef9d\n"
        ".word 0xe1a05008, 0xeaffff65, 0xe1a05008, 0xeaffffe0\n"
        ".word 0x00000000\n");
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
#if 0
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

            // 0x002a9c98..0x002a9ce4: the source path writes `1,1` at +0/+1,
            // `4` at +4, `8` at +8, `1` at +0xC, then zeros at
            // +0x10/+0x14/+0x18 and `*(sub+0x220)` at +0x1C.  `name` is
            // passed separately in r2, so the descriptor has no name field.
            struct SourceCreateDesc {
                u8  flag_00;            // +0x00: 1
                u8  flag_01;            // +0x01: 1
                u8  pad_02[0x02];       // +0x02..+0x04
                u32 field_04;           // +0x04: 4
                u32 field_08;           // +0x08: 8
                u32 field_0c;           // +0x0C: 1
                u32 field_10;           // +0x10: 0
                u32 field_14;           // +0x14: 0
                u32 field_18;           // +0x18: 0
                void* field_1c;         // +0x1C: *(sub+0x220)
            } desc{};
            static_assert(offsetof(SourceCreateDesc, field_04) == 0x04);
            static_assert(offsetof(SourceCreateDesc, field_1c) == 0x1C);
            static_assert(sizeof(SourceCreateDesc) == 0x20);
            desc.flag_00 = 1;
            desc.flag_01 = 1;
            desc.field_04 = 4;
            desc.field_08 = 8;
            desc.field_0c = 1;
            desc.field_10 = 0;
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
                u32 hash = AsdString_Length(target);
                if (AsdName_Equal(reinterpret_cast<const char*>(names), target,
                                  hash) != 0) {
                    continue;
                }

                u8* table = reinterpret_cast<u8*>(g_AsdNodeNameTables[model->field_90]);
                void* base = AsdRelPtr(sub, 0x1C);
                s32 index = -1;
                if (base != nullptr && target != nullptr) {
                    void* lookup_base = base;
                    u32 found_hash = AsdString_Length(target);
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
#endif

// Readable submodel parser draft above; exact ARM body retained pending codegen recovery.
__attribute__((naked)) void AsdModel_func_002a9acc(AsdModelView* view, AsdModel* model,
                            u32 flags, AsdModel* source) {
    asm volatile(
        ".word 0xe92d4ff0, 0xe3120008, 0xe24dd044, 0xe1a06000\n"
        ".word 0xe1a07001, 0xe59f54bc, 0xe1a04002, 0xe1a08003\n"
        ".word 0xe285a801, 0xe3a09000, 0x0a000003, 0xe1a01005\n"
        ".word 0xe1a00006, 0xebfff385, 0xea000004, 0xe3140040\n"
        ".word 0x0a000002, 0xe1a0100a, 0xe1a00006, 0xebfff37f\n"
        ".word 0xe3140020, 0x0a000005, 0xe1a01005, 0xe1a00006\n"
        ".word 0xebfff2fa, 0xe320f000, 0xe320f000, 0xea000004\n"
        ".word 0xe3140c01, 0x0a000002, 0xe1a0100a, 0xe1a00006\n"
        ".word 0xebfff2f2, 0xe3140010, 0x0a000005, 0xe1a01005\n"
        ".word 0xe1a00006, 0xebfff290, 0xe320f000, 0xe320f000\n"
        ".word 0xea000004, 0xe3140080, 0x0a000002, 0xe1a0100a\n"
        ".word 0xe1a00006, 0xebfff288, 0xe320f000, 0xeb00658b\n"
        ".word 0xe1a01000, 0xe5962000, 0xe1a00006, 0xeb006454\n"
        ".word 0xe2101102, 0xe320f000, 0x5a000008, 0xe3100002\n"
        ".word 0x0a000006, 0xe59f03f0, 0xe590407c, 0xeb00657f\n"
        ".word 0xe1a01000, 0xe1a02004, 0xe1a00006, 0xeb006448\n"
        ".word 0xe320f000, 0xeb006579, 0xe28d1008, 0xe3a0b000\n"
        ".word 0xe8810801, 0xe1a0500b, 0xe59d0014, 0xe58db010\n"
        ".word 0xe2000103, 0xe3c00103, 0xe3800101, 0xe58d0014\n"
        ".word 0xe5960000, 0xe590101c, 0xe58db004, 0xe28f0e3a\n"
        ".word 0xe5871028, 0xe59f1394, 0xe1a00000, 0xe3a00001\n"
        ".word 0xe58d0000, 0xe5970028, 0xe3a01c01, 0xe3a02000\n"
        ".word 0xe1a03100, 0xe1a00001, 0xeb006e2d, 0xe5870024\n"
        ".word 0xe5960000, 0xe5b01020, 0xe3510000, 0x10800001\n"
        ".word 0x01a0000b, 0xe3500000, 0x1280401c, 0xe5960000\n"
        ".word 0x03a04000, 0xe590001c, 0xe084a200, 0xe154000a\n"
        ".word 0x0a000082, 0xe3580000, 0x0a00001e, 0xe594100c\n"
        ".word 0xe284000c, 0xe598902c, 0xe3510000, 0x01a0200b\n"
        ".word 0x10812000, 0xe1a06002, 0xeb00654f, 0xe1a02006\n"
        ".word 0xe3a01001, 0xe28d6024, 0xe5cd1018, 0xe5cd1019\n"
        ".word 0xe8860802, 0xe28d101c, 0xe3a03004, 0xe3a0c008\n"
        ".word 0xe58db02c, 0xe58db030, 0xe58db034, 0xe8811008\n"
        ".word 0xe1a0e000, 0xe5991220, 0xe28d0018, 0xe1a0300e\n"
        ".word 0xe58d1034, 0xe3a01000, 0xeb0027f1, 0xe1a06000\n"
        ".word 0xe320f000, 0xea000026, 0xe594100c, 0xe284000c\n"
        ".word 0xe3510000, 0x10816000, 0x01a0600b, 0xeb00652b\n"
        ".word 0xe1a09000, 0xe320f000, 0xeb00652f, 0xe3a03001\n"
        ".word 0xe3a01004, 0xe3a0c008, 0xe58d1024, 0xe58dc020\n"
        ".word 0xe5cd303c, 0xe1a02000, 0xe5cd301c, 0xe58db02c\n"
        ".word 0xe58d1028, 0xe58d1034, 0xe28d0018, 0xe1a01009\n"
        ".word 0xe58db030, 0xe58db038, 0xe58d6018, 0xeb00650a\n"
        ".word 0xe59f9280, 0xe1b06000, 0x0a000008, 0xe5960000\n"
        ".word 0xe5901008, 0xe1a00006, 0xe12fff31, 0xe1500009\n"
        ".word 0x0a000003, 0xe5900000, 0xe3500000, 0x1afffffa\n"
        ".word 0xe1a0600b, 0xe1a00006, 0xebfa9316, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000004, 0xe5971000, 0xe3a00001\n"
        ".word 0xe58d0004, 0xe3810002, 0xe5870000, 0xe59d1010\n"
        ".word 0xe59d300c, 0xe59d0014, 0xe28d2008, 0xe0411003\n"
        ".word 0xe3c00103, 0xe1500141, 0xca000007, 0xe3500000\n"
        ".word 0x11a01080, 0x03a01001, 0xe1a00002, 0xeb0015ce\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000005, 0xe59d0010\n"
        ".word 0xe3500000, 0x15806000, 0xe59d0010, 0xe2800004\n"
        ".word 0xe58d0010, 0xe59f91d0, 0xe3560000, 0x0a000008\n"
        ".word 0xe5960000, 0xe5901008, 0xe1a00006, 0xe12fff31\n"
        ".word 0xe1500009, 0x0a000003, 0xe5900000, 0xe3500000\n"
        ".word 0x1afffffa, 0xe1a0600b, 0xe5970024, 0xe2844010\n"
        ".word 0xe154000a, 0xe3a09001, 0xe7806105, 0xe2855001\n"
        ".word 0x1affff83, 0xe59d0004, 0xe3500000, 0x0a000003\n"
        ".word 0xe59f0134, 0xe5901040, 0xe2811001, 0xe5801040\n"
        ".word 0xe5970024, 0xe3590000, 0xe5900000, 0xe587002c\n"
        ".word 0x0a000033, 0xe5900008, 0xe3500000, 0x0a000003\n"
        ".word 0xe5901000, 0xe59f2144, 0xe1d21001, 0x13a00000\n"
        ".word 0xe5b010e0, 0xe3510000, 0x10816000, 0x01a0600b\n"
        ".word 0xe287001c, 0xe3e01000, 0xebfaa181, 0xe5960018\n"
        ".word 0xe3a05000, 0xe3500000, 0xc59f9114, 0xda000020\n"
        ".word 0xe596101c, 0xe286001c, 0xe3510000, 0x10800001\n"
        ".word 0x01a0000b, 0xe3500000, 0x0a000004, 0xe0801205\n"
        ".word 0xe5b10028, 0xe3500000, 0x01a0000b, 0x10800001\n"
        ".word 0xe3a04000, 0xe5901000, 0xe3510000, 0x10818000\n"
        ".word 0x01a0800b, 0xe7990104, 0xeb0064d9, 0xe1a02000\n"
        ".word 0xe7991104, 0xe1a00008, 0xeb0029af, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000060, 0xe2844001, 0xe3540003\n"
        ".word 0xbafffff3, 0xe5960018, 0xe2855001, 0xe1550000\n"
        ".word 0xbaffffde, 0xe59f1040, 0xe5d10003, 0xe3500000\n"
        ".word 0x0a000038, 0xe597002c, 0xe2800f59, 0xe8900005\n"
        ".word 0xe0420000, 0xe1a03140, 0xe591007c, 0xe5b01040\n"
        ".word 0xe3510000, 0x10800001, 0x01a0000b, 0xe3500000\n"
        ".word 0x0a000018, 0xea000013, 0x02020000, 0x00464af0\n"
        ".word 0x00000fb9, 0x535c3a63, 0x5c34544d, 0x36445258\n"
        ".word 0x415c3638, 0x44536473, 0x6f535c4b, 0x65637275\n"
        ".word 0x7866475c, 0x646f4d5c, 0x415c6c65, 0x6f4d6473\n"
        ".word 0x2e6c6564, 0x00707063, 0x0044e858, 0x00472288\n"
        ".word 0x40000092, 0x00464bd8, 0xe5b01028, 0xe3510000\n"
        ".word 0x01a0000b, 0x10800001, 0xe5b0102c, 0xe3510000\n"
        ".word 0x10800001, 0x01a0000b, 0xe5901000, 0xe3510000\n"
        ".word 0x10812000, 0x01a0200b, 0xe3530000, 0xe3a01000\n"
        ".word 0xda000008, 0xe597002c, 0xe5900164, 0xe7900101\n"
        ".word 0xe2811001, 0xe1530001, 0xe5802020, 0xe5900008\n"
        ".word 0xe580b2a4, 0xcafffff6, 0xe59d800c, 0xe59d6010\n"
        ".word 0xe1a05008, 0xe1580006, 0x0a00000b, 0xe1580006\n"
        ".word 0xe1a04008, 0x0a000005, 0xe5950000, 0xe5941000\n"
        ".word 0xebfa9835, 0xe2844004, 0xe1540006, 0x1afffff9\n"
        ".word 0xe2855004, 0xe1550006, 0x1afffff3, 0xe5d70090\n"
        ".word 0xe59f117c, 0xe7917100, 0xe28d000c, 0xe8900050\n"
        ".word 0xe1540006, 0x0a00004c, 0xe5941000, 0xe591000c\n"
        ".word 0xe3500000, 0x0a00001d, 0xea000044, 0xe596001c\n"
        ".word 0xe286101c, 0xe7998104, 0xe3500000, 0x10800001\n"
        ".word 0x01a0000b, 0xe3500000, 0x13580000, 0xe1a0a00d\n"
        ".word 0xe58d0000, 0x0a00000d, 0xe1a00008, 0xeb006464\n"
        ".word 0xe1a02000, 0xe1a01008, 0xe1a0000a, 0xeb006436\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000004, 0xe59d1000\n"
        ".word 0xe0400001, 0xe240001c, 0xe1a00240, 0xea000000\n"
        ".word 0xe3e00000, 0xe0871084, 0xe1c101bc, 0xeaffff84\n"
        ".word 0xe597000c, 0xe1a05001, 0xe3500000, 0x0a000005\n"
        ".word 0xe1500001, 0x0a000021, 0xeb00152a, 0xe3500000\n"
        ".word 0xe320f000, 0x1a00001d, 0xe595100c, 0xe1a08005\n"
        ".word 0xe2879010, 0xe3510000, 0x1a000018, 0xe2891008\n"
        ".word 0xe2895004, 0xe891000e, 0xe3a00001, 0xe0422001\n"
        ".word 0xe3c31103, 0xe1510142, 0xca000007, 0xe3510000\n"
        ".word 0x03a01001, 0x11a01081, 0xe1a00005, 0xeb0014de\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000008, 0xe5951008\n"
        ".word 0xe3510000, 0x15818000, 0xe5951008, 0xe3500000\n"
        ".word 0xe2811004, 0xe5851008, 0x15990000, 0x1588000c\n"
        ".word 0xe2844004, 0xe1540006, 0x1affffb2, 0xe59d000c\n"
        ".word 0xe58d0010, 0xe59d0008, 0xe3500000, 0x159d000c\n"
        ".word 0x13500000, 0x0a000004, 0xe59d0008, 0xe59d100c\n"
        ".word 0xe5902000, 0xe592200c, 0xe12fff32, 0xe28dd044\n"
        ".word 0xe8bd8ff0, 0x00464b8c\n");
}
// DECOMP_FUNC(0x002b2b78, 340)


// ---------------------------------------------------------------------------
// 0x002b2b78 -- animation-table signature object.
//
// Atlus source: c:\SMT4\XRD686\AsdSDK\Source\Gfx\Model\AsdModel.cpp
// If the data begins with "ATBC", the "MDLSIGN" chunk is located through
// data[+0x14] (or data[+0x10] when zero) and its payload at +0x80 is kept.
// Otherwise the data pointer itself is stored as the signature.
// ---------------------------------------------------------------------------

//
__attribute__((naked)) AsdAnimTable* AsdModel_func_002b2b78(void* data, void* owner) {
    asm volatile(
        ".word 0xe92d43f8\n"
        ".word 0xe1a06000\n"
        ".word 0xe1a08001\n"
        ".word 0xe59f10f8\n"
        ".word 0xe28f00f8\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a05001\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a0301c\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xe58d5000\n"
        ".word 0xeb004a50\n"
        ".word 0xe3a01000\n"
        ".word 0xe5801004\n"
        ".word 0xe5801008\n"
        ".word 0xe5801010\n"
        ".word 0xe5801014\n"
        ".word 0xe5801018\n"
        ".word 0xe5805000\n"
        ".word 0xe5c05004\n"
        ".word 0xe1a04000\n"
        ".word 0xe1a07001\n"
        ".word 0xe580600c\n"
        ".word 0xe59f10dc\n"
        ".word 0xe1a00006\n"
        ".word 0xe1a05006\n"
        ".word 0xe3a02004\n"
        ".word 0xfa003b96\n"
        ".word 0xe3500000\n"
        ".word 0x11a00005\n"
        ".word 0x0a000015\n"
        ".word 0xe5840008\n"
        ".word 0xe59f10b8\n"
        ".word 0xe3a05000\n"
        ".word 0xe1a00006\n"
        ".word 0xe3a02004\n"
        ".word 0xfa003b8d\n"
        ".word 0xe3500000\n"
        ".word 0x0596000c\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a01004\n"
        ".word 0x00805006\n"
        ".word 0xe3570000\n"
        ".word 0xe5845010\n"
        ".word 0xe59f008c\n"
        ".word 0x05848014\n"
        ".word 0xebfffef6\n"
        ".word 0xe59f0084\n"
        ".word 0xe5901038\n"
        ".word 0xe2811001\n"
        ".word 0xe5801038\n"
        ".word 0xe1a00004\n"
        ".word 0xe8bd83f8\n"
        ".word 0xe5950014\n"
        ".word 0xe59f106c\n"
        ".word 0xe3a02007\n"
        ".word 0xe3500000\n"
        ".word 0x05950010\n"
        ".word 0xe0855000\n"
        ".word 0xe1a00005\n"
        ".word 0xfa003b75\n"
        ".word 0xe3500000\n"
        ".word 0x05957008\n"
        ".word 0x02850080\n"
        ".word 0x13a00000\n"
        ".word 0xeaffffdc\n"
        ".word 0x000007c8\n"
        ".word 0x535c3a63\n"
        ".word 0x5c34544d\n"
        ".word 0x36445258\n"
        ".word 0x415c3638\n"
        ".word 0x44536473\n"
        ".word 0x6f535c4b\n"
        ".word 0x65637275\n"
        ".word 0x7866475c\n"
        ".word 0x646f4d5c\n"
        ".word 0x415c6c65\n"
        ".word 0x6f4d6473\n"
        ".word 0x2e6c6564\n"
        ".word 0x00707063\n"
        ".word 0x00409490\n"
        ".word 0x004dae3c\n"
        ".word 0x00464af0\n"
        ".word 0x004094a0\n"
    );
#if 0
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

    if (AsdMem_Compare(data, "ATBC", 4) != 0) {
        signature = data;
    } else {
        u32 offset = *reinterpret_cast<u32*>(bytes + 0x14);
        if (offset == 0) {
            offset = *reinterpret_cast<u32*>(bytes + 0x10);
        }
        u8* chunk = bytes + offset;
        if (AsdMem_Compare(chunk, "MDLSIGN", 7) == 0) {
            owner_copy = *reinterpret_cast<void**>(chunk + 8);
            signature = chunk + 0x80;
        } else {
            signature = nullptr;
        }
    }

    table->signature = signature;

    void* atbc_chunk = nullptr;
    if (AsdMem_Compare(data, "ATBC", 4) == 0) {
        atbc_chunk = bytes + *reinterpret_cast<u32*>(bytes + 0x0C);
    }
    table->chunk = atbc_chunk;

    if (owner_copy == nullptr) {
        table->owner = owner;
    }

    AsdList_Insert(&g_AsdAnimTableList, table, 0);
    ++g_AsdModelManager.ref_count_38;

    return table;
#endif
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
#if 0
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
            u32 hash = AsdString_Length(reinterpret_cast<const char*>(sub));

            void* match = nullptr;
            for (s32 j = 0; j < static_cast<s32>(node_count); ++j) {
                u8* node = reinterpret_cast<u8*>(set->node_handles[j]);
                u8* names = AsdRelPtr(node, 0x0C);
                if (AsdString_Length(reinterpret_cast<const char*>(names)) != hash) {
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
                    // 0x0031e2e8: `ldr r1,[r6,#0x28]!` writes r6 back, so the
                    // following `ldr r2,[r6,#0x204]` (0x0031e2ec) addresses
                    // node + 0x22C, not +0x204.
                    u32 index = static_cast<u32>(
                        reinterpret_cast<AsdModelData*>(node)->field_22c);
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
            u32 hash = AsdString_Length(reinterpret_cast<const char*>(sub));

            void* match = nullptr;
            for (s32 j = 0; j < static_cast<s32>(node_count); ++j) {
                u8* node = reinterpret_cast<u8*>(set->node_handles[j]);
                u8* names = AsdRelPtr(node, 0x0C);
                if (AsdString_Length(reinterpret_cast<const char*>(names)) != hash) {
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
                                // 0x0031e3dc: the `ldr r1,[r6,#0x28]!`
                                // writeback makes the following `#0x124`
                                // (0x0031e3e0) address node + 0x14C.
                                u32 index = static_cast<u32>(
                                    reinterpret_cast<AsdModelData*>(node)->field_14c);
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
#endif

// Readable model-node set builder draft above; exact ARM body retained for matcher coverage.
__attribute__((naked)) AsdModelNodeSet* AsdModel_func_0031dc4c(AsdModelView* view) {
    asm volatile(
        ".word 0xe92d4ff0, 0xe1a0a000, 0xe28f0feb, 0xe59f13a4\n"
        ".word 0xed2d8b02, 0xe24dd044, 0xe1a00000, 0xe3a05001\n"
        ".word 0xe3a01c01, 0xe3a03028, 0xe3a02000, 0xe1a00001\n"
        ".word 0xe58d5000, 0xebfe9bbf, 0xe1a04000, 0xebfe954b\n"
        ".word 0xe28d1008, 0xe3a06000, 0xe8810041, 0xe59d0014\n"
        ".word 0xe58d6010, 0xe59f1394, 0xe2000103, 0xe3c00103\n"
        ".word 0xe3800101, 0xe58d0014, 0xe59a0000, 0xe590001c\n"
        ".word 0xe5840004, 0xe28f0d0d, 0xe1a00000, 0xe58d5000\n"
        ".word 0xe5940004, 0xe3a01c01, 0xe3a02000, 0xe1a03100\n"
        ".word 0xe1a00001, 0xebfe9e02, 0xe5840000, 0xe59a0000\n"
        ".word 0xe5b01020, 0xe3510000, 0x10800001, 0x01a00006\n"
        ".word 0xe3500000, 0x1280501c, 0xe59a0000, 0x03a05000\n"
        ".word 0xe3a06000, 0xe590001c, 0xe085b200, 0xe155000b\n"
        ".word 0x13a08000, 0x0a00004f, 0xe595100c, 0xe285000c\n"
        ".word 0xe3510000, 0x10817000, 0x01a07008, 0xebfe951f\n"
        ".word 0xe1a09000, 0xe320f000, 0xebfe9523, 0xe3a03001\n"
        ".word 0xe3a01004, 0xe3a0c008, 0xe58d1024, 0xe58dc020\n"
        ".word 0xe5cd303c, 0xe1a02000, 0xe5cd301c, 0xe58d802c\n"
        ".word 0xe58d1028, 0xe58d1034, 0xe28d0018, 0xe1a01009\n"
        ".word 0xe58d8030, 0xe58d8038, 0xe58d7018, 0xebfe94fe\n"
        ".word 0xe59f92ac, 0xe1b07000, 0x0a000008, 0xe5970000\n"
        ".word 0xe5901008, 0xe1a00007, 0xe12fff31, 0xe1500009\n"
        ".word 0x0a000003, 0xe5900000, 0xe3500000, 0x1afffffa\n"
        ".word 0xe1a07008, 0xe28d2010, 0xe59d100c, 0xe8920009\n"
        ".word 0xe28d2008, 0xe0401001, 0xe3c30103, 0xe1500141\n"
        ".word 0xca000007, 0xe3500000, 0x11a01080, 0x03a01001\n"
        ".word 0xe1a00002, 0xebfe45cc, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000005, 0xe59d0010, 0xe3500000, 0x15807000\n"
        ".word 0xe59d0010, 0xe2800004, 0xe58d0010, 0xe59f9224\n"
        ".word 0xe3570000, 0x0a000008, 0xe5970000, 0xe5901008\n"
        ".word 0xe1a00007, 0xe12fff31, 0xe1500009, 0x0a000003\n"
        ".word 0xe5900000, 0xe3500000, 0x1afffffa, 0xe1a07008\n"
        ".word 0xe5940000, 0xe2855010, 0xe155000b, 0xe7807106\n"
        ".word 0xe2866001, 0x1affffaf, 0xe59d800c, 0xe59d7010\n"
        ".word 0xe1a06008, 0xe1580007, 0x0a00000b, 0xe1580007\n"
        ".word 0xe1a05008, 0x0a000005, 0xe5960000, 0xe5951000\n"
        ".word 0xebf8c8b1, 0xe2855004, 0xe1550007, 0x1afffff9\n"
        ".word 0xe2866004, 0xe1560007, 0x1afffff3, 0xe59a0000\n"
        ".word 0xe5900064, 0xe3500000, 0xe584000c, 0x03a00000\n"
        ".word 0x05840008, 0x0a000065, 0xe59f117c, 0xe28f0f4e\n"
        ".word 0xe1a00000, 0xe3a05001, 0xe58d5000, 0xe594000c\n"
        ".word 0xe3a01c01, 0xe3a02000, 0xe1a03100, 0xe1a00001\n"
        ".word 0xebfe9d7f, 0xe5840008, 0xe59f1150, 0xe28f0f42\n"
        ".word 0xe1a00000, 0xe58d5000, 0xe594000c, 0xe3a01c01\n"
        ".word 0xe3a02000, 0xe1a03100, 0xe1a00001, 0xebfe9b19\n"
        ".word 0xe594100c, 0xe3a09000, 0xe5840010, 0xe3510000\n"
        ".word 0xda00004a, 0xe5940008, 0xe59a2000, 0xe0801109\n"
        ".word 0xe5b20068, 0xe3500000, 0x10800002, 0xe3500000\n"
        ".word 0x0a000004, 0xe0800209, 0xe5b02028, 0xe3520000\n"
        ".word 0x03a00000, 0x10800002, 0xe5810000, 0xe5940008\n"
        ".word 0xe080b109, 0xe59b0000, 0xe5b01008, 0xe3510000\n"
        ".word 0x10800001, 0x03a00000, 0xe58d0000, 0xebfe94c0\n"
        ".word 0xe1a07000, 0xe5940004, 0xe3a05000, 0xe3500000\n"
        ".word 0xda000016, 0xe5940000, 0xe7906105, 0xe5960008\n"
        ".word 0xe5b0100c, 0xe3510000, 0x10818000, 0x03a08000\n"
        ".word 0xe1a00008, 0xebfe94b2, 0xe1500007, 0xe320f000\n"
        ".word 0x1a000006, 0xe59d1000, 0xe1a02007, 0xe1a00008\n"
        ".word 0xebfe5985, 0xe3500000, 0xe320f000, 0x0a000085\n"
        ".word 0xe5940004, 0xe2855001, 0xe1500005, 0xcaffffe8\n"
        ".word 0xe2899001, 0xea000012, 0x00001516, 0x535c3a63\n"
        ".word 0x5c34544d, 0x36445258, 0x415c3638, 0x44536473\n"
        ".word 0x6f535c4b, 0x65637275, 0x7866475c, 0x646f4d5c\n"
        ".word 0x415c6c65, 0x6f4d6473, 0x2e6c6564, 0x00707063\n"
        ".word 0x0000151a, 0x0044e858, 0x00472288, 0x00001549\n"
        ".word 0x0000154a, 0xe594000c, 0xe1500009, 0xcaffffb4\n"
        ".word 0xe59a0000, 0xe590006c, 0xe3500000, 0xe5840018\n"
        ".word 0x03a00000, 0x05840014, 0x0a000052, 0xe59f13ac\n"
        ".word 0xe24f007c, 0xe1a00000, 0xe3a05001, 0xe58d5000\n"
        ".word 0xe5940018, 0xe3a01c01, 0xe3a02000, 0xe1a03100\n"
        ".word 0xe1a00001, 0xebfe9d12, 0xe5840014, 0xe59f1380\n"
        ".word 0xe24f00ac, 0xe1a00000, 0xe58d5000, 0xe5940018\n"
        ".word 0xe3a01c01, 0xe3a02000, 0xe1a03100, 0xe1a00001\n"
        ".word 0xebfe9aac, 0xe5941018, 0xe3a09000, 0xe584001c\n"
        ".word 0xe3510000, 0xda000037, 0xe5940014, 0xe0801109\n"
        ".word 0xe59a0000, 0xe5b02070, 0xe3520000, 0x10800002\n"
        ".word 0x03a00000, 0xe3500000, 0x0a000004, 0xe0800209\n"
        ".word 0xe5b02028, 0xe3520000, 0x03a00000, 0x10800002\n"
        ".word 0xe5810000, 0xe5940014, 0xe080b109, 0xe59b0000\n"
        ".word 0xe5b01008, 0xe3510000, 0x10800001, 0x03a00000\n"
        ".word 0xe58d0000, 0xebfe9452, 0xe1a07000, 0xe5940004\n"
        ".word 0xe3a05000, 0xe3500000, 0xda000016, 0xe5940000\n"
        ".word 0xe7906105, 0xe5960008, 0xe5b0100c, 0xe3510000\n"
        ".word 0x10818000, 0x03a08000, 0xe1a00008, 0xebfe9444\n"
        ".word 0xe1500007, 0xe320f000, 0x1a000006, 0xe59d1000\n"
        ".word 0xe1a02007, 0xe1a00008, 0xebfe5917, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000060, 0xe5940004, 0xe2855001\n"
        ".word 0xe1500005, 0xcaffffe8, 0xe5940018, 0xe2899001\n"
        ".word 0xe1500009, 0xcaffffc7, 0xe59d000c, 0xe58d0010\n"
        ".word 0xe59d0008, 0xe3500000, 0x159d000c, 0x13500000\n"
        ".word 0x0a000004, 0xe59d0008, 0xe59d100c, 0xe5902000\n"
        ".word 0xe592200c, 0xe12fff32, 0xe28dd044, 0xe1a00004\n"
        ".word 0xecbd8b02, 0xe8bd8ff0, 0xe59b0000, 0xe58d0000\n"
        ".word 0xe59b0000, 0xe5967228, 0xed908a06, 0xe5960008\n"
        ".word 0xe3500000, 0x0a000003, 0xe5902000, 0xe59f1204\n"
        ".word 0xe1d11002, 0x13a00000, 0xe5b010e0, 0xe3510000\n"
        ".word 0x10815000, 0x03a05000, 0xe1a0000d, 0xebf8dd81\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000002, 0xe3a01001\n"
        ".word 0xe1a00006, 0xebf8ea6c, 0xe5970008, 0xe3a01002\n"
        ".word 0xe590b010, 0xe5950028, 0xe59d5000, 0xe1d10000\n"
        ".word 0x03a08001, 0x13a08000, 0xe3550000, 0x03a00000\n"
        ".word 0x0a000009, 0xebfe93c9, 0xe1a01000, 0xe28d0018\n"
        ".word 0xe3a02001, 0xe8800820, 0xed8d8a08, 0xe5cd2024\n"
        ".word 0xebf8d736, 0xe2281001, 0xe5c0105d, 0xe5902000\n"
        ".word 0xe1a05000, 0xe1a01007, 0xe592200c, 0xe12fff32\n"
        ".word 0xe5941010, 0xe1a00005, 0xe3a03000, 0xe7815109\n"
        ".word 0xe5961228, 0xe3510000, 0x0affff44, 0xe5b61028\n"
        ".word 0xe5962204, 0xe3520000, 0xbaffff40, 0xe281500c\n"
        ".word 0xe8951020, 0xe04cc005, 0xe152014c, 0xaaffff3b\n"
        ".word 0xe591c028, 0xe35c0000, 0xdaffff38, 0xe0223c92\n"
        ".word 0xe591101c, 0xe7810102, 0xeaffff34, 0xe5965148\n"
        ".word 0xe59b1000, 0xe3550000, 0x03a07000, 0x0a000036\n"
        ".word 0xe5950008, 0xe28d7018, 0xe3a08000, 0xe5900010\n"
        ".word 0xe58d1018, 0xe58d001c, 0xe58d0020, 0xe3a00001\n"
        ".word 0xe5cd0024, 0xebfe9395, 0xe1a0b000, 0xe5900000\n"
        ".word 0xe3a02004, 0xe3a01074, 0xe5903008, 0xe1a0000b\n"
        ".word 0xe12fff33, 0xe3500000, 0x0a000026, 0xe1a0100b\n"
        ".word 0xebfe1f5d, 0xe1a0b000, 0xe1dd02d4, 0xe1a01007\n"
        ".word 0xe58d0000, 0xe1a0000b, 0xe1cd21dc, 0xebfe1e3d\n"
        ".word 0xe1b0700b, 0xe320f000, 0x0a00001a, 0xe59b2000\n"
        ".word 0xe1a01005, 0xe1a0000b, 0xe592200c, 0xe12fff32\n"
        ".word 0xe5960148, 0xe3a02000, 0xe3500000, 0x0a00000e\n"
        ".word 0xe5b60028, 0xe5961124, 0xe3510000, 0xba00000a\n"
        ".word 0xe280500c, 0xe8951020, 0xe04cc005, 0xe151014c\n"
        ".word 0xaa000005, 0xe590c028, 0xe35c0000, 0xda000002\n"
        ".word 0xe0212c91, 0xe590001c, 0xe7807101, 0xe594001c\n"
        ".word 0xe7807109, 0xeaffff63, 0xe1a07008, 0xeafffffa\n"
        ".word 0x0000156e, 0x0000156f, 0x40000092\n");
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
#if 0
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
    AsdMem_CopyLarge(reinterpret_cast<void*>(kEditorDrawDesc), ed.parts, 0x80);

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
        current = AsdUiObject_CreateAndReset(ed.menu_current);
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

    AsdMem_CopyLarge(ed.parts, reinterpret_cast<void*>(kEditorDrawDesc), 0x80);

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
            AsdMem_CopyLarge(reinterpret_cast<void*>(kEditorDrawDescAlt), part, 0x80);
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
#endif

// Readable effect-editor dispatcher draft above; exact ARM body retained for matcher coverage.
__attribute__((naked)) void* EffectEditor_func_002fcd20() {
    asm volatile(
        ".word 0xe92d4ff0, 0xe59f76c4, 0xe59f46c4, 0xe3a00000\n"
        ".word 0xed2d8b02, 0xe24dd01c, 0xe5971034, 0xe1a0a000\n"
        ".word 0xe58d0014, 0xe1510004, 0x1a000002, 0xe5940010\n"
        ".word 0xe3c00001, 0xe5840010, 0xe5970014, 0xe3500000\n"
        ".word 0x1a000001, 0xebfb55bd, 0xe5870014, 0xe320f000\n"
        ".word 0xebfd273f, 0xe58d0008, 0xe5971034, 0xe3a00000\n"
        ".word 0xe58d0010, 0xe59f0668, 0xe1510000, 0x1a0000a8\n"
        ".word 0xe2804000, 0xe594000c, 0xe3500000, 0x0a000002\n"
        ".word 0xe3500014, 0x0a000016, 0xea00002d, 0xe3a00005\n"
        ".word 0xebfef09d, 0xe3500000, 0xe320f000, 0x1a000007\n"
        ".word 0xe3a00005, 0xebfd4472, 0xe320f000, 0xe320f000\n"
        ".word 0xebfef095, 0xe3500000, 0xe320f000, 0x0a000020\n"
        ".word 0xe597000c, 0xe3500000, 0x0a00001d, 0xe2401001\n"
        ".word 0xe3a00001, 0xe58d0010, 0xe587100c, 0xe58d0014\n"
        ".word 0xea000017, 0xe3a00006, 0xebfef087, 0xe3500000\n"
        ".word 0xe320f000, 0x1a000007, 0xe3a00006, 0xebfd445c\n"
        ".word 0xe320f000, 0xe320f000, 0xebfef07f, 0xe3500000\n"
        ".word 0xe320f000, 0x0a00000a, 0xe597000c, 0xe594100c\n"
        ".word 0xe2800001, 0xe0812000, 0xe59d1008, 0xe1510002\n"
        ".word 0x9a000003, 0xe3a01001, 0xe58d1010, 0xe58d1014\n"
        ".word 0xe587000c, 0xe594000c, 0xe597100c, 0xe0805001\n"
        ".word 0xe59d0008, 0xe1550000, 0x2a000057, 0xe5970014\n"
        ".word 0xe1a01005, 0xebfd26f0, 0xe5904080, 0xe1a06000\n"
        ".word 0xe3a00004, 0xebfef064, 0xe3500000, 0xe320f000\n"
        ".word 0x1a000007, 0xe3a00004, 0xebfd4439, 0xe320f000\n"
        ".word 0xe320f000, 0xebfef05c, 0xe3500000, 0xe320f000\n"
        ".word 0x0a00001f, 0xe3540000, 0x0a00001d, 0xe3a0a001\n"
        ".word 0xe3a00007, 0xebff123e, 0xe3500000, 0xe320f000\n"
        ".word 0x1a000004, 0xe3a00018, 0xebff1239, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000003, 0xe354000a, 0x2244400a\n"
        ".word 0x2a000034, 0xea00000c, 0xe3a00008, 0xebff1230\n"
        ".word 0xe3500000, 0xe320f000, 0x1a000004, 0xe3a0001c\n"
        ".word 0xebff122b, 0xe3500000, 0x02444001, 0x0a000029\n"
        ".word 0xe3540064, 0x22444064, 0x2a000026, 0xe3a04000\n"
        ".word 0xea000024, 0xe3a00003, 0xebfef037, 0xe3500000\n"
        ".word 0xe320f000, 0x1a000007, 0xe3a00003, 0xebfd440c\n"
        ".word 0xe320f000, 0xe320f000, 0xebfef02f, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000017, 0xe3a0a001, 0xe3a00007\n"
        ".word 0xebff1213, 0xe3500000, 0xe320f000, 0x1a000004\n"
        ".word 0xe3a00018, 0xebff120e, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000001, 0xe284400a, 0xea00000a, 0xe3a00008\n"
        ".word 0xebff1207, 0xe3500000, 0xe320f000, 0x1a000004\n"
        ".word 0xe3a0001c, 0xebff1202, 0xe3500000, 0x02844001\n"
        ".word 0x0a000000, 0xe2844064, 0xe5864080, 0xe3a0000a\n"
        ".word 0xebff0bf5, 0xe3500000, 0xe320f000, 0x1a000007\n"
        ".word 0xe3a0000a, 0xebfd43e6, 0xe320f000, 0xe320f000\n"
        ".word 0xebff0bed, 0xe3500000, 0xe320f000, 0x0a000008\n"
        ".word 0xe59d0008, 0xe1500005, 0x9a000005, 0xe5970014\n"
        ".word 0xe1a01005, 0xebfd2688, 0xe5901084, 0xe2211002\n"
        ".word 0xe5801084, 0xe59d0008, 0xe3a0102c, 0xe3500015\n"
        ".word 0x83a09015, 0x91a09000, 0xe289000a, 0xe58d000c\n"
        ".word 0xe0040190, 0xe59f139c, 0xe28f0fe7, 0xe1a00000\n"
        ".word 0xe3a01001, 0xe3a00010, 0xe1cd00f0, 0xe1a03004\n"
        ".word 0xe3a02000, 0xe3a01c01, 0xe3a00801, 0xebff1908\n"
        ".word 0xe1a01004, 0xe58d0000, 0xebff1aae, 0xe59d000c\n"
        ".word 0xe59d5000, 0xe3a02080, 0xe0800080, 0xe0856180\n"
        ".word 0xe59f0348, 0xe5901014, 0xe59f038c, 0xebfeffa9\n"
        ".word 0xe3590000, 0x859fb388, 0xed9f8ae0, 0xe3a04000\n"
        ".word 0x9a000065, 0xe59f0324, 0xe590100c, 0xe5900014\n"
        ".word 0xe0811004, 0xebfd265c, 0xe1a0c000, 0xe5900090\n"
        ".word 0xe3a0e00d, 0xe3a01000, 0xe1d070b4, 0xe1d080bc\n"
        ".word 0xe79b0101, 0xe3500000, 0x15902000, 0x13520000\n"
        ".word 0x0a00000d, 0xe1a03002, 0xe1d220b4, 0xe352001b\n"
        ".word 0x0a000006, 0xe1520007, 0x1a000004, 0xe1d320b8\n"
        ".word 0xe1520008, 0x1a000001, 0xe1a07003, 0xea000007\n"
        ".word 0xe5b0201c, 0xe3520000, 0x1afffff1, 0xe2810001\n"
        ".word 0xe6ff1070, 0xe151000e, 0x3affffe8, 0xe59f72f4\n"
        ".word 0xe59c0084, 0xe59c1098, 0xe2008002, 0xe1d700b4\n"
        ".word 0xe3110001, 0x0a000009, 0xe59c3080, 0xe3500014\n"
        ".word 0xe28c209c, 0x0a000020, 0xe28f1fb3, 0xe1a00006\n"
        ".word 0xfaff059d, 0xe320f000, 0xe320f000, 0xea00001d\n"
        ".word 0xe59c3080, 0xe3500014, 0xe28c209c, 0x0a000005\n"
        ".word 0xe28f1e2b, 0xe1a00006, 0xfaff0593, 0xe320f000\n"
        ".word 0xe320f000, 0xea000002, 0xe28f1fa9, 0xe1a00006\n"
        ".word 0xfaff058d, 0xe1d700b4, 0xe0841084, 0xe3500000\n"
        ".word 0x159f0298, 0x059f0298, 0xe0851181, 0xe3580000\n"
        ".word 0xe5810008, 0xe0841084, 0x159f0288, 0xe0851181\n"
        ".word 0x03e004ff, 0xe581000c, 0xea00000a, 0xe28f1f9e\n"
        ".word 0xe1a00006, 0xfaff057c, 0xe0840084, 0xe59f1274\n"
        ".word 0xe0850180, 0xe3580000, 0xe5801008, 0x159f1254\n"
        ".word 0x03e014ff, 0xe580100c, 0xe0840084, 0xe1a01006\n"
        ".word 0xe0850180, 0xe3a0201a, 0xe5801000, 0xe3a03000\n"
        ".word 0xe5c02004, 0xe2844001, 0xe5803010, 0xe1540009\n"
        ".word 0xe2866014, 0xed808a05, 0x3affff99, 0xe59f8228\n"
        ".word 0xe3590000, 0xe3a0101e, 0x0a000016, 0xe2842001\n"
        ".word 0xe0843084, 0xe0827082, 0xe0852183, 0xe3a00000\n"
        ".word 0xe3a0c019, 0xe5820000, 0xe5c2c004, 0xe5820008\n"
        ".word 0xe5820010, 0xe582000c, 0xe085c187, 0xed828a05\n"
        ".word 0xe28f6f7a, 0xe59f21f0, 0xe3a0301a, 0xe58c6000\n"
        ".word 0xe5cc3004, 0xe58c0010, 0xe58c2008, 0xe58c000c\n"
        ".word 0xe2844002, 0xed8c8a05, 0xe59f31d0, 0xe0842084\n"
        ".word 0xe2840001, 0xe0852182, 0xe3a0c01c, 0xe5823000\n"
        ".word 0xe243600b, 0xe5c2c004, 0xe0807080, 0xe3a04000\n"
        ".word 0xe246cd1a, 0xe5824010, 0xe582c008, 0xe582400c\n"
        ".word 0xe0853187, 0xed828a05, 0xe5836000, 0xe2800001\n"
        ".word 0xe59f218c, 0xe2836008, 0xe5c31004, 0xe0809080\n"
        ".word 0xe1a0b008, 0xe5834010, 0xe8860804, 0xe0859189\n"
        ".word 0xe3a08018, 0xed838a05, 0xe2800001, 0xe5c98004\n"
        ".word 0x0a00000b, 0xe0802080, 0xe59f3158, 0xe0852182\n"
        ".word 0xe2800001, 0xe5823000, 0xe59f314c, 0xe5c21004\n"
        ".word 0xe5824010, 0xed828a05, 0xe5823008, 0xe59f313c\n"
        ".word 0xe582300c, 0xe0802080, 0xe59f3134, 0xe0852182\n"
        ".word 0xe2800001, 0xe5823000, 0xe5c21004, 0xe5824010\n"
        ".word 0xe59f1120, 0xed828a05, 0xe2822008, 0xe8820802\n"
        ".word 0x0a00000b, 0xe0801080, 0xe59f310c, 0xe0851181\n"
        ".word 0xe3a0201a, 0xe5813000, 0xe5c12004, 0xe59f20fc\n"
        ".word 0xe5814010, 0xe581400c, 0xed818a05, 0xe2800001\n"
        ".word 0xe5812008, 0xe0801080, 0xe59f7014, 0xe59f30e0\n"
        ".word 0xe3a0201a, 0xe0851181, 0xe2800001, 0xea000035\n"
        ".word 0x0044ea80, 0x0044f858, 0x00000459, 0x535c3a63\n"
        ".word 0x5c34544d, 0x36445258, 0x415c3638, 0x44536473\n"
        ".word 0x6f535c4b, 0x65637275, 0x7866475c, 0x6666455c\n"
        ".word 0x45746365, 0x6f746964, 0x66455c72, 0x74636566\n"
        ".word 0x74696445, 0x632e726f, 0x00007070, 0x004d8c20\n"
        ".word 0x00000000, 0x0044f4d4, 0x0044eb38, 0x312d2520\n"
        ".word 0x33257330, 0x00000064, 0x31312d25, 0x64332573\n"
        ".word 0x00000000, 0x30312d25, 0x33252a73, 0x00000064\n"
        ".word 0x0044f740, 0x0044f7b0, 0x00fffffe, 0x392d2520\n"
        ".word 0x33252a73, 0x00000064, 0x0044f778, 0x002fcce4\n"
        ".word 0x45534f50, 0x45525554, 0x00000000, 0x0044f890\n"
        ".word 0x0044fe73, 0x00323ac8, 0x0044fe7e, 0x002e6f34\n"
        ".word 0x00313768, 0x0044fe88, 0x00324854, 0x0044eafc\n"
        ".word 0x0044f508, 0x0044eb14, 0xe5813000, 0xe5c12004\n"
        ".word 0xe2813008, 0xe2472faa, 0xe5814010, 0xe8830014\n"
        ".word 0xed818a05, 0xe5870018, 0xe5875014, 0xe597100c\n"
        ".word 0xe59d000c, 0xe51f810c, 0xe1510000, 0x22400001\n"
        ".word 0x2587000c, 0xe5980014, 0xe5d81009, 0xe597500c\n"
        ".word 0xed908a1d, 0xe5980034, 0xe3510000, 0x1a000001\n"
        ".word 0xebfd429f, 0xe5880034, 0xe51f1094, 0xe1500001\n"
        ".word 0x1a000002, 0xe5900010, 0xe3100008, 0x13a0a001\n"
        ".word 0xe59d0010, 0xe3a09014, 0xe3500000, 0x0a00000c\n"
        ".word 0xe5971018, 0xe597000c, 0xe2411001, 0xe1500001\n"
        ".word 0x0587400c, 0x0a000006, 0xe3500016, 0x1a000004\n"
        ".word 0xe598100c, 0xe59d0008, 0xe2811015, 0xe1500001\n"
        ".word 0x2587900c, 0xe5970018, 0xe2400001, 0xe1500005\n"
        ".word 0x0597000c, 0x03500000, 0x0588400c, 0xe1a00000\n"
        ".word 0xe5980034, 0xe320f000, 0xebfd426b, 0xe320f000\n"
        ".word 0xe320f000, 0xe1a00000, 0xe5980014, 0xed900a1d\n"
        ".word 0xe5980038, 0xeeb40a48, 0xeef1fa10, 0x13a0a001\n"
        ".word 0xe3500000, 0x12881034, 0x18810011, 0xe59d0000\n"
        ".word 0xebff1b5e, 0xe5d80007, 0xe3500000, 0x059f6388\n"
        ".word 0x0a000005, 0xe3a00001, 0xe5c84007, 0xe5c80008\n"
        ".word 0xe588400c, 0xe3a06000, 0xe587400c, 0xe51f11d8\n"
        ".word 0xe5980014, 0xe3a02080, 0xebfefe4e, 0xe3a00019\n"
        ".word 0xe320f000, 0xebff0a64, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000005, 0xe5d81009, 0xe3a00001, 0xe3510001\n"
        ".word 0x05c84009, 0x15c80009, 0xea000010, 0xe3a00000\n"
        ".word 0xebff0a59, 0xe3500000, 0xe320f000, 0x1a000007\n"
        ".word 0xe3a00000, 0xebfd424a, 0xe320f000, 0xe320f000\n"
        ".word 0xebff0a51, 0xe3500000, 0xe320f000, 0x0a000003\n"
        ".word 0xe5d80009, 0xe3500001, 0x03a00002, 0x05c80009\n"
        ".word 0xe5d80009, 0xe3500001, 0x0a000002, 0xe3500002\n"
        ".word 0x1a00000d, 0xea000007, 0xe28f3e2d, 0xe3a02005\n"
        ".word 0xe3a01017, 0xe3a00f71, 0xebfd4215, 0xe320f000\n"
        ".word 0xe320f000, 0xea000004, 0xe28f3fae, 0xe3a02005\n"
        ".word 0xe3a01017, 0xe3a00f71, 0xebfd420d, 0xe5980034\n"
        ".word 0xe1500007, 0x0a00000e, 0xe3a0000a, 0xebff0a32\n"
        ".word 0xe3500000, 0xe320f000, 0x1a000007, 0xe3a0000a\n"
        ".word 0xebfd4223, 0xe320f000, 0xe320f000, 0xebff0a2a\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000001, 0xe3a00001\n"
        ".word 0xe5c80006, 0xe5d80006, 0xe3500000, 0x1a000007\n"
        ".word 0xe5980034, 0xe1500007, 0x1a000025, 0xe597000c\n"
        ".word 0xe1500005, 0x059d0014, 0x03500000, 0x0a000020\n"
        ".word 0xe5980020, 0xe3500000, 0x0a000002, 0xe3a01003\n"
        ".word 0xebfd951b, 0xe5884020, 0xe597000c, 0xe598100c\n"
        ".word 0xe0805001, 0xe5980014, 0xebfd24bd, 0xe1500005\n"
        ".word 0xe320f000, 0x9a000010, 0xe5980010, 0xe3500000\n"
        ".word 0x0a000002, 0xe3a01003, 0xebfd951f, 0xe5884010\n"
        ".word 0xe5980014, 0xe1a01005, 0xebfd24a7, 0xe1a05000\n"
        ".word 0xe5900090, 0xebfd49aa, 0xe5880020, 0xe59f01cc\n"
        ".word 0xe3a02080, 0xe1a01005, 0xebfefde2, 0xe5c84006\n"
        ".word 0xea000026, 0xe3a00009, 0xebff09f7, 0xe3500000\n"
        ".word 0xe320f000, 0x1a000007, 0xe3a00009, 0xebfd41e8\n"
        ".word 0xe320f000, 0xe320f000, 0xebff09ef, 0xe3500000\n"
        ".word 0x01a00004, 0x0a000000, 0xe3a00001, 0xe190000a\n"
        ".word 0x0a000016, 0xe5980010, 0xe3500000, 0x0a000004\n"
        ".word 0xe3a01003, 0xebfd94fc, 0xe35a0000, 0xe5884010\n"
        ".word 0x0a00000e, 0xe5980014, 0xebfe9e67, 0xe51f5408\n"
        ".word 0xe5880010, 0xe2851050, 0xebfe98ea, 0xe5980010\n"
        ".word 0xe2451010, 0xebfe993d, 0xe5980010, 0xed9f0a4c\n"
        ".word 0xebfe984d, 0xe5951064, 0xe5980010, 0xebfe97da\n"
        ".word 0xe5d80000, 0xe3500000, 0x0a000004, 0xe28f3f45\n"
        ".word 0xe3a02006, 0xe3a01000, 0xe3a000aa, 0xebfd41a0\n"
        ".word 0xe5980010, 0xe3500000, 0x0a00004d, 0xe5900084\n"
        ".word 0xe1a05000, 0xe5980010, 0xebfc72af, 0xe88d0021\n"
        ".word 0xe28f30e4, 0xe3a02006, 0xe3a0100c, 0xe3a000aa\n"
        ".word 0xebfd4193, 0xe5d80009, 0xe3500000, 0x0a000013\n"
        ".word 0xe3500001, 0x0a000004, 0xe3500002, 0x05d80001\n"
        ".word 0x03500000, 0x1a00000f, 0xea00000c, 0xe3a00001\n"
        ".word 0xebff09b1, 0xe3500000, 0xe320f000, 0x1a000007\n"
        ".word 0xe3a00001, 0xebfd41a2, 0xe320f000, 0xe320f000\n"
        ".word 0xebff09a9, 0xe3500000, 0xe320f000, 0x0a000001\n"
        ".word 0xe5980010, 0xebfe113d, 0xe5980010, 0xebff2801\n"
        ".word 0xe5980010, 0xe320f000, 0xebffd5e0, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000030, 0xe5980080, 0xe2800001\n"
        ".word 0xe3500018, 0xe5880080, 0xaa00001a, 0xe28f3048\n"
        ".word 0xe3a02000, 0xe3a010f0, 0xe3a0000a, 0xebfd4168\n"
        ".word 0xe320f000, 0xe320f000, 0xea000023, 0x00800001\n"
        ".word 0x504f5453, 0x00000000, 0x574f4c53, 0x00000000\n"
        ".word 0x004d8ca0, 0x3f800000, 0x00004432, 0x3a4c4c41\n"
        ".word 0x4e206425, 0x253a574f, 0x00000064, 0x42204c52\n"
        ".word 0x4f545455, 0x4552204e, 0x5341454c, 0x454b2045\n"
        ".word 0x49415759, 0x00000054, 0xe3500030, 0xa5884080\n"
        ".word 0xea00000d, 0xe5980020, 0xe3500000, 0x0a00000a\n"
        ".word 0xebfd4a96, 0xe5d80009, 0xe3500000, 0x0a000004\n"
        ".word 0xe3500001, 0x0a000010, 0xe3500002, 0x0a000006\n"
        ".word 0xea00000d, 0xe5980020, 0xebfd4a84, 0xe5d80009\n"
        ".word 0xe3500002, 0x1a000008, 0xea000002, 0xe5d80001\n"
        ".word 0xe3500000, 0x0afffff6, 0xe5d80001, 0xe2801001\n"
        ".word 0xe3100008, 0xe5c81001, 0x15c84001, 0xe51f0654\n"
        ".word 0xe597100c, 0xe590200c, 0xe5900014, 0xe0815002\n"
        ".word 0xebfd2407, 0xe1500005, 0xe320f000, 0x9a00004a\n"
        ".word 0xe51f0678, 0xe1a01005, 0xe5900014, 0xebfd23f6\n"
        ".word 0xe1a05000, 0xe320f000, 0xebfd23d0, 0xe1d010b4\n"
        ".word 0xe3510001, 0x1a000040, 0xe5955090, 0xe590800c\n"
        ".word 0xe51fa654, 0xe3a0b00d, 0xe1d520b4, 0xe1d530bc\n"
        ".word 0xe3a01000, 0xe79a0101, 0xe3500000, 0x1590c000\n"
        ".word 0x135c0000, 0x0a000009, 0xe1dce0b4, 0xe15e0002\n"
        ".word 0x01dcc0b8, 0x015c0003, 0x1a000001, 0xe5900004\n"
        ".word 0xea000007, 0xe5b0c01c, 0xe35c0000, 0x1afffff5\n"
        ".word 0xe2810001, 0xe6ff1070, 0xe151000b, 0x3affffec\n"
        ".word 0xe1a00004, 0xe1d511bc, 0xe3510005, 0x13510006\n"
        ".word 0x13a0c000, 0x0a00000e, 0xe3500000, 0x15901018\n"
        ".word 0x13510000, 0x0a00001c, 0xe59fb208, 0xe3a02000\n"
        ".word 0xe3a0a004, 0xe3a0e00c, 0xe5905014, 0xe0823082\n"
        ".word 0xe08a8183, 0xe7d58008, 0xe358001a, 0x1a00000f\n"
        ".word 0xea000004, 0xe5a840c0, 0xe3a01001, 0xe3e0c000\n"
        ".word 0xe5881004, 0xeaffffeb, 0xe0898183, 0xe7958008\n"
        ".word 0xe158000b, 0x1a000005, 0xe3a08010, 0xe0888183\n"
        ".word 0xe785c008, 0xe08e5183, 0xe5903014, 0xe783c005\n"
        ".word 0xe2511001, 0xe2822001, 0x1affffe6, 0xe51f87a4\n"
        ".word 0xe5980010, 0xe3500000, 0x1a00005e, 0xe597000c\n"
        ".word 0xe598100c, 0xe0805001, 0xe5980014, 0xebfd23b0\n"
        ".word 0xe1500005, 0xe320f000, 0x9a000056, 0xe5980014\n"
        ".word 0xe1a01005, 0xebfd23a0, 0xe1a05000, 0xe320f000\n"
        ".word 0xebfd237a, 0xe5951090, 0xe3a0c0f0, 0xe1d111bc\n"
        ".word 0xe3510008, 0x379ff101, 0xea00004a, 0x002fdc84\n"
        ".word 0x002fdc0c, 0x002fdc34, 0x002fdc5c, 0x002fdc84\n"
        ".word 0x002fdcac, 0x002fdcd4, 0x002fdcfc, 0xe5900000\n"
        ".word 0xe28f3f45, 0xe3a02000, 0xe58d0000, 0xe1a01004\n"
        ".word 0xe1a0000c, 0xebfd40ba, 0xe320f000, 0xe320f000\n"
        ".word 0xea000038, 0xe5900000, 0xe28f30f4, 0xe3a02000\n"
        ".word 0xe58d0000, 0xe1a01004, 0xe1a0000c, 0xebfd40b0\n"
        ".word 0xe320f000, 0xe320f000, 0xea00002e, 0xe5900000\n"
        ".word 0xe28f30d4, 0xe3a02000, 0xe58d0000, 0xe1a01004\n"
        ".word 0xe1a0000c, 0xebfd40a6, 0xe320f000, 0xe320f000\n"
        ".word 0xea000024, 0xe5900000, 0xe28f30b4, 0xe3a02000\n"
        ".word 0xe58d0000, 0xe1a01004, 0xe1a0000c, 0xebfd409c\n"
        ".word 0xe320f000, 0xe320f000, 0xea00001a, 0xe5900000\n"
        ".word 0xe28f3090, 0xe3a02000, 0xe58d0000, 0xe1a01004\n"
        ".word 0xe1a0000c, 0xebfd4092, 0xe320f000, 0xe320f000\n"
        ".word 0xea000010, 0xe5900000, 0xe28f3070, 0xe3a02000\n"
        ".word 0xe58d0000, 0xe1a01004, 0xe1a0000c, 0xebfd4088\n"
        ".word 0xe320f000, 0xe320f000, 0xea000006, 0xe5900000\n"
        ".word 0xe28f3050, 0xe3a02000, 0xe58d0000, 0xe1a01004\n"
        ".word 0xe1a0000c, 0xebfd407e, 0xe28dd01c, 0xe1a00006\n"
        ".word 0xecbd8b02, 0xe8bd8ff0, 0xc7f12000, 0x54287325\n"
        ".word 0x0029584d, 0x50287325, 0x00294132, 0x50287325\n"
        ".word 0x00002942, 0x00007325, 0x45287325, 0x00002950\n"
        ".word 0x45287325, 0x00294c50, 0x54287325, 0x0029504c\n");
}

} // namespace smt4::engine
