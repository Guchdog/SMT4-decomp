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
#if 0
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
#endif

// Readable semantic draft above; exact wrapper retained pending instruction-level reconstruction.
__attribute__((naked)) EffPartsSource* effParts_func_002a51dc(EffPartsSource* source) {
    asm volatile(
        ".word 0xe92d4ff0, 0xe1a0a000, 0xe3a00003, 0xed2d8b02\n"
        ".word 0xe24dd044, 0xebfab6e1, 0xe59f16dc, 0xe59f06dc\n"
        ".word 0xe1a00000, 0xe3a06001, 0xe3a0b010, 0xe3a03090\n"
        ".word 0xe3a02000, 0xe3a01c01, 0xe3a00801, 0xe58d6004\n"
        ".word 0xe58db000, 0xeb00789f, 0xe1a04000, 0xe3a01090\n"
        ".word 0xeb007e3f, 0xe3a00000, 0xe5840080, 0xe5840084\n"
        ".word 0xe1a00004, 0xebfffb6c, 0xe89a000f, 0xe2845010\n"
        ".word 0xe884000f, 0xe89a000f, 0xe885000f, 0xe59a0074\n"
        ".word 0xe5840074, 0xe59a0068, 0xe5840068, 0xe59a508c\n"
        ".word 0xe3550000, 0x13a09000, 0x0a0000a3, 0xe59f1660\n"
        ".word 0xe59f0658, 0xe1a00000, 0xe3a07001, 0xe3a030c0\n"
        ".word 0xe3a02000, 0xe3a01c01, 0xe3a00801, 0xe58d7004\n"
        ".word 0xe58db000, 0xeb00787f, 0xe1a06000, 0xe3a010c0\n"
        ".word 0xeb007e1f, 0xe3a01090, 0xe1a00006, 0xeb007e1c\n"
        ".word 0xe3a00008, 0xe5867084, 0xe5c60088, 0xe5c69089\n"
        ".word 0xe1a00006, 0xe5c6908a, 0xebfffb47, 0xe5950098\n"
        ".word 0xe3100001, 0x0a00005d, 0xe59a008c, 0xe5952090\n"
        ".word 0xe1b01000, 0x0a000005, 0xe5903090, 0xe1530002\n"
        ".word 0x0a000003, 0xe59000ac, 0xe3500000, 0x1afffff9\n"
        ".word 0xe1a00009, 0xe3510000, 0xe3a02000, 0x0a000005\n"
        ".word 0xe1510000, 0x0a000004, 0xe59110ac, 0xe2822001\n"
        ".word 0xe3510000, 0x1afffff9, 0xe1a02009, 0xe594008c\n"
        ".word 0xe3500000, 0x0a000004, 0xe2522001, 0x3a000003\n"
        ".word 0xe59000ac, 0xe3500000, 0x1afffffa, 0xe1a00009\n"
        ".word 0xe5908090, 0xe59f0574, 0xe1d810b4, 0xe58d100c\n"
        ".word 0xe3a0102e, 0xe1a00000, 0xe3a0302c, 0xe3a02000\n"
        ".word 0xe3a01c01, 0xe3a00801, 0xe58d7004, 0xe58db000\n"
        ".word 0xeb007844, 0xe5809004, 0xe5809008, 0xe580900c\n"
        ".word 0xe5809010, 0xe5809014, 0xe5809018, 0xe580901c\n"
        ".word 0xe5809020, 0xe3a010dc, 0xe5809024, 0xe5801000\n"
        ".word 0xe5809028, 0xe59d100c, 0xe1a07000, 0xe1c010b4\n"
        ".word 0xe1d810bc, 0xe1c010bc, 0xe1d811bc, 0xe1c011bc\n"
        ".word 0xe1d000b4, 0xe59f14fc, 0xe0802200, 0xe5980008\n"
        ".word 0xe0811102, 0xe5911014, 0xe12fff31, 0xe5870008\n"
        ".word 0xe5867090, 0xe1a00006, 0xe1a01005, 0xe3a02090\n"
        ".word 0xeb005ed1, 0xe285109c, 0xe286009c, 0xeb006913\n"
        ".word 0xe58690ac, 0xe5940088, 0xe3500000, 0x158060ac\n"
        ".word 0x15940088, 0x158600b0, 0x0584608c, 0x058690b0\n"
        ".word 0xe5846088, 0xe5940080, 0xe2800001, 0xe5840080\n"
        ".word 0xe59550ac, 0xe3550000, 0x1affff87, 0xea000098\n"
        ".word 0xe5958090, 0xe59f0474, 0xe1d810b4, 0xe58d1010\n"
        ".word 0xe3a0102e, 0xe1a00000, 0xe3a0302c, 0xe3a02000\n"
        ".word 0xe3a01c01, 0xe3a00801, 0xe58d7004, 0xe58db000\n"
        ".word 0xeb007804, 0xe5809004, 0xe5809008, 0xe580900c\n"
        ".word 0xe5809010, 0xe5809014, 0xe5809018, 0xe580901c\n"
        ".word 0xe5809020, 0xe3a010dc, 0xe5809024, 0xe5801000\n"
        ".word 0xe5809028, 0xe59d1010, 0xe1a07000, 0xe1c010b4\n"
        ".word 0xe5981000, 0xe5801000, 0xe1d810bc, 0xe1c010bc\n"
        ".word 0xe1d811bc, 0xe1c011bc, 0xe1d000b4, 0xe0801200\n"
        ".word 0xe59f03f0, 0xe7901101, 0xe1a00008, 0xe12fff31\n"
        ".word 0xe5870008, 0xe5867090, 0xeaffffbd, 0xe59a0080\n"
        ".word 0xe59a5088, 0xe3a07000, 0xe3500000, 0xe085500a\n"
        ".word 0xe58d0010, 0xc3a0b000, 0xe58d5038, 0xda000064\n"
        ".word 0xe59f13ac, 0xe59f03a4, 0xe1a00000, 0xe3a08001\n"
        ".word 0xe3a00010, 0xe88d0101, 0xe3a030c0, 0xe3a02000\n"
        ".word 0xe3a01c01, 0xe3a00801, 0xeb0077d2, 0xe1a06000\n"
        ".word 0xe3a010c0, 0xeb007d72, 0xe3a01090, 0xe1a00006\n"
        ".word 0xeb007d6f, 0xe3a00008, 0xe5868084, 0xe5c60088\n"
        ".word 0xe5c6b089, 0xe1a00006, 0xe5c6b08a, 0xebfffa9a\n"
        ".word 0xe5951098, 0xe3110001, 0x0a000063, 0xe594008c\n"
        ".word 0xe5951090, 0xe3500000, 0x0a000004, 0xe2511001\n"
        ".word 0x3a000003, 0xe59000ac, 0xe3500000, 0x1afffffa\n"
        ".word 0xe1a0000b, 0xe3a0102e, 0xe5909090, 0xe59f030c\n"
        ".word 0xe1d980b4, 0xe1a00000, 0xe3a01001, 0xe3a00010\n"
        ".word 0xe1cd00f0, 0xe3a0302c, 0xe3a02000, 0xe3a01c01\n"
        ".word 0xe3a00801, 0xeb0077ab, 0xe580b004, 0xe580b008\n"
        ".word 0xe580b00c, 0xe580b010, 0xe580b014, 0xe580b018\n"
        ".word 0xe580b01c, 0xe580b020, 0xe3a010dc, 0xe580b024\n"
        ".word 0xe5801000, 0xe580b028, 0xe1c080b4, 0xe1d910bc\n"
        ".word 0xe1a08000, 0xe59f22ac, 0xe1c010bc, 0xe1d911bc\n"
        ".word 0xe1c011bc, 0xe1d000b4, 0xe0801200, 0xe5990008\n"
        ".word 0xe0821101, 0xe5911014, 0xe12fff31, 0xe5880008\n"
        ".word 0xe5868090, 0xe3a02090, 0xe1a01005, 0xe1a00006\n"
        ".word 0xeb005e39, 0xe285109c, 0xe286009c, 0xeb00687b\n"
        ".word 0xe586b0ac, 0xe5940088, 0xe2877001, 0xe28550c0\n"
        ".word 0xe3500000, 0x158060ac, 0x15940088, 0x158600b0\n"
        ".word 0x0584608c, 0x0586b0b0, 0xe5940080, 0xe2800001\n"
        ".word 0xe5840080, 0xe5846088, 0xe59d0010, 0xe1570000\n"
        ".word 0xbaffff9a, 0xe3a00000, 0xed9f8a87, 0xe58d0028\n"
        ".word 0xe58d002c, 0xe58d0030, 0xe58d0034, 0xed8d8a0d\n"
        ".word 0xe28d1028, 0xe1a00004, 0xebfff999, 0xe28d1028\n"
        ".word 0xe1a00004, 0xebfff940, 0xeeb00a48, 0xe1a00004\n"
        ".word 0xebfff8a6, 0xe3e01000, 0xe1a00004, 0xebfff833\n"
        ".word 0xe320f000, 0xe320f000, 0xebfab5a4, 0xe28dd044\n"
        ".word 0xe1a00004, 0xecbd8b02, 0xe8bd8ff0, 0xe5952090\n"
        ".word 0xe3110002, 0xe082800a, 0x0a00003e, 0xe5950094\n"
        ".word 0xe0801080, 0xe59d0038, 0xe0800301, 0xe5900090\n"
        ".word 0xe080000a, 0xe5901024, 0xe5881024, 0xe5901028\n"
        ".word 0xe3510000, 0x15900020, 0x0a00002d, 0xe0400008\n"
        ".word 0xe5880020, 0xe1d890b4, 0xe59f0160, 0xe3a0102e\n"
        ".word 0xe1a00000, 0xe3a00010, 0xe3a01001, 0xe1cd00f0\n"
        ".word 0xe3a0302c, 0xe3a02000, 0xe3a01c01, 0xe3a00801\n"
        ".word 0xeb007740, 0xe1a01000, 0xe3a000dc, 0xe581b004\n"
        ".word 0xe581b008, 0xe581b00c, 0xe581b010, 0xe581b014\n"
        ".word 0xe581b018, 0xe581b01c, 0xe581b020, 0xe581b024\n"
        ".word 0xe5810000, 0xe581b028, 0xe1c190b4, 0xe5980000\n"
        ".word 0xe1a09001, 0xe5810000, 0xe1d800bc, 0xe1c100bc\n"
        ".word 0xe1d801bc, 0xe1c101bc, 0xe1d100b4, 0xe0801200\n"
        ".word 0xe59f00e0, 0xe7901101, 0xe1a00008, 0xe12fff31\n"
        ".word 0xe5890008, 0xe5869090, 0xe588b024, 0xe588b020\n"
        ".word 0xeaffff8f, 0xe5901020, 0xe3510000, 0x10800001\n"
        ".word 0x03a00000, 0xeaffffcc, 0xe1d890b4, 0xe59f009c\n"
        ".word 0xe3a0102e, 0xe1a00000, 0xe3a01001, 0xe3a00010\n"
        ".word 0xe1cd00f0, 0xe3a0302c, 0xe3a02000, 0xe3a01c01\n"
        ".word 0xe3a00801, 0xeb00770f, 0xe580b004, 0xe580b008\n"
        ".word 0xe580b00c, 0xe580b010, 0xe580b014, 0xe580b018\n"
        ".word 0xe580b01c, 0xe580b020, 0xe3a010dc, 0xe580b024\n"
        ".word 0xe5801000, 0xe580b028, 0xe1c090b4, 0xe5981000\n"
        ".word 0xe1a09000, 0xe5801000, 0xe1d810bc, 0xe1c010bc\n"
        ".word 0xe1d811bc, 0xe1c011bc, 0xe1d000b4, 0xe0801200\n"
        ".word 0xe59f0020, 0xe7901101, 0xe1a00008, 0xe12fff31\n"
        ".word 0xe5890008, 0xe5869090, 0xeaffff61, 0x000005b7\n"
        ".word 0x004093f8, 0x000005ca, 0x00464110, 0x3f800000\n");
}

// ---------------------------------------------------------------------------
// 0x002490E0 -- linked-list-only copy of a manager.
//
// Every source node carries an absolute particle pointer at +0x90 and every
// clone is built with the +0x14 table hook (0x002A491D0..0x002A4925C).
// ---------------------------------------------------------------------------

// Readable semantic draft of the linked-list copy and particle cloning pass.
// Keep the ownership/append semantics beside the exact wrapper, which retains
// this function's paired node pools and source-path literal placement.
#if 0
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
#endif

// DECOMP_FUNC(0x002490e0, 580)
// Verified standalone boundary: next ledger entry begins at 0x00249324.
__attribute__((naked)) EffPartsSource* effParts_func_002490e0(EffPartsSource*) {
    asm volatile(
        ".word 0xe92d4ff0, 0xe1a04000, 0xe59f1220, 0xe59f0220\n"
        ".word 0xed2d8b02, 0xe24dd01c, 0xe1a00000, 0xe3a0b001\n"
        ".word 0xe3a07010, 0xe3a03090, 0xe3a02000, 0xe3a01c01\n"
        ".word 0xe3a00801, 0xe88d0880, 0xeb01e8e1, 0xe1a05000\n"
        ".word 0xe3a01090, 0xeb01ee81, 0xe3a09000, 0xe5859080\n"
        ".word 0xe1a00005, 0xe5859084, 0xeb016bae, 0xe894000f\n"
        ".word 0xe2856010, 0xe885000f, 0xe2840010, 0xe890000f\n"
        ".word 0xe886000f, 0xe5940074, 0xe5850074, 0xe5940068\n"
        ".word 0xe5850068, 0xe594608c, 0xe3560000, 0x0a000051\n"
        ".word 0xe59f11a0, 0xe59f0198, 0xe1a00000, 0xe3a04010\n"
        ".word 0xe3a030c0, 0xe3a02000, 0xe3a01c01, 0xe3a00801\n"
        ".word 0xe88d0810, 0xeb01e8c2, 0xe1a07000, 0xe3a010c0\n"
        ".word 0xeb01ee62, 0xe3a01090, 0xe1a00007, 0xeb01ee5f\n"
        ".word 0xe3a00008, 0xe587b084, 0xe5c70088, 0xe5c79089\n"
        ".word 0xe1a00007, 0xe5c7908a, 0xeb016b8a, 0xe1a08007\n"
        ".word 0xe5967090, 0xe59f0138, 0xe3a0102e, 0xe1d7a0b4\n"
        ".word 0xe1a00000, 0xe3a0302c, 0xe3a02000, 0xe3a01c01\n"
        ".word 0xe3a00801, 0xe88d0810, 0xeb01e8a9, 0xe5809004\n"
        ".word 0xe5809008, 0xe580900c, 0xe5809010, 0xe5809014\n"
        ".word 0xe5809018, 0xe580901c, 0xe5809020, 0xe3a010dc\n"
        ".word 0xe5809024, 0xe5801000, 0xe5809028, 0xe1c0a0b4\n"
        ".word 0xe1d710bc, 0xe1a04000, 0xe1c010bc, 0xe1d711bc\n"
        ".word 0xe1c011bc, 0xe6ff007a, 0xe59f10cc, 0xe0802200\n"
        ".word 0xe5970008, 0xe0811102, 0xe5911014, 0xe12fff31\n"
        ".word 0xe5840008, 0xe1a01006, 0xe3a02090, 0xe1a00008\n"
        ".word 0xe5884090, 0xeb01cf37, 0xe58890ac, 0xe5950088\n"
        ".word 0xe1a07008, 0xe3500000, 0x158070ac, 0x15950088\n"
        ".word 0x158700b0, 0x0585708c, 0x058790b0, 0xe5857088\n"
        ".word 0xe5950080, 0xe2800001, 0xe5850080, 0xe59660ac\n"
        ".word 0xe3560000, 0x1affffad, 0xe58d9008, 0xed9f8a17\n"
        ".word 0xe58d900c, 0xe58d9010, 0xe58d9014, 0xed8d8a05\n"
        ".word 0xe28d1008, 0xe1a00005, 0xeb016a9c, 0xe28d1008\n"
        ".word 0xe1a00005, 0xeb016a43, 0xeeb00a48, 0xe1a00005\n"
        ".word 0xeb0169a9, 0xe3e01000, 0xe1a00005, 0xeb016936\n"
        ".word 0xe28dd01c, 0xe1a00005, 0xecbd8b02, 0xe8bd8ff0\n"
        ".word 0x000005b7, 0x004093f8, 0x000005ca, 0x00464110\n"
        ".word 0x3f800000\n");
}
// DECOMP_FUNC(0x0024972c, 164)


// ---------------------------------------------------------------------------
// 0x0024972C -- replace buffer 0 (+0x10/+0x14/+0x18, key +0x0C).
//
// Frees the old allocation, clears the triple, then allocates `size` bytes and
// copies `data`; a null source or non-positive size leaves the cleared triple.
// ---------------------------------------------------------------------------

//
__attribute__((naked)) void effParts_func_0024972c(EffPartsParticle*, const void*,
                                                   s32, u16)
{
    asm volatile(
        ".word 0xE92D40F0\n"
        ".word 0xE1A04000\n"
        ".word 0xE24DD00C\n"
        ".word 0xE5900018\n"
        ".word 0xE1A07001\n"
        ".word 0xE1A05002\n"
        ".word 0xE3500000\n"
        ".word 0xE1A06003\n"
        ".word 0x0A000004\n"
        ".word 0xEB01EB02\n" // AsdMem_Free (0x002C4360)
        ".word 0xE3A00000\n"
        ".word 0xE5840010\n"
        ".word 0xE5840014\n"
        ".word 0xE5840018\n"
        ".word 0xE3570000\n"
        ".word 0x13550000\n"
        ".word 0xDA000013\n"
        ".word 0xE59F1050\n"
        ".word 0xE59F0050\n"
        ".word 0xE1A00000\n"
        ".word 0xE3A01001\n"
        ".word 0xE3A00010\n"
        ".word 0xE1CD00F0\n"
        ".word 0xE1A03005\n"
        ".word 0xE3A02000\n"
        ".word 0xE3A01C01\n"
        ".word 0xE3A00801\n"
        ".word 0xEB01E741\n" // AsdWork_Alloc (0x002C34A4)
        ".word 0xE1C460BC\n" // key -> part +0x0C
        ".word 0xE5840018\n" // allocation -> part +0x18
        ".word 0xE2844010\n"
        ".word 0xE1A02005\n"
        ".word 0xE8840021\n" // buffer and size -> part +0x10/+0x14
        ".word 0xE28DD00C\n"
        ".word 0xE1A01007\n" // data source for tail copy
        ".word 0xE8BD40F0\n"
        ".word 0xEA01F20C\n" // tail branch to AsdMem_Copy (0x002C5FF4)
        ".word 0xE28DD00C\n"
        ".word 0xE8BD80F0\n"
        ".word 0x00000438\n" // Original line marker.
        ".word 0x004093F8\n"); // Original literal pool word.
}
// DECOMP_FUNC(0x0024fda4, 192)


// ---------------------------------------------------------------------------
// 0x0024FDA4 -- clone a particle through the +0x14 table hook.
// ---------------------------------------------------------------------------

//
__attribute__((naked)) EffPartsParticle* effParts_func_0024fda4(EffPartsParticle*)
{
    asm volatile(
        ".word 0xE92D4070\n"
        ".word 0xE1A05000\n"
        ".word 0xE1D060B4\n"
        ".word 0xE59F00A4\n"
        ".word 0xE24DD008\n"
        ".word 0xE3A0102E\n"
        ".word 0xE1A00000\n"
        ".word 0xE3A00010\n"
        ".word 0xE3A01001\n"
        ".word 0xE1CD00F0\n"
        ".word 0xE3A0302C\n"
        ".word 0xE3A02000\n"
        ".word 0xE3A01C01\n"
        ".word 0xE3A00801\n"
        ".word 0xEB01CDB0\n" // AsdWork_Alloc (0x002C34A4)
        ".word 0xE3A01000\n"
        ".word 0xE5801004\n"
        ".word 0xE5801008\n"
        ".word 0xE580100C\n"
        ".word 0xE5801010\n"
        ".word 0xE5801014\n"
        ".word 0xE5801018\n"
        ".word 0xE580101C\n"
        ".word 0xE5801020\n"
        ".word 0xE5801024\n"
        ".word 0xE3A020DC\n"
        ".word 0xE5801028\n"
        ".word 0xE5802000\n"
        ".word 0xE1C060B4\n"
        ".word 0xE1D510BC\n"
        ".word 0xE1A04000\n"
        ".word 0xE1C010BC\n"
        ".word 0xE1D511BC\n"
        ".word 0xE1C011BC\n"
        ".word 0xE6FF0076\n"
        ".word 0xE59F1028\n"
        ".word 0xE0800200\n"
        ".word 0xE0811100\n"
        ".word 0xE5950008\n"
        ".word 0xE5911014\n" // Type-table create-instance hook at +0x14.
        ".word 0xE12FFF31\n" // Indirect call through that hook.
        ".word 0xE1A01000\n"
        ".word 0xE5841008\n"
        ".word 0xE28DD008\n"
        ".word 0xE1A00004\n"
        ".word 0xE8BD8070\n"
        ".word 0x004093F8\n" // Original literal pool word.
        ".word 0x00464110\n"); // Original type-table literal.
}
// DECOMP_FUNC(0x0024fe64, 196)


// ---------------------------------------------------------------------------
// 0x0024FE64 -- clone a particle through the +0x00 table hook.
// Unlike 0x0024FDA4 this also copies +0x00 from the record.
// ---------------------------------------------------------------------------

//
__attribute__((naked)) EffPartsParticle* effParts_func_0024fe64(EffPartsParticle*)
{
    asm volatile(
        ".word 0xE92D4070\n"
        ".word 0xE1A05000\n"
        ".word 0xE1D060B4\n"
        ".word 0xE59F00A8\n"
        ".word 0xE24DD008\n"
        ".word 0xE3A0102E\n"
        ".word 0xE1A00000\n"
        ".word 0xE3A00010\n"
        ".word 0xE3A01001\n"
        ".word 0xE1CD00F0\n"
        ".word 0xE3A0302C\n"
        ".word 0xE3A02000\n"
        ".word 0xE3A01C01\n"
        ".word 0xE3A00801\n"
        ".word 0xEB01CD80\n" // AsdWork_Alloc (0x002C34A4)
        ".word 0xE3A01000\n"
        ".word 0xE5801004\n"
        ".word 0xE5801008\n"
        ".word 0xE580100C\n"
        ".word 0xE5801010\n"
        ".word 0xE5801014\n"
        ".word 0xE5801018\n"
        ".word 0xE580101C\n"
        ".word 0xE5801020\n"
        ".word 0xE5801024\n"
        ".word 0xE3A020DC\n"
        ".word 0xE5801028\n"
        ".word 0xE5802000\n"
        ".word 0xE1C060B4\n"
        ".word 0xE5951000\n"
        ".word 0xE1A04000\n"
        ".word 0xE5801000\n"
        ".word 0xE1D510BC\n"
        ".word 0xE1C010BC\n"
        ".word 0xE1D511BC\n"
        ".word 0xE1C011BC\n"
        ".word 0xE6FF0076\n"
        ".word 0xE59F1024\n"
        ".word 0xE0800200\n"
        ".word 0xE7911100\n" // Type-table create-record hook at +0.
        ".word 0xE1A00005\n"
        ".word 0xE12FFF31\n" // Indirect call through that hook.
        ".word 0xE1A01000\n"
        ".word 0xE5841008\n"
        ".word 0xE28DD008\n"
        ".word 0xE1A00004\n"
        ".word 0xE8BD8070\n"
        ".word 0x004093F8\n" // Original literal pool word.
        ".word 0x00464110\n"); // Original type-table literal.
}
// DECOMP_FUNC(0x0025caa8, 128)


// ---------------------------------------------------------------------------
// 0x0025CAA8 -- allocate and initialise one child node.
// ---------------------------------------------------------------------------

//
__attribute__((naked)) EffPartsNode* effParts_func_0025caa8()
{
    asm volatile(
        ".word 0xE92D4030\n"
        ".word 0xE24DD00C\n"
        ".word 0xE59F1068\n"
        ".word 0xE59F0068\n"
        ".word 0xE1A00000\n"
        ".word 0xE3A05001\n"
        ".word 0xE3A00010\n"
        ".word 0xE88D0021\n"
        ".word 0xE3A030C0\n"
        ".word 0xE3A02000\n"
        ".word 0xE3A01C01\n"
        ".word 0xE3A00801\n"
        ".word 0xEB019A71\n" // AsdWork_Alloc (0x002C34A4)
        ".word 0xE1A04000\n"
        ".word 0xE3A010C0\n"
        ".word 0xEB01A011\n" // AsdMem_Zero (0x002C4B30)
        ".word 0xE3A01090\n"
        ".word 0xE1A00004\n"
        ".word 0xEB01A00E\n" // AsdMem_Zero (0x002C4B30)
        ".word 0xE3A01008\n"
        ".word 0xE5845084\n"
        ".word 0xE3A00000\n"
        ".word 0xE5C41088\n"
        ".word 0xE5C40089\n"
        ".word 0xE5C4008A\n"
        ".word 0xE1A00004\n"
        ".word 0xEB011D38\n" // AsdDrawDesc_Init (0x002A3FF8)
        ".word 0xE28DD00C\n"
        ".word 0xE1A00004\n"
        ".word 0xE8BD8030\n"
        ".word 0x000005CA\n" // Original line marker.
        ".word 0x004093F8\n"); // Original literal pool word.
}
// DECOMP_FUNC(0x0025cc14, 164)


// ---------------------------------------------------------------------------
// 0x0025CC14 -- replace buffer 1 (+0x20/+0x24/+0x28, key +0x1C).
// ---------------------------------------------------------------------------

//
__attribute__((naked)) void effParts_func_0025cc14(EffPartsParticle*, const void*,
                                                   s32, u16)
{
    asm volatile(
        ".word 0xE92D40F0\n"
        ".word 0xE1A04000\n"
        ".word 0xE24DD00C\n"
        ".word 0xE5900028\n"
        ".word 0xE1A07001\n"
        ".word 0xE1A05002\n"
        ".word 0xE3500000\n"
        ".word 0xE1A06003\n"
        ".word 0x0A000004\n"
        ".word 0xEB019DC8\n" // AsdMem_Free (0x002C4360)
        ".word 0xE3A00000\n"
        ".word 0xE5840020\n"
        ".word 0xE5840024\n"
        ".word 0xE5840028\n"
        ".word 0xE3570000\n"
        ".word 0x13550000\n"
        ".word 0xDA000013\n"
        ".word 0xE59F1050\n"
        ".word 0xE59F0050\n"
        ".word 0xE1A00000\n"
        ".word 0xE3A01001\n"
        ".word 0xE3A00010\n"
        ".word 0xE1CD00F0\n"
        ".word 0xE1A03005\n"
        ".word 0xE3A02000\n"
        ".word 0xE3A01C01\n"
        ".word 0xE3A00801\n"
        ".word 0xEB019A07\n" // AsdWork_Alloc (0x002C34A4)
        ".word 0xE1C461BC\n" // key -> part +0x1C
        ".word 0xE5840028\n" // allocation -> part +0x28
        ".word 0xE2844020\n"
        ".word 0xE1A02005\n"
        ".word 0xE8840021\n" // buffer and size -> part +0x20/+0x24
        ".word 0xE28DD00C\n"
        ".word 0xE1A01007\n" // data source for tail copy
        ".word 0xE8BD40F0\n"
        ".word 0xEA01A4D2\n" // tail branch to AsdMem_Copy (0x002C5FF4)
        ".word 0xE28DD00C\n"
        ".word 0xE8BD80F0\n"
        ".word 0x0000045E\n" // Original line marker.
        ".word 0x004093F8\n"); // Original literal pool word.
}
// DECOMP_FUNC(0x0028c920, 348)


// ---------------------------------------------------------------------------
// 0x0028C920 -- deep copy of one particle record.
//
// Buffer 0 is re-allocated when (resolved source != 0 && size +0x14 > 0) and
// buffer 1 goes through 0x0025CC14; +0x0C/+0x1C keys are copied.
// ---------------------------------------------------------------------------

//
__attribute__((naked)) EffPartsParticle* effParts_func_0028c920(EffPartsParticle*)
{
    asm volatile(
        ".word 0xE92D47F0\n"
        ".word 0xE1A04000\n"
        ".word 0xE24DD008\n"
        ".word 0xE3A0102E\n"
        ".word 0xE1D060B4\n"
        ".word 0xE59F0138\n"
        ".word 0xE1A00000\n"
        ".word 0xE3A09001\n"
        ".word 0xE3A0A010\n"
        ".word 0xE3A0302C\n"
        ".word 0xE3A02000\n"
        ".word 0xE3A01C01\n"
        ".word 0xE3A00801\n"
        ".word 0xE58D9004\n"
        ".word 0xE58DA000\n"
        ".word 0xEB00DAD0\n" // AsdWork_Alloc (0x002C34A4)
        ".word 0xE3A01000\n"
        ".word 0xE5801004\n"
        ".word 0xE5801008\n"
        ".word 0xE580100C\n"
        ".word 0xE5801010\n"
        ".word 0xE5801014\n"
        ".word 0xE5801018\n"
        ".word 0xE580101C\n"
        ".word 0xE5801020\n"
        ".word 0xE5801024\n"
        ".word 0xE3A020DC\n"
        ".word 0xE5801028\n"
        ".word 0xE5802000\n"
        ".word 0xE1C060B4\n"
        ".word 0xE5941000\n"
        ".word 0xE1A05000\n"
        ".word 0xE5801000\n"
        ".word 0xE5946014\n"
        ".word 0xE3560000\n"
        ".word 0x0A000019\n"
        ".word 0xE5940018\n"
        ".word 0xE3500000\n"
        ".word 0x15947010\n"
        ".word 0x0A000022\n"
        ".word 0xE1D480BC\n"
        ".word 0xE3570000\n"
        ".word 0x13560000\n"
        ".word 0xDA000011\n"
        ".word 0xE59F10A0\n"
        ".word 0xE59F0098\n"
        ".word 0xE1A00000\n"
        ".word 0xE1A03006\n"
        ".word 0xE3A02000\n"
        ".word 0xE3A01C01\n"
        ".word 0xE3A00801\n"
        ".word 0xE58D9004\n"
        ".word 0xE58DA000\n"
        ".word 0xEB00DAAA\n" // AsdWork_Alloc (0x002C34A4)
        ".word 0xE2851010\n"
        ".word 0xE1C580BC\n"
        ".word 0xE5850018\n"
        ".word 0xE8810041\n"
        ".word 0xE1A02006\n"
        ".word 0xE5950010\n"
        ".word 0xE1A01007\n"
        ".word 0xEB00E576\n" // AsdMem_Copy (0x002C5FF4)
        ".word 0xE5942024\n"
        ".word 0xE3520000\n"
        ".word 0x0A000006\n"
        ".word 0xE5940028\n"
        ".word 0xE3500000\n"
        ".word 0x15941020\n"
        ".word 0x0A00000A\n"
        ".word 0xE1D431BC\n"
        ".word 0xE1A00005\n"
        ".word 0xEBFF4074\n" // effParts_func_0025cc14 (0x0025CC14)
        ".word 0xE28DD008\n"
        ".word 0xE1A00005\n"
        ".word 0xE8BD87F0\n"
        ".word 0xE5940010\n"
        ".word 0xE3500000\n"
        ".word 0x10807004\n"
        ".word 0x03A07000\n"
        ".word 0xEAFFFFD7\n"
        ".word 0xE5940020\n"
        ".word 0xE3500000\n"
        ".word 0x10801004\n"
        ".word 0x03A01000\n"
        ".word 0xEAFFFFEF\n"
        ".word 0x004093F8\n" // Original file literal.
        ".word 0x00000438\n"); // Original line marker.
}
// DECOMP_FUNC(0x00192168, 124)


// ---------------------------------------------------------------------------
// 0x00192168 -- allocate one empty particle and store the 16-bit type id.
// ---------------------------------------------------------------------------

//
__attribute__((naked)) EffPartsParticle* effParts_func_00192168(u32)
{
    asm volatile(
        ".word 0xE92D4010\n"
        ".word 0xE1A04000\n"
        ".word 0xE59F0068\n"
        ".word 0xE24DD008\n"
        ".word 0xE3A0102E\n"
        ".word 0xE1A00000\n"
        ".word 0xE3A01001\n"
        ".word 0xE3A00010\n"
        ".word 0xE1CD00F0\n"
        ".word 0xE3A0302C\n"
        ".word 0xE3A02000\n"
        ".word 0xE3A01C01\n"
        ".word 0xE3A00801\n"
        ".word 0xEB04C4C0\n" // AsdWork_Alloc (0x002C34A4)
        ".word 0xE3A01000\n"
        ".word 0xE5801004\n"
        ".word 0xE5801008\n"
        ".word 0xE580100C\n"
        ".word 0xE5801010\n"
        ".word 0xE5801014\n"
        ".word 0xE5801018\n"
        ".word 0xE580101C\n"
        ".word 0xE5801020\n"
        ".word 0xE5801024\n"
        ".word 0xE3A020DC\n"
        ".word 0xE5801028\n"
        ".word 0xE5802000\n"
        ".word 0xE1C040B4\n"
        ".word 0xE28DD008\n"
        ".word 0xE8BD8010\n"
        ".word 0x004093F8\n"); // Original literal pool word.
}
// DECOMP_FUNC(0x001d2460, 104)


// ---------------------------------------------------------------------------
// 0x001D2460 -- create an empty parts manager.
// ---------------------------------------------------------------------------

//
__attribute__((naked)) EffPartsSource* effParts_func_001d2460()
{
    asm volatile(
        ".word 0xE92D4010\n"
        ".word 0xE59F1054\n"
        ".word 0xE59F0054\n"
        ".word 0xE24DD008\n"
        ".word 0xE1A00000\n"
        ".word 0xE3A01001\n"
        ".word 0xE3A00010\n"
        ".word 0xE1CD00F0\n"
        ".word 0xE3A03090\n"
        ".word 0xE3A02000\n"
        ".word 0xE3A01C01\n"
        ".word 0xE3A00801\n"
        ".word 0xEB03C403\n" // AsdWork_Alloc (0x002C34A4)
        ".word 0xE1A04000\n"
        ".word 0xE3A01090\n"
        ".word 0xEB03C9A3\n" // AsdMem_Zero (0x002C4B30)
        ".word 0xE3A01000\n"
        ".word 0xE5841080\n"
        ".word 0xE1A00004\n"
        ".word 0xE5841084\n"
        ".word 0xEB0346D0\n" // AsdDrawDesc_Init (0x002A3FF8)
        ".word 0xE28DD008\n"
        ".word 0xE1A00004\n"
        ".word 0xE8BD8010\n"
        ".word 0x000005B7\n" // Original line marker.
        ".word 0x004093F8\n"); // Original literal pool word.
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

// Readable semantic draft of file loading, record materialization, clone/link
// handling, and cleanup. Preserve it with the exact wrapper for later structural
// decompilation of the original record loops and shared literal pool.
#if 0
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
#endif

// DECOMP_FUNC(0x001e1970, 576)
// Verified standalone boundary: next ledger entry begins at 0x001E1BB0.
__attribute__((naked)) EffPartsSource* effParts_func_001e1970(const char*) {
    asm volatile(
        ".word 0xe92d4ff0, 0xe24dd00c, 0xe3a03080, 0xe3a02001\n"
        ".word 0xe28d1008, 0xeb03912c, 0xe1a08000, 0xe59f1214\n"
        ".word 0xe59f0214, 0xe1a00000, 0xe3a0b001, 0xe3a00010\n"
        ".word 0xe88d0801, 0xe3a03090, 0xe3a02000, 0xe3a01c01\n"
        ".word 0xe3a00801, 0xeb0386ba, 0xe1a05000, 0xe3a01090\n"
        ".word 0xeb038c5a, 0xe3a0a000, 0xe585a080, 0xe1a00005\n"
        ".word 0xe585a084, 0xeb030987, 0xe898000f, 0xe2854010\n"
        ".word 0xe3a07000, 0xe885000f, 0xe898000f, 0xe884000f\n"
        ".word 0xe5980074, 0xe5850074, 0xe5980068, 0xe5850068\n"
        ".word 0xe5980080, 0xe5981088, 0xe3500000, 0xe0814008\n"
        ".word 0x9a00005f, 0xe5940098, 0xe3100001, 0xe5940090\n"
        ".word 0x0a00002a, 0xe595908c, 0xe3590000, 0x0a000004\n"
        ".word 0xe2500001, 0x3a000003, 0xe59990ac, 0xe3590000\n"
        ".word 0x1afffffa, 0xe1a0900a, 0xe320f000, 0xeb01ec15\n"
        ".word 0xe1a06000, 0xe3a020c0, 0xe1a01009, 0xeb036d3d\n"
        ".word 0xe3a01090, 0xe1a00006, 0xeb038c30, 0xe3a00008\n"
        ".word 0xe586b084, 0xe5c60088, 0xe5c6a089, 0xe1a00006\n"
        ".word 0xe5c6a08a, 0xeb03095b, 0xe5960098, 0xe3800001\n"
        ".word 0xe5860098, 0xe5990090, 0xe5860090, 0xe59900ac\n"
        ".word 0xe3500000, 0x158060b0, 0x159910ac, 0x158610ac\n"
        ".word 0x0586a0ac, 0x05856088, 0xe58960ac, 0xe58690b0\n"
        ".word 0xe5950080, 0xe2800001, 0xe5850080, 0xea000012\n"
        ".word 0xe0800008, 0xeb02ab91, 0xe1a09000, 0xe320f000\n"
        ".word 0xeb01ebf0, 0xe5809090, 0xe580a0ac, 0xe5951088\n"
        ".word 0xe1a06000, 0xe3510000, 0x158100ac, 0x15952088\n"
        ".word 0x158020b0, 0x0585008c, 0x0580a0b0, 0xe5952080\n"
        ".word 0xe5850088, 0xe2821001, 0xe5851080, 0xe5940098\n"
        ".word 0xe3100002, 0x0a00000c, 0xe595208c, 0xe5940094\n"
        ".word 0xe3520000, 0x0a000004, 0xe2500001, 0x3a000003\n"
        ".word 0xe59220ac, 0xe3520000, 0x1afffffa, 0xe1a0200a\n"
        ".word 0xe1a01006, 0xe1a00005, 0xeb01eb4a, 0xe1a01004\n"
        ".word 0xe3a02090, 0xe1a00006, 0xeb036cfa, 0xe284109c\n"
        ".word 0xe286009c, 0xeb03773c, 0xe5940098, 0xe2877001\n"
        ".word 0xe28440c0, 0xe5860098, 0xe5980080, 0xe1500007\n"
        ".word 0x8affff9f, 0xe1a00008, 0xeb0389f0, 0xe28dd00c\n"
        ".word 0xe1a00005, 0xe8bd8ff0, 0x000005b7, 0x004093f8\n");
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

// Readable semantic draft for P2A texture loading and animation-wrapper setup.
// Keep its offset and mode-selection notes beside the exact ARM wrapper below.
#if 0
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
#endif

// DECOMP_FUNC(0x00249324, 484)
// Verified standalone boundary: next ledger function begins at 0x00249508,
// immediately after the original source-path literal.
__attribute__((naked)) EffP2AAnim* effP2A_func_00249324(const void*) {
    asm volatile(
        ".word 0xe92d4ff0, 0xe3500000, 0xe24dd00c, 0xe3a0a001\n"
        ".word 0xe3a0b010, 0xe3a05000, 0x0a000047, 0xe5901000\n"
        ".word 0xe1a07000, 0xe3a0001c, 0xe0816007, 0xe4968004\n"
        ".word 0xe0800108, 0xe0814000, 0xe3a01f47, 0xe28f0f5b\n"
        ".word 0xe1a00000, 0xe1a03004, 0xe3a02000, 0xe3a01c01\n"
        ".word 0xe3a00801, 0xe58da004, 0xe58db000, 0xeb01e847\n"
        ".word 0xe1a05000, 0xe1a01007, 0xe5855018, 0xe5972000\n"
        ".word 0xe280001c, 0xeb01f315, 0xe285001c, 0xe2851024\n"
        ".word 0xe585800c, 0xe1c500f0, 0xe595101c, 0xe3580000\n"
        ".word 0xe3a04000, 0xe0800001, 0xe2800008, 0xe5850014\n"
        ".word 0xda000012, 0xe5960000, 0xe0809007, 0xe1a00009\n"
        ".word 0xeb010df3, 0xe3500000, 0xe1a00009, 0x0a000003\n"
        ".word 0xeb010db4, 0xe5951014, 0xe7810104, 0xea000003\n"
        ".word 0xe320f000, 0xeb010d9f, 0xe5951014, 0xe7810104\n"
        ".word 0xe2844001, 0xe1540008, 0xe2866004, 0xbaffffec\n"
        ".word 0xe585a010, 0xe585a008, 0xe5951000, 0xe3a00000\n"
        ".word 0xe5912004, 0xe3520000, 0xc5953004, 0xc3a0c002\n"
        ".word 0xda000009, 0xe0801100, 0xe0831101, 0xe5914010\n"
        ".word 0xe3140201, 0x1591100c, 0x15851008, 0x0a00001a\n"
        ".word 0xe2800001, 0xe1500002, 0xbafffff5, 0xe5951008\n"
        ".word 0xe3a00018, 0xe0811101, 0xe0804101, 0xe3a0107a\n"
        ".word 0xe28f0058, 0xe1a00000, 0xe1a03004, 0xe3a02000\n"
        ".word 0xe3a01c01, 0xe3a00801, 0xe58da004, 0xe58db000\n"
        ".word 0xeb01e802, 0xe2801018, 0xe5801010, 0xe1a04000\n"
        ".word 0xe3a01000, 0xe5805000, 0xebfe233b, 0xe1c4a1b4\n"
        ".word 0xe28dd00c, 0xe1a00004, 0xe8bd8ff0, 0xe5911008\n"
        ".word 0xe3110040, 0x03110080, 0x1585c008, 0xeaffffdf\n"
        ".word 0x535c3a63, 0x5c34544d, 0x36445258, 0x415c3638\n"
        ".word 0x44536473, 0x6f535c4b, 0x65637275, 0x7866475c\n"
        ".word 0x6666455c, 0x5c746365, 0x50666665, 0x632e4132\n"
        ".word 0x00007070\n");
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

// Readable semantic draft of TLP texture-table allocation, entry copying,
// texture dispatch, and element-count accumulation. Keep it beside the exact
// ARM wrapper for future cleanup of the original VFP/literal-pool layout.
#if 0
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
#endif

// DECOMP_FUNC(0x00249588, 420)
// Verified boundary: the next ledger function starts at 0x0024972C, immediately
// after this function's source-path literal.
__attribute__((naked)) EffTLPObject* effTLP_func_00249588(const void*) {
    asm volatile(
        ".word 0xe92d43f0, 0xe24dd00c, 0xe3a01036, 0xe1a09000\n"
        ".word 0xe5908004, 0xe1a00208, 0xe0800108, 0xe2804028\n"
        ".word 0xe28f0f52, 0xe1a00000, 0xe3a01001, 0xe3a00010\n"
        ".word 0xe1cd00f0, 0xe1a03004, 0xe3a02000, 0xe3a01c01\n"
        ".word 0xe3a00801, 0xeb01e7b4, 0xe1a06000, 0xe3a00000\n"
        ".word 0xe286701c, 0xe3e02000, 0xe1a04000, 0xe8870045\n"
        ".word 0xe2861028, 0xe2860010, 0xe0813208, 0xe880000a\n"
        ".word 0xe2895010, 0xe5990000, 0xe3580000, 0xe0857208\n"
        ".word 0xe5860000, 0xe5990004, 0xe5860004, 0xe5990008\n"
        ".word 0xe5860008, 0xe599000c, 0xe586000c, 0x9a000016\n"
        ".word 0xe596c010, 0xe895000f, 0xe08cc204, 0xe88c000f\n"
        ".word 0xe1a00007, 0xeb010d59, 0xe3500000, 0xe1a00007\n"
        ".word 0x0a000003, 0xeb010d1a, 0xe5961014, 0xe7810104\n"
        ".word 0xea000003, 0xe320f000, 0xeb010d05, 0xe5961014\n"
        ".word 0xe7810104, 0xe5b50004, 0xe2844001, 0xe1540008\n"
        ".word 0xe285500c, 0xe0877000, 0x3affffe8, 0xe5962004\n"
        ".word 0xe3a00000, 0xe3520000, 0x0a000011, 0xe5961010\n"
        ".word 0xe3120001, 0xe2411010, 0x0a000001, 0xe5b10010\n"
        ".word 0xe2800001, 0xe1b020a2, 0xe3a03000, 0x0a000007\n"
        ".word 0xe5b1c010, 0xe2800001, 0xe5b14010, 0xe2833001\n"
        ".word 0xe2522001, 0xe080000c, 0xe0833004, 0x1afffff7\n"
        ".word 0xe0800003, 0xe596101c, 0xe5860018, 0xe2810001\n"
        ".word 0xe586001c, 0xe28dd00c, 0xe1a00006, 0xe8bd83f0\n"
        ".word 0x535c3a63, 0x5c34544d, 0x36445258, 0x415c3638\n"
        ".word 0x44536473, 0x6f535c4b, 0x65637275, 0x7866475c\n"
        ".word 0x6666455c, 0x5c746365, 0x54666665, 0x632e504c\n"
        ".word 0x00007070\n");
}

} // namespace smt4::engine
