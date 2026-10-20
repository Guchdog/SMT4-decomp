#include "engine/asd_effect2.h"
#include "engine/asd_effect.h"
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

    // Effect behavior factory and reference helpers.
    void* effBehavior_func_00269404(u32 id, u32 count, void* data);        // 0x00269404
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
// DECOMP_FUNC(0x002e7c30, 612)
void effParticle_func_002e7c30(EffParticle* dest, const EffParticle* source)
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
// DECOMP_FUNC(0x00313908, 412)
void* effObjectParticle_func_00313908(EffParticleSource* source)
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
// DECOMP_FUNC(0x0030efb0, 572)
void* effPolygonRing_func_0030efb0(EffPolygonRing* object)
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
// DECOMP_FUNC(0x0031551c, 456)
void* effPolygonRing_func_0031551c(EffPolygonRing* object)
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
// DECOMP_FUNC(0x00315700, 452)
void* effPolygonRing_func_00315700(EffPolygonRing* object)
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
// DECOMP_FUNC(0x0024fab8, 600)
void effPolygonTrack_func_0024fab8(EffPolygonTrack* object,
                                   const EffPolygonTrackConfig* config)
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
// DECOMP_FUNC(0x002691f0, 532)
EffGeometry* effGeometry_func_002691f0(const EffGeometrySource* source)
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
// DECOMP_FUNC(0x001f68b0, 532)
EffGeomEngine* effGeomEngine_func_001f68b0(u32 count, u32 flags, u32 mode)
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
