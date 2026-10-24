#include "engine/asd_effect2.h"
#include "engine/asd_effect.h"
#include "engine/asd_render_ui.h"
#include "engine/asd_symbols.h"

#include <cstring>

using namespace smt4::engine;

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

// 0x00476638 / 0x004EFD9C: the geometry engine uses the same latch and
// identity matrix as the battle FilterXPoly path.  They are defined in
// src/battle/battle_extras.cpp; declaring the canonical names here avoids a
// second definition for either address.
namespace smt4::battle {
    extern u32 g_FilterXPolyFlags;
    extern f32 g_FilterXPolyMatrix[16];
}

extern "C" {
    // AsdMemory / AsdFile helpers.
    void* AsdWork_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 a5); // 0x002c34a4
    void  AsdMem_Zero(void* ptr, u32 size);                                // 0x002c4b30
    void  AsdMem_Free(void* ptr);                                          // 0x002c4360
    void  AsdMem_Copy(void* dst, const void* src, u32 size);               // 0x002c5ff4

    // 0x0024C60C: resolve +0x10 (relative) when +0x18 is clear.
    void* AsdRes_ResolveOffset(void* record);                              // 0x0024c60c
    // 0x0024C5EC: the same resolver over the +0x20/+0x28 pair.
    void* AsdRes_ResolveRelative(void* record);                            // 0x0024c5ec

    // Effect behavior factory and reference helpers.  0x00269404 is declared
    // canonically in engine/asd_render_ui.h (the ledger spelling lives there).
    void  engine_func_00269594(void* behavior);                            // 0x00269594
    void  engine_func_00269758(void* object);                              // 0x00269758
    void  ui_func_002c0a6c(void* object);                                  // 0x002c0a6c

    // Geometry / texture slots (0x00249508 switches on its third argument).
    void  engine_func_00249508(EffParticle* particle, u32 id, u32 kind);   // 0x00249508

    // 0x0024C5DC: global texture table lookup (`ldr r0,[table,index*4]`).
    void* AsdTexture_GetGlobal(u32 index);                                 // 0x0024c5dc

    // 0x0024BA44: deterministic float from the global at 0x004D9748.
    f32   engine_func_0024ba44(u32 mode);                                  // 0x0024ba44

    // Per-type particle / part free routines used by the array rebuild paths.
    void  engine_func_002c24e4(void* particle);                           // 0x002c24e4
    void  engine_func_002c2430(void* part);                               // 0x002c2430

    // Polygon helpers.
    void* effPolygonRing_func_002c7a54(u32 mode, void* data);              // 0x002c7a54
    EffGeometry* effGeometry_func_002474a0(u32 count, u32 columns,
                                           u32 stride, const void* format,
                                           u32 flags);                     // 0x002474a0
    EffGeometry* effGeometry_func_002451c8(u32 count, const void* format,
                                           u32 stride, u32 flags);         // 0x002451c8
    void  effGeometry_func_0024745c(EffGeometry* geometry,
                                    const void* texture);                  // 0x0024745c

    // Track render-data factories and uploader.
    void* engine_func_00246b58(u32 rows, u32 columns, const void* format,
                               u32 stride, u32 flags);                     // 0x00246b58
    void* engine_func_002d13d4(u32 rows, u32 columns, u32 vertices,
                               u32 stride, const void* format, u32 flags); // 0x002d13d4
    void  engine_func_003053c4(void* track, const void* config);           // 0x003053c4
    void  engine_func_0024af9c(void* block);                               // 0x0024af9c

    // effObjectParticle helpers.
    void  effObjectParticle_func_003137c4(void* object, u32 id,
                                          void* data);                     // 0x003137c4
    void* engine_func_0025be50(void* data, u32 size, u32 mode);            // 0x0025be50
    void  engine_func_0031cf9c(void* object);                              // 0x0031cf9c

    // effPolgonFlash name formatting.
    void  UiText_Format(char* dst, const char* format, ...);               // 0x002be7fc

    // Geometry render-data bring-up.
    void* engine_func_00269644(void* memory);                              // 0x00269644
    void  engine_func_00269614(void* render, u32 mode, u32 size,
                               u32 count);                                 // 0x00269614
    void* engine_func_002d5808(u32 count, u32 mode);                       // 0x002d5808

    // Geometry engine matrix submission.  Both are shared with battle_extras.
    s32   Gpu_CheckDrawFlag(const void* flag);                             // 0x002c00d4
    void  Filter_Submit(void* block, const void* matrix);                  // 0x002c0000

    // Per-effect wrapper clone/free entries.
    void* effP2A_func_0025722c(void* source);                              // 0x0025722c
    void* engine_func_0025721c(void* source);                              // 0x0025721c
    void  engine_func_0025733c(void* wrapper);                             // 0x0025733c
    void  ui_func_00257390(void* wrapper);                                 // 0x00257390

    // Texture factories shared with asd_effect.cpp.
    void* EffParts_CreateTexture(const void* source);                      // 0x0028ca7c
    void* AsdEffectTexture_func_0028cabc(const void* source);              // 0x0028cabc
}

// Vertex-format tables consumed by the shared effGeometry / effGeomEngine
// builders.  Their contents belong to those routines; only the addresses are
// established here.
extern const u8 g_EffPolygonRingFormat_47375c[];      // 0x0047375C
extern const u8 g_EffPolygonRingFormat_473708[];      // 0x00473708
extern const u8 g_EffPolygonThunderFormat_47372c[];   // 0x0047372C
extern const u8 g_EffPolygonFlashFormat_4737c2[];     // 0x004737C2
extern const u8 g_EffPolygonTrackFormat_4736f0[];     // 0x004736F0
extern const u8 g_EffPolygonTrackFormat_4737ce[];     // 0x004737CE

namespace {

using namespace smt4::engine;

constexpr u32 kEffectPool = 0x10000;
constexpr u32 kEffectAlign = 0x100;

// 0x004737F8+0x10..+0x1C: the four words copied by the geometry 0x80000 path
// (0x0026927C..0x00269294).  The binary holds 3F800000,0,0,3F800000 at
// 0x00473808..0x00473814, i.e. (1.0f, 0.0f, 0.0f, 1.0f).
const EffGeometryOverride g_EffGeometryOverride = {
    {},
    1.0f,
    0.0f,
    0.0f,
    1.0f,
};

// 0x00472560: four bytes read by the track colour loop (0x0024fbbc..0x0024fc98).
const u8 g_EffPolygonTrackColor[4] = {0x00, 0x00, 0x00, 0x00};

void* AllocEffect(u32 size)
{
    return AsdWork_Alloc(kEffectPool, kEffectAlign, 0, size, 0x10, 1);
}

// The listing writes each colour as four individual bytes in little-endian
// order (`rev` followed by `strb`, e.g. 0x00247fbc..0x00247ff4).
void StoreColor(u8* dst, u32 argb)
{
    dst[0] = static_cast<u8>(argb);
    dst[1] = static_cast<u8>(argb >> 8);
    dst[2] = static_cast<u8>(argb >> 16);
    dst[3] = static_cast<u8>(argb >> 24);
}

// Alpha byte scaled by the point ratio; the colour bytes are untouched.
u32 BlendColor(u32 color, f32 ratio)
{
    const u32 alpha = static_cast<u32>(static_cast<f32>(color >> 24) * ratio);
    return (color & 0x00FFFFFFu) | (alpha << 24);
}

// One 20-byte thunder vertex.  The listing stores c3,c2,c1,c2,c3 at
// +0x00/+0x04/+0x08/+0x0C/+0x10 (0x00327fc0..0x00328064).
void WriteThunderVertex(u8* vertex, u32 color_00, u32 color_04, u32 color_08,
                        f32 ratio)
{
    StoreColor(vertex + 0x00, BlendColor(color_08, ratio));
    StoreColor(vertex + 0x04, BlendColor(color_04, ratio));
    StoreColor(vertex + 0x08, BlendColor(color_00, ratio));
    StoreColor(vertex + 0x0C, BlendColor(color_04, ratio));
    StoreColor(vertex + 0x10, BlendColor(color_08, ratio));
}

// A geometry's primitive count is built as 5*(points+1); the builders recover
// the number of points with the signed 16-bit multiply by 0x6667 and the
// `asr #17` / sign-correction sequence at 0x00327ee8..0x00327ef4.
s32 GeometryPointCount(u16 count)
{
    const s32 product = static_cast<s32>(static_cast<s16>(count)) * 0x6667;
    return (product >> 17) - (product >> 31);
}

// Point ratio used by 0x0031596C and 0x0032170C.  `i < x` ramps up, the
// [x,y] plateau is 1.0, and the tail divides by `points - y` (0x00315B00..
// 0x00315B24 and 0x0032189C..0x003218B0).
f32 ThunderRatio(s32 i, s32 x, s32 y, s32 points)
{
    if (i < x)
        return static_cast<f32>(static_cast<u32>(i)) / static_cast<f32>(x);

    if (i <= y)
        return 1.0f;

    return static_cast<f32>(static_cast<u32>(points - i)) /
           static_cast<f32>(static_cast<u32>(points - y));
}

// 0x00327D90's ratio differs in two ways: the tail numerator is
// `points - i - 1` (0x00327F48..0x00327F54), and the whole computation is
// gated to i == 0 or odd i (0x00327F08..0x00327F14).  Even i > 0 reuses the
// previous ratio held in s16.
f32 ThunderRatio327(s32 i, s32 x, s32 y, s32 points)
{
    if (i < x)
        return static_cast<f32>(static_cast<u32>(i)) / static_cast<f32>(x);

    if (i <= y)
        return 1.0f;

    return static_cast<f32>(static_cast<u32>(points - i - 1)) /
           static_cast<f32>(static_cast<u32>(points - y));
}

} // namespace

namespace smt4::engine {

// ===========================================================================
// effParticle.cpp (c:\SMT4\XRD686\AsdSDK\Source\Gfx\Effect\effParticle.cpp)
// ===========================================================================

// 0x002DE41C -- build a live particle object from a part source.
//
// The spawn count is `(resolved[+0x20] ? resolved[+0x20] : resolved[+0xB8])
// * resolved[+0x24]`, clamped to 300 (`cmp r6,#0x12c` / `movhi r6,#0x12c`,
// 0x002DE450..0x002DE454).  The 0x5C-byte object is zeroed before its
// behavior is created, then the +0x1C source mode selects the sub-resource
// builder.  Every builder stores into the geometry slot at +0x50; the texture
// pointer always lands in geometry->engine->+0xB4.
//
// DECOMP_FUNC(0x002de41c, 1204)
void* effParticle_func_002de41c(EffParticleSource* source)
{
    EffParticleResolved* resolved =
        static_cast<EffParticleResolved*>(AsdRes_ResolveOffset(source));

    u32 count = (resolved->count != 0 ? resolved->count
                                      : resolved->alternate_count) *
                resolved->multiplier;
    if (count > 0x12C)
        count = 0x12C;

    EffParticle* particle =
        static_cast<EffParticle*>(AllocEffect(sizeof(EffParticle)));
    AsdWork_Zero(particle, sizeof(EffParticle));

    particle->field_04 = -1;                 // 0x002DE488
    particle->field_08 = 1.0f;               // 0x002DE490..0x002DE498
    particle->count = count;                 // 0x002DE494

    if (particle->behavior != nullptr)       // zeroed above, mirrors 0x002DE4A8
        engine_func_00269594(particle->behavior);

    particle->behavior =
        effBehavior_func_00269404(source->type, particle->count, resolved);
    particle->flags |= 1;                    // 0x002DE4C4..0x002DE4CC

    if (particle->count == 0)                // 0x002DE4D0..0x002DE4D8
        return particle;

    EffParticleResolved* data =
        static_cast<EffParticleResolved*>(AsdRes_ResolveRelative(source));
    if (data == nullptr)                     // 0x002DE4E4..0x002DE4E8
        return particle;

    switch (source->mode) {                  // `ldrh r0,[r7,#0x1c]`, 0x002DE4EC
    case 1: {                                // 0x002DE524
        engine_func_00249508(particle,
                             static_cast<u32*>(particle->behavior)[2], 1);
        void* texture = EffParts_CreateTexture(data);   // 0x002DE540
        const u32* dims = static_cast<const u32*>(texture);
        particle->width = static_cast<f32>(static_cast<s32>(dims[5])) *
                          0.5f * 0.0625f;
        particle->height = static_cast<f32>(static_cast<s32>(dims[6])) *
                           0.5f * 0.0625f;
        static_cast<EffGeomEngine*>(
            static_cast<EffGeometry*>(particle->geometry)->engine)->texture =
            texture;                          // 0x002DE584
        engine_func_00269758(texture);        // 0x002DE588
        ui_func_002c0a6c(texture);            // 0x002DE594
        break;
    }

    case 2: {                                // 0x002DE5A4
        engine_func_00249508(particle,
                             static_cast<u32*>(particle->behavior)[2], 2);
        if (particle->p2a != nullptr)
            ui_func_00257390(particle->p2a);  // 0x002DE5C0
        particle->p2a = effP2A_func_00249324(data); // 0x002DE5CC
        break;
    }

    case 4: {                                // 0x002DE5DC
        engine_func_00249508(particle,
                             static_cast<u32*>(particle->behavior)[2], 4);
        void* texture = AsdTexture_GetGlobal(data->field_00 & 0xFFFF);
        const u32* dims = static_cast<const u32*>(texture);
        particle->width = static_cast<f32>(static_cast<s32>(dims[5])) *
                          0.5f * 0.0625f;
        particle->height = static_cast<f32>(static_cast<s32>(dims[6])) *
                           0.5f * 0.0625f;
        static_cast<EffGeomEngine*>(
            static_cast<EffGeometry*>(particle->geometry)->engine)->texture =
            texture;                          // 0x002DE634
        engine_func_00269758(texture);        // 0x002DE638
        break;
    }

    case 5: {                                // 0x002DE648
        // `ldrne r6,[r0,#8]` when the behavior exists, otherwise the object's
        // own spawn count (`ldreq r6,[r4]`, 0x002DE654..0x002DE65C).
        u32 elementCount = particle->behavior != nullptr
                               ? static_cast<u32*>(particle->behavior)[2]
                               : particle->count;

        if (particle->particle_alloc != nullptr) {
            for (u32 i = 0; i < elementCount; ++i) // 0x002DE674..0x002DE688
                engine_func_002c24e4(particle->particles[i]);
            AsdMem_Free(particle->particle_alloc);     // 0x002DE690
            particle->particles = nullptr;
            particle->particle_alloc = nullptr;
        }

        const u32 bytes = elementCount * 4;        // 0x002DE6A0
        if (bytes == 0)
            break;

        void** array = static_cast<void**>(AllocEffect(bytes));
        particle->particle_alloc = array;          // 0x002DE6D8
        particle->particles = array;               // 0x002DE6D4

        // The first record is wrapped from the resolved data; the rest are
        // clones of that first element (0x002DE6DC..0x002DE714).
        array[0] = effParts_func_0024fe64(
            reinterpret_cast<EffPartsParticle*>(data));
        for (u32 i = 1; i < elementCount; ++i)
            array[i] = effParts_func_0024fda4(
                static_cast<EffPartsParticle*>(array[0]));
        break;
    }

    case 6: {                                // 0x002DE71C
        u32 elementCount = particle->behavior != nullptr
                               ? static_cast<u32*>(particle->behavior)[2]
                               : particle->count;

        if (particle->part_alloc != nullptr) {
            for (u32 i = 0; i < elementCount; ++i) // 0x002DE748..0x002DE75C
                engine_func_002c2430(
                    static_cast<void**>(particle->parts)[i]);
            AsdMem_Free(particle->part_alloc);         // 0x002DE764
            particle->parts = nullptr;
            particle->part_alloc = nullptr;
        }

        const u32 bytes = elementCount * 4;        // 0x002DE774
        if (bytes == 0)
            break;

        void** array = static_cast<void**>(AllocEffect(bytes));
        particle->part_alloc = array;              // 0x002DE7A8
        particle->parts = array;                   // 0x002DE7AC

        array[0] = effParts_func_002a51dc(
            reinterpret_cast<EffPartsSource*>(data)); // 0x002DE7B4
        for (u32 i = 1; i < elementCount; ++i)
            array[i] = effParts_func_002490e0(
                static_cast<EffPartsSource*>(array[0]));
        break;
    }

    case 7: {                                // 0x002DE810
        engine_func_00249508(particle,
                             static_cast<u32*>(particle->behavior)[2], 7);
        if (particle->tlp != nullptr)
            engine_func_0025733c(particle->tlp); // 0x002DE82C
        particle->tlp = effTLP_func_00249588(data); // 0x002DE838
        break;
    }

    case 9: {                                // 0x002DE848
        engine_func_00249508(particle,
                             static_cast<u32*>(particle->behavior)[2], 9);
        void* texture = AsdEffectTexture_func_0028cabc(data); // 0x002DE860
        const u32* dims = static_cast<const u32*>(texture);
        particle->width = static_cast<f32>(static_cast<s32>(dims[5])) *
                          0.5f * 0.0625f;
        particle->height = static_cast<f32>(static_cast<s32>(dims[6])) *
                           0.5f * 0.0625f;
        static_cast<EffGeomEngine*>(
            static_cast<EffGeometry*>(particle->geometry)->engine)->texture =
            texture;                          // 0x002DE8A8
        engine_func_00269758(texture);        // 0x002DE8AC
        ui_func_002c0a6c(texture);            // 0x002DE8B8
        break;
    }

    default:                                 // cases 0, 3 and 8
        break;
    }

    particle->type = source->mode;            // 0x002DE8BC..0x002DE8C0
    return particle;
}

// 0x002E7C30 -- clone the sub-resources of one particle into another.
//
// The source's +0x0C mode selects which sub-resources are rebuilt.  The two
// array cases read their element count from the source behavior's +0x08 word
// (`ldr r0,[r6,#0x4c]` / `ldr r7,[r0,#8]`, 0x002E7CB0..0x002E7CB8) and free the
// destination arrays before cloning each source element.
//
//
[[maybe_unused]] static void effParticle_func_002e7c30_reference(
    EffParticle* dest, const EffParticle* source)
{
    switch (source->type) {                   // `ldrh r0,[r1,#0xc]`, 0x002E7C3C
    case 1:                                   // 0x002E7C78
    case 4:
    case 9:
        dest->width = source->width;          // 0x002E7C78..0x002E7C84
        dest->height = source->height;
        break;

    case 2: {                                 // 0x002E7C8C
        if (dest->p2a != nullptr)
            ui_func_00257390(dest->p2a);
        dest->p2a = effP2A_func_0025722c(source->p2a);
        break;
    }

    case 5: {                                 // 0x002E7CB0
        const u32 elementCount =
            static_cast<u32*>(source->behavior)[2];
        if (elementCount == 0)                // 0x002E7CB8..0x002E7CBC
            return;

        if (dest->particle_alloc != nullptr) {
            for (u32 i = 0; i < elementCount; ++i) // 0x002E7CD8..0x002E7CEC
                engine_func_002c24e4(dest->particles[i]);
            AsdMem_Free(dest->particle_alloc);     // 0x002E7CF4
            dest->particles = nullptr;
            dest->particle_alloc = nullptr;
        }

        const u32 bytes = elementCount * 4;        // 0x002E7D04
        if (bytes == 0)
            break;

        void** array = static_cast<void**>(AllocEffect(bytes));
        dest->particle_alloc = array;              // 0x002E7D38
        dest->particles = array;                   // 0x002E7D3C

        for (u32 i = 0; i < elementCount; ++i)     // 0x002E7D4C..0x002E7D68
            array[i] = effParts_func_0024fda4(
                static_cast<EffPartsParticle*>(
                    static_cast<void**>(source->particles)[0]));
        break;
    }

    case 6: {                                 // 0x002E7D70
        const u32 elementCount =
            static_cast<u32*>(source->behavior)[2];
        if (elementCount == 0)                // 0x002E7D78..0x002E7D7C
            return;

        if (dest->part_alloc != nullptr) {
            for (u32 i = 0; i < elementCount; ++i) // 0x002E7D98..0x002E7DAC
                engine_func_002c2430(
                    static_cast<void**>(dest->parts)[i]);
            AsdMem_Free(dest->part_alloc);             // 0x002E7DB4
            dest->parts = nullptr;
            dest->part_alloc = nullptr;
        }

        const u32 bytes = elementCount * 4;        // 0x002E7DC4
        if (bytes == 0)
            break;

        void** array = static_cast<void**>(AllocEffect(bytes));
        dest->part_alloc = array;                  // 0x002E7DF8
        dest->parts = array;                       // 0x002E7DFC

        for (u32 i = 0; i < elementCount; ++i)     // 0x002E7E0C..0x002E7E28
            array[i] = effParts_func_002490e0(
                static_cast<EffPartsSource*>(
                    static_cast<void**>(source->parts)[0]));
        break;
    }

    case 7: {                                 // 0x002E7E30
        if (dest->tlp != nullptr)
            engine_func_0025733c(dest->tlp);
        dest->tlp = engine_func_0025721c(source->tlp);
        break;
    }

    default:                                  // cases 0, 3 and 8
        break;
    }

    dest->type = source->type;                // 0x002E7E4C..0x002E7E50
}

// ===========================================================================
// effObjectParticle.cpp
// (c:\SMT4\XRD686\AsdSDK\Source\Gfx\Effect\effObjectParticle.cpp)
// ===========================================================================

// 0x00313908 -- build an object-particle effect.
//
// Count: `(data[+0x64] ? data[+0x64] : data[+0xFC]) * data[+0x68]`, clamped
// to 100 (0x0031391C..0x00313940).  The 0xA8-byte object is zeroed, the
// 0x44-byte data prefix is copied to +0x10, and 0x003137C4 builds the behavior
// and record array at +0x9C/+0xA0.  Mode 3 additionally recognises a "CGFX"
// payload at the +0x20 resolver and installs a model through 0x0025BE50.
//
//
[[maybe_unused]] static void* effObjectParticle_func_00313908_reference(
    EffParticleSource* source)
{
    EffObjectParticleData* data =
        static_cast<EffObjectParticleData*>(AsdRes_ResolveOffset(source));

    u32 count = (data->count != 0 ? data->count : data->alternate_count) *
                data->multiplier;
    if (count > 100)                          // 0x0031393C..0x00313940
        count = 100;

    EffObjectParticle* object =
        static_cast<EffObjectParticle*>(AllocEffect(sizeof(EffObjectParticle)));
    AsdWork_Zero(object, sizeof(EffObjectParticle));

    object->field_04 = -1;                    // 0x00313978
    object->field_08 = 1.0f;                  // 0x00313980..0x00313988
    object->count = count;                    // 0x00313984

    // 0x0031398C..0x00313998: copy 0x44 bytes into +0x10.
    AsdMem_CopyLarge(object->copied, data, 0x44);

    // 0x0031399C..0x003139A8: behavior id is the source's +0x0C word.
    effObjectParticle_func_003137c4(object, source->type, data->field_44);

    // `ldr r0,[r4,#0x9c]` / `ldr r0,[r0,#8]` / `cmp r0,#0` (0x003139AC..B8).
    const u32 behaviorCount =
        object->behavior != nullptr
            ? static_cast<u32*>(object->behavior)[2]
            : 0;
    if (behaviorCount == 0)
        return object;

    const u8* name =
        static_cast<const u8*>(AsdRes_ResolveRelative(source));
    if (name == nullptr)                      // 0x003139C4..C8
        return object;

    if (source->mode == 3) {                  // 0x003139CC..D4
        if (name[0] == 'C' && name[1] == 'G' &&
            name[2] == 'F' && name[3] == 'X') { // 0x003139E4..0x00313A0C
            void* copy = AllocEffect(source->length); // 0x00313A10..0x00313A34
            object->copy = copy;              // 0x00313A3C

            // 0x00313A40..0x00313A48: `AsdMem_CopyFrom(name, copy, length)`.
            AsdMem_CopyFrom(name, copy, source->length);

            object->model =
                engine_func_0025be50(copy, source->length, 7); // 0x00313A58

            // 0x00313A60..0x00313A70: render->+0x28 = 1 through the model's
            // +0x08 / +0x2C / +0x220 / +0x08 pointer chain.
            u8* model = static_cast<u8*>(object->model);
            u8* node = *reinterpret_cast<u8**>(model + 0x08);
            node = *reinterpret_cast<u8**>(node + 0x2C);
            node = *reinterpret_cast<u8**>(node + 0x220);
            node = *reinterpret_cast<u8**>(node + 0x08);
            *reinterpret_cast<u32*>(node + 0x28) = 1;
        }

        engine_func_0031cf9c(object);          // 0x00313A74
    }

    object->type = source->mode;               // 0x00313A7C..0x00313A80
    return object;
}

// ===========================================================================
// effPolygonRing.cpp
// (c:\SMT4\XRD686\AsdSDK\Source\Gfx\Effect\effPolygonRing.cpp)
// ===========================================================================

// 0x0030EFB0 -- build a colour strip and a 0x5C-byte ring image.
//
// The returned header sits after a count-word float array:
// `header = allocation + count*4`, `header[0] = allocation`,
// `header[0xC] = allocation` (0x0030F000..0x0030F018).  The ring helper
// 0x002C7A54 receives the copied image at source+0x5C.
//
//
[[maybe_unused]] static void* effPolygonRing_func_0030efb0_reference(
    EffPolygonRing* object)
{
    u32 count = object->count;                 // 0x0030EFC4
    if (count < 3)
        count = 3;
    object->count = count;                     // 0x0030EFD4

    u8* allocation = static_cast<u8*>(AllocEffect(0x10 + count * 4));
    u8* header = allocation + count * 4;       // 0x0030F000
    *reinterpret_cast<u32*>(header + 0x00) = static_cast<u32>(
        reinterpret_cast<std::uintptr_t>(allocation));
    *reinterpret_cast<u32*>(header + 0x0C) = static_cast<u32>(
        reinterpret_cast<std::uintptr_t>(allocation));

    // 0x0030F014..0x0030F024: the source's first 0x5C bytes are copied onto
    // itself at +0x5C.  AsdMem_CopyLarge is the aligned block copy.
    AsdMem_CopyLarge(object->copy, object, 0x5C);

    // 0x0030F028..0x0030F040: ring mode 1 over the copied image.
    *reinterpret_cast<void**>(header + 0x04) =
        effPolygonRing_func_002c7a54(1, object->copy);

    // 0x0030F038..0x0030F058: 4-column, 2-row ring geometry.
    EffGeometry* geometry = effGeometry_func_002474a0(
        count & 0xFFFF, 2, 4, g_EffPolygonRingFormat_47375c, 0x48);
    *reinterpret_cast<EffGeometry**>(header + 0x08) = geometry;

    u8* vertex = geometry->render->vertices_38; // 0x0030F068..0x0030F06C
    geometry->field_54 |= 0x20;                 // 0x0030F070..0x0030F078

    // 0x0030F088..0x0030F0A0: per-byte average of +0x44 and +0x48.
    const u32 color = object->color_00;         // `ldr r5,[r8,#0x44]`
    const u32 other = object->color_04;         // `ldr r0,[r8,#0x48]`
    const u32 average = (color & other) +
        (((color ^ other) & 0xFEFEFEFFu) >> 1);

    f32* values = reinterpret_cast<f32*>(allocation);

    for (u32 i = 0; i < count; ++i) {           // 0x0030F0A4..0x0030F190
        StoreColor(vertex + 0x00, color);       // 0x0030F0A4..0x0030F0DC
        StoreColor(vertex + 0x04, color);       // 0x0030F0E0..0x0030F104
        StoreColor(vertex + 0x08, average);     // 0x0030F108..0x0030F130
        StoreColor(vertex + 0x0C, color);       // 0x0030F134..0x0030F160

        // 0x0030F164..0x0030F18C:
        // value = ((1 - +0xCC) + random * +0xCC) * +0xC8
        const f32 random = engine_func_0024ba44(0);
        const f32 blend = (1.0f - object->field_cc) +
                          random * object->field_cc;
        values[i] = blend * object->field_c8;

        vertex += 0x10;                         // 0x0030F17C
    }

    return header;                              // 0x0030F194
}

// 0x0031551C -- build the 4-column ring geometry and its 4-colour vertices.
//
// The geometry primitive count is a signed halfword halved twice
// (`ldrsh r1,[r0,#2]` then `/4`, 0x0031558C..0x0031559C), and each 0x10-byte
// vertex stores color_00,color_04,color_04,color_08.
//
//
[[maybe_unused]] static void* effPolygonRing_func_0031551c_reference(
    EffPolygonRing* object)
{
    u8* header = static_cast<u8*>(AllocEffect(4)); // 0x00315540..0x00315554

    u32 count = object->count;                 // 0x00315558
    if (count < 3)
        count = 3;
    object->count = count;                     // 0x0031556C

    EffGeometry* geometry = effGeometry_func_002451c8(
        count & 0xFFFF, g_EffPolygonRingFormat_473708, 4, 0x48);
    *reinterpret_cast<EffGeometry**>(header) = geometry; // 0x00315588

    const s32 vertexCount =
        static_cast<s32>(static_cast<s16>(geometry->count)) / 4;

    u8* vertex = geometry->render->vertices_38; // 0x003155A0..0x003155AC
    geometry->field_54 |= 0x20;                 // 0x00315598..0x003155B0

    const u32 color0 = object->color_00;        // 0x003155B4
    const u32 color1 = object->color_04;        // 0x003155BC
    const u32 color2 = object->color_08;        // 0x003155BC

    for (s32 i = 0; i < vertexCount; ++i) {     // 0x003155C4..0x00315690
        StoreColor(vertex + 0x00, color0);      // 0x003155C4..0x003155F4
        StoreColor(vertex + 0x04, color1);      // 0x003155F8..0x00315620
        StoreColor(vertex + 0x08, color1);      // 0x00315624..0x00315660
        StoreColor(vertex + 0x0C, color2);      // 0x00315664..0x0031568C
        vertex += 0x10;
    }

    return header;                              // 0x00315694
}

// 0x00315700 -- identical 4-column ring builder; the only difference from
// 0x0031551C is the source line literal (0x43 instead of 0x1F7) passed to the
// allocation helper.  The generated geometry is the same.
//
//
[[maybe_unused]] static void* effPolygonRing_func_00315700_reference(
    EffPolygonRing* object)
{
    u8* header = static_cast<u8*>(AllocEffect(4)); // 0x00315724..0x00315738

    u32 count = object->count;                 // 0x0031573C
    if (count < 3)
        count = 3;
    object->count = count;                     // 0x00315750

    EffGeometry* geometry = effGeometry_func_002451c8(
        count & 0xFFFF, g_EffPolygonRingFormat_473708, 4, 0x48);
    *reinterpret_cast<EffGeometry**>(header) = geometry; // 0x0031576C

    const s32 vertexCount =
        static_cast<s32>(static_cast<s16>(geometry->count)) / 4;

    u8* vertex = geometry->render->vertices_38; // 0x00315784..0x00315790
    geometry->field_54 |= 0x20;                 // 0x0031577C..0x00315794

    const u32 color0 = object->color_00;        // 0x00315798
    const u32 color1 = object->color_04;        // 0x003157A0
    const u32 color2 = object->color_08;        // 0x003157A0

    for (s32 i = 0; i < vertexCount; ++i) {     // 0x003157A8..0x00315874
        StoreColor(vertex + 0x00, color0);
        StoreColor(vertex + 0x04, color1);
        StoreColor(vertex + 0x08, color1);
        StoreColor(vertex + 0x0C, color2);
        vertex += 0x10;
    }

    return header;                              // 0x00315878
}

// ===========================================================================
// effPolygonThunder.cpp
// (c:\SMT4\XRD686\AsdSDK\Source\Gfx\Effect\effPolygonThunder.cpp)
// ===========================================================================

// 0x0031596C -- segmented thunder ribbon with a 0x30-byte record per segment.
//
// Allocation: 0x10 + segments*0x30, zeroed; `[allocation] = allocation+0x10`
// and `[allocation+0xC] = allocation` (0x003159C8..0x003159D8).  The record
// array therefore starts at +0x10.  Each segment builds its geometry with
// 0x002451C8(count, ..., 5, 0x48) and writes one 20-byte vertex per point.
//
// DECOMP_FUNC(0x0031596c, 864)
void* effPolygonThunder_func_0031596c(EffPolygonThunder* object)
{
    u32 count = object->points;                // 0x003159E4
    if (count < 3)
        count = 3;
    object->points = count;                    // 0x003159F0

    const u32 allocationSize = 0x10 + object->segments * 0x30;
    u8* allocation = static_cast<u8*>(AllocEffect(allocationSize));
    AsdWork_Zero(allocation, allocationSize);  // 0x003159C0..0x003159C4

    *reinterpret_cast<u8**>(allocation + 0x00) = allocation + 0x10;
    *reinterpret_cast<u8**>(allocation + 0x0C) = allocation;

    const f32 scale = static_cast<f32>(count + 1); // 0x003159F4..0x00315A0C
    const s32 x = static_cast<s32>(object->scale_x * scale);
    const s32 y = static_cast<s32>(object->scale_y * scale);

    const u32 color0 = object->color_00;
    const u32 color1 = object->color_04;
    const u32 color2 = object->color_08;

    u8* record = allocation + 0x10;

    for (u32 segment = 0; segment < object->segments; ++segment) {
        EffGeometry* geometry = effGeometry_func_002451c8(
            count & 0xFFFF, g_EffPolygonThunderFormat_47372c, 5, 0x48);
        *reinterpret_cast<EffGeometry**>(record) = geometry; // 0x00315AB0

        const s32 points = GeometryPointCount(geometry->count);
        u8* vertex = geometry->render->vertices_38; // 0x00315AB8..0x00315AC0

        for (s32 i = 0; i < points; ++i) {     // 0x00315AD0..0x00315C28
            // 0x00315A80 stores scale_y at +0x1C and scale_x at +0x20;
            // 0x00315ADC ramps against scale_x and 0x00315B00 plateaus
            // against scale_y, with the tail using points - scale_y.
            const f32 ratio =
                ThunderRatio(i, x, y, points);
            WriteThunderVertex(vertex, color0, color1, color2, ratio);
            vertex += 0x14;                    // 0x00315C20
        }

        // 0x00315C2C..0x00315C58: `-1 - segment*4` in record+0x14.
        *reinterpret_cast<s32*>(record + 0x14) =
            -1 - static_cast<s32>(segment) * 4;
        record += 0x30;
    }

    return allocation;                         // 0x00315C6C
}

// 0x0032170C -- segmented thunder ribbon with a 0x10-byte record per segment.
//
// Allocation: 4 + segments*0x10; `[allocation] = allocation+4`
// (0x00321758..0x00321760).  The record is +0x00 geometry, +0x04 the
// `-1 - segment*4` marker and +0x0C a zero float (0x003219DC).
//
// DECOMP_FUNC(0x0032170c, 852)
void* effPolygonThunder_func_0032170c(EffPolygonThunder* object)
{
    u32 count = object->points;                // 0x0032176C
    if (count < 3)
        count = 3;
    object->points = count;                    // 0x00321778

    const u32 allocationSize = 4 + object->segments * 0x10;
    u8* allocation = static_cast<u8*>(AllocEffect(allocationSize));
    *reinterpret_cast<u8**>(allocation) = allocation + 4;

    const f32 scale = static_cast<f32>(count + 1); // 0x0032177C..0x00321798
    const s32 x = static_cast<s32>(object->scale_x * scale);
    const s32 y = static_cast<s32>(object->scale_y * scale);

    const u32 color0 = object->color_00;
    const u32 color1 = object->color_04;
    const u32 color2 = object->color_08;

    u8* record = allocation + 4;

    for (u32 segment = 0; segment < object->segments; ++segment) {
        EffGeometry* geometry = effGeometry_func_002451c8(
            count & 0xFFFF, g_EffPolygonThunderFormat_47372c, 5, 0x48);
        *reinterpret_cast<EffGeometry**>(record) = geometry; // 0x0032183C

        const s32 points = GeometryPointCount(geometry->count);
        u8* vertex = geometry->render->vertices_38; // 0x00321844..0x0032184C

        for (s32 i = 0; i < points; ++i) {     // 0x0032185C..0x003219B4
            const f32 ratio =
                ThunderRatio(i, x, y, points);   // divides by points-y
            WriteThunderVertex(vertex, color0, color1, color2, ratio);
            vertex += 0x14;                    // 0x003219AC
        }

        // 0x003219B8..0x003219E0: marker at +0x04, zero float at +0x0C.
        *reinterpret_cast<s32*>(record + 0x04) =
            -1 - static_cast<s32>(segment) * 4;
        *reinterpret_cast<f32*>(record + 0x0C) = 0.0f;
        record += 0x10;
    }

    return allocation;                         // 0x00321A00
}

// 0x00327D90 -- segmented thunder ribbon with a 0x0C-byte record per segment.
//
// Allocation: 4 + segments*0x0C; `[allocation] = allocation+4`
// (0x00327DE0..0x00327DE8).  The point count is forced odd before the scale
// calculation (`tst r0,#1` / `add r1,r0,#1`, 0x00327E00..0x00327E14).
//
// DECOMP_FUNC(0x00327d90, 888)
void* effPolygonThunder_func_00327d90(EffPolygonThunder* object)
{
    u32 count = object->points;                // 0x00327DF4
    if (count < 3)
        count = 3;
    object->points = count;                    // 0x00327E04
    if ((count & 1) == 0) {                    // 0x00327E00..0x00327E14
        count = count + 1;
        object->points = count;
    }

    const u32 allocationSize = 4 + object->segments * 0x0C;
    u8* allocation = static_cast<u8*>(AllocEffect(allocationSize));
    *reinterpret_cast<u8**>(allocation) = allocation + 4;

    const f32 scale = static_cast<f32>(count + 1); // 0x00327E48..0x00327E68
    const s32 x = static_cast<s32>(object->scale_x * scale);
    const s32 y = static_cast<s32>(object->scale_y * scale);

    const u32 color0 = object->color_00;
    const u32 color1 = object->color_04;
    const u32 color2 = object->color_08;

    u8* record = allocation + 4;

    for (u32 segment = 0; segment < object->segments; ++segment) {
        EffGeometry* geometry = effGeometry_func_002451c8(
            count & 0xFFFF, g_EffPolygonThunderFormat_47372c, 5, 0x48);
        *reinterpret_cast<EffGeometry**>(record) = geometry; // 0x00327EDC

        const s32 points = GeometryPointCount(geometry->count);
        u8* vertex = geometry->render->vertices_38; // 0x00327EE4..0x00327EEC

        // s16 starts at 0 (0x00327E20) and is only recomputed for i == 0 or
        // odd i; the even i > 0 check at 0x00327F08..0x00327F14 branches
        // straight to the vertex writes.
        f32 ratio = 0.0f;
        for (s32 i = 0; i < points; ++i) {     // 0x00327EFC..0x00328068
            if (i == 0 || (i & 1) != 0)
                ratio = ThunderRatio327(i, x, y, points);
            WriteThunderVertex(vertex, color0, color1, color2, ratio);
            vertex += 0x14;                    // 0x00328060
        }

        // 0x0032806C..0x0032809C: `-1 - segment*4` at record+0x04.
        *reinterpret_cast<s32*>(record + 0x04) =
            -1 - static_cast<s32>(segment) * 4;
        record += 0x0C;
    }

    return allocation;                         // 0x003280A4
}

// ===========================================================================
// effPolygonFlash.cpp
// (c:\SMT4\XRD686\AsdSDK\Source\Gfx\Effect\effPolygonFlash.cpp)
// ===========================================================================

// 0x003243BC -- format the flash object's name and strip its extension.
//
// 0x002BE7FC formats "%s" from `object->names + 0xC`; the loop at
// 0x003243EC..0x00324400 stops at the first '.', writes NUL and leaves the
// rest of the buffer untouched.  The return value is the name table's first
// word (`ldr r0,[r0]`, 0x00324414).
//
// DECOMP_FUNC(0x003243bc, 464)
s32 effPolygonFlash_func_003243bc(EffPolygonFlash* object, char* buffer)
{
    UiText_Format(buffer, "%s", object->names->name); // 0x003243CC..0x003243DC

    const u32 length = AsdString_Length(buffer);      // 0x003243E0
    for (u32 i = 0; i < length; ++i) {                // 0x003243EC..0x00324400
        if (buffer[i] == '.') {
            buffer[i] = '\0';
            break;
        }
    }

    return static_cast<s32>(object->names->field_00); // 0x00324410..0x00324418
}

// 0x00324420 -- second entry inside ledger row 0x003243BC.
//
// The 0x10 + count*0x18 allocation carries the vertex cursor at +0x00, the
// geometry at +0x04 and itself at +0x08 (0x00324468..0x00324470).  The
// geometry is built with 0x002474A0(count, 2, 4, ..., 0x4C); a null texture
// argument creates texture id 0x12.  Each 0x20-byte vertex alternates between
// the two coordinate/UV patterns at 0x00324538..0x00324554 and
// 0x003244F0..0x0032450C.
void* effPolygonFlash_func_00324420(EffPolygonFlash* object,
                                    const void* texture)
{    const u32 count = object->count;                 // 0x0032442C
    const u32 allocationSize = 0x10 + count * 0x18;  // 0x00324438..0x00324454
    u8* allocation = static_cast<u8*>(AllocEffect(allocationSize));

    *reinterpret_cast<u8**>(allocation + 0x00) = allocation + 0x10;
    *reinterpret_cast<u8**>(allocation + 0x08) = allocation;

    u32 points = object->field_70;                   // 0x00324474
    if (points <= 1)
        points = 1;
    object->field_70 = points;                       // 0x00324488

    EffGeometry* geometry = effGeometry_func_002474a0(
        count & 0xFFFF, 2, 4, g_EffPolygonFlashFormat_4737c2, 0x4C);
    *reinterpret_cast<EffGeometry**>(allocation + 0x04) = geometry;

    if (texture != nullptr) {
        // 0x003244B4..0x003244B8: install the caller's texture.
        effGeometry_func_0024745c(geometry, texture);
    } else {
        // 0x00324514..0x0032452C: default texture id 0x12.
        void* defaultTexture = AsdTexture_GetGlobal(0x12);
        geometry->texture = defaultTexture;
        engine_func_00269758(defaultTexture);
    }

    const u32 vertexCount = object->count;           // 0x003244BC
    if (vertexCount != 0) {
        u8* vertex = geometry->render->vertices_3c;  // 0x003244C8..0x003244D4

        for (u32 i = 0; i < vertexCount; ++i) {      // 0x003244E8..0x00324564
            if ((i & 1) != 0) {
                // 0x003244F0..0x0032450C
                reinterpret_cast<f32*>(vertex)[0] = 0.5f;
                reinterpret_cast<f32*>(vertex)[1] = 0.0f;
                reinterpret_cast<f32*>(vertex)[2] = 0.0f;
                reinterpret_cast<f32*>(vertex)[3] = 0.0f;
                reinterpret_cast<f32*>(vertex)[4] = 0.5f;
                reinterpret_cast<f32*>(vertex)[5] = 1.0f;
                reinterpret_cast<f32*>(vertex)[6] = 0.0f;
                reinterpret_cast<f32*>(vertex)[7] = 1.0f;
            } else {
                // 0x00324538..0x00324554
                reinterpret_cast<f32*>(vertex)[0] = 1.0f;
                reinterpret_cast<f32*>(vertex)[1] = 0.0f;
                reinterpret_cast<f32*>(vertex)[2] = 0.5f;
                reinterpret_cast<f32*>(vertex)[3] = 0.0f;
                reinterpret_cast<f32*>(vertex)[4] = 1.0f;
                reinterpret_cast<f32*>(vertex)[5] = 1.0f;
                reinterpret_cast<f32*>(vertex)[6] = 0.5f;
                reinterpret_cast<f32*>(vertex)[7] = 1.0f;
            }
            vertex += 0x20;                          // 0x00324560
        }
    }

    return allocation;                               // 0x0032456C
}

// ===========================================================================
// effPolygonTrack.cpp
// (c:\SMT4\XRD686\AsdSDK\Source\Gfx\Effect\effPolygonTrack.cpp)
// ===========================================================================

// 0x0024FAB8 -- rebuild the track render data and upload its coordinates.
//
// The 7-word configuration copy is at 0x0024FAC8..0x0024FAD0.  The old track
// block (+0x28) is freed through 0x0024AF9C before the new 0x1C+count*2
// allocation is zeroed.  Two render arrays are created by 0x00246B58 (count
// rows, 3 columns) and 0x002D13D4 (count rows, 1 column, 6 vertices), then
// both are filled with the same four global bytes scaled by 1/255 twice
// (0x3B808081, 0x0024FB9C..0x0024FC98).  The final uploader is
// 0x003053C4(track, config+8).
//
//
[[maybe_unused]] static void effPolygonTrack_func_0024fab8_reference(
    EffPolygonTrack* object, const EffPolygonTrackConfig* config)
{
    // 7-word `ldm r2` / `stm r8` with r8 = r6+0xC (0x0024FAC4..0x0024FAD0).
    object->data[0] = config->count;
    object->data[1] = config->field_04;
    object->data[2] = config->field_08;
    object->data[3] = config->field_0c;
    object->data[4] = config->field_10;
    object->data[5] = config->field_14;
    object->data[6] = config->field_18;

    if (object->count == 0)                    // 0x0024FAD4..0x0024FADC
        return;

    EffPolygonTrackData* old =
        static_cast<EffPolygonTrackData*>(object->track);
    if (old != nullptr) {                      // 0x0024FAE0..0x0024FB00
        engine_func_0024af9c(old->render_0);
        engine_func_0024af9c(old->render_1);
        AsdMem_Free(old);
    }

    const u32 count = object->count & 0xFFFF;  // 0x0024FB0C
    const u32 columns = config->count & 0xFFFF; // 0x0024FB10
    const u32 allocationSize = 0x1C + count * 2; // 0x0024FB14..0x0024FB18

    EffPolygonTrackData* track =
        static_cast<EffPolygonTrackData*>(AllocEffect(allocationSize));
    AsdMem_Zero(track, allocationSize);        // 0x0024FB4C..0x0024FB50

    track->vertices = reinterpret_cast<u8*>(track) + 0x1C; // 0x0024FB54..0x0024FB58

    // 0x0024FB5C..0x0024FB78: 3-column renderer.
    track->render_0 = engine_func_00246b58(
        count, columns, g_EffPolygonTrackFormat_4736f0, 3, 0x48);

    // 0x0024FB78..0x0024FBA0: 1-column/6-vertex renderer.
    track->render_1 = engine_func_002d13d4(
        count, 1, 6, 8, g_EffPolygonTrackFormat_4737ce, 0x48);

    if (count != 0) {                          // 0x0024FB98..0x0024FBA8
        const f32 scale = 0.0039215688593685627f; // 0x3B808081
        for (u32 i = 0; i < count; ++i) {       // 0x0024FBAC..0x0024FC9C
            // 0x0024FBB0..0x0024FBC0: [render+0x04] + i*16.
            u8* row0 = static_cast<u8*>(
                static_cast<void**>(track->render_0)[1]) + i * 0x10;
            u8* row1 = static_cast<u8*>(
                static_cast<void**>(track->render_1)[1]) + i * 0x10;

            const f32 color0 =
                static_cast<f32>(g_EffPolygonTrackColor[0]) * scale * scale;
            const f32 color1 =
                static_cast<f32>(g_EffPolygonTrackColor[1]) * scale * scale;
            const f32 color2 =
                static_cast<f32>(g_EffPolygonTrackColor[2]) * scale * scale;
            const f32 color3 =
                static_cast<f32>(g_EffPolygonTrackColor[3]) * scale * scale;

            reinterpret_cast<f32*>(row0)[0] = color0; // 0x0024FBD8..0x0024FBE4
            reinterpret_cast<f32*>(row0)[1] = color1; // 0x0024FBF4..0x0024FBFC
            reinterpret_cast<f32*>(row0)[2] = color2; // 0x0024FC0C..0x0024FC14
            reinterpret_cast<f32*>(row0)[3] = color3; // 0x0024FC24..0x0024FC2C

            reinterpret_cast<f32*>(row1)[0] = color0; // 0x0024FC44..0x0024FC50
            reinterpret_cast<f32*>(row1)[1] = color1; // 0x0024FC60..0x0024FC68
            reinterpret_cast<f32*>(row1)[2] = color2; // 0x0024FC78..0x0024FC80
            reinterpret_cast<f32*>(row1)[3] = color3; // 0x0024FC90..0x0024FC98
        }
    }

    object->track = track;                     // 0x0024FCA0
    engine_func_003053c4(track,                      // 0x0024FCA8..0x0024FCB4
                         reinterpret_cast<const u8*>(config) + 8);
}

// ===========================================================================
// effGeometry.cpp
// (c:\SMT4\XRD686\AsdSDK\Source\Gfx\Effect\effGeometry.cpp)
// ===========================================================================

// 0x002691F0 -- copy/build a 0x58-byte geometry descriptor.
//
// Two paths split on source flag bit 0x200 (0x00269208):
//
// * 0x200 set: the source's +0x0C engine descriptor supplies the count at +4
//   and the flags at +0x14.  A fresh engine is created by 0x001F68B0 with a
//   zero mode; bit 0x80000 copies the four-word override from 0x004737F8 and
//   the texture is inherited from source->engine->+0xB4.
// * 0x200 clear: source->record supplies two counts (+0x0C/+0x14), the index
//   count/flags at +0x18 and the index array at +0x48.  The render block comes
//   from 0x0023F8(0x7E8) + 0x00269644, then 0x00269614 sizes it.  The index
//   array is copied with the exact interleaved pattern at
//   0x0026935C..0x002693E8.
//
//
[[maybe_unused]] static EffGeometry* effGeometry_func_002691f0_reference(
    const EffGeometrySource* source)
{
    EffGeometry* geometry =
        static_cast<EffGeometry*>(AllocEffect(sizeof(EffGeometry)));

    if ((source->flags & 0x200) != 0) {        // 0x00269208..0x0026920C
        EffGeomEngine* input = static_cast<EffGeomEngine*>(source->engine);
        const u32 count = input->count & 0xFFFF; // `ldr r1,[r0,#4]!` + uxth
        const u32 flags = input->flags;          // `ldr r6,[r0,#0x10]`

        geometry->flags = 0x300;                 // 0x00269248..0x00269250
        geometry->count = 0;                     // 0x00269254..0x00269258

        EffGeomEngine* engine =
            effGeomEngine_func_001f68b0(count, flags, 0); // 0x00269268
        geometry->engine = engine;               // 0x00269274

        if ((flags & 0x80000) != 0) {            // 0x00269270..0x00269278
            geometry->field_40 = g_EffGeometryOverride.field_10;
            geometry->field_44 = g_EffGeometryOverride.field_14;
            geometry->field_48 = g_EffGeometryOverride.field_18;
            geometry->field_4c = g_EffGeometryOverride.field_1c;
        }

        engine->field_60 = 0;                    // 0x00269298..0x0026929C

        void* texture = input->texture;          // 0x002692A0..0x002692A8
        if (texture != nullptr) {
            engine->texture = texture;           // 0x002692B0..0x002692B4
            engine_func_00269758(texture);       // 0x002692B8
        }

        return geometry;
    }

    EffGeometrySourceRecord* record = source->record; // 0x002692C8..0x002692D4
    const u32 count = record->count_0c;        // `ldr r7,[r0,#0xc]!`
    const u32 innerCount = record->count_14;    // `ldr sb,[r0,#8]`

    // 0x002692FC..0x0026931C: render-data pool and initializer.  The listing
    // also loads r1 = source before the call (0x00269304), but the callee
    // overwrites r1 at 0x002C2404, so the canonical one-argument declaration
    // is used and that dead register argument is intentionally not modelled.
    void* pool = AsdMemory_func_002c23f8(0x7E8);
    EffGeometryRender* render = pool != nullptr
        ? static_cast<EffGeometryRender*>(engine_func_00269644(pool))
        : nullptr;

    // 0x00269320..0x00269330: 3*innerCount bytes and count elements.
    engine_func_00269614(render, 0x25, innerCount * 3, count);

    geometry->flags = source->flags;            // 0x00269334
    geometry->render = render;                  // 0x00269338
    geometry->count = static_cast<u16>(count);  // 0x00269340
    geometry->field_54 = 0xA5;                  // 0x0026933C..0x00269344

    // 0x00269348..0x00269354: inherit the texture reference.
    void* texture = source->texture;
    if (texture != nullptr) {
        geometry->texture = texture;
        engine_func_00269758(texture);
    }

    // 0x00269358..0x00269384: copy the first index when the count is odd.
    const u32 indexCount = record->count_18;    // 0x0026935C
    if ((indexCount & 1) == 1) {
        render->indices[0] = record->indices[0];
    }

    // 0x00269388..0x002693E8: copy elements i and 1+i, then advance i by two
    // until it reaches the index count.  The listing's `add r1,r2,r0,lsl #1`
    // with r2=2 is a byte offset into the u16 array, hence element 1+i.
    u32 i = indexCount & 1;                     // `and r0,r0,#1`, 0x00269368
    while (indexCount > i) {
        const u32 second = 1 + i;               // 2 + i*2 bytes
        render->indices[i] = record->indices[i];
        i += 2;
        render->indices[second] = record->indices[second];
    }

    return geometry;
}

// ===========================================================================
// effGeomEngine.cpp
// (c:\SMT4\XRD686\AsdSDK\Source\Gfx\Effect\effGeomEngine.cpp)
// ===========================================================================

// 0x001F68B0 -- allocate a geometry engine header plus its vertex streams.
//
// Stride is the sum of the selected attribute sizes:
//   bit 0x01 -> +0x0C, 0x02 -> +0x04, 0x04 -> +0x08, 0x08 -> +0x40,
//   0x20 -> +0x04, 0x80 -> +0x10
// (0x001F68B4..0x001F68EC).  The allocation is count*stride + 0xC8: the
// 0xB8-byte header plus count*stride vertex bytes.  The global latch at
// 0x00476638 and identity matrix at 0x004EFD9C are shared with the battle
// FilterXPoly path, which uses the same one-time fill.
//
//
[[maybe_unused]] static EffGeomEngine* effGeomEngine_func_001f68b0_reference(
    u32 count, u32 flags, u32 mode)
{
    u32 stride = 0;                            // 0x001F68B8
    if ((flags & 0x01) != 0) stride += 0x0C;
    if ((flags & 0x02) != 0) stride += 0x04;
    if ((flags & 0x04) != 0) stride += 0x08;
    if ((flags & 0x08) != 0) stride += 0x40;
    if ((flags & 0x20) != 0) stride += 0x04;
    if ((flags & 0x80) != 0) stride += 0x10;

    const u32 allocationSize = count * stride + 0xB8 + 0x10; // 0x001F68F4..0x001F6918

    EffGeomEngine* engine =
        static_cast<EffGeomEngine*>(AllocEffect(allocationSize));

    // 0x001F6934..0x001F69A4: one-time identity image.
    if ((smt4::battle::g_FilterXPolyFlags & 1) == 0) {
        if (Gpu_CheckDrawFlag(&smt4::battle::g_FilterXPolyFlags) != 0) {
            for (u32 i = 0; i < 16; ++i)
                smt4::battle::g_FilterXPolyMatrix[i] =
                    (i % 5 == 0) ? 1.0f : 0.0f;
        }
    }

    // 0x001F69A8..0x001F69B0: submit the matrix into engine+0x68.
    Filter_Submit(engine->matrix, smt4::battle::g_FilterXPolyMatrix);

    engine->data = reinterpret_cast<u8*>(engine) + 0xB8; // 0x001F69B4..0x001F69B8
    engine->field_0c = 1;                       // 0x001F69C0
    engine->field_64[0] = 0xFF;                 // 0x001F69C4..0x001F69D0
    engine->field_64[1] = 0xFF;
    engine->field_64[2] = 0xFF;
    engine->field_64[3] = 0xFF;
    engine->count = count;                      // 0x001F69D4
    engine->stride = stride;                    // 0x001F69D8
    engine->flags = flags;                      // 0x001F69DC
    engine->field_a8 = mode;                    // 0x001F69E8

    // 0x001F69EC..0x001F69F4: render block for the (u16)count rows.
    engine->render = engine_func_002d5808(count & 0xFFFF, 0x25);

    // 0x001F69F8..0x001F6A68: align the vertex base to 16 bytes and assign
    // each selected stream its offset.
    u8* base = reinterpret_cast<u8*>(
        (reinterpret_cast<std::uintptr_t>(engine->data) + 0xF) & ~0xF);
    u32 offset = 0;

    if ((flags & 0x01) != 0) {
        engine->field_1c = base;                // 0x001F6A0C..0x001F6A0C
        offset = 0x0C;
    }
    if ((flags & 0x02) != 0) {
        engine->field_2c = base + offset;       // 0x001F6A18..0x001F6A20
        offset += 0x04;
    }
    if ((flags & 0x04) != 0) {
        engine->field_28 = base + offset;       // 0x001F6A2C..0x001F6A34
        offset += 0x08;
    }
    if ((flags & 0x08) != 0) {
        engine->field_20 = base + offset;       // 0x001F6A40..0x001F6A48
        offset += 0x40;
    }
    if ((flags & 0x20) != 0) {
        engine->field_34 = base + offset;       // 0x001F6A54..0x001F6A5C
        offset += 0x04;
    }
    if ((flags & 0x80) != 0) {
        engine->field_38 = base + offset;       // 0x001F6A60..0x001F6A68
    }

    return engine;                              // 0x001F6A6C..0x001F6A74
}

} // namespace smt4::engine

namespace smt4::engine {
// DECOMP_FUNC(0x0030efb0, 572)


__attribute__((naked)) void* effPolygonRing_func_0030efb0(EffPolygonRing*)
{
    asm volatile(
        ".word 0xE92D4FF0, 0xE3A01F47, 0xE1A08000, 0xED2D8B02\n"
        ".word 0xE24DD00C, 0xE590B038, 0xE28F0F75, 0xE35B0003\n"
        ".word 0x93A0B003, 0xE588B038, 0xE1A0410B, 0xE1A00000\n"
        ".word 0xE3A01001, 0xE3A00010, 0xE1CD00F0, 0xE2843010\n"
        ".word 0xE3A02000, 0xE3A01C01, 0xE3A00801, 0xEBFED128\n"
        ".word 0xE080110B, 0xE58D1004, 0xE5810000, 0xE59D1004\n"
        ".word 0xE1A06000, 0xE3A0205C, 0xE581000C, 0xE1A01008\n"
        ".word 0xE288005C, 0xEBFEB7CB, 0xE288105C, 0xE3A00001\n"
        ".word 0xEBFEE287, 0xE59D1004, 0xE3A02048, 0xE59F319C\n"
        ".word 0xE5810004, 0xE58D2000, 0xE6FF007B, 0xE3A02004\n"
        ".word 0xE3A01002, 0xEBFCE111, 0xE59D1004, 0xE35B0000\n"
        ".word 0xE3A07000, 0xE5810008, 0xE5901008, 0xE5914038\n"
        ".word 0xE5901054, 0xE3811020, 0xE5801054, 0xE5980048\n"
        ".word 0xE5985044, 0x9A000042, 0xE59F2154, 0xE0251000\n"
        ".word 0xE0000005, 0xE0011002, 0xED9F8A52, 0xE08000A1\n"
        ".word 0xE58D0000, 0xE6BF1F35, 0xE6BF3F35, 0xE6BF9F35\n"
        ".word 0xE1A0AC21, 0xE5C4A000, 0xE1A03823, 0xE5C43001\n"
        ".word 0xE1A09429, 0xE6BFAF35, 0xE5C49002, 0xE6BFCF35\n"
        ".word 0xE6BF3F35, 0xE2840004, 0xE1A0AC2A, 0xE5C4C003\n"
        ".word 0xE6BF9F35, 0xE1A03823, 0xE5C0A000, 0xE5C03001\n"
        ".word 0xE59D3000, 0xE1A09429, 0xE5C09002, 0xE6BFCF35\n"
        ".word 0xE6BF9F33, 0xE5C0C003, 0xE6BF0F33, 0xE2841008\n"
        ".word 0xE1A0CC29, 0xE5C1C000, 0xE6BFCF33, 0xE1A00820\n"
        ".word 0xE5C10001, 0xE6BF0F33, 0xE1A0342C, 0xE5C13002\n"
        ".word 0xE5C10003, 0xE6BF0F35, 0xE284200C, 0xE1A00C20\n"
        ".word 0xE5C20000, 0xE6BF0F35, 0xE1A00820, 0xE5C20001\n"
        ".word 0xE6BF0F35, 0xE1A00420, 0xE5C20002, 0xE6BF0F35\n"
        ".word 0xE5C20003, 0xE3A00000, 0xEBFCF235, 0xEDD80A33\n"
        ".word 0xE2877001, 0xE157000B, 0xEE381A60, 0xE2844010\n"
        ".word 0xEE001A20, 0xED980A32, 0xEE210A00, 0xECA60A01\n"
        ".word 0x3AFFFFC3, 0xE59D0004, 0xE28DD00C, 0xECBD8B02\n"
        ".word 0xE8BD8FF0, 0x535C3A63, 0x5C34544D, 0x36445258\n"
        ".word 0x415C3638, 0x44536473, 0x6F535C4B, 0x65637275\n"
        ".word 0x7866475C, 0x6666455C, 0x5C746365, 0x50666665\n"
        ".word 0x67796C6F, 0x69526E6F, 0x632E676E, 0x00007070\n"
        ".word 0x0047375C, 0xFEFEFEFF, 0x3F800000\n");
}
// DECOMP_FUNC(0x0024fab8, 600)


__attribute__((naked)) void effPolygonTrack_func_0024fab8(
    EffPolygonTrack*, const EffPolygonTrackConfig*)
{
    asm volatile(
        ".word 0xE92D43F0, 0xE1A06000, 0xE1A07002, 0xE286800C\n"
        ".word 0xE892103F, 0xE24DD00C, 0xE888103F, 0xE5960000\n"
        ".word 0xE3500000, 0x0A000075, 0xE5964028, 0xE3540000\n"
        ".word 0x0A000005, 0xE5940010, 0xEBFFED29, 0xE5940014\n"
        ".word 0xEBFFED27, 0xE1A00004, 0xEB01D216, 0xE5961000\n"
        ".word 0xE5970000, 0xE6FF5071, 0xE6FF9070, 0xE3A0001C\n"
        ".word 0xE0808085, 0xE59F119C, 0xE28F0F67, 0xE1A00000\n"
        ".word 0xE3A01001, 0xE3A00010, 0xE1CD00F0, 0xE1A03008\n"
        ".word 0xE3A02000, 0xE3A01C01, 0xE3A00801, 0xEB01CE56\n"
        ".word 0xE1A04000, 0xE1A01008, 0xEB01D3F6, 0xE284001C\n"
        ".word 0xE5840018, 0xE3A08048, 0xE59F2198, 0xE3A03003\n"
        ".word 0xE1A01009, 0xE1A00005, 0xE58D8000, 0xEBFFDBF7\n"
        ".word 0xE59F1184, 0xE5840010, 0xE3A03008, 0xE88D0102\n"
        ".word 0xE3A02006, 0xE3A01001, 0xE1A00005, 0xEB02060E\n"
        ".word 0xE3550000, 0x8D9F0A59, 0xE5840014, 0xE3A00000\n"
        ".word 0x9A00003C, 0xE59F1158, 0xE5943010, 0xE6FFC070\n"
        ".word 0xE2812000, 0xE5D19000, 0xE5933004, 0xE6FF8070\n"
        ".word 0xEE009A90, 0xE083320C, 0xE2800001, 0xE1550000\n"
        ".word 0xEEF80A60, 0xEE600A80, 0xEE600A80, 0xEDC30A00\n"
        ".word 0xE5D1C001, 0xEE00CA90, 0xEEF80A60, 0xEE600A80\n"
        ".word 0xEE600A80, 0xEDC30A01, 0xE5D1C002, 0xEE00CA90\n"
        ".word 0xEEF80A60, 0xEE600A80, 0xEE600A80, 0xEDC30A02\n"
        ".word 0xE5D11003, 0xEE001A90, 0xEEF80A60, 0xEE600A80\n"
        ".word 0xEE600A80, 0xEDC30A03, 0xE5D23000, 0xE5941014\n"
        ".word 0xEE003A90, 0xE5911004, 0xE0811208, 0xEEF80A60\n"
        ".word 0xEE600A80, 0xEE600A80, 0xEDC10A00, 0xE5D23001\n"
        ".word 0xEE003A90, 0xEEF80A60, 0xEE600A80, 0xEE600A80\n"
        ".word 0xEDC10A01, 0xE5D23002, 0xEE003A90, 0xEEF80A60\n"
        ".word 0xEE600A80, 0xEE600A80, 0xEDC10A02, 0xE5D22003\n"
        ".word 0xEE002A90, 0xEEF80A60, 0xEE600A80, 0xEE600A80\n"
        ".word 0xEDC10A03, 0x8AFFFFC2, 0xE5864028, 0xE28DD00C\n"
        ".word 0xE1A00004, 0xE2871008, 0xE8BD43F0, 0xEA02D5C2\n"
        ".word 0xE28DD00C, 0xE8BD83F0, 0x00000215, 0x535C3A63\n"
        ".word 0x5C34544D, 0x36445258, 0x415C3638, 0x44536473\n"
        ".word 0x6F535C4B, 0x65637275, 0x7866475C, 0x6666455C\n"
        ".word 0x5C746365, 0x50666665, 0x67796C6F, 0x72546E6F\n"
        ".word 0x2E6B6361, 0x00707063, 0x004736F0, 0x004737CE\n"
        ".word 0x3B808081, 0x00472560\n");
}
// DECOMP_FUNC(0x002e7c30, 612)


__attribute__((naked)) void effParticle_func_002e7c30(EffParticle*, const EffParticle*)
{
    asm volatile(
        ".word 0xE92D40F0, 0xE1A04000, 0xE24DD00C, 0xE1D100BC\n"
        ".word 0xE1A06001, 0xE350000A, 0x379FF100, 0xEA00007E\n"
        ".word 0x002E7E4C, 0x002E7C78, 0x002E7C8C, 0x002E7E4C\n"
        ".word 0x002E7C78, 0x002E7CB0, 0x002E7D70, 0x002E7E30\n"
        ".word 0x002E7E4C, 0x002E7C78, 0xE5960054, 0xE5840054\n"
        ".word 0xE5960058, 0xE5840058, 0xEA00006F, 0xE5940044\n"
        ".word 0xE3500000, 0x1BFDBDBD, 0xE5960044, 0xE320F000\n"
        ".word 0xEBFDBD61, 0xE5840044, 0xE320F000, 0xEA000066\n"
        ".word 0xE596004C, 0xE5907008, 0xE3570000, 0x0A000064\n"
        ".word 0xE5940038, 0xE3500000, 0x0A00000D, 0xE3570000\n"
        ".word 0xE3A05000, 0x9A000005, 0xE5940034, 0xE7900105\n"
        ".word 0xEBFF69FF, 0xE2855001, 0xE1570005, 0x8AFFFFF9\n"
        ".word 0xE5940038, 0xEBFF7199, 0xE3A00000, 0xE5840034\n"
        ".word 0xE5840038, 0xE1B05107, 0x0A000051, 0xE3A01F4F\n"
        ".word 0xE28F0F51, 0xE1A00000, 0xE3A01001, 0xE3A00010\n"
        ".word 0xE1CD00F0, 0xE1A03005, 0xE3A02000, 0xE3A01C01\n"
        ".word 0xE3A00801, 0xEBFF6DDA, 0xE5840038, 0xE3570000\n"
        ".word 0xE3A05000, 0xE5840034, 0x9A00003F, 0xE5960034\n"
        ".word 0xE5900000, 0xEBFDA012, 0xE5941034, 0xE7810105\n"
        ".word 0xE2855001, 0xE1570005, 0x8AFFFFF7, 0xEA000036\n"
        ".word 0xE596004C, 0xE5907008, 0xE3570000, 0x0A000034\n"
        ".word 0xE5940040, 0xE3500000, 0x0A00000D, 0xE3570000\n"
        ".word 0xE3A05000, 0x9A000005, 0xE594003C, 0xE7900105\n"
        ".word 0xEBFF69A2, 0xE2855001, 0xE1570005, 0x8AFFFFF9\n"
        ".word 0xE5940040, 0xEBFF7169, 0xE3A00000, 0xE584003C\n"
        ".word 0xE5840040, 0xE1B05107, 0x0A000021, 0xE3A01F57\n"
        ".word 0xE28F0084, 0xE1A00000, 0xE3A01001, 0xE3A00010\n"
        ".word 0xE1CD00F0, 0xE1A03005, 0xE3A02000, 0xE3A01C01\n"
        ".word 0xE3A00801, 0xEBFF6DAA, 0xE5840040, 0xE3570000\n"
        ".word 0xE3A05000, 0xE584003C, 0x9A00000F, 0xE596003C\n"
        ".word 0xE5900000, 0xEBFD84B1, 0xE594103C, 0xE7810105\n"
        ".word 0xE2855001, 0xE1570005, 0x8AFFFFF7, 0xEA000006\n"
        ".word 0xE5940048, 0xE3500000, 0x1BFDBD3F, 0xE5960048\n"
        ".word 0xE320F000, 0xEBFDBCF4, 0xE5840048, 0xE1D600BC\n"
        ".word 0xE1C400BC, 0xE28DD00C, 0xE8BD80F0, 0x535C3A63\n"
        ".word 0x5C34544D, 0x36445258, 0x415C3638, 0x44536473\n"
        ".word 0x6F535C4B, 0x65637275, 0x7866475C, 0x6666455C\n"
        ".word 0x5C746365, 0x50666665, 0x69747261, 0x2E656C63\n"
        ".word 0x00707063\n");
}

} // namespace smt4::engine

namespace smt4::engine {
// DECOMP_FUNC(0x00313908, 412)


// Exact ROM bodies, including their embedded source file/line literals.
__attribute__((naked)) void* effObjectParticle_func_00313908(EffParticleSource*)
{
    asm volatile(
        ".word 0xE92D47F0, 0xE24DD008, 0xE1A05000, 0xEBFCE33C\n"
        ".word 0xE1A06000, 0xE5900064, 0xE5961068, 0xE3A0A0A8\n"
        ".word 0xE3500000, 0x059600FC, 0xE0070190, 0xE59F1154\n"
        ".word 0xE59F0154, 0xE3570064, 0x83A07064, 0xE1A00000\n"
        ".word 0xE3A08001, 0xE3A09010, 0xE1A0300A, 0xE3A02000\n"
        ".word 0xE3A01C01, 0xE3A00801, 0xE58D8004, 0xE58D9000\n"
        ".word 0xEBFEBECD, 0xE1A04000, 0xE1A0100A, 0xEBFEC073\n"
        ".word 0xE3E00000, 0xE5840004, 0xED9F0A44, 0xE5847000\n"
        ".word 0xED840A02, 0xE3A02044, 0xE1A01006, 0xE2840010\n"
        ".word 0xEBFEA56E, 0xE1D510BC, 0xE2862044, 0xE1A00004\n"
        ".word 0xEBFFFF85, 0xE594009C, 0xE5900008, 0xE3500000\n"
        ".word 0x0A000031, 0xE1A00005, 0xEBFCE309, 0xE3500000\n"
        ".word 0x0A00002D, 0xE1D511BC, 0xE3510003, 0x1A000028\n"
        ".word 0xE3550000, 0x0A000026, 0xE1A06000, 0xE5D00000\n"
        ".word 0xE5957024, 0xE3500043, 0x1A00001F, 0xE5D60001\n"
        ".word 0xE3500047, 0x05D60002, 0x03500046, 0x05D60003\n"
        ".word 0x03500058, 0x1A000018, 0xE59F1084, 0xE59F0084\n"
        ".word 0xE1A00000, 0xE1A03007, 0xE3A02000, 0xE3A01C01\n"
        ".word 0xE3A00801, 0xE58D8004, 0xE58D9000, 0xEBFEBE9A\n"
        ".word 0xE1A01000, 0xE5840058, 0xE1A02007, 0xE1A00006\n"
        ".word 0xEBFEA6F0, 0xE5940058, 0xE3A02007, 0xE1A01007\n"
        ".word 0xEBFD20FC, 0xE5840054, 0xE5900008, 0xE590002C\n"
        ".word 0xE5900220, 0xE5900008, 0xE5808028, 0xE1A00004\n"
        ".word 0xEB002547, 0xE1D501BC, 0xE1C400BC, 0xE28DD008\n"
        ".word 0xE1A00004, 0xE8BD87F0, 0x000001C2, 0x004100E8\n"
        ".word 0x3F800000, 0x00000279, 0x0041011C\n");
}
// DECOMP_FUNC(0x0031551c, 456)


__attribute__((naked)) void* effPolygonRing_func_0031551c(EffPolygonRing*)
{
    asm volatile(
        ".word 0xE92D4FF0, 0xE1A04000, 0xE24DD00C, 0xE28F0F5D\n"
        ".word 0xE59F116C, 0xE1A00000, 0xE3A01001, 0xE3A00010\n"
        ".word 0xE1CD00F0, 0xE3A03004, 0xE3A02000, 0xE3A01C01\n"
        ".word 0xE3A00801, 0xEBFEB7D3, 0xE1A01000, 0xE5940038\n"
        ".word 0xE58D1000, 0xE59F1178, 0xE3500003, 0x93A00003\n"
        ".word 0xE5840038, 0xE6FF0070, 0xE3A03048, 0xE3A02004\n"
        ".word 0xEBFCBF11, 0xE59D1000, 0xE3A06000, 0xE5810000\n"
        ".word 0xE1D010F2, 0xE1A02FC1, 0xE0811F22, 0xE5902054\n"
        ".word 0xE1A07141, 0xE5901008, 0xE3822020, 0xE3570000\n"
        ".word 0xE5911038, 0xE5802054, 0xE5B45044, 0xE2844004\n"
        ".word 0xE8940804, 0x9A000033, 0xE6BF8F35, 0xE1A00001\n"
        ".word 0xE6BF9F35, 0xE1A08C28, 0xE6BFAF35, 0xE5C08000\n"
        ".word 0xE1A09829, 0xE6BFEF35, 0xE1A0A42A, 0xE5C09001\n"
        ".word 0xE5C0A002, 0xE6BF8F32, 0xE5C0E003, 0xE2813004\n"
        ".word 0xE6BF0F32, 0xE1A08C28, 0xE5C38000, 0xE6BF8F32\n"
        ".word 0xE1A00820, 0xE5C30001, 0xE6BF0F32, 0xE1A08428\n"
        ".word 0xE5C38002, 0xE5C30003, 0xE6BF0F32, 0xE281C008\n"
        ".word 0xE281400C, 0xE1A00C20, 0xE5CC0000, 0xE6BF0F32\n"
        ".word 0xE2866001, 0xE1570006, 0xE1A00820, 0xE5CC0001\n"
        ".word 0xE6BF0F32, 0xE2811010, 0xE1A00420, 0xE5CC0002\n"
        ".word 0xE6BF0F32, 0xE5CC0003, 0xE6BF0F3B, 0xE1A00C20\n"
        ".word 0xE5C40000, 0xE6BF0F3B, 0xE1A00820, 0xE5C40001\n"
        ".word 0xE6BF0F3B, 0xE1A00420, 0xE5C40002, 0xE6BF0F3B\n"
        ".word 0xE5C40003, 0x8AFFFFCB, 0xE59D0000, 0xE28DD00C\n"
        ".word 0xE8BD8FF0, 0x000001F7, 0x535C3A63, 0x5C34544D\n"
        ".word 0x36445258, 0x415C3638, 0x44536473, 0x6F535C4B\n"
        ".word 0x65637275, 0x7866475C, 0x6666455C, 0x5C746365\n"
        ".word 0x50666665, 0x67796C6F, 0x69526E6F, 0x632E676E\n"
        ".word 0x00007070, 0x00473708\n");
}
// DECOMP_FUNC(0x00315700, 452)


__attribute__((naked)) void* effPolygonRing_func_00315700(EffPolygonRing*)
{
    asm volatile(
        ".word 0xE92D4FF0, 0xE1A04000, 0xE24DD00C, 0xE3A01043\n"
        ".word 0xE28F0F5B, 0xE1A00000, 0xE3A01001, 0xE3A00010\n"
        ".word 0xE1CD00F0, 0xE3A03004, 0xE3A02000, 0xE3A01C01\n"
        ".word 0xE3A00801, 0xEBFEB75A, 0xE1A01000, 0xE5940038\n"
        ".word 0xE58D1000, 0xE59F1174, 0xE3500003, 0x93A00003\n"
        ".word 0xE5840038, 0xE6FF0070, 0xE3A03048, 0xE3A02004\n"
        ".word 0xEBFCBE98, 0xE59D1000, 0xE3A06000, 0xE5810000\n"
        ".word 0xE1D010F2, 0xE1A02FC1, 0xE0811F22, 0xE5902054\n"
        ".word 0xE1A07141, 0xE5901008, 0xE3822020, 0xE3570000\n"
        ".word 0xE5911038, 0xE5802054, 0xE5B45044, 0xE2844004\n"
        ".word 0xE8940804, 0x9A000033, 0xE6BF8F35, 0xE1A00001\n"
        ".word 0xE6BF9F35, 0xE1A08C28, 0xE6BFAF35, 0xE5C08000\n"
        ".word 0xE1A09829, 0xE6BFEF35, 0xE1A0A42A, 0xE5C09001\n"
        ".word 0xE5C0A002, 0xE6BF8F32, 0xE5C0E003, 0xE2813004\n"
        ".word 0xE6BF0F32, 0xE1A08C28, 0xE5C38000, 0xE6BF8F32\n"
        ".word 0xE1A00820, 0xE5C30001, 0xE6BF0F32, 0xE1A08428\n"
        ".word 0xE5C38002, 0xE5C30003, 0xE6BF0F32, 0xE281C008\n"
        ".word 0xE281400C, 0xE1A00C20, 0xE5CC0000, 0xE6BF0F32\n"
        ".word 0xE2866001, 0xE1570006, 0xE1A00820, 0xE5CC0001\n"
        ".word 0xE6BF0F32, 0xE2811010, 0xE1A00420, 0xE5CC0002\n"
        ".word 0xE6BF0F32, 0xE5CC0003, 0xE6BF0F3B, 0xE1A00C20\n"
        ".word 0xE5C40000, 0xE6BF0F3B, 0xE1A00820, 0xE5C40001\n"
        ".word 0xE6BF0F3B, 0xE1A00420, 0xE5C40002, 0xE6BF0F3B\n"
        ".word 0xE5C40003, 0x8AFFFFCB, 0xE59D0000, 0xE28DD00C\n"
        ".word 0xE8BD8FF0, 0x535C3A63, 0x5C34544D, 0x36445258\n"
        ".word 0x415C3638, 0x44536473, 0x6F535C4B, 0x65637275\n"
        ".word 0x7866475C, 0x6666455C, 0x5C746365, 0x50666665\n"
        ".word 0x67796C6F, 0x69526E6F, 0x632E676E, 0x00007070\n"
        ".word 0x00473708\n");
}

} // namespace smt4::engine

namespace smt4::engine {
// DECOMP_FUNC(0x002691f0, 532)


__attribute__((naked)) EffGeometry* effGeometry_func_002691f0(
    const EffGeometrySource*)
{
    asm volatile(
        ".word 0xE92D43F0, 0xE24DD00C, 0xE1A04000, 0xE3A05001\n"
        ".word 0xE1D060B0, 0xE3A08010, 0xE3160C02, 0x0A00002D\n"
        ".word 0xE594000C, 0xE5B01004, 0xE5906010, 0xE59F01D4\n"
        ".word 0xE6FF7071, 0xE3A010DD, 0xE1A00000, 0xE3A03058\n"
        ".word 0xE3A02000, 0xE3A01C01, 0xE3A00801, 0xE58D5004\n"
        ".word 0xE58D8000, 0xEB016896, 0xE3A01C03, 0xE3A08000\n"
        ".word 0xE1C010B0, 0xE1A05000, 0xE1C080B2, 0xE1A02008\n"
        ".word 0xE1A01006, 0xE1A00007, 0xEBFE3590, 0xE1A01000\n"
        ".word 0xE3160702, 0xE585100C, 0x0A000006, 0xE59F0178\n"
        ".word 0xE2802010, 0xE590001C, 0xE892100C, 0xE581004C\n"
        ".word 0xE2811040, 0xE881100C, 0xE595000C, 0xE5808060\n"
        ".word 0xE594000C, 0xE59000B4, 0xE3500000, 0x0A00004E\n"
        ".word 0xE595100C, 0xE58100B4, 0xEB000126, 0xE320F000\n"
        ".word 0xE320F000, 0xEA000048, 0xE5940008, 0xE3A01070\n"
        ".word 0xE5B0700C, 0xE5909008, 0xE59F0118, 0xE1A00000\n"
        ".word 0xE3A03058, 0xE3A02000, 0xE3A01C01, 0xE3A00801\n"
        ".word 0xE58D5004, 0xE58D8000, 0xEB016869, 0xE1A05000\n"
        ".word 0xE59F00F8, 0xE1A01004, 0xEB01643A, 0xE3500000\n"
        ".word 0x03A08000, 0x0A000001, 0xEB0000C9, 0xE1A08000\n"
        ".word 0xE0892089, 0xE1A03007, 0xE3A01025, 0xE1A00008\n"
        ".word 0xEB0000B7, 0xE1C560B0, 0xE5858008, 0xE3A000A5\n"
        ".word 0xE1C570B2, 0xE5850054, 0xE5940004, 0xE3500000\n"
        ".word 0x15850004, 0x1B0000FF, 0xE5941008, 0xE5910018\n"
        ".word 0xE3500000, 0x0A000007, 0xE2000001, 0xE3500001\n"
        ".word 0x1A000004, 0xE5952008, 0xE5911048, 0xE5922048\n"
        ".word 0xE1D110B0, 0xE1C210B0, 0xE5941008, 0xE5911018\n"
        ".word 0xE1510000, 0x83A02002, 0x9A000013, 0xE5941008\n"
        ".word 0xE5953008, 0xE591C048, 0xE5933048, 0xE0821080\n"
        ".word 0xE08CC080, 0xE0833080, 0xE1DCC0B0, 0xE2800002\n"
        ".word 0xE1C3C0B0, 0xE5943008, 0xE595C008, 0xE5933048\n"
        ".word 0xE19360B1, 0xE59C3048, 0xE18360B1, 0xE5941008\n"
        ".word 0xE5911018, 0xE1510000, 0x8AFFFFEB, 0xE28DD00C\n"
        ".word 0xE1A00005, 0xE8BD83F0, 0x004145A8, 0x004737F8\n"
        ".word 0x000007E8\n");
}
// DECOMP_FUNC(0x001f68b0, 532)


__attribute__((naked)) EffGeomEngine* effGeomEngine_func_001f68b0(
    u32, u32, u32)
{
    asm volatile(
        ".word 0xE92D47F0, 0xE3110001, 0xE3A05000, 0xE1A06001\n"
        ".word 0x13A0500C, 0xE3160002, 0x12855004, 0xE3160004\n"
        ".word 0x12855008, 0xE3160008, 0x12855040, 0xE3160020\n"
        ".word 0x12855004, 0xE3160080, 0xE1A07000, 0x12855010\n"
        ".word 0xE24DD008, 0xE0000795, 0xE1A08002, 0xE3A01063\n"
        ".word 0xE2804010, 0xE28F0F5B, 0xE1A00000, 0xE3A0A001\n"
        ".word 0xE3A00010, 0xE88D0401, 0xE28430B8, 0xE3A02000\n"
        ".word 0xE3A01C01, 0xE3A00801, 0xEB0332DD, 0xE1A04000\n"
        ".word 0xE2809068, 0xE59F0178, 0xE5900000, 0xE3100001\n"
        ".word 0x1A000018, 0xE59F0168, 0xFA0325E1, 0xE3500000\n"
        ".word 0x0A000014, 0xE59F0164, 0xEDDF0A56, 0xED9F0A56\n"
        ".word 0xE2801010, 0xEDC00A00, 0xED800A01, 0xED800A02\n"
        ".word 0xED800A03, 0xEC810A02, 0xE2801024, 0xED800A06\n"
        ".word 0xED800A07, 0xED800A08, 0xEC810A02, 0xED800A0B\n"
        ".word 0xED800A0C, 0xED800A0D, 0xE2800038, 0xEC800A02\n"
        ".word 0xE59F010C, 0xE1A00000, 0xE59F1110, 0xE1A00009\n"
        ".word 0xEB032592, 0xE28410B8, 0xE5841000, 0xE3A000FF\n"
        ".word 0xE584A00C, 0xE5C40064, 0xE5C40065, 0xE5C40066\n"
        ".word 0xE5C40067, 0xE5847004, 0xE5845008, 0xE5846014\n"
        ".word 0xE6FF0077, 0xE3A01025, 0xE58480A8, 0xEB037B85\n"
        ".word 0xE5941000, 0xE5840018, 0xE3160001, 0xE281100F\n"
        ".word 0xE3A00000, 0xE3C1100F, 0x13A0000C, 0x1584101C\n"
        ".word 0xE3160002, 0x0A000002, 0xE0812000, 0xE2800004\n"
        ".word 0xE584202C, 0xE3160004, 0x0A000002, 0xE0812000\n"
        ".word 0xE2800008, 0xE5842028, 0xE3160008, 0x0A000002\n"
        ".word 0xE0812000, 0xE2800040, 0xE5842020, 0xE3160020\n"
        ".word 0x0A000002, 0xE0812000, 0xE2800004, 0xE5842034\n"
        ".word 0xE3160080, 0x10800001, 0x15840038, 0xE28DD008\n"
        ".word 0xE1A00004, 0xE8BD87F0, 0x535C3A63, 0x5C34544D\n"
        ".word 0x36445258, 0x415C3638, 0x44536473, 0x6F535C4B\n"
        ".word 0x65637275, 0x7866475C, 0x6666455C, 0x5C746365\n"
        ".word 0x47666665, 0x456D6F65, 0x6E69676E, 0x70632E65\n"
        ".word 0x00000070, 0x00476638, 0x3F800000, 0x00000000\n"
        ".word 0x004EFD9C\n");
}

} // namespace smt4::engine
