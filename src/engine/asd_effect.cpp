#include "engine/asd_effect.h"
#include "engine/asd_symbols.h"
#include <cstdint>

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

extern "C" {
    // AsdMemory (c:\SMT4\XRD686\AsdSDK\Source\Sys\Mem\AsdMemory.cpp)
    void* AsdWork_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 a5); // 0x002c34a4
    void  AsdMem_Zero(void* ptr, u32 size);                                // 0x002c4b30
    void  AsdMem_Free(void* ptr);                                          // 0x002c4360
    void  AsdMem_Copy(void* dst, const void* src, u32 size);               // 0x002c5ff4

    // AsdFile (c:\SMT4\XRD686\AsdSDK\Source\Sys\File\AsdFile.cpp)
    // 0x002C5E3C: build "rom:/%s" (0x002C5E9C), open, read `user` bytes and
    // return the data pointer; `out_size` receives the stream size.
    void* AsdFile_LoadSync(const char* name, u32* out_size,
                           u32 flags, u32 user);                           // 0x002c5e3c

    // AsdDraw / AsdPart (names shared with asd_frame.cpp and asd_model.cpp)
    void  AsdDrawDesc_Init(void* desc);                                    // 0x002a3ff8
    void  AsdPart_Setup1(void* part, void* arg);                           // 0x002a3bf8
    void  AsdPart_Setup2(void* part, void* arg);                           // 0x002a3d50
    void  AsdPart_SetScale(void* part, f32 scale);                         // 0x002a399c
    void  AsdPart_SetValue(void* part, void* value);                       // 0x002a37dc

    // 0x00152D7C / 0x00152DAC: nested counter over the global at 0x00465120.
    // `Enter` stores its argument in the inner object's +0x38 slot and bumps
    // the depth; `Leave` decrements and restores the saved +0x38 value.
    void  AsdEffect_LockEnter(u32 id);                                     // 0x00152d7c
    void  AsdEffect_LockLeave();                                           // 0x00152dac

    // AsdEffectTexture: "STEX" magic test and the two texture factories.
    bool  AsdEffect_IsStex(const void* data);                              // 0x0028cba8
    void* AsdEffectTexture_func_0028cabc(const void* source);              // 0x0028cabc
    void* EffParts_CreateTexture(const void* source);                      // 0x0028ca7c

    // effP2A entry binder (writes one 0x14-byte destination entry).
    void  EffP2A_BindEntry(smt4::engine::EffP2AAnim* anim, u32 index);      // 0x001d21a0

    // effParts child re-parenting helper; recurses through the manager list.
    void  EffParts_func_0025c888(smt4::engine::EffPartsSource* manager,
                                 smt4::engine::EffPartsNode* child,
                                 smt4::engine::EffPartsNode* parent);        // 0x0025c888
}

namespace {

using namespace smt4::engine;

u32 AsdAddr(const void* ptr)
{
    return static_cast<u32>(reinterpret_cast<std::uintptr_t>(ptr));
}

void* AsdPtr(u32 value)
{
    return reinterpret_cast<void*>(static_cast<std::uintptr_t>(value));
}

// Explicit field clears emitted by every inline 0x2C particle constructor
// (0x002A5390, 0x002A5490, 0x002A55F4, 0x002A57A8 and 0x002A5864).  +0x00 is
// written separately because the record variants restore `[source]` after the
// 0xDC default.
void ClearParticleFields(EffPartsParticle* particle)
{
    particle->type = 0;
    particle->instance = nullptr;
    particle->field_0c = 0;
    particle->data_0 = 0;
    particle->size_0 = 0;
    particle->alloc_0 = nullptr;
    particle->field_1c = 0;
    particle->data_1 = 0;
    particle->size_1 = 0;
    particle->alloc_1 = nullptr;
    particle->field_00 = 0xDC;
}

EffPartsParticle* AllocParticle()
{
    return reinterpret_cast<EffPartsParticle*>(
        AsdWork_Alloc(0x10000, 0x100, 0, 0x2C, 0x10, 1));
}

// Walk `count` links from `node`; the listing decrements *before* advancing so
// index 0 returns `node` itself (0x002A5344..0x002A5354, 0x002A55A8..0x002A55B8,
// 0x002A1E1A30..0x002A1E1A40 and 0x002A1E1B38..0x002A1E1B48).
EffPartsNode* NthNode(EffPartsNode* node, u32 index)
{
    if (node == nullptr)
        return nullptr;

    for (;;) {
        if (index == 0)
            break;
        --index;
        node = node->next;
        if (node == nullptr)
            break;
    }
    return node;
}

// Resolve a particle's +0x10 word: an absolute address when +0x18 is set,
// otherwise an offset from the record itself (0x0028C9B0..0x0028CA14).
const u8* ResolveData0(const EffPartsParticle* source)
{
    if (source->alloc_0 != nullptr)
        return reinterpret_cast<const u8*>(AsdPtr(source->data_0));
    if (source->data_0 != 0)
        return reinterpret_cast<const u8*>(source) + source->data_0;
    return nullptr;
}

const u8* ResolveData1(const EffPartsParticle* source)
{
    if (source->alloc_1 != nullptr)
        return reinterpret_cast<const u8*>(AsdPtr(source->data_1));
    if (source->data_1 != 0)
        return reinterpret_cast<const u8*>(source) + source->data_1;
    return nullptr;
}

} // namespace

namespace smt4::engine {

// ===========================================================================
// effParts.cpp (c:\SMT4\XRD686\AsdSDK\Source\Gfx\Effect\effParts.cpp)
// ===========================================================================

// ---------------------------------------------------------------------------
// 0x002A51DC -- copy a manager (or loaded header) into a live part object.
//
// Linked mode (+0x8C non-null, 0x002A5268) walks the source's 0xC0-byte nodes
// and clones each one; the +0x98 bit-1 nodes first remap the source list onto
// the destination list, while all other nodes carry a direct particle pointer
// at +0x90.  Array mode (0x002A5508) walks `count` 0xC0-byte records at
// `source + record_offset`, where +0x90 is an index (bit 1) or a relative
// particle offset, and record bit 2 redirects buffer 1 from another record.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002a51dc, 1808)
EffPartsSource* effParts_func_002a51dc(EffPartsSource* source)
{
    AsdEffect_LockEnter(3);                                     // 0x002a51f0

    EffPartsSource* self = reinterpret_cast<EffPartsSource*>(
        AsdWork_Alloc(0x10000, 0x100, 0, 0x90, 0x10, 1));       // 0x002a5220
    AsdMem_Zero(self, 0x90);                                    // 0x002a522c
    self->count = 0;                                            // 0x002a5234
    self->field_84 = 0;                                         // 0x002a5238
    AsdDrawDesc_Init(self);                                     // 0x002a5240

    self->field_00 = source->field_00;                          // 0x002a5244/0x002a524c
    self->field_10 = source->field_00;                          // 0x002a5250/0x002a5254
    self->field_74 = source->field_74;                          // 0x002a5258
    self->field_68 = source->field_68;                          // 0x002a5260

    EffPartsNode* node = source->first;                         // 0x002a5268
    if (node != nullptr) {
        do {
            EffPartsNode* child = reinterpret_cast<EffPartsNode*>(
                AsdWork_Alloc(0x10000, 0x100, 0, 0xC0, 0x10, 1)); // 0x002a52a0
            AsdMem_Zero(child, 0xC0);                           // 0x002a52ac
            AsdMem_Zero(child, 0x90);                           // 0x002a52b8
            child->field_84 = 1;                                // 0x002a52c0
            child->field_88 = 8;                                // 0x002a52c4
            child->field_89 = 0;                                // 0x002a52c8
            child->field_8a = 0;                                // 0x002a52d0
            AsdDrawDesc_Init(child);                            // 0x002a52d4

            if ((node->flags & 1) != 0) {
                // 0x002A52E4..0x002A5330: index of `node` in the source list,
                // matched by particle identity.
                EffPartsNode* match = source->first;
                if (match != nullptr) {
                    while (match->target.particle != node->target.particle) {
                        match = match->next;
                        if (match == nullptr)
                            break;
                    }
                }

                u32 index = 0;
                if (source->first != nullptr) {
                    EffPartsNode* cursor = source->first;
                    while (cursor != match) {                   // 0x002a531c
                        cursor = cursor->next;
                        ++index;
                        if (cursor == nullptr) {                // 0x002a5330
                            index = 0;
                            break;
                        }
                    }
                }

                // 0x002A5338..0x002A535C: same index in the destination list.
                EffPartsNode* origin = self->first;
                origin = NthNode(origin, index);
                EffPartsParticle* template_particle = origin->target.particle; // 0x002a535c

                EffPartsParticle* particle = AllocParticle();   // 0x002a538c
                ClearParticleFields(particle);                  // 0x002a5390..0x002a53b8
                particle->type = template_particle->type;       // 0x002a53c8
                particle->field_0c = template_particle->field_0c; // 0x002a53d0
                particle->field_1c = template_particle->field_1c; // 0x002a53d8
                EffPartsTypeEntry* entry =
                    &g_EffPartsTypeTable[particle->type];       // 0x002a53e4
                particle->instance = entry->create_instance(
                    template_particle->instance);               // 0x002a53f0/0x002a53f4
                child->target.particle = particle;              // 0x002a53fc
            } else {
                // 0x002A545C: direct particle pointer stored in the source node.
                EffPartsParticle* template_particle = node->target.particle;

                EffPartsParticle* particle = AllocParticle();   // 0x002a548c
                ClearParticleFields(particle);                  // 0x002a5490..0x002a54b8
                particle->type = template_particle->type;       // 0x002a54c8
                particle->field_00 = template_particle->field_00; // 0x002a54d0
                particle->field_0c = template_particle->field_0c; // 0x002a54d8
                particle->field_1c = template_particle->field_1c; // 0x002a54e0
                EffPartsTypeEntry* entry =
                    &g_EffPartsTypeTable[particle->type];       // 0x002a54e8
                particle->instance = entry->create_record(
                    template_particle);                         // 0x002a54f8
                child->target.particle = particle;              // 0x002a5500
            }

            // 0x002A5400: copy the 0x90-byte node prefix and the name.
            AsdMem_CopyLarge(child, node, 0x90);                // 0x002a540c
            AsdString_Strcpy(child->name, node->name);          // 0x002a5418
            child->next = nullptr;                              // 0x002a541c

            if (self->children.last != nullptr) {               // 0x002a5420
                self->children.last->next = child;              // 0x002a5428
                child->prev = self->children.last;              // 0x002a5430
            } else {
                self->first = child;                            // 0x002a5434
                child->prev = nullptr;                          // 0x002a5438
            }
            self->children.last = child;                        // 0x002a543c
            self->count = self->count + 1;                      // 0x002a5448

            node = node->next;                                  // 0x002a544c
        } while (node != nullptr);
    } else {
        const u32 remaining = source->count;                    // 0x002a5508
        EffPartsNode* record = reinterpret_cast<EffPartsNode*>(
            reinterpret_cast<u8*>(source) + source->children.record_offset); // 0x002a5518
        EffPartsNode* const array_base = record;                // [sp+0x38] at 0x002a5524
        u32 index = 0;

        if (remaining > 0) {                                    // 0x002a5528
            do {
                EffPartsNode* child = reinterpret_cast<EffPartsNode*>(
                    AsdWork_Alloc(0x10000, 0x100, 0, 0xC0, 0x10, 1)); // 0x002a5554
                AsdMem_Zero(child, 0xC0);                       // 0x002a5560
                AsdMem_Zero(child, 0x90);                       // 0x002a556c
                child->field_84 = 1;                            // 0x002a5574
                child->field_88 = 8;                            // 0x002a5578
                child->field_89 = 0;                            // 0x002a557c
                child->field_8a = 0;                            // 0x002a5584
                AsdDrawDesc_Init(child);                        // 0x002a5588

                if ((record->flags & 1) != 0) {
                    // 0x002A5598..0x002A55C4: +0x90 is a source-list index.
                    EffPartsNode* origin = self->first;
                    origin = NthNode(origin, record->target.link);
                    EffPartsParticle* template_particle = origin->target.particle;

                    EffPartsParticle* particle = AllocParticle(); // 0x002a55f0
                    ClearParticleFields(particle);              // 0x002a55f4..0x002a561c
                    particle->type = template_particle->type;   // 0x002a5624
                    particle->field_0c = template_particle->field_0c; // 0x002a562c
                    particle->field_1c = template_particle->field_1c; // 0x002a563c
                    EffPartsTypeEntry* entry =
                        &g_EffPartsTypeTable[particle->type];   // 0x002a5644
                    particle->instance = entry->create_instance(
                        template_particle->instance);           // 0x002a5650/0x002a5654
                    child->target.particle = particle;          // 0x002a565c
                } else {
                    // 0x002A5728: +0x90 is an offset from the header base.
                    EffPartsParticle* template_particle =
                        reinterpret_cast<EffPartsParticle*>(
                            reinterpret_cast<u8*>(source) + record->target.link);

                    if ((record->flags & 2) != 0) {             // 0x002a572c
                        // 0x002A5738..0x002A5768: buffer 1 of the record at
                        // +0x94 supplies the data; the copied size is +0x24.
                        EffPartsNode* other_record =
                            reinterpret_cast<EffPartsNode*>(
                                reinterpret_cast<u8*>(array_base) +
                                record->field_94 * 0xC0);       // 0x002a5744
                        EffPartsParticle* other =
                            reinterpret_cast<EffPartsParticle*>(
                                reinterpret_cast<u8*>(source) +
                                other_record->target.link);     // 0x002a574c

                        template_particle->size_1 = other->size_1; // 0x002a5754
                        u32 data_address;
                        if (other->alloc_1 != nullptr) {        // 0x002a5760
                            data_address = other->data_1;
                        } else {
                            data_address = other->data_1 != 0
                                ? AsdAddr(other) + other->data_1 // 0x002a5828
                                : 0;                            // 0x002a582c
                        }
                        template_particle->data_1 =
                            data_address - AsdAddr(template_particle); // 0x002a5768

                        EffPartsParticle* particle = AllocParticle(); // 0x002a579c
                        ClearParticleFields(particle);          // 0x002a57a8..0x002a57d0
                        particle->type = template_particle->type; // 0x002a57d4
                        particle->field_00 = template_particle->field_00; // 0x002a57e0
                        particle->field_0c = template_particle->field_0c; // 0x002a57e8
                        particle->field_1c = template_particle->field_1c; // 0x002a57f0
                        EffPartsTypeEntry* entry =
                            &g_EffPartsTypeTable[particle->type]; // 0x002a57f8
                        particle->instance = entry->create_record(
                            template_particle);                 // 0x002a5808
                        child->target.particle = particle;      // 0x002a5810

                        template_particle->size_1 = 0;          // 0x002a5814
                        template_particle->data_1 = 0;          // 0x002a5818
                    } else {
                        // 0x002A5834: plain relative particle record.
                        EffPartsParticle* particle = AllocParticle(); // 0x002a5860
                        ClearParticleFields(particle);          // 0x002a5864..0x002a588c
                        particle->type = template_particle->type; // 0x002a5894
                        particle->field_00 = template_particle->field_00; // 0x002a58a0
                        particle->field_0c = template_particle->field_0c; // 0x002a58a8
                        particle->field_1c = template_particle->field_1c; // 0x002a58b0
                        EffPartsTypeEntry* entry =
                            &g_EffPartsTypeTable[particle->type]; // 0x002a58b8
                        particle->instance = entry->create_record(
                            template_particle);                 // 0x002a58c8
                        child->target.particle = particle;      // 0x002a58d0
                    }
                }

                // 0x002A5660: copy the node prefix and name, then append.
                AsdMem_CopyLarge(child, record, 0x90);          // 0x002a566c
                AsdString_Strcpy(child->name, record->name);    // 0x002a5678
                child->next = nullptr;                          // 0x002a567c

                if (self->children.last != nullptr) {           // 0x002a568c
                    self->children.last->next = child;          // 0x002a5690
                    child->prev = self->children.last;          // 0x002a5698
                } else {
                    self->first = child;                        // 0x002a569c
                    child->prev = nullptr;                      // 0x002a56a0
                }
                self->count = self->count + 1;                  // 0x002a56ac
                self->children.last = child;                    // 0x002a56b0

                ++index;                                        // 0x002a5684
                record = reinterpret_cast<EffPartsNode*>(
                    reinterpret_cast<u8*>(record) + 0xC0);      // 0x002a5688
            } while (index < remaining);                        // 0x002a56bc
        }
    }

    // 0x002A56C0..0x002A5708: {0,0,0,1.0f} setup, uniform scale 1.0 and the
    // white (0xFFFFFFFF) tint.
    EffPartsVec4 value;
    value.value[0] = 0.0f;
    value.value[1] = 0.0f;
    value.value[2] = 0.0f;
    value.value[3] = 1.0f;                                      // 0x002a56d8
    AsdPart_Setup2(self, &value);                               // 0x002a56e4
    AsdPart_Setup1(self, &value);                               // 0x002a56f0
    AsdPart_SetScale(self, 1.0f);                               // 0x002a56fc
    AsdPart_SetValue(self, reinterpret_cast<void*>(
        static_cast<std::uintptr_t>(0xFFFFFFFFu)));             // 0x002a5708
    AsdEffect_LockLeave();                                      // 0x002a5714
    return self;
}

// ---------------------------------------------------------------------------
// 0x002490E0 -- linked-list-only copy of a manager.
//
// Every source node carries an absolute particle pointer at +0x90 and every
// clone is built with the +0x14 table hook (0x002A491D0..0x002A4925C).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002490e0, 580)
EffPartsSource* effParts_func_002490e0(EffPartsSource* source)
{
    EffPartsSource* self = reinterpret_cast<EffPartsSource*>(
        AsdWork_Alloc(0x10000, 0x100, 0, 0x90, 0x10, 1));       // 0x00249118
    AsdMem_Zero(self, 0x90);                                    // 0x00249124
    self->count = 0;                                            // 0x0024912c
    self->field_84 = 0;                                         // 0x00249134
    AsdDrawDesc_Init(self);                                     // 0x00249138

    self->field_00 = source->field_00;                          // 0x0024913c/0x00249144
    self->field_10 = source->field_10;                          // 0x00249148/0x00249150
    self->field_74 = source->field_74;                          // 0x00249154
    self->field_68 = source->field_68;                          // 0x0024915c

    EffPartsNode* node = source->first;                         // 0x00249164
    if (node != nullptr) {
        do {
            EffPartsNode* child = reinterpret_cast<EffPartsNode*>(
                AsdWork_Alloc(0x10000, 0x100, 0, 0xC0, 0x10, 1)); // 0x00249194
            AsdMem_Zero(child, 0xC0);                           // 0x002491a0
            AsdMem_Zero(child, 0x90);                           // 0x002491ac
            child->field_84 = 1;                                // 0x002491b4
            child->field_88 = 8;                                // 0x002491b8
            child->field_89 = 0;                                // 0x002491bc
            child->field_8a = 0;                                // 0x002491c4
            AsdDrawDesc_Init(child);                            // 0x002491c8

            EffPartsParticle* template_particle = node->target.particle; // 0x002491d0
            EffPartsParticle* particle = AllocParticle();       // 0x002491f8
            ClearParticleFields(particle);                      // 0x002491fc..0x00249228
            particle->type = template_particle->type;           // 0x0024922c
            particle->field_0c = template_particle->field_0c;   // 0x00249238
            particle->field_1c = template_particle->field_1c;   // 0x00249240
            EffPartsTypeEntry* entry =
                &g_EffPartsTypeTable[particle->type];           // 0x0024924c
            particle->instance = entry->create_instance(
                template_particle->instance);                   // 0x0024925c
            child->target.particle = particle;                  // 0x00249270

            AsdMem_CopyLarge(child, node, 0x90);                // 0x00249274
            child->next = nullptr;                              // 0x00249278

            if (self->children.last != nullptr) {               // 0x0024927c
                self->children.last->next = child;              // 0x00249288
                child->prev = self->children.last;              // 0x0024928c
            } else {
                self->first = child;                            // 0x00249294
                child->prev = nullptr;                          // 0x00249298
            }
            self->children.last = child;                        // 0x0024929c
            self->count = self->count + 1;                      // 0x002492a8

            node = node->next;                                  // 0x002492ac
        } while (node != nullptr);
    }

    // 0x002A492B8..0x002A492FC.
    EffPartsVec4 value;
    value.value[0] = 0.0f;
    value.value[1] = 0.0f;
    value.value[2] = 0.0f;
    value.value[3] = 1.0f;                                      // 0x002a492cc
    AsdPart_Setup2(self, &value);                               // 0x002a492d8
    AsdPart_Setup1(self, &value);                               // 0x002a492e4
    AsdPart_SetScale(self, 1.0f);                               // 0x002a492f0
    AsdPart_SetValue(self, reinterpret_cast<void*>(
        static_cast<std::uintptr_t>(0xFFFFFFFFu)));             // 0x002a492fc
    return self;
}

// ---------------------------------------------------------------------------
// 0x0024972C -- replace buffer 0 (+0x10/+0x14/+0x18, key +0x0C).
//
// Frees the old allocation, clears the triple, then allocates `size` bytes and
// copies `data`; a null source or non-positive size leaves the cleared triple.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0024972c, 164)
void effParts_func_0024972c(EffPartsParticle* part, const void* data,
                            s32 size, u16 key)
{
    if (part->alloc_0 != nullptr) {                             // 0x00249744
        AsdMem_Free(part->alloc_0);                             // 0x00249750
        part->data_0 = 0;                                       // 0x00249758
        part->size_0 = 0;                                       // 0x0024975c
        part->alloc_0 = nullptr;                                // 0x00249760
    }

    if (data == nullptr || size <= 0)                           // 0x00249764..0x0024976C
        return;

    void* buffer = AsdWork_Alloc(0x10000, 0x100, 0, static_cast<u32>(size),
                                 0x10, 1);                      // 0x00249798
    part->field_0c = key;                                       // 0x0024979c
    part->alloc_0 = buffer;                                     // 0x002497a0
    part->data_0 = AsdAddr(buffer);                             // 0x002497ac
    part->size_0 = static_cast<u32>(size);                      // 0x002497ac
    AsdMem_Copy(buffer, data, static_cast<u32>(size));          // 0x002497bc
}

// ---------------------------------------------------------------------------
// 0x0024FDA4 -- clone a particle through the +0x14 table hook.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0024fda4, 192)
EffPartsParticle* effParts_func_0024fda4(EffPartsParticle* source)
{
    u16 type = source->type;                                    // 0x0024fdac
    EffPartsParticle* particle = AllocParticle();               // 0x0024fddc
    ClearParticleFields(particle);                              // 0x0024fde4..0x0024fe10
    particle->type = type;                                      // 0x0024fe14
    particle->field_0c = source->field_0c;                      // 0x0024fe20
    particle->field_1c = source->field_1c;                      // 0x0024fe28
    EffPartsTypeEntry* entry = &g_EffPartsTypeTable[particle->type]; // 0x0024fe34
    particle->instance = entry->create_instance(source->instance); // 0x0024fe44
    return particle;
}

// ---------------------------------------------------------------------------
// 0x0024FE64 -- clone a particle through the +0x00 table hook.
// Unlike 0x0024FDA4 this also copies +0x00 from the record.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0024fe64, 196)
EffPartsParticle* effParts_func_0024fe64(EffPartsParticle* source)
{
    u16 type = source->type;                                    // 0x0024fe6c
    EffPartsParticle* particle = AllocParticle();               // 0x0024fe9c
    ClearParticleFields(particle);                              // 0x0024fea4..0x0024fed0
    particle->type = type;                                      // 0x0024fed4
    particle->field_00 = source->field_00;                      // 0x0024fee0
    particle->field_0c = source->field_0c;                      // 0x0024fee8
    particle->field_1c = source->field_1c;                      // 0x0024fef0
    EffPartsTypeEntry* entry = &g_EffPartsTypeTable[particle->type]; // 0x0024fefc
    particle->instance = entry->create_record(source);          // 0x0024ff08
    return particle;
}

// ---------------------------------------------------------------------------
// 0x0025CAA8 -- allocate and initialise one child node.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0025caa8, 128)
EffPartsNode* effParts_func_0025caa8()
{
    EffPartsNode* node = reinterpret_cast<EffPartsNode*>(
        AsdWork_Alloc(0x10000, 0x100, 0, 0xC0, 0x10, 1));       // 0x0025cad8
    AsdMem_Zero(node, 0xC0);                                    // 0x0025cae4
    AsdMem_Zero(node, 0x90);                                    // 0x0025caf0
    node->field_84 = 1;                                         // 0x0025caf8
    node->field_88 = 8;                                         // 0x0025cb00
    node->field_89 = 0;                                         // 0x0025cb04
    node->field_8a = 0;                                         // 0x0025cb08
    AsdDrawDesc_Init(node);                                     // 0x0025cb10
    return node;
}

// ---------------------------------------------------------------------------
// 0x0025CC14 -- replace buffer 1 (+0x20/+0x24/+0x28, key +0x1C).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0025cc14, 164)
void effParts_func_0025cc14(EffPartsParticle* part, const void* data,
                            s32 size, u16 key)
{
    if (part->alloc_1 != nullptr) {                             // 0x0025cc2c
        AsdMem_Free(part->alloc_1);                             // 0x0025cc38
        part->data_1 = 0;                                       // 0x0025cc40
        part->size_1 = 0;                                       // 0x0025cc44
        part->alloc_1 = nullptr;                                // 0x0025cc48
    }

    if (data == nullptr || size <= 0)                           // 0x0025cc4c..0x0025cc54
        return;

    void* buffer = AsdWork_Alloc(0x10000, 0x100, 0, static_cast<u32>(size),
                                 0x10, 1);                      // 0x0025cc80
    part->field_1c = key;                                       // 0x0025cc84
    part->alloc_1 = buffer;                                     // 0x0025cc88
    part->data_1 = AsdAddr(buffer);                             // 0x0025cc94
    part->size_1 = static_cast<u32>(size);                      // 0x0025cc94
    AsdMem_Copy(buffer, data, static_cast<u32>(size));          // 0x0025cca4
}

// ---------------------------------------------------------------------------
// 0x0028C920 -- deep copy of one particle record.
//
// Buffer 0 is re-allocated when (resolved source != 0 && size +0x14 > 0) and
// buffer 1 goes through 0x0025CC14; +0x0C/+0x1C keys are copied.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0028c920, 348)
EffPartsParticle* effParts_func_0028c920(EffPartsParticle* source)
{
    EffPartsParticle* particle = AllocParticle();               // 0x0028c95c
    ClearParticleFields(particle);                              // 0x0028c964..0x0028c990
    particle->type = source->type;                              // 0x0028c994
    particle->field_00 = source->field_00;                      // 0x0028c9a0

    const u32 size_0 = source->size_0;                          // 0x0028c9a4
    if (size_0 != 0) {
        const u8* data = ResolveData0(source);                  // 0x0028c9b0..0x0028c9bc
        if (data != nullptr && static_cast<s32>(size_0) > 0) {  // 0x0028c9c4..0x0028c9cc
            void* buffer = AsdWork_Alloc(0x10000, 0x100, 0, size_0,
                                         0x10, 1);              // 0x0028c9f4
            particle->field_0c = source->field_0c;              // 0x0028c9fc
            particle->alloc_0 = buffer;                         // 0x0028ca00
            particle->data_0 = AsdAddr(buffer);                 // 0x0028ca04
            particle->size_0 = size_0;                          // 0x0028ca04
            AsdMem_Copy(buffer, data, size_0);                  // 0x0028ca14
        }
    }

    if (source->size_1 != 0) {                                  // 0x0028ca18
        effParts_func_0025cc14(particle, ResolveData1(source),
                               static_cast<s32>(source->size_1),
                               source->field_1c);               // 0x0028ca34
    }
    return particle;
}

// ---------------------------------------------------------------------------
// 0x00192168 -- allocate one empty particle and store the 16-bit type id.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00192168, 124)
EffPartsParticle* effParts_func_00192168(u32 id)
{
    EffPartsParticle* particle = AllocParticle();               // 0x0019219c
    ClearParticleFields(particle);                              // 0x001921a4..0x001921d0
    particle->type = static_cast<u16>(id);                      // 0x001921d4
    return particle;
}

// ---------------------------------------------------------------------------
// 0x001D2460 -- create an empty parts manager.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001d2460, 104)
EffPartsSource* effParts_func_001d2460()
{
    EffPartsSource* manager = reinterpret_cast<EffPartsSource*>(
        AsdWork_Alloc(0x10000, 0x100, 0, 0x90, 0x10, 1));       // 0x001d2490
    AsdMem_Zero(manager, 0x90);                                 // 0x001d249c
    manager->count = 0;                                         // 0x001d24a4
    manager->field_84 = 0;                                      // 0x001d24ac
    AsdDrawDesc_Init(manager);                                  // 0x001d24b0
    return manager;
}

// ---------------------------------------------------------------------------
// 0x001E1970 -- load an effParts file and materialise every 0xC0 record.
//
// `AsdFile_LoadSync(path, &size, 1, 0x80)` returns the 0x90-byte header.
// Records start at `header + header->+0x88`; bit-1 records clone the manager
// node at index +0x90 and splice the clone after it, bit-2 records call the
// 0x0025C888 re-parent helper, and the record's 0x90-byte prefix + name are
// copied into the new node last.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001e1970, 576)
EffPartsSource* effParts_func_001e1970(const char* path)
{
    u32 size = 0;
    EffPartsSource* header = reinterpret_cast<EffPartsSource*>(
        AsdFile_LoadSync(path, &size, 1, 0x80));                // 0x001e1984

    EffPartsSource* manager = reinterpret_cast<EffPartsSource*>(
        AsdWork_Alloc(0x10000, 0x100, 0, 0x90, 0x10, 1));       // 0x001e19b4
    AsdMem_Zero(manager, 0x90);                                 // 0x001e19c0
    manager->count = 0;                                         // 0x001e19c8
    manager->field_84 = 0;                                      // 0x001e19d0
    AsdDrawDesc_Init(manager);                                  // 0x001e19d4

    manager->field_00 = header->field_00;                       // 0x001e19d8/0x001e19e4
    manager->field_10 = header->field_00;                       // 0x001e19e8/0x001e19ec
    manager->field_74 = header->field_74;                       // 0x001e19f0
    manager->field_68 = header->field_68;                       // 0x001e19f8
    const u32 remaining = header->count;                        // 0x001e1a00
    EffPartsNode* record = reinterpret_cast<EffPartsNode*>(
        reinterpret_cast<u8*>(header) + header->children.record_offset); // 0x001e1a04/0x001e1a0c

    u32 index = 0;
    if (remaining != 0) {                                       // 0x001e1a10
        do {
            EffPartsNode* child;
            if ((record->flags & 1) != 0) {
                // 0x001E1A24..0x001E1A48: clone the live node at +0x90 and
                // splice it directly after that node.
                EffPartsNode* template_node =
                    NthNode(manager->first, record->target.link);
                child = effParts_func_0025caa8();               // 0x001e1a4c
                AsdMem_CopyLarge(child, template_node, 0xC0);   // 0x001e1a5c
                AsdMem_Zero(child, 0x90);                       // 0x001e1a68
                child->field_84 = 1;                            // 0x001e1a70
                child->field_88 = 8;                            // 0x001e1a74
                child->field_89 = 0;                            // 0x001e1a78
                child->field_8a = 0;                            // 0x001e1a80
                AsdDrawDesc_Init(child);                        // 0x001e1a84
                child->flags = child->flags | 1;                // 0x001e1a90
                child->target.particle = template_node->target.particle; // 0x001e1a98

                EffPartsNode* next = template_node->next;       // 0x001e1a9c
                if (next != nullptr) {
                    next->prev = child;                         // 0x001e1aa4
                    child->next = next;                         // 0x001e1aac
                } else {
                    child->next = nullptr;                      // 0x001e1ab0
                    manager->children.last = child;             // 0x001e1ab4
                }
                template_node->next = child;                    // 0x001e1ab8
                child->prev = template_node;                    // 0x001e1abc
                manager->count = manager->count + 1;            // 0x001e1ac8
            } else {
                // 0x001E1AD0: +0x90 is a relative particle offset.
                EffPartsParticle* particle = effParts_func_0028c920(
                    reinterpret_cast<EffPartsParticle*>(
                        reinterpret_cast<u8*>(header) + record->target.link));
                child = effParts_func_0025caa8();               // 0x001e1ae0
                child->target.particle = particle;              // 0x001e1ae4
                child->next = nullptr;                          // 0x001e1ae8

                if (manager->children.last != nullptr) {        // 0x001e1af4
                    manager->children.last->next = child;       // 0x001e1af8
                    child->prev = manager->children.last;       // 0x001e1b00
                } else {
                    manager->first = child;                     // 0x001e1b04
                    child->prev = nullptr;                      // 0x001e1b08
                }
                manager->children.last = child;                 // 0x001e1b10
                manager->count = manager->count + 1;            // 0x001e1b18
            }

            // 0x001E1B1C: records with bit 2 are re-parented onto the node at
            // +0x94 through the 0x0025C888 helper.
            if ((record->flags & 2) != 0) {
                EffPartsNode* parent = NthNode(manager->first,
                                               record->field_94);
                EffParts_func_0025c888(manager, child, parent);  // 0x001e1b58
            }

            AsdMem_CopyLarge(child, record, 0x90);              // 0x001e1b68
            AsdString_Strcpy(child->name, record->name);        // 0x001e1b74
            child->flags = record->flags;                       // 0x001e1b84

            ++index;                                            // 0x001e1b7c
            record = reinterpret_cast<EffPartsNode*>(
                reinterpret_cast<u8*>(record) + 0xC0);          // 0x001e1b80
        } while (index < remaining);                            // 0x001e1b90
    }

    AsdMem_Free(header);                                        // 0x001e1b98
    return manager;
}

// ===========================================================================
// effP2A.cpp (c:\SMT4\XRD686\AsdSDK\Source\Gfx\Effect\effP2A.cpp)
// ===========================================================================

// ---------------------------------------------------------------------------
// 0x00249324 -- build the P2A texture set and its animation wrapper.
//
// Header: +0x00 header_size, +0x04 entry_count, +0x08 first 0x14-byte entry.
// At `file + header_size`: a u32 texture count followed by that many u32
// offsets; each offset names an "STEX" or plain texture record.
//
// Mode starts at 1 (0x00249418).  For each 0x14-byte entry:
//   flags +0x10 & 0x10000000 -> mode = entry[+0x0C]
//   else +0x08 & (0x40|0x80) -> mode = 2
// The wrapper is 0x18 + mode*0x14 bytes and binds entry 0 via 0x001D21A0.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00249324, 484)
EffP2AAnim* effP2A_func_00249324(const void* file)
{
    EffP2AObject* object = nullptr;

    if (file != nullptr) {                                      // 0x00249328
        const u8* base = reinterpret_cast<const u8*>(file);
        const u32 header_size = *reinterpret_cast<const u32*>(base); // 0x00249340
        const u8* texture_offsets = base + header_size;         // 0x0024934C
        const u32 texture_count =
            *reinterpret_cast<const u32*>(texture_offsets);     // 0x00249350
        texture_offsets += 4;                                   // pre-index writeback

        const u32 alloc_size = header_size + 0x1C + texture_count * 4; // 0x00249354
        object = reinterpret_cast<EffP2AObject*>(
            AsdWork_Alloc(0x10000, 0x100, 0, alloc_size, 0x10, 1)); // 0x00249380

        object->self = object;                                  // 0x0024938c
        AsdMem_Copy(reinterpret_cast<u8*>(object) + 0x1C, base,
                    header_size);                               // 0x00249398
        object->texture_count = texture_count;                  // 0x002493a4
        object->header = reinterpret_cast<u8*>(object) + 0x1C;  // 0x002493a8
        object->entries = reinterpret_cast<u8*>(object) + 0x24; // 0x002493a8
        object->textures = reinterpret_cast<void**>(
            reinterpret_cast<u8*>(object) + 0x1C + header_size + 8); // 0x002493bc

        for (u32 i = 0; i < texture_count; ++i) {               // 0x002493c4
            const u8* source = base +
                *reinterpret_cast<const u32*>(texture_offsets + i * 4); // 0x002493c8
            object->textures[i] = AsdEffect_IsStex(source)       // 0x002493d4
                ? AsdEffectTexture_func_0028cabc(source)        // 0x002493e4
                : EffParts_CreateTexture(source);               // 0x002493f8
        }

        object->field_10 = 1;                                   // 0x00249414
        object->mode = 1;                                       // 0x00249418

        const u32 entry_count = *reinterpret_cast<const u32*>(
            reinterpret_cast<const u8*>(object->header) + 4);   // 0x00249424
        for (u32 i = 0; i < entry_count; ++i) {                 // 0x00249438
            const EffP2AEntry* entry = reinterpret_cast<const EffP2AEntry*>(
                reinterpret_cast<const u8*>(object->entries) + i * 0x14);
            if ((entry->field_10 & 0x10000000u) != 0) {         // 0x00249444
                object->mode = entry->field_0c;                 // 0x0024944c
            } else if ((entry->field_08 & 0x40u) != 0 ||
                       (entry->field_08 & 0x80u) != 0) {        // 0x002494c4
                object->mode = 2;                               // 0x002494cc
            }
        }
    }

    // 0x00249460: the caller guarantees a non-null resource; the listing reads
    // [object+8] here and then sizes the wrapper from it.
    const u32 mode = object->mode;
    const u32 alloc_size = 0x18 + mode * 0x14;                  // 0x00249468
    EffP2AAnim* anim = reinterpret_cast<EffP2AAnim*>(
        AsdWork_Alloc(0x10000, 0x100, 0, alloc_size, 0x10, 1)); // 0x00249494
    anim->entries = reinterpret_cast<u8*>(anim) + 0x18;         // 0x0024949c
    anim->object = object;                                      // 0x002494a8
    EffP2A_BindEntry(anim, 0);                                  // 0x002494ac
    anim->count = 1;                                            // 0x002494b0
    return anim;
}

// ===========================================================================
// effTLP.cpp (c:\SMT4\XRD686\AsdSDK\Source\Gfx\Effect\effTLP.cpp)
// ===========================================================================

// ---------------------------------------------------------------------------
// 0x00249588 -- build the TLP vertex/UV table.
//
// Input: +0x00..+0x0C copied to the object, +0x04 record count, then `count`
// 0x10-byte records.  The texture blob starts right after the records and each
// record's +0x04 advances the blob cursor (pre-indexed `ldr r0,[r5,#4]!` at
// 0x0024966C).  The final total is sum(record[+0x00] + 1) over all records
// (odd-first + paired unroll at 0x00249698..0x002496D8).
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00249588, 420)
EffTLPObject* effTLP_func_00249588(const void* resource)
{
    const u8* base = reinterpret_cast<const u8*>(resource);
    const u32 count = *reinterpret_cast<const u32*>(base + 4);  // 0x00249598
    const u32 alloc_size = 0x28 + count * 20;                   // 0x002495A4

    EffTLPObject* object = reinterpret_cast<EffTLPObject*>(
        AsdWork_Alloc(0x10000, 0x100, 0, alloc_size, 0x10, 1)); // 0x002495CC

    object->generation = 0;                                     // 0x002495E4
    object->field_20 = -1;                                      // 0x002495DC
    object->self = object;                                      // 0x002495E4
    object->entries = reinterpret_cast<EffTLPEntry*>(
        reinterpret_cast<u8*>(object) + 0x28);                  // 0x002495F0
    object->textures = reinterpret_cast<void**>(
        reinterpret_cast<u8*>(object) + 0x28 + count * 16);     // 0x002495F0

    object->field_00 = *reinterpret_cast<const u32*>(base + 0x00); // 0x00249608
    object->count = *reinterpret_cast<const u32*>(base + 0x04);    // 0x00249610
    object->field_08 = *reinterpret_cast<const u32*>(base + 0x08); // 0x00249618
    object->field_0c = *reinterpret_cast<const u32*>(base + 0x0C); // 0x00249620

    const u8* record = base + 0x10;
    const u8* texture = record + count * 16;                    // 0x00249604
    for (u32 i = 0; i < count; ++i) {                           // 0x00249624
        EffTLPEntry* entry = reinterpret_cast<EffTLPEntry*>(
            reinterpret_cast<u8*>(object->entries) + i * 0x10);
        *entry = *reinterpret_cast<const EffTLPEntry*>(record);  // 0x0024962C/0x00249634

        object->textures[i] = AsdEffect_IsStex(texture)          // 0x0024963c
            ? AsdEffectTexture_func_0028cabc(texture)           // 0x0024964c
            : EffParts_CreateTexture(texture);                  // 0x00249660

        const u32 step = *reinterpret_cast<const u32*>(record + 4); // 0x0024966c
        record += 0x10;                                         // 0x00249678
        texture += step;                                        // 0x0024967c
    }

    // 0x00249684..0x002496D8: total = sum(field_00 + 1), odd entry first then
    // pairs accumulated in two registers that are added together.
    u32 total = 0;
    if (count != 0) {
        u32 entry_index = 0;
        if ((count & 1) != 0) {
            total = object->entries[0].field_00 + 1;
            entry_index = 1;
        }

        u32 pair_total = 0;
        for (u32 pairs = count >> 1; pairs != 0; --pairs) {
            total += object->entries[entry_index].field_00 + 1;
            pair_total += object->entries[entry_index + 1].field_00 + 1;
            entry_index += 2;
        }
        total += pair_total;
    }

    object->total = total;                                      // 0x002496e0
    object->generation = object->generation + 1;                // 0x002496e8
    return object;
}

} // namespace smt4::engine
