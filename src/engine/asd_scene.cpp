#include "engine/asd_scene.h"
#include "engine/asd_symbols.h"
#include <cstdint>

namespace smt4::engine {

// ---------------------------------------------------------------------------
// Globals (addresses are the .bss locations used by the listing)
// ---------------------------------------------------------------------------

AsdCameraManager g_AsdCameraManager{};      // 0x0044EA58
AsdCameraDefaults g_AsdCameraDefaults{};    // 0x004D4924
AsdSceneGlobals g_AsdScene{};               // 0x00464C00
AsdProcessPool g_AsdProcessPool{};          // 0x004E3CF4
AsdSequenceState g_AsdSequence{};           // 0x004E3F4C

// The array at 0x004C5830 holds five list heads: both 0x0028674C and
// 0x0032FF4C walk `r5` from 0 to 4 (`cmp r5,#5`, 0x00286824 / 0x0032FF80),
// and 0x0032FFA8 initialises exactly five 0x10-byte entries (0x0032FFC8-
// 0x00330010).
AsdTaskList g_AsdTaskLists[5]{};            // 0x004C5830

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

extern "C" {
    // AsdMemory (c:\SMT4\XRD686\AsdSDK\Source\Sys\Mem\AsdMemory.cpp)
    void  AsdMem_Zero(void* ptr, u32 size);                                 // 0x002c4b30
    void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);         // 0x002c4b84
    void* AsdMem_AllocAlign(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);    // 0x002c54f0
    void  AsdMem_Copy(void* dst, const void* src, u32 size);                // 0x002c5ff4
    void  AsdMem_FillBytes(void* dst, u32 size, u32 value);                 // 0x002c4450

    // Resource database (AsdFile / AsdMemory)
    void* AsdRes_Create(void* desc, void* a1, void* a2, void* a3);          // 0x002c3188
    void* AsdRes_GetContext();                                              // 0x002c31bc
    void* AsdRes_GetDevice();                                               // 0x002c31d8
    u32   AsdRes_BuildKey(void* out);                                       // 0x002c2be8

    // Animation tracks (AsdModel.cpp family; signatures shared with
    // src/engine/asd_model.cpp)
    void* AsdAnim_CreateTrack(void* track, void* context);                  // 0x002a6108
    void  AsdAnim_SetupTrack(void* track, void* desc, void* a2, void* a3,
                             s32 flag);                                     // 0x002a5ca4
    s32   AsdScene_MatchTrack(void* owner, void* track);                    // 0x00245478

    // Camera projection helpers (AsdCamera.cpp)
    void  AsdCamera_InitProjection(void* projection, u32 mode);             // 0x002c2210
    void  AsdCamera_LookAt(void* projection, const f32* eye,
                           const f32* target, const f32* up);               // 0x002c20a8
    void  AsdCamera_SetPerspective(void* projection, u32 mode, f32 p0,
                                   f32 p1, f32 p2, f32 p3);                 // 0x002c1ffc

    // Scene resource constructors (AsdScene.cpp)
    void* AsdScene_CreateFogObject(const AsdSceneCreateDesc* desc,
                                   void* context);                          // 0x001203d8
    void* AsdScene_CreateNodeObject(const AsdSceneCreateDesc* desc,
                                    void* context);                         // 0x0011d8e4
    void* AsdScene_CreateEffectObject(const AsdSceneCreateDesc* desc,
                                      void* context);                       // 0x0011ff20
    void* AsdScene_CreateLightObject(const AsdSceneCreateDesc* desc,
                                     void* context);                        // 0x0012aaf4
    void* AsdScene_CreateEnvObject(const AsdSceneCreateDesc* desc,
                                   void* context);                          // 0x0012b3b0

    // Kernel helpers
    // 0x002C4460 is the process-link routine reached from AsdText as
    // `AsdUi_Attach(void*, void*)`; AsdProcess.cpp calls it with the two
    // packed process handles.
    void  AsdProcess_Attach(u32 parent, u32 child);                         // 0x002c4460
    void* AsdGxCommandList_Create();                                        // 0x002c5d90

    // Widget factory (AsdSequence.cpp / soundTest)
    void* AsdUi_Create(const char* kind, std::uintptr_t name, u32 a2, u32 a3,
                       u32 cb0, u32 cb1, void* obj);                         // 0x002c5978
}

namespace {

// Mirrors `ldr rN,[base,#offset]!; addne base,base,rN` relative pointers.
u8* AsdRelPtr(u8* base, u32 offset) {
    if (base == nullptr) {
        return nullptr;
    }
    const u32 rel = *reinterpret_cast<const u32*>(base + offset);
    return rel != 0 ? base + offset + rel : nullptr;
}

// `ldr r0,[obj]; ldr r1,[r0,#8]; blx r1` -- the virtual type identifier.
void* AsdVtableType(void* object) {
    void** vtable = *reinterpret_cast<void***>(object);
    using GetTypeFn = void* (*)(void*);
    return reinterpret_cast<GetTypeFn>(vtable[2])(object);
}

// Walks the virtual type chain (`ldr r0,[r0]`) until `type` is reached.
void* AsdTypeMatch(void* object, u32 type) {
    if (object == nullptr) {
        return nullptr;
    }
    void* current = AsdVtableType(object);
    while (current != reinterpret_cast<void*>(static_cast<std::uintptr_t>(type))) {
        current = *reinterpret_cast<void**>(current);
        if (current == nullptr) {
            return nullptr;
        }
    }
    return object;
}

// `context->vtable[2](context, size, align)` -- the resource allocator used by
// 0x003102F4-0x00310310 for the 0x74-byte camera track.
void* AsdRes_AllocObject(void* context, u32 size, u32 align) {
    void** vtable = *reinterpret_cast<void***>(context);
    using AllocFn = void* (*)(void*, u32, u32);
    return reinterpret_cast<AllocFn>(vtable[2])(context, size, align);
}

AsdSceneCreateDesc MakeSceneCreateDesc() {
    AsdSceneCreateDesc desc{};
    desc.enabled = 1;   // 0x0010BDBC `strb r7,[sp,#8]`
    desc.visible = 1;   // 0x0010BDC4 `strb r7,[sp,#9]`
    desc.field_0c = 1;  // 0x0010BDC0 `strd r6,r7,[sp,#0x10]`
    return desc;
}

} // namespace

// ===========================================================================
// AsdCamera.cpp
// ===========================================================================

// ---------------------------------------------------------------------------
// 0x00105C50 -- create the camera manager and its two projection blocks.
//
// Atlus source: c:\SMT4\XRD686\AsdSDK\Source\Gfx\Camera\AsdCamera.cpp
// Allocation: 0xA98 bytes (0x00105C6C), zero-filled (0x00105C94).
// Both projections are initialised identically except for the last argument
// of `engine_func_002c1ffc`: 1.6666666 for the first, 1.3333334 for the second
// (0x00105CD8 / 0x00105D14).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00105c50, 340)
void* AsdCamera_func_00105c50(void* name) {
    AsdCamera* camera = static_cast<AsdCamera*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0xA98, 1));   // 0x00105C88
    AsdMem_Zero(camera, 0xA98);                     // 0x00105C94

    g_AsdCameraManager.camera = camera;             // 0x00105CA4

    AsdCamera_InitProjection(&camera->projection_data[0], 1);            // 0x00105CA8
    AsdCamera_LookAt(&camera->projection_data[0],                        // 0x00105CBC
                     g_AsdCameraDefaults.eye,
                     g_AsdCameraDefaults.target,
                     g_AsdCameraDefaults.up);
    AsdCamera_SetPerspective(&camera->projection_data[0], 1,             // 0x00105CE4
                             30.0f, 20.0f, 25600.0f, 1.6666666f);

    AsdCamera_InitProjection(&camera->projection_data[1], 1);            // 0x00105CF0
    AsdCamera_LookAt(&camera->projection_data[1],                        // 0x00105D04
                     g_AsdCameraDefaults.eye,
                     g_AsdCameraDefaults.target,
                     g_AsdCameraDefaults.up);
    AsdCamera_SetPerspective(&camera->projection_data[1], 1,             // 0x00105D20
                             30.0f, 20.0f, 25600.0f, 1.3333334f);

    camera->projections[0] = &camera->projection_data[0];               // 0x00105D2C
    camera->projections[1] = &camera->projection_data[1];

    void* proc = AsdUi_Create("CamManagerProc",                          // 0x00105D50
                              reinterpret_cast<std::uintptr_t>(name),
                              0, 0, 0x0010E508, 0x0010E9CC, camera);
    g_AsdCameraManager.proc = proc;                                     // 0x00105D54
    return proc;
}

// ---------------------------------------------------------------------------
// 0x00310124 -- bind one animation track per scene node to the camera.
//
// Atlus source: c:\SMT4\XRD686\AsdSDK\Source\Gfx\Camera\AsdCamera.cpp
// Outer traversal: `ldr r1,[r4,#0x48]!` resolves the entry list at
// (scene + 0x48 + rel), skips its 0x1C-byte prefix and walks `[scene+0x44]`
// entries of 0x10 bytes (0x00310160-0x003101B4, advance at 0x003103E0).
// Inner traversal: (scene + 0x80 + rel) + index*0x10, then the pre-indexed
// `ldr r1,[r0,#0x28]!` resolves the node at +0x28 (0x003102AC-0x003102D4).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00310124, 804)
AsdCameraAnim* AsdCamera_func_00310124(AsdCameraScene* scene) {
    AsdCameraAnim* anim = static_cast<AsdCameraAnim*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, 0x18, 1));   // 0x00310158

    // `ldr r1,[r4,#0x48]; add r0,r4,#0x48; ... addne r0,r0,#0x1c`
    u8* entry = nullptr;
    if (scene->entry_rel != 0) {
        entry = reinterpret_cast<u8*>(scene) + 0x48 + scene->entry_rel + 0x1C;
    }
    // `add r1,r0,r1,lsl #4` -- when the relative pointer is absent the listing
    // still uses the raw count*16 value as the limit (0x00310188).
    u8* end = entry != nullptr
        ? entry + scene->entry_count * 0x10u
        : reinterpret_cast<u8*>(
              static_cast<std::uintptr_t>(scene->entry_count) * 0x10u);

    anim->scene = scene;                                // 0x00310198

    while (entry != end) {
        // `ldr r1,[r0,#0xc]!` -- effective offset entry+0x0C.
        u8* source = AsdRelPtr(entry, 0x0C);

        void* context = AsdRes_GetContext();            // 0x003101B4
        void* device = AsdRes_GetDevice();              // 0x003101C0

        // Descriptor image at sp+0x28 (0x003101D4-0x00310200).
        AsdCameraCreateDesc desc{};
        desc.source = source;
        desc.field_04 = 1;
        desc.field_08 = 8;
        desc.field_0c = 4;
        desc.field_1c = 4;
        desc.field_24 = 1;

        void* created = AsdRes_Create(                  // 0x00310204
            &desc, context, device,
            reinterpret_cast<void*>(static_cast<std::uintptr_t>(4)));

        // Type-id checks against 0x0044E858 (0x00310208-0x00310238) and
        // 0x0044E820 (0x0031023C-0x00310274).
        anim->object_44E858 = AsdTypeMatch(created, 0x0044E858);
        anim->object_44E820 = AsdTypeMatch(created, 0x0044E820);

        // 0x00310284 `ldr sb,[r8,#0x268]` has no null test: a failed
        // 0x0044E820 cast faults on the original hardware as well.
        AsdCameraAnimOwner* owner = static_cast<AsdCameraAnimOwner*>(
            anim->object_44E820);
        AsdCameraAnimSource* anim_source = owner->source;
        const s32 node_count = scene->node_count;       // 0x00310288

        if (anim_source != nullptr) {
            const f32 duration = anim_source->clip->duration;    // 0x003102A0
            // `cmp fp,#0; ble` -- the clip is read before the count test.
            for (s32 index = 0; index < node_count; ++index) {
                // `ldr r1,[r0,#0x80]!` then `ldr r1,[r0,#0x28]!`
                // (0x003102AC-0x003102D4); effective node offset +0x28.
                u8* node = nullptr;
                if (scene->node_rel != 0) {
                    u8* table = reinterpret_cast<u8*>(scene) + 0x80 +
                                scene->node_rel + index * 0x10u;
                    node = AsdRelPtr(table, 0x28);
                }

                AsdCameraTrackDesc track_desc{};        // 0x003102D8-0x003102F0
                track_desc.source = node;
                track_desc.time = duration;
                track_desc.field_08 = 0x40;
                track_desc.field_0c = 1;

                void* context_now = AsdRes_GetContext(); // 0x003102F4
                void* track_memory = AsdRes_AllocObject(context_now, 0x74, 4); // 0x00310310

                AsdCameraTrack* track = nullptr;
                if (track_memory != nullptr) {
                    track = static_cast<AsdCameraTrack*>(
                        AsdAnim_CreateTrack(track_memory, context_now)); // 0x00310320
                    // `ldrd r2,r3,[sp,#0x34]` passes the raw +0x04/+0x08
                    // descriptor words; the fifth argument is byte +0x0C.
                    AsdAnim_SetupTrack(
                        track, &track_desc,
                        reinterpret_cast<void*>(static_cast<std::uintptr_t>(
                            *reinterpret_cast<const u32*>(&track_desc.time))),
                        reinterpret_cast<void*>(static_cast<std::uintptr_t>(0x40)),
                        track_desc.field_0c);           // 0x0031033C
                }

                anim->track = track;                    // 0x00310340

                // `ldr r0,[r4]; ldr r2,[r0,#0xc]; blx r2` -- vtable slot 3.
                void** track_vtable = *reinterpret_cast<void***>(track);
                using BindFn = void (*)(void*, void*);
                reinterpret_cast<BindFn>(track_vtable[3])(track, anim_source); // 0x00310354

                // 0x0031035C-0x00310384: param_a/param_b (track+0x44/+0x48),
                // argument track+0x50, third float 0.0, then shift the track's
                // current value into previous and store the returned value.
                AsdCameraTrack* live = anim->track;
                const f32 value = live->evaluate(live->evaluate_arg,
                                                 live->param_a, live->param_b,
                                                 0.0f);
                const f32 previous = live->current;
                live->previous = previous;
                live->current = value;
                live->field_58 = 1;

                if (AsdScene_MatchTrack(anim->object_44E820, live) != 0) { // 0x00310394
                    // 0x003103A4-0x003103C8: grid descriptor at +0x28, cells at
                    // +0x1C, index 0, written only when count and rows are > 0.
                    u8* grid = *reinterpret_cast<u8**>(
                        reinterpret_cast<u8*>(anim->object_44E820) + 0x28);
                    const u32 count =
                        (*reinterpret_cast<u32*>(grid + 0x10) -
                         *reinterpret_cast<u32*>(grid + 0x0C)) >> 2;
                    const s32 rows = *reinterpret_cast<s32*>(grid + 0x28);
                    if (static_cast<s32>(count) > 0 && rows > 0) {
                        void** cells = *reinterpret_cast<void***>(grid + 0x1C);
                        cells[0] = live;
                    }
                }
            }
        }

        entry += 0x10;                                  // 0x003103E0
    }

    return anim;                                        // 0x003103F4
}

// ===========================================================================
// AsdScene.cpp
// ===========================================================================

// ---------------------------------------------------------------------------
// 0x0010BD34 -- create the two fog records and register them at
// 0x00464C04 (`ldr r0,[sb,#4]`, 0x0010BE1C).
//
// Allocation: 0x10 bytes (0x0010BD80).  Data block values: 0.3/0.3/0.5/1.0 at
// +0xB4..+0xC0, parameter block {3, 100.0, 5000.0, 10.0} (0x0010BE00-0x0010BE18).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0010bd34, 300)
void AsdScene_func_0010bd34() {
    for (u32 index = 0; index < 2; ++index) {
        AsdSceneFog* fog = static_cast<AsdSceneFog*>(
            AsdMem_AllocAlign(0x100, 0x100, 0, 0x10, 1));    // 0x0010BD90
        fog->field_00 = 0;                                  // 0x0010BD94
        fog->object = nullptr;
        fog->data = nullptr;
        fog->params = nullptr;

        const AsdSceneCreateDesc desc = MakeSceneCreateDesc();
        void* context = AsdRes_GetContext();                // 0x0010BDB0
        void* object = AsdScene_CreateFogObject(&desc, context); // 0x0010BDCC
        fog->object = object;                               // 0x0010BDD0

        AsdSceneFogData* data = static_cast<AsdSceneFogData*>(
            *reinterpret_cast<void**>(reinterpret_cast<u8*>(object) + 0x08));
        fog->data = data;                                   // 0x0010BDD8

        // 0x0010BDE0: `vstmia r1!,{s16}` then `vstmia r1,{s16,s17,s18}`.
        data->field_b4 = 0.3f;
        data->field_b8 = 0.3f;
        data->field_bc = 0.5f;
        data->field_c0 = 1.0f;

        // 0x0010BDEC: `ldr r1,[r0,#0xc8]!` -- effective offset data+0xC8.
        AsdSceneFogParams* params = static_cast<AsdSceneFogParams*>(
            AsdRelPtr(reinterpret_cast<u8*>(data), 0xC8));
        fog->params = params;                               // 0x0010BDFC

        params->kind = 3;                                   // 0x0010BE00
        params->near_distance = 100.0f;                     // 0x0010BE10
        params->far_distance = 5000.0f;                     // 0x0010BE18
        params->density = 10.0f;                            // 0x0010BE08

        g_AsdScene.fogs[index] = fog;                       // 0x0010BE20
    }
}

// ---------------------------------------------------------------------------
// 0x0010E5F0 -- create the two scene slots (node, effect, light, environment).
//
// Allocation: 0x0C bytes per record (0x0010E64C).  Node colour
// 0.2/0.2/0.2/1.0 plus `AsdRes_BuildKey` at +0xC8 (0x0010E694-0x0010E6B4);
// effect colour 0.1/0.0/0.0/1.0, 0.9/0.9/1.0/1.0 at +0xC8, 0.0/1.0/0.0/0.5
// at +0xD8 (0x0010E728-0x0010E764).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0010e5f0, 476)
void AsdScene_func_0010e5f0() {
    for (u32 index = 0; index < 2; ++index) {
        // --- node -----------------------------------------------------------
        AsdSceneObject* node = static_cast<AsdSceneObject*>(
            AsdMem_AllocAlign(0x100, 0x100, 0, 0x0C, 1));    // 0x0010E64C
        node->index = -1;                                   // 0x0010E65C
        node->object = nullptr;
        node->data = nullptr;

        const AsdSceneCreateDesc desc = MakeSceneCreateDesc();
        void* context = AsdRes_GetContext();                // 0x0010E660
        void* object = AsdScene_CreateNodeObject(&desc, context); // 0x0010E680
        node->object = object;                              // 0x0010E684

        AsdSceneNodeData* node_data = static_cast<AsdSceneNodeData*>(
            *reinterpret_cast<void**>(reinterpret_cast<u8*>(object) + 0x08));
        node->data = node_data;                             // 0x0010E68C

        node_data->color_r = 0.2f;                          // 0x0010E694
        node_data->color_g = 0.2f;                          // 0x0010E698
        node_data->color_b = 0.2f;                          // 0x0010E6A0
        node_data->color_a = 1.0f;
        node_data->key = AsdRes_BuildKey(&node_data->color_r); // 0x0010E6AC

        g_AsdScene.slot->nodes[index] = node;               // 0x0010E6C0

        // --- effect ---------------------------------------------------------
        AsdSceneObject* effect = static_cast<AsdSceneObject*>(
            AsdMem_AllocAlign(0x100, 0x100, 0, 0x0C, 1));    // 0x0010E6E0
        effect->index = -1;                                 // 0x0010E6F0
        effect->object = nullptr;
        effect->data = nullptr;

        context = AsdRes_GetContext();                      // 0x0010E6F4
        object = AsdScene_CreateEffectObject(&desc, context); // 0x0010E714
        effect->object = object;                            // 0x0010E718

        AsdSceneEffectData* effect_data = static_cast<AsdSceneEffectData*>(
            *reinterpret_cast<void**>(reinterpret_cast<u8*>(object) + 0x08));
        effect->data = effect_data;                         // 0x0010E720

        effect_data->color_r = 0.1f;                        // 0x0010E740
        effect_data->color_g = 0.0f;
        effect_data->color_b = 0.0f;
        effect_data->color_a = 1.0f;
        effect_data->field_c8 = 0.9f;                       // 0x0010E728
        effect_data->field_cc = 0.9f;
        effect_data->field_d0 = 1.0f;
        effect_data->field_d4 = 1.0f;
        effect_data->field_d8 = 0.0f;                       // 0x0010E758
        effect_data->field_dc = 1.0f;
        effect_data->field_e0 = 0.0f;
        effect_data->field_e4 = 0.5f;                       // 0x0010E764

        g_AsdScene.slot->effects[index] = effect;           // 0x0010E770

        // --- light and environment -----------------------------------------
        g_AsdScene.slot->lights[index] = AsdScene_func_001186b4();        // 0x0010E780
        g_AsdScene.slot->environments[index] = AsdScene_func_00118c7c();  // 0x0010E798
    }
}

// ---------------------------------------------------------------------------
// 0x001186B4 -- create one light record.
//
// Allocation: 0x0C bytes (0x001186E0).  Data block at +0xB8 holds kind 2
// (0x00118734); +0x48..+0x50 hold 0.0/15.0/5.0 (0x0011874C-0x00118758);
// +0xBC..+0xC8 hold 0.2/0.2/0.2/1.0, +0xCC..+0xD8 hold 1.0 x4,
// +0xE8..+0xF0 hold 0.01/0.001/0.0001, +0xF4..+0xFC hold 1.0/1.0/pi/2, and
// +0xDC..+0xE4 hold 0.0/0.0/-1.0.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001186b4, 388)
void* AsdScene_func_001186b4() {
    AsdSceneObject* light = static_cast<AsdSceneObject*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, 0x0C, 1));        // 0x001186E0
    light->index = -1;                                       // 0x001186F4
    light->object = nullptr;
    light->data = nullptr;

    const AsdSceneCreateDesc desc = MakeSceneCreateDesc();
    void* context = AsdRes_GetContext();                     // 0x001186FC
    void* object = AsdScene_CreateLightObject(&desc, context); // 0x0011871C
    light->object = object;                                  // 0x00118720

    AsdSceneLightData* data = static_cast<AsdSceneLightData*>(
        *reinterpret_cast<void**>(reinterpret_cast<u8*>(object) + 0x08));
    light->data = data;                                      // 0x00118730

    data->kind = 2;                                          // 0x00118734
    data->field_48 = 0.0f;                                   // 0x00118758
    data->field_4c = 15.0f;
    data->field_50 = 5.0f;                                   // 0x0011874C
    data->color_r = 0.2f;                                    // 0x00118768
    data->color_g = 0.2f;
    data->color_b = 0.2f;
    data->color_a = 1.0f;
    data->field_cc = 1.0f;                                   // 0x00118784
    data->field_d0 = 1.0f;
    data->field_d4 = 1.0f;
    data->field_d8 = 1.0f;
    data->field_dc = 0.0f;                                   // 0x001187C4
    data->field_e0 = 0.0f;
    data->field_e4 = -1.0f;
    data->field_e8 = 0.01f;                                  // 0x0011879C
    data->field_ec = 0.001f;
    data->field_f0 = 0.0001f;
    data->field_f4 = 1.0f;                                   // 0x001187A8
    data->field_f8 = 1.0f;                                   // 0x001187B4
    data->field_fc = 1.5707964f;                             // 0x001187B8

    return light;                                            // 0x001187D4
}

// ---------------------------------------------------------------------------
// 0x00118C7C -- create one environment-light record.
//
// Allocation: 0x0C bytes (0x00118CAC).  Direction (-0.40824828, -0.81649655,
// -0.40824828) at +0x10C..+0x114 (0x00118D10); key at +0xFC/+0x100/+0x104/
// +0x108 for the four colour blocks (0x00118D48, 0x00118D7C, 0x00118DAC,
// 0x00118DDC).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00118c7c, 448)
void* AsdScene_func_00118c7c() {
    AsdSceneObject* env = static_cast<AsdSceneObject*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, 0x0C, 1));        // 0x00118CAC
    env->index = -1;                                         // 0x00118CC0
    env->object = nullptr;
    env->data = nullptr;

    const AsdSceneCreateDesc desc = MakeSceneCreateDesc();
    void* context = AsdRes_GetContext();                     // 0x00118CC8
    void* object = AsdScene_CreateEnvObject(&desc, context); // 0x00118CE8
    env->object = object;                                    // 0x00118CEC

    AsdSceneEnvData* data = static_cast<AsdSceneEnvData*>(
        *reinterpret_cast<void**>(reinterpret_cast<u8*>(object) + 0x08));
    env->data = data;                                        // 0x00118CFC

    data->kind = 0;                                          // 0x00118D00
    data->field_10c = -0.40824828f;                          // 0x00118D10
    data->field_110 = -0.81649655f;                          // 0x00118D14
    data->field_114 = -0.40824828f;

    data->color_r = 0.2f;                                    // 0x00118D24
    data->color_g = 0.2f;
    data->color_b = 0.2f;
    data->color_a = 1.0f;
    data->field_fc = AsdRes_BuildKey(&data->color_r);        // 0x00118D3C

    data->field_cc = 1.0f;                                   // 0x00118D54
    data->field_d0 = 1.0f;
    data->field_d4 = 1.0f;
    data->field_d8 = 1.0f;
    data->field_100 = AsdRes_BuildKey(&data->field_cc);      // 0x00118D6C

    data->field_dc = 0.8f;                                   // 0x00118D88
    data->field_e0 = 0.8f;
    data->field_e4 = 0.8f;
    data->field_e8 = 1.0f;
    data->field_104 = AsdRes_BuildKey(&data->field_dc);      // 0x00118DA0

    data->field_ec = 0.8f;                                   // 0x00118DB8
    data->field_f0 = 0.8f;
    data->field_f4 = 0.8f;
    data->field_f8 = 1.0f;
    data->field_108 = AsdRes_BuildKey(&data->field_ec);      // 0x00118DD0

    return env;                                              // 0x00118DE4
}

// ---------------------------------------------------------------------------
// 0x002CB788 -- create one scene node record (the same node image built by
// 0x0010E5F0, without registering it in a slot).
//
// Allocation: 0x0C bytes (0x002CB7B4).  Colour 0.2/0.2/0.2/1.0 at
// +0xB8..+0xC4 and `AsdRes_BuildKey` at +0xC8 (0x002CB808-0x002CB830).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002cb788, 204)
void* AsdScene_func_002cb788() {
    AsdSceneObject* node = static_cast<AsdSceneObject*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, 0x0C, 1));        // 0x002CB7B4
    node->index = -1;                                        // 0x002CB7C8
    node->object = nullptr;
    node->data = nullptr;

    const AsdSceneCreateDesc desc = MakeSceneCreateDesc();
    void* context = AsdRes_GetContext();                     // 0x002CB7D0
    void* object = AsdScene_CreateNodeObject(&desc, context); // 0x002CB7F0
    node->object = object;                                   // 0x002CB7F4

    AsdSceneNodeData* data = static_cast<AsdSceneNodeData*>(
        *reinterpret_cast<void**>(reinterpret_cast<u8*>(object) + 0x08));
    node->data = data;                                       // 0x002CB804

    data->color_r = 0.2f;                                    // 0x002CB80C
    data->color_g = 0.2f;
    data->color_b = 0.2f;
    data->color_a = 1.0f;
    data->key = AsdRes_BuildKey(&data->color_r);             // 0x002CB824

    return node;                                             // 0x002CB838
}

// ===========================================================================
// AsdProcess.cpp
// ===========================================================================

// ---------------------------------------------------------------------------
// 0x00102E80 -- initialise the process pool.
//
// `AsdMem_FillBytes(0x004E3D0C, 0x200, 1)` (0x00102E94) resets the id table;
// the bucket array is `count * 8` bytes (0x00102EB4) and the first id is 1
// (0x00102ECC).  The bucket pointer is returned in r0.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00102e80, 152)
void* AsdProcess_func_00102e80(u32 count) {
    AsdMem_FillBytes(g_AsdProcessPool.id_table, 0x200, 1);   // 0x00102E94
    g_AsdProcessPool.bucket_count = static_cast<s32>(count); // 0x00102EA4

    void* buckets = AsdMem_Alloc(0x100, 0x100, 0, count * 8u, 1); // 0x00102EC4
    g_AsdProcessPool.buckets = static_cast<AsdProcessNode**>(buckets); // 0x00102EC8
    g_AsdProcessPool.next_id = 1;                            // 0x00102ECC
    return buckets;
}

// ---------------------------------------------------------------------------
// 0x00118488 -- create and link one process node.
//
// Arguments follow the AAPCS layout observed at 0x001184A0-0x001184AC:
//   r0 = name, r1 = bucket, [sp+0]=u16 field_34, [sp+4]=u16 field_36,
//   [sp+8..0x14] = four floats, [sp+0x1c] = parent handle (r6 at 0x001184A4).
// Allocation: 0xA4 bytes (0x001184BC).
//
// Unique id: 0x00118530-0x00118580 increments `next_id`, wraps to 1 at
// 0x000FFFFF and restarts the bucket scan whenever an existing node matches.
// List insertion happens only for state values 1..5 (jump table at
// 0x001185F4: case 0 and the default both target 0x0011863C, cases 1-5 target
// 0x0011860C).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00118488, 556)
u32 AsdProcess_func_00118488(const char* name, u32 bucket, u16 field_34,
                             u16 field_36, f32 field_38, f32 field_3c,
                             f32 field_40, f32 field_48, u32 parent) {
    AsdProcessNode* node = static_cast<AsdProcessNode*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0xA4, 1));             // 0x001184CC
    if (node == nullptr) {
        return 0;                                            // 0x001184D4
    }

    // 0x001184DC-0x00118510: copy at most 0x18 signed bytes and sum them.  The
    // store happens before the length test, so a 25th character lands in the
    // low byte of name_hash exactly as in the listing.
    u8* raw = reinterpret_cast<u8*>(node);
    u32 index = 0;
    node->name_hash = 0;                                     // 0x001184E0
    for (;;) {
        const s8 character = static_cast<s8>(name[index]);
        raw[index] = static_cast<u8>(character);             // 0x00118504
        if (character == 0) {
            break;
        }
        if (index >= 0x18) {
            break;
        }
        node->name_hash += character;                        // 0x001184F8
        ++index;
    }

    node->bucket = bucket;                                   // 0x00118518
    raw[0x17] = 0;                                           // 0x0011851C
    node->state = 1;                                         // 0x00118520

    // Pick the next unused id (0x00118530-0x00118580).
    for (;;) {
        u32 candidate = g_AsdProcessPool.next_id + 1;
        if (candidate >= 0xFFFFFu) {
            candidate = 1;                                   // 0x00118544
        }
        g_AsdProcessPool.next_id = candidate;

        bool used = false;
        for (s32 slot = 0; slot < g_AsdProcessPool.bucket_count && !used; ++slot) {
            for (AsdProcessNode* item = g_AsdProcessPool.buckets[slot];
                 item != nullptr; item = item->next) {
                if (item->id == candidate) {                 // 0x00118564
                    used = true;
                    break;
                }
            }
        }
        if (!used) {
            break;
        }
    }

    const u32 id = g_AsdProcessPool.next_id;                 // 0x00118548
    node->id = id;                                           // 0x00118590
    // 0x00118584-0x0011859C: `lsl #12; lsr #12` masks the id, then
    // `orr ...,bucket<<20` packs the bucket into the handle.
    node->handle = (id & 0x000FFFFFu) | (bucket << 20);

    node->field_34 = field_34;                               // 0x001185A0
    node->field_36 = field_36;                               // 0x001185A4
    node->field_38 = field_38;                               // 0x001185B0
    node->field_3c = field_3c;
    node->field_40 = field_40;
    node->field_48 = field_48;                               // 0x001185A8

    node->command_list = AsdGxCommandList_Create();          // 0x001185B8
    node->field_6c = 1;                                      // 0x001185BC
    node->field_74 = 1;                                      // 0x001185C0
    node->field_7c = 1;                                      // 0x001185C4
    node->field_84 = 1;                                      // 0x001185C8
    node->flags |= 0x00190000u;                              // 0x001185D0

    // `add r0,r2,r0,lsl #3` -- bucket slot, two pointers per bucket.
    u8* list = reinterpret_cast<u8*>(g_AsdProcessPool.buckets) + bucket * 8u;

    switch (node->state) {
        case 1:
        case 2:
        case 3:
        case 4:
        case 5: {
            AsdProcessNode* head = *reinterpret_cast<AsdProcessNode**>(list);
            if (head == nullptr) {
                *reinterpret_cast<AsdProcessNode**>(list) = node;        // 0x00118664
                *reinterpret_cast<AsdProcessNode**>(list + 4) = node;    // 0x00118668
                node->prev = nullptr;                                    // 0x0011866C
            } else {
                AsdProcessNode* tail = *reinterpret_cast<AsdProcessNode**>(list + 4);
                tail->next = node;                                       // 0x0011861C
                node->prev = tail;                                       // 0x00118624
                *reinterpret_cast<AsdProcessNode**>(list + 4) = node;    // 0x00118628
            }
            node->next = nullptr;                                        // 0x0011862C
            ++g_AsdProcessPool.process_count;                            // 0x00118638
            break;
        }
        default:
            break;
    }

    if (parent != 0) {
        AsdProcess_Attach(parent, node->handle);             // 0x0011864C
    }
    return node->handle;                                     // 0x00118650
}

// ===========================================================================
// AsdSequence.cpp
// ===========================================================================

// ---------------------------------------------------------------------------
// 0x002C59B8 -- stage a sequence buffer and re-enter the current callback.
//
// The table entry is `table + index*12` (0x002C59C8-0x002C59D0); the selector
// word at +0 must be non-zero.  When `data` is null the staging pair is
// cleared (0x002C5A28-0x002C5A30), otherwise `size` bytes are allocated and
// copied (0x002C5A0C-0x002C5A20).  The callback of the *current* entry is
// tail-called through `bx r0` (0x002C5A50-0x002C5A5C).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002c59b8, 180)
void AsdSequence_func_002c59b8(u32 index, const void* data, u32 size) {
    AsdSequenceEntry* entry = &g_AsdSequence.table[index * 3u];
    if (entry->selector == 0) {                              // 0x002C59D4
        return;
    }

    g_AsdSequence.requested = index;                         // 0x002C59E0

    if (data != nullptr) {
        void* buffer = AsdMem_Alloc(0x100, 0x100, 0, size, 1); // 0x002C5A0C
        g_AsdSequence.buffer = buffer;                        // 0x002C5A18
        g_AsdSequence.buffer_size = size;
        AsdMem_Copy(buffer, data, size);                      // 0x002C5A20
    } else {
        g_AsdSequence.buffer = nullptr;                       // 0x002C5A2C
        g_AsdSequence.buffer_size = 0;                        // 0x002C5A30
    }

    const s32 current = g_AsdSequence.current;                // 0x002C5A34
    if (current < 0) {                                        // 0x002C5A3C
        return;
    }

    AsdSequenceEntry* live = reinterpret_cast<AsdSequenceEntry*>(
        reinterpret_cast<u8*>(g_AsdSequence.table) + static_cast<u32>(current) * 12u);
    using CallbackFn = void (*)();
    reinterpret_cast<CallbackFn>(live->callback)();           // 0x002C5A5C
}

// ===========================================================================
// Task.c
// ===========================================================================

// ---------------------------------------------------------------------------
// 0x002861F8 -- allocate and priority-insert one task.
//
// Stack arguments (0x00286214-0x00286228): [sp+0]=float arg3, [sp+4]=payload
// size (r6), [sp+8]=type (r5), [sp+0xc]=priority (r7), [sp+0x10]=payload-init
// flag (r8).  Allocation is `payload_size + 0x34` (0x00286228/0x00286250).
// The list heads live at `0x004C5830 + type*0x10` (0x00286230).
// Insert order is ascending priority and stable for equal priorities:
// before head when head->priority > new (0x002862CC), after tail when
// tail->priority <= new (0x0028630C), otherwise before the first node with a
// larger priority (0x00286350).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002861f8, 508)
void* Task_func_002861f8(void* arg0, void* arg1, void* arg2, f32 arg3,
                         f32 arg4, u32 payload_size, u32 type, u16 priority,
                         u32 init_payload) {
    u32 block_size = payload_size + 0x34u;                    // 0x00286224
    u8* block = static_cast<u8*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, block_size, 1));   // 0x00286254
    if (block == nullptr) {
        return nullptr;                                       // 0x0028625C
    }

    AsdTaskNode* node = reinterpret_cast<AsdTaskNode*>(block);
    node->type = static_cast<u8>(type);                       // 0x00286260
    node->priority = priority;                                // 0x00286268
    node->field_02 = 0;                                       // 0x00286274
    node->field_04 = 0;                                       // 0x00286270
    node->arg0 = arg0;                                        // 0x00286278
    node->arg1 = arg1;
    node->arg2 = arg2;
    node->arg3 = arg3;                                        // 0x00286280
    node->arg4 = arg4;                                        // 0x00286284
    node->field_24 = 0;                                       // 0x00286298
    node->field_28 = 0;
    node->field_2c = 0;
    node->field_30 = 0;
    node->prev = nullptr;                                     // 0x00286290
    node->next = nullptr;                                     // 0x00286294

    AsdTaskList* list = &g_AsdTaskLists[type];                // 0x00286230
    // 0x00286230 performs no range check on `type`; the array at 0x004C5830
    // holds five heads (see the definition in this file).
    AsdTaskNode* head = list->head;
    AsdTaskNode* tail = list->tail;
    const u32 count = list->count;

    if (count == 0) {                                         // 0x002862AC
        list->head = node;                                    // 0x002862B4
        list->tail = node;
    } else if (head->priority > node->priority) {             // 0x002862C4
        AsdTaskNode* previous = head->prev;                   // 0x002862CC
        node->prev = previous;                                // 0x002862D8
        node->next = head;
        if (previous != nullptr) {
            previous->next = node;                            // 0x002862E0
        }
        head->prev = node;                                    // 0x002862EC
        list->head = node;                                    // 0x002862F0
    } else if (tail != nullptr && tail->priority <= node->priority) {
        // 0x0028630C-0x00286330: append after the tail, repair head->prev.
        node->prev = tail;
        node->next = tail->next;
        tail->next = node;
        if (node->next != nullptr) {
            node->next->prev = node;
        }
        list->tail = node;
    } else {
        // 0x00286338-0x00286380: walk from the head to the first larger
        // priority and link the task in front of it.
        AsdTaskNode* current = list->head;
        while (current != nullptr && current->priority <= node->priority) {
            current = current->next;
        }
        if (current != nullptr) {
            AsdTaskNode* previous = current->prev;            // 0x00286350
            node->prev = previous;
            node->next = current;
            if (previous != nullptr) {
                previous->next = node;                        // 0x00286364
            }
            current->prev = node;                             // 0x00286370
        }
    }

    ++list->count;                                            // 0x00286390

    u8* payload = block + 0x34;                               // 0x00286394
    if (init_payload != 0) {
        AsdWork_Zero(payload, payload_size);                  // 0x002863A4
    }
    return payload;                                           // 0x002863A8
}

} // namespace smt4::engine
